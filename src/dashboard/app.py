"""
Football Salary Intelligence — Flask Web App (Multi-Page)
Run from project root: python src/dashboard/app.py  →  open http://localhost:5001
"""
from flask import Flask, render_template, jsonify, request, Response, send_file
import pandas as pd
import numpy as np
import os, math, hashlib, re, urllib.parse, io
import requests as req_lib
from pathlib import Path

app = Flask(__name__, template_folder='templates')

# ── Paths (all relative to project root) ───────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS      = PROJECT_ROOT / "data" / "results"
DASH_DIR     = Path(__file__).parent
PHOTO_CACHE  = DASH_DIR / "photo_cache"
LOGO_CACHE   = DASH_DIR / "logo_cache"
PHOTO_MAP    = DASH_DIR / "player_photo_mapping.csv"

# ── Team logo helpers ────────────────────────────────────────
# Transfermarkt club IDs (badge CDN: tmssl.akamaized.net/images/wappen/normquad/{id}.png)
TM_IDS = {
    # ── Premier League ────────────────────────────────────────
    'Arsenal':11,'Aston Villa':405,'Brighton':1237,'Brentford':1246,
    'Chelsea':631,'Crystal Palace':873,'Everton':29,'Fulham':931,
    'Liverpool':31,'Manchester City':281,'Manchester Utd':985,
    'Manchester United':985,'Newcastle Utd':762,'Newcastle United':762,
    'Tottenham':148,'Tottenham Hotspur':148,'West Ham':379,
    'West Ham United':379,'Wolves':543,'Bournemouth':989,
    "Nott'ham Forest":703,'Nottingham Forest':703,'Luton Town':1068,
    'Sheffield Utd':350,'Sheffield United':350,'Burnley':1132,
    'Southampton':180,'Leicester City':1003,'Leeds United':399,
    'Ipswich Town':677,'Ipswich':677,
    # ── La Liga ───────────────────────────────────────────────
    'Real Madrid':418,'Barcelona':131,'Atlético Madrid':13,
    'Atletico Madrid':13,'Athletic Club':621,'Villarreal':383,
    'Real Sociedad':681,'Real Betis':150,'Valencia':1049,
    'Celta Vigo':940,'Sevilla':368,'Getafe':3709,'Girona':12321,
    'Osasuna':331,'Rayo Vallecano':366,'Mallorca':237,
    'Almería':16795,'Almeria':16795,'Cádiz':5860,'Cadiz':5860,
    'Las Palmas':472,'Deportivo Alavés':1108,'Alavés':1108,
    'Granada':2835,'Valladolid':1039,'Eibar':1444,'Espanyol':714,
    'Leganés':3003,'Leganes':3003,
    # ── Bundesliga ────────────────────────────────────────────
    'Bayern Munich':27,'Borussia Dortmund':16,'Dortmund':16,
    'RB Leipzig':23826,'Bayer Leverkusen':15,'Leverkusen':15,
    'Eintracht Frankfurt':24,'Frankfurt':24,'Stuttgart':79,
    'Union Berlin':89,'Wolfsburg':82,"Borussia M'gladbach":18,
    'Gladbach':18,'Mönchengladbach':18,'Freiburg':17,
    'Hoffenheim':533,'Mainz 05':39,'Mainz':39,
    'Werder Bremen':86,'Augsburg':167,'Köln':3,'Koln':3,
    'Darmstadt 98':105,'VfL Bochum':80,'Bochum':80,'Heidenheim':2932,
    'Schalke 04':33,'Hertha BSC':44,'Holstein Kiel':10696,
    'St Pauli':35,'St. Pauli':35,'FC St. Pauli':35,
    # ── Serie A ───────────────────────────────────────────────
    'Inter Milan':46,'Inter':46,'Juventus':506,'AC Milan':5,
    'Milan':5,'Napoli':6195,'Atalanta':800,'Roma':12,
    'Lazio':398,'Fiorentina':430,'Bologna':1040,'Torino':416,
    'Udinese':410,'Genoa':252,'Sassuolo':6574,'Cagliari':1390,
    'Lecce':1839,'Empoli':749,'Hellas Verona':276,'Verona':276,
    'Frosinone':2953,'Monza':6592,'Salernitana':380,
    'Sampdoria':157,'Spezia':3522,'Venezia':907,'Parma':97,
    'Como':17586,
    # ── Ligue 1 ───────────────────────────────────────────────
    'Paris S-G':583,'PSG':583,'Paris Saint-Germain':583,
    'Marseille':244,'Monaco':162,'Lyon':1041,'Lens':826,
    'Lille':1082,'Nice':417,'Rennes':273,'Lorient':1075,
    'Nantes':995,'Montpellier':969,'Strasbourg':667,
    'Reims':1421,'Brest':3911,'Metz':347,'Toulouse':415,
    'Le Havre':738,'Clermont Foot':17512,'Auxerre':2488,'Angers':1054,
    'Saint-Étienne':618,'Saint-Etienne':618,
}
_LEAGUE_HEX = {
    'Premier League':'#7dd3fc','La Liga':'#fcd34d',
    'Bundesliga':'#fca5a5','Serie A':'#93c5fd','Ligue 1':'#f9a8d4',
}

