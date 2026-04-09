"""
Fetch player headshot URLs from Wikipedia for all players in efficiency_combined.csv.
Outputs docs/data/photos.json  — a dict of { "Player Name": "https://..." }

Run from project root:  python scripts/fetch_player_photos.py
"""
import json, ssl, time, unicodedata
import urllib.request, urllib.parse
from pathlib import Path

# macOS often lacks system certs for Python — build a permissive context
try:
    import certifi
    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CTX = ssl._create_unverified_context()  # noqa: S501 — no cert bundle available

import pandas as pd

ROOT    = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "data" / "results"
OUT     = ROOT / "docs" / "data" / "photos.json"

WIKI_API = "https://en.wikipedia.org/w/api.php"
BATCH    = 50      # Wikipedia allows up to 50 titles per request
DELAY    = 0.2     # seconds between batches (be polite)

# ── Helpers ────────────────────────────────────────────────────

def strip_accents(s):
    return ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )

def wiki_thumbnails(titles):
    """
    Query Wikipedia pageimages for a list of titles (up to 50).
    Returns dict { normalised_title: thumbnail_url_or_None }
    """
    params = {
        'action':      'query',
        'titles':      '|'.join(titles),
        'prop':        'pageimages',
        'piprop':      'thumbnail',
        'pithumbsize': 120,
        'redirects':   1,
        'format':      'json',
        'formatversion': 2,
    }
    url = WIKI_API + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': 'TFG-FootballSalaries/1.0'})
    with urllib.request.urlopen(req, timeout=10, context=_SSL_CTX) as resp:
        data = json.loads(resp.read())

    result = {}
    pages  = data.get('query', {}).get('pages', [])
    redirects = {r['from']: r['to'] for r in data.get('query', {}).get('redirects', [])}
    normalised = {n['from']: n['to'] for n in data.get('query', {}).get('normalized', [])}

    # Build reverse map: canonical title → original title submitted
    rev = {}
    for orig in titles:
        t = orig
        t = normalised.get(t, t)
        t = redirects.get(t, t)
        rev[t] = orig

    for page in pages:
        if page.get('missing'):
            continue
        thumb = page.get('thumbnail', {}).get('source')
        canonical = page.get('title', '')
        orig = rev.get(canonical, canonical)
        if thumb:
            result[orig] = thumb

    return result


# ── Load players ───────────────────────────────────────────────

eff = pd.read_csv(
    RESULTS / "02_efficiency_scores/01_core_efficiency/efficiency_combined.csv",
    low_memory=False
)
players = sorted(eff['Player'].dropna().unique().tolist())
print(f"Unique players: {len(players)}")

# ── Fetch in batches ───────────────────────────────────────────

photo_map = {}   # player_name → thumbnail_url

# First pass: exact names
batches = [players[i:i+BATCH] for i in range(0, len(players), BATCH)]
not_found = []

for i, batch in enumerate(batches):
    try:
        res = wiki_thumbnails(batch)
        photo_map.update(res)
        found = len(res)
        miss  = len(batch) - found
        not_found.extend([p for p in batch if p not in res])
        print(f"  Batch {i+1}/{len(batches)}: {found} found, {miss} not found")
    except Exception as e:
        print(f"  Batch {i+1} error: {e}")
        not_found.extend(batch)
    time.sleep(DELAY)

print(f"\nFirst pass: {len(photo_map)} photos, {len(not_found)} missing")

# Second pass: try accent-stripped names for missing players
if not_found:
    print("Retrying with accent-stripped names…")
    stripped_map = {}  # stripped_name → original_name
    retry_players = []
    for p in not_found:
        s = strip_accents(p)
        if s != p:
            stripped_map[s] = p
            retry_players.append(s)
        else:
            retry_players.append(p)  # no change, will still fail but included

    retry_batches = [retry_players[i:i+BATCH] for i in range(0, len(retry_players), BATCH)]
    for i, batch in enumerate(retry_batches):
        try:
            res = wiki_thumbnails(batch)
            for stripped, url in res.items():
                orig = stripped_map.get(stripped, stripped)
                if orig not in photo_map:
                    photo_map[orig] = url
            print(f"  Retry batch {i+1}/{len(retry_batches)}: {len(res)} found")
        except Exception as e:
            print(f"  Retry batch {i+1} error: {e}")
        time.sleep(DELAY)

# ── Save ───────────────────────────────────────────────────────

OUT.parent.mkdir(exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(photo_map, f, ensure_ascii=False, separators=(',', ':'))

kb = OUT.stat().st_size / 1024
hit_rate = len(photo_map) / len(players) * 100
print(f"\n✅  photos.json saved ({kb:.0f} KB)")
print(f"   Hit rate: {len(photo_map)}/{len(players)} = {hit_rate:.1f}%")
