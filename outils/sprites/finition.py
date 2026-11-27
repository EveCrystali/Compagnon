"""Finition du dessin fin (2×) pour la troisième série (fin.SERIE3) : objets de pêche et de cuisine, décors de boutique,
bonus, gestes, soins, interface.

Même principe que retouches_fines.py : chaque sprite est d'abord rejoué sur la toile fine (formes calculées à la
finesse double) ou, s'il est fait de pixels posés à la main, agrandi par la règle commune (rendu.agrandir_image).
Puis la finition ajoute ce que la grille 1× ne porte pas :

  1. `riche(t)` : une lumière d'en haut à gauche sur les couleurs principales (liseré clair d'un pixel fin en haut et à
     gauche des zones épaisses, ombre d'un pixel fin en bas et à droite, bas des grandes zones adouci en trame puis en
     aplat plus sombre) ; les zones étroites, les cernes et les blancs restent intacts ;
  2. une fonction décorée par `@finition("id", …)` qui peint, avec les outils de la toile (coordonnées de la grille
     1×, demi-unités permises) ou `t.pf` (pixels fins), les détails propres au sprite : reflets, écailles, vapeur,
     étincelles, brins. Elle reçoit (t, k) pour l'image k ; `@finition(..., auto=False)` désactive l'étape 1.

Les couleurs ajoutées sont dérivées de celles du sprite (plus claires ou plus sombres, ombres tirées vers le bleu
nuit) : la palette reste dans la même famille, sans opposition rouge / vert. 62 couleurs au plus par sprite.
"""
import os

import toile
from retouches_fines import eclaircir, assombrir, _rvb, _clarte

FINITIONS = {}

# Palette commune des dessins (mêmes valeurs que generer.py).
ENCRE, NOIR2, BLANC, CREME, CREME_O = "#1c2128", "#2d333b", "#ffffff", "#f6f8fa", "#c9d1d9"
GRIS, GRIS_C, ARDOISE, ARGENT, ARGENT_C = "#768390", "#adbac7", "#3b4654", "#b8c4d2", "#e6ecf2"
B1, B2, B3, B4 = "#1f4f8a", "#4a8fdc", "#6cb6ff", "#b4dbff"
NUIT, NUIT2 = "#0d2a4d", "#16365e"
O1, O2, O3, O4, O5 = "#8a4a1f", "#d9803a", "#f69d50", "#ffc89a", "#ffd8b0"
J1, J2, J3, J4 = "#7a5a10", "#c9a227", "#f5d76e", "#fff6cc"
V1, V2, V3, V4 = "#3a2a7a", "#6a5acd", "#9b8cff", "#d2caff"
S1, S2, S3 = "#8a6e4b", "#c4a77d", "#e8d5b0"
BR1, BR2, BR3 = "#4a2e17", "#7a4b26", "#a86f3c"
T1, T2, T3 = "#0f4a63", "#2689b8", "#3fb8e0"


def finition(*ids, auto=True):
    def poser(f):
        for i in ids:
            FINITIONS[i] = (f, auto)
        return f
    return poser


def composantes(t):
    """Zones connexes (4 voisins) de même couleur : liste de (couleur, ensemble de (X, Y))."""
    vu = [[False] * t.W for _ in range(t.H)]
    out = []
    for Y in range(t.H):
        for X in range(t.W):
            c = t.g[Y][X]
            if c is None or vu[Y][X]:
                continue
            pile, zone = [(X, Y)], set()
            vu[Y][X] = True
            while pile:
                x, y = pile.pop()
                zone.add((x, y))
                for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    u, v = x + a, y + b
                    if 0 <= u < t.W and 0 <= v < t.H and not vu[v][u] and t.g[v][u] == c:
                        vu[v][u] = True
                        pile.append((u, v))
            out.append((c, zone))
    return out


def _eligible(c):
    return c is not None and len(c) == 7 and c[0] == "#" and 170 <= _clarte(c) <= 700


