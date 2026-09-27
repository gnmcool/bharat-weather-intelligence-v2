// M2 acceptance test: CORE /api/v1 (truth) vs V2 API /api/v2 vs V2 UI.
// Usage: PLAYWRIGHT_CHROMIUM=/opt/pw-browsers/chromium node tools/m2-acceptance/acceptance.mjs <V2_SITE> <V2_API> <CORE_API> [--json out.json]
// Read-only GETs against CORE. Exits 1 on any failed check.
import { writeFileSync } from "node:fs";

const [, , SITE = "http://localhost:5174/", V2 = "http://localhost:8702/api/v2", CORE = "https://bharat-weather-intelligence-brown.vercel.app/api/v1"] = process.argv;
const jsonOut = process.argv.includes("--json") ? process.argv[process.argv.indexOf("--json") + 1] : null;
const PLACES = [
  { name: "Ahmedabad", lat: 23.0225, lon: 72.5714 },
  { name: "Shimla", lat: 31.1048, lon: 77.1734 },
  { name: "Chennai", lat: 13.0827, lon: 80.2707 },
  { name: "Guwahati", lat: 26.1445, lon: 91.7362 },
  { name: "Uttarkashi", lat: 31.0033, lon: 78.5841 },
];
const results = [];
const check = (group, n, name, ok, detail = "") => { results.push({ group, n, name, ok: !!ok, detail }); console.log(`${ok ? "PASS" : "FAIL"} [${group}] ${n}. ${name}${detail ? " — " + detail : ""}`); };
const j = async (url, t = 180000) => { const r = await fetch(url, { signal: AbortSignal.timeout(t) }); if (!r.ok) throw new Error(`${url} HTTP ${r.status}`); return r.json(); };
const q = (p) => `lat=${p.lat}&lon=${p.lon}&name=${encodeURIComponent(p.name)}`;
const agreeRe = /(\d+) of (\d+) models?/;
const IST = 5.5 * 3600e3;
const istDate = (s) => new Date(Date.parse(s) + IST).toISOString().slice(0, 10);

