"""Remplace le nom d'un joueur par le titre de sa page Wikipédia quand ce titre en est
une version courte : moins de mots, tous présents dans le nom (accents ignorés).
Retire ainsi les prénoms en trop (« Jeremy Henoc Pied » -> « Jérémy Pied »)
sans remplacer un nom français par sa transcription anglaise.
Met à jour name et search_key dans data/joueurs_agrege.csv, et garde la clé de
l'ancien nom complet dans search_alias pour que la recherche le trouve encore.
"""
import csv, json, re, unicodedata

MAP = {'ı': 'i', 'ø': 'o', 'Ø': 'o', 'ł': 'l', 'Ł': 'l', 'ß': 'ss', 'ð': 'd', 'đ': 'd', 'Đ': 'd', 'æ': 'ae', 'Æ': 'ae', 'œ': 'oe', 'Œ': 'oe'}

def key(n):
    """Clé de recherche, identique à norm() dans index.html."""
    s = ''.join(MAP.get(c, c) for c in n.lower())
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    s = re.sub(r"['’\-.]", '', s)
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z ]', ' ', s)).strip()

titres = json.load(open('data/raw/wiki_complet/titres.json'))
path = 'data/joueurs_agrege.csv'
rows = list(csv.DictReader(open(path, encoding='utf-8')))
changes = []
for r in rows:
    t = re.sub(r'\s*\([^)]*\)', '', titres.get(r['player'], '')).strip()
    mots_t, mots_n = key(t).split(), key(r['name']).split()
    if t and len(mots_t) < len(mots_n) and set(mots_t) <= set(mots_n):
        changes.append((r['name'], t))
        r['search_alias'] = r.get('search_alias') or key(r['name'])
        r['name'], r['search_key'] = t, key(t)
with open(path, 'w', newline='', encoding='utf-8') as f:
    fields = list(rows[0]) + ([] if 'search_alias' in rows[0] else ['search_alias'])
    w = csv.DictWriter(f, fieldnames=fields, restval=''); w.writeheader(); w.writerows(rows)
print(len(changes), 'noms raccourcis')
for a, b in changes[:40]: print(f'  {a}  ->  {b}')
