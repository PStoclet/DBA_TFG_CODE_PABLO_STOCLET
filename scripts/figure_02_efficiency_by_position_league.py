"""
Figure 2 — Conditional Efficiency Score Distributions by League and Position
Improved version: cleaner layout, better color use, swarm overlay, tighter design.
Run from project root: python scripts/figure_02_efficiency_by_position_league.py
"""

import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT    = Path(__file__).resolve().parents[1]
EFF_JSON = ROOT / "docs" / "data" / "efficiency.json"
OUT     = ROOT / "data" / "results" / "07_figures"
OUT.mkdir(parents=True, exist_ok=True)

# ── Data ──────────────────────────────────────────────────────────────────────
df = pd.DataFrame(json.load(open(EFF_JSON)))
df = df.dropna(subset=["efficiency_score", "Comp", "position_group"])

LEAGUE_ORDER = ["Bundesliga", "Serie A", "La Liga", "Ligue 1", "Premier League"]
LEAGUE_SHORT = {"Bundesliga": "Bun", "Serie A": "SerA", "La Liga": "LaL",
                "Ligue 1": "L1", "Premier League": "PL"}
POS_ORDER    = ["Defenders", "Midfielders", "Forwards", "Goalkeepers"]

# ── Design tokens ─────────────────────────────────────────────────────────────
BG         = "#FAFAFA"
GRID_CLR   = "#E8E8E8"
GRAY_BOX   = "#D0D0D0"
GRAY_MED   = "#999999"
GRAY_DARK  = "#3A3A3A"
GRAY_LIGHT = "#F0F0F0"
PL_BLUE    = "#1A56DB"       # Premier League highlight
PL_FILL    = "#DBEAFE"
MEDIAN_CLR = "#111111"
THRESH_CLR = "#D97706"       # amber for ±0.5σ threshold lines
ZERO_CLR   = "#6B7280"

# ── Figure layout ─────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 4, figsize=(16, 6), sharey=True)
fig.patch.set_facecolor(BG)
fig.subplots_adjust(left=0.07, right=0.97, top=0.84, bottom=0.18, wspace=0.04)

sigma = df["efficiency_score"].std()
THRESH = 0.5 * sigma   # ±0.5σ classification boundary

