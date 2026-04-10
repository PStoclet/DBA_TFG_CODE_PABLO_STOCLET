"""
Figure 4 — Wage Rigidity and Efficiency Persistence (H4)
No external title, no caption. Two panels: persistence by position + budget rigidity.
"""
import json, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
from pathlib import Path

ROOT     = Path(__file__).resolve().parents[1]
OUT      = ROOT / "data" / "results" / "07_figures"
OUT.mkdir(parents=True, exist_ok=True)

# ── Data ──────────────────────────────────────────────────────────────────────
df = pd.DataFrame(json.load(open(ROOT / "docs" / "data" / "efficiency.json")))
df = df.dropna(subset=["efficiency_score"]).sort_values(["Player","Season"])
df["prev_wage"] = df.groupby("Player")["Annual_Wages_EUR"].shift(1)
df["frozen"]    = (df["Annual_Wages_EUR"] == df["prev_wage"]) & df["prev_wage"].notna()
df["prev_eff"]  = df.groupby("Player")["efficiency_score"].shift(1)
df2 = df.dropna(subset=["prev_eff"])

POS      = ["Defenders","Midfielders","Forwards","Goalkeepers"]
POS_S    = ["DEF","MID","FWD","GK"]
flex_rho = []
froz_rho = []
for pos in POS:
    sub = df2[df2["position_group"]==pos]
    flex_rho.append(np.corrcoef(sub[~sub["frozen"]]["prev_eff"],
                                sub[~sub["frozen"]]["efficiency_score"])[0,1])
    froz_rho.append(np.corrcoef(sub[sub["frozen"]]["prev_eff"],
                                sub[sub["frozen"]]["efficiency_score"])[0,1])

budget = pd.read_csv(ROOT / "data/results/06_descriptive_stats/01_wage_descriptives/wage_rigidity_by_budget.csv")
BUDGET_LABELS = {"Low budget":"Low\nBudget","Mid budget":"Mid\nBudget","High budget":"High\nBudget"}

# ── Design ────────────────────────────────────────────────────────────────────
BG        = "#FAFAFA"
GRAY_DARK = "#2D2D2D"
GRAY_MID  = "#888888"
GRAY_GRID = "#E8E8E8"
FLEX_CLR  = "#93C5FD"   # steel blue
FROZ_CLR  = "#991B1B"   # dark red
BUDGET_CLRS = ["#991B1B","#D97706","#6B7280"]   # red / amber / gray

fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(13, 5.5),
                                  gridspec_kw={"wspace":0.38})
fig.patch.set_facecolor(BG)

# ── Panel A: Persistence grouped bars ─────────────────────────────────────────
x    = np.arange(len(POS))
w    = 0.33
bars_flex = ax_a.bar(x - w/2, flex_rho, width=w, color=FLEX_CLR,
                     alpha=0.92, zorder=3, label="Flexible wages")
bars_froz = ax_a.bar(x + w/2, froz_rho, width=w, color=FROZ_CLR,
                     alpha=0.92, zorder=3, label="Frozen wages")

for bars, vals in [(bars_flex, flex_rho), (bars_froz, froz_rho)]:
    for bar, v in zip(bars, vals):
        ax_a.text(bar.get_x() + bar.get_width()/2, v + 0.012,
                  f"{v:.3f}", ha="center", va="bottom",
                  fontsize=8.5, color=GRAY_DARK,
                  fontweight="bold" if bars is bars_froz else "normal")

# Delta annotation (avg gap)
avg_delta = np.mean([f - x_ for f, x_ in zip(froz_rho, flex_rho)])
ax_a.annotate("", xy=(3 + w/2, froz_rho[3] + 0.01),
              xytext=(3 + w/2, flex_rho[3] + 0.01),
              arrowprops=dict(arrowstyle="<->", color=GRAY_DARK, lw=1.3))
ax_a.text(3 + w/2 + 0.08, (froz_rho[3] + flex_rho[3])/2,
          f"Δ = +{avg_delta:.2f}", va="center", fontsize=8, color=GRAY_DARK)

