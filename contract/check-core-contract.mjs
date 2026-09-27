// Verifies that CORE still provides everything V2 depends on (contract/core-api-contract.json).
// 1) each path exists in CORE's OpenAPI document; 2) each listed field is present with the
// expected type in a live response. Read-only GET requests only.
// Usage: node contract/check-core-contract.mjs [CORE_ORIGIN]
import { readFileSync } from "node:fs";

const origin = (process.argv[2] ?? process.env.BWI_CORE_ORIGIN ?? "https://bharat-weather-intelligence-brown.vercel.app").replace(/\/$/, "");
const contract = JSON.parse(readFileSync(new URL("./core-api-contract.json", import.meta.url), "utf8"));
const typeOf = (v) => (v === null ? "null" : Array.isArray(v) ? "array" : typeof v);
const errors = [];

const openapi = await (await fetch(`${origin}/openapi.json`)).json();
for (const ep of contract.endpoints) {
  if (!openapi.paths?.[ep.path]?.get) errors.push(`${ep.path}: not in CORE OpenAPI`);
  const r = await fetch(`${origin}${ep.sample}`);
  if (!r.ok) { errors.push(`${ep.sample}: HTTP ${r.status}`); continue; }
  let body = await r.json();
  if (ep.list) {
    if (!Array.isArray(body)) { errors.push(`${ep.sample}: expected a list`); continue; }
    if (!body.length) { console.log(`  ${ep.path}: empty list (fields not checked)`); continue; }
    body = body[0];
  }
  const before = errors.length;
  for (const [field, want] of Object.entries(ep.fields)) {
    if (!(field in body)) { errors.push(`${ep.path}: missing field "${field}"`); continue; }
    const got = typeOf(body[field]);
    if (!want.split("|").includes(got)) errors.push(`${ep.path}: "${field}" is ${got}, expected ${want}`);
  }
  console.log(`  ${errors.length === before ? "ok  " : "FAIL"} ${ep.path}`);
}
if (errors.length) {
  console.error(`CORE contract check FAILED against ${origin}:\n - ${errors.join("\n - ")}`);
  process.exit(1);
}
console.log(`CORE contract check passed against ${origin} (${contract.endpoints.length} endpoints).`);
