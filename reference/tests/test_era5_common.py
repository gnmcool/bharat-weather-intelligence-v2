"""Requests, canonical hashes, fixed area and points, grid-node rule, 30 km rule, eligibility (plan §4-§6)."""
import hashlib
import json
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from reference.tests import C  # noqa: F401  (sets sys.path)
import era5_common as C  # noqa: E402,F811

UTC = timezone.utc


def test_fixed_source_constants():
    assert (C.DATASET, C.PRODUCT_TYPE, C.VARIABLE, C.DATA_FORMAT, C.DOWNLOAD_FORMAT) == (
        "reanalysis-era5-single-levels", "reanalysis", "total_precipitation", "grib", "unarchived")
    assert C.FINAL_EXPVER == "0001" and C.EARTH_RADIUS_KM == 6371.0 and C.MAX_NODE_KM == 30.0
    assert C.VALIDATION_MONTH == "2026-09" and C.MAX_RETRIEVALS == 2 and C.WAIT_DAYS == 70


def test_points_hash_and_fixed_area():
    pts = C.load_points()
    assert len(pts) == 36 and C.points_sha256() == C.POINTS_SHA256
    assert C.POINTS_SHA256 == "4919f87259fd22a83a6050e01497f3be86711ce0e10e28aecbb9af324b65d49e"
    assert C.area_for(pts) == C.AREA == [34.0, 72.25, 8.25, 94.75]
    assert all(isinstance(p["lat"], Decimal) for p in pts)                   # exact decimals from the JSON text
    raw = json.loads(C.POINTS_FILE.read_text())
    assert [p["id"] for p in pts] == [p["id"] for p in raw["points"]]         # file order preserved


def test_changed_points_file_is_refused(tmp_path):
    doc = json.loads(C.POINTS_FILE.read_text())
    doc["points"][0]["lat"] = 10.733
    f = tmp_path / "points.json"
    f.write_text(json.dumps(doc))
    with pytest.raises(C.ReferenceError_, match="differs from the approved"):
        C.load_points(f)


def _expected(month_year, month, days, b_year, b_month, b_day):
    common = {"area": [34.0, 72.25, 8.25, 94.75], "data_format": "grib", "download_format": "unarchived",
              "product_type": ["reanalysis"], "variable": ["total_precipitation"]}
    return ({**common, "year": [b_year], "month": [b_month], "day": [b_day],
             "time": ["19:00", "20:00", "21:00", "22:00", "23:00"]},
            {**common, "year": [month_year], "month": [month], "day": [f"{d:02d}" for d in range(1, days + 1)],
             "time": [f"{h:02d}:00" for h in range(24)]})


@pytest.mark.parametrize("month,exp,items", [
    ("2026-09", _expected("2026", "09", 30, "2026", "08", "31"), 720),     # 30-day month
    ("2026-10", _expected("2026", "10", 31, "2026", "09", "30"), 744),     # 31-day month
    ("2027-02", _expected("2027", "02", 28, "2027", "01", "31"), 672),     # February
    ("2028-02", _expected("2028", "02", 29, "2028", "01", "31"), 696),     # leap February
    ("2027-01", _expected("2027", "01", 31, "2026", "12", "31"), 744),     # January: boundary in the previous year
])
def test_requests_exact(month, exp, items):
    rq = C.build_requests(month)
    assert rq["boundary"] == exp[0] and rq["month"] == exp[1]
    assert C.item_count(rq["boundary"]) == 5 and C.item_count(rq["month"]) == items
    # boundary and month are separate requests: no shared stamp, boundary = last UTC day of M-1, 19-23Z
    b, m = C.expected_stamps(rq["boundary"]), C.expected_stamps(rq["month"])
    assert not set(b) & set(m) and len(b) == 5 and len(m) == items
    assert b[0].hour == 19 and b[-1].hour == 23 and (m[0] - b[-1]).total_seconds() == 3600


