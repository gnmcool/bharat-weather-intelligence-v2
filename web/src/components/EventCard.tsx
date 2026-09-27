import { istDateTime } from "../lib/format";
import { LEVEL } from "../lib/present";
import { useApp } from "../lib/store";
import type { V2Event } from "../v2-api/types";
import { EvidenceButton, LevelDot, SystemLabel } from "./ui";

export type Audience = "citizen" | "farmer" | "government";

/**
 * SYSTEM ASSESSMENT event from /api/v2/events. Never styled like an official alert.
 * FACT (CORE headline) → ASSESSMENT (level, timing, agreement) → EVIDENCE (drawer) → POTENTIAL RELEVANCE (context).
 */
export function EventCard({ e, showLabel = false, audience = "citizen" }: { e: V2Event; showLabel?: boolean; audience?: Audience }) {
  const openEvidence = useApp((s) => s.openEvidence);
  const lv = LEVEL[e.severity.level] ?? LEVEL[0];
  return (
    <article className={`rounded-lg border bg-surface px-3 py-2.5 ${lv.ring}`} data-testid="event" data-event-type={e.type}
      data-level={e.severity.level} data-start={e.start ?? ""} data-end={e.end ?? ""} data-classification={e.classification}>
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
        {showLabel && <SystemLabel />}
        <LevelDot level={e.severity.level} />
        <span className="text-[14px] font-medium">{e.title}</span>
        <span className={`text-[12.5px] font-medium ${lv.text}`} data-testid="event-status">{e.severity.status}</span>
        {e.experimental && <span className="rounded bg-surface-2 px-1 text-[10.5px] uppercase text-muted">Experimental</span>}
      </div>
      <div className="mt-1 text-[13px] text-text" data-core-text>{e.headline}</div>
      <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-[12px] text-muted">
        <span data-testid="event-when"><span className="text-text">When:</span> {e.start ? `${istDateTime(e.start)} → ${istDateTime(e.end)}` : e.timing_note}</span>
        <span data-testid="event-agreement">{e.model_agreement.text}</span>
      </div>
      {e.context && (
        <p className="mt-1.5 border-l-2 border-line pl-2 text-[12.5px] text-muted" data-testid="impact-context" title={`${e.context.label}. ${e.context.source}`}>
          <span className="text-[10.5px] font-semibold uppercase tracking-wide">Potential relevance · context</span><br />
          <span className="text-text/90">{e.context[audience]}</span>
        </p>
      )}
      <div className="mt-2">
        <EvidenceButton onClick={() => openEvidence({ point: { lat: e.location.lat, lon: e.location.lon, name: e.location.name, taluka: e.location.taluka }, risk: e.type })} />
      </div>
    </article>
  );
}
