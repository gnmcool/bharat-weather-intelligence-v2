# Farmer screens in Gujarati

| Item | Value |
| --- | --- |
| Status | built on `feature/farmer-gujarati`; **not released**. Release needs (1) native-speaker sign-off of every string below and (2) owner approval to merge to `main` |
| Scope | the Farmer screen (steps 1–7). Other screens, Hindi and other languages: later |
| Code | `web/src/i18n/coreText.ts` (CORE text), `web/src/i18n/lang.ts` (switch, V2 labels), `web/src/modes/Farmer.tsx`, `web/test/coreText.test.ts` |
| CORE | unchanged (core-v1.0, 2840f8d). No new rules, thresholds or advice |

## 1. What CORE gives the farmer screen
CORE does not issue advisories. It returns six **system-derived, unvalidated indicators** (heat stress, cold stress,
heavy rain, dry spell, dry harvest window, disease-favourable weather) with its own disclaimer that they "are not
farming instructions", plus a separate block pointing to the official IMD × ICAR Agromet Advisory. The Gujarati
screen keeps exactly that separation: forecast table → system indicators (badged unvalidated) → official advisory.

## 2. How CORE's English becomes Gujarati
- CORE sends finished English sentences (for example `3 of 7 days ≥ 34 °C`), not structured values, and CORE is frozen.
- Each sentence is matched against CORE's fixed sentence patterns; the numbers are copied from the English into the
  Gujarati template. Nothing is computed, rounded or reformatted.
- **A sentence that does not match exactly is shown in English**, marked `lang="en"`, never guessed. A future CORE
  wording change therefore appears as English, not as wrong Gujarati.
- Fixed paragraphs (disclaimer, official-advisory text, crop notes) are translated only on an exact match.
- Not translated, by rule: official IMD weather warnings (shown as issued, with a Gujarati note saying so); state,
  district and place names (CORE's English names); weather-event cards in step 6 (from the V2 events API; shown in
  English under a Gujarati notice — a later milestone).
- Digits stay Western (0–9) in both languages; dates use Gujarati weekday and month names.

## 3. Tests (`npm test` in `web/`, run in CI)
The fixture `web/test/fixtures/core_farmer_text.json` is CORE's real output: frozen CORE `farmer.assess` run
read-only on synthetic weather for all 8 crops × all stages × 4 weather scenarios (100 distinct indicator sentences).
The tests check that every sentence is translated field by field, that numbers are carried over unchanged, that English
mode returns CORE text unchanged, that changed wording falls back to English, that the disclaimer keeps "not
instructions" and "official", and that every crop, season, stage and crop note in CORE's `crops.yaml` has Gujarati.

## 4. Before release: native-speaker review
I drafted these strings; I cannot vouch for agricultural Gujarati. The reviewer should be a native Gujarati speaker
who knows farm vocabulary (for example a KVK or AAU/JAU/NAU/SDAU extension contact). Strings I am least sure of:
`ડોડવા વિકાસ` (castor capsule development), `ચાપવા અવસ્થા` (cotton squaring), `સૂયા અવસ્થા` (groundnut pegging),
`માળ (સ્પાઇક)` (castor spike), `મોલો-મશી` (aphids), `ચરમી` (cumin blight), and the level words `નજર રાખો` /
`સાવધાન` / `ગંભીર`. Mark each row OK or give the correction.

