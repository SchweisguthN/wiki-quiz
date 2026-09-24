"""Matchs joués dans les 5 grands championnats, évalués à l'époque de chaque passage.

Un passage (club, début, fin) compte pour les saisons où son club figure dans
data/clubs_saisons_top5.csv ; ses matchs sont proratisés selon la part de ces saisons.
"""
import csv, glob
from collections import defaultdict

q = lambda u: u.rsplit('/', 1)[-1]

def load_ref(path='data/clubs_saisons_top5.csv'):
    ref = defaultdict(dict)  # club -> {année de début de saison: ligue}
    for r in csv.DictReader(open(path, encoding='utf-8')):
        ref[r['club']][int(r['season_start'])] = r['league']
    return ref

def load_stints(pattern='data/raw/selection/lot_*.csv'):
    rows = set()
    for f in sorted(glob.glob(pattern)):
        for r in csv.DictReader(open(f, encoding='utf-8')):
            if r.get('player'):
                rows.add((q(r['player']), q(r['club']), r['apps'], (r['start'] or '')[:4], (r.get('end') or '')[:4]))
    return rows

def top5_share(ref, club, apps, start, end):
    """(matchs top 5, ligues) pour un passage, ou None s'il ne touche aucune saison top 5."""
    try: apps = float(apps)
    except (TypeError, ValueError): return None
    if not start.isdigit(): return None
    a = int(start); b = int(end) if end.isdigit() else 2027
    seasons = {y: 1.0 for y in range(a, b)} if b > a else {a - 1: .5, a: .5}  # une seule année civile : ambigu
    hit = {y: w for y, w in seasons.items() if y in ref[club]}
    if not hit: return None
    return min(apps, 45 * len(seasons)) * sum(hit.values()) / sum(seasons.values()), {ref[club][y] for y in hit}
