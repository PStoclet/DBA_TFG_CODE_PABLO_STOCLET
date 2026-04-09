/**
 * api-shim.js — intercepts /api/* fetch calls on GitHub Pages
 * and serves results from pre-exported static JSON files in docs/data/.
 *
 * Loaded once in <head> of every docs/*.html page.
 * Page JS requires zero changes — all fetch('/api/...') calls are
 * transparently redirected to in-memory data.
 */
(function () {
  'use strict';

  // ── Resolve docs/ base URL from this script's own src ─────
  // Works regardless of whether the HTML page is at docs/ root
  // or a subfolder like docs/pages/.
  const _BASE = (() => {
    const s = document.currentScript;
    if (s && s.src) return s.src.replace(/\/data\/api-shim\.js.*$/, '/');
    return '';
  })();

  // ── Team logo mapping (Transfermarkt IDs) ─────────────────
  const _TM_IDS = {'Arsenal':11, 'Aston Villa':405, 'Brighton':1237, 'Brentford':1246, 'Chelsea':631, 'Crystal Palace':873, 'Everton':29, 'Fulham':931, 'Liverpool':31, 'Manchester City':281, 'Manchester Utd':985, 'Manchester United':985, 'Newcastle Utd':762, 'Newcastle United':762, 'Tottenham':148, 'Tottenham Hotspur':148, 'West Ham':379, 'West Ham United':379, 'Wolves':543, 'Bournemouth':989, 'Nott\'ham Forest':703, 'Nottingham Forest':703, 'Luton Town':1068, 'Sheffield Utd':350, 'Sheffield United':350, 'Burnley':1132, 'Southampton':180, 'Leicester City':1003, 'Leeds United':399, 'Ipswich Town':677, 'Ipswich':677, 'Real Madrid':418, 'Barcelona':131, 'Atlético Madrid':13, 'Atletico Madrid':13, 'Athletic Club':621, 'Villarreal':383, 'Real Sociedad':681, 'Real Betis':150, 'Valencia':1049, 'Celta Vigo':940, 'Sevilla':368, 'Getafe':3709, 'Girona':12321, 'Osasuna':331, 'Rayo Vallecano':366, 'Mallorca':237, 'Almería':16795, 'Almeria':16795, 'Cádiz':5860, 'Cadiz':5860, 'Las Palmas':472, 'Deportivo Alavés':1108, 'Alavés':1108, 'Granada':2835, 'Valladolid':1039, 'Eibar':1444, 'Espanyol':714, 'Leganés':3003, 'Leganes':3003, 'Bayern Munich':27, 'Borussia Dortmund':16, 'Dortmund':16, 'RB Leipzig':23826, 'Bayer Leverkusen':15, 'Leverkusen':15, 'Eintracht Frankfurt':24, 'Frankfurt':24, 'Stuttgart':79, 'Union Berlin':89, 'Wolfsburg':82, 'Borussia M\'gladbach':18, 'Gladbach':18, 'Mönchengladbach':18, 'Freiburg':17, 'Hoffenheim':533, 'Mainz 05':39, 'Mainz':39, 'Werder Bremen':86, 'Augsburg':167, 'Köln':3, 'Koln':3, 'Darmstadt 98':105, 'VfL Bochum':80, 'Bochum':80, 'Heidenheim':2932, 'Schalke 04':33, 'Hertha BSC':44, 'Holstein Kiel':10696, 'St Pauli':35, 'St. Pauli':35, 'FC St. Pauli':35, 'Inter Milan':46, 'Inter':46, 'Juventus':506, 'AC Milan':5, 'Milan':5, 'Napoli':6195, 'Atalanta':800, 'Roma':12, 'Lazio':398, 'Fiorentina':430, 'Bologna':1040, 'Torino':416, 'Udinese':410, 'Genoa':252, 'Sassuolo':6574, 'Cagliari':1390, 'Lecce':1839, 'Empoli':749, 'Hellas Verona':276, 'Verona':276, 'Frosinone':2953, 'Monza':6592, 'Salernitana':380, 'Sampdoria':157, 'Spezia':3522, 'Venezia':907, 'Parma':97, 'Como':17586, 'Paris S-G':583, 'PSG':583, 'Paris Saint-Germain':583, 'Marseille':244, 'Monaco':162, 'Lyon':1041, 'Lens':826, 'Lille':1082, 'Nice':417, 'Rennes':273, 'Lorient':1075, 'Nantes':995, 'Montpellier':969, 'Strasbourg':667, 'Reims':1421, 'Brest':3911, 'Metz':347, 'Toulouse':415, 'Le Havre':738, 'Clermont Foot':17512, 'Auxerre':2488, 'Angers':1054, 'Saint-Étienne':618, 'Saint-Etienne':618};
  function _logoUrl(team) {
    const id = _TM_IDS[team];
    return id ? `${_BASE}images/logos/tm_${id}.png` : '';
  }


  const EFF_THRESHOLD = 0.18;

  // ── Pre-load all data in parallel ──────────────────────────
  const _loaded = Promise.all([
    fetch(_BASE + 'data/efficiency.json').then(r => r.json()),
    fetch(_BASE + 'data/coefficients.json').then(r => r.json()),
    fetch(_BASE + 'data/hypotheses.json').then(r => r.json()),
    fetch(_BASE + 'data/psr_era.json').then(r => r.json()),
    fetch(_BASE + 'data/photos.json').then(r => r.json()).catch(() => ({})),
  ]).then(([eff, coef, hyp, psr, photos]) => {
    // Pre-compute derived fields once
    const seasons = [...new Set(eff.map(r => r.Season).filter(Boolean))].sort();
    const leagues = [...new Set(eff.map(r => r.Comp).filter(Boolean))].sort();
    const latest  = seasons[seasons.length - 1] || null;
    return { eff, coef, hyp, psr, photos, seasons, leagues, latest };
  });

  // ── URL helpers ────────────────────────────────────────────
  function parseApiUrl(urlStr) {
    const [path, qs] = urlStr.split('?');
    const params = new URLSearchParams(qs || '');
    return { path, params };
  }

  // ── Filter efficiency rows by season + leagues ─────────────
  function filterEff(eff, params, seasons, leagues, latest) {
    const seasonParam = params.get('season');
    const season  = (seasonParam && seasonParam !== 'all') ? seasonParam : null;
    const defaultSeason = (!seasonParam) ? latest : null; // no param = use latest; 'all' = no filter
    const activeSeason = season || defaultSeason;
    const lgList  = params.getAll('league').filter(Boolean);
    const useLgs  = lgList.length ? lgList : leagues;
    let data = eff;
    if (activeSeason)  data = data.filter(r => r.Season === activeSeason);
    if (useLgs.length) data = data.filter(r => useLgs.includes(r.Comp));
    return data;
  }

  // ── Aggregation helpers ────────────────────────────────────
  function mean(arr) {
    return arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;
  }
  function median(arr) {
    if (!arr.length) return 0;
    const s = [...arr].sort((a, b) => a - b);
    return s[Math.floor(s.length / 2)];
  }
  function std(arr, m) {
    if (arr.length < 2) return 0;
    const mu = m !== undefined ? m : mean(arr);
    return Math.sqrt(arr.reduce((a, b) => a + (b - mu) ** 2, 0) / (arr.length - 1));
  }
  function classify(s) {
    if (s == null) return 'Unknown';
    return s < -EFF_THRESHOLD ? 'Underpaid' : s > EFF_THRESHOLD ? 'Overpaid' : 'Fairly Paid';
  }

  // ── Route handler ──────────────────────────────────────────
  function handleApi(path, params, { eff, coef, hyp, psr, photos, seasons, leagues, latest }) {

    // /api/meta
    if (path === '/api/meta') {
      return { seasons, leagues, latest };
    }

    // /api/stats
    if (path === '/api/stats') {
      const df = filterEff(eff, params, seasons, leagues, latest);
      const n  = df.length;
      if (!n) return { n: 0 };
      const scores = df.map(r => r.efficiency_score).filter(s => s != null);
      const nOv = df.filter(r => r.efficiency_label === 'Overpaid').length;
      const nUn = df.filter(r => r.efficiency_label === 'Underpaid').length;
      const nFa = df.filter(r => r.efficiency_label === 'Fairly Paid').length;
      const wages = df.map(r => r.Annual_Wages_EUR).filter(w => w != null);
      return {
        total:           n,
        unique_players:  new Set(df.map(r => r.Player)).size,
        leagues:         new Set(df.map(r => r.Comp)).size,
        pct_overpaid:    +((nOv / n * 100).toFixed(1)),
        pct_underpaid:   +((nUn / n * 100).toFixed(1)),
        pct_fairly_paid: +((nFa / n * 100).toFixed(1)),
        mean_eff:        +(mean(scores).toFixed(4)),
        median_wage:     Math.round(median(wages)),
      };
    }

    // /api/efficiency-histogram
    if (path === '/api/efficiency-histogram') {
      const df = filterEff(eff, params, seasons, leagues, latest);
      const scores = df.map(r => r.efficiency_score).filter(s => s != null);
      const result = [];
      for (let b = -3.0; b < 3.01; b = Math.round((b + 0.25) * 100) / 100) {
        const next = Math.round((b + 0.25) * 100) / 100;
        const count = scores.filter(s => s >= b && s < next).length;
        result.push({ bin: +b.toFixed(2), mid: +((b + next) / 2).toFixed(3), count,
                      label: `${b.toFixed(2)} to ${next.toFixed(2)}` });
      }
      return result;
    }

    // /api/league-stats
    if (path === '/api/league-stats') {
      const df = filterEff(eff, params, seasons, leagues, latest);
      const byLeague = {};
      df.forEach(r => {
        if (!r.Comp) return;
        if (!byLeague[r.Comp]) byLeague[r.Comp] = [];
        byLeague[r.Comp].push(r);
      });
      return Object.entries(byLeague).map(([Comp, rows]) => {
        const scores = rows.map(r => r.efficiency_score).filter(s => s != null);
        const m = mean(scores);
        const wages  = rows.map(r => r.Annual_Wages_EUR).filter(w => w != null);
        return {
          Comp,
          mean:         +(m.toFixed(4)),
          std:          +(std(scores, m).toFixed(4)),
          n:            scores.length,
          pct_ov:       +(rows.filter(r => r.efficiency_label === 'Overpaid').length / rows.length * 100).toFixed(1),
          pct_un:       +(rows.filter(r => r.efficiency_label === 'Underpaid').length / rows.length * 100).toFixed(1),
          median_wage:  Math.round(median(wages)),
        };
      });
    }

    // /api/position-league
    if (path === '/api/position-league') {
      const df = filterEff(eff, params, seasons, leagues, latest);
      const grouped = {};
      df.forEach(r => {
        const key = `${r.Comp}||${r.position_group}`;
        if (!grouped[key]) grouped[key] = { league: r.Comp, position: r.position_group, scores: [] };
        if (r.efficiency_score != null) grouped[key].scores.push(r.efficiency_score);
      });
      return Object.values(grouped).map(g => ({
        league: g.league, position: g.position,
        mean: +(mean(g.scores).toFixed(4)),
      }));
    }

    // /api/top-players
    if (path === '/api/top-players') {
      let df = filterEff(eff, params, seasons, leagues, latest);
      const n     = parseInt(params.get('n') || '20');
      const type_ = params.get('type') || 'underpaid';
      const pos   = params.get('position') || 'all';
      if (pos !== 'all') df = df.filter(r => r.position_group === pos);
      let sorted;
      if (type_ === 'underpaid')
        sorted = [...df].sort((a, b) => (a.efficiency_score || 0) - (b.efficiency_score || 0));
      else if (type_ === 'overpaid')
        sorted = [...df].sort((a, b) => (b.efficiency_score || 0) - (a.efficiency_score || 0));
      else
        sorted = [...df].sort((a, b) => Math.abs(a.efficiency_score || 0) - Math.abs(b.efficiency_score || 0));
      return sorted.slice(0, n).map(r => ({ ...r, photo_url: photos[r.Player] || '' }));
    }

    // /api/scatter
    if (path === '/api/scatter') {
      let df = filterEff(eff, params, seasons, leagues, latest);
      const pos = params.get('position') || 'all';
      if (pos !== 'all') df = df.filter(r => r.position_group === pos);
      df = df.filter(r => r.Annual_Wages_EUR != null && r.efficiency_score != null);
      if (df.length > 800) {
        const step = df.length / 800;
        df = Array.from({ length: 800 }, (_, i) => df[Math.floor(i * step)]);
      }
      return df.map(r => ({
        Player: r.Player, Team: r.Team, Comp: r.Comp,
        position_group: r.position_group, Annual_Wages_EUR: r.Annual_Wages_EUR,
        efficiency_score: r.efficiency_score, efficiency_label: r.efficiency_label,
      }));
    }

    // /api/squads
    if (path === '/api/squads') {
      const df = filterEff(eff, params, seasons, leagues, latest);
      const byTeam = {};
      df.forEach(r => {
        const key = `${r.Team}||${r.Comp}`;
        if (!byTeam[key]) byTeam[key] = { Team: r.Team, Comp: r.Comp, rows: [] };
        byTeam[key].rows.push(r);
      });
      const result = Object.values(byTeam).map(g => {
        const rows   = g.rows;
        const n      = rows.length;
        const scores = rows.map(r => r.efficiency_score).filter(s => s != null);
        const wages  = rows.map(r => r.Annual_Wages_EUR).filter(w => w != null);
        const total  = wages.reduce((a, b) => a + b, 0);
        return {
          Team: g.Team, Comp: g.Comp,
          mean_eff:    +(mean(scores).toFixed(4)),
          median_eff:  +(median(scores).toFixed(4)),
          n,
          pct_ov:      +(rows.filter(r => r.efficiency_label === 'Overpaid').length / n * 100).toFixed(1),
          pct_un:      +(rows.filter(r => r.efficiency_label === 'Underpaid').length / n * 100).toFixed(1),
          pct_fair:    +(rows.filter(r => r.efficiency_label === 'Fairly Paid').length / n * 100).toFixed(1),
          total_wages: Math.round(total),
          mean_wage:   Math.round(wages.length ? total / wages.length : 0),
          rank_eff:    0,
          logo_url:    _logoUrl(g.Team),
        };
      });
      // rank by mean_eff
      const sorted = [...result].sort((a, b) => a.mean_eff - b.mean_eff);
      sorted.forEach((r, i) => { r.rank_eff = i + 1; });
      return result;
    }

    // /api/squad-detail
    if (path === '/api/squad-detail') {
      let df = filterEff(eff, params, seasons, leagues, latest);
      const team = params.get('team') || '';
      df = df.filter(r => r.Team === team);
      return df
        .sort((a, b) => (a.efficiency_score || 0) - (b.efficiency_score || 0))
        .map(r => ({
          ...r,
          efficiency_label: classify(r.efficiency_score),
          photo_url: photos[r.Player] || '',
        }));
    }

    // /api/squad-health
    if (path === '/api/squad-health') {
      return [];
    }

    // /api/formation-xi
    if (path === '/api/formation-xi') {
      let df = filterEff(eff, params, seasons, leagues, latest);
      if (!df.length) df = eff; // fallback to full dataset
      const xi_type = params.get('type') || 'underpaid';
      const slots = [
        { pos: 'Goalkeepers', abbr: 'GK',  count: 1 },
        { pos: 'Defenders',   abbr: 'DEF', count: 4 },
        { pos: 'Midfielders', abbr: 'MID', count: 4 },
        { pos: 'Forwards',    abbr: 'FWD', count: 2 },
      ];
      const xi = [];
      slots.forEach(s => {
        let group = df.filter(r => r.position_group === s.pos);
        if (!group.length) group = eff.filter(r => r.position_group === s.pos);
        const sorted = [...group].sort((a, b) =>
          xi_type === 'underpaid'
            ? (a.efficiency_score || 0) - (b.efficiency_score || 0)
            : (b.efficiency_score || 0) - (a.efficiency_score || 0)
        );
        sorted.slice(0, s.count).forEach((r, i) => {
          xi.push({
            player:     r.Player,
            team:       r.Team,
            league:     r.Comp,
            position:   s.pos,
            abbr:       s.abbr,
            efficiency: +(r.efficiency_score || 0).toFixed(2),
            eff_pct:    +(r.efficiency_pct || 0).toFixed(1),
            wage:       Math.round(r.Annual_Wages_EUR || 0),
            slot:       i,
            photo_url:  photos[r.Player] || '',
          });
        });
      });
      return xi;
    }



    // /api/team-logo  — serve pre-downloaded local image
    if (path === '/api/team-logo') {
      const team = params.get('team') || '';
      return { logo_url: _logoUrl(team) };
    }

    // /api/photo  — look up Wikipedia thumbnail from photos.json
    if (path === '/api/photo') {
      const player = params.get('player') || '';
      return { photo_url: photos[player] || '' };
    }

    // /api/coefficients
    if (path === '/api/coefficients') {
      const pos = params.get('position');
      return pos ? coef.filter(r => r.model === pos) : coef;
    }

    // /api/model-summaries
    if (path === '/api/model-summaries') {
      return [
        { position: 'Defenders',   r2: 0.713, rmse: 0.42, n: 2250, f_stat: null },
        { position: 'Midfielders', r2: 0.692, rmse: 0.45, n: 3005, f_stat: null },
        { position: 'Forwards',    r2: 0.690, rmse: 0.47, n: 925,  f_stat: null },
        { position: 'Goalkeepers', r2: 0.634, rmse: 0.51, n: 526,  f_stat: null },
      ];
    }

    // /api/hypotheses
    if (path === '/api/hypotheses') {
      return hyp;
    }

    // /api/psr-era
    if (path === '/api/psr-era') {
      return psr;
    }

    return null; // unhandled — fall through to real fetch
  }

  // ── Intercept window.fetch ─────────────────────────────────
  const _origFetch = window.fetch.bind(window);
  window.fetch = function (url, opts) {
    const urlStr = typeof url === 'string' ? url
      : (url instanceof URL ? url.toString()
        : (url && url.url ? url.url : String(url)));

    if (urlStr.startsWith('/api/')) {
      const { path, params } = parseApiUrl(urlStr);
      return _loaded.then(data => {
        const result = handleApi(path, params, data);
        if (result !== null) {
          return new Response(JSON.stringify(result), {
            status:  200,
            headers: { 'Content-Type': 'application/json' },
          });
        }
        return _origFetch(url, opts);
      });
    }

    return _origFetch(url, opts);
  };

  // ── Patch <img src="/api/team-logo?..."> in the DOM ───────
  // fetch() interception can't catch img src attribute loads,
  // so we use a MutationObserver to swap them for local paths.
  function _patchLogoImg(img) {
    const src = img.getAttribute('src') || '';
    if (!src.startsWith('/api/team-logo')) return;
    const params = new URLSearchParams(src.split('?')[1] || '');
    const team = decodeURIComponent(params.get('team') || '');
    const id = _TM_IDS[team];
    if (id) img.src = `images/logos/tm_${id}.png`;
  }

  function _patchSubtree(root) {
    const imgs = root.tagName === 'IMG' ? [root] : root.querySelectorAll('img[src^="/api/team-logo"]');
    imgs.forEach(_patchLogoImg);
  }

  // Patch on DOMContentLoaded (for any static imgs)
  document.addEventListener('DOMContentLoaded', () => _patchSubtree(document.body));

  // Patch dynamically inserted nodes
  new MutationObserver(mutations => {
    mutations.forEach(m => {
      m.addedNodes.forEach(node => {
        if (node.nodeType !== 1) return;
        _patchSubtree(node);
      });
    });
  }).observe(document.documentElement, { childList: true, subtree: true });

})();
