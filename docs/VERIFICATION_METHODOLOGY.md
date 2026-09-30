# BWI verification methodology

**Version:** **VM-1.1**. VM-1.0 (M4.3) was approved by the owner on 30 Sep 2026 (draft VM-1.0-draft, commit
`f223a05`, approved with one modification: heat/cold verification is a future extension, §10); decisions in §20.
VM-1.1 records the four owner decisions of the M4.4-A Gate 1 review (30 Sep 2026) — missing-data reason precedence,
islands, elevation, primary comparisons — and fixes the bootstrap implementation details that VM-1.0 left open (§21).
VM-1.1 changes no eligibility rule, floor or reference: every pair eligible under VM-1.0 is eligible under VM-1.1.
Any change to this document requires a new version number.

**Inputs this document is built on:** the M4.0 feasibility report (`docs/evidence/m4_step1_probe_report.json`), the
M4.1 prospective archive (`docs/ARCHIVE.md`), the M4.2/M4.3 historical dataset (`docs/HISTORY.md`, 31 immutable
releases `history-2024-02` … `history-2026-08`), and CORE's risk criteria **as published by CORE's public API**
(`/api/v1/dashboard` → `risks[].criterion`, read 30 Sep 2026). Where this document and the older
`docs/VERIFICATION.md` (M0) differ, this document supersedes it (IMERG is not currently a reference; Earth2Studio
GFS is not an independent model and is not in the historical dataset).

---

## 1. Purpose and scope

Three different questions. They use different data, answer different users, and are **never combined into one
score**.

| Code | Question | Unit being judged | Data |
| --- | --- | --- | --- |
| **A. Model skill** | How accurately did ECMWF, GFS and ICON forecast Tmax, Tmin, rain (and gust, see §3)? | each model separately | historical dataset (nominal leads) now; prospective archive (exact leads) later |
| **B. Model agreement** | Does the observed outcome differ when 0, 1, 2 or 3 of the three independent models forecast an event? | the agreement count, not a model | historical dataset |
| **C. CORE risk-engine performance** | When CORE issued a risk level, how often was the corresponding event observed? | CORE's issued risk items | CORE's stored outputs — **prospective archive only** (see §10) |

A says nothing about CORE's usefulness; C says nothing about which model is best; B is not a probability.

---

## 2. Data sources

### 2.1 Forecasts

| Source | Where archived | Period | Run time | Lead |
| --- | --- | --- | --- | --- |
| ECMWF IFS 0.25° (`ecmwf_ifs025`) | historical releases; prospective daily releases | hist.: 5 Feb 2024 → 31 Aug 2026; prosp.: 28 Sep 2026 → | hist.: **unknown** (`run_time_known = false`); prosp.: exact | hist.: nominal 1–7; prosp.: exact `lead_day` 0–10 |
| NCEP GFS (`gfs_global`) | same | hist.: 1 Feb 2024 →; prosp.: 28 Sep 2026 → | same | same |
| DWD ICON (`icon_global`) | same | hist.: 1 Feb 2024 →; prosp.: 28 Sep 2026 → | same | hist.: nominal 1–6 (no lead 7) |
| Earth2Studio GFS (`e2s_gfs025`) | **prospective archive only** (not in the historical dataset) | 28 Sep 2026 → | exact | exact |

**Earth2Studio GFS is the same GFS model**, processed by CORE. It is never an independent model, never counted in
agreement (B), and when verified (prospectively) it is reported as "GFS as processed by Earth2Studio" next to GFS,
not as a fourth model. FourCastNet output is not archived and is out of scope.

CORE's own displayed values are Open-Meteo **best-match blends** (no single run); CORE's issued risk items are stored
only in the prospective archive (`core_risks_<D>.parquet`, from 28 Sep 2026).

### 2.2 References

| Reference | Nature | Variables in the archive | Coverage | Label to use |
| --- | --- | --- | --- | --- |
| **ERA5** (Open-Meteo archive, `era5`) | reanalysis (model + assimilated observations), ~31 km grid, ~6-day lag | tmax, tmin, precip (IST day), precip_0830, gust_max | all 36 points, all 31 months, complete | "ERA5 reanalysis" — **never "observation"** |
| **IMD 0.25° gridded rain** | rain-gauge analysis | precip_0830 only | valid dates **1 Feb 2024 → 30 Dec 2025**; 34 of 36 points (nearest valid cell ≤ 30 km); **none for 2026** (file not published); South Andaman and Lakshadweep unavailable (category G) | "IMD gridded rain-gauge analysis" |
| **METAR** (Iowa Environmental Mesonet) | airport observations | tmax, tmin (integer °C), max sustained wind, gust when reported, min visibility, weather-code counts | only 6 points meet the matching rule (≤ 25 km, \|Δelev\| ≤ 100 m, full-day reporting): Delhi VIDP and Tiruchirappalli VOTR near-complete; Imphal VEIM partial; Raipur VERP, Chandigarh VICG, Puducherry VOPC mostly unavailable | "METAR station observation" |
| IMERG | satellite estimate | — | **not implemented** (needs Earthdata, decision B6) | — |

