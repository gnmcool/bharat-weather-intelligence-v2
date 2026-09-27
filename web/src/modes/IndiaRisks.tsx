import { ShieldAlert } from "lucide-react";
import { useMemo, useState } from "react";
import { EvidenceButton, LevelDot, Load, Section, SystemLabel } from "../components/ui";
import { istDateTime, num } from "../lib/format";
import { LEVEL } from "../lib/present";
import { useApp } from "../lib/store";
import { useCore } from "../lib/useCore";
import WeatherMap from "../map/WeatherMap";
import { v2 } from "../v2-api/client";
import type { V2District, V2IndiaRisks } from "../v2-api/types";

export const LEVEL_FILL = ["", "#fcd34d", "#fb923c", "#ef4444"]; // Watch, Alert, Severe (same scale as LEVEL dots)
export const OFFICIAL_OUTLINE = "#f87171";

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
  const { openEvidence, setGovState } = useApp();
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
            <div className="text-[22px] font-semibold tabular-nums leading-tight">{x.districts} <span className="text-[12.5px] font-normal text-muted">districts</span></div>
            <div className="mt-0.5 flex gap-2 text-[11.5px] tabular-nums">
              <span className={LEVEL[1].text}>{x.watch} watch</span><span className={LEVEL[2].text}>{x.alert} alert</span><span className={LEVEL[3].text}>{x.severe} severe</span>
            </div>
            <div className="text-[11px] text-muted">{x.states} states/UTs</div>
          </button>
        ))}
        {/* OFFICIAL — separate tile, separate colour, never summed with system counts */}
        <div className="rounded-lg border border-official/50 bg-official/[0.08] px-3 py-2" data-testid="official-count" data-count={d.official.districts_with_alerts}>
          <div className="inline-flex items-center gap-1 text-[11px] font-semibold uppercase text-red-200"><ShieldAlert size={12} /> Official alerts</div>
          <div className="text-[22px] font-semibold tabular-nums leading-tight">{d.official.districts_with_alerts} <span className="text-[12.5px] font-normal text-muted">districts</span></div>
          <div className="text-[11.5px] text-muted">{d.official.alerts} active alerts{d.official.alerts_without_district ? ` (${d.official.alerts_without_district} without a district)` : ""}</div>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
        <div>
          <WeatherMap className="h-[400px] w-full overflow-hidden rounded-xl border border-line lg:h-[500px]" districtFill={fill} districtOutline={outline}
            onDistrictClick={(id) => { const x = byId.get(id); if (x) setPicked(x); }} />
          <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11.5px] text-muted" data-testid="risk-map-legend" data-filled={Object.keys(fill).length}>
            <span className="text-text">{h.title}, next 7 days:</span>
            {[1, 2, 3].map((l) => <span key={l} className="inline-flex items-center gap-1"><span className="h-2.5 w-2.5 rounded-sm" style={{ background: LEVEL_FILL[l] }} />{LEVEL[l].name}</span>)}
            <span className="inline-flex items-center gap-1"><span className="h-2.5 w-3 rounded-sm border-2 border-dashed" style={{ borderColor: OFFICIAL_OUTLINE }} />Official alert (outline)</span>
            <span>{Object.keys(fill).length} districts coloured = count above</span>
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
                    <span>{st.state}</span>
                    <span className="tabular-nums"><b className="font-medium">{st.districts}</b> <span className="text-[11.5px] text-muted">({st.watch}/{st.alert}/{st.severe})</span></span>
                  </li>
                ))}
              </ol>
            ) : <p className="mt-1 text-[12.5px] text-muted">No district at Watch level or above.</p>}
            <p className="mt-1 text-[11px] text-muted">Districts at watch / alert / severe.</p>
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

      <div className="space-y-1 text-[12px] leading-relaxed text-muted">
        <p><span className="text-text">When:</span> {d.window}. CORE district tables generated {istDateTime(d.core_generated_at.oldest)} – {istDateTime(d.core_generated_at.newest)}. For the day of the peak, open a district.</p>
        <p><span className="text-text">How counted:</span> {d.method} {h.rule}</p>
        <p data-testid="coverage"><span className="text-text">Coverage:</span> {d.coverage.districts_received} of {d.coverage.districts_expected} districts
          {d.coverage.complete ? " (all states and UTs)." : ` — incomplete: ${d.coverage.states_failed.map((f) => f.state).join(", ")} failed at CORE and are not counted.`}</p>
        <p><span className="text-text">Not counted by district:</span> {d.not_counted.map((n) => n.title).join(", ")} — CORE evaluates these only at points (see each location's assessment).</p>
        <details><summary className="cursor-pointer underline decoration-dotted underline-offset-2">Limitations</summary>
          <ul className="mt-1 list-disc space-y-1 pl-5">{d.limitations.map((l) => <li key={l}>{l}</li>)}{d.not_counted.map((n) => <li key={n.id}>{n.title}: {n.reason}</li>)}</ul>
        </details>
        <p>{d.classification_label}. Official alerts are shown separately and are never added to system counts.</p>
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
      {x.official_alerts > 0 && <div className="mt-1 text-red-200">{x.official_alerts} official alert(s) — see Risks &amp; alerts</div>}
      <div className="mt-2 flex flex-wrap gap-2">
        <EvidenceButton onClick={onEvidence} label={`Evidence: ${hazard}`} />
        <button onClick={onState} className="rounded-md border border-line px-2 py-1 text-[12px] hover:border-accent">Open state table</button>
      </div>
    </div>
  );
}