def riche(t, haut=True, bas=True, trame=True, epais=3, zone_min=40):
    """Lumière d'en haut à gauche sur les zones assez grandes de la toile fine (voir l'en-tête)."""
    poses = {}
    for c, zone in composantes(t):
        if len(zone) < zone_min or not _eligible(c):
            continue
        xs = [p[0] for p in zone]
        ys = [p[1] for p in zone]
        larg, haut_z = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
        if min(larg, haut_z) < 5:
            continue
        clair, sombre = eclaircir(c, 0.34), assombrir(c, 0.2)
        y0, y1 = min(ys), max(ys)
        for (X, Y) in zone:
            # profondeur au-dessus / à gauche / en dessous / à droite, dans la même zone
            def prof(a, b):
                n = 0
                while n < epais + 1 and (X + a * (n + 1), Y + b * (n + 1)) in zone:
                    n += 1
                return n
            if haut and (X, Y - 1) not in zone and prof(0, 1) >= epais:
                poses[(X, Y)] = clair
            elif haut and larg >= 9 and (X - 1, Y) not in zone and prof(1, 0) >= epais and prof(0, 1) >= 2:
                poses[(X, Y)] = clair
            elif bas and (X, Y + 1) not in zone and prof(0, -1) >= epais:
                poses[(X, Y)] = sombre
            elif bas and larg >= 9 and (X + 1, Y) not in zone and prof(-1, 0) >= epais and prof(0, -1) >= 2:
                poses[(X, Y)] = sombre
            elif trame and haut_z >= 20 and larg >= 9:
                f = (Y - y0) / max(1, y1 - y0)
                if f > 0.82 or (f > 0.7 and (X + Y) % 2 == 0):
                    poses[(X, Y)] = sombre
    for (X, Y), c in poses.items():
        t.g[Y][X] = c


def brillance(t, x, y, c="#ffffff", rx=1.0, ry=0.5):
    """Petit reflet ovale (coordonnées de la grille 1×), posé seulement sur ce qui est dessiné."""
    e = t.e
    for Y in range(t.H):
        for X in range(t.W):
            if t.g[Y][X] is None:
                continue
            u, v = ((X + 0.5) / e - x) / rx, ((Y + 0.5) / e - y) / ry
            if u * u + v * v <= 1:
                t.g[Y][X] = c


def scintille(t, x, y, c="#ffffff", r=2):
    """Étoile à quatre branches en pixels fins, centrée sur le pixel fin (x, y) de la grille réelle."""
    t.pf(x, y, c)
    for n in range(1, r + 1):
        for a, b in ((n, 0), (-n, 0), (0, n), (0, -n)):
            t.pf(x + a, y + b, c)


def degrade_v(t, y0, y1, x0, x1, couleurs, trame=True):
    """Dégradé vertical tramé, en pixels fins (de y0 à y1, de x0 à x1, coordonnées de la grille 1×) :
    `couleurs` du haut vers le bas, deux rangées de trame entre deux couleurs."""
    e = t.e
    Y0, Y1, X0, X1 = int(y0 * e), int(y1 * e), int(x0 * e), int(x1 * e)
    n = len(couleurs)
    for Y in range(Y0, Y1):
        f = (Y - Y0) / max(1, Y1 - Y0) * n
        i = min(n - 1, int(f))
        frac = f - i
        for X in range(X0, X1):
            c = couleurs[i]
            if trame and i + 1 < n and frac > 0.78 and (X + Y) % 2 == 0:
                c = couleurs[i + 1]
            elif trame and i > 0 and frac < 0.22 and (X + Y) % 2 == 1:
                c = couleurs[i - 1]
            t.g[Y][X] = c


# ---- Pinceaux fins : coordonnées de la grille 1× (réelles, demi-unités permises), pixels fins calculés dessous.
# `sur` : ensemble de couleurs que le pinceau a le droit de recouvrir (None : tout ce qui est dessiné) ; les cernes et
# le vide restent donc intacts.
def _ok(t, X, Y, sur):
    if not (0 <= X < t.W and 0 <= Y < t.H):
        return False
    v = t.g[Y][X]
    return v is not None and (sur is None or v in sur)


def disque(t, cx, cy, rx, ry, c, sur=None, cond=None):
    """Ellipse pleine (coordonnées 1×) peinte seulement sur `sur`."""
    e = t.e
    for Y in range(max(0, int((cy - ry) * e) - 1), min(t.H, int((cy + ry) * e) + 2)):
        for X in range(max(0, int((cx - rx) * e) - 1), min(t.W, int((cx + rx) * e) + 2)):
            u, v = ((X + 0.5) / e - cx) / rx, ((Y + 0.5) / e - cy) / ry
            if u * u + v * v <= 1 and _ok(t, X, Y, sur) and (cond is None or cond(u, v)):
                t.g[Y][X] = c


