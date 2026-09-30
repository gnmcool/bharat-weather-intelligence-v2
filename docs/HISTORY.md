# Historical verification dataset and reference observations (M4.2)

Status: **probe stage.** No large backfill has been run. The full backfill starts only after the owner
reviews the probe report (`history/probe/<run_id>/` on the `archive-index` branch).

## Why a separate dataset

The prospective archive (`docs/ARCHIVE.md`) stores each forecast **with its exact model run time**,
saved before the weather happened, in immutable releases. Historical forecasts obtained now cannot meet
that standard: Open-Meteo's Previous Runs API gives, for each hourly valid time, "the value that was
predicted 24 h (48 h, … 7 × 24 h) before", **without saying which model run** produced it. So:

| | Prospective archive (M4.1) | Historical backfill (M4.2) |
| --- | --- | --- |
| Code | `archive/` | `history/` (imports nothing that writes to the archive) |
| Storage | immutable releases `archive-daily-*` | `archive-index` branch `history/…` (probe); later separate `history-*` releases |
| `dataset` | *(prospective only)* | `historical_backfill` |
| Run time | `run_time_utc` exact, `run_time_known = true` | `run_time_utc` **null**, `run_time_known = false` |
| Lead | `lead_day` = valid IST date − IST date of the run | `nominal_lead_day` = N of `previous_dayN` (value predicted ≥ N × 24 h before each hour) |
| Daily value | Open-Meteo daily aggregate of one run | our own IST-day aggregate of 24 hourly values, each possibly from a different run cycle |
| Validation | refused unless complete | each day marked `complete` (24 of 24 hours) or not; incomplete days keep `value = null` |

The two are never merged into one table. Any verification that uses both must report them separately.

## Plan (from the Step 1 feasibility findings only)

1. **Coverage matrix first** (`history/probe.py coverage`). For each model × variable × lead 1–7 ×
   month (the 15th of each month, Jan 2024 → Sep 2026), count the hours returned at one point
   (Ahmedabad). Models: `ecmwf_ifs025`, `gfs_seamless`, `gfs_global`, `icon_seamless`, `icon_global`.
   Variables: temperature, precipitation, gusts, CAPE (CAPE for availability only; no CAPE product).
   ECMWF 9 km (`ecmwf_ifs`) is **not** in scope: Step 1 gave no evidence it adds anything over 0.25°.
   The GFS temperature-only period before 2024 is recorded but not backfilled (it has no rain or gusts).
2. **Small sample backfill** for all 36 points: July 2024 (monsoon) and January 2025 (winter), for the
   models/variables/leads the matrix shows as available. Nothing interpolated, nothing taken from another
   lead or model; a missing hour makes that day incomplete.
3. **ERA5** (Open-Meteo archive, `era5`), same points and months: labelled *reanalysis*, secondary
   reference, ~6-day availability lag.
4. **METAR** (Iowa Environmental Mesonet archive): nearest station to each point, with distance and
   elevation difference stored. Daily Tmax, Tmin, max sustained wind, max reported gust, minimum
   visibility and counts of thunder/fog/rain **reports** (occurrence only). **METAR rainfall is never
   read** (the `p01m` field is a 0.00 placeholder in the Indian feed).
5. **IMD 0.25° gridded rainfall**, yearly files 2024 and 2025: daily rainfall at the nearest valid cell
   within **30 km** (decision B4), distance stored; beyond 30 km = unavailable (islands). IMD is the
   primary rainfall reference; ERA5 rainfall only secondary. **Date convention (measured, probe run
   36373096319):** an IMD file date D holds the 24 h *ending* 08:30 IST on D (IMD vs ERA5 r = 0.67 with
   this alignment, 0.22 without). It is stored under the window's start date D − 1, the same date as
   the model and ERA5 `precip_0830` for that window. Every probe re-checks this alignment and reports a
   problem if the best match is not at zero shift.
6. **IMERG** stays deferred (needs an Earthdata login; decision B6).
7. **Probe report**: request count and weighted Open-Meteo calls, rate-limit responses, bytes per row,
   projections for the full backfill, free-tier sufficiency, assumptions needing approval.

## Refusal rules for historical data

- A (model, variable, lead, month) cell the source does not provide is recorded as **not available**,
  never filled.
- A backfill job has an explicit expectation (points × days × variables × leads, taken from the matrix).
  It writes a coverage report comparing expected vs obtained; if anything expected is missing the job is
  marked **partial** in the report and the file name, and is never presented as complete.
