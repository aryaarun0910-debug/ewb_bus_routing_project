"""Generates docs/figures/chart_robustness.png -- the six-check robustness
bar chart, using the results in analysis/outputs/robustness.json (produced
by analysis/robustness_analysis.py --json).

Usage
-----
  python analysis/generate_robustness_chart.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt

_REPO = Path(__file__).parent.parent
ROBUSTNESS_JSON = _REPO / "analysis" / "outputs" / "robustness.json"
OUT = _REPO / "docs" / "figures" / "chart_robustness.png"

BG = "#0d1117"
TEXT = "#e6edf3"
GRID = "#30363d"
BLUE = "#1f8fff"


def run() -> None:
    d = json.loads(ROBUSTNESS_JSON.read_text(encoding="utf-8"))

    labels = ["Random\nsplit", "Temporal\nsplit\n(2023→2024)",
              "Anchor\n−20%", "Anchor\n+20%", "Year\nshift", "Season\nshift"]
    values = [
        d["iid_check"]["random_split"]["r2"],
        d["iid_check"]["temporal_split"]["r2"],
        d["anchor_sensitivity"]["runs"]["anchor_minus_20pct"]["r2"],
        d["anchor_sensitivity"]["runs"]["anchor_plus_20pct"]["r2"],
        d["domain_shift"]["year_shift_avg_r2"],
        d["domain_shift"]["season_shift_avg_r2"],
    ]

    fig, ax = plt.subplots(figsize=(12, 6.5))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    bars = ax.bar(labels, values, color=BLUE, width=0.6)

    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.0008,
                f"{value:.3f}", ha="center", va="bottom", color=TEXT, fontsize=12)

    ax.set_ylim(0.90, 0.96)
    ax.set_ylabel("R² (unseen test data)", color=TEXT, fontsize=12)
    ax.set_title("Demand model robustness — R² holds steady across every validation check",
                  color=TEXT, fontsize=15, pad=14)

    ax.tick_params(colors=TEXT, labelsize=12)
    ax.spines[:].set_visible(False)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)

    fig.tight_layout()
    fig.savefig(OUT, dpi=120, facecolor=BG)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    run()
