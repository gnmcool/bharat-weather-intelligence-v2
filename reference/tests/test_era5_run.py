"""End-to-end D2 driver with a fake CDS and a fake GitHub, on full-size synthetic GRIB (the fixed 36 points and area).

Covers: eligibility, request ids persisted before/after submit, resume, uncertain submission, the retry table,
the retrieval limit (no automatic third), expver refusal, structural refusal, E days, R2, publication, tampering,
no partial release, immutability, append-only archive-index provenance, secret redaction and deterministic rebuild.
"""
import hashlib
import json
from datetime import date, datetime, timezone

import pytest

from reference.tests import KEY, FakeCDS, FakeGH, flat_index, http, scan_for_secret, transport
import era5_common as C
import era5_extract as X
import era5_grib as G
import era5_run as RUN

UTC = timezone.utc
M = "2026-10"                       # a normal month (eligible from 9 Jan 2027)
V = "2026-09"                       # the validation month (R2), eligible from 9 Dec 2026
TODAY = date(2027, 1, 9)


class Env:
    def __init__(self, tmp, cds=None, gh=None, today=TODAY, run_id="run1", index=None):
        self.tmp = tmp
        self.cds = cds or FakeCDS(tmp / "cds")
        self.gh = gh or FakeGH()
        self.index = index or tmp / "index"
        self.persisted, self.sleeps, self.t = [], [], [0.0]
        self.deps = RUN.Deps(cds=self.cds, gh=self.gh, index=self.index, work=tmp / "work" / run_id, run_id=run_id,
                             persist=self.persisted.append, today=today, sleep=self._sleep,
                             monotonic=lambda: self.t[0], code={"commit": "test-commit"}, secrets=(KEY,),
                             now=lambda: f"{today.isoformat()}T12:00:00Z")
        self.deps.deadline = self.deps.policy.poll_deadline_s

    def _sleep(self, s):
        self.sleeps.append(s)
        self.t[0] += s

    def run(self, month=M, repeat_check=False):
        return RUN.process_month(self.deps, month, repeat_check)

    def again(self, run_id, today=None):
        """A later workflow run (new commit of the request file): same CDS, GitHub and archive-index."""
        return Env(self.tmp, cds=self.cds, gh=self.gh, today=today or self.deps.today, run_id=run_id, index=self.index)

    def ledger(self, month=M):
        p = self.index / "reference" / "era5" / "jobs" / f"{month}.jsonl"
        return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []

    def refusals(self):
        d = self.index / "reference" / "era5" / "refused"
        return sorted(json.loads(p.read_text())["failing_check"] for p in d.glob("*.json")) if d.exists() else []


@pytest.fixture
def env(tmp_path):
    return Env(tmp_path)


# ---------------------------------------------------------------- happy path, provenance, determinism
def test_normal_month_published_with_full_provenance(env):
    out = env.run()
    assert out["outcome"] == "published" and out["tag"] == "ref-era5-2026-10", out
    rel = env.gh.rel["ref-era5-2026-10"]
    assert not rel["draft"]
    assert sorted(rel["assets"]) == sorted([
        "era5_cds_boundary_2026-10.grib", "era5_cds_month_2026-10.grib", "era5_cds_requests_2026-10.json",
        "era5_hourly_2026-10.parquet", "era5_ist_day_2026-10.parquet", "gap_report_ref-era5-2026-10.json",
        "manifest_ref-era5-2026-10.json"])
    man = json.loads(rel["assets"]["manifest_ref-era5-2026-10.json"])
    for f in man["files"]:                                              # manifest checksums match the release
        assert hashlib.sha256(rel["assets"][f["name"]]).hexdigest() == f["sha256"]
    rq = C.build_requests(M)
    reqs = man["source"]["requests"]
    assert {r: reqs[r]["request_sha256"] for r in C.ROLES} == {r: C.request_sha256(rq[r]) for r in C.ROLES}
    assert all(reqs[r]["request_id"] for r in C.ROLES) and reqs["boundary"]["request"]["day"] == ["30"]
    assert man["source"]["cds_dataset"] == C.DATASET and man["version"]["expver"] == "0001"
    assert "retrieved 70 days after month end" in man["version"]["statement"]
    assert "does not exclude later ECMWF corrections" in man["version"]["statement"]
    assert man["licence"]["terms_accepted_on"] == "2026-09-30" and man["licence"]["terms_accepted_stated_by"] == "owner"
    assert man["licence"]["attribution"]["derived_tables"].startswith("Contains modified Copernicus")
    assert man["points"]["sha256"] == C.POINTS_SHA256 and man["points"]["area"] == C.AREA
    ss = next(p for p in man["points"]["per_point"] if p["point_id"] == "IN-11-243")
    assert (ss["node_lat"], ss["node_lon"], ss["tie_break_applied"]) == (27.25, 88.5, True)
    assert man["coverage"]["utc_stamps_used"] == ["2026-09-30T19:00:00+00:00", "2026-10-31T18:00:00+00:00"]
    assert len(man["coverage"]["utc_stamps_requested_unused"]) == 5            # 31 Oct 19-23Z
    assert man["retrieval"]["jobs"][1]["items_requested"] == 744 and man["retrieval"]["jobs"][0]["items_requested"] == 5
    assert man["repeat_check"] == {"repeat_check": False, "result": None}
    # archive-index record and ledger
    idx = json.loads((env.index / "reference/era5/index/2026-10.json").read_text())
    assert idx["tag"] == "ref-era5-2026-10" and idx["manifest_sha256"] == hashlib.sha256(
        rel["assets"]["manifest_ref-era5-2026-10.json"]).hexdigest()
    assert idx["checks"]["immutability"]["github_immutable_flag"] is True
    ev = [(e["event"], e["role"]) for e in env.ledger()]
    assert ev[:4] == [("intent", "boundary"), ("submitted", "boundary"), ("intent", "month"), ("submitted", "month")]
    assert ev[-2:] == [("closed", "boundary"), ("closed", "month")]
    assert env.cds.submits() == 2


