"""Tests for the route-quality and service-floor logic in
demand_route_optimizer.py — the pipeline script that produces the
README's headline "1.16% mean / 30.2% worst-case" optimality-gap claim
and the minimum-service-floor guarantee.

Importing this module trains the XGBoost demand model as a side effect
(no __main__ guard around data loading), so this import is slow
(several seconds) compared to the script_json-based tests in
test_routing.py. The scenario-simulation / file-writing section of the
script IS guarded behind `if __name__ == "__main__":`, so importing it
here does not run the 4-scenario simulation or write route_plan.json.
"""

import random

import pytest

pytest.importorskip("xgboost")
pytest.importorskip("pandas")
dro = pytest.importorskip("demand_route_optimizer")


def _uniform_demand(value=50.0):
    return {sid: value for sid in dro.STOP_IDS}


# ── route_gaps / optimal_path_time ──────────────────────────────────────────


def test_optimal_path_time_never_exceeds_the_given_order():
    """optimal_path_time is a true minimum over permutations with the start
    fixed, so it can never be worse than the time of the order handed in."""
    rng = random.Random(0)
    for _ in range(10):
        order = rng.sample(dro.STOP_IDS, rng.randint(3, 6))
        assert dro.optimal_path_time(order) <= dro.path_time(order) + 1e-9


def test_route_gaps_are_never_negative():
    """2-opt can't beat the brute-force optimum, so every measured gap must
    be >= 0 (within floating-point tolerance)."""
    routes = dro.greedy_route(_uniform_demand(80.0))
    for gap in dro.route_gaps(routes):
        assert gap >= -1e-6


def test_route_gaps_skips_routes_under_three_stops():
    """route_gaps only evaluates routes with >= 3 stops (a 1- or 2-stop
    route has no ordering choice to be sub-optimal about)."""
    routes = [{"route_stops": ["S01"]}, {"route_stops": ["S01", "S02"]}]
    assert dro.route_gaps(routes) == []


# ── apply_service_floor ─────────────────────────────────────────────────────


def _empty_route_missing(stop_id):
    """A single-bus route plan that visits every stop except stop_id."""
    stops = [s for s in dro.STOP_IDS if s != stop_id]
    return [{
        "bus": 1,
        "route_stops": stops,
        "route_names": [dro.STOP_MAP[s]["name"] for s in stops],
        "stop_demand": {s: 10.0 for s in stops},
        "total_demand": 10.0 * len(stops),
        "route_time_min": dro.path_time(stops),
    }]


def test_service_floor_not_triggered_before_threshold():
    """A stop missed for fewer than SERVICE_FLOOR_WINDOWS consecutive windows
    must not be force-inserted yet."""
    target = dro.STOP_IDS[0]
    routes = _empty_route_missing(target)
    windows_since_served = {sid: 0 for sid in dro.STOP_IDS}

    additions = dro.apply_service_floor(routes, _uniform_demand(), windows_since_served)

    assert target not in additions
    assert target not in routes[0]["route_stops"]
    assert windows_since_served[target] == 1


def test_service_floor_force_inserts_after_threshold_breached():
    """Once a stop has been missed SERVICE_FLOOR_WINDOWS times, it must be
    force-added to a route and its counter reset to 0."""
    target = dro.STOP_IDS[0]
    routes = _empty_route_missing(target)
    windows_since_served = {sid: 0 for sid in dro.STOP_IDS}
    windows_since_served[target] = dro.SERVICE_FLOOR_WINDOWS - 1

    additions = dro.apply_service_floor(routes, _uniform_demand(), windows_since_served)

    assert target in additions
    assert target in routes[0]["route_stops"]
    assert windows_since_served[target] == 0


def test_service_floor_resets_counter_for_served_stops():
    """A stop already present in a route must have its miss-counter reset to
    0, regardless of its prior value."""
    routes = dro.greedy_route(_uniform_demand(80.0))
    served_stop = routes[0]["route_stops"][0]
    windows_since_served = {sid: 5 for sid in dro.STOP_IDS}

    dro.apply_service_floor(routes, _uniform_demand(), windows_since_served)

    assert windows_since_served[served_stop] == 0


def test_service_floor_is_noop_with_no_routes():
    """With zero routes there is nowhere to insert a floor stop, so the
    function must return no additions rather than error."""
    windows_since_served = {sid: dro.SERVICE_FLOOR_WINDOWS for sid in dro.STOP_IDS}
    additions = dro.apply_service_floor([], _uniform_demand(), windows_since_served)
    assert additions == []
