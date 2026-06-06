"""
script_json.py  —  ML Demand Prediction -> Unity Bus Route Path
===============================================================
Called by Unity's PythonStringList.cs for each bus.
Outputs:  {"items": ["S12", "Q23", "S10", "Q17", "S13", ...]}

Requirements:
  - demand_model.pkl must already exist (run demand_route_optimizer.py once first)
"""

import json
import pickle
from pathlib import Path

import networkx as nx
from sklearn.preprocessing import LabelEncoder

# ── CONFIG ────────────────────────────────────────────────────────────────────

PKL_PATH = Path(__file__).parent / "demand_model.pkl"

# Which bus route to output: 0 = Bus1, 1 = Bus2, 2 = Bus3
BUS_INDEX = 0

# Scenario conditions
SCENARIO = dict(
    day_type         = "weekday",
    month            = 9,
    weather          = "sunny",
    climate_event    = "none",
    special_event    = "none",
    temperature_c    = 19.0,
    wind_kmh         = 10.0,
    precipitation_mm = 0.0,
    is_school_term   = 1,
    is_uni_term      = 0,
)

# Hours to predict demand over (AM Peak = 07:00-09:00)
TIME_WINDOW_HOURS = list(range(7, 9))

# ── ML -> UNITY STOP ID MAPPING ───────────────────────────────────────────────
# Derived by matching ML stop coordinates to Unity scene positions.
# ML y-axis goes DOWN; Unity y-axis goes UP — so the mapping is non-trivial.
#
#  ML ID  | ML Name          | Unity ID | Unity pos
#  --------+------------------+----------+-----------
#  S01     | North Hub        | S12      | (5, 11)
#  S02     | Northwest End    | S11      | (1, 10)
#  S03     | Upper Junction   | S10      | (3,  8)
#  S04     | Northeast Pass   | S13      | (4,  9)
#  S05     | Far East End     | S14      | (8,  9)
#  S06     | West End         | S5       | (0,  7)
#  S07     | West Hub         | S9       | (3,  7)
#  S08     | City Centre      | S8       | (4,  6)
#  S09     | East Hub         | S15      | (7,  6)
#  S10     | Lower West End   | S4       | (0,  5)
#  S11     | South Junction   | S6       | (2,  4)
#  S12     | Southeast Cross  | S7       | (5,  4)
#  S13     | South End        | S3       | (1,  2)
#  S14     | Far South West   | S1       | (0,  0)
#  S15     | Far South East   | S2       | (5,  0)

ML_TO_UNITY = {
    "S01": "S12", "S02": "S11", "S03": "S10", "S04": "S13", "S05": "S14",
    "S06": "S5",  "S07": "S9",  "S08": "S8",  "S09": "S15", "S10": "S4",
    "S11": "S6",  "S12": "S7",  "S13": "S3",  "S14": "S1",  "S15": "S2",
}

# ── Q CORNER WAYPOINT MAPPING ─────────────────────────────────────────────────
# Derived geometrically from the Unity scene positions.
# Keys:   (unity_stop_a, unity_stop_b)
# Values: Q corners in order of travel from a -> b
# Reverse direction is handled automatically by q_corners().
#
ROAD_Q_WAYPOINTS = {
    # ML S01-S03  North Hub → Upper Junction        S12(5,11) → S10(3,8)
    ("S12", "S10"): [],

    # ML S01-S04  North Hub → Northeast Pass        S12(5,11) → S13(4,9)
    ("S12", "S13"): [],

    # ML S02-S03  NW End → Upper Junction           S11(1,10) → S10(3,8)
    ("S11", "S10"): ["Q23", "Q18"],   # right along y=10, then down to y=8

    # ML S03-S04  Upper Junction → Northeast Pass   S10(3,8)  → S13(4,9)
    ("S10", "S13"): ["Q17"],

    # ML S03-S07  Upper Junction → West Hub         S10(3,8)  → S9(3,7)
    ("S10", "S9"):  [],               # same x, direct

    # ML S04-S05  Northeast Pass → Far East End     S13(4,9)  → S14(8,9)
    ("S13", "S14"): ["Q21", "Q22"],   # along y=9 eastward

    # ML S05-S09  Far East End → East Hub           S14(8,9)  → S15(7,6)
    ("S14", "S15"): ["Q15", "Q8"],

    # ML S06-S07  West End → West Hub               S5(0,7)   → S9(3,7)
    ("S5",  "S9"):  ["Q11"],          # along y=7

    # ML S06-S10  West End → Lower West End         S5(0,7)   → S4(0,5)
    ("S5",  "S4"):  [],               # same x, direct

    # ML S07-S08  West Hub → City Centre            S9(3,7)   → S8(4,6)
    ("S9",  "S8"):  ["Q12"],

    # ML S07-S11  West Hub → South Junction         S9(3,7)   → S6(2,4)
    ("S9",  "S6"):  ["Q9", "Q10"],    # down then left

    # ML S08-S09  City Centre → East Hub            S8(4,6)   → S15(7,6)
    ("S8",  "S15"): ["Q13", "Q14"],   # along y≈6-7

    # ML S08-S12  City Centre → Southeast Cross     S8(4,6)   → S7(5,4)
    ("S8",  "S7"):  ["Q6"],

    # ML S09-S12  East Hub → Southeast Cross        S15(7,6)  → S7(5,4)
    ("S15", "S7"):  ["Q7"],

    # ML S10-S11  Lower West End → South Junction   S4(0,5)   → S6(2,4)
    ("S4",  "S6"):  ["Q5"],

    # ML S11-S12  South Junction → Southeast Cross  S6(2,4)   → S7(5,4)
    ("S6",  "S7"):  ["Q4"],           # along y=4

    # ML S11-S13  South Junction → South End        S6(2,4)   → S3(1,2)
    ("S6",  "S3"):  [],

    # ML S12-S15  SE Cross → Far South East         S7(5,4)   → S2(5,0)
    ("S7",  "S2"):  ["Q2"],           # along x=5

    # ML S13-S14  South End → Far South West        S3(1,2)   → S1(0,0)
    ("S3",  "S1"):  ["Q25"],

    # ML S13-S15  South End → Far South East        S3(1,2)   → S2(5,0)
    ("S3",  "S2"):  ["Q1"],
}

