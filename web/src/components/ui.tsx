import { ChevronDown, ExternalLink, Info, ScanSearch, ShieldAlert } from "lucide-react";
import { useState, type ReactNode } from "react";
import type { CoreOfficialWarning, CoreProvenance, CoreRiskItem } from "../core-api/types";
import { istDateTime, runLabel } from "../lib/format";
import { AGREEMENT_EXPLAINER, LEVEL, modelAgreement, riskLabel, SEVERITY } from "../lib/present";
import { useApp } from "../lib/store";
import type { Loadable } from "../lib/useCore";

export function Section({ title, right, children, id, className = "" }: { title: string; right?: ReactNode; children: ReactNode; id?: string; className?: string }) {
  return (
    <section id={id} className={`border-t border-line pt-5 ${className}`}>
      <div className="mb-3 flex items-baseline justify-between gap-3">
        <h2 className="text-[12px] font-semibold uppercase tracking-[0.08em] text-muted">{title}</h2>
        {right && <div className="text-[12px] text-muted">{right}</div>}
      </div>
      {children}
    </section>
  );
}

/** Loading / error handling for any CORE request. Errors name the endpoint; nothing is substituted. */
export function Load<T>({ s, children, lines = 3 }: { s: Loadable<T>; children: (d: T) => ReactNode; lines?: number }) {
  if (s.state === "ok") return <>{children(s.data)}</>;
  if (s.state === "error")
    return (
      <div role="alert" className="rounded-lg border border-official/40 bg-official/10 px-3 py-2 text-[13px] text-red-200">
        Source unavailable: {s.message}. No substitute data is shown.
      </div>
    );
  return (
    <div className="space-y-2" aria-busy="true">
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className="h-4 animate-pulse rounded bg-surface-2" style={{ width: `${90 - i * 12}%` }} />
      ))}
    </div>
  );
}

export function LevelDot({ level }: { level: number }) {
  return <span className={`inline-block h-2.5 w-2.5 shrink-0 rounded-full ${LEVEL[level]?.dot ?? "bg-muted"}`} aria-hidden />;
}

/** OFFICIAL ALERT — issuer wording verbatim. Never styled or labelled like a system assessment. */
export function OfficialAlert({ w, compact }: { w: CoreOfficialWarning; compact?: boolean }) {
  return (
    <article className="rounded-lg border border-official/50 bg-official/[0.08] p-3" data-testid="official-alert" data-alert-id={w.id}>
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px]">
        <span className="inline-flex items-center gap-1 rounded bg-official px-1.5 py-0.5 font-semibold uppercase tracking-wide text-white">
          <ShieldAlert size={12} /> Official alert
        </span>
        {w.severity && <span className={`font-semibold ${SEVERITY[w.severity]?.text ?? "text-text"}`}>{w.severity}</span>}
        {w.event && <span className="text-text">{w.event}</span>}
        <span className="text-muted">· {w.issuer}</span>
      </div>
      <p className={`mt-1.5 text-[13.5px] leading-snug text-text ${compact ? "line-clamp-3" : ""}`}>{w.headline}</p>
      <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11.5px] text-muted">
        {w.area && <span>{w.area}</span>}
        <span>Valid {istDateTime(w.effective)} → {istDateTime(w.expires)}</span>
        {w.link && (
          <a className="inline-flex items-center gap-1 text-accent hover:underline" href={w.link} target="_blank" rel="noreferrer">
            Original CAP message <ExternalLink size={11} />
          </a>
        )}
      </div>
      <div className="mt-1 text-[11px] text-muted">Source: {w.source}{w.sender ? ` · sent by ${w.sender}` : ""}</div>
    </article>
  );
}

