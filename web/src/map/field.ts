import type { CoreGridField } from "../core-api/types";
import { colorAt, type Palette } from "./palettes";

// Renders a CORE grid field (row-major, south→north rows) to an image for a MapLibre image source.
// Rows are resampled to Web Mercator spacing so cells sit at the right latitudes. Display only:
// no value is changed; the point readout (sample) uses the raw CORE values.

const mercY = (lat: number) => Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360));
const invMercY = (y: number) => (Math.atan(Math.exp(y)) * 360) / Math.PI - 90;

export function renderField(f: CoreGridField, p: Palette): { url: string; coords: [[number, number], [number, number], [number, number], [number, number]] } {
  const [w, s, e, n] = f.bbox;
  const H = f.ny * 2;
  const cv = document.createElement("canvas");
  cv.width = f.nx;
  cv.height = H;
  const ctx = cv.getContext("2d")!;
  const img = ctx.createImageData(f.nx, H);
  const yN = mercY(n);
  const yS = mercY(s);
  const dy = (n - s) / (f.ny - 1);
  for (let row = 0; row < H; row++) {
    const lat = invMercY(yN - ((row + 0.5) / H) * (yN - yS));
    const fy = (lat - s) / dy;
    const j0 = Math.max(0, Math.min(f.ny - 1, Math.floor(fy)));
    const j1 = Math.min(f.ny - 1, j0 + 1);
    const ty = Math.min(1, Math.max(0, fy - j0));
    for (let i = 0; i < f.nx; i++) {
      const a = f.values[j0 * f.nx + i];
      const b = f.values[j1 * f.nx + i];
      const k = (row * f.nx + i) * 4;
      if (a === null || b === null) { img.data[k + 3] = 0; continue; }
      const c = colorAt(p, a + (b - a) * ty);
      img.data[k] = c[0]; img.data[k + 1] = c[1]; img.data[k + 2] = c[2]; img.data[k + 3] = c[3];
    }
  }
  ctx.putImageData(img, 0, 0);
  return { url: cv.toDataURL("image/png"), coords: [[w, n], [e, n], [e, s], [w, s]] };
}

/** Bilinear value at a point from the raw CORE grid (null outside the grid). */
export function sample(f: CoreGridField, lat: number, lon: number): number | null {
  const [w, s, e, n] = f.bbox;
  if (lat < s || lat > n || lon < w || lon > e) return null;
  const fx = ((lon - w) / (e - w)) * (f.nx - 1);
  const fy = ((lat - s) / (n - s)) * (f.ny - 1);
  const i = Math.floor(fx), j = Math.floor(fy);
  const i1 = Math.min(f.nx - 1, i + 1), j1 = Math.min(f.ny - 1, j + 1);
  const g = (x: number, y: number) => f.values[y * f.nx + x];
  const q = [g(i, j), g(i1, j), g(i, j1), g(i1, j1)];
  if (q.some((x) => x === null)) return null;
  const tx = fx - i, ty = fy - j;
  const [a, b, c, d] = q as number[];
  return a * (1 - tx) * (1 - ty) + b * tx * (1 - ty) + c * (1 - tx) * ty + d * tx * ty;
}
