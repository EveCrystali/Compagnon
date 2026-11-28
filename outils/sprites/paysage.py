"""Le moteur de peinture des paysages (docs/PEINTURE.md) : de quoi composer un décor de campagne 480 × 240 comme un
peintre, par le code. Né de l'étude docs/maquettes/paysages (direction C, choisie par Antoine le 28 novembre 2026 :
règle 9 de CLAUDE.md, « le pixel art n'est jamais une baisse de qualité ni de définition »).

Un décor se décrit en « unités du monde » : x de 0 à 192, y de -16 (le haut du cadre) à 80, le sol vers y = 78. De
y = 0 à 80 ce sont les coordonnées des décors d'avant ; le cadre 2:1 ajoute 16 unités de ciel ou de plafond au-dessus.
La grille réelle est deux fois et demie plus fine (480 × 240, 2 px d'écran par pixel) : les grandes formes se donnent en unités, les petites
choses (feuilles, brins, tuiles, éclats) se posent au pixel.

Trois idées à garder en tête :
  - des plans, du fond vers nous (ciel, nuages, lointains, plan moyen, premier plan) : `Tableau.plan(nom, profondeur)` ;
  - une seule lumière : `P.soleil`, que toutes les briques regardent (versants, liserés, reflets) ;
  - une palette limitée et nommée : `Tons` (62 couleurs au plus par décor, la limite du format).

Les briques sont rangées dans l'ordre d'un tableau : ciel, nuages, lointains, terres, eau, vie, premier plan. Chacune
dessine sur le plan en cours de `P` (le `Peintre`). `P.p` est la phase de la boucle d'ambiance (0 ≤ p < 1) : tout ce qui
bouge en dépend par `onde(p)` ou par un tirage décalé, pour que la boucle se referme.

Outil de fabrication (numpy, Pillow) : rien ici n'est embarqué. Les décors sont écrits par decors_hd.py.
"""
import math

import numpy as np
from PIL import Image, ImageDraw

W, H = 480, 240                   # la grille d'un décor (cadre 2:1)
HAUT = -16.0                      # le y du haut du cadre, en unités du monde
IMAGES, DUREE = 8, 200            # la boucle d'ambiance par défaut : 8 images à 5 images par seconde
MARGE = 6                         # unités peintes hors champ de chaque côté (parallaxe, cadrage du téléphone)
BAYER = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + 0.5) / 16.0

# ---------------------------------------------------------------------------------------------------------------
# Palette : une liste commune, chaque couleur prend un numéro à son premier emploi ; un décor n'écrit que les siennes.
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


class Tons:
    """Les tons d'un décor : des rampes nommées, du sombre au clair. Les briques lisent les tons en cours (`T`).

    ciel (12, du zénith à l'horizon), soleil, loin (6, lointains du plus proche au plus brumeux), herbe (5), or (3 :
    liserés de lumière), nuit (3 : premier plan à contre-jour), bois (5 : deux bruns, trois clairs), toit (2),
    pierre (2), orange (2), lueur (2 : fenêtres, lanternes), eau (9 tons froids ; les reflets chauds viennent du ciel),
    creme, encre, violet, bleu. `nuage` : 10 tons, par défaut tirés du ciel."""

    def __init__(self, ciel, loin, herbe, eau, soleil="#fff6d8", nuage=None,
                 or_=("#d9a441", "#f2c46b", "#ffe08f"), nuit=("#0b1530", "#11203f", "#15304f"),
                 bois=("#4a2e17", "#7a4b26", "#bf915f", "#e2bd85", "#f4dcae"), toit=("#3d3f7a", "#5458a0"),
                 pierre=("#6b6183", "#c3b8c9"), orange=("#d9803a", "#f69d50"), lueur=("#ffd65a", "#fff2b0"),
                 creme="#fff6e6", encre="#1c2128", violet="#9b8cff", bleu="#6cb6ff"):
        assert len(ciel) == 12 and len(loin) == 6 and len(herbe) == 5 and len(eau) == 9
        self.CIEL = cs(*ciel)
        self.SOL, self.BLANC = c(soleil), c("#ffffff")
        self.L0, self.L1, self.L2, self.L3, self.L4, self.L5 = cs(*loin)
        self.S0, self.S1, self.S2, self.S3, self.S4 = cs(*herbe)
        self.OR1, self.OR2, self.OR3 = cs(*or_)
        self.N0, self.N1, self.N2 = cs(*nuit)
        self.BR1, self.BR2, self.M2, self.M3, self.M4 = cs(*bois)
        self.D1, self.D2 = cs(*toit)
        self.P1, self.P3 = cs(*pierre)
        self.O2, self.O3 = cs(*orange)
        self.LUM, self.LUM2 = cs(*lueur)
        self.CREME, self.ENCRE, self.VIOLET, self.BLEU = c(creme), c(encre), c(violet), c(bleu)
        self.EAU = cs(*eau) + self.CIEL[8:11]
        self.NUAGE = cs(*nuage) if nuage else self.CIEL[2:11] + [self.SOL]
        assert len(self.NUAGE) == 10


T = None        # les tons en cours


def utiliser(tons):
    global T
    T = tons


def rvb(h):
    return int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)


FIN = True         # les détails que seule une grille de 2,5 pixels par unité peut porter


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
# Le peintre
# ---------------------------------------------------------------------------------------------------------------


class Peintre:
    """Une grille de numéros de couleur (-1 : vide), des coordonnées « monde », des pinceaux.
    soleil : (x, y) de la lumière, en unités ; phase : où l'on est dans la boucle d'ambiance (0 ≤ p < 1)."""

    def __init__(self, soleil, phase=0.0, largeur=W, hauteur=H):
        self.W, self.H = largeur, hauteur
        self.s = self.W / 192.0                      # pixels par unité du monde
        self.y0 = 80 - self.H / self.s               # haut du tableau, en unités du monde
        self.M = int(round(MARGE * self.s))
        self.Wt = self.W + 2 * self.M
        self.XI, self.YI = np.meshgrid(np.arange(self.Wt), np.arange(self.H))
        self.X = (self.XI - self.M + 0.5) / self.s
        self.Y = (self.YI + 0.5) / self.s + self.y0
        self.T = BAYER[self.YI % 4, self.XI % 4]     # le seuil de trame de chaque pixel
        self.p = phase
        self.soleil = soleil
        self.tr = 1.0                                 # largeur des trames de `rampe` (matiere=True : 0,4)
        self.horizon, self.ciel_haut, self.halo = 45.5, 0.2, 0.34
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
        haut[0] = masque[0]                           # le bord du cadre n'est pas une crête
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


def valeur_ciel(P, X, Y):
    """La clarté du ciel (0 : zénith sombre, 1 : l'horizon près du soleil) ; l'eau s'en sert aussi."""
    t = np.clip((Y - P.y0) / (P.horizon - P.y0), 0, 1)
    v = (P.ciel_haut + (1 - P.ciel_haut) * t) ** 0.9 * 0.93
    d = np.hypot(X - P.soleil[0], (Y - P.soleil[1]) * 1.8)
    v = v + P.halo * np.exp(-(d / 34.0) ** 2) + 0.07 * (fbm(X / 46.0, Y / 9.0, 3, 5) - 0.5)
    return np.clip(v, 0, 1)


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


def profil(x, base, amp, ech, graine):
    x = np.asarray(x, dtype=float)
    n = fbm(x / ech, np.full_like(x, 0.37), 4, graine)
    return base - amp * (0.55 * (1 - np.abs(2 * n - 1)) + 0.45 * n)


def table_reflets():
    """Chaque couleur de la palette → le ton d'eau qui la reflète (assombrie, tirée vers le bleu nuit)."""
    eau = np.array([rvb(PAL[i]) for i in T.EAU], dtype=float)
    fond = np.array(rvb(PAL[T.EAU[1]]), dtype=float)
    t = np.zeros(len(PAL), dtype=np.int16)
    for i, h in enumerate(PAL):
        r = np.array(rvb(h), dtype=float) * 0.74 + fond * 0.26
        t[i] = int(np.argmin(((eau - r) ** 2 * np.array([1.0, 1.2, 0.8])).sum(axis=1)))
    return t


def tampon_feuille(P, g):
    """Une petite feuille en pixels (liste de décalages), selon la finesse de la grille."""
    o = int(hz(g, 5, 7) * 4)
    if FIN:
        formes = [[(0, 0), (1, 0), (2, 0), (3, 0), (1, -1), (2, -1), (1, 1), (2, 1), (4, 0)],
                  [(0, 0), (0, 1), (0, 2), (0, 3), (-1, 1), (-1, 2), (1, 1), (1, 2), (0, 4)],
                  [(0, 0), (1, 1), (2, 2), (3, 3), (1, 0), (2, 1), (3, 2), (0, 1), (1, 2)],
                  [(0, 0), (1, -1), (2, -2), (3, -3), (1, 0), (2, -1), (3, -2), (0, -1), (1, -2)]]
    else:
        formes = [[(0, 0), (1, 0), (2, 0), (1, -1)], [(0, 0), (0, 1), (0, 2), (1, 1)], [(0, 0), (1, 1), (2, 2), (1, 0)],
                  [(0, 0), (1, -1), (2, -2), (1, 0)]]
    return formes[o]


