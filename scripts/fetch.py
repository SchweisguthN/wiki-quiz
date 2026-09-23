"""Lance les requêtes SPARQL de queries/<job>/ sur Wikidata.

Chaque job contient query.rq (avec un marqueur {{VALUES}}) et lots.txt
(un lot de Q-IDs par ligne, lignes '#' ignorées). Sortie : data/raw/<job>/lot_NN.csv.
Les lots déjà récupérés sont sautés ; un lot qui timeoute est coupé en deux.
"""
import csv, io, pathlib, sys, time, urllib.parse, urllib.request

ENDPOINT = "https://query.wikidata.org/sparql"
UA = "IconicCareersBot/1.0 (https://github.com/SchweisguthN/wiki-quiz)"

def run(query):
    data = urllib.parse.urlencode({"query": query}).encode()
    req = urllib.request.Request(ENDPOINT, data=data, headers={"User-Agent": UA, "Accept": "text/csv"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return list(csv.reader(io.StringIO(r.read().decode("utf-8"))))

def fetch(template, ids, depth=0):
    for attempt in range(3):
        try:
            return run(template.replace("{{VALUES}}", " ".join(ids)))
        except Exception as e:
            print(f"{'  '*depth}échec ({len(ids)} ids, essai {attempt+1}) : {e}", flush=True)
            time.sleep(10 * (attempt + 1))
    if len(ids) == 1:
        raise RuntimeError(f"abandon sur {ids[0]}")
    half = len(ids) // 2
    a, b = fetch(template, ids[:half], depth+1), fetch(template, ids[half:], depth+1)
    return a + b[1:]  # une seule ligne d'en-tête

for job in sorted(pathlib.Path("queries").iterdir()):
    template = (job / "query.rq").read_text()
    lots = [l.split() for l in (job / "lots.txt").read_text().splitlines() if l.strip() and not l.startswith("#")]
    out = pathlib.Path("data/raw") / job.name
    out.mkdir(parents=True, exist_ok=True)
    for n, ids in enumerate(lots, 1):
        dest = out / f"lot_{n:02d}.csv"
        if dest.exists():
            continue
        rows = fetch(template, ids)
        with open(dest, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)
        print(f"{job.name} lot {n}/{len(lots)} : {len(rows)-1} lignes", flush=True)
        time.sleep(5)
