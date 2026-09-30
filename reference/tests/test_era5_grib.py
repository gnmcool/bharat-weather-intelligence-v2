"""GRIB decoding, structural validation and the expver acceptance test (plan §3, §5.6, §6)."""
from datetime import datetime, timezone

import numpy as np
import pytest

from reference.tests import write_grib
import era5_common as C
import era5_grib as G

UTC = timezone.utc
SMALL = [34.0, 72.25, 33.0, 73.5]           # 5 x 6 grid: fast unit tests on the same code paths


@pytest.fixture(scope="module")
def rq():
    r = C.build_requests("2026-10", area=SMALL)
    return r


def _dec(tmp_path, request, name="f.grib", **kw):
    return G.decode(write_grib(tmp_path / name, request, **kw))


def test_decode_uses_validity_time_and_records_encoding(tmp_path, rq):
    d = _dec(tmp_path, rq["month"])
    assert len(d["messages"]) == 744 and d["values"].shape == (744, 30)
    stamps = [m["stamp"] for m in d["messages"]]
    assert stamps == C.expected_stamps(rq["month"])
    first = d["messages"][0]
    assert first["dataType"] == "fc" and int(first["dataTime"]) == 1800 and first["stepRange"] == "5-6"
    assert int(first["dataDate"]) == 20260930 and first["stamp"] == datetime(2026, 10, 1, 0, tzinfo=UTC)
    v = G.validate(d, rq["month"], "month")
    assert v["ok"] and v["expver_ok"] and v["problems"] == []
    assert v["summary"]["base_times"] == ["1800", "600"] and v["summary"]["missing_values"] == 0
    assert all(q and q > 0 for q in v["summary"]["packing_steps"])
    assert d["sha256"] and d["bytes"] > 0


def test_boundary_file_validates(tmp_path, rq):
    d = _dec(tmp_path, rq["boundary"])
    v = G.validate(d, rq["boundary"], "boundary")
    assert v["ok"] and [m["stamp"].hour for m in d["messages"]] == [19, 20, 21, 22, 23]
    assert {m["stepRange"] for m in d["messages"]} == {"0-1", "1-2", "2-3", "3-4", "4-5"}


def test_expver_0005_fails(tmp_path, rq):
    bad = datetime(2026, 10, 31, 23, tzinfo=UTC)
    d = _dec(tmp_path, rq["month"], expver=lambda t: "0005" if t == bad else "0001")
    v = G.validate(d, rq["month"], "month")
    assert not v["ok"] and not v["expver_ok"]
    assert any(p.startswith("[expver]") and "'0005': 1" in p for p in v["problems"])


def test_all_era5t_fails(tmp_path, rq):
    d = _dec(tmp_path, rq["boundary"], expver=lambda t: "0005")
    v = G.validate(d, rq["boundary"], "boundary")
    assert not v["expver_ok"] and v["summary"]["expver"] == {"0005": 5}


def test_missing_expver_fails(tmp_path, rq):
    d = _dec(tmp_path, rq["boundary"], no_local=True)
    v = G.validate(d, rq["boundary"], "boundary")
    assert not v["expver_ok"] and any("None" in p for p in v["problems"] if p.startswith("[expver]"))


def test_unused_stamp_expver_also_checked(tmp_path, rq):
    """The month file's 19-23Z hours of its last day are unused by month M but still must be final."""
    unused = datetime(2026, 10, 31, 21, tzinfo=UTC)
    d = _dec(tmp_path, rq["month"], expver=lambda t: "0005" if t == unused else "0001")
    assert not G.validate(d, rq["month"], "month")["expver_ok"]


def test_missing_and_duplicate_stamps_fail(tmp_path, rq):
    t = datetime(2026, 10, 15, 3, tzinfo=UTC)
    v = G.validate(_dec(tmp_path, rq["month"], "a.grib", drop=[t]), rq["month"], "month")
    assert any(p.startswith("[stamps]") and "missing" in p for p in v["problems"])
    v = G.validate(_dec(tmp_path, rq["month"], "b.grib", duplicate=[t]), rq["month"], "month")
    assert any(p.startswith("[stamps]") and "duplicated" in p for p in v["problems"])


def test_wrong_grid_and_variable_fail(tmp_path, rq):
    v = G.validate(_dec(tmp_path, rq["boundary"], "g.grib", area=[34.0, 72.25, 33.0, 73.25]), rq["boundary"], "b")
    assert any(p.startswith("[grid]") for p in v["problems"])
    v = G.validate(_dec(tmp_path, rq["boundary"], "t.grib", short_name="2t"), rq["boundary"], "b")
    assert any(p.startswith("[variable]") for p in v["problems"])


def test_missing_values_are_nan_not_zero(tmp_path, rq):
    t = datetime(2026, 9, 30, 20, tzinfo=UTC)
    d = _dec(tmp_path, rq["boundary"], missing={t: [7]})
    k = [m["stamp"] for m in d["messages"]].index(t)
    assert np.isnan(d["values"][k, 7]) and not np.isnan(d["values"][k, 6])
    assert G.validate(d, rq["boundary"], "boundary")["summary"]["missing_values"] == 1


def test_truncated_or_empty_file_is_a_decode_error(tmp_path, rq):
    p = write_grib(tmp_path / "x.grib", rq["boundary"])
    data = p.read_bytes()
    p.write_bytes(data[: len(data) // 2 + 17])
    with pytest.raises(G.GribDecodeError):
        G.decode(p)
    p.write_bytes(b"")
    with pytest.raises(G.GribDecodeError):
        G.decode(p)
    p.write_bytes(b"<html>error page</html>")
    with pytest.raises(G.GribDecodeError):
        G.decode(p)


def test_full_area_grid_signature():
    assert G.expected_grid() == ("regular_ll", 91, 104, 0.25, 0.25, 34.0, 72.25, 8.25, 94.75)