def test_intent_persisted_before_submit_and_request_id_right_after(env):
    seen = []

    def observer(event, request):
        seen.append((len(env.ledger()), env.ledger()[-1]["event"], len(env.persisted)))
    env.cds.observer = observer
    env.run()
    assert seen[0] == (1, "intent", 1) and seen[1] == (3, "intent", 3)  # intent written *and persisted* first
    ev = env.ledger()
    assert ev[1]["event"] == "submitted" and ev[1]["request_id"].startswith("0000")


def test_deterministic_rebuild_from_released_grib(env, tmp_path):
    env.run()
    rel = env.gh.rel["ref-era5-2026-10"]["assets"]
    for role in C.ROLES:
        (tmp_path / f"{role}.grib").write_bytes(rel[f"era5_cds_{role}_2026-10.grib"])
    files = {role: G.decode(tmp_path / f"{role}.grib") for role in C.ROLES}
    X.build_tables(C.load_points(), files, M, tmp_path / "rebuilt")
    for name in ("era5_hourly_2026-10.parquet", "era5_ist_day_2026-10.parquet"):
        assert (tmp_path / "rebuilt" / name).read_bytes() == rel[name]


def test_ist_day_complete_for_every_point(env):
    env.run()
    import io
    import pyarrow.parquet as pq
    d = pq.read_table(io.BytesIO(env.gh.rel["ref-era5-2026-10"]["assets"]["era5_ist_day_2026-10.parquet"])).to_pandas()
    assert len(d) == 36 * 31 and d.reason.isna().all() and (d.hours_present == 24).all()


# ---------------------------------------------------------------- eligibility and limits
def test_before_eligibility_nothing_is_submitted(tmp_path):
    e = Env(tmp_path, today=date(2027, 1, 8))
    out = e.run()
    assert out["outcome"] == "refused" and "eligibility date 2027-01-09" in out["reason"]
    assert e.cds.calls == [] and e.ledger() == [] and e.refusals() == ["eligibility"]


def test_published_month_is_never_redone(env):
    env.run()
    n = len(env.cds.calls)
    out = env.again("run2").run()
    assert out["outcome"] == "done" and len(env.cds.calls) == n


def test_missing_credentials_refused_before_any_ledger_entry(tmp_path):
    e = Env(tmp_path)
    e.deps.cds = None
    out = e.run()
    assert out["outcome"] == "refused" and e.ledger() == [] and e.refusals() == ["credentials"]


# ---------------------------------------------------------------- final data (expver) and structure
def test_era5t_in_month_file_refuses_and_publishes_nothing(env):
    env.cds.grib_kwargs["month"] = {"expver": lambda t: "0005" if t.day >= 29 else "0001"}
    out = env.run()
    assert out["outcome"] == "refused" and out["check"] == "expver"
    assert env.gh.rel == {} and env.refusals() == ["expver"]
    assert {e["outcome"] for e in env.ledger() if e["event"] == "closed"} == {"refused"}


