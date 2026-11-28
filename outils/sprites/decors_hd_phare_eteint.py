"""Décors haute définition du « Phare éteint » (480 × 240), peints avec paysage.py.

Un mystère au bord de la mer : une côte de granit, la brume, la nuit bleue. Palette : bleus de nuit, gris-bleus de
brume, granit ardoise, bois sombre, et une seule famille chaude (lanternes, bougies, poêle, fenêtres) qui porte la
lumière et troue le bleu. La brume épaissit avec la distance. Le phare de la Dent-Creuse est le même partout : une tour
effilée sur son rocher, une galerie, une lanterne vitrée ; il est éteint, sauf à la toute fin, sur la jetée.

Coordonnées : unités du monde (x de 0 à 192, y de -16 à 80). Places et clés : assets/scenes/phare-eteint.txt.
"""
import math

import numpy as np

import paysage as pg
from decors_hd import decor
from paysage import Tons, cs, hz, onde, voile, halo, dallage, rai, poussiere

NU0, NU1, NU2, NU3, NU4 = cs("#0b1630", "#13254a", "#1d3766", "#2e4f86", "#4a6fa8")
BM1, BM2, BM3, BM4 = cs("#5f7aa6", "#8098bf", "#a9bbd8", "#cfdaea")
ME0, ME1, ME2 = cs("#08142a", "#0f2443", "#1b3a62")
GR1, GR2, GR3, GR4 = cs("#232a3a", "#3a4357", "#566079", "#7f889c")
LU1, LU2, LU3, LU4, LU5 = cs("#8a4a1f", "#d9803a", "#f69d50", "#ffc89a", "#fff1c9")
BO1, BO2, BO3, BO4 = cs("#2e1d12", "#4e321d", "#77502f", "#a87a4c")
CREME, ENCRE = cs("#efe4cc", "#0a0f1c")
CIRE, CIRE2 = cs("#d9a82e", "#f5d76e")
VI1, VI2 = cs("#33294f", "#56487e")
GO1, GO2 = cs("#4a3f2a", "#6e6040")
VOLET, VOLET2 = cs("#3f6fb0", "#6c98d0")
LAITON, LAITON2 = cs("#b98b2e", "#e8c45e")
BLANC = cs("#ffffff")[0]

PHARE = Tons(
    ciel=("#0a0f1c", "#0b1630", "#13254a", "#1d3766", "#2e4f86", "#4a6fa8", "#5f7aa6", "#8098bf", "#a9bbd8", "#cfdaea",
          "#e3eaf3", "#f3f5f8"),
    loin=("#232a3a", "#3a4357", "#566079", "#7f889c", "#a9bbd8", "#cfdaea"),
    herbe=("#0f2436", "#17384a", "#245566", "#3d7a84", "#6aa8a4"),
    eau=("#08142a", "#0f2443", "#1b3a62", "#2e4f86", "#4a6fa8", "#5f7aa6", "#8098bf", "#a9bbd8", "#cfdaea"),
    soleil="#fff1c9", or_=("#b98b2e", "#e8c45e", "#fff1c9"), nuit=("#0a0f1c", "#0b1630", "#13254a"),
    bois=("#2e1d12", "#4e321d", "#77502f", "#a87a4c", "#efe4cc"), toit=("#33294f", "#56487e"), pierre=("#566079", "#a9bbd8"),
    orange=("#d9803a", "#f69d50"), lueur=("#ffc89a", "#fff1c9"), creme="#efe4cc", encre="#0a0f1c", violet="#8a7cc0",
    bleu="#6c98d0")
# Le même monde au petit matin (chez Pilou, le Passe-Pied) : la brume est claire, le ciel pâle.
AUBE = Tons(
    ciel=("#4a6fa8", "#5f7aa6", "#7189b4", "#8098bf", "#95aacc", "#a9bbd8", "#bccae1", "#cfdaea", "#dde4ee", "#ebe8e6",
          "#f6e6d2", "#fff1c9"),
    loin=("#3a4357", "#566079", "#7f889c", "#a9bbd8", "#cfdaea", "#e3eaf3"),
    herbe=("#0f2436", "#17384a", "#245566", "#3d7a84", "#6aa8a4"),
    eau=("#13254a", "#1d3766", "#2e4f86", "#4a6fa8", "#5f7aa6", "#8098bf", "#a9bbd8", "#cfdaea", "#e3eaf3"),
    soleil="#fff1c9", or_=("#b98b2e", "#e8c45e", "#fff1c9"), nuit=("#0a0f1c", "#0b1630", "#13254a"),
    bois=("#2e1d12", "#4e321d", "#77502f", "#a87a4c", "#efe4cc"), toit=("#33294f", "#56487e"), pierre=("#566079", "#a9bbd8"),
    orange=("#d9803a", "#f69d50"), lueur=("#ffc89a", "#fff1c9"), creme="#efe4cc", encre="#0a0f1c", violet="#8a7cc0",
    bleu="#6c98d0")


# ---------------------------------------------------------------------------------------------------------------
# Ce qui revient de lieu en lieu
# ---------------------------------------------------------------------------------------------------------------
def _a(x):
    return np.asarray(x, dtype=float)


def brume(P, y, ep, g, coul, force=0.6, x0=-10, x1=202):
    """Un banc de brume qui respire : une bande ondulée, déchirée par le bruit, posée en trame."""
    d = pg.fbm((P.X + 2.5 * onde(P.p, 0.13 * g)) / 26.0, P.Y / 5.0, 3, 500 + g)
    m = (np.abs(P.Y - y - 2.5 * np.sin(P.X / 21.0 + g)) < ep * (0.5 + 0.9 * d)) & (P.X > x0) & (P.X < x1)
    voile(P, m, coul, force)


def phare(P, x, y, h, sombre, clair, allume=False, rocher=True):
    """Le phare de la Dent-Creuse : (x, y) le pied de la tour, h sa hauteur. Tour effilée, galerie, lanterne vitrée, toit
    pointu ; sur son rocher. allume : sa lanterne brille (la fin de l'histoire)."""
    k = h / 40.0
    if rocher:
        pts = [(x - 15 * k, y + 7 * k), (x - 11 * k, y + 1.5 * k), (x - 5 * k, y - 0.6 * k), (x + 5 * k, y), (x + 10 * k, y + 2.5 * k),
               (x + 16 * k, y + 7 * k)]
        P.poly(pts, sombre)
        P.trait(pts[1][0], pts[1][1], pts[2][0], pts[2][1], clair)
    P.poly([(x - 4.2 * k, y), (x + 4.2 * k, y), (x + 2.6 * k, y - h * 0.78), (x - 2.6 * k, y - h * 0.78)], sombre)
    P.poly([(x - 4.2 * k, y), (x - 3.0 * k, y), (x - 1.8 * k, y - h * 0.78), (x - 2.6 * k, y - h * 0.78)], clair)
    P.rect(x - 3.8 * k, y - h * 0.8, 7.6 * k, max(0.4, 1.2 * k), sombre)                    # la galerie
    P.rect(x - 2.2 * k, y - h * 0.93, 4.4 * k, h * 0.13, sombre)                            # la lanterne
    P.poly([(x - 2.8 * k, y - h * 0.93), (x + 2.8 * k, y - h * 0.93), (x, y - h)], sombre)
    if allume:
        P.rect(x - 1.6 * k, y - h * 0.91, 3.2 * k, h * 0.09, LU5)
        halo(P, x, y - h * 0.87, 9 * k + 4, LU4, 0.6)
    else:
        P.rect(x - 1.6 * k, y - h * 0.91, 3.2 * k, h * 0.09, clair)
    for j in range(3):                                                                      # ses meurtrières
        if k > 0.5:
            P.rect(x - 0.4 * k, y - h * (0.2 + 0.2 * j), max(0.4, 0.8 * k), max(0.4, 1.6 * k), clair)


def bougie(P, x, y, h=5.0, allumee=True, lueur=14.0):
    """Une bougie dans son bougeoir ; sa flamme vacille et éclaire en trame."""
    P.ell(x, y, 2.6, 0.9, LAITON)
    P.ell(x, y - 0.4, 1.8, 0.6, LAITON2)
    P.rect(x - 0.8, y - h, 1.6, h, CREME)
    P.rect(x + 0.2, y - h, 0.6, h, BM3)
    P.trait(x, y - h, x, y - h - 0.8, ENCRE)
    if allumee:
        d = 0.4 * onde(P.p * 2)
        halo(P, x, y - h - 2.0, lueur, LU4, 0.5)
        P.poly([(x - 0.9, y - h - 0.6), (x + 0.9, y - h - 0.6), (x + d, y - h - 4.2)], LU3)
        P.poly([(x - 0.5, y - h - 0.6), (x + 0.5, y - h - 0.6), (x + d * 0.6, y - h - 2.8)], LU5)


def fanal(P, x, y, k=1.0, lueur=12.0):
    """Une lanterne-tempête posée ou pendue : (x, y) son pied."""
    vif = int(P.p * 8) % 5 != 0
    halo(P, x, y - 2.6 * k, lueur, LU3, 0.5)
    P.rect(x - 1.4 * k, y - 0.7 * k, 2.8 * k, 0.7 * k, GR1)
    P.rect(x - 1.1 * k, y - 4.0 * k, 2.2 * k, 3.4 * k, LU4 if vif else LU3)
    P.rect(x - 0.4 * k, y - 3.2 * k, 0.8 * k, 2.0 * k, LU5)
    P.rect(x - 1.4 * k, y - 4.6 * k, 2.8 * k, 0.7 * k, GR1)
    P.trait(x - 1.2 * k, y - 4.0 * k, x - 1.2 * k, y - 0.7 * k, GR1)
    P.trait(x + 1.1 * k, y - 4.0 * k, x + 1.1 * k, y - 0.7 * k, GR1)
    P.courbe([(x - 1.2 * k, y - 4.6 * k), (x, y - 6.4 * k), (x + 1.2 * k, y - 4.6 * k)], GR2, 1)


def goeland(P, x, y, sens=1, pose=True):
    """Un goéland : posé (il tourne la tête de temps en temps) ou en vol (ses ailes battent)."""
    if pose:
        tourne = sens if int(P.p * 8 + x) % 6 else -sens
        P.ell(x, y - 1.6, 2.4, 1.5, BM4)
        P.ell(x - sens * 0.6, y - 1.3, 1.8, 1.0, GR4)
        P.poly([(x - sens * 2.0, y - 1.8), (x - sens * 4.0, y - 1.0), (x - sens * 2.0, y - 0.8)], GR3)
        P.ell(x + sens * 1.6, y - 3.4, 1.1, 1.1, BLANC)
        P.rect(min(x + sens * 1.6 + tourne * 0.8, x + sens * 1.6 + tourne * 2.0), y - 3.4, 1.2, 0.5, LU3)
        P.point(x + sens * 1.6 + tourne * 0.3, y - 3.7, ENCRE)
        P.trait(x - 0.4, y, x - 0.4, y - 0.6, LU2)
    else:
        aile = onde(P.p * 2, x * 0.01)
        P.trait(x - 3.2, y - 1.2 * aile, x, y, BM4, P.ep(0.5))
        P.trait(x, y, x + 3.2, y - 1.2 * aile, BM4, P.ep(0.5))
        P.point(x, y, BLANC)


def barque_a_sec(P, x, y, l=22.0, coul=None, sens=1):
    """Une barque tirée au sec, couchée sur le flanc : bordés, liston clair, un banc."""
    c0, c1, c2 = coul or (BO1, BO2, BO3)
    P.poly([(x - l / 2, y - 4.0), (x + l / 2 + 2 * sens, y - 5.0), (x + l / 2 - 3, y), (x - l / 2 + 3, y)], c0)
    P.poly([(x - l / 2 + 1, y - 3.4), (x + l / 2, y - 4.2), (x + l / 2 - 3.4, y - 1.2), (x - l / 2 + 3.4, y - 1.2)], c1)
    P.trait(x - l / 2, y - 4.1, x + l / 2 + 2 * sens, y - 5.1, c2, P.ep(0.5))
    for i in range(3):
        P.trait(x - l / 2 + 3 + i * 0.4, y - 3.0 + i * 0.9, x + l / 2 - 2 - i * 0.6, y - 3.8 + i * 0.9, c0)
    P.rect(x - 1.5, y - 4.6, 3.0, 0.8, c2)


def casier(P, x, y, k=1.0):
    """Un casier à homards : arceaux de bois, filet en croisillons."""
    P.ell(x, y - 2.2 * k, 4.0 * k, 2.6 * k, BO1, cond=P.Y < y)
    m = ((P.X - x) / (3.4 * k)) ** 2 + ((P.Y - y + 2.2 * k) / (2.0 * k)) ** 2 <= 1
    P.remplir(m & (P.Y < y) & ((P.XI + P.YI) % 3 == 0), BO3)
    P.remplir(m & (P.Y < y) & ((P.XI - P.YI) % 3 == 0), BO2)
    P.rect(x - 4.0 * k, y - 0.6 * k, 8.0 * k, 0.6 * k, BO2)
    for dx in (-2.6, 0, 2.6):
        P.trait(x + dx * k, y, x + dx * k * 0.8, y - 4.4 * k, BO3)


def pierres_de_taille(P, masque, coul, joint, lh=3.4, lw=7.0, dx=0.0, dy=0.0):
    """Un appareil de pierre : joints horizontaux, joints verticaux décalés d'une assise sur l'autre."""
    assise = np.floor((P.Y - dy) / lh)
    P.remplir(masque & (((P.Y - dy) % lh) < 0.42), joint)
    P.remplir(masque & ((((P.X - dx) / lw + assise * 0.5) % 1.0) < 0.42 / lw) & (((P.Y - dy) % lh) >= 0.42), joint)


