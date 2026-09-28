"""Pure functions (no network) that turn source responses into historical / reference / matched rows (M4.2-M4.3).

Every unavailable value carries a reason and expected / present / missing counts. Nothing is filled."""
from __future__ import annotations

import math
import re
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

import numpy as np

from common import (AGG_TEXT, HOURLY, LEAD_BASIS, MATCH_MAP, NOT_COMPARABLE, REF_LABEL, aggregate_daily, haversine_km,
                    known_not_provided, parse_hourly_times)

IST = timezone(timedelta(hours=5, minutes=30))
KT_TO_KMH = 1.852
MILE_TO_KM = 1.609344


def _agg_text(how: str, window: str) -> str:
    return AGG_TEXT[window].format(how=how)


# ------------------------------------------------------------------ Open-Meteo previous runs -> historical rows
def rows_from_previous_runs(resp: list[dict], points: list[dict], model: str, om_model: str, hourly: list[str],
                            leads: list[int], days: list[date], url: str, retrieved: datetime) -> list[dict]:
    if len(resp) != len(points):
        raise ValueError(f"{len(resp)} responses for {len(points)} points")
    out = []
    # a (variable, lead) column empty at every point and hour of the request = the source does not provide it
    col_empty = {(var, n): all(all(v is None for v in ((r.get("hourly") or {}).get(f"{var}_previous_day{n}") or []))
                                for r in resp) for var in hourly for n in leads}
    for p, r in zip(points, resp):
        h = r.get("hourly") or {}
        times = parse_hourly_times(h.get("time", []))
        for var in hourly:
            for n in leads:
                vals = h.get(f"{var}_previous_day{n}")
                if vals is None:
                    vals = [None] * len(times)   # source returned no such column: every day absent
                if col_empty[(var, n)]:
                    why = (f"not provided by source: {model} has no {var} at nominal lead {n} (M4.2 coverage matrix)"
                           if known_not_provided(model, var, n) else
                           f"source returned no {var} at nominal lead {n} for any point in the whole request period "
                           f"(unexpected; listed as an anomaly)")
                else:
                    why = None
                for dv, unit, how, window in HOURLY[var]:
                    for d, v, npres in aggregate_daily(times, vals, how, window, days):
                        reason = None if v is not None else (
                            why or f"source hours missing: {24 - npres} of 24 (no interpolation, no substitution)")
                        out.append({
                            "dataset": "historical_backfill", "point_id": p["id"], "lat": p["lat"], "lon": p["lon"],
                            "model": model, "om_model": om_model, "source": "open-meteo previous-runs api",
                            "source_url": url.split("?")[0] + f"?models={om_model}&hourly={var}_previous_day{n}",
                            "run_time_utc": None, "run_time_known": False, "nominal_lead_day": n,
                            "lead_basis": LEAD_BASIS.format(n=n), "valid_date_ist": d, "variable": dv, "value": v,
                            "unit": unit, "hours_expected": 24, "hours_present": npres, "hours_missing": 24 - npres,
                            "complete": v is not None, "reason": reason,
                            "aggregation": _agg_text(how, window), "retrieved_at_utc": retrieved})
    return out


def hours_present(resp: dict, var: str, n: int) -> int:
    vals = (resp.get("hourly") or {}).get(f"{var}_previous_day{n}")
    return 0 if vals is None else sum(v is not None for v in vals)


# ------------------------------------------------------------------ ERA5 -> reference rows
def rows_from_era5(resp: list[dict], points: list[dict], hourly: list[str], days: list[date], url: str,
                   retrieved: datetime) -> list[dict]:
    out = []
    for p, r in zip(points, resp):
        h = r.get("hourly") or {}
        times = parse_hourly_times(h.get("time", []))
        glat, glon = r.get("latitude"), r.get("longitude")
        dist = haversine_km(p["lat"], p["lon"], glat, glon) if glat is not None else None
        for var in hourly:
            vals = h.get(var) or [None] * len(times)
            for dv, unit, how, window in HOURLY[var]:
                for d, v, npres in aggregate_daily(times, vals, how, window, days):
                    out.append(_ref("era5", "reanalysis", p, "era5_grid", glat, glon, dist, None, d, dv, v, unit,
                                    npres, 24, v is not None,
                                    None if v is not None else f"ERA5 hours missing: {24 - npres} of 24",
                                    _agg_text(how, window), url.split("?")[0] + "?models=era5",
                                    retrieved, "ERA5 reanalysis: a model-based estimate constrained by observations, "
                                              "not an observation; ~6-day availability lag"))
    return out


