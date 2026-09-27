# CORE vs V2 comparison

`compare.mjs` is the M1 acceptance test. It opens the CORE website and the V2 website in a real
browser for the same locations, captures the CORE API response each site received, and checks:

- **A — same data:** current conditions, 48-hour and 10-day series (including per-model values),
  risks (level, status, model agreement), official alerts, and provenance/model runs are identical.
- **B — V2 display:** what V2 shows equals that data (display rounding only).
- **C — CORE display:** what CORE shows equals the same data (CORE rounds to whole degrees, ±0.5).

It also checks Farmer (`/farmer`) and Government (`/region/state`, `/region/india`) data.

```bash
npm i -D playwright && npx playwright install chromium     # once
node tools/compare/compare.mjs                              # live V2 vs live CORE
node tools/compare/compare.mjs http://localhost:5174/       # local V2 dev server vs live CORE
node tools/compare/compare.mjs --json report.json           # also write a JSON report
```

CORE builds a fresh dashboard for every request, so the two sites' responses carry timestamps a
few seconds apart; the check requires them to be close together and compares every value inside.
