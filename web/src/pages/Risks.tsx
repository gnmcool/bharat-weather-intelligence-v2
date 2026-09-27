import { useMemo, useState } from "react";
import { core } from "../core-api/client";
import type { CoreOfficialWarning } from "../core-api/types";
import { OfficialAlert, Provenance, SystemLabel, SystemRisk } from "../components/ui";
import { AGREEMENT_EXPLAINER, sevRank } from "../lib/present";
import type { Mode } from "../lib/store";
import { useCore } from "../lib/useCore";
import { DataQualityNotices } from "../components/DataQualityNotice";
import { Load, RunLine, Section, useDashboard, useEvents } from "./blocks";

export default function RisksPage({ mode }: { mode: Mode }) {
  const dash = useDashboard();
  const events = useEvents();
  const national = useCore<CoreOfficialWarning[]>("warnings", core.warnings);
  const localFirst = mode !== "government";

  const local = (
    <Load s={dash} lines={6}>
      {(d) => (
        <div className="space-y-6">
          <Section title={`Official alerts for ${d.location.name}`} right={<span>{d.warnings.length} active</span>}>
            {d.warnings.length ? (
              <div className="space-y-2">{[...d.warnings].sort((a, b) => sevRank(b) - sevRank(a)).map((w) => <OfficialAlert key={w.id} w={w} />)}</div>
            ) : (
              <p className="text-[13.5px] text-muted" data-testid="no-local-alerts">No official alert in the NDMA SACHET feed matches this district or state right now.</p>
            )}
          </Section>
          <Section title="System assessments — next 7 days" right={<SystemLabel />}>
            <p className="mb-3 max-w-3xl text-[12.5px] leading-relaxed text-muted">
              Bharat Weather Intelligence analysis from CORE's documented rules (IMD criteria where they exist; system indicators marked experimental).
              These are not official warnings. {AGREEMENT_EXPLAINER}
            </p>
            {events.state === "ok" && <DataQualityNotices list={events.data.data_quality} className="mb-3" />}
            <div className="grid gap-2 lg:grid-cols-2" data-testid="risk-list">
              {[...d.risks].sort((a, b) => b.level - a.level).map((r) => <SystemRisk key={r.id} r={r} />)}
            </div>
          </Section>
          <div className="space-y-2 border-t border-line pt-4"><RunLine d={d} /><Provenance sources={d.sources} /></div>
        </div>
      )}
    </Load>
  );

  const all = (
    <Section title="All official alerts in India" right={national.state === "ok" ? <span>{national.data.length} active · NDMA SACHET</span> : undefined}>
      <Load s={national} lines={5}>{(ws) => <NationalAlerts ws={ws} />}</Load>
    </Section>
  );

  return <div className="space-y-6">{localFirst ? <>{local}{all}</> : <>{all}{local}</>}</div>;
}

function NationalAlerts({ ws }: { ws: CoreOfficialWarning[] }) {
  const [sev, setSev] = useState<string>("all");
  const [q, setQ] = useState("");
  const [all, setAll] = useState(false);
  const list = useMemo(() => ws
    .filter((w) => sev === "all" || w.severity === sev)
    .filter((w) => !q || `${w.area} ${w.headline} ${w.issuer} ${w.sender}`.toLowerCase().includes(q.toLowerCase()))
    .sort((a, b) => sevRank(b) - sevRank(a)), [ws, sev, q]);
  const count = (s: string) => ws.filter((w) => w.severity === s).length;
  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center gap-2 text-[12.5px]">
        {["all", "Extreme", "Severe", "Moderate", "Minor"].map((s) => (
          <button key={s} onClick={() => setSev(s)} className={`rounded-md px-2.5 py-1 ${sev === s ? "bg-text text-bg" : "bg-surface-2 text-muted hover:text-text"}`}>
            {s === "all" ? `All ${ws.length}` : `${s} ${count(s)}`}
          </button>
        ))}
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filter by state, district or issuer"
          className="h-8 min-w-[200px] flex-1 rounded-md border border-line bg-bg px-2.5 outline-none focus:border-accent" aria-label="Filter alerts" />
      </div>
      <div className="grid gap-2 lg:grid-cols-2">{(all ? list : list.slice(0, 12)).map((w) => <OfficialAlert key={w.id} w={w} />)}</div>
      {!all && list.length > 12 && (
        <button onClick={() => setAll(true)} className="mt-3 rounded-md border border-line px-3 py-1.5 text-[13px] hover:border-accent">Show all {list.length} alerts</button>
      )}
      {!list.length && <p className="text-[13px] text-muted">No alerts match this filter.</p>}
      <p className="mt-3 text-[11.5px] text-muted">Official Common Alerting Protocol messages from IMD, CWC and State Disaster Management Authorities via NDMA SACHET, shown with the issuer's wording.</p>
    </div>
  );
}
