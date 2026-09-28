"""Offline tests for the M4.3 monthly historical backfill (all sources replaced by synthetic data; no network)."""
from __future__ import annotations

import io
import json
import pathlib
import sys
import urllib.error
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest
import xarray as xr

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

import backfill as B  # noqa: E402
import sources  # noqa: E402
from common import HistoryError, load_points, sha256_file, write_json  # noqa: E402

POINTS = load_points()
DROP_POINT = POINTS[3]["id"]           # one hour missing for this point (source gap)
PAIRED = POINTS[5]                      # a station 5 km away, same elevation -> matched
HILL = POINTS[6]                        # a station 5 km away but 400 m higher -> not matched


def _times(u1, u2):
    t = datetime(u1.year, u1.month, u1.day, tzinfo=timezone.utc)
    out = []
    while t.date() <= u2:
        out.append(t)
        t += timedelta(hours=1)
    return out


def fake_previous_runs(points, model, hourly, leads, u1, u2):
    ts = _times(u1, u2)
    res = []
    for p in points:
        h = {"time": [t.strftime("%Y-%m-%dT%H:%M") for t in ts]}
        for v in hourly:
            for n in leads:
                if model == "ecmwf_ifs025" and v == "wind_gusts_10m":
                    h[f"{v}_previous_day{n}"] = [None] * len(ts)
                    continue
                if model == "icon_global" and n == 7:
                    h[f"{v}_previous_day{n}"] = [None] * len(ts)
                    continue
                vals = [(25.0 + t.hour % 7) if v == "temperature_2m" else 0.5 for t in ts]
                if p["id"] == DROP_POINT and model == "gfs_global" and v == "temperature_2m" and n == 1:
                    vals[40] = None
                h[f"{v}_previous_day{n}"] = vals
        res.append({"latitude": p["lat"] + 0.05, "longitude": p["lon"], "hourly": h})
    return res, "https://previous-runs-api.open-meteo.com/v1/forecast?x"


def fake_era5(points, hourly, u1, u2):
    ts = _times(u1, u2)
    rain = [float((t - timedelta(hours=4)).day % 5) / 24 for t in ts]
    return [{"latitude": p["lat"] + 0.1, "longitude": p["lon"], "elevation": 100.0,
             "hourly": {"time": [t.strftime("%Y-%m-%dT%H:%M") for t in ts],
                        **{v: (rain if v == "precipitation" else [20.0] * len(ts)) for v in hourly}}}
            for p in points], "https://archive-api.open-meteo.com/v1/archive?x"


def fake_stations():
    return [{"id": "VPAR", "name": "paired", "lat": PAIRED["lat"] + 0.045, "lon": PAIRED["lon"], "elev_m": 120.0},
            {"id": "VHIL", "name": "hill", "lat": HILL["lat"] + 0.045, "lon": HILL["lon"], "elev_m": 500.0}]


GAP_DAY = None


def fake_metar(station, start, end):
    obs = []
    for t in _times(start, end - timedelta(days=1)):
        ist = t.astimezone(timezone(timedelta(hours=5, minutes=30)))
        if GAP_DAY and ist.date() == GAP_DAY and ist.hour >= 12:
            continue   # afternoon block missing on this day
        for mm in (0, 30):
            tt = t + timedelta(minutes=mm)
            obs.append({"valid": tt.strftime("%Y-%m-%d %H:%M"), "tmpc": "30", "sknt": "5", "gust": "M",
                        "vsby": "6.21", "wxcodes": "M"})
    return obs, "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=X&year1=x"


def make_imd(imd_dir: pathlib.Path, year: int, status="available"):
    imd_dir.mkdir(parents=True, exist_ok=True)
    if status != "available":
        write_json(imd_dir / f"imd_raw_{year}.json", {"year": year, "status": status, "checked_utc": "2026-09-28T00:00:00Z"})
        return
    lats, lons = np.arange(6.5, 38.75, 0.25), np.arange(66.5, 100.25, 0.25)
    t = pd.date_range(f"{year}-01-01", f"{year}-12-31")
    a = np.full((len(t), len(lats), len(lons)), np.nan, dtype="float32")
    li, lj = np.where((lats > 8) & (lats < 35))[0], np.where((lons > 68) & (lons < 90))[0]
    for k, ft in enumerate(t):
        a[k, li[:, None], lj[None, :]] = float((ft - pd.Timedelta(days=1)).day % 5)
    nc = imd_dir / f"RF25_ind{year}_rfp25.nc"
    xr.Dataset({"RAINFALL": (("TIME", "LATITUDE", "LONGITUDE"), a)},
               coords={"TIME": t, "LATITUDE": lats, "LONGITUDE": lons}).to_netcdf(nc)
    write_json(imd_dir / f"imd_raw_{year}.json", {"year": year, "status": "available", "sha256": sha256_file(nc),
                                                  "release_tag": f"history-imd-raw-{year}"})


