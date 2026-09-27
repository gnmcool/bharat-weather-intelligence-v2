# Forecast verification strategy

**Status:** archive running from M0 (27 Sept 2026). Metrics are planned for M4.

## Pipeline

```
archive (daily, M0) ──► reference data (M4) ──► error per forecast ──► metrics by segment ──► report
```

## 1. Archive (running)

`archive/snapshot.py` runs daily at 11:00 IST (`archive.yml`) and stores in this repo's monthly
releases (`archive-YYYY-MM`):

| File | Content | Size |
|---|---|---|
| `e2s_gfs_daily_<cycle>.nc` | CORE's Earth2Studio GFS forecast as daily values per IST day and lead day: rain (mm), Tmax, Tmin (°C), max gust (km/h); 0.25°, India | ~2 MB |
| `points_<date>.json` | Open-Meteo daily forecasts from ECMWF IFS, GFS and ICON **separately**, 10 days, at 36 fixed points (`points.json`: one district per State/UT) | ~65 KB |

Each file records source, model, issue time, source URL, retrieval time and method. The point list
is fixed: entries are never changed, only appended, so records stay comparable over time.

## 2. Reference data (M4). Always name the reference

| Variable | Reference | Nature | Access |
|---|---|---|---|
| Rainfall | NASA GPM **IMERG** (Late/Final, 0.1°) | Satellite estimate | Free NASA Earthdata account (token as a repository secret) |
| Temperature, wind, rain | **ERA5** reanalysis (via Open-Meteo archive API) | Model reanalysis, ~5-day lag | Free |
| Stations | IMD AWS / synoptic | Observations | Not openly available; to be added only with IMD access |

Every metric is labelled with its reference, e.g. "verified against ERA5 reanalysis, not
stations".

## 3. Metrics

- Continuous: **MAE, RMSE, bias** for Tmax, Tmin, rain and gust.
- Rain events: hit rate, false-alarm ratio and frequency bias at IMD thresholds (heavy
  64.5 mm, very heavy 115.6 mm).
- Segments: variable × lead day × model (ECMWF, GFS, ICON, Earth2Studio GFS) × point/region ×
  season.

## 4. Minimum data before any claim

| Claim | Minimum |
|---|---|
| Preliminary error figures (clearly marked preliminary) | 30 days |
| Seasonal statements | One full season (~90 days) of that season |
| "Model X performs better" | Statistically meaningful difference over at least one season, per variable and lead time |
| Calibrated "confidence" from model agreement | Verified hit rates per agreement level over at least one season |

## Known limitations

A grid-cell forecast compared with a point reference has representativeness error. IMERG
underestimates some orographic and coastal rain. ERA5 is a model, not the truth. These caveats are
shown alongside the metrics.
