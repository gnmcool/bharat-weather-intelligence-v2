import { ShieldAlert } from "lucide-react";
import { useMemo, useState } from "react";
import { Download, FileText } from "lucide-react";
import { coreUrl } from "../core-api/client";
import { DataQualityNotice, DataQualityNotices } from "../components/DataQualityNotice";
import { EvidenceButton, LevelDot, Load, OfficialAlert, Section, SystemLabel } from "../components/ui";
import { istDateTime as fmtWhen } from "../lib/format";
import type { V2Events } from "../v2-api/types";
import { istDateTime, num } from "../lib/format";
import { LEVEL } from "../lib/present";
import { useApp } from "../lib/store";
import { useCore } from "../lib/useCore";
import WeatherMap from "../map/WeatherMap";
import { v2 } from "../v2-api/client";
import type { V2District, V2IndiaRisks } from "../v2-api/types";

import { LEVEL_FILL, OFFICIAL_OUTLINE } from "./levelColors";
export { LEVEL_FILL, OFFICIAL_OUTLINE };

export function useIndiaRisks() {
  return useCore<V2IndiaRisks>("v2:india-risks", v2.indiaRisks);
}

/** district id → fill colour for one hazard. Exactly the districts counted for that hazard. */
export function hazardFill(d: V2IndiaRisks, hazard: string): Record<string, string> {
  const out: Record<string, string> = {};
  for (const x of d.districts) {
    const lv = hazard === "any" ? Math.max(...Object.values(x.levels)) : x.levels[hazard] ?? 0;
    if (lv >= 1) out[x.id] = LEVEL_FILL[lv];
  }
  return out;
}
export function officialOutline(d: V2IndiaRisks): Record<string, string> {
  const out: Record<string, string> = {};
  for (const x of d.districts) if (x.official_alerts > 0) out[x.id] = OFFICIAL_OUTLINE;
  return out;
}

export function openDistrictEvidence(openEvidence: ReturnType<typeof useApp.getState>["openEvidence"], x: V2District, hazard: string) {
  const lv = x.levels[hazard] ?? 0;
  openEvidence({
    point: { lat: x.lat, lon: x.lon, name: `${x.district} (district point)` },
    risk: hazard,
    context: `District count level: ${LEVEL[lv]?.name ?? "—"} (CORE /region/state, next 7 days). The evidence is CORE's point assessment at the same representative point.`,
  });
}

