# La police pixel de Pilou

Pilou écrit avec sa propre police pixel : sa voix écrite. Dessinée à la main, 100 % originale, complète pour le
français. Elle remplace Segoe UI / Roboto là où Pilou parle (première vague : la bulle et les petits mots).

## Où est quoi

| Fichier | Rôle |
|---|---|
| `outils/sprites/police.py` | L'atelier : le dessin de chaque glyphe, le crénage, la mise en page de référence, la planche |
| `assets/police/texte.txt`, `titre.txt` | Les polices lues par le PC et Android (écrites par le script, ne pas éditer à la main) |
| `assets/police/texte2x.txt`, `titre2x.txt` | Les mêmes, deux fois plus fines (dessin fin, règle MMPX commune aux sprites) |
| `outils/sprites/police-reference.txt` | Lignes, largeurs et empreintes de pixels de vrais textes : les tests des deux côtés la relisent |
| `apps/PilouBureau/PolicePixel.cs`, `TextePixel.cs` | PC : lecture et mise en page (sans WPF) ; élément WPF qui dessine |
| `android/.../PolicePixel.java`, `TextePixelVue.java` | Android : lecture et mise en page ; vue, et image pour le widget |

```
python3 outils/sprites/police.py            # assets/police/*.txt et police-reference.txt
python3 outils/sprites/police.py planche    # + planches/police.png, police-glyphes.png, police-glyphes-titre.png
```

`generer.py` réécrit aussi les polices, `reference.py` aussi la référence.

## La grille

```
rangée  0-1   accents des capitales      É Ê À Ç…
        2     vide (l'accent respire)
        3-9   capitales, chiffres, hampes (b d f h k l)
        2-3   accents des minuscules     é è ê ë…
        5-9   œil des minuscules (5 rangées) ── ligne de base sous la rangée 9
        10-11 jambages (g j p q y), virgule, cédille
```

- **Chasse variable** : capitales et chiffres 5 de large (I, 1 : 3 ; L : 4 ; Œ Æ : 7), minuscules 4 (i 1, l 2,
  f r t 3, m w v 5). Un pixel entre deux glyphes, une espace normale de 2 (4 pixels entre deux mots).
- **Interligne** : 12 pixels (texte), 13 (titre).
- **Titre** : le dessin du texte épaissi d'un pixel vers la droite (gras), mêmes formes. Cinq glyphes dont
  l'épaississement bouchait les creux sont redessinés à la main (`GRAS_MAIN` : m, w, M, W, #).
- **Crénage** : quelques paires se rapprochent d'un pixel (T, F, P, V, Y, L, r, f ; et le « j » après une lettre sans
  jambage).
- **Accents** : composés (lettre nue + signe centré), pour que toutes les lettres accentuées aient le même accent.
- **Signes** : ♥ ♡ ✓ ✗ ✧ ✦ ★ → ← ↑ ↓ ♪ ♫ ☁ ☀ ☾ ☂ ❄ ⚡ ☺ ▼ ▲ ▶ ◀ ● ○ ■ □ ◆, et `¤` dessiné comme une pièce
  (« po »).
- **Caractère absent** (emoji…) : une case de 6 pixels, où la police système l'écrit (secours).

## La mise en page (identique en Python, C# et Java)

Tout se compte en points de code et en pixels de la grille 1× (le dessin fin a les mêmes chasses).

1. **Préparer** : `'` devient `’` ; l'espace devant `! ? ; : »` et derrière `«` devient une espace fine insécable
   (U+202F, 3 pixels au lieu de 4) ; les sélecteurs de variante disparaissent.
2. **Couper** aux espaces normales (mangées), après un trait d'union (gardé), aux retours à la ligne (forcés). Jamais
   aux espaces insécables : « bonjour ! » ne se sépare pas de son « ! ».
3. **Remplir** glouton. Un mot plus long qu'une ligne se coupe entre deux caractères, sans ouvrir une ligne par une
   ponctuation.
4. **Lignes max** : la dernière finit par « … ».

## La taille à l'écran

Un pixel de police tombe toujours sur un nombre entier de pixels de l'écran : le plus proche de la taille voulue
(PC : 1,3 unité WPF, donc 1 pixel à 100 %, 2 à 125-175 %, 3 à 200 % ; téléphone : 1,25 dp dans la bulle, 1,6 dp sur
l'Accueil, 1,2 dp dans le widget). Quand ce nombre est pair, la police fine (2×) est dessinée à la place : traits
arrondis, même place. Sur le PC, seulement si le « Dessin fin » est actif.

## Où elle sert

| | PC | Android |
|---|---|---|
| Phrase de Pilou en tête de bulle (petits mots, réactions, « toc toc ! ») | ✓ `BullePixel.cs` | — |
| Mot du jour : bulle flottante, Accueil, widget | — | ✓ `Bulle.java`, `PresenceVue.motTete`, `Widget.java` |

| Récit, choix, bandeau et lieu de l'Aventure | ✓ `FenetreAventure.cs` | ✓ `Lecture.java` |
| En-tête, barre du bas, Accueil, Jouer, Boutique, Collection | — | ✓ `Style.Texte` (docs/STYLE.md) |

Les tailles et les cas où la police système reste permise sont fixés dans [STYLE.md](STYLE.md). À convertir ensuite :
les fenêtres du PC hors menu, bulle et Aventure ; sur le téléphone, Réglages, liste des aventures, épreuves, atelier.
