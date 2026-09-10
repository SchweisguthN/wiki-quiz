# Iconic Careers

Jeu où l'on devine un footballeur à partir de sa carrière en club. On affiche
le parcours d'un joueur (clubs, périodes, matchs joués, prêts en retrait) et il
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

### `joueurs_agrege.csv` — la table joueurs (14 100 lignes)

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

Niveaux de difficulté :
- **facile** : star (60+ pages Wikipédia)
- **moyen** : 250+ matchs dans les grands championnats
- **difficile** : 100 à 250 matchs
- **legende** : 10 à 100 matchs
- **exclu** : moins de 10 matchs (hors périmètre de jeu)

### `carrieres_nettoyees.csv` — les carrières (112 760 lignes)

Une ligne par passage en club. Colonnes : `player`, `name`, `club`,
`clubLabel`, `apps` (matchs), `start`, `end` (années). Sélections nationales
retirées, dates aberrantes corrigées. C'est la source pour l'affichage des
parcours.

## Méthodologie des données

Les données viennent de **Wikidata**, interrogé en SPARQL. Grandes étapes :

1. **Sélection** — pour chaque grand championnat (Ligue 1, Premier League,
   La Liga, Bundesliga, Serie A), extraction des joueurs ayant au moins un
   passage renseigné (matchs + dates + nationalité + poste), actifs en 2000 ou
   après. Union des cinq → ~14 100 joueurs.
2. **Carrières complètes** — pour chaque joueur retenu, récupération de tous ses
   clubs (y compris hors top 5) pour l'affichage.
3. **Nettoyage** — exclusion des sélections nationales (via la classe Wikidata
   « équipe nationale de football », pas par le libellé), correction des dates
   aberrantes, assainissement des nombres de matchs (plafond ~45/saison,
   valeurs corrompues ignorées).
4. **Difficulté** — calculée sur les matchs top 5 et la notoriété (sitelinks).
5. **Nationalité principale** — la sélection A jouée quand elle existe (le pays
   sous les couleurs duquel le joueur a le plus de sélections), sinon la liste
   des nationalités Wikidata.
6. **Prêts** — non fournis par la donnée ; déduits à l'affichage quand un
   passage est strictement enclavé dans la période d'un autre club.

Note : la couverture Wikidata est inégale (meilleure sur les joueurs notables et
la période récente). Les seuils de difficulté et la nationalité de secours
peuvent être affinés.

## Licence des données

Les données sont dérivées de Wikidata, sous licence
[CC0](https://creativecommons.org/publicdomain/zero/1.0/).
