// Gujarati rendering of CORE farmer text. Run: npm test (node --experimental-strip-types --test).
// The fixture is CORE's real output (CORE 2840f8d farmer.assess on synthetic weather), not a copy of its templates.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  coreText, cropName, CROP_GU, indicatorText, LEVEL_GU, seasonName, SEASON_GU, stageName, STAGE_GU,
} from "../src/i18n/coreText.ts";

const fx = JSON.parse(readFileSync(new URL("./fixtures/core_farmer_text.json", import.meta.url), "utf8"));
// Same numbers, same text form (Gujarati word order may move "of 7" before the count; checked separately below).
const nums = (s: string) => (s.match(/\d+(?:\.\d+)?/g) ?? []).sort().join(",");
const GUJ = /[઀-૿]/;

test("fixture comes from frozen CORE 2840f8d", () => {
  assert.equal(fx.core_commit, "2840f8d");
  assert.ok(fx.indicators.length >= 50);
});

test("every CORE indicator sentence is translated, field by field", () => {
  for (const i of fx.indicators) {
    const o = indicatorText(i, "gu");
    for (const f of ["label", "value", "rule"] as const) {
      assert.ok(o[f].gu, `${i.id}.${f} not translated: ${i[f]}`);
      assert.match(o[f].text, GUJ, `${i.id}.${f}`);
    }
  }
});

test("numbers are copied unchanged (value and rule)", () => {
  for (const i of fx.indicators) {
    const o = indicatorText(i, "gu");
    assert.equal(nums(o.value.text), nums(i.value), `value ${i.value} → ${o.value.text}`);
    // heavy_rain's rule numbers are CORE constants; all others carry the thresholds through
    assert.equal(nums(o.rule.text), nums(i.rule), `rule ${i.rule} → ${o.rule.text}`);
    const m = i.value.match(/^(\d+) of 7 (days|nights) (≥|≤) (\d+) °C$/);
    if (m) assert.equal(o.value.text, `7 માંથી ${m[1]} ${m[2] === "days" ? "દિવસ" : "રાત"} ${m[3]} ${m[4]} °C`);
  }
});

test("English mode returns CORE text unchanged", () => {
  for (const i of fx.indicators) {
    const o = indicatorText(i, "en");
    assert.deepEqual([o.label.text, o.value.text, o.rule.text], [i.label, i.value, i.rule]);
    assert.ok(!o.label.gu && !o.value.gu && !o.rule.gu);
  }
  assert.equal(coreText(fx.paragraphs.disclaimer, "en").text, fx.paragraphs.disclaimer);
});

test("changed or unknown CORE wording falls back to English, never a guess", () => {
  const base = fx.indicators.find((i: { id: string }) => i.id === "heat_stress");
  const cases = [
    { ...base, label: "Heat stress (new wording)" },
    { ...base, value: "3 of 10 days ≥ 34 °C" },
    { ...base, rule: "Tmax ≥ 34 °C at early flowering" }, // unknown stage
    { ...base, id: "new_indicator" },
  ];
  const o0 = indicatorText(cases[0], "gu");
  assert.ok(!o0.label.gu && o0.label.text === cases[0].label && o0.value.gu);
  assert.ok(!indicatorText(cases[1], "gu").value.gu);
  assert.ok(!indicatorText(cases[2], "gu").rule.gu);
  const o3 = indicatorText(cases[3], "gu");
  assert.ok(!o3.label.gu && !o3.value.gu && !o3.rule.gu);
  assert.deepEqual(coreText(fx.paragraphs.disclaimer + " ", "gu"), { text: fx.paragraphs.disclaimer + " ", gu: false });
  assert.deepEqual(coreText(null, "gu"), { text: "", gu: false });
});

test("the disclaimer and official advisory text are translated, and keep the 'not instructions' meaning", () => {
  const p = fx.paragraphs;
  for (const k of ["disclaimer", "official_title", "official_note", "official_integration", "validation_status"]) {
    assert.ok(coreText(p[k], "gu").gu, `${k} not translated`);
  }
  const d = coreText(p.disclaimer, "gu").text;
  assert.match(d, /સૂચના નથી/); // "not instructions"
  assert.match(d, /સત્તાવાર/); // "official"
  for (const l of fx.link_labels) assert.ok(coreText(l, "gu").gu, `link ${l}`);
  assert.match(coreText(fx.link_labels[2], "gu").text, /1800-180-1551/);
});

test("every crop, season, stage and crop note in CORE's crops.yaml has Gujarati", () => {
  for (const [id, c] of Object.entries<{ label: string; season: string; stages: string[]; note: string | null }>(fx.crops)) {
    assert.ok(cropName(id, c.label, "gu").gu, id);
    assert.ok(seasonName(c.season, "gu").gu, c.season);
    for (const s of c.stages) assert.ok(stageName(s, "gu").gu, `${id}.${s}`);
    if (c.note) assert.ok(coreText(c.note, "gu").gu, `${id} note`);
  }
  assert.equal(Object.keys(CROP_GU).length, Object.keys(fx.crops).length);
  const stages = new Set(Object.values<{ stages: string[] }>(fx.crops).flatMap((c) => c.stages));
  assert.deepEqual(Object.keys(STAGE_GU).sort(), [...stages].sort(), "no stale or missing stages");
  assert.deepEqual(Object.keys(SEASON_GU).sort(), [...new Set(Object.values<{ season: string }>(fx.crops).map((c) => c.season))].sort());
});

test("four levels, matching CORE's 0–3 scale", () => {
  assert.equal(LEVEL_GU.length, 4);
});
