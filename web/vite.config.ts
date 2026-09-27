import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// V2 consumes CORE read-only:
//  - code: `@core/*` -> ../core/frontend/src (git submodule pinned to a CORE commit; never edited here)
//  - data: CORE's production API (VITE_API_BASE); in dev, /api is proxied to it.
const CORE_API = process.env.BWI_CORE_API ?? "https://bharat-weather-intelligence-brown.vercel.app";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@core": fileURLToPath(new URL("../core/frontend/src", import.meta.url)) } },
  server: {
    host: true,
    port: 5174,
    fs: { allow: [".."] },
    proxy: { "/api": { target: CORE_API, changeOrigin: true } },
  },
  build: { chunkSizeWarningLimit: 1800 },
});
