"""
Fetch Transfermarkt player IDs for every player in efficiency_combined.csv.
Saves docs/data/photos.json — { "Player Name": "https://img.a.transfermarkt.technology/portrait/medium/{id}.jpg" }

Run from project root:  python scripts/fetch_tm_player_ids.py
Progress is saved incrementally — safe to interrupt and resume.
"""
import json, re, ssl, time, unicodedata
import urllib.request, urllib.parse
from pathlib import Path

import pandas as pd

ROOT    = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "data" / "results"
OUT     = ROOT / "docs" / "data" / "photos.json"
CACHE   = ROOT / "docs" / "data" / "_tm_id_cache.json"   # interim progress file

PHOTO_BASE = "https://img.a.transfermarkt.technology/portrait/medium/{id}.jpg"
SEARCH_URL = "https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche"
DELAY      = 0.4   # seconds between requests

HEADERS = {
    'User-Agent':      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept':          'text/html,application/xhtml+xml',
    'Referer':         'https://www.transfermarkt.com/',
}

# SSL context (macOS cert fix)
try:
    import certifi
    _CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _CTX = ssl._create_unverified_context()

# Regex to extract the first player ID from TM search results
_PLAYER_ID_RE = re.compile(r'/[^/]+/profil/spieler/(\d+)')


def tm_search_id(name: str) -> str | None:
    """Search TM for `name`, return the first player's TM numeric ID or None."""
    params = urllib.parse.urlencode({'query': name, 'Spieler_page': '1'})
    url = f"{SEARCH_URL}?{params}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=12, context=_CTX) as resp:
            html = resp.read().decode('utf-8', errors='replace')
    except Exception:
        return None

    # Find the *first* occurrence of /profil/spieler/{id}
    m = _PLAYER_ID_RE.search(html)
    return m.group(1) if m else None


def strip_accents(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')


# ── Load players ────────────────────────────────────────────────────────────

eff = pd.read_csv(
    RESULTS / "02_efficiency_scores/01_core_efficiency/efficiency_combined.csv",
    low_memory=False,
)
all_players = sorted(eff['Player'].dropna().unique().tolist())
print(f"Unique players: {len(all_players)}")

# ── Load existing cache to resume if interrupted ─────────────────────────────

cache: dict[str, str | None] = {}
if CACHE.exists():
    with open(CACHE) as f:
        cache = json.load(f)
    print(f"Resuming from cache: {len(cache)} already processed")

# ── Fetch TM IDs ─────────────────────────────────────────────────────────────

total = len(all_players)
found = sum(1 for v in cache.values() if v)

for i, player in enumerate(all_players):
    if player in cache:
        continue   # already fetched

    tm_id = tm_search_id(player)
    if tm_id is None:
        # Retry once with accent-stripped name
        stripped = strip_accents(player)
        if stripped != player:
            tm_id = tm_search_id(stripped)

    cache[player] = tm_id
    if tm_id:
        found += 1

    # Save incrementally every 50 players
    if (i + 1) % 50 == 0:
        with open(CACHE, 'w') as f:
            json.dump(cache, f, ensure_ascii=False, separators=(',', ':'))
        print(f"  [{i+1}/{total}] found so far: {found}")

    time.sleep(DELAY)

# Final cache save
with open(CACHE, 'w') as f:
    json.dump(cache, f, ensure_ascii=False, separators=(',', ':'))

# ── Build photos.json from IDs ────────────────────────────────────────────────

photo_map: dict[str, str] = {}
for player, tm_id in cache.items():
    if tm_id:
        photo_map[player] = PHOTO_BASE.format(id=tm_id)

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(photo_map, f, ensure_ascii=False, separators=(',', ':'))

kb  = OUT.stat().st_size / 1024
hit = len(photo_map) / len(all_players) * 100
print(f"\n✅  photos.json saved ({kb:.0f} KB)")
print(f"   Hit rate: {len(photo_map)}/{len(all_players)} = {hit:.1f}%")
print(f"\nYou can delete docs/data/_tm_id_cache.json if no longer needed.")
