"""
generate_map_dataset.py
=======================
Generates a synthetic passenger demand dataset for the abstract bus-network map.

15 stops (blue dots from the hand-drawn image) connected by a road graph.
Each stop is assigned an importance level (major / medium / minor) which
drives its base demand.  Weather, seasonal effects, climate events and
special events are all modelled so they can be used as ML features.

Output
------
  map_demand_dataset.csv  (~65 000 rows)

Columns
-------
  stop_id, stop_name, stop_x, stop_y, stop_importance,
  day_scenario, month, month_name, day_type,
  hour, time_label,
  weather_type, temperature_c, wind_kmh, precipitation_mm,
  climate_event, special_event,
  is_school_term, is_uni_term,
  boardings, alightings, net_flow, occupancy_pct
"""

import csv
import math
import random
from pathlib import Path

random.seed(42)

# ─────────────────────────────────────────────────────────────────────────────
# 1.  MAP TOPOLOGY  (matches the hand-drawn image)
# ─────────────────────────────────────────────────────────────────────────────
#
# Coordinate system: x right, y down  (normalised 0-10 grid)
# Importance determines base demand traffic:
#   major  ≈ 67-90 boardings/hour at AM peak weekday
#   medium ≈ 30-45
#   minor  ≈  7-17

STOPS = [
    # ── Major hubs (high traffic) ─────────────────────────────────────────────
    {"id": "S01", "name": "North Hub",        "x": 5.8, "y": 0.5,  "importance": "major",  "base": 94},
    {"id": "S03", "name": "Upper Junction",   "x": 3.5, "y": 3.8,  "importance": "major",  "base": 96},
    {"id": "S07", "name": "West Hub",         "x": 3.5, "y": 4.9,  "importance": "major",  "base": 92},
    {"id": "S09", "name": "East Hub",         "x": 7.7, "y": 5.8,  "importance": "major",  "base": 94},

    # ── Medium stops ──────────────────────────────────────────────────────────
    {"id": "S04", "name": "Northeast Pass",   "x": 5.0, "y": 2.7,  "importance": "medium", "base": 48},
    {"id": "S08", "name": "City Centre",      "x": 4.5, "y": 5.8,  "importance": "medium", "base": 47},
    {"id": "S11", "name": "South Junction",   "x": 2.5, "y": 7.5,  "importance": "medium", "base": 40},
    {"id": "S12", "name": "Southeast Cross",  "x": 5.7, "y": 7.7,  "importance": "medium", "base": 42},

    # ── Minor endpoints (low traffic) ─────────────────────────────────────────
    {"id": "S02", "name": "Northwest End",    "x": 1.4, "y": 1.5,  "importance": "minor",  "base": 16},
    {"id": "S05", "name": "Far East End",     "x": 8.8, "y": 2.8,  "importance": "minor",  "base": 10},
    {"id": "S06", "name": "West End",         "x": 0.4, "y": 4.9,  "importance": "minor",  "base":  9},
    {"id": "S10", "name": "Lower West End",   "x": 0.4, "y": 6.6,  "importance": "minor",  "base":  8},
    {"id": "S13", "name": "South End",        "x": 1.4, "y": 10.3, "importance": "minor",  "base": 14},
    {"id": "S14", "name": "Far South West",   "x": 0.4, "y": 11.5, "importance": "minor",  "base":  7},
    {"id": "S15", "name": "Far South East",   "x": 5.8, "y": 11.5, "importance": "minor",  "base":  9},
]

# Road edges (stop_a, stop_b, travel_time_minutes)
EDGES = [
    ("S01", "S03",  8),   # top loop direct
    ("S01", "S04",  5),
    ("S02", "S03",  7),
    ("S03", "S04",  4),
    ("S03", "S07",  4),
    ("S04", "S05",  9),
    ("S05", "S09",  8),
    ("S06", "S07",  5),
    ("S06", "S10",  4),
    ("S07", "S08",  4),
    ("S07", "S11",  6),
    ("S08", "S09",  6),
    ("S08", "S12",  5),
    ("S09", "S12",  6),
    ("S10", "S11",  4),
    ("S11", "S12",  5),
    ("S11", "S13",  7),
    ("S12", "S15",  8),
    ("S13", "S14",  3),
    ("S13", "S15",  7),
]

