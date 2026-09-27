# Model agreement methodology

V2 uses the term **Model Agreement**, not "confidence". Agreement between models is not a
calibrated probability. The API field inherited from CORE is still named `confidence`, and it is
kept unchanged for CORE compatibility. V2 only changes the label and the explanation.

## Independent models

| Counted | Model | Why |
|---|---|---|
| Yes | ECMWF IFS 0.25° | Independent global model |
| Yes | NOAA GFS | Independent global model |
| Yes | DWD ICON | Independent global model |
| **No** | Earth2Studio GFS | Same GFS forecast, processed locally: identical source |
| **No** | FourCastNet (Earth2Studio AI) | Initialised from GFS; shown only as an experimental comparison |

## How agreement is expressed

- **Agreement:** "k of 3 models" reach the same risk level (within one level) within ±1 day of
  the peak. This is CORE's existing rule, reused unchanged.
- **Forecast range:** minimum–maximum of the three models' values, e.g. "38–47 mm (ECMWF, GFS,
  ICON)". It is described as the spread of three models, never as a likelihood.
- **Lead time:** agreement beyond day 5 is shown with the lead time, and CORE caps its level at
  "medium" there.
- If fewer than 3 models are available, V2 says so ("2 of 2 available models"), and does not
  imply full agreement.

## Wording

| Use | Do not use |
|---|---|
| "Model agreement: 3 of 3" | "High confidence", "90% certain" |
| "Forecast range 38–47 mm across 3 models" | "Expected 38–47 mm" (without the models) |
| "Models disagree: ECMWF 31 °C, GFS 35 °C" | Hiding disagreement by showing one number |

A calibrated "confidence" may only be introduced after verification (see `VERIFICATION.md`)
shows how often each agreement level was right, over a documented period.
