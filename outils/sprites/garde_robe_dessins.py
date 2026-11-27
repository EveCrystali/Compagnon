"""Dessins de la boutique garnie (garde_robe.py) : objets des ensembles, objets seuls, décors et bonus d'ensemble.

Même grille que Pilou (48 × 56) et mêmes ancres que boutique_sprites.py : tête (sommet du crâne, x 24 y 24), yeux
(x 24 y 30), cou (x 24 y 43), corps (x 24 y 37), main (flanc droit, x 39 y 39), pieds (x 24 y 50), côté (au sol,
x 31 y 52). Palette sans opposition rouge / vert : bleus, oranges, violets, jaunes, sables, sarcelle, neutres.
Chaque fonction dessine un article et l'écrit (assets/sprites/<id>.txt) ; DESSINS les range par identifiant.
"""
import math

import toile
import fins
from toile import Toile, ecrire
from boutique_sprites import (ENCRE, NOIR2, BLANC, CREME, CREME_O, GRIS, GRIS_C, ARDOISE, ARGENT, ARGENT_C, B1, B2, B3, B4,
                              NUIT, NUIT2, O1, O2, O3, O4, O5, J1, J2, J3, J4, V1, V2, V3, V4, S1, S2, S3, BR1, BR2, BR3, T1,
                              T2, T3, ROSE)

DESSINS = {}
CAFE, CAFE2, MOUSSE = "#3b2416", "#5c3a22", "#e8d5b0"
LUEUR = "#fff6cc99"


def dessin(id_):
    def deco(f):
        import fin
        if id_ in fin.SERIE4:
            def dans_le_lot():
                with fins.lot():
                    return f()
            DESSINS[id_] = dans_le_lot
        else:
            DESSINS[id_] = f
        return f
    return deco


def T(w, h):
    return Toile(w, h)


def etoile(t, x, y, c):
    if toile.fin() and fins.ACTIF:
        fins.etincelle(t, x + 0.5, y + 0.5, c, bras=3, coeur=fins.clair(c, 0.6))
        return
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        t.p(x + dx, y + dy, c)


def eclat(t, x, y, c, k=0):
    """Petit scintillement : une croix qui grandit puis se referme selon k."""
    if toile.fin() and fins.ACTIF:
        if k % 3 == 0:
            fins.point_fin(t, x + 0.5, y + 0.5, c)
        elif k % 3 == 1:
            fins.etincelle(t, x + 0.5, y + 0.5, c, bras=3, coeur=fins.clair(c, 0.6))
        else:
            fins.etincelle(t, x + 0.5, y + 0.5, c, bras=5, coeur=BLANC)
        return
    if k % 3 == 0:
        t.p(x, y, c)
    elif k % 3 == 1:
        etoile(t, x, y, c)
    else:
        for d in (-2, -1, 1, 2):
            t.p(x + d, y, c)
            t.p(x, y + d, c)
        t.p(x, y, BLANC)


def rell(t, cx, cy, rx, ry, ang, c):
    """Ellipse pleine tournée de ang radians."""
    ca, sa = math.cos(ang), math.sin(ang)
    for y in range(t.h):
        for x in range(t.w):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            u, v = (dx * ca + dy * sa) / rx, (-dx * sa + dy * ca) / ry
            if u * u + v * v <= 1:
                t.p(x, y, c)


def tete(id_, t, point, coiffe=True, duree=0, commentaire=""):
    ecrire(id_, t, slot="tete", ancre="tete", point=point, coiffe=coiffe, duree=duree, commentaire=commentaire)


# =====================================================================================================
# Tête
# =====================================================================================================
@dessin("chapeau-explorateur")
def _():
    t = T(36, 15)
    t.ell(18, 12, 12, 11, S3, cond=lambda x, y, u, v: v < 0)
    t.ell(14, 6, 5, 3, CREME, cond=lambda x, y, u, v: u < 0.2)
    t.rect(17, 1, 2, 10, S2)
    t.rect(6, 8, 24, 3, BR2)
    t.rect(6, 8, 24, 1, BR3)
    t.ell(18, 12.5, 17.5, 2.6, S2)
    t.ell(18, 12, 17, 1.6, S3, cond=lambda x, y, u, v: v < 0)
    t.contour(S1)
    tete("chapeau-explorateur", t, (18, 11), commentaire="Casque d'explorateur (ensemble Explorateur)")


@dessin("toque-myrtille")
def _():
    t = T(26, 24)
    for cx, cy, r in ((8, 9, 6), (18, 9, 6), (13, 7, 7)):
        t.ell(cx, cy, r, r * 0.9, CREME)
    t.rect(5, 10, 16, 10, CREME)
    t.ell(10, 6, 2.5, 2, BLANC)
    for x in (9, 13, 17):
        t.ligne(x, 12, x, 19, CREME_O)
    t.rect(3, 19, 20, 4, ARGENT_C)
    t.rect(3, 19, 20, 1, BLANC)
    t.ell(13, 2, 2.6, 2.4, B2)
    t.p(12, 1, B4)
    t.contour(GRIS)
    tete("toque-myrtille", t, (13, 21), commentaire="Toque à la myrtille (ensemble Pâtissier)")


@dessin("bonnet-lune")
def _():
    t = T(32, 18)
    t.ell(16, 15, 14, 14, NUIT2, cond=lambda x, y, u, v: v < 0)
    t.rect(2, 13, 28, 4, B1)
    for x in range(3, 29, 3):
        t.p(x, 14, B3)
    # Croissant de lune jaune.
    t.ell(16, 7, 4.2, 4.2, J3)
    t.ell(18, 6, 3.6, 3.6, NUIT2)
    for x, y in ((7, 8), (24, 5), (10, 3)):
        t.p(x, y, J4)
    t.contour(ENCRE)
    tete("bonnet-lune", t, (16, 15), commentaire="Bonnet lune (ensemble Astronome)")


@dessin("tricorne-moka")
def _():
    t = T(38, 14)
    t.poly([(0, 6), (19, 0), (38, 6), (31, 13), (19, 9), (7, 13)], CAFE2)
    t.poly([(0, 6), (19, 0), (38, 6), (37, 7), (19, 2), (1, 7)], MOUSSE)
    t.poly([(7, 13), (19, 9), (31, 13), (27, 13), (19, 11), (11, 13)], CAFE)
    # Grain de café en écusson.
    t.ell(19, 6, 2.6, 3.2, BR3)
    t.ligne(19, 4, 19, 8, CAFE)
    t.contour(ENCRE)
    tete("tricorne-moka", t, (19, 11), commentaire="Tricorne moka (ensemble Pirate des mers de café)")


@dessin("chapeau-paille")
def _():
    t = T(44, 14)
    t.ell(22, 11, 21.5, 3, J3)
    t.ell(22, 10.5, 21, 1.8, J4, cond=lambda x, y, u, v: v < 0)
    t.ell(22, 10, 9, 9, J3, cond=lambda x, y, u, v: v < 0)
    for x in range(14, 31, 3):
        t.ligne(x, 2, x + 1, 9, J2)
    t.rect(13, 7, 18, 2, B2)
    t.poly([(29, 8), (34, 12), (31, 12)], B2)
    for x in range(2, 43, 4):
        t.p(x, 11, J2)
    t.contour(J1)
    tete("chapeau-paille", t, (22, 10), commentaire="Chapeau de paille (ensemble Jardinier)")


@dessin("casquette-pixel")
def _():
    t = T(34, 13)
    t.ell(14, 11, 12, 10, V2, cond=lambda x, y, u, v: v < 0)
    t.ell(10, 5, 4, 2.5, V3)
    t.rect(13, 1, 2, 2, V1)
    t.rect(20, 8, 14, 3, V1)
    t.rect(20, 8, 14, 1, V3)
    # Cœur pixel orange sur le devant.
    t.motif(9, 5, [".o.o.", "ooooo", ".ooo.", "..o.."], {"o": O3})
    t.contour(ENCRE)
    tete("casquette-pixel", t, (14, 10), commentaire="Casquette pixel (ensemble Rétro-arcade)")


@dessin("bonnet-oreillettes")
def _():
    t = T(36, 26)
    t.ell(18, 15, 14, 13, B2, cond=lambda x, y, u, v: v < 0)
    for y in range(4, 15):
        for x in range(36):
            if t.get(x, y) == B2 and (x + y) % 4 == 0:
                t.p(x, y, B3)
    t.rect(3, 13, 30, 3, CREME)
    for x0 in (1, 30):
        t.poly([(x0, 15), (x0 + 5, 15), (x0 + 4, 21), (x0 + 1, 21)], B2)
        t.rect(x0 + 1, 16, 3, 4, CREME)
        t.ligne(x0 + 2, 21, x0 + 2, 25, CREME_O)
    t.ell(18, 2.5, 3, 2.5, CREME)
    t.contour(B1)
    tete("bonnet-oreillettes", t, (18, 14), commentaire="Bonnet à oreillettes (ensemble Hiver douillet)")


@dessin("chapeau-plage")
def _():
    t = T(46, 15)
    t.ell(23, 12, 22.5, 3.2, CREME)
    t.ell(23, 12, 22, 2, BLANC, cond=lambda x, y, u, v: v < -0.3)
    t.ell(23, 11, 10, 10, CREME, cond=lambda x, y, u, v: v < 0)
    t.ell(19, 5, 3, 2, BLANC)
    t.rect(13, 7, 20, 3, O3)
    t.rect(13, 7, 20, 1, O5)
    t.ell(31, 9, 2.4, 2.4, O2)
    t.contour(S1)
    tete("chapeau-plage", t, (23, 11), commentaire="Chapeau de plage (ensemble Plage)")


@dessin("coiffe-courge")
def _():
    t = T(32, 18)
    t.ell(16, 13, 15, 10, O3, cond=lambda x, y, u, v: v < 0.25)
    for x in (8, 16, 24):
        t.ligne(x, 4, x, 15, O2)
    t.ell(11, 7, 3, 2, O5)
    t.rect(14, 0, 4, 4, T1)
    t.poly([(17, 1), (24, 0), (21, 3)], T2)
    t.contour(O1)
    tete("coiffe-courge", t, (16, 14), commentaire="Coiffe courge (ensemble Nuit des frissons)")


@dessin("bonnet-lutin")
def _():
    t = T(36, 22)
    t.poly([(2, 17), (14, 2), (24, 0), (33, 6), (30, 8), (24, 5), (28, 17)], V2)
    t.poly([(14, 2), (24, 0), (24, 3), (16, 6)], V3)
    t.rect(1, 16, 28, 5, CREME)
    for x in range(2, 28, 3):
        t.p(x, 17, BLANC)
    t.ell(32.5, 8.5, 2.8, 2.8, J3)
    t.p(32, 7, J4)
    t.contour(V1)
    tete("bonnet-lutin", t, (15, 19), commentaire="Bonnet de lutin (ensemble Fêtes de l'hiver)")


@dessin("bandeau-eponge")
def _():
    t = T(26, 5)
    t.poly([(4, 0), (22, 0), (25, 4), (1, 4)], O3)
    t.rect(3, 2, 20, 1, CREME)
    t.contour(O1)
    # Posé sur le front, sous le sommet du crâne.
    ecrire("bandeau-eponge", t, slot="tete", ancre="tete", point=(13, -1), commentaire="Bandeau éponge")


