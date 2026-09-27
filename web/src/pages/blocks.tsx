// Home building blocks, all rendered from one CORE /dashboard response (no extra calls).
import { ArrowRight, CircleCheck } from "lucide-react";
import { useState } from "react";
import { EventCard } from "../components/EventCard";
import { v2 } from "../v2-api/client";
import type { V2Events } from "../v2-api/types";
import { core } from "../core-api/client";
import type { CoreDashboard } from "../core-api/types";
import { Load, OfficialAlert, Section, Stat, SystemLabel } from "../components/ui";
import { compass, istDateTime, istDay, istTime, num, signed, wmoText } from "../lib/format";
import { navigate } from "../lib/router";
import { useApp } from "../lib/store";
import { useCore } from "../lib/useCore";

export function useDashboard() {
  const place = useApp((s) => s.place);
  return useCore<CoreDashboard>(`dash:${place.lat},${place.lon},${place.name}`, () => core.dashboard(place.lat, place.lon, place.name, place.taluka));
}

const v = (d: CoreDashboard, k: string) => d.current.values[k]?.value ?? null;

export function CurrentWeather({ d }: { d: CoreDashboard }) {
  const place = useApp((s) => s.place);
  const loc = d.location;
  const point = place.via === "gps" || place.via === "map" || !!loc.taluka || place.via === "search";
  return (
    <div data-testid="current">
      <div className="text-[12.5px] text-muted">
        {[loc.district, loc.state].filter(Boolean).join(", ")}
        {loc.elevation_m !== null && <> · {num(loc.elevation_m)} m</>} · {d.current.terrain}
      </div>
      <div className="mt-1 flex items-end gap-4">
        <div className="text-[56px] font-light leading-none tabular-nums tracking-tight" data-testid="cur-temp">{num(v(d, "temperature_2m"), 1)}°</div>
        <div className="pb-1.5">
          <div className="text-[16px] font-medium">{wmoText(v(d, "weather_code"))}</div>
          <div className="text-[13px] text-muted">Feels like <span data-testid="cur-feels">{num(v(d, "apparent_temperature"), 1)}</span>°C</div>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-3 gap-x-4 gap-y-3 sm:grid-cols-6">
        <Stat label="Rain now" value={<><span data-testid="cur-rain">{num(v(d, "precipitation"), 1)}</span> mm</>} />
        <Stat label="Humidity" value={<><span data-testid="cur-rh">{num(v(d, "relative_humidity_2m"))}</span>%</>} />
        <Stat label="Wind" value={<><span data-testid="cur-wind">{num(v(d, "wind_speed_10m"))}</span> km/h</>} sub={`${compass(v(d, "wind_direction_10m"))} · gusts ${num(v(d, "wind_gusts_10m"))}`} />
        <Stat label="Pressure" value={<><span data-testid="cur-msl">{num(v(d, "pressure_msl"))}</span> hPa</>} />
        <Stat label="Cloud" value={`${num(v(d, "cloud_cover"))}%`} />
        <Stat label="Visibility" value={d.current.visibility_m !== null ? `${num(d.current.visibility_m / 1000, 1)} km` : "—"} />
      </div>
      <p className="mt-3 text-[11.5px] text-muted">
        As of {istTime(d.current.time)} IST · {d.current.source}
        {point && <> · point forecast at model-grid resolution</>}
      </p>
    </div>
  );
}

/**
 * "What should you know?" from /api/v2/events (M2). Order: 1 official alerts, 2 severe, 3 alert-level,
 * 4 watch-level system assessments, 5 significant departures from normal. Every line is a CORE record;
 * no generated text. If nothing significant: "No significant weather event detected."
 */
