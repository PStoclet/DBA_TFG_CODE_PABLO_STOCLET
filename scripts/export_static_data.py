"""
Export static JSON data for the GitHub Pages site.
Run from the project root: python scripts/export_static_data.py

Outputs go to docs/data/ and are committed to git.
"""
import json, math
import numpy as np
import pandas as pd
from pathlib import Path

ROOT    = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "data" / "results"
OUT     = ROOT / "docs" / "data"
OUT.mkdir(exist_ok=True)

EFF_THRESHOLD = 0.18

def safe_load(rel):
    p = RESULTS / rel
    try:
        df = pd.read_csv(p, low_memory=False)
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        return df
    except Exception as e:
        print(f"  ⚠  {p.name}: {e}")
        return pd.DataFrame()

def clean(v):
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    if hasattr(v, 'item'):
        v = v.item()
    return v

def to_records(df, cols=None):
    if cols:
        df = df[[c for c in cols if c in df.columns]]
    return [{k: clean(v) for k, v in row.items()} for row in df.fillna('').to_dict('records')]

def write_json(name, data):
    path = OUT / name
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
    size_kb = path.stat().st_size / 1024
    print(f"  ✅ {name} ({size_kb:.0f} KB)")

# ── Load data ──────────────────────────────────────────────
print("\n⚽  Loading data …")

eff      = safe_load("02_efficiency_scores/01_core_efficiency/efficiency_combined.csv")
coef_all = safe_load("01_model_coefficients/01_linear_model_coefficients/coef_all_models.csv")
psr_era  = safe_load("03_hypothesis_tests/02_psr_tests/psr_era_efficiency.csv")
psr_pers = safe_load("03_hypothesis_tests/02_psr_tests/psr_persistence_test.csv")
chow     = safe_load("03_hypothesis_tests/03_structural_breaks/chow_test_psr_break.csv")
h1       = safe_load("03_hypothesis_tests/01_core_hypotheses/hypothesis_H1.csv")
h2       = safe_load("03_hypothesis_tests/01_core_hypotheses/hypothesis_H2.csv")
h3       = safe_load("03_hypothesis_tests/01_core_hypotheses/hypothesis_H3.csv")

# ── 1. efficiency.json ─────────────────────────────────────
print("\n📊 Exporting efficiency data …")
if not eff.empty:
    eff['position_group'] = eff['position_group'].replace({'Defensas': 'Defenders'})

    def classify(s):
        if pd.isna(s):
            return 'Unknown'
        return 'Underpaid' if s < -EFF_THRESHOLD else ('Overpaid' if s > EFF_THRESHOLD else 'Fairly Paid')

    eff['efficiency_label'] = eff['efficiency_score'].map(classify)

    if 'efficiency_pct' not in eff.columns:
        eff['efficiency_pct'] = ((np.exp(eff['efficiency_score'].fillna(0)) - 1) * 100).round(1)

    COLS = ['Player', 'Team', 'Comp', 'Season', 'Age', 'Nation', 'position_group',
            'Annual_Wages_EUR', 'efficiency_score', 'efficiency_pct', 'efficiency_label']

    records = to_records(eff, COLS)
    write_json('efficiency.json', records)
    print(f"     {len(records):,} player-seasons")
else:
    print("  ⚠  efficiency_combined.csv not found — skipping")

# ── 2. coefficients.json ───────────────────────────────────
print("\n📐 Exporting model coefficients …")
if not coef_all.empty:
    SKIP = {'const', 'Age2', 'G_Sh_zero', 'SoTPct_zero', 'SavePct_PK_zero',
            'tkl_above_system', 'int_above_system', 'sota_vs_avg'}
    df = coef_all.copy()
    if 'variable' in df.columns:
        df = df[~df['variable'].isin(SKIP)]
        df = df[~df['variable'].str.lower().str.contains('intercept', na=False)]
    result = []
    for _, r in df.iterrows():
        result.append({
            'model':       r.get('model', ''),
            'variable':    r.get('variable', ''),
            'coef':        round(float(r['coef']), 4) if pd.notna(r.get('coef')) else 0,
            'se':          round(float(r['se']), 4)   if pd.notna(r.get('se'))   else 0,
            'pvalue':      float(r['pvalue'])           if pd.notna(r.get('pvalue')) else 1,
            'ci_lo':       round(float(r['ci_lo']), 4) if pd.notna(r.get('ci_lo')) else 0,
            'ci_hi':       round(float(r['ci_hi']), 4) if pd.notna(r.get('ci_hi')) else 0,
            'significant': float(r.get('pvalue', 1)) < 0.05,
        })
    write_json('coefficients.json', result)
else:
    print("  ⚠  coef_all_models.csv not found — skipping")

# ── 3. hypotheses.json ─────────────────────────────────────
print("\n🔬 Exporting hypothesis results …")
hyp = {'H1': [], 'H2': [], 'H3': [], 'chow': [], 'psr_persist': {}}

for _, r in h1.iterrows():
    hyp['H1'].append({
        'model':       r.get('model', ''),
        'coef':        round(float(r.get('coef_NPGls_p90_sq', 0)), 4),
        'pvalue':      float(r.get('pvalue', 1)),
        'significant': float(r.get('pvalue', 1)) < 0.05,
    })

for _, r in h2.iterrows():
    hyp['H2'].append({
        'model':       r.get('model', ''),
        'levene_W':    round(float(r.get('levene_W', 0)), 3),
        'pvalue':      float(r.get('levene_pvalue', 1)),
        'significant': float(r.get('levene_pvalue', 1)) < 0.05,
    })

for _, r in h3.iterrows():
    hyp['H3'].append({
        'model': r.get('model', ''),
        'icc':   float(r.get('icc', 0)),
        'clubs': int(r.get('clubs_qualifying', 0)),
    })

for _, r in chow.iterrows():
    hyp['chow'].append({
        'league':      r.get('league', ''),
        'position':    r.get('position', ''),
        'F':           round(float(r.get('F', 0)), 3),
        'pvalue':      float(r.get('p', 1)),
        'significant': float(r.get('p', 1)) < 0.05,
        'n':           int(r.get('n', 0)),
    })

if not psr_pers.empty:
    r = psr_pers.iloc[0]
    hyp['psr_persist'] = {
        'normal': round(float(r.get('persistence_wage_adjusts', 0.33)), 4),
        'frozen': round(float(r.get('persistence_wage_frozen', 0.88)), 4),
        't':      round(float(r.get('t_interaction', 17.3)), 2),
        'p':      float(r.get('p_interaction', 1.56e-64)),
        'r2':     round(float(r.get('r2_adj', 0.52)), 4),
    }

write_json('hypotheses.json', hyp)

# ── 4. psr_era.json ────────────────────────────────────────
print("\n📈 Exporting FSR era data …")
if not psr_era.empty:
    write_json('psr_era.json', to_records(psr_era))
else:
    print("  ⚠  psr_era_efficiency.csv not found — skipping")

print("\n✅  Done. Files written to docs/data/\n")
