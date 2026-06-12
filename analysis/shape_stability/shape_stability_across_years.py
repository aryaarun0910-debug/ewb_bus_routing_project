"""
shape_stability_across_years.py
===============================
The "does the demand model decay?" question, answered with three years of
observed data: correlates TfL BUSTO hour-of-day boarding shapes across
2023-24, 2024-25 and 2025-26 (weekday/Saturday/Sunday, Routes 1-149 files).

If year-over-year r is very high (~0.99), demand shapes are structurally
stable and the system's retraining cadence is years, not weeks — the
opposite of a fragile ML system. Also re-checks the weekend single-midday-
peak finding on the newest year (was 2023 an outlier? answer below).

Outputs: shape_stability.json, shape_stability.png (this folder)
"""

import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
BUSTO = HERE.parent / "tfl_busto_full"

YEARS = ["2023_24", "2024_25", "2025_26"]
YEAR_PREFIX = {"2023_24": "2023-2024", "2024_25": "2024-2025", "2025_26": "2025-2026"}
DAYS = ["Weekday", "Saturday", "Sunday"]

def hourly_shape(year, day):
    f = BUSTO / (f"{YEAR_PREFIX[year]}_{year}_{day}_TOTAL_DEMAND_BY_ROUTE_"
                 f"BY_QUARTER_HOUR_Routes_1-149.csv")
    if not f.exists():
        return None
    df = pd.read_csv(f, usecols=["QHr", "Boardings"])
    df["hour"] = df["QHr"].str.slice(0, 2).astype(int)
    h = df.groupby("hour")["Boardings"].sum().reindex(range(24), fill_value=0).values
    return h / h.max() if h.max() > 0 else h

def pearson(a, b):
    return float(np.corrcoef(a, b)[0, 1])

shapes = {d: {y: hourly_shape(y, d) for y in YEARS} for d in DAYS}
results = {}
for d in DAYS:
    have = {y: s for y, s in shapes[d].items() if s is not None}
    results[d.lower()] = {
        "years_available": list(have),
        "pairwise_r": {f"{a} vs {b}": round(pearson(have[a], have[b]), 4)
                       for a, b in combinations(have, 2)},
        "peak_hours_by_year": {y: [int(h) for h in np.argsort(s)[-3:][::-1]]
                               for y, s in have.items()},
    }

fig, axes = plt.subplots(1, 3, figsize=(16, 4.6), facecolor="#F5F4F0")
colors = {"2023_24": "#6B6B6B", "2024_25": "#0E7C7B", "2025_26": "#B33A3A"}
for ax, d in zip(axes, DAYS):
    ax.set_facecolor("#F5F4F0")
    for y in YEARS:
        if shapes[d][y] is not None:
            ax.plot(range(24), shapes[d][y], color=colors[y], lw=2.2,
                    label=y.replace("_", "–"))
    rs = list(results[d.lower()]["pairwise_r"].values())
    ax.set_title(f"{d} — min pairwise r = {min(rs):.3f}" if rs else d,
                 fontsize=12, color="#1A1A1A", fontweight="bold")
    ax.set_xlabel("hour of day", fontsize=9, color="#6B6B6B")
    ax.set_xticks(range(0, 24, 4))
    ax.tick_params(colors="#6B6B6B", labelsize=8)
    for s in ax.spines.values():
        s.set_color("#CCCCCC")
    ax.legend(fontsize=8, frameon=False)
fig.suptitle("Observed hour-of-day demand shape, three consecutive years (TfL BUSTO, Routes 1-149)",
             fontsize=13, color="#1A1A1A", fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig(HERE / "shape_stability.png", dpi=200)

(HERE / "shape_stability.json").write_text(json.dumps(results, indent=2))
print(json.dumps(results, indent=2))
print("Wrote shape_stability.png / shape_stability.json")
