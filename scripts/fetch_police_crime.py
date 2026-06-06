"""
fetch_police_crime.py
=====================
Fetches street-level crime incidents within 400m of each Ladywood model
stop using the Police Data API (data.police.uk — free, no auth required).

Covers 12 months: Jan 2024 - Dec 2024.

Crime categories
----------------
  anti-social-behaviour, bicycle-theft, burglary, criminal-damage-arson,
  drugs, possession-of-weapons, public-order, robbery, shoplifting,
  theft-from-the-person, vehicle-crime, violent-crime, other-crime

Output
------
  data/crime/ladywood_stop_crime_2024.json

Usage
-----
  python scripts/fetch_police_crime.py
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from pathlib import Path

import requests

_REPO   = Path(__file__).parent.parent
OUT_DIR = _REPO / "data" / "crime"
OUT     = OUT_DIR / "ladywood_stop_crime_2024.json"

API_BASE = "https://data.police.uk/api/crimes-street/all-crime"
HEADERS  = {"User-Agent": "ewb-bus-routing/1.0 (EWB design challenge; educational use)"}
MONTHS   = [f"2024-{m:02d}" for m in range(1, 13)]
SLEEP_S  = 1.5

STOPS: dict[str, dict] = {
    "S01": {"name": "New Street Station",        "lat": 52.4778, "lon": -1.8990},
    "S02": {"name": "Spring St",                 "lat": 52.4868, "lon": -1.9101},
    "S03": {"name": "Jewellery Quarter Station", "lat": 52.4868, "lon": -1.9101},
    "S04": {"name": "Soho Hill",                 "lat": 52.5012, "lon": -1.9178},
    "S05": {"name": "Five Ways (Metro)",         "lat": 52.4737, "lon": -1.9102},
    "S06": {"name": "Dudley Rd",                 "lat": 52.4887, "lon": -1.9302},
    "S07": {"name": "Five Ways Station",         "lat": 52.4737, "lon": -1.9102},
    "S08": {"name": "Icknield Port Rd",          "lat": 52.4914, "lon": -1.9267},
    "S09": {"name": "Belgrave Interchange",      "lat": 52.4820, "lon": -1.8960},
    "S10": {"name": "Ladywood Fire Station",     "lat": 52.4820, "lon": -1.9200},
    "S11": {"name": "Edgbaston Village Metro",   "lat": 52.4680, "lon": -1.9170},
    "S12": {"name": "Summerfield Park",          "lat": 52.4940, "lon": -1.9200},
    "S13": {"name": "City Rd Medical Centre",    "lat": 52.4880, "lon": -1.9350},
    "S14": {"name": "Mencap Centre",             "lat": 52.5020, "lon": -1.9430},
    "S15": {"name": "Summerfield Crescent",      "lat": 52.4930, "lon": -1.9230},
}

ALL_CATEGORIES = [
    "anti-social-behaviour", "bicycle-theft", "burglary",
    "criminal-damage-arson", "drugs", "possession-of-weapons",
    "public-order", "robbery", "shoplifting", "theft-from-the-person",
    "vehicle-crime", "violent-crime", "other-crime",
]


def fetch_stop_month(lat: float, lon: float, month: str) -> list[dict]:
    """Fetch all crimes near a point for one month."""
    params = {"lat": lat, "lng": lon, "date": month}
    try:
        r = requests.get(API_BASE, params=params, headers=HEADERS, timeout=30)
        if r.status_code == 503:
            return []
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"      Warning ({month}): {e}")
        return []


def run() -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result = {}
    total = len(STOPS)

    print(f"Fetching crime data for {total} stops x {len(MONTHS)} months")
    print(f"Source: data.police.uk (West Midlands Police, 2024)")
    print("-" * 65)

    for i, (sid, stop) in enumerate(STOPS.items(), 1):
        lat, lon = stop["lat"], stop["lon"]
        print(f"\n[{i}/{total}] {sid} — {stop['name']}")

        # Aggregate across all months
        by_category: dict[str, int] = defaultdict(int)
        total_incidents = 0

        for month in MONTHS:
            crimes = fetch_stop_month(lat, lon, month)
            for crime in crimes:
                cat = crime.get("category", "other-crime")
                by_category[cat] += 1
                total_incidents += 1
            time.sleep(SLEEP_S)

        # Ensure all categories present
        counts = {cat: by_category.get(cat, 0) for cat in ALL_CATEGORIES}
        counts["total_2024"] = total_incidents

        print(f"  Total incidents 2024: {total_incidents}")
        top = sorted(by_category.items(), key=lambda x: x[1], reverse=True)[:3]
        for cat, n in top:
            print(f"    {cat:<30} {n}")

        result[sid] = {
            "stop_name":    stop["name"],
            "lat":          lat,
            "lon":          lon,
            "year":         2024,
            "crime_counts": counts,
            "data_source":  "data.police.uk — West Midlands Police",
        }

    # Summary table
    sep = "-" * 65
    print(f"\n{'Crime Totals by Stop (2024)':^65}")
    print(sep)
    for sid in sorted(result, key=lambda s: result[s]["crime_counts"]["total_2024"], reverse=True):
        r = result[sid]
        n = r["crime_counts"]["total_2024"]
        bar = "#" * (n // 20)
        print(f"  {sid}  {r['stop_name']:<30}  {n:>4}  {bar}")
    print(sep)

    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nWrote {OUT}")
    return result


if __name__ == "__main__":
    run()
