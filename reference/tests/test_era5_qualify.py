"""The 2025-01 qualification path: allow-list, separation from the official D2 paths, R1/R2, four-job cap, labels.

Offline only: fake CDS, a temporary git worktree on branch era5-qualification. No GitHub client exists in this path.
"""
import hashlib
import json
import pathlib
import subprocess
import sys
from datetime import date

import pytest

from reference.tests import KEY, FakeCDS, http, scan_for_secret, transport
import era5_common as C
import era5_qualify as Q
import era5_run as RUN

LABEL = "QUALIFICATION — not a D2 reference; never used in M4.4 metrics."
REPO = pathlib.Path(__file__).resolve().parents[2]


def git_repo(path: pathlib.Path, branch: str) -> pathlib.Path:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", "-b", branch, str(path)], check=True)
    return path


class QEnv:
    def __init__(self, tmp, cds=None, run_id="q1", index=None, today=date(2026, 10, 1)):
        self.tmp = tmp
        self.cds = cds or FakeCDS(tmp / "cds")
        self.index = index or git_repo(tmp / "qidx", Q.QUAL_BRANCH)
        self.persisted, self.sleeps, self.t = [], [], [0.0]
        self.deps = RUN.Deps(cds=self.cds, gh=None, index=self.index, work=tmp / "work" / run_id, run_id=run_id,
                             persist=self.persisted.append, today=today, sleep=self._sleep,
                             monotonic=lambda: self.t[0], code={"commit": "test"}, secrets=(KEY,),
                             now=lambda: f"{today.isoformat()}T12:00:00Z")
        self.deps.deadline = self.deps.policy.poll_deadline_s

    def _sleep(self, s):
        self.sleeps.append(s)
        self.t[0] += s

    def run(self, month="2025-01"):
        return Q.qualify(self.deps, month)

    def again(self, run_id):
        return QEnv(self.tmp, cds=self.cds, run_id=run_id, index=self.index)

    def ledger(self):
        p = self.index / "qualification" / "era5" / "jobs" / "2025-01.jsonl"
        return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []


@pytest.fixture
def q(tmp_path):
    return QEnv(tmp_path)


# ---------------------------------------------------------------- allow-list
def test_only_2025_01_is_allowed(tmp_path):
    assert Q.ALLOWED_MONTHS == ("2025-01",)
    Q.check_month("2025-01")
    for m in ("2026-09", "2026-10", "2025-02", "2024-12", "2027-01", "2025-1"):
        with pytest.raises(Q.QualificationRefused):
            Q.check_month(m)


@pytest.mark.parametrize("month", ["2026-09", "2026-10", "2025-02"])
def test_other_months_refused_before_any_cds_call(q, month):
    with pytest.raises(Q.QualificationRefused, match="allow-list"):
        q.run(month)
    assert q.cds.calls == [] and q.ledger() == [] and q.persisted == []


def test_request_file_validation(tmp_path):
    f = tmp_path / "r.json"
    f.write_text(json.dumps({"month": "2025-01", "purpose": "pipeline qualification"}))
    assert Q.read_request(f)["month"] == "2025-01"
    for doc in ({"month": "2026-09", "purpose": "x"}, {"month": "2025-01"},
                {"month": "2025-01", "purpose": "x", "repeat_check": False}, {"months": ["2025-01"], "purpose": "x"}):
        f.write_text(json.dumps(doc))
        with pytest.raises(Q.QualificationRefused):
            Q.read_request(f)


# ---------------------------------------------------------------- structural separation from the official D2 paths
@pytest.mark.parametrize("branch", ["archive-index", "main", "m4-history", "other"])
def test_refuses_any_index_branch_but_era5_qualification(tmp_path, branch):
    e = QEnv(tmp_path, index=git_repo(tmp_path / "idx", branch))
    with pytest.raises(Q.QualificationRefused, match="era5-qualification"):
        e.run()
    assert e.cds.calls == []


