// Farmer site (#/kisan): one simple screen for farmers — language, district, then rain for today and the next
// three days plus any official warning. Reads CORE's public API only (dashboard, states, districts); no new rules.
import "@fontsource/hind-vadodara/gujarati-400.css";
import "@fontsource/hind-vadodara/gujarati-600.css";
import "@fontsource/hind-vadodara/gujarati-700.css";
import "@fontsource/hind/devanagari-400.css";
import "@fontsource/hind/devanagari-600.css";
import "@fontsource/hind/devanagari-700.css";
import "@fontsource/hind/latin-400.css";
import "@fontsource/hind/latin-600.css";
import "@fontsource/hind/latin-700.css";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { core } from "../core-api/client";
import type { CoreDashboard, CoreDistrict, CoreState } from "../core-api/types";
import { cached } from "../lib/useCore";
import { istToday, isStale, mmText, pickDays, pickWarnings, rainView, type KLang, type RainView, type WarningView } from "./rules";
import { districtName, GUJARAT_DISTRICTS, K, kLocale, stateName, type KText } from "./strings";

interface Place { lat: number; lon: number; district: string | null; state: string | null }

const store = {
  get<T>(k: string): T | null { try { const v = localStorage.getItem(k); return v ? (JSON.parse(v) as T) : null; } catch { return null; } },
  set(k: string, v: unknown) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* this visit only */ } },
};
const LANG_KEY = "bwi2.kisan.lang";
const PLACE_KEY = "bwi2.kisan.place";
const FONT: Record<KLang, string> = {
  gu: "'Hind Vadodara', 'Noto Sans Gujarati', 'Shruti', sans-serif",
  hi: "'Hind', 'Noto Sans Devanagari', 'Mangal', sans-serif",
  en: "'Hind', 'Segoe UI', system-ui, sans-serif",
};

export default function KisanApp() {
  const [lang, setLangState] = useState<KLang | null>(() => store.get<KLang>(LANG_KEY));
  const [place, setPlaceState] = useState<Place | null>(() => store.get<Place>(PLACE_KEY));
  const [screen, setScreen] = useState<"lang" | "place" | "home">(() => (!lang ? "lang" : !place ? "place" : "home"));
  const l = lang ?? "gu";
  const t = K[l];

  useEffect(() => {
    document.documentElement.lang = l;
    document.title = l === "gu" ? "ખેડૂત હવામાન · BWI" : l === "hi" ? "किसान मौसम · BWI" : "Farmer weather · BWI";
    const prev = document.body.style.background;
    document.body.style.background = "#f3f6f1";
    return () => { document.body.style.background = prev; };
  }, [l]);

  const setLang = (v: KLang) => { store.set(LANG_KEY, v); setLangState(v); setScreen(place ? "home" : "place"); };
  const setPlace = (p: Place) => { store.set(PLACE_KEY, p); setPlaceState(p); setScreen("home"); };

  return (
    <div lang={l} style={{ fontFamily: FONT[l] }} className="min-h-screen bg-[#f3f6f1] text-[#13221a]">
      <div className="mx-auto flex min-h-screen max-w-[480px] flex-col px-4 pb-8 pt-[max(16px,env(safe-area-inset-top))]">
        {screen === "lang" && <LangScreen onPick={setLang} />}
        {screen === "place" && <PlaceScreen t={t} l={l} onPick={setPlace} onLang={() => setScreen("lang")} hasPlace={!!place} onBack={() => setScreen("home")} />}
        {screen === "home" && place && <HomeScreen t={t} l={l} place={place} onChange={() => setScreen("place")} onLang={() => setScreen("lang")} onResolved={(p) => store.set(PLACE_KEY, p)} />}
      </div>
    </div>
  );
}

// ── Language ─────────────────────────────────────────────────────────────────

