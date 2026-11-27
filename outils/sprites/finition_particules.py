"""Finition fine (2×) des particules : confettis, bulles de savon, mousse, traînée prisme, vapeur, feu, éclaboussure, orbite de
lunes, cercle de glyphes. Chaque image est redessinée en pixels fins avec les mêmes positions que le 1× (mêmes images,
mêmes durées) : les formes deviennent rondes, fuselées ou ombrées au lieu de petits blocs.
"""
import math

import fins
from finition import finition, ENCRE, BLANC, CREME, CREME_O, GRIS_C, B1, B2, B3, B4, O1, O2, O3, O4, O5, J2, J3, J4, \
    V1, V2, V3, V4
from finition_lot3 import vider, px, trait_fin
from finition_objets import croissant, teinte_ell

clair, sombre = fins.clair, fins.sombre


def pastille(t, cx, cy, rx, ry, c, angle=0.0, ombre=True, eclat=True):
    """Petite pastille ovale tournée, ombrée en bas à droite, éclat d'un pixel fin en haut à gauche."""
    e = t.e
    ca, sa = math.cos(angle), math.sin(angle)
    R = max(rx, ry)
    cl, so = clair(c, 0.45), sombre(c, 0.22)
    cases = []
    for Y in range(int((cy - R) * e) - 1, int((cy + R) * e) + 2):
        for X in range(int((cx - R) * e) - 1, int((cx + R) * e) + 2):
            dx, dy = (X + 0.5) / e - cx, (Y + 0.5) / e - cy
            u, v = (dx * ca + dy * sa) / rx, (-dx * sa + dy * ca) / ry
            if u * u + v * v <= 1:
                cases.append((X, Y, dx, dy))
    for X, Y, dx, dy in cases:
        t.pf(X, Y, so if (ombre and dx + dy > R * 0.25) else c)
    if eclat and cases:
        X, Y, _, _ = min(cases, key=lambda p: p[2] + p[3])
        t.pf(X, Y, cl)


# ---- confettis -----------------------------------------------------------------------------------------
@finition("confettis", auto=False)
def _confettis(t, k):
    vider(t)
    cols = [B3, O3, J3, V3, B4, O4]
    for i in range(26):
        x = (i * 37 + 5) % 45
        y = (i * 13 + k * 8) % 48
        if 7 < x < 38 and 8 < y < 46:
            continue
        ang = ((i * 53 + k * 37) % 180) * math.pi / 180
        pastille(t, x + 1, y + 0.8, 1.35, 0.7, cols[i % len(cols)], ang)


# ---- bulles de savon -------------------------------------------------------------------------------------
@finition("bulles-savon", auto=False)
def _bulles_savon(t, k):
    vider(t)
    e = t.e
    for i, (x, base, r) in enumerate(((3, 40, 3), (48, 34, 2.5), (8, 26, 2), (44, 20, 3), (2, 14, 2.5))):
        ph = (k / 6 + i * 0.23) % 1
        y = base - ph * 14
        cx = x + 2 + math.sin(ph * 6 + i) * 1.5
        fins.bulle_fin(t, cx, y, r + 0.4, B4)
        # Irisation : un reflet violet pâle et un reflet orangé le long du bord bas droit.
        R = (r + 0.4) * e
        for j in range(7):
            a = math.radians(20 + j * 8)
            t.pf(int(cx * e + math.cos(a) * (R - 0.6)), int(y * e + math.sin(a) * (R - 0.6)), V4)
        for j in range(4):
            a = math.radians(95 + j * 8)
            t.pf(int(cx * e + math.cos(a) * (R - 0.6)), int(y * e + math.sin(a) * (R - 0.6)), O5)


