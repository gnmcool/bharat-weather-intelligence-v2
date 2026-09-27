import { useEffect, useState } from "react";
import { config } from "../config";
import { core, CoreApiError } from "../core-api/client";
import type { CoreGridMeta, CoreHealth, CoreOfficialWarning } from "../core-api/types";

// M0 deployment check page — NOT the V2 application UI (that starts in M1).
// It proves three things on the deployed site: the build works, the page is served from the
// V2 repository, and CORE's API is reachable read-only from V2's origin.

type Status<T> = { state: "loading" } | { state: "ok"; data: T } | { state: "error"; message: string };

function useCore<T>(fn: () => Promise<T>): Status<T> {
  const [s, setS] = useState<Status<T>>({ state: "loading" });
  useEffect(() => {
    fn().then((data) => setS({ state: "ok", data })).catch((e: unknown) =>
      setS({ state: "error", message: e instanceof CoreApiError ? e.message : "unexpected error" }));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  return s;
}

const ist = (iso: string | null | undefined) =>
  iso ? new Date(iso).toLocaleString("en-IN", { timeZone: "Asia/Kolkata", day: "numeric", month: "short", hour: "numeric", minute: "2-digit" }) + " IST" : "—";

function Row<T>({ label, s, show }: { label: string; s: Status<T>; show: (d: T) => string }) {
  const dot = s.state === "ok" ? "bg-emerald-400" : s.state === "error" ? "bg-official" : "bg-muted";
  return (
    <div className="flex items-start justify-between gap-4 py-2.5">
      <dt className="flex items-center gap-2 text-[13px]"><span className={`inline-block h-2 w-2 rounded-full ${dot}`} />{label}</dt>
      <dd className="text-right text-[13px]">{s.state === "ok" ? show(s.data) : s.state === "error" ? <span className="text-official">{s.message}</span> : "checking…"}</dd>
    </div>
  );
}

export default function App() {
  const health = useCore<CoreHealth>(core.health);
  const grid = useCore<CoreGridMeta>(core.gridMeta);
  const alerts = useCore<CoreOfficialWarning[]>(core.warnings);
  const repo = "https://github.com/gnmcool/bharat-weather-intelligence-v2";

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
      <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-[12.5px] text-amber-200">
        V2 foundation (milestone M0) — deployment check only, not a weather product. For weather information use{" "}
        <a className="underline" href={config.coreSite}>Bharat Weather Intelligence</a>.
      </div>

      <header className="mt-6 flex items-center gap-3">
        <img src={`${import.meta.env.BASE_URL}favicon.svg`} alt="" className="h-10 w-10" />
        <div className="leading-tight">
          <h1 className="text-[20px] font-semibold tracking-tight">Bharat Weather Intelligence — V2</h1>
          <div className="text-[13px] text-muted">Weather. Impact. Decisions for a Safer, Stronger India.</div>
          <div className="text-[12px] text-muted">Made by <span className="font-medium text-text">Gaurav Makwana</span></div>
        </div>
      </header>

      <section className="mt-6 rounded-xl border border-line bg-surface p-5">
        <h2 className="text-[13px] font-semibold uppercase tracking-wide text-muted">CORE API (read-only)</h2>
        <p className="mt-1 text-[13px] text-muted">
          Live responses from <code className="text-text">{config.coreApiBase}</code>. V2 reads CORE only through this API.
        </p>
        <dl className="mt-3 divide-y divide-line">
          <Row label="API health" s={health} show={(d) => d.status} />
          <Row label="Forecast grid" s={grid} show={(d) => `${d.source} · ${d.model} · run ${ist(d.issue_time)}`} />
          <Row label="Official alerts feed" s={alerts} show={(d) => `${d.length} active (NDMA SACHET)`} />
        </dl>
      </section>

      <section className="mt-4 rounded-xl border border-line bg-surface p-5 text-[13px]">
        <h2 className="text-[13px] font-semibold uppercase tracking-wide text-muted">Build</h2>
        <dl className="mt-2 grid grid-cols-[auto_1fr] gap-x-6 gap-y-1.5">
          <dt className="text-muted">Environment</dt><dd>{config.appEnv}</dd>
          <dt className="text-muted">CORE baseline</dt><dd>{config.coreBaseline}</dd>
          <dt className="text-muted">Source</dt><dd><a className="text-accent underline" href={repo}>{repo.replace("https://", "")}</a></dd>
          <dt className="text-muted">Docs</dt><dd><a className="text-accent underline" href={`${repo}/tree/main/docs`}>architecture, boundary and data policies</a></dd>
        </dl>
      </section>
    </div>
  );
}
