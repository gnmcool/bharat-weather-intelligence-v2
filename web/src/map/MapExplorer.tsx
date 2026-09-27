import { Flame, Layers, ShieldAlert, TriangleAlert, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { core } from "../core-api/client";
import type { CoreEoLayer, CoreFires, CoreGridField, CoreGridMeta, CoreOfficialWarning } from "../core-api/types";
import { istDateTime, num, runLabel } from "../lib/format";
import { SEVERITY } from "../lib/present";
import { useApp } from "../lib/store";
import { cached, useCore } from "../lib/useCore";
import { EvidenceButton, LevelDot } from "../components/ui";
import { LEVEL } from "../lib/present";
import { hazardFill, LEVEL_FILL, OFFICIAL_OUTLINE, openDistrictEvidence } from "../modes/IndiaRisks";
import { v2 } from "../v2-api/client";
import type { V2District, V2IndiaRisks } from "../v2-api/types";
import { sample } from "./field";
import { cssGradient, PALETTES } from "./palettes";
import WeatherMap from "./WeatherMap";

const ORDER = ["tp", "t2m", "wind", "fg10m", "tcc", "r2m", "msl", "tcwv"];
const JUMPS: [string, number][] = [["Now", 0], ["+6 h", 6], ["+12 h", 12], ["+24 h", 24], ["+48 h", 48], ["+3 d", 72], ["+5 d", 120], ["+7 d", 168]];
const SEV_FILL: Record<string, string> = { Extreme: "#dc2626", Severe: "#f97316", Moderate: "#facc15", Minor: "#38bdf8" };

export default function MapExplorer({ compact = false, className = "" }: { compact?: boolean; className?: string }) {
  const { place, setPlace, openEvidence } = useApp();
  const meta = useCore<CoreGridMeta>("grid-meta", core.gridMeta);
  const [layer, setLayer] = useState("tp");
  const [ti, setTi] = useState<number | null>(null);
  const [field, setField] = useState<CoreGridField | null>(null);
  const [fieldErr, setFieldErr] = useState<string | null>(null);
  const [alertsOn, setAlertsOn] = useState(!compact);
  const [eoId, setEoId] = useState<string | null>(null);
  const [firesOn, setFiresOn] = useState(false);
  const [panel, setPanel] = useState(false);
  const [point, setPoint] = useState<{ lat: number; lon: number } | null>(null);
  // M2 system-risk layer (districts) from /api/v2/region/india/risks
  const [riskHazard, setRiskHazard] = useState<string | null>(null);
  const [riskPick, setRiskPick] = useState<V2District | null>(null);
  const risks = useCore<V2IndiaRisks>(riskHazard ? "v2:india-risks" : null, v2.indiaRisks);
  const warnings = useCore<CoreOfficialWarning[]>(alertsOn ? "warnings" : null, core.warnings);
  const eoLayers = useCore<CoreEoLayer[]>(eoId ? "eo-layers" : null, core.earthobsLayers);
  const fires = useCore<CoreFires>(firesOn ? "fires" : null, core.fires);

  const times = meta.state === "ok" ? meta.data.times : [];
  const nowIdx = useMemo(() => {
    if (!times.length) return 0;
    const now = Date.now();
    let best = 0;
    times.forEach((t, i) => { if (Math.abs(Date.parse(t) - now) < Math.abs(Date.parse(times[best]) - now)) best = i; });
    return best;
  }, [times]);
  const idx = ti ?? nowIdx;

  useEffect(() => {
    if (!times.length) return;
    let live = true;
    setFieldErr(null);
    cached(`field:${layer}:${times[idx]}`, () => core.gridField(layer, times[idx]))
      .then((f) => live && setField(f))
      .catch((e) => live && setFieldErr(String(e.message ?? e)));
    return () => { live = false; };
  }, [layer, idx, times]);

  const jump = (h: number) => {
    const target = Date.parse(times[nowIdx]) + h * 3600e3;
    let best = nowIdx;
    times.forEach((t, i) => { if (Math.abs(Date.parse(t) - target) < Math.abs(Date.parse(times[best]) - target)) best = i; });
    setTi(best);
  };

  const alertFill = useMemo(() => {
    if (!alertsOn || warnings.state !== "ok") return null;
    const rank: Record<string, number> = { Extreme: 4, Severe: 3, Moderate: 2, Minor: 1 };
    const best: Record<string, string> = {};
    const r: Record<string, number> = {};
    for (const w of warnings.data) for (const id of w.district_ids) {
      const k = rank[w.severity ?? ""] ?? 0;
      if (!(id in r) || k > r[id]) { r[id] = k; best[id] = SEV_FILL[w.severity ?? ""] ?? "#94a3b8"; }
    }
    return best;
  }, [alertsOn, warnings]);

  const riskFill = useMemo(() => (riskHazard && risks.state === "ok" ? hazardFill(risks.data, riskHazard) : null), [riskHazard, risks]);
  const riskById = useMemo(() => (risks.state === "ok" ? new Map(risks.data.districts.map((x) => [x.id, x])) : null), [risks]);
  // Official alerts become an outline when the system fill is on, so official and system are never merged.
  const officialAsOutline = useMemo(() => {
    if (!riskFill || !alertFill) return null;
    return Object.fromEntries(Object.keys(alertFill).map((id) => [id, OFFICIAL_OUTLINE]));
  }, [riskFill, alertFill]);

  const pal = PALETTES[layer];
  const eo = eoId && eoLayers.state === "ok" ? eoLayers.data.find((l) => l.id === eoId) ?? null : null;
  const pointVal = point && field ? sample(field, point.lat, point.lon) : null;
  const vars = meta.state === "ok" ? ORDER.filter((v) => meta.data.variables[v] && PALETTES[v]) : [];

  return (
    <div className={`relative overflow-hidden rounded-xl border border-line ${className}`}>
      <WeatherMap className="h-full w-full" field={field && pal ? { data: field, palette: pal } : null} fieldOpacity={eo ? 0.35 : riskFill ? 0.25 : 0.72}
        districtFill={riskFill ?? alertFill} districtOutline={officialAsOutline} eo={eo} fires={firesOn && fires.state === "ok" ? (fires.data as unknown as GeoJSON.FeatureCollection) : null}
        marker={point ?? { lat: place.lat, lon: place.lon }} onClick={(lat, lon) => { setRiskPick(null); setPoint({ lat, lon }); }} interactive
        onDistrictClick={riskFill ? (id, _s, _n, lat, lon) => {
          const x = riskById?.get(id);
          if (x && riskHazard && (riskHazard === "any" ? x.max_level : x.levels[riskHazard]) >= 1) { setPoint(null); setRiskPick(x); }
          else { setRiskPick(null); setPoint({ lat, lon }); }
        } : undefined} />

      {/* layer + timeline controls */}
      <div className="pointer-events-none absolute inset-x-2 bottom-2 flex flex-col gap-2 sm:inset-x-3 sm:bottom-3">
        {riskPick && riskHazard && (
          <div className="pointer-events-auto self-start rounded-lg border border-line bg-surface/95 p-3 text-[12.5px] shadow-xl" data-testid="map-risk-card" data-district={riskPick.id}>
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-[10.5px] font-semibold uppercase tracking-wide text-slate-300">System assessment · district</div>
                <div className="font-medium">{riskPick.district}, {riskPick.state}</div>
                <div className="mt-1 grid grid-cols-2 gap-x-3">
                  {Object.entries(riskPick.levels).map(([k, lv]) => <span key={k} className="inline-flex items-center gap-1.5"><LevelDot level={lv} />{k}: {LEVEL[lv].name}</span>)}
                </div>
                <div className="text-muted">When: next 7 days (open evidence for the dates) · representative point</div>
              </div>
              <button onClick={() => setRiskPick(null)} aria-label="Close"><X size={15} className="text-muted" /></button>
            </div>
            <div className="mt-2 flex flex-wrap gap-2">
              {Object.entries(riskPick.levels).filter(([, lv]) => lv >= 1).map(([k]) => (
                <EvidenceButton key={k} label={`Evidence: ${k}`} onClick={() => openDistrictEvidence(openEvidence, riskPick, k)} />
              ))}
            </div>
          </div>
        )}
        {point && (
          <div className="pointer-events-auto self-start rounded-lg border border-line bg-surface/95 p-3 text-[12.5px] shadow-xl" data-testid="point-card">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="font-medium">{point.lat.toFixed(3)}°N {point.lon.toFixed(3)}°E</div>
                <div className="text-[17px] font-medium tabular-nums">{pal ? `${num(pointVal, 1)} ${pal.unit}` : "—"} <span className="text-[12px] font-normal text-muted">{pal?.label}</span></div>
                <div className="text-muted">{istDateTime(times[idx])} · grid value (~27 km), not a measurement</div>
              </div>
              <button onClick={() => setPoint(null)} aria-label="Close"><X size={15} className="text-muted" /></button>
            </div>
            <button onClick={() => { setPlace({ name: `${point.lat.toFixed(3)}, ${point.lon.toFixed(3)}`, lat: +point.lat.toFixed(4), lon: +point.lon.toFixed(4), via: "map" }); setPoint(null); }}
              className="mt-2 rounded-md bg-accent px-2.5 py-1.5 text-[12.5px] font-medium text-white">Use this point as my location</button>
          </div>
        )}
        <div className="pointer-events-auto rounded-xl border border-line bg-surface/95 p-2 shadow-xl backdrop-blur">
          <div className="flex items-center gap-2">
            <button onClick={() => setPanel(!panel)} aria-expanded={panel} className={`flex h-9 shrink-0 items-center gap-1.5 rounded-lg px-2.5 text-[13px] ${panel ? "bg-accent text-white" : "bg-surface-2"}`}>
              <Layers size={15} /> <span className="hidden sm:inline">{pal?.label ?? "Layers"}</span>
            </button>
            <div className="flex min-w-0 flex-1 gap-1 overflow-x-auto" role="group" aria-label="Forecast time">
              {JUMPS.map(([lbl, h]) => {
                const target = times.length ? Date.parse(times[nowIdx]) + h * 3600e3 : 0;
                const on = times.length > 0 && Math.abs(Date.parse(times[idx]) - target) < 1.6 * 3600e3;
                return (
                  <button key={lbl} onClick={() => jump(h)} disabled={!times.length}
                    className={`h-9 shrink-0 rounded-lg px-2.5 text-[12.5px] tabular-nums ${on ? "bg-text text-bg" : "text-muted hover:text-text"}`}>{lbl}</button>
                );
              })}
            </div>
          </div>
          {!compact && times.length > 0 && (
            <input type="range" min={0} max={times.length - 1} value={idx} onChange={(e) => setTi(+e.target.value)} className="mt-2 w-full accent-accent" aria-label="Forecast time step" />
          )}
          <div className="mt-1 flex flex-wrap items-center justify-between gap-x-3 gap-y-1 px-1 text-[11.5px] text-muted">
            <span className="font-medium text-text" data-testid="map-time">{times.length ? istDateTime(times[idx]) : "Loading forecast times…"}</span>
            {pal && (
              <span className="flex items-center gap-2">
                <span className="h-2 w-28 rounded-full" style={{ background: cssGradient(pal) }} />
                {pal.ticks[0]}–{pal.ticks[pal.ticks.length - 1]} {pal.unit}
              </span>
            )}
            {meta.state === "ok" && <span data-testid="map-source">{meta.data.source} · {meta.data.model} · run {runLabel(meta.data.issue_time)}</span>}
            {fieldErr && <span className="text-red-300">Field unavailable: {fieldErr}</span>}
          </div>
        </div>
      </div>

      {panel && (
        <div className="absolute right-2 top-2 z-10 max-h-[calc(100%-120px)] w-[min(300px,calc(100%-16px))] overflow-y-auto rounded-xl border border-line bg-surface/95 p-3 text-[13px] shadow-xl backdrop-blur sm:right-3 sm:top-3">
          <div className="mb-2 flex items-center justify-between"><span className="font-semibold">Map layers</span><button onClick={() => setPanel(false)} aria-label="Close layers"><X size={15} /></button></div>
          <div className="text-[11.5px] uppercase tracking-wide text-muted">Forecast (Earth2Studio GFS)</div>
          <div className="mt-1 grid grid-cols-2 gap-1">
            {vars.map((v) => (
              <button key={v} onClick={() => setLayer(v)} className={`rounded-md px-2 py-1.5 text-left ${layer === v ? "bg-accent text-white" : "bg-surface-2 hover:bg-line"}`}>{PALETTES[v].label}</button>
            ))}
          </div>
          <div className="mt-3 text-[11.5px] uppercase tracking-wide text-muted">System risk by district (next 7 days)</div>
          <div className="mt-1 grid grid-cols-3 gap-1" data-testid="risk-layer">
            {[["none", "Off"], ["any", "Any"], ["rain", "Heavy rain"], ["heat", "Heat"], ["cold", "Cold"], ["wind", "Wind"]].map(([id, lbl]) => (
              <button key={id} onClick={() => { setRiskHazard(id === "none" ? null : id); setRiskPick(null); }} data-hazard={id}
                className={`rounded-md px-2 py-1.5 text-left ${(riskHazard ?? "none") === id ? "bg-accent text-white" : "bg-surface-2 hover:bg-line"}`}>{lbl}</button>
            ))}
          </div>
          {riskHazard && (
            <div className="mt-1 text-[11px] text-muted">
              <div className="flex flex-wrap gap-x-3">{[1, 2, 3].map((l) => <span key={l} className="inline-flex items-center gap-1"><span className="h-2 w-2 rounded-sm" style={{ background: LEVEL_FILL[l] }} />{LEVEL[l].name}</span>)}</div>
              {risks.state === "loading" && <p>Loading district counts (up to a minute on first use)…</p>}
              {risks.state === "error" && <p className="text-red-300">Unavailable: {risks.message}</p>}
              {risks.state === "ok" && <p data-testid="risk-layer-count" data-count={Object.keys(riskFill ?? {}).length}><TriangleAlert size={11} className="inline" /> {Object.keys(riskFill ?? {}).length} districts at Watch or above. CORE level at each district's representative point; official alerts shown as dashed outline. Click a coloured district for evidence.</p>}
            </div>
          )}
          <div className="mt-3 text-[11.5px] uppercase tracking-wide text-muted">Official</div>
          <label className="mt-1 flex items-center gap-2"><input type="checkbox" checked={alertsOn} onChange={(e) => setAlertsOn(e.target.checked)} />
            <ShieldAlert size={14} className="text-official" /> Districts with official alerts
          </label>
          {alertsOn && riskFill && <p className="ml-6 mt-1 text-[11px] text-muted">Shown as a dashed red outline while the system-risk layer is on, so official and system are never merged.</p>}
          {alertsOn && !riskFill && (
            <div className="ml-6 mt-1 flex flex-wrap gap-x-3 text-[11px] text-muted">
              {Object.entries(SEV_FILL).map(([k, c]) => <span key={k} className="inline-flex items-center gap-1"><span className="h-2 w-2 rounded-sm" style={{ background: c }} /><span className={SEVERITY[k]?.text}>{k}</span></span>)}
            </div>
          )}
          <div className="mt-3 text-[11.5px] uppercase tracking-wide text-muted">Satellite imagery (NASA)</div>
          <p className="text-[11.5px] text-muted">Imagery available for viewing; not used as quantitative evidence.</p>
          <div className="mt-1 space-y-1">
            {["rain_now", "flood", "soil", "ndvi", "truecolor"].map((id) => (
              <label key={id} className="flex items-center gap-2"><input type="radio" name="eo" checked={eoId === id} onChange={() => setEoId(id)} />
                {({ rain_now: "Rain now (IMERG)", flood: "Flood water (VIIRS)", soil: "Soil moisture (SMAP)", ndvi: "Vegetation (NDVI)", truecolor: "True colour (daily)" } as Record<string, string>)[id]}
              </label>
            ))}
            <label className="flex items-center gap-2"><input type="radio" name="eo" checked={eoId === null} onChange={() => setEoId(null)} /> None</label>
          </div>
          {eo && <p className="mt-1 text-[11.5px] text-muted">{eo.desc} Image time: {eo.time}.</p>}
          <label className="mt-2 flex items-center gap-2"><input type="checkbox" checked={firesOn} onChange={(e) => setFiresOn(e.target.checked)} /><Flame size={14} className="text-orange-400" /> Active fires (FIRMS, 24 h)</label>
          {firesOn && fires.state === "ok" && <p className="ml-6 text-[11.5px] text-muted">{fires.data.meta.count} detections · {fires.data.meta.source}. Heat detections, not confirmed fires.</p>}
          {meta.state === "ok" && <p className="mt-3 text-[11px] text-muted">{meta.data.resolution_note}</p>}
        </div>
      )}
    </div>
  );
}
