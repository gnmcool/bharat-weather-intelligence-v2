// CORE vs V2 data-integrity check (M1 acceptance test).
//
// For each test location it opens the CORE website and the V2 website in a real browser,
// captures the CORE API response each site received, and checks:
//   A. same data  — V2 and CORE received the same CORE data (values, risks, alerts, model runs)
//   B. V2 display — what V2 shows equals the data it received (display rounding only)
//   C. CORE display — what CORE shows equals the same data (CORE rounds to whole degrees)
// plus Farmer (/farmer) and Government (/region/state, /region/india) responses.
//
// Usage:  node tools/compare/compare.mjs [V2_URL] [CORE_SITE_URL] [--json out.json]
// Needs Playwright:  npm i -D playwright && npx playwright install chromium
// (or set PLAYWRIGHT_CHROMIUM to an existing Chromium executable).

import { writeFileSync } from "node:fs";

const args = process.argv.slice(2);
const jsonOut = args.includes("--json") ? args[args.indexOf("--json") + 1] : null;
const pos = args.filter((a, i) => !a.startsWith("--") && args[i - 1] !== "--json");
const V2 = pos[0] ?? "https://gnmcool.github.io/bharat-weather-intelligence-v2/";
const CORE = pos[1] ?? "https://gnmcool.github.io/bharat-weather-intelligence/";
const API = process.env.CORE_API ?? "https://bharat-weather-intelligence-brown.vercel.app/api/v1";

let chromium;
try {
  ({ chromium } = await import("playwright"));
} catch {
  ({ chromium } = await import(process.env.PLAYWRIGHT_MODULE ?? "/opt/node-tools/node_modules/playwright/index.mjs"));
}

const LOCATIONS = [
  { name: "Ahmedabad", lat: 23.0225, lon: 72.5714, why: "plains, Gujarat (pilot)" },
  { name: "Shimla", lat: 31.1048, lon: 77.1734, why: "hills (terrain class differs)" },
  { name: "Chennai", lat: 13.0827, lon: 80.2707, why: "coastal" },
  { name: "Guwahati", lat: 26.1445, lon: 91.7362, why: "north-east, active alerts likely" },
];
const FARMER = { crop: "cotton", stage: "flowering" };
const GOV_STATE = "gujarat";

const results = [];
const check = (loc, group, name, ok, detail = "") => results.push({ loc, group, name, ok: !!ok, detail });
const eqNum = (a, b, tol = 0) => a === b || (a !== null && b !== null && Math.abs(a - b) <= tol + 1e-9);
const fixed = (v, d) => (v === null || v === undefined ? "—" : Number(v).toFixed(d));

const browser = await chromium.launch(process.env.PLAYWRIGHT_CHROMIUM ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM } : {});

async function openCapture(url, init, match) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  if (init) await ctx.addInitScript(init.fn, init.arg);
  const page = await ctx.newPage();
  const got = {};
  page.on("response", async (r) => {
    for (const [key, re] of Object.entries(match)) if (re.test(r.url()) && r.request().method() === "GET" && r.ok()) {
      try { got[key] = await r.json(); } catch { /* not JSON */ }
    }
  });
  await page.goto(url, { waitUntil: "networkidle", timeout: 180000 }).catch(() => {});
  return { ctx, page, got };
}

async function waitFor(got, key, ms = 90000) {
  const t0 = Date.now();
  while (!got[key] && Date.now() - t0 < ms) await new Promise((r) => setTimeout(r, 500));
  return got[key];
}

const cv = (d, k) => d.current.values[k]?.value ?? null;

