# Bharat Weather Intelligence — V2

*Made by Gaurav Makwana*

**Weather. Impact. Decisions for a Safer, Stronger India.**

## Purpose

V2 is the next product experience of Bharat Weather Intelligence: an India-focused weather
intelligence and decision-support platform for **citizens, farmers and government**. It is built
around one chain:

**WEATHER → RISK → IMPACT → DECISION SUPPORT**

and these questions: *What is happening? Is it unusual? What could it affect? Why does the system
think that? Is there an official warning? What should the user know?*

It is not meant to become another Windy. Windy is a benchmark for map interaction, timeline and
layers only.

## Relationship with CORE

| | CORE (protected) | V2 (this repository) |
|---|---|---|
| Repository | [gnmcool/bharat-weather-intelligence](https://github.com/gnmcool/bharat-weather-intelligence) | gnmcool/bharat-weather-intelligence-v2 |
| Website | https://gnmcool.github.io/bharat-weather-intelligence/ | https://gnmcool.github.io/bharat-weather-intelligence-v2/ |
| API | `https://bharat-weather-intelligence-brown.vercel.app/api/v1` | consumes CORE's API **read-only** |
| Status | Production/reference, unchanged since tag `core-v1.0` | In development (M1 and M2 approved; M3 built, awaiting approval) |

CORE stays independently buildable, deployable and runnable. V2 never modifies it. **CORE's API
is the boundary.** V2 imports no CORE source code, and every CORE endpoint and field it relies on
is listed in `contract/core-api-contract.json` and checked daily against the live API. Details:
[docs/CORE_BOUNDARY.md](docs/CORE_BOUNDARY.md).

## Architecture (short)

```
web/        V2 website (React + TypeScript + Vite + Tailwind + MapLibre + Recharts) → GitHub Pages
  src/config.ts     runtime configuration
  src/core-api/     typed read-only client for CORE's /api/v1 (the only way V2 reaches CORE)
  src/pages/        Home, Forecast, Risks & alerts, Insights
  src/modes/        Farmer workflow, Government India view and state drill-down
  src/map/          V2's own map (MapLibre) drawing CORE's gridded fields
tools/compare/  CORE-vs-V2 data comparison (M1 acceptance test)
tools/m2-acceptance/, tools/m3-acceptance/  milestone acceptance tests
contract/   CORE API contract + live checker
archive/    daily forecast archive for verification → this repo's releases
docs/       architecture and policies
api-v2/     (M2) V2-only endpoints in a separate service (/api/v2); reads CORE over HTTP, never changes /api/v1
```

Full picture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Data principles

- Real data only: no mock data where a real source exists, and no fabricated history.
- Every value keeps its provenance: source, model, run time, valid time, units, method.
- A failed source is shown as unavailable, never silently replaced.
- **District** is the finest unit for area statistics. Taluka and village values are point
  forecasts and are labelled so. See [docs/GEOGRAPHIC_PRECISION.md](docs/GEOGRAPHIC_PRECISION.md).
- **Model Agreement** (ECMWF, GFS, ICON: 3 independent models) replaces "confidence".
  Earth2Studio GFS and FourCastNet are not counted separately. See
  [docs/MODEL_AGREEMENT.md](docs/MODEL_AGREEMENT.md).
- Thunderstorm potential is labelled "model derived", never as observed lightning. Satellite is
  "imagery available" until point values exist. See [docs/DATA_PROVENANCE.md](docs/DATA_PROVENANCE.md).

## Official vs system-derived

| OFFICIAL WARNING | SYSTEM ASSESSMENT |
|---|---|
| IMD, CWC, NDMA/SACHET, SDMA, verbatim, with issuer and validity | Bharat Weather Intelligence analysis, with rule, period and sources |
| Red "Official warning" label | Blue-grey "System assessment" label; never uses the word "warning" |

The two are never merged into one statement.

## Milestones

| | Scope | Status |
|---|---|---|
| M0 | Foundation: repo, docs, CI, Pages, CORE contract, forecast archive | **Done** |
| M1 | Navigation (Home, Map, Risks & alerts, Forecast, Insights × Citizen/Farmer/Government) on existing CORE data only; CORE-vs-V2 comparison tool | Approved |
| M2 | Events, evidence drawer, what-should-you-know by priority, India district risk counts, map risk layer, farmer event chain; `api-v2/` (IMD normals deferred) | Approved |
| M3 | Decision support with guardrails: Citizen summary + WHEN timeline, Farmer 7-step workflow, Government India → state → district → event → evidence, impact context, data-quality notices, CORE issues log | **Built — awaiting approval** |
| M4 | Scientific validation. Done: Phase 0 plan, Step 1 feasibility, **immutable daily forecast archive (awaiting review)**. Next stages not started | In progress |

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) and [docs/DECISIONS.md](docs/DECISIONS.md).

## Run locally

```bash
git clone https://github.com/gnmcool/bharat-weather-intelligence-v2
cd bharat-weather-intelligence-v2/web
npm ci
npm run dev                # http://localhost:5174 — /api is proxied to CORE's production API
```

Other commands:

```bash
npm run build              # typecheck + production build (web/dist)
npm run contract           # check CORE still provides what V2 needs (read-only GETs)
node ../tools/compare/compare.mjs   # CORE vs V2 data comparison in a real browser (needs Playwright)
BWI_CORE_ORIGIN=http://127.0.0.1:8000 npm run dev   # use a CORE API running on your own PC

cd ../archive
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q tests  # offline archive tests
python snapshot.py --out out   # one archive snapshot (downloads ~46 MB from CORE's release)
```

## Forecast archive

Every day at 11:00 IST, `archive.yml` saves CORE's Earth2Studio GFS forecast as daily values
(~2 MB) and ECMWF, GFS and ICON forecasts at 36 fixed points (~65 KB) to this repository's
monthly releases (`archive-YYYY-MM`). It reads CORE's public outputs only, and CORE's own
forecast workflow is untouched. See [docs/VERIFICATION.md](docs/VERIFICATION.md).