/** Government: where is the problem, how widespread is it, and when does it matter. */
export default function IndiaRisks() {
  const s = useIndiaRisks();
  return (
    <Section title="India — district risk counts" right={<SystemLabel />}>
      <Load s={s} lines={6}>{(d) => <Body d={d} />}</Load>
      {s.state === "loading" && <p className="mt-2 text-[12px] text-muted">Building counts from CORE's district tables for 36 states and UTs — the first request can take about a minute.</p>}
    </Section>
  );
}

function Body({ d }: { d: V2IndiaRisks }) {
  const { openEvidence, setGovState, govState } = useApp();
  const [hazard, setHazard] = useState(() => [...d.hazards].sort((a, b) => b.districts - a.districts)[0]?.id ?? "rain");
  const [picked, setPicked] = useState<V2District | null>(null);
  const fill = useMemo(() => hazardFill(d, hazard), [d, hazard]);
  const outline = useMemo(() => officialOutline(d), [d]);
  const byId = useMemo(() => new Map(d.districts.map((x) => [x.id, x])), [d]);
  const h = d.hazards.find((x) => x.id === hazard)!;

  return (
    <div className="space-y-4" data-testid="india-risks">
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
        {d.hazards.map((x) => (
          <button key={x.id} onClick={() => { setHazard(x.id); setPicked(null); }} data-testid="hazard-count" data-hazard={x.id} data-count={x.districts}
            className={`rounded-lg border px-3 py-2 text-left ${hazard === x.id ? "border-accent bg-accent/10" : "border-line bg-surface hover:border-accent/60"}`}>
            <div className="text-[12.5px] text-muted">{x.title}</div>
            <div className="text-[22px] font-semibold tabular-nums leading-tight">{x.districts}</div>
            <div className="text-[11.5px] leading-snug text-text/90" data-testid="count-label">{x.count_label}</div>
            <div className="mt-0.5 flex gap-2 text-[11.5px] tabular-nums">
              <span className={LEVEL[1].text}>{x.watch} watch</span><span className={LEVEL[2].text}>{x.alert} alert</span><span className={LEVEL[3].text}>{x.severe} severe</span>
            </div>
            <div className="text-[11px] text-muted">{x.count_basis} · {x.states} states/UTs</div>
          </button>
        ))}
        {/* OFFICIAL — separate tile, separate colour, never summed with system counts */}
        <div className="rounded-lg border border-official/50 bg-official/[0.08] px-3 py-2" data-testid="official-count" data-count={d.official.districts_with_alerts}>
          <div className="inline-flex items-center gap-1 text-[11px] font-semibold uppercase text-red-200"><ShieldAlert size={12} /> Official alerts</div>
          <div className="text-[22px] font-semibold tabular-nums leading-tight">{d.official.districts_with_alerts}</div>
          <div className="text-[11.5px] leading-snug text-text/90">districts named in active official alerts</div>
          <div className="text-[11.5px] text-muted">{d.official.alerts} active alerts{d.official.alerts_without_district ? ` (${d.official.alerts_without_district} without a district)` : ""}</div>
        </div>
      </div>

      <DataQualityNotices list={d.data_quality.filter((n) => n.id === "incomplete_coverage")} />
      <p className="text-[13px] font-medium" data-testid="count-statement">{d.statement}</p>
      <div className="flex flex-wrap items-center gap-1.5 text-[12px]" data-testid="not-counted">
        <span className="text-muted">Not currently included in district count:</span>
        {d.not_counted.map((n) => <span key={n.id} title={n.reason} className="rounded border border-dashed border-line px-1.5 py-0.5 text-muted" data-id={n.id}>{n.title}</span>)}
      </div>
      <DataQualityNotices list={d.data_quality.filter((n) => n.id !== "representative_point" && n.id !== "incomplete_coverage")} />

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
        <div>
          <WeatherMap className="h-[400px] w-full overflow-hidden rounded-xl border border-line lg:h-[500px]" districtFill={fill} districtOutline={outline} highlightState={govState}
            onDistrictClick={(id) => { const x = byId.get(id); if (x) setPicked(x); }} />
          <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11.5px] text-muted" data-testid="risk-map-legend" data-filled={Object.keys(fill).length}>
            <span className="text-text">{h.title}, next 7 days:</span>
            {[1, 2, 3].map((l) => <span key={l} className="inline-flex items-center gap-1"><span className="h-2.5 w-2.5 rounded-sm" style={{ background: LEVEL_FILL[l] }} />{LEVEL[l].name}</span>)}
            <span className="inline-flex items-center gap-1"><span className="h-2.5 w-3 rounded-sm border-2 border-dashed" style={{ borderColor: OFFICIAL_OUTLINE }} />Official alert (outline)</span>
            <span>{Object.keys(fill).length} district representative points coloured = count above</span>
          </div>
        </div>
        <div className="space-y-4">
          {picked ? (
            <DistrictCard x={picked} hazard={hazard} onClose={() => setPicked(null)} onState={() => setGovState(picked.state_slug)} onEvidence={() => openDistrictEvidence(openEvidence, picked, hazard)} />
          ) : (
            <p className="text-[12.5px] text-muted">Click a district on the map for its levels and evidence.</p>
          )}
          <div>
            <h3 className="text-[13px] font-medium">Where it is concentrated — {h.title}</h3>
            {h.by_state.length ? (
              <ol className="mt-1 divide-y divide-line text-[13px]" data-testid="concentration">
                {h.by_state.slice(0, 8).map((st) => (
                  <li key={st.state} className="flex items-baseline justify-between gap-3 py-1.5" data-state={st.state} data-count={st.districts}>
                    <button className="text-left hover:text-accent" onClick={() => { const x = d.districts.find((z) => z.state === st.state); if (x) setGovState(x.state_slug); }}>{st.state}</button>
                    <span className="tabular-nums"><b className="font-medium">{st.districts}</b> <span className="text-[11.5px] text-muted">({st.watch}/{st.alert}/{st.severe})</span></span>
                  </li>
                ))}
              </ol>
            ) : <p className="mt-1 text-[12.5px] text-muted">No district at Watch level or above.</p>}
            <p className="mt-1 text-[11px] text-muted">Districts with system-assessed risk at watch / alert / severe. Click a state for its district list.</p>
          </div>
          <div>
            <h3 className="text-[13px] font-medium text-red-200">Official alerts by event</h3>
            <ul className="mt-1 text-[12.5px]" data-testid="official-by-event">
              {d.official.by_event.slice(0, 6).map((e) => <li key={e.event} className="flex justify-between py-0.5"><span>{e.event}</span><span className="tabular-nums">{e.districts} districts</span></li>)}
            </ul>
            <p className="mt-1 text-[11px] text-muted">{d.official.source}</p>
          </div>
        </div>
      </div>

      {govState && <StateFocus d={d} slug={govState} hazard={hazard} onPick={setPicked} />}

      <div className="space-y-1 text-[12px] leading-relaxed text-muted">
        <p><span className="text-text">When:</span> {d.window}. CORE district tables generated {istDateTime(d.core_generated_at.oldest)} – {istDateTime(d.core_generated_at.newest)}. For the day of the peak, open a district.</p>
        <p><span className="text-text">How counted:</span> {d.method} {h.rule}</p>
        <p data-testid="coverage"><span className="text-text">Coverage:</span> {d.coverage.districts_received} of {d.coverage.districts_expected} districts
          {d.coverage.complete ? " (all states and UTs)." : ` — incomplete: ${d.coverage.states_failed.map((f) => f.state).join(", ")} failed at CORE and are not counted.`}</p>
        <p><span className="text-text">Not counted by district:</span> {d.not_counted.map((n) => n.title).join(", ")} — CORE evaluates these only at points (see each location's assessment).</p>
        <details><summary className="cursor-pointer underline decoration-dotted underline-offset-2">Limitations</summary>
          <ul className="mt-1 list-disc space-y-1 pl-5">{d.limitations.map((l) => <li key={l}>{l}</li>)}{d.not_counted.map((n) => <li key={n.id}>{n.title}: {n.reason}</li>)}</ul>
        </details>
        <p>{d.classification_label}. Official alerts are shown separately and are never added to system counts. No impact (damage, loss, flooding) is estimated from these counts.</p>
      </div>
    </div>
  );
}

function DistrictCard({ x, hazard, onClose, onState, onEvidence }: { x: V2District; hazard: string; onClose: () => void; onState: () => void; onEvidence: () => void }) {
  return (
    <div className="rounded-lg border border-line bg-surface p-3 text-[12.5px]" data-testid="district-card" data-district={x.id}>
      <div className="flex items-start justify-between gap-2">
        <div><div className="text-[14px] font-medium">{x.district}</div><div className="text-muted">{x.state} · representative point {x.lat.toFixed(3)}, {x.lon.toFixed(3)}</div></div>
        <button onClick={onClose} className="text-muted" aria-label="Close">×</button>
      </div>
      <div className="mt-2 grid grid-cols-2 gap-1">
        {Object.entries(x.levels).map(([k, lv]) => (
          <div key={k} className={`flex items-center gap-1.5 ${k === hazard ? "font-medium" : ""}`} data-level-of={k} data-level={lv}><LevelDot level={lv} />{k[0].toUpperCase() + k.slice(1)}: {LEVEL[lv].name}</div>
        ))}
      </div>
      <div className="mt-2 text-muted">7-day max {num(x.values.tmax_7d_max as number, 1)} °C · min {num(x.values.tmin_7d_min as number, 1)} °C · rain {num(x.values.rain_7d as number, 1)} mm (wettest day {num(x.values.rain_max_day as number, 1)}) · gust {num(x.values.gust_max as number)} km/h</div>
      {x.terrain === "hills" && <div className="mt-2"><DataQualityNotice n={{ id: "elevation", title: "Mountain terrain", text: "This district is hill terrain (CORE). Its representative point may be much higher or lower than towns in the district, so conditions may vary within the district." }} compact /></div>}
      <DistrictEvents x={x} />
      <div className="mt-2 flex flex-wrap gap-2">
        <EvidenceButton onClick={onEvidence} label={`Evidence: ${hazard}`} />
        <button onClick={onState} className="rounded-md border border-line px-2 py-1 text-[12px] hover:border-accent">Open state table</button>
      </div>
    </div>
  );
}

/** WHAT and WHEN at the district's representative point: /api/v2/events (all 11 CORE risks, point assessment). */
function DistrictEvents({ x }: { x: V2District }) {
  const ev = useCore<V2Events>(`events:${x.lat},${x.lon},${x.district} (district point)`, () => v2.events({ lat: x.lat, lon: x.lon, name: `${x.district} (district point)` }));
  const openEvidence = useApp((s) => s.openEvidence);
  return (
    <div className="mt-2 border-t border-line pt-2" data-testid="district-events">
      <div className="text-[11px] font-semibold uppercase tracking-wide text-muted">At the representative point — what and when</div>
      <Load s={ev} lines={2}>
        {(d) => (
          <div className="mt-1 space-y-1.5">
            {d.official_alerts.length > 0 && (
              <div className="space-y-1.5" data-testid="district-official">{d.official_alerts.slice(0, 2).map((w) => <OfficialAlert key={w.id} w={w} compact />)}
                {d.official_alerts.length > 2 && <p className="text-[11.5px] text-red-200">+{d.official_alerts.length - 2} more official alerts</p>}</div>
            )}
            {d.events.length === 0 && <p className="text-muted">No system event at Watch or above at this point.</p>}
            {d.events.map((e) => (
              <div key={e.id} className="flex flex-wrap items-center gap-x-2" data-testid="district-event" data-event-type={e.type} data-level={e.severity.level}>
                <LevelDot level={e.severity.level} /><span className="font-medium">{e.title}</span><span className={LEVEL[e.severity.level].text}>{e.severity.status}</span>
                <span className="text-muted">{e.start ? `${fmtWhen(e.start)} → ${fmtWhen(e.end)}` : "timing not provided by CORE"}</span>
                <button className="text-accent" onClick={() => openEvidence({ point: { lat: x.lat, lon: x.lon, name: `${x.district} (district point)` }, risk: e.type, context: "Point assessment at the district's representative point." })}>evidence</button>
              </div>
            ))}
            <p className="text-[11px] text-muted">Point assessment; thunderstorm, fog, flood and other point-only risks appear here but are not in the district counts.</p>
          </div>
        )}
      </Load>
    </div>
  );
}

/** State focus: the same counted districts for one state, plus CORE's existing exports. */
function StateFocus({ d, slug, hazard, onPick }: { d: V2IndiaRisks; slug: string; hazard: string; onPick: (x: V2District) => void }) {
  const rows = d.districts.filter((x) => x.state_slug === slug);
  if (!rows.length) return null;
  const flagged = rows.filter((x) => Object.values(x.levels).some((l) => l >= 1) || x.official_alerts > 0)
    .sort((a, b) => b.max_level - a.max_level || b.official_alerts - a.official_alerts);
  const n = (h: string) => rows.filter((x) => x.levels[h] >= 1).length;
  return (
    <div className="rounded-xl border border-line p-3" data-testid="state-focus" data-state={slug}>
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="text-[14px] font-medium">{rows[0].state} — {rows.length} districts</h3>
        <div className="flex gap-2 text-[12px]">
          <a href={coreUrl(`/region/state/${slug}/export.xlsx`)} className="inline-flex items-center gap-1 rounded-md border border-line px-2 py-1 hover:border-accent"><Download size={13} /> Excel (CORE)</a>
          <a href={coreUrl(`/region/state/${slug}/report.html`)} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 rounded-md border border-line px-2 py-1 hover:border-accent"><FileText size={13} /> Briefing (CORE)</a>
        </div>
      </div>
      <p className="mt-1 text-[12.5px]" data-testid="state-counts">
        {d.hazards.map((h) => <span key={h.id} className="mr-3" data-hazard={h.id} data-count={n(h.id)}><b className="font-medium">{n(h.id)}</b> with system-assessed {h.title.toLowerCase()} risk</span>)}
        <span className="text-red-200"><b className="font-medium">{rows.filter((x) => x.official_alerts > 0).length}</b> named in official alerts</span>
      </p>
      {flagged.length ? (
        <div className="mt-2 overflow-x-auto">
          <table className="w-full min-w-[560px] text-[12.5px]" data-testid="state-focus-table">
            <thead className="text-left text-muted"><tr className="border-b border-line"><th className="py-1 font-normal">District</th>{d.hazards.map((h) => <th key={h.id} className="font-normal">{h.title}</th>)}<th className="font-normal text-red-200">Official alerts</th><th className="font-normal">Terrain</th></tr></thead>
            <tbody>{flagged.map((x) => (
              <tr key={x.id} className={`border-b border-line/60 ${x.levels[hazard] >= 1 ? "" : "text-muted"}`} data-district={x.id}>
                <td className="py-1"><button className="text-left hover:text-accent" onClick={() => onPick(x)}>{x.district}</button></td>
                {d.hazards.map((h) => <td key={h.id}><span className="inline-flex items-center gap-1"><LevelDot level={x.levels[h.id]} />{LEVEL[x.levels[h.id]].name}</span></td>)}
                <td className="text-red-200">{x.official_alerts || "—"}</td><td>{x.terrain}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      ) : <p className="mt-2 text-[12.5px] text-muted">No district in this state with system-assessed risk or an official alert.</p>}
      <p className="mt-1 text-[11px] text-muted">Levels at each district's representative point, next 7 days. Conditions may vary within a district. Click a district for timing and evidence.</p>
    </div>
  );
}
