// Single place for V2 runtime configuration (read at build time by Vite).
export const config = {
  /** CORE API base, e.g. "https://bharat-weather-intelligence-brown.vercel.app/api/v1" or "/api/v1" (dev proxy). */
  coreApiBase: ((import.meta.env.VITE_CORE_API_BASE as string | undefined) ?? "/api/v1").replace(/\/$/, ""),
  /** V2 intelligence API base (separate service, api-v2/), e.g. "https://<project>.vercel.app/api/v2" or "/api/v2" (dev proxy). */
  apiV2Base: ((import.meta.env.VITE_API_V2_BASE as string | undefined) ?? "/api/v2").replace(/\/$/, ""),
  appEnv: (import.meta.env.VITE_APP_ENV as string | undefined) ?? (import.meta.env.DEV ? "local" : "preview"),
  /** CORE version V2 was verified against (tag in the CORE repository). */
  coreBaseline: "core-v1.0 (2840f8d)",
  coreSite: "https://gnmcool.github.io/bharat-weather-intelligence/",
} as const;
