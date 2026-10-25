// Farmer site (#/kisan): how CORE's numbers become the few words a farmer sees. Presentation only — no new
// weather rules: rain categories are IMD's published 24-h rainfall classes, the chance is CORE's
// precipitation_probability_max, and warnings are CORE's official alerts (IMD/CWC/SDMA via NDMA SACHET), shown
// with their fixed warning type translated and the issuer's original message one tap away.
//
// No imports, so it is tested directly with Node (web/test/kisan.test.ts).

export type KLang = "gu" | "hi" | "en";

// ── Rain ─────────────────────────────────────────────────────────────────────

/** IMD 24-hour rainfall classes (mm): very light 0.1–2.4, light 2.5–15.5, moderate 15.6–64.4, heavy 64.5–115.5,
 *  very heavy 115.6–204.4, extremely heavy ≥ 204.5. */
export type RainClass = "none" | "veryLight" | "light" | "moderate" | "heavy" | "veryHeavy" | "extreme";
export function rainClass(mm: number | null | undefined): RainClass {
  if (mm === null || mm === undefined || Number.isNaN(mm) || mm < 0.1) return "none";
  if (mm < 2.5) return "veryLight";
  if (mm < 15.6) return "light";
  if (mm < 64.5) return "moderate";
  if (mm < 115.6) return "heavy";
  if (mm < 204.5) return "veryHeavy";
  return "extreme";
}

/** How sure the forecast is, from CORE's daily maximum precipitation probability. */
export type Likelihood = "unlikely" | "possible" | "likely";
export function likelihood(prob: number | null | undefined): Likelihood {
  if (prob === null || prob === undefined || Number.isNaN(prob) || prob < 30) return "unlikely";
  return prob < 60 ? "possible" : "likely";
}

export type RainKind = "dry" | "smallChance" | "rain" | "heavyRain";
export interface RainView {
  kind: RainKind;
  cls: RainClass;
  lik: Likelihood;
  prob: number | null;
  mm: number | null;
}
/**
 * One day's rain in farmer terms.
 * - no measurable rain forecast and chance < 30 % → dry
 * - otherwise, rain amount below 0.1 mm or chance < 30 % → "small chance" (never a promise of rain)
 * - heavy (≥ 64.5 mm) gets its own kind so the screen can stress it
 */
export function rainView(mm: number | null | undefined, prob: number | null | undefined): RainView {
  const cls = rainClass(mm);
  const lik = likelihood(prob);
  const p = prob === null || prob === undefined || Number.isNaN(prob) ? null : Math.round(prob);
  const m = mm === null || mm === undefined || Number.isNaN(mm) ? null : mm;
  let kind: RainKind;
  if (cls === "none" && lik === "unlikely") kind = "dry";
  else if (cls === "none" || lik === "unlikely") kind = "smallChance";
  else if (cls === "heavy" || cls === "veryHeavy" || cls === "extreme") kind = "heavyRain";
  else kind = "rain";
  return { kind, cls, lik, prob: p, mm: m };
}

/** Rain amount as people say it: whole millimetres, "less than 1 mm" below 1. */
export const mmText = (mm: number | null) => (mm === null ? null : mm < 1 ? "<1" : String(Math.round(mm)));

// ── Days ─────────────────────────────────────────────────────────────────────

export interface DayRow {
  date: string; // YYYY-MM-DD, IST
  precipitation_sum: number | null;
  precipitation_probability_max: number | null;
  temperature_2m_max: number | null;
  temperature_2m_min: number | null;
  weather_code: number | null;
}
/** Today (IST) and the next three days from CORE's daily rows; rows before today are skipped. */
export function pickDays(daily: DayRow[], todayIst: string): DayRow[] {
  const rows = daily.filter((d) => d.date >= todayIst).sort((a, b) => a.date.localeCompare(b.date));
  return rows[0]?.date === todayIst ? rows.slice(0, 4) : [];
}
/** Today's date in India Standard Time, YYYY-MM-DD. */
export function istToday(now: Date = new Date()): string {
  return new Date(now.getTime() + 5.5 * 3600_000).toISOString().slice(0, 10);
}