# ─────────────────────────────────────────────────────────────────────────────
# 2.  WEATHER MODEL
# ─────────────────────────────────────────────────────────────────────────────

WEATHER_TYPES = [
    "sunny", "partly_cloudy", "overcast",
    "light_rain", "heavy_rain", "fog",
    "light_snow", "heavy_snow", "storm", "heatwave",
]

# Monthly probability distribution (columns = WEATHER_TYPES, must sum to 1.0)
WEATHER_PROBS = {
    1:  [0.05, 0.10, 0.20, 0.25, 0.15, 0.10, 0.10, 0.04, 0.01, 0.00],
    2:  [0.08, 0.12, 0.20, 0.25, 0.12, 0.08, 0.10, 0.04, 0.01, 0.00],
    3:  [0.15, 0.18, 0.22, 0.22, 0.10, 0.07, 0.04, 0.01, 0.01, 0.00],
    4:  [0.20, 0.20, 0.22, 0.22, 0.08, 0.05, 0.01, 0.00, 0.01, 0.01],
    5:  [0.25, 0.22, 0.20, 0.18, 0.07, 0.04, 0.00, 0.00, 0.01, 0.03],
    6:  [0.30, 0.22, 0.17, 0.15, 0.06, 0.03, 0.00, 0.00, 0.01, 0.06],
    7:  [0.32, 0.22, 0.15, 0.13, 0.05, 0.02, 0.00, 0.00, 0.01, 0.10],
    8:  [0.30, 0.22, 0.16, 0.14, 0.06, 0.02, 0.00, 0.00, 0.01, 0.09],
    9:  [0.22, 0.20, 0.20, 0.20, 0.10, 0.04, 0.01, 0.00, 0.02, 0.01],
    10: [0.15, 0.18, 0.22, 0.25, 0.12, 0.05, 0.02, 0.00, 0.01, 0.00],
    11: [0.08, 0.12, 0.22, 0.28, 0.14, 0.08, 0.05, 0.02, 0.01, 0.00],
    12: [0.05, 0.10, 0.20, 0.25, 0.12, 0.10, 0.10, 0.05, 0.02, 0.01],
}

# Temperature range (°C) per month
TEMP_RANGES = {
    1: (-4, 8),   2: (-3, 10), 3: (1, 14),   4: (4, 18),
    5: (8, 22),   6: (12, 26), 7: (15, 30),  8: (14, 29),
    9: (10, 23),  10: (6, 17), 11: (1, 12),  12: (-3, 8),
}

# Wind speed range (km/h) per weather type
WIND_RANGES = {
    "sunny": (0, 15),       "partly_cloudy": (5, 20),  "overcast": (10, 25),
    "light_rain": (15, 30), "heavy_rain": (25, 45),    "fog": (0, 10),
    "light_snow": (10, 25), "heavy_snow": (20, 45),    "storm": (50, 90),
    "heatwave": (0, 15),
}

# Precipitation (mm/hour)
PRECIP = {
    "sunny": 0.0,   "partly_cloudy": 0.0, "overcast": 0.1,
    "light_rain": 2.5, "heavy_rain": 10.0, "fog": 0.2,
    "light_snow": 1.0, "heavy_snow": 4.0,  "storm": 15.0,
    "heatwave": 0.0,
}

# How each weather type multiplies boardings
WEATHER_DEMAND_MULT = {
    "sunny":        1.00,
    "partly_cloudy": 1.02,
    "overcast":     1.06,
    "light_rain":   1.18,   # rain drives people onto buses
    "heavy_rain":   1.28,
    "fog":          0.93,
    "light_snow":   0.82,
    "heavy_snow":   0.52,
    "storm":        0.42,
    "heatwave":     0.88,
}

# ─────────────────────────────────────────────────────────────────────────────
# 3.  CLIMATE EVENTS  (rarer, multi-day conditions)
# ─────────────────────────────────────────────────────────────────────────────

