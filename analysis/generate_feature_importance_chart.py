"""Generates docs/figures/chart_feature_importance.png -- a horizontal bar
chart of the top demand-model features, using analysis/outputs/explainability.json
(produced by analysis/explainability.py --json).

Usage
-----
  python analysis/explainability.py --json   # writes analysis/outputs/explainability.json
  python analysis/generate_feature_importance_chart.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt

_REPO = Path(__file__).parent.parent
EXPLAIN_JSON = _REPO / "analysis" / "outputs" / "explainability.json"
OUT = _REPO / "docs" / "figures" / "chart_feature_importance.png"

BG = "#0d1117"
TEXT = "#e6edf3"
GRID = "#30363d"
BLUE = "#1f8fff"

N_FEATURES = 10


def run() -> None:
    d = json.loads(EXPLAIN_JSON.read_text(encoding="utf-8"))
    top = d["top_features"][:N_FEATURES]
    # Plot with the highest-ranked feature at the top.
    top = list(reversed(top))

    labels = [f["feature"] for f in top]
    values = [f["combined_rank_score"] for f in top]

    fig, ax = plt.subplots(figsize=(10, 7))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    bars = ax.barh(labels, values, color=BLUE, height=0.6)

    for bar, value in zip(bars, values):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2,
                 f"{value:.3f}", ha="left", va="center", color=TEXT, fontsize=11)

    ax.set_xlim(0, max(values) * 1.2)
    ax.set_xlabel("Combined rank score (mean of normalised gain + permutation importance)",
                  color=TEXT, fontsize=11)
    ax.set_title(f"What drives predicted demand — top {N_FEATURES} XGBoost features\n"
                 f"({d['dataset_rows']:,} rows, {d['n_perm_repeats']} permutation repeats)",
                 color=TEXT, fontsize=14, pad=14)

    ax.tick_params(colors=TEXT, labelsize=12)
    ax.spines[:].set_visible(False)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)

    fig.tight_layout()
    fig.savefig(OUT, dpi=120, facecolor=BG, bbox_inches="tight")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    run()
