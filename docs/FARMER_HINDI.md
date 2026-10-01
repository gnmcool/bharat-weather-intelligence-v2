# Farmer screens in Hindi

| Item | Value |
| --- | --- |
| Status | built on `feature/farmer-gujarati`; **not released**. Release needs (1) native-speaker sign-off of every string below and (2) owner approval to merge to `main` |
| Scope | the same as Gujarati: the whole Farmer home (current weather, "What should you know?", event cards) and the field workflow (steps 1–7). The switch reads English · ગુજરાતી · हिन्दी |
| Method | identical to Gujarati (`docs/FARMER_GUJARATI.md` §1–3): CORE's English is matched against CORE's fixed patterns, numbers are copied unchanged, anything that does not match stays English. Same exclusions: official IMD warnings, place names, the evidence drawer, data-quality notices |
| Code | `web/src/i18n/coreText.ts` (`hi` column), `web/src/i18n/lang.ts` (`hi` labels) |
| Tests | every check in `web/test/coreText.test.ts` runs for Hindi as well as Gujarati, on the same real-CORE fixtures; Hindi output must be in Devanagari and contain no Gujarati script (and vice versa) |
| CORE | unchanged (core-v1.0, 2840f8d) |

## Before release: native-speaker review
The reviewer should be a native Hindi speaker who knows farm vocabulary (for example a KVK or ICAR extension contact).
Strings I am least sure of:
- `कल` for "tomorrow" — in Hindi it also means "yesterday"; context usually settles it, but `आने वाला कल` is the
  unambiguous alternative.
- `कुछ भारी` for IMD's "rather heavy" rain — IMD's own Hindi bulletins should decide this term.
- Crop-stage terms: `खूँटी (पेग) बनने की अवस्था` (groundnut pegging), `डोडा (कैप्सूल) विकास` (castor capsules),
  `टिंडा विकास` (cotton bolls), `कली बनने की अवस्था` (cotton squaring); season `ज़ायद`.
- Pest and disease words: `माहू` (aphids), `झुलसा रोग` (cumin blight).
- `सूखा अंतराल` (dry spell) — must not read as "drought".
- The level words `नज़र रखें` / `सावधान` / `गंभीर`, and whether `AM`/`PM` should become Hindi time words.

Mark each row OK or give the correction (247 rows).

### 4a. Farmer report — CORE text (63 strings)

