# M2 intelligence layer — events, evidence, India risk counts

Everything here is deterministic and traceable: **DATA → RULE → RESULT**. The data is CORE's
public `/api/v1`; the rules and thresholds are CORE's existing risk rules, unchanged. V2 adds
structure, wording and aggregation only. Service: `api-v2/` (FastAPI, `/api/v2`).

## Endpoints

| Endpoint | Built from (CORE) | Returns |
|---|---|---|
| `GET /api/v2/events?lat&lon&name[&taluka]` | `/dashboard` | official alerts (separate list), system events, significant departures from normal, "what should you know" priority list |
| `GET /api/v2/evidence?lat&lon&name&risk` | `/dashboard`, `/grid/point` | nine evidence sections in a fixed order for one risk |
| `GET /api/v2/region/india/risks` | `/geo/states`, `/region/state/{slug}` × 36, `/warnings?national=true` | district counts per hazard and level, by state, district list, official-alert districts, coverage, limitations |
| `GET /api/v2/health` | `/health` | service and CORE status |

Failures of a CORE call return HTTP 502 naming the CORE endpoint. No substitute data is returned.

## Event engine

An **event** is a CORE risk item with level ≥ 1 (Watch) at a point, re-expressed as:

| Field | Source |
|---|---|
| `type` | CORE risk id |
| `title` | V2 wording (`api-v2/app/catalogue.py` `TITLE`) — e.g. "Thunderstorm potential — model derived" |
| `severity` | CORE `level` / `status`, unchanged |
| `start`, `end` | CORE `period_start` / `period_end`, unchanged. If CORE gives none (fog, drought): `timing_note` = "Timing not provided by CORE…" — V2 does not parse times out of headlines |
| `location`, `geographic_unit` | CORE `location`; always `kind: point` (district named for context) |
| `classification` | `system`, or `official` only when CORE marks the item `official` (cyclone, from IMD alerts) |
| `supporting_risk` | CORE `reference`, `criterion`, `peak_value`, `unit` |
| `model_agreement` | parsed from CORE `confidence.basis` "k of n models …" → "Model agreement: k of n". Not converted to a percentage. CORE's `confidence.score` is **not** passed on. Risks CORE assesses from a single blended model → "not assessed" |
| `evidence` | link to `/api/v2/evidence` |

Event categories are CORE's 11 risks. **No "Extreme rain" category**: CORE's rain Severe
level is IMD "very heavy" (≥ 115.6 mm/day); IMD "extremely heavy" (≥ 204.5 mm/day) is not a
CORE rule, and adding it would be a new threshold (not allowed in M2). Flood = CORE's
72-hour accumulation rule; cyclone = official only.

### What should you know? (priority)

1. Official alerts (CORE `warnings` for the location; and CORE risk items marked official)
2. Severe system events · 3. Alert-level · 4. Watch-level
5. Significant departures from normal = CORE anomaly items whose CORE category is outside its
   normal band (not "Near normal"/"Normal"). Labelled "not a hazard on its own".

If there is no official alert and no event at Watch or above: **"No significant weather event detected."**
(departures from normal may still be listed below it).

## Evidence engine — fixed section order

