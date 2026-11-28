# Le Théâtre en haute définition : le format

Règle 9 de `CLAUDE.md` (Antoine, 28 novembre 2026) : le pixel art n'est jamais une baisse de définition. La scène passe de
192 × 80 à **480 × 240 unités**. Ce document fixe le format des ressources : décors, plans, acteurs, personnages, Pilou.
Les sessions « paysages » et « personnages HD » produisent à ce format ; le moteur (`outils/sprites/theatre.py`,
`Theatre.cs`, `Theatre.java`) les lit à l'identique. Le format d'aujourd'hui (192 × 80) est décrit dans
[SCENES.md](SCENES.md) ; il reste en service pendant la migration.

Statut : **format décidé ; moteur de référence écrit** (`outils/sprites/theatre_hd.py`, branche `claude/theatre-hd`) ;
PC et téléphone en cours.

## 1. L'unité et le cadre

| | |
|---|---|
| Scène | 480 × 240 unités (rapport 2:1) |
| Une unité | un pixel du dessin, jamais agrandi en dessin : 1 unité = 1 pixel du Pilou fin du bureau |
| À l'écran | `k` px d'écran par unité, `k` entier, le même pour toute l'image |
| PC (100 %) | `k = 2` : scène de 960 × 480 px |
| Téléphone de 1078 px | `k = 2` : 960 × 480 px, 59 px de marge de chaque côté, rien n'est coupé |
| Écran de 1440 px et plus | `k = 3` (1440 × 720) |
| Écran plus étroit que 960 px (720 px) | `k = 2`, et la scène est **cadrée** : on voit `floor(largeur / 2)` unités (360 sur 720 px), la caméra glisse doucement (une seconde) pour garder dans le champ Pilou, le personnage qui parle, et l'acteur touché. La légende du lieu est posée par l'interface, pas par la scène : elle ne sort jamais du cadre. `k = 1` (480 px de large) est refusé : trop petit. |

La caméra : un seul nombre, `x` du bord gauche visible, entier, borné à `[0, 480 − largeur visible]`. Sur un écran
assez large, elle vaut 0 et ne bouge pas.

## 2. Pendant la migration : deux définitions, jamais dans la même scène

Pour chaque décor, le moteur choisit **un seul jeu** de ressources :

- **HD** si `assets/decors/decor-<campagne>-<décor>.txt` existe en 480 × 240 **et** si la scène a sa section dans
  `assets/scenes-hd/<campagne>.txt` : décor HD, scène HD, Pilou fin, personnages et acteurs HD (§ 5 à 7). Un acteur
  ou un personnage sans version HD n'est **pas** dessiné (jamais d'ancien sprite agrandi dans une scène HD) ; le
  personnage garde alors son portrait dans la boîte de dialogue.
- **Ancien** sinon : tout comme aujourd'hui (192 × 80, `scene-pilou`, `pied-*`, `acteur-*` d'`assets/sprites2x`),
  affiché à l'échelle entière qui tient (aujourd'hui ×5 sur PC).

Le jeu reste jouable et fusionnable à chaque étape. Quand une campagne est entièrement HD, ses anciennes ressources
sont retirées.

## 3. Les décors : `assets/decors/decor-<campagne>-<décor>.txt`

Le format compact de la session « paysages » (docs/SPRITES.md, « Décors haute définition ») est **adopté tel quel**
pour un décor d'un seul plan, avec la taille 480 × 240 et une extension pour les plans.

```
# commentaire
id: decor-prologue-mare
taille: 480 240
plans: 3                            1 à 5 ; absent : 1 (un seul plan, le format d'aujourd'hui)
plan: ciel 0 fond                   nom, profondeur (0 à 100), fond | devant
duree: 200                          ms par image de ce plan
palette: a=#5b6fc4 b=#7384d0 …      67 lettres au plus, propre à ce plan
images: 8
…                                   images × 240 lignes de plages
plan: arbres 40 fond
duree: 0
palette: …
images: 1
…
plan: herbes 100 devant
…
```

- **Plages** : `[n]c` comme aujourd'hui ; `n` décimal, absent = 1 ; `c` une lettre de palette (`a-z A-Z ! $ % & * + -
  / < > ? @ ^ _ ~`), `.` = comme le pixel de l'image précédente du même plan (jamais dans la première image), et
  **`,` = transparent** (interdit dans le premier plan, qui est opaque). La somme des `n` vaut la largeur du plan.
- **Plans** : du fond vers l'avant. Le premier plan est opaque et fait 480 × 240. Les suivants ont 240 de haut et une
  largeur ≥ 480 (plus large : de quoi glisser plus tard). La **profondeur** dit de combien le plan suit la caméra :
  0 = immobile (le ciel), 100 = au pas de la caméra (le sol). Tant que la caméra vaut 0, la profondeur ne change rien.
- **Ordre de dessin** : les plans `fond` dans l'ordre, puis les acteurs, les personnages et Pilou (triés par la ligne
  de leurs pieds, comme aujourd'hui), puis les plans `devant`, puis les effets (éclats, notes, ronds).
- **Animation d'un plan** : image `(t / duree) mod images` ; `duree: 0` ou `images: 1` = fixe. Aux animations réduites,
  les plans restent sur leur première image (même règle qu'aujourd'hui pour les décors).
- **Couleurs** : opaques (`#rrggbb`) ; aucune demi-transparence, le léger se dit en trame. Jamais d'opposition rouge /
  vert.
