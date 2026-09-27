// M3 acceptance test: decision-support workflows (Citizen, Farmer, Government) with scientific guardrails.
// Usage: PLAYWRIGHT_CHROMIUM=/opt/pw-browsers/chromium node tools/m3-acceptance/acceptance.mjs <V2_SITE> <V2_API> <CORE_API> [--json out.json]
// Read-only. Exits 1 on any failure. M1 (tools/compare) and M2 (tools/m2-acceptance) regressions run separately.
import { createHash } from "node:crypto";
import { execSync } from "node:child_process";
import { writeFileSync } from "node:fs";

const [, , SITE = "http://localhost:5174/", V2 = "http://localhost:8702/api/v2", CORE = "https://bharat-weather-intelligence-brown.vercel.app/api/v1"] = process.argv;
const jsonOut = process.argv.includes("--json") ? process.argv[process.argv.indexOf("--json") + 1] : null;
const PLACES = [
  { name: "Ahmedabad", lat: 23.0225, lon: 72.5714, note: "plains, no significant event" },
  { name: "Shimla", lat: 31.1048, lon: 77.1734, note: "mountain, multiple system events" },
  { name: "Chennai", lat: 13.0827, lon: 80.2707, note: "coastal, official alert, CORE-2" },
  { name: "Guwahati", lat: 26.1445, lon: 91.7362, note: "official flood alerts (state match)" },
  { name: "Uttarkashi", lat: 31.0033, lon: 78.5841, note: "mountain 5,264 m, official alerts + severe/alert/watch" },
];
// V2-generated text must never be an instruction (M3 §11). CORE and issuer wording are excluded (marked in the DOM).
const IMPERATIVE = /\b(evacuate|spray|harvest now|do not harvest|cancel|avoid|stay indoors|go indoors|must|should|we recommend|you are advised)\b/i;
const REQUIRED_STATEMENT = "District risk counts are based on the representative forecast point for each district. Conditions may vary within a district.";
const results = [];
const check = (group, n, name, ok, detail = "") => { results.push({ group, n, name, ok: !!ok, detail }); console.log(`${ok ? "PASS" : "FAIL"} [${group}] ${n}. ${name}${detail ? " — " + detail : ""}`); };
const j = async (url, t = 240000) => { const r = await fetch(url, { signal: AbortSignal.timeout(t) }); if (!r.ok) throw new Error(`${url} HTTP ${r.status}`); return r.json(); };
const q = (p) => `lat=${p.lat}&lon=${p.lon}&name=${encodeURIComponent(p.name)}`;

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE ?? "/opt/node-tools/node_modules/playwright/index.mjs");
const browser = await chromium.launch({ executablePath: process.env.PLAYWRIGHT_CHROMIUM });
const summary = {};

