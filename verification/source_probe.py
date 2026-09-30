"""M4.4-A Gate 2 hold: controlled, read-only source probe for the two lead-step findings (owner-approved scope).

Questions:
  A. Does the GFS rainfall series change temporal resolution / forecast-hour structure around hour 120 (nominal
     lead >= 5)?
  B. Does the ECMWF temperature series change temporal resolution / forecast-hour structure around hour 144
     (nominal lead >= 6)?

Scope (minimum): 3 archive points x 3 representative dates, one variable per model (GFS precipitation, ECMWF
temperature_2m), previous_day1..7, requested through the SAME code path the archive used
(history/sources.previous_runs). Each request is made twice to test determinism. About 12 requests and 36 counted
Open-Meteo calls in total. Nothing is written to the archive, census or results. The raw responses are
saved with their SHA-256 so that every observation can be checked.

What the probe measures (pure functions, tested offline):
  * precipitation: wet-hour pattern per aligned 3-h group (one wet hour / three equal values / varying hourly),
    daily totals per lead;
  * temperature: node spacing — the largest k in {1, 3, 6} for which every hour lies on the straight line between
    k-hourly nodes (tolerance 0.051 degC, as the source rounds to 0.1), located hour by hour;
  * transformation: the archive's own aggregate_daily() applied to the probed hourly values, compared with the
    archived daily value for the same model/point/variable/lead/date (preserves vs introduces).
The probe does not infer run times (the archive is run_time_known = false). The forecast hours that correspond to a
valid hour are stated only as far as the source's documented definition of previous_dayN allows.

  python verification/source_probe.py --out DIR --cache DIR --confirm-network
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
import sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


hc = _load("history_common_probe", REPO / "history" / "common.py")   # history/common.py (the archive's own code)

PROBE_POINTS = ["IN-07-delhi", "IN-33-614", "IN-32-594"]          # VIDP point, VOTR point, a wet-coast point
PROBE_DATES = [date(2024, 7, 15), date(2025, 1, 15), date(2025, 7, 15)]
TARGETS = {"A": ("gfs_global", "gfs_global", "precipitation", ("precip", "precip_0830")),
           "B": ("ecmwf_ifs025", "ecmwf_ifs025", "temperature_2m", ("tmax", "tmin"))}
LEADS = list(range(1, 8))
TOL_T = 0.051


# ------------------------------------------------------------------ pure analysis
def precip_groups(vals: list, offset: int = 0) -> Counter:
    """Classify aligned 3-h groups (hours offset, offset+1, offset+2 mod 3) of an hourly precipitation series."""
    c = Counter()
    v = [None if x is None else float(x) for x in vals]
    for i in range(offset, len(v) - 2, 3):
        g = v[i:i + 3]
        if any(x is None for x in g):
            c["incomplete"] += 1
        elif all(x == 0 for x in g):
            c["dry"] += 1
        elif sum(x > 0 for x in g) == 1:
            c["one_wet_hour"] += 1
        elif g[0] == g[1] == g[2]:
            c["three_equal"] += 1
        else:
            c["varying"] += 1
    return c


def linear_ok(vals: list, k: int, offset: int, tol: float = TOL_T) -> tuple[np.ndarray, np.ndarray]:
    """Per hour: (ok, determined). An hour is determined when it is a non-node hour with a non-missing node on both
    sides (nodes: i % k == offset); it is ok when it lies on the straight line between them. Node hours and
    undetermined hours are ok (they cannot contradict the spacing)."""
    v = np.array([np.nan if x is None else float(x) for x in vals])
    ok = np.ones(len(v), bool)
    det = np.zeros(len(v), bool)
    for i in range(len(v)):
        if np.isnan(v[i]) or i % k == offset:
            continue
        lo = i - ((i - offset) % k)
        hi = lo + k
        if lo < 0 or hi >= len(v) or np.isnan(v[lo]) or np.isnan(v[hi]):
            continue
        det[i] = True
        ok[i] = abs(v[lo] + (v[hi] - v[lo]) * (i - lo) / k - v[i]) <= tol
    return ok, det


def node_spacing(vals: list, lo: int, hi: int) -> dict:
    """Largest k in (6, 3), with its offset, such that every determined hour in [lo, hi) lies on the line between
    k-hourly nodes (at least k - 1 hours determined); otherwise k = 1 (genuinely hourly variation)."""
    for k in (6, 3):
        for off in range(k):
            ok, det = linear_ok(vals, k, off)
            if det[lo:hi].sum() >= k - 1 and ok[lo:hi].all():
                return {"k": k, "offset": off}
    return {"k": 1, "offset": 0}


def hourly_profile(vals: list) -> dict:
    """For each hour: is it an interior point of a straight segment (value = mean of its neighbours)?"""
    v = [None if x is None else float(x) for x in vals]
    out = []
    for i in range(len(v)):
        if i == 0 or i == len(v) - 1 or None in (v[i - 1], v[i], v[i + 1]):
            out.append(None)
        else:
            out.append(abs((v[i - 1] + v[i + 1]) / 2 - v[i]) <= TOL_T)
    return {"interior_linear": out}


def reproduce_daily(times: list[datetime], vals: list, var: str, days: list[date]) -> dict:
    """The archive's own IST-day / IMD-window aggregation applied to probed hourly values."""
    out = {}
    for dv, unit, how, window in hc.HOURLY[var]:
        for d, v, n in hc.aggregate_daily(times, vals, how, window, days):
            out[(dv, d)] = (v, n)
    return out


