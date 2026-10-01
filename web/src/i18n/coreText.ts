// Gujarati and Hindi rendering of CORE text on the farmer screens (CORE 2840f8d: backend/app/engines/farmer.py,
// crops.yaml, risk.py, anomaly.py) and of V2's event text (api-v2 catalogue).
//
// Rules (docs/FARMER_GUJARATI.md, docs/FARMER_HINDI.md):
//  - Presentation only. Levels, numbers and thresholds come from CORE unchanged; nothing is computed here.
//  - CORE sends finished English sentences. Each one is matched against CORE's fixed sentence patterns; numbers are
//    copied from the English text into the translated template. A sentence that does not match exactly is shown in
//    English (never guessed). So a future CORE wording change shows up as English, not as a wrong translation.
//  - Official text (IMD warnings, advisory links' targets) is never altered.
//  - Every translated string needs native-speaker review before release (review list in the docs).
//
// This file has no imports so it can be tested directly with Node (web/test/coreText.test.ts).

export type Lang = "en" | "gu" | "hi";
/** Languages with translations. */
export type TL = "gu" | "hi";
export const TLS: readonly TL[] = ["gu", "hi"];
type ByLang<T> = Record<TL, T>;

/** A rendered string plus whether it is translated (false = CORE's English shown as is). */
export interface Out {
  text: string;
  tr: boolean;
}
const en = (text: string): Out => ({ text, tr: false });
const tr = (text: string): Out => ({ text, tr: true });
const isTL = (l: Lang): l is TL => l !== "en";

// ── Fixed vocabulary ─────────────────────────────────────────────────────────

export const LEVEL_NAMES: ByLang<readonly string[]> = {
  gu: ["જોખમ નથી", "નજર રાખો", "સાવધાન", "ગંભીર"],
  hi: ["जोखिम नहीं", "नज़र रखें", "सावधान", "गंभीर"],
};
/** Level name for CORE's 0–3 level in the given language (English names come from present.ts). */
export const levelName = (level: number, lang: Lang): string | undefined => (isTL(lang) ? LEVEL_NAMES[lang][level] : undefined);

/** crops.yaml crop id → name. */
export const CROPS: ByLang<Record<string, string>> = {
  gu: { wheat: "ઘઉં", paddy: "ડાંગર", cotton: "કપાસ", groundnut: "મગફળી", castor: "દિવેલા (એરંડા)", bajra: "બાજરી", cumin: "જીરું", mustard: "રાયડો" },
  hi: { wheat: "गेहूँ", paddy: "धान", cotton: "कपास", groundnut: "मूँगफली", castor: "अरंडी", bajra: "बाजरा", cumin: "जीरा", mustard: "सरसों" },
};

/** crops.yaml season strings. */
export const SEASONS: ByLang<Record<string, string>> = {
  gu: { Rabi: "રવિ", Kharif: "ખરીફ", "Kharif / Summer": "ખરીફ / ઉનાળુ" },
  hi: { Rabi: "रबी", Kharif: "खरीफ़", "Kharif / Summer": "खरीफ़ / ज़ायद" },
};

/** crops.yaml stage ids. */
export const STAGES: ByLang<Record<string, string>> = {
  gu: {
    sowing: "વાવણી", nursery: "ધરુવાડિયું", transplanting: "ફેરરોપણી", vegetative: "વાનસ્પતિક વૃદ્ધિ",
    squaring: "ચાપવા અવસ્થા", flowering: "ફૂલ અવસ્થા", pegging: "સૂયા અવસ્થા", pod_fill: "શીંગ ભરાવાની અવસ્થા",
    grain_fill: "દાણા ભરાવાની અવસ્થા", boll_development: "જીંડવા વિકાસ", capsule_development: "ડોડવા વિકાસ",
    seed_development: "બીજ વિકાસ", harvest: "કાપણી",
  },
  hi: {
    sowing: "बुवाई", nursery: "नर्सरी (पौधशाला)", transplanting: "रोपाई", vegetative: "वानस्पतिक वृद्धि",
    squaring: "कली बनने की अवस्था", flowering: "फूल अवस्था", pegging: "खूँटी (पेग) बनने की अवस्था", pod_fill: "फली भराव",
    grain_fill: "दाना भराव", boll_development: "टिंडा विकास", capsule_development: "डोडा (कैप्सूल) विकास",
    seed_development: "बीज विकास", harvest: "कटाई",
  },
};

const stageEn = (s: string) => s.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());
const pickTL = (dict: ByLang<Record<string, string>>, key: string, lang: Lang, english: string): Out =>
  isTL(lang) && dict[lang][key] ? tr(dict[lang][key]) : en(english);

export const cropName = (id: string, english: string, lang: Lang): Out => pickTL(CROPS, id, lang, english);
export const seasonName = (s: string, lang: Lang): Out => pickTL(SEASONS, s, lang, s);
export const stageName = (s: string, lang: Lang): Out => pickTL(STAGES, s, lang, stageEn(s));
/** CORE writes the stage inside rule text as stage.replace("_", " "), e.g. "grain fill". */
const stageFromRule = (s: string, l: TL): string | undefined => STAGES[l][s.replace(/ /g, "_")];

// ── Patterns ─────────────────────────────────────────────────────────────────

const N = "(\\d+(?:\\.\\d+)?)"; // a number as CORE prints it; copied verbatim, never reformatted

