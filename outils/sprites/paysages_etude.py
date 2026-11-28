"""Étude « paysages haute définition » (docs/maquettes/paysages/ETUDE.md) : la mare du prologue au soleil couchant,
peinte par le code dans trois définitions, pour qu'Antoine tranche à l'œil.

    py outils/sprites/paysages_etude.py [dossier]          (défaut : docs/maquettes/paysages)

    A  192 ×  80 unités, 5 px par unité   la définition d'aujourd'hui, enrichie
    B  320 × 160 unités, 3 px par unité   haute définition, grand paysage
    C  480 × 240 unités, 2 px par unité   très haute définition
    D  384 × 160 unités, 3 px par unité   exactement le double de l'actuel (même rapport), 1152 px de large :
                                          plus large que l'écran, donc cadrée sur téléphone

Rien n'est importé ni dessiné à la main dans un logiciel : chaque pixel sort des fonctions ci-dessous. Le même
tableau est décrit une seule fois, en « unités du monde » (celles du décor actuel : 192 de large, le sol à y = 80) ;
chaque définition le rejoue sur sa grille, et les petites choses (feuilles, brins, tuiles, reflets) se dessinent au
pixel de cette grille : plus la grille est fine, plus il y en a.

Composition, comme un peintre : un premier plan sombre (berge, arbre, roseaux) ; un plan moyen (mare, prés, maison,
colline d'en face) ; des lointains bleutés ; un grand ciel. Une seule lumière : le soleil bas, derrière les crêtes.
Palette limitée (62 couleurs au plus, la limite du format texte des sprites) : violets, pêche, or, sarcelle, crème ;
jamais d'opposition rouge / vert.

Outil d'étude seulement : il n'écrit rien dans assets/ et ne touche pas aux décors en service. Il dépend de numpy et
de Pillow (comme les planches).
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)

FORMATS = {"A": (192, 80, 5), "B": (320, 160, 3), "C": (480, 240, 2), "D": (384, 160, 3)}
IMAGES, DUREE = 8, 200            # la boucle d'ambiance : 8 images à 5 images par seconde
MARGE = 6                         # unités peintes hors champ de chaque côté, pour la parallaxe
SOLEIL = (112.0, 37.0)
BAYER = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + 0.5) / 16.0

# ---------------------------------------------------------------------------------------------------------------
# Palette : une liste commune, chaque couleur prend un numéro à son premier emploi.
# ---------------------------------------------------------------------------------------------------------------
PAL = []
_NUM = {}


def c(h):
    if h not in _NUM:
        _NUM[h] = len(PAL)
        PAL.append(h)
    return _NUM[h]


def cs(*hs):
    return [c(h) for h in hs]


def rvb(h):
    return int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)


CIEL = cs("#262758", "#34316f", "#473c86", "#5f4a99", "#7d5aa6", "#a06aa8", "#c67c9f", "#e4928a", "#f4ab72", "#fbc67c",
          "#ffdf9e", "#fff0c4")
SOL, BLANC = c("#fff6d8"), c("#ffffff")
L0, L1, L2, L3, L4, L5 = cs("#4a4788", "#5d5a9c", "#7770b0", "#9484bd", "#b596c2", "#d3a5b8")
S0, S1, S2, S3, S4 = cs("#0e2a40", "#123f52", "#1d6578", "#2f8f9c", "#5bb3ae")
OR1, OR2, OR3 = cs("#d9a441", "#f2c46b", "#ffe08f")
N0, N1, N2 = cs("#0b1530", "#11203f", "#15304f")
BR1, BR2, M2, M3, M4 = cs("#4a2e17", "#7a4b26", "#bf915f", "#e2bd85", "#f4dcae")
D1, D2 = cs("#3d3f7a", "#5458a0")
P1, P3 = cs("#6b6183", "#c3b8c9")
O2, O3 = cs("#d9803a", "#f69d50")
LUM, LUM2 = cs("#ffd65a", "#fff2b0")
CREME, ENCRE, VIOLET, BLEU = cs("#fff6e6", "#1c2128", "#9b8cff", "#6cb6ff")
# L'eau : neuf tons froids à elle, puis les chauds du ciel pour les reflets du couchant.
EAU = cs("#101a38", "#182650", "#22346a", "#33437f", "#4d4f92", "#6d5a9a", "#93669a", "#bb7890", "#dc917f") + CIEL[8:11]
NUAGE = [CIEL[2], CIEL[3], CIEL[4], CIEL[5], CIEL[6], CIEL[7], CIEL[8], CIEL[9], CIEL[10], SOL]


# ---------------------------------------------------------------------------------------------------------------
# Hasard et bruit (déterministes : la même image à chaque lancement)
# ---------------------------------------------------------------------------------------------------------------
def hz(a, b=0, g=0):
    a = np.asarray(a, dtype=np.int64)
    b = np.asarray(b, dtype=np.int64)
    h = (a * 374761393 + b * 668265263 + int(g) * 362437 + 1013904223) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return (h & 0xFFFFFF) / float(1 << 24)


def bruit(x, y, g=0):
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    ix, iy = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64)
    fx, fy = x - ix, y - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = hz(ix, iy, g), hz(ix + 1, iy, g)
    d, e = hz(ix, iy + 1, g), hz(ix + 1, iy + 1, g)
    return (a + (b - a) * fx) * (1 - fy) + (d + (e - d) * fx) * fy


def fbm(x, y, octaves=4, g=0):
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    s, amp, tot = 0.0, 1.0, 0.0
    for o in range(octaves):
        s = s + amp * bruit(x * (2 ** o), y * (2 ** o), g + o * 17)
        tot += amp
        amp *= 0.5
    return s / tot


def onde(p, d=0.0):
    return math.sin(2 * math.pi * (p + d))


# ---------------------------------------------------------------------------------------------------------------
# Le peintre : une grille de numéros de couleur (-1 : vide), des coordonnées « monde », des pinceaux
# ---------------------------------------------------------------------------------------------------------------
class Peintre:
    def __init__(self, fmt, phase=0.0):
        self.fmt = fmt
        self.W, self.H, self.k = FORMATS[fmt]
        self.s = self.W / 192.0                      # pixels par unité du monde
        self.y0 = 80 - self.H / self.s               # haut du tableau, en unités du monde
        self.M = int(round(MARGE * self.s))
        self.Wt = self.W + 2 * self.M
        self.XI, self.YI = np.meshgrid(np.arange(self.Wt), np.arange(self.H))
        self.X = (self.XI - self.M + 0.5) / self.s
        self.Y = (self.YI + 0.5) / self.s + self.y0
        self.T = BAYER[self.YI % 4, self.XI % 4]
        self.p = phase
        self.hd = self.s >= 1.6
        self.thd = self.s >= 2.4
        # À la définition d'aujourd'hui, un pixel est gros : on trame moins et on sème moins, sinon tout se brouille.
        self.d = 1.0 if self.hd else 0.5
        self.tr = 1.0 if self.hd else 0.55
        self.a = None
        self.neuf()

    def neuf(self):
        self.a = np.full((self.H, self.Wt), -1, dtype=np.int16)
        return self.a

    # -- conversions
    def px(self, x):
        return int(math.floor(x * self.s + self.M))

    def py(self, y):
        return int(math.floor((y - self.y0) * self.s))

    def ep(self, u):
        """Épaisseur en pixels d'une largeur donnée en unités (un pixel au moins)."""
        return max(1, int(round(u * self.s)))

    # -- pinceaux
    def remplir(self, masque, coul):
        self.a[masque] = coul

    def rampe(self, masque, v, rampe, trame=0.6):
        """Valeur 0..1 → un ton de la rampe ; `trame` : part de chaque palier qui se mélange en damier ordonné."""
        n = len(rampe)
        f = np.clip(v, 0, 1) * (n - 1)
        i = np.floor(f)
        fr = f - i
        if trame > 0:
            fr = np.clip((fr - 0.5) / (trame * self.tr) + 0.5, 0, 1)
            i = i + (fr > self.T)
        else:
            i = i + (fr > 0.5)
        i = np.clip(i, 0, n - 1).astype(np.int64)
        self.a[masque] = np.asarray(rampe, dtype=np.int16)[i][masque]

    def bloc(self, X, Y, coul, ep=1):
        x0, y0 = max(0, X), max(0, Y)
        x1, y1 = min(self.Wt, X + ep), min(self.H, Y + ep)
        if x0 < x1 and y0 < y1:
            self.a[y0:y1, x0:x1] = coul

    def point(self, x, y, coul, ep=1):
        self.bloc(self.px(x), self.py(y), coul, ep)

    def trait(self, x0, y0, x1, y1, coul, ep=1):
        X0, Y0, X1, Y1 = self.px(x0), self.py(y0), self.px(x1), self.py(y1)
        n = max(abs(X1 - X0), abs(Y1 - Y0), 1)
        for i in range(n + 1):
            self.bloc(int(round(X0 + (X1 - X0) * i / n)), int(round(Y0 + (Y1 - Y0) * i / n)), coul, ep)

    def courbe(self, pts, coul, ep=1, ep_fin=None):
        """Suite de points lissée (Catmull-Rom) ; l'épaisseur peut s'affiner jusqu'à ep_fin."""
        P = [pts[0]] + list(pts) + [pts[-1]]
        segs = len(pts) - 1
        pas = max(6, int(8 * self.s))
        prec = None
        for i in range(segs):
            p0, p1, p2, p3 = P[i], P[i + 1], P[i + 2], P[i + 3]
            for j in range(pas + 1):
                t = j / pas
                q = [0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t * t
                            + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t ** 3) for k in (0, 1)]
                u = (i + t) / segs
                e = ep if ep_fin is None else max(1, int(round(ep + (ep_fin - ep) * u)))
                if prec is not None:
                    self.trait(prec[0], prec[1], q[0], q[1], coul, e)
                prec = q

    def ell(self, cx, cy, rx, ry, coul, cond=None):
        rx, ry = max(rx, 0.5 / self.s), max(ry, 0.5 / self.s)
        m = ((self.X - cx) / rx) ** 2 + ((self.Y - cy) / ry) ** 2 <= 1
        if cond is not None:
            m &= cond
        self.a[m] = coul
        return m

    def rect(self, x, y, w, h, coul):
        X0, Y0 = self.px(x), self.py(y)
        X1, Y1 = max(X0 + 1, int(round((x + w) * self.s + self.M))), max(Y0 + 1, int(round((y + h - self.y0) * self.s)))
        X0, Y0, X1, Y1 = max(0, X0), max(0, Y0), min(self.Wt, X1), min(self.H, Y1)
        if X0 < X1 and Y0 < Y1:
            self.a[Y0:Y1, X0:X1] = coul

    def masque_poly(self, pts):
        im = Image.new("L", (self.Wt, self.H), 0)
        ImageDraw.Draw(im).polygon([(x * self.s + self.M - 0.5, (y - self.y0) * self.s - 0.5) for x, y in pts], fill=1)
        return np.asarray(im).astype(bool)

    def poly(self, pts, coul):
        m = self.masque_poly(pts)
        self.a[m] = coul
        return m

    def crete(self, masque):
        """Les pixels du masque dont le voisin du dessus n'en fait pas partie (le liseré de lumière)."""
        haut = np.zeros_like(masque)
        haut[1:] = masque[:-1]
        return masque & ~haut

    def volumes(self, boules, rampe, lum, plancher=None, grain=0.0, graine=0, trame=0.55, gain=0.55, base=0.5):
        """Des boules éclairées comme des volumes (nuages, feuillages) : la plus haute gagne, la lumière vient de
        `lum` (vecteur x, y, z). Renvoie le masque peint."""
        best = np.zeros(self.X.shape)
        nx, ny = np.zeros(self.X.shape), np.zeros(self.X.shape)
        for (x, y, r) in boules:
            r = max(r, 0.6 / self.s)
            dx, dy = self.X - x, self.Y - y
            h = np.sqrt(np.maximum(r * r - dx * dx - dy * dy, 0)) / r
            g = h * r > best
            best = np.where(g, h * r, best)
            nx, ny = np.where(g, dx / r, nx), np.where(g, dy / r, ny)
        m = best > 0
        if plancher is not None:
            m &= self.Y < plancher
        nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
        v = base + gain * (nx * lum[0] + ny * lum[1] + nz * lum[2])
        if grain:
            v = v + grain * (fbm(self.X / 3.0, self.Y / 2.0, 3, graine) - 0.5)
        self.rampe(m, v, rampe, trame)
        return m


