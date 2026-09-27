import { config } from "../config";
import type { CoreGridMeta, CoreHealth, CoreOfficialWarning } from "./types";

/** Error from CORE: carries which endpoint failed so the UI can show a source status, never fake data. */
export class CoreApiError extends Error {
  constructor(public endpoint: string, public status: number | null, message: string) {
    super(message);
  }
}

async function get<T>(path: string, params?: Record<string, string | number | undefined>, timeoutMs = 20000): Promise<T> {
  const q = new URLSearchParams();
  Object.entries(params ?? {}).forEach(([k, v]) => v !== undefined && q.set(k, String(v)));
  const url = `${config.coreApiBase}${path}${q.size ? `?${q}` : ""}`;
  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), timeoutMs);
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

/** Read-only access to CORE. V2 never writes to CORE. */
export const core = {
  health: () => get<CoreHealth>("/health"),
  gridMeta: () => get<CoreGridMeta>("/grid/meta", { source: "gfs" }),
  warnings: () => get<CoreOfficialWarning[]>("/warnings", { national: "true" }),
};
