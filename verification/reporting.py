"""Reporting labels (owner decision at the M4.4-B review, 30 Sep 2026). No statistical methodology is changed.

A degenerate bootstrap interval: the value lies on a boundary of its range and every defined bootstrap replicate
reproduces it, so the 95% percentile interval collapses to that value ([0, 0] or [1, 1]). This happens when a
count is zero or complete (for example 0 hits, or events on every case). The value is kept unchanged. The label
says this does not imply certainty.
"""
from __future__ import annotations

import math

DEGENERATE_LABEL = ("Degenerate bootstrap interval: all bootstrap replicates produced the same boundary value; this "
                    "does not imply statistical certainty.")
# boundary values by metric: proportions in [0, 1]; frequency bias >= 0 (lower boundary only)
BOUNDARIES = {"pod": (0.0, 1.0), "far": (0.0, 1.0), "csi": (0.0, 1.0), "freq_bias": (0.0,), "frequency": (0.0, 1.0)}


def degenerate(metric: str, value, lo, hi) -> bool:
    """True when the interval collapses to a boundary value. For a proportion at 0 or 1, the underlying count is 0
    or complete in the full sample, so it is 0 or complete in every resample (resamples are unions of the sample's
    blocks). Every defined replicate therefore equals the boundary value."""
    if metric not in BOUNDARIES or any(x is None or (isinstance(x, float) and math.isnan(x)) for x in (value, lo, hi)):
        return False
    return value in BOUNDARIES[metric] and lo == hi == value


def label(metric: str, value, lo, hi) -> str | None:
    return DEGENERATE_LABEL if degenerate(metric, value, lo, hi) else None
