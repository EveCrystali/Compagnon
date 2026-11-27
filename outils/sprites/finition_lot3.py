"""Finition fine (2×) de la quatrième série (fin.SERIE4) : ce qui restait agrandi automatiquement.

Pas de lumière générique : chaque sprite a son dessin fin (formes rejouées à la finesse double, puis reflets, liserés et
ombres posés à la main). Les coordonnées sont celles de la grille 1× (demi-unités permises) ; `t.pf` / les pinceaux
de finition.py travaillent en pixels fins. Palette : bleus, oranges, violets, jaunes, neutres, jamais rouge contre vert.
"""
import math

from finition import *  # noqa: F401,F403
import fins
from finition import finition, disque, trait, arc, points, poly, scintille, eclaircir, assombrir


def vider(t):
    for r in t.g:
        for i in range(len(r)):
            r[i] = None


def px(t, pts, c):
    """Pixels fins (X, Y) de la grille réelle."""
    for X, Y in pts:
        t.pf(X, Y, c)


def trait_fin(t, x0, y0, x1, y1, c, ep=1):
    """Ligne de ep pixels fins d'épaisseur (coordonnées 1×), sur le vide comme sur le dessiné."""
    e = t.e
    X0, Y0, X1, Y1 = int(round(x0 * e)), int(round(y0 * e)), int(round(x1 * e)), int(round(y1 * e))
    dx, dy = abs(X1 - X0), -abs(Y1 - Y0)
    sx, sy = (1 if X0 < X1 else -1), (1 if Y0 < Y1 else -1)
    err = dx + dy
    while True:
        for b in range(ep):
            for a in range(ep):
                t.pf(X0 + a, Y0 + b, c)
        if X0 == X1 and Y0 == Y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            X0 += sx
        if e2 <= dx:
            err += dx
            Y0 += sy


def etoile5(t, cx, cy, r, c, c_clair=None, c_ombre=None):
    """Étoile à cinq branches pleine (coordonnées 1×), flanc bas droit ombré, cœur éclairé."""
    pts = []
    for i in range(10):
        a = math.radians(-90 + i * 36)
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    t.poly(pts, c)
    e = t.e
    if c_ombre:
        for Y in range(t.H):
            for X in range(t.W):
                if t.g[Y][X] == c and ((X + 0.5) / e - cx) + ((Y + 0.5) / e - cy) > r * 0.45:
                    t.g[Y][X] = c_ombre
    if c_clair:
        t.ell(cx - r * 0.18, cy - r * 0.2, r * 0.3, r * 0.26, c_clair)


# ======================================================================================================
# Variantes d'évolution (visage et tête, stades 2 à 4)
# ======================================================================================================
def _joues(t, k):
    """Deux joues en galet : coins arrondis, éclat en haut à gauche, bas un ton plus chaud."""
    W = t.W
    vider(t)
    for X0 in (0, W - 8):
        for Y in range(0, 4):
            for X in range(X0, X0 + 8):
                if (Y in (0, 3)) and X in (X0, X0 + 7):
                    continue
                t.pf(X, Y, O3 if Y == 3 else O4)
        px(t, [(X0 + 2, 0), (X0 + 3, 0), (X0 + 2, 1)], O5)
        px(t, [(X0 + 1, 3), (X0 + 6, 3)], None)


for _s in (2, 3, 4):
    finition("variante-calin-%d" % _s, auto=False)(_joues)


def _etoile_joue(t, k):
    """Petite étoile à quatre branches avec un cœur plus clair et deux étincelles."""
    vider(t)
    W = t.W
    cx, cy = W - 5, 3
    for n in range(0, 4):
        for a, b in ((n, 0), (-n, 0), (0, n), (0, -n)):
            c = J3 if n < 3 else J4
            if n == 3 and (a == 0 or True):
                c = J3
            t.pf(cx + a, cy + b, c)
    px(t, [(cx - 1, cy - 1), (cx + 1, cy - 1), (cx - 1, cy + 1), (cx + 1, cy + 1)], J3)
    px(t, [(cx, cy), (cx - 1, cy), (cx, cy - 1)], J4)
    px(t, [(cx + 1, cy + 1)], J2)
    px(t, [(cx + 3, cy - 3)], J4)


for _s in (2, 3, 4):
    finition("variante-espiegle-%d" % _s, auto=False)(_etoile_joue)


def _brin(t, p0, c, p2, r0, r1, col, plus=0.0):
    """Brin courbe qui s'effile : disques le long d'une courbe de Bézier (coordonnées 1×), rayons r0 → r1."""
    e = t.e
    for i in range(61):
        k = i / 60.0
        x = (1 - k) ** 2 * p0[0] + 2 * k * (1 - k) * c[0] + k * k * p2[0]
        y = (1 - k) ** 2 * p0[1] + 2 * k * (1 - k) * c[1] + k * k * p2[1]
        r = (r0 + (r1 - r0) * k + plus) * e
        X0, Y0 = x * e, y * e
        for Y in range(int(Y0 - r) - 1, int(Y0 + r) + 2):
            for X in range(int(X0 - r) - 1, int(X0 + r) + 2):
                if (X + 0.5 - X0) ** 2 + (Y + 0.5 - Y0) ** 2 <= r * r:
                    t.pf(X, Y, col)


def _meche(t, k):
    """Mèche rebelle : trois brins qui s'effilent, cerne sombre, cœur à la teinte de Pilou, filet de lumière."""
    vider(t)
    brins = [((2.0, 7.0), (1.2, 3.4), (3.4, 0.8)), ((4.7, 7.0), (4.1, 3.0), (5.2, 0.6)), ((7.0, 7.0), (6.4, 4.2), (8.2, 2.0))]
    for p0, c, p2 in brins:
        _brin(t, p0, c, p2, 1.45, 0.45, "@contour")
    for p0, c, p2 in brins:
        _brin(t, p0, c, p2, 0.95, 0.1, "@base")
    for p0, c, p2 in brins:
        _brin(t, (p0[0] - 0.2, p0[1] - 1.0), (c[0] - 0.25, c[1]), (p2[0] - 0.1, p2[1] + 1.4), 0.3, 0.0, "@clair")


def _poly_libre(t, pts, c):
    """Polygone plein (coordonnées 1×) qui peint aussi sur le vide."""
    e = t.e
    for Y in range(t.H):
        yc = (Y + 0.5) / e
        xs = []
        for i in range(len(pts)):
            (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
            if (y0 <= yc < y1) or (y1 <= yc < y0):
                xs.append(x0 + (yc - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for a, b in zip(xs[0::2], xs[1::2]):
            for X in range(t.W):
                if a <= (X + 0.5) / e < b:
                    t.g[Y][X] = c


for _s in (2, 3, 4):
    finition("variante-espiegle-%d-tete" % _s, auto=False)(_meche)


import finition_effets  # noqa: E402,F401  (effets, bonus d'ensemble)
import finition_objets  # noqa: E402,F401  (icônes, accessoires, objets)
