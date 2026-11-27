"""Finition fine (2×) des icônes et accessoires de la quatrième série : cadenas, badge, pièce d'or, ballon, marmites, bonus
de base, bulle, clochette, accessoires de tête / cou, appareil photo, arrosoir...

Chaque sprite est soit redessiné en pixels fins à partir de ses formes (même silhouette, mêmes ancrages, dimensions ×2),
soit retouché sur le rejeu fin avec des pinceaux ciblés (reflets, ombres douces, liserés). Aucune règle générale.
"""
import math

import fins
from finition import finition, trait, arc, points, disque, poly, composantes, \
    ENCRE, NOIR2, BLANC, CREME, CREME_O, GRIS, GRIS_C, ARDOISE, ARGENT, ARGENT_C, B1, B2, B3, B4, O1, O2, O3, O4, O5, \
    J1, J2, J3, J4, V1, V2, V3, V4, S1, S2, S3, BR1, BR2, BR3, T1, T2, T3
from finition_lot3 import vider, px, trait_fin
from retouches_fines import eclaircir, assombrir

clair, sombre = fins.clair, fins.sombre


# ---- pinceaux de retouche --------------------------------------------------------------------------
def rr(t, x, y, w, h, r, c):
    """Rectangle à coins arrondis (coordonnées 1×), rayon r, peint même sur le vide."""
    e = t.e
    for Y in range(int(y * e), int((y + h) * e)):
        for X in range(int(x * e), int((x + w) * e)):
            px_, py_ = (X + 0.5) / e, (Y + 0.5) / e
            dx = max(x + r - px_, px_ - (x + w - r), 0)
            dy = max(y + r - py_, py_ - (y + h - r), 0)
            if dx * dx + dy * dy <= r * r:
                t.pf(X, Y, c)


def teinte_ell(t, cx, cy, rx, ry, sur, c, cond=None):
    """Recolore en `c` les pixels de couleur `sur` (ensemble ou couleur) dans l'ellipse ; cond(u, v) précise."""
    e = t.e
    sur = sur if isinstance(sur, (set, frozenset, tuple, list)) else {sur}
    for Y in range(max(0, int((cy - ry) * e) - 1), min(t.H, int((cy + ry) * e) + 2)):
        for X in range(max(0, int((cx - rx) * e) - 1), min(t.W, int((cx + rx) * e) + 2)):
            u, v = ((X + 0.5) / e - cx) / rx, ((Y + 0.5) / e - cy) / ry
            if u * u + v * v <= 1 and t.g[Y][X] in sur and (cond is None or cond(u, v)):
                t.g[Y][X] = c


def croissant(t, cx, cy, rx, ry, sur, c, decal=(0.3, 0.3), reduit=0.8):
    """Croissant d'ombre : pixels `sur` de l'ellipse qui sortent d'une ellipse plus petite décalée (en bas à droite)."""
    e = t.e
    sur = sur if isinstance(sur, (set, frozenset, tuple, list)) else {sur}
    for Y in range(max(0, int((cy - ry) * e) - 1), min(t.H, int((cy + ry) * e) + 2)):
        for X in range(max(0, int((cx - rx) * e) - 1), min(t.W, int((cx + rx) * e) + 2)):
            x_, y_ = (X + 0.5) / e, (Y + 0.5) / e
            u, v = (x_ - cx) / rx, (y_ - cy) / ry
            if u * u + v * v <= 1 and t.g[Y][X] in sur:
                u3, v3 = (x_ - cx + decal[0] * rx) / (rx * reduit), (y_ - cy + decal[1] * ry) / (ry * reduit)
                if u3 * u3 + v3 * v3 > 1:
                    t.g[Y][X] = c


def recolorer(t, avant, apres):
    for r in t.g:
        for i, v in enumerate(r):
            if v == avant:
                r[i] = apres


def bord_interne(t, c, vers, cotes, epais=1, cond=None):
    """Pixels de couleur c qui touchent (à `epais` pixels fins) un voisin d'une autre couleur du côté indiqué
    ('h' haut, 'b' bas, 'g' gauche, 'd' droite) : liseré de lumière ou d'ombre ciblé."""
    pos = []
    dirs = {"h": (0, -1), "b": (0, 1), "g": (-1, 0), "d": (1, 0)}
    for Y in range(t.H):
        for X in range(t.W):
            if t.g[Y][X] != c:
                continue
            if cond is not None and not cond(X / t.e, Y / t.e):
                continue
            for k in cotes:
                a, b = dirs[k]
                if t.getf(X + a * epais, Y + b * epais) != c:
                    pos.append((X, Y))
                    break
    for X, Y in pos:
        t.g[Y][X] = vers


