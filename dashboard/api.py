"""
api.py
======
FastAPI backend for the Predictive Bus Routing dashboard.

Serves the static network (stops + real road geometry) and, in later
features, live demand predictions and route plans from the trained
XGBoost model.

Run:
    uvicorn dashboard.api:app --port 8000
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dashboard.ladywood_display import STOPS_DISPLAY

_REPO_ROOT = Path(__file__).parent.parent
_ROAD_PATHS = _REPO_ROOT / "data" / "gtfs" / "road_paths.json"

app = FastAPI(title="Predictive Bus Routing API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

with open(_ROAD_PATHS, encoding="utf-8") as f:
    _road_paths: dict[str, list[list[float]]] = json.load(f)


@app.get("/api/stops")
def get_stops():
    """The 15 model stops — id, name, coordinates, routes, importance tier."""
    return [
        {"stop_id": sid, **info}
        for sid, info in STOPS_DISPLAY.items()
    ]


@app.get("/api/roads")
def get_roads():
    """Real road-following polylines between every pair of stops.

    Keys are "S01|S07" (sorted stop-id pair); each value is a list of
    [lng, lat] points. The reverse direction reuses the same polyline.
    """
    return _road_paths


@app.get("/api/health")
def health():
    return {"status": "ok", "stops": len(STOPS_DISPLAY), "road_segments": len(_road_paths)}
