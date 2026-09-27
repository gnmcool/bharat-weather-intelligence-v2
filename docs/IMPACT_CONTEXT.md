# Impact context (M3) — method

V2's decision-support chain is **FACT → ASSESSMENT → EVIDENCE → POTENTIAL RELEVANCE**.
Decision authority stays with the user and the appropriate authority.

## Rule

- A potential-relevance line is shown **only** next to a CORE risk at Watch level or above
  (an M2 event). No event → no context.
- The text comes from a fixed catalogue (`api-v2/app/catalogue.py` `CONTEXT`), one line per
  hazard per audience (citizen, farmer); government uses "Districts or locations with
  system-assessed … risk".
- Every line is labelled **"Potential relevance — general context, not an impact forecast"**.
- Wording is conditional ("may", "relevant to"). No instruction verbs; an automated test fails
  on words such as evacuate, spray, harvest, cancel, avoid, stay, must, should, advise,
  recommend (`api-v2/tests/test_m3.py`).
- No claim that damage, casualties, crop loss, flooding or infrastructure impact has occurred
  or will occur. V2 has no observation or impact dataset.
- Cyclone: none (official-only; the official alert text is the only source).

## Catalogue

| Hazard | Citizen | Farmer |
|---|---|---|
| Heat | High temperatures may affect people working or travelling outdoors, especially in the afternoon. | Heat during this period may be relevant to field work and to crops at heat-sensitive stages. |
| Cold | Low temperatures may affect people outdoors, especially at night and in the early morning. | Low night temperatures during this period may be relevant to crops at cold-sensitive stages. |
| Heavy rain | Heavy rain may affect travel and low-lying areas. | Rain during this period may affect field operations. |
| Strong wind | Strong gusts may affect travel, trees and loose structures. | Strong wind during this period may affect field operations and tall standing crops. |
| Thunderstorm potential | If thunderstorms develop, they may bring sudden heavy rain, gusts and lightning. | If thunderstorms develop, they may interrupt field operations. |
| Lightning potential | Lightning potential is most relevant to people in open areas. | Lightning potential is most relevant to people working in open fields. |
| Flood-related risk | Accumulated rain may affect low-lying and poorly drained areas. | Accumulated rain may be relevant to waterlogging in low-lying fields. |
| Fog | Low visibility may affect road, rail and air travel. | Low visibility may affect early-morning field work and transport. |
| Fire weather | Hot, dry and windy conditions may be relevant to the spread of fires. | Hot, dry and windy conditions may be relevant to fire in dry fields and crop residue. |
| Dry spell | A rainfall deficit may be relevant to local water availability. | A rainfall deficit during this period may be relevant to soil moisture and irrigation. |

These are general statements of relevance, not validated impact relationships. Validated
impact rules (e.g. IMD impact-based forecasting matrices) are a later milestone.

## Farmer crop link

Event → existing CORE crop indicator that uses the same weather variable (heat → heat stress,
cold → cold stress, rain/flood → heavy rain and harvest window, dry spell → dry spell). Display
link only; no agronomic threshold is added. Indicators stay labelled **System-derived ·
Unvalidated**; the official Agromet advisory is a separate block.