# ---------------------------------------------------------------------------------------------------------------
# Les plans d'un tableau
# ---------------------------------------------------------------------------------------------------------------
class Tableau:
    """Les plans d'une image, du fond vers nous. `plan(nom, profondeur)` ouvre un plan neuf sur le peintre ; la
    profondeur (0 : le ciel, immobile ; 1 : le premier plan) règle la parallaxe quand la caméra glisse."""

    def __init__(self, P):
        self.P = P
        self.plans = []

    def plan(self, nom, profondeur):
        self.plans.append((nom, profondeur, self.P.neuf()))
        return self.P

    def derriere(self):
        """Tout ce qui est déjà peint (plan en cours compris), caméra au repos : ce que l'eau reflète."""
        out = None
        for _, _, g in self.plans:
            out = g.copy() if out is None else np.where(g >= 0, g, out)
        return out

    def image(self, camera=0.0):
        """L'image composée (numéros de couleur) ; camera : glissement en unités du monde."""
        P = self.P
        out = None
        for _, prof, g in self.plans:
            d = int(round(camera * prof * P.s))
            vue = g[:, P.M + d:P.M + d + P.W]
            out = vue.copy() if out is None else np.where(vue >= 0, vue, out)
        assert (out >= 0).all(), "pixel vide (un décor est opaque)"
        return out


def en_image(idx, k=1):
    pal = np.array([rvb(h) for h in PAL], dtype=np.uint8)
    im = Image.fromarray(pal[idx], "RGB")
    return im.resize((im.width * k, im.height * k), Image.NEAREST) if k != 1 else im


