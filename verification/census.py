"""M4.4-A Gate 1: eligibility / sample census. COUNTS ONLY — no error, bias, MAE, RMSE or event metric is computed.

Eligibility (VM-1.0 §6), per (experiment, model, variable, nominal lead, valid date, point):
  forecast available (24/24 h, no A-D reason) AND reference available (no E-G reason) AND same variable and window
  AND spatial rule (ERA5 grid <= 30 km; IMD cell <= 30 km; METAR matched station only) AND nominal lead 1-7.
Exclusion reason: the forecast's category if the forecast is unavailable, else the reference's category.
Missing values are never zero: an eligible pair must have both values present, otherwise the census refuses.
"""
from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

from common import (EXPERIMENTS, ERA5_MAX_GRID_KM, HIGH_ALTITUDE_M, IMD_MAX_KM, LEADS, MODELS, RAINY_DAY_MM, REGIONS,
                    SEASONS, STATE_REGION, CensusError, classify_reason, floor_status)

CATS = list("ABCDEFG")
LIMITATIONS = {
    "A1": ["ERA5-reanalysis-not-observation", "ERA5-ECMWF-lineage", "point-vs-grid"],
    "A2": ["METAR-station-level-only", "METAR-integer-degC", "METAR-half-hourly-sampling"],
    "A3": ["IMD-2026-not-published", "IMD-islands-no-cell-within-30km", "point-vs-grid"],
    "A4": ["ERA5-reanalysis-not-observation", "ERA5-rain-secondary", "point-vs-grid"],
}
COMBOS = [MODELS] + [c for c in itertools.combinations(MODELS, 2)]


def pairs_for_month(md: dict, overrides: dict) -> pd.DataFrame:
    M, pairing = md["matched"], {p["point_id"]: p for p in md["pairing"]["pairs"]}
    out = []
    for exp, spec in EXPERIMENTS.items():
        s = M[M["variable"].isin(spec["variables"]) & (M["reference"] == spec["reference"])].copy()
        if s.empty:
            raise CensusError(f"{md['tag']}: no rows for {exp}")
        if (s["window"] != spec["window"]).any():
            raise CensusError(f"{md['tag']} {exp}: window differs from {spec['window']} (rain-day windows never mixed)")
        if not s["nominal_lead_day"].isin(LEADS).all():
            raise CensusError(f"{md['tag']} {exp}: nominal lead outside 1-7")
        # forecast category (with verified annotation overrides)
        fc = s["forecast_reason"].map(classify_reason)
        keys = list(zip(s["model"], s["point_id"], s["variable"], s["nominal_lead_day"].astype(int), s["valid_date_ist"]))
        ov = pd.Series([overrides.get(k) for k in keys], index=s.index)
        fc = ov.where(ov.notna(), fc)
        if (s["forecast_available"] & fc.notna()).any() or (~s["forecast_available"] & fc.isna()).any():
            raise CensusError(f"{md['tag']} {exp}: forecast availability inconsistent with its reason")
        rc = s["reference_reason"].map(classify_reason)
        if (s["reference_available"] & rc.notna()).any() or (~s["reference_available"] & rc.isna()).any():
            raise CensusError(f"{md['tag']} {exp}: reference availability inconsistent with its reason")
        # spatial rules
        dist = pd.to_numeric(s["ref_distance_km"], errors="coerce")
        if spec["reference"] == "era5":
            spatial_ok = dist <= ERA5_MAX_GRID_KM
        elif spec["reference"] == "imd_rf025":
            spatial_ok = dist <= IMD_MAX_KM
        else:
            spatial_ok = s["point_id"].map(lambda p: pairing[p]["paired"])
        spatial_ok = spatial_ok.fillna(False).astype(bool)
        eligible = s["forecast_available"] & s["reference_available"] & spatial_ok
        reason = fc.where(~s["forecast_available"], rc)
        reason = reason.where(~(s["forecast_available"] & s["reference_available"] & ~spatial_ok), "G")
        reason = reason.where(~eligible, None)
        if (eligible & (s["forecast_value"].isna() | s["reference_value"].isna())).any():
            raise CensusError(f"{md['tag']} {exp}: eligible pair without a value (missing is never zero)")
        if (~eligible & reason.isna()).any():
            raise CensusError(f"{md['tag']} {exp}: excluded pair without a reason")
        state = s["point_id"].map(lambda p: pairing[p]["state"])
        unknown = set(state) - set(STATE_REGION)
        if unknown:
            raise CensusError(f"{md['tag']}: states without a region {sorted(unknown)}")
        elev = s["point_id"].map(lambda p: pairing[p]["point_elev_m"])
        out.append(pd.DataFrame({
            "experiment": exp, "model": s["model"].values, "variable": s["variable"].values,
            "window": spec["window"], "reference": spec["reference"], "lead": s["nominal_lead_day"].astype(int).values,
            "date": s["valid_date_ist"].values, "month": md["month"], "point_id": s["point_id"].values,
            "region": state.map(STATE_REGION).values, "high_altitude": (elev >= HIGH_ALTITUDE_M).values,
            "point_elev_m": elev.values,
            "station": s["point_id"].map(lambda p: pairing[p]["station"] if pairing[p]["paired"] else None).values,
            "season": SEASONS[int(md["month"][5:7])],
            "eligible": eligible.values, "reason": reason.values,
            "rainy": (eligible & (s["reference_value"] >= RAINY_DAY_MM)).values if spec.get("rainy_split") else False,
        }))
    return pd.concat(out, ignore_index=True)


