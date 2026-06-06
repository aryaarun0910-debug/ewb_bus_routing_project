"""bus2_route.py — outputs Bus 2's ML-predicted route for Unity."""
import sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import script_json as m   # safe: main block is guarded by __name__ == "__main__"

demand = m.predict_window_demand(m.TIME_WINDOW_HOURS, m.SCENARIO)
routes = m.greedy_route(demand)

items = m.build_unity_path(routes[1]["route_stops"]) if len(routes) > 1 else []
print(json.dumps({"items": items}))
