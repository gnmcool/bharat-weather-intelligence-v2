// Types for the V2 intelligence API (api-v2/app). Kept in step with api-v2 responses.
import type { CoreAnomalyItem, CoreOfficialWarning, CoreProvenance } from "../core-api/types";

export interface V2Location { name: string; lat: number; lon: number; district: string | null; district_id: string | null; state: string | null; taluka: string | null; elevation_m: number | null }

export interface V2Agreement { assessed: boolean; agreeing: number | null; of: number | null; models?: string[]; text: string; basis: string | null; note: string }

export interface V2Event {
  id: string; type: string; title: string; core_label: string; headline: string; explanation: string;
  severity: { level: number; status: string };
  start: string | null; end: string | null; timing_note: string | null;
  location: V2Location;
  geographic_unit: { kind: "point"; description: string; district_id: string | null };
  classification: "system" | "official"; classification_label: string; experimental: boolean;
  supporting_risk: { id: string; reference: string | null; criterion: string; peak_value: number | null; unit: string | null; source: string };
  model_agreement: V2Agreement;
  sources: string[];
  evidence: string;
}

export type V2OfficialAlert = CoreOfficialWarning & { classification: "official" };
export type V2Anomaly = CoreAnomalyItem & { kind: "departure_from_normal"; baseline: string; baseline_note: string };

export interface V2WhatToKnowItem { priority: number; group: string; kind: "official" | "official_event" | "event" | "anomaly"; ref: string }

export interface V2Events {
  location: V2Location; core_generated_at: string;
  official_alerts: V2OfficialAlert[]; events: V2Event[]; anomalies: V2Anomaly[];
  what_to_know: { items: V2WhatToKnowItem[]; message: string | null; rule: string };
  not_flagged: string[]; sources: CoreProvenance[]; notices: string[];
}

export interface V2ModelValue { value: number | null; days: number }
export interface V2Evidence {
  risk: string; location: V2Location; section_order: string[];
  sections: {
    detected: { title: string; core_label: string; severity: { level: number; status: string }; headline: string; explanation: string; classification: "system" | "official"; classification_label: string; experimental: boolean };
    when: { start: string | null; end: string | null; timing_note: string | null; evidence_window: { start: string | null; end: string | null; dates: string[]; basis: string } };
    model_agreement: V2Agreement;
    forecast_range: { available: boolean; reason?: string; variable?: string; unit?: string; aggregation?: string; dates?: string[]; per_model?: Record<string, V2ModelValue>; min?: number; max?: number; text?: string; note?: string; source?: string };
    normal_departure: {
      available: boolean; reason?: string | null; method?: string;
      baseline: { source: string | null; model: string | null; notes: string | null; label: string };
      core_anomaly_items: CoreAnomalyItem[];
      forecast?: { label: string; value: number; unit: string; dates: string[]; source: string };
      normal?: { value: number; unit: string }; departure?: { value: number; unit: string; pct: number | null }; note?: string;
    };
    earth2studio: { available: boolean; model: string; note: string; reason?: string; variable?: string; unit?: string; value?: number | null; issue_time?: string; valid_from?: string; valid_to?: string; steps?: number; partial?: boolean; partial_note?: string | null; source?: string };
    satellite: { status: string; layers: { id: string; label: string }[]; quantitative: false; note?: string };
    official: { status: "OFFICIAL ALERT" | "NO OFFICIAL ALERT"; alerts: V2OfficialAlert[]; other_alerts_at_location: { id: string; event: string | null; issuer: string }[]; match_note: string; source: string };
    rule: { reference: string | null; criterion: string; data: { peak_value: number | null; unit: string | null }; result: string; note: string };
    provenance: { provider: string | null; model: string | null; run: string | null; run_detail?: string | null; valid: string | null; source: string | null; retrieved_at: string | null; licence?: string | null }[];
  };
}

export interface V2HazardCount {
  id: string; title: string; watch: number; alert: number; severe: number; districts: number; states: number;
  by_state: { state: string; districts: number; watch: number; alert: number; severe: number }[]; rule: string;
}
export interface V2District {
  id: string; district: string; state: string; state_slug: string; lat: number; lon: number; terrain: string | null;
  levels: Record<string, number>; max_level: number; official_alerts: number; values: Record<string, number | string | null>;
}
export interface V2IndiaRisks {
  generated_at: string; core_generated_at: { oldest: string | null; newest: string | null };
  unit: "district"; window: string; classification: "system"; classification_label: string; method: string; levels: string[];
  hazards: V2HazardCount[];
  not_counted: { id: string; title: string; reason: string }[];
  official: { classification: "official"; districts_with_alerts: number; alerts: number; alerts_without_district: number; by_event: { event: string; districts: number }[]; source: string; error: string | null };
  coverage: { states: number; states_failed: { state: string; state_slug: string; expected_districts: number; error: string }[]; districts_expected: number; districts_received: number; complete: boolean };
  districts: V2District[]; limitations: string[]; sources: { provider: string; source: string; note?: string }[];
}
