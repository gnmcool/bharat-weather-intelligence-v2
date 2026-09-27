import { Info } from "lucide-react";
import type { V2Notice } from "../v2-api/types";

/**
 * DATA QUALITY NOTE — factual, short, not alarming. Notices come from api-v2 and are triggered
 * by CORE fields (terrain, model check, grid source), never by new thresholds (docs/DATA_QUALITY.md).
 */
export function DataQualityNotice({ n, compact = false }: { n: V2Notice; compact?: boolean }) {
  return (
    <aside className="rounded-lg border border-slate-500/30 bg-slate-500/[0.07] px-3 py-2 text-[12.5px] leading-relaxed" data-testid="dq-notice" data-id={n.id}>
      <div className="flex items-center gap-1.5 text-[10.5px] font-semibold uppercase tracking-[0.08em] text-slate-300">
        <Info size={12} /> Data quality note{compact ? "" : ` · ${n.title}`}
      </div>
      <p className="mt-0.5 text-slate-200/90">{n.text}</p>
      {n.by_hazard && typeof n.by_hazard === "object" ? (
        <p className="mt-0.5 text-[11.5px] text-muted" data-testid="dq-by-hazard">
          Hill-terrain districts in each count: {Object.entries(n.by_hazard as Record<string, number>).map(([h, k]) => `${h} ${k}`).join(" · ")}.
        </p>
      ) : null}
    </aside>
  );
}

export function DataQualityNotices({ list, className = "" }: { list: V2Notice[]; className?: string }) {
  if (!list.length) return null;
  return <div className={`space-y-2 ${className}`}>{list.map((n, i) => <DataQualityNotice key={`${n.id}-${i}`} n={n} />)}</div>;
}
