"""Verified, read-only access to the immutable historical releases (VM-1.0 §17; M4.4 plan §0).

Before any file is used:
  1. the release must be published (not a draft) and immutable;
  2. the release's manifest must hash to the manifest SHA-256 recorded on the archive-index branch;
  3. every data file must hash to its manifest entry.
Any mismatch raises CensusError (tampered or unexpected input is refused). Only our own releases and the
archive-index branch are read; no weather-data service is contacted.
"""
from __future__ import annotations

import hashlib
import io
import json
import pathlib
import ssl
import subprocess
import urllib.request

import pandas as pd

from common import MODELS, NOT_INDEPENDENT, REPO, CensusError, classify_reason

GH_REPO = "gnmcool/bharat-weather-intelligence-v2"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class GitHubSource:
    """Real source: public release downloads (cached) + the archive-index branch via git."""

    def __init__(self, cache: pathlib.Path, ca: str | None = "/root/.ccr/ca-bundle.crt"):
        self.cache = cache
        cache.mkdir(parents=True, exist_ok=True)
        self.ctx = ssl.create_default_context(cafile=ca) if ca and pathlib.Path(ca).exists() else None
        subprocess.run(["git", "-C", str(REPO), "fetch", "-q", "origin", "archive-index"], check=True)
        self.index_commit = self._git("rev-parse", "origin/archive-index").strip()
        self._releases = None

    def _git(self, *a) -> str:
        return subprocess.run(["git", "-C", str(REPO), *a], check=True, capture_output=True, text=True).stdout

    def _get(self, url: str) -> bytes:
        req = urllib.request.Request(url, headers={"User-Agent": "bwi-verification-census"})
        with urllib.request.urlopen(req, context=self.ctx, timeout=300) as r:
            return r.read()

    def index_files(self, prefix: str) -> dict[str, bytes]:
        names = [n for n in self._git("ls-tree", "--name-only", f"{self.index_commit}", prefix + "/").split() if n]
        return {n: self._git("show", f"{self.index_commit}:{n}").encode() for n in names if n.endswith(".json")}

    def release(self, tag: str) -> dict:
        if self._releases is None:
            j = json.loads(self._get(f"https://api.github.com/repos/{GH_REPO}/releases?per_page=100"))
            self._releases = {x["tag_name"]: x for x in j}
        if tag not in self._releases:
            raise CensusError(f"release {tag} not found")
        return self._releases[tag]

    def asset(self, tag: str, name: str) -> bytes:
        p = self.cache / tag / name
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(self._get(f"https://github.com/{GH_REPO}/releases/download/{tag}/{name}"))
        return p.read_bytes()


def load_index(source) -> tuple[dict, list]:
    recs = {}
    for n, b in source.index_files("history/index").items():
        r = json.loads(b)
        recs[r["month"]] = r
    anns = [json.loads(b) for b in source.index_files("history/annotations").values()]
    return recs, anns


def load_month(source, rec: dict) -> dict:
    """Verify and load one monthly release. Returns tables + provenance."""
    tag, month = rec["tag"], rec["month"]
    info = source.release(tag)
    if info.get("draft") or info.get("immutable") is not True:
        raise CensusError(f"{tag}: release is not published and immutable (draft={info.get('draft')}, "
                          f"immutable={info.get('immutable')})")
    mname = f"manifest_history-{month}.json"
    mb = source.asset(tag, mname)
    if sha256_bytes(mb) != rec["manifest_sha256"]:
        raise CensusError(f"{tag}: manifest SHA-256 differs from the archive-index record (tampered or unexpected)")
    man = json.loads(mb)
    if man.get("dataset") != "historical_backfill":
        raise CensusError(f"{tag}: not a historical_backfill release (historical and prospective are never mixed)")
    files = {}
    for f in man["files"]:
        b = source.asset(tag, f["name"])
        if sha256_bytes(b) != f["sha256"]:
            raise CensusError(f"{tag}: {f['name']} SHA-256 differs from the manifest (tampered input refused)")
        files[f["kind"]] = b
    matched = pd.read_parquet(io.BytesIO(files["matched"]))
    forecasts = pd.read_parquet(io.BytesIO(files["forecasts"]))
    pairing = json.loads(files["metar_pairing"])
    # historical and prospective are never mixed; only independent models
    if (matched["dataset"] != "matched_historical").any() or matched["run_time_known"].any():
        raise CensusError(f"{tag}: rows that are not historical nominal-lead data")
    bad = set(matched["model"]) - set(MODELS)
    if bad:
        why = "; ".join(NOT_INDEPENDENT.get(m, f"{m} is not one of the independent models") for m in sorted(bad))
        raise CensusError(f"{tag}: unexpected model(s) {sorted(bad)} — {why}")
    return {"month": month, "tag": tag, "matched": matched, "forecasts": forecasts, "pairing": pairing,
            "provenance": {"tag": tag, "release_id": info.get("id"), "manifest_sha256": rec["manifest_sha256"],
                           "processing_version": man.get("processing_version"),
                           "files": {f["name"]: f["sha256"] for f in man["files"]}}}


def annotation_overrides(month_data: dict, annotations: list) -> tuple[dict, list]:
    """Forecast-row reclassifications from archive-index annotations, applied only if the annotation's manifest hash and
    row-key hash both match the verified release. Returns {(point, variable, lead, date): category}, notes."""
    over, notes = {}, []
    for a in annotations:
        if a.get("release") != month_data["tag"]:
            continue
        if a["manifest_sha256"] != month_data["provenance"]["manifest_sha256"]:
            raise CensusError(f"annotation {a['id']}: manifest hash does not match {a['release']}")
        F = month_data["forecasts"]
        r = a["reclassify"]
        sel = F[(F["model"] == a["model"]) & F["variable"].isin(a["variables"]) & ~F["complete"]
                & (F["reason"].map(classify_reason) == r["from"])]
        keys = sorted(f"{x.point_id}|{x.variable}|{x.nominal_lead_day}|{x.valid_date_ist}|{x.hours_present}"
                      for x in sel.itertuples())
        if len(sel) != r["rows"] or sha256_bytes("\n".join(keys).encode()) != a["row_keys_sha256"]:
            raise CensusError(f"annotation {a['id']}: selected rows do not match its recorded row keys")
        for x in sel.itertuples():
            over[(a["model"], x.point_id, x.variable, int(x.nominal_lead_day), x.valid_date_ist)] = r["to"]
        notes.append({"annotation": a["id"], "rows": len(sel), "from": r["from"], "to": r["to"]})
    return over, notes
