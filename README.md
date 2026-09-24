# Iconic Careers

Jeu où l'on devine un footballeur à partir de sa carrière en club. On affiche
le parcours d'un joueur (clubs, périodes, matchs joués) et il
faut retrouver son nom.

## Contenu du dépôt

```
iconic-careers/
├── data/
│   ├── joueurs_agrege.csv        # 1 ligne par joueur : la table de sélection et d'indices
│   ├── carrieres_nettoyees.csv   # 1 ligne par passage en club : ce qu'on affiche
│   └── mvp_data.json             # échantillon de 320 joueurs + noms, embarqué dans le prototype
├── prototype/
│   └── index.html                # prototype jouable, autonome (à ouvrir dans un navigateur)
└── README.md
```

## Le prototype

`prototype/index.html` est un fichier autonome : il embarque ses données et
charge React via CDN. Aucune installation, aucun serveur. Ouvre-le dans un
navigateur pour jouer.

C'est un MVP fonctionnel : réglages de partie (championnats, période,
difficulté), série de 10 joueurs, autocomplétion tolérante aux accents,
3 essais par joueur, indices optionnels, récapitulatif final. Le design suit une
direction « album de vignettes ». Il tourne sur l'échantillon de 320 joueurs de
`mvp_data.json` (pas la base complète).

## Les données

### `joueurs_agrege.csv` — la table joueurs (15 392 lignes)

Une ligne par joueur. Colonnes :

| colonne | description |
|---|---|
| `player` | identifiant Wikidata (Q-ID) |
| `name` | nom d'affichage |
| `search_key` | nom normalisé (minuscules, sans accent, 26 lettres) pour l'autocomplétion |
| `nationalite` | nationalité principale (voir méthodo) |
| `nationalites_brut` | toutes les nationalités listées, séparées par ` / ` |
| `postes` | poste(s), séparés par ` / ` |
| `nb_clubs` | nombre de clubs dans la carrière complète |
| `apps_top5` | matchs cumulés dans les 5 grands championnats (assaini) |
| `sitelinks` | nombre de pages Wikipédia (proxy de notoriété) |
| `difficulte` | `facile` / `moyen` / `difficile` / `legende` / `exclu` |
| `first_year`, `last_year` | premières et dernières années d'activité |

Niveaux de difficulté (calculés par `scripts/difficulte.py`) :

`score = pages Wikipédia + matchs top 5 / 10 + matchs dans un grand club / 5`

Les grands clubs sont 28 clubs à forte visibilité européenne depuis 2000, listés
dans le script. Un match dans un grand club pèse donc trois fois plus qu'ailleurs.

- **facile** : star (60+ pages Wikipédia)
- **moyen** : score ≥ 75
- **difficile** : score ≥ 42
- **legende** : score < 42
- **exclu** : moins de 10 matchs top 5 (hors périmètre de jeu)

Les colonnes `matchs_grands_clubs` et `score` permettent de réajuster les seuils.

### `carrieres_nettoyees.csv` — les carrières (140 887 lignes)

Une ligne par passage en club pro. Colonnes : `player`, `name`, `club` (Q-ID),
`clubLabel`, `apps` (matchs de championnat), `start`, `end` (années), `pret`
(1 si prêt) et `source` (`wikipedia` ou `wikidata`). Construit par
`scripts/carrieres.py` à partir de l'infobox Wikipédia (anglais) du joueur, clubs
de formation exclus ; pour les rares joueurs sans infobox, à partir de
`carrieres_wikidata.csv`, avec des prêts déduits des dates.

## Collecte automatisée

`scripts/fetch.py` exécute les requêtes de `queries/<job>/` (une requête
`query.rq` et ses lots de Q-IDs dans `lots.txt`) et écrit les résultats dans
`data/raw/<job>/`. Le workflow GitHub Actions *Collecte Wikidata* le lance à
chaque modification de `queries/`. Les lots déjà récupérés sont sautés ; un lot
qui timeoute ou revient tronqué est découpé automatiquement.

## Méthodologie des données

Les données viennent de **Wikidata**, interrogé en SPARQL. Grandes étapes :

1. **Sélection** — `data/clubs_saisons_top5.csv` liste, pour chaque grand
   championnat (Ligue 1, Premier League, La Liga, Bundesliga, Serie A), les clubs
   présents chaque saison depuis 1999-2000. Un joueur est retenu si l'un de ses
   passages renseignés (matchs + dates, avec nationalité et poste) chevauche une
   saison où son club était dans un de ces championnats. On évalue donc le
   championnat à l'époque du passage, pas aujourd'hui → 15 392 joueurs.
   Les matchs d'un passage à cheval sur plusieurs divisions sont proratisés
   selon la part des saisons jouées en top 5.
2. **Carrières complètes** — l'infobox Wikipédia de chaque joueur (99 % en ont une),
   récupérée par `scripts/wiki.py` : clubs pros, matchs de championnat, prêts. Les
   clubs y sont des liens convertis en Q-ID Wikidata. Wikidata sert de secours.
3. **Nettoyage** — exclusion des sélections nationales (via la classe Wikidata
   « équipe nationale de football », pas par le libellé), correction des dates
   aberrantes, assainissement des nombres de matchs (plafond ~45/saison,
   valeurs corrompues ignorées).
4. **Difficulté** — score combinant notoriété, matchs top 5 et matchs en grand club.
   Les joueuses (fiches rattachées par erreur au club masculin) sont exclues.
5. **Nationalité principale** — la sélection A jouée quand elle existe (le pays
   sous les couleurs duquel le joueur a le plus de sélections), sinon la liste
   des nationalités Wikidata.
6. **Prêts** — non fournis par la donnée ; déduits à l'affichage quand un
   passage est strictement enclavé dans la période d'un autre club.

Note : la couverture Wikidata est inégale (meilleure sur les joueurs notables et
la période récente). Les seuils de difficulté et la nationalité de secours
peuvent être affinés.

## Licence des données

Les carrières proviennent des infobox de Wikipédia (CC BY-SA), dont les contributeurs sont remerciés.


Les données sont dérivées de Wikidata, sous licence
[CC0](https://creativecommons.org/publicdomain/zero/1.0/).
