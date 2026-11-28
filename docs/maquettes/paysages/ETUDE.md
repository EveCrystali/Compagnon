# Paysages des campagnes : étude haute définition

Étude du 28 novembre 2026, à faire trancher par Antoine à l'œil. Ce n'est pas la refonte : un seul paysage, trois
directions. Page à ouvrir : [comparaison.html](comparaison.html).

- **Recommandation : la direction B** (320 × 160 unités à 3 px). Confiance : 70 %.
- A ne coûte presque rien mais ne porte pas le « fourmillement » ; C est à peine plus beau que B pour bien plus cher.
- Rien n'a tourné dans l'application : ce sont des images de l'outil d'étude. La fluidité sur téléphone reste à mesurer.

## La demande

Antoine, mot pour mot : « Je pense que les paysages de campagne devraient [être] beaux : détaillés, fourmille de petits
détails, soignés, avec de grands paysages bien peints en haute définition pour aussi provoquer un effet waouh. »

## Ce qui a été peint

La mare du prologue (« La mare », `decor-prologue-mare`) au soleil couchant : la colline d'en face et son arbre, la
maison au loin, les trois nénuphars et la grenouille de l'histoire. Tout sort de
`outils/sprites/paysages_etude.py` : aucun logiciel de dessin, aucune image importée, aucun style repris.

| | Définition | Pixel à l'écran | Taille à l'écran | Fichiers |
|---|---|---|---|---|
| 0. Actuel | 192 × 80 | 5 px | 960 × 400 | `actuel-decor.gif`, `actuel-pc.png`, `actuel-telephone.png` |
| A. Enrichi | 192 × 80 | 5 px | 960 × 400 | `A-decor.gif`, `A-parallaxe.gif`, `A-pc.png`, `A-telephone.png` |
| B. Haute définition | 320 × 160 | 3 px | 960 × 480 | `B-decor.gif`, `B-parallaxe.gif`, `B-pc.png`, `B-telephone.png` |
| C. Très haute définition | 480 × 240 | 2 px | 960 × 480 | `C-decor.gif`, `C-parallaxe.gif`, `C-pc.png`, `C-telephone.png` |

Aussi : `X-decor.png` (image fixe à la taille d'écran), `X-decor-1x.png` (un pixel par unité), `X-scene.png` (le décor
avec Pilou et un personnage).

**Méthode.** Le tableau est décrit une seule fois, en unités du décor actuel ; chaque définition le rejoue sur sa
grille. Les grandes formes sont les mêmes ; les petites (feuilles, brins, tuiles, éclats) se dessinent au pixel de la
grille, donc il y en a plus quand la grille est fine. La comparaison porte ainsi sur la définition, pas sur le sujet.

**Composition.** Premier plan sombre (berge, arbre, lanterne, roseaux, panneau) ; plan moyen (mare, prés, maison,
colline) ; lointains bleutés (trois crêtes, un moulin) ; grand ciel. Une lumière : le soleil bas derrière les crêtes.
Palette : 57 couleurs (violets, pêche, or, sarcelle, crème), sans opposition rouge / vert.

**Détails animés (20).** Étoiles, nuages, oiseaux, moulin, fumée, fenêtres, linge, balançoire, mouton, reflets, éclats
du soleil sur l'eau, ronds, grenouille, barque, libellule, nénuphars, herbes, feuilles, lanterne, roseaux, lucioles.
La mare est le miroir calculé de tout ce qui est derrière elle.

