"""Offline tests for the M4.2 historical/reference dataset (no network)."""
from __future__ import annotations

import pathlib
import sys
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pyarrow as pa
import pytest
import xarray as xr

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

from build import imd_rows, metar_daily, pair_stations, rows_from_previous_runs  # noqa: E402
from common import (HIST_SCHEMA, REF_SCHEMA, aggregate_daily, backfill_report, om_weight,  # noqa: E402
                    utc_request_range, validate_history_rows, validate_reference_rows, window_instants)
import sources  # noqa: E402

IST = timezone(timedelta(hours=5, minutes=30))
NOW = datetime(2026, 9, 28, tzinfo=timezone.utc)
PTS = [{"id": "P1", "lat": 23.0, "lon": 72.5}, {"id": "P2", "lat": 13.08, "lon": 80.27}]


def hourly_times(d1: date, d2: date):
    t = datetime(d1.year, d1.month, d1.day, tzinfo=timezone.utc)
    out = []
    while t.date() <= d2:
        out.append(t)
        t += timedelta(hours=1)
    return out


def fake_resp(d1, d2, drop=None, missing_var=None, leads=(1, 2)):
    u1, u2 = utc_request_range(d1, d2)
    times = hourly_times(u1, u2)
    h = {"time": [t.strftime("%Y-%m-%dT%H:%M") for t in times]}
    for var in ("temperature_2m", "precipitation", "wind_gusts_10m"):
        if var == missing_var:
            continue
        for n in leads:
            vals = [20.0 + (t.hour % 12) if var == "temperature_2m" else 1.0 for t in times]
            if drop and drop[0] == var and drop[1] == n:
                vals[drop[2]] = None
            h[f"{var}_previous_day{n}"] = vals
    return {"hourly": h}


# ---------------- time windows
def test_ist_day_window_is_the_ist_calendar_day():
    d = date(2024, 7, 15)
    w = window_instants(d, "ist_day")
    assert len(w) == 24
    assert w[0] == datetime(2024, 7, 14, 19, tzinfo=timezone.utc)
    assert w[-1] == datetime(2024, 7, 15, 18, tzinfo=timezone.utc)
    assert {t.astimezone(IST).date() for t in w} == {d}


def test_imd_window_is_0830_to_0830_ist():
    d = date(2024, 7, 15)
    w = window_instants(d, "imd_window")
    # hourly totals ending 04:00Z..03:00Z(+1) cover 03:00Z D .. 03:00Z D+1 = 08:30 IST D .. 08:30 IST D+1
    assert (w[0] - timedelta(hours=1)).astimezone(IST) == datetime(2024, 7, 15, 8, 30, tzinfo=IST)
    assert w[-1].astimezone(IST) == datetime(2024, 7, 16, 8, 30, tzinfo=IST)


def test_request_range_covers_both_windows():
    d1, d2 = date(2024, 7, 1), date(2024, 7, 31)
    u1, u2 = utc_request_range(d1, d2)
    need = window_instants(d1, "ist_day")[0], window_instants(d2, "imd_window")[-1]
    assert u1 <= need[0].date() and need[1].date() <= u2


# ---------------- aggregation: nothing filled
def test_aggregate_requires_all_24_hours():
    d = date(2024, 7, 15)
    times = window_instants(d, "ist_day")
    vals = list(range(24))
    assert list(aggregate_daily(times, vals, "max", "ist_day", [d])) == [(d, 23.0, 24)]
    vals[5] = None
    assert list(aggregate_daily(times, vals, "max", "ist_day", [d])) == [(d, None, 23)]
    vals[5] = float("nan")
    assert list(aggregate_daily(times, vals, "sum", "ist_day", [d])) == [(d, None, 23)]


def test_historical_rows_have_unknown_run_and_nominal_lead():
    d1 = d2 = date(2024, 7, 15)
    rows = rows_from_previous_runs([fake_resp(d1, d2)] * 2, PTS, "gfs_global", "gfs_global",
                                   ["temperature_2m", "precipitation", "wind_gusts_10m"], [1, 2], [d1], "u?x", NOW)
    df = pa.Table.from_pylist(rows, schema=HIST_SCHEMA).to_pandas()
    assert (~df.run_time_known).all() and df.run_time_utc.isna().all()
    assert set(df.nominal_lead_day) == {1, 2}
    assert (df.dataset == "historical_backfill").all()
    assert df.complete.all()
    assert validate_history_rows(df) == []
    tmax = df[(df.variable == "tmax") & (df.point_id == "P1") & (df.nominal_lead_day == 1)].value.iloc[0]
    assert tmax == 31.0