CLIMATE_EVENTS = [
    "none", "heatwave_event", "cold_snap",
    "named_storm", "heavy_snow_event", "flooding", "dense_fog",
]
CLIMATE_EVENT_PROBS  = [0.920, 0.020, 0.020, 0.010, 0.010, 0.010, 0.010]
CLIMATE_EVENT_DEMAND = {
    "none":             1.00,
    "heatwave_event":   0.83,  # people avoid travel in extreme heat
    "cold_snap":        0.89,
    "named_storm":      0.35,
    "heavy_snow_event": 0.45,
    "flooding":         0.60,
    "dense_fog":        0.78,
}

# ─────────────────────────────────────────────────────────────────────────────
# 4.  SPECIAL EVENTS  (one-off occurrences at specific stops)
# ─────────────────────────────────────────────────────────────────────────────

SPECIAL_EVENTS      = ["none", "festival", "market", "sports_match", "concert", "road_closure"]
SPECIAL_EVENT_PROBS = [0.900, 0.020, 0.030, 0.020, 0.020, 0.010]

# Which stop is the epicentre of each event type
SPECIAL_EVENT_STOP = {
    "festival":    "S01",
    "market":      "S07",
    "sports_match":"S01",
    "concert":     "S08",
    "road_closure":"S03",
    "none":         None,
}

# Demand multiplier AT the event stop (during its active hours)
SPECIAL_EVENT_MULT = {
    "festival": 2.5, "market": 1.8, "sports_match": 2.2,
    "concert": 2.0,  "road_closure": 0.1, "none": 1.0,
}

# Spillover multiplier for immediately adjacent stops
SPECIAL_EVENT_SPILLOVER = {
    "festival": 1.35, "market": 1.15, "sports_match": 1.45,
    "concert": 1.20,  "road_closure": 1.60, "none": 1.0,
}

EVENT_ACTIVE_HOURS = {
    "festival":    set(range(10, 23)),
    "market":      set(range(8,  16)),
    "sports_match":set(range(14, 22)),
    "concert":     set(range(18, 24)),
    "road_closure":set(range(0,  24)),
    "none":        set(),
}

STOP_NEIGHBORS = {
    "S01": {"S04", "S03"},
    "S07": {"S06", "S03", "S08"},
    "S08": {"S07", "S09", "S12"},
    "S03": {"S02", "S04", "S07"},
}

# ─────────────────────────────────────────────────────────────────────────────
# 5.  HOURLY DEMAND PROFILES
# ─────────────────────────────────────────────────────────────────────────────

def _wd_sat_sun(wd, sat_scale, sun_scale, sat_mid_boost=None):
    """Build sat/sun dicts from a weekday dict."""
    sat = {h: (wd[h][0] * sat_scale, wd[h][1] * sat_scale) for h in range(24)}
    sun = {h: (wd[h][0] * sun_scale, wd[h][1] * sun_scale) for h in range(24)}
    if sat_mid_boost:
        for h in sat_mid_boost:
            sat[h] = (sat[h][0] * 1.30, sat[h][1] * 1.30)
    return sat, sun


def _profile_major(hour, day_type):
    wd = {
         0: (0.04, 0.04),  1: (0.02, 0.02),  2: (0.01, 0.01),  3: (0.01, 0.01),
         4: (0.05, 0.03),  5: (0.18, 0.10),  6: (0.42, 0.28),  7: (0.85, 0.60),
         8: (1.00, 0.75),  9: (0.70, 0.55), 10: (0.48, 0.45), 11: (0.50, 0.50),
        12: (0.55, 0.55), 13: (0.52, 0.52), 14: (0.50, 0.55), 15: (0.62, 0.70),
        16: (0.88, 0.95), 17: (0.95, 1.00), 18: (0.72, 0.80), 19: (0.50, 0.55),
        20: (0.35, 0.40), 21: (0.28, 0.32), 22: (0.20, 0.22), 23: (0.10, 0.12),
    }
    sat, sun = _wd_sat_sun(wd, 0.75, 0.50, sat_mid_boost=range(10, 17))
    # Floor at 0.30 for sat, 0.15 for sun (hubs never truly quiet)
    sat = {h: (max(0.30, sat[h][0]), max(0.30, sat[h][1])) for h in range(24)}
    sun = {h: (max(0.15, sun[h][0]), max(0.15, sun[h][1])) for h in range(24)}
    return {"weekday": wd, "saturday": sat, "sunday": sun}[day_type][hour]