def trait(t, x0, y0, x1, y1, c, sur=None):
    """Ligne d'un pixel fin d'épaisseur (coordonnées 1×), seulement sur `sur`."""
    e = t.e
    X0, Y0, X1, Y1 = int(round(x0 * e)), int(round(y0 * e)), int(round(x1 * e)), int(round(y1 * e))
    dx, dy = abs(X1 - X0), -abs(Y1 - Y0)
    sx, sy = (1 if X0 < X1 else -1), (1 if Y0 < Y1 else -1)
    err = dx + dy
    while True:
        if _ok(t, X0, Y0, sur):
            t.g[Y0][X0] = c
        if X0 == X1 and Y0 == Y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            X0 += sx
        if e2 <= dx:
            err += dx
            Y0 += sy


def arc(t, cx, cy, rx, ry, a0, a1, c, sur=None):
    """Arc d'ellipse d'un pixel fin d'épaisseur, de l'angle a0 à a1 (degrés, 0 = droite, 90 = bas)."""
    import math
    n = max(8, int(max(rx, ry) * t.e * abs(a1 - a0) / 40))
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        X, Y = int((cx + math.cos(a) * rx) * t.e), int((cy + math.sin(a) * ry) * t.e)
        if _ok(t, X, Y, sur):
            t.g[Y][X] = c


def points(t, pts, c, sur=None):
    """Pixels fins isolés : pts = [(X, Y)] sur la grille réelle."""
    for X, Y in pts:
        if _ok(t, X, Y, sur):
            t.g[Y][X] = c


def poly(t, pts, c, sur=None):
    """Polygone plein (coordonnées 1×), seulement sur `sur`."""
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
            for X in range(max(0, int(a * e) - 1), min(t.W, int(b * e) + 2)):
                if a <= (X + 0.5) / e < b and _ok(t, X, Y, sur):
                    t.g[Y][X] = c


def oeil(t, x, y, r=1.0, fond="#ffffff", pupille="#1c2128", sur=None):
    """Œil rond : anneau clair, pupille, reflet d'un pixel fin en haut à gauche. (x, y) : centre, grille 1×."""
    disque(t, x, y, r * 1.5, r * 1.5, fond, sur)
    disque(t, x + 0.1, y + 0.1, r, r, pupille, None)
    t.pf(int((x - r * 0.45) * t.e), int((y - r * 0.5) * t.e), "#ffffff")


def dominante(t, X0, Y0, X1, Y1):
    """Couleur la plus présente dans un rectangle de la grille réelle."""
    n = {}
    for Y in range(max(0, Y0), min(t.H, Y1)):
        for X in range(max(0, X0), min(t.W, X1)):
            c = t.g[Y][X]
            if c is not None:
                n[c] = n.get(c, 0) + 1
    return max(n, key=n.get) if n else None


def lisere_lateral(t, couleurs):
    """Rubans étroits : bord gauche éclairci, bord droit assombri, pour les couleurs données."""
    poses = []
    for Y in range(t.H):
        for X in range(t.W):
            c = t.g[Y][X]
            if c in couleurs:
                if t.getf(X - 1, Y) != c and t.getf(X - 1, Y) is not None and t.getf(X + 1, Y) == c:
                    poses.append((X, Y, eclaircir(c, 0.3)))
                elif t.getf(X + 1, Y) != c and t.getf(X + 1, Y) is not None and t.getf(X - 1, Y) == c:
                    poses.append((X, Y, assombrir(c, 0.22)))
    for X, Y, c in poses:
        t.g[Y][X] = c


DETAILS = {}


def detail(*ids):
    """Détail dessiné pendant le dessin d'origine, dans le repère du sprite avant rognage (sprites rognés après coup)."""
    def poser(f):
        for i in ids:
            DETAILS[i] = f
        return f
    return poser


def poser_detail(id_, t):
    """Appelé par generer.py en dessin fin, juste après le cerne et avant le rognage."""
    import finition_prises  # noqa: F401  (inscrit les détails de la pêche)
    f = DETAILS.get(id_)
    if f:
        f(t)


def _base(id_, images):
    from retouches_fines import _base_fine
    return _base_fine(id_, images)


def _serie3(id_):
    def toutes(images):
        images = _base(id_, images)
        f, auto = FINITIONS.get(id_, (None, True))
        for k, t in enumerate(images):
            if auto:
                riche(t)
            if f:
                f(t, k)
        return images
    return toutes


def inscrire():
    import fin
    import finition_cuisine  # noqa: F401  (inscrit les finitions de chaque famille)
    for i in fin.SERIE3:
        fin.RETOUCHES[i] = _serie3(i)
