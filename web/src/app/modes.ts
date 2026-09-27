export type Mode = "citizen" | "farmer" | "government";
export type Screen = "home" | "map" | "risks" | "forecast" | "insights";

export const MODES: { id: Mode; label: string }[] = [
  { id: "citizen", label: "Citizen" },
  { id: "farmer", label: "Farmer" },
  { id: "government", label: "Government" },
];

// Five destinations (audit decision: Satellite folds into Map layers + evidence; Alerts into Risks)
export const SCREENS: { id: Screen; label: string; milestone: string; what: string }[] = [
  { id: "home", label: "Home", milestone: "M1–M2", what: "Current weather, What should you know?, 3-day outlook" },
  { id: "map", label: "Map", milestone: "M1", what: "Weather layers, satellite, timeline, tap any point" },
  { id: "risks", label: "Risks & alerts", milestone: "M2", what: "System assessments with evidence; official alerts kept separate" },
  { id: "forecast", label: "Forecast", milestone: "M1", what: "Hourly and 10-day forecast with model range" },
  { id: "insights", label: "Insights", milestone: "M2–M4", what: "Weather vs normal, season so far, forecast verification" },
];
