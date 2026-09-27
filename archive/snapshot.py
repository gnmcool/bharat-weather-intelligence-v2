"""Daily forecast archive for V2 forecast verification (milestone M0).

Verification needs forecasts that were saved *before* the weather happened. CORE keeps only the
latest forecast, so this job stores a small daily snapshot. It reads CORE's public outputs only
and never writes to CORE.

Outputs (in --out):
  e2s_gfs_daily_<cycle>.nc   Earth2Studio GFS store (CORE `forecast` release) reduced to daily
                             values per India Standard Time day, for each lead day:
                             rain_mm (sum), tmax_c, tmin_c, gust_max_kmh. 0.25° grid, as CORE.
  points_<YYYY-MM-DD>.json   Open-Meteo daily forecasts from ECMWF IFS, NOAA GFS and DWD ICON,
                             separately, for the fixed points in points.json (one per State/UT).

Provenance: every file records its source URL, model, cycle/issue time and retrieval time.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

import numpy as np
import xarray as xr

CORE_STORE_URL = "https://github.com/gnmcool/bharat-weather-intelligence/releases/download/forecast/gfs_latest.nc"
OPEN_METEO = "https://api.open-meteo.com/v1/forecast"
MODELS = ["ecmwf_ifs025", "gfs_seamless", "icon_seamless"]
DAILY = ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "wind_gusts_10m_max"]
IST = timedelta(hours=5, minutes=30)
HERE = pathlib.Path(__file__).resolve().parent


def fetch(url: str, dest: pathlib.Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "BWI-V2-archive/0.1"})
    with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)


def e2s_daily(src: pathlib.Path, out_dir: pathlib.Path, retrieved: str) -> pathlib.Path:
    ds = xr.open_dataset(src).load()
    issue = str(ds.attrs.get("issue_time", ""))
    cycle = datetime.fromisoformat(issue.replace("Z", "+00:00")).strftime("%Y%m%d%H")
    # valid time -> IST calendar day; drop partial first/last days (< 8 three-hourly steps)
    ist_day = (ds.time.values + np.timedelta64(int(IST.total_seconds()), "s")).astype("datetime64[D]")
    ds = ds.assign_coords(ist_day=("time", ist_day))
    counts = ds.time.groupby("ist_day").count()
    full = counts.ist_day.values[counts.values >= 8]
    g = ds.sel(time=np.isin(ist_day, full)).groupby("ist_day")
    out = xr.Dataset(
        {
            "rain_mm": g.sum("time")["tp"].astype("float32"),
            "tmax_c": g.max("time")["t2m"].astype("float32"),
            "tmin_c": g.min("time")["t2m"].astype("float32"),
        }
    )
    if "fg10m" in ds:
        out["gust_max_kmh"] = (g.max("time")["fg10m"] * 3.6).astype("float32")
    issue_day = np.datetime64((datetime.fromisoformat(issue.replace("Z", "+00:00")) + IST).date())
    out = out.assign_coords(lead_day=("ist_day", (out.ist_day.values - issue_day).astype(int)))
    out.attrs = {
        "title": "BWI V2 forecast archive — Earth2Studio GFS daily values (IST days)",
        "source": ds.attrs.get("source", "NOAA GFS via Earth2Studio"),
        "model": ds.attrs.get("model", "GFS 0.25°"),
        "issue_time": issue,
        "source_url": CORE_STORE_URL,
        "retrieved_at": retrieved,
        "method": "3-hourly CORE store aggregated by India Standard Time calendar day; days with < 8 steps dropped",
    }
    dest = out_dir / f"e2s_gfs_daily_{cycle}.nc"
    out.to_netcdf(dest, encoding={v: {"zlib": True, "complevel": 5} for v in out.data_vars})
    return dest


def points(out_dir: pathlib.Path, retrieved: str) -> pathlib.Path:
    pts = json.loads((HERE / "points.json").read_text())["points"]
    q = {
        "latitude": ",".join(str(p["lat"]) for p in pts),
        "longitude": ",".join(str(p["lon"]) for p in pts),
        "daily": ",".join(DAILY),
        "models": ",".join(MODELS),
        "forecast_days": 10,
        "timezone": "Asia/Kolkata",
        "wind_speed_unit": "kmh",
    }
    url = f"{OPEN_METEO}?{urllib.parse.urlencode(q)}"
    req = urllib.request.Request(url, headers={"User-Agent": "BWI-V2-archive/0.1"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.load(r)
    data = data if isinstance(data, list) else [data]
    day = datetime.now(timezone.utc).astimezone(timezone(IST)).strftime("%Y-%m-%d")
    doc = {
        "title": "BWI V2 forecast archive — multi-model point forecasts",
        "source": "Open-Meteo (ECMWF IFS 0.25°, NOAA GFS, DWD ICON; model data licences apply)",
        "source_url": OPEN_METEO,
        "models": MODELS,
        "retrieved_at": retrieved,
        "points": [{**p, "daily": d.get("daily"), "daily_units": d.get("daily_units")} for p, d in zip(pts, data)],
    }
    dest = out_dir / f"points_{day}.json"
    dest.write_text(json.dumps(doc, separators=(",", ":")))
    return dest


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="out")
    ap.add_argument("--store", help="use a local CORE store instead of downloading")
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    retrieved = datetime.now(timezone.utc).isoformat(timespec="seconds")
    src = pathlib.Path(a.store) if a.store else out / "gfs_latest.nc"
    if not a.store:
        fetch(CORE_STORE_URL, src)
    written = [e2s_daily(src, out, retrieved), points(out, retrieved)]
    if not a.store:
        src.unlink(missing_ok=True)
    for f in written:
        print(f"{f.name}\t{f.stat().st_size / 1e6:.2f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
