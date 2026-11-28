"""La police pixel de Pilou : sa voix écrite (docs/POLICE.md).

    python3 outils/sprites/police.py            → assets/police/*.txt, outils/sprites/police-reference.txt
    python3 outils/sprites/police.py planche    → la même chose, plus outils/sprites/planches/police*.png

Dessin 100 % original, fait ici à la main, glyphe par glyphe. Les fichiers produits dans `assets/police/` sont la
seule source lue par le PC (`PolicePixel.cs`) et par l'app Android (`PolicePixel.java`) ; ce script n'est que
l'atelier qui les écrit.

Grille d'un glyphe (rangées, de haut en bas) :

    0-1   accents des capitales (rangée 2 : vide, pour respirer)
    3-9   capitales et chiffres (7 rangées), hampes des minuscules (b d f h k l t)
    2-3   accents des minuscules (rangée 4 : vide)
    5-9   œil des minuscules (5 rangées) ; la ligne de base est sous la rangée 9
    10-11 jambages (g j p q y, virgule, cédille)

Trois tailles, mêmes chasses (la mise en page est la même pour toutes, en pixels de la grille 1×) :

    texte     la grille ci-dessus, chasse variable, un pixel entre deux glyphes
    titre     le même dessin épaissi d'un pixel vers la droite (gras), un pixel de plus par glyphe
    *2x       les deux, deux fois plus fins (règle commune MMPX, `rendu.agrandir_image`), pour le dessin fin

La mise en page (largeur, coupure des lignes, espaces fines insécables du français) est décrite et écrite trois fois
à l'identique : `mettre_en_page` ici, `PolicePixel.Couper` (C#), `PolicePixel.couper` (Java). Les tests des deux
côtés relisent `police-reference.txt` (lignes, largeurs et empreinte des pixels de vrais textes de Pilou).
"""
import os
import sys

import rendu

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.normpath(os.path.join(ICI, "..", ".."))
DOSSIER = os.path.join(RACINE, "assets", "police")
REFERENCE = os.path.join(ICI, "police-reference.txt")

HAUTEUR = 12      # rangées d'un glyphe
BASE = 10         # première rangée sous la ligne de base
LIGNE = 12        # pas d'une ligne à la suivante
CHASSE = 1        # pixels vides entre deux glyphes
INCONNU = 6       # largeur d'un caractère sans dessin (la police système le dessine dans cette case)
CAP, XH = 3, 5    # haut des capitales, haut de l'œil des minuscules

# ---------------------------------------------------------------------------------------------------------------
# Dessin. G[c] = (rangée du haut, [rangées]) ; '#' encre, '.' vide. Toutes les rangées d'un glyphe ont sa largeur.

G = {}


def g(c, haut, motif):
    rangs = motif.split()
    larg = len(rangs[0])
    assert all(len(r) == larg for r in rangs), c
    assert haut + len(rangs) <= HAUTEUR, c
    G[c] = (haut, rangs)


def vide(c, largeur):
    G[c] = (0, ["." * largeur]) if largeur else (0, [])
    LARGEURS_VIDES[c] = largeur


LARGEURS_VIDES = {}

# ---- Capitales : 5 de large, coins adoucis (Pilou est tout rond), I et L plus étroits ; le A pointu (rond, il
# se lisait H à la taille texte).
g("A", CAP, "..#.. .#.#. #...# #...# ##### #...# #...#")
g("B", CAP, "####. #...# #...# ####. #...# #...# ####.")
g("C", CAP, ".###. #...# #.... #.... #.... #...# .###.")
g("D", CAP, "###.. #..#. #...# #...# #...# #..#. ###..")
g("E", CAP, "##### #.... #.... ####. #.... #.... #####")
g("F", CAP, "##### #.... #.... ####. #.... #.... #....")
g("G", CAP, ".###. #...# #.... #.### #...# #...# .####")
g("H", CAP, "#...# #...# #...# ##### #...# #...# #...#")
g("I", CAP, "### .#. .#. .#. .#. .#. ###")
g("J", CAP, "..### ...#. ...#. ...#. ...#. #..#. .##..")
g("K", CAP, "#...# #..#. #.#.. ##... #.#.. #..#. #...#")
g("L", CAP, "#... #... #... #... #... #... ####")
g("M", CAP, "#...# ##.## #.#.# #.#.# #...# #...# #...#")
g("N", CAP, "#...# ##..# #.#.# #.#.# #..## #...# #...#")
g("O", CAP, ".###. #...# #...# #...# #...# #...# .###.")
g("P", CAP, "####. #...# #...# ####. #.... #.... #....")
g("Q", CAP, ".###. #...# #...# #...# #.#.# #..#. .##.# .....")
g("R", CAP, "####. #...# #...# ####. #.#.. #..#. #...#")
g("S", CAP, ".###. #...# #.... .###. ....# #...# .###.")
g("T", CAP, "##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#..")
g("U", CAP, "#...# #...# #...# #...# #...# #...# .###.")
g("V", CAP, "#...# #...# #...# #...# .#.#. .#.#. ..#..")
g("W", CAP, "#...# #...# #...# #.#.# #.#.# ##.## #...#")
g("X", CAP, "#...# #...# .#.#. ..#.. .#.#. #...# #...#")
g("Y", CAP, "#...# #...# .#.#. ..#.. ..#.. ..#.. ..#..")
g("Z", CAP, "##### ....# ...#. ..#.. .#... #.... #####")
g("Œ", CAP, ".###### #..#... #..#... #..#### #..#... #..#... .######")
g("Æ", CAP, "..##### .#.#... #..#... ####### #..#... #..#... #..####")

