"""D2 driver: committed request file -> CDS retrieval by request id -> validation -> R2 -> immutable release.

Specification: docs/M4.4-D2_PLAN.md (revision 3, frozen at 781d2e8), §4-§11. Run only by
.github/workflows/era5-reference.yml when a commit changes reference/era5_request.json (no schedule, no manual
trigger). Offline tests drive `process_month` with fake CDS / GitHub / index objects.

Guarantees (each enforced in code and tested):
- a month is requested only on or after its eligibility date (last day + 70 days), and published only if every
  requested value has expver = 0001;
- each CDS job is submitted at most once; its intent is persisted *before* the submit call and its request id
  *immediately after*; timeouts end the run as "pending" and a later run resumes by request id;
- an uncertain submission (transport error, 5xx) consumes the retrieval and is never resubmitted;
- at most two retrievals (four CDS jobs) per month; R2 only for 2026-09; never an automatic third retrieval;
- library retries are disabled; the BWI retry table (RetryPolicy) is applied here;
- nothing partial is published; releases are immutable; archive-index records are append-only;
- the CDS key is never written to any file, record, error text or log.
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
from dataclasses import dataclass, field
from datetime import date, datetime, timezone

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))

import era5_common as C  # noqa: E402
import era5_extract as X  # noqa: E402
import era5_grib as G  # noqa: E402
import era5_r2 as R2  # noqa: E402
from era5_cds import CDSDownloadError, CDSError, CDSHTTPError, CDSJobFailed, CDSTransportError, redact, status_class  # noqa: E402
from era5_ledger import Ledger, now_utc, plan_next  # noqa: E402

SCHEMA_VERSION = 1
TARGET_KIND = "grib_month"            # asset used for the post-publication tamper attempts


# ================================================================== policy (§8.3; BWI parameters, not CDS limits)
@dataclass
class RetryPolicy:
    transient_waits: tuple = (30, 60, 120)     # poll/download: transport error, 5xx -> 3 retries
    wait_429: int = 120                        # 429 on poll/download: wait 120 s (within the same 3-retry cap)
    redownloads: int = 2                       # malformed/incomplete download: re-download the same result 2 more times
    poll_first: int = 60                       # queued/running: poll every 60 s, doubling to at most 600 s
    poll_max: int = 600
    poll_deadline_s: int = 300 * 60            # below the GitHub Actions job limit (330 min)


@dataclass
class Deps:
    cds: object | None                         # era5_cds.CDSClient (None when CDS_API_KEY is absent)
    gh: object                                 # history.backfill.GH-compatible (+ delete_draft)
    index: pathlib.Path                        # archive-index worktree
    work: pathlib.Path
    run_id: str
    persist: object                            # callable(msg): commit + push the archive-index worktree
    today: date
    sleep: object = time.sleep
    monotonic: object = time.monotonic
    policy: RetryPolicy = field(default_factory=RetryPolicy)
    code: dict = field(default_factory=dict)
    points_file: pathlib.Path = C.POINTS_FILE
    secrets: tuple = ()
    deadline: float | None = None
    now: object = now_utc                      # UTC ISO timestamp for records (injectable in tests)
    preflight_result: dict | None = None       # credential preflight, run at most once per workflow run

    def red(self, x) -> str:
        return redact(x, self.secrets)


class Pending(Exception):
    """The job is still queued/running (or transiently unreachable) at the deadline: resume later by request id."""


class Refused(Exception):
    def __init__(self, reason: str, check: str = "refused"):
        super().__init__(reason)
        self.reason, self.check = reason, check


# ================================================================== request file
def read_request(path: pathlib.Path) -> dict:
    doc = json.loads(pathlib.Path(path).read_text())
    allowed = {"months", "purpose", "repeat_check"}
    if set(doc) - allowed:
        raise C.ReferenceError_(f"request file: unexpected keys {sorted(set(doc) - allowed)}")
    months = doc.get("months")
    if not isinstance(months, list) or not months or len(set(months)) != len(months):
        raise C.ReferenceError_("request file: 'months' must be a non-empty list of distinct YYYY-MM")
    for m in months:
        C.parse_month(m)
    if not isinstance(doc.get("purpose"), str) or not doc["purpose"].strip():
        raise C.ReferenceError_("request file: 'purpose' is required")
    if not isinstance(doc.get("repeat_check"), bool):
        raise C.ReferenceError_("request file: 'repeat_check' must be true or false")
    return doc


# ================================================================== archive-index records (append-only)
def _idx_path(deps: Deps, *parts: str) -> pathlib.Path:
    return deps.index.joinpath("reference", "era5", *parts)


def write_new(path: pathlib.Path, obj) -> None:
    """Create a record; an existing record is never overwritten."""
    if path.exists():
        raise C.ReferenceError_(f"archive-index record {path.name} already exists; never overwritten")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, sort_keys=True, default=str) + "\n")


def record_refusal(deps: Deps, month: str, reason: str, check: str, ledger: Ledger | None, extra: dict | None = None):
    rec = {"month": month, "run_id": deps.run_id, "recorded_utc": deps.now(), "reason": deps.red(reason),
           "failing_check": check, "code": deps.code, "published": False,
           "jobs": _jobs_summary(ledger) if ledger else [], **(extra or {})}
    write_new(_idx_path(deps, "refused", f"{month}_{deps.run_id}.json"), rec)
    deps.persist(f"reference/era5: {month} refused ({check}) run {deps.run_id}")
    return rec


def _jobs_summary(ledger: Ledger) -> list[dict]:
    out = []
    for r in (1, 2):
        for role in C.ROLES:
            j = ledger.job(r, role)
            if j["state"] != "none":
                out.append({k: j[k] for k in ("retrieval", "role", "state", "request_id", "request_sha256", "items",
                                              "file_sha256", "bytes", "outcome", "submitted_utc")})
    return out


# ================================================================== one CDS job
def _deadline_passed(deps: Deps) -> bool:
    return deps.deadline is not None and deps.monotonic() >= deps.deadline


def _transient(deps: Deps, attempt: int, err: CDSError) -> bool:
    """Wait for the next transient retry; False when the 3-retry cap is exhausted."""
    if attempt >= len(deps.policy.transient_waits):
        return False
    wait = deps.policy.wait_429 if isinstance(err, CDSHTTPError) and err.status == 429 \
        else deps.policy.transient_waits[attempt]
    deps.sleep(wait)
    return True


def _is_transient(err: CDSError) -> bool:
    return isinstance(err, CDSTransportError) or (isinstance(err, CDSHTTPError) and (err.status >= 500 or err.status == 429))


def submit_job(deps: Deps, ledger: Ledger, r: int, role: str, request: dict) -> None:
    """intent (persisted) -> one submit call -> request id (persisted). Never a second submit for the same job."""
    st = ledger.job(r, role)
    if st["state"] != "none":
        return
    if deps.cds is None:
        raise Refused("CDS_API_KEY is not available to the workflow; nothing submitted", "credentials")
    if ledger.cds_jobs_started() >= 2 * C.MAX_RETRIEVALS:
        raise Refused("four CDS jobs already started for this month; no further submission", "retrieval limit")
    sha = C.request_sha256(request)
    ledger.append("intent", r, role, request_sha256=sha, items=C.item_count(request))   # persisted before the call
    try:
        rid = deps.cds.submit(request)
    except CDSHTTPError as e:
        if 400 <= e.status < 500 and e.status != 429:
            ledger.append("closed", r, role, outcome="refused", reason=deps.red(f"HTTP {e.status} on submit: {e}"))
            raise Refused(f"CDS rejected the {role} request (HTTP {e.status}): {deps.red(e)}", "submit 4xx") from None
        ledger.append("closed", r, role, outcome="refused", reason=deps.red(f"submission uncertain: {e}"))
        raise Refused(f"submission uncertain for the {role} request ({deps.red(e)}); the retrieval counts as used "
                      "and is never resubmitted automatically", "submission uncertain") from None
    except CDSError as e:
        ledger.append("closed", r, role, outcome="refused", reason=deps.red(f"submission uncertain: {e}"))
        raise Refused(f"submission uncertain for the {role} request ({deps.red(e)}); the retrieval counts as used "
                      "and is never resubmitted automatically", "submission uncertain") from None
    ledger.append("submitted", r, role, request_id=rid, request_sha256=sha)          # persisted immediately


def poll_job(deps: Deps, ledger: Ledger, r: int, role: str) -> dict:
    """Poll by request id until successful. Raises Pending (deadline / transient cap) or Refused (failed job, 4xx)."""
    st = ledger.job(r, role)
    rid = st["request_id"]
    interval, errors, last = deps.policy.poll_first, 0, None
    while True:
        try:
            s = deps.cds.status(rid)
        except CDSError as e:
            if _is_transient(e):
                if not _transient(deps, errors, e):
                    raise Pending(f"{role}: status unreachable after {errors} retries ({deps.red(e)})") from None
                errors += 1
                continue
            ledger.append("closed", r, role, outcome="refused", reason=deps.red(f"poll: {e}"))
            raise Refused(f"{role}: CDS error while polling ({deps.red(e)})", "poll 4xx") from None
        errors = 0
        cls = status_class(s)
        if cls != last:
            ledger.append("status", r, role, request_id=rid, status=s, status_class=cls)
            last = cls
        if cls == "successful":
            return {"request_id": rid, "successful_utc": deps.now()}
        if cls == "failed":
            ledger.append("closed", r, role, outcome="refused", reason=f"CDS job status {s}")
            raise Refused(f"{role}: CDS job {rid} ended with status {s}", "job failed")
        if _deadline_passed(deps):
            raise Pending(f"{role}: job {rid} still {s} at the poll deadline")
        deps.sleep(interval)
        interval = min(interval * 2, deps.policy.poll_max)


def download_job(deps: Deps, ledger: Ledger, r: int, role: str, request: dict) -> tuple[pathlib.Path, dict]:
    """Download a completed result by request id and decode it. Re-downloads the *same result* only."""
    st = ledger.job(r, role)
    rid = st["request_id"]
    target = deps.work / f"r{r}_{role}.grib"
    malformed, errors = 0, 0
    t0 = deps.monotonic()
    while True:
        try:
            if target.exists():
                target.unlink()
            got = deps.cds.download(rid, target) or {}
            want = got.get("announced_bytes")
            if want is not None and target.stat().st_size != int(want):
                raise CDSDownloadError(f"downloaded {target.stat().st_size} bytes, announced {want}")
            dec = G.decode(target)
        except (CDSDownloadError, G.GribDecodeError) as e:
            if malformed >= deps.policy.redownloads:
                ledger.append("closed", r, role, outcome="refused", reason=deps.red(f"malformed download: {e}"))
                raise Refused(f"{role}: malformed or incomplete download after {malformed + 1} attempts "
                              f"({deps.red(e)}); not resubmitted", "malformed download") from None
            malformed += 1
            continue
        except CDSError as e:
            if _is_transient(e):
                if not _transient(deps, errors, e):
                    raise Pending(f"{role}: download unreachable after {errors} retries ({deps.red(e)})") from None
                errors += 1
                continue
            ledger.append("closed", r, role, outcome="refused", reason=deps.red(f"download: {e}"))
            raise Refused(f"{role}: result of {rid} not downloadable ({deps.red(e)}); not resubmitted",
                          "download 4xx") from None
        break
    if st["file_sha256"] and st["file_sha256"] != dec["sha256"]:
        ledger.append("closed", r, role, outcome="refused",
                      reason=f"re-download differs from the recorded file ({dec['sha256'][:12]} != {st['file_sha256'][:12]})")
        raise Refused(f"{role}: re-downloaded result differs from the file recorded earlier", "result changed")
    if not st["file_sha256"]:
        ledger.append("downloaded", r, role, request_id=rid, bytes=dec["bytes"], file_sha256=dec["sha256"],
                      items=C.item_count(request), download_seconds=round(deps.monotonic() - t0, 3))
    return target, dec


def run_retrieval(deps: Deps, ledger: Ledger, month: str, r: int, requests: dict) -> dict:
    """Submit (once), poll and download both jobs of retrieval r, then validate both files (§5.6, §6)."""
    for role in C.ROLES:                                     # boundary first, then month; each at most once
        submit_job(deps, ledger, r, role, requests[role])
    files, meta = {}, {}
    for role in C.ROLES:
        st = ledger.job(r, role)
        if st["state"] in ("uncertain",) or st["state"].startswith("closed:refused") or st["state"] == "failed":
            raise Refused(f"{role} job of retrieval {r} is {st['state']}", "job state")
        poll = poll_job(deps, ledger, r, role) if st["state"] == "open" else {"request_id": st["request_id"]}
        path, dec = download_job(deps, ledger, r, role, requests[role])
        files[role], meta[role] = dec, {**poll, "path": path}
    problems, summaries = [], {}
    for role in C.ROLES:
        v = G.validate(files[role], requests[role], role)
        problems += v["problems"]
        summaries[role] = v["summary"]
    if problems:
        for role in C.ROLES:
            ledger.append("closed", r, role, outcome="refused", reason="; ".join(problems)[:1000])
        check = "expver" if any(p.startswith("[expver]") for p in problems) else "structure"
        raise Refused("; ".join(problems), check)
    points = C.load_points(deps.points_file)
    stage = deps.work / f"r{r}_tables"
    tables = X.build_tables(points, files, month, stage)
    return {"retrieval": r, "files": files, "meta": meta, "summaries": summaries, "tables": tables,
            "hourly_path": stage / f"era5_hourly_{month}.parquet", "day_path": stage / f"era5_ist_day_{month}.parquet"}


# ================================================================== release
def retrieval_year_utc(ledger: Ledger, r: int) -> str:
    """UTC time of the first recorded download of the month job of retrieval r (the retrieval date)."""
    for e in ledger.events():
        if e["event"] == "downloaded" and e["retrieval"] == r and e["role"] == "month":
            return e["utc"]
    raise C.ReferenceError_(f"retrieval {r}: no recorded download")


def build_stage(deps: Deps, month: str, res: dict, requests: dict, ledger: Ledger, repeat_ref: str | None,
                repeat_check: bool, points_sha: str) -> pathlib.Path:
    stage = deps.work / "stage"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    names = {"boundary": f"era5_cds_boundary_{month}.grib", "month": f"era5_cds_month_{month}.grib"}
    for role in C.ROLES:
        shutil.copyfile(res["meta"][role]["path"], stage / names[role])
    r = res["retrieval"]
    jobs = {role: ledger.job(r, role) for role in C.ROLES}
    req_doc = {role: {"request": requests[role], "canonical_json": C.canonical_json(requests[role]),
                      "request_sha256": C.request_sha256(requests[role]), "request_id": jobs[role]["request_id"]}
               for role in C.ROLES}
    (stage / f"era5_cds_requests_{month}.json").write_text(json.dumps(req_doc, indent=1, sort_keys=True) + "\n")
    shutil.copyfile(res["hourly_path"], stage / res["hourly_path"].name)
    shutil.copyfile(res["day_path"], stage / res["day_path"].name)
    gap_name = f"gap_report_{C.tag_for(month)}.json"
    (stage / gap_name).write_text(json.dumps(res["tables"]["gap"], indent=1, sort_keys=True) + "\n")
    kinds = [("grib_boundary", names["boundary"], None), (TARGET_KIND, names["month"], None),
             ("requests", f"era5_cds_requests_{month}.json", None),
             ("hourly", res["hourly_path"].name, res["tables"]["hourly_rows"]),
             ("ist_day", res["day_path"].name, res["tables"]["day_rows"]), ("gap_report", gap_name, None)]
    files = [{"kind": k, "name": n, "bytes": (stage / n).stat().st_size, "rows": rows,
              "sha256": hashlib.sha256((stage / n).read_bytes()).hexdigest()} for k, n, rows in kinds]
    lic = C.load_licence()
    days = C.month_days(month)
    ev = ledger.events()
    retrieval = []
    for role in C.ROLES:
        j = jobs[role]
        mine = [e for e in ev if e["retrieval"] == r and e["role"] == role]
        st_utc = next((e["utc"] for e in mine if e["event"] == "status" and e.get("status_class") == "successful"), None)
        dl = next((e for e in mine if e["event"] == "downloaded"), {})
        retrieval.append({"role": role, "retrieval": r, "request_id": j["request_id"],
                          "request_sha256": j["request_sha256"], "items_requested": j["items"],
                          "submitted_utc": j["submitted_utc"], "successful_status_utc": st_utc,
                          "downloaded_utc": dl.get("utc"), "bytes_downloaded": j["bytes"],
                          "download_seconds": dl.get("download_seconds"), "file_sha256": j["file_sha256"],
                          "statuses": [e["status"] for e in mine if e["event"] == "status"]})
    retrieved_days = (date.fromisoformat(retrieval_year_utc(ledger, r)[:10]) - days[-1]).days
    nodes = res["tables"]["nodes"]
    stamps_used = [C.ist_day_stamps(d) for d in days]
    requested = C.expected_stamps(requests["boundary"]) + C.expected_stamps(requests["month"])
    used = {t for s in stamps_used for t in s}
    year = int(retrieval_year_utc(ledger, r)[:4])
    man = {
        "dataset": "era5_reference_supplement", "role": "secondary rain reference (interim)",
        "label": "ERA5 reanalysis (secondary)", "month": month, "schema_version": SCHEMA_VERSION, "plan": C.PLAN,
        "source": {"service": "Copernicus Climate Data Store", "api": C.CDS_URL, "cds_dataset": C.DATASET,
                   "product_type": C.PRODUCT_TYPE, "variable": C.VARIABLE, "data_format": C.DATA_FORMAT,
                   "requests": req_doc,
                   "grib_encoding_observed": {role: res["summaries"][role] for role in C.ROLES}},
        "version": {"expver": C.FINAL_EXPVER, "expver_check": "all requested values expver = 0001 (both files)",
                    "statement": f"final ERA5 as served by the CDS at retrieval time; retrieved {retrieved_days} days "
                                 f"after month end (>= {C.WAIT_DAYS}); does not exclude later ECMWF corrections"},
        "retrieval": {"retrieval_number": r, "jobs": retrieval},
        "coverage": {"ist_dates": [str(days[0]), str(days[-1])],
                     "utc_stamps_used": [min(used).isoformat(), max(used).isoformat()],
                     "utc_stamps_requested_unused": sorted(t.isoformat() for t in set(requested) - used)},
        "code": deps.code,
        "points": {"file": "archive/points.json", "sha256": points_sha, "area": C.AREA, "node_rule": C.NODE_RULE,
                   "per_point": [{"point_id": n["point_id"], "lat": str(n["lat"]), "lon": str(n["lon"]),
                                  "node_lat": float(n["node_lat"]), "node_lon": float(n["node_lon"]),
                                  "distance_km": round(n["distance_km"], 3), "eligible": bool(n["eligible"]),
                                  "tie_break_applied": bool(n["tie_break_applied"]), "note": C.NODE_NOTE}
                                 for n in nodes]},
        "aggregation": C.AGGREGATION_RULE,
        "licence": {"licence": lic["licence"], "terms_accepted_on": lic["accepted_on"],
                    "terms_accepted_stated_by": lic["stated_by"], "attribution": C.attribution(year)},
        "files": files,
        "repeat_check": {"repeat_check": repeat_check, "result": repeat_ref},
        "missing_data": {"e_days": len(res["tables"]["gap"]["e_days"]), "g_days": len(res["tables"]["gap"]["g_days"]),
                         "note": "E-days are excluded from M4.4-D metrics, never zero, never forecast misses"},
    }
    (stage / f"manifest_{C.tag_for(month)}.json").write_text(json.dumps(man, indent=1, sort_keys=True, default=str) + "\n")
    return stage


def publish_month(deps: Deps, month: str, res: dict, requests: dict, ledger: Ledger, repeat_ref, repeat_check,
                  points_sha: str, evidence_retrieval: int | None = None) -> dict:
    from history.backfill import PublicationError, publish
    tag = C.tag_for(month)
    stage = build_stage(deps, month, res, requests, ledger, repeat_ref, repeat_check, points_sha)
    man_name = f"manifest_{tag}.json"
    year = int(retrieval_year_utc(ledger, res["retrieval"])[:4])
    try:
        checks = publish(tag, f"ERA5 reference (secondary) {month}",
                         f"D2 ERA5 secondary rain reference for {month} (CDS {C.DATASET}, {C.VARIABLE}, expver "
                         f"{C.FINAL_EXPVER}). {C.attribution(year)['raw_grib']}. {C.NON_RESPONSIBILITY}.",
                         stage, TARGET_KIND, gh=deps.gh)
    except PublicationError as e:
        after = deps.gh.state(tag)
        if after == "draft":
            deps.gh.delete_draft(tag)
        raise Refused(f"publication failed (data valid; the month stays resumable by request id): {e}",
                      "publication") from None
    r = res["retrieval"]
    rec = {"month": month, "tag": tag, "release_url": deps.gh.url(tag), "run_id": deps.run_id,
           "recorded_utc": deps.now(), "manifest_sha256": hashlib.sha256((stage / man_name).read_bytes()).hexdigest(),
           "files": {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(stage.iterdir())},
           "checks": checks, "request_ids": {role: ledger.job(r, role)["request_id"] for role in C.ROLES},
           "e_days": res["tables"]["gap"]["e_days"], "g_days": res["tables"]["gap"]["g_days"],
           "repeat_check": repeat_ref, "code": deps.code}
    write_new(_idx_path(deps, "index", f"{month}.json"), rec)
    for role in C.ROLES:
        ledger.append("closed", r, role, outcome="published", tag=tag)
    if evidence_retrieval:
        for role in C.ROLES:
            ledger.append("closed", evidence_retrieval, role, outcome="evidence", note="R2 repeat (validation evidence)")
    deps.persist(f"reference/era5: {month} published as {tag} (run {deps.run_id})")
    return rec


# ================================================================== credential preflight
LICENCE_CHECK_NOTE = ("partial: the account has accepted at least one dataset licence; the CDS client cannot tell "
                      "which licence ERA5 requires, so this does not prove that the ERA5 terms were accepted")


def preflight(deps: Deps) -> dict:
    """Verify the CDS credential before any ledger intent or submission (no job is created, no data downloaded).

    Calls only the account endpoints: POST /profiles/v1/account/verification/pat and
    GET /profiles/v1/account/licences?scope=dataset. Runs at most once per workflow run (the result, including a
    failure, is cached). A failure raises Refused(..., "credentials") and writes nothing to the job ledger, so no
    retrieval slot is used. The authentication response is never recorded (it may contain account details)."""
    if deps.preflight_result is None:
        deps.preflight_result = _run_preflight(deps)
    res = deps.preflight_result
    if not res["ok"]:
        raise Refused(res["reason"], "credentials")
    return res


def _run_preflight(deps: Deps) -> dict:
    if deps.cds is None:
        return {"ok": False, "reason": "CDS_API_KEY is not available to the workflow; nothing submitted"}
    try:
        deps.cds.check_authentication()
    except CDSHTTPError as e:
        if e.status in (401, 403):
            return {"ok": False, "reason": f"credentials: authentication failed (HTTP {e.status}); nothing submitted"}
        if 400 <= e.status < 500 and e.status != 429:
            return {"ok": False, "reason": deps.red(f"credentials: authentication check rejected (HTTP {e.status}): "
                                                   f"{e}; nothing submitted")}
        return {"ok": False, "reason": deps.red(f"credentials: preflight unavailable ({e}); nothing submitted")}
    except CDSError as e:
        return {"ok": False, "reason": deps.red(f"credentials: preflight unavailable ({e}); nothing submitted")}
    try:
        licences = deps.cds.accepted_dataset_licences()
    except CDSHTTPError as e:
        if 400 <= e.status < 500 and e.status != 429:
            return {"ok": False, "reason": deps.red(f"credentials: licence check rejected (HTTP {e.status}): {e}; "
                                                   "nothing submitted")}
        return {"ok": False, "reason": deps.red(f"credentials: preflight unavailable ({e}); nothing submitted")}
    except CDSError as e:
        return {"ok": False, "reason": deps.red(f"credentials: preflight unavailable ({e}); nothing submitted")}
    if not licences:
        return {"ok": False, "reason": "credentials: no dataset licence accepted on this CDS account; nothing submitted"}
    return {"ok": True, "authentication": "ok", "accepted_dataset_licences": licences,
            "licence_check": LICENCE_CHECK_NOTE}


# ================================================================== one month
def process_month(deps: Deps, month: str, repeat_check: bool) -> dict:
    tag = C.tag_for(month)
    deps.work.mkdir(parents=True, exist_ok=True)
    if deps.gh.state(tag) == "published":
        return {"month": month, "outcome": "done", "reason": f"{tag} is already published; never overwritten"}
    if not C.is_eligible(month, deps.today):
        rec = record_refusal(deps, month, f"eligibility date {C.eligibility_date(month)} not reached "
                                          f"(today {deps.today}); nothing submitted", "eligibility", None)
        return {"month": month, "outcome": "refused", "reason": rec["reason"]}
    try:
        points = C.load_points(deps.points_file)
        points_sha = C.points_sha256(deps.points_file)
        if C.area_for(points) != C.AREA or len(points) != C.N_POINTS:
            raise C.ReferenceError_(f"area {C.area_for(points)} / {len(points)} points differ from the plan")
    except C.ReferenceError_ as e:
        rec = record_refusal(deps, month, str(e), "points", None)
        return {"month": month, "outcome": "refused", "reason": rec["reason"]}
    ledger = Ledger(deps.index, month, deps.run_id, persist=deps.persist, clock=deps.now)
    requests = C.build_requests(month)
    decision = plan_next(ledger, month, repeat_check)
    try:
        if decision["action"] == "done":
            return {"month": month, "outcome": "done", "reason": decision["reason"]}
        if decision["action"] == "stop":
            return {"month": month, "outcome": "stopped", "reason": decision["reason"]}
        if decision["action"] == "refuse_uncertain":
            r = decision["retrieval"]
            for role in C.ROLES:
                if ledger.job(r, role)["state"] in ("uncertain", "open", "downloaded"):
                    ledger.append("closed", r, role, outcome="refused", reason="submission uncertain")
            raise Refused(decision["reason"], "submission uncertain")
        if decision["action"] == "refuse":
            raise Refused(decision["reason"], "retrieval limit")
        preflight(deps)                      # before any ledger write or submit; raises Refused("credentials")
        r = decision["retrieval"]
        if not repeat_check:
            res = run_retrieval(deps, ledger, month, r, requests)
            rec = publish_month(deps, month, res, requests, ledger, None, False, points_sha)
            return {"month": month, "outcome": "published", "tag": tag, "retrieval": r, "release": rec["release_url"]}
        # validation month (R2): retrieval 1 complete and valid, then retrieval 2, then the value-level comparison
        first = run_retrieval(deps, ledger, month, 1, requests)
        second = run_retrieval(deps, ledger, month, 2, requests)
        cmp_ = R2.compare(month, first, second)
        vpath = _idx_path(deps, "validation", f"{month}_repeat.json")
        if vpath.exists():                   # an earlier run compared and passed, then publication failed
            prev = json.loads(vpath.read_text())
            if not (prev.get("passed") and cmp_["passed"]):
                raise Refused("R2 record exists but the comparison does not pass now", "R2")
        else:
            vrec = {"month": month, "run_id": deps.run_id, "recorded_utc": deps.now(), **cmp_,
                    "request_ids": {f"retrieval_{k}": {role: ledger.job(k, role)["request_id"] for role in C.ROLES}
                                    for k in (1, 2)}}
            write_new(vpath, vrec)
            deps.persist(f"reference/era5: {month} R2 comparison ({'pass' if cmp_['passed'] else 'FAIL'})")
        if not cmp_["passed"]:
            for k, outcome in ((1, "refused"), (2, "evidence")):
                for role in C.ROLES:
                    ledger.append("closed", k, role, outcome=outcome, reason="R2 comparison failed")
            raise Refused("R2 comparison failed: " + "; ".join(cmp_["problems"]), "R2")
        ref = f"reference/era5/validation/{month}_repeat.json"
        rec = publish_month(deps, month, first, requests, ledger, ref, True, points_sha, evidence_retrieval=2)
        return {"month": month, "outcome": "published", "tag": tag, "retrieval": 1, "repeat_check": ref,
                "release": rec["release_url"]}
    except Pending as p:
        for r in (1, 2):
            for role in C.ROLES:
                j = ledger.job(r, role)
                if j["state"] in ("open", "downloaded") and j["request_id"]:
                    ledger.append("closed", r, role, outcome="pending", reason=deps.red(p))
        return {"month": month, "outcome": "pending", "reason": deps.red(p)}
    except Refused as e:
        rec = record_refusal(deps, month, e.reason, e.check, ledger)
        return {"month": month, "outcome": "refused", "reason": rec["reason"], "check": e.check}
    except C.ReferenceError_ as e:
        rec = record_refusal(deps, month, str(e), "rule", ledger)
        return {"month": month, "outcome": "refused", "reason": rec["reason"], "check": "rule"}


# ================================================================== CLI (GitHub Actions)
def _code_info() -> dict:
    def git(*a):
        r = subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True)
        return r.stdout.strip() or None
    from importlib import metadata
    vers = {}
    for p in ("ecmwf-datastores-client", "multiurl", "eccodes", "pandas", "pyarrow"):   # pandas/pyarrow: table bytes
        try:
            vers[p] = metadata.version(p)
        except metadata.PackageNotFoundError:
            vers[p] = None
    server, repo, run = (os.environ.get(k) for k in ("GITHUB_SERVER_URL", "GITHUB_REPOSITORY", "GITHUB_RUN_ID"))
    return {"commit": os.environ.get("GITHUB_SHA") or git("rev-parse", "HEAD"),
            "request_file_commit": git("log", "-1", "--format=%H", "--", "reference/era5_request.json"),
            "workflow_run_url": f"{server}/{repo}/actions/runs/{run}" if server and repo and run else None,
            "versions": vers}


class RefGH:
    """history.backfill.GH plus draft deletion (a stale draft is deleted before a refusal is recorded)."""

    def __init__(self):
        from history.backfill import GH
        self._gh = GH()

    def __getattr__(self, name):
        return getattr(self._gh, name)

    def delete_draft(self, tag: str) -> None:
        from history.backfill import sh
        if self._gh.state(tag) == "draft":
            sh("gh", "release", "delete", tag, "-y")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="D2 ERA5 reference retrieval (committed request file only)")
    ap.add_argument("--request", required=True)
    ap.add_argument("--index", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--poll-deadline-min", type=int, default=300)
    a = ap.parse_args(argv)
    key = os.environ.get("CDS_API_KEY", "")
    secrets = (key,) if key else ()
    try:
        doc = read_request(pathlib.Path(a.request))
    except (C.ReferenceError_, ValueError) as e:
        print(json.dumps({"error": redact(e, secrets)}))
        return 1
    from era5_cds import CDSClient
    from history.backfill import commit_index
    cds = CDSClient(key) if key else None
    idx = pathlib.Path(a.index)
    pol = RetryPolicy(poll_deadline_s=a.poll_deadline_min * 60)
    deps = Deps(cds=cds, gh=RefGH(), index=idx, work=pathlib.Path(a.work), run_id=a.run_id,
                persist=lambda msg: commit_index(idx, msg), today=datetime.now(timezone.utc).date(), policy=pol,
                code=_code_info(), secrets=secrets)
    deps.deadline = deps.monotonic() + pol.poll_deadline_s
    out = []
    for m in doc["months"]:
        deps.work = pathlib.Path(a.work) / m
        out.append(process_month(deps, m, doc["repeat_check"]))
    pf = deps.preflight_result
    pf_summary = None if pf is None else {"ok": pf["ok"], "reason": pf.get("reason"),
                                          "accepted_dataset_licences": len(pf.get("accepted_dataset_licences", [])),
                                          "licence_check": pf.get("licence_check")}
    print(redact(json.dumps({"run_id": a.run_id, "purpose": doc["purpose"], "preflight": pf_summary, "months": out},
                            indent=1, default=str), secrets))
    return 1 if any(o["outcome"] == "refused" for o in out) else 0


if __name__ == "__main__":
    sys.exit(main())
