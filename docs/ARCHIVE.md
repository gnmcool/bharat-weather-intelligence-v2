# Immutable daily forecast archive (M4 archive foundation)

Verification needs forecasts that were saved **before** the weather happened, with their exact
run time, and proof that nothing was changed afterwards. This archive provides that for the 36
fixed points in `archive/points.json`. It replaces the M0 monthly appendable release.

## What is captured each day

| File | Content | Rows per day |
| --- | --- | --- |
| `forecasts_<D>.parquet` | ECMWF IFS 0.25° (`ecmwf_ifs025`), GFS global (`gfs_global`; identical to CORE's `gfs_seamless` over India, run time checked on both GFS grids), ICON global (`icon_global`) daily Tmax, Tmin, rain, max gust at the 36 points for the next 10 IST days, plus Earth2Studio GFS (CORE store, nearest 0.25° cell) | 36 × 4 variables × (10 + 10 + 10 + ~9) days ≈ 5,600 |
| `core_risks_<D>.parquet` | All 11 CORE risk items per point exactly as CORE showed them (level, status, period, peak, agreement basis, matched official alert ids, CORE's per-model run note; from schema version 2: CORE's rule text `criterion` and flood's wet-soil flag) | 396 |
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
7. a value is outside a physically plausible range (unit mix-ups);
8. (schema version 2) the CORE risk table differs from `CORE_RISK_SCHEMA`, CORE's rule text (`criterion`) is missing
   or empty on any row, a point lacks exactly one flood item, a flood item's wet-soil flag cannot be read from
   CORE's text (it is never guessed), or a non-flood row carries the flag.

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

The M0 release `archive-2026-09` (appendable and mutable during M0) keeps its two files unchanged.
Editing its notes after release immutability was enabled made GitHub mark it immutable as well
(27 Sep 2026); its title and notes say so. An immutable copy is published as `archive-legacy-m0-2026-09` with
`legacy_manifest_m0_2026-09.json`: **provenance incomplete** — Open-Meteo run times were not recorded
(`run_time_known = false`) and the Earth2Studio file was overwritten once during M0. Not usable for
lead-time verification.

## Measured (first release, 28 Sep 2026)

| Item | Value |
| --- | --- |
| Files per day | forecasts 17.5 KB · core_risks 9.3 KB · core_daily 5.3 KB · Earth2Studio grid 2.18 MB · manifest 3.8 KB · gap report 1.2 KB |
| Per day | ≈ 2.22 MB (points only ≈ 37 KB; the grid is 98 %) |
| Per month / year | ≈ 67 MB / ≈ 810 MB (points only ≈ 1.1 MB / ≈ 13.5 MB) |
| Rows per day | 5,616 forecast rows (5,184 required, 432 ICON days 8–10 stored empty and partial), 396 CORE risk rows, 1,440 CORE daily rows |
| GitHub Actions | ≈ 3 min per day (collect ≈ 2 min 15 s, validate 1 s, publish + verify 8 s, index 2 s) |
| Requests per day | ≈ 48 HTTP requests (3 multi-location Open-Meteo data requests ≈ 108 counted calls, metadata before/after, 36 CORE dashboards, 1 store download) |

## Acceptance tests

- Offline: `pytest archive/tests` (lead rules, coverage, checksum, missing row, bad lead, failed
  model, unit mix-up, schema types).
- Live: `workflow_dispatch` with `inject = checksum | missing_row | bad_lead` must end with
  "Nothing was published" and a refusal record in the index.

## Validation evidence: three intentional failed runs (expected)

On 28 Sep 2026 three `workflow_dispatch` runs were started **on purpose** with an injected fault to prove
the refusal path. Each one was required to fail, and did. They are acceptance evidence, not product
failures, and must stay in the Actions history.

| Run | Injected fault | Result | Index record |
| --- | --- | --- | --- |
| 36347335335 | `checksum` (a file altered after its SHA-256 was recorded) | refused, nothing published | `index/refused/2026-09-28_36347335335.json` |
| 36347404057 | `missing_row` (one expected forecast value removed) | refused, nothing published | `index/refused/2026-09-28_36347404057.json` |
| 36347567385 | `bad_lead` (one `lead_day` made inconsistent with its run time) | refused, nothing published | `index/refused/2026-09-28_36347567385.json` |

The real archive for that day, `archive-daily-2026-09-28`, was produced by a separate, uninjected run.

## Not in this milestone

Backfill, the 109-station expansion, verification metrics, IMD normals, CAPE, IMERG.

## Schema version 2 — CORE rule text (M4.4-D D1, approved 30 Sep 2026)

M4.4-D verifies what CORE issued (`docs/M4.4-D_PROSPECTIVE_VERIFICATION.md`, M4.4-D-SPEC-1.0). Decision Q5 adds
exactly two fields to `core_risks`, each with a verification purpose:

| Field | Type | Content | Purpose |
| --- | --- | --- | --- |
| `criterion` | string, required, non-empty | CORE's rule text for the item, verbatim from CORE's API | proves which rule produced the item (detects any change to CORE rules) |
| `flood_wet_soil` | bool; flood rows only (null otherwise) | whether CORE applied its wet-soil +1 level. Read from CORE's explanation: core-v1.0 writes `Rain-based indicator only (no river/drainage model).`, followed by ` Soil already wet.` when the modifier applies | only flood items without the modifier can be tied to the rain-only rule |

- No issue-time field is added. `core_generated_at_utc` and the period stay the authoritative timing fields, and
  issue times are never normalised.
- `SCHEMA_VERSION` = 2 in the manifest. Version 1 releases stay exactly as published. They are flagged **"rule
  text not archived"** on `archive-index` (`index/annotations/core-rule-text-not-archived.json`) and read with
  `CORE_RISK_SCHEMA_V1`; `core_rule_text_status(schema_version)` reports the flag.
- **Deployment:** the daily capture runs from `main`. The change takes effect only when it is merged into `main`,
  which needs the owner's approval. Until then, each new daily release is still version 1 and carries the flag.

