# Bharat Weather Intelligence — V2

*Made by Gaurav Makwana*

**Weather. Impact. Decisions for a Safer, Stronger India.**

V2 is a new product experience built **on top of** Bharat Weather Intelligence **CORE**. It is a
separate repository by design. CORE stays independently deployable and is never modified from
here.

| | CORE (stable) | V2 (this repo, in development) |
|---|---|---|
| Repository | [gnmcool/bharat-weather-intelligence](https://github.com/gnmcool/bharat-weather-intelligence) | gnmcool/bharat-weather-intelligence-v2 |
| Website | https://gnmcool.github.io/bharat-weather-intelligence/ | https://gnmcool.github.io/bharat-weather-intelligence-v2/ |
| API | https://bharat-weather-intelligence-brown.vercel.app/api/v1 | consumes CORE's API, read-only |

## How V2 uses CORE (read-only)

- **Code:** `core/` is a git submodule pinned to a specific CORE commit (baseline `2840f8d`,
  tag `core-v1.0`). V2 imports CORE's typed API client, formatting and, from M1, its map engine
  via the `@core/*` alias (`web/vite.config.ts`). Nothing under `core/` is edited here. If V2
  needs a different behaviour, the module is copied into `web/` first.
- **Data:** V2 calls CORE's existing `/api/v1` endpoints unchanged. CORE's API already allows
  requests from `https://gnmcool.github.io`, so no CORE change was needed.
- **Backend additions** (events, evidence, district risk counts, verification) will live in this
  repo as a separate service (`api-v2/`, from M2). They must not alter any `/api/v1` contract.

Updating the CORE pin is a deliberate step: `cd core && git fetch && git checkout <commit>`,
then re-test V2.

## Layout

```
core/       CORE repository (git submodule, pinned) — do not edit
web/        V2 website (React + TypeScript + Vite + Tailwind)
archive/    Daily forecast archive for verification (snapshot.py, points.json)
docs/       Decisions and plan
.github/    pages.yml (V2 website), archive.yml (daily archive)
```

## Run locally

```bash
git clone --recurse-submodules https://github.com/gnmcool/bharat-weather-intelligence-v2
cd bharat-weather-intelligence-v2/web
npm install
npm run dev          # http://localhost:5174 — /api is proxied to CORE's production API
```

Set `BWI_CORE_API=http://127.0.0.1:8000` to use a CORE API running on your own PC instead.

## Forecast archive

Verification needs forecasts saved **before** the weather happens, and CORE keeps only the
latest one. Every day at 11:00 IST, `archive.yml` saves:

- `e2s_gfs_daily_<cycle>.nc`: CORE's Earth2Studio GFS forecast reduced to daily rain, Tmax,
  Tmin and gust per lead day (0.25°, about 2 MB);
- `points_<date>.json`: ECMWF, GFS and ICON daily forecasts from Open-Meteo, **separately**, at
  36 fixed points (one district per State/UT, `archive/points.json`).

Files go to monthly releases (`archive-YYYY-MM`) in this repository.

## Status

Milestone **M0** (safe start): repository, CORE pin, V2 shell with a live connection to CORE,
and the daily archive. See `docs/DECISIONS.md` and the Phase 0 audit.
