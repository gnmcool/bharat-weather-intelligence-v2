"""Append-only CDS job ledger on archive-index (D2 plan §7.3) and the retrieval limit (§7.1).

`reference/era5/jobs/YYYY-MM.jsonl`: one JSON line per event; lines are never edited or deleted. Every event is
pushed to archive-index before the run continues (the `persist` callback), so an `intent` is durable *before* the
submit call and a `request_id` is durable *before* anything else happens with the job.
"""
from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone

from era5_common import MAX_RETRIEVALS, ROLES, VALIDATION_MONTH, ReferenceError_

EVENTS = ("intent", "submitted", "status", "downloaded", "closed")
TERMINAL_OUTCOMES = ("published", "refused", "evidence")     # a `closed` with outcome "pending" keeps the job open


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Ledger:
    def __init__(self, index_root: pathlib.Path, month: str, run_id: str, persist=None, clock=now_utc):
        self.path = pathlib.Path(index_root) / "reference" / "era5" / "jobs" / f"{month}.jsonl"
        self.month, self.run_id = month, str(run_id)
        self._persist = persist or (lambda msg: None)
        self._clock = clock

    # ------------------------------------------------------------ storage
    def events(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(x) for x in self.path.read_text().splitlines() if x.strip()]

    def append(self, event: str, retrieval: int, role: str | None, **fields) -> dict:
        if event not in EVENTS:
            raise ValueError(event)
        rec = {"event": event, "month": self.month, "retrieval": int(retrieval), "role": role,
               "run_id": self.run_id, "utc": self._clock(), **fields}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        before = self.path.read_bytes() if self.path.exists() else b""
        with open(self.path, "ab") as f:
            f.write((json.dumps(rec, sort_keys=True) + "\n").encode())
        if not self.path.read_bytes().startswith(before):          # append-only guard
            raise ReferenceError_("job ledger was modified instead of appended")
        self._persist(f"reference/era5: {self.month} r{retrieval} {role or '-'} {event} (run {self.run_id})")
        return rec

    # ------------------------------------------------------------ state
    def job(self, retrieval: int, role: str) -> dict:
        """State of one job: none | uncertain | open | failed | downloaded | closed(<outcome>)."""
        evs = [e for e in self.events() if e["retrieval"] == retrieval and e["role"] == role]
        st = {"retrieval": retrieval, "role": role, "state": "none", "request_id": None, "request_sha256": None,
              "items": None, "file_sha256": None, "bytes": None, "outcome": None, "submitted_utc": None,
              "closed_run_id": None}
        for e in evs:
            if e["event"] == "intent":
                st.update(state="uncertain", request_sha256=e.get("request_sha256"), items=e.get("items"))
            elif e["event"] == "submitted":
                st.update(state="open", request_id=e["request_id"], submitted_utc=e["utc"])
            elif e["event"] == "status":
                if e.get("status_class") == "failed":
                    st["state"] = "failed"
            elif e["event"] == "downloaded":
                st.update(state="downloaded", file_sha256=e["file_sha256"], bytes=e["bytes"])
            elif e["event"] == "closed":
                st["outcome"] = e["outcome"]
                if e["outcome"] in TERMINAL_OUTCOMES:
                    st.update(state=f"closed:{e['outcome']}", closed_run_id=e["run_id"])
        return st

    def retrieval(self, r: int) -> dict:
        jobs = {role: self.job(r, role) for role in ROLES}
        states = {j["state"] for j in jobs.values()}
        if states == {"none"}:
            s = "none"
        elif any(x.startswith("closed:refused") or x == "failed" for x in states):
            s = "refused"
        elif all(x == "closed:published" for x in states):
            s = "published"
        elif all(x == "closed:evidence" for x in states):
            s = "evidence"
        elif "uncertain" in states:
            s = "uncertain"
        elif all(x == "downloaded" for x in states):
            s = "downloaded"
        else:
            s = "in_progress"
        closed_runs = {j["closed_run_id"] for j in jobs.values() if j["closed_run_id"]}
        return {"retrieval": r, "state": s, "jobs": jobs, "closed_run_ids": sorted(closed_runs)}

    def started(self) -> list[int]:
        return sorted({e["retrieval"] for e in self.events() if e["event"] == "intent"})

    def cds_jobs_started(self) -> int:
        return sum(1 for e in self.events() if e["event"] == "intent")


def plan_next(ledger: Ledger, month: str, repeat_check: bool) -> dict:
    """Decide what this run may do for the month (§7.1, §11). Never returns a third retrieval.

    Returns {"action": resume|start|refuse|done, "retrieval": r, "reason": ...}."""
    if repeat_check != (month == VALIDATION_MONTH):
        return {"action": "refuse", "retrieval": None,
                "reason": f"R2 (repeat_check) is required for {VALIDATION_MONTH} only; got repeat_check="
                          f"{repeat_check} for {month}"}
    r1, r2 = ledger.retrieval(1), ledger.retrieval(2)
    for r in (r2, r1):
        if r["state"] == "uncertain":
            return {"action": "refuse_uncertain", "retrieval": r["retrieval"],
                    "reason": "submission uncertain: an intent was recorded without a request id; the retrieval "
                              "counts as used and is never resubmitted automatically"}
    if "published" in (r1["state"], r2["state"]):
        return {"action": "done", "retrieval": None, "reason": "already published"}
    if r1["state"] == "none":
        return {"action": "start", "retrieval": 1, "reason": "first retrieval"}
    if r1["state"] == "in_progress" and r2["state"] == "none":
        return {"action": "resume", "retrieval": 1, "reason": "resume retrieval 1 by request id"}
    if repeat_check:                                            # validation month: retrieval 2 is the R2 repeat
        if r1["state"] == "refused":
            return {"action": "refuse", "retrieval": None,
                    "reason": f"{VALIDATION_MONTH}: retrieval 1 was refused; the second retrieval is reserved for the "
                              "R2 repeat, so the month has no retry slot (owner decision required)"}
        if r2["state"] == "refused":
            return {"action": "refuse", "retrieval": None, "reason": "R2 retrieval refused; no third retrieval"}
        if r2["state"] == "evidence":
            return {"action": "refuse", "retrieval": None,
                    "reason": "R2 already compared and recorded; the month was not published; no third retrieval"}
        if r2["state"] in ("in_progress", "downloaded"):
            return {"action": "resume", "retrieval": 2, "reason": "resume the R2 retrieval by request id"}
        return {"action": "start", "retrieval": 2, "reason": "R2 repeat after a downloaded retrieval 1"}
    if r1["state"] == "downloaded" and r2["state"] == "none":
        return {"action": "resume", "retrieval": 1, "reason": "retrieval 1 downloaded earlier; re-download by "
                                                              "request id and publish"}
    # normal month: a second retrieval only after retrieval 1 definitively failed, and never in the same run
    if r2["state"] in ("in_progress", "downloaded"):
        return {"action": "resume", "retrieval": 2, "reason": "resume retrieval 2 by request id"}
    if r2["state"] != "none":
        return {"action": "refuse", "retrieval": None,
                "reason": f"retrieval limit reached ({MAX_RETRIEVALS} retrievals); no automatic third retrieval"}
    if r1["state"] == "refused":
        if ledger.run_id in r1["closed_run_ids"]:
            return {"action": "stop", "retrieval": None,
                    "reason": "retrieval 1 was refused in this run; a second retrieval needs a new committed request"}
        return {"action": "start", "retrieval": 2, "reason": "second retrieval after a refused retrieval 1"}
    return {"action": "resume", "retrieval": 1, "reason": "resume retrieval 1"}
