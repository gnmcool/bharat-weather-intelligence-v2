# CORE / V2 boundary

CORE (`gnmcool/bharat-weather-intelligence`) is the protected production and reference system.
V2 is developed independently and **consumes CORE read-only**.

## Rules

| V2 may | V2 must not |
|---|---|
| Call CORE's public `/api/v1` endpoints with GET | Commit to CORE, open automated changes against it, or edit its settings |
| Download CORE's public release asset `forecast/gfs_latest.nc` (archive job) | Import CORE source files at build time or run time (no submodule, no path alias) |
| Declare its own TypeScript types for the CORE fields it uses | Rely on a CORE field that is not listed in `contract/core-api-contract.json` |
| Re-implement presentation it needs (charts, map) in `web/` | Change CORE's risk rules, thresholds, tests, workflows, Pages site or local setup |
| Add V2-only endpoints in `api-v2/` (from M2) | Add, rename or remove anything under CORE's `/api/v1` |

**Controlled reuse of CORE frontend code** (for example the map rendering engine in M1) is
allowed only with a written technical reason in `DECISIONS.md` and your approval. When allowed,
the code is copied into `web/` with a header naming the CORE file and commit. It is never
linked.

## The contract

`contract/core-api-contract.json` lists every CORE endpoint and field V2 uses.
`contract/check-core-contract.mjs` verifies against the live CORE API that:

1. each path exists in CORE's OpenAPI document (`/openapi.json`);
2. each field is present in a live response with the expected type.

It runs daily and on pull requests that touch the contract or the client (`core-contract.yml`).
It is deliberately **not** part of the build, so a CORE outage never blocks V2 deployment. A
failure means CORE changed or is down; V2 is adapted, and CORE is not.

## Other dependencies on CORE

- **CORS:** CORE's API allows browser requests from `https://gnmcool.github.io`, which covers
  V2's Pages site. If V2 moves to another domain, CORE's `BWI_CORS_ORIGINS` would need your
  approval to change.
- **Capacity:** V2 traffic shares CORE's Open-Meteo free-tier quota (non-commercial, about
  10,000 calls a day) and Vercel Hobby limits. V2 must cache and must not poll aggressively.

## Baseline

V2 was established against CORE tag **`core-v1.0`** (commit `2840f8d`). Any later CORE change is
adopted by re-running the contract check, not by code sync.

## Requesting a CORE change

If V2 genuinely needs something only CORE can provide, write it up (what, why, which contract
entry, risk to CORE). It is implemented in CORE only after your explicit approval, as a CORE
change with CORE's own tests.
