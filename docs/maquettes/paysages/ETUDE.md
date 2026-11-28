# Paysages des campagnes : étude haute définition

Étude du 28 novembre 2026, à faire trancher par Antoine à l'œil. Ce n'est pas la refonte : un seul paysage, quatre
directions. Page à ouvrir : [comparaison.html](comparaison.html).

- **Recommandation : la direction D** (384 × 160 unités à 3 px, le double exact de l'actuel). Confiance : 70 %.
- D donne le même pixel à l'écran que B, un dessin plus fin, et convertit l'existant par × 2 au lieu de tout refaire.
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
| D. Double exact | 384 × 160 | 3 px | 1152 × 480 | `D-decor.gif`, `D-parallaxe.gif`, `D-pc.png`, `D-telephone.png` |

Aussi : `X-decor.png` (image fixe à la taille d'écran), `X-decor-1x.png` (un pixel par unité), `X-scene.png` (le décor
avec Pilou et un personnage).

**Méthode.** Le tableau est décrit une seule fois, en unités du décor actuel ; chaque définition le rejoue sur sa
grille. Les grandes formes sont les mêmes ; les petites (feuilles, brins, tuiles, éclats) se dessinent au pixel de la
grille, donc il y en a plus quand la grille est fine. La comparaison porte ainsi sur la définition, pas sur le sujet.
B et C ont un cadre plus haut (2:1) : 16 unités de ciel en plus. A et D gardent le cadre d'aujourd'hui (2,4:1).

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
choix posés sur la scène du PC ne sont pas montrés ; en D, la fenêtre du PC est élargie en étirant le gabarit dans ses
zones vides.

## Constats à l'œil

| | Constat |
|---|---|
| Actuel | Propre et lisible. Grands aplats, trois plans, deux images. Aucun effet « waouh ». |
| A | Nettement plus riche que l'actuel, et la lumière fonctionne. Mais un pixel de 5 px est trop gros pour les petits détails : les reflets et les herbes tournent au bruit, les nuages restent des marches d'escalier. J'ai dû réduire de moitié le tramage et les semis pour que l'image reste lisible. |
| B | Le premier palier où le paysage se lit comme une peinture : nuages en volumes, feuillage feuille par feuille, tuiles, chemin de lumière sur l'eau. Le cadre plus haut donne le plus grand ciel des quatre (lune, étoiles). |
| C | Plus fin que B (croisillons des fenêtres, reflet dans l'œil de la grenouille), mais à l'écran la différence avec B est faible. Le pixel de 2 px commence à ne plus se lire comme du pixel art à côté d'un habillage à 5 px. |
| D | Même pixel à l'écran que B, dessin un peu plus fin (2 unités par unité actuelle, contre 1,67). L'image est plus grande : 1152 px sur PC, toute la largeur du téléphone. Le ciel est moins haut qu'en B. Le mini-Pilou doublé automatiquement est anguleux : lisible, mais à affiner. |

**Pilou dans la scène D.** Le Pilou fin du bureau (96 × 112) à 3 px ferait 288 × 336 px : trop grand pour une scène de
480 px de haut. Le bon point de départ est le mini-Pilou de scène (34 × 36) doublé en 68 × 72 par la règle commune
d'agrandissement (MMPX) : son corps fait 120 × 90 px à l'écran (100 × 75 aujourd'hui), soit exactement la proportion
d'aujourd'hui dans une scène 1,2 fois plus grande. Les personnages-objets partent de leur portrait fin 64 × 64
(192 px à l'écran, 160 aujourd'hui).

**Cadrage de D.** 1152 px, c'est 74 px de trop pour un téléphone de 1078 px : on coupe 37 px par bord, soit 12 unités
du nouveau décor (6 unités d'aujourd'hui). Dans le montage, Pilou à sa place (24) tient à 5 px du bord : les places
trop près d'un bord seront à vérifier scène par scène, ou bien la scène glisse (léger travelling). Sur un téléphone de
1236 px (celui de la capture Robolectric), 1152 px tient sans rien couper, comme aujourd'hui. Sur 720 px : 2 px par
unité, 768 px, même coupe de 12 unités par bord. Sur PC : la fenêtre s'élargit de 192 px (1196 px dans le montage), ou
la scène est cadrée à 960 px. Ce cadrage coupe 96 px par bord (32 unités du nouveau décor) et Pilou, à sa place,
serait coupé : l'élargissement est le bon choix.

## Ce que chaque direction impose

Chiffres mesurés par l'outil sur ce décor (format texte des sprites, 8 images) ; les totaux sur 46 décors sont
extrapolés. Les faits sur le moteur viennent de la session du Théâtre, relayés par le pilote (confiance annoncée :
85 à 90 %) ; j'ai vérifié la constante `W, H = 192, 80` dans `theatre.py`, pas le reste.

| | Actuel | A | B | C | D |
|---|---|---|---|---|---|
| Rapport à l'actuel | — | × 1 | × 5/3, autre cadre | × 2,5, autre cadre | × 2 exact, même cadre |
| Pixels par image | 15 360 | 15 360 | 51 200 (× 3,3) | 115 200 (× 7,5) | 61 440 (× 4) |
| Poids d'un décor (texte) | 94 Ko (6 images) | 121 Ko | 401 Ko | 902 Ko | 481 Ko |
| Poids d'un décor (gzip) | non mesuré | 13 Ko | 94 Ko | 171 Ko | 109 Ko |
| 46 décors (texte) | 4,3 Mo | ≈ 5,6 Mo | ≈ 18 Mo | ≈ 41 Mo | ≈ 22 Mo |
| Couleurs | — | 56 | 57 | 57 | 56 |
| Pilou de scène (92 poses) | en service | inchangé | à redessiner (rapport non entier) | à redessiner | doublé automatiquement ; à affiner ensuite |
| Personnages en pied (29) | 13 faits, 16 à dessiner | inchangé | 29 à redessiner | 29 à redessiner | 13 : portrait fin 64 × 64 tel quel ; 16 à dessiner (déjà prévus dans SCENES.md) |
| Acteurs (17 : bêtes, effets) | en service | inchangés | à redessiner | à redessiner | doublés automatiquement |
| Scènes (une quarantaine) | — | inchangées | à replacer à l'œil | à replacer à l'œil | coordonnées doublées |
| Décors à refaire | — | 46 | 46 | 46 | 46 |
| Code PC et Android | — | aucun | taille, une quinzaine de constantes de mouvement à mettre à l'échelle 5/3, référence, tests, mise en page | idem, plus un format de ressource plus compact | taille et constantes × 2, référence, tests ; cadrage sur téléphone, largeur de la fenêtre PC |
| Téléphone de 1078 px | 960 px, marges | 960 px, marges | 960 px, marges | 960 px, marges | pleine largeur, 12 unités coupées par bord |
| Téléphone de 720 px | 3 px, 576 px | 3 px, 576 px | 2 px, 640 px | 1 px, 480 px : trop petit | 2 px, pleine largeur, 12 unités coupées par bord |
| Effet | faible | moyen | fort, le plus grand ciel | très fort | fort, le plus grand à l'écran |

Correction par rapport à la première version de cette étude : j'avais compté pour B « 13 personnages réutilisables »
et « le Pilou du bureau existe ». C'est vrai des dessins, pas de leur usage : les poses de scène et les personnages
sont posés au pixel sur la grille de 192, et un rapport de 5/3 ne les convertit pas. En B comme en C, ils sont à
refaire.

**Charge de dessin.** Le théâtre recompose toute l'image douze fois par seconde (décor, acteurs, Pilou), puis
l'agrandit. En B il y a 3,3 fois plus de pixels à composer, en D 4 fois, en C 7,5 fois. Je n'ai rien mesuré sur un
appareil : SCENES.md note déjà que la fluidité à 192 × 80 n'a jamais été vérifiée sur un vrai téléphone. Le risque est
réel en C, modéré en B et D. Confiance : 55 %.

**Règle « une seule taille de pixel ».** Elle tient dans la scène pour toutes les directions (décor, Pilou,
personnages à la même unité). Mais en B, C et D, l'habillage (cadres à 5 px, police à 4 px) n'a plus le pixel de la
scène : STYLE.md dit aujourd'hui « une seule taille de pixel dans toute l'app : celle de la scène ». Il faudra soit
l'assumer (la scène est un tableau dans un cadre), soit affiner les cadres. C'est une décision d'Antoine.

**Parallaxe.** Elle demande des plans séparés (cinq ici), donc un changement du format des décors et du compositeur
des deux côtés. Les GIF la montrent ; je la garderais pour une seconde étape, elle n'est pas nécessaire à l'effet.
En D, elle donnerait un sens au cadrage du téléphone (la scène glisse au lieu d'être coupée).

**Temps de travail.** Estimations, pas des mesures ; une « session » est une session de travail comme celle-ci.
Confiance : 55 %.

| | A | B | C | D |
|---|---|---|---|---|
| 46 décors (le moteur de peinture existe, il reste à composer chaque lieu) | 5 à 7 | 6 à 8 | 7 à 10 | 6 à 8 |
| Pilou de scène, personnages, acteurs | 0 | 4 à 6 | 6 à 8 | 1 à 2 |
| Code, scènes, référence, tests, mise en page | 0 | 4 à 5 | 5 à 7 | 2 à 3 |
| Total (sessions) | 5 à 7 | 14 à 19 | 18 à 25 | 9 à 13 |

**Risques.**

- B, C, D : PC et Android doivent calculer la même image (règle 5). Tout changement de taille passe par la référence
  et les deux tests. En D c'est une multiplication par deux ; en B et C, un rapport non entier ou un nouveau cadre.
- B, C, D : la scène gagne 80 px de haut ; la fenêtre du PC s'allonge (ou la boîte de dialogue rétrécit), le fil du
  téléphone descend d'autant.
- D : le cadrage sur téléphone est une règle nouvelle (coupe ou glissement), à écrire des deux côtés.
- D : le Pilou de scène doublé est anguleux ; il faudra le redessiner finement un jour, mais rien ne bloque d'ici là.
- C : poids (≈ 41 Mo de texte, à comparer aux 11 Mo de tout `assets/sprites2x` aujourd'hui), mémoire, lecture du
  texte au chargement.
- Toutes : mes décors sont générés par bruit et par formules ; 46 lieux demandent 46 compositions distinctes pour ne
  pas se ressembler. C'est le gros du travail, quelle que soit la définition.
- L'outil d'étude utilise numpy (absent du reste de `outils/sprites/`) : à garder comme outil de fabrication, ou à
  réécrire sur `toile.py` si on veut tout au même endroit.

## Recommandation

**D : 384 × 160 unités à 3 px, le double exact de l'actuel.** Confiance : 70 %.

1. L'effet demandé y est : même pixel à l'écran que B, dessin plus fin, image plus grande (toute la largeur du
   téléphone).
2. C'est la seule direction haute définition qui convertit l'existant au lieu de le refaire : scènes, mouvements,
   acteurs, Pilou de scène, 13 personnages. Environ 9 à 13 sessions, contre 14 à 19 pour B.
3. Ce qu'on perd face à B : le cadre 2:1 et son très grand ciel. Si Antoine tient à ce ciel, B reste possible, au prix
   de tout replacer.
4. C est écarté : à peine plus beau, bien plus lourd, trop petit sur un téléphone étroit. A est écarté : il ne porte
   pas le fourmillement.

Avant de lancer la refonte, une vérification courte : afficher ce décor D dans le vrai théâtre, sur le PC puis sur un
téléphone, et mesurer la fluidité. Si elle ne tient pas, le repli est de ne recomposer que ce qui change d'une image à
l'autre.

## Refaire les images

```bash
py outils/sprites/paysages_etude.py                 # tout, dans docs/maquettes/paysages
py outils/sprites/paysages_etude.py <dossier> D     # une seule direction
```