type Build = (m: RegExpMatchArray) => string | undefined;
interface Pattern {
  re: RegExp;
  out: ByLang<Build>;
}
const P = (src: string, gu: Build, hi: Build): Pattern => ({ re: new RegExp(`^${src}$`), out: { gu, hi } });

function match(patterns: Pattern[] | undefined, s: string, l: TL): string | undefined {
  for (const p of patterns ?? []) {
    const m = s.match(p.re);
    if (m) return p.out[l](m);
  }
  return undefined;
}

// ── Indicators (farmer.py `ind.append(...)`) ──────────────────────────────────

const LABEL: Record<string, Record<string, ByLang<string>>> = {
  heat_stress: { "Heat stress for this stage": { gu: "આ અવસ્થામાં ગરમીનો તણાવ", hi: "इस अवस्था में गर्मी का तनाव" } },
  cold_stress: { "Cold / frost stress": { gu: "ઠંડી / હિમનો તણાવ", hi: "ठंड / पाले का तनाव" } },
  heavy_rain: { "Heavy rain": { gu: "ભારે વરસાદ", hi: "भारी वर्षा" } },
  dry_spell: { "Dry spell": { gu: "વરસાદ વગરનો ગાળો", hi: "सूखा अंतराल" } },
  harvest_window: { "Dry harvest window": { gu: "કાપણી માટે કોરો ગાળો", hi: "कटाई के लिए सूखी अवधि" } },
  disease_weather: { "Disease-favourable weather": { gu: "રોગને અનુકૂળ હવામાન", hi: "रोग के अनुकूल मौसम" } },
};

const VALUE: Record<string, Pattern[]> = {
  heat_stress: [P(`${N} of 7 days ≥ ${N} °C`, (m) => `7 માંથી ${m[1]} દિવસ ≥ ${m[2]} °C`, (m) => `7 में से ${m[1]} दिन ≥ ${m[2]} °C`)],
  cold_stress: [P(`${N} of 7 nights ≤ ${N} °C`, (m) => `7 માંથી ${m[1]} રાત ≤ ${m[2]} °C`, (m) => `7 में से ${m[1]} रातें ≤ ${m[2]} °C`)],
  heavy_rain: [P(`max ${N} mm/day`, (m) => `મહત્તમ ${m[1]} મિમી/દિવસ`, (m) => `अधिकतम ${m[1]} मिमी/दिन`)],
  dry_spell: [P(`${N} days`, (m) => `${m[1]} દિવસ`, (m) => `${m[1]} दिन`)],
  harvest_window: [P(`longest dry run ${N} days`, (m) => `સૌથી લાંબો કોરો ગાળો ${m[1]} દિવસ`, (m) => `सबसे लंबी सूखी अवधि ${m[1]} दिन`)],
  disease_weather: [
    P(`${N} humid hours \\(RH ≥ ${N}%, ${N}–${N} °C\\)`,
      (m) => `${m[1]} ભેજવાળા કલાક (ભેજ ≥ ${m[2]}%, ${m[3]}–${m[4]} °C)`,
      (m) => `${m[1]} नम घंटे (आर्द्रता ≥ ${m[2]}%, ${m[3]}–${m[4]} °C)`),
  ],
};

const RULE: Record<string, Pattern[]> = {
  heat_stress: [
    P(`Tmax ≥ ${N} °C at ([a-z ]+)`,
      (m) => (stageFromRule(m[2], "gu") ? `${stageFromRule(m[2], "gu")} વખતે મહત્તમ તાપમાન ≥ ${m[1]} °C` : undefined),
      (m) => (stageFromRule(m[2], "hi") ? `${stageFromRule(m[2], "hi")} पर अधिकतम तापमान ≥ ${m[1]} °C` : undefined)),
  ],
  cold_stress: [
    P(`Tmin ≤ ${N} °C at ([a-z ]+)`,
      (m) => (stageFromRule(m[2], "gu") ? `${stageFromRule(m[2], "gu")} વખતે લઘુત્તમ તાપમાન ≤ ${m[1]} °C` : undefined),
      (m) => (stageFromRule(m[2], "hi") ? `${stageFromRule(m[2], "hi")} पर न्यूनतम तापमान ≤ ${m[1]} °C` : undefined)),
  ],
  heavy_rain: [
    P(`IMD heavy rain ≥ ${N} mm/day \\(Watch ≥ ${N}\\)`,
      (m) => `IMD મુજબ ભારે વરસાદ ≥ ${m[1]} મિમી/દિવસ (નજર રાખો ≥ ${m[2]})`,
      (m) => `IMD के अनुसार भारी वर्षा ≥ ${m[1]} मिमी/दिन (नज़र रखें ≥ ${m[2]})`),
  ],
  dry_spell: [
    P(`Consecutive days < ${N} mm`,
      (m) => `સળંગ દિવસો, દરેક દિવસે ${m[1]} મિમી કરતાં ઓછો વરસાદ`,
      (m) => `लगातार दिन, हर दिन ${m[1]} मिमी से कम वर्षा`),
  ],
  harvest_window: [
    P(`days < ${N} mm & rain prob < ${N}%`,
      (m) => `દિવસો: વરસાદ < ${m[1]} મિમી અને વરસાદની શક્યતા < ${m[2]}%`,
      (m) => `दिन: वर्षा < ${m[1]} मिमी और वर्षा की संभावना < ${m[2]}%`),
  ],
  disease_weather: [
    P(`Leaf-wetness proxy; stage-sensitive for this crop`,
      () => "પાનની ભીનાશનો અંદાજ; આ પાક માટે આ અવસ્થા સંવેદનશીલ છે",
      () => "पत्ती के गीलेपन का अनुमान; इस फसल के लिए यह अवस्था संवेदनशील है"),
    P(`Leaf-wetness proxy`, () => "પાનની ભીનાશનો અંદાજ", () => "पत्ती के गीलेपन का अनुमान"),
  ],
};

