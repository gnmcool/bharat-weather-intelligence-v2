import { ExternalLink, ShieldAlert, ShieldCheck, X } from "lucide-react";
import { useEffect, type ReactNode } from "react";
import { istDateTime, istDay, num, runLabel, signed } from "../lib/format";
import { LEVEL } from "../lib/present";
import { useApp } from "../lib/store";
import { useCore } from "../lib/useCore";
import { v2 } from "../v2-api/client";
import type { V2Evidence } from "../v2-api/types";
import { LevelDot, Load, OfficialAlert, SystemLabel } from "./ui";

/**
 * One evidence structure for every system assessment, wherever it is opened from
 * (What should you know, Risks list, map, Government counts, Farmer):
 * WHAT WAS DETECTED → WHEN → MODEL AGREEMENT → FORECAST RANGE → NORMAL / DEPARTURE →
 * SATELLITE EVIDENCE → OFFICIAL ALERT → RULE APPLIED → PROVENANCE.
 * All content comes from /api/v2/evidence, which is built from CORE /api/v1 responses.
 */
export default function EvidenceDrawer() {
  const { evidence: t, openEvidence } = useApp();
  const key = t ? `ev:${t.point.lat},${t.point.lon},${t.point.name},${t.risk}` : null;
  const ev = useCore<V2Evidence>(key, () => v2.evidence(t!.point, t!.risk));
  useEffect(() => {
    if (!t) return;
    const esc = (e: KeyboardEvent) => e.key === "Escape" && openEvidence(null);
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [t, openEvidence]);
  if (!t) return null;
  return (
    <div className="fixed inset-0 z-50" role="dialog" aria-modal="true" aria-label="Evidence">
      <button className="absolute inset-0 bg-black/50" aria-label="Close evidence" onClick={() => openEvidence(null)} />
      <aside className="absolute inset-x-0 bottom-0 flex max-h-[88vh] flex-col rounded-t-2xl border border-line bg-bg shadow-2xl sm:inset-y-0 sm:left-auto sm:right-0 sm:max-h-none sm:w-[520px] sm:rounded-none sm:border-y-0 sm:border-r-0"
        data-testid="evidence-drawer" data-risk={t.risk}>
        <div className="flex items-start justify-between gap-3 border-b border-line px-4 py-3">
          <div className="min-w-0">
            <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-muted">Why is this shown?</div>
            <div className="truncate text-[15px] font-medium">{ev.state === "ok" ? ev.data.sections.detected.title : t.risk} · {t.point.name ?? `${t.point.lat.toFixed(3)}, ${t.point.lon.toFixed(3)}`}</div>
            {t.context && <div className="mt-0.5 text-[12px] text-muted">{t.context}</div>}
          </div>
          <button onClick={() => openEvidence(null)} aria-label="Close" className="rounded-md p-1 hover:bg-surface-2"><X size={18} /></button>
        </div>
        <div className="flex-1 overflow-y-auto px-4 py-3">
          <Load s={ev} lines={10}>{(d) => <Body d={d} />}</Load>
        </div>
      </aside>
    </div>
  );
}

function S({ n, k, title, children }: { n: number; k: string; title: string; children: ReactNode }) {
  return (
    <section className="border-b border-line py-3 last:border-b-0" data-testid="ev-section" data-key={k}>
      <h3 className="mb-1.5 flex items-center gap-2 text-[11.5px] font-semibold uppercase tracking-[0.08em] text-muted">
        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-surface-2 text-[10.5px] text-text">{n}</span>{title}
      </h3>
      <div className="space-y-1.5 text-[13px] leading-relaxed">{children}</div>
    </section>
  );
}
const Plain = ({ children }: { children: ReactNode }) => <p className="text-text">{children}</p>;
const Small = ({ children }: { children: ReactNode }) => <p className="text-[11.5px] text-muted">{children}</p>;
const Unavailable = ({ children }: { children: ReactNode }) => <p className="text-[12.5px] text-muted" data-testid="ev-unavailable">Not available — {children}</p>;

function Body({ d }: { d: V2Evidence }) {
  const s = d.sections;
  const lv = LEVEL[s.detected.severity.level] ?? LEVEL[0];
  const fr = s.forecast_range, nd = s.normal_departure, e2s = s.earth2studio;
  const win = s.when.evidence_window;
  return (
    <div>
      <S n={1} k="detected" title="What was detected">
        <div className="flex flex-wrap items-center gap-2">
          {s.detected.classification === "system" ? <SystemLabel /> : (
            <span className="inline-flex items-center gap-1 rounded bg-official px-1.5 py-0.5 text-[10.5px] font-semibold uppercase text-white"><ShieldAlert size={11} /> From official alert</span>
          )}
          {s.detected.experimental && <span className="rounded bg-surface-2 px-1 text-[10.5px] uppercase text-muted">Experimental</span>}
        </div>
        <div className="flex items-center gap-2"><LevelDot level={s.detected.severity.level} /><span className="font-medium">{s.detected.title}</span>
          <span className={`font-medium ${lv.text}`} data-testid="ev-level" data-level={s.detected.severity.level}>{s.detected.severity.status}</span></div>
        <Plain>{s.detected.headline}</Plain>
        <Small>{s.detected.explanation}</Small>
        <Small>{s.detected.classification_label}. Location: {d.location.name}{d.location.district ? `, ${d.location.district} district` : ""} — point forecast.</Small>
      </S>

      <S n={2} k="when" title="When">
        {s.when.start ? (
          <Plain><span data-testid="ev-when">{istDateTime(s.when.start)} → {istDateTime(s.when.end)}</span></Plain>
        ) : (
          <Plain>{s.when.timing_note}</Plain>
        )}
        <Small>Values below are taken over {win.dates.length === 1 ? istDay(win.dates[0]) : `${istDay(win.dates[0])} – ${istDay(win.dates[win.dates.length - 1])}`} ({win.basis}).</Small>
      </S>

      <S n={3} k="model_agreement" title="Model agreement">
        {s.model_agreement.assessed ? (
          <>
            <Plain><b data-testid="ev-agreement">{s.model_agreement.text}</b> — {s.model_agreement.agreeing} of the {s.model_agreement.of} independent forecast models (ECMWF, GFS, ICON) show this.</Plain>
            <Small>CORE: “{s.model_agreement.basis}”. {s.model_agreement.note}</Small>
          </>
        ) : (
          <>
            <p className="text-text" data-testid="ev-agreement">{s.model_agreement.text}</p>
            <Small>{s.model_agreement.note}{s.model_agreement.basis ? ` CORE: “${s.model_agreement.basis}”.` : ""}</Small>
          </>
        )}
      </S>

      <S n={4} k="forecast_range" title="Forecast range">
        {fr.available ? (
          <>
            <Plain>{fr.variable}: <b data-testid="ev-range">{fr.text}</b></Plain>
            <table className="w-full text-[12.5px] tabular-nums">
              <tbody>
                {Object.entries(fr.per_model!).map(([m, v]) => (
                  <tr key={m} className="border-b border-line/60" data-testid="ev-model" data-model={m} data-value={v.value ?? ""}>
                    <td className="py-1">{m}</td><td className="text-right">{num(v.value, 1)} {fr.unit}</td><td className="pl-3 text-[11px] text-muted">independent model</td>
                  </tr>
                ))}
                <tr data-testid="ev-e2s" data-value={e2s.available ? e2s.value ?? "" : ""}>
                  <td className="py-1 text-muted">GFS · Earth2Studio</td>
                  <td className="text-right text-muted">{e2s.available ? `${num(e2s.value, 1)} ${e2s.unit}${e2s.partial ? " *" : ""}` : "—"}</td>
                  <td className="pl-3 text-[11px] text-muted">same model as GFS — not counted</td>
                </tr>
              </tbody>
            </table>
            <Small>{fr.note}</Small>
          </>
        ) : (
          <>
            <Unavailable>{fr.reason}</Unavailable>
            {e2s.available && (
              <p className="text-[12.5px]" data-testid="ev-e2s" data-value={e2s.value ?? ""}>GFS · Earth2Studio: {e2s.variable?.toLowerCase()} {num(e2s.value, 1)} {e2s.unit} <span className="text-muted">(same model as GFS — not an independent model)</span></p>
            )}
          </>
        )}
        {e2s.available ? (
          <Small>Earth2Studio: {e2s.variable}, run {runLabel(e2s.issue_time ?? null)}, {istDateTime(e2s.valid_from ?? null)} → {istDateTime(e2s.valid_to ?? null)}. {e2s.partial_note ? `* ${e2s.partial_note}` : ""} {e2s.note}</Small>
        ) : (
          <Small>Earth2Studio GFS: {e2s.reason}</Small>
        )}
      </S>

      <S n={5} k="normal_departure" title="Normal / departure">
        {nd.forecast ? (
          <div className="grid grid-cols-3 gap-2 text-center" data-testid="ev-normal">
            <div className="rounded-lg bg-surface px-2 py-1.5"><div className="text-[11px] text-muted">Forecast</div><div className="font-medium tabular-nums">{num(nd.forecast.value, 1)} {nd.forecast.unit}</div></div>
            <div className="rounded-lg bg-surface px-2 py-1.5"><div className="text-[11px] text-muted">Normal (1991–2020)</div><div className="font-medium tabular-nums">{num(nd.normal!.value, 1)} {nd.normal!.unit}</div></div>
            <div className="rounded-lg bg-surface px-2 py-1.5"><div className="text-[11px] text-muted">Departure</div><div className="font-medium tabular-nums">{signed(nd.departure!.value)} {nd.departure!.unit}{nd.departure!.pct !== null ? ` (${signed(nd.departure!.pct, 0)}%)` : ""}</div></div>
          </div>
        ) : !nd.core_anomaly_items.length ? <Unavailable>{nd.reason}</Unavailable> : null}
        {nd.forecast && <Small>{nd.forecast.label}, {nd.forecast.dates.map((x) => istDay(x)).join(", ")}. {nd.note}</Small>}
        {nd.core_anomaly_items.map((it) => (
          <p key={it.id} className="text-[12.5px]"><span className="text-muted">{it.label} · {it.period}:</span> {num(it.value, 1)} {it.unit} vs normal {num(it.normal, 1)} — {signed(it.departure)} {it.unit}{it.category ? ` (${it.category})` : ""}</p>
        ))}
        <Small>Normal: {nd.baseline.label}.</Small>
      </S>

      <S n={6} k="satellite" title="Satellite evidence">
        <Plain><span data-testid="ev-satellite">{s.satellite.status}</span>{s.satellite.layers.length ? `: ${s.satellite.layers.map((l) => l.label).join(", ")}` : ""}</Plain>
        {s.satellite.note && <Small>{s.satellite.note}</Small>}
      </S>

      <S n={7} k="official" title="Official alert">
        {s.official.status === "OFFICIAL ALERT" ? (
          <>
            <div className="inline-flex items-center gap-1 rounded bg-official px-1.5 py-0.5 text-[11px] font-semibold uppercase text-white" data-testid="ev-official">Official alert</div>
            <div className="space-y-2">{s.official.alerts.map((w) => <OfficialAlert key={w.id} w={w} compact />)}</div>
          </>
        ) : (
          <div className="inline-flex items-center gap-1 rounded border border-line px-1.5 py-0.5 text-[11px] font-semibold uppercase text-muted" data-testid="ev-official"><ShieldCheck size={12} /> No official alert</div>
        )}
        {s.official.other_alerts_at_location.length > 0 && (
          <Small>Other official alerts at this location (different hazard): {s.official.other_alerts_at_location.map((a) => `${a.event ?? "alert"} — ${a.issuer}`).join("; ")}.</Small>
        )}
        <Small>{s.official.match_note} Source: {s.official.source}. The system assessment above is not an official warning.</Small>
      </S>

      <S n={8} k="rule" title="Rule applied">
        <div className="space-y-1 rounded-lg bg-surface px-3 py-2 text-[12.5px]">
          <div><span className="text-muted">Data · </span>{s.rule.data.peak_value !== null ? `${num(s.rule.data.peak_value, 1)} ${s.rule.data.unit ?? ""}` : "see headline"}</div>
          <div><span className="text-muted">Rule · </span><span data-testid="ev-rule">{s.rule.criterion}</span></div>
          <div><span className="text-muted">Result · </span>{s.rule.result}</div>
        </div>
        <Small>{s.rule.note}{s.rule.reference ? ` CORE methodology reference ${s.rule.reference}.` : ""}</Small>
      </S>

      <S n={9} k="provenance" title="Provenance">
        <ul className="space-y-1.5 text-[12px]">
          {s.provenance.map((p, i) => (
            <li key={i} data-testid="ev-provenance">
              <span className="text-text">{p.provider}</span>{p.model ? ` — ${p.model}` : ""}
              {p.run && <> · run {runLabel(p.run)}</>}
              {p.valid && <> · valid {p.valid}</>}
              {p.run_detail && <div className="text-muted">{p.run_detail}</div>}
              <div className="text-muted">
                {p.source && (p.source.startsWith("http") ? <a href={p.source} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-accent">{p.source} <ExternalLink size={10} /></a> : <>CORE {p.source}</>)}
                {p.retrieved_at && <> · retrieved {istDateTime(p.retrieved_at)}</>}
              </div>
            </li>
          ))}
        </ul>
      </S>
    </div>
  );
}
