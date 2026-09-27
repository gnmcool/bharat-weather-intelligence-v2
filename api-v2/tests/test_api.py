import json
import re

from conftest import load

AHD = dict(lat=23.0225, lon=72.5714, name="Ahmedabad")
SHIMLA = dict(lat=31.1048, lon=77.1734, name="Shimla")
CHENNAI = dict(lat=13.0827, lon=80.2707, name="Chennai")
GUW = dict(lat=26.1445, lon=91.7362, name="Guwahati")
UTK = dict(lat=31.0033, lon=78.5841, name="Uttarkashi")


def _events(client, p):
    r = client.get("/api/v2/events", params=p)
    assert r.status_code == 200, r.text
    return r.json()


# ---- events ---------------------------------------------------------------------------------

def test_no_event_location(client):
    d = _events(client, AHD)
    assert d["events"] == [] and d["official_alerts"] == []
    assert d["what_to_know"]["message"] == "No significant weather event detected."


def test_events_mirror_core_risks_exactly(client):
    for name, p in (("shimla", SHIMLA), ("chennai", CHENNAI), ("guwahati", GUW), ("uttarkashi", UTK)):
        dash = load(f"dashboard_{name}")
        d = _events(client, p)
        core = {r["id"]: r for r in dash["risks"] if r["level"] >= 1}
        assert {e["type"] for e in d["events"]} == set(core), name
        for e in d["events"]:
            r = core[e["type"]]
            assert e["severity"]["level"] == r["level"]            # severity = CORE level
            assert e["start"] == r["period_start"] and e["end"] == r["period_end"]  # timestamps unchanged
            assert e["supporting_risk"]["criterion"] == r["criterion"]
            if r["period_start"] is None:
                assert e["timing_note"]


def test_multiple_risks_and_priority_order(client):
    d = _events(client, UTK)
    pri = [i["priority"] for i in d["what_to_know"]["items"]]
    assert pri == sorted(pri)
    assert pri[0] == 1  # official alert first
    assert len(d["events"]) >= 4
    lv = [e["severity"]["level"] for e in d["events"]]
    assert lv == sorted(lv, reverse=True)


def test_official_alerts_separate_and_not_events(client):
    for p in (CHENNAI, GUW, UTK):
        d = _events(client, p)
        assert d["official_alerts"], p
        assert all(a["classification"] == "official" for a in d["official_alerts"])
        # No system assessment carries the official classification or wording.
        for e in d["events"]:
            assert e["classification"] == "system"
            assert "official warning" not in e["title"].lower()
            assert e["classification_label"] == "System assessment — not an official warning"


def test_model_agreement_is_count_not_probability(client):
    d = _events(client, UTK)
    by = {e["type"]: e for e in d["events"]}
    assert by["rain"]["model_agreement"]["text"] == "Model agreement: 3 of 3"
    assert by["flood"]["model_agreement"]["text"] == "Model agreement: 0 of 3"
    assert by["fog"]["model_agreement"]["assessed"] is False
    blob = json.dumps(d)
    assert not re.search(r"\d+\s?%\s*(confidence|probab|chance)", blob, re.I)
    for e in d["events"]:
        assert "score" not in e["model_agreement"]


def test_convective_titles_say_model_derived(client):
    d = _events(client, SHIMLA)
    t = {e["type"]: e["title"] for e in d["events"]}
    assert t["thunderstorm"] == "Thunderstorm potential — model derived"
    assert t["lightning"] == "Lightning potential — model derived"


# ---- evidence -------------------------------------------------------------------------------

def _ev(client, p, risk):
    r = client.get("/api/v2/evidence", params={**p, "risk": risk})
    assert r.status_code == 200, r.text
    return r.json()


def test_evidence_section_order_fixed(client):
    for risk in ("rain", "fog", "thunderstorm", "cold"):
        e = _ev(client, UTK, risk)
        assert e["section_order"] == ["detected", "when", "model_agreement", "forecast_range", "normal_departure",
                                      "earth2studio", "satellite", "official", "rule", "provenance"]
        assert list(e["sections"]) == e["section_order"]


def test_rain_evidence_matches_core_data(client):
    dash = load("dashboard_uttarkashi")
    e = _ev(client, UTK, "rain")["sections"]
    day = next(r for r in dash["daily"] if r["date"] == "2026-09-27")
    fr = e["forecast_range"]
    assert fr["per_model"]["ECMWF"]["value"] == day["models"]["ecmwf_ifs025"]["precip"]
    assert fr["per_model"]["GFS"]["value"] == day["models"]["gfs_seamless"]["precip"]
    assert fr["per_model"]["ICON"]["value"] == day["models"]["icon_seamless"]["precip"]
    assert fr["min"] == 52.8 and fr["max"] == 82.1 and "model spread" in fr["note"]
    nd = e["normal_departure"]
    assert nd["forecast"]["value"] == day["precipitation_sum"] and nd["normal"]["value"] == day["normal_precip"]
    assert "NASA POWER" in nd["baseline"]["label"] and "not IMD" in nd["baseline"]["label"]
    assert e["official"]["status"] == "OFFICIAL ALERT"
    assert e["official"]["alerts"][0]["event"] == "Very Heavy Rain"


