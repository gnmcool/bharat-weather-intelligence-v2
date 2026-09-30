"""Known-answer tests for M4.4-B rain event verification (synthetic data; no network). Written and passing before any
event metric touched the real archive."""
from __future__ import annotations

import pathlib
import re
import sys

import numpy as np
import pandas as pd
import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

import events as EV  # noqa: E402
import metrics as MX  # noqa: E402
import run_census  # noqa: E402
import run_events  # noqa: E402
from common import CensusError  # noqa: E402
from test_census import FakeSource, build_month  # noqa: E402
from test_metrics import _dates  # noqa: E402

MONTHS = ("2025-06", "2025-07", "2025-08")
RAIN = ("precip", "precip_0830")


# ---------------------------------------------------------------- pure functions, hand-computed answers

def test_contingency_counts_known():
    f = [40, 70, 0, 0, 36, 10]
    o = [70, 70, 70, 0, 0, 0]
    c = EV.contingency(f, o, 35.6)
    assert (c["hits"], c["misses"], c["false_alarms"], c["correct_negatives"]) == (2, 1, 1, 2)
    assert c["n"] == 6 and c["observed_events"] == 3 and c["forecast_events"] == 3 and c["base_rate"] == 0.5
    c = EV.contingency(f, o, 64.5)
    assert (c["hits"], c["misses"], c["false_alarms"], c["correct_negatives"]) == (1, 2, 0, 3)


def test_ratios_known():
    r = EV.ratios(2, 1, 1)                  # a=2 hits, b=1 false alarm, c=1 miss
    assert r["pod"] == pytest.approx(2 / 3) and r["far"] == pytest.approx(1 / 3)
    assert r["csi"] == pytest.approx(2 / 4) and r["freq_bias"] == pytest.approx(3 / 3)
    r = EV.ratios(10, 30, 5)
    assert (r["pod"], r["far"], r["csi"], r["freq_bias"]) == pytest.approx((10 / 15, 30 / 40, 10 / 45, 40 / 15))


def test_zero_denominators_give_no_value_never_zero():
    assert EV.ratios(0, 0, 0) == {"pod": None, "far": None, "csi": None, "freq_bias": None}
    r = EV.ratios(0, 0, 5)                  # no forecast events: FAR undefined, POD = 0 (a defined zero)
    assert r["far"] is None and r["pod"] == 0.0 and r["freq_bias"] == 0.0
    r = EV.ratios(0, 5, 0)                  # no observed events: POD and frequency bias undefined
    assert r["pod"] is None and r["freq_bias"] is None and r["far"] == 1.0
    c = EV.contingency([], [], 35.6)
    assert c["n"] == 0 and c["base_rate"] is None


def test_thresholds_applied_exactly():
    stored = np.array([35.6, 35.59, 64.5, 64.49, 115.6, 115.5], dtype=np.float32)   # archive storage precision
    assert list(EV.is_event(stored, 35.6)) == [True, False, True, True, True, True]
    assert list(EV.is_event(stored, 64.5)) == [False, False, True, False, True, True]
    assert list(EV.is_event(stored, 115.6)) == [False, False, False, False, True, False]
    with pytest.raises(MX.MetricError, match="not a CORE M-RAIN threshold"):
        EV.is_event([1.0], 50.0)                                                      # no new thresholds
    assert EV.THRESHOLDS == (35.6, 64.5, 115.6)


def test_missing_values_refused_in_pure_functions():
    with pytest.raises(MX.MetricError, match="missing"):
        EV.contingency([40.0, np.nan], [70.0, 0.0], 35.6)


def test_event_floor():
    assert EV.floor_ok(20, 20) == {"pod": True, "far": True, "csi": True, "freq_bias": True}
    assert EV.floor_ok(19, 40) == {"pod": False, "far": True, "csi": False, "freq_bias": False}
    assert EV.floor_ok(40, 19) == {"pod": True, "far": False, "csi": False, "freq_bias": False}


def test_event_bootstrap_known_and_reproducible():
    days = np.repeat(_dates(140), 5)
    o = np.where(np.arange(len(days)) % 4 == 0, 80.0, 0.0)
    r = EV.bootstrap_events(o, o, days, 35.6, "perfect")                  # perfect forecast
    assert r["pod"]["value"] == 1.0 and r["pod"]["ci"] == (1.0, 1.0) and r["far"]["ci"] == (0.0, 0.0)
    assert r["csi"]["ci"] == (1.0, 1.0) and r["freq_bias"]["ci"] == (1.0, 1.0)
    f = np.where(np.random.default_rng(2).random(len(days)) < 0.3, 50.0, 0.0)
    r1 = EV.bootstrap_events(f, o, days, 35.6, "cell")
    r2 = EV.bootstrap_events(f, o, days, 35.6, "cell")
    assert r1 == r2 and r1["seed"] == MX.cell_seed("cell")
    lo, hi = r1["pod"]["ci"]
    assert lo <= r1["pod"]["value"] <= hi