Fixed rules: **METAR rainfall is never used** (`p01m` is a placeholder in the Indian feed). A missing reference is
never replaced by another reference or fabricated; ERA5 rain is never presented as an IMD substitute.

---

## 3. Variables

| Variable | Forecast field | Reference(s) | Unit | Aggregation | Verifiable now? | Known limitations |
| --- | --- | --- | --- | --- | --- | --- |
| Tmax | `tmax` | ERA5 (all points); METAR (matched points) | °C | max of 24 hourly values in the IST day | **Yes** (ERA5: agreement with reanalysis; METAR: 2–3 stations) | grid vs point representativeness; high-altitude points (§12); METAR integer °C, half-hourly sampling |
| Tmin | `tmin` | same | °C | min of 24 hourly values | **Yes**, same caveats | same |
| Rain, IMD day | `precip_0830` | IMD (2024–2025); ERA5 | mm | sum of 24 hourly totals, 08:30 → 08:30 IST, stored under the start date | **Yes** vs IMD for 1 Feb 2024 – 30 Dec 2025; vs ERA5 for all months | point vs 0.25° cell; IMD cell distance ≤ 30 km; rain-gauge density varies |
| Rain, IST day | `precip` | ERA5 | mm | sum of 24 hourly totals ending 19:00 Z … 18:00 Z (23:30 → 23:30 IST, 30 min earlier than the calendar day) | vs ERA5 only (secondary) | no gauge reference on this window |
| Max gust | `gust_max` | ERA5 gust (model-diagnosed) | km/h | max of 24 hourly values | **Not verifiable against observations.** ERA5-agreement only, labelled exploratory. ECMWF has no gust (A). METAR gust is not comparable (reported only when present; sustained wind is not gust) | reanalysis gusts are a diagnostic, typically smoothed |

Out of scope (not in the dataset): CAPE, visibility, weather codes from models, RH, soil moisture, 30-day rain
normals.

---

## 4. Lead-time definition

Four different times — never mixed:

| Term | Meaning | Field |
| --- | --- | --- |
| run (initialisation) time | when the model run started | historical: **unknown** (`run_time_utc` null); prospective: `run_time_utc` |
| valid date | the IST calendar day (or IMD rain day, §5) the value describes | `valid_date_ist` |
| lead day | how far ahead the value was predicted | historical: `nominal_lead_day`; prospective: `lead_day` |
| retrieval time | when BWI downloaded the data | `retrieved_at_utc` — provenance only, never used in scoring |

**Historical Day N (N = 1…7) = nominal previous_dayN.** Every one of the 24 hourly values that make up the daily
value was predicted **at least N × 24 hours before its valid hour** (Open-Meteo Previous Runs). The model run is not
identified, and the 24 hours of one day may come from different runs. The effective lead of each hour lies between
24N h and 24N h plus the source's update interval. Day N is therefore "a forecast at least N days ahead", not "the
day-N output of a known run".

**Prospective lead_day** = valid IST date − IST date of the exact run. A 00 UTC run's lead_day 1 covers hours
18.5–42.5 h ahead; historical Day 1 hours are ≥ 24 h ahead. **The two are different quantities and are never pooled**
(separate results, separate `lead_type` field, §16).

**Eligibility (lead):** historical samples require `dataset = historical_backfill`, `run_time_known = false`,
`nominal_lead_day ∈ 1…7`. Prospective samples require `run_time_known = true`, `day_partial = false`,
`lead_day ≥ 1`.

---

## 5. Temporal alignment

- **Temperature and gust:** IST calendar day, identical construction for forecast and ERA5 (24 hourly values
  00:30…23:30 IST). METAR: max/min of all reports in the IST day, only if the day meets the METAR completeness rule.
- **Rain — two windows exist; each experiment names its window:**

| Experiment | Forecast | Reference | Why |
| --- | --- | --- | --- |
| R-IMD (primary rain verification) | `precip_0830` | IMD `precip_0830` | IMD defines its rain day and its 24-h rain categories on 08:30 → 08:30 IST. IMD file date D (window end) is stored at D − 1; the alignment was checked in every monthly release: best at zero shift in every month with rain (Feb 2024 – Nov 2025), a tie in dry Dec 2025, not applicable in 2026 (no IMD). |
| R-ERA5-IST (secondary) | `precip` | ERA5 `precip` | same window CORE's daily values use (IST day) |
| R-ERA5-0830 (secondary, cross-check) | `precip_0830` | ERA5 `precip_0830` | allows like-for-like comparison with R-IMD on the same days |

Results from different windows are never merged. A rain threshold is applied on the window of the experiment it
belongs to.

---

## 6. Missing-data rules

| Category | Meaning | Treatment |
| --- | --- | --- |
| A | not provided by source (ECMWF gust; ICON lead 7; METAR gust as a reference) | the (model, variable, lead) cell is **not defined**: excluded from that model's results and from every comparison that would include it; reported as "not provided", never as poor skill |
| B | before source archive start (ECMWF, 1–10 Feb 2024; annotation `2024-02-ecmwf-archive-start`) | excluded; reported as a coverage note |
| C | source outage (April 2026: ECMWF rain leads 5/7, 17–23 Apr; ICON 9–13 Apr) | excluded; **never counted as a forecast error**; reported as a coverage note per model |
| D | request/download failure | a month with D is not published; none remain (Sep 2025 recovered). If ever present: excluded, reported |
| E / F / G | reference unavailable / incomplete / not spatially matched | the pair is excluded; reported in reference coverage |

