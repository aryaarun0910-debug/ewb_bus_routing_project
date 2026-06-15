"""
fetch_osm_pois.py
=================
Fetches real Points of Interest (POIs) within 400m of each Ladywood model
stop using the OSM Overpass API (free, no auth required).

POI categories fetched
----------------------
  hospitals       — amenity=hospital
  clinics / GPs   — amenity=clinic | healthcare=doctor
  schools         — amenity=school | amenity=college | amenity=university
  supermarkets    — shop=supermarket
  convenience     — shop=convenience
  pharmacies      — amenity=pharmacy
  bus stops       — highway=bus_stop  (density = interchange indicator)
  workplaces      — office=* | building=office | building=industrial

Each category count becomes a feature for the demand model, replacing the
hand-labelled major/medium/minor stop tier.

Output
------
  data/osm/ladywood_stop_pois.json

Usage
-----
  python scripts/fetch_osm_pois.py

No API key needed. Overpass API rate-limit: 1 req/2s — script sleeps between stops.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import requests

_REPO   = Path(__file__).parent.parent
OUT_DIR = _REPO / "data" / "osm"
OUT     = OUT_DIR / "ladywood_stop_pois.json"

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
RADIUS_M     = 400
SLEEP_S      = 4.0  # polite delay between stops (one request per stop now)

# Stop coordinates (WGS84) — averaged from matching data/gtfs/ladywood_stops.json
# entries by exact stop name (multiple GTFS entries per stop = different
# direction/platform; averaging gives a representative point for the 400m
# POI radius). Previous values were not derived from GTFS and were off by
# 300m-2.2km for 14/15 stops.
STOPS: dict[str, dict] = {
    "S01": {"name": "New Street Station",        "lat": 52.4776, "lon": -1.8962},
    "S02": {"name": "Spring St",                 "lat": 52.4677, "lon": -1.9034},
    "S03": {"name": "Jewellery Quarter Station", "lat": 52.4897, "lon": -1.9126},
    "S04": {"name": "Soho Hill",                 "lat": 52.4963, "lon": -1.9151},
    "S05": {"name": "Five Ways (Metro)",         "lat": 52.4756, "lon": -1.9138},
    "S06": {"name": "Dudley Rd",                 "lat": 52.4859, "lon": -1.9368},
    "S07": {"name": "Five Ways Station",         "lat": 52.4715, "lon": -1.9120},
    "S08": {"name": "Icknield Port Rd",          "lat": 52.4787, "lon": -1.9267},
    "S09": {"name": "Belgrave Interchange",      "lat": 52.4668, "lon": -1.8991},
    "S10": {"name": "Ladywood Fire Station",     "lat": 52.4780, "lon": -1.9276},
    "S11": {"name": "Edgbaston Village Metro",   "lat": 52.4722, "lon": -1.9236},
    "S12": {"name": "Summerfield Park",          "lat": 52.4865, "lon": -1.9385},
    "S13": {"name": "City Rd Medical Centre",    "lat": 52.4861, "lon": -1.9409},
    "S14": {"name": "Mencap Centre",             "lat": 52.4930, "lon": -1.9591},
    "S15": {"name": "Summerfield Crescent",      "lat": 52.4829, "lon": -1.9341},
}

HEADERS = {
    "User-Agent": "ewb-bus-routing/1.0 (EWB design challenge; contact: aryaarun0910@gmail.com)",
    "Accept":     "application/json",
}


def _categorise(tags: dict) -> str | None:
    """Return category name for an OSM element's tags, or None if unmatched."""
    amenity  = tags.get("amenity", "")
    shop     = tags.get("shop", "")
    highway  = tags.get("highway", "")
    office   = tags.get("office", "")
    building = tags.get("building", "")
    health   = tags.get("healthcare", "")

    if amenity == "hospital":                           return "hospitals"
    if amenity in ("clinic", "doctors") or health == "doctor": return "gp_clinics"
    if amenity == "pharmacy":                           return "pharmacies"
    if amenity in ("school", "college", "university"): return "schools"
    if shop == "supermarket":                           return "supermarkets"
    if shop == "convenience":                           return "convenience"
    if highway == "bus_stop":                           return "bus_stops"
    if office or building in ("office", "industrial"):  return "workplaces"
    return None


def _build_query(lat: float, lon: float, r: int) -> str:
    """Single Overpass query fetching all relevant elements near a point."""
    return (
        f"[out:json][timeout:30];\n"
        f"(\n"
        f'  node["amenity"~"hospital|clinic|doctors|pharmacy|school|college|university"](around:{r},{lat},{lon});\n'
        f'  way["amenity"~"hospital|clinic|pharmacy|school|college|university"](around:{r},{lat},{lon});\n'
        f'  node["shop"~"supermarket|convenience"](around:{r},{lat},{lon});\n'
        f'  way["shop"~"supermarket|convenience"](around:{r},{lat},{lon});\n'
        f'  node["highway"="bus_stop"](around:{r},{lat},{lon});\n'
        f'  node["office"](around:{r},{lat},{lon});\n'
        f'  way["office"](around:{r},{lat},{lon});\n'
        f'  way["building"~"office|industrial"](around:{r},{lat},{lon});\n'
        f'  node["healthcare"="doctor"](around:{r},{lat},{lon});\n'
        f");\n"
        f"out tags;"
    )


