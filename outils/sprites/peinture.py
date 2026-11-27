"""Pinceaux des illustrations (décors des campagnes, vignettes, souvenirs) : outil de fabrication, pas embarqué.

Tout se peint sur une `toile.Toile`, en coordonnées de la grille 1× (continues), mais chaque pinceau travaille
pixel par pixel sur la grille réelle : rejoué à l'échelle 2 (dessin fin), un dégradé tramé, un liseré de crête,
un voile de brume ou une lueur sont calculés à la finesse double (trame plus fine, liseré d'un pixel fin), au lieu
d'être agrandis. Les mélanges (brume, lueur, ombre) retombent toujours sur une couleur de la palette restreinte
de l'illustration (`Palette`) : pas de couleur inventée, et jamais plus de couleurs que de lettres.
"""
import math

BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def seuil(X, Y):
    """Seuil de trame ordonnée (Bayer 4 × 4) d'un pixel réel, entre 0 et 1."""
    return (BAYER[Y % 4][X % 4] + 0.5) / 16


def hasard(X, Y, graine=0):
    """Bruit déterministe d'un pixel (entre 0 et 1), le même sur toutes les machines."""
    n = (X * 374761393 + Y * 668265263 + graine * 2246822519) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65536.0


def rvb(c):
    return int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)


def hexa(r, v, b):
    return "#%02x%02x%02x" % (int(round(r)), int(round(v)), int(round(b)))


def mix(a, b, k):
    ra, va, ba = rvb(a)
    rb, vb, bb = rvb(b)
    return hexa(ra + (rb - ra) * k, va + (vb - va) * k, ba + (bb - ba) * k)


class Palette:
    """Palette restreinte d'une illustration : `proche(c)` ramène toute couleur à la plus proche de la palette."""

    def __init__(self, *couleurs):
        self.c = []
        for c in couleurs:
            if isinstance(c, (list, tuple)):
                self.c.extend(c)
            else:
                self.c.append(c)
        self._cache = {}

    def proche(self, c):
        if c in self._cache:
            return self._cache[c]
        r, v, b = rvb(c)
        best = min(self.c, key=lambda p: (2 * (rvb(p)[0] - r) ** 2 + 4 * (rvb(p)[1] - v) ** 2 + 3 * (rvb(p)[2] - b) ** 2))
        self._cache[c] = best
        return best

    def melange(self, a, b, k):
        return self.proche(mix(a, b, k))

    def rampes(self, *rampes):
        """Rampes de lumière (du plus sombre au plus clair) : eclairer / assombrir y avancent d'un pas."""
        self._rampe = {}
        for r in rampes:
            for i, c in enumerate(r):
                self._rampe.setdefault(c, (r, i))
        return self

    def pas(self, c, n):
        r = getattr(self, "_rampe", {}).get(c)
        if r is None:
            return c
        rampe, i = r
        return rampe[min(max(i + n, 0), len(rampe) - 1)]


# ---------------------------------------------------------------------------------------------------------
# Parcours de la grille réelle
# ---------------------------------------------------------------------------------------------------------
def pixels(t, x0=0, y0=0, x1=None, y1=None):
    """(X, Y, x, y) pour chaque pixel réel dont le centre (x, y), en coordonnées 1×, tombe dans le cadre."""
    e = t.e
    x1 = t.w if x1 is None else x1
    y1 = t.h if y1 is None else y1
    X0, X1 = max(0, int(math.floor(x0 * e))), min(t.W, int(math.ceil(x1 * e)))
    Y0, Y1 = max(0, int(math.floor(y0 * e))), min(t.H, int(math.ceil(y1 * e)))
    for Y in range(Y0, Y1):
        y = (Y + 0.5) / e
        for X in range(X0, X1):
            yield X, Y, (X + 0.5) / e, y


def remplir(t, cond, c, cadre=(0, 0, None, None)):
    for X, Y, x, y in pixels(t, *cadre):
        if cond(x, y):
            t.g[Y][X] = c(X, Y, x, y) if callable(c) else c


