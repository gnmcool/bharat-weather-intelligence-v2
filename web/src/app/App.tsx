import { useEffect, useState } from "react";
import { MODES, SCREENS, type Mode, type Screen } from "./modes";
import CoreStatus from "../pages/CoreStatus";

// V2 shell (milestone M0). Navigation, mode and routing only; screens arrive in M1+.
// Routing is hash-based (#/map?mode=farmer) so it works on GitHub Pages without server rewrites.

function readHash(): { screen: Screen; mode: Mode } {
  const [path, query] = location.hash.replace(/^#\/?/, "").split("?");
  const screen = (SCREENS.find((s) => s.id === path)?.id ?? "home") as Screen;
  const m = new URLSearchParams(query ?? "").get("mode");
  const mode = (MODES.find((x) => x.id === m)?.id ?? "citizen") as Mode;
  return { screen, mode };
}

export default function App() {
  const [{ screen, mode }, setRoute] = useState(readHash);
  useEffect(() => {
    const h = () => setRoute(readHash());
    window.addEventListener("hashchange", h);
    return () => window.removeEventListener("hashchange", h);
  }, []);
  const go = (s: Screen, m: Mode = mode) => {
    location.hash = `/${s}?mode=${m}`;
  };
  const current = SCREENS.find((s) => s.id === screen)!;

  return (
    <div className="mx-auto flex min-h-full max-w-6xl flex-col px-4 pb-10 sm:px-6">
      <div className="mt-3 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-[12.5px] text-amber-200">
        V2 preview (milestone M0) — work in progress, not for decisions. The live product remains{" "}
        <a className="underline" href="https://gnmcool.github.io/bharat-weather-intelligence/">Bharat Weather Intelligence</a>.
      </div>

      <header className="flex flex-wrap items-center gap-x-6 gap-y-3 py-5">
        <div className="flex items-center gap-3">
          <img src={`${import.meta.env.BASE_URL}favicon.svg`} alt="" className="h-9 w-9" />
          <div className="leading-tight">
            <div className="text-[17px] font-semibold tracking-tight">Bharat Weather Intelligence</div>
            <div className="text-[12px] text-muted">Weather. Impact. Decisions for a Safer, Stronger India.</div>
            <div className="text-[11px] text-muted">Made by <span className="font-medium text-text">Gaurav Makwana</span></div>
          </div>
        </div>
        <div role="radiogroup" aria-label="Mode" className="ml-auto flex rounded-lg border border-line bg-surface p-1">
          {MODES.map((m) => (
            <button key={m.id} role="radio" aria-checked={mode === m.id} onClick={() => go(screen, m.id)}
              className={`rounded-md px-3 py-1.5 text-[13px] font-medium transition-colors ${mode === m.id ? "bg-accent text-white" : "text-muted hover:text-text"}`}>
              {m.label}
            </button>
          ))}
        </div>
      </header>

      <nav aria-label="Primary" className="-mx-1 flex gap-1 overflow-x-auto border-b border-line pb-px">
        {SCREENS.map((s) => (
          <button key={s.id} onClick={() => go(s.id)} aria-current={screen === s.id ? "page" : undefined}
            className={`shrink-0 border-b-2 px-3 py-2 text-[13.5px] font-medium ${screen === s.id ? "border-accent text-text" : "border-transparent text-muted hover:text-text"}`}>
            {s.label}
          </button>
        ))}
      </nav>

      <main className="mt-6 grid gap-5 lg:grid-cols-[1fr_380px]">
        <section className="rounded-xl border border-line bg-surface p-5">
          <div className="text-[12px] uppercase tracking-wide text-muted">{MODES.find((m) => m.id === mode)!.label} · {current.label}</div>
          <h1 className="mt-1 text-[20px] font-semibold">{current.what}</h1>
          <p className="mt-3 max-w-prose text-[14px] leading-relaxed text-muted">
            This screen is planned for milestone {current.milestone}. It will be built on CORE's existing APIs; nothing
            shown in V2 will use mock data.
          </p>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <div className="rounded-lg border border-official/40 bg-official/10 p-3">
              <div className="text-[11px] font-semibold uppercase tracking-wide text-official">Official warning</div>
              <p className="mt-1 text-[13px] text-text">IMD, CWC, NDMA/SACHET, SDMA — shown verbatim, always in this style.</p>
            </div>
            <div className="rounded-lg border border-system/40 bg-system/10 p-3">
              <div className="text-[11px] font-semibold uppercase tracking-wide text-system">System assessment</div>
              <p className="mt-1 text-[13px] text-text">Bharat Weather Intelligence analysis — never presented as a warning.</p>
            </div>
          </div>
        </section>
        <CoreStatus />
      </main>
    </div>
  );
}
