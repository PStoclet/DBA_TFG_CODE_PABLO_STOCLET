"""
Figure 6 — Injury Context Robustness Analysis
No external title, no caption. Two panels: matching coverage + Jaccard stability.
"""
import pandas as pd, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT  = ROOT / "data" / "results" / "07_figures"
OUT.mkdir(parents=True, exist_ok=True)

# ── Data ──────────────────────────────────────────────────────────────────────
summary = pd.read_csv(ROOT / "data/results/08_injury_context/01_core_tables/injury_context_summary.csv")
stab    = pd.read_csv(ROOT / "data/results/08_injury_context/02_diagnostics/ranking_stability_by_tier.csv")

# Panel A values (from summary + known totals)
N_TOTAL    = 6702
matched_strict  = int(round(summary["match_rate_strict"].iloc[0] * N_TOTAL))
matched_fallback= int(round(summary["match_rate_with_fallback"].iloc[0] * N_TOTAL))
rate_strict     = summary["match_rate_strict"].iloc[0]
rate_fallback   = summary["match_rate_with_fallback"].iloc[0]
alias_lift      = summary["strict_rate_lift"].iloc[0]

panel_a = pd.DataFrame({
    "label":   ["All rows\n(baseline)", "Strict\n(Tier 1)", "Strict +\nFallback"],
    "matched": [rate_fallback, rate_strict, rate_fallback],
    "unmatched":[1-rate_fallback, 1-rate_strict, 1-rate_fallback],
    "n_matched":[matched_fallback, matched_strict, matched_fallback],
})

# Panel B — Jaccard by tier (strict_only and strict_plus_fallback rows)
row_s  = stab[stab["tier"]=="strict_only"].iloc[0]
row_sf = stab[stab["tier"]=="strict_plus_fallback"].iloc[0]
jac_data = pd.DataFrame({
    "label":   ["Top-20\nOverpaid\n(Strict)",
                "Top-20\nUnderpaid\n(Strict)",
                "Top-20\nOverpaid\n(S+FB)",
                "Top-20\nUnderpaid\n(S+FB)"],
    "jaccard": [row_s["top20_overpaid_jaccard_baseline_vs_adjusted"],
                row_s["top20_underpaid_jaccard_baseline_vs_adjusted"],
                row_sf["top20_overpaid_jaccard_baseline_vs_adjusted"],
                row_sf["top20_underpaid_jaccard_baseline_vs_adjusted"]],
})

# ── Design ────────────────────────────────────────────────────────────────────
BG         = "#FAFAFA"
GRAY_DARK  = "#2D2D2D"
GRAY_MID   = "#888888"
GRAY_GRID  = "#E8E8E8"
GREEN_M    = "#166534"   # matched
GREEN_L    = "#4ADE80"   # matched light
GRAY_UN    = "#D1D5DB"   # unmatched
ROBUST     = "#15803D"   # robust ≥0.75 — forest green
ACCEPT     = "#B45309"   # acceptable 0.65–0.75 — warm amber
BORDER     = "#9F1239"   # borderline <0.65 — deep rose
THRESH_75  = "#374151"
THRESH_65  = "#9CA3AF"

BAR_CLRS = []
for v in jac_data["jaccard"]:
    if v >= 0.75:   BAR_CLRS.append(ROBUST)
    elif v >= 0.65: BAR_CLRS.append(ACCEPT)
    else:           BAR_CLRS.append(BORDER)

fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(13, 5.5),
                                  gridspec_kw={"wspace":0.38})
fig.patch.set_facecolor(BG)

# ── Panel A: Stacked bars ─────────────────────────────────────────────────────
xs = np.arange(len(panel_a))
ax_a.bar(xs, panel_a["matched"]*100, color=GREEN_M, alpha=0.88,
         zorder=3, width=0.45, label="Injury-matched")
ax_a.bar(xs, panel_a["unmatched"]*100, bottom=panel_a["matched"]*100,
         color=GRAY_UN, alpha=0.6, zorder=3, width=0.45, label="Unmatched (zero adj.)")

for i, (r_m, n_m) in enumerate(zip(panel_a["matched"], panel_a["n_matched"])):
    ax_a.text(i, r_m*100/2, f"{r_m*100:.1f}%\n({n_m:,})",
              ha="center", va="center", fontsize=9, color="white", fontweight="bold")

