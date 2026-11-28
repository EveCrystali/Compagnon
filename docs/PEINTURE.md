# Peindre un paysage de campagne

Les décors des campagnes sont de grands paysages en pixel art, **480 × 240 à 2 px d'écran par pixel, cadre 2:1**,
peints par du code. Décision d'Antoine du 28 novembre 2026, après l'étude `docs/maquettes/paysages/` : « C minimum.
Pixel art ne doit pas rimer avec baisse de qualité/définition, c'est une règle à figer. » (règle 9 de `CLAUDE.md`).
Cette page suffit pour peindre un lieu neuf au même niveau.

| Fichier | Rôle |
|---|---|
| `outils/sprites/paysage.py` | le moteur : palette, peintre, plans, briques |
| `outils/sprites/decors_hd_<campagne>.py` | les lieux d'une campagne (une fonction par lieu) ; l'ajouter à `CAMPAGNES` dans `decors_hd.py` |
| `outils/sprites/decors_hd.py` | registre, écriture d'`assets/decors/`, référence, planches |
| `outils/sprites/paysages_etude.py` | l'étude d'origine, figée (ses montages PC et téléphone servent encore) |

```bash
py outils/sprites/decors_hd.py                  # tous les décors, la référence, les planches
py outils/sprites/decors_hd.py prologue mare    # un seul lieu (la référence n'est pas réécrite)
```

Il faut numpy et Pillow. Les planches sortent dans `docs/maquettes/paysages/<campagne>/` : `<lieu>.gif` (la boucle),
`<lieu>-avant-apres.png`, `<lieu>-pc.png`, `<lieu>-telephone.png`. Les montages reprennent le gabarit de l'étude :
l'étiquette du lieu, le texte et les places de Pilou et du personnage sont ceux du gabarit, pas ceux de la scène.

## Composer un lieu

```python
@decor("prologue", "mare", soleil=(112.0, 30.5), tons=HEURE_DOREE, nom="La mare")
def mare(P, tab):
    tab.plan("ciel", 0.0);      pg.ciel(P, haut=0.08)
    tab.plan("nuages", 0.08);   pg.cumulus(P, [...]); pg.barres(P, [...])
    tab.plan("lointains", 0.2); pg.crete(P, f, [ombre, base, lumière, brume])
    tab.plan("moyen", 0.5);     pg.pre(P, f_pre); pg.maison(...); pg.miroir(P, tab.derriere(), 47.4)
    tab.plan("premier", 1.0);   pg.sol(P, f_berge); pg.touffes(P, f_berge); pg.feuillage(P, haut)
```

1. **Lire le texte de la campagne** : ce que Pilou décrit dans ce lieu doit se voir (objets, bêtes, heure).
2. **Choisir la lumière** : une seule source, `soleil=(x, y)`. Toutes les briques la regardent.
3. **Choisir les tons** : un `Tons` par campagne et par heure (rampes du ciel, des lointains, de l'herbe, de l'eau).
4. **Peindre du fond vers nous**, un `tab.plan(nom, profondeur)` par plan. Premier plan sombre, plan moyen, lointains
   clairs et bleutés, ciel : c'est ce contraste qui donne la profondeur.
5. **Semer la vie** : dix à vingt petites choses qui bougent, liées à la phase `P.p`.
6. **Regarder**, à la taille d'écran (2 px par pixel). Puis une deuxième et une troisième passe.

**Coordonnées.** Tout se donne en « unités du monde » : x de 0 à 192, y de -16 (`pg.HAUT`, le haut du cadre) à 80, le
sol vers y = 78. De y = 0 à 80, ce sont les coordonnées des scènes d'avant ; le cadre 2:1 ajoute 16 unités de ciel ou
de plafond. La grille est deux fois et demie plus fine (un pixel = 0,4 unité) ; les fractions sont permises. Le peintre déborde de 6 unités de
chaque côté (`MARGE`) pour la parallaxe et le cadrage.