def test_canonical_json_and_hash_are_fixed():
    rq = C.build_requests("2026-10")["boundary"]
    text = ('{"area":[34.0,72.25,8.25,94.75],"data_format":"grib","day":["30"],"download_format":"unarchived",'
            '"month":["09"],"product_type":["reanalysis"],"time":["19:00","20:00","21:00","22:00","23:00"],'
            '"variable":["total_precipitation"],"year":["2026"]}')
    assert C.canonical_json(rq) == text
    assert C.request_sha256(rq) == hashlib.sha256(text.encode()).hexdigest()
    reordered = json.loads(json.dumps(rq), object_pairs_hook=lambda kv: dict(reversed(kv)))
    assert C.request_sha256(reordered) == C.request_sha256(rq)             # key order does not matter
    changed = {**rq, "time": rq["time"][:4]}
    assert C.request_sha256(changed) != C.request_sha256(rq)


def test_node_rule_decimal_and_ties():
    D = Decimal
    assert C.node_coord(D("27.32")) == D("27.25") and C.node_coord(D("88.375")) == D("88.5")   # east on a tie
    assert C.node_coord(D("20.125")) == D("20.25")                          # latitude tie goes north
    assert C.node_coord(D("20.1249")) == D("20.0") and C.node_coord(D("20.1251")) == D("20.25")
    assert C.node_coord(D("72.288")) == D("72.25")
    assert C.is_midpoint(D("88.375")) and not C.is_midpoint(D("88.376")) and not C.is_midpoint(D("27.32"))
    # a binary float would misjudge the midpoint for coordinates like 0.1+0.025; Decimal evaluation does not
    assert C.node_coord(D("0.125")) == D("0.25")


def test_south_sikkim_tie_break_and_all_nodes():
    nodes = [C.node_for(p) for p in C.load_points()]
    ss = next(n for n in nodes if n["point_id"] == "IN-11-243")
    assert (ss["node_lat"], ss["node_lon"]) == (Decimal("27.25"), Decimal("88.5")) and ss["tie_break_applied"]
    assert round(ss["distance_km"], 3) == 14.601
    assert [n["point_id"] for n in nodes if n["tie_break_applied"]] == ["IN-11-243"]
    d = [n["distance_km"] for n in nodes]
    assert all(n["eligible"] for n in nodes) and 2.5 < min(d) and max(d) < 16.5
    for n in nodes:                                                       # every node inside the fixed area
        assert 8.25 <= float(n["node_lat"]) <= 34.0 and 72.25 <= float(n["node_lon"]) <= 94.75


def test_30km_rule_boundary(monkeypatch):
    p = {"id": "X", "lat": Decimal("20.1"), "lon": Decimal("80.1")}
    monkeypatch.setattr(C, "haversine_km", lambda *a: 30.0)
    assert C.node_for(p)["eligible"] is True                               # exactly 30.0 km is eligible
    monkeypatch.setattr(C, "haversine_km", lambda *a: 30.01)
    assert C.node_for(p)["eligible"] is False


def test_haversine_radius():
    assert C.haversine_km(0, 0, 0, 1) == pytest.approx(6371.0 * 3.141592653589793 / 180, rel=1e-12)


def test_ist_day_window():
    s = C.ist_day_stamps(date(2027, 1, 1))
    assert s[0] == datetime(2026, 12, 31, 19, tzinfo=UTC) and s[-1] == datetime(2027, 1, 1, 18, tzinfo=UTC)
    assert len(s) == 24 and len(set(s)) == 24


@pytest.mark.parametrize("month,first", [("2026-09", date(2026, 12, 9)), ("2026-10", date(2027, 1, 9)),
                                         ("2026-11", date(2027, 2, 8)), ("2026-12", date(2027, 3, 11)),
                                         ("2027-01", date(2027, 4, 11))])
def test_eligibility_dates_match_plan_table(month, first):
    assert C.eligibility_date(month) == first
    assert C.is_eligible(month, first) and not C.is_eligible(month, first.replace(day=first.day - 1))


def test_invalid_month_refused():
    for m in ("2026-13", "2026-9", "26-09", "abc"):
        with pytest.raises(C.ReferenceError_):
            C.build_requests(m)


def test_licence_file_and_attribution():
    lic = C.load_licence()
    assert lic["accepted_on"] == "2026-09-30" and lic["stated_by"] == "owner"
    a = C.attribution(2026)
    assert a["raw_grib"] == "Generated using Copernicus Climate Change Service information 2026"
    assert a["derived_tables"] == "Contains modified Copernicus Climate Change Service information 2026"
    assert "Neither the European Commission nor ECMWF is responsible" in a["statement"]
    assert "key" not in json.dumps(lic).lower() and "token" not in json.dumps(lic).lower()
