"""
generate_real_demand_dataset.py
================================
Builds map_demand_dataset.csv from REAL Ladywood data instead of pure
synthetic sampling. Replaces the exogenous variables and the per-stop demand
anchor in generate_map_dataset.py with observed values:

  - weather_type / temperature_c / wind_kmh / precipitation_mm
        <- Open-Meteo hourly archive, Birmingham 2023-2024
            (data/weather/birmingham_hourly_2023_2024.csv)
  - is_school_term
        <- real Birmingham term + bank-holiday calendar
            (data/school_terms/birmingham_term_calendar.json)
  - climate_event ("named_storm")
        <- derived from observed storm_hours in the daily summary
  - per-stop demand anchor (replaces synthetic "base")
        <- GEoDS/UCL concessionary smartcard annual journeys
            (data/geods/ladywood_smartcard_summary.json)
            For the 3 stops with no smartcard match, falls back to the
            existing synthetic tier base.
  - static per-stop real features (new columns):
        imd_score, poi_total, population, crime_total_2024, elevation_m

The hour-of-day demand SHAPE (commuter peaks etc.) is retained from the
synthetic generator's PROFILE_FN curves, since no real per-hour boarding
counts exist publicly for these stops — this is documented as a remaining
limitation (see README Caveats / docs/MODEL_CARD.md).

Special events (festival/market/etc.) remain synthetic overlays — there is
no public record of one-off events at these stops for 2023-2024.

Output
------
  map_demand_dataset.csv  (real exogenous variables across 2 real years, 15 stops)

Usage
-----
  python "prediction model/generate_real_demand_dataset.py"
"""

from __future__ import annotations

import csv
import json
import math
import random
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))
from generate_map_dataset import (   # noqa: E402  (reuse synthetic shape fns)
    STOPS, PROFILE_FN, CLIMATE_EVENT_DEMAND, SPECIAL_EVENTS,
    SPECIAL_EVENT_PROBS, SPECIAL_EVENT_STOP, SPECIAL_EVENT_MULT,
    SPECIAL_EVENT_SPILLOVER, EVENT_ACTIVE_HOURS, STOP_NEIGHBORS,
    SEASONAL_MULT, WEATHER_DEMAND_MULT, MONTH_NAMES,
)

random.seed(42)

_REPO = Path(__file__).parent.parent
HOURLY_WEATHER = _REPO / "data" / "weather" / "birmingham_hourly_2023_2024.csv"
DAILY_WEATHER  = _REPO / "data" / "weather" / "birmingham_daily_summary_2023_2024.csv"
TERM_CALENDAR  = _REPO / "data" / "school_terms" / "birmingham_term_calendar.json"
UNI_TERM       = _REPO / "data" / "school_terms" / "university_term_calendar.json"
SMARTCARD      = _REPO / "data" / "geods" / "ladywood_smartcard_summary.json"
IMD            = _REPO / "data" / "imd" / "ladywood_imd_2019.json"
POIS           = _REPO / "data" / "osm" / "ladywood_stop_pois.json"
CRIME          = _REPO / "data" / "crime" / "ladywood_stop_crime_2024.json"
ELEVATION      = _REPO / "data" / "elevation" / "ladywood_stop_elevation.json"
POPULATION     = _REPO / "data" / "census" / "ladywood_population_2021.json"
CAR_FREE       = _REPO / "data" / "census" / "ladywood_car_availability.json"
SERVICE_PROFILE= _REPO / "data" / "gtfs" / "service_profile.json"

# Real WGS84 coordinates for the 15 model stops, from ladywood_display.py.
# Replaces the abstract 0-10 grid used for synthetic map topology.
REAL_STOP_COORDS: dict[str, tuple[float, float]] = {
    "S01": (52.477558, -1.896240), "S02": (52.467575, -1.904080),
    "S03": (52.489780, -1.912559), "S04": (52.496273, -1.915020),
    "S05": (52.475674, -1.913573), "S06": (52.485722, -1.936805),
    "S07": (52.472332, -1.912667), "S08": (52.478622, -1.926436),
    "S09": (52.466953, -1.898929), "S10": (52.477840, -1.927453),
    "S11": (52.472256, -1.923237), "S12": (52.486561, -1.938601),
    "S13": (52.486130, -1.940943), "S14": (52.493015, -1.959108),
    "S15": (52.482845, -1.934218),
}