def test_era5t_in_boundary_file_refuses(env):
    env.cds.grib_kwargs["boundary"] = {"expver": lambda t: "0005"}
    assert env.run()["check"] == "expver" and env.gh.rel == {}


def test_missing_stamp_refuses(env):
    env.cds.grib_kwargs["month"] = {"drop": [datetime(2026, 10, 7, 11, tzinfo=UTC)]}
    out = env.run()
    assert out["check"] == "structure" and "[stamps]" in out["reason"] and env.gh.rel == {}


def test_missing_hour_publishes_E_day(env):
    idx = flat_index(28.75, 77.0)                                     # Delhi node
    env.cds.grib_kwargs["month"] = {"missing": {datetime(2026, 10, 15, 2, tzinfo=UTC): [idx]}}
    assert env.run()["outcome"] == "published"
    gap = json.loads(env.gh.rel["ref-era5-2026-10"]["assets"]["gap_report_ref-era5-2026-10.json"])
    assert gap["e_days"] == [{"point_id": "IN-07-delhi", "ist_date": "2026-10-15", "hours_present": 23,
                              "reason": "ERA5 hours missing: 23 of 24"}]
    idx_rec = json.loads((env.index / "reference/era5/index/2026-10.json").read_text())
    assert idx_rec["e_days"] == gap["e_days"]


# ---------------------------------------------------------------- submission, resume, retries
def test_timeout_then_resume_by_request_id_without_resubmission(env):
    env.cds.status_script = {"boundary": ["accepted"] * 400, "month": ["running"] * 400}
    env.deps.deadline = 3000
    out = env.run()
    assert out["outcome"] == "pending" and env.cds.submits() == 2 and env.refusals() == []
    assert env.sleeps[:5] == [60, 120, 240, 480, 600]                   # queued polling cadence, capped at 600 s
    later = env.again("run2")
    for j in env.cds.jobs.values():
        j["status"] = []
    out = later.run()
    assert out["outcome"] == "published" and env.cds.submits() == 2   # resumed, nothing resubmitted


@pytest.mark.parametrize("err,check", [(transport(), "submission uncertain"), (http(503), "submission uncertain"),
                                       (http(502), "submission uncertain"), (http(400), "submit 4xx"),
                                       (http(403), "submit 4xx"), (http(429), "submission uncertain")])
def test_submit_errors(env, err, check):
    env.cds.submit_errors = [err]
    out = env.run()
    assert out["outcome"] == "refused" and out["check"] == check
    assert env.cds.submits() == 1                                      # the month job was never submitted
    assert env.gh.rel == {}


def test_uncertain_submission_never_resubmitted_and_no_third_retrieval(env):
    env.cds.submit_errors = [transport()]
    assert env.run()["check"] == "submission uncertain"
    same = env.run()                                                   # same run again: no second retrieval
    assert same["outcome"] in ("stopped", "refused") and env.cds.submits() == 1
    r2 = env.again("run2")                                             # new committed request: retrieval 2
    r2.cds.submit_errors = [http(403)]
    assert r2.run()["outcome"] == "refused" and env.cds.submits() == 2
    r3 = env.again("run3")
    out = r3.run()
    assert out["outcome"] == "refused" and "no automatic third retrieval" in out["reason"]
    assert env.cds.submits() == 2


def test_intent_without_request_id_from_an_earlier_run_is_refused(env):
    lg = RUN.Ledger(env.index, M, "crashed-run")
    lg.append("intent", 1, "boundary", request_sha256="x", items=5)      # e.g. the runner died during submit
    out = env.again("run2").run()
    assert out["outcome"] == "refused" and out["check"] == "submission uncertain" and env.cds.submits() == 0


def test_poll_transient_errors_within_cap(env):
    env.cds.status_script = {"boundary": [transport(), http(503)]}
    assert env.run()["outcome"] == "published"
    assert env.sleeps[:2] == [30, 60]


def test_poll_429_waits_120(env):
    env.cds.status_script = {"boundary": [http(429)]}
    assert env.run()["outcome"] == "published" and env.sleeps[0] == 120


def test_poll_transient_errors_beyond_cap_leave_the_job_pending(env):
    env.cds.status_script = {"boundary": [transport()] * 4}
    out = env.run()
    assert out["outcome"] == "pending" and env.sleeps == [30, 60, 120] and env.cds.submits() == 2
    assert env.refusals() == []


def test_poll_404_refuses(env):
    env.cds.status_script = {"month": [http(404)]}
    assert env.run()["check"] == "poll 4xx" and env.cds.submits() == 2


