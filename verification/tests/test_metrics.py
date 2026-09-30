"""Known-answer tests for M4.4-A Gate 2 (bias, MAE, RMSE, block bootstrap, floor enforcement, integrity).

Synthetic data only; no network. Written and passing before any metric touched the real archive.
"""
from __future__ import annotations

import json
import math
import pathlib
import re
import shutil
import sys
from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

import metrics as MX  # noqa: E402
import run_census  # noqa: E402
import run_metrics  # noqa: E402
from common import CensusError  # noqa: E402
from test_census import FakeSource, build_month  # noqa: E402

OFFSET = {"ecmwf_ifs025": 0.0, "gfs_global": 1.0, "icon_global": -0.5}
MONTHS = ("2025-06", "2025-07", "2025-08")


# ---------------------------------------------------------------- pure metric functions (hand-computed answers)

def test_bias_mae_rmse_known_answers():
    f, o = [1.0, 2.0, 3.0, 4.0], [0.0, 0.0, 0.0, 0.0]
    assert MX.bias(f, o) == 2.5 and MX.mae(f, o) == 2.5
    assert MX.rmse(f, o) == pytest.approx(math.sqrt(30 / 4), abs=1e-12)
    f, o = [8.0, 12.0], [10.0, 10.0]                          # errors -2, +2
    assert MX.bias(f, o) == 0.0 and MX.mae(f, o) == 2.0 and MX.rmse(f, o) == 2.0
    f, o = [0.0, 0.0, 3.0], [1.0, 2.0, 0.0]                   # errors -1, -2, +3
    assert MX.bias(f, o) == 0.0 and MX.mae(f, o) == 2.0 and MX.rmse(f, o) == pytest.approx(math.sqrt(14 / 3))


def test_zero_error():
    x = [21.5, 30.0, 12.25]
    assert MX.bias(x, x) == 0.0 and MX.mae(x, x) == 0.0 and MX.rmse(x, x) == 0.0
    dates = [date(2024, 2, 1) + timedelta(days=i) for i in range(70)]
    r = MX.bootstrap(np.zeros(70), dates, "zero")
    assert all(r[m]["value"] == 0.0 and r[m]["ci"] == (0.0, 0.0) for m in MX.METRICS)


@pytest.mark.parametrize("b", [1.5, -0.7])
def test_positive_and_negative_bias(b):
    o = np.linspace(0, 10, 50)
    f = o + b
    assert MX.bias(f, o) == pytest.approx(b) and MX.mae(f, o) == pytest.approx(abs(b))
    assert MX.rmse(f, o) == pytest.approx(abs(b))
    dates = [date(2024, 3, 1) + timedelta(days=i) for i in range(50)]
    r = MX.bootstrap(f - o, dates, "const")
    assert r["bias"]["ci"] == pytest.approx((b, b)) and r["mae"]["ci"] == pytest.approx((abs(b), abs(b)))


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
def test_missing_values_are_refused_never_zero(bad):
    for fn in (MX.bias, MX.mae, MX.rmse):
        with pytest.raises(MX.MetricError, match="missing|non-finite"):
            fn([1.0, bad], [0.0, 0.0])
        with pytest.raises(MX.MetricError):
            fn([1.0, 2.0], [bad, 0.0])
    with pytest.raises(MX.MetricError):
        MX.bootstrap([1.0, bad], [date(2024, 2, 1), date(2024, 2, 20)], "x")


def test_zero_and_invalid_denominator():
    assert MX.bias([], []) is None and MX.mae([], []) is None and MX.rmse([], [])is None   # n = 0: no metric
    with pytest.raises(MX.MetricError, match="empty"):
        MX.bootstrap([], [], "empty")
    with pytest.raises(MX.MetricError, match="equal length"):
        MX.bias([1.0, 2.0], [1.0])
    with pytest.raises(MX.MetricError, match="fewer than 2 blocks"):          # one block: interval undefined
        MX.bootstrap([1.0, 2.0, 3.0], [date(2024, 2, 1)] * 3, "one-block")
    with pytest.raises(MX.MetricError, match="same shared-data pairs"):
        MX.paired_bootstrap([1.0, 2.0], [1.0], [date(2024, 2, 1), date(2024, 2, 9)], "p")
    with pytest.raises(MX.MetricError, match="before the block origin"):
        MX.bootstrap([1.0, 2.0], [date(2024, 1, 1), date(2024, 2, 9)], "early")


def test_blocks_are_fixed_7_day_calendar_blocks():
    d = [date(2024, 2, 1), date(2024, 2, 7), date(2024, 2, 8), date(2024, 2, 14), date(2024, 2, 15)]
    assert list(MX.block_ids(d)) == [0, 0, 1, 1, 2]


