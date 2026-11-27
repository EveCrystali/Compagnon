"""Finition fine (2×) de la cuisine : plats (`plat-*`), en-cas (`encas-*`), icônes de besoin (`soin-*`), vapeur, mousse.

Les coordonnées sont celles du dessin d'origine (grille 1×) ; les pinceaux de finition.py travaillent en pixels fins.
"""
import math

from finition import (finition, disque, trait, arc, points, poly, oeil, scintille, eclaircir, assombrir, _clarte,
                      ENCRE, NOIR2, BLANC, CREME, CREME_O, GRIS, GRIS_C, ARDOISE, ARGENT, ARGENT_C, B1, B2, B3, B4,
                      O1, O2, O3, O4, O5, J1, J2, J3, J4, V1, V2, V3, V4, S1, S2, S3, BR1, BR2, BR3, T2, NUIT)

DORE = "#f2a94e"


def assiette_fin(t, cx, cy, rx=11, ry=3.5):
    """Assiette : lumière sur le bord, ombre portée du mets, cavité plus creuse."""
    arc(t, cx, cy, rx - 0.3, ry - 0.3, 195, 345, BLANC, {CREME})
    arc(t, cx, cy - 0.5, rx - 2.6, ry - 1.3, 20, 160, CREME_O, {BLANC})
    arc(t, cx, cy, rx - 0.3, ry - 0.2, 20, 160, assombrir(CREME_O, 0.15), {CREME, CREME_O})
    # Petit filet bleu pâle sur le marli.
    arc(t, cx, cy + 0.2, rx - 1.4, ry - 0.8, 200, 340, B4, {CREME, BLANC})


def boule(t, x, y, rx, ry, c, grain=True):
    """Boule rôtie ou dorée : reflet en haut à gauche, ombre en bas à droite, quelques grains."""
    disque(t, x - rx * 0.3, y - ry * 0.4, rx * 0.5, ry * 0.32, eclaircir(c, 0.5), {c})
    arc(t, x, y, rx - 0.2, ry - 0.2, 10, 100, assombrir(c, 0.25), {c})
    if grain:
        e = t.e
        for (a, b) in ((0.3, 0.2), (-0.1, 0.55), (0.55, -0.1)):
            points(t, [(int((x + a * rx) * e), int((y + b * ry) * e))], assombrir(c, 0.3), {c})


@finition("plat-assiette")
def _assiette(t, k):
    assiette_fin(t, 13, 12)
    disque(t, 12, 10.9, 8.5, 1.3, CREME_O, {CREME, BLANC})   # ombre portée du poisson
    # Poisson : œil rond, écailles, nervures de queue, grillures plus nettes.
    oeil(t, 7, 7, 0.9, fond=O5, sur={ENCRE, O3, O5})
    for j, yy in enumerate((6.4, 8.0)):
        for i in range(5):
            X = int((9.5 + i * 2.0 + (j % 2)) * 2)
            points(t, [(X, int(yy * 2)), (X + 1, int(yy * 2) + 1), (X + 2, int(yy * 2))], O2, {O3})
    for dy in (-1.6, 0, 1.6):
        trait(t, 20.5, 7.5, 24, 7.5 + dy * 1.6, O2, {O3})
    disque(t, 10.5, 5.2, 4.5, 0.6, eclaircir(O3, 0.45), {O3})
    # Garniture bleutée : reflet.
    disque(t, 16.3, 3.7, 0.8, 0.5, BLANC, {B3})
    trait(t, 14.5, 4.4, 19.2, 4.4, B2, {B3})
    arc(t, 12, 7.5, 7.6, 3.4, 40, 140, O2, {O3})


@finition("plat-bol")
def _bol(t, k):
    arc(t, 12, 6, 10.6, 3.2, 195, 345, BLANC, {CREME})
    arc(t, 12, 6, 9.6, 2.3, 20, 160, assombrir(O4, 0.18), {O4})
    # Remous de la soupe et miettes dorées.
    arc(t, 11, 6, 5.5, 1.3, 190, 330, eclaircir(O4, 0.45), {O4})
    arc(t, 13, 6.4, 3.0, 0.8, 200, 340, eclaircir(O4, 0.35), {O4})
    for (x, y) in ((8, 5.2), (15.5, 5.4), (11, 7.3)):
        disque(t, x, y, 0.55, 0.4, J3, {O4, O2})
    # Reflet de glaçure en arc, liseré à points sur la bande bleue.
    arc(t, 12, 7, 9.8, 7.0, 150, 188, BLANC, {CREME})
    for i in range(20):
        a = math.radians(40 + i * 5.2)
        X, Y = int((12 + math.cos(a) * 10.6) * 2), int((7 + math.sin(a) * 7.6) * 2)
        if 0 <= Y < t.H and 0 <= X < t.W and t.g[Y][X] == B3 and i % 2 == 0:
            t.g[Y][X] = B4
    # Pied du bol.
    trait(t, 8.5, 14.4, 15.5, 14.4, CREME_O, {CREME})