# ---------------------------------------------------------------------------------------------------------------
# Le ciel
# ---------------------------------------------------------------------------------------------------------------
def valeur_ciel(P, X, Y):
    t = np.clip((Y - P.y0) / (45.5 - P.y0), 0, 1)
    if P.y0 >= 0:
        t = 0.2 + 0.8 * t                     # le bandeau court garde un peu du haut du ciel
    v = t ** 0.9 * 0.93
    d = np.hypot(X - SOLEIL[0], (Y - SOLEIL[1]) * 1.8)
    v = v + 0.34 * np.exp(-(d / 34.0) ** 2) + 0.07 * (fbm(X / 46.0, Y / 9.0, 3, 5) - 0.5)
    return np.clip(v, 0, 1)


def ciel(P):
    P.neuf()
    tout = np.ones(P.X.shape, dtype=bool)
    v = valeur_ciel(P, P.X, P.Y)
    P.rampe(tout, v, CIEL, 0.75)
    # Premières étoiles, dans le haut sombre : une par case au plus, elles scintillent.
    pas = 4.0
    for cy in range(int(P.y0 // pas) - 1, 8):
        for cx in range(-2, 52):
            if hz(cx, cy, 11) > 0.22:
                continue
            x, y = (cx + hz(cx, cy, 12)) * pas, (cy + hz(cx, cy, 13)) * pas
            X, Y = P.px(x), P.py(y)
            if not (0 <= X < P.Wt and 0 <= Y < P.H) or v[Y, X] > 0.3:
                continue
            vive = ((P.p + hz(cx, cy, 14)) % 1.0) < 0.55
            P.bloc(X, Y, SOL if vive else CIEL[5])
            if P.hd and vive and hz(cx, cy, 15) < 0.3:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    P.bloc(X + dx, Y + dy, CIEL[4])
    # Croissant de lune, haut à droite.
    lx, ly = 150.0, P.y0 + (11 if P.y0 < 0 else 6.5)
    r = 2.6 if P.y0 < 0 else 2.0
    lune = (P.X - lx) ** 2 + (P.Y - ly) ** 2 <= r * r
    creux = (P.X - lx + r * 0.55) ** 2 + (P.Y - ly + r * 0.25) ** 2 <= (r * 0.95) ** 2
    P.remplir(lune & ~creux, SOL)
    # Le soleil : disque crème, cœur blanc.
    d = np.hypot(P.X - SOLEIL[0], P.Y - SOLEIL[1])
    P.remplir((d < 7.4) & (P.T < 0.5), CIEL[11])
    P.remplir(d < 5.6, SOL)
    P.remplir(d < 4.2, BLANC)
    return P.a


def amas(cx, cy, l, h, graine, n):
    """Un cumulus : des boules le long d'une base, plus hautes au milieu."""
    b = []
    for i in range(n):
        u = (i + 0.5) / n + (hz(i, 1, graine) - 0.5) * 0.6 / n
        bord = 1 - abs(u - 0.5) * 2
        r = h * (0.3 + 0.7 * bord ** 0.7) * (0.5 + 0.5 * hz(i, 2, graine))
        b.append((cx + (u - 0.5) * l, cy - r * (0.3 + 0.6 * hz(i, 3, graine)), r))
        if hz(i, 4, graine) < 0.5:                       # un bourgeon posé sur l'épaule de la boule
            b.append((cx + (u - 0.5) * l + r * 0.5, cy - r * 1.25, r * 0.5))
    return b


def nuages(P):
    P.neuf()
    p = P.p

    def vers_soleil(x, y, z=0.35):
        dx, dy = SOLEIL[0] - x, SOLEIL[1] - y
        n = math.hypot(dx, dy) or 1
        return dx / n * 0.32, 0.72, z

    # Voiles hauts (cirrus) : des filaments de bruit étirés, éclairés par-dessous.
    def densite(X, Y, d):
        return fbm((X + d) / 30.0, Y / 2.4, 4, 21) - 0.58 - 0.16 * ((Y - (P.y0 + 13)) / 9.0) ** 2

    d0 = densite(P.X, P.Y, 0.5 * onde(p))
    m = d0 > 0
    dessous = d0 - densite(P.X, P.Y + 1.4, 0.5 * onde(p))
    prox = np.exp(-(np.hypot(P.X - SOLEIL[0], P.Y - SOLEIL[1]) / 70.0) ** 2)
    P.rampe(m, 0.22 + 2.6 * dessous + 0.45 * prox + 1.2 * d0, NUAGE[:8], 0.7)
    # Cumulus en volumes : ombre violette en haut, ventre rose puis or vers le soleil.
    groupes = [(36, 15, 46, 8.0, 3, 8, 0.0), (171, 20, 34, 5.5, 5, 7, 0.3), (92, -3.5, 42, 7.5, 7, 8, 0.55),
               (140, 7, 20, 3.4, 9, 5, 0.8)]
    for (cx, cy, l, h, g, n, d) in groupes:
        cx = cx + 0.6 * onde(p, d)
        lum = vers_soleil(cx, cy - h * 0.4)
        P.volumes(amas(cx, cy, l, h, g, n), NUAGE, lum, plancher=cy + h * 0.12, grain=0.22, graine=g, gain=0.62,
                  base=0.5)
        # Le ventre plat, liseré de lumière : la dernière rangée du nuage prend l'or du couchant.
        bas = (P.a >= 0) & (np.abs(P.Y - (cy + h * 0.12)) < 0.6 / P.s + 0.25) & (np.abs(P.X - cx) < l * 0.42)
        P.remplir(bas & (fbm(P.X / 3.0, P.Y, 2, g) > 0.35), NUAGE[7])
    # Barres basses, tout près de l'horizon : presque dans le soleil.
    for i, (x, y, rx, ry) in enumerate(((66, 30.5, 17, 1.25), (150, 28.5, 22, 1.5), (104, 26.2, 13, 1.0),
                                        (22, 33, 14, 1.1), (128, 32.6, 9, 0.8))):
        x = x + 0.5 * onde(p, 0.2 * i)
        u, w = (P.X - x) / rx, (P.Y - y) / ry
        forme = u * u + w * w + 0.5 * (fbm(P.X / 5.0, P.Y / 1.2, 3, 40 + i) - 0.5) <= 1
        P.rampe(forme, 0.5 + 0.34 * w + 0.3 * np.exp(-((P.X - SOLEIL[0]) / 40.0) ** 2), NUAGE[2:], 0.6)
    return P.a


# ---------------------------------------------------------------------------------------------------------------
# Les lointains
# ---------------------------------------------------------------------------------------------------------------
def profil(x, base, amp, ech, graine):
    x = np.asarray(x, dtype=float)
    n = fbm(x / ech, np.full_like(x, 0.37), 4, graine)
    return base - amp * (0.55 * (1 - np.abs(2 * n - 1)) + 0.45 * n)


def f_loin1(x):
    x = np.asarray(x, dtype=float)
    creux = 0.3 + 0.7 * np.clip(np.abs(x - SOLEIL[0]) / 46.0, 0, 1) ** 1.3
    return profil(x, 42.0, 15.0, 34.0, 61) * creux + 42.0 * (1 - creux)


def f_loin2(x):
    return profil(x, 43.5, 8.0, 21.0, 62)


def f_loin3(x):
    return profil(x, 45.6, 5.0, 12.0, 63)


def lointains(P):
    P.neuf()
    p = P.p
    for f, rampe, pente in ((f_loin1, [L3, L4, L5, CIEL[7]], 0.9), (f_loin2, [L2, L3, L4, L5], 0.7),
                            (f_loin3, [L1, L2, L3, L4], 0.5)):
        fx = f(P.X)
        prof = P.Y - fx
        m = prof >= 0
        cote = np.where(P.X < SOLEIL[0], 1.0, -1.0)
        xs = P.X + prof * pente * cote
        versant = (f(xs + 0.7) - f(xs - 0.7)) * cote > 0           # la face tournée vers le soleil
        v = 0.12 + 0.36 * versant + 0.5 * np.clip(prof / 7.0, 0, 1) + 0.1 * (fbm(P.X / 4.0, P.Y / 2.0, 2, 70) - 0.5)
        P.rampe(m, v, rampe, 0.6)
        P.remplir(P.crete(m) & versant, rampe[2])
    # Sapins minuscules sur la crête la plus proche.
    x = -MARGE
    while x < 192 + MARGE:
        k = int(round(x * 10))
        if hz(k, 0, 81) < 0.55 and not 96 < x < 128:
            h = 0.9 + 1.5 * hz(k, 1, 81)
            y = float(f_loin3(x)) + 0.3
            P.poly([(x - 0.55, y), (x + 0.55, y), (x, y - h)], L0)
            P.trait(x, y - h, x, y, L0)
        x += 0.5 + 0.9 * hz(k, 2, 81)
    # Un moulin sur la crête : ses ailes tournent (un quart de tour par boucle, il a quatre ailes).
    mx = 70.0
    my = float(f_loin3(mx)) + 0.2
    P.poly([(mx - 0.9, my), (mx + 0.9, my), (mx + 0.55, my - 3.4), (mx - 0.55, my - 3.4)], L1)
    P.trait(mx + 0.5, my - 3.3, mx + 0.8, my - 0.2, L4)
    P.poly([(mx - 0.8, my - 3.3), (mx + 0.8, my - 3.3), (mx, my - 4.4)], L0)
    for q in range(4):
        a = (p + q) * math.pi / 2 + 0.3
        P.trait(mx, my - 3.5, mx + 3.0 * math.cos(a), my - 3.5 + 3.0 * math.sin(a), L0 if q % 2 else D1)
    P.point(mx, my - 3.5, L5)
    # Des oiseaux rentrent, en chevron, devant le soleil.
    for i, (dx, dy) in enumerate(((0, 0), (-3.2, 1.2), (3.0, 1.5), (-6.6, 2.6), (6.2, 3.1), (-9.6, 4.1), (-1.2, 4.6))):
        x, y = 92 + dx + 0.4 * onde(p, 0.1 * i), 21 + dy + 0.25 * onde(p, 0.3 + 0.13 * i)
        aile = onde(p * 2, 0.17 * i)
        e = max(1.0, 1.1 * P.s) / P.s
        P.trait(x - e, y - 0.55 * aile * e, x, y, CIEL[1])
        P.trait(x, y, x + e, y - 0.55 * aile * e, CIEL[1])
    return P.a


# ---------------------------------------------------------------------------------------------------------------
# Le plan moyen : prés, champs, maison, colline d'en face, puis la mare et ses reflets
# ---------------------------------------------------------------------------------------------------------------
def f_pre(x):
    x = np.asarray(x, dtype=float)
    return 45.8 + 0.9 * np.sin(x / 13.0 + 0.6) - 3.2 * np.exp(-((x - 38) / 25.0) ** 2) + 0.4 * np.sin(x / 4.7)


def f_rive(x):
    x = np.asarray(x, dtype=float)
    return 47.6 + 0.5 * np.sin(x / 7.0 + 2.0) + 0.3 * np.sin(x / 2.9)


def f_colline(x):
    x = np.asarray(x, dtype=float)
    return 47.0 - 22.5 * np.maximum(0, 1 - ((x - 153) / 32.0) ** 2) ** 0.62


def f_berge(x):
    x = np.asarray(x, dtype=float)
    return (72.6 + 1.1 * np.sin(x / 19.0 + 1.0) + 0.5 * np.sin(x / 6.3) - 6.0 * np.exp(-((x - 2) / 22.0) ** 2)
            - 5.0 * np.exp(-((x - 191) / 19.0) ** 2))


def arbre_rond(P, x, y, r, graine, tronc=1.6):
    P.trait(x, y, x, y - tronc, BR1, P.ep(0.35))
    b = [(x + (hz(i, 1, graine) - 0.5) * r * 1.3, y - tronc - r * 0.6 - (hz(i, 2, graine) - 0.3) * r * 0.9,
          r * (0.55 + 0.35 * hz(i, 3, graine))) for i in range(5)]
    cote = 1.0 if x < SOLEIL[0] else -1.0
    P.volumes(b, [S0, S1, S2, S3, OR1], (0.75 * cote, -0.35, 0.25), grain=0.35, graine=graine, gain=0.6, base=0.34)


def maison(P, hx, gy, p, grande=True):
    k = 1.0 if grande else 0.62
    w, h = 9.0 * k, 5.2 * k
    # Mur : la face droite prend le soleil, la gauche est dans l'ombre.
    P.rect(hx - w / 2, gy - h, w, h + 0.4, M4)
    P.rect(hx - w / 2, gy - h, w * 0.36, h + 0.4, M3)
    P.rect(hx - w / 2, gy - h, max(1.0 / P.s, w * 0.09), h + 0.4, M2)
    P.rect(hx - w / 2, gy - 0.5 * k, w, 0.9 * k, P1)                           # soubassement de pierre
    # Toit violet, pan éclairé à droite ; rangs de tuiles dès que la grille le permet.
    toit = [(hx - w / 2 - 1.1 * k, gy - h), (hx - w * 0.28, gy - h - 3.6 * k), (hx + w * 0.28, gy - h - 3.6 * k),
            (hx + w / 2 + 1.1 * k, gy - h)]
    mt = P.poly(toit, D1)
    P.remplir(mt & (P.X > hx + w * 0.1), D2)
    if P.hd:
        rang = (np.floor((P.Y - gy) * P.s / 2.0) % 2 == 0) & (((P.XI + (np.floor((P.Y - gy) * P.s / 2.0) % 4)) % 3) == 0)
        P.remplir(mt & rang, CIEL[1])
    P.remplir(P.crete(mt) & (P.X > hx - w * 0.3), L3)
    # Cheminée.
    chx, chy = hx + w * 0.2, gy - h - 4.9 * k
    P.rect(chx, chy, 1.3 * k, 2.6 * k, P1)
    P.rect(chx + 0.8 * k, chy, max(1.0 / P.s, 0.5 * k), 2.6 * k, P3)
    # Porte ronde bleu-violet, fenêtres qui s'allument (elles vacillent).
    P.rect(hx - 0.9 * k, gy - 3.0 * k, 1.8 * k, 3.0 * k, D2)
    P.ell(hx, gy - 3.0 * k, 0.9 * k, 0.9 * k, D2)
    if P.hd:
        P.point(hx + 0.45 * k, gy - 1.5 * k, LUM)
    for i, fx in enumerate((hx - w * 0.36, hx + w * 0.22)):
        vive = ((p * 2 + 0.37 * i) % 1.0) < 0.5
        P.rect(fx, gy - 3.9 * k, 1.7 * k, 1.8 * k, LUM2 if vive else LUM)
        if P.hd:
            P.rect(fx, gy - 3.9 * k, 1.7 * k, 1.0 / P.s, O2)
            P.trait(fx + 0.85 * k, gy - 3.9 * k, fx + 0.85 * k, gy - 2.2 * k, BR2)
        if P.thd:
            P.trait(fx, gy - 3.0 * k, fx + 1.6 * k, gy - 3.0 * k, BR2)
            P.rect(fx - 0.2, gy - 2.1 * k, 1.7 * k + 0.4, 1.0 / P.s, P3)        # appui de fenêtre
    return chx + 0.6 * k, chy


def fumee(P, x, y, p):
    for i in range(6):
        age = (p + i / 6.0) % 1.0
        fx, fy = x + 5.5 * age ** 1.3 + 0.5 * math.sin(age * 7 + i), y - 10.5 * age
        r = 0.45 + 1.5 * age
        m = ((P.X - fx) ** 2 + (P.Y - fy) ** 2 <= r * r) & (P.T > age * 0.95 - 0.08)
        P.remplir(m, L5 if age < 0.5 else L4)
        if age < 0.55:
            P.ell(fx + r * 0.3, fy + r * 0.2, r * 0.45, r * 0.45, CIEL[10], cond=P.T > age)


def moyen(P):
    P.neuf()
    p = P.p
    X, Y = P.X, P.Y
    # ---- Les prés, à contre-jour : sarcelle, crêtes dorées.
    fp = f_pre(X)
    terre = Y < f_rive(X) + 0.8                    # plus bas, c'est la mare
    pre = (Y >= fp) & terre
    v = 0.62 + 0.3 * (fbm(X / 9.0, Y / 2.2, 3, 90) - 0.5) - 0.11 * (Y - fp)
    P.rampe(pre, v, [S1, S2, S3, S4], 0.7)
    # Champ de lavande (rangs violets) et champ de blé (sillons dorés), séparés par des haies.
    for (x0, x1, y0, y1, a, b, pente) in ((7, 25, 0.5, 2.6, CIEL[4], CIEL[3], 1.6), (58, 92, 0.6, 2.8, OR2, OR1, -1.8),
                                          (98, 128, 0.9, 2.4, S4, S3, 1.2)):
        champ = (X > x0 + (Y - fp) * 1.4) & (X < x1 + (Y - fp) * 1.4) & (Y > fp + y0) & (Y < fp + y1)
        rang = np.floor((X + (Y - fp) * pente) * P.s / max(2, P.ep(0.9))) % 2 == 0
        P.remplir(champ & rang, a)
        P.remplir(champ & ~rang, b)
        haie = (np.abs(Y - (fp + y0)) < 0.5 / P.s + 0.2) & (X > x0) & (X < x1 + 3) & (hz(P.XI // P.ep(0.7), 3, x0) < 0.7)
        P.remplir(haie, S0)
    P.remplir(P.crete(pre), OR2)
    P.remplir(P.crete(pre) & (X > 86), OR3)
    # ---- La colline d'en face (le but du voyage) : à contre-jour, son flanc gauche accroche la lumière.
    fc = f_colline(X)
    col = (Y >= fc) & (fc < 46.9) & terre
    u = (X - 153) / 32.0
    v = 0.44 - 0.42 * u + 0.2 * (fbm(X / 6.0, Y / 3.0, 3, 91) - 0.5) + 0.05 * np.sin((Y - fc) * 1.5 + X * 0.2) \
        - 0.012 * (Y - fc)
    P.rampe(col, v, [S0, S1, S2, S3, S4], 0.75)
    P.remplir(P.crete(col) & (X < 163), OR3)
    P.remplir(P.crete(col) & (X >= 163), S3)
    # Bosquets sur ses flancs.
    n = int(15 * P.s ** 0.8)
    pts = sorted(((124 + 58 * float(hz(i, 1, 92)), float(hz(i, 2, 92)), float(hz(i, 3, 92))) for i in range(n)),
                 key=lambda q: q[1])
    for (x, t, t2) in pts:
        haut = float(f_colline(x))
        y = haut + 2.6 + (45.0 - haut) * t ** 0.8
        if y > 46 or haut > 43.5 or abs(x - 146 - (y - 35) * 0.3) < 4.5:
            continue
        r = 0.9 + 0.9 * t2
        P.ell(x + r * 0.9, y + r * 0.55, r * 1.3, r * 0.35, S0)                 # son ombre, vers la droite
        P.ell(x, y, r, r * 0.9, S1 if x > 152 else S2)
        P.ell(x - r * 0.3, y - r * 0.3, r * 0.6, r * 0.5, S2 if x > 152 else S3)
        if x < 152:
            P.point(x - r * 0.55, y - r * 0.55, OR2)
    # Le sentier en lacets jusqu'au sommet.
    lacets = [(136.5, 46.6), (145, 42.6), (140.5, 39.2), (151.5, 35.2), (146.5, 31.4), (153.5, 27.8), (152.4, 25.2)]
    for i in range(len(lacets) - 1):
        (xa, ya), (xb, yb) = lacets[i], lacets[i + 1]
        P.trait(xa, ya, xb, yb, OR2 if i % 2 == 0 else OR1, P.ep(0.45 if i > 2 else 0.6))
    # L'arbre unique du sommet, et sa balançoire.
    sx, sy = 153.0, float(f_colline(153.0)) + 0.3
    P.courbe([(sx - 0.2, sy + 0.4), (sx + 0.1, sy - 2.6), (sx - 0.1, sy - 6.4)], BR1, P.ep(1.1), P.ep(0.6))
    P.trait(sx, sy - 3.4, sx + 3.4, sy - 5.2, BR1, 1)
    dx = 0.35 * onde(p)
    if P.hd:
        P.trait(sx + 2.2, sy - 4.5, sx + 2.2 + dx, sy - 1.6, M2)
        P.trait(sx + 3.2, sy - 5.0, sx + 3.2 + dx, sy - 1.6, M2)
        P.trait(sx + 2.0 + dx, sy - 1.5, sx + 3.4 + dx, sy - 1.5, O3)
    else:
        P.trait(sx + 2.6, sy - 4.6, sx + 2.6 + dx, sy - 1.6, M2)
    feuillage = [(sx - 0.2, sy - 7.6, 4.0), (sx - 3.7, sy - 6.0, 2.8), (sx + 3.6, sy - 6.4, 2.9), (sx - 1.6, sy - 10.2, 2.8),
                 (sx + 2.0, sy - 9.8, 2.6), (sx + 0.4, sy - 5.2, 2.6), (sx - 5.2, sy - 4.8, 1.5), (sx + 5.3, sy - 5.0, 1.4)]
    P.volumes(feuillage, [S0, S1, S2, S3, OR1, OR3], (-0.8, 0.1, 0.25), grain=0.5, graine=93, gain=0.62, base=0.36,
              trame=0.8)
    # ---- La vie des prés.
    for (x, r, g) in ((12, 2.1, 1), (55, 1.8, 2), (97, 2.0, 3), (108, 1.5, 4), (118, 2.2, 5), (1, 2.4, 6)):
        arbre_rond(P, x, float(f_pre(x)) + 0.4, r, 100 + g)
    for i, x in enumerate((27.0, 29.6, 49.5, 52.0)):                            # peupliers
        gy = float(f_pre(x)) + 0.3
        h = 6.5 + 1.5 * hz(i, 0, 94)
        P.ell(x, gy - h / 2 - 0.4, 1.05, h / 2, S0)
        P.ell(x + 0.35, gy - h / 2 - 0.4, 0.6, h / 2 - 0.5, S1)
        P.ell(x + 0.7, gy - h / 2 - 0.6, 0.3, h / 2 - 1.2, S3)
        P.trait(x, gy, x, gy - 0.9, BR1)
    # La remise, puis la maison et sa fumée.
    maison(P, 20.5, float(f_pre(20.5)) + 0.5, p, grande=False)
    hx = 38.0
    gy = float(f_pre(hx)) + 0.6
    chx, chy = maison(P, hx, gy, p)
    fumee(P, chx, chy, p)
    # Le linge qui sèche : une corde entre deux piquets, quatre pièces qui se balancent.
    lx0, lx1, ly = hx + 6.5, hx + 17.5, gy - 3.4
    P.trait(lx0, gy + 0.2, lx0, ly, BR1)
    P.trait(lx1, float(f_pre(lx1)) + 0.4, lx1, ly + 0.2, BR1)
    for i in range(12):
        ua, ub = i / 12.0, (i + 1) / 12.0
        P.trait(lx0 + (lx1 - lx0) * ua, ly + 1.1 * math.sin(math.pi * ua), lx0 + (lx1 - lx0) * ub,
                ly + 1.1 * math.sin(math.pi * ub), M2)
    for i, (u, coul, l, h) in enumerate(((0.16, CREME, 1.6, 2.1), (0.38, O3, 1.3, 1.7), (0.6, BLEU, 1.7, 2.3),
                                         (0.82, CREME, 1.2, 1.5))):
        x, y = lx0 + (lx1 - lx0) * u, ly + 1.1 * math.sin(math.pi * u) + 0.2
        d = 0.45 * onde(p, 0.2 * i)
        P.poly([(x - l / 2, y), (x + l / 2, y), (x + l / 2 + d, y + h), (x - l / 2 + d, y + h)], coul)
        if P.hd:
            P.trait(x + l / 2 + d * 0.5 - 1.0 / P.s, y + 0.3, x + l / 2 + d - 1.0 / P.s, y + h - 0.2,
                    {CREME: M3, O3: O2, BLEU: D2}[coul])
    # Meules de foin sur le champ de blé, ombres longues vers la gauche.
    for i, x in enumerate((63.0, 70.5, 79.0, 86.5)):
        gy2 = float(f_pre(x)) + 2.0 + 0.5 * (i % 2)
        P.trait(x - 4.0, gy2, x - 0.5, gy2, S1, 1)
        P.ell(x, gy2 - 0.9, 1.5, 1.5, OR1, cond=P.Y < gy2 + 0.1)
        P.ell(x + 0.5, gy2 - 1.0, 0.9, 1.1, OR3, cond=P.Y < gy2 + 0.1)
        P.ell(x - 0.9, gy2 - 0.7, 0.5, 0.9, O2, cond=P.Y < gy2 + 0.1)
    # Moutons : cinq, dont un qui broute.
    for i, (x, dy) in enumerate(((100.5, 1.6), (104.5, 2.3), (111.0, 1.5), (114.0, 2.5), (122.5, 1.9))):
        y = float(f_pre(x)) + dy
        broute = i == 1 and onde(p) > 0
        P.ell(x, y - 0.75, 1.05, 0.7, CREME)
        if P.hd:
            P.ell(x - 0.2, y - 0.55, 0.8, 0.35, P3)
            P.trait(x - 0.5, y - 0.2, x - 0.5, y + 0.25, ENCRE)
            P.trait(x + 0.5, y - 0.2, x + 0.5, y + 0.25, ENCRE)
        P.point(x + 1.0, y - (0.35 if broute else 0.95), ENCRE, P.ep(0.45))
    # Clôture le long du chemin de la maison à la mare.
    x = 22.0
    while x < 60:
        y = float(f_pre(x)) + 1.9
        P.trait(x, y, x, y - 1.2, BR2)
        P.trait(x, y - 0.8, min(x + 2.6, 60), float(f_pre(min(x + 2.6, 60))) + 1.1, BR2)
        if P.hd:
            P.point(x, y - 1.2, M2)
        x += 2.6
    # ---- La rive d'en face : une bande sombre, des joncs.
    fr = f_rive(X)
    rive = (Y >= fr) & (Y < fr + 1.5 + 0.5 * np.sin(X / 3.1))
    P.rampe(rive, 0.3 + 0.5 * (fbm(X / 3.0, Y, 2, 95) - 0.5) + 0.2 * (Y - fr), [S1, S0, N2], 0.6)
    P.remplir(P.crete(rive) & (fbm(X / 6.0, Y * 0, 2, 96) > 0.56), OR1)
    n = int(120 * P.s * P.d)
    for i in range(n):
        x = -MARGE + (192 + 2 * MARGE) * hz(i, 1, 97)
        if 132 < x < 176 and hz(i, 4, 97) < 0.7:
            continue
        y = float(f_rive(x))
        h = 0.5 + 1.6 * hz(i, 2, 97) ** 2
        P.trait(x, y + 0.3, x + (hz(i, 3, 97) - 0.5) * 0.5, y - h, S0 if hz(i, 5, 97) < 0.7 else S1)
    return P.a


def table_reflets():
    """Chaque couleur de la palette → le ton d'eau qui la reflète (assombrie, tirée vers le bleu nuit)."""
    eau = np.array([rvb(PAL[i]) for i in EAU], dtype=float)
    fond = np.array(rvb(PAL[EAU[1]]), dtype=float)
    t = np.zeros(len(PAL), dtype=np.int16)
    for i, h in enumerate(PAL):
        r = np.array(rvb(h), dtype=float) * 0.74 + fond * 0.26
        t[i] = int(np.argmin(((eau - r) ** 2 * np.array([1.0, 1.2, 0.8])).sum(axis=1)))
    return t


def nenuphar(P, x, y, r, graine, fleur=None):
    ry = r * 0.36
    P.ell(x, y + 0.5, r * 0.98, ry, EAU[0])                                      # son ombre sur l'eau
    ang = 2 * math.pi * hz(graine, 1, 3)
    u, w = (P.X - x) / r, (P.Y - y) / ry
    a = np.arctan2(w, u)
    fente = np.abs(((a - ang + math.pi) % (2 * math.pi)) - math.pi) < 0.22
    m = (u * u + w * w <= 1) & ~fente
    P.rampe(m, 0.48 - 0.38 * w - 0.2 * u + 0.25 * (fbm(P.X * 1.3, P.Y * 2.0, 2, graine) - 0.5), [S1, S2, S3, S4], 0.6)
    bord = m & (u * u + w * w > (1 - 1.6 / (r * P.s)) ** 2) & (w < -0.1) & (u < 0.3)
    P.remplir(bord, OR2)                                                         # le bord qui prend le couchant
    if P.hd and r > 3:
        for k in range(5):
            b = ang + 0.6 + k * 1.15
            P.trait(x, y, x + r * 0.8 * math.cos(b), y + ry * 0.8 * math.sin(b), S2)
    if fleur is not None:
        fx, fy = x + r * 0.35, y - ry * 0.2
        t = max(0.5, 0.42 * r)
        if P.hd:
            for b in range(5):
                P.ell(fx + t * 0.9 * math.cos(b * 1.26 + 0.3), fy - t * 0.3 + t * 0.45 * math.sin(b * 1.26 + 0.3), t * 0.5,
                      t * 0.36, fleur)
            P.ell(fx, fy - t * 0.45, t * 0.5, t * 0.45, CREME if fleur != CREME else SOL)
            P.point(fx, fy - t * 0.45, OR2)
        else:
            P.point(fx, fy - 0.5, fleur)
            P.point(fx, fy - 1.5 / P.s - 0.5, OR2)


def grenouille(P, x, y, p):
    k = 1.0
    cligne = 0.80 < p < 0.92
    P.ell(x, y, 2.7 * k, 2.0 * k, S2)
    P.ell(x + 0.2, y - 0.3, 2.3 * k, 1.6 * k, S3)
    P.ell(x, y + 0.8, 1.7 * k, 1.1 * k, CREME)
    P.ell(x - 2.4, y + 1.3, 1.1, 0.7, S2)
    P.ell(x + 2.4, y + 1.3, 1.1, 0.7, S2)
    for cote in (-1, 1):
        ex, ey = x + cote * 1.35, y - 1.9
        P.ell(ex, ey, 1.05, 1.05, S3)
        if cligne:
            P.trait(ex - 0.6, ey, ex + 0.6, ey, S1)
        else:
            P.ell(ex, ey, 0.7, 0.7, CREME)
            P.ell(ex + 0.15, ey + 0.05, 0.38, 0.45, ENCRE)
            if P.thd:
                P.point(ex - 0.2, ey - 0.3, BLANC)
    P.trait(x - 1.2, y - 0.2, x + 1.2, y - 0.2, S1)
    if P.hd:
        P.point(x - 1.4, y - 0.4, S1)
        P.point(x + 1.3, y - 0.4, S1)
        for (dx, dy) in ((-1.5, -1.0), (0.9, -1.2), (1.8, 0.2)):
            P.point(x + dx, y + dy, S4)
        P.trait(x - 1.9, y - 1.3, x - 0.8, y - 2.9, S4)                          # liseré du couchant sur le dos


def barque(P, x, y, p):
    y = y + 0.25 * onde(p, 0.1)
    P.poly([(x - 6.2, y - 1.1), (x + 6.6, y - 1.3), (x + 5.0, y + 1.0), (x - 4.8, y + 1.0)], BR1)
    P.poly([(x - 5.6, y - 0.9), (x + 5.9, y - 1.1), (x + 4.8, y + 0.3), (x - 4.6, y + 0.3)], BR2)
    P.trait(x - 6.2, y - 1.2, x + 6.6, y - 1.4, M2)
    P.trait(x - 6.2, y - 1.2, x - 3.0, y - 1.25, OR2)
    P.rect(x - 1.0, y - 1.0, 2.0, 0.6, M3)
    P.trait(x + 2.0, y - 1.6, x + 8.5, y + 0.6, M2)                              # la rame, posée
    if P.hd:
        P.ell(x + 8.6, y + 0.7, 0.9, 0.4, M3)
        P.trait(x - 4.6, y + 0.3, x + 4.8, y + 0.3, BR1)
    P.trait(x - 6.2, y - 1.0, x - 9.6, y - 2.0, M3)                              # l'amarre
    P.rect(x - 10.2, y - 3.4, 0.9, 4.6, BR1)
    P.point(x - 10.2, y - 3.4, OR2)
    # Reflet : des tirets sombres sous la coque.
    for i in range(4):
        d = 0.5 * onde(p, 0.25 * i)
        P.trait(x - 4.6 + i * 0.6 + d, y + 1.3 + i * 0.6, x + 4.6 - i * 0.9 + d, y + 1.3 + i * 0.6, EAU[0])


def eau(P, derriere):
    """La mare : le miroir de tout ce qui est derrière (ciel, nuages, lointains, prés, colline), brisé par les rides,
    puis le chemin de lumière du soleil, les nénuphars, la grenouille, la barque."""
    p = P.p
    X, Y = P.X, P.Y
    axe = 47.4
    lut = table_reflets()
    ys = P.YI.astype(float)
    Yw = Y
    src_y = np.clip(np.floor((axe - (Yw - axe) * 1.28 - P.y0) * P.s), 0, P.H - 1).astype(np.int64)
    amp = (0.25 + 0.06 * (Yw - axe)) * P.s * (1.0 if P.hd else 0.6)
    dec = np.round(amp * np.sin(Yw * 2.3 + 2 * math.pi * p + 0.6 * np.sin(X / 9.0))).astype(np.int64)
    # Une rangée sur deux, le reflet s'étire en tirets horizontaux (l'eau plate ne rend pas les détails).
    q = P.ep(0.9)
    xq = np.where((P.YI // max(1, P.ep(0.5))) % 2 == 0, (P.XI // q) * q, P.XI)
    src_x = np.clip(xq + dec, 0, P.Wt - 1)
    e = lut[derriere[src_y, src_x]].astype(float)
    # Profondeur : l'eau fonce vers nous et dans les coins ; elle garde le ciel au milieu.
    e = e - 2.6 * np.clip((Yw - 56) / 17.0, 0, 1) ** 1.4 - 1.2 * np.clip((np.abs(X - 100) - 62) / 30.0, 0, 1)
    e = e + 0.9 * P.d * (fbm(X / 14.0, Yw / 1.6, 3, 120) - 0.5)
    # Le chemin de lumière sous le soleil : des éclats qui scintillent, de plus en plus larges vers nous.
    dl = P.ep(1.5)
    cell = (P.XI + (P.YI % 3) * 2) // dl
    h1 = hz(cell, P.YI, 121)
    large = np.maximum(2.2 + (Yw - axe) * 0.55, 0.5)
    force = np.exp(-((X - SOLEIL[0] - 0.6 * np.sin(Yw * 0.7)) / large) ** 2)
    temps = np.floor(((p + hz(cell, P.YI, 122)) % 1.0) * 4)
    eclat = (h1 < 0.78 * force) & (temps < 2) & (Yw > axe + 0.6)
    e = np.where(eclat, np.maximum(e, 8) + 1.6 + 1.6 * force, e)
    # Rides : de petits tirets un ton plus clair, partout.
    h2 = hz(cell, P.YI, 123)
    ride = (h2 < 0.05 * P.d) & (np.floor(((p + hz(cell, P.YI, 124)) % 1.0) * 4) < 2)
    e = np.where(ride, e + 1.5, e)
    # Ronds dans l'eau (deux, décalés).
    for (rx0, ry0, d) in ((80.0, 66.5, 0.0), (121.0, 56.5, 0.45), (146.0, 64.0, 0.7)):
        age = (p + d) % 1.0
        r = 1.0 + 5.5 * age
        dd = np.hypot((X - rx0), (Yw - ry0) * 2.8)
        anneau = (np.abs(dd - r) < 0.8 / P.s + 0.12) & (P.T > age * 0.9)
        e = np.where(anneau, e + 2.2, e)
    eau_m = Yw >= axe - 0.6
    idx = np.clip(np.floor(e + 0.5 + (P.T - 0.5) * P.tr), 0, len(EAU) - 1).astype(np.int64)
    eclats_vifs = eclat & (force > 0.55) & (h1 < 0.3)
    P.neuf()
    P.a[eau_m] = np.asarray(EAU, dtype=np.int16)[idx][eau_m]
    P.remplir(eau_m & eclats_vifs, SOL)
    # ---- Ce qui flotte.
    barque(P, 163.0, 51.6, p)
    petits = [(31, 55.5, 2.2, VIOLET), (37, 58.6, 1.6, None), (25.5, 59.8, 2.6, CREME), (44, 54.2, 1.4, None),
              (20, 63.5, 1.9, None), (152, 58.8, 2.4, CREME), (160, 62.4, 1.7, None), (168, 59.5, 2.1, VIOLET),
              (174, 64.0, 1.5, None), (143, 67.4, 2.0, None), (52, 68.6, 2.3, VIOLET), (112, 68.5, 1.6, None),
              (78, 53.0, 1.3, None), (103, 51.6, 1.1, None), (131, 52.3, 1.2, CREME)]
    for i, (x, y, r, fl) in enumerate(petits):
        nenuphar(P, x, y + 0.12 * onde(p, 0.13 * i), r, 200 + i, fl)
    for i, x in enumerate((62.0, 96.0, 130.0)):                                  # les trois nénuphars de l'histoire
        nenuphar(P, x, 61.0 + (i % 2) * 1.2, 7.4, 300 + i, CREME if i == 2 else None)
    grenouille(P, 96.0, 60.0, p)
    # Une libellule au-dessus de l'eau : corps bleu, ailes qui battent.
    lx, ly = 119.0 + 0.5 * onde(p), 53.4 + 0.3 * onde(p, 0.25)
    P.trait(lx - 1.6, ly, lx + 1.6, ly, D2, P.ep(0.35))
    P.point(lx + 1.7, ly, BLEU)
    haut = int(p * IMAGES) % 2 == 0
    for cote in (-1, 1):
        P.trait(lx + 0.2, ly, lx + 0.2 + cote * 0.4, ly - (1.5 if haut else 0.7), CREME)
        P.trait(lx - 0.5, ly, lx - 0.5 + cote * 0.3, ly + (0.3 if haut else 1.1), SOL)
    # Pierres du bord, près de nous.
    for (x, y, r) in ((39.0, 69.6, 2.0), (45.5, 71.0, 1.4), (151.0, 70.2, 1.8), (157.0, 71.6, 1.2), (99.0, 73.4, 1.6)):
        P.ell(x, y + 0.5, r * 1.15, r * 0.4, EAU[0])
        P.ell(x, y, r, r * 0.62, P1, cond=P.Y < y + 0.35)
        P.ell(x - r * 0.25, y - r * 0.22, r * 0.55, r * 0.3, P3, cond=P.Y < y + 0.35)
        P.point(x - r * 0.5, y - r * 0.45, OR2)
    return P.a


# ---------------------------------------------------------------------------------------------------------------
# Le premier plan : la berge où l'on marche, l'arbre et sa lanterne, les roseaux, le panneau, les lucioles
# ---------------------------------------------------------------------------------------------------------------
def haut_feuillage(x):
    x = np.asarray(x, dtype=float)
    return 13.0 - 0.33 * x + 2.6 * np.sin(x / 6.0) + 1.2 * np.sin(x / 2.3 + 1.0)


def tampon_feuille(P, g):
    """Une petite feuille en pixels (liste de décalages), selon la finesse de la grille."""
    o = int(hz(g, 5, 7) * 4)
    if P.thd:
        formes = [[(0, 0), (1, 0), (2, 0), (3, 0), (1, -1), (2, -1), (1, 1), (2, 1), (4, 0)],
                  [(0, 0), (0, 1), (0, 2), (0, 3), (-1, 1), (-1, 2), (1, 1), (1, 2), (0, 4)],
                  [(0, 0), (1, 1), (2, 2), (3, 3), (1, 0), (2, 1), (3, 2), (0, 1), (1, 2)],
                  [(0, 0), (1, -1), (2, -2), (3, -3), (1, 0), (2, -1), (3, -2), (0, -1), (1, -2)]]
    elif P.hd:
        formes = [[(0, 0), (1, 0), (2, 0), (1, -1)], [(0, 0), (0, 1), (0, 2), (1, 1)], [(0, 0), (1, 1), (2, 2), (1, 0)],
                  [(0, 0), (1, -1), (2, -2), (1, 0)]]
    else:
        formes = [[(0, 0), (1, 0)], [(0, 0), (0, 1)], [(0, 0), (1, 1)], [(0, 0), (1, -1)]]
    return formes[o]


def premier_plan(P):
    P.neuf()
    p = P.p
    X, Y = P.X, P.Y
    fb = f_berge(X)
    berge = Y >= fb
    prof = Y - fb
    # La terre : sombre, un rien plus claire là où l'on marche ; le bord qui regarde l'eau prend la lumière.
    v = 0.3 + 0.5 * (fbm(X / 6.0, Y / 2.0, 3, 130) - 0.5) + 0.42 * np.exp(-prof / 1.3) \
        + 0.16 * np.exp(-((Y - 77.6) / 1.6) ** 2)
    P.rampe(berge, v, [N0, N1, N2, S1, S2], 0.8)
    bord = P.crete(berge)
    P.remplir(bord, S2)
    P.remplir(bord & (fbm(X / 7.0, Y * 0, 2, 131) > 0.6), OR1)
    # Cailloux du chemin.
    n = int(46 * P.s * P.d)
    for i in range(n):
        x, y = -MARGE + (192 + 2 * MARGE) * hz(i, 1, 132), 75.6 + 4.0 * hz(i, 2, 132)
        if y > float(f_berge(x)) + 1.5:
            P.point(x, y, N2 if hz(i, 3, 132) < 0.6 else P1)
            if P.hd and hz(i, 3, 132) > 0.8:
                P.point(x + 1.0 / P.s, y, P1)
    # Touffes d'herbe : sur le bord (hautes, elles se balancent) et sur la berge (rases).
    n = int(210 * P.s * P.d)
    for i in range(n):
        x = -MARGE + (192 + 2 * MARGE) * hz(i, 1, 133)
        sur_bord = hz(i, 2, 133) < 0.62
        y = float(f_berge(x)) + (0.4 + 0.6 * hz(i, 3, 133) if sur_bord else 1.2 + 6.5 * hz(i, 3, 133))
        if y > 79.8:
            continue
        h = (1.2 + 3.6 * hz(i, 4, 133) ** 2) if sur_bord else (0.5 + 1.1 * hz(i, 4, 133))
        penche = (hz(i, 5, 133) - 0.5) * 1.6
        vent = 0.5 * h / 4.0 * onde(p, x / 37.0)
        t = hz(i, 6, 133)
        coul = OR2 if t > 0.9 else (OR1 if t > 0.8 else (S2 if t > 0.55 else (S1 if t > 0.28 else N1)))
        if not sur_bord and coul in (OR1, OR2):
            coul = S2
        P.trait(x, y, x + penche * 0.5 + vent * 0.4, y - h * 0.55, coul)
        P.trait(x + penche * 0.5 + vent * 0.4, y - h * 0.55, x + penche + vent, y - h, coul)
    # Fleurs : marguerites crème, coquelicots orange, clochettes violettes.
    n = int(15 * P.s ** 0.6)
    for i in range(int((n + 6) * (1.0 if P.hd else 0.6))):
        x = 10 + 172 * hz(i, 1, 134)
        y = float(f_berge(x)) + 0.9 + 4.6 * hz(i, 2, 134)
        if y > 79 or 13 < x < 31 or 158 < x < 178:
            continue                                                             # on laisse libre la place des personnages
        h = 1.4 + 1.6 * hz(i, 3, 134)
        d = 0.25 * onde(p, x / 23.0)
        sorte = int(hz(i, 4, 134) * 3)
        P.trait(x, y, x + d, y - h, S2)
        coul = (CREME, O3, VIOLET)[sorte]
        if P.hd:
            for (ax, ay) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                P.point(x + d + ax / P.s, y - h + ay / P.s, coul)
            P.point(x + d, y - h, OR2 if sorte == 0 else (ENCRE if sorte == 1 else CREME))
            if P.thd:
                P.point(x + d + 1 / P.s, y - h * 0.5, S3)
        else:
            P.point(x + d, y - h, coul)
    # Champignons au pied de l'arbre.
    for (x, y, r) in ((10.6, 77.4, 1.2), (12.6, 78.3, 0.8)):
        P.rect(x - 0.3, y - 0.9, 0.7, 1.0, CREME)
        P.ell(x, y - 1.1, r, r * 0.75, O2, cond=P.Y < y - 0.8)
        P.ell(x - r * 0.2, y - 1.3, r * 0.6, r * 0.35, O3, cond=P.Y < y - 0.8)
        P.point(x - r * 0.3, y - 1.5, CREME)
        if P.hd:
            P.point(x + r * 0.4, y - 1.3, CREME)
    # ---- L'arbre du premier plan, à gauche : tronc à contre-jour, écorce, liseré orange côté soleil.
    def bord_tronc(y):
        y = np.asarray(y, dtype=float)
        return 6.4 + 1.4 * np.sin((y - 20) / 21.0) + 1.6 * np.exp(-((y - 80) / 5.0) ** 2) + 0.4 * np.sin(y / 3.1)

    tronc = X < bord_tronc(Y)
    P.rampe(tronc, 0.25 + 0.55 * (fbm(X / 1.3, Y / 9.0, 3, 140) - 0.5) + 0.07 * (X - 2), [N0, N1, N2], 0.7)
    lis = tronc & (X > bord_tronc(Y) - 1.2 / P.s - 0.25)
    P.remplir(lis & (fbm(X * 0, Y / 6.0, 2, 141) > 0.5), O2)
    P.remplir(lis & (X > bord_tronc(Y) - 1.0 / P.s) & (fbm(X * 0, Y / 6.0, 2, 141) > 0.62), O3)
    if P.hd:                                                                     # un nœud dans l'écorce
        P.ell(2.6, 52.0, 1.3, 2.0, N0)
        P.ell(2.6, 52.0, 0.7, 1.2, N1)
    # Racine qui court vers la droite.
    P.courbe([(5.5, 76.5), (9.5, 77.6), (14.0, 79.2), (17.0, 80.5)], N1, P.ep(1.0), 1)
    # Branche maîtresse, puis le feuillage : une masse sombre trouée de ciel, et des feuilles une à une sur le bord.
    P.courbe([(5.0, 19.0), (16.0, 12.5), (30.0, 9.5), (44.0, 7.0), (58.0, 1.5)], N0, P.ep(1.8), 1)
    P.courbe([(18.0, 12.0), (24.0, 14.5), (29.0, 18.0)], N0, P.ep(0.8), 1)
    hf = haut_feuillage(X)
    dedans = hf - Y
    masse = (dedans > 1.6 + 2.6 * (fbm(X / 3.5, Y / 3.0, 3, 142) - 0.5)) & (X < 78)
    trou = (fbm(X / 2.6, Y / 2.2, 3, 143) > 0.66) & (dedans < 7) & (dedans > 0.8)
    P.rampe(masse & ~trou, 0.3 + 0.9 * (fbm(X / 2.0, Y / 2.0, 3, 144) - 0.5) + 0.05 * np.clip(6 - dedans, 0, 6),
            [N0, N1, N2, S1], 0.9)
    n = int(520 * P.s * P.s)
    xs = -MARGE + (84 + MARGE) * hz(np.arange(n), 1, 145)
    ys = P.y0 - 2 + (22 - P.y0) * hz(np.arange(n), 2, 145)
    ordre = np.argsort(haut_feuillage(xs) - ys)[::-1]                            # le dedans d'abord, le bord à la fin
    for i in ordre:
        x, y = float(xs[i]), float(ys[i])
        d = float(haut_feuillage(x)) - y
        if d < -1.4 or d > 9 or (d > 3.5 and hz(i, 3, 145) < 0.6):
            continue
        t = hz(i, 4, 145)
        if d < 1.6:
            coul = O3 if t > 0.86 else (O2 if t > 0.7 else (OR1 if t > 0.62 else (S2 if t > 0.34 else S1)))
            x += 0.3 * onde(p, x / 11.0)
            y += 0.15 * onde(p, 0.25 + x / 7.0)
        elif d < 3.5:
            coul = S2 if t > 0.82 else (S1 if t > 0.4 else N2)
        else:
            coul = S1 if t > 0.7 else N2
        X0, Y0 = P.px(x), P.py(y)
        for (ax, ay) in tampon_feuille(P, i):
            P.bloc(X0 + ax, Y0 + ay, coul)
    # La lanterne pendue à la branche : elle se balance, sa flamme vacille.
    bal = 0.45 * onde(p, 0.1)
    ax, ay = 27.5, 18.0
    lx, ly = ax + bal, ay + 4.4
    P.trait(ax, ay - 2.5, lx, ly - 1.4, N0)
    if P.hd:                                                                     # halo tramé autour de la flamme
        d = np.hypot(X - lx, (Y - ly) * 1.1)
        P.remplir((d < 3.4) & (P.T < 0.34 - d * 0.1) & (P.a < 0), LUM)
    P.rect(lx - 1.0, ly - 1.4, 2.0, 0.6, N0)
    P.rect(lx - 0.8, ly - 0.8, 1.6, 2.2, LUM if int(p * IMAGES) % 3 else LUM2)
    P.rect(lx - 0.3, ly - 0.3, 0.6, 1.2, LUM2 if int(p * IMAGES) % 3 else BLANC)
    P.rect(lx - 1.0, ly + 1.3, 2.0, 0.5, N0)
    P.trait(lx - 1.0, ly - 0.9, lx - 1.0, ly + 1.4, N0)
    P.trait(lx + 0.95, ly - 0.9, lx + 0.95, ly + 1.4, BR1)
    # ---- À droite : roseaux et quenouilles, le panneau qui montre la colline.
    px_, py_ = 187.0, 62.0
    P.rect(px_ - 0.7, py_, 1.5, 19.0, BR1)
    P.rect(px_ - 0.7, py_, max(1.0 / P.s, 0.4), 19.0, M2)
    fleche = [(px_ - 8.0, py_ + 1.0), (px_ + 4.0, py_ + 0.4), (px_ + 4.2, py_ + 4.6), (px_ - 7.8, py_ + 5.2),
              (px_ - 10.4, py_ + 3.3)]
    mf = P.poly(fleche, BR2)
    P.remplir(P.crete(mf), M2)
    P.remplir(mf & (np.abs(P.Y - (py_ + 5.0 - (P.X - px_) * 0.05)) < 0.5 / P.s + 0.1), BR1)
    # Le dessin gravé : une colline, son arbre, un soleil (pas de texte : Pilou ne sait pas encore tout écrire).
    P.ell(px_ - 2.4, py_ + 4.0, 2.6, 1.9, M3, cond=(P.Y < py_ + 4.0) & mf)
    P.trait(px_ - 2.4, py_ + 2.2, px_ - 2.4, py_ + 1.4, M3)
    P.point(px_ + 1.8, py_ + 1.6, OR2, P.ep(0.5))
    n = int(13 * P.s ** 0.7)
    for i in range(n):
        x0 = 173.5 + 23 * hz(i, 1, 150)
        if abs(x0 - px_) < 1.2:
            continue
        h = 13 + 19 * hz(i, 2, 150)
        penche = -1.5 - 3.5 * hz(i, 3, 150) + 0.8 * onde(p, 0.07 * i)
        coul = (N0, N1, S1, N1)[i % 4]
        pts = [(x0, 81.0), (x0 + penche * 0.25, 81 - h * 0.5), (x0 + penche, 81 - h)]
        P.courbe(pts, coul, P.ep(0.4), 1)
        if hz(i, 4, 150) < 0.55:                                                 # une quenouille
            qx, qy = x0 + penche * 0.8, 81 - h * 0.86
            P.ell(qx, qy, 0.75, 2.1, BR1)
            P.ell(qx - 0.3, qy - 0.2, 0.3, 1.5, BR2)
            if P.hd:
                P.trait(qx - 0.7, qy - 1.2, qx - 0.7, qy + 0.9, O2)
        else:                                                                    # une longue feuille
            P.courbe([(x0 + 0.4, 81.0), (x0 + 1.5 + penche * 0.3, 81 - h * 0.45), (x0 + 3.5 + penche, 81 - h * 0.6)],
                     coul, P.ep(0.5), 1)
    # ---- Lucioles : dans les coins sombres, elles s'allument et s'éteignent chacune à son rythme.
    lucioles = [(11.5, 68.0), (20.0, 73.6), (9.0, 48.0), (15.0, 31.0), (56.0, 76.4), (74.0, 78.2), (118.0, 77.0),
                (141.0, 75.4), (163.0, 74.2), (179.5, 56.0), (184.0, 45.0), (176.0, 69.0), (34.0, 24.0), (47.0, 15.5),
                (88.0, 75.2), (6.0, 60.0)]
    for i, (x, y) in enumerate(lucioles):
        ph = (p + hz(i, 0, 160)) % 1.0
        if ph > 0.5:
            continue
        x, y = x + 0.5 * onde(p, hz(i, 1, 160)), y + 0.4 * onde(p, 0.25 + hz(i, 2, 160))
        if P.hd and 0.1 < ph < 0.4:
            for (ax, ay) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                P.bloc(P.px(x) + ax * P.ep(0.4), P.py(y) + ay * P.ep(0.4), OR1, P.ep(0.4))
        P.point(x, y, LUM2 if 0.1 < ph < 0.4 else LUM, P.ep(0.4))
    return P.a


# ---------------------------------------------------------------------------------------------------------------
# Composition des plans, parallaxe
# ---------------------------------------------------------------------------------------------------------------
PLANS = ("ciel", "nuages", "lointains", "moyen", "premier")
PARALLAXE = {"ciel": 0.0, "nuages": 0.08, "lointains": 0.2, "moyen": 0.5, "premier": 1.0}


def plans(fmt, phase):
    """Les cinq plans d'une image de la boucle : {nom: grille de numéros de couleur, -1 = vide}."""
    P = Peintre(fmt, phase)
    r = {"ciel": ciel(P).copy(), "nuages": nuages(P).copy(), "lointains": lointains(P).copy()}
    haut = moyen(P).copy()
    derriere = r["ciel"].copy()
    for nom in ("nuages", "lointains"):
        derriere = np.where(r[nom] >= 0, r[nom], derriere)
    derriere = np.where(haut >= 0, haut, derriere)
    mare = eau(P, derriere).copy()
    r["moyen"] = np.where(haut >= 0, haut, mare)
    r["premier"] = premier_plan(P).copy()
    return P, r


def composer(P, r, camera=0.0):
    """L'image vue : les plans posés du fond vers nous, chacun décalé selon sa profondeur (camera en unités)."""
    out = None
    for nom in PLANS:
        d = int(round(camera * PARALLAXE[nom] * P.s))
        vue = r[nom][:, P.M + d:P.M + d + P.W]
        out = vue.copy() if out is None else np.where(vue >= 0, vue, out)
    assert (out >= 0).all(), "pixel vide (un décor est opaque)"
    return out


def en_image(idx, k=1):
    pal = np.array([rvb(h) for h in PAL], dtype=np.uint8)
    im = Image.fromarray(pal[idx], "RGB")
    return im.resize((im.width * k, im.height * k), Image.NEAREST) if k != 1 else im


def boucle(fmt, camera=None):
    """Les images de la boucle (numéros de couleur). camera : fonction phase → décalage, pour montrer la parallaxe."""
    ims = []
    for i in range(IMAGES):
        P, r = plans(fmt, i / IMAGES)
        ims.append(composer(P, r, camera(i / IMAGES) if camera else 0.0))
    return ims


def poids_texte(ims):
    """Poids du décor dans le format texte des sprites (une lettre par pixel, une ligne par rangée), brut et gzip."""
    import gzip
    couleurs = sorted({int(v) for im in ims for v in np.unique(im)})
    lettres = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    assert len(couleurs) <= len(lettres), "%d couleurs : le format texte en porte 62" % len(couleurs)
    lettre = {v: lettres[i] for i, v in enumerate(couleurs)}
    lignes = ["palette: " + " ".join("%s=%s" % (lettre[v], PAL[v]) for v in couleurs), "images:"]
    for k, im in enumerate(ims):
        if k:
            lignes.append("---")
        lignes += ["".join(lettre[int(v)] for v in rang) for rang in im]
    brut = ("\n".join(lignes) + "\n").encode("utf-8")
    return len(brut), len(gzip.compress(brut, 9)), len(couleurs)


def ecrire_gif(chemin, images, duree):
    images[0].save(chemin, save_all=True, append_images=images[1:], duration=duree, loop=0, optimize=False)


# ---------------------------------------------------------------------------------------------------------------
# Montages : la scène avec Pilou et un personnage en pied, dans la fenêtre du PC et sur l'écran du téléphone
# ---------------------------------------------------------------------------------------------------------------
SOL_Y, PLACE, INTERLOCUTEUR = 78.6, 24.0, 165.0
GABARITS = os.path.normpath(os.path.join(ICI, "..", "..", "docs", "maquettes", "paysages", "gabarits"))


def _rogner(im):
    return im.crop(im.getbbox())


def personnages(fmt):
    """(Pilou, personnage) à l'unité de la définition : images RGBA, un pixel par unité.
    A : le mini-Pilou de scène et le personnage en pied d'aujourd'hui (dessinés à l'unité de 5 px).
    B : le Pilou du bureau 48 × 56 et le portrait fin 64 × 64 du personnage, déjà dessinés.
    C : le Pilou fin 96 × 112 ; le personnage n'existe pas à cette unité (on montre le portrait fin, trop petit).
    D : tout ce qui existe à l'unité d'aujourd'hui, doublé (agrandissement automatique ou dessin fin déjà fait)."""
    import planches
    import rendu
    fins = rendu._dossier("sprites2x")
    if fmt == "A":
        pilou = planches.sprite_image(fins["scene-pilou"], 1, 0)
        perso = planches.sprite_image(fins["pied-grande-panne-grumeau"], 1, 0)
    elif fmt == "D":
        # Le double exact : le mini-Pilou de scène agrandi par la règle commune (MMPX), le portrait fin du personnage.
        pilou = planches.sprite_image(rendu.agrandir(fins["scene-pilou"]), 1, 0)
        perso = planches.sprite_image(fins["portrait-grande-panne-grumeau"], 1, 0)
    else:
        B = rendu.banque()
        g = rendu.rendre(rendu.Pose(expr="joie"), B, rendu.teintes(), rendu.tenues(), 1 if fmt == "B" else 2)
        pilou = planches.grille_image(g, 1)
        perso = planches.sprite_image(fins["portrait-grande-panne-grumeau"], 1, 0)
    return _rogner(pilou), _rogner(perso)


def scene(fmt, idx):
    """Le décor à sa taille d'écran (960 px de large), Pilou à sa place, le personnage à la sienne."""
    W, H, k = FORMATS[fmt]
    s = W / 192.0
    im = en_image(idx, k).convert("RGBA")
    pilou, perso = personnages(fmt)
    sol = int(round((SOL_Y - (80 - H / s)) * s))
    for spr, x in ((pilou, PLACE), (perso, INTERLOCUTEUR)):
        g = spr.resize((spr.width * k, spr.height * k), Image.NEAREST)
        im.alpha_composite(g, ((int(round(x * s)) - spr.width // 2) * k, sol * k - g.height))
    return im.convert("RGB")


def montage_pc(fmt, idx):
    """La fenêtre Aventure du PC à 100 % (gabarit : capture réelle, scène de 960 × 400). Une scène plus haute
    allonge la fenêtre d'autant ; l'étiquette du lieu et les boutons sont repris du gabarit."""
    g = Image.open(os.path.join(GABARITS, "pc-fenetre-100.png")).convert("RGB")
    sc = scene(fmt, idx)
    x0, y0, bas = 22, 136, 532
    large = sc.width - 960
    if large > 0:
        # Fenêtre élargie : on étire le gabarit dans une colonne vide (500 au-dessus de la scène, 700 dans la boîte).
        g2 = Image.new("RGB", (g.width + large, g.height))
        for (ya, yb, col) in ((0, bas, 500), (bas, g.height, 700)):
            g2.paste(g.crop((0, ya, col, yb)), (0, ya))
            g2.paste(g.crop((col, ya, col + 1, yb)).resize((large, yb - ya)), (col, ya))
            g2.paste(g.crop((col, ya, g.width, yb)), (col + large, ya))
        g = g2
    plus = sc.height - 400
    out = Image.new("RGB", (g.width, g.height + plus))
    out.paste(g.crop((0, 0, g.width, y0)), (0, 0))
    cote = g.crop((0, 300, g.width, 301)).resize((g.width, sc.height))
    out.paste(cote, (0, y0))
    out.paste(sc, (x0, y0))
    out.paste(g.crop((0, bas, g.width, g.height)), (0, bas + plus))
    # Étiquette « LA MARE » (coins en escalier de 5 px) et boutons « Relire », « De côté… ».
    for (a, b, c2, d, coin) in ((24, 144, 137, 192, 5), (824 + max(0, large), 144, 892 + max(0, large), 173, 2),
                                (897 + max(0, large), 144, 980 + max(0, large), 173, 2)):
        bout = g.crop((a, b, c2, d)).convert("RGBA")
        px = bout.load()
        for (cx, cy) in ((0, 0), (bout.width - coin, 0), (0, bout.height - coin), (bout.width - coin, bout.height - coin)):
            for j in range(coin):
                for i in range(coin):
                    r, v, bl, _ = px[cx + i, cy + j]
                    if coin == 5 or (r > 150 and bl > 200):          # un bout de l'ancien ciel dans le coin
                        px[cx + i, cy + j] = (0, 0, 0, 0)
        out.paste(bout, (a, b), bout)
    return out


def montage_telephone(fmt, idx):
    """L'écran Aventure d'un téléphone de 1078 × 2400 (gabarit : capture Robolectric 1236 × 2745 du même écran,
    ramenée à 1078 de large ; son habillage est donc légèrement adouci, la scène, elle, est au pixel près)."""
    import police
    g = Image.open(os.path.join(GABARITS, "telephone-robolectric-1236x2745.png")).convert("RGB")
    r = 1078 / g.width
    t = g.resize((1078, int(round(g.height * r))), Image.LANCZOS)
    out = Image.new("RGB", (1078, 2400), t.getpixel((5, t.height - 3)))
    out.paste(t, (0, 0))
    sc = scene(fmt, idx)
    if sc.width > 1078:                                                 # cadrage : on perd (largeur - 1078) / 2 par bord
        g0 = (sc.width - 1078) // 2
        sc = sc.crop((g0, 0, g0 + 1078, sc.height))
    haut = int(round(332 * r))
    libre = int(round(1240 * r))                                        # le fil commence plus bas
    d = ImageDraw.Draw(out)
    d.rectangle([0, haut - 2, 1078, libre], fill=(23, 25, 41))
    d.rectangle([0, haut, 1078, haut + sc.height - 1], fill=(10, 13, 26))
    x0 = (1078 - sc.width) // 2
    out.paste(sc, (x0, haut))
    # Le pointillé de progression, sous la scène.
    ligne = t.crop((0, int(round(820 * r)), 1078, int(round(834 * r))))
    out.paste(ligne, (0, haut + sc.height + 10))
    # L'étiquette du lieu, au cadre pixel (unité de 5 px), police de Pilou à 4 px le pixel.
    pts = police.dessiner(["La mare"], police.police_texte())
    lw = (max(x for x, _ in pts) + 1) * 4
    bx, by, bw, bh = x0 + 10, haut + 10, lw + 40, 80
    d.rectangle([bx + 5, by, bx + bw - 6, by + bh - 1], fill=(106, 90, 205))
    d.rectangle([bx, by + 5, bx + bw - 1, by + bh - 6], fill=(106, 90, 205))
    d.rectangle([bx + 5, by + 5, bx + bw - 6, by + bh - 6], fill=(21, 26, 46))
    for (x, y) in pts:
        d.rectangle([bx + 20 + x * 4, by + 16 + y * 4, bx + 23 + x * 4, by + 19 + y * 4], fill=(230, 236, 242))
    return out


def actuel(dossier):
    """Le décor en service aujourd'hui (assets/sprites2x/decor-prologue-mare), tel quel, pour comparer."""
    import planches
    import rendu
    fins = rendu._dossier("sprites2x")
    dec = fins["decor-prologue-mare"]
    ims = [planches.sprite_image(dec, 5, i).convert("RGB") for i in range(len(dec.images))]
    ims[0].save(os.path.join(dossier, "actuel-decor.png"))
    ecrire_gif(os.path.join(dossier, "actuel-decor.gif"), ims, dec.duree)
    # Les mêmes montages, avec le décor actuel.
    global scene
    vraie = scene

    def scene_actuelle(fmt, idx):
        im = ims[0].convert("RGBA")
        pilou, perso = personnages("A")
        for spr, x in ((pilou, PLACE), (perso, INTERLOCUTEUR)):
            g = spr.resize((spr.width * 5, spr.height * 5), Image.NEAREST)
            im.alpha_composite(g, ((int(round(x)) - spr.width // 2) * 5, 79 * 5 - g.height))
        return im.convert("RGB")

    scene = scene_actuelle
    try:
        scene_actuelle("A", None).save(os.path.join(dossier, "actuel-scene.png"))
        montage_pc("A", None).save(os.path.join(dossier, "actuel-pc.png"))
        montage_telephone("A", None).save(os.path.join(dossier, "actuel-telephone.png"))
    finally:
        scene = vraie
    chemin = os.path.join(rendu.ASSETS, "sprites2x", "decor-prologue-mare.txt")
    return os.path.getsize(chemin), len(dec.images), dec.duree


def main():
    dossier = sys.argv[1] if len(sys.argv) > 1 else os.path.normpath(os.path.join(ICI, "..", "..", "docs", "maquettes",
                                                                                 "paysages"))
    seuls = sys.argv[2] if len(sys.argv) > 2 else "ABCD"
    os.makedirs(dossier, exist_ok=True)
    mesures = {}
    for fmt in seuls:
        W, H, k = FORMATS[fmt]
        ims = boucle(fmt)
        brut, gz, n = poids_texte(ims)
        mesures[fmt] = (W, H, k, brut, gz, n)
        vues = [en_image(im, k) for im in ims]
        vues[0].save(os.path.join(dossier, "%s-decor.png" % fmt))
        en_image(ims[0]).save(os.path.join(dossier, "%s-decor-1x.png" % fmt))
        ecrire_gif(os.path.join(dossier, "%s-decor.gif" % fmt), vues, DUREE)
        # La parallaxe : la caméra glisse de ±3 unités, les plans suivent chacun à sa vitesse.
        pano = [en_image(im, k) for im in boucle(fmt, lambda p: 3.0 * onde(p))]
        ecrire_gif(os.path.join(dossier, "%s-parallaxe.gif" % fmt), pano, DUREE)
        scene(fmt, ims[0]).save(os.path.join(dossier, "%s-scene.png" % fmt))
        montage_pc(fmt, ims[0]).save(os.path.join(dossier, "%s-pc.png" % fmt))
        montage_telephone(fmt, ims[0]).save(os.path.join(dossier, "%s-telephone.png" % fmt))
        print("%s  %d x %d, %d px/unite, %d couleurs, texte %d Ko (gzip %d Ko)" % (fmt, W, H, k, n, brut // 1024,
                                                                                    gz // 1024))
    mesures["actuel"] = actuel(dossier)
    print("actuel", mesures["actuel"])
    return mesures


if __name__ == "__main__":
    main()
