"""Write the git index record for one archive day (published or refused).

The index lives on the `archive-index` branch (append-only data branch, never merged into main):
  index/YYYY/MM/<day>.json         published release: manifest, SHA-256 of manifest and gap report,
                                   release URL, post-publish checksum verification, immutability checks
  index/refused/<day>_<run>.json   refused attempt: gap report and problems (nothing was published)
  INDEX.csv                        one line per attempt
Git history is the tamper-evident record that a file existed before the weather it forecast.
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import sys
from datetime import datetime, timezone

from common import sha256, write_json


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True)
    ap.add_argument("--index", required=True, help="checkout of the archive-index branch")
    ap.add_argument("--status", choices=["published", "refused"], required=True)
    ap.add_argument("--tag")
    ap.add_argument("--release-url")
    ap.add_argument("--checks", help="JSON file with post-publish verification and immutability results")
    ap.add_argument("--run-id", default="local")
    a = ap.parse_args()
    stage, idx = pathlib.Path(a.stage), pathlib.Path(a.index)
    gap = next(stage.glob("gap_report_*.json"), None)
    man = next(stage.glob("manifest_*.json"), None)
    day = json.loads(gap.read_text()).get("archive_date_ist") if gap else "unknown"
    rec = {
        "archive_date_ist": day, "status": a.status, "recorded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "run_id": a.run_id, "tag": a.tag, "release_url": a.release_url,
        "manifest_sha256": sha256(man) if man else None, "gap_report_sha256": sha256(gap) if gap else None,
        "manifest": json.loads(man.read_text()) if man else None,
        "gap_report": json.loads(gap.read_text()) if gap else None,
        "checks": json.loads(pathlib.Path(a.checks).read_text()) if a.checks else None,
    }
    if a.status == "published":
        path = idx / "index" / day[:4] / day[5:7] / f"{day}.json"
        if path.exists():
            print(f"refusing to overwrite existing index record {path}", file=sys.stderr)
            return 1
    else:
        path = idx / "index" / "refused" / f"{day}_{a.run_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, rec)
    csv_path = idx / "INDEX.csv"
    new = not csv_path.exists()
    with open(csv_path, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["archive_date_ist", "status", "tag", "manifest_sha256", "forecast_rows", "missing", "recorded_utc", "run_id"])
        rows = next((x["rows"] for x in (rec["manifest"] or {}).get("files", []) if x["kind"] == "forecasts"), None)
        w.writerow([day, a.status, a.tag or "", rec["manifest_sha256"] or "", rows or "",
                    len((rec["gap_report"] or {}).get("missing", [])), rec["recorded_utc"], a.run_id])
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
