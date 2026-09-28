# V2 decisions log

Newest first. Each decision was approved by the owner unless marked *proposed*.

| Date | Decision | Why |
|---|---|---|
| 2026-09-28 | Historical forecasts (M4.2) are a **separate dataset** (`history/`, `dataset = historical_backfill`): `run_time_known = false`, `run_time_utc` null, `nominal_lead_day` = N of Open-Meteo `previous_dayN`; daily values only from all 24 hourly values; never mixed with the prospective archive | Owner's M4.2 brief; the source does not identify the model run |
| 2026-09-28 | Rain is aggregated twice: IST calendar day and 08:30→08:30 IST (IMD gauge day); IMD is the primary rain reference, ERA5 secondary; METAR rain never used | Step 1 findings; IMD day definition |
| 2026-09-28 | *Proposed:* METAR pairing = nearest station ≤ 25 km and \|Δ elevation\| ≤ 100 m; METAR day complete = ≥ 20 reports and one in each 6-h IST block | Needs owner approval after the probe |
| 2026-09-28 | Forecast archive = one **immutable** GitHub release per IST day (`archive-daily-YYYY-MM-DD`), draft → verified → published; manifest + checks committed to the append-only `archive-index` branch; refusal on any incomplete data | M4 B2; Step 1 found monthly appends incompatible with immutability |
| 2026-09-28 | Archive models `ecmwf_ifs025`, `gfs_global`, `icon_global` with exact run times from Open-Meteo run metadata (checked before and after; GFS on both grids). `gfs025` rejected: no temperature or rain | Step 1 probe |
| 2026-09-28 | Only the 36 fixed points; no backfill, no 109-station expansion until the prospective archive is proven | Owner's instruction (B3 not approved) |
| 2026-09-27 | Government counts are worded "districts with system-assessed … risk" with the statement "District risk counts are based on the representative forecast point for each district. Conditions may vary within a district." Never "affected districts" | Owner's M3 brief: no district-wide impact dataset |
| 2026-09-27 | Data-quality notices are one reusable component; each is triggered by a CORE field (terrain, model-check text, grid source) or by coverage — never a new threshold (`DATA_QUALITY.md`) | Honest about limits without changing CORE |
| 2026-09-27 | CORE problems are logged in `CORE_ISSUES.md` (CORE-1 … CORE-6) and not fixed from V2 | CORE frozen; fixes need explicit approval |
| 2026-09-27 | Impact context = fixed, conditional catalogue lines shown only beside a CORE event; tested against instruction words; no LLM | FACT → ASSESSMENT → EVIDENCE → POTENTIAL RELEVANCE (`IMPACT_CONTEXT.md`) |
| 2026-09-27 | Farmer order: location → crop → stage → weather → system indicators (SYSTEM-DERIVED · UNVALIDATED) → potential crop relevance → official advisory (separate block) | Owner's M3 brief |
| 2026-09-27 | Incomplete India counts (a CORE state failing after one retry) are flagged directly under the count tiles and cached 60 s only | Never present a partial total as complete |
| 2026-09-27 | M2 intelligence runs in a **separate service `api-v2/`** (FastAPI, `/api/v2`, own Vercel project) that reads CORE only over HTTP `/api/v1` | Owner's M2 brief: V2-only, isolated, no `/api/v1` change |
| 2026-09-27 | Events = CORE risk items at Watch or above; severity, timing, criteria unchanged. No "Extreme rain" category (IMD ≥ 204.5 mm is not a CORE rule) | No new thresholds in M2 |
| 2026-09-27 | CORE `confidence.score` is not passed to the UI; agreement is shown only as "k of n" | Prevents agreement being read as probability |
| 2026-09-27 | District counts only for heat/cold/rain/wind (what CORE evaluates per district); other hazards listed as not counted | No manufactured precision; no new district rule |
| 2026-09-27 | Official alerts drawn as a dashed red outline when the system-risk fill is on | Official and system never visually merged |
| 2026-09-27 | Official-alert ↔ hazard link in evidence uses words in the alert's event/headline; CORE's location match is shown | Display link only; issuer wording untouched |
| 2026-09-27 | Farmer: event → existing CORE indicator using the same weather variable (display link); no link where none exists | No new agronomic rules |
| 2026-09-27 | M1 uses **only** CORE's public API, plus two public CORE website files (district and state GeoJSON outlines), both listed in the contract. No CORE source is imported; the map is V2's own MapLibre implementation | Owner's M1 brief. `/api/v1` does not serve polygons; these files are public, read-only and CORS-open |
| 2026-09-27 | CORE's `thunderstorm` and `lightning` risk items are labelled **"Thunderstorm potential — model derived"** and **"Lightning potential — model derived"**. Levels, status and rules unchanged | Approved decision: never present model output as observed lightning |
| 2026-09-27 | "What should you know?" lists official alerts first, then CORE risk items at Watch or above; if none, it says so. No new detection | M1 brief: no invented intelligence |
| 2026-09-27 | The 10-day table shows CORE's per-model values (ECMWF, GFS, ICON) as a range "across models", not as a probability | Existing CORE data; model-agreement methodology |
| 2026-09-27 | **CORE's API is the boundary.** V2 imports no CORE source code. The earlier M0 draft pinned CORE as a git submodule and imported two CORE frontend files; both were removed | Owner's M0 brief: no structural dependency on internal CORE files without a clear technical reason |
| 2026-09-27 | V2 declares its own types for the CORE fields it uses (`web/src/core-api/`), backed by `contract/core-api-contract.json` and a daily live check | A duplicated type is safe only if drift is detected. The contract check detects it |
| 2026-09-27 | Controlled reuse of CORE frontend code (e.g. the map engine in M1) only with a written reason and approval, as a copy with a header naming the CORE file and commit | Keeps V2 independent while avoiding needless rewrites |
| 2026-09-27 | V2 is a **separate repository**; CORE is untouched and independently deployable | Owner's instruction |
| 2026-09-27 | V2 website on this repository's GitHub Pages | Own URL, free, and CORE's CORS already allows `gnmcool.github.io`, so no CORE change is needed |
| 2026-09-27 | V2 backend additions go in a separate service (`api-v2/`, from M2); no change to `/api/v1` contracts | Owner's instruction |
| 2026-09-27 | `main` + short-lived milestone branches with PRs and required CI; no long-running `develop` branch | One developer; `main` deploys only the preview site |
| 2026-09-27 | **District** is the finest unit for area statistics; taluka and village get labelled point forecasts only | 0.25° cell (~700 km²) is larger than an average taluka (~550 km²); 144 of 724 districts already have < 3 cells |
| 2026-09-27 | "Thunderstorm potential — model derived" plus official lightning alerts. Never "lightning" as observed | No open observed-lightning feed for India |
| 2026-09-27 | **Model Agreement** from ECMWF, GFS and ICON only; API field `confidence` kept for CORE compatibility | Earth2Studio GFS and FourCastNet share GFS; no calibration yet |
| 2026-09-27 | Rain vs normal to use **IMD 1991–2020 gridded normals** when implemented; NASA POWER for temperature, and not presented as India rainfall climatology | MERRA-2 rainfall is weak over India |
| 2026-09-27 | "Satellite imagery available" until Earthdata point values are implemented | Images are not quantitative evidence |
| 2026-09-27 | Verification: archive from M0; references IMERG and ERA5, always named; no confidence claims before enough history | Verification needs saved forecasts and a named reference |
| 2026-09-27 | Five destinations (Home, Map, Risks & alerts, Forecast, Insights); mode is the primary context; satellite lives in Map and evidence | Avoid 7 tabs × 3 modes clutter |