// ---------------- Citizen ----------------
for (const p of PLACES) {
  const G = `${p.name} (${p.note})`;
  const [ev, core] = await Promise.all([j(`${V2}/events?${q(p)}`), j(`${CORE}/dashboard?${q(p)}`)]);
  const page = await browser.newPage({ viewport: { width: 1360, height: 1000 } });
  await page.goto(`${SITE}#/home?mode=citizen&${q(p)}`, { waitUntil: "networkidle" });
  await page.waitForSelector('[data-testid="wtk-summary"]', { timeout: 120000 });
  await page.getByText(/Show \d+ more system/).click().catch(() => {});
  const ui = await page.evaluate(() => {
    const root = document.querySelector('[data-testid="what-to-know"]');
    const order = [...root.querySelectorAll('[data-testid="official-alert"], [data-testid="event"]')].map((e) => e.dataset.testid === "official-alert" ? "official" : "event");
    const events = [...root.querySelectorAll('[data-testid="event"]')].map((e) => ({ type: e.dataset.eventType, cls: e.dataset.classification, inSystem: !!e.closest('[data-testid="wtk-system"]'), inOfficial: !!e.closest('[data-testid="wtk-official"]') }));
    const v2Text = [...document.querySelectorAll('[data-testid="impact-context"], [data-testid="dq-notice"], [data-testid="wtk-summary"], [data-testid="wtk-none"], [data-testid="event-when"], [data-testid="event-timeline"]')].map((e) => e.innerText);
    return { order, events, v2Text, notices: [...document.querySelectorAll('[data-testid="dq-notice"]')].map((e) => e.dataset.id),
      contexts: [...root.querySelectorAll('[data-testid="event"] [data-testid="impact-context"]')].length,
      bars: document.querySelectorAll('[data-testid="timeline-bar"]').length, none: document.querySelector('[data-testid="wtk-none"]')?.innerText ?? null,
      officialInsideSystem: !!root.querySelector('[data-testid="wtk-system"] [data-testid="official-alert"]') };
  });
  const firstEv = ui.order.indexOf("event"), lastOff = ui.order.lastIndexOf("official");
  check(G, 1, "Official alerts first and in their own group", (firstEv < 0 || lastOff < firstEv) && !ui.officialInsideSystem && ui.order.filter((x) => x === "official").length === Math.min(3, ev.official_alerts.length), `${ev.official_alerts.length} official`);
  check(G, 2, "Every event card is system-derived and in the system group", ui.events.every((e) => e.cls === "system" && e.inSystem && !e.inOfficial) && ui.events.length === ev.events.length, `${ui.events.length} system events`);
  check(G, "2b", "Each event carries potential-relevance context (labelled)", ui.contexts === ev.events.length && ev.events.every((e) => e.context?.label.includes("not an impact forecast")));
  const timed = ev.events.filter((e) => e.start && e.end).length;
  check(G, "2c", "WHEN timeline: one bar per timed event (CORE period)", ui.bars === timed, `${ui.bars}/${timed}`);
  if (!ev.events.length && !ev.official_alerts.length) check(G, "2d", '"No significant weather event detected."', ui.none?.includes("No significant weather event detected."));
  const wantNotices = [...(core.current.terrain === "hills" ? ["elevation"] : []),
    ...core.risks.filter((r) => r.level === 0 && /^0 of \d+ models?.*show no event/.test(r.confidence?.basis ?? "")).map(() => "core_inconsistency")];
  check(G, 6, "Data-quality notices = what CORE fields require (terrain, CORE-2 check)", JSON.stringify(ui.notices) === JSON.stringify(wantNotices), `terrain ${core.current.terrain}; notices [${ui.notices.join(", ") || "none"}]`);
  check(G, 8, "No V2-generated instruction on the page", ui.v2Text.every((t) => !IMPERATIVE.test(t)));
  // 3: evidence traceable
  if (ev.events.length) {
    const e0 = ev.events[0];
    await page.locator(`[data-testid="event"][data-event-type="${e0.type}"] [data-testid="view-evidence"]`).first().click();
    await page.waitForSelector('[data-testid="ev-section"][data-key="provenance"]', { timeout: 90000 });
    const dr = await page.evaluate(() => ({ keys: [...document.querySelectorAll('[data-testid="ev-section"]')].map((s) => s.dataset.key),
      rule: document.querySelector('[data-testid="ev-rule"]')?.innerText, prov: document.querySelectorAll('[data-testid="ev-provenance"]').length,
      notices: [...document.querySelectorAll('[data-testid="evidence-drawer"] [data-testid="dq-notice"]')].map((e) => e.dataset.id),
      ctx: document.querySelector('[data-testid="evidence-drawer"] [data-testid="impact-context"]')?.innerText ?? "" }));
    const evd = await j(`${V2}/evidence?${q(p)}&risk=${e0.type}`);
    const crit = core.risks.find((r) => r.id === e0.type).criterion;
    check(G, 3, `Evidence traceable (${e0.type}): 9 sections, CORE rule, ≥ 3 provenance entries, notices = API`,
      dr.keys.length === 9 && dr.rule === crit && dr.prov >= 3 && JSON.stringify(dr.notices) === JSON.stringify(evd.data_quality.map((n) => n.id)),
      `${dr.prov} provenance; notices [${dr.notices.join(", ")}]`);
    check(G, 8, "Evidence context is conditional, not an instruction", !IMPERATIVE.test(dr.ctx));
  }
  summary[p.name] = { terrain: core.current.terrain, official: ev.official_alerts.length, events: ev.events.map((e) => `${e.title} ${e.severity.status}`), notices: ui.notices };
  await page.close();
}

