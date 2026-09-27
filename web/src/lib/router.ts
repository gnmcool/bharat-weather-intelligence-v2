import { useEffect, useState } from "react";
import type { Mode, Screen } from "./store";

// Hash routing (#/forecast?mode=farmer&lat=..&lon=..&name=..) so GitHub Pages needs no rewrites.
// lat/lon/name let a view be shared or tested for an exact location.

export const SCREENS: { id: Screen; label: string }[] = [
  { id: "home", label: "Home" },
  { id: "map", label: "Map" },
  { id: "risks", label: "Risks & alerts" },
  { id: "forecast", label: "Forecast" },
  { id: "insights", label: "Insights" },
];
export const MODES: { id: Mode; label: string }[] = [
  { id: "citizen", label: "Citizen" },
  { id: "farmer", label: "Farmer" },
  { id: "government", label: "Government" },
];

export interface Route {
  screen: Screen;
  mode: Mode;
  lat?: number;
  lon?: number;
  name?: string;
}

export function parseHash(h = location.hash): Route {
  const [path, query] = h.replace(/^#\/?/, "").split("?");
  const q = new URLSearchParams(query ?? "");
  const screen = (SCREENS.find((s) => s.id === path)?.id ?? "home") as Screen;
  const mode = (MODES.find((m) => m.id === q.get("mode"))?.id ?? "citizen") as Mode;
  const lat = q.get("lat") ? Number(q.get("lat")) : undefined;
  const lon = q.get("lon") ? Number(q.get("lon")) : undefined;
  return { screen, mode, lat: Number.isFinite(lat) ? lat : undefined, lon: Number.isFinite(lon) ? lon : undefined, name: q.get("name") ?? undefined };
}

export function navigate(to: Partial<Route>) {
  const cur = parseHash();
  const next = { ...cur, ...to };
  const q = new URLSearchParams({ mode: next.mode });
  location.hash = `/${next.screen}?${q}`;
}

export function useRoute(): Route {
  const [r, setR] = useState(parseHash);
  useEffect(() => {
    const h = () => {
      setR(parseHash());
      window.scrollTo({ top: 0 });
    };
    window.addEventListener("hashchange", h);
    return () => window.removeEventListener("hashchange", h);
  }, []);
  return r;
}