- **Référence** : `outils/sprites/decors-hd-reference.txt`, une ligne par plan : `id plan largeur hauteur images duree`
  puis le FNV-1a de chaque image décodée (ARGB `0xFFrrggbb`, transparent = `0x00000000`, rangée par rangée).

## 4. Les scènes : `assets/scenes-hd/<campagne>.txt`

La syntaxe d'`assets/scenes/<campagne>.txt` (SCENES.md), **en unités HD** : `scene`, `sol`, `place`, `interlocuteur`,
`cle`, `acteur`, `sensible`. Les tableaux HD sont peints dans le **repère des paysages** : un point (x, y) de l'ancienne
scène devient (2,5 x, 2,5 y + 40). Les scènes HD sont donc **écrites par la conversion** de l'ancienne scène
(`py outils/sprites/theatre_hd.py`), jamais à la main ; quand un tableau demande une retouche (le Pilou fin est plus
large que le mini-Pilou), elle va dans la table `AJUSTEMENTS` de `theatre_hd.py`. Les longueurs et vitesses du moteur
sont multipliées par 5/2 (`E(sc, v)`).

## 5. Pilou : le Pilou fin du bureau

Dans une scène HD, Pilou **est** le Pilou fin du bureau (rendu fin de `RenduPilou`, grille 96 × 112), avec son stade
réel (Gouttelette, Pilou, Nimbus, Astral), sa variante câline ou espiègle, sa couleur, ses accessoires et ses
expressions. Plus de `scene-pilou` en HD.

| | |
|---|---|
| Toile | 96 × 112 unités |
| Ancrage | colonne 48, **ligne des pieds 107** (vérifiée sur les stades 1 et 2 ; Nimbus et Astral descendent de 3 à 4 unités sous ses pieds : son nuage, sa traîne) |
| Taille mesurée (pose de repos) | Gouttelette 46 × 68, Pilou 62 × 87, Nimbus 86 × 84, Astral 80 × 102 |
| Ce que le Théâtre lui demande | une pose du bureau : expression (humeur), bouche (parle), marche, regard, saut (décalage vertical), et l'évolution (0 à 1) pour la métamorphose |

Le rendu fin est déjà le même sur le PC et le téléphone (`rendus-reference-2x.txt`). La correspondance « état de scène →
pose du bureau » est `theatre.pose_hd` : marche, bouche ouverte une image sur deux pendant une réplique (champ `parle` du
rendu, ajouté pour le Théâtre), clin d'œil, regard, saut de joie, coucou (antenne qui salue), sursaut ; l'humeur donne
l'expression. Le stade, la variante, la couleur et les accessoires viennent du joueur.

## 6. Les personnages en pied : `assets/sprites-hd/pied-<campagne>-<personnage>.txt`

Même format compact (§ 3, un seul plan, `,` transparent), plus deux champs :

```
id: pied-grande-panne-grumeau
taille: 72 104
ancre: 36 103                       x du milieu, y de la ligne des pieds
duree: 150
palette: …
images: 5                           0 et 1 repos, 2 yeux fermés, 3 et 4 bouche ouverte (comme aujourd'hui)
```

- **Tailles** (le corps de Pilou au stade Pilou fait 87 de haut) : humains 100 à 135 ; personnages-objets 60 à 110 ;
  ceux qui volent gardent du vide sous eux dans la toile (comme aujourd'hui, × 2,5).
- Un personnage regarde vers la droite dans son dessin ; le moteur le retourne pour regarder Pilou.

## 7. Les acteurs : `assets/sprites-hd/acteur-<nom>.txt`

Même format que les personnages (§ 6) : `taille`, `ancre` (par défaut le milieu du bas), `duree`, `images`. Taille
indicative : 2,5 fois l'acteur d'aujourd'hui, redessiné (jamais agrandi). Même ordre d'images qu'aujourd'hui pour les
acteurs qui réagissent (vol, traverse, rond…).

## 8. Charge

- Chaque image de chaque plan est décodée **une fois** (au chargement du décor) puis gardée.
- À chaque pas (12 par seconde), on ne recompose que les rectangles qui changent : plans animés, acteurs, personnages,
  Pilou, effets. Les plans fixes sont aplatis une fois.
- Mesures à donner (avant / après, PC et test Java) : temps de chargement d'un décor, temps de composition d'une image,
  processeur du PC pendant une lecture.

## 9. Nommage et outils

| Ressource | Fichier | Produit par |
|---|---|---|
| Décor HD | `assets/decors/decor-<campagne>-<décor>.txt` | session « paysages » (`outils/sprites/decors_hd.py`) |
| Scène HD | `assets/scenes-hd/<campagne>.txt` | moteur (replacement à l'œil) |
| Personnage en pied HD | `assets/sprites-hd/pied-<campagne>-<personnage>.txt` | session « personnages HD » |
| Acteur HD | `assets/sprites-hd/acteur-<nom>.txt` | session « personnages HD » |
| Pilou | rendu fin du bureau, pas de fichier | — |

Un seul lecteur (le décodeur compact, § 3) pour les décors, les personnages et les acteurs, des deux côtés, sans
bibliothèque.