def test_event_bootstrap_undefined_resamples():
    """Events concentrated in one block: many resamples have no events -> interval 'no value', never zero."""
    days = np.repeat(_dates(140), 5)
    o = np.zeros(len(days))
    o[:5] = 80.0                                                             # all events on the first date
    r = EV.bootstrap_events(o, o, days, 35.6, "rare")
    assert r["pod"]["value"] == 1.0 and r["pod"]["undefined_resamples"] > EV.MAX_UNDEFINED_RESAMPLES
    assert r["pod"]["ci"] is None


def test_paired_event_bootstrap():
    days = np.repeat(_dates(140), 5)
    o = np.where(np.arange(len(days)) % 4 == 0, 80.0, 0.0)
    r = EV.paired_bootstrap_events(o, np.full(len(o), 40.0), o, days, 35.6, "pair")
    assert r["a"]["pod"]["value"] == 1.0 and r["b"]["pod"]["value"] == 1.0
    assert r["diff"]["pod"]["value"] == 0.0 and r["diff"]["pod"]["ci"] == (0.0, 0.0)
    assert r["b"]["far"]["value"] == pytest.approx(0.75) and r["diff"]["far"]["value"] == pytest.approx(-0.75)


# ---------------------------------------------------------------- end-to-end synthetic archive

def _month(m):
    M, F, pairing = build_month(m)
    day = pd.to_datetime(M["valid_date_ist"]).dt.day
    rain = M["variable"].isin(RAIN)
    ref = np.where(day % 3 == 0, 70.0, 0.0)
    M.loc[rain & M["reference_available"], "reference_value"] = ref[(rain & M["reference_available"]).values]
    fc = {"ecmwf_ifs025": ref, "gfs_global": np.full(len(M), 40.0), "icon_global": np.zeros(len(M))}
    for mdl, v in fc.items():
        sel = rain & M["forecast_available"] & (M["model"] == mdl)
        M.loc[sel, "forecast_value"] = v[sel.values]
    return M, F, pairing