function LangScreen({ onPick }: { onPick: (l: KLang) => void }) {
  const btn = "h-[72px] rounded-2xl border-2 border-[#1d6b45] text-[28px] font-semibold";
  return (
    <main className="flex flex-1 flex-col justify-center gap-7 py-6">
      <div className="flex flex-col items-center gap-3">
        <SunCloudIcon className="h-[72px] w-[72px] text-[#1d6b45]" />
        <h1 className="text-center text-[30px] font-bold leading-tight" style={{ fontFamily: FONT.gu }}>
          <span lang="gu">હવામાન</span> · <span lang="hi" style={{ fontFamily: FONT.hi }}>मौसम</span> · <span lang="en" style={{ fontFamily: FONT.en }}>Weather</span>
        </h1>
      </div>
      <p className="text-center text-[20px] leading-relaxed text-[#3d4f44]">
        <span lang="gu" style={{ fontFamily: FONT.gu }}>{K.gu.chooseLang}</span><br />
        <span lang="hi" style={{ fontFamily: FONT.hi }}>{K.hi.chooseLang}</span><br />
        <span lang="en" style={{ fontFamily: FONT.en }}>{K.en.chooseLang}</span>
      </p>
      <div className="flex flex-col gap-3.5">
        <button type="button" lang="gu" onClick={() => onPick("gu")} className={`${btn} bg-[#1d6b45] text-white`} style={{ fontFamily: FONT.gu }}>ગુજરાતી</button>
        <button type="button" lang="hi" onClick={() => onPick("hi")} className={`${btn} bg-white`} style={{ fontFamily: FONT.hi }}>हिन्दी</button>
        <button type="button" lang="en" onClick={() => onPick("en")} className={`${btn} bg-white`} style={{ fontFamily: FONT.en }}>English</button>
      </div>
    </main>
  );
}

// ── District ─────────────────────────────────────────────────────────────────