export interface IndicatorIn {
  id: string;
  label: string;
  value: string;
  rule: string;
}
export interface IndicatorOut {
  label: Out;
  value: Out;
  rule: Out;
}

/** Render one CORE indicator. Each field falls back to CORE's English independently. */
export function indicatorText(i: IndicatorIn, lang: Lang): IndicatorOut {
  if (!isTL(lang)) return { label: en(i.label), value: en(i.value), rule: en(i.rule) };
  const pick = (t: string | undefined, eng: string) => (t ? tr(t) : en(eng));
  return {
    label: pick(LABEL[i.id]?.[i.label]?.[lang], i.label),
    value: pick(match(VALUE[i.id], i.value, lang), i.value),
    rule: pick(match(RULE[i.id], i.rule, lang), i.rule),
  };
}

// ── Fixed CORE text: exact-match only ────────────────────────────────────────

export const EXACT: Record<string, ByLang<string>> = {
  // farmer.py disclaimer
  "SYSTEM-DERIVED WEATHER INDICATORS — computed automatically from forecast models using unvalidated thresholds. They are not farming instructions. Follow the official Agromet Advisory for decisions.": {
    gu: "સિસ્ટમ-આધારિત હવામાન સૂચકાંકો — ફોરકાસ્ટ મોડેલોમાંથી, ચકાસણી ન થયેલી મર્યાદાઓ (થ્રેશોલ્ડ) વડે આપમેળે ગણાયેલા. આ ખેતી માટેની સૂચના નથી. નિર્ણય માટે સત્તાવાર કૃષિ-હવામાન સલાહ (Agromet Advisory) અનુસરો.",
    hi: "सिस्टम-आधारित मौसम संकेतक — पूर्वानुमान मॉडलों से, बिना सत्यापित सीमाओं (थ्रेशोल्ड) के आधार पर अपने-आप गणना किए गए। ये खेती के निर्देश नहीं हैं। निर्णय के लिए आधिकारिक कृषि-मौसम सलाह (Agromet Advisory) का पालन करें।",
  },
  // farmer.py OFFICIAL_ADVISORY
  "Official Agromet Advisory (IMD × ICAR — Gramin Krishi Mausam Sewa)": {
    gu: "સત્તાવાર કૃષિ-હવામાન સલાહ (IMD × ICAR — ગ્રામીણ કૃષિ મૌસમ સેવા)",
    hi: "आधिकारिक कृषि-मौसम सलाह (IMD × ICAR — ग्रामीण कृषि मौसम सेवा)",
  },
  "District Agromet Advisory Service bulletins are issued every Tuesday and Friday by IMD with State Agricultural Universities / KVKs. They are the authoritative source for farm operations.": {
    gu: "જિલ્લા કૃષિ-હવામાન સલાહ સેવાના બુલેટિન IMD દ્વારા રાજ્ય કૃષિ યુનિવર્સિટીઓ / KVK સાથે મળીને દર મંગળવારે અને શુક્રવારે બહાર પડે છે. ખેતીના કામ માટે એ જ અધિકૃત સ્ત્રોત છે.",
    hi: "ज़िला कृषि-मौसम सलाह सेवा के बुलेटिन IMD द्वारा राज्य कृषि विश्वविद्यालयों / KVK के साथ मिलकर हर मंगलवार और शुक्रवार को जारी किए जाते हैं। खेती के कामों के लिए यही प्रामाणिक स्रोत है।",
  },
  "Not yet ingested automatically — requires IMD Agromet data access (see docs/ARCHITECTURE.md).": {
    gu: "આ સલાહ હજી આપમેળે અહીં લાવવામાં આવતી નથી — તે માટે IMD કૃષિ-હવામાન ડેટાની પરવાનગી જરૂરી છે.",
    hi: "यह सलाह अभी अपने-आप यहाँ नहीं लाई जाती — इसके लिए IMD कृषि-मौसम डेटा की अनुमति ज़रूरी है।",
  },
  "IMD — Agromet services": { gu: "IMD — કૃષિ-હવામાન સેવાઓ", hi: "IMD — कृषि-मौसम सेवाएँ" },
  "Meghdoot app (IMD/ICAR/IITM) — district advisories": { gu: "મેઘદૂત એપ (IMD/ICAR/IITM) — જિલ્લાની સલાહ", hi: "मेघदूत ऐप (IMD/ICAR/IITM) — ज़िला सलाह" },
  "Kisan Call Centre — 1800-180-1551": { gu: "કિસાન કોલ સેન્ટર — 1800-180-1551", hi: "किसान कॉल सेंटर — 1800-180-1551" },
  // crops.yaml notes
  "Terminal heat after anthesis shortens grain filling (Porter & Gawith 1999 review of wheat temperature responses).": {
    gu: "ફૂલ આવ્યા પછીની ગરમી દાણા ભરાવાનો સમય ટૂંકો કરે છે (Porter & Gawith 1999, ઘઉં પર તાપમાનની અસરની સમીક્ષા).",
    hi: "फूल आने के बाद की गर्मी दाना भरने का समय घटा देती है (Porter & Gawith 1999, गेहूँ पर तापमान के प्रभाव की समीक्षा)।",
  },
  "Temperatures above ~35 °C at anthesis increase spikelet sterility (Jagadish et al. 2007).": {
    gu: "ફૂલ અવસ્થાએ આશરે 35 °C થી વધુ તાપમાનથી દાણા ખાલી રહેવાનું (વંધ્યતા) વધે છે (Jagadish et al. 2007).",
    hi: "फूल अवस्था में लगभग 35 °C से अधिक तापमान से दाने खाली रहने (बंध्यता) की समस्या बढ़ती है (Jagadish et al. 2007)।",
  },
  "High heat at flowering raises square and boll shedding; validate local thresholds.": {
    gu: "ફૂલ અવસ્થાએ વધુ ગરમીથી ચાપવા અને જીંડવા ખરવાનું વધે છે; સ્થાનિક મર્યાદાઓની ચકાસણી જરૂરી છે.",
    hi: "फूल अवस्था में अधिक गर्मी से कलियों और टिंडों का झड़ना बढ़ता है; स्थानीय सीमाओं का सत्यापन ज़रूरी है।",
  },
  "Heat stress at flowering/pegging reduces pod set.": {
    gu: "ફૂલ/સૂયા અવસ્થાએ ગરમીનો તણાવ શીંગ બેસવાનું ઘટાડે છે.",
    hi: "फूल/खूँटी अवस्था में गर्मी का तनाव फलियाँ बनना घटाता है।",
  },
  "Relatively heat tolerant; cold nights slow spike development.": {
    gu: "ગરમી પ્રમાણમાં સહન કરે છે; ઠંડી રાતો માળ (સ્પાઇક) ના વિકાસને ધીમો પાડે છે.",
    hi: "गर्मी अपेक्षाकृत सह लेती है; ठंडी रातें बाली (स्पाइक) के विकास को धीमा करती हैं।",
  },
  "Heat tolerant; very high temperature at flowering reduces seed set.": {
    gu: "ગરમી સહન કરે છે; ફૂલ અવસ્થાએ ખૂબ ઊંચું તાપમાન દાણા બેસવાનું ઘટાડે છે.",
    hi: "गर्मी सहनशील; फूल अवस्था में बहुत अधिक तापमान दाने बनना घटाता है।",
  },
  "Cloudy, humid spells at flowering favour blight (Alternaria) — a major Gujarat concern.": {
    gu: "ફૂલ અવસ્થાએ વાદળછાયું, ભેજવાળું હવામાન ચરમી (Alternaria blight) ને અનુકૂળ છે — ગુજરાતમાં મોટી સમસ્યા.",
    hi: "फूल अवस्था में बादल और नमी वाला मौसम झुलसा रोग (Alternaria blight) के अनुकूल है — गुजरात में बड़ी समस्या।",
  },
  "Frost at flowering/pod fill damages pods; cloudy humid weather favours aphids.": {
    gu: "ફૂલ/શીંગ ભરાવાની અવસ્થાએ હિમ શીંગોને નુકસાન કરે છે; વાદળછાયું ભેજવાળું હવામાન મોલો-મશી (એફિડ) ને અનુકૂળ છે.",
    hi: "फूल/फली भराव अवस्था में पाला फलियों को नुकसान पहुँचाता है; बादल और नमी वाला मौसम माहू (एफिड) के अनुकूल है।",
  },
  // crops.yaml validation_status
  unvalidated: { gu: "ચકાસણી બાકી", hi: "सत्यापन बाकी" },
  // CORE anomaly.py labels, periods and categories (farmer home, "Departure from normal")
  "Max temperature": { gu: "મહત્તમ તાપમાન", hi: "अधिकतम तापमान" },
  "Min temperature": { gu: "લઘુત્તમ તાપમાન", hi: "न्यूनतम तापमान" },
  "Max temperature (7-day mean)": { gu: "મહત્તમ તાપમાન (7 દિવસની સરેરાશ)", hi: "अधिकतम तापमान (7 दिन का औसत)" },
  Rainfall: { gu: "વરસાદ", hi: "वर्षा" },
  Today: { gu: "આજે", hi: "आज" },
  "Next 7 days": { gu: "આવતા 7 દિવસ", hi: "अगले 7 दिन" },
  "Next 7 days (forecast)": { gu: "આવતા 7 દિવસ (આગાહી)", hi: "अगले 7 दिन (पूर्वानुमान)" },
  "Past 30 days (model analysis)": { gu: "છેલ્લા 30 દિવસ (મોડેલ વિશ્લેષણ)", hi: "पिछले 30 दिन (मॉडल विश्लेषण)" },
  "Above normal": { gu: "સામાન્યથી વધુ", hi: "सामान्य से अधिक" },
  "Below normal": { gu: "સામાન્યથી ઓછું", hi: "सामान्य से कम" },
  "Near normal": { gu: "લગભગ સામાન્ય", hi: "लगभग सामान्य" },
  "Large excess": { gu: "ઘણો વધુ", hi: "बहुत अधिक" },
  Excess: { gu: "વધુ", hi: "अधिक" },
  Normal: { gu: "સામાન્ય", hi: "सामान्य" },
  Deficient: { gu: "ઓછો", hi: "कम" },
  "Large deficient": { gu: "ઘણો ઓછો", hi: "बहुत कम" },
  "No rain": { gu: "વરસાદ નહીં", hi: "वर्षा नहीं" },
  "Dry season": { gu: "સૂકી ઋતુ", hi: "शुष्क मौसम" },
  "Rain in dry season": { gu: "સૂકી ઋતુમાં વરસાદ", hi: "शुष्क मौसम में वर्षा" },
  // CORE current-conditions fields (services.py source, terrain.py classes)
  "Open-Meteo best-match (model analysis, not a station observation)": {
    gu: "Open-Meteo best-match (મોડેલ વિશ્લેષણ, હવામાન મથકનું અવલોકન નથી)",
    hi: "Open-Meteo best-match (मॉडल विश्लेषण, मौसम केंद्र का अवलोकन नहीं)",
  },
  plains: { gu: "મેદાની વિસ્તાર", hi: "मैदानी क्षेत्र" },
  coastal: { gu: "દરિયાકાંઠો", hi: "तटीय क्षेत्र" },
  hills: { gu: "પહાડી વિસ્તાર", hi: "पहाड़ी क्षेत्र" },
  // V2 format.wmoText (WMO 4677 groups)
  Clear: { gu: "ચોખ્ખું આકાશ", hi: "साफ़ आसमान" },
  "Partly cloudy": { gu: "આંશિક વાદળછાયું", hi: "आंशिक बादल" },
  Overcast: { gu: "ઘેરાં વાદળ", hi: "घने बादल" },
  Fog: { gu: "ધુમ્મસ", hi: "कोहरा" },
  Drizzle: { gu: "ઝરમર", hi: "बूँदाबाँदी" },
  Rain: { gu: "વરસાદ", hi: "बारिश" },
  "Heavy rain": { gu: "ભારે વરસાદ", hi: "भारी बारिश" },
  Snow: { gu: "હિમવર્ષા", hi: "बर्फ़बारी" },
  Showers: { gu: "ઝાપટાં", hi: "बौछारें" },
  "Violent showers": { gu: "ખૂબ ભારે ઝાપટાં", hi: "बहुत तेज़ बौछारें" },
  Thunderstorm: { gu: "ગાજવીજ સાથે વાવાઝોડું", hi: "गरज-चमक के साथ तूफ़ान" },
  "Thunderstorm with hail": { gu: "કરા સાથે ગાજવીજ અને વાવાઝોડું", hi: "ओलों के साथ गरज-चमक और तूफ़ान" },
  // V2 api-v2 events.py what_to_know.message
  "No significant weather event detected.": { gu: "કોઈ મહત્ત્વની હવામાન ઘટના મળી નથી.", hi: "कोई महत्वपूर्ण मौसम घटना नहीं मिली।" },
};

