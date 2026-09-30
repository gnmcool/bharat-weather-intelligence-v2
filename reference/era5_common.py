"""Fixed definitions for D2 (docs/M4.4-D2_PLAN.md, revision 3, frozen at 781d2e8).

Everything here is a direct transcription of the plan: source (§3), request (§4), grid-node rule and tie-break
(§5.2), 30 km rule (§5.3), IST-day window (§5.4), eligibility date (§6), licence and attribution (§10.6).
Nothing in this module talks to the network.
"""
from __future__ import annotations

import calendar
import hashlib
import json
import math
import pathlib
from datetime import date, datetime, timedelta, timezone
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal

ROOT = pathlib.Path(__file__).resolve().parents[1]
HERE = pathlib.Path(__file__).resolve().parent

PLAN = "docs/M4.4-D2_PLAN.md (revision 3, commit 781d2e8)"

# ---------------------------------------------------------------- source (§3)
CDS_URL = "https://cds.climate.copernicus.eu/api"
DATASET = "reanalysis-era5-single-levels"
PRODUCT_TYPE = "reanalysis"
VARIABLE = "total_precipitation"
SHORT_NAME = "tp"
UNITS = "m"
DATA_FORMAT = "grib"
DOWNLOAD_FORMAT = "unarchived"
FINAL_EXPVER = "0001"               # final ERA5; 0005 = ERA5T (preliminary)
GRID_STEP = Decimal("0.25")

# ---------------------------------------------------------------- points and area (§4.2, §5.1)
POINTS_FILE = ROOT / "archive" / "points.json"
POINTS_SHA256 = "4919f87259fd22a83a6050e01497f3be86711ce0e10e28aecbb9af324b65d49e"
AREA = [34.0, 72.25, 8.25, 94.75]  # [North, West, South, East], derived by the §4.2 rule from the points above
N_POINTS = 36

# ---------------------------------------------------------------- rules (§5.2–§5.4, §6)
EARTH_RADIUS_KM = 6371.0
MAX_NODE_KM = 30.0                  # VM §6 rule 4: eligible if distance <= 30 km
WAIT_DAYS = 70                      # R1: eligibility date = last day of the month + 70 days (a start date only)
VALIDATION_MONTH = "2026-09"        # R2: the first month retrieved; the only month with the controlled repeat
MAX_RETRIEVALS = 2                  # per reference month; each retrieval = 2 CDS jobs (boundary + month)
ROLES = ("boundary", "month")

AGGREGATION_RULE = (
    "IST calendar day D = 00:00-24:00 IST = 18:30Z (D-1) ... 18:30Z (D). ERA5 values are stamped at full UTC hours "
    "(GRIB validity time); each value is the total precipitation over the preceding hour (t-1 h, t]. Day D uses the "
    "24 stamps 19:00Z (D-1) ... 18:00Z (D), covering 18:00Z (D-1) ... 18:00Z (D) = 23:30 IST (D-1) ... 23:30 IST (D): "
    "the ERA5 day starts and ends 30 minutes earlier than the IST calendar day (hourly data cannot be split at :30). "
    "Hourly mm = GRIB value (m) x 1000 in float64; the daily value is the float64 sum of the 24 hourly mm values, "
    "stored as float32. A day has a value only if all 24 stamps exist and are non-missing at the point's node; "
    "otherwise it is null with reason E. A point whose node is > 30 km away has every day null with reason G. "
    "Values are used as delivered: no clipping, smoothing, filling or interpolation."
)

NODE_RULE = (
    "Nearest 0.25 degree node per axis: node = floor(coordinate x 4 + 0.5) / 4, evaluated in exact decimal "
    "arithmetic on the coordinates as written in archive/points.json. A coordinate exactly midway between two grid "
    "lines goes to the northern (latitude) / eastern (longitude) node. No land-sea selection."
)

NODE_NOTE = ("nearest 0.25° CDS node; not land-cell selected; may differ from the Open-Meteo cell used for the "
             "historical ERA5 values")

# ---------------------------------------------------------------- licence and attribution (§10.6)
LICENCE = "Licence to use Copernicus Products (CC-BY per CDS dataset page)"
ATTRIBUTION_RAW = "Generated using Copernicus Climate Change Service information {year}"
ATTRIBUTION_DERIVED = "Contains modified Copernicus Climate Change Service information {year}"
NON_RESPONSIBILITY = ("Neither the European Commission nor ECMWF is responsible for any use that may be made of the "
                      "Copernicus information or data it contains")
LICENCE_FILE = HERE / "era5_licence.json"

UTC = timezone.utc


class ReferenceError_(RuntimeError):
    """A D2 rule is violated; the retrieval or month is refused (never silently repaired)."""


# ---------------------------------------------------------------- points
def load_points(path: pathlib.Path = POINTS_FILE, expected_sha256: str | None = POINTS_SHA256) -> list[dict]:
    """The 36 fixed points in file order, coordinates as exact Decimals (parsed from the JSON text).

    Refuses if the file's SHA-256 differs from the approved hash: a changed points file is outside D2's scope."""
    raw = path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None and sha != expected_sha256:
        raise ReferenceError_(f"archive/points.json SHA-256 {sha} differs from the approved {expected_sha256}")
    doc = json.loads(raw.decode("utf-8"), parse_float=Decimal)
    pts = doc["points"] if isinstance(doc, dict) else doc
    out = [{"id": p["id"], "lat": Decimal(p["lat"]), "lon": Decimal(p["lon"]),
            "district": p.get("district"), "state": p.get("state")} for p in pts]
    if len({p["id"] for p in out}) != len(out):
        raise ReferenceError_("duplicate point ids in archive/points.json")
    return out


