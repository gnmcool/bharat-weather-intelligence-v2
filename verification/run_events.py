"""Run M4.4-B: rain event verification (weather-model event detection only; NOT CORE risk verification).

  python verification/run_events.py --census DIR --out DIR [--cache DIR]

Same integrity chain as M4.4-A Gate 2: every release verified (published, immutable, manifest and file SHA-256),
February 2024 annotation required, census recomputed from the verified data and byte-identical to the published
census-2. No external data call.

Samples: the census-2 eligible pairs of A3 (rain 08:30-08:30 IST vs IMD) -> experiment B3 (primary reference) and
A4 (rain IST day vs ERA5) -> B4 (secondary). IMD and ERA5 are never combined. Stratum "all" only.
Per census cell x CORE M-RAIN threshold (35.6 / 64.5 / 115.6 mm):
  * census status not "meets floor"          -> suppressed: no count or value computed;
  * census floor met                          -> contingency counts and base rate;
  * ratio event floor (VM §11) not met        -> that ratio "insufficient sample", no value computed;
  * ratio event floor met                     -> value and 95% block-bootstrap interval.
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
from census import census, pairs_for_month  # noqa: E402
from common import CENSUS_VERSION, METHODOLOGY_VERSION, MODELS, CensusError  # noqa: E402
import events as EV  # noqa: E402
from inputs import GitHubSource, annotation_overrides, load_index, load_month  # noqa: E402
import metrics as MX  # noqa: E402
from run_census import _commit  # noqa: E402
from run_metrics import FEB_ANNOTATION, _check_counts, _mask, _sha, cell_id  # noqa: E402

GATE = "M4.4-B rain event verification (weather-model event detection; not CORE risk verification)"
EXP = {"A3": {"id": "B3", "reference_role": "primary reference (IMD)", "label": "IMD gridded rain-gauge analysis",
              "window": "08:30-08:30 IST"},
       "A4": {"id": "B4", "reference_role": "secondary reference (ERA5)", "label": "ERA5 reanalysis",
              "window": "IST calendar day"}}
PRIMARY_LEADS = range(1, 7)
GFS_LIMIT = ("source-resolution:gfs-precip-lead5+ (source representation change established; effect on verification "
             "metrics unresolved)")
ERA5_EVENT_LIMIT = "ERA5-under-represents-localised-convective-rain"
COLUMNS = ["event_cell_id", "census_cell_id", "experiment", "comparison", "subject", "model_a", "model_b", "variable",
           "window", "reference", "lead", "geo_slice_type", "geo_slice", "season", "threshold_mm",
           "threshold_source", "n", "n_dates", "n_points", "hits", "misses", "false_alarms", "correct_negatives",
           "observed_events", "forecast_events", "base_rate", "metric", "status", "value", "ci_low", "ci_high",
           "undefined_resamples", "interval_excludes_zero", "n_blocks", "seed", "floor_rule", "role", "role_basis",
           "limitations", "statement"]


def event_role(r) -> tuple[str, str]:
    why = []
    if r["season"] != "all":
        why.append("seasonal slice")
    if r["geo_slice_type"] == "region":
        why.append("regional slice")
    if r["geo_slice_type"] == "high_altitude":
        why.append("elevation diagnostic")
    if int(r["lead"]) not in PRIMARY_LEADS:
        why.append("lead 7")
    if r["comparison"].count("+") >= 2:
        why.append("three-model shared sample")
    if why:
        return "exploratory", "; ".join(why)
    if r["experiment"] == "A3":
        return "primary", "IMD reference, pooled eligible points, all seasons, leads 1-6"
    return "secondary", "ERA5 reference (secondary), pooled, all seasons, leads 1-6"


def verified_pairs(source, census_dir: pathlib.Path):
    """M4.4-A integrity chain (unchanged). Returns (P, C, census record, provenance, annotations)."""
    crec = json.loads((census_dir / "census_run.json").read_text())
    ccsv = census_dir / "census_cells.csv"
    if _sha(ccsv) != crec["result_sha256"]["census_cells.csv"]:
        raise CensusError("census_cells.csv does not match its recorded SHA-256 (tampered census refused)")
    if crec.get("census_version") != CENSUS_VERSION or crec.get("methodology_version") != METHODOLOGY_VERSION:
        raise CensusError(f"census {crec.get('census_version')}/{crec.get('methodology_version')} is not "
                          f"{CENSUS_VERSION}/{METHODOLOGY_VERSION}")
    recs, anns = load_index(source)
    parts, prov, ann_notes = [], [], []
    for m in crec["months"]:
        md = load_month(source, recs[m])
        over, notes = annotation_overrides(md, anns)
        if m == "2024-02" and not any(n["annotation"] == FEB_ANNOTATION for n in notes):
            raise CensusError(f"2024-02 used without the verified {FEB_ANNOTATION} annotation")
        ann_notes += [{"month": m, **n} for n in notes]
        parts.append(pairs_for_month(md, over))
        prov.append(md["provenance"])
    if [(p["tag"], p["manifest_sha256"]) for p in prov] != [(p["tag"], p["manifest_sha256"]) for p in crec["releases"]]:
        raise CensusError("the census was built from different releases")
    if ann_notes != crec["annotations_applied"]:
        raise CensusError("annotations applied differ from the census record")
    P = pd.concat(parts, ignore_index=True)
    C = census(P)
    if hashlib.sha256(C.to_csv(index=False).encode()).hexdigest() != crec["result_sha256"]["census_cells.csv"]:
        raise CensusError("the census recomputed from the verified releases differs from the published census")
    return P, C, crec, prov, ann_notes


def _population(r, n_points) -> str:
    t, v = r["geo_slice_type"], r["geo_slice"]
    where = {"pooled": f"the {n_points} archive points with eligible pairs", "region": f"the {v} region ({n_points} points)",
             "high_altitude": f"archive points {'at' if v == '>=1000m' else 'below'} 1,000 m ({n_points} points)"}[t]
    return where + ("" if r["season"] == "all" else f", {r['season']} season")


def _fmt(x):
    return "no value" if x is None else f"{x:.3f}"


def _rows(base, subject, cont, res, floors, r, sub, thr):
    out = []
    ev = EXP[r["experiment"]]
    head = (f"rain >= {thr} mm ({EV.THRESHOLD_SOURCE[thr]}; threshold only) vs {ev['label']} ({ev['window']}), nominal "
            f"lead {int(r['lead'])}, {_population(r, sub['point_id'].nunique())}, {sub['date'].min()} to "
            f"{sub['date'].max()}; n={len(sub):,} pairs, {cont['observed_events']} reference events"
            + ("" if cont["hits"] is None else f"; hits {cont['hits']}, misses {cont['misses']}, false alarms "
               f"{cont['false_alarms']}, correct negatives {cont['correct_negatives']}"))
    for m in EV.RATIOS:
        diff = subject.startswith("difference")
        row = {**base, "subject": subject, "metric": m, **{k: cont[k] for k in
               ("hits", "misses", "false_alarms", "correct_negatives", "observed_events", "forecast_events", "base_rate")}}
        if not floors[m]:
            row.update(status="insufficient sample", value=None, ci_low=None, ci_high=None, undefined_resamples=None,
                       interval_excludes_zero=None,
                       statement=f"{m.upper()}: insufficient sample (event floor: >= {EV.EVENT_FLOOR} reference events "
                                 f"for POD, >= {EV.EVENT_FLOOR} forecast events for FAR, both for CSI and frequency "
                                 f"bias). {head}. No value computed.")
            out.append(row)
            continue
        x = res[m]
        v, ci = x["value"], x["ci"]
        status = "ok" if v is not None else "no value"
        excl = None if (ci is None or not diff) else bool(ci[0] > 0 or ci[1] < 0)
        ci_txt = "interval: no value" if ci is None else f"95% {'paired ' if diff else ''}block-bootstrap interval {ci[0]:.3f} to {ci[1]:.3f}"
        if diff:
            st = (f"Measured {m.upper()} difference ({subject.split(': ')[1]}) on the shared-data sample: {_fmt(v)} "
                  f"({ci_txt}; the interval {'excludes' if excl else 'includes' if excl is not None else 'is not available for'} 0). "
                  f"{head}. A measured difference for this population, reference, threshold and period only; it does "
                  f"not show that either model is better in general.")
        else:
            st = f"Measured {m.upper()} of {subject}: {_fmt(v)} ({ci_txt}). {head}."
        st += " Weather-model rainfall-event verification; not CORE risk verification."
        row.update(status=status, value=v, ci_low=None if ci is None else ci[0], ci_high=None if ci is None else ci[1],
                   undefined_resamples=x["undefined_resamples"], interval_excludes_zero=excl, statement=st)
        out.append(row)
    return out


def compute(P: pd.DataFrame, C: pd.DataFrame, calls: list | None = None):
    rows, supp = [], []
    for aexp in ("A3", "A4"):
        T = C[(C["experiment"] == aexp) & (C["stratum"] == "all")]
        E = P[(P["experiment"] == aexp) & P["eligible"]].copy()
        for col in ("forecast_value", "reference_value"):
            if not np.isfinite(E[col].astype(np.float64).values).all():
                raise CensusError(f"{aexp}: non-finite value in an eligible pair")
        single = {k: g for k, g in E.groupby(["model", "variable", "lead"], sort=True)}
        wide = {}
        for (var, lead), g in E.groupby(["variable", "lead"], sort=True):
            F = g.pivot(index=["point_id", "date"], columns="model", values="forecast_value")
            Rv = g.pivot(index=["point_id", "date"], columns="model", values="reference_value")
            spread = (Rv.max(axis=1) - Rv.min(axis=1)).fillna(0)
            if (spread != 0).any():
                raise CensusError(f"{aexp} {var} L{lead}: reference differs between models for the same point/date")
            A = g.drop_duplicates(["point_id", "date"]).set_index(["point_id", "date"])[
                ["region", "high_altitude", "station", "season", "rainy"]]
            wide[(var, lead)] = F.join(Rv.max(axis=1).rename("reference_value")).join(A).reset_index()
        for _, r in T.iterrows():
            ccid = cell_id(r)
            role_, basis = event_role(r)
            for thr in EV.THRESHOLDS:
                ecid = f"{EXP[aexp]['id']}|{ccid.split('|', 1)[1]}|T{thr}"
                if r["status"] != "meets floor":
                    supp.append({"event_cell_id": ecid, "census_cell_id": ccid, "experiment": EXP[aexp]["id"],
                                 "comparison": r["comparison"], "threshold_mm": thr, "status": r["status"],
                                 "census_n_eligible": r["n_eligible"], "floor_rule": r["floor_rule"]})
                    continue
                gfs = "gfs_global" in (r["comparison"] + str(r["model"])) and int(r["lead"]) >= 5
                lim = [r["limitations"]] + ([ERA5_EVENT_LIMIT] if aexp == "A4" else []) + ([GFS_LIMIT] if gfs else [])
                base = {"event_cell_id": ecid, "census_cell_id": ccid, "experiment": EXP[aexp]["id"],
                        "comparison": r["comparison"], "variable": r["variable"], "window": r["window"],
                        "reference": r["reference"], "lead": int(r["lead"]), "geo_slice_type": r["geo_slice_type"],
                        "geo_slice": r["geo_slice"], "season": r["season"], "threshold_mm": thr,
                        "threshold_source": EV.THRESHOLD_SOURCE[thr],
                        "floor_rule": f"{r['floor_rule']}; POD >= {EV.EVENT_FLOOR} reference events, FAR >= "
                                      f"{EV.EVENT_FLOOR} forecast events, CSI/frequency bias both",
                        "role": role_, "role_basis": basis, "limitations": ";".join(lim)}
                if r["comparison"] == "single-model":
                    g = single[(r["model"], r["variable"], int(r["lead"]))]
                    sub = g[_mask(g, r)]
                    _check_counts(sub, r, ccid)
                    cont = EV.contingency(sub["forecast_value"].values, sub["reference_value"].values, thr)
                    fl = EV.floor_ok(cont["observed_events"], cont["forecast_events"])
                    res = {"n_blocks": None, "seed": None}
                    if any(fl.values()):
                        if calls is not None:
                            calls.append(ecid)
                        res = EV.bootstrap_events(sub["forecast_value"].values, sub["reference_value"].values,
                                                  sub["date"].values, thr, ecid)
                    ext = {**base, "model_a": r["model"], "model_b": None, "n": cont["n"],
                           "n_dates": sub["date"].nunique(), "n_points": sub["point_id"].nunique(),
                           "n_blocks": res["n_blocks"], "seed": res["seed"]}
                    rows += _rows(ext, r["model"], cont, res, fl, r, sub, thr)
                    continue
                combo = r["comparison"].split(":", 1)[1].split("+")
                W = wide[(r["variable"], int(r["lead"]))]
                sub = W[_mask(W, r) & W[combo].notna().all(axis=1).values]
                _check_counts(sub, r, ccid)
                ext = {**base, "n_dates": sub["date"].nunique(), "n_points": sub["point_id"].nunique()}
                conts = {mdl: EV.contingency(sub[mdl].values, sub["reference_value"].values, thr) for mdl in combo}
                fls = {mdl: EV.floor_ok(c["observed_events"], c["forecast_events"]) for mdl, c in conts.items()}
                if len(combo) == 2:
                    a, b = combo
                    any_ok = any(fls[a].values()) or any(fls[b].values())
                    res = {"n_blocks": None, "seed": None, "a": {}, "b": {}, "diff": {}}
                    if any_ok:
                        if calls is not None:
                            calls.append(ecid)
                        res = EV.paired_bootstrap_events(sub[a].values, sub[b].values, sub["reference_value"].values,
                                                         sub["date"].values, thr, ecid)
                    e2 = {**ext, "model_a": a, "model_b": b, "n": len(sub), "n_blocks": res["n_blocks"], "seed": res["seed"]}
                    rows += _rows(e2, a, conts[a], res.get("a"), fls[a], r, sub, thr)
                    rows += _rows(e2, b, conts[b], res.get("b"), fls[b], r, sub, thr)
                    fd = {m: fls[a][m] and fls[b][m] for m in EV.RATIOS}
                    cd = {k: None for k in ("hits", "misses", "false_alarms", "correct_negatives", "forecast_events")}
                    cd.update(observed_events=conts[a]["observed_events"], base_rate=conts[a]["base_rate"])
                    rows += _rows(e2, f"difference: {a} minus {b}", cd, res.get("diff"), fd, r, sub, thr)
                else:
                    for mdl in combo:
                        res = {"n_blocks": None, "seed": None}
                        if any(fls[mdl].values()):
                            if calls is not None:
                                calls.append(ecid + "|" + mdl)
                            res = EV.bootstrap_events(sub[mdl].values, sub["reference_value"].values,
                                                      sub["date"].values, thr, ecid)
                        rows += _rows({**ext, "model_a": mdl, "model_b": None, "n": len(sub),
                                       "n_blocks": res["n_blocks"], "seed": res["seed"]}, mdl, conts[mdl], res,
                                      fls[mdl], r, sub, thr)
    R = pd.DataFrame(rows, columns=COLUMNS)
    for c in ("value", "ci_low", "ci_high", "base_rate"):
        R[c] = R[c].astype(float).round(6)
    R = R.sort_values(["experiment", "event_cell_id", "subject", "metric"], kind="mergesort").reset_index(drop=True)
    S = pd.DataFrame(supp).sort_values("event_cell_id", kind="mergesort").reset_index(drop=True)
    return R, S


def run(source, out: pathlib.Path, census_dir: pathlib.Path, calls: list | None = None) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    P, C, crec, prov, ann_notes = verified_pairs(source, census_dir)
    R, S = compute(P, C, calls)
    R.to_parquet(out / "event_results.parquet", index=False)
    R.to_csv(out / "event_results.csv", index=False)
    S.to_csv(out / "event_suppressed_cells.csv", index=False)
    meta = R.drop_duplicates("event_cell_id")[["event_cell_id", "census_cell_id", "experiment", "comparison", "reference",
                                               "lead", "geo_slice_type", "geo_slice", "season", "threshold_mm", "role",
                                               "role_basis", "limitations"]]
    meta.to_csv(out / "event_comparison_metadata.csv", index=False)
    config = {"thresholds_mm": list(EV.THRESHOLDS), "threshold_source": "CORE M-RAIN (thresholds only)",
              "event": "value >= threshold, applied in float32 (archive storage precision)",
              "ratios": {"pod": "a/(a+c)", "far": "b/(a+b)", "csi": "a/(a+b+c)", "freq_bias": "(a+b)/(a+c)",
                         "base_rate": "(a+c)/n", "zero_denominator": "no value"},
              "floors": {"sample": "census status 'meets floor' (VM §11 pooled/season/region/high-altitude)",
                         "pod": f">= {EV.EVENT_FLOOR} reference events", "far": f">= {EV.EVENT_FLOOR} forecast events",
                         "csi_freq_bias": "both"},
              "ci": {"level": MX.CI_LEVEL, "method": MX.CI_METHOD, "resamples": MX.BOOTSTRAP_RESAMPLES,
                     "block_days": MX.BLOCK_DAYS, "block_origin": str(MX.BLOCK_ORIGIN), "master_seed": MX.BOOTSTRAP_SEED,
                     "cell_seed": "first 8 bytes of SHA-256('<master_seed>|<event_cell_id>'), big-endian",
                     "undefined_resamples": f"left out; interval 'no value' if more than {EV.MAX_UNDEFINED_RESAMPLES}"},
              "references": {"B3": "IMD (primary), 08:30-08:30 IST", "B4": "ERA5 (secondary), IST day; never combined"},
              "primary_leads": list(PRIMARY_LEADS), "rounding": "value, ci, base_rate rounded to 6 decimals"}
    hashes = {n: _sha(out / n) for n in ("event_results.csv", "event_suppressed_cells.csv", "event_comparison_metadata.csv")}
    cells = R.drop_duplicates("event_cell_id")
    ratio_rows = R[~R["subject"].str.startswith("difference")]
    rec = {
        "gate": GATE, "methodology_version": METHODOLOGY_VERSION, "census_id": f"{CENSUS_VERSION}@{crec['code_commit'][:7]}",
        "census_cells_sha256": crec["result_sha256"]["census_cells.csv"],
        "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(), "code_commit": _commit(),
        "archive_index_commit": getattr(source, "index_commit", None), "models": list(MODELS), "months": crec["months"],
        "releases": prov, "annotations_applied": ann_notes, "config": config,
        "config_sha256": hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
        "result_sha256": hashes,
        "counts": {"event_cells_total": int(len(cells) + len(S)), "event_cells_with_counts": int(len(cells)),
                   "event_cells_suppressed_by_census_floor": int(len(S)),
                   "suppressed_by_status": {k: int(v) for k, v in S["status"].value_counts().sort_index().items()},
                   "ratio_values_computed": int((ratio_rows["status"] == "ok").sum()),
                   "ratio_values_insufficient_sample": int((ratio_rows["status"] == "insufficient sample").sum()),
                   "ratio_values_no_value": int((ratio_rows["status"] == "no value").sum()),
                   "cells_by_role": {k: int(v) for k, v in cells["role"].value_counts().sort_index().items()}},
        "not_done": ["CORE risk verification", "M4.4-C/D", "historical rule replay", "METAR occurrence",
                     "global model ranking", "overall BWI score"],
        "external_data_calls": "none (own immutable releases and archive-index only)",
    }
    (out / "event_run.json").write_text(json.dumps(rec, indent=1, default=str) + "\n")
    (out / "event_report.md").write_text(report(R, S, rec))
    return rec


def _cell(x):
    if x.status != "ok":
        return x.status
    ci = "" if pd.isna(x.ci_low) else f" [{x.ci_low:.2f}, {x.ci_high:.2f}]"
    return f"{x.value:.2f}{ci}"


def _table(D: pd.DataFrame) -> list[str]:
    L = ["| Model | Thr (mm) | Lead | n | Obs ev | Fc ev | Hits | Misses | FA | CN | POD | FAR | CSI | Freq bias |",
         "| --- |" + " --- |" * 13]
    for (subj, thr, lead), g in D.groupby(["subject", "threshold_mm", "lead"], sort=True):
        v = {m: g[g["metric"] == m].iloc[0] for m in EV.RATIOS}
        x = v["pod"]
        L.append(f"| {subj} | {thr} | {lead} | {int(x.n):,} | {int(x.observed_events):,} | {int(x.forecast_events):,} | "
                 f"{int(x.hits):,} | {int(x.misses):,} | {int(x.false_alarms):,} | {int(x.correct_negatives):,} | "
                 + " | ".join(_cell(v[m]) for m in EV.RATIOS) + " |")
    return L


def report(R: pd.DataFrame, S: pd.DataFrame, rec: dict) -> str:
    c = rec["counts"]
    L = [f"# M4.4-B — rain event verification ({rec['methodology_version']}, census {rec['census_id']})", "",
         "**Weather-model rainfall-event verification only.** Not CORE risk verification, not CORE alert accuracy, "
         "not impact accuracy. Thresholds are CORE M-RAIN thresholds used as rainfall amounts only.", "",
         f"Code {rec['code_commit'][:7]}; archive-index {str(rec['archive_index_commit'])[:7]}; "
         f"{len(rec['months'])} verified releases. IMD (B3) and ERA5 (B4) results are separate; counts are never "
         "combined.", "",
         f"Event cells with counts: {c['event_cells_with_counts']:,}; suppressed by the census sample floor or not "
         f"defined: {c['event_cells_suppressed_by_census_floor']:,}. Ratio values computed: "
         f"{c['ratio_values_computed']:,}; insufficient sample (event floor): {c['ratio_values_insufficient_sample']:,}.",
         "", "No overall score and no model ranking are produced. Differences are measured differences for the stated "
         "population, reference, threshold and period only.", ""]
    single = R[R["comparison"] == "single-model"]
    for role, exp, title in (("primary", "B3", "Primary — IMD, pooled, all seasons, leads 1–6"),
                             ("secondary", "B4", "Secondary — ERA5, pooled, all seasons, leads 1–6")):
        D = single[(single["role"] == role) & (single["experiment"] == exp)]
        L += [f"## {title}", ""] + (_table(D) if len(D) else ["No cell met the floor."]) + [""]
    L += ["## Source-resolution limitation (reporting note — not a measured forecast error)", "",
          "GFS rainfall, nominal leads 5–7: the source representation change is established; its effect on "
          "verification metrics is unresolved (VM-1.1 §21). Rows are marked in `limitations`. No data were corrected "
          "or excluded. A discontinuity at these leads is not evidence of forecast-skill improvement or degradation.", ""]
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
