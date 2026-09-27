import { config } from "../config";
import type {
  CoreCropList, CoreDashboard, CoreDistrict, CoreEoLayer, CoreFarmerReport, CoreFires, CoreGeoResult, CoreGridField,
  CoreGridMeta, CoreHealth, CoreOfficialWarning, CoreRegionIndia, CoreRegionState, CoreState,
} from "./types";

/** Error from CORE: carries which endpoint failed so the UI shows a source status, never fake data. */
export class CoreApiError extends Error {
  constructor(public endpoint: string, public status: number | null, message: string) {
    super(message);
  }
}

type Params = Record<string, string | number | undefined | null>;

async function get<T>(path: string, params?: Params, opts: { timeoutMs?: number; signal?: AbortSignal } = {}): Promise<T> {
  const q = new URLSearchParams();
  Object.entries(params ?? {}).forEach(([k, v]) => v !== undefined && v !== null && q.set(k, String(v)));
  const url = `${config.coreApiBase}${path}${[...q].length ? `?${q}` : ""}`;
  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), opts.timeoutMs ?? 45000);
  opts.signal?.addEventListener("abort", () => ac.abort());
  try {
    const r = await fetch(url, { signal: ac.signal });
    if (!r.ok) throw new CoreApiError(path, r.status, `CORE ${path} returned HTTP ${r.status}`);
    return (await r.json()) as T;
  } catch (e) {
    if (e instanceof CoreApiError) throw e;
    throw new CoreApiError(path, null, `CORE ${path} unreachable (${(e as Error).name})`);
  } finally {
    clearTimeout(timer);
  }
}

/** URL of a CORE endpoint (for map tile templates and CORE's own export links). */
export const coreUrl = (path: string) => {
  const base = config.coreApiBase.startsWith("http") ? config.coreApiBase : `${location.origin}${config.coreApiBase}`;
  return `${base}${path}`;
};

/** Public static assets published on CORE's website (not /api/v1). Listed in the contract. */
export const coreAsset = (file: "geo/india_districts.geojson" | "geo/india_states.geojson") => `${config.coreSite}${file}`;

/** Read-only access to CORE. V2 never writes to CORE. */
export const core = {
  health: () => get<CoreHealth>("/health"),
  dashboard: (lat: number, lon: number, name?: string, taluka?: string | null, signal?: AbortSignal) =>
    get<CoreDashboard>("/dashboard", { lat, lon, name, taluka }, { signal }),
  search: (q: string, signal?: AbortSignal) => get<CoreGeoResult[]>("/geo/search", { q }, { signal }),
  states: () => get<CoreState[]>("/geo/states"),
  districts: (slug: string) => get<CoreDistrict[]>(`/geo/states/${slug}/districts`),
  crops: () => get<CoreCropList>("/farmer/crops"),
  farmer: (lat: number, lon: number, crop: string, stage: string, name?: string, taluka?: string | null) =>
    get<CoreFarmerReport>("/farmer", { lat, lon, crop, stage, name, taluka }),
  warnings: () => get<CoreOfficialWarning[]>("/warnings", { national: "true" }),
  regionIndia: (metric: string, hours: number) => get<CoreRegionIndia>("/region/india", { metric, hours }, { timeoutMs: 90000 }),
  regionState: (slug: string) => get<CoreRegionState>(`/region/state/${slug}`, undefined, { timeoutMs: 120000 }),
  gridMeta: () => get<CoreGridMeta>("/grid/meta", { source: "gfs" }),
  gridField: (v: string, time?: string) => get<CoreGridField>("/grid/field", { var: v, time, source: "gfs" }),
  earthobsLayers: () => get<CoreEoLayer[]>("/earthobs/layers"),
  fires: () => get<CoreFires>("/earthobs/fires"),
};