def _ref(ref, rtype, p, site, slat, slon, dist, delev, d, var, val, unit, nobs, nexp, complete, reason, agg, url,
         retrieved, note):
    return {"dataset": "reference", "reference": ref, "reference_type": rtype, "reference_label": REF_LABEL[ref],
            "point_id": p["id"], "site_id": site, "site_lat": slat, "site_lon": slon, "distance_km": dist,
            "elev_diff_m": delev, "valid_date_ist": d, "variable": var, "value": val if complete else None, "unit": unit,
            "n_obs": nobs, "n_expected": nexp, "n_missing": max(0, nexp - nobs), "complete": complete,
            "reason": None if complete else (reason or "unavailable"), "aggregation": agg, "source_url": url,
            "retrieved_at_utc": retrieved, "note": note}


# ------------------------------------------------------------------ METAR station pairing
def pair_stations(points: list[dict], stations: list[dict], point_elev: dict, max_km: float, max_delev_m: float):
    """Nearest METAR station to each point. `paired` only under the proposed rule (distance and elevation)."""
    out = []
    for p in points:
        best = min(stations, key=lambda s: haversine_km(p["lat"], p["lon"], s["lat"], s["lon"]))
        dist = haversine_km(p["lat"], p["lon"], best["lat"], best["lon"])
        pe = point_elev.get(p["id"])
        de = (best["elev_m"] - pe) if (pe is not None and best.get("elev_m") is not None) else None
        reasons = []
        if dist > max_km:
            reasons.append(f"nearest station {dist:.0f} km > {max_km:.0f} km")
        if de is None:
            reasons.append("elevation difference unknown")
        elif abs(de) > max_delev_m:
            reasons.append(f"elevation difference {de:+.0f} m exceeds ±{max_delev_m:.0f} m")
        out.append({"point_id": p["id"], "district": p.get("district"), "state": p.get("state"),
                    "station": best["id"], "station_name": best.get("name"), "station_lat": best["lat"],
                    "station_lon": best["lon"], "distance_km": round(dist, 1), "point_elev_m": pe,
                    "station_elev_m": best.get("elev_m"), "elev_diff_m": None if de is None else round(de, 1),
                    "paired": not reasons, "reason_not_paired": "; ".join(reasons) or None})
    return out


# ------------------------------------------------------------------ METAR -> reference rows
def _num(x):
    try:
        v = float(x)
        return None if math.isnan(v) else v
    except (TypeError, ValueError):
        return None