@pytest.fixture
def fakes(monkeypatch):
    monkeypatch.setattr(sources, "previous_runs", fake_previous_runs)
    monkeypatch.setattr(sources, "era5", fake_era5)
    monkeypatch.setattr(sources, "iem_stations", fake_stations)
    monkeypatch.setattr(sources, "iem_metar", fake_metar)
    monkeypatch.setattr(B.time, "sleep", lambda s: None)
    global GAP_DAY
    GAP_DAY = date(2024, 2, 10)
    yield
    GAP_DAY = None


@pytest.fixture(scope="module")
def imd_dir(tmp_path_factory):
    d = tmp_path_factory.mktemp("imd")
    make_imd(d, 2024)
    return d


def test_month_build_and_validate(fakes, imd_dir, tmp_path):
    man = B.build_month("2024-02", tmp_path, imd_dir)
    assert man["retrieval_errors"] == []
    q = B.validate_month(tmp_path)
    assert q["publishable"], q["problems"]
    days = 29
    assert q["expected_values"] == 36 * 3 * 5 * 7 * days
    assert q["status"] == "partial"                     # ECMWF gusts and ICON lead 7 are not provided
    assert q["missing_by_category"]["A"] == 36 * 7 * 29 + 36 * 5 * 29   # ECMWF gusts + ICON lead 7
    assert q["missing_by_category"]["C"] >= 1
    F = pq.read_table(tmp_path / "forecasts_history-2024-02.parquet").to_pandas()
    assert (~F.run_time_known).all() and F.run_time_utc.isna().all()
    miss = F[~F.complete]
    assert miss.reason.notna().all() and (miss.hours_present + miss.hours_missing == miss.hours_expected).all()
    g = F[(F.model == "ecmwf_ifs025") & (F.variable == "gust_max")]
    assert g.value.isna().all() and g.reason.str.startswith("not provided by source").all()
    one = F[(F.point_id == DROP_POINT) & (F.model == "gfs_global") & (F.variable == "tmax") & (F.nominal_lead_day == 1)
            & ~F.complete]
    assert len(one) == 1 and one.hours_missing.iloc[0] == 1 and one.reason.iloc[0].startswith("source outage: 1 of 24 hours missing (retrieval succeeded")

    M = pq.read_table(tmp_path / "matched_history-2024-02.parquet").to_pandas()
    assert (M.reference_label[M.reference == "era5"] == "ERA5 reanalysis").all()
    assert (~M.run_time_known).all() and M.lead_basis.str.startswith("nominal previous_day").all()
    met = M[(M.reference == "metar") & (M.variable == "tmax")]
    ok = met[met.point_id == PAIRED["id"]]
    assert ok.reference_available.sum() == len(ok) - 21   # gap day unavailable (3 models x 7 leads)
    gap = ok[~ok.reference_available]
    assert gap.reference_reason.str.contains("no report in IST 6-h block").all()
    hill = met[met.point_id == HILL["id"]]
    assert (~hill.reference_available).all() and hill.reference_reason.str.contains("elevation difference").all()
    assert hill.ref_elev_diff_m.notna().all() and hill.ref_distance_km.notna().all()
    other = met[~met.point_id.isin([PAIRED["id"], HILL["id"]])]
    assert other.reference_reason.str.startswith("no METAR match").all()
    # an unavailable reference never makes the forecast unavailable
    assert met.forecast_available.sum() > 0
    mg = M[(M.reference == "metar") & (M.variable == "gust_max")]
    assert (~mg.reference_available).all() and mg.reference_reason.str.contains("gust").all()
    imd = M[M.reference == "imd_rf025"]
    and_ = imd[imd.point_id == "IN-35-640"]
    assert (~and_.reference_available).all() and and_.reference_reason.str.contains("no IMD cell within 30 km").all()
    assert q["imd_alignment"]["best_lag"] == "+0"
    assert q["metar_by_point"][HILL["id"]]["matched"] is False


