"""Historical verification dataset (M4.2): schemas, IST-day aggregation, validation and coverage reports.

Kept separate from the prospective immutable archive (`archive/`). Historical model values come from
Open-Meteo's Previous Runs API, which gives for every hourly valid time "the value predicted N x 24 h
before" WITHOUT the model run that produced it. Therefore every historical forecast row has
run_time_known = false, run_time_utc = null and a *nominal* lead (N). Nothing here fills, interpolates
or substitutes a missing value: a day with fewer than 24 hourly values keeps value = null.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

import pyarrow as pa

SCHEMA_VERSION = 1
HERE = pathlib.Path(__file__).resolve().parent
POINTS_FILE = HERE.parent / "archive" / "points.json"   # the same 36 fixed points as the prospective archive
LEADS = list(range(1, 8))                                # previous_day1 .. previous_day7

# hourly Open-Meteo variable -> daily variables built from it (variable, unit, aggregation, window)
HOURLY = {
    "temperature_2m": [("tmax", "degC", "max", "ist_day"), ("tmin", "degC", "min", "ist_day")],
    "precipitation": [("precip", "mm", "sum", "ist_day"), ("precip_0830", "mm", "sum", "imd_window")],
    "wind_gusts_10m": [("gust_max", "km/h", "max", "ist_day")],
    "cape": [("cape_max", "J/kg", "max", "ist_day")],
}
BACKFILL_HOURLY = ["temperature_2m", "precipitation", "wind_gusts_10m"]   # CAPE: availability only (no CAPE product)
PLAUSIBLE = {"tmax": (-60, 60), "tmin": (-60, 60), "precip": (0, 1500), "precip_0830": (0, 1500),
             "gust_max": (0, 400), "cape_max": (0, 10000), "wind_max": (0, 400), "vis_min": (0, 100)}

HIST_SCHEMA = pa.schema([
    ("dataset", pa.string()),                          # always "historical_backfill"
    ("point_id", pa.string()),
    ("lat", pa.float32()),
    ("lon", pa.float32()),
    ("model", pa.string()),                            # archive model name (same names as the prospective archive)
    ("om_model", pa.string()),                         # Open-Meteo model id actually requested
    ("source", pa.string()),
    ("source_url", pa.string()),
    ("run_time_utc", pa.timestamp("ms", tz="UTC")),    # always null: the run is not identified by the source
    ("run_time_known", pa.bool_()),                    # always false
    ("nominal_lead_day", pa.int16()),                  # N of previous_dayN
    ("lead_basis", pa.string()),
    ("valid_date_ist", pa.date32()),                   # IST calendar day (or IMD-window start day, see aggregation)
    ("variable", pa.string()),
    ("value", pa.float32()),                           # null unless complete
    ("unit", pa.string()),
    ("hours_expected", pa.int8()),
    ("hours_present", pa.int8()),
    ("complete", pa.bool_()),
    ("aggregation", pa.string()),
    ("retrieved_at_utc", pa.timestamp("ms", tz="UTC")),
])

REF_SCHEMA = pa.schema([
    ("dataset", pa.string()),                          # always "reference"
    ("reference", pa.string()),                        # era5 | metar | imd_rf025
    ("reference_type", pa.string()),                   # reanalysis | station_observation | gridded_gauge_analysis
    ("point_id", pa.string()),
    ("site_id", pa.string()),                          # METAR ICAO, IMD cell "lat,lon", ERA5 "grid"
    ("site_lat", pa.float32()),
    ("site_lon", pa.float32()),
    ("distance_km", pa.float32()),                     # point -> site
    ("elev_diff_m", pa.float32()),                     # site - point (null if unknown)
    ("valid_date_ist", pa.date32()),
    ("variable", pa.string()),
    ("value", pa.float32()),                           # null unless complete
    ("unit", pa.string()),
    ("n_obs", pa.int16()),
    ("complete", pa.bool_()),
    ("aggregation", pa.string()),
    ("source_url", pa.string()),
    ("retrieved_at_utc", pa.timestamp("ms", tz="UTC")),
    ("note", pa.string()),
])

LEAD_BASIS = ("Open-Meteo Previous Runs API previous_day{n}: each hourly value was predicted at least {n} x 24 h "
              "before its valid time; the model run (initialisation time) is not identified by the source")
AGG_TEXT = {
    "ist_day": "{how} of 24 hourly values at 19:00Z (previous day) .. 18:00Z = IST day 00:30..23:30 (instants); "
               "hourly precipitation is the preceding-hour total, so the precipitation day is 18:00Z..18:00Z "
               "(30 min earlier than the IST day)",
    "imd_window": "sum of 24 hourly totals ending 04:00Z .. 03:00Z next day = 08:30 IST on this date to 08:30 IST the "
                  "next day (IMD's rain-gauge day; aligned exactly)",
}


def load_points() -> list[dict]:
    return json.loads(POINTS_FILE.read_text())["points"]


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def om_weight(n_locations: int, n_variables: int, n_days: int) -> float:
    """Open-Meteo counted API calls: each location counts; >10 variables or >14 days count as fractions more."""
    return n_locations * max(1.0, n_variables / 10) * max(1.0, n_days / 14)


def window_instants(d: date, window: str) -> list[datetime]:
    """The 24 hourly UTC instants whose values form day `d` for the given window."""
    if window == "ist_day":
        start = datetime(d.year, d.month, d.day, tzinfo=timezone.utc) - timedelta(hours=5)      # 19:00Z previous day
    elif window == "imd_window":
        start = datetime(d.year, d.month, d.day, 4, tzinfo=timezone.utc)                        # 04:00Z = 09:30 IST
    else:
        raise ValueError(window)
    return [start + timedelta(hours=h) for h in range(24)]


def utc_request_range(d1: date, d2: date) -> tuple[date, date]:
    """UTC start/end dates that contain every instant needed for IST days d1..d2 in both windows."""
    return d1 - timedelta(days=1), d2 + timedelta(days=1)


def parse_hourly_times(times: list[str]) -> list[datetime]:
    return [datetime.fromisoformat(t).replace(tzinfo=timezone.utc) for t in times]


def aggregate_daily(times_utc: list[datetime], values: list, how: str, window: str, days: list[date]):
    """Yield (day, value|None, hours_present). value only when all 24 instants are present and non-null."""
    lookup = {t: v for t, v in zip(times_utc, values)}
    for d in days:
        vals = [lookup.get(t) for t in window_instants(d, window)]
        present = [v for v in vals if v is not None and not (isinstance(v, float) and math.isnan(v))]
        n = len(present)
        if n < 24:
            yield d, None, n
            continue
        if how == "max":
            yield d, float(max(present)), n
        elif how == "min":
            yield d, float(min(present)), n
        elif how == "sum":
            yield d, float(sum(present)), n
        else:
            raise ValueError(how)


def date_range(d1: date, d2: date) -> list[date]:
    return [d1 + timedelta(days=i) for i in range((d2 - d1).days + 1)]


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: pathlib.Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=1, sort_keys=True, default=str) + "\n")


class HistoryError(RuntimeError):
    """Raised when historical data breaks a rule and must not be used."""


# ------------------------------------------------------------------ validation
def validate_history_rows(df) -> list[str]:
    """Rules for historical forecast rows (a pandas DataFrame in HIST_SCHEMA). Returns problems."""
    p = []
    if (df["dataset"] != "historical_backfill").any():
        p.append("dataset must be historical_backfill")
    if df["run_time_known"].any():
        p.append("run_time_known must be false for historical rows (run not identified by the source)")
    if df["run_time_utc"].notna().any():
        p.append("run_time_utc must be null for historical rows")
    if (~df["nominal_lead_day"].isin(LEADS)).any():
        p.append("nominal_lead_day outside 1..7")
    if (df["value"].notna() & ~df["complete"]).any():
        p.append("value present on an incomplete day (partial days must stay null)")
    if (df["complete"] & (df["hours_present"] != df["hours_expected"])).any():
        p.append("complete flag inconsistent with hours_present")
    if (df["complete"] & df["value"].isna()).any():
        p.append("complete day without a value")
    dup = df.duplicated(["point_id", "model", "nominal_lead_day", "valid_date_ist", "variable"]).sum()
    if dup:
        p.append(f"{dup} duplicate rows")
    for var, (lo, hi) in PLAUSIBLE.items():
        v = df.loc[(df["variable"] == var) & df["value"].notna(), "value"]
        n = int(((v < lo) | (v > hi)).sum())
        if n:
            p.append(f"{n} {var} values outside {lo}..{hi}")
    return p


def validate_reference_rows(df, imd_max_km: float = 30.0) -> list[str]:
    p = []
    if (df["dataset"] != "reference").any():
        p.append("dataset must be reference")
    metar_rain = df[(df["reference"] == "metar") & df["variable"].str.startswith("precip")]
    if len(metar_rain):
        p.append("METAR rainfall is not a verification reference (p01m is a placeholder in the Indian feed)")
    far = df[(df["reference"] == "imd_rf025") & df["value"].notna() & (df["distance_km"] > imd_max_km)]
    if len(far):
        p.append(f"IMD values from a cell more than {imd_max_km} km away")
    if (df["value"].notna() & ~df["complete"]).any():
        p.append("value present on an incomplete day")
    dup = df.duplicated(["reference", "point_id", "site_id", "valid_date_ist", "variable"]).sum()
    if dup:
        p.append(f"{dup} duplicate rows")
    for var, (lo, hi) in PLAUSIBLE.items():
        v = df.loc[(df["variable"] == var) & df["value"].notna(), "value"]
        n = int(((v < lo) | (v > hi)).sum())
        if n:
            p.append(f"{n} {var} values outside {lo}..{hi}")
    return p


# ------------------------------------------------------------------ coverage / backfill report
def backfill_report(df, expected: list[dict]) -> dict:
    """Compare a backfill against its explicit expectation.

    expected: [{"model", "variable", "nominal_lead_day", "points": [...], "days": [date...]}]
    Status is "complete" only if every expected (point, day) has a complete value; otherwise "partial",
    with counts per cell. Nothing is ever reported complete by default.
    """
    have = defaultdict(set)
    for r in df[df["complete"]].itertuples():
        have[(r.model, r.variable, int(r.nominal_lead_day))].add((r.point_id, r.valid_date_ist))
    rows_any = defaultdict(set)
    for r in df.itertuples():
        rows_any[(r.model, r.variable, int(r.nominal_lead_day))].add((r.point_id, r.valid_date_ist))
    cells, total_exp, total_ok = [], 0, 0
    for e in expected:
        key = (e["model"], e["variable"], e["nominal_lead_day"])
        exp = {(pt, d) for pt in e["points"] for d in e["days"]}
        ok = len(exp & have[key])
        stored_incomplete = len((exp & rows_any[key]) - have[key])
        cells.append({"model": key[0], "variable": key[1], "nominal_lead_day": key[2], "expected": len(exp),
                      "complete": ok, "stored_incomplete": stored_incomplete,
                      "absent": len(exp) - ok - stored_incomplete,
                      "status": "complete" if ok == len(exp) else "partial"})
        total_exp += len(exp)
        total_ok += ok
    return {"status": "complete" if total_ok == total_exp and total_exp > 0 else "partial",
            "expected_values": total_exp, "complete_values": total_ok,
            "missing_values": total_exp - total_ok, "cells": cells}