function PlaceScreen({ t, l, onPick, onLang, hasPlace, onBack }: { t: KText; l: KLang; onPick: (p: Place) => void; onLang: () => void; hasPlace: boolean; onBack: () => void }) {
  const [states, setStates] = useState<CoreState[] | null>(null);
  const [slug, setSlug] = useState("gujarat");
  const [districts, setDistricts] = useState<CoreDistrict[] | null>(null);
  const [q, setQ] = useState("");
  const [geo, setGeo] = useState<"idle" | "busy" | "failed">("idle");
  const [loadErr, setLoadErr] = useState(false);

  useEffect(() => { cached("states", core.states).then(setStates).catch(() => setLoadErr(true)); }, []);
  useEffect(() => {
    setDistricts(null);
    cached(`districts:${slug}`, () => core.districts(slug)).then(setDistricts).catch(() => setLoadErr(true));
  }, [slug]);
  const stateEn = states?.find((s) => s.state_slug === slug)?.state ?? (slug === "gujarat" ? "Gujarat" : null);

  const shown = useMemo(() => {
    const needle = q.trim().toLowerCase();
    const list = (districts ?? []).map((d) => ({ d, label: districtName(d.district, l) }));
    list.sort((a, b) => a.label.localeCompare(b.label, kLocale(l)));
    if (!needle) return list;
    return list.filter(({ d, label }) => label.toLowerCase().includes(needle) || d.district.toLowerCase().includes(needle)
      || Object.values(GUJARAT_DISTRICTS[d.district] ?? {}).some((n) => n.includes(q.trim())));
  }, [districts, q, l]);

  const locate = () => {
    if (!navigator.geolocation) { setGeo("failed"); return; }
    setGeo("busy");
    navigator.geolocation.getCurrentPosition(
      (pos) => { setGeo("idle"); onPick({ lat: +pos.coords.latitude.toFixed(4), lon: +pos.coords.longitude.toFixed(4), district: null, state: null }); },
      () => setGeo("failed"),
      { enableHighAccuracy: false, timeout: 15000, maximumAge: 600000 },
    );
  };

  return (
    <main className="flex flex-col gap-5 py-2">
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-[28px] font-bold leading-tight">{t.pickPlace}</h1>
        <div className="flex shrink-0 gap-2">
          {hasPlace && <Pill onClick={onBack}>←</Pill>}
          <Pill onClick={onLang} label={t.langLabel}>{t.langShort}</Pill>
        </div>
      </div>
      <button type="button" onClick={locate} disabled={geo === "busy"}
        className="flex h-16 items-center justify-center gap-2.5 rounded-2xl border-2 border-[#1f6fb2] bg-[#e6f0f9] text-[21px] font-semibold text-[#12466f] disabled:opacity-60">
        <PinIcon className="h-7 w-7" />{geo === "busy" ? t.locating : t.useLocation}
      </button>
      {geo === "failed" && <p role="alert" className="rounded-xl bg-[#fff1e0] px-4 py-3 text-[17px] text-[#6b3200]">{t.locationFailed}</p>}

      <div className="flex flex-col gap-2">
        <span className="text-[17px] text-[#3d4f44]">{t.orPick}</span>
        <label className="flex flex-col gap-1 text-[15px] text-[#3d4f44]" htmlFor="k-state">{t.state}
          <select id="k-state" value={slug} onChange={(e) => { setSlug(e.target.value); setQ(""); }}
            className="h-14 rounded-xl border-[1.5px] border-[#9fb0a5] bg-white px-3 text-[19px] text-[#13221a]">
            {(states ?? [{ state: "Gujarat", state_slug: "gujarat", n_districts: 34 }]).map((s) => <option key={s.state_slug} value={s.state_slug}>{stateName(s.state, l)}</option>)}
          </select>
        </label>
        <input id="k-search" type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder={t.searchPh} aria-label={t.searchPh}
          className="h-14 rounded-xl border-[1.5px] border-[#9fb0a5] bg-white px-4 text-[19px] text-[#13221a] placeholder:text-[#6b7b70]" />
      </div>

      {loadErr && <p role="alert" className="rounded-xl bg-[#fff1e0] px-4 py-3 text-[17px] text-[#6b3200]">{t.failed}</p>}
      {!districts && !loadErr && <p className="text-[18px] text-[#3d4f44]">{t.loading}</p>}
      {districts && (
        <div className="grid grid-cols-2 gap-2.5">
          {shown.map(({ d, label }) => (
            <button key={d.id} type="button" onClick={() => onPick({ lat: d.lat, lon: d.lon, district: d.district, state: stateEn })}
              className="min-h-[60px] rounded-xl border-[1.5px] border-[#c9d4cc] bg-white px-3 py-2 text-left text-[20px] font-semibold leading-tight">
              {label}
            </button>
          ))}
          {!shown.length && <p className="col-span-2 text-[18px] text-[#3d4f44]">{t.noMatch}</p>}
        </div>
      )}
    </main>
  );
}

// ── Weather ──────────────────────────────────────────────────────────────────

