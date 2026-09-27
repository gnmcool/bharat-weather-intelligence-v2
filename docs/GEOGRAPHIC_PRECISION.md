# Geographic precision policy

The gridded forecast (NOAA GFS processed by Earth2Studio) is 0.25°, about 27 km × 25 km, or
roughly 700 km² per cell over central India. An average Indian taluka / tehsil is around
550 km². Statistics finer than the data are false precision.

## Levels

| Level | What V2 may show | Required label |
|---|---|---|
| India, State | Area statistics and counts (e.g. districts at each risk level) | Source, run time, method |
| **District (finest area unit)** | Area statistics from grid cells inside the district polygon: mean, max, total | "District statistic from N grid cells (0.25°)" |
| Taluka / tehsil, village, GPS point | **Point forecast only**: the forecast at that location | "Point forecast — model grid value at ~27 km resolution, not a local measurement" |

## Rules

- Never present a taluka or village value as an aggregated area statistic, a ranking or a
  choropleth, unless a validated sub-district dataset is added later with your approval.
- District statistics use the grid cells whose **centres** fall inside the district polygon
  (CORE's method, `/region/india`). Measured on CORE's grid (27 Sept 2026): median 5 cells per
  district; **144 of 724 districts have fewer than 3 cells** and **18 have none**.
  - Always show the cell count. Under 3 cells, add "limited spatial detail".
  - With 0 cells, show no area statistic. Show the point forecast at the district centre instead,
    labelled as a point forecast.
- Point values come from the grid (bilinear) or from Open-Meteo point models. Name which one.
- District boundaries are pilot-grade (724 districts, inherited from CORE). They are to be
  replaced with Survey of India / LGD boundaries before any official use.
