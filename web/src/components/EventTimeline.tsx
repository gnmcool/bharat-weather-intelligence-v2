import { istDay } from "../lib/format";
import { LEVEL } from "../lib/present";
import type { V2Event } from "../v2-api/types";
import { LEVEL_FILL } from "../modes/levelColors";

const DAY = 86400e3;
const IST = 5.5 * 3600e3;

/** WHEN: each event's CORE period on a 7-day IST axis. Events CORE gives no period for are listed, not drawn. */
export function EventTimeline({ events }: { events: V2Event[] }) {
  if (!events.length) return null;
  const today = Math.floor((Date.now() + IST) / DAY) * DAY - IST; // IST midnight today, as UTC ms
  const end = today + 7 * DAY;
  const timed = events.filter((e) => e.start && e.end);
  const untimed = events.filter((e) => !(e.start && e.end));
  const pct = (t: number) => `${Math.max(0, Math.min(100, ((t - today) / (end - today)) * 100))}%`;
  return (
    <div data-testid="event-timeline">
      <div className="grid grid-cols-7 text-center text-[10.5px] text-muted">
        {Array.from({ length: 7 }).map((_, i) => <div key={i} className="border-l border-line first:border-l-0">{istDay(new Date(today + i * DAY + IST).toISOString().slice(0, 10), { weekday: "short", day: "numeric" })}</div>)}
      </div>
      <div className="mt-1 space-y-1">
        {timed.map((e) => {
          const s = Date.parse(e.start!), f = Date.parse(e.end!);
          return (
            <div key={e.id} className="relative h-5 rounded bg-surface" data-testid="timeline-bar" data-event-type={e.type}>
              <div className="absolute inset-y-0 rounded" style={{ left: pct(s), width: `calc(${pct(Math.min(f, end))} - ${pct(s)})`, minWidth: 4, background: LEVEL_FILL[e.severity.level], opacity: 0.85 }} />
              <span className="absolute inset-y-0 left-1.5 flex items-center text-[11px] font-medium text-bg mix-blend-normal" style={{ left: `calc(${pct(s)} + 4px)` }}>
                <span className="rounded bg-bg/70 px-1 text-text">{e.title} · {LEVEL[e.severity.level].name}</span>
              </span>
            </div>
          );
        })}
      </div>
      {untimed.length > 0 && <p className="mt-1 text-[11.5px] text-muted">No period from CORE: {untimed.map((e) => `${e.title} (${e.severity.status})`).join(", ")} — see headline.</p>}
      <p className="mt-1 text-[11px] text-muted">System assessments only; bars show CORE's risk period (IST).</p>
    </div>
  );
}