/** Fixed CORE text, translated only on an exact match; otherwise CORE's English. */
export function coreText(s: string | null | undefined, lang: Lang): Out {
  const v = s ?? "";
  return isTL(lang) && EXACT[v] ? tr(EXACT[v][lang]) : en(v);
}

// ── Weather-event cards (V2 /api/v2/events over CORE risks; CORE 2840f8d risk.py headlines) ─────────────────

export const WEEKDAYS: ByLang<Record<string, string>> = {
  gu: { Mon: "સોમ", Tue: "મંગળ", Wed: "બુધ", Thu: "ગુરુ", Fri: "શુક્ર", Sat: "શનિ", Sun: "રવિ" },
  hi: { Mon: "सोम", Tue: "मंगल", Wed: "बुध", Thu: "गुरु", Fri: "शुक्र", Sat: "शनि", Sun: "रवि" },
};
export const MONTHS: ByLang<Record<string, string>> = {
  gu: { Jan: "જાન્યુ", Feb: "ફેબ્રુ", Mar: "માર્ચ", Apr: "એપ્રિલ", May: "મે", Jun: "જૂન", Jul: "જુલાઈ", Aug: "ઑગસ્ટ", Sep: "સપ્ટે", Oct: "ઑક્ટો", Nov: "નવે", Dec: "ડિસે" },
  // Same abbreviations as the browser's hi-IN dates (Intl), so headline and "When" lines match.
  hi: { Jan: "जन॰", Feb: "फ़र॰", Mar: "मार्च", Apr: "अप्रैल", May: "मई", Jun: "जून", Jul: "जुल॰", Aug: "अग॰", Sep: "सित॰", Oct: "अक्टू॰", Nov: "नव॰", Dec: "दिस॰" },
};
const REL_DAY: ByLang<{ today: string; tomorrow: string }> = { gu: { today: "આજે", tomorrow: "આવતીકાલે" }, hi: { today: "आज", tomorrow: "कल" } };

