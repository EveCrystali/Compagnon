"""Finition fine (2×) des effets de la boutique garnie : bonus d'ensemble (`bonus-*`), pluies (pétales, feuilles, flocons,
vermicelles), étincelles. Chaque image est redessinée en pixels fins avec les mêmes positions que le dessin 1×
(garde_robe_dessins.py) : mêmes images, mêmes durées, même silhouette d'ensemble, tracés plus fins.
"""
import math

import fins
from finition import finition, BLANC, ENCRE, NOIR2, ARGENT_C, B1, B2, B3, B4, O1, O2, O3, O4, O5, J2, J3, J4, V3, V4, S2, S3, \
    BR3, CREME, GRIS_C
from finition_lot3 import vider, trait_fin, etoile5

ROSE = "#ff9ec7"
CAFE, CAFE2 = "#3b2416", "#5c3a22"
clair, sombre = fins.clair, fins.sombre


def _libre(x, y, marge):
    x0, y0, x1, y1 = marge
    return not (x0 < x < x1 and y0 < y < y1)


def _chute(t, k, couleurs, forme, n=14):
    """Même placement que garde_robe_dessins.chute, dessin de `forme(t, x, y, c, k)` en fin."""
    w, h = t.w, t.h
    for i in range(n):
        x0 = (i * 29 + 3) % (w - 4) + 2
        y = (i * 17 + k * h / 8) % h
        x = x0 + math.sin((y + i * 7) / 6) * 2.5
        if not _libre(x, y, (9, 10, w - 9, h - 2)):
            continue
        forme(t, int(x), int(y), couleurs[i % len(couleurs)], (i + k) % 2)


# ---- formes de chute --------------------------------------------------------------------------------
def vermicelle(t, x, y, c, k):
    e = t.e
    X, Y = x * e, y * e
    long, larg = (5, 2) if k else (2, 5)
    for j in range(larg):
        for i in range(long):
            t.pf(X + i, Y + j, c)
    t.pf(X, Y, clair(c, 0.5))
    t.pf(X + long - 1, Y + larg - 1, sombre(c, 0.25))


def flocon(t, x, y, c, k):
    e = t.e
    X, Y = x * e + 1, y * e + 1
    if k:
        for n in range(1, 3):
            for a, b in ((n, 0), (-n, 0), (0, n), (0, -n)):
                t.pf(X + a, Y + b, c)
        for a, b in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
            t.pf(X + a, Y + b, c)
        t.pf(X, Y, BLANC)
    else:
        for a, b in ((0, 0), (1, 0), (0, 1), (1, 1)):
            t.pf(X + a, Y + b, c)


def petale(t, x, y, c, k):
    t.ell(x + 0.9, y + 0.8, 1.15, 0.7 if k else 0.85, c)
    t.pf(int((x + 0.4) * t.e), int((y + 0.5) * t.e), clair(c, 0.5))


def feuille(t, x, y, c, k):
    e = t.e
    ang = math.radians(-40 if k else 40)
    ca, sa = math.cos(ang), math.sin(ang)
    cx, cy = x + 0.3, y + 0.5
    nerv = sombre(c, 0.25)
    for Y in range(int((cy - 3) * e), int((cy + 3) * e)):
        for X in range(int((cx - 3) * e), int((cx + 3) * e)):
            dx, dy = (X + 0.5) / e - cx, (Y + 0.5) / e - cy
            u, v = (dx * ca + dy * sa) / 2.1, (-dx * sa + dy * ca) / 0.95
            if u * u + v * v <= 1 - 0.0 * u:
                t.pf(X, Y, nerv if abs(v) < 0.12 else c)


@finition("bonus-patissier", auto=False)
def _patissier(t, k):
    vider(t)
    _chute(t, k, [B3, O3, V3, J3, CREME], vermicelle, 18)


@finition("bonus-hiver", auto=False)
def _hiver(t, k):
    vider(t)
    _chute(t, k, [BLANC, B4, ARGENT_C], flocon, 16)


@finition("pluie-petales", auto=False)
def _petales(t, k):
    vider(t)
    _chute(t, k, [ROSE, V4, O5, CREME], petale)


@finition("feuilles-tourbillon", auto=False)
def _feuilles(t, k):
    vider(t)
    _chute(t, k, [O3, O2, J3, BR3], feuille, 12)