_EMPTY = {cat: -1 for cat in [
    "hospitals", "gp_clinics", "pharmacies", "schools",
    "supermarkets", "convenience", "bus_stops", "workplaces",
]}

# Try multiple Overpass mirrors in order
_MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]


def fetch_stop_pois(lat: float, lon: float) -> dict[str, int]:
    """Fetch all POI categories for a stop; retries across mirrors on failure."""
    query = _build_query(lat, lon, RADIUS_M)
    for attempt, mirror in enumerate(_MIRRORS):
        wait = 5 * (attempt + 1)
        if attempt > 0:
            print(f"    Retrying with mirror {mirror} (wait {wait}s)...")
            time.sleep(wait)
        try:
            r = requests.post(mirror, data={"data": query}, headers=HEADERS, timeout=60)
            if r.status_code == 429:
                print(f"    429 on {mirror}, trying next mirror...")
                continue
            r.raise_for_status()
            elements = r.json().get("elements", [])
            return _count_elements(elements)
        except Exception as e:
            print(f"    Warning ({mirror}): {e}")
            continue
    print("    All mirrors failed.")
    return dict(_EMPTY)


def _count_elements(elements: list) -> dict[str, int]:
    counts: dict[str, int] = {
        "hospitals": 0, "gp_clinics": 0, "pharmacies": 0, "schools": 0,
        "supermarkets": 0, "convenience": 0, "bus_stops": 0, "workplaces": 0,
    }
    for el in elements:
        cat = _categorise(el.get("tags", {}))
        if cat:
            counts[cat] += 1
    return counts


def _poi_score(counts: dict[str, int]) -> int:
    """Weighted POI density score (foot-traffic / demand proxy)."""
    return (
        counts.get("hospitals", 0) * 5 +
        counts.get("gp_clinics", 0) * 3 +
        counts.get("schools", 0) * 2 +
        counts.get("supermarkets", 0) * 2 +
        counts.get("workplaces", 0) * 1 +
        counts.get("bus_stops", 0) * 1 +
        counts.get("pharmacies", 0) * 1 +
        counts.get("convenience", 0) * 1
    )


def assign_tiers(scores: dict[str, int]) -> dict[str, str]:
    """Rank stops by POI score and split into major/medium/minor thirds.

    Absolute score thresholds don't transfer between corridors — a score of
    40 is "major" on a quiet suburban route and "minor" in a city centre.
    Tiers are therefore relative to this corridor's own stops, split into
    equal thirds (ties broken by stop_id for a stable, reproducible split).
    """
    ordered = sorted(scores, key=lambda sid: (scores[sid], sid))
    third = len(ordered) // 3
    tiers: dict[str, str] = {}
    for rank, sid in enumerate(ordered):
        if rank < third:
            tiers[sid] = "minor"
        elif rank < 2 * third:
            tiers[sid] = "medium"
        else:
            tiers[sid] = "major"
    return tiers


def run() -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    result = {}
    total = len(STOPS)
    sep = "-" * 65

    print(f"Fetching OSM POIs within {RADIUS_M}m of {total} Ladywood stops")
    print(f"Overpass API: {OVERPASS_URL}")
    print(sep)

    for i, (sid, stop) in enumerate(STOPS.items(), 1):
        lat, lon = stop["lat"], stop["lon"]
        print(f"\n[{i}/{total}] {sid} — {stop['name']} ({lat:.4f}, {lon:.4f})")

        counts = fetch_stop_pois(lat, lon)
        for category, count in counts.items():
            status = f"{count}" if count >= 0 else "ERR"
            print(f"  {category:<15} {status}")
        time.sleep(SLEEP_S)

        result[sid] = {
            "stop_name": stop["name"],
            "lat":       lat,
            "lon":       lon,
            "radius_m":  RADIUS_M,
            "poi_counts": counts,
            "poi_score": _poi_score(counts),
            "data_source": "OpenStreetMap via Overpass API",
        }

    tiers = assign_tiers({sid: v["poi_score"] for sid, v in result.items()})
    for sid in result:
        result[sid]["derived_tier"] = tiers[sid]
        print(f"  {sid} score={result[sid]['poi_score']:<4} -> {tiers[sid]}")

    print(f"\n{sep}")
    print("Stop tier summary (relative tertile, real POI-derived):")
    for tier in ["major", "medium", "minor"]:
        stops_in_tier = [sid for sid, v in result.items() if v["derived_tier"] == tier]
        print(f"  {tier:<8}: {', '.join(stops_in_tier)}")

    print(sep)

    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nWrote {OUT}")
    return result


if __name__ == "__main__":
    run()