// ---------------- Farmer ----------------
for (const [p, crop, stage] of [[PLACES[4], "paddy", "flowering"], [PLACES[0], "cotton", "flowering"]]) {
  const G = `Farmer ${p.name} ${crop}/${stage}`;
  const page = await browser.newPage({ viewport: { width: 1360, height: 1000 } });
  await page.addInitScript(([c, s]) => { try { localStorage.setItem("bwi2.crop", JSON.stringify({ crop: c, stage: s })); } catch {} }, [crop, stage]);
  await page.goto(`${SITE}#/home?mode=farmer&${q(p)}`, { waitUntil: "networkidle" });
  await page.waitForSelector('[data-testid="farmer-indicators"]', { timeout: 120000 });
  await page.waitForSelector('[data-testid="farmer-events"], [data-testid="farmer-events-none"]', { timeout: 90000 });
  const f = await page.evaluate(() => {
    const ind = document.querySelector('[data-testid="farmer-indicators"]'), adv = document.querySelector('[data-testid="official-advisory"]');
    const pos = (el) => el ? [...document.querySelectorAll("*")].indexOf(el) : -1;
    const steps = ["farmer-days", "farmer-indicators", "farmer-events", "official-advisory"].map((id) => pos(document.querySelector(`[data-testid="${id}"]`) ?? (id === "farmer-events" ? document.querySelector('[data-testid="farmer-events-none"]') : null)));
    return { badges: !!ind.querySelector('[data-testid="badge-system-derived"]') && !!ind.querySelector('[data-testid="badge-unvalidated"]'),
      each: [...ind.querySelectorAll('[data-testid="farmer-indicator"]')].map((e) => /unvalidated/i.test(e.innerText)),
      separate: !!adv && !adv.contains(ind) && !ind.contains(adv) && !/system-derived/i.test(adv.querySelector("div")?.innerText ?? ""),
      advOfficial: /official agricultural advisory/i.test(adv?.innerText ?? ""), steps,
      ctx: [...document.querySelectorAll('[data-testid="farmer-events"] [data-testid="impact-context"]')].map((e) => e.innerText),
      links: [...document.querySelectorAll('[data-testid="farmer-linked-indicator"]')].map((e) => e.dataset.id) };
  });
  check(G, 7, "Indicators labelled SYSTEM-DERIVED and UNVALIDATED (block and each indicator)", f.badges && f.each.length > 0 && f.each.every(Boolean), `${f.each.length} indicators`);
  check(G, 7, "Official Agromet advisory is a separate official block", f.separate && f.advOfficial);
  check(G, "7b", "Workflow order: weather → system indicators → crop relevance → official advisory", f.steps.every((x, i) => x > 0 && (i === 0 || f.steps[i - 1] < x)), f.steps.join(" < "));
  check(G, 8, "Farmer context lines are conditional, not instructions", f.ctx.every((t) => !IMPERATIVE.test(t)), `${f.ctx.length} lines; linked indicators [${f.links.join(", ")}]`);
  await page.close();
}

// ---------------- Government ----------------
const india = await j(`${V2}/region/india/risks`, 300000);
const G = "Government India";
check(G, 4, "District counts only for the documented four hazards", india.hazards.map((h) => h.id).sort().join() === "cold,heat,rain,wind"
  && india.not_counted.every((n) => n.status === "Not currently included in district count") && india.not_counted.length === 7);
