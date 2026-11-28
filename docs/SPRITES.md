# Sprites de Pilou

Pilou et tous ses objets sont dessinés **une seule fois**, dans `assets/`, et lus tels quels par le PC
(ressources embarquées de `PilouBureau.exe`) et par l'app Android (ressources Java de l'APK).

| Fichier | Contenu |
|---|---|
| `assets/sprites/<id>.txt` | un sprite (plusieurs images s'il est animé) |
| `assets/index.txt` | la liste des identifiants (Android ne sait pas lister un dossier de ressources) |
| `assets/sprites2x/<id>.txt` | le même sprite redessiné deux fois plus fin, s'il l'a été (rendu fin, voir plus bas) |
| `assets/index2x.txt` | la liste des sprites redessinés en fin |
| `assets/teintes.txt` | couleurs de Pilou : contour, ombre, base, clair |
| `assets/tenues.txt` | tenue d'activité → sprites portés |
| `assets/plats.txt` | recette → sprite du plat |

## Grille

Pilou se dessine sur une grille de **48 × 56**, la même partout, à la taille d'affichage d'avant
(un pixel de cette grille vaut 104/48 unités WPF sur le PC), et, en rendu fin, sur la grille double 96 × 112. Le corps est procédural (une ellipse ombrée
en trame, un reflet, un cerne d'un pixel) ; le visage, l'antenne, l'étincelle et tout ce qu'il porte
viennent des sprites. Trois rendus suivent la même règle et tombent sur les mêmes pixels :
`outils/sprites/rendu.py` (référence), `apps/PilouBureau/RenduPilou.cs`, `android/.../RenduPilou.java`
— vérifié par `RenduTests.cs` et `RenduPilouTest.java` sur les poses de `outils/sprites/rendus-reference.txt`
(et de `rendus-reference-2x.txt` pour le rendu fin).

## Rendu fin (2×)

Le rendu existe à deux échelles. **1** : la grille 48 × 56 de toujours, inchangée au pixel près. **2** : le
**rendu fin**, sur une grille **96 × 112**, pour tous les endroits où Pilou est affiché assez grand (portraits et
récompenses des campagnes, accueil et boutique du téléphone, bureau Windows).

- **Corps** : calculé directement à la finesse double (contour plus rond, cerne de deux pixels fins, trame à trois
  paliers — un quart, un demi, trois quarts — au lieu du seul damier, reflet en croissant, antenne qui se courbe,
  pieds arrondis). Mêmes grandeurs que le 1×, multipliées par deux, arrondies au pixel fin : les animations
  (respiration, saut, assis, tremblement…) tombent aux mêmes endroits.
- **Sprites** : si `assets/sprites2x/<id>.txt` existe (même format, mêmes ancrages × 2), c'est lui ; sinon le
  sprite 1× est **agrandi automatiquement**, une fois, au premier usage.
- **Agrandissement automatique** : règle **MMPX** (Morgan McGuire et Mara Gagiu, « MMPX Style-Preserving Pixel Art
  Magnification », 2021). Chaque pixel devient 2 × 2 pixels pris parmi lui-même et ses voisins : ni flou, ni
  nouvelle couleur. Par rapport à EPX / Scale2x, elle garde les cernes sombres d'un pixel, traite les croisements et
  lisse aussi les pentes 2:1. Les couleurs se comparent par leur lettre de palette, le vide compte comme une
  couleur, la « clarté » d'une couleur vaut (r + v + b + 1) × (256 − alpha) (256 pour le vide ; les références
  `@contour`… prennent les valeurs du bleu). Strictement la même dans `rendu.agrandir` (Python),
  `Sprite.Agrandi` (C#) et `Sprites.agrandir` (Java).
- **Vérifié** par `rendus-reference-2x.txt` (les poses de référence à l'échelle 2) et `agrandis-reference.txt`
  (chaque sprite agrandi), dans `RenduTests.cs` et `RenduPilouTest.java`.

| | Échelle 1 | Rendu fin |
|---|---|---|
| Python | `rendu.rendre(pose, B, T, TEN)` | `rendu.rendre(pose, B, T, TEN, 2)` |
| C# | `RenduPilou.Rendre(allure, banque)` | `RenduPilou.Rendre(allure, banque, 2)` (ou `out geo, debord, 2, tampon`) |
| Java | `RenduPilou.rendre(allure, banque, geo)` | `RenduPilou.rendre(allure, banque, geo, 2)` (ou `…, 2, tampon`) |

La géométrie rendue (`Geometrie`) reste en pixels de la grille 48 × 56 aux deux échelles. Un `TamponRendu` (C#) ou
`RenduPilou.Tampon` (Java) gardé d'une image à l'autre évite toute allocation des grilles.

**Où il sert.** Téléphone : `new PilouVue(contexte, pixel, true)` passe en fin dès qu'un pixel fin fait au moins
2 pixels de l'écran (accueil, essayage, installation, bulle flottante sur les écrans denses), et arrondit alors sa
taille pour qu'un pixel fin tombe sur un nombre entier de pixels ; sinon elle reste en 1×. PC : réglage
**« Dessin fin »** du menu (activé par défaut). La fenêtre de Pilou prend l'échelle qui met un pixel fin sur un
nombre entier de pixels physiques à toutes les mises à l'échelle de Windows (`Placement.PixelsParPixelFin`,
`Placement.Echelle`), et ce qui l'accompagne suit (sprites fins, tailles ramenées à des pixels entiers :
`Finesse.Net`, `Pixels.Affiner`). Décoché : le rendu d'origine.

### Redessiner un sprite en 2×

Les dessins sont faits de formes (`toile.py` : ellipses, polygones, lignes, cernes). Pour le rendu fin, les mêmes
fonctions de dessin sont **rejouées sur une toile deux fois plus fine** (`toile.ECHELLE = 2`) : les coordonnées
restent celles de la grille 1× (les demi-unités sont permises), les formes sont calculées à la finesse double, les
motifs écrits à la main sont agrandis par la règle commune.

1. Ajouter l'identifiant à `SERIE` dans `outils/sprites/fin.py`.
2. Au besoin, lui donner une retouche dans `outils/sprites/retouches_fines.py` : une recette en quelques mots
   (`"L:#f69d50 O:#f69d50 P:#6a5acd:12"` : liseré clair, ombre, plis, mailles, couture, reflet) ou une fonction
   décorée par `@retouche("id")` ; ou, dans la fonction de dessin elle-même, un bloc `if toile.fin():` qui ajoute
   en pixels fins ce que la grille 1× ne peut pas porter (`t.pf`, `t.motif_fin`, demi-unités).
3. `python3 outils/sprites/generer.py && python3 outils/sprites/planches_hd.py`, regarder
   `planches/hd/cosmetiques-redessines.png`, corriger ; puis `python3 outils/sprites/reference.py`.

Seconde série (`fin.SERIE2` : boutique garnie, tenues d'activité, météo, créatures et trophées d'expédition, 133
sprites) : rejouée en fin comme la première ; quand un dessin est fait de pixels posés à la main (le rejeu ne serait
qu'un agrandissement au plus proche voisin), sa base fine est l'agrandissement commun, puis `retouche_auto` pose un
liseré de lumière et une ombre d'un pixel fin sur ses couleurs principales (ou une recette de `RECETTES2`). Avant /
après : `python3 outils/sprites/planches_campagnes.py` (`redessines-<n>.png`).

Quatrième série (`fin.SERIE4` : variantes d'évolution, poufs, polaroïds, bonus d'ensemble, icônes, accessoires, objets
tenus en main, particules — 96 sprites) : **aucune finition générique**. Chaque sprite a son dessin fin, écrit à la main
dans `finition_lot3.py` (variantes), `finition_effets.py` (bonus, pluies), `finition_objets*.py` (icônes, accessoires,
objets) et `finition_particules.py` (confettis, bulles, mousse, feu...) : soit redessiné en pixels fins à partir de ses
formes (même silhouette, mêmes ancrages, mêmes images et durées), soit rejeu fin retouché couleur par couleur. Les pinceaux
communs (cœur, étincelle, bulle, note) sont dans `fins.py`, appelés par les primitives d'origine quand `fins.ACTIF`.
Reprises du lot précédent : `plat-friture`, `soin-faim`, `prise-ecrevisse` (`finition_objets3.py`).

`python3 outils/sprites/fin.py` liste les sprites redessinés et ceux encore agrandis automatiquement
(`planches/hd/rapport.txt`). Le visage est entièrement dessiné en pixels fins (`visage_sprites.py`).

## Humeurs et tenues de voyage (campagnes)

Dix humeurs en plus des expressions d'origine, aux deux échelles (`Allure.Expr` / `allure.expr` / `Pose.expr`) :
`joie`, `peur`, `triste`, `surpris`, `determine`, `fatigue`, `tendre`, `colere`, `malice`, `neutre`. Chacune a ses
yeux (`oeil-<humeur>`, avec sourcil ; `oeil-malice-d` : œil droit dessiné à part), sa bouche (`bouche-<humeur>`),
parfois une marque posée sur l'ancre des yeux (`marque-triste` : larme ; `marque-peur` : goutte ; `marque-colere` :
signe de colère) et ses joues (`joie`, `tendre`). Chaque humeur se lit à sa forme, jamais à une couleur seule.

Huit tenues de voyage (`voyage_sprites.py`, `assets/tenues.txt`), pour Pilou « occupé » pendant une attente :
`Tenue = "voyage-marche"` (baluchon, bâton, pas sur place), `voyage-course` (bandeau, foulée), `voyage-bateau`
(barque, rame, vagues), `voyage-grimpe` (corde), `voyage-nage` (bouée), `voyage-nuit` (bonnet, couverture, lune),
`voyage-cache` (buisson, seuls les yeux dépassent), `voyage-attend` (assis, il regarde sa montre). La pose de
chaque mode (marche, tangage, guet…) est imposée par le rendu commun (`voyager` / `Voyager`) : il suffit de
donner la tenue. Sur le PC : `Pose.Tenue` et `Pose.Humeur` ; essais `--essai=tenue:voyage-marche`,
`--essai=humeur:joie`, `--essai=dessin:origine`.

## Décors et illustrations des campagnes

Tout ce que déclare une fiche `assets/campagnes/<campagne>/campagne.json` a son dessin, aux deux échelles, dessiné
nativement en fin (`fin.ids_campagnes`) :

| Sprite | Format | Contenu |
|---|---|---|
| `decor-<campagne>-<décor>` | **96 × 40** (fin **192 × 80**), opaque, `ancre: aucun` | le décor d'une scène (`decors` de la fiche, champ `decor` des nœuds), en bandeau paysage |
| `<objet>` (l'identifiant de l'objet) | selon l'emplacement | objet exclusif `"portable": true` : `slot` = son `emplacement`, ancre de cet emplacement (`tete`, `cou` ; `dos` → `cou` en `couche: derriere` ; `main`) |
| `souvenir-<campagne>-<souvenir>` | 24 × 24 (48 × 48) | timbre dentelé, une scène dedans, liseré à la couleur de la campagne |
| `campagne-<campagne>` | 32 × 32 (64 × 64) | vignette de la liste des campagnes (carte aux coins ronds) |
| `ton-humour`, `ton-mystere`, `ton-emotion`, `ton-epique` | 12 × 12 (24 × 24) | emblème du ton, chacun d'une **forme** à lui : rond rieur, losange à serrure, cœur, étoile |

**Décors.** Format commun paysage 96 × 40 (rapport 2,4 : un bandeau d'en-tête), 192 × 80 en fin. Trois plans au
moins, une lumière qui vient d'un côté, un détail charmant par décor ; tous s'animent en boucle (6 à 8 images, voir
« Animations des campagnes »), avec autant d'images et la même `duree` aux deux échelles. Une palette
restreinte par campagne (`PAL` de chaque module, et ses rampes de lumière) : prologue (fin d'après-midi dorée, herbes
sarcelle), grande-panne (plastique beige, néons cyan et orange, gelée sarcelle), phare-eteint (nuit bleue, brume,
granit, lanternes orange), petit-nuage (ciels lavés, soirs lavande, neige, mélèzes dorés). Les lecteurs n'ont aucune
limite de taille ; une illustration garde au plus 62 couleurs (les lettres de `toile.LETTRES`).

Modules : `decors_campagnes.py` (registre, format), `decors_prologue.py`, `decors_panne.py`, `decors_phare.py`,
`decors_nuage.py` ; `peinture.py` (pinceaux qui travaillent pixel par pixel sur la grille réelle : dégradés tramés,
reliefs à crête éclairée, brume en paliers, lueurs en anneaux le long des rampes de la palette — rejoués en fin, ils
donnent une trame et des liserés d'un pixel fin au lieu d'être agrandis) ; `campagnes_sprites.py` (objets exclusifs,
souvenirs, vignettes, emblèmes). Planches : `python3 outils/sprites/planches_campagnes.py [dossier]`
(`decors-<campagne>.png`, `exclusifs-portes.png`, `souvenirs.png`, `vignettes.png`).

**Afficher une illustration** (rien à charger de plus : la banque commune les a) :

| | Décor | Souvenir, vignette, ton |
|---|---|---|
| C# | `Illustrations.Decor(Banque.Commune, campagne, etat.Decor, 2)` → `Sprite?` (null : garder le repli) | `Illustrations.Souvenir(b, campagne, id)`, `Illustrations.Vignette(b, campagne)`, `Illustrations.Ton(b, ton)` |
| Java | `Sprites.decor(Sprites.banque(), campagne, etat.decor, 2)` → `Sprite` ou `null` | `Sprites.souvenir(b, campagne, id, 2)`, `Sprites.vignette(b, campagne, 2)`, `Sprites.ton(b, ton, 2)` |

Le sprite rendu se peint comme tout objet de la banque : `Banque.Grille(s, t)` ou `Pixels.Sprite(id, …)` /
`Apercu.Sprite(id, t)` sur le PC, `Sprites.dessiner(peintre, s, x, y, p, t, false)` sur le téléphone (`t` en ms pour
les décors animés). Échelle 2 = dessin fin natif (192 × 80) ; échelle 1 = 96 × 40.
Vérifié par `IllustrationsTests.cs` et `IllustrationsTest.java` (chaque décor, souvenir, objet exclusif et vignette
déclaré a son sprite, au bon format, opaque, natif en fin ; chaque exclusif se voit porté aux quatre stades ; les
emblèmes de ton ont quatre silhouettes différentes), et par quatre poses de `rendus-reference.txt`.

## Décors haute définition (480 × 240)

Décision d'Antoine du 28 novembre 2026 (étude `docs/maquettes/paysages/`, règle 9 de `CLAUDE.md`) : les décors passent
à **480 × 240 au minimum**, 2 px d'écran par pixel (960 × 480), cadre 2:1.
Ils sont peints par `outils/sprites/paysage.py` ([PEINTURE.md](PEINTURE.md)) et écrits par
`py outils/sprites/decors_hd.py` (numpy et Pillow, donc hors de `generer.py`).

**Format provisoire.** La session du Théâtre écrit `docs/SCENES-HD.md` (tailles, plans de parallaxe, format, noms) :
c'est lui qui fera foi, et les décors seront réexportés à son format. D'ici là, rien ne lit ces fichiers : les décors
192 × 80 d'`assets/sprites2x` restent en service.

| | |
|---|---|
| Emplacement | `assets/decors/decor-<campagne>-<décor>.txt` : mêmes identifiants que les décors actuels |
| Embarquement | Android : déjà pris (tout `assets/` est en ressources) ; PC : une ligne `EmbeddedResource` à ajouter |
| Coordonnées | 2,5 × celles du décor fin actuel, plus 40 pixels de ciel en haut : pixel = (2,5 x, 2,5 y + 40) ; le sol vers y = 235 |
| Référence | `outils/sprites/decors-hd-reference.txt` : `id largeur hauteur images duree` puis l'empreinte FNV-1a de chaque image (pixels ARGB `0xFFrrggbb`, rangée par rangée, même calcul que `theatre.fnv`) |

**Format « décor compact »** (texte UTF-8, fins de ligne LF) :

```
# commentaire
id: decor-prologue-mare
taille: 480 240
duree: 200                       ms par image
palette: a=#5b6fc4 b=#7384d0 …   une lettre par couleur, 67 au plus, décor opaque
images: 8
12a3b.c200.                      puis images × hauteur lignes, sans séparateur
```

- Une ligne est une suite de plages `[n]c` : `n` décimal (absent : 1), `c` une lettre de palette, ou `.` pour « comme
  le pixel de l'image précédente » (jamais dans la première image). La somme des `n` vaut la largeur.
- Lettres permises : `a-z A-Z ! $ % & * + - / < > ? @ ^ _ ~`. Jamais un chiffre (ce sont les longueurs) ni `.`.
- Le lecteur de référence est `decors_hd.decoder` (une trentaine de lignes) ; C# et Java le refont à l'identique, sans
  bibliothèque.

**Poids mesuré** sur les six décors du prologue (8 images chacun) : 81 à 161 Ko, 682 Ko en tout, contre 901 Ko
*par décor* à une lettre par pixel (÷ 6 à 11) ; 256 Ko une fois compressés (APK). Extrapolé à 46 décors : ≈ 5,2 Mo
(2 Mo compressés), à comparer aux 4,3 Mo des décors d'aujourd'hui.

**Ce qui bouge.** D'une image à la suivante, 1,2 à 6 % des pixels changent (6 % : la mare et ses reflets) ; le « . »
du format les isole, un moteur peut ne redessiner que les plages qui ne sont pas des « . ».

## Personnages en haute définition

Les personnages en pied des campagnes sont **redessinés** à l'unité de la scène HD (480 × 240 unités, 2 px d'écran par
unité ; règle 9 de `CLAUDE.md`), jamais agrandis. Format et nommage : [SCENES-HD.md](SCENES-HD.md), § 6.

| Module (`outils/sprites/`) | Rôle |
|---|---|
| `pinceau_hd.py` | la feuille et ses pinceaux, en Python pur : volumes éclairés d'en haut à gauche (`boule`, `tube`, `tour`, `poly`), rampes de trois à cinq tons, trame ordonnée seulement au passage d'un ton à l'autre, cerne teinté par matière, traits « pixel parfait » |
| `personnages_hd.py` | le registre (`PERSOS`), l'état (`Etat`), le visage commun (`oeil`, `sourcil`, `bouche`), Grumeau, Lison, Brouillon le petit nuage |
| `personnages_hd_panne.py` | les douze autres personnages de « La Grande Panne » |
| `personnages_hd_export.py` | l'export `assets/sprites-hd/pied-*.txt` et la référence `personnages-hd-reference.txt` |
| `planches_personnages_hd.py` | planches de contrôle et GIF (Pillow, outil de contrôle seulement) |

```bash
py outils/sprites/personnages_hd_export.py            # écrit assets/sprites-hd et la référence
py outils/sprites/planches_personnages_hd.py          # planches et GIF, dans docs/maquettes/personnages
```

- **État d'un dessin** : humeur, paupières (ouvertes, mi-closes, fermées), bouche (0 à 3), souffle, phase des petits
  mouvements (sable, nattes, traîne, curseur). Chaque humeur change une forme (sourcils, paupières, bouche, bras,
  goutte), pas seulement une couleur.
- **Fichiers** : `pied-<campagne>-<id>.txt` (neutre) et `pied-<campagne>-<id>-<humeur>.txt`, cinq images (repos,
  inspiré, yeux fermés, bouche entrouverte, bouche ouverte), même toile et même ancrage pour toutes les humeurs d'un
  personnage. Ceux qui flottent ont leur vide sous eux dans la toile.
- **Sens** : le fichier regarde vers la droite (SCENES-HD.md) ; c'est le miroir du dessin, pensé pour la place
  habituelle (à droite de Pilou). Retourné par le moteur, le personnage retrouve sa lumière en haut à gauche et ses
  inscriptions à l'endroit (« Ctrl », « 13 37 », « 404 »). Non retourné, elles sont à l'envers : au moteur de le savoir.
- **Lisibilité** : chaque personnage se vérifie sur fond sombre, fond clair et décor (planche de groupe) ; une matière
  sombre porte un liseré clair côté lumière (le chapeau du Balayeur).
- **Toise** : une par campagne, sur la planche de groupe, Pilou fin pour repère.

| Campagne | État | Planche de groupe |
|---|---|---|
| La Grande Panne (13) | dessinés et exportés (33 fichiers, 194 Ko) ; pas encore lus par le moteur | [groupe-grande-panne.png](maquettes/personnages/groupe-grande-panne.png) |
| Le phare éteint (7) | Lison dessinée (essai) ; six à faire | — |
| Petit Nuage (9) | Brouillon dessiné (essai) ; huit à faire | — |
| Acteurs de scène | à faire | — |

Planches par personnage (toutes les humeurs, sept images) et GIF : `docs/maquettes/personnages/<campagne>-<id>.png`
et `.gif`.

## Animations des campagnes

Les campagnes vivent : décors en boucle, portraits des personnages, écriture lettre à lettre, transitions, fond qui
respire. Tout ce que le PC et le téléphone doivent calculer de la même façon (quelle image à quel instant, combien de
lettres écrites, l'ordre du volet, les couleurs et les particules du fond, quand tombent les récompenses) est dans
`outils/sprites/animations.py`, en arithmétique entière ; `reference.py` en écrit `outils/sprites/animations-reference.txt`,
relu ligne à ligne par `AnimationsCampagneTests.cs` (`AnimationsCampagne.cs`) et `AnimationsTest.java` (`Animations.java`).

**Décors animés.** Les 46 décors bouclent sur **6 à 8 images, de 180 à 250 ms** (4 à 5,5 images par seconde). Rien
n'est redessiné à la main : `decors_campagnes.toiles` rejoue le dessin de chaque image avec une **phase** de boucle
`decors_campagnes.PHASE` (0 ≤ p < 1) ; les outils des décors s'en servent (`dc.onde()` : flammes qui vacillent, reflets
de la mer, étoiles du ciel de nuit, vagues, nuages qui dérivent d'un pixel, draps, drapeau, ailes des oiseaux,
balancier qui frémit), puis les **effets d'ambiance** de `ambiances_decors.py` se posent dessus : `faisceau` (le phare
qui tourne), `reflets`, `brume` (ondes stationnaires : elle respire sans filer), `pulse` (lanternes, néons, poêle,
flaques de lumière), `fumee`, `particules` (poussière dans un rai, neige, bruine, aiguilles de mélèze, braises, graines),
`pluie`, `vent` (herbes, feuillages : le haut balance, la base reste plantée ; seulement sur les couleurs données, pour
ne pas faire trembler la trame du ciel), `onduler` (eau), `scintille` (points clairs isolés qui s'éteignent chacun à
son tour), `balayage` (reflet sur une vitre, une lentille, une barre de chargement). Chaque effet est une fonction
périodique de la phase : la dernière image retombe sur la première sans à-coup. Couleurs prises dans la palette du
décor (62 au plus). Réglage par décor dans `REGLES` : nombre d'images, durée, « garder » l'ancienne alternance du dessin.

**Portraits des personnages** (`portraits_campagnes.py`, voir LORE.md) : `portrait-<campagne>-<personnage>` (neutre) et
`portrait-<campagne>-<personnage>-<expression>`, 32 × 32 (fin 64 × 64, natif), fond transparent, cerne sombre, cinq
images dans un ordre fixe, déclaré par une clé que les anciens lecteurs ignorent :

```
portrait: repos 0 1 cligne 2 parle 3 4
```

0 repos ; 1 inspiré (le haut du corps monte d'un pixel) ; 2 yeux fermés ; 3 et 4 bouche mi-ouverte et ouverte.
`animations.image_portrait(n, duree, t, parle, niveau)` choisit : clignement 150 ms toutes les 4,3 s, respiration
toutes les 900 ms, parole 3-4-3-0 à 140 ms tant que Pilou écrit une réplique du personnage (« … »). Les expressions
sont celles de Pilou (`joie`, `peur`, `triste`, `surpris`, `colere`, `tendre`, `malice`…) ; une expression non dessinée
retombe sur le visage neutre (`AnimationsCampagne.Portrait`, `Animations.portrait`). 29 personnages, 69 portraits.

**Niveaux.** Réglage « animations des campagnes » : `completes` (tout), `reduites` (décors fixes, clignement seul,
fondu au lieu du volet, pas de particules), `aucune` (rien ne bouge, texte écrit d'un coup). Le réglage du joueur décide ;
tant qu'il n'a rien choisi (réglage vide), le système donne la valeur de départ : `aucune` s'il demande moins
d'animations (Windows : « Afficher les animations » coupé ; Android : échelle des animations à 0), sinon `completes`.

**Le théâtre** (scène vivante de la fenêtre Aventure : mini-Pilou en pied, acteurs d'ambiance, réactions aux clics,
travelling entre deux lieux) a sa page : [SCENES.md](SCENES.md). Ses sprites (`scene-pilou`, `acteur-*`) n'existent qu'en
dessin fin.

**Mémoire et charge.** Chaque image n'est rendue qu'une fois, puis gardée dans un cache borné (28 sprites sur le PC,
24 sur le téléphone : au plus ~10 Mo) ; une image ne change à l'écran que lorsque son numéro change (4 à 7 fois par
seconde pour un décor, ~7 fois pour un portrait qui parle). Le téléphone lit les décors et portraits fins **à la
demande** (`Banque.aLire`, 12 gardés) : ils ne ralentissent pas le démarrage. Fichiers : environ 5,5 Mo de texte de plus
dans `assets/sprites2x` (6 images par décor), compressés dans l'APK.

**Planches** : `python3 outils/sprites/planches_animations.py [dossier] [filtre]` → `decors-<campagne>.png` (toutes les
images côte à côte, la première répétée à droite pour juger la boucle), `decors-<campagne>.gif` (mosaïque à la vitesse
réelle), `portraits-<campagne>.png` et `.gif` (repos puis parole, avec le choix d'image commun).

## Vie du personnage

Pilou ne bouge pas plus souvent : les mouvements déjà là changent de forme. Règles communes dans
`outils/sprites/vie.py` (arithmétique entière), `Vie.cs` et `Vie.java`, vérifiées par `vie-reference.txt` ; le dessin
est dans `rendu.py` et les deux `RenduPilou`, vérifié par les poses `vie=1`, `etire=`, `antenne=`, `atterri=`,
`lumiere=` de `rendus-reference*.txt`.

| Quoi | Complètes | Réduites | Aucune |
|---|---|---|---|
| Saut (petit saut, caresse, fête) | il se ramasse, décolle étiré, arc en parabole, s'écrase et rebondit (ressort amorti), l'antenne suit 60 ms en retard | arc en parabole seul | saut d'avant (sinus) |
| Lâché, il retombe | ressort amorti, deux bouffées de poussière | écrasement d'avant | écrasement d'avant |
| Ombre en l'air | s'éclaircit en trame (un pixel sur deux) | ombre pleine | ombre pleine |
| Marche | une bouffée de poussière du pied arrière tous les deux pas | — | — |
| Lumière du moment | matin crème, soir violet, nuit bleu nuit (10 à 18 %) ; ni aube ni couchant par temps couvert ; l'alerte (inquiet) ne change pas | pareil | — |

Le niveau est celui du réglage « ✧ » des campagnes (et « aucune » si le système coupe les animations). Déjà là avant,
et gardés : respiration, clignement, balancement de l'antenne, regard qui suit la souris de près (PC, réglage
« suit la souris »), confettis et cœurs de la scène, poussière de course.

Essai sur le PC : `--essai=vie[:completes|reduites|aucune][:heure]` (saut, marche aller-retour, chute, en boucle de
9 s). Planches : `python3 outils/sprites/planches_vie.py` → `sauts.png`, `receptions.png`, `lumieres.png`,
`avant-apres.gif` dans `outils/sprites/planches/vie`.

## Saynètes de repos

Au calme, Pilou s'occupe tout seul quelques secondes, à la place d'une occupation ordinaire. La banque est
`assets/saynetes.txt`, écrite par `outils/sprites/saynetes.py` et lue telle quelle par `Saynetes.cs` et
`Saynetes.java` ; tirages et poses sont vérifiés des deux côtés par `saynetes-reference.txt`. Les accessoires sont
des sprites `sc-<nom>-<k>`, une image par étape (`saynetes_sprites.py`) : c'est la saynète qui choisit l'étape.

| Saynète | Poids | Condition | Trait dominant (poids × 3) | Ce qu'il fait |
|---|---|---|---|---|
| lit | 16 | stade 2 à 4, main libre | grand lecteur, amateur d'histoires | s'assoit avec le livre de lecture, suit les lignes, sourit à un passage |
| compte | 12 | main libre | chineur, veinard | assis, empile ses pièces une à une ; le compte est bon |
| etincelle | 10 | — | — | poursuit une petite étincelle à petits bonds, la rattrape sur l'antenne |
| endort | 8 | 12 h – 16 h, 20 h – 7 h | douillet | assis, clignements lents, bâillement, la tête tombe… et le sursaut |
| bord | 8 | — (miroir vers le bord le plus proche) | — | se penche par-dessus le bord, découvre le vide, recule |
| etire | 16 | — | lève-tôt | s'étire, un bras en l'air, les yeux fermés |
| ciel | 10 | — | tête en l'air, flâneur | regarde les nuages passer |
| danse | 8 | pas au travail | bon public | petite danse à petits bonds, notes de musique |
| flocon | 10 | décembre à février | — | un flocon descend sur son nez |
| feuille | 10 | septembre à novembre | — | une feuille lui tombe sur la tête, il se secoue |
| papillon | 10 | mars à août | — | un papillon passe, se pose sur l'antenne, repart |
| boit | 12 | tasse de café ou chocolat porté | douillet | assis, petites gorgées les yeux fermés |
| guette | 12 | lunette ou jumelles portées | voyageur | guette au loin, et tiens ! un petit bond |
| compagnon | 12 | un compagnon porté | câlin, bon voisin | un regard, un bond, un cœur sur l'antenne |
| etoiles | 10 | 21 h – 6 h | couche-tard | regarde les étoiles ; une étoile filante passe |
| peche | 10 | main libre | pêcheur du dimanche | assis, surveille sa canne ; le bouchon danse, plonge |
| bulles | 8 | — | tête en l'air | souffle une bulle de savon, la regarde monter, elle éclate |
| fredonne | 10 | — | siffloteur | fredonne les yeux fermés, les notes montent, il se balance |
| pirouette | 8 | pas au travail | — | tourne sur lui-même d'un petit bond |
| secoue | 8 | — | — | un frisson, il s'ébroue des pieds à l'antenne |
| grignote | 10 | main libre | gourmand | assis, grignote un biscuit ; des miettes |
| reve | 10 | — | tête en l'air, amateur d'histoires | assis, une petite pensée flotte au-dessus de sa tête |
| equilibre | 8 | — (miroir) | — | tient en équilibre, penche, se rattrape, fier de lui |
| souffle | 6 | — | — | souffle sur son antenne, l'étincelle vacille, il rit |
| hoquet | 4 | — | — | hic… hic… hic, puis plus rien |
| ecoute | 8 | — | — | tend l'oreille, à gauche, à droite… rien |
| eternue | 1 (rare) | — | — | éternue une bulle d'encre qui monte et éclate |
| salue | 1 (rare) | — (miroir) | — | salue… personne, et fait mine de rien |
| trebuche | 1 (rare) | — (miroir) | — | trébuche sur rien, tombe assis, fait mine de rien |
| voeu | 1 (rare) | — | — | fait un vœu, les yeux fermés ; une étoile filante, un cœur |

Réactions au monde (poids 0 : jamais tirées au sort ; sur le PC seulement, le téléphone n'a ni bord ni souris) :

| Réaction | Quand | Ce qu'il fait |
|---|---|---|
| freine | au bout d'une marche contre le bord de l'écran, une fois sur deux | freine, se penche vers le vide, le regarde, recule |
| lache | pris et lâché, une fois retombé (après le ressort de la réception) | un temps sonné, il se secoue, ça va |
| survol | la souris reste 6 s sur lui (une fois par survol, après le ronron) | lève les yeux, tente de l'attraper d'un bond, un cœur |

Règles :
- **Retenue** : seulement au calme (expression « repos »), jamais pendant la saisie, jamais caché (plein écran,
  visio) ; sur le PC, une chance sur trois à la place d'une occupation (une sur sept au travail), au moins 40 s entre
  deux (80 s au travail), jamais deux fois la même de suite ; sur le téléphone, une toutes les 25 à 45 s tant que
  il est affiché et animé. Interrompue dès que quelque chose se passe (caresse, IA qui attend, jeu, campagne, prise).
- **Rien à gagner** : aucune xp, aucune pièce n'est liée à une saynète.
- **Traits** : un trait parmi les trois dominants (docs/TRAITS.md) triple le poids des saynètes qui lui ressemblent
  (`trait=` dans la banque). Le poids seulement.
- **Éveil** : sans aucune session d'IA, Pilou est éveillé (« un compagnon de tout », docs/DECISIONS.md). Il ne dort
  que si tu t'absentes 10 min (2 min de minuit à 6 h), règle commune `endormi(heure, inactif)` vérifiée des deux côtés ;
  le téléphone sans PC (pas appairé, ou PC éteint) le montre éveillé, endormi seulement la nuit. Essai :
  `--essai=eveil:<secondes d'absence>[:<heure>]`.
- **Raccords** : chaque mouvement part de 0 et y revient (il se ramasse avant, retombe après) ; `saynetes.verifier()`
  le contrôle, ainsi que les durées (3 à 8 s).
- **Pas de faux signal** : les expressions qui disent quelque chose d'une session (concentre, attente, inquiet,
  surpris, grimace : roue, « ! » ou croix orange sur l'antenne) sont interdites dans les saynètes.
- **Réglage ✧** : complètes, tout ; réduites, sans saut, étirement ni penché (posture, regard, visage, objets) ;
  aucune, pas de saynète.

Essai sur le PC : `--essai=saynete[:<id>][:completes|reduites|aucune]` (toutes à la suite, ou une seule en boucle ;
les réactions aussi, par leur nom).
Planche : `python3 outils/sprites/planches_saynetes.py [dossier] [pas_ms]` → une bande par saynète dans
`outils/sprites/planches/saynetes`.

## Format d'un sprite

```
# commentaire
id: lunettes-rondes
slot: yeux             tete | yeux | cou | dos | main | compagnon | effet | visage | objet
ancre: yeux            point de Pilou où il se pose (ci-dessous) ; aucun pour un objet seul
decalage: -14 -1       coin haut-gauche par rapport à l'ancre, en pixels de la grille
couche: derriere       dessiné avant le corps (cape, aura) ; par défaut : devant
coiffe: oui            cache l'antenne (chapeaux)
duree: 250             ms par image quand il y en a plusieurs
portrait: repos 0 1 cligne 2 parle 3 4   (portraits de campagne seulement ; clé ignorée des anciens lecteurs)
palette: a=#1c2128 b=#b4dbff c=@contour
images:
..aaaa..
.abbbba.
---
(image suivante)
```

`.` est transparent. Une couleur `#rrggbbaa` porte sa transparence. `@contour`, `@ombre`, `@base`,
`@clair` prennent la teinte de Pilou (paupières, par exemple).

## Ancres

Calculées à chaque image d'après le corps (elles suivent la respiration, les sauts et les stades) :
`tete` (sommet du crâne, au centre), `yeux` (haut des yeux), `bouche`, `cou`, `corps` (centre),
`main` (flanc droit), `main-g` (flanc gauche), `pieds`, `cote` (au sol, à droite : compagnons),
`antenne` (pointe de l'antenne).

Ordre de dessin : couche arrière, ombre, corps, visage, antenne, puis dos, cou, visage, yeux, tête,
main, compagnon, effet. Les bottes de pluie (emplacement de boutique `pieds`) se posent sur l'ancre
`pieds`.

Boutique rétro (`outils/sprites/boutique_sprites.py`) : une cinquantaine d'objets répartis par emplacement
(`tete`, `yeux`, `cou`, `dos` — souvent `couche: derriere` —, `main`, `pieds`, `compagnon` sur l'ancre `cote`,
`effet`), six teintes (`pervenche`, `mandarine`, `miel`, `prune`, `acier`, `peche` ; les trois chaudes rejoignent
`CHAUDES`), les décors `fond-nuit`, `fond-foret`, `fond-plage`, `fond-arcade`, `fond-espace` (scènes 64 × 48,
`ancre: aucun`, dessinées derrière Pilou par l'app et l'aperçu de la boutique, jamais sur lui) et des icônes
d'interface (`cadenas`, `badge-boutique`, `pierre-calme`, `canne-doree`, `marmite-cuivre`). Les cadres de bulle
ne sont pas des sprites : `Boutique.Style` (PC) et `Boutique.style` (téléphone). Planches : `boutique-retro.png`,
`boutique-retro-stades.png` (stades 1, 3, 4, négligé, terne), `boutique-decors.png`.

Boutique garnie (`outils/sprites/garde_robe.py` pour le catalogue, `garde_robe_dessins.py` pour les dessins) :
140 articles de plus, rangés dans `assets/catalogue.txt` (lu tel quel par `Boutique.cs` et `Boutique.java` : numéro
stable, emplacement, prix, niveau, rareté 0–5, saison, ensemble, passage), les dix ensembles et leur effet bonus
(`bonus-<ensemble>`, ajouté aux objets quand l'ensemble est porté en entier), les paliers de collection, et neuf
teintes (`caramel`, `potiron` et `cuivre` rejoignent `CHAUDES`). Les titres (emplacement `titre`) et les cadres de
bulle ne sont pas des sprites. Planches de contrôle, une par rayon : `python3 outils/sprites/planches.py` →
`planches/boutique2/` (`rayon-*.png`, `vignettes-petites.png` à la taille de la boutique, `ensembles.png`).

Météo (`outils/sprites/meteo_sprites.py`) : `meteo-pluie`, `meteo-averse`, `meteo-eclair`,
`meteo-neige`, `meteo-brouillard`, `meteo-vent`, `meteo-soleil` (plein cadre, animés) et
`meteo-mouille`, `meteo-givre` (sur Pilou) ; les objets `impermeable`, `bottes-pluie`, `moufles`,
`eventail`, `parapluie-etoile`. `Meteo.Effet` (PC) et `Meteo.effet` (téléphone) choisissent lesquels
ajouter selon le temps et ce que Pilou porte. Planches : `python3 outils/sprites/planches.py`
(`meteo.png`, `meteo-2.png`, `boutique-meteo.png`).

## Stades d'évolution

1 Gouttelette (petit, yeux immenses, antenne courte) · 2 Pilou · 3 Pilou Nimbus (nuage à volutes,
deux bras, double antenne, gouttes qui tombent) · 4 Pilou Astral (élancé, cape-comète, couronne
d'étincelles en orbite, regard serein). L'animation d'évolution alterne la silhouette claire de
l'ancien et du nouveau stade de plus en plus vite, puis une gerbe d'étincelles révèle le nouveau.

## Ajouter ou retoucher un sprite

```
python3 outils/sprites/generer.py      # réécrit assets/ (sprites, sprites2x, index, tenues…) depuis les dessins
python3 outils/sprites/planches.py     # planches PNG de contrôle (outils/sprites/planches/)
python3 outils/sprites/planches_hd.py  # planches du rendu fin : avant / après, portrait, bureau (planches/hd/)
python3 outils/sprites/reference.py    # nouvelles empreintes si le rendu de Pilou change exprès (deux échelles)
```

Palette : bleus, oranges, argent, violets, jaunes, sables, neutres ; jamais d'opposition rouge / vert,
et chaque rareté ou état garde aussi un signe de forme. Un identifiant inconnu est ignoré sans erreur.

Petits gestes (`outils/sprites/gestes_sprites.py`, docs/NOTIFICATIONS.md) : `pouf-1` à `pouf-5` (fumée, une image
par étape, sur l'ancre `corps`), `clavier-mini` (devant Pilou assis, pattes à sa teinte qui tapent, touche enfoncée
d'un pixel), `appareil-photo` et `photo-flash` (ancre `yeux`), `polaroid-1` à `polaroid-4` (la photo glisse le long
du flanc et se développe), `enveloppe-notif` (ouverte, une lettre dépasse) et `enveloppe-close` (cachet rond),
brandies sur l'ancre `tete`. Pendant un geste, le PC retire de la tenue d'activité ce qu'elle tient en main
(`GestesPilou.TenueCompatible`) et passe le reste en objets : le rendu commun n'a rien de nouveau à savoir.

Sur le PC : `PilouBureau.exe --instantane=<png> --essai=tenue:code` (ou `objet:cape`, `stade:3`,
`evolution`, `soins:faim|proprete|moral|boude|amadoue|dos|rayonnant|lavage|calin|espiegle`) rend la fenêtre dans
une image.

Soins : icônes de besoin `soin-faim`, `soin-proprete`, `soin-moral` ; en-cas `encas-*` ; `mousse`
(toilette) et `rayonnant` (effets animés, 4 images) ; variantes `variante-calin-<stade>` et
`variante-espiegle-<stade>` (visage), avec `-tete`. Bouderie : `oeil-boude` et `bouche-boude` (choisis
par le rendu quand l'allure dit `Boude` au repos), `boude-nuage` (nuage gris qui bruine),
`boude-eclaircie` (amadoué : un soleil pointe), `boude-bras` (bras croisés du Nimbus) ; `Dos` : ni
visage ni sprites `visage`/`yeux`. Planche de contrôle : `bouderie.png`.

Expéditions (`outils/sprites/expedition_sprites.py`, [EXPEDITIONS.md](EXPEDITIONS.md)) : `epee-bois` (dans le dos,
`couche: derriere`, ancre `corps`), le butin exclusif porté `torche` (main), `bouclier-couvercle` (flanc gauche,
ancre `main-g`), `casque-passoire` (tête), `slime-apprivoise` (compagnon) et l'icône `carte-tresor` ;
`pansement` (ancre `tete`, après une défaite) ; icônes `coffre-expedition` (badge du journal) et
`coffre-expedition-ouvert`, `eclat-cristal`, `eclair-energie`, `galette-route`, `jus-etoile` (en-cas de route,
aussi croqués par `Manger`) ; créatures `crea-<id>` (deux images : bug géant, slime de cache, spectre 404, golem de
tickets, hydre des dépendances, gargouille de latence) et trophées `trophee-<boss>` (même coupe, un emblème gravé
différent par boss). Le départ réutilise `baluchon`, l'absence la `pancarte`. Rien de neuf dans le rendu commun :
trois poses de `rendus-reference.txt` les vérifient sur le PC et le téléphone. Planches : `expedition.png`,
`expedition-pilou.png`.
