"""Accessoires des saynètes de repos (saynetes.py ; docs/SPRITES.md, « Saynètes de repos »). Appelé par generer.py.

Une image par étape (sprite « sc-<nom>-<k> ») : c'est la saynète qui choisit l'étape, au même instant sur le PC et
le téléphone.

    sc-pieces-1 … 4      la pile de pièces qu'il compte, posée au sol devant lui (ancre « pieds »)
    sc-etincelle-1 … 6   son étincelle qui file autour de lui, puis revient sur l'antenne (ancre « corps »)
    sc-encre-1 … 4       la bulle d'encre de l'éternuement, qui monte et éclate (ancre « bouche »)
    sc-flocon-1 … 4      un flocon qui descend jusqu'à son nez (ancre « yeux »)
    sc-feuille-1 … 5     une feuille d'automne qui tombe sur sa tête, puis s'en va quand il se secoue (ancre « tete »)
    sc-papillon-1 … 6    un papillon qui passe, se pose sur l'antenne, repart (ancre « corps »)
    sc-filante-1 … 3     une étoile filante au-dessus de lui (ancre « corps »)
    sc-canne-1 … 3       la canne qu'il surveille, le bouchon qui danse puis plonge (ancre « main »)
    sc-bulle-1 … 4       une bulle de savon qui monte et éclate (ancre « bouche »)
    sc-note-1 … 3        une note qu'il fredonne, à trois hauteurs (ancre « bouche »)
    sc-biscuit-1 … 3     le biscuit qu'il grignote (ancre « main »)
    sc-pensee-1 … 3      la bulle de pensée qui se forme au-dessus de sa tête (ancre « tete »)

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


# ---- Second lot

GRIS_C = "#adbac7"


def filante():
    # Toile 48 × 44 (le pixel (24, 30) est le centre du corps) : l'étoile file de gauche à droite au-dessus de lui.
    for k, (x, y) in enumerate(((10, 8), (32, 2), (43, 6))):
        t = Toile(48, 44)
        # Traînée de neuf pixels qui monte vers l'étoile (orange près d'elle, bleu au bout), sur deux rangs au départ.
        for i in range(2, 11):
            c = O3 if i < 4 else O4 if i < 7 else B4
            t.p(x - i, y + i // 3, c)
            if i < 5:
                t.p(x - i, y + i // 3 - 1, J4)
        for (u, v) in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1), (-2, 0), (2, 0), (0, -2), (0, 2)):
            t.p(x + u, y + v, J4 if abs(u) + abs(v) < 2 else O4)
        for (u, v) in ((-1, -1), (1, 1), (-1, 1), (1, -1)):
            t.p(x + u, y + v, B4)
        t.p(x, y, BLANC)
        ecrire("sc-filante-%d" % (k + 1), t, slot="effet", ancre="corps", point=(24, 30),
               commentaire="Saynètes « étoiles » et « vœu » : l'étoile filante, étape %d sur 3" % (k + 1))


def canne():
    # Toile 10 × 26 : le pixel (1, 16) est sa main. La canne monte vers la droite ; le fil descend jusqu'au bouchon,
    # posé devant lui ; le bouchon plonge (étape 2 : d'un pixel ; étape 3 : sous l'eau, un rond qui s'élargit).
    for k in range(3):
        t = Toile(10, 26)
        bout = (8, 1) if k < 2 else (8, 3)
        t.ligne(1, 16, bout[0], bout[1], O1)
        t.p(1, 16, O2)
        t.p(2, 15, O2)
        bas = 23 if k == 0 else 24
        t.ligne(bout[0], bout[1] + 1, bout[0], bas - 2 if k < 2 else 24, GRIS_C)
        if k < 2:
            t.p(bout[0], bas - 1, O3)
            t.p(bout[0], bas, CREME)
            if k == 1:
                t.p(bout[0] - 1, bas + 1, B3)
                t.p(bout[0] + 1, bas + 1, B3)
        else:
            for x in range(5, 10):
                t.p(x, 25, B3)
            t.p(bout[0], 24, B4)
        ecrire("sc-canne-%d" % (k + 1), t, slot="effet", ancre="main", point=(1, 16),
               commentaire="Saynète « pêche » : la canne, étape %d sur 3" % (k + 1))


def bulle_savon():
    # Comme la bulle d'encre (à droite de la bouche, hors du visage), mais une bulle de savon : un anneau clair,
    # transparente au milieu, un reflet blanc ; elle éclate en quatre points.
    for k, (cx, cy, r) in enumerate(((3, 17, 1.5), (4, 11, 2.6), (6, 4, 3.4))):
        t = Toile(16, 22)
        t.anneau(cx, cy, r, r, B4)
        t.p(int(cx - r * 0.5), int(cy - r * 0.5), BLANC)
        t.p(int(cx + r * 0.6), int(cy + r * 0.4), B3)
        ecrire("sc-bulle-%d" % (k + 1), t, slot="effet", ancre="bouche", point=(-10, 18),
               commentaire="Saynète « bulles » : la bulle de savon, étape %d sur 4" % (k + 1))
    t = Toile(16, 22)
    for (x, y) in ((6, 0), (2, 4), (10, 4), (6, 8)):
        t.p(x, y, B4)
    t.p(6, 4, BLANC)
    ecrire("sc-bulle-4", t, slot="effet", ancre="bouche", point=(-10, 18), commentaire="Saynète « bulles » : elle éclate")


def note():
    # Une croche, à droite de la bouche, à trois hauteurs et trois couleurs (orange, bleu, violet : la forme suffit).
    for k, (x, y, c) in enumerate(((2, 12, O3), (5, 7, B3), (1, 2, V2))):
        t = Toile(10, 18)
        t.rect(x, y + 3, 2, 2, c)
        t.ligne(x + 1, y, x + 1, y + 3, c)
        t.p(x + 2, y, c)
        t.p(x + 3, y + 1, c)
        ecrire("sc-note-%d" % (k + 1), t, slot="effet", ancre="bouche", point=(-8, 16),
               commentaire="Saynète « fredonne » : une note, hauteur %d sur 3" % (k + 1))


def biscuit():
    # Biscuit rond tenu en main : entier, croqué, presque fini avec des miettes.
    for k in range(3):
        t = Toile(9, 9)
        t.ell(3.5, 3.5, 3.2, 3.2, O2)
        for (x, y) in ((2, 2), (5, 3), (3, 5)):
            t.p(x, y, O1)
        t.p(2, 1, O4)
        if k >= 1:
            for (x, y) in ((6, 0), (7, 1), (6, 1), (7, 2), (5, 0)):
                t.p(x, y, None)
        if k == 2:
            for x in range(4, 8):
                for y in range(0, 5):
                    t.p(x, y, None)
            t.p(5, 8, O3)
            t.p(7, 7, O2)
            t.p(1, 8, O3)
        t.contour(O1)
        ecrire("sc-biscuit-%d" % (k + 1), t, slot="effet", ancre="main", point=(3, 4),
               commentaire="Saynète « grignote » : le biscuit, étape %d sur 3" % (k + 1))


def pensee():
    # Bulle de pensée au-dessus de sa tête, à droite : deux petits ronds, puis le nuage, une étoile dedans.
    for k in range(3):
        t = Toile(22, 20)
        t.ell(2, 17, 1.2, 1.2, CREME)
        if k >= 1:
            t.ell(5, 13, 1.8, 1.8, CREME)
        if k >= 2:
            for (cx, cy, r) in ((11, 6, 4.5), (16, 6, 3.8), (13, 3, 3.6), (8, 7, 3)):
                t.ell(cx, cy, r, r * 0.85, CREME)
            for (u, v) in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
                t.p(12 + u, 5 + v, O3)
            t.p(12, 5, J4)
        t.contour(GRIS_C)
        ecrire("sc-pensee-%d" % (k + 1), t, slot="effet", ancre="tete", point=(-1, 18),
               commentaire="Saynète « rêve » : la pensée, étape %d sur 3" % (k + 1))


def tout():
    pieces()
    etincelle()
    encre()
    flocon()
    feuille()
    papillon()
    filante()
    canne()
    bulle_savon()
    note()
    biscuit()
    pensee()
