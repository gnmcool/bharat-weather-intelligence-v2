import { Bar, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { CoreDashboard } from "../core-api/types";
import { Provenance } from "../components/ui";
import { compass, istDay, istTime, MODEL_NAME, num, wmoText } from "../lib/format";
import type { Mode } from "../lib/store";
import GovernmentStateTable from "../modes/GovernmentStateTable";
import { Load, RunLine, Section, useDashboard } from "./blocks";

export default function ForecastPage({ mode }: { mode: Mode }) {
  const dash = useDashboard();
  if (mode === "government") return <GovernmentStateTable title="District forecast table (next 7 days)" />;
  return (
    <Load s={dash} lines={8}>
      {(d) => (
        <div className="space-y-6">
          <Section title="Next 48 hours" right={<span>Hourly · IST</span>}><Hourly d={d} /></Section>
          <Section title="10-day outlook" right={<span>Model range: ECMWF · GFS · ICON</span>}><TenDay d={d} /></Section>
          <div className="space-y-2 border-t border-line pt-4"><RunLine d={d} /><Provenance sources={d.sources} /></div>
        </div>
      )}
    </Load>
  );
}

function Hourly({ d }: { d: CoreDashboard }) {
  const h = d.hourly;
  const t = h.time as string[];
  const rows = t.map((time, i) => ({
    time,
    label: istTime(time, { hour: "numeric" }),
    temp: (h.temperature_2m as (number | null)[])[i],
    feels: (h.apparent_temperature as (number | null)[])[i],
    rain: (h.precipitation as (number | null)[])[i],
    pop: (h.precipitation_probability as (number | null)[])[i],
    wind: (h.wind_speed_10m as (number | null)[])[i],
    gust: (h.wind_gusts_10m as (number | null)[])[i],
    rh: (h.relative_humidity_2m as (number | null)[])[i],
    dir: (h.wind_direction_10m as (number | null)[])[i],
    code: (h.weather_code as (number | null)[])[i],
  }));
  return (
    <div>
      <div className="h-64 w-full" data-testid="hourly-chart">
        <ResponsiveContainer>
          <ComposedChart data={rows} margin={{ top: 8, right: 8, bottom: 0, left: -18 }}>
            <CartesianGrid stroke="#253041" vertical={false} />
            <XAxis dataKey="label" tick={{ fill: "#93a1b3", fontSize: 11 }} interval={5} tickLine={false} axisLine={{ stroke: "#253041" }} />
            <YAxis yAxisId="t" tick={{ fill: "#93a1b3", fontSize: 11 }} unit="°" domain={["dataMin - 2", "dataMax + 2"]} tickLine={false} axisLine={false} />
            <YAxis yAxisId="r" orientation="right" tick={{ fill: "#93a1b3", fontSize: 11 }} unit=" mm" tickLine={false} axisLine={false} allowDecimals />
            <Tooltip contentStyle={{ background: "#121923", border: "1px solid #253041", borderRadius: 8, fontSize: 12 }} labelStyle={{ color: "#e6ebf2" }}
              labelFormatter={(_, p) => (p?.[0] ? `${istDay(p[0].payload.time)} ${istTime(p[0].payload.time)} IST` : "")} />
            <Legend wrapperStyle={{ fontSize: 12, color: "#93a1b3" }} />
            <Bar yAxisId="r" dataKey="rain" name="Rain (mm/h)" fill="#3b82f6" barSize={6} />
            <Line yAxisId="t" dataKey="temp" name="Temperature (°C)" stroke="#f59e0b" dot={false} strokeWidth={2} />
            <Line yAxisId="t" dataKey="feels" name="Feels like (°C)" stroke="#f59e0b" strokeDasharray="4 3" dot={false} strokeWidth={1} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-3 overflow-x-auto">
        <table className="w-full min-w-[640px] text-[12.5px] tabular-nums" data-testid="hourly-table">
          <thead className="text-left text-muted">
            <tr className="border-b border-line"><th className="py-1.5 font-normal">Time (IST)</th><th className="font-normal">Weather</th><th className="text-right font-normal">Temp °C</th><th className="text-right font-normal">Feels</th><th className="text-right font-normal">Rain mm</th><th className="text-right font-normal">Chance</th><th className="text-right font-normal">RH %</th><th className="text-right font-normal">Wind km/h</th><th className="text-right font-normal">Gust</th></tr>
          </thead>
          <tbody>
            {rows.filter((_, i) => i % 3 === 0).map((r) => (
              <tr key={r.time} className="border-b border-line/60">
                <td className="py-1.5">{istDay(r.time, { weekday: "short" })} {istTime(r.time, { hour: "numeric" })}</td>
                <td className="text-muted">{wmoText(r.code)}</td>
                <td className="text-right">{num(r.temp, 1)}</td><td className="text-right text-muted">{num(r.feels, 1)}</td>
                <td className="text-right">{num(r.rain, 1)}</td><td className="text-right">{num(r.pop)}%</td>
                <td className="text-right">{num(r.rh)}</td><td className="text-right">{num(r.wind)} {compass(r.dir)}</td><td className="text-right">{num(r.gust)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="mt-1 text-[11.5px] text-muted">Every third hour shown in the table; the chart shows all 48 hours from CORE.</p>
      </div>
    </div>
  );
}

function range(vals: (number | null | undefined)[], digits = 0) {
  const v = vals.filter((x): x is number => typeof x === "number");
  if (!v.length) return "—";
  const lo = Math.min(...v), hi = Math.max(...v);
  return lo === hi ? num(lo, digits) : `${num(lo, digits)}–${num(hi, digits)}`;
}

function TenDay({ d }: { d: CoreDashboard }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] text-[12.5px] tabular-nums" data-testid="daily-table">
        <thead className="text-left text-muted">
          <tr className="border-b border-line">
            <th className="py-1.5 font-normal">Day</th><th className="font-normal">Weather</th>
            <th className="text-right font-normal">Max / min °C</th><th className="text-right font-normal">Normal max / min</th>
            <th className="text-right font-normal">Max across models</th>
            <th className="text-right font-normal">Rain mm</th><th className="text-right font-normal">Rain across models</th>
            <th className="text-right font-normal">Chance</th><th className="text-right font-normal">Gust km/h</th>
          </tr>
        </thead>
        <tbody>
          {d.daily.map((r) => {
            const m = r.models ?? {};
            const names = Object.keys(m);
            return (
              <tr key={r.date} className="border-b border-line/60" data-testid="daily-row" data-date={r.date}>
                <td className="py-1.5">{istDay(r.date)}</td>
                <td className="text-muted">{wmoText(r.weather_code)}</td>
                <td className="text-right font-medium">{num(r.temperature_2m_max)} / {num(r.temperature_2m_min)}</td>
                <td className="text-right text-muted">{num(r.normal_tmax)} / {num(r.normal_tmin)}</td>
                <td className="text-right" title={names.map((k) => `${MODEL_NAME[k] ?? k} ${num(m[k].tmax, 1)}°`).join(" · ")}>{range(names.map((k) => m[k].tmax))}</td>
                <td className="text-right font-medium">{num(r.precipitation_sum, 1)}</td>
                <td className="text-right" title={names.map((k) => `${MODEL_NAME[k] ?? k} ${num(m[k].precip, 1)} mm`).join(" · ")}>{range(names.map((k) => m[k].precip), 1)}</td>
                <td className="text-right">{num(r.precipitation_probability_max)}%</td>
                <td className="text-right">{num(r.wind_gusts_10m_max)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="mt-2 text-[11.5px] leading-relaxed text-muted">
        Main values: CORE's best-match forecast. "Across models" is the spread of the independent models (ECMWF, GFS, ICON) for that day — a range between models, not a probability; hover for each model.
        Normals: NASA POWER 1991–2020 (MERRA-2), indicative.
      </p>
    </div>
  );
}
