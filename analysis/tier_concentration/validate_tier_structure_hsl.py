"""
validate_tier_structure_hsl.py
==============================
Second-country, true stop-level check of the Ladywood model's tier design.

HSL (Helsinki) publishes observed boardings PER STOP (open APC-equivalent,
6,708 stops). The Ladywood model assumes demand concentrates across stops in
a major/medium/minor tier structure. Question: in a real network measured at
the stop level, how is boarding volume distributed across volume terciles —
and does the Ladywood synthetic dataset's concentration match that reality?

Outputs: tier share table (printed + JSON). Ladywood comparison uses the
regenerated dataset in beast/hardening/ablation (same generator as the repo).
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
HSL = HERE.parent / "international" / "helsinki_stop_boardings.csv"
LADYWOOD = (HERE.parent.parent / "hardening" / "ablation" /
            "prediction model" / "map_demand_dataset.csv")

def tier_shares(per_stop: pd.Series) -> dict:
    """Share of total boardings captured by each volume tercile of stops."""
    s = per_stop.sort_values(ascending=False)
    n = len(s)
    thirds = np.array_split(s.values, 3)
    tot = s.sum()
    return {
        "n_stops": int(n),
        "top_third_share": round(float(thirds[0].sum() / tot), 3),
        "middle_third_share": round(float(thirds[1].sum() / tot), 3),
        "bottom_third_share": round(float(thirds[2].sum() / tot), 3),
        "gini": round(float(gini(s.values)), 3),
    }

def gini(x):
    x = np.sort(np.asarray(x, dtype=float))
    n = len(x)
    return float((2 * np.arange(1, n + 1) - n - 1).dot(x) / (n * x.sum()))

# Helsinki: observed boardings per stop
hsl = pd.read_csv(HSL)
hsl_shares = tier_shares(hsl["Nousijamaa"])

# Ladywood synthetic dataset: total boardings per stop
lw = pd.read_csv(LADYWOOD, usecols=["stop_id", "boardings"])
lw_shares = tier_shares(lw.groupby("stop_id")["boardings"].sum())

out = {"helsinki_observed_6708_stops": hsl_shares,
       "ladywood_modelled_15_stops": lw_shares}
print(json.dumps(out, indent=2))
(HERE / "tier_structure_hsl.json").write_text(json.dumps(out, indent=2))
print("Wrote tier_structure_hsl.json")
