"""
parse_geods_smartcard.py
========================
Parses UCL/GEoDS "West Midlands Accessibility and Travel Passes" smartcard
data (ESRC Big Data Network / TfWM ENCTS concessionary travel, 2010-2016)
for Ladywood model stop LSOAs.

Source: https://data.geods.ac.uk/dataset/west-midlands-accessibility-and-travel-passes
Real anonymised concessionary smartcard boardings (60+ and disabled
pass-holders) linked to vehicle GPS — the closest public proxy to actual
stop-level ridership available for the West Midlands.

Inputs (place in data/geods/, downloaded manually from GEoDS — requires login)
-------------------------------------------------------------------------------
  trendslsoa60pl.csv       monthly journeys per home LSOA, 60+ pass-holders
  trendslsoadisab.csv      monthly journeys per home LSOA, disabled pass-holders
  eligible_pop_wm.csv      ENCTS-eligible population per LSOA per year
  lsoaclusterpropslong.csv travel-behaviour cluster proportions per LSOA
  mp_lsoa_avl_10_or_more_81_percent.csv   origin-destination journey counts (AVL-matched)

Output
------
  data/geods/ladywood_smartcard_summary.json

Usage
-----
  python scripts/parse_geods_smartcard.py
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

_REPO = Path(__file__).parent.parent
GEODS_DIR = _REPO / "data" / "geods"
OUT = GEODS_DIR / "ladywood_smartcard_summary.json"

TRENDS_60PL = GEODS_DIR / "trendslsoa60pl.csv"
TRENDS_DISAB = GEODS_DIR / "trendslsoadisab.csv"
ELIGIBLE_POP = GEODS_DIR / "eligible_pop_wm.csv"
CLUSTERS = GEODS_DIR / "lsoaclusterpropslong.csv"
OD_FLOWS = GEODS_DIR / "mp_lsoa_avl_10_or_more_81_percent.csv"

CLUSTER_LABELS = {
    "1": "rarely_seen",
    "2": "irregular",
    "3": "regular",
    "4": "withdrawing",
    "5": "withdrawing_post_2014",
    "6": "daily",
}

# LSOA11 codes (this GEoDS data covers 2010-2016, pre-dating the 2021 LSOA
# boundary changes) -- matches scripts/fetch_imd_scores.py STOP_LSOA, which
# is re-derived from corrected GTFS coords. S05 keeps its lsoa11 E01033639
# (its 2021 successor E01034948 didn't exist yet in this period).
STOP_LSOA: dict[str, dict] = {
    "S01": {"lsoa": "E01033615", "name": "New Street Station"},
    "S02": {"lsoa": "E01033624", "name": "Spring St"},
    "S03": {"lsoa": "E01033559", "name": "Jewellery Quarter Station"},
    "S04": {"lsoa": "E01033638", "name": "Soho Hill"},
    "S05": {"lsoa": "E01033639", "name": "Five Ways (Metro)"},
    "S06": {"lsoa": "E01009153", "name": "Dudley Rd"},
    "S07": {"lsoa": "E01033626", "name": "Five Ways Station"},
    "S08": {"lsoa": "E01009143", "name": "Icknield Port Rd"},
    "S09": {"lsoa": "E01033640", "name": "Belgrave Interchange"},
    "S10": {"lsoa": "E01009140", "name": "Ladywood Fire Station"},
    "S11": {"lsoa": "E01009143", "name": "Edgbaston Village Metro"},
    "S12": {"lsoa": "E01009152", "name": "Summerfield Park"},
    "S13": {"lsoa": "E01009346", "name": "City Rd Medical Centre"},
    "S14": {"lsoa": "E01010062", "name": "Mencap Centre"},
    "S15": {"lsoa": "E01009153", "name": "Summerfield Crescent"},
}

LSOA_TO_STOPS: dict[str, list[str]] = defaultdict(list)
for sid, info in STOP_LSOA.items():
    LSOA_TO_STOPS[info["lsoa"]].append(sid)

TARGET_LSOAS = {info["lsoa"] for info in STOP_LSOA.values()}


def _annual_trends(path: Path) -> dict[str, dict[str, float]]:
    """Sum monthly journeys (n) by year for each target LSOA."""
    totals: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lsoa = row["lsoa"].strip('"')
            if lsoa not in TARGET_LSOAS:
                continue
            try:
                n = float(row["n"])
            except ValueError:
                continue
            if n < 0:
                continue
            year = row["month"][:4]
            totals[lsoa][year] += n
    return {l: dict(y) for l, y in totals.items()}


def _eligible_population(path: Path) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = defaultdict(dict)
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lsoa = row["lsoa11cd"].strip()
            if lsoa not in TARGET_LSOAS:
                continue
            try:
                out[lsoa][row["measure"]] = int(float(row["value"]))
            except ValueError:
                continue
    return dict(out)


def _clusters(path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lsoa = row["lsoa11cd"].strip()
            if lsoa not in TARGET_LSOAS:
                continue
            entry = out.setdefault(lsoa, {"total_population": int(float(row["n_tot"])), "clusters": {}})
            label = CLUSTER_LABELS.get(row["cluster"].strip(), row["cluster"])
            entry["clusters"][label] = round(float(row["cluster_prop"]), 4)
    return out


def _od_flows(path: Path) -> dict[str, dict[str, float]]:
    """Total journeys (2014-2016) where target LSOA is origin or destination."""
    outbound: dict[str, float] = defaultdict(float)
    inbound: dict[str, float] = defaultdict(float)
    internal: dict[str, float] = defaultdict(float)
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            orig, dest = row["orig"].strip(), row["dest"].strip()
            if orig not in TARGET_LSOAS and dest not in TARGET_LSOAS:
                continue
            try:
                count = float(row["count"])
            except ValueError:
                continue
            if orig == dest and orig in TARGET_LSOAS:
                internal[orig] += count
                continue
            if orig in TARGET_LSOAS:
                outbound[orig] += count
            if dest in TARGET_LSOAS:
                inbound[dest] += count
    return {
        "outbound_journeys": dict(outbound),
        "inbound_journeys": dict(inbound),
        "internal_journeys": dict(internal),
    }


def run() -> dict:
    print("Parsing GEoDS smartcard data for Ladywood stops...")
    print(f"  TARGET LSOAs: {len(TARGET_LSOAS)}")

    trends_60pl = _annual_trends(TRENDS_60PL)
    print(f"  60+ trend matches: {len(trends_60pl)} LSOAs")

    trends_disab = _annual_trends(TRENDS_DISAB)
    print(f"  Disabled trend matches: {len(trends_disab)} LSOAs")

    eligible_pop = _eligible_population(ELIGIBLE_POP)
    print(f"  Eligible population matches: {len(eligible_pop)} LSOAs")

    clusters = _clusters(CLUSTERS)
    print(f"  Cluster matches: {len(clusters)} LSOAs")

    od = _od_flows(OD_FLOWS)
    print(f"  OD flow matches: outbound={len(od['outbound_journeys'])} "
          f"inbound={len(od['inbound_journeys'])} internal={len(od['internal_journeys'])}")

    result = {}
    sep = "-" * 78
    print(f"\n{'GEoDS Smartcard Summary by Stop (concessionary pass-holders)':^78}")
    print(sep)
    print(f"  {'Stop':<5} {'Name':<28} {'60+ 2016':>10} {'Disab 2016':>11} {'Elig.pop':>9} {'Top cluster':>16}")
    print(f"  {'-'*5} {'-'*28} {'-'*10} {'-'*11} {'-'*9} {'-'*16}")

    for sid, info in STOP_LSOA.items():
        lsoa = info["lsoa"]
        t60 = trends_60pl.get(lsoa, {})
        tdis = trends_disab.get(lsoa, {})
        elig = eligible_pop.get(lsoa, {})
        clus = clusters.get(lsoa, {})

        top_cluster = None
        if clus.get("clusters"):
            top_cluster = max(clus["clusters"].items(), key=lambda kv: kv[1])

        result[sid] = {
            "lsoa": lsoa,
            "stop_name": info["name"],
            "annual_journeys_60plus": t60,
            "annual_journeys_disabled": tdis,
            "eligible_population_by_year": elig,
            "travel_behaviour_clusters": clus.get("clusters"),
            "cluster_total_population": clus.get("total_population"),
            "smartcard_outbound_journeys_2014_2016": od["outbound_journeys"].get(lsoa),
            "smartcard_inbound_journeys_2014_2016": od["inbound_journeys"].get(lsoa),
            "smartcard_internal_journeys_2014_2016": od["internal_journeys"].get(lsoa),
            "data_source": "UCL/GEoDS West Midlands Accessibility and Travel Passes "
                           "(ENCTS concessionary smartcard, TfWM, 2010-2016)",
        }

        n60 = t60.get("2016")
        ndis = tdis.get("2016")
        ep = elig.get("2016") or elig.get(2016) or (max(elig.values()) if elig else None)
        n60_str = f"{n60:,.0f}" if n60 else "n/a"
        ndis_str = f"{ndis:,.0f}" if ndis else "n/a"
        ep_str = f"{ep:,}" if ep else "n/a"
        cl_str = f"{top_cluster[0]} ({top_cluster[1]:.0%})" if top_cluster else "n/a"
        print(f"  {sid}  {info['name']:<28} {n60_str:>10} {ndis_str:>11} {ep_str:>9} {cl_str:>16}")

    print(sep)

    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nWrote {OUT}")
    return result


if __name__ == "__main__":
    run()
