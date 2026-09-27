"""Event engine: CORE risk outputs → V2 events. No new thresholds and no new rules.

An event is a CORE risk item with level >= 1 at a point, re-expressed with explicit
timing, classification, supporting rule, model agreement and an evidence reference.
Severity is CORE's level unchanged.
"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlencode

from .catalogue import AGREEMENT_NOTE, LEVEL_NAME, NORMAL_CATEGORIES, TITLE

_AGREE = re.compile(r"(\d+) of (\d+) models?")


def model_agreement(risk: dict) -> dict:
    """Parse CORE's confidence.basis ("k of n models …"). Never converted to a percentage."""
    basis = (risk.get("confidence") or {}).get("basis") or ""
    m = _AGREE.search(basis)
    if not m or risk.get("official"):
        return {"assessed": False, "agreeing": None, "of": None, "text": "Model agreement: not assessed",
                "basis": basis or None, "note": "CORE assesses this risk from a single blended model or an official source; there is no multi-model agreement count."}
    k, n = int(m.group(1)), int(m.group(2))
    return {"assessed": True, "agreeing": k, "of": n, "models": ["ECMWF", "GFS", "ICON"],
            "text": f"Model agreement: {k} of {n}", "basis": basis, "note": AGREEMENT_NOTE}


def location_of(dash: dict) -> dict:
    loc = dash["location"]
    return {k: loc.get(k) for k in ("name", "lat", "lon", "district", "district_id", "state", "taluka", "elevation_m")}


def evidence_ref(loc: dict, risk_id: str) -> str:
    q = {"lat": loc["lat"], "lon": loc["lon"], "name": loc.get("name"), "risk": risk_id}
    if loc.get("taluka"):
        q["taluka"] = loc["taluka"]
    return "/api/v2/evidence?" + urlencode({k: v for k, v in q.items() if v is not None})


def build_event(risk: dict, dash: dict) -> dict:
    loc = location_of(dash)
    start, end = risk.get("period_start"), risk.get("period_end")
    official = bool(risk.get("official"))
    return {
        "id": f"{risk['id']}@{loc['lat']:.4f},{loc['lon']:.4f}",
        "type": risk["id"],
        "title": TITLE.get(risk["id"], risk.get("label")),
        "core_label": risk.get("label"),
        "headline": risk.get("headline"),
        "explanation": risk.get("explanation"),
        "severity": {"level": risk["level"], "status": risk.get("status") or LEVEL_NAME[risk["level"]]},
        "start": start,
        "end": end,
        "timing_note": None if start else "Timing not provided by CORE for this risk; see the headline.",
        "location": loc,
        "geographic_unit": {
            "kind": "point",
            "description": f"Point forecast at {loc['name']}" + (f", within {loc['district']} district" if loc.get("district") else ""),
            "district_id": loc.get("district_id"),
        },
        # System-derived unless CORE itself marks the item as coming from an official alert (cyclone).
        "classification": "official" if official else "system",
        "classification_label": "From an official alert (via CORE)" if official else "System assessment — not an official warning",
        "experimental": bool(risk.get("experimental")),
        "supporting_risk": {
            "id": risk["id"], "reference": risk.get("reference"), "criterion": risk.get("criterion"),
            "peak_value": risk.get("peak_value"), "unit": risk.get("unit"), "source": "CORE /api/v1/dashboard risks[]",
        },
        "model_agreement": model_agreement(risk),
        "sources": risk.get("sources") or [],
        "evidence": evidence_ref(loc, risk["id"]),
    }


def official_alert(w: dict) -> dict:
    keep = ("id", "event", "headline", "description", "issuer", "sender", "severity", "urgency", "certainty",
            "effective", "expires", "area", "link", "match", "district_ids", "source")
    return {"classification": "official", **{k: w.get(k) for k in keep}}


_SEV = {"Extreme": 4, "Severe": 3, "Moderate": 2, "Minor": 1}


def significant_anomalies(dash: dict) -> list[dict]:
    a = dash.get("anomaly") or {}
    base = a.get("baseline") or {}
    out = []
    for it in a.get("items") or []:
        if it.get("category") in NORMAL_CATEGORIES:
            continue
        out.append({**it, "kind": "departure_from_normal",
                    "baseline": f"{base.get('source', 'unknown')} — {base.get('model', '')}".strip(" —"),
                    "baseline_note": "Reanalysis baseline (NASA POWER), indicative; not an IMD station or gridded climatology."})
    return out


def build_events(dash: dict) -> dict[str, Any]:
    risks = dash.get("risks") or []
    events = [build_event(r, dash) for r in risks if r.get("level", 0) >= 1]
    events.sort(key=lambda e: (-e["severity"]["level"], e["start"] or "9999", e["type"]))
    alerts = sorted((official_alert(w) for w in dash.get("warnings") or []), key=lambda w: -_SEV.get(w.get("severity") or "", 0))
    anomalies = significant_anomalies(dash)

    # "What should you know?" priority — each item points at the record it came from.
    items: list[dict] = []
    for w in alerts:
        items.append({"priority": 1, "group": "Official alerts", "kind": "official", "ref": w["id"]})
    sys_events = [e for e in events if e["classification"] == "system"]
    off_events = [e for e in events if e["classification"] == "official"]
    for e in off_events:
        items.append({"priority": 1, "group": "Official alerts", "kind": "official_event", "ref": e["id"]})
    for lvl, pri, group in ((3, 2, "Severe system assessments"), (2, 3, "Alert-level system assessments"), (1, 4, "Watch-level system assessments")):
        for e in sys_events:
            if e["severity"]["level"] == lvl:
                items.append({"priority": pri, "group": group, "kind": "event", "ref": e["id"]})
    for a in anomalies:
        items.append({"priority": 5, "group": "Significant departures from normal", "kind": "anomaly", "ref": a["id"]})
    significant = any(i["priority"] <= 4 for i in items)

    return {
        "location": location_of(dash),
        "core_generated_at": dash.get("generated_at"),
        "official_alerts": alerts,
        "events": events,
        "anomalies": anomalies,
        "what_to_know": {
            "items": items,
            "message": None if significant else "No significant weather event detected.",
            "rule": "Priority: 1 official alerts, 2 severe, 3 alert-level, 4 watch-level system assessments, 5 significant departures from normal (CORE category outside its normal band). A weather event is significant when it is an official alert or a CORE risk at Watch level or above.",
        },
        "not_flagged": [r["id"] for r in risks if r.get("level", 0) == 0],
        "sources": dash.get("sources") or [],
        "notices": dash.get("notices") or [],
    }
