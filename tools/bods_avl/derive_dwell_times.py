"""
derive_dwell_times.py — turn collected AVL into per-stop dwell profiles.

Reads avl_raw/*.csv (from collect_avl.py), snaps observations to the repo's
Ladywood stop coordinates, estimates dwell per vehicle per stop visit, and
aggregates to stop x hour x day-type profiles correlated against PROFILE_FN.

Run after >= ~2 weeks of collection:  py -3 derive_dwell_times.py
"""

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
_REPO_ROOT = HERE.parent.parent
RAW = HERE / "avl_raw"
STOPS_JSON = _REPO_ROOT / "data" / "gtfs" / "ladywood_stops.json"
SNAP_RADIUS_M = 50.0
MIN_DWELL_S, MAX_DWELL_S = 10, 300       # outside this: traffic hold / layover

def haversine_m(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    h = (math.sin((lat2 - lat1) * p / 2) ** 2 + math.cos(lat1 * p) *
         math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2)
    return 6371000 * 2 * math.asin(math.sqrt(h))

stops = json.loads(STOPS_JSON.read_text())
stops = [{"id": s.get("id") or s["stop_id"],
          "name": s.get("name", ""),
          "lat": s["lat"],
          "lon": s.get("lon") or s["lng"]}
         for s in (stops["stops"] if isinstance(stops, dict) else stops)]

files = sorted(RAW.glob("avl_*.csv"))
if not files:
    raise SystemExit("No AVL collected yet - run collect_avl.py first")
df = pd.concat(pd.read_csv(f) for f in files)
df["t"] = pd.to_datetime(df["recorded_at"], format="ISO8601", utc=True)
df = df.dropna(subset=["lat", "lon"]).sort_values(["vehicle_ref", "t"])
n_raw = len(df)
# SIRI feeds re-broadcast stale positions for parked/out-of-service vehicles
# ("ghosts" with hours-old RecordedAtTime). Dedup repeated records and drop
# anything that predates each day's first plausible service observation.
df = df.drop_duplicates(subset=["vehicle_ref", "recorded_at"])
day_start = df.groupby(df["t"].dt.date)["t"].transform("median")
df = df[(day_start - df["t"]).dt.total_seconds() < 6 * 3600]
print(f"{n_raw:,} raw -> {len(df):,} after ghost/dup filtering, "
      f"{df['vehicle_ref'].nunique()} vehicles, {len(files)} days")

# Snap each observation to nearest stop within radius
def nearest_stop(lat, lon):
    best, bd = None, SNAP_RADIUS_M
    for s in stops:
        d = haversine_m(lat, lon, s["lat"], s["lon"])
        if d < bd:
            best, bd = s["id"], d
    return best

df["stop"] = [nearest_stop(la, lo) for la, lo in zip(df["lat"], df["lon"])]
at_stop = df.dropna(subset=["stop"]).copy()

# Dwell = span of consecutive same-stop observations per vehicle
at_stop["visit"] = ((at_stop["stop"] != at_stop["stop"].shift()) |
                    (at_stop["vehicle_ref"] != at_stop["vehicle_ref"].shift())
                    ).cumsum()
visits = (at_stop.groupby(["visit", "vehicle_ref", "stop"])
          .agg(start=("t", "min"), end=("t", "max")).reset_index())
visits["dwell_s"] = (visits["end"] - visits["start"]).dt.total_seconds()
visits = visits[visits["dwell_s"].between(MIN_DWELL_S, MAX_DWELL_S)]
# SIRI timestamps are UTC; PROFILE_FN curves are local (Europe/London)
local = visits["start"].dt.tz_convert("Europe/London")
visits["hour"] = local.dt.hour
visits["day_type"] = np.where(local.dt.dayofweek >= 5, "weekend", "weekday")

profile = (visits.groupby(["stop", "day_type", "hour"])["dwell_s"]
           .median().round(1).reset_index())
profile.to_csv(HERE / "dwell_profiles.csv", index=False)

# Stop ranking by total dwell activity (the APC-proxy ranking)
rank = (visits.groupby("stop")["dwell_s"].sum().sort_values(ascending=False))
print("\nStop ranking by observed dwell activity (top = busiest):")
print(rank.to_string())
rank.to_json(HERE / "stop_ranking_observed.json")
print("\nWrote dwell_profiles.csv + stop_ranking_observed.json")
print("Next: correlate dwell_profiles vs PROFILE_FN per tier - the Birmingham "
      "shape check.")
