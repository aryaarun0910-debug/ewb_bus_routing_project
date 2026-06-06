"""
fetch_bods_live.py
==================
Fetches live bus positions near Ladywood from the Bus Open Data Service
(BODS) SIRI-VM feed via the DfT API.

Takes a 5-minute snapshot of all buses within a bounding box around
Ladywood and records their positions, operators, and delays.
Run repeatedly (e.g. via cron/scheduler) to build up a real dataset
of on-time performance and coverage near the model stops.

API
---
  Base URL: https://data.bus-data.dft.gov.uk/api/v1/datafeed/
  Auth:     BODS_API_KEY env var (never commit the key)
  Docs:     https://data.bus-data.dft.gov.uk/api/v1/

Bounding box — covers all 15 Ladywood model stops + buffer:
  N=52.510  S=52.460  W=-1.950  E=-1.890

Output
------
  data/bods/snapshots/YYYY-MM-DDTHH-MM.json  (one file per run)
  data/bods/bods_summary.json                (aggregate stats)

Usage
-----
  python scripts/fetch_bods_live.py
  # or schedule every 5 minutes during peak hours
"""

from __future__ import annotations

import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import requests

_REPO      = Path(__file__).parent.parent
SNAP_DIR   = _REPO / "data" / "bods" / "snapshots"
SUMMARY    = _REPO / "data" / "bods" / "bods_summary.json"

API_BASE   = "https://data.bus-data.dft.gov.uk/api/v1/datafeed/"
API_KEY    = os.environ.get("BODS_API_KEY", "")

# Ladywood bounding box (lat/lon)
BBOX = {"north": 52.510, "south": 52.460, "west": -1.950, "east": -1.890}

SIRI_NS = {
    "s":    "http://www.siri.org.uk/siri",
    "siri": "http://www.siri.org.uk/siri",
}


def load_api_key() -> str:
    key = API_KEY
    if not key:
        env_file = _REPO / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("BODS_API_KEY="):
                    key = line.split("=", 1)[1].strip()
    if not key:
        raise RuntimeError("BODS_API_KEY not set. Add it to .env or environment.")
    return key


def fetch_siri_vm(api_key: str) -> str:
    """Fetch SIRI-VM XML for bounding box."""
    params = {
        "boundingBox": f"{BBOX['west']},{BBOX['south']},{BBOX['east']},{BBOX['north']}",
    }
    headers = {
        "Authorization": f"Token {api_key}",
        "User-Agent":    "ewb-bus-routing/1.0 (EWB design challenge; educational use)",
    }
    r = requests.get(API_BASE, params=params, headers=headers, timeout=60)
    r.raise_for_status()
    return r.text


def parse_vehicle_activities(xml_text: str) -> list[dict]:
    """Parse SIRI-VM XML into list of vehicle activity dicts."""
    root = ET.fromstring(xml_text)
    activities = []

    for va in root.findall(".//s:VehicleActivity", SIRI_NS):
        def get(path: str) -> str:
            el = va.find(path, SIRI_NS)
            return el.text.strip() if el is not None and el.text else ""

        mvj = va.find(".//s:MonitoredVehicleJourney", SIRI_NS)
        if mvj is None:
            continue

        def mvj_get(tag: str) -> str:
            el = mvj.find(f"s:{tag}", SIRI_NS)
            return el.text.strip() if el is not None and el.text else ""

        loc  = mvj.find("s:VehicleLocation", SIRI_NS)
        lat  = loc.find("s:Latitude",  SIRI_NS).text.strip() if loc is not None and loc.find("s:Latitude",  SIRI_NS) is not None else ""
        lon  = loc.find("s:Longitude", SIRI_NS).text.strip() if loc is not None and loc.find("s:Longitude", SIRI_NS) is not None else ""
        if not lat or not lon:
            continue

        activities.append({
            "recorded_at":      get("s:RecordedAtTime"),
            "vehicle_ref":      mvj_get("VehicleRef"),
            "operator_ref":     mvj_get("OperatorRef"),
            "line_ref":         mvj_get("LineRef"),
            "direction_ref":    mvj_get("DirectionRef"),
            "origin_name":      mvj_get("OriginName"),
            "destination_name": mvj_get("DestinationName"),
            "origin_aimed_dep": mvj_get("OriginAimedDepartureTime"),
            "latitude":         float(lat),
            "longitude":        float(lon),
            "bearing":          mvj_get("Bearing"),
            "delay_seconds":    mvj_get("Delay"),
            "occupancy":        mvj_get("Occupancy"),
        })

    return activities


def update_summary(snapshot: list[dict], snap_time: str) -> None:
    """Append snapshot stats to rolling summary JSON."""
    summary = []
    if SUMMARY.exists():
        summary = json.loads(SUMMARY.read_text())

    operators = {}
    lines = {}
    for v in snapshot:
        op = v["operator_ref"]
        ln = v["line_ref"]
        operators[op] = operators.get(op, 0) + 1
        lines[ln]     = lines.get(ln, 0) + 1

    summary.append({
        "snapshot_time":  snap_time,
        "vehicle_count":  len(snapshot),
        "top_operators":  sorted(operators.items(), key=lambda x: x[1], reverse=True)[:5],
        "top_lines":      sorted(lines.items(),     key=lambda x: x[1], reverse=True)[:10],
    })

    SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def run() -> list[dict]:
    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    api_key  = load_api_key()
    now      = datetime.now(timezone.utc)
    snap_tag = now.strftime("%Y-%m-%dT%H-%M")

    print(f"Fetching BODS SIRI-VM snapshot at {snap_tag} UTC")
    print(f"Bounding box: {BBOX}")

    xml_text   = fetch_siri_vm(api_key)
    activities = parse_vehicle_activities(xml_text)

    print(f"Found {len(activities)} vehicles in Ladywood area")

    if activities:
        snap_file = SNAP_DIR / f"{snap_tag}.json"
        snap_file.write_text(json.dumps(activities, indent=2), encoding="utf-8")
        print(f"Wrote {snap_file}")

        # Print sample
        for v in activities[:5]:
            delay = v["delay_seconds"] or "0"
            print(f"  Line {v['line_ref']:<6} {v['operator_ref']:<10} "
                  f"-> {v['destination_name']:<25} delay={delay}s")

        update_summary(activities, snap_tag)
        print(f"Updated {SUMMARY}")
    else:
        print("No vehicles found — check bounding box or API key.")

    return activities


if __name__ == "__main__":
    run()