def test_failed_job_refuses(env):
    env.cds.status_script = {"month": ["running", "failed"]}
    out = env.run()
    assert out["check"] == "job failed" and env.gh.rel == {}


def test_malformed_download_redownloaded_same_result(env):
    env.cds.download_script = {"month": ["truncate", "garbage"]}
    assert env.run()["outcome"] == "published"
    assert sum(1 for c in env.cds.calls if c[0] == "download") == 1 + 3 and env.cds.submits() == 2  # boundary once, month 3x


def test_malformed_download_three_times_refuses(env):
    env.cds.download_script = {"month": ["truncate"] * 3}
    out = env.run()
    assert out["check"] == "malformed download" and env.cds.submits() == 2 and env.gh.rel == {}


def test_download_expired_refuses_without_resubmission(env):
    env.cds.download_script = {"month": [http(404, "result expired")]}
    assert env.run()["check"] == "download 4xx" and env.cds.submits() == 2


def test_download_transient_beyond_cap_is_pending(env):
    env.cds.download_script = {"boundary": [transport()] * 4}
    assert env.run()["outcome"] == "pending" and env.sleeps == [30, 60, 120]


# ---------------------------------------------------------------- publication: no partial release, tampering, immutability
def test_failed_upload_leaves_no_release_and_resumes_without_resubmission(env):
    env.gh.fail_upload.add("era5_ist_day_2026-10.parquet")
    out = env.run()
    assert out["outcome"] == "refused" and out["check"] == "publication"
    assert "ref-era5-2026-10" not in env.gh.rel and env.gh.deleted == ["ref-era5-2026-10"]   # draft deleted
    env.gh.fail_upload.clear()
    later = env.again("run2")
    assert later.run()["outcome"] == "published" and env.cds.submits() == 2               # re-download by id


def test_corrupted_upload_is_detected_and_not_published(env):
    env.gh.corrupt_on_upload.add("era5_cds_month_2026-10.grib")
    out = env.run()
    assert out["check"] == "publication" and "ref-era5-2026-10" not in env.gh.rel


def test_published_release_is_immutable(env):
    env.run()
    rel = env.gh.rel["ref-era5-2026-10"]
    with pytest.raises(RuntimeError, match="immutable"):
        env.gh.upload("ref-era5-2026-10", env.tmp / "work" / "run1" / "stage" / "manifest_ref-era5-2026-10.json")
    with pytest.raises(RuntimeError, match="immutable"):
        env.gh.delete_asset("ref-era5-2026-10", "era5_cds_month_2026-10.grib")
    idx = json.loads((env.index / "reference/era5/index/2026-10.json").read_text())
    imm = idx["checks"]["immutability"]
    assert imm["add_new_asset"]["rejected"] and imm["delete_asset"]["rejected"] and len(rel["assets"]) == 7


def test_archive_index_records_never_overwritten(env):
    env.run()
    with pytest.raises(C.ReferenceError_, match="never overwritten"):
        RUN.write_new(env.index / "reference/era5/index/2026-10.json", {})
    before = (env.index / "reference/era5/jobs/2026-10.jsonl").read_bytes()
    env.again("run2").run()
    assert (env.index / "reference/era5/jobs/2026-10.jsonl").read_bytes().startswith(before)


def test_failed_intent_persist_means_nothing_is_submitted(env):
    def persist(msg):
        raise RuntimeError("could not push index")
    env.deps.persist = persist
    with pytest.raises(RuntimeError, match="could not push index"):
        env.run()
    assert env.cds.submits() == 0                                     # the submit call is never reached


def test_tampered_stage_file_is_not_published(env, monkeypatch):
    real = RUN.build_stage

    def tampering(*a, **k):
        stage = real(*a, **k)
        (stage / "era5_ist_day_2026-10.parquet").write_bytes(b"tampered")
        return stage
    monkeypatch.setattr(RUN, "build_stage", tampering)
    out = env.run()
    assert out["outcome"] == "refused" and out["check"] == "publication" and "checksum" in out["reason"]
    assert env.gh.rel == {}