# ---- bonus d'ensemble --------------------------------------------------------------------------------
@finition("bonus-explorateur", auto=False)
def _explorateur(t, k):
    vider(t)
    for i in range(10):
        a = math.pi * (0.05 + i * 0.1)
        x, y = 28 - math.cos(a) * 26, 6 + math.sin(a) * 4
        if (i - k) % 8 < 5:
            yy = y + (0.55 if i % 2 else -0.35)
            t.ell(x + 1.1, yy + 0.5, 1.25, 0.8, S2)
            t.ell(x + 2.3, yy + 0.5, 0.45, 0.4, S2)
            for X in range(int((x - 0.2) * t.e), int((x + 2.4) * t.e)):
                Y0 = int((yy - 0.3) * t.e)
                if t.getf(X, Y0) == S2:
                    t.pf(X, Y0, S3)
                Y1 = int((yy + 1.3) * t.e) - 1
                if t.getf(X, Y1) == S2:
                    t.pf(X, Y1, "#8a6e4b")
    # Croix de la carte : deux barres épaisses, lumière en haut à gauche, ombre en dessous à droite.
    for (a, b, c, d) in ((48.7, 1.7, 52.3, 5.3), (52.3, 1.7, 48.7, 5.3)):
        dx, dy = (d - b), -(c - a)
        n = math.hypot(dx, dy)
        dx, dy = dx / n * 0.62, dy / n * 0.62
        barre = [(a + dx, b + dy), (c + dx, d + dy), (c - dx, d - dy), (a - dx, b - dy)]
        t.poly([(x + 0.3, y + 0.3) for x, y in barre], O2)
        t.poly(barre, O3)


@finition("bonus-astronome", auto=False)
def _astronome(t, k):
    vider(t)
    e = t.e
    for i in range(2):
        a = (k / 10 + i / 2) * 2 * math.pi
        x, y = 28 + math.cos(a) * 26, 14 + math.sin(a) * 8
        for j in range(1, 11):
            b = a - j * 0.055
            X, Y = int((28 + math.cos(b) * 26) * e), int((14 + math.sin(b) * 8) * e)
            c = B4 if j <= 4 else B3 + "cc" if j <= 7 else B3 + "66"
            for (dx, dy) in ((0, 0), (1, 0), (0, 1), (1, 1)) if j <= 3 else ((0, 0),):
                t.pf(X + dx, Y + dy, c)
        fins.etincelle(t, int(x) + 0.5, int(y) + 0.5, J4, bras=4, coeur=BLANC)
    for i, (x, y) in enumerate(((4, 2), (50, 4), (40, 0), (12, 26))):
        if (i + k) % 3 == 0:
            fins.point_fin(t, x + 0.5, y + 0.5, BLANC)


@finition("bonus-pirate", auto=False)
def _pirate(t, k):
    vider(t)
    e = t.e
    for i, x in enumerate((4, 49, 10, 44)):
        for y in range(0, 16):
            yy = (y * 2 + k * 3 + i * 7) % 40
            if (y + k) % 5 < 3:
                n = int(2.2 * e)
                for m in range(n):
                    sy = yy + m / e
                    X = int((x + math.sin((sy + i) / 3) * 1.5) * e)
                    t.pf(X, int(sy * e), ARGENT_C + ("bb" if m < n - 1 else "66"))
                    if m == 0:
                        t.pf(X + 1, int(sy * e), ARGENT_C + "44")
    for i, (x, y) in enumerate(((2, 30), (51, 22), (6, 8))):
        yy = y - (k + i) % 3
        t.ell(x, yy, 1.4, 1.8, CAFE2)
        trait_fin(t, x - 0.1, yy - 1.4, x + 0.15, yy + 1.4, CAFE, 1)
        t.pf(int((x - 0.6) * e), int((yy - 0.9) * e), BR3)
        t.pf(int((x - 0.6) * e) + 1, int((yy - 0.9) * e), BR3)


