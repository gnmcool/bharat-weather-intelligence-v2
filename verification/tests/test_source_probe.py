"""Offline tests for the Gate 2 hold source probe (synthetic source with planted temporal structure; no network)."""
from __future__ import annotations

import json
import math
import pathlib
import sys
from datetime import date, datetime, timedelta

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

import source_probe as SP  # noqa: E402


def _series(var, n, hours):
    out = []
    for h in range(hours):
        if var == "precipitation":
            if n <= 4:
                out.append(round(0.1 * (1 + (h * 7) % 5), 1))          # varies hour by hour
            else:
                out.append(0.9 if h % 3 == 2 else 0.0)                 # one wet hour per 3-h group
        else:
            if n <= 5:
                out.append(round(30 + 5 * math.sin(2 * math.pi * h / 24), 1))   # hourly variation
            else:
                node = [30.0, 34.0, 31.0, 27.0]                          # 6-hourly nodes, linear between
                i, r = divmod(h, 6)
                a, b = node[i % 4], node[(i + 1) % 4]
                out.append(round(a + (b - a) * r / 6, 3))
    return out


def fake_fetcher(calls, vary_second=False):
    def f(points, om_model, var, d):
        calls.append((om_model, var, d))
        start = datetime(d.year, d.month, d.day) - timedelta(days=1)
        hours = 72
        times = [(start + timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M") for h in range(hours)]
        resp = []
        for _ in points:
            h = {"time": times}
            for n in SP.LEADS:
                s = _series(var, n, hours)
                if vary_second and len(calls) % 2 == 0:
                    s = [x + 0.1 for x in s]
                h[f"{var}_previous_day{n}"] = s
            resp.append({"hourly": h})
        return resp, f"https://example.invalid/{om_model}"
    return f


def test_precip_group_classification():
    assert SP.precip_groups([0, 0, 0.9, 0, 0, 0.3]) == {"one_wet_hour": 2}
    assert SP.precip_groups([0.3, 0.3, 0.3, 0.1, 0.2, 0.4]) == {"three_equal": 1, "varying": 1}
    assert SP.precip_groups([0, 0, 0, None, 0, 0]) == {"dry": 1, "incomplete": 1}


def test_node_spacing_detection():
    hourly = [round(30 + 5 * math.sin(2 * math.pi * h / 24), 1) for h in range(48)]
    six = _series("temperature_2m", 6, 48)
    assert SP.node_spacing(hourly, 0, 48)["k"] == 1
    assert SP.node_spacing(six, 0, 48) == {"k": 6, "offset": 0}
    three = [v if h % 3 == 0 else None for h, v in enumerate(hourly)]
    for h in range(48):                                        # fill 3-hourly nodes linearly
        if three[h] is None:
            lo, hi = h - h % 3, h - h % 3 + 3
            if hi < 48:
                three[h] = three[lo] + (hourly[hi] - three[lo]) * (h - lo) / 3
    assert SP.node_spacing(three[:46], 0, 46)["k"] == 3


def test_probe_run_offline(tmp_path):
    calls = []
    archived = {}

    def loader(model, pid, n, d, dvs):
        return archived.get((model, pid, n, d), {})
    res = SP.run(tmp_path / "o", tmp_path / "c", fetcher=fake_fetcher(calls), archived_loader=loader)
    assert len(calls) == 2 * len(SP.PROBE_DATES) * 2                  # 2 targets x 3 dates x 2 (determinism)
    assert res["deterministic"] is True and len(res["requests"]) == 6
    A = res["questions"]["A"]["by_date"]["2025-07-15"]["IN-07-delhi"]
    assert A["4"]["groups"]["offset0"].get("one_wet_hour", 0) == 0
    assert A["5"]["groups"]["offset0"]["one_wet_hour"] == 24          # planted: one wet hour per group
    B = res["questions"]["B"]["by_date"]["2025-07-15"]["IN-07-delhi"]
    assert B["5"]["spacing_whole_request"]["k"] == 1 and B["6"]["spacing_whole_request"]["k"] == 6
    assert json.loads((tmp_path / "o" / "probe_result.json").read_text())["points"] == SP.PROBE_POINTS
    assert sorted(p.name for p in (tmp_path / "o").iterdir() if p.name != "probe_result.json") == \
        sorted(r["file"] for r in res["requests"])                    # writes only into --out


def test_archive_transformation_check(tmp_path):
    """The archive's own aggregation of the probed hours equals the archived value -> 'preserves'."""
    calls = []
    f = fake_fetcher(calls)
    pts = [{"id": "X"}]
    resp, _ = f(pts, "gfs_global", "precipitation", date(2025, 7, 15))
    times = SP.hc.parse_hourly_times(resp[0]["hourly"]["time"])
    vals = resp[0]["hourly"]["precipitation_previous_day5"]
    repro = SP.reproduce_daily(times, vals, "precipitation", [date(2025, 7, 15)])
    same = {k: v for k, (v, _) in repro.items()}
    c = SP.compare_archive(repro, same)
    assert c["max_abs_diff"] == 0 and c["n_compared"] == 2
    off = {k: v + 1.0 for k, v in same.items()}
    assert SP.compare_archive(repro, off)["max_abs_diff"] == pytest.approx(1.0)


def test_nondeterministic_source_is_reported(tmp_path):
    res = SP.run(tmp_path / "o", tmp_path / "c", fetcher=fake_fetcher([], vary_second=True))
    assert res["deterministic"] is False


def test_network_requires_explicit_confirmation(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "argv", ["source_probe.py", "--out", str(tmp_path / "o"), "--cache", str(tmp_path)])
    assert SP.main() == 2 and not (tmp_path / "o").exists()