# ======================================================================================================
# Icônes de l'interface
# ======================================================================================================
@finition("cadenas", auto=False)
def _cadenas(t, k):
    """Cadenas redessiné : anse ronde éclairée à gauche, corps arrondi en trois tons, plaque et trou de serrure."""
    vider(t)
    t.anneau(5, 4.5, 3.5, 4, ARGENT, ep=1.5)
    rr(t, 0, 5, 10, 7, 1.3, sombre(ARGENT, 0.28))
    rr(t, 0, 5, 10, 5.7, 1.3, ARGENT)
    rr(t, 0.6, 5.5, 8.8, 1.3, 0.6, ARGENT_C)
    rr(t, 0.5, 6.4, 1.0, 4.2, 0.4, ARGENT_C)
    # Anse : lumière en haut à gauche, ombre à droite.
    arc(t, 5, 4.5, 2.85, 3.3, 185, 265, ARGENT_C, {ARGENT})
    arc(t, 5, 4.5, 2.85, 3.3, 300, 360, sombre(ARGENT, 0.28), {ARGENT})
    arc(t, 5, 4.5, 2.85, 3.3, 0, 40, sombre(ARGENT, 0.28), {ARGENT})
    # Serrure : rond et fente, petit reflet.
    disque(t, 5, 7.7, 1.15, 1.15, ENCRE)
    poly(t, [(4.4, 8.4), (5.6, 8.4), (5.9, 10.2), (4.1, 10.2)], ENCRE)
    t.pf(int(4.4 * t.e), int(7.1 * t.e), ARDOISE)
    t.contour(ENCRE)


@finition("badge-boutique", auto=False)
def _badge(t, k):
    """Sac de boutique : corps arrondi en bas, pli du haut éclairé, anse ronde, étoile à cinq branches qui scintille."""
    vider(t)
    t.anneau(7, 4.2, 3.4, 3.4, O1, ep=1.3)
    rr(t, 1, 4, 12, 11, 1.2, O3)
    rr(t, 1, 4, 12, 2.2, 0.6, O2)
    t.rect(1.6, 4.2, 10.8, 0.5, O4)
    for Y in range(int(6.2 * t.e), int(15 * t.e)):          # flanc droit plus sombre, bas adouci
        for X in range(int(10.6 * t.e), int(13 * t.e)):
            if t.g[Y][X] == O3:
                t.g[Y][X] = O2
    for X in range(int(1.4 * t.e), int(12.6 * t.e)):
        if t.g[int(14.4 * t.e)][X] == O3:
            t.g[int(14.4 * t.e)][X] = O2
    t.rect(1.7, 7.2, 0.6, 5.6, O4)
    arc(t, 7, 4.2, 2.7, 2.7, 190, 260, O2, {O1})
    c = J4 if k == 0 else BLANC
    pts = [(7, 6.6), (8.1, 8.8), (10.5, 9.1), (8.7, 10.7), (9.3, 13.1), (7, 11.8), (4.7, 13.1), (5.3, 10.7), (3.5, 9.1), (5.9, 8.8)]
    t.poly(pts, J3 if k == 0 else CREME_O)
    t.poly([(x * 0.94 + 0.45, y * 0.94 + 0.55) for x, y in pts], c)
    px(t, [(int(6.4 * t.e), int(8.9 * t.e))], BLANC)
    t.contour(ENCRE)


def piece(t, larg, ox=0, oy=0):
    """Pièce d'or vue de face (larg = 12) ou qui tourne : tranche, rebord, creux, relief de la fente, éclat."""
    cx, cy, rx, ry = ox + 6, oy + 6, larg / 2, 6
    t.ell(cx, cy, rx, ry, J3)
    if larg >= 4:
        croissant(t, cx, cy, rx, ry, {J3}, J2, (0.25, 0.3), 0.86)
    if larg >= 9:
        t.ell(cx, cy, rx - 1.15, ry - 1.15, J2)
        t.ell(cx, cy, rx - 1.95, ry - 1.95, J3)
        teinte_ell(t, cx, cy, rx - 1.95, ry - 1.95, {J3}, J4, lambda u, v: u * -0.8 + v * -0.8 > 0.78)
        croissant(t, cx, cy, rx - 1.95, ry - 1.95, {J3}, "#e3bd44", (0.25, 0.3), 0.8)
        # Fente en relief : I sombre, lumière à gauche, ombre en dessous.
        t.rect(cx - 0.7 if larg >= 12 else cx - 0.4, cy - 3, 1.4 if larg >= 12 else 0.8, 6, J1)
        t.rect(cx - 1.0 if larg >= 12 else cx - 0.7, cy - 3, 0.3, 6, J4)
        t.pf(int((cx - 3.6) * t.e), int((cy - 3.4) * t.e), "#ffffff")
        # Crans sur le rebord.
        for i in range(10):
            a = i * math.pi / 5 + 0.3
            X, Y = int((cx + math.cos(a) * (rx - 0.55)) * t.e), int((cy + math.sin(a) * (ry - 0.55)) * t.e)
            if t.getf(X, Y) == J3:
                t.pf(X, Y, J2)
    elif larg >= 4:
        t.ell(cx, cy, rx - 0.8, ry - 1.0, J2)
        t.rect(cx - 0.2, cy - 3, 0.4, 6, J1)


