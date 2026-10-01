// Gujarati rendering of CORE's farmer-report text (CORE 2840f8d, backend/app/engines/farmer.py and crops.yaml).
//
// Rules (docs/FARMER_GUJARATI.md):
//  - Presentation only. Levels, numbers and thresholds come from CORE unchanged; nothing is computed here.
//  - CORE sends finished English sentences. Each one is matched against CORE's fixed sentence patterns; numbers are
//    copied from the English text into the Gujarati template. A sentence that does not match exactly is shown in
//    English (never guessed). So a future CORE wording change shows up as English, not as wrong Gujarati.
//  - Official text (IMD warnings, advisory links' targets) is never altered.
//  - Every Gujarati string here needs native-speaker review before release (REVIEW list in the doc).
//
// This file has no imports so it can be tested directly with Node (web/test/coreText.test.ts).

export type Lang = "en" | "gu";

/** A rendered string plus whether it is Gujarati (false = English fallback). */
export interface Out {
  text: string;
  gu: boolean;
}
const en = (text: string): Out => ({ text, gu: false });
const g = (text: string): Out => ({ text, gu: true });

// ── Fixed vocabulary ─────────────────────────────────────────────────────────

export const LEVEL_GU = ["જોખમ નથી", "નજર રાખો", "સાવધાન", "ગંભીર"] as const;

/** crops.yaml crop id → Gujarati name. */
export const CROP_GU: Record<string, string> = {
  wheat: "ઘઉં",
  paddy: "ડાંગર",
  cotton: "કપાસ",
  groundnut: "મગફળી",
  castor: "દિવેલા (એરંડા)",
  bajra: "બાજરી",
  cumin: "જીરું",
  mustard: "રાયડો",
};

/** crops.yaml season strings → Gujarati. */
export const SEASON_GU: Record<string, string> = {
  Rabi: "રવિ",
  Kharif: "ખરીફ",
  "Kharif / Summer": "ખરીફ / ઉનાળુ",
};

/** crops.yaml stage ids → Gujarati. */
export const STAGE_GU: Record<string, string> = {
  sowing: "વાવણી",
  nursery: "ધરુવાડિયું",
  transplanting: "ફેરરોપણી",
  vegetative: "વાનસ્પતિક વૃદ્ધિ",
  squaring: "ચાપવા અવસ્થા",
  flowering: "ફૂલ અવસ્થા",
  pegging: "સૂયા અવસ્થા",
  pod_fill: "શીંગ ભરાવાની અવસ્થા",
  grain_fill: "દાણા ભરાવાની અવસ્થા",
  boll_development: "જીંડવા વિકાસ",
  capsule_development: "ડોડવા વિકાસ",
  seed_development: "બીજ વિકાસ",
  harvest: "કાપણી",
};

const stageEn = (s: string) => s.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());

export function cropName(id: string, english: string, lang: Lang): Out {
  return lang === "gu" && CROP_GU[id] ? g(CROP_GU[id]) : en(english);
}
export function seasonName(s: string, lang: Lang): Out {
  return lang === "gu" && SEASON_GU[s] ? g(SEASON_GU[s]) : en(s);
}
export function stageName(s: string, lang: Lang): Out {
  return lang === "gu" && STAGE_GU[s] ? g(STAGE_GU[s]) : en(stageEn(s));
}
/** CORE writes the stage inside rule text as stage.replace("_", " "), e.g. "grain fill". */
const stageFromRule = (s: string): string | undefined => STAGE_GU[s.replace(/ /g, "_")];

// ── Indicators (farmer.py `ind.append(...)`) ──────────────────────────────────

const N = "(\\d+(?:\\.\\d+)?)"; // a number as CORE prints it; copied verbatim, never reformatted

interface Pattern {
  re: RegExp;
  gu: (m: RegExpMatchArray) => string | undefined;
}
const P = (src: string, gu: Pattern["gu"]): Pattern => ({ re: new RegExp(`^${src}$`), gu });

const LABEL: Record<string, Record<string, string>> = {
  heat_stress: { "Heat stress for this stage": "આ અવસ્થામાં ગરમીનો તણાવ" },
  cold_stress: { "Cold / frost stress": "ઠંડી / હિમનો તણાવ" },
  heavy_rain: { "Heavy rain": "ભારે વરસાદ" },
  dry_spell: { "Dry spell": "વરસાદ વગરનો ગાળો" },
  harvest_window: { "Dry harvest window": "કાપણી માટે કોરો ગાળો" },
  disease_weather: { "Disease-favourable weather": "રોગને અનુકૂળ હવામાન" },
};

