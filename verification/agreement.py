"""M4.4-C: model-agreement analysis (VM §9). ECMWF + GFS + ICON only; weather-model rainfall events; not CORE risk
verification; observed frequencies only.

For each (point, valid date, nominal lead, threshold τ) where all three independent models and the reference are
eligible: k = number of the three models with forecast >= τ (float32, as M4.4-B). Per k-group (k = 0, 1, 2, 3):
n cases, reference events (reference >= τ), observed event frequency = events / n.
The k-groups of one (reference, lead, threshold) partition the same sample: they are mutually exclusive and are
not independent samples.

Floors (VM §11): a k-group shows a frequency only with n >= 100 and >= 10 reference events; otherwise "insufficient
sample" and no value is computed.

Bootstrap (VM-1.1 §21): one draw matrix per (reference, lead, threshold) cell, from the cell id. The per-block
n and events of every k-group are resampled with the same draws; frequency* = events* / n*. A resample with n* = 0 has
no value for that group, is left out and counted, and more than 25 such resamples make the interval "no value".
"""
from __future__ import annotations

import numpy as np

from events import MAX_UNDEFINED_RESAMPLES, is_event
from metrics import BOOTSTRAP_RESAMPLES, MetricError, _counts, _draws, _interval, block_ids, cell_seed

AGREEMENT_MODELS = ("ecmwf_ifs025", "gfs_global", "icon_global")
MIN_N, MIN_EVENTS = 100, 10


def k_and_members(forecasts: dict, threshold: float):
    """forecasts: {model: array} for exactly the three models. Returns (k array, member-code array), where the member
    code lists the models at or above the threshold in AGREEMENT_MODELS order ('-' when k = 0)."""
    if tuple(sorted(forecasts)) != tuple(sorted(AGREEMENT_MODELS)):
        raise MetricError("agreement counts ECMWF, GFS and ICON only (Earth2Studio GFS is never a model here)")
    ev = {m: is_event(forecasts[m], threshold) for m in AGREEMENT_MODELS}
    k = sum(ev[m].astype(int) for m in AGREEMENT_MODELS)
    names = {"ecmwf_ifs025": "ECMWF", "gfs_global": "GFS", "icon_global": "ICON"}
    members = np.array(["+".join(names[m] for m in AGREEMENT_MODELS if ev[m][i]) or "-" for i in range(len(k))])
    return np.asarray(k), members


def group_counts(groups, observed) -> dict:
    """{group: (n, events)} for every group value present."""
    groups, observed = np.asarray(groups), np.asarray(observed, bool)
    return {g: (int((groups == g).sum()), int(observed[groups == g].sum())) for g in sorted(set(groups.tolist()))}


def floor_ok(n: int, events: int) -> bool:
    return n >= MIN_N and events >= MIN_EVENTS


def bootstrap_groups(groups, observed, dates, cell_id: str, compute: set, resamples: int = BOOTSTRAP_RESAMPLES) -> dict:
    """Frequency and 95% interval for the groups in `compute` only (those meeting the floor), all resampled with one
    draw matrix (same blocks). Nothing is computed for any other group."""
    groups, observed = np.asarray(groups), np.asarray(observed, bool)
    if groups.size == 0:
        raise MetricError("empty sample")
    blocks = block_ids(dates)
    uniq, inv = np.unique(blocks, return_inverse=True)
    kb = len(uniq)
    if kb < 2:
        raise MetricError("fewer than 2 blocks: a block bootstrap is undefined")
    seed = cell_seed(cell_id)
    C = _counts(_draws(kb, seed, resamples), kb)
    out = {"n_blocks": kb, "seed": seed, "groups": {}}
    for g in sorted(compute):
        m = groups == g
        nb = np.bincount(inv, weights=m.astype(float), minlength=kb)
        eb = np.bincount(inv, weights=(m & observed).astype(float), minlength=kb)
        n_star, e_star = C @ nb, C @ eb
        with np.errstate(divide="ignore", invalid="ignore"):
            f = np.where(n_star > 0, e_star / n_star, np.nan)
        und = int(np.isnan(f).sum())
        ok = f[~np.isnan(f)]
        ci = None if (und > MAX_UNDEFINED_RESAMPLES or ok.size == 0) else _interval(ok)
        n, e = int(m.sum()), int((m & observed).sum())
        out["groups"][g] = {"n": n, "events": e, "value": e / n if n else None, "ci": ci, "undefined_resamples": und}
    return out
