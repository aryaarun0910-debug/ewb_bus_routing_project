"""API contract tests for the FastAPI dashboard backend.
Requires demand_model.pkl + data/gtfs/road_paths.json + route_plan.json on disk."""

import pytest

pytest.importorskip("xgboost")
pytest.importorskip("fastapi")
api = pytest.importorskip("api")
from fastapi.testclient import TestClient  # noqa: E402

client = TestClient(api.app)


def test_stops_returns_all_15_with_static_features():
    r = client.get("/api/stops")
    assert r.status_code == 200
    stops = r.json()
    assert len(stops) == 15
    for s in stops:
        assert "stop_id" in s and "name" in s
        # Static features merged in from the lookup table.
        assert "imd_score" in s


def test_stops_handles_missing_static_data_as_null_not_nan():
    """A stop with a genuine data gap (e.g. no Census car_free_pct for its
    LSOA) must serialise as JSON null, not float('nan') — the raw response
    text must not contain the bare token 'NaN', which is not valid JSON and
    previously crashed this endpoint outright for stop S14."""
    r = client.get("/api/stops")
    assert r.status_code == 200
    assert "NaN" not in r.text


def test_roads_keys_are_sorted_pairs_with_geometry():
    r = client.get("/api/roads")
    assert r.status_code == 200
    roads = r.json()
    assert len(roads) > 0
    for key, geometry in roads.items():
        a, b = key.split("|")
        assert a <= b, f"key {key} is not a sorted pair"
        assert len(geometry) >= 2
        assert all(len(pt) == 2 for pt in geometry)  # [lng, lat]


def test_demand_returns_a_prediction_per_stop():
    r = client.get("/api/demand", params={"hour": 8, "weather": "sunny"})
    assert r.status_code == 200
    d = r.json()
    assert d["hour"] == 8
    assert len(d["predictions"]) == 15
    assert all(v >= 0 for v in d["predictions"].values())


def test_scenarios_is_a_non_empty_list_of_names():
    r = client.get("/api/scenarios")
    assert r.status_code == 200
    scenarios = r.json()
    assert isinstance(scenarios, list)
    assert len(scenarios) > 0


def test_routes_for_known_scenario_attaches_real_geometry():
    scenarios = client.get("/api/scenarios").json()
    scenario = scenarios[0]
    r = client.get(f"/api/routes/{scenario}/AM Peak")
    assert r.status_code == 200
    d = r.json()
    assert d["scenario"] == scenario
    assert d["window"] == "AM Peak"
    for route in d["routes"]:
        assert len(route["route_stops"]) >= 1
        assert len(route["geometry"]) >= len(route["route_stops"])


def test_routes_for_unknown_scenario_reports_available_options():
    r = client.get("/api/routes/Not A Real Scenario/AM Peak")
    assert r.status_code == 200
    d = r.json()
    assert d["error"] == "unknown scenario"
    assert len(d["available"]) > 0


def test_routes_for_unknown_window_reports_available_options():
    scenarios = client.get("/api/scenarios").json()
    scenario = scenarios[0]
    r = client.get(f"/api/routes/{scenario}/Brunch")
    assert r.status_code == 200
    d = r.json()
    assert d["error"] == "unknown window"
    assert len(d["available"]) > 0


def test_health_reports_loaded_artefacts():
    r = client.get("/api/health")
    assert r.status_code == 200
    d = r.json()
    assert d["status"] == "ok"
    assert d["stops"] == 15
    assert d["road_segments"] > 0