**Missing is never zero.** A day with fewer than 24 hourly values has no value and no pair.

**Reason precedence when both sides are unavailable (VM-1.1).** Each excluded pair keeps **both** sides' categories
(`forecast_category`, `reference_category`; "none" when that side was available). For headline counts one primary
reason is assigned: **D > C > B > A > E / F / G** (download failure, source outage, before archive start, not
provided by source, then the reference/spatial limitations). The primary reason is a counting convention only; the
other side's reason is never discarded and is reported (`reference_unavailable_E/F/G`, `n_both_unavailable`, and the
exclusion table by both categories). Example: ICON lead 7 at an island point for IMD rain → primary A, reference G
kept. Historical archive data are not changed.

**A forecast/reference pair is eligible for scoring only if all hold:** (1) forecast `complete = true` (24 of 24
hours; no A–D reason); (2) reference `complete = true`; (3) same variable, same window (§5), same valid date,
same point; (4) spatial rule met (METAR matched; IMD cell ≤ 30 km; ERA5 grid cell ≤ 30 km); (5) lead eligibility
(§4). **Model comparisons use the intersection sample:** only (point, date, lead) combinations where every compared
model and the reference are eligible. Consequently gust comparisons are GFS vs ICON only, and lead 7 comparisons are
ECMWF vs GFS only.

---

## 7. Continuous metrics

For eligible pairs *(fᵢ, oᵢ)*, *i = 1…n*, error *eᵢ = fᵢ − oᵢ*:

| Metric | Definition | Meaning | Use |
| --- | --- | --- | --- |
| Mean bias | (1/n) Σ eᵢ | systematic over- (+) or under- (−) forecasting | always report with MAE; for temperature, shows grid/elevation offsets |
| MAE | (1/n) Σ \|eᵢ\| | typical error size, in the variable's unit | primary accuracy measure for Tmax, Tmin, rain |
| RMSE | √((1/n) Σ eᵢ²) | error size weighting large errors more | report beside MAE; for rain flag as dominated by a few heavy-rain days |

Also reported with every metric: n, number of distinct valid dates, number of points, reference label, window,
lead type. Rain MAE/RMSE are reported for all eligible days and separately for days where the reference ≥ 2.5 mm
(approved: 2.5 mm is IMD's standard "rainy day", an **analytical classification only**; it must never become a BWI
risk threshold).

Breakdowns: by model × variable × lead (always); by season and by region only when the sample floor (§11) is met;
per point only for METAR stations and as a diagnostic list, never ranked. **No overall "BWI score"** — combining
variables with different units and references has no scientific meaning here.

---

## 8. Rain events (detection) — separate from continuous error

Thresholds: **only CORE's existing M-RAIN categories** (IMD 24-h categories as published by CORE):
Watch ≥ 35.6 mm, Alert ≥ 64.5 mm, Severe ≥ 115.6 mm (per 24 h). No new thresholds.

Contingency table per threshold τ (event = value ≥ τ), per model × lead × window:

| | Reference ≥ τ | Reference < τ |
| --- | --- | --- |
| Forecast ≥ τ | hit *a* | false alarm *b* |
| Forecast < τ | miss *c* | correct negative *d* |

POD = a/(a+c); FAR (false-alarm ratio) = b/(a+b); CSI = a/(a+b+c); frequency bias = (a+b)/(a+c); base rate
= (a+c)/n. All four counts and the base rate are always published with the ratios. Primary: R-IMD (08:30 window,
the window on which IMD defines the categories). ERA5 event results are secondary and labelled (ERA5 under-represents
localised convective rain). Gust events at CORE's M-WIND thresholds (50 / 62 / 89 km/h) are **not verified against
observations** (no observed gust reference); an ERA5-agreement table may be shown, labelled exploratory.

---

## 9. Model-agreement analysis (B)

- Models counted: **ECMWF, GFS, ICON only.** Earth2Studio GFS never adds agreement (and is absent historically).
- Sample: (point, valid date, nominal lead, threshold τ) where **all three models are eligible** (so k ∈ {0,1,2,3}).
  This excludes lead 7 (ICON: A), gust (ECMWF: A), 1–10 Feb 2024 ECMWF (B) and April 2026 outage cells (C).
  A "2 of 2 available" group is not merged with "2 of 3".
- Definition (daily): k = number of the three models with forecast ≥ τ on that valid date at that lead. τ = CORE's
  M-RAIN thresholds (35.6 / 64.5 / 115.6 mm); reference R-IMD (primary) or ERA5 (secondary, labelled).
- CORE-style definition (for §10 only): CORE counts "k of 3 models reach the same risk level (within one level)
  within ±1 day of the peak" (`MODEL_AGREEMENT.md`). That rule is used when judging CORE's issued items, not for the
  daily historical analysis.
