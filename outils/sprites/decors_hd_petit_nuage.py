"""Décors haute définition de « Petit Nuage » (480 × 240), peints avec paysage.py.

Du jardin aux montagnes, sous des ciels qui changent : ciels lavés d'après l'orage, soirs lavande et pêche, aubes roses,
neige blanche et bleutée, roches ardoise, herbes sarcelle, prés jaunes, mélèzes dorés, terre claire, une lampe orange.
Pas de vert : les feuillages sont sarcelle, l'automne est doré. Les montagnes ont un versant éclairé, un versant d'ombre
et la neige en crête ; les deux sommets en forme de dents, avec leur col arrondi, reviennent de lieu en lieu.

Coordonnées : unités du monde (x de 0 à 192, y de -16 à 80). Places et clés : assets/scenes/petit-nuage.txt.
"""
import math

import numpy as np

import paysage as pg
from decors_hd import decor
from paysage import Tons, cs, hz, onde, voile, halo, dallage, rai, poussiere

NE1, NE2, NE3, NE4 = cs("#93aacb", "#c3d3e6", "#e6eef7", "#ffffff")
R1, R2, R3, R4 = cs("#3c4252", "#5c6478", "#8790a4", "#b5bccb")
PJ1, PJ2, PJ3, PJ4 = cs("#8a6e2a", "#c9a64a", "#e8cf7a", "#f6e6a8")
ME1, ME2 = cs("#b8742a", "#e0a040")
TE1, TE2, TE3 = cs("#6b4a2e", "#a07a52", "#d8bd92")
BO1, BO2, BO3 = cs("#3b2616", "#5e3c22", "#8a5a33")
LA1, LA2, LA3 = cs("#f69d50", "#ffd29a", "#fff1c9")
ENCRE, NU1, NU2 = cs("#161a26", "#0f1a33", "#1d2c55")
RO1, RO2 = cs("#8a4a1f", "#b8652e")
BLANC = NE4
CREME = cs("#fff6e6")[0]

_COMMUN = dict(
    loin=("#5c6478", "#8790a4", "#93aacb", "#b5bccb", "#c3d3e6", "#e6eef7"),
    herbe=("#0e2a40", "#123f52", "#1d6578", "#2f8f9c", "#5bb3ae"),
    or_=("#c9a64a", "#e8cf7a", "#f6e6a8"), nuit=("#161a26", "#0f1a33", "#1d2c55"),
    bois=("#3b2616", "#5e3c22", "#8a5a33", "#d8bd92", "#f2e6cc"), toit=("#3c4252", "#5c6478"), pierre=("#8790a4", "#c3d3e6"),
    orange=("#b8652e", "#f69d50"), lueur=("#ffd29a", "#fff1c9"), creme="#fff6e6", encre="#161a26", violet="#8a79b8", bleu="#8fb6d8")
EAU_CLAIRE = ("#1b3550", "#234566", "#2c5577", "#3d6a8f", "#4f7fa6", "#6f9bc0", "#8fb6d8", "#b5cfe6", "#dbe9f5")
EAU_SOMBRE = ("#0f1a33", "#16264a", "#1d2c55", "#2c4070", "#3f5688", "#5c6fa0", "#7d88b4", "#a3a5c6", "#c9c0d4")
LAVE = Tons(ciel=("#7fb0df", "#8ebae3", "#9cc3e8", "#accdec", "#bcd7ef", "#cce0f2", "#dbe9f5", "#e6eff8", "#f2f6fb", "#f8f6f0",
                  "#fdf4e4", "#fff8ec"), eau=EAU_CLAIRE, soleil="#fffdf4", **_COMMUN)
SOIR = Tons(ciel=("#3f3f7c", "#4d4b8b", "#5c5a9a", "#7369a9", "#8a79b8", "#b08eb6", "#d9a3b5", "#e8b5aa", "#f5c8a0", "#f9d6ad",
                  "#fde4bd", "#fff1c9"), eau=EAU_SOMBRE, soleil="#fff6d8", **_COMMUN)
ROSE = Tons(ciel=("#7f98cc", "#93a8d6", "#a8b8de", "#bcc6e4", "#d0cde4", "#e0cfe0", "#e8c8d8", "#f0d0d4", "#f8dcc8", "#fbe6d2",
                  "#fdf0e0", "#fff8ee"), eau=EAU_CLAIRE, soleil="#fffaf0", **_COMMUN)
NUIT = Tons(ciel=("#0b1226", "#0f1a33", "#162244", "#1d2c55", "#2a3b6c", "#3b4f85", "#51679c", "#6c82b2", "#8a9fc6", "#a9bad8",
                  "#c3d3e6", "#e6eef7"), eau=EAU_SOMBRE, soleil="#fff1c9", **_COMMUN)


# ---------------------------------------------------------------------------------------------------------------
# Ce qui revient de lieu en lieu
# ---------------------------------------------------------------------------------------------------------------
def _a(x):
    return np.asarray(x, dtype=float)


def sommets(P, f, rampe, neige=5.0, graine=0, limite=None, bas=None):
    """Une chaîne de montagnes sous la courbe f : versants de roche (rampe de 4 tons), la neige en crête, plus épaisse
    dans les creux ; limite : au-dessus de ce y tout est neige."""
    m = pg.crete(P, f, rampe, pente=0.9, fond=14.0, bas=bas)
    fx = f(P.X)
    prof = P.Y - fx
    cote = np.where(P.X < P.soleil[0], 1.0, -1.0)
    xs = P.X + prof * 0.9 * cote
    versant = (f(xs + 0.7) - f(xs - 0.7)) * cote > 0
    n = neige * (0.5 + 0.9 * pg.fbm(P.X / 5.0, P.Y / 3.0, 3, 700 + graine))
    blanc = m & ((prof < n) | ((limite is not None) & (P.Y < (limite if limite is not None else 0) + 3 * np.sin(P.X / 7.0))))
    P.remplir(blanc & versant, NE4)
    P.remplir(blanc & ~versant, NE2)
    P.remplir(blanc & ~versant & (P.T < 0.3), NE1)
    return m


def deux_dents(x):
    """Les deux sommets en forme de dents, un col arrondi entre eux : le repère du voyage."""
    x = _a(x)
    g = 32.0 * np.maximum(0, 1 - np.abs(x - 74) / 36.0) ** 0.9
    d = 37.0 * np.maximum(0, 1 - np.abs(x - 124) / 40.0) ** 0.9
    col = 16.0 * np.exp(-((x - 99) / 18.0) ** 2)
    return 46.0 - np.maximum(np.maximum(g, d), col) - 3.0 * pg.fbm(x / 7.0, x * 0, 3, 710)


def meleze(P, x, y, h, graine=0, dore=True):
    """Un mélèze : tronc fin, étages de branches qui retombent ; doré à l'automne, il perd ses aiguilles."""
    T = pg.T
    P.trait(x, y, x, y - h, BO1, P.ep(0.5 + h / 40.0))
    tons = (PJ1, PJ2, PJ3, ME2) if dore else (T.S0, T.S1, T.S2, T.S3)
    n = int(5 + h / 4)
    for i in range(n):
        u = i / (n - 1.0)
        yy = y - h * (0.18 + 0.82 * u)
        l = h * 0.3 * (1 - u) + 0.8
        bal = 0.2 * onde(P.p, (x + i) * 0.07)
        for cote in (-1, 1):
            P.poly([(x, yy - 0.8), (x + cote * l + bal, yy + l * 0.34), (x + cote * l * 0.6 + bal, yy + l * 0.42), (x, yy + 1.0)],
                   tons[(i + (cote > 0)) % 2 + (1 if cote * (P.soleil[0] - x) > 0 else 0)])
        P.point(x + (hz(i, 1, graine) - 0.5) * l, yy + l * 0.3, tons[3])


def aiguilles(P, x0, y0, x1, y1, n, graine=0):
    """Les aiguilles d'or qui tombent : de petits traits qui descendent en biais."""
    for i in range(n):
        t = (P.p + hz(i, 1, graine)) % 1.0
        x, y = x0 + (x1 - x0) * hz(i, 2, graine) - 6 * t, y0 + (y1 - y0) * ((hz(i, 3, graine) + t * 0.5) % 1.0)
        P.trait(x, y, x - 0.6, y + 0.9, PJ3 if i % 2 else ME2)


def petit_nuage(P, x, y, l, h, graine, boit=False, tons=None, yeux=True):
    """Un nuage du troupeau : rond, blanc, deux yeux ; s'il boit, son ventre est posé sur l'eau et ses yeux sont fermés."""
    lum = (0.3 if P.soleil[0] > x else -0.3, -0.6, 0.4)
    P.volumes(pg.amas(x, y, l, h, graine, max(3, int(l / 3.2))), tons or [NE1, NE2, NE3, NE4, BLANC], lum, plancher=y + h * 0.12,
              grain=0.12, graine=graine, gain=0.55, base=0.62, trame=0.5)
    if yeux and l > 7:
        ex = x + (hz(graine, 1, 720) - 0.5) * l * 0.2
        ey = y - h * 0.34
        for dx in (-l * 0.1, l * 0.1):
            if boit or (P.p + hz(graine, 2, 720)) % 1.0 > 0.9:
                P.trait(ex + dx - 0.5, ey, ex + dx + 0.5, ey, R1)
            else:
                P.point(ex + dx, ey, R1, 2 if l > 12 else 1)


def flaque(P, x, y, rx, ry=None, graine=0):
    """Une flaque qui reflète le ciel : un bord sombre, le clair du ciel dedans, parfois un rond."""
    T = pg.T
    ry = ry or rx * 0.22
    P.ell(x, y, rx, ry, T.EAU[2])
    P.ell(x, y - ry * 0.15, rx * 0.9, ry * 0.75, T.EAU[6])
    P.ell(x - rx * 0.2, y - ry * 0.3, rx * 0.5, ry * 0.3, T.EAU[8])
    t = (P.p + hz(graine, 1, 730)) % 1.0
    if t < 0.6:
        d = np.hypot(P.X - x - rx * 0.3, (P.Y - y) * rx / ry)
        P.remplir((np.abs(d - rx * 0.7 * t) < 0.4) & (d < rx * 0.86), BLANC)


def cairn(P, x, y, k=1.0, neige=True):
    """Un cairn : des pierres plates empilées, coiffées de neige."""
    for i, (w, h) in enumerate(((5.0, 2.2), (4.0, 2.0), (3.2, 1.8), (2.2, 1.6), (1.4, 1.4))):
        yy = y - i * 1.9 * k
        P.ell(x + (i % 2) * 0.4 * k, yy - h * 0.5 * k, w * 0.5 * k, h * 0.55 * k, R2 if i % 2 else R3)
        P.ell(x - w * 0.12 * k, yy - h * 0.7 * k, w * 0.3 * k, h * 0.2 * k, R4)
    if neige:
        P.ell(x + 0.2 * k, y - 9.6 * k, 1.4 * k, 0.9 * k, NE4)
        P.ell(x, y + 0.2, 4.0 * k, 0.9 * k, NE3)


def bocal(P, x, y, w, h, contenu, graine=0, lueur=False):
    """Un bocal sur son étagère : verre, couvercle de toile ficelé, une étiquette manuscrite ; lueur : il brille."""
    if lueur:
        halo(P, x, y - h * 0.5, w * 1.6 + 2, contenu, 0.4 + 0.12 * onde(P.p, hz(graine, 1, 740)))
    P.rect(x - w / 2, y - h, w, h, NE1)
    P.rect(x - w / 2 + 0.4, y - h * 0.82, w - 0.8, h * 0.82 - 0.4, contenu)
    P.rect(x - w / 2 + 0.4, y - h * 0.82, max(0.4, w * 0.18), h * 0.82 - 0.4, NE3)
    P.rect(x - w / 2 - 0.3, y - h - 0.8, w + 0.6, 1.2, TE3)
    P.rect(x - w / 2 - 0.3, y - h + 0.3, w + 0.6, 0.4, BO2)
    if w > 3:
        P.rect(x - w * 0.3, y - h * 0.5, w * 0.6, h * 0.24, CREME)
        P.rect(x - w * 0.2, y - h * 0.42, w * 0.36, 0.4, BO2)


def brume_claire(P, y, ep, g, coul, force=0.6, x0=-10, x1=202):
    d = pg.fbm((P.X + 2.5 * onde(P.p, 0.13 * g)) / 26.0, P.Y / 5.0, 3, 750 + g)
    voile(P, (np.abs(P.Y - y - 2.5 * np.sin(P.X / 21.0 + g)) < ep * (0.5 + 0.9 * d)) & (P.X > x0) & (P.X < x1), coul, force)