# ── ROAD NETWORK (must match demand_route_optimizer.py) ───────────────────────

STOPS = [
    {"id": "S01", "name": "North Hub",       "x": 5.8, "y": 0.5,  "importance": "major"},
    {"id": "S03", "name": "Upper Junction",  "x": 3.5, "y": 3.8,  "importance": "major"},
    {"id": "S07", "name": "West Hub",        "x": 3.5, "y": 4.9,  "importance": "major"},
    {"id": "S09", "name": "East Hub",        "x": 7.7, "y": 5.8,  "importance": "major"},
    {"id": "S04", "name": "Northeast Pass",  "x": 5.0, "y": 2.7,  "importance": "medium"},
    {"id": "S08", "name": "City Centre",     "x": 4.5, "y": 5.8,  "importance": "medium"},
    {"id": "S11", "name": "South Junction",  "x": 2.5, "y": 7.5,  "importance": "medium"},
    {"id": "S12", "name": "Southeast Cross", "x": 5.7, "y": 7.7,  "importance": "medium"},
    {"id": "S02", "name": "Northwest End",   "x": 1.4, "y": 1.5,  "importance": "minor"},
    {"id": "S05", "name": "Far East End",    "x": 8.8, "y": 2.8,  "importance": "minor"},
    {"id": "S06", "name": "West End",        "x": 0.4, "y": 4.9,  "importance": "minor"},
    {"id": "S10", "name": "Lower West End",  "x": 0.4, "y": 6.6,  "importance": "minor"},
    {"id": "S13", "name": "South End",       "x": 1.4, "y": 10.3, "importance": "minor"},
    {"id": "S14", "name": "Far South West",  "x": 0.4, "y": 11.5, "importance": "minor"},
    {"id": "S15", "name": "Far South East",  "x": 5.8, "y": 11.5, "importance": "minor"},
]

EDGES = [
    ("S01", "S03",  8), ("S01", "S04",  5), ("S02", "S03",  7),
    ("S03", "S04",  4), ("S03", "S07",  4), ("S04", "S05",  9),
    ("S05", "S09",  8), ("S06", "S07",  5), ("S06", "S10",  4),
    ("S07", "S08",  4), ("S07", "S11",  6), ("S08", "S09",  6),
    ("S08", "S12",  5), ("S09", "S12",  6), ("S10", "S11",  4),
    ("S11", "S12",  5), ("S11", "S13",  7), ("S12", "S15",  8),
    ("S13", "S14",  3), ("S13", "S15",  7),
]

STOP_MAP = {s["id"]: s for s in STOPS}
STOP_IDS = [s["id"] for s in STOPS]

G = nx.Graph()
for s in STOPS:
    G.add_node(s["id"])
for a, b, t in EDGES:
    G.add_edge(a, b, travel_time=t)

ALL_PATH_LENGTHS = dict(nx.all_pairs_dijkstra_path_length(G, weight="travel_time"))
ALL_PATH_NODES   = dict(nx.all_pairs_dijkstra_path(G, weight="travel_time"))

N_BUSES          = 3
ROUTE_BUDGET_MIN = 70
MIN_DEMAND_VISIT = 2.0

# ── LOAD MODEL ────────────────────────────────────────────────────────────────

