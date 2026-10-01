// Gujarati and Hindi rendering of CORE farmer text. Run: npm test (node --experimental-strip-types --test).
// Fixtures are CORE's real output (CORE 2840f8d farmer.assess / risk.assess on synthetic weather, plus captured live
// CORE dashboards through api-v2 build_events), not copies of its templates. Every check runs for every language.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  coreText, cropName, CROPS, eventText, indicatorText, LEVEL_NAMES, MONTHS, seasonName, SEASONS, stageName, STAGES, TLS, type TL, WEEKDAYS,
} from "../src/i18n/coreText.ts";

const fx = JSON.parse(readFileSync(new URL("./fixtures/core_farmer_text.json", import.meta.url), "utf8"));
const ev = JSON.parse(readFileSync(new URL("./fixtures/core_event_text.json", import.meta.url), "utf8"));
// Same numbers, same text form (word order may move "of 7" before the count; checked separately below).
const nums = (s: string) => (s.match(/\d+(?:\.\d+)?/g) ?? []).sort().join(",");
const SCRIPT: Record<TL, RegExp> = { gu: /[઀-૿]/, hi: /[ऀ-ॿ]/ };
const OTHER: Record<TL, RegExp> = { gu: /[ऀ-ॿ]/, hi: /[઀-૿]/ };
const OF7: Record<TL, (n: string, kind: string, op: string, t: string) => string> = {
  gu: (n, k, op, t) => `7 માંથી ${n} ${k === "days" ? "દિવસ" : "રાત"} ${op} ${t} °C`,
  hi: (n, k, op, t) => `7 में से ${n} ${k === "days" ? "दिन" : "रातें"} ${op} ${t} °C`,
};
const DISCLAIMER_MARKERS: Record<TL, RegExp[]> = { gu: [/સૂચના નથી/, /સત્તાવાર/], hi: [/निर्देश नहीं/, /आधिकारिक/] };
const ENGLISH_WORDS = /\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|today|tomorrow)\b/;

const mkEvent = (type: string, headline: string, level = 2) => ({
  type, title: ev.v2_titles[type], headline, severity: { level, status: ["No risk", "Watch", "Alert", "Severe"][level] },
  timing_note: null, model_agreement: { text: "Model agreement: 2 of 3" }, context: { farmer: ev.v2_context_farmer[type] },
});

test("fixtures come from frozen CORE 2840f8d and cover every system event type", () => {
  assert.equal(fx.core_commit, "2840f8d");
  assert.equal(ev.core_commit, "2840f8d");
  assert.ok(fx.indicators.length >= 50);
  assert.deepEqual(Object.keys(ev.headlines).sort(), ["cold", "drought", "fire", "flood", "fog", "heat", "lightning", "rain", "thunderstorm", "wind"]);
});

test("English mode returns CORE text unchanged", () => {
  for (const i of fx.indicators) {
    const o = indicatorText(i, "en");
    assert.deepEqual([o.label.text, o.value.text, o.rule.text], [i.label, i.value, i.rule]);
    assert.ok(!o.label.tr && !o.value.tr && !o.rule.tr);
  }
  assert.equal(coreText(fx.paragraphs.disclaimer, "en").text, fx.paragraphs.disclaimer);
  const e = mkEvent("heat", ev.headlines.heat[0]);
  const o = eventText(e, "en");
  assert.deepEqual([o.title.text, o.headline.text, o.status.text], [e.title, e.headline, "Alert"]);
  assert.ok(!o.headline.tr);
});