# ---------------------------------------------------------------- bootstrap behaviour

def _dates(n_days, start=date(2024, 2, 1)):
    return [start + timedelta(days=i) for i in range(n_days)]


def test_bootstrap_reproducible_and_order_independent():
    rng = np.random.default_rng(1)
    days = _dates(200)
    e = rng.normal(0.5, 2.0, 200 * 10)
    d = np.repeat(days, 10)
    r1, r2 = MX.bootstrap(e, d, "cellA"), MX.bootstrap(e, d, "cellA")
    assert r1 == r2                                                        # fixed seed: identical
    perm = rng.permutation(len(e))
    r3 = MX.bootstrap(e[perm], d[perm], "cellA")                          # row order does not matter
    for m in MX.METRICS:
        assert r3[m]["ci"] == pytest.approx(r1[m]["ci"], abs=1e-9)
    assert MX.bootstrap(e, d, "cellB")["bias"]["ci"] != r1["bias"]["ci"]  # seed is per cell
    assert MX.cell_seed("cellA") == MX.cell_seed("cellA") != MX.cell_seed("cellB")


def test_bootstrap_known_iid_behaviour_and_coverage():
    """Independent N(1, 2^2) errors: interval width ~ 2 x 1.96 x 2/sqrt(n); ~95% coverage of the true mean."""
    days = np.repeat(_dates(420), 10)
    n = len(days)
    covered, widths = 0, []
    for k in range(200):
        e = np.random.default_rng(1000 + k).normal(1.0, 2.0, n)
        lo, hi = MX.bootstrap(e, days, f"cov{k}")["bias"]["ci"]
        covered += lo <= 1.0 <= hi
        widths.append(hi - lo)
    assert 0.88 <= covered / 200 <= 0.99
    assert np.mean(widths) == pytest.approx(2 * 1.96 * 2.0 / math.sqrt(n), rel=0.15)


def test_bootstrap_keeps_whole_dates_together():
    """A shock shared by all points on a date must widen the interval (spatial correlation preserved)."""
    rng = np.random.default_rng(7)
    days = _dates(420)
    shock = np.repeat(rng.normal(0, 2.0, len(days)), 10)
    d = np.repeat(days, 10)
    e = shock + rng.normal(0, 0.1, len(d))
    lo, hi = MX.bootstrap(e, d, "corr")["bias"]["ci"]
    naive = 2 * 1.96 * e.std() / math.sqrt(len(e))                         # treats 4,200 pairs as independent
    assert (hi - lo) > 2.5 * naive


def test_paired_difference_same_blocks():
    days = np.repeat(_dates(140), 5)
    a = np.random.default_rng(3).normal(0, 1, len(days))
    r = MX.paired_bootstrap(a + 0.25, a, days, "pair")
    assert r["diff"]["bias"]["value"] == pytest.approx(0.25)
    assert r["diff"]["bias"]["ci"] == pytest.approx((0.25, 0.25))          # same blocks: constant shift has no spread
    s = MX.bootstrap(a + 0.25, days, "pair")
    assert r["a"]["mae"] == s["mae"]                                       # same seed, same blocks as single-model


# ---------------------------------------------------------------- end-to-end on a synthetic archive

def _source():
    src = FakeSource()
    for m in MONTHS:
        M, F, pairing = build_month(m)
        M["forecast_value"] = M["forecast_value"] + M["model"].map(OFFSET).where(M["forecast_available"])
        src.add_month(m, M, F, pairing)
    return src


