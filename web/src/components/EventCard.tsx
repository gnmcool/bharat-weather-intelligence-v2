import { istDateTime } from "../lib/format";
import { LEVEL } from "../lib/present";
import { useApp } from "../lib/store";
import type { V2Event } from "../v2-api/types";
import { eventText, type Lang, type Out } from "../i18n/coreText";
import { dateLocale, EVENT_CARD } from "../i18n/lang";
import { EvidenceButton, LevelDot, SystemLabel } from "./ui";

export type Audience = "citizen" | "farmer" | "government";

/**
 * SYSTEM ASSESSMENT event from /api/v2/events. Never styled like an official alert.
 * FACT (CORE headline) → ASSESSMENT (level, timing, agreement) → EVIDENCE (drawer) → POTENTIAL RELEVANCE (context).
 */
/** English that stays English inside a Gujarati card is marked lang="en", never presented as a translation. */
const T = ({ o }: { o: Out }) => (!o.tr && o.text ? <span lang="en" data-untranslated>{o.text}</span> : <>{o.text}</>);


export function EventCard({ e, showLabel = false, audience = "citizen", lang = "en" }: { e: V2Event; showLabel?: boolean; audience?: Audience; lang?: Lang }) {
  const openEvidence = useApp((s) => s.openEvidence);
  const lv = LEVEL[e.severity.level] ?? LEVEL[0];
  // Translated only on the farmer screens; other audiences keep English. The evidence drawer itself stays English.
  const tl = lang !== "en" && audience === "farmer" ? lang : null;
  const L = tl ? EVENT_CARD[tl] : null;
  const x = tl ? eventText({ ...e, context: e.context ? { farmer: e.context.farmer } : null }, tl) : null;
  return (
    <article className={`rounded-lg border bg-surface px-3 py-2.5 ${lv.ring}`} data-testid="event" data-event-type={e.type}
      data-level={e.severity.level} data-start={e.start ?? ""} data-end={e.end ?? ""} data-classification={e.classification}>
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
        {showLabel && <SystemLabel />}
        <LevelDot level={e.severity.level} />
        <span className="text-[14px] font-medium">{x ? <T o={x.title} /> : e.title}</span>
        <span className={`text-[12.5px] font-medium ${lv.text}`} data-testid="event-status">{x ? <T o={x.status} /> : e.severity.status}</span>
        {e.experimental && <span className="rounded bg-surface-2 px-1 text-[10.5px] uppercase text-muted">{L ? L.experimental : "Experimental"}</span>}
      </div>
      <div className="mt-1 text-[13px] text-text" data-core-text>{x ? <T o={x.headline} /> : e.headline}</div>
      <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-[12px] text-muted">
        <span data-testid="event-when"><span className="text-text">{L ? L.when : "When:"}</span> {e.start ? `${istDateTime(e.start, tl ? dateLocale(tl) : undefined)} → ${istDateTime(e.end, tl ? dateLocale(tl) : undefined)}` : x ? <T o={x.timing} /> : e.timing_note}</span>
        <span data-testid="event-agreement">{x ? <T o={x.agreement} /> : e.model_agreement.text}</span>
      </div>
      {e.context && (
        <p className="mt-1.5 border-l-2 border-line pl-2 text-[12.5px] text-muted" data-testid="impact-context" title={`${e.context.label}. ${e.context.source}`}>
          <span className="text-[10.5px] font-semibold uppercase tracking-wide">{L ? L.context : "Potential relevance · context"}</span><br />
          <span className="text-text/90">{x ? <T o={x.context} /> : e.context[audience]}</span>
        </p>
      )}
      <div className="mt-2">
        <EvidenceButton label={L ? L.evidence : undefined} onClick={() => openEvidence({ point: { lat: e.location.lat, lon: e.location.lon, name: e.location.name, taluka: e.location.taluka }, risk: e.type })} />
      </div>
    </article>
  );
}