for (const L of LOCATIONS) {
  const q = `lat=${L.lat}&lon=${L.lon}&name=${encodeURIComponent(L.name)}`;
  // ---------- V2 ----------
  const v2 = await openCapture(`${V2}#/home?mode=citizen&${q}`, null, { dash: /\/dashboard\?/ });
  const dV2 = await waitFor(v2.got, "dash");
  await v2.page.waitForSelector('[data-testid="cur-temp"]', { timeout: 60000 }).catch(() => {});
  const v2Home = await v2.page.evaluate(() => Object.fromEntries(["cur-temp", "cur-feels", "cur-rain", "cur-rh", "cur-wind", "cur-msl"].map((id) => [id, document.querySelector(`[data-testid="${id}"]`)?.textContent?.replace("°", "") ?? null])));
  await v2.page.evaluate(() => { location.hash = "/risks?mode=citizen"; });
  await v2.page.waitForSelector('[data-testid="system-risk"]', { timeout: 60000 }).catch(() => {});
  const v2Risks = await v2.page.evaluate(() => [...document.querySelectorAll('[data-testid="risk-list"] [data-testid="system-risk"]')].map((e) => ({ id: e.getAttribute("data-risk-id"), level: Number(e.getAttribute("data-risk-level")), status: e.querySelector('[data-testid="risk-status"]')?.textContent })));
  const v2Alerts = await v2.page.evaluate(() => [...document.querySelectorAll('main [data-testid="official-alert"]')].map((e) => e.getAttribute("data-alert-id")));
  await v2.page.evaluate(() => { location.hash = "/forecast?mode=citizen"; });
  await v2.page.waitForSelector('[data-testid="daily-row"]', { timeout: 60000 }).catch(() => {});
  const v2Daily = await v2.page.evaluate(() => [...document.querySelectorAll('[data-testid="daily-row"]')].map((r) => ({ date: r.getAttribute("data-date"), cells: [...r.querySelectorAll("td")].map((td) => td.textContent.trim()) })));
  const v2Hourly = await v2.page.evaluate(() => [...document.querySelectorAll('[data-testid="hourly-table"] tbody tr')].map((r) => [...r.querySelectorAll("td")].map((td) => td.textContent.trim())));
  await v2.ctx.close();

  // ---------- CORE ----------
  const coreSite = await openCapture(`${CORE}?mode=citizen`, { fn: (p) => localStorage.setItem("bwi.place", JSON.stringify(p)), arg: { name: L.name, lat: L.lat, lon: L.lon } }, { dash: /\/dashboard\?/ });
  const dCore = await waitFor(coreSite.got, "dash");
  await coreSite.page.waitForTimeout(3000);
  const coreText = await coreSite.page.evaluate(() => document.querySelector("aside")?.innerText ?? "");
  await coreSite.ctx.close();

  if (!dV2 || !dCore) { check(L.name, "A", "both sites received /dashboard", false, `V2 ${!!dV2}, CORE ${!!dCore}`); continue; }

  // A — same data
  // CORE builds a fresh dashboard per request, so generated_at differs by the seconds between the two
  // page loads; the data inside is what must match (checked field by field below).
  const gap = Math.abs(Date.parse(dV2.generated_at) - Date.parse(dCore.generated_at)) / 1000;
  check(L.name, "A", "responses fetched close together", gap < 300, `generated ${gap.toFixed(0)} s apart (${dV2.generated_at} / ${dCore.generated_at})`);
  for (const k of ["temperature_2m", "apparent_temperature", "precipitation", "relative_humidity_2m", "wind_speed_10m", "wind_gusts_10m", "pressure_msl"])
    check(L.name, "A", `current ${k}`, eqNum(cv(dV2, k), cv(dCore, k)), `${cv(dV2, k)} vs ${cv(dCore, k)}`);
  check(L.name, "A", "48-hour series (temperature, rain, wind)", ["temperature_2m", "precipitation", "wind_speed_10m"].every((k) => JSON.stringify(dV2.hourly[k]) === JSON.stringify(dCore.hourly[k])) && JSON.stringify(dV2.hourly.time) === JSON.stringify(dCore.hourly.time), `${dV2.hourly.time.length} hours`);
  check(L.name, "A", "10-day series (max, min, rain, models)", JSON.stringify(dV2.daily.map((r) => [r.date, r.temperature_2m_max, r.temperature_2m_min, r.precipitation_sum, r.models])) === JSON.stringify(dCore.daily.map((r) => [r.date, r.temperature_2m_max, r.temperature_2m_min, r.precipitation_sum, r.models])), `${dV2.daily.length} days`);
  check(L.name, "A", "risks (id, level, status, model agreement)", JSON.stringify(dV2.risks.map((r) => [r.id, r.level, r.status, r.confidence])) === JSON.stringify(dCore.risks.map((r) => [r.id, r.level, r.status, r.confidence])), `${dV2.risks.length} risks`);
  check(L.name, "A", "official alerts", JSON.stringify(dV2.warnings.map((w) => w.id).sort()) === JSON.stringify(dCore.warnings.map((w) => w.id).sort()), `${dV2.warnings.length} alerts`);
  check(L.name, "A", "provenance / model runs", JSON.stringify(dV2.sources.map((s) => [s.source, s.model, s.issue_time, s.notes])) === JSON.stringify(dCore.sources.map((s) => [s.source, s.model, s.issue_time, s.notes])), (dV2.sources.find((s) => s.issue_time)?.notes ?? "").slice(0, 120));

  // B — V2 shows exactly what it received
  const d = dV2;
  const pairs = [["cur-temp", cv(d, "temperature_2m"), 1], ["cur-feels", cv(d, "apparent_temperature"), 1], ["cur-rain", cv(d, "precipitation"), 1], ["cur-rh", cv(d, "relative_humidity_2m"), 0], ["cur-wind", cv(d, "wind_speed_10m"), 0], ["cur-msl", cv(d, "pressure_msl"), 0]];
  for (const [id, val, dg] of pairs) check(L.name, "B", `V2 shows ${id}`, v2Home[id] === fixed(val, dg), `shown ${v2Home[id]}, data ${val}`);
  const expRisks = [...d.risks].sort((a, b) => b.level - a.level).map((r) => ({ id: r.id, level: r.level, status: r.status }));
  check(L.name, "B", "V2 shows all 11 risks with CORE levels and status", JSON.stringify(v2Risks) === JSON.stringify(expRisks), `${v2Risks.length} shown`);
  check(L.name, "B", "V2 shows the location's official alerts", JSON.stringify([...v2Alerts].sort()) === JSON.stringify(d.warnings.map((w) => w.id).sort()), `${v2Alerts.length} shown`);
  const dailyOk = d.daily.every((r, i) => v2Daily[i]?.date === r.date && v2Daily[i].cells[2] === `${fixed(r.temperature_2m_max, 0)} / ${fixed(r.temperature_2m_min, 0)}` && v2Daily[i].cells[5] === fixed(r.precipitation_sum, 1));
  check(L.name, "B", "V2 10-day table = data", dailyOk, `${v2Daily.length} rows`);
  const hourlyOk = v2Hourly.every((row, k) => row[2] === fixed(d.hourly.temperature_2m[k * 3], 1) && row[4] === fixed(d.hourly.precipitation[k * 3], 1));
  check(L.name, "B", "V2 48-hour table = data", hourlyOk && v2Hourly.length === 16, `${v2Hourly.length} rows (every 3rd hour)`);

  // C — CORE shows the same data (CORE rounds temperatures to whole degrees)
  const ct = coreText;
  const tMatch = ct.match(/\n(-?\d+)°\n/);
  check(L.name, "C", "CORE shows current temperature", tMatch && Math.abs(Number(tMatch[1]) - cv(dCore, "temperature_2m")) <= 0.5, `CORE shows ${tMatch?.[1]}°, data ${cv(dCore, "temperature_2m")}`);
  const fMatch = ct.match(/Feels (-?\d+)°/);
  check(L.name, "C", "CORE shows feels-like", fMatch && Math.abs(Number(fMatch[1]) - cv(dCore, "apparent_temperature")) <= 0.5, `CORE shows ${fMatch?.[1]}°, data ${cv(dCore, "apparent_temperature")}`);
  // CORE's page orders risks by severity, so compare the statuses as a set.
  const statuses = dCore.risks.map((r) => r.status).sort();
  const coreStatuses = [...ct.matchAll(/\n(No risk|Watch|Alert|Severe)\n/g)].map((m) => m[1]).slice(0, statuses.length);
  check(L.name, "C", "CORE shows the same risk statuses", JSON.stringify([...coreStatuses].sort()) === JSON.stringify(statuses), coreStatuses.join(", "));
}

