"""Offline tests for the immutable daily archive (collect -> validate). No network: sources are mocked."""
import json
import pathlib
import sys
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest
import xarray as xr

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import collect  # noqa: E402
import common  # noqa: E402
import validate  # noqa: E402

RUN = datetime(2026, 9, 28, 0, tzinfo=timezone.utc)          # 00Z run = 05:30 IST on 28 Sep
RETRIEVED = datetime(2026, 9, 28, 5, 40, tzinfo=timezone.utc)
PTS = json.loads((HERE / "points.json").read_text())["points"]


# ---------------- pure time rules ----------------
def test_lead_day_uses_ist_date_of_run():
    assert common.lead_day(date(2026, 9, 29), RUN) == 1
    late = datetime(2026, 9, 27, 18, tzinfo=timezone.utc)      # 18Z = 23:30 IST, still 27 Sep IST
    assert common.lead_day(date(2026, 9, 28), late) == 1
    later = datetime(2026, 9, 27, 19, tzinfo=timezone.utc)     # 19Z = 00:30 IST on 28 Sep
    assert common.lead_day(date(2026, 9, 28), later) == 0


def test_day_coverage():
    end = RUN + timedelta(days=6, hours=9)                      # ECMWF-like 06Z-style short run
    assert not common.day_fully_covered(date(2026, 9, 28), RUN, end, 3)   # lead 0 starts before the run
    assert common.day_fully_covered(date(2026, 9, 29), RUN, end, 3)
    assert not common.day_fully_covered(date(2026, 10, 4), RUN, end, 3)   # beyond the last valid time


# ---------------- end-to-end with mocked sources ----------------
@pytest.fixture()
def store(tmp_path):
    times = pd.date_range("2026-09-28T03:00", periods=80, freq="3h")
    lat = np.arange(6.0, 38.5, 0.25, dtype="float32")
    lon = np.arange(66.0, 99.5, 0.25, dtype="float32")
    shape = (len(times), len(lat), len(lon))
    ds = xr.Dataset({"tp": (("time", "lat", "lon"), np.ones(shape, "float32")),
                     "t2m": (("time", "lat", "lon"), np.full(shape, 25, "float32")),
                     "fg10m": (("time", "lat", "lon"), np.full(shape, 10, "float32"))},
                    coords={"time": times, "lat": lat, "lon": lon}, attrs={"issue_time": "2026-09-28T00:00:00+00:00"})
    p = tmp_path / "store.nc"
    ds.to_netcdf(p)
    return p


CORE_IDS = ["heat", "cold", "rain", "wind", "thunderstorm", "lightning", "flood", "drought", "fog", "fire", "cyclone"]
FLOOD_EXPLANATION = {"dry": "Rain-based indicator only (no river/drainage model).",
                     "wet": "Rain-based indicator only (no river/drainage model). Soil already wet."}
CORE_FIXTURE = {"flood_explanation": FLOOD_EXPLANATION["dry"], "drop_criterion": None}


def core_risks_fixture():
    """11 CORE items per point, shaped like CORE core-v1.0 RiskItem (criterion on every item; flood explanation)."""
    out = []
    for rid in CORE_IDS:
        r = {"id": rid, "level": 0, "status": "No risk", "confidence": {"basis": "3 of 3"},
             "criterion": f"core-v1.0 rule text for {rid}", "explanation": f"explanation for {rid}"}
        if rid == "flood":
            r["explanation"] = CORE_FIXTURE["flood_explanation"]
        if rid == CORE_FIXTURE["drop_criterion"]:
            del r["criterion"]
        out.append(r)
    return out


@pytest.fixture(autouse=True)
def _reset_core_fixture():
    CORE_FIXTURE.update(flood_explanation=FLOOD_EXPLANATION["dry"], drop_criterion=None)
    yield


