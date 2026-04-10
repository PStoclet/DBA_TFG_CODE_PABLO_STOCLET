"""
Figure 1 — Hierarchy-first layout: temporal OOS validation (C) as full-width primary band;
in-sample fit (A) and RMSE (B) as a compact supporting row. Horizontal lollipops in A/B.
All numeric values fixed per thesis specification (no data-driven overrides).
"""

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.transforms import blended_transform_factory

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "results" / "07_figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif", "Times", "Nimbus Roman"],
        "font.size": 11,
        "axes.titlesize": 12,
        "axes.labelsize": 11.5,
        "xtick.labelsize": 11,
        "ytick.labelsize": 11,
        "figure.dpi": 150,
        "savefig.dpi": 400,
        "axes.linewidth": 0.55,
        "axes.edgecolor": "#2a2a2a",
        "axes.labelcolor": "#1a1a1a",
        "xtick.color": "#1a1a1a",
        "ytick.color": "#1a1a1a",
    }
)

NAVY = "#0D1B2A"
GRAY_LIGHT = "#E6E6E6"
GRAY_CONNECT = "#C4C4C4"
GRID_H = "#EBEBEB"  # horizontal panels: x-grid
GRID_V = "#E6E6E6"  # panel C: y-grid
RED_REF = "#B71C1C"
BG = "#FFFFFF"
PANEL_C_BG = "#F4F5F7"

positions = ["DEF", "MID", "FWD", "GK"]
x = np.arange(len(positions))
y_idx = np.arange(len(positions))

adj_r2 = np.array([0.713, 0.692, 0.690, 0.634])
rmse = np.array([0.631, 0.672, 0.707, 0.722])
oos_s1 = np.array([0.13, 0.18, 0.51, 0.52])
oos_s2 = np.array([0.17, 0.21, 0.56, 0.53])

REF_OOS = 0.15

SPLIT_A = "Train 22–24 / Test 24–25"
SPLIT_B = "Train 23–25 / Test 22–23"
TITLE = "Model fit, prediction error, and temporal validation by position"

FS_TITLE = 13.5
FS_C = 13.5
FS_AB = 11.25
FS_AXIS = 11.5
FS_TICK = 11
FS_VAL = 10.75
FS_KEY = 9.75


def style_ab(ax):
    ax.set_facecolor(BG)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.xaxis.grid(True, color=GRID_H, linewidth=0.32, linestyle="-", alpha=0.75)
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", length=3.5, width=0.55, color="#333333")


def style_c(ax):
    ax.set_facecolor(PANEL_C_BG)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#2f2f2f")
    ax.spines["bottom"].set_color("#2f2f2f")
    ax.spines["left"].set_linewidth(0.75)
    ax.spines["bottom"].set_linewidth(0.75)
    ax.yaxis.grid(True, color=GRID_V, linewidth=0.32, linestyle="-", alpha=0.72)
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", length=3.5, width=0.55, color="#333333")


