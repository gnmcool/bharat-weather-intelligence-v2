// Verifies that CORE still provides everything V2 depends on (contract/core-api-contract.json).
// For each API endpoint: 1) the path exists in CORE's OpenAPI document; 2) every listed field is
// present with the expected type in a live response. For each public asset: reachable and the
// listed feature properties exist. Read-only GET requests only.
// Field paths: "a.b.c", "list[0].x" (first element), "values.*" (first value of an object).
// Usage: node contract/check-core-contract.mjs [CORE_ORIGIN]
import { readFileSync } from "node:fs";

const origin = (process.argv[2] ?? process.env.BWI_CORE_ORIGIN ?? "https://bharat-weather-intelligence-brown.vercel.app").replace(/\/$/, "");
const contract = JSON.parse(readFileSync(new URL("./core-api-contract.json", import.meta.url), "utf8"));
const typeOf = (v) => (v === null ? "null" : Array.isArray(v) ? "array" : typeof v);
const errors = [];

function resolve(obj, path) {
  let cur = obj;
  for (const raw of path.split(".")) {
    if (cur === null || cur === undefined) return { missing: true };
    const m = raw.match(/^([^[\]]*)(\[0\])?$/);
    const key = m[1];
    if (key === "*") {
      const vals = Object.values(cur);
      if (!vals.length) return { empty: true };
      cur = vals[0];
    } else if (key) {
      if (!(key in cur)) return { missing: true };
      cur = cur[key];
    }
    if (m[2]) {
      if (!Array.isArray(cur)) return { missing: true, why: "not a list" };
      if (!cur.length) return { empty: true };
      cur = cur[0];
    }
  }
  return { value: cur };
}

async function fetchJson(url, timeoutMs = 120000) {
  const r = await fetch(url, { signal: AbortSignal.timeout(timeoutMs) });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

function checkFields(label, body, fields) {
  const before = errors.length;
  let skipped = 0;
  for (const [path, want] of Object.entries(fields)) {
    const res = resolve(body, path);
    if (res.empty) { skipped++; continue; } // empty list/object in this sample: cannot check
    if (res.missing) { errors.push(`${label}: missing "${path}"`); continue; }
    const got = typeOf(res.value);
    if (!want.split("|").includes(got)) errors.push(`${label}: "${path}" is ${got}, expected ${want}`);
  }
  console.log(`  ${errors.length === before ? "ok  " : "FAIL"} ${label}${skipped ? ` (${skipped} fields not present in this sample)` : ""}`);
}

const openapi = await fetchJson(`${origin}/openapi.json`);
for (const ep of contract.endpoints) {
  if (!openapi.paths?.[ep.path]?.get) errors.push(`${ep.path}: not in CORE OpenAPI`);
  let body;
  try { body = await fetchJson(`${origin}${ep.sample}`); } catch (e) { errors.push(`${ep.sample}: ${e.message}`); continue; }
  checkFields(ep.path, body, ep.fields);
}
for (const a of contract.assets ?? []) {
  let body;
  try { body = await fetchJson(a.url); } catch (e) { errors.push(`${a.url}: ${e.message}`); continue; }
  checkFields(a.url.replace(/^https:\/\/[^/]+/, ""), body, a.fields);
}
if (errors.length) {
  console.error(`CORE contract check FAILED against ${origin}:\n - ${errors.join("\n - ")}`);
  process.exit(1);
}
console.log(`CORE contract check passed against ${origin} (${contract.endpoints.length} endpoints, ${(contract.assets ?? []).length} assets).`);
