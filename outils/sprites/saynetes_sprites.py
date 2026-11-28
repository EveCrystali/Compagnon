"""Accessoires des saynètes de repos (saynetes.py ; docs/SPRITES.md, « Saynètes de repos »). Appelé par generer.py.

Une image par étape (sprite « sc-<nom>-<k> ») : c'est la saynète qui choisit l'étape, au même instant sur le PC et
le téléphone.

    sc-pieces-1 … 4      la pile de pièces qu'il compte, posée au sol devant lui (ancre « pieds »)
    sc-etincelle-1 … 6   son étincelle qui file autour de lui, puis revient sur l'antenne (ancre « corps »)
    sc-encre-1 … 4       la bulle d'encre de l'éternuement, qui monte et éclate (ancre « bouche »)
    sc-flocon-1 … 4      un flocon qui descend jusqu'à son nez (ancre « yeux »)
    sc-feuille-1 … 5     une feuille d'automne qui tombe sur sa tête, puis s'en va quand il se secoue (ancre « tete »)
    sc-papillon-1 … 6    un papillon qui passe, se pose sur l'antenne, repart (ancre « corps »)

Palette orange / bleu / violet / crème / ardoise : jamais d'opposition rouge-vert. Chaque étape a son signe de forme
(la pile monte d'une pièce, la bulle grossit puis éclate en gouttes, les ailes s'ouvrent et se ferment).
"""
from toile import Toile, ecrire

ENCRE = "#1c2128"
ARDOISE = "#3b4654"
ARDOISE_C = "#545d68"
BLANC = "#ffffff"
CREME = "#f6f8fa"
B2, B3, B4 = "#4a8fdc", "#6cb6ff", "#b4dbff"
O1, O2, O3, O4 = "#8a4a1f", "#d9803a", "#f69d50", "#ffc89a"
J4 = "#fff6cc"
V1, V2, V3 = "#6e4a9e", "#b98ad9", "#e2c8f5"


def pieces():
    # Toile 9 × 10 posée à droite de ses pieds, la dernière ligne au ras du sol.
    for k in range(1, 5):
        t = Toile(9, 10)
        for i in range(k):
            y = 8 - 2 * i
            x = 1 + (i % 2)
            t.rect(x, y, 6, 2, O2)
            t.rect(x + 1, y, 4, 1, O3)
            t.p(x + 1, y, J4)
            t.p(x, y + 1, O1)
            t.p(x + 5, y + 1, O1)
        t.contour(O1)
        ecrire("sc-pieces-%d" % k, t, slot="effet", ancre="pieds", point=(-7, 9),
               commentaire="Saynète « compte » : pile de %d pièce%s" % (k, "s" if k > 1 else ""))


def etoile(t, x, y, grand=True):
    for (u, v) in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
        t.p(x + u, y + v, O3)
    if grand:
        for (u, v) in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            t.p(x + u, y + v, B3)
    t.p(x, y, J4)