| # | Kind | English | Shown | OK? |
| --- | --- | --- | --- | --- |
| 1 | Level | No risk | जोखिम नहीं |  |
| 2 | Level | Watch | नज़र रखें |  |
| 3 | Level | Alert | सावधान |  |
| 4 | Level | Severe | गंभीर |  |
| 5 | Crop | Wheat | गेहूँ |  |
| 6 | Crop | Rice (paddy) | धान |  |
| 7 | Crop | Cotton | कपास |  |
| 8 | Crop | Groundnut | मूँगफली |  |
| 9 | Crop | Castor | अरंडी |  |
| 10 | Crop | Pearl millet (bajra) | बाजरा |  |
| 11 | Crop | Cumin (jeera) | जीरा |  |
| 12 | Crop | Mustard | सरसों |  |
| 13 | Season | Rabi | रबी |  |
| 14 | Season | Kharif | खरीफ़ |  |
| 15 | Season | Kharif / Summer | खरीफ़ / ज़ायद |  |
| 16 | Stage | sowing | बुवाई |  |
| 17 | Stage | nursery | नर्सरी (पौधशाला) |  |
| 18 | Stage | transplanting | रोपाई |  |
| 19 | Stage | vegetative | वानस्पतिक वृद्धि |  |
| 20 | Stage | squaring | कली बनने की अवस्था |  |
| 21 | Stage | flowering | फूल अवस्था |  |
| 22 | Stage | pegging | खूँटी (पेग) बनने की अवस्था |  |
| 23 | Stage | pod fill | फली भराव |  |
| 24 | Stage | grain fill | दाना भराव |  |
| 25 | Stage | boll development | टिंडा विकास |  |
| 26 | Stage | capsule development | डोडा (कैप्सूल) विकास |  |
| 27 | Stage | seed development | बीज विकास |  |
| 28 | Stage | harvest | कटाई |  |
| 29 | Indicator name | Heavy rain | भारी वर्षा |  |
| 30 | Indicator value (example) | max 40 mm/day | अधिकतम 40 मिमी/दिन |  |
| 31 | Indicator rule (example) | IMD heavy rain ≥ 64.5 mm/day (Watch ≥ 35.6) | IMD के अनुसार भारी वर्षा ≥ 64.5 मिमी/दिन (नज़र रखें ≥ 35.6) |  |
| 32 | Indicator name | Dry spell | सूखा अंतराल |  |
| 33 | Indicator value (example) | 1 days | 1 दिन |  |
| 34 | Indicator rule (example) | Consecutive days < 2.5 mm | लगातार दिन, हर दिन 2.5 मिमी से कम वर्षा |  |
| 35 | Indicator name | Disease-favourable weather | रोग के अनुकूल मौसम |  |
| 36 | Indicator value (example) | 38 humid hours (RH ≥ 85%, 15–30 °C) | 38 नम घंटे (आर्द्रता ≥ 85%, 15–30 °C) |  |
| 37 | Indicator rule (example) | Leaf-wetness proxy | पत्ती के गीलेपन का अनुमान |  |
| 38 | Indicator name | Heat stress for this stage | इस अवस्था में गर्मी का तनाव |  |
| 39 | Indicator value (example) | 3 of 7 days ≥ 32 °C | 7 में से 3 दिन ≥ 32 °C |  |
| 40 | Indicator rule (example) | Tmax ≥ 32 °C at flowering | फूल अवस्था पर अधिकतम तापमान ≥ 32 °C |  |
| 41 | Indicator name | Cold / frost stress | ठंड / पाले का तनाव |  |
| 42 | Indicator value (example) | 1 of 7 nights ≤ 3 °C | 7 में से 1 रातें ≤ 3 °C |  |
| 43 | Indicator rule (example) | Tmin ≤ 3 °C at flowering | फूल अवस्था पर न्यूनतम तापमान ≤ 3 °C |  |
| 44 | Indicator name | Dry harvest window | कटाई के लिए सूखी अवधि |  |
| 45 | Indicator value (example) | longest dry run 1 days | सबसे लंबी सूखी अवधि 1 दिन |  |
| 46 | Indicator rule (example) | days < 1.0 mm & rain prob < 30% | दिन: वर्षा < 1.0 मिमी और वर्षा की संभावना < 30% |  |
| 47 | Indicator rule (example) | Leaf-wetness proxy; stage-sensitive for this crop | पत्ती के गीलेपन का अनुमान; इस फसल के लिए यह अवस्था संवेदनशील है |  |
| 48 | Fixed text | SYSTEM-DERIVED WEATHER INDICATORS — computed automatically from forecast models using unvalidated thresholds. They are not farming instructions. Follow the official Agromet Advisory for decisions. | सिस्टम-आधारित मौसम संकेतक — पूर्वानुमान मॉडलों से, बिना सत्यापित सीमाओं (थ्रेशोल्ड) के आधार पर अपने-आप गणना किए गए। ये खेती के निर्देश नहीं हैं। निर्णय के लिए आधिकारिक कृषि-मौसम सलाह (Agromet Advisory) का पालन करें। |  |
| 49 | Fixed text | Official Agromet Advisory (IMD × ICAR — Gramin Krishi Mausam Sewa) | आधिकारिक कृषि-मौसम सलाह (IMD × ICAR — ग्रामीण कृषि मौसम सेवा) |  |
| 50 | Fixed text | District Agromet Advisory Service bulletins are issued every Tuesday and Friday by IMD with State Agricultural Universities / KVKs. They are the authoritative source for farm operations. | ज़िला कृषि-मौसम सलाह सेवा के बुलेटिन IMD द्वारा राज्य कृषि विश्वविद्यालयों / KVK के साथ मिलकर हर मंगलवार और शुक्रवार को जारी किए जाते हैं। खेती के कामों के लिए यही प्रामाणिक स्रोत है। |  |
| 51 | Fixed text | Not yet ingested automatically — requires IMD Agromet data access (see docs/ARCHITECTURE.md). | यह सलाह अभी अपने-आप यहाँ नहीं लाई जाती — इसके लिए IMD कृषि-मौसम डेटा की अनुमति ज़रूरी है। |  |
| 52 | Fixed text | unvalidated | सत्यापन बाकी |  |
| 53 | Fixed text | IMD — Agromet services | IMD — कृषि-मौसम सेवाएँ |  |
| 54 | Fixed text | Meghdoot app (IMD/ICAR/IITM) — district advisories | मेघदूत ऐप (IMD/ICAR/IITM) — ज़िला सलाह |  |
| 55 | Fixed text | Kisan Call Centre — 1800-180-1551 | किसान कॉल सेंटर — 1800-180-1551 |  |
| 56 | Fixed text | Terminal heat after anthesis shortens grain filling (Porter & Gawith 1999 review of wheat temperature responses). | फूल आने के बाद की गर्मी दाना भरने का समय घटा देती है (Porter & Gawith 1999, गेहूँ पर तापमान के प्रभाव की समीक्षा)। |  |
| 57 | Fixed text | Temperatures above ~35 °C at anthesis increase spikelet sterility (Jagadish et al. 2007). | फूल अवस्था में लगभग 35 °C से अधिक तापमान से दाने खाली रहने (बंध्यता) की समस्या बढ़ती है (Jagadish et al. 2007)। |  |
| 58 | Fixed text | High heat at flowering raises square and boll shedding; validate local thresholds. | फूल अवस्था में अधिक गर्मी से कलियों और टिंडों का झड़ना बढ़ता है; स्थानीय सीमाओं का सत्यापन ज़रूरी है। |  |
| 59 | Fixed text | Heat stress at flowering/pegging reduces pod set. | फूल/खूँटी अवस्था में गर्मी का तनाव फलियाँ बनना घटाता है। |  |
| 60 | Fixed text | Relatively heat tolerant; cold nights slow spike development. | गर्मी अपेक्षाकृत सह लेती है; ठंडी रातें बाली (स्पाइक) के विकास को धीमा करती हैं। |  |
| 61 | Fixed text | Heat tolerant; very high temperature at flowering reduces seed set. | गर्मी सहनशील; फूल अवस्था में बहुत अधिक तापमान दाने बनना घटाता है। |  |
| 62 | Fixed text | Cloudy, humid spells at flowering favour blight (Alternaria) — a major Gujarat concern. | फूल अवस्था में बादल और नमी वाला मौसम झुलसा रोग (Alternaria blight) के अनुकूल है — गुजरात में बड़ी समस्या। |  |
| 63 | Fixed text | Frost at flowering/pod fill damages pods; cloudy humid weather favours aphids. | फूल/फली भराव अवस्था में पाला फलियों को नुकसान पहुँचाता है; बादल और नमी वाला मौसम माहू (एफिड) के अनुकूल है। |  |

