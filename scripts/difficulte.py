"""Recalcule la difficulté dans data/joueurs_agrege.csv.

score = pages Wikipédia + matchs top 5 / 10 + matchs dans un grand club / 5
Facile : 60 pages ou plus. Sinon (10 matchs top 5 minimum) :
Moyen si score >= 75, Difficile si score >= 42, Légende en dessous.
"""
import csv, sys
from collections import defaultdict
sys.path.insert(0, 'scripts')
from top5 import load_ref, load_stints, top5_share

GRANDS_CLUBS = {  # visibilité européenne depuis 2000
    'Q18656', 'Q1130849', 'Q9617', 'Q9616', 'Q50602', 'Q18741',          # PL : Man Utd, Liverpool, Arsenal, Chelsea, Man City, Tottenham
    'Q8682', 'Q7156', 'Q8701', 'Q10333', 'Q10329',                       # Liga : Real, Barça, Atlético, Valence, Séville
    'Q1422', 'Q631', 'Q1543', 'Q2739', 'Q2609', 'Q2641',                 # Serie A : Juve, Inter, Milan, Rome, Lazio, Naples
    'Q15789', 'Q41420', 'Q104761', 'Q32494', 'Q702455',                  # Bundesliga : Bayern, Dortmund, Leverkusen, Schalke, Leipzig
    'Q483020', 'Q132885', 'Q704', 'Q180305', 'Q172476', 'Q19516',        # L1 : PSG, OM, OL, Monaco, Bordeaux, Lille
}
SEUIL_FACILE, SEUIL_MOYEN, SEUIL_DIFFICILE = 60, 75, 42

ref = load_ref()
grand = defaultdict(float)
for p, c, apps, a, b in load_stints():
    if c in GRANDS_CLUBS and (s := top5_share(ref, c, apps, a, b)):
        grand[p] += s[0]

path = 'data/joueurs_agrege.csv'
rows = list(csv.DictReader(open(path, encoding='utf-8')))
for r in rows:
    pages, top5, g = int(r['sitelinks'] or 0), int(r['apps_top5']), round(grand[r['player']])
    score = pages + top5 / 10 + g / 5
    r['matchs_grands_clubs'], r['score'] = g, round(score)
    r['difficulte'] = ('facile' if pages >= SEUIL_FACILE else 'exclu' if top5 < 10 else
                       'moyen' if score >= SEUIL_MOYEN else 'difficile' if score >= SEUIL_DIFFICILE else 'legende')
fields = [k for k in rows[0] if k not in ('matchs_grands_clubs', 'score', 'difficulte')] + ['matchs_grands_clubs', 'score', 'difficulte']
with open(path, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
from collections import Counter
print(Counter(r['difficulte'] for r in rows))
