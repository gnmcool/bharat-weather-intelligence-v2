# V2 decisions log

Newest first. Each decision was approved by the owner unless marked *proposed*.

| Date | Decision | Why |
|---|---|---|
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
