"""
validate_shape_vs_busto.py
==========================
Validates UK2026-82's synthetic hour-of-day demand-shape curves (PROFILE_FN in
generate_map_dataset.py) against OBSERVED per-stop boardings: TfL BUSTO
(autumn 2023, boardings by stop by quarter-hour, TfL Open Data licence).

This is the strongest public test available in the UK: TfWM does not release
per-stop hourly boardings for Ladywood, so London's observed curves serve as a
transferable *shape prior*. The claim under test is narrow and honest:
"our modelled commuter-peak SHAPE resembles how UK urban bus boardings
actually distribute across the day" — not that London levels equal Ladywood's.

Outputs (this folder): shape_validation.png, shape_validation.json,
SHAPE_VALIDATION.md
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
BUSTO_DIR = HERE.parent / "data_mined" / "tfl_busto"

# ── The repo's weekday boarding-factor curves (copied verbatim from
#    generate_map_dataset.py PROFILE_FN — boarding factor, index = hour) ──────
REPO_CURVES = {
    "major": [0.04, 0.02, 0.01, 0.01, 0.05, 0.18, 0.42, 0.85, 1.00, 0.70, 0.48,
              0.50, 0.55, 0.52, 0.50, 0.62, 0.88, 0.95, 0.72, 0.50, 0.35, 0.28,
              0.20, 0.10],
    "medium": [0.03, 0.01, 0.01, 0.01, 0.04, 0.14, 0.35, 0.75, 0.90, 0.60, 0.42,
               0.45, 0.48, 0.46, 0.44, 0.56, 0.78, 0.85, 0.65, 0.44, 0.30, 0.22,
               0.15, 0.08],
    "minor": [0.02, 0.01, 0.00, 0.00, 0.03, 0.12, 0.38, 1.00, 0.88, 0.40, 0.25,
              0.22, 0.25, 0.22, 0.26, 0.30, 0.28, 0.24, 0.20, 0.16, 0.12, 0.10,
              0.06, 0.04],
}

def norm(v):
    v = np.asarray(v, dtype=float)
    return v / v.max() if v.max() > 0 else v

def load_day(day):
    f = BUSTO_DIR / f"2023_24_{day}_demand_by_quarter_hour_routes1-149.csv"
    if not f.exists():
        return None
    try:
        df = pd.read_csv(f, usecols=["QHr", "STOPCODE", "Boardings"])
    except (PermissionError, OSError):
        print(f"{day}: file locked (still downloading) — skipped")
        return None
    df["hour"] = df["QHr"].str.slice(0, 2).astype(int)
    return df

results = {}
day = "Weekday"
df = load_day(day)
print(f"{day}: {len(df):,} stop/route/quarter-hour rows, "
      f"{df['STOPCODE'].nunique():,} unique stops, "
      f"{df['Boardings'].sum():,.0f} total boardings")

# Observed network-wide hourly shape
hourly = df.groupby("hour")["Boardings"].sum().reindex(range(24), fill_value=0)
obs_all = norm(hourly.values)

# Stop-volume terciles as a proxy for the repo's major/medium/minor tiers
stop_tot = df.groupby("STOPCODE")["Boardings"].sum()
q1, q2 = stop_tot.quantile([1 / 3, 2 / 3])
tier_of = pd.cut(stop_tot, bins=[-np.inf, q1, q2, np.inf],
                 labels=["minor", "medium", "major"])
df["tier"] = df["STOPCODE"].map(tier_of)

obs_tier = {}
for tier in ["major", "medium", "minor"]:
    h = (df[df["tier"] == tier].groupby("hour")["Boardings"].sum()
         .reindex(range(24), fill_value=0))
    obs_tier[tier] = norm(h.values)

# Pearson correlations: repo modelled curve vs observed
def pearson(a, b):
    return float(np.corrcoef(a, b)[0, 1])

results["weekday"] = {
    "n_rows": int(len(df)),
    "n_stops": int(df["STOPCODE"].nunique()),
    "pearson_overall_vs_major_curve": pearson(obs_all, norm(REPO_CURVES["major"])),
    "pearson_by_tier": {
        t: pearson(obs_tier[t], norm(REPO_CURVES[t])) for t in obs_tier
    },
    "observed_peak_hours": [int(h) for h in hourly.nlargest(3).index],
    "modelled_peak_hours_major": [8, 17, 16],
    "observed_hourly_shape": [round(float(x), 4) for x in obs_all],
}

# Optional: Saturday/Sunday if downloaded
for day2, repo_floor in [("Saturday", 0.75), ("Sunday", 0.50)]:
    d2 = load_day(day2)
    if d2 is None:
        continue
    h2 = d2.groupby("hour")["Boardings"].sum().reindex(range(24), fill_value=0)
    # repo saturday/sunday major curve = wd * factor, mid-boost for sat, floored
    wd = np.array(REPO_CURVES["major"])
    if day2 == "Saturday":
        sat = wd * 0.75
        sat[10:17] *= 1.30
        model2 = np.maximum(0.30, sat)
    else:
        model2 = np.maximum(0.15, wd * 0.50)
    results[day2.lower()] = {
        "pearson_vs_major_curve": pearson(norm(h2.values), norm(model2)),
        "observed_peak_hours": [int(h) for h in h2.nlargest(3).index],
    }
    print(f"{day2}: r = {results[day2.lower()]['pearson_vs_major_curve']:.3f}")

# ── Chart ────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(16, 4.6), facecolor="#F5F4F0")
hours = np.arange(24)
for ax, tier in zip(axes, ["major", "medium", "minor"]):
    ax.set_facecolor("#F5F4F0")
    r = results["weekday"]["pearson_by_tier"][tier]
    ax.plot(hours, norm(REPO_CURVES[tier]), color="#6B6B6B", lw=2.2,
            ls="--", label="UK2026-82 modelled curve")
    ax.plot(hours, obs_tier[tier], color="#0E7C7B", lw=2.6,
            label="TfL observed (autumn 2023)")
    ax.set_title(f"{tier} stops — Pearson r = {r:.3f}",
                 fontsize=12, color="#1A1A1A", fontweight="bold")
    ax.set_xlabel("hour of day", fontsize=9, color="#6B6B6B")
    ax.set_xticks(range(0, 24, 4))
    ax.tick_params(colors="#6B6B6B", labelsize=8)
    for s in ax.spines.values():
        s.set_color("#CCCCCC")
    ax.legend(fontsize=8, frameon=False)
fig.suptitle("Hour-of-day demand shape: modelled (synthetic) vs observed (TfL BUSTO, "
             "boardings per stop per quarter-hour) — weekday",
             fontsize=13, color="#1A1A1A", fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig(HERE / "shape_validation.png", dpi=200)
print("Wrote shape_validation.png")

(HERE / "shape_validation.json").write_text(json.dumps(results, indent=2))
print("Wrote shape_validation.json")
print(json.dumps(results["weekday"]["pearson_by_tier"], indent=2))
