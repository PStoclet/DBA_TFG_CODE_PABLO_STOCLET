# Football Salary Efficiency — TFG Bachelor's Thesis


> 🌐 **Live project page:** [pstoclet.github.io/DBA_TFG_CODE_PABLO_STOCLET](https://pstoclet.github.io/DBA_TFG_CODE_PABLO_STOCLET)

Econometric analysis of salary efficiency in European football. The project estimates position-specific wage models using OLS regression, computes individual efficiency scores (observed vs. predicted log-wage), and applies the framework to scouting, squad restructuring, and market intelligence.

**Leagues covered:** Premier League, La Liga, Bundesliga, Serie A, Ligue 1  
**Seasons:** 2022–23 through 2024–25  
**Data sources:** FBRef (performance stats), Capology (salary data)

---

## Research Questions

1. Does the relationship between player productivity and wages follow a non-linear (concave) pattern? (**H1**)
2. Are there systematic salary structure differences across the five major European leagues? (**H2**)
3. What share of salary variance is explained by the club rather than by individual performance? (**H3**)

---

## Key Concept: Efficiency Score

```
efficiency_score = log_wage_observed − log_wage_estimated
```

- **> 0** → player earns above what the model predicts (tendency to be overpaid)
- **< 0** → player earns below what the model predicts (tendency to be underpaid)
- Labels (Overpaid / Fair / Underpaid) use a ±0.5 threshold on the log-residual scale

---

## Project Structure

```
TFG_Código/
├── data/
│   ├── raw/                    # Source data from FBRef and Capology (not tracked by git)
│   │   ├── performance_stats/
│   │   ├── player_salaries/
│   │   └── club_wages/
│   ├── processed/              # Cleaned and feature-engineered datasets (not tracked)
│   └── results/                # Pipeline outputs — all analysis results
│       ├── 01_model_coefficients/    # OLS coefficients and model summaries per position
│       ├── 02_efficiency_scores/     # Individual scores, panel comparison, career trajectory
│       ├── 03_hypothesis_tests/      # H1/H2/H3 tests, PSR, Chow, defensive context
│       ├── 04_robustness/            # Bootstrap, OOS validation, VIF, threshold stability
│       ├── 05_scouting_hiring/       # Transfer intelligence, squad health, scouting scores
│       ├── 06_descriptive_stats/     # Wage rigidity, nationality premium, league effects
│       ├── 07_figures/               # Static figures for thesis
│       ├── 08_injury_context/        # Injury-adjusted analysis
│       └── 09_interactive_visualizations/  # HTML interactive charts
│
├── notebooks/
│   ├── 01_scraping.ipynb             # FBRef and Capology data collection
│   ├── 02_data_cleaning.ipynb        # Merging, deduplication, type fixes
│   ├── 03_feature_engineering.ipynb  # Age², league dummies, position groups
│   ├── 04_ols_regression.ipynb       # Position-specific OLS models
│   └── 05_salary_efficiency_pipeline.ipynb  # Full pipeline: scores + all outputs
│
├── src/
│   ├── dashboard/
│   │   ├── app.py                    # Flask web application (main entry point)
│   │   └── templates/                # Jinja2 HTML templates
│   │       ├── base.html             # Shared layout, CSS theme, Chart.js config
│   │       ├── index.html            # Landing page — key findings overview
│   │       ├── players.html          # Player-level efficiency explorer
│   │       ├── squads.html           # Squad composition and positional health
│   │       ├── market.html           # Transfer market intelligence
│   │       ├── models.html           # Model coefficients and fit statistics
│   │       ├── hypotheses.html       # Hypothesis test results
│   │       ├── applications.html     # Scouting and hiring recommendations
│   │       └── xi.html               # Best XI builder
│   └── visualizations/
│       ├── figure_01_wage_model_fit.py
│       ├── thesis_figures.py
│       └── supplementary_figures.py
│
├── docs/
│   └── output_guide.md          # Field guide: what each results file contains
│
├── requirements.txt
└── .gitignore
```

---

## Regression Specification

Each position group (Defenders, Midfielders, Forwards, Goalkeepers) is estimated separately:

```
log_wage = β₀ + β₁·Age + β₂·Age² + β₃·performance_metrics + β₄·league_dummies + ε
```

Controls include position-specific performance variables (e.g., progressive carries, xG, pressures), club-level wage budget proxies, and season fixed effects.

---

## How to Run

### Prerequisites

```bash
pip install -r requirements.txt
```

### 1. Data Collection

Run notebooks in order:

```bash
jupyter notebook notebooks/01_scraping.ipynb
jupyter notebook notebooks/02_data_cleaning.ipynb
jupyter notebook notebooks/03_feature_engineering.ipynb
```

### 2. Run the Analysis Pipeline

```bash
jupyter notebook notebooks/04_ols_regression.ipynb
jupyter notebook notebooks/05_salary_efficiency_pipeline.ipynb
```

Outputs are written to `data/results/`.

### 3. Launch the Dashboard

```bash
python src/dashboard/app.py
```

Then open [http://localhost:5000](http://localhost:5000) in your browser.

> The dashboard is a Flask web app — not Streamlit. It reads from `data/results/` and serves interactive HTML pages.

---

## Key Results (Summary)

| Finding | Value |
|---|---|
| PSR interaction coefficient | +0.5541 (t=17.32, p=1.56e-64) |
| Salary freeze persistence | 0.882 vs 0.328 with adjustment |
| Forwards OOS R² | ~0.51–0.56 |
| Defenders/Midfielders OOS R² | ~0.13–0.21 |
| Overpaid/Underpaid Jaccard stability (0.4 vs 0.6 threshold) | ~0.606 |

PSR (Profit and Sustainability Regulations) significantly increase wage rigidity — when salaries cannot adjust, salary inefficiencies persist at nearly 3× the rate.

---

## Results File Reference

See [docs/output_guide.md](docs/output_guide.md) for a complete guide to every output file: what it contains, which columns matter, and how to interpret the values.

---

## Dashboard Pages

| Page | URL | Description |
|---|---|---|
| Overview | `/` | Key findings, KPIs, hypothesis summaries |
| Players | `/players` | Individual efficiency scores and rankings |
| Squads | `/squads` | Positional health by club |
| Market | `/market` | Transfer intelligence and cross-league matrix |
| Models | `/models` | OLS coefficients, R², RMSE by position |
| Hypotheses | `/hypotheses` | H1/H2/H3 test results, PSR, Chow test |
| Applications | `/applications` | Scouting recommendations, coach hiring |
| Best XI | `/xi` | Optimal underpaid XI builder |

---

## Notes

- `data/raw/` and `data/processed/` are excluded from version control (large binary files).
- `data/results/` CSV outputs are also excluded — regenerate by running the pipeline notebooks.
- The `.claude/` directory contains local Claude Code settings and is gitignored.