def compare_archive(repro: dict, archived: dict) -> dict:
    """archived: {(variable, date): value}. Returns max abs difference and per-key detail."""
    rows, diffs = [], []
    for k, (v, n) in sorted(repro.items(), key=lambda x: (x[0][0], x[0][1])):
        a = archived.get(k)
        d = None if (v is None or a is None) else abs(float(v) - float(a))
        rows.append({"variable": k[0], "date": str(k[1]), "probe": v, "archived": a, "hours": n, "abs_diff": d})
        if d is not None:
            diffs.append(d)
    return {"max_abs_diff": max(diffs) if diffs else None, "n_compared": len(diffs), "rows": rows}


# ------------------------------------------------------------------ network (only with --confirm-network)
def fetch(points: list[dict], om_model: str, var: str, d: date):
    saved = sys.modules.get("common")
    sys.modules["common"] = hc                       # history/sources.py imports its sibling as `common`
    try:
        src = _load("history_sources_probe", REPO / "history" / "sources.py")
    finally:
        if saved is None:
            sys.modules.pop("common", None)
        else:
            sys.modules["common"] = saved
    s, e = d - timedelta(days=1), d + timedelta(days=1)
    resp, url = src.previous_runs(points, om_model, [var], LEADS, s, e)
    return resp, url


def run(out: pathlib.Path, cache: pathlib.Path, fetcher=fetch, archived_loader=None) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    allp = {p["id"]: p for p in hc.load_points()}
    pts = [allp[i] for i in PROBE_POINTS]
    result = {"started_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "points": PROBE_POINTS,
              "dates": [str(d) for d in PROBE_DATES], "requests": [], "questions": {}}
    for q, (model, om_model, var, dvs) in TARGETS.items():
        Q = {"model": model, "variable": var, "by_date": {}}
        for d in PROBE_DATES:
            r1, url = fetcher(pts, om_model, var, d)
            r2, _ = fetcher(pts, om_model, var, d)
            b1 = json.dumps(r1, sort_keys=True).encode()
            b2 = json.dumps(r2, sort_keys=True).encode()
            name = f"{q}_{model}_{var}_{d}.json"
            (out / name).write_bytes(b1)
            result["requests"].append({"question": q, "url": url, "file": name, "sha256": hashlib.sha256(b1).hexdigest(),
                                       "repeat_identical": b1 == b2})
            per_point = {}
            for p, r in zip(pts, r1):
                h = r["hourly"]
                times = hc.parse_hourly_times(h["time"])
                lead = {}
                for n in LEADS:
                    vals = h.get(f"{var}_previous_day{n}") or [None] * len(times)
                    day_idx = [i for i, t in enumerate(times) if t.date() == d]
                    entry = {"hours_present": sum(v is not None for v in vals)}
                    if var == "precipitation":
                        entry["groups"] = {f"offset{o}": dict(precip_groups(vals, o)) for o in range(3)}
                        entry["groups_by_6h_segment"] = [
                            {"utc_start": times[s].isoformat(), **{f"offset{o}": dict(precip_groups(vals[s:s + 6], o))
                                                                   for o in range(3)}}
                            for s in range(0, len(vals), 6)]
                        entry["hourly_values"] = vals
                        entry["utc_day_total"] = (round(sum(vals[i] for i in day_idx), 3)
                                                  if all(vals[i] is not None for i in day_idx) else None)
                    else:
                        entry["spacing_whole_request"] = node_spacing(vals, 0, len(vals))
                        entry["spacing_by_6h_segment"] = [
                            {"utc_start": times[s].isoformat(), **node_spacing(vals, s, min(s + 6, len(vals)))}
                            for s in range(0, len(vals) - 1, 6)]
                        entry["hourly_values"] = vals
                        entry["interior_linear_hours_utc"] = [
                            times[i].strftime("%m-%dT%H") for i, f in enumerate(hourly_profile(vals)["interior_linear"])
                            if f]
                    repro = reproduce_daily(times, vals, var, [d])
                    if archived_loader is not None:
                        entry["archive_check"] = compare_archive(repro, archived_loader(model, p["id"], n, d, dvs))
                    entry["probe_daily"] = {f"{k[0]}": v for k, (v, _) in repro.items()}
                    lead[str(n)] = entry
                per_point[p["id"]] = lead
            Q["by_date"][str(d)] = per_point
        result["questions"][q] = Q
    result["deterministic"] = all(r["repeat_identical"] for r in result["requests"])
    result["finished_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (out / "probe_result.json").write_text(json.dumps(result, indent=1, default=str) + "\n")
    return result


def archived_from_cache(cache: pathlib.Path):
    """Archived daily values from the verified, cached immutable releases (read-only)."""
    frames = {}

    def get(model, pid, n, d, dvs):
        m = f"{d:%Y-%m}"
        if m not in frames:
            frames[m] = pd.read_parquet(cache / f"history-{m}" / f"forecasts_history-{m}.parquet")
        F = frames[m]
        s = F[(F.model == model) & (F.point_id == pid) & (F.nominal_lead_day == n) & (F.valid_date_ist == d)
              & F.variable.isin(dvs)]
        return {(r.variable, d): (None if r.value is None or pd.isna(r.value) else float(r.value)) for r in s.itertuples()}
    return get


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--cache", required=True, help="verified release cache (read-only)")
    ap.add_argument("--confirm-network", action="store_true", help="required: the probe calls the source")
    a = ap.parse_args()
    if not a.confirm_network:
        print("refusing: the probe contacts the source; pass --confirm-network once approved")
        return 2
    res = run(pathlib.Path(a.out), pathlib.Path(a.cache), archived_loader=archived_from_cache(pathlib.Path(a.cache)))
    print(json.dumps({"requests": len(res["requests"]), "deterministic": res["deterministic"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
