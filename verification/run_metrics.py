"""Run M4.4-A Gate 2: bias, MAE, RMSE with 95% block-bootstrap intervals, for census cells that meet the floor only.

  python verification/run_metrics.py --census DIR --out DIR [--cache DIR]

Integrity before any metric (VM-1.1 §17): every release is verified (published, immutable, manifest SHA-256 equal to
the archive-index record, every file SHA-256 equal to the manifest); annotations are applied only if their hashes
match (the February 2024 ECMWF archive-start annotation is required when that month is used); the census is
recomputed from the verified data and must be byte-identical to the published census whose hash is recorded; the
census must have been built from the same releases. Any mismatch refuses the run. Only our own releases and the
archive-index branch are read; no weather-data service is contacted.

Only cells with census status "meets floor" are computed. No value is computed for any other cell.
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
from census import COMBOS, census, pairs_for_month  # noqa: E402
from common import (CENSUS_VERSION, EXPERIMENTS, METHODOLOGY_VERSION, MODELS, UNITS, CensusError)  # noqa: E402
from inputs import GitHubSource, annotation_overrides, load_index, load_month  # noqa: E402
import metrics as MX  # noqa: E402
from run_census import _commit  # noqa: E402

GATE = "M4.4-A Gate 2 (bias, MAE, RMSE)"
FEB_ANNOTATION = "2024-02-ecmwf-archive-start"
PRIMARY_LEADS = range(1, 7)
REF_LABEL = {"era5": "ERA5 reanalysis", "metar": "METAR station observations", "imd_rf025": "IMD gridded rain-gauge analysis"}
VAR_LABEL = {"tmax": "Tmax", "tmin": "Tmin", "precip": "rain (IST day)", "precip_0830": "rain (08:30-08:30 IST)"}
COLUMNS = ["cell_id", "experiment", "comparison", "subject", "model_a", "model_b", "variable", "window", "reference",
           "lead", "geo_slice_type", "geo_slice", "season", "stratum", "n", "n_dates", "n_points", "n_blocks",
           "period_start", "period_end", "metric", "value", "ci_low", "ci_high", "unit", "interval_excludes_zero",
           "role", "role_basis", "high_altitude_slice", "point_elev_m", "metar_elev_diff_m", "seed", "limitations",
           "statement"]


def cell_id(r) -> str:
    return (f"{r['experiment']}|{r['comparison']}|{r['model'] if isinstance(r['model'], str) else '-'}|{r['variable']}|"
            f"L{int(r['lead'])}|{r['geo_slice_type']}={r['geo_slice']}|{r['season']}|{r['stratum']}")


def role(r) -> tuple[str, str]:
    """VM-1.1 §21 declared primary comparisons; everything else is exploratory (with the reasons)."""
    why = []
    if r["reference"] == "era5":
        why.append("ERA5 comparison")
    if r["season"] != "all":
        why.append("seasonal slice")
    if r["geo_slice_type"] == "region":
        why.append("regional slice")
    if r["geo_slice_type"] == "high_altitude":
        why.append("elevation diagnostic")
    if int(r["lead"]) not in PRIMARY_LEADS:
        why.append("lead 7")
    if r["stratum"] != "all":
        why.append("rainy-day stratum")
    if r["comparison"].count("+") >= 2:
        why.append("three-model shared sample")
    if why:
        return "exploratory", "; ".join(why)
    if r["experiment"] == "A2":
        return "primary", "temperature vs METAR, station meeting the floor, all seasons, leads 1-6"
    if r["experiment"] == "A3":
        return "primary", "rain vs IMD, pooled eligible points, all seasons, all days, leads 1-6"
    return "exploratory", "not a declared primary comparison"


def _mask(D: pd.DataFrame, r) -> np.ndarray:
    t, v = r["geo_slice_type"], r["geo_slice"]
    if t == "pooled":
        m = np.ones(len(D), bool)
    elif t == "region":
        m = (D["region"] == v).values
    elif t == "high_altitude":
        m = D["high_altitude"].values if v == ">=1000m" else ~D["high_altitude"].values
    elif t == "station":
        m = (D["station"] == v).values
    else:
        raise CensusError(f"unknown slice type {t}")
    m = np.array(m, dtype=bool)                                   # own, writable copy
    if r["season"] != "all":
        m &= (D["season"] == r["season"]).values
    if r["stratum"] != "all":
        m &= D["rainy"].values.astype(bool)
    return m


def _check_counts(sub: pd.DataFrame, r, cid: str):
    got = (len(sub), sub["date"].nunique(), sub["point_id"].nunique())
    want = (int(r["n_eligible"]), int(r["n_dates"]), int(r["n_points"]))
    if got != want:
        raise CensusError(f"{cid}: metric sample {got} differs from the census {want}")


def _fmt(x: float) -> str:
    return f"{x:+.2f}" if x is not None else "n/a"


def _population(r, n_points) -> str:
    t, v = r["geo_slice_type"], r["geo_slice"]
    where = {"pooled": f"the {n_points} archive points with eligible pairs",
             "region": f"the {v} region ({n_points} points)",
             "high_altitude": f"archive points {'at' if v == '>=1000m' else 'below'} 1,000 m ({n_points} points)",
             "station": f"METAR station {v}"}[t]
    s = "" if r["season"] == "all" else f", {r['season']} season"
    k = "" if r["stratum"] == "all" else f", days with reference {r['stratum'].split('>=')[1]}"
    return where + s + k


def _rows_for(r, subject, res, sub, extra) -> list[dict]:
    unit = UNITS[r["variable"]]
    out = []
    for m in MX.METRICS:
        v, (lo, hi) = res[m]["value"], res[m]["ci"]
        diff = subject.startswith("difference")
        excl = bool(lo > 0 or hi < 0) if (diff or m == "bias") else None
        pop = _population(r, sub["point_id"].nunique())
        period = f"{sub['date'].min()} to {sub['date'].max()}"
        head = (f"{VAR_LABEL[r['variable']]} vs {REF_LABEL[r['reference']]}, nominal lead {int(r['lead'])}, {pop}, "
                f"{period}; n={len(sub):,} pairs, {sub['date'].nunique()} dates")
        if diff:
            st = (f"Measured {m.upper() if m != 'bias' else 'bias'} difference ({subject.split(': ')[1]}) on the shared-"
                  f"data sample: {_fmt(v)} {unit} (95% paired block-bootstrap interval {_fmt(lo)} to {_fmt(hi)}); "
                  f"the interval {'excludes' if excl else 'includes'} 0. {head}. This is a measured difference for "
                  f"this population, reference, metric and period only; it does not show that either model is "
                  f"better in general.")
        else:
            st = (f"Measured {m.upper() if m != 'bias' else 'bias'} of {subject}: {_fmt(v)} {unit} (95% block-"
                  f"bootstrap interval {_fmt(lo)} to {_fmt(hi)}). {head}.")
        out.append({**extra, "subject": subject, "metric": m, "value": v, "ci_low": lo, "ci_high": hi, "unit": unit,
                    "interval_excludes_zero": excl, "period_start": str(sub["date"].min()),
                    "period_end": str(sub["date"].max()), "statement": st})
    return out


def compute(P: pd.DataFrame, C: pd.DataFrame, station_elev: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Metric rows for census cells that meet the floor; and the list of suppressed cells (no value)."""
    todo = C[C["status"] == "meets floor"]
    supp = C[C["status"] != "meets floor"].copy()
    supp.insert(0, "cell_id", [cell_id(r) for _, r in supp.iterrows()])
    supp = supp[["cell_id", "experiment", "comparison", "model", "variable", "lead", "geo_slice_type", "geo_slice",
                 "season", "stratum", "n_eligible", "n_dates", "n_points", "status", "floor_rule"]]
    rows = []
    for exp in EXPERIMENTS:
        T = todo[todo["experiment"] == exp]
        if T.empty:
            continue
        E = P[(P["experiment"] == exp) & P["eligible"]].copy()
        E["e"] = E["forecast_value"].astype(np.float64) - E["reference_value"].astype(np.float64)
        if not np.isfinite(E["e"].values).all():
            raise CensusError(f"{exp}: non-finite error in an eligible pair")
        single = {k: g for k, g in E.groupby(["model", "variable", "lead"], sort=True)}
        attrs = ["point_id", "date", "region", "high_altitude", "station", "season", "rainy"]
        wide = {}
        for (var, lead), g in E.groupby(["variable", "lead"], sort=True):
            W = g.pivot(index=["point_id", "date"], columns="model", values="e")
            A = g.drop_duplicates(["point_id", "date"]).set_index(["point_id", "date"])[attrs[2:]]
            wide[(var, lead)] = W.join(A).reset_index()
        for _, r in T.iterrows():
            cid = cell_id(r)
            role_, basis = role(r)
            base = {"cell_id": cid, "experiment": exp, "comparison": r["comparison"], "variable": r["variable"],
                    "window": r["window"], "reference": r["reference"], "lead": int(r["lead"]),
                    "geo_slice_type": r["geo_slice_type"], "geo_slice": r["geo_slice"], "season": r["season"],
                    "stratum": r["stratum"], "role": role_, "role_basis": basis,
                    "high_altitude_slice": {">=1000m": True, "<1000m": False}.get(r["geo_slice"]),
                    "point_elev_m": None, "metar_elev_diff_m": None, "limitations": r["limitations"]}
            if r["geo_slice_type"] == "station":
                base["point_elev_m"], base["metar_elev_diff_m"] = station_elev[r["geo_slice"]]
            if r["comparison"] == "single-model":
                g = single[(r["model"], r["variable"], int(r["lead"]))]
                sub = g[_mask(g, r)]
                _check_counts(sub, r, cid)
                res = MX.bootstrap(sub["e"].values, sub["date"].values, cid)
                ext = {**base, "model_a": r["model"], "model_b": None, "n": len(sub), "n_dates": sub["date"].nunique(),
                       "n_points": sub["point_id"].nunique(), "n_blocks": res["n_blocks"], "seed": res["seed"]}
                rows += _rows_for(r, r["model"], res, sub, ext)
                continue
            combo = r["comparison"].split(":", 1)[1].split("+")
            W = wide[(r["variable"], int(r["lead"]))]
            if not set(combo) <= set(W.columns):
                raise CensusError(f"{cid}: shared-data sample has no pairs for {combo}")
            sub = W[_mask(W, r) & W[combo].notna().all(axis=1).values]
            _check_counts(sub, r, cid)
            ext = {**base, "n": len(sub), "n_dates": sub["date"].nunique(), "n_points": sub["point_id"].nunique()}
            if len(combo) == 2:
                a, b = combo
                res = MX.paired_bootstrap(sub[a].values, sub[b].values, sub["date"].values, cid)
                ext.update(model_a=a, model_b=b, n_blocks=res["n_blocks"], seed=res["seed"])
                rows += _rows_for(r, a, res["a"], sub, ext)
                rows += _rows_for(r, b, res["b"], sub, ext)
                rows += _rows_for(r, f"difference: {a} minus {b}", res["diff"], sub, ext)
            else:
                for mdl in combo:
                    res = MX.bootstrap(sub[mdl].values, sub["date"].values, cid)
                    rows += _rows_for(r, mdl, res, sub, {**ext, "model_a": mdl, "model_b": None,
                                                         "n_blocks": res["n_blocks"], "seed": res["seed"]})
    R = pd.DataFrame(rows, columns=COLUMNS)
    for c in ("value", "ci_low", "ci_high"):
        R[c] = R[c].astype(float).round(6)
    R = R.sort_values(["experiment", "cell_id", "subject", "metric"], kind="mergesort").reset_index(drop=True)
    return R, supp.sort_values("cell_id", kind="mergesort").reset_index(drop=True)


