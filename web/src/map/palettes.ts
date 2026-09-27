// V2 colour scales for CORE grid variables. Stops are [value, [r,g,b]] in the variable's display unit.
export interface Palette {
  label: string;
  unit: string;
  stops: [number, [number, number, number]][];
  ticks: number[];
  /** values at or below this are drawn transparent (e.g. no rain) */
  clearBelow?: number;
}

export const PALETTES: Record<string, Palette> = {
  t2m: {
    label: "Temperature", unit: "°C", ticks: [0, 10, 20, 30, 40],
    stops: [[-10, [94, 60, 153]], [0, [59, 110, 190]], [10, [72, 169, 191]], [20, [120, 190, 120]], [26, [233, 212, 96]], [32, [240, 150, 60]], [38, [214, 72, 50]], [45, [140, 20, 40]]],
  },
  tp: {
    label: "Rain (3 h)", unit: "mm", ticks: [1, 5, 10, 20, 40], clearBelow: 0.2,
    stops: [[0.2, [150, 200, 240]], [1, [90, 160, 230]], [5, [40, 110, 210]], [10, [60, 70, 190]], [20, [140, 60, 190]], [40, [210, 60, 150]], [80, [240, 110, 110]]],
  },
  wind: {
    label: "Wind speed", unit: "km/h", ticks: [10, 20, 40, 60, 90],
    stops: [[0, [45, 70, 120]], [10, [50, 120, 170]], [20, [60, 170, 160]], [30, [150, 200, 90]], [45, [235, 200, 70]], [60, [235, 130, 60]], [90, [200, 60, 90]], [120, [150, 40, 150]]],
  },
  fg10m: {
    label: "Wind gust", unit: "km/h", ticks: [20, 40, 60, 90],
    stops: [[0, [45, 70, 120]], [20, [60, 150, 170]], [40, [150, 200, 90]], [60, [235, 170, 60]], [90, [210, 70, 80]], [130, [150, 40, 150]]],
  },
  r2m: {
    label: "Humidity", unit: "%", ticks: [20, 40, 60, 80, 100],
    stops: [[0, [150, 100, 60]], [30, [210, 180, 110]], [50, [160, 200, 150]], [70, [80, 170, 170]], [90, [50, 110, 190]], [100, [40, 70, 160]]],
  },
  msl: {
    label: "Pressure (sea level)", unit: "hPa", ticks: [995, 1000, 1005, 1010, 1015],
    stops: [[990, [120, 60, 160]], [998, [70, 110, 200]], [1004, [90, 170, 180]], [1008, [170, 200, 120]], [1012, [230, 190, 90]], [1020, [220, 110, 70]]],
  },
  tcc: {
    label: "Cloud cover", unit: "%", ticks: [20, 40, 60, 80, 100], clearBelow: 5,
    stops: [[5, [70, 80, 95]], [40, [130, 140, 155]], [70, [185, 192, 202]], [100, [235, 238, 242]]],
  },
  tcwv: {
    label: "Precipitable water", unit: "kg/m²", ticks: [10, 30, 50, 70],
    stops: [[0, [150, 110, 70]], [20, [200, 190, 120]], [40, [110, 190, 160]], [55, [60, 140, 200]], [70, [70, 70, 180]]],
  },
};

export function colorAt(p: Palette, v: number): [number, number, number, number] {
  if (p.clearBelow !== undefined && v < p.clearBelow) return [0, 0, 0, 0];
  const s = p.stops;
  if (v <= s[0][0]) return [...s[0][1], 255];
  for (let i = 1; i < s.length; i++) {
    if (v <= s[i][0]) {
      const [a, ca] = s[i - 1];
      const [b, cb] = s[i];
      const t = (v - a) / (b - a);
      return [ca[0] + (cb[0] - ca[0]) * t, ca[1] + (cb[1] - ca[1]) * t, ca[2] + (cb[2] - ca[2]) * t, 255];
    }
  }
  return [...s[s.length - 1][1], 255];
}

export const cssGradient = (p: Palette) => {
  const lo = p.stops[0][0];
  const hi = p.stops[p.stops.length - 1][0];
  return `linear-gradient(90deg, ${p.stops.map(([v, c]) => `rgb(${c.join(",")}) ${(((v - lo) / (hi - lo)) * 100).toFixed(1)}%`).join(", ")})`;
};

/** Choropleth scale for Government district statistics (existing CORE /region/india metrics). */
export const METRIC_PALETTE: Record<string, Palette> = {
  rain: { label: "Rainfall total", unit: "mm", ticks: [2.5, 15.6, 64.5, 115.6, 204.5], clearBelow: 0.1,
    stops: [[0.1, [70, 90, 120]], [2.5, [60, 120, 200]], [15.6, [50, 90, 210]], [64.5, [150, 60, 200]], [115.6, [220, 60, 120]], [204.5, [250, 200, 60]]] },
  tmax: PALETTES.t2m,
  tmin: PALETTES.t2m,
  gust: PALETTES.fg10m,
  rh: PALETTES.r2m,
};
