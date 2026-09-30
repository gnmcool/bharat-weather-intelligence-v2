"""Collect one day's forecast archive into a staging directory (M4 archive foundation).

Reads only public sources: Open-Meteo (per-model forecasts + model run metadata), CORE's public
Earth2Studio store and CORE's public /api/v1/dashboard. Writes only to --out. Publishing is a
separate step (publish.sh) that runs only after validate.py passes.

Outputs in --out:
  forecasts_<D>.parquet      exact-run model forecasts at the 36 fixed points (FORECAST_SCHEMA)
  core_risks_<D>.parquet     CORE risk items as CORE showed them (prospective CORE-level record)
  core_daily_<D>.parquet     CORE best-match daily values as shown (a blend: no single model run)
  e2s_gfs_grid_<cycle>.nc    Earth2Studio GFS daily grid (IST days), as in M0
  gap_report_<D>.json        what was expected, present, missing, not provided by the source
  manifest_<D>.json          files, SHA-256, rows, sources, run times, expectation spec
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import xarray as xr

from common import (CORE_DAILY_SCHEMA, CORE_RISK_SCHEMA, DAILY_VARS, FORECAST_SCHEMA, HERE, IST, SCHEMA_VERSION, flood_wet_soil_flag,
                    ArchiveError, day_fully_covered, lead_day, sha256, write_json)

OPEN_METEO = "https://api.open-meteo.com/v1/forecast"
OM_META = "https://api.open-meteo.com/data/{}/static/meta.json"
CORE_API = "https://bharat-weather-intelligence-brown.vercel.app/api/v1"
CORE_STORE_URL = "https://github.com/gnmcool/bharat-weather-intelligence/releases/download/forecast/gfs_latest.nc"
FORECAST_DAYS = 10

# Archive model -> (Open-Meteo forecast model id, Open-Meteo metadata ids that must all report the same run,
# variables the source provides). From the M4 Step 1 probe (27 Sep 2026, GitHub Actions):
#   ecmwf_ifs025 = CORE's ECMWF; all four daily variables present
#   gfs_global  = CORE's gfs_seamless over India (identical values); built from the GFS 0.11 and 0.25 grids, so both
#                 metadata files must report the same initialisation. (`gfs025` alone returned no temperature/rain.)
#   icon_global = CORE's icon_seamless over India (identical values); ~7.5-day range
MODELS = {
    "ecmwf_ifs025": ("ecmwf_ifs025", ["ecmwf_ifs025"], ["tmax", "tmin", "precip", "gust_max"]),
    "gfs_global": ("gfs_global", ["ncep_gfs013", "ncep_gfs025"], ["tmax", "tmin", "precip", "gust_max"]),
    "icon_global": ("icon_global", ["dwd_icon"], ["tmax", "tmin", "precip", "gust_max"]),
}

STATS = {"requests": 0, "retries": 0, "rate_limited": 0, "http_errors": 0, "network_errors": 0}


def http_json(url: str, timeout: int = 90, tries: int = 4):
    last = None
    for a in range(tries):
        STATS["requests"] += 1
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "BWI-V2-archive/2"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            body = e.read()[:300].decode(errors="replace")
            last = f"HTTP {e.code}: {body}"
            if e.code == 429 or "limit" in body.lower():
                STATS["rate_limited"] += 1
            else:
                STATS["http_errors"] += 1
                if 400 <= e.code < 500:
                    break
        except Exception as e:  # noqa: BLE001 — network: retry with backoff
            STATS["network_errors"] += 1
            last = f"{type(e).__name__}: {e}"
        STATS["retries"] += 1
        time.sleep(min(60, 5 * 2 ** a))
    raise ArchiveError(f"{url.split('?')[0]} failed after retries: {last}")


def parse_ts(v) -> datetime:
    if isinstance(v, (int, float)):
        return datetime.fromtimestamp(v, tz=timezone.utc)
    return datetime.fromisoformat(str(v).replace("Z", "+00:00"))


def model_meta(meta_ids: list[str]) -> dict:
    """Run metadata; when a model is built from several grids, all must report the same initialisation."""
    ms = [http_json(OM_META.format(i)) for i in meta_ids]
    inits = {m["last_run_initialisation_time"] for m in ms}
    if len(inits) != 1:
        return {"run_time_utc": None, "inits": sorted(inits)}
    return {"run_time_utc": parse_ts(ms[0]["last_run_initialisation_time"]),
            "data_end_utc": min(parse_ts(m["data_end_time"]) for m in ms),
            "available_utc": max(parse_ts(m["last_run_availability_time"]) for m in ms),
            "step_hours": max(int(m["temporal_resolution_seconds"] // 3600) for m in ms)}


def fetch_model(arch_model: str, pts: list[dict], retrieved: datetime) -> tuple[list[dict], dict]:
    om_model, meta_ids, variables = MODELS[arch_model]
    q = urllib.parse.urlencode({
        "latitude": ",".join(str(p["lat"]) for p in pts), "longitude": ",".join(str(p["lon"]) for p in pts),
        "daily": ",".join(DAILY_VARS), "models": om_model, "timezone": "Asia/Kolkata",
        "forecast_days": FORECAST_DAYS, "wind_speed_unit": "kmh"})
    for attempt in range(3):
        before = model_meta(meta_ids)
        data = http_json(f"{OPEN_METEO}?{q}")
        after = model_meta(meta_ids)
        if before["run_time_utc"] is not None and before["run_time_utc"] == after["run_time_utc"]:
            break
        STATS["retries"] += 1  # a run landed during the request, or the grids disagree: run time would be ambiguous
        time.sleep(120)
    else:
        raise ArchiveError(f"{arch_model}: exact run time could not be established (run changed or grids disagree)")
    data = data if isinstance(data, list) else [data]
    if len(data) != len(pts):
        raise ArchiveError(f"{arch_model}: {len(data)} locations returned for {len(pts)} points")
    run, end, step = before["run_time_utc"], before["data_end_utc"], before["step_hours"]
    rows = []
    for p, d in zip(pts, data):
        daily = d.get("daily") or {}
        for i, ds in enumerate(daily.get("time", [])):
            vd = date.fromisoformat(ds)
            full = day_fully_covered(vd, run, end, step)
            for om_var, (var, unit) in DAILY_VARS.items():
                v = (daily.get(om_var) or [None] * (i + 1))[i]
                rows.append({"point_id": p["id"], "lat": p["lat"], "lon": p["lon"], "model": arch_model,
                             "source": f"Open-Meteo forecast API, model {om_model}", "source_url": OPEN_METEO,
                             "run_time_utc": run, "run_time_known": True, "valid_date_ist": vd,
                             "lead_day": lead_day(vd, run), "day_partial": not full, "variable": var,
                             "value": None if v is None else float(v), "unit": unit, "retrieved_at_utc": retrieved})
    first = date.fromisoformat(data[0]["daily"]["time"][0])
    dates = [first + timedelta(days=k) for k in range(FORECAST_DAYS)]
    full_leads = sorted({lead_day(d, run) for d in dates if day_fully_covered(d, run, end, step)})
    spec = {"model": arch_model, "open_meteo_model": om_model, "metadata_ids": meta_ids,
            "run_time_utc": run.isoformat(), "run_available_utc": before["available_utc"].isoformat(),
            "data_end_utc": end.isoformat(), "step_hours": step, "variables": variables,
            "expected_leads": full_leads, "points": len(pts)}
    return rows, spec


# ---------------- Earth2Studio (CORE store) ----------------
def e2s(out: pathlib.Path, pts: list[dict], retrieved: datetime, store: pathlib.Path | None):
    src = store or out / "_gfs_latest.nc"
    if store is None:
        req = urllib.request.Request(CORE_STORE_URL, headers={"User-Agent": "BWI-V2-archive/2"})
        with urllib.request.urlopen(req, timeout=600) as r, open(src, "wb") as f:
            while chunk := r.read(1 << 20):
                f.write(chunk)
    ds = xr.open_dataset(src).load()
    issue = parse_ts(str(ds.attrs.get("issue_time", "")))
    ist_day = (ds.time.values + np.timedelta64(19800, "s")).astype("datetime64[D]")
    ds = ds.assign_coords(ist_day=("time", ist_day))
    counts = ds.time.groupby("ist_day").count()
    full = counts.ist_day.values[counts.values >= 8]
    g = ds.sel(time=np.isin(ist_day, full)).groupby("ist_day")
    grid = xr.Dataset({"precip": g.sum("time")["tp"].astype("float32"), "tmax": g.max("time")["t2m"].astype("float32"),
                       "tmin": g.min("time")["t2m"].astype("float32")})
    if "fg10m" in ds:
        grid["gust_max"] = (g.max("time")["fg10m"] * 3.6).astype("float32")
    grid.attrs = {"source": "NOAA GFS 0.25 deg via Earth2Studio (CORE store)", "issue_time": issue.isoformat(),
                  "source_url": CORE_STORE_URL, "retrieved_at": retrieved.isoformat(),
                  "method": "3-hourly store aggregated by IST calendar day; days with < 8 steps dropped"}
    cycle = issue.strftime("%Y%m%d%H")
    grid_path = out / f"e2s_gfs_grid_{cycle}.nc"
    grid.to_netcdf(grid_path, encoding={v: {"zlib": True, "complevel": 5} for v in grid.data_vars})
    lat, lon = grid["lat" if "lat" in grid.coords else "latitude"], grid["lon" if "lon" in grid.coords else "longitude"]
    units = {"precip": "mm", "tmax": "degC", "tmin": "degC", "gust_max": "km/h"}
    rows = []
    for p in pts:
        cell = grid.sel({lat.name: p["lat"], lon.name: p["lon"]}, method="nearest")
        for dd in grid.ist_day.values:
            vd = date.fromisoformat(str(dd)[:10])
            for var in grid.data_vars:
                v = float(cell[var].sel(ist_day=dd).values)
                rows.append({"point_id": p["id"], "lat": p["lat"], "lon": p["lon"], "model": "e2s_gfs025",
                             "source": "Earth2Studio GFS 0.25 deg (CORE store), nearest grid cell", "source_url": CORE_STORE_URL,
                             "run_time_utc": issue, "run_time_known": True, "valid_date_ist": vd, "lead_day": lead_day(vd, issue),
                             "day_partial": False, "variable": var, "value": None if np.isnan(v) else v, "unit": units[var],
                             "retrieved_at_utc": retrieved})
    if store is None:
        src.unlink(missing_ok=True)
    leads = sorted({lead_day(date.fromisoformat(str(d)[:10]), issue) for d in grid.ist_day.values})
    spec = {"model": "e2s_gfs025", "run_time_utc": issue.isoformat(), "variables": list(grid.data_vars),
            "expected_leads": leads, "points": len(pts), "grid_file": grid_path.name}
    return rows, spec, grid_path


# ---------------- CORE snapshot ----------------
def core_snapshot(pts: list[dict], retrieved: datetime):
    def one(p):
        q = urllib.parse.urlencode({"lat": p["lat"], "lon": p["lon"], "name": p["district"]})
        return p, http_json(f"{CORE_API}/dashboard?{q}", timeout=120)

    risks, daily = [], []
    with cf.ThreadPoolExecutor(4) as ex:
        results = list(ex.map(one, pts))
    for p, d in results:
        gen = parse_ts(d["generated_at"])
        runs = next((s.get("notes") for s in d.get("sources", []) if s.get("issue_time")), None)
        alert_ids = json.dumps(sorted(w["id"] for w in d.get("warnings", [])))
        for r in d["risks"]:
            risks.append({"point_id": p["id"], "core_generated_at_utc": gen, "retrieved_at_utc": retrieved, "risk_id": r["id"],
                          "level": r["level"], "status": r.get("status"), "period_start": r.get("period_start"),
                          "period_end": r.get("period_end"), "peak_value": r.get("peak_value"), "unit": r.get("unit"),
                          "agreement_basis": (r.get("confidence") or {}).get("basis"), "official": bool(r.get("official")),
                          "experimental": bool(r.get("experimental")), "reference": r.get("reference"),
                          "official_alert_ids": alert_ids, "model_runs_note": runs,
                          # M4.4-D D1: CORE's rule text verbatim, and flood's wet-soil flag (flood rows only)
                          "criterion": r.get("criterion"),
                          "flood_wet_soil": flood_wet_soil_flag(r.get("explanation")) if r["id"] == "flood" else None})
        for row in d.get("daily", []):
            for k, (var, unit) in DAILY_VARS.items():
                daily.append({"point_id": p["id"], "core_generated_at_utc": gen, "retrieved_at_utc": retrieved,
                              "valid_date_ist": date.fromisoformat(row["date"]), "variable": var,
                              "value": None if row.get(k) is None else float(row[k]), "unit": unit})
    return risks, daily, {"points": len(pts), "risks_per_point": 11, "source": f"{CORE_API}/dashboard"}


def write_table(rows: list[dict], schema: pa.Schema, path: pathlib.Path) -> int:
    t = pa.Table.from_pylist(rows, schema=schema)
    pq.write_table(t, path, compression="zstd")
    return t.num_rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--store", help="local CORE store (tests)")
    ap.add_argument("--inject", choices=["none", "checksum", "missing_row", "bad_lead"], default="none",
                    help="acceptance tests only: introduce one fault; the archive must then be refused")
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    retrieved = datetime.now(timezone.utc).replace(microsecond=0)
    day = retrieved.astimezone(IST).date().isoformat()
    pts = json.loads((HERE / "points.json").read_text())["points"]

    fc_rows, specs, errors = [], [], []
    for m in MODELS:
        try:
            r, s = fetch_model(m, pts, retrieved)
            fc_rows += r
            specs.append(s)
        except ArchiveError as e:
            errors.append(str(e))
    e2s_rows, e2s_spec, grid_path = e2s(out, pts, retrieved, pathlib.Path(a.store) if a.store else None)
    fc_rows += e2s_rows
    specs.append(e2s_spec)
    try:
        core_risks, core_daily, core_spec = core_snapshot(pts, retrieved)
    except ArchiveError as e:
        errors.append(str(e))
        core_risks, core_daily, core_spec = [], [], {"points": len(pts), "risks_per_point": 11, "error": str(e)}

    if a.inject == "missing_row":  # drop one expected (non-null, fully covered) row
        victim = next(i for i, r in enumerate(fc_rows) if not r["day_partial"] and r["value"] is not None and r["lead_day"] >= 1)
        fc_rows.pop(victim)
    if a.inject == "bad_lead":
        fc_rows[0]["lead_day"] += 1

    files = []
    n = write_table(fc_rows, FORECAST_SCHEMA, out / f"forecasts_{day}.parquet")
    files.append(("forecasts", out / f"forecasts_{day}.parquet", n))
    n = write_table(core_risks, CORE_RISK_SCHEMA, out / f"core_risks_{day}.parquet")
    files.append(("core_risks", out / f"core_risks_{day}.parquet", n))
    n = write_table(core_daily, CORE_DAILY_SCHEMA, out / f"core_daily_{day}.parquet")
    files.append(("core_daily", out / f"core_daily_{day}.parquet", n))
    files.append(("e2s_grid", grid_path, None))

    manifest = {
        "schema_version": SCHEMA_VERSION, "archive_date_ist": day, "created_utc": retrieved.isoformat(),
        "producer": {"script": "archive/collect.py", "git_sha": _env("GITHUB_SHA"), "run_url": _run_url(),
                     "test_injection": a.inject},
        "run_time_policy": "forecasts table: run_time_utc is the exact model initialisation from Open-Meteo run metadata "
                           "(checked before and after the request) or the Earth2Studio store issue time; run_time_known is always true. "
                           "CORE tables record CORE's generated_at; CORE best-match is a blend and has no single run time.",
        "lead_day_definition": "valid_date_ist minus the IST calendar date of run_time_utc",
        "points_file": "archive/points.json", "points": len(pts),
        "expected": {"forecasts": specs, "core": core_spec},
        "files": [{"kind": k, "name": p.name, "bytes": p.stat().st_size, "rows": r, "sha256": sha256(p)} for k, p, r in files],
        "collection_errors": errors, "http": dict(STATS), "duration_s": round(time.time() - t0, 1),
    }
    if a.inject == "checksum":  # corrupt the forecasts file AFTER its checksum was recorded
        f = out / f"forecasts_{day}.parquet"
        b = bytearray(f.read_bytes())
        b[len(b) // 2] ^= 0xFF
        f.write_bytes(bytes(b))
    write_json(out / f"manifest_{day}.json", manifest)
    print(json.dumps({k: manifest[k] for k in ("archive_date_ist", "files", "collection_errors", "http", "duration_s")}, indent=1))
    return 0


def _env(k):
    import os
    return os.environ.get(k)


def _run_url():
    import os
    if os.environ.get("GITHUB_RUN_ID"):
        return f"{os.environ.get('GITHUB_SERVER_URL')}/{os.environ.get('GITHUB_REPOSITORY')}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
    return None


if __name__ == "__main__":
    sys.exit(main())
