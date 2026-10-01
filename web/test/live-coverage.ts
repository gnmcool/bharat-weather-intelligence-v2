// Live translation coverage: fetch today's real CORE output and report every string the farmer screens would show
// in English while Gujarati or Hindi is selected. Read-only GET requests to CORE's public API; changes nothing.
//
// Run: node --experimental-strip-types test/live-coverage.ts   (CORE_API_BASE overrides the default URL)
// Exit: 0 all translated · 1 untranslated strings found · 2 CORE unreachable or too many failed requests.
// Writes a markdown report to $GITHUB_STEP_SUMMARY when set (GitHub Actions job summary).
import { appendFileSync } from "node:fs";
import { coreText, cropName, EVENT_TITLE, eventText, indicatorText, seasonName, stageName, TLS, type Out, type TL } from "../src/i18n/coreText.ts";
import { wmoText } from "../src/lib/format.ts";

const BASE = (process.env.CORE_API_BASE ?? "https://bharat-weather-intelligence-brown.vercel.app/api/v1").replace(/\/$/, "");

// Gujarat first (launch region), then contrasting climates so most event types appear on a typical day.
const POINTS: { name: string; lat: number; lon: number }[] = [
  { name: "Ahmedabad", lat: 23.0225, lon: 72.5714 },
  { name: "Rajkot", lat: 22.3039, lon: 70.8022 },
  { name: "Bhuj", lat: 23.2420, lon: 69.6669 },
  { name: "Palanpur", lat: 24.1724, lon: 72.4381 },
  { name: "Surat", lat: 21.1702, lon: 72.8311 },
  { name: "Junagadh", lat: 21.5222, lon: 70.4579 },
  { name: "Uttarkashi", lat: 30.7268, lon: 78.4354 },
  { name: "Shimla", lat: 31.1048, lon: 77.1734 },
  { name: "Chennai", lat: 13.0827, lon: 80.2707 },
  { name: "Guwahati", lat: 26.1445, lon: 91.7362 },
  { name: "Jaisalmer", lat: 26.9157, lon: 70.9083 },
  { name: "Mumbai", lat: 19.0760, lon: 72.8777 },
];
// Farmer reports for every crop × stage at these points (one plains, one hills).
const FARMER_POINTS = [POINTS[0], POINTS[6]];

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));
let failures = 0;
let requests = 0;
async function get<T>(path: string, params: Record<string, string | number> = {}): Promise<T | null> {
  const url = `${BASE}${path}?${new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)]))}`;
  for (let attempt = 1; attempt <= 2; attempt++) {
    requests++;
    try {
      const r = await fetch(url, { signal: AbortSignal.timeout(45_000) });
      if (r.ok) return (await r.json()) as T;
      if (r.status < 500 && r.status !== 429) break;
    } catch {
      /* retry once */
    }
    await sleep(3000);
  }
  failures++;
  console.error(`request failed: ${path} ${JSON.stringify(params)}`);
  return null;
}

/** Untranslated English strings, per language: text → where it was seen. */
const misses: Record<TL, Map<string, Set<string>>> = { gu: new Map(), hi: new Map() };
let checked = 0;
function check(o: Out, english: string, where: string, l: TL) {
  checked++;
  if (!o.tr && english) {
    const m = misses[l];
    if (!m.has(english)) m.set(english, new Set());
    m.get(english)!.add(where);
  }
}

interface Risk { id: string; level: number; status: string; headline: string; official?: boolean; confidence?: { basis?: string } }
interface Dash {
  location: { name: string };
  current: { terrain: string; source: string; values: Record<string, { value: number | null } | undefined> };
  risks: Risk[];
  anomaly?: { items?: { label: string; period: string; category: string | null }[] } | null;
}
interface Crops { validation_status: string; crops: { id: string; label: string; season: string; stages: string[] }[] }
interface Farmer {
  crop: string; crop_label: string; stage: string; season: string; validation_status: string; crop_note: string | null; disclaimer: string;
  official: { title: string; note: string; integration: string; links: { label: string }[] };
  indicators: { id: string; label: string; value: string; rule: string }[];
}

