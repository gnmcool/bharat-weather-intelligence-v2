"""M4.4-A Gate 2: continuous metrics (bias, MAE, RMSE) and the 7-day block bootstrap (VM-1.1 §7, §14, §21).

Pure functions, no I/O. Error e = forecast - reference.
  bias = mean(e), MAE = mean(|e|), RMSE = sqrt(mean(e^2)).
Missing values are refused (never zero, never dropped silently): any NaN/inf raises MetricError. An empty sample has
no metric (None) — there is no other denominator in these three metrics, so "invalid denominator" means n = 0.

Bootstrap (VM-1.1 §21): non-overlapping 7-day calendar blocks anchored on BLOCK_ORIGIN; the cell's non-empty blocks
are drawn with replacement (as many as there are), 1,000 resamples; percentile 95% interval. Each cell's generator
is seeded from SHA-256(master seed, cell id). Paired differences resample both models' errors with the same blocks.
"""
from __future__ import annotations

import hashlib
from datetime import date

import numpy as np

METRICS = ("bias", "mae", "rmse")
BOOTSTRAP_SEED = 20240201
BOOTSTRAP_RESAMPLES = 1000
BLOCK_DAYS = 7
BLOCK_ORIGIN = date(2024, 2, 1)
CI_LEVEL = 0.95
CI_METHOD = "percentile; 7-day non-overlapping calendar blocks of whole valid dates (all points together)"


class MetricError(ValueError):
    """Invalid metric input (missing / non-finite values, empty or inconsistent samples)."""


def _errors(forecast, reference) -> np.ndarray:
    f = np.asarray(forecast, dtype=np.float64)
    o = np.asarray(reference, dtype=np.float64)
    if f.shape != o.shape or f.ndim != 1:
        raise MetricError("forecast and reference must be 1-D arrays of equal length (pairs)")
    if not (np.isfinite(f).all() and np.isfinite(o).all()):
        raise MetricError("missing or non-finite value in an eligible pair (missing is never zero)")
    return f - o


def bias(forecast, reference):
    e = _errors(forecast, reference)
    return None if e.size == 0 else float(e.mean())


def mae(forecast, reference):
    e = _errors(forecast, reference)
    return None if e.size == 0 else float(np.abs(e).mean())


def rmse(forecast, reference):
    e = _errors(forecast, reference)
    return None if e.size == 0 else float(np.sqrt((e * e).mean()))


def point_metrics(e: np.ndarray) -> dict:
    e = np.asarray(e, dtype=np.float64)
    if not np.isfinite(e).all():
        raise MetricError("non-finite error")
    if e.size == 0:
        return {m: None for m in METRICS}
    return {"bias": float(e.mean()), "mae": float(np.abs(e).mean()), "rmse": float(np.sqrt((e * e).mean()))}


def block_ids(dates) -> np.ndarray:
    """7-day calendar block index of each valid date (datetime.date or numpy datetime64)."""
    d = np.asarray(dates, dtype="datetime64[D]")
    days = (d - np.datetime64(BLOCK_ORIGIN, "D")).astype(np.int64)
    if (days < 0).any():
        raise MetricError("valid date before the block origin")
    return days // BLOCK_DAYS


def cell_seed(cell_id: str, master: int = BOOTSTRAP_SEED) -> int:
    return int.from_bytes(hashlib.sha256(f"{master}|{cell_id}".encode()).digest()[:8], "big")


def _block_sums(e: np.ndarray, blocks: np.ndarray):
    """Per non-empty block: n, sum e, sum |e|, sum e^2."""
    uniq, inv = np.unique(blocks, return_inverse=True)
    k = len(uniq)
    n = np.bincount(inv, minlength=k).astype(np.float64)
    s1 = np.bincount(inv, weights=e, minlength=k)
    sa = np.bincount(inv, weights=np.abs(e), minlength=k)
    s2 = np.bincount(inv, weights=e * e, minlength=k)
    return n, s1, sa, s2, inv, k


def _from_sums(n, s1, sa, s2) -> dict:
    return {"bias": s1 / n, "mae": sa / n, "rmse": np.sqrt(s2 / n)}


def _draws(k: int, seed: int, resamples: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.integers(0, k, size=(resamples, k))


def _counts(draws: np.ndarray, k: int) -> np.ndarray:
    """(resamples, k) matrix: how many times each block was drawn in each resample."""
    c = np.zeros((draws.shape[0], k), dtype=np.float64)
    np.add.at(c, (np.repeat(np.arange(draws.shape[0]), k), draws.ravel()), 1.0)
    return c


def _interval(x: np.ndarray) -> tuple[float, float]:
    lo, hi = np.percentile(x, [100 * (1 - CI_LEVEL) / 2, 100 * (1 + CI_LEVEL) / 2])
    return float(lo), float(hi)


def bootstrap(e, dates, cell_id: str, resamples: int = BOOTSTRAP_RESAMPLES) -> dict:
    """Point values and 95% block-bootstrap intervals for bias, MAE and RMSE of one sample of errors."""
    e = np.asarray(e, dtype=np.float64)
    if e.size == 0:
        raise MetricError("empty sample: no metric and no interval")
    if not np.isfinite(e).all():
        raise MetricError("non-finite error")
    blocks = block_ids(dates)
    if blocks.shape != e.shape:
        raise MetricError("one valid date per error is required")
    n, s1, sa, s2, _, k = _block_sums(e, blocks)
    if k < 2:
        raise MetricError("fewer than 2 blocks: a block bootstrap is undefined")
    C = _counts(_draws(k, cell_seed(cell_id), resamples), k)
    R = _from_sums(C @ n, C @ s1, C @ sa, C @ s2)
    pm = point_metrics(e)
    return {"n_blocks": k, "seed": cell_seed(cell_id),
            **{m: {"value": pm[m], "ci": _interval(R[m])} for m in METRICS}}


def paired_bootstrap(e_a, e_b, dates, cell_id: str, resamples: int = BOOTSTRAP_RESAMPLES) -> dict:
    """Both models' metrics on the same shared-data pairs and the difference (a - b), with the same resampled blocks."""
    e_a = np.asarray(e_a, dtype=np.float64)
    e_b = np.asarray(e_b, dtype=np.float64)
    if e_a.shape != e_b.shape:
        raise MetricError("paired comparison needs the same shared-data pairs for both models")
    if e_a.size == 0:
        raise MetricError("empty shared-data sample")
    if not (np.isfinite(e_a).all() and np.isfinite(e_b).all()):
        raise MetricError("non-finite error")
    blocks = block_ids(dates)
    if blocks.shape != e_a.shape:
        raise MetricError("one valid date per pair is required")
    na, a1, aa, a2, inv, k = _block_sums(e_a, blocks)
    _, b1, ba, b2, _, _ = _block_sums(e_b, blocks)
    if k < 2:
        raise MetricError("fewer than 2 blocks: a block bootstrap is undefined")
    seed = cell_seed(cell_id)
    C = _counts(_draws(k, seed, resamples), k)
    RA = _from_sums(C @ na, C @ a1, C @ aa, C @ a2)
    RB = _from_sums(C @ na, C @ b1, C @ ba, C @ b2)
    pa, pb = point_metrics(e_a), point_metrics(e_b)
    return {"n_blocks": k, "seed": seed,
            "a": {m: {"value": pa[m], "ci": _interval(RA[m])} for m in METRICS},
            "b": {m: {"value": pb[m], "ci": _interval(RB[m])} for m in METRICS},
            "diff": {m: {"value": pa[m] - pb[m], "ci": _interval(RA[m] - RB[m])} for m in METRICS}}
