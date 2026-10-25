# Farmer site (`#/kisan`)

A separate, simple page for farmers: <https://gnmcool.github.io/bharat-weather-intelligence-v2/#/kisan>.
The detailed site (Citizen, Farmer, Government) is unchanged and is linked from the bottom of the page.

| Item | Value |
| --- | --- |
| Status | built on `feature/kisan`; private preview; **not live** until the owner approves |
| Code | `web/src/kisan/` (`KisanApp.tsx` screens, `rules.ts` rain and warning rules, `strings.ts` wording), route in `web/src/main.tsx` |
| Data | CORE public API only: `/dashboard` (daily rain, chance, temperature, official warnings), `/geo/states`, `/geo/states/{state}/districts`. No new weather rules |
| Tests | `web/test/kisan.test.ts` (in `npm test` and CI); the daily live check also reports any official warning type without Gujarati/Hindi wording |

## Screens
1. **Language** on first visit: ગુજરાતી · हिन्दी · English (remembered on the phone).
2. **District**: "use my location", or a state (Gujarat first) and a district list with search.
3. **Weather**: today's rain in one card, the next three days as tiles, then official warnings; the free Kisan Call
   Centre number; a link to the detailed site. A normal day fits one phone screen.

## Rules (`rules.ts`)
- **Rain amount words** are IMD's 24-hour classes: very light 0.1–2.4 mm, light 2.5–15.5, moderate 15.6–64.4,
  heavy 64.5–115.5, very heavy 115.6–204.4, extremely heavy ≥ 204.5.
- **Chance** is CORE's daily maximum precipitation probability: below 30 % unlikely, 30–59 % possible, 60 % and over
  likely. A day reads "no rain" only when both amount and chance are low; amount without chance, or chance without
  amount, reads "small chance of rain". Heavy rain is never shown when the chance is below 30 %.
- **Heavy rain** carries a fixed caution ("heavy-rain forecasts are often wrong; check the IMD warning"), because
  verification (M4.4-B) found the models catch about a quarter of heavy-rain days a day ahead.
- **Official warnings** (IMD, CWC, SDMAs via NDMA SACHET, as CORE attaches them):
  - expired ones and national-only ones are not shown;
  - warnings for the farmer's own district come first, in full; warnings elsewhere in the state are one collapsed line;
  - the warning **type** (a fixed vocabulary: heavy rain, lightning, flood, squall…) and the expiry time are shown in
    the farmer's language; the issuer's **original message** is one tap away, unchanged. An unknown type is shown in
    the issuer's English. Free text is never machine-translated.
- **Old data**: a note appears when CORE's forecast is more than six hours old.

