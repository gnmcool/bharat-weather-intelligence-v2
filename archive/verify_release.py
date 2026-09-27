"""Verify a release against the staged manifest; after publication, also prove it cannot be modified.

--published adds three deliberate modification attempts, each of which MUST fail:
  add a new asset · overwrite an existing asset (--clobber) · delete an existing asset
and reads GitHub's `immutable` flag for the release. Any successful modification fails this script.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import tempfile

from common import sha256, write_json


def sh(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(list(args), capture_output=True, text=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--stage", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--published", action="store_true")
    a = ap.parse_args()
    stage = pathlib.Path(a.stage)
    man = json.loads(next(stage.glob("manifest_*.json")).read_text())
    res = {"tag": a.tag, "published": a.published, "checksums": {}, "immutability": {}}
    ok = True
    with tempfile.TemporaryDirectory() as d:
        r = sh("gh", "release", "download", a.tag, "-D", d)
        if r.returncode:
            print(r.stderr, file=sys.stderr)
            return 1
        for f in man["files"]:
            got = sha256(pathlib.Path(d) / f["name"])
            res["checksums"][f["name"]] = {"manifest": f["sha256"], "downloaded": got, "match": got == f["sha256"]}
            ok &= got == f["sha256"]
        for extra in ("manifest", "gap_report"):
            local = next(stage.glob(f"{extra}_*.json"))
            same = sha256(local) == sha256(pathlib.Path(d) / local.name)
            res["checksums"][local.name] = {"match": same}
            ok &= same
    if a.published:
        import os
        info = json.loads(sh("gh", "api", f"repos/{os.environ.get('GITHUB_REPOSITORY', 'gnmcool/bharat-weather-intelligence-v2')}/releases/tags/{a.tag}").stdout or "{}")
        res["immutability"]["draft"] = info.get("draft")
        res["immutability"]["github_immutable_flag"] = info.get("immutable")
        ok &= info.get("immutable") is True
        probe = pathlib.Path(tempfile.gettempdir()) / "immutability_probe.txt"
        probe.write_text("this upload must be rejected\n")
        target = next(f["name"] for f in man["files"] if f["kind"] == "forecasts")
        tampered = pathlib.Path(tempfile.gettempdir()) / target
        tampered.write_bytes(b"tampered")
        attempts = {
            "add_new_asset": sh("gh", "release", "upload", a.tag, str(probe)),
            "overwrite_asset": sh("gh", "release", "upload", a.tag, str(tampered), "--clobber"),
            "delete_asset": sh("gh", "release", "delete-asset", a.tag, target, "-y"),
        }
        for k, r in attempts.items():
            rejected = r.returncode != 0
            res["immutability"][k] = {"rejected": rejected, "message": (r.stderr or r.stdout).strip()[:300]}
            ok &= rejected
        # after the attempts, the published forecasts file must still match its manifest checksum
        with tempfile.TemporaryDirectory() as d:
            sh("gh", "release", "download", a.tag, "-p", target, "-D", d)
            want = next(f["sha256"] for f in man["files"] if f["name"] == target)
            still = (pathlib.Path(d) / target).exists() and sha256(pathlib.Path(d) / target) == want
            res["immutability"]["unchanged_after_attempts"] = still
            ok &= still
    res["ok"] = bool(ok)
    write_json(pathlib.Path(a.out), res)
    print(json.dumps(res, indent=1)[:3000])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