def _rebuild_manifest(stage: pathlib.Path):
    man_p = next(stage.glob("manifest_history-*.json"))
    man = json.loads(man_p.read_text())
    for f in man["files"]:
        p = stage / f["name"]
        f["sha256"] = sha256_file(p)
        if f["rows"] is not None:
            f["rows"] = pq.ParquetFile(p).metadata.num_rows
    write_json(man_p, man)


def test_refusals(fakes, imd_dir, tmp_path, monkeypatch):
    s = tmp_path / "a"
    B.build_month("2024-02", s, imd_dir)
    # checksum tamper
    f = s / "reference_history-2024-02.parquet"
    f.write_bytes(f.read_bytes() + b"x")
    assert any("checksum" in p for p in B.validate_month(s)["problems"])
    # missing forecast row (manifest updated to hide it: completeness still refuses)
    s2 = tmp_path / "b"
    B.build_month("2024-02", s2, imd_dir)
    fp = s2 / "forecasts_history-2024-02.parquet"
    t = pq.read_table(fp)
    pq.write_table(t.slice(1), fp)
    _rebuild_manifest(s2)
    assert any("expected keys absent" in p for p in B.validate_month(s2)["problems"])
    # METAR substitution (a row for an unmatched point)
    s3 = tmp_path / "c"
    B.build_month("2024-02", s3, imd_dir)
    pj = s3 / "metar_pairing_history-2024-02.json"
    P = json.loads(pj.read_text())
    for p in P["pairs"]:
        if p["point_id"] == PAIRED["id"]:
            p["paired"], p["reason_not_paired"] = False, "test"
    write_json(pj, P)
    _rebuild_manifest(s3)
    assert any("substitution" in p for p in B.validate_month(s3)["problems"])


def test_failed_source_and_missing_imd_are_refused(fakes, tmp_path, monkeypatch):
    def boom(points, model, *a):
        if model == "icon_global":
            raise HistoryError("previous-runs failed: HTTP 500")
        return fake_previous_runs(points, model, *a)
    monkeypatch.setattr(sources, "previous_runs", boom)
    empty = tmp_path / "imd"
    empty.mkdir()
    B.build_month("2024-02", tmp_path / "s", empty)
    q = B.validate_month(tmp_path / "s")
    assert not q["publishable"]
    assert any("icon_global" in p for p in q["problems"]) and any("imd 2024" in p for p in q["problems"])


def test_imd_2026_unpublished_is_missing_reference_not_failure(fakes, tmp_path):
    d = tmp_path / "imd"
    make_imd(d, 2026, status="unavailable")
    B.build_month("2026-08", tmp_path / "s", d)
    q = B.validate_month(tmp_path / "s")
    assert q["publishable"], q["problems"]
    M = pq.read_table(tmp_path / "s" / "matched_history-2026-08.parquet").to_pandas()
    imd = M[M.reference == "imd_rf025"]
    assert (~imd.reference_available).all() and imd.reference_reason.str.contains("IMD 2026 rainfall file not published").all()
    era = M[(M.reference == "era5") & (M.variable == "precip_0830")]
    assert era.reference_available.all()        # ERA5 is present but is never used as an IMD substitute
    assert (imd.reference_label.str.startswith("IMD")).all()


def test_year_boundary_needs_next_year_file(fakes, tmp_path):
    d = tmp_path / "imd"
    make_imd(d, 2024)       # 31 Dec 2024 window ends 1 Jan 2025 -> 2025 file required
    B.build_month("2024-12", tmp_path / "s", d)
    q = B.validate_month(tmp_path / "s")
    assert not q["publishable"] and any("imd 2025" in p for p in q["problems"])