- Result per k: n, number of days with the reference ≥ τ, their ratio (observed relative frequency) with a 95%
  bootstrap interval (§14). Secondary: by model combination (e.g. only GFS vs only ECMWF within k = 1).
- Wording (fixed): "In the archived sample (period, points, reference), when k of 3 models forecast ≥ τ, the reference
  reached ≥ τ on x of n days." Never "probability", "chance" or "confidence". A calibrated statement may be proposed
  only after this analysis, as a separate decision.
- Floors: each k-group needs n ≥ 100 and ≥ 10 reference events to show a frequency; otherwise "insufficient sample".

---

## 10. CORE / BWI risk verification (C) — separate from A and B

**C1 — CORE's actual issued outputs (primary).** Source: `core_risks_<D>.parquet` in the prospective daily releases
(36 points × 11 risks per day, from 28 Sep 2026). CORE's historical outputs before 28 Sep 2026 were **not recorded
and cannot be reconstructed**; C1 therefore starts with the prospective archive.

For each archived risk item: issued level L (0 None … 3 Severe), issue date, period (`period_start`–`period_end`).

| Term | Definition |
| --- | --- |
| Event window | `period_start`…`period_end` if given; if CORE gives none, the 7 IST days after the issue date |
| Observed event at level ≥ ℓ | the reference meets **CORE's own published criterion for level ℓ** on at least one day in the window |
| Hit | L ≥ ℓ and observed ≥ ℓ |
| False alarm | L ≥ ℓ and not observed ≥ ℓ |
| Miss | L < ℓ and observed ≥ ℓ within the 7 days after issue |
| Correct negative | L < ℓ and not observed ≥ ℓ |

Tables for ℓ = Watch, Alert, Severe. CORE's issued level is judged as issued; where the issued level contradicts
CORE's written criterion (e.g. CORE-2, heat), the case is listed, not corrected.

Which CORE risks can be verified, using only CORE's existing criteria:

| CORE risk | Criterion (CORE, verbatim basis) | Reference | Status |
| --- | --- | --- | --- |
| rain (M-RAIN) | 24-h rain ≥ 35.6 / 64.5 / 115.6 mm | IMD (not 2026), ERA5 | **verifiable** (IMD gap in 2026, §15) |
| heat (M-HEAT) | Tmax ≥ 40 °C plains & departure ≥ 4.5 / 6.5 °C; Watch: departure ≥ 3 °C | ERA5/METAR Tmax **plus a normal** | **future extension** — needs a normals input and a terrain class that are not in the archive; not part of M4.4, and no reference (e.g. NASA POWER) is added for it at this stage |
| cold (M-COLD) | Tmin ≤ 10 °C plains & departure ≤ −4.5 / −6.5 °C | same | **future extension**, as heat |
| wind (M-WIND) | daily max gust ≥ 50 / 62 / 89 km/h | ERA5 gust only | exploratory only (no observed gust) |
| flood (M-FLOOD) | 72-h rain ≥ 115.6 / 204.5 / 300 mm; +1 level with soil moisture | IMD/ERA5 rain (3-day sums) | rain part only; soil-moisture part not verifiable |
| thunderstorm, lightning (M-TS) | model weather codes, CAPE | none as a system reference | **not verifiable** as a system forecast; METAR thunderstorm reports at matched stations may be shown as **station-level supplementary occurrence only** (approved), never extrapolated |
| fog (M-FOG) | visibility < 1000 / 200 / 50 m | METAR visibility (matched stations) | **station-level supplementary occurrence only** (approved), never extrapolated nationally |
| fire, drought, cyclone | heuristic / 30-day rain vs normal / official only | none suitable | **not verifiable** (cyclone is an official alert, not a system forecast) |

**C2 — "historical rule replay" (approved).** CORE's M-RAIN thresholds and "k of 3" logic applied to the historical
per-model forecasts. This is **not CORE's output** and **not historical CORE performance** (CORE uses a best-match
blend and its own runs, which were not recorded before 28 Sep 2026). It is always called "historical rule replay" and
reported apart from C1 and from A/B.

Raw model skill (A) and CORE risk performance (C) are different analyses: a good model can feed a poorly calibrated
rule, and vice versa.

---

## 11. Sample floors (approved — publication/reporting floors)

These are **publication and reporting floors**. A metric is published only if its floor is met; otherwise the cell shows **"insufficient sample"** (with n) and no
number.

| Result type | Floor |
| --- | --- |
| Continuous metric, pooled (overall / model / lead / variable) | n ≥ 300 eligible pairs **and** ≥ 60 distinct valid dates **and** ≥ 10 points |
| Continuous, by season or region | same n and dates; region ≥ 3 points |
| Continuous, single point (METAR stations) | ≥ 90 eligible days |
| Event POD | ≥ 20 reference events |
| Event FAR | ≥ 20 forecast events |
| CSI / frequency bias | both of the above |
| Agreement group (B) | n ≥ 100 and ≥ 10 reference events per k |
| CORE risk (C1), per risk type and level | ≥ 20 issued items at that level (FAR) and ≥ 20 observed events (POD); in any case not before 90 days of prospective archive |
| "Model X differs from model Y" | paired intersection sample meeting the pooled floor **and** a 95% paired bootstrap interval of the difference that excludes 0 |

