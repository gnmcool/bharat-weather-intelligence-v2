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
| M1 | V2 shell on real data: navigation (5 destinations × 3 modes), Home "now", Forecast, Map. Existing CORE APIs only; "Model agreement" label | V2 shows the same numbers as CORE for the same place and time |
| M2 | Intelligence: what-should-you-know cards, evidence drawer, weather vs normal (IMD rain normals), events. `api-v2/` created | Every card opens evidence with provenance; official and system never merged |
| M3 | Farmer workflow, Government summary (district counts), drill-down, exports | District counts reconcile with maps; exports open |
| M4 | Satellite point values, thunderstorm potential (CAPE), first verification report, performance, phone layout | Verification report with named reference, ≥ 30 days of archive |

Each milestone needs your explicit approval before it starts.
