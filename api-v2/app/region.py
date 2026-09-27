"""India district risk counts, aggregated from CORE /region/state for every state/UT.

Counting unit: district (never taluka). A district counts for a hazard when CORE's level at
that district's representative interior point is >= Watch. The count is therefore
"districts where the representative point reaches the level", not an area-coverage figure.
Only hazards CORE evaluates per district (heat, cold, rain, wind) are counted; official alerts
are counted from CORE's per-district official_warnings and the national SACHET list.
"""
from __future__ import annotations

import asyncio
from collections import Counter, defaultdict
from datetime import datetime, timezone

from .catalogue import LEVEL_NAME, TITLE
from .config import settings
from .core_client import CoreClient, CoreError

COUNTED = ["rain", "heat", "cold", "wind"]
NOT_COUNTED = {
    "thunderstorm": "CORE evaluates thunderstorm potential only per point (hourly single-model); /region/state has no district level.",
    "lightning": "As thunderstorm: point-only in CORE.",
    "flood": "CORE's flood rule (72-h accumulation + soil moisture) is point-only; river floods are official CWC alerts (counted under official alerts).",
    "fog": "Point-only in CORE.",
    "fire": "Point-only in CORE.",
    "drought": "Point-only in CORE (the district table gives 30-day rain departure, shown separately, not as a risk level).",
    "cyclone": "Official only; counted under official alerts.",
}
LIMITATIONS = [
    "One representative interior point per district (CORE /region/state). A district is counted if that point reaches the level; this is not the share of the district area affected.",
    "Large or mountainous districts may be poorly represented by one point (e.g. a high-altitude point in a Himalayan district can reach cold levels that valley towns do not).",
    "Gridded-field statistics are also limited: of 724 districts, 18 contain no 0.25° grid-cell centre and 144 contain fewer than 3 (docs/GEOGRAPHIC_PRECISION.md). No per-district precision beyond this is claimed.",
    "Assessment window is CORE's next 7 days; the day of the peak per district is not published by CORE /region/state. Open a district for the point assessment and its dates.",
    "Taluka and village remain point-forecast locations; no taluka statistics are produced.",
]


async def build_india_risks(client: CoreClient) -> dict:
    states = await client.states()
    sem = asyncio.Semaphore(settings.region_concurrency)

    async def one(s: dict):
        async with sem:
            try:
                return s, await client.region_state(s["state_slug"]), None
            except CoreError as e:
                return s, None, e.message[:200]

    results = await asyncio.gather(*(one(s) for s in states))
    try:
        national = await client.warnings_national()
        nat_err = None
    except CoreError as e:
        national, nat_err = [], e.message[:200]

    districts, failed, generated = [], [], []
    for s, data, err in results:
        if data is None:
            failed.append({"state": s["state"], "state_slug": s["state_slug"], "expected_districts": s.get("n_districts"), "error": err})
            continue
        generated.append(data.get("generated_at"))
        for d in data["districts"]:
            districts.append({
                "id": d["id"], "district": d["district"], "state": data["state"], "state_slug": data["state_slug"],
                "lat": d["lat"], "lon": d["lon"], "terrain": d.get("terrain"),
                "levels": {k: d["levels"].get(k, 0) for k in COUNTED}, "max_level": d.get("max_level", 0),
                "official_alerts": d.get("official_warnings", 0),
                "values": {k: d.get(k) for k in ("tmax_7d_max", "tmin_7d_min", "rain_7d", "rain_max_day", "gust_max", "rain_30d_pct", "rain_30d_cat")},
            })

    hazards = []
    for h in COUNTED:
        by_level = Counter(d["levels"][h] for d in districts)
        by_state: dict[str, Counter] = defaultdict(Counter)
        for d in districts:
            if d["levels"][h] >= 1:
                by_state[d["state"]][d["levels"][h]] += 1
        conc = sorted(({"state": st, "districts": sum(c.values()), "watch": c[1], "alert": c[2], "severe": c[3]}
                       for st, c in by_state.items()), key=lambda x: (-x["districts"], x["state"]))
        hazards.append({"id": h, "title": TITLE[h], "watch": by_level[1], "alert": by_level[2], "severe": by_level[3],
                        "districts": by_level[1] + by_level[2] + by_level[3], "states": len(conc), "by_state": conc,
                        "rule": "CORE district levels (IMD heat/cold/rain criteria; Beaufort gusts), representative point, next 7 days."})

    ids = {d["id"] for d in districts}
    by_event: dict[str, set] = defaultdict(set)
    for w in national:
        for did in w.get("district_ids") or []:
            by_event[w.get("event") or "Unspecified"].add(did)
    off_districts = {d["id"] for d in districts if d["official_alerts"] > 0}
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "core_generated_at": {"oldest": min(filter(None, generated), default=None), "newest": max(filter(None, generated), default=None)},
        "unit": "district",
        "window": "Next 7 days (CORE /region/state)",
        "classification": "system",
        "classification_label": "System assessment counts — not official warnings",
        "method": "Count of districts whose CORE level at the district's representative interior point is Watch or above, per hazard, from CORE /api/v1/region/state for every state and UT.",
        "levels": LEVEL_NAME,
        "hazards": hazards,
        "not_counted": [{"id": k, "title": TITLE[k], "reason": v} for k, v in NOT_COUNTED.items()],
        "official": {
            "classification": "official",
            "districts_with_alerts": len(off_districts),
            "alerts": len(national),
            "alerts_without_district": sum(1 for w in national if not w.get("district_ids")),
            "by_event": sorted(({"event": e, "districts": len(v & ids) if ids else len(v)} for e, v in by_event.items()),
                               key=lambda x: -x["districts"]),
            "source": "NDMA SACHET CAP feed via CORE (/region/state official_warnings, /warnings?national=true)",
            "error": nat_err,
        },
        "coverage": {"states": len(states), "states_failed": failed,
                     "districts_expected": sum(s.get("n_districts") or 0 for s in states),
                     "districts_received": len(districts), "complete": not failed},
        "districts": districts,
        "limitations": LIMITATIONS,
        "sources": [{"provider": "Bharat Weather Intelligence CORE", "source": "/api/v1/region/state/{state}", "note": "Open-Meteo best-match per district point; NASA POWER normals"},
                    {"provider": "NDMA SACHET", "source": "/api/v1/warnings?national=true"}],
    }
