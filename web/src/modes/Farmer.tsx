import { ExternalLink, ShieldCheck, Sprout } from "lucide-react";
import { useEffect, useState } from "react";
import { core } from "../core-api/client";
import type { CoreCropList, CoreDistrict, CoreFarmerReport, CoreState } from "../core-api/types";
import { EventCard } from "../components/EventCard";
import { LevelDot, Load, OfficialAlert, Provenance, Section, SystemLabel } from "../components/ui";
import { v2 } from "../v2-api/client";
import type { V2Events } from "../v2-api/types";
import { istDay, num } from "../lib/format";
import { FARMER_LINK, LEVEL } from "../lib/present";
import { useApp } from "../lib/store";
import { useCore } from "../lib/useCore";
import { coreText, cropName, indicatorText, levelName, seasonName, stageName, type Lang, type Out } from "../i18n/coreText";
import { dateLocale, LANG_LABEL, uiText, useLang } from "../i18n/lang";

/**
 * A rendered string. When Gujarati was asked for but only CORE's English exists, the English is shown as is,
 * marked lang="en" so it is never mistaken for a translation.
 */
function Tx({ o, lang }: { o: Out; lang: Lang }) {
  if (lang !== "en" && !o.tr && o.text) return <span lang="en" data-untranslated title={uiText(lang).english_kept}>{o.text}</span>;
  return <>{o.text}</>;
}

export function LangSwitch() {
  const { lang, setLang } = useLang();
  const t = uiText(lang);
  return (
    <div className="flex items-center justify-end gap-1 text-[13px]" role="group" aria-label={t.lang_switch} data-testid="farmer-lang">
      {(["en", "gu", "hi"] as const).map((l) => (
        <button key={l} type="button" onClick={() => setLang(l)} aria-pressed={lang === l} data-lang={l}
          className={`h-8 rounded-md border px-3 ${lang === l ? "border-accent bg-accent/15 text-text" : "border-line text-muted hover:text-text"}`}>
          {LANG_LABEL[l]}
        </button>
      ))}
    </div>
  );
}

