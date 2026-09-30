"""M4.4-B: rain event detection (weather-model event verification only; NOT CORE risk verification).

Thresholds: only CORE's existing M-RAIN thresholds (35.6 / 64.5 / 115.6 mm per 24 h; VM §8). Event = value >= threshold,
evaluated independently for each threshold, for forecast and reference separately.

  hits a = forecast event & reference event      false alarms b = forecast event & reference no event
  misses c = no forecast event & reference event correct negatives d = neither
  POD = a/(a+c)  FAR = b/(a+b)  CSI = a/(a+b+c)  frequency bias = (a+b)/(a+c)  base rate = (a+c)/n
A zero denominator gives None ("no value"), never zero.

Precision: the archive stores values as float32; the threshold is applied in float32 (np.float32(value) >=
np.float32(threshold)), so a stored 35.6 is an event at 35.6.

Bootstrap (VM-1.1 §21, same blocks / seed derivation / draws as M4.4-A): per 7-day block the counts a, b, c, d are
summed; each resample recomputes the ratios from the resampled counts. A resample whose denominator is zero has no
value for that ratio; it is left out of the percentile interval and counted. If more than 25 of 1,000 resamples
(2.5 %) have no value, the interval itself is "no value".
"""
from __future__ import annotations

import numpy as np

from metrics import BOOTSTRAP_RESAMPLES, MetricError, _counts, _draws, _interval, block_ids, cell_seed

THRESHOLDS = (35.6, 64.5, 115.6)                  # CORE M-RAIN (Watch, Alert, Severe thresholds) — no others
THRESHOLD_SOURCE = {35.6: "CORE M-RAIN Watch threshold", 64.5: "CORE M-RAIN Alert threshold",
                    115.6: "CORE M-RAIN Severe threshold"}
RATIOS = ("pod", "far", "csi", "freq_bias")
EVENT_FLOOR = 20                                  # VM §11: POD >= 20 reference events; FAR >= 20 forecast events
MAX_UNDEFINED_RESAMPLES = 25                      # 2.5 % of 1,000


def is_event(values, threshold: float) -> np.ndarray:
    v = np.asarray(values, dtype=np.float64)
    if not np.isfinite(v).all():
        raise MetricError("missing or non-finite value in an eligible pair (missing is never zero)")
    if threshold not in THRESHOLDS:
        raise MetricError(f"threshold {threshold} is not a CORE M-RAIN threshold")
    return v.astype(np.float32) >= np.float32(threshold)


def contingency(forecast, reference, threshold: float) -> dict:
    f, o = is_event(forecast, threshold), is_event(reference, threshold)
    if f.shape != o.shape:
        raise MetricError("forecast and reference must be paired")
    a = int((f & o).sum())
    b = int((f & ~o).sum())
    c = int((~f & o).sum())
    d = int((~f & ~o).sum())
    n = a + b + c + d
    return {"hits": a, "false_alarms": b, "misses": c, "correct_negatives": d, "n": n,
            "observed_events": a + c, "forecast_events": a + b, "base_rate": (a + c) / n if n else None}


def _div(x, y):
    return None if y == 0 else x / y


def ratios(a: int, b: int, c: int) -> dict:
    return {"pod": _div(a, a + c), "far": _div(b, a + b), "csi": _div(a, a + b + c), "freq_bias": _div(a + b, a + c)}


def floor_ok(observed_events: int, forecast_events: int) -> dict:
    """VM §11 event floors, per ratio."""
    pod = observed_events >= EVENT_FLOOR
    far = forecast_events >= EVENT_FLOOR
    return {"pod": pod, "far": far, "csi": pod and far, "freq_bias": pod and far}


def _vec_ratios(A, B, Cm) -> dict:
    with np.errstate(divide="ignore", invalid="ignore"):
        out = {"pod": A / (A + Cm), "far": B / (A + B), "csi": A / (A + B + Cm), "freq_bias": (A + B) / (A + Cm)}
    return {k: np.where(np.isfinite(v), v, np.nan) for k, v in out.items()}


def _ci(x: np.ndarray):
    ok = x[~np.isnan(x)]
    und = int(np.isnan(x).sum())
    if und > MAX_UNDEFINED_RESAMPLES or ok.size == 0:
        return None, und
    return _interval(ok), und


def _block_counts(f_ev, o_ev, blocks):
    uniq, inv = np.unique(blocks, return_inverse=True)
    k = len(uniq)
    cnt = lambda m: np.bincount(inv, weights=m.astype(np.float64), minlength=k)
    return cnt(f_ev & o_ev), cnt(f_ev & ~o_ev), cnt(~f_ev & o_ev), k


def bootstrap_events(forecast, reference, dates, threshold: float, cell_id: str,
                     resamples: int = BOOTSTRAP_RESAMPLES) -> dict:
    f_ev, o_ev = is_event(forecast, threshold), is_event(reference, threshold)
    if f_ev.size == 0:
        raise MetricError("empty sample")
    blocks = block_ids(dates)
    a, b, c, k = _block_counts(f_ev, o_ev, blocks)
    if k < 2:
        raise MetricError("fewer than 2 blocks: a block bootstrap is undefined")
    C = _counts(_draws(k, cell_seed(cell_id), resamples), k)
    R = _vec_ratios(C @ a, C @ b, C @ c)
    point = ratios(int(a.sum()), int(b.sum()), int(c.sum()))
    out = {"n_blocks": k, "seed": cell_seed(cell_id)}
    for m in RATIOS:
        ci, und = _ci(R[m])
        out[m] = {"value": point[m], "ci": ci, "undefined_resamples": und}
    return out


def paired_bootstrap_events(f_a, f_b, reference, dates, threshold: float, cell_id: str,
                            resamples: int = BOOTSTRAP_RESAMPLES) -> dict:
    """Both models on the same shared-data pairs (same reference, same resampled blocks) and the difference a - b."""
    fa, fb, o = is_event(f_a, threshold), is_event(f_b, threshold), is_event(reference, threshold)
    if not (fa.shape == fb.shape == o.shape):
        raise MetricError("paired comparison needs the same shared-data pairs for both models")
    blocks = block_ids(dates)
    aa, ab, ac, k = _block_counts(fa, o, blocks)
    ba, bb, bc, _ = _block_counts(fb, o, blocks)
    if k < 2:
        raise MetricError("fewer than 2 blocks: a block bootstrap is undefined")
    seed = cell_seed(cell_id)
    C = _counts(_draws(k, seed, resamples), k)
    RA, RB = _vec_ratios(C @ aa, C @ ab, C @ ac), _vec_ratios(C @ ba, C @ bb, C @ bc)
    pa = ratios(int(aa.sum()), int(ab.sum()), int(ac.sum()))
    pb = ratios(int(ba.sum()), int(bb.sum()), int(bc.sum()))
    out = {"n_blocks": k, "seed": seed, "a": {}, "b": {}, "diff": {}}
    for m in RATIOS:
        for key, R, p in (("a", RA, pa), ("b", RB, pb)):
            ci, und = _ci(R[m])
            out[key][m] = {"value": p[m], "ci": ci, "undefined_resamples": und}
        d = RA[m] - RB[m]
        ci, und = _ci(d)
        out["diff"][m] = {"value": None if pa[m] is None or pb[m] is None else pa[m] - pb[m], "ci": ci,
                          "undefined_resamples": und}
    return out