@finition("plat-ramen")
def _ramen(t, k):
    arc(t, 12, 9, 10.6, 3.2, 195, 345, BLANC, {CREME})
    # Bouillon : nouilles ondulées, éclat, algue, œuf et son jaune.
    for dy in (-0.9, 0.0, 0.9):
        for i in range(12):
            xx = 5 + i * 0.7
            points(t, [(int(xx * 2), int((9 + dy + math.sin(i * 1.1 + dy) * 0.45) * 2))], J2, {J4, J3})
    disque(t, 9, 7.5, 2.5, 1.2, O4, {O4, J4})
    disque(t, 9.4, 7.5, 1.0, 0.55, O3, {O4})
    scintille(t, 7 * 2 + 1, 15, BLANC, 1)
    disque(t, 15, 7.5, 1.6, 1.6, NUIT, {NUIT, J4})
    trait(t, 14.1, 6.7, 15.5, 6.5, "#2a5ea8", {NUIT})
    # Baguettes : un filet de lumière sur chaque.
    trait(t, 17.7, 0.4, 14.2, 8.4, eclaircir(BR3, 0.4), {BR3})
    trait(t, 20.7, 0.4, 16.2, 8.4, eclaircir(BR3, 0.4), {BR3})
    # Bol : reflet d'émail et bande à points.
    arc(t, 12, 10, 10.2, 7.2, 150, 190, B4, {B2, B3})
    for i in range(26):
        a = math.radians(30 + i * 4.8)
        X, Y = int((12 + math.cos(a) * 10.8) * 2), int((10 + math.sin(a) * 7.8) * 2)
        if 0 <= Y < t.H and 0 <= X < t.W and t.g[Y][X] == B3 and i % 2 == 0:
            t.g[Y][X] = B4


@finition("plat-friture")
def _friture(t, k):
    # Cornet de papier : plis et reflet.
    trait(t, 3, 4.7, 24, 4.7, eclaircir(BR3, 0.4), {BR3})
    for (x, y) in ((5, 3), (9, 2), (13, 3), (17, 2), (20, 3), (11, 1)):
        for Y in range(int(y * 2 - 3), int(y * 2)):
            for X in range(int(x * 2 - 3), int(x * 2)):
                if t.getf(X, Y) == J4:
                    t.g[Y][X] = DORE
        boule(t, x, y, 2.6, 2.0, DORE)
        disque(t, x - 0.9, y - 0.8, 0.7, 0.45, J4, {DORE, eclaircir(DORE, 0.5)})


@finition("plat-brochette")
def _brochette(t, k):
    trait(t, 0.4, 4.6, 27.6, 4.6, eclaircir(BR3, 0.4), {BR3})
    trait(t, 0.4, 6.4, 27.6, 6.4, assombrir(BR2, 0.3), {BR2})
    for i, x in enumerate((5, 11, 17, 23)):
        c = [O3, CREME, O2, J3][i]
        for Y in range(int(4 * 2) - 2, int(4 * 2) + 2):
            for X in range(2 * (x - 1) - 1, 2 * (x - 1) + 3):
                if t.getf(X, Y) in (O5, CREME_O):
                    t.g[Y][X] = c
        boule(t, x, 5.5, 3, 3.5, c, grain=False)
        if c == CREME:
            points(t, [(2 * x + 1, 9), (2 * x - 2, 12)], CREME_O, {CREME})
        else:
            trait(t, x - 1.2, 7.2, x + 1.4, 7.6, assombrir(c, 0.2), {c})