### 4a. CORE text (63 strings)
| # | Kind | CORE English | Gujarati shown | OK? |
| --- | --- | --- | --- | --- |
| 1 | Level | No risk | જોખમ નથી |  |
| 2 | Level | Watch | નજર રાખો |  |
| 3 | Level | Alert | સાવધાન |  |
| 4 | Level | Severe | ગંભીર |  |
| 5 | Crop | Wheat | ઘઉં |  |
| 6 | Crop | Rice (paddy) | ડાંગર |  |
| 7 | Crop | Cotton | કપાસ |  |
| 8 | Crop | Groundnut | મગફળી |  |
| 9 | Crop | Castor | દિવેલા (એરંડા) |  |
| 10 | Crop | Pearl millet (bajra) | બાજરી |  |
| 11 | Crop | Cumin (jeera) | જીરું |  |
| 12 | Crop | Mustard | રાયડો |  |
| 13 | Season | Rabi | રવિ |  |
| 14 | Season | Kharif | ખરીફ |  |
| 15 | Season | Kharif / Summer | ખરીફ / ઉનાળુ |  |
| 16 | Stage | sowing | વાવણી |  |
| 17 | Stage | nursery | ધરુવાડિયું |  |
| 18 | Stage | transplanting | ફેરરોપણી |  |
| 19 | Stage | vegetative | વાનસ્પતિક વૃદ્ધિ |  |
| 20 | Stage | squaring | ચાપવા અવસ્થા |  |
| 21 | Stage | flowering | ફૂલ અવસ્થા |  |
| 22 | Stage | pegging | સૂયા અવસ્થા |  |
| 23 | Stage | pod fill | શીંગ ભરાવાની અવસ્થા |  |
| 24 | Stage | grain fill | દાણા ભરાવાની અવસ્થા |  |
| 25 | Stage | boll development | જીંડવા વિકાસ |  |
| 26 | Stage | capsule development | ડોડવા વિકાસ |  |
| 27 | Stage | seed development | બીજ વિકાસ |  |
| 28 | Stage | harvest | કાપણી |  |
| 29 | Indicator name | Heavy rain | ભારે વરસાદ |  |
| 30 | Indicator value (example) | max 40 mm/day | મહત્તમ 40 મિમી/દિવસ |  |
| 31 | Indicator rule (example) | IMD heavy rain ≥ 64.5 mm/day (Watch ≥ 35.6) | IMD મુજબ ભારે વરસાદ ≥ 64.5 મિમી/દિવસ (નજર રાખો ≥ 35.6) |  |
| 32 | Indicator name | Dry spell | વરસાદ વગરનો ગાળો |  |
| 33 | Indicator value (example) | 1 days | 1 દિવસ |  |
| 34 | Indicator rule (example) | Consecutive days < 2.5 mm | સળંગ દિવસો, દરેક દિવસે 2.5 મિમી કરતાં ઓછો વરસાદ |  |
| 35 | Indicator name | Disease-favourable weather | રોગને અનુકૂળ હવામાન |  |
| 36 | Indicator value (example) | 38 humid hours (RH ≥ 85%, 15–30 °C) | 38 ભેજવાળા કલાક (ભેજ ≥ 85%, 15–30 °C) |  |
| 37 | Indicator rule (example) | Leaf-wetness proxy | પાનની ભીનાશનો અંદાજ |  |
| 38 | Indicator name | Heat stress for this stage | આ અવસ્થામાં ગરમીનો તણાવ |  |
| 39 | Indicator value (example) | 3 of 7 days ≥ 32 °C | 7 માંથી 3 દિવસ ≥ 32 °C |  |
| 40 | Indicator rule (example) | Tmax ≥ 32 °C at flowering | ફૂલ અવસ્થા વખતે મહત્તમ તાપમાન ≥ 32 °C |  |
| 41 | Indicator name | Cold / frost stress | ઠંડી / હિમનો તણાવ |  |
| 42 | Indicator value (example) | 1 of 7 nights ≤ 3 °C | 7 માંથી 1 રાત ≤ 3 °C |  |
| 43 | Indicator rule (example) | Tmin ≤ 3 °C at flowering | ફૂલ અવસ્થા વખતે લઘુત્તમ તાપમાન ≤ 3 °C |  |
| 44 | Indicator name | Dry harvest window | કાપણી માટે કોરો ગાળો |  |
| 45 | Indicator value (example) | longest dry run 1 days | સૌથી લાંબો કોરો ગાળો 1 દિવસ |  |
| 46 | Indicator rule (example) | days < 1.0 mm & rain prob < 30% | દિવસો: વરસાદ < 1.0 મિમી અને વરસાદની શક્યતા < 30% |  |
| 47 | Indicator rule (example) | Leaf-wetness proxy; stage-sensitive for this crop | પાનની ભીનાશનો અંદાજ; આ પાક માટે આ અવસ્થા સંવેદનશીલ છે |  |
| 48 | disclaimer | SYSTEM-DERIVED WEATHER INDICATORS — computed automatically from forecast models using unvalidated thresholds. They are not farming instructions. Follow the official Agromet Advisory for decisions. | સિસ્ટમ-આધારિત હવામાન સૂચકાંકો — ફોરકાસ્ટ મોડેલોમાંથી, ચકાસણી ન થયેલી મર્યાદાઓ (થ્રેશોલ્ડ) વડે આપમેળે ગણાયેલા. આ ખેતી માટેની સૂચના નથી. નિર્ણય માટે સત્તાવાર કૃષિ-હવામાન સલાહ (Agromet Advisory) અનુસરો. |  |
| 49 | official title | Official Agromet Advisory (IMD × ICAR — Gramin Krishi Mausam Sewa) | સત્તાવાર કૃષિ-હવામાન સલાહ (IMD × ICAR — ગ્રામીણ કૃષિ મૌસમ સેવા) |  |
| 50 | official note | District Agromet Advisory Service bulletins are issued every Tuesday and Friday by IMD with State Agricultural Universities / KVKs. They are the authoritative source for farm operations. | જિલ્લા કૃષિ-હવામાન સલાહ સેવાના બુલેટિન IMD દ્વારા રાજ્ય કૃષિ યુનિવર્સિટીઓ / KVK સાથે મળીને દર મંગળવારે અને શુક્રવારે બહાર પડે છે. ખેતીના કામ માટે એ જ અધિકૃત સ્ત્રોત છે. |  |
| 51 | official integration | Not yet ingested automatically — requires IMD Agromet data access (see docs/ARCHITECTURE.md). | આ સલાહ હજી આપમેળે અહીં લાવવામાં આવતી નથી — તે માટે IMD કૃષિ-હવામાન ડેટાની પરવાનગી જરૂરી છે. |  |
| 52 | validation status | unvalidated | ચકાસણી બાકી |  |
| 53 | Advisory link | IMD — Agromet services | IMD — કૃષિ-હવામાન સેવાઓ |  |
| 54 | Advisory link | Meghdoot app (IMD/ICAR/IITM) — district advisories | મેઘદૂત એપ (IMD/ICAR/IITM) — જિલ્લાની સલાહ |  |
| 55 | Advisory link | Kisan Call Centre — 1800-180-1551 | કિસાન કોલ સેન્ટર — 1800-180-1551 |  |
| 56 | Crop note (wheat) | Terminal heat after anthesis shortens grain filling (Porter & Gawith 1999 review of wheat temperature responses). | ફૂલ આવ્યા પછીની ગરમી દાણા ભરાવાનો સમય ટૂંકો કરે છે (Porter & Gawith 1999, ઘઉં પર તાપમાનની અસરની સમીક્ષા). |  |
| 57 | Crop note (paddy) | Temperatures above ~35 °C at anthesis increase spikelet sterility (Jagadish et al. 2007). | ફૂલ અવસ્થાએ આશરે 35 °C થી વધુ તાપમાનથી દાણા ખાલી રહેવાનું (વંધ્યતા) વધે છે (Jagadish et al. 2007). |  |
| 58 | Crop note (cotton) | High heat at flowering raises square and boll shedding; validate local thresholds. | ફૂલ અવસ્થાએ વધુ ગરમીથી ચાપવા અને જીંડવા ખરવાનું વધે છે; સ્થાનિક મર્યાદાઓની ચકાસણી જરૂરી છે. |  |
| 59 | Crop note (groundnut) | Heat stress at flowering/pegging reduces pod set. | ફૂલ/સૂયા અવસ્થાએ ગરમીનો તણાવ શીંગ બેસવાનું ઘટાડે છે. |  |
| 60 | Crop note (castor) | Relatively heat tolerant; cold nights slow spike development. | ગરમી પ્રમાણમાં સહન કરે છે; ઠંડી રાતો માળ (સ્પાઇક) ના વિકાસને ધીમો પાડે છે. |  |
| 61 | Crop note (bajra) | Heat tolerant; very high temperature at flowering reduces seed set. | ગરમી સહન કરે છે; ફૂલ અવસ્થાએ ખૂબ ઊંચું તાપમાન દાણા બેસવાનું ઘટાડે છે. |  |
| 62 | Crop note (cumin) | Cloudy, humid spells at flowering favour blight (Alternaria) — a major Gujarat concern. | ફૂલ અવસ્થાએ વાદળછાયું, ભેજવાળું હવામાન ચરમી (Alternaria blight) ને અનુકૂળ છે — ગુજરાતમાં મોટી સમસ્યા. |  |
| 63 | Crop note (mustard) | Frost at flowering/pod fill damages pods; cloudy humid weather favours aphids. | ફૂલ/શીંગ ભરાવાની અવસ્થાએ હિમ શીંગોને નુકસાન કરે છે; વાદળછાયું ભેજવાળું હવામાન મોલો-મશી (એફિડ) ને અનુકૂળ છે. |  |

