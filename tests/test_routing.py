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