def metar_daily(obs: list[dict], pair: dict, point: dict, days: list[date], url: str, retrieved: datetime,
                min_obs: int = 20) -> list[dict]:
    """Daily IST values from METARs. A day is complete when it has >= min_obs reports of that field AND at least
    one in each 6-hour IST block (so a max/min is not taken from half a day). Rain amounts are never used."""
    seen, by_day = set(), defaultdict(list)
    for o in obs:
        t = o.get("valid")
        if not t or t in seen:
            continue
        seen.add(t)
        ts = datetime.strptime(t, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).astimezone(IST)
        by_day[ts.date()].append((ts.hour // 6, o))
    out = []
    site = (pair["station"], pair["station_lat"], pair["station_lon"], pair["distance_km"], pair["elev_diff_m"])
    note = "METAR at the nearest airport; point observation, may not represent the district; integer degC"

    def add(d, var, val, unit, nobs, complete, reason, agg, extra=""):
        out.append(_ref("metar", "station_observation", point, *site, d, var, val, unit, nobs, min_obs, complete,
                        reason, agg, url, retrieved, note + extra))

    def coverage(blocks_n):
        n, blocks = blocks_n
        ok = n >= min_obs and blocks == {0, 1, 2, 3}
        why = []
        if n < min_obs:
            why.append(f"{n} reports < {min_obs} required")
        miss = sorted({0, 1, 2, 3} - blocks)
        if miss:
            why.append("no report in IST 6-h block(s) " + ", ".join(f"{b * 6:02d}-{b * 6 + 6:02d}h" for b in miss))
        return ok, ("incomplete reporting coverage: " + "; ".join(why)) if why else None

    for d in days:
        recs = by_day.get(d, [])

        def field(name, conv=lambda v: v):
            vals = [(b, _num(o.get(name))) for b, o in recs]
            vals = [(b, conv(v)) for b, v in vals if v is not None]
            ok, why = coverage((len(vals), {b for b, _ in vals}))
            return [v for _, v in vals], ok, why

        t, ok, why = field("tmpc")
        add(d, "tmax", max(t) if ok else None, "degC", len(t), ok, why, "max of METAR temperatures in the IST day")
        add(d, "tmin", min(t) if ok else None, "degC", len(t), ok, why, "min of METAR temperatures in the IST day")
        w, ok, why = field("sknt", lambda v: v * KT_TO_KMH)
        add(d, "wind_max", max(w) if ok else None, "km/h", len(w), ok, why,
            "max sustained (10-min mean) wind reported in the IST day; not a gust")
        g = [v * KT_TO_KMH for v in (_num(o.get("gust")) for _, o in recs) if v is not None]
        gok = ok and bool(g)
        add(d, "gust_max_reported", max(g) if gok else None, "km/h", len(g), gok,
            why or "no gust group reported (METAR reports gusts only when present; absence is not zero)",
            "max gust group reported in the IST day",
            "; METAR reports a gust only when present: no gust group does not mean zero gust")
        vis, ok, why = field("vsby", lambda v: v * MILE_TO_KM)
        add(d, "vis_min", min(vis) if ok else None, "km", len(vis), ok, why,
            "min reported visibility in the IST day (METAR caps at ~10 km)")
        codes = [(o.get("wxcodes") or "") for _, o in recs]
        codes = ["" if c == "M" else c for c in codes]
        rok, why = coverage((len(recs), {b for b, _ in recs}))
        for var, pat in (("ts_reports", r"TS"), ("fg_reports", r"FG"), ("ra_reports", r"RA|DZ")):
            cnt = sum(bool(re.search(pat, c)) for c in codes)
            add(d, var, float(cnt) if rok else None, "reports", len(recs), rok, why,
                f"number of METARs in the IST day whose weather group contains {pat.replace('|', ' or ')}",
                "; occurrence only — METAR rain amounts are never used")
    return out


# ------------------------------------------------------------------ IMD gridded rainfall -> reference rows
def imd_find_names(ds):
    var = next((v for v in ds.data_vars if v.lower() in ("rainfall", "rf", "rain")), None)
    lat = next((c for c in ds.coords if c.lower() in ("lat", "latitude")), None)
    lon = next((c for c in ds.coords if c.lower() in ("lon", "longitude")), None)
    tim = next((c for c in ds.coords if c.lower() in ("time",)), None)
    if not all((var, lat, lon, tim)):
        raise ValueError(f"unexpected IMD file layout: vars {list(ds.data_vars)}, coords {list(ds.coords)}")
    return var, lat, lon, tim


def imd_rows(ds, points: list[dict], max_km: float, url: str, file_sha: str, retrieved: datetime,
             days_wanted: set | None = None):
    """Daily rain at the nearest valid IMD cell within max_km (decision B4). Beyond max_km: unavailable rows."""
    var, latn, lonn, timn = imd_find_names(ds)
    a = ds[var].values.astype("float64")
    a = np.where(a < 0, np.nan, a)   # IMD fill values are negative when present
    lats, lons = ds[latn].values, ds[lonn].values
    valid_all = np.isfinite(a).all(axis=0)
    valid_any = np.isfinite(a).any(axis=0)
    times = [np.datetime64(t, "D").astype(object) for t in ds[timn].values]
    cells = [(i, j) for i in range(len(lats)) for j in range(len(lons)) if valid_all[i, j]]
    info, out = [], []
    for p in points:
        best = min(cells, key=lambda c: haversine_km(p["lat"], p["lon"], lats[c[0]], lons[c[1]]))
        dist = haversine_km(p["lat"], p["lon"], lats[best[0]], lons[best[1]])
        oi = int(np.abs(lats - p["lat"]).argmin()); oj = int(np.abs(lons - p["lon"]).argmin())
        own_valid = bool(valid_all[oi, oj]) and haversine_km(p["lat"], p["lon"], lats[oi], lons[oj]) < 20
        usable = dist <= max_km
        info.append({"point_id": p["id"], "cell_lat": float(lats[best[0]]), "cell_lon": float(lons[best[1]]),
                     "distance_km": round(dist, 1), "own_cell_valid": own_valid, "usable": usable,
                     "label": ("own grid cell" if own_valid else "nearby grid cell") if usable
                     else f"IMD rainfall unavailable (nearest valid cell {dist:.0f} km > {max_km:.0f} km)"})
        site = f"{float(lats[best[0]]):.2f},{float(lons[best[1]]):.2f}"
        for k, fd in enumerate(times):
            # IMD file date = the day the 24 h ends (08:30 IST). Probe run 36373096319: IMD vs ERA5 r = 0.67 with
            # this alignment, 0.22 with the file date taken as the window start. Stored date = window START.
            d = fd - timedelta(days=1)
            if days_wanted is not None and d not in days_wanted:
                continue
            v = a[k, best[0], best[1]] if usable else np.nan
            ok = usable and bool(np.isfinite(v))
            reason = None if ok else (f"no IMD cell within {max_km:.0f} km (nearest valid cell {dist:.0f} km)"
                                      if not usable else "IMD value missing in the source file")
            out.append(_ref("imd_rf025", "gridded_gauge_analysis", p, site if usable else "none",
                            float(lats[best[0]]) if usable else None, float(lons[best[1]]) if usable else None,
                            dist, None, d, "precip_0830", float(v) if ok else None, "mm", 1 if ok else 0, 1, ok, reason,
                            "IMD 0.25 deg gridded daily rainfall (rain-gauge analysis): 24 h from 08:30 IST on valid_date_ist to "
                            "08:30 IST the next day (IMD file date = next day, the end of the window)",
                            url + f" (file sha256 {file_sha})", retrieved,
                            ("own cell" if own_valid else f"nearby grid cell {dist:.0f} km") if usable
                            else f"unavailable: nearest valid IMD cell {dist:.0f} km away (limit {max_km:.0f} km)"))
    meta = {"valid_cells_all_days": int(valid_all.sum()), "valid_cells_any_day": int(valid_any.sum()),
            "days": len(times), "first_file_day": str(times[0]), "last_file_day": str(times[-1])}
    return out, info, meta


# ------------------------------------------------------------------ matched forecast/reference rows (M4.3)
def build_matched(F, R, pairing: dict, missing_ref_reason: dict):
    """One row per historical forecast value x applicable reference (MATCH_MAP). No values are changed or filled.

    F: forecast rows (HIST_SCHEMA DataFrame); R: reference rows (REF_SCHEMA DataFrame);
    pairing: point_id -> METAR pairing record; missing_ref_reason: reference -> reason when a row is absent
    (e.g. the IMD year file is not published). Unavailable references never mark a forecast as failed."""
    import pandas as pd
    parts = []
    key = ["point_id", "valid_date_ist"]
    for var, refs in MATCH_MAP.items():
        f = F[F["variable"] == var]
        if f.empty:
            continue
        base = pd.DataFrame({
            "dataset": "matched_historical", "point_id": f["point_id"].values, "model": f["model"].values,
            "run_time_known": False, "nominal_lead_day": f["nominal_lead_day"].values,
            "lead_basis": [f"nominal previous_day{n}" for n in f["nominal_lead_day"].values],
            "valid_date_ist": f["valid_date_ist"].values, "variable": var,
            "window": "imd_0830" if var == "precip_0830" else "ist_day", "unit": f["unit"].values,
            "forecast_value": f["value"].values, "forecast_available": f["complete"].values,
            "forecast_reason": f["reason"].values})
        for ref, rvar in refs:
            m = base.copy()
            m["reference"], m["reference_label"], m["reference_variable"] = ref, REF_LABEL[ref], rvar
            if rvar is None:
                m["reference_value"], m["reference_available"] = None, False
                m["reference_reason"] = NOT_COMPARABLE[(ref, var)]
                m["ref_site_id"], m["ref_distance_km"], m["ref_elev_diff_m"] = None, None, None
                parts.append(m)
                continue
            r = R[(R["reference"] == ref) & (R["variable"] == rvar)][
                key + ["value", "complete", "reason", "site_id", "distance_km", "elev_diff_m"]]
            m = m.merge(r, on=key, how="left", validate="many_to_one")
            absent = m["complete"].isna()
            m["reference_value"] = m.pop("value")
            m["reference_available"] = m.pop("complete").fillna(False).astype(bool)
            reason = m.pop("reason").astype(object)
            if ref == "metar":
                unpaired = m["point_id"].map(lambda pid: not pairing[pid]["paired"])
                reason[absent & unpaired] = m.loc[absent & unpaired, "point_id"].map(
                    lambda pid: "no METAR match: " + pairing[pid]["reason_not_paired"])
                reason[absent & ~unpaired] = "no METAR reports retrieved for this IST day"
                m = m.astype({"site_id": object, "distance_km": "float64", "elev_diff_m": "float64"})
                for col, src in (("site_id", "station"), ("distance_km", "distance_km"), ("elev_diff_m", "elev_diff_m")):
                    m.loc[absent, col] = m.loc[absent, "point_id"].map(lambda pid, s=src: pairing[pid][s])
            else:
                reason[absent] = missing_ref_reason.get(ref, f"{REF_LABEL[ref]} not available for this day")
            m["reference_reason"] = reason.where(~m["reference_available"], None)
            m = m.rename(columns={"site_id": "ref_site_id", "distance_km": "ref_distance_km",
                                  "elev_diff_m": "ref_elev_diff_m"})
            parts.append(m)
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