OUT = Path(__file__).parent / "map_demand_dataset.csv"

# Synthetic tier-base values (fallback for stops with no smartcard match)
TIER_BASE = {"major": 80, "medium": 40, "minor": 12}
TIER_RANGE = {"major": (60, 100), "medium": (25, 55), "minor": (5, 22)}


# ─────────────────────────────────────────────────────────────────────────────
# 1.  LOAD REAL DATA
# ─────────────────────────────────────────────────────────────────────────────

def load_hourly_weather() -> dict[tuple[str, int], dict]:
    """(date, hour) -> {weather_type, temperature_c, wind_kmh, precipitation_mm}"""
    out = {}
    with HOURLY_WEATHER.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[(row["date"], int(row["hour"]))] = {
                "weather_type":     row["weather_type"],
                "temperature_c":    float(row["temperature_c"]),
                "wind_kmh":         float(row["wind_kmh"]),
                "precipitation_mm": float(row["precipitation_mm"]),
            }
    return out


def load_daily_storms() -> set[str]:
    """Dates flagged as having storm activity (-> climate_event=named_storm)."""
    storm_days = set()
    with DAILY_WEATHER.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if int(row["storm_hours"]) > 0:
                storm_days.add(row["date"])
    return storm_days


def load_term_calendar() -> dict[str, dict]:
    return json.loads(TERM_CALENDAR.read_text(encoding="utf-8"))


def load_uni_term_calendar() -> dict[str, bool]:
    """Date -> is_uni_term (University of Birmingham + Aston composite)."""
    raw = json.loads(UNI_TERM.read_text(encoding="utf-8"))
    return {d: v["is_uni_term"] for d, v in raw.items()}


def load_car_free() -> dict[str, float | None]:
    """stop_id -> car-free household percentage (Census 2021 TS045).
    S14 (Mencap Centre) is in Sandwell LA — no Birmingham Census coverage; returns None."""
    data = json.loads(CAR_FREE.read_text(encoding="utf-8"))
    return {sid: v.get("no_car_pct") for sid, v in data.items()}


def load_service_profile() -> dict[str, dict[str, dict[int, int]]]:
    """stop_id -> day_type -> hour -> scheduled departures.
    Source: TfWM GTFS static feed, mined by scripts/build_gtfs_profile.py."""
    raw = json.loads(SERVICE_PROFILE.read_text(encoding="utf-8"))
    out = {}
    for sid, info in raw.items():
        out[sid] = {
            "weekday":  {int(h): v for h, v in info.get("weekday",  {}).items()},
            "saturday": {int(h): v for h, v in info.get("saturday", {}).items()},
            "sunday":   {int(h): v for h, v in info.get("sunday",   {}).items()},
        }
    return out


def load_smartcard_anchor() -> dict[str, float]:
    """Per-stop relative demand anchor from real concessionary journey volumes."""
    data = json.loads(SMARTCARD.read_text(encoding="utf-8"))
    raw = {}
    for sid, info in data.items():
        j60   = info.get("annual_journeys_60plus") or {}
        jdis  = info.get("annual_journeys_disabled") or {}
        years = set(j60) | set(jdis)
        if not years:
            continue
        total = sum(j60.get(y, 0) + jdis.get(y, 0) for y in years) / len(years)
        if total > 0:
            raw[sid] = total
    return raw


def load_static_features() -> dict[str, dict]:
    """Per-stop static real-world features merged from multiple sources."""
    imd      = json.loads(IMD.read_text(encoding="utf-8"))
    pois     = json.loads(POIS.read_text(encoding="utf-8"))
    crime    = json.loads(CRIME.read_text(encoding="utf-8"))
    elev     = json.loads(ELEVATION.read_text(encoding="utf-8"))
    pop      = json.loads(POPULATION.read_text(encoding="utf-8"))
    car_free = load_car_free()

    out = {}
    for sid in [s["id"] for s in STOPS]:
        out[sid] = {
            "imd_score":         (imd.get(sid) or {}).get("imd_score"),
            "poi_total":         sum((pois.get(sid) or {}).get("poi_counts", {}).values()) or None,
            "population":        (pop.get(sid) or {}).get("total_population"),
            "crime_total_2024":  sum((crime.get(sid) or {}).get("crime_counts", {}).values()) or None,
            "elevation_m":       (elev.get(sid) or {}).get("elevation_m"),
            "car_free_pct":      car_free.get(sid),
        }
    return out


