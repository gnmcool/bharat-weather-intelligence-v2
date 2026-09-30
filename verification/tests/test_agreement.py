"""Known-answer tests for M4.4-C model agreement and the degenerate-interval reporting label (synthetic; no network)."""
from __future__ import annotations

import pathlib
import re
import sys

import numpy as np
import pandas as pd
import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

import agreement as AG  # noqa: E402
import metrics as MX  # noqa: E402
import reporting as RP  # noqa: E402
import run_agreement  # noqa: E402
import run_census  # noqa: E402
from test_census import FakeSource  # noqa: E402
from test_events import MONTHS, _month  # noqa: E402
from test_metrics import _dates  # noqa: E402


# ---------------------------------------------------------------- reporting label
def test_degenerate_label_only_at_boundary():
    assert RP.label("pod", 0.0, 0.0, 0.0) == RP.DEGENERATE_LABEL
    assert RP.label("far", 1.0, 1.0, 1.0) == RP.DEGENERATE_LABEL
    assert RP.label("frequency", 1.0, 1.0, 1.0) == RP.DEGENERATE_LABEL
    assert RP.label("pod", 0.4, 0.4, 0.4) is None                 # zero width but not a boundary value
    assert RP.label("pod", 0.0, 0.0, 0.1) is None                 # boundary value but a real interval
    assert RP.label("freq_bias", 1.0, 1.0, 1.0) is None           # 1 is not a boundary for frequency bias
    assert RP.label("mae", 0.0, 0.0, 0.0) is None                 # continuous metrics: not labelled
    assert RP.label("pod", 0.0, None, None) is None
    assert "does not imply statistical certainty" in RP.DEGENERATE_LABEL


# ---------------------------------------------------------------- pure agreement functions
def test_k_and_members():
    f = {"ecmwf_ifs025": [70, 0, 40, 0], "gfs_global": [40, 40, 0, 0], "icon_global": [70, 0, 36, 0]}
    k, mem = AG.k_and_members(f, 35.6)
    assert list(k) == [3, 1, 2, 0] and list(mem) == ["ECMWF+GFS+ICON", "GFS", "ECMWF+ICON", "-"]
    k, _ = AG.k_and_members(f, 64.5)
    assert list(k) == [2, 0, 0, 0]
    with pytest.raises(MX.MetricError, match="ECMWF, GFS and ICON only"):
        AG.k_and_members({"ecmwf_ifs025": [1], "gfs_global": [1], "e2s_gfs025": [1]}, 35.6)


def test_group_counts_and_floor():
    assert AG.group_counts(["k=1", "k=1", "k=2"], [True, False, True]) == {"k=1": (2, 1), "k=2": (1, 1)}
    assert AG.floor_ok(100, 10) and not AG.floor_ok(99, 50) and not AG.floor_ok(500, 9)


def test_group_bootstrap_known_reproducible_shared_draws():
    days = np.repeat(_dates(140), 5)
    rng = np.random.default_rng(4)
    groups = rng.choice(["k=0", "k=1", "k=2"], len(days))
    obs = rng.random(len(days)) < np.where(groups == "k=2", 0.6, 0.1)
    r1 = AG.bootstrap_groups(groups, obs, days, "cell", {"k=1", "k=2"})
    r2 = AG.bootstrap_groups(groups, obs, days, "cell", {"k=1", "k=2"})
    assert r1 == r2 and set(r1["groups"]) == {"k=1", "k=2"}              # nothing for k=0 (not requested)
    g = r1["groups"]["k=2"]
    assert g["value"] == pytest.approx(obs[groups == "k=2"].mean()) and g["ci"][0] <= g["value"] <= g["ci"][1]
    solo = AG.bootstrap_groups(groups, obs, days, "cell", {"k=2"})
    assert solo["groups"]["k=2"] == r1["groups"]["k=2"]                   # one draw matrix per cell, shared by groups
    assert r1["seed"] == MX.cell_seed("cell")


