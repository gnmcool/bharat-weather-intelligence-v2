// Farmer site (#/kisan) wording in Gujarati, Hindi and English. Every Gujarati and Hindi string needs
// native-speaker review before wide release (docs/KISAN.md lists them). No imports: tested with Node.
import type { KLang, Likelihood, RainClass } from "./rules";

type Rain = Record<RainClass, string>;

export interface KText {
  chooseLang: string;
  pickPlace: string;
  useLocation: string;
  locating: string;
  locationFailed: string;
  orPick: string;
  searchPh: string;
  state: string;
  noMatch: string;
  change: string;
  langShort: string;
  langLabel: string;
  today: string;
  next3: string;
  dry: string;
  smallChance: string;
  chance: (p: number) => string;
  rainOf: Rain; // "{class} rain"
  likely: Record<Exclude<Likelihood, "unlikely">, string>;
  amount: (mm: string) => string;
  maxMin: (max: string, min: string) => string;
  heavyNote: string;
  warnOwn: string;
  warnState: (n: number) => string;
  showAll: string;
  severity: Record<string, string>;
  until: (when: string) => string;
  issuedBy: (who: string) => string;
  original: string;
  hideOriginal: string;
  noWarning: string;
  notSure: string;
  kcc: string;
  more: string;
  updated: (when: string) => string;
  stale: string;
  loading: string;
  failed: string;
  retry: string;
  noDays: string;
  attribution: string;
  events: Record<string, string>;
}

const rainGu: Rain = { none: "", veryLight: "ઝરમર", light: "હળવો વરસાદ", moderate: "મધ્યમ વરસાદ", heavy: "ભારે વરસાદ", veryHeavy: "અતિ ભારે વરસાદ", extreme: "અત્યંત ભારે વરસાદ" };
const rainHi: Rain = { none: "", veryLight: "बूँदाबाँदी", light: "हल्की बारिश", moderate: "मध्यम बारिश", heavy: "भारी बारिश", veryHeavy: "बहुत भारी बारिश", extreme: "अत्यंत भारी बारिश" };
const rainEn: Rain = { none: "", veryLight: "Drizzle", light: "Light rain", moderate: "Moderate rain", heavy: "Heavy rain", veryHeavy: "Very heavy rain", extreme: "Extremely heavy rain" };

