// Types for the parts of CORE's /api/v1 that V2 uses. This is V2's own declaration of the
// boundary, not a copy of CORE's frontend. Every field here is listed in
// contract/core-api-contract.json and checked against CORE's live API by CI (core-contract.yml).
// Add a field here only together with the contract entry.

/** GET /health */
export interface CoreHealth {
  status: string;
  time: string;
  earth2studio_store: string | null;
}

/** GET /grid/meta — gridded forecast metadata (Earth2Studio GFS store, or CORE's coarse fallback). */
export interface CoreGridMeta {
  source: string; // e.g. "NOAA GFS via Earth2Studio" — or "Open-Meteo (fallback)"
  model: string;
  issue_time: string | null; // model run (ISO, UTC)
  times: string[]; // valid times (ISO, UTC)
  resolution_note: string;
}

/** GET /warnings — official CAP alerts (IMD, CWC, SDMA via NDMA SACHET). Shown verbatim, never merged with system output. */
export interface CoreOfficialWarning {
  id: string;
  headline: string;
  issuer: string;
  severity: string | null;
  effective: string | null;
  expires: string | null;
  area: string | null;
  source: string;
}
