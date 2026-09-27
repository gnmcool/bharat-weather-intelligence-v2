import { ExternalLink, ShieldCheck, Sprout } from "lucide-react";
import { useEffect, useState } from "react";
import { core } from "../core-api/client";
import type { CoreCropList, CoreDistrict, CoreFarmerReport, CoreState } from "../core-api/types";
import { LevelDot, Load, OfficialAlert, Provenance, Section } from "../components/ui";
import { istDay, num } from "../lib/format";
import { LEVEL } from "../lib/present";
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
      <Section title="Your field">
        <ol className="grid gap-3 text-[13px] sm:grid-cols-2 lg:grid-cols-4">
          <li>
            <label className="text-muted">1 · State</label>
            <select value={stateSlug} onChange={(e) => setStateSlug(e.target.value)} className="mt-1 h-10 w-full rounded-lg border border-line bg-surface px-2">
              <option value="">Select state</option>
              {states.state === "ok" && states.data.map((s) => <option key={s.state_slug} value={s.state_slug}>{s.state}</option>)}
            </select>
          </li>
          <li>
            <label className="text-muted">2 · District</label>
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
            <label className="text-muted">3 · Crop</label>
            <select value={crop?.crop ?? ""} onChange={(e) => { const c = cropList.find((x) => x.id === e.target.value); if (c) setCrop({ crop: c.id, stage: c.stages[0] }); }}
              className="mt-1 h-10 w-full rounded-lg border border-line bg-surface px-2">
              <option value="">Select crop</option>
              {cropList.map((c) => <option key={c.id} value={c.id}>{c.label} ({c.season})</option>)}
            </select>
          </li>
          <li>
            <label className="text-muted">4 · Growth stage</label>
            <select value={validStage ? crop!.stage : ""} disabled={!cur} onChange={(e) => setCrop({ crop: cur!.id, stage: e.target.value })}
              className="mt-1 h-10 w-full rounded-lg border border-line bg-surface px-2 disabled:opacity-50">
              <option value="">Select stage</option>
              {cur?.stages.map((s) => <option key={s} value={s}>{stageName(s)}</option>)}
            </select>
          </li>
        </ol>
        <p className="mt-2 text-[12px] text-muted">
          Field location: <span className="text-text">{place.name}</span> ({place.lat.toFixed(3)}, {place.lon.toFixed(3)}). For a village, use the location search at the top; the forecast is a point forecast at model-grid resolution.
        </p>
      </Section>

      {!validStage && <p className="text-[13.5px] text-muted">Choose a crop and growth stage to see weather indicators for your field.</p>}

      {validStage && (
        <Load s={report} lines={6}>
          {(r) => (
            <div className="space-y-6">
              {/* OFFICIAL ADVISORY — always first, always separate */}
              <section className="rounded-xl border border-emerald-500/40 bg-emerald-500/[0.06] p-4" data-testid="official-advisory">
                <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wide text-emerald-300"><ShieldCheck size={14} /> Official agricultural advisory</div>
                <h3 className="mt-1 text-[15px] font-medium">{r.official.title}</h3>
                <p className="mt-1 text-[13px] text-muted">{r.official.note}</p>
                <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[13px]">
                  {r.official.links.map((l) => <li key={l.url}><a href={l.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-accent hover:underline">{l.label} <ExternalLink size={11} /></a></li>)}
                </ul>
                <p className="mt-2 text-[11.5px] text-muted">{r.official.integration}</p>
              </section>

              {r.warnings.length > 0 && (
                <Section title="Official weather alerts for this area">
                  <div className="space-y-2">{r.warnings.map((w) => <OfficialAlert key={w.id} w={w} />)}</div>
                </Section>
              )}

              {/* SYSTEM-DERIVED — clearly unvalidated */}
              <section className="rounded-xl border border-system/40 bg-system/[0.07] p-4" data-testid="farmer-indicators">
                <div className="flex flex-wrap items-center gap-2 text-[11px] font-semibold uppercase tracking-wide text-slate-200">
                  <Sprout size={14} /> System-derived indicators · {r.validation_status}
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
                        <div className="text-[11.5px] text-muted">Rule: {i.rule}</div>
                      </div>
                    </div>
                  ))}
                </div>
                {r.crop_note && <p className="mt-2 text-[12px] text-muted">{r.crop_note}</p>}
              </section>

              <Section title="Next days for field work">
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[560px] text-[12.5px] tabular-nums" data-testid="farmer-days">
                    <thead className="text-left text-muted"><tr className="border-b border-line">
                      <th className="py-1.5 font-normal">Day</th><th className="text-right font-normal">Max / min °C</th><th className="text-right font-normal">Rain mm</th>
                      <th className="text-right font-normal">Chance</th><th className="text-right font-normal">Spray-suitable hours</th><th className="text-right font-normal">Disease-favourable hours</th>
                    </tr></thead>
                    <tbody>{r.days.map((d) => (
                      <tr key={d.date} className="border-b border-line/60">
                        <td className="py-1.5">{istDay(d.date)}</td><td className="text-right">{num(d.tmax)} / {num(d.tmin)}</td><td className="text-right">{num(d.rain, 1)}</td>
                        <td className="text-right">{num(d.rain_prob)}%</td><td className="text-right">{num(d.spray_hours)}</td><td className="text-right">{num(d.disease_hours)}</td>
                      </tr>
                    ))}</tbody>
                  </table>
                </div>
                <p className="mt-2 text-[11.5px] text-muted">Spray and disease hours are system-derived indicators from CORE's unvalidated thresholds.</p>
              </Section>
              <Provenance sources={r.sources} />
            </div>
          )}
        </Load>
      )}
    </div>
  );
}