def _team_abbr(t):
    stop = {'fc','cf','ac','as','sc','rc','rb','vfl','tsg','sv','fsv','1.','borussia',
            'real','athletic','club','paris','saint','germain','nott\'ham','aston',
            'crystal','west','newcastle','sheffield','manchester','united','city',
            'utd','town','rovers','wanderers','sport','sporting'}
    words = [w for w in re.split(r'[\s\-\.]+', t) if w.lower() not in stop and len(w) > 1]
    if not words: words = t.split()
    return ''.join(w[0] for w in words[:3]).upper() or t[:3].upper()

def _logo_svg(team, league=''):
    abbr  = _team_abbr(team)
    color = _LEAGUE_HEX.get(league, '#94a3b8')
    # hex to rgb for gradient
    h = color.lstrip('#')
    r2, g2, b2 = (int(h[i:i+2],16) for i in (0,2,4))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 44 44" width="44" height="44">'
        f'<defs>'
        f'<linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">'
        f'<stop offset="0%" style="stop-color:rgb(10,18,38)"/>'
        f'<stop offset="100%" style="stop-color:rgb(15,25,50)"/>'
        f'</linearGradient>'
        f'<radialGradient id="glow" cx="30%" cy="30%" r="70%">'
        f'<stop offset="0%" style="stop-color:rgba({r2},{g2},{b2},0.22)"/>'
        f'<stop offset="100%" style="stop-color:rgba({r2},{g2},{b2},0)"/>'
        f'</radialGradient>'
        f'</defs>'
        f'<rect width="44" height="44" rx="11" fill="url(#bg)"/>'
        f'<rect width="44" height="44" rx="11" fill="url(#glow)"/>'
        f'<rect width="44" height="44" rx="11" fill="none" stroke="{color}" stroke-width="1" stroke-opacity="0.45"/>'
        f'<text x="22" y="29" text-anchor="middle" font-family="system-ui,-apple-system,sans-serif" '
        f'font-weight="800" font-size="12" fill="{color}" opacity="0.95">{abbr}</text></svg>'
    )

# ── Helpers ─────────────────────────────────────────────────
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
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)): return None
    if hasattr(v, 'item'): v = v.item()
    return v

def to_records(df, cols=None, max_rows=None):
    if cols: df = df[[c for c in cols if c in df.columns]]
    if max_rows: df = df.head(max_rows)
    return [{k: clean(v) for k,v in row.items()} for row in df.fillna('').to_dict('records')]

# ── Photo helpers ────────────────────────────────────────────
def _norm(s):   return re.sub(r"\s+", " ", str(s).strip().lower())
def _pkey(p,t): return hashlib.sha1(f"{_norm(p)}|{_norm(t)}".encode()).hexdigest()[:20]

_photo_urls = {}
if PHOTO_MAP.exists():
    _pm = pd.read_csv(PHOTO_MAP)
    for _, r in _pm.iterrows():
        p = str(r.get('Player','')).strip()
        u = str(r.get('photo_url','')).strip()
        if p and u.startswith('http'):
            _photo_urls[p.lower()] = u
    print(f"  📸 Photo map: {len(_photo_urls)} players")

_POS_GRAD = {
    'Goalkeepers': ('245,158,11',  '180,110,5'),
    'Defenders':   ('96,165,250',  '37,99,235'),
    'Midfielders': ('192,132,252', '126,58,237'),
    'Forwards':    ('251,146,60',  '234,88,12'),
}

