"""Échantillon de joueurs pour le prototype, injecté dans index.html (window.GAME_DATA).

L'autocomplétion couvre toute la base ; l'échantillon fixe les joueurs à deviner.
"""
import csv, json, random, re
from collections import defaultdict

TAILLE = {'facile': 70, 'moyen': 70, 'difficile': 90, 'legende': 90}
random.seed(42)
agg = list(csv.DictReader(open('data/joueurs_agrege.csv', encoding='utf-8')))
car = defaultdict(list)
for r in csv.DictReader(open('data/carrieres_nettoyees.csv', encoding='utf-8')):
    car[r['player']].append({'club': r['clubLabel'], 'start': r['start'], 'end': r['end'], 'apps': r['apps'], 'loan': r['pret'] == '1'})
num = lambda x: int(x) if x.isdigit() else None
sample = [r for d, n in TAILLE.items() for r in random.sample([r for r in agg if r['difficulte'] == d], n)]
random.shuffle(sample)
data = {
    'players': [{'id': r['player'], 'name': r['name'], 'key': r['search_key'], 'nat': r['nationalite'],
                 'pos': r['postes'], 'diff': r['difficulte'], 'apps_top5': int(r['apps_top5']),
                 'first': num(r['first_year']), 'last': num(r['last_year']),
                 'leagues': r['championnats'].split(' / ') if r['championnats'] else [],
                 'career': car[r['player']]} for r in sample],
    'names': [{'n': r['name'], 'k': r['search_key']} for r in agg],
}
json.dump(data, open('data/mvp_data.json', 'w', encoding='utf-8'), ensure_ascii=False)
html = open('index.html', encoding='utf-8').read()
new = 'window.GAME_DATA=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';</script>'
html, n = re.subn(r'window\.GAME_DATA=.*?;</script>', lambda m: new, html, count=1, flags=re.S)
assert n == 1, 'marqueur GAME_DATA introuvable'
open('index.html', 'w', encoding='utf-8').write(html)
print(len(data['players']), 'joueurs à deviner,', len(data['names']), 'noms en autocomplétion')