// ── Official warnings ────────────────────────────────────────────────────────

export interface WarningIn {
  id: string;
  event: string | null;
  severity: string | null;
  headline: string;
  description: string | null;
  sender: string | null;
  issuer: string;
  effective: string | null;
  expires: string | null;
  area: string | null;
  match: "district" | "state" | "national";
}

/** Fixed SACHET/IMD warning types → our key. Anything else stays in the issuer's English. */
const EVENT_KEYS: [RegExp, string][] = [
  [/^extremely heavy rain(fall)?$/, "extremelyHeavyRain"],
  [/^very heavy rain(fall)?$/, "veryHeavyRain"],
  [/^heavy (to very heavy )?rain(fall)?$/, "heavyRain"],
  [/^moderate rain(fall)?$/, "moderateRain"],
  [/^(light|light to moderate) rain(fall)?$/, "lightRain"],
  [/^rain(fall)?$/, "rain"],
  [/^thunder ?showers?$/, "thunderShower"],
  [/^(moderate |severe )?thunderstorms?( and lightning| with lightning)?$/, "thunderstorm"],
  [/^lightning$/, "lightning"],
  [/^squall(y| wind| winds)?$/, "squall"],
  [/^(strong|gusty|high) winds?$/, "strongWind"],
  [/^hail(storm)?$/, "hail"],
  [/^dust ?storm$/, "dustStorm"],
  [/^flash flood$/, "flashFlood"],
  [/^flood(s|ing)?$/, "flood"],
  [/^cloud ?burst$/, "cloudburst"],
  [/^landslides?$/, "landslide"],
  [/^(severe )?heat ?wave$/, "heatWave"],
  [/^(severe )?cold ?wave$/, "coldWave"],
  [/^(dense )?fog$/, "fog"],
  [/^(cyclone|cyclonic storm|severe cyclonic storm|depression|deep depression)$/, "cyclone"],
];
export function eventKey(event: string | null | undefined): string | null {
  const e = (event ?? "").toLowerCase().replace(/\bwarning\b/g, "").replace(/\s+/g, " ").trim();
  if (!e) return null;
  for (const [re, k] of EVENT_KEYS) if (re.test(e)) return k;
  return null;
}

const SEV_RANK: Record<string, number> = { Extreme: 4, Severe: 3, Moderate: 2, Minor: 1 };
export const sevRank = (s: string | null | undefined) => SEV_RANK[s ?? ""] ?? 0;

export interface WarningView extends WarningIn {
  key: string | null; // translated type key, or null = show the issuer's English
  own: boolean; // matched to the farmer's district
}
/**
 * Warnings to show: still in force at `now`, the farmer's district first, then the rest of the state; within each,
 * most severe first, then latest effective. National-only items are left to the detailed site.
 */
export function pickWarnings(ws: WarningIn[], now: Date = new Date()): { own: WarningView[]; state: WarningView[] } {
  const t = now.getTime();
  const live = ws.filter((w) => {
    if (w.match === "national") return false;
    const exp = w.expires ? Date.parse(w.expires) : NaN;
    return Number.isNaN(exp) || exp > t;
  });
  const order = (a: WarningView, b: WarningView) =>
    sevRank(b.severity) - sevRank(a.severity) || (Date.parse(b.effective ?? "") || 0) - (Date.parse(a.effective ?? "") || 0);
  const v = live.map((w) => ({ ...w, key: eventKey(w.event), own: w.match === "district" }));
  return { own: v.filter((w) => w.own).sort(order), state: v.filter((w) => !w.own).sort(order) };
}

/** Data older than this many hours gets an "old forecast" note. */
export const STALE_HOURS = 6;
export const isStale = (generatedAt: string, now: Date = new Date()) =>
  now.getTime() - Date.parse(generatedAt) > STALE_HOURS * 3600_000;