### 4b. Weather events — CORE headlines and V2 event text (76 strings)

| # | Kind | English | Shown | OK? |
| --- | --- | --- | --- | --- |
| 1 | Event title (heat) | Heat | गर्मी |  |
| 2 | Event title (cold) | Cold | ठंड |  |
| 3 | Event title (rain) | Heavy rain | भारी वर्षा |  |
| 4 | Event title (wind) | Strong wind | तेज़ हवा |  |
| 5 | Event title (thunderstorm) | Thunderstorm potential — model derived | गरज-चमक के साथ तूफ़ान की संभावना — मॉडल आधारित |  |
| 6 | Event title (lightning) | Lightning potential — model derived | बिजली गिरने की संभावना — मॉडल आधारित |  |
| 7 | Event title (flood) | Flood-related risk (rainfall accumulation) | बाढ़ से जुड़ा जोखिम (जमा हुई वर्षा) |  |
| 8 | Event title (drought) | Dry spell / rainfall deficit | सूखा अंतराल / वर्षा की कमी |  |
| 9 | Event title (fog) | Fog | कोहरा |  |
| 10 | Event title (fire) | Fire weather | आग के अनुकूल मौसम |  |
| 11 | Headline (cold, example) | Cold-wave conditions Mon 05 Oct | सोम 05 अक्टू॰ शीतलहर की स्थिति |  |
| 12 | Headline (cold, example) | Severe cold wave tomorrow | कल गंभीर शीतलहर |  |
| 13 | Headline (cold, example) | Severe cold wave Tue 29 Sep | मंगल 29 सित॰ गंभीर शीतलहर |  |
| 14 | Headline (drought, example) | Last 30 days: 52 mm vs normal 120 mm (-57%, Deficient) | पिछले 30 दिन: 52 मिमी, सामान्य 120 मिमी (-57%, कम) |  |
| 15 | Headline (drought, example) | Last 30 days: 40 mm vs normal 120 mm (-67%, Large deficient) | पिछले 30 दिन: 40 मिमी, सामान्य 120 मिमी (-67%, बहुत कम) |  |
| 16 | Headline (drought, example) | Last 30 days: 100 mm vs normal 133 mm (-25%, Deficient) | पिछले 30 दिन: 100 मिमी, सामान्य 133 मिमी (-25%, कम) |  |
| 17 | Headline (drought, example) | Last 30 days: 124 mm vs normal 160 mm (-22%, Deficient) | पिछले 30 दिन: 124 मिमी, सामान्य 160 मिमी (-22%, कम) |  |
| 18 | Headline (fire, example) | Hot, dry and windy spells ahead | आगे गर्म, सूखे और तेज़ हवा वाले दौर |  |
| 19 | Headline (flood, example) | 72-h rain up to 130 mm (incl. past 2 days) — flooding possible | 72 घंटों में 130 मिमी तक वर्षा (पिछले 2 दिन सहित) — बाढ़ संभव |  |
| 20 | Headline (flood, example) | 72-h rain up to 690 mm (incl. past 2 days) — flooding possible | 72 घंटों में 690 मिमी तक वर्षा (पिछले 2 दिन सहित) — बाढ़ संभव |  |
| 21 | Headline (flood, example) | 72-h rain up to 142 mm (incl. past 2 days) — flooding possible | 72 घंटों में 142 मिमी तक वर्षा (पिछले 2 दिन सहित) — बाढ़ संभव |  |
| 22 | Headline (fog, example) | Visibility down to 600 m around Thu 01 AM | गुरु 01 AM के आसपास दृश्यता घटकर 600 मीटर |  |
| 23 | Headline (fog, example) | Visibility down to 30 m around Thu 12 AM | गुरु 12 AM के आसपास दृश्यता घटकर 30 मीटर |  |
| 24 | Headline (fog, example) | Visibility down to 340 m around Sun 10 PM | रवि 10 PM के आसपास दृश्यता घटकर 340 मीटर |  |
| 25 | Headline (fog, example) | Visibility down to 60 m around Tue 01 AM | मंगल 01 AM के आसपास दृश्यता घटकर 60 मीटर |  |
| 26 | Headline (heat, example) | Heat-wave conditions Sat 03 Oct | शनि 03 अक्टू॰ लू (हीटवेव) की स्थिति |  |
| 27 | Headline (heat, example) | Severe heat-wave conditions tomorrow | कल गंभीर लू (हीटवेव) की स्थिति |  |
| 28 | Headline (lightning, example) | Lightning risk present from Thu 1 Oct, 12 AM | गुरु 1 अक्टू॰, 12 AM से बिजली गिरने का खतरा |  |
| 29 | Headline (lightning, example) | Lightning risk high from Thu 1 Oct, 6 AM | गुरु 1 अक्टू॰, 6 AM से बिजली गिरने का अधिक खतरा |  |
| 30 | Headline (lightning, example) | Lightning risk present from Mon 28 Sep, 2 PM | सोम 28 सित॰, 2 PM से बिजली गिरने का खतरा |  |
| 31 | Headline (lightning, example) | Lightning risk present from Tue 29 Sep, 10 AM | मंगल 29 सित॰, 10 AM से बिजली गिरने का खतरा |  |
| 32 | Headline (rain, example) | Rather heavy rain Sat 03 Oct (50 mm) | शनि 03 अक्टू॰ कुछ भारी वर्षा (50 मिमी) |  |
| 33 | Headline (rain, example) | Very heavy rain tomorrow (150 mm) | कल बहुत भारी वर्षा (150 मिमी) |  |
| 34 | Headline (rain, example) | Rather heavy rain today (58 mm) | आज कुछ भारी वर्षा (58 मिमी) |  |
| 35 | Headline (thunderstorm, example) | Thunderstorm possible from Thu 1 Oct, 12 AM | गुरु 1 अक्टू॰, 12 AM से गरज-चमक के साथ तूफ़ान की संभावना |  |
| 36 | Headline (thunderstorm, example) | Thunderstorm likely from Thu 1 Oct, 6 AM | गुरु 1 अक्टू॰, 6 AM से गरज-चमक के साथ तूफ़ान की अधिक संभावना |  |
| 37 | Headline (thunderstorm, example) | Thunderstorm possible from Mon 28 Sep, 2 PM | सोम 28 सित॰, 2 PM से गरज-चमक के साथ तूफ़ान की संभावना |  |
| 38 | Headline (thunderstorm, example) | Thunderstorm possible from Tue 29 Sep, 10 AM | मंगल 29 सित॰, 10 AM से गरज-चमक के साथ तूफ़ान की संभावना |  |
| 39 | Headline (wind, example) | Gusts up to 57 km/h Tue 06 Oct | मंगल 06 अक्टू॰ 57 किमी/घंटा तक के हवा के झोंके |  |
| 40 | Headline (wind, example) | Gusts up to 99 km/h tomorrow | कल 99 किमी/घंटा तक के हवा के झोंके |  |
| 41 | Headline (example) | Heat watch tomorrow | कल गर्मी पर नज़र रखें |  |
| 42 | Headline (example) | Heat-wave conditions today | आज लू (हीटवेव) की स्थिति |  |
| 43 | Headline (example) | Cold watch Sat 03 Oct | शनि 03 अक्टू॰ ठंड पर नज़र रखें |  |
| 44 | Headline (example) | Cold-wave conditions tomorrow | कल शीतलहर की स्थिति |  |
| 45 | Model agreement (example) | Model agreement: 2 of 3 | मॉडलों की सहमति: 3 में से 2 |  |
| 46 | Event text | Heat during this period may be relevant to field work and to crops at heat-sensitive stages. | इस अवधि की गर्मी खेत के काम और गर्मी के प्रति संवेदनशील अवस्था वाली फसलों के लिए महत्वपूर्ण हो सकती है। |  |
| 47 | Event text | Low night temperatures during this period may be relevant to crops at cold-sensitive stages. | इस अवधि में रात का कम तापमान ठंड के प्रति संवेदनशील अवस्था वाली फसलों के लिए महत्वपूर्ण हो सकता है। |  |
| 48 | Event text | Rain during this period may affect field operations. | इस अवधि की वर्षा खेत के कामों को प्रभावित कर सकती है। |  |
| 49 | Event text | Strong wind during this period may affect field operations and tall standing crops. | इस अवधि की तेज़ हवा खेत के कामों और ऊँची खड़ी फसलों को प्रभावित कर सकती है। |  |
| 50 | Event text | If thunderstorms develop, they may interrupt field operations. | अगर गरज-चमक के साथ तूफ़ान आता है, तो खेत का काम रुक सकता है। |  |
| 51 | Event text | Lightning potential is most relevant to people working in open fields. | बिजली गिरने की संभावना खुले खेतों में काम करने वालों के लिए सबसे अधिक महत्वपूर्ण है। |  |
| 52 | Event text | Accumulated rain may be relevant to waterlogging in low-lying fields. | जमा हुई वर्षा निचले खेतों में जलभराव के लिए महत्वपूर्ण हो सकती है। |  |
| 53 | Event text | Low visibility may affect early-morning field work and transport. | कम दृश्यता सुबह-सुबह के खेत के काम और परिवहन को प्रभावित कर सकती है। |  |
| 54 | Event text | Hot, dry and windy conditions may be relevant to fire in dry fields and crop residue. | गर्म, सूखा और तेज़ हवा वाला मौसम सूखे खेतों और फसल अवशेषों में आग के लिए महत्वपूर्ण हो सकता है। |  |
| 55 | Event text | A rainfall deficit during this period may be relevant to soil moisture and irrigation. | इस अवधि की वर्षा की कमी मिट्टी की नमी और सिंचाई के लिए महत्वपूर्ण हो सकती है। |  |
| 56 | Event text | Timing not provided by CORE for this risk; see the headline. | CORE ने इस जोखिम का समय नहीं दिया है; मुख्य वाक्य देखें। |  |
| 57 | Event text | Model agreement: not assessed | मॉडलों की सहमति: आकलन नहीं |  |
| 58 | Weekday | Mon | सोम |  |
| 59 | Weekday | Tue | मंगल |  |
| 60 | Weekday | Wed | बुध |  |
| 61 | Weekday | Thu | गुरु |  |
| 62 | Weekday | Fri | शुक्र |  |
| 63 | Weekday | Sat | शनि |  |
| 64 | Weekday | Sun | रवि |  |
| 65 | Month | Jan | जन॰ |  |
| 66 | Month | Feb | फ़र॰ |  |
| 67 | Month | Mar | मार्च |  |
| 68 | Month | Apr | अप्रैल |  |
| 69 | Month | May | मई |  |
| 70 | Month | Jun | जून |  |
| 71 | Month | Jul | जुल॰ |  |
| 72 | Month | Aug | अग॰ |  |
| 73 | Month | Sep | सित॰ |  |
| 74 | Month | Oct | अक्टू॰ |  |
| 75 | Month | Nov | नव॰ |  |
| 76 | Month | Dec | दिस॰ |  |

