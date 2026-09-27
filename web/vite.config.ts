import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// V2 talks to CORE only over HTTP (CORE's public /api/v1). No CORE source files are imported.
// Dev: requests to /api are proxied to CORE so the browser sees one origin.
// Production: VITE_CORE_API_BASE is the full CORE API URL (set in .github/workflows/pages.yml).
const CORE_ORIGIN = process.env.BWI_CORE_ORIGIN ?? "https://bharat-weather-intelligence-brown.vercel.app";
// V2 intelligence API (api-v2/, a separate service). Dev: run it locally on :8702 or point BWI_API_V2_ORIGIN at the deployed one.
const API_V2_ORIGIN = process.env.BWI_API_V2_ORIGIN ?? "http://127.0.0.1:8702";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true,
    port: 5174,
    proxy: {
      "/api/v2": { target: API_V2_ORIGIN, changeOrigin: true },
      "/api/v1": { target: CORE_ORIGIN, changeOrigin: true },
    },
  },
  build: { chunkSizeWarningLimit: 1800 },
});