# ---- mousse ----------------------------------------------------------------------------------------------
@finition("mousse", auto=False)
def _mousse(t, k):
    vider(t)
    e = t.e
    bulles = [(4, 20, 3.2), (43, 17, 3.0), (9, 6, 2.6), (39, 5, 2.8), (24, 1.5, 2.2), (2, 31, 2.4), (46, 30, 2.4)]
    foam = ((14, 12), (18, 9), (23, 8), (28, 9), (33, 11), (36, 15), (11, 16), (10, 22), (38, 21))
    for i, (x, y) in enumerate(foam):
        r = 2.6 + 0.6 * ((i + k) % 2)
        t.ell(x, y, r, r, BLANC)
    for i, (x, y) in enumerate(foam):
        r = 2.6 + 0.6 * ((i + k) % 2)
        croissant(t, x, y, r, r, {BLANC}, B4, (0.3, 0.3), 0.78)
        t.pf(int((x - r * 0.45) * e), int((y - r * 0.5) * e), "#e8f4ff")
    for i, (x, y, r) in enumerate(bulles):
        ph = (k + i) % 4
        yy = y - ph * 1.5
        if ph == 3:
            for a, b in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                trait_fin(t, x + a * 1.6, yy + b * 1.6, x + a * 2.5, yy + b * 2.5, B4, 1)
            continue
        rr_ = r * (0.7 + 0.15 * ph)
        fins.bulle_fin(t, x, yy, rr_, B3)
    t.contour(CREME_O)


# ---- traînée prisme --------------------------------------------------------------------------------------
@finition("trainee-prisme", auto=False)
def _prisme(t, k):
    vider(t)
    e = t.e
    bandes = [B4, B3, V3, V2, O3, J3]
    for i, c in enumerate(bandes):
        r = 23.5 - i * 1.6
        for Y in range(t.H):
            for X in range(t.W):
                d = math.hypot((X + 0.5) / e - 24, ((Y + 0.5) / e - 27) * 1.15)
                if r - 1.6 < d <= r and (X * 7 + Y * 13 + k * 5) % 29 != 0:
                    t.pf(X, Y, clair(c, 0.35) if d > r - 0.45 else c)
    for i in range(3):
        fins.etincelle(t, 4 + ((i * 17 + k * 7) % 40) + 0.5, 2 + (i * 5 + k * 3) % 8 + 0.5, J4, bras=3, coeur=BLANC)


# ---- vapeur, feu, éclaboussure ---------------------------------------------------------------------------
@finition("vapeur", auto=False)
def _vapeur(t, k):
    vider(t)
    for i in range(3):
        ph = (k / 4 + i / 3) % 1
        y = int(12 - ph * 12)
        x = 4 + i * 6 + int(math.sin(ph * 6 + i) * 2)
        a = "%02x" % int(255 * (1 - ph * 0.45))
        r = 2 - ph
        t.ell(x - 0.5, y + 0.2, r * 0.8, r * 0.7, CREME + a)
        t.ell(x + 0.6, y - 0.3, r * 0.9, r * 0.75, CREME + a)
        t.ell(x, y + 0.6, r * 1.0, r * 0.6, CREME + a)
        t.ell(x - 0.4, y - 0.1, r * 0.35, r * 0.25, BLANC + a)


@finition("feu", auto=False)
def _feu(t, k):
    """Flammes : langues courbes à trois couches (orange, orangé clair, cœur jaune pâle), penchées au gré de l'image."""
    vider(t)
    e = t.e
    for i in range(6):
        x = 2 + i * 4 + 1.8
        h = 4 + ((i * 3 + k * 2) % 5)
        lean = (((i + k) % 3) - 1) * 0.9
        for (ech, c) in ((1.0, O3), (0.66, "#ffc89a"), (0.36, "#fff6cc")):
            hh = h * ech + (0.0 if ech == 1.0 else 0.4)
            for Y in range(int((10 - hh) * e), 10 * e):
                s = max(0.0, (Y / e - (10 - hh)) / hh)
                demi = 1.95 * ech * (s ** 0.55)
                cx = x + lean * 1.5 * (1 - s) ** 1.2
                for X in range(int((cx - demi) * e), int((cx + demi) * e) + 1):
                    if cx - demi <= (X + 0.5) / e <= cx + demi:
                        t.pf(X, Y, c)


