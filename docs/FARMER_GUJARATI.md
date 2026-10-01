# Farmer screens in Gujarati

Hindi uses the same method and code; see `docs/FARMER_HINDI.md` for its review sheet.

| Item | Value |
| --- | --- |
| Status | **released 1 Oct 2026** on the owner's sign-off. The owner (CA Gaurav N. Makwana) reviewed the full app with the Gujarati screens on a private preview of this code and approved publication. No row-level marks were recorded, so the rows below carry no individual OK; the "least sure" terms in §4 remain the first to verify with farmers or a KVK |
| Scope | the whole Farmer home: current weather, "What should you know?" (with event cards), and the field workflow (steps 1–7). The switch sits at the top of the Farmer home. Citizen and Government screens, the evidence drawer, Hindi and other languages: later |
| Code | `web/src/i18n/coreText.ts` (CORE and V2 event text; Gujarati and Hindi columns over the same English patterns), `web/src/i18n/lang.ts` (switch, V2 labels), `web/src/modes/Farmer.tsx`, `web/src/pages/blocks.tsx` and `Home.tsx` (farmer home), `web/src/components/EventCard.tsx`, `web/test/coreText.test.ts` |
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
- Weather-event cards (farmer home and step 6) are rendered the same way: CORE's event headlines (from
  `risk.py`, e.g. `Rather heavy rain today (58 mm)`) are matched against CORE's patterns; days and months are mapped
  (`today` → `આજે`, `Tue 29 Sep` → `મંગળ 29 સપ્ટે`); `AM`/`PM` are kept as written.