**Montages.** PC : capture réelle de la fenêtre à 100 % (`gabarits/pc-fenetre-100.png`). Téléphone : capture
Robolectric du même écran (`gabarits/telephone-robolectric-1236x2745.png`, CI du 28 novembre) ramenée à 1078 × 2400.
Limites honnêtes : l'habillage du téléphone est adouci par la réduction, son texte est celui du gabarit (« Devant la
porte ») ; le personnage est Grumeau, emprunté à « La Grande Panne » (le prologue n'a pas de personnage en pied) ; les
choix posés sur la scène du PC ne sont pas montrés.

## Constats à l'œil

| | Constat |
|---|---|
| Actuel | Propre et lisible. Grands aplats, trois plans, deux images. Aucun effet « waouh ». |
| A | Nettement plus riche que l'actuel, et la lumière fonctionne. Mais un pixel de 5 px est trop gros pour les petits détails : les reflets et les herbes tournent au bruit, les nuages restent des marches d'escalier. J'ai dû réduire de moitié le tramage et les semis pour que l'image reste lisible. |
| B | Le premier palier où le paysage se lit comme une peinture : nuages en volumes, feuillage feuille par feuille, tuiles, chemin de lumière sur l'eau. Le grand ciel (deux fois plus haut) fait l'essentiel de l'effet. |
| C | Plus fin que B (croisillons des fenêtres, reflet dans l'œil de la grenouille), mais à l'écran la différence avec B est faible. Le pixel de 2 px commence à ne plus se lire comme du pixel art à côté d'un habillage à 5 px. |

## Ce que chaque direction impose

Chiffres mesurés par l'outil sur ce décor (format texte des sprites, 8 images) ; les totaux sur 46 décors sont
extrapolés.

| | Actuel | A | B | C |
|---|---|---|---|---|
| Pixels par image | 15 360 | 15 360 | 51 200 (× 3,3) | 115 200 (× 7,5) |
| Poids d'un décor (texte) | 94 Ko (6 images) | 121 Ko | 401 Ko | 902 Ko |
| Poids d'un décor (gzip) | non mesuré | 13 Ko | 94 Ko | 171 Ko |
| 46 décors (texte) | 4,3 Mo | ≈ 5,6 Mo | ≈ 18 Mo | ≈ 41 Mo |
| Couleurs | — | 56 | 57 | 57 |
| Mini-Pilou de scène (92 poses) | en service | inchangé | remplacé par le Pilou du bureau 48 × 56 ; ses poses de scène (marche, bond, coucou…) à refaire à cette taille | Pilou fin 96 × 112 ; mêmes poses à refaire |
| Personnages en pied (29) | 13 faits, 16 à dessiner | inchangé | 13 : le portrait fin 64 × 64 sert tel quel ; 16 à dessiner (déjà prévus dans SCENES.md) | 29 à redessiner (× 1,5) |
| Acteurs (17 : bêtes, effets) | en service | inchangés | à redessiner | à redessiner |
| Décors à refaire | — | 46 | 46 | 46 |
| Code PC et Android | — | aucun | taille de scène (192 × 80 codée dans `theatre.py`, `Theatre.cs`, `Theatre.java`), fichiers `assets/scenes/*.txt`, référence et tests, hauteur de la fenêtre et de l'écran | idem, plus un format de ressource plus compact |
| Téléphone de 720 px de large | 3 px, 576 px | 3 px, 576 px | 2 px, 640 px | 1 px, 480 px : trop petit |

**Charge de dessin.** Le théâtre recompose toute l'image douze fois par seconde (décor, acteurs, Pilou), puis
l'agrandit. En B il y a 3,3 fois plus de pixels à composer, en C 7,5 fois. La surface affichée, elle, ne change presque
pas (960 × 480 au lieu de 960 × 400). Je n'ai rien mesuré sur un appareil : SCENES.md note déjà que la fluidité à
192 × 80 n'a jamais été vérifiée sur un vrai téléphone. Le risque est réel en C, modéré en B. Confiance : 55 %.

**Règle « une seule taille de pixel ».** Elle tient dans la scène pour les trois directions (décor, Pilou,
personnages à la même unité). Mais en B et C, l'habillage (cadres à 5 px, police à 4 px) n'a plus le pixel de la
scène : STYLE.md dit aujourd'hui « une seule taille de pixel dans toute l'app : celle de la scène ». Il faudra soit
l'assumer (la scène est un tableau dans un cadre), soit affiner les cadres. C'est une décision d'Antoine.

**Parallaxe.** Elle demande des plans séparés (cinq ici), donc un changement du format des décors et du compositeur
des deux côtés. Les GIF la montrent ; je la garderais pour une seconde étape, elle n'est pas nécessaire à l'effet.

**Temps de travail.** Estimations, pas des mesures ; une « session » est une session de travail comme celle-ci.
Confiance : 55 %.

| | A | B | C |
|---|---|---|---|
| 46 décors (le moteur de peinture existe, il reste à composer chaque lieu) | 5 à 7 sessions | 6 à 8 | 7 à 10 |
| Pilou de scène, personnages, acteurs | 0 | 3 à 4 | 6 à 8 |
| Code, référence, tests, mise en page | 0 | 2 à 3 | 3 à 4 |
| Total | 5 à 7 | 11 à 15 | 16 à 22 |

**Risques.**

- B et C : PC et Android doivent calculer la même image (règle 5). Tout changement de taille passe par la référence
  et les deux tests ; c'est mécanique, mais large.
- B et C : la fenêtre du PC gagne 80 px de haut (ou la boîte de dialogue en perd 80) ; sur téléphone la scène prend
  480 px au lieu de 400, donc le fil descend d'autant.
- C : poids (≈ 41 Mo de texte, à comparer aux 11 Mo de tout `assets/sprites2x` aujourd'hui), mémoire, lecture du
  texte au chargement.
- Toutes : mes décors sont générés par bruit et par formules ; 46 lieux demandent 46 compositions distinctes pour ne
  pas se ressembler. C'est le gros du travail, quelle que soit la définition.
- L'outil d'étude utilise numpy (absent du reste de `outils/sprites/`) : à garder comme outil de fabrication, ou à
  réécrire sur `toile.py` si on veut tout au même endroit.

## Recommandation

**B : 320 × 160 unités à 3 px.** Confiance : 70 %.

1. C'est là que l'effet demandé apparaît ; A n'y arrive pas, C n'ajoute presque rien à l'œil.
2. Le Pilou du bureau et 13 personnages existent déjà à cette unité : le joueur retrouve en scène le Pilou qu'il
   connaît, au lieu d'un mini-Pilou à part.
3. Le poids reste raisonnable (≈ 18 Mo de texte, bien moins une fois compressé dans l'APK).
4. Il tient sur un petit téléphone (2 px), ce que C ne fait pas.

Avant de lancer la refonte, une vérification courte : afficher ce décor B dans le vrai théâtre, sur le PC puis sur un
téléphone, et mesurer la fluidité. Si elle ne tient pas, le repli est B sans recomposition complète (ne redessiner
que ce qui change).

## Refaire les images

```bash
py outils/sprites/paysages_etude.py            # tout, dans docs/maquettes/paysages
py outils/sprites/paysages_etude.py <dossier> B   # une seule direction
```
