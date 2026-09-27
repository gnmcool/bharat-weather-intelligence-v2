import { CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { CoreDashboard } from "../core-api/types";
import { Provenance } from "../components/ui";
import { istDay, num, signed } from "../lib/format";
import type { Mode } from "../lib/store";
import GovernmentStateTable from "../modes/GovernmentStateTable";
import { Load, Section, useDashboard } from "./blocks";

export default function InsightsPage({ mode }: { mode: Mode }) {
  const dash = useDashboard();
  if (mode === "government") return <GovernmentStateTable title="Rainfall and temperature vs normal by district" focus="normal" />;
  return <Load s={dash} lines={6}>{(d) => <Body d={d} />}</Load>;
}

function Body({ d }: { d: CoreDashboard }) {
  const a = d.anomaly;
  if (!a) return <p className="text-[13.5px] text-muted">CORE returned no weather-vs-normal baseline for this location.</p>;
  const chart = d.daily.map((r) => ({ date: istDay(r.date, { day: "numeric", month: "short" }), tmax: r.temperature_2m_max, nmax: r.normal_tmax, tmin: r.temperature_2m_min, nmin: r.normal_tmin }));
  return (
    <div className="space-y-6">
      <Section title={`Weather vs normal — ${d.location.name}`}>
        <div className="divide-y divide-line" data-testid="anomaly-list">
          {a.items.map((it) => (
            <div key={it.id} className="grid grid-cols-[1fr_auto] items-baseline gap-x-4 py-2.5 sm:grid-cols-[220px_1fr_auto]" data-testid="anomaly-item" data-id={it.id}>
              <div className="text-[13px] text-muted">{it.label}<span className="block text-[11.5px]">{it.period}</span></div>
              <div className="text-[15px] tabular-nums">
                <span className="font-medium">{num(it.value, 1)} {it.unit}</span>
                <span className="text-muted"> vs normal {num(it.normal, 1)} {it.unit}</span>
              </div>
              <div className="col-span-2 text-[13px] tabular-nums sm:col-span-1 sm:text-right">
                <span className="font-medium">{signed(it.departure)} {it.unit}</span>
                {it.departure_pct !== null && <span className="text-muted"> ({signed(it.departure_pct, 0)}%)</span>}
                {it.category && <span className="ml-2 rounded bg-surface-2 px-1.5 py-0.5 text-[11.5px]">{it.category}</span>}
              </div>
            </div>
          ))}
          {a.dry_spell_days !== null && (
            <div className="py-2.5 text-[13px]"><span className="text-muted">Dry spell: </span><span className="font-medium">{a.dry_spell_days} days</span>{a.dry_spell_note && <span className="text-muted"> — {a.dry_spell_note}</span>}</div>
          )}
        </div>
      </Section>
      <Section title="Daily temperature vs normal (10 days)">
        <div className="h-56 w-full">
          <ResponsiveContainer>
            <ComposedChart data={chart} margin={{ top: 8, right: 8, bottom: 0, left: -18 }}>
              <CartesianGrid stroke="#253041" vertical={false} />
              <XAxis dataKey="date" tick={{ fill: "#93a1b3", fontSize: 11 }} tickLine={false} axisLine={{ stroke: "#253041" }} />
              <YAxis tick={{ fill: "#93a1b3", fontSize: 11 }} unit="°" domain={["dataMin - 2", "dataMax + 2"]} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ background: "#121923", border: "1px solid #253041", borderRadius: 8, fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line dataKey="tmax" name="Forecast max" stroke="#f59e0b" strokeWidth={2} dot={false} />
              <Line dataKey="nmax" name="Normal max" stroke="#f59e0b" strokeDasharray="4 3" dot={false} />
              <Line dataKey="tmin" name="Forecast min" stroke="#38bdf8" strokeWidth={2} dot={false} />
              <Line dataKey="nmin" name="Normal min" stroke="#38bdf8" strokeDasharray="4 3" dot={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </Section>
      <Section title="About the normal">
        <p className="max-w-3xl text-[12.5px] leading-relaxed text-muted">
          {a.method} Baseline: {a.baseline.source} — {a.baseline.model}. {a.baseline.notes} For rainfall this reanalysis baseline is indicative only; IMD 1991–2020 gridded rainfall normals are planned for a later milestone.
        </p>
        <div className="mt-2"><Provenance sources={[a.baseline, ...d.sources]} /></div>
      </Section>
    </div>
  );
}
