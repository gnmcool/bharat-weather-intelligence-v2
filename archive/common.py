"""Shared schema, constants and helpers for the V2 immutable daily forecast archive (M4)."""
from __future__ import annotations

import hashlib
import json
import pathlib
from datetime import date, datetime, timedelta, timezone

import pyarrow as pa

SCHEMA_VERSION = 1
IST = timezone(timedelta(hours=5, minutes=30))
HERE = pathlib.Path(__file__).resolve().parent

# ---- forecasts table: exact-run model forecasts only (run_time_known is always true) ----
FORECAST_SCHEMA = pa.schema([
    ("point_id", pa.string()),
    ("lat", pa.float32()),
    ("lon", pa.float32()),
    ("model", pa.string()),
    ("source", pa.string()),
    ("source_url", pa.string()),
    ("run_time_utc", pa.timestamp("ms", tz="UTC")),   # model initialisation instant
    ("run_time_known", pa.bool_()),
    ("valid_date_ist", pa.date32()),                  # calendar day in India Standard Time
    ("lead_day", pa.int16()),                         # valid_date_ist - date(run_time in IST)
    ("day_partial", pa.bool_()),                      # the run does not cover the whole IST day
    ("variable", pa.string()),
    ("value", pa.float32()),
    ("unit", pa.string()),
    ("retrieved_at_utc", pa.timestamp("ms", tz="UTC")),
])
REQUIRED_NON_NULL = [f.name for f in FORECAST_SCHEMA if f.name != "value"]

# ---- CORE snapshot tables (CORE output as shown; best-match values are a blend, so no model run time) ----
CORE_RISK_SCHEMA = pa.schema([
    ("point_id", pa.string()),
    ("core_generated_at_utc", pa.timestamp("ms", tz="UTC")),
    ("retrieved_at_utc", pa.timestamp("ms", tz="UTC")),
    ("risk_id", pa.string()),
    ("level", pa.int8()),
    ("status", pa.string()),
    ("period_start", pa.string()),
    ("period_end", pa.string()),
    ("peak_value", pa.float32()),
    ("unit", pa.string()),
    ("agreement_basis", pa.string()),
    ("official", pa.bool_()),
    ("experimental", pa.bool_()),
    ("reference", pa.string()),
    ("official_alert_ids", pa.string()),              # JSON list of CORE-matched SACHET ids at that time
    ("model_runs_note", pa.string()),                 # CORE's "per-model runs used" provenance text
])
CORE_DAILY_SCHEMA = pa.schema([
    ("point_id", pa.string()),
    ("core_generated_at_utc", pa.timestamp("ms", tz="UTC")),
    ("retrieved_at_utc", pa.timestamp("ms", tz="UTC")),
    ("valid_date_ist", pa.date32()),
    ("variable", pa.string()),
    ("value", pa.float32()),
    ("unit", pa.string()),
])

DAILY_VARS = {  # Open-Meteo daily variable -> (archive variable, unit)
    "temperature_2m_max": ("tmax", "degC"),
    "temperature_2m_min": ("tmin", "degC"),
    "precipitation_sum": ("precip", "mm"),
    "wind_gusts_10m_max": ("gust_max", "km/h"),
}


def run_ist_date(run_time_utc: datetime) -> date:
    return run_time_utc.astimezone(IST).date()


def lead_day(valid_date_ist: date, run_time_utc: datetime) -> int:
    return (valid_date_ist - run_ist_date(run_time_utc)).days


def ist_day_window_utc(d: date) -> tuple[datetime, datetime]:
    start = datetime(d.year, d.month, d.day, tzinfo=IST).astimezone(timezone.utc)
    return start, start + timedelta(days=1)


def day_fully_covered(d: date, run_time_utc: datetime, data_end_utc: datetime, step_hours: int) -> bool:
    """True when every model step in the IST day lies within [run init, last valid time]."""
    s, e = ist_day_window_utc(d)
    return s >= run_time_utc and (e - timedelta(hours=step_hours)) <= data_end_utc


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: pathlib.Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=1, sort_keys=True, default=str) + "\n")


class ArchiveError(RuntimeError):
    """Raised when an archive must not be published."""
