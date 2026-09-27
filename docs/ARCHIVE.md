# Immutable daily forecast archive (M4 archive foundation)

Verification needs forecasts that were saved **before** the weather happened, with their exact
run time, and proof that nothing was changed afterwards. This archive provides that for the 36
fixed points in `archive/points.json`. It replaces the M0 monthly appendable release.

## What is captured each day

| File | Content | Rows per day |
| --- | --- | --- |
| `forecasts_<D>.parquet` | ECMWF IFS 0.25° (`ecmwf_ifs025`), GFS global (`gfs_global`; identical to CORE's `gfs_seamless` over India, run time checked on both GFS grids), ICON global (`icon_global`) daily Tmax, Tmin, rain, max gust at the 36 points for the next 10 IST days, plus Earth2Studio GFS (CORE store, nearest 0.25° cell) | 36 × 4 variables × (10 + 10 + 10 + ~9) days ≈ 5,600 |
| `core_risks_<D>.parquet` | All 11 CORE risk items per point exactly as CORE showed them (level, status, period, peak, agreement basis, matched official alert ids, CORE's per-model run note) | 396 |
| `core_daily_<D>.parquet` | CORE best-match daily values as shown (a blend: no single model run) | ~1,440 |
| `e2s_gfs_grid_<cycle>.nc` | Earth2Studio GFS daily grid over India (as in M0) | grid |
| `manifest_<D>.json` | files, SHA-256, rows, sources, every model's run time and coverage, expectation spec | — |
| `gap_report_<D>.json` | expected vs present, missing items, what the source does not provide | — |

## Time semantics

- `run_time_utc` — the model initialisation **instant** (UTC timestamp). For Open-Meteo models it
  is `last_run_initialisation_time` from the model's metadata, read immediately before and after
  the data request; if a new run lands in between, the request is repeated. For Earth2Studio it is
  the store's `issue_time`. `run_time_known` is therefore always **true** in this archive.
- `valid_date_ist` — a calendar **date** in India Standard Time (Parquet `date32`), never a timestamp.
- `lead_day = valid_date_ist − (IST calendar date of run_time_utc)`. A 00Z run is 05:30 IST, so
  its lead 1 is the next IST day; an 18Z run is 23:30 IST of the same IST date.
- `day_partial` — true when the run does not cover the whole IST day (always lead 0, which starts
  before the run; and trailing days beyond the run's last valid time, e.g. ECMWF 06Z/18Z runs end
  at ~6 days). Partial days are stored but never required and must be excluded from verification.

## Refusal rules (nothing incomplete is published)

`archive/validate.py` must pass before a release is created. It refuses when:

1. a file differs from the manifest, or any SHA-256 or row count does not match;
2. the schema or types differ, a required column is null, or `run_time_known` is false;
3. any `lead_day` disagrees with the rule above, or is negative;
4. a (point, model, run, valid date, variable) appears twice;
5. any **expected** value is missing — expected = every point × every variable the source provides ×
   every lead the run fully covers (from its own metadata);
6. a whole model or the CORE snapshot (36 points × 11 risks) is missing;
7. a value is outside a physically plausible range (unit mix-ups).

A refused day is recorded in the index (`index/refused/`) with its gap report; no release exists
for it. **Missing stays missing**: nothing is filled, interpolated or taken from another run.

## Immutability

- Repository setting **"Enable release immutability"** is on (M4, approved decision B2).
- One release per IST day: `archive-daily-YYYY-MM-DD`. It is created as a draft, every asset is
  downloaded and checked against the manifest, then published. Publication locks assets and tag.
- After publication the workflow tries to (1) add an asset, (2) overwrite an asset, (3) delete an
  asset; all three must be rejected, the published file must still match its checksum, and GitHub's
  `immutable` flag must be true. Results are stored in the index record.
- The **`archive-index`** branch (append-only, never merged into `main`) holds per day: manifest,
  SHA-256 of manifest and gap report, release URL, verification and immutability results, plus
  `INDEX.csv`. Its git history is the tamper-evident proof of when each file existed. Existing
  index records are never overwritten.

## Legacy M0 data

The M0 release `archive-2026-09` (mutable, appendable) is kept unchanged except for a LEGACY
note. An immutable copy is published as `archive-legacy-m0-2026-09` with
`legacy_manifest_m0_2026-09.json`: **provenance incomplete** — Open-Meteo run times were not recorded
(`run_time_known = false`) and the Earth2Studio file was overwritten once during M0. Not usable for
lead-time verification.

## Acceptance tests

- Offline: `pytest archive/tests` (lead rules, coverage, checksum, missing row, bad lead, failed
  model, unit mix-up, schema types).
- Live: `workflow_dispatch` with `inject = checksum | missing_row | bad_lead` must end with
  "Nothing was published" and a refusal record in the index.

## Not in this milestone

Backfill, the 109-station expansion, verification metrics, IMD normals, CAPE, IMERG.