# ─────────────────────────────────────────────────────────────────────────────
# 2.  BUILD PER-STOP DEMAND ANCHOR (replaces synthetic `base`)
#     Smartcard journeys -> relative scaling -> rescaled within tier range,
#     same clamping approach as scripts/recalibrate_base_demand.py
# ─────────────────────────────────────────────────────────────────────────────

def build_anchors() -> dict[str, float]:
    smartcard = load_smartcard_anchor()
    if smartcard:
        mean_journeys = sum(smartcard.values()) / len(smartcard)
    anchors = {}
    for stop in STOPS:
        sid, imp = stop["id"], stop["importance"]
        lo, hi = TIER_RANGE[imp]
        if sid in smartcard:
            ratio = smartcard[sid] / mean_journeys
            val = TIER_BASE[imp] * ratio
            anchors[sid] = max(lo, min(hi, val))
        else:
            anchors[sid] = TIER_BASE[imp]
    return anchors


# ─────────────────────────────────────────────────────────────────────────────
# 3.  DEMAND CALCULATION (mirrors generate_map_dataset.get_demand, but driven
#     by the real anchor + real weather/season inputs passed in)
# ─────────────────────────────────────────────────────────────────────────────

def _noisy(x, sigma=0.18):
    if x < 0.5:
        return 0
    return max(0, round(x * math.exp(random.gauss(0, sigma))))


def get_demand(stop, anchor, hour, day_type, month, weather, special_event, climate_event):
    imp = stop["importance"]
    bf, af = PROFILE_FN[imp](hour, day_type)
    sf = SEASONAL_MULT[month]
    wm = WEATHER_DEMAND_MULT.get(weather, 1.0)
    cm = CLIMATE_EVENT_DEMAND[climate_event]

    em_b = em_a = 1.0
    if special_event != "none":
        event_stop = SPECIAL_EVENT_STOP[special_event]
        active = EVENT_ACTIVE_HOURS[special_event]
        if stop["id"] == event_stop and hour in active:
            em_b = em_a = SPECIAL_EVENT_MULT[special_event]
        elif (event_stop and stop["id"] in STOP_NEIGHBORS.get(event_stop, set())
              and hour in active):
            em_b = em_a = SPECIAL_EVENT_SPILLOVER[special_event]

    raw_b = anchor * bf * sf * wm * cm * em_b
    raw_a = anchor * af * sf * wm * cm * em_a
    return _noisy(raw_b), _noisy(raw_a)


# ─────────────────────────────────────────────────────────────────────────────
# 4.  MAIN GENERATION LOOP — iterate every real day in the weather archive
# ─────────────────────────────────────────────────────────────────────────────

