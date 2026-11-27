"""Pinceaux du dessin fin (2×) pour les sprites dont la forme se rejoue : étincelles, cœurs, notes, bulles, pétales...

Les fonctions de dessin d'origine (generer.py, garde_robe_dessins.py...) les appellent dans un bloc `if toile.fin():`
à la place des pixels posés à la main du 1×. Coordonnées en unités de la grille 1× (demi-unités permises), pixels fins
calculés dessous. Le 1× n'est jamais touché.
"""
import math
from contextlib import contextmanager

ACTIF = False   # vrai pendant le dessin d'un sprite de la série 4 : les primitives d'origine passent en fin


@contextmanager
def lot():
    global ACTIF
    ACTIF = True
    try:
        yield
    finally:
        ACTIF = False


TEINTE = {"@contour": "#1f4f8a", "@ombre": "#4a8fdc", "@base": "#6cb6ff", "@clair": "#b4dbff"}


def _rvb(c):
    c = TEINTE.get(c, c)
    return int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16), c[7:9]


def clair(c, k=0.35):
    if c is None:
        return None
    r, v, b, a = _rvb(c)
    return "#%02x%02x%02x" % tuple(int(round(x + (255 - x) * k)) for x in (r, v, b)) + a


def sombre(c, k=0.2):
    if c is None:
        return None
    r, v, b, a = _rvb(c)
    return "#%02x%02x%02x" % tuple(int(round(x + (n - x) * k)) for x, n in zip((r, v, b), (20, 24, 48))) + a


def etincelle(t, cx, cy, c, bras=3, coeur=None, diag=True):
    """Étincelle à quatre branches centrée en (cx, cy) : branches d'un pixel fin qui s'effilent (la dernière plus
    pâle), petits pixels en diagonale autour du cœur, cœur plus clair."""
    e = t.e
    X, Y = int(round(cx * e)), int(round(cy * e))
    pale = clair(c, 0.45)
    for n in range(1, bras + 1):
        cc = pale if n == bras and bras > 2 else c
        for a, b in ((n, 0), (-n, 0), (0, n), (0, -n)):
            t.pf(X + a, Y + b, cc)
    if diag and bras >= 3:
        for a, b in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            t.pf(X + a, Y + b, c)
    t.pf(X, Y, coeur or c)


def point_fin(t, cx, cy, c, r=1.0):
    """Petit grain rond de r pixels fins de rayon (au moins 2 pixels fins)."""
    e = t.e
    X, Y = int(round(cx * e)), int(round(cy * e))
    t.pf(X, Y, c)
    t.pf(X - 1, Y, c)
    t.pf(X, Y - 1, c)
    t.pf(X - 1, Y - 1, c)


def _dans_coeur(u, v):
    u = u * 1.08
    for s in (-0.53, 0.53):
        if (u - s) ** 2 + (v + 0.44) ** 2 <= 0.55 ** 2:
            return True
    return v >= -0.35 and abs(u) <= (1.0 - v) * 0.93


def coeur_fin(t, x, y, w, h, fond, lueur=None, ombre=True):
    """Cœur plein dans la boîte (x, y, w, h) : lobes ronds, reflet en haut à gauche (couleur `lueur` ou plus claire que
    le fond), bord bas droit plus sombre."""
    e = t.e
    X0, Y0, X1, Y1 = int(round(x * e)), int(round(y * e)), int(round((x + w) * e)), int(round((y + h) * e))
    cx, cy, rx, ry = (X0 + X1) / 2, (Y0 + Y1) / 2, (X1 - X0) / 2, (Y1 - Y0) / 2
    cl, so = lueur or clair(fond, 0.3), sombre(fond, 0.2)
    dedans = []
    for Y in range(Y0, Y1):
        for X in range(X0, X1):
            u, v = (X + 0.5 - cx) / rx, (Y + 0.5 - cy) / ry
            if _dans_coeur(u, v):
                dedans.append((X, Y, u, v))
                t.pf(X, Y, so if (ombre and u + v * 0.8 > 0.95) else fond)
    for X, Y, u, v in dedans:
        if ((u + 0.52) / 0.3) ** 2 + ((v + 0.52) / 0.2) ** 2 <= 1 and t.getf(X, Y) == fond:
            t.pf(X, Y, cl)
    t.pf(int(cx - rx * 0.62), int(cy - ry * 0.5), clair(cl, 0.6))


def bulle_fin(t, cx, cy, r, c, reflet="#ffffff", plein=None):
    """Bulle : anneau fin d'un pixel fin, croissant de lumière en haut à gauche, éclat en bas à droite."""
    e = t.e
    R = r * e
    X0, Y0 = cx * e, cy * e
    for Y in range(int(Y0 - R) - 2, int(Y0 + R) + 3):
        for X in range(int(X0 - R) - 2, int(X0 + R) + 3):
            d = math.hypot(X + 0.5 - X0, Y + 0.5 - Y0)
            if R - 1.5 <= d <= R:
                ang = math.atan2(Y + 0.5 - Y0, X + 0.5 - X0)
                t.pf(X, Y, c if not (-2.5 < ang < -1.0 and R > 4) else clair(c, 0.5))
            elif plein and d < R - 1.5:
                t.pf(X, Y, plein)
    if R >= 4:
        a0 = math.radians(205)
        for i in range(8):
            a = a0 + i * 0.075
            t.pf(int(X0 + math.cos(a) * (R - 2.2)), int(Y0 + math.sin(a) * (R - 2.2)), reflet)
        t.pf(int(X0 + R * 0.55), int(Y0 + R * 0.55), reflet)
    elif R >= 2.5:
        t.pf(int(X0 - R * 0.45), int(Y0 - R * 0.45), reflet)


def note_fin(t, x, y, c):
    """Croche : tête ovale penchée, hampe fine, crochet qui s'effile, petit reflet sur la tête."""
    t.ell(x + 1.3, y + 3.8, 1.7, 1.25, c)
    t.rect(x + 2.5, y - 2, 0.5, 6, c)
    t.poly([(x + 3.0, y - 2), (x + 5.2, y - 0.4), (x + 4.9, y + 1.2), (x + 3.0, y - 0.2)], c)
    e = t.e
    t.pf(int((x + 0.7) * e), int((y + 3.3) * e), clair(c, 0.55))
    t.pf(int((x + 0.7) * e) + 1, int((y + 3.3) * e), clair(c, 0.55))