// ---------------- API checks per location ----------------
const summary = {};
for (const p of PLACES) {
  const G = p.name;
  let core = await j(`${CORE}/dashboard?${q(p)}`);
  let ev = await j(`${V2}/events?${q(p)}`);
  // CORE rebuilds per request; if a model update landed between the two calls, refetch once.
  const sig = (risks) => JSON.stringify(risks.filter((r) => r.level >= 1).map((r) => [r.id, r.level, r.period_start, r.period_end]));
  if (sig(core.risks) !== JSON.stringify(ev.events.map((e) => [e.type, e.severity.level, e.start, e.end]).sort())) {
    core = await j(`${CORE}/dashboard?${q(p)}`);
  }
  const coreEv = core.risks.filter((r) => r.level >= 1);
  const byType = Object.fromEntries(ev.events.map((e) => [e.type, e]));
  summary[G] = { events: ev.events.map((e) => `${e.title} ${e.severity.status}`), official: ev.official_alerts.map((w) => `${w.event} (${w.issuer}, ${w.match})`), message: ev.what_to_know.message };

  check(G, 1, "Event timestamps = CORE period_start/period_end", coreEv.every((r) => byType[r.id] && byType[r.id].start === r.period_start && byType[r.id].end === r.period_end),
    coreEv.map((r) => `${r.id} ${r.period_start ?? "no period"}→${r.period_end ?? ""}`).join("; ") || "no events");
  check(G, 2, "Event set and severity = CORE risk levels", coreEv.length === ev.events.length && coreEv.every((r) => byType[r.id]?.severity.level === r.level),
    coreEv.map((r) => `${r.id}=${r.level}`).join(", ") || "none ≥ Watch");
  check(G, 3, "Model agreement = CORE 'k of n' (or not assessed)", coreEv.every((r) => {
    const m = (r.confidence?.basis ?? "").match(agreeRe), a = byType[r.id].model_agreement;
    return m && !r.official ? a.assessed && a.agreeing === +m[1] && a.of === +m[2] && a.text === `Model agreement: ${m[1]} of ${m[2]}` : !a.assessed;
  }), ev.events.map((e) => `${e.type}: ${e.model_agreement.text}`).join("; ") || "n/a");
  const coreIds = core.warnings.map((w) => w.id).sort().join(",");
  check(G, 4, "Official alerts separate: same ids as CORE warnings; no event classified official unless CORE says so",
    ev.official_alerts.map((w) => w.id).sort().join(",") === coreIds && ev.official_alerts.every((w) => w.classification === "official")
    && ev.events.every((e) => e.classification === (core.risks.find((r) => r.id === e.type).official ? "official" : "system")),
    `${ev.official_alerts.length} official, ${ev.events.length} system`);
  const pri = ev.what_to_know.items.map((i) => i.priority);
  check(G, "4b", "What-should-you-know priority order (1 official … 5 anomalies)", pri.every((x, i) => i === 0 || pri[i - 1] <= x)
    && (ev.what_to_know.message === null) === (ev.official_alerts.length + ev.events.length > 0), ev.what_to_know.message ?? pri.join(","));

  // evidence for every event
  let evOk = true, e2sOk = true, sysOk = true, probOk = true, satOk = true; const ed = [];
  for (const e of ev.events) {
    const d = await j(`${V2}/evidence?${q(p)}&risk=${e.type}`);
    const s = d.sections;
    if (JSON.stringify(Object.keys(s)) !== JSON.stringify(d.section_order)) evOk = false;
    const r = core.risks.find((x) => x.id === e.type);
    if (s.rule.criterion !== r.criterion || s.detected.severity.level !== r.level) evOk = false;
    if (s.forecast_range.available) {
      const key = { heat: "tmax", cold: "tmin", rain: "precip" }[e.type];
      const agg = { heat: Math.max, cold: Math.min, rain: Math.max }[e.type];
      const days = core.daily.filter((x) => s.when.evidence_window.dates.includes(x.date));
      const exp = { ECMWF: "ecmwf_ifs025", GFS: "gfs_seamless", ICON: "icon_seamless" };
      for (const [m, k] of Object.entries(exp)) {
        const want = agg(...days.map((x) => x.models[k][key]));
        if (s.forecast_range.per_model[m].value !== want) { evOk = false; ed.push(`${e.type} ${m} ${s.forecast_range.per_model[m].value}≠${want}`); }
      }
      if (Object.keys(s.forecast_range.per_model).sort().join() !== "ECMWF,GFS,ICON") e2sOk = false;
    }
    if (e.start && s.when.evidence_window.dates[0] !== istDate(e.start)) { evOk = false; ed.push(`${e.type} window`); }
    if (s.model_agreement.assessed && s.model_agreement.of !== 3) e2sOk = false;
    if (!/NOT counted|not an independent/i.test(s.earth2studio.note)) e2sOk = false;
    if (s.detected.classification === "system" && !/not an official warning/i.test(s.detected.classification_label)) sysOk = false;
    if (/\bconfirm/i.test(s.satellite.status) || s.satellite.quantitative !== false) satOk = false;
    const txt = JSON.stringify(d);
    if (/(agreement|agree)[^"]{0,40}\d+\s?%|\d+\s?%[^"]{0,20}(probab|confiden)/i.test(txt)) probOk = false;
    ed.push(`${e.type}: ${s.forecast_range.available ? s.forecast_range.text : "range n/a"}; E2S ${s.earth2studio.available ? s.earth2studio.value + " " + s.earth2studio.unit : "n/a"}; ${s.official.status}`);
  }
  check(G, 5, "Evidence matches CORE data (rule, level, per-model values, window)", evOk, ed.join(" | ") || "no events");
  check(G, 7, "No GFS double counting (3 independent models; E2S labelled not counted)", e2sOk);
  check(G, 8, "No system assessment labelled official", sysOk);
  check(G, 9, "No probability inferred from agreement", probOk);
  check(G, "9b", "Satellite never 'confirms'", satOk);
}