def _player_avatar_svg(player, pos=''):
    """Generate a beautiful gradient avatar for players without a photo."""
    words = [w for w in re.split(r'[\s\-\.]', player.strip()) if w and w[0].isalpha()]
    ini   = ''.join(w[0] for w in words)[:2].upper() or '?'
    c1, c2 = _POS_GRAD.get(pos, ('99,102,241', '79,70,229'))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 160" width="120" height="160">'
        f'<defs>'
        f'<linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">'
        f'<stop offset="0%" stop-color="rgb(10,18,38)"/>'
        f'<stop offset="100%" stop-color="rgb(17,28,52)"/>'
        f'</linearGradient>'
        f'<radialGradient id="glow" cx="50%" cy="38%" r="60%">'
        f'<stop offset="0%" stop-color="rgba({c1},0.30)"/>'
        f'<stop offset="100%" stop-color="rgba({c1},0)"/>'
        f'</radialGradient>'
        f'</defs>'
        f'<rect width="120" height="160" fill="url(#bg)"/>'
        f'<rect width="120" height="160" fill="url(#glow)"/>'
        f'<circle cx="60" cy="60" r="38" fill="rgba({c1},0.10)" stroke="rgba({c1},0.40)" stroke-width="1.5"/>'
        f'<text x="60" y="75" text-anchor="middle"'
        f' font-family="system-ui,-apple-system,sans-serif"'
        f' font-weight="800" font-size="30" fill="rgba({c1},1.0)">{ini}</text>'
        f'<rect x="0" y="0" width="3" height="160" fill="rgba({c1},0.8)"/>'
        f'</svg>'
    )

def photo_url_for(player, team='', pos=''):
    p = urllib.parse.quote(str(player))
    t = urllib.parse.quote(str(team))
    g = urllib.parse.quote(str(pos))
    return f"/api/photo?player={p}&team={t}&pos={g}"

# ── Load all CSVs at startup ─────────────────────────────────
print("\n⚽  Loading Football Intelligence data …")
eff      = safe_load("02_efficiency_scores/01_core_efficiency/efficiency_combined.csv")
coef_all = safe_load("01_model_coefficients/01_linear_model_coefficients/coef_all_models.csv")
psr_era  = safe_load("03_hypothesis_tests/02_psr_tests/psr_era_efficiency.csv")
psr_pers = safe_load("03_hypothesis_tests/02_psr_tests/psr_persistence_test.csv")
chow     = safe_load("03_hypothesis_tests/03_structural_breaks/chow_test_psr_break.csv")
h1       = safe_load("03_hypothesis_tests/01_core_hypotheses/hypothesis_H1.csv")
h2       = safe_load("03_hypothesis_tests/01_core_hypotheses/hypothesis_H2.csv")
h3       = safe_load("03_hypothesis_tests/01_core_hypotheses/hypothesis_H3.csv")
hiring   = safe_load("05_scouting_hiring/01_hiring_engine/coach_hiring_suggestions.csv")
health   = safe_load("05_scouting_hiring/01_hiring_engine/squad_positional_health.csv")
t_def    = safe_load("05_scouting_hiring/03_scouting_scores/talent_defenders.csv")
t_mid    = safe_load("05_scouting_hiring/03_scouting_scores/talent_midfielders.csv")
t_fwd    = safe_load("05_scouting_hiring/03_scouting_scores/talent_forwards.csv")
t_gk     = safe_load("05_scouting_hiring/03_scouting_scores/talent_goalkeepers.csv")

for df, lbl in [(t_def,'Defenders'),(t_mid,'Midfielders'),(t_fwd,'Forwards'),(t_gk,'Goalkeepers')]:
    if not df.empty and 'position_group' not in df.columns:
        df['position_group'] = lbl

EFF_THRESHOLD = 0.18  # ≈ ±20% wage deviation

if not eff.empty:
    eff['position_group'] = eff['position_group'].replace({'Defensas':'Defenders'})
    # Tripartite efficiency label
    def _classify(s):
        if pd.isna(s): return 'Unknown'
        return 'Underpaid' if s < -EFF_THRESHOLD else ('Overpaid' if s > EFF_THRESHOLD else 'Fairly Paid')
    eff['efficiency_label'] = eff['efficiency_score'].map(_classify)
    # Ensure efficiency_pct exists
    if 'efficiency_pct' not in eff.columns:
        eff['efficiency_pct'] = ((np.exp(eff['efficiency_score'].fillna(0)) - 1) * 100).round(1)
    SEASONS = sorted(eff['Season'].dropna().unique().tolist())
    LEAGUES = sorted(eff['Comp'].dropna().unique().tolist())
    LATEST  = SEASONS[-1] if SEASONS else None