/** SYSTEM ASSESSMENT — one CORE risk item, levels and rules unchanged; "confidence" shown as Model agreement. */
export function SystemRisk({ r, open: openInit = false }: { r: CoreRiskItem; open?: boolean }) {
  const [open, setOpen] = useState(openInit);
  const { place, openEvidence } = useApp();
  const ag = modelAgreement(r.confidence);
  const lv = LEVEL[r.level] ?? LEVEL[0];
  return (
    <article className={`rounded-lg border bg-surface ${lv.ring}`} data-testid="system-risk" data-risk-id={r.id} data-risk-level={r.level}>
      <button className="flex w-full items-start gap-3 px-3 py-2.5 text-left" onClick={() => setOpen(!open)} aria-expanded={open}>
        <LevelDot level={r.level} />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-baseline gap-x-2">
            <span className="text-[14px] font-medium text-text">{riskLabel(r)}</span>
            <span className={`text-[12.5px] font-medium ${lv.text}`} data-testid="risk-status">{r.status}</span>
            {r.official ? (
              <span className="rounded bg-official/20 px-1 text-[10.5px] font-semibold uppercase text-red-200">From official alert</span>
            ) : r.experimental ? (
              <span className="rounded bg-surface-2 px-1 text-[10.5px] uppercase text-muted">Experimental</span>
            ) : null}
          </div>
          <div className="mt-0.5 text-[13px] text-muted">{r.headline}</div>
        </div>
        <ChevronDown size={16} className={`mt-1 shrink-0 text-muted transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <div className="space-y-2 border-t border-line px-3 py-3 text-[12.5px] leading-relaxed">
          <p className="text-text">{r.explanation}</p>
          <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-muted">
            <dt>Rule</dt><dd className="text-text">{r.criterion}</dd>
            {(r.period_start || r.period_end) && (<><dt>Period</dt><dd className="text-text">{istDateTime(r.period_start)} → {istDateTime(r.period_end)}</dd></>)}
            {r.peak_value !== null && (<><dt>Peak</dt><dd className="text-text">{r.peak_value} {r.unit}</dd></>)}
            <dt title={AGREEMENT_EXPLAINER}>Agreement</dt>
            <dd className="text-text" data-testid="model-agreement">{ag.short}. <span className="text-muted">{ag.detail}</span></dd>
            <dt>Sources</dt><dd className="text-text">{r.sources.join(" · ")}</dd>
            {r.reference && (<><dt>Method</dt><dd className="text-text">CORE methodology {r.reference}</dd></>)}
          </dl>
          <EvidenceButton onClick={() => openEvidence({ point: { lat: place.lat, lon: place.lon, name: place.name, taluka: place.taluka }, risk: r.id })} />
          <p className="flex items-start gap-1.5 text-[11.5px] text-muted"><Info size={12} className="mt-0.5 shrink-0" />{AGREEMENT_EXPLAINER}</p>
        </div>
      )}
    </article>
  );
}

export function SystemLabel() {
  return <span className="rounded bg-system/25 px-1.5 py-0.5 text-[10.5px] font-semibold uppercase tracking-wide text-slate-200">System assessment</span>;
}

/** Provenance list, verbatim from CORE. */
export function Provenance({ sources, extra }: { sources: CoreProvenance[]; extra?: ReactNode }) {
  return (
    <details className="group text-[12px] text-muted">
      <summary className="cursor-pointer select-none list-none hover:text-text">
        <span className="underline decoration-dotted underline-offset-2">Sources and data provenance</span>
      </summary>
      <ul className="mt-2 space-y-1.5">
        {sources.map((s, i) => (
          <li key={i} data-testid="provenance">
            <span className="text-text">{s.source}</span>
            {s.model && <> — {s.model}</>}
            {s.issue_time && <> · run {runLabel(s.issue_time)}</>}
            {s.notes && <div>{s.notes}</div>}
            {s.licence && <div className="text-[11px]">Licence: {s.licence}</div>}
          </li>
        ))}
        {extra}
      </ul>
    </details>
  );
}

export function Stat({ label, value, sub, testid }: { label: string; value: ReactNode; sub?: ReactNode; testid?: string }) {
  return (
    <div className="min-w-0">
      <div className="text-[11.5px] text-muted">{label}</div>
      <div className="text-[16px] font-medium tabular-nums text-text" data-testid={testid}>{value}</div>
      {sub && <div className="text-[11px] text-muted">{sub}</div>}
    </div>
  );
}

/** Opens the evidence drawer (same structure everywhere). */
export function EvidenceButton({ onClick, label = "View evidence" }: { onClick: () => void; label?: string }) {
  return (
    <button onClick={onClick} data-testid="view-evidence"
      className="inline-flex items-center gap-1.5 rounded-md border border-line px-2 py-1 text-[12px] font-medium text-accent hover:border-accent">
      <ScanSearch size={13} /> {label}
    </button>
  );
}