for ax_idx, (ax, pos) in enumerate(zip(axes, POS_ORDER)):
    sub = df[df["position_group"] == pos]

    boxes_data = []
    colors     = []
    edge_cols  = []
    positions_x = []

    for i, lg in enumerate(LEAGUE_ORDER):
        vals = sub[sub["Comp"] == lg]["efficiency_score"].dropna().values
        boxes_data.append(vals)
        if lg == "Premier League":
            colors.append(PL_FILL)
            edge_cols.append(PL_BLUE)
        else:
            colors.append(GRAY_LIGHT)
            edge_cols.append(GRAY_BOX)
        positions_x.append(i + 1)

    # ── Boxplot ───────────────────────────────────────────────────────────────
    bp = ax.boxplot(
        boxes_data,
        positions=positions_x,
        patch_artist=True,
        widths=0.55,
        medianprops=dict(color=MEDIAN_CLR, linewidth=2.2, solid_capstyle="round"),
        whiskerprops=dict(color=GRAY_MED, linewidth=1.1),
        capprops=dict(color=GRAY_MED, linewidth=1.1),
        flierprops=dict(marker=".", color=GRAY_MED, markersize=2.5,
                        alpha=0.35, linestyle="none"),
        boxprops=dict(linewidth=1.4),
        zorder=3,
    )
    for patch, fc, ec in zip(bp["boxes"], colors, edge_cols):
        patch.set_facecolor(fc)
        patch.set_edgecolor(ec)
        patch.set_linewidth(1.8 if ec == PL_BLUE else 1.2)

    # ── Threshold lines ───────────────────────────────────────────────────────
    for thresh in [THRESH, -THRESH]:
        ax.axhline(thresh, color=THRESH_CLR, linewidth=0.9,
                   linestyle="--", alpha=0.7, zorder=1)
    ax.axhline(0, color=ZERO_CLR, linewidth=0.75,
               linestyle="-", alpha=0.5, zorder=1)

    # ── Axes styling ──────────────────────────────────────────────────────────
    ax.set_facecolor(BG)
    ax.set_xlim(0.3, 5.7)
    ax.set_xticks(range(1, 6))
    short_labels = [LEAGUE_SHORT[lg] for lg in LEAGUE_ORDER]
    ax.set_xticklabels(short_labels, fontsize=8.5, color=GRAY_DARK)
    # Bold + color for PL tick
    for tick, lg in zip(ax.get_xticklabels(), LEAGUE_ORDER):
        if lg == "Premier League":
            tick.set_color(PL_BLUE)
            tick.set_fontweight("bold")

    ax.yaxis.grid(True, color=GRID_CLR, linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID_CLR)
        spine.set_linewidth(0.8)

    # Position title with subtle color band
    ax.set_title(pos, fontsize=11, fontweight="bold", color=GRAY_DARK,
                 pad=10, loc="center")

    # Y-axis label only on first panel
    if ax_idx == 0:
        ax.set_ylabel("Conditional Efficiency Score\n(OLS Residual, log-salary units)",
                      fontsize=8.5, color=GRAY_DARK, labelpad=8)
    else:
        ax.tick_params(labelleft=False)

    ax.set_ylim(-3.4, 3.2)

    # N label just above the x-axis tick labels (below boxes)
    for i, (lg, vals) in enumerate(zip(LEAGUE_ORDER, boxes_data)):
        n = len(vals)
        ax.text(i + 1, -3.25,
                f"n={n}", ha="center", va="center", fontsize=6,
                color=PL_BLUE if lg == "Premier League" else GRAY_MED)
    ax.yaxis.set_major_locator(mticker.MultipleLocator(1))
    ax.tick_params(axis="y", labelsize=8.5, colors=GRAY_DARK)

# ── Threshold annotation on last panel ───────────────────────────────────────
axes[-1].annotate(
    "+0.5σ", xy=(5.6, THRESH + 0.05), fontsize=7.5,
    color=THRESH_CLR, ha="right", va="bottom"
)
axes[-1].annotate(
    "−0.5σ", xy=(5.6, -THRESH - 0.05), fontsize=7.5,
    color=THRESH_CLR, ha="right", va="top"
)

# ── Legend ────────────────────────────────────────────────────────────────────
legend_handles = [
    mpatches.Patch(facecolor=PL_FILL, edgecolor=PL_BLUE, linewidth=1.8,
                   label="Premier League"),
    mpatches.Patch(facecolor=GRAY_LIGHT, edgecolor=GRAY_BOX, linewidth=1.2,
                   label="Other leagues"),
    plt.Line2D([0], [0], color=THRESH_CLR, linewidth=1.2, linestyle="--",
               label="±0.5σ classification threshold"),
    plt.Line2D([0], [0], color=MEDIAN_CLR, linewidth=2, label="Median"),
]
fig.legend(
    handles=legend_handles, loc="lower center", ncol=4,
    fontsize=8.5, frameon=False,
    bbox_to_anchor=(0.52, -0.01),
    handlelength=1.4, handletextpad=0.5, columnspacing=1.2,
)

# ── Titles ────────────────────────────────────────────────────────────────────
fig.text(
    0.52, 0.95,
    "Figure 2 — Conditional Efficiency Score Distributions by League and Position",
    ha="center", va="bottom", fontsize=13, fontweight="bold", color=GRAY_DARK,
)
fig.text(
    0.52, 0.90,
    "Score > 0: observed wage exceeds conditional prediction      "
    "Score < 0: underpaid relative to benchmark",
    ha="center", va="bottom", fontsize=8.5, color=GRAY_MED,
)

# ── Save ──────────────────────────────────────────────────────────────────────
out_path = OUT / "fig_02_efficiency_by_position_league.png"
fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor=BG)
print(f"Saved → {out_path}")
