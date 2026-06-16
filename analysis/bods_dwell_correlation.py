"""
bods_dwell_correlation.py
=========================
Correlates observed BODS dwell profiles against the model's synthetic PROFILE_FN
demand curves — the first Birmingham-specific shape validation.

For each stop tier (major / medium / minor), computes Spearman rank correlation
between:
  - observed median dwell-seconds by hour (from dwell_profiles.csv via derive_dwell_times.py)
  - model predicted boardings by hour at representative conditions

A positive correlation means the shape of real bus dwell behaviour at Ladywood
stops tracks the shape of the model's demand predictions. This is evidence —
not proof — that the demand shape, though synthetic, captures real signal.

Usage
-----
  # Run from the repo root; --dwell is required
  py -3 analysis/bods_dwell_correlation.py --dwell <path_to_dwell_profiles.csv>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
from scipy import stats

_REPO = Path(__file__).parent.parent


# Model's PROFILE_FN peak demand fractions by tier and hour (weekday)
# Extracted from generate_map_dataset.py PROFILE_FN definitions
_PROFILE_WEEKDAY = {
    "major": {
        0: 0.05, 1: 0.02, 2: 0.01, 3: 0.01, 4: 0.03, 5: 0.15,
        6: 0.50, 7: 0.85, 8: 1.00, 9: 0.80, 10: 0.60, 11: 0.55,
        12: 0.55, 13: 0.60, 14: 0.65, 15: 0.75, 16: 0.85, 17: 0.95,
        18: 0.80, 19: 0.60, 20: 0.40, 21: 0.30, 22: 0.20, 23: 0.10,
    },
    "medium": {
        0: 0.03, 1: 0.01, 2: 0.01, 3: 0.01, 4: 0.02, 5: 0.10,
        6: 0.40, 7: 0.75, 8: 0.90, 9: 0.75, 10: 0.55, 11: 0.50,
        12: 0.50, 13: 0.55, 14: 0.60, 15: 0.70, 16: 0.80, 17: 0.90,
        18: 0.75, 19: 0.55, 20: 0.35, 21: 0.25, 22: 0.15, 23: 0.08,
    },
    "minor": {
        0: 0.02, 1: 0.01, 2: 0.00, 3: 0.01, 4: 0.02, 5: 0.08,
        6: 0.35, 7: 1.00, 8: 0.85, 9: 0.65, 10: 0.45, 11: 0.40,
        12: 0.40, 13: 0.45, 14: 0.50, 15: 0.55, 16: 0.65, 17: 0.75,
        18: 0.60, 19: 0.40, 20: 0.25, 21: 0.15, 22: 0.08, 23: 0.04,
    },
}

# S01-S15 importance tiers
_STOP_TIER = {
    "S01": "major", "S03": "major", "S07": "major", "S09": "major",
    "S04": "medium", "S08": "medium", "S11": "medium", "S12": "medium",
    "S02": "minor", "S05": "minor", "S06": "minor", "S10": "minor",
    "S13": "minor", "S14": "minor", "S15": "minor",
}

# ATCO -> S-code mapping (from ladywood_display.py / GTFS)
_ATCO_TO_SID: dict[str, str] | None = None

def _load_atco_map() -> dict[str, str]:
    global _ATCO_TO_SID
    if _ATCO_TO_SID is not None:
        return _ATCO_TO_SID
    stops_path = _REPO / "data" / "gtfs" / "ladywood_stops.json"
    raw = json.loads(stops_path.read_text())
    # ladywood_stops.json uses ATCO codes as stop_id
    # We need to map from ATCO to the S01-S15 model IDs.
    # The mapping is maintained in ladywood_display.py STOPS_DISPLAY;
    # load it from the dashboard module.
    sys.path.insert(0, str(_REPO / "dashboard"))
    from ladywood_display import STOPS_DISPLAY
    # Build name -> S-code lookup
    name_to_sid = {info["name"]: sid for sid, info in STOPS_DISPLAY.items()}
    # Build ATCO -> S-code by matching stop names
    atco_to_sid = {}
    for entry in raw:
        name = entry["name"]
        if name in name_to_sid:
            atco_to_sid[entry["stop_id"]] = name_to_sid[name]
    _ATCO_TO_SID = atco_to_sid
    return atco_to_sid


def run(dwell_path: Path) -> None:
    if not dwell_path.exists():
        print(f"ERROR: dwell_profiles.csv not found at {dwell_path}")
        print("Run derive_dwell_times.py first, or pass --dwell <path>")
        sys.exit(1)

    dwell_df = pd.read_csv(dwell_path)
    atco_map = _load_atco_map()

    # Map ATCO codes to model stop IDs
    if "stop" in dwell_df.columns:
        dwell_df["sid"] = dwell_df["stop"].map(atco_map)
    else:
        print(f"ERROR: expected 'stop' column in {dwell_path}, found: {list(dwell_df.columns)}")
        sys.exit(1)

    dwell_df = dwell_df.dropna(subset=["sid"])
    weekday_dwell = dwell_df[dwell_df["day_type"] == "weekday"].copy()

    print(f"Loaded dwell profiles: {len(dwell_df)} rows")
    print(f"Matched to model stops: {dwell_df['sid'].nunique()} unique stops")
    print(f"Weekday rows: {len(weekday_dwell)}\n")

    results = []
    for sid in sorted(_STOP_TIER):
        tier = _STOP_TIER[sid]
        stop_rows = weekday_dwell[weekday_dwell["sid"] == sid]
        if len(stop_rows) < 8:
            results.append({"stop": sid, "tier": tier, "r": None, "n_hours": len(stop_rows),
                            "note": "insufficient data"})
            continue

        # Pivot: one row per hour, value = median_dwell_s
        pivot = stop_rows.groupby("hour")["median_dwell_s"].median()
        hours = sorted(pivot.index)
        observed = [pivot[h] for h in hours]
        predicted = [_PROFILE_WEEKDAY[tier][h] for h in hours]

        r, p = stats.spearmanr(observed, predicted)
        results.append({
            "stop": sid, "tier": tier, "n_hours": len(hours),
            "r": round(r, 3), "p": round(p, 4),
            "note": "significant" if p < 0.05 else "not significant"
        })

    # Summary by tier
    print(f"{'Stop':<6} {'Tier':<8} {'N hrs':<7} {'Spearman r':<12} {'p-val':<8} {'Verdict'}")
    print("-" * 55)
    for res in results:
        if res["r"] is None:
            print(f"{res['stop']:<6} {res['tier']:<8} {res['n_hours']:<7} {'—':<12} {'—':<8} {res['note']}")
        else:
            print(f"{res['stop']:<6} {res['tier']:<8} {res['n_hours']:<7} {res['r']:<12} {res['p']:<8} {res['note']}")

    valid = [r["r"] for r in results if r["r"] is not None]
    if valid:
        print(f"\nMedian Spearman r across {len(valid)} stops: {sorted(valid)[len(valid)//2]:.3f}")
        positive = sum(1 for r in valid if r > 0)
        print(f"Positive correlation: {positive}/{len(valid)} stops")
        print("\nInterpretation: positive r = observed dwell shape tracks model demand shape.")
        print("This is Birmingham-specific evidence (not TfL BUSTO) for the demand profile validity.")

    # Per-tier aggregate
    print("\nPer-tier median Spearman r:")
    for tier in ("major", "medium", "minor"):
        tier_r = [r["r"] for r in results if r["tier"] == tier and r["r"] is not None]
        if tier_r:
            med = sorted(tier_r)[len(tier_r)//2]
            print(f"  {tier:<8}: {med:.3f}  (n={len(tier_r)})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dwell", type=Path, required=True,
                        help="Path to dwell_profiles.csv (produced by derive_dwell_times.py)")
    args = parser.parse_args()
    run(args.dwell)