def _sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(source, out: pathlib.Path, census_dir: pathlib.Path, months: list[str] | None = None) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    # --- the published census (Gate 1 record) --------------------------------------------------------------------
    crec = json.loads((census_dir / "census_run.json").read_text())
    ccsv = census_dir / "census_cells.csv"
    if _sha(ccsv) != crec["result_sha256"]["census_cells.csv"]:
        raise CensusError("census_cells.csv does not match its recorded SHA-256 (tampered census refused)")
    if crec.get("census_version") != CENSUS_VERSION or crec.get("methodology_version") != METHODOLOGY_VERSION:
        raise CensusError(f"census {crec.get('census_version')}/{crec.get('methodology_version')} is not "
                          f"{CENSUS_VERSION}/{METHODOLOGY_VERSION}")
    if crec.get("metrics_computed") != "none":
        raise CensusError("the census record must be counts only")
    # --- verified releases ----------------------------------------------------------------------------------------
    recs, anns = load_index(source)
    months = months or crec["months"]
    if months != crec["months"]:
        raise CensusError("metric months differ from the census months")
    parts, prov, ann_notes, elev = [], [], [], {}
    for m in months:
        md = load_month(source, recs[m])
        over, notes = annotation_overrides(md, anns)
        if m == "2024-02" and not any(n["annotation"] == FEB_ANNOTATION for n in notes):
            raise CensusError(f"2024-02 used without the verified {FEB_ANNOTATION} annotation")
        ann_notes += [{"month": m, **n} for n in notes]
        parts.append(pairs_for_month(md, over))
        prov.append(md["provenance"])
        for p in md["pairing"]["pairs"]:
            if p["paired"]:
                elev.setdefault(p["station"], set()).add((p["point_elev_m"], p["elev_diff_m"]))
    if [(p["tag"], p["manifest_sha256"]) for p in prov] != [(p["tag"], p["manifest_sha256"]) for p in crec["releases"]]:
        raise CensusError("the census was built from different releases")
    if ann_notes != crec["annotations_applied"]:
        raise CensusError("annotations applied differ from the census record")
    station_elev = {}
    for st, v in elev.items():
        if len(v) != 1:
            raise CensusError(f"station {st}: elevation differs between months {sorted(v)}")
        station_elev[st] = next(iter(v))
    P = pd.concat(parts, ignore_index=True)
    C = census(P)
    if hashlib.sha256(C.to_csv(index=False).encode()).hexdigest() != crec["result_sha256"]["census_cells.csv"]:
        raise CensusError("the census recomputed from the verified releases differs from the published census")
    C_pub = pd.read_csv(ccsv)
    if len(C_pub) != len(C) or (C_pub["status"].values != C["status"].values).any():
        raise CensusError("published census cells do not line up with the recomputed census")
    # --- metrics ------------------------------------------------------------------------------------------------
    R, S = compute(P, C, station_elev)
    R.to_parquet(out / "metric_results.parquet", index=False)
    R.to_csv(out / "metric_results.csv", index=False)
    S.to_csv(out / "suppressed_cells.csv", index=False)
    meta = (R.drop_duplicates("cell_id")[["cell_id", "experiment", "comparison", "variable", "reference", "lead",
                                           "geo_slice_type", "geo_slice", "season", "stratum", "role", "role_basis"]])
    meta.to_csv(out / "comparison_metadata.csv", index=False)
    config = {"metrics": list(MX.METRICS), "error": "forecast - reference (float64 from the archived float32 values)",
              "ci_level": MX.CI_LEVEL, "ci_method": MX.CI_METHOD, "resamples": MX.BOOTSTRAP_RESAMPLES,
              "block_days": MX.BLOCK_DAYS, "block_origin": str(MX.BLOCK_ORIGIN), "master_seed": MX.BOOTSTRAP_SEED,
              "cell_seed": "first 8 bytes of SHA-256('<master_seed>|<cell_id>'), big-endian",
              "primary_leads": list(PRIMARY_LEADS), "cells": "census status 'meets floor' only",
              "rounding": "value, ci_low, ci_high rounded to 6 decimals"}
    cfg_sha = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    hashes = {n: _sha(out / n) for n in ("metric_results.csv", "suppressed_cells.csv", "comparison_metadata.csv")}
    cells = R.drop_duplicates("cell_id")
    rec = {
        "gate": GATE, "methodology_version": METHODOLOGY_VERSION, "census_version": CENSUS_VERSION,
        "census_id": f"{CENSUS_VERSION}@{crec['code_commit'][:7]}",
        "census_code_commit": crec["code_commit"], "census_cells_sha256": crec["result_sha256"]["census_cells.csv"],
        "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(), "code_commit": _commit(),
        "archive_index_commit": getattr(source, "index_commit", None), "models": list(MODELS), "months": months,
        "releases": prov, "annotations_applied": ann_notes, "config": config, "config_sha256": cfg_sha,
        "result_sha256": hashes,
        "counts": {"census_cells": int(len(C)), "cells_computed": int(len(cells)),
                   "cells_suppressed": int(len(S)),
                   "suppressed_by_status": {k: int(v) for k, v in S["status"].value_counts().sort_index().items()},
                   "metric_rows": int(len(R)),
                   "cells_by_role": {k: int(v) for k, v in cells["role"].value_counts().sort_index().items()}},
        "not_done": ["M4.4-B/C/D", "overall BWI score", "global model ranking", "event metrics", "gust"],
        "external_data_calls": "none (own immutable releases and archive-index only)",
    }
    (out / "metric_run.json").write_text(json.dumps(rec, indent=1, default=str) + "\n")
    (out / "metric_report.md").write_text(report(R, S, rec))
    return rec