Daily values at 36 points are correlated in space and time, so n overstates independent information; the interval
method (§14) accounts for this, and the floors are minimums, not proofs.

---

## 12. Geography

- The 36 points are **one representative district point per State/UT** (the district nearest the mean of the state's
  district centroids). They are not random, not area- or population-weighted, and **not a nationally representative
  sample**. A pooled result means "average over the 36 state points", never "India".
- No extrapolation to the 724 districts, or to any district that is not an archive point.
- Regions (approved, following IMD's homogeneous regions): North-West 10 (J&K, Ladakh, HP,
  Uttarakhand, Punjab, Chandigarh, Haryana, Delhi, UP, Rajasthan); Central 7 (Gujarat, DNH-DD, MP, Chhattisgarh,
  Maharashtra, Goa, Odisha); South Peninsula 6 (AP, Telangana, Karnataka, Kerala, TN, Puducherry); East & North-East
  11 (Bihar, Jharkhand, WB, Sikkim, Assam, Meghalaya, Arunachal, Nagaland, Manipur, Mizoram, Tripura); Islands 2
  (Andaman & Nicobar, Lakshadweep) — always reported separately and **never merged into mainland regional results**
  (no IMD reference, G).
- High-altitude flag: point elevation ≥ 1,000 m (90 m DEM, stored in each release's pairing file): Ladakh 4,983 m,
  J&K 2,940 m, Sikkim 2,470 m, HP 1,744 m, Meghalaya 1,366 m, Uttarakhand 1,141 m. Temperature results for these are
  reported separately (grid-terrain representativeness).
- METAR results are per station (6 matched; 2 near-complete); never pooled into a national figure.
- **Islands (VM-1.1):** pooled results cover all 36 archive points wherever pairs are eligible, **including the
  island points** (for IMD rain the islands have no cell within 30 km, so they are G and absent). Islands are never
  silently removed from pooled results. Regional results keep islands as their own region; when that region fails
  the floor it is published as "insufficient sample".
- **Elevation (VM-1.1):** diagnostic only. Reported: archive point elevation, the ≥ 1,000 m flag, and the METAR
  station elevation difference where available. No finer elevation bands; forecasts and references are never
  elevation-adjusted.

---

## 13. Seasons

IMD seasons: winter (Jan–Feb), pre-monsoon (Mar–May), monsoon (Jun–Sep), post-monsoon (Oct–Dec).

| Season | Months in the dataset (all references) | Months with IMD rain |
| --- | --- | --- |
| Winter | Feb 2024, Jan–Feb 2025, Jan–Feb 2026 (5) | Feb 2024, Jan–Feb 2025 (3) |
| Pre-monsoon | Mar–May 2024, 2025, 2026 (9) | 2024, 2025 (6) |
| Monsoon | Jun–Sep 2024, 2025; Jun–Aug 2026 (11; monsoon 2026 incomplete) | 2024, 2025 (8) |
| Post-monsoon | Oct–Dec 2024, 2025 (6) | 2024, 2025 (6; Dec 2025 to the 30th) |

Seasonal results only where §11 floors are met; season-year cells (e.g. "monsoon 2025") are shown only if they meet
the floor on their own. Winter rain events will mostly be "insufficient sample".

---

## 14. Uncertainty and interpretation

- Intervals: 95% **block bootstrap** — resample whole valid dates (all points together, preserving spatial
  correlation) in 7-day blocks (temporal correlation), 1,000 resamples, fixed recorded seed (approved).
- Every result carries three separate statements: **measured result** (number, n, interval, reference, period,
  lead type) · **limitation** (reference nature, representativeness, exclusions) · **interpretation** (only what the
  numbers support).
- Not allowed: "confidence" for agreement; any probability not derived from a verified, calibrated analysis; "best
  model" in general (only per variable, lead, window, reference and period, and only with a significant paired
  difference); national conclusions; results without their reference named.
- **ERA5 caution:** ERA5 is produced by ECMWF with a closely related model. Comparisons against ERA5 may favour ECMWF,
  especially for temperature. ERA5-based model differences are reported as "agreement with ERA5 reanalysis" and
  **cannot support a ranking of models**. Model-difference statements require an independent reference (IMD for rain;
  METAR for temperature at matched stations).

---

## 15. The 2026 IMD gap

- IMD 2026 is not published (checked each batch run, latest 30 Sep 2026, 0-byte response). All 2026 IMD pairs are E.
- **Can proceed now:** R-IMD rain verification and events for **1 Feb 2024 – 30 Dec 2025** (the 31 Dec 2025 window
  ends in 2026); all ERA5-based analyses for all 31 months (secondary, labelled); temperature vs METAR.
- **Must wait:** any IMD-based rain statement for 2026 (e.g. monsoon 2026) until IMD publishes 2026 or IMERG is
  implemented (B6). ERA5 is not a substitute and 2026 ERA5 rain results are never merged with IMD results.