def _profile_medium(hour, day_type):
    wd = {
         0: (0.03, 0.03),  1: (0.01, 0.01),  2: (0.01, 0.01),  3: (0.01, 0.01),
         4: (0.04, 0.02),  5: (0.14, 0.08),  6: (0.35, 0.22),  7: (0.75, 0.50),
         8: (0.90, 0.65),  9: (0.60, 0.50), 10: (0.42, 0.40), 11: (0.45, 0.45),
        12: (0.48, 0.48), 13: (0.46, 0.46), 14: (0.44, 0.50), 15: (0.56, 0.65),
        16: (0.78, 0.85), 17: (0.85, 0.92), 18: (0.65, 0.72), 19: (0.44, 0.50),
        20: (0.30, 0.35), 21: (0.22, 0.28), 22: (0.15, 0.18), 23: (0.08, 0.10),
    }
    sat, sun = _wd_sat_sun(wd, 0.65, 0.40)
    sat = {h: (max(0.20, sat[h][0]), max(0.20, sat[h][1])) for h in range(24)}
    sun = {h: (max(0.10, sun[h][0]), max(0.10, sun[h][1])) for h in range(24)}
    return {"weekday": wd, "saturday": sat, "sunday": sun}[day_type][hour]


def _profile_minor(hour, day_type):
    """Endpoint / quiet stop — strong outbound AM, inbound PM."""
    wd = {
         0: (0.02, 0.03),  1: (0.01, 0.01),  2: (0.00, 0.00),  3: (0.00, 0.00),
         4: (0.03, 0.01),  5: (0.12, 0.04),  6: (0.38, 0.10),  7: (1.00, 0.18),
         8: (0.88, 0.22),  9: (0.40, 0.28), 10: (0.25, 0.25), 11: (0.22, 0.28),
        12: (0.25, 0.30), 13: (0.22, 0.28), 14: (0.26, 0.35), 15: (0.30, 0.58),
        16: (0.28, 0.88), 17: (0.24, 1.00), 18: (0.20, 0.72), 19: (0.16, 0.42),
        20: (0.12, 0.28), 21: (0.10, 0.18), 22: (0.06, 0.12), 23: (0.04, 0.08),
    }
    sat, sun = _wd_sat_sun(wd, 0.55, 0.35)
    sat = {h: (max(0.05, sat[h][0]), max(0.05, sat[h][1])) for h in range(24)}
    sun = {h: (max(0.02, sun[h][0]), max(0.02, sun[h][1])) for h in range(24)}
    return {"weekday": wd, "saturday": sat, "sunday": sun}[day_type][hour]


PROFILE_FN = {
    "major":  _profile_major,
    "medium": _profile_medium,
    "minor":  _profile_minor,
}

# ─────────────────────────────────────────────────────────────────────────────
# 6.  SEASONAL AND TERM CALENDARS
# ─────────────────────────────────────────────────────────────────────────────

SEASONAL_MULT = {
    1: 0.88, 2: 0.90, 3: 0.96, 4: 0.98, 5: 1.02, 6: 1.04,
    7: 1.00, 8: 0.92, 9: 1.06, 10: 1.04, 11: 0.96, 12: 0.90,
}

SCHOOL_TERM = {1:1, 2:1, 3:1, 4:0, 5:1, 6:1, 7:0, 8:0, 9:1, 10:1, 11:1, 12:0}
UNI_TERM    = {1:1, 2:1, 3:1, 4:0, 5:1, 6:0, 7:0, 8:0, 9:0, 10:1, 11:1, 12:1}

MONTH_NAMES = {
    1:"January", 2:"February", 3:"March",     4:"April",
    5:"May",     6:"June",     7:"July",       8:"August",
    9:"September", 10:"October", 11:"November", 12:"December",
}

# ─────────────────────────────────────────────────────────────────────────────
# 7.  DEMAND CALCULATION
# ─────────────────────────────────────────────────────────────────────────────

