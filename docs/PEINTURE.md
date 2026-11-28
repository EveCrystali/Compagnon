# Peindre un paysage de campagne

Les décors des campagnes sont de grands paysages en pixel art, 384 × 160, peints par du code. Décision d'Antoine du
28 novembre 2026, après l'étude `docs/maquettes/paysages/` : « D minimum. Pixel art ne doit pas rimer avec baisse de
qualité/définition. » Cette page suffit pour peindre un lieu neuf au même niveau.

| Fichier | Rôle |
|---|---|
| `outils/sprites/paysage.py` | le moteur : palette, peintre, plans, briques |
| `outils/sprites/decors_hd_<campagne>.py` | les lieux d'une campagne (une fonction par lieu) |
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
6. **Regarder**, à la taille d'écran (3 px par pixel). Puis une deuxième et une troisième passe.

**Coordonnées.** Tout se donne en « unités du monde » : 192 de large, 80 de haut, le sol vers y = 78, comme les
scènes d'avant. La grille est deux fois plus fine ; les demi-unités sont permises. Le peintre déborde de 6 unités de
chaque côté (`MARGE`) pour la parallaxe et le cadrage.

**Places à laisser lisibles.** Pilou se tient à gauche, son interlocuteur à droite (dans le prologue : x ≈ 18 à 24 et
x ≈ 165, pieds à y = 78). Pas de fleur vive ni de détail important à ces endroits. Sur un téléphone de 1078 px, 12
pixels du décor sont coupés de chaque côté : rien d'essentiel dans les 6 unités de bord.

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

Une brique manque ? L'écrire dans le fichier de la campagne d'abord ; la monter dans `paysage.py` quand un second
lieu s'en sert. Un lieu d'intérieur (La Grande Panne) se peint avec les pinceaux de `P` et ses propres briques : le
moteur n'impose pas un paysage.

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
- **Trop de trame brouille** : sur les petites formes, `trame` de 0 à 0,5.
- **Contenu original** : aucune forme, aucun cadrage repris d'un jeu ou d'une image existante.
- **Cohérence d'une campagne** : mêmes tons, mêmes repères (dans le prologue : la maison, la colline et son arbre),
  l'heure qui avance d'un lieu à l'autre.

## Ce qui sort

`assets/decors/decor-<campagne>-<lieu>.txt`, au format « décor compact » (voir [SPRITES.md](SPRITES.md), « Décors haute
définition »), et `outils/sprites/decors-hd-reference.txt`. Les plans restent séparés dans le moteur
(`decors_hd.tableau(id, phase).plans`) : ils serviront à la parallaxe et au cadrage du téléphone ; aujourd'hui seule
l'image composée est écrite.
