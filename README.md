# Football Salary Efficiency — DBA Thesis · IE University 2025

> 🌐 **Live dashboard:** [pstoclet.github.io/DBA_TFG_CODE_PABLO_STOCLET](https://pstoclet.github.io/DBA_TFG_CODE_PABLO_STOCLET)

Econometric analysis of salary efficiency in European football. The project estimates position-specific wage models using OLS regression, computes individual efficiency scores (observed vs. predicted log-wage), and applies the framework to scouting, squad restructuring, and market intelligence.

**Leagues:** Premier League · La Liga · Bundesliga · Serie A · Ligue 1  
**Seasons:** 2022–23 · 2023–24 · 2024–25 · **Observations:** 6,702 player-seasons  
**Data sources:** FBRef (performance stats) · Capology (salary data) · StatsBomb  
**Author:** Pablo Stoclet · Supervisor: Prof. Paula Abascal Gutierrez-Colomer

---

## Research Questions

| # | Hypothesis | Result |
|---|---|---|
| H1 | Does wage return follow a concave (inverted-U) age curve, and does superstar convexity exist for Forwards? | Partial — age curve confirmed all 4 positions; superstar convexity not significant (p=0.261) |
| H2 | Do leagues follow systematically different wage-setting structures? | Confirmed — Levene's W = 2.44–10.96, all p < 0.05 |
| H3 | Does club identity drive wage premiums beyond individual performance? | Partial — ICC meaningful for Forwards (0.187) and Goalkeepers (0.203); near-zero for DEF/MID |
| H4 | Do frozen wages lock in mispricing and amplify efficiency persistence? | Confirmed — β̂ = 0.554, t = 17.32, p < 10⁻⁶⁴ |

---

## Key Concept: Efficiency Score

```
efficiency_score = log_wage_observed − log_wage_predicted
```

- **> +0.5σ** → player earns above what the model predicts → classified **Overpaid**
- **< −0.5σ** → player earns below what the model predicts → classified **Underpaid**
- Within **±0.5σ** → classified **Fairly Priced**

The threshold is ±0.5 standard deviations of the residual distribution, not a fixed percentage.

---

## Model Performance

| Position | Adj. R² | RMSE | Key Significant Predictors |
|---|---|---|---|
| Defenders | 0.713 | 0.631 | Minutes share, duels, progressive actions |
| Midfielders | 0.692 | 0.672 | Shots on target, key passes, minutes share |
| Forwards | 0.690 | 0.707 | Non-penalty goals p90, shots, goal conversion |
| Goalkeepers | 0.634 | 0.722 | Minutes share, penalty save % |

Models use club-clustered standard errors. Wage peak ages: 31.5 (DEF) · 32.2 (MID) · 32.3 (FWD) · 36.0 (GK).

---

## Regression Specification

```
log(annual_wage) = β₀ + β₁·Age + β₂·Age²
                 + β₃·performance_metrics
                 + β₄·league_dummies
                 + β₅·log(club_wage_budget)
                 + ε
```

Estimated separately per position group. Club-clustered standard errors throughout.

---

## Key Results

| Finding | Value |
|---|---|
| Wage rigidity interaction coefficient (H4) | β̂ = +0.554 (t = 17.32, p = 1.56×10⁻⁶⁴) |
| Efficiency persistence — frozen wages | ρ = 0.882 |
| Efficiency persistence — flexible wages | ρ = 0.328 |
| Forwards in-sample Adj. R² | 0.690 |
| Forwards out-of-sample R² | 0.51–0.56 |
| Defenders / Midfielders OOS R² | 0.13–0.21 |
| Chow structural break (Ligue 1 + Serie A midfielders) | F = 4.73–7.69, p < 0.001 |
| Bootstrap ranking stability (top-20 underpaid) | Jaccard = 0.727 |

Frozen-wage players show mispricing persistence nearly **3× higher** than players on adjusting contracts.

---

## Project Structure

```
TFG_Código/
├── docs/                        # GitHub Pages site (live dashboard)
│   ├── index.html               # Landing page
│   ├── pages/                   # All dashboard pages
│   │   ├── market.html          # League efficiency rankings
│   │   ├── players.html         # Player wage rankings
│   │   ├── squads.html          # Squad salary analysis
│   │   ├── xi.html              # Best Value XI
│   │   ├── models.html          # OLS coefficient explorer
│   │   ├── hypotheses.html      # H1–H4 results
│   │   └── applications.html    # Practical tools
│   ├── data/                    # Static JSON served by api-shim.js
│   └── images/                  # Team logos and player photos
│
├── notebooks/
│   ├── 01_scraping.ipynb        # FBRef and Capology data collection
│   ├── 02_data_cleaning.ipynb   # Merging, deduplication, type fixes
│   ├── 03_feature_engineering.ipynb  # Age², league dummies, position groups
│   ├── 04_ols_regression.ipynb  # Position-specific OLS models
│   └── 05_salary_efficiency_pipeline.ipynb  # Full pipeline: scores + all outputs
│
├── scripts/
│   ├── figure_02_efficiency_by_position_league.py
│   ├── figure_03_wage_premium_heatmap.py
│   ├── figure_04_wage_rigidity_persistence.py
│   ├── figure_05_bootstrap_rankings.py
│   ├── figure_06_injury_robustness.py
│   └── export_static_data.py    # Exports docs/data/ JSON for the dashboard
│
├── src/
│   ├── dashboard/app.py         # Flask web app — run locally
│   └── visualizations/          # Legacy static figure scripts
│
├── data/                        # Tracked in git (raw inputs + pipeline outputs)
│   ├── raw/                     # Source data (club wages, player stats)
│   ├── processed/               # Cleaned and feature-engineered datasets
│   └── results/                 # Pipeline outputs
│       ├── 01_model_coefficients/
│       ├── 02_efficiency_scores/
│       ├── 03_hypothesis_tests/
│       ├── 04_robustness/
│       ├── 05_scouting_hiring/
│       ├── 06_descriptive_stats/
│       ├── 07_figures/          # All thesis figures (figs 02–06 + earlier versions)
│       ├── 08_injury_context/
│       └── 09_interactive_visualizations/
│
├── requirements.txt
└── .gitignore
```

---

## How to Run

**Prerequisites:**
```bash
pip install -r requirements.txt
```

**1. Reproduce the full pipeline (data → model → scores → outputs):**
```bash
jupyter notebook notebooks/01_scraping.ipynb
jupyter notebook notebooks/02_data_cleaning.ipynb
jupyter notebook notebooks/03_feature_engineering.ipynb
jupyter notebook notebooks/04_ols_regression.ipynb
jupyter notebook notebooks/05_salary_efficiency_pipeline.ipynb
```

**2. Regenerate thesis figures:**
```bash
python scripts/figure_02_efficiency_by_position_league.py
python scripts/figure_03_wage_premium_heatmap.py
python scripts/figure_04_wage_rigidity_persistence.py
python scripts/figure_05_bootstrap_rankings.py
python scripts/figure_06_injury_robustness.py
```

**3. Local dashboard** (reads from `data/results/`):
```bash
python src/dashboard/app.py
# → http://localhost:5000
```

**4. Export static JSON for the GitHub Pages dashboard:**
```bash
python scripts/export_static_data.py
```

---

## Further Reading

- **[Live dashboard](https://pstoclet.github.io/DBA_TFG_CODE_PABLO_STOCLET)** — interactive charts and findings summary
- **[docs/output_guide.md](docs/output_guide.md)** — field guide to every results file in `data/results/`