// ---------- Farmer ----------
{
  const L = LOCATIONS[0];
  const init = { fn: (a) => { localStorage.setItem("bwi2.crop", JSON.stringify(a.crop)); localStorage.setItem("bwi2.place", JSON.stringify(a.place)); }, arg: { crop: FARMER, place: { name: L.name, lat: L.lat, lon: L.lon, via: "test" } } };
  const v2 = await openCapture(`${V2}#/home?mode=farmer`, init, { farmer: /\/farmer\?/ });
  const got = await waitFor(v2.got, "farmer");
  await v2.page.waitForSelector('[data-testid="farmer-indicator"]', { timeout: 60000 }).catch(() => {});
  const shown = await v2.page.evaluate(() => [...document.querySelectorAll('[data-testid="farmer-indicator"]')].map((e) => [e.getAttribute("data-id"), Number(e.getAttribute("data-level"))]));
  const sep = await v2.page.evaluate(() => { const a = document.querySelector('[data-testid="official-advisory"]'); const b = document.querySelector('[data-testid="farmer-indicators"]'); return !!a && !!b && !a.contains(b) && !b.contains(a); });
  await v2.ctx.close();
  const direct = await (await fetch(`${API}/farmer?crop=${FARMER.crop}&stage=${FARMER.stage}&lat=${L.lat}&lon=${L.lon}&name=${L.name}`)).json();
  check("Farmer (Ahmedabad, cotton, flowering)", "A", "V2 received CORE /farmer data", got && JSON.stringify(got.indicators) === JSON.stringify(direct.indicators) && JSON.stringify(got.days) === JSON.stringify(direct.days), got ? `${got.indicators.length} indicators, ${got.days.length} days` : "no response");
  check("Farmer (Ahmedabad, cotton, flowering)", "B", "V2 shows every indicator with CORE level", got && JSON.stringify(shown) === JSON.stringify(got.indicators.map((i) => [i.id, i.level])), `${shown.length} shown`);
  check("Farmer (Ahmedabad, cotton, flowering)", "B", "Official advisory and system indicators are separate blocks", sep);
}

