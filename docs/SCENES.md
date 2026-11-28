# Le théâtre des campagnes : une scène vivante

La fenêtre Aventure montre le lieu de l'histoire **en entier**, comme une scène de dessin animé en pixel art : Pilou
y vit en pied (il entre, marche, parle, réagit, s'en va), des petites bêtes passent, l'eau fait des ronds, et ce qu'on
touche répond. Ce document est le contrat commun : dessin (Python), référence, PC et téléphone.

Décisions d'Antoine (atelier du 27 novembre 2026, planches dans `docs/maquettes/animations/`, registre
`docs/maquettes/animations/DECISIONS.md`) :

- **Mise en scène « Théâtre »** : la scène prend toute la largeur (décor fin 192 × 80 agrandi d'un facteur entier, ×5
  dans la fenêtre de 1020 × 720) ; dessous, une boîte de dialogue montre la réplique en cours avec le portrait de qui
  parle ; les choix se posent sur la scène ; « ☰ Relire » rouvre tout le fil par-dessus la scène.
- **Mini-Pilou taille M** : corps 20 × 15 pixels fins (100 px à l'écran à ×5).
- **Tous les personnages en pied** dans la scène (29), en plus de leur portrait dans la boîte : à dessiner campagne par
  campagne (voir « Ce qui reste »).
- **Le Pilou du bureau suit l'aventure** : échos de la scène, bout de décor pendant l'attente, départ et retour joués,
  objets du sac portés (voir « Ce qui reste »).
- **Le réglage « ✧ » décide** des animations ; le réglage « Afficher les animations » de Windows (ou l'échelle
  d'animation d'Android) ne donne que la valeur de départ tant que le joueur n'a rien choisi (28 novembre 2026 : chez
  Antoine, Windows a ses animations coupées, et toutes les animations des campagnes l'étaient avec).

## Ce qui est calculé en commun

Tout ce qui décide d'un pixel est dans `outils/sprites/theatre.py` (référence), porté à l'identique dans
`apps/PilouBureau/Theatre.cs` et `android/.../Theatre.java` : arithmétique entière, tables (`SINUS`, `LISSE`), division
tronquée vers zéro, même ordre des opérations, même mélange alpha. `python3 outils/sprites/theatre.py` écrit
`assets/scenes/animations.txt` et `outils/sprites/theatre-reference.txt` (scénarios, positions, acteurs et effets,
empreinte FNV-1a de chaque image) ; `TheatreTests.cs` et `TheatreTest.java` la rejouent ligne à ligne.

| Fonction | Rôle |
|---|---|
| `pilou(scène, anims, événements, t, regard, niveau)` | (x, y des pieds, image, miroir, visible) du mini-Pilou |
| `acteurs(...)` | les acteurs d'ambiance présents : sprite, image, x (centre), y (bas), miroir |
| `effets(...)` | les effets de réaction aux clics (éclats, bulle, note, ronds, poisson, ploufs, graines) |
| `composer(...)` | l'image ARGB 192 × 80 : décor, puis acteurs et Pilou triés par leurs pieds, puis les effets |
| `fnv(pixels)` | l'empreinte d'une image, pour comparer les trois calculs |

**Le temps.** `t` est le temps de la scène en millisecondes. Tout avance par pas de 83 ms (douze images par seconde,
« en deux » comme un dessin animé) ; le décor garde sa propre boucle (`duree` de son sprite).

**Les événements**, toujours ajoutés dans l'ordre du temps (`(t, sorte, a, b)`) :

| Sorte | a, b | Effet |
|---|---|---|
| `entree` | a : x de départ (0 : le bord gauche) | Pilou marche jusqu'à sa place |
| `depart` | a : +1 droite, -1 gauche | il marche jusqu'à sortir de la scène (un choix l'envoie en route) |
| `humeur` | a : l'humeur du message | son visage de repos ; « joie » et « surpris » jouent aussi un geste |
| `parle` | a : fin de la réplique | sa bouche bouge pendant l'écriture ; une nouvelle réplique remplace la précédente (a = t la coupe) |
| `clic` | a, b : point touché (pixels du décor) | Pilou (saut de joie, puis coucou), un acteur (il s'enfuit), une chose sensible (sa réaction) |

Un clic ne voit que ce qui le précède : en ajouter un ne change jamais le passé (testé). Les 24 derniers clics
seulement comptent. Le regard suit la souris sur le PC (paramètre `regard`, pas un événement) ; rien sur le téléphone.

**Les niveaux.** `completes` : tout. `reduites` : décor fixe, pas d'acteurs, Pilou à sa place qui cligne. `aucune` :
rien ne bouge.

## Les sprites de scène (dessin fin seulement)

| Sprite | Module | Contenu |
|---|---|---|
| `scene-pilou` | `scene_pilou.py` | le mini-Pilou M, 34 × 36, ancre (17, 33) ; corps, pieds et tige aux couleurs de sa teinte (`@contour`, `@ombre`, `@base`, `@clair`) |
| `acteur-<nom>` | `acteurs_scenes.py` | les bêtes (libellule, papillon, oiseau, abeille, graine, feuille, poisson) et les effets (rond, plouf, bulle, éclats, note) ; ancre : le milieu du bas |

Le mini-Pilou est dessiné image par image avec les principes du dessin animé : anticipation (il s'écrase avant de
sauter), étirement en vol, amorti à la réception, l'antenne qui traîne derrière le mouvement, le corps qui penche en
marchant. Ses animations nommées (`assets/scenes/animations.txt`) : un visage de repos par humeur (`repos-joie`,
`repos-peur`…), `cligne`, `marche`, `joie`, `peur`, `regard-g`, `regard-d`, `regard-h`, `bond`, `coucou`, `parle`,
`pense`, `surpris`.

## Une scène par décor : `assets/scenes/<campagne>.txt`

```
scene mare
sol 4 78 188 78                       la ligne où marchent les pieds de Pilou (x0 y0 x1 y1 ; une pente est permise)
place 18                              où il se tient
interlocuteur 168                     où se tiendra un personnage en pied
acteur libellule vol 60 40 160 58 7   acteur-libellule : comportement, puis ses paramètres
acteur rond rond 70 68 2600 0
sensible grenouille 90 48 102 60 bulle 93 55   ce qui répond au clic : zone, réaction, paramètres
```

Comportements : `vol x0 y0 x1 y1 graine` (posé, puis un trait vers un autre point de la zone : libellule, papillon,
abeille ; s'enfuit si on le touche) ; `traverse y0 y1 période décalage vitesse` (oiseau qui passe ; s'envole si on le
touche) ; `rond x y période décalage` ; `saut x y période décalage` (poisson) ; `pose x y` ; `flotte x y période
décalage vx vy` (graines) ; `chute x y période décalage` (feuille). Réactions : `bulle x y` (la grenouille gonfle sa
gorge, une note monte, Pilou sursaute puis a un peu peur), `rond` (un rond dans l'eau ; au troisième, un poisson saute),
`graines x y` (le pissenlit lâche ses graines).

Un décor sans section garde une scène par défaut (sol à 77, place 30, sans acteurs) : Pilou y vit déjà, sans bêtes.

**Juger une scène** : `python3 outils/sprites/planches_theatre.py [dossier] [campagne] [décor]` →
`theatre-<campagne>-<décor>.gif` (Pilou entre, on le touche, on touche chaque chose sensible, il s'en va) et une
planche d'images clés.

## Sur Windows

`VueTheatre.cs` affiche (image 192 × 80 réécrite seulement quand elle change, agrandie d'un facteur entier sans
lissage) ; `FenetreAventure.cs` raconte :

- un message de Pilou qui s'écrit : la scène prend son lieu (travelling de 1,2 s depuis le lieu précédent : l'ancien
  décor part à gauche, le nouveau arrive, Pilou marche au milieu), Pilou revient s'il était parti, prend l'humeur du
  message et parle pendant l'écriture ; la boîte montre la réplique lettre à lettre ; ensuite, le temps de la lire
  (38 ms par lettre, 1,6 à 7 s), « ▼ » ; un clic dans la boîte ou Espace passe à la suite ;
- des messages déjà lus (rattrapage à l'ouverture) : pas de travelling, Pilou entre simplement dans le dernier lieu ;
- un choix (ou « vas-y ») qui mène à une attente ou un repos : Pilou sort de la scène en marchant ; la fenêtre ouverte
  pendant une attente montre le lieu sans lui ;
- survoler un choix : Pilou regarde vers lui ; la souris sur la scène : il la suit des yeux, la main apparaît sur ce
  qui répond.

Choisir, repartir et la fin se posent sur la scène ; une attente, une épreuve, « mettre de côté » s'affichent à la
place de la boîte. Le chapitre, le lieu et le sac sont à droite de la boîte.

## Ce qui reste (prochaines étapes)

1. **Scènes des trois grandes campagnes** (40 décors) : sol, places, acteurs et réactions propres à chaque lieu
   (mouettes, chat du port, brume qui glisse, paquets de données, bocaux…), avec de nouveaux acteurs.
2. **Les 29 personnages en pied** (`pied-<campagne>-<personnage>` : repos, clignement, parole, un geste à lui), placés
   sur `interlocuteur` quand le message les fait vivre. Un premier jet de Tudal existe dans les planches de l'atelier.
3. **Chorégraphies des choix** : un choix peut jouer un trajet (sauter de nénuphar en nénuphar) au lieu de la sortie
   simple.
4. **Le Pilou du bureau** : les quatre liens décidés (échos, bout de décor, départ et retour, objets du sac).

## Jamais vérifié sur un vrai appareil

La fluidité (douze images par seconde de 192 × 80 plus l'agrandissement) sur un PC modeste et sur téléphone ; l'échelle
à 125 et 150 % ; le travelling sur une machine lente.
