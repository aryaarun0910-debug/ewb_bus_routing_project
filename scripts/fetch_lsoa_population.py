"""
fetch_lsoa_population.py
========================
Downloads ONS Census 2021 usual resident population for Birmingham LSOAs
from the Nomis bulk download API and extracts counts for the 15 model stops.

Census tables
-------------
  TS001  (NM_2021_1) — Number of usual residents
    Total usual residents per LSOA — the denominator for demand scaling.
    Requires c2021_restype_3=0 to select "Total: All usual residents"
    (without it, Nomis returns 3 rows per LSOA: total/household/communal).

  TS007A (NM_2020_1) — Age by 5-year bands
    Used to derive elderly (65+, exact from the 65-69...85+ bands) and
    young (0-14, sum of the 0-4/5-9/10-14 bands — the nearest TS007A
    equivalent to the standard 0-15 "children" cut, one year narrower)
    proportions — key indicators of bus dependency.

Output
------
  data/census/ladywood_population_2021.json

Usage
-----
  python scripts/fetch_lsoa_population.py
"""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

import requests

_REPO   = Path(__file__).parent.parent
OUT_DIR = _REPO / "data" / "census"
OUT     = OUT_DIR / "ladywood_population_2021.json"

HEADERS = {"User-Agent": "ewb-bus-routing/1.0 (EWB design challenge; educational use)"}

# Query exactly the 15 stop LSOAs by code — avoids LA filter syntax issues.
# These are LSOA21 codes (2021 Census boundaries). 14/15 match the LSOA11
# code used in fetch_imd_scores.py; S05's LSOA11 (E01033639, Birmingham 136D)
# was itself split for 2021, so S05 uses its LSOA21 successor E01034948
# (Birmingham 136E) here.
_LSOA_CODES = ",".join([
    "E01033615", "E01033624", "E01033559", "E01033638", "E01034948",
    "E01009153", "E01033626", "E01009143", "E01033640", "E01009140",
    "E01009143", "E01009152", "E01009346", "E01010062", "E01009153",
])

TS001_URL = (
    f"https://www.nomisweb.co.uk/api/v01/dataset/NM_2021_1.data.csv"
    f"?geography={_LSOA_CODES}"
    f"&date=latest"
    f"&c2021_restype_3=0"
    f"&measures=20100"
    f"&select=geography_code,geography_name,obs_value"
)

TS007A_URL = (
    f"https://www.nomisweb.co.uk/api/v01/dataset/NM_2020_1.data.csv"
    f"?geography={_LSOA_CODES}"
    f"&date=latest"
    f"&measures=20100"
    f"&select=geography_code,c2021_age_19_name,obs_value"
)

# TS007A 5-year age bands used to derive the young/elderly proportions
_YOUNG_BANDS = {"Aged 4 years and under", "Aged 5 to 9 years", "Aged 10 to 14 years"}
_ELDERLY_BANDS = {
    "Aged 65 to 69 years", "Aged 70 to 74 years", "Aged 75 to 79 years",
    "Aged 80 to 84 years", "Aged 85 years and over",
}

# LSOA21 codes — see _LSOA_CODES comment above for the S05 LSOA11/LSOA21 split.
STOP_LSOA: dict[str, dict] = {
    "S01": {"lsoa": "E01033615", "name": "New Street Station"},
    "S02": {"lsoa": "E01033624", "name": "Spring St"},
    "S03": {"lsoa": "E01033559", "name": "Jewellery Quarter Station"},
    "S04": {"lsoa": "E01033638", "name": "Soho Hill"},
    "S05": {"lsoa": "E01034948", "name": "Five Ways (Metro)"},
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


def fetch_ts001() -> dict[str, int]:
    """Total usual residents per LSOA."""
    print("Fetching TS001 (usual residents) from Nomis...")
    r = requests.get(TS001_URL, headers=HEADERS, timeout=60)
    r.raise_for_status()
    reader = csv.DictReader(io.StringIO(r.text))
    pop: dict[str, int] = {}
    for row in reader:
        code = row.get("GEOGRAPHY_CODE", "").strip()
        val  = row.get("OBS_VALUE", "").strip()
        if code.startswith("E01") and val:
            try:
                pop[code] = int(float(val))
            except ValueError:
                pass
    print(f"  Got {len(pop)} Birmingham LSOAs")
    return pop


def fetch_ts007a() -> dict[str, dict]:
    """5-year age band counts per LSOA — returns dict of lsoa -> {band: count}."""
    print("Fetching TS007A (age bands) from Nomis...")
    r = requests.get(TS007A_URL, headers=HEADERS, timeout=60)
    r.raise_for_status()
    reader = csv.DictReader(io.StringIO(r.text))

    ages: dict[str, dict] = {}
    for row in reader:
        code  = row.get("GEOGRAPHY_CODE", "").strip()
        label = row.get("C2021_AGE_19_NAME", "").strip()
        val   = row.get("OBS_VALUE", "").strip()
        if not code.startswith("E01") or not val or label == "Total":
            continue
        try:
            ages.setdefault(code, {})[label] = int(float(val))
        except ValueError:
            pass

    print(f"  Got age data for {len(ages)} Birmingham LSOAs")
    return ages


def run() -> dict:
    pop   = fetch_ts001()
    ages  = fetch_ts007a()

    result = {}
    sep = "-" * 65

    print(f"\n{'Population & Age Structure by Stop':^65}")
    print(sep)
    print(f"  {'Stop':<5} {'Name':<30} {'Pop':>5} {'<15':>5} {'65+':>5}")
    print(f"  {'-'*5} {'-'*30} {'-'*5} {'-'*5} {'-'*5}")

    for sid, info in STOP_LSOA.items():
        lsoa = info["lsoa"]
        total = pop.get(lsoa)
        age_data = ages.get(lsoa, {})

        if total is None:
            result[sid] = {
                "lsoa": lsoa, "stop_name": info["name"],
                "note": "not in Birmingham LA download",
            }
            print(f"  {sid}  {info['name']:<30}  no data")
            continue

        elderly = sum(v for k, v in age_data.items() if k in _ELDERLY_BANDS)
        young   = sum(v for k, v in age_data.items() if k in _YOUNG_BANDS)

        elderly_pct = round(100 * elderly / total, 1) if total else 0
        young_pct   = round(100 * young   / total, 1) if total else 0

        result[sid] = {
            "lsoa":            lsoa,
            "stop_name":       info["name"],
            "total_population": total,
            "elderly_65plus":  elderly,
            "elderly_pct":     elderly_pct,
            "young_0to14":     young,
            "young_pct":       young_pct,
            "age_bands_raw":   age_data,
            "data_source":     "Census 2021 TS001 (NM_2021_1) + TS007A (NM_2020_1), Nomis",
        }
        print(f"  {sid}  {info['name']:<30}  {total:>5}  {young_pct:>4.1f}%  {elderly_pct:>4.1f}%")

    print(sep)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nWrote {OUT}")
    return result


if __name__ == "__main__":
    run()
