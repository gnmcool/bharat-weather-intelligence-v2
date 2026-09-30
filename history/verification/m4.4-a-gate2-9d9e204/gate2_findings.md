# M4.4-A Gate 2 — data issues found during review (for the owner's decision)

Written after the metric run (code `9d9e204`, census `m4.4-a-census-2@55030a4`, archive-index `bb6714a`). This note
changes no result: `metric_results.csv` is published exactly as computed. Nothing below was checked against any
external source. Gate 2 permitted no external data calls, so every cause given here is a hypothesis.

## 1. GFS rain: step at nominal lead ≥ 5 (both rain windows)

The mean GFS rain forecast over IMD-eligible pairs is 4.2–4.5 mm/day at leads 1–4. At leads 5, 6 and 7 it is
2.0, 1.5 and 1.5 mm/day, while the reference stays at 4.7 mm/day. The same step (about 0.4–0.5 × the lead 1–4 level)
appears in **every one of the 23 IMD months**, and against ERA5 (A4 bias −0.3 at lead 4, then −2.6 / −3.0 / −3.0).
The dry-forecast fraction rises from 0.51 to 0.55–0.56. ECMWF and ICON show no such step. The step is systematic and
unrelated to season, so it is a property of the archived values. Whether it comes from the source's output or from
how it was aggregated cannot be established offline.

Consequence: at leads 5–6, the GFS rain MAE is **lower** than at leads 1–4 (4.35–4.37 vs 4.48–5.12 mm), because
under-forecasting on the many dry days reduces absolute error. The primary paired MAE differences at leads 5–6
(ECMWF − GFS +0.78 / +0.82 mm; GFS − ICON −0.74 / −0.84 mm; intervals exclude 0) are therefore driven by this step,
and **should not be read as a difference in forecast quality**.

Hypothesis: GFS 0.25° output changes from hourly to 3-hourly after forecast hour 120. The way the 3-hourly
accumulations appear in the hourly series that was summed may undercount the total.

Affected cells: 6 primary (A3 GFS leads 5–6, single-model and the two GFS pairs) and 1,124 exploratory (GFS
rain, leads 5–7, A3/A4).

## 2. ECMWF temperature: step at nominal lead ≥ 6

The mean ECMWF Tmax at METAR stations falls by 0.3–1.4 °C from lead 5 to lead 6 in **every one of the 31 months**.
The mean error over all matched-station pairs moves from −0.94 to −1.68 °C (a diagnostic, not a published cell;
A2 is per station only). The pooled A1 (ERA5) bias moves from −0.26 to −0.82 °C. Tmin shows a smaller step
(about −0.2 °C). GFS and ICON show no step.

Hypothesis: ECMWF open data change from 3-hourly to 6-hourly steps after forecast hour 144. A daily maximum taken
from coarser steps misses the afternoon peak.

Affected cells: 24 primary (A2 ECMWF lead 6 at 4 stations × Tmax/Tmin, single-model and the two ECMWF pairs) and
576 exploratory (ECMWF temperature, leads 6–7, A1/A2).

## 3. Other observations (no action proposed)

- **Large station-specific offsets:** GFS vs METAR at VIDP (Tmin bias +4.6 to +4.8 °C, Tmax +3.2 to +3.6 °C) and
  at VICG (Tmax +3.1 to +3.6 °C). These are station-level measured offsets. Point-vs-grid and station siting are
  possible contributors. They are not evidence about GFS elsewhere.
- **ERA5–ECMWF lineage** is visible in the data: the ECMWF rain bias against ERA5 is about 0.0 mm at every lead,
  while GFS and ICON are about −0.3 to −0.8 mm at leads 1–4. This is exploratory, and is why ERA5 comparisons
  cannot support model differences (VM §14).
- **VICG** meets the station floor with 135–143 days, so its intervals are wide.
- **Rain RMSE is about 3 × MAE** (12.8–15.4 vs 4.4–5.2 mm), so it is dominated by heavy-rain days, as VM §7
  anticipates.

## 4. Decision needed before M4.4-B (not taken here)

For the lead cells affected by steps 1 and 2, one of the following:

- (a) keep them published with a data-quality flag;
- (b) withhold them pending a source check (this needs an approved probe of the raw hourly source output);
- (c) declare those leads not comparable for those model–variable combinations in VM-1.2.

No result, release or methodology text has been changed on account of these findings.