## Wording for native-speaker review (105 strings)
| # | Key | English | Gujarati | Hindi |
| --- | --- | --- | --- | --- |
| 1 | chooseLang | Choose your language | ભાષા પસંદ કરો | भाषा चुनें |
| 2 | pickPlace | Choose your district | તમારો જિલ્લો પસંદ કરો | अपना ज़िला चुनें |
| 3 | useLocation | Use my location | મારું સ્થાન વાપરો | मेरी जगह का उपयोग करें |
| 4 | locating | Finding your location… | સ્થાન શોધાય છે… | जगह खोजी जा रही है… |
| 5 | locationFailed | Could not find your location. Choose your district below. | સ્થાન મળ્યું નહીં. નીચેથી જિલ્લો પસંદ કરો. | जगह नहीं मिली। नीचे से ज़िला चुनें। |
| 6 | orPick | Or choose your district | અથવા જિલ્લો પસંદ કરો | या ज़िला चुनें |
| 7 | searchPh | Type a district name | જિલ્લાનું નામ લખો | ज़िले का नाम लिखें |
| 8 | state | State | રાજ્ય | राज्य |
| 9 | noMatch | No district with that name | આ નામનો જિલ્લો મળ્યો નહીં | इस नाम का ज़िला नहीं मिला |
| 10 | change | Change | બદલો | बदलें |
| 11 | langShort | Language | ભાષા | भाषा |
| 12 | langLabel | Change language | ભાષા બદલો | भाषा बदलें |
| 13 | today | Today | આજે | आज |
| 14 | next3 | Next 3 days | આવતા 3 દિવસ | अगले 3 दिन |
| 15 | dry | No rain | વરસાદ નથી | बारिश नहीं |
| 16 | smallChance | Small chance of rain | વરસાદની થોડી શક્યતા | बारिश की थोड़ी संभावना |
| 17 | chance | Chance 70% | શક્યતા 70% | संभावना 70% |
| 18 | rainOf.veryLight | Drizzle | ઝરમર | बूँदाबाँदी |
| 19 | rainOf.light | Light rain | હળવો વરસાદ | हल्की बारिश |
| 20 | rainOf.moderate | Moderate rain | મધ્યમ વરસાદ | मध्यम बारिश |
| 21 | rainOf.heavy | Heavy rain | ભારે વરસાદ | भारी बारिश |
| 22 | rainOf.veryHeavy | Very heavy rain | અતિ ભારે વરસાદ | बहुत भारी बारिश |
| 23 | rainOf.extreme | Extremely heavy rain | અત્યંત ભારે વરસાદ | अत्यंत भारी बारिश |
| 24 | likely.possible | possible | શક્ય | संभव |
| 25 | likely.likely | likely | સંભવ | की उम्मीद |
| 26 | amount | 12 mm | 12 મિમી | 12 मिमी |
| 27 | maxMin | Max 36° · Min 23° | મહત્તમ 36° · લઘુત્તમ 23° | अधिकतम 36° · न्यूनतम 23° |
| 28 | heavyNote | Heavy-rain forecasts are often wrong. Check the IMD warning. | ભારે વરસાદની આગાહી ઘણી વાર ખોટી પડે છે. IMD ની ચેતવણી જુઓ. | भारी बारिश का पूर्वानुमान अक्सर गलत होता है। IMD की चेतावनी देखें। |
| 29 | warnOwn | Official warning for your district | તમારા જિલ્લા માટે સત્તાવાર ચેતવણી | आपके ज़िले के लिए आधिकारिक चेतावनी |
| 30 | warnState | 3 official warnings elsewhere in your state | રાજ્યના બીજા જિલ્લાઓમાં 3 સત્તાવાર ચેતવણીઓ | राज्य के दूसरे ज़िलों में 3 आधिकारिक चेतावनियाँ |
| 31 | showAll | Show all | બધી બતાવો | सभी दिखाएँ |
| 32 | severity.Extreme | Extreme | અતિ ગંભીર | अत्यंत गंभीर |
| 33 | severity.Severe | Severe | ગંભીર | गंभीर |
| 34 | severity.Moderate | Moderate | મધ્યમ | मध्यम |
| 35 | severity.Minor | Minor | હળવી | हल्की |
| 36 | until | until 25 Oct, 6:00 pm | 25 Oct, 6:00 pm સુધી | 25 Oct, 6:00 pm तक |
| 37 | issuedBy | Issued by IMD Ahmedabad | જારીકર્તા: IMD Ahmedabad | जारीकर्ता: IMD Ahmedabad |
| 38 | original | Original message | મૂળ સંદેશ (અંગ્રેજીમાં) | मूल संदेश (अंग्रेज़ी में) |
| 39 | hideOriginal | Hide original message | મૂળ સંદેશ છુપાવો | मूल संदेश छिपाएँ |
| 40 | noWarning | No official warning for your district | તમારા જિલ્લા માટે કોઈ સત્તાવાર ચેતવણી નથી | आपके ज़िले के लिए कोई आधिकारिक चेतावनी नहीं |
| 41 | notSure | This is a forecast, not a certainty. | આ આગાહી છે, ખાતરી નથી. | यह पूर्वानुमान है, पक्का नहीं। |
| 42 | kcc | Farm advice, free call: | ખેતીની સલાહ, મફત કૉલ: | खेती की सलाह, मुफ़्त कॉल: |
| 43 | more | See more detail | વધુ વિગત જુઓ | और जानकारी देखें |
| 44 | updated | Updated 25 Oct, 3:15 pm | અપડેટ: 25 Oct, 3:15 pm | अपडेट: 25 Oct, 3:15 pm |
| 45 | stale | This forecast is old. Open again in a while. | આ આગાહી જૂની છે. થોડી વાર પછી ફરી ખોલો. | यह पूर्वानुमान पुराना है। थोड़ी देर बाद फिर खोलें। |
| 46 | loading | Getting the weather… | હવામાન લાવી રહ્યા છીએ… | मौसम लाया जा रहा है… |
| 47 | failed | Could not get the weather. Check your internet and try again. | હવામાન મળ્યું નહીં. ઇન્ટરનેટ તપાસીને ફરી પ્રયાસ કરો. | मौसम नहीं मिला। इंटरनेट जाँचकर फिर कोशिश करें। |
| 48 | retry | Try again | ફરી પ્રયાસ કરો | फिर कोशिश करें |
| 49 | noDays | Today's forecast is not available yet. | આજની આગાહી હજી ઉપલબ્ધ નથી. | आज का पूर्वानुमान अभी उपलब्ध नहीं है। |
| 50 | attribution | Weather data by Open-Meteo.com (CC BY 4.0) · Warnings: IMD, CWC, SDMA (NDMA SACHET) | હવામાન ડેટા: Open-Meteo.com (CC BY 4.0) · ચેતવણીઓ: IMD, CWC, SDMA (NDMA SACHET) | मौसम डेटा: Open-Meteo.com (CC BY 4.0) · चेतावनियाँ: IMD, CWC, SDMA (NDMA SACHET) |
| 51 | events.extremelyHeavyRain | Extremely heavy rain | અત્યંત ભારે વરસાદ | अत्यंत भारी बारिश |
| 52 | events.veryHeavyRain | Very heavy rain | અતિ ભારે વરસાદ | बहुत भारी बारिश |
| 53 | events.heavyRain | Heavy rain | ભારે વરસાદ | भारी बारिश |
| 54 | events.moderateRain | Moderate rain | મધ્યમ વરસાદ | मध्यम बारिश |
| 55 | events.lightRain | Light rain | હળવો વરસાદ | हल्की बारिश |
| 56 | events.rain | Rain | વરસાદ | बारिश |
| 57 | events.thunderShower | Thunder showers | ગાજવીજ સાથે ઝાપટાં | गरज के साथ बौछारें |
| 58 | events.thunderstorm | Thunderstorm | ગાજવીજ સાથે વાવાઝોડું | गरज-चमक के साथ तूफ़ान |
| 59 | events.lightning | Lightning | વીજળી પડવાનું જોખમ | बिजली गिरने का खतरा |
| 60 | events.squall | Squall | તોફાની પવન | तूफ़ानी हवाएँ |
| 61 | events.strongWind | Strong wind | તેજ પવન | तेज़ हवा |
| 62 | events.hail | Hail | કરા પડવાની શક્યતા | ओले गिरने की संभावना |
| 63 | events.dustStorm | Dust storm | ધૂળની આંધી | धूल भरी आँधी |
| 64 | events.flashFlood | Flash flood | અચાનક પૂર | अचानक बाढ़ |
| 65 | events.flood | Flood | પૂર | बाढ़ |
| 66 | events.cloudburst | Cloudburst | વાદળ ફાટવું | बादल फटना |
| 67 | events.landslide | Landslide | ભૂસ્ખલન | भूस्खलन |
| 68 | events.heatWave | Heat wave | લૂ (હીટવેવ) | लू (हीटवेव) |
| 69 | events.coldWave | Cold wave | શીતલહેર | शीतलहर |
| 70 | events.fog | Dense fog | ગાઢ ધુમ્મસ | घना कोहरा |
| 71 | events.cyclone | Cyclone | વાવાઝોડું (ચક્રવાત) | चक्रवात |
| 72 | district | Ahmedabad | અમદાવાદ | अहमदाबाद |
| 73 | district | Amreli | અમરેલી | अमरेली |
| 74 | district | Anand | આણંદ | आणंद |
| 75 | district | Aravalli | અરવલ્લી | अरवल्ली |
| 76 | district | Banaskantha | બનાસકાંઠા | बनासकांठा |
| 77 | district | Bharuch | ભરૂચ | भरूच |
| 78 | district | Bhavnagar | ભાવનગર | भावनगर |
| 79 | district | Botad | બોટાદ | बोटाद |
| 80 | district | Chhota Udaipur | છોટા ઉદેપુર | छोटा उदयपुर |
| 81 | district | Dahod | દાહોદ | दाहोद |
| 82 | district | Dang | ડાંગ | डांग |
| 83 | district | Devbhumi Dwarka | દેવભૂમિ દ્વારકા | देवभूमि द्वारका |
| 84 | district | Gandhinagar | ગાંધીનગર | गांधीनगर |
| 85 | district | Gir Somnath | ગીર સોમનાથ | गिर सोमनाथ |
| 86 | district | Jamnagar | જામનગર | जामनगर |
| 87 | district | Junagadh | જૂનાગઢ | जूनागढ़ |
| 88 | district | Kheda | ખેડા | खेड़ा |
| 89 | district | Kutch | કચ્છ | कच्छ |
| 90 | district | Mahisagar | મહીસાગર | महीसागर |
| 91 | district | Mehsana | મહેસાણા | मेहसाणा |
| 92 | district | Morbi | મોરબી | मोरबी |
| 93 | district | Narmada | નર્મદા | नर्मदा |
| 94 | district | Navsari | નવસારી | नवसारी |
| 95 | district | Panchmahal | પંચમહાલ | पंचमहल |
| 96 | district | Patan | પાટણ | पाटण |
| 97 | district | Porbandar | પોરબંદર | पोरबंदर |
| 98 | district | Rajkot | રાજકોટ | राजकोट |
| 99 | district | Sabarkantha | સાબરકાંઠા | साबरकांठा |
| 100 | district | Surat | સુરત | सूरत |
| 101 | district | Surendranagar | સુરેન્દ્રનગર | सुरेंद्रनगर |
| 102 | district | Tapi | તાપી | तापी |
| 103 | district | Vadodara | વડોદરા | वडोदरा |
| 104 | district | Valsad | વલસાડ | वलसाड |
| 105 | district | Vav-Tharad | વાવ-થરાદ | वाव-थराद |
