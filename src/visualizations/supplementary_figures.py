"""
generate_additional_thesis_figures.py
======================================
Figures 8-17 for the TFG thesis.

Design rule (ChartBuddy "Gray + Accent"):
  ‣ Start every chart in gray / neutral
  ‣ Color ONLY the data that carries the message
  ‣ One clear message per chart
  ‣ Max 5-6 colors per chart; red = overpaid / bad, green = underpaid / good

Run from project root:
    python Code/04_visualizations/generate_additional_thesis_figures.py
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import seaborn as sns
from pathlib import Path

# ── PATHS ────────────────────────────────────────────────────────────
ROOT      = Path(__file__).resolve().parent.parent.parent
RESULTS   = ROOT / "data" / "results"
COEF_DIR  = RESULTS / "01_model_coefficients"
EFF_DIR   = RESULTS / "02_efficiency_scores"
HYP_DIR   = RESULTS / "03_hypothesis_tests"
ROB_DIR   = RESULTS / "04_robustness"
SCOUT_DIR = RESULTS / "05_scouting_hiring"
DESC_DIR  = RESULTS / "06_descriptive_stats"
FIG_DIR   = RESULTS / "07_figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM  (same as generate_visualizations.py)
# ══════════════════════════════════════════════════════════════════════
GRAY_BG   = "#F5F5F7"
WHITE     = "#FFFFFF"
GRAY_90   = "#1D1D1F"
GRAY_60   = "#6E6E73"
GRAY_40   = "#AEAEB2"
GRAY_20   = "#D1D1D6"
GRAY_DATA = "#8E8E93"

ACCENT = {
    "Defenders":   "#0071E3",
    "Midfielders": "#30B845",
    "Forwards":    "#FF3B30",
    "Goalkeepers": "#AF52DE",
}
LEAGUE_ACCENT = {
    "Premier League": "#37003C",
    "La Liga":        "#FF4438",
    "Bundesliga":     "#E2001A",
    "Serie A":        "#1D3461",
    "Ligue 1":        "#1E6F5C",
}
COLOR_POS  = "#30B845"   # green  = underpaid / good
COLOR_NEG  = "#FF3B30"   # red    = overpaid  / bad
COLOR_NEUT = GRAY_DATA   # gray   = fair / neutral

LEAGUE_ORDER = ["Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1"]
POS_ORDER    = ["Defenders", "Midfielders", "Forwards", "Goalkeepers"]

plt.rcParams.update({
    "font.family":       "sans-serif",
    "font.sans-serif":   ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "font.size":         11,
    "axes.titlesize":    13,
    "axes.titleweight":  "bold",
    "axes.labelsize":    11,
    "axes.labelcolor":   GRAY_60,
    "xtick.labelsize":   10,
    "ytick.labelsize":   10,
    "xtick.color":       GRAY_60,
    "ytick.color":       GRAY_60,
    "legend.fontsize":   10,
    "figure.dpi":        150,
    "savefig.dpi":       300,
    "savefig.bbox":      "tight",
    "savefig.facecolor": GRAY_BG,
    "figure.facecolor":  GRAY_BG,
    "axes.facecolor":    WHITE,
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.edgecolor":    GRAY_20,
    "axes.linewidth":    0.8,
    "axes.grid":         True,
    "grid.alpha":        0.35,
    "grid.linestyle":    "-",
    "grid.linewidth":    0.4,
    "grid.color":        GRAY_20,
})
SAVE_KW = dict(facecolor=GRAY_BG, edgecolor="none")

# ── LOAD DATA ────────────────────────────────────────────────────────
ec          = pd.read_csv(EFF_DIR / "01_core_efficiency" / "efficiency_combined.csv")
coef        = pd.read_csv(COEF_DIR / "01_linear_model_coefficients" / "coef_all_models.csv")
psr_era     = pd.read_csv(HYP_DIR  / "02_psr_tests"         / "psr_era_efficiency.csv")
pos_profile = pd.read_csv(DESC_DIR / "02_position_diagnostics" / "position_efficiency_profile.csv")
temporal    = pd.read_csv(ROB_DIR  / "04_out_of_sample"     / "temporal_oos_validation.csv")
bootstrap   = pd.read_csv(ROB_DIR  / "01_bootstrap"         / "ranking_bootstrap_uncertainty_final.csv")
ec["position_group"] = ec["position_group"].replace({"Defensas": "Defenders"})
coef["model"]        = coef["model"].replace({"Defensas": "Defenders"})
print(f"Loaded efficiency_combined: {len(ec):,} rows")


# ══════════════════════════════════════════════════════════════════════
# FIG 8 — Sample composition
# Message: "Samples are comparable across leagues"
# Gray+Accent: use one sequential blue per position so all 4 are needed
# but apply sequential (light→dark) shades, not rainbow
# ══════════════════════════════════════════════════════════════════════
def fig08_sample_composition():
    print("[8] Sample composition...")
    counts = ec.groupby(["Comp", "position_group"]).size().unstack(fill_value=0)
    counts = counts.reindex(LEAGUE_ORDER)[POS_ORDER]

    # Sequential blue shades (one hue family, not rainbow)
    blues = ["#B3CDE3", "#6BAED6", "#2171B5", "#08306B"]

    fig, ax = plt.subplots(figsize=(11, 6))
    bottom = np.zeros(len(LEAGUE_ORDER))
    for i, pos in enumerate(POS_ORDER):
        vals = counts[pos].values
        ax.bar(range(len(LEAGUE_ORDER)), vals, bottom=bottom,
               label=pos, color=blues[i], edgecolor=WHITE, linewidth=0.6)
        # Label inside segment only if it's wide enough
        for j, (v, b) in enumerate(zip(vals, bottom)):
            if v > 60:
                ax.text(j, b + v / 2, str(v), ha="center", va="center",
                        fontsize=9, color=WHITE, fontweight="bold")
        bottom += vals

    # Total n on top — this IS the message
    for j, league in enumerate(LEAGUE_ORDER):
        total = counts.loc[league].sum()
        ax.text(j, total + 12, f"n = {total:,}", ha="center", va="bottom",
                fontsize=10, fontweight="bold", color=GRAY_90)

    ax.set_xticks(range(len(LEAGUE_ORDER)))
    ax.set_xticklabels(LEAGUE_ORDER, rotation=15, ha="right")
    ax.set_ylabel("Player-Season Observations")
    ax.set_ylim(0, counts.values.sum(axis=1).max() * 1.12)
    ax.set_title("Sample Composition by League and Position",
                 fontsize=15, fontweight="bold", color=GRAY_90, pad=14)
    ax.legend(title="Position", frameon=True, framealpha=0.95,
              edgecolor=GRAY_20, loc="upper right")
    plt.tight_layout()
    fig.savefig(FIG_DIR / "fig_08_sample_composition.png", **SAVE_KW)
    plt.close(fig)
    print("  ✅ fig_08")


# ══════════════════════════════════════════════════════════════════════
# FIG 9 — Model performance (Adj R², RMSE)
# Message: "All models explain ≥ 65 % of wage variance"
# Gray+Accent: bars all gray, highlight the BEST performer
# ══════════════════════════════════════════════════════════════════════
def fig09_model_performance():
    print("[9] Model performance...")
    summary_dir = COEF_DIR / "03_model_summaries"
    rows = []
    for pos in POS_ORDER:
        f = summary_dir / f"summary_{pos.lower()}.txt"
        if f.exists():
            with open(f) as fh:
                fh.readline()
                parts = fh.readline().strip().split()
                n     = int(parts[0].split("=")[1])
                adjr2 = float(parts[1].split("=")[1])
                rmse  = float(parts[2].split("=")[1])
                rows.append({"Position": pos, "n": n, "Adj_R2": adjr2, "RMSE": rmse})
    sdf = pd.DataFrame(rows)

    best_r2   = sdf["Adj_R2"].idxmax()
    best_rmse = sdf["RMSE"].idxmin()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    # Adj R² — highlight best in accent blue
    colors_r2 = [ACCENT["Defenders"] if i == best_r2 else GRAY_DATA
                 for i in range(len(sdf))]
    bars = ax1.barh(sdf["Position"], sdf["Adj_R2"],
                    color=colors_r2, edgecolor=WHITE, height=0.5)
    ax1.set_xlim(0, 1.05)
    ax1.set_xlabel("Adjusted R²")
    ax1.set_title("Explanatory Power", fontsize=13, fontweight="bold",
                  color=GRAY_90, pad=12)
    ax1.axvline(0.65, color=GRAY_40, lw=0.8, ls=":", alpha=0.7)
    ax1.text(0.655, -0.5, "65 %", fontsize=8, color=GRAY_60)
    for bar, val, n in zip(bars, sdf["Adj_R2"], sdf["n"]):
        c = WHITE if bar.get_facecolor()[:3] != (
            matplotlib.colors.to_rgb(GRAY_DATA)) else GRAY_90
        ax1.text(val - 0.015, bar.get_y() + bar.get_height() / 2,
                 f"{val:.3f}", va="center", ha="right",
                 fontsize=10, color=WHITE, fontweight="bold")
        ax1.text(val + 0.015, bar.get_y() + bar.get_height() / 2,
                 f"n = {n:,}", va="center", fontsize=9, color=GRAY_60)

    # RMSE — highlight best in accent green
    colors_rm = [ACCENT["Midfielders"] if i == best_rmse else GRAY_DATA
                 for i in range(len(sdf))]
    bars2 = ax2.barh(sdf["Position"], sdf["RMSE"],
                     color=colors_rm, edgecolor=WHITE, height=0.5)
    ax2.set_xlabel("RMSE (log-wage units)")
    ax2.set_title("Prediction Error  (lower = better)",
                  fontsize=13, fontweight="bold", color=GRAY_90, pad=12)
    for bar, val in zip(bars2, sdf["RMSE"]):
        ax2.text(val - 0.005, bar.get_y() + bar.get_height() / 2,
                 f"{val:.3f}", va="center", ha="right",
                 fontsize=10, color=WHITE, fontweight="bold")

    fig.suptitle("Position-Specific Model Performance",
                 fontsize=17, fontweight="bold", color=GRAY_90, y=1.02)
    plt.tight_layout()
    fig.savefig(FIG_DIR / "fig_09_model_performance.png", **SAVE_KW)
    plt.close(fig)
    print("  ✅ fig_09")


# ══════════════════════════════════════════════════════════════════════
# FIG 10 — Efficiency breakdown (overpaid / fair / underpaid)
# Message: "~20 % overpaid, ~20 % underpaid across all positions"
# Gray+Accent: red / gray / green is the SEMANTIC system — keep it
# ══════════════════════════════════════════════════════════════════════
def fig10_efficiency_breakdown():
    print("[10] Efficiency breakdown...")
    pf = pos_profile.set_index("position_group").reindex(POS_ORDER)

    fig, ax = plt.subplots(figsize=(10, 5))
    cats   = ["overpaid_rate", "fair_rate", "underpaid_rate"]
    labels = ["Overpaid  (ε > +0.5)", "Fairly Paid", "Underpaid  (ε < −0.5)"]
    colors = [COLOR_NEG, COLOR_NEUT, COLOR_POS]

    bottom = np.zeros(len(POS_ORDER))
    for cat, label, color in zip(cats, labels, colors):
        vals = pf[cat].values
        ax.barh(POS_ORDER, vals, left=bottom, label=label,
                color=color, edgecolor=WHITE, height=0.55)
        for i, (v, b) in enumerate(zip(vals, bottom)):
            if v > 0.06:
                ax.text(b + v / 2, i, f"{v:.0%}",
                        ha="center", va="center", fontsize=9.5,
                        color=WHITE, fontweight="bold")
        bottom += vals

    ax.set_xlim(0, 1)
    ax.set_xlabel("Proportion of Players")
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax.set_title("Wage Classification by Position",
                 fontsize=15, fontweight="bold", color=GRAY_90, pad=14)
    ax.legend(frameon=True, framealpha=0.95, edgecolor=GRAY_20,
              loc="lower right", fontsize=10)
    plt.tight_layout()
    fig.savefig(FIG_DIR / "fig_10_efficiency_breakdown.png", **SAVE_KW)
    plt.close(fig)
    print("  ✅ fig_10")


# ══════════════════════════════════════════════════════════════════════
# FIG 11 — Temporal stability
# Message: "Efficiency is stable across seasons"
# Gray+Accent: all league lines in gray EXCEPT the most volatile one
# ══════════════════════════════════════════════════════════════════════
def fig11_temporal_stability():
    print("[11] Temporal stability...")
    fig, ax = plt.subplots(figsize=(10, 6))
    seasons = ["2022-2023", "2023-2024", "2024-2025"]

    # Compute range per league to identify most / least volatile
    ranges = {}
    for league in LEAGUE_ORDER:
        ldf = psr_era[psr_era["Comp"] == league].copy()
        ldf["Season"] = pd.Categorical(ldf["Season"], categories=seasons, ordered=True)
        ldf = ldf.sort_values("Season")
        if len(ldf) == 3:
            ranges[league] = ldf["mean_efficiency"].max() - ldf["mean_efficiency"].min()

    if ranges:
        most_volatile = max(ranges, key=ranges.get)
    else:
        most_volatile = None

    for league in LEAGUE_ORDER:
        ldf = psr_era[psr_era["Comp"] == league].copy()
        ldf["Season"] = pd.Categorical(ldf["Season"], categories=seasons, ordered=True)
        ldf = ldf.sort_values("Season")
        is_volatile = (league == most_volatile)
        color = LEAGUE_ACCENT[league] if is_volatile else GRAY_40
        lw    = 2.8 if is_volatile else 1.4
        alpha = 0.95 if is_volatile else 0.60
        zorder = 5 if is_volatile else 2
        ax.plot(ldf["Season"], ldf["mean_efficiency"], "o-",
                color=color, lw=lw, markersize=8 if is_volatile else 6,
                alpha=alpha, zorder=zorder, label=league,
                markeredgecolor=WHITE, markeredgewidth=0.8)
        ax.fill_between(ldf["Season"],
                        ldf["mean_efficiency"] - ldf["std_efficiency"] / 2,
                        ldf["mean_efficiency"] + ldf["std_efficiency"] / 2,
                        color=color, alpha=0.08)

    ax.axhline(0, color=GRAY_90, ls="-", lw=0.7, alpha=0.22)
    ax.set_ylabel("Mean Efficiency Score")
    ax.set_xlabel("Season")
    ax.set_title("League Efficiency Stability Across Seasons",
                 fontsize=15, fontweight="bold", color=GRAY_90, pad=14)
    ax.text(0.5, 1.01,
            "Gray = stable leagues  |  Colored = most variable league  |  Bands = ±0.5 σ",
            transform=ax.transAxes, ha="center", fontsize=9.5,
            color=GRAY_60, style="italic")
    ax.legend(frameon=True, framealpha=0.95, edgecolor=GRAY_20,
              loc="upper right", fontsize=9)
    plt.tight_layout()
    fig.savefig(FIG_DIR / "fig_11_temporal_league_efficiency.png", **SAVE_KW)
    plt.close(fig)
    print("  ✅ fig_11")


# ══════════════════════════════════════════════════════════════════════
# FIG 12 — Out-of-sample validation
# Message: "Models generalise well (OOS R² close to in-sample)"
# Gray+Accent: all bars gray, highlight positions that drop most OOS
# ══════════════════════════════════════════════════════════════════════
def fig12_oos_validation():
    print("[12] OOS validation...")
    splits = temporal["split"].unique()[:2]
    fig, axes = plt.subplots(1, len(splits), figsize=(13, 5), sharey=True)

    for ax, split_name in zip(np.ravel(axes), splits):
        sub = (temporal[temporal["split"] == split_name]
               .set_index("position_group")
               .reindex(POS_ORDER)
               .reset_index())
        worst = sub["r2_oos"].idxmin()
        colors = [ACCENT["Forwards"] if i == worst else GRAY_DATA
                  for i in range(len(sub))]
        bars = ax.barh(sub["position_group"], sub["r2_oos"],
                       color=colors, edgecolor=WHITE, height=0.5)
        for bar, val, rmse in zip(bars, sub["r2_oos"], sub["rmse_oos"]):
            ax.text(val - 0.008, bar.get_y() + bar.get_height() / 2,
                    f"{val:.3f}", va="center", ha="right",
                    fontsize=10, color=WHITE, fontweight="bold")
            ax.text(val + 0.008, bar.get_y() + bar.get_height() / 2,
                    f"RMSE {rmse:.3f}", va="center",
                    fontsize=8.5, color=GRAY_60)
        ax.set_xlim(0, 0.85)
        ax.set_xlabel("Out-of-Sample R²")
        clean = (split_name
                 .replace("train_", "Train ")
                 .replace("__test_", " → Test ")
                 .replace("_", "/"))
        ax.set_title(clean, fontsize=11, fontweight="bold", color=GRAY_90, pad=10)

    fig.suptitle("Temporal Out-of-Sample Validation",
                 fontsize=17, fontweight="bold", color=GRAY_90, y=1.04)
    fig.text(0.5, 0.995, "Train on 2 seasons → predict the 3rd",
             ha="center", fontsize=10, color=GRAY_60, style="italic")
    plt.tight_layout()
    fig.savefig(FIG_DIR / "fig_12_oos_validation.png", **SAVE_KW)
    plt.close(fig)
    print("  ✅ fig_12")


# ══════════════════════════════════════════════════════════════════════
# FIG 13 — Wage rigidity by budget tier
# Message: "Elite clubs freeze wages MORE than mid-tier clubs"
# Gray+Accent: green (low tier) → gray (mid) → red (high), semantic
# ══════════════════════════════════════════════════════════════════════
def fig13_wage_rigidity():
    print("[13] Wage rigidity...")
    rig = pd.read_csv(DESC_DIR / "01_wage_descriptives" / "wage_rigidity_by_budget.csv")
    # Sort by frozen_rate so highest is leftmost (typical bar convention)
    rig = rig.sort_values("frozen_rate", ascending=False).reset_index(drop=True)

    # Semantic: HIGH frozen rate = BAD = RED, LOW = GOOD = GREEN
    # Assign color per bar based on its actual value, not tier position
    max_rate = rig["frozen_rate"].max()
    min_rate = rig["frozen_rate"].min()
    def rate_color(r):
        if r == max_rate:
            return COLOR_NEG    # red = most rigid
        elif r == min_rate:
            return COLOR_POS    # green = least rigid
        else:
            return COLOR_NEUT   # gray = middle
    tier_colors = [rate_color(r) for r in rig["frozen_rate"]]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(range(len(rig)), rig["frozen_rate"] * 100,
                  color=tier_colors, edgecolor=WHITE, width=0.5)
    ax.set_xticks(range(len(rig)))
    ax.set_xticklabels(rig["bill_tier"], fontsize=11)

    for bar, val, tot in zip(bars, rig["frozen_rate"] * 100, rig["n_transitions"]):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 1.2,
                f"{val:.1f} %", ha="center", fontsize=12,
                fontweight="bold", color=GRAY_90)
        ax.text(bar.get_x() + bar.get_width() / 2, val / 2,
                f"n = {tot:,}", ha="center", va="center",
                fontsize=9, color=WHITE, fontweight="bold")

    ax.set_ylabel("% Players with Frozen Wages Season-to-Season")
    ax.set_ylim(0, rig["frozen_rate"].max() * 100 * 1.22)
    ax.set_title("Wage Rigidity by Club Budget Tier",
                 fontsize=15, fontweight="bold", color=GRAY_90, pad=14)
    ax.text(0.5, 1.01,
            "Red = most rigid  ·  Green = least rigid",
            transform=ax.transAxes, ha="center",
            fontsize=9.5, color=GRAY_60, style="italic")
    plt.tight_layout()
    fig.savefig(FIG_DIR / "fig_13_wage_rigidity.png", **SAVE_KW)
    plt.close(fig)
    print("  ✅ fig_13")


# ══════════════════════════════════════════════════════════════════════
# FIG 14 — Bootstrap ranking uncertainty (top underpaid)
# Message: "These players are robustly underpaid"
# Gray+Accent: bars gray (CI), green diamond = mean rank
# ══════════════════════════════════════════════════════════════════════
def fig14_bootstrap_rankings():
    print("[14] Bootstrap rankings...")
    bund = bootstrap[bootstrap["side"] == "Underpaid"].head(15).copy()
    bund = bund.sort_values("mean_rank").reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(12, 9))
    # Reserve top margin so suptitle + subtitle don't clash with axes
    fig.subplots_adjust(top=0.88)

    for i, row in bund.iterrows():
        ax.barh(i, row["p90_rank"] - row["p10_rank"],
                left=row["p10_rank"], height=0.55,
                color=GRAY_20, edgecolor=GRAY_40, linewidth=0.6)
        ax.plot(row["mean_rank"], i, "D",
                color=COLOR_POS, markersize=10,
                markeredgecolor=WHITE, markeredgewidth=1.2, zorder=5)

    labels = [f"{r['Player']}  —  {r['Team']}  ({r['Season'][:4]})"
              for _, r in bund.iterrows()]
    ax.set_yticks(range(len(bund)))
    ax.set_yticklabels(labels, fontsize=9.5)
    ax.invert_yaxis()
    ax.set_xlabel("Bootstrap Rank  (1 = most underpaid)")

    # Title via suptitle — controls top padding precisely
    fig.suptitle("Top 15 Most Underpaid Players",
                 fontsize=16, fontweight="bold", color=GRAY_90, y=0.97)
    fig.text(0.5, 0.91,
             "P10–P90 bootstrap uncertainty interval  ·  ◆ = mean rank  ·  2 000 iterations",
             ha="center", fontsize=9.5, color=GRAY_60, style="italic")

    legend_el = [
        mpatches.Patch(color=GRAY_20, ec=GRAY_40, label="P10 – P90 range"),
        Line2D([0], [0], marker="D", color="none", markerfacecolor=COLOR_POS,
               markeredgecolor=WHITE, markersize=9, label="Mean rank"),
    ]
    ax.legend(handles=legend_el, frameon=True, framealpha=0.95,
              edgecolor=GRAY_20, loc="lower right")
    fig.savefig(FIG_DIR / "fig_14_bootstrap_rankings.png", **SAVE_KW)
    plt.close(fig)
    print("  ✅ fig_14")


# ══════════════════════════════════════════════════════════════════════
# FIG 15 — Squad restructuring potential
# Message: "Top clubs could save €X M by replacing overpaid players"
# Gray+Accent: all bars same blue (one category), annotate savings
# ══════════════════════════════════════════════════════════════════════
def fig15_squad_restructuring():
    print("[15] Squad restructuring...")
    sq = pd.read_csv(
        SCOUT_DIR / "02_squad_restructuring" / "squad_restructuring_summary.csv")
    sq = sq.nlargest(10, "net_saving_4yr_EUR").sort_values("net_saving_4yr_EUR")

    fig, ax = plt.subplots(figsize=(11, 7))
    y_labels = sq["club"] + "  (" + sq["league"].str[:3] + ")"
    bars = ax.barh(y_labels, sq["net_saving_4yr_EUR"] / 1e6,
                   color=ACCENT["Defenders"], edgecolor=WHITE, height=0.6)

    xmax = (sq["net_saving_4yr_EUR"] / 1e6).max()
    for bar, val, pct in zip(bars, sq["net_saving_4yr_EUR"] / 1e6,
                              sq["bill_reduction_pct"]):
        ax.text(val - xmax * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"€{val:.0f} M", va="center", ha="right",
                fontsize=9.5, color=WHITE, fontweight="bold")
        ax.text(val + xmax * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"−{pct:.0f} % wage bill", va="center",
                fontsize=9, color=GRAY_60)

    ax.set_xlabel("Projected 4-Year Net Wage Savings (€ Millions)")
    ax.set_title("Squad Restructuring Potential — Top 10 Clubs",
                 fontsize=15, fontweight="bold", color=GRAY_90, pad=14)
    ax.text(0.5, 1.01, "Efficiency-based replacement strategy",
            transform=ax.transAxes, ha="center",
            fontsize=9.5, color=GRAY_60, style="italic")
    plt.tight_layout()
    fig.savefig(FIG_DIR / "fig_15_squad_restructuring.png", **SAVE_KW)
    plt.close(fig)
    print("  ✅ fig_15")


# ══════════════════════════════════════════════════════════════════════
# FIG 16 — NEW: Wage-Age Profile (predicted)
# Message: "Every position has a wage peak; it differs by role"
# Uses OLS Age / Age² coefficients to draw the predicted curve
# Gray+Accent: all curves gray, highlight the position with earliest peak
# ══════════════════════════════════════════════════════════════════════
def fig16_wage_age_profile():
    print("[16] Wage-Age profile (NEW)...")

    # Extract Age and Age² coefficients + intercept for each position
    fig, ax = plt.subplots(figsize=(11, 6))

    age_range = np.linspace(17, 38, 300)
    peak_ages = {}

    for pos in POS_ORDER:
        pc = coef[coef["model"] == pos].set_index("variable")
        if "Age" not in pc.index or "Age2" not in pc.index:
            continue
        b_age  = pc.loc["Age",  "coef"]
        b_age2 = pc.loc["Age2", "coef"]
        # Peak age from derivative: d/dAge = b_age + 2*b_age2*Age = 0
        peak = -b_age / (2 * b_age2)
        peak_ages[pos] = peak
        predicted = b_age * age_range + b_age2 * age_range ** 2
        predicted -= predicted.min()          # normalise to start at 0
        ax.plot(age_range, predicted, color=GRAY_40, lw=2.0, alpha=0.5)

    # Highlight position with earliest peak in accent
    if peak_ages:
        earliest_pos = min(peak_ages, key=peak_ages.get)
        pc = coef[coef["model"] == earliest_pos].set_index("variable")
        b_age  = pc.loc["Age",  "coef"]
        b_age2 = pc.loc["Age2", "coef"]
        predicted = b_age * age_range + b_age2 * age_range ** 2
        predicted -= predicted.min()
        ax.plot(age_range, predicted, color=ACCENT[earliest_pos],
                lw=3.0, label=f"{earliest_pos} (earliest peak)")

    # Annotate peak age lines
    for pos, peak in peak_ages.items():
        pc = coef[coef["model"] == pos].set_index("variable")
        b_age  = pc.loc["Age",  "coef"]
        b_age2 = pc.loc["Age2", "coef"]
        predicted = b_age * age_range + b_age2 * age_range ** 2
        predicted -= predicted.min()
        peak_val = b_age * peak + b_age2 * peak ** 2
        peak_val -= (b_age * age_range + b_age2 * age_range ** 2).min()
        color = ACCENT[pos] if pos == earliest_pos else GRAY_60
        ax.axvline(peak, color=color, lw=0.8, ls="--", alpha=0.55)
        ax.text(peak + 0.15, peak_val * 0.95,
                f"{pos[:3]}.\npeak {peak:.1f}",
                fontsize=8, color=color, va="top")

    ax.set_xlabel("Age (years)")
    ax.set_ylabel("Predicted log-wage premium  (relative units)")
    ax.set_title("Predicted Wage-Age Profile by Position",
                 fontsize=15, fontweight="bold", color=GRAY_90, pad=14)
    ax.text(0.5, 1.01,
            "Derived from OLS Age + Age² coefficients  ·  Colored = earliest-peaking position",
            transform=ax.transAxes, ha="center",
            fontsize=9.5, color=GRAY_60, style="italic")

    # Manual legend for all positions
    handles = [Line2D([0], [0], color=ACCENT[pos] if pos == earliest_pos else GRAY_40,
                      lw=2.5 if pos == earliest_pos else 1.8, label=pos)
               for pos in peak_ages]
    ax.legend(handles=handles, frameon=True, framealpha=0.95,
              edgecolor=GRAY_20, loc="upper right")
    plt.tight_layout()
    fig.savefig(FIG_DIR / "fig_16_wage_age_profile.png", **SAVE_KW)
    plt.close(fig)
    print("  ✅ fig_16  (NEW)")


# ══════════════════════════════════════════════════════════════════════
# FIG 17 — NEW: Diverging dot plot — top over/underpaid players
# Message: "These are the most misallocated wages in European football"
# Gray+Accent: green = underpaid, red = overpaid, gray = zero line
# ══════════════════════════════════════════════════════════════════════
def fig17_top_mispaid_diverging():
    print("[17] Top over/underpaid diverging plot (NEW)...")

    latest = (ec.sort_values("Season", ascending=False)
                .drop_duplicates(subset="Player", keep="first"))
    underpaid = (latest.nsmallest(12, "efficiency_score")
                 [["Player", "Team", "efficiency_score"]]
                 .sort_values("efficiency_score")        # most negative at top
                 .reset_index(drop=True))
    overpaid  = (latest.nlargest(12, "efficiency_score")
                 [["Player", "Team", "efficiency_score"]]
                 .sort_values("efficiency_score", ascending=False)
                 .reset_index(drop=True))

    # Use a single-axis mirrored design: underpaid left of 0, overpaid right
    fig, ax = plt.subplots(figsize=(14, 9))
    fig.subplots_adjust(top=0.88, left=0.02, right=0.98)

    n = max(len(underpaid), len(overpaid))
    y_under = np.arange(len(underpaid))
    y_over  = np.arange(len(overpaid))

    # Underpaid bars (green, extend LEFT from 0)
    ax.barh(y_under, underpaid["efficiency_score"],
            color=COLOR_POS, alpha=0.30, height=0.55,
            edgecolor=COLOR_POS, linewidth=0.5)
    ax.scatter(underpaid["efficiency_score"], y_under,
               color=COLOR_POS, s=70, zorder=5, edgecolors=WHITE, linewidths=1.0)

    # Underpaid labels — RIGHT-aligned inside the bar from the center
    for i, row in underpaid.iterrows():
        label = f"{row['Player']}  ({row['Team']})"
        ax.text(-0.05, i, label, ha="right", va="center",
                fontsize=8.5, color=GRAY_90)

    # Overpaid bars (red, extend RIGHT from 0) — place on same y axis but right side
    # Shift overpaid y positions by adding offset so they interleave cleanly
    ax.barh(y_over, overpaid["efficiency_score"],
            color=COLOR_NEG, alpha=0.30, height=0.55,
            edgecolor=COLOR_NEG, linewidth=0.5)
    ax.scatter(overpaid["efficiency_score"], y_over,
               color=COLOR_NEG, s=70, zorder=5, edgecolors=WHITE, linewidths=1.0)

    # Overpaid labels — LEFT-aligned inside the bar from the center
    for i, row in overpaid.iterrows():
        label = f"({row['Team']})  {row['Player']}"
        ax.text(0.05, i, label, ha="left", va="center",
                fontsize=8.5, color=GRAY_90)

    ax.axvline(0, color=GRAY_90, lw=1.2, alpha=0.35)
    ax.set_yticks([])
    ax.set_xlabel("Efficiency Score  (negative = underpaid, positive = overpaid)")

    # Section labels
    xmin = underpaid["efficiency_score"].min() * 1.05
    xmax = overpaid["efficiency_score"].max()  * 1.05
    ax.set_xlim(xmin, xmax)
    ax.text(xmin * 0.5, n - 0.5, "MOST UNDERPAID",
            ha="center", fontsize=12, fontweight="bold",
            color=COLOR_POS, alpha=0.7)
    ax.text(xmax * 0.5, n - 0.5, "MOST OVERPAID",
            ha="center", fontsize=12, fontweight="bold",
            color=COLOR_NEG, alpha=0.7)

    fig.suptitle("Largest Wage Misalignments in European Football",
                 fontsize=17, fontweight="bold", color=GRAY_90, y=0.97)
    fig.text(0.5, 0.91,
             "Most recent season per player  ·  Efficiency score = residual from OLS wage model",
             ha="center", fontsize=9.5, color=GRAY_60, style="italic")
    fig.savefig(FIG_DIR / "fig_17_top_mispaid_diverging.png", **SAVE_KW)
    plt.close(fig)
    print("  ✅ fig_17  (NEW)")


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 65)
    print("  ADDITIONAL THESIS FIGURES  (Gray + Accent, ChartBuddy)")
    print("=" * 65)

    fig08_sample_composition()
    fig09_model_performance()
    fig10_efficiency_breakdown()
    fig11_temporal_stability()
    fig12_oos_validation()
    fig13_wage_rigidity()
    fig14_bootstrap_rankings()
    fig15_squad_restructuring()
    fig16_wage_age_profile()
    fig17_top_mispaid_diverging()

    print("\n" + "=" * 65)
    print(f"  ✅ ALL FIGURES → {FIG_DIR}")
    print("=" * 65)
    for f in sorted(FIG_DIR.glob("fig_*.png")):
        flag = "  ← NEW" if f.name in (
            "fig_16_wage_age_profile.png",
            "fig_17_top_mispaid_diverging.png") else ""
        print(f"  {f.name:50s} {f.stat().st_size/1024:7.1f} KB{flag}")