# ---- Minuscules : œil de 5, 4 de large (m w v x 5, i 1, j l 2, f t r 3).
g("a", XH, ".##. ...# .### #..# .###")
g("b", CAP, "#... #... ###. #..# #..# #..# ###.")
g("c", XH, ".### #... #... #... .###")
g("d", CAP, "...# ...# .### #..# #..# #..# .###")
g("e", XH, ".##. #..# #### #... .###")
g("f", CAP, "..## .#.. ###. .#.. .#.. .#.. .#..")
g("g", XH, ".### #..# #..# #..# .### ...# ###.")
g("h", CAP, "#... #... ###. #..# #..# #..# #..#")
g("i", CAP, "# . # # # # #")
g("ı", XH, "# # # # #")
g("j", CAP, ".# .. .# .# .# .# .# .# #.")
g("ȷ", XH, ".# .# .# .# .# .# #.")
g("k", CAP, "#... #... #..# #.#. ##.. #.#. #..#")
g("l", CAP, "#. #. #. #. #. #. .#")
g("m", XH, "####. #.#.# #.#.# #.#.# #.#.#")
g("n", XH, "###. #..# #..# #..# #..#")
g("o", XH, ".##. #..# #..# #..# .##.")
g("p", XH, "###. #..# #..# #..# ###. #... #...")
g("q", XH, ".### #..# #..# #..# .### ...# ...#")
g("r", XH, "#.## ##.. #... #... #...")
g("s", XH, ".### #... .##. ...# ###.")
g("t", CAP + 1, "#.. ### #.. #.. #.. .##")
g("u", XH, "#..# #..# #..# #..# .###")
g("v", XH, "#...# #...# .#.#. .#.#. ..#..")
g("w", XH, "#...# #...# #.#.# #.#.# .#.#.")
g("x", XH, "#...# .#.#. ..#.. .#.#. #...#")
g("y", XH, "#..# #..# #..# #..# .### ...# ###.")
g("z", XH, "#### ...# .##. #... ####")
g("œ", XH, ".##.##. #..#..# #..#### #..#... .##.###")
g("æ", XH, ".##.##. ...#..# .###### #..#... .##.###")
g("ß", CAP, ".##. #..# #..# #.#. #..# #..# #.#.")

# ---- Chiffres : 5 de large (le 1 : 3), mêmes rangées que les capitales.
g("0", CAP, ".###. #...# #..## #.#.# ##..# #...# .###.")
g("1", CAP, ".#. ##. .#. .#. .#. .#. ###")
g("2", CAP, ".###. #...# ....# ...#. ..#.. .#... #####")
g("3", CAP, ".###. #...# ....# ..##. ....# #...# .###.")
g("4", CAP, "...#. ..##. .#.#. #..#. ##### ...#. ...#.")
g("5", CAP, "##### #.... ####. ....# ....# #...# .###.")
g("6", CAP, "..##. .#... #.... ####. #...# #...# .###.")
g("7", CAP, "##### ....# ...#. ..#.. .#... .#... .#...")
g("8", CAP, ".###. #...# #...# .###. #...# #...# .###.")
g("9", CAP, ".###. #...# #...# .#### ....# ...#. .##..")

# ---- Ponctuation.
g(".", 9, "#")
g(",", 9, ".# .# #.")
g(";", XH + 1, ".# .. .. .# .# #.")
g(":", XH + 1, "# . . #")
g("!", CAP, "# # # # # . #")
g("?", CAP, ".###. #...# ....# ...#. ..#.. ..... ..#..")
g("¡", XH, "# . # # # # #")
g("¿", XH, "..#.. ..... ..#.. .#... #.... #...# .###.")
g("…", 9, "#.#.#")
g("'", CAP, "# #")
g("’", CAP, ".# .# #.")
g("‘", CAP, ".# #. #.")
g('"', CAP, "#.# #.#")
g("”", CAP, ".#.# .#.# #.#.")
g("“", CAP, ".#.# #.#. #.#.")
g("«", XH + 1, ".#.# #.#. .#.#")
g("»", XH + 1, "#.#. .#.# #.#.")
g("‹", XH + 1, ".# #. .#")
g("›", XH + 1, "#. .# #.")
g("-", 7, "###")
g("‐", 7, "###")
g("‑", 7, "###")
g("–", 7, "#####")
g("—", 7, "#######")
g("_", 9, "#####")
g("(", CAP, ".# #. #. #. #. #. #. .#")
g(")", CAP, "#. .# .# .# .# .# .# #.")
g("[", CAP, "## #. #. #. #. #. #. ##")
g("]", CAP, "## .# .# .# .# .# .# ##")
g("{", CAP, ".## .#. .#. #.. .#. .#. .#. .##")
g("}", CAP, "##. .#. .#. ..# .#. .#. .#. ##.")
g("/", CAP, "..# ..# .#. .#. .#. #.. #..")
g("\\", CAP, "#.. #.. .#. .#. .#. ..# ..#")
g("|", CAP, "# # # # # # # # #")
g("·", 7, "#")
g("•", 6, ".#. ### .#.")
g("°", CAP, ".#. #.# .#.")
g("^", CAP, ".#. #.#")
g("~", 6, ".#..# #.##. ")
g("*", CAP, "..#.. #.#.# .###. #.#.# ..#..")
g("#", CAP + 1, ".#.#. ##### .#.#. ##### .#.#.")
g("+", XH, "..#.. ..#.. ##### ..#.. ..#..")
g("−", 7, "#####")
g("=", 6, "#### .... ####")
g("≈", 5, ".#..# #.##. ..... .#..# #.##.")
g("×", XH, "#...# .#.#. ..#.. .#.#. #...#")
g("÷", XH, "..#.. ..... ##### ..... ..#..")
g("<", XH, "...# ..#. .#.. ..#. ...#")
g(">", XH, "#... .#.. ..#. .#.. #...")
g("%", CAP + 1, "##..# ##.#. ..#.. .#.## #..##")
g("&", CAP, ".##.. #..#. .##.. .#... #.#.# #..#. .##.#")
g("@", CAP, ".####. #....# #.##.# #.#.## #.###. #..... .####.")
g("$", CAP - 1, "..#.. .#### #.#.. .###. ..#.# ####. ..#.. .....")
g("€", CAP, "..### .#... ####. .#... ####. .#... ..###")
g("£", CAP, "..##. .#..# .#... ####. .#... .#... #####")
g("§", CAP, ".### #... .##. #..# .##. ...# ###.")
g("№", CAP, "#..#.... ##.#.##. #.##.#.# #..#.#.# #..#..#. #..#.... #..#.###")

