// V2's own declaration of the CORE /api/v1 fields it uses (CORE baseline core-v1.0).
// Not copied from CORE source: written from CORE's public responses. Every field below is listed
// in contract/core-api-contract.json and checked against CORE's live API (core-contract.yml).
// Add a field here only together with its contract entry.

// ---------- shared ----------
export interface CoreProvenance {
  source: string;
  model: string | null;
  issue_time: string | null;
  retrieved_at: string | null;
  url: string | null;
  licence: string | null;
  notes: string | null;
}

export interface CoreLocation {
  name: string;
  lat: number;
  lon: number;
  state: string | null;
  district: string | null;
  district_id: string | null;
  taluka: string | null;
  elevation_m: number | null;
}

// ---------- /health ----------
export interface CoreHealth {
  status: string;
  time: string;
  earth2studio_store: string | null;
}

// ---------- /dashboard ----------
export interface CoreValue {
  value: number | null;
  unit: string;
}

export interface CoreCurrent {
  time: string; // local time (IST), no offset
  values: Record<string, CoreValue>; // temperature_2m, apparent_temperature, precipitation, relative_humidity_2m, wind_speed_10m, …
  visibility_m: number | null;
  dew_point: number | null;
  terrain: string;
  source: string;
}

export type CoreHourly = { time: string[]; units: Record<string, string> } & Record<string, (number | null)[] | string[] | Record<string, string>>;

export interface CoreModelDay {
  tmax: number | null;
  tmin: number | null;
  precip: number | null;
}

export interface CoreDailyRow {
  date: string;
  weather_code: number | null;
  temperature_2m_max: number | null;
  temperature_2m_min: number | null;
  precipitation_sum: number | null;
  precipitation_probability_max: number | null;
  wind_speed_10m_max: number | null;
  wind_gusts_10m_max: number | null;
  wind_direction_10m_dominant: number | null;
  normal_tmax: number | null;
  normal_tmin: number | null;
  normal_precip: number | null;
  models: Record<string, CoreModelDay> | null; // ecmwf_ifs025, gfs_seamless, icon_seamless
}

/** CORE's `confidence` object. V2 presents it as "Model agreement" (docs/MODEL_AGREEMENT.md). */
export interface CoreConfidence {
  level: "high" | "medium" | "low" | "n/a";
  score: number | null;
  basis: string;
}

export interface CoreRiskItem {
  id: string; // heat, cold, rain, wind, thunderstorm, lightning, flood, drought, fog, fire, cyclone
  label: string;
  level: 0 | 1 | 2 | 3;
  status: string; // No risk / Watch / Alert / Severe
  headline: string;
  explanation: string;
  criterion: string;
  reference: string | null;
  period_start: string | null;
  period_end: string | null;
  peak_value: number | null;
  unit: string | null;
  confidence: CoreConfidence;
  sources: string[];
  official: boolean;
  experimental: boolean;
}

export interface CoreAnomalyItem {
  id: string;
  label: string;
  period: string;
  value: number | null;
  normal: number | null;
  departure: number | null;
  departure_pct: number | null;
  unit: string;
  category: string | null;
  note: string | null;
}

export interface CoreAnomaly {
  baseline: CoreProvenance;
  method: string;
  items: CoreAnomalyItem[];
  dry_spell_days: number | null;
  dry_spell_note: string | null;
}

export interface CoreOfficialWarning {
  id: string;
  headline: string;
  description: string | null;
  event: string | null;
  issuer: string;
  sender: string | null;
  severity: string | null;
  urgency: string | null;
  certainty: string | null;
  effective: string | null;
  expires: string | null;
  area: string | null;
  link: string | null;
  match: "district" | "state" | "national";
  district_ids: string[];
  source: string;
}

export interface CoreDashboard {
  location: CoreLocation;
  generated_at: string;
  timezone: string;
  current: CoreCurrent;
  hourly: CoreHourly;
  daily: CoreDailyRow[];
  anomaly: CoreAnomaly | null;
  risks: CoreRiskItem[];
  warnings: CoreOfficialWarning[];
  sources: CoreProvenance[];
  notices: string[];
}