def _noisy(x, sigma=0.18):
    if x < 0.5:
        return 0
    return max(0, round(x * math.exp(random.gauss(0, sigma))))


def get_demand(stop, hour, day_type, month, weather, special_event, climate_event):
    base = stop["base"]
    imp  = stop["importance"]

    bf, af = PROFILE_FN[imp](hour, day_type)
    sf  = SEASONAL_MULT[month]
    wm  = WEATHER_DEMAND_MULT[weather]
    cm  = CLIMATE_EVENT_DEMAND[climate_event]

    # ── Special event multiplier ──────────────────────────────────────────────
    em_b = em_a = 1.0
    if special_event != "none":
        event_stop = SPECIAL_EVENT_STOP[special_event]
        active     = EVENT_ACTIVE_HOURS[special_event]
        if stop["id"] == event_stop and hour in active:
            em_b = em_a = SPECIAL_EVENT_MULT[special_event]
        elif (event_stop and
              stop["id"] in STOP_NEIGHBORS.get(event_stop, set()) and
              hour in active):
            em_b = em_a = SPECIAL_EVENT_SPILLOVER[special_event]

    raw_b = base * bf * sf * wm * cm * em_b
    raw_a = base * af * sf * wm * cm * em_a
    return _noisy(raw_b), _noisy(raw_a)


# ─────────────────────────────────────────────────────────────────────────────
# 8.  WEATHER SAMPLING HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def sample_weather(month):
    probs = WEATHER_PROBS[month]
    r, cumul = random.random(), 0.0
    for wtype, p in zip(WEATHER_TYPES, probs):
        cumul += p
        if r <= cumul:
            return wtype
    return WEATHER_TYPES[-1]


def sample_temp(month, weather):
    lo, hi = TEMP_RANGES[month]
    if weather in ("heavy_snow", "light_snow"):
        hi = min(hi, 4);  lo = max(lo - 4, -15)
    elif weather == "heatwave":
        lo = max(lo, 27); hi = hi + 6
    return round(random.uniform(lo, hi), 1)


def sample_wind(weather):
    lo, hi = WIND_RANGES[weather]
    return round(random.uniform(lo, hi), 1)


# ─────────────────────────────────────────────────────────────────────────────
# 9.  DATASET GENERATION
#     Strategy: 5 "day scenarios" per (month × day_type) so weather varies
#     across same-month days.  All stops see the same weather on the same day.
#     Rows: 15 stops × 12 months × 3 day_types × 5 scenarios × 24 hours
#          = 64 800 rows
# ─────────────────────────────────────────────────────────────────────────────

DAY_TYPES     = ["weekday", "saturday", "sunday"]
N_SCENARIOS   = 5   # representative day samples per (month × day_type)

rows = []
scenario_counter = 0

for month in range(1, 13):
    for day_type in DAY_TYPES:
        for scenario_idx in range(N_SCENARIOS):
            scenario_counter += 1

            # Sample day-level conditions (shared by all stops this day)
            weather = sample_weather(month)
            temp    = sample_temp(month, weather)
            wind    = sample_wind(weather)
            precip  = PRECIP[weather]

            # Climate event (rare)
            climate = random.choices(CLIMATE_EVENTS,
                                     weights=CLIMATE_EVENT_PROBS)[0]

            # Special event (slightly more likely in summer / Dec)
            if month in (6, 7, 8, 12):
                sp_wts = [0.86, 0.03, 0.04, 0.03, 0.03, 0.01]
            else:
                sp_wts = SPECIAL_EVENT_PROBS
            special = random.choices(SPECIAL_EVENTS, weights=sp_wts)[0]

            for stop in STOPS:
                for hour in range(24):
                    boardings, alightings = get_demand(
                        stop, hour, day_type, month,
                        weather, special, climate)

                    # ── Occupancy proxy ───────────────────────────────────────
                    occ_base = {"major": 65, "medium": 50, "minor": 35}
                    occ = occ_base[stop["importance"]]
                    if hour in {7, 8, 16, 17, 18} and day_type == "weekday":
                        occ = min(98, occ + random.randint(15, 35))
                    elif day_type == "saturday" and 10 <= hour <= 16:
                        occ = min(90, occ + random.randint(5, 20))
                    occ = max(5, occ + random.randint(-10, 10))

                    rows.append({
                        "stop_id":          stop["id"],
                        "stop_name":        stop["name"],
                        "stop_x":           stop["x"],
                        "stop_y":           stop["y"],
                        "stop_importance":  stop["importance"],
                        "day_scenario":     scenario_counter,
                        "month":            month,
                        "month_name":       MONTH_NAMES[month],
                        "day_type":         day_type,
                        "hour":             hour,
                        "time_label":       f"{hour:02d}:00",
                        "weather_type":     weather,
                        "temperature_c":    temp,
                        "wind_kmh":         wind,
                        "precipitation_mm": precip,
                        "climate_event":    climate,
                        "special_event":    special,
                        "is_school_term":   SCHOOL_TERM[month],
                        "is_uni_term":      UNI_TERM[month],
                        "boardings":        boardings,
                        "alightings":       alightings,
                        "net_flow":         boardings - alightings,
                        "occupancy_pct":    occ,
                    })