export const K: Record<KLang, KText> = {
  gu: {
    chooseLang: "ભાષા પસંદ કરો",
    pickPlace: "તમારો જિલ્લો પસંદ કરો",
    useLocation: "મારું સ્થાન વાપરો",
    locating: "સ્થાન શોધાય છે…",
    locationFailed: "સ્થાન મળ્યું નહીં. નીચેથી જિલ્લો પસંદ કરો.",
    orPick: "અથવા જિલ્લો પસંદ કરો",
    searchPh: "જિલ્લાનું નામ લખો",
    state: "રાજ્ય",
    noMatch: "આ નામનો જિલ્લો મળ્યો નહીં",
    change: "બદલો",
    langShort: "ભાષા",
    langLabel: "ભાષા બદલો",
    today: "આજે",
    next3: "આવતા 3 દિવસ",
    dry: "વરસાદ નથી",
    smallChance: "વરસાદની થોડી શક્યતા",
    chance: (p) => `શક્યતા ${p}%`,
    rainOf: rainGu,
    likely: { possible: "શક્ય", likely: "સંભવ" },
    amount: (mm) => `${mm} મિમી`,
    maxMin: (a, b) => `મહત્તમ ${a}° · લઘુત્તમ ${b}°`,
    heavyNote: "ભારે વરસાદની આગાહી ઘણી વાર ખોટી પડે છે. IMD ની ચેતવણી જુઓ.",
    warnOwn: "તમારા જિલ્લા માટે સત્તાવાર ચેતવણી",
    warnState: (n) => (n === 1 ? "રાજ્યના બીજા જિલ્લામાં 1 સત્તાવાર ચેતવણી" : `રાજ્યના બીજા જિલ્લાઓમાં ${n} સત્તાવાર ચેતવણીઓ`),
    showAll: "બધી બતાવો",
    severity: { Extreme: "અતિ ગંભીર", Severe: "ગંભીર", Moderate: "મધ્યમ", Minor: "હળવી" },
    until: (w) => `${w} સુધી`,
    issuedBy: (who) => `જારીકર્તા: ${who}`,
    original: "મૂળ સંદેશ (અંગ્રેજીમાં)",
    hideOriginal: "મૂળ સંદેશ છુપાવો",
    noWarning: "તમારા જિલ્લા માટે કોઈ સત્તાવાર ચેતવણી નથી",
    notSure: "આ આગાહી છે, ખાતરી નથી.",
    kcc: "ખેતીની સલાહ, મફત કૉલ:",
    more: "વધુ વિગત જુઓ",
    updated: (w) => `અપડેટ: ${w}`,
    stale: "આ આગાહી જૂની છે. થોડી વાર પછી ફરી ખોલો.",
    loading: "હવામાન લાવી રહ્યા છીએ…",
    failed: "હવામાન મળ્યું નહીં. ઇન્ટરનેટ તપાસીને ફરી પ્રયાસ કરો.",
    retry: "ફરી પ્રયાસ કરો",
    noDays: "આજની આગાહી હજી ઉપલબ્ધ નથી.",
    attribution: "હવામાન ડેટા: Open-Meteo.com (CC BY 4.0) · ચેતવણીઓ: IMD, CWC, SDMA (NDMA SACHET)",
    events: {
      extremelyHeavyRain: "અત્યંત ભારે વરસાદ", veryHeavyRain: "અતિ ભારે વરસાદ", heavyRain: "ભારે વરસાદ", moderateRain: "મધ્યમ વરસાદ",
      lightRain: "હળવો વરસાદ", rain: "વરસાદ", thunderShower: "ગાજવીજ સાથે ઝાપટાં", thunderstorm: "ગાજવીજ સાથે વાવાઝોડું",
      lightning: "વીજળી પડવાનું જોખમ", squall: "તોફાની પવન", strongWind: "તેજ પવન", hail: "કરા પડવાની શક્યતા", dustStorm: "ધૂળની આંધી",
      flashFlood: "અચાનક પૂર", flood: "પૂર", cloudburst: "વાદળ ફાટવું", landslide: "ભૂસ્ખલન", heatWave: "લૂ (હીટવેવ)",
      coldWave: "શીતલહેર", fog: "ગાઢ ધુમ્મસ", cyclone: "વાવાઝોડું (ચક્રવાત)",
    },
  },
  hi: {
    chooseLang: "भाषा चुनें",
    pickPlace: "अपना ज़िला चुनें",
    useLocation: "मेरी जगह का उपयोग करें",
    locating: "जगह खोजी जा रही है…",
    locationFailed: "जगह नहीं मिली। नीचे से ज़िला चुनें।",
    orPick: "या ज़िला चुनें",
    searchPh: "ज़िले का नाम लिखें",
    state: "राज्य",
    noMatch: "इस नाम का ज़िला नहीं मिला",
    change: "बदलें",
    langShort: "भाषा",
    langLabel: "भाषा बदलें",
    today: "आज",
    next3: "अगले 3 दिन",
    dry: "बारिश नहीं",
    smallChance: "बारिश की थोड़ी संभावना",
    chance: (p) => `संभावना ${p}%`,
    rainOf: rainHi,
    likely: { possible: "संभव", likely: "की उम्मीद" },
    amount: (mm) => `${mm} मिमी`,
    maxMin: (a, b) => `अधिकतम ${a}° · न्यूनतम ${b}°`,
    heavyNote: "भारी बारिश का पूर्वानुमान अक्सर गलत होता है। IMD की चेतावनी देखें।",
    warnOwn: "आपके ज़िले के लिए आधिकारिक चेतावनी",
    warnState: (n) => (n === 1 ? "राज्य के दूसरे ज़िले में 1 आधिकारिक चेतावनी" : `राज्य के दूसरे ज़िलों में ${n} आधिकारिक चेतावनियाँ`),
    showAll: "सभी दिखाएँ",
    severity: { Extreme: "अत्यंत गंभीर", Severe: "गंभीर", Moderate: "मध्यम", Minor: "हल्की" },
    until: (w) => `${w} तक`,
    issuedBy: (who) => `जारीकर्ता: ${who}`,
    original: "मूल संदेश (अंग्रेज़ी में)",
    hideOriginal: "मूल संदेश छिपाएँ",
    noWarning: "आपके ज़िले के लिए कोई आधिकारिक चेतावनी नहीं",
    notSure: "यह पूर्वानुमान है, पक्का नहीं।",
    kcc: "खेती की सलाह, मुफ़्त कॉल:",
    more: "और जानकारी देखें",
    updated: (w) => `अपडेट: ${w}`,
    stale: "यह पूर्वानुमान पुराना है। थोड़ी देर बाद फिर खोलें।",
    loading: "मौसम लाया जा रहा है…",
    failed: "मौसम नहीं मिला। इंटरनेट जाँचकर फिर कोशिश करें।",
    retry: "फिर कोशिश करें",
    noDays: "आज का पूर्वानुमान अभी उपलब्ध नहीं है।",
    attribution: "मौसम डेटा: Open-Meteo.com (CC BY 4.0) · चेतावनियाँ: IMD, CWC, SDMA (NDMA SACHET)",
    events: {
      extremelyHeavyRain: "अत्यंत भारी बारिश", veryHeavyRain: "बहुत भारी बारिश", heavyRain: "भारी बारिश", moderateRain: "मध्यम बारिश",
      lightRain: "हल्की बारिश", rain: "बारिश", thunderShower: "गरज के साथ बौछारें", thunderstorm: "गरज-चमक के साथ तूफ़ान",
      lightning: "बिजली गिरने का खतरा", squall: "तूफ़ानी हवाएँ", strongWind: "तेज़ हवा", hail: "ओले गिरने की संभावना", dustStorm: "धूल भरी आँधी",
      flashFlood: "अचानक बाढ़", flood: "बाढ़", cloudburst: "बादल फटना", landslide: "भूस्खलन", heatWave: "लू (हीटवेव)",
      coldWave: "शीतलहर", fog: "घना कोहरा", cyclone: "चक्रवात",
    },
  },
  en: {
    chooseLang: "Choose your language",
    pickPlace: "Choose your district",
    useLocation: "Use my location",
    locating: "Finding your location…",
    locationFailed: "Could not find your location. Choose your district below.",
    orPick: "Or choose your district",
    searchPh: "Type a district name",
    state: "State",
    noMatch: "No district with that name",
    change: "Change",
    langShort: "Language",
    langLabel: "Change language",
    today: "Today",
    next3: "Next 3 days",
    dry: "No rain",
    smallChance: "Small chance of rain",
    chance: (p) => `Chance ${p}%`,
    rainOf: rainEn,
    likely: { possible: "possible", likely: "likely" },
    amount: (mm) => `${mm} mm`,
    maxMin: (a, b) => `Max ${a}° · Min ${b}°`,
    heavyNote: "Heavy-rain forecasts are often wrong. Check the IMD warning.",
    warnOwn: "Official warning for your district",
    warnState: (n) => (n === 1 ? "1 official warning elsewhere in your state" : `${n} official warnings elsewhere in your state`),
    showAll: "Show all",
    severity: { Extreme: "Extreme", Severe: "Severe", Moderate: "Moderate", Minor: "Minor" },
    until: (w) => `until ${w}`,
    issuedBy: (who) => `Issued by ${who}`,
    original: "Original message",
    hideOriginal: "Hide original message",
    noWarning: "No official warning for your district",
    notSure: "This is a forecast, not a certainty.",
    kcc: "Farm advice, free call:",
    more: "See more detail",
    updated: (w) => `Updated ${w}`,
    stale: "This forecast is old. Open again in a while.",
    loading: "Getting the weather…",
    failed: "Could not get the weather. Check your internet and try again.",
    retry: "Try again",
    noDays: "Today's forecast is not available yet.",
    attribution: "Weather data by Open-Meteo.com (CC BY 4.0) · Warnings: IMD, CWC, SDMA (NDMA SACHET)",
    events: {
      extremelyHeavyRain: "Extremely heavy rain", veryHeavyRain: "Very heavy rain", heavyRain: "Heavy rain", moderateRain: "Moderate rain",
      lightRain: "Light rain", rain: "Rain", thunderShower: "Thunder showers", thunderstorm: "Thunderstorm",
      lightning: "Lightning", squall: "Squall", strongWind: "Strong wind", hail: "Hail", dustStorm: "Dust storm",
      flashFlood: "Flash flood", flood: "Flood", cloudburst: "Cloudburst", landslide: "Landslide", heatWave: "Heat wave",
      coldWave: "Cold wave", fog: "Dense fog", cyclone: "Cyclone",
    },
  },
};

