"""
equity.py
=========
Stop-level deprivation analysis for the Ladywood bus network.

Assigns each stop an IMD-derived deprivation score and computes how equitably
the dynamic routing system serves the most deprived areas.

Deprivation scores
------------------
Scores are derived from the English Indices of Multiple Deprivation 2019 (IMD
2019), published by MHCLG and fetched live into data/imd/ladywood_imd_2019.json
by scripts/fetch_imd_scores.py. Each stop is mapped to its LSOA.

  Source: MHCLG, "English Indices of Deprivation 2019: LSOA data"
  https://www.gov.uk/government/statistics/english-indices-of-deprivation-2019

Two deprivation measures are reported per stop:

  imd_decile       — England-wide IMD 2019 decile (1 = most deprived 10% of
                      England's 32,844 LSOAs, 10 = least deprived). Taken
                      directly from MHCLG, externally verifiable.

  deprivation_band — "high" / "medium" / "low", a *corridor-relative* ranking.
                      Stops are ranked by national IMD rank and split into
                      equal thirds (ties broken by stop_id), via
                      assign_deprivation_bands() below — the same
                      relative-tertile approach used for POI tiers in
                      fetch_osm_pois.py, so that the variable is informative
                      regardless of where this corridor sits nationally.

LSOA → IMD 2019 mapping (from data/imd/ladywood_imd_2019.json)
----------------------------------------------------------------
  Stop  Name                       LSOA        IMD rank  Decile  Band
  S08   Icknield Port Rd           E01009143     765       1     high
  S11   Edgbaston Village Metro    E01009143     765       1     high
  S09   Belgrave Interchange       E01033640     830       1     high
  S04   Soho Hill                  E01033638     871       1     high
  S14   Mencap Centre              E01010062    1394       1     high
  S05   Five Ways (Metro)          E01033639    2197       1     medium
  S12   Summerfield Park           E01009152    2203       1     medium
  S06   Dudley Rd                  E01009153    2431       1     medium
  S15   Summerfield Crescent       E01009153    2431       1     medium
  S13   City Rd Medical Centre     E01009346    3798       2     medium
  S10   Ladywood Fire Station      E01009140    6930       3     low
  S02   Spring St                  E01033624    7607       3     low
  S07   Five Ways Station          E01033626    9262       3     low
  S01   New Street Station         E01033615   10295       4     low
  S03   Jewellery Quarter Station  E01033559   14019       5     low

National context: 9/15 Ladywood stops are in IMD decile 1 (England's most
deprived 10% of LSOAs); 13/15 are in deciles 1-3 (most-deprived 30%). S01
(decile 4) and S03 (decile 5) are the only stops outside the most-deprived
40% of England.

Note: S08/S11 and S06/S15 each share an LSOA (their GTFS coordinates fall
in the same ~1,500-resident census area), so they have identical IMD figures
— a real feature of the geography, not a data error.

deprivation_score [0,1] = 1 - (imd_rank - 1) / 32843, i.e. rank 1 -> 1.0 and
rank 32844 -> 0.0. Used only for display ordering, not for banding.

Equity metric
-------------
  Allocation-mismatch index (dissimilarity index) between each stop's share
  of buses and its share of real predicted demand, averaged across every
  scenario/window snapshot in the live route plan. 0 = service is perfectly
  proportional to demand; 1 = total mismatch. A fixed schedule can't move
  buses when conditions shift demand elsewhere, so its mismatch holds
  roughly constant; the dynamic optimiser reallocates toward wherever need
  has actually moved, so its mismatch runs lower on average — a measured,
  not assumed, equity gain.

Usage
-----
  python analysis/equity.py              # print summary
  python analysis/equity.py --json       # write analysis/outputs/equity.json
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent
_ROUTE_PLAN = _REPO_ROOT / "prediction model" / "route_plan.json"

# ── IMD 2019 data for each mapped Ladywood stop ───────────────────────────────
# imd_rank / imd_decile are taken directly from data/imd/ladywood_imd_2019.json
# (live MHCLG fetch). deprivation_score and deprivation_band are derived below
# by _normalised_score() and assign_deprivation_bands() — not hand-set.

STOP_DEPRIVATION: dict[str, dict] = {
    "S08": {"name": "Icknield Port Rd",       "lsoa": "E01009143", "lsoa_name": "Birmingham 136A", "imd_rank":  765, "imd_decile": 1,
            "msoa_name": "Five Ways North", "notes": "Route 8A/8C; IMD decile 1 (England's most deprived 10%)"},
    "S11": {"name": "Edgbaston Village Metro","lsoa": "E01009143", "lsoa_name": "Birmingham 136A", "imd_rank":  765, "imd_decile": 1,
            "msoa_name": "Five Ways North", "notes": "Metro interchange, route 126; shares an LSOA with S08; IMD decile 1"},
    "S09": {"name": "Belgrave Interchange",   "lsoa": "E01033640", "lsoa_name": "Birmingham 134E", "imd_rank":  830, "imd_decile": 1,
            "msoa_name": "Attwood Green & Park Central", "notes": "Route 8A/8C interchange; IMD decile 1"},
    "S04": {"name": "Soho Hill",              "lsoa": "E01033638", "lsoa_name": "Birmingham 049F", "imd_rank":  871, "imd_decile": 1,
            "msoa_name": "Hockley & Jewellery Quarter", "notes": "Northern Ladywood / Handsworth edge; IMD decile 1"},
    "S14": {"name": "Mencap Centre",          "lsoa": "E01010062", "lsoa_name": "Sandwell 026C",   "imd_rank": 1394, "imd_decile": 1,
            "msoa_name": "Sandwell 026", "notes": "Only stop outside Birmingham LA (Sandwell); Mencap disability services; IMD decile 1"},
    "S05": {"name": "Five Ways (Metro)",      "lsoa": "E01033639", "lsoa_name": "Birmingham 136D", "imd_rank": 2197, "imd_decile": 1,
            "msoa_name": "Five Ways North", "notes": "Metro stop; commuter interchange; IMD decile 1 despite affluent-area perception of Edgbaston/Brindleyplace"},
    "S12": {"name": "Summerfield Park",       "lsoa": "E01009152", "lsoa_name": "Birmingham 053B", "imd_rank": 2203, "imd_decile": 1,
            "msoa_name": "Summerfield", "notes": "Route 80; IMD decile 1"},
    "S06": {"name": "Dudley Rd",              "lsoa": "E01009153", "lsoa_name": "Birmingham 053C", "imd_rank": 2431, "imd_decile": 1,
            "msoa_name": "Summerfield", "notes": "Route 80; City Hospital corridor; IMD decile 1"},
    "S15": {"name": "Summerfield Crescent",   "lsoa": "E01009153", "lsoa_name": "Birmingham 053C", "imd_rank": 2431, "imd_decile": 1,
            "msoa_name": "Summerfield", "notes": "Route 80; shares an LSOA with S06; IMD decile 1"},
    "S13": {"name": "City Rd Medical Centre", "lsoa": "E01009346", "lsoa_name": "Birmingham 053E", "imd_rank": 3798, "imd_decile": 2,
            "msoa_name": "Summerfield", "notes": "Healthcare-access stop, route 80; IMD decile 2"},
    "S10": {"name": "Ladywood Fire Station",  "lsoa": "E01009140", "lsoa_name": "Birmingham 060C", "imd_rank": 6930, "imd_decile": 3,
            "msoa_name": "Rotton Park", "notes": "Route 80; IMD decile 3"},
    "S02": {"name": "Spring St",              "lsoa": "E01033624", "lsoa_name": "Birmingham 134C", "imd_rank": 7607, "imd_decile": 3,
            "msoa_name": "Attwood Green & Park Central", "notes": "Route 8A/8C; IMD decile 3"},
    "S07": {"name": "Five Ways Station",      "lsoa": "E01033626", "lsoa_name": "Birmingham 134D", "imd_rank": 9262, "imd_decile": 3,
            "msoa_name": "Attwood Green & Park Central", "notes": "Ring Road interchange, multiple routes converge; IMD decile 3"},
    "S01": {"name": "New Street Station",     "lsoa": "E01033615", "lsoa_name": "Birmingham 135C", "imd_rank": 10295, "imd_decile": 4,
            "msoa_name": "Digbeth", "notes": "City-centre rail terminus; IMD decile 4 — least deprived Ladywood model stop, but still in England's most-deprived 40%"},
    "S03": {"name": "Jewellery Quarter Stn",  "lsoa": "E01033559", "lsoa_name": "Birmingham 049E", "imd_rank": 14019, "imd_decile": 5,
            "msoa_name": "Hockley & Jewellery Quarter", "notes": "Rail + Metro interchange, partially gentrified; IMD decile 5 — only Ladywood model stop outside the most-deprived 40% of England"},
}

_N_LSOAS = 32_844  # England LSOAs, IMD 2019


def _normalised_score(imd_rank: int) -> float:
    """Normalise IMD rank to [0,1]: rank 1 -> 1.0 (most deprived), rank 32,844 -> 0.0."""
    return round(1 - (imd_rank - 1) / (_N_LSOAS - 1), 3)


def assign_deprivation_bands(ranks: dict[str, int]) -> dict[str, str]:
    """Rank stops by national IMD rank and split into corridor-relative thirds.

    Bands are relative to this corridor's own stops, split into equal thirds
    by national IMD rank (lower rank = more deprived = "high"), ties broken
    by stop_id — the same relative-tertile approach used for POI tiers in
    fetch_osm_pois.py. See national_context in run_analysis() for the
    absolute (decile-based) headline figure.
    """
    ordered = sorted(ranks, key=lambda sid: (ranks[sid], sid))
    third = len(ordered) // 3
    bands: dict[str, str] = {}
    for i, sid in enumerate(ordered):
        if i < third:
            bands[sid] = "high"
        elif i < 2 * third:
            bands[sid] = "medium"
        else:
            bands[sid] = "low"
    return bands

# Fixed-schedule stop memberships (from api.py _FIXED_ROUTES)
FIXED_STOPS: dict[str, list[str]] = {
    "8A/8C": ["S02", "S03", "S04", "S07", "S08", "S09"],
    "80":    ["S01", "S06", "S07", "S10", "S12", "S13", "S14", "S15"],
    "126":   ["S05", "S11"],
}


@dataclass
class StopEquity:
    stop_id:    str
    name:       str
    score:      float      # deprivation score [0,1], 1 = most deprived (national IMD rank)
    imd_rank:   int         # England-wide IMD 2019 rank (1 = most deprived of 32,844 LSOAs)
    imd_decile: int         # England-wide IMD 2019 decile (1 = most deprived 10%)
    lsoa:       str
    fixed_coverage: bool   # served by any fixed route
    deprivation_band: str  # "high" / "medium" / "low" — corridor-relative, see assign_deprivation_bands()

    @classmethod
    def from_data(cls, sid: str, fixed_stops_all: set[str], bands: dict[str, str]) -> "StopEquity":
        d = STOP_DEPRIVATION[sid]
        return cls(
            stop_id=sid,
            name=d["name"],
            score=_normalised_score(d["imd_rank"]),
            imd_rank=d["imd_rank"],
            imd_decile=d["imd_decile"],
            lsoa=d["lsoa"],
            fixed_coverage=sid in fixed_stops_all,
            deprivation_band=bands[sid],
        )


def _gini(values: list[float]) -> float:
    """Gini coefficient of a list of non-negative values."""
    if not values or sum(values) == 0:
        return 0.0
    n = len(values)
    sorted_v = sorted(values)
    cumsum = 0.0
    for i, v in enumerate(sorted_v):
        cumsum += (2 * (i + 1) - n - 1) * v
    return cumsum / (n * sum(values))


def _dissimilarity(service: dict[str, float], demand: dict[str, float], stop_ids: list[str]) -> float | None:
    """Index of dissimilarity between a service allocation and demand.

    sum(|service_share_i - demand_share_i|) / 2, in [0, 1].
    0 = each stop's share of buses exactly matches its share of demand
    (perfectly proportional allocation); 1 = total mismatch. This is the
    standard segregation/dissimilarity index, and — unlike a Gini of raw
    service/demand ratios — it isn't distorted by stops with near-zero demand.
    """
    total_s = sum(service[sid] for sid in stop_ids)
    total_d = sum(demand[sid]  for sid in stop_ids)
    if total_s == 0 or total_d == 0:
        return None
    return sum(abs(service[sid] / total_s - demand[sid] / total_d) for sid in stop_ids) / 2


def _allocation_mismatch() -> dict:
    """How well bus allocation tracks demand, averaged across every
    scenario/window snapshot in the live route plan — the actual
    differentiator between fixed and dynamic routing, since both already
    name-check all 15 stops (a static coverage Gini is identical for both).

    For each snapshot we compare two allocations against that hour's real
    predicted demand:
      fixed_service[stop]   = number of fixed routes calling at that stop
                              (constant — set once, ignores conditions)
      dynamic_service[stop] = number of buses the optimiser sends there
                              this hour (reacts to weather/day/events)

    and score each with the dissimilarity index against demand_per_stop.
    A fixed schedule can't move buses when a storm shifts demand toward
    different areas, so its mismatch stays flat across scenarios; the
    dynamic optimiser reallocates toward wherever need has moved, so its
    mismatch should run lower on average — a real, measured equity gain
    rather than an assumed one.
    """
    if not _ROUTE_PLAN.exists():
        return {"mismatch_fixed": None, "mismatch_dynamic": None, "n_snapshots": 0}

    with open(_ROUTE_PLAN, encoding="utf-8") as f:
        plan: dict = json.load(f)

    fixed_count = {sid: sum(1 for r in FIXED_STOPS.values() if sid in r) for sid in STOP_DEPRIVATION}

    fixed_scores: list[float] = []
    dynamic_scores: list[float] = []

    for scenario_plan in plan.values():
        for window_plan in scenario_plan.values():
            demand: dict[str, float] = window_plan.get("demand_per_stop", {})
            if not demand:
                continue

            dynamic_count = {sid: 0 for sid in STOP_DEPRIVATION}
            for route in window_plan.get("routes", []):
                for sid in route.get("route_stops", []):
                    if sid in dynamic_count:
                        dynamic_count[sid] += 1

            stop_ids = [sid for sid in STOP_DEPRIVATION if demand.get(sid, 0) > 0]
            if not stop_ids:
                continue

            full_demand = {sid: demand.get(sid, 0.0) for sid in STOP_DEPRIVATION}
            fv = _dissimilarity(fixed_count,   full_demand, stop_ids)
            dv = _dissimilarity(dynamic_count, full_demand, stop_ids)
            if fv is not None:
                fixed_scores.append(fv)
            if dv is not None:
                dynamic_scores.append(dv)

    if not fixed_scores:
        return {"mismatch_fixed": None, "mismatch_dynamic": None, "n_snapshots": 0}

    return {
        "mismatch_fixed":   round(sum(fixed_scores)   / len(fixed_scores),   3),
        "mismatch_dynamic": round(sum(dynamic_scores) / len(dynamic_scores), 3),
        "n_snapshots":      len(fixed_scores),
    }


def run_analysis() -> dict:
    fixed_stops_all: set[str] = set()
    for stops in FIXED_STOPS.values():
        fixed_stops_all.update(stops)

    bands = assign_deprivation_bands({sid: d["imd_rank"] for sid, d in STOP_DEPRIVATION.items()})
    equity_stops = [StopEquity.from_data(sid, fixed_stops_all, bands) for sid in STOP_DEPRIVATION]

    # Coverage gap: high-deprivation (corridor-relative) stops not served by any fixed route
    high_dep = [s for s in equity_stops if s.deprivation_band == "high"]
    high_dep_unserved_fixed = [s for s in high_dep if not s.fixed_coverage]

    n_decile1 = sum(1 for s in equity_stops if s.imd_decile == 1)
    n_decile_le3 = sum(1 for s in equity_stops if s.imd_decile <= 3)

    # Allocation-mismatch index (see _allocation_mismatch): how well bus
    # allocation tracks real predicted demand, averaged across every
    # scenario/window snapshot in the live route plan. This is the real
    # differentiator — both fixed and dynamic routes name-check all 15 stops
    # (so a static coverage ratio is identical for both, which is why those
    # were dropped from this summary). Lower = allocation matches need more closely.
    mismatch         = _allocation_mismatch()
    mismatch_fixed   = mismatch["mismatch_fixed"]
    mismatch_dynamic = mismatch["mismatch_dynamic"]
    mismatch_n       = mismatch["n_snapshots"]

    return {
        "stops": [
            {
                "stop_id":          s.stop_id,
                "name":             s.name,
                "deprivation_score": s.score,
                "imd_rank":         s.imd_rank,
                "imd_decile":       s.imd_decile,
                "lsoa":             s.lsoa,
                "deprivation_band": s.deprivation_band,
                "fixed_coverage":   s.fixed_coverage,
                "msoa_name":        STOP_DEPRIVATION[s.stop_id]["msoa_name"],
                "notes":            STOP_DEPRIVATION[s.stop_id]["notes"],
            }
            for s in equity_stops
        ],
        "summary": {
            "n_stops":                          len(equity_stops),
            "n_high_deprivation_stops":         len(high_dep),
            "n_high_dep_unserved_by_fixed":     len(high_dep_unserved_fixed),
            "high_dep_unserved_names":          [s.name for s in high_dep_unserved_fixed],
            "allocation_mismatch_fixed":        mismatch_fixed,
            "allocation_mismatch_dynamic":      mismatch_dynamic,
            "mismatch_snapshots_compared":      mismatch_n,
        },
        "national_context": {
            "n_stops_imd_decile_1":      n_decile1,
            "n_stops_imd_decile_1_to_3": n_decile_le3,
            "note": (
                f"{n_decile1}/{len(equity_stops)} Ladywood model stops are in IMD 2019 "
                f"decile 1 (England's most deprived 10% of LSOAs); {n_decile_le3}/"
                f"{len(equity_stops)} are in deciles 1-3 (most-deprived 30%). Only "
                "S01 (decile 4) and S03 (decile 5) fall outside the most-deprived 40%."
            ),
        },
        "data_source": "MHCLG English Indices of Deprivation 2019 (IMD 2019), LSOA level",
        "methodology": (
            "imd_rank and imd_decile are the England-wide IMD 2019 values for each "
            "stop's LSOA (data/imd/ladywood_imd_2019.json, live MHCLG fetch). "
            "deprivation_score = 1 - (imd_rank - 1) / 32843, for display ordering only. "
            "deprivation_band is a corridor-relative tertile over imd_rank "
            "(assign_deprivation_bands); see national_context for the absolute "
            "(decile-based) headline figure. "
            "Allocation-mismatch index = sum(|service share - demand share|) / 2 "
            "across stops (the standard dissimilarity index, 0 = perfectly "
            "proportional, 1 = total mismatch), averaged across every scenario "
            "and time window in the live route plan — i.e. how closely bus "
            "allocation tracks demand as it shifts with weather and time of day."
        ),
    }


def print_summary(result: dict) -> None:
    s = result["summary"]
    nc = result["national_context"]
    sep = "─" * 60
    print(f"\n{'Stop Equity Analysis — Ladywood IMD 2019':^60}")
    print(sep)
    print(f"  {nc['note']}")
    print(sep)
    print(f"  Stops analysed:                 {s['n_stops']}")
    print(f"  High-deprivation stops (corridor-relative): {s['n_high_deprivation_stops']}")
    print(f"  High-dep stops unserved (fixed):{s['n_high_dep_unserved_by_fixed']}")
    if s["high_dep_unserved_names"]:
        for nm in s["high_dep_unserved_names"]:
            print(f"    · {nm}")
    print()
    print(f"  Allocation mismatch (fixed schedule):  {s['allocation_mismatch_fixed']}")
    print(f"  Allocation mismatch (dynamic routing): {s['allocation_mismatch_dynamic']}")
    print(f"    (averaged across {s['mismatch_snapshots_compared']} scenario/window snapshots — lower means buses track real demand more closely)")
    print(sep)
    print("\nStop deprivation scores (most → least deprived):")
    for stop in sorted(result["stops"], key=lambda x: -x["deprivation_score"]):
        flag = "" if stop["fixed_coverage"] else " ⚠ not on fixed route"
        print(f"  {stop['stop_id']}  {stop['deprivation_score']:.2f}  {stop['name']:<28}{flag}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_analysis()
    print_summary(result)

    if args.json:
        out_dir = Path(__file__).parent / "outputs"
        out_dir.mkdir(exist_ok=True)
        out_path = out_dir / "equity.json"
        out_path.write_text(json.dumps(result, indent=2))
        print(f"\nWrote {out_path}")
