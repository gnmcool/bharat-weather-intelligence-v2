"""M4.3 historical backfill: monthly immutable `history-YYYY-MM` releases of the matched historical dataset.

Scope (owner-approved): 1 Feb 2024 -> latest complete month; the 36 fixed points; ECMWF IFS 0.25, GFS, ICON;
temperature, rain, gusts; nominal leads 1-7. References: ERA5 reanalysis, IMD 0.25 deg gauge analysis (raw yearly
files kept in immutable `history-imd-raw-YYYY` releases), METAR only where the matching rule holds.

Historical rows are a reconstruction from Open-Meteo's Previous Runs API: run_time_known = false, no run time,
lead = "nominal previous_dayN". They are never an exact forecast-run archive and never pooled with it.
No skill scores are computed here.

  python history/backfill.py month   --month 2024-02 --out STAGE --imd-dir DIR     build one month
  python history/backfill.py validate STAGE                                        refuse or accept a month
  python history/backfill.py batch   --months-file F --index IDX --work W --budget N
  python history/backfill.py quality --index IDX --out FILE                        aggregate quality report
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sources as S  # noqa: E402
from build import build_matched, imd_rows, metar_daily, pair_stations, rows_from_era5, rows_from_previous_runs  # noqa: E402
from common import (BACKFILL_HOURLY, CATEGORIES, HIST_SCHEMA, classify_reason, HOURLY, LEADS, MATCH_MAP, MATCHED_SCHEMA, POINTS_FILE,  # noqa: E402
                    PROCESSING_VERSION, REF_SCHEMA, SCHEMA_VERSION, HistoryError, date_range, haversine_km,
                    load_points, om_weight, sha256_file, utc_request_range, validate_history_rows,
                    validate_reference_rows, write_json)

MODELS = ["ecmwf_ifs025", "gfs_global", "icon_global"]          # same names as the prospective archive
ERA5_HOURLY = ["temperature_2m", "precipitation", "wind_gusts_10m"]
DAILY_VARS = [dv for v in BACKFILL_HOURLY for dv, *_ in HOURLY[v]]   # tmax tmin precip precip_0830 gust_max
IMD_MAX_KM = 30.0
METAR_MAX_KM, METAR_MAX_DELEV = 25.0, 100.0
IMD_REQUIRED_UNTIL = 2025      # years <= this must be available; later years may be unpublished (owner rule H)
MAX_GRID_KM = 30.0             # forecast / ERA5 grid cell farther than this from the point = spatial anomaly
REPO = os.environ.get("GITHUB_REPOSITORY", "gnmcool/bharat-weather-intelligence-v2")


def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0)


def month_days(month: str) -> list[date]:
    y, m = map(int, month.split("-"))
    first = date(y, m, 1)
    nxt = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
    return date_range(first, nxt - timedelta(days=1))


def month_weight(n_points: int, n_days: int) -> float:
    """Open-Meteo counted calls for one month (3 previous-runs requests + 1 ERA5 request)."""
    d = n_days + 2
    return len(MODELS) * om_weight(n_points, len(BACKFILL_HOURLY) * len(LEADS), d) + om_weight(n_points, len(ERA5_HOURLY), d)


def write_table(df: pd.DataFrame, schema: pa.Schema, path: pathlib.Path) -> int:
    t = pa.Table.from_pandas(df[schema.names], schema=schema, preserve_index=False)
    pq.write_table(t, path, compression="zstd")
    return t.num_rows


# ================================================================== build one month
def build_month(month: str, out: pathlib.Path, imd_dir: pathlib.Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    points = load_points()
    days = month_days(month)
    u1, u2 = utc_request_range(days[0], days[-1])
    errors, anomalies, sources_used = [], [], {}
    F_rows, R_rows = [], []
    t0 = time.time()

    # --- forecasts (Open-Meteo Previous Runs API)
    for model in MODELS:
        try:
            resp, url = S.previous_runs(points, model, BACKFILL_HOURLY, LEADS, u1, u2)
        except S.QuotaExhausted:
            raise
        except Exception as e:  # noqa: BLE001 — a failed retrieval is always a problem (rule G)
            errors.append({"source": f"open-meteo previous-runs {model}", "error": str(e)[:400]})
            continue
        F_rows += rows_from_previous_runs(resp, points, model, model, BACKFILL_HOURLY, LEADS, days, url, now_utc())
        gd = [haversine_km(p["lat"], p["lon"], r["latitude"], r["longitude"]) for p, r in zip(points, resp)]
        sources_used[model] = {"api": S.PREV_RUNS, "om_model": model, "request_utc_dates": [str(u1), str(u2)],
                               "hourly": [f"{v}_previous_day1..7" for v in BACKFILL_HOURLY], "timezone": "GMT",
                               "grid_distance_km_max": round(max(gd), 1)}
        if max(gd) > MAX_GRID_KM:
            anomalies.append({"type": "spatial", "detail": f"{model} grid cell {max(gd):.0f} km from a point"})

    # --- ERA5 reanalysis
    elev = {}
    try:
        resp, url = S.era5(points, ERA5_HOURLY, u1, u2)
        R_rows += rows_from_era5(resp, points, ERA5_HOURLY, days, url, now_utc())
        elev = {p["id"]: r.get("elevation") for p, r in zip(points, resp)}
        gd = [haversine_km(p["lat"], p["lon"], r["latitude"], r["longitude"]) for p, r in zip(points, resp)]
        sources_used["era5"] = {"api": S.ERA5, "label": "ERA5 reanalysis", "request_utc_dates": [str(u1), str(u2)],
                                "grid_distance_km_max": round(max(gd), 1)}
        if max(gd) > MAX_GRID_KM:
            anomalies.append({"type": "spatial", "detail": f"ERA5 grid cell {max(gd):.0f} km from a point"})
    except S.QuotaExhausted:
        raise
    except Exception as e:  # noqa: BLE001
        errors.append({"source": "era5", "error": str(e)[:400]})

    # --- METAR: only stations meeting the matching rule (<= 25 km, |dElev| <= 100 m); no substitution
    pairing = {}
    try:
        stations = S.iem_stations()
        if not elev:
            raise HistoryError("point elevations unavailable (ERA5 request failed), cannot apply the elevation rule")
        pairs = pair_stations(points, stations, elev, METAR_MAX_KM, METAR_MAX_DELEV)
        pairing = {p["point_id"]: p for p in pairs}
        write_json(out / f"metar_pairing_history-{month}.json",
                   {"rule": {"max_km": METAR_MAX_KM, "max_abs_elev_diff_m": METAR_MAX_DELEV,
                             "day": ">= 20 reports and >= 1 report in each 6-h IST block"},
                    "stations_in_network": len(stations), "point_elevation_source": "Open-Meteo 90 m DEM (ERA5 request)",
                    "pairs": pairs})
        for pr in pairs:
            if not pr["paired"]:
                continue
            p = next(x for x in points if x["id"] == pr["point_id"])
            try:
                obs, url = S.iem_metar(pr["station"], days[0] - timedelta(days=1), days[-1] + timedelta(days=2))
            except Exception as e:  # noqa: BLE001
                errors.append({"source": f"metar {pr['station']}", "error": str(e)[:400]})
                continue
            R_rows += metar_daily(obs, pr, p, days, url.split("&year1")[0], now_utc())
            time.sleep(5)   # IEM asks for gentle use; throttled in M4.2 at faster rates
        sources_used["metar"] = {"api": S.IEM_ASOS, "fields": S.METAR_FIELDS, "rain": "never requested",
                                 "stations": sorted(p["station"] for p in pairs if p["paired"])}
    except Exception as e:  # noqa: BLE001
        errors.append({"source": "metar pairing", "error": str(e)[:400]})

    # --- IMD (raw yearly files from the immutable raw releases; file date = END of the 08:30 IST window)
    import xarray as xr
    missing_ref_reason, imd_files = {}, []
    need_years = sorted({(d + timedelta(days=1)).year for d in days})
    for y in need_years:
        nc, meta_p = imd_dir / f"RF25_ind{y}_rfp25.nc", imd_dir / f"imd_raw_{y}.json"
        meta = json.loads(meta_p.read_text()) if meta_p.exists() else None
        if nc.exists() and meta and meta.get("status") == "available":
            if sha256_file(nc) != meta["sha256"]:
                errors.append({"source": f"imd {y}", "error": "raw file checksum differs from its release metadata"})
                continue
            with xr.open_dataset(nc) as ds:
                rows, info, _ = imd_rows(ds, points, IMD_MAX_KM, S.IMD_RF25 + f" RF25={y}", meta["sha256"], now_utc(),
                                         set(days))
            R_rows += rows
            imd_files.append({"year": y, "release": meta.get("release_tag"), "sha256": meta["sha256"]})
        elif meta and meta.get("status") == "unavailable" and y > IMD_REQUIRED_UNTIL:
            missing_ref_reason["imd_rf025"] = (f"IMD {y} rainfall file not published by the source (checked "
                                               f"{meta.get('checked_utc')}); no substitute used")
        else:
            errors.append({"source": f"imd {y}", "error": "required IMD yearly file not available"})
    sources_used["imd_rf025"] = {"api": S.IMD_RF25, "files": imd_files, "max_km": IMD_MAX_KM,
                                 "date_convention": "file date D = 24 h ending 08:30 IST on D; stored at D - 1"}
    missing_ref_reason.setdefault("era5", "ERA5 not retrieved")

    # --- tables
    F = pd.DataFrame(F_rows, columns=HIST_SCHEMA.names)
    R = pd.DataFrame(R_rows, columns=REF_SCHEMA.names)
    files = []
    nF = write_table(F, HIST_SCHEMA, out / f"forecasts_history-{month}.parquet")
    files.append(("forecasts", f"forecasts_history-{month}.parquet", nF))
    nR = write_table(R, REF_SCHEMA, out / f"reference_history-{month}.parquet")
    files.append(("reference", f"reference_history-{month}.parquet", nR))
    if pairing and len(F):
        M = build_matched(pq.read_table(out / files[0][1]).to_pandas(), pq.read_table(out / files[1][1]).to_pandas(),
                          pairing, missing_ref_reason)
        nM = write_table(M, MATCHED_SCHEMA, out / f"matched_history-{month}.parquet")
        files.append(("matched", f"matched_history-{month}.parquet", nM))
    if (out / f"metar_pairing_history-{month}.json").exists():
        files.append(("metar_pairing", f"metar_pairing_history-{month}.json", None))

    man = {
        "dataset": "historical_backfill", "month": month, "schema_version": SCHEMA_VERSION,
        "processing_version": PROCESSING_VERSION, "code_commit": os.environ.get("GITHUB_SHA", "local"),
        "created_utc": now_utc(), "period_ist": [str(days[0]), str(days[-1])],
        "points_file_sha256": sha256_file(POINTS_FILE),
        "statement": ("Historical reconstruction from Open-Meteo's Previous Runs API. run_time_known = false; the "
                      "model run is not identified by the source and no run time is invented. Lead = nominal "
                      "previous_dayN (each hourly value predicted at least N x 24 h before). Not an exact "
                      "forecast-run archive; never pool with the prospective archive."),
        "expected": {"models": MODELS, "variables": DAILY_VARS, "nominal_leads": LEADS,
                     "points": [p["id"] for p in points], "days": [str(d) for d in days],
                     "values": len(points) * len(MODELS) * len(DAILY_VARS) * len(LEADS) * len(days)},
        "match_map": {k: [list(x) for x in v] for k, v in MATCH_MAP.items()},
        "sources": sources_used, "missing_reference_reasons": missing_ref_reason,
        "retrieval_errors": errors, "anomalies": anomalies, "http": dict(S.STATS), "build_secs": round(time.time() - t0),
        "files": [{"kind": k, "name": n, "rows": r, "sha256": sha256_file(out / n), "bytes": (out / n).stat().st_size}
                  for k, n, r in files],
    }
    write_json(out / f"manifest_history-{month}.json", man)
    return man


# ================================================================== validate one month (refuse = never published)
def _corr(a, b):
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 30 or np.std(a[m]) == 0 or np.std(b[m]) == 0:
        return None, int(m.sum())
    return round(float(np.corrcoef(a[m], b[m])[0, 1]), 3), int(m.sum())


def imd_alignment(R: pd.DataFrame) -> dict:
    e = R[(R.reference == "era5") & (R.variable == "precip_0830")][["point_id", "valid_date_ist", "value"]]
    i = R[(R.reference == "imd_rf025") & R.value.notna()][["point_id", "valid_date_ist", "value"]]
    res = {}
    for lag in (-1, 0, 1):
        e2 = e.assign(valid_date_ist=[d + timedelta(days=lag) for d in e.valid_date_ist])
        m = i.merge(e2, on=["point_id", "valid_date_ist"])
        r, n = _corr(m.value_x.to_numpy(float), m.value_y.to_numpy(float))
        res[f"{lag:+d}"] = {"pearson_r": r, "pairs": n}
    known = {k: v["pearson_r"] for k, v in res.items() if v["pearson_r"] is not None}
    best = max(known, key=known.get) if known else None
    return {"results": res, "best_lag": best,
            "anomaly": best is not None and best != "+0" and known[best] - known.get("+0", -1) > 0.05,
            "note": "IMD vs ERA5 08:30 IST rain; data-alignment diagnostic only, not verification. Dry months give "
                    "weak or no correlation (inconclusive, not an anomaly)."}


def validate_month(stage: pathlib.Path) -> dict:
    man_p = next(stage.glob("manifest_history-*.json"))
    man = json.loads(man_p.read_text())
    month = man["month"]
    problems, anomalies = [], list(man.get("anomalies", []))
    # 1. files and checksums
    listed = {f["name"]: f for f in man["files"]}
    present = {p.name for p in stage.iterdir() if p.is_file() and not p.name.startswith(("manifest_", "gap_report_"))}
    if set(listed) != present:
        problems.append(f"files differ from manifest: unlisted {sorted(present - set(listed))}, missing {sorted(set(listed) - present)}")
    for n, f in listed.items():
        p = stage / n
        if p.exists() and sha256_file(p) != f["sha256"]:
            problems.append(f"checksum mismatch: {n}")
        elif p.exists() and f["rows"] is not None and pq.ParquetFile(p).metadata.num_rows != f["rows"]:
            problems.append(f"row count mismatch: {n}")
    for k in ("forecasts", "reference", "matched", "metar_pairing"):
        if not any(f["kind"] == k for f in man["files"]):
            problems.append(f"{k} file missing")
    # 2. source failures (rule G: always a problem)
    for e in man.get("retrieval_errors", []):
        problems.append(f"source retrieval failed: {e['source']}: {e['error'][:200]}")
    q = {"month": month, "dataset": "historical_backfill", "publishable": False}
    if problems:
        q["problems"] = problems
        return q
    F = pq.read_table(stage / f"forecasts_history-{month}.parquet")
    R = pq.read_table(stage / f"reference_history-{month}.parquet")
    M = pq.read_table(stage / f"matched_history-{month}.parquet")
    for t, sch, name in ((F, HIST_SCHEMA, "forecasts"), (R, REF_SCHEMA, "reference"), (M, MATCHED_SCHEMA, "matched")):
        if not t.schema.equals(sch, check_metadata=False):
            problems.append(f"{name} schema differs")
    F, R, M = F.to_pandas(), R.to_pandas(), M.to_pandas()
    exp = man["expected"]
    days = [date.fromisoformat(d) for d in exp["days"]]
    # 3. every expected forecast key present exactly once (no silent partial backfill)
    key = ["point_id", "model", "variable", "nominal_lead_day", "valid_date_ist"]
    have = set(map(tuple, F[key].itertuples(index=False, name=None)))
    want = {(p, m, v, n, d) for p in exp["points"] for m in exp["models"] for v in exp["variables"]
            for n in exp["nominal_leads"] for d in days}
    if have != want or len(F) != len(want):
        problems.append(f"forecast keys: {len(want - have)} expected keys absent, {len(have - want)} unexpected, "
                        f"{len(F) - len(have)} duplicates")
    problems += [f"forecasts: {x}" for x in validate_history_rows(F)]
    problems += [f"reference: {x}" for x in validate_reference_rows(R, IMD_MAX_KM)]
    # 4. references: ERA5 rows for every point/day/variable; METAR only for matched stations within the rule
    era = R[R.reference == "era5"]
    if len(era) != len(exp["points"]) * len(days) * 5:
        problems.append(f"ERA5 rows {len(era)} != expected {len(exp['points']) * len(days) * 5}")
    pairing = {p["point_id"]: p for p in json.loads((stage / f"metar_pairing_history-{month}.json").read_text())["pairs"]}
    met = R[R.reference == "metar"]
    if len(met) and not met.point_id.map(lambda x: pairing[x]["paired"]).all():
        problems.append("METAR rows for a point without a valid station match (substitution is not allowed)")
    if len(met) and ((met.distance_km > METAR_MAX_KM) | (met.elev_diff_m.abs() > METAR_MAX_DELEV)).any():
        problems.append("METAR rows outside the matching rule")
    # 5. matched table: one row per forecast value x reference; values identical to the source tables
    n_want = sum(len(MATCH_MAP[v]) for v in F.variable)
    if len(M) != n_want:
        problems.append(f"matched rows {len(M)} != expected {n_want}")
    if M.run_time_known.any():
        problems.append("matched rows with run_time_known = true")
    if (M.reference_label[M.reference == "era5"] != "ERA5 reanalysis").any():
        problems.append("ERA5 not labelled 'ERA5 reanalysis'")
    if (M.reference_available & M.reference_value.isna()).any() or (~M.reference_available & M.reference_reason.isna()).any():
        problems.append("matched: availability flags inconsistent with values/reasons")
    if (~M.forecast_available & M.forecast_reason.isna()).any():
        problems.append("matched: unavailable forecast without a reason")
    chk = M.merge(F[key + ["value"]], on=["point_id", "model", "variable", "nominal_lead_day", "valid_date_ist"])
    if not np.allclose(chk.forecast_value.to_numpy(float), chk.value.to_numpy(float), equal_nan=True):
        problems.append("matched forecast values differ from the forecast table")
    # 6. anomalies (reported for review; not a refusal)
    for (m, v, n), g in F.groupby(["model", "variable", "nominal_lead_day"]):
        if g.reason.fillna("").str.contains("unexpected").all() and len(g):
            anomalies.append({"type": "source", "detail": f"{m} {v} lead {n}: source returned nothing all month"})
    align = imd_alignment(R)
    if align["anomaly"]:
        anomalies.append({"type": "date_alignment", "detail": f"IMD best matches ERA5 at lag {align['best_lag']}"})
    q.update(quality(F, R, M, exp, pairing, man))
    q.update({"imd_alignment": align, "anomalies": anomalies, "problems": problems, "publishable": not problems})
    return q


def _missing_breakdown(F: pd.DataFrame, col: str) -> dict:
    g = F.groupby(col).agg(expected=("complete", "size"), available=("complete", "sum"))
    return {str(k): {"expected": int(r.expected), "available": int(r.available), "missing": int(r.expected - r.available)}
            for k, r in g.iterrows()}


def reason_class(r: str | None) -> str:
    c = classify_reason(r)
    return "available" if c is None else f"{c}: {CATEGORIES[c]}"


def quality(F, R, M, exp, pairing, man) -> dict:
    n_exp = exp["values"]
    avail = int(F.complete.sum())
    refcov = {}
    for (ref, var), g in M.drop_duplicates(["point_id", "valid_date_ist", "variable", "reference"]).groupby(
            ["reference", "variable"]):
        reasons = Counter(g.reference_reason.dropna().map(lambda s: s.split(":")[0].split("(")[0].strip()[:80]))
        cats = Counter(g.reference_reason.dropna().map(classify_reason))
        refcov[f"{ref}:{var}"] = {"expected": len(g), "available": int(g.reference_available.sum()),
                                  "unavailable": int((~g.reference_available).sum()), "reasons": dict(reasons),
                                  "categories": dict(cats)}
    metar_pts = {}
    mt = M[(M.reference == "metar") & (M.variable == "tmax")].drop_duplicates(["point_id", "valid_date_ist"])
    for pid, g in mt.groupby("point_id"):
        pr = pairing[pid]
        metar_pts[pid] = {"station": pr["station"], "distance_km": pr["distance_km"], "elev_diff_m": pr["elev_diff_m"],
                          "matched": pr["paired"], "reason_not_matched": pr["reason_not_paired"],
                          "days": len(g), "days_available": int(g.reference_available.sum())}
    imd = M[(M.reference == "imd_rf025")].drop_duplicates(["point_id", "valid_date_ist"])
    imd_pts = {pid: {"days": len(g), "available": int(g.reference_available.sum()),
                     "distance_km": None if g.ref_distance_km.isna().all() else round(float(g.ref_distance_km.max()), 1)}
               for pid, g in imd.groupby("point_id")}
    return {
        "expected_values": n_exp, "rows_stored": len(F), "values_available": avail, "values_missing": n_exp - avail,
        "status": "complete" if avail == n_exp else "partial",
        "missing_by_reason": dict(Counter(map(reason_class, F.reason[~F.complete]))),
        "missing_by_category": dict(Counter(map(classify_reason, F.reason[~F.complete]))),
        "category_legend": CATEGORIES,
        "missing_by_model": _missing_breakdown(F, "model"), "missing_by_variable": _missing_breakdown(F, "variable"),
        "missing_by_lead": _missing_breakdown(F, "nominal_lead_day"),
        "missing_by_location": _missing_breakdown(F, "point_id"),
        "reference_coverage": refcov, "metar_by_point": metar_pts, "imd_by_point": imd_pts,
        "matched_rows": len(M), "reference_rows": len(R),
    }


# ================================================================== raw IMD yearly file
def imd_raw(year: int, out: pathlib.Path) -> dict:
    import xarray as xr
    out.mkdir(parents=True, exist_ok=True)
    checked = now_utc()
    try:
        body = S.imd_year(year)
    except Exception as e:  # noqa: BLE001
        return {"year": year, "status": "failed", "error": str(e)[:300], "checked_utc": checked}
    nc = out / f"RF25_ind{year}_rfp25.nc"
    nc.write_bytes(body)
    try:
        with xr.open_dataset(nc) as ds:
            from build import imd_find_names
            var, _, _, tim = imd_find_names(ds)
            a = ds[var].values
            t = ds[tim].values
            fmt = {"variable": var, "shape": list(a.shape), "dims": list(ds[var].dims),
                   "valid_cells_all_days": int(np.isfinite(np.where(a < 0, np.nan, a)).all(axis=0).sum()),
                   "first_file_day": str(np.datetime64(t[0], "D")), "last_file_day": str(np.datetime64(t[-1], "D"))}
    except Exception as e:  # noqa: BLE001 — not a NetCDF: the year is not published (e.g. empty response)
        nc.unlink()
        return {"year": year, "status": "unavailable", "checked_utc": checked, "bytes": len(body),
                "reason": f"source did not return a readable NetCDF ({len(body)} bytes): {str(e)[:120]}"}
    meta = {"year": year, "status": "available", "source_url": S.IMD_RF25, "request": f"POST form RF25={year}",
            "download_utc": checked, "bytes": len(body), "sha256": sha256_file(nc), "format_check": fmt,
            "processing_version": PROCESSING_VERSION, "code_commit": os.environ.get("GITHUB_SHA", "local"),
            "licence_note": "IMD Pune gridded rainfall; cite IMD (Pai et al. 2014). Raw file kept unmodified."}
    write_json(out / f"imd_raw_{year}.json", meta)
    write_json(out / f"manifest_imd-raw-{year}.json", {"dataset": "imd_raw", "year": year, "files": [
        {"kind": "raw", "name": nc.name, "rows": None, "sha256": meta["sha256"], "bytes": len(body)},
        {"kind": "metadata", "name": f"imd_raw_{year}.json", "rows": None, "sha256": sha256_file(out / f"imd_raw_{year}.json")}]})
    write_json(out / f"gap_report_imd-raw-{year}.json", {"year": year, "format_check": fmt, "publishable": True})
    return meta


# ================================================================== batch driver (GitHub Actions)
def sh(*a, check=True, **kw):
    r = subprocess.run(list(a), capture_output=True, text=True, **kw)
    if check and r.returncode:
        raise RuntimeError(f"{' '.join(a[:4])}: {r.stderr.strip()[:400]}")
    return r


def release_state(tag: str) -> str:
    r = sh("gh", "release", "view", tag, "--json", "isDraft", "-q", ".isDraft", check=False)
    return "none" if r.returncode else ("draft" if r.stdout.strip() == "true" else "published")


def publish(tag: str, title: str, notes: str, stage: pathlib.Path, target_kind: str) -> dict:
    assets = [str(p) for p in sorted(stage.iterdir()) if p.is_file()]
    sh("gh", "release", "create", tag, "--draft", "--latest=false", "--title", title, "--notes", notes, *assets)
    vr = pathlib.Path(__file__).resolve().parents[1] / "archive" / "verify_release.py"
    with tempfile.TemporaryDirectory() as d:
        sh(sys.executable, str(vr), "--tag", tag, "--stage", str(stage), "--out", f"{d}/pre.json", "--target-kind", target_kind)
        sh("gh", "release", "edit", tag, "--draft=false", "--latest=false")
        r = sh(sys.executable, str(vr), "--tag", tag, "--stage", str(stage), "--out", f"{d}/checks.json", "--published",
               "--target-kind", target_kind, check=False)
        checks = json.loads(pathlib.Path(f"{d}/checks.json").read_text()) if pathlib.Path(f"{d}/checks.json").exists() else {}
    if r.returncode:
        raise RuntimeError(f"post-publish verification failed for {tag}: {r.stdout[-400:]}")
    return checks


def commit_index(idx: pathlib.Path, msg: str):
    sh("git", "-C", str(idx), "add", "-A")
    if sh("git", "-C", str(idx), "diff", "--cached", "--quiet", check=False).returncode:
        sh("git", "-C", str(idx), "commit", "-qm", msg)
        for _ in range(5):
            if not sh("git", "-C", str(idx), "push", "-q", "origin", "archive-index", check=False).returncode:
                return
            sh("git", "-C", str(idx), "pull", "-q", "--rebase", "origin", "archive-index", check=False)
        raise RuntimeError("could not push index")


def append_csv(idx: pathlib.Path, row: list):
    p = idx / "history" / "INDEX.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    new = not p.exists()
    with open(p, "a") as f:
        if new:
            f.write("item,status,tag,manifest_sha256,expected_values,values_available,status_detail,recorded_utc,run_id\n")
        f.write(",".join(str(x) for x in row) + "\n")


def ensure_imd(years, imd_dir: pathlib.Path, idx: pathlib.Path, work: pathlib.Path, run_id: str,
               dry_run: bool = False) -> list:
    log = []
    imd_dir.mkdir(parents=True, exist_ok=True)
    for y in years:
        tag = f"history-imd-raw-{y}"
        st = release_state(tag)
        if dry_run and st != "published":   # dry run: download and check the raw file, publish nothing
            meta = imd_raw(y, work / f"imd-{y}")
            if meta["status"] == "available":
                for f in (work / f"imd-{y}").iterdir():
                    shutil.copy(f, imd_dir / f.name)
            write_json(imd_dir / f"imd_raw_{y}.json", meta)
            log.append({"year": y, "dry_run": True, **{k: meta.get(k) for k in ("status", "sha256", "bytes", "reason", "error")}})
            continue
        if st == "published":   # never re-download over an existing raw release: use it and check its checksum
            sh("gh", "release", "download", tag, "-D", str(imd_dir), "--clobber")
            meta = json.loads((imd_dir / f"imd_raw_{y}.json").read_text())
            ok = sha256_file(imd_dir / f"RF25_ind{y}_rfp25.nc") == meta["sha256"]
            meta["release_tag"] = tag
            write_json(imd_dir / f"imd_raw_{y}.json", meta)
            log.append({"year": y, "status": "available", "release": tag, "checksum_ok": ok})
            continue
        if st == "draft":
            sh("gh", "release", "delete", tag, "-y")
        stage = work / f"imd-{y}"
        meta = imd_raw(y, stage)
        if meta["status"] != "available":
            write_json(imd_dir / f"imd_raw_{y}.json", meta)
            rec = idx / "history" / "imd-raw" / f"{y}_{meta['status']}_{run_id}.json"
            rec.parent.mkdir(parents=True, exist_ok=True)
            write_json(rec, meta)
            append_csv(idx, [f"imd-raw-{y}", meta["status"], "", "", "", "", meta.get("reason", meta.get("error", "")).replace(",", ";")[:120], now_utc(), run_id])
            log.append({"year": y, **meta})
            continue
        checks = publish(tag, f"IMD raw gridded rainfall {y} (unmodified)",
                         f"Raw IMD 0.25 deg daily gridded rainfall file for {y}, downloaded {meta['download_utc']} from "
                         f"{S.IMD_RF25} (RF25={y}). SHA-256 {meta['sha256']}. Unmodified source file. BWI-V2 M4.3.",
                         stage, "raw")
        meta["release_tag"] = tag
        for f in stage.iterdir():
            shutil.copy(f, imd_dir / f.name)
        write_json(imd_dir / f"imd_raw_{y}.json", meta)
        rec = idx / "history" / "imd-raw" / f"{y}.json"
        rec.parent.mkdir(parents=True, exist_ok=True)
        write_json(rec, {"meta": meta, "checks": checks, "run_id": run_id})
        append_csv(idx, [f"imd-raw-{y}", "published", tag, sha256_file(stage / f"manifest_imd-raw-{y}.json"), "", "", "", now_utc(), run_id])
        commit_index(idx, f"history: IMD raw {y} published ({tag})")
        log.append({"year": y, "status": "published", "release": tag})
    return log


def batch(months: list[str], idx: pathlib.Path, work: pathlib.Path, budget: float, run_id: str,
          dry_run: bool = False) -> dict:
    points = load_points()
    summary = {"run_id": run_id, "started_utc": now_utc(), "budget_counted_calls": budget, "months": {},
               "dry_run": dry_run}
    # IMD file date = window end, so a month's last day needs the next day's (possibly next year's) file
    years = sorted({(d + timedelta(days=1)).year for m in months for d in (month_days(m)[0], month_days(m)[-1])})
    summary["imd"] = ensure_imd(years, work / "imd", idx, work, run_id, dry_run)
    for month in months:
        tag = f"history-{month}"
        st = release_state(tag)
        if st == "published":
            summary["months"][month] = "already published (never overwritten)"
            continue
        if st == "draft":
            sh("gh", "release", "delete", tag, "-y")
        est = month_weight(len(points), len(month_days(month)))
        if S.STATS["om_weighted_calls"] + est > budget:
            summary["months"][month] = f"deferred: run budget ({budget:.0f} counted calls) reached"
            summary["stopped"] = "budget"
            break
        stage = work / f"m-{month}"
        shutil.rmtree(stage, ignore_errors=True)
        try:
            man = build_month(month, stage, work / "imd")
            q = validate_month(stage)
        except S.QuotaExhausted as e:
            summary["months"][month] = f"deferred: Open-Meteo quota ({e})"
            summary["stopped"] = "quota"
            break
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            q = {"month": month, "publishable": False, "problems": [f"build failed: {e}"]}
            man = None
        write_json(stage / f"gap_report_history-{month}.json", q)
        msha = sha256_file(stage / f"manifest_history-{month}.json") if man else ""
        if dry_run:   # no release, no index record: only a clearly labelled dry-run report
            d = idx / "history" / "dryrun" / run_id
            d.mkdir(parents=True, exist_ok=True)
            write_json(d / f"{month}.json", {"DRY_RUN": "nothing was published", "month": month, "manifest": man,
                                             "quality": q})
            summary["months"][month] = ("dry run: would publish" if q["publishable"] else "dry run: would REFUSE: "
                                        + "; ".join(q.get("problems", []))[:300])
            continue
        if not q["publishable"]:
            rec = idx / "history" / "refused" / f"{month}_{run_id}.json"
            rec.parent.mkdir(parents=True, exist_ok=True)
            write_json(rec, {"month": month, "status": "refused", "run_id": run_id, "manifest": man, "quality": q})
            append_csv(idx, [month, "refused", "", msha, "", "", "; ".join(q["problems"])[:150].replace(",", ";"), now_utc(), run_id])
            commit_index(idx, f"history: refused {month} (run {run_id})")
            summary["months"][month] = "refused: " + "; ".join(q["problems"])[:300]
            continue
        checks = publish(tag, f"Historical forecast/reference dataset {month} (reconstruction, run time unknown)",
                         f"Matched historical dataset for {month}: Open-Meteo Previous Runs reconstruction "
                         f"(run_time_known = false, nominal previous_dayN leads; NOT an exact forecast-run archive) "
                         f"with ERA5 reanalysis, IMD gauge analysis and METAR (matched stations only). "
                         f"Status: {q['status']} ({q['values_available']}/{q['expected_values']} forecast values). "
                         f"Manifest and quality report are committed to the archive-index branch. No skill scores.",
                         stage, "forecasts")
        url = sh("gh", "release", "view", tag, "--json", "url", "-q", ".url").stdout.strip()
        rec = idx / "history" / "index" / f"{month}.json"
        if rec.exists():
            raise RuntimeError(f"refusing to overwrite index record {rec}")
        rec.parent.mkdir(parents=True, exist_ok=True)
        write_json(rec, {"month": month, "status": "published", "tag": tag, "release_url": url, "run_id": run_id,
                         "manifest_sha256": msha, "gap_report_sha256": sha256_file(stage / f"gap_report_history-{month}.json"),
                         "manifest": man, "quality": q, "checks": checks})
        append_csv(idx, [month, "published", tag, msha, q["expected_values"], q["values_available"], q["status"], now_utc(), run_id])
        commit_index(idx, f"history: published {month} ({tag})")
        summary["months"][month] = f"published ({q['status']}, {q['values_available']}/{q['expected_values']})"
        shutil.rmtree(stage, ignore_errors=True)
    summary["http"] = dict(S.STATS)
    summary["finished_utc"] = now_utc()
    rec = idx / "history" / ("dryrun" if dry_run else "runs") / (f"{run_id}/summary.json" if dry_run else f"{run_id}.json")
    rec.parent.mkdir(parents=True, exist_ok=True)
    write_json(rec, summary)
    commit_index(idx, f"history: {'DRY RUN ' if dry_run else ''}batch run {run_id}")
    return summary


# ================================================================== aggregate quality report
OLD_LABEL_CATEGORY = {   # m4.3-1 gap-report labels (batch 1) -> category, before annotations
    "not provided by source (structural)": "A", "source hours missing": "C", "source returned nothing (unexpected)": "C"}


def month_categories(rec: dict, annotations: list[dict]) -> tuple[dict, list]:
    """Forecast missing-value counts by category A-G for one published month, with annotations applied.
    Annotations only relabel counts; they never change data. A hash mismatch is reported, not applied."""
    q = rec["quality"]
    if "missing_by_category" in q:
        cats = Counter({k: v for k, v in q["missing_by_category"].items()})
    else:
        cats = Counter()
        for label, n in q["missing_by_reason"].items():
            cats[OLD_LABEL_CATEGORY.get(label, "C")] += n
    notes = []
    for a in annotations:
        if a["release"] != rec["tag"]:
            continue
        if a["manifest_sha256"] != rec["manifest_sha256"]:
            notes.append({"annotation": a["id"], "applied": False, "problem": "manifest SHA-256 differs from index record"})
            continue
        r = a["reclassify"]
        if cats[r["from"]] < r["rows"]:
            notes.append({"annotation": a["id"], "applied": False, "problem": "more rows than the source category holds"})
            continue
        cats[r["from"]] -= r["rows"]
        cats[r["to"]] += r["rows"]
        notes.append({"annotation": a["id"], "applied": True, "rows": r["rows"], "from": r["from"], "to": r["to"]})
    return {k: v for k, v in sorted(cats.items()) if v}, notes


def aggregate(idx: pathlib.Path, months_scope: list[str]) -> dict:
    recs = {p.stem: json.loads(p.read_text()) for p in sorted((idx / "history" / "index").glob("*.json"))}
    ann_dir = idx / "history" / "annotations"
    annotations = [json.loads(p.read_text()) for p in sorted(ann_dir.glob("*.json"))] if ann_dir.exists() else []
    by_cat, cat_by_month, ann_notes = Counter(), {}, []
    refused = [p.name for p in sorted((idx / "history" / "refused").glob("*.json"))] if (idx / "history" / "refused").exists() else []
    tot = Counter()
    by = {k: defaultdict(Counter) for k in ("missing_by_model", "missing_by_variable", "missing_by_lead", "missing_by_location")}
    reasons, refcov, metar, imd, anomalies, sizes, manifests, align = Counter(), defaultdict(Counter), {}, defaultdict(Counter), [], Counter(), {}, {}
    failures = []
    for p in (sorted((idx / "history" / "refused").glob("*.json")) if (idx / "history" / "refused").exists() else []):
        r = json.loads(p.read_text())
        failures.append({"attempt": p.stem, "problems": r["quality"].get("problems", [])})
    for m, r in recs.items():
        q, man = r["quality"], r["manifest"]
        mc, notes = month_categories(r, annotations)
        cat_by_month[m] = mc
        by_cat.update(mc)
        ann_notes += [{"month": m, **n} for n in notes]
        tot.update({"expected": q["expected_values"], "available": q["values_available"], "rows": q["rows_stored"],
                    "matched_rows": q["matched_rows"], "reference_rows": q["reference_rows"]})
        for k in by:
            for key, v in q[k].items():
                by[k][key].update(v)
        reasons.update(q["missing_by_reason"])
        for key, v in q["reference_coverage"].items():
            refcov[key].update({"expected": v["expected"], "available": v["available"]})
            refcov[key].update({f"reason: {rk}": rv for rk, rv in v["reasons"].items()})
        for pid, v in q["metar_by_point"].items():
            metar.setdefault(pid, {**{k: v[k] for k in ("station", "distance_km", "elev_diff_m", "matched", "reason_not_matched")},
                                   "days": 0, "days_available": 0})
            metar[pid]["days"] += v["days"]
            metar[pid]["days_available"] += v["days_available"]
        for pid, v in q["imd_by_point"].items():
            imd[pid].update({"days": v["days"], "available": v["available"]})
        anomalies += [{"month": m, **a} for a in q.get("anomalies", [])]
        align[m] = {"best_lag": q["imd_alignment"]["best_lag"],
                    "r": {k: v["pearson_r"] for k, v in q["imd_alignment"]["results"].items()}}
        for f in man["files"]:
            sizes[f["kind"]] += f["bytes"]
        manifests[m] = {"tag": r["tag"], "manifest_sha256": r["manifest_sha256"], "release_url": r["release_url"],
                        "files": {f["name"]: f["sha256"] for f in man["files"]}}
    done = sorted(recs)
    missing_months = [m for m in months_scope if m not in recs]
    exp_all = tot["expected"]
    return {
        "generated_utc": now_utc(), "scope_months": months_scope, "published_months": done,
        "months_not_published": missing_months, "refused_attempts": refused,
        "dataset_status": ("partial" if missing_months or tot["available"] < exp_all else "complete"),
        "status_explanation": ("complete only if every scoped month is published AND every expected forecast value "
                               "is available; the job finishing does not make it complete"),
        "expected_values": exp_all, "rows_stored": tot["rows"], "values_available": tot["available"],
        "values_missing": exp_all - tot["available"], "missing_by_reason": dict(reasons),
        "missing_by_category": dict(sorted(by_cat.items())), "missing_by_category_by_month": cat_by_month,
        "category_legend": CATEGORIES, "annotations_applied": ann_notes,
        **{k: {kk: dict(vv) for kk, vv in v.items()} for k, v in by.items()},
        "reference_coverage": {k: dict(v) for k, v in refcov.items()}, "metar_by_point": metar,
        "imd_by_point": {k: dict(v) for k, v in imd.items()}, "anomalies": anomalies, "imd_alignment_by_month": align, "refused_attempt_problems": failures,
        "storage_bytes": dict(sizes), "matched_rows": tot["matched_rows"], "reference_rows": tot["reference_rows"],
        "manifests": manifests,
    }


def month_range(first: str, last: str) -> list[str]:
    y, m = map(int, first.split("-"))
    out = []
    while f"{y:04d}-{m:02d}" <= last:
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    a1 = sp.add_parser("month"); a1.add_argument("--month", required=True); a1.add_argument("--out", required=True); a1.add_argument("--imd-dir", required=True)
    a2 = sp.add_parser("validate"); a2.add_argument("stage")
    a3 = sp.add_parser("batch"); a3.add_argument("--months-file", required=True); a3.add_argument("--index", required=True)
    a3.add_argument("--work", required=True); a3.add_argument("--budget", type=float, default=7000); a3.add_argument("--run-id", default="local")
    a3.add_argument("--dry-run", action="store_true"); a3.add_argument("--only", default="", help="comma list of months")
    a4 = sp.add_parser("quality"); a4.add_argument("--index", required=True); a4.add_argument("--months-file", required=True); a4.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.cmd == "month":
        print(json.dumps(build_month(a.month, pathlib.Path(a.out), pathlib.Path(a.imd_dir)), default=str)[:3000])
        return 0
    if a.cmd == "validate":
        q = validate_month(pathlib.Path(a.stage))
        print(json.dumps(q, default=str, indent=1)[:4000])
        return 0 if q["publishable"] else 1
    spec = json.loads(pathlib.Path(a.months_file).read_text())
    months = month_range(spec["first"], spec["last"])
    if a.cmd == "batch":
        if a.only:
            only = a.only.split(",")
            if not set(only) <= set(months):
                raise SystemExit(f"--only months outside the approved scope: {sorted(set(only) - set(months))}")
            months = [m for m in months if m in only]
        s = batch(months, pathlib.Path(a.index), pathlib.Path(a.work), a.budget, a.run_id, a.dry_run)
        print(json.dumps(s, default=str, indent=1))
        return 1 if any(v.startswith(("refused", "dry run: would REFUSE")) for v in s["months"].values()) else 0
    rep = aggregate(pathlib.Path(a.index), months)
    write_json(pathlib.Path(a.out), rep)
    print(json.dumps({k: rep[k] for k in ("dataset_status", "expected_values", "values_available", "values_missing",
                                          "published_months", "months_not_published")}, default=str, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
