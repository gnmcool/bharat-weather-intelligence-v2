// V2 presentation rules for CORE data. Labels and explanations only: levels, values and rules
// come from CORE unchanged (docs/DATA_PROVENANCE.md, docs/MODEL_AGREEMENT.md).
import type { CoreConfidence, CoreOfficialWarning, CoreRiskItem } from "../core-api/types";

/** Display names. Model-only thunderstorm/lightning risks are never shown as observations. */
const RISK_LABEL: Record<string, string> = {
  thunderstorm: "Thunderstorm potential — model derived",
  lightning: "Lightning potential — model derived",
};
export const riskLabel = (r: CoreRiskItem) => RISK_LABEL[r.id] ?? r.label;

export const LEVEL = [
  { name: "No risk", dot: "bg-emerald-400", text: "text-emerald-300", ring: "border-line" },
  { name: "Watch", dot: "bg-amber-300", text: "text-amber-200", ring: "border-amber-400/40" },
  { name: "Alert", dot: "bg-orange-400", text: "text-orange-300", ring: "border-orange-400/50" },
  { name: "Severe", dot: "bg-red-500", text: "text-red-300", ring: "border-red-500/60" },
] as const;

export const SEVERITY: Record<string, { text: string; rank: number }> = {
  Extreme: { text: "text-red-300", rank: 4 },
  Severe: { text: "text-orange-300", rank: 3 },
  Moderate: { text: "text-amber-200", rank: 2 },
  Minor: { text: "text-sky-200", rank: 1 },
};
export const sevRank = (w: CoreOfficialWarning) => SEVERITY[w.severity ?? ""]?.rank ?? 0;

/**
 * Model agreement, from CORE's `confidence` object (API field name kept for CORE compatibility).
 * CORE's basis text states "k of n models …"; V2 shows that count rather than a confidence word.
 */
export function modelAgreement(c: CoreConfidence): { short: string; detail: string; applicable: boolean } {
  const m = c.basis.match(/(\d+) of (\d+) models?/);
  if (c.level === "n/a" || !m) {
    return { short: "Model agreement: not applicable", detail: c.basis, applicable: false };
  }
  return {
    short: `Model agreement: ${m[1]} of ${m[2]}`,
    detail: c.basis,
    applicable: true,
  };
}

export const AGREEMENT_EXPLAINER =
  "How many of the independent forecast models (ECMWF, GFS, ICON) reach the same risk level within a day of the peak. " +
  "It describes agreement between models, not a probability. Earth2Studio GFS and FourCastNet are not counted separately because they are GFS.";

/** Items for "What should you know?" — existing CORE data only, no new detection. */
export function whatToKnow(risks: CoreRiskItem[], warnings: CoreOfficialWarning[]) {
  const official = [...warnings].sort((a, b) => sevRank(b) - sevRank(a));
  const system = risks.filter((r) => r.level >= 1 && !r.official).sort((a, b) => b.level - a.level);
  const officialRisk = risks.filter((r) => r.official && r.level >= 1); // e.g. CORE cyclone item built from an IMD alert
  return { official, officialRisk, system };
}
