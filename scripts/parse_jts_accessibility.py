"""
parse_jts_accessibility.py
===========================
Parses DfT Journey Time Statistics for Ladywood model stop LSOAs.

JTS0501 — Travel time to nearest hospital by public transport/walking
JTS0502 — Travel time to nearest GP by public transport/walking

Key columns (minutes by public transport):
  HospPTt  — minutes to nearest hospital by PT
  HospPTp  — % of population within 30 min of hospital by PT
  GPPTt    — minutes to nearest GP by PT
  GPPTp    — % of population within 15 min of GP by PT

Output
------
  data/dft/ladywood_jts_accessibility.json

Usage
-----
  python scripts/parse_jts_accessibility.py
"""

from __future__ import annotations

import json
from pathlib import Path

from odf.opendocument import load
from odf import table, text

_REPO   = Path(__file__).parent.parent
JTS0501 = _REPO / "data" / "dft" / "jts0501.ods"
JTS0502 = _REPO / "data" / "dft" / "jts0502.ods"
OUT     = _REPO / "data" / "dft" / "ladywood_jts_accessibility.json"

# LSOA11 codes (DfT JTS is published on 2011 boundaries), matching
# scripts/fetch_imd_scores.py STOP_LSOA, re-derived from corrected GTFS
# coords. NOTE: jts0501.ods / jts0502.ods are not present in data/dft/ --
# this script cannot currently be run; codes updated for consistency only.
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


def _odf_rows(path: Path, sheet_name: str | None = None, max_rows: int = 100000) -> tuple[list[str], list[list[str]]]:
    """Return (header, data_rows) from first matching sheet."""
    doc = load(path)
    sheets = doc.spreadsheet.getElementsByType(table.Table)

    target = None
    for s in sheets:
        name = s.getAttribute("name")
        if sheet_name is None or (sheet_name and sheet_name.lower() in name.lower()):
            target = s
            break
    if target is None and sheets:
        target = sheets[0]

    all_rows = []
    for row in target.getElementsByType(table.TableRow)[:max_rows]:
        cells = row.getElementsByType(table.TableCell)
        vals  = ["".join(str(p) for p in cell.getElementsByType(text.P)) for cell in cells]
        all_rows.append(vals)

    # Find header row: contains 'LSOA' or 'lsoa_code' in col 0
    header_idx = 0
    for i, row in enumerate(all_rows):
        if row and ("lsoa" in str(row[0]).lower() or str(row[0]).strip().upper().startswith("E0")):
            header_idx = i
            break

    # The row before data is the header
    header = all_rows[header_idx - 1] if header_idx > 0 else all_rows[0]
    data   = all_rows[header_idx:]
    return header, data


def _parse_jts(path: Path, col_keywords: list[str]) -> dict[str, dict]:
    """Parse a JTS ODS and extract named columns for Ladywood LSOAs."""
    print(f"Parsing {path.name}...")
    header, data = _odf_rows(path)
    header_lower = [str(h).lower().strip() for h in header]
    print(f"  {len(data)} data rows, {len(header)} columns")
    print(f"  Header sample: {header[:8]}")

    # Find column indices for our keywords
    col_indices: dict[str, int] = {}
    for kw in col_keywords:
        for j, h in enumerate(header_lower):
            if kw.lower() in h:
                col_indices[kw] = j
                break

    # Find LSOA code column (col 0 or first col starting with E01...)
    lsoa_col = 0

    result: dict[str, dict] = {}
    for row in data:
        if not row or not str(row[0]).strip().startswith("E0"):
            continue
        lsoa_code = str(row[lsoa_col]).strip()
        vals = {}
        for kw, col in col_indices.items():
            v = row[col] if len(row) > col else ""
            try:
                vals[kw] = float(str(v).strip())
            except ValueError:
                vals[kw] = None
        result[lsoa_code] = vals

    print(f"  Matched {len(result)} LSOAs")
    return result


def run() -> dict:
    # Hospital PT travel time columns
    hosp_data = _parse_jts(JTS0501, ["HospPTt", "HospPTp", "HospCyct", "HospCart"])
    # GP PT travel time columns
    gp_data   = _parse_jts(JTS0502, ["GPPTt", "GPPTp", "GPCyct", "GPCart"])

    result = {}
    sep = "-" * 70
    print(f"\n{'JTS Accessibility by Stop':^70}")
    print(sep)
    print(f"  {'Stop':<5} {'Name':<30} {'Hosp PT':>8} {'Hosp%':>6} {'GP PT':>7} {'GP%':>5}")
    print(f"  {'-'*5} {'-'*30} {'-'*8} {'-'*6} {'-'*7} {'-'*5}")

    for sid, info in STOP_LSOA.items():
        lsoa = info["lsoa"]
        hosp = hosp_data.get(lsoa, {})
        gp   = gp_data.get(lsoa, {})

        hosp_pt = hosp.get("HospPTt")
        hosp_pct = hosp.get("HospPTp")
        gp_pt   = gp.get("GPPTt")
        gp_pct  = gp.get("GPPTp")

        result[sid] = {
            "lsoa":                lsoa,
            "stop_name":           info["name"],
            "hospital_pt_minutes": hosp_pt,
            "hospital_pt_pct_30min": hosp_pct,
            "hospital_car_minutes": hosp.get("HospCart"),
            "gp_pt_minutes":       gp_pt,
            "gp_pt_pct_15min":     gp_pct,
            "gp_car_minutes":      gp.get("GPCart"),
            "data_source":         "DfT Journey Time Statistics (JTS0501, JTS0502)",
        }

        h_str  = f"{hosp_pt:.0f}min"  if hosp_pt  else "n/a"
        hp_str = f"{hosp_pct:.0f}%"   if hosp_pct else "n/a"
        g_str  = f"{gp_pt:.0f}min"    if gp_pt    else "n/a"
        gp_str = f"{gp_pct:.0f}%"     if gp_pct   else "n/a"
        print(f"  {sid}  {info['name']:<30} {h_str:>8} {hp_str:>6} {g_str:>7} {gp_str:>5}")

    print(sep)

    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nWrote {OUT}")
    return result


if __name__ == "__main__":
    run()