@pytest.fixture(scope="module")
def ev(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("ev")
    src = FakeSource()
    for m in MONTHS:
        src.add_month(m, *_month(m))
    run_census.run(src, tmp / "census")
    calls = []
    rec = run_events.run(src, tmp / "out", tmp / "census", calls=calls)
    R = pd.read_csv(tmp / "out" / "event_results.csv")
    S = pd.read_csv(tmp / "out" / "event_suppressed_cells.csv")
    C = pd.read_csv(tmp / "census" / "census_cells.csv")
    return src, tmp, rec, R, S, C, calls


def _row(R, cell, subject, metric):
    q = R[(R.event_cell_id == cell) & (R.subject == subject) & (R.metric == metric)]
    assert len(q) == 1, (cell, subject, metric, len(q))
    return q.iloc[0]


def test_known_answers_end_to_end(ev):
    *_, R, S, C, calls = ev
    cell = "B3|single-model|{m}|precip_0830|L1|pooled=all-points|all|all|T{t}"
    e = _row(R, cell.format(m="ecmwf_ifs025", t=35.6), "ecmwf_ifs025", "pod")
    assert (e.hits, e.misses, e.false_alarms, e.correct_negatives) == (300, 0, 0, 620)   # 30 event days x 10 IMD points
    assert e.base_rate == pytest.approx(300 / 920)
    for m, v in (("pod", 1.0), ("far", 0.0), ("csi", 1.0), ("freq_bias", 1.0)):
        assert _row(R, cell.format(m="ecmwf_ifs025", t=35.6), "ecmwf_ifs025", m).value == pytest.approx(v)
    g = {m: _row(R, cell.format(m="gfs_global", t=35.6), "gfs_global", m) for m in EV.RATIOS}
    assert (g["pod"].hits, g["pod"].false_alarms, g["pod"].misses, g["pod"].correct_negatives) == (300, 620, 0, 0)
    assert g["far"].value == pytest.approx(620 / 920) and g["csi"].value == pytest.approx(300 / 920)
    assert g["freq_bias"].value == pytest.approx(920 / 300)
    g = {m: _row(R, cell.format(m="gfs_global", t=64.5), "gfs_global", m) for m in EV.RATIOS}
    assert g["pod"].value == 0.0 and g["pod"].status == "ok"                           # a real zero: 300 misses
    assert all(g[m].status == "insufficient sample" and pd.isna(g[m].value) for m in ("far", "csi", "freq_bias"))
    t = {m: _row(R, cell.format(m="ecmwf_ifs025", t=115.6), "ecmwf_ifs025", m) for m in EV.RATIOS}
    assert all(x.status == "insufficient sample" and pd.isna(x.value) for x in t.values())   # no 115.6 mm events


def test_missing_values_excluded(ev):
    *_, R, S, C, calls = ev
    c = _row(R, "B3|single-model|gfs_global|precip_0830|L2|pooled=all-points|all|all|T35.6", "gfs_global", "pod")
    assert c.n == 10 * (92 - 9) and c.observed_events == 10 * (30 - 3)               # GFS outage days 1-3 excluded


def test_sample_floor_enforced_no_hidden_values(ev):
    *_, R, S, C, calls = ev
    assert not any("T115.6" in x for x in calls)                                      # no event -> never bootstrapped
    insufficient = R[R.status == "insufficient sample"]
    assert insufficient[["value", "ci_low", "ci_high"]].isna().all().all()
    census_fail = {run_events.cell_id(r) for _, r in C.iterrows()
                   if r.experiment in ("A3", "A4") and r.stratum == "all" and r.status != "meets floor"}
    assert set(S.census_cell_id) == census_fail and not (set(R.census_cell_id) & census_fail)
    assert "hits" not in S.columns and "value" not in S.columns
    isl = S[S.census_cell_id.str.contains("region=islands")]
    assert len(isl) and set(isl.status) <= {"insufficient sample", "not defined"}


def test_imd_and_era5_separate(ev):
    *_, R, S, C, calls = ev
    assert set(R[R.experiment == "B3"].reference) == {"imd_rf025"} and set(R[R.experiment == "B4"].reference) == {"era5"}
    b4 = _row(R, "B4|single-model|ecmwf_ifs025|precip|L1|pooled=all-points|all|all|T35.6", "ecmwf_ifs025", "pod")
    assert b4.hits == 12 * 30 and b4.n_points == 12                                   # ERA5 includes the islands
    assert set(R[R.experiment == "B3"].window) == {"imd_0830"} and set(R[R.experiment == "B4"].window) == {"ist_day"}


def test_shared_data_pairing(ev):
    *_, R, S, C, calls = ev
    cell = "B3|shared-data:ecmwf_ifs025+gfs_global|-|precip_0830|L2|pooled=all-points|all|all|T35.6"
    a = _row(R, cell, "ecmwf_ifs025", "pod")
    assert a.n == 10 * 83 and a.observed_events == 270
    d = _row(R, cell, "difference: ecmwf_ifs025 minus gfs_global", "far")
    assert d.value == pytest.approx(0.0 - 560 / 830)                                  # GFS: 560 false alarms of 830
    assert bool(d.interval_excludes_zero) is True
    assert not R.event_cell_id.str.contains(r"icon_global.*\|L7\|").any()               # ICON lead 7 not defined


def test_roles_and_limitations(ev):
    *_, R, S, C, calls = ev
    P = R[R.role == "primary"]
    assert set(P.experiment) == {"B3"} and set(P.geo_slice_type) == {"pooled"} and set(P.season) == {"all"}
    assert P.lead.between(1, 6).all() and not P.comparison.str.count(r"\+").ge(2).any()
    assert set(R[R.experiment == "B4"].role) <= {"secondary", "exploratory"}
    assert set(R[R.lead == 7].role) == {"exploratory"}
    g = R[R.event_cell_id.str.contains("gfs_global") & (R.lead >= 5)]
    assert len(g) and g.limitations.str.contains("source-resolution:gfs-precip-lead5+", regex=False).all()
    assert not R[~R.event_cell_id.str.contains("gfs_global")].limitations.str.contains("source-resolution").any()
    assert not R[R.event_cell_id.str.contains("gfs_global") & (R.lead < 5)].limitations.str.contains(
        "source-resolution").any()


def test_wording(ev):
    src, tmp, rec, R, S, C, calls = ev
    text = " ".join(R.statement) + (tmp / "out" / "event_report.md").read_text()
    for ok in ("not CORE risk verification", "Not CORE risk verification, not CORE alert accuracy, not impact accuracy",
               "does not show that either model is better in general", "No overall score and no model ranking"):
        text = text.replace(ok, "")
    bad = re.findall(r"\b(better|best|worse|superior|outperform\w*|ranking|CORE risk|alert accuracy|impact accuracy)\b",
                     text, re.I)
    assert not bad, bad[:5]


def test_deterministic_and_provenance(ev, tmp_path):
    src, tmp, rec, *_ = ev
    rec2 = run_events.run(src, tmp_path / "again", tmp / "census")
    assert rec2["result_sha256"] == rec["result_sha256"]
    assert rec["methodology_version"] == "VM-1.1" and rec["config"]["thresholds_mm"] == [35.6, 64.5, 115.6]
    assert rec["counts"]["event_cells_with_counts"] + rec["counts"]["event_cells_suppressed_by_census_floor"] == \
        rec["counts"]["event_cells_total"]


def test_tampered_census_refused(ev, tmp_path):
    import shutil
    src, tmp, *_ = ev
    shutil.copytree(tmp / "census", tmp_path / "c")
    p = tmp_path / "c" / "census_cells.csv"
    p.write_text(p.read_text().replace("insufficient sample", "meets floor", 1))
    with pytest.raises(CensusError, match="tampered census"):
        run_events.run(src, tmp_path / "o", tmp_path / "c")