/** Gujarat's districts as CORE names them (geo/states/gujarat/districts), in Gujarati and Hindi. Other states keep
 *  CORE's English names for now. */
export const GUJARAT_DISTRICTS: Record<string, { gu: string; hi: string }> = {
  Ahmedabad: { gu: "અમદાવાદ", hi: "अहमदाबाद" }, Amreli: { gu: "અમરેલી", hi: "अमरेली" }, Anand: { gu: "આણંદ", hi: "आणंद" },
  Aravalli: { gu: "અરવલ્લી", hi: "अरवल्ली" }, Banaskantha: { gu: "બનાસકાંઠા", hi: "बनासकांठा" }, Bharuch: { gu: "ભરૂચ", hi: "भरूच" },
  Bhavnagar: { gu: "ભાવનગર", hi: "भावनगर" }, Botad: { gu: "બોટાદ", hi: "बोटाद" }, "Chhota Udaipur": { gu: "છોટા ઉદેપુર", hi: "छोटा उदयपुर" },
  Dahod: { gu: "દાહોદ", hi: "दाहोद" }, Dang: { gu: "ડાંગ", hi: "डांग" }, "Devbhumi Dwarka": { gu: "દેવભૂમિ દ્વારકા", hi: "देवभूमि द्वारका" },
  Gandhinagar: { gu: "ગાંધીનગર", hi: "गांधीनगर" }, "Gir Somnath": { gu: "ગીર સોમનાથ", hi: "गिर सोमनाथ" }, Jamnagar: { gu: "જામનગર", hi: "जामनगर" },
  Junagadh: { gu: "જૂનાગઢ", hi: "जूनागढ़" }, Kheda: { gu: "ખેડા", hi: "खेड़ा" }, Kutch: { gu: "કચ્છ", hi: "कच्छ" },
  Mahisagar: { gu: "મહીસાગર", hi: "महीसागर" }, Mehsana: { gu: "મહેસાણા", hi: "मेहसाणा" }, Morbi: { gu: "મોરબી", hi: "मोरबी" },
  Narmada: { gu: "નર્મદા", hi: "नर्मदा" }, Navsari: { gu: "નવસારી", hi: "नवसारी" }, Panchmahal: { gu: "પંચમહાલ", hi: "पंचमहल" },
  Patan: { gu: "પાટણ", hi: "पाटण" }, Porbandar: { gu: "પોરબંદર", hi: "पोरबंदर" }, Rajkot: { gu: "રાજકોટ", hi: "राजकोट" },
  Sabarkantha: { gu: "સાબરકાંઠા", hi: "साबरकांठा" }, Surat: { gu: "સુરત", hi: "सूरत" }, Surendranagar: { gu: "સુરેન્દ્રનગર", hi: "सुरेंद्रनगर" },
  Tapi: { gu: "તાપી", hi: "तापी" }, Vadodara: { gu: "વડોદરા", hi: "वडोदरा" }, Valsad: { gu: "વલસાડ", hi: "वलसाड" },
  "Vav-Tharad": { gu: "વાવ-થરાદ", hi: "वाव-थराद" },
};
export const STATE_NAMES: Record<string, { gu: string; hi: string }> = { Gujarat: { gu: "ગુજરાત", hi: "गुजरात" } };

export const districtName = (english: string, lang: KLang) => (lang === "en" ? english : GUJARAT_DISTRICTS[english]?.[lang] ?? english);
export const stateName = (english: string, lang: KLang) => (lang === "en" ? english : STATE_NAMES[english]?.[lang] ?? english);

/** Date/time locale: native month and weekday names, Western digits. */
export const kLocale = (l: KLang) => (l === "gu" ? "gu-IN-u-nu-latn" : l === "hi" ? "hi-IN-u-nu-latn" : "en-IN");
