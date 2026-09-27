# Development workflow

## Branches

- `main` is always deployable. Every push to `main` that touches `web/` deploys the V2 site.
- Work happens on short-lived branches named by milestone: `m1/home-screen`, `m2/evidence-api`,
  etc. They are merged into `main` by pull request after **CI** passes.
- A separate long-running `develop` branch is **not** used. With one developer and an
  independent preview site, it would add merge work without adding safety. This can be revisited.
- Recommended GitHub setting: protect `main`, requiring the **CI** checks (`Web — typecheck and
  build`, `Archive — tests`) before merging. This is configured by the repo owner in Settings →
  Branches.

## Configuration

| Where | Name | Purpose | Default |
|---|---|---|---|
| `web/.env.local` (local only) | `VITE_CORE_API_BASE` | CORE API base used by the browser | `/api/v1` (proxied in dev) |
| `web/.env.local` | `VITE_APP_ENV` | Environment label | `local` |
| Shell (dev server) | `BWI_CORE_ORIGIN` | Where the dev proxy sends `/api` | CORE production API |
| GitHub → Settings → Variables | `CORE_API_BASE` | CORE API base for the Pages build | CORE production `/api/v1` |
| GitHub → Settings → Variables | `CORE_ORIGIN` | Origin used by the contract check | CORE production API |

No secrets are needed in M0. An Earthdata token (for IMERG, in M4) will be a repository
**secret**, never committed.

## Milestones

| | Scope | Exit check |
|---|---|---|
| **M0** ✅ | Repo, docs, CI, Pages, CORE API client + contract check, forecast archive | V2 site live; CORE unchanged; archive files present |
| M1 (built) | V2 experience on existing CORE data: 5 destinations × 3 modes, location, current, forecast, map, risks, alerts, insights, Farmer and Government workflows | `tools/compare/compare.mjs`: V2 and CORE show the same data for 4 locations + Farmer + Government |
| M2 | Intelligence: events, evidence drawer, what-should-you-know by priority, India district risk counts, map risk layer, farmer event chain. `api-v2/` created (IMD rain normals deferred) | Every system card opens evidence with provenance; official and system never merged; counts reconcile with the map |
| M3 | Farmer workflow, Government summary (district counts), drill-down, exports | District counts reconcile with maps; exports open |
| M4 | Satellite point values, thunderstorm potential (CAPE), first verification report, performance, phone layout | Verification report with named reference, ≥ 30 days of archive |

Each milestone needs your explicit approval before it starts.

## api-v2 (M2)

```bash
cd api-v2
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -q                     # offline, CORE fixtures
uvicorn app.main:app --port 8702        # live, reads CORE_API_BASE
```

With `api-v2` on :8702, `npm run dev` in `web/` proxies `/api/v2` to it (override with
`BWI_API_V2_ORIGIN`). Production: repository variable `API_V2_BASE` → `VITE_API_V2_BASE` in
`pages.yml`.

| Variable (api-v2) | Default | Purpose |
|---|---|---|
| `CORE_API_BASE` | CORE production `/api/v1` | The only data source |
| `CORS_ORIGINS` | `https://gnmcool.github.io`, localhost:5174 | Browser origins allowed |
| `POINT_TTL_S` / `REGION_TTL_S` | 600 / 1200 | Cache lifetimes |
| `REGION_CONCURRENCY` | 6 | Parallel CORE state requests |

Acceptance test: `PLAYWRIGHT_CHROMIUM=/opt/pw-browsers/chromium node tools/m2-acceptance/acceptance.mjs <site> <api-v2 base> <CORE api base> --json out.json`.

M3 acceptance: `PLAYWRIGHT_CHROMIUM=/opt/pw-browsers/chromium node tools/m3-acceptance/acceptance.mjs <site> <api-v2 base> <CORE api base> --json out.json`
(run together with the M1 `tools/compare` and M2 `tools/m2-acceptance` regressions).