def fake_http(url, timeout=90, tries=4):
    if "/static/meta.json" in url:
        days = 6 if "ecmwf" in url else 15
        return {"last_run_initialisation_time": int(RUN.timestamp()), "last_run_availability_time": int((RUN + timedelta(hours=5)).timestamp()),
                "data_end_time": int((RUN + timedelta(days=days, hours=9)).timestamp()), "temporal_resolution_seconds": 3600}
    if "/dashboard" in url:
        return {"generated_at": "2026-09-28T05:41:00Z", "warnings": [],
                "sources": [{"issue_time": "x", "notes": "Per-model runs used for confidence (...)"}],
                "risks": core_risks_fixture(),
                "daily": [{"date": (date(2026, 9, 28) + timedelta(days=k)).isoformat(), "temperature_2m_max": 30, "temperature_2m_min": 20,
                           "precipitation_sum": 1, "wind_gusts_10m_max": 20} for k in range(10)]}
    # Open-Meteo multi-location daily: ECMWF-like model has no data after its last valid time
    short = "ecmwf" in url
    out = []
    for _ in PTS:
        dates = [(date(2026, 9, 28) + timedelta(days=k)).isoformat() for k in range(10)]
        val = lambda base: [None if short and k > 6 else base + k * 0.1 for k in range(10)]  # noqa: E731
        out.append({"daily": {"time": dates, "temperature_2m_max": val(30), "temperature_2m_min": val(20),
                              "precipitation_sum": val(1), "wind_gusts_10m_max": val(20)}})
    return out


def run_collect(tmp_path, store, inject="none", monkeypatch=None):
    monkeypatch.setattr(collect, "http_json", fake_http)
    monkeypatch.setattr(sys, "argv", ["collect.py", "--out", str(tmp_path / "stage"), "--store", str(store), "--inject", inject])
    assert collect.main() == 0
    return tmp_path / "stage"


def test_complete_archive_is_publishable(tmp_path, store, monkeypatch):
    stage = run_collect(tmp_path, store, monkeypatch=monkeypatch)
    res = validate.validate(stage)
    assert res["ok"], res["problems"]
    g = res["gaps"]
    assert not g["missing"]
    assert any(x["model"] == "ecmwf_ifs025" and x["leads"] for x in g["not_provided_by_source"])  # beyond the short run
    df = pq.read_table(next(stage.glob("forecasts_*.parquet"))).to_pandas()
    assert set(df["model"]) == {"ecmwf_ifs025", "gfs_global", "icon_global", "e2s_gfs025"}
    assert df["run_time_known"].all()


def test_run_time_and_valid_date_are_distinct_types(tmp_path, store, monkeypatch):
    stage = run_collect(tmp_path, store, monkeypatch=monkeypatch)
    t = pq.read_table(next(stage.glob("forecasts_*.parquet")))
    assert str(t.schema.field("run_time_utc").type) == "timestamp[ms, tz=UTC]"
    assert str(t.schema.field("valid_date_ist").type) == "date32[day]"
    df = t.to_pandas()
    assert (df["run_time_utc"] == pd.Timestamp(RUN)).loc[df["model"] != "e2s_gfs025"].all()


def test_manifest_checksums_match(tmp_path, store, monkeypatch):
    stage = run_collect(tmp_path, store, monkeypatch=monkeypatch)
    man = json.loads(next(stage.glob("manifest_*.json")).read_text())
    for f in man["files"]:
        assert common.sha256(stage / f["name"]) == f["sha256"]


@pytest.mark.parametrize("inject,expect", [("checksum", "checksum mismatch"), ("missing_row", "expected forecast values missing"),
                                           ("bad_lead", "lead_day inconsistent")])
def test_injected_faults_are_refused(tmp_path, store, monkeypatch, inject, expect):
    stage = run_collect(tmp_path, store, inject, monkeypatch)
    res = validate.validate(stage)
    assert not res["ok"]
    assert any(expect in p for p in res["problems"]), res["problems"]


def test_failed_model_is_refused(tmp_path, store, monkeypatch):
    def broken(url, timeout=90, tries=4):
        if "models=gfs_global" in url:
            raise common.ArchiveError("simulated outage")
        return fake_http(url)
    monkeypatch.setattr(collect, "http_json", broken)
    monkeypatch.setattr(sys, "argv", ["collect.py", "--out", str(tmp_path / "s"), "--store", str(store)])
    collect.main()
    res = validate.validate(tmp_path / "s")
    assert not res["ok"] and any("gfs_global missing entirely" in p for p in res["problems"])