def test_refuses_non_git_index_and_official_layout(tmp_path):
    e = QEnv(tmp_path, index=tmp_path / "plain")
    (tmp_path / "plain").mkdir()
    with pytest.raises(Q.QualificationRefused):
        e.run()
    e2 = QEnv(tmp_path / "b")
    (e2.index / "reference" / "era5").mkdir(parents=True)
    with pytest.raises(Q.QualificationRefused, match="official D2 layout"):
        e2.run()
    assert e.cds.calls == [] and e2.cds.calls == []


def test_refuses_when_a_release_client_is_supplied(q):
    q.deps.gh = object()
    with pytest.raises(Q.QualificationRefused, match="no publication"):
        q.run()


def test_no_publication_code_in_the_qualification_module():
    """Structural: the module references no publication / official-index function and no official request path."""
    import ast
    tree = ast.parse((REPO / "reference" / "era5_qualify.py").read_text())
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | \
            {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    for forbidden in ("publish_month", "publish", "commit_index", "record_refusal", "_idx_path", "write_new",
                      "process_month", "RefGH", "backfill"):
        assert forbidden not in names, forbidden
    consts = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    assert not any("era5_request.json" in c for c in consts)
    assert not any(c.startswith("reference/era5/") for c in consts)
    assert Q.QUAL_PREFIX == ("qualification", "era5")


def test_qualification_does_not_import_the_publication_module(tmp_path):
    code = ("import sys; sys.path.insert(0, 'reference'); sys.path.insert(0, '.');"
            "import era5_qualify; print('history.backfill' in sys.modules)")
    r = subprocess.run([sys.executable, "-c", code], cwd=REPO, capture_output=True, text=True)
    assert r.stdout.strip() == "False", r.stderr


# ---------------------------------------------------------------- the qualification run
def test_full_qualification_r1_r2_four_jobs_labelled(q):
    out = q.run()
    assert out["outcome"] == "passed" and out["label"] == LABEL, out
    assert q.cds.submits() == 4                                     # R1 (2) + R2 (2)
    kinds = [c[0] for c in q.cds.calls]
    assert kinds[:2] == ["auth", "licences"]                        # preflight before any submit
    ev = q.ledger()
    assert {(x["retrieval"], x["role"]) for x in ev if x["event"] == "intent"} == \
        {(1, "boundary"), (1, "month"), (2, "boundary"), (2, "month")}
    assert all(x["outcome"] == "evidence" for x in ev if x["event"] == "closed")
    # requests: the production two-request design, with the year boundary
    jobs = list(q.cds.jobs.values())
    b = next(j["request"] for j in jobs if j["role"] == "boundary")
    m = next(j["request"] for j in jobs if j["role"] == "month")
    assert (b["year"], b["month"], b["day"], b["time"]) == (["2024"], ["12"], ["31"],
                                                             ["19:00", "20:00", "21:00", "22:00", "23:00"])
    assert (m["year"], m["month"], len(m["day"]), len(m["time"])) == (["2025"], ["01"], 31, 24)
    assert m == C.build_requests("2025-01")["month"]
    # result record (qualification branch only) and labels
    rec = json.loads((q.index / "qualification/era5/results/2025-01.json").read_text())
    assert rec["QUALIFICATION_NOTICE"] == LABEL and rec["official"] is False and rec["passed"]
    assert rec["expver"] == {"boundary": {"0001": 5}, "month": {"0001": 744}}
    assert rec["ist_days"] == {"rows": 36 * 31, "complete": 36 * 31, "E": 0, "G": 0}
    assert rec["r2"]["passed"] and rec["requests"]["month"]["items"] == 744
    outdir = pathlib.Path(out["output_dir"])
    assert outdir.name == "QUALIFICATION_era5_2025-01"
    assert LABEL in (outdir / "QUALIFICATION_README.txt").read_text()
    man = json.loads((outdir / "qualification_manifest_era5_2025-01.json").read_text())
    assert man["QUALIFICATION_NOTICE"] == LABEL and man["official"] is False
    assert man["dataset"] == "era5_d2_pipeline_qualification_not_official"
    assert set(rec["output_files_sha256"]) == {p.name for p in outdir.iterdir()}


def test_nothing_written_to_official_paths(q):
    q.run()
    assert not (q.index / "reference").exists()                     # never reference/era5/...
    official_index = REPO / "reference" / "era5_request.json"
    assert not official_index.exists()
    written = {str(p.relative_to(q.index)) for p in q.index.rglob("*") if p.is_file() and ".git" not in p.parts}
    assert written and all(w.startswith("qualification/era5/") for w in written)


def test_completed_qualification_makes_no_further_cds_calls(q):
    q.run()
    n = len(q.cds.calls)
    assert q.again("q2").run()["outcome"] == "done" and len(q.cds.calls) == n


def test_r2_mismatch_is_reported_as_failed(tmp_path):
    from reference.tests import flat_index
    from datetime import datetime, timezone
    e = QEnv(tmp_path)
    idx = flat_index(28.75, 77.0)

    def perturb(t, v):
        if t == datetime(2025, 1, 10, 3, tzinfo=timezone.utc):
            v[idx] += 0.002
        return v
    e.cds.grib_kwargs[(2, "month")] = {"perturb": perturb}
    out = e.run()
    assert out["outcome"] == "failed" and e.cds.submits() == 4
    rec = json.loads((e.index / "qualification/era5/results/2025-01.json").read_text())
    assert rec["passed"] is False and rec["r2"]["exceedances"]["hourly"][0][0] == "IN-07-delhi"
    assert e.again("q2").run()["outcome"] == "done" and e.cds.submits() == 4   # no further jobs


def test_era5t_refused_and_no_further_jobs(tmp_path):
    e = QEnv(tmp_path)
    e.cds.grib_kwargs["month"] = {"expver": lambda t: "0005"}
    out = e.run()
    assert out["outcome"] == "refused" and out["check"] == "expver" and e.cds.submits() == 2
    assert e.again("q2").run()["outcome"] == "refused" and e.cds.submits() == 2   # never a retry


def test_four_job_cap_holds(tmp_path):
    e = QEnv(tmp_path)
    lg = Q.QualLedger(e.index, "2025-01", "old")
    for r in (1, 2):
        for role in C.ROLES:
            lg.append("intent", r, role)
            lg.append("submitted", r, role, request_id=f"x{r}{role}")
    e.cds.jobs.update({f"x{r}{role}": {"request": C.build_requests("2025-01")[role], "role": role, "nth": r,
                                        "status": [], "download": []} for r in (1, 2) for role in C.ROLES})
    e.run()
    assert e.cds.submits() == 0                                     # all four already exist: resume only
    assert Q.QualLedger(e.index, "2025-01", "x").cds_jobs_started() == 4


def test_pending_then_resume_without_resubmission(tmp_path):
    e = QEnv(tmp_path)
    e.cds.status_script = {"month": ["running"] * 400}
    e.deps.deadline = 2000
    assert e.run()["outcome"] == "pending" and e.cds.submits() == 2
    e.cds.status_script = {}
    for j in e.cds.jobs.values():
        j["status"] = []
    assert e.again("q2").run()["outcome"] == "passed" and e.cds.submits() == 4   # R1 resumed by id, then R2


def test_failed_preflight_writes_no_ledger_and_uses_no_job(tmp_path):
    e = QEnv(tmp_path)
    e.cds.auth_errors = [http(401, "bad token")]
    out = e.run()
    assert out["outcome"] == "refused" and out["check"] == "credentials"
    assert e.cds.submits() == 0 and e.ledger() == []


# ---------------------------------------------------------------- secret
def test_secret_never_in_outputs(tmp_path, capsys):
    envs = []
    for k, setup in enumerate([lambda c: None, lambda c: setattr(c, "submit_errors", [transport()]),
                               lambda c: setattr(c, "auth_errors", [http(403, "denied")]),
                               lambda c: c.download_script.update({"month": [http(404)]})]):
        e = QEnv(tmp_path / f"e{k}")
        setup(e.cds)
        out = e.run()
        assert KEY not in json.dumps(out, default=str)
        envs.append(e)
    roots = [x.index for x in envs] + [x.tmp / "work" for x in envs if (x.tmp / "work").exists()]
    assert scan_for_secret(*roots) == []
    assert KEY not in capsys.readouterr().out


def test_cli_refuses_wrong_month_and_redacts(tmp_path, capsys, monkeypatch):
    req = tmp_path / "r.json"
    req.write_text(json.dumps({"month": "2026-09", "purpose": "x"}))
    monkeypatch.setenv("CDS_API_KEY", KEY)
    idx = git_repo(tmp_path / "qi", Q.QUAL_BRANCH)
    rc = Q.main(["--request", str(req), "--index", str(idx), "--work", str(tmp_path / "w"), "--run-id", "1"])
    out = capsys.readouterr().out
    assert rc == 1 and "allow-list" in out and LABEL in out and KEY not in out


# ---------------------------------------------------------------- hardening: names, commit messages, reproducibility
def test_output_names_are_qualification_only(q):
    out = pathlib.Path(q.run()["output_dir"])
    names = sorted(p.name for p in out.iterdir())
    assert "qualification_manifest_era5_2025-01.json" in names and "qualification_gap_report_era5_2025-01.json" in names
    assert not any(n.startswith(("manifest_ref-era5", "gap_report_ref-era5")) for n in names)   # no official names
    man = json.loads((out / "qualification_manifest_era5_2025-01.json").read_text())
    assert {f["name"] for f in man["files"]} <= set(names)                       # manifest lists the renamed files
    for f in man["files"]:
        assert hashlib.sha256((out / f["name"]).read_bytes()).hexdigest() == f["sha256"]
    assert man["dataset"] != "era5_reference_supplement" and "qualification" in man["dataset"]
    assert man["official"] is False and man["QUALIFICATION_NOTICE"] == LABEL
    rec = json.loads((q.index / "qualification/era5/results/2025-01.json").read_text())
    assert set(rec["output_files_sha256"]) == set(names)


def test_commit_messages_say_qualification(q):
    q.run()
    assert q.persisted and all(m.startswith("qualification/era5:") for m in q.persisted), q.persisted[:3]
    assert not any("reference/era5" in m for m in q.persisted)


def test_production_ledger_messages_unchanged(tmp_path):
    msgs = []
    from era5_ledger import Ledger
    Ledger(tmp_path, "2026-09", "r", persist=msgs.append).append("intent", 1, "boundary")
    assert msgs == ["reference/era5: 2026-09 r1 boundary intent (run r)"]       # official D2 wording untouched


def test_tables_rebuild_byte_identically_from_output_grib(q, tmp_path):
    """B17 within the pinned environment: tables re-derived from the output GRIB files are byte-identical."""
    import era5_extract as X
    import era5_grib as G
    out = pathlib.Path(q.run()["output_dir"])
    files = {r: G.decode(out / f"era5_cds_{r}_2025-01.grib") for r in C.ROLES}
    X.build_tables(C.load_points(), files, "2025-01", tmp_path / "rebuilt")
    for n in ("era5_hourly_2025-01.parquet", "era5_ist_day_2025-01.parquet"):
        assert (tmp_path / "rebuilt" / n).read_bytes() == (out / n).read_bytes()


def test_pandas_pyarrow_pinned_and_recorded():
    from importlib import metadata
    req = (REPO / "reference" / "requirements.txt").read_text()
    pins = dict(l.split("==") for l in req.splitlines() if "==" in l and not l.startswith("#"))
    assert pins["pandas"] == "3.0.6" and pins["pyarrow"] == "25.0.1"
    assert metadata.version("pandas") == pins["pandas"] and metadata.version("pyarrow") == pins["pyarrow"]
    vers = RUN._code_info()["versions"]
    assert vers["pandas"] == "3.0.6" and vers["pyarrow"] == "25.0.1"