else:
    SEASONS, LEAGUES, LATEST = [], [], None

print(f"  ✅ efficiency_combined: {len(eff):,} rows | seasons={SEASONS}")
print(f"  🌐 Ready!\n")

# ── Filter helper ──────────────────────────────────────────
def apply_filters(df, season=None, leagues=None):
    if season and 'Season' in df.columns:
        df = df[df['Season'] == season]
    if leagues and 'Comp' in df.columns:
        df = df[df['Comp'].isin(leagues)]
    return df

def parse_request_filters():
    season  = request.args.get('season') or LATEST
    leagues = [l for l in request.args.getlist('league') if l] or LEAGUES
    return season, leagues

# ════════════════════════════════════════════════════════════
# HTML ROUTES (Pages)
# ════════════════════════════════════════════════════════════
@app.route('/')
def home():
    return render_template('index.html', page='home', seasons=SEASONS, leagues=LEAGUES, latest=LATEST)

@app.route('/market')
def market():
    return render_template('market.html', page='market', seasons=SEASONS, leagues=LEAGUES, latest=LATEST)

@app.route('/players')
def players():
    return render_template('players.html', page='players', seasons=SEASONS, leagues=LEAGUES, latest=LATEST)

@app.route('/squads')
def squads():
    return render_template('squads.html', page='squads', seasons=SEASONS, leagues=LEAGUES, latest=LATEST)

@app.route('/xi')
def xi_page():
    return render_template('xi.html', page='xi', seasons=SEASONS, leagues=LEAGUES, latest=LATEST)

@app.route('/models')
def models():
    return render_template('models.html', page='models', seasons=SEASONS, leagues=LEAGUES, latest=LATEST)

@app.route('/hypotheses')
def hypotheses():
    return render_template('hypotheses.html', page='hypotheses', seasons=SEASONS, leagues=LEAGUES, latest=LATEST)

@app.route('/applications')
def applications():
    return render_template('applications.html', page='applications', seasons=SEASONS, leagues=LEAGUES, latest=LATEST)

# ════════════════════════════════════════════════════════════
# API ENDPOINTS
# ════════════════════════════════════════════════════════════

@app.route('/api/photo')
def api_photo():
    player = request.args.get('player','').strip()
    team   = request.args.get('team','').strip()
    pos    = request.args.get('pos','').strip()
    key    = _pkey(player, team)
    cached = PHOTO_CACHE / (key + '.jpg')
    if cached.exists():
        return send_file(str(cached), mimetype='image/jpeg')
    url = _photo_urls.get(player.lower())
    if url:
        try:
            r = req_lib.get(url, timeout=4, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.transfermarkt.com/',
            })
            if r.status_code == 200 and r.headers.get('content-type','').startswith('image'):
                PHOTO_CACHE.mkdir(exist_ok=True)
                cached.write_bytes(r.content)
                return Response(r.content, mimetype='image/jpeg')
        except Exception as e:
            print(f"  Photo fetch failed {player}: {e}")
    # Return a beautiful generated avatar instead of 404
    svg = _player_avatar_svg(player, pos)
    return Response(svg, mimetype='image/svg+xml',
                    headers={'Cache-Control': 'public, max-age=86400'})


@app.route('/api/team-logo')
def api_team_logo():
    team   = request.args.get('team','').strip()
    league = request.args.get('league','').strip()
    tm_id  = TM_IDS.get(team)
    if tm_id:
        cached = LOGO_CACHE / f"tm_{tm_id}.png"
        if cached.exists():
            return send_file(str(cached), mimetype='image/png')
        try:
            r = req_lib.get(
                f"https://tmssl.akamaized.net/images/wappen/normquad/{tm_id}.png",
                timeout=4,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': 'https://www.transfermarkt.com/',
                    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                }
            )
            if r.status_code == 200 and 'image' in r.headers.get('content-type',''):
                LOGO_CACHE.mkdir(exist_ok=True)
                cached.write_bytes(r.content)
                return Response(r.content, mimetype='image/png')
        except Exception as e:
            print(f"  Logo fetch failed {team} (TM {tm_id}): {e}")
    return Response(_logo_svg(team, league), mimetype='image/svg+xml',
                    headers={'Cache-Control':'public, max-age=86400'})