- When IMD 2026 appears: new immutable `history-imd-raw-2026`; the monthly releases are not modified — an additional,
  versioned reference supplement for 2026 is published (approved); existing immutable monthly releases are never
  modified.

---

## 16. Verification output schema (design only)

One row per result. Proposed fields:

| Field | Notes |
| --- | --- |
| result_id, methodology_version, experiment | experiment ∈ A-continuous, A-event, B-agreement, C1-core-issued, C2-historical-rule-replay, S-metar-occurrence |
| dataset, lead_type | historical_nominal \| prospective_exact |
| model \| agreement_k \| core_risk | exactly one is set, per experiment |
| variable, window | tmax / tmin / precip / precip_0830 / gust_max; ist_day \| imd_0830 |
| lead_day | nominal or exact, per lead_type |
| period_start, period_end, season | |
| scope, region, point_id | pooled \| region \| point; high_altitude flag |
| reference_source, reference_label | e.g. `imd_rf025`, "IMD gridded rain-gauge analysis" |
| sample_count, n_dates, n_points | |
| metric, value, ci_low, ci_high, ci_method | value empty when status ≠ ok |
| status | ok \| insufficient sample \| not verifiable |
| eligibility_rule | id of the rule in §6 (and the intersection set for comparisons) |
| limitations | list of limitation codes (ERA5-reanalysis, ERA5-ECMWF-lineage, point-vs-grid, high-altitude, METAR-integer, …) |
| event fields | event_definition, threshold, threshold_source (e.g. CORE M-RAIN Watch), hits, misses, false_alarms, correct_negatives, base_rate |
| provenance | archive releases (tag + manifest SHA-256), annotations applied, reference versions, code commit, config SHA-256, bootstrap seed |

---

## 17. Reproducibility

Every verification run will record, in an append-only record on `archive-index` (e.g. `history/verification/<run>/`):
the exact archive releases used (tags and manifest SHA-256); annotations applied (e.g. `2024-02-ecmwf-archive-start`);
reference versions (IMD raw release SHA-256; ERA5 retrieval dates as stored in the releases); code commit;
methodology version; the full configuration (filters, date range, points, thresholds and their CORE source, bootstrap
settings) and its SHA-256; and the result table's SHA-256. Inputs are the immutable releases only, so any result can
be recomputed later.

---

## 18. What this stage does not do

It does not change CORE, risk rules or thresholds; improve forecasts; train or run a neural network; generate
probabilities or confidence scores; create impact forecasts; build UI; compute any metric; or alter the historical
archive.

---

## 19. M4.4 entry criteria

M4.4 (implementation of scoring) may start only when all hold, and the owner has approved:

1. This methodology is approved (VM-1.0, 30 Sep 2026 — done).
2. Every metric has a named eligibility rule (§6) and reference (§2).
3. Missing-data treatment A–G is explicit (§6).
4. Sample floors are fixed (§11).
5. A, B and C are separate, with C1 (CORE-issued outputs, prospective) separate from C2 (historical rule replay).
6. Reproducibility record format is fixed (§17).
7. Scoring code will be tested offline on synthetic data with known answers (MAE/RMSE/bias and a contingency table
   computed by hand) before it touches the archive.

---

## 20. Decisions recorded (owner approval, 30 Sep 2026)

| # | Decision | Approved as |
| --- | --- | --- |
| 1 | Sample floors (§11) | publication/reporting floors; below the floor report "insufficient sample", no number |
| 2 | 2.5 mm rainy-day split (§7) | analytical classification only; never a BWI risk threshold |
| 3 | IMD-style regions (§12) | approved; islands always separate, never merged into mainland results |
| 4 | Uncertainty (§14) | 95% intervals, 7-day block bootstrap on whole valid dates, 1,000 iterations, fixed seed |
| 5 | Heat / cold (§10) | **restricted**: future extension requiring an additional reference input; NASA POWER is not added in M4.4; the verification dataset is not expanded at this stage |
| 6 | METAR occurrence (thunderstorm, fog) | station-level supplementary validation only; never extrapolated nationally |
| 7 | C2 | "historical rule replay", explicitly separate from CORE-issued risk verification (C1) |
| 8 | IMD 2026 | versioned reference supplement when available; immutable monthly releases never modified |

---

## 21. VM-1.1 amendments (owner decisions at the M4.4-A Gate 1 review, 30 Sep 2026)

| # | Decision | Recorded as |
| --- | --- | --- |
| 1 | Missing-data reason precedence | §6: primary reason D > C > B > A > E/F/G; both sides' categories always kept |
| 2 | Islands | §12: included in pooled results where eligible; separate region; "insufficient sample" below floor |
| 3 | Elevation | §12: diagnostic only (point elevation, ≥ 1,000 m flag, METAR elevation difference); no bands; no adjustment |
| 4 | Primary comparisons | below; everything else is secondary/exploratory |

**Primary comparisons (declared before any metric was computed).**

- *Temperature:* Tmax and Tmin vs **METAR** at each matched station that meets the station floor, all seasons pooled,
  nominal leads 1–6: each model, and each model pair on the pair's shared-data sample.
