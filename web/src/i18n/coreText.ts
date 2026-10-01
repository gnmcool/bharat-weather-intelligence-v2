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

export const EXACT: Record<string, string> = {
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
  // CORE anomaly.py labels, periods and categories (farmer home, "Departure from normal")
  "Max temperature": "મહત્તમ તાપમાન",
  "Min temperature": "લઘુત્તમ તાપમાન",
  "Max temperature (7-day mean)": "મહત્તમ તાપમાન (7 દિવસની સરેરાશ)",
  Rainfall: "વરસાદ",
  Today: "આજે",
  "Next 7 days": "આવતા 7 દિવસ",
  "Next 7 days (forecast)": "આવતા 7 દિવસ (આગાહી)",
  "Past 30 days (model analysis)": "છેલ્લા 30 દિવસ (મોડેલ વિશ્લેષણ)",
  "Above normal": "સામાન્યથી વધુ",
  "Below normal": "સામાન્યથી ઓછું",
  "Near normal": "લગભગ સામાન્ય",
  "Large excess": "ઘણો વધુ",
  Excess: "વધુ",
  Normal: "સામાન્ય",
  Deficient: "ઓછો",
  "Large deficient": "ઘણો ઓછો",
  "No rain": "વરસાદ નહીં",
  "Dry season": "સૂકી ઋતુ",
  "Rain in dry season": "સૂકી ઋતુમાં વરસાદ",
  // CORE current-conditions fields (services.py source, terrain.py classes)
  "Open-Meteo best-match (model analysis, not a station observation)": "Open-Meteo best-match (મોડેલ વિશ્લેષણ, હવામાન મથકનું અવલોકન નથી)",
  plains: "મેદાની વિસ્તાર",
  coastal: "દરિયાકાંઠો",
  hills: "પહાડી વિસ્તાર",
  // V2 format.wmoText (WMO 4677 groups)
  Clear: "ચોખ્ખું આકાશ",
  "Partly cloudy": "આંશિક વાદળછાયું",
  Overcast: "ઘેરાં વાદળ",
  Fog: "ધુમ્મસ",
  Drizzle: "ઝરમર",
  Rain: "વરસાદ",
  "Heavy rain": "ભારે વરસાદ",
  Snow: "હિમવર્ષા",
  Showers: "ઝાપટાં",
  "Violent showers": "ખૂબ ભારે ઝાપટાં",
  Thunderstorm: "ગાજવીજ સાથે વાવાઝોડું",
  "Thunderstorm with hail": "કરા સાથે ગાજવીજ અને વાવાઝોડું",
  // V2 api-v2 events.py what_to_know.message
  "No significant weather event detected.": "કોઈ મહત્ત્વની હવામાન ઘટના મળી નથી.",
};

/** A fixed CORE paragraph in Gujarati if it matches CORE's text exactly; otherwise CORE's English. */
export function coreText(s: string | null | undefined, lang: Lang): Out {
  const v = s ?? "";
  return lang === "gu" && EXACT[v] ? g(EXACT[v]) : en(v);
}

// ── Weather-event cards (V2 /api/v2/events over CORE risks; CORE 2840f8d risk.py headlines) ─────────────────

export const WD: Record<string, string> = { Mon: "સોમ", Tue: "મંગળ", Wed: "બુધ", Thu: "ગુરુ", Fri: "શુક્ર", Sat: "શનિ", Sun: "રવિ" };
export const MO: Record<string, string> = {
  Jan: "જાન્યુ", Feb: "ફેબ્રુ", Mar: "માર્ચ", Apr: "એપ્રિલ", May: "મે", Jun: "જૂન",
  Jul: "જુલાઈ", Aug: "ઑગસ્ટ", Sep: "સપ્ટે", Oct: "ઑક્ટો", Nov: "નવે", Dec: "ડિસે",
};
const WDS = Object.keys(WD).join("|");
const MOS = Object.keys(MO).join("|");
/** CORE _fmt_day: "today" | "tomorrow" | "Sat 03 Oct". */
const DAY = `(today|tomorrow|(?:${WDS}) \\d{2} (?:${MOS}))`;
const dayGu = (s: string) =>
  s === "today" ? "આજે" : s === "tomorrow" ? "આવતીકાલે" : s.replace(/^(\w{3}) (\d{2}) (\w{3})$/, (_, w, d, m) => `${WD[w]} ${d} ${MO[m]}`);
/** CORE thunderstorm time: "Thu 1 Oct, 2 PM". AM/PM kept as written (review item). */
const WHEN = `((?:${WDS}) \\d{1,2} (?:${MOS}), \\d{1,2} (?:AM|PM))`;
const whenGu = (s: string) => s.replace(/^(\w{3}) (\d{1,2}) (\w{3}), /, (_, w, d, m) => `${WD[w]} ${d} ${MO[m]}, `);
/** CORE fog time: "Thu 02 AM". */
const HOUR = `((?:${WDS}) \\d{2} (?:AM|PM))`;
const hourGu = (s: string) => s.replace(/^(\w{3}) /, (_, w) => `${WD[w]} `);