@finition("eclaboussure", auto=False)
def _eclaboussure(t, k):
    vider(t)
    e = t.e
    t.ell(11, 13, 4 + k * 2, 1.2, B3)
    t.ell(11, 13.5, 3.5 + k * 2, 0.6, B2)
    for i in range(7):
        a = math.pi * (0.1 + i * 0.8 / 6)
        r = 3 + k * 3.5
        x, y = 11 + math.cos(a) * r, 13 - math.sin(a) * r * 0.9
        c = B4 if i % 2 else BLANC
        ry = 2.2 - k * 0.4
        t.ell(x, y, 1.5, ry, c)
        t.poly([(x - 1.0, y - ry * 0.4), (x, y - ry - 1.1), (x + 1.0, y - ry * 0.4)], c)
        px(t, [(int((x - 0.5) * e), int((y - 0.3) * e))], BLANC if c == B4 else B4)
        px(t, [(int((x + 0.5) * e), int((y + ry * 0.5) * e))], B3)


# ---- orbite de lunes -------------------------------------------------------------------------------------
@finition("orbite-lunes", auto=False)
def _orbite(t, k):
    vider(t)
    e = t.e
    for i, c in enumerate(("#b4dbff", "#fff6cc", "#d2caff")):
        a = (k / 12 + i / 3) * 2 * math.pi
        for j in range(1, 9):
            b = a - j * 0.085
            al = "%02x" % max(0x22, 0x99 - j * 0x14)
            X, Y = int((28 + math.cos(b) * 25) * e), int((12 + math.sin(b) * 9) * e)
            t.pf(X, Y, c + al)
            if j < 4:
                t.pf(X + 1, Y, c + al)
        x, y = 28 + math.cos(a) * 25, 12 + math.sin(a) * 9
        t.ell(x, y, 3, 3, c)
        croissant(t, x, y, 3, 3, {c}, sombre(c, 0.28), (0.25, 0.25), 0.78)
        t.ell(x - 0.9, y - 0.9, 1.1, 0.8, BLANC)
        t.pf(int((x + 0.9) * e), int((y + 0.6) * e), sombre(c, 0.45))
        t.pf(int((x + 0.3) * e), int((y + 1.4) * e), sombre(c, 0.45))


# ---- cercle de glyphes -----------------------------------------------------------------------------------
@finition("cercle-glyphes", auto=False)
def _glyphes(t, k):
    vider(t)
    e = t.e
    t.anneau(26, 7, 25.4, 6.9, V2 + "55", ep=0.6)
    t.anneau(26, 7, 25, 6.5, V2, ep=0.55)
    t.anneau(26, 7, 21, 5, V1, ep=0.55)
    for i in range(12):
        a = (i / 12 + k / 96) * 2 * math.pi
        x, y = 26 + math.cos(a) * 23, 7 + math.sin(a) * 5.8
        c = B4 if (i + k) % 4 == 0 else V3
        x, y = int(x) + 0.5, int(y) + 0.5
        m = i % 3
        if m == 0:      # croix en X
            trait_fin(t, x - 1.1, y - 1.1, x + 1.1, y + 1.1, c, 1)
            trait_fin(t, x + 1.1, y - 1.1, x - 1.1, y + 1.1, c, 1)
        elif m == 1:    # deux barres
            trait_fin(t, x - 1.3, y - 0.9, x + 1.3, y - 0.9, c, 1)
            trait_fin(t, x - 1.3, y + 0.9, x + 1.3, y + 0.9, c, 1)
        else:           # losange
            trait_fin(t, x, y - 1.3, x + 1.3, y, c, 1)
            trait_fin(t, x + 1.3, y, x, y + 1.3, c, 1)
            trait_fin(t, x, y + 1.3, x - 1.3, y, c, 1)
            trait_fin(t, x - 1.3, y, x, y - 1.3, c, 1)
        if c == B4:
            t.pf(int(x * e), int(y * e), BLANC)