# =====================================================================================================================
# Le jardin après l'orage : un fond de jardin au petit matin. Herbe couchée et luisante, flaques, un arrosoir renversé
# (la clé), un pot de fleurs retourné, un massif de ronces mouillées au fond, lumière lavée, ciel très pâle.
# =====================================================================================================================
@decor("petit-nuage", "jardin-lave", soleil=(34.0, 4.0), tons=LAVE, nom="Le jardin après l'orage")
def jardin_lave(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=44.0, haut=0.0, halo=0.3, disque=4.6)
    # Un arc-en-ciel pâle (sans rouge ni vert : orange, crème, bleu, violet), qui s'efface.
    d = np.hypot(X - 150.0, (Y - 60.0) * 1.1)
    for i, c0 in enumerate((LA2, T.CIEL[11], T.BLEU, T.VIOLET)):
        voile(P, (np.abs(d - 72.0 + i * 1.6) < 0.8) & (Y < 44), c0, 0.34 + 0.06 * onde(p))
    tab.plan("nuages", 0.08)
    pg.cumulus(P, [(150, 6, 46, 8.0, 760, 9, 0.0), (70, -6, 34, 5.5, 761, 7, 0.4), (16, 16, 22, 3.6, 762, 5, 0.7)], dessous=-0.5)
    pg.voiles(P, y=26.0, epais=8.0, seuil=0.6, graine=763)
    tab.plan("lointains", 0.2)
    sommets(P, lambda x: deux_dents(x) + 10.0, [T.L2, T.L3, T.L4, T.L5], neige=3.0, graine=1)
    pg.crete(P, lambda x: pg.profil(x, 46.0, 7.0, 22.0, 764), [T.L1, T.L2, T.L3, T.L4], 0.5)
    brume_claire(P, 44.0, 4.0, 1, T.CIEL[10], 0.5)
    tab.plan("moyen", 0.5)
    # ---- Le fond du jardin : la palissade, le massif de ronces mouillées (des gouttes y brillent), un pommier.
    f_pre = lambda x: 48.0 + 1.5 * np.sin(_a(x) / 15.0) + 0.5 * np.sin(_a(x) / 4.0)
    pg.pre(P, f_pre, [T.S1, T.S2, T.S3, T.S4], clair=0.7, graine=765, pente=0.03)
    for x in np.arange(-6.0, 198.0, 5.0):                        # la palissade, une planche de travers
        h = 10 + 1.5 * hz(int(x), 1, 766)
        pen = 1.6 if int(x) % 35 == 4 else 0.0
        P.poly([(x, 50.0), (x + 4.0, 50.0), (x + 4.0 + pen, 50.0 - h), (x + 2.0 + pen, 50.0 - h - 2.0), (x + pen, 50.0 - h)], TE2)
        P.poly([(x, 50.0), (x + 1.0, 50.0), (x + 1.0 + pen, 50.0 - h), (x + pen, 50.0 - h)], TE3)
    P.rect(-6.0, 42.0, 204.0, 1.0, TE1)
    ronces = [(110 + 9 * i + 4 * hz(i, 1, 767), 49 - 3 * hz(i, 2, 767), 5 + 3 * hz(i, 3, 767)) for i in range(10)]
    P.volumes(ronces, [T.S0, T.S1, T.S2, T.S3], (-0.6, -0.5, 0.4), plancher=52.0, grain=1.0, graine=768, gain=0.6, base=0.4, trame=0.8)
    for i in range(26):
        x, y = 108 + 88 * hz(i, 1, 769), 42 + 9 * hz(i, 2, 769)
        P.point(x, y, T.VIOLET if i % 3 else NU2, 2)             # des mûres
        if (p + hz(i, 3, 769)) % 1.0 < 0.3:
            P.point(x + 1.0, y - 1.0, BLANC)                    # une goutte qui brille
    pg.arbre_rond(P, 24.0, 50.0, 6.0, 770, tronc=7.0)
    for i in range(5):
        P.ell(18 + 3 * i + (i % 2), 40 + (i % 3) * 2, 0.9, 0.9, LA1)                          # des pommes
    for i in range(4):                                          # l'arbre s'égoutte
        t = (p + i / 4.0) % 1.0
        P.point(19 + i * 3.4, 44 + 8 * t * t, T.EAU[7])
    # ---- La pelouse : l'herbe couchée par la pluie, luisante ; les flaques qui gardent le ciel.
    f_sol = lambda x: 56.0 + 0.8 * np.sin(_a(x) / 17.0)
    sol = Y > f_sol(X)
    couche = pg.fbm((X + (Y - 56) * 1.6) / 9.0, Y / 2.0, 3, 771)
    P.rampe(sol, 0.5 + 0.5 * (couche - 0.5) + 0.004 * (X - 96) - 0.008 * (Y - 56), [T.S0, T.S1, T.S2, T.S3, T.S4], 0.8)
    voile(P, sol & (pg.fbm((X + (Y - 56) * 1.6) / 2.4, Y / 5.0, 2, 772) > 0.7), T.CIEL[9], 0.4)   # les brins mouillés qui luisent
    for i, (x, y, rx) in enumerate(((66.0, 62.0, 12.0), (100.0, 70.0, 16.0), (22.0, 68.0, 9.0), (176.0, 66.0, 10.0), (140.0, 77.0, 9.0))):
        flaque(P, x, y, rx, graine=i)
    # L'arrosoir renversé (il se vide encore), le pot retourné et son géranium, un râteau oublié.
    ax, ay = 142.0, 72.0
    P.ell(ax, ay + 0.8, 16.0, 2.0, T.S0)
    P.poly([(ax - 10, ay - 12), (ax + 8, ay - 14), (ax + 10, ay - 1), (ax - 12, ay + 0.6)], R3)
    P.rampe(P.masque_poly([(ax - 10, ay - 12), (ax + 8, ay - 14), (ax + 10, ay - 1), (ax - 12, ay + 0.6)]),
            0.3 + 0.045 * (ay - Y) + 0.2 * (pg.fbm(X / 3.0, Y / 2.0, 2, 773) - 0.5), [R2, R3, R4, NE3], 0.6)
    P.ell(ax - 11, ay - 5.6, 2.4, 6.4, R2)                       # l'ouverture
    P.ell(ax - 11, ay - 5.6, 1.6, 5.2, ENCRE)
    P.poly([(ax + 9, ay - 8), (ax + 22, ay - 15), (ax + 23, ay - 13), (ax + 10, ay - 5)], R3)   # le bec
    P.ell(ax + 23.4, ay - 14.4, 1.6, 2.4, R2)
    for k in range(5):
        t = (p + k / 5.0) % 1.0
        P.point(ax + 24.6 + 1.6 * t, ay - 14.0 + 13.0 * t * t, T.EAU[7] if k % 2 else BLANC)
    P.courbe([(ax - 4, ay - 13.4), (ax, ay - 20.0), (ax + 6, ay - 14.2)], R2, P.ep(0.9))        # l'anse
    flaque(P, ax + 26.0, ay + 0.4, 5.0, graine=9)
    P.poly([(84.0, 62.0), (96.0, 60.0), (93.0, 70.0), (87.0, 71.0)], RO2)                      # le pot retourné
    P.poly([(84.0, 62.0), (96.0, 60.0), (95.6, 62.0), (84.6, 64.0)], RO1)
    P.ell(98.0, 70.0, 5.0, 1.4, TE1)                             # sa terre répandue
    P.trait(97.0, 69.0, 104.0, 65.0 + 0.3 * onde(p), T.S2)
    P.ell(104.6, 64.6 + 0.3 * onde(p), 1.6, 1.4, LA1)
    P.trait(54.0, 58.0, 76.0, 54.0, BO2, P.ep(0.6))               # le râteau
    for i in range(5):
        P.trait(52.0 + i * 0.9, 56.0 + i * 0.9, 51.4 + i * 0.9, 58.4 + i * 0.9, R2)
    for i in range(3):                                          # des vers sortis de terre, un escargot
        P.courbe([(116 + i * 22, 75.0 + i), (118 + i * 22, 74.2 + i + 0.3 * onde(p, 0.3 * i)), (120.4 + i * 22, 75.0 + i)], LA1, 1)
    tab.plan("premier", 1.0)
    # ---- Premier plan : de grandes feuilles lourdes d'eau, à gauche et à droite ; les gouttes qui s'en détachent.
    for (x0, cote, g) in ((-6.0, 1, 774), (198.0, -1, 775)):
        for i in range(5):
            a = -1.3 + i * 0.3 + 0.03 * onde(p, 0.1 * i)
            l = 22 + 8 * hz(i, 1, g)
            bx_, by_ = x0 + cote * l * math.cos(a) * 0.9, 82.0 + l * math.sin(a)
            P.poly([(x0, 82.0), (x0 + cote * l * 0.5 * math.cos(a) - 3, 82.0 + l * 0.5 * math.sin(a) - 2), (bx_, by_),
                    (x0 + cote * l * 0.5 * math.cos(a) + 3, 82.0 + l * 0.5 * math.sin(a) + 3)], T.S0 if i % 2 else T.S1)
            P.trait(x0, 82.0, bx_, by_, T.S3)
            t = (p + hz(i, 2, g)) % 1.0
            P.point(bx_, by_ + 14 * t * t, T.EAU[8] if t < 0.8 else T.S3)
    pg.touffes(P, lambda x: 78.6 + 0.0 * _a(x), n=60, haut=2.4, graine=776)
    poussiere(P, 20, 0, 180, 50, 12, T.CIEL[11], 777)


# =====================================================================================================================
# Le chemin creux : un chemin de terre claire entre deux haies basses de noisetiers, à hauteur d'herbe. Ornières sèches,
# soleil d'automne haut et blanc, une ligne de montagnes blanches très loin au bout.
# =====================================================================================================================
@decor("petit-nuage", "chemin-creux", soleil=(120.0, -6.0), tons=LAVE, nom="Le chemin creux")
def chemin_creux(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=40.0, haut=0.1, halo=0.36, disque=4.8)
    tab.plan("nuages", 0.08)
    pg.cumulus(P, [(40, 8, 40, 6.5, 780, 8, 0.0), (168, 14, 30, 5.0, 781, 6, 0.5)], dessous=-0.5)
    tab.plan("lointains", 0.2)
    sommets(P, lambda x: deux_dents(x) + 6.0, [T.L2, T.L3, T.L4, T.L5], neige=9.0, graine=2, limite=30.0)
    pg.crete(P, lambda x: pg.profil(x, 44.0, 6.0, 26.0, 782), [T.L1, T.L2, T.L3, T.L4], 0.5)
    brume_claire(P, 42.0, 3.0, 2, T.CIEL[10], 0.5)
    tab.plan("moyen", 0.5)
    # ---- Les prés d'automne de part et d'autre, jaunes ; le chemin qui fuit vers les montagnes.
    f_pre = lambda x: 44.0 + 1.0 * np.sin(_a(x) / 19.0)
    pre = Y > f_pre(X)
    P.rampe(pre, 0.6 + 0.3 * (pg.fbm(X / 10.0, Y / 2.0, 3, 783) - 0.5) - 0.01 * (Y - 44), [PJ1, PJ2, PJ3, PJ4], 0.75)
    fx_, fy_ = 100.0, 43.0
    demi = (Y - fy_) * 0.62 + 0.6
    chemin = pre & (np.abs(X - fx_ - 2.0 * np.sin(Y / 9.0)) < demi)
    P.rampe(chemin, 0.6 + 0.3 * (pg.fbm(X / 6.0, Y / 1.6, 3, 784) - 0.5) - 0.004 * (Y - 44), [TE1, TE2, TE3, CREME], 0.75)
    for cote in (-0.45, 0.45):                                  # les ornières sèches
        orn = pre & (np.abs(X - fx_ - 2.0 * np.sin(Y / 9.0) - demi * cote) < 0.4 + demi * 0.07)
        P.remplir(orn, TE1)
        P.remplir(orn & (pg.fbm(X / 2.0, Y / 1.2, 2, 785) > 0.55), TE2)
    herbe_mil = pre & (np.abs(X - fx_ - 2.0 * np.sin(Y / 9.0)) < demi * 0.12) & (pg.fbm(X / 1.4, Y / 2.0, 2, 786) > 0.42)
    P.remplir(herbe_mil & (P.T < 0.5), PJ2)
    # Les haies de noisetiers : deux talus qui se rapprochent, feuillage doré et sarcelle, des noisettes.
    for cote in (-1, 1):
        for i in range(11):
            u = i / 10.0
            y = 46.0 + 34.0 * u ** 1.5
            x = fx_ + cote * ((y - fy_) * 0.62 + 4 + 10 * u + 3 * hz(i, 1, 787 + cote))
            r = 3.0 + 9.0 * u
            b = [(x + cote * r * 0.3 * j + (hz(i, j, 788) - 0.5) * r, y - r * (0.5 + 0.6 * hz(i, j + 4, 788)), r * (0.6 + 0.3 * hz(i, j + 8, 788))) for j in range(4)]
            P.volumes(b, [T.S0, T.S1, T.S2, PJ1, PJ2, PJ3], (-0.3 * cote, -0.7, 0.3), plancher=y + r * 0.3, grain=1.1, graine=789 + i + (cote > 0) * 20,
                      gain=0.6, base=0.42, trame=0.85)
            P.trait(x, y + r * 0.3, x + cote * 0.6, y - r * 0.4, BO1, P.ep(0.3 + 0.6 * u))
            if u > 0.4:
                for q in range(4):
                    P.point(x + (hz(i, q, 790) - 0.5) * r * 1.6, y - r * 0.6 + (hz(i, q + 5, 790) - 0.5) * r, RO2, 2)
    for i in range(7):                                          # des feuilles qui tombent
        t = (p + i / 7.0) % 1.0
        x, y = 30 + 22 * i + 5 * math.sin(t * 6.283 + i), 20 + 40 * t
        P.rect(x, y, 1.2, 0.8, PJ2 if i % 2 else ME2)
    pg.oiseaux(P, 60, 4, 5, coul=T.CIEL[0])
    tab.plan("premier", 1.0)
    # ---- Premier plan : l'herbe haute du talus, des graminées, des colchiques, un caillou ; tout près de l'œil.
    f_sol = lambda x: 75.0 + 1.0 * np.sin(_a(x) / 13.0) + 3.0 * np.exp(-((_a(x) - 100) / 26.0) ** 2)
    m = Y > f_sol(X)
    P.rampe(m, 0.4 + 0.4 * (pg.fbm(X / 6.0, Y / 2.0, 3, 791) - 0.5) + 0.3 * np.exp(-(Y - f_sol(X)) / 1.4), [T.S0, T.S1, TE1, TE2, TE3], 0.8)
    pg.cailloux(P, f_sol, n=30, y0=76.0, graine=792)
    for i in range(46):                                         # les graminées, leurs épis dorés
        x = -6 + 204 * hz(i, 1, 793)
        if 46 < x < 88 or 112 < x < 150:
            continue
        h = 8 + 16 * hz(i, 2, 793)
        bal = 0.8 * onde(p, x / 40.0) * h / 20.0
        P.courbe([(x, 81.0), (x + (hz(i, 3, 793) - 0.5) * 3, 81 - h * 0.6), (x + (hz(i, 3, 793) - 0.5) * 5 + bal, 81 - h)], T.S1 if i % 3 else PJ1, 1)
        P.ell(x + (hz(i, 3, 793) - 0.5) * 5 + bal, 81 - h - 0.8, 0.6, 1.6, PJ2 if i % 2 else PJ3)
    for i in range(7):
        x = 6 + 28 * i + 6 * hz(i, 1, 794)
        if not (46 < x < 88 or 112 < x < 150):
            pg.fleur(P, x, 79.0, 2.0 + hz(i, 2, 794), T.VIOLET, CREME)
    poussiere(P, 60, 10, 140, 60, 16, T.CIEL[11], 795)


