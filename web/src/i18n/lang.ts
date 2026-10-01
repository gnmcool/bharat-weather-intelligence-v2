import { create } from "zustand";
import type { Lang } from "./coreText";

const KEY = "bwi2.lang";
const initial = (): Lang => {
  try {
    return localStorage.getItem(KEY) === "gu" ? "gu" : "en";
  } catch {
    return "en";
  }
};

/** Display language for the farmer screens. English is the default; the choice is remembered on this device. */
export const useLang = create<{ lang: Lang; setLang: (l: Lang) => void }>((set) => ({
  lang: initial(),
  setLang: (lang) => {
    try {
      localStorage.setItem(KEY, lang);
    } catch {
      /* storage unavailable: kept for this visit only */
    }
    set({ lang });
  },
}));

/** Farmer-screen labels written by V2 (not CORE). Same keys in both languages. */
const UI = {
  en: {
    wtk_title: "What should you know?",
    feels: "Feels like",
    rain_now: "Rain now", humidity: "Humidity", wind: "Wind", gusts: "gusts", pressure: "Pressure", cloud: "Cloud", visibility: "Visibility",
    u_mm: "mm", u_kmh: "km/h", u_km: "km",
    as_of: "As of", point_note: "point forecast at model-grid resolution",
    wtk_summary: (off: number, sys: number, sev: string) =>
      `${off} official alert${off === 1 ? "" : "s"} · ${sys} system assessment${sys === 1 ? "" : "s"} at Watch or above${sev ? ` (${sev})` : ""} · next 7 days`,
    sev_names: ["Severe", "Alert", "Watch"] as string[],
    none_detail: "No official alert for this location and no CORE risk at Watch level or above in the next 7 days.",
    official_alert: "Official alert",
    more_official: (n: number) => `+${n} more official alerts`,
    system_note: "CORE risk rules · next 7 days · not official warnings",
    show_more: (n: number) => `Show ${n} more system assessments`,
    dep_title: "Departure from normal", dep_sub: "· not a hazard on its own", forecast: "forecast", normal: "normal",
    normal_note: "Normal: NASA POWER 1991–2020 (MERRA-2 reanalysis), indicative — not IMD normals.",
    v2_down: "The V2 event service is unavailable. CORE's own risk list is still under Risks & alerts.",
    system_label: "System assessment",
    lang_switch: "Language",
    field_title: "Your field — location, crop, growth stage",
    loc_state: "1 · Location — state",
    loc_district: "1 · Location — district",
    sel_state: "Select state",
    sel_district: "Select district",
    crop: "2 · Crop",
    sel_crop: "Select crop",
    stage: "3 · Growth stage",
    sel_stage: "Select stage",
    field_location: "Field location:",
    field_help: "For a village, use the location search at the top; the forecast is a point forecast at model-grid resolution.",
    official_later: "The official agricultural advisory is shown separately in step 7.",
    choose_prompt: "Choose a crop and growth stage to see weather indicators for your field.",
    weather_title: "4 · Weather — next days at your field",
    th_day: "Day",
    th_temp: "Max / min °C",
    th_rain: "Rain mm",
    th_chance: "Chance",
    th_spray: "Spray-suitable hours*",
    th_disease: "Disease-favourable hours*",
    weather_note: "Forecast values from CORE. *Spray and disease hours are system-derived, unvalidated indicators from CORE's thresholds.",
    ind_title: "5 · System indicators",
    badge_system: "System-derived",
    badge_unvalidated: "Unvalidated",
    core_status: "CORE status:",
    rule: "Rule:",
    rule_suffix: "system-derived, unvalidated",
    rel_title: "6 · Potential crop relevance — weather events",
    rel_head: "Potential crop relevance",
    rel_none: "No significant weather event detected for this field in CORE's 7-day assessment.",
    rel_uses: (n: number, crop: string, stage: string, why: string) =>
      `Existing CORE indicator${n > 1 ? "s" : ""} for ${crop} (${stage}) that use ${why}:`,
    rel_no_ind: (crop: string) => `No existing CORE crop indicator for ${crop} at this stage uses this signal. V2 does not add agronomic rules.`,
    rel_official: (title: string) => `Official advisory: ${title} — step 7 below.`,
    off_head: "7 · Official agricultural advisory",
    off_sep: "Steps 5 and 6 are system output, not an official agricultural advisory. For farm decisions, follow the official advisory.",
    alerts_title: "Official weather alerts for this area",
    alerts_note: "",
    english_kept: "",
    why: { "daily maximum temperature": "daily maximum temperature", "daily minimum temperature": "daily minimum temperature", "daily rainfall": "daily rainfall", "consecutive dry days": "consecutive dry days" } as Record<string, string>,
  },
  gu: {
    wtk_title: "તમારે શું જાણવું જોઈએ?",
    feels: "અનુભવાતું તાપમાન",
    rain_now: "હાલનો વરસાદ", humidity: "ભેજ", wind: "પવન", gusts: "ઝાટકા", pressure: "હવાનું દબાણ", cloud: "વાદળ", visibility: "દૃશ્યતા",
    u_mm: "મિમી", u_kmh: "કિમી/કલાક", u_km: "કિમી",
    as_of: "સમય:", point_note: "મોડેલ-ગ્રીડના એક બિંદુની આગાહી",
    wtk_summary: (off: number, sys: number, sev: string) =>
      `${off} સત્તાવાર ચેતવણી · ${sys} સિસ્ટમ મૂલ્યાંકન 'નજર રાખો' કે તેથી ઉપરના સ્તરે${sev ? ` (${sev})` : ""} · આવતા 7 દિવસ`,
    sev_names: ["ગંભીર", "સાવધાન", "નજર રાખો"],
    none_detail: "આ સ્થળ માટે કોઈ સત્તાવાર ચેતવણી નથી અને આવતા 7 દિવસમાં CORE નું કોઈ જોખમ 'નજર રાખો' કે તેથી ઉપરના સ્તરે નથી.",
    official_alert: "સત્તાવાર ચેતવણી",
    more_official: (n: number) => `+${n} વધુ સત્તાવાર ચેતવણીઓ`,
    system_note: "CORE ના જોખમ નિયમો · આવતા 7 દિવસ · સત્તાવાર ચેતવણી નથી",
    show_more: (n: number) => `વધુ ${n} સિસ્ટમ મૂલ્યાંકન બતાવો`,
    dep_title: "સામાન્યથી તફાવત", dep_sub: "· પોતે જોખમ નથી", forecast: "આગાહી", normal: "સામાન્ય",
    normal_note: "સામાન્ય: NASA POWER 1991–2020 (MERRA-2 રીએનાલિસિસ), અંદાજિત — IMD ના સામાન્ય આંકડા નથી.",
    v2_down: "V2 ઘટના સેવા હાલ ઉપલબ્ધ નથી. CORE ની પોતાની જોખમ યાદી 'Risks & alerts' માં છે.",
    system_label: "સિસ્ટમ મૂલ્યાંકન",
    lang_switch: "ભાષા",
    field_title: "તમારું ખેતર — સ્થળ, પાક, પાકની અવસ્થા",
    loc_state: "1 · સ્થળ — રાજ્ય",
    loc_district: "1 · સ્થળ — જિલ્લો",
    sel_state: "રાજ્ય પસંદ કરો",
    sel_district: "જિલ્લો પસંદ કરો",
    crop: "2 · પાક",
    sel_crop: "પાક પસંદ કરો",
    stage: "3 · પાકની અવસ્થા",
    sel_stage: "અવસ્થા પસંદ કરો",
    field_location: "ખેતરનું સ્થળ:",
    field_help: "ગામ માટે ઉપરના સ્થળ-શોધનો ઉપયોગ કરો; આગાહી મોડેલ-ગ્રીડના એક બિંદુ માટેની છે.",
    official_later: "સત્તાવાર કૃષિ સલાહ પગલું 7 માં અલગથી બતાવી છે.",
    choose_prompt: "તમારા ખેતર માટે હવામાન સૂચકાંકો જોવા પાક અને પાકની અવસ્થા પસંદ કરો.",
    weather_title: "4 · હવામાન — તમારા ખેતર પર આવતા દિવસો",
    th_day: "દિવસ",
    th_temp: "મહત્તમ / લઘુત્તમ °C",
    th_rain: "વરસાદ મિમી",
    th_chance: "શક્યતા",
    th_spray: "છંટકાવ માટે યોગ્ય કલાક*",
    th_disease: "રોગને અનુકૂળ કલાક*",
    weather_note: "આગાહીના આંકડા CORE માંથી. *છંટકાવ અને રોગના કલાક CORE ની મર્યાદાઓ પરથી ગણાયેલા સિસ્ટમ-આધારિત, ચકાસણી ન થયેલા સૂચકાંકો છે.",
    ind_title: "5 · સિસ્ટમ સૂચકાંકો",
    badge_system: "સિસ્ટમ-આધારિત",
    badge_unvalidated: "ચકાસણી થયેલ નથી",
    core_status: "CORE સ્થિતિ:",
    rule: "નિયમ:",
    rule_suffix: "સિસ્ટમ-આધારિત, ચકાસણી થયેલ નથી",
    rel_title: "6 · પાક પર સંભવિત અસર — હવામાનની ઘટનાઓ",
    rel_head: "પાક પર સંભવિત અસર",
    rel_none: "CORE ના 7 દિવસના મૂલ્યાંકનમાં આ ખેતર માટે કોઈ મહત્ત્વની હવામાન ઘટના મળી નથી.",
    rel_uses: (_n: number, crop: string, stage: string, why: string) => `${crop} (${stage}) માટેના CORE ના હાલના સૂચકાંકો, જે ${why} પર આધારિત છે:`,
    rel_no_ind: (crop: string) => `આ અવસ્થાએ ${crop} માટે CORE નો કોઈ સૂચકાંક આ સંકેતનો ઉપયોગ કરતો નથી. V2 ખેતીના નવા નિયમો ઉમેરતું નથી.`,
    rel_official: (title: string) => `સત્તાવાર સલાહ: ${title} — નીચે પગલું 7.`,
    off_head: "7 · સત્તાવાર કૃષિ સલાહ",
    off_sep: "પગલાં 5 અને 6 સિસ્ટમનું પરિણામ છે, સત્તાવાર કૃષિ સલાહ નથી. ખેતીના નિર્ણયો માટે સત્તાવાર સલાહ અનુસરો.",
    alerts_title: "આ વિસ્તાર માટે સત્તાવાર હવામાન ચેતવણીઓ",
    alerts_note: "સત્તાવાર ચેતવણીઓ જારી થયેલી ભાષામાં જ બતાવી છે; તેનો અનુવાદ કરવામાં આવતો નથી.",
    english_kept: "અંગ્રેજીમાં (અનુવાદ ઉપલબ્ધ નથી)",
    why: { "daily maximum temperature": "દૈનિક મહત્તમ તાપમાન", "daily minimum temperature": "દૈનિક લઘુત્તમ તાપમાન", "daily rainfall": "દૈનિક વરસાદ", "consecutive dry days": "સળંગ કોરા દિવસો" } as Record<string, string>,
  },
};

export type UiText = (typeof UI)["en"];
export const uiText = (lang: Lang): UiText => UI[lang];

/** Locale for dates (weekday and month names). Digits stay Western in both languages. */
export const dateLocale = (lang: Lang) => (lang === "gu" ? "gu-IN-u-nu-latn" : "en-IN");
