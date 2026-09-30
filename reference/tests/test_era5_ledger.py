"""Append-only job ledger and the retrieval limit (plan §7)."""
import json

import pytest

import reference.tests  # noqa: F401
import era5_common as C
from era5_ledger import Ledger, plan_next


def L(tmp_path, month="2026-10", run="run1", persisted=None):
    return Ledger(tmp_path, month, run, persist=(persisted.append if persisted is not None else None))


def test_append_only_and_persisted(tmp_path):
    msgs = []
    lg = L(tmp_path, persisted=msgs)
    lg.append("intent", 1, "boundary", request_sha256="a", items=5)
    first = lg.path.read_bytes()
    lg.append("submitted", 1, "boundary", request_id="rid-1")
    assert lg.path.read_bytes().startswith(first) and len(msgs) == 2
    assert lg.path == tmp_path / "reference" / "era5" / "jobs" / "2026-10.jsonl"
    evs = [json.loads(x) for x in lg.path.read_text().splitlines()]
    assert [e["event"] for e in evs] == ["intent", "submitted"] and all(e["run_id"] == "run1" for e in evs)
    with pytest.raises(ValueError):
        lg.append("rewrite", 1, "boundary")


def test_job_states(tmp_path):
    lg = L(tmp_path)
    assert lg.job(1, "month")["state"] == "none"
    lg.append("intent", 1, "month", request_sha256="s", items=744)
    assert lg.job(1, "month")["state"] == "uncertain"                     # intent without request id
    lg.append("submitted", 1, "month", request_id="r1")
    assert lg.job(1, "month")["state"] == "open" and lg.job(1, "month")["request_id"] == "r1"
    lg.append("closed", 1, "month", outcome="pending")
    assert lg.job(1, "month")["state"] == "open"                           # pending keeps the job resumable
    lg.append("downloaded", 1, "month", request_id="r1", bytes=10, file_sha256="f")
    assert lg.job(1, "month")["state"] == "downloaded"
    lg.append("closed", 1, "month", outcome="published")
    assert lg.job(1, "month")["state"] == "closed:published"


def _both(lg, r, *events):
    for role in C.ROLES:
        for ev, kw in events:
            lg.append(ev, r, role, **kw)


def test_first_retrieval_and_resume(tmp_path):
    lg = L(tmp_path)
    assert plan_next(lg, "2026-10", False)["action"] == "start"
    _both(lg, 1, ("intent", {}), ("submitted", {"request_id": "x"}))
    d = plan_next(lg, "2026-10", False)
    assert (d["action"], d["retrieval"]) == ("resume", 1)


def test_uncertain_submission_is_refused_not_resubmitted(tmp_path):
    lg = L(tmp_path)
    lg.append("intent", 1, "boundary")
    assert plan_next(lg, "2026-10", False)["action"] == "refuse_uncertain"


def test_second_retrieval_only_after_failure_and_never_in_the_same_run(tmp_path):
    lg = L(tmp_path, run="run1")
    _both(lg, 1, ("intent", {}), ("submitted", {"request_id": "x"}), ("closed", {"outcome": "refused"}))
    assert plan_next(lg, "2026-10", False)["action"] == "stop"            # same run: no automatic retrieval 2
    lg2 = L(tmp_path, run="run2")
    d = plan_next(lg2, "2026-10", False)
    assert (d["action"], d["retrieval"]) == ("start", 2)                   # new committed request
    _both(lg2, 2, ("intent", {}), ("submitted", {"request_id": "y"}), ("closed", {"outcome": "refused"}))
    lg3 = L(tmp_path, run="run3")
    d = plan_next(lg3, "2026-10", False)
    assert d["action"] == "refuse" and "no automatic third retrieval" in d["reason"]


def test_published_month_is_done(tmp_path):
    lg = L(tmp_path)
    _both(lg, 1, ("intent", {}), ("submitted", {"request_id": "x"}), ("downloaded", {"file_sha256": "f", "bytes": 1}),
          ("closed", {"outcome": "published"}))
    assert plan_next(lg, "2026-10", False)["action"] == "done"


def test_r2_only_for_the_validation_month(tmp_path):
    assert plan_next(L(tmp_path, "2026-10"), "2026-10", True)["action"] == "refuse"
    assert plan_next(L(tmp_path, "2026-09"), "2026-09", False)["action"] == "refuse"
    assert plan_next(L(tmp_path, "2026-09"), "2026-09", True)["action"] == "start"


def test_validation_month_sequence(tmp_path):
    lg = L(tmp_path, "2026-09")
    _both(lg, 1, ("intent", {}), ("submitted", {"request_id": "x"}), ("downloaded", {"file_sha256": "f", "bytes": 1}))
    d = plan_next(lg, "2026-09", True)
    assert (d["action"], d["retrieval"]) == ("start", 2)
    _both(lg, 2, ("intent", {}), ("submitted", {"request_id": "y"}))
    assert (plan_next(lg, "2026-09", True)["action"], plan_next(lg, "2026-09", True)["retrieval"]) == ("resume", 2)
    _both(lg, 2, ("closed", {"outcome": "evidence"}))
    assert plan_next(lg, "2026-09", True)["action"] == "refuse"            # compared, not published: no third


def test_validation_month_without_retry_slot(tmp_path):
    lg = L(tmp_path, "2026-09")
    _both(lg, 1, ("intent", {}), ("submitted", {"request_id": "x"}), ("closed", {"outcome": "refused"}))
    d = plan_next(L(tmp_path, "2026-09", run="later"), "2026-09", True)
    assert d["action"] == "refuse" and "no retry slot" in d["reason"]


def test_job_counter(tmp_path):
    lg = L(tmp_path)
    _both(lg, 1, ("intent", {}))
    assert lg.cds_jobs_started() == 2 and lg.started() == [1]