/** Farmer workflow: Location → District → Village/point → Crop → Growth stage → CORE's existing indicators. */
export default function FarmerWorkflow() {
  const { place, setPlace, crop, setCrop } = useApp();
  const lang = useLang((s) => s.lang);
  const t = uiText(lang);
  const states = useCore<CoreState[]>("states", core.states);
  const crops = useCore<CoreCropList>("crops", core.crops);
  const [stateSlug, setStateSlug] = useState<string>("");
  const districts = useCore<CoreDistrict[]>(stateSlug ? `districts:${stateSlug}` : null, () => core.districts(stateSlug));

  // preselect the state of the current place
  useEffect(() => {
    if (stateSlug || states.state !== "ok" || !place.state) return;
    const s = states.data.find((x) => x.state === place.state);
    if (s) setStateSlug(s.state_slug);
  }, [states, place.state, stateSlug]);

  const cropList = crops.state === "ok" ? crops.data.crops : [];
  const cur = cropList.find((c) => c.id === crop?.crop);
  const validStage = cur && crop && cur.stages.includes(crop.stage);
  const report = useCore<CoreFarmerReport>(
    validStage ? `farmer:${place.lat},${place.lon},${crop!.crop},${crop!.stage}` : null,
    () => core.farmer(place.lat, place.lon, crop!.crop, crop!.stage, place.name, place.taluka),
  );

  return (
    <div className="space-y-6" data-testid="farmer" lang={lang}>
      <Section title={t.field_title}>
        <ol className="grid gap-3 text-[13px] sm:grid-cols-2 lg:grid-cols-4">
          <li>
            <label className="text-muted">{t.loc_state}</label>
            <select value={stateSlug} onChange={(e) => setStateSlug(e.target.value)} className="mt-1 h-10 w-full rounded-lg border border-line bg-surface px-2">
              <option value="">{t.sel_state}</option>
              {states.state === "ok" && states.data.map((s) => <option key={s.state_slug} value={s.state_slug}>{s.state}</option>)}
            </select>
          </li>
          <li>
            <label className="text-muted">{t.loc_district}</label>
            <select value={place.district ?? ""} disabled={districts.state !== "ok"}
              onChange={(e) => {
                const d = districts.state === "ok" ? districts.data.find((x) => x.district === e.target.value) : null;
                const st = states.state === "ok" ? states.data.find((x) => x.state_slug === stateSlug)?.state : null;
                if (d) setPlace({ name: `${d.district} (district point)`, lat: d.lat, lon: d.lon, district: d.district, state: st ?? null, via: "district" });
              }}
              className="mt-1 h-10 w-full rounded-lg border border-line bg-surface px-2 disabled:opacity-50">
              <option value="">{t.sel_district}</option>
              {districts.state === "ok" && districts.data.map((d) => <option key={d.id} value={d.district}>{d.district}</option>)}
            </select>
          </li>
          <li>
            <label className="text-muted">{t.crop}</label>
            <select value={crop?.crop ?? ""} onChange={(e) => { const c = cropList.find((x) => x.id === e.target.value); if (c) setCrop({ crop: c.id, stage: c.stages[0] }); }}
              className="mt-1 h-10 w-full rounded-lg border border-line bg-surface px-2">
              <option value="">{t.sel_crop}</option>
              {cropList.map((c) => <option key={c.id} value={c.id}>{cropName(c.id, c.label, lang).text} ({seasonName(c.season, lang).text})</option>)}
            </select>
          </li>
          <li>
            <label className="text-muted">{t.stage}</label>
            <select value={validStage ? crop!.stage : ""} disabled={!cur} onChange={(e) => setCrop({ crop: cur!.id, stage: e.target.value })}
              className="mt-1 h-10 w-full rounded-lg border border-line bg-surface px-2 disabled:opacity-50">
              <option value="">{t.sel_stage}</option>
              {cur?.stages.map((s) => <option key={s} value={s}>{stageName(s, lang).text}</option>)}
            </select>
          </li>
        </ol>
        <p className="mt-2 text-[12px] text-muted">
          {t.field_location} <span className="text-text">{place.name}</span> ({place.lat.toFixed(3)}, {place.lon.toFixed(3)}). {t.field_help}
          {validStage && <> {t.official_later}</>}
        </p>
      </Section>

      {!validStage && <p className="text-[13.5px] text-muted">{t.choose_prompt}</p>}

      {validStage && (
        <Load s={report} lines={6}>
          {(r) => {
            const cropLabel = cropName(r.crop, r.crop_label, lang);
            const stage = stageName(r.stage, lang);
            return (
              <div className="space-y-6">
                {/* 4 · WEATHER */}
                <Section title={t.weather_title}>
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[560px] text-[12.5px] tabular-nums" data-testid="farmer-days">
                      <thead className="text-left text-muted"><tr className="border-b border-line">
                        <th className="py-1.5 font-normal">{t.th_day}</th><th className="pl-3 text-right font-normal">{t.th_temp}</th><th className="pl-3 text-right font-normal">{t.th_rain}</th>
                        <th className="pl-3 text-right font-normal">{t.th_chance}</th><th className="pl-3 text-right font-normal">{t.th_spray}</th><th className="pl-3 text-right font-normal">{t.th_disease}</th>
                      </tr></thead>
                      <tbody>{r.days.map((d) => (
                        <tr key={d.date} className="border-b border-line/60">
                          <td className="py-1.5">{istDay(d.date, undefined, dateLocale(lang))}</td><td className="text-right">{num(d.tmax)} / {num(d.tmin)}</td><td className="text-right">{num(d.rain, 1)}</td>
                          <td className="text-right">{num(d.rain_prob)}%</td><td className="text-right">{num(d.spray_hours)}</td><td className="text-right">{num(d.disease_hours)}</td>
                        </tr>
                      ))}</tbody>
                    </table>
                  </div>
                  <p className="mt-2 text-[11.5px] text-muted">{t.weather_note}</p>
                </Section>

                {/* 5 · SYSTEM INDICATORS — SYSTEM-DERIVED, UNVALIDATED */}
                <section className="rounded-xl border border-system/40 bg-system/[0.07] p-4" data-testid="farmer-indicators">
                  <div className="flex flex-wrap items-center gap-2 text-[11px] font-semibold uppercase tracking-wide text-slate-200">
                    <Sprout size={14} /> {t.ind_title}
                    <span className="rounded bg-system/40 px-1.5 py-0.5" data-testid="badge-system-derived">{t.badge_system}</span>
                    <span className="rounded bg-amber-500/25 px-1.5 py-0.5 text-amber-100" data-testid="badge-unvalidated">{t.badge_unvalidated}</span>
                    <span className="font-normal normal-case text-muted">{t.core_status} <Tx o={coreText(r.validation_status, lang)} lang={lang} /></span>
                  </div>
                  <h3 className="mt-1 text-[15px] font-medium"><Tx o={cropLabel} lang={lang} /> — <Tx o={stage} lang={lang} /> (<Tx o={seasonName(r.season, lang)} lang={lang} />)</h3>
                  <p className="mt-1 text-[12.5px] text-amber-200/90" data-testid="farmer-disclaimer"><Tx o={coreText(r.disclaimer, lang)} lang={lang} /></p>
                  <div className="mt-3 grid gap-2 sm:grid-cols-2">
                    {r.indicators.map((i) => {
                      const x = indicatorText(i, lang);
                      return (
                        <div key={i.id} className="flex items-start gap-2.5 rounded-lg border border-line bg-surface px-3 py-2" data-testid="farmer-indicator" data-id={i.id} data-level={i.level}>
                          <LevelDot level={i.level} />
                          <div className="min-w-0 text-[13px]">
                            <div><span className="font-medium"><Tx o={x.label} lang={lang} /></span> <span className={LEVEL[i.level]?.text}>{levelName(i.level, lang) ?? LEVEL[i.level]?.name}</span></div>
                            <div className="text-muted"><Tx o={x.value} lang={lang} /></div>
                            <div className="text-[11.5px] text-muted">{t.rule} <Tx o={x.rule} lang={lang} /> · {t.rule_suffix}</div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  {r.crop_note && <p className="mt-2 text-[12px] text-muted"><Tx o={coreText(r.crop_note, lang)} lang={lang} /></p>}
                </section>

                {/* 6 · POTENTIAL CROP RELEVANCE */}
                <FarmerEvents report={r} lang={lang} cropLabel={cropLabel} stage={stage} />

                {/* 7 · OFFICIAL ADVISORY — separate block, never mixed with system output */}
                <section className="rounded-xl border border-emerald-500/40 bg-emerald-500/[0.06] p-4" data-testid="official-advisory">
                  <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wide text-emerald-300"><ShieldCheck size={14} /> {t.off_head}</div>
                  <h3 className="mt-1 text-[15px] font-medium"><Tx o={coreText(r.official.title, lang)} lang={lang} /></h3>
                  <p className="mt-1 text-[13px] text-muted"><Tx o={coreText(r.official.note, lang)} lang={lang} /></p>
                  <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[13px]">
                    {r.official.links.map((l) => <li key={l.url}><a href={l.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-accent hover:underline"><Tx o={coreText(l.label, lang)} lang={lang} /> <ExternalLink size={11} /></a></li>)}
                  </ul>
                  <p className="mt-2 text-[11.5px] text-muted"><Tx o={coreText(r.official.integration, lang)} lang={lang} /></p>
                  <p className="mt-1 text-[11.5px] text-muted">{t.off_sep}</p>
                </section>

                {r.warnings.length > 0 && (
                  <Section title={t.alerts_title}>
                    {t.alerts_note && <p className="mb-2 text-[12px] text-muted">{t.alerts_note}</p>}
                    <div className="space-y-2" lang="en">{r.warnings.map((w) => <OfficialAlert key={w.id} w={w} />)}</div>
                  </Section>
                )}
                <Provenance sources={r.sources} />
              </div>
            );
          }}
        </Load>
      )}
    </div>
  );
}

/**
 * M2: SYSTEM ASSESSMENT → potential crop relevance → existing CORE crop indicator → official advisory.
 * Uses the same /api/v2/events records and evidence drawer as Citizen and Government. No new agronomic rules.
 */
function FarmerEvents({ report, lang, cropLabel, stage }: { report: CoreFarmerReport; lang: Lang; cropLabel: Out; stage: Out }) {
  const place = useApp((s) => s.place);
  const t = uiText(lang);
  const ev = useCore<V2Events>(`events:${place.lat},${place.lon},${place.name}`, () => v2.events(place));
  return (
    <Section title={t.rel_title} right={<SystemLabel label={t.system_label} />}>
      <Load s={ev} lines={3}>
        {(d) => {
          const events = d.events.filter((e) => e.classification === "system");
          if (!events.length) return <p className="text-[13px] text-muted" data-testid="farmer-events-none">{t.rel_none}</p>;
          return (
            <div className="space-y-3" data-testid="farmer-events">
              {events.map((e) => {
                const link = FARMER_LINK[e.type];
                const inds = link ? report.indicators.filter((i) => link.ids.includes(i.id)) : [];
                return (
                  <div key={e.id} className="grid gap-2 rounded-xl border border-line p-2.5 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]" data-testid="farmer-event-chain" data-event-type={e.type}>
                    <EventCard e={e} audience="farmer" lang={lang} />
                    <div className="space-y-1.5 text-[12.5px]">
                      <div className="text-[11px] font-semibold uppercase tracking-wide text-muted">{t.rel_head}</div>
                      {inds.length ? (
                        <>
                          <p className="text-muted">{t.rel_uses(inds.length, cropLabel.text, stage.text, t.why[link!.why] ?? link!.why)}</p>
                          {inds.map((i) => {
                            const x = indicatorText(i, lang);
                            return (
                              <div key={i.id} className="flex items-start gap-2 rounded-lg border border-system/40 bg-system/[0.07] px-2.5 py-1.5" data-testid="farmer-linked-indicator" data-id={i.id} data-level={i.level}>
                                <LevelDot level={i.level} />
                                <div><span className="font-medium"><Tx o={x.label} lang={lang} /></span> <span className={LEVEL[i.level]?.text}>{levelName(i.level, lang) ?? LEVEL[i.level]?.name}</span> · <Tx o={x.value} lang={lang} /><div className="text-[11px] text-muted">{t.rule} <Tx o={x.rule} lang={lang} /> · <Tx o={coreText(report.validation_status, lang)} lang={lang} /></div></div>
                              </div>
                            );
                          })}
                        </>
                      ) : (
                        <p className="text-muted" data-testid="farmer-no-indicator">{t.rel_no_ind(cropLabel.text)}</p>
                      )}
                      <p className="text-[11.5px] text-muted">{t.rel_official(coreText(report.official.title, lang).text)}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          );
        }}
      </Load>
    </Section>
  );
}