@finition("bonus-jardinier", auto=False)
def _jardinier(t, k):
    vider(t)
    e = t.e
    for i, c in enumerate((O3, B3)):
        a = (k / 8 + i / 2) * 2 * math.pi
        x, y = 28 + math.cos(a) * 25, 18 + math.sin(2 * a) * 8
        x, y = int(x) + 0.5, int(y) + 0.5
        bas, tache = sombre(c, 0.25), clair(c, 0.6)
        if (k + i) % 2 == 0:
            t.ell(x - 1.9, y - 0.9, 1.7, 1.2, c)
            t.ell(x + 1.9, y - 0.9, 1.7, 1.2, c)
            t.ell(x - 1.3, y + 1.0, 1.2, 0.95, bas)
            t.ell(x + 1.3, y + 1.0, 1.2, 0.95, bas)
            for sx in (-1, 1):
                t.pf(int((x + sx * 2.1) * e), int((y - 1.1) * e), tache)
                t.pf(int((x + sx * 2.1) * e) - 1, int((y - 1.1) * e), tache)
        else:
            t.ell(x + 0.8, y - 0.2, 1.1, 1.7, c)
            t.ell(x + 0.6, y + 1.3, 0.8, 0.8, bas)
            t.pf(int((x + 0.6) * e), int((y - 0.9) * e), tache)
        trait_fin(t, x, y - 1.2, x, y + 1.3, ENCRE, 1)
        trait_fin(t, x, y - 1.2, x - 0.9, y - 2.4, ENCRE, 1)
        trait_fin(t, x, y - 1.2, x + 0.9, y - 2.4, ENCRE, 1)
    for i in range(3):
        petale(t, (i * 19 + k * 3) % 54, 30 + (i * 5 + k) % 12, [ROSE, J4, V4][i], k % 2)


@finition("bonus-arcade", auto=False)
def _arcade(t, k):
    vider(t)
    pts = [(2, 6), (46, 4), (5, 26), (48, 22), (24, 0), (40, 34), (8, 38)]
    for i, (x, y) in enumerate(pts):
        if (i + k) % 3 == 0:
            continue
        if i % 2:
            fins.coeur_fin(t, x, y, 5, 4.3, O3, lueur=O5)
        else:
            etoile5(t, x + 2.5, y + 2.3, 2.7, B3, c_clair=B4, c_ombre=B2)


@finition("bonus-plage", auto=False)
def _plage(t, k):
    vider(t)
    for i, (x, y) in enumerate(((6, 4), (48, 8), (2, 22), (52, 30), (26, 0))):
        m = (k + i) % 3
        if m == 0:
            fins.point_fin(t, x + 0.5, y + 0.5, J4)
        elif m == 1:
            fins.etincelle(t, x + 0.5, y + 0.5, J4, bras=3, coeur=BLANC)
        else:
            fins.etincelle(t, x + 0.5, y + 0.5, J4, bras=5, coeur=BLANC)
    for i in range(7):
        x = 4 + i * 8
        y = 42 - ((k + i) % 3)
        fins.bulle_fin(t, x, y, 1.9, B4)


@finition("bonus-frissons", auto=False)
def _frissons(t, k):
    vider(t)
    for i in range(3):
        a = (k / 8 + i / 3) * 2 * math.pi
        x, y = 28 + math.cos(a) * 25, 20 + math.sin(a) * 14
        for j in range(8):
            c = V4 + ("99" if j < 3 else "55" if j < 6 else "33")
            t.ell(x - math.cos(a) * j * 0.12 + math.sin(j * 0.9) * 0.5, y + 1.5 + j * 0.65, 1.7 - j * 0.17, 0.55, c)
        t.ell(x, y, 3.5, 3.5, B4 + "33")
        t.ell(x, y, 2.5, 2.5, B4 + "88")
        t.ell(x, y, 1.6, 1.6, B4)
        t.ell(x, y, 0.9, 0.9, BLANC)


@finition("bonus-fetes", auto=False)
def _fetes(t, k):
    vider(t)
    e = t.e
    cols = [B3, O3, J3, V3]
    for X in range(56 * e):
        x = X / e
        y = 4 + (1 - math.cos(x / 55 * math.pi * 2)) * 4
        t.pf(X, int(y * e), NOIR2)
    for j in range(9):
        x = 2 + j * 6.5
        y = 5 + (1 - math.cos(x / 55 * math.pi * 2)) * 4
        c = cols[(j + k) % 4]
        if (j + k) % 4 == 0:
            t.ell(x, y + 1.4, 2.8, 2.8, c + "44")
            t.ell(x, y + 1.4, 2.0, 2.0, c + "66")
        t.rect(x - 0.5, y - 0.1, 1, 0.8, NOIR2)
        t.ell(x, y + 1.5, 1.15, 1.5, c)
        t.pf(int((x - 0.5) * e), int((y + 0.9) * e), clair(c, 0.6))
        t.pf(int((x - 0.5) * e), int((y + 0.9) * e) + 1, clair(c, 0.4))
        t.pf(int((x + 0.3) * e), int((y + 2.3) * e), sombre(c, 0.3))