# ---------------------------------------------------------------- R2 (validation month)
def test_validation_month_r2_pass_publishes_first_retrieval(tmp_path):
    e = Env(tmp_path, today=date(2026, 12, 9))
    out = e.run(V, True)
    assert out["outcome"] == "published" and out["repeat_check"] == "reference/era5/validation/2026-09_repeat.json"
    assert e.cds.submits() == 4
    val = json.loads((e.index / "reference/era5/validation/2026-09_repeat.json").read_text())
    assert val["passed"] and val["values_identical_after_decoding"]
    man = json.loads(e.gh.rel["ref-era5-2026-09"]["assets"]["manifest_ref-era5-2026-09.json"])
    assert man["retrieval"]["retrieval_number"] == 1
    assert man["repeat_check"] == {"repeat_check": True, "result": "reference/era5/validation/2026-09_repeat.json"}
    ids = {j["request_id"] for j in man["retrieval"]["jobs"]}
    r1 = {e_["request_id"] for e_ in e.ledger(V) if e_["event"] == "submitted" and e_["retrieval"] == 1}
    assert ids == r1
    outcomes = {(x["retrieval"], x["outcome"]) for x in e.ledger(V) if x["event"] == "closed"}
    assert outcomes == {(1, "published"), (2, "evidence")}
    # afterwards: done, never a third retrieval
    assert e.again("run2").run(V, True)["outcome"] == "done" and e.cds.submits() == 4


def test_validation_month_r2_fail_is_not_published(tmp_path):
    e = Env(tmp_path, today=date(2026, 12, 9))
    idx = flat_index(28.75, 77.0)

    def perturb(t, v):
        if t == datetime(2026, 9, 10, 3, tzinfo=UTC):
            v[idx] += 0.002
        return v
    e.cds.grib_kwargs[(2, "month")] = {"perturb": perturb}
    out = e.run(V, True)
    assert out["outcome"] == "refused" and out["check"] == "R2" and e.gh.rel == {}
    val = json.loads((e.index / "reference/era5/validation/2026-09_repeat.json").read_text())
    assert not val["passed"] and val["exceedances"]["hourly"][0][0] == "IN-07-delhi"
    later = e.again("run2").run(V, True)
    assert later["outcome"] == "refused" and e.cds.submits() == 4            # no third retrieval


def test_r2_flag_rules(tmp_path):
    e = Env(tmp_path, today=date(2027, 1, 9))
    assert e.run(V, False)["check"] == "retrieval limit" and e.cds.calls == []
    assert e.run(M, True)["check"] == "retrieval limit" and e.cds.calls == []


def test_validation_month_pending_second_retrieval(tmp_path):
    e = Env(tmp_path, today=date(2026, 12, 9))
    calls = {"n": 0}
    orig = e.cds.status

    def status(rid):
        job = e.cds.jobs[rid]
        if job["nth"] == 2 and calls["n"] < 50:
            calls["n"] += 1
            return "running"
        return orig(rid)
    e.cds.status = status
    e.deps.deadline = 2000
    assert e.run(V, True)["outcome"] == "pending" and e.cds.submits() == 4
    later = e.again("run2")
    later.cds.status = orig
    out = later.run(V, True)
    assert out["outcome"] == "published" and e.cds.submits() == 4


# ---------------------------------------------------------------- secret never recorded
def test_secret_never_written_anywhere(env, capsys):
    env.cds.status_script = {"boundary": [transport(), http(503)]}
    env.run()
    e2 = Env(env.tmp / "b")
    e2.cds.submit_errors = [transport()]
    e2.run()
    e3 = Env(env.tmp / "c")
    e3.cds.download_script = {"month": [http(404)]}
    e3.run()
    assert scan_for_secret(env.index, env.tmp / "work", e2.index, e3.index, e2.tmp / "work", e3.tmp / "work") == []
    for rel in list(env.gh.rel.values()):
        assert all(KEY.encode() not in b for b in rel["assets"].values())
    assert KEY not in capsys.readouterr().out


def test_cli_redacts_and_validates_request_file(tmp_path, capsys, monkeypatch):
    bad = tmp_path / "req.json"
    bad.write_text(json.dumps({"months": ["2026-13"], "purpose": "x", "repeat_check": False}))
    monkeypatch.setenv("CDS_API_KEY", KEY)
    rc = RUN.main(["--request", str(bad), "--index", str(tmp_path), "--work", str(tmp_path / "w"), "--run-id", "1"])
    out = capsys.readouterr().out
    assert rc == 1 and "invalid month" in out and KEY not in out
    for doc in ({"months": [], "purpose": "x", "repeat_check": False}, {"months": ["2026-10"], "repeat_check": False},
                {"months": ["2026-10"], "purpose": "x", "repeat_check": "yes"},
                {"months": ["2026-10"], "purpose": "x", "repeat_check": False, "force": True}):
        bad.write_text(json.dumps(doc))
        with pytest.raises(C.ReferenceError_):
            RUN.read_request(bad)
