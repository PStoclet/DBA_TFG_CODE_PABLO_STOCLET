# Output Guide: What Each File Contains and How to Interpret It

This document covers all major outputs in `data/results/`, with a practical focus for thesis work:

- Which file to look at for a given question
- Which columns matter
- How to interpret the results
- Real examples from the pipeline output

---

## 1. Core Interpretation Rule

The central variable throughout the project is:

```
efficiency_score = log_wage_observed − log_wage_estimated
```

Interpretation:

- `efficiency_score > 0`: player earns **above** what the model predicts (tendency to be overpaid).
- `efficiency_score < 0`: player earns **below** what the model predicts (tendency to be underpaid).
- The larger the absolute value, the larger the mismatch.

Labels:

- `Overpaid` / `Fair` / `Underpaid` depend on the threshold set in the pipeline (normally ±0.5 on the log-residual scale).

---

## 2. Folder Map

Inside `data/results/`:

- `01_model_coefficients/` — econometric results for each position-specific model.
- `02_efficiency_scores/` — individual scores and longitudinal analysis.
- `03_hypothesis_tests/` — H1/H2/H3 tests, FSR, Chow test, defensive context.
- `04_robustness/` — methodological robustness (bootstrap, OOS temporal validation, collinearity, threshold stability).
- `05_scouting_hiring/` — operational outputs (signings, positional health, transfer intelligence).
- `06_descriptive_stats/` — descriptive statistics and efficiency drivers.
- `07_figures/` — static figures for the thesis.
- `08_injury_context/` — injury-adjusted analysis.
- `09_interactive_visualizations/` — interactive HTML charts for thesis and presentation.

---

## 3. 01_model_coefficients (reading the model)

### Files

- `coef_defenders.csv`
- `coef_midfielders.csv`
- `coef_forwards.csv`
- `coef_goalkeepers.csv`
- `coef_all_models.csv`
- `summary_defenders.txt`
- `summary_midfielders.txt`
- `summary_forwards.txt`
- `summary_goalkeepers.txt`

### Key columns in `coef_*.csv`

- `variable`: predictor name.
- `coef`: marginal effect on `log_wage`.
- `se`, `t`, `pvalue`: statistical inference.
- `ci_lo`, `ci_hi`: confidence interval.

### Real example

In `coef_defenders.csv`:

- `Age` coef `+0.5906`, p `0.0000`
- `Age2` coef `−0.00937`, p `0.0000`

Interpretation: concave salary profile (rises with age up to a point, then falls) — economically consistent.

### `summary_*.txt`

Provides:

- `n`, `AdjR2`, `RMSE`, `F`, `p(F)`.
- Readable table suitable for thesis appendices.

---

## 4. 02_efficiency_scores (main thesis output)

### Files

- `efficiency_combined.csv`
- `panel_efficiency_comparison.csv`
- `career_trajectory.csv`
- `career_trajectory_summary.csv`

### `efficiency_combined.csv` (central file)

Contains:

- Player data and features used.
- `fitted_log_wage`
- `efficiency_score`
- `efficiency_pct`
- `efficiency_label`
- `position_group`

### Real example

`Edimilson Fernandes (2024–2025, Brest)`:

- `efficiency_score = 0.9959`
- `efficiency_label = Overpaid`

Interpretation: his observed salary is almost 1 log point above what the model predicts for his context.

### `panel_efficiency_comparison.csv`

Compares OLS score vs. within-player panel score to separate the player's "fixed structural" component from the situational component.

Use: supports the argument that part of apparent inefficiency is persistent and part is transient.

---

## 5. 03_hypothesis_tests (theoretical validity)

### Files

- `hypothesis_H1.csv`
- `hypothesis_H2.csv`
- `hypothesis_H3.csv`
- `psr_persistence_test.csv`
- `chow_test_psr_break.csv`
- `psr_era_efficiency.csv`
- `defender_context_within_between.csv`

### H1 (`hypothesis_H1.csv`)

Tests non-linearity (e.g. quadratic productivity term):

- Midfielders: negative and significant quadratic coefficient (concavity confirmed).
- Forwards: positive sign but not significant (inconclusive in the linear-quadratic version).

### H2 (`hypothesis_H2.csv`)

Cross-league comparison (institutional heterogeneity).  
Low p-value means salary structure differs across leagues.

### H3 (`hypothesis_H3.csv`)

ICC by position (clustered by club):

- High ICC → more variance explained by the club component.
- Low ICC → weaker club-level clustering.

### FSR Persistence (`psr_persistence_test.csv`) — key result

Real example:

- `coef_interaction = +0.5541`
- `t = 17.32`, `p = 1.56e-64`
- Persistence with salary adjustment: `0.328`
- Persistence with frozen salary: `0.882`

Interpretation: when the salary does not adjust, inefficiency persists at nearly 3× the rate.

### Chow test (`chow_test_psr_break.csv`)

Structural break test pre vs. post (e.g. 2022–23 vs. 2024–25).

Real example:

- Ligue 1 Midfielders: `F=7.69`, very low p-value.

Interpretation: structural shift in the salary function for that segment.

---

## 6. 04_robustness (how reliable is the model)

### Main files

- `bootstrap_se_comparison.csv`
- `lasso_variable_selection.csv`
- `model_collinearity_summary.csv`
- `model_vif_table.csv`
- `temporal_oos_validation.csv`
- `threshold_robustness_rates.csv`
- `threshold_set_jaccard_final.csv`
- `ranking_bootstrap_uncertainty_final.csv`

