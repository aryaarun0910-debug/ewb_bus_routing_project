"""
crime_feature_ablation.py
=========================
Answers the redlining/policing-bias question with evidence instead of a promise:
what does crime_total_2024 actually contribute to the demand model?

Replicates the repo's training recipe EXACTLY (demand_route_optimizer.py):
same XGBRegressor hyperparameters, same label-encoded categoricals, same
feature list, same 2023-train / 2024-test temporal split — then trains twice:

  A. FULL        — all features including crime_total_2024
  B. ABLATED     — identical, with crime_total_2024 removed

plus permutation importance of crime_total_2024 in the FULL model.

If the ablated model's test R² is essentially unchanged, the feature is not
load-bearing and the documented mitigation ("low permutation importance,
ablation to publish, resident vote on the feature") becomes a published result.

Outputs: crime_ablation.json, CRIME_ABLATION.md (this folder)
"""

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.inspection import permutation_importance

HERE = Path(__file__).parent
_REPO_ROOT = HERE.parent.parent
DATA = _REPO_ROOT / "prediction model" / "map_demand_dataset.csv"

print("Loading dataset...")
df = pd.read_csv(DATA)
print(f"  {len(df):,} rows")

# ── Replicate the repo's feature engineering verbatim ────────────────────────
CAT_COLS = [
    "stop_id", "stop_importance", "day_type",
    "weather_type", "climate_event", "special_event",
]
for col in CAT_COLS:
    df[col + "_enc"] = LabelEncoder().fit_transform(df[col])

_REAL_STATIC_COLS = ["imd_score", "poi_total", "population", "crime_total_2024", "elevation_m"]

FEATURE_COLS = (
    [c + "_enc" for c in CAT_COLS]
    + ["hour", "month", "temperature_c", "wind_kmh", "precipitation_mm",
       "is_school_term", "is_uni_term", "stop_x", "stop_y"]
    + [c for c in _REAL_STATIC_COLS if c in df.columns]
)
assert "crime_total_2024" in FEATURE_COLS, "crime feature missing from dataset"

y = df["boardings"].values
df["date"] = pd.to_datetime(df["date"])
train_mask = (df["date"].dt.year == 2023).values
test_mask = (df["date"].dt.year == 2024).values
print(f"Temporal split: {train_mask.sum():,} train (2023) / {test_mask.sum():,} test (2024)")

PARAMS = dict(
    n_estimators=400, max_depth=7, learning_rate=0.07,
    subsample=0.80, colsample_bytree=0.80, min_child_weight=5,
    reg_alpha=0.1, reg_lambda=1.0,
    random_state=42, n_jobs=-1,
)

def run(name, feature_cols):
    X = df[feature_cols].values
    m = XGBRegressor(**PARAMS)
    t0 = time.time()
    m.fit(X[train_mask], y[train_mask])
    pred = m.predict(X[test_mask])
    r2 = r2_score(y[test_mask], pred)
    mae = mean_absolute_error(y[test_mask], pred)
    print(f"{name:8s}  R2={r2:.4f}  MAE={mae:.3f}  ({time.time()-t0:.0f}s)")
    return m, r2, mae

full_model, r2_full, mae_full = run("FULL", FEATURE_COLS)
ablated_cols = [c for c in FEATURE_COLS if c != "crime_total_2024"]
_, r2_abl, mae_abl = run("ABLATED", ablated_cols)

# ── Permutation importance of the crime feature in the FULL model ────────────
print("Permutation importance (test set, 5 repeats)...")
X_test = df[FEATURE_COLS].values[test_mask]
perm = permutation_importance(
    full_model, X_test, y[test_mask],
    scoring="r2", n_repeats=5, random_state=42, n_jobs=-1,
)
imp = {c: float(perm.importances_mean[i]) for i, c in enumerate(FEATURE_COLS)}
rank = sorted(imp, key=imp.get, reverse=True)
crime_rank = rank.index("crime_total_2024") + 1

results = {
    "n_rows": int(len(df)),
    "split": "temporal (train 2023, test 2024)",
    "params": {k: v for k, v in PARAMS.items() if k != "n_jobs"},
    "full": {"r2": round(r2_full, 4), "mae": round(mae_full, 4),
             "n_features": len(FEATURE_COLS)},
    "ablated_no_crime": {"r2": round(r2_abl, 4), "mae": round(mae_abl, 4),
                         "n_features": len(ablated_cols)},
    "delta_r2": round(r2_full - r2_abl, 5),
    "crime_permutation_importance": round(imp["crime_total_2024"], 6),
    "crime_importance_rank": f"{crime_rank} of {len(FEATURE_COLS)}",
    "all_permutation_importances": {c: round(imp[c], 6) for c in rank},
}
(HERE / "crime_ablation.json").write_text(json.dumps(results, indent=2))
print(json.dumps({k: results[k] for k in
                  ["full", "ablated_no_crime", "delta_r2",
                   "crime_permutation_importance", "crime_importance_rank"]}, indent=2))
print("Wrote crime_ablation.json")
