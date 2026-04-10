"""
Figure 5 — Bootstrap-Validated Underpaid Player Rankings
No external title, no caption. Left: player table. Right: rank interval plot.
"""
import json, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
from pathlib import Path

ROOT  = Path(__file__).resolve().parents[1]
OUT   = ROOT / "data" / "results" / "07_figures"
OUT.mkdir(parents=True, exist_ok=True)

# ── Data ──────────────────────────────────────────────────────────────────────
boot = pd.read_csv(ROOT / "data/results/04_robustness/01_bootstrap/ranking_bootstrap_uncertainty_final.csv")
eff  = pd.DataFrame(json.load(open(ROOT / "docs" / "data" / "efficiency.json")))

top = boot[boot["side"]=="Underpaid"].nsmallest(15,"mean_rank").reset_index(drop=True)

# Compute annual gap: fitted - actual = actual*(exp(-eff_score)-1)
eff_sub = eff.merge(top[["Player","Season","Team"]], on=["Player","Season","Team"], how="inner")
gap_map = {(r.Player, r.Season, r.Team): r.Annual_Wages_EUR*(np.exp(-r.efficiency_score)-1)
           for _, r in eff_sub.iterrows()}
top["gap_eur"] = top.apply(lambda r: gap_map.get((r.Player, r.Season, r.Team), np.nan), axis=1)
top["season_yr"] = top["Season"].str[:4].astype(int) + 1  # e.g. 2024-2025 → 2025

# ── Design ────────────────────────────────────────────────────────────────────
BG        = "#FFFFFF"
GRAY_DARK = "#2D2D2D"
GRAY_MID  = "#777777"
GRAY_GRID = "#EEEEEE"
GRAY_ROW  = "#F7F7F7"
GREEN     = "#166534"
PL1_BG    = "#DCFCE7"  # highlight row 1
PL1_CLR   = "#15803D"
INTERVAL  = "#9CA3AF"  # gray interval line
DOT_CLR   = "#374151"

N = len(top)

fig = plt.figure(figsize=(14, 7.5), facecolor=BG)

# Left table + right plot side by side
ax_tab = fig.add_axes([0.01, 0.08, 0.39, 0.80])   # table
ax_plt = fig.add_axes([0.42, 0.08, 0.54, 0.80])   # rank plot

# ── LEFT: table ───────────────────────────────────────────────────────────────
ax_tab.set_xlim(0, 10)
ax_tab.set_ylim(-0.5, N + 1.2)
ax_tab.axis("off")

# Column headers
COLS = [("Player", 0.15, "left"),
        ("Club",   4.35, "left"),
        ("Season", 7.0,  "center"),
        ("Annual gap", 9.2, "right")]
for label, x, ha in COLS:
    ax_tab.text(x, N + 0.7, label, ha=ha, va="center",
                fontsize=9, fontweight="bold", color=GRAY_DARK)

# Divider under header
ax_tab.axhline(N + 0.35, color=GRAY_DARK, linewidth=0.8, xmin=0, xmax=1)

# Rows
for i, row in top.iterrows():
    y    = N - i - 0.5
    is_1 = (i == 0)
    bg   = PL1_BG if is_1 else (GRAY_ROW if i % 2 == 0 else BG)
    rect = plt.Rectangle([0, y - 0.45], 10, 0.9, facecolor=bg, zorder=0)
    ax_tab.add_patch(rect)

    txt_c = PL1_CLR if is_1 else GRAY_DARK
    fw    = "bold" if is_1 else "normal"

    # Rank number
    ax_tab.text(-0.1, y, f"{i+1}", ha="right", va="center",
                fontsize=8, color=GRAY_MID)
    # Player
    ax_tab.text(0.15, y, row["Player"], ha="left", va="center",
                fontsize=9, color=txt_c, fontweight=fw)
    # Club
    ax_tab.text(4.35, y, row["Team"], ha="left", va="center",
                fontsize=8.5, color=txt_c if is_1 else GRAY_MID)
    # Season (year only)
    ax_tab.text(7.0, y, str(row["season_yr"]), ha="center", va="center",
                fontsize=8.5, color=txt_c if is_1 else GRAY_DARK, fontweight=fw)
    # Gap
    gap = row["gap_eur"]
    if pd.notna(gap):
        gap_str = f"−€{gap/1e6:.2f}M" if gap >= 1e5 else f"−€{gap/1e3:.0f}K"
        ax_tab.text(9.2, y, gap_str, ha="right", va="center",
                    fontsize=8.5, color=PL1_CLR if is_1 else GREEN, fontweight=fw)

