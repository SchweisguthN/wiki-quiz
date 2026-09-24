"""Données du site : un index léger injecté dans index.html, et les carrières
réparties en tranches chargées à la demande (careers/<n>.json).

window.GAME_DATA :
  players : [id, nom, clé, alias, niveau, championnats, 1re année, dernière année] des joueurs jouables
  others  : [nom, clé, alias] des joueurs hors jeu, pour l'autocomplétion
  shards  : nombre de tranches ; un joueur Qn est dans careers/<n % shards>.json
careers/<t>.json : {Q-ID: [nationalité, poste, [[club, début, fin, matchs, prêt], ...]]}
"""
import csv, json, pathlib, re
from collections import defaultdict

TRANCHES = 512
num = lambda x: int(x) if x.isdigit() else None
agg = list(csv.DictReader(open('data/joueurs_agrege.csv', encoding='utf-8')))
jouables = [r for r in agg if r['difficulte'] != 'exclu']
ids = {r['player'] for r in jouables}

careers = defaultdict(list)
for r in csv.DictReader(open('data/carrieres_nettoyees.csv', encoding='utf-8')):
    if r['player'] in ids:
        careers[r['player']].append([r['clubLabel'], num(r['start']), num(r['end']), num(r['apps']), int(r['pret'] == '1')])

tranches = defaultdict(dict)
for r in jouables:
    tranches[int(r['player'][1:]) % TRANCHES][r['player']] = [r['nationalite'], r['postes'], careers[r['player']]]
out = pathlib.Path('careers')
out.mkdir(exist_ok=True)
for f in out.glob('*.json'):
    f.unlink()
for t, d in tranches.items():
    (out / f'{t}.json').write_text(json.dumps(d, ensure_ascii=False, separators=(',', ':')))

data = {
    'players': [[r['player'], r['name'], r['search_key'], r['search_alias'], r['difficulte'],
                 r['championnats'].split(' / ') if r['championnats'] else [], num(r['first_year']), num(r['last_year'])]
                for r in jouables],
    'others': [[r['name'], r['search_key'], r['search_alias']] for r in agg if r['player'] not in ids],
    'shards': TRANCHES,
}
html = open('index.html', encoding='utf-8').read()
new = 'window.GAME_DATA=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';</script>'
html, n = re.subn(r'window\.GAME_DATA=.*?;</script>', lambda m: new, html, count=1, flags=re.S)
assert n == 1, 'marqueur GAME_DATA introuvable'
open('index.html', 'w', encoding='utf-8').write(html)
tailles = [f.stat().st_size for f in out.glob('*.json')]
print(f"{len(jouables)} joueurs jouables, {len(data['others'])} autres noms ; index {len(new) // 1024} Ko ; "
      f"{len(tailles)} tranches de {min(tailles) // 1024}-{max(tailles) // 1024} Ko (moy. {sum(tailles) // len(tailles) // 1024} Ko)")
