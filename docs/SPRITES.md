# Sprites de Pilou

Pilou et tous ses objets sont dessinés **une seule fois**, dans `assets/`, et lus tels quels par le PC
(ressources embarquées de `PilouBureau.exe`) et par l'app Android (ressources Java de l'APK).

| Fichier | Contenu |
|---|---|
| `assets/sprites/<id>.txt` | un sprite (plusieurs images s'il est animé) |
| `assets/index.txt` | la liste des identifiants (Android ne sait pas lister un dossier de ressources) |
| `assets/teintes.txt` | couleurs de Pilou : contour, ombre, base, clair |
| `assets/tenues.txt` | tenue d'activité → sprites portés |
| `assets/plats.txt` | recette → sprite du plat |

## Grille

Pilou se dessine sur une grille de **48 × 56**, la même partout, à la taille d'affichage d'avant
(un pixel de cette grille vaut 104/48 unités WPF sur le PC). Le corps est procédural (une ellipse ombrée
en trame, un reflet, un cerne d'un pixel) ; le visage, l'antenne, l'étincelle et tout ce qu'il porte
viennent des sprites. Trois rendus suivent la même règle et tombent sur les mêmes pixels :
`outils/sprites/rendu.py` (référence), `apps/PilouBureau/RenduPilou.cs`, `android/.../RenduPilou.java`
— vérifié par `RenduTests.cs` et `RenduPilouTest.java` sur les poses de `outils/sprites/rendus-reference.txt`.

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
python3 outils/sprites/generer.py      # réécrit assets/ depuis les dessins du script
python3 outils/sprites/planches.py     # planches PNG de contrôle (outils/sprites/planches/)
python3 outils/sprites/reference.py    # nouvelles empreintes si le rendu de Pilou change exprès
```

Palette : bleus, oranges, argent, violets, jaunes, sables, neutres ; jamais d'opposition rouge / vert,
et chaque rareté ou état garde aussi un signe de forme. Un identifiant inconnu est ignoré sans erreur.

Sur le PC : `PilouBureau.exe --instantane=<png> --essai=tenue:code` (ou `objet:cape`, `stade:3`,
`evolution`, `soins:faim|proprete|moral|terne|rayonnant|lavage|calin|espiegle`) rend la fenêtre dans
une image.

Soins : icônes de besoin `soin-faim`, `soin-proprete`, `soin-moral` ; en-cas `encas-*` ; `mousse`
(toilette) et `rayonnant` (effets animés, 4 images) ; variantes `variante-calin-<stade>` et
`variante-espiegle-<stade>` (visage), avec `-tete` ; teinte `terne` (Pilou négligé).