- *Rainfall:* 08:30–08:30 IST rain vs **IMD**, pooled over the eligible archive points, all seasons pooled, all
  days (no rainy-day stratum), nominal leads 1–6: each model, and each model pair on the pair's shared-data sample.
- *Secondary / exploratory:* every ERA5 comparison (A1, A4), seasonal slices, regional slices, elevation
  diagnostics (high-altitude slices), lead 7, the rainy-day (≥ 2.5 mm) stratum, and the three-model shared sample.
  Exploratory results are published with their numbers but are not findings (no multiplicity correction; Q3).
- *Wording:* a metric difference is reported only as the measured difference for the declared population,
  reference, metric and period, with its interval. It is never described as one model being "better" in general;
  no overall score and no global model ranking are produced.

**Bootstrap implementation (fixes details VM-1.0 §14 left open; approved settings unchanged; owner-approved at the
Gate 2 review, 30 Sep 2026 — a clarification, not a change: the Gate 2 results were computed exactly this way).**

- Blocks: fixed, non-overlapping 7-day calendar blocks beginning **1 Feb 2024** (the first date of the historical
  dataset). Block number = ⌊(valid date − 2024-02-01 in days) / 7⌋. A block holds every eligible pair of the cell
  whose valid date falls in it (all points together). Let the cell's K non-empty blocks be sorted by block number.
- Resampling: **1,000** resamples; each draws K block indices with replacement. For resample b, the counts c₍b,k₎
  of each block give n* = Σ c·n_k, Σe* = Σ c·Σe_k, Σ|e|* = Σ c·Σ|e|_k, Σe²* = Σ c·Σe²_k, and
  bias* = Σe*/n*, MAE* = Σ|e|*/n*, RMSE* = √(Σe²*/n*). The reported value is computed from all pairs (not the mean
  of the resamples).
- Interval: **percentile**, `numpy.percentile(values, [2.5, 97.5])` with NumPy's default `method="linear"`
  (Hyndman–Fan type 7).
- **Seed derivation (exact):**
  1. Cell id (UTF-8 string):
     `{experiment}|{comparison}|{model or "-"}|{variable}|L{lead}|{geo_slice_type}={geo_slice}|{season}|{stratum}`,
     e.g. `A3|single-model|gfs_global|precip_0830|L5|pooled=all-points|all|all`.
  2. Input string: `"20240201|" + cell id` (master seed 20240201, a pipe, the cell id), encoded as UTF-8.
  3. Hash: **SHA-256** of that byte string.
  4. Integer: the **first 8 bytes** of the digest read as an **unsigned big-endian** integer (0 … 2⁶⁴ − 1).
     Example: the cell above → digest prefix `5bec439491c535d8` → seed 6623743457334998488.
  5. RNG: `numpy.random.default_rng(seed)` — the **PCG64** bit generator seeded through NumPy's `SeedSequence`.
  6. Draws: one call `rng.integers(0, K, size=(1000, K))` (64-bit integers, 0 inclusive, K exclusive); row b is
     resample b, and the values index the cell's sorted non-empty blocks.
  7. Model pairs use one generator and one draw matrix for both models (paired). In the three-model shared-sample
     cells, each model's resampling uses the same cell seed, and therefore the same draws.
- Software: the Gate 2 run used Python 3.11.15, NumPy 2.4.4, pandas 3.0.2 and pyarrow 25.0.1. NumPy does not guarantee
  identical `Generator` output across versions, so exact reproduction uses NumPy 2.4.4. With another version, a
  re-run is checked against the recorded result SHA-256 values.
- Stored values (value, interval ends) are rounded to 6 decimals.
- Model pairs: the interval is for the difference (model A − model B) in bias, MAE and RMSE. An interval that
  excludes 0 is reported as such; nothing more is inferred.
- Metrics are computed only for cells whose census status is "meets floor"; no value is computed, stored or
  reported for any other cell.


**Source-representation limitation — M4.4-A reporting note (owner decision after the source probe, 30 Sep 2026).**
This is a reporting note on the source data, not a measured forecast error and not a methodology change. No data
correction, reprocessing, interpolation, smoothing, exclusion or resolution correction is applied.

| Affected results | Source representation change | Causal effect on the verification metric |
| --- | --- | --- |
| GFS rainfall, nominal leads 5–7 (A3, A4) | **Established:** the source's hourly series changes structure from lead 5 (evenly spread 3-hour totals and a 6-hour pattern, absent at leads 1–4), coinciding with the documented change to 3-hourly GFS output after forecast hour 120 | **Unresolved:** spreading a 3-hour total evenly does not reduce it; the mechanism of the lower lead-5–7 rain totals is not established |
| ECMWF temperature, nominal leads 6–7 (A1, A2) | **Established:** the source's hourly series changes from 3-hourly to 6-hourly node structure at lead 6, with a smaller diurnal range, coinciding with the documented 6-hourly ECMWF open-data steps after forecast hour 144 | **Unresolved:** the thinning simulation is directionally and approximately quantitatively consistent with the observed Tmax step, but does not establish causality; the small Tmin step is not explained |

- **Both hypotheses are UNRESOLVED.** The archive reproduces the source values exactly (the archive preserves the
  change; it does not introduce it).
