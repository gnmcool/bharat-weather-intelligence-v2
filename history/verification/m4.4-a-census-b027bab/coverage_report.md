# M4.4-A census (Gate 1, counts only) — VM-1.0

Months 2024-02 … 2026-08 (31 releases); code b027bab; archive-index 5963220. **No metric was computed.**

## Totals

| Experiment | Pairs | Eligible | Excluded |
| --- | --- | --- | --- |
| A1 Tmax/Tmin vs ERA5 reanalysis (agreement with reanalysis, not observation) | 1,425,816 | 1,352,952 | 72,864 |
| A2 Tmax/Tmin vs METAR station observation (matched stations only, per station) | 1,425,816 | 104,794 | 1,321,022 |
| A3 Rain (08:30-08:30 IST) vs IMD gridded rain-gauge analysis | 712,908 | 473,892 | 239,016 |
| A4 Rain (IST day) vs ERA5 reanalysis (secondary) | 712,908 | 676,260 | 36,648 |

## Exclusions by category (all leads)

| Experiment | Model | Variable | A | B | C | D | E | F | G |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | ecmwf_ifs025 | tmax | 0 | 1,764 | 0 | 0 | 0 | 0 | 0 |
| A1 | ecmwf_ifs025 | tmin | 0 | 1,764 | 0 | 0 | 0 | 0 | 0 |
| A1 | icon_global | tmax | 33,948 | 0 | 720 | 0 | 0 | 0 | 0 |
| A1 | icon_global | tmin | 33,948 | 0 | 720 | 0 | 0 | 0 | 0 |
| A2 | ecmwf_ifs025 | tmax | 0 | 1,764 | 0 | 0 | 5,191 | 15,859 | 196,560 |
| A2 | ecmwf_ifs025 | tmin | 0 | 1,764 | 0 | 0 | 5,191 | 15,859 | 196,560 |
| A2 | gfs_global | tmax | 0 | 0 | 0 | 0 | 5,285 | 15,911 | 198,030 |
| A2 | gfs_global | tmin | 0 | 0 | 0 | 0 | 5,285 | 15,911 | 198,030 |
| A2 | icon_global | tmax | 33,948 | 0 | 720 | 0 | 4,510 | 13,593 | 169,140 |
| A2 | icon_global | tmin | 33,948 | 0 | 720 | 0 | 4,510 | 13,593 | 169,140 |
| A3 | ecmwf_ifs025 | precip_0830 | 0 | 1,512 | 432 | 0 | 61,056 | 0 | 9,702 |
| A3 | gfs_global | precip_0830 | 0 | 0 | 0 | 0 | 61,488 | 0 | 9,786 |
| A3 | icon_global | precip_0830 | 33,948 | 0 | 540 | 0 | 52,164 | 0 | 8,388 |
| A4 | ecmwf_ifs025 | precip | 0 | 1,764 | 504 | 0 | 0 | 0 | 0 |
| A4 | icon_global | precip | 33,948 | 0 | 432 | 0 | 0 | 0 | 0 |

## Cells meeting the publication floor (single-model)

| Experiment | Slice type | Cells | Meets floor | Insufficient sample |
| --- | --- | --- | --- | --- |
| A1 | high_altitude | 420 | 400 | 20 |
| A1 | pooled | 210 | 200 | 10 |
| A1 | region | 1050 | 800 | 250 |
| A2 | station | 1260 | 600 | 660 |
| A3 | high_altitude | 420 | 320 | 100 |
| A3 | pooled | 210 | 180 | 30 |
| A3 | region | 1050 | 580 | 470 |
| A4 | high_altitude | 420 | 340 | 80 |
| A4 | pooled | 210 | 200 | 10 |
| A4 | region | 1050 | 640 | 410 |