@pytest.fixture(scope="module")
def gate2(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("g2")
    src = _source()
    crec = run_census.run(src, tmp / "census")
    calls = []
    orig = MX.bootstrap, MX.paired_bootstrap
    run_metrics.MX.bootstrap = lambda e, d, cid, **k: (calls.append(cid), orig[0](e, d, cid, **k))[1]
    run_metrics.MX.paired_bootstrap = lambda a, b, d, cid, **k: (calls.append(cid), orig[1](a, b, d, cid, **k))[1]
    try:
        rec = run_metrics.run(src, tmp / "metrics", tmp / "census")
    finally:
        run_metrics.MX.bootstrap, run_metrics.MX.paired_bootstrap = orig
    R = pd.read_csv(tmp / "metrics" / "metric_results.csv")
    C = pd.read_csv(tmp / "census" / "census_cells.csv")
    return src, tmp, crec, rec, R, C, calls


def _v(R, cell, subject, metric):
    q = R[(R.cell_id == cell) & (R.subject == subject) & (R.metric == metric)]
    assert len(q) == 1, (cell, subject, metric, len(q))
    return q.iloc[0]


def test_known_answer_station_metrics(gate2):
    *_, R, _, _ = gate2
    # VIDP, GFS Tmax lead 1: forecast 31, reference 5 on odd days (47) and 1 on even days (45), Jun-Aug 2025
    cell = "A2|single-model|gfs_global|tmax|L1|station=VIDP|all|all"
    b, m, r = (_v(R, cell, "gfs_global", k) for k in ("bias", "mae", "rmse"))
    assert b.n == 92 and b.n_dates == 92 and b.n_points == 1
    assert b.value == pytest.approx((47 * 26 + 45 * 30) / 92, abs=1e-6) and m.value == pytest.approx(b.value, abs=1e-6)
    assert r.value == pytest.approx(math.sqrt((47 * 26 ** 2 + 45 * 30 ** 2) / 92), abs=1e-6)
    assert b.role == "primary" and b.ci_low <= b.value <= b.ci_high
    assert b.point_elev_m == 200 and b.metar_elev_diff_m == 10.0                  # elevation recorded, not adjusted


def test_sample_floor_enforced(gate2):
    *_, R, C, calls = gate2
    meets = {run_metrics.cell_id(r) for _, r in C.iterrows() if r.status == "meets floor"}
    others = {run_metrics.cell_id(r) for _, r in C.iterrows() if r.status != "meets floor"}
    assert set(R.cell_id) == meets                                             # every floor cell, nothing else
    assert not (set(calls) & others)                                           # no hidden computation either
    assert set(calls) == meets
    S = pd.read_csv(gate2[1] / "metrics" / "suppressed_cells.csv")
    assert set(S.cell_id) == others and not ({"value", "ci_low", "ci_high"} & set(S.columns))
    assert "A2|single-model|gfs_global|tmax|L1|station=VOTR|all|all" in others   # 86 days < 90
    assert "A1|single-model|gfs_global|tmax|L1|region=islands|all|all" in others  # islands: insufficient sample
    assert "A1|single-model|icon_global|tmax|L7|pooled=all-points|all|all" in others


def test_islands_in_pooled_results(gate2):
    *_, R, _, _ = gate2
    b = _v(R, "A1|single-model|gfs_global|tmax|L1|pooled=all-points|all|all", "gfs_global", "bias")
    assert b.n_points == 12                                                    # includes both island points
    b = _v(R, "A3|single-model|gfs_global|precip_0830|L1|pooled=all-points|all|all", "gfs_global", "bias")
    assert b.n_points == 10                                                    # islands G for IMD only


def test_shared_data_pairing(gate2):
    *_, R, C, _ = gate2
    cell = "A4|shared-data:ecmwf_ifs025+gfs_global|-|precip|L2|pooled=all-points|all|all"
    d = _v(R, cell, "difference: ecmwf_ifs025 minus gfs_global", "bias")
    assert d.n == 12 * (92 - 9)                                                # GFS outage days 1-3 of each month drop
    assert d.value == pytest.approx(-1.0) and (d.ci_low, d.ci_high) == pytest.approx((-1.0, -1.0))
    assert bool(d.interval_excludes_zero) is True
    a = _v(R, cell, "ecmwf_ifs025", "mae")
    single = _v(R, "A4|single-model|ecmwf_ifs025|precip|L2|pooled=all-points|all|all", "ecmwf_ifs025", "mae")
    assert single.n == 12 * 92 and a.n == 12 * 83                              # shared sample differs from single-model
    d7 = R[R.cell_id.str.contains(r"shared-data:ecmwf_ifs025\+icon_global") & R.cell_id.str.contains("L7")]
    assert d7.empty                                                            # ICON lead 7 not defined: never computed
    three = R[R.comparison == "shared-data:ecmwf_ifs025+gfs_global+icon_global"]
    assert set(three.role) == {"exploratory"} and not three.subject.str.startswith("difference").any()


def test_primary_and_exploratory_roles(gate2):
    *_, R, _, _ = gate2
    P = R[R.role == "primary"]
    assert set(P.experiment) == {"A2", "A3"} and set(P.season) == {"all"} and set(P.stratum) == {"all"}
    assert P.lead.between(1, 6).all() and set(P.geo_slice_type) <= {"station", "pooled"}
    assert not P.comparison.str.count(r"\+").ge(2).any()
    X = R[R.role == "exploratory"]
    assert set(R[R.reference == "era5"].role) == {"exploratory"}
    assert set(R[R.lead == 7].role) == {"exploratory"}
    assert set(R[R.geo_slice_type.isin(["region", "high_altitude"])].role) == {"exploratory"}
    assert "ERA5 comparison" in set(X.role_basis.str.split("; ").explode())
    M = pd.read_csv(gate2[1] / "metrics" / "comparison_metadata.csv")
    assert set(M.cell_id) == set(R.cell_id) and set(M.role) == {"primary", "exploratory"}


def test_no_superiority_language(gate2):
    *_, R, _, _ = gate2
    text = " ".join(R.statement) + (gate2[1] / "metrics" / "metric_report.md").read_text()
    text = text.replace("does not show that either model is better in general", "")
    text = text.replace("They do not show that any model is better in general", "")
    text = text.replace("No overall score and no model ranking are produced", "")
    assert not re.search(r"\b(better|best|worse|worst|superior|outperform\w*|wins?|rank\w*|score)\b", text, re.I), \
        re.findall(r"\b(better|best|worse|worst|superior|outperform\w*|wins?|rank\w*|score)\b", text, re.I)[:5]


def test_provenance_record(gate2):
    src, tmp, crec, rec, *_ = gate2
    assert rec["methodology_version"] == "VM-1.1" and rec["census_version"] == "m4.4-a-census-2"
    assert rec["census_cells_sha256"] == crec["result_sha256"]["census_cells.csv"]
    assert [r["manifest_sha256"] for r in rec["releases"]] == [src.recs[m]["manifest_sha256"] for m in MONTHS]
    assert rec["code_commit"] and rec["config"]["resamples"] == 1000 and rec["config"]["block_days"] == 7
    assert rec["result_sha256"]["metric_results.csv"] == \
        __import__("hashlib").sha256((tmp / "metrics" / "metric_results.csv").read_bytes()).hexdigest()
    assert rec["counts"]["cells_computed"] + rec["counts"]["cells_suppressed"] == rec["counts"]["census_cells"]


def test_deterministic(gate2, tmp_path):
    src, tmp, _, rec, *_ = gate2
    rec2 = run_metrics.run(src, tmp_path / "again", tmp / "census")
    assert rec2["result_sha256"] == rec["result_sha256"]


# ---------------------------------------------------------------- integrity: tampered inputs are refused

def test_tampered_census_refused(gate2, tmp_path):
    src, tmp, *_ = gate2
    cdir = tmp_path / "c"
    shutil.copytree(tmp / "census", cdir)
    C = pd.read_csv(cdir / "census_cells.csv")
    i = C.index[C.status == "insufficient sample"][0]
    C.loc[i, "status"] = "meets floor"                                         # try to unlock a suppressed cell
    C.to_csv(cdir / "census_cells.csv", index=False)
    with pytest.raises(CensusError, match="tampered census"):
        run_metrics.run(src, tmp_path / "o", cdir)
    rec = json.loads((cdir / "census_run.json").read_text())                   # ... even with its hash updated
    rec["result_sha256"]["census_cells.csv"] = __import__("hashlib").sha256((cdir / "census_cells.csv").read_bytes()).hexdigest()
    (cdir / "census_run.json").write_text(json.dumps(rec))
    with pytest.raises(CensusError, match="differs from the published census"):
        run_metrics.run(src, tmp_path / "o2", cdir)


def test_tampered_release_refused(gate2, tmp_path):
    src, tmp, *_ = gate2
    bad = _source()
    tag = "history-2025-07"
    name = "matched_history-2025-07.parquet"
    bad.assets[tag][name] = bad.assets[tag][name] + b"x"
    with pytest.raises(CensusError, match="tampered"):
        run_metrics.run(bad, tmp_path / "o", tmp / "census")
    bad2 = _source()
    bad2.rel["history-2025-06"] = {"draft": False, "immutable": False}
    with pytest.raises(CensusError, match="immutable"):
        run_metrics.run(bad2, tmp_path / "o2", tmp / "census")


def test_census_from_other_releases_refused(gate2, tmp_path):
    src, tmp, *_ = gate2
    cdir = tmp_path / "c"
    shutil.copytree(tmp / "census", cdir)
    rec = json.loads((cdir / "census_run.json").read_text())
    rec["releases"][0]["manifest_sha256"] = "0" * 64
    (cdir / "census_run.json").write_text(json.dumps(rec))
    with pytest.raises(CensusError, match="different releases"):
        run_metrics.run(src, tmp_path / "o", cdir)


def test_february_annotation_required(tmp_path):
    src = FakeSource()
    src.add_month("2024-02", *build_month("2024-02", feb_archive_start=True))  # no annotation recorded
    run_census.run(src, tmp_path / "c")
    with pytest.raises(CensusError, match="2024-02-ecmwf-archive-start"):
        run_metrics.run(src, tmp_path / "o", tmp_path / "c")