### Collinearity

`model_collinearity_summary.csv`:

- `condition_number` by position.
- Very high values indicate coefficient instability (especially relevant for Forwards).

### Temporal OOS validation

`temporal_oos_validation.csv`:

- `rmse_oos`, `r2_oos` by temporal split.
- The most honest metric for out-of-sample generalization.

Real examples:

- Forwards OOS R² around `0.51–0.56` (good).
- Defenders/Midfielders lower (`~0.13–0.21`) — more structural noise.

### Threshold robustness

`threshold_set_jaccard_final.csv`:

- Measures stability of under/overpaid classifications when the threshold changes (0.4/0.5/0.6).

Real example:

- Overpaid 0.4 vs. 0.6: Jaccard `~0.606`.

Interpretation: reasonable but not total stability — correct and realistic.

### Ranking uncertainty

`ranking_bootstrap_uncertainty_final.csv`:

- `mean_rank`, `p10_rank`, `p90_rank`, `appear_rate`.

Real example:

- `Pablo Torre | 2024–2025 | Barcelona`: `mean_rank=1.0`, interval [1,1], `appear_rate~0.635`.

Interpretation: very robust as the top underpaid player within the bootstrap.

---

## 7. 05_scouting_hiring (real-world application)

### Files

- `coach_hiring_suggestions.csv`
- `squad_positional_health.csv`
- `talent_defenders.csv`, `talent_midfielders.csv`, `talent_forwards.csv`, `talent_goalkeepers.csv`
- `scouting_value_scores.csv`
- `scouting_by_league.csv`
- `scouting_by_nationality.csv`
- `transfer_intelligence_signings.csv`
- `transfer_intelligence_summary.csv`
- `cross_league_signing_matrix.csv`
- `squad_restructuring_transactions.csv`
- `squad_restructuring_summary.csv`

### `coach_hiring_suggestions.csv`

Prioritized list of affordable, efficient signings by club.

Real example:

- Real Madrid → Cesar Tarrega (Defenders), `efficiency_score=−1.867`, `value_rating=Exceptional`.

### `transfer_intelligence_summary.csv`

Aggregate "market intelligence" score per club (`transfer_iq_score`).

Interpretation:

- Higher score → better balance between buying value and capturing value in sales.

---

## 8. 06_descriptive_stats (economic narrative)

### Files

- `position_efficiency_profile.csv`
- `position_mean_significance.csv`
- `position_driver_correlations.csv`
- `position_wage_rigidity_effects.csv`
- `position_supply_scarcity_tests.csv`
- `position_tail_pressure.csv`
- `desc_wage_by_position_league.csv`
- `desc_wage_rigidity.csv`
- `ext_ar1_autocorrelation.csv`
- `ext_nationality_premium.csv`
- `ext_club_wage_efficiency.csv`
- `ext_league_premium_over_time.csv`
- `nationality_efficiency_map.csv`
- `wage_rigidity_by_budget.csv`

### `position_tail_pressure.csv` (useful for thesis)

Net overpaid pressure by position:

- `net_overpaid_pressure = overpaid_rate − underpaid_rate`

Real examples:

- Defenders: `+0.0031`
- Forwards: `+0.0043`

Interpretation: small differences in the center, but extreme tails matter.

---

## 9. 09_interactive_visualizations (charts for thesis and defense)

Key files:

- `viz_distribution_efficiency_by_league_position.html`
- `viz_efficiency_state_transitions_sankey.html`
- `viz_wage_setting_density_contours.html`
- `viz_club_efficiency_frontier.html`
- `viz_collinearity_heatmap.html`
- `viz_temporal_oos_rmse.html`
- `viz_threshold_set_jaccard_underpaid_final.html`
- `viz_threshold_set_jaccard_overpaid_final.html`

Recommended use:

- Export screenshots for the PDF thesis.
- Show interactively during the oral defense.

---

## 10. Recommended Reading Order (15-minute overview)

1. `02_efficiency_scores/efficiency_combined.csv`
2. `01_model_coefficients/summary_*.txt`
3. `03_hypothesis_tests/psr_persistence_test.csv`
4. `03_hypothesis_tests/chow_test_psr_break.csv`
5. `04_robustness/temporal_oos_validation.csv`
6. `04_robustness/model_collinearity_summary.csv`
7. `05_scouting_hiring/coach_hiring_suggestions.csv`
8. `09_interactive_visualizations/viz_club_efficiency_frontier.html`

---

## 11. Interpretation Checklist (common errors to avoid)

- Do not conflate correlation with causation.
- Do not interpret statistical significance in isolation without checking OOS robustness.
- Do not present top rankings without bootstrap uncertainty intervals.
- Do not draw global conclusions from a single label threshold.
- Do not ignore collinearity when coefficients change sign across specifications.

---

## 12. Ready-to-Use Thesis Phrases

- "Salary inefficiency is defined as a conditional deviation from the expected wage, not as a normative judgment about the absolute salary level."
- "Temporal robustness results show that out-of-sample predictive capacity is heterogeneous across positions."
- "FSR evidence suggests that contractual rigidity increases the persistence of salary mismatches."
- "Underpaid/overpaid rankings are reported with bootstrap uncertainty to avoid deterministic interpretations."
