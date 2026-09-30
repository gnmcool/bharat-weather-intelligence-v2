"""GRIB decoding and structural / final-data validation (D2 plan §3, §5.6, §6).

A file is decoded completely with ecCodes. Each message's time is its GRIB *validity* date/time; the base-time/step
encoding is recorded, never assumed. Validation never repairs anything: every failing check is reported by name and
the retrieval is refused by the caller.
"""
from __future__ import annotations

import hashlib
import pathlib
from collections import Counter
from datetime import datetime

import numpy as np

from era5_common import (AREA, FINAL_EXPVER, GRID_STEP, SHORT_NAME, UNITS, UTC, expected_stamps)

ENCODING_KEYS = ("edition", "dataType", "class", "stream", "typeOfLevel", "packingType", "bitsPerValue")


class GribDecodeError(RuntimeError):
    """The file is not a complete, decodable GRIB file (truncated, corrupt or empty)."""


def _get(h, key):
    import eccodes as ec
    try:
        if not ec.codes_is_defined(h, key):
            return None
        return ec.codes_get(h, key)
    except Exception:  # noqa: BLE001 — an undecodable key is recorded as missing
        return None


def decode(path: pathlib.Path) -> dict:
    """Decode every message. Returns messages (metadata per message) and values (n_messages x n_points, float64,
    NaN where the GRIB bitmap marks a value missing)."""
    import eccodes as ec
    path = pathlib.Path(path)
    raw = path.read_bytes()
    msgs, vals = [], []
    try:
        with open(path, "rb") as f:
            while True:
                h = ec.codes_grib_new_from_file(f)
                if h is None:
                    break
                try:
                    m = {k: _get(h, k) for k in ("shortName", "paramId", "units", "expver", "validityDate",
                                                  "validityTime", "dataDate", "dataTime", "stepRange", "gridType",
                                                  "Ni", "Nj", "iDirectionIncrementInDegrees",
                                                  "jDirectionIncrementInDegrees", "latitudeOfFirstGridPointInDegrees",
                                                  "longitudeOfFirstGridPointInDegrees",
                                                  "latitudeOfLastGridPointInDegrees",
                                                  "longitudeOfLastGridPointInDegrees", "numberOfDataPoints",
                                                  "binaryScaleFactor", "decimalScaleFactor", "bitmapPresent",
                                                  "missingValue", *ENCODING_KEYS)}
                    v = np.asarray(ec.codes_get_values(h), dtype=np.float64)
                    if m.get("bitmapPresent"):
                        v = np.where(v == float(m["missingValue"]), np.nan, v)
                finally:
                    ec.codes_release(h)
                m["packing_step"] = packing_step(m)
                m["stamp"] = validity_stamp(m)
                msgs.append(m)
                vals.append(v)
    except GribDecodeError:
        raise
    except Exception as e:  # noqa: BLE001 — any ecCodes failure means the file is not usable
        raise GribDecodeError(f"{path.name}: GRIB decode failed: {type(e).__name__}: {str(e)[:200]}") from None
    if not msgs:
        raise GribDecodeError(f"{path.name}: no GRIB messages")
    sizes = {len(v) for v in vals}
    if len(sizes) != 1:
        raise GribDecodeError(f"{path.name}: messages have different numbers of values {sorted(sizes)}")
    return {"name": path.name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "messages": msgs,
            "values": np.vstack(vals)}


def packing_step(m: dict) -> float | None:
    """Decoding precision of a simple-packed message: 2**E / 10**D (E binary, D decimal scale factor)."""
    e, d = m.get("binaryScaleFactor"), m.get("decimalScaleFactor")
    if e is None or d is None:
        return None
    return float(2.0 ** int(e) / 10.0 ** int(d))


