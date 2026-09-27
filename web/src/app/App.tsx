import { CalendarDays, Home as HomeIcon, Lightbulb, Map as MapIcon, ShieldAlert } from "lucide-react";
import { lazy, Suspense, useEffect } from "react";
import EvidenceDrawer from "../components/EvidenceDrawer";
import LocationPicker from "../components/LocationPicker";
import { config } from "../config";
import { MODES, navigate, SCREENS, useRoute } from "../lib/router";
import { useApp, type Screen } from "../lib/store";
import Home from "../pages/Home";
import RisksPage from "../pages/Risks";

// Heavier screens load on demand (map engine, charts)
const MapExplorer = lazy(() => import("../map/MapExplorer"));
const ForecastPage = lazy(() => import("../pages/Forecast"));
const InsightsPage = lazy(() => import("../pages/Insights"));
const Loading = () => <div className="h-40 animate-pulse rounded-xl bg-surface" aria-busy="true" />;

const ICON: Record<Screen, typeof HomeIcon> = { home: HomeIcon, map: MapIcon, risks: ShieldAlert, forecast: CalendarDays, insights: Lightbulb };

function ModeSwitch({ mode, className }: { mode: string; className: string }) {
  return (
    <div role="radiogroup" aria-label="Mode" className={`rounded-lg border border-line bg-surface p-0.5 ${className}`}>
      {MODES.map((m) => (
        <button key={m.id} role="radio" aria-checked={mode === m.id} onClick={() => navigate({ mode: m.id })}
          className={`flex-1 rounded-md px-3 py-1.5 text-[13px] font-medium sm:flex-none ${mode === m.id ? "bg-accent text-white" : "text-muted hover:text-text"}`}>{m.label}</button>
      ))}
    </div>
  );
}

export default function App() {
  const route = useRoute();
  const { setPlace } = useApp();
  const { screen, mode } = route;

  // A shared/tested link may carry an exact location: #/home?mode=citizen&lat=..&lon=..&name=..
  useEffect(() => {
    if (route.lat !== undefined && route.lon !== undefined) {
      setPlace({ name: route.name ?? `${route.lat.toFixed(3)}, ${route.lon.toFixed(3)}`, lat: route.lat, lon: route.lon, via: route.name ? "link" : "map" });
      navigate({ screen, mode }); // drop the coordinates from the address bar
    }
  }, [route.lat, route.lon]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="min-h-full pb-20 lg:pb-8">
      <header className="sticky top-0 z-40 border-b border-line bg-bg/95 backdrop-blur">
        <div className="mx-auto flex max-w-[1400px] items-center gap-3 px-4 py-2.5 sm:gap-5 sm:px-6">
          <a href="#/home" className="flex min-w-0 shrink items-center gap-2.5" onClick={(e) => { e.preventDefault(); navigate({ screen: "home" }); }}>
            <img src={`${import.meta.env.BASE_URL}favicon.svg`} alt="" className="h-8 w-8 shrink-0" />
            <span className="min-w-0 leading-tight">
              <span className="block truncate text-[15px] font-semibold tracking-tight">Bharat Weather Intelligence</span>
              <span className="block truncate text-[11px] text-muted">Made by Gaurav Makwana · V2 preview</span>
            </span>
          </a>
          <ModeSwitch mode={mode} className="hidden sm:flex" />
          <div className="ml-auto min-w-0 max-w-[45%] sm:max-w-none"><LocationPicker compact /></div>
        </div>
        <div className="px-4 pb-2 sm:hidden"><ModeSwitch mode={mode} className="flex w-full" /></div>
        <nav aria-label="Primary" className="mx-auto hidden max-w-[1400px] gap-1 px-4 sm:px-6 lg:flex">
          {SCREENS.map((s) => (
            <button key={s.id} onClick={() => navigate({ screen: s.id })} aria-current={screen === s.id ? "page" : undefined}
              className={`border-b-2 px-3 py-2 text-[13.5px] font-medium ${screen === s.id ? "border-accent text-text" : "border-transparent text-muted hover:text-text"}`}>{s.label}</button>
          ))}
        </nav>
      </header>

      <div className="mx-auto max-w-[1400px] px-4 pt-3 sm:px-6">
        <p className="text-[11.5px] text-amber-200/80">
          Preview of V2, built on the same data as <a className="underline" href={config.coreSite}>Bharat Weather Intelligence</a>. Official warnings come only from IMD, CWC and SDMAs; everything else is a system assessment.
        </p>
      </div>

      <main className="mx-auto max-w-[1400px] px-4 pt-4 sm:px-6">
        <Suspense fallback={<Loading />}>
          {screen === "home" && <Home mode={mode} />}
          {screen === "map" && <MapExplorer className="h-[calc(100vh-190px)] min-h-[480px]" />}
          {screen === "risks" && <RisksPage mode={mode} />}
          {screen === "forecast" && <ForecastPage mode={mode} />}
          {screen === "insights" && <InsightsPage mode={mode} />}
        </Suspense>
      </main>

      <EvidenceDrawer />

      {/* phone / tablet navigation */}
      <nav aria-label="Primary" className="fixed inset-x-0 bottom-0 z-40 grid grid-cols-5 border-t border-line bg-bg/95 pb-[env(safe-area-inset-bottom)] backdrop-blur lg:hidden">
        {SCREENS.map((s) => {
          const Icon = ICON[s.id];
          return (
            <button key={s.id} onClick={() => navigate({ screen: s.id })} aria-current={screen === s.id ? "page" : undefined}
              className={`flex flex-col items-center gap-0.5 py-2 text-[10.5px] ${screen === s.id ? "text-accent" : "text-muted"}`}>
              <Icon size={19} />{s.label.replace(" & alerts", "")}
            </button>
          );
        })}
      </nav>
    </div>
  );
}
