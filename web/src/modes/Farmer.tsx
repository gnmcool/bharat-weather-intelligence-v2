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

const stageName = (s: string) => s.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());

/** Farmer workflow: Location → District → Village/point → Crop → Growth stage → CORE's existing indicators. */
export default function FarmerWorkflow() {
  const { place, setPlace, crop, setCrop } = useApp();
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
    <div className="space-y-6" data-testid="farmer">
      <Section title="Your field — location, crop, growth stage">
        <ol className="grid gap-3 text-[13px] sm:grid-cols-2 lg:grid-cols-4">
          <li>
            <label className="text-muted">1 · Location — state</label>
            <select value={stateSlug} onChange={(e) => setStateSlug(e.target.value)} className="mt-1 h-10 w-full rounded-lg border border-line bg-surface px-2">
              <option value="">Select state</option>
              {states.state === "ok" && states.data.map((s) => <option key={s.state_slug} value={s.state_slug}>{s.state}</option>)}
            </select>
          </li>
          <li>
            <label className="text-muted">1 · Location — district</label>
            <select value={place.district ?? ""} disabled={districts.state !== "ok"}
              onChange={(e) => {
                const d = districts.state === "ok" ? districts.data.find((x) => x.district === e.target.value) : null;
                const st = states.state === "ok" ? states.data.find((x) => x.state_slug === stateSlug)?.state : null;
                if (d) setPlace({ name: `${d.district} (district point)`, lat: d.lat, lon: d.lon, district: d.district, state: st ?? null, via: "district" });
              }}
              className="mt-1 h-10 w-full rounded-lg border border-line bg-surface px-2 disabled:opacity-50">
              <option value="">Select district</option>
              {districts.state === "ok" && districts.data.map((d) => <option key={d.id} value={d.district}>{d.district}</option>)}
            </select>
          </li>
          <li>
            <label className="text-muted">2 · Crop</label>
            <select value={crop?.crop ?? ""} onChange={(e) => { const c = cropList.find((x) => x.id === e.target.value); if (c) setCrop({ crop: c.id, stage: c.stages[0] }); }}
              className="mt-1 h-10 w-full rounded-lg border border-line bg-surface px-2">
              <option value="">Select crop</option>
              {cropList.map((c) => <option key={c.id} value={c.id}>{c.label} ({c.season})</option>)}
            </select>
          </li>
          <li>
            <label className="text-muted">3 · Growth stage</label>
            <select value={validStage ? crop!.stage : ""} disabled={!cur} onChange={(e) => setCrop({ crop: cur!.id, stage: e.target.value })}
              className="mt-1 h-10 w-full rounded-lg border border-line bg-surface px-2 disabled:opacity-50">
              <option value="">Select stage</option>
              {cur?.stages.map((s) => <option key={s} value={s}>{stageName(s)}</option>)}
            </select>
          </li>
        </ol>
        <p className="mt-2 text-[12px] text-muted">
          Field location: <span className="text-text">{place.name}</span> ({place.lat.toFixed(3)}, {place.lon.toFixed(3)}). For a village, use the location search at the top; the forecast is a point forecast at model-grid resolution.
          {validStage && <> The official agricultural advisory is shown separately in step 7.</>}
        </p>
      </Section>

      {!validStage && <p className="text-[13.5px] text-muted">Choose a crop and growth stage to see weather indicators for your field.</p>}

      {validStage && (
        <Load s={report} lines={6}>
          {(r) => (
            <div className="space-y-6">
              {/* 4 · WEATHER */}
              <Section title="4 · Weather — next days at your field">
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[560px] text-[12.5px] tabular-nums" data-testid="farmer-days">
                    <thead className="text-left text-muted"><tr className="border-b border-line">
                      <th className="py-1.5 font-normal">Day</th><th className="text-right font-normal">Max / min °C</th><th className="text-right font-normal">Rain mm</th>
                      <th className="text-right font-normal">Chance</th><th className="text-right font-normal">Spray-suitable hours*</th><th className="text-right font-normal">Disease-favourable hours*</th>
                    </tr></thead>
                    <tbody>{r.days.map((d) => (
                      <tr key={d.date} className="border-b border-line/60">
                        <td className="py-1.5">{istDay(d.date)}</td><td className="text-right">{num(d.tmax)} / {num(d.tmin)}</td><td className="text-right">{num(d.rain, 1)}</td>
                        <td className="text-right">{num(d.rain_prob)}%</td><td className="text-right">{num(d.spray_hours)}</td><td className="text-right">{num(d.disease_hours)}</td>
                      </tr>
                    ))}</tbody>
                  </table>
                </div>
                <p className="mt-2 text-[11.5px] text-muted">Forecast values from CORE. *Spray and disease hours are system-derived, unvalidated indicators from CORE's thresholds.</p>
              </Section>

              {/* 5 · SYSTEM INDICATORS — SYSTEM-DERIVED, UNVALIDATED */}
              <section className="rounded-xl border border-system/40 bg-system/[0.07] p-4" data-testid="farmer-indicators">
                <div className="flex flex-wrap items-center gap-2 text-[11px] font-semibold uppercase tracking-wide text-slate-200">
                  <Sprout size={14} /> 5 · System indicators
                  <span className="rounded bg-system/40 px-1.5 py-0.5" data-testid="badge-system-derived">System-derived</span>
                  <span className="rounded bg-amber-500/25 px-1.5 py-0.5 text-amber-100" data-testid="badge-unvalidated">Unvalidated</span>
                  <span className="font-normal normal-case text-muted">CORE status: {r.validation_status}</span>
                </div>
                <h3 className="mt-1 text-[15px] font-medium">{r.crop_label} — {stageName(r.stage)} ({r.season})</h3>
                <p className="mt-1 text-[12.5px] text-amber-200/90">{r.disclaimer}</p>
                <div className="mt-3 grid gap-2 sm:grid-cols-2">
                  {r.indicators.map((i) => (
                    <div key={i.id} className="flex items-start gap-2.5 rounded-lg border border-line bg-surface px-3 py-2" data-testid="farmer-indicator" data-id={i.id} data-level={i.level}>
                      <LevelDot level={i.level} />
                      <div className="min-w-0 text-[13px]">
                        <div><span className="font-medium">{i.label}</span> <span className={LEVEL[i.level]?.text}>{LEVEL[i.level]?.name}</span></div>
                        <div className="text-muted">{i.value}</div>
                        <div className="text-[11.5px] text-muted">Rule: {i.rule} · system-derived, unvalidated</div>
                      </div>
                    </div>
                  ))}
                </div>
                {r.crop_note && <p className="mt-2 text-[12px] text-muted">{r.crop_note}</p>}
              </section>

              {/* 6 · POTENTIAL CROP RELEVANCE */}
              <FarmerEvents report={r} />

              {/* 7 · OFFICIAL ADVISORY — separate block, never mixed with system output */}
              <section className="rounded-xl border border-emerald-500/40 bg-emerald-500/[0.06] p-4" data-testid="official-advisory">
                <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wide text-emerald-300"><ShieldCheck size={14} /> 7 · Official agricultural advisory</div>
                <h3 className="mt-1 text-[15px] font-medium">{r.official.title}</h3>
                <p className="mt-1 text-[13px] text-muted">{r.official.note}</p>
                <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[13px]">
                  {r.official.links.map((l) => <li key={l.url}><a href={l.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-accent hover:underline">{l.label} <ExternalLink size={11} /></a></li>)}
                </ul>
                <p className="mt-2 text-[11.5px] text-muted">{r.official.integration}</p>
                <p className="mt-1 text-[11.5px] text-muted">Steps 5 and 6 are system output, not an official agricultural advisory. For farm decisions, follow the official advisory.</p>
              </section>

              {r.warnings.length > 0 && (
                <Section title="Official weather alerts for this area">
                  <div className="space-y-2">{r.warnings.map((w) => <OfficialAlert key={w.id} w={w} />)}</div>
                </Section>
              )}
              <Provenance sources={r.sources} />
            </div>
          )}
        </Load>
      )}
    </div>
  );
}

/**
 * M2: SYSTEM ASSESSMENT → potential crop relevance → existing CORE crop indicator → official advisory.
 * Uses the same /api/v2/events records and evidence drawer as Citizen and Government. No new agronomic rules.
 */
function FarmerEvents({ report }: { report: CoreFarmerReport }) {
  const place = useApp((s) => s.place);
  const ev = useCore<V2Events>(`events:${place.lat},${place.lon},${place.name}`, () => v2.events(place));
  return (
    <Section title="6 · Potential crop relevance — weather events" right={<SystemLabel />}>
      <Load s={ev} lines={3}>
        {(d) => {
          const events = d.events.filter((e) => e.classification === "system");
          if (!events.length) return <p className="text-[13px] text-muted" data-testid="farmer-events-none">No significant weather event detected for this field in CORE's 7-day assessment.</p>;
          return (
            <div className="space-y-3" data-testid="farmer-events">
              {events.map((e) => {
                const link = FARMER_LINK[e.type];
                const inds = link ? report.indicators.filter((i) => link.ids.includes(i.id)) : [];
                return (
                  <div key={e.id} className="grid gap-2 rounded-xl border border-line p-2.5 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]" data-testid="farmer-event-chain" data-event-type={e.type}>
                    <EventCard e={e} audience="farmer" />
                    <div className="space-y-1.5 text-[12.5px]">
                      <div className="text-[11px] font-semibold uppercase tracking-wide text-muted">Potential crop relevance</div>
                      {inds.length ? (
                        <>
                          <p className="text-muted">Existing CORE indicator{inds.length > 1 ? "s" : ""} for {report.crop_label} ({stageName(report.stage)}) that use {link!.why}:</p>
                          {inds.map((i) => (
                            <div key={i.id} className="flex items-start gap-2 rounded-lg border border-system/40 bg-system/[0.07] px-2.5 py-1.5" data-testid="farmer-linked-indicator" data-id={i.id} data-level={i.level}>
                              <LevelDot level={i.level} />
                              <div><span className="font-medium">{i.label}</span> <span className={LEVEL[i.level]?.text}>{LEVEL[i.level]?.name}</span> · {i.value}<div className="text-[11px] text-muted">Rule: {i.rule} · {report.validation_status}</div></div>
                            </div>
                          ))}
                        </>
                      ) : (
                        <p className="text-muted" data-testid="farmer-no-indicator">No existing CORE crop indicator for {report.crop_label} at this stage uses this signal. V2 does not add agronomic rules.</p>
                      )}
                      <p className="text-[11.5px] text-muted">Official advisory: {report.official.title} — step 7 below.</p>
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
