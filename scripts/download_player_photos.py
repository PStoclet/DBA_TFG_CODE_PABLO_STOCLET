"""
Download Transfermarkt player photos locally.
Extracts player IDs from existing photos.json, fetches each player's TM
profile page to get the correct image URL (TM now uses {id}-{timestamp}.jpg),
downloads the image, and rewrites photos.json with relative paths.

Run from project root:  python scripts/download_player_photos.py
Safe to interrupt and resume — already-downloaded files are skipped.
"""
import json, re, ssl, time, unicodedata
import urllib.request
from pathlib import Path

ROOT    = Path(__file__).resolve().parents[1]
PHOTOS  = ROOT / "docs" / "data" / "photos.json"
OUT     = ROOT / "docs" / "images" / "player_photos"
CACHE   = ROOT / "docs" / "data" / "_photo_url_cache.json"
DELAY   = 0.35

HEADERS = {
    'User-Agent':      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept':          'text/html,application/xhtml+xml,image/avif,image/webp,*/*;q=0.8',
    'Referer':         'https://www.transfermarkt.com/',
}
IMG_HEADERS = {**HEADERS, 'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8'}

try:
    import certifi
    _CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _CTX = ssl._create_unverified_context()

# Regex to find the medium portrait URL in TM profile HTML
_IMG_RE = re.compile(r'portrait/medium/(\d+-\d+\.jpg)')

def slugify(name: str) -> str:
    s = unicodedata.normalize('NFD', name)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = re.sub(r'[^a-zA-Z0-9 ]', '', s).strip()
    s = re.sub(r'\s+', '_', s).lower()
    return s or 'unknown'

def fetch_real_img_url(player_id: str, player_slug: str = 'player') -> str | None:
    """Fetch TM profile page, extract current portrait/medium URL."""
    url = f"https://www.transfermarkt.com/{player_slug}/profil/spieler/{player_id}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=12, context=_CTX) as resp:
            html = resp.read().decode('utf-8', errors='replace')
    except Exception:
        return None
    m = _IMG_RE.search(html)
    if m:
        return f"https://img.a.transfermarkt.technology/portrait/medium/{m.group(1)}"
    return None

def download_img(url: str) -> bytes | None:
    req = urllib.request.Request(url, headers=IMG_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=12, context=_CTX) as resp:
            data = resp.read()
        return data if len(data) > 2000 else None
    except Exception:
        return None

OUT.mkdir(parents=True, exist_ok=True)

# Load existing photos.json — extract player→id mapping from old URLs
with open(PHOTOS, encoding='utf-8') as f:
    old_map: dict[str, str] = json.load(f)

_ID_FROM_URL = re.compile(r'/portrait/medium/(\d+)(?:-\d+)?\.jpg')
player_ids: dict[str, str] = {}
for player, url in old_map.items():
    m = _ID_FROM_URL.search(url)
    if m:
        player_ids[player] = m.group(1)

print(f"Players with IDs: {len(player_ids)}")

# Load cache of resolved real image URLs (to resume safely)
url_cache: dict[str, str | None] = {}
if CACHE.exists():
    with open(CACHE) as f:
        url_cache = json.load(f)
    print(f"Resuming: {len(url_cache)} URLs already resolved")

total   = len(player_ids)
done    = 0
skipped = 0
failed  = 0
local_map: dict[str, str] = {}

for i, (player, tm_id) in enumerate(player_ids.items()):
    slug     = slugify(player)
    filename = f"{slug}.jpg"
    dest     = OUT / filename
    local_rel = f"images/player_photos/{filename}"

    # Already downloaded locally — just record path
    if dest.exists() and dest.stat().st_size > 2000:
        local_map[player] = local_rel
        skipped += 1
        continue

    # Get real image URL (with timestamp)
    if player not in url_cache:
        real_url = fetch_real_img_url(tm_id, slug.replace('_', '-'))
        url_cache[player] = real_url
        time.sleep(DELAY)
    else:
        real_url = url_cache[player]

    if not real_url:
        failed += 1
        # Keep old TM URL as fallback (may still work in browsers via no-referrer)
        local_map[player] = old_map.get(player, '')
        continue

    # Download image
    data = download_img(real_url)
    if data:
        with open(dest, 'wb') as f:
            f.write(data)
        local_map[player] = local_rel
        done += 1
        time.sleep(DELAY * 0.7)
    else:
        local_map[player] = old_map.get(player, '')
        failed += 1

    # Save cache + progress every 50
    if (i + 1) % 50 == 0:
        with open(CACHE, 'w') as f:
            json.dump(url_cache, f, ensure_ascii=False, separators=(',', ':'))
        print(f"  [{i+1}/{total}] downloaded:{done}  skipped:{skipped}  failed:{failed}")

# Final cache save
with open(CACHE, 'w') as f:
    json.dump(url_cache, f, ensure_ascii=False, separators=(',', ':'))

# Rewrite photos.json with local paths (fallback to old URL for failures)
with open(PHOTOS, 'w', encoding='utf-8') as f:
    json.dump(local_map, f, ensure_ascii=False, separators=(',', ':'))

disk_mb = sum(p.stat().st_size for p in OUT.glob('*.jpg')) / 1024 / 1024
print(f"\n✅  Done: {done} downloaded, {skipped} already existed, {failed} failed")
print(f"   Disk: {disk_mb:.1f} MB in docs/images/player_photos/")
print(f"   photos.json updated with local paths")