# =====================================================================================================================
# Le Pré aux Draps : un pré en pente douce traversé de cordes à linge. Onze grands draps blancs qui claquent au vent,
# pinces en bois, panier d'osier, ombres mouvantes sur l'herbe, lumière d'après-midi. Le sol descend de 72 à 76.
# =====================================================================================================================
@decor("petit-nuage", "pre-aux-draps", soleil=(160.0, 2.0), tons=LAVE, nom="Le Pré aux Draps")
def pre_aux_draps(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=38.0, haut=0.0, halo=0.34, disque=5.0)
    tab.plan("nuages", 0.08)
    pg.cumulus(P, [(46, 4, 50, 8.5, 800, 9, 0.0), (112, -6, 30, 5.0, 801, 6, 0.4), (18, 22, 20, 3.4, 802, 5, 0.7)], dessous=-0.5)
    tab.plan("lointains", 0.2)
    sommets(P, lambda x: deux_dents(x) + 8.0, [T.L2, T.L3, T.L4, T.L5], neige=6.0, graine=3)
    pg.crete(P, lambda x: pg.profil(x, 42.0, 6.0, 24.0, 803), [T.L1, T.L2, T.L3, T.L4], 0.5)
    tab.plan("moyen", 0.5)
    # ---- Le pré : il monte vers la gauche ; l'herbe ondule ; les ombres des draps y courent.
    f_pre = lambda x: 40.0 + (_a(x) - 96) * 0.03 + 1.5 * np.sin(_a(x) / 21.0)
    pre = Y > f_pre(X)
    onde_h = pg.fbm((X + 3 * onde(p)) / 12.0, Y / 2.4, 3, 804)
    P.rampe(pre, 0.62 + 0.4 * (onde_h - 0.5) - 0.006 * (Y - 40), [T.S1, T.S2, T.S3, T.S4, PJ3], 0.8)
    P.remplir(P.crete(pre), PJ3)
    pg.arbre_rond(P, 12.0, float(f_pre(12.0)) + 0.5, 4.0, 805, tronc=4.0)
    pg.maison(P, 176.0, float(f_pre(176.0)) + 0.6, p, grande=False)
    # Trois cordes, onze draps : chacun gonfle et claque à son rythme ; son ombre glisse sur l'herbe, en biais.
    k = 0
    for rang, (yc, ech, x0, x1, n) in enumerate(((46.0, 0.5, 30.0, 150.0, 4), (54.0, 0.75, 14.0, 176.0, 4), (64.0, 1.0, 44.0, 190.0, 3))):
        for x in (x0, x1):
            P.rect(x - 0.5 * ech, yc - 14 * ech, 1.0 * ech + 0.4, 15 * ech, BO2)
            P.trait(x - 2.0 * ech, yc - 13.6 * ech, x + 2.0 * ech, yc - 13.6 * ech, BO2)
        P.courbe([(x0, yc - 13.4 * ech), ((x0 + x1) / 2, yc - 11.6 * ech), (x1, yc - 13.4 * ech)], TE3, 1)
        for i in range(n):
            u = (i + 0.5) / n
            cx = x0 + (x1 - x0) * u
            top = yc - 13.4 * ech + 1.8 * ech * math.sin(math.pi * u) + 0.4
            w, h = (x1 - x0) / n * 0.78, 13.0 * ech
            v1, v2 = onde(p, 0.09 * k), onde(p, 0.09 * k + 0.25)
            pts = [(cx - w / 2, top), (cx + w / 2, top), (cx + w / 2 + 2.6 * ech * v1 + 2 * ech, top + h * 0.5), (cx + w / 2 + 4.0 * ech * v2 + 3 * ech, top + h),
                   (cx - w / 2 + 4.0 * ech * v1 + 3 * ech, top + h + 0.8 * ech * v2), (cx - w / 2 + 2.0 * ech * v2 + 1.6 * ech, top + h * 0.5)]
            ombre = [(q[0] - 10 * ech, yc + (q[1] - top) * 0.12 + 1.0) for q in pts]
            voile(P, P.masque_poly(ombre) & pre, T.S0, 0.5)
            md = P.poly(pts, NE4)
            pli = np.sin((X - cx) * 1.1 / ech + (Y - top) * 0.25 / ech + v1 * 2.0)
            P.rampe(md, 0.66 + 0.26 * pli + 0.012 * (X - cx) / ech, [NE1, NE2, NE3, NE4], 0.6)
            P.remplir(P.crete(md), BLANC)
            for dx in (-w * 0.4, 0.0, w * 0.4):                 # les pinces en bois
                P.rect(cx + dx - 0.3 * ech, top - 0.9 * ech, 0.7 * ech + 0.3, 1.8 * ech, TE2)
            k += 1
    # Le panier d'osier, plein ; une pince tombée ; une bergeronnette sur un piquet.
    bx_, by_ = 112.0, 73.0
    P.ell(bx_, by_ + 0.6, 9.0, 1.6, T.S0)
    pan = P.poly([(bx_ - 8, by_ - 6), (bx_ + 8, by_ - 6), (bx_ + 6, by_), (bx_ - 6, by_)], TE2)
    P.remplir(pan & ((P.XI + P.YI) % 3 == 0), TE1)
    P.remplir(pan & ((P.XI - P.YI) % 3 == 0), TE3)
    P.rect(bx_ - 8.6, by_ - 6.8, 17.2, 1.4, TE3)
    P.volumes([(bx_ - 3, by_ - 8, 3.4), (bx_ + 2, by_ - 8.6, 3.8), (bx_ + 5, by_ - 7.4, 2.4)], [NE1, NE2, NE3, NE4], (0.5, -0.6, 0.4), plancher=by_ - 6.4,
              gain=0.5, base=0.6, trame=0.5)
    P.rect(124.0, 74.6, 2.4, 0.8, TE2)
    P.ell(44.0, 49.0, 1.6, 1.1, R4)
    P.ell(45.4, 48.2, 0.8, 0.8, ENCRE)
    P.trait(42.4, 49.0, 40.2, 48.0 - (0.6 if int(p * 8) % 2 else 0), R2)
    tab.plan("premier", 1.0)
    # ---- Premier plan : le bas du pré, en pente (72 à gauche, 76 à droite) : herbes, boutons d'or, pâquerettes.
    f_sol = lambda x: 73.0 + (_a(x) - 4) * (4.0 / 184.0) + 0.6 * np.sin(_a(x) / 11.0)
    pg.sol(P, f_sol, [T.S0, T.S1, T.S2, T.S3, T.S4], chemin=78.0, graine=806, lisere=0.56)
    pg.touffes(P, f_sol, n=260, haut=4.0, graine=807)
    for i in range(20):
        x = 4 + 184 * hz(i, 1, 808)
        if 50 < x < 92 or 130 < x < 172:
            continue
        pg.fleur(P, x, float(f_sol(x)) + 1.0 + 3 * hz(i, 2, 808), 1.6 + 1.6 * hz(i, 3, 808), PJ3 if i % 2 else CREME, PJ2)
    pg.tronc(P, lambda y: 5.0 + 1.0 * np.sin(_a(y) / 13.0) + 1.6 * np.exp(-((_a(y) - 80) / 5.0) ** 2), graine=809)
    pg.feuillage(P, lambda x: 10.0 - 0.5 * _a(x) + 2.4 * np.sin(_a(x) / 5.0), x0=-6, x1=40, n=420, graine=810, y_max=16.0,
                 tons=([T.S0, T.S1, T.S1, T.S2], [T.S1, T.S2, T.S3], [T.S2, T.S3, T.S4, PJ2, PJ3]))
    poussiere(P, 30, 10, 180, 60, 14, BLANC, 811)


# =====================================================================================================================
# L'Étang-qui-fume : un petit étang rond bordé de roseaux et d'un saule (la clé, à droite), nénuphars, brume épaisse
# posée sur l'eau, grandes toiles d'araignée chargées de rosée sur la rive d'en face, lumière gris-bleu de l'aube.
# =====================================================================================================================
@decor("petit-nuage", "etang-qui-fume", soleil=(56.0, 30.0), tons=ROSE, nom="L'Étang-qui-fume")
def etang_qui_fume(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=44.0, haut=0.0, halo=0.24, disque=4.0)
    tab.plan("nuages", 0.08)
    pg.voiles(P, y=-4.0, epais=10.0, seuil=0.56, graine=820)
    pg.barres(P, [(60, 34.0, 20, 1.2), (120, 28.0, 16, 1.0)])
    tab.plan("lointains", 0.2)
    sommets(P, lambda x: deux_dents(x) + 4.0, [T.L1, T.L2, T.L3, T.L4], neige=6.0, graine=4)
    pg.crete(P, lambda x: pg.profil(x, 45.0, 6.0, 20.0, 821), [T.L0, T.L1, T.L2, T.L3], 0.5)
    pg.sapins(P, lambda x: pg.profil(x, 45.0, 6.0, 20.0, 821), densite=0.7, graine=822, coul=T.S0)
    tab.plan("moyen", 0.5)
    # ---- La rive d'en face : herbe sombre, piquets ; entre eux, les grandes toiles d'araignée lourdes de rosée.
    f_rive = lambda x: 47.0 + 0.7 * np.sin(_a(x) / 8.0)
    pg.rive(P, f_rive, epais=2.0, joncs=150, graine=823)
    for i, (x, r) in enumerate(((30.0, 6.0), (58.0, 5.0), (86.0, 7.0), (108.0, 4.6))):
        y = 40.0 - (i % 2) * 2
        for dx in (-r - 1, r + 1):
            P.trait(x + dx, 47.6, x + dx * 0.96, y - r - 2, T.S0)
        for a in range(0, 180, 20):
            ra = math.radians(a)
            P.trait(x - r * math.cos(ra), y - r * math.sin(ra) * 0.9, x + r * math.cos(ra), y + r * math.sin(ra) * 0.9, T.CIEL[8])
        for rr in (0.3, 0.55, 0.8, 1.0):
            d = np.hypot(X - x, (Y - y) / 0.9)
            P.remplir((np.abs(d - r * rr) < 0.22), T.CIEL[9])
        for q in range(14):                                     # les perles de rosée : elles s'allument l'une après l'autre
            a, rr = 6.283 * hz(i, q, 824), r * (0.3 + 0.7 * hz(i, q + 20, 824))
            if (p + hz(i, q + 40, 824)) % 1.0 < 0.5:
                P.point(x + rr * math.cos(a), y + rr * 0.9 * math.sin(a), BLANC)
    # ---- L'étang, miroir ; la brume épaisse posée dessus, qui monte en fumées lentes.
    f_berge = lambda x: 72.6 + 1.0 * np.sin(_a(x) / 19.0) - 4.0 * np.exp(-((_a(x) - 190) / 24.0) ** 2) - 3.0 * np.exp(-((_a(x) - 2) / 20.0) ** 2)
    pg.miroir(P, tab.derriere(), 48.4, ronds=((84.0, 64.0, 0.2), (40.0, 58.0, 0.7)), fonce=(58.0, 16.0), eclats=0.5, rides=0.03, graine=825)
    for i, (x, y, r, fl) in enumerate(((60, 60, 4.0, CREME), (72, 64, 2.6, None), (100, 58, 3.0, None), (50, 67, 3.2, T.VIOLET), (112, 66, 4.4, CREME),
                                       (88, 54, 1.8, None), (34, 62, 2.4, None))):
        pg.nenuphar(P, x, y + 0.12 * onde(p, 0.13 * i), r, 826 + i, fl)
    for g, (y, ep, f) in enumerate(((51.0, 2.6, 0.7), (56.0, 2.4, 0.6), (62.0, 2.2, 0.5), (68.0, 1.8, 0.35))):
        brume_claire(P, y, ep, 10 + g, T.CIEL[10], f)
    for i in range(9):                                          # les fumées de l'étang
        t = (p + i / 9.0) % 1.0
        x = 20 + 16 * i + 4 * math.sin(t * 6.283 + i)
        voile(P, np.hypot((X - x) / 1.2, Y - (56 - 16 * t)) < 2.0 + 4.0 * t, T.CIEL[10], 0.5 - 0.48 * t)
    # Le saule : son tronc penché sur l'eau, ses longues branches qui pendent et se balancent, jusqu'à la toucher.
    sx, sy = 150.0, 70.0
    P.courbe([(sx + 8, sy + 6), (sx + 4, sy - 14), (sx - 2, sy - 34), (sx - 6, sy - 52)], BO1, P.ep(5.0), P.ep(2.0))
    P.courbe([(sx + 9.6, sy + 4), (sx + 5.6, sy - 14), (sx - 0.4, sy - 34)], BO2, 1)
    for (bx_, by_) in ((sx - 22, sy - 62), (sx + 10, sy - 66), (sx - 8, sy - 72), (sx + 24, sy - 56)):
        P.courbe([(sx - 4, sy - 44), ((sx + bx_) / 2, (sy - 44 + by_) / 2 - 4), (bx_, by_)], BO1, P.ep(1.6), 1)
    P.volumes([(sx - 14, sy - 64, 9), (sx + 6, sy - 68, 10), (sx + 22, sy - 62, 8), (sx - 26, sy - 58, 7), (sx - 4, sy - 74, 8), (sx + 32, sy - 56, 6),
               (sx - 34, sy - 52, 6), (sx + 14, sy - 74, 7)], [T.S0, T.S1, T.S2, T.S3],
              (-0.7, -0.4, 0.3), grain=2.4, graine=833, gain=0.45, base=0.42, trame=1.0)
    for i in range(64):
        x0 = sx - 40 + 1.25 * i + hz(i, 1, 834)
        l = 22 + 26 * hz(i, 2, 834) * (1 - abs(x0 - sx) / 60.0)
        y0 = sy - 58 + 8 * abs(x0 - sx) / 40.0 + 4 * hz(i, 3, 834)
        bal = 1.6 * onde(p, x0 / 50.0) * l / 30.0
        P.courbe([(x0, y0), (x0 + bal * 0.4, y0 + l * 0.5), (x0 + bal, y0 + l)], (T.S1, T.S2, T.S3, PJ2)[i % 4], 1)
    tab.plan("premier", 1.0)
    pg.sol(P, f_berge, graine=835)
    pg.cailloux(P, f_berge, graine=836)
    pg.touffes(P, f_berge, graine=837)
    pg.roseaux(P, -6.0, 16.0, n=12, haut=(14.0, 36.0), penche=1.0, graine=838)
    pg.roseaux(P, 100.0, 124.0, n=6, haut=(8.0, 16.0), penche=-1.0, graine=839)
    pg.grenouille(P, 78.0, 73.4, p)
    pg.libellule(P, 96.0, 60.0)
    pg.lucioles(P, [(10.0, 60.0), (24.0, 70.0), (176.0, 74.0), (120.0, 76.0)], graine=840)