- Not translated, by rule: official IMD weather warnings (shown as issued, with a Gujarati note saying so); state,
  district and place names (CORE's English names); the evidence drawer (its button says "in English"); data-quality
  notices; compass letters (N, SW…).
- Behaviour change in English too: the Farmer home's "What should you know?" now shows the **farmer** context line on
  event cards (it showed the citizen line; step 6 already used the farmer line).
- Digits stay Western (0–9) in both languages; dates use Gujarati weekday and month names.

## 3. Tests (`npm test` in `web/`, run in CI)
Fixtures are CORE's real output, never a copy of its templates:
- `core_farmer_text.json`: frozen CORE `farmer.assess` run read-only on synthetic weather for all 8 crops × all
  stages × 4 weather scenarios (100 distinct indicator sentences).
- `core_event_text.json`: frozen CORE `risk.assess` run read-only on 28 synthetic weather scenarios × 10 seeds
  (139 distinct event headlines across all 10 system event types), plus the headlines and anomaly words from the five
  captured live CORE dashboards in `api-v2/tests/fixtures/` run through V2's own `build_events`.
The tests check that every sentence and headline is translated field by field, that numbers are carried over unchanged, that English
mode returns CORE text unchanged, that changed wording falls back to English, that the disclaimer keeps "not
instructions" and "official", and that every crop, season, stage and crop note in CORE's `crops.yaml` has Gujarati.

### Live check (daily)
\`web/test/live-coverage.ts\` (workflow \`translation-coverage.yml\`) fetches today's real CORE output, read-only: 12
dashboards (six in Gujarat, six in contrasting climates) and farmer reports for every crop × stage at two points. It
fails if any string the Gujarati or Hindi farmer screens would show is still in English, and lists each one in the job
summary. It runs every day at 07:45 IST once the workflow is on \`main\` (GitHub only schedules from the default
branch), and on every push that changes the translation files. First run, 1 Oct 2026: 25 live events, 86 farmer
reports, 3,888 strings checked, all translated in both languages. A deliberately reworded CORE headline was caught.

## 4. Before release: native-speaker review
I drafted these strings; I cannot vouch for agricultural Gujarati. The reviewer should be a native Gujarati speaker
who knows farm vocabulary (for example a KVK or AAU/JAU/NAU/SDAU extension contact). Strings I am least sure of:
`ડોડવા વિકાસ` (castor capsule development), `ચાપવા અવસ્થા` (cotton squaring), `સૂયા અવસ્થા` (groundnut pegging),
`માળ (સ્પાઇક)` (castor spike), `મોલો-મશી` (aphids), `ચરમી` (cumin blight), the level words `નજર રાખો` /
`સાવધાન` / `ગંભીર`, `હીટવેવ (લૂ)` and `શીતલહેર`, the rain categories in 4b, and whether `AM`/`PM` should be
replaced by Gujarati time words. Mark each row OK or give the correction (247 rows).

### 4a. Farmer report — CORE text (63 strings)

| # | Kind | English | Shown | OK? |
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
| 48 | Fixed text | SYSTEM-DERIVED WEATHER INDICATORS — computed automatically from forecast models using unvalidated thresholds. They are not farming instructions. Follow the official Agromet Advisory for decisions. | સિસ્ટમ-આધારિત હવામાન સૂચકાંકો — ફોરકાસ્ટ મોડેલોમાંથી, ચકાસણી ન થયેલી મર્યાદાઓ (થ્રેશોલ્ડ) વડે આપમેળે ગણાયેલા. આ ખેતી માટેની સૂચના નથી. નિર્ણય માટે સત્તાવાર કૃષિ-હવામાન સલાહ (Agromet Advisory) અનુસરો. |  |
| 49 | Fixed text | Official Agromet Advisory (IMD × ICAR — Gramin Krishi Mausam Sewa) | સત્તાવાર કૃષિ-હવામાન સલાહ (IMD × ICAR — ગ્રામીણ કૃષિ મૌસમ સેવા) |  |
| 50 | Fixed text | District Agromet Advisory Service bulletins are issued every Tuesday and Friday by IMD with State Agricultural Universities / KVKs. They are the authoritative source for farm operations. | જિલ્લા કૃષિ-હવામાન સલાહ સેવાના બુલેટિન IMD દ્વારા રાજ્ય કૃષિ યુનિવર્સિટીઓ / KVK સાથે મળીને દર મંગળવારે અને શુક્રવારે બહાર પડે છે. ખેતીના કામ માટે એ જ અધિકૃત સ્ત્રોત છે. |  |
| 51 | Fixed text | Not yet ingested automatically — requires IMD Agromet data access (see docs/ARCHITECTURE.md). | આ સલાહ હજી આપમેળે અહીં લાવવામાં આવતી નથી — તે માટે IMD કૃષિ-હવામાન ડેટાની પરવાનગી જરૂરી છે. |  |
| 52 | Fixed text | unvalidated | ચકાસણી બાકી |  |
| 53 | Fixed text | IMD — Agromet services | IMD — કૃષિ-હવામાન સેવાઓ |  |
| 54 | Fixed text | Meghdoot app (IMD/ICAR/IITM) — district advisories | મેઘદૂત એપ (IMD/ICAR/IITM) — જિલ્લાની સલાહ |  |
| 55 | Fixed text | Kisan Call Centre — 1800-180-1551 | કિસાન કોલ સેન્ટર — 1800-180-1551 |  |
| 56 | Fixed text | Terminal heat after anthesis shortens grain filling (Porter & Gawith 1999 review of wheat temperature responses). | ફૂલ આવ્યા પછીની ગરમી દાણા ભરાવાનો સમય ટૂંકો કરે છે (Porter & Gawith 1999, ઘઉં પર તાપમાનની અસરની સમીક્ષા). |  |
| 57 | Fixed text | Temperatures above ~35 °C at anthesis increase spikelet sterility (Jagadish et al. 2007). | ફૂલ અવસ્થાએ આશરે 35 °C થી વધુ તાપમાનથી દાણા ખાલી રહેવાનું (વંધ્યતા) વધે છે (Jagadish et al. 2007). |  |
| 58 | Fixed text | High heat at flowering raises square and boll shedding; validate local thresholds. | ફૂલ અવસ્થાએ વધુ ગરમીથી ચાપવા અને જીંડવા ખરવાનું વધે છે; સ્થાનિક મર્યાદાઓની ચકાસણી જરૂરી છે. |  |
| 59 | Fixed text | Heat stress at flowering/pegging reduces pod set. | ફૂલ/સૂયા અવસ્થાએ ગરમીનો તણાવ શીંગ બેસવાનું ઘટાડે છે. |  |
| 60 | Fixed text | Relatively heat tolerant; cold nights slow spike development. | ગરમી પ્રમાણમાં સહન કરે છે; ઠંડી રાતો માળ (સ્પાઇક) ના વિકાસને ધીમો પાડે છે. |  |
| 61 | Fixed text | Heat tolerant; very high temperature at flowering reduces seed set. | ગરમી સહન કરે છે; ફૂલ અવસ્થાએ ખૂબ ઊંચું તાપમાન દાણા બેસવાનું ઘટાડે છે. |  |
| 62 | Fixed text | Cloudy, humid spells at flowering favour blight (Alternaria) — a major Gujarat concern. | ફૂલ અવસ્થાએ વાદળછાયું, ભેજવાળું હવામાન ચરમી (Alternaria blight) ને અનુકૂળ છે — ગુજરાતમાં મોટી સમસ્યા. |  |
| 63 | Fixed text | Frost at flowering/pod fill damages pods; cloudy humid weather favours aphids. | ફૂલ/શીંગ ભરાવાની અવસ્થાએ હિમ શીંગોને નુકસાન કરે છે; વાદળછાયું ભેજવાળું હવામાન મોલો-મશી (એફિડ) ને અનુકૂળ છે. |  |

### 4b. Weather events — CORE headlines and V2 event text (76 strings)

| # | Kind | English | Shown | OK? |
| --- | --- | --- | --- | --- |
| 1 | Event title (heat) | Heat | ગરમી |  |
| 2 | Event title (cold) | Cold | ઠંડી |  |
| 3 | Event title (rain) | Heavy rain | ભારે વરસાદ |  |
| 4 | Event title (wind) | Strong wind | તેજ પવન |  |
| 5 | Event title (thunderstorm) | Thunderstorm potential — model derived | ગાજવીજ સાથે વાવાઝોડાની સંભાવના — મોડેલ આધારિત |  |
| 6 | Event title (lightning) | Lightning potential — model derived | વીજળી પડવાની સંભાવના — મોડેલ આધારિત |  |
| 7 | Event title (flood) | Flood-related risk (rainfall accumulation) | પૂર સંબંધિત જોખમ (એકઠો થયેલો વરસાદ) |  |
| 8 | Event title (drought) | Dry spell / rainfall deficit | વરસાદ વગરનો ગાળો / વરસાદની ઘટ |  |
| 9 | Event title (fog) | Fog | ધુમ્મસ |  |
| 10 | Event title (fire) | Fire weather | આગ માટે અનુકૂળ હવામાન |  |
| 11 | Headline (cold, example) | Cold-wave conditions Mon 05 Oct | સોમ 05 ઑક્ટો શીતલહેરની સ્થિતિ |  |
| 12 | Headline (cold, example) | Severe cold wave tomorrow | આવતીકાલે ગંભીર શીતલહેર |  |
| 13 | Headline (cold, example) | Severe cold wave Tue 29 Sep | મંગળ 29 સપ્ટે ગંભીર શીતલહેર |  |
| 14 | Headline (drought, example) | Last 30 days: 52 mm vs normal 120 mm (-57%, Deficient) | છેલ્લા 30 દિવસ: 52 મિમી, સામાન્ય 120 મિમી (-57%, ઓછો) |  |
| 15 | Headline (drought, example) | Last 30 days: 40 mm vs normal 120 mm (-67%, Large deficient) | છેલ્લા 30 દિવસ: 40 મિમી, સામાન્ય 120 મિમી (-67%, ઘણો ઓછો) |  |
| 16 | Headline (drought, example) | Last 30 days: 100 mm vs normal 133 mm (-25%, Deficient) | છેલ્લા 30 દિવસ: 100 મિમી, સામાન્ય 133 મિમી (-25%, ઓછો) |  |
| 17 | Headline (drought, example) | Last 30 days: 124 mm vs normal 160 mm (-22%, Deficient) | છેલ્લા 30 દિવસ: 124 મિમી, સામાન્ય 160 મિમી (-22%, ઓછો) |  |
| 18 | Headline (fire, example) | Hot, dry and windy spells ahead | આગળના દિવસોમાં ગરમ, સૂકા અને પવનવાળા ગાળા |  |
| 19 | Headline (flood, example) | 72-h rain up to 130 mm (incl. past 2 days) — flooding possible | 72 કલાકમાં 130 મિમી સુધી વરસાદ (છેલ્લા 2 દિવસ સહિત) — પૂર શક્ય |  |
| 20 | Headline (flood, example) | 72-h rain up to 690 mm (incl. past 2 days) — flooding possible | 72 કલાકમાં 690 મિમી સુધી વરસાદ (છેલ્લા 2 દિવસ સહિત) — પૂર શક્ય |  |
| 21 | Headline (flood, example) | 72-h rain up to 142 mm (incl. past 2 days) — flooding possible | 72 કલાકમાં 142 મિમી સુધી વરસાદ (છેલ્લા 2 દિવસ સહિત) — પૂર શક્ય |  |
| 22 | Headline (fog, example) | Visibility down to 600 m around Thu 01 AM | ગુરુ 01 AM આસપાસ દૃશ્યતા ઘટીને 600 મીટર |  |
| 23 | Headline (fog, example) | Visibility down to 30 m around Thu 12 AM | ગુરુ 12 AM આસપાસ દૃશ્યતા ઘટીને 30 મીટર |  |
| 24 | Headline (fog, example) | Visibility down to 340 m around Sun 10 PM | રવિ 10 PM આસપાસ દૃશ્યતા ઘટીને 340 મીટર |  |
| 25 | Headline (fog, example) | Visibility down to 60 m around Tue 01 AM | મંગળ 01 AM આસપાસ દૃશ્યતા ઘટીને 60 મીટર |  |
| 26 | Headline (heat, example) | Heat-wave conditions Sat 03 Oct | શનિ 03 ઑક્ટો હીટવેવ (લૂ) ની સ્થિતિ |  |
| 27 | Headline (heat, example) | Severe heat-wave conditions tomorrow | આવતીકાલે ગંભીર હીટવેવ (લૂ) ની સ્થિતિ |  |
| 28 | Headline (lightning, example) | Lightning risk present from Thu 1 Oct, 12 AM | ગુરુ 1 ઑક્ટો, 12 AM થી વીજળી પડવાનું જોખમ |  |
| 29 | Headline (lightning, example) | Lightning risk high from Thu 1 Oct, 6 AM | ગુરુ 1 ઑક્ટો, 6 AM થી વીજળી પડવાનું વધુ જોખમ |  |
| 30 | Headline (lightning, example) | Lightning risk present from Mon 28 Sep, 2 PM | સોમ 28 સપ્ટે, 2 PM થી વીજળી પડવાનું જોખમ |  |
| 31 | Headline (lightning, example) | Lightning risk present from Tue 29 Sep, 10 AM | મંગળ 29 સપ્ટે, 10 AM થી વીજળી પડવાનું જોખમ |  |
| 32 | Headline (rain, example) | Rather heavy rain Sat 03 Oct (50 mm) | શનિ 03 ઑક્ટો સાધારણ ભારે વરસાદ (50 મિમી) |  |
| 33 | Headline (rain, example) | Very heavy rain tomorrow (150 mm) | આવતીકાલે અતિ ભારે વરસાદ (150 મિમી) |  |
| 34 | Headline (rain, example) | Rather heavy rain today (58 mm) | આજે સાધારણ ભારે વરસાદ (58 મિમી) |  |
| 35 | Headline (thunderstorm, example) | Thunderstorm possible from Thu 1 Oct, 12 AM | ગુરુ 1 ઑક્ટો, 12 AM થી ગાજવીજ સાથે વાવાઝોડાની શક્યતા |  |
| 36 | Headline (thunderstorm, example) | Thunderstorm likely from Thu 1 Oct, 6 AM | ગુરુ 1 ઑક્ટો, 6 AM થી ગાજવીજ સાથે વાવાઝોડાની વધુ શક્યતા |  |
| 37 | Headline (thunderstorm, example) | Thunderstorm possible from Mon 28 Sep, 2 PM | સોમ 28 સપ્ટે, 2 PM થી ગાજવીજ સાથે વાવાઝોડાની શક્યતા |  |
| 38 | Headline (thunderstorm, example) | Thunderstorm possible from Tue 29 Sep, 10 AM | મંગળ 29 સપ્ટે, 10 AM થી ગાજવીજ સાથે વાવાઝોડાની શક્યતા |  |
| 39 | Headline (wind, example) | Gusts up to 57 km/h Tue 06 Oct | મંગળ 06 ઑક્ટો 57 કિમી/કલાક સુધીના પવનના ઝાટકા |  |
| 40 | Headline (wind, example) | Gusts up to 99 km/h tomorrow | આવતીકાલે 99 કિમી/કલાક સુધીના પવનના ઝાટકા |  |
| 41 | Headline (example) | Heat watch tomorrow | આવતીકાલે ગરમી પર નજર રાખો |  |
| 42 | Headline (example) | Heat-wave conditions today | આજે હીટવેવ (લૂ) ની સ્થિતિ |  |
| 43 | Headline (example) | Cold watch Sat 03 Oct | શનિ 03 ઑક્ટો ઠંડી પર નજર રાખો |  |
| 44 | Headline (example) | Cold-wave conditions tomorrow | આવતીકાલે શીતલહેરની સ્થિતિ |  |
| 45 | Model agreement (example) | Model agreement: 2 of 3 | મોડેલોની સહમતી: 3 માંથી 2 |  |
| 46 | Event text | Heat during this period may be relevant to field work and to crops at heat-sensitive stages. | આ સમયગાળાની ગરમી ખેતરના કામ અને ગરમી પ્રત્યે સંવેદનશીલ અવસ્થાના પાક માટે મહત્ત્વની હોઈ શકે. |  |
| 47 | Event text | Low night temperatures during this period may be relevant to crops at cold-sensitive stages. | આ સમયગાળાનું રાત્રિનું નીચું તાપમાન ઠંડી પ્રત્યે સંવેદનશીલ અવસ્થાના પાક માટે મહત્ત્વનું હોઈ શકે. |  |
| 48 | Event text | Rain during this period may affect field operations. | આ સમયગાળાનો વરસાદ ખેતરના કામને અસર કરી શકે. |  |
| 49 | Event text | Strong wind during this period may affect field operations and tall standing crops. | આ સમયગાળાનો તેજ પવન ખેતરના કામ અને ઊંચા ઊભા પાકને અસર કરી શકે. |  |
| 50 | Event text | If thunderstorms develop, they may interrupt field operations. | જો ગાજવીજ સાથે વાવાઝોડું થાય, તો ખેતરનું કામ અટકી શકે. |  |
| 51 | Event text | Lightning potential is most relevant to people working in open fields. | વીજળી પડવાની સંભાવના ખુલ્લા ખેતરમાં કામ કરતા લોકો માટે સૌથી વધુ મહત્ત્વની છે. |  |
| 52 | Event text | Accumulated rain may be relevant to waterlogging in low-lying fields. | એકઠો થયેલો વરસાદ નીચાણવાળા ખેતરોમાં પાણી ભરાવા માટે મહત્ત્વનો હોઈ શકે. |  |
| 53 | Event text | Low visibility may affect early-morning field work and transport. | ઓછી દૃશ્યતા વહેલી સવારના ખેતરના કામ અને વાહનવ્યવહારને અસર કરી શકે. |  |
| 54 | Event text | Hot, dry and windy conditions may be relevant to fire in dry fields and crop residue. | ગરમ, સૂકું અને પવનવાળું હવામાન સૂકા ખેતરો અને પાકના અવશેષોમાં આગ માટે મહત્ત્વનું હોઈ શકે. |  |
| 55 | Event text | A rainfall deficit during this period may be relevant to soil moisture and irrigation. | આ સમયગાળાની વરસાદની ઘટ જમીનના ભેજ અને પિયત માટે મહત્ત્વની હોઈ શકે. |  |
| 56 | Event text | Timing not provided by CORE for this risk; see the headline. | CORE એ આ જોખમનો સમય આપ્યો નથી; મુખ્ય વાક્ય જુઓ. |  |
| 57 | Event text | Model agreement: not assessed | મોડેલોની સહમતી: આકારણી નથી |  |
| 58 | Weekday | Mon | સોમ |  |
| 59 | Weekday | Tue | મંગળ |  |
| 60 | Weekday | Wed | બુધ |  |
| 61 | Weekday | Thu | ગુરુ |  |
| 62 | Weekday | Fri | શુક્ર |  |
| 63 | Weekday | Sat | શનિ |  |
| 64 | Weekday | Sun | રવિ |  |
| 65 | Month | Jan | જાન્યુ |  |
| 66 | Month | Feb | ફેબ્રુ |  |
| 67 | Month | Mar | માર્ચ |  |
| 68 | Month | Apr | એપ્રિલ |  |
| 69 | Month | May | મે |  |
| 70 | Month | Jun | જૂન |  |
| 71 | Month | Jul | જુલાઈ |  |
| 72 | Month | Aug | ઑગસ્ટ |  |
| 73 | Month | Sep | સપ્ટે |  |
| 74 | Month | Oct | ઑક્ટો |  |
| 75 | Month | Nov | નવે |  |
| 76 | Month | Dec | ડિસે |  |

### 4c. Farmer home — CORE weather words (36 strings)

| # | Kind | English | Shown | OK? |
| --- | --- | --- | --- | --- |
| 1 | Word | Max temperature | મહત્તમ તાપમાન |  |
| 2 | Word | Min temperature | લઘુત્તમ તાપમાન |  |
| 3 | Word | Max temperature (7-day mean) | મહત્તમ તાપમાન (7 દિવસની સરેરાશ) |  |
| 4 | Word | Rainfall | વરસાદ |  |
| 5 | Word | Today | આજે |  |
| 6 | Word | Next 7 days | આવતા 7 દિવસ |  |
| 7 | Word | Next 7 days (forecast) | આવતા 7 દિવસ (આગાહી) |  |
| 8 | Word | Past 30 days (model analysis) | છેલ્લા 30 દિવસ (મોડેલ વિશ્લેષણ) |  |
| 9 | Word | Above normal | સામાન્યથી વધુ |  |
| 10 | Word | Below normal | સામાન્યથી ઓછું |  |
| 11 | Word | Near normal | લગભગ સામાન્ય |  |
| 12 | Word | Large excess | ઘણો વધુ |  |
| 13 | Word | Excess | વધુ |  |
| 14 | Word | Normal | સામાન્ય |  |
| 15 | Word | Deficient | ઓછો |  |
| 16 | Word | Large deficient | ઘણો ઓછો |  |
| 17 | Word | No rain | વરસાદ નહીં |  |
| 18 | Word | Dry season | સૂકી ઋતુ |  |
| 19 | Word | Rain in dry season | સૂકી ઋતુમાં વરસાદ |  |
| 20 | Word | Open-Meteo best-match (model analysis, not a station observation) | Open-Meteo best-match (મોડેલ વિશ્લેષણ, હવામાન મથકનું અવલોકન નથી) |  |
| 21 | Word | plains | મેદાની વિસ્તાર |  |
| 22 | Word | coastal | દરિયાકાંઠો |  |
| 23 | Word | hills | પહાડી વિસ્તાર |  |
| 24 | Word | Clear | ચોખ્ખું આકાશ |  |
| 25 | Word | Partly cloudy | આંશિક વાદળછાયું |  |
| 26 | Word | Overcast | ઘેરાં વાદળ |  |
| 27 | Word | Fog | ધુમ્મસ |  |
| 28 | Word | Drizzle | ઝરમર |  |
| 29 | Word | Rain | વરસાદ |  |
| 30 | Word | Heavy rain | ભારે વરસાદ |  |
| 31 | Word | Snow | હિમવર્ષા |  |
| 32 | Word | Showers | ઝાપટાં |  |
| 33 | Word | Violent showers | ખૂબ ભારે ઝાપટાં |  |
| 34 | Word | Thunderstorm | ગાજવીજ સાથે વાવાઝોડું |  |
| 35 | Word | Thunderstorm with hail | કરા સાથે ગાજવીજ અને વાવાઝોડું |  |
| 36 | Word | No significant weather event detected. | કોઈ મહત્ત્વની હવામાન ઘટના મળી નથી. |  |

### 4d. Screen labels written by V2 (72 strings)

| # | Key | English | Shown | OK? |
| --- | --- | --- | --- | --- |
| 1 | wtk_title | What should you know? | તમારે શું જાણવું જોઈએ? |  |
| 2 | feels | Feels like | અનુભવાતું તાપમાન |  |
| 3 | rain_now | Rain now | હાલનો વરસાદ |  |
| 4 | humidity | Humidity | ભેજ |  |
| 5 | wind | Wind | પવન |  |
| 6 | gusts | gusts | ઝાટકા |  |
| 7 | pressure | Pressure | હવાનું દબાણ |  |
| 8 | cloud | Cloud | વાદળ |  |
| 9 | visibility | Visibility | દૃશ્યતા |  |
| 10 | u_mm | mm | મિમી |  |
| 11 | u_kmh | km/h | કિમી/કલાક |  |
| 12 | u_km | km | કિમી |  |
| 13 | as_of | As of | સમય: |  |
| 14 | point_note | point forecast at model-grid resolution | મોડેલ-ગ્રીડના એક બિંદુની આગાહી |  |
| 15 | wtk_summary | 1 official alert · 2 system assessments at Watch or above (…) · next 7 days | 1 સત્તાવાર ચેતવણી · 2 સિસ્ટમ મૂલ્યાંકન 'નજર રાખો' કે તેથી ઉપરના સ્તરે (…) · આવતા 7 દિવસ |  |
| 16 | sev_names | Severe / Alert / Watch | ગંભીર / સાવધાન / નજર રાખો |  |
| 17 | none_detail | No official alert for this location and no CORE risk at Watch level or above in the next 7 days. | આ સ્થળ માટે કોઈ સત્તાવાર ચેતવણી નથી અને આવતા 7 દિવસમાં CORE નું કોઈ જોખમ 'નજર રાખો' કે તેથી ઉપરના સ્તરે નથી. |  |
| 18 | official_alert | Official alert | સત્તાવાર ચેતવણી |  |
| 19 | more_official | +3 more official alerts | +3 વધુ સત્તાવાર ચેતવણીઓ |  |
| 20 | system_note | CORE risk rules · next 7 days · not official warnings | CORE ના જોખમ નિયમો · આવતા 7 દિવસ · સત્તાવાર ચેતવણી નથી |  |
| 21 | show_more | Show 3 more system assessments | વધુ 3 સિસ્ટમ મૂલ્યાંકન બતાવો |  |
| 22 | dep_title | Departure from normal | સામાન્યથી તફાવત |  |
| 23 | dep_sub | · not a hazard on its own | · પોતે જોખમ નથી |  |
| 24 | forecast | forecast | આગાહી |  |
| 25 | normal | normal | સામાન્ય |  |
| 26 | normal_note | Normal: NASA POWER 1991–2020 (MERRA-2 reanalysis), indicative — not IMD normals. | સામાન્ય: NASA POWER 1991–2020 (MERRA-2 રીએનાલિસિસ), અંદાજિત — IMD ના સામાન્ય આંકડા નથી. |  |
| 27 | v2_down | The V2 event service is unavailable. CORE's own risk list is still under Risks & alerts. | V2 ઘટના સેવા હાલ ઉપલબ્ધ નથી. CORE ની પોતાની જોખમ યાદી 'Risks & alerts' માં છે. |  |
| 28 | system_label | System assessment | સિસ્ટમ મૂલ્યાંકન |  |
| 29 | lang_switch | Language | ભાષા |  |
| 30 | field_title | Your field — location, crop, growth stage | તમારું ખેતર — સ્થળ, પાક, પાકની અવસ્થા |  |
| 31 | loc_state | 1 · Location — state | 1 · સ્થળ — રાજ્ય |  |
| 32 | loc_district | 1 · Location — district | 1 · સ્થળ — જિલ્લો |  |
| 33 | sel_state | Select state | રાજ્ય પસંદ કરો |  |
| 34 | sel_district | Select district | જિલ્લો પસંદ કરો |  |
| 35 | crop | 2 · Crop | 2 · પાક |  |
| 36 | sel_crop | Select crop | પાક પસંદ કરો |  |
| 37 | stage | 3 · Growth stage | 3 · પાકની અવસ્થા |  |
| 38 | sel_stage | Select stage | અવસ્થા પસંદ કરો |  |
| 39 | field_location | Field location: | ખેતરનું સ્થળ: |  |
| 40 | field_help | For a village, use the location search at the top; the forecast is a point forecast at model-grid resolution. | ગામ માટે ઉપરના સ્થળ-શોધનો ઉપયોગ કરો; આગાહી મોડેલ-ગ્રીડના એક બિંદુ માટેની છે. |  |
| 41 | official_later | The official agricultural advisory is shown separately in step 7. | સત્તાવાર કૃષિ સલાહ પગલું 7 માં અલગથી બતાવી છે. |  |
| 42 | choose_prompt | Choose a crop and growth stage to see weather indicators for your field. | તમારા ખેતર માટે હવામાન સૂચકાંકો જોવા પાક અને પાકની અવસ્થા પસંદ કરો. |  |
| 43 | weather_title | 4 · Weather — next days at your field | 4 · હવામાન — તમારા ખેતર પર આવતા દિવસો |  |
| 44 | th_day | Day | દિવસ |  |
| 45 | th_temp | Max / min °C | મહત્તમ / લઘુત્તમ °C |  |
| 46 | th_rain | Rain mm | વરસાદ મિમી |  |
| 47 | th_chance | Chance | શક્યતા |  |
| 48 | th_spray | Spray-suitable hours* | છંટકાવ માટે યોગ્ય કલાક* |  |
| 49 | th_disease | Disease-favourable hours* | રોગને અનુકૂળ કલાક* |  |
| 50 | weather_note | Forecast values from CORE. *Spray and disease hours are system-derived, unvalidated indicators from CORE's thresholds. | આગાહીના આંકડા CORE માંથી. *છંટકાવ અને રોગના કલાક CORE ની મર્યાદાઓ પરથી ગણાયેલા સિસ્ટમ-આધારિત, ચકાસણી ન થયેલા સૂચકાંકો છે. |  |
| 51 | ind_title | 5 · System indicators | 5 · સિસ્ટમ સૂચકાંકો |  |
| 52 | badge_system | System-derived | સિસ્ટમ-આધારિત |  |
| 53 | badge_unvalidated | Unvalidated | ચકાસણી થયેલ નથી |  |
| 54 | core_status | CORE status: | CORE સ્થિતિ: |  |
| 55 | rule | Rule: | નિયમ: |  |
| 56 | rule_suffix | system-derived, unvalidated | સિસ્ટમ-આધારિત, ચકાસણી થયેલ નથી |  |
| 57 | rel_title | 6 · Potential crop relevance — weather events | 6 · પાક પર સંભવિત અસર — હવામાનની ઘટનાઓ |  |
| 58 | rel_head | Potential crop relevance | પાક પર સંભવિત અસર |  |
| 59 | rel_none | No significant weather event detected for this field in CORE's 7-day assessment. | CORE ના 7 દિવસના મૂલ્યાંકનમાં આ ખેતર માટે કોઈ મહત્ત્વની હવામાન ઘટના મળી નથી. |  |
| 60 | rel_uses | Existing CORE indicators for Cotton (…) that use …: | કપાસ (…) માટેના CORE ના હાલના સૂચકાંકો, જે … પર આધારિત છે: |  |
| 61 | rel_no_ind | No existing CORE crop indicator for Cotton at this stage uses this signal. V2 does not add agronomic rules. | આ અવસ્થાએ કપાસ માટે CORE નો કોઈ સૂચકાંક આ સંકેતનો ઉપયોગ કરતો નથી. V2 ખેતીના નવા નિયમો ઉમેરતું નથી. |  |
| 62 | rel_official | Official advisory: … — step 7 below. | સત્તાવાર સલાહ: … — નીચે પગલું 7. |  |
| 63 | off_head | 7 · Official agricultural advisory | 7 · સત્તાવાર કૃષિ સલાહ |  |
| 64 | off_sep | Steps 5 and 6 are system output, not an official agricultural advisory. For farm decisions, follow the official advisory. | પગલાં 5 અને 6 સિસ્ટમનું પરિણામ છે, સત્તાવાર કૃષિ સલાહ નથી. ખેતીના નિર્ણયો માટે સત્તાવાર સલાહ અનુસરો. |  |
| 65 | alerts_title | Official weather alerts for this area | આ વિસ્તાર માટે સત્તાવાર હવામાન ચેતવણીઓ |  |
| 66 | alerts_note | — | સત્તાવાર ચેતવણીઓ જારી થયેલી ભાષામાં જ બતાવી છે; તેનો અનુવાદ કરવામાં આવતો નથી. |  |
| 67 | english_kept | — | અંગ્રેજીમાં (અનુવાદ ઉપલબ્ધ નથી) |  |
| 68 | signal | daily maximum temperature | દૈનિક મહત્તમ તાપમાન |  |
| 69 | signal | daily minimum temperature | દૈનિક લઘુત્તમ તાપમાન |  |
| 70 | signal | daily rainfall | દૈનિક વરસાદ |  |
| 71 | signal | consecutive dry days | સળંગ કોરા દિવસો |  |
| 72 | event card | When: / Experimental / Potential relevance · context / View evidence | ક્યારે: / પ્રાયોગિક / સંભવિત સુસંગતતા · સામાન્ય સંદર્ભ, અસરની આગાહી નથી / પુરાવા જુઓ (અંગ્રેજીમાં) |  |

