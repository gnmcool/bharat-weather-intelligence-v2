"""Build the degenerate-interval reporting annotation for a published event-results table (owner decision at the
M4.4-B review). Reads the published results; writes a separate annotation. The results themselves are never changed.

  python verification/label_degenerate.py RESULTS.csv[.gz|.parquet] RESULT_SHA256 RECORD_PATH OUT.json
"""
from __future__ import annotations

import json
import sys

import pandas as pd

from reporting import DEGENERATE_LABEL, degenerate


def build(R: pd.DataFrame, results_sha: str, record: str) -> dict:
    ok = R[(R["status"] == "ok") & ~R["subject"].str.startswith("difference")]   # label defined for boundary values only
    lab = ok[[degenerate(m, v, lo, hi) for m, v, lo, hi in
              zip(ok["metric"], ok["value"], ok["ci_low"], ok["ci_high"])]]
    rows = [{"event_cell_id": r.event_cell_id, "subject": r.subject, "metric": r.metric, "value": r.value,
             "interval": [r.ci_low, r.ci_high], "role": r.role} for r in lab.itertuples()]
    return {"id": "m4.4-b-degenerate-interval-label-1", "kind": "reporting label (append-only; results unchanged)",
            "decided": "owner, M4.4-B review, 30 Sep 2026", "label": DEGENERATE_LABEL,
            "applies_to": {"record": record, "event_results_csv_sha256": results_sha},
            "rule": "single-model rows with status ok, value on a boundary (POD/FAR/CSI 0 or 1; frequency bias 0) and "
                    "ci_low == ci_high == value; model-difference rows are not labelled (a difference of 0 is not a "
                    "boundary value)",
            "rows_labelled": len(rows), "by_role": lab["role"].value_counts().sort_index().to_dict(), "rows": rows}


if __name__ == "__main__":
    src, sha, record, out = sys.argv[1:5]
    R = pd.read_parquet(src) if src.endswith(".parquet") else pd.read_csv(src)
    rec = build(R, sha, record)
    with open(out, "w") as f:
        json.dump(rec, f, indent=1, default=str)
        f.write("\n")
    print(rec["rows_labelled"], rec["by_role"])
