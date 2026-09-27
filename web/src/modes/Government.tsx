import { useMemo, useState } from "react";
import { core, coreAsset } from "../core-api/client";
import type { CoreOfficialWarning, CoreRegionIndia } from "../core-api/types";
import { Load, Section } from "../components/ui";
import { istDateTime, num, runLabel } from "../lib/format";
import { SEVERITY } from "../lib/present";
import { navigate } from "../lib/router";
import { useApp } from "../lib/store";
import { useCore } from "../lib/useCore";
import { colorAt, cssGradient, METRIC_PALETTE } from "../map/palettes";
import WeatherMap from "../map/WeatherMap";

const METRICS = [
  { id: "rain", label: "Rainfall total" },
  { id: "tmax", label: "Max temperature" },
  { id: "tmin", label: "Min temperature" },
  { id: "gust", label: "Max wind" },
  { id: "rh", label: "Mean humidity" },
];
const HOURS = [24, 72, 120];

/** Government India view: CORE /region/india district statistics (existing metrics), hotspots, official alerts. */
export default function GovernmentIndia() {
  const { govState, setGovState } = useApp();
  const [metric, setMetric] = useState("rain");
  const [hours, setHours] = useState(72);
  const india = useCore<CoreRegionIndia>(`india:${metric}:${hours}`, () => core.regionIndia(metric, hours));
  const warnings = useCore<CoreOfficialWarning[]>("warnings", core.warnings);
  const districtsGeo = useCore<GeoJSON.FeatureCollection>("districts-geo", () => fetch(coreAsset("geo/india_districts.geojson")).then((r) => r.json()));

  const names = useMemo(() => {
    const m: Record<string, { district: string; state: string; slug: string }> = {};
    if (districtsGeo.state === "ok") for (const f of districtsGeo.data.features) {
      const p = f.properties as Record<string, string>;
      m[p.id] = { district: p.district, state: p.state, slug: p.state_slug };
    }
    return m;
  }, [districtsGeo]);

  const pal = METRIC_PALETTE[metric];
  const fill = useMemo(() => {
    if (india.state !== "ok") return null;
    const out: Record<string, string> = {};
    for (const [id, v] of Object.entries(india.data.values)) {
      if (v === null) continue;
      const c = colorAt(pal, v);
      if (c[3] > 0) out[id] = `rgb(${c[0] | 0},${c[1] | 0},${c[2] | 0})`;
    }
    return out;
  }, [india, pal]);

  const hot = india.state === "ok"
    ? Object.entries(india.data.values).filter(([, v]) => v !== null).sort((a, b) => (metric === "tmin" ? (a[1]! - b[1]!) : (b[1]! - a[1]!))).slice(0, 10)
    : [];
  const bySev = (s: string) => (warnings.state === "ok" ? warnings.data.filter((w) => w.severity === s).length : 0);

  return (
    <div className="space-y-6" data-testid="government">
      <Section title="India — district statistics from the forecast grid">
        <div className="mb-3 flex flex-wrap items-center gap-2 text-[12.5px]">
          <select value={metric} onChange={(e) => setMetric(e.target.value)} className="h-9 rounded-lg border border-line bg-surface px-2" aria-label="Metric">
            {METRICS.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}
          </select>
          <div className="flex rounded-lg border border-line p-0.5">
            {HOURS.map((h) => <button key={h} onClick={() => setHours(h)} className={`rounded-md px-2.5 py-1 ${hours === h ? "bg-text text-bg" : "text-muted"}`}>Next {h === 120 ? "5 days" : `${h} h`}</button>)}
          </div>
          {pal && <span className="flex items-center gap-2 text-muted"><span className="h-2 w-28 rounded-full" style={{ background: cssGradient(pal) }} />{pal.unit}</span>}
        </div>
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
          <WeatherMap className="h-[420px] w-full overflow-hidden rounded-xl border border-line lg:h-[520px]" districtFill={fill} highlightState={govState}
            onDistrictClick={(_, slug) => setGovState(slug)} />
          <div>
            <h3 className="text-[13px] font-medium">Top 10 districts {metric === "tmin" ? "(lowest)" : "(highest)"}</h3>
            <Load s={india} lines={8}>
              {(d) => (
                <>
                  <ol className="mt-2 divide-y divide-line text-[13px]" data-testid="hotspots">
                    {hot.map(([id, v], i) => (
                      <li key={id} className="flex items-baseline justify-between gap-3 py-1.5">
                        <button className="text-left hover:text-accent" onClick={() => names[id] && setGovState(names[id].slug)}>
                          <span className="text-muted">{i + 1}.</span> {names[id]?.district ?? id} <span className="text-muted">· {names[id]?.state}</span>
                        </button>
                        <span className="tabular-nums font-medium" data-district={id}>{num(v, 1)} {d.unit}</span>
                      </li>
                    ))}
                  </ol>
                  <p className="mt-2 text-[11.5px] leading-relaxed text-muted">
                    {d.label}, {d.aggregation}, {istDateTime(d.window[0])} → {istDateTime(d.window[1])}. {d.meta.source} · {d.meta.model} · run {runLabel(d.meta.issue_time)}.
                    District statistic from grid cells inside each district (0.25°); small districts have limited spatial detail.
                  </p>
                </>
              )}
            </Load>
          </div>
        </div>
        <p className="mt-2 text-[12px] text-muted">Click a district on the map to open its state below.</p>
      </Section>

      <Section title="Official alerts in India" right={<button onClick={() => navigate({ screen: "risks" })} className="text-accent">Open all alerts</button>}>
        <Load s={warnings} lines={2}>
          {(ws) => (
            <div className="flex flex-wrap gap-x-5 gap-y-1 text-[13px]" data-testid="gov-alert-counts">
              <span><b>{ws.length}</b> active</span>
              {["Extreme", "Severe", "Moderate", "Minor"].map((s) => <span key={s} className={SEVERITY[s].text}>{bySev(s)} {s}</span>)}
              <span className="text-muted">NDMA SACHET (IMD, CWC, SDMAs)</span>
            </div>
          )}
        </Load>
      </Section>
    </div>
  );
}
