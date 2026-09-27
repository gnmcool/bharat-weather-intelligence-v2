import { useEffect, useState } from "react";
import { CoreApiError } from "../core-api/client";

// Small request cache so switching screens does not refetch the same CORE response.
// CORE itself caches for several minutes; V2 keeps a response for 5 minutes.
const TTL_MS = 5 * 60 * 1000;
const cache = new Map<string, { at: number; p: Promise<unknown> }>();

export type Loadable<T> =
  | { state: "loading" }
  | { state: "ok"; data: T }
  | { state: "error"; endpoint: string; message: string };

export function cached<T>(key: string, fn: () => Promise<T>): Promise<T> {
  const hit = cache.get(key);
  if (hit && Date.now() - hit.at < TTL_MS) return hit.p as Promise<T>;
  const p = fn();
  cache.set(key, { at: Date.now(), p });
  p.catch(() => cache.delete(key));
  return p;
}

/** Fetch from CORE via the typed client. `key` null = do not fetch yet. */
export function useCore<T>(key: string | null, fn: () => Promise<T>): Loadable<T> {
  const [s, setS] = useState<Loadable<T>>({ state: "loading" });
  useEffect(() => {
    if (!key) return;
    let live = true;
    setS({ state: "loading" });
    cached(key, fn)
      .then((data) => live && setS({ state: "ok", data }))
      .catch((e: unknown) => {
        if (!live) return;
        const err = e instanceof CoreApiError ? e : null;
        setS({ state: "error", endpoint: err?.endpoint ?? key, message: err?.message ?? "Unexpected error" });
      });
    return () => {
      live = false;
    };
  }, [key]); // eslint-disable-line react-hooks/exhaustive-deps
  return s;
}