with open(PKL_PATH, "rb") as f:
    _saved = pickle.load(f)

model        = _saved["model"]
encoders     = _saved["encoders"]
FEATURE_COLS = _saved["feature_cols"]


def _safe_encode(enc: LabelEncoder, value: str) -> int:
    if value in enc.classes_:
        return int(enc.transform([value])[0])
    fallback = "none" if "none" in enc.classes_ else enc.classes_[0]
    return int(enc.transform([fallback])[0])


# ── PREDICTION ────────────────────────────────────────────────────────────────

def predict_stop_demand(stop_id, hour, day_type, month, weather,
                        climate_event, special_event,
                        temperature_c, wind_kmh, precipitation_mm,
                        is_school_term, is_uni_term) -> float:
    s = STOP_MAP[stop_id]
    row = [
        _safe_encode(encoders["stop_id"],         stop_id),
        _safe_encode(encoders["stop_importance"],  s["importance"]),
        _safe_encode(encoders["day_type"],         day_type),
        _safe_encode(encoders["weather_type"],     weather),
        _safe_encode(encoders["climate_event"],    climate_event),
        _safe_encode(encoders["special_event"],    special_event),
        hour, month, temperature_c, wind_kmh, precipitation_mm,
        is_school_term, is_uni_term, s["x"], s["y"],
    ]
    return max(0.0, float(model.predict([row])[0]))


def predict_window_demand(hours: list, conditions: dict) -> dict:
    demand = {}
    for sid in STOP_IDS:
        total = sum(predict_stop_demand(sid, h, **conditions) for h in hours)
        demand[sid] = round(total, 1)
    return demand


# ── GREEDY ROUTE OPTIMIZER ────────────────────────────────────────────────────

def greedy_route(demand: dict) -> list:
    remaining = dict(demand)
    routes = []

    for bus_idx in range(N_BUSES):
        candidates = [(sid, d) for sid, d in remaining.items() if d >= MIN_DEMAND_VISIT]
        if not candidates:
            break

        start = max(candidates, key=lambda x: x[1])[0]
        route_stops  = [start]
        route_demand = {start: remaining.pop(start, 0)}
        route_time   = 0.0
        current      = start

        while True:
            best_sid, best_score, best_tt = None, -1.0, 0
            for sid, dem in remaining.items():
                if dem < MIN_DEMAND_VISIT:
                    continue
                tt = ALL_PATH_LENGTHS[current].get(sid, float("inf"))
                if route_time + tt > ROUTE_BUDGET_MIN:
                    continue
                score = dem / max(1.0, tt)
                if score > best_score:
                    best_score, best_sid, best_tt = score, sid, tt
            if best_sid is None:
                break
            route_stops.append(best_sid)
            route_demand[best_sid] = remaining.pop(best_sid, 0)
            route_time += best_tt
            current = best_sid

        routes.append({
            "bus":            bus_idx + 1,
            "route_stops":    route_stops,
            "total_demand":   round(sum(route_demand.values()), 1),
            "route_time_min": round(route_time, 1),
        })

    return routes


# ── FORMAT FOR UNITY ──────────────────────────────────────────────────────────

def ml_to_unity(stop_id: str) -> str:
    """Convert ML stop ID to Unity GameObject name using the position-derived mapping."""
    return ML_TO_UNITY[stop_id]


def q_corners(unity_a: str, unity_b: str) -> list:
    """Return Q corners between two Unity stop names, handling reverse direction."""
    if (unity_a, unity_b) in ROAD_Q_WAYPOINTS:
        return ROAD_Q_WAYPOINTS[(unity_a, unity_b)]
    if (unity_b, unity_a) in ROAD_Q_WAYPOINTS:
        return list(reversed(ROAD_Q_WAYPOINTS[(unity_b, unity_a)]))
    return []


def build_unity_path(route_stops: list) -> list:
    """
    Converts ML stop list to Unity path, inserting Q corners.
    Uses actual graph shortest path between consecutive route stops
    so multi-hop segments include all intermediate stops + Q corners.
    """
    if not route_stops:
        return []

    items = [ml_to_unity(route_stops[0])]

    for i in range(1, len(route_stops)):
        physical_path = ALL_PATH_NODES[route_stops[i - 1]][route_stops[i]]
        for j in range(1, len(physical_path)):
            seg_a = ml_to_unity(physical_path[j - 1])
            seg_b = ml_to_unity(physical_path[j])
            items.extend(q_corners(seg_a, seg_b))
            items.append(seg_b)

    return items


# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    demand = predict_window_demand(TIME_WINDOW_HOURS, SCENARIO)
    routes = greedy_route(demand)

    if BUS_INDEX < len(routes):
        items = build_unity_path(routes[BUS_INDEX]["route_stops"])
    else:
        items = []

    print(json.dumps({"items": items}))
