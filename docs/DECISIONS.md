# V2 decisions log

| Date | Decision | Why |
|---|---|---|
| 2026-09-27 | V2 is a **separate repository**; CORE is untouched and independently deployable | Owner's instruction; zero risk to the live CORE site and API |
| 2026-09-27 | V2 consumes CORE **read-only**: code via a pinned git submodule (`core/`), data via CORE's `/api/v1` | Reuse without forking; CORE updates are adopted deliberately |
| 2026-09-27 | V2 backend additions go in a separate service in this repo (`api-v2/`, from M2); no change to `/api/v1` contracts | Owner's instruction; isolates risk |
| 2026-09-27 | V2 website on this repo's GitHub Pages (`gnmcool.github.io/bharat-weather-intelligence-v2`) | Own URL, free, and CORE's API already allows this origin, so CORE needs no change. Replaces the earlier "own Vercel site" idea, which assumed a branch in the CORE repo |
| 2026-09-27 | **District** is the finest unit for area statistics; taluka and village get point forecasts only | A 0.25° cell (~700 km²) is larger than an average taluka (~550 km²) |
| 2026-09-27 | Map shows **"Thunderstorm potential (model)"**, not "Lightning"; plus official lightning alerts | No open observed-lightning feed for India |
| 2026-09-27 | "Confidence" is shown as **model agreement** (independent models only: ECMWF, GFS, ICON) | Earth2Studio GFS and FourCastNet share GFS, so they are not independent; no calibration yet |
| 2026-09-27 | Five destinations: Home, Map, Risks & alerts, Forecast, Insights; mode (Citizen / Farmer / Government) is the primary switch | Avoid 7 tabs × 3 modes clutter |
| 2026-09-27 | Forecast archive starts in M0 | Verification is impossible without saved past forecasts |