@dessin("chapeau-melon")
def _():
    t = T(30, 16)
    t.ell(15, 12, 10, 12, NOIR2, cond=lambda x, y, u, v: v < 0)
    t.ell(11, 5, 3, 3, ARDOISE)
    t.p(10, 3, GRIS)
    t.rect(5, 9, 20, 3, O2)
    t.rect(5, 9, 20, 1, O3)
    t.ell(15, 13.5, 14.5, 2.4, NOIR2)
    t.ell(15, 13, 14, 1.2, ARDOISE, cond=lambda x, y, u, v: v < 0)
    t.contour(GRIS)
    tete("chapeau-melon", t, (15, 13), commentaire="Chapeau melon")


@dessin("chapeau-champi")
def _():
    t = T(38, 15)
    t.ell(19, 13, 18.5, 12, V2, cond=lambda x, y, u, v: v < 0)
    t.ell(19, 13, 18.5, 3, V1, cond=lambda x, y, u, v: v > 0)
    for cx, cy, r in ((10, 7, 2.2), (19, 3.5, 2.6), (28, 7, 2.2), (14, 10, 1.4), (24, 10, 1.4)):
        t.ell(cx, cy, r, r, CREME)
    t.contour(ENCRE)
    tete("chapeau-champi", t, (19, 12), commentaire="Chapeau champignon (violet à pois crème)")


@dessin("nid-oiseau")
def _():
    images = []
    for k in range(4):
        t = T(30, 16)
        t.ell(15, 12, 13, 4, BR2)
        for x in range(3, 28, 2):
            t.ligne(x, 9 + x % 3, x + 3, 15 - x % 2, BR1 if x % 4 else BR3)
        t.ell(11, 9.5, 2.4, 2, B4)
        t.ell(16, 9, 2.4, 2, B4)
        t.p(10, 9, BLANC)
        # Oisillon qui pépie (bec ouvert une image sur deux).
        h = 1 if k % 2 else 0
        t.ell(21, 7 - h, 3.2, 3, J3)
        t.p(22, 6 - h, ENCRE)
        t.poly([(24, 6 - h), (27, 7 - h - (k % 2)), (24, 8 - h)], O3)
        t.contour(ENCRE)
        images.append(t)
    tete("nid-oiseau", images, (15, 13), coiffe=True, duree=300, commentaire="Nid d'oiseau")


@dessin("couronne-cristal")
def _():
    images = []
    for k in range(4):
        t = T(30, 18)
        t.rect(3, 12, 24, 4, B4)
        t.rect(3, 12, 24, 1, BLANC)
        for i, (x, h) in enumerate(((5, 7), (10, 10), (15, 13), (20, 10), (25, 7))):
            t.poly([(x - 2.5, 13), (x, 13 - h), (x + 2.5, 13)], B4 if i % 2 else V4)
            t.ligne(x, 12 - h + 2, x, 12, BLANC)
        t.ell(15, 14, 1.6, 1.4, V2)
        eclat(t, [4, 26, 15, 9][k], [3, 5, 0, 4][k], BLANC, k)
        t.contour(B2)
        images.append(t)
    tete("couronne-cristal", images, (15, 14), coiffe=True, duree=220, commentaire="Couronne de cristal (mythique)")


# =====================================================================================================
# Yeux
# =====================================================================================================
def yeux(id_, t, point, duree=0, commentaire=""):
    ecrire(id_, t, slot="yeux", ancre="yeux", point=point, duree=duree, commentaire=commentaire)


@dessin("jumelles")
def _():
    t = T(28, 11)
    for x0 in (1, 16):
        t.rect(x0, 1, 11, 9, NOIR2)
        t.ell(x0 + 5.5, 5.5, 4, 3.6, B2)
        t.ell(x0 + 4.5, 4.5, 1.6, 1.4, B4)
    t.rect(12, 3, 4, 4, ARDOISE)
    t.rect(13, 1, 2, 2, GRIS)
    t.contour(ENCRE)
    yeux("jumelles", t, (14, 2), commentaire="Jumelles (ensemble Explorateur)")


@dessin("lunettes-etoiles")
def _():
    t = T(34, 13)
    for cx in (8, 26):
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            r = 6.5 if i % 2 == 0 else 3.2
            pts.append((cx + math.cos(a) * r, 6.5 + math.sin(a) * r))
        t.poly(pts, J3)
        t.ell(cx, 7, 2.8, 2.4, V1)
        t.p(cx - 1, 6, V4)
    t.rect(14, 5, 6, 1, J2)
    t.contour(J1)
    yeux("lunettes-etoiles", t, (17, 3), commentaire="Lunettes étoiles (ensemble Astronome)")


@dessin("bandeau-oeil")
def _():
    t = T(34, 14)
    t.ligne(0, 5, 33, 0, NOIR2)
    t.ligne(0, 6, 33, 1, NOIR2)
    t.ell(10, 8.5, 4.6, 4, ENCRE)
    t.ell(9, 7.5, 2, 1.4, ARDOISE)
    t.ell(10, 9, 1.4, 1.4, J2)
    yeux("bandeau-oeil", t, (17, 5), commentaire="Bandeau d'œil (ensemble Pirate des mers de café)")


@dessin("lunettes-pixel")
def _():
    t = T(32, 8)
    t.rect(0, 0, 32, 2, ENCRE)
    for x0 in (2, 17):
        t.rect(x0, 2, 13, 5, ENCRE)
        for y in (2, 4, 6):
            t.rect(x0 + 1, y, 11, 1, V2)
        t.rect(x0 + 2, 2, 2, 1, V4)
    yeux("lunettes-pixel", t, (16, 1), commentaire="Lunettes pixel (ensemble Rétro-arcade)")


@dessin("lunettes-plage")
def _():
    t = T(32, 11)
    for cx in (8, 24):
        t.ell(cx, 5.5, 6, 5, O3)
        t.ell(cx, 5.5, 4.4, 3.6, B1)
        t.ell(cx - 1.5, 4, 1.6, 1.2, B3)
    t.rect(13, 4, 6, 1, O3)
    t.contour(O1)
    yeux("lunettes-plage", t, (16, 2), commentaire="Lunettes de plage (ensemble Plage)")


@dessin("masque-loup")
def _():
    t = T(34, 13)
    t.poly([(0, 3), (8, 1), (17, 4), (26, 1), (34, 3), (31, 10), (22, 11), (17, 8), (12, 11), (3, 10)], V2)
    for cx in (9, 25):
        t.ell(cx, 6, 3.4, 2.2, None)
    t.poly([(0, 3), (8, 1), (17, 4), (26, 1), (34, 3), (33, 4), (26, 2), (17, 5), (8, 2), (1, 4)], J3)
    t.contour(V1)
    t.ligne(31, 3, 34, -3, CREME)
    t.ligne(32, 3, 33, -2, J4)
    yeux("masque-loup", t, (17, 3), commentaire="Loup de bal (ensemble Nuit des frissons)")


@dessin("masque-sommeil")
def _():
    t = T(32, 10)
    t.poly([(1, 1), (31, 1), (30, 8), (18, 9), (16, 7), (14, 9), (2, 8)], V3)
    t.rect(1, 1, 31, 1, V4)
    for cx in (8, 24):
        t.ligne(cx - 3, 4, cx - 1, 6, V1)
        t.ligne(cx - 1, 6, cx + 1, 6, V1)
        t.ligne(cx + 1, 6, cx + 3, 4, V1)
        for d in (-3, 0, 3):
            t.p(cx + d, 7, V1)
    t.contour(V1)
    yeux("masque-sommeil", t, (16, 1), commentaire="Masque de sommeil")


@dessin("lunettes-loupe")
def _():
    t = T(32, 13)
    for cx in (8, 24):
        t.ell(cx, 6.5, 6.5, 6, NOIR2)
        t.ell(cx, 6.5, 5.2, 4.8, BLANC)
        t.ell(cx + 0.5, 7, 3, 3, ENCRE)
        t.ell(cx - 0.5, 5.5, 1, 1, BLANC)
    t.rect(14, 5, 4, 1, NOIR2)
    t.contour(ENCRE)
    yeux("lunettes-loupe", t, (16, 3), commentaire="Lunettes-loupes")


@dessin("lunettes-ski")
def _():
    t = T(38, 11)
    t.rect(0, 3, 38, 3, NOIR2)
    t.poly([(4, 1), (34, 1), (33, 9), (21, 10), (19, 8), (17, 10), (5, 9)], ARDOISE)
    t.poly([(6, 2), (32, 2), (31, 8), (21, 9), (19, 7), (17, 9), (7, 8)], O3)
    t.poly([(6, 2), (32, 2), (31, 4), (7, 4)], J3)
    t.ligne(10, 7, 14, 3, J4)
    t.contour(ENCRE)
    yeux("lunettes-ski", t, (19, 3), commentaire="Masque de ski")


@dessin("lunettes-kaleido")
def _():
    images = []
    cols = [B3, V3, O3, J3]
    for k in range(4):
        t = T(32, 13)
        for cx in (8, 24):
            t.ell(cx, 6.5, 6.5, 6, ARGENT)
            for y in range(13):
                for x in range(32):
                    u, v = x + 0.5 - cx, y + 0.5 - 6.5
                    if u * u / 25 + v * v / 21 <= 1:
                        a = (math.atan2(v, u) / (2 * math.pi) * 6 + k) % 4
                        t.p(x, y, cols[int(a)])
            t.p(cx, 6, BLANC)
        t.rect(14, 5, 4, 1, ARGENT)
        t.contour(ENCRE)
        images.append(t)
    yeux("lunettes-kaleido", images, (16, 3), duree=200, commentaire="Lunettes kaléidoscope")


# =====================================================================================================
# Cou
# =====================================================================================================
def cou(id_, t, point, duree=0, commentaire=""):
    ecrire(id_, t, slot="cou", ancre="cou", point=point, duree=duree, commentaire=commentaire)


@dessin("foulard-explorateur")
def _():
    t = T(30, 11)
    t.poly([(1, 0), (29, 0), (15, 10)], O3)
    t.rect(1, 0, 28, 2, O2)
    for x in range(4, 27, 4):
        t.p(x, 3, O5)
    t.ell(15, 2, 2.4, 2, O1)
    t.contour(ENCRE)
    cou("foulard-explorateur", t, (15, 1), commentaire="Foulard d'explorateur (ensemble Explorateur)")