# =====================================================================================================================
# Le Plateau Râpé : un plateau immense, plat et jaune, herbe rase et cailloux, un seul arbre mort au milieu (la clé),
# pas une ombre ; au loin de hauts nuages d'orage noirs en forme d'enclume ; l'air tremble.
# =====================================================================================================================
@decor("petit-nuage", "plateau-rape", soleil=(96.0, -40.0), tons=LAVE, nom="Le Plateau Râpé")
def plateau_rape(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=52.0, haut=0.0, halo=0.0, disque=0)
    voile(P, Y > 30, PJ4, np.clip((Y - 30) / 40.0, 0, 0.5))       # la poussière jaune qui monte à l'horizon
    tab.plan("nuages", 0.08)
    # ---- Les enclumes : trois nuages d'orage, noirs en bas, étalés tout en haut ; un éclair, loin, de temps en temps.
    orage = [ENCRE, R1, R1, R2, R3, R4, NE2]
    for i, (x, base, l, h) in enumerate(((36.0, 44.0, 40.0, 16.0), (150.0, 46.0, 50.0, 20.0), (96.0, 47.0, 30.0, 10.0))):
        x = x + 0.5 * onde(p, 0.3 * i)
        b = pg.amas(x, base, l, h * 0.7, 850 + i, 9) + [(x + (j - 2) * l * 0.2, base - h * 1.25, h * 0.36) for j in range(5)] + \
            [(x, base - h * 0.8, h * 0.4), (x - l * 0.1, base - h * 0.5, h * 0.4)]
        P.volumes(b, orage, (0.0, -0.8, 0.3), plancher=base, grain=0.3, graine=853 + i, gain=0.7, base=0.36, trame=0.8)
        voile(P, (np.abs(X - x) < l * 0.5) & (Y > base) & (Y < base + 8) & ((P.XI + P.YI * 2) % 5 == 0), R2, 0.6)   # la pluie, là-bas
    if int(p * 8) == 5:
        P.courbe([(152.0, 34.0), (149.0, 40.0), (153.0, 43.0), (150.0, 49.0)], BLANC, 1)
        halo(P, 151.0, 38.0, 14.0, NE3, 0.4)
    tab.plan("lointains", 0.2)
    pg.crete(P, lambda x: pg.profil(x, 52.0, 3.0, 40.0, 856), [PJ1, PJ2, T.L3, T.L4], 0.4)
    tab.plan("moyen", 0.5)
    # ---- Le plateau : plat, jaune, râpé ; l'air qui tremble au ras du sol ; pas une ombre.
    sol = Y > 52.0
    P.rampe(sol, 0.62 + 0.3 * (pg.fbm(X / (4.0 + (Y - 52) * 0.5), (Y - 52) / 1.2, 3, 857) - 0.5) + 0.004 * (Y - 52), [PJ1, PJ2, PJ3, PJ4], 0.8)
    tremble = sol & (Y < 58) & (np.sin(X * 0.9 + Y * 3.0 + p * 6.283 * 2) > 0.5)
    P.remplir(tremble & (P.T < 0.5), PJ4)
    voile(P, (Y > 49) & (Y < 53) & (np.sin(X * 0.7 + p * 6.283) > 0.2), PJ4, 0.4)
    for i in range(90):                                         # les cailloux et les touffes rases, de plus en plus gros vers nous
        y = 53 + 26 * hz(i, 1, 858) ** 1.4
        x = -6 + 204 * hz(i, 2, 858)
        k = 0.3 + (y - 52) / 22.0
        if i % 3 == 0:
            P.ell(x, y, 1.6 * k, 0.8 * k, R3)
            P.ell(x - 0.3 * k, y - 0.3 * k, 0.9 * k, 0.4 * k, R4)
        else:
            for q in range(3):
                P.trait(x + q * 0.7 * k, y, x + q * 0.9 * k - 0.6 * k, y - 1.6 * k, PJ1)
    # L'arbre mort, seul au milieu : tronc gris argenté, branches nues, un nid vide ; un corbeau s'y pose.
    ax, ay = 100.0, 58.0
    P.courbe([(ax - 1.0, ay + 1.0), (ax, ay - 12.0), (ax - 1.6, ay - 24.0), (ax + 0.6, ay - 34.0)], R2, P.ep(2.4), P.ep(0.8))
    P.courbe([(ax + 0.2, ay), (ax + 1.0, ay - 12.0), (ax - 0.6, ay - 24.0)], R4, 1)
    for (pts, ep) in (([(ax - 0.4, ay - 14), (ax - 6, ay - 20), (ax - 8, ay - 28)], 1.0), ([(ax - 0.8, ay - 22), (ax + 6, ay - 27), (ax + 8, ay - 33)], 1.0),
                      ([(ax - 6, ay - 20), (ax - 11, ay - 21), (ax - 13, ay - 24)], 0.6), ([(ax + 6, ay - 27), (ax + 11, ay - 27), (ax + 13, ay - 30)], 0.6),
                      ([(ax, ay - 30), (ax - 4, ay - 35), (ax - 3.6, ay - 39)], 0.6), ([(ax + 0.4, ay - 32), (ax + 3, ay - 38)], 0.5)):
        P.courbe(pts, R2, P.ep(ep), 1)
    P.ell(ax + 6.6, ay - 28.4, 2.4, 1.2, BO2)                    # le nid
    cy_ = ay - 39.6
    P.ell(ax - 3.8, cy_ - 1.2, 2.0, 1.4, ENCRE)                  # le corbeau
    P.ell(ax - 2.4, cy_ - 2.4, 1.0, 1.0, ENCRE)
    P.rect(ax - 1.6, cy_ - 2.4 + (0.6 if int(p * 8) % 5 == 0 else 0), 1.4, 0.5, R2)
    P.poly([(ax - 5.4, cy_ - 1.4), (ax - 8.0, cy_ - 0.2), (ax - 5.4, cy_ - 0.4)], ENCRE)
    for i in range(5):                                          # des tourbillons de poussière
        t = (p + i / 5.0) % 1.0
        voile(P, np.hypot((X - (20 + 36 * i + 14 * t)) / 2.0, Y - (60 - 6 * t)) < 1.0 + 2.6 * t, PJ4, 0.5 - 0.45 * t)
    tab.plan("premier", 1.0)
    f_sol = lambda x: 76.4 + 0.5 * np.sin(_a(x) / 15.0)
    m = Y > f_sol(X)
    P.rampe(m, 0.45 + 0.4 * (pg.fbm(X / 6.0, Y / 2.0, 3, 859) - 0.5), [TE1, PJ1, PJ2, PJ3], 0.8)
    pg.cailloux(P, f_sol, n=50, y0=76.6, graine=860)
    for i in range(30):
        x = -6 + 204 * hz(i, 1, 861)
        if 20 < x < 60 or 130 < x < 170:
            continue
        for q in range(4):
            P.trait(x + q * 0.8, 77.0, x + q * 1.2 - 1.4 + 0.3 * onde(p, x / 30.0), 77.0 - 3 - 3 * hz(i, q, 862), PJ1 if q % 2 else TE1)
    P.ell(12.0, 77.0, 6.0, 3.0, R2)                              # un crâne de mouton ? non : une grosse pierre, et un lézard dessus
    P.ell(10.6, 76.0, 3.6, 1.6, R4)
    P.courbe([(10.0, 74.6), (13.0, 74.0), (16.0, 74.8 + 0.3 * onde(p))], PJ1, P.ep(0.6))
    poussiere(P, 0, 40, 192, 76, 30, PJ4, 863)


# =====================================================================================================================
# La halte du Bout-des-Prés : une petite halte de pierre au pied des montagnes. Toit d'ardoise, cheminée qui fume ; sur
# le faîte, une girouette en fer rouillé (un coq) avec une lanterne accrochée au bec (la clé) ; sommets blancs derrière ;
# la nuit finit.
# =====================================================================================================================
@decor("petit-nuage", "halte-girouette", soleil=(30.0, 40.0), tons=NUIT, nom="La halte du Bout-des-Prés")
def halte_girouette(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=52.0, haut=0.0, halo=0.2, etoiles=0.4, lune=(160.0, -4.0, 3.6), disque=0)
    tab.plan("nuages", 0.08)
    pg.voiles(P, y=20.0, epais=8.0, seuil=0.6, graine=870)
    tab.plan("lointains", 0.2)
    sommets(P, lambda x: deux_dents(x) - 2.0, [T.CIEL[2], T.CIEL[3], T.CIEL[5], T.CIEL[6]], neige=12.0, graine=5, limite=34.0)
    pg.crete(P, lambda x: pg.profil(x, 50.0, 8.0, 22.0, 871), [T.CIEL[1], T.CIEL[2], T.CIEL[3], T.CIEL[4]], 0.5)
    pg.sapins(P, lambda x: pg.profil(x, 50.0, 8.0, 22.0, 871), densite=0.8, graine=872, coul=T.CIEL[0])
    brume_claire(P, 50.0, 4.0, 20, T.CIEL[5], 0.45)
    tab.plan("moyen", 0.5)
    # ---- Le pré, bleu de nuit, givré ; le chemin qui arrive ; la halte de pierre et sa fenêtre allumée.
    f_pre = lambda x: 54.0 + 1.4 * np.sin(_a(x) / 17.0)
    pre = Y > f_pre(X)
    P.rampe(pre, 0.5 + 0.3 * (pg.fbm(X / 9.0, Y / 2.0, 3, 873) - 0.5) - 0.006 * (Y - 54), [NU1, NU2, T.S1, T.S2], 0.8)
    for j in range(40):
        u = j / 39.0
        P.ell(96 - 60 * u + 8 * math.sin(u * 5), 60 + 20 * u, 2.0 + 5 * u, 0.7 + 0.5 * u, T.CIEL[5] if j % 2 else T.CIEL[4])
    hx, hy, hw, hh = 96.0, 62.0, 44.0, 24.0
    mur = (np.abs(X - hx) < hw / 2) & (Y > hy - hh) & (Y < hy)
    P.rampe(mur, 0.5 - 0.012 * (X - hx) + 0.4 * (pg.fbm(X / 3.0, Y / 2.4, 3, 874) - 0.5), [R1, R2, R3, R4], 0.7)
    P.remplir(mur & (((Y - hy) % 3.2) < 0.4), R1)
    P.remplir(mur & ((((X - hx) / 6.0 + np.floor((Y - hy) / 3.2) * 0.5) % 1.0) < 0.07), R1)
    toit = P.poly([(hx - hw / 2 - 4, hy - hh), (hx + hw / 2 + 4, hy - hh), (hx + 4, hy - hh - 20), (hx - 4, hy - hh - 20)], T.CIEL[1])
    P.rampe(toit, 0.5 - 0.02 * (X - hx) + 0.3 * (((Y - hy) % 2.6) / 2.6), [ENCRE, T.CIEL[1], T.CIEL[2], T.CIEL[3]], 0.5)
    P.remplir(toit & (((Y - hy) % 2.6) < 0.4), ENCRE)
    P.remplir(P.crete(toit), T.CIEL[6])
    voile(P, toit & (Y < hy - hh - 12), NE3, 0.4)                # un reste de givre sur le faîte
    P.rect(hx + 10, hy - hh - 22, 5.0, 12.0, R2)                  # la cheminée
    P.rect(hx + 10, hy - hh - 22, 1.4, 12.0, R3)
    P.rect(hx + 9, hy - hh - 23.4, 7.0, 1.6, R3)
    pg.fumee(P, hx + 12.5, hy - hh - 24.0, p)
    P.ell(hx - 9, hy - 9.0, 5.0, 5.4, BO1, cond=Y < hy - 8.6)     # la porte
    P.rect(hx - 14, hy - 9.0, 10.0, 9.0, BO1)
    P.ell(hx - 9, hy - 8.6, 4.0, 4.4, BO2, cond=Y < hy - 8.2)
    P.rect(hx - 13, hy - 8.6, 8.0, 8.6, BO2)
    P.point(hx - 6.4, hy - 4.6, LA2)
    P.rect(hx + 5, hy - 15.0, 10.0, 9.0, BO1)                     # la fenêtre allumée
    P.rect(hx + 6, hy - 14.0, 8.0, 7.0, LA2 if int(p * 8) % 6 else LA3)
    P.rect(hx + 9.6, hy - 14.0, 0.8, 7.0, BO1)
    P.rect(hx + 6, hy - 10.8, 8.0, 0.8, BO1)
    halo(P, hx + 10, hy - 10.5, 16.0, LA1, 0.45)
    voile(P, (Y > hy) & (Y < hy + 9) & (np.abs(X - hx - 10 - (Y - hy) * 0.4) < 5 + (Y - hy) * 0.7), LA2, 0.3)
    P.rect(hx - 20, hy - 6.0, 4.0, 6.0, BO2)                      # le banc de pierre, un bâton de marche, des sabots
    P.rect(hx + 18, hy - 3.0, 9.0, 1.2, R4)
    P.rect(hx + 19, hy - 1.8, 1.2, 1.8, R2)
    P.rect(hx + 25, hy - 1.8, 1.2, 1.8, R2)
    # La girouette : un coq de fer rouillé, sur sa tige ; il tourne un peu ; la lanterne pend à son bec et se balance.
    gx, gy = hx, hy - hh - 20.0
    P.rect(gx - 0.4, gy - 12.0, 0.9, 12.0, ENCRE)
    P.trait(gx - 5.0, gy - 5.0, gx + 5.0, gy - 5.0, ENCRE)
    P.trait(gx, gy - 9.0, gx, gy - 1.0, ENCRE)
    for (dx, dy) in ((-5.6, -5.0), (5.6, -5.0)):
        P.point(gx + dx, gy + dy, RO1, 2)
    s = 1.0 if onde(p) > -0.3 else 0.8                           # il pivote à peine : sa silhouette se resserre
    coq = [(gx - 6 * s, gy - 14.0), (gx - 2 * s, gy - 17.0), (gx + 3 * s, gy - 16.6), (gx + 5 * s, gy - 20.0), (gx + 7.4 * s, gy - 19.0),
           (gx + 6 * s, gy - 15.0), (gx + 3 * s, gy - 12.0), (gx - 3 * s, gy - 12.0)]
    P.poly(coq, RO1)
    P.poly([(gx - 6 * s, gy - 14.0), (gx - 10 * s, gy - 19.0), (gx - 8.6 * s, gy - 13.6), (gx - 10.6 * s, gy - 11.0), (gx - 5 * s, gy - 12.4)], RO1)   # la queue
    P.poly([(gx + 4.4 * s, gy - 20.0), (gx + 5.4 * s, gy - 22.6), (gx + 6.6 * s, gy - 20.4)], RO2)                                           # la crête
    P.trait(gx - 4 * s, gy - 15.6, gx + 4 * s, gy - 16.0, RO2)
    P.point(gx + 5.6 * s, gy - 18.8, ENCRE)
    bec = (gx + 8.4 * s, gy - 18.4)
    P.trait(gx + 7.2 * s, gy - 18.6, bec[0], bec[1], RO2)
    bal = 0.7 * onde(p, 0.2)
    P.trait(bec[0], bec[1], bec[0] + bal, bec[1] + 4.0, ENCRE)
    halo(P, bec[0] + bal, bec[1] + 6.4, 14.0, LA1, 0.5)
    P.rect(bec[0] + bal - 1.4, bec[1] + 4.0, 2.8, 0.7, ENCRE)
    P.rect(bec[0] + bal - 1.1, bec[1] + 4.7, 2.2, 3.0, LA2 if int(p * 8) % 5 else LA3)
    P.rect(bec[0] + bal - 0.4, bec[1] + 5.2, 0.8, 1.8, LA3)
    P.rect(bec[0] + bal - 1.4, bec[1] + 7.7, 2.8, 0.7, ENCRE)
    for (x, h, g) in ((34.0, 22.0, 875), (44.0, 16.0, 876), (150.0, 26.0, 877), (164.0, 18.0, 878), (176.0, 22.0, 879)):
        meleze(P, x, float(f_pre(x)) + 3.0, h, g, dore=False)
    tab.plan("premier", 1.0)
    f_sol = lambda x: 72.0 + 0.8 * np.sin(_a(x) / 15.0)
    pg.sol(P, f_sol, [T.N0, T.N1, T.N2, T.S1, T.S2], chemin=76.0, graine=880, lisere=2.0)
    pg.touffes(P, f_sol, n=200, haut=3.0, graine=881)
    voile(P, (Y > f_sol(X)) & (pg.fbm(X / 2.0, Y / 1.4, 2, 882) > 0.68), NE2, 0.5)          # le givre
    for x in np.arange(-4.0, 198.0, 16.0):                       # la clôture du pré
        if 16 < x < 48 or 144 < x < 178:
            continue
        P.rect(x, 62.0, 1.4, 12.0, ENCRE)
        P.trait(x, 65.0, x + 16.0, 65.6, ENCRE)
    pg.lucioles(P, [(20.0, 66.0), (60.0, 70.0), (140.0, 68.0), (182.0, 64.0)], graine=883)