@app.route('/api/efficiency-histogram')
def api_efficiency_histogram():
    season, leagues = parse_request_filters()
    df = apply_filters(eff.copy(), season, leagues)
    if df.empty or 'efficiency_score' not in df.columns:
        return jsonify([])
    scores = df['efficiency_score'].dropna()
    bins = np.arange(-3.0, 3.25, 0.25)
    counts, edges = np.histogram(scores, bins=bins)
    result = []
    for i, cnt in enumerate(counts):
        mid = round((edges[i] + edges[i+1]) / 2, 3)
        result.append({'bin': round(edges[i], 2), 'mid': mid, 'count': int(cnt),
                       'label': f'{edges[i]:.2f} to {edges[i+1]:.2f}'})
    return jsonify(result)


@app.route('/api/meta')
def api_meta():
    return jsonify({'seasons': SEASONS, 'leagues': LEAGUES, 'latest': LATEST})


@app.route('/api/stats')
def api_stats():
    season, leagues = parse_request_filters()
    df = apply_filters(eff.copy(), season, leagues)
    n  = len(df)
    if n == 0: return jsonify({'n':0})
    n_ov = int((df['efficiency_label']=='Overpaid').sum())      if 'efficiency_label' in df.columns else 0
    n_un = int((df['efficiency_label']=='Underpaid').sum())     if 'efficiency_label' in df.columns else 0
    n_fa = int((df['efficiency_label']=='Fairly Paid').sum())   if 'efficiency_label' in df.columns else 0
    return jsonify({
        'total':           n,
        'unique_players':  int(df['Player'].nunique()) if 'Player' in df.columns else 0,
        'leagues':         int(df['Comp'].nunique())   if 'Comp'   in df.columns else 0,
        'pct_overpaid':    round(n_ov/n*100, 1),
        'pct_underpaid':   round(n_un/n*100, 1),
        'pct_fairly_paid': round(n_fa/n*100, 1),
        'mean_eff':        round(float(df['efficiency_score'].mean()), 4) if 'efficiency_score' in df.columns else 0,
        'median_wage':     int(df['Annual_Wages_EUR'].median()) if 'Annual_Wages_EUR' in df.columns else 0,
    })


@app.route('/api/league-stats')
def api_league_stats():
    season, leagues = parse_request_filters()
    df = apply_filters(eff.copy(), season, leagues)
    if df.empty: return jsonify([])
    g = df.groupby('Comp').agg(
        mean=('efficiency_score','mean'), std=('efficiency_score','std'),
        n=('efficiency_score','count'),
        pct_ov=('efficiency_label', lambda x:(x=='Overpaid').mean()*100),
        pct_un=('efficiency_label', lambda x:(x=='Underpaid').mean()*100),
        median_wage=('Annual_Wages_EUR','median'),
    ).reset_index()
    return jsonify(to_records(g))


@app.route('/api/position-league')
def api_pos_league():
    season, leagues = parse_request_filters()
    df = apply_filters(eff.copy(), season, leagues)
    if df.empty: return jsonify([])
    g = df.groupby(['Comp','position_group'])['efficiency_score'].mean().reset_index()
    g.columns = ['league','position','mean']
    return jsonify(to_records(g))


@app.route('/api/top-players')
def api_top_players():
    season, leagues = parse_request_filters()
    n       = int(request.args.get('n', 20))
    type_   = request.args.get('type', 'underpaid')
    pos     = request.args.get('position', 'all')
    df = apply_filters(eff.copy(), season, leagues)
    if pos != 'all' and 'position_group' in df.columns:
        df = df[df['position_group']==pos]
    if type_ == 'underpaid':
        df = df.nsmallest(n, 'efficiency_score')
    elif type_ == 'overpaid':
        df = df.nlargest(n, 'efficiency_score')
    else:  # fairly_paid: closest to 0
        df = df.iloc[(df['efficiency_score'].abs()).argsort()].head(n)
    COLS = ['Player','Team','Comp','Season','Age','Nation','position_group',
            'Annual_Wages_EUR','efficiency_score','efficiency_pct','efficiency_label']
    result = []
    for _, r in df[[c for c in COLS if c in df.columns]].iterrows():
        d = {k: clean(v) for k,v in r.items()}
        d['photo_url'] = photo_url_for(r.get('Player',''), r.get('Team',''), r.get('position_group',''))
        result.append(d)
    return jsonify(result)