def rect(t, x, y, w, h, c):
    for X, Y, _, _ in pixels(t, x, y, x + w, y + h):
        t.g[Y][X] = c


def ell(t, cx, cy, rx, ry, c, cond=None):
    for X, Y, x, y in pixels(t, cx - rx - 1, cy - ry - 1, cx + rx + 1, cy + ry + 1):
        u, v = (x - cx) / rx, (y - cy) / ry
        if u * u + v * v <= 1 and (cond is None or cond(x, y, u, v)):
            t.g[Y][X] = c


def poly(t, pts, c):
    """Polygone plein (pair-impair), limité à son cadre."""
    e = t.e
    ys = [p[1] for p in pts]
    Y0, Y1 = max(0, int(min(ys) * e) - 1), min(t.H, int(max(ys) * e) + 2)
    for Y in range(Y0, Y1):
        yc = (Y + 0.5) / e
        xs = []
        for i in range(len(pts)):
            (xa, ya), (xb, yb) = pts[i], pts[(i + 1) % len(pts)]
            if (ya <= yc < yb) or (yb <= yc < ya):
                xs.append(xa + (yc - ya) * (xb - xa) / (yb - ya))
        xs.sort()
        for a, b in zip(xs[0::2], xs[1::2]):
            for X in range(max(0, int(a * e) - 1), min(t.W, int(b * e) + 2)):
                if a <= (X + 0.5) / e < b:
                    t.g[Y][X] = c


def point(t, x, y, c):
    """Un seul pixel réel (fin en 2×) au point (x, y) de la grille 1×."""
    t.pf(int(x * t.e), int(y * t.e), c)


def trait(t, x0, y0, x1, y1, c, ep=1):
    """Trait d'`ep` pixels réels d'épaisseur (1 : un pixel fin en 2×, un pixel en 1×)."""
    e = t.e
    X0, Y0, X1, Y1 = int(round(x0 * e)), int(round(y0 * e)), int(round(x1 * e)), int(round(y1 * e))
    n = max(abs(X1 - X0), abs(Y1 - Y0), 1)
    for i in range(n + 1):
        X = int(round(X0 + (X1 - X0) * i / n))
        Y = int(round(Y0 + (Y1 - Y0) * i / n))
        for a in range(ep):
            for b in range(ep):
                t.pf(X + a, Y + b, c)


def trait1(t, x0, y0, x1, y1, c):
    """Trait d'un pixel de la grille 1× (deux pixels fins en 2×)."""
    trait(t, x0, y0, x1, y1, c, ep=t.e)


def hline(t, x0, x1, y, c):
    """Ligne horizontale d'un pixel réel à la hauteur y (1×)."""
    Y = int(y * t.e)
    for X in range(max(0, int(x0 * t.e)), min(t.W, int(math.ceil(x1 * t.e)))):
        t.pf(X, Y, c)


def vline(t, x, y0, y1, c):
    X = int(x * t.e)
    for Y in range(max(0, int(y0 * t.e)), min(t.H, int(math.ceil(y1 * t.e)))):
        t.pf(X, Y, c)


def courbe(t, pts, c, ep=None, n=None):
    """Courbe de Bézier (3 ou 4 points), d'`ep` pixels réels (défaut : un pixel 1×)."""
    ep = t.e if ep is None else ep
    n = n or int(40 * t.e)
    prev = None
    for i in range(n + 1):
        u = i / n
        if len(pts) == 3:
            (ax, ay), (bx, by), (cx, cy) = pts
            x = (1 - u) ** 2 * ax + 2 * (1 - u) * u * bx + u * u * cx
            y = (1 - u) ** 2 * ay + 2 * (1 - u) * u * by + u * u * cy
        else:
            (ax, ay), (bx, by), (cx, cy), (dx, dy) = pts
            x = (1 - u) ** 3 * ax + 3 * (1 - u) ** 2 * u * bx + 3 * (1 - u) * u * u * cx + u ** 3 * dx
            y = (1 - u) ** 3 * ay + 3 * (1 - u) ** 2 * u * by + 3 * (1 - u) * u * u * cy + u ** 3 * dy
        if prev:
            trait(t, prev[0], prev[1], x, y, c, ep)
        prev = (x, y)


