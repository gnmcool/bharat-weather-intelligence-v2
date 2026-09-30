"""36-point extraction, 30 km rule, IST-day aggregation and the gap report (D2 plan §5, §10.2).

Tables are deterministic functions of the two GRIB files and archive/points.json (no timestamps inside), so they can
be rebuilt byte-identically from a published release.
"""
from __future__ import annotations

import pathlib
from datetime import date

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from era5_common import ReferenceError_, ist_day_stamps, month_days, node_for
from era5_grib import grid_axes

HOURLY_SCHEMA = pa.schema([
    ("point_id", pa.string()), ("utc_time", pa.timestamp("s", tz="UTC")), ("precipitation_mm", pa.float64()),
    ("node_lat", pa.float64()), ("node_lon", pa.float64()), ("expver", pa.string()), ("source_request", pa.string()),
])
DAY_SCHEMA = pa.schema([
    ("point_id", pa.string()), ("ist_date", pa.date32()), ("precip_ist_day_mm", pa.float32()),
    ("hours_present", pa.int8()), ("reason", pa.string()), ("node_distance_km", pa.float64()),
    ("eligible", pa.bool_()),
])


def select_nodes(points: list[dict], decoded: dict) -> list[dict]:
    """Per point: the §5.2 node, its index in the decoded grid, distance, eligibility and tie-break flag.

    Refuses if a node is not present in the decoded grid (§5.2)."""
    lats, lons = grid_axes(decoded["messages"][0])
    ni = len(lons)
    out = []
    for p in points:
        n = node_for(p)
        j = np.where(np.abs(lats - float(n["node_lat"])) < 1e-6)[0]
        i = np.where(np.abs(lons - float(n["node_lon"])) < 1e-6)[0]
        if len(j) != 1 or len(i) != 1:
            raise ReferenceError_(f"[grid] node {n['node_lat']},{n['node_lon']} of {p['id']} is not in the decoded grid")
        out.append({**n, "index": int(j[0]) * ni + int(i[0])})
    return out


def hourly_table(nodes: list[dict], files: dict[str, dict]) -> pd.DataFrame:
    """One row per point and stamp, from both files (boundary first). Missing GRIB values stay null."""
    rows = []
    for node in nodes:
        for role in ("boundary", "month"):
            dec = files[role]
            col = dec["values"][:, node["index"]]
            for m, v in zip(dec["messages"], col):
                rows.append((node["point_id"], m["stamp"], None if np.isnan(v) else float(v) * 1000.0,
                             float(node["node_lat"]), float(node["node_lon"]), m.get("expver"), role))
    df = pd.DataFrame(rows, columns=[f.name for f in HOURLY_SCHEMA])
    order = {n["point_id"]: k for k, n in enumerate(nodes)}
    df["_o"] = df.point_id.map(order)
    return df.sort_values(["_o", "utc_time"], kind="stable").drop(columns="_o").reset_index(drop=True)


def day_values(nodes: list[dict], hourly: pd.DataFrame, month: str) -> tuple[pd.DataFrame, dict]:
    """IST-day values (§5.4-§5.6) and, per point-day, the float64 sum used for comparisons.

    G (node > 30 km) takes precedence over E (fewer than 24 non-missing hours); a null is never zero."""
    by_point = {pid: g.set_index("utc_time")["precipitation_mm"] for pid, g in hourly.groupby("point_id", sort=False)}
    rows, exact = [], {}
    for node in nodes:
        s = by_point[node["point_id"]]
        for d in month_days(month):
            stamps = [pd.Timestamp(t) for t in ist_day_stamps(d)]
            present = [s.get(t) for t in stamps if t in s.index]
            vals = [v for v in present if v is not None and not pd.isna(v)]
            hours = len(vals)
            total64 = float(np.sum(np.asarray(vals, dtype=np.float64))) if hours == 24 else None
            if not node["eligible"]:
                value, reason = None, "G"
            elif hours < 24:
                value, reason = None, "E"
            else:
                value, reason = float(np.float32(total64)), None
            exact[(node["point_id"], d)] = total64 if reason is None else None
            rows.append((node["point_id"], d, value, hours, reason, float(node["distance_km"]), bool(node["eligible"])))
    return pd.DataFrame(rows, columns=[f.name for f in DAY_SCHEMA]), exact


def gap_report(nodes: list[dict], hourly: pd.DataFrame, days: pd.DataFrame, month: str) -> dict:
    dd = days[days.reason.notna()]
    return {
        "month": month,
        "expected_hours_per_point": int(hourly.groupby("point_id").size().iloc[0]) if len(hourly) else 0,
        "present_hours": {pid: int(g.precipitation_mm.notna().sum()) for pid, g in hourly.groupby("point_id", sort=False)},
        "e_days": [{"point_id": r.point_id, "ist_date": str(r.ist_date), "hours_present": int(r.hours_present),
                    "reason": f"ERA5 hours missing: {int(r.hours_present)} of 24"}
                   for r in dd[dd.reason == "E"].itertuples()],
        "g_days": [{"point_id": r.point_id, "ist_date": str(r.ist_date), "reason": "ERA5 cell > 30 km",
                    "node_distance_km": round(float(r.node_distance_km), 3)} for r in dd[dd.reason == "G"].itertuples()],
        "negative_hourly_values": int((hourly.precipitation_mm < 0).sum()),
        "e_day_note": "E-days are excluded from M4.4-D verification metrics, never converted to zero and never "
                      "treated as forecast misses.",
    }


def write_table(df: pd.DataFrame, schema: pa.Schema, path: pathlib.Path) -> int:
    """Deterministic parquet (fixed schema, no pandas index, no statistics timestamps)."""
    t = pa.Table.from_pandas(df, schema=schema, preserve_index=False)
    pq.write_table(t, path, compression="zstd", write_statistics=False)
    return t.num_rows


def build_tables(points: list[dict], files: dict[str, dict], month: str, out: pathlib.Path) -> dict:
    """Extract, aggregate and write the hourly and IST-day tables for one validated retrieval."""
    nodes = select_nodes(points, files["month"])
    b_nodes = select_nodes(points, files["boundary"])
    if [n["index"] for n in nodes] != [n["index"] for n in b_nodes]:
        raise ReferenceError_("[grid] boundary and month files index the nodes differently")
    hourly = hourly_table(nodes, files)
    days, exact = day_values(nodes, hourly, month)
    out.mkdir(parents=True, exist_ok=True)
    h_rows = write_table(hourly, HOURLY_SCHEMA, out / f"era5_hourly_{month}.parquet")
    d_rows = write_table(days, DAY_SCHEMA, out / f"era5_ist_day_{month}.parquet")
    return {"nodes": nodes, "hourly": hourly, "days": days, "exact": exact, "hourly_rows": h_rows, "day_rows": d_rows,
            "gap": gap_report(nodes, hourly, days, month)}


def expected_day_rows(month: str, n_points: int) -> int:
    return len(month_days(month)) * n_points


def ist_dates(month: str) -> list[date]:
    return month_days(month)