function HomeScreen({ t, l, place, onChange, onLang, onResolved }: { t: KText; l: KLang; place: Place; onChange: () => void; onLang: () => void; onResolved: (p: Place) => void }) {
  const [attempt, setAttempt] = useState(0);
  const [s, setS] = useState<{ state: "loading" } | { state: "ok"; d: CoreDashboard } | { state: "error" }>({ state: "loading" });
  useEffect(() => {
    let live = true;
    setS({ state: "loading" });
    const key = `kisan:${place.lat},${place.lon}:${attempt}`;
    cached(key, () => core.dashboard(place.lat, place.lon, place.district ?? undefined))
      .then((d) => {
        if (!live) return;
        setS({ state: "ok", d });
        if (!place.district && d.location.district) onResolved({ ...place, district: d.location.district, state: d.location.state });
      })
      .catch(() => live && setS({ state: "error" }));
    return () => { live = false; };
  }, [place.lat, place.lon, attempt]); // eslint-disable-line react-hooks/exhaustive-deps

  const districtEn = place.district ?? (s.state === "ok" ? s.d.location.district : null);
  const stateEn = place.state ?? (s.state === "ok" ? s.d.location.state : null);
  const title = districtEn ? districtName(districtEn, l) : (s.state === "ok" ? s.d.location.name : "…");

  return (
    <main className="flex flex-col gap-4">
      <header className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-[28px] font-bold leading-tight">{title}</h1>
          {stateEn && <p className="text-[15px] text-[#4b5e52]">{stateName(stateEn, l)}</p>}
        </div>
        <div className="flex shrink-0 gap-2">
          <Pill onClick={onChange}>{t.change}</Pill>
          <Pill onClick={onLang} label={t.langLabel}>{t.langShort}</Pill>
        </div>
      </header>

      {s.state === "loading" && (
        <div aria-busy="true" className="flex flex-col gap-4">
          <div className="h-[190px] animate-pulse rounded-3xl bg-[#dfe7e1]" />
          <div className="grid grid-cols-3 gap-2"><div className="h-[150px] animate-pulse rounded-2xl bg-[#dfe7e1]" /><div className="h-[150px] animate-pulse rounded-2xl bg-[#dfe7e1]" /><div className="h-[150px] animate-pulse rounded-2xl bg-[#dfe7e1]" /></div>
          <p className="text-[18px] text-[#3d4f44]">{t.loading}</p>
        </div>
      )}
      {s.state === "error" && (
        <div role="alert" className="flex flex-col gap-3 rounded-2xl bg-[#fff1e0] p-4">
          <p className="text-[19px] text-[#6b3200]">{t.failed}</p>
          <button type="button" onClick={() => setAttempt((a) => a + 1)} className="h-14 rounded-xl bg-[#1d6b45] text-[20px] font-semibold text-white">{t.retry}</button>
        </div>
      )}
      {s.state === "ok" && <Weather t={t} l={l} d={s.d} />}
    </main>
  );
}

function Weather({ t, l, d }: { t: KText; l: KLang; d: CoreDashboard }) {
  const [now] = useState(() => new Date());
  const days = pickDays(d.daily, istToday(now));
  const fmtTime = (iso: string) => new Date(iso).toLocaleString(kLocale(l), { timeZone: "Asia/Kolkata", day: "numeric", month: "short", hour: "numeric", minute: "2-digit" });
  const weekday = (date: string) => new Date(`${date}T12:00:00+05:30`).toLocaleDateString(kLocale(l), { timeZone: "Asia/Kolkata", weekday: "short" });
  const w = pickWarnings(d.warnings, now);

  return (
    <>
      {isStale(d.generated_at, now) && <p role="status" className="rounded-xl bg-[#fff1e0] px-4 py-3 text-[17px] text-[#6b3200]">{t.stale}</p>}
      {!days.length ? (
        <p className="rounded-2xl bg-white p-4 text-[19px]">{t.noDays}</p>
      ) : (
        <>
          <TodayCard t={t} r={rainView(days[0].precipitation_sum, days[0].precipitation_probability_max)} max={days[0].temperature_2m_max} min={days[0].temperature_2m_min} />
          <section aria-labelledby="k-next" className="flex flex-col gap-2">
            <h2 id="k-next" className="text-[19px] font-semibold">{t.next3}</h2>
            <div className="grid grid-cols-3 gap-2">
              {days.slice(1, 4).map((x) => {
                const r = rainView(x.precipitation_sum, x.precipitation_probability_max);
                return (
                  <div key={x.date} className="flex flex-col items-center gap-1 rounded-2xl border-[1.5px] border-[#d3ddd6] bg-white px-1.5 py-3 text-center">
                    <span className="text-[18px] font-semibold">{weekday(x.date)}</span>
                    <RainIcon kind={r.kind} className={`h-10 w-10 ${r.kind === "dry" ? "text-[#b86e00]" : "text-[#1f6fb2]"}`} />
                    <span className="text-[16px] leading-snug">{shortWord(t, r)}</span>
                    {r.prob !== null && <span className="text-[15px] text-[#4b5e52]">{t.chance(r.prob)}</span>}
                  </div>
                );
              })}
            </div>
          </section>
        </>
      )}

      <Warnings t={t} l={l} w={w} fmt={fmtTime} />

      <footer className="mt-2 flex flex-col gap-2 text-[16px] text-[#3d4f44]">
        <p>{t.notSure}</p>
        <p>{t.kcc} <a href="tel:18001801551" className="text-[19px] font-semibold text-[#13221a] underline" lang="en">1800-180-1551</a></p>
        <p className="text-[14px]">{t.updated(fmtTime(d.generated_at))}</p>
        <a href="#/home?mode=farmer" className="text-[16px] text-[#1d6b45] underline">{t.more}</a>
        <p className="text-[12.5px] text-[#5b6b60]">{t.attribution}</p>
      </footer>
    </>
  );
}