export function WhatToKnow({ limit = 3 }: { d?: CoreDashboard; limit?: number }) {
  const place = useApp((s) => s.place);
  const ev = useCore<V2Events>(`events:${place.lat},${place.lon},${place.name}`, () => v2.events(place));
  return (
    <div data-testid="what-to-know">
      <Load s={ev} lines={3}>{(d) => <WhatToKnowBody d={d} limit={limit} />}</Load>
      {ev.state === "error" && <p className="mt-2 text-[12px] text-muted">The V2 event service is unavailable. CORE's own risk list is still under Risks &amp; alerts.</p>}
    </div>
  );
}

function WhatToKnowBody({ d, limit }: { d: V2Events; limit: number }) {
  const [more, setMore] = useState(false);
  const byId = new Map(d.events.map((e) => [e.id, e]));
  const official = d.official_alerts;
  const officialEvents = d.what_to_know.items.filter((i) => i.kind === "official_event").map((i) => byId.get(i.ref)!).filter(Boolean);
  const system = d.what_to_know.items.filter((i) => i.kind === "event").map((i) => byId.get(i.ref)!).filter(Boolean);
  const anomalies = d.anomalies;
  const n = more ? 99 : limit;
  return (
    <div className="space-y-3">
      {d.what_to_know.message && (
        <div className="flex items-start gap-2.5 rounded-lg border border-line bg-surface px-3 py-3 text-[14px]" data-testid="wtk-none">
          <CircleCheck size={18} className="mt-0.5 shrink-0 text-emerald-400" />
          <div>
            <div className="font-medium">{d.what_to_know.message}</div>
            <div className="mt-1 text-[12px] text-muted">No official alert for this location and no CORE risk at Watch level or above in the next 7 days.</div>
          </div>
        </div>
      )}
      {(official.length > 0 || officialEvents.length > 0) && (
        <div className="space-y-2" data-testid="wtk-official">
          <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-red-200">Official alert</div>
          {official.slice(0, n).map((w) => <OfficialAlert key={w.id} w={w} compact />)}
          {officialEvents.map((e) => <EventCard key={e.id} e={e} />)}
          {official.length > n && <button onClick={() => navigate({ screen: "risks" })} className="text-[12.5px] text-accent">+{official.length - n} more official alerts</button>}
        </div>
      )}
      {system.length > 0 && (
        <div className="space-y-2" data-testid="wtk-system">
          <div className="flex items-center gap-2"><SystemLabel /><span className="text-[12px] text-muted">CORE risk rules · next 7 days · not official warnings</span></div>
          {system.slice(0, n).map((e) => <EventCard key={e.id} e={e} />)}
          {system.length > n && <button onClick={() => setMore(true)} className="text-[12.5px] text-accent">Show {system.length - n} more system assessments</button>}
        </div>
      )}
      {anomalies.length > 0 && (
        <div className="space-y-1" data-testid="wtk-anomalies">
          <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-muted">Departure from normal <span className="font-normal normal-case tracking-normal">· not a hazard on its own</span></div>
          {anomalies.slice(0, more ? 99 : 2).map((a) => (
            <p key={a.id} className="text-[13px]" data-testid="wtk-anomaly" data-id={a.id}>
              <span className="text-muted">{a.label} ({a.period}):</span> forecast {num(a.value, 1)} {a.unit}, normal {num(a.normal, 1)} {a.unit} → <b className="font-medium">{signed(a.departure)} {a.unit}</b>{a.category ? ` · ${a.category}` : ""}
            </p>
          ))}
          <p className="text-[11px] text-muted">Normal: NASA POWER 1991–2020 (MERRA-2 reanalysis), indicative — not IMD normals.</p>
        </div>
      )}
    </div>
  );
}

/** Now / +6 h / +12 h / +18 h / +24 h / +48 h from CORE's hourly series, then 3 days. */
export function ForecastPreview({ d }: { d: CoreDashboard }) {
  const h = d.hourly;
  const times = h.time as string[];
  const t = h.temperature_2m as (number | null)[];
  const pp = h.precipitation_probability as (number | null)[];
  const pr = h.precipitation as (number | null)[];
  const ws = h.wind_speed_10m as (number | null)[];
  const code = h.weather_code as (number | null)[];
  const nowIst = new Date().toLocaleString("sv-SE", { timeZone: "Asia/Kolkata" }).slice(0, 13); // "YYYY-MM-DD HH"
  const i0 = Math.max(0, times.findIndex((x) => x.replace("T", " ").slice(0, 13) === nowIst));
  const steps = [0, 6, 12, 18, 24, 47].map((o) => i0 + o).filter((i) => i < times.length);
  return (
    <div>
      <div className="-mx-1 flex overflow-x-auto pb-1" data-testid="hourly-strip">
        {steps.map((i, k) => (
          <div key={i} className="min-w-[104px] flex-1 border-l border-line px-2 first:border-l-0">
            <div className="text-[11.5px] text-muted">{k === 0 ? "Now" : `+${i - i0} h`} · {istTime(times[i], { hour: "numeric" })}</div>
            <div className="text-[18px] font-medium tabular-nums">{num(t[i])}°</div>
            <div className="text-[11.5px] text-muted">{wmoText(code[i])}</div>
            <div className="text-[11.5px] text-muted">Rain {num(pr[i], 1)} mm</div>
            <div className="text-[11.5px] text-muted">Chance {num(pp[i])}%</div>
            <div className="text-[11.5px] text-muted">Wind {num(ws[i])} km/h</div>
          </div>
        ))}
      </div>
      <div className="mt-3 divide-y divide-line rounded-lg border border-line">
        {d.daily.slice(0, 3).map((r) => (
          <div key={r.date} className="flex items-center gap-3 px-3 py-2 text-[13px]">
            <div className="w-24 shrink-0">{istDay(r.date, { weekday: "short", day: "numeric", month: "short" })}</div>
            <div className="flex-1 text-muted">{wmoText(r.weather_code)}</div>
            <div className="w-20 text-right tabular-nums">{num(r.temperature_2m_max)}° / {num(r.temperature_2m_min)}°</div>
            <div className="w-24 text-right tabular-nums text-muted">{num(r.precipitation_sum, 1)} mm · {num(r.precipitation_probability_max)}%</div>
          </div>
        ))}
      </div>
      <button onClick={() => navigate({ screen: "forecast" })} className="mt-2 inline-flex items-center gap-1 text-[12.5px] text-accent">48-hour and 10-day forecast <ArrowRight size={13} /></button>
    </div>
  );
}

export function RiskSummary({ d }: { d: CoreDashboard }) {
  const counts = [0, 1, 2, 3].map((lv) => d.risks.filter((r) => r.level === lv).length);
  return (
    <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-[13px]" data-testid="risk-summary">
      <span><b className="font-semibold">{d.warnings.length}</b> official alerts for this location</span>
      <span className="text-muted">System assessments (11):</span>
      {["No risk", "Watch", "Alert", "Severe"].map((n, i) => (
        <span key={n} className="inline-flex items-center gap-1.5"><span className={`h-2 w-2 rounded-full ${["bg-emerald-400", "bg-amber-300", "bg-orange-400", "bg-red-500"][i]}`} />{counts[i]} {n}</span>
      ))}
      <button onClick={() => navigate({ screen: "risks" })} className="inline-flex items-center gap-1 text-accent">All risks and alerts <ArrowRight size={13} /></button>
    </div>
  );
}

export function InsightsPreview({ d }: { d: CoreDashboard }) {
  const items = d.anomaly?.items ?? [];
  if (!d.anomaly) return <p className="text-[13px] text-muted">Weather-vs-normal is unavailable for this location (CORE returned no baseline).</p>;
  return (
    <div>
      <div className="grid gap-3 sm:grid-cols-2">
        {items.slice(0, 2).map((a) => (
          <div key={a.id} className="text-[13px]">
            <div className="text-muted">{a.label} · {a.period}</div>
            <div className="text-[16px] font-medium tabular-nums">{num(a.value, 1)} {a.unit} <span className="text-[13px] text-muted">normal {num(a.normal, 1)} · {signed(a.departure)}{a.unit === "%" ? "" : ` ${a.unit}`}</span></div>
            {a.category && <div className="text-[12px] text-muted">{a.category}</div>}
          </div>
        ))}
      </div>
      <p className="mt-2 text-[11.5px] text-muted">Normal: {d.anomaly.baseline.source} ({d.anomaly.baseline.model}) — indicative for rainfall; IMD gridded normals are planned.</p>
      <button onClick={() => navigate({ screen: "insights" })} className="mt-1 inline-flex items-center gap-1 text-[12.5px] text-accent">All insights <ArrowRight size={13} /></button>
    </div>
  );
}

export function RunLine({ d }: { d: CoreDashboard }) {
  const perModel = d.sources.find((s) => s.issue_time);
  return (
    <p className="text-[11.5px] text-muted" data-testid="run-line">
      Generated by CORE {istDateTime(d.generated_at)}{perModel?.notes ? ` · ${perModel.notes}` : ""}
    </p>
  );
}

export { Load, Section };
