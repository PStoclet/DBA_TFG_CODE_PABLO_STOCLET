# Injury Context Outputs

This folder contains the injury-context layer used to complement (not replace) the core salary-efficiency model.

## Folder structure

- `00_inputs/`
  - `full_dataset_thesis - 1.csv` (project-local copy of injury source dataset)
  - `team_alias_map.csv` (manual club-name normalization map)

- `01_core_tables/`
  - `injury_context_summary.csv`
  - `injury_context_summary_tiers.csv`
  - `efficiency_with_injury_context.csv`
  - `injury_player_season_overlap.csv`
  - `injury_player_season_overlap_aggregated.csv`

- `02_diagnostics/`
  - `matching_coverage_lift.csv`
  - `ranking_stability_by_tier.csv`
  - `injury_match_diagnostics_rows.csv`
  - `team_alias_suggestions_from_unmatched.csv`

- `03_rankings/`
  - `top20_overpaid_baseline.csv`
  - `top20_overpaid_injury_adjusted.csv`
  - `top20_underpaid_baseline.csv`
  - `top20_underpaid_injury_adjusted.csv`
  - `baseline_vs_injury_adjusted_ranking_shift_overpaid_top20.csv`

- `04_visuals/`
  - `viz_injury_days_vs_efficiency.html`
  - `viz_efficiency_by_injury_bucket.html`
  - `viz_top_overpaid_rank_shift_after_injury_adjustment.html`
  - `viz_injury_match_mode_counts.html`

## Notes

- Edit `00_inputs/team_alias_map.csv` and rerun Section 21 to improve strict coverage.
- Use `02_diagnostics/team_alias_suggestions_from_unmatched.csv` as a checklist for new aliases.
