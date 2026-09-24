"""Lecture de l'infobox « Infobox football biography » de Wikipédia (anglais)."""
import re

def fields(text):
    """Champs de l'infobox : {nom: valeur brute}."""
    m = re.search(r"\{\{\s*Infobox football biography", text, re.I)
    if not m:
        return {}
    i, depth = m.start(), 0
    for j in range(i, len(text) - 1):          # fin de l'infobox : accolades équilibrées
        pair = text[j:j + 2]
        depth += (pair == "{{") - (pair == "}}")
        if depth == 0:
            body = text[i + 2:j]; break
    else:
        body = text[i + 2:]
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    body = re.sub(r"<ref[^>/]*/>|<ref[^>]*>.*?</ref>", "", body, flags=re.S)
    body = re.sub(r"\[\[([^\]|]+)\|[^\]]*\]\]", r"[[\1]]", body)   # [[Page|texte]] -> [[Page]]
    out, depth, cur = {}, 0, ""
    parts = []
    for ch_i, ch in enumerate(body):               # découpe sur les | de premier niveau
        two = body[ch_i:ch_i + 2]
        if two in ("{{", "[["): depth += 1
        if two in ("}}", "]]"): depth -= 1
        if ch == "|" and depth <= 1:
            parts.append(cur); cur = ""
        else:
            cur += ch
    parts.append(cur)
    for p in parts[1:]:
        if "=" in p:
            k, v = p.split("=", 1)
            out[k.strip().lower()] = v.strip()
    return out

def links(value):
    return [l.strip() for l in re.findall(r"\[\[([^\]#]+)", value)]
