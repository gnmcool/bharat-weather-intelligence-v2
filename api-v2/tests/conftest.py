"""Offline tests: CORE responses are captured fixtures served by an httpx mock transport."""
import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

FX = Path(__file__).parent / "fixtures"
PLACES = {  # lat → fixture name
    "23.0225": "ahmedabad", "31.1048": "shimla", "13.0827": "chennai", "26.1445": "guwahati", "31.0033": "uttarkashi",
}


def load(name: str):
    return json.loads((FX / f"{name}.json").read_text())


def _handler(request: httpx.Request) -> httpx.Response:
    p, q = request.url.path, request.url.params
    base = "/api/v1"
    if p == f"{base}/dashboard":
        place = PLACES.get(q["lat"])
        return httpx.Response(200, json=load(f"dashboard_{place}")) if place else httpx.Response(500, text="no fixture")
    if p == f"{base}/grid/point":
        place = PLACES.get(q["lat"])
        f = FX / f"gridpoint_{place}.json"
        return httpx.Response(200, json=json.loads(f.read_text())) if f.exists() else httpx.Response(503, text="grid store unavailable")
    if p == f"{base}/geo/states":
        return httpx.Response(200, json=[s for s in load("states") if s["state_slug"] in ("goa", "uttarakhand", "sikkim")])
    if p.startswith(f"{base}/region/state/"):
        slug = p.rsplit("/", 1)[1]
        f = FX / f"state_{slug}.json"
        return httpx.Response(200, json=json.loads(f.read_text())) if f.exists() else httpx.Response(504, text="timeout")
    if p == f"{base}/warnings":
        return httpx.Response(200, json=load("warnings_national"))
    if p == f"{base}/health":
        return httpx.Response(200, json={"status": "ok"})
    return httpx.Response(404, text="unknown")


@pytest.fixture()
def client(monkeypatch):
    from app import main
    from app.core_client import CoreClient
    mock = CoreClient(base="https://core.test/api/v1", transport=httpx.MockTransport(_handler))
    monkeypatch.setattr(main, "core", mock)
    main._reset_for_tests()
    return TestClient(main.app)
