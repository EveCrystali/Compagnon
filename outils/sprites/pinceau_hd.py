"""Pinceaux des personnages en haute définition (docs/SPRITES.md, « Personnages en haute définition »).

Outil de fabrication en Python pur (ni numpy ni Pillow) : une `Feuille` est une grille de couleurs à l'unité de la
scène HD (480 × 240 unités, 2 px d'écran par unité). Tout se dessine en coordonnées continues (le pixel i couvre
[i, i + 1[) ; chaque forme est un volume éclairé d'en haut à gauche, rendu sur une `Rampe` de trois à cinq tons, avec
une bande de trame ordonnée (Bayer 4 × 4) au passage d'un ton au suivant. La trame est ancrée au décalage de la
feuille : un corps qui monte d'un pixel (la respiration) emporte sa trame, elle ne scintille pas.

Chaque pixel se souvient de la couleur de cerne de sa matière : le cerne extérieur (`cerner`) est teinté (brun
sombre autour du bois, bleu nuit autour du ciré), jamais un noir uniforme.
"""
import math

BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
CERNE = "#1a1726"
# La lumière : en haut à gauche, un peu vers nous.
LX, LY, LZ = -0.50, -0.62, 0.60


def seuil(X, Y):
    return (BAYER[Y % 4][X % 4] + 0.5) / 16.0


def rvb(c):
    return int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)


def mix(a, b, k):
    ra, va, ba = rvb(a)
    rb, vb, bb = rvb(b)
    return "#%02x%02x%02x" % (int(round(ra + (rb - ra) * k)), int(round(va + (vb - va) * k)),
                              int(round(ba + (bb - ba) * k)))


class Rampe:
    """Les tons d'une matière, du plus sombre au plus clair, et la couleur de son cerne."""

    def __init__(self, *tons, cerne=None):
        self.t = tons
        self.cerne = cerne or mix(tons[0], CERNE, 0.62)

    def __getitem__(self, i):
        return self.t[max(0, min(len(self.t) - 1, i))]

    def __len__(self):
        return len(self.t)


def _lum(nx, ny, nz):
    return nx * LX + ny * LY + nz * LZ