### 4b. Farmer-screen labels written by V2 (44 strings)
| # | Key | English | Gujarati shown | OK? |
| --- | --- | --- | --- | --- |
| 1 | lang_switch | Language | ભાષા |  |
| 2 | field_title | Your field — location, crop, growth stage | તમારું ખેતર — સ્થળ, પાક, પાકની અવસ્થા |  |
| 3 | loc_state | 1 · Location — state | 1 · સ્થળ — રાજ્ય |  |
| 4 | loc_district | 1 · Location — district | 1 · સ્થળ — જિલ્લો |  |
| 5 | sel_state | Select state | રાજ્ય પસંદ કરો |  |
| 6 | sel_district | Select district | જિલ્લો પસંદ કરો |  |
| 7 | crop | 2 · Crop | 2 · પાક |  |
| 8 | sel_crop | Select crop | પાક પસંદ કરો |  |
| 9 | stage | 3 · Growth stage | 3 · પાકની અવસ્થા |  |
| 10 | sel_stage | Select stage | અવસ્થા પસંદ કરો |  |
| 11 | field_location | Field location: | ખેતરનું સ્થળ: |  |
| 12 | field_help | For a village, use the location search at the top; the forecast is a point forecast at model-grid resolution. | ગામ માટે ઉપરના સ્થળ-શોધનો ઉપયોગ કરો; આગાહી મોડેલ-ગ્રીડના એક બિંદુ માટેની છે. |  |
| 13 | official_later | The official agricultural advisory is shown separately in step 7. | સત્તાવાર કૃષિ સલાહ પગલું 7 માં અલગથી બતાવી છે. |  |
| 14 | choose_prompt | Choose a crop and growth stage to see weather indicators for your field. | તમારા ખેતર માટે હવામાન સૂચકાંકો જોવા પાક અને પાકની અવસ્થા પસંદ કરો. |  |
| 15 | weather_title | 4 · Weather — next days at your field | 4 · હવામાન — તમારા ખેતર પર આવતા દિવસો |  |
| 16 | th_day | Day | દિવસ |  |
| 17 | th_temp | Max / min °C | મહત્તમ / લઘુત્તમ °C |  |
| 18 | th_rain | Rain mm | વરસાદ મિમી |  |
| 19 | th_chance | Chance | શક્યતા |  |
| 20 | th_spray | Spray-suitable hours* | છંટકાવ માટે યોગ્ય કલાક* |  |
| 21 | th_disease | Disease-favourable hours* | રોગને અનુકૂળ કલાક* |  |
| 22 | weather_note | Forecast values from CORE. *Spray and disease hours are system-derived, unvalidated indicators from CORE's thresholds. | આગાહીના આંકડા CORE માંથી. *છંટકાવ અને રોગના કલાક CORE ની મર્યાદાઓ પરથી ગણાયેલા સિસ્ટમ-આધારિત, ચકાસણી ન થયેલા સૂચકાંકો છે. |  |
| 23 | ind_title | 5 · System indicators | 5 · સિસ્ટમ સૂચકાંકો |  |
| 24 | badge_system | System-derived | સિસ્ટમ-આધારિત |  |
| 25 | badge_unvalidated | Unvalidated | ચકાસણી થયેલ નથી |  |
| 26 | core_status | CORE status: | CORE સ્થિતિ: |  |
| 27 | rule | Rule: | નિયમ: |  |
| 28 | rule_suffix | system-derived, unvalidated | સિસ્ટમ-આધારિત, ચકાસણી થયેલ નથી |  |
| 29 | rel_title | 6 · Potential crop relevance — weather events | 6 · પાક પર સંભવિત અસર — હવામાનની ઘટનાઓ |  |
| 30 | rel_head | Potential crop relevance | પાક પર સંભવિત અસર |  |
| 31 | rel_none | No significant weather event detected for this field in CORE's 7-day assessment. | CORE ના 7 દિવસના મૂલ્યાંકનમાં આ ખેતર માટે કોઈ મહત્ત્વની હવામાન ઘટના મળી નથી. |  |
| 32 | rel_uses | Existing CORE indicators for Cotton (Flowering) that use daily rainfall: | કપાસ (ફૂલ અવસ્થા) માટેના CORE ના હાલના સૂચકાંકો, જે દૈનિક વરસાદ પર આધારિત છે: |  |
| 33 | rel_no_ind | No existing CORE crop indicator for 2 at this stage uses this signal. V2 does not add agronomic rules. | આ અવસ્થાએ 2 માટે CORE નો કોઈ સૂચકાંક આ સંકેતનો ઉપયોગ કરતો નથી. V2 ખેતીના નવા નિયમો ઉમેરતું નથી. |  |
| 34 | rel_official | Official advisory: 2 — step 7 below. | સત્તાવાર સલાહ: 2 — નીચે પગલું 7. |  |
| 35 | events_english | — | ઘટનાની વિગતો હાલ અંગ્રેજીમાં છે. |  |
| 36 | off_head | 7 · Official agricultural advisory | 7 · સત્તાવાર કૃષિ સલાહ |  |
| 37 | off_sep | Steps 5 and 6 are system output, not an official agricultural advisory. For farm decisions, follow the official advisory. | પગલાં 5 અને 6 સિસ્ટમનું પરિણામ છે, સત્તાવાર કૃષિ સલાહ નથી. ખેતીના નિર્ણયો માટે સત્તાવાર સલાહ અનુસરો. |  |
| 38 | alerts_title | Official weather alerts for this area | આ વિસ્તાર માટે સત્તાવાર હવામાન ચેતવણીઓ |  |
| 39 | alerts_note | — | સત્તાવાર ચેતવણીઓ જારી થયેલી ભાષામાં જ બતાવી છે; તેનો અનુવાદ કરવામાં આવતો નથી. |  |
| 40 | english_kept | — | અંગ્રેજીમાં (અનુવાદ ઉપલબ્ધ નથી) |  |
| 41 | signal | daily maximum temperature | દૈનિક મહત્તમ તાપમાન |  |
| 42 | signal | daily minimum temperature | દૈનિક લઘુત્તમ તાપમાન |  |
| 43 | signal | daily rainfall | દૈનિક વરસાદ |  |
| 44 | signal | consecutive dry days | સળંગ કોરા દિવસો |  |