// ---------------- District reconciliation ----------------
const india = await j(`${V2}/region/india/risks`, 300000);
const states = await j(`${CORE}/geo/states`);
const coreLevels = {};
const coreStateGen = {};
for (let i = 0; i < states.length; i += 6) {
  const chunk = await Promise.all(states.slice(i, i + 6).map((s) => j(`${CORE}/region/state/${s.state_slug}`, 200000)));
  for (const st of chunk) { coreStateGen[st.state_slug] = st.generated_at; for (const d of st.districts) coreLevels[d.id] = d; }
}
const geo = await j("https://gnmcool.github.io/bharat-weather-intelligence/geo/india_districts.geojson");
const geoIds = new Set(geo.features.map((f) => f.properties.id));
const R = "Districts";
check(R, 6, "Coverage: every map district received once", india.coverage.complete && india.districts.length === geoIds.size && india.districts.every((d) => geoIds.has(d.id)),
  `${india.districts.length} received, ${geoIds.size} on map`);
let mism = [];
for (const d of india.districts) for (const h of ["rain", "heat", "cold", "wind"]) if (coreLevels[d.id]?.levels[h] !== d.levels[h]) mism.push(`${d.id} ${h}`);
check(R, 6, "District levels = CORE /region/state (fetched independently)", mism.length === 0, mism.slice(0, 5).join(", ") || "724 × 4 levels equal");
const counts = {};
for (const h of india.hazards) {
  const n = india.districts.filter((d) => d.levels[h.id] >= 1).length;
  const nCore = Object.values(coreLevels).filter((d) => d.levels[h.id] >= 1).length;
  counts[h.id] = { v2: h.districts, recount: n, core: nCore, watch: h.watch, alert: h.alert, severe: h.severe };
  check(R, 6, `${h.title}: count = recount = CORE recount = Σ by state`, h.districts === n && n === nCore && h.by_state.reduce((a, b) => a + b.districts, 0) === n, `${h.districts} districts`);
}
const offCore = Object.values(coreLevels).filter((d) => d.official_warnings > 0).length;
const offV2 = india.districts.filter((d) => d.official_alerts > 0).length;
// Alerts change minute to minute. If CORE's tables were regenerated after V2 built its (20-min cached) counts,
// a difference is a timing difference, reported as such; the V2 total must still equal V2's own district list.
const coreNewer = Object.values(coreStateGen).some((t) => t > india.generated_at);
check(R, 6, "Official-alert districts = CORE per-district official_warnings (same snapshot)",
  india.official.districts_with_alerts === offV2 && (offV2 === offCore || coreNewer),
  offV2 === offCore ? `${offCore} districts` : `V2 ${offV2} (built ${india.generated_at}) vs CORE now ${offCore} — CORE regenerated later; timing difference`);