class Feuille:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.c = [[None] * w for _ in range(h)]
        self.k = [[None] * w for _ in range(h)]
        self.ox = self.oy = 0          # décalage entier de tout ce qui se dessine (respiration, balancement)

    # ---- bas niveau
    def pose(self, X, Y, c, k=None):
        if 0 <= X < self.w and 0 <= Y < self.h:
            self.c[Y][X] = c
            if k is not None:
                self.k[Y][X] = k
            elif self.k[Y][X] is None:
                self.k[Y][X] = mix(c, CERNE, 0.62)

    def px(self, x, y, c, k=None):
        """Un pixel, en coordonnées du dessin (décalage appliqué)."""
        X, Y = int(math.floor(x)) + self.ox, int(math.floor(y)) + self.oy
        self.pose(X, Y, c, k)
        return (X, Y)

    def lire(self, x, y):
        X, Y = int(math.floor(x)) + self.ox, int(math.floor(y)) + self.oy
        if 0 <= X < self.w and 0 <= Y < self.h:
            return self.c[Y][X]
        return None

    def _ton(self, r, v, X, Y, trame):
        n = len(r.t)
        f = max(0.0, min(1.0, v)) * (n - 1)
        i = int(f)
        if i >= n - 1:
            return r.t[n - 1]
        fr = f - i
        lo, hi = 0.5 - trame, 0.5 + trame
        if fr <= lo:
            return r.t[i]
        if fr >= hi:
            return r.t[i + 1]
        return r.t[i + 1] if (fr - lo) / (hi - lo) > seuil(X - self.ox, Y - self.oy) else r.t[i]

    def forme(self, dedans, boite, matiere, val=None, ton=None, trame=0.22, dans=None, hors=None, densite=None,
              cerne=None):
        """Peint les pixels où `dedans(x, y)` ; `val(x, y)` (0 sombre … 1 clair) choisit le ton de la rampe.
        `dans` / `hors` : ensembles de pixels déjà peints qui limitent la forme. `densite` : transparence en trame.
        Renvoie l'ensemble des pixels peints."""
        x0, y0, x1, y1 = boite
        fait = set()
        plat = isinstance(matiere, str)
        k = cerne if cerne is not None else (None if plat else matiere.cerne)
        for Y in range(max(0, int(math.floor(y0)) + self.oy), min(self.h, int(math.ceil(y1)) + self.oy + 1)):
            y = Y + 0.5 - self.oy
            for X in range(max(0, int(math.floor(x0)) + self.ox), min(self.w, int(math.ceil(x1)) + self.ox + 1)):
                x = X + 0.5 - self.ox
                if dans is not None and (X, Y) not in dans:
                    continue
                if hors is not None and (X, Y) in hors:
                    continue
                if not dedans(x, y):
                    continue
                if densite is not None:
                    d = densite(x, y) if callable(densite) else densite
                    if d <= seuil(X - self.ox, Y - self.oy):
                        continue
                if plat:
                    c = matiere
                elif ton is not None:
                    c = matiere[ton]
                else:
                    c = self._ton(matiere, val(x, y), X, Y, trame)
                self.c[Y][X] = c
                self.k[Y][X] = k if k is not None else mix(c, CERNE, 0.62)
                fait.add((X, Y))
        return fait

    def gommer(self, pixels, garde=None):
        """Efface des pixels (garde(X, Y) vrai : le pixel reste, mais ne sera pas cerné)."""
        for (X, Y) in pixels:
            if garde is not None and garde(X, Y):
                self.k[Y][X] = ""
            else:
                self.c[Y][X] = None
                self.k[Y][X] = None

    # ---- volumes
    def boule(self, cx, cy, rx, ry, matiere, gain=0.625, biais=0.375, cond=None, **kw):
        """Ellipsoïde éclairé. cond(x, y, u, v) rogne la forme."""
        def dedans(x, y):
            u, v = (x - cx) / rx, (y - cy) / ry
            return u * u + v * v <= 1 and (cond is None or cond(x, y, u, v))

        def val(x, y):
            u, v = (x - cx) / rx, (y - cy) / ry
            return biais + gain * _lum(u, v, math.sqrt(max(0.0, 1 - u * u - v * v)))
        return self.forme(dedans, (cx - rx, cy - ry, cx + rx, cy + ry), matiere, val, **kw)

    def disque(self, cx, cy, rx, ry, matiere, cond=None, **kw):
        """Ellipse à plat (une couleur, ou un ton d'une rampe avec ton=)."""
        def dedans(x, y):
            u, v = (x - cx) / rx, (y - cy) / ry
            return u * u + v * v <= 1 and (cond is None or cond(x, y, u, v))
        return self.forme(dedans, (cx - rx, cy - ry, cx + rx, cy + ry), matiere, **kw)

    def tube(self, pts, matiere, gain=0.625, biais=0.375, **kw):
        """Membre : suite de points (x, y, rayon) reliés par des capsules au rayon interpolé."""
        segs = [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)] or [(pts[0], pts[0])]

        def proche(x, y):
            meilleur = None
            for (ax, ay, ar), (bx, by, br) in segs:
                dx, dy = bx - ax, by - ay
                l2 = dx * dx + dy * dy
                s = 0.0 if l2 == 0 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / l2))
                qx, qy, r = ax + dx * s, ay + dy * s, ar + (br - ar) * s
                d = math.hypot(x - qx, y - qy) / max(r, 1e-6)
                if meilleur is None or d < meilleur[0]:
                    meilleur = (d, (x - qx) / max(r, 1e-6), (y - qy) / max(r, 1e-6))
            return meilleur

        def dedans(x, y):
            return proche(x, y)[0] <= 1

        def val(x, y):
            d, nx, ny = proche(x, y)
            return biais + gain * _lum(nx, ny, math.sqrt(max(0.0, 1 - d * d)))
        rm = max(p[2] for p in pts)
        boite = (min(p[0] for p in pts) - rm, min(p[1] for p in pts) - rm,
                 max(p[0] for p in pts) + rm, max(p[1] for p in pts) + rm)
        return self.forme(dedans, boite, matiere, val, **kw)

    def poly(self, pts, matiere, rond=0.9, ny=0.0, gain=0.625, biais=0.375, val=None, **kw):
        """Polygone plein (pair-impair). Sans `val` ni `ton`, il est éclairé comme un fût : chaque ligne est
        bombée d'un bord à l'autre (rond = 0 : à plat ; ny < 0 : la face regarde un peu vers le haut)."""
        def portees(y):
            xs = []
            for i in range(len(pts)):
                (xa, ya), (xb, yb) = pts[i], pts[(i + 1) % len(pts)]
                if (ya <= y < yb) or (yb <= y < ya):
                    xs.append(xa + (y - ya) * (xb - xa) / (yb - ya))
            xs.sort()
            return list(zip(xs[0::2], xs[1::2]))
        cache = {}

        def portee(x, y):
            if y not in cache:
                cache[y] = portees(y)
            for a, b in cache[y]:
                if a <= x < b:
                    return a, b
            return None

        def dedans(x, y):
            return portee(x, y) is not None

        def v(x, y):
            a, b = portee(x, y)
            u = ((x - a) / max(b - a, 1e-6) * 2 - 1) * rond
            return biais + gain * _lum(u, ny, math.sqrt(max(0.0, 1 - u * u - ny * ny)))
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        plat = isinstance(matiere, str) or kw.get("ton") is not None
        return self.forme(dedans, (min(xs), min(ys), max(xs), max(ys)), matiere, None if plat else (val or v), **kw)

    def tour(self, cx, y0, y1, demi, matiere, gain=0.625, biais=0.375, cond=None, **kw):
        """Pièce tournée (fuseau, plateau, ampoule de verre) d'axe vertical : demi(y) est sa demi-largeur.
        Là où elle s'élargit vers le bas, la surface regarde vers le haut et prend la lumière."""
        def dedans(x, y):
            return abs(x - cx) <= demi(y) and (cond is None or cond(x, y))

        def val(x, y):
            w = max(demi(y), 1e-6)
            u = max(-1.0, min(1.0, (x - cx) / w))
            pente = demi(y + 0.5) - demi(y - 0.5)
            nx, ny, nz = u, -pente * 0.7, math.sqrt(max(0.0, 1 - u * u))
            n = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            return biais + gain * _lum(nx / n, ny / n, nz / n)
        m = max(demi(y0 + (y1 - y0) * i / 40.0) for i in range(41))
        return self.forme(dedans, (cx - m, y0, cx + m, y1 - 0.01), matiere, val, **kw)

    def rect(self, x, y, w, h, matiere, **kw):
        return self.poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], matiere, **kw)

    # ---- traits d'un pixel
    def _points_ligne(self, x0, y0, x1, y1):
        x0, y0, x1, y1 = int(math.floor(x0)), int(math.floor(y0)), int(math.floor(x1)), int(math.floor(y1))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        out = []
        while True:
            out.append((x0, y0))
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy
        return out

    def _tracer(self, points, c, k=None, sur=None, dans=None):
        fait = set()
        for (x, y) in points:
            X, Y = x + self.ox, y + self.oy
            if not (0 <= X < self.w and 0 <= Y < self.h):
                continue
            if sur and self.c[Y][X] is None:
                continue
            if dans is not None and (X, Y) not in dans:
                continue
            self.c[Y][X] = c
            if k is not None:
                self.k[Y][X] = k
            elif self.k[Y][X] is None:
                self.k[Y][X] = mix(c, CERNE, 0.62)
            fait.add((X, Y))
        return fait

    def trait(self, x0, y0, x1, y1, c, k=None, sur=False, dans=None):
        return self._tracer(self._points_ligne(x0, y0, x1, y1), c, k, sur, dans)

    def courbe(self, pts, c, k=None, sur=False, dans=None):
        """Courbe d'un pixel passant par les points (Catmull-Rom), nettoyée de ses coudes en L."""
        if len(pts) == 2:
            return self.trait(pts[0][0], pts[0][1], pts[1][0], pts[1][1], c, k, sur, dans)
        p = [pts[0]] + list(pts) + [pts[-1]]
        brut = []
        for i in range(1, len(p) - 2):
            p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
            n = int(max(abs(p2[0] - p1[0]), abs(p2[1] - p1[1])) * 4) + 2
            for j in range(n + 1):
                s = j / n
                q = []
                for d in (0, 1):
                    q.append(0.5 * ((2 * p1[d]) + (-p0[d] + p2[d]) * s + (2 * p0[d] - 5 * p1[d] + 4 * p2[d] - p3[d]) * s * s
                                    + (-p0[d] + 3 * p1[d] - 3 * p2[d] + p3[d]) * s ** 3))
                pt = (int(math.floor(q[0])), int(math.floor(q[1])))
                if not brut or brut[-1] != pt:
                    brut.append(pt)
        # Ligne « pixel parfait » : on retire le pixel du coin quand ses deux voisins se touchent en diagonale.
        net = []
        i = 0
        while i < len(brut):
            if 0 < i < len(brut) - 1:
                a, b, d = net[-1], brut[i], brut[i + 1]
                if abs(a[0] - d[0]) == 1 and abs(a[1] - d[1]) == 1 and (b[0] == a[0] or b[1] == a[1]) \
                        and (b[0] == d[0] or b[1] == d[1]):
                    i += 1
                    continue
            net.append(brut[i])
            i += 1
        return self._tracer(net, c, k, sur, dans)

    # ---- finitions
    def ourler(self, pixels, c, cotes=((1, 0), (0, 1)), dehors=True):
        """Liseré intérieur d'une forme posée sur une autre : ses pixels de bord (du côté `cotes`) dont le voisin
        est plein mais hors de la forme prennent la couleur c. dehors=True : aussi quand le voisin est vide."""
        a_poser = []
        for (X, Y) in pixels:
            for a, b in cotes:
                v = (X + a, Y + b)
                if v in pixels:
                    continue
                plein = 0 <= v[0] < self.w and 0 <= v[1] < self.h and self.c[v[1]][v[0]] is not None
                if plein or dehors:
                    a_poser.append((X, Y))
                    break
        for (X, Y) in a_poser:
            self.c[Y][X] = c
        return set(a_poser)

    def recolorer(self, pixels, table):
        for (X, Y) in pixels:
            c = self.c[Y][X]
            if c in table:
                self.c[Y][X] = table[c]

    def pleins(self):
        return {(X, Y) for Y in range(self.h) for X in range(self.w) if self.c[Y][X] is not None}

    def cerner(self):
        """Cerne extérieur d'un pixel, à la couleur de cerne de la matière voisine (coins laissés ouverts)."""
        a_poser = []
        for Y in range(self.h):
            for X in range(self.w):
                if self.c[Y][X] is not None:
                    continue
                for a, b in ((0, 1), (1, 0), (-1, 0), (0, -1)):
                    x, y = X + a, Y + b
                    if 0 <= x < self.w and 0 <= y < self.h and self.c[y][x] is not None and self.k[y][x] != "":
                        a_poser.append((X, Y, self.k[y][x] or CERNE))
                        break
        for X, Y, k in a_poser:
            self.c[Y][X] = k
            self.k[Y][X] = k

    def sans_orphelins(self):
        """Retire les pixels sans aucun voisin (diagonales comprises) : un point de trame perdu au bord d'un halo."""
        seuls = []
        for Y in range(self.h):
            for X in range(self.w):
                if self.c[Y][X] is None:
                    continue
                if not any(0 <= X + a < self.w and 0 <= Y + b < self.h and self.c[Y + b][X + a] is not None
                           for b in (-1, 0, 1) for a in (-1, 0, 1) if a or b):
                    seuls.append((X, Y))
        for (X, Y) in seuls:
            self.c[Y][X] = None
            self.k[Y][X] = None
        return len(seuls)

    def couleurs(self):
        vues = []
        for r in self.c:
            for v in r:
                if v is not None and v not in vues:
                    vues.append(v)
        return vues