def etincelle():
    # Toile 48 × 44 : le pixel (24, 30) est le centre du corps ; l'antenne est vers (24, 11).
    etapes = [((8, 8), (11, 11)), ((5, 24), (8, 20)), ((40, 6), (37, 9)), ((43, 22), (40, 19)), ((24, 2), (27, -1))]
    for k, ((x, y), (tx, ty)) in enumerate(etapes):
        t = Toile(48, 44)
        etoile(t, x, y)
        t.p(tx, ty, B4)  # la traînée, d'où elle vient
        t.p((tx + x) // 2, (ty + y) // 2, O4)
        ecrire("sc-etincelle-%d" % (k + 1), t, slot="effet", ancre="corps", point=(24, 30),
               commentaire="Saynète « étincelle » : étape %d sur 6" % (k + 1))
    # Rattrapée : elle se pose sur l'antenne, quatre petits éclats autour.
    t = Toile(48, 44)
    etoile(t, 24, 9, grand=False)
    for (x, y) in ((19, 6), (29, 6), (20, 12), (28, 12)):
        t.p(x, y, B3)
    ecrire("sc-etincelle-6", t, slot="effet", ancre="corps", point=(24, 30),
           commentaire="Saynète « étincelle » : rattrapée, sur l'antenne")


def encre():
    # Toile 16 × 22 posée à droite de sa bouche (10 pixels plus loin) : la bulle monte devant lui, hors du visage.
    for k, (cx, cy, r) in enumerate(((3, 17, 1.6), (4, 12, 2.4), (5, 6, 3.4))):
        t = Toile(16, 22)
        t.ell(cx, cy, r, r, ARDOISE)
        t.ell(cx + 0.4, cy + 0.5, r * 0.6, r * 0.5, ENCRE)
        t.p(int(cx - r * 0.4), int(cy - r * 0.4), B4)
        if r > 2:
            t.p(int(cx - r * 0.4) + 1, int(cy - r * 0.4), BLANC)
        t.contour(ENCRE)
        ecrire("sc-encre-%d" % (k + 1), t, slot="effet", ancre="bouche", point=(-10, 18),
               commentaire="Saynète « éternue » : la bulle d'encre, étape %d sur 4" % (k + 1))
    # Elle éclate : un anneau ouvert et quatre gouttes qui s'écartent.
    t = Toile(16, 22)
    for (x, y) in ((5, 2), (2, 4), (8, 4), (1, 7), (9, 7), (2, 10), (8, 10), (5, 11)):
        t.p(x, y, ARDOISE_C)
    for (x, y) in ((0, 1), (11, 2), (0, 12), (11, 12)):
        t.p(x, y, ENCRE)
        t.p(x, y + 1, ARDOISE)
    t.p(5, 6, B4)
    ecrire("sc-encre-4", t, slot="effet", ancre="bouche", point=(-10, 18),
           commentaire="Saynète « éternue » : la bulle éclate")


def flocon():
    # Toile 14 × 32 : la colonne 5 est entre ses yeux (il descend à droite de l'antenne), la ligne 28 juste sous les yeux (le nez).
    for k, (x, y) in enumerate(((10, 4), (11, 11), (8, 18), (5, 27))):
        t = Toile(14, 32)
        for (u, v) in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
            t.p(x + u, y + v, BLANC)
        for (u, v) in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            t.p(x + u, y + v, B4)
        for (u, v) in ((-1, -1), (1, 1), (-1, 1), (1, -1)):
            t.p(x + u, y + v, B3)
        t.p(x, y, B4)
        ecrire("sc-flocon-%d" % (k + 1), t, slot="effet", ancre="yeux", point=(5, 26),
               commentaire="Saynète « flocon » : étape %d sur 4" % (k + 1))


def feuille_dessin(t, x, y, penche):
    # Une feuille de 6 × 3 (penchée : 5 × 4), nervure sombre, bord clair.
    if penche == 0:
        t.rect(x, y, 5, 2, O2)
        t.p(x + 1, y - 1, O3)
        t.p(x + 2, y - 1, O3)
        t.p(x + 5, y + 1, O1)
        t.p(x + 1, y + 1, O1)
        t.p(x + 2, y + 1, O1)
        t.p(x + 3, y, O4)
    else:
        for i in range(4):
            t.p(x + i, y + (i * penche) // 2, O2)
            t.p(x + i, y + 1 + (i * penche) // 2, O3)
        t.p(x + 4, y + 1 + (4 * penche) // 2, O1)
        t.p(x + 1, y + (penche > 0), O4)
    t.contour(O1)


def feuille():
    # Toile 34 × 42 : le pixel (17, 30) est le haut de sa tête.
    for k, (x, y, p) in enumerate(((6, 9, 1), (20, 14, -1), (9, 20, 1), (15, 27, 0), (29, 36, -1))):
        t = Toile(34, 42)
        feuille_dessin(t, x, y, p)
        ecrire("sc-feuille-%d" % (k + 1), t, slot="effet", ancre="tete", point=(17, 30),
               commentaire="Saynète « feuille » : étape %d sur 5" % (k + 1))


def papillon_dessin(t, x, y, ouvert):
    """Papillon de 7 × 5 : ailes ouvertes (haut violet clair, bas violet sombre) ou refermées, dressées."""
    if ouvert:
        for sx in (-1, 1):
            for (u, v, c) in ((3, -2, V2), (2, -2, V3), (1, -1, V2), (2, -1, V3), (3, -1, V2), (1, 0, V2), (2, 0, V2),
                              (1, 1, V1), (2, 1, V1)):
                t.p(x + sx * u, y + v, c)
    else:
        for sx in (-1, 1):
            for (u, v, c) in ((1, -3, V3), (1, -2, V2), (1, -1, V2), (2, -3, V2), (2, -2, V1)):
                t.p(x + sx * u, y + v, c)
    for v in (-1, 0, 1):
        t.p(x, y + v, ENCRE)
    t.p(x - 1, y - 2 if ouvert else y - 4, ARDOISE)
    t.p(x + 1, y - 2 if ouvert else y - 4, ARDOISE)


def papillon():
    # Toile 48 × 44 : le pixel (24, 30) est le centre du corps ; l'antenne est vers (24, 11).
    for k, (x, y) in enumerate(((6, 22), (8, 10), (15, 2), (37, 7), (27, 16), (42, 4))):
        t = Toile(48, 44)
        papillon_dessin(t, x, y, k % 2 == 0 and k != 4)
        ecrire("sc-papillon-%d" % (k + 1), t, slot="effet", ancre="corps", point=(24, 30),
               commentaire="Saynète « papillon » : étape %d sur 6" % (k + 1))


def tout():
    pieces()
    etincelle()
    encre()
    flocon()
    feuille()
    papillon()
