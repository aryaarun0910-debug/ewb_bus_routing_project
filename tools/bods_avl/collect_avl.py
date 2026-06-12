"""
collect_avl.py — BODS SIRI-VM collector for the Ladywood corridors.

Polls the DfT Bus Open Data Service live-location feed for West Midlands buses
on the modelled lines (8A/8C/80/126) and appends observations to a daily CSV.
Vehicle positions only — no passenger or personal data.

Setup (one-off):
  1. Free BODS account: https://data.bus-data.dft.gov.uk/account/signup/
  2. Save your API key as the single line of:  .bods_key  (this folder)

Run:  py -3 collect_avl.py          (Ctrl+C to stop; safe to restart anytime)
"""

import csv
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

HERE = Path(__file__).parent
KEY_FILE = HERE / ".bods_key"
OUT_DIR = HERE / "avl_raw"
OUT_DIR.mkdir(exist_ok=True)

# Ladywood-ish bounding box (covers the 8A/8C inner circle, 80, 126 corridors)
BBOX = "-2.01,52.45,-1.85,52.52"          # minLon,minLat,maxLon,maxLat
LINES = {"8A", "8C", "80", "126"}
POLL_SECONDS = 30
NS = {"s": "http://www.siri.org.uk/siri"}

def api_key() -> str:
    if not KEY_FILE.exists():
        raise SystemExit("No .bods_key file - see BODS_AVL_PIPELINE.md step 1-3")
    return KEY_FILE.read_text().strip()

def poll(key: str) -> list[dict]:
    url = (f"https://data.bus-data.dft.gov.uk/api/v1/datafeed/"
           f"?boundingBox={BBOX}&api_key={key}")
    with urlopen(url, timeout=30) as r:
        tree = ET.parse(r)
    rows = []
    for va in tree.iterfind(".//s:VehicleActivity", NS):
        def get(path):
            el = va.find(path, NS)
            return el.text if el is not None else ""
        line = get(".//s:LineRef")
        if line not in LINES:
            continue
        rows.append({
            "recorded_at": get(".//s:RecordedAtTime"),
            "line": line,
            "vehicle_ref": get(".//s:VehicleRef"),
            "lat": get(".//s:Latitude"),
            "lon": get(".//s:Longitude"),
            "bearing": get(".//s:Bearing"),
            "journey_ref": get(".//s:DatedVehicleJourneyRef"),
        })
    return rows

def main():
    key = api_key()
    fields = ["recorded_at", "line", "vehicle_ref", "lat", "lon",
              "bearing", "journey_ref"]
    print(f"Polling BODS every {POLL_SECONDS}s for lines {sorted(LINES)} "
          f"in bbox {BBOX} - Ctrl+C to stop")
    while True:
        try:
            rows = poll(key)
            day_file = OUT_DIR / f"avl_{datetime.now(timezone.utc):%Y%m%d}.csv"
            new = not day_file.exists()
            with day_file.open("a", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=fields)
                if new:
                    w.writeheader()
                w.writerows(rows)
            print(f"{datetime.now():%H:%M:%S}  +{len(rows):3d} obs -> {day_file.name}")
        except KeyboardInterrupt:
            raise
        except Exception as e:                       # transient API hiccups
            print(f"{datetime.now():%H:%M:%S}  poll failed ({e}) - retrying")
        time.sleep(POLL_SECONDS)

if __name__ == "__main__":
    main()
