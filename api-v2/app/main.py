"""Bharat Weather Intelligence V2 API (/api/v2).

A separate service. It reads CORE only through CORE's public /api/v1 over HTTP and never
changes CORE. Endpoints: /events, /evidence, /region/india/risks, /health.
"""
from __future__ import annotations

import asyncio

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .catalogue import TITLE
from .config import settings
from .core_client import CoreError, cache, core
from .events import build_events
from .evidence import build_evidence
from .region import build_india_risks

VERSION = "m2"
app = FastAPI(title="Bharat Weather Intelligence V2 API", version=VERSION,
              description="Events, evidence and India district risk counts built on CORE /api/v1 (read-only).")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["GET"], allow_headers=["*"])


def _core_fail(e: CoreError):
    # No substitute data: the failure is reported with the CORE endpoint that failed.
    raise HTTPException(status_code=502, detail={"error": "CORE API request failed", "core_endpoint": e.path,
                                                 "core_status": e.status, "message": e.message,
                                                 "note": "No substitute data is returned."})


@app.get("/api/v2/health")
async def health():
    try:
        h = await core.health()
        return {"status": "ok", "version": VERSION, "core_api_base": core.base, "core": h}
    except CoreError as e:
        return JSONResponse(status_code=503, content={"status": "core_unreachable", "version": VERSION, "core_api_base": core.base, "error": e.message})


@app.get("/api/v2/events")
async def events(lat: float = Query(..., ge=-90, le=90), lon: float = Query(..., ge=-180, le=180),
                 name: str | None = None, taluka: str | None = None):
    try:
        dash = await core.dashboard(lat, lon, name, taluka)
    except CoreError as e:
        _core_fail(e)
    return build_events(dash)


@app.get("/api/v2/evidence")
async def evidence(lat: float = Query(..., ge=-90, le=90), lon: float = Query(..., ge=-180, le=180),
                   risk: str = Query(..., description="CORE risk id, e.g. rain"), name: str | None = None, taluka: str | None = None):
    if risk not in TITLE:
        raise HTTPException(status_code=404, detail=f"Unknown risk '{risk}'. Known: {', '.join(TITLE)}")
    dash_t = asyncio.create_task(core.dashboard(lat, lon, name, taluka))
    gp_t = asyncio.create_task(core.grid_point(lat, lon))
    try:
        dash = await dash_t
    except CoreError as e:
        gp_t.cancel()
        _core_fail(e)
    gp, gp_err = None, None
    try:
        gp = await gp_t
    except CoreError as e:
        gp_err = e.message[:200]
    try:
        return build_evidence(risk, dash, gp, gp_err)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"CORE returned no '{risk}' risk for this location.")


_india: dict = {}


@app.get("/api/v2/region/india/risks")
async def india_risks():
    import time
    hit = _india.get("v")
    if hit and hit[0] > time.time():
        return hit[1]
    lock = _india.setdefault("lock", asyncio.Lock())
    async with lock:
        hit = _india.get("v")
        if hit and hit[0] > time.time():
            return hit[1]
        try:
            out = await build_india_risks(core)
        except CoreError as e:
            _core_fail(e)
        ttl = settings.region_ttl if out["coverage"]["complete"] else 60
        _india["v"] = (time.time() + ttl, out)
        return out


@app.get("/")
async def root():
    return {"service": "bwi-api-v2", "version": VERSION, "endpoints": ["/api/v2/health", "/api/v2/events", "/api/v2/evidence", "/api/v2/region/india/risks"],
            "core_api_base": core.base, "docs": "/docs"}


def _reset_for_tests():
    cache.clear()
    _india.clear()
