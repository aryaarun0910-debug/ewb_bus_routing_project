"""
parse_census_car_distance.py
============================
Parses Census 2021 TS045 (car availability) and TS058 (distance to work)
for the 15 Ladywood model stop LSOAs.

TS045 — Car or van availability
  Key metric: % of households with NO car — direct measure of transit dependency.

TS058 — Distance travelled to work
  Key metric: % travelling <5km (short trips) and % travelling 10km+ (long trips).
  Short trips validate stops with high walk/local-bus demand.
  Long trips validate interchange stops (New Street, Five Ways) as origin points.

Output
------
  data/census/ladywood_car_availability.json
  data/census/ladywood_distance_to_work.json

Usage
-----
  python scripts/parse_census_car_distance.py
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import openpyxl

warnings.filterwarnings("ignore")

_REPO = Path(__file__).parent.parent

TS045_XLSX = _REPO / "data" / "census" / "ts045_car_availability_birmingham_lsoa_2021.xlsx"
TS058_XLSX = _REPO / "data" / "census" / "ts058_distance_to_work_birmingham_lsoa_2021.xlsx"
OUT_CAR    = _REPO / "data" / "census" / "ladywood_car_availability.json"
OUT_DIST   = _REPO / "data" / "census" / "ladywood_distance_to_work.json"

# LSOA21 codes (TS045/TS058 are published on 2021 LSOA boundaries), matching
# the re-derived mapping in scripts/fetch_lsoa_population.py. S14's LSOA
# (E01010062) is in Sandwell, outside the Birmingham LA xlsx download, so it
# will report "outside Birmingham LA boundary" below — this is correct, not
# a lookup error.
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


def _load_lsoa_rows(path: Path, n_cols: int) -> dict[str, tuple]:
    wb = openpyxl.load_workbook(path)
    ws = wb.active
    out = {}
    for row in ws.iter_rows(values_only=True):
        if not row[0] or not isinstance(row[0], str):
            continue
        code = row[0].split(" : ")[0].strip()
        if not code.startswith("E"):
            continue
        out[code] = row[:n_cols]
    return out


def parse_ts045() -> dict:
    rows = _load_lsoa_rows(TS045_XLSX, 6)
    print(f"TS045: loaded {len(rows)} Birmingham LSOAs")

    result = {}
    matched = 0
    for sid, info in STOP_LSOA.items():
        row = rows.get(info["lsoa"])
        if row is None:
            result[sid] = {"lsoa": info["lsoa"], "stop_name": info["name"],
                           "note": "outside Birmingham LA boundary"}
            continue
        total     = int(row[1]) or 1
        no_car    = int(row[2])
        one_car   = int(row[3])
        two_car   = int(row[4])
        three_plus = int(row[5])
        result[sid] = {
            "lsoa":            info["lsoa"],
            "stop_name":       info["name"],
            "total_households": total,
            "no_car":          no_car,
            "one_car":         one_car,
            "two_car":         two_car,
            "three_plus_car":  three_plus,
            "no_car_pct":      round(100 * no_car    / total, 1),
            "one_car_pct":     round(100 * one_car   / total, 1),
            "two_plus_car_pct": round(100 * (two_car + three_plus) / total, 1),
            "data_source":     "Census 2021 TS045",
        }
        matched += 1
    print(f"  Matched {matched}/15 stops")
    return result


def parse_ts058() -> dict:
    rows = _load_lsoa_rows(TS058_XLSX, 12)
    print(f"TS058: loaded {len(rows)} Birmingham LSOAs")

    result = {}
    matched = 0
    for sid, info in STOP_LSOA.items():
        row = rows.get(info["lsoa"])
        if row is None:
            result[sid] = {"lsoa": info["lsoa"], "stop_name": info["name"],
                           "note": "outside Birmingham LA boundary"}
            continue
        total      = int(row[1]) or 1
        lt2km      = int(row[2])
        two_5km    = int(row[3])
        five_10km  = int(row[4])
        ten_20km   = int(row[5])
        twenty_30km = int(row[6])
        thirty_40km = int(row[7])
        forty_60km = int(row[8])
        sixty_plus = int(row[9])
        home       = int(row[10])

        short_trip  = lt2km + two_5km           # <5km
        medium_trip = five_10km + ten_20km      # 5-20km
        long_trip   = twenty_30km + thirty_40km + forty_60km + sixty_plus  # 20km+

        result[sid] = {
            "lsoa":              info["lsoa"],
            "stop_name":         info["name"],
            "total_employed":    total,
            "lt2km":             lt2km,
            "two_to_5km":        two_5km,
            "five_to_10km":      five_10km,
            "ten_to_20km":       ten_20km,
            "twenty_plus_km":    twenty_30km + thirty_40km + forty_60km + sixty_plus,
            "works_from_home":   home,
            "short_trip_pct":    round(100 * short_trip  / total, 1),
            "medium_trip_pct":   round(100 * medium_trip / total, 1),
            "long_trip_pct":     round(100 * long_trip   / total, 1),
            "home_worker_pct":   round(100 * home        / total, 1),
            "data_source":       "Census 2021 TS058",
        }
        matched += 1
    print(f"  Matched {matched}/15 stops")
    return result


def print_car_summary(data: dict) -> None:
    sep = "-" * 65
    print(f"\n{'Car Availability by Stop (% no car)':^65}")
    print(sep)
    for sid in sorted(data, key=lambda s: data[s].get("no_car_pct", 0), reverse=True):
        r = data[sid]
        if "no_car_pct" not in r:
            print(f"  {sid}  {r['stop_name']:<30}  no data")
        else:
            bar = "#" * int(r["no_car_pct"] / 3)
            print(f"  {sid}  {r['stop_name']:<30}  {r['no_car_pct']:>5.1f}% no car  {bar}")
    print(sep)


def print_dist_summary(data: dict) -> None:
    sep = "-" * 65
    print(f"\n{'Distance to Work by Stop':^65}")
    print(sep)
    print(f"  {'Stop':<6} {'Name':<30} {'<5km':>6} {'5-20km':>7} {'20km+':>6} {'WFH':>5}")
    print(f"  {'-'*6} {'-'*30} {'-'*6} {'-'*7} {'-'*6} {'-'*5}")
    for sid in sorted(data):
        r = data[sid]
        if "short_trip_pct" not in r:
            print(f"  {sid}  {r['stop_name']:<30}  no data")
        else:
            print(f"  {sid}  {r['stop_name']:<30}  {r['short_trip_pct']:>5.1f}%"
                  f"  {r['medium_trip_pct']:>6.1f}%  {r['long_trip_pct']:>5.1f}%"
                  f"  {r['home_worker_pct']:>4.1f}%")
    print(sep)


if __name__ == "__main__":
    car_data  = parse_ts045()
    dist_data = parse_ts058()

    print_car_summary(car_data)
    print_dist_summary(dist_data)

    OUT_CAR.write_text(json.dumps(car_data,  indent=2), encoding="utf-8")
    OUT_DIST.write_text(json.dumps(dist_data, indent=2), encoding="utf-8")
    print(f"\nWrote {OUT_CAR}")
    print(f"Wrote {OUT_DIST}")