async function main() {
  const crops = await get<Crops>("/farmer/crops");
  if (!crops) {
    console.error(`CORE unreachable at ${BASE}`);
    process.exit(2);
  }
  for (const l of TLS) {
    check(coreText(crops.validation_status, l), crops.validation_status, "crops: validation_status", l);
    for (const c of crops.crops) {
      check(cropName(c.id, c.label, l), c.label, `crop ${c.id}`, l);
      check(seasonName(c.season, l), c.season, `crop ${c.id} season`, l);
      for (const s of c.stages) check(stageName(s, l), s, `crop ${c.id} stage`, l);
    }
  }

  let events = 0;
  for (const p of POINTS) {
    const d = await get<Dash>("/dashboard", { lat: p.lat, lon: p.lon, name: p.name });
    if (!d) continue;
    const code = d.current.values?.weather_code?.value ?? null;
    for (const l of TLS) {
      check(coreText(d.current.terrain, l), d.current.terrain, `${p.name}: terrain`, l);
      check(coreText(d.current.source, l), d.current.source, `${p.name}: current source`, l);
      if (code !== null) check(coreText(wmoText(code), l), wmoText(code), `${p.name}: weather code ${code}`, l);
      for (const a of d.anomaly?.items ?? []) {
        for (const w of [a.label, a.period, a.category]) if (w) check(coreText(w, l), w, `${p.name}: anomaly`, l);
      }
      // Events = CORE risks at Watch or above that are not official (api-v2 build_event); title from V2's catalogue.
      for (const r of d.risks.filter((x) => x.level >= 1 && !x.official)) {
        if (l === "gu") events++;
        const title = EVENT_TITLE[r.id]?.en ?? r.id;
        const o = eventText({ type: r.id, title, headline: r.headline, severity: { level: r.level, status: r.status },
          timing_note: null, model_agreement: { text: "" }, context: null }, l);
        check(o.headline, r.headline, `${p.name}: ${r.id} headline`, l);
        check(o.status, r.status, `${p.name}: ${r.id} status`, l);
        if (!EVENT_TITLE[r.id]) check({ text: r.id, tr: false }, `event type "${r.id}" has no title translation`, p.name, l);
      }
    }
    await sleep(500);
  }

  let reports = 0;
  for (const p of FARMER_POINTS) {
    for (const c of crops.crops) {
      for (const s of c.stages) {
        const f = await get<Farmer>("/farmer", { lat: p.lat, lon: p.lon, crop: c.id, stage: s, name: p.name });
        if (!f) continue;
        reports++;
        const at = `${p.name}: ${c.id}/${s}`;
        for (const l of TLS) {
          for (const i of f.indicators) {
            const o = indicatorText(i, l);
            check(o.label, i.label, `${at} ${i.id} label`, l);
            check(o.value, i.value, `${at} ${i.id} value`, l);
            check(o.rule, i.rule, `${at} ${i.id} rule`, l);
          }
          for (const [k, v] of [["disclaimer", f.disclaimer], ["crop note", f.crop_note], ["official title", f.official.title],
            ["official note", f.official.note], ["official integration", f.official.integration]] as const) {
            if (v) check(coreText(v, l), v, `${at} ${k}`, l);
          }
          for (const k of f.official.links) check(coreText(k.label, l), k.label, `${at} advisory link`, l);
        }
        await sleep(250);
      }
    }
  }

  const failedShare = failures / Math.max(1, requests);
  const lines: string[] = [
    `## Farmer-screen translation coverage against live CORE`,
    ``,
    `CORE: \`${BASE}\` · ${new Date().toISOString()}`,
    ``,
    `| | Count |`, `| --- | --- |`,
    `| Points (dashboard) | ${POINTS.length} |`, `| System events seen (Watch or above) | ${events} |`,
    `| Farmer reports (crop × stage × point) | ${reports} |`, `| Strings checked (all languages) | ${checked} |`,
    `| Failed requests | ${failures} of ${requests} |`,
    ``,
  ];
  let total = 0;
  for (const l of TLS) {
    const m = misses[l];
    total += m.size;
    lines.push(`### ${l === "gu" ? "Gujarati" : "Hindi"}: ${m.size === 0 ? "all translated" : `${m.size} untranslated string(s) — shown in English`}`);
    if (m.size) {
      lines.push(``, `| CORE text | Seen at (first 3) |`, `| --- | --- |`);
      for (const [text, where] of m) lines.push(`| ${text.replace(/\|/g, "\\|")} | ${[...where].slice(0, 3).join("; ")} |`);
    }
    lines.push(``);
  }
  if (total) lines.push(`Untranslated strings are shown in English (never guessed). Add the pattern or phrase to \`web/src/i18n/coreText.ts\`, with native-speaker review.`);
  const report = lines.join("\n");
  console.log(report);
  if (process.env.GITHUB_STEP_SUMMARY) appendFileSync(process.env.GITHUB_STEP_SUMMARY, report + "\n");
  if (failedShare > 0.2) {
    console.error(`Too many failed requests (${failures}/${requests}); coverage result is not reliable.`);
    process.exit(2);
  }
  process.exit(total ? 1 : 0);
}

await main();