def lollipop_horizontal(ax, xvals, xlim, xlabel, title, fmt="{:.3f}"):
    """DEF at top of y-axis to mirror left-to-right reading in panel C."""
    floor = xlim[0]
    for yi, xv in zip(y_idx, xvals):
        ax.plot(
            [floor, xv],
            [yi, yi],
            color=GRAY_LIGHT,
            linewidth=1.2,
            solid_capstyle="round",
            zorder=1,
        )
        ax.scatter(
            [xv],
            [yi],
            s=62,
            color=NAVY,
            edgecolors=NAVY,
            linewidths=0.85,
            zorder=3,
        )
        ax.annotate(
            fmt.format(xv),
            (xv, yi),
            xytext=(7, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=FS_VAL,
            color="#111111",
        )
    ax.set_yticks(y_idx)
    ax.set_yticklabels(positions, fontsize=FS_TICK)
    ax.set_xlim(*xlim)
    ax.set_ylim(-0.55, len(positions) - 0.45)
    ax.invert_yaxis()
    ax.set_title(title, pad=7, fontweight="600", fontsize=FS_AB, color="#111111")
    ax.set_xlabel(xlabel, fontsize=FS_AXIS)


# --- Primary band (C) full width; supporting row (A | B) ---
fig = plt.figure(figsize=(12.4, 6.35), facecolor=BG)
gs = fig.add_gridspec(
    nrows=2,
    ncols=2,
    height_ratios=[1.72, 1.0],
    width_ratios=[1.0, 1.0],
    left=0.065,
    right=0.985,
    top=0.9,
    bottom=0.11,
    hspace=0.5,
    wspace=0.28,
)

ax_c = fig.add_subplot(gs[0, :])
ax_a = fig.add_subplot(gs[1, 0])
ax_b = fig.add_subplot(gs[1, 1])

fig.text(
    0.065,
    0.965,
    TITLE,
    ha="left",
    va="top",
    fontsize=FS_TITLE,
    fontweight="600",
    color="#111111",
)

# --- Panel C (dominant: full figure width, top) ---
style_c(ax_c)
offset = 0.19
ms_c = 105
for i in range(len(positions)):
    y1, y2 = oos_s1[i], oos_s2[i]
    ax_c.plot(
        [i - offset, i + offset],
        [y1, y2],
        color=GRAY_CONNECT,
        linewidth=1.0,
        solid_capstyle="round",
        zorder=1,
        alpha=0.98,
    )
    ax_c.scatter(
        [i - offset],
        [y1],
        s=ms_c,
        color=NAVY,
        zorder=4,
        edgecolors=NAVY,
        linewidths=1.05,
    )
    ax_c.scatter(
        [i + offset],
        [y2],
        s=ms_c,
        facecolors="white",
        edgecolors=NAVY,
        linewidths=1.3,
        zorder=4,
    )
    ax_c.annotate(
        f"{y1:.2f}",
        (i - offset, y1),
        xytext=(0, 9),
        textcoords="offset points",
        ha="center",
        fontsize=FS_VAL,
        color="#111111",
    )
    ax_c.annotate(
        f"{y2:.2f}",
        (i + offset, y2),
        xytext=(0, 9),
        textcoords="offset points",
        ha="center",
        fontsize=FS_VAL,
        color="#111111",
    )

ax_c.axhline(REF_OOS, color=RED_REF, linestyle="--", linewidth=1.08, zorder=2, alpha=0.93)
_trans_xy = blended_transform_factory(ax_c.transAxes, ax_c.transData)
ax_c.text(
    0.012,
    REF_OOS + 0.02,
    r"$R^2_{\mathrm{OOS}} = 0.15$",
    transform=_trans_xy,
    ha="left",
    va="bottom",
    fontsize=10.75,
    color=RED_REF,
)

ax_c.set_xticks(x)
ax_c.set_xticklabels(positions, fontsize=FS_TICK + 0.25)
ax_c.set_xlim(-0.62, len(positions) - 0.38)
ax_c.set_ylim(0.02, 0.72)
ax_c.set_title(
    "(C) Temporal validation (OOS $R^2$, two splits)",
    pad=11,
    fontweight="700",
    fontsize=FS_C,
    color="#111111",
)
ax_c.set_ylabel(r"Out-of-sample $R^2$", fontsize=FS_AXIS + 0.25)
ax_c.set_xlabel("Position", fontsize=FS_AXIS)

# Direct in-panel key (right-aligned; single accent tone, no legend box)
ax_c.text(
    0.985,
    0.93,
    "\u25cf  " + SPLIT_A,
    transform=ax_c.transAxes,
    ha="right",
    va="top",
    fontsize=FS_KEY,
    color=NAVY,
)
ax_c.text(
    0.985,
    0.855,
    "\u25cb  " + SPLIT_B,
    transform=ax_c.transAxes,
    ha="right",
    va="top",
    fontsize=FS_KEY,
    color=NAVY,
)

# --- Panel A: horizontal lollipop (no 0.63 line) ---
style_ab(ax_a)
lollipop_horizontal(
    ax_a,
    adj_r2,
    (0.575, 0.805),
    "Adjusted R²",
    "(A) In-sample fit (Adj. R²)",
)

# --- Panel B ---
style_ab(ax_b)
lollipop_horizontal(
    ax_b,
    rmse,
    (0.575, 0.805),
    "RMSE",
    "(B) Prediction error (RMSE, log salary)",
)

out_png = OUT_DIR / "fig_01_wage_model_fit_academic.png"
plt.savefig(out_png, bbox_inches="tight", facecolor=BG, edgecolor="none")
plt.close()

caption = (
    "Figure 1. Temporal out-of-sample performance is shown in the upper panel; the lower row reports "
    "in-sample adjusted R² and RMSE for context. Panel (A): adjusted R² exceeds 0.63 for all four models; "
    "defenders are highest and goalkeepers lowest among positions. Panel (B): RMSE is lowest for defenders "
    "and increases through goalkeepers. Panel (C): paired estimates compare two rolling train–test splits "
    "(filled markers: Train 22–24 / Test 24–25; open markers: Train 23–25 / Test 22–23), connected horizontally "
    "to show level and split-to-split gap; the horizontal line marks R²_OOS = 0.15. Forwards and goalkeepers "
    "exhibit substantially higher temporal R² than defenders and midfielders in both splits; defenders fall "
    "below 0.15 in the first split and remain weakest overall, while midfielders lie only modestly above the "
    "benchmark in both splits."
)

(OUT_DIR / "fig_01_wage_model_fit_academic_caption.txt").write_text(caption + "\n", encoding="utf-8")

print(f"Saved: {out_png}")
print(f"Caption: {OUT_DIR / 'fig_01_wage_model_fit_academic_caption.txt'}")