for (const L of TLS) {
  const inScript = (s: string, what: string) => {
    assert.match(s, SCRIPT[L], `${L} ${what}: not in ${L} script: ${s}`);
    assert.doesNotMatch(s, OTHER[L], `${L} ${what}: contains the other Indic script: ${s}`);
  };

  test(`[${L}] every CORE indicator sentence is translated, field by field, numbers unchanged`, () => {
    for (const i of fx.indicators) {
      const o = indicatorText(i, L);
      for (const f of ["label", "value", "rule"] as const) {
        assert.ok(o[f].tr, `${L} ${i.id}.${f} not translated: ${i[f]}`);
        inScript(o[f].text, `${i.id}.${f}`);
      }
      assert.equal(nums(o.value.text), nums(i.value), `value ${i.value} → ${o.value.text}`);
      assert.equal(nums(o.rule.text), nums(i.rule), `rule ${i.rule} → ${o.rule.text}`);
      const m = i.value.match(/^(\d+) of 7 (days|nights) (≥|≤) (\d+) °C$/);
      if (m) assert.equal(o.value.text, OF7[L](m[1], m[2], m[3], m[4]));
    }
  });

  test(`[${L}] changed or unknown CORE wording falls back to English, never a guess`, () => {
    const base = fx.indicators.find((i: { id: string }) => i.id === "heat_stress");
    const o0 = indicatorText({ ...base, label: "Heat stress (new wording)" }, L);
    assert.ok(!o0.label.tr && o0.label.text === "Heat stress (new wording)" && o0.value.tr);
    assert.ok(!indicatorText({ ...base, value: "3 of 10 days ≥ 34 °C" }, L).value.tr);
    assert.ok(!indicatorText({ ...base, rule: "Tmax ≥ 34 °C at early flowering" }, L).rule.tr); // unknown stage
    const o3 = indicatorText({ ...base, id: "new_indicator" }, L);
    assert.ok(!o3.label.tr && !o3.value.tr && !o3.rule.tr);
    assert.deepEqual(coreText(fx.paragraphs.disclaimer + " ", L), { text: fx.paragraphs.disclaimer + " ", tr: false });
    assert.deepEqual(coreText(null, L), { text: "", tr: false });
  });

  test(`[${L}] disclaimer and official advisory text are translated and keep the 'not instructions' meaning`, () => {
    const p = fx.paragraphs;
    for (const k of ["disclaimer", "official_title", "official_note", "official_integration", "validation_status"]) {
      const o = coreText(p[k], L);
      assert.ok(o.tr, `${L} ${k} not translated`);
      inScript(o.text, k);
    }
    for (const re of DISCLAIMER_MARKERS[L]) assert.match(coreText(p.disclaimer, L).text, re);
    for (const l of fx.link_labels) assert.ok(coreText(l, L).tr, `link ${l}`);
    assert.match(coreText(fx.link_labels[2], L).text, /1800-180-1551/);
  });

  test(`[${L}] every crop, season, stage and crop note in CORE's crops.yaml is translated`, () => {
    for (const [id, c] of Object.entries<{ label: string; season: string; stages: string[]; note: string | null }>(fx.crops)) {
      assert.ok(cropName(id, c.label, L).tr, id);
      assert.ok(seasonName(c.season, L).tr, c.season);
      for (const s of c.stages) assert.ok(stageName(s, L).tr, `${id}.${s}`);
      if (c.note) assert.ok(coreText(c.note, L).tr, `${id} note`);
    }
    assert.equal(Object.keys(CROPS[L]).length, Object.keys(fx.crops).length);
    const stages = new Set(Object.values<{ stages: string[] }>(fx.crops).flatMap((c) => c.stages));
    assert.deepEqual(Object.keys(STAGES[L]).sort(), [...stages].sort(), "no stale or missing stages");
    assert.deepEqual(Object.keys(SEASONS[L]).sort(), [...new Set(Object.values<{ season: string }>(fx.crops).map((c) => c.season))].sort());
    assert.equal(LEVEL_NAMES[L].length, 4);
  });

  test(`[${L}] every CORE event headline, title, status, agreement and farmer context is translated`, () => {
    for (const [type, hs] of Object.entries<string[]>(ev.headlines)) {
      for (const h of hs) {
        const o = eventText(mkEvent(type, h), L);
        for (const f of ["title", "headline", "status", "agreement", "context"] as const) {
          assert.ok(o[f].tr, `${L} ${type}.${f} not translated${f === "headline" ? `: ${h}` : ""}`);
          inScript(o[f].text, `${type}.${f}`);
        }
        assert.equal(nums(o.headline.text), nums(h), `${h} → ${o.headline.text}`);
        assert.doesNotMatch(o.headline.text, ENGLISH_WORDS);
      }
    }
  });

  test(`[${L}] headlines and anomaly words from captured live CORE dashboards are translated`, () => {
    for (const [type, hs] of Object.entries<string[]>(ev.live_headlines)) {
      for (const h of hs) {
        const o = eventText(mkEvent(type, h), L);
        assert.ok(o.headline.tr, `live ${type}: ${h}`);
        assert.equal(nums(o.headline.text), nums(h));
      }
    }
    for (const w of ev.live_anomaly_words) assert.ok(coreText(w, L).tr, `anomaly word: ${w}`);
  });

  test(`[${L}] model agreement keeps k and n in the right places; watch-level headlines covered`, () => {
    const e = { ...mkEvent("rain", ev.headlines.rain[0]), model_agreement: { text: "Model agreement: 1 of 3" } };
    assert.equal(eventText(e, L).agreement.text, L === "gu" ? "મોડેલોની સહમતી: 3 માંથી 1" : "मॉडलों की सहमति: 3 में से 1");
    assert.ok(eventText({ ...e, model_agreement: { text: "Model agreement: not assessed" } }, L).agreement.tr);
    for (const [type, h] of [["heat", "Heat watch tomorrow"], ["cold", "Cold watch Sat 03 Oct"], ["wind", "Gusts up to 55 km/h"]]) {
      const o = eventText(mkEvent(type, h, 1), L).headline;
      assert.ok(o.tr, h);
      inScript(o.text, h);
      assert.doesNotMatch(o.text, ENGLISH_WORDS);
    }
  });

  test(`[${L}] event text: unknown wording, titles and types fall back to English`, () => {
    const e = mkEvent("heat", ev.headlines.heat[0]);
    assert.ok(!eventText({ ...e, headline: "Heat wave expected on Saturday" }, L).headline.tr);
    assert.ok(!eventText({ ...e, title: "Heat (renamed)" }, L).title.tr);
    assert.ok(!eventText({ ...e, type: "cyclone", title: "Cyclone (official alert logic)" }, L).headline.tr);
    assert.ok(!eventText({ ...e, context: { farmer: "New context sentence." } }, L).context.tr);
  });
}

