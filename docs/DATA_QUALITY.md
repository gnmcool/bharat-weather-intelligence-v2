# Data-quality notices (M3)

One reusable component (`web/src/components/DataQualityNotice.tsx`), fed by `api-v2`. Every
notice is triggered by a CORE field or by V2's own data coverage — never by a new weather
threshold. Wording is factual and short (`api-v2/app/catalogue.py` `NOTICES`).

| id | Trigger (data) | Where shown |
|---|---|---|
| `representative_point` | Always, with district counts | Government counts (as the bold statement), map risk layer, state focus |
| `incomplete_hazards` | Always, with district counts | Government counts |
| `elevation_districts` | ≥ 1 counted district has CORE `terrain = "hills"`; lists hill districts per hazard | Government counts |
| `elevation` | CORE `current.terrain = "hills"` at the location, or district `terrain = "hills"` | Home, Risks, evidence drawer, district card, map card |
| `grid_vs_point` | An Earth2Studio value is shown in the evidence | Evidence drawer |
| `core_inconsistency` | A CORE risk at level 0 whose basis says "0 of n models … show no event" (see CORE-2) | Home, Risks, evidence for that risk |
| `incomplete_coverage` | A CORE state table failed after one retry | Government counts, directly under the tiles |

Rules: notices never change a level, count or value; they explain it. Each links to a CORE
issue (`CORE_ISSUES.md`) where a CORE change may be needed.