| # | Section | Content | If unavailable |
|---|---|---|---|
| 1 | What was detected | V2 title, CORE level/status, headline, explanation, "System assessment — not an official warning", experimental flag | — |
| 2 | When | CORE period; evidence window = IST dates of the period, else CORE's 7-day horizon (stated) | "Timing not provided by CORE" |
| 3 | Model agreement | "Model agreement: k of n" + CORE basis text + note "not a probability; Earth2Studio/FourCastNet not counted" | "not assessed" + reason |
| 4 | Forecast range | per-model ECMWF / GFS / ICON from CORE `daily[].models`: heat = max Tmax, cold = min Tmin, rain = max daily rain over the window; range = min–max, "model spread" | reason per hazard (CORE publishes no per-model wind, convection, fog, fire, flood-72h) |
| 4b | Earth2Studio GFS | CORE `/grid/point` over the window (t2m max/min, tp IST-day max or sum, fg10m max). Shown **as GFS, not counted**. Flagged *partial* when the run starts after or ends before the window | reason |
| 5 | Normal / departure | FORECAST (CORE best-match daily) vs NORMAL (NASA POWER 1991–2020, MERRA-2 — indicative, **not IMD**) and DEPARTURE; plus the CORE anomaly items for that hazard | reason |
| 6 | Satellite evidence | "Satellite imagery available" + relevant NASA layers. **Never "confirms"**; `quantitative: false` | "No relevant satellite imagery layer" |
| 7 | Official alert | "OFFICIAL ALERT" with the related CORE-matched alerts (issuer wording), or "NO OFFICIAL ALERT"; other alerts at the location listed separately. Relation to the hazard = words in the alert's event/headline (display link) | — |
| 8 | Rule applied | DATA (CORE peak value) → RULE (CORE criterion) → RESULT (CORE level) | — |
| 9 | Provenance | provider, model, run, valid window, source endpoint, retrieval time for every source used | — |

The same drawer opens from: What should you know, Risks & alerts, the map, Government counts
and Farmer.

## India district risk counts — methodology

- **Unit:** district (724). No taluka statistics.
- **Rule:** a district counts for a hazard when CORE's level at the district's representative
  interior point (CORE `/region/state`) is ≥ Watch. Counts are split Watch / Alert / Severe
  and by state. Window: CORE's next 7 days.
- **Counted hazards:** heat, cold, heavy rain, strong wind — the only ones CORE evaluates per
  district. Thunderstorm, lightning, flood, fog, fire and drought are point-only in CORE and are
  listed as *not counted* (computing them would take ~2,000 extra Open-Meteo calls per refresh
  and a new district rule).
- **Official:** districts with ≥ 1 official alert (CORE per-district `official_warnings`), and
  districts per alert event from `/warnings?national=true` `district_ids`. Shown in a separate
  tile and as a dashed red outline on the map; never added to system counts.
- **Reconciliation:** the map colours exactly the districts in the count (same payload); the
  acceptance test recomputes every count from an independent fetch of all 36 CORE state tables.
- **Coverage:** if a CORE state request fails, that state is listed as failed and the counts are
  marked incomplete (cached for 60 s only). Nothing is estimated.
- **Cache:** 20 minutes (CORE's own state cache is 20 minutes). Cold build ≈ 55 s.

### Limitations (shown in the UI)

- One representative point per district: not an area-coverage statistic. Large or mountainous
  districts can be badly represented — see finding F1 below.
- Gridded-field statistics: 18 of 724 districts contain no 0.25° grid-cell centre and 144
  contain fewer than 3 (GEOGRAPHIC_PRECISION.md).
- The peak day per district is not in CORE `/region/state`; open a district for the point
  assessment with dates.

## Findings about CORE outputs (not changed — CORE is frozen; for the owner's decision)

- **F1 — high-altitude district points.** Several Himalayan districts' representative points are
  on high ground (Uttarkashi 5,264 m, Pithoragarh). CORE's point forecast is elevation-adjusted
  while the NASA POWER normal is a ~50 km reanalysis cell, so departures of −10 to −15 °C arise
  and the district is counted as **Severe cold** in late September (8 of 12 cold districts on
  27 Sep 2026). Same mechanism can inflate heat departures in lower hill points (e.g. Doda).
- **F2 — heat level vs its own Watch criterion.** Chennai, 27 Sep: CORE heat = No risk while its
  explanation states +4.8 °C departure and its criterion says "Watch (system): departure ≥ 3 °C";
  its basis says "0 of 3 models … show no event". V2 reports CORE's level unchanged.
- **F3 — Earth2Studio vs point forecast.** At Uttarkashi the E2S cell temperature (−1.8 °C) differs
  from the elevation-adjusted point models (−13.6 to −5.5 °C): a grid-cell value at ~27 km is not
  a point value. The evidence shows both, labelled.