**Places à laisser lisibles.** Pilou se tient à gauche, son interlocuteur à droite (lire `assets/scenes/<campagne>.txt` :
`sol`, `place`, `interlocuteur`, en coordonnées d'avant). À cette définition Pilou est grand : environ 38 unités de
large et 45 de haut. Pas de fleur vive ni de détail important derrière lui ni derrière le personnage.

## Les briques

| Plan | Briques |
|---|---|
| Ciel | `ciel` (dégradé tramé, halo, étoiles, lune, disque), `cumulus`, `voiles`, `barres`, `oiseaux` |
| Lointains | `profil` (une ligne de crête par bruit), `crete`, `sapins`, `moulin` |
| Terres | `pre`, `champ`, `colline`, `bosquets`, `sentier`, `rive`, `grand_arbre`, `arbre_rond`, `peuplier` |
| Vie | `maison`, `fumee`, `linge`, `cloture`, `meule`, `mouton` |
| Eau | `miroir` (reflet calculé de `tab.derriere()`), `nenuphar`, `grenouille`, `canard`, `barque`, `libellule`, `pierre` |
| Premier plan | `sol`, `cailloux`, `touffes`, `fleurs`, `fleur`, `champignon`, `tronc`, `feuillage`, `lanterne`, `roseaux`, `lucioles` |
| Pinceaux de `P` | `rampe`, `remplir`, `volumes`, `ell`, `rect`, `poly`, `trait`, `courbe`, `point`, `bloc`, `crete` |

Une brique manque ? L'écrire dans le fichier de la campagne d'abord ; la monter dans `paysage.py` quand une autre
campagne s'en sert.

**Intérieurs.** Dans `paysage.py` : `dallage` (sol en perspective vers un point de fuite), `rai` (rai de lumière et sa
poussière), `voile` et `halo` (lumière, ombre ou brume posées en trame), `poussiere`, `roue` (engrenage). Dans
`decors_hd_grande_panne.py` (douze intérieurs) : `neon`, `voyant`, `sept` (afficheur à sept segments), `papiers`,
`affiche` (pictogramme sans texte), `cable`, `tickets`, `tour_dossiers`. Dans `decors_hd_phare_eteint.py` (nuit, brume,
mer) : `brume`, `phare`, `bougie`, `fanal`, `goeland`, `barque_a_sec`, `casier`, `pierres_de_taille`, `bidon`, `pendule`.
Dans `decors_hd_evolution.py` (le fond du jardin de Pilou, à trois heures : un lieu, une fonction, un paramètre
d'heure) : `pot_cabane`, `rose_tremiere`. Dans `decors_hd_petit_nuage.py` (montagne, neige, ciels) : `sommets` (roche et neige en crête), `deux_dents`, `meleze`,
`aiguilles`, `petit_nuage` (un nuage du troupeau, avec ses yeux), `flaque`, `cairn`, `bocal`, `brume_claire`. La profondeur d'un
intérieur vient du point de fuite, des éclairages et d'un premier plan sombre ; le « ciel » est le mur ou le plafond.

**`P.rampe(masque, valeur, rampe, trame)`** est le pinceau central : une valeur de 0 à 1 par pixel devient un ton de
la rampe, et les paliers se mélangent en damier ordonné sur la part `trame`. `trame=0` : aplats nets ; `0.7` : ciel.

**`P.volumes(boules, rampe, lumière)`** éclaire des boules comme des volumes : nuages, feuillages.

## Les tons

`Tons(ciel=[12], loin=[6], herbe=[5], eau=[9], …)`. Les briques lisent les tons en cours par `pg.T` :

| Nom | Sens |
|---|---|
| `CIEL[0..11]` | du zénith à l'horizon |
| `NUAGE[0..9]` | de l'ombre au ventre éclairé |
| `L0`…`L5` | lointains, du plus proche au plus brumeux |
| `S0`…`S4` | herbe et feuilles, du sombre au clair |
| `OR1`…`OR3` | liserés de lumière |
| `N0`…`N2` | premier plan à contre-jour |
| `EAU[0..11]` | neuf tons froids, puis les trois chauds du ciel |
| `BR1`, `BR2`, `M2`…`M4` | bois et murs |
| `D1`, `D2`, `P1`, `P3`, `O2`, `O3`, `LUM`, `LUM2`, `CREME`, `ENCRE`, `VIOLET`, `BLEU`, `SOL`, `BLANC` | toit, pierre, orange, lueurs, accents |

## Les pièges

- **67 couleurs au plus par décor** (une lettre par couleur dans le format). Un décor du prologue en a 56.
- **Jamais d'opposition rouge / vert** (Antoine est deutéranope) : orange, bleu, violet, crème, sarcelle.
- **La boucle doit se refermer** : tout mouvement passe par `onde(P.p, décalage)` ou par un tirage `(P.p + hasard) % 1`.
  Un déplacement continu (nuage qui traverse) ne boucle pas : le faire osciller.
- **Le hasard est `hz(i, j, graine)`**, jamais `random` : la même image à chaque lancement, sinon la référence change.
  Changer de graine suffit pour qu'un lieu ne ressemble pas à l'autre.
- **L'eau ne reflète que ce qui est déjà peint** : appeler `miroir` après les terres du même plan, avant ce qui flotte.
- **Un pré sans limite descend jusqu'en bas** et couvre l'eau : lui donner `jusque=` (un masque).
- **Les liserés continus font « pointillés »** : les rompre par un bruit lent, pas par un tirage par pixel.
- **Le damier n'est pas une matière.** À 2 px d'écran, une grande surface tramée se lit comme un grillage gris.
  Déclarer le lieu `@decor(..., matiere=True)` : les voiles, halos et rais se mélangent alors en tons pleins
  (`teinte`), et la trame de `rampe` ne sert plus qu'au passage étroit d'un ton au suivant. Une surface se peint en
  matière : pierre appareillée, veines du bois, enduit taché, dallage, deux ou trois tons posés avec la lumière du lieu.
- **Douze détails vivants au moins par décor**, dont trois qui racontent le texte de la scène : les lister dans la PR.
  S'il en manque, le décor n'est pas fini. Les briques de « petite vie » aident (`papillon_de_nuit`, `araignee`,
  `toile_araignee`, `goutte`, `souris`, `vapeur`, `avion_papier`, `etincelle`, `yeux`), mais un détail propre au lieu
  vaut mieux qu'un détail passe-partout.
- **Un décor se peint en profondeur, pas en aplats avec des objets posés.** L'étalon est `prologue/mare.png`. Ouvrir
  le décor à côté, en taille réelle ; écrire cinq faiblesses précises ; corriger ; recommencer au moins trois fois.
  Les critères : aucune zone de plus de 40 × 40 unités sans matière ni variation de ton ; une source de lumière, avec
  ses ombres portées, ses liserés éclairés et ses reflets ; les lointains pâlissent et bleuissent ; un élément de premier
  plan cadre ; six détails vivants au moins sont animés. Pour un intérieur : poser la géométrie d'abord (point de fuite,
  profondeur de chaque pixel), puis peindre chaque surface selon sa profondeur et son angle au jour (voir `hall` dans
  `decors_hd_grande_panne.py`).
- **Un sol poli reflète** : `reflet(P, masque, tab.derriere(), axe)` mélange à chaque pixel du sol la couleur qui se
  trouve à la même distance au-dessus de la ligne `axe`. Il ne voit que les plans déjà terminés (`tab.derriere()`), pas
  le plan en cours. Une lumière colorée dans un sol clair ne se lit pas en mélange (`voile` retombe sur le beige) : la
  poser en traînées de ton franc (`P.remplir` sur un tirage `hz` par ligne).
- **Une lumière calculée plutôt que posée après coup** (`decors_hd_phare_eteint.py`, troisième passe) :
  `lumiere(P, sources)` donne à chaque pixel sa part de lumière, et chaque surface se peint par
  `P.rampe(masque, teinte × lumière, rampe)` avec une rampe qui va de l'ombre froide à la lumière chaude (`R_BOIS`,
  `R_GRANIT`, `R_PLATRE`, `R_FROID`…). Une ombre portée se retire de la lumière avant de peindre le sol. Les matières :
  `lames` (planches veinées, nœuds, joints), `appareil` (pierres de taille au biseau éclairé), `enduit`, `plancher`,
  `paves` (dalles mouillées, lune et feux), `flammes`, `fumerolle`, `boule_verre`, `cylindre`, `lisere`. Piège :
  `voile` et `teinte` choisissent le ton le plus proche parmi tous les tons du décor, herbe comprise ; sur un mur gris
  ou une brume, ils tirent vers le sarcelle. Peindre alors la brume en tons pleins (`nappe` dans `port_trebrume`).
