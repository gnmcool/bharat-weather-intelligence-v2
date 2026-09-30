# M4.4-A hold — source probe report (run 36684062500) — revision 2

**Revision 2 (30 Sep 2026, owner review):** wording only. "UNRESOLVED, with support for Tmax" is replaced with
the owner's wording for the thinning simulation. No number, observation or verdict changed. Both hypotheses remain
UNRESOLVED. Revision 1 (`probe_report.md`) is kept unchanged.

**Status:** the 30 held primary cells remain held. No release, census, Gate 2 result or methodology was changed. No
VM-1.2 was created and M4.4-B has not started.

**Record:** archive-index `history/verification/source-probe/36684062500/` (raw responses, `probe_result.json`,
SHA256SUMS). Report and analysis: `…/36684062500-report/`. Every number below is reproduced by `analysis.py` from
`probe_result.json`; its output is in `analysis_output.txt`.

## 1–3. Source, request parameters, dates and points

| Item | Value |
| --- | --- |
| Source | Open-Meteo Previous Runs API, `https://previous-runs-api.open-meteo.com/v1/forecast` — the endpoint and code path (`history/sources.previous_runs`) the archive used |
| Probe code | commit `ced65d6`; the workflow verified it was byte-identical (`git diff --exit-code ced65d6 HEAD -- verification history`) |
| Run | GitHub Actions run 36684062500 (one-off, no schedule), 30 Sep 2026 |
| A | `models=gfs_global`, `hourly=precipitation_previous_day1..7`, `timezone=GMT` |
| B | `models=ecmwf_ifs025`, `hourly=temperature_2m_previous_day1..7`, `timezone=GMT` |
| Points | IN-07-delhi (28.6370, 77.1090), IN-33-614 Tiruchirappalli (10.8700, 78.7350), IN-32-594 Thrissur (10.4610, 76.2980) |
| Dates | 15 Jul 2024, 15 Jan 2025, 15 Jul 2025; each request covers `start_date = D−1` to `end_date = D+1` (72 UTC hours) |
| Requests | 6 request pairs (2 targets × 3 dates, each made twice), 3 locations per request; no rate limiting or errors |
| Archive comparison | releases history-2024-07, -2025-01 and -2025-07, re-verified in the run (published, immutable, manifest SHA-256 = archive-index record at 11d29f6) |

A preceding run (36683555123) failed **before** any source request. The workflow's release-verification step could
not read a certificate path that exists only in the workspace. Only the workflow was fixed; the probe code was not
changed. No outputs were written for that run.

## Documented source behaviour (provider documentation, read 30 Sep 2026)

- **Previous Runs API (Open-Meteo):** "_previous_day1_ is the value that was predicted 24 hours before valid time,
  _previous_day2_ 48 hours before, and so on up to day 7." Global models update every 6 hours.
- **GFS 0.25° (Open-Meteo GFS page):** temporal resolution "Hourly, 3-hourly after 120 hours". The page also says
  that after 120 hours values are interpolated from 3-hourly to 1-hourly. **NOAA/EMC:** GFS "produces hourly
  forecast output for the first 120 hours, then 3 hourly for days 5-16."
- **ECMWF IFS 0.25° open data (Open-Meteo ECMWF page):** "3-Hourly, 6-hourly after 144 hours"; "The Open-Meteo API
  dynamically interpolates all data to a consistent 1-hourly time-series". The interpolation method is not
  documented. **ECMWF open data page:** steps "For times 00z & 12z: 0 to 144 by 3, 150 to 360 by 6. For times 06z &
  18z: 0 to 144 by 3."
- Not documented: how Open-Meteo converts GFS 3-hourly precipitation to hourly values, or how it interpolates
  temperature.

The documentation implies that nominal lead 5 corresponds to forecast hours of at least 120, and lead 6 to at least
144. This is an inference from documentation, not an observation: the API does not return run times or forecast
hours, and the archive has `run_time_known = false`.

## 4–5. Available hours and temporal spacing (observed)

Every requested series was complete: 72 of 72 hours at every lead, point and date, for both targets. The API
returns hourly values at all leads. The spacing below is inferred from the pattern of the values.

**A. GFS precipitation (9 point-dates, 72 h each)**

| Lead | Wet 3-h groups with three equal hourly values, aligned so each group ends at 03/06/09… UTC | Same, other two alignments | Share of rain in hours 00/06/12/18 UTC | 72-h total, all 9 point-dates |
| --- | --- | --- | --- | --- |
| 1–4 | 0–4 % (0/83, 1/75, 3/80, 2/87) | 0–4 % | 0.16–0.17 | 127–169 mm |
| 5 | **47 %** (30/64) | 8–12 % | **0.35** | 38.7 mm |
| 6 | **58 %** (36/62) | 12–20 % | 0.10 (0.25 in hours 04 and 05) | 49.8 mm |
| 7 | **59 %** (30/51) | 15–25 % | 0.13 | 36.3 mm |

**Observed:**
- The hourly rain series changes structure between lead 4 and lead 5. From lead 5 onward, about half of the wet
  3-hour groups are three identical values, aligned to 3-hourly steps ending at 03, 06, 09 … UTC. That is the
  signature of a 3-hour total spread evenly over its hours.
