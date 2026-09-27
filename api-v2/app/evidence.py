"""Evidence engine: DATA → RULE → RESULT for one CORE risk at one point.

Every number here is copied or aggregated from a CORE /api/v1 response (dashboard, grid/point).
Aggregations (max/min/sum over the event window) are stated in the response. Nothing is
estimated, interpolated or substituted; missing data is reported as unavailable with a reason.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from .catalogue import (ANOMALY_ITEMS, E2S_EVIDENCE, INDEPENDENT_MODELS, LEVEL_NAME, MODEL_EVIDENCE,
                        MODEL_EVIDENCE_UNAVAILABLE, NORMAL_EVIDENCE, OFFICIAL_KEYWORDS, SATELLITE,
                        SATELLITE_LABEL, TITLE)
from .events import core_inconsistencies, impact_context, location_of, model_agreement, notice, official_alert

IST = timezone(timedelta(hours=5, minutes=30))
SECTION_ORDER = ["detected", "when", "model_agreement", "forecast_range", "normal_departure",
                 "earth2studio", "satellite", "official", "rule", "provenance"]


def _parse(ts: str | None) -> datetime | None:
    if not ts:
        return None
    d = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=IST)


def event_window(risk: dict, dash: dict) -> dict:
    """IST window the evidence values are taken over."""
    start, end = _parse(risk.get("period_start")), _parse(risk.get("period_end"))
    if start and end:
        return {"start": start.isoformat(), "end": end.isoformat(),
                "dates": _dates(start.astimezone(IST).date(), end.astimezone(IST).date()),
                "basis": "CORE risk period (period_start → period_end)"}
    days = [r["date"] for r in dash.get("daily", [])[:7]]
    return {"start": None, "end": None, "dates": days,
            "basis": "CORE does not give a period for this risk; values cover CORE's 7-day assessment horizon"}


def _dates(a: date, b: date) -> list[str]:
    out, d = [], a
    while d <= b:
        out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def _agg(vals: list[float], how: str) -> float | None:
    if not vals:
        return None
    return {"max": max, "min": min, "sum": sum}[how](vals) if how != "sum" else round(sum(vals), 1)


def forecast_range(risk_id: str, dash: dict, win: dict) -> dict:
    if risk_id not in MODEL_EVIDENCE:
        return {"available": False, "reason": MODEL_EVIDENCE_UNAVAILABLE.get(risk_id, "Not published by CORE.")}
    key, how, label, unit = MODEL_EVIDENCE[risk_id]
    rows = [r for r in dash.get("daily", []) if r["date"] in win["dates"]]
    per_model: dict[str, Any] = {}
    for mk, name in INDEPENDENT_MODELS.items():
        vals = [r["models"][mk][key] for r in rows if (r.get("models") or {}).get(mk, {}).get(key) is not None]
        per_model[name] = {"value": _agg(vals, how), "days": len(vals)}
    vs = [v["value"] for v in per_model.values() if v["value"] is not None]
    if not vs:
        return {"available": False, "reason": "CORE returned no per-model values for the event window."}
    lo, hi = min(vs), max(vs)
    return {
        "available": True, "variable": label, "unit": unit, "aggregation": how, "dates": [r["date"] for r in rows],
        "per_model": per_model, "min": lo, "max": hi,
        "text": f"{lo:g}–{hi:g} {unit}" if lo != hi else f"{lo:g} {unit}",
        "note": "Range between the independent models (ECMWF, GFS, ICON) — model spread, not a probability or confidence interval.",
        "source": "CORE /api/v1/dashboard daily[].models",
    }


def normal_departure(risk_id: str, dash: dict, win: dict) -> dict:
    anomaly = dash.get("anomaly") or {}
    base = anomaly.get("baseline") or {}
    baseline = {"source": base.get("source"), "model": base.get("model"), "notes": base.get("notes"),
                "label": "NASA POWER 1991–2020 (MERRA-2 reanalysis) — indicative; not IMD rainfall normals"}
    items = [it for it in anomaly.get("items") or [] if it.get("id") in ANOMALY_ITEMS.get(risk_id, [])]
    out: dict[str, Any] = {"baseline": baseline, "core_anomaly_items": items, "method": anomaly.get("method")}
    spec = NORMAL_EVIDENCE.get(risk_id)
    if not spec:
        out.update(available=bool(items), reason=None if items else "CORE publishes no normal for the variable behind this risk.")
        return out
    fkey, nkey, how, label, unit = spec
    rows = [r for r in dash.get("daily", []) if r["date"] in win["dates"] and r.get(fkey) is not None and r.get(nkey) is not None]
    if not rows:
        out.update(available=bool(items), reason="CORE daily rows lack forecast or normal values for the window.")
        return out
    if how == "sum":
        fc, nm, on = round(sum(r[fkey] for r in rows), 1), round(sum(r[nkey] for r in rows), 1), [r["date"] for r in rows]
    else:
        pick = max(rows, key=lambda r: r[fkey]) if how == "peak" else min(rows, key=lambda r: r[fkey])
        fc, nm, on = pick[fkey], pick[nkey], [pick["date"]]
    dep = round(fc - nm, 1)
    out.update(available=True, forecast={"label": label, "value": fc, "unit": unit, "dates": on, "source": "CORE best-match forecast (daily)"},
               normal={"value": nm, "unit": unit}, departure={"value": dep, "unit": unit,
               "pct": round(100 * dep / nm) if unit == "mm" and nm >= 5 else None},
               note="FORECAST is what the model expects; DEPARTURE is forecast minus the NASA POWER normal for the same calendar days.")
    return out


def earth2studio(risk_id: str, gp: dict | None, win: dict, err: str | None) -> dict:
    base = {"model": "GFS 0.25° via Earth2Studio (CORE grid store)",
            "note": "Earth2Studio here runs NOAA GFS. It is the same model as GFS above and is NOT counted as an independent model or in model agreement."}
    if risk_id not in E2S_EVIDENCE:
        return {**base, "available": False, "reason": "No Earth2Studio variable corresponds to this risk."}
    if gp is None:
        return {**base, "available": False, "reason": f"CORE /grid/point unavailable: {err}"}
    key, how, label, unit = E2S_EVIDENCE[risk_id]
    times = [_parse(t) for t in gp.get("time", [])]
    series = gp.get("series", {}).get(key, [])
    lo = _parse(win["start"]) if win["start"] else datetime.combine(date.fromisoformat(win["dates"][0]), datetime.min.time(), IST)
    hi = _parse(win["end"]) if win["end"] else datetime.combine(date.fromisoformat(win["dates"][-1]), datetime.max.time(), IST)
    sel = [(t, v) for t, v in zip(times, series) if t and v is not None and lo <= t <= hi]
    if not sel:
        return {**base, "available": False, "issue_time": gp.get("issue_time"),
                "reason": "The Earth2Studio GFS run does not cover the event window."}
    if how == "daymax":
        days: dict[str, float] = {}
        for t, v in sel:
            d = t.astimezone(IST).date().isoformat()
            days[d] = days.get(d, 0.0) + v
        value = round(max(days.values()), 1)
    else:
        value = _agg([v for _, v in sel], how)
        value = round(value, 1) if value is not None else None
    covered_from, covered_to = sel[0][0], sel[-1][0]
    late_start = covered_from > lo + timedelta(hours=3)
    early_end = covered_to < hi - timedelta(hours=3)
    notes = []
    if late_start:
        notes.append("The Earth2Studio run starts after the window begins, so part of the window is not covered; the value is not comparable with the full-window model values.")
    if early_end:
        notes.append("The Earth2Studio run ends before the window ends.")
    return {**base, "available": True, "variable": label, "unit": unit, "value": value, "issue_time": gp.get("issue_time"),
            "valid_from": covered_from.isoformat(), "valid_to": covered_to.isoformat(), "steps": len(sel),
            "partial": late_start or early_end, "partial_note": " ".join(notes) or None,
            "source": gp.get("source")}


def satellite(risk_id: str) -> dict:
    layers = SATELLITE.get(risk_id, [])
    extra = ["firms"] if risk_id == "fire" else []
    if not layers and not extra:
        return {"status": "No relevant satellite imagery layer", "layers": [], "quantitative": False}
    return {"status": "Satellite imagery available", "layers": [{"id": l, "label": SATELLITE_LABEL[l]} for l in layers + extra],
            "quantitative": False,
            "note": "Imagery is available on the map for visual context. No satellite value is used in this assessment, so it does not confirm or reject it."}


def official(risk_id: str, dash: dict) -> dict:
    words = OFFICIAL_KEYWORDS.get(risk_id, [])
    warns = dash.get("warnings") or []
    related, other = [], []
    for w in warns:
        text = f"{w.get('event') or ''} {w.get('headline') or ''}".lower()
        (related if any(k in text for k in words) else other).append(official_alert(w))
    return {"status": "OFFICIAL ALERT" if related else "NO OFFICIAL ALERT",
            "alerts": related, "other_alerts_at_location": [{"id": w["id"], "event": w["event"], "issuer": w["issuer"]} for w in other],
            "match_note": "Alerts are matched to this location by CORE (district, state or polygon, see 'match'). Linking an alert to this hazard uses words in its event name.",
            "source": "NDMA SACHET CAP feed via CORE"}


def provenance(dash: dict, gp: dict | None, win: dict) -> list[dict]:
    out = [{"provider": "Bharat Weather Intelligence CORE", "model": None, "run": None,
            "valid": f"{win['dates'][0]} → {win['dates'][-1]} (IST)" if win["dates"] else None,
            "source": "/api/v1/dashboard", "retrieved_at": dash.get("generated_at")}]
    for s in dash.get("sources") or []:
        out.append({"provider": s.get("source"), "model": s.get("model"), "run": s.get("issue_time"),
                    "run_detail": s.get("notes"), "valid": None, "source": s.get("url"), "retrieved_at": s.get("retrieved_at"),
                    "licence": s.get("licence")})
    if gp:
        out.append({"provider": gp.get("source"), "model": gp.get("model"), "run": gp.get("issue_time"),
                    "valid": f"{gp['time'][0]} → {gp['time'][-1]} (UTC)" if gp.get("time") else None,
                    "source": "/api/v1/grid/point", "retrieved_at": None})
    return out


def build_evidence(risk_id: str, dash: dict, gp: dict | None, gp_err: str | None = None) -> dict:
    risk = next((r for r in dash.get("risks") or [] if r["id"] == risk_id), None)
    if risk is None:
        raise KeyError(risk_id)
    win = event_window(risk, dash)
    level = risk["level"]
    sections = {
        "detected": {"title": TITLE.get(risk_id, risk.get("label")), "core_label": risk.get("label"),
                     "severity": {"level": level, "status": risk.get("status") or LEVEL_NAME[level]},
                     "headline": risk.get("headline"), "explanation": risk.get("explanation"),
                     "classification": "official" if risk.get("official") else "system",
                     "classification_label": "From an official alert (via CORE)" if risk.get("official") else "System assessment — not an official warning",
                     "experimental": bool(risk.get("experimental"))},
        "when": {"start": risk.get("period_start"), "end": risk.get("period_end"),
                 "timing_note": None if risk.get("period_start") else "Timing not provided by CORE for this risk.",
                 "evidence_window": win},
        "model_agreement": model_agreement(risk),
        "forecast_range": forecast_range(risk_id, dash, win),
        "normal_departure": normal_departure(risk_id, dash, win),
        "earth2studio": earth2studio(risk_id, gp, win, gp_err),
        "satellite": satellite(risk_id),
        "official": official(risk_id, dash),
        "rule": {"reference": risk.get("reference"), "criterion": risk.get("criterion"),
                 "data": {"peak_value": risk.get("peak_value"), "unit": risk.get("unit")},
                 "result": f"{risk.get('status') or LEVEL_NAME[level]} (level {level}) assigned by CORE",
                 "note": "Rule and level are CORE's existing risk rules, unchanged by V2."},
        "provenance": provenance(dash, gp, win),
    }
    dq = []
    if (dash.get("current") or {}).get("terrain") == "hills":
        dq.append(notice("elevation", elevation_m=dash["location"].get("elevation_m"), terrain="hills"))
    if sections["earth2studio"].get("available"):
        dq.append(notice("grid_vs_point"))
    dq += [n for n in core_inconsistencies(dash) if n["risk"] == risk_id]
    return {"risk": risk_id, "location": location_of(dash), "section_order": SECTION_ORDER, "sections": sections,
            "data_quality": dq, "context": impact_context(risk_id) if level >= 1 and not risk.get("official") else None}
