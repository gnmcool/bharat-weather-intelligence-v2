"""Declarative V2 catalogue: wording and data mappings for each CORE risk.

Nothing here is a threshold or a detection rule. Levels, thresholds and criteria come from
CORE's /dashboard risks unchanged. This file only decides:
  * the V2 title of an event (wording),
  * which CORE-published numbers are shown as evidence for that risk,
  * which satellite layers are relevant for visual context,
  * which words link an official alert to a hazard,
  * which existing CORE crop indicators use the same weather variable.
See docs/EVENTS_AND_EVIDENCE.md.
"""
from __future__ import annotations

LEVEL_NAME = ["No risk", "Watch", "Alert", "Severe"]
INDEPENDENT_MODELS = {"ecmwf_ifs025": "ECMWF", "gfs_seamless": "GFS", "icon_seamless": "ICON"}

# V2 titles. "potential — model derived" for convective items: they are never observations.
TITLE = {
    "heat": "Heat",
    "cold": "Cold",
    "rain": "Heavy rain",
    "wind": "Strong wind",
    "thunderstorm": "Thunderstorm potential — model derived",
    "lightning": "Lightning potential — model derived",
    "flood": "Flood-related risk (rainfall accumulation)",
    "drought": "Dry spell / rainfall deficit",
    "fog": "Fog",
    "fire": "Fire weather",
    "cyclone": "Cyclone (official alert logic)",
}

# Per-model evidence CORE publishes: daily.models.{ecmwf_ifs025,gfs_seamless,icon_seamless}.{tmax,tmin,precip}.
# (key in models, aggregation over the event window, label, unit)
MODEL_EVIDENCE = {
    "heat": ("tmax", "max", "Highest daily maximum temperature in the event window", "°C"),
    "cold": ("tmin", "min", "Lowest daily minimum temperature in the event window", "°C"),
    "rain": ("precip", "max", "Highest daily rainfall in the event window", "mm/day"),
}
MODEL_EVIDENCE_UNAVAILABLE = {
    "wind": "CORE publishes per-model daily temperature and rainfall only; per-model gusts are not available.",
    "flood": "CORE's flood rule uses 72-hour accumulated rain including the past 2 days of analysis; CORE does not publish that accumulation per model.",
    "thunderstorm": "CORE assesses convection from a single blended model (hourly CAPE, weather code, rain chance); there are no per-model values.",
    "lightning": "CORE assesses lightning potential from the thunderstorm signal of a single blended model; there are no per-model values.",
    "fog": "CORE derives visibility from a single blended model; there are no per-model values.",
    "fire": "CORE's fire-weather heuristic uses a single blended model; there are no per-model values.",
    "drought": "The dry-spell / deficit rule uses past-30-day model analysis and the forecast, not per-model forecasts.",
    "cyclone": "Cyclone is official-only in CORE: it comes from IMD alerts, not from model values.",
}

# Best-match forecast vs NASA POWER normal, from CORE daily rows: (forecast key, normal key, aggregation, label, unit)
NORMAL_EVIDENCE = {
    "heat": ("temperature_2m_max", "normal_tmax", "peak", "Daily maximum temperature on the peak day", "°C"),
    "cold": ("temperature_2m_min", "normal_tmin", "trough", "Daily minimum temperature on the coldest day", "°C"),
    "rain": ("precipitation_sum", "normal_precip", "sum", "Rainfall total over the event window", "mm"),
    "flood": ("precipitation_sum", "normal_precip", "sum", "Forecast rainfall total over the event window", "mm"),
    "thunderstorm": ("precipitation_sum", "normal_precip", "sum", "Forecast rainfall total over the event window", "mm"),
    "lightning": ("precipitation_sum", "normal_precip", "sum", "Forecast rainfall total over the event window", "mm"),
}
# CORE anomaly items relevant to each hazard (anomaly.items[].id).
ANOMALY_ITEMS = {
    "heat": ["tmax_today", "tmax_7d"],
    "cold": ["tmin_today"],
    "rain": ["rain_7d"],
    "flood": ["rain_7d", "rain_30d"],
    "thunderstorm": ["rain_7d"],
    "lightning": ["rain_7d"],
    "drought": ["rain_30d", "rain_7d"],
}

# Earth2Studio GFS point series (CORE /grid/point; 3-hourly UTC): (series key, aggregation, label, unit)
E2S_EVIDENCE = {
    "heat": ("t2m", "max", "Highest 3-hourly temperature in the window", "°C"),
    "cold": ("t2m", "min", "Lowest 3-hourly temperature in the window", "°C"),
    "rain": ("tp", "daymax", "Highest IST-day rainfall total in the window", "mm/day"),
    "flood": ("tp", "sum", "Rainfall total over the forecast part of the window", "mm"),
    "thunderstorm": ("tp", "sum", "Rainfall total over the window", "mm"),
    "lightning": ("tp", "sum", "Rainfall total over the window", "mm"),
    "wind": ("fg10m", "max", "Highest 3-hourly wind gust in the window", "km/h"),
}

# CORE /earthobs/layers ids that give visual context. Never quantitative.
SATELLITE = {
    "rain": ["rain_now"],
    "flood": ["flood", "rain_now"],
    "thunderstorm": ["rain_now", "truecolor"],
    "lightning": ["rain_now", "truecolor"],
    "drought": ["soil", "ndvi"],
    "fog": ["truecolor"],
    "fire": ["truecolor"],  # plus NASA FIRMS hotspots layer
    "cyclone": ["truecolor", "rain_now"],
}
SATELLITE_LABEL = {
    "rain_now": "Rain now (NASA IMERG)",
    "flood": "Flood water (NASA VIIRS/MODIS)",
    "soil": "Soil moisture (NASA SMAP)",
    "ndvi": "Crop greenness (NDVI)",
    "truecolor": "True colour (VIIRS daily)",
    "firms": "Active fires (NASA FIRMS)",
}

