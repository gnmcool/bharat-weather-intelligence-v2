"""R2 value-level comparison (plan §11): identical passes, within packing bound passes, beyond fails, structure fails."""
from datetime import datetime, timezone
from decimal import Decimal

import numpy as np
import pytest

from reference.tests import default_value, flat_index, write_grib
import era5_common as C
import era5_extract as X
import era5_grib as G
import era5_r2 as R2

UTC = timezone.utc
SMALL = [34.0, 72.25, 33.0, 73.5]
PTS = [{"id": "P1", "lat": Decimal("33.611"), "lon": Decimal("72.818")},
       {"id": "P2", "lat": Decimal("33.125"), "lon": Decimal("73.375")}]
MONTH = "2026-09"


def retrieval(tmp, name, **kw):
    rq = C.build_requests(MONTH, area=SMALL)
    d = tmp / name
    d.mkdir()
    files = {role: G.decode(write_grib(d / f"{role}.grib", rq[role], **kw.get(role, {}))) for role in C.ROLES}
    tables = X.build_tables(PTS, files, MONTH, d / "t")
    return {"files": files, "tables": tables, "hourly_path": d / "t" / f"era5_hourly_{MONTH}.parquet",
            "day_path": d / "t" / f"era5_ist_day_{MONTH}.parquet"}


@pytest.fixture(scope="module")
def first(tmp_path_factory):
    return retrieval(tmp_path_factory.mktemp("r"), "first")


def test_identical_passes(first, tmp_path):
    res = R2.compare(MONTH, first, retrieval(tmp_path, "second"))
    assert res["passed"] and res["values_identical_after_decoding"]
    assert res["max_abs_diff_mm"] == {"hourly": 0.0, "ist_day": 0.0, "monthly": 0.0}
    assert res["table_sha256"]["first"] == res["table_sha256"]["repeat"]


def test_within_packing_bound_passes(first, tmp_path):
    """A re-encoding difference smaller than the packing step (different reference value) passes."""
    q = min(m["packing_step"] for m in first["files"]["month"]["messages"])
    shift = datetime(2026, 9, 12, 5, tzinfo=UTC)

    def perturb(t, v):
        if t == shift:
            v = v + q * 0.3                          # below half a packing step of either message
        return v
    second = retrieval(tmp_path, "second", month={"perturb": perturb})
    res = R2.compare(MONTH, first, second)
    assert res["passed"], res
    assert res["max_abs_diff_mm"]["hourly"] <= q * 1000


def test_beyond_bound_fails(first, tmp_path):
    shift = datetime(2026, 9, 12, 5, tzinfo=UTC)
    idx = flat_index(33.5, 72.75, SMALL)

    def perturb(t, v):
        if t == shift:
            v[idx] += 0.0005                         # 0.5 mm: far beyond the packing precision
        return v
    res = R2.compare(MONTH, first, retrieval(tmp_path, "second", month={"perturb": perturb}))
    assert not res["passed"] and res["exceedances"]["hourly"] and res["exceedances"]["ist_day"]
    assert res["exceedances"]["hourly"][0][0] == "P1"


def test_expver_difference_fails(first, tmp_path):
    res = R2.compare(MONTH, first, retrieval(tmp_path, "second", boundary={"expver": lambda t: "0005"}))
    assert not res["passed"] and any(p.startswith("[expver]") for p in res["problems"])


def test_missing_position_difference_fails(first, tmp_path):
    hole = datetime(2026, 9, 20, 3, tzinfo=UTC)
    second = retrieval(tmp_path, "second", month={"missing": {hole: [flat_index(33.5, 72.75, SMALL)]}})
    res = R2.compare(MONTH, first, second)
    assert not res["passed"] and "E/G reasons or hours_present differ" in " ".join(res["problems"])


def test_many_small_diffs_in_a_day_within_summed_bound(first, tmp_path):
    q = min(m["packing_step"] for m in first["files"]["month"]["messages"])

    def perturb(t, v):
        return v + q * 0.2 if t.day == 12 else v
    res = R2.compare(MONTH, first, retrieval(tmp_path, "second", month={"perturb": perturb}))
    assert res["passed"] and res["max_abs_diff_mm"]["ist_day"] > 0


def test_criterion_is_recorded(first, tmp_path):
    res = R2.compare(MONTH, first, retrieval(tmp_path, "second"))
    assert "q1/2 + q2/2" in res["criterion"] and res["packing_steps_m"]
    assert set(res["grib_sha256"]["first"]) == {"boundary", "month"}
