"""Read-only HTTP client for the CORE public API (/api/v1).

This is the ONLY way api-v2 obtains data from CORE. It never imports CORE code and never
touches CORE files (docs/CORE_BOUNDARY.md). Errors are raised, never replaced with
substitute data.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

from .config import settings


class CoreError(RuntimeError):
    def __init__(self, path: str, status: int | None, message: str):
        super().__init__(f"CORE {path}: {message}")
        self.path = path
        self.status = status
        self.message = message


class _TTLCache:
    """Small in-process cache with one in-flight fetch per key (no stampede on cold start)."""

    def __init__(self) -> None:
        self._data: dict[str, tuple[float, Any]] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    async def get(self, key: str, ttl: float, fetch):
        hit = self._data.get(key)
        if hit and hit[0] > time.time():
            return hit[1]
        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            hit = self._data.get(key)
            if hit and hit[0] > time.time():
                return hit[1]
            value = await fetch()
            self._data[key] = (time.time() + ttl, value)
            return value

    def clear(self) -> None:
        self._data.clear()


cache = _TTLCache()


class CoreClient:
    def __init__(self, base: str | None = None, transport: httpx.AsyncBaseTransport | None = None):
        self.base = (base or settings.core_api_base).rstrip("/")
        self._transport = transport

    async def _get(self, path: str, params: dict | None = None, timeout: float = 60.0) -> Any:
        params = {k: v for k, v in (params or {}).items() if v is not None}
        r = None
        for attempt in (1, 2):  # one retry on a transport error (connection reset/refused, timeout); never on an HTTP error
            try:
                async with httpx.AsyncClient(timeout=timeout, transport=self._transport, headers={"user-agent": "bwi-api-v2"}) as c:
                    r = await c.get(f"{self.base}{path}", params=params)
                break
            except httpx.TransportError as e:
                if attempt == 2:
                    raise CoreError(path, None, f"{type(e).__name__}: {e}") from e
                await asyncio.sleep(1.0)
            except httpx.HTTPError as e:
                raise CoreError(path, None, f"{type(e).__name__}: {e}") from e
        if r.status_code != 200:
            raise CoreError(path, r.status_code, r.text[:300])
        return r.json()

    async def dashboard(self, lat: float, lon: float, name: str | None = None, taluka: str | None = None) -> dict:
        key = f"dash:{lat:.4f}:{lon:.4f}:{name}:{taluka}"
        return await cache.get(key, settings.point_ttl, lambda: self._get("/dashboard", {"lat": lat, "lon": lon, "name": name, "taluka": taluka}))

    async def grid_point(self, lat: float, lon: float) -> dict:
        key = f"gp:{lat:.3f}:{lon:.3f}"
        return await cache.get(key, settings.point_ttl, lambda: self._get("/grid/point", {"lat": lat, "lon": lon}))

    async def grid_meta(self) -> dict:
        return await cache.get("gridmeta", settings.point_ttl, lambda: self._get("/grid/meta"))

    async def states(self) -> list[dict]:
        return await cache.get("states", 24 * 3600, lambda: self._get("/geo/states"))

    async def region_state(self, slug: str) -> dict:
        return await cache.get(f"state:{slug}", settings.region_ttl, lambda: self._get(f"/region/state/{slug}", timeout=150.0))

    async def warnings_national(self) -> list[dict]:
        return await cache.get("warn:nat", settings.point_ttl, lambda: self._get("/warnings", {"national": "true"}))

    async def health(self) -> dict:
        return await self._get("/health", timeout=20.0)


core = CoreClient()