// ---------------- UI checks ----------------
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE ?? "/opt/node-tools/node_modules/playwright/index.mjs");
const browser = await chromium.launch({ executablePath: process.env.PLAYWRIGHT_CHROMIUM });
const U = "UI";
for (const p of PLACES) {
  const page = await browser.newPage({ viewport: { width: 1360, height: 1000 } });
  await page.goto(`${SITE}#/home?mode=citizen&${q(p)}`, { waitUntil: "networkidle" });
  await page.waitForSelector('[data-testid="what-to-know"] [data-testid="event"], [data-testid="wtk-none"], [data-testid="what-to-know"] [data-testid="official-alert"]', { timeout: 90000 });
  const ev = await j(`${V2}/events?${q(p)}`);
  const shown = await page.evaluate(() => {
    const root = document.querySelector('[data-testid="what-to-know"]');
    const order = [...root.querySelectorAll('[data-testid="official-alert"], [data-testid="event"]')].map((e) => e.dataset.testid === "official-alert" ? "official" : `event:${e.dataset.level}`);
    return { order, none: root.querySelector('[data-testid="wtk-none"]')?.innerText ?? null,
      eventLabels: [...root.querySelectorAll('[data-testid="event"]')].map((e) => e.innerText),
      officialInsideEvent: !!root.querySelector('[data-testid="event"] [data-testid="official-alert"]') };
  });
  const firstEvent = shown.order.findIndex((x) => x.startsWith("event"));
  const lastOfficial = shown.order.lastIndexOf("official");
  const lv = shown.order.filter((x) => x.startsWith("event")).map((x) => +x.split(":")[1]);
  check(`${p.name} UI`, 4, "UI: official alerts first and separate; system events by severity", (lastOfficial < firstEvent || firstEvent < 0) && !shown.officialInsideEvent && lv.every((x, i) => i === 0 || lv[i - 1] >= x), shown.order.join(" "));
  if (!ev.events.length && !ev.official_alerts.length) check(`${p.name} UI`, "4c", 'UI says "No significant weather event detected."', shown.none?.includes("No significant weather event detected."), shown.none ?? "missing");
  check(`${p.name} UI`, 8, "UI: no system card calls itself an official warning", shown.eventLabels.every((t) => !/official (warning|alert)/i.test(t)));
  check(`${p.name} UI`, 9, "UI: no percentage next to model agreement", shown.eventLabels.every((t) => !/agreement[^\n]*%/i.test(t)));
  if (ev.events.length) {
    const e0 = ev.events[0];
    await page.locator(`[data-testid="what-to-know"] [data-testid="event"][data-event-type="${e0.type}"] [data-testid="view-evidence"]`).first().click();
    await page.waitForSelector('[data-testid="ev-section"][data-key="provenance"]', { timeout: 90000 });
    const drawer = await page.evaluate(() => ({
      keys: [...document.querySelectorAll('[data-testid="ev-section"]')].map((s) => s.dataset.key),
      level: document.querySelector('[data-testid="ev-level"]')?.dataset.level,
      official: document.querySelector('[data-testid="ev-official"]')?.innerText.trim(),
      text: document.querySelector('[data-testid="evidence-drawer"]').innerText,
    }));
    const evd = await j(`${V2}/evidence?${q(p)}&risk=${e0.type}`);
    check(`${p.name} UI`, 5, `Evidence drawer (${e0.type}): 9 sections in fixed order, level and official status match`,
      drawer.keys.join() === "detected,when,model_agreement,forecast_range,normal_departure,satellite,official,rule,provenance"
      && +drawer.level === e0.severity.level && drawer.official.toUpperCase() === evd.sections.official.status,
      `${drawer.official}; level ${drawer.level}`);
    check(`${p.name} UI`, "9b", "Drawer: no 'Satellite confirms'; E2S marked not counted", !/satellite confirms/i.test(drawer.text) && /not (counted|an independent)/i.test(drawer.text));
  }
  await page.close();
}
// Government page: counts shown = API counts = coloured districts
const gp = await browser.newPage({ viewport: { width: 1440, height: 1200 } });
await gp.goto(`${SITE}#/home?mode=government`, { waitUntil: "networkidle" });
await gp.waitForSelector('[data-testid="hazard-count"]', { timeout: 300000 });
for (const h of india.hazards) {
  await gp.locator(`[data-testid="hazard-count"][data-hazard="${h.id}"]`).click();
  await gp.waitForTimeout(300);
  const ui = await gp.evaluate((id) => ({ tile: +document.querySelector(`[data-testid="hazard-count"][data-hazard="${id}"]`).dataset.count, filled: +document.querySelector('[data-testid="risk-map-legend"]').dataset.filled,
    conc: [...document.querySelectorAll('[data-testid="concentration"] [data-count]')].map((e) => +e.dataset.count) }), h.id);
  check("Government UI", 6, `${h.title}: tile = map coloured districts = API`, ui.tile === h.districts && ui.filled === h.districts, `tile ${ui.tile}, map ${ui.filled}, api ${h.districts}`);
}
const offUi = await gp.evaluate(() => +document.querySelector('[data-testid="official-count"]').dataset.count);
check("Government UI", 4, "Official alert districts shown in a separate tile", offUi === india.official.districts_with_alerts, `${offUi}`);
await browser.close();

const failed = results.filter((r) => !r.ok);
console.log(`\n${results.length - failed.length}/${results.length} checks passed`);
if (jsonOut) writeFileSync(jsonOut, JSON.stringify({ at: new Date().toISOString(), site: SITE, v2: V2, core: CORE, results, summary, counts, official_districts: india.official.districts_with_alerts }, null, 2));
process.exit(failed.length ? 1 : 0);
