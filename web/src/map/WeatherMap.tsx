import maplibregl, { type GeoJSONSource, type ImageSource, type Map as MLMap } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef, useState } from "react";
import { coreAsset } from "../core-api/client";
import type { CoreEoLayer, CoreGridField } from "../core-api/types";
import { renderField } from "./field";
import { type Palette } from "./palettes";

const STYLE = "https://tiles.openfreemap.org/styles/dark"; // OpenFreeMap (OpenStreetMap data), no key
const INDIA: [[number, number], [number, number]] = [[67.5, 6.5], [97.5, 36.5]];

export interface WeatherMapProps {
  field?: { data: CoreGridField; palette: Palette } | null;
  fieldOpacity?: number;
  /** district id -> CSS colour (government choropleth or official-alert overlay) */
  districtFill?: Record<string, string> | null;
  highlightState?: string | null;
  eo?: CoreEoLayer | null;
  fires?: GeoJSON.FeatureCollection | null;
  marker?: { lat: number; lon: number } | null;
  flyTo?: { lat: number; lon: number; zoom?: number } | null;
  onClick?: (lat: number, lon: number) => void;
  onDistrictClick?: (id: string, stateSlug: string, name: string) => void;
  className?: string;
  interactive?: boolean;
}

export default function WeatherMap(p: WeatherMapProps) {
  const el = useRef<HTMLDivElement>(null);
  const map = useRef<MLMap | null>(null);
  const markerRef = useRef<maplibregl.Marker | null>(null);
  const [ready, setReady] = useState(false);
  const cb = useRef(p);
  cb.current = p;

  useEffect(() => {
    const m = new maplibregl.Map({
      container: el.current!,
      style: STYLE,
      bounds: INDIA,
      fitBoundsOptions: { padding: 12 },
      attributionControl: false,
      dragRotate: false,
      pitchWithRotate: false,
      interactive: p.interactive !== false,
    });
    m.touchZoomRotate?.disableRotation();
    m.addControl(new maplibregl.AttributionControl({ compact: true }), "top-left");
    if (p.interactive !== false) m.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    map.current = m;
    m.on("load", () => {
      for (const l of m.getStyle().layers ?? []) if (l.id.includes("boundary")) m.setLayoutProperty(l.id, "visibility", "none");
      const firstSymbol = m.getStyle().layers?.find((l) => l.type === "symbol")?.id;
      m.addSource("field", { type: "image", url: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=", coordinates: [[0, 1], [1, 1], [1, 0], [0, 0]] });
      m.addLayer({ id: "field", type: "raster", source: "field", paint: { "raster-opacity": 0, "raster-resampling": "linear", "raster-fade-duration": 0 } }, firstSymbol);
      m.addSource("eo", { type: "raster", tiles: [], tileSize: 256, attribution: "NASA EOSDIS GIBS" });
      m.addLayer({ id: "eo", type: "raster", source: "eo", layout: { visibility: "none" }, paint: { "raster-opacity": 0.85 } }, firstSymbol);
      m.addSource("districts", { type: "geojson", data: coreAsset("geo/india_districts.geojson"), promoteId: "id" });
      m.addLayer({ id: "district-fill", type: "fill", source: "districts", paint: { "fill-color": ["coalesce", ["feature-state", "fill"], "rgba(0,0,0,0)"], "fill-opacity": 0.72 } }, firstSymbol);
      m.addLayer({ id: "district-line", type: "line", source: "districts", paint: { "line-color": "rgba(210,220,235,0.18)", "line-width": 0.5 } }, firstSymbol);
      m.addSource("states", { type: "geojson", data: coreAsset("geo/india_states.geojson") });
      m.addLayer({ id: "state-line", type: "line", source: "states", paint: { "line-color": "rgba(230,236,245,0.55)", "line-width": 0.9 } }, firstSymbol);
      m.addLayer({ id: "state-hl", type: "line", source: "states", filter: ["==", ["get", "state_slug"], ""], paint: { "line-color": "#3b9ae1", "line-width": 2.2 } }, firstSymbol);
      m.addSource("fires", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
      m.addLayer({ id: "fires", type: "circle", source: "fires", layout: { visibility: "none" },
        paint: { "circle-radius": ["interpolate", ["linear"], ["zoom"], 4, 2, 8, 4], "circle-color": ["interpolate", ["linear"], ["get", "frp"], 0, "#ffd166", 20, "#f77f00", 80, "#d62828"], "circle-stroke-color": "#1b1b1b", "circle-stroke-width": 0.5 } });
      m.on("click", (e) => {
        const f = m.queryRenderedFeatures(e.point, { layers: ["district-fill"] })[0];
        if (f && cb.current.onDistrictClick) cb.current.onDistrictClick(String(f.properties.id), String(f.properties.state_slug), String(f.properties.district));
        else cb.current.onClick?.(e.lngLat.lat, e.lngLat.lng);
      });
      setReady(true);
    });
    return () => m.remove();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // gridded field
  useEffect(() => {
    const m = map.current;
    if (!ready || !m) return;
    if (!p.field) { m.setPaintProperty("field", "raster-opacity", 0); return; }
    const { url, coords } = renderField(p.field.data, p.field.palette);
    (m.getSource("field") as ImageSource).updateImage({ url, coordinates: coords });
    m.setPaintProperty("field", "raster-opacity", p.fieldOpacity ?? 0.72);
  }, [ready, p.field, p.fieldOpacity]);

  // district fills (choropleth or official-alert overlay)
  const lastFill = useRef<string[]>([]);
  useEffect(() => {
    const m = map.current;
    if (!ready || !m) return;
    const apply = () => {
      for (const id of lastFill.current) m.removeFeatureState({ source: "districts", id });
      const ids = Object.keys(p.districtFill ?? {});
      for (const id of ids) m.setFeatureState({ source: "districts", id }, { fill: p.districtFill![id] });
      lastFill.current = ids;
    };
    if (m.isSourceLoaded("districts")) apply();
    else m.once("sourcedata", apply);
  }, [ready, p.districtFill]);

  useEffect(() => {
    const m = map.current;
    if (!ready || !m) return;
    m.setFilter("state-hl", ["==", ["get", "state_slug"], p.highlightState ?? ""]);
  }, [ready, p.highlightState]);

  // NASA GIBS imagery (tiles served by NASA, catalogue from CORE)
  useEffect(() => {
    const m = map.current;
    if (!ready || !m) return;
    if (!p.eo) { m.setLayoutProperty("eo", "visibility", "none"); return; }
    m.removeLayer("eo");
    m.removeSource("eo");
    m.addSource("eo", { type: "raster", tiles: [p.eo.tiles], tileSize: 256, maxzoom: p.eo.maxzoom, attribution: p.eo.attribution });
    m.addLayer({ id: "eo", type: "raster", source: "eo", paint: { "raster-opacity": p.eo.opacity } }, "district-fill");
  }, [ready, p.eo]);

  useEffect(() => {
    const m = map.current;
    if (!ready || !m) return;
    m.setLayoutProperty("fires", "visibility", p.fires ? "visible" : "none");
    if (p.fires) (m.getSource("fires") as GeoJSONSource).setData(p.fires);
  }, [ready, p.fires]);

  useEffect(() => {
    const m = map.current;
    if (!ready || !m) return;
    markerRef.current?.remove();
    if (p.marker) {
      const dot = document.createElement("div");
      dot.className = "h-3.5 w-3.5 rounded-full border-2 border-white bg-accent shadow";
      markerRef.current = new maplibregl.Marker({ element: dot }).setLngLat([p.marker.lon, p.marker.lat]).addTo(m);
    }
  }, [ready, p.marker?.lat, p.marker?.lon]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (ready && p.flyTo) map.current?.flyTo({ center: [p.flyTo.lon, p.flyTo.lat], zoom: p.flyTo.zoom ?? 6.5, duration: 800 });
  }, [ready, p.flyTo]);

  return <div ref={el} className={p.className} style={{ position: "relative" }} data-testid="weather-map" />;
}