- `run_time_known = true` in a historical row, a non-null `run_time_utc`, a lead outside 1–7 or a value
  on an incomplete day are validation errors.

## Not in M4.2

Skill scores, verification dashboards or UI, thresholds, risk rules, CAPE or IMERG products, CORE fixes,
probabilities or confidence.

## Probe results (28 Sep 2026)

Runs: **36373096319** (all steps; 110 min) and **36381151744** (IMD + ERA5 re-run after two fixes, 6 min).
Outputs: `archive-index` branch, `history/probe/<run>/`.

### Coverage matrix (one point, every IST day 1 Jan 2024 → 20 Sep 2026; complete = 24 of 24 hours)

| Model (archive name) | Temperature | Rain | Gusts | CAPE | Leads with data | Starts (lead 1) |
| --- | --- | --- | --- | --- | --- | --- |
| ECMWF IFS 0.25° (`ecmwf_ifs025`) | yes | yes | **never** | **never** | 1–7 | 5 Feb 2024 |
| GFS (`gfs_global` = `gfs_seamless`) | yes | yes | yes | yes | 1–7 | 20 Jan 2024 (temperature alone from 25 Mar 2021, gap 30 Dec 2023 – 19 Jan 2024; not used) |
| ICON (`icon_global` = `icon_seamless`) | yes | yes | yes | **never** | **1–6 (no lead 7)** | 20 Jan 2024 |

Lead N starts N − 1 days after lead 1. Short source outages (stored incomplete, never filled):
ECMWF rain leads 5 and 7, 17–23 Apr 2026; GFS CAPE leads 3 and 5, 18–19 Apr 2026; ICON leads 1–3,
4–6 (temperature/rain), 10–13 Apr 2026. ECMWF 9 km was not tested for backfill (out of scope).

**This corrects the Step 1 summary:** GFS and ICON start 20 Jan 2024, not March and July 2024 (Step 1
sampled only a few dates).

### Sample backfill (36 points × July 2024 + January 2025)

207,576 of 207,576 expected daily values complete (status `complete`); 234,360 rows including the
cells the source does not provide (ECMWF gusts, ICON lead 7), which are stored empty and listed as
"not provided". Stored with `run_time_known = false`. 274 KB Parquet.

### References (same points and months)

| Reference | Result |
| --- | --- |
| ERA5 (reanalysis) | 11,160 / 11,160 daily values complete |
| IMD 0.25° rain | 2024 and 2025 files obtained (4,964 valid cells, unchanged format); 34 / 36 points on their own cell; South Andaman (1,228 km) and Lakshadweep (369 km) unavailable. **2026 not published** (empty response) |
| METAR (IEM) | 145 stations in the network; only **6 / 36** points meet the proposed pairing rule (≤ 25 km, ±100 m). Of those only Delhi (VIDP) and Tiruchirappalli (VOTR) give complete days in both months. IEM has **no** 2024–25 reports for Chandigarh, Srinagar, Tezpur, Kishangarh (they report today). Daytime-only airports fail the day rule |

Spot checks against the sources: METAR VIDP 15 Jul 2024 and VOTR 10 Jan 2025 (Tmax, Tmin, minimum
visibility, observation count) match IEM exactly.

### Projection for the full backfill (1 Feb 2024 → latest, 36 points, 3 models, leads 1–7)

~19,300 Open-Meteo counted calls (previous runs ~16,600 + ERA5 ~2,600): about 2 days of the free daily
limit, 6 % of the monthly limit. ~3.6 M rows, ~5 MB Parquet. METAR ~544 IEM requests (throttled at ~1
per 30 s; several hours). IMD: 2 files, 25 MB each.

## M4.3 matched historical dataset (owner-approved 28 Sep 2026)

Scope: **1 Feb 2024 → 31 Aug 2026**, the 36 points, ECMWF IFS 0.25° / GFS / ICON, tmax, tmin, rain (IST day and
08:30 IST day), max gust, nominal leads 1–7. September 2026 is outside M4.3 (added later as a complete month).

