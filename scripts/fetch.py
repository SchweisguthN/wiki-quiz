"""Lance les requêtes SPARQL de queries/<job>/ sur Wikidata.

Chaque job contient query.rq (avec un marqueur {{VALUES}}) et lots.txt
(un lot de Q-IDs par ligne, lignes '#' ignorées). Sortie : data/raw/<job>/lot_NN.csv,
commitée et poussée après chaque lot. Les lots déjà présents sont sautés.
Un lot qui timeoute est coupé en deux ; un club qui timeoute seul est noté
dans failed.txt et sauté. Un refus d'accès arrête tout.
"""
import csv, http.client, io, pathlib, subprocess, time, urllib.error, urllib.parse, urllib.request

ENDPOINT = "https://query.wikidata.org/sparql"
UA = "IconicCareersBot/1.0 (https://github.com/SchweisguthN/wiki-quiz)"

def run(query):
    data = urllib.parse.urlencode({"query": query}).encode()
    req = urllib.request.Request(ENDPOINT, data=data, headers={"User-Agent": UA, "Accept": "text/csv"})
    with urllib.request.urlopen(req, timeout=70) as r:
        return list(csv.reader(io.StringIO(r.read().decode("utf-8"))))

def fetch(template, ids):
    for attempt in range(4):
        try:
            return run(template.replace("{{VALUES}}", " ".join(ids)))
        except urllib.error.HTTPError as e:
            if e.code in (403, 400):
                raise SystemExit(f"Refus Wikidata ({e.code}) : {e.read()[:300]!r}")
            if e.code in (429, 503):  # limitation de débit : on attend et on réessaie
                wait = int(e.headers.get("Retry-After") or 30)
                print(f"  {e.code}, pause {wait}s", flush=True); time.sleep(wait); continue
            break  # 500 = timeout côté Wikidata
        except (TimeoutError, http.client.IncompleteRead):  # réponse coupée = timeout
            break
        except OSError as e:  # erreur réseau : on réessaie
            print(f"  réseau : {e}, nouvel essai", flush=True); time.sleep(15)
    if len(ids) == 1:
        print(f"  abandon : {ids[0]} timeoute seul", flush=True)
        FAILED.append(ids[0])
        return None
    print(f"  timeout sur {len(ids)} ids, découpage", flush=True)
    half = len(ids) // 2
    parts = [r for r in (fetch(template, ids[:half]), fetch(template, ids[half:])) if r]
    return parts[0] + [row for p in parts[1:] for row in p[1:]] if parts else None

def push(path, msg):
    subprocess.run(["git", "add", str(path)], check=True)
    subprocess.run(["git", "commit", "-qm", msg], check=True)
    subprocess.run(["git", "pull", "-q", "--rebase", "origin", "main"], check=True)
    subprocess.run(["git", "push", "-q", "origin", "HEAD:main"], check=True)

FAILED = []
for job in sorted(pathlib.Path("queries").iterdir()):
    template = (job / "query.rq").read_text()
    lots = [l.split() for l in (job / "lots.txt").read_text().splitlines() if l.strip() and not l.startswith("#")]
    out = pathlib.Path("data/raw") / job.name
    out.mkdir(parents=True, exist_ok=True)
    for n, ids in enumerate(lots, 1):
        dest = out / f"lot_{n:02d}.csv"
        if dest.exists():
            continue
        t = time.time()
        rows = fetch(template, ids) or [[]]
        with open(dest, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)
        print(f"{job.name} lot {n}/{len(lots)} : {len(rows)-1} lignes en {time.time()-t:.0f}s", flush=True)
        push(dest, f"Collecte {job.name} lot {n}/{len(lots)}")
    if FAILED:
        (out / "failed.txt").write_text("\n".join(FAILED) + "\n")
        push(out / "failed.txt", f"Collecte {job.name} : {len(FAILED)} échecs")
        FAILED.clear()