const HEAT: Record<string, string> = {
  "Heat watch": "ગરમી પર નજર રાખો",
  "Heat-wave conditions": "હીટવેવ (લૂ) ની સ્થિતિ",
  "Severe heat-wave conditions": "ગંભીર હીટવેવ (લૂ) ની સ્થિતિ",
};
const COLD: Record<string, string> = {
  "Cold watch": "ઠંડી પર નજર રાખો",
  "Cold-wave conditions": "શીતલહેરની સ્થિતિ",
  "Severe cold wave": "ગંભીર શીતલહેર",
};
const RAIN_CAT: Record<string, string> = {
  "Very light": "ખૂબ હળવો", Light: "હળવો", Moderate: "મધ્યમ", "Rather heavy": "સાધારણ ભારે",
  Heavy: "ભારે", "Very heavy": "અતિ ભારે", "Extremely heavy": "અત્યંત ભારે",
};
const DEP_CAT: Record<string, string> = {
  "Large excess": "ઘણો વધુ", Excess: "વધુ", Normal: "સામાન્ય", Deficient: "ઓછો", "Large deficient": "ઘણો ઓછો", "No rain": "વરસાદ નહીં",
};
const alt = (o: Record<string, string>) => Object.keys(o).map((k) => k.replace(/[-]/g, "\\-")).join("|");

const HEADLINE: Record<string, Pattern[]> = {
  heat: [P(`(${alt(HEAT)}) ${DAY}`, (m) => `${dayGu(m[2])} ${HEAT[m[1]]}`)],
  cold: [P(`(${alt(COLD)}) ${DAY}`, (m) => `${dayGu(m[2])} ${COLD[m[1]]}`)],
  rain: [P(`(${alt(RAIN_CAT)}) rain ${DAY} \\(${N} mm\\)`, (m) => `${dayGu(m[2])} ${RAIN_CAT[m[1]]} વરસાદ (${m[3]} મિમી)`)],
  wind: [
    P(`Gusts up to ${N} km/h ${DAY}`, (m) => `${dayGu(m[2])} ${m[1]} કિમી/કલાક સુધીના પવનના ઝાટકા`),
    P(`Gusts up to ${N} km/h`, (m) => `${m[1]} કિમી/કલાક સુધીના પવનના ઝાટકા`),
  ],
  thunderstorm: [
    P(`Thunderstorm likely from ${WHEN}`, (m) => `${whenGu(m[1])} થી ગાજવીજ સાથે વાવાઝોડાની વધુ શક્યતા`),
    P(`Thunderstorm possible from ${WHEN}`, (m) => `${whenGu(m[1])} થી ગાજવીજ સાથે વાવાઝોડાની શક્યતા`),
  ],
  lightning: [
    P(`Lightning risk high from ${WHEN}`, (m) => `${whenGu(m[1])} થી વીજળી પડવાનું વધુ જોખમ`),
    P(`Lightning risk present from ${WHEN}`, (m) => `${whenGu(m[1])} થી વીજળી પડવાનું જોખમ`),
  ],
  flood: [
    P(`72-h rain up to ${N} mm \\(incl\\. past 2 days\\) — flooding possible`, (m) => `72 કલાકમાં ${m[1]} મિમી સુધી વરસાદ (છેલ્લા 2 દિવસ સહિત) — પૂર શક્ય`),
    P(`72-h rain up to ${N} mm \\(incl\\. past 2 days\\)`, (m) => `72 કલાકમાં ${m[1]} મિમી સુધી વરસાદ (છેલ્લા 2 દિવસ સહિત)`),
  ],
  drought: [
    P(`Last 30 days: ${N} mm vs normal ${N} mm \\(([+-]\\d+)%, (${alt(DEP_CAT)})\\)`,
      (m) => `છેલ્લા 30 દિવસ: ${m[1]} મિમી, સામાન્ય ${m[2]} મિમી (${m[3]}%, ${DEP_CAT[m[4]]})`),
  ],
  fog: [P(`Visibility down to ${N} m around ${HOUR}`, (m) => `${hourGu(m[2])} આસપાસ દૃશ્યતા ઘટીને ${m[1]} મીટર`)],
  fire: [P(`Hot, dry and windy spells ahead`, () => "આગળના દિવસોમાં ગરમ, સૂકા અને પવનવાળા ગાળા")],
};