# ---- Signes de Pilou.
g("♥", XH - 1, ".##.##. ####### ####### .#####. ..###.. ...#...")
g("♡", XH - 1, ".##.##. #..#..# #.....# .#...#. ..#.#.. ...#...")
g("✓", XH, ".....## ....##. ##.##.. .###... ..#....")
g("✔", XH, ".....## ....##. ##.##.. .###... ..#....")
g("✗", XH, "##...## .##.##. ..###.. .##.##. ##...##")
g("✧", XH - 1, "...#... ...#... ..#.#.. ##...## ..#.#.. ...#... ...#...")
g("✦", XH - 1, "...#... ...#... ..###.. ####### ..###.. ...#... ...#...")
g("★", CAP, "...#... ...#... ####### .#####. ..###.. .##.##. ##...##")
g("→", XH, "....#.. .....#. ####### .....#. ....#..")
g("⟶", XH, "......#.. .......#. ######### .......#. ......#..")
g("←", XH, "..#.... .#..... ####### .#..... ..#....")
g("↑", CAP, "..#.. .###. #.#.# ..#.. ..#.. ..#.. ..#..")
g("↓", CAP, "..#.. ..#.. ..#.. ..#.. #.#.# .###. ..#..")
g("♪", CAP, "..#.. ..##. ..#.# ..#.. .##.. ###.. .#...")
g("♫", CAP, ".#### .#..# .#..# .#..# ##.## ##.## .....")
g("☁", XH, "...##... .##..##. #......# #......# .######.")
g("☀", CAP, "#..#..# .#...#. ..###.. #.###.# ..###.. .#...#. #..#..#")
g("☾", CAP, ".### ##.. #... #... #... ##.. .###")
g("☂", CAP, "..###.. .#####. ####### ...#... ...#... ...#.#. ....#..")
g("❄", CAP, "...#... #.###.# .#.#.#. ###.### .#.#.#. #.###.# ...#...")
g("⚡", CAP, "...## ..##. .##.. ##### ..##. .##.. ##...")
g("☺", CAP - 1, "..###.. .#...#. #.#.#.# #.....# #.#.#.# #..#..# .#...#. ..###..")
g("▼", XH, "##### .###. ..#..")
g("▲", XH, "..#.. .###. #####")
g("▶", XH - 1, "#.. ##. ### ##. #..")
g("◀", XH - 1, "..# .## ### .## ..#")
g("●", XH, ".###. ##### ##### ##### .###.")
g("○", XH, ".###. #...# #...# #...# .###.")
g("■", XH, "##### ##### ##### ##### #####")
g("□", XH, "##### #...# #...# #...# #####")
g("◆", XH, "..#.. .###. ##### .###. ..#..")
# Pièce d'or (« po ») : un rond frappé, sur le signe monétaire générique.
g("¤", CAP + 1, ".###. #.#.# #.#.# #.#.# #...# .###.")

# ---- Espaces (largeur seule) : normale, insécable, fine insécable (française), fine.
vide(" ", 2)
vide(" ", 2)
vide(" ", 1)
vide(" ", 0)
vide(" ", 0)

# ---------------------------------------------------------------------------------------------------------------
# Lettres accentuées : la lettre nue, plus un signe posé au-dessus (ou dessous, la cédille), centré.

SIGNES = {
    "aigu": [".#", "#."],
    "grave": ["#.", ".#"],
    "circ": [".#.", "#.#"],
    "trema": ["#.#"],
    "trema4": ["#..#"],
    "rond": [".#.", "#.#", ".#."],
    "tilde": [".#.#", "#.#."],
    "caron": ["#.#", ".#."],
}
CEDILLE = [".#", "##"]

ACCENTS = {
    "aigu": "éÉáÁíÍóÓúÚýÝ",
    "grave": "èÈàÀìÌòÒùÙ",
    "circ": "êÊâÂîÎôÔûÛ",
    "trema": "ëËäÄïÏöÖüÜÿŸ",
    "tilde": "ñÑãÃõÕ",
    "rond": "åÅ",
    "caron": "šŠžŽčČ",
}
NUES = {"í": "ı", "ì": "ı", "î": "ı", "ï": "ı"}