def test_missing_hour_or_missing_variable_stays_missing():
    d1 = d2 = date(2024, 7, 15)
    # drop one hour inside the IST day for temperature lead 1; ECMWF-like: no gust column at all
    resp = fake_resp(d1, d2, drop=("temperature_2m", 1, 30), missing_var="wind_gusts_10m")
    rows = rows_from_previous_runs([resp], PTS[:1], "ecmwf_ifs025", "ecmwf_ifs025",
                                   ["temperature_2m", "precipitation", "wind_gusts_10m"], [1, 2], [d1], "u?x", NOW)
    df = pd.DataFrame(rows)
    t1 = df[(df.variable == "tmax") & (df.nominal_lead_day == 1)].iloc[0]
    assert pd.isna(t1.value) and not t1.complete and t1.hours_present == 23
    t2 = df[(df.variable == "tmax") & (df.nominal_lead_day == 2)].iloc[0]
    assert t2.complete
    g = df[df.variable == "gust_max"]
    assert g.value.isna().all() and (g.hours_present == 0).all()
    assert validate_history_rows(pa.Table.from_pylist(rows, schema=HIST_SCHEMA).to_pandas()) == []


# ---------------- validation refuses what must not happen
def _hist_df():
    d = date(2024, 7, 15)
    rows = rows_from_previous_runs([fake_resp(d, d)], PTS[:1], "gfs_global", "gfs_global",
                                   ["temperature_2m"], [1], [d], "u?x", NOW)
    return pa.Table.from_pylist(rows, schema=HIST_SCHEMA).to_pandas()


@pytest.mark.parametrize("mutate,msg", [
    (lambda df: df.assign(run_time_known=True), "run_time_known"),
    (lambda df: df.assign(run_time_utc=pd.Timestamp("2024-07-14T00:00Z")), "run_time_utc"),
    (lambda df: df.assign(nominal_lead_day=8), "1..7"),
    (lambda df: df.assign(complete=False), "incomplete"),
    (lambda df: pd.concat([df, df]), "duplicate"),
    (lambda df: df.assign(value=99.0), "outside"),
    (lambda df: df.assign(dataset="prospective"), "historical_backfill"),
])
def test_validation_refuses(mutate, msg):
    probs = validate_history_rows(mutate(_hist_df()))
    assert any(msg in p for p in probs), probs


# ---------------- backfill report: partial is explicit
def test_backfill_report_complete_and_partial():
    d1, d2 = date(2024, 7, 15), date(2024, 7, 16)
    days = [d1, d2]
    rows = rows_from_previous_runs([fake_resp(d1, d2, drop=("temperature_2m", 1, 30))], PTS[:1], "gfs_global",
                                   "gfs_global", ["temperature_2m"], [1, 2], days, "u?x", NOW)
    df = pd.DataFrame(rows)
    exp = [{"model": "gfs_global", "variable": "tmax", "nominal_lead_day": n, "points": ["P1"], "days": days}
           for n in (1, 2)]
    rep = backfill_report(df, exp)
    assert rep["status"] == "partial" and rep["missing_values"] == 1
    cell = next(c for c in rep["cells"] if c["nominal_lead_day"] == 1)
    assert cell["stored_incomplete"] == 1 and cell["status"] == "partial"
    rep2 = backfill_report(df, exp[1:])
    assert rep2["status"] == "complete"
    # an expected point with no rows at all is "absent", never complete
    exp3 = [dict(exp[1], points=["P1", "P9"])]
    rep3 = backfill_report(df, exp3)
    assert rep3["status"] == "partial" and rep3["cells"][0]["absent"] == 2
    assert backfill_report(df, [])["status"] == "partial"   # nothing expected is never "complete"


# ---------------- METAR: no rain, completeness, gust semantics
def test_metar_never_requests_or_accepts_rain():
    assert "p01m" not in sources.METAR_FIELDS
    bad = pd.DataFrame([{"dataset": "reference", "reference": "metar", "point_id": "P1", "site_id": "VAAH",
                         "valid_date_ist": date(2024, 7, 15), "variable": "precip", "value": 0.0, "complete": True,
                         "distance_km": 5.0}])
    assert any("METAR rainfall" in p for p in validate_reference_rows(bad))


def _obs(day: date, hours, gust_at=None, wx_at=None):
    out = []
    for h in hours:
        for m in (0, 30):
            t = datetime(day.year, day.month, day.day, h, m, tzinfo=IST).astimezone(timezone.utc)
            out.append({"valid": t.strftime("%Y-%m-%d %H:%M"), "tmpc": str(20 + h), "sknt": "10",
                        "gust": "25" if h == gust_at else "M", "vsby": "3.00",
                        "wxcodes": "TSRA" if h == wx_at else "M"})
    return out


PAIR = {"station": "VAAH", "station_lat": 23.07, "station_lon": 72.63, "distance_km": 8.0, "elev_diff_m": 3.0}


def test_metar_daily_complete_day():
    d = date(2024, 7, 15)
    rows = {r["variable"]: r for r in metar_daily(_obs(d, range(24), gust_at=15, wx_at=16), PAIR, PTS[0], [d], "u", NOW)}
    assert rows["tmax"]["value"] == 43 and rows["tmin"]["value"] == 20 and rows["tmax"]["complete"]
    assert rows["wind_max"]["value"] == pytest.approx(18.52)
    assert rows["gust_max_reported"]["value"] == pytest.approx(25 * 1.852)
    assert rows["ts_reports"]["value"] == 2 and rows["ra_reports"]["value"] == 2
    assert rows["vis_min"]["value"] == pytest.approx(3 * 1.609344)
    assert all(not v.startswith("precip") for v in rows)