# ─────────────────────────────────────────────────────────────────────────────
# 10.  WRITE CSV
# ─────────────────────────────────────────────────────────────────────────────

FIELDNAMES = [
    "stop_id", "stop_name", "stop_x", "stop_y", "stop_importance",
    "day_scenario", "month", "month_name", "day_type",
    "hour", "time_label",
    "weather_type", "temperature_c", "wind_kmh", "precipitation_mm",
    "climate_event", "special_event",
    "is_school_term", "is_uni_term",
    "boardings", "alightings", "net_flow", "occupancy_pct",
]

OUT = Path(__file__).parent / "map_demand_dataset.csv"
with open(OUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
    writer.writeheader()
    writer.writerows(rows)

# ─────────────────────────────────────────────────────────────────────────────
# 11.  SUMMARY STATS
# ─────────────────────────────────────────────────────────────────────────────

print(f"Written : {OUT}")
print(f"Rows    : {len(rows):,}")
print(f"Stops   : {len(STOPS)}")
print()

# Per-stop average weekday boardings/day
print(f"{'Stop':<22} {'Importance':<10} {'Avg weekday board/day':>22}")
print("-" * 58)
for stop in STOPS:
    wd_rows = [r for r in rows if r["stop_id"] == stop["id"]
               and r["day_type"] == "weekday"]
    # Group by scenario and sum hours, then average across scenarios
    by_scen = {}
    for r in wd_rows:
        by_scen.setdefault(r["day_scenario"], 0)
        by_scen[r["day_scenario"]] += r["boardings"]
    avg = sum(by_scen.values()) / max(len(by_scen), 1)
    print(f"  {stop['name']:<20} {stop['importance']:<10} {avg:>18.0f}")

print()

# Weather distribution in dataset
weather_counts = {}
for r in rows:
    weather_counts[r["weather_type"]] = weather_counts.get(r["weather_type"], 0) + 1
total = len(rows)
print("Weather distribution:")
for wt in WEATHER_TYPES:
    pct = 100 * weather_counts.get(wt, 0) / total
    print(f"  {wt:<16}: {pct:5.1f}%")

print()

# Special events present
se_counts = {}
for r in rows:
    if r["special_event"] != "none":
        se_counts[r["special_event"]] = se_counts.get(r["special_event"], 0) + 1
print("Special events in dataset:")
for ev, cnt in sorted(se_counts.items()):
    print(f"  {ev:<14}: {cnt:,} rows")

print()
print("Sample — North Hub weekday AM peak (all weather types seen):")
sample = [r for r in rows if r["stop_id"] == "S01"
          and r["day_type"] == "weekday" and r["hour"] == 8]
sample.sort(key=lambda r: r["boardings"], reverse=True)
print(f"  {'Weather':<16} {'Temp':>6} {'Board':>6} {'Alight':>7} {'Occ%':>6}")
for r in sample[:10]:
    print(f"  {r['weather_type']:<16} {r['temperature_c']:>5.1f}C"
          f" {r['boardings']:>6} {r['alightings']:>7} {r['occupancy_pct']:>5}%")
