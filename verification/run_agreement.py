"""Run M4.4-C: model-agreement analysis (ECMWF + GFS + ICON; weather-model rainfall events; not CORE risk
verification; observed frequencies only).

  python verification/run_agreement.py --census DIR --out DIR [--cache DIR]

Same integrity chain as M4.4-A/B (verified releases, February annotation, census recomputed = published census-2).
Sample: the census-2 three-model shared-data sample (all three models and the reference eligible), pooled over the
archive points, all seasons, for A3 (IMD 08:30 day) -> C3 (primary reference) and A4 (ERA5 IST day) -> C4
(secondary). IMD and ERA5 are never combined. Leads 1-6; lead 7 is not analysed (ICON not defined).
Roles: C3 leads 1-4 primary; C4 leads 1-4 secondary; leads 5-6 exploratory (GFS source-resolution note); the
model-combination breakdown of k = 1 and k = 2 is exploratory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import agreement as AG  # noqa: E402
from common import CENSUS_VERSION, METHODOLOGY_VERSION, CensusError  # noqa: E402
import events as EV  # noqa: E402
from inputs import GitHubSource  # noqa: E402
import metrics as MX  # noqa: E402
from reporting import DEGENERATE_LABEL, label  # noqa: E402
from run_census import _commit  # noqa: E402
from run_events import verified_pairs  # noqa: E402
from run_metrics import _sha, cell_id  # noqa: E402

GATE = "M4.4-C model-agreement analysis (weather-model rainfall events; not CORE risk verification)"
EXP = {"A3": ("C3", "IMD gridded rain-gauge analysis", "08:30-08:30 IST rain day"),
       "A4": ("C4", "ERA5 reanalysis", "IST calendar day")}
LEADS = range(1, 7)
PRIMARY_LEADS = range(1, 5)
COMBO3 = "shared-data:ecmwf_ifs025+gfs_global+icon_global"
LEAD56_LIMIT = ("GFS rainfall source representation changes at this lead range. The effect on the verification metric "
                "and on the model-agreement distribution is unresolved.")
K_GROUPS = ["k=0", "k=1", "k=2", "k=3"]
MEMBER_GROUPS = {"k=1": ["ECMWF", "GFS", "ICON"], "k=2": ["ECMWF+GFS", "ECMWF+ICON", "GFS+ICON"]}
COLUMNS = ["cell_id", "census_cell_id", "experiment", "reference", "window", "lead", "threshold_mm", "threshold_source",
           "analysis", "group", "k", "n", "reference_events", "status", "frequency", "ci_low", "ci_high",
           "undefined_resamples", "interval_note", "cell_n", "n_dates", "n_points", "period_start", "period_end",
           "n_blocks", "seed", "floor_rule", "role", "role_basis", "limitations", "statement"]


def _role(aexp: str, lead: int, analysis: str) -> tuple[str, str]:
    if analysis == "model-combination":
        return "exploratory", "model-combination breakdown" + ("; leads 5-6" if lead >= 5 else "")
    if lead not in PRIMARY_LEADS:
        return "exploratory", "leads 5-6 (GFS source-resolution limitation)"
    if aexp == "A3":
        return "primary", "IMD reference, pooled, all seasons, leads 1-4"
    return "secondary", "ERA5 reference (secondary), pooled, all seasons, leads 1-4"


def compute(P: pd.DataFrame, C: pd.DataFrame, calls: list | None = None) -> pd.DataFrame:
    rows = []
    for aexp, (xid, ref_label, window) in EXP.items():
        E = P[(P["experiment"] == aexp) & P["eligible"] & P["model"].isin(AG.AGREEMENT_MODELS)]
        for lead in LEADS:
            crow = C[(C["experiment"] == aexp) & (C["comparison"] == COMBO3) & (C["lead"] == lead)
                     & (C["geo_slice_type"] == "pooled") & (C["season"] == "all") & (C["stratum"] == "all")]
            if len(crow) != 1:
                raise CensusError(f"{aexp} L{lead}: three-model census cell not found")
            cr = crow.iloc[0]
            ccid = cell_id(cr)
            g = E[E["lead"] == lead]
            F = g.pivot(index=["point_id", "date"], columns="model", values="forecast_value")
            Rv = g.pivot(index=["point_id", "date"], columns="model", values="reference_value")
            F = F[F[list(AG.AGREEMENT_MODELS)].notna().all(axis=1)]
            Rv = Rv.loc[F.index]
            if ((Rv.max(axis=1) - Rv.min(axis=1)) != 0).any():
                raise CensusError(f"{aexp} L{lead}: reference differs between models")
            n_all, dates = len(F), F.index.get_level_values("date")
            got = (n_all, dates.nunique(), F.index.get_level_values("point_id").nunique())
            if got != (int(cr["n_eligible"]), int(cr["n_dates"]), int(cr["n_points"])):
                raise CensusError(f"{ccid}: agreement sample {got} differs from the census")
            for thr in EV.THRESHOLDS:
                if cr["status"] != "meets floor":
                    for analysis, groups in (("k-groups", K_GROUPS), ("model-combination", sum(MEMBER_GROUPS.values(), []))):
                        for grp in groups:
                            rows.append({"cell_id": f"{xid}|{analysis}|L{lead}|T{thr}", "census_cell_id": ccid,
                                         "experiment": xid, "lead": lead, "threshold_mm": thr, "analysis": analysis,
                                         "group": grp, "status": cr["status"], "floor_rule": cr["floor_rule"]})
                    continue
                k, members = AG.k_and_members({m: F[m].values for m in AG.AGREEMENT_MODELS}, thr)
                obs = EV.is_event(Rv.max(axis=1).values, thr)
                kg = np.array([f"k={x}" for x in k])
                period = (str(min(dates)), str(max(dates)))
                for analysis, grp_arr, groups in (("k-groups", kg, K_GROUPS),
                                                  ("model-combination", members, sum(MEMBER_GROUPS.values(), []))):
                    cid = f"{xid}|{analysis}|L{lead}|T{thr}"
                    counts = {gname: (int((grp_arr == gname).sum()), int(obs[grp_arr == gname].sum())) for gname in groups}
                    compute_set = {gname for gname, (n, e) in counts.items() if AG.floor_ok(n, e)}
                    res = {"n_blocks": None, "seed": None, "groups": {}}
                    if compute_set:
                        if calls is not None:
                            calls.append((cid, sorted(compute_set)))
                        res = AG.bootstrap_groups(grp_arr, obs, dates.values, cid, compute_set)
                    role_, basis = _role(aexp, lead, analysis)
                    lim = [LEAD56_LIMIT] if lead >= 5 else []
                    for gname in groups:
                        n, e = counts[gname]
                        kk = int(gname[2]) if gname.startswith("k=") else len(gname.split("+"))
                        base = {"cell_id": cid, "census_cell_id": ccid, "experiment": xid, "reference": cr["reference"],
                                "window": cr["window"], "lead": lead, "threshold_mm": thr,
                                "threshold_source": EV.THRESHOLD_SOURCE[thr], "analysis": analysis, "group": gname,
                                "k": kk, "n": n, "reference_events": e, "cell_n": n_all, "n_dates": dates.nunique(),
                                "n_points": got[2], "period_start": period[0], "period_end": period[1],
                                "n_blocks": res["n_blocks"], "seed": res["seed"],
                                "floor_rule": f"{cr['floor_rule']}; per group n >= {AG.MIN_N} and >= {AG.MIN_EVENTS} "
                                              "reference events",
                                "role": role_, "role_basis": basis, "limitations": ";".join(lim)}
                        who = "" if analysis == "k-groups" else f" (models at or above the threshold: {gname})"
                        if gname not in compute_set:
                            rows.append({**base, "status": "insufficient sample", "frequency": None, "ci_low": None,
                                         "ci_high": None, "undefined_resamples": None, "interval_note": None,
                                         "statement": f"{gname}{who}: insufficient sample (needs n >= {AG.MIN_N} and "
                                                      f">= {AG.MIN_EVENTS} reference events). No value computed."})
                            continue
                        x = res["groups"][gname]
                        ci = x["ci"]
                        lo, hi = (None, None) if ci is None else ci
                        note = label("frequency", x["value"], lo, hi)
                        st = (f"In the archived sample ({period[0]} to {period[1]}, {got[2]} archive points, {ref_label}, "
                              f"{window}, nominal lead {lead}), when {kk} of 3 models forecast >= {thr} mm{who}, the "
                              f"reference reached >= {thr} mm on {e} of {n} days (observed frequency {x['value']:.3f}; "
                              + ("95% block-bootstrap interval: no value" if ci is None else
                                 f"95% block-bootstrap interval {lo:.3f} to {hi:.3f}") + ").")
                        if note:
                            st += " " + note
                        rows.append({**base, "status": "ok", "frequency": x["value"], "ci_low": lo, "ci_high": hi,
                                     "undefined_resamples": x["undefined_resamples"], "interval_note": note,
                                     "statement": st})
    R = pd.DataFrame(rows, columns=COLUMNS)
    for c in ("frequency", "ci_low", "ci_high"):
        R[c] = R[c].astype(float).round(6)
    return R.sort_values(["experiment", "analysis", "lead", "threshold_mm", "group"], kind="mergesort").reset_index(drop=True)


def run(source, out: pathlib.Path, census_dir: pathlib.Path, calls: list | None = None) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    P, C, crec, prov, ann_notes = verified_pairs(source, census_dir)
    R = compute(P, C, calls)
    R.to_parquet(out / "agreement_results.parquet", index=False)
    R.to_csv(out / "agreement_results.csv", index=False)
    config = {"models": list(AG.AGREEMENT_MODELS), "k": "number of the three models with forecast >= threshold (float32)",
              "thresholds_mm": list(EV.THRESHOLDS), "threshold_source": "CORE M-RAIN (thresholds only)",
              "sample": "census-2 three-model shared-data sample, pooled, all seasons, leads 1-6",
              "references": {"C3": "IMD 08:30-08:30 IST (primary)", "C4": "ERA5 IST day (secondary); never combined"},
              "floors": f"per group n >= {AG.MIN_N} and >= {AG.MIN_EVENTS} reference events",
              "ci": {"level": MX.CI_LEVEL, "method": MX.CI_METHOD, "resamples": MX.BOOTSTRAP_RESAMPLES,
                     "block_days": MX.BLOCK_DAYS, "block_origin": str(MX.BLOCK_ORIGIN), "master_seed": MX.BOOTSTRAP_SEED,
                     "cell_seed": "SHA-256('<master_seed>|<cell_id>')[:8], big-endian; one draw matrix per cell, shared "
                                  "by all its groups",
                     "undefined_resamples": f"n* = 0 left out; interval 'no value' if more than {EV.MAX_UNDEFINED_RESAMPLES}"},
              "degenerate_label": DEGENERATE_LABEL, "primary_leads": list(PRIMARY_LEADS),
              "exploratory_leads": [5, 6], "lead_7": "not analysed (ICON not defined)",
              "rounding": "frequency and interval rounded to 6 decimals"}
    hashes = {"agreement_results.csv": _sha(out / "agreement_results.csv")}
    ok = R[R["status"] == "ok"]
    rec = {"gate": GATE, "methodology_version": METHODOLOGY_VERSION,
           "census_id": f"{CENSUS_VERSION}@{crec['code_commit'][:7]}", "census_cells_sha256": crec["result_sha256"]["census_cells.csv"],
           "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(), "code_commit": _commit(),
           "archive_index_commit": getattr(source, "index_commit", None), "months": crec["months"], "releases": prov,
           "annotations_applied": ann_notes, "config": config,
           "config_sha256": hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
           "result_sha256": hashes,
           "counts": {"group_rows": int(len(R)), "computed": int(len(ok)),
                      "insufficient_sample": int((R["status"] == "insufficient sample").sum()),
                      "census_floor_not_met": int((~R["status"].isin(["ok", "insufficient sample"])).sum()),
                      "degenerate_intervals_labelled": int(ok["interval_note"].notna().sum()),
                      "interval_no_value": int(ok["ci_low"].isna().sum()),
                      "computed_by_role": {k: int(v) for k, v in ok["role"].value_counts().sort_index().items()}},
           "not_done": ["M4.4-D CORE risk verification", "historical rule replay", "METAR occurrence validation",
                        "calibrated forecast statements"],
           "external_data_calls": "none (own immutable releases and archive-index only)"}
    (out / "agreement_run.json").write_text(json.dumps(rec, indent=1, default=str) + "\n")
    (out / "agreement_report.md").write_text(report(R, rec))
    return rec


def _fmt_group(x) -> str:
    if x.status != "ok":
        return f"{x.status} (n {int(x.n):,})" if not pd.isna(x.n) else x.status
    ci = "interval: no value" if pd.isna(x.ci_low) else f"[{x.ci_low:.3f}, {x.ci_high:.3f}]"
    return f"{int(x.reference_events):,} of {int(x.n):,} = {x.frequency:.3f} {ci}" + (" ◊" if isinstance(x.interval_note, str) else "")


def _table(D: pd.DataFrame, groups: list) -> list[str]:
    L = ["| Lead | Threshold (mm) | " + " | ".join(groups) + " |", "| --- | --- |" + " --- |" * len(groups)]
    for (lead, thr), g in D.groupby(["lead", "threshold_mm"], sort=True):
        by = {r.group: r for r in g.itertuples()}
        L.append(f"| {lead} | {thr} | " + " | ".join(_fmt_group(by[x]) for x in groups) + " |")
    return L


def report(R: pd.DataFrame, rec: dict) -> str:
    L = [f"# M4.4-C — model agreement ({rec['methodology_version']}, census {rec['census_id']})", "",
         "**Weather-model rainfall-event agreement only (ECMWF, GFS, ICON).** Not CORE risk verification and not a "
         "calibrated forecast statement.", "",
         "Each cell reads: \"In the archived sample … when k of 3 models forecast ≥ τ, the reference reached ≥ τ on "
         "x of n days.\" The k-groups of one lead and threshold partition the same sample. They are mutually "
         "exclusive, not independent samples, and their intervals must not be compared as if they were independent.",
         "", f"◊ = {DEGENERATE_LABEL}", "",
         f"Code {rec['code_commit'][:7]}; archive-index {str(rec['archive_index_commit'])[:7]}. IMD (C3) and ERA5 (C4) "
         "are separate; their counts are never combined. Lead 7 is not analysed (ICON not defined).", ""]
    K = R[R["analysis"] == "k-groups"]
    for exp, role, title in (("C3", "primary", "Primary — IMD, pooled, all seasons, leads 1–4"),
                             ("C4", "secondary", "Secondary — ERA5, pooled, all seasons, leads 1–4")):
        L += [f"## {title}", ""] + _table(K[(K.experiment == exp) & (K.role == role)], K_GROUPS) + [""]
    L += ["## Exploratory — leads 5–6", "", f"**Limitation:** {LEAD56_LIMIT} A lower GFS event count at these leads "
          "does not mean improved or degraded forecast skill.", ""]
    for exp in ("C3", "C4"):
        L += [f"### {exp} ({'IMD' if exp == 'C3' else 'ERA5'})", ""] + _table(K[(K.experiment == exp) & (K.lead >= 5)], K_GROUPS) + [""]
    M = R[(R["analysis"] == "model-combination") & (R["experiment"] == "C3") & (R["lead"] <= 4)]
    L += ["## Exploratory — which models make up k = 1 and k = 2 (IMD, leads 1–4)", ""] + \
        _table(M, sum(MEMBER_GROUPS.values(), [])) + ["", "ERA5, leads 5–6 and every other cell: `agreement_results.csv`.", ""]
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--census", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cache", default="/tmp/claude-0/verification-cache")
    a = ap.parse_args()
    rec = run(GitHubSource(pathlib.Path(a.cache)), pathlib.Path(a.out), pathlib.Path(a.census))
    print(json.dumps(rec["counts"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