ax_tab.axhline(-0.1, color=GRAY_GRID, linewidth=0.6)

# Column header lines
ax_tab.text(0.15, N + 1.1, "Player", ha="left", fontsize=8, color=GRAY_MID)

# ── RIGHT: bootstrap rank plot ────────────────────────────────────────────────
ax_plt.set_facecolor(BG)
ax_plt.set_xlim(N + 1, 0.3)   # reversed: rank 1 on right
ax_plt.set_ylim(-0.5, N - 0.5)

# Horizontal grid
for i in range(N):
    y    = N - i - 1
    is_1 = (i == 0)
    if i % 2 == 0:
        rect = plt.Rectangle([0.3, y - 0.45], N + 0.7, 0.9,
                              facecolor=PL1_BG if is_1 else GRAY_ROW, zorder=0)
        ax_plt.add_patch(rect)

for i, row in top.iterrows():
    y    = N - i - 1
    is_1 = (i == 0)
    p10  = row["p10_rank"]
    p90  = row["p90_rank"]
    mean = row["mean_rank"]
    rate = row["appear_rate"] * 100

    # Interval line
    lw   = 2.5 if is_1 else 1.4
    clr  = PL1_CLR if is_1 else INTERVAL
    ax_plt.plot([p10, p90], [y, y], color=clr, linewidth=lw,
                solid_capstyle="round", zorder=3)

    # Mean dot
    ax_plt.scatter(mean, y, color=PL1_CLR if is_1 else DOT_CLR,
                   s=55 if is_1 else 35, zorder=4, linewidths=0)

    # Appear rate label (right side)
    ax_plt.text(0.5, y, f"{rate:.0f}%",
                ha="left", va="center", fontsize=7.5,
                color=PL1_CLR if is_1 else GRAY_MID,
                fontweight="bold" if is_1 else "normal")

# Appear rate column header
ax_plt.text(0.5, N - 0.1, "Appear\nrate",
            ha="left", va="bottom", fontsize=7.5, color=GRAY_MID)

ax_plt.set_yticks([])
ax_plt.set_xlabel("Bootstrap Rank  (1 = most underpaid)", fontsize=9, color=GRAY_DARK)
ax_plt.xaxis.set_major_locator(mticker.MultipleLocator(5))
ax_plt.tick_params(axis="x", labelsize=8.5, colors=GRAY_DARK)
for sp in ax_plt.spines.values():
    sp.set_edgecolor(GRAY_GRID)
    sp.set_linewidth(0.7)

# Divider between panels
fig.text(0.415, 0.08, "", fontsize=1)
ax_plt.axvline(N + 0.5, color=GRAY_GRID, linewidth=0.5, zorder=0)

# ── Legend ────────────────────────────────────────────────────────────────────
legend_els = [
    mpatches.Patch(facecolor=PL1_BG, edgecolor=PL1_CLR, linewidth=1.5,
                   label="Pablo Torre — rank 1 in every resample drawn"),
    plt.Line2D([0],[0], color=INTERVAL, linewidth=1.5,
               label="P10–P90 bootstrap interval"),
    plt.Line2D([0],[0], color=DOT_CLR, marker="o", markersize=5,
               linewidth=0, label="Mean bootstrap rank"),
]
fig.legend(handles=legend_els, loc="lower center", ncol=3,
           fontsize=8, frameon=False, bbox_to_anchor=(0.52, 0.00),
           handlelength=1.4, columnspacing=1.5)

# ── Header ────────────────────────────────────────────────────────────────────
fig.text(0.50, 0.97,
         "Bootstrap-Validated Underpaid Player Rankings  ·  800 Resamples  ·  "
         "Bars: P10–P90 rank intervals",
         ha="center", va="top", fontsize=9, color=GRAY_DARK, fontweight="bold")
fig.text(0.50, 0.935,
         "Appear rate: share of resamples in which the player is drawn into the sample  "
         "(distinct from rank stability)",
         ha="center", va="top", fontsize=7.5, color=GRAY_MID)

# Dividing line between table and plot
fig.patches.append(mpatches.FancyArrowPatch(
    (0.41, 0.08), (0.41, 0.92), transform=fig.transFigure,
    color=GRAY_GRID, linewidth=0.8, arrowstyle="-"))

fig.savefig(OUT / "fig_05_bootstrap_rankings.png",
            dpi=300, bbox_inches="tight", facecolor=BG)
print(f"Saved → {OUT / 'fig_05_bootstrap_rankings.png'}")