def test_cold_range_is_window_min_per_model(client):
    dash = load("dashboard_uttarkashi")
    e = _ev(client, UTK, "cold")["sections"]["forecast_range"]
    days = [r for r in dash["daily"] if "2026-09-27" <= r["date"] <= "2026-10-03"]
    assert e["per_model"]["ICON"]["value"] == min(r["models"]["icon_seamless"]["tmin"] for r in days)


def test_earth2studio_not_counted_as_model(client):
    e = _ev(client, UTK, "rain")["sections"]
    assert set(e["forecast_range"]["per_model"]) == {"ECMWF", "GFS", "ICON"}
    assert e["model_agreement"]["of"] == 3
    assert "NOT counted" in e["earth2studio"]["note"]
    assert e["earth2studio"]["available"] is True
    # E2S run 27 Sep 06Z starts after the IST day began: flagged partial, never presented as comparable.
    assert e["earth2studio"]["partial"] is True and "not comparable" in e["earth2studio"]["partial_note"]


def test_earth2studio_missing_is_reported_not_substituted(client):
    e = _ev(client, CHENNAI, "thunderstorm")["sections"]["earth2studio"]
    assert e["available"] is False and "unavailable" in e["reason"]


def test_satellite_never_confirms(client):
    for risk in ("rain", "flood", "fog", "drought", "heat"):
        s = _ev(client, UTK, risk)["sections"]["satellite"]
        assert "confirm" not in s["status"].lower()
        assert s["quantitative"] is False


def test_no_official_alert_state(client):
    e = _ev(client, SHIMLA, "thunderstorm")["sections"]["official"]
    assert e["status"] == "NO OFFICIAL ALERT" and e["alerts"] == []


def test_guwahati_flood_alert_linked_to_flood_not_thunderstorm(client):
    assert _ev(client, GUW, "flood")["sections"]["official"]["status"] == "OFFICIAL ALERT"
    ts = _ev(client, GUW, "thunderstorm")["sections"]["official"]
    assert ts["status"] == "NO OFFICIAL ALERT" and ts["other_alerts_at_location"]


def test_provenance_has_runs(client):
    p = _ev(client, UTK, "rain")["sections"]["provenance"]
    assert any(x["provider"] == "Open-Meteo" and x.get("run_detail") for x in p)
    assert any("Earth2Studio" in (x["provider"] or "") and x["run"] for x in p)


def test_unknown_risk_404(client):
    assert client.get("/api/v2/evidence", params={**AHD, "risk": "tornado"}).status_code == 404


def test_core_failure_is_502_without_substitute(client):
    r = client.get("/api/v2/events", params={"lat": 10.0, "lon": 76.0})
    assert r.status_code == 502
    assert r.json()["detail"]["note"] == "No substitute data is returned."


# ---- India risk counts ----------------------------------------------------------------------

def test_india_counts_reconcile_with_district_list(client):
    r = client.get("/api/v2/region/india/risks")
    assert r.status_code == 200, r.text
    d = r.json()
    for h in d["hazards"]:
        n = sum(1 for x in d["districts"] if x["levels"][h["id"]] >= 1)
        assert h["districts"] == n == h["watch"] + h["alert"] + h["severe"]
        assert sum(s["districts"] for s in h["by_state"]) == n


def test_india_counts_equal_core_state_levels(client):
    d = client.get("/api/v2/region/india/risks").json()
    utk = load("state_uttarakhand")
    ours = {x["id"]: x for x in d["districts"]}
    for x in utk["districts"]:
        assert ours[x["id"]]["levels"] == {k: x["levels"][k] for k in ("rain", "heat", "cold", "wind")}


def test_india_failed_state_reported(client):
    d = client.get("/api/v2/region/india/risks").json()
    assert d["coverage"]["complete"] is False
    assert [s["state_slug"] for s in d["coverage"]["states_failed"]] == ["sikkim"]
    assert d["coverage"]["districts_received"] == 15


def test_india_no_taluka_and_not_counted_listed(client):
    d = client.get("/api/v2/region/india/risks").json()
    assert d["unit"] == "district"
    assert {x["id"] for x in d["not_counted"]} >= {"thunderstorm", "flood", "fog"}
    assert d["classification_label"].startswith("System")
