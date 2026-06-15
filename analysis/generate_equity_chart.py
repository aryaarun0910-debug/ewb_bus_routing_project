"""Generates docs/figures/chart_equity.png -- the allocation-mismatch bar
chart comparing the fixed schedule to the dynamic optimiser, using the
summary stats in analysis/outputs/equity.json (produced by analysis/equity.py).

Usage
-----
  python analysis/generate_equity_chart.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt

_REPO = Path(__file__).parent.parent
EQUITY_JSON = _REPO / "analysis" / "outputs" / "equity.json"
OUT = _REPO / "docs" / "figures" / "chart_equity.png"

BG = "#0d1117"
TEXT = "#e6edf3"
GRID = "#30363d"
GRAY = "#999999"
ORANGE = "#FFA500"


def run() -> None:
    summary = json.loads(EQUITY_JSON.read_text(encoding="utf-8"))["summary"]
    fixed = summary["allocation_mismatch_fixed"]
    dynamic = summary["allocation_mismatch_dynamic"]
    n_snapshots = summary["mismatch_snapshots_compared"]

    fig, ax = plt.subplots(figsize=(8.5, 7))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    bars = ax.bar(
        ["Fixed\nschedule", "Dynamic\noptimiser"],
        [fixed, dynamic],
        color=[GRAY, ORANGE],
        width=0.6,
    )

    for bar, value in zip(bars, [fixed, dynamic]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.012,
                f"{value:.3f}", ha="center", va="bottom",
                color=TEXT, fontsize=16, fontweight="bold")

    ax.set_ylim(0, 0.5)
    ax.set_ylabel("Allocation-mismatch index\n(0 = service exactly matches demand)",
                   color=TEXT, fontsize=12)
    ax.set_title(f"Bus allocation vs. real demand\n"
                  f"(avg. across {n_snapshots} scenario/window snapshots)",
                  color=TEXT, fontsize=14, pad=14)

    ax.tick_params(colors=TEXT, labelsize=12)
    ax.spines[:].set_visible(False)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)

    fig.tight_layout()
    fig.savefig(OUT, dpi=120, facecolor=BG)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    run()