# Alias lift annotation on bar 2 → bar 3
ax_a.annotate(f"Manual alias map\n+{alias_lift*100:.1f} pp lift (19 clubs)",
              xy=(2, rate_fallback*100 - 2),
              xytext=(1.0, 72),
              arrowprops=dict(arrowstyle="->", color=GRAY_DARK, lw=0.9),
              fontsize=7.5, color=GRAY_DARK, ha="center")

ax_a.set_xticks(xs)
ax_a.set_xticklabels(panel_a["label"], fontsize=9.5, color=GRAY_DARK)
ax_a.set_ylabel("Share of Observations (%)", fontsize=9, color=GRAY_DARK)
ax_a.set_ylim(0, 115)
ax_a.yaxis.set_major_locator(mticker.MultipleLocator(20))
ax_a.set_title(f"A   Injury Context Matching Coverage\n(n = {N_TOTAL:,} total observations)",
               fontsize=10, fontweight="bold", color=GRAY_DARK, loc="left", pad=8)
ax_a.legend(fontsize=8, frameon=False, loc="upper right")
ax_a.yaxis.grid(True, color=GRAY_GRID, linewidth=0.5, zorder=0)
ax_a.set_axisbelow(True)
for sp in ax_a.spines.values(): sp.set_edgecolor(GRAY_GRID)
ax_a.set_facecolor(BG)

# ── Panel B: Jaccard bars ──────────────────────────────────────────────────────
xs_b = np.arange(len(jac_data))
bars_b = ax_b.bar(xs_b, jac_data["jaccard"], color=BAR_CLRS,
                  alpha=0.88, zorder=3, width=0.5,
                  edgecolor="white", linewidth=1.2)

for bar, v in zip(bars_b, jac_data["jaccard"]):
    ax_b.text(bar.get_x() + bar.get_width()/2, v + 0.012,
              f"{v:.3f}", ha="center", va="bottom",
              fontsize=9.5, fontweight="bold", color=GRAY_DARK)

# Threshold lines
ax_b.axhline(0.75, color=THRESH_75, linewidth=1.1, linestyle="--", zorder=2, alpha=0.8)
ax_b.axhline(0.65, color=THRESH_65, linewidth=0.9, linestyle=":", zorder=2, alpha=0.8)
ax_b.text(3.3, 0.758, "0.75", ha="left", va="bottom", fontsize=7.5, color=THRESH_75)
ax_b.text(3.3, 0.658, "0.65", ha="left", va="bottom", fontsize=7.5, color=THRESH_65)

ax_b.set_xticks(xs_b)
ax_b.set_xticklabels(jac_data["label"], fontsize=8.5, color=GRAY_DARK)
ax_b.set_ylabel("Jaccard Similarity\n(Baseline vs Injury-Adjusted)", fontsize=9, color=GRAY_DARK)
ax_b.set_ylim(0, 1.0)
ax_b.yaxis.set_major_locator(mticker.MultipleLocator(0.2))
ax_b.set_title("B   Top-20 Ranking Stability After Injury Adjustment\n"
               "Jaccard = 1.0: identical sets;  < 0.65: sensitivity flag",
               fontsize=10, fontweight="bold", color=GRAY_DARK, loc="left", pad=8)

legend_b = [mpatches.Patch(color=ROBUST, alpha=0.9, label="Robust (≥ 0.75)"),
            mpatches.Patch(color=ACCEPT, alpha=0.9, label="Acceptable (0.65–0.75)"),
            mpatches.Patch(color=BORDER, alpha=0.9, label="Borderline (< 0.65)")]
ax_b.legend(handles=legend_b, fontsize=8, frameon=False, loc="upper left")
ax_b.yaxis.grid(True, color=GRAY_GRID, linewidth=0.5, zorder=0)
ax_b.set_axisbelow(True)
for sp in ax_b.spines.values(): sp.set_edgecolor(GRAY_GRID)
ax_b.set_facecolor(BG)

fig.savefig(OUT / "fig_06_injury_robustness.png",
            dpi=300, bbox_inches="tight", facecolor=BG)
print(f"Saved → {OUT / 'fig_06_injury_robustness.png'}")