def test_unit_mixup_is_refused(tmp_path, store, monkeypatch):
    stage = run_collect(tmp_path, store, monkeypatch=monkeypatch)
    f = next(stage.glob("forecasts_*.parquet"))
    df = pq.read_table(f).to_pandas()
    df.loc[df["variable"] == "gust_max", "value"] *= 100          # e.g. cm/s by mistake
    import pyarrow as pa
    pq.write_table(pa.Table.from_pandas(df, schema=common.FORECAST_SCHEMA, preserve_index=False), f, compression="zstd")
    man_p = next(stage.glob("manifest_*.json"))
    man = json.loads(man_p.read_text())
    for x in man["files"]:
        if x["name"] == f.name:
            x["sha256"] = common.sha256(f)
    man_p.write_text(json.dumps(man))
    res = validate.validate(stage)
    assert not res["ok"] and any("plausible range" in p for p in res["problems"])


def test_points_file_is_fixed_and_valid():
    assert len(PTS) == 36 and len({p["id"] for p in PTS}) == 36
    for p in PTS:
        assert 5 <= p["lat"] <= 38 and 66 <= p["lon"] <= 99


def test_grids_disagreeing_on_run_time_is_refused(tmp_path, store, monkeypatch):
    def split(url, timeout=90, tries=4):
        r = fake_http(url)
        if "ncep_gfs013" in url:
            r = {**r, "last_run_initialisation_time": r["last_run_initialisation_time"] - 21600}
        return r
    monkeypatch.setattr(collect, "http_json", split)
    monkeypatch.setattr(collect.time, "sleep", lambda s: None)
    monkeypatch.setattr(sys, "argv", ["collect.py", "--out", str(tmp_path / "s"), "--store", str(store)])
    collect.main()
    res = validate.validate(tmp_path / "s")
    assert not res["ok"] and any("gfs_global" in p for p in res["problems"])


# ---------------- M4.4-D D1: CORE rule text and flood wet-soil flag ----------------
def _core(stage):
    return pq.read_table(next(stage.glob("core_risks_*.parquet")))


def test_d1_rule_text_and_flood_flag_captured(tmp_path, store, monkeypatch):
    stage = run_collect(tmp_path, store, monkeypatch=monkeypatch)
    assert validate.validate(stage)["ok"]
    t = _core(stage)
    assert t.schema.equals(common.CORE_RISK_SCHEMA, check_metadata=False)
    df = t.to_pandas()
    assert df["criterion"].notna().all() and (df["criterion"] == "core-v1.0 rule text for " + df["risk_id"]).all()
    assert (df.loc[df.risk_id == "flood", "flood_wet_soil"] == False).all()   # noqa: E712
    assert df.loc[df.risk_id != "flood", "flood_wet_soil"].isna().all()
    man = json.loads(next(stage.glob("manifest_*.json")).read_text())
    assert man["schema_version"] == common.SCHEMA_VERSION == 2


def test_d1_wet_soil_flag_true(tmp_path, store, monkeypatch):
    CORE_FIXTURE["flood_explanation"] = FLOOD_EXPLANATION["wet"] + " Official: CWC has an active flood warning."
    stage = run_collect(tmp_path, store, monkeypatch=monkeypatch)
    assert validate.validate(stage)["ok"]
    df = _core(stage).to_pandas()
    assert (df.loc[df.risk_id == "flood", "flood_wet_soil"] == True).all()     # noqa: E712


def test_d1_missing_rule_text_is_refused(tmp_path, store, monkeypatch):
    CORE_FIXTURE["drop_criterion"] = "rain"
    stage = run_collect(tmp_path, store, monkeypatch=monkeypatch)
    res = validate.validate(stage)
    assert not res["ok"] and any("criterion" in p and "36 core_risks rows" in p for p in res["problems"]), res["problems"]


