"""36-point extraction, IST-day stitching, E/G handling and deterministic tables (plan §5, §10.2)."""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest

from reference.tests import flat_index, write_grib
import era5_common as C
import era5_extract as X
import era5_grib as G

UTC = timezone.utc
SMALL = [34.0, 72.25, 33.0, 73.5]
PTS = [{"id": "P1", "lat": Decimal("33.611"), "lon": Decimal("72.818")},      # node 33.5, 72.75
       {"id": "P2", "lat": Decimal("33.125"), "lon": Decimal("73.375")}]      # tie on both axes: node 33.25, 73.5


def hour_value(t, lats, lons):
    """Value in metres encoding the stamp: day-of-month + hour/100 (mm), identical at every node."""
    mm = t.day + t.hour / 100.0
    return np.full(len(lats) * len(lons), mm / 1000.0)


@pytest.fixture(scope="module")
def files(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("x")
    rq = C.build_requests("2027-01", area=SMALL)                # January: boundary is 31 Dec 2026
    return rq, {role: G.decode(write_grib(tmp / f"{role}.grib", rq[role], value_fn=hour_value)) for role in C.ROLES}


def test_nodes_and_tie_break(files):
    rq, f = files
    nodes = X.select_nodes(PTS, f["month"])
    assert [(float(n["node_lat"]), float(n["node_lon"])) for n in nodes] == [(33.5, 72.75), (33.25, 73.5)]
    assert [n["tie_break_applied"] for n in nodes] == [False, True]
    assert nodes[0]["index"] == flat_index(33.5, 72.75, SMALL)


def test_ist_day_stitching_across_the_year_boundary(files, tmp_path):
    rq, f = files
    t = X.build_tables(PTS, f, "2027-01", tmp_path)
    d = t["days"]
    assert len(d) == 2 * 31 and d.reason.isna().all() and (d.hours_present == 24).all()
    jan1 = d[(d.point_id == "P1") & (d.ist_date == date(2027, 1, 1))].iloc[0]
    # 19..23Z on 31 Dec (boundary file) + 00..18Z on 1 Jan (month file), each encoded as day + hour/100 mm
    want = sum(31 + h / 100 for h in range(19, 24)) + sum(1 + h / 100 for h in range(0, 19))
    assert jan1.precip_ist_day_mm == pytest.approx(want, abs=2e-3)
    hourly = t["hourly"]
    assert set(hourly.source_request) == {"boundary", "month"}
    assert len(hourly) == 2 * (5 + 744) and hourly.precipitation_mm.notna().all()
    assert hourly[hourly.source_request == "boundary"].utc_time.min() == pd.Timestamp("2026-12-31 19:00", tz="UTC")
    stored = pq.read_table(tmp_path / "era5_ist_day_2027-01.parquet").schema.field("precip_ist_day_mm").type
    assert str(stored) == "float"                                               # stored as float32
    assert t["exact"][("P1", date(2027, 1, 1))] == pytest.approx(want, abs=2e-3)  # float64 sum kept for comparisons


def test_month_without_boundary_hours_is_E_not_zero(files, tmp_path):
    """If the boundary hours were absent the first day must be null (E), never a 19-hour total or zero."""
    rq, f = files
    trunc = {"boundary": {**f["boundary"], "messages": f["boundary"]["messages"][:0],
                          "values": f["boundary"]["values"][:0]}, "month": f["month"]}
    nodes = X.select_nodes(PTS, f["month"])
    hourly = X.hourly_table(nodes, trunc)
    days, _ = X.day_values(nodes, hourly, "2027-01")
    first = days[days.ist_date == date(2027, 1, 1)]
    assert first.precip_ist_day_mm.isna().all() and (first.reason == "E").all() and (first.hours_present == 19).all()
    assert days[days.ist_date == date(2027, 1, 2)].reason.isna().all()


def test_missing_hour_gives_E_with_hours_present(tmp_path):
    rq = C.build_requests("2027-01", area=SMALL)
    hole = datetime(2027, 1, 10, 4, tzinfo=UTC)                # inside IST day 10 Jan
    idx = flat_index(33.5, 72.75, SMALL)
    f = {role: G.decode(write_grib(tmp_path / f"{role}.grib", rq[role], value_fn=hour_value,
                                   missing={hole: [idx]} if role == "month" else None)) for role in C.ROLES}
    t = X.build_tables(PTS, f, "2027-01", tmp_path / "o")
    d = t["days"].set_index(["point_id", "ist_date"])
    assert pd.isna(d.loc[("P1", date(2027, 1, 10)), "precip_ist_day_mm"])
    assert d.loc[("P1", date(2027, 1, 10)), "reason"] == "E" and d.loc[("P1", date(2027, 1, 10)), "hours_present"] == 23
    assert pd.isna(d.loc[("P2", date(2027, 1, 10)), "reason"])                # other point unaffected
    assert t["gap"]["e_days"] == [{"point_id": "P1", "ist_date": "2027-01-10", "hours_present": 23,
                                   "reason": "ERA5 hours missing: 23 of 24"}]
    assert t["hourly"].precipitation_mm.isna().sum() == 1                      # the hour stays null, not zero


def test_far_node_gives_G_but_keeps_hourly_values(files, tmp_path, monkeypatch):
    rq, f = files
    real = C.haversine_km
    monkeypatch.setattr(C, "haversine_km", lambda *a: 30.01 if float(a[0]) == 33.611 else real(*a))
    t = X.build_tables(PTS, f, "2027-01", tmp_path)
    p1 = t["days"][t["days"].point_id == "P1"]
    assert (p1.reason == "G").all() and p1.precip_ist_day_mm.isna().all() and (~p1.eligible).all()
    assert (p1.hours_present == 24).all()                                      # data present, still G
    assert t["hourly"][t["hourly"].point_id == "P1"].precipitation_mm.notna().all()
    assert len(t["gap"]["g_days"]) == 31 and t["gap"]["e_days"] == []
    monkeypatch.setattr(C, "haversine_km", lambda *a: 30.0)
    t2 = X.build_tables(PTS, f, "2027-01", tmp_path / "b")
    assert t2["days"].reason.isna().all()                                      # exactly 30.0 km is eligible


def test_negative_values_kept_as_delivered_and_counted(tmp_path):
    rq = C.build_requests("2027-01", area=SMALL)
    neg = datetime(2027, 1, 5, 12, tzinfo=UTC)

    def fn(t, lats, lons):
        v = hour_value(t, lats, lons)
        return v * 0 - 1e-5 if t == neg else v
    f = {role: G.decode(write_grib(tmp_path / f"{role}.grib", rq[role], value_fn=fn)) for role in C.ROLES}
    t = X.build_tables(PTS, f, "2027-01", tmp_path / "o")
    assert t["gap"]["negative_hourly_values"] == 2
    row = t["hourly"][(t["hourly"].point_id == "P1") & (t["hourly"].utc_time == pd.Timestamp(neg))].iloc[0]
    assert row.precipitation_mm < 0                                            # not clipped


def test_node_outside_grid_is_refused(files):
    rq, f = files
    with pytest.raises(C.ReferenceError_, match="not in the decoded grid"):
        X.select_nodes([{"id": "far", "lat": Decimal("20.0"), "lon": Decimal("80.0")}], f["month"])


def test_tables_are_deterministic(files, tmp_path):
    rq, f = files
    X.build_tables(PTS, f, "2027-01", tmp_path / "a")
    X.build_tables(PTS, f, "2027-01", tmp_path / "b")
    for name in ("era5_hourly_2027-01.parquet", "era5_ist_day_2027-01.parquet"):
        assert (tmp_path / "a" / name).read_bytes() == (tmp_path / "b" / name).read_bytes()
