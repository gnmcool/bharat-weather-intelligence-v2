// Client for the V2 intelligence API (api-v2/). It is separate from CORE; CORE is never called through it
// for anything the V2 API does not add. Failures carry the endpoint and are shown as such (no substitute data).
import { config } from "../config";
import { CoreApiError } from "../core-api/client";
import type { V2Events, V2Evidence, V2IndiaRisks } from "./types";

type Params = Record<string, string | number | undefined | null>;

async function get<T>(path: string, params?: Params, timeoutMs = 60000): Promise<T> {
  const q = new URLSearchParams();
  Object.entries(params ?? {}).forEach(([k, v]) => v !== undefined && v !== null && q.set(k, String(v)));
  const url = `${config.apiV2Base}${path}${[...q].length ? `?${q}` : ""}`;
  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), timeoutMs);
  try {
    const r = await fetch(url, { signal: ac.signal });
    if (!r.ok) {
      let detail = "";
      try { const j = await r.json(); detail = j?.detail?.core_endpoint ? ` (CORE ${j.detail.core_endpoint} failed)` : ""; } catch { /* not JSON */ }
      throw new CoreApiError(`V2 ${path}`, r.status, `V2 API ${path} returned HTTP ${r.status}${detail}`);
    }
    return (await r.json()) as T;
  } catch (e) {
    if (e instanceof CoreApiError) throw e;
    throw new CoreApiError(`V2 ${path}`, null, `V2 API ${path} unreachable (${(e as Error).name})`);
  } finally {
    clearTimeout(timer);
  }
}

export interface PointRef { lat: number; lon: number; name?: string | null; taluka?: string | null }

export const v2 = {
  events: (p: PointRef) => get<V2Events>("/events", { lat: p.lat, lon: p.lon, name: p.name, taluka: p.taluka }),
  evidence: (p: PointRef, risk: string) => get<V2Evidence>("/evidence", { lat: p.lat, lon: p.lon, name: p.name, taluka: p.taluka, risk }),
  indiaRisks: () => get<V2IndiaRisks>("/region/india/risks", undefined, 180000),
};