@finition("po", auto=False)
def _po(t, k):
    vider(t)
    piece(t, 12)
    t.contour(J1)


@finition("po-tourne", auto=False)
def _po_tourne(t, k):
    vider(t)
    piece(t, (12, 9, 4, 2, 4, 9)[k], 1, 1)
    t.contour(J1)


@finition("ballon", auto=False)
def _ballon(t, k):
    """Ballon : sphère crème ombrée en bas à droite, couture orange qui tourne, reflet."""
    vider(t)
    e = t.e
    t.ell(8, 8, 7.5, 7.5, CREME)
    croissant(t, 8, 8, 7.5, 7.5, {CREME}, CREME_O, (0.2, 0.2), 0.84)
    t.ell(5.6, 5.4, 1.7, 1.1, BLANC)
    a = k * math.pi / 4
    ca, sa = math.cos(a), math.sin(a)
    for Y in range(t.H):
        for X in range(t.W):
            if t.g[Y][X] is None:
                continue
            dx, dy = (X + 0.5) / e - 8, (Y + 0.5) / e - 8
            d = -dx * sa + dy * ca            # distance à la couture
            if abs(d) <= 0.85:
                lum = (dx + dy) / 15
                t.g[Y][X] = O4 if d < -0.3 and lum < 0.2 else (O2 if lum > 0.14 or d > 0.35 else O3)
    t.contour(B1)
    # Éclat discret en bas à droite.
    px(t, [(int(11.4 * e), int(11.6 * e)), (int(11.4 * e) + 1, int(11.6 * e))], BLANC)


@finition("marmite", auto=False)
def _marmite(t, k):
    """Marmite : corps cylindrique en trois tons, anses éclairées, bord qui luit, bouillon qui bulle."""
    e = t.e
    # Corps : dégradé horizontal (lumière à gauche, ombre à droite) sur le gris du flanc.
    for Y in range(int(10 * e), int(18 * e)):
        for X in range(int(2 * e), int(26 * e)):
            if t.g[Y][X] in (GRIS, GRIS_C):
                f = (X / e - 2) / 24
                t.g[Y][X] = (ARGENT_C if f < 0.1 else GRIS_C if f < 0.3 else GRIS if f < 0.78 else sombre(GRIS, 0.3))
    for Y in range(int(10 * e), int(20 * e)):
        X = int(4 * e)
        if t.g[Y][X] == ARGENT_C:
            t.g[Y][X] = BLANC if Y % 3 else ARGENT_C
    recolorer(t, ARDOISE, ARDOISE)
    # Rivets et reflet du bord.
    px(t, [(int(6 * e), int(12.5 * e)), (int(20 * e), int(12.5 * e)), (int(6 * e), int(16.5 * e)), (int(20 * e), int(16.5 * e))], sombre(GRIS, 0.5))
    arc(t, 14, 10, 12.0, 3.1, 200, 250, GRIS_C, {ARDOISE})
    arc(t, 14, 10, 12.0, 3.1, 290, 340, GRIS, {ARDOISE})
    # Anses : liseré clair sur le dessus.
    for (x0, x1) in ((0, 3), (25, 28)):
        for X in range(int(x0 * e), int(x1 * e)):
            Y = int(12 * e)
            if t.g[Y][X] == ARDOISE:
                t.g[Y][X] = GRIS
    # Bouillon : dégradé du bleu pâle vers le bleu, remous.
    for Y in range(t.H):
        for X in range(t.W):
            if t.g[Y][X] == B2:
                f = (X / e - 3.5) / 21
                if f < 0.25 and (Y % 2 == 0 or f < 0.12):
                    t.g[Y][X] = B3
    arc(t, 14, 10, 8, 1.5, 20, 160, B3, {B2})