def nue(c):
    import unicodedata
    if c in NUES:
        return NUES[c]
    return unicodedata.normalize("NFD", c)[0]


def composer(c, signe):
    base = nue(c)
    haut, rangs = G[base]
    larg = len(rangs[0])
    s = SIGNES[signe]
    if signe == "trema" and larg == 4:
        s = SIGNES["trema4"]
    if signe == "trema" and larg == 5:
        s = [".#.#."]
    sl = len(s[0])
    capitale = base.isupper()
    # Le signe se pose deux rangées au-dessus du haut de la lettre (une rangée vide entre eux), ou, pour les
    # minuscules, juste au-dessus de l'œil (rangées 2-3).
    if capitale:
        y = haut - 1 - len(s)
    else:
        y = XH - 1 - len(s)
    # Sur les lettres de 4 de large, le signe de 2 se met au milieu en penchant vers la droite (aigu) ou la gauche.
    w = max(larg, sl)
    dx_base = (w - larg) // 2
    dx_signe = (w - sl + (1 if signe == "aigu" else 0)) // 2
    if signe == "aigu" and larg == 4:
        dx_signe = 2
    if signe == "grave" and larg == 4:
        dx_signe = 0
    y = max(0, y)  # l'anneau de Å touche la lettre
    top = min(y, haut)
    bas = max(y + len(s), haut + len(rangs))
    grille = [["."] * w for _ in range(bas - top)]
    for r, ligne in enumerate(rangs):
        for k, ch in enumerate(ligne):
            if ch == "#":
                grille[haut - top + r][dx_base + k] = "#"
    for r, ligne in enumerate(s):
        for k, ch in enumerate(ligne):
            if ch == "#":
                grille[y - top + r][dx_signe + k] = "#"
    G[c] = (top, ["".join(l) for l in grille])


def cedille(c):
    base = nue(c)
    haut, rangs = G[base]
    larg = len(rangs[0])
    grille = [list(l) for l in rangs] + [["."] * larg for _ in range(BASE + 2 - haut - len(rangs))]
    x = larg // 2 - (1 if larg == 4 else 1)
    for r, ligne in enumerate(CEDILLE):
        for k, ch in enumerate(ligne):
            if ch == "#":
                grille[BASE - haut + r][x + k] = "#"
    G[c] = (haut, ["".join(l) for l in grille])


for signe, lettres in ACCENTS.items():
    for c in lettres:
        composer(c, signe)
cedille("ç")
cedille("Ç")

# ---------------------------------------------------------------------------------------------------------------
# Crénage : paires qui se rapprochent (ou s'écartent) d'un pixel.

CRENAGE = {}


def creneau(gauches, droites, delta):
    for a in gauches:
        for b in droites:
            CRENAGE[(a, b)] = delta


RONDES = "aceosgqdœæàâäçéèêëôöœ"
creneau("TF", RONDES + "mnpruvwxyz.,…", -1)
creneau("PV", "aeoàâéèêô.,…", -1)
creneau("Y", RONDES + ".,…", -1)
creneau("L", "TVY’'", -1)
creneau("r", ".,…", -1)
creneau("f", ".,…", -1)
creneau("«‹", "  ", 0)
creneau("  ", "»›", 0)
creneau("lLdDjJ", "’'", 0)
creneau("’'", "aeiouyàâéèêëîïôûhAEIOUYÀÂÉÈÊÎÔ", 0)
# Le crochet du j passe sous la lettre d'avant : « déjà », « toujours » gardent l'écart d'un pixel des autres
# lettres. Sauf après une espace, et après ce qui a de l'encre en bas à droite (q, virgule…) : les deux se
# toucheraient.
creneau([c for c, (haut, rangs) in G.items() if rangs and c not in LARGEURS_VIDES
         and not any(rangs[r - haut][-1] == "#" for r in (BASE, BASE + 1) if 0 <= r - haut < len(rangs))],
        "jȷ", -1)

# Signes qui ne peuvent pas ouvrir une ligne (« bonjour ! » ne se coupe pas devant « ! »), et la typographie
# française : une espace fine insécable avant ! ? ; : » et après «.
AVANT_FINE = "!?;:»›"
APRES_FINE = "«‹"
INSECABLE_AVANT = AVANT_FINE + "  …,."
INSECABLE_APRES = APRES_FINE + "  "


def preparer(texte):
    """Le texte tel qu'il sera écrit : apostrophe courbe, espaces fines françaises, sans sélecteurs de variante.
    Travaille par point de code (les trois versions de la mise en page en font autant)."""
    out = []
    t = [c for c in texte.replace("\r\n", "\n").replace("\r", "\n") if c not in "️︎‍"]
    for i, c in enumerate(t):
        if c == "'":
            c = "’"
        if c == " ":
            suivant = t[i + 1] if i + 1 < len(t) else ""
            precedent = t[i - 1] if i > 0 else ""
            if suivant and suivant in AVANT_FINE or precedent and precedent in APRES_FINE:
                c = " "
        out.append(c)
    return "".join(out)


# ---------------------------------------------------------------------------------------------------------------
# Mise en page (la même en C# et en Java).

