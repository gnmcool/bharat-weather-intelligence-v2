// Display formatting only. These functions never change a value, only how it is written
// (rounding for display, units, IST dates). The CORE-vs-V2 comparison (tools/compare) relies on this.

export const TZ = "Asia/Kolkata";

/** Round for display; "—" for missing. */
export const num = (v: number | null | undefined, digits = 0) =>
  v === null || v === undefined || Number.isNaN(v) ? "—" : v.toFixed(digits);

export const signed = (v: number | null | undefined, digits = 1) =>
  v === null || v === undefined ? "—" : `${v > 0 ? "+" : v < 0 ? "−" : "±"}${Math.abs(v).toFixed(digits)}`;

/** CORE hourly/daily times are local IST without offset ("2026-09-27T21:00"); treat them as IST. */
const asIst = (t: string) => (/[zZ]|[+-]\d\d:?\d\d$/.test(t) ? new Date(t) : new Date(`${t.length === 10 ? `${t}T00:00` : t}+05:30`));

export const istTime = (t: string | null | undefined, opts: Intl.DateTimeFormatOptions = { hour: "numeric", minute: "2-digit" }) =>
  t ? asIst(t).toLocaleTimeString("en-IN", { timeZone: TZ, ...opts }) : "—";

export const istDay = (t: string | null | undefined, opts: Intl.DateTimeFormatOptions = { weekday: "short", day: "numeric", month: "short" }) =>
  t ? asIst(t).toLocaleDateString("en-IN", { timeZone: TZ, ...opts }) : "—";

export const istDateTime = (t: string | null | undefined) =>
  t ? `${asIst(t).toLocaleString("en-IN", { timeZone: TZ, day: "numeric", month: "short", hour: "numeric", minute: "2-digit" })} IST` : "—";

/** Model run label, e.g. "27 Sep 06Z (11:30 IST)". */
export const runLabel = (iso: string | null | undefined) => {
  if (!iso) return "—";
  const d = new Date(iso);
  const z = `${d.toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "UTC" })} ${String(d.getUTCHours()).padStart(2, "0")}Z`;
  return `${z} (${d.toLocaleTimeString("en-IN", { timeZone: TZ, hour: "numeric", minute: "2-digit" })} IST)`;
};

export const compass = (deg: number | null | undefined) => {
  if (deg === null || deg === undefined) return "";
  const d = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"];
  return d[Math.round(((deg % 360) + 360) % 360 / 22.5) % 16];
};

/** WMO weather code → short description (WMO 4677 groups as used by Open-Meteo). */
export const wmoText = (code: number | null | undefined): string => {
  if (code === null || code === undefined) return "—";
  if (code === 0) return "Clear";
  if (code <= 2) return "Partly cloudy";
  if (code === 3) return "Overcast";
  if (code === 45 || code === 48) return "Fog";
  if (code >= 51 && code <= 57) return "Drizzle";
  if (code >= 61 && code <= 67) return code >= 65 ? "Heavy rain" : "Rain";
  if (code >= 71 && code <= 77) return "Snow";
  if (code >= 80 && code <= 82) return code === 82 ? "Violent showers" : "Showers";
  if (code >= 95) return code === 95 ? "Thunderstorm" : "Thunderstorm with hail";
  return `Code ${code}`;
};

export const MODEL_NAME: Record<string, string> = { ecmwf_ifs025: "ECMWF", gfs_seamless: "GFS", icon_seamless: "ICON" };