const WDS = Object.keys(WEEKDAYS.gu).join("|");
const MOS = Object.keys(MONTHS.gu).join("|");
/** CORE _fmt_day: "today" | "tomorrow" | "Sat 03 Oct". */
const DAY = `(today|tomorrow|(?:${WDS}) \\d{2} (?:${MOS}))`;
const dayT = (s: string, l: TL) =>
  s === "today" || s === "tomorrow"
    ? REL_DAY[l][s]
    : s.replace(/^(\w{3}) (\d{2}) (\w{3})$/, (_, w, d, m) => `${WEEKDAYS[l][w]} ${d} ${MONTHS[l][m]}`);
/** CORE thunderstorm time: "Thu 1 Oct, 2 PM". AM/PM kept as written (review item). */
const WHEN = `((?:${WDS}) \\d{1,2} (?:${MOS}), \\d{1,2} (?:AM|PM))`;
const whenT = (s: string, l: TL) => s.replace(/^(\w{3}) (\d{1,2}) (\w{3}), /, (_, w, d, m) => `${WEEKDAYS[l][w]} ${d} ${MONTHS[l][m]}, `);
/** CORE fog time: "Thu 02 AM". */
const HOUR = `((?:${WDS}) \\d{2} (?:AM|PM))`;
const hourT = (s: string, l: TL) => s.replace(/^(\w{3}) /, (_, w) => `${WEEKDAYS[l][w]} `);