def largeur_glyphe(c, police):
    if c in police["vides"]:
        return police["vides"][c]
    gl = police["glyphes"].get(c)
    return len(gl[1][0]) if gl and gl[1] else INCONNU if gl is None else 0


def largeur(s, police):
    """Largeur en pixels de la grille 1× d'un texte déjà préparé, sans retour à la ligne."""
    w = 0
    prev = None
    for c in s:
        if prev is not None:
            w += police["chasse"] + police["crenage"].get((prev, c), 0)
        w += largeur_glyphe(c, police)
        prev = c
    return w


def mettre_en_page(texte, police, max_largeur=0, max_lignes=0):
    """Lignes d'un texte coupé à max_largeur pixels (0 : sans limite), au plus max_lignes (0 : toutes ; la
    dernière finit alors par « … »).

    1. `preparer` le texte.
    2. Points de coupure : une espace normale (U+0020 ou U+2009, mangée à la coupure), après un trait d'union
       (gardé en fin de ligne), un retour à la ligne (forcé). Les espaces insécables ne coupent jamais.
    3. Remplissage glouton : un morceau va sur la ligne s'il y tient, sinon il ouvre la suivante.
    4. Un morceau plus long qu'une ligne entière se coupe entre deux caractères (au moins un par ligne), en
       reculant pour ne pas ouvrir une ligne par une ponctuation ou une espace insécable (INSECABLE_AVANT) ni la
       finir par une ouverture (INSECABLE_APRES).
    """
    t = preparer(texte)
    morceaux = []   # (texte, séparateur) : ' ' espace mangée, '' trait d'union, '\n' forcé, None fin
    cour = []
    for c in t:
        if c in "  ":
            morceaux.append(("".join(cour), c))
            cour = []
        elif c == "\n":
            morceaux.append(("".join(cour), "\n"))
            cour = []
        elif c in "-‐":
            cour.append(c)
            morceaux.append(("".join(cour), ""))
            cour = []
        else:
            cour.append(c)
    morceaux.append(("".join(cour), None))

    def tient(s):
        return max_largeur <= 0 or largeur(s, police) <= max_largeur

    lignes = []
    ligne = ""
    attente = ""   # l'espace entre la ligne et le morceau suivant
    for m, sep in morceaux:
        if m == "" and sep in (" ", " "):
            if ligne != "":
                attente = attente or sep
            continue
        if m != "":
            if ligne == "":
                ligne = m
            elif tient(ligne + attente + m):
                ligne = ligne + attente + m
            else:
                lignes.append(ligne)
                ligne = m
            while not tient(ligne) and len(ligne) > 1:
                n = 1
                while n < len(ligne) and tient(ligne[:n + 1]):
                    n += 1
                # Jamais de « ! », « ? », « » » ni d'espace insécable en tête de ligne, ni de « « » en fin.
                while n > 1 and (ligne[n] in INSECABLE_AVANT or ligne[n - 1] in INSECABLE_APRES):
                    n -= 1
                lignes.append(ligne[:n])
                ligne = ligne[n:]
        attente = sep if sep in (" ", " ") else ""
        if sep == "\n":
            lignes.append(ligne)
            ligne = ""
    lignes.append(ligne)
    if max_lignes > 0 and len(lignes) > max_lignes:
        der = lignes[max_lignes - 1]
        while der != "" and not tient(der + "…"):
            der = der[:-1]
        der = der.rstrip("    ")
        lignes = lignes[:max_lignes - 1] + [der + "…"]
    return lignes


def dessiner(lignes, police):
    """Pixels allumés (x, y) du texte : ligne i en y = i × LIGNE, glyphes de gauche à droite."""
    pts = []
    for i, l in enumerate(lignes):
        x = 0
        prev = None
        for c in l:
            if prev is not None:
                x += police["chasse"] + police["crenage"].get((prev, c), 0)
            gl = police["glyphes"].get(c)
            if gl and gl[1] and c not in police["vides"]:
                haut, rangs = gl
                for r, rg in enumerate(rangs):
                    for k, ch in enumerate(rg):
                        if ch == "#":
                            pts.append((x + k, i * police["ligne"] + haut + r))
            x += largeur_glyphe(c, police)
            prev = c
    return pts


def empreinte(lignes, police):
    """FNV-1a 32 bits des pixels allumés, en ordre de lecture (rangée par rangée, de gauche à droite)."""
    h = 2166136261
    for x, y in sorted(set(dessiner(lignes, police)), key=lambda p: (p[1], p[0])):
        h = ((h ^ (x * 65536 + y)) * 16777619) & 0xFFFFFFFF
    return h


# ---------------------------------------------------------------------------------------------------------------
# Tailles dérivées.

def gras(rangs):
    w = len(rangs[0]) + 1
    out = []
    for r in rangs:
        l = r + "."
        out.append("".join("#" if l[k] == "#" or (k > 0 and l[k - 1] == "#") else "." for k in range(w)))
    return out


def fin(haut, rangs):
    """Glyphe deux fois plus fin (MMPX), placé sur une grille de 2 × HAUTEUR rangées."""
    if not rangs:
        return 0, []
    im = [r.replace("#", "e") for r in rangs]
    grand = rendu.agrandir_image(im, {"e": "#1c2128"})
    return haut * 2, [r.replace("e", "#") for r in grand]


def police_texte():
    return {"nom": "texte", "glyphes": dict(G), "vides": dict(LARGEURS_VIDES), "crenage": dict(CRENAGE),
            "chasse": CHASSE, "ligne": LIGNE}


