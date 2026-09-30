"""M4.4 verification: shared definitions, straight from VM-1.0 (docs/VERIFICATION_METHODOLOGY.md).

Gate 1 (M4.4-A census) uses only this module, inputs.py and census.py. No metric is computed anywhere in this package
at Gate 1.
"""
from __future__ import annotations

import importlib.util
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
METHODOLOGY_VERSION = "VM-1.1"
CENSUS_VERSION = "m4.4-a-census-2"   # census-2: both sides' reasons preserved (VM-1.1 §6 precedence)

# VM-1.1 §6: primary exclusion reason precedence (owner decision, 30 Sep 2026). Forecast-side D > C > B > A rank above
# every reference-side reason (E, F, G), so the primary reason is the forecast's when the forecast is unavailable;
# the other side's reason is always kept as well.
PRECEDENCE = ["D", "C", "B", "A", "E", "F", "G"]

# single source of truth for categories A-G: history/common.py (loaded by path; both packages have a common.py)
_spec = importlib.util.spec_from_file_location("history_common", REPO / "history" / "common.py")
history_common = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(history_common)
classify_reason = history_common.classify_reason
CATEGORIES = history_common.CATEGORIES

# VM-1.0 §2: the only independent models. Earth2Studio GFS (e2s_gfs025) is never one of them.
MODELS = ("ecmwf_ifs025", "gfs_global", "icon_global")
NOT_INDEPENDENT = {"e2s_gfs025": "Earth2Studio GFS is the same GFS model (VM-1.0 §2)"}
LEADS = tuple(range(1, 8))

# VM-1.0 §3/§5 and the owner's M4.4-A scope: one window per experiment, never mixed. Gust excluded (Q5).
EXPERIMENTS = {
    "A1": {"variables": ("tmax", "tmin"), "reference": "era5", "window": "ist_day",
           "label": "Tmax/Tmin vs ERA5 reanalysis (agreement with reanalysis, not observation)", "geo": "pooled"},
    "A2": {"variables": ("tmax", "tmin"), "reference": "metar", "window": "ist_day",
           "label": "Tmax/Tmin vs METAR station observation (matched stations only, per station)", "geo": "station"},
    "A3": {"variables": ("precip_0830",), "reference": "imd_rf025", "window": "imd_0830",
           "label": "Rain (08:30-08:30 IST) vs IMD gridded rain-gauge analysis", "geo": "pooled", "rainy_split": True},
    "A4": {"variables": ("precip",), "reference": "era5", "window": "ist_day",
           "label": "Rain (IST day) vs ERA5 reanalysis (secondary)", "geo": "pooled", "rainy_split": True},
}
RAINY_DAY_MM = 2.5   # VM-1.0 §7: analytical split on the reference value only; never a risk threshold

# VM-1.0 §13: IMD seasons
SEASONS = {1: "winter", 2: "winter", 3: "pre-monsoon", 4: "pre-monsoon", 5: "pre-monsoon",
           6: "monsoon", 7: "monsoon", 8: "monsoon", 9: "monsoon",
           10: "post-monsoon", 11: "post-monsoon", 12: "post-monsoon"}

# VM-1.0 §12 (approved): IMD-style regions by State/UT; islands always separate
REGIONS = {
    "north-west": ["Jammu and Kashmir", "Ladakh", "Himachal Pradesh", "Uttarakhand", "Punjab", "Chandigarh", "Haryana",
                   "Delhi", "Uttar Pradesh", "Rajasthan"],
    "central": ["Gujarat", "Dadra and Nagar Haveli and Daman and Diu", "Madhya Pradesh", "Chhattisgarh", "Maharashtra",
                "Goa", "Odisha"],
    "south-peninsula": ["Andhra Pradesh", "Telangana", "Karnataka", "Kerala", "Tamil Nadu", "Puducherry"],
    "east-north-east": ["Bihar", "Jharkhand", "West Bengal", "Sikkim", "Assam", "Meghalaya", "Arunachal Pradesh",
                        "Nagaland", "Manipur", "Mizoram", "Tripura"],
    "islands": ["Andaman and Nicobar Islands", "Lakshadweep"],
}
STATE_REGION = {s: r for r, states in REGIONS.items() for s in states}
HIGH_ALTITUDE_M = 1000.0   # VM-1.0 §12: point DEM elevation >= 1,000 m
ERA5_MAX_GRID_KM = 30.0    # VM-1.0 §6 (4)
IMD_MAX_KM = 30.0

# VM-1.0 §11 publication floors (continuous results)
FLOORS = {
    "pooled": {"n": 300, "dates": 60, "points": 10},
    "season": {"n": 300, "dates": 60, "points": 10},
    "region": {"n": 300, "dates": 60, "points": 3},
    "high_altitude": {"n": 300, "dates": 60, "points": 3},
    "station": {"n": 90, "dates": 90, "points": 1},     # single point: >= 90 eligible days
}


def floor_status(kind: str, n: int, dates: int, points: int) -> tuple[str, str]:
    f = FLOORS[kind]
    ok = n >= f["n"] and dates >= f["dates"] and points >= f["points"]
    rule = f"{kind}: n >= {f['n']}, dates >= {f['dates']}, points >= {f['points']}"
    return ("meets floor" if ok else "insufficient sample"), rule


class CensusError(RuntimeError):
    """Input or rule violation: the census refuses to run."""
