import { LocateFixed, MapPin, Search, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { core } from "../core-api/client";
import type { CoreGeoResult } from "../core-api/types";
import { useApp, type Place } from "../lib/store";

/** Current place + change control (search via CORE /geo/search, or GPS). */
export default function LocationPicker({ compact }: { compact?: boolean }) {
  const { place, setPlace } = useApp();
  const [open, setOpen] = useState(false);
  return (
    <div className="relative flex justify-end">
      <button onClick={() => setOpen(!open)} aria-expanded={open}
        className={`flex max-w-full items-center gap-1.5 rounded-lg border border-line bg-surface px-2.5 text-left hover:border-accent/60 ${compact ? "h-9" : "h-10"}`}>
        <MapPin size={15} className="shrink-0 text-accent" />
        <span className="truncate text-[13.5px] font-medium" data-testid="place-name">{place.name}</span>
        {(place.district || place.state) && <span className="hidden truncate text-[12px] text-muted sm:inline">{[place.district, place.state].filter(Boolean).join(", ")}</span>}
      </button>
      {open && <Picker onPick={(p) => { setPlace(p); setOpen(false); }} onClose={() => setOpen(false)} />}
    </div>
  );
}

function Picker({ onPick, onClose }: { onPick: (p: Place) => void; onClose: () => void }) {
  const [q, setQ] = useState("");
  const [res, setRes] = useState<CoreGeoResult[]>([]);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [active, setActive] = useState(0);
  const box = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const h = (e: MouseEvent) => !box.current?.contains(e.target as Node) && onClose();
    const k = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("mousedown", h);
    document.addEventListener("keydown", k);
    return () => { document.removeEventListener("mousedown", h); document.removeEventListener("keydown", k); };
  }, [onClose]);

  useEffect(() => {
    if (q.trim().length < 2) { setRes([]); return; }
    const ac = new AbortController();
    const t = setTimeout(() => {
      setBusy(true);
      core.search(q.trim(), ac.signal).then((r) => { setRes(r); setActive(0); setMsg(r.length ? null : "No places found in India for that name."); })
        .catch(() => !ac.signal.aborted && setMsg("Search is unavailable right now (CORE /geo/search)."))
        .finally(() => setBusy(false));
    }, 250);
    return () => { clearTimeout(t); ac.abort(); };
  }, [q]);

  const pick = (r: CoreGeoResult) => onPick({ name: r.name, lat: r.lat, lon: r.lon, taluka: r.taluka, district: r.district, state: r.state, via: "search" });

  const gps = () => {
    if (!window.isSecureContext || !navigator.geolocation) { setMsg("This browser only shares location on secure (https) pages."); return; }
    setMsg("Finding your location…");
    navigator.geolocation.getCurrentPosition(
      (p) => onPick({ name: "My location", lat: +p.coords.latitude.toFixed(4), lon: +p.coords.longitude.toFixed(4), via: "gps" }),
      (e) => setMsg(e.code === 1 ? "Location permission was denied. Search for your place instead." : "Could not get your location. Search for your place instead."),
      { timeout: 12000, maximumAge: 600000 },
    );
  };

  return (
    <div ref={box} className="absolute right-0 top-full z-50 mt-2 w-[min(92vw,380px)] rounded-xl border border-line bg-surface p-2 shadow-2xl">
      <div className="flex items-center gap-2 rounded-lg border border-line bg-bg px-2.5 focus-within:border-accent">
        <Search size={15} className="text-muted" />
        <input autoFocus value={q} onChange={(e) => setQ(e.target.value)} enterKeyHint="search" aria-label="Search a place"
          placeholder="City, taluka or village" className="h-10 w-full bg-transparent text-[14px] outline-none placeholder:text-muted"
          onKeyDown={(e) => {
            if (e.key === "ArrowDown") { e.preventDefault(); setActive((a) => Math.min(res.length - 1, a + 1)); }
            if (e.key === "ArrowUp") { e.preventDefault(); setActive((a) => Math.max(0, a - 1)); }
            if (e.key === "Enter" && res[active]) pick(res[active]);
          }} />
        {busy ? <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-accent border-t-transparent" /> : q && <button onClick={() => setQ("")} aria-label="Clear"><X size={14} className="text-muted" /></button>}
      </div>
      <button onClick={gps} className="mt-1 flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-[13px] text-accent hover:bg-surface-2">
        <LocateFixed size={15} /> Use my location
      </button>
      {msg && <div className="px-2.5 py-1.5 text-[12px] text-muted">{msg}</div>}
      <ul role="listbox" className="max-h-72 overflow-auto">
        {res.map((r, i) => (
          <li key={`${r.lat},${r.lon}`}>
            <button role="option" aria-selected={i === active} onMouseEnter={() => setActive(i)} onClick={() => pick(r)}
              className={`w-full rounded-lg px-2.5 py-2 text-left ${i === active ? "bg-surface-2" : ""}`}>
              <div className="text-[13.5px]">{r.name}</div>
              <div className="text-[11.5px] text-muted">{[r.taluka && r.taluka !== r.name ? `${r.taluka} taluka` : null, r.district, r.state].filter(Boolean).join(" · ")}</div>
            </button>
          </li>
        ))}
      </ul>
      <p className="px-2.5 pb-1 pt-2 text-[11px] text-muted">Forecasts for a taluka or village are point forecasts at model-grid resolution, not local measurements.</p>
    </div>
  );
}