# =====================================================================================================================
# Chez Pilou : un coin de bureau au petit matin, vu de tout près (on est une goutte d'encre). Le soleil entre par la
# fenêtre de gauche et couche sur le bois le dessin des carreaux. L'encrier ouvert et sa plume, l'enveloppe sans timbre
# appuyée contre lui (la clé), la bougie pour la brûler, les cartes d'Anselme épinglées au mur, une par hiver.
# Le plateau du bureau est le sol (y = 52) : Pilou se tient à droite de la bougie.
# =====================================================================================================================
@decor("phare-eteint", "chez-pilou", soleil=(30.0, -6.0), tons=AUBE, nom="Chez Pilou", matiere=True)
def chez_pilou(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tout = np.ones(X.shape, dtype=bool)
    BORD = 45.0                                                 # le fond du plateau, contre le mur
    wx, wy, ww, wh = 5.0, -12.0, 40.0, 41.0                     # la fenêtre

    # =========================================================================================================== le mur
    tab.plan("ciel", 0.0)
    # Le rai de soleil : une bande qui descend de la fenêtre vers la droite, et réchauffe ce qu'elle traverse.
    axe = (Y - wy - wh * 0.5) - (X - wx - ww * 0.5) * 0.52
    rai_ = np.clip((1 - np.abs(axe) / 15.0) * 3.0, 0, 1) * (X > wx + ww) * np.clip(1 - (X - wx - ww) / 150.0, 0, 1)
    Lm = 0.66 + 0.24 * rai_ + 0.24 * np.exp(-((X - 76.0) / 50.0) ** 2 - ((Y - 46.0) / 18.0) ** 2) - 0.0008 * (X - 60.0)
    Lm = Lm * (1 - 0.3 * np.clip(1 - (Y + 16.0) / 9.0, 0, 1))                                     # le plafond est dans l'ombre
    lames(P, tout, Lm, larg=13.0, graine=510, vertical=True, alb=0.78, sens=-1, noeuds=0.5)
    P.rampe((Y > BORD - 3.4) & (Y <= BORD), (0.58 - 0.05 * (Y - BORD + 3.4)) * Lm, R_BOIS, 0.5)     # la plinthe du fond
    P.rampe((Y > BORD - 3.4) & (Y <= BORD - 3.0), 0.9 * Lm, R_BOIS, 0.5)

    # ---- La fenêtre : l'aube sur les toits, la brume entre les cheminées, des oiseaux.
    fen = m_rect(P, wx, wy, ww, wh)
    sol_ = (wx + 8.0, wy + 22.6)                                                                   # le soleil se lève derrière les toits
    ds = np.hypot(X - sol_[0], (Y - sol_[1]) * 1.3)
    P.rampe(fen, 0.3 + 0.023 * (Y - wy) + 0.05 * (pg.fbm(X / 14.0, Y / 3.0, 3, 511) - 0.5) + 0.3 * np.exp(-(ds / 15.0) ** 2), T.CIEL, 0.6)
    for i, (cx_, cy_, l) in enumerate(((wx + 24.0, wy + 7.0, 20.0), (wx + 10.0, wy + 13.0, 14.0), (wx + 31.0, wy + 18.0, 15.0))):      # des barres de nuages, dorées par-dessous
        cx_ = cx_ + 0.6 * onde(p, 0.2 * i)
        nb = ((X - cx_) / (l / 2)) ** 2 + ((Y - cy_) / 1.5) ** 2 + 0.6 * (pg.fbm(X / 4.0, Y / 0.9, 3, 512 + i) - 0.5) < 1
        P.rampe(fen & nb, 0.3 + 0.5 * (Y - cy_ + 1.0) / 2.0, [T.CIEL[6], T.CIEL[9], T.CIEL[11], LU4], 0.5)
    P.remplir(fen & (ds < 4.4), T.CIEL[11])
    P.remplir(fen & (ds < 3.4), BLANC)
    rangs = ((wy + 31.6, (T.CIEL[5], T.CIEL[8]), 514), (wy + 35.2, (T.CIEL[2], T.CIEL[5]), 515), (wy + 39.0, (T.CIEL[0], T.CIEL[3]), 516))
    for rang, (base, tons_, g) in enumerate(rangs):                                               # trois rangs de toits, du plus brumeux au plus net
        x = wx - 3.0 + rang * 2.3
        i = 0
        while x < wx + ww:
            w = 6.0 + 5.0 * hz(i, 1, g)
            h = 1.0 + 4.0 * hz(i, 2, g)
            toit = P.masque_poly([(x - 0.6, base - h), (x + w + 0.6, base - h), (x + w * 0.5, base - h - w * 0.42)])
            P.remplir(fen & (m_rect(P, x, base - h, w, wy + wh - base + h) | toit), tons_[0])
            P.remplir(fen & toit & (X < x + w * 0.5), tons_[1])                                   # le versant au soleil
            P.remplir(fen & m_rect(P, x, base - h, 0.8, wy + wh - base + h), tons_[1])
            chx = x + w * (0.66 if i % 2 else 0.24)
            P.remplir(fen & m_rect(P, chx, base - h - w * 0.42, 1.4, w * 0.3), tons_[0])            # la cheminée
            P.remplir(fen & m_rect(P, chx, base - h - w * 0.42, 0.4, w * 0.3), tons_[1])
            if rang == 2 and i % 2 == 0:
                P.remplir(fen & m_rect(P, x + w * 0.4, base - h + 1.4, 1.4, 1.6), LU4)             # une fenêtre déjà allumée
            if rang > 0 and i % 2 == 1:
                fumerolle(P, chx + 0.7, base - h - w * 0.42 - 0.6, h=9.0, n=3, d=0.3 * i, coul=T.CIEL[11], force=0.45, large=0.7)
            x += w + 0.4
            i += 1
        if rang < 2:                                                                              # une nappe de brume entre deux rangs
            nb = fen & (np.abs(Y - base - 1.0 - 0.5 * np.sin(X / 3.0 + rang)) < 0.9) & (pg.fbm((X + onde(p, 0.3 * rang)) / 5.0, Y / 1.2, 2, 517 + rang) > 0.4)
            P.remplir(nb, T.CIEL[9 + rang])
    for i in range(3):                                                                            # des oiseaux passent
        t = (p + i / 3.0) % 1.0
        ox, oy = wx + ww * t, wy + 5.0 + i * 3.4 + 1.6 * math.sin(t * 9.0)
        if wx + 1 < ox < wx + ww - 2:
            a_ = 0.6 * onde(p * 2, 0.2 * i)
            P.trait(ox - 1.0, oy - a_, ox, oy, T.CIEL[0])
            P.trait(ox, oy, ox + 1.0, oy - a_, T.CIEL[0])
    # Le cadre et ses petits-bois : sombres à contre-jour, un filet d'or sur l'arête.
    cadre = m_rect(P, wx - 3.0, wy - 3.0, ww + 6.0, wh + 6.0) & ~fen
    P.rampe(cadre, 0.3 + 0.02 * (X - wx), R_BOIS, 0.5)
    croix = fen & ((np.abs(X - wx - ww / 2) < 0.9) | (np.abs(Y - wy - wh * 0.46) < 0.9))
    P.rampe(croix, 0.26, R_BOIS, 0.5)
    lisere(P, fen & ~croix, R_BOIS[8], -1, 0)
    lisere(P, fen & ~croix, R_BOIS[7], 0, 1)
    lisere(P, fen & ~croix, R_BOIS[0], 0, -1)
    P.rampe(m_rect(P, wx - 5.0, wy + wh + 3.0, ww + 12.0, 2.6), (0.9 - 0.16 * (Y - wy - wh - 3.0)) * (0.6 + 0.4 * (X > wx)), R_BOIS, 0.5)     # l'appui
    P.rampe(m_rect(P, wx - 5.0, wy + wh + 5.6, ww + 12.0, 1.0), 0.3, R_BOIS, 0.5)
    # Sur l'appui : un pot de bruyère et une petite bouteille bleue, que le soleil traverse.
    px0, py0 = wx + 31.0, wy + wh + 3.0
    P.poly([(px0 - 2.6, py0 - 4.4), (px0 + 2.6, py0 - 4.4), (px0 + 1.9, py0), (px0 - 1.9, py0)], LU1)
    P.rect(px0 - 2.9, py0 - 5.0, 5.8, 0.9, LU2)
    P.rect(px0 - 2.9, py0 - 5.0, 1.0, 0.9, LU4)
    for i in range(12):
        a = 0.2 + hz(i, 1, 515) * (math.pi - 0.4)
        l = 4.0 + 3.0 * hz(i, 2, 515)
        P.trait(px0, py0 - 5.0, px0 + l * math.cos(a), py0 - 5.4 - l * math.sin(a), T.S1 if i % 2 else T.S2)
        P.point(px0 + l * math.cos(a), py0 - 5.8 - l * math.sin(a), T.VIOLET if i % 3 else VI2, 2 if i % 4 == 0 else 1)
    bx_ = wx + 13.0
    bt = m_rect(P, bx_ - 1.8, py0 - 6.0, 3.6, 6.0) | m_rect(P, bx_ - 0.7, py0 - 8.6, 1.4, 2.6)
    P.rampe(bt, 0.5 - 0.3 * (X - bx_) / 1.8 + 0.2 * (Y < py0 - 3.0), R_TOILE, 0.5)
    P.rect(bx_ - 1.4, py0 - 5.4, 0.5, 4.0, BLANC)
    # Le rideau, retenu par une embrasse ; il respire.
    rx0 = wx + ww + 3.0
    bouge = 0.35 * onde(p, 0.2)
    rid = (X > rx0 - 1.0) & (X < rx0 + 8.0 + 1.6 * np.sin((Y - wy) / 9.0) + bouge * (Y - wy) / 40.0) & (Y > wy - 4.0) & (Y < wy + wh + 3.0)
    pli = 0.5 + 0.5 * np.sin((X - rx0) * 2.2 + 0.6 * np.sin(Y / 5.0) + bouge)
    P.rampe(rid, 0.2 + 0.36 * pli + 0.26 * np.clip(1 - (X - rx0) / 5.0, 0, 1), R_TOILE, 0.5)
    lisere(P, rid, R_TOILE[5], -1, 0)
    P.rect(rx0 - 1.0, wy + 25.0, 7.6, 1.2, LAITON)
    P.rect(rx0 - 1.0, wy + 25.0, 2.0, 1.2, LAITON2)
    P.rect(wx - 4.0, wy - 5.4, ww + 18.0, 1.0, LAITON)                                            # la tringle
    P.ell(wx + ww + 14.6, wy - 4.9, 1.2, 1.2, LAITON2)

    # ---- Les cartes d'Anselme, une par hiver, sur un fil : chacune montre le phare et son feu.
    fx0, fx1, fy = 56.0, 100.0, -7.0
    P.courbe([(fx0, fy), ((fx0 + fx1) / 2, fy + 3.0), (fx1, fy)], GO2, 1)
    P.point(fx0, fy, LAITON2, 2)
    P.point(fx1, fy, LAITON2, 2)
    for i in range(4):
        cx_ = fx0 + 5.5 + i * 11.0
        cy_ = fy + 3.0 * (1 - ((cx_ - (fx0 + fx1) / 2) / 22.0) ** 2) + 0.6
        inc = (0.4, -0.7, 0.6, -0.3)[i] + 0.25 * onde(p, 0.23 * i)
        carte = P.masque_poly([(cx_ - 4.4 + inc * 0.4, cy_), (cx_ + 4.4 + inc * 0.4, cy_ + inc * 0.5), (cx_ + 4.4 - inc * 0.6, cy_ + 7.4 + inc * 0.5), (cx_ - 4.4 - inc * 0.6, cy_ + 7.4)])
        P.rampe(carte, 0.82 * Lm + 0.3, R_PAPIER, 0.5)
        img = carte & (np.abs(X - cx_) < 3.6) & (Y > cy_ + 0.9) & (Y < cy_ + 6.4)
        P.rampe(img, 0.2 + 0.1 * (Y - cy_) + 0.1 * i, R_NUIT, 0.5)                                 # la nuit de la carte
        P.remplir(img & (Y > cy_ + 5.0), NU1 if i % 2 else NU2)
        if i == 2:
            P.remplir(img & (Y > cy_ + 5.0) & ((P.XI + P.YI) % 3 == 0), BM4)                       # un hiver de neige
        fais = P.masque_poly([(cx_ - 1.0, cy_ + 2.4), (cx_ + 3.8, cy_ + 1.0), (cx_ + 3.8, cy_ + 3.6)])
        P.remplir(img & fais, LU4 if i != 1 else LU3)
        P.rect(cx_ - 1.6, cy_ + 2.6, 0.9, 2.6, BM4)
        P.rect(cx_ - 1.7, cy_ + 2.0, 1.1, 0.7, LU5)
        P.rect(cx_ - 0.6, cy_ - 1.0, 1.2, 2.2, R_BOIS[6])                                           # la pince à linge
        P.rect(cx_ - 0.6, cy_ - 1.0, 0.4, 2.2, R_BOIS[8])

    # ---- L'étagère : des livres, un coquillage, un réveil de laiton ; une petite carte marine épinglée dessous.
    ex, ey = 106.0, 12.0
    P.rampe(m_rect(P, ex, ey, 86.0, 1.8), (0.9 - 0.3 * (Y - ey)) * (Lm + 0.1), R_BOIS, 0.5)
    P.rampe(m_rect(P, ex + 0.6, ey + 1.8, 86.0, 1.4), 0.34 * Lm, R_BOIS, 0.5)                       # son ombre
    for cxl in (ex + 6.0, ex + 70.0):
        P.poly([(cxl, ey + 1.8), (cxl + 1.4, ey + 1.8), (cxl + 1.4, ey + 3.6), (cxl, ey + 6.4)], R_BOIS[2])
    x = ex + 2.0
    i = 0
    dos = (R_TOILE, [VI1, VI1, VI2, T.VIOLET, BM3, BM4], R_CUIVRE, R_NUIT[1:7], [GO1, GO1, GO2, LAITON, LAITON2, LU5], R_VERRE)
    while x < ex + 53:
        w, h = 2.2 + 2.4 * hz(i, 1, 516), 8.4 + 4.0 * hz(i, 2, 516)
        penche = (i == 7)
        r = dos[int(hz(i, 3, 516) * len(dos))]
        if penche:
            liv = P.masque_poly([(x, ey), (x + w, ey), (x + w + 3.4, ey - h), (x + 3.4, ey - h)])
        else:
            liv = m_rect(P, x, ey - h, w, h)
        P.rampe(liv, (0.34 + 0.3 * np.clip(1 - (X - x - (3.4 * (ey - Y) / h if penche else 0)) / w, 0, 1)) * (0.5 + Lm), r, 0.5)
        if not penche:
            P.rect(x, ey - h * 0.78, w, 0.5, LAITON)
            P.rect(x, ey - h * 0.22, w, 0.5, LAITON)
            lisere(P, liv, r[5], -1, 0)
        x += w + (3.6 if penche else 0.3)
        i += 1
    P.rampe(m_ell(P, ex + 60.6, ey - 1.9, 3.2, 2.0), 0.5 - 0.3 * (X - ex - 60.6) / 3.2 - 0.2 * (Y - ey + 1.9), R_PAPIER, 0.5)       # le coquillage
    for k in range(4):
        P.trait(ex + 58.4 + k * 1.1, ey - 0.4, ex + 61.6, ey - 3.4, R_PAPIER[1])
    rv = (ex + 70.0, ey - 4.6)                                                                    # le réveil
    P.rampe(m_ell(P, rv[0], rv[1], 4.2, 4.2), 0.5 - 0.3 * (X - rv[0]) / 4.2 - 0.2 * (Y - rv[1]) / 4.2, [GO1, LAITON, LAITON2, LU5], 0.5)
    P.rampe(m_ell(P, rv[0], rv[1], 3.2, 3.2), 0.7 - 0.2 * (X - rv[0]) / 3.2, R_PAPIER[2:], 0.5)
    P.trait(rv[0], rv[1], rv[0] - 1.4, rv[1] - 1.2, ENCRE)
    a_ = 2 * math.pi * int(p * 8) / 8.0
    P.trait(rv[0], rv[1], rv[0] + 2.4 * math.sin(a_), rv[1] - 2.4 * math.cos(a_), LU2)                # la trotteuse
    for dx in (-2.8, 2.8):
        P.ell(rv[0] + dx, rv[1] - 4.4, 1.3, 1.0, LAITON2)
        P.trait(rv[0] + dx * 0.9, rv[1] + 3.6, rv[0] + dx * 1.2, rv[1] + 4.6, GO1)
    cm = m_rect(P, 146.0, 20.0, 19.0, 14.0)                                                       # la carte marine : une côte, un rocher, une croix
    P.rampe(m_rect(P, 147.0, 34.0, 19.0, 0.8), 0.36 * Lm, R_BOIS, 0.5)
    P.rampe(cm, (0.66 + 0.1 * (pg.fbm(X / 3.0, Y / 3.0, 2, 517) - 0.5)) * (0.5 + Lm), R_PAPIER, 0.5)
    cote_ = cm & (X < 153.0 + 2.6 * np.sin(Y / 2.2) + 1.6 * np.sin(Y * 1.3))
    P.remplir(cote_, R_PLATRE[6])
    lisere(P, cote_, R_TOILE[2], 1, 0)
    P.ell(160.0, 27.0, 1.3, 0.9, R_PLATRE[4])
    P.trait(159.0, 25.0, 161.0, 23.4, LU2)
    P.trait(159.0, 23.4, 161.0, 25.0, LU2)
    for k in range(3):
        P.remplir(cm & (np.abs(Y - 30.0 - k * 1.2 - 0.4 * np.sin(X * 0.9)) < 0.2) & (X > 154.0) & ((P.XI // 2) % 2 == 0), R_TOILE[3])
    P.point(155.6, 20.8, LU2, 2)
    # Dans l'angle, en haut à droite : une toile, son araignée.
    pg.toile_araignee(P, 196.0, -14.0, 11.0, sens=(-1, 1), coul=R_PAPIER[1])
    pg.araignee(P, 188.4, -8.0, 8.0, d=0.3, coul=R_BOIS[0])

    # ====================================================================================================== le bureau
    tab.plan("moyen", 0.5)
    bureau = Y > BORD
    # Le soleil couche les carreaux sur le bois : un grand quadrilatère, coupé par l'ombre des petits-bois.
    tq = (Y - BORD) / 35.0
    xl, xr = 30.0 + 40.0 * tq, 92.0 + 66.0 * tq
    sq = (X - xl) / (xr - xl)
    tache = np.clip(np.minimum(sq, 1 - sq) * 12.0, 0, 1) * np.clip(tq * 30.0, 0, 1)
    tache = tache * (1 - np.clip(1 - np.abs(sq - 0.5) / 0.03, 0, 1)) * (1 - np.clip(1 - np.abs(tq - 0.52) / 0.035, 0, 1))
    Lb = 0.64 + 0.58 * tache + 0.1 * np.exp(-((X - 96.0) / 9.0) ** 2 - ((Y - 54.0) / 3.0) ** 2)

    def ombre(pts, f=0.5):
        nonlocal Lb
        Lb = Lb * (1 - f * P.masque_poly(pts))

    ombre([(70.0, 51.6), (83.0, 51.6), (112.0, 60.5), (96.0, 62.0)], 0.52)                         # l'encrier
    ombre([(60.0, 50.8), (71.0, 50.8), (98.0, 63.0), (82.0, 62.0)], 0.4)                           # l'enveloppe
    ombre([(93.6, 51.8), (97.0, 51.8), (121.0, 59.6), (116.0, 60.2)], 0.4)                         # la bougie
    ombre([(12.0, 52.0), (38.0, 52.0), (52.0, 57.0), (20.0, 57.6)], 0.45)                          # les livres
    ombre([(172.0, 52.4), (183.0, 52.4), (196.0, 56.0), (184.0, 56.4)], 0.35)                      # la tasse
    dy = np.maximum(Y - 30.0, 0.3)
    z = 60.0 / dy
    lame = np.floor(z * 1.15 + 0.2)
    fil = np.sin(z * 34.0 + 5.0 * pg.fbm(X / 40.0, z * 2.0, 3, 518) + 2.0 * hz(lame, 0, 519))
    v = 0.66 + 0.1 * hz(lame, 1, 519) + 0.07 * fil + 0.2 * (pg.fbm(X / 22.0, z * 6.0, 3, 520) - 0.5)
    nd = np.hypot((X - 136.0) / 5.0, (Y - 66.0) / 1.5)                                            # un nœud du bois
    v = v - 0.2 * np.clip(1 - nd, 0, 1) + 0.06 * np.sin(nd * 5.0) * (nd < 2.6)
    joint = (z * 1.15 + 0.2 - lame) < 0.02 * z
    v = np.where(joint, v * 0.55, v)
    P.rampe(bureau, v * Lb, R_BOIS, 0.5)
    P.rampe(bureau & (Y < BORD + 0.5), 0.36, R_BOIS, 0.5)                                          # l'ombre au pied du mur

    # ---- À gauche : deux livres couchés, une paire de lunettes dessus.
    for k, (lx0, ly0, lw_, lh_, r) in enumerate(((9.0, 47.0, 30.0, 5.2, R_TOILE), (12.0, 42.6, 24.0, 4.4, [VI1, VI1, VI2, T.VIOLET, BM3, BM4]))):
        liv = m_rect(P, lx0, ly0, lw_, lh_)
        P.rampe(liv, 0.34 + 0.3 * (X < lx0 + 3.0) + 0.08 * (Y < ly0 + 1.0), r, 0.5)
        tr = m_rect(P, lx0 + lw_ - 1.2, ly0 + 0.8, 1.2, lh_ - 1.6)
        P.rampe(tr, 0.7 + 0.2 * ((P.YI % 2) == 0), R_PAPIER, 0.5)                                   # la tranche
        for dx in (4.0, lw_ - 6.0):
            P.rect(lx0 + dx, ly0, 0.6, lh_, LAITON)
        P.rect(lx0, ly0, lw_, 0.4, r[4])
    for dx in (0.0, 7.0):                                                                         # les lunettes
        P.ell(18.0 + dx, 40.2, 2.8, 2.2, LAITON)
        P.ell(18.0 + dx, 40.2, 2.1, 1.6, T.CIEL[9])
        P.point(17.2 + dx, 39.4, BLANC)
    P.trait(20.8, 40.0, 22.2, 40.0, LAITON)
    P.trait(27.8, 40.0, 33.0, 42.4, LAITON)

    # ---- La clé : l'enveloppe sans timbre, appuyée contre l'encrier ouvert ; la plume.
    kx, ky = 76.0, 52.0
    env = [(47.0, 51.0), (69.6, 49.4), (71.4, 33.6), (49.0, 35.2)]
    me = P.masque_poly(env)
    P.rampe(me, 0.74 + 0.012 * (X - 47.0) - 0.008 * (Y - 34.0) + 0.06 * (pg.fbm(X / 3.0, Y / 3.0, 2, 521) - 0.5), R_PAPIER, 0.5)
    cx_, cy_ = 59.2, 41.6                                       # le rabat, déjà ouvert d'un coup de pouce
    P.trait(env[3][0], env[3][1], cx_, cy_, R_PAPIER[1])
    P.trait(env[2][0], env[2][1], cx_, cy_, R_PAPIER[1])
    P.trait(env[3][0] + 0.4, env[3][1] + 0.5, cx_, cy_ + 0.5, R_PAPIER[5])
    P.trait(env[0][0], env[0][1], cx_ - 2.0, cy_ + 3.0, R_PAPIER[2])
    P.trait(env[1][0], env[1][1], cx_ + 2.0, cy_ + 2.8, R_PAPIER[2])
    P.rampe(m_ell(P, cx_, cy_, 2.0, 1.8), 0.5 - 0.3 * (X - cx_) / 2.0 - 0.3 * (Y - cy_) / 1.8, R_CUIVRE[1:5], 0.5)                # le cachet de cire, rompu
    P.trait(cx_ - 1.6, cy_ + 0.6, cx_ + 1.4, cy_ - 0.8, R_CUIVRE[0])
    for k in range(3):                                                                            # l'adresse, à la main : trois traits
        P.trait(52.0 + k * 0.6, 45.6 + k * 1.5, 61.0 - k * 2.0, 45.0 + k * 1.5, R_NUIT[2])
    lisere(P, me, R_PAPIER[1], 1, 0)
    lisere(P, me, R_PAPIER[5], 0, -1)
    if int(p * 8) % 4 == 0:                                                                       # une écaille de maquereau y brille
        P.point(66.4, 47.6, BLANC)
    else:
        P.point(66.4, 47.6, BM3)
    # L'encrier : un gros verre bleu de nuit, l'encre dedans, le soleil qui le traverse et tombe en tache bleue.
    corps = (m_rect(P, kx - 7.6, ky - 11.0, 15.2, 11.0) | m_ell(P, kx, ky - 11.0, 7.6, 2.4)) & ~(m_rect(P, kx - 7.6, ky - 1.4, 15.2, 1.4) & (np.abs(X - kx) > 6.8))
    nx = (X - kx) / 7.6
    P.rampe(corps, 0.2 + 0.5 * np.exp(-((nx + 0.62) / 0.2) ** 2) + 0.2 * np.exp(-((nx - 0.7) / 0.14) ** 2) + 0.1 * (Y > ky - 2.0), R_NUIT, 0.5)
    P.remplir(corps & (Y > ky - 8.6) & (np.abs(nx) < 0.78), NU0)                                    # l'encre
    P.remplir(corps & (Y > ky - 8.6) & (Y < ky - 8.0) & (np.abs(nx) < 0.78), NU2)
    P.rect(kx - 5.6, ky - 10.0, 0.8, 7.0, BM4)                                                    # l'éclat de la fenêtre
    P.rect(kx - 4.4, ky - 9.4, 0.4, 3.0, BM2)
    col = m_rect(P, kx - 3.4, ky - 15.6, 6.8, 3.4)
    P.rampe(col, 0.3 + 0.5 * np.exp(-((nx + 0.3) / 0.12) ** 2), R_NUIT, 0.5)
    P.rampe(m_ell(P, kx, ky - 15.6, 4.2, 1.3), 0.5 - 0.3 * nx, R_NUIT, 0.5)                         # la lèvre
    P.ell(kx, ky - 15.6, 2.8, 0.7, ENCRE)
    P.remplir(m_ell(P, 97.0, 58.6, 6.0, 1.3) & bureau, R_TOILE[2])                                 # la tache de lumière bleue, dans son ombre
    P.remplir(m_ell(P, 97.6, 58.6, 3.0, 0.6) & bureau, R_TOILE[3])
    bch = m_ell(P, 87.6, ky - 1.2, 2.6, 1.3)                                                      # son bouchon de liège, posé à côté
    P.rampe(bch, 0.6 - 0.3 * (X - 87.6) / 2.6, R_BOIS[4:], 0.5)
    P.ell(87.2, ky - 1.8, 1.8, 0.7, R_BOIS[7])
    # La plume d'oie : la hampe, les barbes, la pointe tachée ; elle frémit.
    fr = 0.4 * onde(p, 0.1)
    q0, q1 = (kx + 0.6, ky - 15.4), (kx + 20.0 + fr, ky - 43.0)
    ux, uy = q1[0] - q0[0], q1[1] - q0[1]
    ln = math.hypot(ux, uy)
    ux, uy = ux / ln, uy / ln
    s_ = (X - q0[0]) * ux + (Y - q0[1]) * uy
    d_ = (X - q0[0]) * -uy + (Y - q0[1]) * ux
    larg_p = 4.6 * np.sin(np.clip((s_ - 6.0) / (ln - 5.0), 0, 1) * math.pi) ** 0.6
    barbes = (s_ > 6.0) & (s_ < ln + 1.0) & (np.abs(d_) < larg_p)
    P.rampe(barbes, 0.62 - 0.1 * d_ + 0.12 * np.sin((s_ - d_ * 1.6) * 3.4) - 0.1 * (d_ > 0), R_PAPIER, 0.5)
    P.remplir(barbes & (np.abs(((s_ + np.abs(d_) * 1.2) % 5.0) - 2.5) < 0.2) & (np.abs(d_) > 1.2) & (hz(np.floor((s_ + np.abs(d_) * 1.2) / 5.0), 0, 522) < 0.5), R_BOIS[4])
    P.trait(q0[0] - ux * 3.0, q0[1] - uy * 3.0, q1[0], q1[1], R_PAPIER[5], 1)
    P.trait(q0[0] - ux * 3.0 + 0.4, q0[1] - uy * 3.0, q0[0] + ux * 7.0 + 0.4, q0[1] + uy * 7.0, R_PAPIER[2], 1)
    pg.goutte(P, kx + 3.0, ky - 12.0, ky - 0.4, coul=NU1, d=0.5)                                    # elle a goutté sur le verre

    # ---- La bougie dans son bougeoir de laiton ; les allumettes et la cire, pour la lettre qu'il faudrait brûler.
    cx_, cy_ = 95.2, 52.0
    P.rampe(m_ell(P, cx_, cy_ - 0.4, 4.2, 1.5), 0.5 - 0.3 * (X - cx_) / 4.2, [GO1, LAITON, LAITON2, LU5], 0.5)
    P.ell(cx_, cy_ - 0.9, 3.0, 0.9, GO1)
    P.courbe([(cx_ + 3.6, cy_ - 0.8), (cx_ + 6.2, cy_ - 2.2), (cx_ + 4.4, cy_ - 0.2)], LAITON, 2)
    ci = m_rect(P, cx_ - 1.2, cy_ - 11.0, 2.4, 10.2)
    P.rampe(ci, 0.7 - 0.24 * (X - cx_) / 1.2, R_PAPIER, 0.5)
    P.rect(cx_ - 1.6, cy_ - 8.0, 0.6, 3.0, R_PAPIER[4])                                             # une coulure
    P.rect(cx_ + 0.9, cy_ - 10.0, 0.6, 2.0, R_PAPIER[3])
    P.trait(cx_, cy_ - 11.0, cx_, cy_ - 12.0, ENCRE)
    fd = 0.4 * onde(p * 2)
    halo(P, cx_, cy_ - 13.6, 7.0, LU4, 0.4)
    P.poly([(cx_ - 0.9, cy_ - 11.6), (cx_ + 0.9, cy_ - 11.6), (cx_ + fd, cy_ - 15.6)], LU3)
    P.poly([(cx_ - 0.5, cy_ - 11.6), (cx_ + 0.5, cy_ - 11.6), (cx_ + fd * 0.6, cy_ - 14.0)], LU5)
    bo = m_rect(P, 141.0, 49.0, 7.0, 3.0)                                                         # la boîte d'allumettes, entrouverte
    P.rampe(bo, 0.5 + 0.2 * (Y < 49.8) - 0.03 * (X - 141.0), R_TOILE, 0.5)
    P.rect(141.0, 50.0, 7.0, 0.5, R_PLATRE[3])
    P.rect(148.0, 49.6, 2.0, 2.0, R_BOIS[6])
    for k in range(3):
        P.trait(148.4, 49.9 + k * 0.6, 152.0, 49.6 + k * 0.6, R_BOIS[7])
        P.point(152.2, 49.6 + k * 0.6, LU2)
    P.trait(136.0, 51.4, 140.0, 50.6, R_CUIVRE[2], 3)                                              # le bâton de cire à cacheter
    P.point(136.0, 51.2, R_CUIVRE[4])

    # ---- La tasse de thé, sa soucoupe ; elle fume dans le soleil.
    tx, ty = 177.0, 52.0
    P.rampe(m_ell(P, tx, ty, 7.0, 1.7), 0.6 - 0.2 * (X - tx) / 7.0, R_PAPIER, 0.5)
    P.ell(tx, ty + 0.5, 7.0, 1.6, R_PAPIER[1], cond=Y > ty + 0.6)
    tasse = m_rect(P, tx - 4.4, ty - 8.0, 8.8, 7.6) | m_ell(P, tx, ty - 0.6, 4.4, 1.3)
    P.rampe(tasse, 0.66 - 0.3 * (X - tx) / 4.4, R_TOILE, 0.5)
    P.remplir(tasse & (np.abs(Y - ty + 5.6) < 0.4), R_TOILE[5])                                     # un filet blanc
    P.rampe(m_ell(P, tx, ty - 8.0, 4.4, 1.3), 0.8, R_PAPIER, 0.5)
    P.ell(tx, ty - 7.9, 3.5, 0.8, R_BOIS[4])                                                       # le thé
    P.ell(tx - 1.0, ty - 8.0, 1.4, 0.3, R_BOIS[6])
    P.courbe([(tx + 4.2, ty - 6.6), (tx + 7.6, ty - 5.0), (tx + 4.2, ty - 2.2)], R_TOILE[2], P.ep(0.7))
    P.trait(tx - 6.4, ty - 0.6, tx - 3.6, ty + 0.4, R_ETAIN[4])                                    # la cuillère
    fumerolle(P, tx, ty - 9.4, h=15.0, n=4, d=0.2, coul=T.CIEL[11], force=0.45, large=1.0)

    # ---- Sur le devant du bureau : le buvard et une réponse commencée, le porte-plume, un timbre pas encore collé,
    # la boussole (on part), la loupe, des taches d'encre.
    buv = P.masque_poly([(16.0, 61.0), (58.0, 59.4), (63.0, 74.0), (13.0, 76.6)])
    P.rampe(buv, (0.42 + 0.1 * (pg.fbm(X / 4.0, Y / 2.0, 2, 523) - 0.5)) * (0.5 + Lb), [VI1, VI1, VI2, T.VIOLET, BM3], 0.5)
    pap = P.masque_poly([(19.0, 62.4), (52.0, 61.0), (56.0, 71.6), (17.4, 74.0)])
    P.rampe(pap, 0.56 * (0.42 + Lb), R_PAPIER, 0.5)
    for j in range(4):
        P.trait(22.0, 64.6 + j * 2.1, 48.0 - (14.0 if j == 3 else j * 1.5), 63.6 + j * 2.1, R_NUIT[2])
    lisere(P, buv, R_BOIS[1], 0, 1)
    P.trait(40.0, 71.0, 62.0, 66.6, R_BOIS[2], 3)                                                  # le porte-plume
    P.trait(40.0, 70.6, 62.0, 66.2, R_BOIS[6], 1)
    P.trait(36.0, 71.8, 40.0, 71.0, R_ETAIN[4], 2)
    P.point(35.6, 72.0, NU0)
    tim = P.masque_poly([(66.0, 67.0), (73.0, 66.2), (74.0, 71.0 + 0.3 * onde(p)), (67.0, 72.0)])   # le timbre : son coin se soulève
    P.rampe(tim, 0.8, R_PAPIER, 0.5)
    P.remplir(P.masque_poly([(67.2, 68.0), (72.2, 67.4), (72.8, 70.4), (68.0, 71.0)]), R_TOILE[2])
    P.point(70.0, 69.0, LU4, 2)
    for i, (x, y, rx, ry) in enumerate(((104.0, 71.0, 3.0, 1.0), (109.6, 72.6, 1.0, 0.4), (84.0, 76.0, 1.6, 0.5))):               # l'encre renversée
        P.ell(x, y, rx, ry, NU0)
        P.point(x - rx * 0.4, y - ry * 0.4, NU3 if i else BM2)
    bs = (124.0, 69.0)                                                                            # la boussole
    P.rampe(m_ell(P, bs[0], bs[1], 6.2, 3.0), 0.5 - 0.3 * (X - bs[0]) / 6.2 - 0.2 * (Y - bs[1]) / 3.0, [GO1, LAITON, LAITON2, LU5], 0.5)
    P.rampe(m_ell(P, bs[0], bs[1] - 0.3, 5.0, 2.2), 0.76 - 0.1 * (X - bs[0]) / 5.0, R_PAPIER, 0.5)
    P.ell(bs[0], bs[1] + 3.0, 6.2, 0.9, R_BOIS[2], cond=Y > bs[1] + 2.4)
    an = 0.5 + 0.24 * onde(p * 2, 0.1) * (1 if p < 0.5 else 0.3)
    P.trait(bs[0], bs[1] - 0.3, bs[0] + 4.0 * math.cos(an), bs[1] - 0.3 - 1.7 * math.sin(an), LU2)
    P.trait(bs[0], bs[1] - 0.3, bs[0] - 4.0 * math.cos(an), bs[1] - 0.3 + 1.7 * math.sin(an), NU2)
    P.point(bs[0], bs[1] - 0.3, ENCRE)
    P.ell(bs[0] + 7.0, bs[1] - 1.0, 1.4, 1.0, LAITON)                                              # son anneau
    P.ell(bs[0] + 7.0, bs[1] - 1.0, 0.7, 0.4, R_BOIS[3])
    lp = (166.0, 70.0)                                                                            # la loupe
    P.trait(lp[0] + 5.0, lp[1] + 2.0, lp[0] + 17.0, lp[1] + 6.4, R_BOIS[2], P.ep(1.1))
    P.trait(lp[0] + 5.0, lp[1] + 1.6, lp[0] + 17.0, lp[1] + 6.0, R_BOIS[5], 1)
    P.rampe(m_ell(P, lp[0], lp[1], 6.6, 3.2), 0.5 - 0.3 * (X - lp[0]) / 6.6, [GO1, LAITON, LAITON2, LU5], 0.5)
    lent = m_ell(P, lp[0], lp[1], 5.4, 2.4)
    P.rampe(lent, (0.74 + 0.12 * np.sin(z * 20.0)) * (Lb + 0.24), R_BOIS[3:], 0.5)                    # le fil du bois, grossi
    P.remplir(lent & m_ell(P, lp[0] - 2.0, lp[1] - 0.9, 2.2, 0.7), BLANC if int(p * 8) % 5 == 0 else T.CIEL[10])
    for i in range(8):                                                                            # des miettes de biscuit
        P.point(150.0 + 30.0 * hz(i, 1, 524), 57.0 + 8.0 * hz(i, 2, 524), R_BOIS[7] if i % 2 else R_BOIS[8])

    # ================================================================================================== premier plan
    tab.plan("premier", 1.0)
    # À gauche, un gros dictionnaire debout, tout près, à contre-jour ; son signet de soie.
    dic = P.masque_poly([(-6.0, 80.0), (-6.0, 30.0), (7.0, 28.0), (11.0, 80.0)])
    P.rampe(dic, 0.2 + 0.03 * (X + 6.0) + 0.1 * (pg.fbm(X / 2.0, Y / 9.0, 2, 525) - 0.5), [R_BOIS[0], VI1, VI1, VI2], 0.5)
    lisere(P, dic, T.VIOLET, 1, 0, cond=Y > 34)
    for yy in (38.0, 44.0, 70.0):
        P.remplir(dic & (np.abs(Y - yy + 0.14 * (X + 6.0)) < 0.5), LAITON)
    P.remplir(P.masque_poly([(-6.0, 30.0), (7.0, 28.0), (6.4, 26.6), (-6.0, 28.4)]), R_PAPIER[2])     # la tranche de tête
    sg = 0.4 * onde(p, 0.3)
    P.courbe([(3.0, 27.6), (5.0 + sg, 34.0), (4.0 + sg * 1.6, 41.0)], LU2, 2)                         # le signet
    # En bas, le bord du bureau dans l'ombre ; à droite, le pied d'une lampe de laiton, éteinte.
    P.rampe(Y > 78.2, 0.2 + 0.06 * (pg.fbm(X / 9.0, Y, 2, 526) - 0.5), R_BOIS, 0.5)
    lpd = (m_ell(P, 190.0, 80.0, 12.0, 4.4) & (Y > 76.4)) | m_rect(P, 189.2, -6.0, 2.6, 84.0) | m_ell(P, 190.5, 76.6, 4.0, 1.6)
    P.rampe(lpd, 0.3 + 0.3 * np.clip(1 - (X - 180.0) / 10.0, 0, 1) * (Y > 76.0) + 0.34 * (X < 190.2) * (Y <= 76.0), [R_BOIS[0], GO1, LAITON, LAITON2, LU5], 0.5)
    lisere(P, lpd, LU5, -1, 0, cond=(pg.fbm(Y / 3.0, 0 * Y, 2, 527) > 0.36))
    for yy in (20.0, 21.4, 60.0):                                                                 # ses bagues
        P.rect(188.8, yy, 3.4, 0.8, GO1)
    abat = P.masque_poly([(174.0, -4.0), (198.0, -2.4), (198.0, -16.0), (181.0, -16.0)])
    P.rampe(abat, 0.22 + 0.016 * (186.0 - X) + 0.1 * (pg.fbm(X / 6.0, Y / 2.0, 2, 529) - 0.5), R_TOILE[:4], 0.5)
    lisere(P, abat, R_TOILE[4], 0, 1)
    P.trait(180.0, -3.0, 180.0 + 0.3 * onde(p, 0.4), 3.0, LAITON)                                  # la chaînette
    P.ell(180.0 + 0.3 * onde(p, 0.4), 3.8, 0.8, 0.9, LAITON2)
    # La poussière dans le rai de soleil.
    for i in range(26):
        if (p + hz(i, 1, 528)) % 1.0 < 0.6:
            gx = 40.0 + 110.0 * hz(i, 2, 528) + 0.8 * onde(p, hz(i, 4, 528))
            gy = wy + wh * 0.5 + (gx - wx - ww * 0.5) * 0.52 + (hz(i, 3, 528) - 0.5) * 26.0 + 0.5 * onde(p, 0.25 + hz(i, 5, 528))
            P.point(gx, gy, LU5 if hz(i, 6, 528) < 0.5 else BLANC)


# =====================================================================================================================
# Le quai de Trébrume : sept heures du soir, la brume. On est sur le quai, au coin de l'auberge (son enseigne, sa fenêtre
# jaune). Au large, la Dent-Creuse : une grande dent noire sur son rocher, éteinte, devant une lune voilée (la clé).
# Sur le quai : la Puce tirée au sec, que Tudal goudronne (l'éraflure fraîche sur son flanc), le brasero et le pot de
# goudron, les casiers, le panneau du Passe-Pied, le fanal. Le quai est le sol (y = 66) ; la mer est juste derrière.
# Repères de la scène : le phare (130..156, 0..50), l'étrave de la Puce où se pose le chat (112, 52), un rond dans
# l'eau (60, 60), le fanal des papillons de nuit (176, 30).
# =====================================================================================================================
def paves(P, m, Lc, Lw, fx, yh, larg=2.8, prof=4.0, graine=0):
    """Un quai de dalles de granit en perspective, mouillé : chaque dalle son ton, bombée, des joints noirs ; la
    lumière froide de la lune et la lumière chaude des feux se partagent les pierres."""
    X, Y = P.X, P.Y
    dy = np.maximum(Y - yh, 0.25)
    z = 60.0 / dy * prof
    r = np.floor(z)
    fz = z - r
    uu = (X - fx) / dy * 10.0 / larg + 7.3 * hz(r, 1, graine)
    cu = np.floor(uu)
    fu = uu - cu
    ton = 0.74 + 0.5 * hz(cu, r, graine + 3)
    grain = pg.fbm(X / 0.9, Y / 0.9, 2, graine + 4) - 0.5
    lj = 0.4 / (larg * dy / 10.0)
    hj = 0.4 / (dy * dy / (60.0 * prof))
    joint = (fu < lj) | (fz > 1 - hj)
    bombe = 0.16 * (0.5 - fz) + 0.1 * (0.5 - np.abs(fu - 0.5))          # le haut de la dalle accroche la lune
    alb = 0.62 * (ton + 0.3 * grain) + bombe
    flaque = (pg.fbm(X / 7.0, (Y - yh) / 1.3, 3, graine + 5) > 0.63)    # l'eau qui reste dans les creux
    alb = np.where(flaque, alb * 0.55 + 0.3 * Lw + 0.16, alb)
    alb = np.where(joint & ~flaque, 0.22, alb)
    v = alb * (Lc + Lw)
    chaud = Lw > 0.5 * Lc
    P.rampe(m & ~chaud, v, R_FROID, 0.5)
    P.rampe(m & chaud, v, R_GRANIT, 0.5)
    return flaque


def dent_creuse(P, x, y, h, lune, eteint=True):
    """Le phare de la Dent-Creuse, de près : (x, y) le pied de la tour, h sa hauteur. Une tour noire, effilée, sa galerie,
    sa lanterne vitrée, son toit pointu ; le rocher luisant et l'écume à son pied. lune : (x, y) de la lumière."""
    X, Y = P.X, P.Y
    k = h / 40.0
    cote = 1 if lune[0] > x else -1
    # Le rocher : une échine déchiquetée, des pans, l'écume.
    def crete(xx):
        return y + 0.8 * k - 5.2 * k * np.exp(-((xx - x) / (9.0 * k)) ** 2) + 1.6 * k * (pg.fbm(xx / (2.2 * k), 0.3 + 0 * xx, 3, 701) - 0.5) * 2 \
            + 0.012 * (xx - x) ** 2 / k
    roc = (Y > crete(X)) & (Y < y + 7.5 * k) & (np.abs(X - x) < 19 * k)
    pan = pg.fbm(X / (3.0 * k) + 0.4 * (Y - y), Y / (2.4 * k), 3, 702)
    P.rampe(roc, 0.16 + 0.34 * pan + 0.1 * cote * (X - x) / (19 * k) - 0.04 * (Y - y), [ENCRE, NU0, NU1, GR1, GR2, GR3], 0.5)
    lis = P.crete(roc) & (pg.fbm(X / 2.0, 0 * X, 2, 703) > 0.4) & ((X - x) * cote > -4 * k)
    P.a[lis] = BM1
    # La tour.
    def demi(yy):
        t = np.clip((y - yy) / (h * 0.78), 0, 1)
        return (4.4 - 1.7 * t ** 0.8) * k
    tour = (np.abs(X - x) < demi(Y)) & (Y <= y + 0.6 * k) & (Y > y - h * 0.78)
    nx = (X - x) / np.maximum(demi(Y), 0.1)
    P.rampe(tour, 0.12 + 0.26 * np.clip(cote * nx - 0.45, 0, 1) + 0.06 * (pg.fbm(X / 1.4, Y / 5.0, 2, 704) - 0.5), [ENCRE, NU0, NU1, NU2, NU3], 0.5)
    for j in range(1, 6):                                       # les assises de granit, à peine visibles
        yy = y - h * 0.78 * j / 6.0
        P.remplir(tour & (np.abs(Y - yy) < 0.22) & (cote * nx > 0.1), NU0)
    lisere(P, tour, BM1 if True else NU3, cote, 0, cond=(pg.fbm(Y / 3.0, 0 * Y, 2, 705) > 0.36))            # le liseré de lune
    for j, t in enumerate((0.16, 0.36, 0.56)):                  # les meurtrières
        P.rect(x - 0.5 * k - cote * 0.6 * k, y - h * t - 1.6 * k, 1.0 * k, 2.0 * k, ENCRE)
        P.rect(x - 0.5 * k - cote * 0.6 * k, y - h * t - 1.6 * k, 0.4, 2.0 * k, NU2)
    P.rect(x - 1.2 * k, y - 2.8 * k, 2.4 * k, 3.2 * k, ENCRE)     # la porte de fer
    # La galerie, la lanterne, le toit.
    gy = y - h * 0.78
    P.rect(x - 4.2 * k, gy - 0.9 * k, 8.4 * k, 1.2 * k, ENCRE)
    P.rect(x - 4.2 * k, gy - 0.9 * k, 8.4 * k, 0.4, NU2)
    for dx in np.arange(-4.0, 4.01, 1.0):
        P.rect(x + dx * k - 0.2, gy - 2.6 * k, 0.4, 1.8 * k, ENCRE)
    P.rect(x - 4.2 * k, gy - 2.8 * k, 8.4 * k, 0.4, NU1)
    lant = m_rect(P, x - 2.4 * k, gy - 6.4 * k, 4.8 * k, 5.6 * k)
    P.rampe(lant, 0.2 + 0.4 * np.clip(cote * (X - x) / (2.4 * k), -1, 1) * 0.5 + 0.1, [NU0, NU1, NU2, NU3, NU4], 0.5)
    for dx in (-2.4, -0.8, 0.8, 2.2):
        P.rect(x + dx * k, gy - 6.4 * k, 0.4, 5.6 * k, ENCRE)
    P.rect(x - 2.4 * k, gy - 3.8 * k, 4.8 * k, 0.4, ENCRE)
    if (P.p * 2) % 1.0 < 0.3:
        P.point(x + cote * 1.4 * k, gy - 5.2 * k, BM4)            # la vitre renvoie un peu de lune
    P.poly([(x - 3.2 * k, gy - 6.4 * k), (x + 3.2 * k, gy - 6.4 * k), (x, gy - 9.8 * k)], ENCRE)
    P.trait(x + cote * 0.4, gy - 9.4 * k, x + cote * 3.0 * k, gy - 6.5 * k, NU2)
    P.trait(x, gy - 9.8 * k, x, gy - 11.6 * k, ENCRE)
    P.point(x, gy - 11.9 * k, NU1)
    return roc | tour


@decor("phare-eteint", "port-trebrume", soleil=(163.0, 13.0), tons=PHARE, nom="Le quai de Trébrume", matiere=True)
def port_trebrume(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    LUNE = (163.0, 13.0)
    HOR, QY = 45.0, 62.0                                        # l'horizon, le bord du quai
    vac = 1.0 + 0.1 * onde(p * 2) + 0.05 * onde(p * 3, 0.2)

    # ============================================================================================================ le ciel
    tab.plan("ciel", 0.0)
    P.horizon, P.ciel_haut, P.halo = HOR, 0.06, 0.34
    tout = np.ones(X.shape, dtype=bool)
    vc = pg.valeur_ciel(P, X, Y)
    P.rampe(tout, 0.03 + 0.6 * vc, T.CIEL, 0.75)
    for i in range(46):                                         # quelques étoiles, là où la brume les laisse passer
        ex, ey = 198.0 * hz(i, 1, 708) - 3.0, -15.0 + 30.0 * hz(i, 2, 708) ** 1.6
        if math.hypot(ex - LUNE[0], ey - LUNE[1]) > 22.0 and (p + hz(i, 3, 708)) % 1.0 < 0.7:
            P.point(ex, ey, T.CIEL[8] if hz(i, 4, 708) < 0.4 else T.CIEL[5])
    dl = np.hypot(X - LUNE[0], Y - LUNE[1])
    voile(P, dl < 12.0, T.CIEL[9], 0.5 * np.clip(1 - dl / 12.0, 0, 1) ** 1.4, lumiere=False)
    P.remplir(dl < 3.4, T.CIEL[10])
    P.remplir(dl < 2.9, T.SOL)
    P.remplir((dl < 2.9) & (pg.fbm(X / 1.6, Y / 1.6, 2, 711) > 0.6), T.CIEL[10])                    # ses mers
    tab.plan("nuages", 0.08)
    def bancs(y, epais, seuil, graine, tons, zone=None):
        d = pg.fbm((X + 0.6 * onde(p, 0.01 * graine)) / 34.0, Y / 2.2, 4, graine) - seuil - 0.2 * ((Y - y) / epais) ** 2
        dessous = d - (pg.fbm((X + 0.6 * onde(p, 0.01 * graine)) / 34.0, (Y + 1.2) / 2.2, 4, graine) - seuil - 0.2 * ((Y + 1.2 - y) / epais) ** 2)
        prox = np.exp(-(np.hypot(X - LUNE[0], (Y - LUNE[1]) * 1.6) / 46.0) ** 2)
        P.rampe((d > 0) if zone is None else ((d > 0) & zone), 0.16 + 2.2 * dessous + 0.62 * prox + 1.0 * d, tons, 0.6)

    def nappe(y, epais, graine, tons, zone=None, seuil=0.62):
        # Un banc de brume : une bande pleine au milieu, déchirée sur ses bords, plus claire là où la lune la touche.
        def dens(yy):
            return (0.4 + pg.fbm((X + 1.2 * onde(p, 0.013 * graine)) / 17.0, yy / 2.6, 3, graine)) * np.exp(-((yy - y - 1.2 * np.sin(X / 23.0 + graine)) / epais) ** 2) - seuil
        d = dens(Y)
        prox = np.exp(-(np.hypot(X - LUNE[0], (Y - LUNE[1]) * 1.4) / 60.0) ** 2)
        m = d > 0
        if zone is not None:
            m &= zone
        P.rampe(m, 0.22 + 1.5 * d + 1.6 * (d - dens(Y + 1.0)) + 0.42 * prox, tons, 0.6)

    bancs(-7.0, 8.0, 0.55, 520, T.CIEL[1:7])
    bancs(12.0, 5.0, 0.6, 521, T.CIEL[3:10])                                                       # un voile passe devant la lune
    bancs(27.0, 6.0, 0.56, 522, T.CIEL[3:9])
    bancs(38.0, 4.0, 0.57, 523, T.CIEL[4:10])

    # ======================================================================================================== les lointains
    tab.plan("lointains", 0.2)
    # Une pointe de terre très loin, à gauche ; la Mâchoire (des récifs) ; puis la Dent-Creuse.
    f1 = lambda x: HOR - 0.5 - 4.5 * np.clip((60 - x) / 60.0, 0, 1) ** 0.7 - 1.4 * pg.fbm(x / 9.0, 0 * x + 0.5, 3, 712)
    P.remplir((Y > f1(X)) & (Y < HOR + 0.5) & (X < 66), T.CIEL[5])
    # La Mâchoire : une rangée de récifs bas, déchiquetés, et l'écume qui s'y brise.
    hm = 13.0 * np.clip(pg.fbm(X / 2.0, 0 * X + 0.7, 3, 713) - 0.36, 0, 1) * np.clip(1 - np.abs(X - 106.0) / 17.0, 0, 1) ** 0.5
    mach = (Y > HOR + 0.4 - hm) & (Y < HOR + 0.8) & (hm > 0.3)
    P.rampe(mach, 0.2 + 0.5 * (pg.fbm(X / 1.2, Y / 1.2, 2, 7131) - 0.3), [ENCRE, NU0, NU1, NU2], 0.5)
    lisere(P, mach, T.CIEL[6], 1, 0)
    for i in range(6):
        if (p + 0.17 * i) % 1.0 < 0.5:
            ex = 92.0 + i * 5.0
            P.trait(ex - 1.4, HOR + 0.9, ex + 2.0, HOR + 0.9, BM4)
    dent_creuse(P, 143.0, 43.4, 41.0, LUNE)
    for i in range(6):                                          # l'écume au pied du rocher
        t = (p + i / 6.0) % 1.0
        ex = 127.0 + i * 6.4 + 1.5 * math.sin(i * 2.0)
        P.trait(ex - 2.0 - t, HOR + 0.6 + (i % 2) * 0.5, ex + 2.0 + t, HOR + 0.6 + (i % 2) * 0.5, BM4 if t < 0.5 else BM2)
    for i in range(4):                                          # les balises du Passe-Pied, recouvert par la mer
        bx_ = 151.0 + i * 8.0
        by_ = HOR + 2.6 + i * 3.4
        P.trait(bx_, by_, bx_ + 0.2 * onde(p, 0.2 * i), by_ - 3.0 - i * 1.2, ENCRE, 1 if i < 2 else 2)
        P.rect(bx_ - 0.6, by_ - 3.8 - i * 1.2, 1.2 + 0.4 * (i > 1), 0.8, LU2 if i % 2 else BM4)
    nappe(44.4, 1.7, 524, T.CIEL[6:11])                                                       # la brume efface le pied du rocher
    nappe(34.6, 1.6, 529, T.CIEL[5:10], zone=X < 128, seuil=0.74)
    for i in range(5):                                          # les goélands, haut dans le soir
        goeland(P, 100 + 9 * i + 3 * onde(p, 0.2 * i), 4 + 6 * hz(i, 1, 714) + onde(p, 0.3 * i), pose=False)

    # ================================================================================================ le port et le quai
    tab.plan("moyen", 0.5)
    # ---- Le village, de l'autre côté du bassin : des maisons de granit serrées, des toits d'ardoise, des fenêtres.
    R_MUR = [ENCRE, NU0, NU1, GR1, NU2, GR2, NU3, GR3]
    R_LOIN = [NU1, NU2, NU2, NU3, NU3, NU4, BM1, BM2]
    # (x, largeur, y du toit, rang : 0 = le fond, dans la brume ; 1 = devant)
    maisons = ((-9.0, 13.0, 15.0, 0), (9.0, 12.0, 11.0, 0), (26.0, 11.0, 14.0, 0), (41.0, 12.0, 18.0, 0), (54.0, 9.0, 24.0, 0),
               (-7.0, 15.0, 26.0, 1), (6.0, 11.0, 21.0, 1), (16.0, 14.0, 27.0, 1), (29.0, 12.0, 23.0, 1), (40.0, 13.0, 29.0, 1), (52.0, 11.0, 33.0, 1))
    P.rect(21.0, 2.0, 2.6, 12.0, NU1)                                                             # le clocher, derrière
    P.poly([(20.4, 2.0), (24.2, 2.0), (22.3, -6.0)], NU0)
    P.trait(22.9, -4.0, 24.0, 1.8, NU3)
    P.rect(21.8, 4.6, 1.0, 1.6, NU0)
    for i, (hx, hw, top, rang) in enumerate(maisons):
        base = HOR + 0.6
        mur = m_rect(P, hx, top, hw, base - top)
        pierre_ = pg.fbm(X / 1.1, Y / 0.9, 2, 720 + i) - 0.5
        r_m = R_MUR if rang else R_LOIN
        P.rampe(mur, 0.3 + 0.1 * (X - hx) / hw + 0.2 * pierre_ - 0.004 * (Y - top) + 0.06 * hz(i, 0, 7201), r_m, 0.5)
        P.rampe(m_rect(P, hx + hw - 1.2, top, 1.2, base - top), 0.66, r_m, 0.5)                              # l'arête à la lune
        haut_t = hw * 0.44
        pignon = P.masque_poly([(hx - 1.0, top), (hx + hw + 1.0, top), (hx + hw * 0.5, top - haut_t)])
        ard = ((np.floor(Y / 0.82) + np.floor((X + (np.floor(Y / 0.82) % 2) * 0.8) / 1.6)) % 2 == 0)
        P.rampe(pignon, 0.2 + 0.1 * ard * rang + 0.34 * (X > hx + hw * 0.5), [ENCRE, NU0, VI1, NU2, VI2, NU3] if rang else [NU1, NU2, NU3, NU3, NU4, BM1], 0.5)
        lisere(P, pignon, BM1 if rang else NU4, 1, 0, cond=X > hx + hw * 0.5)
        P.rect(hx - 1.0, top, hw + 2.0, 0.5, ENCRE if rang else NU1)                                               # l'ombre de l'égout
        cx_ = hx + hw * (0.2 if i % 2 else 0.72)                 # la cheminée, sa fumée
        P.rect(cx_, top - haut_t * 0.9 - 1.0, 2.0, haut_t * 0.7, GR1 if rang else NU1)
        P.rect(cx_ + 1.4, top - haut_t * 0.9 - 1.0, 0.6, haut_t * 0.7, GR3 if rang else NU3)
        P.rect(cx_ - 0.3, top - haut_t * 0.9 - 1.6, 2.6, 0.7, NU0)
        if i in (1, 6, 8, 10):
            fumerolle(P, cx_ + 1.0, top - haut_t * 0.9 - 2.4, h=11.0, n=3, d=0.2 * i, coul=T.CIEL[6], force=0.36, large=0.9)
        nf = max(2, int(hw // 4.0))
        for j in range(int((base - top - 2.5) // 6.0)):
            for q in range(nf):
                fx_ = hx + 1.6 + q * (hw - 5.4) / max(1, nf - 1)
                fy_ = top + 2.2 + j * 6.0
                allume = hz(i * 7 + j, q, 721) < (0.5 if rang else 0.3)
                vif = (p + hz(i, j * 3 + q, 722)) % 1.0 < 0.93
                if allume:
                    dd = np.hypot(X - fx_ - 1.1, Y - fy_ - 1.6)
                    voile(P, mur & (dd < 3.4), LU2, 0.3 * (1 - dd / 3.4), lumiere=True)
                P.rect(fx_, fy_, 2.2, 3.2, (LU4 if vif else LU3) if allume else (NU0 if rang else NU1))
                if allume:
                    P.rect(fx_ + 1.0, fy_, 0.4, 3.2, LU2)
                    P.rect(fx_, fy_ + 1.4, 2.2, 0.4, LU2)
                else:
                    P.point(fx_ + 1.4, fy_ + 0.4, NU3)
                    P.rect(fx_ - 0.8, fy_, 0.8, 3.2, (VOLET, VI2, NU3)[(i + q) % 3])                 # un volet
                P.rect(fx_ - 0.4, fy_ + 3.2, 3.0, 0.4, GR3 if rang else NU3)                       # l'appui
        if rang:                                                                                  # la porte
            dx_ = hx + hw * 0.5 - 1.0 + (2.6 if i % 2 else -2.6)
            P.rect(dx_, base - 4.6, 2.4, 4.6, NU0)
            P.rect(dx_, base - 4.6, 2.4, 0.4, GR3)
    nappe(41.0, 2.2, 526, T.CIEL[5:9], zone=X < 78)                                          # la brume entre les maisons
    # Leur quai, la cale, une digue qui s'avance et son petit feu de port.
    rive = (Y >= HOR - 0.4) & (Y < HOR + 2.0) & (X < 68)
    appareil(P, rive, 0.7 + 0 * X, LUNE, lh=1.3, lw=3.4, graine=723, rampe=[ENCRE, NU0, NU1, GR1, GR2, GR3], alb=0.6)
    digue = P.masque_poly([(60.0, HOR - 0.8), (86.0, HOR + 0.2), (86.0, HOR + 2.0), (60.0, HOR + 2.0)])
    appareil(P, digue, 0.74 + 0 * X, LUNE, lh=1.2, lw=3.0, graine=724, rampe=[ENCRE, NU0, NU1, GR1, GR2, GR3], alb=0.62)
    lisere(P, digue | rive, GR2, 0, -1, cond=pg.fbm(X / 2.0, 0 * X, 2, 725) > 0.42)
    P.rect(83.4, HOR - 5.6, 1.4, 5.8, GR1)                       # le feu du musoir
    P.rect(84.2, HOR - 5.6, 0.6, 5.8, GR3)
    feu_port = (p * 2) % 1.0 < 0.55
    P.rect(83.2, HOR - 7.4, 1.8, 1.8, LU5 if feu_port else LU1)
    if feu_port:
        halo(P, 84.1, HOR - 6.5, 6.0, LU3, 0.5)
    P.poly([(82.8, HOR - 7.4), (85.4, HOR - 7.4), (84.1, HOR - 8.8)], ENCRE)
    for i, mx_ in enumerate((8.0, 22.0, 33.0, 47.0)):            # des mâts, le long de leur quai
        dx = 0.4 * onde(p, 0.23 * i)
        P.trait(mx_ + dx, HOR - 13.0 - 3 * (i % 2), mx_, HOR + 0.6, ENCRE)
        P.trait(mx_ + dx * 0.7 - 2.0, HOR - 9.0 - 3 * (i % 2), mx_ + dx * 0.7 + 2.0, HOR - 9.4 - 3 * (i % 2), ENCRE)
        P.poly([(mx_ - 4.0, HOR - 0.6), (mx_ + 4.6, HOR - 0.8), (mx_ + 3.4, HOR + 1.2), (mx_ - 3.0, HOR + 1.2)], NU0)
        P.trait(mx_ - 4.0, HOR - 0.7, mx_ + 4.6, HOR - 0.9, GR3)

    # ---- La mer : le miroir du soir, le chemin de lune, les feux qui s'y cassent.
    pg.miroir(P, tab.derriere(), HOR + 1.2, fonce=(50.0, 12.0), eclats=0.9, rides=0.09, graine=525, ronds=((60.0, 60.0, 0.0), (128.0, 55.0, 0.5)))
    eau = (Y > HOR + 2.0) & (Y < QY)
    for i, (hx, hw, top, ton) in enumerate(maisons[5:]):         # les fenêtres jaunes, étirées dans l'eau
        for q in range(2):
            rx = hx + 2.6 + q * (hw - 5.4)
            if hz(i, q, 726) < 0.7:
                for j in range(7):
                    yy = HOR + 2.6 + j * 1.5
                    if (j + int(p * 8) + i) % 3:
                        dx = 0.4 * ((j + i) % 2)
                        P.trait(rx - 0.8 + dx, yy, rx + 0.8 + dx, yy, LU3 if j < 2 else (LU2 if j < 5 else LU1))
    # Un sloop au mouillage, son feu de mât ; plus loin, un canot ; au large, un bateau qui rentre dans la brume.
    sx_, sy_ = 70.0, 53.4 + 0.3 * onde(p, 0.1)
    roul = 0.5 * onde(p, 0.35)
    cq = P.masque_poly([(sx_ - 9.0, sy_ - 2.2), (sx_ + 10.4, sy_ - 2.8), (sx_ + 8.0, sy_ + 0.9), (sx_ - 7.4, sy_ + 0.9)])
    P.rampe(cq, 0.2 + 0.2 * (Y - sy_ + 2.4) / -3.0 + 0.3 + 0.03 * (X - sx_), [ENCRE, NU0, NU1, NU2, NU3], 0.5)
    P.trait(sx_ - 9.0, sy_ - 2.3, sx_ + 10.4, sy_ - 2.9, BM1)
    P.rect(sx_ - 4.0, sy_ - 4.4, 6.0, 2.0, NU1)                  # le rouf
    P.rect(sx_ - 4.0, sy_ - 4.4, 6.0, 0.4, GR3)
    P.rect(sx_ - 2.6, sy_ - 3.6, 1.2, 0.9, LU3)                  # un hublot allumé
    P.trait(sx_ + 1.0 + roul, sy_ - 23.0, sx_ + 0.4, sy_ - 2.6, ENCRE, 2)
    P.trait(sx_ + 1.0 + roul, sy_ - 22.0, sx_ + 10.0, sy_ - 2.9, NU1)
    P.trait(sx_ + 1.0 + roul, sy_ - 22.0, sx_ - 8.6, sy_ - 2.4, NU1)
    P.trait(sx_ + 0.6, sy_ - 6.0, sx_ - 7.0, sy_ - 5.4, GR1, 2)   # la bôme, la voile ferlée
    P.trait(sx_ + 0.6, sy_ - 6.6, sx_ - 6.4, sy_ - 6.0, BM2)
    halo(P, sx_ + 1.0 + roul, sy_ - 23.4, 5.0, LU3, 0.5)
    P.point(sx_ + 0.8 + roul, sy_ - 23.6, LU5, 2)
    for j in range(5):
        if (j + int(p * 8)) % 3:
            P.trait(sx_ - 0.8 + 0.6 * math.sin(j + 6.283 * p), sy_ + 2.0 + j * 1.5, sx_ + 2.0 + 0.6 * math.sin(j + 6.283 * p), sy_ + 2.0 + j * 1.5, LU2 if j > 1 else LU3)
    P.courbe([(sx_ - 4.0, sy_ - 2.0), (62.0, 58.0 + 0.4 * onde(p)), (61.0, 60.6)], GO2, 1)          # son amarre, jusqu'à la bitte
    cx_, cy_ = 124.0, 51.6 + 0.25 * onde(p, 0.6)
    P.poly([(cx_ - 5.0, cy_ - 1.2), (cx_ + 5.6, cy_ - 1.5), (cx_ + 4.0, cy_ + 0.7), (cx_ - 4.0, cy_ + 0.7)], NU0)
    P.trait(cx_ - 5.0, cy_ - 1.3, cx_ + 5.6, cy_ - 1.6, BM1)
    P.trait(cx_ - 1.0, cy_ - 1.2, cx_ + 2.0, cy_ - 2.6, GR3)                                      # un aviron
    lx_, ly_ = 104.0 + 1.0 * onde(p, 0.2), HOR + 0.4
    P.poly([(lx_ - 2.4, ly_ - 0.8), (lx_ + 2.8, ly_ - 1.0), (lx_ + 2.0, ly_ + 0.4), (lx_ - 2.0, ly_ + 0.4)], T.CIEL[3])
    P.trait(lx_, ly_ - 1.0, lx_, ly_ - 5.0, T.CIEL[3])
    if (p + 0.3) % 1.0 < 0.75:
        P.point(lx_, ly_ - 5.4, LU4)
        halo(P, lx_, ly_ - 5.2, 3.0, LU3, 0.4)
    nappe(48.4, 1.5, 527, T.CIEL[5:10], seuil=0.7)                                                        # des nappes sur l'eau
    nappe(56.6, 1.2, 528, T.CIEL[4:8], zone=((X > 30) & (X < 84)) | (X > 114), seuil=0.74)

    # ---- Le quai : les dalles mouillées, la lune dessus, les flaques où tremblent les feux.
    quai = Y >= QY
    Lc = 0.52 + 0.3 * np.exp(-((X - LUNE[0] + 0.5 * (Y - QY)) / 30.0) ** 2) - 0.008 * (Y - QY)
    Lw = lumiere(P, [(176.0, 66.0, 13.0, 0.95), (121.0, 66.0, 9.0, 0.9 * vac), (4.0, 68.0, 16.0, 0.9)], 0.0)
    Lw = Lw * (0.6 + 0.4 * np.clip((Y - QY) / 3.0, 0, 1))

    def ombre_quai(cx, cy, rx, ry, f=0.5):
        nonlocal Lc, Lw
        o = 1 - f * np.clip(1.3 - np.hypot((X - cx) / rx, (Y - cy) / ry), 0, 1)
        Lc, Lw = Lc * o, Lw * o

    ombre_quai(96.0, 66.4, 17.0, 1.7, 0.6)            # sous la Puce
    ombre_quai(50.0, 66.2, 9.0, 1.4, 0.5)             # sous les casiers
    ombre_quai(134.0, 66.0, 8.0, 1.4, 0.5)            # les tonneaux
    flaques = paves(P, quai, Lc, Lw, 120.0, HOR, graine=730)
    cop = quai & (Y < QY + 1.5)                        # la pierre de couronnement
    appareil(P, cop, (Lc + Lw) * 1.25, LUNE, lh=1.5, lw=9.0, graine=731, rampe=R_FROID, alb=0.66, dy=QY)
    lisere(P, quai, BM3, 0, -1, cond=pg.fbm(X / 2.6, 0 * X, 2, 732) > 0.3)
    # Les feux dans les flaques.
    for k, (lx0, coul, y0) in enumerate(((176.0, LU3, 66.4), (121.0, LU2, 66.6), (176.0, LU4, 69.0))):
        dx = X - lx0 - (hz(P.YI, k, 733) - 0.5) * 3.4
        m = quai & (Y > y0) & (Y < 75.6) & (np.abs(dx) < 0.5 + 1.5 * hz(P.YI, 5 + k, 733)) & (hz(P.YI, 9 + k + int(p * 8) % 2, 734) < 0.5)
        P.a[m] = coul
    dx = X - LUNE[0] + 0.5 * (Y - QY) - (hz(P.YI, 3, 735) - 0.5) * 5.0
    m = quai & (Y > 63.6) & (np.abs(dx) < 0.5 + 1.6 * hz(P.YI, 4, 735)) & (hz(P.YI, 6 + int(p * 4) % 2, 735) < 0.42)
    P.a[m] = BM4                                       # et la lune
    # L'échelle de fer, deux bittes d'amarrage, leurs aussières.
    for ex in (72.4, 75.2):
        P.courbe([(ex, QY + 2.0), (ex, QY - 2.6), (ex + 1.0, QY - 3.6), (ex + 1.6, QY - 2.6)], GR1, 2)
        P.point(ex, QY - 2.0, BM2)
    for bx_ in (61.0, 150.0):
        bt = m_rect(P, bx_ - 1.5, QY - 1.6, 3.0, 5.0) | m_ell(P, bx_, QY - 1.6, 2.3, 1.2)
        P.rampe(bt, 0.3 + 0.4 * (X - bx_) / 2.3 - 0.06 * (Y - QY), [ENCRE, NU0, GR1, GR2, GR3, BM2], 0.5)
        P.ell(bx_ + 0.5, QY - 2.0, 1.2, 0.5, BM2)
        P.ell(bx_, QY + 3.6, 2.4, 0.7, ENCRE)
    P.courbe([(150.0, QY + 1.0), (158.0, QY + 3.0 + 0.3 * onde(p, 0.3)), (166.0, QY - 0.6)], GO2, 2)
    P.courbe([(150.0, QY + 1.0), (158.0, QY + 3.0 + 0.3 * onde(p, 0.3)), (166.0, QY - 0.6)], GO1, 1)

    # ---- Les casiers à homards empilés ; un homard veille dedans.
    for i, (x, y, k) in enumerate(((46.6, 65.4, 1.15), (54.0, 65.0, 1.0), (50.0, 60.6, 1.0))):
        casier(P, x, y, k)
        P.trait(x - 4.0 * k, y - 0.4, x + 4.0 * k, y - 0.4, BO3)
    pg.yeux(P, 49.0, 58.4, coul=LU4, d=0.4, ecart=1.6)

    # ---- La Puce, tirée au sec sur ses tins : Tudal la goudronne. L'éraflure fraîche court sur son flanc.
    bx0, bx1, yg, yk = 84.0, 113.0, 54.6, 63.8
    xm, half = (bx0 + bx1) / 2, (bx1 - bx0) / 2
    un = (X - xm) / half
    tonture = yg - 0.9 * un ** 2 - 1.4 * np.clip(un - 0.4, 0, 1) ** 1.5 * 2.2                       # la lisse remonte vers l'étrave
    quille = yk - 6.0 * np.clip(np.abs(un) - 0.56, 0, 1) ** 1.7 * 4.0 * (1 + 0.6 * (un > 0))
    cq = (Y >= tonture) & (Y <= quille) & (X >= bx0) & (X <= bx1 + 0.4)
    t = np.clip((Y - tonture) / np.maximum(quille - tonture, 0.2), 0, 1)
    Lb = lumiere(P, [(121.0, 60.0, 12.0, 0.9 * vac), (176.0, 40.0, 30.0, 0.25)], 0.3)
    goud = X < xm + 3.0 + 1.5 * np.sin(Y * 1.3)                                                    # la moitié déjà goudronnée
    bordes = ((t * 5.0) % 1.0) < 0.14
    P.rampe(cq & goud, (0.22 + 0.4 * np.exp(-((t - 0.3) / 0.12) ** 2) - 0.1 * t) * Lb * 1.4 - 0.05 * bordes, [ENCRE, NU0, NU1, GR2, GR3, BM2], 0.5)
    P.rampe(cq & ~goud, (0.66 - 0.36 * t + 0.14 * (pg.fbm(X / 1.2, Y / 0.8, 2, 740) - 0.5)) * Lb * 1.3 - 0.07 * bordes, R_TOILE, 0.5)
    lisere(P, cq, CREME, 0, -1)                                                                    # le liston
    P.remplir(cq & (t > 0.07) & (t < 0.16), LU2)                                                   # un filet orange sous le liston
    for k in range(3):                                                                            # l'éraflure : le bois à nu
        P.trait(90.0 + k * 0.5, 59.6 + k * 0.5, 104.6 - k * 1.4, 58.4 + k * 0.5, CREME if k == 0 else BO4)
    P.trait(113.2, 53.6, 112.6, 57.0, BO2, 2)                                                      # l'étrave
    P.point(112.8, 52.4, BO3, 2)
    for tx_ in (90.0, 106.0):                                                                     # les tins
        P.rampe(m_rect(P, tx_ - 2.0, 62.6, 4.0, 3.4), (0.4 + 0.1 * (X - tx_)) * (Lc + Lw), R_BOIS, 0.5)
        P.rect(tx_ - 2.0, 62.6, 4.0, 0.4, R_BOIS[5])
    P.trait(86.0, 55.2, 82.4, 65.4, BO2, 2)                                                        # une béquille
    P.trait(93.0, 53.0, 96.4, 53.8, BO4, 2)                                                        # le marteau, posé sur le plat-bord
    P.rect(92.0, 52.2, 1.6, 1.4, GR3)
    P.point(92.0, 52.2, BM3)
    # Le brasero, le pot de goudron qui fume, le pinceau.
    fx_, fy_ = 121.0, 65.6
    for dx in (-2.2, 2.2):
        P.trait(fx_ + dx, fy_ - 3.0, fx_ + dx * 1.5, fy_, ENCRE, 2)
    br = m_rect(P, fx_ - 3.0, fy_ - 5.6, 6.0, 3.0)
    P.remplir(br, ENCRE)
    P.rampe(br & ((P.XI + P.YI) % 3 != 0), 0.5 + 0.4 * (pg.fbm(X / 0.8, Y / 0.8, 2, 741) - 0.5) + 0.2 * onde(p * 2, 0.3), R_FEU[:5], 0.5)
    flammes(P, fx_ - 2.6, fx_ + 2.6, fy_ - 5.4, 4.0, 742, rampe=R_FEU[1:6], gain=1.0)
    halo(P, fx_, fy_ - 6.0, 9.0, LU2, 0.4 * vac)
    pot = m_rect(P, fx_ - 2.2, fy_ - 9.6, 4.4, 3.4)
    P.rampe(pot, 0.2 + 0.3 * (Y - fy_ + 9.6) / 3.4, [ENCRE, NU0, GR1, LU1, LU2], 0.5)
    P.rect(fx_ - 2.6, fy_ - 9.8, 5.2, 0.5, GR2)
    P.trait(fx_ + 1.0, fy_ - 9.8, fx_ + 4.0, fy_ - 13.0, BO3)                                      # le pinceau à goudron
    fumerolle(P, fx_ - 0.6, fy_ - 10.6, h=12.0, n=3, d=0.1, coul=T.CIEL[4], force=0.4, large=0.8)
    for i in range(4):
        tt = (p + hz(i, 0, 743)) % 1.0
        P.point(fx_ - 2.0 + 4.0 * hz(i, 1, 743) + math.sin(tt * 6 + i), fy_ - 6.0 - 9.0 * tt, LU4 if tt < 0.5 else LU2)
    # Deux tonneaux, une caisse de sardines, des bidons.
    for i, (tx_, th_) in enumerate(((131.0, 8.0), (137.4, 6.4))):
        tn = m_rect(P, tx_ - 3.4, 65.0 - th_, 6.8, th_) & (np.abs(X - tx_) < 2.7 + 0.7 * np.sin((Y - 65.0 + th_) / th_ * 3.14))
        lames(P, tn, (0.5 + Lw * 0.8) * cylindre(P, tx_ - 3.4, tx_ + 3.4, 121.0), larg=1.3, graine=744 + i, alb=0.56, noeuds=0, sens=-1)
        for yy in (65.0 - th_ + 1.0, 65.0 - 1.8):
            P.remplir(tn & (Y >= yy) & (Y < yy + 0.7), GR2)
        P.ell(tx_, 65.0 - th_, 2.7, 0.8, R_BOIS[4])
        P.ell(tx_, 65.0 - th_, 1.9, 0.5, R_BOIS[2])
    cs_ = m_rect(P, 141.6, 61.4, 7.0, 4.0)
    lames(P, cs_, 0.56 + Lw * 0.6, larg=1.3, graine=746, vertical=False, alb=0.6, noeuds=0)
    for i in range(4):
        P.ell(143.0 + i * 1.5, 61.2 - (i % 2) * 0.4, 1.1, 0.5, BM3)
        P.point(143.4 + i * 1.5, 61.0 - (i % 2) * 0.4, BM4 if int(p * 8 + i) % 5 else BLANC)

    # ---- Le panneau du Passe-Pied (à demi effacé) ; le fanal du quai, où tournent les papillons de nuit.
    P.rampe(m_rect(P, 164.2, 46.0, 1.4, 19.6), 0.3 + 0.3 * (X - 164.2) / 1.4, R_BOIS, 0.5)
    pn = P.masque_poly([(157.0, 47.0), (171.0, 47.0), (174.0, 50.0), (171.0, 53.0), (157.0, 53.0)])
    lames(P, pn, 0.62 + Lw * 0.5, larg=3.0, graine=747, vertical=False, alb=0.6, noeuds=0.5, rampe=R_PLATRE)
    lisere(P, pn, R_PLATRE[1], 0, 1)
    for j in range(2):                                                                            # ce qui reste de la peinture : des vagues, deux heures
        P.remplir(pn & (np.abs(Y - 49.0 - j * 1.9 - 0.3 * np.sin(X * 1.6)) < 0.25) & (X < 164.0) & (pg.fbm(X / 1.6, Y, 2, 748) > 0.42), NU2)
    for cx_ in (166.4, 169.6):
        P.ell(cx_, 50.0, 1.2, 1.2, NU2, cond=pg.fbm(X / 1.0, Y / 1.0, 2, 749) > 0.4)
        P.point(cx_, 50.0, R_PLATRE[6])
    px_ = 180.0
    P.rampe(m_rect(P, px_ - 0.8, 24.0, 1.6, 41.6), 0.2 + 0.5 * (X < px_), [ENCRE, NU0, GR1, GR2, GR3], 0.5)
    P.rect(px_ - 1.6, 62.0, 3.2, 3.6, GR1)
    P.courbe([(px_, 25.0), (px_ - 2.0, 22.6), (px_ - 4.4, 23.4)], GR1, 2)
    P.trait(px_ - 0.6, 30.0, px_ - 4.0, 25.0, GR1)
    lx_, ly_ = px_ - 4.4 + 0.25 * onde(p, 0.2), 32.4
    P.trait(px_ - 4.4, 23.6, lx_, ly_ - 6.0, GR1)
    halo(P, lx_, ly_ - 3.0, 15.0, LU2, 0.34)
    halo(P, lx_, ly_ - 3.0, 7.0, LU3, 0.5)
    P.poly([(lx_ - 2.4, ly_ - 5.4), (lx_ + 2.4, ly_ - 5.4), (lx_, ly_ - 7.4)], ENCRE)
    vif = int(p * 8) % 5 != 0
    P.rect(lx_ - 1.6, ly_ - 5.4, 3.2, 4.6, LU4 if vif else LU3)
    P.rect(lx_ - 0.6, ly_ - 4.6, 1.2, 2.8, LU5)
    P.rect(lx_ - 2.0, ly_ - 0.8, 4.0, 0.8, ENCRE)
    for dx in (-1.8, 1.4):
        P.rect(lx_ + dx, ly_ - 5.4, 0.4, 4.6, ENCRE)
    lisere(P, m_rect(P, px_ - 0.8, 24.0, 1.6, 20.0), LU3, -1, 0)                                    # le poteau prend sa lumière
    # Une ancre appuyée au poteau, un cordage lové, des coquilles.
    ax, ay = 188.0, 65.6
    P.trait(ax, ay - 13.0, ax - 1.0, ay - 1.0, GR1, P.ep(0.9))
    P.courbe([(ax - 6.0, ay - 5.0), (ax - 4.6, ay - 0.6), (ax - 1.0, ay + 0.2), (ax + 2.8, ay - 1.4), (ax + 4.6, ay - 5.6)], GR1, P.ep(0.9))
    P.trait(ax - 3.4, ay - 11.0, ax + 3.4, ay - 11.6, GR1, 2)
    P.ell(ax, ay - 14.0, 1.5, 1.5, GR1)
    P.ell(ax, ay - 14.0, 0.7, 0.7, T.CIEL[3])
    P.trait(ax - 0.5, ay - 12.0, ax - 1.4, ay - 2.0, LU1)                                          # le fanal la rouille d'un trait
    for i, r in enumerate((4.2, 3.2, 2.2, 1.2)):
        P.ell(170.0, 67.6 - i * 0.5, r, r * 0.42, GO2 if i % 2 else GO1)
    P.ell(170.0, 65.8, 0.8, 0.3, ENCRE)

    # ======================================================================================================= premier plan
    tab.plan("premier", 1.0)
    # À gauche, le coin de l'auberge : le mur de granit, la fenêtre jaune et sa buée, l'enseigne au bigorneau qui grince.
    Lf = lumiere(P, [(2.0, 30.0, 11.0, 0.8)], 0.2)
    mur = m_rect(P, -6.0, -16.0, 17.0, 96.0)
    appareil(P, mur, Lf, (2.0, 30.0), lh=5.0, lw=7.0, graine=750, alb=0.52)
    P.rampe(mur & (X > 10.2), 0.56, R_FROID, 0.5)                                                  # l'arête, à la lune
    fen = m_rect(P, -6.0, 20.0, 12.6, 17.0)
    P.rampe(fen, 0.6 + 0.2 * (pg.fbm(X / 2.0, Y / 3.0, 2, 751) - 0.5) + 0.02 * (Y - 20.0) + 0.05 * onde(p * 2, 0.4), [LU2, LU3, LU4, LU5], 0.5)
    P.remplir(fen & (Y > 30.0 + 1.5 * np.sin(X * 0.9)) & (pg.fbm(X / 1.4, Y / 2.0, 2, 7511) > 0.42), LU5)                      # la buée
    om = m_ell(P, 2.0, 33.6, 2.4, 3.4) | m_ell(P, 2.0, 29.4, 1.5, 1.5)                               # quelqu'un passe derrière la vitre
    P.remplir(fen & om & (int(p * 8) in (2, 3, 4)), LU1)
    for xm_ in (-2.0, 2.4):
        P.rect(xm_, 20.0, 0.7, 17.0, BO1)
    for ym_ in (25.6, 31.2):
        P.rect(-6.0, ym_, 12.6, 0.7, BO1)
    cad = m_rect(P, -6.0, 19.0, 13.8, 19.2) & ~fen
    P.rampe(cad, 0.34 + 0.04 * (Y - 19.0) * (Y < 22), R_BOIS, 0.5)
    P.rampe(m_rect(P, -6.0, 38.2, 14.6, 1.5), 0.62 - 0.2 * (Y - 38.2), R_GRANIT, 0.5)                # l'appui
    lisere(P, fen, R_BOIS[0], 0, -1)
    # Un filet à maquereaux pend au mur, sous la fenêtre, avec ses flotteurs de liège.
    for j in range(7):
        P.courbe([(-6.0, 42.0 + j * 1.9), (2.0, 44.6 + j * 1.9 + 0.3 * onde(p, 0.1 * j)), (10.0, 41.6 + j * 1.9)], GO2 if j % 2 else GO1, 1)
    for x in np.arange(-5.0, 10.0, 1.9):
        P.trait(x, 42.4, x + 0.5, 55.6, GO1)
    for i, x in enumerate((-2.0, 3.0, 8.0)):
        P.ell(x, 56.0 + (i % 2) * 1.4, 1.3, 1.3, LU2)
        P.point(x - 0.5, 55.6 + (i % 2) * 1.4, LU4)
    # L'enseigne : une potence de fer, un panneau de bois, un gros bigorneau peint.
    P.trait(11.0, -9.0, 33.0, -9.0, ENCRE, P.ep(0.8))
    P.courbe([(11.0, -2.0), (19.0, -4.0), (23.0, -9.0)], ENCRE, 2)
    P.courbe([(33.0, -9.0), (34.6, -10.6), (33.0, -11.6)], ENCRE, 1)
    bal = 0.7 * onde(p, 0.15)
    ex, ey = 25.0 + bal, -6.4
    for dx in (-4.0, 4.0):
        P.trait(25.0 + dx, -9.0, ex + dx, ey, ENCRE)
    ens = m_rect(P, ex - 6.4, ey, 12.8, 10.4)
    lames(P, ens, 0.62 + 0.012 * (X - ex), larg=3.5, graine=753, vertical=False, alb=0.62, noeuds=0)
    lisere(P, ens, R_BOIS[1], 0, 1)
    lisere(P, ens, R_BOIS[7], 0, -1)
    cq_ = (ex - 0.6, ey + 5.6)
    coq = m_ell(P, cq_[0], cq_[1], 3.9, 3.5) | P.masque_poly([(cq_[0] + 2.4, cq_[1] - 2.4), (cq_[0] + 5.6, cq_[1] + 1.4), (cq_[0] + 2.4, cq_[1] + 3.4)])
    ang = np.arctan2(Y - cq_[1], X - cq_[0])
    ray = np.hypot(X - cq_[0], Y - cq_[1])
    P.rampe(coq, 0.56 + 0.2 * (X - cq_[0]) / 4.0 - 0.2 * (Y - cq_[1]) / 3.5, [R_PLATRE[3], R_PLATRE[5], R_PLATRE[7], CREME], 0.5)
    P.remplir(coq & (((ray - 0.9 * (ang + math.pi) / math.pi) % 1.8) < 0.42) & (ray < 3.6), R_PLATRE[3])
    P.ell(cq_[0] + 3.4, cq_[1] + 0.8, 1.3, 1.5, R_BOIS[1])
    # En bas : le bord du quai tout près, dans l'ombre ; une bitte, son aussière, un anneau, des algues, une étoile de mer.
    bas = Y > 75.6 + 0.6 * np.sin(X / 9.0)
    P.rampe(bas, 0.26 + 0.2 * (pg.fbm(X / 4.0, Y / 1.2, 3, 754) - 0.5) + 0.1 * (pg.fbm(X / 0.8, Y / 0.8, 2, 755) - 0.5), [ENCRE, NU0, R_GRANIT[1], R_GRANIT[2]], 0.5)
    lisere(P, bas, R_GRANIT[2], 0, -1, cond=pg.fbm(X / 2.0, 0 * X, 2, 756) > 0.45)
    bx_ = 176.0
    bt = m_rect(P, bx_ - 4.0, 66.0, 8.0, 14.0) | m_ell(P, bx_, 66.0, 5.6, 2.4)
    P.rampe(bt, 0.2 + 0.34 * np.clip((X - bx_) / 5.6 + 0.3, 0, 1) - 0.01 * (Y - 66.0), [ENCRE, NU0, GR1, GR2, LU1, LU2], 0.5)
    P.ell(bx_ + 1.0, 65.2, 3.4, 1.1, GR2)
    lisere(P, bt, LU3, 1, 0, cond=(Y < 72.0))
    for k in range(3):
        P.courbe([(bx_ - 4.6, 70.0 + k * 1.4), (bx_, 71.6 + k * 1.4), (bx_ + 4.6, 70.0 + k * 1.4), (198.0, 68.0 + k * 1.4 + 0.3 * onde(p, 0.1 * k))], GO2 if k % 2 == 0 else GO1, P.ep(0.6))
    P.ell(150.0, 77.4, 1.8, 1.0, GR3)                                                             # l'anneau d'amarrage
    P.ell(150.0, 77.4, 1.0, 0.5, ENCRE)
    for i in range(9):                                                                            # des coquilles de moules, des bigorneaux
        x = 84.0 + 52.0 * hz(i, 1, 757)
        P.ell(x, 77.2 + 1.6 * hz(i, 2, 757), 0.9, 0.5, (NU2, GR3, VI2)[i % 3])
        P.point(x + 0.3, 77.0 + 1.6 * hz(i, 2, 757), BM2)
    et = (60.0, 77.6)                                                                             # l'étoile de mer
    for k in range(5):
        a = k * 2 * math.pi / 5 - 1.2
        P.trait(et[0], et[1], et[0] + 2.2 * math.cos(a), et[1] + 1.1 * math.sin(a), LU2, 2)
    P.point(et[0], et[1], LU4)
    brume(P, 71.0, 1.6, 17, T.CIEL[6], 0.2, x0=20, x1=150)


# =====================================================================================================================
# Troisième passe : peindre en matière. Une lumière calculée (`lumiere`), des rampes qui vont de l'ombre froide à la
# lumière chaude, et des surfaces qui ont un grain : bois veiné, pierre appareillée, enduit taché, plancher qui fuit.
# Une surface se peint par `P.rampe(masque, teinte_propre × lumière, rampe)` : la même lumière éclaire tout le lieu.
# =====================================================================================================================
R_BOIS = cs("#10122a", "#1f1728", "#33211f", "#4e321d", "#6d4627", "#8f5f33", "#b57f44", "#dba258", "#ffcf8a")
R_PLATRE = cs("#141a31", "#262742", "#433a4e", "#6b5552", "#94725a", "#bb9364", "#dcb676", "#f4d794", "#fff1c9")
R_GRANIT = cs("#0d1326", "#1c2336", "#30384c", "#4b4c60", "#6f6468", "#977d6c", "#c09a72", "#e6c088")
R_ETAIN = [GR1, GR2, GR3, GR4, BM3, BM4]
R_CUIVRE = cs("#33211f", "#8a4a1f", "#d9803a", "#f69d50", "#ffc89a", "#fff1c9")
R_CIRE = [GO1, GO2, LAITON, CIRE, CIRE2, LU5]
R_VERRE = cs("#0f2436", "#17384a", "#245566", "#3d7a84", "#6aa8a4", "#cfdaea")
R_NUIT = [NU0, NU1, NU2, NU3, NU4, BM1, BM2, BM3]
R_TOILE = cs("#13254a", "#1d3766", "#3f6fb0", "#6c98d0", "#a9bbd8", "#efe4cc")
R_FROID = [ENCRE] + R_GRANIT[:3] + [GR3, GR4, BM3, BM4]
R_PAPIER = cs("#6b6f8e", "#9aa0bd", "#cfd3e0", "#efe4cc", "#fff1c9", "#ffffff")
R_FEU = cs("#33211f", "#8a4a1f", "#d9803a", "#f69d50", "#ffc89a", "#fff1c9", "#ffffff")


def m_rect(P, x, y, w, h):
    return (P.X >= x) & (P.X < x + w) & (P.Y >= y) & (P.Y < y + h)


def m_ell(P, cx, cy, rx, ry):
    return ((P.X - cx) / rx) ** 2 + ((P.Y - cy) / ry) ** 2 <= 1


def lumiere(P, sources, ambiante=0.12):
    """Le champ de lumière d'un lieu : sources = (x, y, portée, force). 0 : le noir ; 1 : en pleine lumière."""
    L = np.full(P.X.shape, float(ambiante))
    for (x, y, r, f) in sources:
        L = L + f / (1.0 + ((P.X - x) ** 2 + (P.Y - y) ** 2) / (r * r))
    return L


def vers(P, x, y):
    """Le vecteur unité de chaque pixel vers la source (x, y)."""
    dx, dy = x - P.X, y - P.Y
    d = np.maximum(np.hypot(dx, dy), 0.01)
    return dx / d, dy / d


def lisere(P, m, coul, dx=1, dy=0, cond=None):
    """Les pixels de m dont le voisin (dx, dy) n'en fait pas partie prennent `coul` : l'arête qui accroche la lumière."""
    b = m & ~np.roll(m, (-dy, -dx), axis=(0, 1))
    if cond is not None:
        b &= cond
    P.a[b] = coul
    return b


def lames(P, m, L, larg=5.0, graine=0, vertical=True, rampe=None, alb=0.62, sens=1, noeuds=0.25, long=0.0):
    """Des planches jointives : un ton par planche, des veines étirées dans le fil, quelques nœuds, un joint sombre et
    son arête claire du côté d'où vient la lumière (sens : +1 la lumière est à droite ou en bas). long : longueur des
    planches (0 : d'un seul tenant)."""
    rampe = R_BOIS if rampe is None else rampe
    u, w = (P.X, P.Y) if vertical else (P.Y, P.X)
    k = np.floor(u / larg)
    du = u - k * larg
    ton = 0.84 + 0.32 * hz(k, 0, graine)
    veine = pg.fbm(u / 0.7 + 3.1 * k, w / 16.0 + 5.3 * k, 3, graine + 1) - 0.5
    v = alb * (ton + 0.34 * veine)
    if noeuds:
        wn = (w + 37.0 * hz(k, 2, graine)) % 43.0 - 21.5
        dn = np.hypot((du - larg * (0.3 + 0.4 * hz(k, 3, graine))) * 1.6, wn * 0.7)
        a_noeud = hz(k, 4, graine) < noeuds
        v = np.where(a_noeud & (dn < 1.5), v * (0.55 + 0.3 * dn), v)
    joint = du < 0.42
    if long:
        wl = w + long * hz(k, 5, graine)
        joint |= (wl % long) < 0.42
    arete = (du > larg - 0.42) if sens > 0 else ((du >= 0.42) & (du < 0.84))
    v = np.where(arete, v + 0.10, v)
    v = np.where(joint, v * 0.5, v)
    P.rampe(m, v * L, rampe, 0.5)


def appareil(P, m, L, src, lh=4.2, lw=8.0, graine=0, rampe=None, alb=0.6, dy=0.0, relief=0.2):
    """Un mur de pierres de taille inégales : un ton par pierre, un grain, des joints creux, et un biseau qui prend la
    lumière du côté de la source `src` (x, y) et l'ombre de l'autre."""
    rampe = R_GRANIT if rampe is None else rampe
    X, Y = P.X, P.Y
    r = np.floor((Y - dy) / lh)
    wv = lw * (0.72 + 0.56 * hz(r, 2, graine))
    xx = X + lw * 3.0 * hz(r, 1, graine) + 0.5 * (pg.bruit(Y / 2.0, r, graine + 9) - 0.5)
    s = np.floor(xx / wv)
    du0, dv0 = xx - s * wv, (Y - dy) - r * lh
    du1, dv1 = wv - du0, lh - dv0
    ton = 0.76 + 0.48 * hz(s, r, graine + 3)
    grain = pg.fbm(X / 1.1, Y / 1.1, 2, graine + 4) - 0.5
    joint = (du0 < 0.42) | (dv0 < 0.42)
    sx, sy = vers(P, src[0], src[1])
    e = 0.84
    bev = ((du1 < e) * sx - ((du0 < 0.42 + e) & ~joint) * sx + (dv1 < e) * sy - ((dv0 < 0.42 + e) & ~joint) * sy)
    v = alb * (ton + 0.3 * grain) + relief * bev
    v = np.where(joint, alb * 0.42, v)
    P.rampe(m, v * L, rampe, 0.5)


def enduit(P, m, L, graine=0, rampe=None, alb=0.66):
    """Un mur enduit à la chaux : de grandes taches lentes, un grain fin, des coulures sous le plafond."""
    rampe = R_PLATRE if rampe is None else rampe
    X, Y = P.X, P.Y
    v = alb * (0.92 + 0.3 * (pg.fbm(X / 13.0, Y / 9.0, 3, graine) - 0.5) + 0.16 * (pg.fbm(X / 1.5, Y / 1.5, 2, graine + 1) - 0.5))
    coul = pg.fbm(X / 2.2, Y / 30.0, 2, graine + 2)
    v = v - 0.12 * np.clip(coul - 0.62, 0, 1) * 4.0 * np.clip(1 - (Y + 6) / 22.0, 0, 1)
    P.rampe(m, v * L, rampe, 0.5)


def plancher(P, m, L, fx, yh, larg=4.0, graine=0, rampe=None, alb=0.62, prof=0.55):
    """Un plancher en perspective : des lames qui fuient vers (fx, yh), chacune son ton, ses veines, ses abouts."""
    rampe = R_BOIS if rampe is None else rampe
    dy = np.maximum(P.Y - yh, 0.25)
    u = (P.X - fx) / dy * 10.0
    z = 60.0 / dy
    k = np.floor(u / larg)
    fu = u / larg - k
    ton = 0.82 + 0.36 * hz(k, 0, graine)
    veine = pg.fbm(u * 1.6 + 3.7 * k, z * 2.4 + 9.1 * k, 3, graine + 1) - 0.5
    zz = z * prof + hz(k, 5, graine)
    about = (zz - np.floor(zz)) < 0.03 * (1 + z * 0.3)
    v = alb * (ton + 0.36 * veine)
    joint = (fu < 0.07 + 0.05 * 10.0 / dy) | about
    v = np.where(~joint & (fu > 0.9), v + 0.08, v)
    v = np.where(joint, v * 0.5, v)
    P.rampe(m, v * L, rampe, 0.5)


def cylindre(P, x0, x1, src_x):
    """L'ombrage d'un volume rond entre x0 et x1, éclairé depuis src_x : 0,55 (côté ombre) à 1,25 (côté lumière)."""
    t = np.clip((P.X - x0) / max(x1 - x0, 0.01), 0, 1)
    tl = 0.76 if src_x > (x0 + x1) / 2 else 0.24
    return 0.55 + 0.7 * np.exp(-((t - tl) / 0.3) ** 2) - 0.12 * np.exp(-((t - (1 - tl)) / 0.12) ** 2)


def flammes(P, x0, x1, base, haut, graine=0, rampe=None, masque=None, gain=1.15):
    """Un feu : des langues de bruit qui montent et bouclent avec la phase, un cœur blanc, des pointes sombres."""
    rampe = R_FEU if rampe is None else rampe
    p = P.p
    X, Y = P.X, P.Y
    u = (X - x0) / (x1 - x0)
    h = (base - Y) / haut
    env = np.clip(1 - (2 * u - 1) ** 2, 0, 1) ** 0.5

    def champ(q):
        return pg.fbm(X / 2.6, (Y + q * haut * 1.6) / 4.2, 3, graine)

    n = (1 - p) * champ(p) + p * champ(p - 1.0)
    langue = 0.5 + 0.5 * np.sin(X * 1.5 + 4.0 * n + 6.283 * p)
    v = env * (1.1 - 0.25 * langue) - h * (0.75 + 0.5 * langue) + (n - 0.5) * (0.5 + 1.1 * np.clip(h, 0, 1))
    m = (v > 0) & (h > -0.02) & (u > 0) & (u < 1)
    if masque is not None:
        m &= masque
    P.rampe(m, 0.12 + np.clip(v, 0, 1) * gain, rampe, 0.5)
    return m


def boule_verre(P, x, y, r, src, rampe=None, filet=None):
    """Une boule de verre (flotteur de filet) : sombre au cœur, un croissant de lumière du côté de la source, un éclat."""
    rampe = R_VERRE if rampe is None else rampe
    d = np.hypot(P.X - x, P.Y - y)
    m = d <= r
    sx, sy = vers(P, src[0], src[1])
    n = ((P.X - x) * sx + (P.Y - y) * sy) / r
    v = 0.3 + 0.2 * n + 0.42 * np.clip(d / r - 0.55, 0, 1) * (1 + n) + 0.12 * ((P.X - x) / r) * -0.5
    P.rampe(m, v, rampe[:5], 0.5)
    ux, uy = (src[0] - x), (src[1] - y)
    k = r * 0.5 / max(math.hypot(ux, uy), 0.01)
    P.point(x + ux * k, y + uy * k, rampe[5])
    if filet is not None:
        P.remplir(m & (((P.XI + P.YI) % 5 == 0) | ((P.XI - P.YI) % 5 == 0)), filet)
    return m


def fumerolle(P, x, y, h=12.0, n=4, d=0.0, coul=None, force=0.5, large=1.0):
    """Une vapeur lente, en tons pleins : des volutes qui montent, s'élargissent et se défont."""
    coul = BM4 if coul is None else coul
    for k in range(n):
        t = (P.p + d + k / n) % 1.0
        cx = x + large * (1.2 + 1.8 * t) * math.sin(t * 5.0 + k * 2.1)
        r = large * (0.9 + 2.4 * t)
        dd = np.hypot(P.X - cx, (P.Y - (y - h * t)) * 1.15)
        voile(P, dd < r, coul, force * (1 - t) * (1 - dd / r) * 1.6)


# =====================================================================================================================
# Le Bigorneau Qui Tousse : la salle basse d'une auberge de pêcheurs, un soir de brume. Tout est éclairé par l'âtre, à
# droite : la marmite de soupe y fume, pendue à sa potence. La grande horloge (la clé) est à gauche du milieu ; le
# comptoir et ses étagères tout à gauche, avec le paquet de lettres sous le torchon ; le ciré jaune goutte à sa patère ;
# la fenêtre à petits carreaux donne sur la nuit bleue du port ; la grande table attend, entre le sel et les poireaux.
# =====================================================================================================================
@decor("phare-eteint", "auberge-bigorneau", soleil=(152.0, 56.0), tons=PHARE, nom="Le Bigorneau Qui Tousse", matiere=True)
def auberge_bigorneau(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    FX, FY = 152.0, 56.0                                        # le feu : la lumière du lieu
    FEU = (FX, FY)
    vac = 1.0 + 0.07 * onde(p * 2) + 0.04 * onde(p * 3, 0.2)     # le feu vacille
    tout = np.ones(X.shape, dtype=bool)

    # ================================================================================================= le mur du fond
    tab.plan("ciel", 0.0)
    Lm = lumiere(P, [(FX, 48.0, 46.0, 1.2), (14.0, 34.0, 15.0, 0.6), (99.0, 56.0, 10.0, 0.3)], 0.13)
    Lm = Lm * (1 - 0.42 * np.clip(1 - np.abs(X - 46.5) / 6.5, 0, 1) * (Y > 4) * (Y < 62))        # l'ombre de l'horloge
    Lm = Lm * (1 - 0.3 * np.clip(1 - np.abs(X - 119.0) / 5.0, 0, 1))                              # celle du manteau
    enduit(P, tout, Lm, 530)
    for i, (x0, y0) in enumerate(((70.0, -3.0), (25.0, 22.0), (186.0, 4.0))):                    # des lézardes
        pts = [(x0, y0)]
        for j in range(5):
            pts.append((pts[-1][0] + 2.4 * (hz(i, j, 541) - 0.5), pts[-1][1] + 2.0))
        P.courbe(pts, R_PLATRE[2], 1)
    # Un pan d'enduit est tombé : le granit paraît dessous.
    trou = (pg.fbm(X / 5.0, Y / 4.0, 3, 542) > 0.56) & m_ell(P, 78.0, 4.0, 10.0, 6.5)
    appareil(P, trou, Lm, FEU, lh=3.2, lw=6.0, graine=543, alb=0.5)
    lisere(P, trou, R_PLATRE[2], 0, -1)
    # Le lambris bas, sa cimaise et sa plinthe.
    bas = (Y >= 31.5) & (Y < 62.5)
    lames(P, bas, Lm, larg=5.2, graine=544, vertical=True, alb=0.56, sens=1)
    cim = (Y >= 29.6) & (Y < 31.6)
    P.rampe(cim, (0.74 - 0.2 * (Y - 29.6)) * Lm, R_BOIS, 0.5)
    P.rampe((Y >= 60.4) & (Y < 62.5), 0.46 * Lm, R_BOIS, 0.5)
    P.rampe((Y >= 60.4) & (Y < 60.8), 0.7 * Lm, R_BOIS, 0.5)
    # Le plafond : des planches sombres, enfumées.
    plaf = Y < -6.6
    lames(P, plaf, lumiere(P, [(FX, 20.0, 60.0, 0.5)], 0.12), larg=3.2, graine=545, vertical=False, alb=0.42, sens=1, noeuds=0, long=46.0)
    P.rampe((Y >= -6.6) & (Y < -3.6), (0.5 - 0.06 * (Y + 6.6)) * (Lm + 0.1), R_BOIS, 0.5)          # la sablière
    P.rampe((Y >= -3.6) & (Y < -2.6), 0.5 * Lm, R_PLATRE, 0.5)                                   # son ombre sur l'enduit

    # ---- La fenêtre à petits carreaux : dehors, la nuit bleue du port, la brume, deux mâts ; dedans, la buée.
    wx, wy, ww, wh = 88.0, 1.0, 30.0, 25.0
    P.rampe(m_rect(P, wx - 3.2, wy - 3.2, ww + 6.4, wh + 5.0), 0.36 * Lm, R_GRANIT, 0.5)          # l'embrasure de pierre
    appareil(P, m_rect(P, wx - 3.2, wy - 3.2, ww + 6.4, wh + 5.0), Lm * 1.25, FEU, lh=4.0, lw=5.0, graine=546, alb=0.62)
    fen = m_rect(P, wx, wy, ww, wh)
    brm = pg.fbm((X + 1.5 * onde(p, 0.1)) / 11.0, Y / 4.0, 3, 547)
    P.rampe(fen, 0.2 + 0.03 * (Y - wy) + 0.26 * (brm - 0.5), R_NUIT, 0.6)
    for i, (mx, mh) in enumerate(((wx + 7.0, 20.0), (wx + 19.5, 15.0))):                          # les mâts qui roulent
        dx = 0.5 * onde(p, 0.3 * i)
        P.trait(mx + dx, wy + wh - mh, mx - dx * 0.3, wy + wh, NU0)
        P.trait(mx + dx - 2.4, wy + wh - mh + 4.0, mx + dx + 2.4, wy + wh - mh + 3.6, NU0)
        P.trait(mx + dx, wy + wh - mh, mx + 6.0, wy + wh, NU1)
    P.remplir(fen & (Y > wy + wh - 4.6 + 0.8 * np.sin(X / 3.0)), NU0)                             # les toits d'en face
    for (lx_, ly_) in ((wx + 25.0, wy + 16.0), (wx + 13.0, wy + 19.6)):                           # deux fenêtres allumées, au loin
        vif = (p + lx_ * 0.01) % 1.0 < 0.86
        voile(P, fen & (np.hypot(X - lx_, Y - ly_) < 3.4), LU2, 0.34 * (1 - np.hypot(X - lx_, Y - ly_) / 3.4), lumiere=True)
        P.rect(lx_ - 0.6, ly_ - 0.6, 1.2, 1.2, LU4 if vif else LU3)
    buee = fen & (Y > wy + wh * 0.42 + 2.2 * np.sin(X / 4.3) + 3.0 * (pg.fbm(X / 6.0, Y / 6.0, 2, 548) - 0.5))
    voile(P, buee, BM3, 0.34 + 0.012 * (Y - wy))
    P.ell(wx + 23.6, wy + 17.4, 1.5, 1.5, NU2, cond=buee)                                         # un bonhomme tracé du doigt
    P.trait(wx + 23.6, wy + 18.8, wx + 23.6, wy + 21.6, NU2)
    P.trait(wx + 22.0, wy + 19.8, wx + 25.2, wy + 19.8, NU2)
    for k in range(4):                                                                            # des gouttes qui glissent
        t = (p + k * 0.27) % 1.0
        gx = wx + 4.0 + k * 7.3
        P.trait(gx, wy + 12.0, gx, wy + 12.0 + 12.0 * t, NU3)
        P.point(gx, wy + 12.4 + 12.0 * t, BM4)
    for i in range(1, 4):                                                                         # les petits-bois
        P.rect(wx + ww * i / 4.0 - 0.5, wy, 1.0, wh, R_BOIS[3])
        P.rect(wx + ww * i / 4.0 + 0.1, wy, 0.4, wh, R_BOIS[5])
    for j in range(1, 3):
        P.rect(wx, wy + wh * j / 3.0 - 0.5, ww, 1.0, R_BOIS[3])
        P.rect(wx, wy + wh * j / 3.0 - 0.5, ww, 0.4, R_BOIS[5])
    cadre = m_rect(P, wx - 1.2, wy - 1.2, ww + 2.4, wh + 2.4) & ~fen
    P.rampe(cadre, (0.62 + 0.012 * (X - wx)) * (Lm + 0.12), R_BOIS, 0.5)
    lisere(P, fen, NU0, 0, -1)                                                                    # l'ombre du cadre sur la vitre
    P.rampe(m_rect(P, wx - 4.6, wy + wh + 1.2, ww + 9.2, 2.0), (0.86 - 0.2 * (Y - wy - wh - 1.2)) * (Lm + 0.1), R_GRANIT, 0.5)   # l'appui
    # Les brise-bise à carreaux, sur leur tringle de laiton.
    P.rect(wx - 2.0, wy + 11.4, ww + 4.0, 0.5, LAITON)
    for cote, x0 in ((-1, wx - 0.6), (1, wx + ww - 7.6)):
        rid = m_rect(P, x0, wy + 11.8, 8.2, wh - 11.0)
        pli = 0.5 + 0.5 * np.sin((X - x0) * 2.6 + 0.4 * np.sin(Y / 2.0) + 0.3 * onde(p, 0.2) * (Y - wy - 12) / 12.0)
        carreau = ((np.floor((X - x0) / 1.7) + np.floor(Y / 1.7)) % 2 == 0)
        P.rampe(rid, (0.36 + 0.3 * pli + 0.3 * carreau) * (0.75 + 0.6 * Lm), R_TOILE, 0.5)
    # Sur l'appui : un bateau en bouteille et un pot de bruyère.
    P.ell(wx + 9.0, wy + wh - 0.4, 4.4, 1.7, T.S1)
    P.ell(wx + 9.0, wy + wh - 0.8, 3.4, 1.1, T.S2)
    P.rect(wx + 13.0, wy + wh - 1.2, 1.8, 1.4, T.S1)
    P.rect(wx + 14.6, wy + wh - 1.2, 0.6, 1.4, R_BOIS[5])
    P.trait(wx + 7.0, wy + wh - 0.2, wx + 11.0, wy + wh - 0.2, R_BOIS[5])
    P.poly([(wx + 8.6, wy + wh - 0.6), (wx + 8.6, wy + wh - 2.0), (wx + 10.4, wy + wh - 0.6)], CREME)
    P.point(wx + 6.6, wy + wh - 1.4, BM4)
    px0 = wx + 21.0
    P.poly([(px0 - 1.8, wy + wh - 2.6), (px0 + 1.8, wy + wh - 2.6), (px0 + 1.3, wy + wh + 1.2), (px0 - 1.3, wy + wh + 1.2)], LU1)
    P.rect(px0 - 2.0, wy + wh - 3.0, 4.0, 0.7, LU2)
    for i in range(9):
        a = hz(i, 1, 549) * math.pi
        P.trait(px0, wy + wh - 3.0, px0 + 3.2 * math.cos(a), wy + wh - 3.4 - 3.0 * math.sin(a), T.S2 if i % 2 else T.S1)
        P.point(px0 + 3.2 * math.cos(a), wy + wh - 3.8 - 3.0 * math.sin(a), VI2 if i % 3 else T.VIOLET)

    # ---- Derrière le comptoir : deux étagères. Bouteilles, chopes d'étain pendues, la boîte à biscuits de Perrine.
    for (ey, x0, x1) in ((6.0, -6.0, 37.0), (19.0, -6.0, 37.0)):
        P.rampe(m_rect(P, x0, ey, x1 - x0, 1.6), (0.8 - 0.25 * (Y - ey)) * (Lm + 0.08), R_BOIS, 0.5)
        P.rampe(m_rect(P, x0, ey + 1.6, x1 - x0, 1.4), 0.36 * Lm, R_PLATRE, 0.5)                    # son ombre
        for bx_ in (x0 + 8.0, x1 - 3.0):                                                          # les consoles
            P.poly([(bx_, ey + 1.6), (bx_ + 1.2, ey + 1.6), (bx_ + 1.2, ey + 3.0), (bx_, ey + 5.0)], R_BOIS[3])

    def bouteille(x, y, h, w, r, bouchon=True):
        corps = m_rect(P, x - w / 2, y - h * 0.62, w, h * 0.62) | m_ell(P, x, y - h * 0.62, w / 2, w * 0.45)
        col = m_rect(P, x - w * 0.2, y - h, w * 0.4, h * 0.4)
        P.rampe(corps | col, (0.34 + 0.5 * cylindre(P, x - w / 2, x + w / 2, FX) * 0.6) * (0.5 + 1.2 * Lm), r, 0.5)
        P.rect(x + w * 0.16, y - h * 0.56, 0.4, h * 0.4, r[-1])                                    # le reflet du feu
        if bouchon:
            P.rect(x - w * 0.2, y - h - 0.6, w * 0.4, 0.7, R_BOIS[6])

    def chope(x, y, k=1.0, pendue=False):
        c = m_rect(P, x - 1.6 * k, y - 4.0 * k, 3.2 * k, 4.0 * k)
        P.rampe(c, (0.3 + 0.5 * cylindre(P, x - 1.6 * k, x + 1.6 * k, FX)) * (0.6 + 1.3 * Lm), R_ETAIN, 0.5)
        P.rect(x - 1.6 * k, y - 4.0 * k, 3.2 * k, 0.4, BM4)
        P.rect(x - 1.6 * k, y - 0.5, 3.2 * k, 0.5, GR1)
        P.courbe([(x - 1.6 * k, y - 3.2 * k), (x - 3.0 * k, y - 2.2 * k), (x - 1.6 * k, y - 0.9 * k)], GR3, 1)
        if pendue:
            P.trait(x - 2.6 * k, y - 2.4 * k, x - 2.6 * k, y - 5.2 * k, GR1)

    bouteille(7.0, 6.0, 9.6, 2.6, R_NUIT[:5] + [BM4])
    bouteille(10.4, 6.0, 6.4, 3.4, R_VERRE)
    # Une petite marine encadrée, des bocaux de bigorneaux, un pichet.
    for i, bx_ in enumerate((15.6, 20.2, 24.8)):
        b = m_rect(P, bx_ - 1.8, 0.6, 3.6, 5.4)
        P.rampe(b, (0.42 + 0.3 * cylindre(P, bx_ - 1.8, bx_ + 1.8, FX)) * (0.6 + 1.3 * Lm), R_VERRE, 0.5)
        P.remplir(b & (Y > 2.6) & (hz(P.XI // 2, P.YI // 2, 550 + i) < 0.5), (CREME, LU4, BM3)[i])
        P.remplir(b & (Y > 2.6) & (hz(P.XI // 2, P.YI // 2, 550 + i) >= 0.8), GR3)
        P.rect(bx_ - 2.0, 0.0, 4.0, 0.9, LAITON)
        P.rect(bx_ + 0.8, 1.4, 0.4, 3.6, BM4)
    pichet = m_ell(P, 31.0, 2.6, 2.6, 3.2) | m_rect(P, 29.4, -1.6, 3.2, 2.4)
    P.rampe(pichet, (0.5 + 0.4 * cylindre(P, 28.4, 33.6, FX)) * (0.5 + 1.4 * Lm), R_TOILE, 0.5)
    P.courbe([(33.4, 0.0), (35.6, 1.6), (33.4, 4.0)], R_TOILE[2], 1)
    P.rect(28.6, 1.6, 4.8, 0.6, R_TOILE[5])
    # L'étagère du bas : la boîte à biscuits (fer bleu, étiquette crème), des assiettes sur chant, les chopes pendues.
    boite = m_rect(P, 0.0, 12.4, 9.0, 6.6)
    P.rampe(boite, (0.5 + 0.016 * (X - 0.0) + 0.1 * (Y < 13.6)) * (0.55 + 1.4 * Lm), R_TOILE, 0.5)
    P.rect(0.0, 13.6, 9.0, 0.4, R_TOILE[1])
    P.rect(1.6, 14.8, 5.8, 3.0, CREME)
    P.ell(4.5, 16.3, 1.6, 1.0, LU2)
    P.rect(2.2, 15.4, 0.8, 0.4, R_TOILE[2])
    P.rect(6.0, 17.0, 0.8, 0.4, R_TOILE[2])
    P.rect(8.4, 12.4, 0.6, 6.6, R_TOILE[4])
    for i, ax_ in enumerate((12.4, 16.2, 20.0)):                                                  # les assiettes d'étain
        a = m_ell(P, ax_, 15.6, 2.3, 3.4)
        P.rampe(a, (0.46 + 0.5 * ((X - ax_) / 2.3)) * (0.7 + 1.5 * Lm), R_ETAIN, 0.5)
        P.remplir(m_ell(P, ax_ + 0.2, 15.6, 1.3, 2.2) & ~m_ell(P, ax_ + 0.5, 15.6, 1.1, 2.0), GR2)
        if int(p * 8 + i * 3) % 8 == 0:
            P.point(ax_ + 1.2, 14.0, BLANC)                                                       # un éclat du feu
    bouteille(25.6, 19.0, 6.0, 2.6, R_CUIVRE[:5] + [LU5])
    bouteille(29.2, 19.0, 8.0, 2.4, R_VERRE)
    bouteille(33.0, 19.0, 6.6, 3.0, R_NUIT[:5] + [BM4])
    for i, cx_ in enumerate((4.0, 10.0, 16.0, 22.0)):
        chope(cx_ + 0.3 * onde(p, 0.2 * i), 28.6, 1.0, pendue=True)

    # ---- À gauche de l'horloge : l'ardoise du jour (une soupe, dessinée) ; le portemanteau, à droite.
    P.rampe(m_rect(P, 39.4, 9.4, 10.2, 13.2), 0.7 * Lm, R_BOIS, 0.5)
    P.rect(40.4, 10.4, 8.2, 11.2, NU0)
    P.remplir(m_rect(P, 40.4, 10.4, 8.2, 11.2) & (pg.fbm(X / 2.0, Y / 2.0, 2, 551) > 0.62), NU1)
    P.ell(44.5, 17.6, 2.6, 1.3, BM3)
    P.ell(44.5, 17.2, 2.6, 0.7, NU0)
    P.ell(44.5, 17.2, 2.0, 0.4, BM2)
    P.courbe([(43.4, 15.6), (44.4, 14.4), (43.2, 13.2), (44.2, 12.0)], BM3, 1)                      # la vapeur
    P.courbe([(45.8, 15.6), (46.6, 14.6), (45.6, 13.6)], BM2, 1)
    P.trait(41.4, 20.4, 46.0, 20.4, BM2)
    P.trait(44.5, 9.4, 44.5, 7.0, GO2)

    # =========================================================================================== ce qui pend aux poutres
    tab.plan("lointains", 0.2)
    Lp = lumiere(P, [(FX, 30.0, 60.0, 1.0)], 0.16)
    for i, xi in enumerate(range(-14, 215, 26)):                                                  # les solives, en fuite
        xt = 96.0 + (xi - 96.0) * 1.42
        s = 1 if xi + 2.5 < 96 else -1
        flanc = P.masque_poly([(xi + 2.5 + s * 2.5, -6.6), (xi + 2.5 + s * 4.2, -6.6), (xt + 3.6 + s * 6.4, -16.0), (xt + 3.6 + s * 3.6, -16.0)])
        lames(P, flanc, Lp, larg=40.0, graine=552 + i, vertical=True, alb=0.3 if (FX - xi) * s < 0 else 0.6, noeuds=0)
        dess = P.masque_poly([(xi, -6.6), (xi + 5.0, -6.6), (xt + 7.2, -16.0), (xt, -16.0)])
        lames(P, dess, Lp, larg=40.0, graine=560 + i, vertical=True, alb=0.5, noeuds=0)
        P.rect(xi - 0.6, -7.2, 6.2, 1.0, R_BOIS[2])                                               # le corbeau
    SRC = (FX, 40.0)

    def pend(x, l, i):
        bal = 0.45 * onde(p, 0.17 * i)
        P.trait(x, -6.6, x + bal, -6.6 + l, GO1)
        return x + bal, -6.6 + l

    # Une guirlande de filet tendue entre deux solives, avec ses flotteurs de liège.
    for j in range(5):
        P.courbe([(38.0, -6.6 + j * 0.2), (52.0, -1.0 + j * 1.5 + 0.3 * onde(p, 0.1 * j)), (66.0, -6.6 + j * 0.2)], GO2 if j % 2 else GO1, 1)
    for x in np.arange(40.0, 66.0, 2.6):
        yb = -6.2 + 5.4 * (1 - ((x - 52.0) / 14.0) ** 2)
        P.trait(x, -6.4, x + 0.5, yb, GO1)
    for x in (45.0, 52.0, 59.0):
        P.ell(x, -0.6 + (0.6 if x == 52.0 else -0.6), 1.3, 0.9, R_BOIS[6])
        P.point(x + 0.4, -1.0 + (0.6 if x == 52.0 else -0.6), R_BOIS[8])
    # Deux boules de verre, une tresse d'oignons, un jambon, une botte de lavande de mer, des poissons séchés, une poêle.
    bx_, by_ = pend(74.0, 5.0, 1)
    boule_verre(P, bx_, by_ + 2.6, 2.6, SRC, rampe=R_NUIT[1:6] + [BM4], filet=GO2)
    bx_, by_ = pend(82.6, 4.0, 2)
    for j in range(5):                                                                            # les oignons
        ox, oy = bx_ + ((j % 2) * 2.0 - 1.0), by_ + 1.4 + j * 2.1
        P.rampe(m_ell(P, ox, oy, 1.7, 1.5), 0.5 + 0.4 * (X - ox) / 1.7 - 0.2 * (Y - oy) / 1.5, R_CUIVRE[1:5], 0.5)
        P.point(ox, oy - 1.6, CREME)
    bx_, by_ = pend(124.0, 5.0, 3)                                                                # le jambon
    jam = m_ell(P, bx_, by_ + 5.2, 3.2, 5.0) & (Y > by_ + 0.6 + np.abs(X - bx_) * 0.5)
    P.rampe(jam, 0.42 + 0.34 * (X - bx_) / 3.2 + 0.2 * (pg.fbm(X / 1.5, Y / 1.5, 2, 570) - 0.5), R_CUIVRE[:5], 0.5)
    P.rect(bx_ - 0.6, by_, 1.2, 1.4, CREME)
    for k in range(3):
        P.trait(bx_ - 2.6 + 0.3 * k, by_ + 3.0 + k * 1.9, bx_ + 2.6 - 0.3 * k, by_ + 2.6 + k * 1.9, GO2)
    bx_, by_ = pend(67.6, 3.6, 4)                                                                # la lavande de mer
    for i in range(11):
        a = (hz(i, 1, 571) - 0.5) * 1.3
        P.trait(bx_, by_, bx_ + 5.0 * math.sin(a), by_ + 5.6 * math.cos(a), T.S1 if i % 2 else T.S2)
        P.point(bx_ + 5.0 * math.sin(a), by_ + 5.8 * math.cos(a), T.VIOLET if i % 2 else VI2, 2)
    P.rect(bx_ - 0.8, by_ - 0.2, 1.6, 1.0, GO2)
    for i, x in enumerate((136.0, 140.0, 144.0)):                                                 # les poissons qui sèchent
        bx_, by_ = pend(x, 2.4, 5 + i)
        po = m_ell(P, bx_, by_ + 3.0, 1.1, 3.0)
        P.rampe(po, 0.5 + 0.4 * (X - bx_) / 1.1, R_ETAIN, 0.5)
        P.poly([(bx_ - 1.3, by_ + 7.0), (bx_ + 1.3, by_ + 7.0), (bx_, by_ + 5.4)], GR3)
        P.point(bx_ + 0.2, by_ + 1.2, ENCRE)
    bx_, by_ = pend(188.0, 5.0, 8)                                                                # la poêle de cuivre
    pm = m_ell(P, bx_, by_ + 6.0, 3.8, 3.8)
    P.rampe(pm, 0.44 + 0.3 * (X - bx_) / 3.8 * -1 + 0.34 * np.hypot(X - bx_, Y - by_ - 6.0) / 3.8, R_CUIVRE, 0.5)
    P.rect(bx_ - 0.5, by_, 1.0, 2.6, R_CUIVRE[1])
    if int(p * 8) % 8 in (2, 3):
        P.point(bx_ - 1.6, by_ + 4.4, BLANC)                                                      # elle renvoie le feu
        P.point(bx_ - 2.0, by_ + 4.4, LU5)
    # Une lanterne de bord pendue à gauche (éteinte : c'est le feu qui éclaire), où une araignée a fait sa toile.
    pg.toile_araignee(P, 12.4, -6.6, 6.5, sens=(-1, 1), coul=BM2)
    pg.araignee(P, 9.0, -3.0, 5.0, d=0.3, coul=GR1)

    # ============================================================================================= la salle elle-même
    tab.plan("moyen", 0.5)
    Ls = lumiere(P, [(FX, 62.0, 34.0, 1.3 * vac), (102.0, 58.0, 12.0, 0.5), (14.0, 50.0, 22.0, 0.42)], 0.26)
    sol = Y >= 62.4
    # Les ombres portées sur le plancher : elles fuient le feu.
    def ombre_sol(cx, cy, rx, ry, f=0.55):
        nonlocal Ls
        d = np.hypot((X - cx) / rx, (Y - cy) / ry)
        Ls = Ls * (1 - f * np.clip(1.25 - d, 0, 1))

    ombre_sol(96.0, 72.6, 24.0, 3.0)                # la table et son banc
    ombre_sol(52.0, 64.4, 10.0, 1.8, 0.5)           # l'horloge
    ombre_sol(16.0, 64.4, 28.0, 2.0, 0.45)          # le comptoir
    plancher(P, sol, Ls, 104.0, 44.0, larg=3.6, graine=572)
    # Le tapis de corde tressée devant le feu : des anneaux crème et bleus, usés au milieu.
    tapis = m_ell(P, 150.0, 72.6, 25.0, 4.3)
    rr = np.hypot((X - 150.0) / 25.0, (Y - 72.6) / 4.3)
    an = np.floor(rr * 6.0 + 0.3 * (pg.fbm(X / 3.0, Y / 1.2, 2, 573) - 0.5))
    usure = pg.fbm(X / 5.0, Y / 1.6, 3, 5731) - 0.5
    P.rampe(tapis & (an % 2 == 0), (0.6 + 0.3 * usure) * Ls, R_PLATRE, 0.5)
    P.rampe(tapis & (an % 2 == 1), (0.5 + 0.3 * usure) * (0.25 + Ls), R_TOILE[:5], 0.5)
    lisere(P, tapis, R_BOIS[1], 0, 1)

    # ---- L'âtre : un manteau de granit, un linteau de chêne, le foyer noir de suie, le feu, la marmite à sa potence.
    ax0, ax1 = 130.0, 174.0
    Lh = lumiere(P, [(FX, 50.0, 46.0, 1.5 * vac)], 0.26)
    suie = 1 - 0.4 * np.exp(-((X - FX) / 17.0) ** 2 - ((Y - 24.0) / 9.0) ** 2)                      # la suie, au-dessus du linteau
    corps = m_rect(P, ax0 - 7.0, -6.6, ax1 - ax0 + 14.0, 69.2)
    appareil(P, corps, Lh * suie, (FX, 46.0), lh=5.6, lw=11.0, graine=574, alb=0.64, relief=0.22)
    for cote, xj in ((-1, ax0 - 7.0), (1, ax1 + 7.0)):                                            # l'arête du manteau
        P.rampe(m_rect(P, xj - 0.6 if cote > 0 else xj, -6.6, 0.8, 69.2), (0.9 if cote < 0 else 0.3) * Lh, R_GRANIT, 0.5)
    foyer = m_rect(P, ax0, 34.0, ax1 - ax0, 28.6)
    Lf = lumiere(P, [(FX, 58.0, 13.0, 1.5 * vac)], 0.05)
    appareil(P, foyer, Lf, (FX, 58.0), lh=3.0, lw=5.0, graine=575, alb=0.5, rampe=R_CUIVRE[:1] + R_BOIS[1:4] + R_CUIVRE[1:4], relief=0.26)
    P.remplir(foyer & (Y < 35.4), R_BOIS[0])                                                      # l'ombre du linteau
    for cote, xj in ((-1, ax0), (1, ax1 - 1.2)):                                                  # les jambages, côté feu
        P.rampe(m_rect(P, xj, 34.0, 1.2, 28.6), (0.7 + 0.02 * (Y - 34.0)) * vac * 0.9, R_GRANIT[2:] + [LU4], 0.5)
    # Le linteau de chêne, et ce qui est posé dessus.
    lint = m_rect(P, ax0 - 10.0, 28.0, ax1 - ax0 + 20.0, 5.6)
    lames(P, lint, Lh + 0.1, larg=30.0, graine=576, vertical=False, alb=0.66, noeuds=0.9)
    P.rampe(lint & (Y > 32.4), (0.95 - 0.006 * np.abs(X - FX)) * vac, R_BOIS[3:], 0.5)             # son dessous, léché par le feu
    P.rampe(lint & (Y < 28.6), 0.86 * Lh + 0.1, R_BOIS, 0.5)
    for xc in (ax0 - 8.0, ax1 + 5.0):                                                             # les corbeaux de pierre
        P.rampe(P.masque_poly([(xc, 33.6), (xc + 3.0, 33.6), (xc + 3.0, 38.6), (xc + 1.4, 38.6)]), 0.66 * Lh, R_GRANIT, 0.5)
    # Au-dessus du linteau : un petit tableau, la Dent-Creuse du temps où elle éclairait (deux éclats, un long).
    tx_, ty_, tw, th = 138.0, 0.6, 28.0, 14.0
    P.rampe(m_rect(P, tx_ + 0.8, ty_ + th, tw, 1.0), 0.2 * Lh, R_GRANIT, 0.5)                       # son ombre
    P.rampe(m_rect(P, tx_, ty_, tw, th), (0.5 + 0.02 * (X - tx_) - 0.02 * (Y - ty_)) * (0.4 + Lh), [GO1, GO2, LAITON, LAITON2, LU5], 0.5)
    toile_ = m_rect(P, tx_ + 1.4, ty_ + 1.4, tw - 2.8, th - 2.8)
    P.rampe(toile_, 0.16 + 0.05 * (Y - ty_) + 0.14 * (pg.fbm(X / 5.0, Y / 1.6, 2, 5741) - 0.5), R_NUIT, 0.5)
    P.remplir(toile_ & (Y > ty_ + 9.4), NU1)                                                      # la mer
    P.remplir(toile_ & (Y > ty_ + 9.4) & (pg.fbm(X / 1.6, Y * 2.0, 2, 5742) > 0.62), NU3)
    lx_ = tx_ + 9.0
    fais = P.masque_poly([(lx_, ty_ + 4.0), (tx_ + tw - 1.4, ty_ + 1.6), (tx_ + tw - 1.4, ty_ + 6.4)]) & toile_
    P.remplir(fais, BM1)
    P.remplir(fais & (np.abs(Y - ty_ - 4.0) < 0.12 * (X - lx_)), LU4)
    P.poly([(lx_ - 4.0, ty_ + 10.0), (lx_ - 1.6, ty_ + 8.4), (lx_ + 2.0, ty_ + 8.6), (lx_ + 4.6, ty_ + 10.0)], NU0)         # le rocher
    P.poly([(lx_ - 1.0, ty_ + 8.6), (lx_ + 1.0, ty_ + 8.6), (lx_ + 0.6, ty_ + 4.6), (lx_ - 0.6, ty_ + 4.6)], BM3)       # la tour
    P.rect(lx_ + 0.2, ty_ + 4.6, 0.4, 4.0, BM1)
    P.rect(lx_ - 0.8, ty_ + 3.4, 1.6, 1.2, LU5)                                                   # la lanterne
    P.poly([(lx_ - 1.0, ty_ + 3.4), (lx_ + 1.0, ty_ + 3.4), (lx_, ty_ + 2.4)], NU0)
    for k in range(5):                                                                            # son reflet dans l'eau
        P.trait(lx_ - 0.8 + (k % 2) * 0.6, ty_ + 10.2 + k * 0.5, lx_ + 0.8 + (k % 2) * 0.6, ty_ + 10.2 + k * 0.5, LU3)
    lisere(P, toile_, GO1, 0, -1)
    lisere(P, toile_, GO1, -1, 0)
    P.trait(tx_ + tw / 2, ty_, tx_ + tw / 2, ty_ - 2.6, R_GRANIT[1])
    mx0 = ax0 - 7.0
    for i, (dx, r) in enumerate(((5.0, 3.0), (11.6, 3.4), (18.6, 3.0))):                           # trois plats d'étain debout
        a = m_ell(P, mx0 + dx, 28.0 - r, r, r)
        P.rampe(a, (0.5 + 0.2 * (Y - 28.0 + r) / r + 0.16 * (X - mx0 - dx) / r) * (0.4 + Lh), R_ETAIN, 0.5)
        P.remplir(m_ell(P, mx0 + dx, 28.0 - r, r * 0.6, r * 0.6) & ~m_ell(P, mx0 + dx, 28.2 - r, r * 0.52, r * 0.52), GR2)
        P.point(mx0 + dx + r * 0.4, 28.6 - r * 0.5, BLANC if int(p * 8 + i * 2) % 5 == 0 else BM4)
    # Un bougeoir, une cruche, le bigorneau de l'enseigne (une grosse coquille, qui « tousse » une petite buée).
    P.rect(mx0 + 25.0, 24.2, 1.2, 3.8, CREME)
    P.rect(mx0 + 24.0, 27.4, 3.2, 0.7, LAITON2)
    cru = m_ell(P, mx0 + 50.0, 24.6, 3.0, 3.4) | m_rect(P, mx0 + 48.6, 19.8, 2.8, 2.4)
    P.rampe(cru, (0.4 + 0.4 * cylindre(P, mx0 + 47.0, mx0 + 53.0, FX) + 0.25 * (Y - 22) / 6.0) * (0.3 + Lh), R_CUIVRE, 0.5)
    P.courbe([(mx0 + 52.6, 21.6), (mx0 + 55.0, 23.4), (mx0 + 52.6, 26.0)], R_CUIVRE[1], 1)
    cq = (mx0 + 37.0, 23.6)
    coq = m_ell(P, cq[0], cq[1], 5.0, 4.4) | P.masque_poly([(cq[0] + 3.0, cq[1] - 3.0), (cq[0] + 8.6, cq[1] + 1.6), (cq[0] + 3.0, cq[1] + 4.4)])
    ang = np.arctan2(Y - cq[1], X - cq[0])
    ray = np.hypot(X - cq[0], Y - cq[1])
    spire = ((ray - 1.1 * (ang + math.pi) / math.pi) % 2.2) < 0.5
    P.rampe(coq, (0.52 + 0.3 * (Y - cq[1]) / 4.4 + 0.1 * (X - cq[0]) / 5.0) * (0.35 + Lh), R_PLATRE[2:], 0.5)
    P.remplir(coq & spire & (ray < 4.6), R_PLATRE[3])
    P.ell(cq[0] + 4.6, cq[1] + 1.0, 1.9, 2.0, R_BOIS[1])
    t = (p * 2) % 1.0                                                                             # il tousse
    if p < 0.5:
        for k in range(3):
            P.ell(cq[0] + 8.4 + 3.4 * t + k * 1.0, cq[1] - 0.2 - 1.6 * t - k * 0.8, 0.5 + 0.7 * t, 0.5 + 0.6 * t, BM3 if t < 0.6 else BM1)
    # Le feu : les bûches, les braises, les flammes, les landiers.
    for (lx0, ly0, lx1, ly1) in ((139.0, 60.6, 165.0, 59.2), (142.0, 58.4, 162.0, 60.6), (146.0, 57.6, 160.0, 56.8)):
        P.trait(lx0, ly0, lx1, ly1, R_BOIS[1], P.ep(1.5))
        P.trait(lx0, ly0 - 0.5, lx1, ly1 - 0.5, R_CUIVRE[1], 1)
        P.ell(lx0, ly0 + 0.3, 0.9, 1.0, R_BOIS[5])
    P.rampe(foyer & (Y > 60.4), 0.4 + 0.6 * (pg.fbm(X / 0.9, Y / 0.9 + p * 0.0, 2, 577) > 0.5) * (0.6 + 0.4 * np.sin(6.283 * (p * 2 + 0.37 * X))), R_FEU[:5], 0.5)
    flammes(P, 139.0, 167.0, 60.6, 17.0, 578, rampe=R_FEU[:6], masque=foyer, gain=0.9)
    flammes(P, 145.0, 161.0, 60.8, 9.0, 579, rampe=R_FEU[3:], masque=foyer, gain=0.8)
    for xl in (135.4, 170.0):                                                                     # les landiers de fer
        P.rect(xl - 0.5, 50.6, 1.0, 11.6, R_GRANIT[0])
        P.ell(xl, 50.0, 1.3, 1.3, R_GRANIT[1])
        P.point(xl + (0.5 if xl < FX else -0.9), 49.6, LU3)
        P.rect(xl - 1.6, 61.2, 3.2, 1.0, R_GRANIT[0])
    for i in range(7):                                                                            # les escarbilles qui montent
        t = (p + hz(i, 0, 580)) % 1.0
        P.point(143.0 + 20.0 * hz(i, 1, 580) + 1.6 * math.sin(t * 7 + i), 56.0 - 20.0 * t, LU5 if t < 0.35 else (LU3 if t < 0.7 else LU1))
    # La potence et la marmite de soupe : fonte noire, un liseré de feu sur le ventre, la vapeur.
    P.rect(ax0 + 1.2, 37.0, 0.9, 20.0, R_GRANIT[0])
    P.trait(ax0 + 1.6, 38.4, 142.6, 38.4, R_GRANIT[0], P.ep(0.7))
    P.trait(ax0 + 1.6, 46.0, 138.0, 38.8, R_GRANIT[0])
    sw = 0.3 * onde(p, 0.4)
    kx, ky = 141.4 + sw, 49.6
    for j in range(5):                                                                            # la chaîne
        P.point(141.6 + sw * j / 5.0, 39.4 + j * 1.3, R_GRANIT[2] if j % 2 else R_GRANIT[0])
    mar = (m_ell(P, kx, ky + 1.0, 6.2, 5.2) & (Y > ky - 2.6)) | m_rect(P, kx - 5.6, ky - 3.6, 11.2, 1.6)
    nx = (X - kx) / 6.2
    P.rampe(mar, 0.16 + 0.5 * np.clip(nx - 0.25, 0, 1) * vac + 0.26 * np.clip((Y - ky - 2.0) / 4.0, 0, 1) * (nx > -0.5), R_GRANIT[:4] + [R_CUIVRE[1], LU2, LU3], 0.5)
    P.ell(kx, ky - 3.6, 5.6, 1.2, R_GRANIT[1])
    P.ell(kx, ky - 3.6, 4.6, 0.8, LU1)                                                            # la soupe
    P.ell(kx + 1.0, ky - 3.6, 2.4, 0.4, LU2)
    P.courbe([(kx - 5.4, ky - 3.2), (kx, 44.4 - 4.0), (kx + 5.4, ky - 3.2)], R_GRANIT[0], 1)         # l'anse
    P.trait(kx + 2.0, ky - 4.0, kx + 5.6, ky - 9.0, R_ETAIN[3])                                     # la louche
    for j in range(3):
        P.ell(kx - 3.0 + j * 3.0, ky + 6.4, 0.7, 1.2, R_GRANIT[0])                                  # ses trois pieds
    fumerolle(P, kx, ky - 5.0, h=13.0, n=4, coul=BM4, force=0.42, large=1.1)
    # La dalle du foyer, qui avance dans la salle ; le tas de bûches, le soufflet, le tisonnier.
    dalle = P.masque_poly([(ax0 - 8.0, 62.4), (ax1 + 8.0, 62.4), (ax1 + 12.0, 66.0), (ax0 - 13.0, 66.0)])
    appareil(P, dalle, Ls * 0.9 + 0.1, (FX, 50.0), lh=1.9, lw=10.0, graine=581, alb=0.72, dy=0.6)
    lisere(P, dalle, R_GRANIT[1], 0, 1)
    for i, (bx_, by_) in enumerate(((184.6, 60.4), (188.6, 60.4), (192.6, 60.4), (186.6, 57.0), (190.6, 57.0), (188.6, 53.6))):
        bu = m_ell(P, bx_, by_, 2.0, 1.9)
        P.rampe(bu, (0.5 + 0.22 * hz(i, 0, 582) - 0.22 * (X - bx_) / 2.0) * (0.5 + Ls * 0.9), R_BOIS, 0.5)
        P.remplir(m_ell(P, bx_, by_, 1.0, 0.9) & ~m_ell(P, bx_, by_, 0.5, 0.5), R_BOIS[3])
        lisere(P, bu, R_BOIS[7], -1, 0, cond=Y < by_ + 0.8)
    P.trait(176.4, 46.0, 178.0, 62.0, R_GRANIT[0], P.ep(0.6))                                       # le tisonnier
    P.trait(175.2, 46.0, 177.6, 46.0, R_GRANIT[0])
    sf = P.masque_poly([(123.6, 40.0), (127.6, 40.0), (126.6, 47.0), (125.6, 50.2), (124.6, 47.0)])  # le soufflet, à son clou
    P.rampe(sf, (0.4 + 0.1 * (X - 123.6)) * (0.3 + Lh), R_BOIS, 0.5)
    P.rect(123.8, 43.0, 3.6, 0.5, LAITON)
    P.rect(125.2, 50.0, 0.8, 2.0, LAITON2)
    P.rect(124.0, 37.6, 0.8, 2.6, R_BOIS[5])
    P.rect(126.4, 37.6, 0.8, 2.6, R_BOIS[6])
    P.point(125.6, 36.8, R_GRANIT[0])

    # ---- La grande horloge de parquet (la clé) : caisse de chêne, fronton cintré, cadran d'émail, balancier de laiton.
    hx_, hy_ = 59.0, 8.0
    Lc = Lm + 0.1
    caisse = m_rect(P, hx_ - 6.0, hy_ + 16.0, 12.0, 38.0)
    tete = m_rect(P, hx_ - 7.4, hy_, 14.8, 16.0) | (m_ell(P, hx_, hy_, 7.4, 4.6) & (Y < hy_ + 0.2))
    socle = m_rect(P, hx_ - 7.8, hy_ + 46.0, 15.6, 8.4)
    corps_h = caisse | tete | socle
    lames(P, corps_h, Lc * (0.72 + 0.045 * (X - hx_ + 8.0)), larg=30.0, graine=583, vertical=True, alb=0.74, noeuds=0)
    P.rampe(corps_h & (X > hx_ + 4.4) & caisse | (tete & (X > hx_ + 5.8)) | (socle & (X > hx_ + 6.2)), 1.05 * Lc + 0.08, R_BOIS, 0.5)   # le flanc au feu
    P.rampe((caisse & (X < hx_ - 4.8)) | (tete & (X < hx_ - 6.2)) | (socle & (X < hx_ - 6.6)), 0.3 * Lc, R_BOIS, 0.5)
    for yy in (hy_ + 15.4, hy_ + 45.4):                                                           # les moulures
        P.rampe(m_rect(P, hx_ - 8.2, yy, 16.4, 1.4), (0.9 - 0.3 * (Y - yy)) * Lc, R_BOIS, 0.5)
    P.rampe(m_rect(P, hx_ - 8.6, hy_ + 54.0, 17.2, 1.0), 0.4 * Lc, R_BOIS, 0.5)
    lisere(P, tete, R_BOIS[7], 0, -1, cond=np.abs(X - hx_) < 6.6)
    P.ell(hx_, hy_ - 4.8, 1.2, 1.2, LAITON2)                                                      # la pomme du fronton
    P.point(hx_ + 0.3, hy_ - 5.2, LU5)
    cad = m_ell(P, hx_, hy_ + 8.0, 5.9, 5.9)
    P.rampe(cad, 0.5 + 0.3 * (X - hx_) / 5.9 - 0.2 * (Y - hy_ - 8) / 5.9, [GO1, LAITON, LAITON2, LU5], 0.5)
    em = m_ell(P, hx_, hy_ + 8.0, 4.9, 4.9)
    P.rampe(em, 0.62 + 0.2 * (X - hx_) / 4.9 - 0.16 * (Y - hy_ - 8.0) / 4.9, [BM2, BM4, CREME, LU5], 0.5)
    for k in range(12):
        a = k * math.pi / 6
        P.trait(hx_ + 3.6 * math.sin(a), hy_ + 8.0 - 3.6 * math.cos(a), hx_ + 4.3 * math.sin(a), hy_ + 8.0 - 4.3 * math.cos(a), ENCRE if k % 3 == 0 else GR2)
    P.trait(hx_, hy_ + 8.0, hx_ - 1.9, hy_ + 6.3, ENCRE, 2)                                        # sept heures moins vingt
    am = (40 + int(p * 8) * 0.0) / 60.0 * 2 * math.pi
    P.trait(hx_, hy_ + 8.0, hx_ + 3.9 * math.sin(am), hy_ + 8.0 - 3.9 * math.cos(am), ENCRE)
    P.point(hx_, hy_ + 8.0, LAITON2)
    P.remplir(m_ell(P, hx_ - 1.6, hy_ + 5.6, 2.2, 1.2) & em & (P.T > 0.5), BLANC)                   # le reflet du verre
    porte = m_rect(P, hx_ - 3.6, hy_ + 19.6, 7.2, 23.0)
    P.rampe(porte, 0.1 + 0.2 * (X - hx_ + 3.6) / 7.2 * Lc, R_BOIS[:4], 0.5)
    P.rampe(m_rect(P, hx_ - 4.2, hy_ + 19.0, 8.4, 24.2) & ~porte, 0.84 * Lc, R_BOIS, 0.5)
    for k, (dx, ly_) in enumerate(((-2.2, 9.0), (2.2, 13.0))):                                    # les deux poids, sur leurs chaînes
        P.trait(hx_ + dx, hy_ + 19.6, hx_ + dx, hy_ + 19.6 + ly_, GO2)
        P.rampe(m_rect(P, hx_ + dx - 0.8, hy_ + 19.6 + ly_, 1.6, 4.4), 0.3 + 0.5 * (X - hx_ - dx + 0.8) / 1.6, [GO1, LAITON, LAITON2, LU5], 0.5)
    ang = 0.2 * onde(p)                                                                           # le balancier
    bx_, by_ = hx_ + 18.6 * math.sin(ang), hy_ + 21.0 + 18.6 * math.cos(ang)
    P.trait(hx_, hy_ + 20.0, bx_, by_, LAITON)
    P.rampe(m_ell(P, bx_, by_, 2.3, 2.3), 0.4 + 0.4 * (X - bx_) / 2.3 - 0.3 * (Y - by_) / 2.3, [GO1, LAITON, LAITON2, LU5], 0.5)
    P.remplir(porte & (np.abs(X - Y * 0.5 - hx_ + 15.6) < 0.5) & (P.T > 0.4), BM1)                 # le reflet de la vitre
    P.ell(hx_ + 3.9, hy_ + 31.0, 0.5, 0.7, LAITON2)                                               # le bouton de la porte

    # ---- Le portemanteau : le ciré jaune qui goutte, un suroît, et la flaque au pied.
    P.rampe(m_rect(P, 69.0, 10.6, 16.0, 2.0), (0.8 - 0.2 * (Y - 10.6)) * (Lm + 0.1), R_BOIS, 0.5)
    for xq in (72.0, 77.0, 82.0):
        P.rect(xq - 0.5, 11.2, 1.0, 1.0, LAITON2)
        P.point(xq - 0.5, 12.4, R_BOIS[2])
    cx_, cy_ = 77.0, 12.0
    bal = 0.25 * onde(p, 0.3)
    cire = P.masque_poly([(cx_ - 3.4, cy_), (cx_ + 3.4, cy_), (cx_ + 6.6 + bal, cy_ + 31.0), (cx_ + 2.0 + bal, cy_ + 32.4), (cx_ - 2.4 + bal, cy_ + 31.2),
                          (cx_ - 6.6 + bal, cy_ + 32.0)])
    manche = P.masque_poly([(cx_ - 3.4, cy_ + 1.0), (cx_ - 7.6, cy_ + 5.0), (cx_ - 9.0 + bal, cy_ + 24.0), (cx_ - 5.6 + bal, cy_ + 24.6), (cx_ - 4.4, cy_ + 8.0)])
    manche2 = P.masque_poly([(cx_ + 3.4, cy_ + 1.0), (cx_ + 7.4, cy_ + 5.0), (cx_ + 9.0 + bal, cy_ + 23.0), (cx_ + 6.0 + bal, cy_ + 24.0), (cx_ + 4.4, cy_ + 8.0)])
    pli = 0.5 + 0.5 * np.sin((X - cx_) * 1.5 - (Y - cy_) * 0.08 * (X - cx_) + 1.0)
    vc = 0.26 + 0.05 * (X - cx_ + 7.0) + 0.24 * pli + 0.2 * (pg.fbm(X / 1.6, Y / 7.0, 2, 584) - 0.5)
    P.rampe(manche, (vc - 0.16) * (0.5 + 1.5 * Lm), R_CIRE, 0.5)
    P.rampe(cire, vc * (0.5 + 1.5 * Lm), R_CIRE, 0.5)
    P.rampe(manche2, (vc + 0.12) * (0.5 + 1.5 * Lm), R_CIRE, 0.5)
    lisere(P, cire | manche2, CIRE2, 1, 0, cond=(Y > cy_ + 3))
    lisere(P, cire, GO1, 0, 1)
    P.trait(cx_ + 0.2, cy_ + 3.0, cx_ + 0.6 + bal, cy_ + 31.0, GO2)                                 # la patte de boutonnage
    for j in range(5):
        P.point(cx_ + 1.2 + bal * j / 5.0, cy_ + 6.0 + j * 5.4, R_ETAIN[4])
    cap = m_ell(P, cx_, cy_ + 0.4, 4.0, 2.8) & (Y < cy_ + 2.2)
    P.rampe(cap, (0.5 + 0.1 * (X - cx_)) * (0.5 + 1.5 * Lm), R_CIRE, 0.5)
    P.ell(cx_, cy_ + 1.2, 2.2, 1.4, GO1)
    so = P.masque_poly([(82.0 - 4.4, 17.6), (82.0 - 2.2, 12.8), (82.0 + 2.2, 12.8), (82.0 + 5.4, 18.4), (82.0, 17.0)])        # le suroît
    P.rampe(so, (0.3 + 0.07 * (X - 78.0)) * (0.5 + 1.5 * Lm), R_CIRE, 0.5)
    for k, gx in enumerate((cx_ - 6.0, cx_ - 1.0, cx_ + 4.6)):                                    # il goutte
        t = (p + k * 0.37) % 1.0
        if t < 0.5:
            yy = cy_ + 32.4 + (64.0 - cy_ - 32.4) * (t / 0.5) ** 2
            P.trait(gx + bal, yy, gx + bal, yy + 0.9, BM3)
    fl = m_ell(P, cx_ - 0.6, 64.8, 7.6, 1.3) & (pg.fbm(X / 2.4, Y, 2, 585) > 0.24)
    P.rampe(fl, 0.34 + 0.3 * (pg.fbm(X / 2.2 + onde(p) * 0.3, Y * 1.6, 2, 586) - 0.5) + 0.1 * (X - cx_) / 7.0, [NU0, NU1, NU2, NU3, BM1], 0.5)
    lisere(P, fl, R_BOIS[1], 0, -1)
    lisere(P, fl, BM2, 0, 1, cond=X > cx_)
    for k, gx in enumerate((cx_ - 6.0, cx_ - 1.0, cx_ + 4.6)):
        t = (p + k * 0.37) % 1.0
        if t >= 0.5:
            u = (t - 0.5) / 0.5
            dd = np.hypot(X - gx, (Y - 64.8) * 3.2)
            P.remplir(fl & (np.abs(dd - 0.5 - 2.8 * u) < 0.32), BM3 if u < 0.5 else BM1)

    # ---- Le comptoir : chêne ciré, panneaux, le dessus qui brille ; la lampe à pétrole ; les lettres sous le torchon.
    cx0, cx1, cyt = -6.0, 38.0, 44.0
    face = m_rect(P, cx0, cyt + 2.2, cx1 - cx0, 62.6 - cyt - 2.2)
    lames(P, face, Lm * 1.15 + 0.04, larg=5.4, graine=587, vertical=True, alb=0.5, sens=1)
    for i in range(4):                                                                            # les panneaux moulurés
        x0 = cx0 + 2.6 + i * 10.6
        pan = m_rect(P, x0, cyt + 5.0, 8.4, 11.4)
        lames(P, pan, Lm * 1.25 + 0.05, larg=30.0, graine=588 + i, vertical=True, alb=0.6, noeuds=0)
        lisere(P, pan, R_BOIS[2], 0, -1)
        lisere(P, pan, R_BOIS[2], -1, 0)
        lisere(P, pan, R_BOIS[7], 1, 0)
        lisere(P, pan, R_BOIS[6], 0, 1)
        coeur = m_rect(P, x0 + 1.6, cyt + 6.8, 5.2, 7.8)
        lisere(P, coeur, R_BOIS[6], 0, -1)
        lisere(P, coeur, R_BOIS[2], 0, 1)
        lisere(P, coeur, R_BOIS[2], 1, 0)
    bout = m_rect(P, cx1, cyt + 2.2, 3.6, 62.6 - cyt - 2.2)                                         # le bout, tourné vers le feu
    lames(P, bout, Lm * 1.9 + 0.1, larg=1.8, graine=592, vertical=True, alb=0.62)
    dessus = m_rect(P, cx0, cyt, cx1 - cx0 + 4.8, 2.2)
    P.rampe(dessus, (0.9 - 0.22 * (Y - cyt)) * (Lm * 1.3 + 0.1), R_BOIS, 0.5)
    P.rampe(dessus & (Y < cyt + 0.5), 1.25 * (Lm * 1.3 + 0.1), R_BOIS, 0.5)
    P.rampe(m_rect(P, cx0, 61.0, cx1 - cx0 + 3.6, 1.6), 0.34 * Lm, R_BOIS, 0.5)                     # la plinthe du comptoir
    P.rect(cx0, 58.6, cx1 - cx0 + 3.6, 0.6, LAITON)                                               # le repose-pied de laiton
    P.remplir(m_rect(P, cx0, 58.6, cx1 - cx0 + 3.6, 0.6) & (np.abs(X - 30.0 - 6.0 * onde(p, 0.2)) < 2.0), LAITON2)
    # La lampe à pétrole, sa flamme, son halo.
    lx_, ly_ = 14.0, cyt
    P.rampe(m_ell(P, lx_, ly_ - 1.6, 2.6, 1.8), 0.4 + 0.3 * (X - lx_) / 2.6, [GO1, LAITON, LAITON2, LU5], 0.5)
    P.rect(lx_ - 1.0, ly_ - 4.0, 2.0, 1.0, LAITON)
    verre = (np.abs(X - lx_) < 1.7 - 0.5 * np.abs((Y - ly_ + 7.0) / 3.0)) & (Y > ly_ - 10.4) & (Y < ly_ - 4.0)
    halo(P, lx_, ly_ - 6.6, 12.0, LU3, 0.4)
    P.remplir(verre, LU4)
    lisere(P, verre, BM4, -1, 0)
    lisere(P, verre, LU5, 1, 0)
    fd = 0.3 * onde(p * 2, 0.3)
    P.poly([(lx_ - 0.6, ly_ - 4.4), (lx_ + 0.6, ly_ - 4.4), (lx_ + fd * 0.5, ly_ - 7.6)], LU5)
    P.point(lx_, ly_ - 5.0, BLANC)
    # Le paquet de lettres, sous le torchon vite rabattu : un coin dépasse, avec son cachet.
    P.poly([(2.0, cyt), (11.6, cyt), (11.0, cyt - 2.6), (2.6, cyt - 2.6)], CREME)
    for j in range(4):
        P.trait(2.4, cyt - 0.5 - j * 0.6, 11.2, cyt - 0.5 - j * 0.6, BM3 if j % 2 else R_PLATRE[5])
    P.poly([(9.0, cyt - 2.6), (13.0, cyt - 3.4), (12.6, cyt - 0.8), (9.4, cyt - 0.4)], T.CIEL[11])     # la lettre du dessus
    P.point(11.8, cyt - 2.0, LU2, 2)
    P.trait(9.8, cyt - 1.6, 11.0, cyt - 1.8, GR3)
    tor = P.masque_poly([(-1.0, cyt + 0.2), (0.6, cyt - 3.6), (5.0, cyt - 4.6), (9.6, cyt - 3.4), (10.4, cyt - 1.6), (6.0, cyt - 2.0), (3.0, cyt + 3.6), (0.0, cyt + 4.2)])
    car = ((np.floor(X / 1.3) + np.floor(Y / 1.3)) % 2 == 0)
    P.rampe(tor, (0.5 + 0.26 * car + 0.14 * np.sin(X * 1.9 + Y)) * (0.5 + 1.2 * Lm), R_TOILE, 0.5)
    # Un verre « déjà sec », une bouteille, deux chopes.
    P.rect(19.0, cyt - 3.6, 2.2, 3.6, BM2)
    P.rect(19.0, cyt - 3.6, 0.5, 3.6, BM4)
    P.rect(19.0, cyt - 0.6, 2.2, 0.6, BM3)
    P.point(20.6, cyt - 3.0, BLANC)
    bouteille(24.4, cyt, 9.0, 2.8, R_VERRE)
    chope(30.0, cyt, 1.1)
    chope(35.0, cyt, 1.0)

    # ---- La grande table et son banc : la chandelle, le bol de soupe, le sel, les poireaux, le pain, les trois crayons.
    Lt = lumiere(P, [(FX, 56.0, 40.0, 1.25 * vac), (103.0, 50.0, 12.0, 0.8)], 0.2)
    tx0, tx1, ty0, ty1 = 86.0, 121.0, 54.0, 60.0
    for (qx, qy) in ((tx0 + 3.0, ty0 + 1.0), (tx1 - 3.0, ty0 + 1.0)):                             # les pieds du fond
        P.rampe(m_rect(P, qx - 1.0, qy, 2.0, 67.4 - qy), 0.26 * Lt, R_BOIS, 0.5)
    plateau = P.masque_poly([(tx0 + 3.0, ty0), (tx1 - 3.0, ty0), (tx1 + 1.6, ty1), (tx0 - 1.6, ty1)])
    dyp = np.maximum(Y - 36.0, 0.3)
    up = (X - 103.0) / dyp
    P.rampe(plateau, (0.74 + 0.2 * hz(np.floor(up * 5.0), 0, 593) + 0.26 * (pg.fbm(up * 9.0, Y * 1.2, 2, 594) - 0.5)) * Lt, R_BOIS, 0.5)
    P.remplir(plateau & (((up * 5.0) % 1.0) < 0.06), R_BOIS[3])
    chant = m_rect(P, tx0 - 1.6, ty1, tx1 - tx0 + 3.2, 1.7)
    P.rampe(chant, (0.5 + 0.005 * (X - tx0)) * Lt, R_BOIS, 0.5)
    P.rampe(chant & (Y < ty1 + 0.42), 1.0 * Lt, R_BOIS, 0.5)
    ceint = m_rect(P, tx0 + 0.6, ty1 + 1.7, tx1 - tx0 - 1.2, 2.2)
    P.rampe(ceint, (0.3 + 0.003 * (X - tx0)) * Lt, R_BOIS, 0.5)
    for qx in (tx0, tx1 - 2.6):                                                                   # les pieds de devant, tournés
        pied = m_rect(P, qx, ty1 + 1.7, 2.6, 12.0) & (np.abs(X - qx - 1.3) < 1.3 - 0.4 * (np.sin((Y - ty1) * 1.4) > 0.3))
        P.rampe(pied, (0.3 + 0.5 * (X - qx) / 2.6) * Lt * 1.1, R_BOIS, 0.5)
    P.rampe(m_rect(P, tx0 + 2.6, 69.0, tx1 - tx0 - 5.2, 1.0), 0.34 * Lt, R_BOIS, 0.5)               # l'entretoise
    # Le banc, devant.
    banc = P.masque_poly([(88.0, 70.6), (119.0, 70.6), (121.6, 73.0), (85.4, 73.0)])
    P.rampe(banc, (0.7 + 0.2 * (pg.fbm(X / 6.0, Y * 2.0, 2, 595) - 0.5)) * Ls * 1.3, R_BOIS, 0.5)
    P.rampe(m_rect(P, 85.4, 73.0, 36.2, 1.2), (0.36 + 0.004 * (X - 85.0)) * Ls, R_BOIS, 0.5)
    for bx_ in (88.0, 116.6):
        P.rampe(m_rect(P, bx_, 74.2, 1.8, 4.0), (0.3 + 0.4 * (X - bx_) / 1.8) * Ls * 1.2, R_BOIS, 0.5)
    lisere(P, banc, R_BOIS[7], 0, -1, cond=X > 100)
    # La chandelle dans sa bouteille, et sa cire qui a coulé.
    bx_, by_ = 103.0, 57.4
    P.ell(bx_ - 3.4, by_ + 0.5, 4.0, 0.8, R_BOIS[3])                                               # son ombre, à l'opposé du feu
    bouteille(bx_, by_, 6.4, 2.6, R_VERRE, bouchon=False)
    P.rect(bx_ - 0.5, by_ - 9.4, 1.0, 3.2, CREME)
    P.point(bx_ - 0.9, by_ - 5.8, CREME)
    P.point(bx_ + 0.5, by_ - 5.0, CREME)
    halo(P, bx_, by_ - 10.6, 9.0, LU3, 0.36)
    fd = 0.35 * onde(p * 2, 0.6)
    P.poly([(bx_ - 0.7, by_ - 9.4), (bx_ + 0.7, by_ - 9.4), (bx_ + fd, by_ - 12.6)], LU4)
    P.poly([(bx_ - 0.4, by_ - 9.4), (bx_ + 0.4, by_ - 9.4), (bx_ + fd * 0.5, by_ - 11.2)], LU5)
    # Le bol de soupe fumant et sa cuillère ; la salière ; le pain entamé.
    sx_, sy_ = 111.0, 58.0
    P.ell(sx_ - 2.6, sy_ + 0.9, 4.0, 0.8, R_BOIS[3])
    P.ell(sx_, sy_, 3.6, 1.7, R_TOILE[2])
    P.ell(sx_, sy_ - 0.7, 3.6, 1.1, CREME)
    P.ell(sx_, sy_ - 0.7, 2.8, 0.7, LU2)
    P.ell(sx_ + 0.9, sy_ - 0.7, 1.3, 0.3, LU3)
    P.rect(sx_ - 3.0, sy_ + 0.4, 6.0, 0.4, R_TOILE[1])
    P.trait(sx_ + 3.8, sy_ + 0.6, sx_ + 7.4, sy_ - 0.4, R_ETAIN[4])
    fumerolle(P, sx_, sy_ - 1.6, h=9.0, n=3, d=0.3, coul=BM4, force=0.36, large=0.8)
    P.rect(116.6, 55.6, 1.6, 2.2, CREME)                                                          # le sel
    P.rect(116.6, 55.2, 1.6, 0.5, R_ETAIN[3])
    P.rect(117.8, 55.6, 0.4, 2.2, BM3)
    pain = m_ell(P, 94.6, 56.8, 4.6, 2.0)
    P.rampe(pain, 0.56 + 0.3 * (X - 94.6) / 4.6 - 0.3 * (Y - 56.8) / 2.0, R_BOIS[4:], 0.5)
    for k in range(3):
        P.trait(92.2 + k * 2.0, 55.6, 93.2 + k * 2.0, 57.4, R_BOIS[4])
    P.ell(98.8, 57.2, 0.9, 1.6, CREME)                                                            # la mie
    # Les poireaux : fûts blancs, feuilles bleu sarcelle, liés d'un brin.
    for k in range(3):
        y0 = 59.0 + k * 0.45
        P.trait(89.0, y0, 95.4, y0 - 0.5, CREME, 1)
        P.trait(91.0, y0, 86.0 - k, y0 + 0.3 - k * 0.4, T.S3, 1)
        P.trait(88.0, y0 + 0.3, 85.0 - k, y0 + 0.6, T.S2, 1)
    P.rect(92.4, 58.4, 0.5, 1.6, GO2)
    # Trois crayons, bien parallèles (M. Vernier) ; les papiers à en-tête d'Odile.
    for k in range(3):
        P.trait(113.6 - k * 0.5, 59.0 + k * 0.42, 118.6 - k * 0.5, 59.0 + k * 0.42, (LU2, CIRE2, R_TOILE[3])[k])
    P.poly([(98.0, 58.6), (103.6, 58.4), (104.4, 59.8), (98.0, 59.9)], T.CIEL[11])
    P.rect(98.8, 58.8, 2.6, 0.4, R_TOILE[2])
    P.trait(98.8, 59.4, 103.0, 59.3, BM3)

    # ---- Devant le feu : le chat sur le paillasson de corde, et une souris près des bûches.
    chx, chy = 130.6, 65.6
    s_ = 0.3 * onde(p)
    R_CHAT = [R_BOIS[1], R_BOIS[2], R_CUIVRE[1], LU2, LU3, LU4]
    cc = m_ell(P, chx, chy - 2.3 - s_ * 0.4, 4.8, 2.5 + s_ * 0.4)
    P.rampe(cc, 0.34 + 0.3 * (X - chx) / 4.8 - 0.26 * (Y - chy + 2.3) / 2.5 + 0.12 * (np.sin(X * 2.2) > 0.3), R_CHAT, 0.5)
    tt = m_ell(P, chx + 3.6, chy - 2.4, 2.1, 1.9)
    P.rampe(tt, 0.44 + 0.3 * (X - chx - 3.6) / 2.1 - 0.2 * (Y - chy + 2.4) / 1.9, R_CHAT, 0.5)
    fr = 0.5 if int(p * 8) % 6 == 0 else 0.0
    P.poly([(chx + 2.4, chy - 3.6), (chx + 2.8, chy - 5.6 - fr), (chx + 3.8, chy - 4.0)], R_CHAT[2])
    P.poly([(chx + 4.2, chy - 4.0), (chx + 5.2, chy - 5.4), (chx + 5.6, chy - 3.4)], R_CHAT[3])
    P.trait(chx + 3.2, chy - 2.4, chx + 4.2, chy - 2.2, R_BOIS[0])                                   # l'œil clos
    P.courbe([(chx - 4.2, chy - 1.2), (chx - 6.4, chy - 0.5), (chx - 7.6, chy - 1.4 - 1.0 * max(0.0, onde(p, 0.3)))], R_CHAT[2], P.ep(0.7))
    lisere(P, cc | tt, LU5, 1, 0, cond=Y < chy - 1.2)                                              # le poil au feu
    pg.souris(P, 68.4, 64.0, sens=1, coul=GR3)

    # ================================================================================================== premier plan
    tab.plan("premier", 1.0)
    # À gauche : un poteau et son aisselier, à contre-jour ; un filet de pêche y retombe avec ses boules de verre.
    Lpp = lumiere(P, [(FX, 40.0, 80.0, 0.9 * vac)], 0.1)
    pot = m_rect(P, -6.0, -16.0, 8.6, 96.0) | P.masque_poly([(2.6, -16.0), (15.0, -16.0), (2.6, -5.0)])
    lames(P, pot, Lpp * 0.4, larg=30.0, graine=596, vertical=True, alb=0.5, noeuds=0.6)
    P.rampe(pot & (X > 2.1) & (Y > -5.0), 0.5 * vac, R_BOIS, 0.5)                                  # l'arête qui prend le feu
    ais = P.masque_poly([(2.6, -5.0), (15.0, -16.0), (13.4, -16.0), (2.6, -6.4)])
    P.rampe(ais, 0.46 * vac, R_BOIS, 0.5)
    for j in range(5):                                                                            # un filet y retombe
        P.courbe([(2.6, -4.0 + j * 1.8), (7.0 + j * 0.4, -8.0 + j * 1.9 + 0.3 * onde(p, 0.08 * j)), (16.0 - j * 1.0, -16.0)], R_BOIS[0] if j % 2 else R_BOIS[2], 1)
    for i in range(6):
        x = 3.4 + i * 2.0
        P.trait(x, -5.0 - (x - 2.6) * 0.88, x + 0.6, -5.0 - (x - 2.6) * 0.5 + 4.6 * max(0.0, 1 - ((x - 8.0) / 6.0) ** 2), R_BOIS[2])
    bx_ = 6.4 + 0.3 * onde(p, 0.2)
    P.trait(6.4, -9.0, bx_, -3.4, R_BOIS[1])
    boule_verre(P, bx_, -0.6, 2.8, (FX, 30.0), rampe=R_NUIT[:5] + [LU4], filet=R_BOIS[1])
    # En bas à droite : un tonneau debout, cerclé de fer, et la chope qu'on y a laissée.
    tx_, ty_ = 185.0, 65.0
    ton = m_rect(P, tx_ - 13.0, ty_, 28.0, 16.0) & (np.abs(X - tx_) < 10.6 + 1.6 * np.sin((Y - ty_) / 15.0 * 2.0))
    Lt2 = lumiere(P, [(FX, 60.0, 34.0, 1.1 * vac)], 0.1)
    lames(P, ton, Lt2 * cylindre(P, tx_ - 11.0, tx_ + 11.0, FX), larg=2.9, graine=597, vertical=True, alb=0.56, noeuds=0, sens=-1)
    for yy in (ty_ + 1.6, ty_ + 9.6):
        P.rampe(ton & (Y >= yy) & (Y < yy + 1.2), 0.66 * Lt2 * cylindre(P, tx_ - 11.0, tx_ + 11.0, FX), R_GRANIT, 0.5)
        P.remplir(ton & (Y >= yy + 1.2) & (Y < yy + 1.6), R_BOIS[1])
    dess = m_ell(P, tx_, ty_, 10.6, 2.2)
    P.rampe(dess, (0.56 + 0.12 * (pg.fbm(X / 3.0, Y * 3.0, 2, 598) - 0.5) - 0.012 * (X - tx_)) * Lt2 * 1.5, R_BOIS, 0.5)
    lisere(P, dess, R_BOIS[7], 0, -1, cond=X < tx_ + 2)
    lisere(P, dess, R_BOIS[1], 0, 1)
    chope(tx_ + 2.0, ty_ + 0.6, 1.3)
    # En bas à gauche : un panier d'osier plein de bigorneaux.
    pan = m_ell(P, 9.0, 80.0, 12.0, 8.0) & (X > 4.0)
    rang = np.floor(Y / 0.82)
    tress = (((X + rang * 1.3) % 2.6) < 0.5)
    P.rampe(pan, (0.36 + 0.07 * (rang % 2) - 0.14 * tress + 0.014 * (X - 2.0)) * (0.6 + Lt2), [R_BOIS[0], R_BOIS[1], GO1, GO2, R_PLATRE[5]], 0.5)
    lisere(P, pan, R_PLATRE[5], 0, -1)
    for i in range(7):                                                                            # les bigorneaux
        P.ell(5.6 + i * 2.2, 72.6 + (i % 2) * 0.7 - 1.2 * math.sin(i * 0.5), 1.3, 1.0, (GR3, R_PLATRE[4], GR4)[i % 3])
        P.point(5.9 + i * 2.2, 72.3 + (i % 2) * 0.7 - 1.2 * math.sin(i * 0.5), BM3)
    voile(P, Y > 78.4, R_BOIS[0], 0.35)
    # La poussière dorée dans la lumière du feu.
    poussiere(P, 96, 8, 176, 58, 16, LU4, 599)


# =====================================================================================================================
# Le guet : vu de nuit, à travers un petit carreau (la clé). Au premier plan le rebord et une bougie éteinte ; dehors la
# brume bleu sombre et, très loin, une minuscule lueur à une fenêtre du phare noir.
# =====================================================================================================================
@decor("phare-eteint", "guet-de-nuit", soleil=(112.0, 22.0), tons=PHARE, nom="Le guet", matiere=True)
def guet_de_nuit(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    # ---- Dehors : la nuit, quelques étoiles derrière la brume, la mer devinée.
    pg.ciel(P, horizon=44.0, haut=0.0, halo=0.0, etoiles=0.16, disque=0)
    tab.plan("nuages", 0.08)
    pg.voiles(P, y=6.0, epais=12.0, seuil=0.56, graine=540)
    tab.plan("lointains", 0.2)
    P.rampe(Y > 40.0, 0.25 + 0.2 * (pg.fbm(X / 14.0, Y / 1.2, 3, 541) - 0.5) - 0.01 * (Y - 40), [ME0, ME1, ME2, NU3], 0.8)
    phare(P, 112.0, 40.0, 30.0, ENCRE, NU1)
    lueur_ = (p % 1.0) < 0.7                                    # la minuscule lueur : elle n'est pas toujours là
    if lueur_:
        P.point(112.0, 40.0 - 30.0 * 0.4, LU4, 2)
        halo(P, 112.4, 40.0 - 30.0 * 0.4 + 0.4, 5.0, LU3, 0.5)
        for j in range(5):                                      # son reflet, en pointillé sur l'eau
            if (j + int(p * 8)) % 2:
                P.point(112.0 + (j % 2) * 0.8, 44.0 + j * 2.0, LU2)
    for g, (y, ep) in enumerate(((36.0, 5.0), (44.0, 4.0), (52.0, 5.0), (24.0, 4.0))):
        brume(P, y, ep, 6 + g, T.CIEL[3 if g < 3 else 2], 0.55)
    tab.plan("moyen", 0.5)
    # ---- Le mur et la fenêtre : un petit carreau à croisillons de plomb, profond ; la buée dans les coins.
    wx0, wx1, wy0, wy1 = 46.0, 146.0, -6.0, 56.0
    dehors = (X > wx0) & (X < wx1) & (Y > wy0) & (Y < wy1)
    mur = ~dehors
    P.rampe(mur, 0.4 + 0.3 * (pg.fbm(X / 7.0, Y / 5.0, 3, 542) - 0.5) - np.hypot(X - 96, Y - 30) / 400.0, [ENCRE, NU0, GR1, GR2], 0.8)
    pierres_de_taille(P, mur & (Y < 62), GR1, ENCRE, lh=5.0, lw=11.0)
    emb = [(wx0, wy0), (wx0 + 6, wy0 + 4), (wx0 + 6, wy1 - 3), (wx0, wy1)]                  # l'embrasure, en biais
    P.poly(emb, GR2)
    P.poly([(wx1, wy0), (wx1 - 6, wy0 + 4), (wx1 - 6, wy1 - 3), (wx1, wy1)], ENCRE)
    P.poly([(wx0, wy0), (wx1, wy0), (wx1 - 6, wy0 + 4), (wx0 + 6, wy0 + 4)], NU0)
    for i in range(1, 4):                                       # les plombs
        P.rect(wx0 + 6 + i * 22.0 - 0.5, wy0 + 4, 1.0, wy1 - wy0 - 7, ENCRE)
    for j in range(1, 3):
        P.rect(wx0 + 6, wy0 + 4 + j * 18.4 - 0.5, wx1 - wx0 - 12, 1.0, ENCRE)
    vitre = (X > wx0 + 6) & (X < wx1 - 6) & (Y > wy0 + 4) & (Y < wy1 - 3)
    coin = np.minimum(np.minimum(X - wx0 - 6, wx1 - 6 - X), np.minimum(Y - wy0 - 4, wy1 - 3 - Y))
    voile(P, vitre, T.CIEL[5], np.clip(0.5 - coin / 14.0, 0, 0.5))                           # la buée
    voile(P, vitre & (np.abs((X - wx0) - (Y - wy0) * 0.8 - 40) < 2.5), T.CIEL[6], 0.25)       # un reflet
    for k in range(4):
        t = (p + k / 4.0) % 1.0
        P.trait(wx0 + 14 + k * 21, wy0 + 6 + 40 * t, wx0 + 14 + k * 21, wy0 + 8 + 40 * t, T.CIEL[6])
    # ---- Le rebord : une tablette de bois, large ; la bougie éteinte (sa mèche fume encore), une longue-vue, un châle.
    reb = (Y > 56.0) & (Y < 64.0)
    P.rampe(reb, 0.5 + 0.3 * (pg.fbm(X / 20.0, Y / 1.2, 2, 543) - 0.5), [BO1, BO2, BO3], 0.7)
    P.remplir(reb & (Y < 56.7), BO4)
    P.rampe(Y >= 64.0, 0.3 + 0.3 * (pg.fbm(X / 6.0, Y / 4.0, 3, 544) - 0.5), [ENCRE, NU0, GR1], 0.8)
    dallage(P, (Y > 70.0), 96.0, 60.0, BO2, BO1, larg=5.0, prof=0.0, joint=ENCRE)
    bougie(P, 128.0, 57.6, h=7.0, allumee=False)
    for k in range(4):
        t = (p + k / 4.0) % 1.0
        voile(P, np.hypot(X - (128.0 + 1.5 * math.sin(t * 5.0 + k)), Y - (49.0 - 12 * t)) < 0.6 + 1.2 * t, T.CIEL[6], 0.5 - 0.45 * t)
    P.poly([(66.0, 55.0), (92.0, 53.4), (92.6, 56.0), (66.4, 57.0)], LAITON)                 # la longue-vue
    P.poly([(66.0, 55.0), (92.0, 53.4), (92.2, 54.2), (66.2, 55.6)], LAITON2)
    P.rect(74.0, 53.8, 1.2, 3.2, BO1)
    P.rect(84.0, 53.2, 1.2, 3.2, BO1)
    P.ell(93.0, 54.7, 0.9, 1.5, T.CIEL[4])
    P.poly([(150.0, 56.0), (176.0, 55.0), (182.0, 64.0), (156.0, 68.0), (148.0, 62.0)], VI1)  # le châle
    P.poly([(152.0, 57.0), (174.0, 56.2), (178.0, 60.0), (154.0, 62.0)], VI2)
    for i in range(8):
        P.trait(156 + i * 3.2, 66.6 - i * 0.4, 156 + i * 3.2 + 0.3 * onde(p, 0.1 * i), 69.6 - i * 0.4, VI2)
    tab.plan("premier", 1.0)
    # ---- Premier plan : le rideau tiré, à gauche ; le dossier d'une chaise, à droite. Tout est dans le noir.
    rid = P.poly([(-6.0, -16.0), (26.0, -16.0), (22.0 + 0.5 * onde(p), 30.0), (30.0 + 0.8 * onde(p), 80.0), (-6.0, 80.0)], ENCRE)
    for j in range(5):
        P.courbe([(2 + j * 5.0, -16.0), (1 + j * 4.6 + 0.4 * onde(p, 0.1 * j), 30.0), (3 + j * 5.6 + 0.6 * onde(p, 0.1 * j), 80.0)], NU1, 1)
    P.rect(172.0, 44.0, 2.4, 36.0, ENCRE)
    P.rect(190.0, 42.0, 2.4, 38.0, ENCRE)
    for y in (46.0, 54.0, 62.0):
        P.rect(172.0, y, 20.0, 2.4, ENCRE)
        P.rect(172.0, y, 20.0, 0.5, NU1)
    poussiere(P, 60, 0, 140, 50, 8, T.CIEL[6], 545)
    # ---- Seconde passe : le guet se peuple, et prend une lumière.
    # Une lampe-tempête, hors champ à gauche, réchauffe le rebord : on veille, on n'a pas tout éteint.
    halo(P, 34.0, 56.0, 44.0, LU1, 0.5, ry=20)
    halo(P, 34.0, 58.0, 20.0, LU2, 0.45, ry=9)
    # Un feu de navire passe au large, lentement, et se reflète.
    nx = 52.0 + 88.0 * p
    if 52 < nx < 138 and not (86 < nx < 90 or 108 < nx < 112):
        P.point(nx, 41.6, LU4)
        P.point(nx, 43.4, LU2)
    # Le chat de la maison, en boule sur le rebord ; un bol de soupe qui fume ; le carnet de guet et son crayon.
    chat(P, 104.0, 56.6, coul=GR2)
    P.ell(80.0, 55.6, 3.6, 1.2, CREME)
    P.ell(80.0, 55.2, 2.8, 0.8, LU2)
    pg.vapeur(P, 80.0, 54.0, coul=BM2, h=9.0)
    P.poly([(58.0, 59.0), (70.0, 58.4), (71.0, 62.6), (59.0, 63.4)], CREME)
    for j in range(3):
        P.trait(60.0, 60.0 + j * 1.0, 68.0 - j * 2, 59.6 + j * 1.0, NU2)
    P.trait(70.0, 63.0, 76.0, 61.0, LAITON)
    # Au mur : un trousseau de clés qui se balance, une pendulette, une carte du large ; une toile dans l'embrasure.
    bal = 0.6 * onde(p)
    P.point(160.0, 20.0, GR4)
    P.trait(160.0, 20.0, 160.0 + bal, 26.0, GR3)
    for q in range(3):
        P.trait(160.0 + bal, 26.0, 159.0 + bal + q * 1.0, 30.0 + q * 0.6, LAITON2 if q % 2 else LAITON)
    pendule(P, 172.0, 6.0, 4.0, d=0.2, coul=BO2, heure=0.94, balancier=7.0)
    P.rect(20.0, 4.0, 18.0, 13.0, BM2)
    P.courbe([(22.0, 13.0), (28.0, 8.0), (34.0, 11.0), (37.0, 7.0)], NU1, 1)
    P.ell(33.0, 9.0, 0.9, 0.9, LU2)
    pg.toile_araignee(P, 52.0, -2.0, 9.0, sens=(1, 1), coul=BM2)
    pg.araignee(P, 140.0, -2.0, 7.0, d=0.6)
    pg.papillon_de_nuit(P, 96.0, 20.0, 12.0, coul=BM3, d=0.2)     # il se cogne au carreau
    for k in range(3):                                          # la pluie fine sur la vitre
        t = (p + k / 3.0 + 0.5) % 1.0
        P.trait(62.0 + k * 30, 0.0 + 44 * t, 62.4 + k * 30, 2.0 + 44 * t, BM2)
    P.rect(4.0, 60.0, 9.0, 12.0, BO1)                             # des bottes au pied du mur, un ciré plié
    P.rect(4.0, 60.0, 9.0, 1.4, BO3)
    P.rect(140.0, 64.0, 16.0, 5.0, CIRE)
    P.rect(140.0, 64.0, 16.0, 1.0, CIRE2)


# =====================================================================================================================
# Le Passe-Pied : une chaussée de pierres claires et de goémon à marée basse, entre des flaques et de la vase luisante,
# qui file dans la brume de l'aube vers un rocher surmonté d'un phare (la clé, en haut à droite).
# =====================================================================================================================
@decor("phare-eteint", "passe-pied", soleil=(60.0, 26.0), tons=AUBE, nom="Le Passe-Pied", matiere=True)
def passe_pied(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=40.0, haut=0.1, halo=0.3, disque=4.0)
    tab.plan("nuages", 0.08)
    pg.voiles(P, y=-4.0, epais=10.0, seuil=0.56, graine=550)
    pg.barres(P, [(40, 28.0, 22, 1.2), (96, 22.0, 16, 1.0)])
    tab.plan("lointains", 0.2)
    phare(P, 146.0, 36.0, 44.0, T.CIEL[2], T.CIEL[4])
    for i in range(6):
        goeland(P, 100 + 10 * i + 3 * onde(p, 0.2 * i), -4 + 9 * hz(i, 1, 551) + onde(p, 0.3 * i), pose=False)
    brume(P, 34.0, 5.0, 11, T.CIEL[9], 0.65)
    brume(P, 24.0, 4.0, 12, T.CIEL[8], 0.4)
    brume(P, 10.0, 4.0, 13, T.CIEL[8], 0.3)
    tab.plan("moyen", 0.5)
    # ---- L'estran : la vase luisante, miroir du ciel, des flaques, des rigoles ; la mer s'est retirée très loin.
    estran = Y > 38.0
    v = pg.valeur_ciel(P, X, 38.0 - (Y - 38.0) * 0.9)
    P.rampe(estran, 0.2 + 0.7 * v + 0.22 * (pg.fbm(X / 12.0, Y / 1.4, 3, 552) - 0.5) - 0.006 * (Y - 38), T.EAU, 0.8)
    flaque = (pg.fbm(X / 9.0, (Y - 38) * (1 + (80 - Y) / 26.0) / 3.0, 3, 553) > 0.66) & estran & (Y < 68.0)
    P.rampe(flaque, 0.34 + 0.4 * v, T.EAU, 0.6)
    P.remplir(P.crete(flaque), T.EAU[2])
    cell = (P.XI + (P.YI % 3) * 2) // 3
    eclat = estran & (hz(cell, P.YI, 554) < 0.5 * np.exp(-((X - 60) / (4 + (Y - 38) * 0.5)) ** 2)) & (np.floor(((p + hz(cell, P.YI, 555)) % 1.0) * 4) < 2)
    P.remplir(eclat, T.SOL)
    # La chaussée : de grosses pierres claires, posées de biais, qui serpentent vers le rocher ; le goémon dessus.
    chemin = lambda y: 146.0 - (_a(y) - 38.0) ** 1.18 * 1.9 + 4.0 * np.sin(_a(y) / 6.0)
    for i in range(34):
        y = 40.0 + (i / 33.0) ** 1.6 * 44.0
        k = 0.4 + (y - 38) / 24.0
        x = float(chemin(y))
        for j in (-1, 0, 1):
            px_, py_ = x + j * 5.4 * k + (hz(i, j + 2, 556) - 0.5) * 2 * k, y + (hz(i, j + 5, 556) - 0.5) * k
            r = (2.6 + 1.2 * hz(i, j + 8, 556)) * k
            P.ell(px_, py_ + r * 0.25, r * 1.1, r * 0.45, T.EAU[1])
            P.ell(px_, py_, r, r * 0.42, GR3 if hz(i, j + 11, 556) < 0.5 else GR4)
            P.ell(px_ - r * 0.2, py_ - r * 0.12, r * 0.6, r * 0.2, BM4)
            if hz(i, j + 14, 556) < 0.4 and k > 0.5:                                         # une touffe de goémon
                for q in range(4):
                    P.courbe([(px_ + (q - 1.5) * r * 0.3, py_), (px_ + (q - 1.5) * r * 0.5 + 0.3 * onde(p, 0.1 * q), py_ - r * 0.5)],
                             GO1 if q % 2 else GO2, P.ep(0.4))
    for i in range(12):                                         # des piquets de bouchot, de travers
        x, y = 8 + 15 * i + 6 * hz(i, 1, 557), 48 + 22 * hz(i, 2, 557)
        if abs(x - float(chemin(y))) < 14:
            continue
        k = 0.4 + (y - 38) / 40.0
        P.trait(x, y, x + (hz(i, 3, 557) - 0.5) * 2, y - 6 * k, GR1, P.ep(0.6 * k))
        P.ell(x, y + 0.3, 1.6 * k, 0.4 * k, T.EAU[1])
    for i, (x, y) in enumerate(((30.0, 52.0), (84.0, 47.0), (170.0, 56.0))):
        goeland(P, x, y, sens=1 if i % 2 else -1)
    barque_a_sec(P, 24.0, 64.0, 22.0, coul=(NU1, NU3, BM3))
    P.courbe([(35.0, 62.0), (44.0, 66.0), (50.0, 64.6)], GO2, 1)
    brume(P, 42.0, 3.0, 14, T.CIEL[9], 0.5)
    brume(P, 50.0, 2.6, 15, T.CIEL[8], 0.3, x0=80)
    tab.plan("premier", 1.0)
    # ---- Premier plan : la grève où l'on se tient : galets, goémon noir, une balise à damier, une ancre rouillée.
    f_g = lambda x: 74.4 + 1.0 * np.sin(_a(x) / 17.0) + 0.5 * np.sin(_a(x) / 5.0)
    pg.sol(P, f_g, [T.N1, T.N2, GR1, GR2, GR3], chemin=77.6, graine=558, lisere=2.0)
    for i in range(70):
        x, y = -6 + 204 * hz(i, 1, 559), 75.4 + 4.4 * hz(i, 2, 559)
        r = 0.6 + 1.2 * hz(i, 3, 559)
        P.ell(x, y, r, r * 0.6, (GR2, GR3, GR4, BM2)[i % 4])
        P.point(x - r * 0.3, y - r * 0.3, BM4)
    for i in range(16):
        x = -4 + 13 * i + 5 * hz(i, 1, 560)
        if 26 < x < 58 or 132 < x < 168:
            continue
        for q in range(5):
            P.courbe([(x + q * 0.9, 76.0), (x + q * 1.4 - 2 + 0.4 * onde(p, 0.1 * q + i), 76.0 - 2.4 - 2 * hz(i, q, 561))], GO1 if q % 2 else ENCRE, P.ep(0.5))
    bx_ = 184.0                                                 # la balise
    P.rect(bx_ - 1.0, 40.0, 2.0, 40.0, ENCRE)
    for j in range(5):
        P.rect(bx_ - 1.0, 42.0 + j * 7.0, 2.0, 3.5, BM4)
    P.poly([(bx_ - 5.0, 40.0), (bx_ + 5.0, 40.0), (bx_, 32.0)], ENCRE)
    P.poly([(bx_ - 2.4, 39.0), (bx_ + 2.4, 39.0), (bx_, 35.0)], LU2)
    goeland(P, bx_, 32.0, sens=-1)
    pg.roseaux(P, -6.0, 8.0, n=5, haut=(8.0, 18.0), penche=1.0, graine=562)
    # ---- Seconde passe : la vie de l'estran.
    for i in range(3):                                          # des crabes, qui filent de travers
        t = (p + i / 3.0) % 1.0
        cx_ = 60.0 + 30 * i + 6 * (t if i % 2 else 1 - t)
        P.ell(cx_, 71.0 + i * 1.2, 1.6, 0.9, LU2)
        P.trait(cx_ - 1.6, 71.0 + i * 1.2, cx_ - 2.6, 70.2 + i * 1.2 - 0.3 * onde(p * 2), LU2)
        P.trait(cx_ + 1.6, 71.0 + i * 1.2, cx_ + 2.6, 70.2 + i * 1.2 - 0.3 * onde(p * 2, 0.5), LU2)
    for i in range(5):                                          # les trous des coques : un jet d'eau, de temps en temps
        if (p + 0.2 * i) % 1.0 < 0.2:
            P.trait(20.0 + i * 34, 62.0 + (i % 2) * 6, 20.0 + i * 34, 60.0 + (i % 2) * 6, BM4)
    v = onde(p)                                                 # un fanion sur la balise
    P.poly([(184.0, 32.0), (190.0, 30.6 + 0.6 * v), (184.0, 29.0)], LU2)
    pg.goutte(P, 120.0, 62.0, 62.0, coul=BM4, d=0.3, flaque=BM4)  # la pluie fine, sur une flaque
    pg.goutte(P, 70.0, 58.0, 58.0, coul=BM4, d=0.7, flaque=BM4)
    P.courbe([(100.0, 76.0), (108.0, 74.0), (116.0, 76.4)], GO2, 1)                               # un cordage échoué, une bouteille
    P.rect(122.0, 75.0, 4.0, 1.6, T.S2)
    P.rect(126.0, 75.4, 1.4, 0.8, T.S3)
    for i in range(4):                                          # des bécasseaux courent au bord de l'eau
        t = (p + i / 4.0) % 1.0
        P.ell(130 + 10 * i + 4 * t, 46.0 + (i % 2), 0.9, 0.7, GR2)
        P.trait(130 + 10 * i + 4 * t, 46.6 + (i % 2), 130 + 10 * i + 4 * t, 47.6 + (i % 2), LU2)


# =====================================================================================================================
# Au pied de la Dent-Creuse : le bas de la tour de granit, vue de tout près. Une lourde porte cloutée sans poignée (la
# clé), des marches mouillées, des traces de goudron ; la mer remonte autour du rocher. Le sol est à y = 68.
# =====================================================================================================================
@decor("phare-eteint", "pied-du-phare", soleil=(20.0, 6.0), tons=PHARE, nom="Au pied de la Dent-Creuse", matiere=True)
def pied_du_phare(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=58.0, haut=0.2, halo=0.12, disque=0)
    tab.plan("nuages", 0.08)
    pg.voiles(P, y=0.0, epais=12.0, seuil=0.52, graine=570)
    pg.voiles(P, y=30.0, epais=9.0, seuil=0.55, graine=571)
    tab.plan("lointains", 0.2)
    # ---- La mer qui remonte, grise, des deux côtés de la tour ; la côte, loin, quelques lumières de Trébrume.
    mer = Y > 52.0
    P.rampe(mer, 0.4 + 0.25 * (pg.fbm((X + 2 * onde(p)) / 14.0, Y / 1.2, 3, 572) - 0.5) - 0.012 * (Y - 52), [ME0, ME1, ME2, NU3, NU4], 0.8)
    pg.crete(P, lambda x: pg.profil(x, 52.0, 4.0, 22.0, 573), [T.CIEL[2], T.CIEL[3], T.CIEL[4], T.CIEL[5]], 0.4, bas=52.6)
    for i in range(7):
        if (p + hz(i, 1, 574)) % 1.0 < 0.85:
            P.point(8 + 5 * i + 2 * hz(i, 2, 574), 50.4 + hz(i, 3, 574), LU4)
    for i in range(10):                                         # les crêtes d'écume qui avancent
        t = (p + hz(i, 1, 575)) % 1.0
        y = 54 + 12 * hz(i, 2, 575)
        x = (-10 + 220 * hz(i, 3, 575) + 6 * t) % 200
        if abs(x - 100) > 34:
            P.trait(x, y, x + 5 + 4 * hz(i, 4, 575), y, BM3 if t < 0.5 else BM1)
    brume(P, 46.0, 5.0, 21, T.CIEL[6], 0.5)
    brume(P, 30.0, 5.0, 22, T.CIEL[5], 0.4)
    tab.plan("moyen", 0.5)
    # ---- La tour : énorme, elle sort du cadre par le haut. Granit en gros blocs, lichens, coulures de goudron.
    cx = 100.0
    demi = lambda y: 44.0 + (_a(y) - 60.0) * 0.1
    tour = (np.abs(X - cx) < demi(Y)) & (Y < 62.0)
    u = (X - cx) / demi(Y)
    P.rampe(tour, 0.62 - 0.4 * u - 0.12 * u * u + 0.2 * (pg.fbm(X / 4.0, Y / 3.0, 3, 576) - 0.5), [ENCRE, GR1, GR2, GR3, GR4], 0.75)
    pierres_de_taille(P, tour, GR2, GR1, lh=6.4, lw=13.0, dx=cx)
    for i in range(9):                                          # lichens et coulures de goudron
        x, y = cx - 38 + 76 * hz(i, 1, 577), -10 + 60 * hz(i, 2, 577)
        if abs(x - cx) < 20 and y > 12:
            continue
        if i % 2:
            voile(P, tour & (np.hypot(X - x, (Y - y) * 1.4) < 3 + 3 * hz(i, 3, 577)) & (pg.fbm(X / 1.5, Y / 1.5, 2, 578) > 0.45), CIRE, 0.6)
        else:
            voile(P, tour & (np.abs(X - x - 0.6 * np.sin(Y / 3.0)) < 1.0 + 0.6 * hz(i, 3, 577)) & (Y > y) & (Y < y + 14 + 12 * hz(i, 4, 577)), ENCRE, 0.8)
    P.remplir((np.abs(X - cx) < demi(Y) + 2.0) & (np.abs(Y - 0.0) < 1.6), GR3)                 # un bandeau de pierre
    P.remplir((np.abs(X - cx) < demi(Y) + 2.0) & (np.abs(Y - 1.8) < 0.5), ENCRE)
    for (dx, y) in ((-24.0, -8.0), (22.0, 14.0)):                # deux meurtrières, noires
        P.rect(cx + dx - 1.4, y, 2.8, 8.0, ENCRE)
        P.rect(cx + dx - 2.2, y + 8.0, 4.4, 1.0, GR3)
    # La porte : chêne noirci, bandes de fer, des clous par dizaines ; aucune poignée. Un heurtoir trop haut.
    px_, top, bas_ = cx, 30.0, 61.0
    arc = lambda r: ((np.hypot(X - px_, Y - top) < r) & (Y <= top)) | ((np.abs(X - px_) < r) & (Y > top) & (Y < bas_))
    P.rampe(arc(19.0), 0.6 - 0.3 * (X - px_) / 19.0, [GR1, GR3, GR4], 0.5)
    for a in range(-80, 81, 16):
        r = math.radians(a - 90)
        P.trait(px_ + 15 * math.cos(r), top + 15 * math.sin(r), px_ + 19 * math.cos(r), top + 19 * math.sin(r), GR1)
    porte = arc(15.0)
    P.rampe(porte, 0.4 - 0.3 * (X - px_) / 15.0 + 0.3 * (pg.fbm(X / 1.2, Y / 16.0, 2, 579) - 0.5), [ENCRE, BO1, BO2], 0.6)
    for i in range(-3, 4):
        P.remplir(porte & (np.abs(X - px_ - i * 4.2) < 0.25), ENCRE)
    for y in (26.0, 40.0, 54.0):
        P.remplir(porte & (np.abs(Y - y) < 1.2), GR1)
        P.remplir(porte & (np.abs(Y - y + 1.0) < 0.3), GR3)
    for j in range(8):
        for i in range(-3, 4):
            x, y = px_ + i * 4.2 + 2.1, 19.0 + j * 5.4
            if (np.hypot(x - px_, min(y - top, 0)) < 14) and abs(x - px_) < 14:
                P.point(x, y, GR4)
                P.point(x, y + 0.5, ENCRE)
    P.ell(px_, 34.0, 2.2, 2.2, GR3)                              # le heurtoir : un anneau dans une gueule de poisson
    P.ell(px_, 34.0, 1.2, 1.2, BO1)
    P.courbe([(px_ - 1.6, 35.6), (px_, 39.0 + 0.3 * onde(p)), (px_ + 1.6, 35.6)], GR4, P.ep(0.6))
    voile(P, porte & (Y > 54), ME2, 0.3)
    # Les marches mouillées, le rocher, les flaques ; une chaîne et son anneau scellé ; un bidon oublié.
    for j in range(4):
        P.rect(px_ - 24 - j * 5.0, 61.0 + j * 2.2, 48 + j * 10.0, 2.2, GR3 if j % 2 else GR2)
        P.rect(px_ - 24 - j * 5.0, 61.0 + j * 2.2, 48 + j * 10.0, 0.5, BM2)
        voile(P, (X > px_ - 24 - j * 5.0) & (X < px_ + 24 + j * 5.0) & (np.abs(Y - 62.4 - j * 2.2) < 0.5), BM3, 0.3)
    f_roc = lambda x: 66.0 + 2.0 * np.sin(_a(x) / 14.0) + 1.0 * np.sin(_a(x) / 4.0) + 6.0 * (np.abs(_a(x) - cx) / 100.0) ** 2
    roc = Y > f_roc(X)
    P.rampe(roc, 0.5 + 0.4 * (pg.fbm(X / 6.0, Y / 2.4, 3, 580) - 0.5) - 0.02 * (Y - 66), [ENCRE, GR1, GR2, GR3], 0.8)
    P.remplir(P.crete(roc) & (pg.fbm(X / 6.0, Y * 0, 2, 581) > 0.5), BM2)
    for (x, y, rx) in ((30.0, 72.0, 9.0), (150.0, 73.0, 11.0), (76.0, 75.6, 6.0)):              # les flaques : elles reflètent le ciel
        P.ell(x, y, rx, 1.5, ME1)
        P.ell(x, y - 0.3, rx * 0.8, 0.9, NU3)
        if int(p * 8 + x) % 4 == 0:
            P.ell(x + 2, y, 1.6, 0.4, BM2)
    P.ell(64.0, 58.0, 1.6, 1.6, GR1)
    for i in range(9):
        P.ell(64.0 - i * 1.8, 60.0 + i * 1.5 + 0.3 * math.sin(i + p * 6.283), 0.9, 0.7, GR3 if i % 2 else GR1)
    P.rect(136.0, 62.0, 6.0, 7.0, LU1)
    P.rect(136.0, 62.0, 1.6, 7.0, LU2)
    P.rect(137.6, 60.6, 2.0, 1.6, GR3)
    P.ell(139.0, 69.4, 4.0, 0.9, ENCRE)
    tab.plan("premier", 1.0)
    # ---- Premier plan : les rochers noirs où la mer se brise, de chaque côté ; l'écume qui retombe.
    for (x0, cote) in ((-6.0, 1), (198.0, -1)):
        pts = [(x0, 80.0), (x0, 52.0), (x0 + cote * 10, 56.0), (x0 + cote * 18, 66.0), (x0 + cote * 30, 72.0), (x0 + cote * 40, 80.0)]
        m = P.poly(pts, ENCRE)
        P.rampe(m, 0.3 + 0.5 * (pg.fbm(X / 4.0, Y / 3.0, 3, 582) - 0.5), [ENCRE, NU0, GR1], 0.8)
        for i in range(8):
            t = (p + i / 8.0) % 1.0
            x = x0 + cote * (30 + 6 * hz(i, 1, 583))
            y = 72.0 - 10 * math.sin(t * math.pi) * (0.5 + hz(i, 2, 583))
            if t < 0.9:
                P.point(x + cote * 6 * t, y, BM4 if t < 0.5 else BM2, 2 if t < 0.3 else 1)
    voile(P, Y > 78.0, ENCRE, 0.4)
    brume(P, 70.0, 2.4, 23, T.CIEL[5], 0.3)
    # ---- Seconde passe : la vie au pied de la tour.
    goeland(P, 60.0, -0.8, sens=1)
    goeland(P, 134.0, -0.8, sens=-1)
    pg.goutte(P, 86.0, 1.8, 61.0, coul=BM3, d=0.2)                # le bandeau goutte
    pg.goutte(P, 118.0, 1.8, 61.0, coul=BM3, d=0.7)
    pg.yeux(P, 76.0, -4.0, coul=LU4, d=0.3, ecart=1.2)            # une lueur, là-haut, derrière la meurtrière : quelqu'un ?
    for i in range(3):                                          # des bernacles et des moules sur le rocher, une étoile de mer
        P.ell(60.0 + i * 3.0, 70.0 + (i % 2), 1.0, 0.7, NU1)
    P.poly([(126.0, 72.0), (128.0, 70.6), (130.0, 72.0), (129.2, 74.0), (126.8, 74.0)], LU2)
    P.courbe([(140.0, 64.0), (146.0, 62.0 + 0.4 * onde(p)), (152.0, 64.0)], GO2, 1)             # une algue prise dans la chaîne
    bal = 0.5 * onde(p, 0.3)                                    # un écriteau de bois cloué de travers : une tête de mort ? non, un poisson
    P.rect(128.0, 40.0, 10.0, 6.0, BO2)
    P.ell(133.0, 43.0, 2.6, 1.2, BM3)
    P.poly([(135.4, 43.0), (137.0, 41.8), (137.0, 44.2)], BM3)
    pg.papillon_de_nuit(P, 100.0, 34.0, 5.0, coul=BM4, d=0.5)


# =====================================================================================================================
# La place de Trébrume : une placette pavée par temps gris. Une mairie minuscule à volets bleus et drapeau mouillé (la
# clé), un panneau d'affichage, une fontaine, un banc, des goélands sur le toit.
# =====================================================================================================================
@decor("phare-eteint", "place-mairie", soleil=(40.0, -10.0), tons=AUBE, nom="La place de Trébrume", matiere=True)
def place_mairie(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=60.0, haut=0.2, halo=0.1, disque=0)
    tab.plan("nuages", 0.08)
    pg.voiles(P, y=-6.0, epais=12.0, seuil=0.5, graine=590)
    pg.voiles(P, y=16.0, epais=9.0, seuil=0.54, graine=591)
    tab.plan("lointains", 0.2)
    # ---- Derrière : les toits d'ardoise du bourg, des cheminées qui fument, et le phare, tout petit, entre deux pignons.
    phare(P, 172.0, 34.0, 22.0, T.CIEL[4], T.CIEL[6], rocher=False)
    for i, (x, w, top) in enumerate(((-4, 26, 22), (20, 20, 30), (150, 22, 36), (176, 24, 28), (134, 18, 40))):
        P.rect(x, top, w, 62 - top, T.CIEL[5] if i % 2 else T.CIEL[4])
        P.poly([(x - 1.5, top), (x + w + 1.5, top), (x + w / 2, top - 10)], T.CIEL[3])
        P.rect(x + w * 0.2, top - 9, 2.4, 6.0, T.CIEL[3])
        pg.fumee(P, x + w * 0.2 + 1.2, top - 9.4, (p + 0.2 * i) % 1.0)
        for j in range(2):
            P.rect(x + 4 + j * (w - 11), top + 6, 3.0, 4.0, LU4 if (i + j) % 3 == 0 else T.CIEL[2])
    brume(P, 44.0, 6.0, 31, T.CIEL[9], 0.5)
    tab.plan("moyen", 0.5)
    # ---- La mairie : minuscule, crépi clair, toit d'ardoise, volets bleus, un perron de trois marches, son drapeau mouillé.
    mx, mw, mtop, mbas = 96.0, 62.0, 22.0, 62.0
    faç = (np.abs(X - mx) < mw / 2) & (Y > mtop) & (Y < mbas)
    P.rampe(faç, 0.6 - 0.006 * (X - mx) + 0.2 * (pg.fbm(X / 8.0, Y / 6.0, 3, 592) - 0.5), [BM2, BM4, CREME], 0.6)
    P.remplir(faç & (Y > mbas - 5), GR3)
    toit = P.poly([(mx - mw / 2 - 3, mtop), (mx + mw / 2 + 3, mtop), (mx + mw / 2 - 8, mtop - 13), (mx - mw / 2 + 8, mtop - 13)], VI1)
    P.remplir(toit & (((Y - mtop) % 2.4) < 0.4), ENCRE)
    P.remplir(toit & ((((X + np.floor((Y - mtop) / 2.4) * 1.5) % 3.0)) < 0.3), VI2)
    P.remplir(P.crete(toit), BM2)
    P.poly([(mx - 9, mtop - 2), (mx + 9, mtop - 2), (mx, mtop - 13)], CREME)                   # le fronton
    P.ell(mx, mtop - 6.4, 3.0, 3.0, VOLET)
    P.ell(mx, mtop - 6.4, 2.2, 2.2, BM4)
    P.trait(mx, mtop - 6.4, mx + 1.2, mtop - 7.6, ENCRE)                                      # l'horloge de la mairie
    P.trait(mx, mtop - 6.4, mx - 0.4, mtop - 4.6, ENCRE)
    P.rect(mx - 1.6, mtop - 21.0, 3.2, 8.0, VI1)                                              # le clocheton
    P.poly([(mx - 2.6, mtop - 21.0), (mx + 2.6, mtop - 21.0), (mx, mtop - 26.0)], VI1)
    P.rect(mx - 0.8, mtop - 19.6, 1.6, 3.0, LAITON if int(p * 8) % 8 else LAITON2)
    for i, dx in enumerate((-22.0, -8.0, 8.0, 22.0)):                                         # les fenêtres et leurs volets bleus
        for j, y in enumerate((mtop + 5.0,) if abs(dx) < 10 else (mtop + 5.0, mtop + 22.0)):
            wx_ = mx + dx
            P.rect(wx_ - 3.0, y, 6.0, 9.0, NU2)
            P.rect(wx_ - 3.0, y, 6.0, 9.0, LU4) if (i + j) % 3 == 1 else None
            P.rect(wx_ - 0.3, y, 0.6, 9.0, CREME)
            P.rect(wx_ - 3.0, y + 4.2, 6.0, 0.6, CREME)
            for cote in (-1, 1):
                vx = wx_ - 6.6 if cote < 0 else wx_ + 3.4
                P.rect(vx, y - 0.4, 3.2, 9.8, VOLET)
                P.rect(vx, y - 0.4, 0.6, 9.8, VOLET2)
                for q in range(4):
                    P.rect(vx + 0.8, y + 0.6 + q * 2.2, 1.8, 0.4, NU2)
    P.ell(mx, mtop + 26.0, 5.0, 5.0, GR3, cond=Y < mtop + 26.5)                               # la porte
    P.rect(mx - 5.0, mtop + 26.0, 10.0, 14.0, GR3)
    P.ell(mx, mtop + 26.6, 4.0, 4.0, VOLET, cond=Y < mtop + 27)
    P.rect(mx - 4.0, mtop + 26.6, 8.0, 13.4, VOLET)
    P.rect(mx - 0.2, mtop + 23.0, 0.4, 17.0, NU2)
    P.point(mx + 1.6, mtop + 33.0, LAITON2)
    for j in range(3):
        P.rect(mx - 9 - j * 2.0, mbas - 3.0 + j * 1.6, 18 + j * 4.0, 1.6, GR4 if j % 2 == 0 else GR3)
    P.trait(mx + 12.0, mtop + 21.0, mx + 20.0, mtop + 12.0, GR1, P.ep(0.6))                    # la hampe
    v = 0.5 * onde(p)
    P.poly([(mx + 20.0, mtop + 12.0), (mx + 23.0, mtop + 13.0 + v), (mx + 22.0, mtop + 24.0 + v), (mx + 18.4, mtop + 22.0)], VOLET)
    P.poly([(mx + 21.2, mtop + 12.6 + v * 0.5), (mx + 23.0, mtop + 13.0 + v), (mx + 22.0, mtop + 24.0 + v), (mx + 20.6, mtop + 23.2 + v * 0.5)], LU2)
    P.poly([(mx + 19.6, mtop + 12.2), (mx + 21.2, mtop + 12.6 + v * 0.5), (mx + 20.6, mtop + 23.2 + v * 0.5), (mx + 19.4, mtop + 22.6)], CREME)
    if int(p * 8) % 3 == 0:
        P.point(mx + 21.0, mtop + 26.0 + 2 * (p * 8 % 1), BM2)                                 # il goutte
    for i, dx in enumerate((-20.0, -6.0, 14.0)):
        goeland(P, mx + dx, mtop - 12.6 + abs(dx) * 0.0, sens=1 if i % 2 else -1)
    # ---- La place : des pavés mouillés qui fuient, la fontaine au milieu à gauche, le banc, le panneau d'affichage.
    sol = Y > 60.0
    dallage(P, sol, 96.0, 44.0, GR3, GR2, larg=3.0, prof=2.0, joint=GR1)
    voile(P, sol, BM2, 0.22)
    voile(P, sol & (pg.fbm(X / 14.0, (Y - 60) / 2.0, 3, 593) > 0.6), BM3, 0.5)                 # des flaques
    fx_, fy_ = 152.0, 66.0                                      # la fontaine
    P.ell(fx_, fy_, 13.0, 3.4, GR2)
    P.ell(fx_, fy_ - 2.0, 13.0, 3.4, GR3)
    P.ell(fx_, fy_ - 2.0, 11.0, 2.6, ME2)
    P.ell(fx_ - 2, fy_ - 2.4, 6.0, 1.2, NU4)
    P.rect(fx_ - 1.6, fy_ - 16.0, 3.2, 14.0, GR3)
    P.rect(fx_ - 1.6, fy_ - 16.0, 1.0, 14.0, GR4)
    P.ell(fx_, fy_ - 16.0, 4.0, 1.4, GR4)
    P.ell(fx_, fy_ - 18.0, 2.0, 2.0, GR3)
    for cote in (-1, 1):
        for k in range(6):
            t = (p * 2 + k / 6.0) % 1.0
            P.point(fx_ + cote * (2.0 + 4.6 * t), fy_ - 15.0 + 12.0 * t * t, BM4 if k % 2 else BM3)
    for k in range(2):
        t = (p + k / 2.0) % 1.0
        P.ell(fx_ - 6 + 12 * k, fy_ - 2.0, 1.0 + 2.6 * t, 0.3 + 0.6 * t, BM3) if t < 0.6 else None
    bx0 = 20.0                                                  # le panneau d'affichage : des avis, un seul tout neuf
    P.rect(bx0, 40.0, 26.0, 18.0, BO2)
    P.rect(bx0, 40.0, 26.0, 1.0, BO4)
    P.poly([(bx0 - 2, 40.0), (bx0 + 28, 40.0), (bx0 + 13, 34.0)], VI1)
    for x in (bx0 + 2, bx0 + 22):
        P.rect(x, 58.0, 2.0, 8.0, BO1)
    for i, (dx, dy, w, h, c0) in enumerate(((2, 3, 7, 9, CREME), (10, 2, 6, 7, BM4), (17, 4, 7, 10, T.CIEL[11]), (10, 10, 6, 6, CIRE2))):
        P.rect(bx0 + dx, 40.0 + dy, w, h, c0)
        for q in range(3):
            P.rect(bx0 + dx + 1, 41.4 + dy + q * 1.8, w - 2 - q, 0.4, GR3)
        P.point(bx0 + dx + w / 2, 40.4 + dy, LU2)
    P.poly([(bx0 + 17, 54.0), (bx0 + 24, 54.0), (bx0 + 24 + 0.6 * onde(p), 57.0), (bx0 + 17.4, 56.0)], T.CIEL[11])
    bcx = 56.0                                                  # le banc
    P.rect(bcx - 9, 62.0, 18.0, 1.4, BO3)
    P.rect(bcx - 9, 57.0, 18.0, 1.2, BO3)
    P.rect(bcx - 9, 59.4, 18.0, 1.0, BO2)
    for x in (bcx - 8, bcx + 6.6):
        P.rect(x, 56.0, 1.2, 10.0, GR1)
    P.ell(bcx, 66.4, 10.0, 0.8, GR1)
    P.trait(128.0, 30.0, 128.0, 64.0, ENCRE, P.ep(0.9))           # le réverbère
    P.rect(125.6, 26.0, 4.8, 5.0, GR1)
    P.rect(126.2, 26.8, 3.6, 3.4, LU4 if int(p * 8) % 6 else LU3)
    halo(P, 128.0, 29.0, 7.0, LU3, 0.35)
    tab.plan("premier", 1.0)
    # ---- Premier plan : une borne de granit et sa chaîne, à gauche ; un bac à fleurs (des bruyères), à droite.
    for x in (6.0, 186.0):
        P.rect(x - 2.6, 62.0, 5.2, 18.0, ENCRE)
        P.ell(x, 62.0, 2.6, 1.6, GR1)
        P.rect(x - 2.6, 62.0, 1.0, 18.0, GR2)
    for i in range(22):
        t = i / 21.0
        P.ell(8 + t * 26, 66 + 9 * math.sin(math.pi * t) * 0.6 + 0.2 * onde(p, t), 0.8, 0.6, GR2 if i % 2 else ENCRE)
    P.rect(160.0, 72.0, 22.0, 8.0, BO1)
    P.rect(160.0, 72.0, 22.0, 1.0, BO3)
    for i in range(12):
        x = 161.5 + i * 1.7
        h = 3 + 3 * hz(i, 1, 594)
        P.trait(x, 72.0, x + 0.3 * onde(p, 0.1 * i), 72.0 - h, T.S1)
        P.point(x + 0.3 * onde(p, 0.1 * i), 72.0 - h, T.VIOLET if i % 2 else VI2, 2)
    voile(P, Y > 78.0, ENCRE, 0.35)
    brume(P, 56.0, 3.0, 32, T.CIEL[10], 0.3)
    # ---- Seconde passe : la vie de la place.
    chat(P, 56.0, 61.0, coul=GR2)                                 # sur le banc
    pg.souris(P, 118.0, 77.0, sens=1, coul=GR3)
    pg.goutte(P, 100.0, 13.0, 60.0, coul=BM2, d=0.4)              # la gouttière de la mairie
    pg.papillon_de_nuit(P, 128.0, 28.0, 4.0, coul=BLANC)
    for i in range(3):                                          # des feuilles mortes que le vent promène
        t = (p + i / 3.0) % 1.0
        P.rect(30 + 40 * i + 14 * t, 70.0 + 3 * math.sin(t * 6.283 + i), 1.4, 0.8, LU2 if i % 2 else GO2)
    P.rect(72.0, 54.0, 5.0, 8.0, VOLET)                           # la boîte aux lettres : la lettre de Pilou est partie d'une pareille
    P.rect(72.0, 54.0, 5.0, 1.2, VOLET2)
    P.rect(73.0, 56.4, 3.0, 0.6, ENCRE)
    P.rect(74.0, 62.0, 1.0, 4.0, GR1)
    P.trait(160.0, 72.0, 160.0, 62.0, GR1)                        # un vélo contre le bac à fleurs ? un parapluie oublié, ouvert, qui roule
    par = 1.0 * onde(p)
    P.ell(146.0 + par, 74.0, 4.0, 2.0, NU2, cond=Y < 74.6)
    P.trait(146.0 + par, 74.0, 147.0 + par, 78.0, GR1)


def chat(P, x, y, coul=None, sens=1):
    """Un chat endormi en boule : il respire, sa queue bat de temps en temps, une oreille frémit."""
    coul = GR2 if coul is None else coul
    s = 0.3 * onde(P.p)
    P.ell(x, y - 2.0 - s * 0.5, 4.6, 2.4 + s * 0.5, coul)
    P.ell(x + sens * 3.4, y - 2.2, 2.0, 1.8, coul)
    P.poly([(x + sens * 2.6, y - 3.6), (x + sens * 3.0, y - 5.2 - (0.4 if int(P.p * 8) % 6 == 0 else 0)), (x + sens * 3.8, y - 3.8)], coul)
    P.poly([(x + sens * 4.0, y - 3.6), (x + sens * 4.8, y - 5.0), (x + sens * 5.0, y - 3.4)], coul)
    P.trait(x + sens * 3.0, y - 2.2, x + sens * 4.2, y - 2.2, ENCRE)
    P.courbe([(x - sens * 4.0, y - 1.0), (x - sens * 6.0, y - 0.4), (x - sens * 7.0, y - 1.6 - 1.0 * max(0.0, onde(P.p, 0.3)))], coul, P.ep(0.7))
    P.ell(x - sens * 1.0, y - 3.4, 2.0, 0.8, BM1)


def ombre_portee(P, masque, force=0.5):
    """L'ombre d'un objet, portée par la lanterne : un ton plus sombre, posé en matière."""
    voile(P, masque & (P.a >= 0), ENCRE, force)


def bidon(P, x, y, k=1.0, coul=None):
    """Un bidon d'huile : (x, y) le milieu de son pied."""
    c0, c1 = coul or (LU1, LU2)
    P.rect(x - 2.4 * k, y - 6.0 * k, 4.8 * k, 6.0 * k, c0)
    P.rect(x - 2.4 * k, y - 6.0 * k, 1.2 * k, 6.0 * k, c1)
    P.rect(x - 2.4 * k, y - 3.4 * k, 4.8 * k, 0.5 * k, ENCRE)
    P.rect(x - 0.8 * k, y - 7.2 * k, 1.6 * k, 1.2 * k, GR3)
    P.courbe([(x + 0.8 * k, y - 6.6 * k), (x + 2.2 * k, y - 7.6 * k), (x + 2.4 * k, y - 5.6 * k)], GR3, 1)


def pendule(P, x, y, r, d=0.0, coul=None, heure=0.0, balancier=0.0):
    """Une pendule ronde : boîtier, cadran, deux aiguilles à son heure à elle ; balancier : sa longueur (0 : aucun)."""
    c0 = coul or BO2
    if balancier:
        a = 0.3 * onde(P.p, d)
        bx_, by_ = x + balancier * math.sin(a), y + r + balancier * math.cos(a)
        P.trait(x, y + r, bx_, by_, LAITON)
        P.ell(bx_, by_, max(0.8, r * 0.3), max(0.8, r * 0.3), LAITON2)
    P.ell(x, y, r + 1.0, r + 1.0, c0)
    P.ell(x, y, r, r, CREME)
    for k in range(12):
        if r > 2.4:
            P.point(x + (r - 0.8) * math.cos(k * math.pi / 6), y + (r - 0.8) * math.sin(k * math.pi / 6), GR2)
    h = heure * 2 * math.pi
    P.trait(x, y, x + r * 0.5 * math.sin(h), y - r * 0.5 * math.cos(h), ENCRE)
    m = (heure * 12 + int(P.p * 8) / 60.0 * (1 if d < 0.5 else 0)) * 2 * math.pi
    P.trait(x, y, x + r * 0.8 * math.sin(m), y - r * 0.8 * math.cos(m), ENCRE)
    P.point(x, y, LAITON)


# =====================================================================================================================
# L'atelier de Basile : une boutique d'horloger encombrée. Des dizaines de pendules qui n'indiquent pas la même heure,
# un établi avec loupe et limes, de la poussière dorée de laiton, une forme sous un drap.
# =====================================================================================================================
@decor("phare-eteint", "atelier-basile", soleil=(150.0, -10.0), tons=PHARE, nom="L'atelier de Basile", matiere=True)
def atelier_basile(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    P.rampe(np.ones(X.shape, dtype=bool), 0.5 + 0.003 * (X - 60) - 0.003 * (Y + 16) + 0.2 * (pg.fbm(X / 14.0, Y / 10.0, 3, 600) - 0.5),
            [BO1, BO2, BO3, LU1], 0.8)
    P.remplir((np.abs((X % 12.0) - 6.0) < 0.3), BO1)
    tab.plan("lointains", 0.2)
    # ---- Le mur de pendules : rondes, carrées, à coucou, à balancier ; aucune n'est d'accord avec sa voisine.
    k = 0
    for j, y in enumerate((-8.0, 8.0, 24.0, 40.0)):
        x = 6.0 + (j % 2) * 5
        while x < 132:
            r = 2.4 + 2.6 * hz(k, 1, 601)
            sorte = int(hz(k, 2, 601) * 4)
            c0 = (BO1, BO3, VI1, LAITON, GR2, VOLET)[int(hz(k, 3, 601) * 6)]
            if sorte == 0:                                      # un coucou : toit pointu, poids en pommes de pin
                P.poly([(x - r - 2, y - r), (x + r + 2, y - r), (x, y - r - 4.4)], BO1)
                P.rect(x - r - 1, y - r, 2 * r + 2, 2 * r + 2, BO2)
                pendule(P, x, y + 0.6, r * 0.7, d=hz(k, 4, 601), coul=BO1, heure=hz(k, 5, 601), balancier=r + 3)
            elif sorte == 1:                                    # une pendule carrée
                P.rect(x - r - 1.2, y - r - 1.2, 2 * r + 2.4, 2 * r + 2.4, c0)
                pendule(P, x, y, r * 0.86, d=hz(k, 4, 601), coul=c0, heure=hz(k, 5, 601))
            else:
                pendule(P, x, y, r, d=hz(k, 4, 601), coul=c0, heure=hz(k, 5, 601), balancier=(r + 2) if sorte == 3 else 0.0)
            x += 2 * r + 5.0 + 3 * hz(k, 6, 601)
            k += 1
    voile(P, (X < 40) & (Y < 60), BO1, np.clip(0.5 - X / 80.0, 0, 0.5))
    tab.plan("moyen", 0.5)
    # ---- La vitrine sur la rue, à droite : le jour gris de Trébrume, des montres pendues à des fils, l'enseigne à l'envers.
    wx, wy, ww, wh = 140.0, -8.0, 46.0, 52.0
    P.rect(wx - 2.5, wy - 2.5, ww + 5, wh + 5, BO1)
    fen = (X > wx) & (X < wx + ww) & (Y > wy) & (Y < wy + wh)
    P.rampe(fen, 0.5 + 0.3 * (pg.fbm(X / 12.0, Y / 6.0, 3, 602) - 0.5) - 0.006 * (Y - wy), [NU4, BM1, BM2, BM3, BM4], 0.8)
    P.remplir(fen & (Y > wy + 34) & (np.abs(((X - wx) % 15.0) - 7.5) < 5.4), BM1)               # les maisons d'en face
    P.remplir(fen & (Y > wy + 46), GR3)
    for i in range(1, 3):
        P.rect(wx + i * ww / 3 - 0.6, wy, 1.2, wh, BO1)
    P.rect(wx, wy + wh * 0.3, ww, 1.2, BO1)
    for i in range(6):                                          # les montres de la vitrine, au bout de leurs fils
        x = wx + 5 + i * 7.2
        l = 16 + 10 * hz(i, 1, 603)
        bal = 0.5 * onde(p, 0.17 * i)
        P.trait(x, wy, x + bal, wy + l, LAITON)
        P.ell(x + bal, wy + l + 1.8, 1.8, 1.8, LAITON2)
        P.ell(x + bal, wy + l + 1.8, 1.1, 1.1, CREME)
    P.rect(wx - 4, wy + wh + 2.5, ww + 8, 2.0, BO3)
    rai(P, wx + 16, wy + 6, 78.0, 30.0, -0.9, LAITON2, 0.34, 46, 604)
    # ---- La grande horloge démontée, et la forme sous le drap : elle a presque la taille d'une lanterne de phare.
    dx_, dy_ = 104.0, 62.0
    drap = [(dx_ - 16, dy_ + 2), (dx_ - 12, dy_ - 22), (dx_ - 4, dy_ - 34), (dx_ + 6, dy_ - 33), (dx_ + 13, dy_ - 20), (dx_ + 17, dy_ + 2)]
    md = P.poly(drap, CREME)
    P.rampe(md, 0.6 + 0.02 * (X - dx_) + 0.35 * np.sin((X - dx_) * 0.7 + (Y - dy_) * 0.08) * 0.5 + 0.1 * (pg.fbm(X / 3.0, Y / 9.0, 2, 605) - 0.5),
            [BM2, BM4, CREME, BLANC], 0.6)
    for i in range(5):
        P.courbe([(dx_ - 10 + i * 5.4, dy_ - 26 + abs(i - 2) * 4), (dx_ - 12 + i * 6.4 + 0.3 * onde(p, 0.1 * i), dy_ - 8), (dx_ - 13 + i * 7.0, dy_ + 2)], BM2, 1)
    P.ell(dx_ + 1, dy_ + 2.4, 18.0, 1.6, BO1)
    # ---- Le plancher et l'établi : étau, loupe sur pied, limes, rouages en vrac, une montre ouverte sous la lampe.
    sol = Y > 62.0
    dallage(P, sol, 150.0, 44.0, BO3, BO2, larg=3.6, prof=0.0, joint=BO1)
    voile(P, sol & (np.abs(X - (wx + 16 - (Y - 0) * 0.9)) < 18), LAITON2, 0.3)
    ex0, ex1, ey = 22.0, 84.0, 58.0
    P.rect(ex0, ey, ex1 - ex0, 3.0, BO3)
    P.rect(ex0, ey, ex1 - ex0, 0.7, BO4)
    P.rect(ex0 + 2, ey + 3.0, ex1 - ex0 - 4, 8.0, BO2)
    for i in range(4):
        P.rect(ex0 + 4 + i * 14.6, ey + 4.2, 12.6, 5.6, BO1)
        P.rect(ex0 + 9.4 + i * 14.6, ey + 6.4, 2.0, 0.8, LAITON)
    for x in (ex0 + 3, ex1 - 5):
        P.rect(x, ey + 11.0, 2.4, 9.0, BO1)
    lx, ly = 70.0, ey                                           # la lampe d'établi
    halo(P, lx - 10, ly - 3, 22.0, LU4, 0.5, ry=10)
    P.courbe([(lx + 4, ly), (lx + 4, ly - 12), (lx - 4, ly - 16)], GR1, P.ep(0.7))
    P.poly([(lx - 10, ly - 14.0), (lx - 2, ly - 18.0), (lx - 1, ly - 15.0), (lx - 8, ly - 11.0)], LAITON)
    P.ell(lx - 6.4, ly - 12.4, 1.6, 1.0, LU5)
    P.ell(52.0, ey - 0.6, 3.4, 1.0, LAITON)                      # la montre ouverte
    P.ell(52.0, ey - 0.8, 2.6, 0.7, CREME)
    P.ell(47.0, ey - 0.4, 2.6, 0.8, LAITON2)
    for i in range(7):
        P.ell(58 + i * 2.6 + (i % 2), ey - 0.5, 0.9, 0.5, LAITON2 if i % 2 else LAITON)       # des rouages en vrac
    for i in range(4):
        P.trait(30 + i * 2.6, ey - 0.4, 33 + i * 2.6, ey - 5.0, GR3 if i % 2 else GR4)         # les limes dans leur pot
    P.rect(29.0, ey - 3.0, 12.0, 3.0, VOLET)
    P.trait(40.0, ey, 40.0, ey - 9.0, GR1)                        # la loupe sur pied
    P.ell(43.0, ey - 10.0, 3.4, 3.4, LAITON)
    P.ell(43.0, ey - 10.0, 2.6, 2.6, BM3)
    P.point(42.2, ey - 11.0, BLANC)
    P.rect(24.0, ey - 5.0, 5.0, 5.0, GR2)                         # l'étau
    P.rect(24.0, ey - 5.0, 5.0, 1.0, GR4)
    P.rect(18.0, 64.0, 9.0, 1.4, BO3)                            # le tabouret
    for x in (19.0, 25.0):
        P.rect(x, 65.4, 1.0, 12.0, BO1)
    tab.plan("premier", 1.0)
    # ---- Premier plan : une comtoise à gauche (son balancier bat), une cloche de verre sur un guéridon, à droite.
    P.rect(-6.0, -16.0, 13.0, 96.0, ENCRE)
    P.rect(5.6, -16.0, 1.4, 96.0, BO2)
    pendule(P, 0.0, 6.0, 5.0, coul=BO1, heure=0.62)
    a = 0.22 * onde(p)
    P.trait(0.5, 16.0, 0.5 + 34 * math.sin(a), 16.0 + 34 * math.cos(a), LAITON)
    P.ell(0.5 + 34 * math.sin(a), 16.0 + 34 * math.cos(a), 3.0, 3.0, LAITON2)
    P.ell(182.0, 64.0, 12.0, 2.4, BO1)
    P.rect(181.0, 66.0, 2.0, 14.0, BO1)
    cloche = ((X - 182.0) / 7.0) ** 2 + ((Y - 56.0) / 9.0) ** 2 <= 1
    voile(P, cloche & (Y < 63.0), BM3, 0.35)
    P.remplir(cloche & (Y < 63.0) & (np.abs(((X - 182.0) / 7.0) ** 2 + ((Y - 56.0) / 9.0) ** 2 - 0.9) < 0.1), BM4)
    pendule(P, 182.0, 57.0, 3.0, coul=LAITON, heure=0.3)
    voile(P, Y > 77.6, ENCRE, 0.3)
    poussiere(P, 30, -8, 170, 64, 40, LAITON2, 606)
    # ---- Seconde passe : la vie de l'atelier.
    chat(P, 134.0, 64.0, coul=BO2)                                # le chat de Basile, dans le rai de soleil
    pg.souris(P, 60.0, 77.0, sens=1, coul=GR3)
    pg.araignee(P, 138.0, -8.0, 8.0, d=0.4)
    t = (p * 1.0) % 1.0                                         # un coucou sort, salue, rentre
    if t < 0.3:
        P.rect(92.0, 20.0, 3.0, 1.6, CREME)
        P.point(95.0, 20.4, LU2)
    for i in range(4):                                          # des copeaux de laiton qui tombent de l'établi
        u = (p + i / 4.0) % 1.0
        P.point(50 + 6 * i, 61.0 + 14 * u * u, LAITON2)
    ombre_portee(P, (np.hypot((X - 106.0) / 20.0, (Y - 65.0) / 1.8) < 1.0), 0.45)
    pg.vapeur(P, 36.0, 55.0, coul=BM3, h=8.0)                     # la tasse de Basile
    P.rect(34.6, 55.0, 3.0, 2.6, VOLET2)
    v = onde(p)                                                 # le drap respire : il y a de l'air là-dessous
    P.courbe([(92.0, 62.0 + 0.4 * v), (104.0, 63.6), (118.0, 62.0 - 0.4 * v)], BM4, 1)


# =====================================================================================================================
# Le sentier des douaniers : un sentier étroit en haut d'une falaise, dans le brouillard. Ajoncs, bord incertain, une
# cabane de guet en planches grises avec une petite fenêtre tournée vers le phare. Le sol : y = 64, de x = 4 à 130.
# =====================================================================================================================
@decor("phare-eteint", "sentier-douaniers", soleil=(170.0, 0.0), tons=AUBE, nom="Le sentier des douaniers", matiere=True)
def sentier_douaniers(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=70.0, haut=0.16, halo=0.12, disque=0)
    tab.plan("nuages", 0.08)
    pg.voiles(P, y=-4.0, epais=12.0, seuil=0.5, graine=610)
    pg.voiles(P, y=24.0, epais=10.0, seuil=0.53, graine=611)
    tab.plan("lointains", 0.2)
    # ---- Le vide, à droite : la mer très bas, la Dent-Creuse et son phare dans le brouillard ; des oiseaux de mer.
    mer = (Y > 58.0)
    P.rampe(mer, 0.5 + 0.3 * (pg.fbm((X + 2 * onde(p)) / 16.0, Y / 1.4, 3, 612) - 0.5) - 0.01 * (Y - 58), [NU2, NU3, NU4, BM1, BM2], 0.8)
    phare(P, 168.0, 58.0, 30.0, T.CIEL[2], T.CIEL[4])
    for i in range(6):                                          # l'écume au pied du rocher
        t = (p + i / 6.0) % 1.0
        P.trait(156 + i * 4.4, 62.0 + (i % 2) * 1.4, 159 + i * 4.4 + 2 * t, 62.0 + (i % 2) * 1.4, BM4 if t < 0.5 else BM2)
    for i in range(5):
        goeland(P, 140 + 9 * i + 3 * onde(p, 0.2 * i), 26 + 14 * hz(i, 1, 613) + onde(p, 0.3 * i), pose=False)
    for g, (y, ep) in enumerate(((54.0, 6.0), (40.0, 6.0), (66.0, 4.0), (20.0, 5.0))):
        brume(P, y, ep, 40 + g, T.CIEL[9] if g % 2 == 0 else T.CIEL[8], 0.6)
    tab.plan("moyen", 0.5)
    # ---- La falaise : la lande qui monte à gauche, le bord déchiqueté, la paroi qui tombe dans le brouillard.
    f_haut = lambda x: 62.0 - 14.0 * np.exp(-((_a(x) - 10) / 46.0) ** 2) + 1.4 * np.sin(_a(x) / 9.0) + 0.6 * np.sin(_a(x) / 3.0)
    bord = lambda y: 136.0 + 5.0 * np.sin(_a(y) / 5.0) + 2.4 * np.sin(_a(y) / 1.7) - (_a(y) - 62) * 0.5
    lande = (Y > f_haut(X)) & (X < bord(Y))
    P.rampe(lande, 0.6 + 0.3 * (pg.fbm(X / 8.0, Y / 2.4, 3, 614) - 0.5) - 0.02 * (Y - f_haut(X)), [T.S0, T.S1, T.S2, T.S3], 0.75)
    paroi = lande & (Y > 66.0 + 2.0 * np.sin(X / 6.0)) & (X > 96 - (Y - 66) * 1.5)
    P.rampe(paroi, 0.55 - 0.012 * (Y - 66) + 0.4 * (pg.fbm(X / 2.4, Y / 8.0, 3, 615) - 0.5), [ENCRE, GR1, GR2, GR3, GR4], 0.8)
    voile(P, paroi, T.CIEL[8], np.clip((Y - 70) / 24.0, 0, 0.8))
    P.remplir(P.crete(lande) & (pg.fbm(X / 5.0, Y * 0, 2, 616) > 0.5), CIRE)
    # Le sentier : une trace claire, étroite, qui longe le bord ; des piquets et un fil, par endroits rompu.
    for i in range(60):
        u = i / 59.0
        x = 2 + 130 * u
        y = 64.6 + 1.2 * math.sin(u * 9)
        P.ell(x, y, 2.6, 0.7, BM2 if i % 2 else GO2)
    for i in range(9):
        x = 104 + i * 3.6
        y = 62.0 + 0.8 * math.sin(i)
        if i in (4, 5):
            P.trait(x, y, x + 1.6, y + 1.0, BO2)                 # un piquet couché : le bord a cédé là
            continue
        P.trait(x, y, x + 0.2, y - 5.0, BO1, P.ep(0.5))
        if i not in (3, 8):
            P.trait(x + 0.2, y - 4.0, x + 3.8, y - 4.0 + 0.4 * onde(p, 0.1 * i), GO2)
    # La cabane de guet : planches grises, toit de tôle, sa petite fenêtre tournée vers le phare ; un fanal à sa porte.
    cx_, cy_ = 62.0, float(f_haut(62.0)) + 1.0
    P.rect(cx_ - 13, cy_ - 20, 26, 20, GR3)
    P.rampe((np.abs(X - cx_) < 13) & (Y > cy_ - 20) & (Y < cy_), 0.5 + 0.02 * (X - cx_) + 0.3 * (pg.fbm(X / 1.3, Y / 14.0, 2, 617) - 0.5), [GR1, GR2, GR3, GR4], 0.6)
    for i in range(-5, 6):
        P.rect(cx_ + i * 2.4 - 0.2, cy_ - 20, 0.4, 20, GR1)
    P.poly([(cx_ - 16, cy_ - 20), (cx_ + 15, cy_ - 23), (cx_ + 16, cy_ - 20.6), (cx_ - 15, cy_ - 17.6)], NU1)
    P.trait(cx_ - 16, cy_ - 20, cx_ + 15, cy_ - 23, BM2)
    P.rect(cx_ + 3, cy_ - 15, 7, 6, ENCRE)                        # la fenêtre
    P.rect(cx_ + 3.6, cy_ - 14.4, 5.8, 4.8, LU3 if int(p * 8) % 7 else LU4)
    halo(P, cx_ + 6.5, cy_ - 12.0, 9.0, LU3, 0.35)
    P.rect(cx_ + 6.2, cy_ - 15, 0.6, 6, ENCRE)
    P.rect(cx_ - 10, cy_ - 13, 7, 13, BO1)                        # la porte
    P.point(cx_ - 4.4, cy_ - 6.6, LAITON2)
    P.rect(cx_ + 9, cy_ - 27, 1.6, 5.0, GR1)                      # le tuyau du poêle
    pg.fumee(P, cx_ + 9.8, cy_ - 27.4, p)
    P.trait(cx_ - 14.6, cy_ - 16.0, cx_ - 18.0, cy_ - 16.0, ENCRE)
    fanal(P, cx_ - 18.0, cy_ - 10.0 + 0.3 * onde(p), 0.9, lueur=9.0)
    P.trait(cx_ + 20.0, cy_ + 1.0, cx_ + 20.0, cy_ - 11.0, BO1, P.ep(0.6))                  # une longue-vue sur son pied
    P.poly([(cx_ + 17.0, cy_ - 11.0), (cx_ + 26.0, cy_ - 13.6), (cx_ + 26.4, cy_ - 12.4), (cx_ + 17.4, cy_ - 9.8)], LAITON)
    # Les ajoncs : des buissons sombres piqués de fleurs jaunes, que le vent peigne ; la bruyère, violette.
    for i in range(16):
        x = -4 + 9.4 * i + 4 * hz(i, 1, 618)
        if x > float(bord(64.0)) - 6 or abs(x - cx_) < 22:
            continue
        y = float(f_haut(x)) + 1.0 + 3 * hz(i, 2, 618) - (5 if x < 30 else 0)
        r = 2.6 + 2.4 * hz(i, 3, 618)
        P.volumes([(x, y, r), (x + r * 0.8, y + r * 0.2, r * 0.7), (x - r * 0.8, y + r * 0.3, r * 0.6)], [T.S0, T.S1, T.S2, T.S3],
                  (0.5, -0.6, 0.3), grain=1.0, graine=619 + i, gain=0.6, base=0.4, trame=0.7)
        for q in range(int(4 + 5 * hz(i, 4, 618))):
            P.point(x + (hz(i, q + 5, 618) - 0.5) * r * 2.2 + 0.3 * onde(p, 0.1 * q), y - r * 0.2 + (hz(i, q + 15, 618) - 0.5) * r * 1.2, CIRE2 if q % 2 else CIRE)
    tab.plan("premier", 1.0)
    # ---- Premier plan : la lande en bas, un muret de pierres sèches, des graminées ; le brouillard qui passe devant.
    f_sol = lambda x: 72.0 + 1.4 * np.sin(_a(x) / 15.0) + 0.6 * np.sin(_a(x) / 4.4) + 10.0 * np.clip((_a(x) - 122) / 40.0, 0, 1) ** 1.5
    avant = (Y > f_sol(X)) & (X < 150.0 + (Y - 72) * 1.0)
    P.rampe(avant, 0.35 + 0.4 * (pg.fbm(X / 6.0, Y / 2.0, 3, 640) - 0.5) + 0.3 * np.exp(-(Y - f_sol(X)) / 1.4), [T.N0, T.N1, T.S0, T.S1, T.S2], 0.8)
    pg.touffes(P, f_sol, n=230, x0=-6, x1=148, haut=4.0, graine=641)
    for i in range(9):                                          # le muret
        x = -6 + i * 5.6
        P.ell(x + 2.6, 73.4 + (i % 2) * 0.8, 3.0, 1.9, GR2 if i % 2 else GR3)
        P.ell(x + 2.0, 72.8 + (i % 2) * 0.8, 1.8, 0.8, GR4)
        P.ell(x + 4.4, 76.6 - (i % 2) * 0.6, 3.0, 1.8, GR1 if i % 2 else GR2)
    for i in range(8):
        x = 60 + i * 9 + 4 * hz(i, 1, 642)
        pg.fleur(P, x, float(f_sol(x)) + 1.5, 2.0 + hz(i, 2, 642), T.VIOLET if i % 2 else CIRE2, CREME)
    brume(P, 74.0, 3.0, 46, T.CIEL[10], 0.35, x0=110)
    brume(P, 60.0, 3.0, 47, T.CIEL[10], 0.3, x0=120)
    # ---- Seconde passe : la vie de la lande.
    for i in range(3):                                          # des lapins dans la lande : l'un se dresse
        x = 12.0 + i * 16.0
        y = 52.0 + i * 3.0
        debout = (i == 1 and int(p * 8) % 8 < 3)
        P.ell(x, y - (1.0 if debout else 0), 1.6, 1.2 + (0.8 if debout else 0), GO2)
        P.trait(x + 0.6, y - 1.6 - (1.6 if debout else 0), x + 0.6, y - 3.4 - (1.6 if debout else 0), GO2)
        P.point(x - 1.4, y, BLANC)
    pg.papillon_de_nuit(P, 44.0, 44.0, 5.0, coul=BLANC)
    P.trait(88.0, 50.0, 88.0, 40.0, BO1)                          # une manche à air en haut d'un mât
    v = onde(p)
    P.poly([(88.0, 40.0), (96.0, 40.6 + 0.8 * v), (96.0, 42.6 + 0.8 * v), (88.0, 43.0)], LU2)
    P.poly([(91.0, 40.2 + 0.3 * v), (93.0, 40.4 + 0.5 * v), (93.0, 42.8 + 0.5 * v), (91.0, 42.9 + 0.3 * v)], CREME)
    for i in range(5):                                          # des cailloux roulent du bord, de loin en loin
        t = (p + i / 5.0) % 1.0
        if i == 2:
            P.point(126.0 + 3 * t, 66.0 + 12 * t * t, GR3)
    P.rect(40.0, 58.0, 6.0, 4.0, BO2)                             # un panier de pêche oublié près de la cabane, une gaffe
    P.trait(48.0, 62.0, 56.0, 46.0, BO3)
    pg.goutte(P, 66.0, 40.0, 60.0, coul=BM4, d=0.6)               # la tôle du toit goutte
    for i in range(6):                                          # la bruyère
        P.point(100.0 + i * 4.0, 68.0 + (i % 2) * 1.6, T.VIOLET, 2)


# =====================================================================================================================
# Le Souffleur : une grotte marine à marée basse. Sable mouillé, goémon, une barque à sec, des bidons alignés, une
# lanterne posée sur un rocher, un conduit sombre qui monte dans la pierre.
# =====================================================================================================================
@decor("phare-eteint", "grotte-souffleur", soleil=(52.0, 30.0), tons=PHARE, nom="Le Souffleur", matiere=True)
def grotte_souffleur(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    # ---- Par la gueule de la grotte, à gauche : la mer basse, grise, et le jour qui entre.
    pg.ciel(P, horizon=44.0, haut=0.5, halo=0.1, disque=0)
    P.rampe(Y > 42.0, 0.55 + 0.25 * (pg.fbm((X + 2 * onde(p)) / 12.0, Y / 1.3, 3, 650) - 0.5) - 0.012 * (Y - 42), [NU2, NU3, NU4, BM1, BM2, BM3], 0.8)
    tab.plan("lointains", 0.2)
    for i in range(6):
        t = (p + i / 6.0) % 1.0
        P.trait(20 + i * 9, 50.0 + i * 1.6, 28 + i * 9 + 3 * t, 50.0 + i * 1.6, BM4 if t < 0.5 else BM2)
    P.poly([(24.0, 44.0), (30.0, 34.0), (36.0, 44.0)], T.CIEL[3])                               # un écueil, dehors
    goeland(P, 30.0, 34.0, sens=1)
    brume(P, 40.0, 4.0, 50, T.CIEL[8], 0.5, x1=90)
    tab.plan("moyen", 0.5)
    # ---- La roche : une voûte sombre, feuilletée, luisante d'eau ; elle se referme autour de l'ouverture.
    gx, gy = 46.0, 36.0
    r = np.hypot((X - gx) / 1.25, Y - gy) + 9.0 * (pg.fbm(X / 14.0, Y / 9.0, 3, 651) - 0.5) + 5.0 * np.sin(np.arctan2(Y - gy, X - gx) * 4)
    roche = (r > 30.0) | (Y > 66.0 + 2.0 * np.sin(X / 13.0))
    v = 0.6 - (r - 30.0) / 110.0 + 0.5 * (pg.fbm(X / 5.0, (Y + X * 0.3) / 2.0, 3, 652) - 0.5) + 0.25 * np.exp(-((X - 150) / 24.0) ** 2 - ((Y - 52) / 16.0) ** 2)
    P.rampe(roche & (Y <= 66.0 + 2.0 * np.sin(X / 13.0)), v, [ENCRE, NU0, GR1, GR2, GR3], 0.85)
    P.remplir((np.abs(r - 30.0) < 0.9) & (Y < 62), BM2)          # le bord de la gueule, mouillé de jour
    for i in range(12):                                         # des gouttes qui tombent de la voûte
        t = (p + hz(i, 1, 653)) % 1.0
        x = 80 + 100 * hz(i, 2, 653)
        if t < 0.7:
            P.point(x, -4 + 12 * hz(i, 3, 653) + 60 * t * t, BM3)
    # Le conduit sombre, qui monte dans la pierre : un trou noir, une échelle de fer, un souffle qui en sort.
    cx_, cy_ = 150.0, 14.0
    P.ell(cx_, cy_ + 6, 10.0, 16.0, ENCRE)
    P.ell(cx_ + 1.0, cy_ + 8, 8.0, 13.0, NU0)
    P.ell(cx_ + 1.6, cy_ + 2, 5.0, 8.0, ENCRE)
    for j in range(9):
        P.rect(cx_ - 3.0, cy_ - 4 + j * 3.4, 6.0, 0.6, GR3)
    P.rect(cx_ - 3.4, cy_ - 6, 0.7, 34.0, GR2)
    P.rect(cx_ + 2.8, cy_ - 6, 0.7, 34.0, GR2)
    for k in range(6):                                          # le souffle : la poussière d'eau qu'il crache
        t = (p + k / 6.0) % 1.0
        voile(P, np.hypot(X - (cx_ + 3 * math.sin(t * 5 + k)), (Y - (cy_ + 24 + 14 * t)) * 0.8) < 2.0 + 5.0 * t, BM2, 0.5 - 0.45 * t)
    # ---- Le sable mouillé : il reflète l'ouverture ; rigoles, goémon, coquillages, traces de quille.
    sable = Y > 66.0 + 2.0 * np.sin(X / 13.0)
    P.rampe(sable, 0.35 + 0.3 * (pg.fbm(X / 10.0, Y / 1.6, 3, 654) - 0.5) + 0.45 * np.exp(-((X - 46) / 34.0) ** 2) - 0.012 * (Y - 66), [NU0, NU1, GR1, GO1, GO2, BM2], 0.8)
    voile(P, sable & (np.abs(X - 46 - (Y - 66) * 0.6) < 10 + (Y - 66) * 0.8), BM3, 0.3)
    for i in range(3):
        P.courbe([(60 + i * 3, 68.0 + i * 0.5), (84 + i * 3, 72.0 + i), (112 + i * 3, 71.0 + i * 0.6)], NU1, 1)   # les traces de quille
    for i in range(10):
        x = 60 + 13 * i + 5 * hz(i, 1, 655)
        if 108 < x < 134:
            continue
        for q in range(4):
            P.courbe([(x + q * 1.0, 74.0 + 2 * hz(i, 2, 655)), (x + q * 1.6 - 2, 72.0 + 2 * hz(i, 2, 655) - 1.2 * hz(i, q, 656))], GO1 if q % 2 else ENCRE, P.ep(0.5))
    barque_a_sec(P, 96.0, 70.0, 30.0, coul=(NU0, NU2, BM2))
    P.trait(88.0, 66.2, 108.0, 63.0, BO3, P.ep(0.5))             # ses avirons
    P.ell(108.6, 62.8, 1.8, 0.8, BO4)
    P.courbe([(110.0, 69.0), (118.0, 72.0), (126.0, 70.0), (132.0, 66.0)], GO2, 1)          # son amarre, jusqu'à l'anneau
    P.ell(133.0, 65.0, 1.4, 1.4, GR3)
    # Les bidons alignés contre la paroi, la lanterne posée sur un rocher : la seule chaleur de la grotte.
    for i in range(7):
        bidon(P, 142.0 + i * 5.6, 68.0 + (i % 2) * 0.6, 1.0, coul=(LU1, LU2) if i % 3 else (NU2, NU4))
    P.ell(136.0, 66.0, 6.0, 4.0, GR2, cond=Y < 68.0)
    P.ell(134.6, 65.0, 3.6, 2.0, GR3, cond=Y < 68.0)
    fanal(P, 136.0, 62.2, 1.3, lueur=22.0)
    voile(P, (np.hypot(X - 136, (Y - 70) * 2.6) < 30) & sable, LU3, 0.3)
    P.rect(176.0, 60.0, 14.0, 8.0, BO2)                          # une caisse, un filet jeté dessus
    P.rect(176.0, 60.0, 14.0, 1.0, BO4)
    P.remplir((X > 174) & (X < 192) & (Y > 57) & (Y < 64) & ((P.XI + P.YI) % 4 == 0), GO2)
    tab.plan("premier", 1.0)
    # ---- Premier plan : la roche noire qui encadre, des stalactites, une flaque où tremble la lanterne.
    haut = Y < -6.0 + 6.0 * pg.fbm(X / 7.0, X * 0, 3, 657) + 10.0 * np.abs(np.sin(X / 9.0)) ** 6
    P.remplir(haut, ENCRE)
    for (x0, cote) in ((198.0, -1),):
        m = P.poly([(x0, -16.0), (x0 + cote * 14, 10.0), (x0 + cote * 6, 40.0), (x0 + cote * 16, 80.0), (x0, 80.0)], ENCRE)
        P.remplir(m & (pg.fbm(X / 3.0, Y / 5.0, 2, 658) > 0.62), NU0)
    P.ell(120.0, 77.0, 14.0, 1.6, ME1)
    for j in range(4):
        if (j + int(p * 8)) % 3:
            P.trait(124.0 - j, 76.4 + j * 0.5, 130.0 + j, 76.4 + j * 0.5, LU2)
    voile(P, Y > 78.0, ENCRE, 0.4)
    poussiere(P, 100, 0, 190, 60, 14, BM3, 659)
    # ---- Seconde passe : la vie de la grotte.
    for i in range(3):
        t = (p + i / 3.0) % 1.0                                   # des crabes
        cx_ = 70.0 + 26 * i + 5 * (t if i % 2 else 1 - t)
        P.ell(cx_, 75.0 + i * 0.8, 1.5, 0.8, LU2)
        P.trait(cx_ - 1.5, 75.0 + i * 0.8, cx_ - 2.4, 74.2 + i * 0.8, LU2)
        P.trait(cx_ + 1.5, 75.0 + i * 0.8, cx_ + 2.4, 74.2 + i * 0.8, LU2)
    pg.yeux(P, 150.0, 6.0, coul=LU4, d=0.2, ecart=1.6)            # quelqu'un, en haut du conduit ?
    pg.papillon_de_nuit(P, 136.0, 58.0, 5.0, coul=BM4)
    pg.goutte(P, 120.0, -4.0, 77.0, coul=BM3, d=0.5, flaque=LU2)
    ombre_portee(P, (np.hypot((X - 160.0) / 22.0, (Y - 70.0) / 2.0) < 1.0), 0.4)                  # l'ombre des bidons
    for i in range(8):                                          # des anatifes sur la paroi, des moules
        P.ell(100.0 + i * 3.0, 20.0 + (i % 3) * 2.0, 0.9, 1.2, NU1)
    v = onde(p)                                                 # des algues qui pendent de la voûte et se balancent
    for i in range(7):
        x = 84.0 + i * 13.0
        P.courbe([(x, -6.0 + (i % 3) * 3), (x + 0.6 * v, 2.0 + (i % 3) * 3), (x + 1.2 * v, 8.0 + (i % 2) * 6)], GO1 if i % 2 else GO2, 1)


# =====================================================================================================================
# La cave du phare : le sous-sol rond, à la lueur d'une lanterne. Un tas de charbon, des rangées de bidons d'huile, un
# panier pendu à une poulie (la clé), un escalier de pierre en colimaçon qui monte dans le noir. Le sol : y = 76.
# =====================================================================================================================
@decor("phare-eteint", "cave-du-phare", soleil=(60.0, 40.0), tons=PHARE, nom="La cave du phare", matiere=True)
def cave_du_phare(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    lx_, ly_ = 60.0, 40.0                                       # la lanterne, pendue à son crochet
    tab.plan("ciel", 0.0)
    # ---- Le mur rond : de gros moellons, éclairés d'un seul côté ; l'humidité y brille.
    d = np.hypot(X - lx_, (Y - ly_) * 1.1)
    courbure = 1 - ((X - 96) / 110.0) ** 2
    P.rampe(np.ones(X.shape, dtype=bool), 0.95 - d / 120.0 + 0.2 * (pg.fbm(X / 6.0, Y / 4.0, 3, 660) - 0.5), [ENCRE, NU0, GR1, GR2, GR3], 0.85)
    pierres_de_taille(P, Y < 66, GR1, ENCRE, lh=6.0, lw=14.0)
    voile(P, (pg.fbm(X / 3.0, Y / 9.0, 3, 661) > 0.66) & (d < 60), BM1, 0.4)
    tab.plan("lointains", 0.2)
    # ---- L'escalier en colimaçon : il monte, à droite, et se perd dans le noir ; une meurtrière tout en haut.
    for i in range(13):
        y = 66.0 - i * 6.0
        x0 = 150.0 + 16.0 * math.sin(i * 0.5)
        l = 26.0 - i * 1.0
        c0 = (GR3, GR2, GR1, NU0)[min(3, i // 3)]
        P.poly([(x0, y), (x0 + l, y - 2.0), (x0 + l, y + 2.0), (x0, y + 4.0)], c0)
        P.trait(x0, y, x0 + l, y - 2.0, (GR4, GR3, GR2, GR1)[min(3, i // 3)])
    P.rect(146.0, -16.0, 5.0, 84.0, GR1)                          # le noyau
    P.rect(146.0, -16.0, 1.4, 84.0, GR2)
    voile(P, (X > 140) & (Y < 30), ENCRE, np.clip((30 - Y) / 40.0, 0, 0.9))
    P.rect(120.0, -10.0, 3.0, 9.0, NU2)
    P.rect(120.6, -9.4, 1.8, 7.8, NU4 if int(p * 8) % 8 else BM1)
    tab.plan("moyen", 0.5)
    # ---- Le sol dallé, le tas de charbon, les rangées de bidons d'huile.
    sol = Y > 64.0
    dallage(P, sol, 96.0, 48.0, GR2, GR1, larg=6.0, prof=1.2, joint=ENCRE)
    voile(P, sol & (np.hypot(X - lx_, (Y - 72) * 3.0) < 60), LU2, 0.34)
    voile(P, sol & (np.hypot(X - lx_, (Y - 72) * 3.0) > 90), ENCRE, 0.5)
    for i in range(16):                                         # le charbon
        x, y, r = 2 + 34 * hz(i, 1, 662), 62 + 6 * hz(i, 2, 662), 2.4 + 3.0 * hz(i, 3, 662)
        P.ell(x, y, r, r * 0.8, ENCRE if i % 3 else NU0)
        P.ell(x + r * 0.3, y - r * 0.3, r * 0.3, r * 0.2, GR2)
    P.trait(30.0, 66.0, 44.0, 58.0, BO2, P.ep(0.8))               # la pelle plantée dedans
    P.poly([(26.0, 64.0), (32.0, 62.0), (33.0, 68.0), (27.0, 69.0)], GR3)
    for j in range(2):
        for i in range(8 - j):
            bidon(P, 104.0 + i * 5.2 + j * 2.6, 66.0 - j * 7.2, 1.0, coul=(LU1, LU2) if (i + j) % 4 else (NU2, NU4))
    P.rect(100.0, 66.0, 44.0, 1.2, BO2)
    # La lanterne : pendue à son crochet, elle se balance un peu ; toute la lumière de la cave vient d'elle.
    P.trait(lx_, 14.0, lx_ + 0.4 * onde(p), ly_ - 7.0, GR1)
    P.trait(lx_ - 6, 14.0, lx_ + 6, 14.0, GR1, P.ep(0.7))
    halo(P, lx_, ly_, 44.0, LU2, 0.5)
    fanal(P, lx_ + 0.4 * onde(p), ly_ + 2.0, 1.6, lueur=20.0)
    # ---- Le panier pendu à sa poulie : il monte et descend à peine, comme si quelqu'un tenait la corde là-haut.
    px_, haut_ = 96.0, -16.0
    dy = 1.2 * onde(p)
    P.ell(px_, -6.0, 3.0, 3.0, GR2)
    P.ell(px_, -6.0, 1.4, 1.4, GR4)
    P.rect(px_ - 0.5, haut_, 1.0, 8.0, GR1)
    P.trait(px_ - 2.8, -6.0, px_ - 2.8, 52.0 + dy, GO2)           # le brin qui porte le panier
    P.trait(px_ + 2.8, -6.0, px_ + 2.8, 66.0, GO2)                # le brin libre, noué à un anneau
    P.ell(px_ + 2.8, 67.0, 1.4, 1.0, GR3)
    bx_, by_ = px_ - 2.8, 60.0 + dy
    P.courbe([(bx_ - 6, by_ - 4), (bx_, by_ - 10), (bx_ + 6, by_ - 4)], GO1, P.ep(0.6))        # l'anse
    pan = P.poly([(bx_ - 8, by_ - 4), (bx_ + 8, by_ - 4), (bx_ + 6, by_ + 6), (bx_ - 6, by_ + 6)], GO2)
    P.remplir(pan & ((P.XI + P.YI) % 3 == 0), GO1)
    P.remplir(pan & ((P.XI - P.YI) % 3 == 0), BO4)
    P.rect(bx_ - 8.4, by_ - 4.6, 16.8, 1.2, BO3)
    P.poly([(bx_ - 5, by_ - 4.6), (bx_ + 3, by_ - 4.6), (bx_ + 4, by_ - 7.4), (bx_ - 3, by_ - 8.0)], CREME)      # un linge : on y a mis quelque chose
    P.ell(bx_, by_ + 14.6 - dy, 9.0, 1.2, ENCRE)                 # son ombre au sol
    tab.plan("premier", 1.0)
    # ---- Premier plan : une barrique et des cordages à gauche, le départ de la rampe de fer à droite ; l'ombre.
    P.ell(6.0, 72.0, 11.0, 13.0, ENCRE)
    P.ell(7.0, 72.0, 9.0, 11.4, NU0)
    for y in (64.0, 80.0):
        P.rect(-4.0, y, 21.0, 1.0, GR1)
    P.courbe([(198.0, 40.0), (186.0, 50.0), (176.0, 66.0), (172.0, 80.0)], ENCRE, P.ep(1.4))
    for i in range(4):
        P.trait(190.0 - i * 5.0, 47.0 + i * 6.0, 190.0 - i * 5.0, 80.0, ENCRE, P.ep(0.6))
    voile(P, Y > 78.0, ENCRE, 0.4)
    poussiere(P, 30, 10, 130, 62, 16, LU4, 663)
    # ---- Seconde passe : les ombres portées, et la vie de la cave.
    # La lanterne est à gauche : tout projette son ombre vers la droite, longue, sur les dalles et sur le mur.
    ombre_portee(P, (Y > 66.0) & (Y < 71.0) & (X > 144.0) & (X < 176.0 + (Y - 66) * 2), 0.5)      # les bidons
    ombre_portee(P, (np.hypot((X - 112.0) / 16.0, (Y - 75.0) / 1.6) < 1.0), 0.55)                 # le panier
    ombre_portee(P, (np.abs(X - 130.0 - (Y - 20) * 0.5) < 2.0) & (Y > 20) & (Y < 60), 0.4)       # sa corde, sur le mur
    ombre_portee(P, (X > 36.0) & (X < 52.0) & (Y > 66.0) & (Y < 70.0), 0.5)                       # le tas de charbon
    # Là-haut, dans l'escalier : une lueur qui descend, puis remonte. Quelqu'un tient la corde.
    lu = 0.5 + 0.5 * onde(p)
    halo(P, 166.0, 6.0 + 4 * lu, 12.0 + 4 * lu, LU1, 0.5)
    halo(P, 166.0, 6.0 + 4 * lu, 5.0, LU3, 0.5)
    pg.papillon_de_nuit(P, 60.0, 38.0, 6.0, coul=BLANC)
    pg.souris(P, 124.0, 75.6, sens=-1, coul=GR3)
    pg.goutte(P, 20.0, -10.0, 60.0, coul=BM2, d=0.3)
    pg.goutte(P, 134.0, -10.0, 74.0, coul=BM2, d=0.8, flaque=BM1)
    pg.toile_araignee(P, 146.0, 40.0, 9.0, sens=(-1, 1), coul=BM2)
    pg.araignee(P, 78.0, -16.0, 10.0, d=0.5)
    for i in range(6):                                          # les éclats du charbon, qui accrochent la flamme
        if (p + 0.17 * i) % 1.0 < 0.4:
            P.point(6 + 30 * hz(i, 1, 664), 60 + 7 * hz(i, 2, 664), LU3)
    P.rect(76.0, 60.0, 12.0, 6.0, BO2)                            # une caisse marquée d'un poisson, un entonnoir, des chiffons
    P.rect(76.0, 60.0, 12.0, 1.0, BO4)
    P.ell(82.0, 63.4, 2.6, 1.0, BM2)
    P.poly([(90.0, 62.0), (96.0, 62.0), (94.0, 65.0), (93.6, 67.0), (92.4, 67.0), (92.0, 65.0)], GR3)
    pg.goutte(P, 93.0, 67.0, 70.0, coul=LU2, d=0.1)               # l'huile, goutte à goutte


# =====================================================================================================================
# La chambre de veille : une pièce ronde et chaude dans le phare. Poêle, lit étroit, fauteuil, table avec un gros carnet
# relié et une boîte en fer, une corne de brume à soufflet, une bougie, la nuit derrière la meurtrière.
# =====================================================================================================================
@decor("phare-eteint", "chambre-de-veille", soleil=(160.0, 50.0), tons=PHARE, nom="La chambre de veille", matiere=True)
def chambre_de_veille(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    fx_, fy_ = 160.0, 50.0                                      # le poêle
    tab.plan("ciel", 0.0)
    d = np.hypot(X - fx_, (Y - fy_) * 1.2)
    P.rampe(np.ones(X.shape, dtype=bool), 0.9 - d / 190.0 + 0.16 * (pg.fbm(X / 8.0, Y / 6.0, 3, 670) - 0.5), [GR1, GR2, BO2, BO3, LU1], 0.85)
    pierres_de_taille(P, (Y < 62) & (Y > 4), BO2, GR1, lh=6.0, lw=13.0)
    P.rampe(Y <= 4.0, 0.4 + 0.3 * (pg.fbm(X / 1.4, Y / 9.0, 2, 671) - 0.5) + 0.002 * X, [BO1, BO2, BO3], 0.6)        # le plafond de planches
    for x in range(-6, 198, 26):
        P.rect(x, -16.0, 4.0, 20.0, BO1)
    P.rect(-6.0, 3.0, 204.0, 1.4, BO1)
    tab.plan("lointains", 0.2)
    # ---- La meurtrière : profonde, la nuit bleue et la brume derrière ; une étoile, de temps en temps.
    mx_, my_ = 96.0, 10.0
    P.poly([(mx_ - 9, my_ - 2), (mx_ + 9, my_ - 2), (mx_ + 6, my_ + 30), (mx_ - 6, my_ + 30)], GR1)
    P.rect(mx_ - 3.0, my_ + 1, 6.0, 26.0, NU1)
    P.rampe((np.abs(X - mx_) < 3.0) & (Y > my_ + 1) & (Y < my_ + 27), 0.3 + 0.3 * (pg.fbm((X + 2 * onde(p)) / 4.0, Y / 5.0, 3, 672) - 0.5) + 0.01 * (Y - my_),
            [NU0, NU1, NU2, NU3], 0.8)
    if int(p * 8) % 4 == 0:
        P.point(mx_ + 0.6, my_ + 6.0, BM4)
    P.rect(mx_ - 7.0, my_ + 30, 14.0, 1.6, GR3)
    # Au mur : une carte des fonds, un baromètre, un ciré, des jumelles, la corne de brume à soufflet.
    P.rect(18.0, 12.0, 26.0, 18.0, CREME)
    P.rampe((X > 18) & (X < 44) & (Y > 12) & (Y < 30), 0.5 + 0.5 * (pg.fbm(X / 6.0, Y / 5.0, 3, 673) - 0.5), [BM3, BM4, CREME], 0.5)
    P.courbe([(20.0, 26.0), (28.0, 20.0), (36.0, 24.0), (42.0, 16.0)], NU3, 1)
    P.ell(34.0, 21.0, 1.0, 1.0, LU2)
    P.ell(58.0, 18.0, 4.4, 4.4, LAITON)
    P.ell(58.0, 18.0, 3.4, 3.4, CREME)
    P.trait(58.0, 18.0, 59.6 + 0.3 * onde(p), 16.0, ENCRE)
    cx_, cy_ = 124.0, 22.0                                      # la corne de brume
    P.poly([(cx_ - 12, cy_ - 2), (cx_ + 2, cy_ - 6), (cx_ + 2, cy_ + 6), (cx_ - 12, cy_ + 2)], LAITON)
    P.poly([(cx_ - 12, cy_ - 2), (cx_ + 2, cy_ - 6), (cx_ + 2, cy_ - 2), (cx_ - 12, cy_)], LAITON2)
    P.ell(cx_ + 2.6, cy_, 2.4, 6.6, LAITON)
    P.ell(cx_ + 3.2, cy_, 1.4, 5.0, BO1)
    souf = 1.0 + 0.3 * onde(p)
    for j in range(5):
        P.poly([(cx_ - 13 - j * 2.2 * souf, cy_ - 4.6), (cx_ - 12 - j * 2.2 * souf, cy_ - 4.6), (cx_ - 12 - j * 2.2 * souf, cy_ + 4.6),
                (cx_ - 13 - j * 2.2 * souf, cy_ + 4.6)], BO2 if j % 2 else BO1)
    P.rect(cx_ - 14 - 11 * souf, cy_ - 5.0, 1.6, 10.0, BO3)
    tab.plan("moyen", 0.5)
    # ---- Le plancher rond, le tapis ; le poêle de fonte et son tuyau ; le lit étroit ; le fauteuil ; la table.
    sol = Y > 62.0
    dallage(P, sol, 96.0, 46.0, BO3, BO2, larg=3.6, prof=0.0, joint=BO1)
    voile(P, sol & (np.hypot(X - fx_, (Y - 70) * 3.0) < 64), LU3, 0.32)
    voile(P, sol & (np.hypot(X - fx_, (Y - 70) * 3.0) > 100), GR1, 0.5)
    P.ell(96.0, 73.0, 30.0, 4.2, VI1)
    P.ell(96.0, 73.0, 27.0, 3.4, VI2)
    P.ell(96.0, 73.0, 18.0, 2.0, VI1)
    halo(P, fx_, fy_ + 6, 40.0, LU2, 0.5, ry=30)                 # le poêle
    P.rect(fx_ - 2.0, -16.0, 4.0, 52.0, GR1)
    P.rect(fx_ - 2.0, -16.0, 1.2, 52.0, GR2)
    P.rect(fx_ - 9.0, 36.0, 18.0, 28.0, ENCRE)
    P.rect(fx_ - 9.0, 36.0, 3.0, 28.0, GR1)
    P.rect(fx_ - 10.5, 34.0, 21.0, 2.4, GR2)
    P.rect(fx_ - 6.0, 44.0, 12.0, 9.0, GR1)
    for i in range(4):
        vif = (LU3, LU4, LU2, LU5)[(i + int(p * 8)) % 4]
        P.rect(fx_ - 5.0 + i * 2.6, 45.0, 1.6, 7.0, vif)
    for x in (fx_ - 8.0, fx_ + 6.0):
        P.rect(x, 64.0, 2.0, 3.0, ENCRE)
    P.ell(fx_, 33.0, 4.0, 2.4, GR2)                              # la bouilloire
    P.rect(fx_ - 4.0, 31.0, 8.0, 3.0, GR2)
    P.courbe([(fx_ + 4.0, 32.0), (fx_ + 7.0, 30.6), (fx_ + 8.0, 28.6)], GR2, P.ep(0.6))
    for k in range(4):
        t = (p + k / 4.0) % 1.0
        voile(P, np.hypot(X - (fx_ + 8.6 + 1.6 * math.sin(t * 5 + k)), Y - (27.0 - 12 * t)) < 0.8 + 1.8 * t, BM4, 0.55 - 0.5 * t)
    lx0 = -6.0                                                  # le lit étroit, à gauche : couverture à carreaux, oreiller
    P.rect(lx0, 54.0, 46.0, 10.0, BO1)
    P.rect(lx0, 50.0, 46.0, 5.0, VOLET)
    for i in range(12):
        P.rect(lx0 + i * 4.0, 50.0, 2.0, 5.0, VOLET2 if i % 2 else NU3)
    P.rect(lx0, 52.0, 46.0, 0.6, CREME)
    P.ell(4.0, 48.6, 7.0, 2.6, CREME)
    P.rect(38.0, 40.0, 3.0, 26.0, BO1)
    P.ell(39.5, 40.0, 2.2, 2.2, BO3)
    fx0 = 52.0                                                  # le fauteuil
    P.ell(fx0 + 9, 46.0, 10.0, 9.0, LU1)
    P.rect(fx0 - 1, 46.0, 20.0, 18.0, LU1)
    P.ell(fx0 + 9, 47.0, 8.0, 7.0, LU2)
    P.rect(fx0 + 1, 47.0, 16.0, 12.0, LU2)
    P.rect(fx0 - 3, 54.0, 5.0, 12.0, LU1)
    P.rect(fx0 + 16, 54.0, 5.0, 12.0, LU1)
    P.rect(fx0 + 1, 58.0, 16.0, 4.0, LU3)
    P.poly([(fx0 + 2, 50.0), (fx0 + 12, 49.0), (fx0 + 14, 58.0), (fx0 + 3, 59.0)], VI2)        # un plaid
    tx0, tx1, ty = 96.0, 136.0, 58.0                            # la table : le gros carnet relié, la boîte en fer, la bougie
    P.rect(tx0, ty, tx1 - tx0, 2.6, BO3)
    P.rect(tx0, ty, tx1 - tx0, 0.7, BO4)
    for x in (tx0 + 2, tx1 - 4):
        P.rect(x, ty + 2.6, 2.0, 14.0, BO1)
    P.poly([(tx0 + 4, ty - 0.4), (tx0 + 20, ty - 0.4), (tx0 + 21, ty - 4.4), (tx0 + 5, ty - 4.4)], LU1)
    P.poly([(tx0 + 5, ty - 4.4), (tx0 + 21, ty - 4.4), (tx0 + 20.6, ty - 5.4), (tx0 + 5.4, ty - 5.4)], CREME)
    P.rect(tx0 + 4, ty - 1.2, 16.6, 0.6, CREME)
    P.rect(tx0 + 11, ty - 5.4, 1.0, 5.0, LU2)                    # le signet
    P.rect(tx0 + 24, ty - 5.0, 9.0, 5.0, GR3)                    # la boîte en fer
    P.rect(tx0 + 24, ty - 5.0, 9.0, 1.2, BM2)
    P.rect(tx0 + 27.6, ty - 3.4, 1.8, 1.4, LAITON)
    bougie(P, tx0 + 36.0, ty - 0.2, h=6.0, lueur=16.0)
    P.rect(tx0 + 10, ty + 6.0, 12.0, 1.4, BO3)                   # un tabouret glissé dessous
    tab.plan("premier", 1.0)
    # ---- Premier plan : la trappe ouverte et le haut de l'échelle, à droite ; une paire de sabots ; l'ombre du bas.
    P.poly([(176.0, 74.0), (198.0, 74.0), (198.0, 80.0), (172.0, 80.0)], ENCRE)
    P.poly([(176.0, 74.0), (198.0, 74.0), (198.0, 60.0), (182.0, 60.0)], BO1)                 # le battant relevé
    P.poly([(177.6, 73.0), (197.0, 73.0), (197.0, 61.4), (183.0, 61.4)], BO2)
    for x in (182.0, 190.0):
        P.rect(x, 70.0, 1.0, 10.0, BO3)
    for (x, c0) in ((24.0, BO3), (30.0, BO2)):
        P.ell(x, 77.6, 3.2, 1.6, c0)
        P.ell(x - 1.0, 77.0, 1.6, 0.8, ENCRE)
    voile(P, Y > 78.0, ENCRE, 0.35)
    poussiere(P, 100, 10, 190, 62, 16, LU4, 674)
    # ---- Seconde passe : la vie de la chambre.
    chat(P, 62.0, 56.6, coul=GR2)                                 # sur le fauteuil
    ombre_portee(P, (np.hypot((X - 116.0) / 22.0, (Y - 74.0) / 1.6) < 1.0), 0.4)
    ombre_portee(P, (np.hypot((X - 60.0) / 14.0, (Y - 67.0) / 1.4) < 1.0), 0.4)
    pg.papillon_de_nuit(P, 132.0, 50.0, 5.0, coul=BLANC)
    pg.araignee(P, 76.0, 4.0, 8.0, d=0.2)
    pg.souris(P, 140.0, 77.6, sens=-1, coul=GR3)
    t = int(p * 8)                                              # une page du carnet se soulève toute seule
    P.poly([(108.0, 52.6), (116.0, 52.6), (115.0 - (t % 4), 50.0 - (t % 4) * 0.4)], CREME)
    for i in range(4):                                          # le linge qui sèche près du poêle
        bal = 0.3 * onde(p, 0.2 * i)
        P.rect(176.0 + i * 4.0 + bal, 20.0, 3.0, 6.0 + (i % 2) * 2, (CREME, VOLET2, BM3, LU2)[i])
    P.trait(174.0, 19.6, 194.0, 19.6, GO2)
    bal = 0.5 * onde(p, 0.6)                                    # un ciré pendu, qui goutte encore
    P.poly([(8.0, 14.0), (16.0, 14.0), (18.0 + bal, 36.0), (6.0 + bal, 36.0)], CIRE)
    pg.goutte(P, 12.0, 36.0, 49.0, coul=BM3, d=0.4)


# =====================================================================================================================
# La lanterne : le sommet du phare. Une grande lentille de verre à échelons (la clé), une machine d'horlogerie en laiton
# avec cadran et manivelle, un poids au bout de sa chaîne, des vitres tout autour ouvertes sur la brume. Le sol : y = 76.
# =====================================================================================================================
@decor("phare-eteint", "lanterne-du-phare", soleil=(96.0, 20.0), tons=PHARE, nom="La lanterne", matiere=True)
def lanterne_du_phare(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    # ---- Dehors, tout autour : la nuit et la brume, qui tournent lentement derrière les vitres.
    pg.ciel(P, horizon=64.0, haut=0.0, halo=0.0, etoiles=0.12, disque=0)
    tab.plan("nuages", 0.08)
    pg.voiles(P, y=0.0, epais=14.0, seuil=0.52, graine=680)
    pg.voiles(P, y=34.0, epais=12.0, seuil=0.52, graine=681)
    for g in range(4):
        brume(P, 10.0 + g * 16.0, 6.0, 60 + g, T.CIEL[3 + g % 2], 0.5)
    for i in range(5):                                          # très bas, très loin : les feux de Trébrume
        if (p + hz(i, 1, 682)) % 1.0 < 0.8:
            P.point(14 + 5 * i, 60.0 + hz(i, 2, 682), LU3)
    tab.plan("lointains", 0.2)
    # ---- La cage de verre : montants de fer, croisillons en losange, le dôme de cuivre au-dessus.
    for i in range(9):
        x = -4 + i * 25.0
        P.rect(x - 0.9, -6.0, 1.8, 72.0, ENCRE)
        P.rect(x - 0.9, -6.0, 0.6, 72.0, GR1)
        if i < 8:
            P.trait(x, -6.0, x + 25.0, 30.0, GR1)
            P.trait(x + 25.0, -6.0, x, 30.0, GR1)
            P.trait(x, 30.0, x + 25.0, 66.0, GR1)
            P.trait(x + 25.0, 30.0, x, 66.0, GR1)
            voile(P, (X > x + 1) & (X < x + 24) & (Y > -6) & (Y < 66) & (np.abs((X - x) - (Y + 6) * 0.3 - 4) < 2.0), T.CIEL[5], 0.2)
    P.rect(-6.0, 29.4, 204.0, 1.2, ENCRE)
    P.rampe(Y < -6.0, 0.4 + 0.02 * (Y + 16) + 0.004 * (X - 96) + 0.2 * (pg.fbm(X / 6.0, Y / 2.0, 2, 683) - 0.5), [BO1, LU1, LAITON], 0.7)   # le dôme
    for x in range(-6, 198, 12):
        P.trait(x, -16.0, x + (x - 96) * 0.08, -6.0, BO1)
    P.rect(-6.0, -6.6, 204.0, 1.2, ENCRE)
    tab.plan("moyen", 0.5)
    # ---- La galerie : un muret de fonte sous les vitres, le plancher de tôle striée.
    P.rampe((Y > 64.0), 0.4 + 0.2 * (pg.fbm(X / 9.0, Y / 3.0, 3, 684) - 0.5), [ENCRE, GR1, GR2], 0.8)
    for x in range(-6, 198, 8):
        P.rect(x, 65.0, 6.0, 5.0, GR2)
        P.rect(x, 65.0, 6.0, 0.7, GR3)
    sol = Y > 70.0
    dallage(P, sol, 96.0, 56.0, GR2, GR1, larg=2.4, prof=2.4, joint=ENCRE)
    voile(P, sol & (np.hypot(X - 96, (Y - 76) * 3.4) > 80), ENCRE, 0.5)
    # ---- La lentille : un grand tambour de verre à échelons, cerclé de laiton ; éteinte, elle garde un reflet de bougie.
    cx, cy = 96.0, 24.0
    u, w = (X - cx) / 24.0, (Y - cy) / 30.0
    lent = (u * u + w * w <= 1)
    r2 = np.sqrt(u * u + w * w)
    P.rampe(lent, 0.35 + 0.35 * (1 - r2) - 0.25 * u + 0.12 * np.sin(r2 * 34.0), [NU1, NU2, NU3, NU4, BM1, BM3], 0.6)
    for k in range(1, 9):                                       # les échelons : des anneaux de prismes
        P.remplir(lent & (np.abs(r2 - k / 9.0) < 0.016), BM2 if k % 2 else NU4)
    P.remplir(lent & (np.abs(u) < 0.014), LAITON)
    P.remplir(lent & (np.abs(w) < 0.012), LAITON)
    P.remplir((u * u + w * w <= 1.07) & ~lent, LAITON)
    P.remplir((u * u + w * w <= 1.07) & ~lent & (u < -0.2) & (w < 0), LAITON2)
    P.remplir(r2 < 0.15, NU0)                                    # l'œil-de-bœuf, au centre
    P.remplir((r2 < 0.15) & (np.hypot(u + 0.04, w + 0.04) < 0.06), BM2)
    refl = (lent & (np.hypot(u + 0.42, w + 0.4) < 0.16))
    voile(P, refl, BM4, 0.6)
    eclat = int(p * 8) % 8
    P.remplir(lent & (np.hypot(u - 0.3 - 0.02 * eclat, w - 0.36) < 0.05), LU4)                 # le reflet de la bougie, qui danse
    P.rect(cx - 16.0, cy + 30.0, 32.0, 3.0, LAITON)                                           # le socle tournant
    P.rect(cx - 16.0, cy + 30.0, 32.0, 0.7, LAITON2)
    P.rect(cx - 12.0, cy + 33.0, 24.0, 10.0, GR1)
    P.rect(cx - 12.0, cy + 33.0, 4.0, 10.0, GR2)
    P.rect(cx - 15.0, cy + 43.0, 30.0, 3.4, GR2)
    # La machine d'horlogerie : un coffre de laiton vitré, ses rouages, le cadran, la manivelle ; le poids et sa chaîne.
    mx0, my0 = 128.0, 44.0
    P.rect(mx0, my0, 30.0, 26.0, LAITON)
    P.rect(mx0, my0, 30.0, 1.4, LAITON2)
    P.rect(mx0 + 2, my0 + 3, 26.0, 16.0, NU0)
    for i, (dx, dy, r) in enumerate(((7.0, 10.0, 5.0), (15.4, 8.0, 3.6), (22.0, 12.0, 4.4), (14.0, 15.0, 2.4))):
        pg.roue(P, mx0 + dx, my0 + dy, r, int(r * 3), LAITON, LAITON2, NU0, angle=0.3 * i + (0.1 * math.sin(p * 6.283) if i == 3 else 0))
    voile(P, (X > mx0 + 2) & (X < mx0 + 28) & (Y > my0 + 3) & (Y < my0 + 19) & (np.abs((X - mx0) - (Y - my0) - 6) < 2), BM3, 0.3)
    P.ell(mx0 + 8, my0 + 23.0, 2.6, 2.6, CREME)                   # le cadran
    P.trait(mx0 + 8, my0 + 23.0, mx0 + 9.4, my0 + 21.6, ENCRE)
    P.trait(mx0 + 30, my0 + 12.0, mx0 + 37.0, my0 + 12.0, GR3, P.ep(0.8))                      # la manivelle
    P.trait(mx0 + 37.0, my0 + 12.0, mx0 + 37.0, my0 + 18.0, GR3, P.ep(0.8))
    P.rect(mx0 + 35.6, my0 + 18.0, 3.0, 4.0, BO3)
    for x in (mx0 + 3, mx0 + 25):
        P.rect(x, my0 + 26, 2.0, 4.0, GR1)
    px_ = 70.0                                                  # le poids, au bout de sa chaîne : il est tout en bas
    for j in range(26):
        P.ell(px_ + 0.2 * onde(p, j * 0.03), -6.0 + j * 2.6, 0.7, 1.2, GR3 if j % 2 else GR1)
    P.poly([(px_ - 3.0, 62.0), (px_ + 3.0, 62.0), (px_ + 2.2, 72.0), (px_ - 2.2, 72.0)], GR2)
    P.rect(px_ - 3.0, 62.0, 6.0, 1.0, GR4)
    P.rect(px_ - 3.0, 62.0, 1.2, 10.0, GR3)
    P.ell(px_, 72.6, 4.4, 0.9, ENCRE)
    # Sur le plancher : une burette d'huile, un chiffon, une bougie posée à même la tôle.
    bougie(P, 46.0, 73.6, h=5.0, lueur=18.0)
    bidon(P, 30.0, 74.0, 0.8)
    P.poly([(52.0, 74.0), (60.0, 73.0), (62.0, 75.4), (53.0, 76.0)], CREME)
    tab.plan("premier", 1.0)
    # ---- Premier plan : le garde-corps de la trappe à gauche, l'échelle du dôme à droite, noirs sur la nuit.
    P.courbe([(-6.0, 50.0), (10.0, 52.0), (18.0, 62.0), (20.0, 80.0)], ENCRE, P.ep(1.4))
    for i in range(4):
        P.trait(2.0 + i * 4.4, 51.0 + i * 3.0, 2.0 + i * 4.4, 80.0, ENCRE, P.ep(0.6))
    for x in (180.0, 190.0):
        P.rect(x, -16.0, 1.4, 96.0, ENCRE)
    for j in range(12):
        P.rect(180.0, -12.0 + j * 8.0, 11.4, 1.0, ENCRE)
        P.rect(180.0, -12.0 + j * 8.0, 11.4, 0.4, GR1)
    voile(P, Y > 78.4, ENCRE, 0.4)
    poussiere(P, 60, 0, 140, 60, 10, BM2, 685)
    # ---- Seconde passe : la vie de la lanterne.
    pg.papillon_de_nuit(P, 46.0, 64.0, 6.0, coul=BLANC)
    pg.papillon_de_nuit(P, 96.0, 24.0, 28.0, coul=BM4, d=0.4)     # il cherche la lumière qui n'est plus là
    for i in range(4):                                          # des oiseaux de mer se cognent aux vitres, puis repartent
        t = (p + i / 4.0) % 1.0
        x, y = 6 + 180 * ((hz(i, 1, 686) + t * 0.4) % 1.0), 4 + 20 * hz(i, 2, 686) + 3 * math.sin(t * 9)
        a = onde(p * 2, 0.2 * i)
        P.trait(x - 2.0, y - 0.8 * a, x, y, BM3)
        P.trait(x, y, x + 2.0, y - 0.8 * a, BM3)
    pg.goutte(P, 120.0, -6.0, 70.0, coul=BM2, d=0.3, flaque=BM1)  # le dôme fuit
    pg.araignee(P, 150.0, -6.0, 9.0, d=0.6)
    pg.toile_araignee(P, 21.0, -6.0, 9.0, sens=(1, 1), coul=BM2)
    P.poly([(108.0, 71.0), (120.0, 70.0), (121.0, 74.0), (109.0, 75.0)], CREME)                   # le registre du gardien, ouvert
    for j in range(3):
        P.trait(110.0, 72.0 + j * 0.9, 118.0 - j * 2, 71.6 + j * 0.9, NU2)
    ombre_portee(P, (np.hypot((X - 70.0) / 9.0, (Y - 74.0) / 1.2) < 1.0), 0.5)
    v = onde(p)                                                 # un chiffon noué à la manivelle, qui bat
    P.poly([(165.0, 62.0), (169.0, 63.0 + 0.6 * v), (166.0, 66.0)], LU2)
    pg.etincelle(P, 143.4, 52.0, coul=LAITON2, d=0.5)             # la machine cherche encore à partir


# =====================================================================================================================
# La jetée, la nuit : le bout d'une jetée de pierre en pleine nuit de brume. Des silhouettes qui attendent, des petits
# feux de mât flous qui approchent sur l'eau noire, le phare au loin (la clé, en haut à droite) : rallumé.
# Le sol monte un peu : de (4, 61) à (64, 66).
# =====================================================================================================================
@decor("phare-eteint", "jetee-nuit", soleil=(174.0, 6.0), tons=PHARE, nom="La jetée, la nuit", matiere=True)
def jetee_nuit(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=44.0, haut=0.0, halo=0.16, etoiles=0.2, disque=0)
    tab.plan("nuages", 0.08)
    pg.voiles(P, y=-6.0, epais=12.0, seuil=0.55, graine=690)
    tab.plan("lointains", 0.2)
    # ---- Le phare, loin, rallumé : son faisceau balaie la brume (un demi-tour par boucle : deux faisceaux opposés).
    fx_, fy_ = 174.0, 40.0
    h = 36.0
    lx_, ly_ = fx_, fy_ - h * 0.87
    a = p * math.pi
    for cote in (0, 1):
        ang = a + cote * math.pi
        dx, dy = X - lx_, (Y - ly_) * 2.2
        along = dx * math.cos(ang) + dy * math.sin(ang)
        across = -dx * math.sin(ang) + dy * math.cos(ang)
        cone = (along > 0) & (np.abs(across) < 1.0 + along * 0.2)
        voile(P, cone & (Y < 46), LU5, np.clip(0.55 - along / 260.0, 0, 0.55) * np.clip(1 - np.abs(across) / (1.0 + along * 0.2), 0, 1) ** 0.6)
    phare(P, fx_, fy_, h, ENCRE, NU1, allume=True)
    for g, (y, ep) in enumerate(((36.0, 5.0), (26.0, 5.0), (14.0, 5.0))):
        brume(P, y, ep, 70 + g, T.CIEL[4], 0.45)
    tab.plan("moyen", 0.5)
    # ---- L'eau noire ; les petits feux de mât, flous, qui approchent ; leurs reflets en pointillé.
    mer = Y > 42.0
    P.rampe(mer, 0.22 + 0.2 * (pg.fbm((X + 2 * onde(p)) / 14.0, Y / 1.2, 3, 691) - 0.5) + 0.25 * np.exp(-((X - fx_) / 12.0) ** 2) - 0.004 * (Y - 42),
            [ME0, ME1, ME2, NU3], 0.85)
    cell = (P.XI + (P.YI % 3) * 2) // 3
    P.remplir(mer & (hz(cell, P.YI, 692) < 0.5 * np.exp(-((X - fx_) / (3 + (Y - 42) * 0.3)) ** 2)) & (np.floor(((p + hz(cell, P.YI, 693)) % 1.0) * 4) < 2), LU4)
    for i, (x, y, k) in enumerate(((92.0, 50.0, 0.6), (112.0, 54.0, 0.8), (134.0, 49.0, 0.5), (150.0, 58.0, 1.0), (76.0, 56.0, 0.9),
                                   (122.0, 46.0, 0.4), (164.0, 51.0, 0.6))):
        x = x - 0.8 * k * onde(p, 0.1 * i)
        y = y + 0.3 * k * onde(p, 0.3 + 0.2 * i)
        P.poly([(x - 6 * k, y - 1.4 * k), (x + 6.6 * k, y - 1.8 * k), (x + 4.6 * k, y + 0.8 * k), (x - 4.4 * k, y + 0.8 * k)], ENCRE)
        P.trait(x, y - 1.6 * k, x, y - 13.0 * k, ENCRE)
        vif = (p + 0.21 * i) % 1.0 < 0.85
        halo(P, x, y - 13.0 * k, 5.0 * k + 2, LU3, 0.5 if vif else 0.25)
        P.point(x, y - 13.4 * k, LU5 if vif else LU3, 2 if k > 0.7 else 1)
        if k > 0.7:
            P.point(x - 3 * k, y - 2.6 * k, LU2)                 # un fanal de bord
        for j in range(int(3 + 4 * k)):
            if (j + i + int(p * 8)) % 3:
                P.trait(x - 1.2 * k, y + 2 + j * 1.6, x + 1.2 * k, y + 2 + j * 1.6, LU2 if j < 3 else LU1)
    brume(P, 46.0, 3.0, 74, T.CIEL[4], 0.5)
    brume(P, 54.0, 2.6, 75, T.CIEL[3], 0.4)
    # ---- La jetée : de gros blocs de granit, le musoir arrondi, un escalier, des bittes, les fanaux de ceux qui attendent.
    haut_j = lambda x: 61.0 + (_a(x) - 4.0) * (5.0 / 60.0)
    jetee = (Y > haut_j(X)) & ((X < 84.0) | (np.hypot(X - 84.0, (Y - 80.0) * 1.4) < 22.0))
    P.rampe(jetee, 0.5 + 0.3 * (pg.fbm(X / 5.0, Y / 2.4, 3, 694) - 0.5) - 0.02 * (Y - haut_j(X)), [ENCRE, NU0, GR1, GR2, GR3], 0.8)
    pierres_de_taille(P, jetee & (Y > haut_j(X) + 2.6), GR1, ENCRE, lh=4.4, lw=10.0)
    P.remplir(P.crete(jetee), GR4)
    voile(P, jetee & (Y < haut_j(X) + 2.4), BM1, 0.3)
    for x in (70.0, 90.0):
        y = float(haut_j(min(x, 84.0))) + (2.0 if x > 84 else 0)
        P.rect(x - 1.3, y - 4.6, 2.6, 5.0, ENCRE)
        P.ell(x, y - 4.6, 2.0, 0.9, GR2)
    # Les silhouettes qui attendent, serrées, de dos : des cirés, des bonnets, un enfant sur des épaules, des fanaux levés.
    for i, (x, hgt, larg) in enumerate(((74.0, 13.0, 3.6), (79.0, 15.0, 4.0), (84.5, 11.0, 3.2), (89.5, 14.0, 3.8), (95.0, 12.0, 3.4),
                                        (99.0, 9.0, 2.8))):
        y = 67.6 + (i % 2) * 0.8
        P.poly([(x - larg, y), (x + larg, y), (x + larg * 0.7, y - hgt * 0.7), (x - larg * 0.7, y - hgt * 0.7)], ENCRE if i % 2 else NU0)
        P.ell(x, y - hgt * 0.82, larg * 0.62, hgt * 0.16, ENCRE if i % 2 else NU0)
        if i == 1:
            P.ell(x + 0.4, y - hgt - 1.6, 1.6, 1.8, NU0)        # l'enfant
        if i in (0, 3):
            bal = 0.4 * onde(p, 0.3 * i)
            P.trait(x + larg * 0.8, y - hgt * 0.6, x + larg * 1.6 + bal, y - hgt * 0.9, ENCRE)
            fanal(P, x + larg * 1.6 + bal, y - hgt * 0.9 + 4.6, 0.8, lueur=9.0)
        elif i == 2:
            P.poly([(x - larg, y - hgt * 0.6), (x - larg * 1.2, y - hgt * 0.2), (x - larg * 0.6, y - hgt * 0.3)], CIRE)   # un ciré jaune
    tab.plan("premier", 1.0)
    # ---- Premier plan : un réverbère de port à gauche (éteint), un tas de casiers et de cordages à droite, des goélands endormis.
    P.rect(-2.0, 10.0, 2.0, 70.0, ENCRE)
    P.rect(-4.4, 6.0, 6.8, 5.0, ENCRE)
    P.rect(-3.6, 7.0, 5.2, 3.0, NU1)
    casier(P, 172.0, 80.0, 1.6)
    casier(P, 184.0, 81.0, 1.8)
    casier(P, 178.0, 73.0, 1.4)
    for r in (7.0, 5.0, 3.0):
        P.ell(156.0, 78.4, r, r * 0.34, ENCRE if r != 5.0 else NU1)
    goeland(P, 178.0, 67.6, sens=-1)
    voile(P, Y > 78.4, ENCRE, 0.4)
    brume(P, 72.0, 3.0, 76, T.CIEL[3], 0.3, x0=96)
    # ---- Seconde passe : la jetée se peuple.
    # Le faisceau, cette fois bien lisible : deux pinceaux pleins qui tournent.
    for cote in (0, 1):
        ang = p * math.pi + cote * math.pi
        dx_, dy_ = X - 174.0, (Y - (40.0 - 36.0 * 0.87)) * 2.2
        along = dx_ * math.cos(ang) + dy_ * math.sin(ang)
        across = -dx_ * math.sin(ang) + dy_ * math.cos(ang)
        voile(P, (along > 2) & (np.abs(across) < 0.6 + along * 0.12) & (Y < 44), LU4, 0.7, lumiere=True)
    # Le premier rang : trois silhouettes plus proches, de dos, sur le musoir ; un chien assis qui remue la queue.
    for i, (x, hgt, larg) in enumerate(((104.0, 20.0, 5.0), (114.0, 24.0, 5.6), (124.0, 17.0, 4.6))):
        y = 78.0
        P.poly([(x - larg, y), (x + larg, y), (x + larg * 0.7, y - hgt * 0.7), (x - larg * 0.7, y - hgt * 0.7)], ENCRE)
        P.ell(x, y - hgt * 0.82, larg * 0.62, hgt * 0.15, ENCRE)
        P.trait(x - larg * 0.7, y - hgt * 0.7, x + larg * 0.7, y - hgt * 0.7, NU2)
        if i == 1:                                              # celui du milieu lève sa lanterne et l'agite
            bal = 1.0 * onde(p)
            P.trait(x + larg * 0.7, y - hgt * 0.6, x + larg * 1.5 + bal, y - hgt * 1.05, ENCRE, P.ep(0.7))
            fanal(P, x + larg * 1.5 + bal, y - hgt * 1.05 + 5.0, 1.0, lueur=14.0)
        if i == 2:
            P.poly([(x - larg, y - hgt * 0.6), (x - larg * 1.3, y - hgt * 0.1), (x - larg * 0.5, y - hgt * 0.2)], CIRE)
    P.ell(136.0, 77.0, 2.6, 2.0, ENCRE)
    P.ell(137.6, 74.6, 1.4, 1.3, ENCRE)
    P.courbe([(134.0, 77.6), (131.6, 77.0), (130.6, 75.6 - 1.0 * abs(onde(p * 2)))], ENCRE, P.ep(0.6))
    # Le clapot contre la jetée, l'écume ; une cloche de brume ; une bouée qui clignote au large.
    for i in range(8):
        t = (p + i / 8.0) % 1.0
        P.trait(60.0 + i * 5.0, 70.0 + (i % 3) * 2.4, 64.0 + i * 5.0 + 2 * t, 70.0 + (i % 3) * 2.4, BM2 if t < 0.5 else NU4)
    bal = 0.7 * onde(p, 0.2)
    P.rect(46.0, 46.0, 1.2, 16.0, ENCRE)
    P.trait(46.6, 46.0, 52.0, 46.0, ENCRE)
    P.poly([(49.6 + bal, 46.6), (54.0 + bal, 46.6), (55.0 + bal, 51.4), (48.6 + bal, 51.4)], LAITON)
    if (p * 2) % 1.0 < 0.5:
        P.point(110.0, 47.0, LU4, 2)
        halo(P, 110.4, 47.4, 4.0, LU2, 0.5)
    pg.papillon_de_nuit(P, 120.0, 52.0, 5.0, coul=BM4, d=0.3)
    P.poly([(10.0, 56.0), (22.0, 56.0), (21.0, 61.0), (11.0, 61.0)], BO2)                         # des caisses, un filet, sur la jetée
    P.rect(10.0, 56.0, 12.0, 1.0, BO4)
    # Une étoile filante au-dessus du phare.
    if int(p * 8) in (5, 6):
        P.trait(120.0 + int(p * 8) * 3, -8.0, 114.0 + int(p * 8) * 3, -10.0, BLANC)