def police_titre():
    gl = {}
    for c, (haut, rangs) in G.items():
        gl[c] = (haut, gras(rangs)) if rangs and c not in LARGEURS_VIDES else (haut, rangs)
    vides = {c: (w + 1 if w else 1) for c, w in LARGEURS_VIDES.items()}
    return {"nom": "titre", "glyphes": gl, "vides": vides, "crenage": dict(CRENAGE), "chasse": CHASSE,
            "ligne": LIGNE + 1}


# ---------------------------------------------------------------------------------------------------------------
# Écriture des fichiers.

def ecrire_police(police, echelle, chemin):
    lignes = [
        "# Police pixel de Pilou, taille « %s »%s. Écrit par outils/sprites/police.py : ne pas éditer à la main."
        % (police["nom"], " (dessin fin, deux fois plus fin)" if echelle == 2 else ""),
        "# Commune au PC (PolicePixel.cs) et à Android (PolicePixel.java). Voir docs/POLICE.md.",
        "#",
        "# En-tête : echelle, hauteur (rangées), ligne (pas d'une ligne, en pixels 1×), chasse, inconnu (case d'un",
        "# caractère sans dessin). Puis un glyphe par bloc : « @ <code hexadécimal> <largeur 1×> <rangée du haut> »,",
        "# ses rangées ('#' encre, '.' vide ; largeur × echelle pixels), une ligne vide. Enfin le crénage :",
        "# « ~ <code> <code> <écart> ».",
        "echelle %d" % echelle,
        "hauteur %d" % (HAUTEUR * echelle),
        "ligne %d" % police["ligne"],
        "chasse %d" % police["chasse"],
        "inconnu %d" % INCONNU,
        "",
    ]
    for c in sorted(police["glyphes"], key=ord):
        haut, rangs = police["glyphes"][c]
        larg = police["vides"][c] if c in police["vides"] else len(rangs[0])
        if c in police["vides"]:
            rangs = []
        if echelle == 2:
            haut, rangs = fin(haut, rangs)
        lignes.append("@ %04X %d %d" % (ord(c), larg, haut))
        lignes.extend(rangs)
        lignes.append("")
    for (a, b), d in sorted(police["crenage"].items(), key=lambda kv: (ord(kv[0][0]), ord(kv[0][1]))):
        if d:
            lignes.append("~ %04X %04X %d" % (ord(a), ord(b), d))
    with open(chemin, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lignes) + "\n")


def lire_police(chemin):
    """Relit un fichier de police (vérifie l'aller-retour) : même structure que police_texte()."""
    gl, vides, cren = {}, {}, {}
    meta = {}
    with open(chemin, encoding="utf-8") as f:
        blocs = f.read().split("\n")
    i = 0
    while i < len(blocs):
        l = blocs[i]
        if l.startswith("#") or l == "":
            i += 1
            continue
        if l.startswith("@ "):
            _, code, larg, haut = l.split()
            c = chr(int(code, 16))
            rangs = []
            i += 1
            while i < len(blocs) and blocs[i] != "":
                rangs.append(blocs[i])
                i += 1
            if not rangs:
                vides[c] = int(larg)
            gl[c] = (int(haut), rangs)
            continue
        if l.startswith("~ "):
            _, a, b, d = l.split()
            cren[(chr(int(a, 16)), chr(int(b, 16)))] = int(d)
        else:
            k, v = l.split()
            meta[k] = int(v)
        i += 1
    return {"glyphes": gl, "vides": vides, "crenage": cren, "chasse": meta["chasse"], "ligne": meta["ligne"],
            "echelle": meta["echelle"]}


# ---------------------------------------------------------------------------------------------------------------
# Textes d'essai : pangrammes, vrais petits mots, vraies phrases de la bulle et des campagnes.

PANGRAMMES = [
    "Portez ce vieux whisky au juge blond qui fume.",
    "Voix ambiguë d'un cœur qui, au zéphyr, préfère les jattes de kiwis.",
    "Dès Noël, où un zéphyr haï me vêt de glaçons würmiens, je dîne d'exquis rôtis de bœuf au kir à l'aÿ d'âge mûr.",
    "ÂME ÉPRISE, ŒIL VIF : ÇA DÉCOIFFE À L'ÎLE DU NORD ! « ÊTRE OU NE PAS ÊTRE ? »",
    "Deuxième jour : déjà joyeux, Alexis jongle avec six kiwis ! « Alors, on y va ? »",
]

PHRASES_BULLE = [
    "coucou ! je m'installe en bas de ton écran, sans te déranger. on grandit ensemble ♥",
    "toc toc ! Claude t'attend",
    "je suis rentré… bredouille et un peu cabossé (clic sur le coffre : le journal)",
    "tu m'as appelé ? je fais demi-tour !",
    "c'est oublié. tu restes « toi », c'est très bien",
    "✦ tout propre !",
    "hmpf ! ☁",
    "+12 po · niveau 4 ✓",
    "je suis plein d'énergie ⚡, garde-le pour plus tard",
    "la pierre de calme retient l'évolution (clic droit → Évolution pour la laisser faire)",
]