const HEAT: Record<string, ByLang<string>> = {
  "Heat watch": { gu: "ગરમી પર નજર રાખો", hi: "गर्मी पर नज़र रखें" },
  "Heat-wave conditions": { gu: "હીટવેવ (લૂ) ની સ્થિતિ", hi: "लू (हीटवेव) की स्थिति" },
  "Severe heat-wave conditions": { gu: "ગંભીર હીટવેવ (લૂ) ની સ્થિતિ", hi: "गंभीर लू (हीटवेव) की स्थिति" },
};
const COLD: Record<string, ByLang<string>> = {
  "Cold watch": { gu: "ઠંડી પર નજર રાખો", hi: "ठंड पर नज़र रखें" },
  "Cold-wave conditions": { gu: "શીતલહેરની સ્થિતિ", hi: "शीतलहर की स्थिति" },
  "Severe cold wave": { gu: "ગંભીર શીતલહેર", hi: "गंभीर शीतलहर" },
};
const RAIN_CAT: Record<string, ByLang<string>> = {
  "Very light": { gu: "ખૂબ હળવો", hi: "बहुत हल्की" },
  Light: { gu: "હળવો", hi: "हल्की" },
  Moderate: { gu: "મધ્યમ", hi: "मध्यम" },
  "Rather heavy": { gu: "સાધારણ ભારે", hi: "कुछ भारी" },
  Heavy: { gu: "ભારે", hi: "भारी" },
  "Very heavy": { gu: "અતિ ભારે", hi: "बहुत भारी" },
  "Extremely heavy": { gu: "અત્યંત ભારે", hi: "अत्यंत भारी" },
};
const DEP_CAT: Record<string, ByLang<string>> = {
  "Large excess": { gu: "ઘણો વધુ", hi: "बहुत अधिक" },
  Excess: { gu: "વધુ", hi: "अधिक" },
  Normal: { gu: "સામાન્ય", hi: "सामान्य" },
  Deficient: { gu: "ઓછો", hi: "कम" },
  "Large deficient": { gu: "ઘણો ઓછો", hi: "बहुत कम" },
  "No rain": { gu: "વરસાદ નહીં", hi: "वर्षा नहीं" },
};
const alt = (o: Record<string, unknown>) => Object.keys(o).map((k) => k.replace(/[-]/g, "\\-")).join("|");