function headline(t: KText, r: RainView) {
  if (r.kind === "dry") return t.dry;
  if (r.kind === "smallChance") return t.smallChance;
  return `${t.rainOf[r.cls]} ${t.likely[r.lik === "likely" ? "likely" : "possible"]}`;
}
const shortWord = (t: KText, r: RainView) => (r.kind === "dry" ? t.dry : r.kind === "smallChance" ? t.smallChance : t.rainOf[r.cls]);

function TodayCard({ t, r, max, min }: { t: KText; r: RainView; max: number | null; min: number | null }) {
  const bg = r.kind === "dry" ? "bg-[#1d6b45]" : r.kind === "smallChance" ? "bg-[#2c5d6e]" : r.kind === "heavyRain" ? "bg-[#0f3557]" : "bg-[#164f7d]";
  const detail = [r.prob !== null ? t.chance(r.prob) : null, r.cls !== "none" && r.kind !== "smallChance" ? t.amount(mmText(r.mm)!) : null].filter(Boolean).join(" · ");
  return (
    <section aria-label={t.today} className={`flex flex-col gap-2 rounded-3xl p-5 text-white ${bg}`}>
      <span className="text-[18px] font-semibold opacity-90">{t.today}</span>
      <div className="flex items-center gap-4">
        <RainIcon kind={r.kind} className="h-[84px] w-[84px] shrink-0" />
        <div className="min-w-0">
          <p className="text-[30px] font-bold leading-tight">{headline(t, r)}</p>
          {detail && <p className="text-[19px]">{detail}</p>}
        </div>
      </div>
      {max !== null && min !== null && <p className="text-[17px] opacity-95">{t.maxMin(String(Math.round(max)), String(Math.round(min)))}</p>}
      {r.kind === "heavyRain" && <p className="rounded-xl bg-white/15 px-3 py-2 text-[16px]">{t.heavyNote}</p>}
    </section>
  );
}

function Warnings({ t, l, w, fmt }: { t: KText; l: KLang; w: { own: WarningView[]; state: WarningView[] }; fmt: (iso: string) => string }) {
  const [all, setAll] = useState(false);
  return (
    <section className="flex flex-col gap-2.5">
      {w.own.length === 0 ? (
        <div className="flex items-center gap-2.5 rounded-2xl bg-[#e5f2ea] px-4 py-3">
          <CheckIcon className="h-7 w-7 shrink-0 text-[#1d6b45]" />
          <span className="text-[18px] font-semibold text-[#14502f]">{t.noWarning}</span>
        </div>
      ) : (
        w.own.map((x) => <WarningCard key={x.id} t={t} l={l} x={x} fmt={fmt} heading={t.warnOwn} />)
      )}
      {w.state.length > 0 && (
        <div className="flex flex-col gap-2 rounded-2xl border-[1.5px] border-[#e2c9a8] bg-white px-4 py-3">
          <div className="flex items-center justify-between gap-3">
            <span className="text-[16px] text-[#4a3520]">{t.warnState(w.state.length)}</span>
            <button type="button" onClick={() => setAll((v) => !v)} aria-expanded={all} className="min-h-[44px] shrink-0 text-[16px] text-[#8a3f00] underline">{t.showAll}</button>
          </div>
          {all && w.state.map((x) => <WarningCard key={x.id} t={t} l={l} x={x} fmt={fmt} compact />)}
        </div>
      )}
    </section>
  );
}