def _slices(P: pd.DataFrame):
    """(slice_type, slice_value, floor_kind, mask) for pooled experiments."""
    yield "pooled", "all-points", "pooled", np.ones(len(P), bool)
    for r in REGIONS:
        yield "region", r, "region", (P["region"] == r).values
    yield "high_altitude", ">=1000m", "high_altitude", P["high_altitude"].values
    yield "high_altitude", "<1000m", "high_altitude", ~P["high_altitude"].values


def _count(g: pd.DataFrame) -> dict:
    e = g[g["eligible"]]
    d = {"n_total": len(g), "n_eligible": len(e), "n_dates": e["date"].nunique(), "n_points": e["point_id"].nunique(),
         "n_excluded": int((~g["eligible"]).sum())}
    rc = g["reason"].value_counts()
    for c in CATS:
        d[f"excluded_{c}"] = int(rc.get(c, 0))
    return d


def census(P: pd.DataFrame) -> pd.DataFrame:
    rows = []
    seasons = ["all"] + ["winter", "pre-monsoon", "monsoon", "post-monsoon"]
    for exp, spec in EXPERIMENTS.items():
        X = P[P["experiment"] == exp]
        geo = ([("station", st, "station", (X["station"] == st).values) for st in sorted(X["station"].dropna().unique())]
               if spec["geo"] == "station" else list(_slices(X)))
        strata = ["all", f"reference>={RAINY_DAY_MM}mm"] if spec.get("rainy_split") else ["all"]
        for (gtype, gval, fkind, gmask), season in itertools.product(geo, seasons):
            S = X[gmask] if season == "all" else X[gmask & (X["season"] == season).values]
            kind = fkind if not (fkind == "pooled" and season != "all") else "season"
            for stratum in strata:
                for (model, var, lead), g in S.groupby(["model", "variable", "lead"], sort=True):
                    if stratum != "all":
                        g = g[g["rainy"]]
                    c = _count(g)
                    if stratum != "all":   # the split applies to eligible pairs only; exclusions belong to "all"
                        c.update({"n_total": c["n_eligible"], "n_excluded": 0, **{f"excluded_{k}": 0 for k in CATS}})
                    status, rule = floor_status(kind, c["n_eligible"], c["n_dates"], c["n_points"])
                    rows.append({"experiment": exp, "comparison": "single-model", "model": model, "variable": var,
                                 "window": spec["window"], "reference": spec["reference"], "lead": int(lead),
                                 "geo_slice_type": gtype, "geo_slice": gval, "season": season, "stratum": stratum,
                                 **c, "floor_rule": rule, "status": status,
                                 "limitations": ";".join(LIMITATIONS[exp] + (["high-altitude"] if gval == ">=1000m" else []))})
                # shared-data (intersection) samples for paired comparisons: every model in the combo eligible
                E = S[S["eligible"]] if stratum == "all" else S[S["rainy"]]
                pres = (E.assign(v=True).pivot_table(index=["variable", "lead", "point_id", "date"], columns="model",
                                                     values="v", aggfunc="any", fill_value=False))
                for var, lead in itertools.product(spec["variables"], sorted(S["lead"].unique())):
                    for combo in COMBOS:
                        if pres.empty or not set(combo) <= set(pres.columns):
                            sub = pres.iloc[0:0]
                        else:
                            try:
                                sub = pres.xs((var, lead), level=["variable", "lead"])
                            except KeyError:
                                sub = pres.iloc[0:0]
                            sub = sub[sub[list(combo)].all(axis=1)] if len(sub) else sub
                        idx = sub.index if len(sub) else pd.MultiIndex.from_tuples([], names=["point_id", "date"])
                        n = len(idx)
                        nd = len(set(idx.get_level_values("date"))) if n else 0
                        npt = len(set(idx.get_level_values("point_id"))) if n else 0
                        status, rule = floor_status(kind, n, nd, npt)
                        note = ""
                        if "icon_global" in combo and lead == 7:
                            note = "not defined: ICON lead 7 not provided by source (A)"
                        rows.append({"experiment": exp, "comparison": "shared-data:" + "+".join(combo), "model": None,
                                     "variable": var, "window": spec["window"], "reference": spec["reference"],
                                     "lead": int(lead), "geo_slice_type": gtype, "geo_slice": gval, "season": season,
                                     "stratum": stratum, "n_total": None, "n_eligible": n, "n_dates": nd,
                                     "n_points": npt, "n_excluded": None, **{f"excluded_{k}": None for k in CATS},
                                     "floor_rule": rule, "status": status if not note else "not defined",
                                     "limitations": ";".join(LIMITATIONS[exp] + ([note] if note else []))})
    C = pd.DataFrame(rows)
    return C.sort_values(["experiment", "comparison", "model", "variable", "lead", "geo_slice_type", "geo_slice",
                          "season", "stratum"], na_position="first", kind="mergesort").reset_index(drop=True)


def exclusions(P: pd.DataFrame) -> pd.DataFrame:
    """Experiment-level exclusion totals by model, variable, lead and category (includes METAR-unmatched points)."""
    X = P[~P["eligible"]]
    t = X.groupby(["experiment", "model", "variable", "lead", "reason"]).size().rename("n_excluded").reset_index()
    return t.sort_values(["experiment", "model", "variable", "lead", "reason"], kind="mergesort").reset_index(drop=True)