def points_sha256(path: pathlib.Path = POINTS_FILE) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------- grid-node rule (§5.2)
def _floor(x: Decimal) -> Decimal:
    return x.to_integral_value(rounding=ROUND_FLOOR)


def node_coord(x: Decimal) -> Decimal:
    """floor(x*4 + 1/2)/4: nearest 0.25 degree grid line; an exact midpoint goes north/east (towards +infinity)."""
    x = Decimal(x)
    return _floor(x * 4 + Decimal("0.5")) / 4


def is_midpoint(x: Decimal) -> bool:
    x4 = Decimal(x) * 4
    return x4 - _floor(x4) == Decimal("0.5")


def grid_ceil(x: Decimal) -> Decimal:
    return (Decimal(x) * 4).to_integral_value(rounding=ROUND_CEILING) / 4


def grid_floor(x: Decimal) -> Decimal:
    return _floor(Decimal(x) * 4) / 4


def area_for(points: list[dict]) -> list[float]:
    """§4.2: [ceil(max lat), floor(min lon), floor(min lat), ceil(max lon)] on the 0.25 degree grid."""
    lats = [p["lat"] for p in points]
    lons = [p["lon"] for p in points]
    return [float(grid_ceil(max(lats))), float(grid_floor(min(lons))),
            float(grid_floor(min(lats))), float(grid_ceil(max(lons)))]


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    """Great-circle distance with Earth radius 6371.0 km (§5.2)."""
    p1, p2 = math.radians(float(lat1)), math.radians(float(lat2))
    dp, dl = p2 - p1, math.radians(float(lon2) - float(lon1))
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def node_for(point: dict) -> dict:
    nlat, nlon = node_coord(point["lat"]), node_coord(point["lon"])
    dist = haversine_km(point["lat"], point["lon"], nlat, nlon)
    return {"point_id": point["id"], "lat": point["lat"], "lon": point["lon"], "node_lat": nlat, "node_lon": nlon,
            "distance_km": dist, "eligible": dist <= MAX_NODE_KM,
            "tie_break_applied": is_midpoint(point["lat"]) or is_midpoint(point["lon"])}


# ---------------------------------------------------------------- months and requests (§4.1)
def parse_month(month: str) -> tuple[int, int]:
    try:
        y, m = (int(x) for x in month.split("-"))
        if len(month) != 7 or not 1 <= m <= 12:
            raise ValueError
    except ValueError:
        raise ReferenceError_(f"invalid month {month!r}; expected YYYY-MM") from None
    return y, m


def month_days(month: str) -> list[date]:
    y, m = parse_month(month)
    return [date(y, m, d) for d in range(1, calendar.monthrange(y, m)[1] + 1)]


def previous_month_last_day(month: str) -> date:
    return month_days(month)[0] - timedelta(days=1)


def build_requests(month: str, area: list[float] | None = None) -> dict[str, dict]:
    """The two CDS requests of one retrieval: boundary (5 items) and month (n x 24 items)."""
    area = list(AREA if area is None else area)
    days = month_days(month)
    b = previous_month_last_day(month)
    common = {"product_type": [PRODUCT_TYPE], "variable": [VARIABLE], "data_format": DATA_FORMAT,
              "download_format": DOWNLOAD_FORMAT, "area": area}
    boundary = {**common, "year": [f"{b.year:04d}"], "month": [f"{b.month:02d}"], "day": [f"{b.day:02d}"],
                "time": [f"{h:02d}:00" for h in range(19, 24)]}
    monthly = {**common, "year": [f"{days[0].year:04d}"], "month": [f"{days[0].month:02d}"],
               "day": [f"{d.day:02d}" for d in days], "time": [f"{h:02d}:00" for h in range(24)]}
    return {"boundary": boundary, "month": monthly}


def canonical_json(request: dict) -> str:
    return json.dumps(request, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def request_sha256(request: dict) -> str:
    return hashlib.sha256(canonical_json(request).encode("ascii")).hexdigest()


def item_count(request: dict) -> int:
    return (len(request["year"]) * len(request["month"]) * len(request["day"]) * len(request["time"])
            * len(request["variable"]))


def expected_stamps(request: dict) -> list[datetime]:
    """Every validity stamp the request asks for (years x months x days x times), skipping impossible dates."""
    out = []
    for y in request["year"]:
        for m in request["month"]:
            for d in request["day"]:
                for t in request["time"]:
                    try:
                        out.append(datetime(int(y), int(m), int(d), int(t[:2]), tzinfo=UTC))
                    except ValueError:
                        continue
    return sorted(out)


def ist_day_stamps(d: date) -> list[datetime]:
    """§5.4: the 24 stamps 19:00Z (D-1) ... 18:00Z (D)."""
    start = datetime(d.year, d.month, d.day, tzinfo=UTC) - timedelta(hours=5)
    return [start + timedelta(hours=h) for h in range(24)]


def eligibility_date(month: str) -> date:
    return month_days(month)[-1] + timedelta(days=WAIT_DAYS)


def is_eligible(month: str, today: date) -> bool:
    return today >= eligibility_date(month)


def tag_for(month: str) -> str:
    parse_month(month)
    return f"ref-era5-{month}"


def load_licence(path: pathlib.Path = LICENCE_FILE) -> dict:
    doc = json.loads(path.read_text())
    for k in ("accepted_on", "stated_by", "licence"):
        if not doc.get(k):
            raise ReferenceError_(f"{path.name}: missing {k}")
    date.fromisoformat(doc["accepted_on"])
    return doc


def attribution(year: int) -> dict:
    return {"raw_grib": ATTRIBUTION_RAW.format(year=year), "derived_tables": ATTRIBUTION_DERIVED.format(year=year),
            "statement": NON_RESPONSIBILITY}
