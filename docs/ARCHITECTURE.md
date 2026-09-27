# V2 architecture

**Status:** milestone M0 (foundation). No application screens yet.

## System context

```
                          ┌──────────────────────────── CORE (protected, separate repo) ─────────────────────────┐
 NOAA GFS / Open-Meteo /  │ Earth2Studio GFS ingest (GitHub Actions, every 6 h) → release forecast/gfs_latest.nc  │
 NASA / SACHET / EUMETSAT │ FastAPI /api/v1 on Vercel (bharat-weather-intelligence-brown.vercel.app)             │
                          │ CORE website on GitHub Pages                                                         │
                          └───────────────▲───────────────────────────────▲──────────────────────────────────────┘
                                          │ HTTPS GET, read-only          │ HTTPS GET, read-only
                                          │ (/api/v1, JSON)               │ (release asset, daily)
┌─────────────────────────────── V2 (this repo) ──────────────────────────┼──────────────────────────────────────┐
│ web/        React + TS + Vite + Tailwind → GitHub Pages                 │                                      │
│   src/core-api/   typed client for the CORE endpoints V2 uses           │                                      │
│ contract/   the endpoints/fields V2 depends on + live checker           │                                      │
│ archive/    daily forecast archive  ────────────────────────────────────┘ + Open-Meteo (ECMWF/GFS/ICON points)  │
│             → this repo's releases (archive-YYYY-MM)                                                          │
│ api-v2/     (M2+, not created yet) V2-only endpoints: events, evidence, district risk counts, verification    │
└───────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Components

| Path | Role | Runs where |
|---|---|---|
| `web/` | V2 website. In M0 only a deployment-check page | Browser; built by `pages.yml` to GitHub Pages |
| `web/src/config.ts` | All runtime configuration (CORE API base, environment label) | Build time (Vite env) |
| `web/src/core-api/` | V2's own typed, read-only client for CORE's `/api/v1` | Browser |
| `contract/` | `core-api-contract.json` (what V2 depends on) + `check-core-contract.mjs` | CI (`core-contract.yml`), locally |
| `archive/` | `snapshot.py` + `points.json`: daily forecast archive for verification | GitHub Actions (`archive.yml`) |
| `.github/workflows/` | `ci.yml` build/tests · `pages.yml` deploy · `core-contract.yml` · `archive.yml` | GitHub Actions |

## Planned (not built in M0)

- `api-v2/` (M2): a separate FastAPI service for V2-only endpoints (`/events`, `/evidence`,
  `/region/india/risks`). It calls CORE's API; it does not import or modify CORE code, and it does
  not change any `/api/v1` contract. Hosting to be decided at M2 (a second Vercel project is the
  default).
- Verification metrics (M4) computed from `archive/` outputs; see `VERIFICATION.md`.

## Why this shape

- **CORE stays independently deployable.** V2 has no build-time or run-time dependency on CORE's
  source, only on its public API, which the contract check watches.
- **Heavy processing stays server-side.** The browser only renders; Earth2Studio runs in CORE's
  workflow, and V2 analysis will run in `api-v2/` or GitHub Actions.
- **History starts now.** The archive runs from M0 because verification needs forecasts saved
  before the weather happened.
