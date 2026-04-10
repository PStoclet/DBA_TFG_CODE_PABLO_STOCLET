"""
Figure 3 — Structural Wage Premiums vs. Bundesliga Baseline
Improved: grouped by position (not alternating rows), clear season labels,
proper colorbar placement, no duplicate titles, publication-ready.
Run from project root: python scripts/figure_03_wage_premium_heatmap.py
"""

import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT     = Path(__file__).resolve().parents[1]
EFF_JSON = ROOT / "docs" / "data" / "efficiency.json"
OUT      = ROOT / "data" / "results" / "07_figures"
OUT.mkdir(parents=True, exist_ok=True)

# ── Data ──────────────────────────────────────────────────────────────────────
df = pd.DataFrame(json.load(open(EFF_JSON)))
df = df.dropna(subset=["Annual_Wages_EUR", "Comp", "Season", "position_group"])

POS_ORDER    = ["Defenders", "Midfielders", "Forwards", "Goalkeepers"]
POS_SHORT    = {"Defenders": "DEF", "Midfielders": "MID",
                "Forwards": "FWD", "Goalkeepers": "GK"}
SEASON_ORDER = ["2022-2023", "2023-2024", "2024-2025"]
SEASON_SHORT = {"2022-2023": "22–23", "2023-2024": "23–24", "2024-2025": "24–25"}

# Leagues to display (Bundesliga is reference, excluded from columns)
DISPLAY_LEAGUES = ["Premier League", "La Liga", "Serie A", "Ligue 1"]

# ── Compute median wage premiums relative to Bundesliga ──────────────────────
medians = (
    df.groupby(["position_group", "Season", "Comp"])["Annual_Wages_EUR"]
    .median()
    .reset_index()
    .rename(columns={"Annual_Wages_EUR": "median_wage"})
)

# Get Bundesliga baseline per (position, season)
bund = medians[medians["Comp"] == "Bundesliga"].rename(
    columns={"median_wage": "bund_wage"}
)[["position_group", "Season", "bund_wage"]]

merged = medians[medians["Comp"].isin(DISPLAY_LEAGUES)].merge(bund, on=["position_group", "Season"])
merged["premium_pct"] = (merged["median_wage"] / merged["bund_wage"] - 1) * 100

# ── Build heatmap matrix ──────────────────────────────────────────────────────
# Rows: position × season (grouped by position, 3 seasons each)
# Columns: 4 leagues

row_labels  = []
row_pos     = []
matrix      = []

for pos in POS_ORDER:
    for season in SEASON_ORDER:
        row_labels.append(f"{SEASON_SHORT[season]}")
        row_pos.append(pos)
        row = []
        for lg in DISPLAY_LEAGUES:
            val = merged.loc[
                (merged["position_group"] == pos) &
                (merged["Season"] == season) &
                (merged["Comp"] == lg),
                "premium_pct"
            ]
            row.append(val.values[0] if len(val) else np.nan)
        matrix.append(row)

matrix = np.array(matrix)  # shape: (12, 4)
n_rows  = len(matrix)
n_cols  = len(DISPLAY_LEAGUES)

# ── Design tokens ─────────────────────────────────────────────────────────────
BG        = "#FFFFFF"
GRAY_DARK = "#2D2D2D"
GRAY_MID  = "#888888"
GRAY_GRID = "#E0E0E0"
DIVIDER   = "#CCCCCC"

# Diverging colormap: blue (below BL) → white (0) → red (above BL)
CMAP = mcolors.LinearSegmentedColormap.from_list(
    "wr",
    ["#1D4ED8", "#93C5FD", "#F1F5F9", "#FCA5A5", "#991B1B"],
    N=256
)
VMAX = 320
VMIN = -VMAX

# ── Figure ────────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(11, 9), facecolor=BG)

# Main heatmap axis + colorbar axis
ax  = fig.add_axes([0.18, 0.08, 0.68, 0.76])
cax = fig.add_axes([0.88, 0.25, 0.018, 0.42])   # slim colorbar on right

# ── Draw cells ────────────────────────────────────────────────────────────────
norm = mcolors.Normalize(vmin=VMIN, vmax=VMAX)

