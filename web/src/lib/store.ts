import { create } from "zustand";

export type Mode = "citizen" | "farmer" | "government";
export type Screen = "home" | "map" | "risks" | "forecast" | "insights";

export interface Place {
  name: string;
  lat: number;
  lon: number;
  taluka?: string | null;
  district?: string | null;
  state?: string | null;
  /** How the place was chosen: search, gps, map, default */
  via?: string;
}

export const DEFAULT_PLACE: Place = { name: "Ahmedabad", lat: 23.0225, lon: 72.5714, district: "Ahmedabad", state: "Gujarat", via: "default" };

const load = <T,>(k: string, fallback: T): T => {
  try {
    const s = localStorage.getItem(k);
    return s ? (JSON.parse(s) as T) : fallback;
  } catch {
    return fallback;
  }
};
const save = (k: string, v: unknown) => {
  try {
    localStorage.setItem(k, JSON.stringify(v));
  } catch {
    /* storage unavailable: preference is kept for this visit only */
  }
};

interface State {
  place: Place;
  setPlace: (p: Place) => void;
  crop: { crop: string; stage: string } | null;
  setCrop: (c: { crop: string; stage: string } | null) => void;
  govState: string | null; // state slug
  setGovState: (s: string | null) => void;
  /** Evidence drawer target (not persisted). */
  evidence: EvidenceTarget | null;
  openEvidence: (t: EvidenceTarget | null) => void;
}

export interface EvidenceTarget {
  point: { lat: number; lon: number; name?: string | null; taluka?: string | null };
  risk: string;
  /** Optional line explaining where the request came from (e.g. a district count on the map). */
  context?: string;
}

export const useApp = create<State>((set) => ({
  place: load<Place>("bwi2.place", DEFAULT_PLACE),
  setPlace: (place) => {
    save("bwi2.place", place);
    set({ place });
  },
  crop: load<{ crop: string; stage: string } | null>("bwi2.crop", null),
  setCrop: (crop) => {
    save("bwi2.crop", crop);
    set({ crop });
  },
  govState: load<string | null>("bwi2.govState", null),
  setGovState: (govState) => {
    save("bwi2.govState", govState);
    set({ govState });
  },
  evidence: null,
  openEvidence: (evidence) => set({ evidence }),
}));
