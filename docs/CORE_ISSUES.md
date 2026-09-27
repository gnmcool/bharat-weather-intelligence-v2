# CORE issues found by V2

CORE is frozen (tag `core-v1.0`, commit `2840f8d`). V2 does **not** fix CORE: it shows CORE's
output unchanged and, where relevant, a data-quality note. Each issue below needs the owner's
explicit approval before any CORE change.

Status values: **Open** (recorded, not investigated) · **Investigating** · **Closed**.

---

## CORE-1 — High-elevation representative points distort district cold (and heat) levels

| | |
|---|---|
| Status | Open |
| Affected endpoint / rule | `/api/v1/region/state/{slug}` district levels (`levels.cold`, `levels.heat`); rules M-COLD / M-HEAT (IMD departure criteria) |
| Evidence | On 27 Sep 2026 all 12 districts with system-assessed cold risk were CORE "hills" terrain, 8 of them *Severe cold* in late September. Uttarkashi's representative point is at 5,264 m: 7-day min −15.5 °C vs NASA POWER normal −0.5 °C (departure ≈ −15 °C). The point forecast is elevation-adjusted; the normal is a ~50 km reanalysis cell, whose mean elevation is far lower |
| Example location | Uttarkashi (IN-05-056, 31.0033, 78.5841); also Pithoragarh, Kinnaur, Kullu, Kishtwar, Kargil, Tawang, North Sikkim |
| Potential consequence | District cold counts are inflated and describe a mountain-top point, not where people live. Same mechanism can raise heat departures at lower hill points (Doda, heat Severe) |
| Proposed investigation | (1) Compare the elevation of each representative point with the district's population-weighted or median elevation; (2) compute normals at the same elevation as the forecast (lapse-rate adjustment or a normal from the same model at the same point); (3) consider choosing representative points by population rather than interior geometry |
| V2 handling | Counts unchanged; "Mountain districts in this count" note with hill-terrain numbers per hazard; hill-terrain note on each hill district card; wording "districts with system-assessed cold risk" |

## CORE-2 — Heat level contradicts CORE's own Watch criterion and model check

| | |
|---|---|
| Status | Open |
| Affected endpoint / rule | `/api/v1/dashboard` `risks[id=heat]`; rule M-HEAT ("Watch (system): departure ≥ 3 °C") |
| Evidence | Chennai, 27 Sep 2026: level 0 "No risk"; explanation "the week's highest is 36.3 °C, +4.8 °C vs normal"; confidence basis "0 of 3 models (ECMWF, GFS, ICON) show no event in 7 days" (i.e. all three models show an event); per-model Tmax 37.0–38.0 °C vs normal 31.5 °C |
| Second observation | Chennai, CORE run of 18:36 UTC 27 Sep: level "No risk", explanation "+4.4 °C vs normal", basis now "2 of 3 models … show no event". The model-check contradiction has gone, but the departure (≥ 3 °C) still meets the written Watch criterion while the level is No risk |
| Example location | Chennai (13.0827, 80.2707) |
| Potential consequence | A heat Watch may be missing at coastal locations; the model-check field and the level disagree, so evidence looks contradictory |
| Proposed investigation | Read the M-HEAT implementation for coastal Watch logic (is the Watch gated on the coastal Tmax ≥ 37 °C threshold as well?); check the basis wording for level 0; test Chennai and other coastal points against the written criterion. **No explanation is assumed until investigated** |
| V2 handling | CORE level shown unchanged; no heat event created; "CORE output inconsistency" note on Home, Risks and the heat evidence, triggered only when a risk is at No risk while CORE's basis says 0 of n models show no event. V2 does **not** test the departure against the Watch criterion itself — that would re-implement CORE's rule — so the second form of this issue is visible in the evidence (departure and rule side by side) but not flagged |

## CORE-3 — Earth2Studio GFS grid values vs point forecasts in mountain terrain

| | |
|---|---|
| Status | Open (expected behaviour; documented so it is not mistaken for an error) |
| Affected endpoint / rule | `/api/v1/grid/point`, `/api/v1/grid/field` (0.25° GFS via Earth2Studio) |
| Evidence | Uttarkashi, 27 Sep 2026: Earth2Studio t2m minimum −1.8 °C over the cold window vs point models −13.6 °C (ECMWF), −13.5 °C (GFS), −5.5 °C (ICON) |
| Example location | Uttarkashi |
| Potential consequence | Users may read the grid value as a point value, or read the difference as model disagreement |
| Proposed investigation | None required in CORE; if needed later, show grid-cell elevation alongside grid values |
| V2 handling | Both values shown; Earth2Studio labelled "same model as GFS — not counted"; "Grid value, not a point value" note in the evidence whenever an Earth2Studio value is shown |

## CORE-4 — Behavioural advice inside a system risk explanation

| | |
|---|---|
| Status | Open |
| Affected endpoint / rule | `/api/v1/dashboard` `risks[id=lightning].explanation` |
| Evidence | Text: "When thunder roars, go indoors. Avoid open fields, trees, water bodies. Use Damini app (IITM) for live strikes." attached to a model-derived Watch |
| Example location | Shimla, Chennai, Guwahati (27 Sep 2026) |
| Potential consequence | Safety instructions appear inside a system assessment, not attributed to an official source; conflicts with V2's "no recommendations" principle |
| Proposed investigation | Decide whether CORE should (a) move the advice to an attributed official-guidance link (NDMA/IMD), or (b) keep it clearly labelled as general guidance |
| V2 handling | Shown only inside the evidence drawer, labelled "CORE explanation"; V2 generates no instructions |

## CORE-5 — Official alerts matched to a location at state level

| | |
|---|---|
| Status | Open |
| Affected endpoint / rule | `/api/v1/dashboard` `warnings[]` (`match: "state"`) |
| Evidence | Guwahati (Kamrup Metropolitan), 27 Sep 2026: two CWC flood alerts for the Brahmaputra at Dibrugarh (district IN-18-310) are returned for Guwahati with `match: "state"` |
| Example location | Guwahati; Chennai (a Karur/Tiruchirappalli thunderstorm alert) |
| Potential consequence | A citizen may read another district's official alert as applying to their location |
| Proposed investigation | Whether CORE should return state-level matches separately from district/polygon matches |
| V2 handling | Issuer wording and area shown verbatim; evidence states the CORE match rule. A separate "elsewhere in the state" grouping would be a V2 display change — proposed for M4, not done |

## CORE-6 — Transient failures of `/region/state` under parallel load

| | |
|---|---|
| Status | Open (minor) |
| Affected endpoint / rule | `/api/v1/region/state/{slug}` |
| Evidence | During cold rebuilds of the India counts from a development machine, 1–2 of 36 parallel state requests occasionally failed with a connection error (27 Sep 2026); none failed from the deployed service |
| Potential consequence | Incomplete India counts |
| V2 handling | One retry on transport errors; if a state still fails, an "incomplete counts" note names it and the result is cached for 60 s only |
