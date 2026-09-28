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