@dessin("foulard-vichy")
def _():
    t = T(32, 12)
    t.poly([(1, 0), (31, 0), (16, 11)], B2)
    for y in range(12):
        for x in range(32):
            if t.get(x, y) == B2:
                a, b = (x // 2) % 2, (y // 2) % 2
                t.p(x, y, CREME if a and b else B2 if a or b else B1)
    t.poly([(26, 0), (32, 0), (31, 5)], B1)
    t.contour(ENCRE)
    cou("foulard-vichy", t, (16, 1), commentaire="Foulard vichy (ensemble Pâtissier)")


@dessin("mariniere")
def _():
    t = T(34, 11)
    t.poly([(0, 0), (34, 0), (30, 8), (17, 3), (4, 8)], B1)
    t.ligne(2, 2, 15, 2, CREME)
    t.ligne(19, 2, 32, 2, CREME)
    t.ligne(3, 4, 13, 4, CREME)
    t.ligne(21, 4, 31, 4, CREME)
    t.poly([(14, 3), (20, 3), (19, 6), (21, 10), (17, 8), (13, 10), (15, 6)], O3)
    t.contour(ENCRE)
    cou("mariniere", t, (17, 1), commentaire="Col marin (ensemble Pirate des mers de café)")


@dessin("jeton-arcade")
def _():
    t = T(24, 14)
    for i in range(12):
        x = 2 + i * 20 / 11
        t.p(int(x), int(math.sin(i / 11 * math.pi) * 4), ARGENT)
    t.ell(12, 9, 4.5, 4.5, J3)
    t.ell(12, 9, 3, 3, J2)
    t.motif(10, 7, [".j.", "jjj", ".j."], {"j": J4})
    t.contour(ENCRE)
    cou("jeton-arcade", t, (12, 1), commentaire="Jeton d'arcade (ensemble Rétro-arcade)")


@dessin("echarpe-tricot")
def _():
    t = T(36, 20)
    t.rect(1, 0, 34, 5, O3)
    t.poly([(22, 3), (29, 3), (31, 18), (24, 18)], O3)
    for y in range(20):
        for x in range(36):
            if t.get(x, y) == O3 and (y // 2) % 3 == 0:
                t.p(x, y, CREME)
            elif t.get(x, y) == O3 and x % 3 == 0:
                t.p(x, y, O2)
    for x in range(24, 32, 2):
        t.ligne(x, 18, x, 19, O4)
    t.contour(O1)
    cou("echarpe-tricot", t, (18, 1), commentaire="Grande écharpe tricotée (ensemble Hiver douillet)")


@dessin("collier-coquillages")
def _():
    t = T(30, 10)
    cols = [CREME, O4, B4, CREME, ROSE, CREME, B4, O4]
    for i in range(9):
        a = math.pi * i / 8
        x, y = 15 - math.cos(a) * 13, 1 + math.sin(a) * 5
        t.ell(x, y, 1.8, 1.6, cols[i % len(cols)])
    t.poly([(12, 5), (18, 5), (15, 9)], O4)
    t.ligne(15, 5, 15, 8, O2)
    t.contour(S1)
    cou("collier-coquillages", t, (15, 1), commentaire="Collier de coquillages (ensemble Plage)")


@dessin("guirlande")
def _():
    images = []
    cols = [B3, O3, J3, V3]
    for k in range(3):
        t = T(34, 10)
        for i in range(34):
            y = 1 + math.sin(i / 33 * math.pi) * 5
            t.p(i, int(y), NOIR2)
        for j in range(8):
            x = 2 + j * 4.2
            y = 2 + math.sin(x / 33 * math.pi) * 5
            c = cols[(j + k) % 4]
            t.ell(x, y + 1.5, 1.4, 1.8, c)
            if (j + k) % 3 == 0:
                t.p(int(x), int(y + 1), BLANC)
        images.append(t)
    cou("guirlande", images, (17, 1), duree=400, commentaire="Guirlande lumineuse (ensemble Fêtes de l'hiver)")


@dessin("clochette")
def _():
    t = T(20, 11)
    t.rect(0, 0, 20, 2, B2)
    t.poly([(7, 2), (13, 2), (15, 8), (5, 8)], J3)
    t.ell(10, 3, 3, 2, J3)
    t.rect(4, 8, 12, 1, J2)
    t.ell(10, 9.5, 1.3, 1.3, J1)
    t.p(8, 4, J4)
    t.contour(ENCRE)
    cou("clochette", t, (10, 1), commentaire="Clochette")


@dessin("pendentif-goutte")
def _():
    t = T(24, 13)
    for i in range(16):
        x = 2 + i * 20 / 15
        t.p(int(x), int(math.sin(i / 15 * math.pi) * 4), ARGENT_C)
    t.ell(12, 9.5, 2.8, 2.8, B3)
    t.poly([(9.5, 9), (14.5, 9), (12, 4)], B3)
    t.p(11, 8, BLANC)
    t.contour(B1)
    cou("pendentif-goutte", t, (12, 1), commentaire="Pendentif goutte")


@dessin("noeud-geant")
def _():
    t = T(32, 15)
    t.poly([(0, 0), (14, 6), (14, 9), (0, 15)], O3)
    t.poly([(32, 0), (18, 6), (18, 9), (32, 15)], O3)
    t.rect(13, 5, 6, 6, O2)
    for x, y in ((3, 4), (6, 9), (3, 11), (28, 4), (25, 9), (28, 11), (8, 6), (23, 6)):
        t.p(x, y, CREME)
    t.contour(O1)
    cou("noeud-geant", t, (16, 4), commentaire="Nœud géant")


@dessin("collier-comete")
def _():
    images = []
    for k in range(4):
        t = T(30, 15)
        for i in range(16):
            x = 2 + i * 26 / 15
            t.p(int(x), int(math.sin(i / 15 * math.pi) * 4), J2)
        t.poly([(15, 6), (16.5, 9), (20, 9.5), (17.3, 11.5), (18.2, 15), (15, 13), (11.8, 15), (12.7, 11.5), (10, 9.5),
                (13.5, 9)], J3)
        t.p(15, 10, J4)
        for i in range(3):
            t.p(9 - i * 2, 8 - i + (k + i) % 2, [B4, V4, BLANC][(i + k) % 3])
        t.contour(J1)
        images.append(t)
    cou("collier-comete", images, (15, 1), duree=240, commentaire="Collier comète")


# =====================================================================================================
# Dos
# =====================================================================================================
def dos(id_, t, point, ancre="cou", couche="derriere", duree=0, commentaire=""):
    ecrire(id_, t, slot="dos", ancre=ancre, point=point, couche=couche, duree=duree, commentaire=commentaire)


@dessin("sac-explorateur")
def _():
    t = T(46, 26)
    t.rect(2, 0, 42, 5, O3)
    for x in range(4, 44, 5):
        t.ligne(x, 0, x + 1, 4, O2)
    t.rect(34, 4, 11, 19, S2)
    t.rect(35, 5, 9, 6, S3)
    t.rect(35, 13, 9, 8, S1)
    t.rect(37, 15, 5, 1, BR2)
    t.rect(0, 6, 9, 13, S2)
    t.ell(4.5, 12, 3, 4, B2)
    t.rect(3, 7, 3, 2, ARGENT)
    t.contour(ENCRE)
    dos("sac-explorateur", t, (23, 16), commentaire="Sac d'expédition (ensemble Explorateur)")


@dessin("cape-constellation")
def _():
    images = []
    for k in range(3):
        t = T(46, 30)
        ond = [0, 1, 0][k]
        t.poly([(9, 0), (37, 0), (44, 27 + ond), (34, 29 - ond), (23, 28 + ond), (12, 29 - ond), (2, 27 + ond)], V1)
        t.poly([(9, 0), (16, 0), (8, 28), (2, 27 + ond)], NUIT2)
        t.poly([(37, 0), (44, 27 + ond), (42, 27 + ond), (35, 0)], V2)
        pts = [(4, 24), (7, 17), (5, 11), (40, 10), (42, 18), (38, 25)]
        for i in range(len(pts) - 1):
            if i != 2:
                t.ligne(*pts[i], *pts[i + 1], V3)
        for i, (x, y) in enumerate(pts):
            etoile(t, x, y, J4 if (i + k) % 3 else BLANC)
        t.contour(ENCRE)
        images.append(t)
    dos("cape-constellation", images, (23, 4), duree=300, commentaire="Cape constellation (ensemble Astronome)")


@dessin("panier-dos")
def _():
    t = T(44, 30)
    t.poly([(31, 10), (43, 10), (41, 29), (33, 29)], BR3)
    for y in range(11, 29, 3):
        t.ligne(32, y, 42, y, BR2)
    for x in range(33, 42, 3):
        t.ligne(x, 11, x, 28, BR1)
    # Carottes orange et fanes sarcelle, un chou bleuté.
    for x0, h in ((33, 9), (37, 11), (40, 8)):
        t.poly([(x0 - 1, 10), (x0 + 2, 10), (x0 + 0.5, 10 - h + 4)], O3)
        t.ligne(x0, 10 - h + 3, x0 - 2, 10 - h, T3)
        t.ligne(x0 + 1, 10 - h + 3, x0 + 2, 10 - h, T2)
    t.ell(37, 8, 3, 2.5, T2)
    t.contour(ENCRE)
    dos("panier-dos", t, (22, 18), commentaire="Hotte de légumes (ensemble Jardinier)")


@dessin("plaid")
def _():
    t = T(44, 32)
    t.ell(22, 16, 19, 16, B2)
    t.rect(1, 14, 42, 16, B2)
    t.poly([(1, 29), (8, 29), (3, 31)], B2)
    t.poly([(43, 29), (36, 29), (41, 31)], B2)
    for y in range(32):
        for x in range(44):
            if t.get(x, y) == B2 and (x % 5 == 0 or y % 5 == 0):
                t.p(x, y, O3 if (x // 5 + y // 5) % 2 else CREME)
    t.contour(B1)
    dos("plaid", t, (22, 13), ancre="tete", commentaire="Plaid, Pilou emmitouflé (ensemble Hiver douillet)")


@dessin("cape-chauve-souris")
def _():
    images = []
    for k in range(3):
        t = T(54, 26)
        e = [0, 2, 1][k]
        for s in (-1, 1):
            pts = [(27, 8), (27 + s * 18, 1 + e), (27 + s * 26, 0 + e), (27 + s * 25, 9), (27 + s * 21, 13), (27 + s * 18, 11),
                   (27 + s * 15, 18), (27 + s * 11, 15), (27 + s * 8, 24), (27, 22)]
            t.poly(pts, V1)
            for bx, by in ((18, 1), (26, 0)):
                t.ligne(27 + s * 6, 9, 27 + s * bx, by + e + 1, V2)
            t.ligne(27 + s * 6, 10, 27 + s * 15, 17, V2)
        t.contour(ENCRE)
        images.append(t)
    dos("cape-chauve-souris", images, (27, 14), ancre="corps", duree=260,
        commentaire="Cape chauve-souris (ensemble Nuit des frissons)")


@dessin("hotte-cadeaux")
def _():
    t = T(46, 30)
    t.ell(38, 19, 8, 10, S2)
    t.ell(36, 16, 4, 5, S3)
    t.rect(32, 8, 12, 3, S1)
    for x0, y0, w, h, c, r in ((31, 1, 7, 8, B3, J3), (37, 3, 7, 6, O3, V4), (35, -2, 5, 5, V3, J4)):
        t.rect(x0, y0, w, h, c)
        t.rect(x0 + w // 2, y0, 1, h, r)
        t.rect(x0, y0 + h // 2, w, 1, r)
    t.contour(ENCRE)
    dos("hotte-cadeaux", t, (23, 16), commentaire="Hotte de cadeaux (ensemble Fêtes de l'hiver)")


@dessin("cartable")
def _():
    t = T(42, 20)
    t.rect(0, 4, 11, 14, O2)
    t.rect(0, 4, 11, 7, O3)
    t.rect(1, 5, 9, 1, O5)
    t.rect(4, 9, 3, 3, J3)
    t.p(5, 10, J1)
    t.anneau(5.5, 4, 3.5, 3, BR2, ep=1)
    t.rect(0, 17, 11, 1, O1)
    t.contour(ENCRE)
    dos("cartable", t, (21, 8), commentaire="Cartable (sur le dos)")


@dessin("cerf-volant")
def _():
    images = []
    for k in range(4):
        t = T(30, 46)
        sw = [0, 1, 2, 1][k]
        cx, cy = 8 + sw, 9
        t.poly([(cx, cy - 8), (cx + 6, cy), (cx, cy + 9), (cx - 6, cy)], O3)
        t.poly([(cx, cy - 8), (cx + 6, cy), (cx, cy)], B3)
        t.poly([(cx, cy), (cx - 6, cy), (cx, cy + 9)], B3)
        t.ligne(cx, cy - 8, cx, cy + 9, O1)
        t.ligne(cx - 6, cy, cx + 6, cy, O1)
        for i in range(5):
            y = cy + 10 + i * 4
            x = cx + int(math.sin(i + k) * 2)
            t.p(x, y, GRIS_C)
            if i % 2:
                t.rect(x - 1, y, 3, 1, V3)
        t.ligne(cx, cy + 9, 29, 45, GRIS_C)
        images.append(t)
    dos("cerf-volant", images, (24, 37), ancre="corps", duree=280, commentaire="Cerf-volant")


@dessin("ailes-libellule")
def _():
    images = []
    for k in range(4):
        t = T(48, 30)
        e = [0, 0.12, 0.2, 0.08][k]
        for s in (-1, 1):
            for ang, l, w in ((-0.45 - e, 12, 4), (0.35 + e, 10, 3.4)):
                dx, dy = math.cos(ang), math.sin(ang)
                cx, cy = 24 + s * dx * (l + 4), 15 + dy * (l + 4)
                rell(t, cx, cy, l, w, ang if s > 0 else -ang, "#d2eaffdd")
                for i in range(4, int(l * 2) + 2, 3):
                    t.p(24 + s * dx * i, 15 + dy * i, B3)
        t.contour(B2)
        images.append(t)
    dos("ailes-libellule", images, (24, 17), ancre="corps", duree=90, commentaire="Ailes de libellule")


@dessin("ailes-nuage")
def _():
    images = []
    for k in range(4):
        t = T(64, 32)
        e = [0, 2, 3, 1][k]
        for s in (-1, 1):
            for i, (dx, dy, r) in enumerate(((10, 14, 7), (18, 9 - e, 8), (26, 5 - e, 6), (22, 18, 6), (14, 22, 5))):
                t.ell(32 + s * dx, dy + 2, r, r * 0.8, BLANC if i % 2 else B4)
        for s in (-1, 1):
            for dx, dy in ((14, 12), (22, 8), (18, 18)):
                t.p(32 + s * dx, dy - e // 2, B3)
        t.contour(B2)
        images.append(t)
    dos("ailes-nuage", images, (32, 20), ancre="corps", duree=170, commentaire="Ailes de nuage")


# =====================================================================================================
# Main (flanc droit)
# =====================================================================================================
def main(id_, t, point, duree=0, commentaire=""):
    ecrire(id_, t, slot="main", ancre="main", point=point, duree=duree, commentaire=commentaire)


@dessin("boussole")
def _():
    t = T(15, 16)
    t.rect(6, 0, 3, 2, J2)
    t.ell(7.5, 9, 7, 7, J2)
    t.ell(7.5, 9, 5.6, 5.6, CREME)
    t.poly([(7.5, 4), (9, 9), (6, 9)], O3)
    t.poly([(7.5, 14), (9, 9), (6, 9)], B2)
    t.p(7, 8, ENCRE)
    for x, y in ((7, 4), (12, 9), (7, 13), (3, 9)):
        t.p(x, y, GRIS) if t.get(x, y) == CREME else None
    t.contour(J1)
    main("boussole", t, (4, 11), commentaire="Boussole (ensemble Explorateur)")


@dessin("fouet")
def _():
    t = T(12, 26)
    for r in (2.2, 3.6, 5):
        t.anneau(6, 7, r, 7, ARGENT, ep=1)
    t.ell(6, 7, 1, 1, None)
    t.rect(5, 13, 3, 3, ARGENT_C)
    t.rect(5, 16, 3, 9, B2)
    t.rect(5, 16, 1, 9, B3)
    t.contour(ENCRE)
    main("fouet", t, (6, 21), commentaire="Fouet (ensemble Pâtissier)")


@dessin("telescope")
def _():
    t = T(22, 22)
    for i in range(14):
        x, y = 2 + i, 15 - i
        w = 2 if i < 5 else 3 if i < 10 else 4
        for d in range(-w, w + 1):
            t.p(x + d * 0.5, y + d * 0.5 + 0.5, J3 if i % 5 else J2)
    t.ell(16.5, 2.5, 3, 3, J2)
    t.ell(16.5, 2.5, 1.8, 1.8, B2)
    t.p(16, 2, B4)
    t.ligne(5, 13, 5, 21, BR2)
    t.ligne(5, 13, 1, 21, BR2)
    t.ligne(5, 13, 9, 21, BR2)
    t.contour(ENCRE)
    main("telescope", t, (2, 16), commentaire="Lunette astronomique (ensemble Astronome)")


@dessin("sabre-cuillere")
def _():
    t = T(14, 30)
    t.ell(7, 5, 4.5, 5.5, ARGENT)
    t.ell(6, 4, 2.5, 3, ARGENT_C)
    t.rect(6, 10, 2, 11, ARGENT)
    t.ligne(1, 21, 12, 21, J2)
    t.ligne(1, 22, 12, 22, J3)
    t.rect(6, 23, 2, 6, CAFE2)
    t.contour(ENCRE)
    main("sabre-cuillere", t, (7, 25), commentaire="Sabre-cuillère (ensemble Pirate des mers de café)")


@dessin("arrosoir")
def _():
    images = []
    for k in range(3):
        t = T(16, 20)
        t.rect(0, 8, 9, 9, B2)
        t.rect(1, 9, 2, 7, B3)
        t.anneau(4.5, 8, 4, 3.5, B1, ep=1.2)
        t.ligne(8, 15, 13, 5, B1)
        t.ligne(9, 15, 14, 5, B2)
        t.rect(12, 3, 3, 3, B1)
        t.p(13, 3, B3)
        for i in range(3):
            if (i + k) % 3 != 2:
                t.p(14 - i % 2, 7 + i * 3 + k % 2, B4)
        t.contour(ENCRE)
        images.append(t)
    main("arrosoir", images, (6, 14), duree=220, commentaire="Arrosoir (ensemble Jardinier)")


@dessin("manette")
def _():
    t = T(22, 12)
    t.rect(4, 2, 14, 7, GRIS_C)
    t.ell(4, 7, 4, 4.5, GRIS_C)
    t.ell(18, 7, 4, 4.5, GRIS_C)
    t.rect(3, 5, 5, 1, ARDOISE)
    t.rect(5, 3, 1, 5, ARDOISE)
    t.ell(16, 4.5, 1.3, 1.3, O3)
    t.ell(18.5, 7, 1.3, 1.3, B3)
    t.rect(10, 4, 2, 1, ARDOISE)
    t.contour(ENCRE)
    main("manette", t, (11, 8), commentaire="Manette (ensemble Rétro-arcade)")


@dessin("chocolat-chaud")
def _():
    images = []
    for k in range(3):
        t = T(16, 20)
        t.rect(2, 9, 10, 10, O3)
        t.rect(3, 9, 8, 2, CAFE2)
        t.rect(3, 10, 2, 8, O4)
        t.anneau(13, 13, 3, 3.5, O2, ep=1.2)
        t.ell(7, 8.5, 2.4, 1.6, CREME)
        for i, x in enumerate((5, 9)):
            for y in range(0, 7):
                if (y + k + i) % 4 < 2:
                    t.p(x + int(math.sin((y + k) * 0.9) * 1.2), y, ARGENT_C)
        t.contour(ENCRE)
        images.append(t)
    main("chocolat-chaud", images, (3, 14), duree=260, commentaire="Chocolat chaud (ensemble Hiver douillet)")


@dessin("pelle-seau")
def _():
    t = T(14, 22)
    t.ligne(9, 0, 9, 9, B1)
    t.ligne(10, 0, 10, 9, B2)
    t.rect(8, 0, 4, 1, B1)
    t.poly([(1, 9), (13, 9), (11, 21), (3, 21)], O3)
    t.rect(1, 9, 12, 2, O2)
    t.rect(3, 12, 2, 8, O5)
    t.anneau(7, 9, 6, 5, O1, ep=1)
    t.contour(ENCRE)
    main("pelle-seau", t, (5, 16), commentaire="Seau et pelle (ensemble Plage)")


@dessin("lanterne-courge")
def _():
    images = []
    for k in range(3):
        t = T(16, 26)
        t.ligne(8, 0, 8, 10, BR2)
        t.ligne(8, 0, 13, 0, BR2)
        t.ell(8, 15, 7, 6, O3)
        for x in (5, 8, 11):
            t.ligne(x, 10, x, 20, O2)
        c = [J3, J4, J3][k]
        t.poly([(4, 13), (7, 13), (5.5, 11)], c)
        t.poly([(9, 13), (12, 13), (10.5, 11)], c)
        t.rect(5, 17, 6, 1, c)
        t.p(6, 18, c)
        t.p(9, 18, c)
        t.rect(7, 8, 2, 2, T1)
        t.contour(O1)
        images.append(t)
    main("lanterne-courge", images, (7, 20), duree=240, commentaire="Lanterne-courge (ensemble Nuit des frissons)")


@dessin("sucre-orge")
def _():
    t = T(12, 28)
    t.anneau(5, 5, 4.5, 4.5, CREME, ep=2.2)
    t.rect(0, 5, 12, 6, None)
    t.rect(8, 5, 2, 22, CREME)
    for y in range(28):
        for x in range(12):
            if t.get(x, y) == CREME and (x + y) % 4 < 2:
                t.p(x, y, O3)
    t.contour(O1)
    main("sucre-orge", t, (9, 23), commentaire="Sucre d'orge (ensemble Fêtes de l'hiver)")


@dessin("loupe")
def _():
    t = T(14, 22)
    t.ell(6, 6, 5.5, 5.5, BR2)
    t.ell(6, 6, 4.2, 4.2, B4)
    t.ell(5, 5, 1.6, 1.6, BLANC)
    t.ligne(9, 10, 12, 20, BR1)
    t.ligne(10, 10, 13, 20, BR2)
    t.contour(ENCRE)
    main("loupe", t, (10, 16), commentaire="Loupe")


@dessin("souffleur-bulles")
def _():
    images = []
    for k in range(4):
        t = T(18, 28)
        t.anneau(13, 7, 3.5, 3.5, O3, ep=1.2)
        t.ligne(13, 11, 13, 26, O2)
        for i in range(3):
            ph = (k / 4 + i / 3) % 1
            x, y = 9 - ph * 6, 7 - ph * 5 + i * 3
            r = 1.6 + i * 0.5
            t.anneau(x, y, r, r, B4, ep=0.9)
            t.p(int(x - r + 1), int(y - r + 1), BLANC)
        images.append(t)
    main("souffleur-bulles", images, (13, 22), duree=200, commentaire="Souffleur de bulles")


@dessin("pinceau")
def _():
    t = T(10, 26)
    t.rect(4, 9, 2, 16, BR3)
    t.rect(4, 7, 2, 3, ARGENT)
    t.poly([(3, 7), (7, 7), (5, 0)], V2)
    t.p(5, 2, V4)
    t.ell(8, 12, 1, 1.4, V3)
    t.contour(ENCRE)
    main("pinceau", t, (5, 20), commentaire="Pinceau")


@dessin("livre")
def _():
    t = T(20, 13)
    t.poly([(0, 2), (10, 4), (10, 13), (0, 11)], V2)
    t.poly([(20, 2), (10, 4), (10, 13), (20, 11)], V2)
    t.poly([(1, 1), (10, 3), (10, 11), (1, 9)], CREME)
    t.poly([(19, 1), (10, 3), (10, 11), (19, 9)], CREME)
    for y in (4, 6, 8):
        t.ligne(3, y - 1, 8, y, GRIS_C)
        t.ligne(12, y, 17, y - 1, GRIS_C)
    t.contour(V1)
    main("livre", t, (4, 8), commentaire="Livre ouvert")


@dessin("lampe-poche")
def _():
    images = []
    for k in range(2):
        t = T(14, 24)
        if k == 0:
            t.poly([(3, 8), (11, 8), (14, 0), (0, 0)], LUEUR)
        t.rect(4, 11, 6, 11, B1)
        t.rect(5, 11, 1, 11, B3)
        t.rect(3, 8, 8, 3, ARGENT)
        t.rect(4, 8, 6, 1, J4 if k == 0 else GRIS_C)
        t.rect(6, 15, 2, 2, O3)
        images.append(t)
    main("lampe-poche", images, (6, 18), duree=900, commentaire="Lampe de poche")


@dessin("ombrelle")
def _():
    t = T(32, 32)
    t.ell(16, 11, 15, 10, CREME, cond=lambda x, y, u, v: v < 0)
    for i in range(6):
        x = 3 + i * 5.2
        t.ell(x, 11, 2.7, 1.8, V3, cond=lambda x_, y_, u, v: v > -0.2)
    for x in range(3, 30, 4):
        t.ligne(16, 2, x, 10, V4)
    t.rect(15, 0, 2, 2, V1)
    t.rect(15, 11, 2, 18, ARGENT)
    t.ligne(16, 29, 13, 31, ARGENT)
    t.contour(V1)
    main("ombrelle", t, (16, 26), commentaire="Ombrelle")


@dessin("micro")
def _():
    t = T(10, 22)
    t.ell(5, 4, 4, 4, ARGENT)
    for y in range(1, 8, 2):
        t.ligne(2, y, 8, y, GRIS)
    t.rect(3, 8, 4, 2, V2)
    t.poly([(3, 10), (7, 10), (6, 21), (4, 21)], NOIR2)
    t.contour(ENCRE)
    main("micro", t, (5, 16), commentaire="Micro")


@dessin("fourchette-geante")
def _():
    t = T(12, 30)
    for x in (2, 5, 8):
        t.rect(x, 0, 2, 8, ARGENT)
    t.rect(2, 7, 8, 3, ARGENT)
    t.poly([(2, 10), (10, 10), (7, 13), (5, 13)], ARGENT)
    t.rect(5, 13, 2, 16, ARGENT_C)
    t.contour(GRIS)
    main("fourchette-geante", t, (6, 25), commentaire="Fourchette géante")


# =====================================================================================================
# Pieds
# =====================================================================================================
def pieds(id_, t, point, duree=0, commentaire=""):
    ecrire(id_, t, slot="pieds", ancre="pieds", point=point, duree=duree, commentaire=commentaire)


def paire(t, x0s, dessiner):
    for x0 in x0s:
        dessiner(x0)


@dessin("bottines")
def _():
    t = T(30, 10)
    for x0 in (0, 16):
        t.rect(x0 + 1, 0, 9, 7, BR2)
        t.ell(x0 + 10, 5, 3.5, 2.5, BR2)
        for y in (1, 3, 5):
            t.p(x0 + 4, y, O3)
            t.p(x0 + 6, y, O3)
        t.rect(x0, 7, 14, 2, NOIR2)
    t.contour(ENCRE)
    pieds("bottines", t, (15, 6), commentaire="Bottines de marche (ensemble Explorateur)")


@dessin("chaussons-creme")
def _():
    t = T(30, 8)
    for x0 in (0, 16):
        t.ell(x0 + 7, 4.5, 6.5, 3.5, CREME)
        t.ell(x0 + 7, 5, 4.5, 1.6, CREME_O)
        t.ell(x0 + 10, 2, 1.8, 1.8, B3)
    t.contour(GRIS)
    pieds("chaussons-creme", t, (15, 4), commentaire="Chaussons crème (ensemble Pâtissier)")


@dessin("bottes-jardin")
def _():
    t = T(30, 12)
    for x0 in (0, 16):
        t.rect(x0 + 2, 0, 8, 9, J3)
        t.rect(x0 + 3, 1, 2, 7, J4)
        t.ell(x0 + 10, 8, 3.5, 2.5, J3)
        t.rect(x0 + 1, 10, 13, 2, J1)
        t.rect(x0 + 2, 0, 8, 1, J2)
    t.contour(ENCRE)
    pieds("bottes-jardin", t, (15, 9), commentaire="Bottes de jardin (ensemble Jardinier)")


@dessin("chaussons-moumoute")
def _():
    t = T(32, 9)
    for x0 in (0, 17):
        t.ell(x0 + 7.5, 5, 7, 4, B4)
        for i in range(8):
            t.p(x0 + 1 + i * 2, 1 + i % 2, BLANC)
            t.p(x0 + 2 + i * 2, 2, BLANC)
        t.rect(x0 + 1, 7, 13, 2, B2)
    t.contour(B1)
    pieds("chaussons-moumoute", t, (16, 5), commentaire="Chaussons moumoute (ensemble Hiver douillet)")


@dessin("tongs")
def _():
    t = T(30, 6)
    for x0 in (0, 16):
        t.rect(x0, 3, 14, 2, O3)
        t.rect(x0, 5, 14, 1, O1)
        t.ligne(x0 + 3, 3, x0 + 7, 0, B2)
        t.ligne(x0 + 11, 3, x0 + 7, 0, B2)
    t.contour(ENCRE)
    pieds("tongs", t, (15, 3), commentaire="Tongs (ensemble Plage)")


@dessin("chaussettes-rayees")
def _():
    t = T(28, 11)
    for x0 in (0, 15):
        t.rect(x0 + 2, 0, 8, 8, CREME)
        t.ell(x0 + 9, 7.5, 3.5, 2.5, CREME)
        for y in range(0, 10, 3):
            t.rect(x0 + 2, y, 8, 1, O3)
        t.rect(x0 + 1, 9, 12, 1, O2)
    t.contour(O1)
    pieds("chaussettes-rayees", t, (14, 7), commentaire="Chaussettes rayées")


@dessin("sabots")
def _():
    t = T(30, 9)
    for x0 in (0, 16):
        t.ell(x0 + 7, 5, 7, 4, S2)
        t.ell(x0 + 5, 3, 3, 1.5, S3)
        t.rect(x0 + 1, 7, 12, 2, BR2)
        t.ell(x0 + 4, 5, 1.4, 1, BR1)
    t.contour(BR1)
    pieds("sabots", t, (15, 5), commentaire="Sabots")


@dessin("pantoufles-lapin")
def _():
    t = T(32, 13)
    for x0 in (0, 17):
        t.ell(x0 + 7.5, 9, 7, 3.8, CREME)
        for ex in (4, 9):
            t.ell(x0 + ex, 3.5, 1.6, 3.6, CREME)
            t.ell(x0 + ex, 3.8, 0.7, 2.4, ROSE)
        t.p(x0 + 11, 8, ENCRE)
        t.p(x0 + 13, 9, ROSE)
    t.contour(GRIS)
    pieds("pantoufles-lapin", t, (16, 9), commentaire="Pantoufles lapin")


@dessin("rollers")
def _():
    t = T(32, 12)
    for x0 in (0, 17):
        t.rect(x0 + 2, 0, 9, 7, V2)
        t.rect(x0 + 2, 0, 9, 1, V4)
        t.ell(x0 + 11, 5, 3.5, 2.5, V2)
        t.rect(x0 + 1, 7, 13, 1, ARDOISE)
        for wx in (3, 7, 11):
            t.ell(x0 + wx, 9.5, 1.6, 1.6, O3)
    t.contour(ENCRE)
    pieds("rollers", t, (16, 8), commentaire="Rollers")


@dessin("bottes-nuage")
def _():
    images = []
    for k in range(4):
        t = T(36, 10)
        for x0 in (0, 18):
            for i, (dx, r) in enumerate(((4, 3.5), (9, 4.5), (14, 3.5))):
                t.ell(x0 + dx, 6 + ((i + k) % 2) * 0.5, r, r * 0.7, BLANC if i == 1 else B4)
        eclat(t, [3, 33, 18, 10][k], [2, 2, 1, 1][k], J4, k)
        t.contour(B2)
        images.append(t)
    pieds("bottes-nuage", images, (18, 5), duree=240, commentaire="Bottes-nuages")


# =====================================================================================================
# Compagnons (au sol, à côté de Pilou ; ancre « cote »)
# =====================================================================================================
def compagnon(id_, images, point, duree=280, commentaire=""):
    ecrire(id_, images, slot="compagnon", ancre="cote", point=point, duree=duree, commentaire=commentaire)


@dessin("macaron")
def _():
    images = []
    for k in range(4):
        t = T(16, 16)
        h = [0, 2, 3, 1][k]
        y = 14 - h
        t.ell(8, y - 8, 7, 3.4, V4)
        t.rect(1, y - 6, 14, 3, CREME)
        t.rect(1, y - 6, 14, 1, BLANC)
        t.ell(8, y - 2, 7, 3, V4)
        t.ell(6, y - 9, 2, 1, BLANC)
        t.p(6, y - 4, ENCRE)
        t.p(10, y - 4, ENCRE)
        t.p(8, y - 3, ROSE)
        t.contour(V1)
        images.append(t)
    compagnon("macaron", images, (1, 15), duree=220, commentaire="Macaron vivant (ensemble Pâtissier)")


@dessin("mini-planete")
def _():
    images = []
    for k in range(6):
        t = T(22, 22)
        f = [0, 1, 1, 0, -1, -1][k]
        cy = 9 + f
        t.ell(11, cy, 5.5, 5.5, O3)
        t.ell(9.5, cy - 2, 2, 1.5, O5)
        t.p(9, cy, ENCRE)
        t.p(13, cy, ENCRE)
        t.p(11, cy + 2, O1)
        t.anneau(11, cy + 0.5, 10, 2.5, J3, ep=1)
        a = k / 6 * 2 * math.pi
        t.ell(11 + math.cos(a) * 9, cy - 5 + math.sin(a) * 2, 1.4, 1.4, B4)
        t.contour(ENCRE)
        images.append(t)
    compagnon("mini-planete", images, (0, 22), duree=260, commentaire="Mini-planète (ensemble Astronome)")


@dessin("perroquet-caramel")
def _():
    images = []
    for k in range(4):
        t = T(16, 22)
        h = 1 if k == 1 else 0
        t.ell(7, 11 - h, 5, 7, O3)
        t.ell(8, 4 - h, 4, 3.8, O3)
        t.ell(7, 13 - h, 3, 4, O5)
        t.poly([(3, 9 - h), (1, 18 - h), (6, 15 - h)], B2)
        t.poly([(11, 4 - h), (15, 5 - h), (12, 8 - h)], J3)
        t.p(9, 3 - h, ENCRE)
        t.poly([(4, 17), (2, 21), (6, 18)], O2)
        t.rect(6, 18, 1, 3, J1)
        t.rect(9, 18, 1, 3, J1)
        if k == 3:
            t.rect(13, 6, 2, 1, J3)
        t.contour(O1)
        images.append(t)
    compagnon("perroquet-caramel", images, (1, 21), duree=300, commentaire="Perroquet caramel (ensemble Pirate des mers de café)")


@dessin("escargot")
def _():
    images = []
    for k in range(4):
        t = T(20, 14)
        s = k % 2
        t.rect(1, 10, 17 + s, 3, CREME)
        t.ell(16 + s, 8, 2.5, 3, CREME)
        t.ligne(16 + s, 5, 15 + s, 1, CREME_O)
        t.ligne(18 + s, 5, 19 + s, 1, CREME_O)
        t.p(15 + s, 1, ENCRE)
        t.p(19 + s, 1, ENCRE)
        t.ell(8, 7, 6, 6, V2)
        for i in range(14):
            a = i * 0.7
            r = 0.6 + i * 0.32
            t.p(int(8 + math.cos(a) * r), int(7 + math.sin(a) * r), V4)
        t.contour(V1)
        images.append(t)
    compagnon("escargot", images, (1, 13), duree=420, commentaire="Escargot (ensemble Jardinier)")


@dessin("cube-pixel")
def _():
    images = []
    for k in range(4):
        h = [0, 3, 5, 3][k]
        sq = 1 if k == 0 else 0
        t = T(14, 18)
        y0 = 17 - 11 + sq - h
        t.rect(1 - sq, y0, 12 + 2 * sq, 11 - sq, V2)
        t.rect(1 - sq, y0, 12 + 2 * sq, 2, V3)
        t.rect(2, y0 + 1, 2, 1, V4)
        t.rect(4, y0 + 4, 2, 2, ENCRE)
        t.rect(8, y0 + 4, 2, 2, ENCRE)
        t.rect(5, y0 + 8, 4, 1, ENCRE)
        t.contour(V1)
        images.append(t)
    compagnon("cube-pixel", images, (1, 17), duree=150, commentaire="Cube pixel (ensemble Rétro-arcade)")


@dessin("bonhomme-neige")
def _():
    images = []
    for k in range(2):
        t = T(16, 22)
        t.ell(8, 16, 6, 5.5, BLANC)
        t.ell(8, 8, 4.5, 4.2, BLANC)
        t.rect(3, 10, 10, 2, B2)
        t.rect(10, 11, 2, 4, B2)
        t.p(6, 7, ENCRE)
        t.p(9, 7, ENCRE)
        t.rect(10, 8, 3, 1, O3)
        t.rect(4, 0, 8, 4, NOIR2)
        t.rect(2, 3, 12, 1, NOIR2)
        for y in (15, 18):
            t.p(8, y, ENCRE)
        t.ligne(2, 13, 0, 10 - k, BR2)
        t.contour(GRIS_C)
        images.append(t)
    compagnon("bonhomme-neige", images, (1, 21), duree=700, commentaire="Petit bonhomme de neige (ensemble Hiver douillet)")


@dessin("chauve-souris")
def _():
    images = []
    for k in range(4):
        t = T(20, 14)
        e = [0, 3, 5, 3][k]
        t.ell(10, 7, 3, 3.5, V1)
        t.poly([(9, 4), (8, 1), (10, 3)], V1)
        t.poly([(11, 4), (12, 1), (10, 3)], V1)
        for s in (-1, 1):
            t.poly([(10 + s * 2, 6), (10 + s * 9, 2 + e), (10 + s * 8, 7 + e // 2), (10 + s * 5, 6 + e // 2), (10 + s * 3, 9)], V2)
        t.p(9, 6, J4)
        t.p(11, 6, J4)
        t.contour(ENCRE)
        images.append(t)
    compagnon("chauve-souris", images, (0, 30), duree=120, commentaire="Chauve-souris (ensemble Nuit des frissons)")


@dessin("renne")
def _():
    images = []
    for k in range(2):
        t = T(18, 22)
        t.ell(8, 15, 6, 4, BR3)
        for x in (4, 7, 10, 12):
            t.rect(x, 17, 1, 4, BR2)
        t.ell(13, 9, 3, 3, BR3)
        t.ell(15, 10.5, 1.5, 1.4, O3 if k == 0 else J3)
        t.p(13, 8, ENCRE)
        t.ligne(12, 6, 10, 1, S2)
        t.ligne(11, 3, 9, 3, S2)
        t.ligne(14, 6, 16, 1, S2)
        t.ligne(15, 3, 17, 3, S2)
        t.ell(7, 16, 3, 1.5, S3)
        t.contour(BR1)
        images.append(t)
    compagnon("renne", images, (1, 21), duree=500, commentaire="Petit renne (ensemble Fêtes de l'hiver)")


@dessin("luciole")
def _():
    images = []
    for k in range(4):
        t = T(14, 14)
        f = [0, -1, -2, -1][k]
        t.ell(7, 9 + f, 5, 4, J4 + "55" if k % 2 == 0 else J4 + "33")
        t.ell(7, 9 + f, 2, 1.6, J3)
        t.ell(5, 7 + f, 1.6, 1.2, ARDOISE)
        t.p(4, 6 + f, ENCRE)
        t.ell(7, 6 + f, 2, 1.2, B4 + "cc")
        images.append(t)
    compagnon("luciole", images, (0, 30), duree=200, commentaire="Luciole")


@dessin("herisson")
def _():
    images = []
    for k in range(2):
        t = T(18, 13)
        t.ell(8, 8, 7, 5, BR2)
        for i in range(8):
            a = math.pi * (0.95 + i * 0.12)
            t.ligne(8 + math.cos(a) * 5, 8 + math.sin(a) * 4, 8 + math.cos(a) * 8, 8 + math.sin(a) * 7, BR1)
        t.ell(13, 9, 3.5, 3, S3)
        t.p(14, 8, ENCRE)
        t.p(16, 9 + k, ENCRE)
        t.rect(5, 12, 2, 1, S1)
        t.rect(11, 12, 2, 1, S1)
        t.contour(ENCRE)
        images.append(t)
    compagnon("herisson", images, (1, 12), duree=600, commentaire="Hérisson")


@dessin("tortue")
def _():
    images = []
    for k in range(4):
        t = T(20, 12)
        s = k % 2
        t.ell(16 + s, 7, 2.6, 2.4, S2)
        t.p(17 + s, 6, ENCRE)
        t.ell(9, 7, 7, 5, T2, cond=lambda x, y, u, v: v < 0.3)
        for cx in (6, 9, 12):
            t.anneau(cx, 5.5, 2, 1.6, T1, ep=0.8)
        t.rect(2, 8, 14, 1, S3)
        t.rect(4 - s, 9, 2, 2, S2)
        t.rect(12 + s, 9, 2, 2, S2)
        t.contour(ENCRE)
        images.append(t)
    compagnon("tortue", images, (1, 11), duree=500, commentaire="Tortue")


@dessin("mini-goutte")
def _():
    images = []
    for k in range(4):
        t = T(14, 18)
        h = [0, 2, 3, 1][k]
        y = 17 - h
        t.ell(7, y - 4.5, 5.5, 4.5, V3)
        t.ell(5.5, y - 6.5, 2, 1.2, V4)
        t.ell(7, y - 2.5, 4.5, 2, V2, cond=lambda x, yy, u, v: v > 0)
        t.p(5, y - 5, ENCRE)
        t.p(9, y - 5, ENCRE)
        t.p(4, y - 3, ROSE)
        t.ligne(7, y - 9, 7, y - 11, V1)
        t.p(7, y - 12, J3)
        t.contour(V1)
        images.append(t)
    compagnon("mini-goutte", images, (1, 17), duree=200, commentaire="Gouttinette, la petite sœur de Pilou")


@dessin("meduse")
def _():
    images = []
    for k in range(4):
        t = T(18, 26)
        f = [0, -1, -2, -1][k]
        t.ell(9, 6 + f, 7, 6, "#9b8cffcc", cond=lambda x, y, u, v: v < 0.3)
        t.ell(7, 4 + f, 2.5, 1.6, V4)
        for i, x in enumerate((4, 7, 10, 13)):
            for y in range(9, 22):
                xx = x + int(math.sin((y + k * 2 + i) * 0.6) * 1.2)
                if y % 2 or i % 2:
                    t.p(xx, y + f, B4 + "cc")
        t.p(7, 6 + f, ENCRE)
        t.p(11, 6 + f, ENCRE)
        eclat(t, 15, 2 + f, J4, k)
        images.append(t)
    compagnon("meduse", images, (0, 30), duree=240, commentaire="Méduse céleste")


@dessin("petit-crabe")
def _():
    images = []
    for k in range(4):
        t = T(20, 12)
        s = [0, 1, 0, -1][k]
        t.ell(10 + s, 7, 6, 3.5, O3)
        t.ell(9 + s, 6, 3, 1.5, O5)
        for x in (5, 8, 12, 15):
            t.ligne(x + s, 9, x + s + (1 if x > 10 else -1), 11, O2)
        for sx in (-1, 1):
            cx = 10 + s + sx * 8
            t.ell(cx, 3, 2.2, 2, O3)
            t.p(cx, 2, O1)
        t.p(8 + s, 4, ENCRE)
        t.p(12 + s, 4, ENCRE)
        t.contour(O1)
        images.append(t)
    compagnon("petit-crabe", images, (1, 11), duree=180, commentaire="Petit crabe")


@dessin("phenix")
def _():
    images = []
    for k in range(4):
        t = T(24, 26)
        e = [0, 2, 3, 1][k]
        for i in range(5):
            x = 4 + i * 3
            hgt = 5 + (i + k) % 3 * 2
            t.poly([(x - 2, 25), (x + 2, 25), (x + (k % 2), 25 - hgt)], O3 if i % 2 else J3)
        t.ell(12, 14, 4.5, 6, O3)
        t.ell(13, 7, 3, 3, O3)
        t.poly([(15, 6), (19, 7), (15, 8)], J3)
        t.p(14, 6, ENCRE)
        t.poly([(13, 4), (11, 0), (14, 3), (16, 0), (15, 4)], J3)
        t.poly([(9, 11), (1, 4 + e), (4, 14), (9, 16)], O2)
        t.poly([(9, 12), (3, 7 + e), (5, 13)], J3)
        t.ell(12, 15, 2.5, 3.5, J4)
        t.contour(O1)
        images.append(t)
    compagnon("phenix", images, (1, 25), duree=150, commentaire="Phénix de braise (mythique)")


# =====================================================================================================
# Effets (ancre corps, autour de Pilou)
# =====================================================================================================
def effet(id_, images, point, ancre="corps", couche="devant", duree=160, commentaire=""):
    ecrire(id_, images, slot="effet", ancre=ancre, point=point, couche=couche, duree=duree, commentaire=commentaire)


def libre(x, y, marge=(7, 8, 38, 46)):
    """Hors de la silhouette de Pilou (les effets tournent autour sans lui marcher dessus)."""
    x0, y0, x1, y1 = marge
    return not (x0 < x < x1 and y0 < y < y1)


@dessin("etincelles")
def _():
    images = []
    pts = [(3, 10), (44, 6), (8, 30), (42, 26), (24, 1), (2, 42), (46, 40), (14, 4), (36, 2)]
    for k in range(6):
        t = T(50, 46)
        for i, (x, y) in enumerate(pts):
            eclat(t, x, y, J4 if i % 2 else B4, (k + i) % 6 // 2 if (k + i) % 6 < 5 else 0)
        images.append(t)
    effet("etincelles", images, (25, 37), duree=150, commentaire="Étincelles")


def chute(id_, couleurs, forme, w=52, h=50, n=14, duree=160, commentaire="", point=None):
    images = []
    for k in range(8):
        t = T(w, h)
        for i in range(n):
            x0 = (i * 29 + 3) % (w - 4) + 2
            y = (i * 17 + k * h / 8) % h
            x = x0 + math.sin((y + i * 7) / 6) * 2.5
            if not libre(x, y, (9, 10, w - 9, h - 2)):
                continue
            forme(t, int(x), int(y), couleurs[i % len(couleurs)], (i + k) % 2)
        images.append(t)
    effet(id_, images, point or (w // 2, h - 8), duree=duree, commentaire=commentaire)


def petale(t, x, y, c, k):
    t.p(x, y, c)
    t.p(x + 1, y + (1 if k else 0), c)
    t.p(x, y + 1, c + "aa")


def feuille(t, x, y, c, k):
    if k:
        t.motif(x - 1, y - 1, [".c", "cc", "c."], {"c": c})
    else:
        t.motif(x - 1, y - 1, ["cc.", ".cc"], {"c": c})


def flocon(t, x, y, c, k):
    etoile(t, x, y, c) if k else t.p(x, y, c)


@dessin("pluie-petales")
def _():
    chute("pluie-petales", [ROSE, V4, O5, CREME], petale, commentaire="Pluie de pétales (printemps)")


@dessin("feuilles-tourbillon")
def _():
    chute("feuilles-tourbillon", [O3, O2, J3, BR3], feuille, n=12, duree=180, commentaire="Tourbillon de feuilles (automne)")


@dessin("cercle-glyphes")
def _():
    images = []
    for k in range(8):
        t = T(52, 14)
        t.anneau(26, 7, 25, 6.5, V2, ep=1)
        t.anneau(26, 7, 21, 5, V1, ep=1)
        for i in range(12):
            a = (i / 12 + k / 96) * 2 * math.pi
            x, y = 26 + math.cos(a) * 23, 7 + math.sin(a) * 5.8
            c = B4 if (i + k) % 4 == 0 else V3
            t.motif(int(x) - 1, int(y) - 1, [["c.c", ".c.", "c.c"], ["ccc", "...", "ccc"], [".c.", "ccc", ".c."]][i % 3],
                    {"c": c})
        images.append(t)
    effet("cercle-glyphes", images, (26, 9), ancre="pieds", couche="derriere", duree=120, commentaire="Cercle de glyphes")


@dessin("aurore-boreale")
def _():
    images = []
    for k in range(6):
        t = T(48, 26)
        for x in range(48):
            haut = 3 + math.sin(x / 6 + k * 0.6) * 3 + math.sin(x / 2.5) * 0.8
            long = 10 + math.sin(x / 4 + k) * 4
            for y in range(int(haut), int(haut + long)):
                f = (y - haut) / long
                c = T3 if f < 0.3 else B3 if f < 0.65 else V3
                if (x + k) % 3 or f < 0.5:
                    t.p(x, y, c + ("dd" if f < 0.5 else "88"))
        for i in range(4):
            t.p((i * 13 + k * 3) % 48, 1 + (i * 3) % 4, BLANC)
        images.append(t)
    effet("aurore-boreale", images, (24, 34), couche="derriere", duree=220, commentaire="Aurore boréale")


@dessin("orbite-lunes")
def _():
    images = []
    for k in range(12):
        t = T(56, 24)
        for i, c in enumerate((B4, J4, V4)):
            a = (k / 12 + i / 3) * 2 * math.pi
            x, y = 28 + math.cos(a) * 25, 12 + math.sin(a) * 9
            t.ell(x, y, 3, 3, c)
            t.ell(x - 0.8, y - 0.8, 1.4, 1.4, BLANC)
            t.p(x + 1, y + 1, GRIS_C)
            for j in range(1, 4):
                b = a - j * 0.18
                t.p(28 + math.cos(b) * 25, 12 + math.sin(b) * 9, c + "77")
        images.append(t)
    effet("orbite-lunes", images, (28, 14), duree=110, commentaire="Orbite de lunes (mythique)")


# ---- Bonus d'ensemble : un effet de plus, dessiné quand l'ensemble complet est porté.
@dessin("bonus-explorateur")
def _():
    images = []
    for k in range(8):
        t = T(56, 12)
        for i in range(10):
            a = math.pi * (0.05 + i * 0.1)
            x, y = 28 - math.cos(a) * 26, 6 + math.sin(a) * 4
            if (i - k) % 8 < 5:
                t.rect(int(x), int(y), 2, 1, S2)
        t.motif(48, 1, ["o...o", ".o.o.", "..o..", ".o.o.", "o...o"], {"o": O3})
        images.append(t)
    effet("bonus-explorateur", images, (28, 5), ancre="pieds", couche="derriere", duree=200,
          commentaire="Bonus de l'ensemble Explorateur : piste de pas et croix de carte")


@dessin("bonus-patissier")
def _():
    def vermicelle(t, x, y, c, k):
        if k:
            t.rect(x, y, 2, 1, c)
        else:
            t.rect(x, y, 1, 2, c)
    chute("bonus-patissier", [B3, O3, V3, J3, CREME], vermicelle, n=18, duree=140,
          commentaire="Bonus de l'ensemble Pâtissier : pluie de vermicelles")


@dessin("bonus-astronome")
def _():
    images = []
    for k in range(10):
        t = T(56, 28)
        for i in range(2):
            a = (k / 10 + i / 2) * 2 * math.pi
            x, y = 28 + math.cos(a) * 26, 14 + math.sin(a) * 8
            etoile(t, x, y, J4)
            for j in range(1, 5):
                b = a - j * 0.12
                t.p(28 + math.cos(b) * 26, 14 + math.sin(b) * 8, B4 if j < 3 else B3 + "88")
        for i, (x, y) in enumerate(((4, 2), (50, 4), (40, 0), (12, 26))):
            if (i + k) % 3 == 0:
                t.p(x, y, BLANC)
        images.append(t)
    effet("bonus-astronome", images, (28, 24), duree=120, commentaire="Bonus de l'ensemble Astronome : étoiles filantes en orbite")


@dessin("bonus-pirate")
def _():
    images = []
    for k in range(6):
        t = T(54, 44)
        for i, x in enumerate((4, 49, 10, 44)):
            for y in range(0, 16):
                yy = (y * 2 + k * 3 + i * 7) % 40
                if (y + k) % 5 < 3:
                    t.p(x + int(math.sin((yy + i) / 3) * 1.5), yy, ARGENT_C + "bb")
        for i, (x, y) in enumerate(((2, 30), (51, 22), (6, 8))):
            yy = y - (k + i) % 3
            t.ell(x, yy, 1.4, 1.8, CAFE2)
            t.p(x, yy, BR3)
        images.append(t)
    effet("bonus-pirate", images, (27, 38), duree=200, commentaire="Bonus de l'ensemble Pirate : vapeur de café et grains")


@dessin("bonus-jardinier")
def _():
    images = []
    for k in range(8):
        t = T(56, 44)
        for i, c in enumerate((O3, B3)):
            a = (k / 8 + i / 2) * 2 * math.pi
            x, y = 28 + math.cos(a) * 25, 18 + math.sin(2 * a) * 8
            ouvert = (k + i) % 2 == 0
            if ouvert:
                t.motif(int(x) - 2, int(y) - 1, ["c.c", "ccc", "c.c"], {"c": c})
            else:
                t.motif(int(x) - 1, int(y) - 1, [".c", "cc", ".c"], {"c": c})
            t.p(int(x), int(y), ENCRE)
        for i in range(3):
            petale(t, (i * 19 + k * 3) % 54, 30 + (i * 5 + k) % 12, [ROSE, J4, V4][i], k % 2)
        images.append(t)
    effet("bonus-jardinier", images, (28, 37), duree=170, commentaire="Bonus de l'ensemble Jardinier : papillons")


@dessin("bonus-arcade")
def _():
    images = []
    pts = [(2, 6), (46, 4), (5, 26), (48, 22), (24, 0), (40, 34), (8, 38)]
    for k in range(6):
        t = T(52, 44)
        for i, (x, y) in enumerate(pts):
            if (i + k) % 3 == 0:
                continue
            if i % 2:
                t.motif(x, y, [".o.o.", "ooooo", ".ooo.", "..o.."], {"o": O3})
            else:
                t.motif(x, y, ["..b..", ".bbb.", "bbbbb", ".b.b."], {"b": B3})
        images.append(t)
    effet("bonus-arcade", images, (26, 37), duree=180, commentaire="Bonus de l'ensemble Rétro-arcade : cœurs et étoiles 8 bits")


@dessin("bonus-hiver")
def _():
    chute("bonus-hiver", [BLANC, B4, ARGENT_C], flocon, n=16, duree=200, commentaire="Bonus de l'ensemble Hiver douillet : flocons")


@dessin("bonus-plage")
def _():
    images = []
    for k in range(6):
        t = T(56, 46)
        for i, (x, y) in enumerate(((6, 4), (48, 8), (2, 22), (52, 30), (26, 0))):
            eclat(t, x, y, J4, (k + i) % 3)
        for i in range(7):
            x = 4 + i * 8
            y = 42 - ((k + i) % 3)
            t.anneau(x, y, 1.6, 1.6, B4, ep=0.8)
        images.append(t)
    effet("bonus-plage", images, (28, 37), duree=170, commentaire="Bonus de l'ensemble Plage : reflets et écume")


@dessin("bonus-frissons")
def _():
    images = []
    for k in range(8):
        t = T(56, 44)
        for i in range(3):
            a = (k / 8 + i / 3) * 2 * math.pi
            x, y = 28 + math.cos(a) * 25, 20 + math.sin(a) * 14
            t.ell(x, y, 2.4, 2.4, B4 + "bb")
            t.ell(x, y, 1.2, 1.2, BLANC)
            t.poly([(x - 2, y), (x + 2, y), (x - math.cos(a) * 1 + 0.5, y + 5)], V4 + "88")
        images.append(t)
    effet("bonus-frissons", images, (28, 37), duree=150, commentaire="Bonus de l'ensemble Nuit des frissons : feux follets")


@dessin("bonus-fetes")
def _():
    images = []
    cols = [B3, O3, J3, V3]
    for k in range(4):
        t = T(56, 20)
        for x in range(56):
            y = 4 + (1 - math.cos(x / 55 * math.pi * 2)) * 4
            if x % 2 == 0:
                t.p(x, int(y), NOIR2)
        for j in range(9):
            x = 2 + j * 6.5
            y = 5 + (1 - math.cos(x / 55 * math.pi * 2)) * 4
            c = cols[(j + k) % 4]
            t.ell(x, y + 1, 1.3, 1.6, c)
            if (j + k) % 4 == 0:
                t.ell(x, y + 1, 2.6, 2.6, c + "44")
        images.append(t)
    effet("bonus-fetes", images, (28, 30), couche="derriere", duree=350, commentaire="Bonus de l'ensemble Fêtes : guirlande en arc")


# =====================================================================================================
# Décors : scènes de 64 × 48 derrière Pilou (sans ancre)
# =====================================================================================================
W, H = 64, 48


def fond(id_, images, duree=500, commentaire=""):
    ecrire(id_, images, duree=duree, commentaire=commentaire)


def ciel(t, haut, bas, h=H, coupe=0.55):
    for y in range(h):
        t.rect(0, y, W, 1, haut if y < h * coupe else bas)


@dessin("fond-patisserie")
def _():
    images = []
    for k in range(2):
        t = T(W, H)
        for x in range(W):
            t.rect(x, 0, 1, 30, CREME if (x // 4) % 2 else B4)
        t.rect(0, 10, W, 2, BR2)
        for i, x in enumerate(range(4, 60, 7)):
            t.ell(x + 2, 8, 2.6, 1.6, [V3, O4, B3, J4, ROSE][i % 5])
            t.rect(x, 7, 5, 1, CREME)
        t.rect(0, 30, W, 18, BR3)
        t.rect(0, 30, W, 2, S3)
        for x in range(2, 64, 6):
            t.rect(x, 34, 1, 14, BR2)
        # Gâteau à étages sur le comptoir.
        t.rect(6, 22, 14, 8, CREME)
        t.rect(9, 16, 8, 6, V4)
        t.rect(6, 22, 14, 2, V3)
        t.ell(13, 15, 1.6, 1.6, B2)
        t.p(13 if k else 12, 12, J4)
        t.rect(46, 24, 12, 6, S2)
        for x in (48, 51, 54):
            t.ell(x + 1, 23, 1.6, 1.6, O3)
        images.append(t)
    fond("fond-patisserie", images, duree=700, commentaire="Décor : pâtisserie (ensemble Pâtissier)")


@dessin("fond-observatoire")
def _():
    images = []
    for k in range(2):
        t = T(W, H)
        ciel(t, NUIT, NUIT2)
        for i in range(16):
            x, y = (i * 23 + 5) % 64, (i * 11 + 2) % 26
            t.p(x, y, J4 if (i + k) % 3 else B4)
        t.ell(32, 54, 40, 14, "#12283f")
        t.ell(46, 31, 11, 10, ARGENT, cond=lambda x, y, u, v: v < 0)
        t.rect(35, 30, 22, 8, GRIS_C)
        t.ell(42, 26, 2, 4, NUIT)
        t.ligne(43, 27, 52, 17, J2)
        t.ligne(44, 27, 53, 17, J3)
        for x in (38, 44, 50):
            t.rect(x, 33, 3, 3, J4 if k else J3)
        images.append(t)
    fond("fond-observatoire", images, duree=800, commentaire="Décor : observatoire (ensemble Astronome)")


@dessin("fond-mer-cafe")
def _():
    images = []
    for k in range(2):
        t = T(W, H)
        ciel(t, O4, O5, h=26)
        t.ell(14, 22, 6, 6, J3, cond=lambda x, y, u, v: v < 0.4)
        t.rect(0, 24, W, 24, CAFE2)
        for y in range(26, 48, 4):
            for x in range(0, 64, 8):
                t.rect(x + ((y // 4 + k) % 2) * 4, y, 4, 1, MOUSSE)
        # Île-tasse.
        t.rect(40, 16, 16, 12, CREME)
        t.rect(40, 16, 16, 2, CAFE)
        t.anneau(57, 22, 4, 4, CREME, ep=2)
        for i in range(3):
            t.p(44 + i * 4, 12 - (i + k) % 2, ARGENT_C)
            t.p(45 + i * 4, 9 - (i + k) % 2, ARGENT_C)
        images.append(t)
    fond("fond-mer-cafe", images, duree=600, commentaire="Décor : mer de café (ensemble Pirate des mers de café)")


@dessin("fond-potager")
def _():
    images = []
    for k in range(2):
        t = T(W, H)
        ciel(t, B4, "#d8ecff", h=28)
        t.ell(52, 8, 5, 5, J3)
        t.rect(0, 22, W, 26, BR2)
        for y in (28, 36, 44):
            t.rect(0, y, W, 1, BR1)
            for x in range(3, 64, 8):
                if y == 36:
                    t.poly([(x, y - 1), (x + 3, y - 1), (x + 1.5, y + 3)], O3)
                    t.ligne(x + 1, y - 2, x, y - 5 - k, T3)
                else:
                    t.ell(x + 2, y - 2, 3, 2.4, T2)
                    t.ell(x + 2, y - 2.5, 1.4, 1, T3)
        for x in range(0, 64, 5):
            t.rect(x, 17, 2, 6, S3)
        t.rect(0, 18, W, 1, S2)
        images.append(t)
    fond("fond-potager", images, duree=700, commentaire="Décor : potager (ensemble Jardinier)")


@dessin("fond-frissons")
def _():
    images = []
    for k in range(2):
        t = T(W, H)
        ciel(t, "#1a1040", "#2a1a5a")
        t.ell(46, 12, 8, 8, J4)
        t.ell(44, 10, 2, 2, J3)
        for x0 in (6, 56):
            t.rect(x0, 18, 3, 24, ENCRE)
            t.ligne(x0 + 1, 24, x0 - 6, 16, ENCRE)
            t.ligne(x0 + 1, 28, x0 + 7, 21, ENCRE)
        t.rect(0, 40, W, 8, "#120a2a")
        for x in (14, 34, 48):
            t.ell(x, 40, 4, 3, O3)
            t.p(x - 1, 39, J4 if (x + k) % 2 else J3)
            t.p(x + 1, 39, J4 if (x + k) % 2 else J3)
        images.append(t)
    fond("fond-frissons", images, duree=600, commentaire="Décor : nuit des frissons (ensemble Nuit des frissons)")


@dessin("fond-fetes")
def _():
    images = []
    for k in range(3):
        t = T(W, H)
        ciel(t, NUIT, NUIT2)
        for i, x in enumerate((2, 22, 42)):
            h = 14 + i % 2 * 4
            t.rect(x, 40 - h, 18, h, [V1, BR2, B1][i])
            t.poly([(x - 1, 40 - h), (x + 9, 40 - h - 7), (x + 19, 40 - h)], CREME)
            for wx in (x + 3, x + 11):
                t.rect(wx, 40 - h + 4, 4, 4, J3 if (i + k) % 3 else O4)
        t.rect(0, 40, W, 8, BLANC)
        for x in range(0, 64, 3):
            y = 10 + int((1 - math.cos(x / 63 * math.pi * 2)) * 3)
            t.p(x, y, [B3, O3, J3, V3][(x // 3 + k) % 4])
        for i in range(14):
            t.p((i * 17 + 3) % 64, (i * 7 + k * 5) % 38, BLANC)
        images.append(t)
    fond("fond-fetes", images, duree=500, commentaire="Décor : village en fête (ensemble Fêtes de l'hiver)")


@dessin("fond-montagne")
def _():
    images = []
    for k in range(2):
        t = T(W, H)
        ciel(t, B3, B4)
        for x0, h, c in ((-4, 30, B1), (20, 38, B2), (44, 28, B1)):
            t.poly([(x0, 40), (x0 + 16, 40 - h), (x0 + 32, 40)], c)
            t.poly([(x0 + 11, 40 - h + 7), (x0 + 16, 40 - h), (x0 + 21, 40 - h + 7), (x0 + 16, 40 - h + 5)], BLANC)
        t.rect(0, 38, W, 10, T2)
        for x in range(0, 64, 6):
            t.rect(x + (k * 3) % 6, 42, 3, 1, T3)
        t.ell(8 + k, 8, 5, 1.6, BLANC)
        images.append(t)
    fond("fond-montagne", images, duree=900, commentaire="Décor : montagne et lac")


@dessin("fond-ville")
def _():
    images = []
    for k in range(2):
        t = T(W, H)
        ciel(t, "#0b1530", NUIT)
        t.ell(10, 8, 3, 3, J4)
        for i, (x, w, h) in enumerate(((0, 10, 24), (11, 8, 32), (20, 12, 20), (33, 9, 36), (43, 10, 26), (54, 10, 30))):
            t.rect(x, 48 - h, w, h, [ARDOISE, NOIR2][i % 2])
            for wy in range(48 - h + 3, 46, 4):
                for wx in range(x + 2, x + w - 1, 3):
                    if (wx * 7 + wy * 3 + i + k) % 5 < 2:
                        t.p(wx, wy, J3 if (wx + wy) % 2 else O4)
        images.append(t)
    fond("fond-ville", images, duree=900, commentaire="Décor : ville la nuit")


@dessin("fond-bibliotheque")
def _():
    t = T(W, H)
    t.rect(0, 0, W, H, BR1)
    cols = [B2, O3, V2, J2, B1, O2, V3, S2]
    for y0 in (2, 16, 30):
        t.rect(0, y0 + 11, W, 2, BR3)
        x, i = 1, y0
        while x < 63:
            w = 2 + (i * 7) % 3
            h = 8 + (i * 5) % 3
            t.rect(x, y0 + 11 - h, w, h, cols[i % len(cols)])
            t.rect(x, y0 + 11 - h + 2, w, 1, J4 if i % 3 == 0 else CREME_O)
            x += w + (1 if i % 4 == 0 else 0)
            i += 1
    t.rect(0, 44, W, 4, BR2)
    fond("fond-bibliotheque", t, commentaire="Décor : bibliothèque")


@dessin("fond-cerisiers")
def _():
    images = []
    for k in range(2):
        t = T(W, H)
        ciel(t, B4, "#e6f2ff")
        t.rect(0, 38, W, 10, T2)
        for x0 in (12, 50):
            t.rect(x0 - 1, 24, 3, 16, BR2)
            for dx, dy, r in ((-6, 18, 6), (5, 17, 6), (0, 12, 7), (-2, 21, 5), (6, 22, 4)):
                t.ell(x0 + dx, dy, r, r * 0.8, ROSE if (dx + dy) % 2 else V4)
        for i in range(10):
            petale(t, (i * 13 + k * 5) % 62, (i * 9 + k * 7) % 38 + 4, [ROSE, V4][i % 2], k)
        images.append(t)
    fond("fond-cerisiers", images, duree=600, commentaire="Décor : cerisiers en fleurs (printemps)")


@dessin("fond-automne")
def _():
    images = []
    for k in range(2):
        t = T(W, H)
        ciel(t, O5, "#ffe8cc")
        for i, x0 in enumerate((6, 26, 46, 60)):
            t.rect(x0 - 1, 20, 3, 22, BR1)
            t.ell(x0, 14 + i % 2 * 3, 9, 9, [O3, O2, J3, BR3][i])
            t.ell(x0 - 3, 11 + i % 2 * 3, 3, 2, O5)
        t.rect(0, 40, W, 8, BR2)
        for x in range(0, 64, 3):
            t.p(x, 41 + x % 2, [O3, J3, BR3][x % 3])
        for i in range(6):
            feuille(t, (i * 11 + k * 4) % 62 + 1, (i * 7 + k * 9) % 34 + 4, [O3, J3, BR3][i % 3], k)
        images.append(t)
    fond("fond-automne", images, duree=600, commentaire="Décor : sous-bois d'automne")


@dessin("fond-aurore")
def _():
    images = []
    for k in range(3):
        t = T(W, H)
        t.rect(0, 0, W, H, "#07122a")
        for c, dy in ((T3 + "aa", 4), (B3 + "99", 10), (V3 + "88", 16)):
            for x in range(W):
                y0 = dy + math.sin(x / 8 + k * 0.8 + dy) * 3
                for y in range(int(y0), int(y0) + 6):
                    t.p(x, y, c)
        for i in range(12):
            t.p((i * 19 + 7) % 64, (i * 13) % 30, BLANC)
        t.ell(32, 56, 44, 16, BLANC)
        t.ell(32, 56, 44, 15, B4, cond=lambda x, y, u, v: v > -0.85)
        images.append(t)
    fond("fond-aurore", images, duree=500, commentaire="Décor : aurore boréale")


def tout():
    for f in DESSINS.values():
        f()