// ---------- geography ----------
export interface CoreGeoResult {
  name: string;
  lat: number;
  lon: number;
  state: string | null;
  district: string | null;
  taluka: string | null;
  district_id: string | null;
}

export interface CoreState {
  state: string;
  state_slug: string;
  n_districts: number;
}

export interface CoreDistrict {
  id: string;
  district: string;
  lat: number;
  lon: number;
}

// ---------- farmer ----------
export interface CoreCrop {
  id: string;
  label: string;
  season: string;
  stages: string[];
}

export interface CoreCropList {
  validation_status: string;
  crops: CoreCrop[];
}

export interface CoreFarmerIndicator {
  id: string;
  label: string;
  level: number;
  value: string;
  rule: string;
}

export interface CoreFarmerDay {
  date: string;
  tmax: number | null;
  tmin: number | null;
  rain: number | null;
  rain_prob: number | null;
  spray_hours: number | null;
  disease_hours: number | null;
}

export interface CoreFarmerReport {
  crop: string;
  crop_label: string;
  stage: string;
  season: string;
  validation_status: string;
  crop_note: string | null;
  disclaimer: string;
  official: { title: string; note: string; links: { label: string; url: string }[]; integration: string };
  indicators: CoreFarmerIndicator[];
  days: CoreFarmerDay[];
  location: CoreLocation;
  warnings: CoreOfficialWarning[];
  sources: CoreProvenance[];
  notices: string[];
}

// ---------- government ----------
export interface CoreGridMetaLite {
  source: string;
  model: string;
  issue_time: string | null;
  resolution_note: string;
}

export interface CoreRegionIndia {
  metric: string;
  label: string;
  unit: string;
  hours: number;
  values: Record<string, number | null>; // district id -> value
  window: [string, string];
  aggregation: string;
  meta: CoreGridMetaLite;
}

export interface CoreStateDistrictRow {
  id: string;
  district: string;
  terrain: string;
  tmax_7d_max: number | null;
  tmin_7d_min: number | null;
  tmax_anom_7d: number | null;
  rain_7d: number | null;
  rain_7d_normal: number | null;
  rain_30d: number | null;
  rain_30d_normal: number | null;
  rain_30d_pct: number | null;
  rain_30d_cat: string | null;
  gust_max: number | null;
  levels: Record<string, number>;
  max_level: number;
  official_warnings: number;
}

export interface CoreRegionState {
  state: string;
  state_slug: string;
  generated_at: string;
  districts: CoreStateDistrictRow[];
  warnings: CoreOfficialWarning[];
  sources: CoreProvenance[];
  method: string;
  notices: string[];
}

// ---------- map ----------
export interface CoreGridMeta {
  source: string; // "NOAA GFS via Earth2Studio" — or "Open-Meteo (fallback)"
  model: string;
  issue_time: string | null;
  times: string[];
  variables: Record<string, { label: string; unit: string }>;
  bbox: [number, number, number, number]; // W,S,E,N
  nx: number;
  ny: number;
  resolution_note: string;
  notices: string[];
}

/** Values are row-major, south→north rows (ascending latitude), west→east columns. */
export interface CoreGridField {
  var: string;
  time: string;
  nx: number;
  ny: number;
  bbox: [number, number, number, number];
  min: number;
  max: number;
  values: (number | null)[];
  source: string;
  model: string;
  issue_time: string | null;
}

export interface CoreEoLayer {
  id: string;
  label: string;
  tiles: string;
  time: string;
  maxzoom: number;
  opacity: number;
  desc: string;
  legend: string | null;
  cadence: string;
  attribution: string;
}

export interface CoreFires {
  type: "FeatureCollection";
  features: { type: "Feature"; geometry: { type: "Point"; coordinates: [number, number] }; properties: { frp: number; time: string } }[];
  meta: { count: number; latest: string | null; window: string; source: string };
}