### 4c. Farmer home — CORE weather words (36 strings)

| # | Kind | English | Shown | OK? |
| --- | --- | --- | --- | --- |
| 1 | Word | Max temperature | अधिकतम तापमान |  |
| 2 | Word | Min temperature | न्यूनतम तापमान |  |
| 3 | Word | Max temperature (7-day mean) | अधिकतम तापमान (7 दिन का औसत) |  |
| 4 | Word | Rainfall | वर्षा |  |
| 5 | Word | Today | आज |  |
| 6 | Word | Next 7 days | अगले 7 दिन |  |
| 7 | Word | Next 7 days (forecast) | अगले 7 दिन (पूर्वानुमान) |  |
| 8 | Word | Past 30 days (model analysis) | पिछले 30 दिन (मॉडल विश्लेषण) |  |
| 9 | Word | Above normal | सामान्य से अधिक |  |
| 10 | Word | Below normal | सामान्य से कम |  |
| 11 | Word | Near normal | लगभग सामान्य |  |
| 12 | Word | Large excess | बहुत अधिक |  |
| 13 | Word | Excess | अधिक |  |
| 14 | Word | Normal | सामान्य |  |
| 15 | Word | Deficient | कम |  |
| 16 | Word | Large deficient | बहुत कम |  |
| 17 | Word | No rain | वर्षा नहीं |  |
| 18 | Word | Dry season | शुष्क मौसम |  |
| 19 | Word | Rain in dry season | शुष्क मौसम में वर्षा |  |
| 20 | Word | Open-Meteo best-match (model analysis, not a station observation) | Open-Meteo best-match (मॉडल विश्लेषण, मौसम केंद्र का अवलोकन नहीं) |  |
| 21 | Word | plains | मैदानी क्षेत्र |  |
| 22 | Word | coastal | तटीय क्षेत्र |  |
| 23 | Word | hills | पहाड़ी क्षेत्र |  |
| 24 | Word | Clear | साफ़ आसमान |  |
| 25 | Word | Partly cloudy | आंशिक बादल |  |
| 26 | Word | Overcast | घने बादल |  |
| 27 | Word | Fog | कोहरा |  |
| 28 | Word | Drizzle | बूँदाबाँदी |  |
| 29 | Word | Rain | बारिश |  |
| 30 | Word | Heavy rain | भारी बारिश |  |
| 31 | Word | Snow | बर्फ़बारी |  |
| 32 | Word | Showers | बौछारें |  |
| 33 | Word | Violent showers | बहुत तेज़ बौछारें |  |
| 34 | Word | Thunderstorm | गरज-चमक के साथ तूफ़ान |  |
| 35 | Word | Thunderstorm with hail | ओलों के साथ गरज-चमक और तूफ़ान |  |
| 36 | Word | No significant weather event detected. | कोई महत्वपूर्ण मौसम घटना नहीं मिली। |  |