# ======================================================================================================
# Marmite en cuivre, bonus de base
# ======================================================================================================
@finition("marmite-cuivre", auto=False)
def _marmite_cuivre(t, k):
    """Marmite de cuivre : panse ronde bien ombrée, bord clair, anses, grand reflet de métal poli."""
    vider(t)
    e = t.e
    t.ell(8, 6.5, 7, 5, O2, cond=lambda x, y, u, v: v > -0.6)
    croissant(t, 8, 6.5, 7, 5, {O2}, "#b4672c", (0.3, 0.35), 0.8)
    t.rect(1, 3, 14, 2, O3)
    t.rect(1, 3, 14, 0.5, O5)
    t.rect(1, 4.6, 14, 0.4, O2)
    rr(t, 0, 4, 2, 2, 0.6, O1)
    rr(t, 14, 4, 2, 2, 0.6, O1)
    t.rect(0.3, 4.2, 1.2, 0.4, O2)
    t.ell(4, 7.2, 1.2, 2.0, O4)
    t.ell(3.7, 6.5, 0.45, 1.2, O5)
    points(t, [(int(6.2 * e), int(9.6 * e)), (int(9.5 * e), int(10.2 * e)), (int(11.5 * e), int(9.4 * e))], O3, {O2})
    t.contour(ENCRE)


@finition("bonus-cafe", auto=False)
def _bonus_cafe(t, k):
    """Tasse : panse arrondie, café qui luit, anse ronde, lumière à gauche, volutes de vapeur."""
    vider(t)
    e = t.e
    t.rect(1, 4.5, 8, 5.5, CREME)
    t.ell(5, 10, 4, 1.15, CREME)
    t.ell(9.7, 7.5, 2.5, 2.7, CREME)
    t.ell(5, 4.7, 4, 1.15, BLANC)
    t.ell(5, 4.8, 3.2, 0.82, BR2)
    t.ell(4.2, 4.6, 1.2, 0.3, BR3)
    croissant(t, 5, 8, 4.0, 3.2, {CREME}, CREME_O, (0.25, 0.1), 0.85)
    t.rect(1.6, 5.8, 0.7, 3.4, BLANC)
    for Y in range(t.H):                      # anse : trou central
        for X in range(t.W):
            x_, y_ = (X + 0.5) / e, (Y + 0.5) / e
            if ((x_ - 9.7) / 1.25) ** 2 + ((y_ - 7.5) / 1.5) ** 2 <= 1 and x_ > 9.0:
                t.g[Y][X] = None
    t.contour(GRIS)
    for (a, b, c_, d) in ((3.3, 3.5, 3.0, 2.0), (3.0, 2.0, 3.5, 1.0), (6.2, 3.4, 5.8, 2.2), (5.8, 2.2, 6.3, 0.9)):
        trait_fin(t, a, b, c_, d, GRIS_C, 1)


@finition("bonus-tests", auto=False)
def _bonus_tests(t, k):
    """Case cochée : carré arrondi, cadre en deux tons, reflet en haut, coche épaisse en relief."""
    vider(t)
    rr(t, 0, 0, 12, 12, 1.4, B2)
    rr(t, 1, 1, 10, 10, 0.9, B4)
    rr(t, 1, 1, 10, 3.2, 0.9, eclaircir(B4, 0.5))
    t.rect(1, 9.7, 10, 1.3, B3)
    t.rect(0, 0.4, 12, 0.3, B3)
    ch = [(2.6, 6.2), (3.7, 5.2), (5.0, 6.7), (8.6, 2.6), (9.7, 3.6), (5.1, 9.0)]
    t.poly([(x + 0.3, y + 0.4) for x, y in ch], B2)
    t.poly(ch, B1)
    trait_fin(t, 3.5, 5.3, 5.0, 6.8, B2, 1)


@finition("bulle", auto=False)
def _bulle(t, k):
    """Bulle : film en deux tons, grand reflet courbe en haut à gauche, éclat en bas à droite."""
    vider(t)
    e = t.e
    t.ell(8, 8, 7.5, 7.5, B4)
    t.ell(8, 8, 6.3, 6.3, "#d8ecff")
    teinte_ell(t, 8, 8, 6.3, 6.3, {"#d8ecff"}, "#e8f4ff", lambda u, v: u + v < -0.5)
    croissant(t, 8, 8, 6.3, 6.3, {"#d8ecff"}, B4, (0.28, 0.28), 0.8)
    arc(t, 8, 8, 5.7, 5.7, 200, 255, BLANC, {"#d8ecff", "#e8f4ff"})
    arc(t, 8, 8, 5.1, 5.1, 205, 245, BLANC, {"#d8ecff", "#e8f4ff"})
    t.ell(5, 5.2, 1.6, 1.0, BLANC)
    arc(t, 8, 8, 6.6, 6.6, 20, 70, "#ffffff", {B4})
    t.contour(B2)
