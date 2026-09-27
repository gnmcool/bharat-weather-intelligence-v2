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
| Status | Production/reference, unchanged since tag `core-v1.0` | In development (milestone M0 done) |

CORE stays independently buildable, deployable and runnable. V2 never modifies it. **CORE's API
is the boundary.** V2 imports no CORE source code, and every CORE endpoint and field it relies on
is listed in `contract/core-api-contract.json` and checked daily against the live API. Details:
[docs/CORE_BOUNDARY.md](docs/CORE_BOUNDARY.md).

## Architecture (short)

```
web/        V2 website (React + TypeScript + Vite + Tailwind) → GitHub Pages
  src/config.ts     runtime configuration
  src/core-api/     typed read-only client for CORE's /api/v1
contract/   CORE API contract + live checker
archive/    daily forecast archive for verification → this repo's releases
docs/       architecture and policies
api-v2/     (from M2) V2-only endpoints in a separate service; never changes /api/v1
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
| M1 | Navigation (Home, Map, Risks & alerts, Forecast, Insights × Citizen/Farmer/Government); Home, Forecast, Map on CORE data | Awaiting approval |
| M2 | What-should-you-know, evidence ("Why this forecast?"), weather vs normal (IMD normals), events; `api-v2/` | Planned |
| M3 | Farmer workflow; Government India summary and district drill-down | Planned |
| M4 | Satellite point values, thunderstorm potential, verification report, performance | Planned |

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