/** V2 event titles (api-v2 catalogue.TITLE), keyed by event type and checked against the English. */
export const EVENT_TITLE: Record<string, [string, string]> = {
  heat: ["Heat", "ગરમી"],
  cold: ["Cold", "ઠંડી"],
  rain: ["Heavy rain", "ભારે વરસાદ"],
  wind: ["Strong wind", "તેજ પવન"],
  thunderstorm: ["Thunderstorm potential — model derived", "ગાજવીજ સાથે વાવાઝોડાની સંભાવના — મોડેલ આધારિત"],
  lightning: ["Lightning potential — model derived", "વીજળી પડવાની સંભાવના — મોડેલ આધારિત"],
  flood: ["Flood-related risk (rainfall accumulation)", "પૂર સંબંધિત જોખમ (એકઠો થયેલો વરસાદ)"],
  drought: ["Dry spell / rainfall deficit", "વરસાદ વગરનો ગાળો / વરસાદની ઘટ"],
  fog: ["Fog", "ધુમ્મસ"],
  fire: ["Fire weather", "આગ માટે અનુકૂળ હવામાન"],
};

/** V2 farmer context (api-v2 catalogue.CONTEXT[...][1]); exact match only. */
export const EVENT_EXACT: Record<string, string> = {
  "Heat during this period may be relevant to field work and to crops at heat-sensitive stages.":
    "આ સમયગાળાની ગરમી ખેતરના કામ અને ગરમી પ્રત્યે સંવેદનશીલ અવસ્થાના પાક માટે મહત્ત્વની હોઈ શકે.",
  "Low night temperatures during this period may be relevant to crops at cold-sensitive stages.":
    "આ સમયગાળાનું રાત્રિનું નીચું તાપમાન ઠંડી પ્રત્યે સંવેદનશીલ અવસ્થાના પાક માટે મહત્ત્વનું હોઈ શકે.",
  "Rain during this period may affect field operations.": "આ સમયગાળાનો વરસાદ ખેતરના કામને અસર કરી શકે.",
  "Strong wind during this period may affect field operations and tall standing crops.":
    "આ સમયગાળાનો તેજ પવન ખેતરના કામ અને ઊંચા ઊભા પાકને અસર કરી શકે.",
  "If thunderstorms develop, they may interrupt field operations.": "જો ગાજવીજ સાથે વાવાઝોડું થાય, તો ખેતરનું કામ અટકી શકે.",
  "Lightning potential is most relevant to people working in open fields.":
    "વીજળી પડવાની સંભાવના ખુલ્લા ખેતરમાં કામ કરતા લોકો માટે સૌથી વધુ મહત્ત્વની છે.",
  "Accumulated rain may be relevant to waterlogging in low-lying fields.":
    "એકઠો થયેલો વરસાદ નીચાણવાળા ખેતરોમાં પાણી ભરાવા માટે મહત્ત્વનો હોઈ શકે.",
  "Low visibility may affect early-morning field work and transport.": "ઓછી દૃશ્યતા વહેલી સવારના ખેતરના કામ અને વાહનવ્યવહારને અસર કરી શકે.",
  "Hot, dry and windy conditions may be relevant to fire in dry fields and crop residue.":
    "ગરમ, સૂકું અને પવનવાળું હવામાન સૂકા ખેતરો અને પાકના અવશેષોમાં આગ માટે મહત્ત્વનું હોઈ શકે.",
  "A rainfall deficit during this period may be relevant to soil moisture and irrigation.":
    "આ સમયગાળાની વરસાદની ઘટ જમીનના ભેજ અને સિંચાઈ માટે મહત્ત્વની હોઈ શકે.",
  "Timing not provided by CORE for this risk; see the headline.": "CORE એ આ જોખમનો સમય આપ્યો નથી; મુખ્ય વાક્ય જુઓ.",
  "Model agreement: not assessed": "મોડેલોની સહમતી: આકારણી નથી",
};
const AGREE = P(`Model agreement: (\\d+) of (\\d+)`, (m) => `મોડેલોની સહમતી: ${m[2]} માંથી ${m[1]}`);

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
  const ex = (s: string | null | undefined): Out => {
    const v = s ?? "";
    return lang === "gu" && EVENT_EXACT[v] ? g(EVENT_EXACT[v]) : en(v);
  };
  if (lang !== "gu") {
    return { title: en(e.title), headline: en(e.headline ?? ""), status: en(e.severity.status), timing: en(e.timing_note ?? ""),
      agreement: en(e.model_agreement.text), context: en(e.context?.farmer ?? "") };
  }
  const t = EVENT_TITLE[e.type];
  const h = match(HEADLINE[e.type], e.headline ?? "");
  const lv = ["No risk", "Watch", "Alert", "Severe"].indexOf(e.severity.status);
  const ag = e.model_agreement.text.match(AGREE.re);
  return {
    title: t && t[0] === e.title ? g(t[1]) : en(e.title),
    headline: h ? g(h) : en(e.headline ?? ""),
    status: lv >= 0 ? g(LEVEL_GU[lv]) : en(e.severity.status),
    timing: ex(e.timing_note),
    agreement: ag ? g(AGREE.gu(ag)!) : ex(e.model_agreement.text),
    context: ex(e.context?.farmer),
  };
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
  Object.keys(EXACT).length +
  Object.values(HEADLINE).flat().length +
  Object.keys(EVENT_TITLE).length +
  Object.keys(EVENT_EXACT).length +
  Object.keys(WD).length +
  Object.keys(MO).length;
