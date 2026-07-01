"""Tests for the route optimiser (2-opt + capacity), importing script_json
(the demand-model + routing module shared by the dashboard and offline
solver). Requires demand_model.pkl on disk."""

import itertools
import random

import pytest

pytest.importorskip("xgboost")
script_json = pytest.importorskip("script_json")

m = script_json


def test_two_opt_never_increases_travel_time():
    """2-opt must return an ordering no longer than the input, for many seeds."""
    stops = m.STOP_IDS
    rng = random.Random(0)
    for _ in range(40):
        k = rng.randint(4, 8)
        order = rng.sample(stops, k)
        before = m.path_time(order)
        after = m.path_time(m.two_opt(order))
        assert after <= before + 1e-9


def test_two_opt_keeps_start_fixed():
    order = m.STOP_IDS[:6]
    assert m.two_opt(order)[0] == order[0]


def test_two_opt_is_near_optimal_small_case():
    """On small routes, 2-opt should match brute-force optimal closely."""
    stops = m.STOP_IDS
    rng = random.Random(1)
    gaps = []
    for _ in range(15):
        order = rng.sample(stops, 6)
        start, rest = order[0], order[1:]
        opt = min(m.path_time([start, *p]) for p in itertools.permutations(rest))
        got = m.path_time(m.two_opt(order))
        if opt > 0:
            gaps.append((got - opt) / opt)
    assert max(gaps) < 0.20          # worst case within 20%
    assert sum(gaps) / len(gaps) < 0.05   # mean within 5%


def test_two_opt_handles_tiny_routes():
    assert m.two_opt([]) == []
    assert m.two_opt(["S01"]) == ["S01"]
    assert m.two_opt(["S01", "S02"]) == ["S01", "S02"]


def _uniform_demand(value=50.0):
    return {sid: value for sid in m.STOP_IDS}


def test_greedy_respects_capacity():
    routes = m.greedy_route(_uniform_demand(80.0))
    for r in routes:
        assert r["total_demand"] <= m.BUS_CAPACITY + 1e-6


def test_greedy_bus_count_bounded():
    routes = m.greedy_route(_uniform_demand(80.0))
    assert 0 < len(routes) <= m.N_BUSES


def test_greedy_no_duplicate_stops_across_routes():
    routes = m.greedy_route(_uniform_demand(80.0))
    seen = [s for r in routes for s in r["route_stops"]]
    assert len(seen) == len(set(seen))


def test_greedy_empty_demand_returns_no_routes():
    assert m.greedy_route({sid: 0.0 for sid in m.STOP_IDS}) == []


def test_greedy_never_visits_stops_below_min_demand():
    """Stops below MIN_DEMAND_VISIT boardings must never appear in a route,
    even when other stops have plenty of demand to route towards."""
    demand = {sid: 0.0 for sid in m.STOP_IDS}
    # Only give demand to every other stop; the rest sit below the threshold.
    above_threshold = m.STOP_IDS[::2]
    for sid in above_threshold:
        demand[sid] = 50.0
    below_threshold = [sid for sid in m.STOP_IDS if sid not in above_threshold]

    routes = m.greedy_route(demand)
    visited = {s for r in routes for s in r["route_stops"]}
    assert visited.issubset(set(above_threshold))
    assert not visited & set(below_threshold)


def test_greedy_respects_route_budget():
    """No route's travel time may exceed ROUTE_BUDGET_MIN, even under demand
    high enough that every stop would otherwise be worth visiting."""
    routes = m.greedy_route(_uniform_demand(200.0))
    for r in routes:
        assert m.path_time(r["route_stops"]) <= m.ROUTE_BUDGET_MIN + 1e-9


# ── Unity bridge contract (build_unity_path / ml_to_unity / q_corners) ──────


def test_ml_to_unity_mapping_is_a_bijection_over_all_stops():
    """Every ML stop ID must have a Unity equivalent, and no two ML stops may
    map to the same Unity stop (the mapping is a 1:1 axis-flip, per README)."""
    mapped = [m.ml_to_unity(sid) for sid in m.STOP_IDS]
    assert len(mapped) == len(m.STOP_IDS)
    assert len(set(mapped)) == len(mapped)


def test_build_unity_path_starts_at_the_first_stop():
    route = m.STOP_IDS[:4]
    items = m.build_unity_path(route)
    assert items[0] == m.ml_to_unity(route[0])


def test_build_unity_path_visits_every_stop_in_order():
    """Every ML stop in the route must appear, as its Unity equivalent, in
    the same relative order in the bridged output (Q corners may be
    interleaved between them, but stop order itself must be preserved)."""
    route = m.STOP_IDS[:5]
    items = m.build_unity_path(route)
    expected_unity_stops = [m.ml_to_unity(sid) for sid in route]
    positions = [items.index(u) for u in expected_unity_stops]
    assert positions == sorted(positions)


def test_build_unity_path_empty_route_returns_empty():
    assert m.build_unity_path([]) == []