# =====================================================================================================================
# Le sentier des mélèzes : un sentier en lacets dans une pente raide, des mélèzes dorés qui perdent leurs aiguilles, des
# rochers gris, les premières plaques de neige ; deux sommets blancs en forme de dents, un col arrondi entre eux.
# =====================================================================================================================
@decor("petit-nuage", "sentier-des-melezes", soleil=(170.0, -8.0), tons=LAVE, nom="Le sentier des mélèzes")
def sentier_des_melezes(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=40.0, haut=0.0, halo=0.3, disque=4.4)
    tab.plan("nuages", 0.08)
    pg.cumulus(P, [(30, 2, 34, 5.5, 890, 7, 0.0)], dessous=-0.5)
    pg.voiles(P, y=-6.0, epais=8.0, seuil=0.62, graine=891)
    tab.plan("lointains", 0.2)
    # ---- Les deux dents et leur col : tout près maintenant, ils remplissent le ciel.
    grand = lambda x: deux_dents(96 + (_a(x) - 96) / 1.5) * 1.5 - 34.0
    sommets(P, grand, [R2, R3, R4, T.L4], neige=16.0, graine=6, limite=14.0)
    brume_claire(P, 34.0, 4.0, 30, T.CIEL[9], 0.4)
    tab.plan("moyen", 0.5)
    # ---- La pente : raide, d'herbe rousse et de rocaille ; le sentier y monte en lacets ; des plaques de neige.
    f_p = lambda x: 62.0 - (_a(x) - 20) * 0.2 + 4.0 * np.sin(_a(x) / 23.0) + 1.5 * np.sin(_a(x) / 7.0)
    pente = Y > f_p(X) - 14.0 * np.clip((_a(X) - 120) / 60.0, 0, 1)
    P.rampe(pente, 0.55 + 0.4 * (pg.fbm(X / 8.0, (Y + X * 0.2) / 2.4, 3, 892) - 0.5) - 0.006 * (Y - 40), [TE1, PJ1, PJ2, PJ3], 0.8)
    for i in range(9):                                          # les plaques de neige
        x, y = 100 + 90 * hz(i, 1, 893), 28 + 26 * hz(i, 2, 893)
        r = 3 + 6 * hz(i, 3, 893)
        m = pente & (np.hypot((X - x) / 1.8, Y - y) + 2.0 * pg.fbm(X / 3.0, Y / 2.0, 2, 894 + i) < r * 0.7)
        P.remplir(m, NE4)
        P.remplir(m & (pg.fbm(X / 2.0, Y / 1.5, 2, 895) > 0.6), NE2)
    lacets = [(30, 78), (70, 68), (40, 60), (96, 50), (64, 44), (124, 36), (104, 30), (150, 22), (140, 16), (176, 8)]
    for i in range(len(lacets) - 1):
        (xa, ya), (xb, yb) = lacets[i], lacets[i + 1]
        l = max(0.8, 3.2 - 0.3 * i)
        for j in range(30):
            u = j / 29.0
            P.ell(xa + (xb - xa) * u, ya + (yb - ya) * u, l, l * 0.4, TE3 if (i + j // 5) % 2 else CREME)
    for i in range(16):                                         # les rochers gris
        x, y = 4 + 12 * i + 5 * hz(i, 1, 896), float(f_p(4 + 12 * i)) + 4 + 14 * hz(i, 2, 896)
        r = 1.6 + 3.0 * hz(i, 3, 896)
        P.ell(x, y, r, r * 0.6, R2)
        P.ell(x + r * 0.2, y - r * 0.2, r * 0.6, r * 0.3, R4)
    # Les mélèzes dorés, sur toute la pente, de plus en plus petits vers le haut ; leurs aiguilles tombent.
    arbres = sorted(((6 + 184 * float(hz(i, 1, 897)), float(hz(i, 2, 897))) for i in range(26)), key=lambda q: q[1])
    for i, (x, u) in enumerate(arbres):
        y = float(f_p(x)) - 14.0 * max(0.0, min(1.0, (x - 120) / 60.0)) + 2 + 26 * u * (1 - x / 400.0)
        if 22 < x < 46 and y > 60 or 108 < x < 132 and y > 62:
            continue
        meleze(P, x, y, 10 + 22 * u, 898 + i, dore=True)
    aiguilles(P, 0, -10, 192, 70, 60, 899)
    tab.plan("premier", 1.0)
    f_sol = lambda x: 72.0 + 1.0 * np.sin(_a(x) / 13.0)
    pg.sol(P, f_sol, [TE1, BO3, PJ1, PJ2, PJ3], chemin=75.6, graine=900, lisere=2.0)
    pg.cailloux(P, f_sol, y0=73.0, graine=901)
    tapis = (Y > f_sol(X)) & (pg.fbm(X / 3.0, Y / 1.4, 3, 902) > 0.58)
    P.remplir(tapis & (P.T < 0.6), ME2)                           # le tapis d'aiguilles
    meleze(P, 6.0, 84.0, 86.0, 903, dore=True)                   # un grand mélèze tout près, à gauche
    meleze(P, 186.0, 82.0, 64.0, 904, dore=True)
    pg.pierre(P, 150.0, 76.0, 4.0, eau=False)
    P.ell(150.0, 73.4, 3.0, 1.0, NE4)
    pg.champignon(P, 70.0, 78.0, 1.4)
    aiguilles(P, 0, 0, 192, 78, 30, 905)


# =====================================================================================================================
# Le terrier aux bocaux : l'intérieur d'un terrier de marmotte. Des étagères de bois du sol au plafond couvertes de
# bocaux à étiquettes manuscrites (fruits, lueurs, brumes), une lampe à huile, un fauteuil de foin, lumière dorée.
# =====================================================================================================================
@decor("petit-nuage", "terrier-aux-bocaux", soleil=(96.0, 30.0), tons=SOIR, nom="Le terrier aux bocaux")
def terrier_aux_bocaux(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    lx_, ly_ = 96.0, 34.0
    tab.plan("ciel", 0.0)
    # ---- La terre du terrier : une voûte ronde, des racines qui pendent, la lumière dorée de la lampe au milieu.
    d = np.hypot(X - lx_, (Y - ly_) * 1.15)
    P.rampe(np.ones(X.shape, dtype=bool), 1.0 - d / 120.0 + 0.2 * (pg.fbm(X / 7.0, Y / 5.0, 3, 910) - 0.5), [BO1, BO2, TE1, TE2, ME1, ME2], 0.85)
    voute = (np.hypot((X - 96) / 1.5, Y - 46) > 64.0 + 4 * pg.fbm(X / 9.0, Y / 9.0, 3, 911))
    P.rampe(voute, 0.3 + 0.5 * (pg.fbm(X / 4.0, Y / 4.0, 3, 912) - 0.5), [ENCRE, BO1, BO2], 0.8)
    for i in range(14):                                         # les racines
        x = 30 + 10 * i + 4 * hz(i, 1, 913)
        y0 = -16.0 + 6 * abs(x - 96) / 60.0
        l = 6 + 14 * hz(i, 2, 913)
        P.courbe([(x, y0), (x + (hz(i, 3, 913) - 0.5) * 4, y0 + l * 0.6), (x + (hz(i, 4, 913) - 0.5) * 6 + 0.3 * onde(p, 0.1 * i), y0 + l)], BO1, P.ep(0.7), 1)
    tab.plan("lointains", 0.2)
    # ---- Les étagères : du sol au plafond, des deux côtés, des bocaux de toutes tailles. Fruits, lueurs, brumes.
    fruits = (LA1, RO2, T.VIOLET, PJ2, ME2, T.S3, NU2, RO1)
    lueurs = (LA3, T.CIEL[11], NE4, PJ4)
    for (x0, x1) in ((8.0, 78.0), (114.0, 184.0)):
        P.rect(x0 - 2, -6.0, 2.0, 70.0, BO1)
        P.rect(x1, -6.0, 2.0, 70.0, BO1)
        for j, y in enumerate((4.0, 18.0, 32.0, 46.0, 60.0)):
            P.rect(x0 - 2, y, x1 - x0 + 4, 1.8, BO2)
            P.rect(x0 - 2, y, x1 - x0 + 4, 0.5, BO3)
            x = x0 + 1.0
            i = 0
            while x < x1 - 4:
                w, h = 3.4 + 3.6 * hz(i + j * 30, 1, 914 + int(x0)), 6 + 5 * hz(i + j * 30, 2, 914 + int(x0))
                sorte = hz(i + j * 30, 3, 914 + int(x0))
                if sorte < 0.55:
                    bocal(P, x + w / 2, y, w, h, fruits[int(hz(i + j * 30, 4, 915) * len(fruits))])
                    for q in range(3):                          # les fruits dedans
                        P.point(x + 1.0 + hz(i, q, 916) * (w - 2), y - 1.4 - hz(i, q + 5, 916) * (h * 0.6), CREME if q else LA3)
                elif sorte < 0.8:
                    bocal(P, x + w / 2, y, w, h, lueurs[int(hz(i + j * 30, 4, 915) * len(lueurs))], graine=i + j * 30, lueur=True)
                else:                                           # une brume : elle tourne dans son bocal
                    bocal(P, x + w / 2, y, w, h, T.CIEL[4])
                    voile(P, (np.abs(X - x - w / 2) < w / 2 - 0.5) & (Y > y - h * 0.8) & (Y < y - 0.5) & (pg.fbm((X + 3 * onde(p, 0.1 * i)) / 1.6, Y / 1.6, 2, 917 + i) > 0.5),
                          NE3, 0.7)
                x += w + 1.0
                i += 1
    voile(P, (X < 30) | (X > 162), BO1, 0.3)
    tab.plan("moyen", 0.5)
    # ---- Le fond du terrier : le couloir qui s'en va, rond ; un rideau de perles ; une petite échelle.
    P.ell(96.0, 44.0, 12.0, 17.0, BO1)
    P.ell(96.0, 45.0, 10.0, 15.0, ENCRE)
    P.ell(97.0, 48.0, 6.0, 9.0, NU1)
    for i in range(7):
        x = 87.6 + i * 2.8
        for j in range(8):
            P.point(x + 0.3 * onde(p, 0.1 * i + 0.05 * j), 30 + j * 3.0 + abs(i - 3) * 1.2, (LA2, T.BLEU, CREME, T.VIOLET)[(i + j) % 4])
    # Le sol de terre battue, un tapis de foin tressé ; la lampe à huile pendue ; le fauteuil de foin ; une table basse.
    sol = Y > 62.0
    P.rampe(sol, 0.5 + 0.3 * (pg.fbm(X / 8.0, Y / 2.0, 3, 918) - 0.5) + 0.3 * np.exp(-(np.hypot(X - lx_, (Y - 72) * 3) / 50.0) ** 2), [BO1, BO2, TE1, TE2, TE3], 0.8)
    P.ell(96.0, 72.0, 34.0, 4.6, PJ1)
    P.ell(96.0, 72.0, 31.0, 3.8, PJ2)
    P.remplir((np.hypot((X - 96) / 31.0, (Y - 72) / 3.8) < 1) & ((P.XI + P.YI) % 3 == 0), PJ1)
    P.trait(lx_, -16.0, lx_ + 0.4 * onde(p), ly_ - 6.0, BO1)
    halo(P, lx_, ly_, 46.0, LA2, 0.5, ry=36)
    halo(P, lx_, ly_, 16.0, LA3, 0.6)
    P.poly([(lx_ - 5, ly_ - 6), (lx_ + 5, ly_ - 6), (lx_ + 2, ly_ - 9), (lx_ - 2, ly_ - 9)], RO1)
    P.ell(lx_, ly_ - 2.0, 3.0, 4.0, LA3)
    P.ell(lx_, ly_ - 1.4, 1.4, 2.4, BLANC if int(p * 8) % 5 else LA2)
    P.ell(lx_, ly_ + 3.0, 4.0, 2.0, RO2)
    P.ell(lx_, ly_ + 2.4, 3.0, 1.2, RO1)
    fx0 = 50.0                                                  # le fauteuil de foin : rond, doré, une couverture
    P.volumes([(fx0 + 10, 50, 11), (fx0 + 2, 58, 7), (fx0 + 18, 58, 7), (fx0 + 10, 62, 10)], [PJ1, PJ2, PJ3, PJ4], (0.5, -0.5, 0.4), plancher=68.0, grain=1.4,
              graine=919, gain=0.5, base=0.55, trame=0.8)
    for i in range(24):
        P.trait(fx0 + 20 * hz(i, 1, 920), 44 + 22 * hz(i, 2, 920), fx0 + 20 * hz(i, 1, 920) + 2, 44 + 22 * hz(i, 2, 920) + 1.4, PJ1)
    P.poly([(fx0 + 4, 56), (fx0 + 16, 55), (fx0 + 18, 64), (fx0 + 3, 65)], T.VIOLET)
    P.poly([(fx0 + 5, 57), (fx0 + 15, 56.2), (fx0 + 16, 60), (fx0 + 4.4, 61)], T.CIEL[5])
    tx0 = 112.0                                                 # la table : une souche ; dessus, un bocal ouvert, une cuillère, une tasse
    P.ell(tx0 + 10, 62.0, 11.0, 2.6, TE3)
    P.ell(tx0 + 10, 62.0, 8.0, 1.6, TE2)
    P.ell(tx0 + 10, 62.0, 4.0, 0.8, TE3)
    P.rect(tx0, 62.0, 20.0, 8.0, BO2)
    P.rect(tx0, 62.0, 4.0, 8.0, BO3)
    bocal(P, tx0 + 6, 61.6, 5.0, 7.0, LA1)
    P.trait(tx0 + 10, 61.0, tx0 + 16, 59.4, NE2)
    P.rect(tx0 + 14, 57.6, 3.4, 3.6, T.BLEU)
    for k in range(3):
        t = (p + k / 3.0) % 1.0
        voile(P, np.hypot(X - (tx0 + 15.6 + 1.2 * math.sin(t * 6 + k)), Y - (56.0 - 9 * t)) < 0.6 + 1.2 * t, CREME, 0.6 - 0.5 * t)
    tab.plan("premier", 1.0)
    # ---- Premier plan : l'entrée ronde du terrier, sombre, en amorce des deux côtés ; un tas de noisettes ; un bocal de lueur.
    bord = np.hypot((X - 96) / 1.56, Y - 44) > 70.0 + 3 * pg.fbm(X / 6.0, Y / 6.0, 3, 921)
    P.rampe(bord, 0.3 + 0.5 * (pg.fbm(X / 3.0, Y / 3.0, 3, 922) - 0.5), [ENCRE, BO1, BO2], 0.8)
    for i in range(9):
        P.ell(160 + 2.4 * (i % 4) + (i // 4), 77.6 - (i // 4) * 1.6, 1.3, 1.1, RO2 if i % 2 else RO1)
    bocal(P, 28.0, 78.0, 6.0, 9.0, LA3, graine=99, lueur=True)
    voile(P, Y > 78.4, ENCRE, 0.3)
    poussiere(P, 50, 0, 140, 60, 26, LA3, 923)


# =====================================================================================================================
# Le col dans le blanc : un col de montagne sous la neige fraîche, un brouillard blanc qui efface l'horizon, une file de
# cairns à demi enfouis, un pont de neige au-dessus d'une faille bleutée ; blanc sur blanc, lumière sans ombre.
# =====================================================================================================================
@decor("petit-nuage", "col-blanc", soleil=(96.0, -60.0), tons=LAVE, nom="Le col dans le blanc")
def col_blanc(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    P.rampe(np.ones(X.shape, dtype=bool), 0.7 + 0.25 * (pg.fbm(X / 30.0, Y / 14.0, 3, 930) - 0.5) + 0.002 * (Y + 16), [NE1, NE2, NE3, NE4, BLANC], 0.9)
    tab.plan("lointains", 0.2)
    # ---- Ce qu'on devine encore : l'épaule des deux dents, à peine plus grise que le blanc ; le brouillard passe devant.
    for i, (f, coul) in enumerate(((lambda x: 20.0 - 30.0 * np.maximum(0, 1 - np.abs(_a(x) - 40) / 60.0) ** 1.2, NE2),
                                   (lambda x: 24.0 - 34.0 * np.maximum(0, 1 - np.abs(_a(x) - 156) / 64.0) ** 1.2, NE2))):
        m = (Y > f(X)) & (Y < 52)
        P.rampe(m, 0.5 + 0.4 * (pg.fbm(X / 6.0, Y / 4.0, 3, 931 + i) - 0.5) + 0.01 * (Y - 10), [NE1, NE2, NE3, NE4], 0.9)
    for g in range(5):
        brume_claire(P, -6.0 + g * 12.0, 7.0, 40 + g, NE4, 0.7)
    tab.plan("moyen", 0.5)
    # ---- Le col : un grand creux de neige ; les congères, soulignées d'un bleu très pâle ; la trace, à peine.
    f_col = lambda x: 50.0 - 8.0 * ((_a(x) - 96) / 96.0) ** 2 + 2.0 * np.sin(_a(x) / 21.0)
    neige = Y > f_col(X)
    P.rampe(neige, 0.72 + 0.3 * (pg.fbm(X / 14.0, (Y - 44) / 2.4, 3, 933) - 0.5) + 0.002 * (Y - 44), [NE1, NE2, NE3, NE4, BLANC], 0.9)
    for i in range(7):                                          # les congères
        y = 54 + i * 4.0
        c = y + 1.6 * np.sin(X / (9.0 + i) + i) + 0.8 * np.sin(X / 3.7 + i * 2)
        P.remplir(neige & (np.abs(Y - c) < 0.3) & (pg.fbm(X / 8.0, Y * 0 + i, 2, 934) > 0.4), NE2)
        voile(P, neige & (Y > c) & (Y < c + 1.4), NE2, 0.3)
    # La faille bleutée et son pont de neige : une arche fragile ; des glaçons dessous ; ça goutte.
    fx_, fy_ = 96.0, 62.0
    bords = lambda y: 10.0 + (_a(y) - fy_) * 1.3 + 3.0 * np.sin(_a(y) / 2.6)
    faille = (np.abs(X - fx_ - 2.0 * np.sin(Y / 4.0)) < bords(Y)) & (Y > fy_) & (Y < 80)
    P.rampe(faille, 0.75 - 0.05 * (Y - fy_) + 0.2 * (pg.fbm(X / 2.0, Y / 6.0, 3, 935) - 0.5), [NU2, T.EAU[3], T.EAU[5], T.EAU[7], NE2], 0.8)
    pont = (np.abs(Y - 68.0 + 3.0 * np.cos((X - fx_) / 16.0)) < 2.6) & (np.abs(X - fx_) < 22.0)
    P.rampe(pont, 0.8 - 0.1 * (Y - 66), [NE2, NE3, NE4, BLANC], 0.7)
    P.remplir(P.crete(pont), BLANC)
    for i in range(9):
        x = fx_ - 14 + i * 3.6
        l = 2 + 4 * hz(i, 1, 936)
        P.trait(x, 70.4 - 3.0 * math.cos((x - fx_) / 16.0) + 2.4, x, 70.4 - 3.0 * math.cos((x - fx_) / 16.0) + 2.4 + l, T.EAU[8])
        t = (p + hz(i, 2, 936)) % 1.0
        if i % 3 == 0 and t < 0.7:
            P.point(x, 74.0 + 8 * t, T.EAU[7])
    # La file de cairns, à demi enfouis, qui se perd dans le blanc ; un ruban orange noué au premier.
    for i, (x, y, k) in enumerate(((150.0, 68.0, 1.5), (132.0, 60.0, 1.1), (120.0, 55.6, 0.8), (112.0, 52.6, 0.6), (106.0, 50.6, 0.45), (40.0, 64.0, 1.3))):
        cairn(P, x, y, k)
        if i > 2:
            voile(P, np.hypot(X - x, Y - y + 4 * k) < 7 * k, NE4, 0.5)
    v = onde(p)
    P.poly([(151.0, 55.0), (156.0, 54.0 + 0.6 * v), (160.0, 55.6 - 0.6 * v), (156.0, 56.6 + 0.6 * v)], LA1)
    for i in range(40):                                         # la neige qui tombe encore, lente
        t = (p + hz(i, 1, 937)) % 1.0
        x, y = -6 + 204 * hz(i, 2, 937) + 3 * math.sin(t * 6.283 + i), -16 + 96 * ((hz(i, 3, 937) + t * 0.25) % 1.0)
        P.point(x, y, NE1 if y < 40 else NE2)
    for g in range(3):
        brume_claire(P, 46.0 + g * 6.0, 3.0, 46 + g, BLANC, 0.5)
    tab.plan("premier", 1.0)
    f_sol = lambda x: 72.0 + 1.2 * np.sin(_a(x) / 17.0) + 6.0 * np.exp(-((_a(x) - 96) / 24.0) ** 2)
    m = Y > f_sol(X)
    P.rampe(m, 0.8 + 0.25 * (pg.fbm(X / 10.0, Y / 2.0, 3, 938) - 0.5), [NE2, NE3, NE4, BLANC], 0.9)
    P.remplir(P.crete(m), BLANC)
    for i in range(8):                                          # des traces de pattes dans la neige fraîche
        P.ell(20 + i * 5.6, 76.0 + (i % 2) * 1.0, 1.0, 0.5, NE1)
    for (x, h) in ((8.0, 10.0), (184.0, 14.0)):                  # deux piquets de balisage, givrés
        P.rect(x - 0.6, 80 - h - 8, 1.2, h + 8, BO2)
        P.rect(x - 0.6, 80 - h - 8, 1.2, 3.0, LA1)
        P.rect(x - 1.0, 80 - h - 9, 2.0, 1.2, NE4)


# =====================================================================================================================
# Le Trou-qui-Siffle : une galerie sombre creusée dans la roche, des parois lisses polies par le vent, des alcôves de
# part et d'autre, la poussière qui file à l'horizontale, une lueur pâle très loin au fond ; bleu nuit et gris.
# =====================================================================================================================
@decor("petit-nuage", "trou-qui-siffle", soleil=(150.0, 34.0), tons=NUIT, nom="Le Trou-qui-Siffle")
def trou_qui_siffle(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    fx_, fy_ = 150.0, 34.0                                      # le fond de la galerie : la lueur
    tab.plan("ciel", 0.0)
    r = np.hypot(X - fx_, (Y - fy_) * 1.25)
    P.rampe(np.ones(X.shape, dtype=bool), 1.0 - r / 60.0, [T.CIEL[2], T.CIEL[4], T.CIEL[7], T.CIEL[10], BLANC], 0.9)
    tab.plan("lointains", 0.2)
    # ---- La galerie : des anneaux de roche de plus en plus proches, polis ; chaque anneau a ses stries de vent.
    for i, (rr, c0) in enumerate(((10.0, 3), (17.0, 2), (27.0, 2), (40.0, 1), (58.0, 1), (82.0, 0))):
        k = rr / 10.0
        cx, cy = fx_ - (rr - 10) * 0.75, fy_ + (rr - 10) * 0.1
        d = np.hypot(X - cx, (Y - cy) * 1.25) + rr * 0.12 * (pg.fbm(X / (3.0 * k), Y / (3.0 * k), 3, 940 + i) - 0.5)
        roche = d > rr
        ang = np.arctan2(Y - cy, X - cx)
        v = 0.75 - 0.16 * i + 0.35 * np.cos(ang - 0.2) * 0.5 + 0.25 * (pg.fbm(ang * 6.0, d / (2.0 * k), 3, 946 + i) - 0.5) - (d - rr) / (30.0 * k)
        P.rampe(roche, v, [ENCRE, NU1, NU2, R1, R2, R3], 0.85)
        if i < 3:                                              # le bord poli des anneaux du fond prend la lueur
            P.remplir(roche & (d < rr + 0.4 * k) & (np.cos(ang - 0.2) > 0.2), R3)
    tab.plan("moyen", 0.5)
    # ---- Les alcôves : des niches rondes dans la paroi ; dans chacune, quelque chose d'oublié (un nid, des os de vent,
    # une lanterne morte, un flûtiau).
    for i, (x, y, rr) in enumerate(((28.0, 24.0, 9.0), (64.0, 8.0, 7.0), (22.0, 56.0, 8.0), (100.0, 2.0, 5.0))):
        P.ell(x, y, rr, rr * 1.2, ENCRE)
        P.ell(x + 0.8, y + 0.8, rr * 0.86, rr * 1.04, NU1)
        P.remplir((np.hypot((X - x) / rr, (Y - y) / (rr * 1.2)) < 1.0) & (np.hypot((X - x - 1.5) / rr, (Y - y - 1.5) / (rr * 1.2)) > 0.92), R2)
        if i == 0:
            P.ell(x, y + 7.0, 5.0, 2.0, BO2)                    # un nid
            for q in range(3):
                P.ell(x - 2 + q * 2, y + 6.0, 1.0, 1.2, NE3)
        elif i == 1:
            for q in range(4):                                  # des tuyaux d'orgue de pierre : c'est eux qui sifflent
                P.rect(x - 4 + q * 2.4, y + 5.0 - q * 2.0, 1.6, 4.0 + q * 2.0, R3)
                P.rect(x - 4 + q * 2.4, y + 5.0 - q * 2.0, 0.5, 4.0 + q * 2.0, R4)
        elif i == 2:
            P.rect(x - 1.6, y + 3.0, 3.2, 5.0, R1)              # une lanterne morte
            P.rect(x - 1.0, y + 3.8, 2.0, 3.4, NU2)
            P.courbe([(x - 1.4, y + 3.0), (x, y + 1.0), (x + 1.4, y + 3.0)], R2, 1)
    # Le sol : une dalle lisse, creusée d'une rigole ; le sable qui court dessus.
    sol = Y > 66.0 + 3.0 * np.sin(X / 30.0) - (X - 30) * 0.05
    P.rampe(sol, 0.4 + 0.3 * (pg.fbm(X / 14.0, Y / 1.4, 3, 952) - 0.5) + 0.4 * np.exp(-((X - 130) / 40.0) ** 2) * np.exp(-(Y - 66) / 9.0), [ENCRE, NU1, NU2, R1, R2, R3], 0.85)
    # ---- Le vent : la poussière file à l'horizontale, par longues traînées claires, du fond vers nous.
    for i in range(70):
        t = (p + hz(i, 1, 953)) % 1.0
        y = -10 + 86 * hz(i, 2, 953)
        dist = 1.0 - t
        x = fx_ - 6 - (170 * t) * (0.6 + 0.8 * hz(i, 3, 953))
        yy = fy_ + (y - fy_) * (0.2 + 0.8 * t)
        l = 2 + 12 * t
        if x > -8:
            P.trait(x, yy, x + l, yy - (yy - fy_) * 0.03, T.CIEL[9] if dist > 0.6 else (T.CIEL[7] if dist > 0.3 else T.CIEL[5]))
    for g in range(3):
        d = pg.fbm((X + 30 * p * (1 + g)) / 16.0, Y / 2.0, 3, 954 + g)
        voile(P, (d > 0.62) & (np.abs(Y - fy_ - (g - 1) * 14) < 10), T.CIEL[6], 0.3)
    tab.plan("premier", 1.0)
    # ---- Premier plan : la paroi toute proche, à gauche, noire ; un pan de roche à droite ; une écharpe prise au vent.
    m = P.poly([(-6, -16), (16, -16), (10, 10), (14, 40), (6, 62), (12, 80), (-6, 80)], ENCRE)
    P.remplir(m & (pg.fbm(X / 2.0, Y / 9.0, 3, 957) > 0.6), NU1)
    m2 = P.poly([(198, -16), (176, -16), (184, 12), (180, 30), (188, 50), (198, 54)], ENCRE)
    P.remplir(m2 & (pg.fbm(X / 2.0, Y / 9.0, 3, 958) > 0.6), NU1)
    ex, ey = 182.0, 40.0
    pts = [(ex, ey)] + [(ex - 6 * j, ey + 2.0 * math.sin(j * 1.3 + p * 6.283) + j * 0.6) for j in range(1, 6)]
    P.courbe(pts, LA1, P.ep(1.4), P.ep(0.6))
    P.courbe([(q[0], q[1] - 0.5) for q in pts], LA2, 1)
    voile(P, Y > 78.0, ENCRE, 0.4)


# =====================================================================================================================
# La Grande Salle : une caverne immense traversée par un fleuve de vent, visible à la poussière qu'il charrie ; une
# corniche étroite le long de la paroi, des grappes de chauves-souris au plafond, un puits de lumière vertical au fond.
# =====================================================================================================================
@decor("petit-nuage", "grande-salle", soleil=(140.0, -40.0), tons=NUIT, nom="La Grande Salle")
def grande_salle(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    P.rampe(np.ones(X.shape, dtype=bool), 0.35 + 0.3 * (pg.fbm(X / 26.0, Y / 16.0, 3, 960) - 0.5) + 0.3 * np.exp(-((X - 140) / 30.0) ** 2), [ENCRE, NU1, NU2, T.CIEL[4]], 0.9)
    tab.plan("lointains", 0.2)
    # ---- Le puits de lumière, tout au fond : une colonne claire qui tombe de la voûte ; la poussière y brille.
    rai(P, 140.0, -16.0, 62.0, 16.0, 0.02, T.CIEL[9], 0.6, 40, 961)
    rai(P, 140.0, -16.0, 62.0, 6.0, 0.02, BLANC, 0.5, 0, 962)
    halo(P, 141.0, 60.0, 22.0, T.CIEL[8], 0.5, ry=7)
    # Les piliers et les concrétions du fond, bleus dans la distance.
    for i, (x, w) in enumerate(((20.0, 9.0), (52.0, 6.0), (84.0, 8.0), (112.0, 5.0), (170.0, 10.0), (186.0, 6.0))):
        l = w * (1 + 0.5 * np.abs(Y - 26) / 40.0) * (0.8 + 0.3 * pg.fbm(Y / 5.0, Y * 0 + i, 2, 963))
        m = (np.abs(X - x) < l / 2) & (Y < 62)
        P.rampe(m, 0.45 + 0.3 * (X - x) / w * (1 if x < 140 else -1) + 0.2 * (pg.fbm(X / 2.0, Y / 8.0, 3, 964 + i) - 0.5), [NU1, NU2, T.CIEL[3], T.CIEL[4], T.CIEL[5]], 0.8)
    tab.plan("moyen", 0.5)
    # ---- La voûte : des draperies de pierre, des stalactites ; les chauves-souris en grappes (l'une s'étire, une autre s'envole).
    voute = Y < -4.0 + 10.0 * pg.fbm(X / 12.0, X * 0, 3, 970) + 7.0 * np.abs(np.sin(X / 7.0)) ** 5
    P.rampe(voute, 0.4 + 0.5 * (pg.fbm(X / 3.0, Y / 5.0, 3, 971) - 0.5), [ENCRE, NU1, NU2, R1], 0.85)
    for g, (x0, n) in enumerate(((36.0, 9), (78.0, 6), (118.0, 8), (168.0, 7))):
        for i in range(n):
            x = x0 + (i - n / 2) * 2.2 + hz(i, g, 972)
            y = float(-4.0 + 10.0 * pg.fbm(x / 12.0, 0.0, 3, 970)) + 1.0 + (i % 2) * 1.2
            P.poly([(x - 1.0, y), (x + 1.0, y), (x + 0.6, y + 3.4), (x, y + 4.4), (x - 0.6, y + 3.4)], ENCRE)
            if (g + i) % 5 == 0 and int(p * 8) % 4 < 2:
                P.poly([(x - 1.0, y + 1.0), (x - 3.4, y + 2.6), (x - 1.0, y + 3.0)], NU1)       # elle ouvre une aile
            if (g * 7 + i) % 6 == 0:
                P.point(x - 0.3, y + 3.4, LA2 if (p + 0.1 * i) % 1.0 < 0.8 else ENCRE)       # un œil
    for i in range(4):                                          # celles qui volent, dans le puits de lumière
        t = (p + i / 4.0) % 1.0
        x, y = 126 + 28 * math.sin(t * 6.283 + i), 16 + 24 * hz(i, 1, 973) + 6 * math.cos(t * 6.283 * 2 + i)
        a = onde(p * 2, 0.2 * i)
        P.trait(x - 2.4, y - 1.0 * a, x, y, ENCRE, P.ep(0.5))
        P.trait(x, y, x + 2.4, y - 1.0 * a, ENCRE, P.ep(0.5))
    # Le gouffre : en bas, le noir ; le fleuve de vent le traverse, une large coulée de poussière claire qui serpente.
    gouffre = Y > 62.0
    P.rampe(gouffre, 0.25 + 0.3 * (pg.fbm(X / 12.0, Y / 3.0, 3, 974) - 0.5) - 0.01 * (Y - 62), [ENCRE, NU1, NU2], 0.85)
    axe = 48.0 + 9.0 * np.sin(X / 34.0 + 1.0) + 3.0 * np.sin(X / 11.0)
    larg = 9.0 + 3.0 * np.sin(X / 23.0)
    flux = pg.fbm((X + 40 * p) / 9.0, (Y - axe) / 1.6, 3, 975)
    dans = np.abs(Y - axe) < larg
    voile(P, dans & (flux > 0.5), T.CIEL[6], 0.6 * (1 - np.abs(Y - axe) / larg))
    voile(P, dans & (flux > 0.62), T.CIEL[9], 0.7 * (1 - np.abs(Y - axe) / larg))
    for i in range(60):                                         # les grains les plus gros, qui filent
        t = (p + hz(i, 1, 976)) % 1.0
        x = (-10 + 212 * ((hz(i, 2, 976) + t) % 1.0))
        y = 48.0 + 9.0 * math.sin(x / 34.0 + 1.0) + 3.0 * math.sin(x / 11.0) + (hz(i, 3, 976) - 0.5) * 16
        P.trait(x, y, x + 3 + 4 * hz(i, 4, 976), y - 0.3, BLANC if i % 3 == 0 else T.CIEL[8])
    tab.plan("premier", 1.0)
    # ---- La corniche étroite où l'on marche (y = 74), le long de la paroi ; un garde-fou de corde ; des cairns ; le vide.
    f_c = lambda x: 72.6 + 1.0 * np.sin(_a(x) / 13.0) + 0.5 * np.sin(_a(x) / 4.0)
    corn = Y > f_c(X)
    P.rampe(corn, 0.45 + 0.4 * (pg.fbm(X / 5.0, Y / 2.0, 3, 977) - 0.5) + 0.3 * np.exp(-(Y - f_c(X)) / 1.2), [ENCRE, NU1, R1, R2, R3], 0.85)
    P.remplir(P.crete(corn) & (pg.fbm(X / 5.0, Y * 0, 2, 978) > 0.45), R4)
    for x in np.arange(4.0, 196.0, 18.0):
        y = float(f_c(x))
        P.rect(x - 0.5, y - 7.0, 1.0, 7.4, BO1)
        if x + 18 < 196:
            P.courbe([(x, y - 6.0), (x + 9, y - 3.6 + 0.4 * onde(p, x * 0.01)), (x + 18, float(f_c(x + 18)) - 6.0)], TE2, 1)
    cairn(P, 96.0, 74.0, 0.9, neige=False)
    paroi = P.poly([(-6, -16), (14, -16), (8, 20), (12, 50), (4, 80), (-6, 80)], ENCRE)
    P.remplir(paroi & (pg.fbm(X / 2.0, Y / 9.0, 3, 979) > 0.58), NU1)
    pg.lanterne(P, 9.0, 40.0, corde=3.6)
    voile(P, Y > 78.4, ENCRE, 0.4)


# =====================================================================================================================
# L'Abreuvoir (et l'Abreuvoir à l'aube) : un grand lac d'altitude cerné de sommets. Le soir, des centaines de nuages
# descendus boire, le ventre posé sur l'eau, lumière dorée, reflets immenses. À l'aube, après la première gelée : herbe
# blanche de givre, eau qui fume, le troupeau qui s'élève lentement en file vers le sud, ciel rose pâle et bleu froid.
# =====================================================================================================================
def _lac(P, tab, aube):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=40.0, haut=0.0, halo=0.34 if not aube else 0.26, etoiles=0.0 if not aube else 0.14, disque=5.4 if not aube else 4.0)
    tab.plan("nuages", 0.08)
    pg.voiles(P, y=-6.0, epais=9.0, seuil=0.6, graine=980)
    if aube:                                                    # le troupeau s'élève, en file, vers le sud (la gauche)
        for i in range(16):
            u = i / 15.0
            x = 176 - 170 * u + 1.0 * onde(p, 0.1 * i)
            y = 34 - 46 * u ** 0.8 - 1.2 * ((p + 0.07 * i) % 1.0) + 2 * math.sin(i * 1.7)
            petit_nuage(P, x, y, 16 - 9 * u, 5.0 - 2.6 * u, 990 + i, tons=[T.CIEL[4], T.CIEL[7], T.CIEL[9], T.CIEL[11], BLANC])
    tab.plan("lointains", 0.2)
    roches = [T.L0, T.L1, T.L2, T.L3] if not aube else [T.L1, T.L2, T.L3, T.L4]
    sommets(P, lambda x: deux_dents(x) - 4.0, roches, neige=11.0, graine=7, limite=30.0, bas=43.0)
    sommets(P, lambda x: pg.profil(x, 40.0, 16.0, 30.0, 981), roches, neige=5.0, graine=8, bas=43.0)
    brume_claire(P, 40.0, 3.0, 50, T.CIEL[9], 0.4)
    tab.plan("moyen", 0.5)
    f_rive = lambda x: 42.6 + 0.4 * np.sin(_a(x) / 9.0)
    pg.rive(P, f_rive, epais=1.2, joncs=40, graine=982)
    if not aube:                                                # le soir : le troupeau boit, serré, jusqu'à l'autre rive
        for i in range(34):
            u = hz(i, 1, 983) ** 0.7
            y = 46.0 + 22.0 * u
            x = 10 + 172 * hz(i, 2, 983)
            if (26 < x < 70 or 126 < x < 174) and y > 60:
                continue
            l = 7 + 16 * u
            petit_nuage(P, x + 0.5 * onde(p, 0.07 * i), y - 0.25 * abs(onde(p, 0.13 * i)), l, l * 0.34, 1000 + i, boit=True,
                        tons=[T.CIEL[5], T.CIEL[7], T.CIEL[9], T.CIEL[11], BLANC])
    f_berge = lambda x: 72.4 + 1.0 * np.sin(_a(x) / 19.0) + 0.4 * np.sin(_a(x) / 5.0) - 3.0 * np.exp(-((_a(x) - 4) / 24.0) ** 2)
    ronds = tuple((10 + 172 * float(hz(i, 2, 983)) - 4, 60.0 + 3 * i, 0.3 * i) for i in range(3))
    pg.miroir(P, tab.derriere(), 43.6, ronds=ronds, fonce=(62.0, 14.0), eclats=0.7, rides=0.04, graine=984)
    if aube:                                                    # l'eau fume ; la glace prend au bord
        for i in range(12):
            t = (p + i / 12.0) % 1.0
            x = 10 + 15 * i + 4 * math.sin(t * 6.283 + i)
            voile(P, np.hypot((X - x) / 1.4, Y - (60 - 18 * t)) < 2.0 + 5.0 * t, T.CIEL[11], 0.5 - 0.48 * t)
        for g in range(3):
            brume_claire(P, 47.0 + g * 5.0, 2.4, 52 + g, T.CIEL[11], 0.5)
        glace = (Y > f_berge(X) - 3.0 - 2.0 * pg.fbm(X / 6.0, X * 0, 2, 985)) & (Y <= f_berge(X) + 1)
        P.rampe(glace, 0.6 + 0.4 * (pg.fbm(X / 4.0, Y / 1.2, 2, 986) - 0.5), [T.EAU[6], T.EAU[8], NE3, NE4], 0.7)
    # Le rocher plat, dans l'eau, près du bord.
    rx, ry = 104.0, 68.0
    P.ell(rx, ry + 1.4, 13.0, 1.6, T.EAU[1])
    roc = P.poly([(rx - 11, ry + 1), (rx - 8, ry - 3), (rx + 7, ry - 4), (rx + 12, ry - 1), (rx + 11, ry + 1.4)], R2)
    P.rampe(roc, 0.4 + 0.1 * (ry - Y) * 2 + 0.3 * (pg.fbm(X / 3.0, Y / 2.0, 2, 987) - 0.5), [R1, R2, R3, R4], 0.7)
    P.remplir(P.crete(roc), NE3 if aube else LA2)
    tab.plan("premier", 1.0)
    # ---- La rive de galets ; l'herbe (dorée le soir, blanche de givre à l'aube) ; un genévrier ; des gentianes.
    galets = [T.N1, T.N2, R1, R2, R3]
    pg.sol(P, f_berge, galets, chemin=77.0, graine=988, lisere=0.5 if not aube else 2.0)
    for i in range(120):
        x, y = -6 + 204 * hz(i, 1, 989), float(f_berge(-6 + 204 * hz(i, 1, 989))) + 0.8 + 6 * hz(i, 2, 989)
        r = 0.7 + 1.5 * hz(i, 3, 989)
        if y < 79.6:
            P.ell(x, y, r, r * 0.6, (R1, R2, R3, R4)[i % 4])
            P.point(x - r * 0.3, y - r * 0.3, NE3 if aube else LA2)
    pg.touffes(P, f_berge, n=150, haut=3.6, graine=1040)
    if aube:
        voile(P, (Y > f_berge(X) - 4) & (P.a >= 0) & (pg.fbm(X / 1.6, Y / 1.2, 2, 1041) > 0.5), NE4, 0.6)       # le givre
    for i in range(10):
        x = 6 + 20 * i + 6 * hz(i, 1, 1042)
        if not (20 < x < 62 or 130 < x < 172):
            pg.fleur(P, x, float(f_berge(x)) + 1.4, 1.6 + hz(i, 2, 1042), T.BLEU if i % 2 else T.VIOLET, CREME)
    P.volumes([(186, 70, 9), (194, 64, 7), (178, 75, 6)], [T.N0, T.N1, T.S0, T.S1, NE3 if aube else PJ2], (-0.7, -0.5, 0.3), grain=1.0, graine=1043,
              gain=0.6, base=0.36, trame=0.85)
    pg.roseaux(P, -6.0, 10.0, n=7, haut=(10.0, 26.0), penche=1.0, graine=1044)
    if not aube:
        pg.lucioles(P, [(14.0, 66.0), (180.0, 60.0), (70.0, 77.0), (150.0, 76.0)], graine=1045)


@decor("petit-nuage", "abreuvoir", soleil=(60.0, 30.0), tons=SOIR, nom="L'Abreuvoir")
def abreuvoir(P, tab):
    _lac(P, tab, aube=False)


@decor("petit-nuage", "abreuvoir-aube", soleil=(150.0, 34.0), tons=ROSE, nom="L'Abreuvoir à l'aube")
def abreuvoir_aube(P, tab):
    _lac(P, tab, aube=True)


# =====================================================================================================================
# La fenêtre de la maison : le rebord intérieur d'une fenêtre, le soir. Une vitre embuée où l'on a dessiné du doigt, une
# petite casserole, un baluchon posé ; dehors un ciel d'hiver traversé de nuages ; la lumière d'une lampe.
# =====================================================================================================================
@decor("petit-nuage", "fenetre-maison", soleil=(96.0, 20.0), tons=NUIT, nom="La fenêtre de la maison")
def fenetre_maison(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    # ---- Dehors : un ciel d'hiver, bleu profond ; les nuages qui passent (le troupeau, là-haut) ; les deux dents, au loin.
    pg.ciel(P, horizon=50.0, haut=0.1, halo=0.0, etoiles=0.3, lune=(132.0, 2.0, 3.4), disque=0)
    tab.plan("nuages", 0.08)
    for i in range(7):
        x = (20 + 26 * i + 14 * p) % 190 + 2
        petit_nuage(P, x, 8 + 10 * hz(i, 1, 1050) + 0.4 * onde(p, 0.1 * i), 12 + 8 * hz(i, 2, 1050), 3.6 + 2 * hz(i, 3, 1050), 1051 + i,
                    tons=[T.CIEL[3], T.CIEL[5], T.CIEL[7], T.CIEL[9], T.CIEL[11]], yeux=False)
    tab.plan("lointains", 0.2)
    sommets(P, lambda x: deux_dents(x) + 6.0, [T.CIEL[1], T.CIEL[2], T.CIEL[4], T.CIEL[5]], neige=8.0, graine=9, limite=36.0)
    f_j = lambda x: 50.0 + 1.5 * np.sin(_a(x) / 15.0)
    P.rampe(Y > f_j(X), 0.5 + 0.3 * (pg.fbm(X / 8.0, Y / 2.0, 3, 1060) - 0.5), [NU1, NU2, T.CIEL[4], T.CIEL[6]], 0.8)   # le jardin sous la neige
    for (x, h, g) in ((60.0, 12.0, 1061), (128.0, 16.0, 1062)):
        meleze(P, x, float(f_j(x)) + 2, h, g, dore=False)
    for i in range(30):                                         # il neige
        t = (p + hz(i, 1, 1063)) % 1.0
        P.point(40 + 112 * hz(i, 2, 1063) + 2 * math.sin(t * 6.283 + i), -10 + 70 * ((hz(i, 3, 1063) + t * 0.25) % 1.0), T.CIEL[10])
    tab.plan("moyen", 0.5)
    # ---- Le mur et la fenêtre : boiseries chaudes, quatre carreaux ; la buée, où un doigt a dessiné un nuage et un chemin.
    wx0, wx1, wy0, wy1 = 40.0, 152.0, -10.0, 56.0
    dedans = (X > wx0) & (X < wx1) & (Y > wy0) & (Y < wy1)
    d = np.hypot(X - 30, (Y - 40) * 1.2)
    P.rampe(~dedans, 0.85 - d / 180.0 + 0.2 * (pg.fbm(X / 3.0, Y / 20.0, 3, 1064) - 0.5), [BO1, BO2, BO3, ME1, ME2], 0.8)
    P.remplir(~dedans & (np.abs((X % 14.0) - 7.0) < 0.3) & (Y < 56), BO1)
    for (a, b, c2, dd) in ((wx0 - 3, wy0 - 3, wx1 - wx0 + 6, 3.0), (wx0 - 3, wy1, wx1 - wx0 + 6, 3.0), (wx0 - 3, wy0, 3.0, wy1 - wy0), (wx1, wy0, 3.0, wy1 - wy0)):
        P.rect(a, b, c2, dd, BO2)
    P.rect(wx0 - 3, wy0 - 3, wx1 - wx0 + 6, 0.8, BO3)
    P.rect((wx0 + wx1) / 2 - 1.2, wy0, 2.4, wy1 - wy0, BO2)
    P.rect(wx0, (wy0 + wy1) / 2 - 1.2, wx1 - wx0, 2.4, BO2)
    coin = np.minimum(np.minimum(X - wx0, wx1 - X), np.minimum(Y - wy0, wy1 - Y))
    buee = dedans & (pg.fbm(X / 12.0, Y / 9.0, 3, 1065) + 0.5 - coin / 30.0 > 0.6)
    voile(P, buee, T.CIEL[8], 0.5)
    trace = np.zeros(X.shape, dtype=bool)                       # le dessin du doigt : un petit nuage et un chemin en lacets
    for (cx_, cy_, r_) in ((70.0, 34.0, 4.0), (75.0, 32.0, 5.0), (81.0, 34.0, 4.0)):
        trace |= (np.abs(np.hypot(X - cx_, Y - cy_) - r_) < 0.7) & (Y < 35.0)
    trace &= ~((np.hypot(X - 75.0, Y - 32.0) < 4.3) & (Y < 35.0))
    trace |= (np.abs(Y - 35.4) < 0.7) & (X > 67) & (X < 84)
    trace |= np.abs(Y - (46.0 - 3.0 * np.sin((X - 88) / 5.0))) < 0.7
    trace &= dedans & (X > 62) & (X < 126)
    P.remplir(trace & (X < 86), T.CIEL[2])
    P.remplir(trace & (X >= 88) & (X < 126), T.CIEL[2])
    for k in range(3):                                          # une goutte qui descend du dessin
        t = (p + k / 3.0) % 1.0
        P.trait(70.0 + k * 22, 36 + 16 * t, 70.0 + k * 22, 38 + 16 * t, T.CIEL[3])
    # Le rideau à carreaux, retenu par une embrasse ; la lampe à pétrole, à gauche.
    for cote in (-1, 1):
        x0 = wx0 - 3 if cote < 0 else wx1 + 3
        r_ = P.poly([(x0, wy0 - 3), (x0 + cote * 22, wy0 - 3), (x0 + cote * 10 + 0.4 * onde(p), 30.0), (x0 + cote * 18, 56.0), (x0, 56.0)], CREME)
        P.remplir(r_ & ((np.floor(X / 3.0) + np.floor(Y / 3.0)) % 2 == 0), LA1)
        P.remplir(r_ & ((np.floor(X / 3.0)) % 2 == 0) & ((np.floor(Y / 3.0)) % 2 == 1), LA2)
        P.rect(x0 + cote * 7 - 2, 29.0, 6.0, 2.0, RO1)
    lx_, ly_ = 22.0, 48.0
    halo(P, lx_, ly_ - 8, 36.0, LA2, 0.5)
    halo(P, lx_, ly_ - 8, 12.0, LA3, 0.6)
    P.ell(lx_, ly_ + 5.0, 5.0, 3.0, RO2)
    P.ell(lx_, ly_ + 4.0, 3.6, 1.8, RO1)
    P.rect(lx_ - 1.6, ly_ - 1.0, 3.2, 4.0, PJ2)
    P.ell(lx_, ly_ - 7.0, 3.4, 6.4, LA3)
    P.ell(lx_, ly_ - 6.0, 1.4, 3.0, BLANC if int(p * 8) % 5 else LA2)
    # ---- Le rebord : une planche large, cirée ; la petite casserole (elle fume) ; le baluchon noué ; une paire de moufles.
    reb = (Y > 56.0)
    P.rampe(reb, 0.55 + 0.3 * (pg.fbm(X / 22.0, Y / 1.4, 3, 1066) - 0.5) - 0.012 * (Y - 56) + 0.3 * np.exp(-((X - 22) / 40.0) ** 2), [BO1, BO2, BO3, ME1, ME2], 0.8)
    P.remplir(reb & (Y < 56.8), TE3)
    cx_, cy_ = 86.0, 62.0                                       # la casserole
    P.ell(cx_, cy_ + 5.4, 9.0, 1.6, BO1)
    P.rect(cx_ - 7, cy_ - 3, 14.0, 8.0, R2)
    P.rect(cx_ - 7, cy_ - 3, 3.0, 8.0, R4)
    P.ell(cx_, cy_ - 3, 7.0, 1.8, R3)
    P.ell(cx_, cy_ - 3, 5.6, 1.2, LA2)
    P.rect(cx_ + 7, cy_ - 1.6, 12.0, 1.6, R1)
    P.rect(cx_ + 7, cy_ - 1.6, 12.0, 0.5, R3)
    for k in range(5):
        t = (p + k / 5.0) % 1.0
        voile(P, np.hypot(X - (cx_ + 2.4 * math.sin(t * 6 + k)), Y - (cy_ - 6 - 18 * t)) < 1.0 + 2.6 * t, CREME, 0.6 - 0.55 * t)
    bx_, by_ = 124.0, 66.0                                      # le baluchon : un carré de tissu à pois, noué sur un bâton
    P.trait(bx_ - 20, by_ + 3, bx_ + 12, by_ - 14, BO2, P.ep(0.9))
    P.volumes([(bx_, by_ - 4, 8.0), (bx_ + 5, by_ - 1, 5.0), (bx_ - 5, by_ - 1, 5.0)], [NU2, T.CIEL[4], T.CIEL[6], T.BLEU], (-0.6, -0.5, 0.4), plancher=by_ + 3.4,
              grain=0.4, graine=1067, gain=0.5, base=0.5, trame=0.5)
    for i in range(12):
        P.point(bx_ - 7 + 14 * hz(i, 1, 1068), by_ - 9 + 10 * hz(i, 2, 1068), CREME)
    P.poly([(bx_ - 1, by_ - 11), (bx_ + 1, by_ - 11), (bx_ + 4, by_ - 16), (bx_ - 4, by_ - 15.4)], T.BLEU)        # le nœud
    P.ell(bx_ + 1, by_ + 4.0, 10.0, 1.4, BO1)
    for (x, c0) in ((150.0, LA1), (158.0, RO2)):
        P.ell(x, 66.0, 3.4, 4.4, c0)
        P.ell(x + 2.6, 64.6, 1.4, 1.8, c0)
        P.rect(x - 3.4, 68.6, 6.8, 2.0, CREME)
    tab.plan("premier", 1.0)
    # ---- Premier plan : le dossier d'une chaise à gauche, un pot de jacinthe à droite ; l'ombre de la pièce.
    P.rect(-2.0, 30.0, 3.0, 50.0, ENCRE)
    for y in (34.0, 44.0, 54.0):
        P.rect(-6.0, y, 8.0, 3.0, ENCRE)
    P.poly([(176.0, 70.0), (190.0, 70.0), (188.0, 80.0), (178.0, 80.0)], RO1)
    P.rect(175.0, 69.0, 16.0, 1.6, RO2)
    for i in range(4):
        P.courbe([(183.0, 69.0), (183.0 + (i - 1.5) * 3, 60.0), (183.0 + (i - 1.5) * 5 + 0.2 * onde(p, 0.1 * i), 54.0)], T.S1 if i % 2 else T.S2, P.ep(0.8), 1)
    for j in range(5):
        P.ell(183.0 + (j % 2) * 1.6 - 0.8, 50.0 + j * 1.8, 1.4, 1.2, T.VIOLET if j % 2 else T.BLEU)
    voile(P, Y > 78.0, ENCRE, 0.35)
    poussiere(P, 10, 10, 60, 56, 10, LA3, 1069)