# ---------------------------------------------------------------------------------------------------------
# Lumière et matière
# ---------------------------------------------------------------------------------------------------------
def degrade(t, y0, y1, couleurs, x0=0, x1=None, trame=0.45):
    """Dégradé vertical en bandes, la fin de chaque bande tramée (trame ordonnée) vers la suivante."""
    n = len(couleurs) - 1
    for X, Y, x, y in pixels(t, x0, y0, x1, y1):
        f = min(max((y - y0) / max(y1 - y0, 1e-6), 0), 0.9999) * n
        i = int(f)
        fr = f - i
        c = couleurs[i]
        if i < n and fr > 1 - trame and (fr - (1 - trame)) / trame > seuil(X, Y):
            c = couleurs[i + 1]
        t.g[Y][X] = c


def relief(t, f, c, lisere=None, x0=0, x1=None, bas=None, cond=None):
    """Remplit sous la courbe y = f(x) ; `lisere` : couleur du premier pixel réel (crête éclairée)."""
    e = t.e
    x1 = t.w if x1 is None else x1
    bas = t.h if bas is None else bas
    for X in range(max(0, int(x0 * e)), min(t.W, int(math.ceil(x1 * e)))):
        x = (X + 0.5) / e
        yb = f(x)
        Y0 = max(0, int(math.ceil(yb * e - 0.5)))
        for Y in range(Y0, min(t.H, int(math.ceil(bas * e)))):
            y = (Y + 0.5) / e
            if cond and not cond(x, y):
                continue
            t.g[Y][X] = lisere if (lisere and Y == Y0) else (c(X, Y, x, y) if callable(c) else c)


def palier(k, n, X, Y, trame=0.35):
    """Niveau entier (0..n) d'une force k ∈ [0, 1] : des bandes nettes, tramées seulement à leur bord."""
    f = min(max(k, 0), 1) * n
    i = int(math.floor(f))
    fr = f - i
    if i < n and fr > 1 - trame and (fr - (1 - trame)) / trame > seuil(X, Y):
        i += 1
    return i


def eclat(t, force, pal, n=2, sens=1, cadre=(0, 0, None, None), sur=None, trame=0.35):
    """Lumière (sens 1) ou ombre (sens -1) le long des rampes de la palette, en paliers nets."""
    for X, Y, x, y in pixels(t, *cadre):
        c = t.g[Y][X]
        if c is None or (sur is not None and c not in sur):
            continue
        q = palier(force(x, y), n, X, Y, trame)
        if q:
            t.g[Y][X] = pal.pas(c, sens * q)


def voile(t, force, couleur, pal=None, cadre=(0, 0, None, None), niveaux=2, sur=None, famille=None):
    """Brume ou fumée : chaque pixel va vers `couleur` selon force(x, y) ∈ [0, 1], en paliers nets (tramés à leur
    bord). Un palier partiel prend, dans la `famille` de la brume (par défaut la rampe de `couleur`), la teinte la
    plus proche du mélange : la brume reste de la même famille, sans couleur nouvelle."""
    if famille is None:
        r = getattr(pal, "_rampe", {}).get(couleur) if pal else None
        famille = r[0] if r else [couleur]
    sub = Palette(famille)
    for X, Y, x, y in pixels(t, *cadre):
        c = t.g[Y][X]
        if c is None or (sur is not None and c not in sur):
            continue
        k = force(x, y)
        if k <= 0:
            continue
        q = palier(k, niveaux, X, Y) / niveaux
        if q >= 1:
            t.g[Y][X] = couleur
        elif q > 0:
            t.g[Y][X] = sub.proche(mix(c, couleur, q))