def test_metar_half_day_is_incomplete_and_no_gust_is_not_zero():
    d = date(2024, 7, 15)
    rows = {r["variable"]: r for r in metar_daily(_obs(d, range(0, 12)), PAIR, PTS[0], [d], "u", NOW)}
    assert rows["tmax"]["value"] is None and not rows["tmax"]["complete"]   # 24 obs but afternoon missing
    rows = {r["variable"]: r for r in metar_daily(_obs(d, range(24)), PAIR, PTS[0], [d], "u", NOW)}
    assert rows["gust_max_reported"]["value"] is None and not rows["gust_max_reported"]["complete"]
    assert "does not mean zero" in rows["gust_max_reported"]["note"]


def test_station_pairing_rule():
    st = [{"id": "NEAR", "lat": 23.05, "lon": 72.55, "elev_m": 60.0},
          {"id": "HILL", "lat": 13.2, "lon": 80.3, "elev_m": 900.0}]
    pr = {x["point_id"]: x for x in pair_stations(PTS, st, {"P1": 50.0, "P2": 10.0}, 25, 100)}
    assert pr["P1"]["paired"] and pr["P1"]["station"] == "NEAR"
    assert not pr["P2"]["paired"] and "elevation" in pr["P2"]["reason_not_paired"]


# ---------------- IMD: 30 km rule, own cell NaN, islands unavailable
def _imd_ds():
    lats = np.arange(6.5, 38.75, 0.25)
    lons = np.arange(66.5, 100.25, 0.25)
    a = np.full((3, len(lats), len(lons)), np.nan, dtype="float32")
    li, lj = int(np.abs(lats - 23.0).argmin()), int(np.abs(lons - 72.5).argmin())
    a[:, li, lj] = [1.0, 2.0, 3.0]                    # P1 own cell valid
    ci, cj = int(np.abs(lats - 13.25).argmin()), int(np.abs(lons - 80.25).argmin())
    a[:, ci, cj] = [5.0, 6.0, 7.0]                    # a valid cell ~19 km from P2 (P2's own cell NaN)
    t = pd.date_range("2024-07-15", periods=3)
    return xr.Dataset({"RAINFALL": (("TIME", "LATITUDE", "LONGITUDE"), a)},
                      coords={"TIME": t, "LATITUDE": lats, "LONGITUDE": lons})


def test_imd_extraction_rules():
    island = {"id": "AN", "lat": 11.67, "lon": 92.74}
    rows, info, meta = imd_rows(_imd_ds(), PTS + [island], 30.0, "imd", "sha", NOW)
    inf = {x["point_id"]: x for x in info}
    assert inf["P1"]["own_cell_valid"] and inf["P1"]["usable"]
    assert not inf["P2"]["own_cell_valid"] and inf["P2"]["usable"] and inf["P2"]["label"] == "nearby grid cell"
    assert not inf["AN"]["usable"] and "unavailable" in inf["AN"]["label"]
    df = pa.Table.from_pylist(rows, schema=REF_SCHEMA).to_pandas()
    assert df[df.point_id == "AN"].value.isna().all()
    assert df[df.point_id == "P2"].value.tolist() == [5.0, 6.0, 7.0]
    # file dates 15..17 Jul hold the 24 h ENDING 08:30 IST that day -> stored as window start 14..16 Jul
    assert sorted(set(df.valid_date_ist)) == [date(2024, 7, 14), date(2024, 7, 15), date(2024, 7, 16)]
    assert (df.variable == "precip_0830").all()
    assert validate_reference_rows(df) == []
    assert meta["valid_cells_all_days"] == 2


def test_imd_far_cell_value_is_refused():
    rows, _, _ = imd_rows(_imd_ds(), PTS, 30.0, "imd", "sha", NOW)
    df = pa.Table.from_pylist(rows, schema=REF_SCHEMA).to_pandas()
    df.loc[df.point_id == "P2", "distance_km"] = 45.0
    assert any("30.0 km" in p for p in validate_reference_rows(df))


# ---------------- quota arithmetic and separation from the prospective archive
def test_open_meteo_weight():
    assert om_weight(1, 4, 1) == 1
    assert om_weight(36, 21, 33) == pytest.approx(36 * 2.1 * 33 / 14)


def test_history_is_separate_from_prospective_archive():
    import importlib.util
    H = HIST_SCHEMA
    spec = importlib.util.spec_from_file_location("archive_common", HERE.parent / "archive" / "common.py")
    ac = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ac)
    assert not H.equals(ac.FORECAST_SCHEMA)
    assert "nominal_lead_day" in H.names and "lead_day" not in H.names
    for f in HERE.glob("*.py"):
        src = f.read_text()
        for forbidden in ("from collect ", "import collect\n", "from validate ", "archive-daily", "gh release"):
            assert forbidden not in src, f"{f.name} must not touch the prospective archive ({forbidden})"
