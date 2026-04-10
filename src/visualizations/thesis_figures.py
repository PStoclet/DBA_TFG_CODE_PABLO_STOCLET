"""
Thesis Figures Generator — Salary Efficiency in European Football
Gray+Accent design principle: everything gray by default, color only on the message.
All figures at 300 dpi, no overlapping text, tight_layout enforced.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings("ignore")

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
AR = ROOT / "data" / "results"
FIG = AR / "07_figures"
FIG.mkdir(parents=True, exist_ok=True)

# ── Color palette (Gray+Accent) ───────────────────────────────────────────────
GRAY     = "#BDBDBD"
GRAY_MID = "#757575"
GRAY_DARK= "#424242"
ACCENT   = "#1565C0"    # deep blue — primary message
RED      = "#C62828"    # overpaid / bad
GREEN    = "#2E7D32"    # underpaid / good
GOLD     = "#F9A825"    # secondary accent
BG       = "#FAFAFA"
GRID_CLR = "#E0E0E0"

POSITION_COLORS = {
    "Defenders":  "#1565C0",
    "Midfielders":"#6A1B9A",
    "Forwards":   "#B71C1C",
    "Goalkeepers":"#E65100",
}

def style_ax(ax, title=None, xlabel=None, ylabel=None, grid="y"):
    ax.set_facecolor(BG)
    ax.tick_params(colors=GRAY_DARK, labelsize=9)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID_CLR)
    if grid == "y":
        ax.yaxis.grid(True, color=GRID_CLR, linewidth=0.6, zorder=0)
        ax.set_axisbelow(True)
    elif grid == "x":
        ax.xaxis.grid(True, color=GRID_CLR, linewidth=0.6, zorder=0)
        ax.set_axisbelow(True)
    elif grid == "both":
        ax.grid(True, color=GRID_CLR, linewidth=0.6, zorder=0)
        ax.set_axisbelow(True)
    if title:
        ax.set_title(title, fontsize=11, fontweight="bold", color=GRAY_DARK, pad=8)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=9, color=GRAY_MID)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9, color=GRAY_MID)

def save(name):
    plt.savefig(FIG / name, dpi=300, bbox_inches="tight", facecolor=BG)
    plt.close("all")
    print(f"  Saved {name}")

# ── Load data ─────────────────────────────────────────────────────────────────
eff   = pd.read_csv(AR / "02_efficiency_scores/01_core_efficiency/efficiency_combined.csv")
eff["position_group"] = eff["position_group"].replace({"Defensas": "Defenders"})

coef  = pd.read_csv(AR / "01_model_coefficients/01_linear_model_coefficients/coef_all_models.csv")
coef_q= pd.read_csv(AR / "01_model_coefficients/02_quantile_coefficients/coef_quantile_all_models.csv")
h1    = pd.read_csv(AR / "03_hypothesis_tests/01_core_hypotheses/hypothesis_H1.csv")
oos   = pd.read_csv(AR / "04_robustness/04_out_of_sample/temporal_oos_validation.csv")
boot  = pd.read_csv(AR / "04_robustness/01_bootstrap/ranking_bootstrap_uncertainty_final.csv")
lasso = pd.read_csv(AR / "04_robustness/05_regularization/lasso_variable_selection.csv")
nat   = pd.read_csv(AR / "06_descriptive_stats/03_nationality/nationality_efficiency_map.csv")
tail  = pd.read_csv(AR / "06_descriptive_stats/02_position_diagnostics/position_tail_pressure.csv")
scouting = pd.read_csv(AR / "05_scouting_hiring/03_scouting_scores/scouting_value_scores.csv")
tiq   = pd.read_csv(AR / "05_scouting_hiring/04_transfer_intelligence/transfer_intelligence_summary.csv")
restruct = pd.read_csv(AR / "05_scouting_hiring/02_squad_restructuring/squad_restructuring_summary.csv")
rigidity = pd.read_csv(AR / "06_descriptive_stats/01_wage_descriptives/desc_wage_rigidity.csv")
psr_era  = pd.read_csv(AR / "03_hypothesis_tests/02_psr_tests/psr_era_efficiency.csv")

print("All data loaded.")

# ══════════════════════════════════════════════════════════════════════════════
# FIG 01 ── Forest plot of OLS coefficients (all 4 models)
# ══════════════════════════════════════════════════════════════════════════════
print("Fig 01 – Forest plot")
positions = ["Defenders", "Midfielders", "Forwards", "Goalkeepers"]
fig, axes = plt.subplots(1, 4, figsize=(16, 6), sharey=False)
fig.patch.set_facecolor(BG)

for ax, pos in zip(axes, positions):
    d = coef[coef["model"] == pos].copy()
    d = d[~d["variable"].isin(["Intercept"])].copy()
    d = d.sort_values("coef")
    colors = [ACCENT if p < 0.05 else GRAY for p in d["pvalue"]]
    y = range(len(d))
    ax.barh(y, d["coef"], color=colors, height=0.6, zorder=3)
    if "ci_lo" in d.columns and "ci_hi" in d.columns:
        ax.errorbar(d["coef"], y,
                    xerr=[d["coef"] - d["ci_lo"], d["ci_hi"] - d["coef"]],
                    fmt="none", color=GRAY_DARK, linewidth=0.8, capsize=2, zorder=4)
    ax.axvline(0, color=GRAY_DARK, linewidth=0.8, linestyle="--")
    ax.set_yticks(list(y))
    ax.set_yticklabels(d["variable"], fontsize=7.5)
    style_ax(ax, title=pos, xlabel="Coefficient", grid="x")

sig_patch = mpatches.Patch(color=ACCENT, label="p < 0.05")
ns_patch  = mpatches.Patch(color=GRAY,   label="p ≥ 0.05")
fig.legend(handles=[sig_patch, ns_patch], loc="lower center", ncol=2,
           frameon=False, fontsize=9)
fig.suptitle("OLS Coefficient Estimates with 95% CI (HC3 Robust SE)", fontsize=13,
             fontweight="bold", color=GRAY_DARK, y=1.01)
plt.tight_layout(w_pad=3)
save("fig_01_forest_plot_coefficients.png")

# ══════════════════════════════════════════════════════════════════════════════
# FIG 02 ── Fitted vs Actual log-wages scatter
# ══════════════════════════════════════════════════════════════════════════════
print("Fig 02 – Fitted vs Actual")
d = eff.dropna(subset=["fitted_log_wage","log_wage","efficiency_label"]).copy()
fig, ax = plt.subplots(figsize=(7, 6))
fig.patch.set_facecolor(BG)
label_map = {"Underpaid": GREEN, "Fair": GRAY, "Overpaid": RED}
for lbl, clr in label_map.items():
    sub = d[d["efficiency_label"] == lbl]
    ax.scatter(sub["fitted_log_wage"], sub["log_wage"], c=clr,
               s=10, alpha=0.5, linewidths=0, label=lbl, zorder=3)
lims = [min(d["fitted_log_wage"].min(), d["log_wage"].min()) - 0.2,
        max(d["fitted_log_wage"].max(), d["log_wage"].max()) + 0.2]
ax.plot(lims, lims, color=GRAY_DARK, linewidth=1, linestyle="--", label="45° line")
ax.set_xlim(lims); ax.set_ylim(lims)
style_ax(ax, title="Fitted vs Actual Log-Wages",
         xlabel="Fitted log-wage (model prediction)",
         ylabel="Actual log-wage (observed)", grid="both")
ax.legend(fontsize=9, frameon=False)
n = len(d)
ax.text(0.02, 0.97, f"n = {n:,}", transform=ax.transAxes,
        fontsize=8, color=GRAY_MID, va="top")
plt.tight_layout()
save("fig_02_fitted_vs_actual.png")

# ══════════════════════════════════════════════════════════════════════════════
# FIG 03 ── Efficiency score distribution by league (boxplot + strip)
# ══════════════════════════════════════════════════════════════════════════════
print("Fig 03 – Efficiency by league")
league_order = ["Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1"]
d = eff[eff["Comp"].isin(league_order)].copy()
fig, ax = plt.subplots(figsize=(10, 5))
fig.patch.set_facecolor(BG)
positions_list = [d[d["Comp"] == lg]["efficiency_score"].dropna().values for lg in league_order]
bp = ax.boxplot(positions_list, patch_artist=True, medianprops=dict(color=ACCENT, linewidth=2),
                whiskerprops=dict(color=GRAY_MID), capprops=dict(color=GRAY_MID),
                flierprops=dict(marker=".", color=GRAY, markersize=3, alpha=0.4),
                widths=0.4, zorder=3)
for patch in bp["boxes"]:
    patch.set_facecolor(BG)
    patch.set_edgecolor(GRAY_MID)

medians = [d[d["Comp"] == lg]["efficiency_score"].median() for lg in league_order]
most_ineff = np.argmax(medians)
bp["boxes"][most_ineff].set_edgecolor(RED)
bp["medians"][most_ineff].set_color(RED)

ax.axhline(0, color=GRAY_DARK, linewidth=0.8, linestyle="--")
ax.set_xticks(range(1, len(league_order)+1))
ax.set_xticklabels(league_order, fontsize=9)
style_ax(ax, title="Wage Efficiency Score Distribution by League",
         ylabel="Efficiency Score (residual from log-wage model)", grid="y")
ax.text(0.01, 0.97, "Positive = overpaid | Negative = underpaid",
        transform=ax.transAxes, fontsize=8, color=GRAY_MID, va="top")
plt.tight_layout()
save("fig_03_ridge_efficiency_by_league.png")

# ══════════════════════════════════════════════════════════════════════════════
# FIG 04 ── PSR persistence: mean efficiency trend per league/season
# ══════════════════════════════════════════════════════════════════════════════
print("Fig 04 – PSR spaghetti")
d = psr_era.copy()
league_order = ["Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1"]
d = d[d["Comp"].isin(league_order)]
fig, ax = plt.subplots(figsize=(9, 5))
fig.patch.set_facecolor(BG)
palette = {"Premier League":"#1565C0","La Liga":"#C62828","Bundesliga":"#F9A825",
           "Serie A":"#2E7D32","Ligue 1":"#6A1B9A"}
for lg in league_order:
    sub = d[d["Comp"] == lg].sort_values("Season")
    ax.plot(sub["Season"], sub["mean_efficiency"], color=palette[lg],
            linewidth=2.2, marker="o", markersize=5, label=lg)
ax.axhline(0, color=GRAY_DARK, linewidth=0.8, linestyle="--", alpha=0.6)
style_ax(ax, title="Mean Wage-Efficiency Score per League and Season",
         xlabel="Season", ylabel="Mean Efficiency Score", grid="y")
ax.legend(fontsize=9, frameon=False, loc="upper right")
ax.tick_params(axis="x", labelsize=9)
ax.text(0.01, 0.03, "Persistent positive mean → systematic overpayment pattern",
        transform=ax.transAxes, fontsize=7.5, color=GRAY_MID)
plt.tight_layout()
save("fig_04_psr_persistence_spaghetti.png")

# ══════════════════════════════════════════════════════════════════════════════
# FIG 05 ── Residual diagnostics (4-panel)
# ══════════════════════════════════════════════════════════════════════════════
print("Fig 05 – Residual diagnostics")
d = eff.dropna(subset=["efficiency_score","fitted_log_wage","position_group","Annual_Wages_EUR"]).copy()
fig = plt.figure(figsize=(13, 10))
fig.patch.set_facecolor(BG)
gs = GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.35)

# 5a – residuals vs fitted
ax1 = fig.add_subplot(gs[0, 0])
ax1.scatter(d["fitted_log_wage"], d["efficiency_score"], color=GRAY, s=6, alpha=0.4, zorder=2)
ax1.axhline(0, color=ACCENT, linewidth=1.2, linestyle="--")
style_ax(ax1, title="Residuals vs Fitted", xlabel="Fitted log-wage", ylabel="Residual")

# 5b – histogram of residuals
ax2 = fig.add_subplot(gs[0, 1])
ax2.hist(d["efficiency_score"], bins=60, color=GRAY, edgecolor=BG, linewidth=0.3, zorder=2)
ax2.axvline(0, color=ACCENT, linewidth=1.2, linestyle="--")
mu = d["efficiency_score"].mean(); s = d["efficiency_score"].std()
ax2.axvline(mu, color=RED, linewidth=1, linestyle=":")
style_ax(ax2, title="Distribution of Efficiency Scores",
         xlabel="Efficiency Score", ylabel="Count")
ax2.text(0.97, 0.95, f"μ={mu:.3f}\nσ={s:.3f}", transform=ax2.transAxes,
         ha="right", va="top", fontsize=8, color=GRAY_DARK)

# 5c – efficiency by position (violin)
ax3 = fig.add_subplot(gs[1, 0])
pos_list = ["Defenders","Midfielders","Forwards","Goalkeepers"]
data_pos = [d[d["position_group"]==p]["efficiency_score"].dropna().values for p in pos_list]
vp = ax3.violinplot(data_pos, showmedians=True)
for i, (body, pos) in enumerate(zip(vp["bodies"], pos_list)):
    body.set_facecolor(POSITION_COLORS[pos])
    body.set_alpha(0.55)
vp["cmedians"].set_color(GRAY_DARK)
vp["cmaxes"].set_color(GRAY); vp["cmins"].set_color(GRAY)
vp["cbars"].set_color(GRAY)
ax3.axhline(0, color=GRAY_DARK, linewidth=0.8, linestyle="--")
ax3.set_xticks([1,2,3,4])
ax3.set_xticklabels(["Def","Mid","Fwd","GK"], fontsize=9)
style_ax(ax3, title="Efficiency Scores by Position", ylabel="Efficiency Score")

# 5d – Q-Q plot
from scipy import stats as sp_stats
ax4 = fig.add_subplot(gs[1, 1])
qq = sp_stats.probplot(d["efficiency_score"].values, dist="norm")
ax4.plot(qq[0][0], qq[0][1], ".", color=GRAY, markersize=3, alpha=0.5, zorder=2)
ax4.plot(qq[0][0], qq[1][0]*qq[0][0]+qq[1][1], color=ACCENT, linewidth=1.5, zorder=3)
style_ax(ax4, title="Q-Q Plot of Residuals",
         xlabel="Theoretical Quantiles", ylabel="Sample Quantiles")

fig.suptitle("Model Residual Diagnostics", fontsize=13, fontweight="bold",
             color=GRAY_DARK, y=1.01)
save("fig_05_residual_diagnostics.png")

# ══════════════════════════════════════════════════════════════════════════════
# FIG 06 ── Coefficient heatmap (significance across models)
# ══════════════════════════════════════════════════════════════════════════════
print("Fig 06 – Coefficient heatmap")
import matplotlib.colors as mcolors

pivot = coef.pivot_table(index="variable", columns="model", values="coef", aggfunc="first")
piv_p = coef.pivot_table(index="variable", columns="model", values="pvalue", aggfunc="first")
pivot = pivot.reindex(columns=["Defenders","Midfielders","Forwards","Goalkeepers"])
piv_p = piv_p.reindex(columns=["Defenders","Midfielders","Forwards","Goalkeepers"])

# Remove intercept
pivot = pivot.drop(index=["Intercept"], errors="ignore")
piv_p = piv_p.drop(index=["Intercept"], errors="ignore")

fig, ax = plt.subplots(figsize=(8, max(5, len(pivot)*0.45)))
fig.patch.set_facecolor(BG)
vmax = np.nanpercentile(np.abs(pivot.values), 95)
norm = mcolors.TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
cmap = plt.cm.RdBu_r
im = ax.imshow(pivot.values, cmap=cmap, norm=norm, aspect="auto")
plt.colorbar(im, ax=ax, shrink=0.8, label="Coefficient value")

for i in range(pivot.shape[0]):
    for j in range(pivot.shape[1]):
        val = pivot.values[i, j]
        pval = piv_p.values[i, j]
        if not np.isnan(val) and not np.isnan(pval):
            star = "**" if pval < 0.01 else ("*" if pval < 0.05 else "")
            txt = f"{val:.2f}{star}"
            ax.text(j, i, txt, ha="center", va="center", fontsize=7,
                    color="white" if abs(val) > vmax*0.5 else GRAY_DARK)

ax.set_xticks(range(4))
ax.set_xticklabels(["Def","Mid","Fwd","GK"], fontsize=9)
ax.set_yticks(range(len(pivot)))
ax.set_yticklabels(pivot.index, fontsize=7.5)
style_ax(ax, title="Coefficient Heatmap Across Models  (* p<0.05, ** p<0.01)", grid=None)
plt.tight_layout()
save("fig_06_coefficient_heatmap.png")

# ══════════════════════════════════════════════════════════════════════════════
# FIG 07 ── Wage distribution by league + position (faceted boxplot)
# ══════════════════════════════════════════════════════════════════════════════
print("Fig 07 – Wage distributions")
league_order = ["Premier League","La Liga","Bundesliga","Serie A","Ligue 1"]
pos_list     = ["Defenders","Midfielders","Forwards","Goalkeepers"]
d = eff[eff["Comp"].isin(league_order) & eff["position_group"].isin(pos_list)].copy()
d["log_wage_m"] = np.log1p(d["Annual_Wages_EUR"] / 1e6)

fig, axes = plt.subplots(1, 4, figsize=(16, 5), sharey=True)
fig.patch.set_facecolor(BG)
for ax, pos in zip(axes, pos_list):
    sub = d[d["position_group"] == pos]
    data_by_league = [sub[sub["Comp"]==lg]["log_wage_m"].dropna().values for lg in league_order]
    bp = ax.boxplot(data_by_league, patch_artist=True,
                    medianprops=dict(color=POSITION_COLORS[pos], linewidth=2),
                    whiskerprops=dict(color=GRAY_MID, linewidth=0.8),
                    capprops=dict(color=GRAY_MID, linewidth=0.8),
                    flierprops=dict(marker=".", color=GRAY, markersize=2.5, alpha=0.4),
                    widths=0.5)
    for patch in bp["boxes"]:
        patch.set_facecolor(BG)
        patch.set_edgecolor(GRAY_MID)
    ax.set_xticks(range(1, 6))
    ax.set_xticklabels(["EPL","LaL","BL","SA","L1"], fontsize=8, rotation=30)
    style_ax(ax, title=pos, ylabel="Log Annual Wage (€M)" if pos=="Defenders" else None, grid="y")
fig.suptitle("Annual Wage Distribution by League and Position", fontsize=13,
             fontweight="bold", color=GRAY_DARK, y=1.01)
plt.tight_layout()
save("fig_07_violin_wages_by_league.png")

# ══════════════════════════════════════════════════════════════════════════════
# FIG 08 ── Sample composition (bar chart)
# ══════════════════════════════════════════════════════════════════════════════
print("Fig 08 – Sample composition")
league_order = ["Premier League","La Liga","Bundesliga","Serie A","Ligue 1"]
d = eff[eff["Comp"].isin(league_order)].copy()
comp_data = d.groupby(["Comp","Season"]).size().unstack(fill_value=0)
comp_data = comp_data.loc[league_order] if all(lg in comp_data.index for lg in league_order) else comp_data

fig, ax = plt.subplots(figsize=(9, 5))
fig.patch.set_facecolor(BG)
seasons = comp_data.columns.tolist()
x = np.arange(len(comp_data))
width = 0.25
for j, (season, clr) in enumerate(zip(seasons, [ACCENT, GOLD, RED])):
    bars = ax.bar(x + j*width, comp_data[season], width=width, color=clr,
                  alpha=0.85, label=season, zorder=3)
    for bar in bars:
        h = bar.get_height()
        if h > 0:
            ax.text(bar.get_x() + bar.get_width()/2, h+3, str(int(h)),
                    ha="center", va="bottom", fontsize=7.5, color=GRAY_DARK)
ax.set_xticks(x + width)
ax.set_xticklabels([lg.replace(" ", "\n") for lg in comp_data.index], fontsize=9)
style_ax(ax, title="Sample Composition: Player-Season Observations by League and Season",
         ylabel="Number of player-season observations", grid="y")
ax.legend(fontsize=9, frameon=False, title="Season")
total = d.shape[0]
ax.text(0.99, 0.97, f"Total: {total:,} observations", transform=ax.transAxes,
        ha="right", va="top", fontsize=9, color=GRAY_DARK)
plt.tight_layout()
save("fig_08_sample_composition.png")

# ══════════════════════════════════════════════════════════════════════════════
# FIG 09 ── Model performance: adj-R² bar chart
# ══════════════════════════════════════════════════════════════════════════════
print("Fig 09 – Model performance")
# Compute from OLS fitted vs actual
pos_list = ["Defenders","Midfielders","Forwards","Goalkeepers"]
metrics = []
for pos in pos_list:
    sub = eff[eff["position_group"]==pos].dropna(subset=["efficiency_score","log_wage","fitted_log_wage"])
    y = sub["log_wage"].values
    yhat = sub["fitted_log_wage"].values
    ss_res = np.sum((y - yhat)**2)
    ss_tot = np.sum((y - y.mean())**2)
    r2 = 1 - ss_res/ss_tot if ss_tot > 0 else 0
    metrics.append({"position": pos, "R2": r2, "n": len(sub),
                    "mean_abs_error": np.mean(np.abs(y - yhat))})
df_m = pd.DataFrame(metrics)

fig, axes = plt.subplots(1, 2, figsize=(10, 4))
fig.patch.set_facecolor(BG)

clrs = [POSITION_COLORS[p] for p in pos_list]
axes[0].bar(df_m["position"], df_m["R2"], color=clrs, alpha=0.85, zorder=3)
for i, (v, lbl) in enumerate(zip(df_m["R2"], df_m["position"])):
    axes[0].text(i, v+0.005, f"{v:.3f}", ha="center", va="bottom", fontsize=9, color=GRAY_DARK)
axes[0].set_ylim(0, 1)
style_ax(axes[0], title="In-sample R² by Position Model", ylabel="R²", grid="y")
axes[0].set_xticklabels(["Def","Mid","Fwd","GK"])

axes[1].bar(df_m["position"], df_m["n"], color=GRAY, alpha=0.75, zorder=3)
for i, v in enumerate(df_m["n"]):
    axes[1].text(i, v+15, str(v), ha="center", va="bottom", fontsize=9, color=GRAY_DARK)
style_ax(axes[1], title="Sample Size by Position", ylabel="N player-season obs.", grid="y")
axes[1].set_xticklabels(["Def","Mid","Fwd","GK"])

fig.suptitle("Model Fit Summary", fontsize=13, fontweight="bold", color=GRAY_DARK)
plt.tight_layout()
save("fig_09_model_performance.png")

# ══════════════════════════════════════════════════════════════════════════════
# FIG 10 ── Efficiency label breakdown by position
# ══════════════════════════════════════════════════════════════════════════════
print("Fig 10 – Efficiency breakdown")
pos_list = ["Defenders","Midfielders","Forwards","Goalkeepers"]
labels = ["Underpaid","Fair","Overpaid"]
label_colors = {"Underpaid": GREEN, "Fair": GRAY, "Overpaid": RED}
d = eff[eff["position_group"].isin(pos_list)].copy()
counts = d.groupby(["position_group","efficiency_label"]).size().unstack(fill_value=0)
counts = counts.loc[[p for p in pos_list if p in counts.index]]
counts_pct = counts.div(counts.sum(axis=1), axis=0) * 100

fig, ax = plt.subplots(figsize=(9, 5))
fig.patch.set_facecolor(BG)
x = np.arange(len(counts_pct))
bottom = np.zeros(len(counts_pct))
for lbl in ["Underpaid","Fair","Overpaid"]:
    if lbl in counts_pct.columns:
        vals = counts_pct[lbl].values
        bars = ax.bar(x, vals, bottom=bottom, color=label_colors[lbl],
                      alpha=0.85, label=lbl, zorder=3)
        for bar, v, b in zip(bars, vals, bottom):
            if v > 5:
                ax.text(bar.get_x()+bar.get_width()/2, b+v/2, f"{v:.0f}%",
                        ha="center", va="center", fontsize=8.5,
                        color="white", fontweight="bold")
        bottom += vals
ax.set_xticks(x)
ax.set_xticklabels(["Def","Mid","Fwd","GK"], fontsize=10)
ax.set_ylim(0, 100)
style_ax(ax, title="Player Classification by Efficiency Label and Position",
         ylabel="Share of players (%)", grid=None)
ax.legend(frameon=False, fontsize=9, loc="upper right")
plt.tight_layout()
save("fig_10_efficiency_breakdown.png")

# ══════════════════════════════════════════════════════════════════════════════
# FIG 11 ── Mean efficiency score per league×season heatmap
# ══════════════════════════════════════════════════════════════════════════════
print("Fig 11 – Temporal league efficiency")
league_order = ["Premier League","La Liga","Bundesliga","Serie A","Ligue 1"]
d = eff[eff["Comp"].isin(league_order)].copy()
pivot = d.groupby(["Comp","Season"])["efficiency_score"].mean().unstack()
pivot = pivot.loc[league_order] if all(lg in pivot.index for lg in league_order) else pivot

fig, ax = plt.subplots(figsize=(8, 4.5))
fig.patch.set_facecolor(BG)
import matplotlib.colors as mcolors
vabs = np.nanpercentile(np.abs(pivot.values), 95)
norm = mcolors.TwoSlopeNorm(vmin=-vabs, vcenter=0, vmax=vabs)
im = ax.imshow(pivot.values, cmap="RdBu_r", norm=norm, aspect="auto")
plt.colorbar(im, ax=ax, label="Mean efficiency score")
for i in range(pivot.shape[0]):
    for j in range(pivot.shape[1]):
        v = pivot.values[i, j]
        if not np.isnan(v):
            ax.text(j, i, f"{v:.3f}", ha="center", va="center",
                    fontsize=9, color="white" if abs(v) > vabs*0.4 else GRAY_DARK)
ax.set_xticks(range(len(pivot.columns)))
ax.set_xticklabels(pivot.columns, fontsize=9)
ax.set_yticks(range(len(pivot.index)))
ax.set_yticklabels(pivot.index, fontsize=9)
style_ax(ax, title="Mean Efficiency Score by League and Season", grid=None)
plt.tight_layout()
save("fig_11_temporal_league_efficiency.png")

# ══════════════════════════════════════════════════════════════════════════════
# FIG 12 ── Out-of-sample validation
# ══════════════════════════════════════════════════════════════════════════════
print("Fig 12 – OOS validation")
d = oos.copy()
pos_list = ["Defenders","Midfielders","Forwards","Goalkeepers"]
d = d[d["position_group"].isin(pos_list)]
splits = sorted(d["split"].unique())
n_splits = len(splits)
x = np.arange(len(pos_list))
width = 0.35

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
fig.patch.set_facecolor(BG)

colors_sp = [ACCENT, GOLD, RED][:n_splits]
for ax, metric, ylabel, title in zip(
        axes, ["r2_oos","rmse_oos"],
        ["R² (out-of-sample)","RMSE (out-of-sample)"],
        ["Out-of-Sample R² by Position and Split","Out-of-Sample RMSE by Position and Split"]):
    for j, (sp, clr) in enumerate(zip(splits, colors_sp)):
        sub = d[d["split"]==sp]
        sub = sub.set_index("position_group").reindex(pos_list)
        ax.bar(x + j*width, sub[metric], width=width, color=clr,
               alpha=0.85, label=sp, zorder=3)
    ax.set_xticks(x + width*(n_splits-1)/2)
    ax.set_xticklabels(["Def","Mid","Fwd","GK"])
    style_ax(ax, title=title, ylabel=ylabel, grid="y")
    ax.legend(fontsize=8, frameon=False)

fig.suptitle("Temporal Out-of-Sample Validation", fontsize=13,
             fontweight="bold", color=GRAY_DARK)
plt.tight_layout()
save("fig_12_oos_validation.png")

# ══════════════════════════════════════════════════════════════════════════════
# FIG 13 ── Wage rigidity by position
# ══════════════════════════════════════════════════════════════════════════════
print("Fig 13 – Wage rigidity")
d = rigidity.copy()
fig, ax = plt.subplots(figsize=(7, 4.5))
fig.patch.set_facecolor(BG)
clrs = [RED if v > 0.5 else GRAY for v in d["pct_frozen_wage"]]
bars = ax.bar(d["model"], d["pct_frozen_wage"]*100, color=clrs, alpha=0.85, zorder=3)
for bar, v in zip(bars, d["pct_frozen_wage"]):
    ax.text(bar.get_x()+bar.get_width()/2, v*100+0.5,
            f"{v*100:.1f}%", ha="center", va="bottom", fontsize=10, color=GRAY_DARK)
ax.axhline(50, color=GRAY_DARK, linewidth=0.8, linestyle="--", alpha=0.5)
style_ax(ax, title="Wage Rigidity: Share of Players with Frozen Wages Across Seasons",
         ylabel="Share of players with frozen wage (%)", grid="y")
red_patch = mpatches.Patch(color=RED, label="> 50% (high rigidity)")
gray_patch = mpatches.Patch(color=GRAY, label="≤ 50%")
ax.legend(handles=[red_patch, gray_patch], fontsize=9, frameon=False)
plt.tight_layout()
save("fig_13_wage_rigidity.png")

# ══════════════════════════════════════════════════════════════════════════════
# FIG 14 ── Bootstrap ranking uncertainty (top 20 underpaid)
# ══════════════════════════════════════════════════════════════════════════════
print("Fig 14 – Bootstrap rankings")
d = boot.copy()
top_under = d[d["side"]=="underpaid"].nsmallest(20, "mean_rank")
top_under = top_under.sort_values("mean_rank")
top_under["label"] = top_under["Player"].str[:18] + " | " + top_under["Season"].astype(str).str[-4:]

fig, ax = plt.subplots(figsize=(9, 7))
fig.patch.set_facecolor(BG)
y = range(len(top_under))
ax.barh(y, top_under["appear_rate"] if "appear_rate" in top_under else [1]*len(top_under),
        color=GRAY, alpha=0.4, height=0.6, zorder=2)
ax.scatter(top_under["mean_rank"], y, color=GREEN, s=60, zorder=4, label="Mean rank")
if "rank_p10" in top_under and "rank_p90" in top_under:
    ax.errorbar(top_under["mean_rank"], y,
                xerr=[top_under["mean_rank"]-top_under["rank_p10"],
                      top_under["rank_p90"]-top_under["mean_rank"]],
                fmt="none", color=GREEN, linewidth=1.2, capsize=3)
ax.set_yticks(list(y))
ax.set_yticklabels(top_under["label"], fontsize=8)
ax.set_xlabel("Bootstrap Mean Rank (lower = more underpaid)", fontsize=9, color=GRAY_MID)
style_ax(ax, title="Bootstrap Ranking Uncertainty — Top 20 Most Underpaid Players",
         grid="x")
ax.legend(fontsize=9, frameon=False)
plt.tight_layout()
save("fig_14_bootstrap_rankings.png")

# ══════════════════════════════════════════════════════════════════════════════
# FIG 15 ── Squad restructuring savings by league
# ══════════════════════════════════════════════════════════════════════════════
print("Fig 15 – Squad restructuring")
d = restruct.copy()
if "league" not in d.columns and "Comp" in d.columns:
    d = d.rename(columns={"Comp": "league"})
d_agg = d.groupby("league").agg(
    total_saving=("wages_freed_EUR", "sum"),
    n_clubs=("club", "count")
).reset_index().sort_values("total_saving", ascending=True)
d_agg["saving_M"] = d_agg["total_saving"] / 1e6

fig, ax = plt.subplots(figsize=(9, 5))
fig.patch.set_facecolor(BG)
clrs = [GREEN if v > d_agg["saving_M"].median() else GRAY for v in d_agg["saving_M"]]
ax.barh(d_agg["league"], d_agg["saving_M"], color=clrs, alpha=0.85, zorder=3)
for i, (v, n) in enumerate(zip(d_agg["saving_M"], d_agg["n_clubs"])):
    ax.text(v+1, i, f"€{v:.0f}M  ({n} clubs)", va="center", fontsize=9, color=GRAY_DARK)
style_ax(ax, title="Simulated Wage Savings from Squad Restructuring by League",
         xlabel="Total potential savings (€M)", grid="x")
plt.tight_layout()
save("fig_15_squad_restructuring.png")

# ══════════════════════════════════════════════════════════════════════════════
# FIG 16 ── Wage-age profile by position
# ══════════════════════════════════════════════════════════════════════════════
print("Fig 16 – Wage-age profile")
d = eff.dropna(subset=["Age","log_wage","position_group"]).copy()
pos_list = ["Defenders","Midfielders","Forwards","Goalkeepers"]
fig, axes = plt.subplots(2, 2, figsize=(12, 9), sharex=True, sharey=True)
fig.patch.set_facecolor(BG)
axes_flat = axes.flatten()

for ax, pos in zip(axes_flat, pos_list):
    sub = d[d["position_group"]==pos].copy()
    clr = POSITION_COLORS[pos]
    # scatter (gray)
    ax.scatter(sub["Age"], sub["log_wage"], color=GRAY, s=6, alpha=0.3, zorder=2)
    # polynomial fit
    z = np.polyfit(sub["Age"].values, sub["log_wage"].values, 2)
    p = np.poly1d(z)
    age_range = np.linspace(sub["Age"].min(), sub["Age"].max(), 100)
    ax.plot(age_range, p(age_range), color=clr, linewidth=2.5, zorder=4, label="Quadratic fit")
    # mark peak
    peak_age = -z[1]/(2*z[0]) if z[0] != 0 else None
    if peak_age and sub["Age"].min() < peak_age < sub["Age"].max():
        ax.axvline(peak_age, color=clr, linewidth=1.2, linestyle=":", alpha=0.7)
        ax.text(peak_age+0.2, sub["log_wage"].max()-0.2, f"Peak~{peak_age:.0f}y",
                color=clr, fontsize=7.5)
    style_ax(ax, title=pos, xlabel="Age" if pos in ["Forwards","Goalkeepers"] else None,
             ylabel="Log Annual Wage" if pos in ["Defenders","Forwards"] else None, grid="both")

fig.suptitle("Wage-Age Profile by Position (Quadratic Fit)", fontsize=13,
             fontweight="bold", color=GRAY_DARK)
plt.tight_layout()
save("fig_16_wage_age_profile.png")

# ══════════════════════════════════════════════════════════════════════════════
# FIG 17 ── Top over/underpaid diverging bar chart
# ══════════════════════════════════════════════════════════════════════════════
print("Fig 17 – Top mispaid diverging bars")
top_n = 12
top_over  = eff.nlargest(top_n, "efficiency_score")[["Player","Team","Comp","efficiency_score","position_group"]].copy()
top_under = eff.nsmallest(top_n, "efficiency_score")[["Player","Team","Comp","efficiency_score","position_group"]].copy()
combined_top = pd.concat([top_under, top_over])
combined_top["label"] = combined_top["Player"].str[:18] + "\n" + combined_top["Team"].str[:14]
combined_top = combined_top.sort_values("efficiency_score")

fig, ax = plt.subplots(figsize=(9, 10))
fig.patch.set_facecolor(BG)
colors_bar = [GREEN if v < 0 else RED for v in combined_top["efficiency_score"]]
y = range(len(combined_top))
ax.barh(y, combined_top["efficiency_score"], color=colors_bar, alpha=0.85, height=0.65, zorder=3)
ax.axvline(0, color=GRAY_DARK, linewidth=1)
ax.set_yticks(list(y))
ax.set_yticklabels(combined_top["label"], fontsize=7.5)
style_ax(ax, title=f"Top {top_n} Most Underpaid and Overpaid Players (Efficiency Score)",
         xlabel="Efficiency Score (residual from log-wage model)", grid="x")
green_patch = mpatches.Patch(color=GREEN, label="Underpaid")
red_patch   = mpatches.Patch(color=RED,   label="Overpaid")
ax.legend(handles=[green_patch, red_patch], frameon=False, fontsize=9)
plt.tight_layout()
save("fig_17_top_mispaid_diverging.png")

print("\n✓ All 17 figures saved to:", FIG)