def mots_presence(n=24):
    chemin = os.path.join(RACINE, "assets", "presence", "mots.txt")
    out = []
    with open(chemin, encoding="utf-8") as f:
        for l in f:
            l = l.rstrip("\n")
            if not l or l.startswith("#"):
                continue
            parts = l.split("|", 2)
            if len(parts) == 3 and "{" not in parts[2]:
                out.append(parts[2])
    # Les plus longs et quelques-uns au hasard (reproductible) : ce qui risque le plus de mal se couper.
    longs = sorted(out, key=len, reverse=True)[: n // 2]
    pas = max(1, len(out) // (n - len(longs)))
    return longs + out[::pas][: n - len(longs)]


def textes_campagnes(n=10):
    import glob
    import json
    out = []
    for f in sorted(glob.glob(os.path.join(RACINE, "assets", "campagnes", "*", "campagne.json"))):
        with open(f, encoding="utf-8") as h:
            d = json.load(h)

        def fouiller(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k in ("texte", "titre", "dit", "phrase") and isinstance(v, str):
                        out.append(v)
                    else:
                        fouiller(v)
            elif isinstance(o, list):
                for v in o:
                    fouiller(v)
        fouiller(d)
    out = [t for t in out if 10 < len(t) < 200]
    pas = max(1, len(out) // n)
    return out[::pas][:n]


def cas_reference():
    """(texte, largeur max, lignes max) des tests partagés."""
    cas = []
    for t in PANGRAMMES:
        cas += [(t, 0, 0), (t, 120, 0)]
    for t in PHRASES_BULLE:
        cas += [(t, 180, 0), (t, 96, 3)]
    for t in mots_presence(16):
        cas.append((t, 150, 0))
    for t in textes_campagnes(8):
        cas.append((t, 200, 4))
    cas += [
        ("anticonstitutionnellement", 40, 0),
        ("demi-tour, arc-en-ciel et grand-mère", 60, 0),
        ("deux  espaces\net un retour", 0, 0),
        ("", 100, 0),
        ("😀 hors police ♥", 80, 0),
        ("« oui » ; « non » : « peut-être ? »", 70, 0),
        ("tu m'as appelé ? je fais demi-tour !", 30, 0),
        ("« étroit » !", 12, 0),
    ]
    return cas


def ecrire_reference(polices):
    lignes = [
        "# Mise en page de la police pixel (outils/sprites/police.py) : PolicePixelTests.cs et PolicePixelTest.java",
        "# doivent retrouver exactement ces lignes, largeurs et empreintes.",
        "# Bloc : « = <police> <largeur max> <lignes max> », le texte (\\n pour un retour à la ligne), puis une ligne",
        "# par ligne coupée « | <largeur> <texte> », puis « # <empreinte FNV-1a des pixels> ».",
        "",
    ]
    for nom, pol in polices:
        for t, w, n in cas_reference():
            ls = mettre_en_page(t, pol, w, n)
            lignes.append("= %s %d %d" % (nom, w, n))
            lignes.append(t.replace("\\", "\\\\").replace("\n", "\\n"))
            for l in ls:
                lignes.append("| %d %s" % (largeur(l, pol), l))
            lignes.append("# %d" % empreinte(ls, pol))
            lignes.append("")
    with open(REFERENCE, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lignes))


# ---------------------------------------------------------------------------------------------------------------
# Planche de contrôle.

def planche():
    from PIL import Image, ImageDraw

    texte, titre = police_texte(), police_titre()
    ENCRE, FOND, BLEU, ORANGE, GRILLE = (28, 33, 40), (246, 241, 230), (47, 126, 216), (200, 106, 28), (226, 219, 204)

    def bloc(lignes, pol, p, couleur, echelle=1, police_fine=None):
        pts = dessiner(lignes, pol)
        w = max([largeur(l, pol) for l in lignes] + [1])
        h = (len(lignes) - 1) * pol["ligne"] + HAUTEUR
        im = Image.new("RGB", (w * p + 2, h * p + 2), FOND)
        d = ImageDraw.Draw(im)
        if police_fine is None:
            for x, y in pts:
                d.rectangle([x * p + 1, y * p + 1, x * p + p, y * p + p], fill=couleur)
        else:
            q = p // 2
            for i, l in enumerate(lignes):
                x = 0
                prev = None
                for c in l:
                    if prev is not None:
                        x += pol["chasse"] + pol["crenage"].get((prev, c), 0)
                    gl = police_fine["glyphes"].get(c)
                    if gl and gl[1] and c not in pol["vides"]:
                        haut, rangs = gl
                        for r, rg in enumerate(rangs):
                            for k, ch in enumerate(rg):
                                if ch == "#":
                                    X, Y = x * 2 + k, (i * pol["ligne"]) * 2 + haut + r
                                    d.rectangle([X * q + 1, Y * q + 1, X * q + q, Y * q + q], fill=couleur)
                    x += largeur_glyphe(c, pol)
                    prev = c
        return im

    def glyphes_grille(pol, p=6):
        cars = sorted((c for c in pol["glyphes"] if c not in pol["vides"]), key=ord)
        par_ligne = 24
        cw, ch = 11 * p, (HAUTEUR + 4) * p
        im = Image.new("RGB", (par_ligne * cw + 8, ((len(cars) + par_ligne - 1) // par_ligne) * ch + 8), FOND)
        d = ImageDraw.Draw(im)
        for i, c in enumerate(cars):
            ox, oy = 4 + (i % par_ligne) * cw, 4 + (i // par_ligne) * ch
            d.rectangle([ox, oy, ox + cw - 3, oy + HAUTEUR * p], outline=GRILLE)
            for yy in (CAP, XH, BASE):
                d.line([ox, oy + yy * p, ox + cw - 3, oy + yy * p], fill=GRILLE)
            haut, rangs = pol["glyphes"][c]
            for r, rg in enumerate(rangs):
                for k, chh in enumerate(rg):
                    if chh == "#":
                        x, y = ox + 2 + k * p, oy + (haut + r) * p
                        d.rectangle([x, y, x + p - 1, y + p - 1], fill=ENCRE)
            d.text((ox + 2, oy + HAUTEUR * p + 2), "%04X" % ord(c), fill=BLEU)
        return im

    os.makedirs(os.path.join(ICI, "planches"), exist_ok=True)
    glyphes_grille(texte).save(os.path.join(ICI, "planches", "police-glyphes.png"))
    glyphes_grille(titre).save(os.path.join(ICI, "planches", "police-glyphes-titre.png"))

    fine_t = {"glyphes": {c: fin(*v) for c, v in texte["glyphes"].items()}}
    fine_ti = {"glyphes": {c: fin(*v) for c, v in titre["glyphes"].items()}}
    morceaux = []
    for t in ["Pilou, ta voix écrite"]:
        morceaux.append(bloc(mettre_en_page(t, titre), titre, 4, BLEU, police_fine=fine_ti))
        morceaux.append(bloc(mettre_en_page(t, titre), titre, 4, ORANGE))
    alpha = ["ABCDEFGHIJKLMNOPQRSTUVWXYZ ŒÆ", "abcdefghijklmnopqrstuvwxyz œæß", "0123456789 +12 po ¤ ×3 %",
             "éèêë àâä îï ôö ùûü ÿ ç ñ", "ÉÈÊË ÀÂÄ ÎÏ ÔÖ ÙÛÜ Ÿ Ç", ". , ; : ! ? … ’ « » – — ( ) [ ] / & @ # * ° € $",
             "♥ ♡ ✓ ✗ ✧ ✦ ★ ☆ → ← ↑ ↓ ♪ ♫ ☁ ☀ ☾ ☂ ❄ ⚡ ☺ ▼ ▲ ● ○ ◆"]
    morceaux.append(bloc(alpha, texte, 3, ENCRE))
    morceaux.append(bloc(alpha, texte, 4, ENCRE, police_fine=fine_t))
    for t in PANGRAMMES:
        morceaux.append(bloc(mettre_en_page(t, texte, 260), texte, 3, ENCRE))
    for t in PHRASES_BULLE:
        morceaux.append(bloc(mettre_en_page(t, texte, 180), texte, 3, ENCRE))
    for t in mots_presence(20):
        morceaux.append(bloc(mettre_en_page(t, texte, 180), texte, 3, ENCRE))
    for t in textes_campagnes(8):
        morceaux.append(bloc(mettre_en_page(t, texte, 260), texte, 3, ENCRE))
    # À taille réelle (1 et 2 pixels écran par pixel de police) : la lecture « pour de vrai ».
    vrai = ["coucou ! je m'installe en bas de ton écran, sans te déranger.", "on grandit ensemble ♥",
            "« toc toc ! Claude t'attend » · +12 po · niveau 4 ✓"]
    morceaux.append(bloc(vrai, texte, 1, ENCRE))
    morceaux.append(bloc(vrai, texte, 2, ENCRE))
    morceaux.append(bloc(vrai, texte, 2, ENCRE, police_fine=fine_t))
    W = max(m.width for m in morceaux) + 40
    H = sum(m.height + 18 for m in morceaux) + 40
    im = Image.new("RGB", (W, H), FOND)
    y = 20
    for m in morceaux:
        im.paste(m, (20, y))
        y += m.height + 18
    im.save(os.path.join(ICI, "planches", "police.png"))


def fichiers():
    """assets/police/*.txt (appelé aussi par generer.py)."""
    os.makedirs(DOSSIER, exist_ok=True)
    texte, titre = police_texte(), police_titre()
    ecrire_police(texte, 1, os.path.join(DOSSIER, "texte.txt"))
    ecrire_police(texte, 2, os.path.join(DOSSIER, "texte2x.txt"))
    ecrire_police(titre, 1, os.path.join(DOSSIER, "titre.txt"))
    ecrire_police(titre, 2, os.path.join(DOSSIER, "titre2x.txt"))


def reference():
    """police-reference.txt (appelé aussi par reference.py), après un aller-retour par les fichiers écrits."""
    texte, titre = police_texte(), police_titre()
    # Aller-retour : ce que lisent le PC et Android redonne la même mise en page.
    relu = lire_police(os.path.join(DOSSIER, "texte.txt"))
    for t, w, n in cas_reference():
        assert mettre_en_page(t, relu, w, n) == mettre_en_page(t, texte, w, n), t
        assert empreinte(mettre_en_page(t, relu, w, n), relu) == empreinte(mettre_en_page(t, texte, w, n), texte), t
    ecrire_reference([("texte", texte), ("titre", titre)])


def main():
    fichiers()
    reference()
    texte = police_texte()
    manquants = sorted({c for t, _, _ in cas_reference() for c in preparer(t)
                        if c not in texte["glyphes"] and c != "\n"})
    print("police : %d glyphes ; sans dessin dans les essais : %s" % (len(texte["glyphes"]), " ".join(manquants)))
    if len(sys.argv) > 1 and sys.argv[1] == "planche":
        planche()


if __name__ == "__main__":
    main()