@finition("plat-papillote")
def _papillote(t, k):
    assiette_fin(t, 13, 12)
    # Plis du papier : zigzags de lumière et d'ombre, rebord froissé.
    for (x0, y0, x1, y1) in ((7, 8, 10, 5.5), (10, 5.5, 11.5, 7), (15, 7, 17, 5.5), (17, 5.5, 20, 8)):
        trait(t, x0, y0, x1, y1, BLANC, {ARGENT_C, ARGENT})
    trait(t, 13, 2.4, 13, 12, assombrir(GRIS_C, 0.15), {GRIS_C})
    trait(t, 5, 8.6, 13, 12.4, assombrir(ARGENT, 0.22), {ARGENT})
    trait(t, 21, 8.6, 13, 12.4, assombrir(ARGENT, 0.22), {ARGENT})
    for i in range(7):
        points(t, [(10 + i * 4, 23 - abs(3 - i) // 2 - 1)], eclaircir(ARGENT, 0.45), {ARGENT})
    scintille(t, 18, 8, BLANC, 2)


@finition("plat-sushi")
def _sushi(t, k):
    # Planche : fil du bois et rebord clair.
    trait(t, 1.4, 9.4, 26.6, 9.4, eclaircir(BR3, 0.4), {BR3})
    for y in (10.4, 11.4):
        trait(t, 2, y, 26, y, assombrir(BR3, 0.15), {BR3})
    for x in (3, 11, 19):
        cx = x + 3
        # Algue : reflet bleuté ; riz : grains ; garniture : éclat.
        arc(t, cx, 6, 3.2, 3.2, 195, 285, "#2a5ea8", {NUIT})
        for (a, b) in ((-1.3, -0.6), (0.9, -1.2), (-0.3, 1.5), (1.4, 0.7), (-1.5, 0.8), (0.2, -1.6)):
            points(t, [(int((cx + a) * 2), int((6 + b) * 2))], CREME_O, {CREME})
        disque(t, cx - 0.3, 5.7, 0.45, 0.35, O5, {O3})
        disque(t, cx + 0.3, 6.5, 0.7, 0.5, O2, {O3})


@finition("plat-poelon")
def _poelon(t, k):
    arc(t, 13, 7, 11.6, 4.6, 195, 345, eclaircir(ARDOISE, 0.5), {ARDOISE})
    arc(t, 13, 7, 11.6, 4.6, 20, 160, "#1f252d", {ARDOISE})
    # Grains de riz : petits traits clairs et ombres.
    for i in range(40):
        a = i * 2.399
        r = 0.2 + (i * 0.083) % 1.0
        X, Y = int((13 + math.cos(a) * 9.6 * r) * 2), int((6.5 + math.sin(a) * 3.0 * r) * 2)
        points(t, [(X, Y), (X + 1, Y)], eclaircir(J3, 0.55) if i % 2 else assombrir(J3, 0.18), {J3})
    # Morceaux arrondis.
    for (x, y, c) in ((7, 6, O3), (12, 5, O2), (17, 7, B3), (10, 8, O4), (15, 5, V3), (19, 5, O3)):
        for Y in range(y * 2, y * 2 + 4):
            for X in range(x * 2, x * 2 + 4):
                if t.getf(X, Y) == c:
                    t.g[Y][X] = J3
        disque(t, x + 1, y + 1, 1.15, 1.0, c, None)
        disque(t, x + 0.6, y + 0.6, 0.45, 0.3, eclaircir(c, 0.55), {c})
    # Manche : rivet et filet de lumière.
    trait(t, 24.4, 6.4, 29.6, 6.4, NOIR2, {ENCRE})
    disque(t, 25.5, 7, 0.45, 0.45, eclaircir(ARDOISE, 0.5), {ENCRE})


@finition("plat-tarte")
def _tarte(t, k):
    # Bord pincé : petits festons sombres puis clairs.
    for i in range(19):
        a = math.radians(12 + i * 8.5)
        x, y = 13 + math.cos(a) * 11.3, 8 + math.sin(a) * 4.7
        points(t, [(int(x * 2), int(y * 2) + 1)], "#c97a28", {DORE, O4})
        points(t, [(int(x * 2) + 1, int(y * 2) - 1)], eclaircir(O4, 0.5), {O4})
    # Dorure : reflets sur le dessus, fentes en courbe, étoile fine.
    disque(t, 8, 6.2, 3.8, 0.6, eclaircir(O4, 0.6), {O4})
    for x in range(3, 24, 4):
        y = 5 + abs(13 - x) // 6
        trait(t, x, y + 0.3, x + 2, y, assombrir(O2, 0.1), {O4, O2})
    for Y in range(14, 20):
        for X in range(22, 30):
            if t.getf(X, Y) == J3:
                t.g[Y][X] = O4
    scintille(t, 26, 17, J3, 3)
    points(t, [(26, 17)], J4)
    # Pied : ombre.
    arc(t, 13, 13, 11.8, 3.1, 25, 155, assombrir(BR3, 0.3), {BR3})


@finition("plat-plateau")
def _plateau(t, k):
    arc(t, 16, 12, 14.7, 4.7, 195, 345, BLANC, {ARGENT})
    arc(t, 16, 11.5, 13, 3.6, 20, 160, ARGENT, {ARGENT_C})
    for (x, y, rx, ry, c) in ((9, 9, 4, 2.5, O3), (16, 8, 3, 3, CREME), (23, 9, 4, 2.5, B3), (13, 12, 2.5, 1.6, O2),
                              (20, 12, 2.5, 1.6, J3)):
        boule(t, x, y, rx, ry, c, grain=c in (O3, O2))
    for Y in range(10, 14):
        for X in range(30, 34):
            if t.getf(X, Y) == O5:
                t.g[Y][X] = CREME
    scintille(t, 31, 11, J4, 2)
    points(t, [(8, 17), (12, 18), (29, 19)], BLANC, {ARGENT_C})


@finition("plat-souffle")
def _souffle(t, k):
    # Ramequin cannelé : une arête claire et une ombre par cannelure.
    for x in range(3, 17, 2):
        trait(t, x + 0.1, 11.8, x + 0.1, 18.8, BLANC, {CREME})
        trait(t, x + 1.0, 11.8, x + 1.0, 18.8, assombrir(CREME_O, 0.1), {CREME_O})
    trait(t, 3, 11.2, 17, 11.2, BLANC, {CREME, CREME_O})
    arc(t, 10, 19, 7, 0.8, 20, 160, assombrir(CREME_O, 0.25), {CREME, CREME_O})
    # Soufflé : croûte dorée au bord, fissure, reflet.
    arc(t, 10, 9, 7.6, 5.6, 195, 345, J3, {J4})
    arc(t, 10, 9, 7.2, 5.2, 200, 340, eclaircir(J3, 0.3), {J4})
    trait(t, 11, 4.2, 12, 6.5, J3, {J4})
    trait(t, 12, 6.5, 11.2, 8.0, J3, {J4})
    scintille(t, 16, 11, BLANC, 2)
    # Feston de croûte sur le rebord.
    for i in range(9):
        points(t, [(int((4.2 + i * 1.5) * 2), 22)], J3, {J4, CREME})


@finition("plat-tartine")
def _tartine(t, k):
    # Croûte : liseré plus foncé à l'intérieur du cerne, mie parsemée de trous.
    for Y in range(t.H):
        for X in range(t.W):
            if t.g[Y][X] == CREME and any(t.getf(X + a, Y + b) is None or t.getf(X + a, Y + b) == BR2
                                           for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                t.g[Y][X] = S3
    points(t, [(8, 20), (26, 19), (34, 20), (30, 15), (12, 14), (38, 14), (20, 22)], CREME_O, {CREME})
    # Beurre fondu et confiture.
    disque(t, 9, 3, 3, 1.5, O4, {O4})
    disque(t, 8, 2.4, 1.6, 0.6, O5, {O4})
    disque(t, 14, 4, 2.5, 1.5, B3, {B3})
    disque(t, 13.3, 3.4, 0.9, 0.5, B4, {B3})
    points(t, [(30, 8), (28, 9), (26, 7)], B2, {B3})
    scintille(t, 26, 7, BLANC, 1)


@finition("plat-invente")
def _invente(t, k):
    arc(t, 12, 13, 10.6, 3.2, 195, 345, BLANC, {CREME})
    # Cloche : trait de lumière courbe, reflets de la pièce, bouton rond.
    arc(t, 12, 9.5, 7.3, 6.0, 190, 255, BLANC, {GRIS_C})
    arc(t, 12, 9.5, 7.6, 6.3, 20, 100, GRIS, {GRIS_C})
    disque(t, 9, 7, 2.6, 1.8, BLANC, {BLANC, GRIS_C})
    scintille(t, 18, 8, BLANC, 2)
    disque(t, 12, 3, 1.1, 1.1, ARGENT_C, {ARGENT})
    trait(t, 11, 2.3, 12, 2.3, BLANC, {ARGENT, ARGENT_C})
    trait(t, 4.2, 9.8, 19.8, 9.8, GRIS, {GRIS_C})
    # Ombre sur l'assiette.
    disque(t, 12, 14.6, 8.5, 0.9, CREME_O, {CREME, BLANC})


@finition("plat-rate")
def _rate(t, k):
    assiette_fin(t, 13, 16)
    # Le charbon : craquelures, braises, éclat de graisse.
    for (x0, y0, x1, y1) in ((8, 12, 11, 10.5), (14, 13.5, 17, 12), (12, 10, 14, 12), (9.5, 13.5, 12, 14.4)):
        trait(t, x0, y0, x1, y1, ARDOISE, {ENCRE, NOIR2})
    disque(t, 11, 11, 2.4, 1.0, NOIR2, {ENCRE, NOIR2})
    trait(t, 9, 10.4, 13, 10.4, ARDOISE, {NOIR2})
    # Fumée : cœur plus clair et frange sombre.
    for Y in range(t.H):
        for X in range(t.W):
            if t.g[Y][X] == GRIS and Y < 32:
                if t.getf(X - 1, Y - 1) is not None and t.getf(X - 2, Y - 2) in (None, ARDOISE) and t.getf(X + 1, Y + 1) == GRIS:
                    t.g[Y][X] = GRIS_C


@finition("encas-croquettes")
def _croquettes(t, k):
    assiette_fin(t, 6, 6, 6, 2)
    for x, y in ((3, 3), (6, 2), (8, 4), (5, 4), (9, 2)):
        disque(t, x + 0.5, y + 0.5, 1.3, 1.1, BR3, {BR3, S3})
        disque(t, x - 0.1, y - 0.2, 0.55, 0.35, S3, {BR3})
        points(t, [(int((x + 1) * 2), int((y + 1) * 2))], assombrir(BR3, 0.3), {BR3})


@finition("encas-pomme")
def _pomme(t, k):
    # Pomme dorée : reflet net, creux de la queue, ombre basse, feuille nervurée.
    disque(t, 3.6, 4.9, 1.2, 0.9, J4, {J3, J4})
    scintille(t, 6, 8, BLANC, 1)
    arc(t, 5, 6.5, 4.0, 3.7, 20, 100, J2, {J3})
    arc(t, 5, 3.2, 1.6, 0.8, 20, 160, J2, {J3})
    trait(t, 6.4, 1.6, 8.4, 0.8, eclaircir(T2, 0.4), {T2})


@finition("encas-gateau")
def _gateau(t, k):
    # Génoise : couches, crème, cerise orange à reflet, coulure.
    trait(t, 1.3, 5.7, 10.7, 5.7, BLANC, {CREME})
    for x in range(2, 11, 2):
        points(t, [(x * 2, 15), (x * 2 + 1, 16)], assombrir(S2, 0.25), {S2})
    trait(t, 1.3, 9.2, 10.7, 9.2, assombrir(S2, 0.2), {S2})
    arc(t, 6, 4.5, 4.7, 1.9, 195, 345, BLANC, {CREME})
    disque(t, 5.6, 1.7, 0.55, 0.4, O5, {O3})
    scintille(t, 11, 3, BLANC, 1)
    points(t, [(6, 10), (7, 11), (6, 12)], CREME, {S2, O4})


@finition("encas-soupe")
def _soupe(t, k):
    arc(t, 6, 6, 4.6, 1.4, 190, 350, eclaircir(S3, 0.5), {S3})
    arc(t, 6, 7.5, 5.2, 3.5, 150, 190, B4, {B3})
    arc(t, 6, 6.5, 5.4, 4.2, 30, 150, B2, {B3})
    # Vapeur : volutes fines.
    for (x, y) in ((4, 2), (8, 3)):
        trait(t, x - 0.2, y + 1.0, x + 0.4, y - 0.4, GRIS_C, None)


@finition("soin-proprete")
def _soin_proprete(t, k):
    scintille(t, 11, 13, BLANC, 3)


@finition("soin-moral")
def _soin_moral(t, k):
    arc(t, 5, 5.5, 3.9, 3.7, 20, 95, O2, {O3})
    points(t, [(13, 5)], O5, {O3})
