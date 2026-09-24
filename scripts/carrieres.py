"""Construit data/carrieres_nettoyees.csv.

Source principale : l'infobox Wikipédia (anglais) du joueur, clubs pros seulement
(les clubs de formation sont écartés), avec les prêts qu'elle signale.
Secours : data/carrieres_wikidata.csv, avec les prêts déduits des dates.
"""
import csv, glob, json, re, sys
from collections import defaultdict
sys.path.insert(0, 'scripts')
from infobox import fields, links

W = 'data/raw/wiki_complet/'
titres = json.load(open(W + 'titres.json'))
infobox = {k: v for f in sorted(glob.glob(W + 'infobox_*.json')) for k, v in json.load(open(f)).items()}
club_q = json.load(open(W + 'clubs.json'))

wikidata, noms, libelle = defaultdict(list), {}, {}
for r in csv.DictReader(open('data/carrieres_wikidata.csv', encoding='utf-8')):
    wikidata[r['player']].append(r); noms[r['player']] = r['name']; libelle.setdefault(r['club'], r['clubLabel'])
for f in glob.glob('data/raw/libelles_clubs/lot_*.csv'):          # libellés français des clubs absents de Wikidata
    for r in csv.DictReader(open(f, encoding='utf-8')):
        if r.get('club'): libelle.setdefault(r['club'].rsplit('/', 1)[-1], r['label'])

def annees(v):
    y = [int(x) for x in re.findall(r'(?:19|20)\d\d', v)]
    if not y: return None, None
    ouvert = re.search(r'[–—-]\s*$', re.sub(r'\{\{[^}]*\}\}', '', v).strip())
    return y[0], (y[1] if len(y) > 1 else None if ouvert else y[0])

def depuis_infobox(f):
    rows = []
    for k in sorted((k for k in f if re.fullmatch(r'clubs\d+', k)), key=lambda k: int(k[5:])):
        n, v = k[5:], f[k]
        l = links(v)
        if not l: continue
        titre = l[0].replace('_', ' '); titre = titre[:1].upper() + titre[1:]
        a, b = annees(f.get('years' + n, ''))
        if a is None: continue
        caps = re.search(r'\d+', re.sub(r'\{\{0+\}\}', '', f.get('caps' + n, '')))
        q = club_q.get(titre, '')
        rows.append((q, libelle.get(q) or titre, caps.group() if caps else '', a, b or '',
                     int('→' in v or '(loan)' in v.lower())))
    return rows

RESERVE = re.compile(r"\bB\b|\bII\b| B$|réserve|reserve|amateurs?$|U-?\d+", re.I)
def prets_deduits(rows):
    """Passage strictement inclus dans un autre (hors équipes réserve) = prêt."""
    out = []
    for i, (q, l, apps, a, b) in enumerate(rows):
        pret = 0
        if a != '' and b != '':
            for j, (q2, l2, _, a2, b2) in enumerate(rows):
                if i != j and q2 != q and a2 != '' and b2 != '' and a2 < a and b < b2:
                    base = RESERVE.sub('', l).strip()
                    if not (RESERVE.search(l) and base and base in l2):
                        pret = 1; break
        out.append((q, l, apps, a, b, pret))
    return out

out, source = [], {'wikipedia': 0, 'wikidata': 0}
for p in noms:
    rows = depuis_infobox(fields(infobox.get(titres.get(p), '')))
    src = 'wikipedia'
    if not rows:
        src = 'wikidata'
        rows = prets_deduits([(r['club'], r['clubLabel'], r['apps'], int(r['start']) if r['start'] else '',
                               int(r['end']) if r['end'] else '') for r in wikidata[p]])
    source[src] += 1
    for q, l, apps, a, b, pret in rows:
        out.append([p, noms[p], q, l, apps, a, b, pret, src])

with open('data/carrieres_nettoyees.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['player', 'name', 'club', 'clubLabel', 'apps', 'start', 'end', 'pret', 'source']); w.writerows(out)
sans = sorted({q for r in out for q in [r[2]] if q and q not in libelle})
print(f"{len(out)} passages ; joueurs par source : {source} ; clubs sans libellé français : {len(sans)}")
open('data/raw/clubs_sans_libelle.txt', 'w').write('\n'.join(sans) + '\n')
