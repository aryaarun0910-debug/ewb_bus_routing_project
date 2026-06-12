"""
opal_asymmetry_test.py
======================
The test that closed the last open shape question — in the design's favour.

The Ladywood minor-stop curve was deliberately designed ASYMMETRIC: residential
low-volume stops board heavily in the AM peak and mostly alight in the PM
(commuters coming home). Boarding-only datasets (TfL BUSTO, r=0.796; Wellington,
r=0.809) could never test this — and Wellington's privacy suppression covers
every minor-stop cell. Sydney's Opal release has tap-ON and tap-OFF counts,
15-minute bins, unsuppressed at usable volumes (TfNSW applied small-count
perturbation, disclosed): the asymmetry is directly measurable.

Data (open, no registration): TfNSW Open Data, "Opal Tap on and Tap off"
  time-loc_20160725-31_2.csv and time-loc_20160808-14.csv
  https://opendata.transport.nsw.gov.au/dataset/opal-tap-on-and-tap-off

Result: AM(6-9) vs PM(15-18) board/alight ratios rise monotonically down the
volume tiers — major ~1.0 (symmetric), medium 1.67/0.76, minor 1.87/0.68.
Low-volume locations board in the morning and alight in the evening, exactly
as the Ladywood minor curve encodes. The ~0.80 minor-tier correlations in
boarding-only validations are an artefact of the data type, not a design error.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
# Adjust if your copies live elsewhere (files are ~30 MB total, open licence)
DATA_FILES = [HERE.parent / "apc_hunt" / "sydney_opal" / f for f in
              ("time-loc_20160725-31_2.csv", "time-loc_20160808-14.csv")]

df = pd.concat(pd.read_csv(f) for f in DATA_FILES)
df = df[df["mode"] == "bus"].copy()
df["count"] = pd.to_numeric(df["count"], errors="coerce")
df = df.dropna(subset=["count"])
df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
df = df[df["date"].dt.dayofweek < 5]
df["hour"] = df["time"].str.split(":").str[0].astype(int)

# Volume terciles by total weekday tap-ons per location (mirrors the repo's
# major/medium/minor importance tiers)
tot = df[df["tap"] == "on"].groupby("loc")["count"].sum()
q1, q2 = tot.quantile([1 / 3, 2 / 3])
df["tier"] = df["loc"].map(pd.cut(tot, bins=[-np.inf, q1, q2, np.inf],
                                  labels=["minor", "medium", "major"]))

results = {
    "weekday_rows": int(len(df)),
    "locations": int(df["loc"].nunique()),
    "total_taps": int(df["count"].sum()),
    "note": "TfNSW small-count perturbation applied at source (disclosed); "
            "two weeks, Jul-Aug 2016",
    "board_alight_ratio_by_tier": {},
}
for t in ["major", "medium", "minor"]:
    sub = df[df["tier"] == t]
    am = sub[sub["hour"].between(6, 9)]
    pm = sub[sub["hour"].between(15, 18)]
    ratio = lambda d: float(d[d["tap"] == "on"]["count"].sum() /
                            max(d[d["tap"] == "off"]["count"].sum(), 1))
    results["board_alight_ratio_by_tier"][t] = {
        "am_6_9": round(ratio(am), 3), "pm_15_18": round(ratio(pm), 3)}

m = results["board_alight_ratio_by_tier"]["minor"]
results["asymmetric_minor_design_vindicated"] = bool(
    m["am_6_9"] > 1.3 and m["pm_15_18"] < 0.8)

print(json.dumps(results, indent=2))
(HERE / "opal_asymmetry.json").write_text(json.dumps(results, indent=2))
print("Wrote opal_asymmetry.json")