for r in range(n_rows):
    for c in range(n_cols):
        val = matrix[r, c]
        if np.isnan(val):
            bg_color = "#F8F8F8"
            txt = "—"
            txt_color = GRAY_MID
        else:
            bg_color = CMAP(norm(val))
            txt = f"+{val:.0f}%" if val >= 0 else f"{val:.0f}%"
            # Use white text on dark cells, dark text on light cells
            lum = 0.2126 * bg_color[0] + 0.7152 * bg_color[1] + 0.0722 * bg_color[2]
            txt_color = "white" if lum < 0.45 else GRAY_DARK
            txt_weight = "bold" if abs(val) >= 100 else "normal"

        rect = plt.Rectangle([c, n_rows - r - 1], 1, 1,
                              facecolor=bg_color, edgecolor=BG, linewidth=1.5)
        ax.add_patch(rect)
        ax.text(c + 0.5, n_rows - r - 0.5, txt,
                ha="center", va="center", fontsize=9.5,
                color=txt_color,
                fontweight="bold" if abs(val) >= 100 else "normal",
                fontfamily="monospace")

# ── Position group divider lines & labels ─────────────────────────────────────
pos_starts = [0, 3, 6, 9]   # row indices where each position group starts (bottom-up)
pos_ends   = [3, 6, 9, 12]

for i, (pos, start, end) in enumerate(zip(POS_ORDER, pos_starts, pos_ends)):
    # Horizontal divider between groups (except at very top)
    y_div = n_rows - start
    if start > 0:
        ax.axhline(y_div, color=DIVIDER, linewidth=1.8, zorder=5)

    # Position label on the left, centered in the group band
    y_center = n_rows - (start + end) / 2
    ax.text(-0.35, y_center, POS_SHORT[pos],
            ha="right", va="center", fontsize=11,
            fontweight="bold", color=GRAY_DARK,
            fontfamily="sans-serif")

# ── Row (season) tick labels ──────────────────────────────────────────────────
ax.set_yticks([n_rows - r - 0.5 for r in range(n_rows)])
ax.set_yticklabels(row_labels, fontsize=8.5, color=GRAY_MID)
ax.tick_params(axis="y", length=0, pad=4)

# ── Column (league) labels ────────────────────────────────────────────────────
ax.set_xticks([c + 0.5 for c in range(n_cols)])
ax.set_xticklabels(DISPLAY_LEAGUES, fontsize=10.5, fontweight="bold",
                   color=GRAY_DARK, ha="center")
ax.tick_params(axis="x", length=0, pad=6, top=True, labeltop=True,
               bottom=False, labelbottom=False)

# ── Bundesliga reference note ──────────────────────────────────────────────────
ax.text(-0.35, -0.6,
        "Bundesliga = 0%\n(reference)",
        ha="right", va="top", fontsize=7.5, color=GRAY_MID,
        style="italic", transform=ax.transData)

# ── Axis limits & clean spines ────────────────────────────────────────────────
ax.set_xlim(0, n_cols)
ax.set_ylim(0, n_rows)
for spine in ax.spines.values():
    spine.set_visible(False)
ax.set_facecolor(BG)

# ── Colorbar ──────────────────────────────────────────────────────────────────
sm = plt.cm.ScalarMappable(cmap=CMAP, norm=norm)
sm.set_array([])
cb = fig.colorbar(sm, cax=cax)
cb.set_label("Premium vs. Bundesliga (%)", fontsize=8, color=GRAY_MID, labelpad=8)
cb.ax.tick_params(labelsize=7.5, colors=GRAY_MID)
cb.outline.set_visible(False)
# Add zero tick explicitly
cb.set_ticks([-200, -100, 0, 100, 200, 300])
cb.ax.yaxis.set_tick_params(color=GRAY_MID)

# ── Titles ────────────────────────────────────────────────────────────────────
fig.text(0.50, 0.955,
         "Figure 3 — Structural Wage Premiums vs. Bundesliga Baseline",
         ha="center", va="bottom",
         fontsize=14, fontweight="bold", color=GRAY_DARK)
fig.text(0.50, 0.920,
         "Median annual wage (€) relative to Bundesliga by position and season  ·  "
         "Bold = premium ≥ 100%",
         ha="center", va="bottom",
         fontsize=8.5, color=GRAY_MID)

# ── Save ──────────────────────────────────────────────────────────────────────
out_path = OUT / "fig_03_wage_premium_heatmap.png"
fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor=BG)
print(f"Saved → {out_path}")