function WarningCard({ t, l, x, fmt, heading, compact }: { t: KText; l: KLang; x: WarningView; fmt: (iso: string) => string; heading?: string; compact?: boolean }) {
  const [orig, setOrig] = useState(false);
  const type = x.key ? t.events[x.key] : x.event || x.headline;
  const sev = x.severity ? t.severity[x.severity] ?? x.severity : null;
  return (
    <article className={`flex flex-col gap-1 rounded-2xl ${compact ? "border border-[#ead7bf] bg-[#fffaf3] p-3" : "border-2 border-[#c25e00] bg-[#fff1e0] p-4"}`}>
      {heading && <span className="text-[15px] font-bold tracking-wide text-[#8a3f00]">{heading}</span>}
      <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
        <span className={`${compact ? "text-[18px]" : "text-[22px]"} font-bold leading-snug`} lang={x.key ? l : "en"}>{type}</span>
        {sev && <span className="rounded-md bg-[#8a3f00] px-2 py-0.5 text-[14px] font-semibold text-white">{sev}</span>}
      </div>
      {x.expires && <span className="text-[16px] text-[#4a3520]">{t.until(fmt(x.expires))}</span>}
      {compact && x.area && <span className="text-[14px] text-[#4a3520]" lang="en">{x.area}</span>}
      <span className="text-[14px] text-[#4a3520]">{t.issuedBy(x.sender || x.issuer)}</span>
      <button type="button" onClick={() => setOrig((v) => !v)} aria-expanded={orig} className="min-h-[44px] self-start text-[15px] text-[#8a3f00] underline">{orig ? t.hideOriginal : t.original}</button>
      {orig && <p lang="en" className="text-[15px] leading-relaxed text-[#3a2a1a]" style={{ fontFamily: FONT.en }}>{x.headline}</p>}
    </article>
  );
}

// ── Small parts ──────────────────────────────────────────────────────────────

function Pill({ onClick, children, label }: { onClick: () => void; children: ReactNode; label?: string }) {
  return <button type="button" onClick={onClick} aria-label={label} className="h-11 rounded-full border-[1.5px] border-[#9fb0a5] bg-white px-4 text-[16px] font-semibold">{children}</button>;
}

function RainIcon({ kind, className }: { kind: RainView["kind"]; className?: string }) {
  if (kind === "dry") return <SunIcon className={className} />;
  const cloud = <path d="M14 30h22a8 8 0 0 0 0-16 11 11 0 0 0-21 3 7 7 0 0 0-1 13z" />;
  return (
    <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth={2.6} strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      {cloud}
      {kind === "smallChance" && <path d="M24 36l-1.5 4" />}
      {kind === "rain" && <path d="M17 35l-2 5M25 35l-2 5M33 35l-2 5" />}
      {kind === "heavyRain" && <path d="M15 34l-2.5 7M21 34l-2.5 7M27 34l-2.5 7M33 34l-2.5 7" strokeWidth={3} />}
    </svg>
  );
}
function SunIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth={2.6} strokeLinecap="round" className={className} aria-hidden="true">
      <circle cx="24" cy="24" r="9" /><path d="M24 6v4M24 38v4M6 24h4M38 24h4M11.3 11.3l2.8 2.8M33.9 33.9l2.8 2.8M36.7 11.3l-2.8 2.8M14.1 33.9l-2.8 2.8" />
    </svg>
  );
}
function SunCloudIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      <circle cx="18" cy="18" r="7" /><path d="M18 4v3M18 29v3M4 18h3M29 18h3M8 8l2 2M28 8l-2 2" /><path d="M24 40h14a7 7 0 0 0 0-14 9 9 0 0 0-17 3 6 6 0 0 0 3 11z" fill="#f3f6f1" />
    </svg>
  );
}
function PinIcon({ className }: { className?: string }) {
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true"><path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z" /><circle cx="12" cy="9.5" r="2.5" /></svg>;
}
function CheckIcon({ className }: { className?: string }) {
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.6} strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M8 12.5l2.7 2.7L16 9.8" /></svg>;
}