- Leads 5–7 also show an uneven 6-hour pattern that leads 1–4 do not.
- In this sample, the 72-hour totals at leads 5–7 are 23–30 % of those at leads 1–4.

**B. ECMWF temperature_2m (9 point-dates, 72 h each)**

| Lead | Mean \|2nd difference\| at UTC hour mod 6 = 0, 1, 2, 3, 4, 5 | Mean daily range |
| --- | --- | --- |
| 1–5 | ≈0.28–0.34, 0.18–0.21, 0.21–0.22, **0.35–0.38**, 0.21–0.22, 0.17–0.20 | 6.97–7.41 °C |
| 6 | 0.29, 0.22, **0.11, 0.14, 0.11**, 0.20 | 6.54 °C |
| 7 | 0.30, 0.23, **0.11, 0.12, 0.11**, 0.21 | 6.50 °C |

**Observed:**
- At leads 1–5 the curvature is concentrated at hours ≡ 0 and 3 (mod 6), consistent with smooth interpolation
  between 3-hourly nodes.
- At leads 6–7 the curvature at hours ≡ 2–4 falls by about 60 %, leaving nodes at 00/06/12/18 UTC only. This is
  consistent with 6-hourly nodes.
- The daily range falls by about 0.7 °C.
- The interpolation is not linear, so the probe's straight-line node test reports k = 1 at every lead. That test
  cannot detect spacing here; it is not evidence of hourly data.

## 6. Repeated-request comparison

The probe reports `deterministic: false` for all six pairs. **This is inconclusive, and is a flaw in the probe's
design:**
- it compared the two responses byte for byte;
- every response contains `generationtime_ms`, the server's own processing time, which changes on each call;
- only the first response of each pair was saved.

So the value-level repeat comparison was **not** established. It was not re-run, because the scope allowed one run.

**Cross-time consistency was established independently (§8):** the source values fetched on 30 Sep 2026 reproduce
the values archived at backfill time exactly.

## 7–8. Archive aggregation applied to raw source values, compared with the archive

The archive's own `aggregate_daily()` (history/common.py) was applied to the probed hourly values: IST-day sum,
IMD 08:30 window sum, IST-day max and min. This covers 126 daily values per question (9 point-dates × 7 leads × 2
daily variables). The **maximum difference from the archived value was 1.5 × 10⁻⁶**, which is float32 storage
rounding, for every lead of both questions.

- The archived daily values, including the lead-5/6 rain reduction and the lead-6 temperature step at these
  point-dates, are exactly what the archive's aggregation gives from the source's hourly values.
- The archive transformation **preserves** the source representation. It does **not introduce** either effect.

## 9. Verdicts

**A — GFS rainfall, around forecast hour 120**

- **Representation change at lead 5: CONFIRMED.** It is documented (3-hourly after 120 h), and it is observed
  (evenly spread 3-hour groups, and a 6-hour pattern from lead 5 onward, absent at leads 1–4).
- **Our archive preserves it: CONFIRMED** (exact reproduction).
- **"Does the available evidence establish that source temporal resolution is responsible for the observed
  lead-dependent metric change?" — No. UNRESOLVED.**
  - Spreading a 3-hour total evenly over its hours does not reduce the total, so 3-hourly resolution by itself does
    not explain a lower daily sum.
  - The 6-hour pattern and the low lead-5–7 totals show that something in the source representation changes at
    lead 5. The probe does not establish the mechanism: there is no native GFS output to compare against.
  - The sample (9 point-dates, dominated by Thrissur in July) is too small to measure the size of the reduction.

**B — ECMWF temperature, around forecast hour 144**

- **Representation change at lead 6: CONFIRMED.** It is documented (6-hourly after 144 h; 06/18z runs end at
  144 h), and it is observed (curvature consistent with 6-hourly nodes and a smaller diurnal range at leads 6–7 only).
- **Our archive preserves it: CONFIRMED** (exact reproduction).
- **"Does the available evidence establish that source temporal resolution is responsible for the observed
  lead-dependent metric change?" — No. UNRESOLVED.**
  - *Inference, not source evidence:* thinning the lead-5 series to 00/06/12/18 UTC nodes and re-interpolating
    lowers IST-day Tmax by 0.7–1.2 °C (spline, linear or PCHIP interpolation), against an archived lead-6 Tmax step
    of −0.5 to −1.4 °C. **The thinning simulation is directionally and approximately quantitatively consistent with
    the observed Tmax step, but does not establish causality.**
  - The observed lead-6 minus lead-5 difference in the probe sample (−0.48 °C) also contains real differences
    between the two runs, which the probe cannot separate.
  - The small archived Tmin step (about −0.2 °C) is **not** explained: thinning raises Tmin slightly (+0.11 °C).

## What is established vs inferred

- **Established:**
  - The source representation changes at nominal lead 5 (GFS rain) and at lead 6 (ECMWF temperature).
  - Both changes coincide with the documented resolution changes.
  - The archive reproduces the source exactly, and our processing introduced neither step.
- **Not established:** that temporal resolution *causes* the metric changes. For GFS rain the mechanism of the
  reduction is unknown. For ECMWF Tmax, the thinning simulation is directionally and approximately quantitatively consistent with the
  observed Tmax step, but does not establish causality. For ECMWF
  Tmin it is unexplained.