- **Les bêtes qui réagissent sont des acteurs, pas du décor** : grenouille, canard, escargot (et ce que la scène rend
  cliquable) sont dessinés par la session des personnages (`assets/sprites-hd/acteur-*.txt`) et posés par la scène.
  Le décor peint leur place (le nénuphar, la feuille, l'eau) et la laisse vide.
- **Contenu original** : aucune forme, aucun cadrage repris d'un jeu ou d'une image existante.
- **Cohérence d'une campagne** : mêmes tons, mêmes repères (dans le prologue : la maison, la colline et son arbre),
  l'heure qui avance d'un lieu à l'autre.

## Ce qui sort

`assets/decors/decor-<campagne>-<lieu>.txt`, au format de [SCENES-HD.md](SCENES-HD.md) (§ 3), et
`outils/sprites/decors-hd-reference.txt`. Chaque `tab.plan(nom, profondeur)` devient un plan du fichier (cinq au
plus ; le premier doit couvrir tout le cadre). Un plan qui ne bouge pas n'est écrit qu'une fois : mettre ce qui
bouge dans peu de plans allège le fichier et le travail du moteur.

**Ne repeindre que ce qui change.** `py outils/sprites/decors_hd.py <campagne> <lieu> [<lieu>…]` repeint ces lieux
(une à deux minutes chacun) et réécrit quand même toute la référence : les autres décors sont relus dans
`assets/decors/`. Avant une PR : fusionner `main`, puis relancer cette commande sur les lieux touchés. Le lancement
sans argument repeint tout (25 minutes) et ne sert plus qu'après un changement d'une brique de `paysage.py`.

**Après tout changement d'un décor**, régénérer aussi la référence du Théâtre, qui porte l'empreinte de chaque plan :
`py outils/sprites/theatre_hd.py` (réécrit `outils/sprites/theatre-hd-reference.txt` ; les tests du PC et du
téléphone la comparent aux fichiers de `assets/decors/`). Sans cela, la CI échoue.

Par campagne : `docs/maquettes/paysages/<campagne>/planche.png` (tous les lieux), et les montages PC et téléphone de
deux lieux (table `MONTAGES` de `decors_hd.py`).
