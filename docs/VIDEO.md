# Vidéo de promo : tourner, monter

La vidéo montrée dans le README (`docs/promo/`) se fait en deux temps, tout en local sur le PC :

1. **Tourner** : `outils/tourner-ecran-gauche.ps1` filme l'écran de gauche pendant qu'un Pilou de démonstration
   joue la visite guidée devant un décor de bureau fictif ;
2. **Monter** : `outils/video/monter.py` lit ce tournage et produit les vidéos, le GIF et une planche de contrôle.

Décisions qui s'appliquent (docs/DECISIONS.md) : sans voix, cartons courts ; d'abord le compagnon, ensuite
seulement les applis et les infos relayées ; images tournées sur le décor fictif, jamais sur le vrai bureau.

## 1. Tourner

Dans PowerShell, depuis le clone du dépôt (« Ne pas déranger » activé) :

```powershell
powershell -ExecutionPolicy Bypass -File .\outils\tourner-ecran-gauche.ps1
```

Le script montre l'écran filmé, demande confirmation, installe ffmpeg au besoin (winget), filme la visite
guidée (environ 2 min 25 avec toutes les scènes), remet ton Pilou et pose `pilou-ecran-gauche.zip` sur le
Bureau : la vidéo et `chronologie.json`. Décompresse-le dans un dossier **hors du dépôt** (par exemple
`%TEMP%\tournage`) : les rushes ne vont jamais dans le dépôt.

`chronologie.json` donne, pour chaque étape de la visite (`Tournage.Etapes` dans `apps/PilouBureau/Tournage.cs`) :
`debut_s`, `fin_s`, `jouee` (une scène que cette version ne sait pas jouer est sautée et notée `false`) et
`cadres`, les rectangles d'intérêt successifs en pixels de la vidéo (`quoi` : `pilou`, `bulle`, `jeu`, `menu`,
`sous-menu`, `info-bulle`, `boutique`, `amis`, `leo`, `defense`, `expeditions`, `aventure`, `journal`,
`menu-icone`, joints par des `+`). Si tu recoupes le début de la vidéo, ajoute `"decalage_s": <secondes coupées>`
à la chronologie : tous les temps reculent d'autant.

## 2. Monter

Il faut Python 3, Pillow (`python -m pip install Pillow`) et ffmpeg (dans le PATH, ou `--ffmpeg chemin`).

```bash
python outils/video/monter.py <dossier-du-tournage> --plan              # le déroulé seul, n'écrit rien
python outils/video/monter.py <dossier-du-tournage> --apercu            # planche de contrôle seule (rapide)
python outils/video/monter.py <dossier-du-tournage>                     # tout, dans docs/promo
python outils/video/monter.py <dossier-du-tournage> --sortie <dossier>  # ailleurs (essai)
```

Sortie (dans `docs/promo/` par défaut) :

| Fichier | Contenu |
|---|---|
| `pilou-promo.mp4` | 16:9, 1920 × 1080, 30 i/s, musique |
| `pilou-promo-vertical.mp4` | 9:16, 1080 × 1920 (carton en haut, image carrée, marque en bas) |
| `pilou-promo.gif` | 480 px de large, 10 i/s, sans son : celui du README |
| `pilou-promo-planche.png` | une image par plan (horizontale et verticale) : à regarder avant de publier |

Le montage complet prend environ trois minutes. **Regarde toujours la planche** (cadrages, cartons qui ne
cachent rien d'important) et quelques images de la vidéo avant de remplacer `docs/promo/`.

Ce que fait l'outil :

- **caméra virtuelle** : pour chaque image, le rectangle d'intérêt de la chronologie (filtré par le plan),
  plus une marge et de la place en haut pour le carton, au format 16:9, jamais plus serré que `zoom_max` (le
  pixel art deviendrait flou), lissé (aller-retour exponentiel) pour glisser sans à-coup ; un carré à part,
  un peu plus serré, pour la version verticale ; sans rectangles (vieille chronologie) : plan large ;
- **cartons** en français, gros et gras, qui « tapent » à l'entrée (un carton identique au plan précédent ne
  retape pas), palette orange / bleu / violet / crème, avec un liseré de couleur ; police système (Segoe UI
  sous Windows, DejaVu ou Liberation sous Linux, sinon celle de Pillow) ;