# Words in an official alert's event/headline that relate it to a hazard (display link only).
OFFICIAL_KEYWORDS = {
    "heat": ["heat"],
    "cold": ["cold", "frost"],
    "rain": ["rain", "shower"],
    "wind": ["wind", "gale", "squall", "cyclone"],
    "thunderstorm": ["thunder"],
    "lightning": ["lightning", "thunder"],
    "flood": ["flood", "inundation"],
    "drought": ["drought"],
    "fog": ["fog"],
    "fire": ["fire"],
    "cyclone": ["cyclone", "depression"],
}

# Existing CORE farmer indicators that use the same weather variable (display link, not an agronomic rule).
FARMER_LINK = {
    "heat": ["heat_stress"],
    "cold": ["cold_stress"],
    "rain": ["heavy_rain", "harvest_window"],
    "flood": ["heavy_rain", "harvest_window"],
    "drought": ["dry_spell"],
}
FARMER_LINK_WHY = {
    "heat": "uses daily maximum temperature",
    "cold": "uses daily minimum temperature",
    "rain": "uses daily rainfall",
    "flood": "uses daily rainfall",
    "drought": "uses consecutive dry days",
}

# Significant departures from normal = CORE's own categories outside its normal band.
NORMAL_CATEGORIES = {None, "", "Near normal", "Normal"}

# Level-0 CORE "confidence" text says "k of n models … show no event"; level >= 1 says "k of n models agree".
AGREEMENT_NOTE = ("Number of independent models (ECMWF, GFS, ICON) that CORE found reaching the same risk level "
                  "within ±1 day. It is agreement between models, not a probability. Earth2Studio GFS and "
                  "FourCastNet (initialised from GFS) are not counted as additional models.")

# ---------------------------------------------------------------------------------------------
# M3 — data-quality notices. Each is triggered by a CORE field, never by a new threshold
# (docs/DATA_QUALITY.md). Factual and short.
NOTICES = {
    "representative_point": {
        "title": "District counts use one forecast point per district",
        "text": "District risk counts are based on the representative forecast point for each district. Conditions may vary within a district.",
    },
    "elevation": {
        "title": "Mountain terrain",
        "text": "In mountainous areas, elevation differences can make a single forecast point less representative of nearby places. CORE classifies this location as hill terrain.",
    },
    "elevation_districts": {
        "title": "Mountain districts in this count",
        "text": "Some counted districts are in hill terrain (CORE classification). Their representative point can be much higher or lower than towns in the district, so the level may not describe conditions across the whole district.",
    },
    "grid_vs_point": {
        "title": "Grid value, not a point value",
        "text": "The Earth2Studio GFS value represents a ~27 km grid cell, not this exact point. In mountainous or coastal terrain it can differ materially from the point forecasts.",
    },
    "incomplete_hazards": {
        "title": "Not every hazard is counted by district",
        "text": "Only heat, cold, heavy rain and strong wind have a district-count method. Other hazards are assessed at individual locations only.",
    },
    "core_inconsistency": {
        "title": "CORE output inconsistency",
        "text": "A CORE risk is at No risk while CORE's own model check says every independent model shows an event. V2 shows CORE's level unchanged; recorded for investigation (CORE-2).",
    },
}

# ---------------------------------------------------------------------------------------------
# M3 — potential-relevance context. Shown only next to a CORE event at Watch or above.
# General, conditional wording ("may"); never an instruction; never a claim that impact occurred.
# Source: V2 context catalogue (docs/IMPACT_CONTEXT.md). Cyclone: official alert text only.
CONTEXT = {
    "heat": ("High temperatures may affect people working or travelling outdoors, especially in the afternoon.",
             "Heat during this period may be relevant to field work and to crops at heat-sensitive stages."),
    "cold": ("Low temperatures may affect people outdoors, especially at night and in the early morning.",
             "Low night temperatures during this period may be relevant to crops at cold-sensitive stages."),
    "rain": ("Heavy rain may affect travel and low-lying areas.",
             "Rain during this period may affect field operations."),
    "wind": ("Strong gusts may affect travel, trees and loose structures.",
             "Strong wind during this period may affect field operations and tall standing crops."),
    "thunderstorm": ("If thunderstorms develop, they may bring sudden heavy rain, gusts and lightning.",
                     "If thunderstorms develop, they may interrupt field operations."),
    "lightning": ("Lightning potential is most relevant to people in open areas.",
                  "Lightning potential is most relevant to people working in open fields."),
    "flood": ("Accumulated rain may affect low-lying and poorly drained areas.",
              "Accumulated rain may be relevant to waterlogging in low-lying fields."),
    "fog": ("Low visibility may affect road, rail and air travel.",
            "Low visibility may affect early-morning field work and transport."),
    "fire": ("Hot, dry and windy conditions may be relevant to the spread of fires.",
             "Hot, dry and windy conditions may be relevant to fire in dry fields and crop residue."),
    "drought": ("A rainfall deficit may be relevant to local water availability.",
                "A rainfall deficit during this period may be relevant to soil moisture and irrigation."),
}
GOV_TERM = {"heat": "heat", "cold": "cold", "rain": "heavy-rain", "wind": "strong-wind", "thunderstorm": "thunderstorm-potential",
            "lightning": "lightning-potential", "flood": "flood-related", "fog": "fog", "fire": "fire-weather", "drought": "dry-spell"}
CONTEXT_LABEL = "Potential relevance — general context, not an impact forecast"