test("headline month/weekday names match the browser's own gu-IN / hi-IN dates", () => {
  for (const [L, loc] of [["gu", "gu-IN"], ["hi", "hi-IN"]] as const) {
    for (let m = 0; m < 12; m++) {
      const d = new Date(Date.UTC(2026, m, 15));
      const en = d.toLocaleDateString("en-GB", { month: "short", timeZone: "UTC" }).slice(0, 3);
      assert.equal(MONTHS[L][en], d.toLocaleDateString(loc, { month: "short", timeZone: "UTC" }), `${L} ${en}`);
    }
    for (let i = 0; i < 7; i++) {
      const d = new Date(Date.UTC(2026, 8, 28 + i));
      const en = d.toLocaleDateString("en-GB", { weekday: "short", timeZone: "UTC" });
      assert.equal(WEEKDAYS[L][en], d.toLocaleDateString(loc, { weekday: "short", timeZone: "UTC" }), `${L} ${en}`);
    }
  }
});

test("the specific Gujarati and Hindi day/month rendering", () => {
  assert.equal(eventText(mkEvent("heat", "Heat watch tomorrow", 1), "gu").headline.text, "આવતીકાલે ગરમી પર નજર રાખો");
  assert.equal(eventText(mkEvent("cold", "Cold watch Sat 03 Oct", 1), "gu").headline.text, "શનિ 03 ઑક્ટો ઠંડી પર નજર રાખો");
  assert.equal(eventText(mkEvent("cold", "Cold watch Sat 03 Oct", 1), "hi").headline.text, "शनि 03 अक्टू॰ ठंड पर नज़र रखें");
  assert.equal(eventText(mkEvent("rain", "Rather heavy rain today (58 mm)"), "hi").headline.text, "आज कुछ भारी वर्षा (58 मिमी)");
});
