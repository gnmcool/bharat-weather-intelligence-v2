"""D2 pipeline QUALIFICATION on one already-final historical month (January 2025). NOT a D2 reference.

QUALIFICATION — not a D2 reference; never used in M4.4 metrics.

Purpose: exercise the production D2 code end to end against the real CDS before the first official month (2026-09)
becomes eligible: credential preflight, the two-request retrieval (boundary + month), submit-once / request-id
ledger / polling / download, GRIB structural and expver=0001 validation, 36-point extraction, IST-day aggregation,
the R2 value-level comparison and the (unpublished) release staging. See docs/M4.4-D2_QUALIFICATION.md.

It reuses the production functions in era5_run unchanged (preflight, run_retrieval, build_stage) and era5_r2.compare.
It differs from the production driver only in what it is NOT able to do:
- months: an explicit allow-list containing only 2025-01; every other month (including 2026-09) is refused;
- index: the ledger and records live under `qualification/era5/...` in a worktree of the separate branch
  `era5-qualification`; the driver refuses to run against any other branch (in particular `archive-index`) and never
  writes `reference/era5/...`;
- publication: there is none. No GitHub client is passed, the production publish/index functions are never called,
  and outputs are written only to a local work directory (uploaded by the workflow as Actions artifacts);
- the official D2 request file is never read or written.
The production limits still apply: each CDS job submitted at most once, at most 2 retrievals / 4 CDS jobs, R1 + R2,
no automatic third retrieval, library retries disabled, the key never recorded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))

import era5_common as C  # noqa: E402
import era5_r2 as R2  # noqa: E402
import era5_run as RUN  # noqa: E402
from era5_cds import redact  # noqa: E402
from era5_ledger import Ledger, now_utc  # noqa: E402

QUAL_LABEL = "QUALIFICATION — not a D2 reference; never used in M4.4 metrics."
QUAL_DATASET = "era5_d2_pipeline_qualification_not_official"   # replaces the official dataset identifier
ALLOWED_MONTHS = ("2025-01",)                      # explicit allow-list: nothing else can be qualified
QUAL_BRANCH = "era5-qualification"                 # the only branch this driver will write to
FORBIDDEN_BRANCHES = ("archive-index", "main", "m4-history")
QUAL_PREFIX = ("qualification", "era5")            # records live under qualification/era5/... (never reference/era5/)
REQUEST_FILE = "reference/era5_qualification_request.json"


class QualificationRefused(RuntimeError):
    pass


class QualLedger(Ledger):
    """The production ledger, stored under qualification/era5/jobs/ instead of reference/era5/jobs/."""

    def __init__(self, index_root, month, run_id, persist=None, clock=now_utc):
        inner = persist or (lambda msg: None)

        def qual_persist(msg: str) -> None:            # commit messages say qualification/era5, never reference/era5
            inner(msg.replace("reference/era5:", "qualification/era5:", 1))
        super().__init__(index_root, month, run_id, persist=qual_persist, clock=clock)
        self.path = pathlib.Path(index_root).joinpath(*QUAL_PREFIX, "jobs", f"{month}.jsonl")


# ================================================================== guards
def check_month(month: str) -> None:
    if month not in ALLOWED_MONTHS:
        raise QualificationRefused(f"month {month!r} is not in the qualification allow-list {list(ALLOWED_MONTHS)}; "
                                   "qualification never touches any other month (in particular 2026-09)")
    if month >= C.VALIDATION_MONTH:                # belt and braces: never the prospective period
        raise QualificationRefused(f"{month} is in the D2 prospective period; qualification refused")


def check_index(index: pathlib.Path) -> None:
    """The index must be a git worktree checked out on the era5-qualification branch."""
    r = subprocess.run(["git", "-C", str(index), "symbolic-ref", "--short", "HEAD"], capture_output=True, text=True)
    branch = r.stdout.strip() if r.returncode == 0 else None
    if branch in FORBIDDEN_BRANCHES or branch != QUAL_BRANCH:
        raise QualificationRefused(f"qualification index must be a worktree of branch {QUAL_BRANCH!r}; "
                                   f"got {branch!r} ({index}); refusing to write anywhere else")
    if (index / "reference" / "era5").exists():
        raise QualificationRefused("qualification index contains reference/era5/ (official D2 layout); refusing")


def read_request(path: pathlib.Path) -> dict:
    doc = json.loads(pathlib.Path(path).read_text())
    if set(doc) != {"month", "purpose"}:
        raise QualificationRefused(f"{REQUEST_FILE}: exactly the keys 'month' and 'purpose' are required")
    if not isinstance(doc["purpose"], str) or not doc["purpose"].strip():
        raise QualificationRefused(f"{REQUEST_FILE}: 'purpose' is required")
    check_month(doc["month"])
    return doc


# ================================================================== records (qualification branch only)
def _qpath(deps: RUN.Deps, *parts: str) -> pathlib.Path:
    return deps.index.joinpath(*QUAL_PREFIX, *parts)


def _write_record(deps: RUN.Deps, path: pathlib.Path, obj: dict, msg: str) -> None:
    if path.exists():
        raise QualificationRefused(f"record {path.name} already exists; never overwritten")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"QUALIFICATION_NOTICE": QUAL_LABEL, "official": False, **obj}, indent=1,
                               sort_keys=True, default=str) + "\n")
    deps.persist(msg)


def qual_names(month: str) -> dict:
    """Qualification-only names for the manifest and gap report (official D2 names are never used for outputs)."""
    return {f"manifest_{C.tag_for(month)}.json": f"qualification_manifest_era5_{month}.json",
            f"gap_report_{C.tag_for(month)}.json": f"qualification_gap_report_era5_{month}.json"}


def _label_outputs(out: pathlib.Path, month: str) -> None:
    """Mark every qualification output as non-official and give the manifest / gap report qualification names."""
    names = qual_names(month)
    for old, new in names.items():
        (out / old).rename(out / new)
    (out / "QUALIFICATION_README.txt").write_text(
        f"{QUAL_LABEL}\n\nERA5 D2 pipeline qualification for {month}. These files test the production D2 code and "
        "release format. They are not a D2 reference release, are not published, and must never be used as reference "
        "data or in any M4.4 verification metric.\n")
    man = out / names[f"manifest_{C.tag_for(month)}.json"]
    doc = json.loads(man.read_text())
    for f in doc.get("files", []):                     # same bytes and SHA-256, qualification name
        f["name"] = names.get(f["name"], f["name"])
    doc = {**doc, "QUALIFICATION_NOTICE": QUAL_LABEL, "official": False, "dataset": QUAL_DATASET,
           "role": "pipeline qualification only (not a reference)"}
    man.write_text(json.dumps(doc, indent=1, sort_keys=True, default=str) + "\n")


# ================================================================== qualification run
def qualify(deps: RUN.Deps, month: str) -> dict:
    """Preflight -> R1 (2 jobs) -> R2 (2 jobs) -> value-level comparison -> labelled, unpublished outputs."""
    check_month(month)
    check_index(deps.index)
    if deps.gh is not None:
        raise QualificationRefused("qualification must run without a GitHub release client (no publication)")
    if not C.is_eligible(month, deps.today):
        raise QualificationRefused(f"{month} not yet past its 70-day date")
    report_path = _qpath(deps, "results", f"{month}.json")
    if report_path.exists():
        return {"month": month, "outcome": "done", "reason": "qualification already recorded; no CDS call",
                "label": QUAL_LABEL}
    deps.work.mkdir(parents=True, exist_ok=True)
    ledger = QualLedger(deps.index, month, deps.run_id, persist=deps.persist, clock=deps.now)
    for r in (1, 2):
        if ledger.retrieval(r)["state"] in ("refused", "uncertain"):
            return _fail(deps, month, ledger, f"retrieval {r} is {ledger.retrieval(r)['state']}; the qualification "
                                              "has failed and no further CDS jobs are submitted", "retrieval limit")
    requests = C.build_requests(month)
    try:
        RUN.preflight(deps)                                           # no job; nothing in the ledger on failure
        first = RUN.run_retrieval(deps, ledger, month, 1, requests)   # R1: boundary + month
        second = RUN.run_retrieval(deps, ledger, month, 2, requests)  # R2: identical repeat
    except RUN.Pending as p:
        return {"month": month, "outcome": "pending", "reason": deps.red(p), "label": QUAL_LABEL}
    except RUN.Refused as e:
        return _fail(deps, month, ledger, e.reason, e.check)
    except C.ReferenceError_ as e:
        return _fail(deps, month, ledger, str(e), "rule")
    cmp_ = R2.compare(month, first, second)
    stage = RUN.build_stage(deps, month, first, requests, ledger, f"qualification/era5/results/{month}.json", True,
                            C.points_sha256(deps.points_file))
    out = deps.work / f"QUALIFICATION_era5_{month}"
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(stage, out)
    shutil.rmtree(stage)
    _label_outputs(out, month)
    files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}
    days = first["tables"]["days"]
    for k, outcome in ((1, "evidence"), (2, "evidence")):
        for role in C.ROLES:
            ledger.append("closed", k, role, outcome=outcome, note="qualification run (not published)")
    rec = {"month": month, "run_id": deps.run_id, "recorded_utc": deps.now(), "code": deps.code,
           "passed": bool(cmp_["passed"]), "r2": cmp_,
           "request_ids": {f"retrieval_{k}": {role: ledger.job(k, role)["request_id"] for role in C.ROLES}
                           for k in (1, 2)},
           "requests": {role: {"canonical_json": C.canonical_json(requests[role]),
                               "request_sha256": C.request_sha256(requests[role]),
                               "items": C.item_count(requests[role])} for role in C.ROLES},
           "expver": {role: first["summaries"][role]["expver"] for role in C.ROLES},
           "grib_sha256": {f"retrieval_{k}": {role: res["files"][role]["sha256"] for role in C.ROLES}
                           for k, res in ((1, first), (2, second))},
           "ist_days": {"rows": int(len(days)), "complete": int(days.reason.isna().sum()),
                        "E": int((days.reason == "E").sum()), "G": int((days.reason == "G").sum())},
           "preflight": {"ok": deps.preflight_result["ok"], "licence_check": deps.preflight_result.get("licence_check")},
           "output_files_sha256": files, "artifact_dir": out.name}
    _write_record(deps, report_path, rec, f"qualification/era5: {month} result ({'pass' if rec['passed'] else 'FAIL'})")
    return {"month": month, "outcome": "passed" if rec["passed"] else "failed", "label": QUAL_LABEL,
            "output_dir": str(out), "r2_passed": rec["passed"]}


def _fail(deps: RUN.Deps, month: str, ledger: QualLedger, reason: str, check: str) -> dict:
    path = _qpath(deps, "refused", f"{month}_{deps.run_id}.json")
    _write_record(deps, path, {"month": month, "run_id": deps.run_id, "recorded_utc": deps.now(),
                               "reason": deps.red(reason), "failing_check": check, "code": deps.code},
                  f"qualification/era5: {month} refused ({check})")
    return {"month": month, "outcome": "refused", "reason": deps.red(reason), "check": check, "label": QUAL_LABEL}


# ================================================================== CLI (GitHub Actions)
def push_branch(index: pathlib.Path, msg: str) -> None:
    """Commit and push the qualification worktree to origin/era5-qualification only."""
    check_index(index)

    def git(*a):
        return subprocess.run(["git", "-C", str(index), *a], capture_output=True, text=True)
    git("add", "-A")
    if git("diff", "--cached", "--quiet").returncode == 0:
        return
    if git("commit", "-qm", msg).returncode:
        raise RuntimeError("qualification commit failed")
    for _ in range(5):
        if git("push", "-q", "origin", f"HEAD:refs/heads/{QUAL_BRANCH}").returncode == 0:
            return
        git("pull", "-q", "--rebase", "origin", QUAL_BRANCH)
    raise RuntimeError("could not push the qualification branch")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="D2 pipeline qualification (2025-01 only; never published)")
    ap.add_argument("--request", required=True)
    ap.add_argument("--index", required=True, help=f"worktree of branch {QUAL_BRANCH}")
    ap.add_argument("--work", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--poll-deadline-min", type=int, default=300)
    a = ap.parse_args(argv)
    key = os.environ.get("CDS_API_KEY", "")
    secrets = (key,) if key else ()
    try:
        doc = read_request(pathlib.Path(a.request))
        index = pathlib.Path(a.index)
        check_index(index)
    except (QualificationRefused, ValueError) as e:
        print(json.dumps({"label": QUAL_LABEL, "error": redact(e, secrets)}, ensure_ascii=False))
        return 1
    from era5_cds import CDSClient
    pol = RUN.RetryPolicy(poll_deadline_s=a.poll_deadline_min * 60)
    deps = RUN.Deps(cds=CDSClient(key) if key else None, gh=None, index=index, work=pathlib.Path(a.work),
                    run_id=a.run_id, persist=lambda msg: push_branch(index, msg),
                    today=datetime.now(timezone.utc).date(), policy=pol, code=RUN._code_info(), secrets=secrets)
    deps.deadline = time.monotonic() + pol.poll_deadline_s
    try:
        out = qualify(deps, doc["month"])
    except QualificationRefused as e:
        out = {"month": doc["month"], "outcome": "refused", "reason": redact(e, secrets), "label": QUAL_LABEL}
    print(redact(json.dumps({"label": QUAL_LABEL, "run_id": a.run_id, "purpose": doc["purpose"], "result": out},
                            indent=1, default=str, ensure_ascii=False), secrets))
    return 0 if out["outcome"] in ("passed", "done", "pending") else 1


if __name__ == "__main__":
    sys.exit(main())