def _tbl(D: pd.DataFrame) -> list[str]:
    L = ["| Cell | Subject | n | Bias [95% CI] | MAE [95% CI] | RMSE [95% CI] |", "| --- | --- | --- | --- | --- | --- |"]
    for (cid, subj), g in D.groupby(["cell_id", "subject"], sort=False):
        v = {m: g[g["metric"] == m].iloc[0] for m in MX.METRICS}
        f = lambda x: f"{x.value:+.2f} [{x.ci_low:+.2f}, {x.ci_high:+.2f}]" + (" †" if x.interval_excludes_zero else "")
        short = cid.replace("|pooled=all-points", "").replace("|all|all", "").replace("|", " · ")   # no raw pipes
        L.append(f"| {short} | {subj} | {int(v['bias'].n):,} | {f(v['bias'])} | {f(v['mae'])} | {f(v['rmse'])} |")
    return L


def report(R: pd.DataFrame, S: pd.DataFrame, rec: dict) -> str:
    c = rec["counts"]
    L = [f"# M4.4-A Gate 2 — bias, MAE, RMSE ({rec['methodology_version']}, census {rec['census_id']})", "",
         f"Months {rec['months'][0]} … {rec['months'][-1]} ({len(rec['months'])} verified immutable releases); code "
         f"{rec['code_commit'][:7]}; archive-index {str(rec['archive_index_commit'])[:7]}. Error = forecast − reference. "
         f"95% intervals: {rec['config']['ci_method']}, {rec['config']['resamples']} resamples, master seed "
         f"{rec['config']['master_seed']}.", "",
         f"Cells computed: **{c['cells_computed']:,}** (of {c['census_cells']:,} census cells); suppressed by the "
         f"publication floor or not defined: **{c['cells_suppressed']:,}** — no value was computed for them.", "",
         "Differences are measured differences for the stated population, reference, metric and period only. They do "
         "not show that any model is better in general. No overall score and no model ranking are produced. "
         "† = the 95% interval excludes 0 (bias and differences only).", ""]
    P = R[R["role"] == "primary"]
    for exp, title in (("A2", "Primary — temperature vs METAR (per station, all seasons, leads 1–6)"),
                       ("A3", "Primary — rain (08:30–08:30 IST) vs IMD (pooled, all seasons, all days, leads 1–6)")):
        L += [f"## {title}", ""]
        D = P[P["experiment"] == exp]
        L += (_tbl(D[D["comparison"] == "single-model"]) + ["", "Model pairs on shared data:", ""] +
              _tbl(D[D["comparison"] != "single-model"]) + [""]) if len(D) else ["No cell met the floor.", ""]
    X = R[R["role"] == "exploratory"]
    L += ["## Exploratory (not findings)", "",
          f"{X['cell_id'].nunique():,} cells. Full values in metric_results.csv. Pooled, all-season, single-model "
          "summary below; seasonal, regional, elevation, rainy-day, lead-7 and three-model cells are in the CSV.", ""]
    Xs = X[(X["geo_slice_type"] == "pooled") & (X["season"] == "all") & (X["stratum"] == "all") &
           (X["comparison"] == "single-model")]
    L += _tbl(Xs) + [""]
    L += ["## Suppressed cells (no value computed)", "", "| Experiment | Comparison | Status | Cells |",
          "| --- | --- | --- | --- |"]
    for (e, cmp_, st), n in S.groupby(["experiment", S["comparison"].str.split(":").str[0], "status"]).size().items():
        L.append(f"| {e} | {cmp_} | {st} | {n:,} |")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--census", required=True, help="directory holding the published census record")
    ap.add_argument("--out", required=True)
    ap.add_argument("--cache", default="/tmp/claude-0/verification-cache")
    a = ap.parse_args()
    rec = run(GitHubSource(pathlib.Path(a.cache)), pathlib.Path(a.out), pathlib.Path(a.census))
    print(json.dumps(rec["counts"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