# ---------------------------------------------------------------------------------------------------------------
# Le ciel
# ---------------------------------------------------------------------------------------------------------------
def ciel(P, horizon=45.5, haut=0.2, halo=0.34, etoiles=0.0, lune=None, disque=5.6, trame=0.75):
    """Dégradé tramé du zénith (ton `haut` de la rampe, 0 = le plus sombre) à l'horizon, halo autour du soleil.
    etoiles : part du ciel (0..1 de la valeur) où elles peuvent paraître ; lune : (x, y, rayon) ou None."""
    P.horizon, P.ciel_haut, P.halo = horizon, haut, halo
    tout = np.ones(P.X.shape, dtype=bool)
    v = valeur_ciel(P, P.X, P.Y)
    P.rampe(tout, v, T.CIEL, trame)
    if etoiles > 0:
        pas = 4.0
        for cy in range(int(P.y0 // pas) - 1, 12):
            for cx in range(-2, 52):
                if hz(cx, cy, 11) > 0.22:
                    continue
                x, y = (cx + hz(cx, cy, 12)) * pas, (cy + hz(cx, cy, 13)) * pas
                X, Y = P.px(x), P.py(y)
                if not (0 <= X < P.Wt and 0 <= Y < P.H) or v[Y, X] > etoiles:
                    continue
                vive = ((P.p + hz(cx, cy, 14)) % 1.0) < 0.55
                P.bloc(X, Y, T.SOL if vive else T.CIEL[5])
                if vive and hz(cx, cy, 15) < 0.3:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        P.bloc(X + dx, Y + dy, T.CIEL[4])
    if lune:
        lx, ly, r = lune
        plein = (P.X - lx) ** 2 + (P.Y - ly) ** 2 <= r * r
        creux = (P.X - lx + r * 0.55) ** 2 + (P.Y - ly + r * 0.25) ** 2 <= (r * 0.95) ** 2
        P.remplir(plein & ~creux, T.SOL)
    if disque:
        d = np.hypot(P.X - P.soleil[0], P.Y - P.soleil[1])
        P.remplir((d < disque * 1.32) & (P.T < 0.5), T.CIEL[11])
        P.remplir(d < disque, T.SOL)
        P.remplir(d < disque * 0.75, T.BLANC)


def cumulus(P, groupes, dessous=0.72):
    """Nuages en volumes. groupes : (x, y de la base, largeur, hauteur, graine, nombre de boules, décalage de phase).
    dessous : part de la lumière qui vient d'en bas (soleil bas : 0,7 ; plein jour : mettre une valeur négative)."""
    for (cx, cy, l, h, g, n, d) in groupes:
        cx = cx + 0.6 * onde(P.p, d)
        dx = P.soleil[0] - cx
        lum = (0.32 * (1 if dx > 0 else -1) * min(1.0, abs(dx) / 30.0), dessous, 0.35)
        P.volumes(amas(cx, cy, l, h, g, n), T.NUAGE, lum, plancher=cy + h * 0.12, grain=0.22, graine=g, gain=0.62,
                  base=0.5)
        if dessous > 0:
            bas = (P.a >= 0) & (np.abs(P.Y - (cy + h * 0.12)) < 0.6 / P.s + 0.25) & (np.abs(P.X - cx) < l * 0.42)
            P.remplir(bas & (fbm(P.X / 3.0, P.Y, 2, g) > 0.35), T.NUAGE[7])


def voiles(P, y=13.0, epais=9.0, seuil=0.58, graine=21):
    """Voiles hauts (cirrus) : des filaments de bruit étirés, éclairés par-dessous."""
    def densite(X, Y):
        return fbm((X + 0.5 * onde(P.p)) / 30.0, Y / 2.4, 4, graine) - seuil - 0.16 * ((Y - y) / epais) ** 2

    d0 = densite(P.X, P.Y)
    dessous = d0 - densite(P.X, P.Y + 1.4)
    prox = np.exp(-(np.hypot(P.X - P.soleil[0], P.Y - P.soleil[1]) / 70.0) ** 2)
    P.rampe(d0 > 0, 0.22 + 2.6 * dessous + 0.45 * prox + 1.2 * d0, T.NUAGE[:8], 0.7)


def barres(P, liste, graine=40):
    """Barres de nuages basses, près de l'horizon. liste : (x, y, demi-largeur, demi-hauteur)."""
    for i, (x, y, rx, ry) in enumerate(liste):
        x = x + 0.5 * onde(P.p, 0.2 * i)
        u, w = (P.X - x) / rx, (P.Y - y) / ry
        forme = u * u + w * w + 0.5 * (fbm(P.X / 5.0, P.Y / 1.2, 3, graine + i) - 0.5) <= 1
        P.rampe(forme, 0.5 + 0.34 * w + 0.3 * np.exp(-((P.X - P.soleil[0]) / 40.0) ** 2), T.NUAGE[2:], 0.6)


def oiseaux(P, x, y, n=7, coul=None):
    """Un vol en chevron, ailes qui battent."""
    coul = T.CIEL[1] if coul is None else coul
    places = ((0, 0), (-3.2, 1.2), (3.0, 1.5), (-6.6, 2.6), (6.2, 3.1), (-9.6, 4.1), (-1.2, 4.6), (9.4, 4.8))[:n]
    for i, (dx, dy) in enumerate(places):
        bx, by = x + dx + 0.4 * onde(P.p, 0.1 * i), y + dy + 0.25 * onde(P.p, 0.3 + 0.13 * i)
        aile = onde(P.p * 2, 0.17 * i)
        P.trait(bx - 1.1, by - 0.6 * aile, bx, by, coul)
        P.trait(bx, by, bx + 1.1, by - 0.6 * aile, coul)


# ---------------------------------------------------------------------------------------------------------------
# Les lointains
# ---------------------------------------------------------------------------------------------------------------
def crete(P, f, rampe, pente=0.7, fond=7.0, bas=None):
    """Une crête lointaine sous la courbe f : versants éclairés du côté du soleil, brume vers le bas.
    rampe : 4 tons (ombre, base, lumière, brume)."""
    fx = f(P.X)
    prof = P.Y - fx
    m = prof >= 0
    if bas is not None:
        m &= P.Y < bas
    cote = np.where(P.X < P.soleil[0], 1.0, -1.0)
    xs = P.X + prof * pente * cote
    versant = (f(xs + 0.7) - f(xs - 0.7)) * cote > 0
    v = 0.12 + 0.36 * versant + 0.5 * np.clip(prof / fond, 0, 1) + 0.1 * (fbm(P.X / 4.0, P.Y / 2.0, 2, 70) - 0.5)
    P.rampe(m, v, rampe, 0.6)
    P.remplir(P.crete(m) & versant, rampe[2])
    return m


def sapins(P, f, densite=0.55, graine=81, coul=None, sauf=None):
    """Sapins minuscules le long d'une crête. sauf : (x0, x1) à laisser nu."""
    coul = T.L0 if coul is None else coul
    x = -MARGE
    while x < 192 + MARGE:
        k = int(round(x * 10))
        if hz(k, 0, graine) < densite and not (sauf and sauf[0] < x < sauf[1]):
            h = 0.9 + 1.5 * hz(k, 1, graine)
            y = float(f(x)) + 0.3
            P.poly([(x - 0.55, y), (x + 0.55, y), (x, y - h)], coul)
            P.trait(x, y - h, x, y, coul)
        x += 0.5 + 0.9 * hz(k, 2, graine)


def moulin(P, x, y):
    """Un moulin lointain : ses ailes font un quart de tour par boucle (il en a quatre, la boucle se referme)."""
    P.poly([(x - 0.9, y), (x + 0.9, y), (x + 0.55, y - 3.4), (x - 0.55, y - 3.4)], T.L1)
    P.trait(x + 0.5, y - 3.3, x + 0.8, y - 0.2, T.L4)
    P.poly([(x - 0.8, y - 3.3), (x + 0.8, y - 3.3), (x, y - 4.4)], T.L0)
    for q in range(4):
        a = (P.p + q) * math.pi / 2 + 0.3
        P.trait(x, y - 3.5, x + 3.0 * math.cos(a), y - 3.5 + 3.0 * math.sin(a), T.L0 if q % 2 else T.D1)
    P.point(x, y - 3.5, T.L5)


# ---------------------------------------------------------------------------------------------------------------
# Les terres
# ---------------------------------------------------------------------------------------------------------------
def pre(P, f, rampe=None, jusque=None, lisere=True, graine=90, pente=0.11, clair=0.62):
    """Un pré sous la courbe f : sarcelle tramée, plus sombre en descendant, crête dorée. jusque : masque à ne pas
    dépasser (par exemple au-dessus d'une rive). Renvoie le masque."""
    rampe = rampe or [T.S1, T.S2, T.S3, T.S4]
    fx = f(P.X)
    m = P.Y >= fx
    if jusque is not None:
        m &= jusque
    v = clair + 0.3 * (fbm(P.X / 9.0, P.Y / 2.2, 3, graine) - 0.5) - pente * (P.Y - fx)
    P.rampe(m, v, rampe, 0.7)
    if lisere:
        P.remplir(P.crete(m), T.OR2)
    return m


def champ(P, f, x0, x1, y0, y1, a, b, pente=1.6, haie=True):
    """Un champ en rangs sur un pré (lavande, blé…) : bandes a / b penchées, une haie sombre en haut."""
    fx = f(P.X)
    m = (P.X > x0 + (P.Y - fx) * 1.4) & (P.X < x1 + (P.Y - fx) * 1.4) & (P.Y > fx + y0) & (P.Y < fx + y1)
    rang = np.floor((P.X + (P.Y - fx) * pente) * P.s / max(2, P.ep(0.9))) % 2 == 0
    P.remplir(m & rang, a)
    P.remplir(m & ~rang, b)
    if haie:
        h = (np.abs(P.Y - (fx + y0)) < 0.5 / P.s + 0.2) & (P.X > x0) & (P.X < x1 + 3) & (hz(P.XI // P.ep(0.7), 3, x0) < 0.7)
        P.remplir(h, T.S0)


def colline(P, f, centre, demi, jusque=None, graine=91, fonce=0.012):
    """Une colline ronde à contre-jour : le flanc tourné vers le soleil accroche la lumière, liseré d'or sur la crête.
    fonce : ce qu'elle perd de clarté par unité en descendant (une très grande colline : 0,004)."""
    fx = f(P.X)
    m = (P.Y >= fx)
    if jusque is not None:
        m &= jusque
    cote = 1.0 if P.soleil[0] < centre else -1.0
    u = (P.X - centre) / demi * cote
    v = 0.44 - 0.42 * u + 0.2 * (fbm(P.X / 6.0, P.Y / 3.0, 3, graine) - 0.5) + 0.05 * np.sin((P.Y - fx) * 1.5 + P.X * 0.2) \
        - fonce * (P.Y - fx)
    P.rampe(m, v, [T.S0, T.S1, T.S2, T.S3, T.S4], 0.75)
    cr = P.crete(m)
    P.remplir(cr & (u < 0.3), T.OR3)
    P.remplir(cr & (u >= 0.3), T.S3)
    return m


def bosquets(P, f, x0, x1, bas, n=15, graine=92, sauf=None):
    """Petits arbres ronds semés sur un flanc, avec leur ombre. sauf(x, y) : vrai là où il n'en faut pas."""
    pts = sorted(((x0 + (x1 - x0) * float(hz(i, 1, graine)), float(hz(i, 2, graine)), float(hz(i, 3, graine)))
                  for i in range(int(n * P.s ** 0.8))), key=lambda q: q[1])
    for (x, t, t2) in pts:
        haut = float(f(x))
        y = haut + 2.6 + (bas - haut) * t ** 0.8
        if y > bas + 1 or haut > bas - 1.5 or (sauf and sauf(x, y)):
            continue
        r = 0.9 + 0.9 * t2
        loin = (x > P.soleil[0]) == (x > (x0 + x1) / 2)
        P.ell(x + r * 0.9, y + r * 0.55, r * 1.3, r * 0.35, T.S0)
        P.ell(x, y, r, r * 0.9, T.S1 if loin else T.S2)
        P.ell(x - r * 0.3, y - r * 0.3, r * 0.6, r * 0.5, T.S2 if loin else T.S3)
        if not loin:
            P.point(x - r * 0.55, y - r * 0.55, T.OR2)


def sentier(P, pts, a=None, b=None, ep=0.5):
    """Un sentier en lacets : segments alternés de deux tons clairs."""
    a, b = a or T.OR2, b or T.OR1
    for i in range(len(pts) - 1):
        P.trait(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], a if i % 2 == 0 else b, P.ep(ep))


def grand_arbre(P, x, y, k=1.0, graine=93, balancoire=False):
    """Un arbre isolé (celui du sommet) : tronc courbe, feuillage en volumes éclairé du côté du soleil."""
    P.courbe([(x - 0.2 * k, y + 0.4), (x + 0.1 * k, y - 2.6 * k), (x - 0.1 * k, y - 6.4 * k)], T.BR1, P.ep(1.1 * k),
             P.ep(0.6 * k))
    P.trait(x, y - 3.4 * k, x + 3.4 * k, y - 5.2 * k, T.BR1, 1)
    if balancoire:
        dx = 0.35 * onde(P.p)
        P.trait(x + 2.2 * k, y - 4.5 * k, x + 2.2 * k + dx, y - 1.6 * k, T.M2)
        P.trait(x + 3.2 * k, y - 5.0 * k, x + 3.2 * k + dx, y - 1.6 * k, T.M2)
        P.trait(x + 2.0 * k + dx, y - 1.5 * k, x + 3.4 * k + dx, y - 1.5 * k, T.O3)
    f = [(-0.2, -7.6, 4.0), (-3.7, -6.0, 2.8), (3.6, -6.4, 2.9), (-1.6, -10.2, 2.8), (2.0, -9.8, 2.6), (0.4, -5.2, 2.6),
         (-5.2, -4.8, 1.5), (5.3, -5.0, 1.4)]
    cote = 1.0 if P.soleil[0] > x else -1.0
    P.volumes([(x + a * k, y + b * k, r * k) for a, b, r in f], [T.S0, T.S1, T.S2, T.S3, T.OR1, T.OR3],
              (0.8 * cote, 0.1, 0.25), grain=0.5, graine=graine, gain=0.62, base=0.36, trame=0.8)


def peuplier(P, x, y, h=7.0):
    cote = 1.0 if P.soleil[0] > x else -1.0
    P.ell(x, y - h / 2 - 0.4, 1.05, h / 2, T.S0)
    P.ell(x + 0.35 * cote, y - h / 2 - 0.4, 0.6, h / 2 - 0.5, T.S1)
    P.ell(x + 0.7 * cote, y - h / 2 - 0.6, 0.3, h / 2 - 1.2, T.S3)
    P.trait(x, y, x, y - 0.9, T.BR1)


def meule(P, x, y):
    """Une meule de foin, son ombre longue à l'opposé du soleil."""
    cote = 1.0 if P.soleil[0] > x else -1.0
    P.trait(x - 4.0 * cote, y, x - 0.5 * cote, y, T.S1, 1)
    P.ell(x, y - 0.9, 1.5, 1.5, T.OR1, cond=P.Y < y + 0.1)
    P.ell(x + 0.5 * cote, y - 1.0, 0.9, 1.1, T.OR3, cond=P.Y < y + 0.1)
    P.ell(x - 0.9 * cote, y - 0.7, 0.5, 0.9, T.O2, cond=P.Y < y + 0.1)


def mouton(P, x, y, broute=False):
    P.ell(x, y - 0.75, 1.05, 0.7, T.CREME)
    P.ell(x - 0.2, y - 0.55, 0.8, 0.35, T.P3)
    P.trait(x - 0.5, y - 0.2, x - 0.5, y + 0.25, T.ENCRE)
    P.trait(x + 0.5, y - 0.2, x + 0.5, y + 0.25, T.ENCRE)
    P.point(x + 1.0, y - (0.35 if broute else 0.95), T.ENCRE, P.ep(0.45))


def linge(P, x0, y0, x1, y1, haut, pieces=None):
    """Une corde à linge entre deux piquets plantés en (x0, y0) et (x1, y1) ; les pièces se balancent."""
    pieces = pieces or ((0.16, T.CREME, 1.6, 2.1), (0.38, T.O3, 1.3, 1.7), (0.6, T.BLEU, 1.7, 2.3), (0.82, T.CREME, 1.2, 1.5))
    ly = min(y0, y1) - haut
    P.trait(x0, y0, x0, ly, T.BR1)
    P.trait(x1, y1, x1, ly + 0.2, T.BR1)
    corde = lambda u: (x0 + (x1 - x0) * u, ly + 1.1 * math.sin(math.pi * u))
    for i in range(12):
        (xa, ya), (xb, yb) = corde(i / 12.0), corde((i + 1) / 12.0)
        P.trait(xa, ya, xb, yb, T.M2)
    ombres = {T.CREME: T.M3, T.O3: T.O2, T.BLEU: T.D2}
    for i, (u, coul, l, h) in enumerate(pieces):
        x, y = corde(u)
        y += 0.2
        d = 0.45 * onde(P.p, 0.2 * i)
        P.poly([(x - l / 2, y), (x + l / 2, y), (x + l / 2 + d, y + h), (x - l / 2 + d, y + h)], coul)
        P.trait(x + l / 2 + d * 0.5 - 1.0 / P.s, y + 0.3, x + l / 2 + d - 1.0 / P.s, y + h - 0.2, ombres.get(coul, T.M3))


def cloture(P, f, x0, x1, dy=1.9, pas=2.6):
    x = x0
    while x < x1:
        y = float(f(x)) + dy
        xs = min(x + pas, x1)
        P.trait(x, y, x, y - 1.2, T.BR2)
        P.trait(x, y - 0.8, xs, float(f(xs)) + dy - 0.8, T.BR2)
        P.point(x, y - 1.2, T.M2)
        x += pas


def rive(P, f, epais=1.5, joncs=120, graine=95, sauf=None):
    """La rive d'en face : une bande sombre sous la courbe f, un liseré par endroits, des joncs."""
    fr = f(P.X)
    m = (P.Y >= fr) & (P.Y < fr + epais + 0.5 * np.sin(P.X / 3.1))
    P.rampe(m, 0.3 + 0.5 * (fbm(P.X / 3.0, P.Y, 2, graine) - 0.5) + 0.2 * (P.Y - fr), [T.S1, T.S0, T.N2], 0.6)
    P.remplir(P.crete(m) & (fbm(P.X / 6.0, P.Y * 0, 2, graine + 1) > 0.56), T.OR1)
    for i in range(int(joncs * P.s)):
        x = -MARGE + (192 + 2 * MARGE) * hz(i, 1, graine + 2)
        if sauf and sauf[0] < x < sauf[1] and hz(i, 4, graine + 2) < 0.7:
            continue
        y = float(f(x))
        h = 0.5 + 1.6 * hz(i, 2, graine + 2) ** 2
        P.trait(x, y + 0.3, x + (hz(i, 3, graine + 2) - 0.5) * 0.5, y - h, T.S0 if hz(i, 5, graine + 2) < 0.7 else T.S1)


# ---------------------------------------------------------------------------------------------------------------
# L'eau
# ---------------------------------------------------------------------------------------------------------------
def miroir(P, derriere, axe, bas=None, ronds=(), fonce=(56.0, 17.0), eclats=0.78, rides=0.05, graine=120):
    """Une eau calme : le miroir de `derriere` (Tableau.derriere()) autour de la ligne y = axe, brisé par les rides,
    avec le chemin de lumière sous le soleil. Ne peint que là où le plan en cours est vide, sous l'axe (et au-dessus
    de `bas`, courbe f(x) ou None). ronds : (x, y, décalage de phase) des ronds dans l'eau. fonce : (y, étendue) à
    partir d'où l'eau s'assombrit vers nous."""
    p = P.p
    X, Y = P.X, P.Y
    lut = table_reflets()
    src_y = np.clip(np.floor((axe - (Y - axe) * 1.28 - P.y0) * P.s), 0, P.H - 1).astype(np.int64)
    amp = (0.25 + 0.06 * (Y - axe)) * P.s
    dec = np.round(amp * np.sin(Y * 2.3 + 2 * math.pi * p + 0.6 * np.sin(X / 9.0))).astype(np.int64)
    q = P.ep(0.9)
    xq = np.where((P.YI // max(1, P.ep(0.5))) % 2 == 0, (P.XI // q) * q, P.XI)
    e = lut[derriere[src_y, np.clip(xq + dec, 0, P.Wt - 1)]].astype(float)
    e = e - 2.6 * np.clip((Y - fonce[0]) / fonce[1], 0, 1) ** 1.4 - 1.2 * np.clip((np.abs(X - 96) - 66) / 30.0, 0, 1)
    e = e + 0.9 * (fbm(X / 14.0, Y / 1.6, 3, graine) - 0.5)
    dl = P.ep(1.5)
    cell = (P.XI + (P.YI % 3) * 2) // dl
    h1 = hz(cell, P.YI, graine + 1)
    large = np.maximum(2.2 + (Y - axe) * 0.55, 0.5)
    force = np.exp(-((X - P.soleil[0] - 0.6 * np.sin(Y * 0.7)) / large) ** 2)
    temps = np.floor(((p + hz(cell, P.YI, graine + 2)) % 1.0) * 4)
    eclat = (h1 < eclats * force) & (temps < 2) & (Y > axe + 0.6)
    e = np.where(eclat, np.maximum(e, 8) + 1.6 + 1.6 * force, e)
    ride = (hz(cell, P.YI, graine + 3) < rides) & (np.floor(((p + hz(cell, P.YI, graine + 4)) % 1.0) * 4) < 2)
    e = np.where(ride, e + 1.5, e)
    for (rx0, ry0, d) in ronds:
        age = (p + d) % 1.0
        dd = np.hypot((X - rx0), (Y - ry0) * 2.8)
        anneau = (np.abs(dd - (1.0 + 5.5 * age)) < 0.8 / P.s + 0.12) & (P.T > age * 0.9)
        e = np.where(anneau, e + 2.2, e)
    m = (Y >= axe - 0.6) & (P.a < 0)
    if bas is not None:
        m &= Y < bas(X) + 1.0
    idx = np.clip(np.floor(e + P.T), 0, len(T.EAU) - 1).astype(np.int64)
    P.a[m] = np.asarray(T.EAU, dtype=np.int16)[idx][m]
    P.remplir(m & eclat & (force > 0.55) & (h1 < 0.3), T.SOL)
    return m


def pierre(P, x, y, r, eau=True):
    if eau:
        P.ell(x, y + 0.5, r * 1.15, r * 0.4, T.EAU[0])
    P.ell(x, y, r, r * 0.62, T.P1, cond=P.Y < y + 0.35)
    P.ell(x - r * 0.25, y - r * 0.22, r * 0.55, r * 0.3, T.P3, cond=P.Y < y + 0.35)
    P.point(x - r * 0.5, y - r * 0.45, T.OR2)


def libellule(P, x, y):
    lx, ly = x + 0.5 * onde(P.p), y + 0.3 * onde(P.p, 0.25)
    P.trait(lx - 1.6, ly, lx + 1.6, ly, T.D2, P.ep(0.35))
    P.point(lx + 1.7, ly, T.BLEU)
    haut = int(P.p * IMAGES) % 2 == 0
    for cote in (-1, 1):
        P.trait(lx + 0.2, ly, lx + 0.2 + cote * 0.4, ly - (1.5 if haut else 0.7), T.CREME)
        P.trait(lx - 0.5, ly, lx - 0.5 + cote * 0.3, ly + (0.3 if haut else 1.1), T.SOL)


def canard(P, x, y, sens=1):
    """Un canard sur l'eau : corps crème, tête sombre, bec orange ; il se dandine, son sillage le suit."""
    y = y + 0.2 * onde(P.p, 0.4)
    for i in range(3):
        P.trait(x - sens * (2.0 + i * 1.6), y + 1.0 + i * 0.5, x - sens * (4.5 + i * 2.2), y + 1.0 + i * 0.5, T.EAU[6])
    P.ell(x, y + 1.0, 2.6, 0.45, T.EAU[0])
    P.ell(x, y, 2.3, 1.2, T.CREME)
    P.ell(x - 0.5 * sens, y + 0.2, 1.4, 0.7, T.P3)
    P.poly([(x - 2.2 * sens, y - 0.3), (x - 3.3 * sens, y - 1.2), (x - 1.6 * sens, y - 0.6)], T.CREME)
    P.ell(x + 1.9 * sens, y - 1.5, 0.95, 0.9, T.S1)
    P.trait(x + 1.6 * sens, y - 0.8, x + 2.2 * sens, y - 0.8, T.BLANC)
    P.rect(min(x + 2.6 * sens, x + 3.7 * sens), y - 1.5, 1.1, 0.5, T.O3)
    P.point(x + 2.1 * sens, y - 1.8, T.ENCRE)


# ---------------------------------------------------------------------------------------------------------------
# Le premier plan
# ---------------------------------------------------------------------------------------------------------------
def sol(P, f, rampe=None, chemin=77.6, graine=130, lisere=0.6):
    """La berge où l'on marche, sous la courbe f : sombre, un rien plus claire sur le chemin (y = chemin), son bord
    qui prend la lumière. Renvoie le masque."""
    rampe = rampe or [T.N0, T.N1, T.N2, T.S1, T.S2]
    fb = f(P.X)
    m = P.Y >= fb
    prof = P.Y - fb
    v = 0.3 + 0.5 * (fbm(P.X / 6.0, P.Y / 2.0, 3, graine) - 0.5) + 0.42 * np.exp(-prof / 1.3) \
        + 0.16 * np.exp(-((P.Y - chemin) / 1.6) ** 2)
    P.rampe(m, v, rampe, 0.8)
    bord = P.crete(m)
    P.remplir(bord, rampe[-1])
    P.remplir(bord & (fbm(P.X / 7.0, P.Y * 0, 2, graine + 1) > lisere), T.OR1)
    return m


def cailloux(P, f, n=46, y0=75.6, y1=79.6, graine=132):
    for i in range(int(n * P.s)):
        x, y = -MARGE + (192 + 2 * MARGE) * hz(i, 1, graine), y0 + (y1 - y0) * hz(i, 2, graine)
        if y > float(f(x)) + 1.5:
            P.point(x, y, T.N2 if hz(i, 3, graine) < 0.6 else T.P1)
            if hz(i, 3, graine) > 0.8:
                P.point(x + 1.0 / P.s, y, T.P1)


def touffes(P, f, n=210, x0=-MARGE, x1=192 + MARGE, haut=3.6, fond=6.5, bord=0.62, tons=None, graine=133, bas=79.8):
    """Des touffes d'herbe sur le bord d'un sol (hautes, elles se balancent) et sur sa surface (rases).
    bord : part des touffes posées sur le bord ; tons : (sombres…, clairs) du plus fréquent en bas au rare en haut."""
    for i in range(int(n * P.s * (x1 - x0) / 204.0)):
        x = x0 + (x1 - x0) * hz(i, 1, graine)
        sur_bord = hz(i, 2, graine) < bord
        y = float(f(x)) + (0.4 + 0.6 * hz(i, 3, graine) if sur_bord else 1.2 + fond * hz(i, 3, graine))
        if y > bas:
            continue
        h = (1.2 + haut * hz(i, 4, graine) ** 2) if sur_bord else (0.5 + 1.1 * hz(i, 4, graine))
        penche = (hz(i, 5, graine) - 0.5) * 1.6
        vent = 0.5 * h / 4.0 * onde(P.p, x / 37.0)
        t = hz(i, 6, graine)
        coul = T.OR2 if t > 0.9 else (T.OR1 if t > 0.8 else (T.S2 if t > 0.55 else (T.S1 if t > 0.28 else T.N1)))
        if not sur_bord and coul in (T.OR1, T.OR2):
            coul = T.S2
        P.trait(x, y, x + penche * 0.5 + vent * 0.4, y - h * 0.55, coul)
        P.trait(x + penche * 0.5 + vent * 0.4, y - h * 0.55, x + penche + vent, y - h, coul)


def fleur(P, x, y, h, coul, coeur=None):
    """Une fleur des champs : une tige qui se balance, quatre pétales, un cœur."""
    d = 0.25 * onde(P.p, x / 23.0)
    P.trait(x, y, x + d, y - h, T.S2)
    for (ax, ay) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        P.point(x + d + ax / P.s, y - h + ay / P.s, coul)
    P.point(x + d, y - h, coeur if coeur is not None else T.OR2)


def fleurs(P, f, n=21, x0=10, x1=182, libres=((13, 31), (158, 178)), fond=4.6, graine=134, bas=79.0):
    """Marguerites crème, coquelicots orange, clochettes violettes, semés sur un sol. libres : intervalles de x à
    laisser dégagés (la place de Pilou, celle de son interlocuteur)."""
    for i in range(n):
        x = x0 + (x1 - x0) * hz(i, 1, graine)
        y = float(f(x)) + 0.9 + fond * hz(i, 2, graine)
        if y > bas or any(a < x < b for a, b in libres):
            continue
        sorte = int(hz(i, 4, graine) * 3)
        fleur(P, x, y, 1.4 + 1.6 * hz(i, 3, graine), (T.CREME, T.O3, T.VIOLET)[sorte], (T.OR2, T.ENCRE, T.CREME)[sorte])


def champignon(P, x, y, r):
    P.rect(x - 0.3, y - 0.9, 0.7, 1.0, T.CREME)
    P.ell(x, y - 1.1, r, r * 0.75, T.O2, cond=P.Y < y - 0.8)
    P.ell(x - r * 0.2, y - 1.3, r * 0.6, r * 0.35, T.O3, cond=P.Y < y - 0.8)
    P.point(x - r * 0.3, y - 1.5, T.CREME)
    P.point(x + r * 0.4, y - 1.3, T.CREME)


def tronc(P, bord, cote=-1, graine=140):
    """Un tronc de premier plan à contre-jour qui sort du cadre : tout ce qui est à gauche (cote = -1) ou à droite
    (cote = 1) de la courbe bord(y). Écorce tramée, liseré orange du côté intérieur. Renvoie le masque."""
    b = bord(P.Y)
    m = (P.X < b) if cote < 0 else (P.X > b)
    dist = (b - P.X) if cote < 0 else (P.X - b)
    P.rampe(m, 0.25 + 0.55 * (fbm(P.X / 1.3, P.Y / 9.0, 3, graine) - 0.5) + 0.07 * (2 - dist * 0.2), [T.N0, T.N1, T.N2], 0.7)
    lis = m & (dist < 1.2 / P.s + 0.25)
    n = fbm(P.X * 0, P.Y / 6.0, 2, graine + 1)
    P.remplir(lis & (n > 0.5), T.O2)
    P.remplir(lis & (dist < 1.0 / P.s) & (n > 0.62), T.O3)
    return m


def feuillage(P, haut, x0=-MARGE, x1=78, n=520, epais=9.0, graine=142, y_max=22.0, tons=None):
    """Un feuillage de premier plan qui pend du haut du cadre : tout ce qui est au-dessus de la courbe haut(x).
    Une masse sombre trouée de ciel, puis des feuilles posées une à une ; celles du bord prennent la lumière et
    remuent. tons : (sombres [4], milieu [3], bord [5]) pour changer d'essence ou de saison."""
    sombres, milieu, bordure = tons or ([T.N0, T.N1, T.N2, T.S1], [T.N2, T.S1, T.S2], [T.S1, T.S2, T.OR1, T.O2, T.O3])
    X, Y = P.X, P.Y
    dedans = haut(X) - Y
    dans_x = (X > x0) & (X < x1)
    masse = (dedans > 1.6 + 2.6 * (fbm(X / 3.5, Y / 3.0, 3, graine) - 0.5)) & dans_x
    trou = (fbm(X / 2.6, Y / 2.2, 3, graine + 1) > 0.66) & (dedans < 7) & (dedans > 0.8)
    P.rampe(masse & ~trou, 0.3 + 0.9 * (fbm(X / 2.0, Y / 2.0, 3, graine + 2) - 0.5) + 0.05 * np.clip(6 - dedans, 0, 6),
            sombres, 0.9)
    k = int(n * P.s * P.s * (x1 - x0) / 90.0)
    xs = x0 + (x1 - x0) * hz(np.arange(k), 1, graine + 3)
    ys = P.y0 - 2 + (y_max + 2 - P.y0) * hz(np.arange(k), 2, graine + 3)
    for i in np.argsort(haut(xs) - ys)[::-1]:                                # le dedans d'abord, le bord à la fin
        x, y = float(xs[i]), float(ys[i])
        d = float(haut(x)) - y
        if d < -1.4 or d > epais or (d > 3.5 and hz(i, 3, graine + 3) < 0.6):
            continue
        t = hz(i, 4, graine + 3)
        if d < 1.6:
            coul = bordure[4] if t > 0.86 else (bordure[3] if t > 0.7 else (bordure[2] if t > 0.62 else
                                                                         (bordure[1] if t > 0.34 else bordure[0])))
            x += 0.3 * onde(P.p, x / 11.0)
            y += 0.15 * onde(P.p, 0.25 + x / 7.0)
        elif d < 3.5:
            coul = milieu[2] if t > 0.82 else (milieu[1] if t > 0.4 else milieu[0])
        else:
            coul = milieu[1] if t > 0.7 else milieu[0]
        X0, Y0 = P.px(x), P.py(y)
        for (ax, ay) in tampon_feuille(P, i):
            P.bloc(X0 + ax, Y0 + ay, coul)


def lanterne(P, x, y, corde=4.4):
    """Une lanterne pendue en (x, y) : elle se balance, sa flamme vacille, un halo tramé autour."""
    lx, ly = x + 0.45 * onde(P.p, 0.1), y + corde
    P.trait(x, y, lx, ly - 1.4, T.N0)
    d = np.hypot(P.X - lx, (P.Y - ly) * 1.1)
    P.remplir((d < 3.4) & (P.T < 0.34 - d * 0.1) & (P.a < 0), T.LUM)
    vive = int(P.p * IMAGES) % 3
    P.rect(lx - 1.0, ly - 1.4, 2.0, 0.6, T.N0)
    P.rect(lx - 0.8, ly - 0.8, 1.6, 2.2, T.LUM if vive else T.LUM2)
    P.rect(lx - 0.3, ly - 0.3, 0.6, 1.2, T.LUM2 if vive else T.BLANC)
    P.rect(lx - 1.0, ly + 1.3, 2.0, 0.5, T.N0)
    P.trait(lx - 1.0, ly - 0.9, lx - 1.0, ly + 1.4, T.N0)
    P.trait(lx + 0.95, ly - 0.9, lx + 0.95, ly + 1.4, T.BR1)


def roseaux(P, x0, x1, n=13, bas=81.0, haut=(13.0, 32.0), penche=-1.0, graine=150, sauf=None):
    """Roseaux, quenouilles et longues feuilles de premier plan, à contre-jour. penche : -1 vers la gauche, 1 vers la
    droite. sauf : (x, demi-largeur) à laisser libre."""
    for i in range(int(n * P.s ** 0.7)):
        x = x0 + (x1 - x0) * hz(i, 1, graine)
        if sauf and abs(x - sauf[0]) < sauf[1]:
            continue
        h = haut[0] + (haut[1] - haut[0]) * hz(i, 2, graine)
        pen = penche * (1.5 + 3.5 * hz(i, 3, graine)) + 0.8 * onde(P.p, 0.07 * i)
        coul = (T.N0, T.N1, T.S1, T.N1)[i % 4]
        P.courbe([(x, bas), (x + pen * 0.25, bas - h * 0.5), (x + pen, bas - h)], coul, P.ep(0.4), 1)
        if hz(i, 4, graine) < 0.55:
            qx, qy = x + pen * 0.8, bas - h * 0.86
            P.ell(qx, qy, 0.75, 2.1, T.BR1)
            P.ell(qx + 0.3 * penche, qy - 0.2, 0.3, 1.5, T.BR2)
            P.trait(qx + 0.7 * penche, qy - 1.2, qx + 0.7 * penche, qy + 0.9, T.O2)
        else:
            P.courbe([(x + 0.4, bas), (x + 1.5 + pen * 0.3, bas - h * 0.45), (x + 3.5 + pen, bas - h * 0.6)], coul,
                     P.ep(0.5), 1)


def lucioles(P, points, graine=160):
    """Des lucioles (ou des vers luisants) : chacune s'allume et s'éteint à son rythme, en flottant un peu."""
    for i, (x, y) in enumerate(points):
        ph = (P.p + hz(i, 0, graine)) % 1.0
        if ph > 0.5:
            continue
        x, y = x + 0.5 * onde(P.p, hz(i, 1, graine)), y + 0.4 * onde(P.p, 0.25 + hz(i, 2, graine))
        if 0.1 < ph < 0.4:
            for (ax, ay) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                P.bloc(P.px(x) + ax, P.py(y) + ay, T.OR1)
        P.point(x, y, T.LUM2 if 0.1 < ph < 0.4 else T.LUM)


# ---------------------------------------------------------------------------------------------------------------
# Intérieurs et lumières : ce qui se pose en trame par-dessus, la perspective d'un sol
# ---------------------------------------------------------------------------------------------------------------
MATIERE = False     # vrai : les voiles se mélangent en tons pleins au lieu de se poser en damier (decor(..., matiere=True))


def _tons_en_cours():
    out = set()
    for v in vars(T).values():
        out |= set(v) if isinstance(v, list) else {v}
    return out


def teinte(P, masque, coul, force, niveaux=5, lumiere=False):
    """Mélange une couleur à ce qui est peint, en tons pleins : chaque couleur déjà posée glisse vers `coul` selon la
    force (0..1), et prend le ton le plus proche parmi ceux du décor. Pas de damier : une lumière, une ombre ou une
    brume se lisent comme une matière. Là où le plan est encore vide, la couleur se pose franchement.
    lumiere : la couleur s'ajoute au lieu de se mélanger (une lueur chaude sur un mur froid l'éclaire et le réchauffe,
    elle ne le grise pas) ; elle ne touche alors que ce qui est déjà peint."""
    f = np.broadcast_to(np.asarray(force, dtype=float), P.a.shape)
    plein = masque & (P.a >= 0)
    if plein.any():
        src = sorted({int(v) for v in np.unique(P.a[plein])})
        cand = sorted(set(src) | {int(coul)} | _tons_en_cours())
        rgb = np.array([rvb(PAL[i]) for i in cand], dtype=float)
        but = np.array(rvb(PAL[coul]), dtype=float)
        lut = np.zeros((niveaux + 1, len(PAL)), dtype=np.int16)
        poids = np.array([1.0, 1.2, 0.8])
        for n in range(niveaux + 1):
            for s in src:
                base = np.array(rvb(PAL[s]), dtype=float)
                if lumiere:
                    cible = np.minimum(255.0, base + but * (0.62 * n / niveaux))
                else:
                    cible = base * (1 - n / niveaux) + but * (n / niveaux)
                lut[n, s] = cand[int(np.argmin((((rgb - cible) ** 2) * poids).sum(axis=1)))]
        # la trame ne sert qu'à passer d'un niveau au suivant, sur un tiers du palier
        g = f * niveaux
        niv = np.floor(g)
        niv = niv + (np.clip((g - niv - 0.5) / 0.34 + 0.5, 0, 1) > P.T)
        niv = np.clip(niv, 0, niveaux).astype(np.int64)
        P.a[plein] = lut[niv, np.maximum(P.a, 0)][plein]
    vide = masque & (P.a < 0)
    if vide.any() and not lumiere:
        P.remplir(vide & (f >= 0.3), coul)


def voile(P, masque, coul, force, lumiere=False):
    """Pose une couleur par-dessus ce qui est peint (lumière, ombre, brume) : force 0..1, nombre ou grille. En trame
    par défaut ; en tons pleins (`teinte`) quand le décor est déclaré matiere=True."""
    if MATIERE:
        teinte(P, masque, coul, force, lumiere=lumiere)
        return
    P.remplir(masque & (P.T < force), coul)


def halo(P, x, y, r, coul, force=0.6, ry=None):
    """Une lueur ronde tramée, plus dense au centre."""
    d = np.hypot(P.X - x, (P.Y - y) * (r / (ry or r)))
    voile(P, d < r, coul, force * (1 - d / r), lumiere=True)


def dallage(P, masque, fx, yh, a, b, larg=5.0, prof=1.6, joint=None):
    """Un sol en perspective : des dalles a / b qui fuient vers (fx, yh) ; joint : la couleur des joints."""
    dy = np.maximum(P.Y - yh, 0.25)
    u = (P.X - fx) / dy * 10.0
    z = 60.0 / dy
    cu, cz = np.floor(u / larg), np.floor(z * prof)
    P.remplir(masque & ((cu + cz) % 2 == 0), a)
    P.remplir(masque & ((cu + cz) % 2 != 0), b)
    if joint is not None:
        fu, fz = u / larg - cu, z * prof - cz
        P.remplir(masque & ((fu < 0.06 + 0.012 * dy / 10) | (fz < 0.05)), joint)


def rai(P, x, y0, y1, largeur, pente, coul, force=0.45, grains=18, graine=0, masque=None):
    """Un rai de lumière qui tombe de (x, y0) jusqu'à y1, en biais (pente : unités de x par unité de y), avec sa
    poussière qui scintille et dérive."""
    cx = x + (P.Y - y0) * pente
    m = (P.Y >= y0) & (P.Y <= y1) & (np.abs(P.X - cx) < largeur / 2 * (1 + (P.Y - y0) / 60.0))
    if masque is not None:
        m &= masque
    voile(P, m, coul, force * (1 - 0.6 * np.abs(P.X - cx) / (largeur / 2 * (1 + (P.Y - y0) / 60.0))), lumiere=True)
    for i in range(grains):
        t = (P.p * 0.5 + hz(i, 1, graine)) % 1.0
        y = y0 + (y1 - y0) * ((hz(i, 2, graine) + t * 0.25) % 1.0)
        gx = x + (y - y0) * pente + (hz(i, 3, graine) - 0.5) * largeur * 0.8 + 0.6 * onde(P.p, hz(i, 4, graine))
        if (P.p + hz(i, 5, graine)) % 1.0 < 0.6:
            P.point(gx, y, T.BLANC if hz(i, 6, graine) < 0.4 else coul)


def poussiere(P, x0, y0, x1, y1, n, coul, graine=0):
    """Des grains de poussière en suspension dans une zone."""
    for i in range(n):
        if (P.p + hz(i, 1, graine)) % 1.0 < 0.55:
            P.point(x0 + (x1 - x0) * hz(i, 2, graine) + 0.8 * onde(P.p, hz(i, 4, graine)),
                    y0 + (y1 - y0) * hz(i, 3, graine) + 0.5 * onde(P.p, 0.25 + hz(i, 5, graine)), coul)


def roue(P, x, y, r, dents, coul, clair, sombre, angle=0.0, moyeu=None):
    """Une roue dentée : couronne à dents carrées, rayons, moyeu."""
    dx, dy = P.X - x, P.Y - y
    d = np.hypot(dx, dy)
    a = np.arctan2(dy, dx) + angle
    dent = ((a * dents / (2 * math.pi)) % 1.0) < 0.5
    m = (d < r) | ((d < r * 1.12) & dent)
    P.remplir(m, coul)
    P.remplir(m & (d > r * 0.84) & (dy < -r * 0.3), clair)
    P.remplir((d < r * 0.74) & (d > r * 0.3), sombre)
    for k in range(5):
        b = angle + k * 2 * math.pi / 5
        P.trait(x + r * 0.3 * math.cos(b), y + r * 0.3 * math.sin(b), x + r * 0.76 * math.cos(b), y + r * 0.76 * math.sin(b), coul,
                max(1, P.ep(r * 0.1)))
    P.remplir(d < r * 0.3, coul)
    P.remplir(d < r * 0.12, moyeu if moyeu is not None else clair)


def reflet(P, masque, derriere, axe, force=0.35, etire=1.0, ondule=0.0):
    """Le reflet d'un sol poli : sous la ligne y = axe, chaque pixel du masque reçoit un peu de la couleur qui se trouve à
    la même distance au-dessus (dans `derriere`, Tableau.derriere()), mélangée en tons pleins. force : part du reflet ;
    etire : combien le reflet s'allonge ; ondule : léger flottement horizontal (en pixels) qui suit la boucle."""
    src_y = np.clip(np.floor((axe - (P.Y - axe) / etire - P.y0) * P.s), 0, P.H - 1).astype(np.int64)
    dec = np.round(ondule * np.sin(P.Y * 1.7 + 2 * math.pi * P.p)).astype(np.int64) if ondule else 0
    haut = derriere[src_y, np.clip(P.XI + dec, 0, P.Wt - 1)]
    m = masque & (P.a >= 0) & (haut >= 0) & (P.Y > axe)
    if not m.any():
        return
    code = P.a.astype(np.int64) * 4096 + haut.astype(np.int64)
    cand = sorted({int(v) for v in np.unique(P.a[m])} | {int(v) for v in np.unique(haut[m])} | _tons_en_cours())
    rgb = np.array([rvb(PAL[i]) for i in cand], dtype=float)
    poids = np.array([1.0, 1.2, 0.8])
    for cle in np.unique(code[m]):
        s_, r_ = int(cle) // 4096, int(cle) % 4096
        cible = np.array(rvb(PAL[s_]), dtype=float) * (1 - force) + np.array(rvb(PAL[r_]), dtype=float) * force
        P.a[m & (code == cle)] = cand[int(np.argmin((((rgb - cible) ** 2) * poids).sum(axis=1)))]


# ---------------------------------------------------------------------------------------------------------------
# Petite vie : de quoi peupler un lieu de détails qui bougent (chacun boucle avec P.p)
# ---------------------------------------------------------------------------------------------------------------
def papillon_de_nuit(P, x, y, r=4.0, coul=None, d=0.0):
    """Un papillon de nuit qui tourne autour d'une lumière en (x, y)."""
    coul = T.CREME if coul is None else coul
    a = 2 * math.pi * (P.p + d)
    px_, py_ = x + r * math.cos(a), y + r * 0.6 * math.sin(2 * a)
    ouvert = int((P.p + d) * IMAGES * 2) % 2 == 0
    P.point(px_, py_, T.ENCRE)
    for cote in (-1, 1):
        P.point(px_ + cote * 0.5, py_ - (0.5 if ouvert else 0.0), coul, 2 if ouvert else 1)


def araignee(P, x, y, l=8.0, coul=None, d=0.0):
    """Une araignée au bout de son fil, pendue en (x, y) : elle descend et remonte."""
    coul = T.ENCRE if coul is None else coul
    bas = y + l * (0.6 + 0.4 * onde(P.p, d))
    P.trait(x, y, x, bas, T.CREME)
    P.ell(x, bas + 0.6, 0.8, 0.7, coul)
    for cote in (-1, 1):
        P.trait(x, bas + 0.4, x + cote * 1.4, bas - 0.2 + 0.3 * onde(P.p * 2, d), coul)
        P.trait(x, bas + 0.8, x + cote * 1.4, bas + 1.4, coul)


def toile_araignee(P, x, y, r, sens=(1, 1), coul=None):
    """Une toile dans un coin (x, y), ouverte vers sens ; une perle de rosée y scintille."""
    coul = T.CREME if coul is None else coul
    for k in range(4):
        a = k * math.pi / 6
        P.trait(x, y, x + sens[0] * r * math.cos(a), y + sens[1] * r * math.sin(a), coul)
    for rr in (0.4, 0.7, 1.0):
        pts = [(x + sens[0] * r * rr * math.cos(k * math.pi / 6), y + sens[1] * r * rr * math.sin(k * math.pi / 6)) for k in range(4)]
        for q in range(3):
            P.trait(pts[q][0], pts[q][1], pts[q + 1][0], pts[q + 1][1], coul)
    if (P.p * 2) % 1.0 < 0.4:
        P.point(x + sens[0] * r * 0.6, y + sens[1] * r * 0.4, T.BLANC)


def goutte(P, x, y0, y1, coul=None, d=0.0, flaque=None):
    """Une goutte qui tombe de y0 à y1, et le rond qu'elle fait en arrivant."""
    coul = T.BLEU if coul is None else coul
    t = (P.p + d) % 1.0
    if t < 0.6:
        P.trait(x, y0 + (y1 - y0) * (t / 0.6) ** 2, x, y0 + (y1 - y0) * (t / 0.6) ** 2 + 0.8, coul)
    else:
        u = (t - 0.6) / 0.4
        dd = np.hypot(P.X - x, (P.Y - y1) * 3.0)
        P.remplir(np.abs(dd - 0.6 - 3.0 * u) < 0.3, flaque if flaque is not None else coul)


def souris(P, x, y, sens=1, coul=None):
    """Une souris (la bête, pas le curseur) : elle fait sa toilette, remue le nez, sa queue bat."""
    coul = T.P1 if coul is None else coul
    P.ell(x, y - 1.2, 2.0, 1.3, coul)
    P.ell(x + sens * 1.8, y - 1.6 - (0.4 if int(P.p * IMAGES) % 4 == 0 else 0), 1.1, 0.9, coul)
    P.ell(x + sens * 1.5, y - 2.6, 0.6, 0.6, T.P3)
    P.point(x + sens * 2.2, y - 1.8, T.ENCRE)
    P.point(x + sens * 2.9, y - 1.4, T.O3)
    P.courbe([(x - sens * 1.8, y - 0.8), (x - sens * 3.4, y - 0.4 - 0.8 * onde(P.p)), (x - sens * 4.6, y - 1.4 - 0.6 * onde(P.p, 0.2))], T.P3, 1)


def vapeur(P, x, y, coul=None, h=10.0, n=3, d=0.0):
    """Une vapeur qui monte en volutes de (x, y) : tasse, soupe, bouche d'aération."""
    coul = T.CREME if coul is None else coul
    for k in range(n):
        t = (P.p + d + k / n) % 1.0
        m = np.hypot(P.X - (x + 1.3 * math.sin(t * 6.0 + k)), P.Y - (y - h * t)) < 0.6 + 1.3 * t
        P.remplir(m & (P.T > t * 0.9 + 0.05), coul)


def avion_papier(P, x0, y0, x1, y1, coul=None, d=0.0):
    """Un avion de papier qui plane de (x0, y0) à (x1, y1), en feston."""
    coul = T.BLANC if coul is None else coul
    t = (P.p + d) % 1.0
    x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t + 2.5 * math.sin(t * 2 * math.pi * 2)
    s = 1 if x1 > x0 else -1
    P.poly([(x, y), (x - s * 4.0, y - 1.4), (x - s * 3.0, y + 0.2), (x - s * 4.0, y + 1.2)], coul)
    P.trait(x, y, x - s * 3.0, y + 0.2, T.P3)


def etincelle(P, x, y, coul=None, d=0.0):
    """Une étincelle qui claque de temps en temps (un contact qui ne tient plus)."""
    coul = T.LUM2 if coul is None else coul
    t = (P.p + d) % 1.0
    if t < 0.25:
        r = 1.0 + 4.0 * t
        for k in range(6):
            a = k * math.pi / 3 + d * 7
            P.point(x + r * math.cos(a), y + r * math.sin(a), coul if k % 2 else T.BLANC)
        P.point(x, y, T.BLANC, 2)


def yeux(P, x, y, coul=None, d=0.0, ecart=2.0):
    """Deux yeux dans le noir : ils clignent, ils regardent ailleurs."""
    coul = T.LUM2 if coul is None else coul
    t = (P.p + d) % 1.0
    if t < 0.82:
        dx = 0.4 if t > 0.5 else 0.0
        P.point(x + dx, y, coul)
        P.point(x + ecart + dx, y, coul)


# ---------------------------------------------------------------------------------------------------------------
# Choses toutes faites (reprises de l'étude)
# ---------------------------------------------------------------------------------------------------------------


def arbre_rond(P, x, y, r, graine, tronc=1.6):
    P.trait(x, y, x, y - tronc, T.BR1, P.ep(0.35))
    b = [(x + (hz(i, 1, graine) - 0.5) * r * 1.3, y - tronc - r * 0.6 - (hz(i, 2, graine) - 0.3) * r * 0.9,
          r * (0.55 + 0.35 * hz(i, 3, graine))) for i in range(5)]
    cote = 1.0 if x < P.soleil[0] else -1.0
    P.volumes(b, [T.S0, T.S1, T.S2, T.S3, T.OR1], (0.75 * cote, -0.35, 0.25), grain=0.35, graine=graine, gain=0.6, base=0.34)


def maison(P, hx, gy, p, grande=True):
    k = 1.0 if grande else 0.62
    w, h = 9.0 * k, 5.2 * k
    # Mur : la face droite prend le soleil, la gauche est dans l'ombre.
    P.rect(hx - w / 2, gy - h, w, h + 0.4, T.M4)
    P.rect(hx - w / 2, gy - h, w * 0.36, h + 0.4, T.M3)
    P.rect(hx - w / 2, gy - h, max(1.0 / P.s, w * 0.09), h + 0.4, T.M2)
    P.rect(hx - w / 2, gy - 0.5 * k, w, 0.9 * k, T.P1)                           # soubassement de pierre
    # Toit violet, pan éclairé à droite ; rangs de tuiles dès que la grille le permet.
    toit = [(hx - w / 2 - 1.1 * k, gy - h), (hx - w * 0.28, gy - h - 3.6 * k), (hx + w * 0.28, gy - h - 3.6 * k),
            (hx + w / 2 + 1.1 * k, gy - h)]
    mt = P.poly(toit, T.D1)
    P.remplir(mt & (P.X > hx + w * 0.1), T.D2)
    rang = (np.floor((P.Y - gy) * P.s / 2.0) % 2 == 0) & (((P.XI + (np.floor((P.Y - gy) * P.s / 2.0) % 4)) % 3) == 0)
    P.remplir(mt & rang, T.CIEL[1])
    P.remplir(P.crete(mt) & (P.X > hx - w * 0.3), T.L3)
    # Cheminée.
    chx, chy = hx + w * 0.2, gy - h - 4.9 * k
    P.rect(chx, chy, 1.3 * k, 2.6 * k, T.P1)
    P.rect(chx + 0.8 * k, chy, max(1.0 / P.s, 0.5 * k), 2.6 * k, T.P3)
    # Porte ronde bleu-violet, fenêtres qui s'allument (elles vacillent).
    P.rect(hx - 0.9 * k, gy - 3.0 * k, 1.8 * k, 3.0 * k, T.D2)
    P.ell(hx, gy - 3.0 * k, 0.9 * k, 0.9 * k, T.D2)
    P.point(hx + 0.45 * k, gy - 1.5 * k, T.LUM)
    for i, fx in enumerate((hx - w * 0.36, hx + w * 0.22)):
        vive = ((p * 2 + 0.37 * i) % 1.0) < 0.5
        P.rect(fx, gy - 3.9 * k, 1.7 * k, 1.8 * k, T.LUM2 if vive else T.LUM)
        P.rect(fx, gy - 3.9 * k, 1.7 * k, 1.0 / P.s, T.O2)
        P.trait(fx + 0.85 * k, gy - 3.9 * k, fx + 0.85 * k, gy - 2.2 * k, T.BR2)
        if FIN:
            P.trait(fx, gy - 3.0 * k, fx + 1.6 * k, gy - 3.0 * k, T.BR2)
            P.rect(fx - 0.2, gy - 2.1 * k, 1.7 * k + 0.4, 1.0 / P.s, T.P3)        # appui de fenêtre
    return chx + 0.6 * k, chy


def fumee(P, x, y, p):
    for i in range(6):
        age = (p + i / 6.0) % 1.0
        fx, fy = x + 5.5 * age ** 1.3 + 0.5 * math.sin(age * 7 + i), y - 10.5 * age
        r = 0.45 + 1.5 * age
        m = ((P.X - fx) ** 2 + (P.Y - fy) ** 2 <= r * r) & (P.T > age * 0.95 - 0.08)
        P.remplir(m, T.L5 if age < 0.5 else T.L4)
        if age < 0.55:
            P.ell(fx + r * 0.3, fy + r * 0.2, r * 0.45, r * 0.45, T.CIEL[10], cond=P.T > age)


def nenuphar(P, x, y, r, graine, fleur=None):
    ry = r * 0.36
    P.ell(x, y + 0.5, r * 0.98, ry, T.EAU[0])                                      # son ombre sur l'eau
    ang = 2 * math.pi * hz(graine, 1, 3)
    u, w = (P.X - x) / r, (P.Y - y) / ry
    a = np.arctan2(w, u)
    fente = np.abs(((a - ang + math.pi) % (2 * math.pi)) - math.pi) < 0.22
    m = (u * u + w * w <= 1) & ~fente
    P.rampe(m, 0.48 - 0.38 * w - 0.2 * u + 0.25 * (fbm(P.X * 1.3, P.Y * 2.0, 2, graine) - 0.5), [T.S1, T.S2, T.S3, T.S4], 0.6)
    bord = m & (u * u + w * w > (1 - 1.6 / (r * P.s)) ** 2) & (w < -0.1) & (u < 0.3)
    P.remplir(bord, T.OR2)                                                         # le bord qui prend le couchant
    if r > 3:
        for k in range(5):
            b = ang + 0.6 + k * 1.15
            P.trait(x, y, x + r * 0.8 * math.cos(b), y + ry * 0.8 * math.sin(b), T.S2)
    if fleur is not None:
        fx, fy = x + r * 0.35, y - ry * 0.2
        t = max(0.5, 0.42 * r)
        for b in range(5):
            P.ell(fx + t * 0.9 * math.cos(b * 1.26 + 0.3), fy - t * 0.3 + t * 0.45 * math.sin(b * 1.26 + 0.3), t * 0.5,
                  t * 0.36, fleur)
        P.ell(fx, fy - t * 0.45, t * 0.5, t * 0.45, T.CREME if fleur != T.CREME else T.SOL)
        P.point(fx, fy - t * 0.45, T.OR2)


def grenouille(P, x, y, p):
    k = 1.0
    cligne = 0.80 < p < 0.92
    P.ell(x, y, 2.7 * k, 2.0 * k, T.S2)
    P.ell(x + 0.2, y - 0.3, 2.3 * k, 1.6 * k, T.S3)
    P.ell(x, y + 0.8, 1.7 * k, 1.1 * k, T.CREME)
    P.ell(x - 2.4, y + 1.3, 1.1, 0.7, T.S2)
    P.ell(x + 2.4, y + 1.3, 1.1, 0.7, T.S2)
    for cote in (-1, 1):
        ex, ey = x + cote * 1.35, y - 1.9
        P.ell(ex, ey, 1.05, 1.05, T.S3)
        if cligne:
            P.trait(ex - 0.6, ey, ex + 0.6, ey, T.S1)
        else:
            P.ell(ex, ey, 0.7, 0.7, T.CREME)
            P.ell(ex + 0.15, ey + 0.05, 0.38, 0.45, T.ENCRE)
            if FIN:
                P.point(ex - 0.2, ey - 0.3, T.BLANC)
    P.trait(x - 1.2, y - 0.2, x + 1.2, y - 0.2, T.S1)
    P.point(x - 1.4, y - 0.4, T.S1)
    P.point(x + 1.3, y - 0.4, T.S1)
    for (dx, dy) in ((-1.5, -1.0), (0.9, -1.2), (1.8, 0.2)):
        P.point(x + dx, y + dy, T.S4)
    P.trait(x - 1.9, y - 1.3, x - 0.8, y - 2.9, T.S4)                          # liseré du couchant sur le dos


def barque(P, x, y, p):
    y = y + 0.25 * onde(p, 0.1)
    P.poly([(x - 6.2, y - 1.1), (x + 6.6, y - 1.3), (x + 5.0, y + 1.0), (x - 4.8, y + 1.0)], T.BR1)
    P.poly([(x - 5.6, y - 0.9), (x + 5.9, y - 1.1), (x + 4.8, y + 0.3), (x - 4.6, y + 0.3)], T.BR2)
    P.trait(x - 6.2, y - 1.2, x + 6.6, y - 1.4, T.M2)
    P.trait(x - 6.2, y - 1.2, x - 3.0, y - 1.25, T.OR2)
    P.rect(x - 1.0, y - 1.0, 2.0, 0.6, T.M3)
    P.trait(x + 2.0, y - 1.6, x + 8.5, y + 0.6, T.M2)                              # la rame, posée
    P.ell(x + 8.6, y + 0.7, 0.9, 0.4, T.M3)
    P.trait(x - 4.6, y + 0.3, x + 4.8, y + 0.3, T.BR1)
    P.trait(x - 6.2, y - 1.0, x - 9.6, y - 2.0, T.M3)                              # l'amarre
    P.rect(x - 10.2, y - 3.4, 0.9, 4.6, T.BR1)
    P.point(x - 10.2, y - 3.4, T.OR2)
    # Reflet : des tirets sombres sous la coque.
    for i in range(4):
        d = 0.5 * onde(p, 0.25 * i)
        P.trait(x - 4.6 + i * 0.6 + d, y + 1.3 + i * 0.6, x + 4.6 - i * 0.9 + d, y + 1.3 + i * 0.6, T.EAU[0])