@app.route('/api/scatter')
def api_scatter():
    season, leagues = parse_request_filters()
    pos = request.args.get('position','all')
    df  = apply_filters(eff.copy(), season, leagues)
    if pos != 'all' and 'position_group' in df.columns:
        df = df[df['position_group']==pos]
    df = df.dropna(subset=['Annual_Wages_EUR','efficiency_score'])
    df = df.sample(min(len(df), 800), random_state=42) if len(df) > 800 else df
    COLS = ['Player','Team','Comp','position_group','Annual_Wages_EUR','efficiency_score','efficiency_label']
    return jsonify(to_records(df, COLS))


@app.route('/api/squads')
def api_squads():
    season, leagues = parse_request_filters()
    df = apply_filters(eff.copy(), season, leagues)
    if df.empty: return jsonify([])
    g = df.groupby(['Team','Comp']).agg(
        mean_eff=('efficiency_score','mean'),
        median_eff=('efficiency_score','median'),
        n=('efficiency_score','count'),
        pct_ov=('efficiency_label', lambda x:(x=='Overpaid').mean()*100),
        pct_un=('efficiency_label', lambda x:(x=='Underpaid').mean()*100),
        pct_fair=('efficiency_label', lambda x:(x=='Fairly Paid').mean()*100),
        total_wages=('Annual_Wages_EUR','sum'),
        mean_wage=('Annual_Wages_EUR','mean'),
    ).reset_index()
    g['rank_eff'] = g['mean_eff'].rank()
    records = to_records(g)
    for rec in records:
        rec['logo_url'] = f"/api/team-logo?team={urllib.parse.quote(rec.get('Team',''))}&league={urllib.parse.quote(rec.get('Comp',''))}"
    return jsonify(records)


@app.route('/api/squad-detail')
def api_squad_detail():
    season, leagues = parse_request_filters()
    team = request.args.get('team','')
    df = apply_filters(eff.copy(), season, leagues)
    df = df[df['Team']==team].copy()
    COLS = ['Player','Team','Comp','Season','Age','Nation','position_group',
            'Annual_Wages_EUR','efficiency_score','efficiency_pct','efficiency_label']
    result = []
    for _, r in df[[c for c in COLS if c in df.columns]].iterrows():
        d = {k: clean(v) for k,v in r.items()}
        d['photo_url'] = photo_url_for(r.get('Player',''), r.get('Team',''), r.get('position_group',''))
        result.append(d)
    result.sort(key=lambda x: (x.get('efficiency_score') or 0))
    # Add per-player label if not already derived
    for d in result:
        s = d.get('efficiency_score') or 0
        d['efficiency_label'] = 'Underpaid' if s < -EFF_THRESHOLD else ('Overpaid' if s > EFF_THRESHOLD else 'Fairly Paid')
    return jsonify(result)


@app.route('/api/squad-health')
def api_squad_health():
    season, leagues = parse_request_filters()
    df = health.copy() if not health.empty else pd.DataFrame()
    if df.empty: return jsonify([])
    return jsonify(to_records(df))


@app.route('/api/formation-xi')
def api_formation_xi():
    season, leagues = parse_request_filters()
    xi_type = request.args.get('type','underpaid')  # underpaid or overpaid

    slots = [('Goalkeepers',t_gk,1,'GK'),('Defenders',t_def,4,'DEF'),
             ('Midfielders',t_mid,4,'MID'),('Forwards',t_fwd,2,'FWD')]
    xi = []
    for pos_name, df, count, abbr in slots:
        if df.empty: continue
        sub = apply_filters(df.copy(), season, leagues)
        if sub.empty: sub = df.copy()
        players = sub.nsmallest(count,'efficiency_score') if xi_type=='underpaid' else sub.nlargest(count,'efficiency_score')
        for i, (_,r) in enumerate(players.iterrows()):
            xi.append({
                'player':     r.get('Player',''),
                'team':       r.get('Team',''),
                'league':     r.get('Comp',''),
                'position':   pos_name, 'abbr': abbr,
                'efficiency': round(float(r.get('efficiency_score',0)),2),
                'eff_pct':    round(float(r.get('efficiency_pct',0)),1) if pd.notna(r.get('efficiency_pct')) else 0,
                'wage':       int(r.get('Annual_Wages_EUR',0)) if pd.notna(r.get('Annual_Wages_EUR')) else 0,
                'slot':       i,
                'photo_url':  photo_url_for(r.get('Player',''), r.get('Team',''), pos_name),
            })
    return jsonify(xi)