- **rythme** : chaque plan dure un nombre entier de demi-mesures de la musique (140 bpm : 0,857 s), donc les
  coupes tombent sur les temps ; transitions coupe, fondu ou balayage de pixels ; fondu au noir à la fin ;
- **musique** chiptune générée par le script (aucun échantillon : libre) ;
- **cartes de fin** : l'installation en une ligne (la commande du README qui se tape dans un terminal, Pilou
  qui surgit et salue) puis « Plein de nouveautés à venir… » ; Pilou y est dessiné par le moteur de référence
  du dépôt (`outils/sprites/rendu.py`), habillé comme celui du tournage.

## 3. Changer le plan de montage

Tout est dans `outils/video/montage.json` ; le code n'a pas à changer. Un plan :

```json
{ "etape": "peche", "de": 0.5, "a": 6, "duree": 3.4, "transition": "balayage",
  "cadrage": { "quoi": "pilou+bulle+jeu", "marge": 90, "restreindre": false },
  "carton": { "texte": "Il pêche…|au bord de l'écran", "couleur": "bleu", "position": "haut" } }
```

| Champ | Sens |
|---|---|
| `etape` | nom de l'étape dans `chronologie.json` ; absente ou `jouee: false` : le plan est sauté, le suivant enchaîne |
| `de`, `a` | sous-plage, en secondes depuis le début de l'étape (par défaut : toute l'étape) |
| `duree` | secondes à l'écran (arrondies à la demi-mesure) ; sinon `vitesse` (1,5 = une fois et demie plus vite). Jamais de ralenti sous ×0,8 : le plan raccourcit |
| `cadrage.quoi` | ce que la caméra suit (mots de `quoi` dans les cadres, joints par `+`) ; vide : tout |
| `cadrage.restreindre` | ne garder que les instants où ce rectangle existe (une fenêtre ouverte, par exemple) |
| `cadrage.marge`, `zoom_max`, `marge_carton` | marge autour de la zone (pixels de la vidéo), zoom maximal, place gardée pour le carton |
| `depuis_large` | secondes de zoom depuis l'écran entier au début du plan (l'accroche) |
| `carton` / `cartons` | un texte (`\|` : retour à la ligne), `couleur` (`creme`, `orange`, `bleu`, `violet`), `position` (`haut`, `bas`), `taille` (`titre`) ; `cartons` : une liste, chacun avec `a`, l'instant d'apparition dans le plan |
| `transition` | `coupe` (défaut), `fondu`, `balayage` |
| `carte` | `installation` ou `a_venir` à la place d'une étape, avec `mesures` (durée) et ses textes |

En tête du fichier : format de sortie, tempo (`rythme`), caméra par défaut, taille du GIF, marque de la
version verticale. Pour vérifier un changement : `--plan` (durées, plans sautés), puis `--apercu`.

## Vie privée

- Le tournage se fait devant le **décor fictif** ; avant le début de la visite et après sa fin, la vidéo montre
  le vrai bureau. L'outil ne lit **que** les images entre le début de la première étape jouée et la fin de la
  dernière (garde-fou dans `Rushes` : une lecture hors de cette plage est refusée) ;
- sans `chronologie.json`, il **refuse** de monter ;
- il n'écrit **que** dans le dossier de sortie (la musique passe par un fichier temporaire de ce dossier,
  effacé à la fin) ;
- aucun rush, aucune image du tournage dans le dépôt : seulement les fichiers finaux de `docs/promo/`.

## Tests

```bash
python outils/video/test_monter.py
```

Une vidéo synthétique (magenta hors de la plage permise) et une chronologie factice : étapes absentes ou non
jouées sautées, durées attendues, cadrages bornés à l'image, `decalage_s`, refus sans chronologie, aucune image
interdite lue ni visible dans les vidéos produites, rien d'écrit hors du dossier de sortie. Il faut Pillow et
ffmpeg ; ce test n'est pas dans la CI (aucun job n'a déjà Pillow et ffmpeg) : le lancer avant de pousser un
changement de `outils/video/`.

## Windows

L'outil est écrit pour Windows comme pour Linux : chemins par `os.path`, fichiers lus et écrits en UTF-8,
ffmpeg appelé avec une liste d'arguments (pas de shell), console qui remplace les caractères qu'elle ne sait
pas afficher, polices cherchées dans `%WINDIR%\Fonts`. Il n'a encore **jamais tourné sur un vrai Windows**
(sessions cloud sous Linux) : au premier essai, vérifier la police des cartons sur la planche.
