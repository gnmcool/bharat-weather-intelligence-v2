// Farmer site (#/kisan) rules and wording. Run: npm test.
import { test } from "node:test";
import assert from "node:assert/strict";
import { eventKey, istToday, isStale, likelihood, pickDays, pickWarnings, rainClass, rainView, mmText, type WarningIn } from "../src/kisan/rules.ts";
import { districtName, GUJARAT_DISTRICTS, K } from "../src/kisan/strings.ts";

test("rain classes follow IMD's 24-hour thresholds exactly", () => {
  const cases: [number | null, string][] = [
    [null, "none"], [0, "none"], [0.09, "none"], [0.1, "veryLight"], [2.49, "veryLight"], [2.5, "light"], [15.59, "light"],
    [15.6, "moderate"], [64.49, "moderate"], [64.5, "heavy"], [115.59, "heavy"], [115.6, "veryHeavy"], [204.49, "veryHeavy"], [204.5, "extreme"],
  ];
  for (const [mm, cls] of cases) assert.equal(rainClass(mm), cls, String(mm));
});

test("chance wording never promises rain the forecast does not support", () => {
  assert.equal(likelihood(null), "unlikely");
  assert.equal(likelihood(29), "unlikely");
  assert.equal(likelihood(30), "possible");
  assert.equal(likelihood(59), "possible");
  assert.equal(likelihood(60), "likely");
  assert.equal(rainView(0, 0).kind, "dry");
  assert.equal(rainView(0, 45).kind, "smallChance"); // chance but no amount
  assert.equal(rainView(6, 20).kind, "smallChance"); // amount but low chance
  assert.equal(rainView(6, 70).kind, "rain");
  assert.equal(rainView(80, 90).kind, "heavyRain");
  assert.equal(rainView(80, 10).kind, "smallChance"); // heavy amount, low chance: not shown as heavy rain
  assert.deepEqual([mmText(null), mmText(0.4), mmText(1.6), mmText(58.4)], [null, "<1", "2", "58"]);
});

test("days: today (IST) and the next three; nothing if today is missing", () => {
  const row = (date: string) => ({ date, precipitation_sum: 0, precipitation_probability_max: 0, temperature_2m_max: 30, temperature_2m_min: 20, weather_code: 0 });
  const daily = ["2026-10-23", "2026-10-24", "2026-10-25", "2026-10-26", "2026-10-27", "2026-10-28", "2026-10-29"].map(row);
  assert.deepEqual(pickDays(daily, "2026-10-25").map((d) => d.date), ["2026-10-25", "2026-10-26", "2026-10-27", "2026-10-28"]);
  assert.deepEqual(pickDays(daily.slice(3), "2026-10-25"), []);
  assert.equal(istToday(new Date("2026-10-24T18:29:00Z")), "2026-10-24");
  assert.equal(istToday(new Date("2026-10-24T18:30:00Z")), "2026-10-25");
});

test("every warning type seen in the live SACHET feed (25 Oct 2026) and stored records gets a translation", () => {
  const seen = ["Lightning", "Flood", "Flash Flood", "Extremely Heavy Rain", "Very Heavy Rain", "Moderate Rain", "Squally",
    "Moderate Thunderstorms", "Heavy Rain", "Thunder shower", "Heat Wave", "Cold Wave", "Dense Fog", "Cyclonic Storm", "Heavy Rainfall Warning"];
  for (const e of seen) {
    const k = eventKey(e);
    assert.ok(k, `no key for ${e}`);
    for (const l of ["gu", "hi", "en"] as const) assert.ok(K[l].events[k!], `${l} lacks ${k}`);
  }
  assert.equal(eventKey("Tsunami"), null); // unknown types stay in the issuer's English
  assert.equal(eventKey(null), null);
});

test("warnings: expired and national ones dropped; own district first; most severe first", () => {
  const now = new Date("2026-10-25T10:00:00+05:30");
  const w = (id: string, match: WarningIn["match"], severity: string, expires: string | null, effective = "2026-10-25T08:00:00+05:30"): WarningIn => ({
    id, event: "Heavy Rain", severity, headline: id, description: null, sender: "IMD", issuer: "IMD", effective, expires, area: null, match,
  });
  const r = pickWarnings([
    w("old", "district", "Extreme", "2026-10-25T09:00:00+05:30"),
    w("nat", "national", "Extreme", null),
    w("st-mod", "state", "Moderate", "2026-10-26T00:00:00+05:30"),
    w("own-mod", "district", "Moderate", "2026-10-26T00:00:00+05:30"),
    w("own-sev", "district", "Severe", "2026-10-26T00:00:00+05:30"),
    w("st-ext", "state", "Extreme", null),
  ], now);
  assert.deepEqual(r.own.map((x) => x.id), ["own-sev", "own-mod"]);
  assert.deepEqual(r.state.map((x) => x.id), ["st-ext", "st-mod"]);
  assert.ok(r.own.every((x) => x.own && x.key === "heavyRain"));
});

test("stale data is flagged after six hours", () => {
  assert.equal(isStale("2026-10-25T04:00:00Z", new Date("2026-10-25T09:59:00Z")), false);
  assert.equal(isStale("2026-10-25T04:00:00Z", new Date("2026-10-25T10:01:00Z")), true);
});

test("wording: complete in every language, in the right script", () => {
  const script = { gu: /[઀-૿]/, hi: /[ऀ-ॿ]/ } as const;
  const keys = Object.keys(K.en) as (keyof typeof K.en)[];
  for (const l of ["gu", "hi"] as const) {
    for (const k of keys) {
      const v = K[l][k];
      const sample = typeof v === "function" ? (v as (...a: unknown[]) => string)(2, "x") : typeof v === "string" ? v : Object.values(v).join(" ");
      if (k === "attribution") continue; // proper names and licence stay Latin
      assert.match(sample, script[l], `${l}.${String(k)}`);
    }
    assert.deepEqual(Object.keys(K[l].events).sort(), Object.keys(K.en.events).sort());
    for (const [c, s] of Object.entries(K[l].rainOf)) if (c !== "none") assert.match(s, script[l], `${l} rain ${c}`);
  }
});

test("Gujarat district names cover CORE's 34 districts", () => {
  const core = ["Ahmedabad", "Amreli", "Anand", "Aravalli", "Banaskantha", "Bharuch", "Bhavnagar", "Botad", "Chhota Udaipur", "Dahod", "Dang",
    "Devbhumi Dwarka", "Gandhinagar", "Gir Somnath", "Jamnagar", "Junagadh", "Kheda", "Kutch", "Mahisagar", "Mehsana", "Morbi", "Narmada", "Navsari",
    "Panchmahal", "Patan", "Porbandar", "Rajkot", "Sabarkantha", "Surat", "Surendranagar", "Tapi", "Vadodara", "Valsad", "Vav-Tharad"];
  assert.deepEqual(Object.keys(GUJARAT_DISTRICTS).sort(), core.sort());
  assert.equal(districtName("Rajkot", "gu"), "રાજકોટ");
  assert.equal(districtName("Pune", "gu"), "Pune"); // other states keep CORE's English for now
});
