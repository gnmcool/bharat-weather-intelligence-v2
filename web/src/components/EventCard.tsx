import { istDateTime } from "../lib/format";
import { LEVEL } from "../lib/present";
import { useApp } from "../lib/store";
import type { V2Event } from "../v2-api/types";
import { eventText, type Lang, type Out } from "../i18n/coreText";
import { dateLocale } from "../i18n/lang";
import { EvidenceButton, LevelDot, SystemLabel } from "./ui";

export type Audience = "citizen" | "farmer" | "government";

/**
 * SYSTEM ASSESSMENT event from /api/v2/events. Never styled like an official alert.
 * FACT (CORE headline) → ASSESSMENT (level, timing, agreement) → EVIDENCE (drawer) → POTENTIAL RELEVANCE (context).
 */
/** English that stays English inside a Gujarati card is marked lang="en", never presented as a translation. */
const T = ({ o, lang }: { o: Out; lang: Lang }) =>
  lang === "gu" && !o.gu && o.text ? <span lang="en" data-untranslated>{o.text}</span> : <>{o.text}</>;

/** Gujarati (farmer screen only for now). The evidence drawer itself stays English. */
const GU = { when: "ક્યારે:", experimental: "પ્રાયોગિક", context: "સંભવિત સુસંગતતા · સામાન્ય સંદર્ભ, અસરની આગાહી નથી", evidence: "પુરાવા જુઓ (અંગ્રેજીમાં)" };

export function EventCard({ e, showLabel = false, audience = "citizen", lang = "en" }: { e: V2Event; showLabel?: boolean; audience?: Audience; lang?: Lang }) {
  const openEvidence = useApp((s) => s.openEvidence);
  const lv = LEVEL[e.severity.level] ?? LEVEL[0];
  // Gujarati only where the farmer context is shown; other audiences keep English.
  const gu = lang === "gu" && audience === "farmer";
  const x = gu ? eventText({ ...e, context: e.context ? { farmer: e.context.farmer } : null }, "gu") : null;
  return (
    <article className={`rounded-lg border bg-surface px-3 py-2.5 ${lv.ring}`} data-testid="event" data-event-type={e.type}
      data-level={e.severity.level} data-start={e.start ?? ""} data-end={e.end ?? ""} data-classification={e.classification}>
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
        {showLabel && <SystemLabel />}
        <LevelDot level={e.severity.level} />
        <span className="text-[14px] font-medium">{x ? <T o={x.title} lang="gu" /> : e.title}</span>
        <span className={`text-[12.5px] font-medium ${lv.text}`} data-testid="event-status">{x ? <T o={x.status} lang="gu" /> : e.severity.status}</span>
        {e.experimental && <span className="rounded bg-surface-2 px-1 text-[10.5px] uppercase text-muted">{gu ? GU.experimental : "Experimental"}</span>}
      </div>
      <div className="mt-1 text-[13px] text-text" data-core-text>{x ? <T o={x.headline} lang="gu" /> : e.headline}</div>
      <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-[12px] text-muted">
        <span data-testid="event-when"><span className="text-text">{gu ? GU.when : "When:"}</span> {e.start ? `${istDateTime(e.start, gu ? dateLocale("gu") : undefined)} → ${istDateTime(e.end, gu ? dateLocale("gu") : undefined)}` : x ? <T o={x.timing} lang="gu" /> : e.timing_note}</span>
        <span data-testid="event-agreement">{x ? <T o={x.agreement} lang="gu" /> : e.model_agreement.text}</span>
      </div>
      {e.context && (
        <p className="mt-1.5 border-l-2 border-line pl-2 text-[12.5px] text-muted" data-testid="impact-context" title={`${e.context.label}. ${e.context.source}`}>
          <span className="text-[10.5px] font-semibold uppercase tracking-wide">{gu ? GU.context : "Potential relevance · context"}</span><br />
          <span className="text-text/90">{x ? <T o={x.context} lang="gu" /> : e.context[audience]}</span>
        </p>
      )}
      <div className="mt-2">
        <EvidenceButton label={gu ? GU.evidence : undefined} onClick={() => openEvidence({ point: { lat: e.location.lat, lon: e.location.lon, name: e.location.name, taluka: e.location.taluka }, risk: e.type })} />
      </div>
    </article>
  );
}
