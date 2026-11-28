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


def dents(x, cx=99.0, k=1.0, base=46.0, miroir=False, serre=1.0):
    """Les deux sommets en forme de dents, un col arrondi entre eux : le fil du voyage. cx : où est le col ; k : la
    taille (0,4 : très loin ; 2 : on est dessous) ; base : le y de leur pied ; miroir : vus de l'autre versant ; serre :
    l'écart entre eux (moins de 1 : vus de biais, ils se recouvrent)."""
    x = _a(x)
    u = (x - cx) / k
    if miroir:
        u = -u
    g = 32.0 * np.maximum(0, 1 - np.abs(u + 25.0 * serre) / 36.0) ** 0.9
    d = 37.0 * np.maximum(0, 1 - np.abs(u - 25.0 * serre) / 40.0) ** 0.9
    col = 16.0 * np.exp(-(u / 18.0) ** 2)
    return base - k * np.maximum(np.maximum(g, d), col) - 3.0 * k * pg.fbm(x / (7.0 * k), x * 0, 3, 710)


def deux_dents(x):
    return dents(x)


def meleze(P, x, y, h, graine=0, dore=True):
    """Un mélèze : un tronc fin, des branches qui partent à l'horizontale et retombent, chargées de touffes d'aiguilles
    irrégulières (pas un triangle) ; doré à l'automne, sarcelle sinon. La lumière vient du côté du soleil."""
    T = pg.T
    tons = (PJ1, PJ2, PJ3, PJ4) if dore else (T.S0, T.S1, T.S2, T.S3)
    bois = BO1 if dore else T.N1
    cote_s = 1 if P.soleil[0] > x else -1
    P.trait(x, y, x + 0.02 * h * (hz(graine, 1, 720) - 0.5), y - h, bois, P.ep(0.4 + h / 34.0))
    n = int(5 + h / 3.2)
    for i in range(n):
        u = i / (n - 1.0)
        yy = y - h * (0.16 + 0.8 * u)
        l = (h * 0.34 * (1 - u) ** 0.8 + 0.7) * (0.75 + 0.5 * hz(i, 2, graine))
        for cote in (-1, 1):
            if hz(i, 3 + cote, graine) < 0.14 and 0.15 < u < 0.85:
                continue                                              # une branche manque : l'arbre respire
            lb = l * (0.8 + 0.4 * hz(i, 6 + cote, graine))
            bal = 0.25 * onde(P.p, (x + i) * 0.07)
            bout = (x + cote * lb + bal, yy + lb * 0.3)
            P.trait(x, yy, bout[0], bout[1], bois)
            k = max(2, int(lb / 1.3))
            for j in range(k):                                        # les touffes, le long de la branche
                t = (j + 1.0) / k
                px_, py_ = x + cote * lb * t + bal * t, yy + lb * 0.3 * t * t
                r = (0.9 + 0.5 * hz(i * 9 + j, 8 + cote, graine)) * (0.6 + 0.5 * (1 - u)) * min(1.6, 0.6 + h / 30.0)
                clair = 2 if cote == cote_s else 1
                P.ell(px_, py_ + r * 0.35, r, r * 0.75, tons[clair - 1])
                P.ell(px_ + cote_s * r * 0.2, py_ + r * 0.1, r * 0.7, r * 0.5, tons[clair])
                if hz(i * 9 + j, 12, graine) < 0.3:
                    P.point(px_ + cote_s * r * 0.3, py_ - r * 0.2, tons[3])
                if h > 26 and hz(i * 9 + j, 13, graine) < 0.5:
                    P.trait(px_, py_ + r, px_ - 0.2, py_ + r + 1.0, tons[0])  # la frange qui pend
    P.ell(x, y - h - 0.6, 0.7, 1.4, tons[2])


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
# Le jardin après l'orage (chapitre 1) : « Ce matin, le jardin est tout lavé. L'arrosoir a roulé jusqu'au portail. Et
# l'herbe est couchée dans le même sens, comme si quelqu'un l'avait peignée. » Le petit matin, le soleil bas à gauche ;
# la pelouse peignée qui luit, les flaques qui gardent le ciel, la palissade et son portail, la boîte aux lettres et le
# tas de bois derrière ; au fond, les ronces où Brouillon s'était pris (une mèche blanche y reste) ; le pot de fleurs
# retourné, la cabane de Pilou ; tout au loin, minuscules et blanches, les montagnes du bout du chemin.
# =====================================================================================================================
@decor("petit-nuage", "jardin-lave", soleil=(30.0, 2.0), tons=LAVE, nom="Le jardin après l'orage", matiere=True)
def jardin_lave(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    # ---- Le ciel lavé : bleu tendre, l'arc-en-ciel pâle (orange, crème, bleu, violet), les derniers nuages qui s'en vont.
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=44.0, haut=0.0, halo=0.36, disque=4.4)
    d = np.hypot(X - 150.0, (Y - 60.0) * 1.1)
    for i, c0 in enumerate((LA2, T.CIEL[11], T.BLEU, T.VIOLET)):
        voile(P, (np.abs(d - 74.0 + i * 1.5) < 0.75) & (Y < 42), c0, 0.3 + 0.08 * onde(p))
    pg.voiles(P, y=22.0, epais=7.0, seuil=0.6, graine=763)
    pg.cumulus(P, [(160, 4, 50, 8.5, 760, 10, 0.0), (82, -8, 36, 5.5, 761, 7, 0.4), (14, 14, 22, 3.6, 762, 5, 0.7)],
               dessous=-0.5)
    tab.plan("lointains", 0.2)
    # ---- Tout au loin : les deux Dents, minuscules et bleues, le haut blanc ; puis le bocage, de plus en plus net.
    massif(P, lambda x: dents(x, cx=150.0, k=0.27, base=41.0), [(143.2, 32.4), (156.8, 31.2)],
           [T.L2, T.L3, T.L4, T.L5], [T.L5, NE2, NE3, NE4], [T.L4, T.L5, NE2], NE4, 1200, brume=(T.CIEL[10], 34.0, 8.0))
    loin = lambda x: pg.profil(x, 41.0, 4.0, 18.0, 1201)
    pg.crete(P, loin, [T.L1, T.L2, T.L3, T.CIEL[9]], 0.6)
    proche = lambda x: 43.5 + 1.6 * np.sin(_a(x) / 13.0) + 0.6 * np.sin(_a(x) / 4.3)
    m = Y > proche(X)
    P.rampe(m, 0.55 + 0.35 * (pg.fbm(X / 5.0, Y / 1.2, 2, 1202) - 0.5) - 0.03 * (Y - 44), [T.S1, T.S2, T.S3, T.L3], 0.5)
    for i in range(16):                                               # haies et bosquets du bocage, leur ombre à droite
        x, y = -4 + 200 * hz(i, 1, 1203), 44.0 + 2.5 * hz(i, 2, 1203)
        r = 1.0 + 1.6 * hz(i, 3, 1203)
        P.ell(x + r * 0.6, y + 0.2, r * 1.2, r * 0.3, T.S0)
        mm = P.ell(x, y - r * 0.5, r, r * 0.8, T.S1)
        P.remplir(mm & (X < x - r * 0.2), T.S3)
    voile(P, Y > proche(X), T.CIEL[10], 0.25)
    tab.plan("moyen", 0.5)
    # ---- Derrière la palissade : le grand tilleul du voisin et une rangée de peupliers, encore ruisselants.
    for (x, h) in ((30.0, 30.0), (37.0, 34.0), (44.0, 28.0), (186.0, 32.0)):
        mp = (np.abs(X - x) < 2.6 * np.sqrt(np.clip((Y - 44.0 + h) / h, 0, 1)) * np.clip((44.0 - Y) / 6.0, 0.5, 1)) & (Y < 44) & (Y > 44 - h)
        P.rampe(mp, 0.5 - 0.35 * (X - x) / 2.6 + 0.25 * (pg.fbm(X / 0.8, Y / 1.6, 2, 1212 + int(x)) - 0.5), [T.S0, T.S1, T.S2, T.S3], 0.5)
    boules = []
    for i in range(34):
        a, r_ = 6.283 * hz(i, 1, 1213), hz(i, 2, 1213) ** 0.6
        boules.append((97 + 17 * r_ * math.cos(a), 18 + 12 * r_ * math.sin(a), 3.4 + 2.6 * hz(i, 3, 1213) * (1.2 - r_)))
    P.rect(94.0, 24.0, 3.0, 20.0, BO1)
    P.trait(95.0, 30.0, 104.0, 22.0, BO1, P.ep(0.7))
    P.trait(95.5, 32.0, 86.0, 24.0, BO1, P.ep(0.7))
    tl = P.volumes(boules, [T.N1, T.S0, T.S1, T.S2, T.S3, T.S4], (-0.62, -0.5, 0.4), grain=0.5, graine=1214, gain=0.65, base=0.45, trame=0.5)
    P.remplir(tl & (pg.fbm(X / 0.7, Y / 0.7, 2, 1215) > 0.7) & (X < 100), T.S4)
    for i in range(10):                                               # il s'égoutte
        t = (p + hz(i, 1, 1216)) % 1.0
        x = 80 + 32 * hz(i, 2, 1216)
        if t < 0.7:
            P.point(x, 30.0 + 10 * hz(i, 3, 1216) + 12 * t * t, T.EAU[7])
    # ---- La palissade, face à nous : planches éclairées à gauche, leur ombre sur l'herbe vers la droite ; le portail
    # entrouvert à droite (l'arrosoir a roulé jusque-là), la boîte aux lettres et le tas de bois derrière.
    pal = np.zeros(X.shape, dtype=bool)
    for x in np.arange(-6.0, 198.0, 4.6):
        if 150.0 < x < 166.0:
            continue
        h = 10.5 + 1.2 * hz(int(x * 3), 1, 766)
        pen = 1.4 if int(x * 3) % 37 == 4 else 0.0
        pm = P.masque_poly([(x, 51.0), (x + 4.0, 51.0), (x + 4.0 + pen, 51.0 - h), (x + 2.0 + pen, 51.0 - h - 1.8), (x + pen, 51.0 - h)])
        P.rampe(pm, 0.55 + 0.3 * (pg.fbm(X / 0.6, Y / 4.0, 2, 1204) - 0.5) - 0.25 * ((X - x) / 4.0), [TE1, TE2, TE3, CREME], 0.45)
        P.remplir(pm & (X < x + 0.5), CREME)                             # le liseré du soleil
        P.remplir(pm & (np.abs(Y - 51.0 + h * 0.45) < 0.25) & (hz(P.XI, 1, 1205) < 0.4), TE1)       # un nœud
        pal |= pm
    for yb in (42.6, 47.4):                                           # les traverses
        tr = (np.abs(Y - yb) < 0.5) & ((X < 150) | (X > 166))
        P.remplir(tr, TE2)
        P.remplir(tr & (Y < yb - 0.2), TE3)
        pal |= tr
    for i in range(14):                                               # la palissade s'égoutte
        x = -2 + 14 * i + 3 * hz(i, 1, 1206)
        t = (p + hz(i, 2, 1206)) % 1.0
        if t < 0.7:
            P.point(x, 51.0 - 3.0 + 6 * t * t, T.EAU[7])
    # Le portail ouvert vers nous, de biais ; derrière, le chemin qui part, la boîte aux lettres, le tas de bois.
    chemin = (X > 150) & (X < 166) & (Y > 44.0) & (Y < 51.4) & (np.abs(X - 158 + (Y - 51) * 0.6) < 3.0 + (Y - 44) * 0.7)
    P.rampe(chemin, 0.6 + 0.2 * (pg.fbm(X / 1.0, Y / 0.6, 2, 1207) - 0.5), [TE2, TE3, PJ4], 0.45)
    porte = P.masque_poly([(150.0, 51.6), (156.0, 53.0), (156.0, 41.6), (150.0, 40.6)])
    P.rampe(porte, 0.6 - 0.3 * (X - 150) / 6.0, [TE1, TE2, TE3], 0.45)
    P.trait(150.0, 44.0, 156.0, 45.4, TE1)
    P.trait(150.0, 49.0, 156.0, 50.4, TE1)
    P.trait(150.4, 50.0, 155.6, 42.0, TE1)
    P.rect(149.0, 38.0, 1.4, 14.0, BO2)
    P.rect(166.0, 38.0, 1.4, 14.0, BO2)
    P.rect(169.0, 36.0, 1.0, 9.0, BO2)                                # la boîte aux lettres, derrière, son drapeau orange
    P.rect(167.4, 33.4, 4.2, 3.0, T.BLEU)
    P.rect(167.4, 33.4, 4.2, 0.8, T.CIEL[3])
    P.rect(171.6, 32.4, 0.5, 2.6, LA1)
    for i in range(9):                                                # le tas de bois, ses bûches coupées
        x, y = 176.0 + (i % 4) * 2.6 + (i // 4) * 1.3, 42.0 - (i // 4) * 2.0
        P.ell(x, y, 1.3, 1.1, BO2)
        P.ell(x - 0.2, y - 0.1, 0.9, 0.8, TE3)
        P.point(x - 0.2, y - 0.1, TE2)
    # ---- Les ronces, au fond à gauche du portail : un massif sombre, des mûres, des gouttes, la mèche blanche.
    ronces = [(70 + 8 * i + 4 * hz(i, 1, 767), 49.5 - 3 * hz(i, 2, 767), 4.6 + 2.6 * hz(i, 3, 767)) for i in range(9)]
    mr = P.volumes(ronces, [T.S0, T.S1, T.S2, T.S3], (-0.6, -0.5, 0.4), plancher=52.0, grain=0.9, graine=768, gain=0.6,
                   base=0.42, trame=0.6)
    P.remplir(mr & (pg.fbm(X / 0.7, Y / 0.7, 2, 1208) > 0.68), T.N1)
    for i in range(40):                                               # les tiges épineuses qui dépassent
        x, y = 66 + 80 * hz(i, 1, 1209), 44 + 7 * hz(i, 2, 1209)
        a = -2.2 + 1.4 * hz(i, 3, 1209)
        P.courbe([(x, y), (x + 2.4 * math.cos(a), y + 2.4 * math.sin(a) - 0.6), (x + 4.4 * math.cos(a), y + 3.8 * math.sin(a))], T.S0, 1)
    for i in range(30):
        x, y = 68 + 74 * hz(i, 1, 769), 43.5 + 7 * hz(i, 2, 769)
        P.point(x, y, T.VIOLET if i % 3 else NU2, 2)
        if (p + hz(i, 3, 769)) % 1.0 < 0.3:
            P.point(x + 0.8, y - 0.8, BLANC)
    mx, my = 112.0, 44.6                                              # la mèche de nuage restée aux épines, qui flotte
    for j in range(5):
        t = j / 4.0
        P.ell(mx + 3.0 * t + 0.5 * onde(p, 0.2 * j), my - 1.0 * t + 0.3 * onde(p, 0.1 + 0.2 * j), 1.2 - 0.6 * t, 0.8 - 0.4 * t, NE4 if j % 2 else NE3)
    # Le pommier à gauche : un tronc, sa ramure ronde, des pommes ; il s'égoutte ; le linge trempé sur un fil.
    ombre_portee_j = (((X - 34.0) / 14.0) ** 2 + ((Y - 53.4) / 1.4) ** 2 < 1)
    voile(P, ombre_portee_j, T.S0, 0.5)
    pg.arbre_rond(P, 24.0, 52.0, 7.0, 770, tronc=8.0)
    for i in range(6):
        P.ell(17 + 3 * i + (i % 2), 38 + (i % 3) * 2.4, 0.9, 0.9, LA1)
        P.point(16.7 + 3 * i + (i % 2), 37.6 + (i % 3) * 2.4, LA2)
    for i in range(4):
        t = (p + i / 4.0) % 1.0
        P.point(18 + i * 3.4, 44 + 9 * t * t, T.EAU[7])
    for i in range(4):
        bal = 0.2 * onde(p, 0.2 * i)
        P.rect(36.0 + i * 5.0 + bal, 33.0, 4.0, 6.0 + (i % 2) * 2.0, (CREME, T.BLEU, LA2, CREME)[i])
        P.rect(36.0 + i * 5.0 + bal, 33.0, 0.8, 6.0 + (i % 2) * 2.0, NE3)
        pg.goutte(P, 38.0 + i * 5.0, 40.0 + (i % 2) * 2.0, 51.0, coul=T.EAU[7], d=0.2 * i)
    P.trait(34.0, 32.6, 60.0, 32.6, TE3)
    P.rect(60.0, 32.0, 0.8, 19.0, BO2)
    # La bergeronnette sur la palissade, qui hoche la queue ; le nichoir et sa mésange.
    bx, by = 126.0, 39.2
    P.ell(bx, by, 1.5, 0.9, NE3)
    P.ell(bx + 1.3, by - 0.7, 0.7, 0.6, ENCRE)
    P.point(bx + 1.6, by - 0.4, NE4)
    q = 1.0 if int(p * 8) % 2 else 0.0
    P.trait(bx - 1.4, by, bx - 3.8, by - 0.6 + q, ENCRE)
    # ---- La pelouse peignée par la pluie : des brins couchés vers la droite, plus longs près de nous, qui luisent.
    f_sol = lambda x: 51.0 + 0.4 * np.sin(_a(x) / 9.0)
    sol = Y > f_sol(X)
    prof_ = np.clip((Y - 51.0) / 29.0, 0, 1)
    v = 0.5 + 0.35 * (pg.fbm((X - Y * 1.4) / (3.0 + 6 * prof_), Y / (0.8 + 2 * prof_), 3, 771) - 0.5) + 0.12 * prof_
    P.rampe(sol, v, [T.S0, T.S1, T.S2, T.S3, T.S4], 0.45)
    voile(P, sol & ~pal, T.S0, np.where((Y > 51) & (Y < 53.5) & (X > 0), 0.45, 0.0))       # l'ombre de la palissade
    for i in range(420):                                              # les brins, un à un
        y = 51.5 + 28.5 * hz(i, 2, 1210) ** 0.8
        x = -6 + 204 * hz(i, 1, 1210)
        k = (y - 51.0) / 29.0
        l = 0.4 + 1.8 * k
        P.trait(x, y, x + l * 1.1, y - l * 0.45, (T.S2, T.S1, T.S0, T.S3)[i % 4] if hz(i, 3, 1210) > 0.04 else T.CIEL[9])
    luit = sol & (pg.fbm((X - Y * 1.4) / 1.6, Y / 3.0, 2, 772) > 0.8)
    P.remplir(luit & (P.T < 0.5), T.CIEL[9])                          # les brins mouillés qui prennent le ciel
    # Les flaques : le ciel dedans, le bord sombre, un rond quand une goutte tombe.
    for i, (x, y, rx) in enumerate(((70.0, 60.0, 11.0), (104.0, 68.0, 15.0), (176.0, 63.0, 9.0), (36.0, 75.0, 8.0), (150.0, 77.0, 8.0))):
        flaque(P, x, y, rx, graine=i)
    # ---- Le pot de fleurs, la cabane de Pilou, retourné : une petite porte, un caillou posé dessus (« fermé à clé »).
    cx, cy = 14.0, 66.0
    pot = P.masque_poly([(cx - 9.0, cy), (cx + 9.0, cy), (cx + 6.4, cy - 13.0), (cx - 6.4, cy - 13.0)])
    voile(P, (((X - cx - 9.0) / 11.0) ** 2 + ((Y - cy - 0.4) / 1.6) ** 2 < 1) & ~pot, T.S0, 0.6)
    P.rampe(pot, 0.75 - 0.5 * (X - cx + 9) / 18.0 + 0.1 * (pg.fbm(X / 1.2, Y / 1.2, 2, 1211) - 0.5), [RO1, RO2, LA1, LA2], 0.45)
    P.rect(cx - 7.2, cy - 13.8, 14.4, 2.2, RO2)
    P.rect(cx - 7.2, cy - 13.8, 14.4, 0.6, LA2)
    porte_ = (((X - cx) / 2.4) ** 2 + ((Y - cy + 3.6) / 3.6) ** 2 < 1) & (Y < cy)
    P.remplir(porte_, BO2)
    P.remplir(porte_ & (np.abs(X - cx) < 0.25), BO1)
    P.point(cx + 1.2, cy - 2.6, PJ3)
    P.ell(cx + 0.6, cy - 15.6, 2.6, 1.6, R2)                           # le caillou
    P.ell(cx - 0.2, cy - 16.2, 1.4, 0.6, R4)
    P.ell(cx - 5.0, cy - 8.0, 1.2, 1.0, CREME)                         # un petit hublot
    P.ell(cx - 5.0, cy - 8.0, 0.7, 0.6, T.CIEL[6])
    # ---- L'arrosoir renversé, la clé de la scène : il a roulé jusqu'au portail, il se vide encore ; son ombre.
    ax, ay = 142.0, 72.0
    P.ell(ax + 4, ay + 0.9, 18.0, 2.2, T.S0)
    corps = P.masque_poly([(ax - 10, ay - 12), (ax + 8, ay - 14), (ax + 10, ay - 1), (ax - 12, ay + 0.6)])
    P.rampe(corps, 0.95 - 0.06 * (ay - Y) * -1 - 0.4 * (X - ax + 10) / 20.0 + 0.15 * (pg.fbm(X / 3.0, Y / 2.0, 2, 773) - 0.5),
            [R1, R2, R3, R4, NE3], 0.45)
    P.remplir(corps & (np.abs(Y - ay + 7.0 + (X - ax) * 0.11) < 0.4), R2)                    # la soudure
    P.remplir(P.crete(corps), NE4)
    P.ell(ax - 11, ay - 5.6, 2.4, 6.4, R2)
    P.ell(ax - 11, ay - 5.6, 1.6, 5.2, ENCRE)
    P.ell(ax - 11.6, ay - 8.0, 0.4, 1.6, R4)
    P.poly([(ax + 9, ay - 8), (ax + 22, ay - 15), (ax + 23, ay - 13), (ax + 10, ay - 5)], R3)
    P.trait(ax + 9, ay - 8, ax + 22, ay - 15, R4)
    P.ell(ax + 23.4, ay - 14.4, 1.6, 2.4, R2)
    for k in range(6):
        t = (p + k / 6.0) % 1.0
        P.point(ax + 24.6 + 1.6 * t, ay - 14.0 + 13.0 * t * t, T.EAU[7] if k % 2 else BLANC)
    P.courbe([(ax - 4, ay - 13.4), (ax, ay - 20.0), (ax + 6, ay - 14.2)], R2, P.ep(0.9))
    P.courbe([(ax - 3.6, ay - 13.8), (ax, ay - 19.6)], R4, 1)
    flaque(P, ax + 26.0, ay + 0.4, 5.0, graine=9)
    # Des moineaux qui se baignent dans la grande flaque, un escargot et son sillage d'argent, des vers, la terre qui fume.
    for i in range(3):
        x = 96.0 + i * 5.0
        bat = int(p * 8 + i) % 3 == 0
        P.ell(x, 66.6, 1.4, 1.0, TE2)
        P.ell(x + 1.0, 65.8, 0.7, 0.7, TE1)
        P.point(x + 1.6, 65.8, PJ3)
        if bat:
            P.trait(x - 1.4, 66.0, x - 2.4, 65.0, TE3)
            P.point(x - 2.0, 64.2, T.EAU[8])
    sx = 58.0 + 0.6 * p
    P.trait(46.0, 71.6, sx, 71.4, T.CIEL[10])
    P.ell(sx + 1.2, 70.6, 1.4, 1.3, TE2)
    P.ell(sx + 1.2, 70.6, 0.7, 0.7, TE3)
    P.ell(sx + 3.0, 71.4, 1.6, 0.5, CREME)
    P.trait(sx + 4.0, 71.0, sx + 4.6, 69.6, CREME)
    for i in range(3):
        P.courbe([(116 + i * 22, 77.0 + i * 0.6), (118 + i * 22, 76.2 + i * 0.6 + 0.3 * onde(p, 0.3 * i)), (120.4 + i * 22, 77.0 + i * 0.6)], LA1, 1)
    pg.vapeur(P, 100.0, 58.0, coul=T.CIEL[11], h=12.0, n=4)
    pg.vapeur(P, 58.0, 60.0, coul=T.CIEL[11], h=10.0, n=3, d=0.4)
    pg.papillon_de_nuit(P, 88.0, 54.0, 4.0, coul=CREME, d=0.3)
    tab.plan("premier", 1.0)
    # ---- Premier plan : les grandes feuilles de rhubarbe, lourdes d'eau, à gauche et à droite ; leurs côtes orange ;
    # les gouttes qui s'en détachent. Elles cadrent sans toucher la place de Pilou ni celle de son interlocuteur.
    for (fx, fy, r, a0, g) in ((-4.0, 82.0, 15.0, -1.0, 774), (8.0, 84.0, 10.0, -0.5, 775), (196.0, 84.0, 13.0, -2.2, 776)):
        cx_, cy_ = fx + r * math.cos(a0) * 0.8, fy + r * math.sin(a0) * 0.8
        fe = (((X - cx_) / r) ** 2 + ((Y - cy_) / (r * 0.55)) ** 2 < 1 + 0.25 * np.sin(np.arctan2(Y - cy_, X - cx_) * 9 + g))
        vf = 0.55 - 0.35 * (X - cx_) / r - 0.2 * (Y - cy_) / r + 0.15 * (pg.fbm(X / 1.4, Y / 1.4, 2, g) - 0.5)
        P.rampe(fe, vf, [T.N1, T.S0, T.S1, T.S2, T.S3], 0.45)
        ang = np.arctan2(Y - fy, X - fx)
        for k in range(5):                                            # les nervures
            ak = a0 - 0.6 + 0.3 * k
            P.remplir(fe & (np.abs(ang - ak) < 0.03) & (np.hypot(X - fx, Y - fy) < r * 1.4), T.S3)
        P.trait(fx, fy, cx_, cy_, LA1, P.ep(0.7))
        P.remplir(P.crete(fe), T.S4)
        for k in range(2):
            t = (p + hz(k, 2, g)) % 1.0
            gx, gy = cx_ + r * 0.6 * (hz(k, 3, g) - 0.5), cy_ - r * 0.2
            P.point(gx, gy, BLANC)
            if t < 0.8:
                P.point(gx + 0.3, gy + 2.0 + 14 * t * t, T.EAU[8])
    pg.feuillage(P, lambda x: -14.0 + 0.36 * (_a(x) - 150.0) + 2.0 * np.sin(_a(x) / 5.0) + 0.8 * np.sin(_a(x) / 2.1), x0=146, x1=200,
                 n=520, epais=7.0, graine=1217, y_max=4.0)
    pg.touffes(P, lambda x: 79.0 + 0.0 * _a(x), n=60, haut=2.2, graine=776)
    poussiere(P, 20, 0, 180, 48, 12, T.CIEL[11], 777)


# =====================================================================================================================
# Le chemin creux (chapitre 2) : « Le chemin passe entre deux haies. Il fait beau. » Puis : « Plus de haies, plus
# d'ombre : un chemin de craie, tout blanc, sous un soleil d'automne qui cogne encore. » Un chemin en perspective entre
# deux haies de noisetiers, ses ornières et sa bande d'herbe ; au bout, les haies s'arrêtent et le chemin devient la
# craie blanche qui file dans les chaumes, vers les montagnes encore bleues. Le soleil d'automne, haut à gauche : la
# haie de gauche jette son ombre sur le chemin, la haie de droite a sa face au soleil.
# =====================================================================================================================
@decor("petit-nuage", "chemin-creux", soleil=(52.0, -8.0), tons=LAVE, nom="Le chemin creux", matiere=True)
def chemin_creux(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    FX_, FY_ = 102.0, 38.0                                            # le bout du chemin creux
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=38.0, haut=0.04, halo=0.42, disque=4.2)
    pg.voiles(P, y=-4.0, epais=7.0, seuil=0.6, graine=1220)
    pg.cumulus(P, [(160, 6, 34, 6.0, 1221, 7, 0.1), (24, 16, 24, 4.0, 1222, 6, 0.6), (44, 4, 30, 4.6, 1238, 7, 0.4)], dessous=-0.5)
    tab.plan("lointains", 0.2)
    # ---- Les montagnes, encore loin et bleues ; les deux Dents se lisent déjà, avec leur col.
    massif(P, lambda x: dents(x, cx=104.0, k=0.48, base=38.5), [(91.0, 22.1), (115.0, 20.3)],
           [T.L1, T.L2, T.L3, T.L4], [T.L5, NE2, NE3, NE4], [T.L3, T.L4, NE2], NE4, 1223, brume=(T.CIEL[10], 26.0, 10.0))
    pg.crete(P, lambda x: pg.profil(x, 38.6, 3.0, 14.0, 1224), [T.L2, T.L3, T.L4, T.CIEL[9]], 0.6)
    # ---- Les chaumes au loin, où file le chemin de craie, tout blanc ; un épouvantail, une ferme, des moutons.
    champ = Y > 38.4 + 0.3 * np.sin(X / 5.0)
    P.rampe(champ, 0.6 + 0.3 * (pg.fbm(X / 3.0, Y / 0.5, 2, 1225) - 0.5) + 0.04 * (Y - 39), [PJ1, PJ2, PJ3, PJ4], 0.5)
    craie = champ & (np.abs(X - FX_ - 2.0 * np.sin((Y - 38) * 0.9)) < 0.4 + (Y - 38.4) * 0.9)
    P.rampe(craie, 0.8 + 0.2 * (pg.fbm(X / 0.8, Y / 0.4, 2, 1226) - 0.5), [TE3, PJ4, CREME, BLANC], 0.45)
    voile(P, champ, T.CIEL[10], 0.2)
    pg.maison(P, 60.0, 39.4, p, grande=False)
    for i, x in enumerate((128.0, 133.0, 140.0)):
        P.ell(x, 40.0, 0.9, 0.5, CREME)
        P.point(x + 0.8, 39.8, TE1)
    P.trait(150.0, 41.0, 150.0, 36.0, BO2)
    P.trait(148.0, 37.6, 152.0, 37.6, BO2)
    P.ell(150.0, 36.2, 0.8, 0.8, TE3)
    P.poly([(148.6, 35.6), (151.4, 35.6), (150.0, 34.2)], LA1)
    tab.plan("moyen", 0.5)
    # ---- Le chemin creux : deux ornières de terre claire, la bande d'herbe au milieu ; il fuit vers le bout des haies.
    def rang(y):                                                      # largeur du chemin à la ligne y
        return np.clip((y - FY_) / (80.0 - FY_), 0, 1)

    k = rang(Y)
    u = (X - FX_) / np.maximum(k * 44.0 + 1.6, 1e-3)                  # -1..1 d'un bord à l'autre
    route = (Y > FY_ + 0.3) & (np.abs(u) < 1)
    prof_ = 30.0 / np.maximum(Y - FY_, 0.5)
    P.rampe(route, 0.62 + 0.2 * (pg.fbm(u * 6, prof_ * 2.0, 2, 1227) - 0.5) + 0.08 * k, [TE1, TE2, TE3, PJ4, CREME], 0.45)
    orn = route & (np.abs(np.abs(u) - 0.45) < 0.1)
    P.rampe(orn, 0.4 + 0.2 * (pg.fbm(u * 8, prof_ * 3.0, 2, 1228) - 0.5), [TE1, TE2, TE3], 0.45)
    herbe_m = route & (np.abs(u) < 0.22) & (pg.fbm(u * 10, prof_ * 4.0, 2, 1229) > 0.35)
    P.rampe(herbe_m, 0.6 + 0.3 * (pg.fbm(X / 1.0, Y / 0.6, 2, 1230) - 0.5), [OC2, PJ1, PJ2, PJ3], 0.45)
    for i in range(70):                                               # des cailloux dans les ornières
        y = FY_ + 1.0 + 41.0 * hz(i, 1, 1231) ** 0.7
        uu = (0.45 + 0.25 * (hz(i, 2, 1231) - 0.5)) * (1 if i % 2 else -1)
        x = FX_ + uu * (float(rang(y)) * 44.0 + 1.6)
        r = 0.2 + 0.7 * float(rang(y))
        P.ell(x, y, r, r * 0.6, R2)
        P.point(x - r * 0.4, y - r * 0.3, R4)
    # ---- Les deux haies de noisetiers, qui se rejoignent au loin : feuilles dorées et sarcelle, la face au soleil à
    # droite, l'ombre de celle de gauche sur le chemin.
    def haie(cote, graine):
        bo = []
        for i in range(190):
            t = hz(i, 1, graine) ** 0.8                                # 0 : au loin, 1 : tout près
            yb = FY_ + 0.6 + 41.0 * t
            r = 0.7 + 7.0 * t * (0.6 + 0.6 * hz(i, 3, graine))
            xb = FX_ + cote * (float(rang(yb)) * 44.0 + 1.2 + r * 0.7 + 56.0 * t * hz(i, 2, graine))
            haut_ = 1.6 + 46.0 * t
            bo.append((xb, yb - haut_ * hz(i, 4, graine) ** 0.8, r))
        return bo

    ombre = (Y > FY_) & (u < -0.55 + 0.25 * np.sin(Y / 3.0)) & route
    voile(P, ombre, TE1, 0.55)
    for cote, g, lum_ in ((-1, 1232, (-0.2, -0.6, 0.6)), (1, 1233, (-0.7, -0.4, 0.4))):
        mh = P.volumes(haie(cote, g), [T.N1, T.S0, T.S1, PJ1, T.S2, PJ2, PJ3] if cote > 0 else [T.N1, T.S0, T.S1, OC2, PJ1, PJ2], lum_, grain=1.4, graine=g + 10, gain=0.55,
                       base=0.42 if cote < 0 else 0.5, trame=0.5)
        ys, xs = np.nonzero(mh)
        for j in range(min(len(xs), 2600)):                              # les feuilles, une à une
            q = int(hz(j, 1, g + 40) * len(xs))
            X0, Y0 = int(xs[q]), int(ys[q])
            v0 = P.a[Y0, X0]
            haut_ = Y0 > 0 and not mh[max(0, Y0 - 3), X0]
            coul = (PJ3 if hz(j, 2, g + 40) < 0.6 else PJ4) if haut_ else (
                v0 if hz(j, 3, g + 40) < 0.7 else ((T.N1, T.S0, T.S1, PJ1) if cote < 0 else (PJ1, PJ2, PJ3, T.S2))[int(hz(j, 4, g + 40) * 4)])
            for (ax, ay) in pg.tampon_feuille(P, j)[:6]:
                P.bloc(X0 + ax, Y0 + ay, coul)
        P.remplir(mh & (pg.fbm(X / 0.8, Y / 0.8, 2, g + 20) > 0.7), PJ3 if cote > 0 else T.S2)
        P.remplir(mh & (pg.fbm(X / 0.6, Y / 0.6, 2, g + 30) > 0.78), T.N1)
        for i in range(30):                                           # des noisettes, des peluches de Brouillon
            x, y = haie(cote, g)[i][0], haie(cote, g)[i][1]
            if i % 5 == 0:
                P.ell(x + 1.0, y + 1.6, 0.6 + 0.6 * hz(i, 9, g), 0.4 + 0.4 * hz(i, 9, g), NE4)
            elif i % 3 == 0:
                P.point(x - 0.6, y + 1.0, BO3, 2 if haie(cote, g)[i][2] > 3 else 1)
    # La toile d'araignée dans la haie de droite, perlée de rosée qui brille.
    cx, cy = 156.0, 46.0
    for a in range(8):
        ang = a * math.pi / 4
        P.trait(cx, cy, cx + 3.6 * math.cos(ang), cy + 3.6 * math.sin(ang), T.CIEL[8])
    for r in (1.4, 2.6):
        P.courbe([(cx + r * math.cos(a * math.pi / 4), cy + r * math.sin(a * math.pi / 4)) for a in range(9)], T.CIEL[8], 1)
    for q in range(6):
        if (p * 6 + q) % 6 < 2:
            P.point(cx + 2.6 * math.cos(q * 1.05), cy + 2.6 * math.sin(q * 1.05), BLANC)
    # Des moineaux sur la haie de gauche, qui sautillent ; un papillon jaune.
    for i in range(3):
        x, y = 30.0 + 9 * i, 30.0 + 3.0 * i - (0.8 if int(p * 8 + i) % 4 == 0 else 0)
        P.ell(x, y, 1.3, 0.9, TE2)
        P.ell(x + 1.0, y - 0.7, 0.6, 0.6, TE1)
        P.point(x + 1.5, y - 0.6, PJ3)
        P.trait(x - 1.2, y, x - 2.4, y + 0.6, TE1)
    pg.papillon_de_nuit(P, 120.0 + 6 * onde(p), 44.0 + 2 * onde(p, 0.3), 3.0, coul=PJ3, d=0.2)
    tab.plan("premier", 1.0)
    # ---- Premier plan : le talus des bords, des pissenlits (jaunes et en graines, qui s'envolent), la pierre où l'on
    # s'assoit, à droite ; des herbes hautes qui se balancent.
    for (xa, cote) in ((-6.0, 1), (198.0, -1)):
        tal = ((X - xa) * cote < 18.0 - 10.0 * np.clip((Y - 62.0) / 18.0, 0, 1) + 3 * np.sin(Y / 3.0)) & (Y > 56.0 + 6.0 * ((X - xa) * cote) / 18.0)
        P.rampe(tal, 0.5 + 0.3 * (pg.fbm(X / 1.4, Y / 1.0, 2, 1234) - 0.5) - 0.2 * (cote < 0), [T.S0, T.S1, T.S2, PJ1, PJ2], 0.45)
    pg.touffes(P, lambda x: 79.5 + 0.0 * _a(x), n=90, haut=3.0, graine=1235)
    for i, (x, y) in enumerate(((8.0, 66.0), (14.0, 71.0), (184.0, 64.0), (190.0, 72.0), (176.0, 76.0))):
        P.trait(x, y + 4, x + 0.3 * onde(p, 0.2 * i), y, T.S2)
        if i % 2:
            P.ell(x + 0.3 * onde(p, 0.2 * i), y, 1.2, 1.0, PJ3)
            P.point(x + 0.3 * onde(p, 0.2 * i) - 0.3, y - 0.3, PJ4)
        else:
            P.ell(x + 0.3 * onde(p, 0.2 * i), y, 1.6, 1.6, NE3)
            P.ell(x + 0.3 * onde(p, 0.2 * i), y, 0.6, 0.6, NE4)
    for i in range(6):                                                # les graines qui partent au vent
        t = (p + i / 6.0) % 1.0
        x, y = 10.0 + 60.0 * t + 4 * i, 64.0 - 30.0 * t + 3 * math.sin(t * 8 + i)
        P.point(x, y, NE4)
        P.point(x, y + 0.6, NE2)
    sx, sy = 170.0, 76.0                                              # la pierre où s'asseoir
    voile(P, (((X - sx - 4.0) / 9.0) ** 2 + ((Y - sy - 0.5) / 1.4) ** 2 < 1), T.S0, 0.6)
    mm = P.ell(sx, sy - 2.0, 6.0, 3.4, R2, cond=Y < sy + 0.4)
    P.rampe(mm, 0.7 - 0.5 * (X - sx) / 6.0 - 0.3 * (Y - sy + 3) / 3.4 + 0.15 * (pg.fbm(X / 0.9, Y / 0.9, 2, 1236) - 0.5), [R1, R2, R3, R4], 0.45)
    P.remplir(mm & (pg.fbm(X / 1.2, Y / 1.2, 2, 1237) > 0.66), ME2)
    P.remplir(P.crete(mm) & (X < sx), CREME)


# =====================================================================================================================
# Le Pré aux Draps (chapitre 2) : « On est arrivés dans un pré plein de cordes à linge. Onze grands draps blancs qui
# claquent au vent. » L'après-midi, le soleil à droite : trois cordes qui fuient en biais dans un pré en pente douce,
# onze draps gonflés par le vent (le troisième, celui de Brouillon, plus près), leurs plis éclairés d'un côté, bleus de
# l'autre, le soleil qui les traverse ; leurs ombres couchées sur l'herbe. La maison de la hérissonne, son panier, ses
# pinces ; au loin, les montagnes plus grandes qu'au chemin creux, encore bleues.
# =====================================================================================================================
def drap(P, x0, x1, y_haut, h, graine, gonfle=1.0, ombre=True):
    """Un drap pendu entre deux pinces : le bas qui ondule au vent, des plis verticaux éclairés à droite, le soleil qui
    passe au travers près du haut, son ombre sur l'herbe vers la gauche. Renvoie son masque."""
    T = pg.T
    X, Y = P.X, P.Y
    w = x1 - x0
    u = (X - x0) / w
    bas = y_haut + h + gonfle * (0.6 * np.sin(u * 7.0 + P.p * 6.283 + graine) + 0.4 * np.sin(u * 13.0 - P.p * 12.566))
    gauche = x0 + 0.6 * gonfle * onde(P.p, 0.1 * graine) * (Y - y_haut) / h
    droite = x1 + 0.9 * gonfle * onde(P.p, 0.1 * graine + 0.2) * (Y - y_haut) / h
    m = (Y >= y_haut) & (Y <= bas) & (X >= gauche) & (X <= droite)
    if ombre:
        om = (Y > y_haut + h + 3.0) & (Y < y_haut + h + 3.0 + h * 0.18) & (X > x0 - h * 0.7 - 0.2 * (Y - y_haut - h)) & (
            X < x1 - h * 0.7 - 0.2 * (Y - y_haut - h)) & (P.a >= 0) & ~m
        voile(P, om, T.S0, 0.45)
    pli = np.sin(u * (5.0 + 2 * hz(graine, 1, 1240)) * math.pi + gonfle * onde(P.p, 0.13 * graine) * 1.5)
    v = 0.66 + 0.24 * pli + 0.1 * (1 - (Y - y_haut) / h) - 0.12 * np.clip((Y - y_haut) / h - 0.7, 0, 1) * 3
    P.rampe(m, v, [SH1, NE1, NE2, NE3, NE4, CREME], 0.45)
    P.remplir(m & (pli > 0.85) & (P.T < 0.5), BLANC)
    P.remplir(m & (np.abs(Y - bas) < 0.35), NE1)                      # l'ourlet
    return m


@decor("petit-nuage", "pre-aux-draps", soleil=(170.0, 4.0), tons=LAVE, nom="Le Pré aux Draps", matiere=True)
def pre_aux_draps(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=40.0, haut=0.05, halo=0.3, disque=4.6)
    pg.voiles(P, y=4.0, epais=6.0, seuil=0.62, graine=1241)
    pg.cumulus(P, [(60, 2, 44, 7.0, 1242, 9, 0.1), (130, -8, 28, 4.6, 1243, 6, 0.5), (18, 20, 22, 3.6, 1244, 5, 0.8), (158, 14, 40, 6.0, 1255, 8, 0.3)],
               dessous=-0.4)
    pg.oiseaux(P, 96, 10, 4, coul=T.CIEL[2])
    tab.plan("lointains", 0.2)
    # ---- Les montagnes, plus grandes qu'au chemin creux, bleues ; les collines, le bocage, un clocher.
    massif(P, lambda x: dents(x, cx=86.0, k=0.62, base=38.0), [(69.0, 17.0), (101.0, 14.4)],
           [T.L1, T.L2, T.L3, T.L4], [T.L5, NE2, NE3, NE4], [T.L3, T.L4, NE2], NE4, 1245, brume=(T.CIEL[10], 24.0, 12.0))
    pg.crete(P, lambda x: pg.profil(x, 38.0, 4.0, 18.0, 1246), [T.L1, T.L2, T.L3, T.CIEL[9]], 0.6)
    coll = lambda x: 40.5 + 1.8 * np.sin(_a(x) / 17.0 + 1.0) + 0.6 * np.sin(_a(x) / 5.0)
    m = Y > coll(X)
    P.rampe(m, 0.55 + 0.4 * (pg.fbm(X / 4.0, Y / 1.0, 2, 1247) - 0.5), [T.S1, T.S2, PJ1, PJ2, T.S3], 0.5)
    for i in range(14):
        x, y = -4 + 200 * hz(i, 1, 1248), float(coll(-4 + 200 * hz(i, 1, 1248))) + 0.6 + 2.0 * hz(i, 2, 1248)
        r = 0.8 + 1.4 * hz(i, 3, 1248)
        mm = P.ell(x, y - r * 0.5, r, r * 0.8, T.S1)
        P.remplir(mm & (X > x + r * 0.2), T.S3)
    P.rect(150.0, 36.0, 1.2, 4.6, T.L2)                               # un clocher, au loin
    P.poly([(149.6, 36.2), (151.6, 36.2), (150.6, 33.0)], T.L1)
    voile(P, m, T.CIEL[10], 0.3)
    tab.plan("moyen", 0.5)
    # ---- Le pré en pente douce : herbe d'automne, plus fine au loin ; le soleil à droite, l'ombre des draps à gauche.
    f_pre = lambda x: 44.0 - 0.02 * (_a(x) - 96) + 0.8 * np.sin(_a(x) / 11.0)
    pre = Y > f_pre(X)
    k = np.clip((Y - 44.0) / 36.0, 0, 1)
    v = 0.55 + 0.6 * (pg.fbm((X + Y * 0.6) / (2.0 + 5 * k), Y / (0.6 + 2 * k), 3, 1249) - 0.5) + 0.3 * (pg.fbm(X / 14.0, Y / 4.0, 2, 1256) - 0.5) + 0.12 * (X - 96) / 96.0
    P.rampe(pre, v, [T.S0, T.S1, T.S2, T.S3, T.S4], 0.45)
    for i in range(950):                                              # les brins couchés par le vent, dorés au soleil
        y = 44.5 + 35.5 * hz(i, 2, 1254) ** 0.75
        x = -6 + 204 * hz(i, 1, 1254)
        l = 0.4 + 2.2 * (y - 44.0) / 36.0
        b = 0.3 * onde(p, x / 40.0) * l
        P.trait(x, y, x + l * 0.5 + b, y - l, (PJ2, T.S3, PJ1, T.S2, PJ3)[i % 5] if x > 60 else (T.S1, T.S2, T.S0, PJ1, T.S3)[i % 5])
    P.remplir(P.crete(pre), PJ3)
    # La maison de la hérissonne, à droite, au bout du pré : un toit de tuiles, une fenêtre, sa fumée.
    hx, hy = 176.0, 46.4
    chx, chy = pg.maison(P, hx, hy, p, grande=False)
    pg.fumee(P, chx, chy, p)
    # ---- Trois cordes qui fuient en biais, onze draps. Les poteaux, les pinces de bois.
    cordes = [(100.0, 172.0, 41.6, 39.6, 4, 3.0), (34.0, 146.0, 39.0, 33.0, 4, 5.0), (-8.0, 64.0, 27.0, 31.0, 3, 8.6)]
    n = 0
    for c, (xa, xb, ya, yb, nd, h) in enumerate(cordes):
        for x in (xa, xb):
            y = ya if x == xa else yb
            P.rect(x - 0.15 * h / 4, y - 0.8, 0.3 * h / 4 + 0.4, h * 2.2 + 3.0, BO2)
            P.rect(x - 0.15 * h / 4, y - 0.8, 0.12 * h / 4 + 0.2, h * 2.2 + 3.0, BO3)
        P.courbe([(xa, ya), ((xa + xb) / 2, (ya + yb) / 2 + 0.06 * h), (xb, yb)], TE2, 1)
        largeur = (xb - xa) / nd
        for i in range(nd):
            n += 1
            x0 = xa + largeur * (i + 0.16)
            x1 = xa + largeur * (i + 0.84)
            y0 = ya + (yb - ya) * (i + 0.5) / nd + 0.05 * h
            md = drap(P, x0, x1, y0, h * 1.5, graine=n, gonfle=0.22 * h)
            for xp in (x0 + 0.4, x1 - 0.6):                              # les pinces
                P.rect(xp, y0 - 0.5 - 0.02 * h, 0.3 + 0.03 * h, 0.6 + 0.08 * h, TE3)
    # Le panier de linge de la hérissonne, au pied de la corde du milieu, des pinces tombées dans l'herbe.
    bx, by = 112.0, 66.0
    voile(P, (((X - bx + 4.0) / 8.0) ** 2 + ((Y - by - 0.3) / 1.2) ** 2 < 1), T.S0, 0.5)
    pan = (((X - bx) / 5.0) ** 2 + ((Y - by + 2.0) / 2.6) ** 2 < 1) & (Y > by - 3.0)
    P.rampe(pan, 0.6 + 0.3 * (X - bx) / 5.0 + 0.3 * (np.sin(X * 3.0) * np.sin(Y * 3.0)), [BO2, BO3, TE2, TE3], 0.45)
    P.ell(bx - 1.0, by - 3.4, 3.4, 1.4, NE4)
    P.ell(bx + 1.6, by - 3.8, 1.8, 1.0, T.BLEU)
    P.courbe([(bx - 4.0, by - 3.0), (bx, by - 6.6), (bx + 4.0, by - 3.0)], BO2, 1)
    for i in range(5):
        P.rect(104.0 + i * 3.2, 70.0 + (i % 2) * 1.4, 0.5, 1.4, TE3)
    # Des pies sur la corde du fond, un merle dans l'herbe, des papillons blancs qui se prennent pour des draps.
    for i in range(2):
        x = 60.0 + i * 30.0
        y = 42.0 - 4.0 * i * 30 / 114
        P.ell(x, y - 0.8, 0.9, 0.6, ENCRE)
        P.ell(x + 0.5, y - 1.3, 0.4, 0.4, ENCRE)
        P.point(x - 0.2, y - 0.8, NE4)
        P.trait(x - 0.8, y - 0.6, x - 2.2, y - 0.2 + 0.4 * onde(p, i * 0.5), ENCRE)
    for i in range(3):
        pg.papillon_de_nuit(P, 40.0 + 40 * i + 6 * onde(p, 0.3 * i), 52.0 + 3 * onde(p, 0.2 + 0.3 * i), 2.6, coul=NE4, d=0.3 * i)
    tab.plan("premier", 1.0)
    # ---- Premier plan : le grand frêne de gauche qui cadre, son feuillage doré au soleil ; des herbes hautes, des
    # marguerites tardives ; le vent qui couche tout vers la droite.
    tronc = (X < 4.0 + 1.0 * np.sin(Y / 7.0)) & (X > -8)
    P.rampe(tronc, 0.3 + 0.4 * np.clip((X + 8) / 12.0, 0, 1) + 0.2 * (pg.fbm(X / 0.8, Y / 3.0, 3, 1250) - 0.5), [ENCRE, BO1, BO2, BO3], 0.45)
    P.remplir(tronc & ~np.roll(tronc, -1, axis=1), OC3)
    pg.feuillage(P, lambda x: 10.0 - 0.36 * _a(x) + 2.4 * np.sin(_a(x) / 5.0) + 1.0 * np.sin(_a(x) / 2.2), x0=-6, x1=50,
                 n=600, epais=8.0, graine=1251, y_max=8.0, tons=([T.N1, T.S0, T.S1, OC2], [T.S1, T.S2, PJ1], [T.S2, PJ1, PJ2, PJ3, PJ4]))
    pg.touffes(P, lambda x: 78.6 + 0.0 * _a(x), n=120, haut=3.6, graine=1252)
    for i, x in enumerate((18.0, 26.0, 47.0, 98.0, 124.0, 176.0, 186.0)):
        y = 76.0 + 2.0 * hz(i, 1, 1253)
        b = 0.4 * onde(p, 0.15 * i)
        P.trait(x, y + 3.0, x + b, y, T.S2)
        P.ell(x + b, y, 1.3, 0.8, NE4)
        P.point(x + b, y, PJ3)


# =====================================================================================================================
# L'Étang-qui-fume (chapitres 2 et 3) : « C'est un étang tout rond, avec des roseaux et un vieux saule. […] l'eau fume.
# Une brume blanche monte de partout. » L'aube rose : le soleil se lève derrière les montagnes à gauche ; l'étang rond
# fait miroir, la brume s'en lève en volutes ; le vieux saule pleure sur la rive droite, et dans ses branches la grande
# toile de Dentelle, ses gouttes rangées par taille, la perle au centre ; les rainettes du chœur sur les nénuphars.
# =====================================================================================================================
def saule(P, x, y, h, graine):
    """Un vieux saule pleureur : un tronc tordu, des branches en arc, et le rideau de rameaux qui tombe jusqu'à l'eau,
    éclairé du côté du soleil ; les rameaux bougent un peu."""
    T = pg.T
    P.courbe([(x, y), (x + 1.5, y - h * 0.3), (x - 1.0, y - h * 0.55), (x + 0.5, y - h * 0.7)], BO1, P.ep(2.0), P.ep(1.0))
    P.courbe([(x + 0.4, y), (x + 1.8, y - h * 0.3), (x - 0.6, y - h * 0.55)], BO2, 1)
    tetes = []
    for i in range(7):
        a = -2.6 + 0.85 * i / 6 * 2.6
        bx, by = x + 0.5 + h * 0.36 * math.cos(a) * 1.2, y - h * 0.7 + h * 0.2 * math.sin(a) - h * 0.12
        P.courbe([(x + 0.5, y - h * 0.68), ((x + bx) / 2, by - h * 0.12), (bx, by)], BO1, P.ep(0.5), 1)
        tetes.append((bx, by))
    bo = [(bx + 3.0 * (hz(j, 1, graine + 5) - 0.5), by + 2.0 * (hz(j, 2, graine + 5) - 0.5), 2.0 + 2.6 * hz(j, 3, graine + 5))
          for j, (bx, by) in enumerate(tetes * 3)]
    P.volumes(bo, [T.S0, T.S1, T.S2, PJ1, T.S3, PJ2], (-0.6, -0.55, 0.4), grain=0.9, graine=graine + 6, gain=0.6, base=0.45, trame=0.5)
    for i in range(240):                                              # les rameaux
        k = i % len(tetes)
        bx, by = tetes[k]
        x0 = bx + (hz(i, 1, graine) - 0.5) * h * 0.4
        y0 = by + (hz(i, 2, graine) - 0.2) * h * 0.12
        l = h * (0.15 + 0.7 * hz(i, 3, graine) ** 1.5)
        b = 0.5 * onde(P.p, x0 / 9.0 + 0.1 * k)
        lumi = x0 < x
        coul = (T.S3 if hz(i, 4, graine) < 0.5 else PJ2) if lumi else (T.S1 if hz(i, 4, graine) < 0.6 else T.S0)
        P.courbe([(x0, y0), (x0 + b * 0.4 + 0.6 * (hz(i, 6, graine) - 0.5), y0 + l * 0.5), (x0 + b + 1.2 * (hz(i, 7, graine) - 0.5), y0 + l)], coul, 1)
        if hz(i, 5, graine) < 0.35:
            P.point(x0 + b * 0.6, y0 + l * 0.6, T.S4 if lumi else T.S2)


@decor("petit-nuage", "etang-qui-fume", soleil=(52.0, 30.0), tons=ROSE, nom="L'Étang-qui-fume", matiere=True)
def etang_qui_fume(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    # ---- Le ciel de l'aube : rose au ras des montagnes, bleu pâle en haut ; des barres de nuages éclairées par-dessous.
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=42.0, haut=0.0, halo=0.4, disque=3.6)
    tab.plan("nuages", 0.08)
    pg.voiles(P, y=-2.0, epais=8.0, seuil=0.58, graine=820)
    pg.barres(P, [(70, 30.0, 22, 1.3), (128, 24.0, 18, 1.0), (24, 20.0, 14, 0.9)])
    pg.cumulus(P, [(160, 6, 30, 5.0, 1260, 7, 0.3)], dessous=0.6)
    tab.plan("lointains", 0.2)
    # ---- Les montagnes, plus grandes qu'au Pré aux Draps, le versant gauche rosi par l'aube ; une forêt noire en dessous.
    massif(P, lambda x: dents(x, cx=92.0, k=0.78, base=42.0), [(72.0, 17.0), (112.0, 13.5)],
           [T.L0, T.L1, T.L2, T.L3], [T.L4, T.CIEL[7], NE3, NE4], [T.L2, T.L3, T.CIEL[5]], T.CIEL[9], 1261,
           brume=(T.CIEL[8], 28.0, 12.0))
    foret = lambda x: pg.profil(x, 44.0, 4.0, 14.0, 821)
    pg.crete(P, foret, [T.L0, T.L1, T.L2, T.CIEL[6]], 0.5)
    pg.sapins(P, foret, densite=0.8, graine=822, coul=T.L0)
    brume_claire(P, 42.0, 2.6, 60, T.CIEL[9], 0.6)
    tab.plan("moyen", 0.5)
    # ---- La rive d'en face, ronde, ses joncs ; un héron immobile dans les hauts-fonds ; le vieux saule à droite.
    f_rive = lambda x: 46.8 + 0.6 * np.sin(_a(x) / 8.0) - 1.6 * np.exp(-((_a(x) - 160) / 20.0) ** 2)
    pg.rive(P, f_rive, epais=2.2, joncs=170, graine=823, sauf=(132, 192))
    hx, hy = 58.0, 47.6                                               # le héron
    P.trait(hx, hy, hx, hy - 3.4, T.L0)
    P.trait(hx + 0.6, hy, hx + 0.6, hy - 3.4, T.L0)
    P.ell(hx + 0.3, hy - 4.6, 1.4, 1.6, T.L1)
    P.courbe([(hx + 0.8, hy - 5.8), (hx + 1.4, hy - 7.6), (hx + 0.6, hy - 9.0)], T.L1, 1)
    P.trait(hx + 0.6, hy - 9.0, hx + 2.6, hy - 8.6, T.CIEL[8])
    sxl, syl = 160.0, 47.0                                            # le saule
    saule(P, sxl, syl, 40.0, 1262)
    # La grande toile de Dentelle, dans le saule (la clé de la scène) : les fils, les gouttes rangées par taille, la
    # perle au centre ; elles s'allument l'une après l'autre ; l'araignée qui tisse.
    cx, cy, R = 146.0, 22.0, 13.0
    for a in range(12):
        ang = a * math.pi / 6
        P.trait(cx, cy, cx + R * math.cos(ang), cy + R * 0.9 * math.sin(ang), NE2)
    for k_ in range(5):
        r = R * (k_ + 1) / 5.4
        P.courbe([(cx + r * math.cos(a * math.pi / 6), cy + r * 0.9 * math.sin(a * math.pi / 6)) for a in range(13)], NE2, 1)
        for a in range(0, 12, 2):
            ang = (a + 0.5) * math.pi / 6
            gx, gy = cx + r * math.cos(ang), cy + r * 0.9 * math.sin(ang)
            vive = ((p * 12 + a + k_ * 3) % 12) < 3
            P.point(gx, gy, BLANC if vive else NE3, 1 + (k_ < 2))
    P.trait(cx - R, cy - R * 0.9, cx, cy, NE3)
    P.trait(cx + R, cy - R * 0.9, cx, cy, NE3)
    P.trait(cx, cy - R * 1.2, cx, cy, NE3)
    halo(P, cx, cy, 3.4, CREME, 0.5 + 0.15 * onde(p))
    P.ell(cx, cy, 1.3, 1.3, NE4)                                       # la perle de rosée qui ne sèche pas
    P.point(cx - 0.4, cy - 0.4, BLANC)
    pg.araignee(P, cx + 6.0, cy - 6.0, 4.0, d=0.2)
    # ---- L'étang : le miroir de tout ce qui précède ; des nénuphars, les rainettes du chœur ; la brume qui monte.
    pg.miroir(P, tab.derriere(), 46.6, ronds=((70.0, 60.0, 0.0), (112.0, 54.0, 0.4), (96.0, 68.0, 0.7)))
    petits = [(30, 55.0, 2.0, T.VIOLET), (40, 60.0, 1.6, None), (66, 52.0, 1.4, None), (84, 58.5, 2.2, CREME),
              (104, 62.0, 1.8, None), (124, 56.0, 2.4, T.VIOLET), (140, 64.0, 2.0, None), (52, 66.0, 2.6, None),
              (118, 70.0, 2.2, CREME), (152, 58.0, 1.6, None)]
    for i, (x, y, r, fl) in enumerate(petits):
        pg.nenuphar(P, x, y + 0.12 * onde(p, 0.13 * i), r, 1263 + i, fl)
    for i, (x, y) in enumerate(((40.0, 59.2), (84.0, 57.6), (124.0, 55.0), (52.0, 65.0), (104.0, 61.2))):
        chante = int(p * 8 + i * 3) % 8 < 2                            # une rainette ; la gorge qui se gonfle
        P.ell(x, y - 0.6, 1.0, 0.7, T.S3)
        P.point(x - 0.5, y - 1.2, ENCRE)
        P.point(x + 0.5, y - 1.2, ENCRE)
        if chante:
            P.ell(x, y - 0.1, 0.7, 0.5, CREME)
    pg.barque(P, 18.0, 52.0, p)
    for g in range(6):                                                # la brume qui fume : des volutes qui montent
        y = 50.0 + g * 3.4
        dens = pg.fbm((X + 5.0 * g + 4.0 * onde(p, 0.1 * g)) / 10.0, (Y + 6.0 * p) / 2.0, 3, 1270 + g)
        voile(P, (np.abs(Y - y - 1.2 * np.sin(X / 9.0 + g)) < 0.6 + 2.6 * dens) & (Y > 46.0) & (dens > 0.45), NE4, 0.32 + 0.04 * g)
    for i in range(9):
        t = (p + i / 9.0) % 1.0
        x = 20 + 18 * i + 2 * math.sin(t * 6 + i)
        voile(P, (np.hypot((X - x - 1.5 * t) / (1.0 + 2.0 * t), Y - 62.0 + 14.0 * t) < 1.6 + 2.0 * t), NE4, 0.5 * (1 - t))
    tab.plan("premier", 1.0)
    # ---- Premier plan : la rive où l'on dort, herbe mouillée de rosée ; des massettes et des roseaux à gauche et à
    # droite ; une libellule ; des gouttes de rosée qui s'allument.
    f_berge = lambda x: (74.6 + 0.9 * np.sin(_a(x) / 17.0) + 0.4 * np.sin(_a(x) / 6.0)
                         - 5.0 * np.exp(-((_a(x) - 2) / 18.0) ** 2) - 5.0 * np.exp(-((_a(x) - 192) / 16.0) ** 2))
    pg.sol(P, f_berge)
    pg.cailloux(P, f_berge)
    pg.touffes(P, f_berge)
    pg.fleurs(P, f_berge)
    pg.roseaux(P, 0.0, 14.0, n=6, haut=(12.0, 24.0), penche=1.0, graine=1271)
    pg.roseaux(P, 176.0, 196.0, sauf=(186.0, 1.2), graine=1272)
    pg.libellule(P, 96.0 + 4 * onde(p), 66.0)
    for i in range(30):
        x, y = -4 + 200 * hz(i, 1, 1273), 75.5 + 4 * hz(i, 2, 1273)
        if (p + hz(i, 3, 1273)) % 1.0 < 0.25:
            P.point(x, y, BLANC)


# =====================================================================================================================
# Le Plateau Râpé (chapitre 4) : « Devant nous, c'est plat, jaune, et ça ne s'arrête pas. […] Un seul arbre, mort, très
# loin, au milieu. […] Et à droite, loin, au ras du plateau, il y a autre chose. Des nuages. Énormes, noirs, plats du
# dessus comme des enclumes. » Midi : le soleil haut, l'air qui tremble au ras du sol ; le plateau jaune en perspective,
# l'arbre mort au milieu (la clé), les Dents-de-Lait alignées au bout, blanches ; les Enclumes qui montent à droite,
# leur pluie en rideaux, un éclair ; la pancarte, le seul caillou qui fasse de l'ombre, un tourbillon de poussière.
# =====================================================================================================================
def enclume(P, x, y_base, l, h, graine, eclair=False):
    """Un cumulonimbus : une tour de bouffées sombres, le dessus étalé en enclume plate, éclairé ; la pluie dessous en
    rideaux tramés ; un éclair qui part parfois."""
    T = pg.T
    X, Y = P.X, P.Y
    tour = []
    for i in range(40):
        u = hz(i, 1, graine) ** 0.8
        yy = y_base - h * 0.72 * u
        tour.append((x + l * 0.42 * (hz(i, 2, graine) - 0.5) * (1.3 - 0.5 * u), yy, l * (0.16 + 0.12 * hz(i, 3, graine)) * (1.15 - 0.45 * u), 4.0 * (1 - u)))
    m_ = bouffees(P, tour, [ENCRE, NU1, NU2, R1, R2, R3, NE2], lum=(0.35, -0.6, 0.3), plancher=y_base + 1.0, graine=graine)
    voile(P, m_ & (Y > y_base - h * 0.35), NU1, 0.5)                   # le ventre noir
    yt = y_base - h * 0.78
    dx_ = (X - x - l * 0.2) / (l * 0.95)
    dessus = (np.abs(Y - yt + 1.0 * (1 - dx_ ** 2)) < (1.0 + 3.4 * (1 - np.abs(dx_))) * (1 + 0.3 * (pg.fbm(X / 2.0, Y, 2, graine) - 0.5))) & (np.abs(dx_) < 1)
    P.rampe(dessus, 0.6 - 0.18 * (Y - yt) + 0.2 * (pg.fbm(X / 2.0, Y, 2, graine + 1) - 0.5), [NU2, R1, R2, R3, R4, NE2, CREME], 0.5)
    P.remplir(P.crete(dessus), CREME)
    for j in range(4):                                                # les rideaux de pluie
        xr = x - l * 0.25 + j * l * 0.16
        voile(P, (np.abs(X - xr - 0.15 * (Y - y_base)) < l * 0.05) & (Y > y_base) & (Y < y_base + 6.0) & (P.T < 0.5), R2, 0.6)
    if eclair and (P.p * 8) % 8 < 1:
        pts = [(x + 2.0, y_base)]
        for k in range(5):
            pts.append((pts[-1][0] + 2.0 * (hz(k, 1, graine + 3) - 0.5) * 2, pts[-1][1] + 1.6))
        for a, b in zip(pts[:-1], pts[1:]):
            P.trait(a[0], a[1], b[0], b[1], LA3)
        voile(P, np.hypot(X - x, Y - y_base + h * 0.3) < h * 0.5, CREME, 0.3, lumiere=True)


@decor("petit-nuage", "plateau-rape", soleil=(70.0, -30.0), tons=LAVE, nom="Le Plateau Râpé", matiere=True)
def plateau_rape(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=44.0, haut=0.0, halo=0.3, disque=0)
    pg.voiles(P, y=-6.0, epais=8.0, seuil=0.6, graine=1280)
    pg.cumulus(P, [(40, 4, 26, 4.0, 1281, 6, 0.2), (96, -6, 18, 3.0, 1282, 5, 0.6)], dessous=-0.6)
    tab.plan("lointains", 0.2)
    # ---- Les Dents-de-Lait, alignées au bout du plateau, blanches ; les Enclumes qui montent à droite, au ras du plateau.
    massif(P, lambda x: dents(x, cx=72.0, k=0.62, base=44.0, serre=1.0) + 0.0, [(56.5, 24.0), (87.5, 21.6)],
           [T.L1, T.L2, T.L3, T.L4], [T.L5, NE2, NE3, NE4], [T.L3, T.L4, NE2], NE4, 1283, brume=(T.CIEL[9], 34.0, 10.0))
    enclume(P, 150.0, 43.0, 50.0, 52.0, 1284, eclair=True)
    enclume(P, 186.0, 43.0, 30.0, 34.0, 1285)
    enclume(P, 118.0, 43.5, 20.0, 18.0, 1286)
    pg.crete(P, lambda x: 44.0 + 0.3 * np.sin(_a(x) / 7.0), [T.L2, T.L3, T.L4, T.CIEL[9]], 0.5)
    tab.plan("moyen", 0.5)
    # ---- Le plateau : jaune, ras, il ne s'arrête pas ; des touffes en rangs qui fuient, la terre craquelée, des cailloux.
    sol = Y > 44.4
    prof_ = 24.0 / np.maximum(Y - 44.0, 0.4)
    u = (X - 96.0) / np.maximum(Y - 44.0, 0.4)
    v = 0.6 + 0.3 * (pg.fbm(u * 1.5, prof_ * 1.6, 3, 1287) - 0.5) + 0.25 * (pg.fbm(u * 0.4, prof_ * 0.3, 2, 1288) - 0.5)
    P.rampe(sol, v, [TE1, OC2, PJ1, PJ2, PJ3, PJ4], 0.45)
    craque = sol & (Y > 56) & (np.abs(np.sin(u * 9.0 + 2.0 * pg.fbm(u, prof_ * 2, 2, 1289))) < 0.06) & (pg.fbm(u * 0.5, prof_, 2, 1290) > 0.55)
    P.remplir(craque, OC1)
    for i in range(500):                                              # touffes d'herbe rase
        y = 44.6 + 35.4 * hz(i, 2, 1291) ** 1.6
        x = -6 + 204 * hz(i, 1, 1291)
        k = (y - 44.0) / 36.0
        h = 0.3 + 2.2 * k
        for j in (-1, 0, 1):
            P.trait(x + j * 0.4 * h, y, x + j * 0.8 * h + 0.3 * onde(p, x / 30.0) * k, y - h, PJ3 if j else PJ1)
    for i in range(60):                                               # des cailloux, leur ombre courte sous eux
        y = 45.0 + 35.0 * hz(i, 2, 1292) ** 1.3
        x = -6 + 204 * hz(i, 1, 1292)
        r = 0.2 + 1.0 * (y - 44.0) / 36.0 * (0.5 + hz(i, 3, 1292))
        P.ell(x + r * 0.3, y + r * 0.3, r * 1.2, r * 0.3, OC1)
        P.ell(x, y, r, r * 0.6, R2 if i % 3 else R3)
        P.point(x - r * 0.3, y - r * 0.3, R4)
    # Une clôture qui fuit vers l'horizon, à gauche, son fil affaissé.
    prec = None
    for i in range(9):
        t = i / 8.0
        x, y = 2.0 + 60.0 * t ** 0.7, 74.0 - 28.0 * t ** 0.7
        h = 6.0 * (1 - 0.85 * t ** 0.7)
        P.trait(x, y, x + 0.2, y - h, BO2, max(1, P.ep(0.6 * (1 - t))))
        if prec:
            P.courbe([(prec[0], prec[1] - prec[2] * 0.8), ((prec[0] + x) / 2, (prec[1] + y) / 2 - (prec[2] + h) * 0.3), (x, y - h * 0.8)], R3, 1)
        prec = (x, y, h)
    # L'air qui tremble au ras de l'horizon.
    tremble = (np.abs(Y - 44.8 - 0.4 * np.sin(X * 0.9 + p * 6.283)) < 0.5)
    voile(P, tremble, T.CIEL[10], 0.5)
    # ---- L'arbre mort, au milieu (la clé de la scène) : un tronc gris argent, fendu, ses branches nues ; un corbeau.
    ax, ay = 100.0, 57.6
    voile(P, (((X - ax - 1.0) / 6.0) ** 2 + ((Y - ay - 0.3) / 0.8) ** 2 < 1), OC1, 0.6)
    P.courbe([(ax, ay), (ax - 0.6, ay - 12.0), (ax + 0.8, ay - 20.0), (ax + 0.2, ay - 30.0)], R2, P.ep(1.6), P.ep(0.5))
    P.courbe([(ax - 0.4, ay), (ax - 1.0, ay - 12.0), (ax + 0.2, ay - 20.0)], R4, 1)
    for (a, l, y0) in ((-2.2, 10.0, 16.0), (-0.7, 8.0, 20.0), (-2.6, 7.0, 25.0), (-0.4, 6.0, 26.0), (-1.6, 5.0, 29.0)):
        bx, by = ax + l * math.cos(a), ay - y0 + l * math.sin(a)
        P.courbe([(ax, ay - y0 + 1.0), ((ax + bx) / 2, (ay - y0 + by) / 2 - 1.0), (bx, by)], R2, P.ep(0.5), 1)
        P.trait(bx, by, bx + 1.4 * math.cos(a - 0.6), by + 1.4 * math.sin(a - 0.6), R2)
    P.ell(ax + 3.6, ay - 28.6, 1.2, 0.8, ENCRE)
    P.ell(ax + 4.6, ay - 29.4, 0.6, 0.6, ENCRE)
    P.point(ax + 5.2, ay - 29.4, R3)
    for i in range(2):                                                # deux milans qui tournent haut
        t = (p + i / 2.0) % 1.0
        x, y = 60 + 30 * i + 8 * math.cos(t * 6.283), 4 + 3 * math.sin(t * 6.283)
        P.trait(x - 2.2, y - 0.4, x, y, NU2)
        P.trait(x, y, x + 2.2, y - 0.4, NU2)
    # Un tourbillon de poussière qui traverse, au loin à droite.
    tx = 128.0 + 6 * onde(p)
    for k in range(14):
        t = k / 13.0
        r = 0.6 + 2.4 * t
        a = p * 12.566 + k
        P.point(tx + r * math.cos(a) + 0.8 * t, 51.0 - 9.0 * t, TE3 if k % 2 else PJ4)
    voile(P, (np.abs(X - tx - 0.6 * (51.0 - Y) / 9.0) < 0.6 + 1.6 * np.clip((51.0 - Y) / 9.0, 0, 1)) & (Y < 51.0) & (Y > 42.0), PJ4, 0.35)
    tab.plan("premier", 1.0)
    # ---- Premier plan : la pancarte de bois (un soleil et un trait plat : « rien avant longtemps »), le seul caillou
    # qui fasse de l'ombre (un lézard dessus), des herbes sèches, des sauterelles.
    px_, py_ = 14.0, 56.0
    P.rect(px_ - 0.6, py_, 1.3, 22.0, BO1)
    P.rect(px_ - 0.6, py_, 0.5, 22.0, BO3)
    pm = P.poly([(px_ - 9.0, py_ - 6.0), (px_ + 9.0, py_ - 7.0), (px_ + 9.4, py_ + 3.0), (px_ - 8.6, py_ + 3.6)], BO2)
    P.rampe(pm, 0.6 + 0.3 * (pg.fbm(X / 0.5, Y / 3.0, 2, 1293) - 0.5), [BO1, BO2, BO3, TE2], 0.45)
    P.remplir(P.crete(pm), TE3)
    P.ell(px_ - 3.6, py_ - 3.0, 1.8, 1.8, PJ3)
    for a in range(8):
        P.trait(px_ - 3.6, py_ - 3.0, px_ - 3.6 + 2.8 * math.cos(a * 0.785), py_ - 3.0 + 2.8 * math.sin(a * 0.785), PJ3)
    P.trait(px_ + 0.4, py_ + 0.2, px_ + 7.0, py_ + 0.2, TE3, P.ep(0.4))
    cx_, cy_ = 176.0, 78.0
    voile(P, (((X - cx_ + 7.0) / 9.0) ** 2 + ((Y - cy_ - 0.2) / 1.6) ** 2 < 1), OC1, 0.7)
    mm = P.ell(cx_, cy_ - 3.0, 7.0, 4.6, R2, cond=Y < cy_ + 0.4)
    P.rampe(mm, 0.7 - 0.4 * (X - cx_) / 7.0 - 0.5 * (Y - cy_ + 4.0) / 4.6 + 0.15 * (pg.fbm(X / 0.9, Y / 0.9, 2, 1294) - 0.5), [R1, R2, R3, R4, NE3], 0.45)
    P.remplir(mm & (pg.fbm(X / 1.2, Y / 1.2, 2, 1295) > 0.67), ME2)
    lx = cx_ - 2.0 + (0.8 if onde(p) > 0.3 else 0.0)                   # le lézard
    P.ell(lx, cy_ - 7.4, 1.6, 0.5, OC3)
    P.trait(lx - 1.4, cy_ - 7.2, lx - 4.0, cy_ - 6.6, OC3)
    P.point(lx + 1.4, cy_ - 7.6, ENCRE)
    pg.touffes(P, lambda x: 79.4 + 0.0 * _a(x), n=80, haut=3.0, graine=1296, tons=(OC1, OC2, PJ1, PJ2, PJ3))
    for i in range(3):                                                # des sauterelles qui sautent
        t = (p + i / 3.0) % 1.0
        x, y = 40 + 50 * i + 8 * t, 77.0 - 6.0 * math.sin(t * math.pi)
        P.trait(x, y, x + 1.2, y - 0.3, PJ1)
        P.point(x + 1.2, y - 0.3, OC1)


# =====================================================================================================================
# La halte du Bout-des-Prés (chapitre 5) : « C'était une girouette. Un coq en fer, tout rouillé, sur le toit d'une
# petite halte en pierre, avec une lanterne pendue au bec. » La nuit, au pied des montagnes enfin proches, sous la lune :
# la halte de pierre, sa fenêtre chaude qui pose un rectangle d'or sur l'herbe, la fumée du poêle ; sur le toit, Tournebise
# (la clé), qui pointe vers la montagne et ne tourne pas, sa lanterne qui se balance ; les sapins, la clôture, un hibou.
# =====================================================================================================================
@decor("petit-nuage", "halte-girouette", soleil=(26.0, -6.0), tons=NUIT, nom="La halte du Bout-des-Prés", matiere=True)
def halte_girouette(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=46.0, haut=0.0, halo=0.18, etoiles=0.5, lune=(26.0, -6.0, 3.6), disque=0)
    t = p % 1.0                                                       # une étoile filante
    if t < 0.25:
        P.trait(30 + 60 * t, -12 + 12 * t, 30 + 60 * t - 4, -12 + 12 * t - 0.8, NE4)
    pg.voiles(P, y=10.0, epais=6.0, seuil=0.6, graine=1300)
    tab.plan("lointains", 0.2)
    # ---- Les montagnes, proches maintenant, sous la lune (à gauche) : neige bleue, versants d'ombre profonds.
    massif(P, lambda x: dents(x, cx=86.0, k=1.15, base=50.0), [(57.0, 13.2), (115.0, 7.4)],
           [ENCRE, NU1, NU2, T.CIEL[4]], [T.CIEL[6], T.CIEL[8], T.CIEL[9], T.CIEL[10]], [NU2, T.CIEL[4], T.CIEL[6]],
           T.CIEL[11], 1301, brume=(T.CIEL[3], 34.0, 12.0))
    foret = lambda x: pg.profil(x, 47.0, 4.0, 14.0, 1302)
    pg.crete(P, foret, [ENCRE, NU1, NU2, T.CIEL[3]], 0.5)
    pg.sapins(P, foret, densite=0.85, graine=1303, coul=ENCRE)
    brume_claire(P, 45.0, 2.4, 61, T.CIEL[4], 0.5)
    tab.plan("moyen", 0.5)
    # ---- Le pré de nuit, bleu, la rosée qui brille sous la lune ; le chemin qui arrive du plateau.
    f_pre = lambda x: 50.0 + 0.8 * np.sin(_a(x) / 13.0)
    pre = Y > f_pre(X)
    k = np.clip((Y - 50.0) / 30.0, 0, 1)
    P.rampe(pre, 0.4 + 0.35 * (pg.fbm((X + Y) / (2 + 4 * k), Y / (0.7 + 1.6 * k), 3, 1304) - 0.5) + 0.1 * (X - 96) / 96, [ENCRE, NU1, T.S0, NU2, T.S1], 0.45)
    chemin = pre & (np.abs(X - 96.0 - 30.0 * (Y - 50.0) / 30.0 * np.sin(Y / 9.0) - 0.8 * (Y - 50)) < 1.0 + 0.5 * (Y - 50.0))
    P.rampe(chemin, 0.45 + 0.3 * (pg.fbm(X / 1.0, Y / 0.6, 2, 1305) - 0.5), [ENCRE, NU1, NU2, R1], 0.45)
    for i in range(700):                                              # les herbes, leur pointe sous la lune
        y = 50.5 + 29.5 * hz(i, 2, 1311) ** 0.8
        x = -6 + 204 * hz(i, 1, 1311)
        l = 0.4 + 2.0 * (y - 50.0) / 30.0
        P.trait(x, y, x - l * 0.3, y - l, (NU2, T.S0, T.S1, T.CIEL[3])[i % 4])
    for i in range(80):
        x, y = -4 + 200 * hz(i, 1, 1306), 51 + 29 * hz(i, 2, 1306)
        if (p + hz(i, 3, 1306)) % 1.0 < 0.2:
            P.point(x, y, T.CIEL[9])
    # ---- Les sapins de part et d'autre, la lune sur leur côté gauche.
    for (x, y, h) in ((30.0, 54.0, 18.0), (40.0, 52.0, 13.0), (150.0, 53.0, 16.0), (162.0, 54.0, 21.0), (176.0, 52.0, 12.0)):
        for j in range(int(h / 1.6)):
            u = j / (h / 1.6)
            w = h * 0.34 * (1 - u) + 0.6
            yy = y - h * u
            m_ = P.masque_poly([(x - w, yy), (x + w, yy), (x, yy - 2.6)])
            P.remplir(m_, ENCRE)
            P.remplir(m_ & (X < x - 0.2), T.S0)
            P.remplir(m_ & (X < x - w * 0.5) & (P.T < 0.5), T.CIEL[4])
    # ---- La halte de pierre : moellons, toit d'ardoise, la fenêtre et la porte en or chaud, la cheminée qui fume.
    hx0, hx1, hy = 74.0, 116.0, 60.0
    mur = (X > hx0) & (X < hx1) & (Y > 36.0) & (Y < hy)
    rang_ = np.floor((Y - 36.0) / 2.2)
    joint = (np.abs(((X - hx0 + 2.6 * (rang_ % 2)) % 5.2) - 0.1) < 0.25) | (np.abs(((Y - 36.0) % 2.2)) < 0.25)
    P.rampe(mur, 0.65 - 0.25 * (X - hx0) / (hx1 - hx0) + 0.2 * (pg.fbm(X / 2.0, Y / 1.2, 2, 1307) - 0.5), [NU1, NU2, R1, R2, R3], 0.45)
    P.remplir(mur & joint, NU1)
    toit = P.masque_poly([(hx0 - 4.0, 37.0), (hx1 + 4.0, 37.0), (hx1 - 4.0, 24.0), (hx0 + 4.0, 24.0)])
    P.rampe(toit, 0.65 - 0.3 * (X - hx0) / (hx1 - hx0) + 0.25 * (np.sin((Y - 24) * 2.6) > 0.6), [ENCRE, NU1, NU2, T.CIEL[3]], 0.45)
    P.remplir(P.crete(toit), T.CIEL[6])
    P.rect(hx1 - 10.0, 18.0, 4.0, 8.0, R1)                            # la cheminée
    P.rect(hx1 - 7.0, 18.0, 1.0, 8.0, R3)
    pg.fumee(P, hx1 - 8.0, 17.6, p)
    fx_, fy_ = 104.0, 44.0                                            # la fenêtre
    halo(P, fx_ + 3.0, fy_ + 3.0, 14.0, LA1, 0.4)
    P.rect(fx_, fy_, 7.0, 7.0, LA2)
    P.rect(fx_ + 0.6, fy_ + 0.6, 5.8, 5.8, LA3)
    P.rect(fx_ + 3.2, fy_, 0.6, 7.0, BO1)
    P.rect(fx_, fy_ + 3.2, 7.0, 0.6, BO1)
    P.ell(fx_ + 1.8, fy_ + 2.0, 1.0, 1.0, BLANC)                       # Brouillon qui boit la vapeur de la marmite ?
    sol_or = P.masque_poly([(fx_ - 1.0, hy + 0.4), (fx_ + 8.0, hy + 0.4), (fx_ + 14.0, hy + 9.0), (fx_ + 2.0, hy + 9.0)])
    P.rampe(sol_or & pre, 0.5 + 0.3 * (pg.fbm(X / 1.0, Y / 0.7, 2, 1310) - 0.5) - 0.04 * (Y - hy), [TE1, BO3, ME1, LA1], 0.45)                    # la fenêtre posée sur l'herbe
    dx_ = 82.0                                                        # la porte, entrouverte
    P.ell(dx_ + 3.4, hy - 9.0, 3.4, 3.0, BO1, cond=Y < hy - 9.0)
    P.rect(dx_, hy - 9.0, 6.8, 9.0, BO1)
    P.rect(dx_ + 4.6, hy - 9.0, 2.2, 9.0, LA2)
    P.rect(dx_ + 5.4, hy - 8.0, 1.0, 8.0, LA3)
    P.rampe(P.masque_poly([(dx_ + 4.6, hy), (dx_ + 6.8, hy), (dx_ + 10.0, hy + 8.0), (dx_ + 5.0, hy + 8.0)]) & pre, 0.55 - 0.04 * (Y - hy), [TE1, BO3, ME1, LA1], 0.45)
    P.rect(fx_ - 0.6, fy_ - 8.0, 8.0, 2.4, NE2)                        # l'écriteau (un coq dessiné)
    P.trait(fx_ + 2.0, fy_ - 7.2, fx_ + 5.0, fy_ - 6.6, NU2)
    # Le banc contre le mur, le tas de bûches, la marmite dehors, les outils.
    P.rect(118.0, 56.0, 8.0, 1.0, BO3)
    P.rect(118.6, 57.0, 0.6, 3.0, BO1)
    P.rect(124.6, 57.0, 0.6, 3.0, BO1)
    for i in range(8):
        x, y = 64.0 + (i % 4) * 2.4 + (i // 4) * 1.2, 59.0 - (i // 4) * 2.0
        P.ell(x, y, 1.2, 1.0, BO2)
        P.ell(x - 0.2, y, 0.8, 0.7, TE2)
    # ---- Tournebise, le coq de fer rouillé, sur le faîte (la clé) : il pointe vers la montagne (à gauche), sa lanterne
    # pendue au bec se balance ; elle éclaire le toit.
    gx, gy = 96.0, 24.0
    P.trait(gx, gy, gx, gy - 12.0, R2)
    P.trait(gx - 3.0, gy - 6.0, gx + 3.0, gy - 6.0, R2)
    P.point(gx - 3.0, gy - 6.0, R4)
    coq = P.masque_poly([(gx - 6.0, gy - 15.0), (gx - 4.0, gy - 18.0), (gx - 2.4, gy - 16.4), (gx + 1.0, gy - 16.0),
                         (gx + 4.0, gy - 20.0), (gx + 6.0, gy - 19.0), (gx + 5.4, gy - 15.0), (gx + 3.0, gy - 12.4),
                         (gx - 3.0, gy - 12.4)])
    P.rampe(coq, 0.5 + 0.3 * (X - gx) / 6.0 + 0.25 * (pg.fbm(X / 0.7, Y / 0.7, 2, 1308) - 0.5), [RO1, ME1, RO2, LA1], 0.45)
    P.remplir(P.crete(coq), LA2)
    P.point(gx - 3.6, gy - 16.6, LA3)                                  # son œil
    P.poly([(gx - 6.0, gy - 15.0), (gx - 7.6, gy - 15.4), (gx - 6.0, gy - 16.0)], ME1)
    bal = 1.2 * onde(p)
    lx, ly = gx - 7.0 + bal, gy - 10.4
    P.trait(gx - 7.0, gy - 15.2, lx, ly - 1.4, R3)
    halo(P, lx, ly, 9.0, LA2, 0.55)
    P.rect(lx - 1.0, ly - 1.4, 2.0, 2.6, BO1)
    P.rect(lx - 0.6, ly - 1.0, 1.2, 1.8, LA3)
    for i in range(3):                                                # des papillons de nuit autour de la lanterne
        t = (p + i / 3.0) % 1.0
        P.point(lx + 4.0 * math.cos(t * 6.283 + i), ly + 2.4 * math.sin(t * 6.283 * 2 + i), NE3)
    tab.plan("premier", 1.0)
    # ---- Premier plan : la clôture de piquets, un hibou sur le piquet de droite (il cligne), des herbes, des pierres.
    for i in range(14):
        x = -4.0 + i * 15.0
        if 16 < x < 44 or 146 < x < 174:
            continue
        P.rect(x, 66.0, 1.2, 12.0, ENCRE)
        P.rect(x + 0.8, 66.0, 0.4, 12.0, NU2)
        P.point(x + 0.6, 66.0, T.CIEL[6])
    for yb in (69.0, 73.0):
        for (a, b) in ((-6.0, 16.0), (44.0, 146.0), (174.0, 198.0)):
            P.trait(a, yb, b, yb + 0.4, NU2)
    ox, oy = 176.0, 64.0                                              # le hibou
    P.ell(ox + 1.0, oy, 2.2, 2.8, TE1)
    P.ell(ox + 1.0, oy + 0.6, 1.4, 1.8, TE2)
    ferme = int(p * 8) % 8 == 3
    for dx in (0.2, 1.8):
        if ferme:
            P.trait(ox + dx - 0.4, oy - 1.0, ox + dx + 0.4, oy - 1.0, ENCRE)
        else:
            P.point(ox + dx, oy - 1.0, LA2, 2)
    P.poly([(ox - 0.6, oy - 2.6), (ox, oy - 3.6), (ox + 0.4, oy - 2.4)], TE1)
    P.poly([(ox + 2.6, oy - 2.6), (ox + 2.0, oy - 3.6), (ox + 1.6, oy - 2.4)], TE1)
    pg.touffes(P, lambda x: 79.2 + 0.0 * _a(x), n=90, haut=3.0, graine=1309, tons=(ENCRE, NU1, T.S0, NU2, T.S1))


# =====================================================================================================================
# Le sentier des mélèzes (chapitre 6) : « On monte. Le sentier fait des lacets entre des mélèzes tout jaunes qui perdent
# leurs aiguilles, ça fait un tapis qui glisse. Là-haut, entre deux Dents-de-Lait, on voit le col : la Gencive. »
# Une pente raide face à nous, le matin : les lacets qui rapetissent en montant, l'éboulis des six gros rochers (le
# raccourci), les mélèzes d'or de plus en plus rares vers le haut, les premières plaques de neige ; au-dessus, les deux
# Dents, plus proches qu'au Plateau, et le col arrondi entre elles. Le soleil vient de la gauche, comme au col.
# =====================================================================================================================
MATIN = Tons(ciel=("#3a68b4", "#4574bc", "#5381c4", "#6390cc", "#759fd4", "#88addb", "#9cbce2", "#b0cbe8", "#c4d8ee",
                   "#d6e4f3", "#e6eef7", "#f4f7fb"), eau=EAU_CLAIRE, soleil="#fff6e0", **_COMMUN)
HA1, HA2, HA3 = cs("#7f9cc6", "#a6bddc", "#c9d8ec")          # la brume bleue des lointains
OC1, OC2, OC3 = cs("#4a3424", "#7a5634", "#b08a4e")          # l'herbe rousse à l'ombre


def f_dents_sentier(x):
    """Les deux Dents vues d'en bas du sentier : la gauche (x = 92), la droite (x = 150), le col arrondi vers x = 121."""
    x = _a(x)
    hl = 52.0 * np.maximum(0, 1 - np.abs(x - 92) / np.where(x < 92, 46.0, 34.0)) ** 1.25
    hr = 47.0 * np.maximum(0, 1 - np.abs(x - 150) / np.where(x < 150, 32.0, 44.0)) ** 1.15
    selle = 32.0 - 0.012 * (x - 121) ** 2
    rug = (2.0 * pg.fbm(x / 3.0, x * 0 + 0.3, 3, 1001) + 0.8 * pg.fbm(x / 1.1, x * 0 + 0.7, 2, 1002)) * (
        1 - 0.8 * np.exp(-((x - 121) / 10.0) ** 2))
    return 46.0 - np.maximum(np.maximum(hl, hr), selle) - rug


def massif(P, f, pics, roche, neige_l, neige_o, liseré, graine, brume=None, arete=0.42, selle=None, droite=False):
    """Une montagne d'ardoise et de neige sous la courbe f : couloirs dans la pente, névés sur les vires, une arête par
    pic (face au soleil à gauche, d'ombre à droite). pics : [(x, y du sommet)]. Renvoie le masque."""
    X, Y = P.X, P.Y
    fx = f(X)
    m = Y > fx
    prof = Y - fx
    ip = np.argmin(np.stack([np.abs(X - px) for px, _ in pics]), axis=0)
    if selle is not None and len(pics) == 2:                             # le partage entre les deux pics : au col
        ip = (X > selle).astype(int)
    cx = np.array([px for px, _ in pics])[ip]
    hy = np.array([py for _, py in pics])[ip]
    ar = cx + arete * (Y - hy)
    s_ = np.sign(X - ar)
    flanc = -np.tanh((X - ar) / 2.5)
    if droite:                                                         # la lumière vient de la droite
        ar = cx - arete * (Y - hy)
        flanc = np.tanh((X - ar) / 2.5)
    if selle is not None:
        w_ = np.clip(1.4 - np.abs(X - selle) / 12.0, 0, 1)
        flanc = w_ * 0.35 * np.tanh((selle - X) / 8.0) + (1 - w_) * flanc
    trav = X - cx - s_ * 0.75 * (Y - hy)

    def ride(t, y):
        return 0.65 * (1 - np.abs(2 * pg.fbm(t / 3.4, y / 10.0, 3, graine) - 1)) + 0.35 * (
            1 - np.abs(2 * pg.fbm(t / 1.2, y / 4.5, 2, graine + 1) - 1))

    pente = ride(trav + 0.4, Y) - ride(trav - 0.4, Y)
    contre = pg.fbm(trav / 10.0, Y / 14.0, 2, graine + 2) - 0.5
    v = 0.46 + 0.3 * flanc + 1.3 * pente + 0.45 * contre
    P.rampe(m, v, roche, 0.5)
    vires = pg.fbm(trav / 7.0, Y / 2.6, 3, graine + 3) + 0.25 * np.clip(prof / 14.0, 0, 1) - 0.4 * np.clip(-pente * 5, 0, 1) - 0.3 * contre
    nv = m & ((vires > 0.56 - 0.06 * flanc) | (prof < 1.0 + 1.2 * pg.fbm(X / 2.4, Y, 2, graine + 4)))
    lum = 0.6 + 0.32 * flanc + 1.2 * pente + 0.3 * (vires - 0.6)
    P.rampe(nv & (flanc > -0.2), lum, neige_l, 0.5)
    P.rampe(nv & (flanc <= -0.2), lum + 0.25, neige_o, 0.5)
    P.remplir(P.crete(m) & (flanc > -0.2), liseré)
    P.remplir(m & (np.abs(X - ar) < 0.3) & (prof < 26), liseré)
    if brume is not None:
        voile(P, m, brume[0], np.clip((Y - brume[1]) / brume[2], 0, 0.9))
    return m


def petit_meleze(P, x, y, h, graine):
    """Un mélèze lointain, au pixel : un fuseau d'or, son côté d'ombre, un tronc qui dépasse à peine."""
    P.trait(x, y, x, y - h, BO1)
    n = max(2, int(h * P.s))
    for j in range(n):
        u = j / max(1, n - 1)
        yy = y - h * (0.15 + 0.85 * u)
        l = h * 0.28 * (1 - u) + 0.3
        P.trait(x - l, yy + 0.2, x, yy, PJ2 if (j + graine) % 3 else PJ1)
        P.trait(x, yy, x + l, yy + 0.2, PJ1 if (j + graine) % 3 else OC3)
        if j % 2 == 0:
            P.point(x - l * 0.6, yy, PJ3)


@decor("petit-nuage", "sentier-des-melezes", soleil=(36.0, -12.0), tons=MATIN, nom="Le sentier des mélèzes", matiere=True)
def sentier_des_melezes(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    # ---- Le ciel : un bleu froid et net ; deux nuages ronds qui passent ; des voiles hauts.
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=36.0, haut=0.05, halo=0.34, disque=4.0)
    pg.voiles(P, y=-8.0, epais=6.0, seuil=0.6, graine=1003)
    pg.cumulus(P, [(176, -2, 26, 5.0, 1004, 6, 0.2), (18, 9, 20, 3.6, 1005, 5, 0.6)], dessous=-0.5)
    tab.plan("lointains", 0.2)
    # ---- Au loin, d'autres sommets, bleus de brume ; puis les deux Dents et la Gencive, nettes, au soleil du matin.
    loin = lambda x: pg.profil(x, 33.0, 13.0, 16.0, 1006) - 6.0 * np.exp(-((_a(x) - 20) / 24.0) ** 2)
    pg.crete(P, loin, [HA1, HA2, HA3, T.CIEL[9]], 0.8)
    voile(P, (Y > loin(X)) & (Y > 26), T.CIEL[10], np.clip((Y - 26.0) / 10.0, 0, 0.8))
    massif(P, f_dents_sentier, [(92.0, float(f_dents_sentier(92.0))), (150.0, float(f_dents_sentier(150.0)))],
           [NU2, R1, R2, R3, R4], [SH1, NE1, NE2, NE3, NE4, BLANC], [SH0, SH1, NE1, NE2, NE3], OR_N, 1007,
           brume=(HA3, 22.0, 16.0), selle=121.0)
    # Le panache que le vent tire des deux pointes, une cascade qui file sur la Dent de droite.
    for (sx, g) in ((92.0, 1008), (150.0, 1009)):
        sy = float(f_dents_sentier(sx)) + 0.8
        u = (X - sx) / 18.0
        pan = (u > 0) & (u < 1) & (np.abs(Y - sy - 2.0 * u - 0.8 * np.sin(u * 7 + p * 6.283)) < 0.5 + 2.0 * u)
        voile(P, pan & (pg.fbm((X - 24 * p) / 2.4, Y / 1.2, 3, g) > 0.45 + 0.4 * u), BLANC, 0.7 * (1 - u))
    for j in range(16):
        y = 18.0 + j * 0.9
        x = 160.0 + 0.6 * math.sin(j * 0.9)
        P.point(x, y, NE4 if (j + int(p * 8)) % 3 else HA2)
    # Le pied des Dents se perd dans une brume douce, où l'on devine une forêt lointaine.
    brume_claire(P, 33.0, 3.0, 50, HA3, 0.55)
    # Une épaule boisée à mi-distance, sous les Dents : des mélèzes d'or et des pins sarcelle, voilés de bleu.
    epaule = lambda x: 38.0 + 3.0 * np.sin((_a(x) - 60) / 20.0) + 0.8 * np.sin(_a(x) / 4.1) + 0.5 * np.sin(_a(x) / 1.7)
    me = Y > epaule(X) + 6.0 * np.clip((60.0 - X) / 30.0, 0, 1) ** 2
    P.rampe(me, 0.5 + 0.6 * (pg.fbm(X / 1.0, Y / 0.8, 2, 1044) - 0.5) + 2.0 * (pg.fbm(X / 6.0 + 0.2, Y / 3.0, 2, 1045) - pg.fbm(X / 6.0 - 0.2, Y / 3.0, 2, 1045)),
            [T.S1, OC2, T.S2, PJ1, PJ2, PJ3], 0.5)
    for i in range(110):
        x = 30 + 166 * hz(i, 1, 1046)
        y = float(epaule(x)) + 6.0 * max(0.0, (60.0 - x) / 30.0) ** 2 + 0.4 + 2.0 * hz(i, 2, 1046)
        h = 1.2 + 1.8 * hz(i, 3, 1046)
        P.trait(x, y, x, y - h, T.S1 if hz(i, 4, 1046) < 0.3 else PJ2)
        P.point(x - 0.3, y - h * 0.5, PJ3 if hz(i, 4, 1046) >= 0.3 else T.S2)
    voile(P, me, HA3, np.clip(0.62 - (Y - 38.0) / 24.0, 0.3, 0.62))
    vallee = (Y > 44.0 + 2.0 * np.sin(X / 7.0) + 1.0 * np.sin(X / 2.3)) & (X < 90)
    P.rampe(vallee, 0.5 + 0.5 * (pg.fbm(X / 1.4, Y / 0.9, 2, 1041) - 0.5) + 0.03 * (Y - 44), [OC2, PJ1, OC3, PJ2, PJ3], 0.5)
    voile(P, vallee, HA3, np.clip(0.6 - (Y - 44.0) / 30.0, 0.15, 0.6))
    for i in range(90):                                               # la forêt d'or, en bas, au loin
        x, y = -4 + 94 * hz(i, 1, 1042), 45.5 + 14.0 * hz(i, 2, 1042)
        petit_meleze(P, x, y, 0.8 + 2.4 * (y - 44) / 16.0, i)
    voile(P, vallee, HA3, 0.25)
    tab.plan("moyen", 0.5)
    # ---- La pente raide, face à nous : herbe rousse et rocaille, des plis où l'ombre s'amasse, la brume vers le haut.
    f_haut = lambda x: np.where(_a(x) < 60, 60.0 + 2.0 * np.sin(_a(x) / 9.0), 60.0 - 0.21 * (_a(x) - 60)) + 1.0 * np.sin(_a(x) / 5.0) + 0.6 * np.sin(_a(x) / 2.1)
    pente = Y > f_haut(X)

    def relief(x, y):
        k = 120.0 / np.maximum(y - 30.0, 3.0)
        return pg.fbm((x - 96) * k / 30.0 / 4.0, k / 1.2, 3, 1011) + 0.4 * pg.fbm((x - 96) * k / 30.0, k / 0.4, 2, 1012)

    lumx = relief(X + 0.6, Y) - relief(X - 0.6, Y)
    proche = np.clip((Y - 37.0) / 40.0, 0, 1)
    pli = np.sin((X * 0.55 + Y) / 4.2 + 2.0 * pg.fbm(X / 9.0, Y / 9.0, 2, 1040))            # les ravines de la pente
    v = 0.6 + (1.5 + 3.0 * proche) * lumx + 0.18 * (pg.fbm(X / 2.0, Y / 1.4, 2, 1013) - 0.5) - 0.1 * proche + 0.12 * pli * (X > 60)
    P.rampe(pente, v, [OC1, TE1, OC2, PJ1, OC3, PJ2, PJ3], 0.45)
    P.remplir(P.crete(pente), PJ4)
    for i in range(14):                                               # des affleurements de roche grise
        x, y = -2 + 196 * hz(i, 1, 1014), 40 + 30 * hz(i, 2, 1014) ** 1.4
        r = (1.2 + 2.0 * hz(i, 3, 1014)) * (0.4 + (y - 37) / 40.0)
        mm = P.ell(x, y, r * 1.4, r * 0.6, R2, cond=Y < y + 0.2)
        P.rampe(mm, 0.6 - 0.5 * (X - x) / r + 0.2 * (pg.fbm(X / 0.9, Y / 0.9, 2, 1016 + i) - 0.5), [R1, R2, R3, R4], 0.5)
        P.remplir(mm & (np.hypot(X - x - r * 0.4, Y - y + r * 0.2) < r * 0.4), ME1)          # du lichen orange
    # Les premières plaques de neige, en haut de la pente, dans les creux à l'ombre.
    for i in range(10):
        x = 140 + 52 * hz(i, 1, 1017)
        y = float(f_haut(x)) + 0.6 + 6.0 * hz(i, 2, 1017)
        r = 1.6 + 3.0 * hz(i, 3, 1017)
        nm = ((((X - x - 0.4 * (Y - y)) / r) ** 2 + ((Y - y) / (r * 0.45)) ** 2 < 1 + 0.9 * (pg.fbm(X / 0.8, Y / 0.5, 2, 1018 + i) - 0.5))
              & pente)
        P.rampe(nm, 0.75 - 0.3 * (X - x) / r, [SH1, NE2, NE3, NE4], 0.5)
    # ---- Les lacets : une bande de terre claire qui zigzague, plus étroite en montant, bordée de pierres.
    lacets = [(46.0, 80.0), (84.0, 73.6), (178.0, 66.0), (112.0, 60.4), (186.0, 54.0), (134.0, 49.6), (190.0, 44.4),
              (152.0, 41.0), (192.0, 37.4)]
    chemin = np.zeros(X.shape, dtype=bool)
    for (x0, y0), (x1, y1) in zip(lacets[:-1], lacets[1:]):
        for k in range(40):
            t = k / 39.0
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            e = 0.35 + 2.6 * ((y - 34.0) / 46.0) ** 1.3
            chemin |= (np.abs(X - x) < e * 2.2) & (np.abs(Y - y) < e * 0.5)
    chemin &= pente
    talus = np.roll(chemin, 3, axis=0) & ~chemin & pente
    voile(P, talus, OC1, 0.6)
    P.rampe(chemin, 0.7 + 0.25 * (pg.fbm(X / 1.6, Y / 0.8, 2, 1019) - 0.5) + 0.004 * (Y - 40), [TE2, TE3, PJ4, CREME], 0.45)
    bordure = chemin & ~np.roll(chemin, -1, axis=0)
    P.remplir(bordure & (hz(P.XI, P.YI, 1020) < 0.5), TE1)
    P.remplir(chemin & ~np.roll(chemin, 1, axis=0) & (hz(P.XI, P.YI, 1021) < 0.35), R3)
    # ---- L'éboulis des six gros rochers, tout droit dans la pente (le raccourci) ; des pierres plus petites autour.
    blocs = [(152.0, 71.0, 4.8), (156.0, 63.4, 3.9), (160.0, 57.0, 3.2), (164.0, 51.4, 2.6), (168.0, 46.6, 2.1), (172.0, 42.6, 1.7)]
    for i in range(40):
        y = 40.0 + 36.0 * hz(i, 2, 1022)
        x = 150.0 + 0.6 * (76.0 - y) * 0.6 + 12.0 * (hz(i, 1, 1022) - 0.5)
        r = 0.4 + 1.2 * hz(i, 3, 1022) * (y - 36) / 40
        P.ell(x, y, r * 1.2, r * 0.7, R2 if hz(i, 4, 1022) < 0.6 else R3)
        P.point(x - r * 0.4, y - r * 0.4, R4)
    for i, (x, y, r) in enumerate(blocs):
        voile(P, (((X - x - r * 0.9) / (r * 1.4)) ** 2 + ((Y - y) / (r * 0.3)) ** 2 < 1) & pente, OC1, 0.6)
        mm = P.ell(x, y - r * 0.5, r, r * 0.72, R2, cond=Y < y + 0.1)
        P.rampe(mm, 0.62 - 0.55 * (X - x) / r - 0.3 * (Y - y + r * 0.5) / r + 0.2 * (pg.fbm(X / 0.8, Y / 0.8, 2, 1023 + i) - 0.5),
                [R1, R2, R3, R4], 0.5)
        P.remplir(P.crete(mm) & (X < x + r * 0.3), NE4)
        P.remplir(mm & (np.abs(X - x - 0.2 * r - 0.3 * (Y - y)) < 0.18 * r) & (Y > y - r * 0.8), R1)    # une fissure
    # ---- Les mélèzes : nombreux en bas, rares en haut ; aucun sur le chemin ni sur l'éboulis.
    places = []
    for i in range(170):
        x = -6 + 204 * hz(i, 1, 1024)
        y = 38.0 + 40.0 * hz(i, 2, 1024) ** 0.75
        if hz(i, 3, 1024) > 0.15 + 0.55 * (y - 37) / 40 or pg.fbm(x / 14.0, y / 6.0, 2, 1043) < 0.42:
            continue
        ix, iy = P.px(x), min(P.H - 1, P.py(y))
        if not (0 <= ix < P.Wt) or chemin[iy, ix] or abs(x - 150.0 - 0.36 * (76.0 - y)) < 7 or not pente[iy, ix]:
            continue
        if (18 < x < 44 and y > 52) or (106 < x < 134 and y > 50):
            continue                                                  # la place de Pilou et de son interlocuteur
        places.append((y, x, i))
    for (y, x, i) in sorted(places):
        h = 1.4 + 24.0 * ((y - 37.0) / 40.0) ** 1.6 * (0.5 + 0.8 * hz(i, 4, 1024))
        if h < 6.0:
            petit_meleze(P, x, y, h, i)
        else:
            meleze(P, x, y, h, graine=1100 + i, dore=hz(i, 5, 1024) > 0.12)
    pg.oiseaux(P, 62, 8, 3, coul=ENCRE)
    # La sentinelle : une marmotte debout sur un rocher, qui siffle (deux poses), près de l'entrée d'un terrier où
    # brille un bocal (on approche de chez Madame Bocal).
    mx, my = 141.0, 49.0
    mm = P.ell(mx, my + 0.6, 2.4, 1.0, R3, cond=Y < my + 0.8)
    P.remplir(P.crete(mm), R4)
    debout = onde(p) > 0
    P.ell(mx, my - 1.6 - (0.4 if debout else 0), 0.9, 1.6 + (0.4 if debout else 0), TE2)
    P.ell(mx + 0.15, my - 3.3 - (0.8 if debout else 0), 0.7, 0.6, TE2)
    P.point(mx + 0.5, my - 3.4 - (0.8 if debout else 0), ENCRE)
    P.ell(mx - 0.3, my - 1.2, 0.4, 0.8, TE3)
    P.ell(146.0, 50.6, 1.4, 1.0, ENCRE, cond=Y < 51.0)
    P.rect(147.6, 49.0, 1.0, 1.6, NE2)
    P.point(147.8, 49.4, LA2)
    tab.plan("premier", 1.0)
    # ---- Premier plan : le sentier où l'on marche, sous un tapis d'aiguilles d'or ; un grand mélèze à gauche, qui cadre ;
    # à droite, un rocher moussu de lichen et un panneau de bois ; les aiguilles qui tombent.
    f_sol = lambda x: 75.6 + 0.8 * np.sin(_a(x) / 11.0) + 0.5 * np.sin(_a(x) / 3.7)
    sol = Y > f_sol(X)
    P.rampe(sol, 0.55 + 0.35 * (pg.fbm(X / 3.0, Y / 1.0, 3, 1025) - 0.5) + 0.03 * (Y - 76), [TE1, OC2, PJ1, OC3, PJ2, PJ3], 0.45)
    P.remplir(P.crete(sol), PJ4)
    for i in range(520):                                              # le tapis d'aiguilles
        x, y = -6 + 204 * hz(i, 1, 1026), 76.0 + 4.0 * hz(i, 2, 1026)
        a = hz(i, 3, 1026) * 3.1
        P.trait(x, y, x + 1.2 * math.cos(a), y + 0.5 * math.sin(a), (PJ3, OC2, ME2, PJ4, OC1)[i % 5])
    for i in range(7):                                                # des pommes de mélèze
        x, y = 50 + 20 * i + 6 * hz(i, 1, 1027), 77.4 + 1.6 * hz(i, 2, 1027)
        P.ell(x, y, 0.7, 0.5, BO3)
        P.point(x - 0.2, y - 0.2, TE3)
    # Le grand mélèze de gauche : son tronc tout proche, son écorce en plaques, ses branches qui pendent au-dessus.
    tr = (X > -6) & (X < 5.0 + 0.6 * np.sin(Y / 9.0)) & (Y > -18)
    P.rampe(tr, 0.3 + 0.5 * np.clip((X + 6) / 11.0, 0, 1) * 0 + 0.55 * np.clip((5.0 - X) / 11.0, 0, 1) + 0.25 * (
        pg.fbm(X / 0.8, Y / 3.0, 3, 1028) - 0.5), [ENCRE, BO1, BO2, BO3, TE2], 0.45)
    P.remplir(tr & (np.abs(np.sin(Y / 1.7 + 2 * np.sin(X))) > 0.94), BO1)                 # les plaques d'écorce
    P.remplir(tr & ~np.roll(tr, 1, axis=1) & (X > 2), OC3)
    pg.feuillage(P, lambda x: 9.0 - 0.32 * _a(x) + 2.4 * np.sin(_a(x) / 5.0) + 1.0 * np.sin(_a(x) / 2.2 + 1.0), x0=-6, x1=56,
                 n=620, epais=8.0, graine=1029, y_max=12.0, tons=([BO1, OC1, OC2, PJ1], [OC2, PJ1, PJ2], [PJ1, PJ2, PJ3, ME2, PJ4]))
    P.courbe([(3.0, -4.0), (14.0, -7.5), (26.0, -9.0), (40.0, -13.0)], BO1, P.ep(1.0), 1)
    P.courbe([(3.0, 6.0), (12.0, 4.6), (20.0, 2.0)], BO1, P.ep(0.7), 1)
    # À droite : un rocher couvert de lichen, une touffe de myrtilles bleues, et le panneau qui montre le col.
    rx_, ry_ = 186.0, 80.0
    mm = P.ell(rx_, ry_, 10.0, 7.5, R2, cond=Y < 80.5)
    P.rampe(mm, 0.66 - 0.5 * (X - rx_) / 10.0 - 0.3 * (Y - 74) / 7.0 + 0.2 * (pg.fbm(X / 1.0, Y / 1.0, 2, 1030) - 0.5),
            [R1, R2, R3, R4], 0.45)
    P.remplir(mm & (pg.fbm(X / 1.4, Y / 1.4, 2, 1031) > 0.62), ME2)
    P.remplir(mm & (pg.fbm(X / 1.4, Y / 1.4, 2, 1031) > 0.72), LA2)
    P.remplir(P.crete(mm) & (X < rx_), NE4)
    for i in range(12):
        x, y = 174.0 + 1.2 * i + 0.8 * hz(i, 1, 1032), 75.0 + 1.2 * hz(i, 2, 1032)
        P.point(x, y, T.BLEU if i % 3 else T.VIOLET, 2)
    px_, py_ = 178.0, 62.0                                            # le panneau : une flèche vers le haut, un col dessiné
    P.rect(px_ - 0.5, py_, 1.1, 14.0, BO1)
    P.rect(px_ - 0.5, py_, 0.4, 14.0, BO3)
    pm = P.poly([(px_ - 6.0, py_ + 0.6), (px_ + 3.2, py_ + 0.2), (px_ + 5.4, py_ + 2.2), (px_ + 3.2, py_ + 4.2), (px_ - 6.0, py_ + 3.8)], BO2)
    P.remplir(P.crete(pm), TE3)
    P.courbe([(px_ - 4.4, py_ + 3.0), (px_ - 2.8, py_ + 1.4), (px_ - 1.8, py_ + 2.4), (px_ - 0.8, py_ + 1.2), (px_ + 1.0, py_ + 3.0)], TE3, 1)
    # Les aiguilles qui tombent, devant tout.
    aiguilles(P, -6, -10, 200, 78, 60, graine=1033)


# =====================================================================================================================
# Le terrier aux bocaux : l'intérieur d'un terrier de marmotte. Des étagères de bois du sol au plafond couvertes de
# bocaux à étiquettes manuscrites (fruits, lueurs, brumes), une lampe à huile, un fauteuil de foin, lumière dorée.
# =====================================================================================================================
@decor("petit-nuage", "terrier-aux-bocaux", soleil=(96.0, 30.0), tons=SOIR, nom="Le terrier aux bocaux", matiere=True)
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
    # La lumière de la lampe : chaude près d'elle, elle tombe vers les bords ; chaque planche jette son ombre dessous ;
    # les bocaux proches renvoient un reflet d'or.
    peint = P.a >= 0
    for y in (4.0, 18.0, 32.0, 46.0, 60.0):
        voile(P, peint & (Y > y + 1.8) & (Y < y + 4.0), BO1, 0.55)
    dl = np.hypot(X - lx_, (Y - ly_) * 1.2)
    voile(P, peint, BO1, np.clip((dl - 26.0) / 70.0, 0, 0.65))
    voile(P, peint & (dl < 34.0), LA2, np.clip(0.45 - dl / 80.0, 0, 0.45), lumiere=True)
    reflet = peint & (np.abs(X - np.round(X / 4.6) * 4.6) < 0.25) & (dl < 40.0) & (P.T < 0.5)
    P.remplir(reflet & (pg.fbm(X / 3.0, Y / 3.0, 2, 1320) > 0.5), LA3)
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
    # ---- Seconde passe : la vie du terrier.
    pg.papillon_de_nuit(P, 96.0, 34.0, 8.0, coul=CREME)
    # Un bocal de lueur dont le couvercle saute, tout seul.
    saut = 1.2 if int(p * 8) in (3, 4) else 0.0
    P.rect(140.0, 12.0 - saut, 6.0, 1.2, TE3)
    P.point(143.0, 9.0 - saut * 2, LA3)
    P.rect(120.0, 64.0, 5.0, 6.0, BO3)                            # une échelle de meunier contre les étagères
    for dx in (0.0, 6.0):
        P.trait(170.0 + dx, 66.0, 174.0 + dx, 20.0, BO2, P.ep(0.6))
    for j in range(9):
        y = 62.0 - j * 5.0
        P.trait(170.0 + (66 - y) * 4 / 46.0, y, 176.0 + (66 - y) * 4 / 46.0, y, BO3)
    pg.vapeur(P, 62.0, 46.0, coul=CREME, h=7.0, d=0.3)            # la bouillotte sur le fauteuil
    P.ell(62.0, 48.0, 2.4, 1.6, RO2)
    P.rect(84.0, 66.0, 10.0, 1.2, BO2)                            # des pantoufles, un tricot en cours, sa pelote qui roule
    for (x, c0) in ((86.0, LA1), (90.0, LA1)):
        P.ell(x, 70.0, 1.8, 1.0, c0)
    pel = 1.5 * onde(p)
    P.ell(134.0 + pel, 76.0, 2.2, 2.0, T.VIOLET)
    P.courbe([(134.0 + pel, 74.0), (128.0, 70.0), (122.0, 66.0)], T.VIOLET, 1)
    pg.souris(P, 150.0, 77.6, sens=-1, coul=TE2)
    pg.araignee(P, 40.0, -10.0, 8.0, d=0.5)
    P.rect(100.0, 30.0, 8.0, 6.0, CREME)                          # la liste des bocaux, épinglée : des traits, des croix
    for j in range(3):
        P.rect(101.0, 31.2 + j * 1.5, 4.0 - j, 0.4, BO2)
        P.point(106.0, 31.2 + j * 1.5, LA1)


# =====================================================================================================================
# Le col dans le blanc (chapitre 7) : « Tout est blanc. […] Et juste devant, posé sur le col comme un couvercle, il y a
# un nuage. Un vrai. Un énorme, immobile, blanc. » Le matin, au-dessus de la mer de brouillard : un ciel bleu dur, les
# deux Dents toutes proches (on est à leur pied, vues d'en dessous), le grand nuage endormi dans la selle du col ; la
# file des six cairns qui monte et s'efface dans le blanc, la faille bleue et son pont de neige, la neige qui crisse.
# Le soleil bas vient de la gauche : versants dorés à gauche, ombres bleues portées vers la droite.
# =====================================================================================================================
COL = Tons(ciel=("#2a5aa6", "#3366b0", "#3f73ba", "#4c80c3", "#5b8ecc", "#6c9cd4", "#7fabdb", "#94bae2", "#aac9e9",
                 "#c1d8f0", "#d8e6f5", "#eef4fa"), eau=EAU_CLAIRE, soleil="#fff8e8", **_COMMUN)
SH0, SH1, OR_N = cs("#5d73a6", "#7d93c2", "#ffe7bd")
GL1, GL2, GL3 = cs("#4f93bd", "#8ccbe2", "#cdeef6")
NEIGE_L = [SH1, NE1, NE2, NE3, NE4, CREME]            # la neige au soleil, de l'ombre au reflet doré
NEIGE_O = [SH0, SH1, NE1, NE2, NE3]                   # la neige à l'ombre


def f_dents_col(x):
    """Les deux Dents vues de leur pied : la gauche (x = 30) monte hors du cadre, la droite (x = 166) un peu moins ;
    entre elles, la selle du col en U, son creux vers x = 100."""
    x = _a(x)
    hl = 66.0 * np.maximum(0, 1 - np.abs(x - 30) / 66.0) ** 1.25
    hr = 62.0 * np.maximum(0, 1 - np.abs(x - 166) / 60.0) ** 1.25
    selle = 30.0 + 0.0042 * (x - 100) ** 2
    rug = (3.2 * pg.fbm(x / 4.0, x * 0 + 0.3, 3, 961) + 1.4 * pg.fbm(x / 1.3, x * 0 + 0.7, 2, 962)) * (
        1 - 0.75 * np.exp(-((x - 100) / 24.0) ** 2))
    return 54.0 - np.maximum(np.maximum(hl, hr), selle) - rug


def f_neve(x):
    """Le haut du champ de neige qui monte vers le col (on le perd dans le brouillard)."""
    x = _a(x)
    return 41.0 + 1.6 * np.sin(x / 17.0) + 2.6 * np.exp(-((x - 30) / 30.0) ** 2) + 2.0 * np.exp(-((x - 170) / 22.0) ** 2)


def ombre_portee(P, x, y, rx, ry, force=0.55):
    """L'ombre bleue qu'une chose posée sur la neige jette vers la droite (le soleil est bas, à gauche)."""
    m = (((P.X - x - rx * 0.55) / rx) ** 2 + ((P.Y - y) / ry) ** 2 <= 1) & (P.a >= 0)
    voile(P, m, SH0, force)


def rocher_neige(P, x, y, r, graine, haut=0.55):
    """Un rocher d'ardoise qui perce la neige : face au soleil claire, l'autre sombre, un chapeau de neige, son ombre."""
    ombre_portee(P, x + r * 0.4, y + 0.2, r * 1.5, r * 0.32)
    m = P.ell(x, y - r * haut * 0.5, r, r * haut, R2, cond=P.Y < y)
    v = 0.55 - 0.55 * (P.X - x) / r + 0.25 * (pg.fbm(P.X / 1.2, P.Y / 0.8, 2, graine) - 0.5)
    P.rampe(m, v, [R1, R2, R3, R4], 0.5)
    cap = m & (P.Y < y - r * haut * (0.75 + 0.25 * np.sin((P.X - x) * 2.1 + graine)))
    P.rampe(cap, 0.75 - 0.4 * (P.X - x) / r, NEIGE_L, 0.5)
    P.remplir(P.crete(m) & (P.X < x), CREME)

def bouffees(P, liste, rampe, lum=(-0.62, -0.55, 0.42), plancher=None, graine=0, aplati=0.88):
    """Un cumulus peint bouffée par bouffée : (x, y, r, z) ; la plus proche (z + hauteur) gagne, chacune ombrée par sa
    normale ; le bas de chaque bouffée s'assombrit là où elle s'enfonce dans la suivante. Renvoie le masque."""
    best = np.full(P.X.shape, -1e9)
    nx, ny, prof_ = np.zeros(P.X.shape), np.zeros(P.X.shape), np.zeros(P.X.shape)
    for k, (x, y, r, z) in enumerate(liste):
        dx, dy = (P.X - x) / r, (P.Y - y) / (r * aplati)
        d2 = dx * dx + dy * dy + 0.16 * (pg.fbm(P.X / 1.1, P.Y / 1.1, 2, graine + k) - 0.5)
        h = np.sqrt(np.clip(1 - d2, 0, 1)) * r + z
        g = (d2 < 1) & (h > best)
        best = np.where(g, h, best)
        nx, ny, prof_ = np.where(g, dx, nx), np.where(g, dy, ny), np.where(g, d2, prof_)
    m = best > -1e8
    if plancher is not None:
        m &= P.Y < plancher
    nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
    v = 0.55 + 0.6 * (nx * lum[0] + ny * lum[1] + nz * lum[2]) - 0.35 * np.clip(ny - 0.45, 0, 1) * (prof_ > 0.5)
    P.rampe(m, v, rampe, 0.5)
    return m


@decor("petit-nuage", "col-blanc", soleil=(14.0, -6.0), tons=COL, nom="Le col dans le blanc", matiere=True)
def col_blanc(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    # ---- Le ciel : un bleu dur au zénith qui pâlit vers la mer de brouillard ; le soleil bas, à gauche ; des voiles.
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=34.0, haut=0.0, halo=0.42, disque=4.2)
    pg.voiles(P, y=-6.0, epais=7.0, seuil=0.6, graine=963)
    lune = np.hypot(X - 128.0, Y + 9.0)                                   # la lune du matin, presque effacée
    P.remplir((lune < 2.6) & (np.hypot(X - 127.0, Y + 9.6) > 2.3), T.CIEL[8])
    tab.plan("lointains", 0.2)
    # ---- Les deux Dents : roche d'ardoise en couloirs qui suivent la pente, névés sur les vires ; pour chaque Dent,
    # une arête descend en biais : à gauche d'elle la face au soleil, à droite la face d'ombre.
    f = f_dents_col(X)
    mont = Y > f
    prof = Y - f
    gauche = np.abs(X - 30) < np.abs(X - 166)
    cx_ = np.where(gauche, 30.0, 166.0)
    haut_ = np.where(gauche, float(f_dents_col(30.0)), float(f_dents_col(166.0)))
    s_ = np.sign(X - cx_ - 0.42 * (Y - haut_))                             # le côté de l'arête
    arete = cx_ + 0.42 * (Y - haut_)
    flanc = -np.tanh((X - arete) / 3.0)
    selle = (X > 62) & (X < 138)
    flanc = np.where(selle, 0.3 * np.tanh((96 - X) / 18.0), flanc)
    trav = X - cx_ - s_ * 0.75 * (Y - haut_)                              # le long des couloirs, ils suivent la pente

    def ride(t, y):                                                      # un bruit « en arêtes », étiré dans la pente
        return 0.65 * (1 - np.abs(2 * pg.fbm(t / 4.5, y / 13.0, 3, 964) - 1)) + 0.35 * (
            1 - np.abs(2 * pg.fbm(t / 1.6, y / 6.0, 2, 992) - 1))

    d = 0.5
    pente = ride(trav + d, Y) - ride(trav - d, Y)
    contrefort = pg.fbm(trav / 14.0, Y / 18.0, 2, 993) - 0.5                # de grands piliers clairs ou sombres
    v = 0.46 + 0.3 * flanc + 1.3 * pente + 0.5 * contrefort + 0.1 * (pg.fbm(X / 2.0, Y / 2.0, 2, 965) - 0.5)
    P.rampe(mont, v, [NU2, R1, R2, R3, R4], 0.5)
    vires = pg.fbm(trav / 9.0, Y / 3.4, 3, 966) + 0.22 * np.clip(prof / 16.0, 0, 1) - 0.4 * np.clip(-pente * 5, 0, 1) - 0.3 * contrefort
    neige = mont & ((vires > 0.55 - 0.08 * flanc) | (prof < 1.2 + 1.4 * pg.fbm(X / 3.0, Y, 2, 967)))
    lum = 0.6 + 0.32 * flanc + 1.2 * pente + 0.3 * (vires - 0.6)
    P.rampe(neige & (flanc > -0.2), lum, NEIGE_L, 0.5)
    P.rampe(neige & (flanc <= -0.2), lum + 0.25, NEIGE_O, 0.5)
    crete_ = P.crete(mont)
    P.remplir(crete_ & (flanc > -0.2), OR_N)                             # le liseré du soleil levant sur les arêtes
    P.remplir(mont & (np.abs(X - arete) < 0.35) & ~selle & (Y < haut_ + 30), OR_N)   # l'arête elle-même, dorée
    # La crête du grand tour : une arête fine qui monte vers la Dent de droite, balisée de trois petits cairns.
    for i, (x, y) in enumerate(((140.0, 19.0), (148.0, 12.4), (155.0, 5.0))):
        P.ell(x, y, 0.6, 0.9, R1)
        P.point(x, y - 1.0, NE4)
    # Le panache de neige que le vent arrache aux deux pointes, vers la droite.
    for (sx, sy, g) in ((30.0, float(f_dents_col(30.0)) + 1.0, 968), (166.0, float(f_dents_col(166.0)) + 1.0, 969)):
        u = (X - sx) / 26.0
        pan = (u > 0) & (u < 1) & (np.abs(Y - sy - 3.0 * u - 1.2 * np.sin(u * 7 + p * 6.283)) < 0.8 + 3.0 * u)
        voile(P, pan & (pg.fbm((X - 30 * p) / 3.0, Y / 1.5, 3, g) > 0.45 + 0.4 * u), NE4, 0.7 * (1 - u))
    # ---- Le grand nuage du col, endormi dans la selle : sommet doré, ventre bleuté, bord effiloché ; il respire à peine.
    souffle = 0.3 * onde(p)
    rampe_n = [SH0, SH1, NE1, NE2, NE3, NE4, BLANC, CREME]
    liste = []
    rangs = ((7.0, 9.0, 2), (12.5, 20.0, 4), (18.0, 32.0, 6), (23.5, 42.0, 8), (29.0, 50.0, 10), (34.0, 56.0, 11))
    for rg, (y, demi, n) in enumerate(rangs):                         # une coupole : étroite en haut, large en bas
        for i in range(n):
            u = (i + 0.5) / n
            x = 96.0 + (u - 0.5) * 2 * demi + 5.0 * (hz(i, rg, 996) - 0.5) - 6.0 * (rg == 0)
            r = (4.0 + 5.4 * hz(i, rg + 7, 996) ** 1.5) * (1.15 - 0.07 * rg)
            liste.append((x, y + 4.0 * (hz(i, rg + 3, 996) - 0.5) - souffle * (6 - rg) * 0.2, r, 4.0 * rg))
    nuage = bouffees(P, liste, rampe_n, plancher=38.0, graine=997)
    P.remplir(P.crete(nuage) & (X < 106) & (P.T < 0.7), OR_N)
    voile(P, nuage & (X < 96) & (Y < 18), CREME, 0.35, lumiere=True)
    # « Grand dort » : deux yeux fermés, tout petits pour sa taille, et un souffle qui s'en va, très lent.
    for ex in (90.0, 101.0):
        P.courbe([(ex - 1.5, 24.1), (ex, 25.0), (ex + 1.5, 24.1)], SH1, 1)
    tt = p % 1.0
    for j in range(3):
        u = (tt + j / 3.0) % 1.0
        voile(P, np.hypot(X - 106.0 - 14 * u, Y - 27.0 + 2 * u) < 0.8 + 1.4 * u, BLANC, 0.7 * (1 - u))
    # ---- La mer de brouillard : elle noie le pied des Dents et le ventre du grand nuage ; des volutes basses qui
    # roulent lentement vers la droite, plus pâles et plus plates au loin.
    voile(P, Y > 31.0, NE4, np.clip((Y - 31.0) / 6.0, 0, 0.9))
    vol = []
    for rg, (y, r0, n) in enumerate(((33.0, 3.6, 16), (36.5, 4.4, 13), (40.0, 5.4, 11))):
        for i in range(n):
            x = -8 + (208.0 / n) * (i + 0.5 * (rg % 2)) + 4.0 * (hz(i, rg, 998) - 0.5) + 1.2 * (rg + 1) * onde(p, 0.3 * rg)
            vol.append((x, y + 1.2 * (hz(i, rg + 4, 998) - 0.5), r0 * (0.8 + 0.5 * hz(i, rg + 8, 998)), 3.0 * rg))
    brume = bouffees(P, vol, [NE2, NE3, NE4, BLANC], lum=(-0.4, -0.6, 0.5), plancher=44.0, graine=999, aplati=0.45)
    P.remplir(P.crete(brume) & (P.T < 0.5), BLANC)
    tab.plan("moyen", 0.5)
    # ---- Le champ de neige qui monte vers le col : des vagues de vent (sastrugi), lumière rasante, ombres bleues.
    fn = f_neve(X)
    champ = Y > fn

    def relief(x, y):
        """Le relief de la neige en perspective : les vagues grandissent en approchant (y de 40 au loin à 80 tout près)."""
        prof_ = 260.0 / np.maximum(y - 34.0, 2.0)                       # la distance, à peu près
        u = (x - 96.0) * prof_ / 40.0
        return pg.fbm(u / 9.0, prof_ / 1.6, 3, 975) + 0.35 * pg.fbm(u / 2.6, prof_ / 0.5, 2, 976)

    def congeres(x, y):
        prof_ = 260.0 / np.maximum(y - 34.0, 2.0)
        return pg.fbm((x - 96.0) * prof_ / 40.0 / 26.0, prof_ / 5.0, 3, 994)

    lumx = relief(X + 0.6, Y) - relief(X - 0.6, Y)
    grand = congeres(X + 1.2, Y) - congeres(X - 1.2, Y)
    haut_c = congeres(X, Y - 0.6) - congeres(X, Y + 0.6)
    proche = np.clip((Y - 42.0) / 38.0, 0, 1)
    v = 0.66 + (0.8 + 2.6 * proche) * lumx + (3.0 + 5.0 * proche) * grand + 1.5 * haut_c + 0.06 * proche
    P.rampe(champ, v, NEIGE_L, 0.45)
    voile(P, champ & (grand < -0.006) & (Y > 46), SH1, np.clip(-grand * 30, 0, 0.7))      # le creux des congères
    P.remplir(P.crete(champ), NE4)
    for i, (y0, amp, per, ph) in enumerate(((47.0, 0.5, 14.0, 0.0), (51.5, 0.8, 18.0, 1.7), (57.5, 1.1, 22.0, 3.1),
                                            (64.5, 1.5, 26.0, 0.6), (71.0, 1.9, 30.0, 2.4))):
        c = y0 + amp * np.sin(X / per + ph) + 0.4 * amp * np.sin(X / (per * 0.37) + ph * 2)
        k = (y0 - 40.0) / 30.0
        ombre = champ & (Y > c) & (Y < c + 1.6 * k + 0.3) & (pg.fbm(X / 9.0, Y * 0 + i, 2, 1000) > 0.35)
        voile(P, ombre, SH1, np.clip(0.6 - (Y - c) / (2.2 * k + 0.4), 0, 0.6))
        P.remplir(ombre & (Y < c + 0.35), NE4)
        P.remplir(champ & (Y > c - 0.4 * k - 0.1) & (Y <= c) & (pg.fbm(X / 9.0, Y * 0 + i, 2, 1000) > 0.35), CREME)
    for i in range(14):                                               # les rides du vent, serrées au loin
        y0 = 42.0 + 38.0 * (i / 13.0) ** 1.6
        c = y0 + (0.3 + 1.2 * i / 13.0) * np.sin(X / (5.0 + i * 1.1) + i) + 0.4 * np.sin(X / 2.7 + i * 1.7)
        trou_ = pg.fbm(X / (1.6 + 0.5 * i), Y * 0 + i, 2, 977) > 0.52
        P.remplir(champ & (np.abs(Y - c) < 0.16 + 0.02 * i) & trou_, NE2 if i % 3 else SH1)
        P.remplir(champ & (Y > c + 0.16) & (Y < c + 0.3 + 0.05 * i) & trou_, NE4)
    voile(P, champ & (Y < 50), NE4, np.clip((50.0 - Y) / 8.0, 0, 0.85))     # le loin se perd dans le blanc
    # ---- La faille bleue et son pont de neige (« ça a fait un bruit de biscotte »).
    def bord_haut(x):
        x = _a(x)
        return 55.0 + 0.03 * (x - 108) + 0.9 * np.sin(x / 9.0) + 0.4 * np.sin(x / 3.1)

    ouv = lambda x: np.clip(5.2 * np.sin(np.clip((_a(x) - 56) / 108.0, 0, 1) * math.pi) ** 0.7, 0, None)
    ouv0 = ouv
    ouv = lambda x: ouv0(x) * (0.55 + 0.9 * pg.fbm(_a(x) / 6.0, _a(x) * 0 + 0.5, 2, 995)) + 0.25 * np.sin(_a(x) * 1.3)
    bh = bord_haut(X)
    faille = (Y > bh) & (Y < bh + ouv(X)) & (X > 58) & (X < 162)
    t = (Y - bh) / np.maximum(ouv(X), 0.3)
    P.rampe(faille, 1.0 - 1.05 * t + 0.18 * (pg.fbm(X / 1.4, Y / 4.0, 2, 978) - 0.5), [NU1, NU2, GL1, GL2, GL3], 0.45)
    P.remplir(faille & (np.abs(np.sin(X * 1.7 + 3 * np.sin(Y))) > 0.97) & (t < 0.6), GL3)   # le grain de la glace
    levre = (Y > bh + ouv(X) - 0.5) & (Y < bh + ouv(X) + 0.5) & (X > 60) & (X < 160)
    P.remplir(levre, NE4)
    P.remplir(P.crete(faille), SH1)
    for i in range(26):                                               # les glaçons sous la lèvre de devant
        x = 62.0 + i * 3.8 + 1.2 * hz(i, 1, 979)
        if 98 < x < 114:
            continue
        y = float(bord_haut(x) + ouv(x)) - 0.3
        l = 0.6 + 2.6 * hz(i, 2, 979) * float(ouv(x)) / 5.2
        P.trait(x, y - l, x, y, GL2)
        P.point(x, y - l, GL3)
    for i in range(3):                                                # ça goutte, au fond
        x = 76.0 + 30 * i
        tt = (p + i / 3.0) % 1.0
        P.point(x + 0.3, float(bord_haut(x)) + 0.8 + 2.2 * tt, GL3 if tt < 0.8 else NU2)
    pxb = 106.0                                                       # le pont : une arche mince, son ombre dessous
    ep_ = 1.6 + 0.04 * (X - pxb) ** 2
    arche = (np.abs(X - pxb) < 7.0) & (Y > bh - 0.8) & (Y < bh + ep_)
    P.rampe(arche, 0.9 - 0.35 * (X - pxb) / 7.0, NEIGE_L, 0.45)
    P.remplir(arche & (Y > bh + ep_ - 0.45), SH0)
    sous = (np.abs(X - pxb) < 7.0) & (Y >= bh + ep_) & (Y < bh + ep_ + 1.2) & faille
    P.remplir(sous, NU1)
    P.remplir(P.crete(arche), CREME)
    for i in range(4):                                                # les fissures de la biscotte
        x = pxb - 3.0 + 2.0 * i
        P.trait(x, float(bord_haut(x)) - 0.2, x + 0.5, float(bord_haut(x)) + 0.8, SH1)
    # ---- Les rochers qui percent, et la file des six cairns : nette devant, effacée au loin.
    for (x, y, r, g) in ((150.0, 49.0, 4.2, 980), (60.0, 47.2, 3.0, 981), (168.0, 52.0, 2.4, 982), (44.0, 50.0, 2.0, 983),
                         (84.0, 64.0, 2.4, 984), (136.0, 62.0, 1.6, 985)):
        rocher_neige(P, x, y, r, g)
    cairns = ((126.0, 72.5, 1.45), (117.0, 64.6, 1.05), (101.0, 52.4, 0.78), (95.0, 47.4, 0.58), (98.0, 43.6, 0.44),
              (101.0, 40.9, 0.32))
    for i, (x, y, k) in enumerate(cairns):
        ombre_portee(P, x + 1.4 * k, y + 0.2, 6.0 * k, 0.9 * k)
        cairn(P, x, y, k)
        if i >= 2:
            voile(P, np.hypot((X - x) / 1.6, Y - y + 4.5 * k) < 7.0 * k, NE4, 0.2 + 0.17 * (i - 2))
    # Les traces d'un lièvre, en Y, qui coupent vers la droite.
    for i in range(6):
        x, y = 132.0 + i * 5.6, 58.0 + i * 1.8
        for (dx, dy) in ((0.0, 0.0), (0.6, 0.9), (2.0, -0.3), (2.0, 0.6)):
            P.point(x + dx, y + dy, SH1)
    # Le lièvre variable, blanc sur blanc : deux yeux, le bout des oreilles ; il cligne.
    lx, ly = 140.0, 56.2
    P.ell(lx, ly, 2.0, 1.3, NE4)
    ombre_portee(P, lx + 1.0, ly + 1.2, 2.4, 0.4, 0.4)
    if (p * 8) % 8 >= 1:
        P.point(lx + 0.9, ly - 0.4, ENCRE)
    P.trait(lx + 0.2, ly - 1.4, lx - 0.4, ly - 3.2 - 0.3 * onde(p), NE4, P.ep(0.4))
    P.point(lx - 0.4, ly - 3.2 - 0.3 * onde(p), ENCRE)
    P.trait(lx + 0.9, ly - 1.4, lx + 0.9, ly - 3.0, NE4, P.ep(0.4))
    P.point(lx + 0.9, ly - 3.0, ENCRE)
    # Des chocards : deux qui jouent dans le vent, un perché sur le deuxième cairn.
    for i in range(2):
        tt = (p + i / 2.0) % 1.0
        x, y = 120 + 28 * i + 16 * math.sin(tt * 6.283), 16 + 6 * i + 4 * math.cos(tt * 6.283)
        a = onde(p * 2, 0.3 * i)
        P.trait(x - 1.8, y - 0.9 * a, x, y, ENCRE)
        P.trait(x, y, x + 1.8, y - 0.9 * a, ENCRE)
        P.point(x + 0.4, y + 0.2, PJ3)
    cx, cy = cairns[1][0], cairns[1][1] - 10.4 * cairns[1][2]
    P.ell(cx, cy, 1.1, 0.8, ENCRE)
    P.ell(cx + 0.9, cy - 0.7, 0.55, 0.55, ENCRE)
    P.point(cx + 1.6, cy - 0.6, PJ3)
    P.point(cx - 0.3, cy + 1.0, LA1)
    # La poudreuse que le vent fait courir au ras de la neige, et les paillettes du givre qui s'allument.
    for i in range(10):
        tt = (p + i / 10.0) % 1.0
        y = 46.0 + 3.0 * i
        x0 = -10 + 220 * tt + 13 * i % 60
        voile(P, champ & (np.abs(Y - y - 0.6 * np.sin(X / 5.0)) < 0.35 + 0.25 * tt) & (X > x0) & (X < x0 + 12 + i),
              NE4, 0.8 - 0.5 * tt)
    for i in range(90):
        x, y = -4 + 200 * hz(i, 1, 986), 44 + 36 * hz(i, 2, 986) ** 0.7
        if (p + hz(i, 3, 986)) % 1.0 < 0.22:
            P.point(x, y, BLANC)
            if hz(i, 4, 986) < 0.3:
                for (dx, dy) in ((0.4, 0), (-0.4, 0), (0, 0.4), (0, -0.4)):
                    P.point(x + dx, y + dy, OR_N)
    tab.plan("premier", 1.0)
    # ---- Premier plan : la congère où l'on marche, des herbes sèches givrées, un gros bloc à gauche, le grand cairn
    # balisé à droite (son ruban orange claque), la neige qui tombe encore, plus grosse près de nous.
    f_sol = lambda x: 76.6 + 1.0 * np.sin(_a(x) / 9.0) + 0.6 * np.sin(_a(x) / 3.3) - 3.0 * np.exp(-((_a(x) - 196) / 12.0) ** 2)
    m = Y > f_sol(X)
    P.rampe(m, 0.72 + 2.5 * (relief(X + 0.8, Y * 2) - relief(X - 0.8, Y * 2)) + 0.12 * (Y - 77), NEIGE_L, 0.45)
    P.remplir(P.crete(m), CREME)
    touffes_ = ((50.0, 5), (57.5, 3), (79.0, 4), (96.0, 6), (101.0, 2), (131.0, 4), (178.5, 3), (14.0, 2))
    for i, (x0, n) in enumerate(touffes_):                            # herbes sèches qui percent, givrées
        for j in range(n):
            x = x0 + (j - n / 2.0) * 0.7 + 0.4 * hz(i * 7 + j, 1, 987)
            y = float(f_sol(x)) + 0.6
            h = 1.6 + 4.2 * hz(i * 7 + j, 2, 987) * (1 - abs(j - n / 2.0) / n)
            b = 0.5 * onde(p, 0.07 * i) * h / 5.0
            tip = x + b + (j - n / 2.0) * 0.35
            P.trait(x, y, tip, y - h, PJ2 if j % 2 else PJ1)
            P.point(tip, y - h, NE4)
            if h > 4 and j % 2 == 0:
                P.point(tip - 0.2, y - h + 1.0, PJ3)
    # Le gros bloc de gauche : une boule d'ardoise fendue, chapeau de neige épais, quelques glaçons ; il cadre sans
    # toucher la place de Pilou.
    bloc = np.zeros(X.shape, dtype=bool)
    nb = np.zeros(X.shape)
    for (bx, by, r) in ((-2.0, 68.0, 11.5), (6.5, 75.0, 5.5), (-5.0, 53.0, 7.5)):
        dd = np.hypot(X - bx, (Y - by) * 1.1) / r
        m_ = dd < 1 + 0.06 * (pg.fbm(X / 1.5, Y / 1.5, 2, 988) - 0.5)
        nb = np.where(m_ & ~bloc, (X - bx) / r, nb)
        bloc |= m_
    vb = 0.7 - 0.7 * nb - 0.006 * (Y - 40) + 0.3 * (pg.fbm(X / 1.4, Y / 2.6, 3, 988) - 0.5)
    P.rampe(bloc, vb, [NU2, R1, R2, R3, R4], 0.45)
    P.remplir(bloc & (np.abs(np.sin(Y / 2.1 + X * 0.5)) > 0.97) & (nb > -0.2), NU1)      # les feuillets de l'ardoise
    P.remplir(bloc & (np.abs(X - 3.0 - 0.3 * (Y - 58)) < 0.3) & (Y > 58) & (Y < 72), ENCRE)  # la fente
    chap = bloc & (Y < 49.0 + 2.0 * np.cos((X + 4) / 5.0) + 0.8 * np.sin(X * 2.3))
    chap |= bloc & (Y < 61.0 + 0.6 * np.sin(X * 1.7) - 0.25 * X) & (Y > 55.4)
    chap |= bloc & (Y < 71.5 + 0.5 * np.sin(X * 1.9)) & (Y > 69.0) & (X > 2)
    P.rampe(chap, 0.95 - 0.06 * (X + 4) - 0.04 * (Y - 40), NEIGE_L, 0.45)
    P.remplir(P.crete(chap), CREME)
    for i, (x, l) in enumerate(((5.6, 2.8), (7.0, 1.4), (8.4, 3.6), (9.6, 1.0))):
        y0 = 58.8 + 0.4 * math.sin(x)
        P.trait(x, y0, x, y0 + l, GL2)
        P.point(x, y0 + l, GL3)
    tt = p % 1.0
    if tt < 0.9:
        P.point(8.4, 63.0 + 14 * tt, GL2)
    # Les pas de Pilou dans la neige fraîche, du bord jusqu'à sa place (« la neige crisse »).
    for i in range(6):
        x, y = 11.0 + i * 3.4, 79.2 - i * 0.5
        P.ell(x, y + (0.4 if i % 2 else 0.0), 1.0, 0.42, SH1)
        P.ell(x - 0.2, y - 0.15 + (0.4 if i % 2 else 0.0), 0.6, 0.18, SH0)
    # Le grand cairn de balisage, à droite, et son ruban.
    ombre_portee(P, 186.0, 80.0, 9.0, 1.4, 0.5)
    cairn(P, 187.0, 80.4, 2.3)
    v = onde(p)
    P.trait(187.6, 58.0, 187.6, 55.0, BO2, P.ep(0.4))
    P.poly([(187.6, 55.2), (192.0, 54.2 + 0.9 * v), (196.0, 55.8 - 0.9 * v), (192.0, 57.0 + 0.6 * v)], LA1)
    P.trait(187.6, 55.2, 192.0, 54.2 + 0.9 * v, LA2)
    # La neige qui tombe : petite au loin (dans ce plan, déjà), grosse tout près.
    for i in range(70):
        tt = (p + hz(i, 1, 990)) % 1.0
        x = -6 + 204 * hz(i, 2, 990) + 2.4 * math.sin(tt * 6.283 + i)
        y = -16 + 98 * ((hz(i, 3, 990) + tt) % 1.0)
        gros = hz(i, 4, 990) < 0.25
        if 12 < x < 50 and 28 < y < 74 and gros:
            continue
        P.point(x, y, NE4 if y > 20 or not gros else NE3, 2 if gros else 1)


# =====================================================================================================================
# Le Trou-qui-Siffle (chapitre 8) : « Devant, la galerie est droite, avec des creux de chaque côté, tous les vingt pas.
# […] Il y a neuf creux. » Une galerie en perspective, droite, qui file vers une ouverture de jour pâle ; les parois
# polies par le vent (stries qui fuient vers le fond), les neuf creux de chaque côté, le plafond où pendent les
# Froisseuses, la poussière que le vent pousse vers nous. La seule lumière vient du fond : elle mouille le sol, dessine
# l'arête des creux et le bord des pierres ; près de nous, tout retombe dans le bleu nuit.
# =====================================================================================================================
FX, FY = 146.0, 33.0            # le point de fuite : l'ouverture, tout au fond
RG, AG = 64.0, 2.6              # le rayon de la galerie (à la profondeur 1) et son ovale (plus large que haute)
NS = 4.0                        # la forme de sa section : un ovale aplati (une superellipse), le sol bien à plat
HS = 44.0                       # le sol, sous l'axe (à la profondeur 1 : y = 77)
ZF = 7.5                        # la profondeur de l'ouverture
CREUX = [1.45 + 0.66 * k for k in range(9)]        # les neuf creux, de chaque côté
SIF1, SIF2, SIF3 = cs("#2a3350", "#46557a", "#9fb4d4")


def galerie_proj(u, w, z):
    """Un point de la galerie (u : de côté, w : vers le bas, à l'échelle de la profondeur 1 ; z : profondeur) → l'écran."""
    return FX + u / z, FY + w / z


def paroi_u(w):
    """Le côté de la paroi à la hauteur w (profondeur 1)."""
    return AG * max(RG ** NS - abs(w) ** NS, 1.0) ** (1.0 / NS)


def paroi_th(th):
    """Le point de la paroi dans la direction th (profondeur 1)."""
    c, s_ = math.cos(th), math.sin(th)
    r = RG / (abs(c) ** NS + abs(s_) ** NS) ** (1.0 / NS)
    return AG * r * c, r * s_


def eclairage(z):
    """La lumière du fond, qui ne porte pas loin : 1 à l'ouverture, presque rien près de nous."""
    return 0.16 + 0.84 * np.exp(-(ZF - np.minimum(z, ZF)) / 3.4)


@decor("petit-nuage", "trou-qui-siffle", soleil=(FX, FY), tons=NUIT, nom="Le Trou-qui-Siffle", matiere=True)
def trou_qui_siffle(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    dx, dy = X - FX, Y - FY
    rho = (np.abs(dx / AG) ** NS + np.abs(dy) ** NS) ** (1.0 / NS) + 1e-6
    zm = RG / rho                                                    # la paroi
    zs = np.where(dy > 0.05, HS / np.maximum(dy, 0.05), 1e9)        # le sol
    sol = zs < zm
    z = np.where(sol, zs, zm)
    u, w = dx * z, dy * z
    fond = z > ZF
    tab.plan("fond", 0.0)
    # ---- L'ouverture, tout au fond : le jour blanc, une pente de neige, la pointe d'une Dent ; il entre des flocons.
    P.rampe(np.ones(X.shape, dtype=bool), 1.0 - np.hypot(dx / 2.0, dy) / (RG / ZF) * 0.5, [NE1, NE2, NE3, NE4, BLANC], 0.5)
    pente = (Y > FY + 1.2 - 0.25 * (X - FX)) & fond
    P.rampe(pente, 0.75 + 0.2 * (pg.fbm(X / 1.5, Y / 0.8, 2, 940) - 0.5), [NE2, NE3, NE4], 0.5)
    P.remplir((Y > FY - 3.2 + 0.9 * np.abs(X - FX + 1.4)) & (Y < FY - 0.4) & (X > FX - 4) & (X < FX + 1.2), NE1)
    tab.plan("galerie", 0.2)
    # ---- Les parois : roche polie en stries qui fuient vers le fond, des anneaux de roche plus durs tous les quelques
    # pas ; la lumière n'arrive que du fond.
    th = np.arctan2(dy, dx / AG)
    paroi = ~sol & ~fond
    sa = th * RG                                                     # l'abscisse le long de la paroi
    stries = pg.fbm(sa / 4.0, z * 0.7, 3, 941) + 0.5 * pg.fbm(sa / 1.1, z * 2.2, 2, 942)
    anneaux = 0.5 + 0.5 * np.sin(z * 7.5 + 2.0 * pg.fbm(sa / 9.0, z, 2, 943))
    lum = eclairage(z)
    bosses = pg.fbm(sa / 18.0, z * 0.8, 2, 955)
    relief_ = pg.fbm(sa / 18.0, (z + 0.12) * 0.8, 2, 955) - bosses           # > 0 : la bosse regarde le fond, la lueur
    v = 0.1 + 0.74 * lum + (0.14 + 0.2 * lum) * (stries - 0.75) + 0.06 * anneaux * lum + 0.12 * (bosses - 0.5) + (
        0.8 + 1.6 * lum) * relief_ + 0.05 * (pg.fbm(X / 1.2, Y / 1.2, 2, 944) - 0.5)
    P.rampe(paroi, v, [ENCRE, NU1, SIF1, NU2, R1, SIF2, R2, R3, R4, SIF3], 0.5)
    arete_ = paroi & (anneaux > 0.975) & (lum > 0.42)
    P.remplir(arete_, R4)                                            # l'arête des anneaux, qui prend la lueur
    mica = paroi & (hz(P.XI, P.YI, 945) > 0.9975) & (lum > 0.3)
    P.remplir(mica & ((P.p * 8 + (X * 7).astype(int) % 8) % 8 < 3), NE3)          # le mica qui s'allume
    coulures = paroi & (pg.fbm(sa / 1.6, w / 30.0 + z * 0.3, 3, 957) > 0.62) & (w > -20)      # l'humidité qui coule
    voile(P, coulures, NU1, 0.45)
    P.remplir(coulures & ~np.roll(coulures, 1, axis=1) & (lum > 0.22), SIF2)
    # ---- Le sol : du sable que le vent a ridé, une rigole d'eau qui renvoie la lueur, des cailloux.
    sable = sol & ~fond
    rides = np.sin(z * 4.2 + 1.6 * np.sin(u / 9.0) + 2.0 * pg.fbm(u / 12.0, z, 2, 946)) * np.clip(1.6 - z / 4.0, 0.2, 1)
    vs = 0.08 + 0.75 * eclairage(z) + (0.1 + 0.1 * eclairage(z)) * rides + 0.12 * (pg.fbm(u / 4.0, z * 7.0, 2, 947) - 0.5)
    P.rampe(sable, vs, [ENCRE, NU1, SIF1, NU2, R1, SIF2, R2, R3, TE3], 0.5)
    rigole = sable & (np.abs(u - 14.0 - 6.0 * np.sin(z * 0.7)) < 2.6) & (z > 1.5)
    P.rampe(rigole, eclairage(z) * 1.05 + 0.1 * np.sin(z * 20.0 + p * 6.283), [NU1, NU2, SIF2, SIF3, NE3, NE4], 0.5)
    for i in range(30):                                              # des cailloux, leur bord éclairé côté fond
        zz = 1.1 + 6.2 * hz(i, 1, 948) ** 1.3
        uu = -64.0 + 128.0 * hz(i, 2, 948)
        if abs(uu) > 60.0:
            continue
        x, y = galerie_proj(uu, HS, zz)
        r = (2.4 + 3.0 * hz(i, 3, 948)) / zz
        ombre = (np.abs((X - x) - (Y - y) * (x - FX) / max(y - FY, 1.0)) < r * 0.8) & (Y > y) & (Y < y + r * 2.4) & sol
        voile(P, ombre, ENCRE, 0.5)                                   # son ombre, qui vient vers nous
        P.ell(x, y - r * 0.4, r, r * 0.55, NU1 if zz < 3 else R1)
        P.ell(x + r * 0.25 * np.sign(FX - x), y - r * 0.7, r * 0.55, r * 0.2, R3 if zz > 3 else SIF2)
    gravier = sable & (hz(P.XI, P.YI, 958) > 0.985)
    P.remplir(gravier & (z < 3), SIF2)
    P.remplir(gravier & (z >= 3), R3)
    # ---- Les neuf creux, de chaque côté : des niches en ogive ; leur paroi du fond, qui nous regarde, prend la lueur.
    for cote in (-1, 1):
        for k, zc in enumerate(CREUX):
            prof_ = 0.2
            dedans = paroi & (np.sign(u) == cote) & (z > zc) & (z < zc + prof_)
            haut_ = 6.0 + 5.0 * np.sqrt(np.clip(1 - ((z - zc - prof_ / 2) / (prof_ / 2)) ** 2, 0, 1))
            haut_ = haut_ + 12.0
            niche = dedans & (w > haut_) & (w < HS - 1.0)
            P.rampe(niche, 0.25 + 0.5 * eclairage(z) + 0.1 * (pg.fbm(X / 1.5, Y / 1.5, 2, 954) - 0.5), [ENCRE, NU1, SIF1], 0.5)
            P.rampe(niche & (z > zc + prof_ * 0.6), eclairage(zc) * 1.4, [NU1, SIF1, NU2, R1, R2], 0.5)
            bord = paroi & (np.sign(u) == cote) & (np.abs(z - zc - prof_) < 0.02 * zc) & (w > haut_) & (w < HS - 1)
            P.remplir(bord & (eclairage(z) > 0.2), R4 if k > 3 else R3)
            seuil_ = dedans & (np.abs(w - HS + 1.0) < 0.9) & (z > zc + 0.05)
            P.remplir(seuil_, R2 if k > 2 else SIF1)
    # Ce qu'on a laissé dans les premiers creux (de part et d'autre, près de nous).
    def dans_creux(cote, k, du=0.0):
        zc = CREUX[k] + 0.25
        return galerie_proj(cote * (paroi_u(HS - 2.0) + 2.0 + du), HS - 1.2, zc), 1.0 / zc

    (x, y), e = dans_creux(-1, 0)                                    # un nid de chocard, trois œufs
    P.ell(x, y - 2.0 * e, 7.0 * e, 2.6 * e, BO2)
    P.ell(x, y - 2.8 * e, 5.0 * e, 1.4 * e, BO1)
    for q in range(3):
        P.ell(x - 2.4 * e + q * 2.4 * e, y - 4.0 * e, 1.3 * e, 1.6 * e, NE3)
    (x, y), e = dans_creux(1, 0)                                     # des tuyaux de pierre : ce sont eux qui sifflent
    for q in range(5):
        hh = (10.0 + q * 5.0) * e
        P.rect(x - 9.0 * e + q * 3.6 * e, y - hh, 2.8 * e, hh, R2)
        P.rect(x - 9.0 * e + q * 3.6 * e, y - hh, 0.9 * e, hh, R4)
        P.rect(x - 9.0 * e + q * 3.6 * e, y - hh + 2.0 * e, 2.8 * e, 0.9 * e, ENCRE)
    pg.vapeur(P, x + 1.0 * e, y - 32.0 * e, coul=SIF3, h=8.0 * e * 2, d=0.2)
    (x, y), e = dans_creux(-1, 1)                                    # un bonnet orange oublié, son pompon
    P.ell(x, y - 2.6 * e, 4.0 * e, 3.0 * e, LA1, cond=Y < y - 0.2)
    P.ell(x - 0.8 * e, y - 3.4 * e, 2.0 * e, 1.2 * e, LA2)
    P.ell(x + 2.4 * e, y - 5.8 * e, 1.4 * e, 1.4 * e, CREME)
    (x, y), e = dans_creux(1, 2)                                     # un bocal de lueur, qui tient bon
    bocal(P, x, y, 7.0 * e, 10.0 * e, LA3, graine=7, lueur=True)
    # ---- La corde-main courante, le long de la paroi gauche, accrochée à des pitons ; elle fuit vers le fond.
    prec = None
    for i in range(12):
        zz = 1.0 + i * 0.55
        uu = -paroi_u(24.0) + 1.0
        xa, ya = galerie_proj(uu, 24.0, zz)
        if prec is not None:
            xm, ym = (prec[0] + xa) / 2, (prec[1] + ya) / 2 + 2.6 / zz + 0.3 * onde(p, 0.1 * i) / zz
            P.courbe([prec, (xm, ym), (xa, ya)], TE2 if zz < 3 else TE1, P.ep(0.9 / zz) if zz < 2 else 1)
        P.point(xa, ya, R4 if zz > 3 else SIF2, max(1, int(2.0 / zz)))
        prec = (xa, ya)
    # ---- Le plafond : les Froisseuses, pendues par centaines ; quelques-unes se grattent, une ouvre l'aile.
    for i in range(170):
        zz = 1.6 + 5.8 * hz(i, 1, 949)
        th_ = -math.pi / 2 + (hz(i, 2, 949) - 0.5) * 1.1
        uu, ww = [q * 0.985 for q in paroi_th(th_)]
        x, y = galerie_proj(uu, ww, zz)
        if y < -16 or y > FY - 2:
            continue
        r = 2.0 / zz
        coul = NU1 if zz < 4 else SIF1
        P.ell(x, y + r * 1.3, r * 0.75, r * 1.3, coul)
        P.point(x + np.sign(FX - x) * r * 0.5, y + r * 1.0, SIF2 if zz < 4 else SIF3)
        if (p + hz(i, 3, 949)) % 1.0 < 0.08:
            P.trait(x - r * 2.0, y + r * 0.6, x + r * 2.0, y + r * 0.6, coul)          # une aile qui s'ouvre
        elif zz < 5 and hz(i, 4, 949) < 0.25 and (p + hz(i, 5, 949)) % 1.0 > 0.2:
            P.point(x - r * 0.3, y + r * 1.9, LA2)                                     # deux yeux qui brillent
            P.point(x + r * 0.3, y + r * 1.9, LA2)
    # Les gouttes du plafond, et leur rond dans la rigole.
    for i, zz in enumerate((2.4, 4.0, 5.8)):
        x0, y0 = galerie_proj(14.0 + 6.0 * math.sin(zz * 0.7), -RG * 0.9, zz)
        x1, y1 = galerie_proj(14.0 + 6.0 * math.sin(zz * 0.7), HS, zz)
        tt = (p + i / 3.0) % 1.0
        if tt < 0.6:
            P.point(x0, y0 + (y1 - y0) * (tt / 0.6) ** 2, SIF3)
        else:
            rr = (tt - 0.6) * 10.0 / zz
            P.remplir((np.abs(np.hypot((X - x1) / 2.4, Y - y1) - rr) < 0.25) & sol, NE3)
    tab.plan("vent", 0.5)
    # ---- Le vent : la poussière vient du fond vers nous, en traînées de plus en plus longues ; des feuilles, une plume.
    for i in range(90):
        tt = (p + hz(i, 1, 950)) % 1.0
        th_ = 2 * math.pi * hz(i, 2, 950)
        rr = 0.35 + 0.6 * hz(i, 3, 950)
        uu, ww = AG * RG * rr * math.cos(th_) * 0.8, min(RG * rr * math.sin(th_), HS - 3.0)
        zz = ZF * (1 - tt) + 0.6
        xa, ya = galerie_proj(uu, ww, zz)
        xb, yb = galerie_proj(uu, ww, zz + 0.35 + 0.4 * tt)
        if -10 < xa < 202 and -18 < ya < 82:
            P.trait(xb, yb, xa, ya, SIF3 if zz > 8 else (SIF2 if zz > 4 else NU2))
    for i in range(6):
        tt = (p + i / 6.0) % 1.0
        zz = ZF * (1 - tt) + 0.7
        uu, ww = (i - 2.5) * 14.0, 10.0 + 22.0 * math.sin(i * 1.7 + tt * 9)
        x, y = galerie_proj(uu, ww, zz)
        e = 1.4 / zz
        if i == 3:
            P.courbe([(x, y), (x + 3 * e, y - e), (x + 6 * e, y)], NE3, 1)
        else:
            P.ell(x, y, 1.6 * e + 0.3, 0.8 * e + 0.3, PJ2 if i % 2 else ME2)
    tab.plan("premier", 1.0)
    # ---- Premier plan : le bord de la galerie, tout près, noir, sa tranche qui prend la lueur ; des éboulis ; une
    # toile d'araignée tendue dans le coin, perlée de poussière.
    arche = (Y < -12.0 + 0.0042 * (X - 100.0) ** 2 + 1.2 * np.sin(X / 4.3) + 0.6 * np.sin(X / 1.7)) | (X < 4.0 + 2.0 * np.sin(Y / 6.0) - 0.04 * (Y - 30))
    va = 0.2 + 0.2 * (pg.fbm(X / 2.0, Y / 2.0, 3, 951) - 0.5) + 0.1 * np.sin(X / 3.0 + Y / 5.0)
    P.rampe(arche, va, [ENCRE, NU1, SIF1], 0.5)
    tranche = arche & ~np.roll(arche, -2, axis=0) & (X > 6)                  # sa tranche, qui prend la lueur
    P.remplir(tranche, SIF2)
    P.remplir(tranche & (np.abs(X - FX) < 50) & (P.T < 0.6), SIF3)
    for i in range(9):                                                # des racines fines qui pendent de l'arche
        x = 30.0 + i * 15.5 + 4 * hz(i, 1, 956)
        y0 = -12.0 + 0.0042 * (x - 100.0) ** 2
        if y0 > 14:
            continue
        l = 3.0 + 6.0 * hz(i, 2, 956)
        b_ = 0.4 * onde(p, 0.13 * i)
        P.courbe([(x, y0 - 0.5), (x + 0.3 + b_ * 0.5, y0 + l * 0.5), (x + b_, y0 + l)], NU1, 1)
        P.point(x + b_, y0 + l, SIF2)
    for (x, y, r) in ((4.0, 80.0, 6.0), (11.0, 81.0, 3.4), (186.0, 81.0, 7.0), (176.0, 81.6, 3.0), (66.0, 81.6, 2.6),
                      (140.0, 82.0, 3.2)):
        mm = P.ell(x, y, r, r * 0.6, NU1, cond=Y < 80.0)
        P.rampe(mm, 0.25 + 0.35 * np.clip(-(np.hypot(X - x - r * 0.3, Y - y + r * 0.5)) / r + 1, 0, 1), [ENCRE, NU1, SIF1, NU2], 0.5)
        P.remplir(P.crete(mm) & (X > x - r * 0.2), SIF2)
    cx, cy = 176.0, -16.0                                            # la toile, dans le coin de droite
    for a in range(6):
        ang = math.pi * (0.5 + a / 10.0)
        P.trait(cx, cy, cx + 14 * math.cos(ang), cy + 14 * math.sin(ang), SIF1)
    for r in (4.0, 7.5, 11.0):
        pts = [(cx + r * math.cos(math.pi * (0.5 + a / 10.0)), cy + r * math.sin(math.pi * (0.5 + a / 10.0)) + 0.6)
               for a in range(6)]
        P.courbe(pts, SIF1, 1)
    sx, sy = cx - 4.0, cy + 9.0 + 0.6 * onde(p)
    P.ell(sx, sy, 0.8, 0.8, ENCRE)
    for q in range(4):
        P.point(cx + 7.5 * math.cos(math.pi * (0.55 + q / 9.0)), cy + 7.5 * math.sin(math.pi * (0.55 + q / 9.0)) + 0.6,
                SIF3 if (p * 4 + q) % 4 < 2 else SIF2)
    voile(P, Y > 79.0, ENCRE, 0.5)


# =====================================================================================================================
# La Grande Salle (chapitre 9) : « D'un coup, plus de murs. La Grande Salle. Je ne vois pas le plafond. Je ne vois pas
# le fond. Je vois juste, au milieu, de la poussière qui file à l'horizontale, d'un trait, sans un bruit. » Une caverne
# immense : des piliers de roche en couches de plus en plus pâles vers le fond, un puits de jour qui tombe de très haut,
# le fleuve de vent que la poussière dessine, ses remous ; la corniche où l'on passe, sa corde ; le gros rocher ; les
# Froisseuses en grappes au plafond.
# =====================================================================================================================
@decor("petit-nuage", "grande-salle", soleil=(132.0, -30.0), tons=NUIT, nom="La Grande Salle", matiere=True)
def grande_salle(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    PX_ = 132.0                                                       # le puits de jour
    tab.plan("fond", 0.0)
    # ---- Le fond, qu'on ne voit pas : un noir bleu, un peu plus clair autour du puits de jour.
    d = np.hypot((X - PX_) / 1.6, Y - 30.0)
    P.rampe(np.ones(X.shape, dtype=bool), 0.62 - d / 120.0 + 0.3 * (pg.fbm(X / 6.0, Y / 6.0, 3, 1330) - 0.5) + 0.12 * (pg.fbm(X / 1.5, Y / 1.5, 2, 1341) - 0.5), [ENCRE, NU1, NU2, T.CIEL[3], T.CIEL[4]], 0.5)
    for c, (prof_, n, tons_) in enumerate(((0.25, 9, [NU2, T.CIEL[3], T.CIEL[4], T.CIEL[5]]),
                                           (0.55, 7, [NU1, NU2, T.CIEL[3], T.CIEL[4]]),
                                           (0.9, 5, [ENCRE, NU1, NU2, T.CIEL[3]]))):
        for i in range(n):                                            # les piliers : stalactite et stalagmite soudées
            x = -10 + 212 * (i + 0.5 + 0.3 * (hz(i, c, 1331) - 0.5)) / n
            w = (2.0 + 3.0 * hz(i, c + 3, 1331)) * (0.6 + 1.2 * prof_)
            taille = np.clip(1 - np.abs(Y - 30.0) / 46.0, 0, 1)
            xc = x + 0.5 * np.sin(Y / 9.0 + i)
            demi = w * (0.4 + 0.9 * (1 - taille) ** 1.6) * (1 + 0.12 * (pg.fbm(X * 0, Y / 2.0, 2, 1342 + i) - 0.5))
            m = np.abs(X - xc) < demi
            lum = np.clip(1 - np.abs(X - PX_) / 60.0, 0, 1)
            cote_ = (X - xc) / np.maximum(demi, 0.1) * np.sign(x - PX_)
            v = 0.35 + 0.3 * cote_ * (0.3 + lum) + 0.2 * (pg.fbm(X / 1.2, Y / 4.0, 2, 1332 + i) - 0.5)
            P.rampe(m, v, tons_, 0.5)
            coulee = m & (np.abs(np.sin((X - xc) * 2.4 + 2.0 * pg.fbm(X / 2.0, Y / 9.0, 2, 1343 + i))) > 0.93)   # la calcite qui coule
            P.remplir(coulee, tons_[min(3, 1 + int(lum.mean() > 0))])
            P.remplir(m & (np.abs(np.abs(X - xc) - demi) < 0.35) & (cote_ > 0) & (lum > 0.2), tons_[3])
        if c == 0:
            pg.rai(P, PX_, -16.0, 62.0, 10.0, -0.12, T.CIEL[8], force=0.4, grains=24, graine=1333)
            voile(P, (np.abs(X - PX_ + 0.12 * (Y + 16)) < 4.0) & (Y > 52) & (Y < 60), T.CIEL[9], 0.4, lumiere=True)
    gouttes_ = (hz(P.XI // 2, P.YI // 3, 1344) > 0.985)
    P.remplir(gouttes_ & (P.a == NU1), NU2)
    P.remplir(gouttes_ & (P.a == ENCRE), NU1)
    tab.plan("vent", 0.3)
    # ---- Le fleuve de vent : la poussière qui file d'un trait, vers la droite ; des remous qui tournent ; un bord de
    # nuage (de Brouillon ?) emporté.
    for i in range(160):
        t = (p + hz(i, 1, 1334)) % 1.0
        y = 26.0 + 28.0 * hz(i, 2, 1334) + 2.0 * math.sin((t * 6.283) + i)
        x = -20 + 240 * ((hz(i, 3, 1334) + t) % 1.0)
        l = 3.0 + 9.0 * hz(i, 4, 1334)
        coul = (T.CIEL[5], T.CIEL[6], T.CIEL[4], T.CIEL[8])[i % 4]
        P.trait(x, y, x + l, y + 0.4 * math.sin(i), coul)
    for k, (cx, cy, r) in enumerate(((52.0, 36.0, 5.0), (104.0, 46.0, 4.0), (160.0, 34.0, 6.0))):
        for j in range(18):                                           # un remous
            a = p * 6.283 * (1 if k % 2 else -1) + j * 0.35
            rr = r * (0.3 + 0.7 * j / 17.0)
            P.point(cx + rr * math.cos(a), cy + rr * 0.5 * math.sin(a), T.CIEL[7] if j % 3 else T.CIEL[9])
    t = p % 1.0
    for j in range(4):
        P.ell(-6 + 210 * t + j * 2.0, 40.0 + 0.6 * math.sin(j + t * 9), 1.2 - 0.2 * j, 0.7, NE3)
    tab.plan("moyen", 0.6)
    # ---- Le gros rocher (« un derrière un rocher »), des éboulis ; le plafond : les grappes de Froisseuses.
    rx_, ry_ = 92.0, 64.0
    mr = P.ell(rx_, ry_ - 6.0, 10.0, 8.0, NU1, cond=Y < ry_ + 0.2)
    P.rampe(mr, 0.45 + 0.4 * np.clip((PX_ - X) / -30.0, -0.5, 0.5) * -1 + 0.4 * (rx_ - X < 0) * 0 + 0.35 * (X - rx_) / 10.0
            - 0.3 * (Y - ry_ + 8) / 8 + 0.15 * (pg.fbm(X / 1.0, Y / 1.0, 2, 1335) - 0.5), [ENCRE, NU1, NU2, R1, R2], 0.45)
    P.remplir(P.crete(mr) & (X > rx_), T.CIEL[6])
    plafond = Y < -10.0 + 4.0 * np.sin(X / 13.0) + 2.0 * pg.fbm(X / 3.0, X * 0, 2, 1336)
    P.rampe(plafond, 0.3 + 0.2 * (pg.fbm(X / 2.0, Y / 2.0, 2, 1337) - 0.5), [ENCRE, NU1, NU2], 0.5)
    for g in range(6):                                                # les grappes de Froisseuses
        gx = 14.0 + g * 32.0 + 6 * hz(g, 1, 1338)
        for i in range(16):
            x = gx + (hz(i, 2, 1338 + g) - 0.5) * 12.0
            y = -10.0 + 4.0 * math.sin(x / 13.0) + 1.0 + hz(i, 3, 1338 + g) * 3.0
            P.ell(x, y + 1.2, 0.7, 1.3, NU1)
            P.point(x + 0.3, y + 1.0, NU2)
            if (p + hz(i, 4, 1338 + g)) % 1.0 < 0.06:
                P.trait(x - 1.6, y + 0.6, x + 1.6, y + 0.6, NU1)
    tab.plan("premier", 1.0)
    # ---- La corniche où l'on passe : une vire de roche le long de la paroi, sa tranche qui prend le jour, le vide
    # dessous ; la corde tendue sur ses piquets ; un petit cairn, un panier oublié, des champignons pâles.
    f_c = lambda x: 70.0 + 0.8 * np.sin(_a(x) / 11.0) + 0.4 * np.sin(_a(x) / 3.3)
    vire = (Y > f_c(X)) & (Y < 78.4 + 0.6 * np.sin(X / 5.0))
    P.rampe(vire, 0.5 + 0.25 * (pg.fbm(X / 2.0, Y / 0.8, 3, 1339) - 0.5) - 0.04 * (Y - 70) + 0.1 * np.clip(1 - np.abs(X - PX_) / 60, 0, 1),
            [ENCRE, NU1, NU2, R1, R2, R3], 0.45)
    P.remplir(P.crete(vire), T.CIEL[6])
    tranche = (Y >= 78.4 + 0.6 * np.sin(X / 5.0)) & (Y < 80.5)
    P.rampe(tranche, 0.35 + 0.2 * (pg.fbm(X / 1.0, Y, 2, 1340) - 0.5), [ENCRE, NU1, NU2], 0.5)
    P.remplir(np.abs(Y - 78.6 - 0.6 * np.sin(X / 5.0)) < 0.25, R3)
    prec = None
    for i in range(13):
        x = -2.0 + i * 16.5
        y = float(f_c(x)) + 0.3
        P.rect(x - 0.5, y - 7.0, 1.0, 7.0, BO1)
        P.rect(x - 0.5, y - 7.0, 0.4, 7.0, BO3)
        if prec:
            P.courbe([(prec[0], prec[1] - 6.0), ((prec[0] + x) / 2, (prec[1] + y) / 2 - 4.4 + 0.3 * onde(p, 0.1 * i)), (x, y - 6.0)], TE2, 1)
        prec = (x, y)
    cairn(P, 172.0, float(f_c(172.0)) + 0.4, 0.7, neige=False)
    for i in range(5):
        x = 60.0 + i * 1.4
        P.ell(x, float(f_c(x)) - 0.6, 0.6, 0.4, T.CIEL[8])
        P.trait(x, float(f_c(x)) - 0.4, x, float(f_c(x)) + 0.3, NE2)
    pg.yeux(P, 4.0, 40.0, coul=LA3, d=0.3)
    voile(P, Y > 79.0, ENCRE, 0.4)


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
    # Les deux Dents vues de l'autre versant (en miroir), et la couronne de sommets autour du lac : roche, névés, arêtes ;
    # le soir, la lumière dorée vient de la gauche ; à l'aube, la lumière rose vient de la droite.
    xs = np.arange(-6.0, 198.0, 0.25)
    fd = lambda x: np.minimum(dents(x, cx=92.0, k=1.15, base=43.0, miroir=True), pg.profil(x, 40.0, 16.0, 30.0, 981))
    fv = fd(xs)
    pics = [(float(xs[np.argmin(np.where(xs < 92, fv, 99))]), float(np.min(np.where(xs < 92, fv, 99)))),
            (float(xs[np.argmin(np.where(xs >= 92, fv, 99))]), float(np.min(np.where(xs >= 92, fv, 99))))]
    neige_l = [T.L4, NE2, NE3, NE4, CREME] if not aube else [T.L4, NE2, NE3, NE4, BLANC]
    massif(P, fd, pics, roches, neige_l, [T.L2, T.L3, T.L4, NE2], OR_N if not aube else T.CIEL[11], 1380,
           brume=(T.CIEL[9], 30.0, 14.0), droite=aube, selle=float(xs[np.argmax(np.where((xs > pics[0][0]) & (xs < pics[1][0]), fv, -99))]))
    for (sx, sy) in pics:                                              # le vent tire la neige des pointes
        u = (X - sx) / 16.0
        pan = (u > 0) & (u < 1) & (np.abs(Y - sy - 1.0 - 2.0 * u - 0.6 * np.sin(u * 7 + p * 6.283)) < 0.4 + 1.6 * u)
        voile(P, pan & (pg.fbm((X - 20 * p) / 2.4, Y / 1.2, 3, 1381) > 0.45 + 0.4 * u), NE4, 0.6 * (1 - u))
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
    # ---- Seconde passe : la vie de l'Abreuvoir.
    if aube:
        for i in range(5):                                      # les derniers du troupeau : ils boivent encore, puis décollent
            t = (p + i / 5.0) % 1.0
            petit_nuage(P, 40.0 + 26 * i, 60.0 - 6.0 * t, 9.0, 3.0, 1100 + i, boit=t < 0.3, tons=[T.CIEL[5], T.CIEL[7], T.CIEL[9], T.CIEL[11], BLANC])
        for i in range(8):                                      # leurs traces de givre sur l'eau
            P.ell(30.0 + i * 18.0, 58.0 + (i % 3) * 4.0, 3.0, 0.5, NE3)
        pg.vapeur(P, 104.0, 62.0, coul=T.CIEL[11], h=10.0, n=4)   # le rocher plat fume au premier soleil
        for i in range(3):                                      # des bouquetins descendent boire, au fond
            P.ell(150.0 + i * 5.0, 42.0, 1.4, 0.9, BO2)
            P.trait(150.6 + i * 5.0, 41.0, 151.6 + i * 5.0, 39.6, BO2)
    else:
        for i in range(6):                                      # ils boivent : de petits ronds devant chaque ventre
            pg.goutte(P, 30.0 + i * 26.0, 62.0 + (i % 3) * 3.0, 62.0 + (i % 3) * 3.0, coul=T.CIEL[10], d=i / 6.0, flaque=T.CIEL[10])
        t = (p + 0.5) % 1.0                                     # un petit nuage arrive en retard, de la droite
        petit_nuage(P, 196.0 - 40.0 * t, 30.0 + 14.0 * t, 8.0, 2.8, 1110, tons=[T.CIEL[5], T.CIEL[7], T.CIEL[9], T.CIEL[11], BLANC])
        for i in range(4):                                      # des marmottes sur la rive, dressées, qui regardent
            x = 62.0 + i * 5.0
            P.ell(x, 71.0, 1.1, 1.8, RO2)
            P.ell(x, 68.8, 0.9, 0.8, RO2)
        pg.papillon_de_nuit(P, 150.0, 66.0, 5.0, coul=CREME, d=0.3)
    # Une truite saute ; des éphémères dansent ; un canot retourné sur la rive.
    t = (p + 0.1) % 1.0
    if t < 0.25:
        P.courbe([(128.0, 62.0 - 10 * math.sin(t / 0.25 * math.pi)), (130.0, 61.0 - 10 * math.sin(t / 0.25 * math.pi)), (132.0, 62.4 - 10 * math.sin(t / 0.25 * math.pi))], NE3, P.ep(0.7))
    pg.goutte(P, 130.0, 62.0, 62.0, coul=NE4, d=0.75, flaque=NE4)
    for i in range(6):
        P.point(84.0 + i * 3.0 + onde(p, 0.2 * i), 64.0 + 2 * onde(p * 2, 0.3 * i), CREME)
    P.poly([(14.0, 72.0), (34.0, 71.0), (30.0, 74.0), (18.0, 74.6)], BO2)
    P.trait(14.0, 72.0, 34.0, 71.0, BO3)
    P.trait(20.0, 74.0, 24.0, 66.0, BO3)                          # sa pagaie, plantée
    P.ell(24.4, 65.0, 1.2, 2.0, BO3)
    cairn(P, 186.0, 62.0, 0.9, neige=aube)


@decor("petit-nuage", "abreuvoir", soleil=(60.0, 30.0), tons=SOIR, nom="L'Abreuvoir", matiere=True)
def abreuvoir(P, tab):
    _lac(P, tab, aube=False)


@decor("petit-nuage", "abreuvoir-aube", soleil=(150.0, 34.0), tons=ROSE, nom="L'Abreuvoir à l'aube", matiere=True)
def abreuvoir_aube(P, tab):
    _lac(P, tab, aube=True)


# =====================================================================================================================
# La fenêtre de la maison (chapitre 12) : « Le soir, je monte sur le rebord de ta fenêtre et je regarde passer les
# nuages. » Le rebord intérieur, le soir, à la lumière de la lampe : la vitre où la pluie coule et où la buée garde un
# dessin fait au doigt ; dehors, la rue, ses toits et ses fenêtres allumées, le ciel d'hiver où passent les nuages (un
# petit traîne derrière les autres), et tout au bout les deux Dents, minuscules ; sur le rebord, la casserole et sa bosse,
# le baluchon, une tasse qui fume, une plante.
# =====================================================================================================================
@decor("petit-nuage", "fenetre-maison", soleil=(8.0, 50.0), tons=NUIT, nom="La fenêtre de la maison", matiere=True)
def fenetre_maison(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    VX0, VX1, VY0, VY1 = 40.0, 168.0, -8.0, 66.0                      # la vitre
    tab.plan("dehors", 0.0)
    # ---- Dehors : le ciel du soir d'hiver, bleu nuit en haut, lavande au ras des toits ; les nuages qui passent.
    pg.ciel(P, horizon=44.0, haut=0.0, halo=0.12, etoiles=0.35, disque=0)
    pg.cumulus(P, [(70, 8, 30, 5.0, 1350, 7, 0.0), (130, 2, 24, 4.0, 1351, 6, 0.3), (172, 14, 34, 5.5, 1352, 8, 0.6)],
               dessous=0.5)
    pg.cumulus(P, [(46 + 1.0 * onde(p, 0.5), 20, 9, 2.4, 1353, 4, 0.1)], dessous=0.5)       # le petit, en retard
    massif(P, lambda x: dents(x, cx=118.0, k=0.22, base=40.0), [(111.0, 33.0), (122.0, 32.0)],
           [T.CIEL[4], T.CIEL[5], T.CIEL[6], T.CIEL[7]], [T.CIEL[8], T.CIEL[9], T.CIEL[10], NE3], [T.CIEL[6], T.CIEL[7], T.CIEL[8]],
           NE3, 1354, brume=(T.CIEL[8], 36.0, 6.0))
    # La rue : des toits d'ardoise, des cheminées qui fument, des fenêtres jaunes ; le réverbère.
    for i in range(9):
        x0 = 20.0 + i * 18.0 + 4 * hz(i, 1, 1355)
        w = 12.0 + 6 * hz(i, 2, 1355)
        yt = 40.0 + 6 * hz(i, 3, 1355)
        mur = (X > x0) & (X < x0 + w) & (Y > yt) & (Y < 70)
        P.rampe(mur, 0.3 + 0.2 * (pg.fbm(X / 2.0, Y / 2.0, 2, 1356 + i) - 0.5), [ENCRE, NU1, NU2], 0.5)
        toit = P.masque_poly([(x0 - 1.0, yt), (x0 + w + 1.0, yt), (x0 + w * 0.5, yt - 5.0 - 2 * hz(i, 4, 1355))])
        P.rampe(toit, 0.35 + 0.3 * (X - x0) / w, [ENCRE, NU1, NU2, T.CIEL[4]], 0.5)
        P.remplir(P.crete(toit), T.CIEL[6])
        for k in range(2):
            fx = x0 + 2.0 + k * (w - 6.0) * 0.8
            if hz(i, 5 + k, 1355) < 0.6:
                P.rect(fx, yt + 3.0, 2.4, 3.0, LA2 if (int(p * 8) + i + k) % 7 else LA1)
                P.rect(fx + 1.1, yt + 3.0, 0.3, 3.0, BO1)
        cx = x0 + w * 0.7
        P.rect(cx, yt - 6.0, 1.6, 4.0, NU1)
        pg.fumee(P, cx + 0.8, yt - 6.2, (p + 0.13 * i) % 1.0)
    tab.plan("vitre", 0.0)
    # ---- La vitre : la pluie qui coule en traînées, la buée en bas (le dessin fait au doigt : un nuage et une goutte),
    # le reflet de la lampe.
    vitre = (X > VX0) & (X < VX1) & (Y > VY0) & (Y < VY1)
    buee = vitre & (Y > 40.0 + 6.0 * pg.fbm(X / 8.0, X * 0, 2, 1357))
    dessin = ((np.abs(np.hypot((X - 70.0) / 1.6, Y - 52.0) - 4.0) < 0.5) & (Y < 53.0)) | (
        (np.abs(np.hypot(X - 64.0, Y - 52.6) - 2.0) < 0.45) & (Y < 53.0)) | (
        (np.abs(np.hypot(X - 77.0, Y - 52.8) - 2.0) < 0.45) & (Y < 53.0)) | ((np.abs(Y - 53.4) < 0.4) & (X > 62) & (X < 79))
    dessin |= (np.abs(np.hypot(X - 90.0, (Y - 54.0) * 0.8) - 2.2) < 0.45)                    # une goutte (Pilou)
    voile(P, buee & ~dessin, T.CIEL[9], np.clip(0.18 + (Y - 40.0) / 90.0, 0, 0.4))
    for i in range(26):                                               # les gouttes qui coulent
        x = VX0 + 2 + (VX1 - VX0 - 4) * hz(i, 1, 1358)
        tt = (p + hz(i, 2, 1358)) % 1.0
        y0 = VY0 + 2 + 40.0 * hz(i, 3, 1358)
        y = y0 + 22.0 * tt * tt
        if y < VY1 - 1:
            P.trait(x, y0, x + 0.3 * math.sin(i), y, T.CIEL[7])
            P.ell(x + 0.3 * math.sin(i), y, 0.6, 0.8, T.CIEL[10])
            P.point(x + 0.1, y - 0.3, BLANC)
    for i in range(60):                                               # les gouttes posées
        x, y = VX0 + 2 + (VX1 - VX0 - 4) * hz(i, 1, 1359), VY0 + 2 + (VY1 - VY0 - 4) * hz(i, 2, 1359)
        P.point(x, y, T.CIEL[9])
        P.point(x - 0.3, y - 0.3, NE4)
    halo(P, 50.0, 30.0, 8.0, LA2, 0.5)                                 # le reflet de la lampe
    tab.plan("dedans", 0.0)
    # ---- La chambre : le mur de bois chaud, éclairé par la lampe à gauche ; l'encadrement, ses croisillons ; les
    # rideaux à plis ; le rebord où l'on s'assoit.
    mur = ~vitre
    dl = np.hypot(X - 16.0, Y - 40.0)
    P.rampe(mur, 0.85 - dl / 120.0 + 0.14 * (pg.fbm(X / 3.0, Y / 3.0, 3, 1360) - 0.5), [BO1, BO2, BO3, TE2, ME1], 0.45)
    P.remplir(mur & (np.abs(((X + 0.5 * np.sin(Y / 9.0)) % 7.0) - 0.2) < 0.25) & (dl < 90), BO1)                   # les lambris
    cadre = (((np.abs(X - VX0) < 2.0) | (np.abs(X - VX1) < 2.0)) & (Y > VY0 - 2) & (Y < VY1 + 2)) | (
        ((np.abs(Y - VY0) < 2.0) | (np.abs(Y - VY1) < 2.0)) & (X > VX0 - 2) & (X < VX1 + 2)) | (
        (np.abs(X - (VX0 + VX1) / 2) < 1.0) & vitre) | ((np.abs(Y - 26.0) < 1.0) & vitre)
    P.rampe(cadre, 0.6 - np.clip((X - 40) / 200.0, 0, 0.4) + 0.1 * (pg.fbm(X / 0.6, Y / 4.0, 2, 1361) - 0.5), [BO1, BO2, BO3, TE2, TE3], 0.45)
    P.remplir(cadre & ~np.roll(cadre, 1, axis=1) & (X < 110), TE3)
    for (x0, x1, cote) in ((26.0, 46.0, 1), (162.0, 186.0, -1)):      # les rideaux
        rid = (X > x0) & (X < x1) & (Y < 72.0 - 6.0 * np.abs(((X - x0) / (x1 - x0)) - (0.0 if cote > 0 else 1.0)) * 0)
        pli = np.sin((X - x0) * 1.5 + 0.4 * onde(p, 0.1 * cote))
        lum_ = 0.6 + 0.25 * pli - 0.25 * (X - 16.0) / 170.0
        P.rampe(rid & (Y > -16) & (Y < 72), lum_, [RO1, ME1, LA1, LA2, CREME], 0.45)
        P.remplir(rid & (np.abs(Y - 30.0) < 1.2), TE1)                 # l'embrasse
    rebord = (Y > 72.0) & (Y < 80.2)
    P.rampe(rebord, 0.8 - np.clip(np.abs(X - 16.0) / 220.0, 0, 0.5) + 0.12 * (pg.fbm(X / 4.0, Y / 0.5, 2, 1362) - 0.5), [BO1, BO2, BO3, TE2, TE3, PJ3], 0.45)
    P.remplir(np.abs(Y - 72.3) < 0.35, PJ4)
    P.remplir((Y > 79.0) & (Y < 80.2), BO1)
    # ---- La lampe, à gauche, et sa lumière ; la casserole cabossée, le baluchon, la tasse qui fume, une plante.
    halo(P, 14.0, 40.0, 26.0, LA2, 0.55)
    P.rect(12.0, 54.0, 4.0, 18.0, BO1)
    P.rect(8.0, 70.0, 12.0, 2.0, BO2)
    abat = P.masque_poly([(4.0, 52.0), (24.0, 52.0), (20.0, 40.0), (8.0, 40.0)])
    P.rampe(abat, 0.85 - (Y - 40) / 40.0, [ME1, LA1, LA2, LA3, CREME], 0.45)
    P.remplir(P.crete(abat), LA3)
    cx, cy = 128.0, 72.4                                               # la casserole, avec sa bosse
    corps = (np.abs(X - cx) < 6.0) & (Y > cy - 5.0) & (Y < cy)
    P.rampe(corps, 0.7 - 0.35 * (X - cx) / 6.0 + 0.2 * (np.hypot(X - cx - 2.0, Y - cy + 3.0) < 1.2), [R1, R2, R3, R4, NE3], 0.45)
    P.ell(cx + 2.0, cy - 3.0, 1.2, 1.0, R1)
    P.rect(cx - 6.4, cy - 5.6, 12.8, 0.8, R4)
    P.rect(cx + 6.0, cy - 4.6, 7.0, 1.0, BO1)
    pg.vapeur(P, cx, cy - 6.0, coul=NE3, h=8.0, n=3)
    bx, by = 150.0, 72.4                                               # le baluchon
    bal = P.ell(bx, by - 3.6, 5.0, 3.8, T.BLEU, cond=Y < by)
    P.rampe(bal, 0.6 - 0.3 * (X - bx) / 5.0 + 0.2 * (np.sin(X * 2.0 + Y) > 0.7), [NU2, T.CIEL[4], T.BLEU, T.CIEL[8]], 0.45)
    P.poly([(bx - 1.0, by - 7.2), (bx + 1.0, by - 7.2), (bx + 2.2, by - 9.4), (bx - 2.2, by - 9.4)], T.BLEU)
    P.trait(bx + 2.0, by - 8.0, bx + 10.0, by - 14.0, BO2, P.ep(0.5))
    mx, my = 104.0, 72.4                                               # la tasse
    P.rect(mx - 2.0, my - 4.0, 4.0, 4.0, CREME)
    P.rect(mx - 2.0, my - 4.0, 1.0, 4.0, LA3)
    P.courbe([(mx + 2.0, my - 3.2), (mx + 3.4, my - 2.2), (mx + 2.0, my - 1.0)], CREME, 1)
    pg.vapeur(P, mx, my - 4.4, coul=NE3, h=6.0, n=2, d=0.4)
    px_, py_ = 178.0, 72.4                                             # une plante en pot (des fleurs bleues)
    P.poly([(px_ - 3.0, py_), (px_ + 3.0, py_), (px_ + 3.6, py_ - 4.0), (px_ - 3.6, py_ - 4.0)], RO2)
    for k in range(5):
        a = -2.2 + 0.35 * k
        P.trait(px_, py_ - 4.0, px_ + 6.0 * math.cos(a), py_ - 4.0 + 8.0 * math.sin(a), T.S2)
        P.point(px_ + 6.0 * math.cos(a), py_ - 4.0 + 8.0 * math.sin(a), T.BLEU, 2)
    P.rect(64.0, 70.6, 6.0, 1.6, CREME)                                # un dessin des montagnes, posé
    P.trait(65.0, 71.8, 67.0, 70.8, NU2)
    P.trait(67.0, 70.8, 69.0, 71.8, NU2)


