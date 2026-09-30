"""Run the M4.4-A Gate 1 census (counts only).

  python verification/run_census.py --out DIR [--cache DIR]

Reads only the immutable history-YYYY-MM releases listed in the archive-index branch (verified; tampered input is
refused) and the recorded annotations. Writes census_cells.{parquet,csv}, census_exclusions.csv, census_run.json and
coverage_report.md to --out. Deterministic: the same inputs give byte-identical census tables.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
from datetime import datetime, timezone

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from census import census, exclusions, pairs_for_month  # noqa: E402
from common import (CENSUS_VERSION, EXPERIMENTS, METHODOLOGY_VERSION, MODELS, REPO, CensusError)  # noqa: E402
from inputs import GitHubSource, annotation_overrides, load_index, load_month  # noqa: E402


def run(source, out: pathlib.Path, months: list[str] | None = None) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    recs, anns = load_index(source)
    months = months or sorted(recs)
    if not months:
        raise CensusError("no published months in the archive index")
    parts, prov, ann_notes = [], [], []
    for m in months:
        md = load_month(source, recs[m])
        over, notes = annotation_overrides(md, anns)
        ann_notes += [{"month": m, **n} for n in notes]
        parts.append(pairs_for_month(md, over))
        prov.append(md["provenance"])
    P = pd.concat(parts, ignore_index=True)
    C = census(P)
    X = exclusions(P)
    C.to_parquet(out / "census_cells.parquet", index=False)
    C.to_csv(out / "census_cells.csv", index=False)
    X.to_csv(out / "census_exclusions.csv", index=False)
    h = {n: hashlib.sha256((out / n).read_bytes()).hexdigest()
         for n in ("census_cells.csv", "census_exclusions.csv")}
    run_rec = {
        "census_version": CENSUS_VERSION, "methodology_version": METHODOLOGY_VERSION, "gate": "M4.4-A census (counts only)",
        "metrics_computed": "none", "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "code_commit": _commit(), "archive_index_commit": getattr(source, "index_commit", None),
        "experiments": {k: {**v, "variables": list(v["variables"])} for k, v in EXPERIMENTS.items()},
        "models": list(MODELS), "months": months, "releases": prov, "annotations_applied": ann_notes,
        "result_sha256": h,
        "totals": {e: {"pairs": int((P["experiment"] == e).sum()),
                       "eligible": int(((P["experiment"] == e) & P["eligible"]).sum())} for e in EXPERIMENTS},
    }
    (out / "census_run.json").write_text(json.dumps(run_rec, indent=1, default=str) + "\n")
    (out / "coverage_report.md").write_text(report(C, X, run_rec))
    return run_rec


def _commit() -> str:
    try:
        return subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def report(C: pd.DataFrame, X: pd.DataFrame, rec: dict) -> str:
    L = [f"# M4.4-A census {rec['census_version']} (counts only) — {rec['methodology_version']}", "",
         f"Months {rec['months'][0]} … {rec['months'][-1]} ({len(rec['months'])} releases); code {rec['code_commit'][:7]}; "
         f"archive-index {str(rec['archive_index_commit'])[:7]}. **No metric was computed.**", ""]
    L += ["## Totals", "", "| Experiment | Pairs | Eligible | Excluded |", "| --- | --- | --- | --- |"]
    for e, t in rec["totals"].items():
        L.append(f"| {e} {EXPERIMENTS[e]['label']} | {t['pairs']:,} | {t['eligible']:,} | {t['pairs'] - t['eligible']:,} |")
    L += ["", "## Exclusions by category (all leads)", "", "| Experiment | Model | Variable | " +
          " | ".join("ABCDEFG") + " |", "| --- | --- | --- |" + " --- |" * 7]
    t = X.groupby(["experiment", "model", "variable", "reason"])["n_excluded"].sum().unstack(fill_value=0)
    for (e, m, v), r in t.iterrows():
        L.append(f"| {e} | {m} | {v} | " + " | ".join(f"{int(r.get(c, 0)):,}" for c in "ABCDEFG") + " |")
    L += ["", "## Both sides unavailable (primary reason D > C > B > A > E/F/G; the other side's reason is kept)", "",
          "| Experiment | Primary (forecast) | Reference category | Pairs |", "| --- | --- | --- | --- |"]
    b = X[(X["forecast_category"] != "none") & (X["reference_category"] != "none")]
    for (e, f, r), n in b.groupby(["experiment", "forecast_category", "reference_category"])["n_excluded"].sum().items():
        L.append(f"| {e} | {f} | {r} | {int(n):,} |")
    L += ["", "## Cells meeting the publication floor (single-model)", "",
          "| Experiment | Slice type | Cells | Meets floor | Insufficient sample |", "| --- | --- | --- | --- | --- |"]
    S = C[C["comparison"] == "single-model"]
    for (e, g), d in S.groupby(["experiment", "geo_slice_type"]):
        L.append(f"| {e} | {g} | {len(d)} | {int((d['status'] == 'meets floor').sum())} | "
                 f"{int((d['status'] == 'insufficient sample').sum())} |")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--cache", default="/tmp/claude-0/verification-cache")
    a = ap.parse_args()
    rec = run(GitHubSource(pathlib.Path(a.cache)), pathlib.Path(a.out))
    print(json.dumps(rec["totals"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
