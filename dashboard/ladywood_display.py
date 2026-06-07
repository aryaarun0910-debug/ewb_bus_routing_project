"""
ladywood_display.py
====================
The 15 Ladywood model stops (S01-S15), each mapped to a real TfWM stop
location, name, route(s), importance tier, and a short descriptive note.

This is the canonical source the rest of the dashboard (and
scripts/build_road_geometry.py) imports STOPS_DISPLAY from.
"""

import json
from pathlib import Path

with open(Path(__file__).parent / "_stops_export.json", encoding="utf-8") as f:
    STOPS_DISPLAY: dict[str, dict] = json.load(f)