// ---------- Government ----------
{
  const init = { fn: (s) => localStorage.setItem("bwi2.govState", JSON.stringify(s)), arg: GOV_STATE };
  const v2 = await openCapture(`${V2}#/home?mode=government`, init, { state: /\/region\/state\/[a-z-]+$/, india: /\/region\/india\?/ });
  const st = await waitFor(v2.got, "state", 150000);
  const india = await waitFor(v2.got, "india", 60000);
  await v2.page.waitForSelector('[data-testid="state-table"] tbody tr', { timeout: 60000 }).catch(() => {});
  const rows = await v2.page.evaluate(() => [...document.querySelectorAll('[data-testid="state-table"] tbody tr')].map((r) => [r.getAttribute("data-district"), ...[...r.querySelectorAll("td")].slice(1).map((td) => td.textContent.trim())]));
  const hot = await v2.page.evaluate(() => [...document.querySelectorAll('[data-testid="hotspots"] [data-district]')].map((e) => [e.getAttribute("data-district"), e.textContent.trim()]));
  await v2.ctx.close();
  const dState = await (await fetch(`${API}/region/state/${GOV_STATE}`)).json();
  const dIndia = await (await fetch(`${API}/region/india?metric=rain&hours=72`)).json();
  const G = "Government (Gujarat / India)";
  check(G, "A", "V2 received CORE /region/state data", st && JSON.stringify(st.districts) === JSON.stringify(dState.districts), st ? `${st.districts.length} districts` : "no response");
  check(G, "A", "V2 received CORE /region/india data", india && JSON.stringify(india.values) === JSON.stringify(dIndia.values), india ? `${Object.keys(india.values).length} districts` : "no response");
  if (st) {
    const byId = Object.fromEntries(st.districts.map((r) => [r.id, r]));
    const ok = rows.length === st.districts.length && rows.every(([id, , tmax, , rain]) => byId[id] && tmax === fixed(byId[id].tmax_7d_max, 1) && rain === fixed(byId[id].rain_7d, 1));
    check(G, "B", "V2 district table = data (max temp, 7-day rain)", ok, `${rows.length} rows`);
  }
  if (india) {
    const ok = hot.length === 10 && hot.every(([id, txt]) => txt.startsWith(fixed(india.values[id], 1)));
    check(G, "B", "V2 top-10 hotspots = data", ok, hot.slice(0, 3).map(([id, t]) => `${id} ${t}`).join("; "));
  }
}

await browser.close();

// ---------- report ----------
const byLoc = {};
for (const r of results) (byLoc[r.loc] ??= []).push(r);
let failed = 0;
for (const [loc, rs] of Object.entries(byLoc)) {
  console.log(`\n## ${loc}`);
  for (const r of rs) {
    if (!r.ok) failed++;
    console.log(`${r.ok ? "PASS" : "FAIL"}  [${r.group}] ${r.name}${r.detail ? `  — ${r.detail}` : ""}`);
  }
}
console.log(`\n${results.length - failed}/${results.length} checks passed. A = same data, B = V2 display, C = CORE display.`);
if (jsonOut) writeFileSync(jsonOut, JSON.stringify({ at: new Date().toISOString(), V2, CORE, results }, null, 2));
process.exit(failed ? 1 : 0);