def test_quota_and_budget_stop_batch(fakes, imd_dir, tmp_path, monkeypatch):
    monkeypatch.setattr(B, "ensure_imd", lambda *a: [])
    monkeypatch.setattr(B, "release_state", lambda tag: "none")
    monkeypatch.setattr(B, "commit_index", lambda *a: None)
    (tmp_path / "work" / "imd").mkdir(parents=True)

    def quota(*a):
        raise sources.QuotaExhausted("Daily API request limit exceeded")
    monkeypatch.setattr(sources, "previous_runs", quota)
    s = B.batch(["2024-02", "2024-03"], tmp_path / "idx", tmp_path / "work", 10000, "t1")
    assert s["stopped"] == "quota" and s["months"]["2024-02"].startswith("deferred") and "2024-03" not in s["months"]
    s = B.batch(["2024-02"], tmp_path / "idx", tmp_path / "work", 100, "t2")
    assert s["stopped"] == "budget" and s["months"]["2024-02"].startswith("deferred: run budget")


def test_daily_quota_response_raises_immediately(monkeypatch):
    def fail(req, timeout):
        raise urllib.error.HTTPError(req.full_url, 429, "Too Many", {},
                                     io.BytesIO(b'{"reason":"Daily API request limit exceeded. Please try again tomorrow."}'))
    monkeypatch.setattr(sources.urllib.request, "urlopen", fail)
    monkeypatch.setattr(sources.time, "sleep", lambda s: pytest.fail("must not sleep/retry on a daily quota"))
    with pytest.raises(sources.QuotaExhausted):
        sources.http("https://previous-runs-api.open-meteo.com/v1/forecast?x")


def test_published_months_are_never_rebuilt(monkeypatch, tmp_path):
    monkeypatch.setattr(B, "ensure_imd", lambda *a: [])
    monkeypatch.setattr(B, "release_state", lambda tag: "published")
    monkeypatch.setattr(B, "commit_index", lambda *a: None)
    monkeypatch.setattr(B, "build_month", lambda *a: pytest.fail("must not rebuild a published month"))
    s = B.batch(["2024-02"], tmp_path / "idx", tmp_path / "w", 10000, "t3")
    assert s["months"]["2024-02"].startswith("already published")


def test_aggregate_quality(fakes, imd_dir, tmp_path):
    idx = tmp_path / "idx"
    (idx / "history" / "index").mkdir(parents=True)
    st = tmp_path / "s"
    man = B.build_month("2024-02", st, imd_dir)
    q = B.validate_month(st)
    write_json(idx / "history" / "index" / "2024-02.json", {"month": "2024-02", "tag": "history-2024-02",
                                                            "release_url": "u", "manifest_sha256": "x",
                                                            "manifest": man, "quality": q})
    rep = B.aggregate(idx, ["2024-02", "2024-03"])
    assert rep["dataset_status"] == "partial" and rep["months_not_published"] == ["2024-03"]
    assert rep["expected_values"] == q["expected_values"] and rep["values_missing"] == q["values_missing"]
    assert set(rep["missing_by_model"]) == {"ecmwf_ifs025", "gfs_global", "icon_global"}
    assert rep["missing_by_lead"]["7"]["missing"] > 0
    assert rep["imd_alignment_by_month"]["2024-02"]["best_lag"] == "+0"


def test_dry_run_publishes_nothing(fakes, imd_dir, tmp_path, monkeypatch):
    monkeypatch.setattr(B, "release_state", lambda tag: "none")
    monkeypatch.setattr(B, "publish", lambda *a, **k: pytest.fail("dry run must not publish"))
    monkeypatch.setattr(B, "commit_index", lambda *a: None)
    monkeypatch.setattr(B, "imd_raw", lambda y, out: pytest.fail("fixture provides IMD"))
    monkeypatch.setattr(B, "ensure_imd", lambda *a: [])
    w = tmp_path / "w"
    import shutil
    shutil.copytree(imd_dir, w / "imd")
    s = B.batch(["2024-02"], tmp_path / "idx", w, 10000, "d1", dry_run=True)
    assert s["months"]["2024-02"] == "dry run: would publish"
    assert (tmp_path / "idx" / "history" / "dryrun" / "d1" / "2024-02.json").exists()
    assert not (tmp_path / "idx" / "history" / "index").exists()


# ---------------------------------------------------------------- M4.3 source-availability classification
from common import CATEGORIES, archive_start, classify_reason  # noqa: E402

ECMWF_START = {"temperature_2m": datetime(2024, 2, 4, 0, tzinfo=timezone.utc),
               "precipitation": datetime(2024, 2, 3, 22, tzinfo=timezone.utc)}


