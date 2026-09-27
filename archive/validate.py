"""Validate a staged daily archive. Exit 0 = may be published; exit 1 = must not be published.

Always writes gap_report_<D>.json. Checks:
  1. manifest lists exactly the files present; every SHA-256 and row count matches
  2. schema, types and non-null required columns; run_time_known is true for every forecast row
  3. lead_day == valid_date_ist - IST date(run_time_utc), and lead_day >= 0
  4. no duplicate (point, model, run, valid date, variable)
  5. completeness: every expected (point, model, variable, lead) has a non-null value, where "expected" = the
     leads the model run fully covers (from its metadata) and the variables the source provides
  6. every expected model is present (a failed model = incomplete); CORE snapshot complete (36 points x 11 risks)
Missing data is reported, never filled.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from collections import Counter

import pyarrow.parquet as pq

from common import FORECAST_SCHEMA, REQUIRED_NON_NULL, ArchiveError, sha256, write_json
from collect import MODELS

EXPECTED_MODELS = list(MODELS) + ["e2s_gfs025"]


def validate(stage: pathlib.Path) -> dict:
    manifests = sorted(stage.glob("manifest_*.json"))
    if len(manifests) != 1:
        raise ArchiveError(f"expected exactly one manifest, found {len(manifests)}")
    man = json.loads(manifests[0].read_text())
    day = man["archive_date_ist"]
    problems: list[str] = []
    gaps = {"archive_date_ist": day, "missing": [], "not_provided_by_source": [], "partial_days_stored": 0,
            "collection_errors": man.get("collection_errors", []), "http": man.get("http"), "test_injection": man["producer"].get("test_injection")}

    # 1. files and checksums
    listed = {f["name"]: f for f in man["files"]}
    present = {p.name for p in stage.iterdir() if p.is_file() and not p.name.startswith(("manifest_", "gap_report_", "_"))}
    if set(listed) != present:
        problems.append(f"files differ from manifest: unlisted {sorted(present - set(listed))}, missing {sorted(set(listed) - present)}")
    for name, f in listed.items():
        p = stage / name
        if not p.exists():
            continue
        if sha256(p) != f["sha256"]:
            problems.append(f"checksum mismatch: {name}")
        elif f.get("rows") is not None and pq.ParquetFile(p).metadata.num_rows != f["rows"]:
            problems.append(f"row count mismatch: {name}")
    if problems:  # do not read content of files that fail their checksum
        gaps["problems"] = problems
        return {"ok": False, "gaps": gaps, "problems": problems}

    # 2. schema and types
    fc = pq.read_table(stage / f"forecasts_{day}.parquet")
    if not fc.schema.equals(FORECAST_SCHEMA, check_metadata=False):
        problems.append("forecasts schema differs from FORECAST_SCHEMA")
    df = fc.to_pandas()
    for c in REQUIRED_NON_NULL:
        if df[c].isna().any():
            problems.append(f"null values in required column {c}")
    if not df["run_time_known"].all():
        problems.append("run_time_known is false for some forecast rows (not allowed in the V2 archive)")

    # 3. lead-day rule (run_time_utc is an instant, valid_date_ist a calendar date: never compared as the same kind)
    run_ist_date = df["run_time_utc"].dt.tz_convert("Asia/Kolkata").dt.date
    calc = [(v - r).days for v, r in zip(df["valid_date_ist"], run_ist_date)]
    bad = df.index[[c != l for c, l in zip(calc, df["lead_day"])]]
    if len(bad):
        problems.append(f"lead_day inconsistent with run and valid date in {len(bad)} rows (first: {df.loc[bad[0], ['point_id', 'model', 'valid_date_ist', 'lead_day']].to_dict()})")
    if (df["lead_day"] < 0).any():
        problems.append("negative lead_day (valid date before the run)")

    # 3b. physically plausible ranges (catches unit mix-ups such as m/s vs km/h; not a weather rule)
    RANGES = {"tmax": (-60, 60), "tmin": (-60, 60), "precip": (0, 1500), "gust_max": (0, 400)}
    for var, (lo, hi) in RANGES.items():
        v = df.loc[(df["variable"] == var) & df["value"].notna(), "value"]
        n = int(((v < lo) | (v > hi)).sum())
        if n:
            problems.append(f"{n} {var} values outside the plausible range {lo}..{hi}")

    # 4. duplicates
    dup = df.duplicated(["point_id", "model", "run_time_utc", "valid_date_ist", "variable"]).sum()
    if dup:
        problems.append(f"{dup} duplicate forecast rows")

    # 5-6. completeness against the expectation spec recorded at collection time
    specs = {s["model"]: s for s in man["expected"]["forecasts"]}
    for m in EXPECTED_MODELS:
        if m not in specs:
            problems.append(f"model {m} missing entirely")
    points = json.loads((pathlib.Path(__file__).parent / "points.json").read_text())["points"]
    have = {(r.point_id, r.model, int(r.lead_day), r.variable) for r in df[df["value"].notna()].itertuples()}
    gaps["partial_days_stored"] = int(df["day_partial"].sum())
    for m, s in specs.items():
        all_vars = sorted(df.loc[df["model"] == m, "variable"].unique()) or s["variables"]
        for v in all_vars:
            if v not in s["variables"]:
                gaps["not_provided_by_source"].append({"model": m, "variable": v, "reason": "variable not provided by this source"})
        for p in points:
            for v in s["variables"]:
                for lead in s["expected_leads"]:
                    if (p["id"], m, lead, v) not in have:
                        gaps["missing"].append({"point_id": p["id"], "model": m, "variable": v, "lead_day": lead})
        beyond = sorted(set(range(0, 10)) - set(s["expected_leads"]))
        if beyond:
            gaps["not_provided_by_source"].append({"model": m, "leads": beyond,
                                                   "reason": "outside the run's full-day coverage (partial or beyond its last valid time)"})
    if gaps["missing"]:
        problems.append(f"{len(gaps['missing'])} expected forecast values missing")

    cr = pq.read_table(stage / f"core_risks_{day}.parquet").to_pandas()
    per_point = Counter(cr["point_id"])
    short = [p["id"] for p in points if per_point.get(p["id"], 0) != man["expected"]["core"]["risks_per_point"]]
    if short:
        problems.append(f"CORE snapshot incomplete for {len(short)} points")
        gaps["missing"] += [{"point_id": pid, "model": "core", "variable": "risks"} for pid in short]
    if man.get("collection_errors"):
        problems.append(f"collection errors: {man['collection_errors']}")

    gaps["expected_counts"] = {m: len(points) * len(s["variables"]) * len(s["expected_leads"]) for m, s in specs.items()}
    gaps["present_counts"] = {m: int(((df["model"] == m) & df["value"].notna() & ~df["day_partial"]).sum()) for m in specs}
    gaps["problems"] = problems
    return {"ok": not problems, "gaps": gaps, "problems": problems}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage")
    a = ap.parse_args()
    stage = pathlib.Path(a.stage)
    try:
        res = validate(stage)
    except ArchiveError as e:
        res = {"ok": False, "gaps": {"problems": [str(e)]}, "problems": [str(e)]}
    day = res["gaps"].get("archive_date_ist", "unknown")
    res["gaps"]["publishable"] = res["ok"]
    write_json(stage / f"gap_report_{day}.json", res["gaps"])
    print(json.dumps({"publishable": res["ok"], "problems": res["problems"],
                      "missing": len(res["gaps"].get("missing", [])),
                      "not_provided_by_source": res["gaps"].get("not_provided_by_source")}, indent=1, default=str))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
