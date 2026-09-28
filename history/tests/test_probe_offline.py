"""End-to-end run of history/probe.py with every network source replaced by synthetic data (no network)."""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import xarray as xr

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

import probe  # noqa: E402
import sources  # noqa: E402
from common import HistoryError  # noqa: E402

ICON_START = date(2024, 7, 10)


def _times(u1, u2):
    t = datetime(u1.year, u1.month, u1.day, tzinfo=timezone.utc)
    out = []
    while t.date() <= u2:
        out.append(t)
        t += timedelta(hours=1)
    return out


def fake_previous_runs(points, model, hourly, leads, u1, u2):
    if model in ("gfs_global", "icon_global"):
        raise HistoryError("previous-runs failed: HTTP 400: model not available")
    ts = _times(u1, u2)
    res = []
    for _ in points:
        h = {"time": [t.strftime("%Y-%m-%dT%H:%M") for t in ts]}
        for v in hourly:
            for n in leads:
                vals = []
                for t in ts:
                    ok = t.date() >= date(2024, 1, 20)
                    if model == "ecmwf_ifs025" and v in ("wind_gusts_10m", "cape"):
                        ok = False
                    if model == "icon_seamless" and (t.date() < ICON_START or n == 7):
                        ok = False
                    vals.append((25.0 if v == "temperature_2m" else 1.0) if ok else None)
                h[f"{v}_previous_day{n}"] = vals
        res.append({"hourly": h})
    return res, "https://previous-runs-api.open-meteo.com/v1/forecast?x"


def fake_era5(points, hourly, u1, u2):
    ts = _times(u1, u2)
    return [{"latitude": p["lat"], "longitude": p["lon"], "elevation": 50.0,
             "hourly": {"time": [t.strftime("%Y-%m-%dT%H:%M") for t in ts],
                        **{v: [1.0] * len(ts) for v in hourly}}} for p in points], "https://archive-api.open-meteo.com/v1/archive?x"


def fake_stations():
    from common import load_points
    return [{"id": f"VX{i:02d}", "name": p["district"], "lat": p["lat"] + 0.05, "lon": p["lon"], "elev_m": 55.0}
            for i, p in enumerate(load_points()[:3])]


def fake_metar(station, start, end):
    obs = []
    for t in _times(start, end - timedelta(days=1)):
        obs.append({"valid": t.strftime("%Y-%m-%d %H:%M"), "tmpc": "30", "sknt": "5", "gust": "M", "vsby": "6.21",
                    "wxcodes": "M"})
    return obs, "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=VAAH&year1=x"


def fake_imd(year):
    if year == 2026:
        return b"<html>not available</html>"
    lats = np.arange(6.5, 38.75, 0.25)
    lons = np.arange(66.5, 100.25, 0.25)
    t = pd.date_range(f"{year}-01-01", f"{year}-12-31")
    a = np.full((len(t), len(lats), len(lons)), np.nan, dtype="float32")
    li = np.where((lats > 8) & (lats < 35))[0]
    lj = np.where((lons > 68) & (lons < 90))[0]
    a[:, li[:, None], lj[None, :]] = 2.0
    ds = xr.Dataset({"RAINFALL": (("TIME", "LATITUDE", "LONGITUDE"), a)},
                    coords={"TIME": t, "LATITUDE": lats, "LONGITUDE": lons})
    with tempfile.NamedTemporaryFile(suffix=".nc") as f:
        ds.to_netcdf(f.name)
        return pathlib.Path(f.name).read_bytes()


def test_probe_end_to_end(monkeypatch, tmp_path):
    monkeypatch.setattr(sources, "previous_runs", fake_previous_runs)
    monkeypatch.setattr(sources, "era5", fake_era5)
    monkeypatch.setattr(sources, "iem_stations", fake_stations)
    monkeypatch.setattr(sources, "iem_metar", fake_metar)
    monkeypatch.setattr(sources, "imd_year", fake_imd)
    monkeypatch.setattr(probe.time, "sleep", lambda s: None)
    monkeypatch.setattr(probe, "SAMPLE_MONTHS", [(date(2024, 7, 5), date(2024, 7, 14)), (date(2025, 1, 1), date(2025, 1, 3))])
    monkeypatch.setattr(probe, "GFS_EARLY_START", None)
    monkeypatch.setattr(sys, "argv", ["probe", "--out", str(tmp_path), "--matrix-end", "2025-01-31"])
    rc = probe.main()
    R = json.loads((tmp_path / "probe_report.json").read_text())
    assert rc == 0, R["problems"]
    assert R["unsupported_model_ids"] == ["gfs_global", "icon_global"]
    summ = {(r["om_model"], r["hourly_variable"], r["lead"]): r for r in R["summary_matrix"]}
    # first complete IST day is the day AFTER the first available UTC day (the IST day starts 18:30Z the day before)
    assert summ[("icon_seamless", "temperature_2m", 1)]["first_complete_day"] == str(ICON_START + timedelta(days=1))
    assert summ[("icon_seamless", "temperature_2m", 7)]["complete_days"] == 0
    assert summ[("ecmwf_ifs025", "wind_gusts_10m", 1)]["complete_days"] == 0
    # the IST day containing the first available UTC hour is incomplete (starts 18:30Z the day before)
    assert summ[("gfs_seamless", "temperature_2m", 1)]["first_complete_day"] == "2024-01-21"

    rep = json.loads((tmp_path / "backfill_report_sample.json").read_text())
    ch = {(c["model"], c["period"]): c for c in rep["model_choice"]}
    assert ch[("gfs_global", "2024-07-05..2024-07-14")]["om_model"] == "gfs_seamless"
    assert ch[("gfs_global", "2024-07-05..2024-07-14")]["substituted"] is True
    # ICON July 2024 expectation covers only the days the source has; ECMWF gusts are "not provided"
    assert any(n["model"] == "ecmwf_ifs025" and n["hourly_variable"] == "wind_gusts_10m"
               for n in rep["not_provided_by_source"])
    assert rep["status"] == "complete", [c for c in rep["cells"] if c["status"] != "complete"][:3]

    h = pq.read_table(tmp_path / "historical_sample.parquet").to_pandas()
    assert (~h.run_time_known).all() and h.run_time_utc.isna().all()
    icon_early = h[(h.model == "icon_global") & (h.valid_date_ist < ICON_START)]
    assert len(icon_early) and icon_early.value.isna().all()          # stored empty, never filled
    ref = pq.read_table(tmp_path / "reference_sample.parquet").to_pandas()
    assert set(ref.reference) == {"era5", "metar", "imd_rf025"}
    assert not ref[(ref.reference == "metar")].variable.str.startswith("precip").any()
    island = ref[(ref.reference == "imd_rf025") & (ref.point_id == "IN-35-640")]
    assert island.value.isna().all()                                   # Andaman: no IMD cell within 30 km
    years = {y["year"]: y for y in R["steps"]["imd"]["years"]}
    assert years[2024]["ok"] and years[2026]["ok"] is False
    assert R["projection_full_backfill"]["previous_runs_weighted_calls"] > 0