def fake_prev_ecmwf_archive_start(points, model, hourly, leads, u1, u2):
    """ECMWF as observed in release history-2024-02: nothing before the first archived run (lead N starts N-1 days
    after lead 1); plus, for GFS, a genuine mid-record outage of 30 hours at every point."""
    res, url = fake_previous_runs(points, model, hourly, leads, u1, u2)
    ts = _times(u1, u2)
    for r in res:
        for v in hourly:
            for n in leads:
                col = r["hourly"][f"{v}_previous_day{n}"]
                for i, t in enumerate(ts):
                    if model == "ecmwf_ifs025" and v in ECMWF_START and t < ECMWF_START[v] + timedelta(days=n - 1):
                        col[i] = None
                    if model == "gfs_global" and v == "precipitation" and n == 2 and \
                            datetime(2024, 2, 20, 6, tzinfo=timezone.utc) <= t < datetime(2024, 2, 21, 12, tzinfo=timezone.utc):
                        col[i] = None
    return res, url


def test_archive_start_table_matches_audit():
    assert archive_start("ecmwf_ifs025", "temperature_2m", 1) == datetime(2024, 2, 4, 0, tzinfo=timezone.utc)
    assert archive_start("ecmwf_ifs025", "precipitation", 7) == datetime(2024, 2, 9, 22, tzinfo=timezone.utc)
    assert archive_start("gfs_global", "temperature_2m", 1) is None


def test_february_archive_start_rows_classify_as_B_exactly(fakes, imd_dir, tmp_path, monkeypatch):
    """Reproduces the audited 6,804 rows of history-2024-02 (36 points x 4 variables x leads 1-7) as category B,
    including the boundary days with 19 / 21 / 6 hours present; a real outage stays C; gusts stay A."""
    monkeypatch.setattr(sources, "previous_runs", fake_prev_ecmwf_archive_start)
    B.build_month("2024-02", tmp_path, imd_dir)
    q = B.validate_month(tmp_path)
    assert q["publishable"], q["problems"]
    F = pq.read_table(tmp_path / "forecasts_history-2024-02.parquet").to_pandas()
    F["cat"] = F.reason.map(classify_reason)
    b = F[F.cat == "B"]
    assert len(b) == 6804
    assert set(b.model) == {"ecmwf_ifs025"} and set(b.variable) == {"tmax", "tmin", "precip", "precip_0830"}
    assert b.valid_date_ist.min() == date(2024, 2, 1) and b.valid_date_ist.max() == date(2024, 2, 10)
    assert sorted(b.hours_present.unique()) == [0, 6, 19, 21]          # the audited boundary pattern
    assert b.reason.str.startswith("before source archive start").all()
    # after the start, ECMWF (temperature, rain) is complete: no B/C rows later
    assert not F[(F.model == "ecmwf_ifs025") & (F.cat == "C")].shape[0]
    # genuine mid-record outage (GFS rain lead 2, 20-21 Feb) -> C, not B
    c = F[F.cat == "C"]
    assert set(c.model) == {"gfs_global"}
    planted = c[(c.point_id == DROP_POINT) & (c.nominal_lead_day == 1) & c.variable.isin(["tmax", "tmin"])]
    assert len(planted) == 2                                   # the fixture's one-hour gap (tmax and tmin)
    outage = c.drop(planted.index)
    assert set(outage.nominal_lead_day) == {2} and set(outage.variable) == {"precip", "precip_0830"}
    assert outage.point_id.nunique() == 36
    assert c.reason.str.contains("source outage").all() and c.reason.str.contains("retrieval succeeded").all()
    # structural gaps remain A and distinct
    a = F[F.cat == "A"]
    assert set(a.model) == {"ecmwf_ifs025", "icon_global"} and a.reason.str.startswith("not provided by source").all()
    assert q["missing_by_category"]["B"] == 6804


def test_outage_straddling_archive_start_is_not_hidden_as_B(fakes, imd_dir, tmp_path, monkeypatch):
    def prev(points, model, hourly, leads, u1, u2):
        res, url = fake_prev_ecmwf_archive_start(points, model, hourly, leads, u1, u2)
        if model == "ecmwf_ifs025":
            ts = _times(u1, u2)
            for r in res:   # an extra missing hour AFTER the start on the boundary day -> must be C (conservative)
                r["hourly"]["temperature_2m_previous_day1"][ts.index(datetime(2024, 2, 4, 10, tzinfo=timezone.utc))] = None
        return res, url
    monkeypatch.setattr(sources, "previous_runs", prev)
    B.build_month("2024-02", tmp_path, imd_dir)
    F = pq.read_table(tmp_path / "forecasts_history-2024-02.parquet").to_pandas()
    r = F[(F.model == "ecmwf_ifs025") & (F.variable == "tmax") & (F.nominal_lead_day == 1)
          & (F.valid_date_ist == date(2024, 2, 4))].reason
    assert r.str.startswith("source outage: 6 of 24").all()