| Release | Content |
| --- | --- |
| `history-YYYY-MM` (31, immutable) | `forecasts_history-*.parquet` (reconstruction, `run_time_known = false`), `reference_history-*.parquet` (ERA5 reanalysis, IMD, METAR), `matched_history-*.parquet` (each forecast value × each applicable reference), `metar_pairing_history-*.json`, `manifest_history-*.json` (SHA-256, rows, sources, processing version, code commit), `gap_report_history-*.json` (quality: expected / present / missing with reasons) |
| `history-imd-raw-2024`, `-2025` (immutable) | unmodified IMD yearly NetCDF, source metadata, download time, SHA-256, format check |
| `archive-index` branch `history/` | `index/<month>.json`, `refused/`, `imd-raw/`, `runs/`, `dryrun/`, `quality/`, `INDEX.csv` (append-only) |

Rules enforced by `history/backfill.py validate` (a month that fails is recorded under `refused/` and never published):
every expected (point, model, variable, lead, day) row present exactly once; every unavailable value has expected /
present / missing counts and a reason; any failed source retrieval refuses the month; METAR only for points meeting
≤ 25 km, |Δ elevation| ≤ 100 m and full-day coverage (no substitution); IMD ≤ 30 km; ERA5 labelled "ERA5 reanalysis";
matched values identical to the source tables. IMD 2026 unpublished → reference unavailable with that reason (no
substitute). Batches stop cleanly at the Open-Meteo free-tier budget or quota; a published month is never rebuilt.

Match map: tmax/tmin → ERA5, METAR; rain (IST day) → ERA5; rain (08:30 IST) → IMD, ERA5; gust → ERA5 (METAR gust is
not comparable: reported only when present). An unavailable reference never marks a forecast as failed.

**Corrections.** A published release is never modified. A correction is a new release `history-YYYY-MM-v2` whose notes
and manifest state what was wrong, which records are affected, why the new version differs, and that it supersedes
`history-YYYY-MM`; the index records both.

No skill scores, rankings or verdicts are computed in M4.3.

### Missing-value categories (processing version m4.3-2, owner-approved 28 Sep 2026)

Every unavailable value carries expected / present / missing counts and a reason; `classify_reason()` maps each
reason to one category. Categories are never merged.

| Category | Meaning | Reason text (starts with) |
| --- | --- | --- |
| A | source structurally unavailable (model / variable / lead does not exist) | `not provided by source` · `METAR reports a gust group…` (not comparable) |
| B | source archive not yet started | `before source archive start` |
| C | source outage / partial availability, retrieval succeeded | `source outage: N of 24 hours missing (retrieval succeeded…)` (m4.3-1 wording: `source hours missing`) |
| D | request/download failure — the month is refused and never published | `source retrieval failed` (refusal records only) |
| E | reference unavailable | IMD year not published · no METAR reports that day · value missing in source file |
| F | temporal incompleteness of a reference | `incomplete reporting coverage` (METAR 6-h blocks / < 20 reports) · `ERA5 hours missing` |
| G | spatial pairing failure | `no METAR match` (> 25 km or \|Δelev\| > 100 m) · `no IMD cell within 30 km` |

Source archive starts (`SOURCE_ARCHIVE_START`): ECMWF IFS 0.25 — first lead-1 value 2024-02-04 00 UTC (temperature),
2024-02-03 22 UTC (precipitation); lead N starts N − 1 days later. A day is B only if **every** missing hour precedes
the start; otherwise C. GFS and ICON have no start inside the M4.3 scope.

**Batch 1 (m4.3-1) wording.** Releases `history-2024-02` … `history-2024-10` use `source hours missing` (→ C by
default). The append-only annotation `archive-index:history/annotations/2024-02-ecmwf-archive-start.json`
reclassifies the 6,804 ECMWF rows of 1–10 Feb 2024 to B, bound to the release's manifest SHA-256; the quality report
applies it only if the hash matches. No released value or file was changed.

### Publication failures (owner-approved 30 Sep 2026)

Publishing is retry-safe: the draft is created first, assets are uploaded one by one (an asset already present counts
only if its SHA-256 matches the manifest; a mismatch stops publication), the complete draft is verified against the
manifest, and only then is the release published and its immutability checked. If publication fails, the month is
recorded append-only as **"publication failure (data valid)"** in `archive-index:history/publication_failed/` and
`INDEX.csv` (manifest and gap-report SHA-256, error, release state afterwards). This is an infrastructure status, not
a data/source category (A–G); the month is not marked published and the batch continues. Batch 3's March 2026 draft
(run 36666584479, HTTP 422 duplicate asset) predates this handling.