const HEADLINE: Record<string, Pattern[]> = {
  heat: [P(`(${alt(HEAT)}) ${DAY}`, (m) => `${dayT(m[2], "gu")} ${HEAT[m[1]].gu}`, (m) => `${dayT(m[2], "hi")} ${HEAT[m[1]].hi}`)],
  cold: [P(`(${alt(COLD)}) ${DAY}`, (m) => `${dayT(m[2], "gu")} ${COLD[m[1]].gu}`, (m) => `${dayT(m[2], "hi")} ${COLD[m[1]].hi}`)],
  rain: [
    P(`(${alt(RAIN_CAT)}) rain ${DAY} \\(${N} mm\\)`,
      (m) => `${dayT(m[2], "gu")} ${RAIN_CAT[m[1]].gu} વરસાદ (${m[3]} મિમી)`,
      (m) => `${dayT(m[2], "hi")} ${RAIN_CAT[m[1]].hi} वर्षा (${m[3]} मिमी)`),
  ],
  wind: [
    P(`Gusts up to ${N} km/h ${DAY}`,
      (m) => `${dayT(m[2], "gu")} ${m[1]} કિમી/કલાક સુધીના પવનના ઝાટકા`,
      (m) => `${dayT(m[2], "hi")} ${m[1]} किमी/घंटा तक के हवा के झोंके`),
    P(`Gusts up to ${N} km/h`, (m) => `${m[1]} કિમી/કલાક સુધીના પવનના ઝાટકા`, (m) => `${m[1]} किमी/घंटा तक के हवा के झोंके`),
  ],
  thunderstorm: [
    P(`Thunderstorm likely from ${WHEN}`,
      (m) => `${whenT(m[1], "gu")} થી ગાજવીજ સાથે વાવાઝોડાની વધુ શક્યતા`,
      (m) => `${whenT(m[1], "hi")} से गरज-चमक के साथ तूफ़ान की अधिक संभावना`),
    P(`Thunderstorm possible from ${WHEN}`,
      (m) => `${whenT(m[1], "gu")} થી ગાજવીજ સાથે વાવાઝોડાની શક્યતા`,
      (m) => `${whenT(m[1], "hi")} से गरज-चमक के साथ तूफ़ान की संभावना`),
  ],
  lightning: [
    P(`Lightning risk high from ${WHEN}`,
      (m) => `${whenT(m[1], "gu")} થી વીજળી પડવાનું વધુ જોખમ`,
      (m) => `${whenT(m[1], "hi")} से बिजली गिरने का अधिक खतरा`),
    P(`Lightning risk present from ${WHEN}`,
      (m) => `${whenT(m[1], "gu")} થી વીજળી પડવાનું જોખમ`,
      (m) => `${whenT(m[1], "hi")} से बिजली गिरने का खतरा`),
  ],
  flood: [
    P(`72-h rain up to ${N} mm \\(incl\\. past 2 days\\) — flooding possible`,
      (m) => `72 કલાકમાં ${m[1]} મિમી સુધી વરસાદ (છેલ્લા 2 દિવસ સહિત) — પૂર શક્ય`,
      (m) => `72 घंटों में ${m[1]} मिमी तक वर्षा (पिछले 2 दिन सहित) — बाढ़ संभव`),
    P(`72-h rain up to ${N} mm \\(incl\\. past 2 days\\)`,
      (m) => `72 કલાકમાં ${m[1]} મિમી સુધી વરસાદ (છેલ્લા 2 દિવસ સહિત)`,
      (m) => `72 घंटों में ${m[1]} मिमी तक वर्षा (पिछले 2 दिन सहित)`),
  ],
  drought: [
    P(`Last 30 days: ${N} mm vs normal ${N} mm \\(([+-]\\d+)%, (${alt(DEP_CAT)})\\)`,
      (m) => `છેલ્લા 30 દિવસ: ${m[1]} મિમી, સામાન્ય ${m[2]} મિમી (${m[3]}%, ${DEP_CAT[m[4]].gu})`,
      (m) => `पिछले 30 दिन: ${m[1]} मिमी, सामान्य ${m[2]} मिमी (${m[3]}%, ${DEP_CAT[m[4]].hi})`),
  ],
  fog: [
    P(`Visibility down to ${N} m around ${HOUR}`,
      (m) => `${hourT(m[2], "gu")} આસપાસ દૃશ્યતા ઘટીને ${m[1]} મીટર`,
      (m) => `${hourT(m[2], "hi")} के आसपास दृश्यता घटकर ${m[1]} मीटर`),
  ],
  fire: [P(`Hot, dry and windy spells ahead`, () => "આગળના દિવસોમાં ગરમ, સૂકા અને પવનવાળા ગાળા", () => "आगे गर्म, सूखे और तेज़ हवा वाले दौर")],
};

/** V2 event titles (api-v2 catalogue.TITLE), keyed by event type and checked against the English. */
export const EVENT_TITLE: Record<string, { en: string } & ByLang<string>> = {
  heat: { en: "Heat", gu: "ગરમી", hi: "गर्मी" },
  cold: { en: "Cold", gu: "ઠંડી", hi: "ठंड" },
  rain: { en: "Heavy rain", gu: "ભારે વરસાદ", hi: "भारी वर्षा" },
  wind: { en: "Strong wind", gu: "તેજ પવન", hi: "तेज़ हवा" },
  thunderstorm: { en: "Thunderstorm potential — model derived", gu: "ગાજવીજ સાથે વાવાઝોડાની સંભાવના — મોડેલ આધારિત", hi: "गरज-चमक के साथ तूफ़ान की संभावना — मॉडल आधारित" },
  lightning: { en: "Lightning potential — model derived", gu: "વીજળી પડવાની સંભાવના — મોડેલ આધારિત", hi: "बिजली गिरने की संभावना — मॉडल आधारित" },
  flood: { en: "Flood-related risk (rainfall accumulation)", gu: "પૂર સંબંધિત જોખમ (એકઠો થયેલો વરસાદ)", hi: "बाढ़ से जुड़ा जोखिम (जमा हुई वर्षा)" },
  drought: { en: "Dry spell / rainfall deficit", gu: "વરસાદ વગરનો ગાળો / વરસાદની ઘટ", hi: "सूखा अंतराल / वर्षा की कमी" },
  fog: { en: "Fog", gu: "ધુમ્મસ", hi: "कोहरा" },
  fire: { en: "Fire weather", gu: "આગ માટે અનુકૂળ હવામાન", hi: "आग के अनुकूल मौसम" },
};