def run() -> None:
    print("Loading real datasets...")
    hourly          = load_hourly_weather()
    storms          = load_daily_storms()
    calendar        = load_term_calendar()
    uni_calendar    = load_uni_term_calendar()
    anchors         = build_anchors()
    static          = load_static_features()
    svc_profile     = load_service_profile()

    print(f"  Hourly weather records : {len(hourly):,}")
    print(f"  Storm days             : {len(storms)}")
    print(f"  Calendar days          : {len(calendar):,}")
    print(f"  Uni term dates loaded  : {sum(v for v in uni_calendar.values())} in-term days")
    print(f"  Demand anchors         : {anchors}")

    dates = sorted({d for (d, _h) in hourly})
    print(f"  Real days covered      : {len(dates)} ({dates[0]} .. {dates[-1]})")

    rows = []
    day_special = {}   # date -> sampled special_event (kept synthetic — no real record)

    for d_str in dates:
        y, m, day = (int(x) for x in d_str.split("-"))
        cal = calendar.get(d_str, {})
        is_term     = 1 if cal.get("is_school_term") else 0
        is_uni_term = 1 if uni_calendar.get(d_str, False) else 0

        wd = date(y, m, day).weekday()
        day_type = "weekday" if wd < 5 else ("saturday" if wd == 5 else "sunday")

        climate_event = "named_storm" if d_str in storms else "none"

        if d_str not in day_special:
            sp_wts = [0.86, 0.03, 0.04, 0.03, 0.03, 0.01] if m in (6, 7, 8, 12) else SPECIAL_EVENT_PROBS
            day_special[d_str] = random.choices(SPECIAL_EVENTS, weights=sp_wts)[0]
        special = day_special[d_str]

        for hour in range(24):
            wx = hourly.get((d_str, hour))
            if wx is None:
                continue

            for stop in STOPS:
                sid = stop["id"]
                boardings, alightings = get_demand(
                    stop, anchors[sid], hour, day_type, m,
                    wx["weather_type"], special, climate_event)

                occ_base = {"major": 65, "medium": 50, "minor": 35}[stop["importance"]]
                occ = occ_base
                if hour in {7, 8, 16, 17, 18} and day_type == "weekday":
                    occ = min(98, occ + random.randint(15, 35))
                elif day_type == "saturday" and 10 <= hour <= 16:
                    occ = min(90, occ + random.randint(5, 20))
                occ = max(5, occ + random.randint(-10, 10))

                feat = static[sid]
                lat, lng = REAL_STOP_COORDS[sid]
                # trips_per_hour: scheduled GTFS departures at this stop this hour
                trips = svc_profile.get(sid, {}).get(day_type, {}).get(hour, 0)
                rows.append({
                    "stop_id":          sid,
                    "stop_name":        stop["name"],
                    "stop_lat":         lat,
                    "stop_lng":         lng,
                    "stop_importance":  stop["importance"],
                    "date":             d_str,
                    "month":            m,
                    "month_name":       MONTH_NAMES[m],
                    "day_type":         day_type,
                    "hour":             hour,
                    "time_label":       f"{hour:02d}:00",
                    "weather_type":     wx["weather_type"],
                    "temperature_c":    wx["temperature_c"],
                    "wind_kmh":         wx["wind_kmh"],
                    "precipitation_mm": wx["precipitation_mm"],
                    "climate_event":    climate_event,
                    "special_event":    special,
                    "is_school_term":   is_term,
                    "is_uni_term":      is_uni_term,
                    "trips_per_hour":   trips,
                    "imd_score":        feat["imd_score"],
                    "poi_total":        feat["poi_total"],
                    "population":       feat["population"],
                    "crime_total_2024": feat["crime_total_2024"],
                    "elevation_m":      feat["elevation_m"],
                    "car_free_pct":     feat["car_free_pct"],
                    "boardings":        boardings,
                    "alightings":       alightings,
                    "net_flow":         boardings - alightings,
                    "occupancy_pct":    occ,
                })

    fieldnames = [
        "stop_id", "stop_name", "stop_lat", "stop_lng", "stop_importance",
        "date", "month", "month_name", "day_type",
        "hour", "time_label",
        "weather_type", "temperature_c", "wind_kmh", "precipitation_mm",
        "climate_event", "special_event",
        "is_school_term", "is_uni_term", "trips_per_hour",
        "imd_score", "poi_total", "population", "crime_total_2024",
        "elevation_m", "car_free_pct",
        "boardings", "alightings", "net_flow", "occupancy_pct",
    ]

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {OUT}")
    print(f"Rows: {len(rows):,}")

    print(f"\n{'Stop':<24} {'Importance':<10} {'Anchor':>8} {'Avg weekday board/day':>22}")
    print("-" * 68)
    for stop in STOPS:
        sid = stop["id"]
        wd_rows = [r for r in rows if r["stop_id"] == sid and r["day_type"] == "weekday"]
        by_date = defaultdict(int)
        for r in wd_rows:
            by_date[r["date"]] += r["boardings"]
        avg = sum(by_date.values()) / max(len(by_date), 1)
        print(f"  {stop['name']:<22} {stop['importance']:<10} {anchors[sid]:>8.1f} {avg:>18.0f}")


if __name__ == "__main__":
    run()