def lueur(t, cx, cy, r, couleur, pal, force=0.5, ry=None, cadre=None, n=2, teinte=False):
    """Halo rond (ou ovale) autour d'une lampe : anneaux nets, chaque anneau un pas plus clair sur sa rampe.
    teinte : chaque anneau se mélange plutôt vers `couleur` (lumière chaude sur des matières froides)."""
    ry = ry or r
    cadre = cadre or (cx - r, cy - ry, cx + r, cy + ry)
    for X, Y, x, y in pixels(t, *cadre):
        c = t.g[Y][X]
        if c is None:
            continue
        d = math.hypot((x - cx) / r, (y - cy) / ry)
        if d >= 1:
            continue
        q = palier(min(1.0, (1 - d) * 3.2 * force), n, X, Y)
        if q:
            en_rampe = getattr(pal, "_rampe", {}).get(c) is not None
            t.g[Y][X] = pal.melange(c, couleur, 0.3 * q) if (teinte or not en_rampe) else pal.pas(c, q)


def semis(t, cond, couleurs, densite, graine=0, cadre=(0, 0, None, None), taille=1):
    """Petits points semés (herbes, étoiles, cailloux) : densité par pixel 1× ; taille en pixels réels."""
    e = t.e
    for X, Y, x, y in pixels(t, *cadre):
        cx, cy = int(x), int(y)
        if (X - cx * e) or (Y - cy * e):
            continue  # un tirage par case 1× : même semis aux deux échelles
        h = hasard(cx, cy, graine)
        if h < densite and cond(x, y):
            c = couleurs[int(hasard(cx, cy, graine + 7) * len(couleurs)) % len(couleurs)]
            dx = int(hasard(cx, cy, graine + 3) * e)
            dy = int(hasard(cx, cy, graine + 5) * e)
            for a in range(taille):
                for b in range(taille):
                    t.pf(cx * e + dx + a, cy * e + dy + b, c)


def nuage(t, cx, cy, l, h, c, clair, ombre, bas_plat=True):
    """Nuage en boules : base `c`, sommet `clair`, dessous `ombre`."""
    boules = []
    n = max(2, int(l / max(h, 1) * 1.6))
    for i in range(n):
        u = i / (n - 1) - 0.5
        bx = cx + u * l * 0.8
        r = h * (0.62 + 0.38 * math.cos(u * math.pi)) * (0.9 + 0.2 * hasard(i, int(cx), 3))
        boules.append((bx, cy - r * 0.35, r * 1.05, r))
    for bx, by, rx, ry in boules:
        ell(t, bx, by, rx, ry, ombre, cond=(lambda x, y, u, v: y <= cy + h * 0.25) if bas_plat else None)
    for bx, by, rx, ry in boules:
        ell(t, bx, by - 0.5, rx * 0.95, ry * 0.92, c, cond=(lambda x, y, u, v: y <= cy) if bas_plat else None)
    for bx, by, rx, ry in boules:
        ell(t, bx - rx * 0.15, by - ry * 0.3, rx * 0.6, ry * 0.5, clair, cond=lambda x, y, u, v: v < 0.2)


def etoile4(t, x, y, c, r=1, coeur=None):
    """Petite étoile à quatre branches (un point en 1× si r = 0)."""
    point(t, x, y, coeur or c)
    e = t.e
    for i in range(1, int(r * e) + 1):
        for a, b in ((i, 0), (-i, 0), (0, i), (0, -i)):
            t.pf(int(x * e) + a, int(y * e) + b, c)


def cerne(t, c, sauf=(), dedans=None):
    """Cerne d'un pixel réel autour de ce qui est dessiné (à l'intérieur d'un cadre, s'il est donné)."""
    poses = []
    for Y in range(t.H):
        for X in range(t.W):
            if t.g[Y][X] is not None:
                continue
            for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                v = t.getf(X + a, Y + b)
                if v is not None and v not in sauf:
                    poses.append((X, Y))
                    break
    for X, Y in poses:
        t.g[Y][X] = c