# ---------------------------------------------------------------- end to end
@pytest.fixture(scope="module")
def ag(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("ag")
    src = FakeSource()
    for m in MONTHS:
        src.add_month(m, *_month(m))       # reference 70 mm every 3rd day; ECMWF = reference; GFS 40; ICON 0
    run_census.run(src, tmp / "census")
    calls = []
    rec = run_agreement.run(src, tmp / "out", tmp / "census", calls=calls)
    R = pd.read_csv(tmp / "out" / "agreement_results.csv")
    return src, tmp, rec, R, calls


def _g(R, exp, analysis, lead, thr, group):
    q = R[(R.experiment == exp) & (R.analysis == analysis) & (R.lead == lead) & (R.threshold_mm == thr) & (R.group == group)]
    assert len(q) == 1, (exp, analysis, lead, thr, group, len(q))
    return q.iloc[0]


def test_known_answers(ag):
    *_, R, calls = ag
    k2 = _g(R, "C3", "k-groups", 1, 35.6, "k=2")          # event days: ECMWF 70 + GFS 40 -> k=2, reference 70
    assert (k2.n, k2.reference_events, k2.frequency, k2.status) == (300, 300, 1.0, "ok")
    assert k2.interval_note == RP.DEGENERATE_LABEL and (k2.ci_low, k2.ci_high) == (1.0, 1.0)
    assert "when 2 of 3 models forecast >= 35.6 mm, the reference reached >= 35.6 mm on 300 of 300 days" in k2.statement
    k1 = _g(R, "C3", "k-groups", 1, 35.6, "k=1")          # other days: GFS only; no reference event
    assert (k1.n, k1.reference_events, k1.status) == (620, 0, "insufficient sample") and pd.isna(k1.frequency)
    for grp in ("k=0", "k=3"):
        x = _g(R, "C3", "k-groups", 1, 35.6, grp)
        assert x.n == 0 and x.status == "insufficient sample"
    k1 = _g(R, "C3", "k-groups", 1, 64.5, "k=1")          # ECMWF alone reaches 64.5 on event days
    assert (k1.n, k1.reference_events, k1.frequency) == (300, 300, 1.0)
    assert _g(R, "C3", "model-combination", 1, 64.5, "ECMWF").n == 300
    assert _g(R, "C3", "model-combination", 1, 35.6, "GFS").n == 620
    assert _g(R, "C3", "k-groups", 1, 115.6, "k=0").status == "insufficient sample"
    s = R[(R.experiment == "C3") & (R.analysis == "k-groups") & (R.lead == 1) & (R.threshold_mm == 35.6)]
    assert s.n.sum() == s.cell_n.iloc[0] == 920                         # k-groups partition the sample


def test_missing_excluded_and_three_models_required(ag):
    *_, R, calls = ag
    x = R[(R.experiment == "C3") & (R.analysis == "k-groups") & (R.lead == 2) & (R.threshold_mm == 35.6)]
    assert x.cell_n.iloc[0] == 10 * (92 - 9)                           # GFS outage days drop from the 3-model sample
    assert set(R.lead) == {1, 2, 3, 4, 5, 6}                           # lead 7 not analysed (ICON not defined)


def test_floor_no_hidden_values(ag):
    *_, R, calls = ag
    computed = {(cid, g) for cid, gs in calls for g in gs}
    ins = R[R.status == "insufficient sample"]
    assert not {(r.cell_id, r.group) for r in ins.itertuples()} & computed
    assert ins[["frequency", "ci_low", "ci_high"]].isna().all().all()
    ok = R[R.status == "ok"]
    assert (ok.n >= 100).all() and (ok.reference_events >= 10).all()


def test_imd_era5_separate(ag):
    *_, R, calls = ag
    assert set(R[R.experiment == "C3"].reference) == {"imd_rf025"} and set(R[R.experiment == "C4"].reference) == {"era5"}
    e = _g(R, "C4", "k-groups", 1, 35.6, "k=2")
    assert e.n == 12 * 30 and e.n_points == 12                         # ERA5 includes the islands; never merged with IMD


def test_roles_and_limitation(ag):
    *_, R, calls = ag
    K = R[R.analysis == "k-groups"]
    assert set(K[(K.experiment == "C3") & (K.lead <= 4)].role) == {"primary"}
    assert set(K[(K.experiment == "C4") & (K.lead <= 4)].role) == {"secondary"}
    assert set(R[R.lead >= 5].role) == {"exploratory"} and set(R[R.analysis == "model-combination"].role) == {"exploratory"}
    assert (R[R.lead >= 5].limitations == run_agreement.LEAD56_LIMIT).all()
    assert R[R.lead <= 4].limitations.isna().all()


def test_wording(ag):
    src, tmp, rec, R, calls = ag
    text = " ".join(R.statement.dropna()) + (tmp / "out" / "agreement_report.md").read_text()
    text = text.replace("Not CORE risk verification", "")
    assert not re.findall(r"\b(probabilit\w*|chance|confidence|likelihood|likely|CORE risk|better|best)\b", text, re.I)


def test_deterministic(ag, tmp_path):
    src, tmp, rec, *_ = ag
    assert run_agreement.run(src, tmp_path / "again", tmp / "census")["result_sha256"] == rec["result_sha256"]


def test_label_annotation_builder():
    import label_degenerate as LD
    R = pd.DataFrame({"event_cell_id": ["c1", "c1", "c2", "c3"], "role": ["primary"] * 4,
                      "subject": ["gfs_global", "difference: a minus b", "icon_global", "icon_global"],
                      "metric": ["pod", "pod", "far", "csi"], "status": ["ok", "ok", "ok", "insufficient sample"],
                      "value": [0.0, 0.0, 0.5, None], "ci_low": [0.0, 0.0, 0.4, None], "ci_high": [0.0, 0.0, 0.6, None]})
    a = LD.build(R, "sha", "rec")
    assert a["rows_labelled"] == 1 and a["rows"][0]["event_cell_id"] == "c1" and a["rows"][0]["subject"] == "gfs_global"
    assert a["label"] == RP.DEGENERATE_LABEL