ax_a.set_xticks(x)
ax_a.set_xticklabels(POS_S, fontsize=10.5, color=GRAY_DARK)
ax_a.set_ylabel("AR(1) Efficiency Persistence (ρ)", fontsize=9, color=GRAY_DARK)
ax_a.set_ylim(0, 1.05)
ax_a.yaxis.set_major_locator(mticker.MultipleLocator(0.2))
ax_a.set_title("A   Efficiency Persistence by Wage Status",
               fontsize=10, fontweight="bold", color=GRAY_DARK, loc="left", pad=10)
ax_a.text(0.5, -0.13, "Higher ρ → mispricing survives longer into next season",
          transform=ax_a.transAxes, fontsize=7.5, color=GRAY_MID,
          va="top", ha="center")
ax_a.legend(fontsize=8.5, frameon=False, loc="upper left",
            handles=[mpatches.Patch(color=FLEX_CLR, label="Flexible wages"),
                     mpatches.Patch(color=FROZ_CLR, label="Frozen wages")])
ax_a.yaxis.grid(True, color=GRAY_GRID, linewidth=0.5, zorder=0)
ax_a.set_axisbelow(True)
for sp in ax_a.spines.values(): sp.set_edgecolor(GRAY_GRID)
ax_a.set_facecolor(BG)

# ── Panel B: Budget tier rigidity ─────────────────────────────────────────────
tiers  = [BUDGET_LABELS[t] for t in budget["bill_tier"]]
rates  = budget["frozen_rate"].values * 100
wages  = budget["avg_frozen_wage_EUR"].values

bars_b = ax_b.bar(tiers, rates, color=BUDGET_CLRS, alpha=0.90, zorder=3, width=0.5)
for bar, r, w_val in zip(bars_b, rates, wages):
    # Pct label on top
    ax_b.text(bar.get_x() + bar.get_width()/2, r + 0.8,
              f"{r:.1f}%", ha="center", va="bottom",
              fontsize=10, fontweight="bold", color=GRAY_DARK)
    # Avg wage label inside
    ax_b.text(bar.get_x() + bar.get_width()/2, r * 0.45,
              f"avg frozen\n€{w_val/1e6:.1f}M / yr",
              ha="center", va="center", fontsize=7.5,
              color="white", fontweight="bold")

ax_b.set_ylabel("Wages Frozen Year-on-Year (%)", fontsize=9, color=GRAY_DARK)
ax_b.set_ylim(0, 88)
ax_b.yaxis.set_major_locator(mticker.MultipleLocator(10))
ax_b.set_title("B   Wage Rigidity Rate by Club Budget Tier",
               fontsize=10, fontweight="bold", color=GRAY_DARK, loc="left", pad=10)
ax_b.text(0.01, 0.99, "Low-budget clubs most rigid → highest FSR exposure",
          transform=ax_b.transAxes, fontsize=7.5, color=GRAY_MID,
          va="top", ha="left")
ax_b.yaxis.grid(True, color=GRAY_GRID, linewidth=0.5, zorder=0)
ax_b.set_axisbelow(True)
for sp in ax_b.spines.values(): sp.set_edgecolor(GRAY_GRID)
ax_b.set_facecolor(BG)
ax_b.tick_params(axis="x", labelsize=10.5, colors=GRAY_DARK)

# ── Header stats strip ────────────────────────────────────────────────────────
fig.text(0.50, 0.97,
         "Frozen wages:  ρ = 0.882     Flexible wages:  ρ = 0.328     "
         "Interaction:  β̂ = 0.554,  t = 17.32,  p < 0.001",
         ha="center", va="top", fontsize=9, color=GRAY_DARK,
         fontweight="bold")

fig.savefig(OUT / "fig_04_wage_rigidity_persistence.png",
            dpi=300, bbox_inches="tight", facecolor=BG)
print(f"Saved → {OUT / 'fig_04_wage_rigidity_persistence.png'}")
