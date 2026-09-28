"""Network access for the historical dataset (M4.2). Public sources only; free tier; nothing written anywhere
except the caller's output directory.

  Open-Meteo Previous Runs API   historical model forecasts at nominal leads 1..7 (run not identified)
  Open-Meteo archive API (era5)  ERA5 reanalysis (secondary reference; ~6-day lag)
  Iowa Environmental Mesonet     METAR archive for Indian airports (temperature, wind, visibility, weather codes;
                                 rainfall NEVER requested)
  IMD Pune                       0.25 deg gridded daily rainfall, one NetCDF file per year
"""
from __future__ import annotations

import csv
import io
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from datetime import date

from common import HistoryError, om_weight

UA = {"User-Agent": "BWI-V2-history/1 (non-commercial research; github.com/gnmcool/bharat-weather-intelligence-v2)"}
PREV_RUNS = "https://previous-runs-api.open-meteo.com/v1/forecast"
ERA5 = "https://archive-api.open-meteo.com/v1/archive"
IEM_STATIONS = "https://mesonet.agron.iastate.edu/geojson/network/IN__ASOS.geojson"
IEM_ASOS = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"
IMD_RF25 = "https://imdpune.gov.in/cmpg/Griddata/RF25.php"

STATS = {"requests": 0, "retries": 0, "rate_limited": 0, "http_errors": 0, "network_errors": 0,
         "om_requests": 0, "om_weighted_calls": 0.0, "bytes": 0, "slept_for_limits_s": 0.0}


class WeightLimiter:
    """Keeps Open-Meteo counted calls under a safety margin of the free-tier minute and hour limits
    (600/min, 5,000/h). Sleeps; never drops a request."""

    def __init__(self, per_min: float = 450, per_hour: float = 4000):
        self.per_min, self.per_hour, self.log = per_min, per_hour, deque()

    def wait(self, w: float) -> None:
        while True:
            now = time.time()
            while self.log and now - self.log[0][0] > 3600:
                self.log.popleft()
            last_min = sum(x for t, x in self.log if now - t <= 60)
            last_hour = sum(x for _, x in self.log)
            if last_min + w <= self.per_min and last_hour + w <= self.per_hour:
                self.log.append((now, w))
                return
            STATS["slept_for_limits_s"] += 5
            time.sleep(5)


LIMITER = WeightLimiter()


def http(url: str, data: bytes | None = None, timeout: int = 120, tries: int = 4) -> bytes:
    last = None
    for a in range(tries):
        STATS["requests"] += 1
        try:
            req = urllib.request.Request(url, data=data, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read()
                STATS["bytes"] += len(body)
                return body
        except urllib.error.HTTPError as e:
            body = e.read()[:300].decode(errors="replace")
            last = f"HTTP {e.code}: {body}"
            if e.code == 429 or "limit" in body.lower():
                STATS["rate_limited"] += 1
                time.sleep(65)  # minute window; the limiter should normally prevent this
            else:
                STATS["http_errors"] += 1
                if 400 <= e.code < 500:
                    break
        except Exception as e:  # noqa: BLE001 — network: retry with backoff
            STATS["network_errors"] += 1
            last = f"{type(e).__name__}: {e}"
        STATS["retries"] += 1
        time.sleep(min(60, 5 * 2 ** a))
    raise HistoryError(f"{url.split('?')[0]} failed: {last}")


def _om(base: str, params: dict, n_loc: int, n_vars: int, n_days: int):
    w = om_weight(n_loc, n_vars, n_days)
    LIMITER.wait(w)
    STATS["om_requests"] += 1
    STATS["om_weighted_calls"] += w
    url = base + "?" + urllib.parse.urlencode(params, safe=",")
    j = json.loads(http(url))
    if isinstance(j, dict) and j.get("error"):
        raise HistoryError(f"Open-Meteo error: {j.get('reason')}")
    return (j if isinstance(j, list) else [j]), url


def previous_runs(points: list[dict], om_model: str, hourly: list[str], leads: list[int], start: date, end: date):
    """Hourly previous_dayN values (UTC timestamps) for several points in one request."""
    vars_ = [f"{v}_previous_day{n}" for v in hourly for n in leads]
    params = {"latitude": ",".join(f"{p['lat']:.4f}" for p in points),
              "longitude": ",".join(f"{p['lon']:.4f}" for p in points),
              "hourly": ",".join(vars_), "models": om_model, "timezone": "GMT",
              "start_date": start.isoformat(), "end_date": end.isoformat()}
    return _om(PREV_RUNS, params, len(points), len(vars_), (end - start).days + 1)


def era5(points: list[dict], hourly: list[str], start: date, end: date):
    params = {"latitude": ",".join(f"{p['lat']:.4f}" for p in points),
              "longitude": ",".join(f"{p['lon']:.4f}" for p in points),
              "hourly": ",".join(hourly), "models": "era5", "timezone": "GMT",
              "start_date": start.isoformat(), "end_date": end.isoformat()}
    return _om(ERA5, params, len(points), len(hourly), (end - start).days + 1)


def iem_stations() -> list[dict]:
    j = json.loads(http(IEM_STATIONS))
    out = []
    for f in j["features"]:
        pr = f["properties"]
        lon, lat = f["geometry"]["coordinates"][:2]
        out.append({"id": f["id"], "name": pr.get("sname"), "lat": lat, "lon": lon, "elev_m": pr.get("elevation"),
                    "archive_begin": pr.get("archive_begin"), "online": pr.get("online")})
    return out


METAR_FIELDS = ["tmpc", "sknt", "gust", "vsby", "wxcodes"]   # never p01m (rain): placeholder in the Indian feed


def iem_metar(station: str, start: date, end: date) -> tuple[list[dict], str]:
    """Routine + special METARs, UTC times, from start 00Z to end 00Z (end exclusive in IEM)."""
    q = [("station", station)] + [("data", f) for f in METAR_FIELDS] + [
        ("year1", start.year), ("month1", start.month), ("day1", start.day),
        ("year2", end.year), ("month2", end.month), ("day2", end.day),
        ("tz", "Etc/UTC"), ("format", "onlycomma"), ("latlon", "no"), ("elev", "no"), ("missing", "M"),
        ("trace", "T"), ("direct", "no"), ("report_type", "3"), ("report_type", "4")]
    url = IEM_ASOS + "?" + urllib.parse.urlencode(q)
    if "p01m" in url:
        raise HistoryError("METAR rainfall must not be requested")
    text = http(url, timeout=180).decode()
    return list(csv.DictReader(io.StringIO(text))), url


def imd_year(year: int) -> bytes:
    return http(IMD_RF25, data=urllib.parse.urlencode({"RF25": year}).encode(), timeout=600, tries=6)