const gp = await browser.newPage({ viewport: { width: 1440, height: 1300 } });
await gp.goto(`${SITE}#/home?mode=government`, { waitUntil: "networkidle" });
await gp.waitForSelector('[data-testid="hazard-count"]', { timeout: 300000 });
const g = await gp.evaluate(() => ({
  statement: document.querySelector('[data-testid="count-statement"]')?.innerText.trim(),
  labels: [...document.querySelectorAll('[data-testid="count-label"]')].map((e) => e.innerText),
  notCounted: [...document.querySelectorAll('[data-testid="not-counted"] [data-id]')].map((e) => e.dataset.id),
  notCountedLabel: document.querySelector('[data-testid="not-counted"]')?.innerText ?? "",
  notices: [...document.querySelectorAll('[data-testid="india-risks"] [data-testid="dq-notice"]')].map((e) => e.dataset.id),
  affected: /affected districts?|districts? affected/i.test(document.querySelector('[data-testid="government"]')?.innerText + document.querySelector('[data-testid="india-risks"]')?.innerText),
  v2Text: [...document.querySelectorAll('[data-testid="dq-notice"], [data-testid="count-statement"], [data-testid="count-label"]')].map((e) => e.innerText),
}));
check(G, 5, "Required statement shown verbatim", g.statement === REQUIRED_STATEMENT);
check(G, 5, 'Counts worded as "districts with system-assessed … risk"; never "affected districts"', g.labels.length === 4 && g.labels.every((l) => /^districts with system-assessed .+ risk$/.test(l)) && !g.affected, g.labels.join(" | "));
check(G, 4, '"Not currently included in district count" for the 7 other hazards', g.notCounted.length === 7 && /Not currently included in district count/.test(g.notCountedLabel), g.notCounted.join(", "));
const wantG = [...(india.coverage.complete ? [] : ["incomplete_coverage"]), "incomplete_hazards", ...(india.hazards.some((h) => h.hills_districts) ? ["elevation_districts"] : [])];
check(G, 6, "Government data-quality notices (coverage, hazard coverage, mountain districts)", JSON.stringify(g.notices) === JSON.stringify(wantG), `[${g.notices.join(", ")}]; hill districts ${india.hazards.map((h) => `${h.id} ${h.hills_districts}/${h.districts}`).join(", ")}`);
check(G, 8, "No V2-generated instruction on the Government page", g.v2Text.every((t) => !IMPERATIVE.test(t)));
// state → district → event → evidence
const cold = india.hazards.find((h) => h.id === "cold");
await gp.locator('[data-testid="hazard-count"][data-hazard="cold"]').click();
if (cold.by_state.length) {
  await gp.locator('[data-testid="concentration"] button').first().click();
  await gp.waitForSelector('[data-testid="state-focus"]');
  const sf = await gp.evaluate(() => ({ text: document.querySelector('[data-testid="state-focus"]').innerText, counts: [...document.querySelectorAll('[data-testid="state-counts"] [data-hazard]')].map((e) => [e.dataset.hazard, +e.dataset.count]), slug: document.querySelector('[data-testid="state-focus"]').dataset.state }));
  const recount = Object.fromEntries(["rain", "heat", "cold", "wind"].map((h) => [h, india.districts.filter((x) => x.state_slug === sf.slug && x.levels[h] >= 1).length]));
  check(G, 5, `State focus (${sf.slug}): counts = district list; states conditions may vary`, sf.counts.every(([h, n]) => recount[h] === n) && /Conditions may vary within a district/.test(sf.text), JSON.stringify(recount));
  await gp.locator('[data-testid="state-focus-table"] button').first().click();
  await gp.waitForSelector('[data-testid="district-events"] [data-testid="district-event"], [data-testid="district-events"] p', { timeout: 90000 });
  const dc = await gp.evaluate(() => ({ id: document.querySelector('[data-testid="district-card"]').dataset.district,
    hills: !!document.querySelector('[data-testid="district-card"] [data-testid="dq-notice"][data-id="elevation"]'),
    events: [...document.querySelectorAll('[data-testid="district-event"]')].map((e) => [e.dataset.eventType, +e.dataset.level, e.innerText]) }));
  const dx = india.districts.find((x) => x.id === dc.id);
  const pe = await j(`${V2}/events?lat=${dx.lat}&lon=${dx.lon}&name=${encodeURIComponent(dx.district + " (district point)")}`);
  check(G, 3, `District ${dx.district}: WHAT/WHEN at the representative point = /events; hill note iff hill terrain`,
    dc.events.length === pe.events.length && pe.events.every((e) => dc.events.some(([t, l]) => t === e.type && l === e.severity.level)) && dc.hills === (dx.terrain === "hills"),
    dc.events.map((x) => x[2].split("\n")[0]).join(" | ") || "no events");
  await gp.locator('[data-testid="district-card"] [data-testid="view-evidence"]').click();
  await gp.waitForSelector('[data-testid="ev-section"][data-key="provenance"]', { timeout: 90000 });
  const n = await gp.evaluate(() => document.querySelectorAll('[data-testid="ev-section"]').length);
  check(G, 3, "District evidence opens with the same 9-section structure", n === 9);
}
await gp.close();
await browser.close();

// ---------------- CORE unchanged ----------------
const head = execSync("git ls-remote https://github.com/gnmcool/bharat-weather-intelligence refs/heads/main refs/tags/core-v1.0").toString();
const site = createHash("sha256").update(Buffer.from(await (await fetch("https://gnmcool.github.io/bharat-weather-intelligence/")).arrayBuffer())).digest("hex");
const health = (await fetch(`${CORE}/health`)).status;
check("CORE", 9, "CORE main and core-v1.0 at 2840f8d; site identical to baseline; API up",
  head.split("\n").filter(Boolean).every((l) => l.startsWith("2840f8df8805808d8f82a04c46c38f7ae5a19d59")) && site.startsWith("497abc94f32453d9") && health === 200, `site ${site.slice(0, 16)}, health ${health}`);

const failed = results.filter((r) => !r.ok);
console.log(`\n${results.length - failed.length}/${results.length} checks passed`);
if (jsonOut) writeFileSync(jsonOut, JSON.stringify({ at: new Date().toISOString(), site: SITE, v2: V2, results, summary, india: india.hazards.map((h) => ({ id: h.id, districts: h.districts, hills: h.hills_districts })) }, null, 2));
process.exit(failed.length ? 1 : 0);