### 4d. Screen labels written by V2 (72 strings)

| # | Key | English | Shown | OK? |
| --- | --- | --- | --- | --- |
| 1 | wtk_title | What should you know? | आपको क्या जानना चाहिए? |  |
| 2 | feels | Feels like | महसूस होने वाला तापमान |  |
| 3 | rain_now | Rain now | अभी वर्षा |  |
| 4 | humidity | Humidity | आर्द्रता |  |
| 5 | wind | Wind | हवा |  |
| 6 | gusts | gusts | झोंके |  |
| 7 | pressure | Pressure | वायुदाब |  |
| 8 | cloud | Cloud | बादल |  |
| 9 | visibility | Visibility | दृश्यता |  |
| 10 | u_mm | mm | मिमी |  |
| 11 | u_kmh | km/h | किमी/घंटा |  |
| 12 | u_km | km | किमी |  |
| 13 | as_of | As of | समय: |  |
| 14 | point_note | point forecast at model-grid resolution | मॉडल-ग्रिड के एक बिंदु का पूर्वानुमान |  |
| 15 | wtk_summary | 1 official alert · 2 system assessments at Watch or above (…) · next 7 days | 1 आधिकारिक चेतावनी · 2 सिस्टम आकलन 'नज़र रखें' या उससे ऊपर के स्तर पर (…) · अगले 7 दिन |  |
| 16 | sev_names | Severe / Alert / Watch | गंभीर / सावधान / नज़र रखें |  |
| 17 | none_detail | No official alert for this location and no CORE risk at Watch level or above in the next 7 days. | इस स्थान के लिए कोई आधिकारिक चेतावनी नहीं है और अगले 7 दिनों में CORE का कोई जोखिम 'नज़र रखें' या उससे ऊपर के स्तर पर नहीं है। |  |
| 18 | official_alert | Official alert | आधिकारिक चेतावनी |  |
| 19 | more_official | +3 more official alerts | +3 और आधिकारिक चेतावनियाँ |  |
| 20 | system_note | CORE risk rules · next 7 days · not official warnings | CORE के जोखिम नियम · अगले 7 दिन · आधिकारिक चेतावनी नहीं |  |
| 21 | show_more | Show 3 more system assessments | 3 और सिस्टम आकलन दिखाएँ |  |
| 22 | dep_title | Departure from normal | सामान्य से अंतर |  |
| 23 | dep_sub | · not a hazard on its own | · अपने-आप में खतरा नहीं |  |
| 24 | forecast | forecast | पूर्वानुमान |  |
| 25 | normal | normal | सामान्य |  |
| 26 | normal_note | Normal: NASA POWER 1991–2020 (MERRA-2 reanalysis), indicative — not IMD normals. | सामान्य: NASA POWER 1991–2020 (MERRA-2 रीएनालिसिस), अनुमानित — IMD के सामान्य आँकड़े नहीं। |  |
| 27 | v2_down | The V2 event service is unavailable. CORE's own risk list is still under Risks & alerts. | V2 घटना सेवा अभी उपलब्ध नहीं है। CORE की अपनी जोखिम सूची 'Risks & alerts' में है। |  |
| 28 | system_label | System assessment | सिस्टम आकलन |  |
| 29 | lang_switch | Language | भाषा |  |
| 30 | field_title | Your field — location, crop, growth stage | आपका खेत — स्थान, फसल, फसल की अवस्था |  |
| 31 | loc_state | 1 · Location — state | 1 · स्थान — राज्य |  |
| 32 | loc_district | 1 · Location — district | 1 · स्थान — ज़िला |  |
| 33 | sel_state | Select state | राज्य चुनें |  |
| 34 | sel_district | Select district | ज़िला चुनें |  |
| 35 | crop | 2 · Crop | 2 · फसल |  |
| 36 | sel_crop | Select crop | फसल चुनें |  |
| 37 | stage | 3 · Growth stage | 3 · फसल की अवस्था |  |
| 38 | sel_stage | Select stage | अवस्था चुनें |  |
| 39 | field_location | Field location: | खेत का स्थान: |  |
| 40 | field_help | For a village, use the location search at the top; the forecast is a point forecast at model-grid resolution. | गाँव के लिए ऊपर की स्थान-खोज का उपयोग करें; पूर्वानुमान मॉडल-ग्रिड के एक बिंदु के लिए है। |  |
| 41 | official_later | The official agricultural advisory is shown separately in step 7. | आधिकारिक कृषि सलाह चरण 7 में अलग से दिखाई गई है। |  |
| 42 | choose_prompt | Choose a crop and growth stage to see weather indicators for your field. | अपने खेत के मौसम संकेतक देखने के लिए फसल और फसल की अवस्था चुनें। |  |
| 43 | weather_title | 4 · Weather — next days at your field | 4 · मौसम — आपके खेत पर आने वाले दिन |  |
| 44 | th_day | Day | दिन |  |
| 45 | th_temp | Max / min °C | अधिकतम / न्यूनतम °C |  |
| 46 | th_rain | Rain mm | वर्षा मिमी |  |
| 47 | th_chance | Chance | संभावना |  |
| 48 | th_spray | Spray-suitable hours* | छिड़काव के लिए उपयुक्त घंटे* |  |
| 49 | th_disease | Disease-favourable hours* | रोग के अनुकूल घंटे* |  |
| 50 | weather_note | Forecast values from CORE. *Spray and disease hours are system-derived, unvalidated indicators from CORE's thresholds. | पूर्वानुमान के आँकड़े CORE से। *छिड़काव और रोग के घंटे CORE की सीमाओं से निकाले गए सिस्टम-आधारित, बिना सत्यापित संकेतक हैं। |  |
| 51 | ind_title | 5 · System indicators | 5 · सिस्टम संकेतक |  |
| 52 | badge_system | System-derived | सिस्टम-आधारित |  |
| 53 | badge_unvalidated | Unvalidated | सत्यापित नहीं |  |
| 54 | core_status | CORE status: | CORE स्थिति: |  |
| 55 | rule | Rule: | नियम: |  |
| 56 | rule_suffix | system-derived, unvalidated | सिस्टम-आधारित, सत्यापित नहीं |  |
| 57 | rel_title | 6 · Potential crop relevance — weather events | 6 · फसल पर संभावित असर — मौसम की घटनाएँ |  |
| 58 | rel_head | Potential crop relevance | फसल पर संभावित असर |  |
| 59 | rel_none | No significant weather event detected for this field in CORE's 7-day assessment. | CORE के 7 दिन के आकलन में इस खेत के लिए कोई महत्वपूर्ण मौसम घटना नहीं मिली। |  |
| 60 | rel_uses | Existing CORE indicators for Cotton (…) that use …: | कपास (…) के लिए CORE के मौजूदा संकेतक, जो … पर आधारित हैं: |  |
| 61 | rel_no_ind | No existing CORE crop indicator for Cotton at this stage uses this signal. V2 does not add agronomic rules. | इस अवस्था में कपास के लिए CORE का कोई संकेतक इस संकेत का उपयोग नहीं करता। V2 खेती के नए नियम नहीं जोड़ता। |  |
| 62 | rel_official | Official advisory: … — step 7 below. | आधिकारिक सलाह: … — नीचे चरण 7। |  |
| 63 | off_head | 7 · Official agricultural advisory | 7 · आधिकारिक कृषि सलाह |  |
| 64 | off_sep | Steps 5 and 6 are system output, not an official agricultural advisory. For farm decisions, follow the official advisory. | चरण 5 और 6 सिस्टम का परिणाम हैं, आधिकारिक कृषि सलाह नहीं। खेती के निर्णयों के लिए आधिकारिक सलाह का पालन करें। |  |
| 65 | alerts_title | Official weather alerts for this area | इस क्षेत्र के लिए आधिकारिक मौसम चेतावनियाँ |  |
| 66 | alerts_note | — | आधिकारिक चेतावनियाँ जारी की गई भाषा में ही दिखाई गई हैं; उनका अनुवाद नहीं किया जाता। |  |
| 67 | english_kept | — | अंग्रेज़ी में (अनुवाद उपलब्ध नहीं) |  |
| 68 | signal | daily maximum temperature | दैनिक अधिकतम तापमान |  |
| 69 | signal | daily minimum temperature | दैनिक न्यूनतम तापमान |  |
| 70 | signal | daily rainfall | दैनिक वर्षा |  |
| 71 | signal | consecutive dry days | लगातार सूखे दिन |  |
| 72 | event card | When: / Experimental / Potential relevance · context / View evidence | कब: / प्रायोगिक / संभावित प्रासंगिकता · सामान्य संदर्भ, असर का पूर्वानुमान नहीं / प्रमाण देखें (अंग्रेज़ी में) |  |

