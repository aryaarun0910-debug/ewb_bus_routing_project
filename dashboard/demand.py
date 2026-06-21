"""
demand.py
=========
Loads the trained XGBoost demand model and reproduces the prediction
feature-row assembly from `prediction model/demand_route_optimizer.py`,
without re-running that script's training pipeline on import (it trains
and plots on import, which is far too slow for an API process).

Exposes `predict_stop_demand(...)` for the FastAPI layer.
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path

import pandas as pd
from sklearn.preprocessing import LabelEncoder

_REPO_ROOT = Path(__file__).parent.parent
_MODEL_DIR = _REPO_ROOT / "prediction model"
_MODEL_PKL = _MODEL_DIR / "demand_model.pkl"
_DATASET_CSV = _MODEL_DIR / "map_demand_dataset.csv"

# Abstract 0-10 grid coordinates used as stop_x/stop_y during model training.
# Matches the values in map_demand_dataset.csv exactly.
_STOP_LATLNG = {
    "S01": (52.477558, -1.896240), "S02": (52.467575, -1.904080),
    "S03": (52.489780, -1.912559), "S04": (52.496273, -1.915020),
    "S05": (52.475674, -1.913573), "S06": (52.485722, -1.936805),
    "S07": (52.472332, -1.912667), "S08": (52.478622, -1.926436),
    "S09": (52.466953, -1.898929), "S10": (52.477840, -1.927453),
    "S11": (52.472256, -1.923237), "S12": (52.486561, -1.938601),
    "S13": (52.486130, -1.940943), "S14": (52.493015, -1.959108),
    "S15": (52.482845, -1.934218),
}
_STOP_IMPORTANCE = {
    "S01": "major", "S03": "major", "S07": "major", "S09": "major",
    "S04": "medium", "S08": "medium", "S11": "medium", "S12": "medium",
    "S02": "minor", "S05": "minor", "S06": "minor", "S10": "minor",
    "S13": "minor", "S14": "minor", "S15": "minor",
}

# Static per-stop columns matching the model's training feature_cols exactly.
_STATIC_COLS = ["imd_score", "poi_total", "population", "elevation_m", "car_free_pct"]
_MODEL_STATIC_COLS = ["imd_score", "poi_total", "population", "elevation_m", "car_free_pct"]

# GTFS service frequency: stop_id -> day_type -> hour -> scheduled departures.
def _load_svc_profile() -> dict[str, dict[str, dict[int, int]]]:
    path = _REPO_ROOT / "data" / "gtfs" / "service_profile.json"
    if not path.exists():
        return {}
    raw = json.loads(path.read_text())
    return {
        sid: {dt: {int(h): v for h, v in hrs.items()}
              for dt, hrs in info.items() if dt in ("weekday", "saturday", "sunday")}
        for sid, info in raw.items()
    }

_svc_profile = _load_svc_profile()


def _load_bundle():
    if not _MODEL_PKL.exists():
        raise FileNotFoundError(
            f"Model not found at {_MODEL_PKL}. "
            "Run python \"prediction model/demand_route_optimizer.py\" first."
        )
    with open(_MODEL_PKL, "rb") as f:
        bundle = pickle.load(f)
    return bundle["model"], bundle["encoders"]


def _load_static_lookup() -> dict[str, dict]:
    if not _DATASET_CSV.exists():
        return {}
    df = pd.read_csv(_DATASET_CSV, usecols=lambda c: c == "stop_id" or c in _STATIC_COLS)
    cols = [c for c in _STATIC_COLS if c in df.columns]
    if not cols:
        return {}
    raw = df.drop_duplicates("stop_id").set_index("stop_id")[cols].to_dict("index")
    return {sid: {k: (float("nan") if pd.isna(v) else v) for k, v in row.items()}
            for sid, row in raw.items()}


_model, _encoders = _load_bundle()
_static_lookup = _load_static_lookup()
_model_static_cols = [c for c in _MODEL_STATIC_COLS
                      if c in next(iter(_static_lookup.values()), {})]


def _safe_encode(enc: LabelEncoder, value: str) -> int:
    if value in enc.classes_:
        return int(enc.transform([value])[0])
    fallback = "none" if "none" in enc.classes_ else enc.classes_[0]
    return int(enc.transform([fallback])[0])


def _build_row(
    stop_id: str, hour: int, day_type: str, month: int,
    weather: str, climate_event: str, special_event: str,
    temperature_c: float, wind_kmh: float, precipitation_mm: float,
    is_school_term: int, is_uni_term: int,
) -> list:
    """Assemble one model feature row for a stop-hour. Order matches FEATURE_COLS
    in prediction model/demand_route_optimizer.py exactly."""
    lat, lng = _STOP_LATLNG[stop_id]
    trips = _svc_profile.get(stop_id, {}).get(day_type, {}).get(hour, 0)
    row = [
        _safe_encode(_encoders["stop_id"], stop_id),
        _safe_encode(_encoders["stop_importance"], _STOP_IMPORTANCE[stop_id]),
        _safe_encode(_encoders["day_type"], day_type),
        _safe_encode(_encoders["weather_type"], weather),
        _safe_encode(_encoders["climate_event"], climate_event),
        _safe_encode(_encoders["special_event"], special_event),
        hour, month,
        temperature_c, wind_kmh, precipitation_mm,
        is_school_term, is_uni_term,
        trips,
        lat, lng,
    ]
    if _model_static_cols:
        static = _static_lookup.get(stop_id, {})
        row += [static.get(c) for c in _model_static_cols]
    return row


def predict_stop_demand(stop_id: str, hour: int, **conditions) -> float:
    """Predicted boardings for one stop at one hour, given conditions."""
    return max(0.0, float(_model.predict([_build_row(stop_id, hour, **conditions)])[0]))


def predict_all_stops(hour: int, **conditions) -> dict[str, float]:
    """Predicted boardings for every stop at one hour, given conditions.

    Batches all stops into a single `model.predict` call — XGBoost's per-call
    overhead dominates single-row predictions, so this is ~40x faster than
    looping `predict_stop_demand` (≈2.2s → ≈50ms for 15 stops), keeping the
    what-if panel and auto-play snappy.
    """
    sids = list(_STOP_LATLNG)
    rows = [_build_row(sid, hour, **conditions) for sid in sids]
    preds = _model.predict(rows)
    return {sid: round(max(0.0, float(p)), 1) for sid, p in zip(sids, preds)}
