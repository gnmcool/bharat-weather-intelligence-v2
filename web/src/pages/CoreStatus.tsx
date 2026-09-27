import { useEffect, useState } from "react";
// Imported read-only from CORE (git submodule) — proves V2 reuses CORE's client and formatting as-is.
import { api, type Dashboard, type GridMeta } from "@core/lib/api";
import { fmtDateTime, n } from "@core/lib/format";

type Row = { label: string; value: string; ok: boolean | null };

// Live connection panel: real values from CORE's production API. No mock data.
export default function CoreStatus() {
  const [meta, setMeta] = useState<GridMeta | null>(null);
  const [dash, setDash] = useState<Dashboard | null>(null);
  const [alerts, setAlerts] = useState<number | null>(null);
  const [err, setErr] = useState<string[]>([]);

  useEffect(() => {
    const fail = (what: string) => () => setErr((e) => [...e, what]);
    api.gridMeta().then(setMeta).catch(fail("grid"));
    api.dashboard(23.0225, 72.5714, "Ahmedabad").then(setDash).catch(fail("dashboard"));
    api.warnings().then((w) => setAlerts(w.length)).catch(fail("alerts"));
  }, []);

  const rows: Row[] = [
    {
      label: "Earth2Studio forecast",
      value: meta ? `${meta.model} · run ${fmtDateTime(meta.issue_time)}` : err.includes("grid") ? "unavailable" : "loading…",
      ok: meta ? meta.source.includes("Earth2Studio") : err.includes("grid") ? false : null,
    },
    {
      label: "Ahmedabad now",
      value: dash ? `${n(dash.current.values.temperature_2m?.value, 1)}°C · ${n(dash.current.values.relative_humidity_2m?.value)}% RH` : err.includes("dashboard") ? "unavailable" : "loading…",
      ok: dash ? true : err.includes("dashboard") ? false : null,
    },
    {
      label: "Official alerts (SACHET)",
      value: alerts !== null ? `${alerts} active` : err.includes("alerts") ? "unavailable" : "loading…",
      ok: alerts !== null ? true : err.includes("alerts") ? false : null,
    },
  ];

  return (
    <aside className="rounded-xl border border-line bg-surface p-5">
      <div className="text-[12px] uppercase tracking-wide text-muted">Connection to CORE</div>
      <p className="mt-1 text-[13px] text-muted">Live values from the CORE API that V2 consumes (read-only).</p>
      <dl className="mt-4 divide-y divide-line">
        {rows.map((r) => (
          <div key={r.label} className="flex items-start justify-between gap-3 py-2.5">
            <dt className="flex items-center gap-2 text-[13px]">
              <span className={`inline-block h-2 w-2 rounded-full ${r.ok === null ? "bg-muted" : r.ok ? "bg-emerald-400" : "bg-official"}`} />
              {r.label}
            </dt>
            <dd className="text-right text-[13px] text-text">{r.value}</dd>
          </div>
        ))}
      </dl>
      {dash && (
        <p className="mt-3 text-[11.5px] leading-snug text-muted">
          Sources: {dash.sources.map((s) => s.source).filter((v, i, a) => a.indexOf(v) === i).join(" · ")}
        </p>
      )}
    </aside>
  );
}