@app.route('/api/coefficients')
def api_coefficients():
    if coef_all.empty: return jsonify([])
    SKIP = {'const','Age2','G_Sh_zero','SoTPct_zero','SavePct_PK_zero',
            'tkl_above_system','int_above_system','sota_vs_avg'}
    df = coef_all.copy()
    if 'variable' in df.columns:
        df = df[~df['variable'].isin(SKIP)]
        df = df[~df['variable'].str.lower().str.contains('intercept',na=False)]
    pos = request.args.get('position')
    if pos and 'model' in df.columns:
        df = df[df['model']==pos]
    result = []
    for _, r in df.iterrows():
        result.append({
            'model':       r.get('model',''),
            'variable':    r.get('variable',''),
            'coef':        round(float(r['coef']),4) if pd.notna(r.get('coef')) else 0,
            'se':          round(float(r['se']),4)   if pd.notna(r.get('se'))   else 0,
            'pvalue':      float(r['pvalue'])          if pd.notna(r.get('pvalue')) else 1,
            'ci_lo':       round(float(r['ci_lo']),4) if pd.notna(r.get('ci_lo')) else 0,
            'ci_hi':       round(float(r['ci_hi']),4) if pd.notna(r.get('ci_hi')) else 0,
            'significant': float(r.get('pvalue',1)) < 0.05,
        })
    return jsonify(result)


@app.route('/api/model-summaries')
def api_model_summaries():
    # Hard-coded from analysis results (thesis constants)
    return jsonify([
        {'position':'Defenders',  'r2':0.713,'rmse':0.42,'n':2250,'f_stat':None},
        {'position':'Midfielders','r2':0.692,'rmse':0.45,'n':3005,'f_stat':None},
        {'position':'Forwards',   'r2':0.690,'rmse':0.47,'n':925, 'f_stat':None},
        {'position':'Goalkeepers','r2':0.634,'rmse':0.51,'n':526, 'f_stat':None},
    ])


@app.route('/api/hypotheses')
def api_hypotheses():
    result = {'H1':[],'H2':[],'H3':[],'chow':[],'psr_persist':{}}
    for _, r in h1.iterrows():
        result['H1'].append({'model':r.get('model',''),'coef':round(float(r.get('coef_NPGls_p90_sq',0)),4),
            'pvalue':float(r.get('pvalue',1)),'significant':float(r.get('pvalue',1))<0.05})
    for _, r in h2.iterrows():
        result['H2'].append({'model':r.get('model',''),'levene_W':round(float(r.get('levene_W',0)),3),
            'pvalue':float(r.get('levene_pvalue',1)),'significant':float(r.get('levene_pvalue',1))<0.05})
    for _, r in h3.iterrows():
        result['H3'].append({'model':r.get('model',''),'icc':float(r.get('icc',0)),
            'clubs':int(r.get('clubs_qualifying',0))})
    for _, r in chow.iterrows():
        result['chow'].append({'league':r.get('league',''),'position':r.get('position',''),
            'F':round(float(r.get('F',0)),3),'pvalue':float(r.get('p',1)),
            'significant':float(r.get('p',1))<0.05,'n':int(r.get('n',0))})
    if not psr_pers.empty:
        r = psr_pers.iloc[0]
        result['psr_persist'] = {
            'normal': round(float(r.get('persistence_wage_adjusts',0.33)),4),
            'frozen': round(float(r.get('persistence_wage_frozen',0.88)),4),
            't':      round(float(r.get('t_interaction',17.3)),2),
            'p':      float(r.get('p_interaction',1.56e-64)),
            'r2':     round(float(r.get('r2_adj',0.52)),4),
        }
    return jsonify(result)


@app.route('/api/psr-era')
def api_psr_era():
    if psr_era.empty: return jsonify([])
    return jsonify(to_records(psr_era))


if __name__ == '__main__':
    print("🌐  http://localhost:5001\n")
    app.run(debug=True, port=5001, host='0.0.0.0')