def test_d1_unknown_flood_text_is_refused_never_guessed(tmp_path, store, monkeypatch):
    CORE_FIXTURE["flood_explanation"] = "Some other wording. Soil already wet."
    stage = run_collect(tmp_path, store, monkeypatch=monkeypatch)
    res = validate.validate(stage)
    assert not res["ok"] and any("wet-soil flag not determinable" in p for p in res["problems"]), res["problems"]
    assert _core(stage).to_pandas().query("risk_id == 'flood'")["flood_wet_soil"].isna().all()


def _rewrite_core(stage, mutate):
    """Rewrite core_risks and its manifest entry consistently (so only rule 7 can fail)."""
    f = next(stage.glob("core_risks_*.parquet"))
    t = mutate(pq.read_table(f))
    pq.write_table(t, f)
    mp = next(stage.glob("manifest_*.json"))
    man = json.loads(mp.read_text())
    for e in man["files"]:
        if e["name"] == f.name:
            e["sha256"], e["rows"], e["bytes"] = common.sha256(f), t.num_rows, f.stat().st_size
    mp.write_text(json.dumps(man))


def test_d1_flag_on_non_flood_row_is_refused(tmp_path, store, monkeypatch):
    stage = run_collect(tmp_path, store, monkeypatch=monkeypatch)
    import pyarrow as pa

    def mutate(t):
        df = t.to_pandas()
        df.loc[df.risk_id == "rain", "flood_wet_soil"] = True
        return pa.Table.from_pandas(df, schema=common.CORE_RISK_SCHEMA, preserve_index=False)
    _rewrite_core(stage, mutate)
    res = validate.validate(stage)
    assert not res["ok"] and any("non-flood rows" in p for p in res["problems"]), res["problems"]


def test_d1_old_v1_core_table_cannot_be_published(tmp_path, store, monkeypatch):
    stage = run_collect(tmp_path, store, monkeypatch=monkeypatch)
    _rewrite_core(stage, lambda t: t.select(common.CORE_RISK_SCHEMA_V1.names))
    res = validate.validate(stage)
    assert not res["ok"] and any("core_risks schema differs" in p for p in res["problems"]), res["problems"]


def test_d1_existing_v1_releases_remain_readable_and_flagged(tmp_path):
    import pyarrow as pa
    row = {f.name: None for f in common.CORE_RISK_SCHEMA_V1}
    row.update(point_id="IN-07-delhi", risk_id="rain", level=0, official=False, experimental=False)
    t = pa.Table.from_pylist([row], schema=common.CORE_RISK_SCHEMA_V1)
    assert "criterion" not in t.schema.names
    assert common.core_rule_text_status(1) == common.RULE_TEXT_NOT_ARCHIVED == "rule text not archived"
    assert common.core_rule_text_status(2) == "archived"


@pytest.mark.parametrize("text,flag", [
    ("Rain-based indicator only (no river/drainage model).", False),
    ("Rain-based indicator only (no river/drainage model). Soil already wet.", True),
    ("Rain-based indicator only (no river/drainage model). Official: CWC has an active flood warning.", False),
    ("Rain-based indicator only (no river/drainage model). Soil already wet. Official: x", True),
    ("Rain-based indicator only (no river/drainage model). Official: note says Soil already wet.", False),
    ("", None), (None, None), ("Soil already wet.", None)])
def test_d1_flood_flag_parser(text, flag):
    assert common.flood_wet_soil_flag(text) is flag



def test_manifest_carries_open_meteo_attribution(tmp_path, store, monkeypatch):
    stage = run_collect(tmp_path, store, monkeypatch=monkeypatch)
    man = json.loads(next(stage.glob("manifest_*.json")).read_text())
    lic = man["data_licences"]
    assert lic[0]["licence"] == "CC BY 4.0" and lic[0]["attribution"] == "Weather data by Open-Meteo.com"
    assert lic[0]["licence_url"] == "https://creativecommons.org/licenses/by/4.0/"
