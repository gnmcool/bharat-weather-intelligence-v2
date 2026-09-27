"""M3: data-quality notices, impact context, government count wording."""
import json
import re

from app.catalogue import CONTEXT, NOTICES

UTK = dict(lat=31.0033, lon=78.5841, name="Uttarkashi")
CHENNAI = dict(lat=13.0827, lon=80.2707, name="Chennai")
AHD = dict(lat=23.0225, lon=72.5714, name="Ahmedabad")
SHIMLA = dict(lat=31.1048, lon=77.1734, name="Shimla")

# Words that would turn context into an instruction (M3 brief §11).
IMPERATIVE = re.compile(r"\b(evacuate|spray|harvest|cancel|avoid|stay|go indoors|do not|don't|must|should|advised?|recommend)\b", re.I)


def test_context_catalogue_is_conditional_not_instructions():
    for hazard, texts in CONTEXT.items():
        for t in texts:
            assert not IMPERATIVE.search(t), (hazard, t)
            assert re.search(r"\bmay\b|relevant", t), (hazard, t)
    for n in NOTICES.values():
        assert not IMPERATIVE.search(n["text"]), n["text"]


def test_context_only_on_events(client):
    d = client.get("/api/v2/events", params=UTK).json()
    for e in d["events"]:
        c = e["context"]
        assert c["label"].startswith("Potential relevance") and "not an impact forecast" in c["label"]
        assert not IMPERATIVE.search(c["citizen"] + c["farmer"] + c["government"])
    assert client.get("/api/v2/events", params=AHD).json()["events"] == []


def test_elevation_notice_from_core_terrain(client):
    ids = lambda p: [n["id"] for n in client.get("/api/v2/events", params=p).json()["data_quality"]]
    assert "elevation" in ids(UTK) and "elevation" in ids(SHIMLA)
    assert "elevation" not in ids(AHD) and "elevation" not in ids(CHENNAI)


def test_chennai_core_inconsistency_recorded_not_corrected(client):
    d = client.get("/api/v2/events", params=CHENNAI).json()
    inc = [n for n in d["data_quality"] if n["id"] == "core_inconsistency"]
    assert [n["risk"] for n in inc] == ["heat"]
    assert inc[0]["core_level"] == "No risk"
    assert "heat" not in [e["type"] for e in d["events"]]  # CORE level kept: no heat event invented
    ev = client.get("/api/v2/evidence", params={**CHENNAI, "risk": "heat"}).json()
    assert ev["sections"]["detected"]["severity"]["level"] == 0
    assert "core_inconsistency" in [n["id"] for n in ev["data_quality"]]


def test_grid_vs_point_notice_when_e2s_shown(client):
    ev = client.get("/api/v2/evidence", params={**UTK, "risk": "cold"}).json()
    ids = [n["id"] for n in ev["data_quality"]]
    assert "grid_vs_point" in ids and "elevation" in ids
    ev = client.get("/api/v2/evidence", params={**CHENNAI, "risk": "thunderstorm"}).json()  # no grid point fixture
    assert "grid_vs_point" not in [n["id"] for n in ev["data_quality"]]


def test_region_wording_and_notices(client):
    d = client.get("/api/v2/region/india/risks").json()
    blob = json.dumps(d).lower()
    assert "affected district" not in blob
    assert d["statement"] == "District risk counts are based on the representative forecast point for each district. Conditions may vary within a district."
    for h in d["hazards"]:
        assert h["count_label"].startswith("districts with system-assessed")
    assert {n["status"] for n in d["not_counted"]} == {"Not currently included in district count"}
    ids = [n["id"] for n in d["data_quality"]]
    assert ids[:3] == ["incomplete_coverage", "representative_point", "incomplete_hazards"]  # fixture: sikkim fails
    cold = next(h for h in d["hazards"] if h["id"] == "cold")
    if cold["hills_districts"]:
        assert "elevation_districts" in ids