def validity_stamp(m: dict) -> datetime | None:
    d, t = m.get("validityDate"), m.get("validityTime")
    if d is None or t is None:
        return None
    t = int(t)
    return datetime.strptime(f"{int(d):08d}", "%Y%m%d").replace(hour=t // 100, minute=t % 100, tzinfo=UTC)


def grid_axes(m: dict) -> tuple[np.ndarray, np.ndarray]:
    """Latitudes (north -> south) and longitudes (west -> east) of a regular_ll message."""
    lat0, lon0 = float(m["latitudeOfFirstGridPointInDegrees"]), float(m["longitudeOfFirstGridPointInDegrees"])
    ni, nj = int(m["Ni"]), int(m["Nj"])
    step = float(GRID_STEP)
    return lat0 - step * np.arange(nj), lon0 + step * np.arange(ni)


def _grid_signature(m: dict) -> tuple:
    return tuple(m.get(k) for k in ("gridType", "Ni", "Nj", "iDirectionIncrementInDegrees",
                                    "jDirectionIncrementInDegrees", "latitudeOfFirstGridPointInDegrees",
                                    "longitudeOfFirstGridPointInDegrees", "latitudeOfLastGridPointInDegrees",
                                    "longitudeOfLastGridPointInDegrees"))


def expected_grid(area: list[float] | None = None) -> tuple:
    n, w, s, e = AREA if area is None else area
    ni = int(round((e - w) / float(GRID_STEP))) + 1
    nj = int(round((n - s) / float(GRID_STEP))) + 1
    return ("regular_ll", ni, nj, float(GRID_STEP), float(GRID_STEP), float(n), float(w), float(s), float(e))


def _same_grid(sig: tuple, want: tuple) -> bool:
    if sig[0] != want[0] or sig[1] != want[1] or sig[2] != want[2]:
        return False
    return all(v is not None and abs(float(v) - float(w)) < 1e-6 for v, w in zip(sig[3:], want[3:]))


def validate(decoded: dict, request: dict, role: str) -> dict:
    """§5.6 structural checks and the §6 expver acceptance test for one downloaded file.

    Returns {"ok": bool, "problems": [...], "expver_ok": bool, "summary": {...}}. Every problem names its check."""
    msgs = decoded["messages"]
    problems = []
    short = Counter(m.get("shortName") for m in msgs)
    if set(short) != {SHORT_NAME}:
        problems.append(f"[variable] {role}: shortName {dict(short)} (expected only '{SHORT_NAME}')")
    units = Counter(m.get("units") for m in msgs)
    if set(units) != {UNITS}:
        problems.append(f"[units] {role}: units {dict(units)} (expected only '{UNITS}')")
    stamps = [m["stamp"] for m in msgs]
    want = expected_stamps(request)
    counts = Counter(stamps)
    dup = sorted(s.isoformat() for s, c in counts.items() if s is not None and c > 1)
    missing = sorted(s.isoformat() for s in set(want) - set(counts))
    extra = sorted(str(s) for s in set(counts) - set(want))
    if dup:
        problems.append(f"[stamps] {role}: duplicated stamps {dup[:5]} ({len(dup)})")
    if missing:
        problems.append(f"[stamps] {role}: missing stamps {missing[:5]} ({len(missing)})")
    if extra:
        problems.append(f"[stamps] {role}: unexpected stamps {extra[:5]} ({len(extra)})")
    want_grid = expected_grid(request.get("area"))
    grids = Counter(_grid_signature(m) for m in msgs)
    if len(grids) != 1 or not _same_grid(next(iter(grids)), want_grid):
        problems.append(f"[grid] {role}: grid {list(grids)[:2]} differs from the requested 0.25° area {want_grid}")
    if decoded["values"].shape[1] != want_grid[1] * want_grid[2]:
        problems.append(f"[grid] {role}: {decoded['values'].shape[1]} values per message, "
                        f"expected {want_grid[1] * want_grid[2]}")
    exp = Counter(m.get("expver") for m in msgs)
    expver_ok = set(exp) == {FINAL_EXPVER}
    if not expver_ok:
        problems.append(f"[expver] {role}: expver {dict((str(k), v) for k, v in exp.items())} — every value must be "
                        f"'{FINAL_EXPVER}' (final ERA5); ERA5T or a missing expver refuses the retrieval")
    summary = {"messages": len(msgs), "stamps_expected": len(want), "expver": {str(k): v for k, v in exp.items()},
               "encoding": {k: sorted({str(m.get(k)) for m in msgs}) for k in ENCODING_KEYS},
               "base_times": sorted({f"{m.get('dataTime')}" for m in msgs}),
               "step_ranges": sorted({str(m.get("stepRange")) for m in msgs}),
               "missing_values": int(np.isnan(decoded["values"]).sum()),
               "negative_values": int((decoded["values"] < 0).sum()),
               "packing_steps": sorted({m["packing_step"] for m in msgs if m["packing_step"] is not None})}
    return {"ok": not problems, "problems": problems, "expver_ok": expver_ok, "summary": summary}
