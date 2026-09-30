"""R2 controlled-repeat comparison at value level (D2 plan §11).

GRIB files are not compared byte for byte. The criterion is derived from the files' own encoding:
- identical structure: stamps, grid, node coordinates, expver = 0001 everywhere, missing-value positions, and E/G
  reasons and hours_present per point-day;
- hourly values: |v1 - v2| <= q1/2 + q2/2 for every point and stamp (v in metres, q = packing step of the message);
- IST-day totals and monthly totals per point: the difference must not exceed the sum of the per-hour bounds of the
  hours summed.
It is a reproducibility test, not a meteorological threshold.
"""
from __future__ import annotations

import hashlib
import pathlib

import numpy as np

from era5_common import FINAL_EXPVER, ist_day_stamps, month_days


def _node_series(files: dict, nodes: list[dict]) -> dict:
    """point_id -> {stamp: (value_m, packing_step_m, expver)} over both files."""
    out = {}
    for n in nodes:
        d = {}
        for role in ("boundary", "month"):
            dec = files[role]
            for m, v in zip(dec["messages"], dec["values"][:, n["index"]]):
                d[m["stamp"]] = (float(v), m["packing_step"], m.get("expver"))
        out[n["point_id"]] = d
    return out


def _sha(path: pathlib.Path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def compare(month: str, first: dict, second: dict) -> dict:
    """first/second: {"files": {role: decoded}, "tables": build_tables(...) result, "stage": dir with the tables}."""
    problems = []
    t1, t2 = first["tables"], second["tables"]
    n1 = [(n["point_id"], str(n["node_lat"]), str(n["node_lon"]), n["index"]) for n in t1["nodes"]]
    n2 = [(n["point_id"], str(n["node_lat"]), str(n["node_lon"]), n["index"]) for n in t2["nodes"]]
    if n1 != n2:
        problems.append("[structure] node coordinates or grid indices differ")
    for role in ("boundary", "month"):
        a, b = first["files"][role], second["files"][role]
        if [m["stamp"] for m in a["messages"]] != [m["stamp"] for m in b["messages"]]:
            problems.append(f"[structure] {role}: validity stamps differ")
        if a["values"].shape != b["values"].shape:
            problems.append(f"[structure] {role}: grid sizes differ")
        for dec, lab in ((a, "first"), (b, "repeat")):
            if {m.get("expver") for m in dec["messages"]} != {FINAL_EXPVER}:
                problems.append(f"[expver] {role} ({lab}): not all {FINAL_EXPVER}")
    d1 = t1["days"][["point_id", "ist_date", "reason", "hours_present"]].astype(str).values.tolist()
    d2 = t2["days"][["point_id", "ist_date", "reason", "hours_present"]].astype(str).values.tolist()
    if d1 != d2:
        problems.append("[structure] E/G reasons or hours_present differ")
    if problems:
        return {"passed": False, "problems": problems}

    s1, s2 = _node_series(first["files"], t1["nodes"]), _node_series(second["files"], t2["nodes"])
    max_h = max_d = max_m = 0.0
    over_h, over_d, over_m = [], [], []
    identical = True
    for pid in s1:
        a, b = s1[pid], s2[pid]
        bound_h = {}
        for t in a:
            (v1, q1, _), (v2, q2, _) = a[t], b[t]
            if np.isnan(v1) != np.isnan(v2):
                over_h.append((pid, t.isoformat(), "missing-value position differs"))
                continue
            if np.isnan(v1):
                continue
            bnd = (q1 or 0.0) / 2 + (q2 or 0.0) / 2
            diff = abs(v1 - v2)
            identical &= v1 == v2
            bound_h[t] = bnd
            max_h = max(max_h, diff * 1000.0)
            if diff > bnd:
                over_h.append((pid, t.isoformat(), diff, bnd))
        month_diff = month_bound = 0.0
        for d in month_days(month):
            st = ist_day_stamps(d)
            if any(t not in bound_h for t in st):
                continue                                       # null day (E/G): compared via reasons above
            tot1 = sum(a[t][0] for t in st)
            tot2 = sum(b[t][0] for t in st)
            bnd = sum(bound_h[t] for t in st)
            diff = abs(tot1 - tot2)
            max_d = max(max_d, diff * 1000.0)
            if diff > bnd:
                over_d.append((pid, str(d), diff, bnd))
            month_diff += tot1 - tot2
            month_bound += bnd
        max_m = max(max_m, abs(month_diff) * 1000.0)
        if abs(month_diff) > month_bound:
            over_m.append((pid, abs(month_diff), month_bound))
    passed = not (over_h or over_d or over_m)
    res = {"passed": passed, "problems": [],
           "values_identical_after_decoding": bool(identical),
           "max_abs_diff_mm": {"hourly": max_h, "ist_day": max_d, "monthly": max_m},
           "exceedances": {"hourly": [list(map(str, x)) for x in over_h[:20]],
                           "ist_day": [list(map(str, x)) for x in over_d[:20]],
                           "monthly": [list(map(str, x)) for x in over_m[:20]]},
           "packing_steps_m": sorted({m["packing_step"] for dec in (*first["files"].values(), *second["files"].values())
                                      for m in dec["messages"] if m["packing_step"] is not None}),
           "criterion": "hourly |v1-v2| <= q1/2 + q2/2 (q = GRIB packing step of each message); IST-day and monthly "
                        "totals within the sum of the per-hour bounds; identical structure, expver, missing "
                        "positions and E/G reasons",
           "table_sha256": {"first": {"hourly": _sha(first["hourly_path"]), "ist_day": _sha(first["day_path"])},
                            "repeat": {"hourly": _sha(second["hourly_path"]), "ist_day": _sha(second["day_path"])}},
           "grib_sha256": {"first": {r: first["files"][r]["sha256"] for r in first["files"]},
                           "repeat": {r: second["files"][r]["sha256"] for r in second["files"]}}}
    if not passed:
        res["problems"].append("[values] differences exceed the packing-precision bound")
    return res