/** V2 farmer context (api-v2 catalogue.CONTEXT[...][1]) and fixed event-card text; exact match only. */
export const EVENT_EXACT: Record<string, ByLang<string>> = {
  "Heat during this period may be relevant to field work and to crops at heat-sensitive stages.": {
    gu: "આ સમયગાળાની ગરમી ખેતરના કામ અને ગરમી પ્રત્યે સંવેદનશીલ અવસ્થાના પાક માટે મહત્ત્વની હોઈ શકે.",
    hi: "इस अवधि की गर्मी खेत के काम और गर्मी के प्रति संवेदनशील अवस्था वाली फसलों के लिए महत्वपूर्ण हो सकती है।",
  },
  "Low night temperatures during this period may be relevant to crops at cold-sensitive stages.": {
    gu: "આ સમયગાળાનું રાત્રિનું નીચું તાપમાન ઠંડી પ્રત્યે સંવેદનશીલ અવસ્થાના પાક માટે મહત્ત્વનું હોઈ શકે.",
    hi: "इस अवधि में रात का कम तापमान ठंड के प्रति संवेदनशील अवस्था वाली फसलों के लिए महत्वपूर्ण हो सकता है।",
  },
  "Rain during this period may affect field operations.": {
    gu: "આ સમયગાળાનો વરસાદ ખેતરના કામને અસર કરી શકે.",
    hi: "इस अवधि की वर्षा खेत के कामों को प्रभावित कर सकती है।",
  },
  "Strong wind during this period may affect field operations and tall standing crops.": {
    gu: "આ સમયગાળાનો તેજ પવન ખેતરના કામ અને ઊંચા ઊભા પાકને અસર કરી શકે.",
    hi: "इस अवधि की तेज़ हवा खेत के कामों और ऊँची खड़ी फसलों को प्रभावित कर सकती है।",
  },
  "If thunderstorms develop, they may interrupt field operations.": {
    gu: "જો ગાજવીજ સાથે વાવાઝોડું થાય, તો ખેતરનું કામ અટકી શકે.",
    hi: "अगर गरज-चमक के साथ तूफ़ान आता है, तो खेत का काम रुक सकता है।",
  },
  "Lightning potential is most relevant to people working in open fields.": {
    gu: "વીજળી પડવાની સંભાવના ખુલ્લા ખેતરમાં કામ કરતા લોકો માટે સૌથી વધુ મહત્ત્વની છે.",
    hi: "बिजली गिरने की संभावना खुले खेतों में काम करने वालों के लिए सबसे अधिक महत्वपूर्ण है।",
  },
  "Accumulated rain may be relevant to waterlogging in low-lying fields.": {
    gu: "એકઠો થયેલો વરસાદ નીચાણવાળા ખેતરોમાં પાણી ભરાવા માટે મહત્ત્વનો હોઈ શકે.",
    hi: "जमा हुई वर्षा निचले खेतों में जलभराव के लिए महत्वपूर्ण हो सकती है।",
  },
  "Low visibility may affect early-morning field work and transport.": {
    gu: "ઓછી દૃશ્યતા વહેલી સવારના ખેતરના કામ અને વાહનવ્યવહારને અસર કરી શકે.",
    hi: "कम दृश्यता सुबह-सुबह के खेत के काम और परिवहन को प्रभावित कर सकती है।",
  },
  "Hot, dry and windy conditions may be relevant to fire in dry fields and crop residue.": {
    gu: "ગરમ, સૂકું અને પવનવાળું હવામાન સૂકા ખેતરો અને પાકના અવશેષોમાં આગ માટે મહત્ત્વનું હોઈ શકે.",
    hi: "गर्म, सूखा और तेज़ हवा वाला मौसम सूखे खेतों और फसल अवशेषों में आग के लिए महत्वपूर्ण हो सकता है।",
  },
  "A rainfall deficit during this period may be relevant to soil moisture and irrigation.": {
    gu: "આ સમયગાળાની વરસાદની ઘટ જમીનના ભેજ અને સિંચાઈ માટે મહત્ત્વની હોઈ શકે.",
    hi: "इस अवधि की वर्षा की कमी मिट्टी की नमी और सिंचाई के लिए महत्वपूर्ण हो सकती है।",
  },
  "Timing not provided by CORE for this risk; see the headline.": {
    gu: "CORE એ આ જોખમનો સમય આપ્યો નથી; મુખ્ય વાક્ય જુઓ.",
    hi: "CORE ने इस जोखिम का समय नहीं दिया है; मुख्य वाक्य देखें।",
  },
  "Model agreement: not assessed": { gu: "મોડેલોની સહમતી: આકારણી નથી", hi: "मॉडलों की सहमति: आकलन नहीं" },
};
const AGREE = P(`Model agreement: (\\d+) of (\\d+)`, (m) => `મોડેલોની સહમતી: ${m[2]} માંથી ${m[1]}`, (m) => `मॉडलों की सहमति: ${m[2]} में से ${m[1]}`);

export interface EventIn {
  type: string;
  title: string;
  headline: string | null;
  severity: { level: number; status: string };
  timing_note: string | null;
  model_agreement: { text: string };
  context: { farmer: string } | null;
}
export interface EventOut {
  title: Out;
  headline: Out;
  status: Out;
  timing: Out;
  agreement: Out;
  context: Out;
}

/** Render a V2 event card's text. Each field falls back to the English independently. */
export function eventText(e: EventIn, lang: Lang): EventOut {
  if (!isTL(lang)) {
    return { title: en(e.title), headline: en(e.headline ?? ""), status: en(e.severity.status), timing: en(e.timing_note ?? ""),
      agreement: en(e.model_agreement.text), context: en(e.context?.farmer ?? "") };
  }
  const ex = (s: string | null | undefined): Out => {
    const v = s ?? "";
    return EVENT_EXACT[v] ? tr(EVENT_EXACT[v][lang]) : en(v);
  };
  const t = EVENT_TITLE[e.type];
  const h = match(HEADLINE[e.type], e.headline ?? "", lang);
  const lv = ["No risk", "Watch", "Alert", "Severe"].indexOf(e.severity.status);
  const ag = match([AGREE], e.model_agreement.text, lang);
  return {
    title: t && t.en === e.title ? tr(t[lang]) : en(e.title),
    headline: h ? tr(h) : en(e.headline ?? ""),
    status: lv >= 0 ? tr(LEVEL_NAMES[lang][lv]) : en(e.severity.status),
    timing: ex(e.timing_note),
    agreement: ag ? tr(ag) : ex(e.model_agreement.text),
    context: ex(e.context?.farmer),
  };
}
