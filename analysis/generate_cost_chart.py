"""Generates docs/figures/chart_cost.png -- a two-panel economic-impact
chart (annual operating cost, fixed vs dynamic; and where the saving goes),
using the summary stats in analysis/outputs/cost_model.json (produced by
analysis/cost_model.py --json).

Usage
-----
  python analysis/cost_model.py --json   # writes analysis/outputs/cost_model.json
  python analysis/generate_cost_chart.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt

_REPO = Path(__file__).parent.parent
COST_JSON = _REPO / "analysis" / "outputs" / "cost_model.json"
OUT = _REPO / "docs" / "figures" / "chart_cost.png"

BG = "#0d1117"
TEXT = "#e6edf3"
GRID = "#30363d"
GRAY = "#999999"
GREEN = "#2ea043"


def _style_axis(ax) -> None:
    ax.set_facecolor(BG)
    ax.tick_params(colors=TEXT, labelsize=11)
    ax.spines[:].set_visible(False)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def run() -> None:
    d = json.loads(COST_JSON.read_text(encoding="utf-8"))

    fixed_yr = d["fixed_schedule"]["total_cost_yr"]
    dynamic_yr = d["dynamic_routing"]["total_cost_yr"]
    opex_saving_yr = d["opex_saving"]["per_year_gbp"]

    net_saving = d["net_annual_saving_gbp"]
    deployment_cost = d["deployment"]["total_annual_deployment_gbp"]
    social_value = d["social_value_per_yr_gbp"]
    breakeven = d["breakeven_months"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6.5))
    fig.patch.set_facecolor(BG)

    # --- Panel 1: annual operating cost, fixed vs dynamic ---
    bars1 = ax1.bar(
        ["Fixed\nschedule", "Dynamic\nrouting"],
        [fixed_yr, dynamic_yr],
        color=[GRAY, GREEN],
        width=0.55,
    )
    for bar, value in zip(bars1, [fixed_yr, dynamic_yr]):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1500,
                  f"£{value:,.0f}", ha="center", va="bottom",
                  color=TEXT, fontsize=13, fontweight="bold")
    ax1.set_ylim(0, fixed_yr * 1.18)
    ax1.set_ylabel("Annual operating cost (£)", color=TEXT, fontsize=12)
    ax1.set_title(f"Operating cost — £{opex_saving_yr:,.0f}/yr saved\n"
                   "(12.5% fewer vehicle-km, DfT BUS0404)",
                   color=TEXT, fontsize=13, pad=12)
    _style_axis(ax1)

    # --- Panel 2: where the saving goes ---
    labels2 = ["Deployment\ncost/yr", "Net opex\nsaving/yr", "Social value\n/yr (TAG)"]
    values2 = [deployment_cost, net_saving, social_value]
    colors2 = [GRAY, GREEN, "#58a6ff"]
    bars2 = ax2.bar(labels2, values2, color=colors2, width=0.6)
    for bar, value in zip(bars2, values2):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 800,
                  f"£{value:,.0f}", ha="center", va="bottom",
                  color=TEXT, fontsize=13, fontweight="bold")
    ax2.set_ylim(0, social_value * 1.18)
    ax2.set_ylabel("£ / year", color=TEXT, fontsize=12)
    ax2.set_title(f"Annual impact — break-even in {breakeven} months",
                   color=TEXT, fontsize=13, pad=12)
    _style_axis(ax2)

    fig.suptitle("Economic model — DfT BUS0404 (operating costs) / TAG A1.3 (passenger time value)",
                  color=TEXT, fontsize=14, y=1.01)

    fig.tight_layout()
    fig.savefig(OUT, dpi=120, facecolor=BG, bbox_inches="tight")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    run()