const VALUE: Record<string, Pattern[]> = {
  heat_stress: [P(`${N} of 7 days ≥ ${N} °C`, (m) => `7 માંથી ${m[1]} દિવસ ≥ ${m[2]} °C`)],
  cold_stress: [P(`${N} of 7 nights ≤ ${N} °C`, (m) => `7 માંથી ${m[1]} રાત ≤ ${m[2]} °C`)],
  heavy_rain: [P(`max ${N} mm/day`, (m) => `મહત્તમ ${m[1]} મિમી/દિવસ`)],
  dry_spell: [P(`${N} days`, (m) => `${m[1]} દિવસ`)],
  harvest_window: [P(`longest dry run ${N} days`, (m) => `સૌથી લાંબો કોરો ગાળો ${m[1]} દિવસ`)],
  disease_weather: [
    P(`${N} humid hours \\(RH ≥ ${N}%, ${N}–${N} °C\\)`, (m) => `${m[1]} ભેજવાળા કલાક (ભેજ ≥ ${m[2]}%, ${m[3]}–${m[4]} °C)`),
  ],
};

const RULE: Record<string, Pattern[]> = {
  heat_stress: [
    P(`Tmax ≥ ${N} °C at ([a-z ]+)`, (m) => (stageFromRule(m[2]) ? `${stageFromRule(m[2])} વખતે મહત્તમ તાપમાન ≥ ${m[1]} °C` : undefined)),
  ],
  cold_stress: [
    P(`Tmin ≤ ${N} °C at ([a-z ]+)`, (m) => (stageFromRule(m[2]) ? `${stageFromRule(m[2])} વખતે લઘુત્તમ તાપમાન ≤ ${m[1]} °C` : undefined)),
  ],
  heavy_rain: [
    P(`IMD heavy rain ≥ ${N} mm/day \\(Watch ≥ ${N}\\)`, (m) => `IMD મુજબ ભારે વરસાદ ≥ ${m[1]} મિમી/દિવસ (નજર રાખો ≥ ${m[2]})`),
  ],
  dry_spell: [P(`Consecutive days < ${N} mm`, (m) => `સળંગ દિવસો, દરેક દિવસે ${m[1]} મિમી કરતાં ઓછો વરસાદ`)],
  harvest_window: [
    P(`days < ${N} mm & rain prob < ${N}%`, (m) => `દિવસો: વરસાદ < ${m[1]} મિમી અને વરસાદની શક્યતા < ${m[2]}%`),
  ],
  disease_weather: [
    P(`Leaf-wetness proxy; stage-sensitive for this crop`, () => "પાનની ભીનાશનો અંદાજ; આ પાક માટે આ અવસ્થા સંવેદનશીલ છે"),
    P(`Leaf-wetness proxy`, () => "પાનની ભીનાશનો અંદાજ"),
  ],
};

function match(patterns: Pattern[] | undefined, s: string): string | undefined {
  for (const p of patterns ?? []) {
    const m = s.match(p.re);
    if (m) return p.gu(m);
  }
  return undefined;
}

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
  if (lang !== "gu") return { label: en(i.label), value: en(i.value), rule: en(i.rule) };
  const pick = (gu: string | undefined, eng: string) => (gu ? g(gu) : en(eng));
  return {
    label: pick(LABEL[i.id]?.[i.label], i.label),
    value: pick(match(VALUE[i.id], i.value), i.value),
    rule: pick(match(RULE[i.id], i.rule), i.rule),
  };
}

// ── Fixed CORE paragraphs: exact-match only ────────────────────────────────────