def test_classifier_covers_all_categories_and_batch1_wording():
    cases = {
        "not provided by source: ecmwf_ifs025 has no wind_gusts_10m at nominal lead 1": "A",
        "METAR reports a gust group only when gusts occur": "A",
        "before source archive start: 5 of 24 hours precede ...": "B",
        "source outage: 3 of 24 hours missing (retrieval succeeded; no interpolation, no substitution)": "C",
        "source hours missing: 24 of 24 (no interpolation, no substitution)": "C",      # m4.3-1 wording (batch 1)
        "source retrieval failed: open-meteo previous-runs icon_global: HTTP 500": "D",
        "IMD 2026 rainfall file not published by the source (checked ...); no substitute used": "E",
        "no METAR reports retrieved for this IST day": "E",
        "incomplete reporting coverage: 0 reports < 20 required; no report in IST 6-h block(s) 00-06h": "E",
        "incomplete reporting coverage: no report in IST 6-h block(s) 00-06h": "F",
        "ERA5 hours missing: 2 of 24": "F",
        "no METAR match: nearest station 55 km > 25 km": "G",
        "no IMD cell within 30 km (nearest valid cell 369 km)": "G",
    }
    for text, cat in cases.items():
        assert classify_reason(text) == cat, text
    assert classify_reason(None) is None
    assert set(CATEGORIES) == set("ABCDEFG")


def test_request_failure_still_refuses_month(fakes, imd_dir, tmp_path, monkeypatch):
    def boom(points, model, *a):
        if model == "ecmwf_ifs025":
            raise HistoryError("previous-runs failed: HTTP 502")
        return fake_previous_runs(points, model, *a)
    monkeypatch.setattr(sources, "previous_runs", boom)
    B.build_month("2024-02", tmp_path, imd_dir)
    q = B.validate_month(tmp_path)
    assert not q["publishable"]
    assert any(p.startswith("source retrieval failed") for p in q["problems"])
    assert all(classify_reason(p) == "D" for p in q["problems"] if p.startswith("source retrieval failed"))


def test_aggregate_applies_annotation_only_with_matching_manifest_hash(tmp_path):
    idx = tmp_path / "idx"
    (idx / "history" / "index").mkdir(parents=True)
    (idx / "history" / "annotations").mkdir(parents=True)
    q = {"expected_values": 100, "values_available": 60, "rows_stored": 100, "matched_rows": 0, "reference_rows": 0,
         "missing_by_reason": {"not provided by source (structural)": 30, "source hours missing": 10},   # batch-1 labels
         "missing_by_model": {}, "missing_by_variable": {}, "missing_by_lead": {}, "missing_by_location": {},
         "reference_coverage": {}, "metar_by_point": {}, "imd_by_point": {},
         "imd_alignment": {"best_lag": "+0", "results": {}}, "anomalies": []}
    write_json(idx / "history" / "index" / "2024-02.json", {"month": "2024-02", "tag": "history-2024-02", "release_url": "u",
                                                            "manifest_sha256": "abc", "quality": q,
                                                            "manifest": {"files": []}})
    ann = {"id": "a1", "release": "history-2024-02", "manifest_sha256": "abc",
           "reclassify": {"from": "C", "to": "B", "rows": 10}}
    write_json(idx / "history" / "annotations" / "a1.json", ann)
    rep = B.aggregate(idx, ["2024-02"])
    assert rep["missing_by_category"] == {"A": 30, "B": 10}
    assert rep["annotations_applied"][0]["applied"] is True
    write_json(idx / "history" / "annotations" / "a1.json", dict(ann, manifest_sha256="WRONG"))
    rep = B.aggregate(idx, ["2024-02"])
    assert rep["missing_by_category"] == {"A": 30, "C": 10}
    assert rep["annotations_applied"][0]["applied"] is False
