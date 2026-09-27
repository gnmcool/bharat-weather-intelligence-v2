import { Provenance } from "../components/ui";
import type { Mode } from "../lib/store";
import { useMedia } from "../lib/useMedia";
import { lazy, Suspense } from "react";
import FarmerWorkflow from "../modes/Farmer";
import GovernmentStateTable from "../modes/GovernmentStateTable";
import { CurrentWeather, ForecastPreview, InsightsPreview, Load, RiskSummary, RunLine, Section, useDashboard, WhatToKnow } from "./blocks";

const MapExplorer = lazy(() => import("../map/MapExplorer"));
const GovernmentIndiaLazy = lazy(() => import("../modes/Government"));

export default function Home({ mode }: { mode: Mode }) {
  if (mode === "government") {
    return (
      <div className="space-y-8">
        <Suspense fallback={<div className="h-96 animate-pulse rounded-xl bg-surface" />}><GovernmentIndiaLazy /></Suspense>
        <GovernmentStateTable title="State drill-down" />
      </div>
    );
  }
  return mode === "farmer" ? <FarmerHome /> : <CitizenHome />;
}

function CitizenHome() {
  const dash = useDashboard();
  const wide = useMedia("(min-width: 1024px)");
  const map = (
    <Suspense fallback={<div className="h-[420px] animate-pulse rounded-xl bg-surface" />}>
      <MapExplorer compact className={wide ? "h-[calc(100vh-150px)] min-h-[520px]" : "h-[420px]"} />
    </Suspense>
  );
  return (
    <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.05fr)]">
      <div className="space-y-6">
        <Load s={dash} lines={6}>
          {(d) => (
            <>
              <CurrentWeather d={d} />
              <Section title="What should you know?"><WhatToKnow d={d} /></Section>
              <Section title="Risks and alerts"><RiskSummary d={d} /></Section>
              <Section title="Forecast"><ForecastPreview d={d} /></Section>
              {!wide && <Section title="Map">{map}</Section>}
              <Section title="Weather vs normal"><InsightsPreview d={d} /></Section>
              <div className="space-y-2 border-t border-line pt-4"><RunLine d={d} /><Provenance sources={d.sources} /></div>
            </>
          )}
        </Load>
      </div>
      {wide && <div className="sticky top-[118px] self-start">{map}</div>}
    </div>
  );
}

function FarmerHome() {
  const dash = useDashboard();
  return (
    <div className="space-y-6">
      <Load s={dash} lines={4}>
        {(d) => (
          <>
            <CurrentWeather d={d} />
            <Section title="What should you know?"><WhatToKnow d={d} limit={2} /></Section>
          </>
        )}
      </Load>
      <FarmerWorkflow />
    </div>
  );
}
