"""M4.2 feasibility probe for the historical verification dataset. SMALL by design: no full backfill.

Steps (all public, free tier, paced under Open-Meteo's limits):
  1. Daily coverage matrix at one point (Ahmedabad): model x variable x lead 1..7 x IST day, Jan 2024 -> recent
     (plus GFS back to Mar 2021 to document its temperature-only period). Hours present per IST day.
  2. Sample backfill for the 36 fixed points: July 2024 and January 2025, the three archive models, the
     variables/leads the matrix shows. Explicit expectation + backfill report (complete / partial).
  3. ERA5 (reanalysis) for the same points and months.
  4. METAR: nearest-station pairing for the 36 points; daily values for stations within 50 km.
  5. IMD 0.25 deg rainfall 2024 and 2025 (and whether 2026 is offered): point extraction with the 30 km rule.
  6. IMD date-convention diagnostic (IMD vs ERA5 at lag -1/0/+1) — a data-alignment check, not verification.
  7. Probe report: requests, weighted calls, rate limits, bytes, rows, projections for the full backfill.
Writes only to --out.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import tempfile
import time
import traceback
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sources as S  # noqa: E402
from build import (hours_present, imd_rows, metar_daily, pair_stations, rows_from_era5,  # noqa: E402,F401
                   rows_from_previous_runs)
from common import (BACKFILL_HOURLY, HIST_SCHEMA, HOURLY, LEADS, REF_SCHEMA, aggregate_daily,  # noqa: E402
                    backfill_report, date_range, haversine_km, load_points, om_weight, parse_hourly_times,
                    sha256_bytes, sha256_file, utc_request_range, validate_history_rows, validate_reference_rows,
                    write_json)

MATRIX_POINT = {"id": "ahmedabad", "lat": 23.0225, "lon": 72.5714}
MATRIX_MODELS = ["ecmwf_ifs025", "gfs_seamless", "gfs_global", "icon_seamless", "icon_global"]
MATRIX_HOURLY = ["temperature_2m", "precipitation", "wind_gusts_10m", "cape"]
# archive model -> Open-Meteo ids to try, in order. The first is the prospective archive's own id; the second is
# CORE's id, identical over India on the current forecast API (Step 1). Any use of the second is recorded per row.
BACKFILL_MODELS = {"ecmwf_ifs025": ["ecmwf_ifs025"], "gfs_global": ["gfs_global", "gfs_seamless"],
                   "icon_global": ["icon_global", "icon_seamless"]}
SAMPLE_MONTHS = [(date(2024, 7, 1), date(2024, 7, 31)), (date(2025, 1, 1), date(2025, 1, 31))]
IMD_YEARS = [2024, 2025, 2026]
IMD_REQUIRED = {2024, 2025}          # a failure here is a problem; 2026 not yet published is a finding
IMD_MAX_KM = 30.0                       # decision B4
METAR_PAIR_KM, METAR_PAIR_DELEV = 25.0, 100.0   # PROPOSED pairing rule (needs approval)
METAR_FETCH_KM = 50.0                   # probe fetches a superset so the effect of the rule is visible
BACKFILL_START = date(2024, 2, 1)       # earliest month with any ECMWF data (Step 1); projection only
MATRIX_START = date(2024, 1, 1)
GFS_EARLY_START = date(2021, 3, 1)      # documents GFS's earlier temperature-only period; not backfilled


def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0)


def month_chunks(d1: date, d2: date):
    d = d1
    while d <= d2:
        nxt = (d.replace(day=28) + timedelta(days=4)).replace(day=1)
        yield d, min(d2, nxt - timedelta(days=1))
        d = nxt


# ------------------------------------------------------------------ 1. coverage matrix
def coverage_matrix(begin: date, end: date, log):
    rows, errors = [], []
    plans = [(m, begin) for m in MATRIX_MODELS] + ([("gfs_seamless", GFS_EARLY_START)] if GFS_EARLY_START else [])
    for model, start in plans:
        stop = end if start >= begin else begin - timedelta(days=1)
        for c1, c2 in month_chunks(start, stop):
            u1, u2 = utc_request_range(c1, c2)
            try:
                resp, _ = S.previous_runs([MATRIX_POINT], model, MATRIX_HOURLY, LEADS, u1, u2)
            except Exception as e:  # noqa: BLE001 — recorded, never filled
                errors.append({"model": model, "chunk": str(c1), "error": str(e)[:300]})
                continue
            h = resp[0].get("hourly") or {}
            times = parse_hourly_times(h.get("time", []))
            days = date_range(c1, c2)
            for var in MATRIX_HOURLY:
                for n in LEADS:
                    vals = h.get(f"{var}_previous_day{n}") or [None] * len(times)
                    for d, _, npres in aggregate_daily(times, vals, "max", "ist_day", days):
                        rows.append((model, var, n, d, npres))
        log(f"matrix {model} from {start}: done")
    df = pd.DataFrame(rows, columns=["om_model", "hourly_variable", "lead", "valid_date_ist", "hours_present"])
    return df, errors


def summarise_matrix(df: pd.DataFrame):
    out = []
    for (m, v, n), g in df.groupby(["om_model", "hourly_variable", "lead"]):
        g = g.sort_values("valid_date_ist")
        ok = g[g["hours_present"] == 24]["valid_date_ist"].tolist()
        first, last = (ok[0], ok[-1]) if ok else (None, None)
        gaps = []
        if ok:
            span = g[(g["valid_date_ist"] >= first) & (g["valid_date_ist"] <= last)]
            bad = span[span["hours_present"] < 24]["valid_date_ist"].tolist()
            for d in bad:   # group consecutive days
                if gaps and (d - gaps[-1][1]).days == 1:
                    gaps[-1][1] = d
                else:
                    gaps.append([d, d])
        out.append({"om_model": m, "hourly_variable": v, "lead": int(n), "days_checked": len(g),
                    "first_complete_day": first, "last_complete_day": last, "complete_days": len(ok),
                    "incomplete_days_inside_span": sum((b - a).days + 1 for a, b in gaps),
                    "gaps": [f"{a}..{b}" if a != b else str(a) for a, b in gaps][:40],
                    "partial_hour_days": int(((g["hours_present"] > 0) & (g["hours_present"] < 24)).sum())})
    return out


def monthly(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["month"] = pd.to_datetime(d["valid_date_ist"]).dt.strftime("%Y-%m")
    d["complete"] = d["hours_present"] == 24
    return (d.groupby(["om_model", "hourly_variable", "lead", "month"])
            .agg(days=("complete", "size"), complete_days=("complete", "sum")).reset_index())


# ------------------------------------------------------------------ 2. sample backfill
def choose_om_model(archive_model: str, dfm: pd.DataFrame, c1: date, c2: date):
    tried = []
    for om in BACKFILL_MODELS[archive_model]:
        g = dfm[(dfm.om_model == om) & (dfm.hourly_variable == "temperature_2m") & (dfm.lead == 1)
                & (dfm.valid_date_ist >= c1) & (dfm.valid_date_ist <= c2)]
        n = int((g.hours_present == 24).sum())
        tried.append({"om_model": om, "complete_days_at_matrix_point": n})
        if n:
            return om, tried
    return None, tried


def expectation(archive_model, om, dfm, c1, c2, points):
    """Expected (variable, lead, days) = exactly the IST days on which the one-point matrix found 24 hours."""
    exp, not_provided = [], []
    for var in BACKFILL_HOURLY:
        for n in LEADS:
            g = dfm[(dfm.om_model == om) & (dfm.hourly_variable == var) & (dfm.lead == n)
                    & (dfm.valid_date_ist >= c1) & (dfm.valid_date_ist <= c2)]
            days = sorted(g[g.hours_present == 24].valid_date_ist.tolist())
            if not days:
                not_provided.append({"model": archive_model, "om_model": om, "hourly_variable": var, "lead": n,
                                     "period": f"{c1}..{c2}"})
                continue
            for dv, *_ in HOURLY[var]:
                exp.append({"model": archive_model, "variable": dv, "nominal_lead_day": n,
                            "points": [p["id"] for p in points], "days": days})
    return exp, not_provided


# ------------------------------------------------------------------ helpers
def write_table(rows, schema, path):
    t = pa.Table.from_pylist(rows, schema=schema)
    pq.write_table(t, path, compression="zstd")
    return t.num_rows, path.stat().st_size


def corr(a, b):
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 30 or np.std(a[m]) == 0 or np.std(b[m]) == 0:
        return None, int(m.sum())
    return round(float(np.corrcoef(a[m], b[m])[0, 1]), 3), int(m.sum())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--skip", default="", help="comma list of steps to skip (matrix,sample,era5,metar,imd)")
    ap.add_argument("--matrix-end", default="", help="last IST day of the coverage matrix (default: today - 8 days)")
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    skip = set(filter(None, a.skip.split(",")))
    points = load_points()
    T0 = time.time()
    R = {"schema_version": 1, "started_utc": now_utc(), "kind": "M4.2 historical/reference feasibility probe (small)",
         "steps": {}, "problems": [], "files": []}
    today = datetime.now(timezone.utc).date()
    matrix_end = date.fromisoformat(a.matrix_end) if a.matrix_end else today - timedelta(days=8)

    def log(msg):
        print(f"[{time.time() - T0:7.0f}s] {msg}", flush=True)

    def step(name, fn):
        if name in skip:
            R["steps"][name] = {"skipped": True}
            return None
        t, s0 = time.time(), dict(S.STATS)
        try:
            res = fn()
            ok = True
        except Exception as e:  # noqa: BLE001 — a failed step is reported, never hidden
            res, ok = None, False
            R["problems"].append(f"step {name} failed: {e}")
            traceback.print_exc()
        R["steps"].setdefault(name, {}).update({
            "ok": ok, "secs": round(time.time() - t),
            "requests": S.STATS["requests"] - s0["requests"],
            "om_requests": S.STATS["om_requests"] - s0["om_requests"],
            "om_weighted_calls": round(S.STATS["om_weighted_calls"] - s0["om_weighted_calls"], 1),
            "rate_limited": S.STATS["rate_limited"] - s0["rate_limited"],
            "bytes_downloaded": S.STATS["bytes"] - s0["bytes"]})
        log(f"step {name}: {'ok' if ok else 'FAILED'}")
        return res

    # 1. matrix
    ctx = {}

    def do_matrix():
        dfm, errs = coverage_matrix(MATRIX_START, matrix_end, log)
        ctx["dfm"] = dfm
        # a 400 = the source rejects that model id (a finding); anything else = a gap in the probe itself
        R["problems"] += [f"matrix chunk failed: {e}" for e in errs if "HTTP 400" not in e["error"]]
        R["unsupported_model_ids"] = sorted({e["model"] for e in errs if "HTTP 400" in e["error"]})
        dfm.to_parquet(out / "coverage_daily_one_point.parquet", index=False)
        monthly(dfm).to_csv(out / "coverage_monthly.csv", index=False)
        summ = summarise_matrix(dfm)
        write_json(out / "coverage_summary.json", {"point": MATRIX_POINT, "through": matrix_end, "rows": summ,
                                                   "errors": errs})
        R["steps"]["matrix"] = {"errors": errs, "through": str(matrix_end)}
        return summ

    summ = step("matrix", do_matrix)

    # 2. sample backfill
    def do_sample():
        dfm = ctx["dfm"]
        rows, expected, notprov, choices = [], [], [], []
        for c1, c2 in SAMPLE_MONTHS:
            u1, u2 = utc_request_range(c1, c2)
            for am in BACKFILL_MODELS:
                om, tried = choose_om_model(am, dfm, c1, c2)
                choices.append({"model": am, "period": f"{c1}..{c2}", "om_model": om, "tried": tried,
                                "substituted": om is not None and om != BACKFILL_MODELS[am][0]})
                if om is None:
                    notprov.append({"model": am, "period": f"{c1}..{c2}", "reason": "no data at the matrix point"})
                    continue
                exp, np_ = expectation(am, om, dfm, c1, c2, points)
                expected += exp
                notprov += np_
                resp, url = S.previous_runs(points, om, BACKFILL_HOURLY, LEADS, u1, u2)
                rows += rows_from_previous_runs(resp, points, am, om, BACKFILL_HOURLY, LEADS, date_range(c1, c2),
                                                url, now_utc())
                log(f"sample {am} ({om}) {c1:%Y-%m}: {len(rows)} rows so far")
        n, size = write_table(rows, HIST_SCHEMA, out / "historical_sample.parquet")
        df = pq.read_table(out / "historical_sample.parquet").to_pandas()
        probs = validate_history_rows(df)
        rep = backfill_report(df, expected)
        rep.update({"model_choice": choices, "not_provided_by_source": notprov, "validation_problems": probs})
        write_json(out / "backfill_report_sample.json", rep)
        if probs:
            R["problems"] += [f"historical sample: {p}" for p in probs]
        # per model / lead / variable completeness table
        df["month"] = pd.to_datetime(df["valid_date_ist"]).dt.strftime("%Y-%m")
        tab = (df.groupby(["month", "model", "om_model", "variable", "nominal_lead_day"])
               .agg(rows=("complete", "size"), complete=("complete", "sum")).reset_index())
        tab.to_csv(out / "sample_completeness.csv", index=False)
        R["steps"]["sample"] = {"rows": n, "bytes": size, "bytes_per_row": round(size / max(n, 1), 2),
                                "status": rep["status"], "expected_values": rep["expected_values"],
                                "complete_values": rep["complete_values"], "model_choice": choices}
        ctx["hist"] = df

    step("sample", do_sample)

    # 3. ERA5
    def do_era5():
        rows, elev = [], {}
        hourly = ["temperature_2m", "precipitation", "wind_gusts_10m"]
        for c1, c2 in SAMPLE_MONTHS:
            u1, u2 = utc_request_range(c1, c2)
            resp, url = S.era5(points, hourly, u1, u2)
            for p, r in zip(points, resp):
                elev[p["id"]] = r.get("elevation")
            rows += rows_from_era5(resp, points, hourly, date_range(c1, c2), url, now_utc())
        ctx["elev"] = elev
        ctx["era5_rows"] = rows
        R["steps"]["era5"] = {"rows": len(rows), "complete": sum(r["complete"] for r in rows)}

    step("era5", do_era5)

    # 4. METAR
    def do_metar():
        stations = S.iem_stations()
        elev = ctx.get("elev", {})
        pairs = pair_stations(points, stations, elev, METAR_PAIR_KM, METAR_PAIR_DELEV)
        write_json(out / "metar_pairing.json", {"rule_proposed": {"max_km": METAR_PAIR_KM, "max_abs_elev_diff_m":
                                                                 METAR_PAIR_DELEV}, "stations_in_network": len(stations),
                                                "point_elevation_source": "Open-Meteo archive API elevation (90 m DEM)",
                                                "pairs": pairs})
        rows = []
        for pr in pairs:
            if pr["distance_km"] > METAR_FETCH_KM:
                continue
            p = next(x for x in points if x["id"] == pr["point_id"])
            for c1, c2 in SAMPLE_MONTHS:
                try:
                    obs, url = S.iem_metar(pr["station"], c1 - timedelta(days=1), c2 + timedelta(days=1))
                except Exception as e:  # noqa: BLE001
                    R["problems"].append(f"METAR {pr['station']} {c1:%Y-%m}: {e}")
                    continue
                rows += metar_daily(obs, pr, p, date_range(c1, c2), url.split("&year1")[0], now_utc())
                time.sleep(1)
        ctx["metar_rows"] = rows
        R["steps"]["metar"] = {"stations_in_network": len(stations), "points_paired_under_proposed_rule":
                               sum(x["paired"] for x in pairs), "points_with_station_within_fetch_km":
                               sum(x["distance_km"] <= METAR_FETCH_KM for x in pairs), "rows": len(rows)}

    step("metar", do_metar)

    # 5. IMD
    def do_imd():
        import xarray as xr
        rows, years = [], []
        want = {d for c1, c2 in SAMPLE_MONTHS for d in date_range(c1, c2)}
        for y in IMD_YEARS:
            rec = {"year": y}
            try:
                t = time.time()
                body = S.imd_year(y)
                rec.update(bytes=len(body), secs=round(time.time() - t), sha256=sha256_bytes(body))
                with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as f:
                    f.write(body)
                try:
                    ds = xr.open_dataset(f.name)
                    r, info, meta = imd_rows(ds, points, IMD_MAX_KM, S.IMD_RF25 + f" RF25={y}", rec["sha256"],
                                             now_utc(), want)
                    rows += r
                    rec.update(ok=True, **meta)
                    if y == IMD_YEARS[0]:
                        write_json(out / "imd_point_cells.json", {"max_km": IMD_MAX_KM, "points": info})
                    ds.close()
                except Exception as e:  # noqa: BLE001 — e.g. year not published: body is not NetCDF
                    rec.update(ok=False, reason=f"not a readable IMD NetCDF: {str(e)[:200]}",
                               head=body[:120].decode(errors="replace"))
                pathlib.Path(f.name).unlink(missing_ok=True)
            except Exception as e:  # noqa: BLE001
                rec.update(ok=False, reason=str(e)[:300])
            years.append(rec)
            log(f"IMD {y}: {rec.get('ok')}")
        ctx["imd_rows"] = rows
        R["steps"]["imd"] = {"years": years, "rows": len(rows)}
        failed = sorted(y["year"] for y in years if y["year"] in IMD_REQUIRED and not y.get("ok"))
        if failed:   # never a silent partial: the sample months need these files
            R["problems"].append(f"IMD years {failed} could not be obtained; IMD reference incomplete for those years")

    step("imd", do_imd)

    # reference table + validation
    ref = ctx.get("era5_rows", []) + ctx.get("metar_rows", []) + ctx.get("imd_rows", [])
    if ref:
        n, size = write_table(ref, REF_SCHEMA, out / "reference_sample.parquet")
        rdf = pq.read_table(out / "reference_sample.parquet").to_pandas()
        probs = validate_reference_rows(rdf, IMD_MAX_KM)
        R["problems"] += [f"reference sample: {p}" for p in probs]
        comp = (rdf.assign(month=pd.to_datetime(rdf["valid_date_ist"]).dt.strftime("%Y-%m"))
                .groupby(["reference", "month", "variable"])
                .agg(rows=("complete", "size"), complete=("complete", "sum"), points=("point_id", "nunique"))
                .reset_index())
        comp.to_csv(out / "reference_completeness.csv", index=False)
        R["reference"] = {"rows": n, "bytes": size, "validation_problems": probs}

        # 6. IMD date-convention diagnostic (alignment only)
        try:
            e = rdf[(rdf.reference == "era5") & (rdf.variable == "precip_0830")]
            i = rdf[(rdf.reference == "imd_rf025") & (rdf.variable == "precip_0830")]
            m = i.merge(e, on=["point_id", "valid_date_ist"], suffixes=("_imd", "_era5"))
            diag = {}
            for lag in (-1, 0, 1):
                e2 = e.copy()
                e2["valid_date_ist"] = pd.to_datetime(e2["valid_date_ist"]) + pd.Timedelta(days=lag)
                e2["valid_date_ist"] = e2["valid_date_ist"].dt.date
                mm = i.merge(e2, on=["point_id", "valid_date_ist"], suffixes=("_imd", "_era5"))
                c, nn = corr(mm["value_imd"].to_numpy(float), mm["value_era5"].to_numpy(float))
                diag[f"era5_shifted_{lag:+d}_day"] = {"pearson_r": c, "pairs": nn}
            best = max((k for k in diag if diag[k]["pearson_r"] is not None), key=lambda k: diag[k]["pearson_r"], default=None)
            if best != "era5_shifted_+0_day":
                R["problems"].append(f"IMD date alignment check: best match is {best}, expected +0 after alignment")
            R["imd_date_convention_check"] = {
                "best": best, "what": "Correlation of IMD daily rain (stored valid date D, after alignment) with ERA5 08:30->08:30 IST rain starting on D+lag, "
                        "36 points, sample months. The lag with the highest r shows how IMD file dates align. "
                        "A data-alignment diagnostic only; NOT forecast verification.",
                "results": diag, "pairs_same_day": len(m)}
        except Exception as ex:  # noqa: BLE001
            R["problems"].append(f"date check failed: {ex}")

    # 7. projections for the full backfill (not run)
    if "dfm" in ctx and "sample" in R["steps"] and R["steps"]["sample"].get("rows"):
        end = matrix_end
        months = list(month_chunks(BACKFILL_START, end))
        n_days = sum((b - a).days + 1 for a, b in months)
        vars_hourly = len(BACKFILL_HOURLY) * len(LEADS)
        w_prev = sum(om_weight(len(points), vars_hourly, (b - a).days + 3) for a, b in months) * len(BACKFILL_MODELS)
        w_era5 = sum(om_weight(len(points), 3, (b - a).days + 3) for a, b in months)
        sample_rows = R["steps"]["sample"]["rows"]
        sample_days = sum((b - a).days + 1 for a, b in SAMPLE_MONTHS)
        rows_full = sample_rows / sample_days * n_days
        R["projection_full_backfill"] = {
            "period": f"{BACKFILL_START}..{end}", "months": len(months), "ist_days": n_days,
            "points": len(points), "models": list(BACKFILL_MODELS),
            "previous_runs_requests": len(months) * len(BACKFILL_MODELS),
            "previous_runs_weighted_calls": round(w_prev), "era5_requests": len(months),
            "era5_weighted_calls": round(w_era5),
            "free_tier_limits": {"per_minute": 600, "per_hour": 5000, "per_day": 10000, "per_month": 300000},
            "min_days_at_free_daily_limit": round((w_prev + w_era5) / 10000, 2),
            "hours_at_paced_4000_per_hour": round((w_prev + w_era5) / 4000, 1),
            "historical_rows": round(rows_full),
            "historical_parquet_mb": round(rows_full * R["steps"]["sample"]["bytes_per_row"] / 1e6, 1),
            "metar_requests": sum(1 for _ in months) * R["steps"].get("metar", {}).get(
                "points_with_station_within_fetch_km", 0),
            "imd_files": sorted({a.year for a, _ in months}),
            "note": "Rows include days that are stored incomplete (value null); these are expected, not failures.",
        }
    R["counters"] = dict(S.STATS)
    R["finished_utc"] = now_utc()
    R["secs"] = round(time.time() - T0)
    R["summary_matrix"] = summ
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name != "probe_report.json":
            R["files"].append({"name": p.name, "bytes": p.stat().st_size, "sha256": sha256_file(p)})
    write_json(out / "probe_report.json", R)
    log(f"done: problems={len(R['problems'])}")
    print(json.dumps({k: R[k] for k in ("steps", "problems", "counters")}, indent=1, default=str)[:6000])
    return 0 if not R["problems"] else 2


if __name__ == "__main__":
    sys.exit(main())
