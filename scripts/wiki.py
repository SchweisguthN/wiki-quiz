"""Récupère les infobox Wikipédia (anglais) des joueurs listés dans wiki/<job>/joueurs.txt.

Sorties dans data/raw/wiki_<job>/ :
  titres.json    Q-ID joueur -> titre de la page en.wikipedia (via Wikidata)
  infobox_NN.json titre -> texte de l'infobox, par tranches de 1000 pages
  clubs.json     titre de page de club -> Q-ID Wikidata (liens trouvés dans les infobox)
Un fichier déjà présent n'est pas recollecté.
"""
import json, pathlib, re, sys, time, urllib.parse, urllib.request
sys.path.insert(0, "scripts")
from infobox import fields, raw, links as infobox_links

UA = "IconicCareersBot/1.0 (https://github.com/SchweisguthN/wiki-quiz; n.schweisguth+claude@gmail.com)"
WD = "https://www.wikidata.org/w/api.php"
EN = "https://en.wikipedia.org/w/api.php"

def api(url, **params):
    params.update(format="json", formatversion=2)
    req = urllib.request.Request(url + "?" + urllib.parse.urlencode(params), headers={"User-Agent": UA})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.load(r)
            if "error" in data:
                print(f"  erreur API : {data['error']}", flush=True); time.sleep(10 * (attempt + 1)); continue
            return data
        except OSError as e:
            print(f"  erreur réseau ({e}), nouvel essai", flush=True); time.sleep(10 * (attempt + 1))
    raise SystemExit(f"abandon : {url} {params}")

def batches(items, n=50):
    items = list(items)
    for i in range(0, len(items), n):
        yield items[i:i + n]

def step(path, build):
    if path.exists():
        return json.loads(path.read_text())
    data = build()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=0))
    print(f"{path} : {len(data)} entrées", flush=True)
    return data

def resolve(d, t):
    """Titre final d'une page après normalisation et redirection."""
    alias = {r["from"]: r["to"] for r in d.get("redirects", []) + d.get("normalized", [])}
    return alias.get(alias.get(t, t), alias.get(t, t))

def titles(ids):
    out = {}
    for b in batches(ids):
        for qid, e in api(WD, action="wbgetentities", ids="|".join(b), props="sitelinks", sitefilter="enwiki")["entities"].items():
            if "enwiki" in e.get("sitelinks", {}):
                out[qid] = e["sitelinks"]["enwiki"]["title"]
        time.sleep(1)
    return out

def wikitexts(pages):
    out = {}
    for b in batches(pages):
        d = api(EN, action="query", prop="revisions", rvprop="content", rvslots="main", redirects=1, titles="|".join(b))["query"]
        text = {p["title"]: p["revisions"][0]["slots"]["main"]["content"] for p in d["pages"] if "revisions" in p}
        for t in b:
            if resolve(d, t) in text:
                out[t] = raw(text[resolve(d, t)])
        time.sleep(1)
    return out

def club_qids(texts):
    links = {l.replace("_", " ") for t in texts.values() for k, v in fields(t).items()
             if re.fullmatch(r"(youth)?clubs\d+", k) for l in infobox_links(v)}
    links = {l[0].upper() + l[1:] for l in links if l}
    out = {}
    for b in batches(sorted(links)):
        d = api(EN, action="query", prop="pageprops", ppprop="wikibase_item", redirects=1, titles="|".join(b))["query"]
        qid = {p["title"]: p.get("pageprops", {}).get("wikibase_item") for p in d["pages"]}
        for t in b:
            if qid.get(resolve(d, t)):
                out[t] = qid[resolve(d, t)]
        time.sleep(1)
    return out

for job in sorted(pathlib.Path("wiki").iterdir()):
    ids = [l.strip() for l in (job / "joueurs.txt").read_text().splitlines() if l.strip()]
    out = pathlib.Path("data/raw") / f"wiki_{job.name}"
    out.mkdir(parents=True, exist_ok=True)
    t = step(out / "titres.json", lambda: titles(ids))
    pages = sorted(set(t.values()))
    w = {}
    for n in range(0, len(pages), 1000):
        w.update(step(out / f"infobox_{n // 1000:02d}.json", lambda: wikitexts(pages[n:n + 1000])))
    step(out / "clubs.json", lambda: club_qids(w))