const EXACT: Record<string, string> = {
  // farmer.py disclaimer
  "SYSTEM-DERIVED WEATHER INDICATORS — computed automatically from forecast models using unvalidated thresholds. They are not farming instructions. Follow the official Agromet Advisory for decisions.":
    "સિસ્ટમ-આધારિત હવામાન સૂચકાંકો — ફોરકાસ્ટ મોડેલોમાંથી, ચકાસણી ન થયેલી મર્યાદાઓ (થ્રેશોલ્ડ) વડે આપમેળે ગણાયેલા. આ ખેતી માટેની સૂચના નથી. નિર્ણય માટે સત્તાવાર કૃષિ-હવામાન સલાહ (Agromet Advisory) અનુસરો.",
  // farmer.py OFFICIAL_ADVISORY
  "Official Agromet Advisory (IMD × ICAR — Gramin Krishi Mausam Sewa)":
    "સત્તાવાર કૃષિ-હવામાન સલાહ (IMD × ICAR — ગ્રામીણ કૃષિ મૌસમ સેવા)",
  "District Agromet Advisory Service bulletins are issued every Tuesday and Friday by IMD with State Agricultural Universities / KVKs. They are the authoritative source for farm operations.":
    "જિલ્લા કૃષિ-હવામાન સલાહ સેવાના બુલેટિન IMD દ્વારા રાજ્ય કૃષિ યુનિવર્સિટીઓ / KVK સાથે મળીને દર મંગળવારે અને શુક્રવારે બહાર પડે છે. ખેતીના કામ માટે એ જ અધિકૃત સ્ત્રોત છે.",
  "Not yet ingested automatically — requires IMD Agromet data access (see docs/ARCHITECTURE.md).":
    "આ સલાહ હજી આપમેળે અહીં લાવવામાં આવતી નથી — તે માટે IMD કૃષિ-હવામાન ડેટાની પરવાનગી જરૂરી છે.",
  "IMD — Agromet services": "IMD — કૃષિ-હવામાન સેવાઓ",
  "Meghdoot app (IMD/ICAR/IITM) — district advisories": "મેઘદૂત એપ (IMD/ICAR/IITM) — જિલ્લાની સલાહ",
  "Kisan Call Centre — 1800-180-1551": "કિસાન કોલ સેન્ટર — 1800-180-1551",
  // crops.yaml notes
  "Terminal heat after anthesis shortens grain filling (Porter & Gawith 1999 review of wheat temperature responses).":
    "ફૂલ આવ્યા પછીની ગરમી દાણા ભરાવાનો સમય ટૂંકો કરે છે (Porter & Gawith 1999, ઘઉં પર તાપમાનની અસરની સમીક્ષા).",
  "Temperatures above ~35 °C at anthesis increase spikelet sterility (Jagadish et al. 2007).":
    "ફૂલ અવસ્થાએ આશરે 35 °C થી વધુ તાપમાનથી દાણા ખાલી રહેવાનું (વંધ્યતા) વધે છે (Jagadish et al. 2007).",
  "High heat at flowering raises square and boll shedding; validate local thresholds.":
    "ફૂલ અવસ્થાએ વધુ ગરમીથી ચાપવા અને જીંડવા ખરવાનું વધે છે; સ્થાનિક મર્યાદાઓની ચકાસણી જરૂરી છે.",
  "Heat stress at flowering/pegging reduces pod set.": "ફૂલ/સૂયા અવસ્થાએ ગરમીનો તણાવ શીંગ બેસવાનું ઘટાડે છે.",
  "Relatively heat tolerant; cold nights slow spike development.":
    "ગરમી પ્રમાણમાં સહન કરે છે; ઠંડી રાતો માળ (સ્પાઇક) ના વિકાસને ધીમો પાડે છે.",
  "Heat tolerant; very high temperature at flowering reduces seed set.":
    "ગરમી સહન કરે છે; ફૂલ અવસ્થાએ ખૂબ ઊંચું તાપમાન દાણા બેસવાનું ઘટાડે છે.",
  "Cloudy, humid spells at flowering favour blight (Alternaria) — a major Gujarat concern.":
    "ફૂલ અવસ્થાએ વાદળછાયું, ભેજવાળું હવામાન ચરમી (Alternaria blight) ને અનુકૂળ છે — ગુજરાતમાં મોટી સમસ્યા.",
  "Frost at flowering/pod fill damages pods; cloudy humid weather favours aphids.":
    "ફૂલ/શીંગ ભરાવાની અવસ્થાએ હિમ શીંગોને નુકસાન કરે છે; વાદળછાયું ભેજવાળું હવામાન મોલો-મશી (એફિડ) ને અનુકૂળ છે.",
  // crops.yaml validation_status
  unvalidated: "ચકાસણી બાકી",
};

/** A fixed CORE paragraph in Gujarati if it matches CORE's text exactly; otherwise CORE's English. */
export function coreText(s: string | null | undefined, lang: Lang): Out {
  const v = s ?? "";
  return lang === "gu" && EXACT[v] ? g(EXACT[v]) : en(v);
}

/** Number of Gujarati strings, for the review list. */
export const STRING_COUNT =
  LEVEL_GU.length +
  Object.keys(CROP_GU).length +
  Object.keys(SEASON_GU).length +
  Object.keys(STAGE_GU).length +
  Object.keys(LABEL).length +
  Object.values(VALUE).flat().length +
  Object.values(RULE).flat().length +
  Object.keys(EXACT).length;