- Evidence: source probe run 36684062500 and its report on archive-index
  (`history/verification/source-probe/`).
- Every M4.4-A result for these model–variable–lead combinations is reported with this note, **separately from the
  measured numbers**. The 30 primary cells placed on hold at the Gate 2 review stay held until the owner releases
  them.

**M4.4-B event implementation (details VM-1.0 §8/§11/§14 leave open; recorded before any event metric was computed).**

- **Scope:** weather-model rainfall-event detection only. It is not CORE risk verification, CORE alert accuracy or
  impact accuracy. Thresholds are CORE's M-RAIN amounts (35.6 / 64.5 / 115.6 mm) and nothing else. Each threshold
  is evaluated independently; an event is value ≥ threshold.
- **Precision:** the archive stores rain as float32, so the comparison is made in float32 (a stored 35.6 mm is an
  event at 35.6 mm).
- **Samples and floors:** event cells use the census-2 eligible samples of A3 (IMD, 08:30 window) and A4 (ERA5, IST
  day), with stratum "all". IMD and ERA5 are never combined.
  1. A cell whose census sample floor (§11: n, dates, points) is not met is suppressed: no count and no value is
     computed.
  2. Otherwise the four counts and the base rate are published.
  3. Each ratio then needs its own event floor: POD needs ≥ 20 reference events, FAR ≥ 20 forecast events, CSI and
     frequency bias both. Below the floor the ratio is "insufficient sample" and no value is computed.
  4. A zero denominator gives "no value", never zero.
- **Bootstrap:** same blocks, seed derivation and draws as §21 (the cell id includes the threshold). The counts
  a, b, c and d are summed per block, and each resample recomputes the ratios from its resampled counts. Model
  pairs share the draws, giving a paired interval for the difference.
- **Undefined resamples:** a resample with a zero denominator has no value for that ratio. It is left out of the
  percentile interval and counted. If more than 25 of the 1,000 resamples (2.5 %) have no value, the interval is
  reported as "no value".
- **Roles:** primary is IMD, pooled eligible points, all seasons, leads 1–6, each model and each model pair on
  shared data. ERA5 pooled, all seasons, leads 1–6 is secondary. Seasonal and regional slices, lead 7 and the
  three-model sample are exploratory, and elevation slices are diagnostic.
- **Source-resolution note:** GFS rain cells at leads 5–7 carry the §21 source-resolution note in `limitations`.
  No data are corrected or excluded.

**Reporting label — degenerate bootstrap intervals (owner decision at the M4.4-B review, 30 Sep 2026).** The
bootstrap method is unchanged, and no interval method (Wilson or other) replaces it.
- **When it applies:** a proportion (POD, FAR, CSI, observed frequency) at 0 or 1, or a frequency bias at 0, whose
  interval collapses to that value.
- **Label:** "Degenerate bootstrap interval: all bootstrap replicates produced the same boundary value; this does not
  imply statistical certainty."
- **Value:** unchanged. [0, 0] and [1, 1] are never read as certainty.
- **Model differences are not labelled.** A difference of 0 is not a boundary value. A zero-width difference
  interval arises when both models behave identically in the sample; it is reported as such.
- **Published M4.4-B results:** the label is added through an append-only annotation; the results are unchanged.

**M4.4-C model agreement (owner decisions at the M4.4-B review, 30 Sep 2026).**
- **Models:** ECMWF, GFS and ICON only.
- **k:** the number of the three models with a forecast ≥ τ, for each point, date, lead and CORE M-RAIN threshold,
  on the census three-model shared sample, pooled, all seasons.
- **References:** IMD (08:30 day) is primary; ERA5 (IST day) is secondary. They are kept separate.
- **Leads:** 1–4 are primary. Leads 5–6 are exploratory, carrying the note "GFS rainfall source representation
  changes at this lead range. The effect on the verification metric and on the model-agreement distribution is
  unresolved." Lead 7 is not analysed, because ICON is not defined there.
- **Per k-group:** n, reference events, observed frequency and a 95% interval (one draw matrix per lead and
  threshold, shared by all its groups).
- **Groups are not independent:** k = 0, 1, 2 and 3 partition the same sample, so they are mutually exclusive and
  their intervals are not independent samples.
- **Floors:** n ≥ 100 and ≥ 10 reference events per group; otherwise "insufficient sample" and no value is computed.
- **Exploratory breakdown:** which models make up k = 1 and k = 2.
- **Fixed wording:** "In the archived sample … when k of 3 models forecast ≥ τ, the reference reached ≥ τ on x of n
  days." The words probability, chance, confidence and likelihood are not used.

**Terminology note on CORE's forecast (owner direction, 30 Sep 2026; VM-1.0 text unchanged).** Where VM-1.0 (§2,
§10) says "best-match blends" or "best-match blend", it means Open-Meteo's best-match forecast. CORE uses the
Open-Meteo best-match forecast for its issued risk values; model agreement is a separate contextual field based on
the available model forecasts. CORE does not blend ECMWF, GFS and ICON into one forecast. The best-match model
composition over India is not documented in the available evidence (M4.4-D-SPEC-1.0, Q6).
