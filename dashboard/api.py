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
from dashboard.demand import predict_all_stops

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


@app.get("/api/demand")
def get_demand(
    hour: int = 8,
    day_type: str = "weekday",
    month: int = 9,
    weather: str = "sunny",
    climate_event: str = "none",
    special_event: str = "none",
    temperature_c: float = 16.0,
    wind_kmh: float = 12.0,
    precipitation_mm: float = 0.0,
    is_school_term: int = 1,
    is_uni_term: int = 1,
):
    """Live per-stop boarding predictions from the trained XGBoost model
    for one hour, given a set of conditions (weather, calendar, events)."""
    predictions = predict_all_stops(
        hour=hour, day_type=day_type, month=month,
        weather=weather, climate_event=climate_event, special_event=special_event,
        temperature_c=temperature_c, wind_kmh=wind_kmh, precipitation_mm=precipitation_mm,
        is_school_term=is_school_term, is_uni_term=is_uni_term,
    )
    return {
        "hour": hour,
        "conditions": {
            "day_type": day_type, "month": month, "weather": weather,
            "climate_event": climate_event, "special_event": special_event,
            "temperature_c": temperature_c, "wind_kmh": wind_kmh,
            "precipitation_mm": precipitation_mm,
            "is_school_term": is_school_term, "is_uni_term": is_uni_term,
        },
        "predictions": predictions,
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "stops": len(STOPS_DISPLAY), "road_segments": len(_road_paths)}
