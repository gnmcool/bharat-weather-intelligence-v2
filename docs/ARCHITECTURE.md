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
│ api-v2/     (M2) V2-only endpoints: /api/v2/events, /evidence, /region/india/risks (reads CORE over HTTP)  │
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
| `api-v2/` (M2) | FastAPI service, `/api/v2/events`, `/evidence`, `/region/india/risks`, `/health`. Reads CORE only over HTTP; in-process TTL cache; offline tests with captured CORE responses. See `EVENTS_AND_EVIDENCE.md` | Vercel (second project, root `api-v2`, region bom1) |
| `web/src/v2-api/` (M2) | Typed client for `api-v2` | Browser |
| `tools/m2-acceptance/` (M2) | CORE vs V2 API vs V2 UI acceptance test (events, evidence, district reconciliation) | Locally / on demand |

```
Browser (GitHub Pages) ──► CORE /api/v1  (forecast, risks, alerts, maps)
        │
        └────────────────► api-v2 /api/v2 ──► CORE /api/v1   (events, evidence, India counts)
```

## Planned

- Verification metrics (M4) computed from `archive/` outputs; see `VERIFICATION.md`.

## Why this shape

- **CORE stays independently deployable.** V2 has no build-time or run-time dependency on CORE's
  source, only on its public API, which the contract check watches.
- **Heavy processing stays server-side.** The browser only renders; Earth2Studio runs in CORE's
  workflow, and V2 analysis will run in `api-v2/` or GitHub Actions.
- **History starts now.** The archive runs from M0 because verification needs forecasts saved
  before the weather happened.
