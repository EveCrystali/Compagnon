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
# Le guet : une chambre sous le toit, « grande comme un tiroir », la nuit. La chandelle vient d'être soufflée : il ne
# reste que la lune dans la brume, qui entre par le carreau (la clé) et couche ses petits-bois sur le plancher. Dehors,
# la mer, le quai, et très loin une minuscule lueur jaune à une fenêtre du phare noir. La chaise est coincée sous la
# poignée de la porte ; l'édredon rouge attend sur le lit ; le bol de soupe fume encore sur le rebord.
# =====================================================================================================================
R_BOISNUIT = [ENCRE, R_BOIS[0], R_BOIS[1], R_PLATRE[1], NU2, NU3, NU4, BM1, BM2]


@decor("phare-eteint", "guet-de-nuit", soleil=(112.0, 22.0), tons=PHARE, nom="Le guet", matiere=True)
def guet_de_nuit(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tout = np.ones(X.shape, dtype=bool)
    wx, wy, ww, wh = 54.0, 0.0, 84.0, 48.0                      # le carreau
    LUNE = (82.0, 12.0)
    SOL = 64.0                                                  # le pied du mur

    # ============================================================================================ dehors, par le carreau
    tab.plan("ciel", 0.0)
    P.horizon, P.ciel_haut, P.halo = 30.0, 0.05, 0.3
    P.soleil = LUNE
    vc = pg.valeur_ciel(P, X, Y)
    P.rampe(tout, 0.04 + 0.6 * vc, T.CIEL, 0.75)
    for i in range(30):
        ex, ey = wx + ww * hz(i, 1, 800), wy + 20.0 * hz(i, 2, 800) ** 1.5
        if math.hypot(ex - LUNE[0], ey - LUNE[1]) > 16.0 and (p + hz(i, 3, 800)) % 1.0 < 0.7:
            P.point(ex, ey, T.CIEL[8] if hz(i, 4, 800) < 0.4 else T.CIEL[5])
    dl = np.hypot(X - LUNE[0], Y - LUNE[1])
    P.rampe(dl < 11.0, 0.3 + 0.7 * np.clip(1 - dl / 11.0, 0, 1) ** 1.5 + 0.5 * vc, T.CIEL[3:10], 0.6)
    P.remplir(dl < 3.8, T.CIEL[10])
    P.remplir(dl < 3.2, T.SOL)
    P.remplir((dl < 3.2) & (pg.fbm(X / 1.6, Y / 1.6, 2, 801) > 0.6), T.CIEL[10])

    def nappe(y, epais, graine, tons, seuil=0.62, zone=None):
        def dens(yy):
            return (0.4 + pg.fbm((X + 1.4 * onde(p, 0.013 * graine)) / 15.0, yy / 2.4, 3, graine)) * np.exp(-((yy - y - 1.0 * np.sin(X / 19.0 + graine)) / epais) ** 2) - seuil
        d = dens(Y)
        prox = np.exp(-(np.hypot(X - LUNE[0], (Y - LUNE[1]) * 1.4) / 50.0) ** 2)
        m = d > 0
        if zone is not None:
            m &= zone
        P.rampe(m, 0.2 + 1.5 * d + 1.6 * (d - dens(Y + 1.0)) + 0.45 * prox, tons, 0.6)

    nappe(7.0, 2.6, 802, T.CIEL[3:9], 0.7)
    nappe(18.0, 2.2, 803, T.CIEL[4:9], 0.72)
    tab.plan("lointains", 0.1)
    HOR = 30.0
    # La Dent-Creuse, noire, au large ; une lueur jaune à une fenêtre du milieu : quelqu'un s'y promène avec une bougie.
    dent_creuse(P, 112.0, HOR - 0.6, 24.0, LUNE)
    t = (p * 1.0) % 1.0
    lx_ = 111.6 + (0.0 if t < 0.5 else 0.5)
    if t < 0.85:
        P.rect(lx_, HOR - 10.6, 0.8, 1.2, LU5)
        for (ax_, ay_) in ((-0.4, 0.0), (0.8, 0.0), (0.0, -0.4), (0.0, 1.2)):
            P.point(lx_ + ax_, HOR - 10.6 + ay_, LU2)
    nappe(HOR - 0.8, 1.6, 804, T.CIEL[5:10], 0.66)
    # La mer : le miroir de la nuit, le chemin de lune ; un feu de bateau qui s'éloigne.
    mer = Y > HOR
    pg.miroir(P, tab.derriere(), HOR, fonce=(36.0, 10.0), eclats=0.85, rides=0.08, graine=805)
    bx_ = 70.0 + 1.5 * onde(p, 0.2)
    P.poly([(bx_ - 2.4, HOR + 2.2), (bx_ + 2.8, HOR + 2.0), (bx_ + 2.0, HOR + 3.2), (bx_ - 2.0, HOR + 3.2)], NU0)
    P.trait(bx_, HOR + 2.0, bx_, HOR - 2.4, NU0)
    if (p + 0.3) % 1.0 < 0.8:
        P.point(bx_, HOR - 2.8, LU4)
    nappe(HOR + 5.0, 1.3, 806, T.CIEL[4:8], 0.72)
    # Le quai sous la fenêtre : des toits d'ardoise mouillés, une cheminée qui fume, le fanal du quai.
    pas = 28.0
    u_ = ((X - wx + 6.0) % pas) / pas
    toits = (Y > 43.6 - 6.0 * (1 - np.abs(u_ - 0.5) * 2)) & mer
    pente = u_ > 0.5
    rang_ = np.floor(Y / 0.82)
    ard = ((X + rang_ * 0.8) % 1.6) < 0.4
    P.rampe(toits, 0.22 + 0.3 * pente - 0.1 * ard - 0.016 * (Y - 40.0), [ENCRE, NU0, VI1, NU2, VI2, NU3], 0.5)
    lisere(P, toits, BM1, 0, -1, cond=pente)
    for cx_ in (wx + 24.0, wx + 70.0):
        P.rect(cx_, 33.6, 2.6, 8.0, NU0)
        P.rect(cx_ + 1.8, 33.6, 0.8, 8.0, NU3)
        P.rect(cx_ - 0.4, 33.0, 3.4, 0.8, ENCRE)
    fumerolle(P, wx + 25.2, 32.4, h=12.0, n=3, d=0.2, coul=T.CIEL[6], force=0.4, large=0.9)
    fx_, fy_ = wx + 11.0, 37.6
    P.trait(fx_, fy_, fx_, 46.0, ENCRE, 2)
    halo(P, fx_, fy_ - 1.0, 7.0, LU2, 0.5)
    P.rect(fx_ - 0.8, fy_ - 2.2, 1.8, 2.2, LU4 if int(p * 8) % 5 else LU3)
    P.poly([(fx_ - 1.4, fy_ - 2.2), (fx_ + 1.6, fy_ - 2.2), (fx_ + 0.1, fy_ - 3.4)], ENCRE)

    # ==================================================================================================== la chambre
    tab.plan("moyen", 0.5)
    fen = m_rect(P, wx, wy, ww, wh)
    # La lumière : presque rien, sauf autour du carreau ; un filet chaud sous la porte.
    dfen = np.hypot(np.clip(np.abs(X - wx - ww / 2) - ww / 2, 0, None), np.clip(np.abs(Y - wy - wh / 2) - wh / 2, 0, None))
    Lm = 0.36 + 0.3 * np.exp(-dfen / 12.0) + lumiere(P, [(8.0, 66.0, 8.0, 0.2)], 0.0)
    mur = ~fen
    lames(P, mur & (Y < SOL), Lm, larg=7.4, graine=810, vertical=True, rampe=R_BOISNUIT, alb=0.66, sens=1, noeuds=0.5)
    # Le rampant du toit : deux chevrons qui descendent, des planches dans l'autre sens.
    for cote, x0 in ((-1, 44.0), (1, 148.0)):
        dist = (X - x0) * cote                                  # ce qu'on s'éloigne du carreau, vers le coin
        ramp = mur & (Y < -6.0 + 0.5 * dist) & (Y < SOL) & (dist > 0)
        lames(P, ramp, Lm * 0.72, larg=4.0, graine=811, vertical=False, rampe=R_BOISNUIT, alb=0.6, noeuds=0, long=30.0)
        chev = mur & (np.abs(Y + 6.0 - 0.5 * dist) < 1.8) & (dist > 0)
        P.rampe(chev, (0.6 - 0.14 * (Y + 6.0 - 0.5 * dist)) * Lm * 1.3, R_BOISNUIT, 0.5)
    # L'embrasure, le cadre, les petits-bois ; un carreau fêlé, recollé d'un papier.
    emb = m_rect(P, wx - 3.4, wy - 3.4, ww + 6.8, wh + 3.4) & ~fen
    P.rampe(emb, 0.5 + 0.3 * (X < wx) + 0.1 * (Y < wy) - 0.2 * (X > wx + ww), R_BOISNUIT, 0.5)
    lisere(P, fen, BM2, 1, 0)
    lisere(P, fen, ENCRE, 0, -1)
    for i in range(1, 4):
        P.rect(wx + ww * i / 4.0 - 0.7, wy, 1.4, wh, R_BOISNUIT[1])
        P.rect(wx + ww * i / 4.0 - 0.7, wy, 0.4, wh, R_BOISNUIT[5])
    for j in range(1, 3):
        P.rect(wx, wy + wh * j / 3.0 - 0.7, ww, 1.4, R_BOISNUIT[1])
        P.rect(wx, wy + wh * j / 3.0 + 0.3, ww, 0.4, R_BOISNUIT[5])
    kx, ky = wx + ww * 0.875, wy + wh * 0.5                     # la fêlure
    for (ax_, ay_) in ((-6.0, -5.0), (5.0, -3.0), (-2.0, 6.0), (6.0, 5.0)):
        P.trait(kx, ky, kx + ax_, ky + ay_, BM3)
    P.poly([(kx - 2.6, ky - 1.6), (kx + 2.4, ky - 2.2), (kx + 2.8, ky + 1.6), (kx - 2.2, ky + 2.0)], R_PAPIER[1])
    for k in range(4):                                          # la buée, et les gouttes qui glissent
        t = (p + k * 0.27) % 1.0
        gx = wx + 9.0 + k * 21.0
        P.trait(gx, wy + 30.0 + 14.0 * t, gx, wy + 31.4 + 14.0 * t, BM2)
    # Le rebord : une planche épaisse, que la lune blanchit. La chandelle soufflée (sa mèche fume), le bol de soupe.
    reb = m_rect(P, wx - 7.0, wy + wh, ww + 14.0, 3.2)
    lames(P, reb, 0.5 + 0.5 * np.exp(-((X - LUNE[0] - 20.0) / 40.0) ** 2), larg=30.0, graine=813, vertical=False, rampe=R_BOISNUIT, alb=0.86, noeuds=0)
    P.rampe(reb & (Y > wy + wh + 2.2), 0.26, R_BOISNUIT, 0.5)
    lisere(P, reb, BM3, 0, -1, cond=pg.fbm(X / 3.0, 0 * X, 2, 814) > 0.3)
    P.rampe(m_rect(P, wx - 6.0, wy + wh + 3.2, ww + 12.0, 1.6), 0.1, R_BOISNUIT, 0.5)              # son ombre
    cx_, cy_ = 100.0, wy + wh
    P.rampe(m_ell(P, cx_, cy_ - 0.4, 3.4, 1.1), 0.4 - 0.3 * (X - cx_) / 3.4, [NU1, GO1, LAITON, BM3], 0.5)
    ci = m_rect(P, cx_ - 1.0, cy_ - 9.0, 2.0, 8.6)
    P.rampe(ci, 0.6 - 0.3 * (X - cx_), [NU3, BM1, BM3, BM4], 0.5)
    P.trait(cx_, cy_ - 9.0, cx_ + 0.2, cy_ - 10.0, ENCRE)
    P.point(cx_ + 0.2, cy_ - 10.2, LU2 if p < 0.25 else LU1)                                      # la mèche rougeoie encore
    fumerolle(P, cx_ + 0.2, cy_ - 11.0, h=14.0, n=3, d=0.0, coul=BM2, force=0.42, large=0.7)
    bx_ = 124.0                                                 # le bol de soupe
    P.rampe(m_ell(P, bx_, cy_ - 1.4, 4.0, 1.9), 0.5 - 0.3 * (X - bx_) / 4.0, R_TOILE, 0.5)
    P.ell(bx_, cy_ - 2.2, 4.0, 1.1, BM3)
    P.ell(bx_, cy_ - 2.2, 3.1, 0.7, LU1)
    P.ell(bx_ - 0.8, cy_ - 2.3, 1.2, 0.3, LU2)
    P.trait(bx_ + 2.0, cy_ - 2.6, bx_ + 6.0, cy_ - 4.6, BM2)
    fumerolle(P, bx_, cy_ - 3.4, h=9.0, n=3, d=0.4, coul=BM3, force=0.36, large=0.8)
    for k in range(3):                                          # une boîte d'allumettes, une allumette brûlée
        P.rect(70.0, cy_ - 2.0 + k * 0.0, 5.0, 2.0, R_TOILE[2])
    P.rect(70.0, cy_ - 2.0, 5.0, 0.5, BM2)
    P.trait(77.0, cy_ - 0.5, 81.0, cy_ - 0.9, BM2)
    P.point(81.2, cy_ - 0.9, ENCRE)

    # ---- Le plancher : la lune y couche le carreau, en long, avec l'ombre des petits-bois.
    sol = Y >= SOL
    tq = (Y - SOL) / 16.0
    xl, xr = wx + 4.0 - 26.0 * tq, wx + ww - 4.0 + 26.0 * tq
    sq = (X - xl) / (xr - xl)
    tache = np.clip(np.minimum(sq, 1 - sq) * 14.0, 0, 1) * np.clip((tq - 0.08) * 12.0, 0, 1)
    for i in range(1, 4):
        tache = tache * (1 - np.clip(1 - np.abs(sq - i / 4.0) / 0.012, 0, 1))
    for j in (0.4, 0.74):
        tache = tache * (1 - np.clip(1 - np.abs(tq - j) / 0.04, 0, 1))
    Ls = 0.26 + 0.66 * tache + lumiere(P, [(6.0, 66.0, 10.0, 0.5)], 0.0) * 0.0
    Lw = np.clip(1 - np.abs(Y - SOL - 1.0 - 0.1 * (X + 6.0)) / (0.6 + 0.12 * (X + 6.0)), 0, 1) * np.clip(1 - (X + 6.0) / 30.0, 0, 1)   # le filet de lumière sous la porte
    plancher(P, sol, Ls, 96.0, 44.0, larg=4.4, graine=815, rampe=R_BOISNUIT, alb=0.8)
    P.rampe(sol & (Lw > 0.25), 0.3 + 0.6 * Lw, R_BOIS[2:], 0.5)
    P.rampe((Y >= SOL - 2.0) & (Y < SOL) & mur, 0.22 + 0 * X, R_BOISNUIT, 0.5)                    # la plinthe

    # ---- À gauche : la porte, sa poignée de laiton, et la chaise coincée dessous.
    porte = m_rect(P, -6.0, 6.0, 20.0, SOL - 6.0)
    lames(P, porte, Lm * 1.25, larg=5.0, graine=816, vertical=True, rampe=R_BOISNUIT, alb=0.62, noeuds=0.3)
    for yy in (16.0, 50.0):                                     # les traverses
        P.rampe(m_rect(P, -6.0, yy, 20.0, 2.6), 0.66 * Lm, R_BOISNUIT, 0.5)
        P.rampe(m_rect(P, -6.0, yy + 2.6, 20.0, 0.5), 0.2 + 0 * X, R_BOISNUIT, 0.5)
    P.rampe(m_rect(P, 14.0, 4.0, 2.0, SOL - 4.0) | m_rect(P, -6.0, 4.0, 22.0, 2.0), 0.5 * Lm * 1.4, R_BOISNUIT, 0.5)        # le chambranle
    P.remplir(m_rect(P, 13.6, 8.0, 0.4, SOL - 8.6) & (pg.fbm(Y / 4.0, 0 * Y, 2, 8161) > 0.4), LU1)       # le couloir éclairé filtre au bord
    P.remplir(m_rect(P, -6.0, SOL - 0.6, 20.0, 0.6), LU3)                                         # et sous la porte
    P.ell(10.6, 38.0, 1.4, 1.4, LAITON)
    P.point(10.2, 37.6, LAITON2)
    P.point(10.6, 41.6, LU3)                                                                      # le trou de la serrure
    # La chaise paillée : le haut du dossier coincé sous la poignée, les pieds arc-boutés sur le plancher.
    R_CH = R_BOISNUIT[2:]
    for (x0, y0, x1, y1, ep_, ton) in ((12.0, 39.4, 22.0, SOL + 3.4, 1.4, 4), (15.0, 42.0, 27.0, 43.4, 1.0, 3), (17.0, 47.0, 28.0, 48.4, 1.0, 3),
                                       (18.6, 53.0, 34.0, 53.0, 1.6, 5), (33.4, 53.0, 36.0, SOL + 4.6, 1.3, 4), (25.6, 40.6, 33.0, 53.0, 1.4, 5),
                                       (20.0, 60.0, 34.6, 60.6, 0.8, 2)):
        P.trait(x0, y0, x1, y1, R_CH[ton], P.ep(ep_))
    P.rampe(P.masque_poly([(18.6, 52.0), (34.0, 52.0), (35.0, 54.4), (19.6, 54.4)]), 0.5 + 0.2 * ((P.XI // 2) % 2), [NU2, GO1, GO2, BM1], 0.5)   # la paille

    # ---- À droite : le lit étroit, son édredon rouge, l'oreiller ; une bouée de liège au mur, qui dévisage.
    lit = P.masque_poly([(150.0, 53.0), (198.0, 53.0), (198.0, SOL + 4.0), (146.0, SOL + 4.0)])
    ua, ub = (X + (Y - 53.0) * 0.9) / 7.0, (X - (Y - 53.0) * 0.9) / 7.0
    gonfle = np.sin((ua % 1.0) * math.pi) * np.sin((ub % 1.0) * math.pi)
    P.rampe(lit, 0.2 + 0.4 * gonfle + 0.22 * np.clip(1 - (X - 146.0) / 34.0, 0, 1) - 0.012 * (Y - 53.0), [R_BOIS[1], R_CUIVRE[0], VI1, R_CUIVRE[1], R_CUIVRE[2], R_CUIVRE[3]], 0.5)
    lisere(P, lit, R_CUIVRE[3], 0, -1, cond=X < 178)
    P.rampe(m_ell(P, 186.0, 52.0, 9.0, 3.4), 0.5 - 0.3 * (X - 186.0) / 9.0 - 0.3 * (Y - 52.0) / 3.4, [NU2, NU4, BM2, BM4], 0.5)       # l'oreiller
    P.rampe(m_rect(P, 146.0, SOL + 4.0, 52.0, 2.0), 0.3 + 0 * X, R_BOISNUIT, 0.5)
    P.rampe(m_rect(P, 147.0, SOL + 6.0, 2.0, 5.0), 0.34 + 0 * X, R_BOISNUIT, 0.5)
    by_ = 20.0
    bo = m_ell(P, 172.0, by_, 7.0, 7.0) & ~m_ell(P, 172.0, by_, 3.6, 3.6)
    ang = np.arctan2(Y - by_, X - 172.0)
    P.rampe(bo, 0.4 - 0.3 * (X - 172.0) / 7.0 + 0.24 * ((np.floor(ang / (math.pi / 4)) % 2) == 0), [NU1, NU2, R_CUIVRE[1], NU4, BM2, BM4], 0.5)
    P.trait(172.0, by_ - 7.0, 172.0, by_ - 10.0, GO1)
    for dx in (-1.4, 1.4):                                      # deux nœuds de corde : des yeux
        P.point(172.0 + dx - 0.2, by_ - 5.4, BM4, 2)
        P.point(172.0 + dx + (0.2 if p < 0.5 else -0.2), by_ - 5.2, ENCRE)
    # Un filet roulé dans l'angle, une ancre ; le baluchon de Pilou au pied du mur.
    for j in range(6):
        P.courbe([(22.0, 6.0 + j * 0.3), (30.0, 12.0 + j * 1.6 + 0.3 * onde(p, 0.1 * j)), (42.0, 2.0 + j * 0.4)], NU2 if j % 2 else NU1, 1)
    bal = m_ell(P, 142.0, SOL - 3.4, 4.4, 3.6)
    P.rampe(bal, 0.4 - 0.3 * (X - 142.0) / 4.4 - 0.2 * (Y - SOL + 3.4) / 3.6, R_TOILE[:5], 0.5)
    P.remplir(bal & ((P.XI + P.YI) % 4 == 0), BM3)
    P.poly([(140.8, SOL - 6.6), (143.2, SOL - 6.6), (142.0, SOL - 8.4)], R_TOILE[3])
    pg.souris(P, 44.0, SOL + 2.0, sens=-1, coul=NU3)

    # ================================================================================================== premier plan
    tab.plan("premier", 1.0)
    # Une poutre tout près, en haut ; un pan de rideau à gauche ; le pied du lit à droite ; à contre-jour.
    pou = Y < -11.0 + 0.5 * np.sin(X / 30.0)
    lames(P, pou, 0.2 + 0.2 * np.exp(-((X - 96.0) / 50.0) ** 2), larg=30.0, graine=817, vertical=False, rampe=R_BOISNUIT, alb=0.6, noeuds=0.9)
    lisere(P, pou, R_BOISNUIT[4], 0, 1, cond=np.abs(X - 96.0) < 60)
    rid = (X < 2.0 + 2.4 * np.sin(Y / 11.0) + 0.3 * onde(p, 0.2) * (Y + 16.0) / 90.0)
    pli = 0.5 + 0.5 * np.sin(X * 2.4 + 0.5 * np.sin(Y / 6.0))
    P.rampe(rid, 0.1 + 0.2 * pli, [ENCRE, NU0, NU1, NU2], 0.5)
    lisere(P, rid, NU3, 1, 0)
    pied = m_rect(P, 187.0, 40.0, 4.0, 40.0) | m_ell(P, 189.0, 39.0, 3.2, 3.2)
    P.rampe(pied, 0.16 + 0.2 * (X < 188.4), [ENCRE, NU0, NU1, NU2, NU3], 0.5)
    lisere(P, pied, NU4, -1, 0)
    P.rampe(Y > 78.6, 0.12 + 0 * X, R_BOISNUIT, 0.5)
    for i in range(22):                                         # la poussière dans le rai de lune
        if (p + hz(i, 1, 818)) % 1.0 < 0.6:
            P.point(60.0 + 76.0 * hz(i, 2, 818) + 0.8 * onde(p, hz(i, 4, 818)), 50.0 + 26.0 * hz(i, 3, 818) + 0.5 * onde(p, 0.25 + hz(i, 5, 818)), BM3 if i % 2 else BM4)
    pg.papillon_de_nuit(P, LUNE[0] + 30.0, 20.0, 4.0, coul=BM4)


# =====================================================================================================================
# Le Passe-Pied : 6 h 10, marée basse. La mer est partie et a laissé un chemin de pierres plates, de flaques et de goémon
# qui brille, quatre cents mètres jusqu'au rocher de la Dent-Creuse (la clé, en haut à droite). La brume est rose. La
# vase est un miroir. Au départ, l'écriteau peint à la main : pierres claires, pied sûr ; pierres vertes, bain sûr.
# Repères de la scène : sol y = 78 ; ronds dans l'eau en (30, 64) et (150, 62) ; le crabe passe en bas.
# =====================================================================================================================
ROSE1, ROSE2, ROSE3 = cs("#c99aa8", "#e8b9b4", "#f6d6c8")
R_VASE = cs("#1d2a44", "#2c3c5c", "#44567a", "#65789c", "#8ea0bf", "#b9c6dc", "#dfe4ee", "#f6e6d2")
R_GALET = cs("#3b4660", "#5c6884", "#8a93a8", "#b9bcc6", "#dcd8d2", "#f3ead8", "#fff6e2")
R_ALGUE = cs("#0f2436", "#17384a", "#245566", "#3d7a84", "#6aa8a4", "#b7d8c8")


@decor("phare-eteint", "passe-pied", soleil=(60.0, 30.0), tons=AUBE, nom="Le Passe-Pied", matiere=True)
def passe_pied(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tout = np.ones(X.shape, dtype=bool)
    HOR = 40.0
    SOLEIL = (60.0, 30.0)

    # ============================================================================================================ le ciel
    tab.plan("ciel", 0.0)
    P.horizon, P.ciel_haut, P.halo = HOR, 0.2, 0.3
    vc = pg.valeur_ciel(P, X, Y)
    P.rampe(tout, 0.1 + 0.88 * vc, T.CIEL, 0.75)
    rose = np.exp(-((Y - HOR + 8.0) / 9.0) ** 2) * (0.6 + 0.6 * pg.fbm(X / 30.0, Y / 4.0, 3, 830))
    P.rampe(rose > 0.42, (rose - 0.42) * 2.4 + 0.2 * np.exp(-((X - SOLEIL[0]) / 40.0) ** 2), [ROSE1, ROSE2, ROSE3, T.CIEL[11]], 0.6)
    ds = np.hypot(X - SOLEIL[0], Y - SOLEIL[1])
    P.rampe(ds < 9.0, 0.3 + 0.7 * np.clip(1 - ds / 9.0, 0, 1), [ROSE3, T.CIEL[11], BLANC], 0.6)
    P.remplir(ds < 3.6, BLANC)
    tab.plan("nuages", 0.08)

    def nappe(y, epais, graine, tons, seuil=0.62, zone=None, pas=17.0):
        def dens(yy):
            return (0.4 + pg.fbm((X + 1.4 * onde(p, 0.013 * graine)) / pas, yy / 2.4, 3, graine)) * np.exp(-((yy - y - 1.0 * np.sin(X / 19.0 + graine)) / epais) ** 2) - seuil
        d = dens(Y)
        prox = np.exp(-(np.hypot(X - SOLEIL[0], (Y - SOLEIL[1]) * 1.4) / 60.0) ** 2)
        m = d > 0
        if zone is not None:
            m &= zone
        P.rampe(m, 0.2 + 1.5 * d + 1.8 * (d - dens(Y - 1.0)) + 0.4 * prox, tons, 0.6)

    nappe(-8.0, 4.0, 831, [T.CIEL[2], T.CIEL[4], T.CIEL[6], ROSE2, ROSE3], 0.6, pas=30.0)
    nappe(6.0, 3.0, 832, [T.CIEL[4], T.CIEL[6], ROSE2, ROSE3, T.CIEL[11]], 0.66, pas=26.0)
    nappe(19.0, 2.4, 833, [T.CIEL[6], ROSE2, ROSE3, T.CIEL[11]], 0.7, pas=24.0)
    pg.oiseaux(P, 104.0, 8.0, n=5, coul=T.CIEL[1])

    # ======================================================================================================== les lointains
    tab.plan("lointains", 0.2)
    # La Dent-Creuse dans la brume rose : pâle, plus nette vers le haut ; la Mâchoire découverte à sa gauche.
    phare(P, 146.0, HOR - 3.4, 35.0, T.CIEL[3], T.CIEL[6], rocher=False)
    fr_ = lambda x: HOR - 0.2 - 4.6 * np.exp(-((x - 146.0) / 9.0) ** 2) - 1.6 * (pg.fbm(x / 1.8, 0 * x + 0.2, 3, 8341) - 0.5) + 0.02 * (x - 146.0) ** 2
    rocher = (Y > fr_(X)) & (Y < HOR + 0.6) & (np.abs(X - 146.0) < 15)
    P.rampe(rocher, 0.3 + 0.5 * (pg.fbm(X / 2.0 + 0.4 * Y, Y / 1.4, 3, 8342) - 0.4) - 0.2 * (X - 146.0) / 15.0, [T.CIEL[2], T.CIEL[3], T.CIEL[4], T.CIEL[6]], 0.5)
    lisere(P, rocher, ROSE3, 0, -1, cond=X < 148)
    lisere(P, P.a == T.CIEL[3], ROSE3, -1, 0, cond=(pg.fbm(Y / 3.0, 0 * Y, 2, 834) > 0.4) & (Y < HOR - 4))    # le soleil rase son flanc
    hm = 10.0 * np.clip(pg.fbm(X / 2.0, 0 * X + 0.7, 3, 835) - 0.4, 0, 1) * np.clip(1 - np.abs(X - 108.0) / 18.0, 0, 1) ** 0.5
    mach = (Y > HOR + 0.2 - hm) & (Y < HOR + 0.6) & (hm > 0.3)
    P.remplir(mach, T.CIEL[4])
    lisere(P, mach, ROSE2, -1, 0)
    f1 = lambda x: HOR - 0.4 - 3.4 * np.clip((x - 168.0) / 30.0, 0, 1) ** 0.8 - 1.0 * pg.fbm(x / 7.0, 0 * x + 0.5, 3, 836)   # une pointe, à droite
    P.remplir((Y > f1(X)) & (Y < HOR + 0.4) & (X > 166), T.CIEL[5])
    nappe(HOR - 1.0, 1.5, 837, [T.CIEL[7], T.CIEL[9], ROSE3, T.CIEL[11]], 0.6, zone=(X < 126) | (X > 166))
    nappe(HOR - 8.0, 1.6, 838, [T.CIEL[8], ROSE3, T.CIEL[11]], 0.72, zone=X > 90)

    # ================================================================================================= l'estran découvert
    tab.plan("moyen", 0.5)
    # La vase mouillée : le miroir du ciel. Puis les bancs de sable ridé, les flaques, la mer restée au loin.
    pg.miroir(P, tab.derriere(), HOR + 0.6, fonce=(74.0, 20.0), eclats=0.55, rides=0.03, graine=839,
              ronds=((30.0, 64.0, 0.0), (150.0, 62.0, 0.5), (96.0, 50.0, 0.3)))
    estran = Y > HOR + 0.6
    dy = np.maximum(Y - HOR, 0.3)
    z = 60.0 / dy
    banc = pg.fbm(X / (4.0 + 0.5 * dy), z * 1.6, 3, 840) + 0.012 * (Y - HOR) - 0.1 * np.exp(-((X - SOLEIL[0] - 0.8 * (Y - HOR)) / (5.0 + 0.4 * dy)) ** 2)
    sable = estran & (banc > 0.52)
    ride = np.sin(z * 30.0 + 4.0 * pg.fbm(X / 20.0, z, 2, 841))
    lum_s = 0.5 + 0.3 * np.exp(-((X - SOLEIL[0] - 0.8 * (Y - HOR)) / 40.0) ** 2) - 0.006 * (Y - HOR)
    P.rampe(sable, (0.6 + 0.12 * ride + 0.5 * (banc - 0.52)) * lum_s * 1.25, R_VASE, 0.5)
    lisere(P, sable, R_VASE[1], 0, 1)                                                              # le bord humide, plus sombre
    lisere(P, sable, R_VASE[7], 0, -1, cond=pg.fbm(X / 3.0, Y, 2, 842) > 0.45)
    for i in range(6):                                          # la mer, qui s'est retirée : un liseré d'écume au loin
        t = (p + i / 6.0) % 1.0
        ex = 10.0 + i * 31.0 + 6.0 * math.sin(i * 1.7)
        P.trait(ex - 6.0 - 2 * t, HOR + 1.2 + (i % 2) * 0.6, ex + 7.0 + 2 * t, HOR + 1.2 + (i % 2) * 0.6, BLANC if t < 0.5 else T.CIEL[9])
    nappe(HOR + 3.4, 1.2, 843, [T.CIEL[8], ROSE3, T.CIEL[11]], 0.72)                                # la brume s'assied sur l'eau

    # ---- Les balises du chenal, une barque échouée sur le flanc, des goélands qui fouillent la vase.
    for i, (bx_, by_, h) in enumerate(((120.0, 46.6, 3.0), (104.0, 49.0, 4.4), (132.0, 52.0, 5.6), (80.0, 55.0, 7.0), (168.0, 58.0, 9.0))):
        P.trait(bx_, by_, bx_ + 0.2 * onde(p, 0.2 * i), by_ - h, T.CIEL[0], 1 if h < 5 else 2)
        P.rect(bx_ - 0.6, by_ - h - 0.9, 1.4, 1.0, LU2 if i % 2 else R_VASE[0])
        for k in range(int(h)):                                 # son reflet, brisé
            if k % 2 == 0:
                P.point(bx_ + 0.3 * math.sin(k + 6.283 * p), by_ + 0.6 + k * 0.7, R_VASE[1])
    qx, qy = 28.0, 56.0                                         # la barque
    cq = P.masque_poly([(qx - 12.0, qy - 2.2), (qx + 12.6, qy - 4.6), (qx + 10.0, qy + 0.6), (qx - 9.0, qy + 1.6)])
    P.rampe(cq, 0.3 + 0.3 * (Y - qy + 4.0) / -5.0 + 0.36 + 0.14 * (pg.fbm(X / 1.4, Y / 0.8, 2, 844) - 0.5), R_TOILE, 0.5)
    lisere(P, cq, ROSE3, 0, -1)
    lisere(P, cq, R_VASE[0], 0, 1)
    P.remplir(cq & (np.abs(Y - qy + 1.0 + 0.1 * (X - qx)) < 0.25), R_TOILE[1])
    P.ell(qx, qy + 1.9, 13.0, 1.0, R_VASE[1])                                                      # son ombre dans la vase
    P.trait(qx + 12.0, qy - 4.4, qx + 22.0, qy + 1.0, GO2)                                         # son amarre, molle
    P.rect(qx + 21.6, qy + 0.4, 1.2, 1.2, R_VASE[0])
    for i, (gx, gy, s_) in enumerate(((66.0, 52.6, 1), (158.0, 55.0, -1))):
        goeland(P, gx, gy, sens=s_, pose=True)
        P.ell(gx, gy + 0.5, 2.6, 0.5, R_VASE[1])

    # ---- Le chemin : des pierres plates qui zigzaguent jusqu'au rocher ; les claires, et les vertes de goémon.
    chemin = [(34.0, 79.0), (50.0, 74.0), (38.0, 69.0), (60.0, 65.0), (84.0, 63.4), (72.0, 59.4), (96.0, 56.6), (116.0, 54.6), (106.0, 51.6),
              (124.0, 49.2), (136.0, 47.2), (130.0, 45.4), (140.0, 43.6), (144.0, 42.0)]
    pierres = []
    for a in range(len(chemin) - 1):
        (x0, y0), (x1, y1) = chemin[a], chemin[a + 1]
        n = max(1, int(math.hypot(x1 - x0, (y1 - y0) * 3.0) / (2.6 + 0.3 * (y0 - HOR))))
        for k in range(n):
            u = (k + 0.5) / n
            pierres.append((x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, a * 31 + k))
    pierres.sort(key=lambda q: q[1])
    for (sx, sy, g) in pierres:
        k = (sy - HOR) / 38.0                                   # la taille, avec la distance
        rx, ry = (1.0 + 5.4 * k) * (0.8 + 0.4 * hz(g, 1, 845)), (0.45 + 1.7 * k) * (0.8 + 0.4 * hz(g, 2, 845))
        sx, sy = sx + (hz(g, 3, 845) - 0.5) * rx * 0.8, sy + (hz(g, 4, 845) - 0.5) * ry
        verte = hz(g, 5, 845) < 0.22
        P.ell(sx + rx * 0.3, sy + ry * 0.7, rx * 1.1, ry * 0.8, R_VASE[0])                           # l'ombre et le reflet
        m = m_ell(P, sx, sy, rx, ry) | (m_ell(P, sx, sy + ry * 0.5, rx, ry) & (Y > sy))
        dessus = m_ell(P, sx, sy, rx, ry)
        v = 0.6 - 0.26 * (X - sx) / rx - 0.2 * (Y - sy) / ry + 0.16 * (pg.fbm(X / 1.3, Y / 0.8, 2, 846) - 0.5) + 0.1 * hz(g, 6, 845)
        P.rampe(m & ~dessus, 0.16 - 0.1 * (X - sx) / rx, R_GALET, 0.5)                                # le chant de la pierre
        P.rampe(dessus, v, R_ALGUE if verte else R_GALET, 0.5)
        if k > 0.25:
            lisere(P, dessus, R_ALGUE[5] if verte else R_GALET[6], -1, 0, cond=Y < sy)
            if hz(g, 7, 845) < 0.4 and not verte:                 # une touffe de goémon accrochée
                for q in range(4):
                    a_ = 0.3 + q * 0.8
                    P.trait(sx + rx * 0.6, sy + ry * 0.4, sx + rx * 0.6 + 2.2 * k * math.cos(a_) + 0.3 * onde(p, 0.1 * q), sy + ry * 0.4 + 1.6 * k * math.sin(a_), R_ALGUE[1 + q % 3])
            if hz(g, 8, 845) < 0.3 and int(p * 8 + g) % 6 == 0:
                P.point(sx - rx * 0.3, sy - ry * 0.3, BLANC)      # l'eau qui luit dessus
    # Les tas de goémon luisant, les flaques bordées de sable, un ruisselet qui file vers la mer.
    for i, (gx, gy, r) in enumerate(((16.0, 66.0, 7.0), (104.0, 68.0, 8.0), (140.0, 60.0, 5.0), (176.0, 68.0, 8.0), (70.0, 74.0, 6.0))):
        tas = m_ell(P, gx, gy, r, r * 0.22) & (pg.fbm(X / 1.6, Y / 0.6, 2, 847 + i) > 0.46)
        P.rampe(tas, 0.06 + 0.6 * (pg.fbm(X / 1.0, Y / 0.6, 2, 848 + i) - 0.3) - 0.16 * (Y - gy) / (r * 0.26), [R_VASE[0]] + R_ALGUE[:4], 0.5)
        for q in range(5):
            if (q + int(p * 8) + i) % 4 == 0:
                P.point(gx + (hz(q, i, 849) - 0.5) * r * 1.4, gy + (hz(q, i + 9, 849) - 0.5) * r * 0.3, BLANC)

    # ================================================================================================== premier plan
    tab.plan("premier", 1.0)
    # À droite, l'écriteau peint à la main, et dessous, d'une autre main, une planchette. Un goéland dessus.
    px_ = 181.0
    P.rampe(m_rect(P, px_ - 1.0, 34.0, 2.0, 46.0), 0.3 + 0.4 * (X < px_ - 0.2) + 0.1 * (pg.fbm(X, Y / 6.0, 2, 850) - 0.5), R_BOIS, 0.5)
    pn = P.masque_poly([(167.0, 37.0), (195.0, 35.8), (195.6, 47.4), (167.4, 48.4)])
    lames(P, pn, 0.86 + 0 * X, larg=3.9, graine=851, vertical=False, rampe=R_PLATRE, alb=0.8, noeuds=0.4)
    lisere(P, pn, R_PLATRE[2], 0, 1)
    lisere(P, pn, ROSE3, -1, 0)
    P.rampe(m_ell(P, 172.6, 40.6, 3.0, 1.4), 0.7, R_GALET, 0.5)                                    # pierre claire : le pied
    P.rect(177.6, 39.6, 1.6, 2.4, R_NUIT[2])
    P.rect(179.0, 39.2, 0.6, 0.6, R_NUIT[2])
    P.rampe(m_ell(P, 172.6, 45.0, 3.0, 1.4), 0.6, R_ALGUE, 0.5)                                    # pierre verte : la vague
    P.courbe([(177.0, 45.4), (178.6, 44.2), (180.2, 45.4), (181.8, 44.2), (183.4, 45.4)], R_NUIT[2], 1)
    P.trait(186.0, 38.6, 193.0, 46.0, LU2, 2)                                                      # hors des pierres : une croix
    P.trait(193.0, 38.6, 186.0, 46.0, LU2, 2)
    pn2 = P.masque_poly([(170.0, 51.0), (192.0, 50.2), (192.4, 55.6), (170.4, 56.6)])
    lames(P, pn2, 0.8 + 0 * X, larg=6.0, graine=852, vertical=False, rampe=R_BOIS, alb=0.7, noeuds=0)
    P.ell(176.0, 53.6, 2.0, 2.0, R_PLATRE[7])                                                      # « une heure, pas plus » : un cadran
    P.trait(176.0, 53.6, 176.0, 52.2, R_NUIT[1])
    P.trait(176.0, 53.6, 177.2, 53.6, R_NUIT[1])
    P.trait(181.0, 53.4, 189.0, 53.0, R_PLATRE[7])
    goeland(P, 186.0, 35.4, sens=-1, pose=True)
    # En bas : les rochers du départ, noirs de goémon, des berniques, une flaque où dort une étoile de mer ; à gauche,
    # une chaîne et son anneau rouillé.
    fr = lambda x: 76.6 + 1.6 * np.sin(x / 13.0) - 3.4 * np.exp(-((x - 8.0) / 12.0) ** 2) - 4.0 * np.exp(-((x - 186.0) / 14.0) ** 2) + 1.2 * (pg.fbm(x / 3.0, 0 * x, 3, 853) - 0.5)
    roc = Y > fr(X)
    P.rampe(roc, 0.3 + 0.5 * (pg.fbm(X / 3.0 + 0.3 * Y, Y / 1.6, 3, 854) - 0.4) - 0.04 * (Y - fr(X)), [R_ALGUE[0], R_VASE[0], R_ALGUE[1], R_VASE[1], R_VASE[2], R_VASE[3]], 0.5)
    lisere(P, roc, ROSE2, 0, -1, cond=pg.fbm(X / 2.4, 0 * X, 2, 855) > 0.42)
    for i in range(16):                                         # le goémon qui pend aux rochers
        x = 198.0 * hz(i, 1, 856) - 3.0
        y0 = float(fr(np.array([x]))[0])
        P.courbe([(x, y0), (x + 0.8 * onde(p, hz(i, 2, 856)), y0 + 1.6), (x + 1.4 * onde(p, hz(i, 2, 856)), y0 + 3.2)], R_ALGUE[2 + i % 3], 1 if i % 3 else 2)
    for i in range(10):                                         # les berniques
        x = 4.0 + 186.0 * hz(i, 3, 857)
        y0 = float(fr(np.array([x]))[0]) + 1.4 + 1.2 * hz(i, 4, 857)
        P.poly([(x - 0.9, y0), (x + 0.9, y0), (x, y0 - 0.9)], R_GALET[3])
        P.point(x - 0.2, y0 - 0.7, R_GALET[6])
    fl = m_ell(P, 118.0, 78.6, 9.0, 1.3)
    P.rampe(fl, 0.5 + 0.3 * (pg.fbm(X / 3.0 + 0.3 * onde(p), Y, 2, 858) - 0.5), [R_VASE[2], R_VASE[4], ROSE2, ROSE3], 0.5)
    for k in range(5):                                          # l'étoile de mer
        a_ = k * 2 * math.pi / 5 - 1.2
        P.trait(114.0, 78.6, 114.0 + 2.0 * math.cos(a_), 78.6 + 0.9 * math.sin(a_), LU2, 2)
    P.point(114.0, 78.6, LU4)
    for k in range(7):                                          # la chaîne
        P.ell(4.0 + k * 2.0, 71.4 + 0.6 * math.sin(k * 0.9) + k * 0.4, 1.0, 0.6, R_CUIVRE[1] if k % 2 else R_VASE[0])
    P.ell(2.6, 70.6, 1.8, 1.6, R_CUIVRE[1])
    P.ell(2.6, 70.6, 0.9, 0.8, R_VASE[0])


# =====================================================================================================================
# Au pied de la Dent-Creuse : le bas de la tour, vue de tout près, énorme, grise, froide. La lune la prend par la gauche
# et laisse son flanc droit dans le noir. La lourde porte de chêne clouté, sans poignée (la clé) : barrée de
# l'intérieur, la serrure bouchée à la cire. Les marches mouillées, les traces de goudron, la petite porte du charbon.
# La mer remonte autour du rocher ; au loin, à gauche, les lampes de Trébrume. Le rocher est le sol (y = 68).
# =====================================================================================================================
@decor("phare-eteint", "pied-du-phare", soleil=(24.0, 4.0), tons=PHARE, nom="Au pied de la Dent-Creuse", matiere=True)
def pied_du_phare(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tout = np.ones(X.shape, dtype=bool)
    LUNE = (24.0, 4.0)
    HOR, SOL = 50.0, 64.0
    TX = 100.0                                                  # l'axe de la tour

    # ============================================================================================================ le ciel
    tab.plan("ciel", 0.0)
    P.horizon, P.ciel_haut, P.halo = HOR, 0.06, 0.34
    vc = pg.valeur_ciel(P, X, Y)
    P.rampe(tout, 0.03 + 0.62 * vc, T.CIEL, 0.75)
    for i in range(40):
        ex, ey = 198.0 * hz(i, 1, 860) - 3.0, -15.0 + 34.0 * hz(i, 2, 860) ** 1.5
        if math.hypot(ex - LUNE[0], ey - LUNE[1]) > 20.0 and (p + hz(i, 3, 860)) % 1.0 < 0.7:
            P.point(ex, ey, T.CIEL[8] if hz(i, 4, 860) < 0.4 else T.CIEL[5])
    dl = np.hypot(X - LUNE[0], Y - LUNE[1])
    P.rampe(dl < 13.0, 0.3 + 0.7 * np.clip(1 - dl / 13.0, 0, 1) ** 1.5 + 0.5 * vc, T.CIEL[3:10], 0.6)
    P.remplir(dl < 4.4, T.CIEL[10])
    P.remplir(dl < 3.7, T.SOL)
    P.remplir((dl < 3.7) & (pg.fbm(X / 1.8, Y / 1.8, 2, 861) > 0.6), T.CIEL[10])
    tab.plan("nuages", 0.08)

    def nappe(y, epais, graine, tons, seuil=0.62, zone=None, pas=17.0):
        def dens(yy):
            return (0.4 + pg.fbm((X + 1.4 * onde(p, 0.013 * graine)) / pas, yy / 2.4, 3, graine)) * np.exp(-((yy - y - 1.0 * np.sin(X / 19.0 + graine)) / epais) ** 2) - seuil
        d = dens(Y)
        prox = np.exp(-(np.hypot(X - LUNE[0], (Y - LUNE[1]) * 1.4) / 60.0) ** 2)
        m = d > 0
        if zone is not None:
            m &= zone
        P.rampe(m, 0.2 + 1.5 * d + 1.6 * (d - dens(Y + 1.0)) + 0.45 * prox, tons, 0.6)

    nappe(-9.0, 4.0, 862, T.CIEL[1:7], 0.6, pas=30.0)
    nappe(8.0, 2.6, 863, T.CIEL[3:9], 0.68, pas=26.0)
    nappe(24.0, 3.0, 864, T.CIEL[3:8], 0.64, pas=24.0)
    nappe(38.0, 2.4, 865, T.CIEL[4:9], 0.62, pas=22.0)

    # ======================================================================================================== les lointains
    tab.plan("lointains", 0.2)
    # Trébrume, là-bas : chaque fenêtre a sa lampe. Un fil de lumières au ras de l'eau.
    f1 = lambda x: HOR - 0.6 - 3.6 * np.clip((60 - x) / 60.0, 0, 1) ** 0.7 - 1.2 * pg.fbm(x / 6.0, 0 * x + 0.5, 3, 866)
    cote_ = (Y > f1(X)) & (Y < HOR + 0.4) & (X < 62)
    P.remplir(cote_, T.CIEL[3])
    for i in range(14):
        lx_ = 2.0 + 56.0 * hz(i, 1, 867)
        ly_ = float(f1(np.array([lx_]))[0]) + 1.0 + 1.4 * hz(i, 2, 867)
        if ly_ < HOR and (p + hz(i, 3, 867)) % 1.0 < 0.9:
            P.point(lx_, ly_, LU4 if hz(i, 4, 867) < 0.5 else LU3)
    nappe(HOR - 1.4, 1.6, 868, T.CIEL[5:10], 0.64)
    # La mer : la houle longue, le chemin de lune, les lampes qui s'y allongent.
    pg.miroir(P, tab.derriere(), HOR, fonce=(58.0, 10.0), eclats=0.9, rides=0.1, graine=869)
    for i in range(14):
        lx_ = 2.0 + 56.0 * hz(i, 1, 867)
        if hz(i, 5, 867) < 0.6:
            for j in range(4):
                if (j + int(p * 8) + i) % 3:
                    P.trait(lx_ - 0.6, HOR + 1.0 + j * 1.3, lx_ + 0.6, HOR + 1.0 + j * 1.3, LU2 if j < 2 else LU1)
    nappe(HOR + 4.0, 1.2, 870, T.CIEL[4:8], 0.72)

    # ====================================================================================================== la tour, le roc
    tab.plan("moyen", 0.5)
    # ---- Le rocher : une échine de granit noir, mouillée, que la lune ourle ; l'écume qui remonte de chaque côté.
    fr = lambda x: SOL - 0.4 + 7.0 * np.clip((np.abs(x - TX) - 52.0) / 44.0, 0, 1) ** 1.5 + 0.9 * (pg.fbm(x / 4.0, 0 * x + 0.3, 3, 871) - 0.5) * np.clip((np.abs(x - TX) - 30.0) / 20.0, 0, 1)
    roc = Y > fr(X)
    pan = pg.fbm(X / 5.0 + 0.5 * Y, Y / 2.0, 3, 872)
    Lr = 0.5 + 0.3 * np.exp(-((X - 40.0) / 50.0) ** 2) - 0.014 * (Y - SOL)
    Lr = Lr * (1 - 0.5 * np.clip(1.2 - np.hypot((X - TX - 26.0) / 44.0, (Y - SOL - 3.0) / 5.0), 0, 1))    # l'ombre de la tour, vers la droite
    P.rampe(roc, (0.4 + 0.66 * (pan - 0.4) + 0.1 * (pg.fbm(X / 0.9, Y / 0.9, 2, 873) - 0.5)) * Lr * 1.5, R_FROID, 0.5)
    fiss = roc & (np.abs(pg.fbm(X / 9.0, Y / 3.0, 3, 874) - 0.5) < 0.012)
    P.a[fiss] = ENCRE
    lisere(P, roc, BM2, 0, -1, cond=(pg.fbm(X / 2.6, 0 * X, 2, 875) > 0.36) & (X < TX + 40))
    for cote, x0 in ((-1, 26.0), (1, 174.0)):                     # l'écume
        for i in range(5):
            t = (p + i / 5.0 + 0.1 * cote) % 1.0
            ex = x0 + cote * (i * 5.0 - 6.0 * t)
            ey = float(fr(np.array([ex]))[0]) - 0.2
            P.trait(ex - 2.4, ey, ex + 2.4, ey, BM4 if t < 0.5 else BM2)
            if t < 0.3:
                P.point(ex + cote * 1.0, ey - 1.0 - 3.0 * t, BLANC)
    # ---- La tour : un cylindre de granit, légèrement fruité. Chaque pierre a son ton ; la lune vient de la gauche.
    def demi(yy):
        return 36.0 - 0.09 * (SOL - yy)
    tour = (np.abs(X - TX) < demi(Y)) & (Y < SOL + 0.4)
    nx = (X - TX) / demi(Y)
    Lt = 0.2 + 0.9 * np.clip(0.55 - 0.9 * nx, 0, 1) ** 1.3 + 0.1 * np.clip(nx - 0.86, 0, 1) * 6.0          # la lune, puis un rien de ciel sur l'arête droite
    Lt = Lt * (0.86 + 0.14 * np.clip((Y + 16.0) / 30.0, 0, 1))
    # les pierres suivent la courbe : elles se resserrent vers les bords
    ang = np.arcsin(np.clip(nx, -0.999, 0.999))
    r = np.floor((Y - 3.0) / 6.2)
    wv = 0.34 * (0.72 + 0.56 * hz(r, 2, 876))
    aa = ang + 3.0 * hz(r, 1, 876)
    s_ = np.floor(aa / wv)
    du0, dv0 = (aa - s_ * wv) * demi(Y) * np.cos(ang), (Y - 3.0) - r * 6.2
    du1, dv1 = (wv - (aa - s_ * wv)) * demi(Y) * np.cos(ang), 6.2 - dv0
    ton = 0.76 + 0.48 * hz(s_, r, 877)
    grain = pg.fbm(X / 1.1, Y / 1.1, 2, 878) - 0.5
    joint = (du0 < 0.42) | (dv0 < 0.42)
    bev = 0.2 * ((du0 < 1.26) & ~joint) * 1.0 - 0.2 * (du1 < 0.84) + 0.16 * ((dv0 < 1.26) & ~joint) - 0.16 * (dv1 < 0.84)
    coul_ = pg.fbm(X / 2.4, Y / 26.0, 2, 879)                    # les coulures de pluie et de sel
    v = 0.6 * (ton + 0.3 * grain) + bev - 0.14 * np.clip(coul_ - 0.6, 0, 1) * 3.0
    v = np.where(joint, 0.24, v)
    P.rampe(tour, v * Lt * 1.25, R_FROID, 0.5)
    lichen = tour & (pg.fbm(X / 3.0, Y / 3.0, 3, 880) > 0.68) & (nx < 0.2)                         # du lichen doré, côté lune
    P.rampe(lichen, 0.5 + 0.4 * (pg.fbm(X / 1.0, Y / 1.0, 2, 881) - 0.5), [GO1, GO2, LAITON], 0.5)
    soub = tour & (Y > SOL - 5.0)                                                                 # le soubassement, noir de goémon
    P.rampe(soub, v * Lt * 0.8 - 0.1 * (Y - SOL + 5.0) / 5.0, [ENCRE, R_GRANIT[0], T.S0, R_GRANIT[1], T.S1, R_GRANIT[2]], 0.5)
    band = tour & (np.abs(Y - 2.0) < 1.5)                                                          # un bandeau de pierre en saillie
    P.rampe(band, (0.8 - 0.3 * (Y - 2.0)) * Lt * 1.3, R_FROID, 0.5)
    P.rampe(tour & (Y >= 3.5) & (Y < 4.6), 0.2 * Lt, R_FROID, 0.5)
    # Deux meurtrières ; à celle de gauche, un rideau qui bouge (la brume joue des tours).
    for i, (mx_, my_) in enumerate(((TX - 21.0, -8.0), (TX + 19.0, 14.0))):
        mm = m_rect(P, mx_ - 1.6, my_, 3.2, 9.0) | m_ell(P, mx_, my_, 1.6, 1.6)
        P.remplir(mm, ENCRE)
        lisere(P, mm, BM1 if i == 0 else R_GRANIT[2], 1, 0)
        P.rampe(m_rect(P, mx_ - 2.6, my_ + 9.0, 5.2, 1.0), 0.7 * Lt, R_FROID, 0.5)
        if i == 0:
            dx = 0.5 * max(0.0, onde(p, 0.2))
            P.rect(mx_ - 1.4, my_ + 0.6, 1.2 + dx, 8.0, NU2)
            P.rect(mx_ - 1.4, my_ + 0.6, 0.4, 8.0, NU3)
    # ---- La porte (la clé) : un arc de granit, des vantaux de chêne, des pentures de fer, des clous, pas de poignée.
    px0, px1, py0 = TX - 15.0, TX + 15.0, 28.0
    arc = (m_rect(P, px0 - 4.0, py0, px1 - px0 + 8.0, SOL - py0) | m_ell(P, TX, py0, 19.0, 15.0)) & (Y < SOL)
    ouv = (m_rect(P, px0, py0, px1 - px0, SOL - py0) | m_ell(P, TX, py0, 15.0, 11.4)) & (Y < SOL)
    ang_a = np.arctan2(Y - py0, X - TX)
    clav = np.floor(ang_a / (math.pi / 11.0))
    vous = arc & ~ouv
    P.rampe(vous, (0.56 + 0.3 * hz(clav, 0, 882) * (Y < py0) + 0.24 * hz(np.floor(Y / 5.0), 1, 882) * (Y >= py0)) * Lt * 1.5 + 0.1, R_FROID, 0.5)
    P.remplir(vous & (Y < py0) & (((ang_a / (math.pi / 11.0)) % 1.0) < 0.07), R_GRANIT[0])
    P.remplir(vous & (Y >= py0) & ((Y % 5.0) < 0.42), R_GRANIT[0])
    lisere(P, ouv, ENCRE, 0, -1)
    lisere(P, ouv, ENCRE, -1, 0)
    lisere(P, arc, BM2, 0, -1, cond=X < TX)
    P.remplir(ouv, ENCRE)
    bois = ouv & (X > px0 + 1.0) & (X < px1 - 0.6) & ((Y > py0 - 10.4 + 0.02 * (X - TX) ** 2 + 0.0 * Y))
    Ld = 0.34 + 0.3 * np.clip((TX + 16.0 - X) / 32.0, 0, 1)                                         # l'embrasure ombre le haut et la gauche
    Ld = Ld * (0.5 + 0.5 * np.clip((Y - py0 + 10.0) / 12.0, 0, 1)) * (0.6 + 0.4 * np.clip((X - px0) / 5.0, 0, 1))
    lames(P, bois, Ld * 1.05, larg=5.0, graine=883, vertical=True, alb=0.6, sens=-1, noeuds=0.5)
    P.remplir(bois & (np.abs(X - TX) < 0.3), ENCRE)                                                # la jointure des deux vantaux
    for yy in (25.0, 41.0, 56.0):                                                                 # les pentures
        pen = bois & (np.abs(Y - yy) < 1.3)
        P.rampe(pen, (0.36 + 0.2 * (Y < yy)) * (0.5 + Ld), [ENCRE, R_GRANIT[0], R_GRANIT[1], R_GRANIT[2], GR3], 0.5)
        for cx_ in np.arange(px0 + 3.0, px1 - 1.0, 4.0):
            P.point(cx_, yy - 0.3, GR4 if cx_ < TX else GR3)
            P.point(cx_ + 0.4, yy + 0.1, ENCRE)
    for i in range(34):                                                                           # les clous, en quinconce
        cx_ = px0 + 2.6 + 25.0 * hz(i, 1, 884)
        cy_ = py0 - 4.0 + 34.0 * hz(i, 2, 884)
        if bois[min(P.H - 1, P.py(cy_)), min(P.Wt - 1, P.px(cx_))]:
            P.point(cx_, cy_, GR3)
            P.point(cx_ + 0.4, cy_ + 0.4, ENCRE)
    # La serrure bouchée à la cire : une plaque de fer, une goutte de cire qui a coulé.
    P.rampe(m_rect(P, TX + 3.0, 43.6, 4.0, 6.0), 0.3 + 0.2 * (X < TX + 4.0), [ENCRE, R_GRANIT[1], R_GRANIT[2], GR3], 0.5)
    P.ell(TX + 5.0, 46.2, 1.1, 1.3, LU2)
    P.point(TX + 4.6, 45.8, LU4)
    P.rect(TX + 4.8, 47.4, 0.5, 1.6, LU1)
    # Un anneau de fer scellé, sa chaîne rouillée ; la plaque du Service des Feux, sans plus de lettres.
    P.ell(TX - 23.0, 46.0, 1.8, 2.2, GR3)
    P.ell(TX - 23.0, 46.0, 0.9, 1.3, R_GRANIT[1])
    for k in range(6):
        P.ell(TX - 23.0 + 0.3 * math.sin(k) + 0.3 * onde(p, 0.3) * k / 6.0, 49.0 + k * 1.9, 0.7, 1.1, R_CUIVRE[1] if k % 2 else R_GRANIT[2])
    pl = m_rect(P, TX + 21.0, 36.0, 8.0, 5.0)
    P.rampe(pl, 0.4 + 0.2 * (pg.fbm(X / 1.0, Y / 1.0, 2, 885) - 0.5), [R_GRANIT[1], NU2, NU3, NU4], 0.5)
    P.rect(TX + 22.4, 37.6, 5.0, 0.4, BM1)
    P.rect(TX + 22.4, 39.0, 3.4, 0.4, BM1)
    for (cx_, cy_) in ((TX + 21.4, 36.4), (TX + 28.2, 36.4), (TX + 21.4, 40.2), (TX + 28.2, 40.2)):
        P.point(cx_, cy_, R_CUIVRE[1])
    P.rect(TX + 24.6, 41.0, 0.5, 5.0 + 0.0, R_CUIVRE[0])                                            # la rouille a coulé dessous
    # La petite porte du charbon, basse, en tôle, à droite ; un filet de poussier devant.
    ch = m_rect(P, TX + 24.0, 52.0, 8.0, 11.6)
    P.rampe(ch, 0.24 + 0.1 * (pg.fbm(X / 1.2, Y / 1.2, 2, 886) - 0.5) + 0.06 * (X < TX + 25.0), [ENCRE, R_GRANIT[0], R_GRANIT[1], R_CUIVRE[0], R_GRANIT[2]], 0.5)
    lisere(P, ch, ENCRE, 0, -1)
    lisere(P, ch, ENCRE, -1, 0)
    P.rect(TX + 24.0, 55.0, 8.0, 0.5, R_GRANIT[2])
    P.rect(TX + 24.0, 60.0, 8.0, 0.5, R_GRANIT[2])
    P.rect(TX + 30.0, 57.0, 1.2, 1.6, GR3)                                                         # le cadenas
    P.remplir(roc & m_ell(P, TX + 29.0, SOL + 1.2, 6.0, 1.0) & (pg.fbm(X / 1.0, Y / 0.6, 2, 887) > 0.4), ENCRE)

    # ---- Les trois marches, usées au milieu, luisantes ; les traces de goudron qui montent jusqu'au seuil.
    for j in range(3):
        y0 = SOL - 4.5 + j * 1.9
        x0, x1 = px0 - 5.0 - j * 3.4, px1 + 5.0 + j * 3.4
        des = P.masque_poly([(x0 + 1.4, y0), (x1 - 1.4, y0), (x1, y0 + 1.0), (x0, y0 + 1.0)])
        usure = 0.1 * np.exp(-((X - TX) / 10.0) ** 2)
        P.rampe(des, (0.7 - usure + 0.12 * (pg.fbm(X / 3.0, Y * 2.0, 2, 888 + j) - 0.5)) * (0.5 + 0.5 * np.clip((TX + 26.0 - X) / 50.0, 0, 1)) * 1.4, R_FROID, 0.5)
        P.rampe(m_rect(P, x0, y0 + 1.0, x1 - x0, 0.9), 0.24 + 0.1 * (X < TX), R_FROID, 0.5)
        lisere(P, des, BM3, 0, -1, cond=(X < TX + 6) & (pg.fbm(X / 2.0, 0 * X, 2, 889 + j) > 0.3))
        for k in range(3):                                      # l'eau qui luit sur la pierre
            if (k + j + int(p * 8)) % 4 == 0:
                P.point(TX - 14.0 + 9.0 * k + 3.0 * j, y0 + 0.4, BLANC)
    for i, (gx, gy) in enumerate(((TX - 31.0, SOL + 3.0), (TX - 24.0, SOL + 1.6), (TX - 17.0, SOL - 0.6), (TX - 11.0, SOL - 2.4), (TX - 6.0, SOL - 4.3))):
        P.ell(gx, gy, 1.5 - 0.14 * i, 0.6, ENCRE)                                                  # des pas dans le goudron
        P.ell(gx + 1.8, gy + 0.2, 0.6, 0.35, ENCRE)
        P.point(gx - 0.4, gy - 0.2, NU3)
    P.ell(TX - 38.0, SOL + 4.6, 4.0, 1.0, ENCRE)                                                   # la flaque de goudron, et un reflet de lune dedans
    P.ell(TX - 38.6, SOL + 4.4, 1.6, 0.3, NU3)
    bid = m_rect(P, TX - 46.0, SOL - 2.6, 4.4, 6.0)                                                # le bidon renversé de Tudal
    P.rampe(bid, 0.4 - 0.2 * (X - TX + 46.0) / 4.4, R_CUIVRE, 0.5)
    P.rect(TX - 46.0, SOL - 0.4, 4.4, 0.5, ENCRE)
    # Des flaques dans le creux du rocher : la lune dedans. Un goéland sur le bandeau, qui tourne la tête.
    for i, (fx_, fy_, rx) in enumerate(((44.0, SOL + 6.0, 9.0), (150.0, SOL + 5.0, 7.0))):
        fl = m_ell(P, fx_, fy_, rx, 1.3) & roc & (pg.fbm(X / 2.4, Y, 2, 890 + i) > 0.3)
        P.rampe(fl, 0.4 + 0.4 * (pg.fbm(X / 2.0 + 0.3 * onde(p), Y * 1.6, 2, 891) - 0.5) + (0.3 if i == 0 else 0.0), [NU0, NU1, NU3, BM1, BM3], 0.5)
        lisere(P, fl, ENCRE, 0, -1)
    goeland(P, TX - 30.0, 0.6, sens=1, pose=True)

    # ================================================================================================== premier plan
    tab.plan("premier", 1.0)
    # Deux masses de roche tout près, noires, coiffées de goémon ; des berniques ; l'embrun qui passe.
    fa = lambda x: 74.0 - 8.0 * np.exp(-((x + 2.0) / 16.0) ** 2) - 9.0 * np.exp(-((x - 196.0) / 15.0) ** 2) + 2.6 * np.sin(x / 17.0) * 0.4 + 1.4 * (pg.fbm(x / 3.0, 0 * x, 3, 892) - 0.5) + 5.0 * np.exp(-((x - 96.0) / 60.0) ** 2)
    av = Y > fa(X)
    P.rampe(av, 0.24 + 0.5 * (pg.fbm(X / 4.0 + 0.4 * Y, Y / 2.0, 3, 893) - 0.42) - 0.03 * (Y - fa(X)), [ENCRE, R_GRANIT[0], T.S0, R_GRANIT[1], R_GRANIT[2]], 0.5)
    lisere(P, av, BM1, 0, -1, cond=(pg.fbm(X / 2.4, 0 * X, 2, 894) > 0.4) & (X < 120))
    for i in range(18):
        x = (hz(i, 1, 895) * 44.0 - 6.0) if i % 2 else (198.0 - hz(i, 1, 895) * 40.0)
        y0 = float(fa(np.array([x]))[0])
        P.courbe([(x, y0), (x + 0.8 * onde(p, hz(i, 2, 895)), y0 + 1.8), (x + 1.6 * onde(p, hz(i, 2, 895)), y0 + 3.6)], T.S1 if i % 3 else T.S2, 1 if i % 3 else 2)
    for i in range(9):
        x = (hz(i, 3, 896) * 40.0 - 4.0) if i % 2 else (196.0 - hz(i, 3, 896) * 36.0)
        y0 = float(fa(np.array([x]))[0]) + 2.0 + 2.0 * hz(i, 4, 896)
        P.poly([(x - 1.0, y0), (x + 1.0, y0), (x, y0 - 1.0)], GR3)
        P.point(x - 0.2, y0 - 0.8, BM3)
    for i in range(12):                                         # l'embrun
        t = (p + hz(i, 0, 897)) % 1.0
        if t < 0.5:
            x = (4.0 + 26.0 * hz(i, 1, 897)) if i % 2 else (166.0 + 26.0 * hz(i, 1, 897))
            P.point(x + 3.0 * t, 70.0 - 14.0 * math.sin(t * 2 * math.pi) * (0.5 + hz(i, 2, 897)), BM4 if t < 0.25 else BM2)


# =====================================================================================================================
# La place de Trébrume : une placette pavée, par temps gris. Il bruine. Au milieu, une mairie si petite qu'on dirait une
# boîte aux lettres avec un drapeau (la clé) : volets bleus, drapeau mouillé, et derrière la fenêtre, Odile à son bureau
# sous sa lampe. La fontaine à gauche, le banc, le panneau d'affichage à droite et sa feuille toute neuve, quatre
# goélands sur le toit. Les pavés mouillés renvoient le ciel et les fenêtres.
# =====================================================================================================================
R_ARDOISE = [ENCRE, NU0, VI1, NU2, VI2, NU3, NU4]
R_CHAUX = cs("#5c6884", "#8a93a8", "#b9bcc6", "#dcd8d2", "#f3ead8", "#fff6e2")


def bruine(P, n, graine, coul, x0=-6.0, x1=198.0, y0=-16.0, y1=80.0):
    """Une pluie fine : de courts traits en biais, qui tombent et bouclent avec la phase."""
    for i in range(n):
        t = (P.p * 2 + hz(i, 0, graine)) % 1.0
        x = x0 + (x1 - x0) * hz(i, 1, graine) - 6.0 * t
        y = y0 + (y1 - y0) * ((hz(i, 2, graine) + t) % 1.0)
        P.trait(x, y, x - 0.5, y + 1.3, coul)


@decor("phare-eteint", "place-mairie", soleil=(40.0, -10.0), tons=AUBE, nom="La place de Trébrume", matiere=True)
def place_mairie(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tout = np.ones(X.shape, dtype=bool)
    SOL = 62.0                                                  # le pied des façades

    # ============================================================================================================ le ciel
    tab.plan("ciel", 0.0)
    P.rampe(tout, 0.5 + 0.006 * (Y + 16.0) + 0.24 * (pg.fbm((X + onde(p)) / 40.0, Y / 9.0, 4, 900) - 0.5) + 0.16 * np.exp(-((X - 40.0) / 50.0) ** 2 - ((Y + 10.0) / 16.0) ** 2), T.CIEL[2:11], 0.7)
    tab.plan("lointains", 0.2)
    # Les maisons du fond, dans la bruine : des pignons gris-bleu, de plus en plus pâles.
    for rang, (tons_, base) in enumerate((((T.CIEL[6], T.CIEL[7]), 44.0), ((T.CIEL[4], T.CIEL[6]), 52.0))):
        x = -10.0 + rang * 7.0
        i = 0
        while x < 200:
            w = 13.0 + 9.0 * hz(i, rang, 901)
            top = base - 20.0 - 12.0 * hz(i, rang + 3, 901)
            if not (56 < x + w / 2 < 134 and rang == 1):
                toit = P.masque_poly([(x - 1.0, top), (x + w + 1.0, top), (x + w * 0.5, top - w * 0.42)])
                P.remplir(m_rect(P, x, top, w, 70.0 - top) | toit, tons_[0])
                P.remplir(toit & (X < x + w * 0.5), tons_[1])
                P.rect(x + w * 0.66, top - w * 0.42 - 0.6, 2.0, w * 0.3, tons_[0])
                for j in range(2):
                    for q in range(2):
                        fx_, fy_ = x + 2.6 + q * (w - 7.6), top + 3.0 + j * 7.0
                        P.rect(fx_, fy_, 2.4, 3.4, LU4 if hz(i * 5 + j, q + rang, 902) < 0.24 else tons_[1])
                if i % 2 == 0:
                    fumerolle(P, x + w * 0.66 + 1.0, top - w * 0.42 - 1.4, h=10.0, n=3, d=0.2 * i, coul=T.CIEL[9], force=0.4, large=0.9)
            x += w + 0.6
            i += 1
    voile_ = (Y > 30.0) & (P.a >= 0)
    P.rampe(voile_ & (pg.fbm((X + 1.5 * onde(p, 0.2)) / 16.0, Y / 2.6, 3, 903) > 0.56) & (np.abs(Y - 47.0) < 5.0), 0.6, [T.CIEL[8], T.CIEL[9]], 0.6)

    # ====================================================================================================== la place
    tab.plan("moyen", 0.5)
    # ---- La mairie : chaux blanche, chaînes d'angle en granit, toit d'ardoise, un clocheton et son horloge.
    mx0, mx1, mtop = 66.0, 124.0, 30.0
    Lj = 0.9 - 0.0016 * (X - 40.0)                              # le jour gris : égal, un peu plus clair à gauche
    mur = m_rect(P, mx0, mtop, mx1 - mx0, SOL - mtop)
    P.rampe(mur, (0.74 + 0.16 * (pg.fbm(X / 9.0, Y / 6.0, 3, 904) - 0.5) + 0.1 * (pg.fbm(X / 1.3, Y / 1.3, 2, 905) - 0.5) - 0.2 * np.clip(pg.fbm(X / 2.0, Y / 24.0, 2, 906) - 0.6, 0, 1) * 3.0) * Lj, R_CHAUX, 0.5)
    P.rampe(mur & (Y < mtop + 1.6), 0.4, R_CHAUX, 0.5)                                             # l'ombre de l'avant-toit
    for xc in (mx0, mx1 - 3.0):                                                                   # les chaînes d'angle
        appareil(P, m_rect(P, xc, mtop, 3.0, SOL - mtop), Lj * 0.9 + 0 * X, (40.0, -10.0), lh=3.2, lw=3.0, graine=907, rampe=R_FROID, alb=0.74)
    P.rampe(m_rect(P, mx0 - 1.0, SOL - 3.0, mx1 - mx0 + 2.0, 3.0), (0.5 + 0.1 * (pg.fbm(X / 1.4, Y, 2, 908) - 0.5)) * Lj, R_FROID, 0.5)       # le soubassement
    toit = P.masque_poly([(mx0 - 3.0, mtop), (mx1 + 3.0, mtop), (mx1 - 5.0, mtop - 13.0), (mx0 + 5.0, mtop - 13.0)])
    rang_ = np.floor(Y / 0.82)
    ard = ((X + rang_ * 0.8) % 1.6) < 0.4
    P.rampe(toit, 0.5 - 0.12 * ard + 0.2 * (pg.fbm(X / 7.0, Y / 2.0, 3, 909) - 0.5) + 0.012 * (mtop - Y) + 0.1 * ((rang_ % 2) == 0), R_ARDOISE, 0.5)
    lisere(P, toit, BM2, 0, -1)                                                                   # le faîtage mouillé
    P.rect(mx0 - 3.6, mtop - 0.4, mx1 - mx0 + 7.2, 1.0, R_FROID[3])                                # la gouttière
    P.rect(mx0 - 3.6, mtop - 0.4, mx1 - mx0 + 7.2, 0.4, BM3)
    P.rect(mx1 + 2.0, mtop, 1.0, SOL - mtop, R_FROID[3])                                           # sa descente
    cx_ = (mx0 + mx1) / 2
    cl = m_rect(P, cx_ - 5.0, mtop - 22.0, 10.0, 12.0)                                             # le clocheton
    P.rampe(cl, (0.76 - 0.03 * (X - cx_)) * Lj, R_CHAUX, 0.5)
    ct = P.masque_poly([(cx_ - 6.4, mtop - 22.0), (cx_ + 6.4, mtop - 22.0), (cx_, mtop - 31.0)])
    P.rampe(ct, 0.4 + 0.24 * (X < cx_) - 0.1 * ard, R_ARDOISE, 0.5)
    P.trait(cx_, mtop - 31.0, cx_, mtop - 34.0, ENCRE)
    P.rampe(m_ell(P, cx_, mtop - 16.4, 3.6, 3.6), 0.5, [GO1, LAITON, LAITON2], 0.5)
    P.rampe(m_ell(P, cx_, mtop - 16.4, 2.9, 2.9), 0.8, R_PAPIER[2:], 0.5)
    P.trait(cx_, mtop - 16.4, cx_ - 1.0, mtop - 17.8, ENCRE)
    am = 2 * math.pi * (0.75 + int(p * 8) / 480.0)
    P.trait(cx_, mtop - 16.4, cx_ + 2.4 * math.sin(am), mtop - 16.4 - 2.4 * math.cos(am), ENCRE)
    for i, gx in enumerate((mx0 + 8.0, mx0 + 20.0, mx1 - 16.0, mx1 - 7.0)):                        # quatre goélands sur le faîte
        goeland(P, gx, mtop - 13.0, sens=1 if i % 2 else -1, pose=True)
    # La porte bleue, son perron, sa plaque ; quatre fenêtres à volets bleus ; à l'une, Odile sous sa lampe.
    porte = m_rect(P, cx_ - 4.6, SOL - 15.0, 9.2, 15.0) | m_ell(P, cx_, SOL - 15.0, 4.6, 3.4)
    P.rampe(m_rect(P, cx_ - 6.0, SOL - 15.4, 12.0, 15.4) | m_ell(P, cx_, SOL - 15.0, 6.0, 4.8), 0.6 * Lj, R_FROID, 0.5)
    lames(P, porte, 0.8 + 0 * X, larg=2.3, graine=910, vertical=True, rampe=R_TOILE, alb=0.56, noeuds=0)
    P.remplir(porte & (np.abs(X - cx_) < 0.25), R_TOILE[0])
    P.remplir(m_ell(P, cx_, SOL - 15.0, 3.6, 2.4) & (Y < SOL - 15.0), NU1)                           # l'imposte
    P.point(cx_ + 1.6, SOL - 7.0, LAITON2, 2)
    P.rect(cx_ + 7.4, SOL - 12.0, 3.6, 2.6, LAITON)                                                # la plaque
    P.rect(cx_ + 8.0, SOL - 11.2, 2.4, 0.4, GO1)
    for j in range(2):
        P.rampe(m_rect(P, cx_ - 8.0 - j * 2.0, SOL - 1.6 + j * 1.6, 16.0 + j * 4.0, 1.6), (0.8 - 0.1 * j + 0.1 * (pg.fbm(X / 2.0, Y, 2, 911) - 0.5)) * Lj, R_FROID, 0.5)
    for i, fx_ in enumerate((mx0 + 7.0, mx0 + 17.6, mx1 - 23.6, mx1 - 13.0)):
        for etage in range(2):
            fy_ = mtop + 4.0 + etage * 14.0
            if etage == 1 and i in (1, 2):
                continue                                         # la porte est là
            f = m_rect(P, fx_, fy_, 6.0, 8.6)
            odile = (i == 0 and etage == 1)
            if odile:                                           # le bureau de la maire : la lampe, les piles de papiers, sa silhouette
                P.rampe(f, 0.5 + 0.4 * np.exp(-((X - fx_ - 4.4) / 2.6) ** 2 - ((Y - fy_ - 3.0) / 3.0) ** 2), [LU1, LU2, LU3, LU4, LU5], 0.5)
                tete = 0.3 * (1 if int(p * 8) % 8 < 2 else 0)
                P.ell(fx_ + 2.2, fy_ + 4.2 + tete, 1.3, 1.4, R_BOIS[1])
                P.rect(fx_ + 0.8, fy_ + 5.6 + tete, 2.8, 3.0, R_BOIS[1])
                for k in range(3):
                    P.rect(fx_ + 4.0 + (k % 2) * 0.4, fy_ + 6.4 - k * 0.8, 1.6, 0.6, R_PAPIER[4] if k % 2 else R_PAPIER[3])
            else:
                P.rampe(f, 0.3 + 0.03 * (Y - fy_) + 0.2 * (pg.fbm(X / 3.0, Y / 2.0, 2, 912 + i) - 0.5), [NU1, NU2, NU3, T.CIEL[4], T.CIEL[6]], 0.5)
            P.rect(fx_ + 2.8, fy_, 0.5, 8.6, R_CHAUX[5])
            P.rect(fx_, fy_ + 4.0, 6.0, 0.5, R_CHAUX[5])
            for cote in (-1, 1):                                # les volets bleus, leurs lames
                vx = fx_ - 3.0 if cote < 0 else fx_ + 6.0
                vol = m_rect(P, vx, fy_, 3.0, 8.6)
                P.rampe(vol, 0.5 + 0.14 * ((np.floor(Y / 0.82) % 2) == 0) - 0.06 * cote, R_TOILE, 0.5)
                lisere(P, vol, R_TOILE[1], 1, 0)
            P.rect(fx_ - 0.6, fy_ + 8.6, 7.2, 0.8, R_FROID[5])                                     # l'appui
            if etage == 0 and i % 2 == 0:                       # une jardinière de bruyère
                for k in range(6):
                    P.point(fx_ + 0.4 + k * 1.0, fy_ + 8.0 - (k % 2) * 0.5, T.VIOLET if k % 2 else VI2, 2)
                    P.point(fx_ + 0.4 + k * 1.0, fy_ + 8.6, T.S2)
    # Le drapeau mouillé, qui pend à sa hampe et s'égoutte.
    hx_, hy_ = cx_ + 12.0, mtop + 2.0
    P.trait(hx_, hy_, hx_ + 9.0, hy_ - 14.0, R_BOIS[5], 2)
    P.point(hx_ + 9.2, hy_ - 14.6, LAITON2, 2)
    bal = 0.4 * onde(p, 0.1)
    dr = P.masque_poly([(hx_ + 8.6, hy_ - 13.4), (hx_ + 4.6, hy_ - 7.2), (hx_ + 5.4 + bal, hy_ + 2.0), (hx_ + 9.6 + bal, hy_ + 3.6), (hx_ + 10.6 + bal * 0.5, hy_ - 4.0)])
    pli = 0.5 + 0.5 * np.sin(X * 2.6 + Y * 0.4)
    P.rampe(dr, 0.3 + 0.4 * pli, R_TOILE, 0.5)
    P.rampe(dr & (Y > hy_ - 3.0), 0.4 + 0.4 * pli, [R_PAPIER[0], R_PAPIER[1], R_PAPIER[2], R_PAPIER[3]], 0.5)
    pg.goutte(P, hx_ + 7.4 + bal, hy_ + 3.8, SOL + 1.0, coul=BM4, d=0.2)

    # ---- Les pavés mouillés : le ciel dedans, les flaques, les fenêtres qui s'y allongent.
    place = Y >= SOL
    Lc = 0.84 + 0.1 * np.exp(-((X - 50.0) / 60.0) ** 2) - 0.004 * (Y - SOL)
    Lw = lumiere(P, [(mx0 + 10.0, SOL + 2.0, 6.0, 0.4)], 0.0)

    def ombre_p(cx, cy, rx, ry, f=0.4):
        nonlocal Lc
        Lc = Lc * (1 - f * np.clip(1.3 - np.hypot((X - cx) / rx, (Y - cy) / ry), 0, 1))

    ombre_p(16.0, 66.6, 14.0, 1.6)
    ombre_p(106.0, 66.4, 12.0, 1.2, 0.3)
    ombre_p(178.0, 66.6, 12.0, 1.4)
    flaques = paves(P, place, Lc, Lw, 96.0, 44.0, larg=2.4, prof=4.6, graine=913)
    refl = flaques & place
    P.rampe(refl & (np.abs(X - cx_) < 30.0) & (Y < SOL + 9.0), 0.7 + 0.2 * (pg.fbm(X / 3.0, Y / 0.7 + onde(p), 2, 914) - 0.5), R_CHAUX[1:], 0.5)      # la façade dans l'eau
    for k in range(6):                                          # la lampe d'Odile, en tirets
        if (k + int(p * 8)) % 3:
            P.trait(mx0 + 9.0, SOL + 1.4 + k * 1.2, mx0 + 11.0, SOL + 1.4 + k * 1.2, LU3 if k < 3 else LU2)
    for i, (rx, ry) in enumerate(((60.0, 72.0), (134.0, 70.0), (96.0, 76.0), (160.0, 75.0))):       # les ronds de la bruine
        t = (p + i * 0.27) % 1.0
        dd = np.hypot(X - rx, (Y - ry) * 3.0)
        P.remplir(place & (np.abs(dd - 0.6 - 3.0 * t) < 0.3) & (t < 0.8), BM4)

    # ---- La fontaine, à gauche : un bassin rond de granit, une borne, un filet d'eau.
    fx_, fy_ = 16.0, 64.0
    bas = (m_rect(P, fx_ - 12.0, fy_ - 4.0, 24.0, 4.4) | m_ell(P, fx_, fy_ + 0.4, 12.0, 2.2)) & ~(m_ell(P, fx_, fy_ - 4.0, 12.0, 2.2) & (Y < fy_ - 4.0))
    appareil(P, bas, (0.74 - 0.26 * (X - fx_) / 12.0) + 0 * X, (40.0, -10.0), lh=2.2, lw=5.0, graine=915, rampe=R_FROID, alb=0.66)
    bord = m_ell(P, fx_, fy_ - 4.0, 12.0, 2.2)
    P.rampe(bord, 0.74, R_FROID, 0.5)
    lisere(P, bord, R_FROID[2], 0, 1)
    eau = m_ell(P, fx_, fy_ - 4.0, 10.4, 1.5)
    P.rampe(eau, 0.5 + 0.3 * (pg.fbm(X / 2.0 + 0.4 * onde(p), Y * 2.0, 2, 916) - 0.5), [NU2, NU3, T.CIEL[4], T.CIEL[7], T.CIEL[9]], 0.5)
    borne = m_rect(P, fx_ - 2.0, fy_ - 18.0, 4.0, 14.0) | m_ell(P, fx_, fy_ - 18.0, 2.6, 1.6)
    P.rampe(borne, (0.62 - 0.3 * (X - fx_) / 2.6) + 0.1 * (pg.fbm(X, Y / 3.0, 2, 917) - 0.5), R_FROID, 0.5)
    P.rect(fx_ + 2.0, fy_ - 12.6, 2.4, 0.8, LAITON)                                                # le bec
    for k in range(6):
        t = (p * 2 + k / 6.0) % 1.0
        P.point(fx_ + 4.4, fy_ - 11.8 + 7.0 * t, BM4 if k % 2 else T.CIEL[9])
    dd = np.hypot(X - fx_ - 4.4, (Y - fy_ + 4.0) * 3.0)
    P.remplir(eau & (np.abs(dd - 0.5 - 3.0 * ((p * 2) % 1.0)) < 0.3), BLANC)
    P.remplir(tout & m_rect(P, fx_ - 2.0, fy_ - 6.0, 4.0, 2.0) & (pg.fbm(X / 0.8, Y / 0.8, 2, 918) > 0.5), T.S1)                 # la mousse au pied
    # Le banc, devant la mairie ; un réverbère éteint ; la boîte aux lettres.
    bx0 = 96.0
    for yy, h_, ton in ((SOL - 6.4, 1.2, 0.7), (SOL - 4.4, 1.2, 0.62), (SOL - 1.2, 1.4, 0.76)):
        P.rampe(m_rect(P, bx0, yy, 20.0, h_), ton * Lj + 0.06 * (pg.fbm(X / 3.0, Y * 2, 2, 919) - 0.5), R_BOIS[1:8], 0.5)
    for xq in (bx0 + 1.6, bx0 + 17.4):
        P.rect(xq, SOL - 6.4, 1.0, 9.4, R_FROID[1])
    lx_ = 134.0
    P.rampe(m_rect(P, lx_ - 0.7, 22.0, 1.4, 44.0), 0.3 + 0.4 * (X < lx_), R_FROID, 0.5)
    P.rect(lx_ - 1.6, 62.0, 3.2, 4.0, R_FROID[2])
    lan = P.masque_poly([(lx_ - 2.4, 16.0), (lx_ + 2.4, 16.0), (lx_ + 1.6, 22.0), (lx_ - 1.6, 22.0)])
    P.rampe(lan, 0.5 - 0.1 * (X - lx_), [NU2, T.CIEL[4], T.CIEL[7], T.CIEL[10]], 0.5)
    P.poly([(lx_ - 3.0, 16.0), (lx_ + 3.0, 16.0), (lx_, 13.0)], R_FROID[1])
    goeland(P, lx_ + 0.4, 13.0, sens=-1, pose=True)
    bl = m_rect(P, 141.0, SOL - 7.0, 4.6, 6.0) | m_ell(P, 143.3, SOL - 7.0, 2.3, 1.2)
    P.rampe(bl, 0.5 - 0.2 * (X - 143.3) / 2.3, R_TOILE, 0.5)
    P.rect(141.8, SOL - 5.6, 3.0, 0.5, R_TOILE[0])
    P.rect(142.9, SOL - 1.0, 0.9, 5.0, R_FROID[2])

    # ---- Le panneau d'affichage, à droite : des avis jaunis, et une feuille toute neuve, bien blanche.
    ax0, ay0 = 166.0, 40.0
    for xq in (ax0 + 1.0, ax0 + 20.0):
        P.rampe(m_rect(P, xq, ay0 - 2.0, 1.6, 28.0), 0.5 + 0.2 * (X < xq + 0.6), R_BOIS, 0.5)
    pan = m_rect(P, ax0, ay0, 22.6, 15.0)
    lames(P, pan, 0.8 + 0 * X, larg=5.0, graine=920, vertical=False, alb=0.5, noeuds=0)
    P.poly([(ax0 - 1.6, ay0), (ax0 + 24.2, ay0), (ax0 + 11.3, ay0 - 4.6)], R_ARDOISE[2])            # son petit toit
    P.poly([(ax0 - 1.6, ay0), (ax0 + 11.3, ay0 - 4.6), (ax0 + 11.3, ay0 - 3.6), (ax0, ay0)], R_ARDOISE[4])
    for i, (qx, qy, qw, qh, r, inc) in enumerate(((ax0 + 1.4, ay0 + 1.6, 5.0, 6.4, R_PLATRE[5:], 0.2), (ax0 + 14.6, ay0 + 1.2, 6.0, 5.0, R_PLATRE[4:8], -0.3),
                                                  (ax0 + 2.0, ay0 + 9.0, 4.4, 4.6, R_PLATRE[5:], -0.2), (ax0 + 15.4, ay0 + 7.6, 5.0, 6.0, R_PLATRE[4:8], 0.3))):
        av = P.masque_poly([(qx, qy), (qx + qw, qy + inc), (qx + qw - inc, qy + qh), (qx - inc, qy + qh - inc)])
        P.rampe(av, 0.6 + 0.2 * (pg.fbm(X, Y, 2, 921 + i) - 0.5), r, 0.5)
        for k in range(3):
            P.trait(qx + 0.8, qy + 1.4 + k * 1.3, qx + qw - 1.2, qy + 1.4 + k * 1.3 + inc, R_PLATRE[3])
        P.point(qx + qw / 2, qy + 0.4, R_CUIVRE[1])
    nf = P.masque_poly([(ax0 + 7.4, ay0 + 2.0), (ax0 + 14.0, ay0 + 1.8), (ax0 + 14.2 + 0.3 * onde(p, 0.3), ay0 + 12.6), (ax0 + 7.6, ay0 + 12.8)])     # la feuille neuve
    P.remplir(nf, BLANC)
    lisere(P, nf, R_PAPIER[2], 1, 0)
    P.rect(ax0 + 8.4, ay0 + 3.4, 4.6, 0.8, R_NUIT[1])
    for k in range(5):
        P.trait(ax0 + 8.4, ay0 + 5.4 + k * 1.3, ax0 + 13.0 - (k % 2), ay0 + 5.4 + k * 1.3, R_NUIT[3])
    P.point(ax0 + 10.8, ay0 + 2.4, LU2, 2)                                                         # sa punaise

    # ================================================================================================== premier plan
    tab.plan("premier", 1.0)
    # En haut à gauche, une branche de platane qui s'égoutte ; en bas, deux bornes de fonte et leur chaîne.
    for i, pts in enumerate(([(-6.0, -6.0), (14.0, -9.0), (34.0, -4.0), (52.0, -8.0)], [(8.0, -8.0), (20.0, 0.0), (30.0, 6.0)], [(30.0, -5.0), (40.0, 2.0), (46.0, 1.0)],
                             [(-6.0, 4.0), (8.0, 2.0), (18.0, 8.0)])):
        P.courbe(pts, R_BOIS[0], P.ep(1.4 - 0.2 * i), 1)
    for i in range(34):
        bx_, by_ = -4.0 + 58.0 * hz(i, 1, 922), -14.0 + 24.0 * hz(i, 2, 922)
        bx_ += 0.3 * onde(p, hz(i, 3, 922))
        for (ax_, ay_) in pg.tampon_feuille(P, i):
            P.bloc(P.px(bx_) + ax_, P.py(by_) + ay_, (T.S0, T.S1, T.S2, R_BOIS[2])[int(hz(i, 4, 922) * 4)])
    for i, gx in enumerate((12.0, 26.0, 44.0)):
        pg.goutte(P, gx, 4.0 + 3.0 * i, 30.0 + 8.0 * i, coul=BM4, d=0.3 * i, flaque=BM4)
    for bx_ in (2.0, 190.0):
        bn = m_rect(P, bx_ - 2.2, 64.0, 4.4, 16.0) | m_ell(P, bx_, 64.0, 3.0, 2.4)
        P.rampe(bn, 0.3 - 0.2 * (X - bx_) / 3.0 + 0.1 * (Y < 64.0), [ENCRE, NU0, NU1, NU3, BM1], 0.5)
        P.rect(bx_ - 2.6, 68.0, 5.2, 0.8, ENCRE)
    for k in range(13):
        u = k / 12.0
        cxk, cyk = 4.0 + 22.0 * u, 68.6 + 9.0 * math.sin(u * math.pi * 0.5) + 0.3 * onde(p, 0.2)
        P.ell(cxk, cyk, 1.0, 0.7, NU0 if k % 2 else NU2)
    P.rampe(Y > 78.8, 0.2 + 0 * X, R_FROID, 0.5)
    bruine(P, 70, 923, T.CIEL[10])


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
# L'atelier de Basile : « horlogerie, mécanique fine, réparations de tout ». Deux cents pendules, et pas deux d'accord.
# L'établi est à droite, sous sa lampe : la loupe, les limes, un cadran de laiton démonté, la poussière dorée. Au mur
# derrière, le tableau de clefs étiquetées, et tout en haut la grosse clef de la Dent-Creuse. Au fond, sur une étagère,
# une forme ronde sous un drap. Le jour gris entre par la vitrine de gauche.
# =====================================================================================================================
R_LAITON = [GO1, GO2, LAITON, LAITON2, LU5]


def horloge(P, x, y, r, L, sorte=0, heure=0.0, d=0.0, balancier=0.0):
    """Une pendule au mur, éclairée par L : boîtier (0 rond de laiton, 1 carré de bois, 2 coucou, 3 œil-de-bœuf sombre),
    cadran d'émail, deux aiguilles à son heure à elle, et un balancier qui bat à son rythme."""
    X, Y = P.X, P.Y
    li = float(L[min(P.H - 1, max(0, P.py(y))), min(P.Wt - 1, max(0, P.px(x)))])
    if balancier:
        a = 0.34 * onde(P.p, d)
        bx_, by_ = x + balancier * math.sin(a), y + r * 0.8 + balancier * math.cos(a)
        P.trait(x, y + r * 0.8, bx_, by_, LAITON if li > 0.4 else GO2)
        P.rampe(m_ell(P, bx_, by_, max(0.8, r * 0.3), max(0.8, r * 0.3)), 0.3 + 0.6 * li - 0.3 * (X - bx_) / r, R_LAITON, 0.5)
    if sorte == 1:
        boite = m_rect(P, x - r - 1.2, y - r - 1.2, 2 * r + 2.4, 2 * r + 2.4)
        P.rampe(boite, (0.7 + 0.2 * (pg.fbm(X / 0.8, Y / 5.0, 2, 930) - 0.5) - 0.1 * (X - x) / r) * li, R_BOIS, 0.5)
        lisere(P, boite, R_BOIS[1], 0, 1)
    elif sorte == 2:
        boite = m_rect(P, x - r - 1.0, y - r - 0.6, 2 * r + 2.0, 2 * r + 2.4) | P.masque_poly([(x - r - 2.4, y - r - 0.6), (x + r + 2.4, y - r - 0.6), (x, y - r - 4.6)])
        P.rampe(boite, (0.62 - 0.14 * (X - x) / r + 0.2 * (Y < y - r - 0.6) * (X < x)) * li, R_BOIS, 0.5)
        P.rect(x - 0.9, y - r - 2.6, 1.8, 1.6, R_BOIS[0])                                           # la petite porte du coucou
    else:
        boite = m_ell(P, x, y, r + 1.2, r + 1.2)
        P.rampe(boite, 0.2 + (0.5 - 0.3 * (X - x) / r - 0.2 * (Y - y) / r) * li * 1.6, R_LAITON if sorte == 0 else R_BOIS[:6], 0.5)
    cad = m_ell(P, x, y, r, r)
    P.rampe(cad, 0.24 + (0.56 - 0.14 * (X - x) / r - 0.1 * (Y - y) / r) * li * 1.3, [R_PAPIER[0], R_PAPIER[1], R_PAPIER[2], CREME, LU5], 0.5)
    if r > 2.4:
        for k in range(12):
            P.point(x + (r - 0.8) * math.sin(k * math.pi / 6), y - (r - 0.8) * math.cos(k * math.pi / 6), GR2 if k % 3 else ENCRE)
    h = heure * 2 * math.pi
    P.trait(x, y, x + r * 0.5 * math.sin(h), y - r * 0.5 * math.cos(h), ENCRE)
    m = (heure * 12 + (int(P.p * 8) / 60.0 if d < 0.5 else 0.0)) * 2 * math.pi
    P.trait(x, y, x + r * 0.82 * math.sin(m), y - r * 0.82 * math.cos(m), ENCRE)
    P.point(x, y, LAITON2)


@decor("phare-eteint", "atelier-basile", soleil=(164.0, 34.0), tons=PHARE, nom="L'atelier de Basile", matiere=True)
def atelier_basile(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tout = np.ones(X.shape, dtype=bool)
    LX, LY = 164.0, 36.0                                        # la lampe de l'établi
    SOL = 62.0
    vac = 1.0 + 0.03 * onde(p * 2)

    # ============================================================================================================ le mur
    tab.plan("ciel", 0.0)
    jour = np.exp(-((X - 14.0) / 34.0) ** 2 - ((Y - 20.0) / 30.0) ** 2)                            # ce que donne la vitrine
    Lm = lumiere(P, [(LX, LY + 4.0, 38.0, 1.1)], 0.2) + 0.3 * jour
    Lm = Lm * (1 - 0.34 * np.clip(1 - np.abs(Y + 12.0) / 6.0, 0, 1))
    lames(P, tout, Lm, larg=8.6, graine=931, vertical=True, alb=0.6, sens=1, noeuds=0.4)
    P.rampe((Y >= SOL - 2.6) & (Y < SOL), 0.4 * Lm, R_BOIS, 0.5)
    P.rampe((Y >= SOL - 2.6) & (Y < SOL - 2.2), 0.7 * Lm, R_BOIS, 0.5)
    P.rampe(Y < -11.0, 0.3 * Lm, R_BOIS, 0.5)                                                      # la corniche
    P.rampe((Y >= -11.0) & (Y < -10.2), 0.16 + 0 * X, R_BOIS, 0.5)
    # ---- La vitrine, à gauche : le jour gris de la rue, les lettres de l'enseigne à l'envers (des pleins et des déliés).
    vx, vy, vw, vh = -6.0, -6.0, 36.0, 44.0
    vit = m_rect(P, vx, vy, vw, vh)
    P.rampe(vit, 0.5 + 0.01 * (Y - vy) + 0.2 * (pg.fbm((X + onde(p)) / 9.0, Y / 5.0, 3, 932) - 0.5), [NU3, NU4, BM1, BM2, BM3, BM4], 0.6)
    for i, (hx, hw, top) in enumerate(((-4.0, 12.0, 14.0), (9.0, 10.0, 8.0), (20.0, 12.0, 17.0))):   # la rue d'en face
        P.remplir(vit & (m_rect(P, hx, top, hw, 60.0) | P.masque_poly([(hx - 1, top), (hx + hw + 1, top), (hx + hw / 2, top - hw * 0.4)])), NU3 if i % 2 else NU4)
        P.remplir(vit & m_rect(P, hx + 2.0, top + 4.0, 2.4, 3.4), LU4 if i == 1 else NU2)
    for k in range(4):                                          # des gouttes sur la vitre
        t = (p + k * 0.27) % 1.0
        P.trait(1.0 + k * 8.0, vy + 4.0 + 30.0 * t, 1.0 + k * 8.0, vy + 5.4 + 30.0 * t, BM4)
    cad = m_rect(P, vx - 2.0, vy - 2.0, vw + 4.0, vh + 4.0) & ~vit
    P.rampe(cad, 0.5 + 0.2 * (X > vx + vw), R_BOIS, 0.5)
    P.rect(vx + vw * 0.5 - 0.6, vy, 1.2, vh, R_BOIS[2])
    P.rect(vx, vy + 12.0, vw, 1.0, R_BOIS[2])
    lisere(P, vit, R_BOIS[0], 0, -1)
    P.rampe(m_rect(P, vx, vy + vh + 2.0, vw + 6.0, 2.4), 0.9 - 0.2 * (Y - vy - vh - 2.0), R_BOIS, 0.5)      # la tablette de la vitrine
    for i, (wx_, r_) in enumerate(((2.0, 2.6), (10.0, 3.4), (19.0, 2.8), (27.0, 2.2))):            # des montres et un réveil en montre
        horloge(P, wx_, vy + vh + 2.0 - r_ - 1.0, r_, Lm * 0 + 0.9, sorte=(0, 1, 0, 3)[i], heure=hz(i, 1, 933), d=hz(i, 2, 933))
    # ---- Le mur des pendules : chacune à son heure, les balanciers qui battent chacun pour soi.
    i = 0
    for row, y0 in enumerate((-4.0, 9.0, 22.0, 35.0, 47.0)):
        x = 37.0 + (row % 2) * 5.0
        while x < 126.0:
            r_ = 2.4 + 2.8 * hz(i, 1, 934)
            cx_, cy_ = x + r_, y0 + (hz(i, 2, 934) - 0.5) * 4.0
            libre = not (66.0 < cx_ < 104.0 and row in (2, 3)) and not (cy_ > 44.0 and cx_ > 110)
            if libre:
                horloge(P, cx_, cy_, r_, Lm, sorte=int(hz(i, 3, 934) * 4), heure=hz(i, 4, 934), d=hz(i, 5, 934),
                        balancier=(3.0 + 3.0 * hz(i, 6, 934)) if hz(i, 7, 934) < 0.45 else 0.0)
            x += 2 * r_ + 3.6 + 3.0 * hz(i, 8, 934)
            i += 1
    # ---- Au fond, sur son étagère : la forme ronde sous un drap.
    ex, ey = 68.0, 40.0
    P.rampe(m_rect(P, ex, ey, 36.0, 1.8), (0.9 - 0.3 * (Y - ey)) * (Lm + 0.1), R_BOIS, 0.5)
    P.rampe(m_rect(P, ex + 0.6, ey + 1.8, 36.0, 1.2), 0.3 * Lm, R_BOIS, 0.5)
    for cxl in (ex + 4.0, ex + 30.0):
        P.poly([(cxl, ey + 1.8), (cxl + 1.4, ey + 1.8), (cxl + 1.4, ey + 3.4), (cxl, ey + 6.0)], R_BOIS[2])
    dx_ = ex + 18.0
    souffle = 0.3 * onde(p, 0.3)
    drap = (m_ell(P, dx_, ey - 9.0, 9.6, 9.0) & (Y < ey - 6.0)) | (m_rect(P, dx_ - 9.6, ey - 9.0, 19.2, 9.0) & (np.abs(X - dx_) < 9.6 + 1.6 * (Y - ey + 9.0) / 9.0 + souffle * (Y - ey + 9.0) / 9.0))
    pli = 0.5 + 0.5 * np.sin((X - dx_) * 1.1 + 0.5 * np.sin(Y * 0.6)) * np.clip((Y - ey + 12.0) / 8.0, 0, 1)
    P.rampe(drap, (0.5 + 0.3 * pli + 0.26 * (X - dx_) / 9.6) * (0.4 + Lm), R_PAPIER, 0.5)
    lisere(P, drap, R_PAPIER[5], 1, 0, cond=Y < ey - 4)
    # ---- Derrière l'établi : le tableau de clefs étiquetées ; tout en haut, la grosse clef de service de la Dent-Creuse.
    kx, ky, kw, kh = 136.0, -6.0, 44.0, 30.0
    P.rampe(m_rect(P, kx + 0.8, ky + kh, kw, 1.2), 0.3 * Lm, R_BOIS, 0.5)
    tabl = m_rect(P, kx, ky, kw, kh)
    lames(P, tabl, Lm * 1.1, larg=30.0, graine=935, vertical=False, alb=0.44, noeuds=0)
    lisere(P, tabl, R_BOIS[7], 0, -1)
    lisere(P, tabl, R_BOIS[1], 0, 1)
    gx, gy = kx + 22.0, ky + 4.4                                 # la grosse clef : anneau, tige, panneton
    P.point(gx - 9.0, gy - 2.0, GR3, 2)
    P.rampe(m_ell(P, gx - 9.0, gy + 1.0, 3.0, 2.6) & ~m_ell(P, gx - 9.0, gy + 1.0, 1.5, 1.2), 0.6, R_LAITON, 0.5)
    P.rampe(m_rect(P, gx - 6.0, gy + 0.4, 17.0, 1.3), 0.5 + 0.3 * (Y < gy + 0.9), R_LAITON, 0.5)
    P.rect(gx + 7.0, gy + 1.7, 1.4, 3.0, LAITON)
    P.rect(gx + 9.6, gy + 1.7, 1.4, 2.2, LAITON)
    P.rect(gx - 4.0, gy + 2.6, 5.0, 3.0, R_PAPIER[4])                                              # son étiquette
    P.rect(gx - 3.2, gy + 3.4, 3.4, 0.4, R_NUIT[2])
    P.rect(gx - 3.2, gy + 4.4, 2.2, 0.4, R_NUIT[2])
    if int(p * 8) % 6 == 0:
        P.point(gx + 3.0, gy + 0.5, BLANC)
    for j in range(3):
        for q in range(8):
            cx_, cy_ = kx + 4.0 + q * 5.2, ky + 11.6 + j * 6.4
            if (j, q) in ((0, 3), (2, 6)):                      # deux crochets vides
                P.point(cx_, cy_ - 1.0, GR3)
                continue
            bal = 0.2 * onde(p, hz(j, q, 936)) if hz(j, q + 9, 936) < 0.3 else 0.0
            P.point(cx_, cy_ - 1.0, GR3)
            P.ell(cx_ + bal, cy_ + 0.4, 1.0, 1.0, R_LAITON[2 + (q + j) % 2])
            P.point(cx_ + bal, cy_ + 0.4, R_BOIS[2])
            P.rect(cx_ - 0.2 + bal, cy_ + 1.4, 0.5, 2.2, R_LAITON[2 + (q + j) % 2])
            P.rect(cx_ + 0.3 + bal, cy_ + 3.0, 0.7, 0.5, R_LAITON[2])
            P.rect(cx_ - 1.6, cy_ + 3.9, 3.0, 1.2, R_PAPIER[3 + (q % 2)])

    # ==================================================================================================== la boutique
    tab.plan("moyen", 0.5)
    Ls = lumiere(P, [(LX - 6.0, 70.0, 26.0, 0.9), (16.0, 70.0, 30.0, 0.5)], 0.22)

    def ombre_s(cx, cy, rx, ry, f=0.5):
        nonlocal Ls
        Ls = Ls * (1 - f * np.clip(1.3 - np.hypot((X - cx) / rx, (Y - cy) / ry), 0, 1))

    ombre_s(150.0, 66.0, 40.0, 3.4, 0.6)
    ombre_s(52.0, 65.0, 10.0, 1.8)
    sol = Y >= SOL
    plancher(P, sol, Ls, 96.0, 40.0, larg=4.2, graine=937, alb=0.66)
    # La comtoise sans aiguilles, en attente : caisse ouverte, on voit ses poids.
    hx_ = 52.0
    caisse = m_rect(P, hx_ - 6.0, 4.0, 12.0, 60.0) | (m_ell(P, hx_, 4.0, 6.0, 4.0) & (Y < 4.2))
    lames(P, caisse, (Lm + 0.14) * (0.9 + 0.03 * (X - hx_ + 6.0)), larg=30.0, graine=938, vertical=True, alb=0.8, noeuds=0)
    P.rampe(caisse & (X > hx_ + 4.6), 1.1 * Lm + 0.06, R_BOIS, 0.5)
    P.rampe(m_ell(P, hx_, 12.0, 4.6, 4.6), 0.5 + 0.2 * (X - hx_) / 4.6, R_PAPIER[1:], 0.5)
    for k in range(12):
        P.point(hx_ + 3.6 * math.sin(k * math.pi / 6), 12.0 - 3.6 * math.cos(k * math.pi / 6), GR2)
    P.point(hx_, 12.0, LAITON2, 2)                                                                # pas d'aiguilles : elles sont sur l'établi
    trou = m_rect(P, hx_ - 3.6, 22.0, 7.2, 30.0)
    P.remplir(trou, R_BOIS[0])
    for dx, l in ((-1.8, 14.0), (1.8, 22.0)):
        P.trait(hx_ + dx, 22.0, hx_ + dx, 22.0 + l, GO2)
        P.rampe(m_rect(P, hx_ + dx - 0.9, 22.0 + l, 1.8, 5.0), 0.3 + 0.5 * (X - hx_ - dx + 0.9) / 1.8, R_LAITON, 0.5)
    P.trait(hx_ + 6.6, 22.0, hx_ + 9.6, 52.0, R_BOIS[4], P.ep(0.9))                                # sa porte, posée contre elle
    P.rampe(m_rect(P, hx_ - 7.2, 60.0, 14.4, 4.0), 0.5 * Lm, R_BOIS, 0.5)

    # ---- L'établi : chêne ciré, tiroirs à boutons de laiton, étau ; sous la lampe, le cadran de laiton démonté.
    ex0, ex1, et = 124.0, 196.0, 48.0
    Le = lumiere(P, [(LX, et, 20.0, 1.3 * vac)], 0.24)
    P.rampe(m_rect(P, ex0, et, ex1 - ex0, 2.4), (0.9 - 0.2 * (Y - et)) * Le, R_BOIS, 0.5)
    P.rampe(m_rect(P, ex0, et, ex1 - ex0, 0.5), 1.2 * Le, R_BOIS, 0.5)
    face = m_rect(P, ex0 + 2.0, et + 2.4, ex1 - ex0 - 2.0, SOL + 1.6 - et - 2.4)
    lames(P, face, Lm * 0.8 + 0.06, larg=30.0, graine=939, vertical=False, alb=0.5, noeuds=0)
    for q in range(4):
        tir = m_rect(P, ex0 + 4.0 + q * 16.0, et + 4.4, 13.6, 5.6)
        lames(P, tir, Lm * 1.1 + 0.06, larg=30.0, graine=940 + q, vertical=False, alb=0.6, noeuds=0)
        lisere(P, tir, R_BOIS[1], 0, 1)
        lisere(P, tir, R_BOIS[7], 0, -1)
        P.point(ex0 + 10.6 + q * 16.0, et + 7.0, LAITON2, 2)
    for xq in (ex0 + 2.0, ex0 + 5.0):
        P.rampe(m_rect(P, xq, et + 12.0, 2.4, SOL + 3.0 - et - 12.0), 0.4 * Lm, R_BOIS, 0.5)
    # La lampe : un bras de laiton, un abat-jour d'opaline bleue, le cône de lumière et sa poussière dorée.
    P.rampe(m_ell(P, LX + 14.0, et - 0.6, 4.0, 1.2), 0.6, R_LAITON, 0.5)
    P.courbe([(LX + 14.0, et - 1.0), (LX + 14.0, LY - 8.0), (LX + 6.0, LY - 12.0), (LX, LY - 7.0)], LAITON, 2)
    ab = P.masque_poly([(LX - 5.6, LY), (LX + 5.6, LY), (LX + 2.4, LY - 6.0), (LX - 2.4, LY - 6.0)])
    P.rampe(ab, 0.56 - 0.2 * (X - LX) / 5.6 + 0.2 * (Y - LY + 6.0) / 6.0, R_TOILE, 0.5)
    P.rect(LX - 5.6, LY, 11.2, 0.6, LU5)
    cone = (Y > LY + 0.6) & (Y < et) & (np.abs(X - LX) < 5.0 + (Y - LY) * 1.1)
    voile(P, cone, LU4, 0.3 * (1 - (Y - LY) / (et - LY + 6.0)) * (1 - np.abs(X - LX) / (5.0 + (Y - LY) * 1.1)) * vac, lumiere=True)
    for i in range(18):                                         # la poussière de laiton
        if (p + hz(i, 1, 941)) % 1.0 < 0.6:
            yy = LY + 1.0 + (et - LY - 2.0) * ((hz(i, 2, 941) + p * 0.5) % 1.0)
            P.point(LX + (hz(i, 3, 941) - 0.5) * (8.0 + (yy - LY) * 1.8) + 0.5 * onde(p, hz(i, 4, 941)), yy, LU5 if i % 2 else LAITON2)
    # Sur l'établi : le grand cadran aux points en relief, les aiguilles, la loupe sur son pied, les limes, des roues.
    cd = m_ell(P, LX - 3.0, et - 1.6, 7.6, 2.2)
    P.rampe(cd, 0.6 - 0.2 * (X - LX + 3.0) / 7.6 + 0.2 * vac - 0.2, R_LAITON, 0.5)
    P.ell(LX - 3.0, et - 1.6, 5.2, 1.4, GO2)
    P.ell(LX - 3.0, et - 1.7, 4.4, 1.1, LAITON2)
    for k in range(12):
        a = k * math.pi / 6
        P.point(LX - 3.0 + 6.4 * math.cos(a), et - 1.6 + 1.8 * math.sin(a), LU5 if (k + int(p * 8)) % 6 == 0 else GO1)
    P.trait(LX + 6.0, et - 0.6, LX + 11.0, et - 1.2, ENCRE)                                         # les deux aiguilles de la comtoise
    P.trait(LX + 6.4, et - 0.2, LX + 9.4, et - 0.2, ENCRE)
    lx_ = LX - 18.0                                             # la loupe d'établi
    P.trait(lx_, et - 0.4, lx_ + 1.0, et - 9.0, GO2, 2)
    P.rampe(m_ell(P, lx_, et - 0.6, 3.0, 1.0), 0.5, R_LAITON, 0.5)
    P.rampe(m_ell(P, lx_ + 2.0, et - 11.0, 4.0, 3.0), 0.5 - 0.2 * (X - lx_ - 2.0) / 4.0, R_LAITON, 0.5)
    P.rampe(m_ell(P, lx_ + 2.0, et - 11.0, 3.1, 2.2), 0.6 + 0.3 * (X - lx_ - 2.0) / 3.1, [NU3, BM1, BM3, LU5], 0.5)
    P.point(lx_ + 0.8, et - 12.0, BLANC)
    for k in range(4):                                          # les limes, bien rangées
        P.trait(ex0 + 4.0 + k * 1.6, et - 0.4, ex0 + 9.0 + k * 1.6, et - 3.4 + k * 0.2, GR3 if k % 2 else GR4)
        P.rect(ex0 + 3.4 + k * 1.6, et - 0.9, 1.2, 0.9, R_BOIS[5])
    for i, (rx_, rr, dents) in enumerate(((LX + 20.0, 2.6, 9), (LX + 25.0, 1.8, 7), (ex0 + 18.0, 2.0, 8))):
        pg.roue(P, rx_, et - rr * 0.5 - 0.6, rr, dents, LAITON, LAITON2, GO1, angle=(1 if i % 2 else -1) * 2 * math.pi * p / dents * 2)
    P.rect(ex1 - 12.0, et - 6.0, 5.0, 6.0, GR2)                                                    # l'étau
    P.rect(ex1 - 13.0, et - 6.6, 7.0, 1.4, GR3)
    P.trait(ex1 - 7.0, et - 3.0, ex1 - 3.0, et - 3.0, GR4, 2)
    # Un tabouret ; une caisse de pendules en dépôt ; le chat de l'horloger dort sur le plancher, dans le jour de la vitrine.
    P.rampe(m_ell(P, 112.0, 60.0, 5.0, 1.5), 0.7 * Le, R_BOIS, 0.5)
    for dx in (-3.6, 0.0, 3.6):
        P.trait(112.0 + dx * 0.8, 61.0, 112.0 + dx * 1.3, 72.0, R_BOIS[3], 2)
    cs_ = m_rect(P, 70.0, 56.0, 20.0, 9.0)
    lames(P, cs_, Ls * 1.4, larg=3.0, graine=942, vertical=False, alb=0.6, noeuds=0.3)
    lisere(P, cs_, R_BOIS[1], 0, 1)
    horloge(P, 76.0, 53.0, 3.0, Lm + 0.2, sorte=0, heure=0.3, d=0.2)
    horloge(P, 84.6, 53.6, 2.4, Lm + 0.2, sorte=1, heure=0.7, d=0.8)
    chat(P, 22.0, 70.0, coul=GR2)
    pg.souris(P, 100.0, 64.6, sens=1, coul=GR3)

    # ================================================================================================== premier plan
    tab.plan("premier", 1.0)
    # À contre-jour, tout près : un globe de verre et sa montre en bas à gauche ; une grande roue dentée qui tourne en
    # haut à droite, pendue à sa chaîne ; un carillon de tubes en haut à gauche.
    gx, gy = 6.0, 72.0
    P.rampe(m_ell(P, gx, gy + 6.0, 10.0, 2.6), 0.3, R_BOIS, 0.5)
    glob = (m_ell(P, gx, gy - 6.0, 8.0, 9.0) | m_rect(P, gx - 8.0, gy - 6.0, 16.0, 12.0)) & (Y < gy + 5.6)
    P.rampe(glob & ~((m_ell(P, gx, gy - 6.0, 7.2, 8.2) | m_rect(P, gx - 7.2, gy - 6.0, 14.4, 12.0))), 0.5, [NU2, NU4, BM2, BM4], 0.5)
    P.remplir(glob & (np.abs(X - gx + 4.6 - 0.1 * (Y - gy)) < 0.5) & (Y > gy - 10.0), BM3)
    horloge(P, gx, gy - 1.0, 4.0, Lm * 0 + 0.7, sorte=0, heure=0.42, d=0.1)
    P.rect(gx - 0.5, gy + 3.0, 1.0, 2.6, GO2)
    pg.roue(P, 180.0, -4.0, 13.0, 14, R_BOIS[1], R_BOIS[3], R_BOIS[0], angle=2 * math.pi * p / 14.0)
    lisere(P, P.a == R_BOIS[1], LAITON, -1, 0, cond=Y > -8)
    for k, cx_ in enumerate((92.0, 96.0, 100.0, 104.0)):
        bal = 0.3 * onde(p, 0.2 * k)
        P.trait(cx_, -16.0, cx_ + bal, -9.0 + k * 1.6, R_BOIS[1])
        P.rampe(m_rect(P, cx_ - 0.7 + bal, -9.0 + k * 1.6, 1.4, 9.0 + k * 1.4), 0.4 + 0.3 * (X < cx_ + bal), R_LAITON, 0.5)
    P.rampe(Y > 78.6, 0.2 + 0 * X, R_BOIS, 0.5)


# =====================================================================================================================
# Le sentier des douaniers : large comme deux pieds, en haut de la falaise, dans le brouillard du matin. À gauche les
# ajoncs qui piquent ; à droite, rien : la brume, et dessous, très loin, la mer qui mâche des cailloux. Au premier
# virage, l'écriteau qui penche. Sur la pointe, la cabane de guet en planches grises, sa petite fenêtre tournée vers le
# phare. Le sentier est le sol (y = 64) et s'arrête au bord (x = 130).
# =====================================================================================================================
R_ROCHE = cs("#232a3a", "#3a4357", "#566079", "#7f889c", "#a9b0bf", "#cfd3da", "#ebe8e6")
R_LANDE = cs("#0f2436", "#17384a", "#245566", "#3d7a84", "#6aa8a4", "#b7d8c8")
AJONC1, AJONC2 = cs("#d9a82e", "#f5d76e")


@decor("phare-eteint", "sentier-douaniers", soleil=(150.0, -4.0), tons=AUBE, nom="Le sentier des douaniers", matiere=True)
def sentier_douaniers(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tout = np.ones(X.shape, dtype=bool)
    SOLEIL = (150.0, -4.0)
    MER = 58.0                                                  # l'horizon noyé, en contrebas

    # ============================================================================================================ le ciel
    tab.plan("ciel", 0.0)
    P.rampe(tout, 0.56 + 0.004 * (Y + 16.0) + 0.2 * (pg.fbm((X + onde(p)) / 46.0, Y / 10.0, 4, 950) - 0.5)
            + 0.3 * np.exp(-(np.hypot(X - SOLEIL[0], Y - SOLEIL[1]) / 30.0) ** 2), T.CIEL[3:], 0.7)
    ds = np.hypot(X - SOLEIL[0], Y - SOLEIL[1])
    P.remplir(ds < 4.0, T.CIEL[11])                                                                # le soleil, un disque pâle dans le brouillard
    P.remplir(ds < 3.2, BLANC)

    def nappe(y, epais, graine, tons, seuil=0.62, zone=None, pas=20.0):
        def dens(yy):
            return (0.4 + pg.fbm((X + 1.6 * onde(p, 0.013 * graine)) / pas, yy / 2.6, 3, graine)) * np.exp(-((yy - y - 1.0 * np.sin(X / 19.0 + graine)) / epais) ** 2) - seuil
        d = dens(Y)
        m = d > 0
        if zone is not None:
            m &= zone
        P.rampe(m, 0.3 + 1.5 * d + 1.8 * (d - dens(Y - 1.0)), tons, 0.6)

    tab.plan("lointains", 0.15)
    # Tout en bas à droite : la mer grise, la Dent-Creuse toute petite sur son rocher, des récifs et leur écume.
    large = X > -10
    P.rampe(large & (Y > MER - 12.0), 0.3 + 0.03 * (Y - MER + 12.0) + 0.16 * (pg.fbm((X + 2.0 * onde(p)) / 9.0, Y / 1.2, 3, 951) - 0.5), [T.CIEL[8], T.CIEL[6], T.CIEL[5], T.CIEL[4], T.CIEL[3]], 0.6)
    phare(P, 170.0, MER - 13.0, 20.0, T.CIEL[4], T.CIEL[7])
    for i in range(7):
        t = (p + i / 7.0) % 1.0
        rx, ry = 138.0 + i * 8.6 + 3.0 * math.sin(i * 2.2), MER - 6.0 + 3.6 * (i % 3) + 2.0 * (i % 2)
        if i % 2:
            P.poly([(rx - 1.8, ry + 0.6), (rx - 0.4, ry - 1.6), (rx + 1.6, ry + 0.6)], T.CIEL[3])
        P.trait(rx - 2.4 - t, ry + 0.8, rx + 2.4 + t, ry + 0.8, BLANC if t < 0.5 else T.CIEL[9])
    nappe(MER - 14.0, 3.0, 952, [T.CIEL[8], T.CIEL[9], T.CIEL[10], T.CIEL[11]], 0.58, zone=large)
    nappe(MER - 4.0, 2.6, 953, [T.CIEL[7], T.CIEL[9], T.CIEL[10]], 0.62, zone=large)
    nappe(MER + 8.0, 4.0, 954, [T.CIEL[8], T.CIEL[9], T.CIEL[10], T.CIEL[11]], 0.5, zone=large)
    for i in range(3):
        goeland(P, 150.0 + 12.0 * i + 3.0 * onde(p, 0.2 * i), 24.0 + 5.0 * i + onde(p, 0.3 * i), pose=False)

    # ======================================================================================================== la falaise
    tab.plan("moyen", 0.5)
    # ---- La pointe, au fond : une lande qui monte, la cabane de guet dessus. Le brouillard la pâlit.
    fp = lambda x: 47.0 - 13.0 * np.exp(-((x - 64.0) / 30.0) ** 2) + 5.0 * np.clip((x - 96.0) / 22.0, 0, 1) ** 1.6 * 4.0 + 0.8 * (pg.fbm(x / 5.0, 0 * x, 3, 955) - 0.5)
    pointe = (Y > fp(X)) & (X < 118.6)
    P.rampe(pointe, 0.42 + 0.34 * (pg.fbm(X / 6.0, Y / 2.4, 3, 956) - 0.5) - 0.004 * (Y - fp(X)), [T.CIEL[3], T.CIEL[4], R_LANDE[3], T.CIEL[5], R_LANDE[4], T.CIEL[7]], 0.5)
    lisere(P, pointe, T.CIEL[9], 0, -1, cond=pg.fbm(X / 2.6, 0 * X, 2, 957) > 0.4)
    fal_p = pointe & (X > 108.0 - 0.3 * (Y - 47.0))                                                # son flanc, à pic
    P.rampe(fal_p, 0.4 + 0.3 * (pg.fbm(X / 1.6, Y / 5.0, 3, 958) - 0.5), [T.CIEL[2], T.CIEL[3], T.CIEL[4], T.CIEL[5]], 0.5)
    # La cabane : des planches grises debout, un toit de tôle, une cheminée de poêle, la petite fenêtre.
    cx0, cy0, cw, chh = 56.0, 22.0, 22.0, 13.6
    cab = m_rect(P, cx0, cy0, cw, chh)
    lames(P, cab, 0.86 + 0.1 * (X - cx0) / cw, larg=2.2, graine=959, vertical=True, rampe=R_ROCHE, alb=0.66, sens=1, noeuds=0.3)
    toit = P.masque_poly([(cx0 - 2.0, cy0 + 0.4), (cx0 + cw + 2.4, cy0 - 1.6), (cx0 + cw + 2.0, cy0 - 4.6), (cx0 - 1.6, cy0 - 2.6)])
    P.rampe(toit, 0.5 + 0.14 * ((np.floor(X / 1.6) % 2) == 0) + 0.02 * (X - cx0), R_ROCHE[:5], 0.5)
    lisere(P, toit, R_ROCHE[6], 0, -1)
    P.rect(cx0 + 4.0, cy0 - 9.0, 1.6, 7.0, R_ROCHE[1])                                             # le tuyau du poêle
    P.rect(cx0 + 3.6, cy0 - 9.6, 2.4, 0.8, R_ROCHE[0])
    fumerolle(P, cx0 + 4.8, cy0 - 10.4, h=13.0, n=4, d=0.1, coul=T.CIEL[10], force=0.45, large=1.0)
    P.rect(cx0 + 13.0, cy0 + 3.0, 5.6, 4.6, R_ROCHE[0])                                            # la fenêtre, tournée vers le phare
    P.rect(cx0 + 13.6, cy0 + 3.6, 4.4, 3.4, LU4 if int(p * 8) % 7 else LU3)
    P.rect(cx0 + 15.6, cy0 + 3.6, 0.4, 3.4, R_ROCHE[0])
    P.rect(cx0 + 16.6, cy0 + 4.6, 0.8, 0.8, ENCRE)                                                 # deux ronds noirs : des jumelles
    P.rect(cx0 + 14.4, cy0 + 4.6, 0.8, 0.8, ENCRE)
    porte = m_rect(P, cx0 + 3.0, cy0 + 4.0, 5.0, chh - 4.0)
    lames(P, porte, 0.6 + 0 * X, larg=1.7, graine=960, vertical=True, rampe=R_ROCHE, alb=0.6, noeuds=0)
    P.point(cx0 + 7.0, cy0 + 9.0, LAITON2)
    P.trait(cx0 + cw + 3.0, cy0 - 6.0, cx0 + cw + 3.0, cy0 + chh, R_ROCHE[1], 2)                    # le mât à signaux, sa flamme
    v_ = onde(p)
    P.poly([(cx0 + cw + 3.4, cy0 - 6.0), (cx0 + cw + 8.4, cy0 - 5.0 + 0.6 * v_), (cx0 + cw + 3.4, cy0 - 3.4)], LU2)
    nappe(52.0, 2.2, 961, [T.CIEL[8], T.CIEL[9], T.CIEL[10]], 0.66, zone=X < 112)                   # le brouillard au pied de la pointe

    # ---- La lande et le sentier : l'herbe rase, la bruyère, le ruban de terre battue qui serpente vers la cabane.
    ft = lambda x: 61.4 + 1.4 * np.sin(x / 23.0) + 0.6 * (pg.fbm(x / 4.0, 0 * x + 0.2, 3, 962) - 0.5)       # le haut du plateau, devant
    bord = 131.0 + 0.5 * (Y - 62.0) + 2.6 * (pg.fbm(Y / 3.0, 0 * Y + 0.4, 3, 963) - 0.5)            # le bord, incertain
    plateau = (Y > ft(X)) & (X < bord)
    herbe = pg.fbm(X / 5.0, Y / 1.4, 3, 964)
    P.rampe(plateau, 0.44 + 0.5 * (herbe - 0.5) + 0.008 * (X - 20.0) - 0.006 * (Y - 62.0), R_LANDE, 0.5)
    chem = plateau & (np.abs(Y - 66.0 - 1.6 * np.sin(X / 16.0) - 0.02 * (X - 60.0)) < 1.8 + 0.3 * pg.fbm(X / 3.0, 0 * X, 2, 965))
    P.rampe(chem, 0.6 + 0.3 * (pg.fbm(X / 2.0, Y / 0.8, 2, 966) - 0.5), R_PLATRE[3:], 0.5)
    lisere(P, chem, R_LANDE[1], 0, 1)
    for i in range(22):                                         # des cailloux dans le sentier
        cxk = 6.0 + 122.0 * hz(i, 1, 967)
        cyk = 66.0 + 1.6 * math.sin(cxk / 16.0) + 0.02 * (cxk - 60.0) + (hz(i, 2, 967) - 0.5) * 2.4
        P.ell(cxk, cyk, 0.9, 0.5, R_ROCHE[4])
        P.point(cxk - 0.3, cyk - 0.3, R_ROCHE[6])
    for i in range(46):                                         # la bruyère, par touffes violettes
        hx_ = 4.0 + 122.0 * hz(i, 1, 968)
        hy_ = 70.0 + 9.0 * hz(i, 2, 968)
        if hx_ < 126 + 0.5 * (hy_ - 62):
            P.point(hx_, hy_, T.VIOLET if i % 2 else VI2, 2 if i % 3 == 0 else 1)
            P.point(hx_ + 0.6, hy_ + 0.6, R_LANDE[2])
    lisere(P, plateau, R_LANDE[5], 0, -1, cond=pg.fbm(X / 2.0, 0 * X, 2, 969) > 0.4)
    # ---- La falaise : des strates de schiste qui plongent dans la brume ; des touffes d'armérie dans les fentes.
    fal = (X >= bord) & (X < bord + 26.0 + 0.6 * (Y - 62.0)) & (Y > ft(X) + 0.6 + 0.3 * (X - bord))
    strate = pg.fbm((X - bord) / 1.6 + 0.2 * Y, Y / 6.0, 3, 970)
    P.rampe(fal, 0.6 + 0.5 * (strate - 0.5) - 0.012 * (X - bord) - 0.01 * (Y - 62.0) + 0.1 * (np.sin((Y + 0.4 * (X - bord)) * 1.3) > 0.6), R_ROCHE, 0.5)
    lisere(P, fal, R_ROCHE[6], -1, 0, cond=pg.fbm(Y / 2.0, 0 * Y, 2, 971) > 0.5)
    for i in range(7):
        ax_ = 134.0 + 16.0 * hz(i, 1, 972)
        ay_ = 66.0 + 12.0 * hz(i, 2, 972)
        P.ell(ax_, ay_, 1.4, 0.8, R_LANDE[2])
        P.point(ax_, ay_ - 0.8, ROSE2 if i % 2 else T.VIOLET, 2)
    # ---- L'écriteau qui penche, au premier virage ; trois piquets et une corde, pour dire où est le bord.
    px_, py_ = 116.0, 64.0
    P.trait(px_, py_ + 1.0, px_ - 2.6, py_ - 15.0, R_BOIS[3], P.ep(0.9))
    P.trait(px_ + 0.4, py_ + 1.0, px_ - 2.2, py_ - 15.0, R_BOIS[6], 1)
    pn = P.masque_poly([(px_ - 12.0, py_ - 14.0), (px_ + 5.4, py_ - 17.0), (px_ + 6.4, py_ - 10.6), (px_ - 11.0, py_ - 7.4)])
    lames(P, pn, 0.9 + 0 * X, larg=3.4, graine=973, vertical=False, rampe=R_PLATRE, alb=0.8, noeuds=0.4)
    lisere(P, pn, R_PLATRE[2], 0, 1)
    P.poly([(px_ - 9.0, py_ - 10.4), (px_ - 6.0, py_ - 14.0), (px_ - 3.4, py_ - 11.2)], R_NUIT[2])    # une falaise, un pas, le vide
    P.point(px_ - 1.4, py_ - 12.0, R_NUIT[2], 2)
    P.point(px_ + 0.6, py_ - 12.6, R_NUIT[2], 2)
    P.trait(px_ + 2.4, py_ - 14.6, px_ + 4.4, py_ - 11.6, LU2, 2)
    for i, qx in enumerate((92.0, 122.0, 127.0)):
        qy = float(ft(np.array([qx]))[0]) + 1.6 + i * 2.0
        P.trait(qx, qy + 2.0, qx + (0.6 if i else -0.4), qy - 5.0, R_BOIS[3], 2)
        P.point(qx + (0.6 if i else -0.4), qy - 5.2, R_BOIS[6])
    P.courbe([(92.0 - 0.4, 59.0), (107.0, 62.6 + 0.3 * onde(p)), (122.6, 61.6)], GO2, 1)
    P.courbe([(122.6, 61.6), (125.0, 64.6 + 0.2 * onde(p, 0.3)), (127.6, 63.6)], GO2, 1)
    # ---- Les ajoncs, à gauche : des buissons d'épines sarcelle, piqués de fleurs jaunes ; ils remuent au vent.
    for i, (ax_, ay_, r) in enumerate(((2.0, 60.0, 9.0), (16.0, 58.4, 7.0), (72.0, 60.6, 5.0), (46.0, 60.0, 4.4))):
        vent = 0.3 * onde(p, 0.1 * i)
        boules = [(ax_ + (hz(k, i, 974) - 0.5) * r * 1.8 + vent, ay_ - hz(k, i + 5, 974) * r * 0.7, r * (0.3 + 0.3 * hz(k, i + 9, 974))) for k in range(9)]
        mb = P.volumes(boules, R_LANDE[:5], (0.3, -0.6, 0.5), plancher=ay_ + 2.0, grain=0.4, graine=975 + i)
        for k in range(int(r * 3.4)):
            fx_, fy_ = ax_ + (hz(k, i, 976) - 0.5) * r * 1.8 + vent, ay_ + 1.0 - hz(k, i + 3, 976) * r * 0.9
            if mb[min(P.H - 1, max(0, P.py(fy_))), min(P.Wt - 1, max(0, P.px(fx_)))]:
                P.point(fx_, fy_, AJONC2 if k % 3 else AJONC1, 2 if k % 4 == 0 else 1)
    # Le gros rocher derrière lequel on peut se cacher ; un lapin de garenne guette derrière.
    rx_, ry_ = 38.0, 62.6
    rm = (m_ell(P, rx_, ry_ - 3.4, 6.6, 5.0) | m_ell(P, rx_ + 3.6, ry_ - 2.0, 4.6, 3.4)) & (Y < ry_ + 0.6)
    P.rampe(rm, 0.56 + 0.2 * (X - rx_) / 6.6 - 0.26 * (Y - ry_ + 3.4) / 5.0 + 0.2 * (pg.fbm(X / 1.6, Y / 1.6, 3, 977) - 0.5), R_ROCHE, 0.5)
    lisere(P, rm, R_ROCHE[6], 0, -1, cond=X > rx_ - 2)
    P.remplir(rm & (pg.fbm(X / 1.2, Y / 1.2, 2, 978) > 0.66), AJONC1)                               # du lichen
    if int(p * 8) % 8 < 5:
        P.ell(rx_ - 7.4, ry_ - 2.4, 1.3, 1.6, R_PLATRE[5])                                         # le lapin
        P.trait(rx_ - 7.8, ry_ - 3.8, rx_ - 8.2, ry_ - 6.2, R_PLATRE[5], 2)
        P.point(rx_ - 7.0, ry_ - 2.8, ENCRE)

    # ================================================================================================== premier plan
    tab.plan("premier", 1.0)
    # Tout près : des herbes hautes que le vent couche, un ajonc en fleur dans le coin gauche, des gouttes de brume.
    for i in range(90):
        gx = 198.0 * hz(i, 1, 979) - 3.0
        if 126 < gx < 150:
            continue
        h = 3.0 + 6.0 * hz(i, 2, 979) + (4.0 if gx < 24 or gx > 170 else 0.0)
        pen = 1.6 + 1.4 * onde(p, hz(i, 3, 979) * 0.3)
        P.courbe([(gx, 80.4), (gx + pen * 0.3, 80.4 - h * 0.6), (gx + pen, 80.4 - h)], (R_LANDE[0], R_LANDE[1], R_LANDE[2], R_LANDE[3])[int(hz(i, 4, 979) * 4)], 2 if hz(i, 5, 979) < 0.3 else 1, 1)
        if hz(i, 6, 979) < 0.16:
            P.point(gx + pen, 80.0 - h, R_PLATRE[7], 2)           # un épi
    boules = [(2.0 + 16.0 * hz(k, 1, 980), 78.0 - 7.0 * hz(k, 2, 980), 2.6 + 2.6 * hz(k, 3, 980)) for k in range(10)]
    mb = P.volumes(boules, R_LANDE[:4], (0.3, -0.6, 0.5), grain=0.4, graine=981)
    for k in range(34):
        fx_, fy_ = -2.0 + 24.0 * hz(k, 4, 982), 80.0 - 12.0 * hz(k, 5, 982)
        if mb[min(P.H - 1, max(0, P.py(fy_))), min(P.Wt - 1, max(0, P.px(fx_)))]:
            P.point(fx_ + 0.2 * onde(p, 0.1 * k), fy_, AJONC2 if k % 3 else AJONC1, 2)
    falp = (X > 150.0 + 2.0 * np.sin(Y / 4.0)) & (Y > 70.0 - 0.5 * (X - 150.0) + 1.6 * (pg.fbm(X / 3.0, 0 * X, 3, 983) - 0.5))        # un éperon de roche, en bas à droite
    P.rampe(falp, 0.34 + 0.4 * (pg.fbm(X / 1.6 + 0.3 * Y, Y / 4.0, 3, 984) - 0.5) - 0.006 * (Y - 60.0), R_ROCHE[:5], 0.5)
    lisere(P, falp, R_ROCHE[5], 0, -1)
    goeland(P, 176.0, 57.6, sens=-1, pose=True)
    for i in range(3):                                          # la brume qui passe devant
        t = (p + i / 3.0) % 1.0
        P.trait(60.0 + 40.0 * i + 10.0 * t, 74.0 + 2.0 * i, 70.0 + 40.0 * i + 10.0 * t, 74.0 + 2.0 * i, T.CIEL[10])


# =====================================================================================================================
# Le Souffleur : une grotte marine sous le rocher du phare, à marée basse. On est dedans. À droite, la gueule de la
# grotte s'ouvre sur la mer et la lune ; à gauche, une lanterne posée sur un rocher éclaire les bidons alignés et le
# conduit sombre qui monte dans la pierre, avec ses crampons de fer. Le canot est tiré au sec sur le sable mouillé.
# La grotte respire : au fond, un souffle d'embrun chaque fois que la vague se retire.
# Repères : lanterne (56, 50), mer sensible (100..192, 54..64), rond (160, 60).
# =====================================================================================================================
R_GROTTE = cs("#070a16", "#0d1326", "#1c2336", "#30384c", "#4b4c60", "#6f6468", "#977d6c", "#c09a72", "#e6c088")
R_SABLE = cs("#0d1326", "#1d2a44", "#2c3c5c", "#44567a", "#65789c", "#8ea0bf", "#b9c6dc")


@decor("phare-eteint", "grotte-souffleur", soleil=(150.0, 18.0), tons=PHARE, nom="Le Souffleur", matiere=True)
def grotte_souffleur(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tout = np.ones(X.shape, dtype=bool)
    LUNE = (150.0, 18.0)
    HOR = 46.0
    LX, LY = 56.0, 46.0                                         # la lanterne
    vac = 1.0 + 0.06 * onde(p * 2) + 0.03 * onde(p * 3, 0.3)

    # ============================================================================================== dehors, par la gueule
    tab.plan("ciel", 0.0)
    P.horizon, P.ciel_haut, P.halo = HOR, 0.08, 0.36
    vc = pg.valeur_ciel(P, X, Y)
    P.rampe(tout, 0.05 + 0.64 * vc, T.CIEL, 0.75)
    dl = np.hypot(X - LUNE[0], Y - LUNE[1])
    P.rampe(dl < 12.0, 0.3 + 0.7 * np.clip(1 - dl / 12.0, 0, 1) ** 1.5 + 0.5 * vc, T.CIEL[3:10], 0.6)
    P.remplir(dl < 4.0, T.CIEL[10])
    P.remplir(dl < 3.4, T.SOL)
    for i in range(20):
        ex, ey = 96.0 + 96.0 * hz(i, 1, 1000), -4.0 + 30.0 * hz(i, 2, 1000)
        if math.hypot(ex - LUNE[0], ey - LUNE[1]) > 16.0 and (p + hz(i, 3, 1000)) % 1.0 < 0.7:
            P.point(ex, ey, T.CIEL[8])

    def nappe(y, epais, graine, tons, seuil=0.64):
        def dens(yy):
            return (0.4 + pg.fbm((X + 1.4 * onde(p, 0.013 * graine)) / 16.0, yy / 2.4, 3, graine)) * np.exp(-((yy - y - np.sin(X / 19.0 + graine)) / epais) ** 2) - seuil
        d = dens(Y)
        P.rampe(d > 0, 0.3 + 1.5 * d + 1.6 * (d - dens(Y + 1.0)), tons, 0.6)

    nappe(30.0, 2.4, 1001, T.CIEL[4:9])
    tab.plan("lointains", 0.15)
    f1 = lambda x: HOR - 0.6 - 2.6 * np.clip((x - 150.0) / 40.0, 0, 1) ** 0.7 - 1.0 * pg.fbm(x / 6.0, 0 * x + 0.5, 3, 1002)
    P.remplir((Y > f1(X)) & (Y < HOR + 0.4) & (X > 146), T.CIEL[3])                                # Trébrume et ses lampes
    for i in range(8):
        lx_ = 152.0 + 40.0 * hz(i, 1, 1003)
        if (p + hz(i, 3, 1003)) % 1.0 < 0.9:
            P.point(lx_, HOR - 1.2 - 1.6 * hz(i, 2, 1003), LU4)
    nappe(HOR - 1.6, 1.6, 1004, T.CIEL[5:10])
    pg.miroir(P, tab.derriere(), HOR, fonce=(58.0, 10.0), eclats=0.95, rides=0.1, graine=1005, ronds=((160.0, 60.0, 0.0), (130.0, 52.0, 0.5)))
    for i in range(4):                                          # la vague qui vient mourir à l'entrée
        t = (p + i / 4.0) % 1.0
        yv = 60.0 + 4.0 * t
        P.remplir((np.abs(Y - yv - 0.6 * np.sin(X / 5.0 + i)) < 0.3) & (X > 96) & (pg.fbm(X / 3.0, 0 * X + i, 2, 1006) > 0.36 + 0.3 * t), BM4 if t < 0.5 else BM2)

    # ======================================================================================================== la grotte
    tab.plan("moyen", 0.5)
    # ---- La gueule : une arche déchiquetée. Tout ce qui n'est pas l'ouverture est de la roche.
    cx_, cy_ = 148.0, 40.0
    ang = np.arctan2(Y - cy_, X - cx_)
    rayon = np.hypot((X - cx_) / 52.0, (Y - cy_) / 44.0)
    bordg = 1.0 + 0.16 * (pg.fbm(ang * 2.2, 0 * ang + 0.3, 4, 1007) - 0.5) * 2.0 + 0.06 * np.sin(ang * 7.0)
    gueule = (rayon < bordg) & (Y < 66.0 + 0.04 * (X - 100.0))
    roche = ~gueule
    Lw = lumiere(P, [(LX, LY, 26.0, 1.2)], 0.0)                                                     # la lanterne
    Lc = 0.1 + 0.5 * np.exp(-np.clip(rayon - bordg, 0, None) / 0.16)                               # la lune, sur le pourtour de l'arche
    pan = pg.fbm(X / 7.0 + 0.4 * Y, Y / 4.0, 4, 1008)
    strate = 0.1 * (pg.fbm((X + 0.5 * Y) / 14.0, (Y - 0.5 * X) / 1.6, 3, 10081) - 0.5) * 2.0
    v = (0.5 + 0.7 * (pan - 0.5) + strate + 0.12 * (pg.fbm(X / 1.0, Y / 1.0, 2, 1009) - 0.5))
    chaud = Lw > 0.6 * Lc
    P.rampe(roche & ~chaud, v * (Lc + Lw) * 1.2, R_FROID, 0.5)
    P.rampe(roche & chaud, v * (Lc + Lw) * 1.1, R_GROTTE, 0.5)
    fiss = roche & (np.abs(pg.fbm(X / 11.0, Y / 5.0, 3, 1010) - 0.5) < 0.01)
    P.a[fiss] = R_GROTTE[0]
    lisere(P, gueule, BM2, -1, 0, cond=pg.fbm(Y / 2.0, 0 * Y, 2, 1011) > 0.4)                       # la lune ourle l'arche
    lisere(P, gueule, BM1, 0, -1, cond=pg.fbm(X / 2.0, 0 * X, 2, 1012) > 0.45)
    # Les stalactites de la voûte, qui gouttent ; des moules en grappes au bas des parois.
    for i in range(16):
        sx = 4.0 + 184.0 * hz(i, 1, 1013)
        l = 3.0 + 7.0 * hz(i, 2, 1013)
        y0 = -16.0 + (2.0 if not (100 < sx < 190) else -2.0)
        P.poly([(sx - 1.2, y0), (sx + 1.2, y0), (sx + 0.2, y0 + l)], R_GROTTE[1] if sx > 90 else R_GROTTE[2])
        P.trait(sx - 0.6, y0, sx + 0.1, y0 + l - 0.6, R_GROTTE[4] if sx < 90 else BM1)
        if i % 4 == 0:
            pg.goutte(P, sx + 0.2, y0 + l, 70.0, coul=BM3, d=hz(i, 3, 1013), flaque=BM3)
    for i in range(40):
        mx_ = 198.0 * hz(i, 1, 1014) - 3.0
        my_ = 58.0 + 6.0 * hz(i, 2, 1014)
        if roche[min(P.H - 1, P.py(my_)), min(P.Wt - 1, max(0, P.px(mx_)))]:
            P.ell(mx_, my_, 0.6, 0.9, R_GROTTE[0])
            P.point(mx_ - 0.2, my_ - 0.4, NU3)
    # ---- Le conduit qui monte dans la pierre : un trou noir, des crampons de fer, un souffle d'embrun.
    kx, ky = 24.0, 8.0
    cond = m_ell(P, kx, ky, 7.0, 13.0) & (pg.fbm(X / 3.0, Y / 3.0, 3, 1015) > 0.24)
    P.rampe(cond, 0.1 + 0.3 * np.clip((Y - ky) / 13.0, 0, 1) * Lw, R_GROTTE[:4], 0.5)
    lisere(P, cond, R_GROTTE[6], 1, 0, cond=Y > ky)
    for k in range(5):
        P.rect(kx - 2.6, ky - 8.0 + k * 4.6, 5.2, 0.6, R_CUIVRE[1] if k % 2 else R_GROTTE[4])
        P.rect(kx - 2.6, ky - 8.0 + k * 4.6, 0.5, 1.6, R_GROTTE[4])
        P.rect(kx + 2.2, ky - 8.0 + k * 4.6, 0.5, 1.6, R_GROTTE[4])
    if p < 0.5:                                                 # la grotte respire
        fumerolle(P, kx, ky + 12.0, h=-10.0, n=3, d=0.0, coul=BM1, force=0.5 * (1 - 2 * p), large=1.6)
    # ---- Le sable mouillé : il boit la lune vers la gueule, la lanterne à gauche ; des rides, des flaques, du goémon.
    fs = lambda x: 66.0 + 1.2 * np.sin(x / 21.0) + 0.6 * (pg.fbm(x / 5.0, 0 * x, 3, 1016) - 0.5) + 0.03 * (x - 100.0) * (x > 100)
    sable = Y > fs(X)
    Lsc = 0.1 + 0.76 * np.exp(-((X - 152.0) / 40.0) ** 2) * np.clip(1 - (Y - 62.0) / 30.0, 0.3, 1)
    Lsw = lumiere(P, [(LX, 66.0, 24.0, 1.0 * vac)], 0.0)

    def ombre(cx, cy, rx, ry, f=0.5):
        nonlocal Lsc, Lsw
        o = 1 - f * np.clip(1.3 - np.hypot((X - cx) / rx, (Y - cy) / ry), 0, 1)
        Lsc, Lsw = Lsc * o, Lsw * o

    ombre(150.0, 73.6, 20.0, 1.8, 0.6)
    ombre(84.0, 71.4, 16.0, 1.4, 0.5)
    ride = np.sin((Y - 66.0) * 3.4 + 2.4 * pg.fbm(X / 14.0, Y / 3.0, 3, 1017) * 3.0)
    vs = 0.6 + 0.1 * ride + 0.24 * (pg.fbm(X / 6.0, Y / 2.0, 3, 1018) - 0.5)
    flaque = sable & (pg.fbm(X / 8.0, (Y - 66.0) / 1.5, 3, 1019) > 0.62)
    vs = np.where(flaque, vs * 0.6 + 0.3, vs)
    chaud = Lsw > 1.2 * Lsc
    P.rampe(sable & ~chaud, vs * (Lsc + Lsw) * 1.2, R_SABLE, 0.5)
    P.rampe(sable & chaud, vs * (Lsc + Lsw) * 1.15, R_GROTTE, 0.5)
    lisere(P, sable, BM1, 0, -1, cond=(X > 100) & (pg.fbm(X / 2.0, 0 * X, 2, 1020) > 0.4))
    dx = X - LUNE[0] - (hz(P.YI, 3, 1021) - 0.5) * 6.0
    P.a[flaque & (np.abs(dx) < 1.0 + 2.0 * hz(P.YI, 4, 1021)) & (hz(P.YI, 6 + int(p * 4) % 2, 1021) < 0.5)] = BM4          # la lune dans les flaques
    dx = X - LX - (hz(P.YI, 5, 1021) - 0.5) * 4.0
    P.a[sable & (Y > 68.0) & (np.abs(dx) < 0.6 + 1.2 * hz(P.YI, 7, 1021)) & (hz(P.YI, 8 + int(p * 8) % 2, 1021) < 0.4)] = LU3  # la lanterne aussi
    for i, (gx, gy, r) in enumerate(((108.0, 70.0, 6.0), (176.0, 72.0, 7.0), (12.0, 73.0, 6.0), (68.0, 76.0, 5.0))):
        tas = m_ell(P, gx, gy, r, r * 0.24) & (pg.fbm(X / 1.6, Y / 0.6, 2, 1022 + i) > 0.44)
        P.rampe(tas, 0.1 + 0.6 * (pg.fbm(X / 1.0, Y / 0.6, 2, 1026 + i) - 0.3), [R_GROTTE[0], T.S0, T.S1, T.S2, T.S3], 0.5)
    # ---- La lanterne sur son rocher ; les bidons d'huile alignés, marqués à la craie.
    rm = m_ell(P, LX, 58.0, 9.0, 7.0) & (Y < 66.6) & (Y > 51.0 + 0.9 * (pg.fbm(X / 2.0, 0 * X, 3, 1030) - 0.5) * 3.0)
    P.rampe(rm, (0.5 + 0.4 * (pg.fbm(X / 3.0 + 0.4 * Y, Y / 2.0, 3, 1031) - 0.5)) * (0.3 + 0.9 * np.clip(1 - (Y - 51.0) / 13.0, 0, 1)) * vac, R_GROTTE, 0.5)
    halo(P, LX, LY, 16.0, LU2, 0.34 * vac)
    P.rect(LX - 2.0, 50.0, 4.0, 1.0, R_GROTTE[1])
    P.rect(LX - 1.6, 45.0, 3.2, 5.0, LU4 if int(p * 8) % 5 else LU3)
    P.rect(LX - 0.6, 46.0, 1.2, 3.0, LU5)
    P.rect(LX - 2.0, 44.2, 4.0, 0.9, R_GROTTE[1])
    for dxl in (-1.8, 1.4):
        P.rect(LX + dxl, 45.0, 0.4, 5.0, R_GROTTE[1])
    P.courbe([(LX - 1.8, 44.2), (LX, 41.6), (LX + 1.8, 44.2)], R_GROTTE[3], 1)
    for i in range(6):
        bx_ = 72.0 + i * 5.6
        by_ = float(fs(np.array([bx_]))[0]) + 3.6 + (i % 2) * 0.5
        bid = m_rect(P, bx_ - 2.2, by_ - 7.0, 4.4, 7.0)
        Lb = float(np.clip(1.1 - (bx_ - LX) / 50.0, 0.3, 1.0)) * vac
        P.rampe(bid, (0.3 + 0.5 * np.clip(1 - (X - bx_ + 2.2) / 4.4, 0, 1)) * Lb, R_CUIVRE, 0.5)
        P.rect(bx_ - 2.2, by_ - 4.0, 4.4, 0.5, R_GROTTE[0])
        P.rect(bx_ - 0.8, by_ - 8.2, 1.6, 1.2, R_GROTTE[4])
        P.courbe([(bx_ + 0.8, by_ - 7.6), (bx_ + 2.2, by_ - 8.4), (bx_ + 2.2, by_ - 6.6)], R_GROTTE[4], 1)
        P.trait(bx_ - 1.4, by_ - 2.6, bx_ + 0.6, by_ - 1.4, R_PAPIER[3])                              # la marque à la craie
        if i % 2:
            P.trait(bx_ - 1.4, by_ - 1.4, bx_ + 0.6, by_ - 2.6, R_PAPIER[3])
    # ---- Le canot tiré au sec, à contre-lune ; ses avirons, son grappin, l'amarre.
    qx, qy = 150.0, 72.6
    un = (X - qx) / 19.0
    tont = qy - 6.4 - 1.0 * un ** 2 * 1.4
    quil = qy - 4.0 * np.clip(np.abs(un) - 0.6, 0, 1) ** 1.6 * 4.0
    cq = (Y >= tont) & (Y <= quil) & (np.abs(un) <= 1)
    t = np.clip((Y - tont) / np.maximum(quil - tont, 0.2), 0, 1)
    P.rampe(cq, 0.2 + 0.3 * np.exp(-((t - 0.2) / 0.14) ** 2) + 0.1 * (un < -0.3) * vac - 0.06 * (((t * 5) % 1.0) < 0.14), [ENCRE, NU0, NU1, NU2, NU3, BM1], 0.5)
    lisere(P, cq, BM3, 0, -1)
    P.trait(qx - 14.0, qy - 7.4, qx + 10.0, qy - 9.4, R_BOIS[4], 2)                                  # un aviron en travers
    P.trait(qx + 19.0, qy - 6.0, 190.0, 68.0 + 0.3 * onde(p), GO2)
    P.trait(qx - 19.0, qy - 5.6, qx - 24.0, qy + 1.0, R_BOIS[3], 2)                                  # la béquille
    pg.yeux(P, 6.0, 60.0, coul=LU4, d=0.3, ecart=1.8)                                              # un crabe, dans une fente
    for i in range(5):                                          # des puces de mer sautent autour de la lanterne
        tt = (p + hz(i, 0, 1032)) % 1.0
        if tt < 0.3:
            P.point(44.0 + 26.0 * hz(i, 1, 1032), 66.0 - 5.0 * math.sin(tt / 0.3 * math.pi), R_GROTTE[7])

    # ================================================================================================== premier plan
    tab.plan("premier", 1.0)
    # La voûte tout près, en haut ; deux blocs en bas, noirs, luisants ; l'eau qui ruisselle.
    vo = Y < -9.0 + 5.0 * (pg.fbm(X / 9.0, 0 * X + 0.6, 4, 1033) - 0.5) * 2.0 + 0.0008 * (X - 96.0) ** 2
    P.rampe(vo, 0.2 + 0.4 * (pg.fbm(X / 4.0, Y / 2.0, 3, 1034) - 0.5), R_GROTTE[:4], 0.5)
    lisere(P, vo, R_GROTTE[5], 0, 1, cond=(X < 96) & (pg.fbm(X / 2.0, 0 * X, 2, 1035) > 0.5))
    lisere(P, vo, BM1, 0, 1, cond=(X >= 96) & (pg.fbm(X / 2.0, 0 * X, 2, 1035) > 0.5))
    fb = lambda x: 79.0 - 9.0 * np.exp(-((x + 2.0) / 12.0) ** 2) - 7.0 * np.exp(-((x - 196.0) / 12.0) ** 2) + 1.0 * (pg.fbm(x / 3.0, 0 * x, 3, 1036) - 0.5)
    bl = Y > fb(X)
    P.rampe(bl, 0.2 + 0.4 * (pg.fbm(X / 3.0 + 0.3 * Y, Y / 1.6, 3, 1037) - 0.5), R_GROTTE[:4], 0.5)
    lisere(P, bl, R_GROTTE[6], 0, -1, cond=(X < 30) & (pg.fbm(X / 2.0, 0 * X, 2, 1038) > 0.4))
    lisere(P, bl, BM2, 0, -1, cond=(X > 160) & (pg.fbm(X / 2.0, 0 * X, 2, 1038) > 0.4))


# =====================================================================================================================
# La cave du phare : le sous-sol rond de la tour, à la lueur d'une lanterne. Le mur tourne : des assises de granit qui
# se resserrent vers les bords. Le tas de charbon à gauche, les rangées de bidons d'huile marqués à la craie à droite,
# le panier pendu à sa poulie (la clé) et la lanterne accrochée à sa corde, l'escalier de pierre en colimaçon qui
# monte dans le noir, la trappe du puits dans le dallage. Le sol est à y = 76.
# =====================================================================================================================
@decor("phare-eteint", "cave-du-phare", soleil=(96.0, 44.0), tons=PHARE, nom="La cave du phare", matiere=True)
def cave_du_phare(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tout = np.ones(X.shape, dtype=bool)
    LX, LY = 96.0, 44.0                                         # la lanterne, pendue au-dessus du panier
    SOL = 62.0
    vac = 1.0 + 0.06 * onde(p * 2) + 0.03 * onde(p * 3, 0.3)
    bal = 0.5 * onde(p, 0.2)                                    # le panier se balance à peine

    # ====================================================================================================== le mur rond
    tab.plan("ciel", 0.0)
    nx = (X - 96.0) / 112.0                                     # où l'on est sur le cylindre, vu de l'intérieur
    ang = np.arcsin(np.clip(nx, -0.999, 0.999))
    Lm = lumiere(P, [(LX, LY, 58.0, 1.5)], 0.16) * (0.55 + 0.45 * np.cos(ang) ** 2)
    r = np.floor((Y + 16.0) / 6.0)
    wv = 0.19 * (0.72 + 0.56 * hz(r, 2, 1040))
    aa = ang + 3.0 * hz(r, 1, 1040)
    s_ = np.floor(aa / wv)
    du0, dv0 = (aa - s_ * wv) * 112.0 * np.cos(ang), (Y + 16.0) - r * 6.0
    du1, dv1 = (wv - (aa - s_ * wv)) * 112.0 * np.cos(ang), 6.0 - dv0
    ton = 0.76 + 0.48 * hz(s_, r, 1041)
    joint = (du0 < 0.42) | (dv0 < 0.42)
    sx = np.sign(LX - X)
    bev = 0.2 * ((du1 < 0.84) * sx - ((du0 < 1.26) & ~joint) * sx) + 0.16 * (((dv1 < 0.84) * 1.0 - ((dv0 < 1.26) & ~joint)) * np.sign(LY - Y))
    v = 0.6 * (ton + 0.3 * (pg.fbm(X / 1.1, Y / 1.1, 2, 1042) - 0.5)) + bev
    v = v - 0.16 * np.clip(pg.fbm(X / 2.6, Y / 26.0, 2, 1043) - 0.58, 0, 1) * 3.0                    # le salpêtre et les coulures
    v = np.where(joint, 0.22, v)
    P.rampe(tout, v * Lm, R_GROTTE, 0.5)
    salp = (pg.fbm(X / 4.0, Y / 3.0, 3, 1044) > 0.7) & (Y > 30)
    P.rampe(salp, 0.5 * Lm + 0.2, [R_GROTTE[2], R_GROTTE[4], GR3, GR4], 0.5)
    # La voûte : des sommiers de pierre noircis, un anneau de fer, la poulie.
    P.rampe(Y < -9.0 + 2.0 * np.cos(ang * 2.0), 0.16 + 0.2 * (pg.fbm(X / 3.0, Y / 1.5, 3, 1045) - 0.5), R_GROTTE[:4], 0.5)
    # Un soupirail tout en haut, à gauche : un rien de nuit bleue, et son barreau.
    sx0, sy0 = 30.0, -4.0
    P.rampe(m_rect(P, sx0 - 1.4, sy0 - 1.4, 10.8, 7.8), 0.3 * Lm + 0.06, R_GROTTE, 0.5)
    so = m_rect(P, sx0, sy0, 8.0, 5.0)
    P.rampe(so, 0.4 + 0.2 * (pg.fbm((X + onde(p)) / 3.0, Y / 2.0, 2, 1046) - 0.5), [NU1, NU2, NU3, NU4, BM1], 0.5)
    for dx in (2.6, 5.4):
        P.rect(sx0 + dx, sy0, 0.6, 5.0, ENCRE)
    P.remplir(m_rect(P, sx0 - 4.0, sy0 + 6.4, 14.0, 24.0) & (np.abs(X - sx0 - 2.0 + 0.3 * (Y - sy0)) < 4.0) & (pg.fbm(X / 2.0, Y / 9.0, 2, 1047) > 0.56), NU2)   # un rai de lune, à peine
    # La petite porte de fer du charbon, à gauche, et la glissière.
    pf = m_rect(P, 4.0, 22.0, 15.0, 22.0)
    P.rampe(pf, (0.3 + 0.14 * (pg.fbm(X / 1.4, Y / 1.4, 2, 1048) - 0.5) + 0.01 * (X - 4.0)) * (0.4 + Lm), [R_GROTTE[0], R_GROTTE[1], R_CUIVRE[0], R_GROTTE[3], R_CUIVRE[1], R_GROTTE[5]], 0.5)
    lisere(P, pf, R_GROTTE[0], 0, -1)
    lisere(P, pf, R_GROTTE[0], -1, 0)
    lisere(P, pf, R_GROTTE[6], 1, 0)
    for yy in (27.0, 38.0):
        P.rect(4.0, yy, 15.0, 0.8, R_GROTTE[4])
        for q in range(4):
            P.point(6.0 + q * 3.6, yy + 0.2, R_GROTTE[6])
    P.rect(15.6, 31.0, 1.6, 3.0, R_GROTTE[5])                                                      # la serrure, bien huilée
    P.point(16.2, 32.4, LU3 if int(p * 8) % 6 == 0 else R_GROTTE[0])
    # Des outils pendus : une pelle à charbon, un entonnoir, une burette ; une étagère de mèches et de verres de lampe.
    P.trait(132.0, 6.0, 132.0, 24.0, R_BOIS[5], 2)
    P.rampe(P.masque_poly([(129.4, 24.0), (134.6, 24.0), (134.0, 30.6), (130.0, 30.6)]), 0.5 * Lm + 0.16, R_ETAIN, 0.5)
    P.rampe(P.masque_poly([(139.0, 10.0), (147.0, 10.0), (144.0, 15.0), (143.6, 19.0), (142.4, 19.0), (142.0, 15.0)]), 0.5 * Lm + 0.2, R_LAITON, 0.5)
    P.point(143.0, 8.6, R_GROTTE[5])
    ex, ey = 54.0, 12.0
    P.rampe(m_rect(P, ex, ey, 28.0, 1.6), (0.9 - 0.3 * (Y - ey)) * (Lm + 0.1), R_BOIS, 0.5)
    P.rampe(m_rect(P, ex + 0.6, ey + 1.6, 28.0, 1.2), 0.24 * Lm, R_GROTTE, 0.5)
    for i in range(5):
        vx = ex + 3.0 + i * 5.4
        ve = (np.abs(X - vx) < 1.5 - 0.5 * np.abs((Y - ey + 4.0) / 3.6)) & (Y > ey - 7.6) & (Y < ey)
        P.rampe(ve, 0.4 + 0.4 * (X > vx) * vac, [NU2, NU4, BM2, LU4], 0.5)                           # des verres de lampe
        if (i + int(p * 8)) % 6 == 0:
            P.point(vx + 0.8, ey - 5.0, BLANC)

    # ====================================================================================================== la réserve
    tab.plan("moyen", 0.5)
    # ---- Le dallage : de grandes dalles rayonnantes, usées, tachées d'huile ; la trappe du puits.
    sol = Y >= SOL
    Lsw = lumiere(P, [(LX, 70.0, 44.0, 1.3 * vac)], 0.0)
    Lsc = 0.1 + 0 * X

    def ombre(cx, cy, rx, ry, f=0.55):
        nonlocal Lsw
        Lsw = Lsw * (1 - f * np.clip(1.3 - np.hypot((X - cx) / rx, (Y - cy) / ry), 0, 1))

    ombre(22.0, 66.0, 26.0, 3.0)
    ombre(150.0, 67.0, 34.0, 3.0)
    ombre(96.0 + bal, 73.0, 9.0, 1.4, 0.5)
    paves(P, sol, Lsc, Lsw, 96.0, 44.0, larg=5.0, prof=3.0, graine=1050)
    P.rampe((Y >= SOL - 1.4) & (Y < SOL), 0.16 + 0 * X, R_GROTTE, 0.5)                               # le pied du mur
    tr = P.masque_poly([(58.0, 69.0), (78.0, 69.0), (80.6, 74.0), (55.4, 74.0)])
    lames(P, tr, Lsw * 1.3 + 0.08, larg=4.2, graine=1051, vertical=True, alb=0.5, noeuds=0.4)
    lisere(P, tr, R_BOIS[0], 0, 1)
    lisere(P, tr, R_BOIS[0], 0, -1)
    P.ell(68.0, 71.4, 1.6, 0.8, R_GROTTE[5])                                                       # son anneau
    P.ell(68.0, 71.4, 0.8, 0.3, R_BOIS[0])
    P.courbe([(69.0, 71.6), (74.0, 73.0), (82.0, 72.0), (86.0, 74.6)], GO2, 1)                       # une ficelle et un hameçon : le grappin de Pilou
    P.point(86.4, 75.0, BM3)
    # ---- Le tas de charbon, sa pelle plantée, le seau.
    fc = lambda x: SOL + 4.0 - 17.0 * np.exp(-((x - 12.0) / 18.0) ** 2) + 1.2 * (pg.fbm(x / 1.6, 0 * x, 3, 1052) - 0.5) * 2.0
    tas = (Y > fc(X)) & (Y < SOL + 6.0 - 0.02 * (X - 12.0) ** 2 * 0.2) & (X < 46)
    bloc_ = pg.fbm(X / 1.4 + 0.3 * Y, Y / 1.2, 3, 1053)
    P.rampe(tas, (0.2 + 1.0 * np.clip(bloc_ - 0.5, 0, 1) * 3.0 * np.clip((X - 0.0) / 24.0, 0, 1)) * (0.4 + Lm), [ENCRE, R_GROTTE[0], R_GROTTE[1], R_GROTTE[3], R_GROTTE[5], R_GROTTE[7]], 0.5)
    lisere(P, tas, R_GROTTE[4], 1, 0, cond=pg.fbm(Y, 0 * Y, 2, 1054) > 0.5)
    for i in range(7):                                          # des boulets ont roulé
        P.ell(40.0 + 9.0 * hz(i, 1, 1055), SOL + 3.0 + 5.0 * hz(i, 2, 1055), 0.9, 0.6, ENCRE)
    P.trait(30.0, 44.0, 35.0, SOL + 1.0, R_BOIS[5], 2)                                             # la pelle
    P.trait(29.0, 43.6, 31.4, 43.2, R_BOIS[6], 2)
    seau = m_rect(P, 44.0, SOL - 1.0, 7.0, 7.0) & (np.abs(X - 47.5) < 2.6 + 0.9 * (SOL + 6.0 - Y) / 7.0)
    P.rampe(seau, (0.3 + 0.5 * np.clip((X - 44.0) / 7.0, 0, 1)) * vac, R_ETAIN, 0.5)
    P.ell(47.5, SOL - 1.0, 3.5, 0.9, ENCRE)
    P.courbe([(44.0, SOL - 0.6), (47.5, SOL - 5.6), (51.0, SOL - 0.6)], GR3, 1)
    # ---- La poulie, sa corde, la lanterne accrochée, et le panier (la clé).
    P.trait(96.0, -16.0, 96.0, -9.0, R_GROTTE[4], 2)
    P.rampe(m_ell(P, 96.0, -7.0, 3.0, 3.0), 0.4 + 0.3 * (Y > -7.0), R_ETAIN, 0.5)
    P.point(96.0, -7.0, ENCRE, 2)
    P.trait(98.6, -6.0, 124.0, 40.0, GO1)                                                          # le brin qui va au taquet
    P.rect(123.0, 39.0, 2.4, 3.4, R_GROTTE[5])
    P.trait(94.0, -6.0, 96.0 + bal, 52.0, GO2)
    lx_ = 96.0 + bal * 0.8
    halo(P, lx_, LY + 2.0, 13.0, LU2, 0.3 * vac)
    P.rect(lx_ - 2.0, LY + 5.0, 4.0, 0.9, R_GROTTE[1])
    P.rect(lx_ - 1.6, LY, 3.2, 5.0, LU4 if int(p * 8) % 5 else LU3)
    P.rect(lx_ - 0.6, LY + 1.0, 1.2, 3.0, LU5)
    P.rect(lx_ - 2.0, LY - 0.8, 4.0, 0.9, R_GROTTE[1])
    for dxl in (-1.8, 1.4):
        P.rect(lx_ + dxl, LY, 0.4, 5.0, R_GROTTE[1])
    px_, py_ = 96.0 + bal, 62.0
    pan = (m_rect(P, px_ - 9.0, py_ - 6.0, 18.0, 12.0) & (np.abs(X - px_) < 9.0 - 1.6 * (Y - py_ + 6.0) / 12.0)) | m_ell(P, px_, py_ + 6.0, 7.4, 1.6)
    rang_ = np.floor(Y / 0.82)
    brin = (((X + rang_ * 1.3) % 2.6) < 0.5)
    P.rampe(pan, (0.5 + 0.1 * (rang_ % 2) - 0.2 * brin - 0.2 * np.abs(X - px_) / 9.0 + 0.3 * np.clip((py_ - Y) / 6.0, 0, 1)) * vac, [R_BOIS[1], R_BOIS[2], GO1, GO2, R_PLATRE[5], R_PLATRE[7]], 0.5)
    P.ell(px_, py_ - 6.0, 9.0, 1.6, R_BOIS[1])
    P.rampe(m_ell(P, px_ - 2.0, py_ - 6.6, 4.4, 1.4), 0.7 * vac, R_PAPIER, 0.5)                      # un torchon, et dessous la soupe du jeudi
    P.rampe(m_ell(P, px_ + 4.0, py_ - 7.0, 2.4, 1.6), 0.6 * vac, R_TOILE, 0.5)
    for cote in (-1, 1):
        P.trait(px_ + cote * 8.0, py_ - 6.0, 96.0 + bal, 52.0, GO2)
    # ---- Les bidons d'huile : trois rangées bien alignées, une marque de craie sur chacun.
    for rang in range(3):
        for i in range(8 - rang):
            bx_ = 122.0 + i * 6.2 + rang * 2.4
            by_ = SOL + 2.0 + rang * 3.6
            k = 0.86 + 0.14 * rang
            bid = m_rect(P, bx_ - 2.4 * k, by_ - 7.4 * k, 4.8 * k, 7.4 * k)
            Lb = float(np.clip(1.2 - (bx_ - LX) / 70.0, 0.3, 1.0)) * vac * (0.7 + 0.15 * rang)
            P.rampe(bid, (0.26 + 0.5 * np.clip(1 - (X - bx_ + 2.4 * k) / (4.8 * k), 0, 1)) * Lb, R_CUIVRE, 0.5)
            P.rect(bx_ - 2.4 * k, by_ - 4.2 * k, 4.8 * k, 0.5, R_GROTTE[0])
            P.rect(bx_ - 0.8 * k, by_ - 8.6 * k, 1.6 * k, 1.3 * k, R_GROTTE[4])
            P.trait(bx_ - 1.4 * k, by_ - 2.8 * k, bx_ + 0.6 * k, by_ - 1.4 * k, R_PAPIER[3])
            if (i + rang) % 3 == 0:
                P.trait(bx_ - 1.4 * k, by_ - 1.4 * k, bx_ + 0.6 * k, by_ - 2.8 * k, R_PAPIER[3])
            if (i * 3 + rang + int(p * 8)) % 11 == 0:
                P.point(bx_ - 1.6 * k, by_ - 6.6 * k, LU5)
    P.ell(118.0, SOL + 9.0, 5.0, 1.0, R_GROTTE[0])                                                  # une flaque d'huile, la lanterne dedans
    P.ell(117.0, SOL + 8.8, 2.0, 0.4, LU2)
    pg.goutte(P, 150.0, -8.0, SOL + 12.0, coul=BM2, d=0.4, flaque=BM2)
    pg.souris(P, 108.0, SOL + 4.0, sens=-1, coul=GR3)

    # ================================================================================================== premier plan
    tab.plan("premier", 1.0)
    # L'escalier de pierre en colimaçon, à droite : les marches en éventail montent dans le noir, la main courante de fer.
    for k in range(9):
        a0 = k * 0.36
        x0 = 198.0 - 22.0 * math.cos(a0 * 0.5) - k * 0.6
        y0 = 78.0 - k * 9.6
        m = P.masque_poly([(x0, y0), (200.0, y0 - 2.0), (200.0, y0 + 7.6), (x0 + 1.0, y0 + 9.6)])
        Lk = 1.9 * vac * math.exp(-k * 0.3)
        P.rampe(m, (0.36 + 0.14 * (pg.fbm(X / 2.0, Y / 2.0, 2, 1056 + k) - 0.5)) * Lk + 0.06, R_GROTTE, 0.5)
        P.rampe(m & (Y < y0 + 1.4 - 0.1 * (X - x0)), 0.9 * Lk + 0.06, R_GROTTE, 0.5)                  # le nez de la marche
    P.courbe([(176.0, 70.0), (180.0, 30.0), (190.0, 0.0), (198.0, -16.0)], R_GROTTE[1], 2)
    for k in range(4):
        P.trait(176.6 + k * 4.0, 66.0 - k * 22.0, 177.6 + k * 4.6, 80.0 - k * 22.0, R_GROTTE[1])
    # À gauche, le montant de la porte par où l'on vient d'entrer ; en bas, l'ombre.
    mo = X < 2.0 + 1.0 * np.sin(Y / 9.0)
    P.rampe(mo, 0.2 + 0.2 * (pg.fbm(X, Y / 4.0, 2, 1066) - 0.5), R_GROTTE[:4], 0.5)
    lisere(P, mo, R_GROTTE[6], 1, 0, cond=pg.fbm(Y / 3.0, 0 * Y, 2, 1067) > 0.4)
    P.rampe(Y > 78.6, 0.1 + 0 * X, R_GROTTE, 0.5)
    pg.toile_araignee(P, 4.0, -16.0, 12.0, sens=(1, 1), coul=R_GROTTE[5])
    for i in range(12):                                         # la poussière de charbon dans la lumière
        if (p + hz(i, 1, 1068)) % 1.0 < 0.5:
            P.point(70.0 + 50.0 * hz(i, 2, 1068) + 0.6 * onde(p, hz(i, 4, 1068)), 30.0 + 30.0 * hz(i, 3, 1068), LU4 if i % 2 else R_GROTTE[7])


# =====================================================================================================================
# La chambre de veille : une pièce ronde et chaude, au milieu de la tour. Le poêle ronfle à droite et rougit le mur
# chaulé ; sur la table, la bougie, le gros carnet de veille relié et la boîte en fer ; le fauteuil d'Anselme et sa
# corne de brume à soufflet ; le lit étroit ; par la meurtrière, la nuit et la brume. Trente ans de nuits ici.
# Repères : bougie de la table (149, 40) pour le papillon ; sol y = 78.
# =====================================================================================================================
@decor("phare-eteint", "chambre-de-veille", soleil=(176.0, 50.0), tons=PHARE, nom="La chambre de veille", matiere=True)
def chambre_de_veille(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tout = np.ones(X.shape, dtype=bool)
    PX, PY = 176.0, 50.0                                        # la gueule du poêle
    BX, BY = 149.0, 40.0                                        # la flamme de la bougie
    SOL = 62.0
    vac = 1.0 + 0.07 * onde(p * 2) + 0.04 * onde(p * 3, 0.2)

    # ====================================================================================================== le mur rond
    tab.plan("ciel", 0.0)
    nx = (X - 96.0) / 116.0
    ang = np.arcsin(np.clip(nx, -0.999, 0.999))
    Lm = (lumiere(P, [(PX, PY, 44.0, 1.1), (BX, BY, 26.0, 0.8)], 0.18)) * (0.6 + 0.4 * np.cos(ang) ** 2)
    Lm = Lm * (1 - 0.36 * np.clip(1 - np.abs(X - 86.0) / 9.0, 0, 1) * (Y > 26) * (Y < 62))          # l'ombre du fauteuil
    # la chaux sur la pierre : on devine les assises dessous, l'enduit s'écaille par endroits
    r = np.floor((Y + 16.0) / 6.6)
    aa = ang + 3.0 * hz(r, 1, 1070)
    dv0 = (Y + 16.0) - r * 6.6
    du0 = (aa % 0.21) * 116.0 * np.cos(ang)
    relief = -0.07 * ((dv0 < 0.6) | (du0 < 0.6))
    v = 0.7 + 0.22 * (pg.fbm(X / 12.0, Y / 8.0, 3, 1071) - 0.5) + 0.12 * (pg.fbm(X / 1.4, Y / 1.4, 2, 1072) - 0.5) + relief
    P.rampe(tout, v * Lm, R_PLATRE, 0.5)
    nu = (pg.fbm(X / 6.0, Y / 5.0, 3, 1073) > 0.73) & (Y > 24)                                      # la pierre à nu
    appareil(P, nu, Lm * 1.3 + 0.1, (PX, PY), lh=6.6, lw=10.0, graine=1074, alb=0.6)
    lisere(P, nu, R_PLATRE[2], 0, -1)
    # Le plafond : des solives rayonnantes, noircies par trente ans de poêle.
    plaf = Y < -8.0 + 2.0 * np.cos(ang * 2.0)
    P.rampe(plaf, (0.3 + 0.2 * (np.sin((X - 96.0) / (Y + 30.0) * 16.0) > 0.4)) * (0.3 + Lm), R_BOIS, 0.5)
    lisere(P, plaf, R_BOIS[1], 0, 1)
    # ---- La meurtrière : une fente profonde, ébrasée ; la nuit bleue, la brume qui passe, une étoile.
    mx_, my_ = 104.0, 2.0
    ebr = P.masque_poly([(mx_ - 8.0, my_ - 3.0), (mx_ + 8.0, my_ - 3.0), (mx_ + 6.0, my_ + 31.0), (mx_ - 6.0, my_ + 31.0)])
    P.rampe(ebr, (0.5 + 0.03 * (X - mx_)) * (Lm + 0.1), R_GRANIT, 0.5)
    fente = m_rect(P, mx_ - 2.4, my_, 4.8, 26.0) | m_ell(P, mx_, my_, 2.4, 2.4)
    P.rampe(fente, 0.3 + 0.2 * (pg.fbm((X + 2.0 * onde(p)) / 4.0, Y / 2.4, 3, 1075) - 0.5) + 0.006 * (Y - my_), R_NUIT, 0.5)
    P.point(mx_ + 0.6, my_ + 5.0, BM4 if p < 0.6 else BM2)
    P.rampe(fente & (Y > my_ + 19.0), 0.1 + 0.3 * (pg.fbm(X / 2.0 + onde(p), Y, 2, 1076) - 0.3), [NU0, NU1, NU2, BM1], 0.5)       # la mer, tout en bas
    lisere(P, fente, ENCRE, -1, 0)
    lisere(P, ebr, BM1, 1, 0, cond=X < mx_)                                                        # un peu de lune sur le tableau de gauche
    P.rampe(m_rect(P, mx_ - 7.0, my_ + 31.0, 14.0, 1.6), 0.8 * (Lm + 0.1), R_GRANIT, 0.5)
    # ---- Au mur : le ciré d'Anselme à sa patère, une étagère de livres de bord, le baromètre, un petit cadre.
    cx_, cy_ = 60.0, 6.0
    P.rect(cx_ - 0.6, cy_ - 1.6, 1.2, 1.6, LAITON)
    cire = P.masque_poly([(cx_ - 3.4, cy_), (cx_ + 3.4, cy_), (cx_ + 6.4, cy_ + 30.0), (cx_ - 6.4, cy_ + 31.0)])
    pli = 0.5 + 0.5 * np.sin((X - cx_) * 1.5 + 1.0)
    P.rampe(cire, (0.2 + 0.04 * (X - cx_ + 7.0) + 0.22 * pli) * (0.4 + 1.3 * Lm), R_CIRE, 0.5)
    for cote in (-1, 1):                                        # les manches
        man = P.masque_poly([(cx_ + cote * 3.4, cy_ + 1.0), (cx_ + cote * 7.6, cy_ + 5.0), (cx_ + cote * 9.0, cy_ + 23.0), (cx_ + cote * 5.8, cy_ + 24.0), (cx_ + cote * 4.4, cy_ + 8.0)])
        P.rampe(man, (0.16 + 0.2 * (cote > 0) + 0.1 * pli) * (0.4 + 1.3 * Lm), R_CIRE, 0.5)
    lisere(P, cire, CIRE2, 1, 0, cond=Y > cy_ + 3)
    P.trait(cx_ + 0.2, cy_ + 3.0, cx_ + 0.6, cy_ + 30.0, GO2)
    P.ell(cx_, cy_ + 0.6, 3.6, 2.2, GO1)
    ex, ey = 116.0, 14.0
    P.rampe(m_rect(P, ex, ey, 26.0, 1.6), (0.9 - 0.3 * (Y - ey)) * (Lm + 0.1), R_BOIS, 0.5)
    P.rampe(m_rect(P, ex + 0.6, ey + 1.6, 26.0, 1.2), 0.3 * Lm, R_PLATRE, 0.5)
    x = ex + 1.0
    i = 0
    dos = (R_TOILE, R_CUIVRE, R_NUIT[1:7], [GO1, GO1, GO2, LAITON, LAITON2, LU5], [VI1, VI1, VI2, T.VIOLET, BM3, BM4])
    while x < ex + 24:
        w, h = 2.2 + 1.8 * hz(i, 1, 1077), 8.0 + 3.0 * hz(i, 2, 1077)
        rr = dos[int(hz(i, 3, 1077) * len(dos))]
        P.rampe(m_rect(P, x, ey - h, w, h), (0.3 + 0.3 * np.clip((X - x) / w, 0, 1)) * (0.4 + Lm), rr, 0.5)
        P.rect(x, ey - h * 0.76, w, 0.5, LAITON)
        x += w + 0.3
        i += 1
    bar = (38.0, 16.0)                                                                            # le baromètre : son aiguille tremble
    P.rampe(m_ell(P, bar[0], bar[1], 5.0, 5.0), (0.5 + 0.2 * (X - bar[0]) / 5.0) * (0.5 + Lm), R_LAITON, 0.5)
    P.rampe(m_ell(P, bar[0], bar[1], 3.9, 3.9), 0.6 + 0.2 * (X - bar[0]) / 3.9, R_PAPIER[1:], 0.5)
    an = -0.9 + 0.08 * onde(p * 2, 0.1)
    P.trait(bar[0], bar[1], bar[0] + 3.2 * math.sin(an), bar[1] - 3.2 * math.cos(an), ENCRE)
    P.point(bar[0], bar[1], LAITON2)
    cd = m_rect(P, 76.0, 4.0, 12.0, 9.0)                                                           # un petit cadre : un bateau
    P.rampe(cd, 0.5 * (0.4 + Lm), R_BOIS, 0.5)
    P.rampe(m_rect(P, 77.2, 5.2, 9.6, 6.6), 0.4 + 0.04 * (Y - 5.0), R_NUIT[2:], 0.5)
    P.poly([(79.6, 10.0), (84.6, 10.0), (83.6, 11.0), (80.4, 11.0)], NU0)
    P.poly([(82.0, 6.4), (82.0, 9.8), (84.4, 9.8)], CREME)

    # ====================================================================================================== la chambre
    tab.plan("moyen", 0.5)
    sol = Y >= SOL
    Ls = lumiere(P, [(PX - 4.0, 70.0, 30.0, 1.2 * vac), (BX, 66.0, 16.0, 0.4)], 0.2)

    def ombre(cx, cy, rx, ry, f=0.5):
        nonlocal Ls
        Ls = Ls * (1 - f * np.clip(1.3 - np.hypot((X - cx) / rx, (Y - cy) / ry), 0, 1))

    ombre(20.0, 66.0, 30.0, 2.6)
    ombre(82.0, 72.6, 14.0, 1.8)
    ombre(146.0, 73.0, 16.0, 1.8, 0.4)
    plancher(P, sol, Ls, 96.0, 44.0, larg=4.6, graine=1078, alb=0.66)
    P.rampe((Y >= SOL - 1.6) & (Y < SOL), 0.4 * Lm, R_BOIS, 0.5)
    tapis = m_ell(P, 110.0, 73.6, 26.0, 3.6)                                                       # le tapis rond, tressé
    rr_ = np.hypot((X - 110.0) / 26.0, (Y - 73.6) / 3.6)
    an_ = np.floor(rr_ * 5.0 + 0.3 * (pg.fbm(X / 3.0, Y / 1.2, 2, 1079) - 0.5))
    P.rampe(tapis & (an_ % 2 == 0), 0.6 * Ls, R_CUIVRE, 0.5)
    P.rampe(tapis & (an_ % 2 == 1), 0.5 * (0.2 + Ls), R_TOILE[:5], 0.5)
    # ---- Le lit étroit, à gauche : un cadre de bois, une couverture de laine rayée, l'oreiller.
    Ll = Lm * 1.2 + 0.1
    P.rampe(m_rect(P, -6.0, 34.0, 4.0, 30.0), 0.6 * Ll, R_BOIS, 0.5)                                # la tête de lit
    mat = P.masque_poly([(-6.0, 48.0), (34.0, 48.0), (36.0, 56.0), (-6.0, 56.0)])
    ray = (np.floor((X + Y * 0.3) / 2.6) % 3 == 0)
    P.rampe(mat, (0.5 + 0.2 * ray + 0.16 * np.sin(X * 0.5) * (Y < 51)) * Ll * 1.2, R_TOILE, 0.5)
    P.rampe(mat & ray & (X > 8), 0.6 * Ll * 1.2, R_PAPIER, 0.5)
    lisere(P, mat, R_TOILE[5], 0, -1)
    P.rampe(m_ell(P, 3.0, 46.6, 6.0, 2.6), (0.7 - 0.2 * (Y - 46.6) / 2.6) * Ll * 1.3, R_PAPIER, 0.5)
    lames(P, m_rect(P, -6.0, 56.0, 43.0, 4.0), Ll, larg=30.0, graine=1080, vertical=False, alb=0.6, noeuds=0)
    P.rampe(m_rect(P, 34.0, 44.0, 3.0, 20.0), (0.5 + 0.2 * (X > 35.4)) * Ll * 1.3, R_BOIS, 0.5)       # le pied de lit
    P.ell(35.5, 43.4, 2.0, 1.6, R_BOIS[6])
    for xq in (-2.0, 30.0):
        P.rampe(m_rect(P, xq, 60.0, 2.4, 5.0), 0.3 * Ll, R_BOIS, 0.5)
    P.rampe(m_ell(P, 24.0, 64.6, 5.0, 1.2), 0.5 * Ls, [R_BOIS[1], R_BOIS[3], GO2, R_PLATRE[5]], 0.5)    # ses chaussons
    # ---- Le fauteuil d'Anselme : un vieux voltaire de cuir, creusé ; la corne de brume à soufflet posée contre lui.
    fx_ = 82.0
    Lf = lumiere(P, [(PX, PY, 50.0, 1.2 * vac), (BX, BY, 30.0, 0.7)], 0.16)
    dos_ = (m_rect(P, fx_ - 8.0, 30.0, 16.0, 26.0) | m_ell(P, fx_, 30.0, 8.0, 5.0))
    cap = np.sin((X - fx_) * 1.0) * np.sin((Y - 30.0) * 0.8)
    P.rampe(dos_, (0.4 + 0.12 * cap + 0.3 * np.clip((X - fx_ + 8.0) / 16.0, 0, 1)) * Lf * 1.2, R_CUIVRE, 0.5)
    for cy2 in np.arange(33.0, 54.0, 5.0):
        for cx2 in (fx_ - 4.0, fx_ + 0.6, fx_ + 5.0):
            P.point(cx2, cy2, R_CUIVRE[0])                                                         # les boutons du capiton
    lisere(P, dos_, R_CUIVRE[4], 1, 0)
    for cote, xa in ((-1, fx_ - 11.6), (1, fx_ + 7.6)):                                           # les accoudoirs
        acc = m_rect(P, xa, 46.0, 4.0, 16.0) | m_ell(P, xa + 2.0, 46.0, 2.6, 2.0)
        P.rampe(acc, (0.3 + 0.4 * (cote > 0) + 0.1 * (Y < 47)) * Lf * 1.2, R_CUIVRE, 0.5)
    ass = P.masque_poly([(fx_ - 8.0, 54.0), (fx_ + 8.0, 54.0), (fx_ + 9.0, 60.0), (fx_ - 9.0, 60.0)])
    P.rampe(ass, (0.6 + 0.1 * np.sin((X - fx_) * 0.5)) * Lf * 1.2, R_CUIVRE, 0.5)
    P.rampe(m_rect(P, fx_ - 11.6, 60.0, 23.2, 3.0), 0.3 * Lf, R_CUIVRE, 0.5)
    for xq in (fx_ - 11.0, fx_ + 9.0):
        P.rampe(m_rect(P, xq, 63.0, 2.0, 4.6), 0.4 * Lf, R_BOIS, 0.5)
    P.rampe(P.masque_poly([(fx_ - 7.0, 36.0), (fx_ + 1.0, 34.0), (fx_ + 3.0, 44.0), (fx_ - 6.0, 46.0)]), (0.6 + 0.2 * (((P.XI + P.YI) // 2) % 2)) * Lf, R_TOILE, 0.5)   # un plaid
    cx_, cy_ = 100.0, 66.0                                                                        # la corne de brume : soufflet de cuir, pavillon de cuivre
    souf = m_rect(P, cx_ - 4.0, cy_ - 9.0, 8.0, 9.0)
    P.rampe(souf, (0.3 + 0.3 * ((np.floor(Y / 1.4) % 2) == 0) + 0.2 * (X > cx_)) * Lf, R_BOIS, 0.5)
    P.rect(cx_ - 4.6, cy_ - 10.0, 9.2, 1.2, R_BOIS[6])
    P.rect(cx_ - 4.6, cy_ - 0.6, 9.2, 1.2, R_BOIS[4])
    pav = P.masque_poly([(cx_ + 4.0, cy_ - 6.0), (cx_ + 4.0, cy_ - 4.0), (cx_ + 12.0, cy_ - 1.0), (cx_ + 12.0, cy_ - 10.0)])
    P.rampe(pav, (0.4 + 0.5 * np.clip((cy_ - 4.0 - Y) / 6.0, 0, 1)) * Lf * 1.3, R_LAITON, 0.5)
    P.ell(cx_ + 12.0, cy_ - 5.5, 1.4, 4.5, GO1)
    if int(p * 8) % 6 == 0:
        P.point(cx_ + 9.0, cy_ - 8.0, BLANC)
    # ---- La table : la bougie, le carnet de veille ouvert (deux écritures), la plume, la boîte en fer, les lunettes cassées.
    tx0, tx1, ty = 132.0, 164.0, 48.0
    Lt = lumiere(P, [(BX, BY + 4.0, 14.0, 1.1), (PX, PY, 40.0, 0.9 * vac)], 0.2)
    plat = P.masque_poly([(tx0 + 2.0, ty - 3.0), (tx1 - 2.0, ty - 3.0), (tx1 + 1.0, ty), (tx0 - 1.0, ty)])
    P.rampe(plat, (0.7 + 0.2 * (pg.fbm(X / 5.0, Y * 1.4, 2, 1081) - 0.5)) * Lt, R_BOIS, 0.5)
    P.rampe(m_rect(P, tx0 - 1.0, ty, tx1 - tx0 + 2.0, 1.6), 0.5 * Lt, R_BOIS, 0.5)
    P.rampe(m_rect(P, tx0 + 1.0, ty + 1.6, tx1 - tx0 - 2.0, 2.0), 0.3 * Lt, R_BOIS, 0.5)
    for xq in (tx0 + 1.0, tx1 - 3.4):
        P.rampe(m_rect(P, xq, ty + 1.6, 2.4, 18.0), (0.3 + 0.4 * (X > xq + 1.0)) * Lt, R_BOIS, 0.5)
    car = P.masque_poly([(138.0, ty - 2.6), (147.0, ty - 2.9), (147.6, ty - 0.6), (137.0, ty - 0.4)])   # le carnet
    P.rampe(car, 0.84, R_PAPIER, 0.5)
    P.rect(137.0, ty - 0.5, 10.6, 0.7, R_TOILE[1])
    P.trait(142.4, ty - 2.8, 142.4, ty - 0.6, R_PAPIER[1])
    for k in range(3):
        P.trait(138.6, ty - 2.2 + k * 0.6, 141.8, ty - 2.3 + k * 0.6, R_NUIT[1])                     # l'écriture d'Anselme, serrée
        P.trait(143.2, ty - 2.3 + k * 0.6, 146.2 - k * 0.6, ty - 2.4 + k * 0.6, R_TOILE[2])           # celle de Lison, ronde
    P.trait(147.0, ty - 1.2, 152.6, ty - 3.6, R_PAPIER[4])                                         # la plume
    P.ell(BX, ty - 1.4, 2.4, 0.8, LAITON)                                                         # le bougeoir
    P.rect(BX - 0.6, BY + 1.0, 1.2, ty - BY - 2.0, CREME)
    halo(P, BX, BY, 9.0, LU3, 0.4)
    fd = 0.35 * onde(p * 2, 0.6)
    P.poly([(BX - 0.7, BY + 1.0), (BX + 0.7, BY + 1.0), (BX + fd, BY - 2.4)], LU4)
    P.poly([(BX - 0.4, BY + 1.0), (BX + 0.4, BY + 1.0), (BX + fd * 0.5, BY - 0.8)], LU5)
    bo = m_rect(P, 154.0, ty - 5.4, 7.0, 3.6)                                                      # la boîte en fer
    P.rampe(bo, (0.4 + 0.3 * (X < 156.0) + 0.1 * (Y < ty - 4.6)) * Lt, R_TOILE, 0.5)
    P.rect(154.0, ty - 4.4, 7.0, 0.4, R_TOILE[0])
    P.rect(156.0, ty - 3.6, 3.0, 1.2, CREME)
    for dxl in (0.0, 2.6):                                                                        # les lunettes, un verre fêlé
        P.ell(134.6 + dxl, ty - 1.4, 1.2, 0.7, LAITON)
        P.ell(134.6 + dxl, ty - 1.4, 0.7, 0.4, BM2)
    P.rampe(m_ell(P, 126.0, 64.0, 4.6, 1.4), 0.6 * Ls, R_BOIS, 0.5)                                 # un tabouret, sous la table
    for dxl in (-3.0, 3.0):
        P.trait(126.0 + dxl * 0.8, 65.0, 126.0 + dxl * 1.2, 72.0, R_BOIS[3], 2)
    # ---- Le poêle de fonte : un fût cannelé sur trois pieds, la porte à mica qui rougeoie, la bouilloire dessus, le tuyau.
    sx0, sx1 = 168.0, 186.0
    fut = m_rect(P, sx0, 38.0, sx1 - sx0, 26.0)
    nxp = (X - (sx0 + sx1) / 2) / ((sx1 - sx0) / 2)
    P.rampe(fut, 0.14 + 0.3 * np.exp(-((nxp + 0.5) / 0.3) ** 2) + 0.06 * (np.sin(X * 3.0) > 0.4) + 0.2 * vac * np.clip((Y - 44.0) / 16.0, 0, 1) * (np.abs(nxp) < 0.7), [ENCRE, R_GRANIT[0], R_GRANIT[1], R_GRANIT[2], R_CUIVRE[0], R_CUIVRE[1]], 0.5)
    for yy in (38.0, 46.0, 62.6):
        P.rampe(m_rect(P, sx0 - 1.0, yy, sx1 - sx0 + 2.0, 1.4), 0.3 + 0.3 * (nxp < -0.2), [ENCRE, R_GRANIT[1], R_GRANIT[3], GR3], 0.5)
    gueule = m_rect(P, PX - 5.0, PY - 1.0, 10.0, 8.0)
    P.remplir(m_rect(P, PX - 5.8, PY - 1.8, 11.6, 9.6), ENCRE)
    P.rampe(gueule, 0.5 + 0.4 * (pg.fbm(X / 1.0, (Y + 3.0 * p) / 1.0, 2, 1082) - 0.5) + 0.2 * onde(p * 2, 0.2) + 0.2 * (Y > PY + 3.0), R_FEU[:6], 0.5)
    for k in range(1, 4):
        P.rect(PX - 5.0 + k * 2.5 - 0.2, PY - 1.0, 0.5, 8.0, ENCRE)                                  # les barreaux
    halo(P, PX, PY + 3.0, 18.0, LU2, 0.3 * vac)
    for dxl in (-7.0, 0.0, 7.0):
        P.trait(PX + dxl, 64.0, PX + dxl * 1.2, 68.6, ENCRE, 2)
    P.rampe(m_rect(P, PX - 2.0, -16.0, 4.6, 54.0), 0.2 + 0.3 * (X < PX - 0.4), [ENCRE, R_GRANIT[0], R_GRANIT[1], R_GRANIT[2]], 0.5)       # le tuyau
    P.rect(PX - 2.6, 10.0, 5.8, 1.0, R_GRANIT[0])
    bo2 = m_ell(P, PX + 3.0, 34.6, 4.6, 3.6)                                                       # la bouilloire, qui chante
    P.rampe(bo2, 0.4 - 0.3 * (X - PX - 3.0) / 4.6 - 0.2 * (Y - 34.6) / 3.6, R_LAITON, 0.5)
    P.trait(PX + 7.4, 33.6, PX + 10.0, 31.6, LAITON, 2)
    P.courbe([(PX + 0.4, 32.0), (PX + 3.0, 28.6), (PX + 5.6, 32.0)], GO1, 1)
    fumerolle(P, PX + 10.4, 30.6, h=11.0, n=3, d=0.1, coul=BM4, force=0.4, large=0.8)
    for i in range(3):                                          # un seau à charbon, des bûchettes
        P.rampe(m_ell(P, 190.0 + i * 0.6, 62.0 - i * 2.2, 2.2, 1.8), 0.5 + 0.2 * hz(i, 0, 1083) - 0.2 * (X - 190.0) / 2.0, R_BOIS[2:], 0.5)
    chat(P, 150.0, 72.0, coul=R_CUIVRE[1], sens=1)                                                  # le chat du phare, sur le tapis, au chaud

    # ================================================================================================== premier plan
    tab.plan("premier", 1.0)
    # À contre-jour : la rampe de l'escalier qui débouche dans la pièce, en bas à gauche ; une lampe-tempête éteinte
    # pendue à la solive, en haut ; l'ombre au ras du plancher.
    for k in range(6):
        xk = -4.0 + k * 5.0
        P.rampe(m_rect(P, xk, 66.0 + k * 2.2, 1.2, 16.0), 0.24 + 0.1 * (k % 2), [ENCRE, R_BOIS[0], R_BOIS[1], R_BOIS[3]], 0.5)
    main = P.masque_poly([(-6.0, 62.0), (26.0, 76.4), (26.0, 78.4), (-6.0, 64.6)])
    P.rampe(main, 0.4 + 0.02 * X, [R_BOIS[0], R_BOIS[1], R_BOIS[3], R_BOIS[5]], 0.5)
    lisere(P, main, R_BOIS[6], 0, -1)
    lt = 0.4 * onde(p, 0.3)
    P.trait(64.0, -16.0, 64.0 + lt, -6.0, R_BOIS[0])
    lan = m_rect(P, 61.6 + lt, -6.0, 4.8, 7.0)
    P.rampe(lan, 0.3 + 0.3 * (X > 64.0 + lt), [ENCRE, NU1, NU3, R_CUIVRE[1]], 0.5)
    P.rect(61.0 + lt, -6.8, 6.0, 1.0, ENCRE)
    P.rect(61.0 + lt, 1.0, 6.0, 1.0, ENCRE)
    P.rampe(Y > 78.8, 0.16 + 0 * X, R_BOIS, 0.5)
    for i in range(12):
        if (p + hz(i, 1, 1084)) % 1.0 < 0.5:
            P.point(120.0 + 60.0 * hz(i, 2, 1084) + 0.6 * onde(p, hz(i, 4, 1084)), 20.0 + 36.0 * hz(i, 3, 1084), LU4)


# =====================================================================================================================
# La lanterne : le sommet du phare, la nuit. Au milieu, la grande lentille à échelons (la clé) dort, son drap tombé à
# ses pieds ; elle boit le peu de lune que la brume laisse passer. À droite, la machine d'horlogerie : des roues de
# laiton patiné, le poids au bout de sa chaîne, la manivelle, et ce cadran de fer-blanc trop neuf, tenu par une vis
# toute neuve. Tout autour, les vitres en losanges ouvertes sur la brume. La chandelle de Pilou est posée par terre.
# =====================================================================================================================
@decor("phare-eteint", "lanterne-du-phare", soleil=(40.0, 4.0), tons=PHARE, nom="La lanterne", matiere=True)
def lanterne_du_phare(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tout = np.ones(X.shape, dtype=bool)
    LUNE = (40.0, 4.0)
    SOL, APPUI = 62.0, 44.0                                     # le plancher ; le haut du muret
    CX, CY = 132.0, 60.0                                        # la chandelle
    vac = 1.0 + 0.08 * onde(p * 2) + 0.04 * onde(p * 3, 0.3)

    # ======================================================================================================== la nuit
    tab.plan("ciel", 0.0)
    P.horizon, P.ciel_haut, P.halo = 40.0, 0.06, 0.34
    vc = pg.valeur_ciel(P, X, Y)
    P.rampe(tout, 0.04 + 0.62 * vc, T.CIEL, 0.75)
    for i in range(46):
        ex, ey = 198.0 * hz(i, 1, 1100) - 3.0, -15.0 + 40.0 * hz(i, 2, 1100) ** 1.4
        if math.hypot(ex - LUNE[0], ey - LUNE[1]) > 18.0 and (p + hz(i, 3, 1100)) % 1.0 < 0.7:
            P.point(ex, ey, T.CIEL[8] if hz(i, 4, 1100) < 0.4 else T.CIEL[5])
    dl = np.hypot(X - LUNE[0], Y - LUNE[1])
    P.rampe(dl < 12.0, 0.3 + 0.7 * np.clip(1 - dl / 12.0, 0, 1) ** 1.5 + 0.5 * vc, T.CIEL[3:10], 0.6)
    P.remplir(dl < 4.0, T.CIEL[10])
    P.remplir(dl < 3.4, T.SOL)
    tab.plan("nuages", 0.08)

    def nappe(y, epais, graine, tons, seuil=0.62, pas=20.0):
        def dens(yy):
            return (0.4 + pg.fbm((X + 2.0 * onde(p, 0.013 * graine)) / pas, yy / 2.4, 3, graine)) * np.exp(-((yy - y - np.sin(X / 19.0 + graine)) / epais) ** 2) - seuil
        d = dens(Y)
        prox = np.exp(-(np.hypot(X - LUNE[0], (Y - LUNE[1]) * 1.4) / 60.0) ** 2)
        P.rampe(d > 0, 0.2 + 1.5 * d + 1.6 * (d - dens(Y + 1.0)) + 0.45 * prox, tons, 0.6)

    nappe(-6.0, 4.0, 1101, T.CIEL[2:8], 0.6, 30.0)
    nappe(12.0, 3.0, 1102, T.CIEL[3:9], 0.64, 26.0)
    nappe(26.0, 3.4, 1103, T.CIEL[4:10], 0.58, 22.0)                                               # on est au-dessus de la brume
    nappe(36.0, 3.0, 1104, T.CIEL[5:10], 0.54, 18.0)
    for i in range(3):                                          # très bas, les lampes de Trébrume percent
        if (p + 0.3 * i) % 1.0 < 0.8:
            P.point(160.0 + 9.0 * i, 39.0 + (i % 2), LU3)

    # ============================================================================================ la cage de la lanterne
    tab.plan("moyen", 0.5)
    # ---- Les vitres : des montants de fonte et des astragales en losanges ; quelques carreaux embués, un fêlé.
    vitrage = Y < APPUI
    pas_x = 24.0
    u = (X - 96.0) / pas_x
    los = (np.abs(((u + (Y + 16.0) / 30.0) % 1.0) - 0.5) < 0.016) | (np.abs(((u - (Y + 16.0) / 30.0) % 1.0) - 0.5) < 0.016)
    mont = np.abs((u % 1.0) - 0.5) > 0.47
    ferr = vitrage & (los | mont | (Y < -13.0) | (np.abs(Y - 14.0) < 0.7))
    P.rampe(ferr, 0.24 + 0.3 * np.exp(-((X - LUNE[0]) / 60.0) ** 2) * (((u * 2.0) % 1.0) < 0.5), [ENCRE, NU0, NU1, NU2, NU3], 0.5)
    for i in range(6):                                          # la buée au bas de quelques vitres
        bx_ = -4.0 + i * 36.0
        buee = vitrage & ~ferr & (np.abs(X - bx_) < 9.0) & (Y > APPUI - 8.0 + 2.0 * np.sin(X / 2.0)) & (pg.fbm(X / 2.0, Y / 1.6, 2, 1105 + i) > 0.44)
        P.remplir(buee, T.CIEL[5])
    for (ax_, ay_) in ((-5.0, -4.0), (4.0, -6.0), (-2.0, 5.0)):
        P.trait(22.0, 26.0, 22.0 + ax_, 26.0 + ay_, BM3)                                           # la fêlure
    for k in range(4):                                          # des gouttes de brume glissent dehors
        t = (p + k * 0.27) % 1.0
        gx = 14.0 + k * 50.0
        P.trait(gx, 2.0 + 36.0 * t, gx, 3.4 + 36.0 * t, BM2)
    # Le muret : un soubassement de tôle rivetée, peint, que la chandelle réchauffe à droite.
    Lw = lumiere(P, [(CX, CY, 26.0, 1.1 * vac)], 0.0)
    Lc = 0.34 + 0.3 * np.exp(-((X - LUNE[0] - 20.0) / 50.0) ** 2)
    muret = (Y >= APPUI) & (Y < SOL)
    pan_ = ((X - 96.0) / pas_x) % 1.0
    v = 0.56 + 0.1 * (pg.fbm(X / 1.4, Y / 1.4, 2, 1106) - 0.5) + 0.12 * (pan_ < 0.5) - 0.1 * np.clip(pg.fbm(X / 2.0, Y / 16.0, 2, 1107) - 0.6, 0, 1) * 3.0
    v = np.where((pan_ < 0.02) | (np.abs(Y - APPUI - 2.0) < 0.4), 0.3, v)
    chaud = Lw > 0.7 * Lc
    P.rampe(muret & ~chaud, v * (Lc + Lw), R_FROID, 0.5)
    P.rampe(muret & chaud, v * (Lc + Lw), R_GRANIT, 0.5)
    for i in range(34):                                         # les rivets
        rx_ = -4.0 + i * 6.0
        P.point(rx_, APPUI + 4.0, BM1 if rx_ < 100 else R_GRANIT[5])
        P.point(rx_ + 0.4, APPUI + 4.4, ENCRE)
    P.rampe((Y >= APPUI - 1.2) & (Y < APPUI), 0.8 * (Lc + Lw), R_FROID, 0.5)                         # la tablette, ourlée de lune
    # ---- Le plancher de tôle striée, en éventail autour de la lentille.
    sol = Y >= SOL
    Lsw = lumiere(P, [(CX, 68.0, 24.0, 1.1 * vac)], 0.0)
    Lsc = 0.3 + 0.36 * np.exp(-((X - 60.0) / 60.0) ** 2) - 0.006 * (Y - SOL)

    def ombre(cx, cy, rx, ry, f=0.55):
        nonlocal Lsw, Lsc
        o = 1 - f * np.clip(1.3 - np.hypot((X - cx) / rx, (Y - cy) / ry), 0, 1)
        Lsw, Lsc = Lsw * o, Lsc * o

    ombre(108.0, 67.0, 24.0, 2.6)                    # la lentille, à l'opposé de la lune
    ombre(168.0, 67.6, 20.0, 2.2, 0.5)
    paves(P, sol, Lsc, Lsw, 96.0, 40.0, larg=4.2, prof=3.4, graine=1108)
    P.remplir(sol & (((X + Y * 2.0) % 3.0) < 0.42) & (pg.fbm(X / 6.0, Y / 2.0, 2, 1109) > 0.7) & (Lsc + Lsw > 0.46), BM1)        # les stries qui accrochent

    # ---- La grande lentille (la clé) : un tonneau de verre, des anneaux de prismes de part et d'autre de l'œil central.
    ox, oy = 96.0, 28.0
    rx_l, ry_l = 21.0, 27.0
    lent = m_ell(P, ox, oy, rx_l, ry_l)
    ny = (Y - oy) / ry_l
    nxl = (X - ox) / np.maximum(rx_l * np.sqrt(np.clip(1 - ny * ny, 0.01, 1)), 0.1)
    ech = np.floor((np.abs(ny) - 0.18) * 9.0)                   # les échelons, au-dessus et au-dessous de l'œil
    fr = ((np.abs(ny) - 0.18) * 9.0) % 1.0
    lune_ = np.exp(-((nxl + 0.55) / 0.3) ** 2)                  # le croissant que la lune y allume
    feu_ = np.exp(-((nxl - 0.74) / 0.12) ** 2) * np.clip(1 - np.abs(Y - 46.0) / 12.0, 0, 1) * vac     # et la chandelle, de l'autre côté
    vl = 0.2 + 0.5 * lune_ + 0.16 * fr * (np.abs(ny) > 0.18) + 0.1 * (ech % 2) - 0.1 * np.abs(nxl)
    P.rampe(lent, vl, R_VERRE[:5] + [BM4], 0.5)
    P.rampe(lent & (feu_ > 0.4) & (fr > 0.3), 0.2 + 0.7 * feu_, [R_VERRE[2], R_CUIVRE[1], LU2, LU3, LU4], 0.5)
    P.remplir(lent & (np.abs(ny) > 0.18) & (fr < 0.1), R_VERRE[0])                                   # les joints des prismes
    oeil = m_ell(P, ox, oy, 7.4, 4.6)                                                              # l'œil : une loupe bombée
    P.rampe(oeil, 0.3 + 0.5 * np.exp(-(np.hypot(X - ox + 2.4, (Y - oy + 1.4) * 1.5) / 3.0) ** 2) - 0.1 * (X - ox) / 7.4, R_VERRE[:5] + [BLANC], 0.5)
    lisere(P, oeil, R_VERRE[0], 0, 1)
    for k in range(-3, 4):                                      # les montants de laiton de l'optique
        xk = ox + rx_l * math.sin(k * 0.44)
        mk = lent & (np.abs(X - ox - (xk - ox) * np.sqrt(np.clip(1 - ny * ny, 0, 1))) < 0.45)
        P.rampe(mk, 0.3 + 0.4 * (k < 0) + 0.3 * (k > 1) * vac, R_LAITON, 0.5)
    for i in range(7):                                          # des éclats qui se déplacent d'un échelon à l'autre
        if (i + int(p * 8)) % 4 == 0:
            P.point(ox - 12.0 + 2.6 * (i % 3), oy - 20.0 + i * 6.4, BLANC)
    for yy, w_ in ((oy - ry_l - 1.0, 12.0), (oy + ry_l - 0.6, 14.0)):                               # les couronnes de laiton
        P.rampe(m_rect(P, ox - w_ / 2, yy, w_, 1.8), 0.4 + 0.4 * np.clip(1 - (X - ox + w_ / 2) / w_, 0, 1), R_LAITON, 0.5)
    pied = P.masque_poly([(ox - 9.0, oy + ry_l + 1.2), (ox + 9.0, oy + ry_l + 1.2), (ox + 13.0, SOL + 4.0), (ox - 13.0, SOL + 4.0)])
    P.rampe(pied, (0.3 + 0.3 * np.clip(1 - (X - ox + 13.0) / 26.0, 0, 1)) + 0.3 * (X > ox + 6) * vac, R_LAITON, 0.5)
    P.rampe(m_rect(P, ox - 15.0, SOL + 4.0, 30.0, 2.0), 0.3 + 0.3 * (X < ox), R_FROID, 0.5)
    # Le drap, tombé à ses pieds.
    dr = (m_ell(P, ox - 20.0, SOL + 4.6, 12.0, 3.4) | m_ell(P, ox - 12.0, SOL + 2.0, 6.0, 3.0)) & (pg.fbm(X / 3.0, Y / 1.4, 2, 1110) > 0.26)
    P.rampe(dr, 0.5 + 0.4 * (pg.fbm(X / 2.0 + 0.4 * Y, Y / 1.2, 3, 1111) - 0.5) + 0.2 * (X < ox - 20), R_PAPIER, 0.5)
    lisere(P, dr, R_PAPIER[0], 0, 1)

    # ---- La machine : un bâti de fonte, des roues de laiton patiné, le tambour et sa chaîne, le poids, la manivelle.
    bx0, by0, bw, bh = 150.0, 34.0, 30.0, 30.0
    Lmch = lumiere(P, [(CX, CY - 6.0, 30.0, 1.3 * vac)], 0.26)
    bati = m_rect(P, bx0, by0, bw, bh)
    P.rampe(bati, (0.3 + 0.1 * (pg.fbm(X / 1.6, Y / 1.6, 2, 1112) - 0.5)) * Lmch, R_GRANIT, 0.5)
    jour = m_rect(P, bx0 + 2.4, by0 + 2.4, bw - 4.8, bh - 9.0)
    P.rampe(jour, 0.1 * Lmch, R_GRANIT, 0.5)
    lisere(P, jour, R_GRANIT[5], -1, 0)
    for i, (rx_, ry_, rr, dents) in enumerate(((bx0 + 9.0, by0 + 10.0, 5.6, 14), (bx0 + 18.6, by0 + 13.6, 4.0, 10), (bx0 + 12.0, by0 + 19.0, 3.0, 8))):
        pg.roue(P, rx_, ry_, rr, dents, GO2, LAITON, GO1, angle=0.3 * i)
        P.point(rx_ - rr * 0.5, ry_ - rr * 0.5, LAITON2 if (i + int(p * 8)) % 5 else BLANC)
    P.rampe(m_rect(P, bx0 + 20.0, by0 + 17.0, 7.0, 5.0), 0.4 + 0.3 * ((np.floor(X / 0.82) % 2) == 0), R_LAITON, 0.5)             # le tambour
    P.trait(bx0 - 5.0, by0 + 6.0, bx0 + 2.4, by0 + 9.0, GO2, 2)                                      # la manivelle
    P.rect(bx0 - 6.4, by0 + 4.6, 1.6, 3.4, R_BOIS[5])
    # Le cadran de réglage : du fer-blanc gris, trop neuf, et sa vis brillante ; sur le bâti, le vieux trait de peinture.
    cdx, cdy = bx0 + 15.0, by0 - 5.0
    P.rampe(m_ell(P, cdx, cdy, 6.4, 6.4), (0.6 - 0.2 * (X - cdx) / 6.4) * (0.6 + 0.5 * Lmch), R_ETAIN, 0.5)
    for k in range(12):
        P.point(cdx + 5.0 * math.sin(k * math.pi / 6), cdy - 5.0 * math.cos(k * math.pi / 6), GR1)
    P.trait(cdx, cdy, cdx + 3.6, cdy - 2.6, ENCRE)                                                 # l'index : onze à gauche, deux à droite… pas ici
    P.point(cdx, cdy, BLANC if int(p * 8) % 4 == 0 else BM4, 2)                                    # la vis neuve
    P.rect(bx0 + 4.0, by0 + 0.6, 3.6, 1.0, R_CUIVRE[2])                                            # le vieux trait de peinture, sur le bâti
    P.trait(cdx - 2.6, cdy + 6.0, bx0 + 5.6, by0 + 0.6, R_GRANIT[1])
    # Le poids, au bout de sa chaîne, dans son puits ; arrêté.
    px_ = bx0 + 23.6
    for k in range(9):
        P.ell(px_, by0 + 22.4 + k * 1.6, 0.6, 0.9, GR3 if k % 2 else GR1)
    P.rampe(m_rect(P, px_ - 2.4, by0 + 36.0, 4.8, 6.6), 0.3 + 0.4 * (X < px_) * vac, R_GRANIT, 0.5)
    P.ell(px_, SOL + 11.0, 4.6, 1.4, ENCRE)
    # Une burette d'huile, un chiffon ; la chandelle de Pilou, posée par terre, et son halo.
    P.rampe(P.masque_poly([(142.0, SOL + 3.0), (146.0, SOL + 3.0), (145.0, SOL - 2.0), (143.0, SOL - 2.0)]), 0.5 * vac, R_LAITON, 0.5)
    P.trait(144.0, SOL - 2.0, 148.0, SOL - 6.0, LAITON)
    P.rampe(m_ell(P, 122.0, SOL + 8.0, 4.0, 1.2), 0.5 + 0.3 * (pg.fbm(X, Y * 2, 2, 1113) - 0.5), R_TOILE, 0.5)
    P.ell(CX, CY + 5.6, 2.6, 0.8, LAITON)
    P.rect(CX - 0.7, CY + 1.0, 1.4, 4.4, CREME)
    halo(P, CX, CY, 9.0, LU3, 0.4 * vac)
    fd = 0.4 * onde(p * 2, 0.4)
    P.poly([(CX - 0.8, CY + 1.0), (CX + 0.8, CY + 1.0), (CX + fd, CY - 2.8)], LU4)
    P.poly([(CX - 0.4, CY + 1.0), (CX + 0.4, CY + 1.0), (CX + fd * 0.5, CY - 1.0)], LU5)
    # À gauche : la trappe et le haut de l'échelle de fer par où l'on monte ; un chiffon rouge noué au garde-corps.
    P.ell(22.0, SOL + 6.0, 13.0, 2.6, ENCRE)
    for xq in (12.0, 30.0):
        P.courbe([(xq, SOL + 6.0), (xq, SOL - 16.0), (xq + (3.0 if xq < 20 else -3.0), SOL - 19.0)], NU2, 2)
        P.point(xq, SOL - 10.0, BM2)
    for k in range(3):
        P.trait(12.0, SOL - 4.0 - k * 5.0, 30.0, SOL - 4.0 - k * 5.0, NU2, 2)
    P.poly([(30.0, SOL - 12.0), (33.0, SOL - 9.0 + 0.4 * onde(p, 0.2)), (31.0, SOL - 6.0 + 0.5 * onde(p, 0.3))], R_CUIVRE[2])

    # ================================================================================================== premier plan
    tab.plan("premier", 1.0)
    # Un montant de la cage tout près, à gauche ; la coupole de cuivre au-dessus, et son bouton d'aération ; l'ombre en bas.
    mt = X < 3.0
    P.rampe(mt, 0.16 + 0.2 * (X > 1.6), [ENCRE, NU0, NU1, NU3], 0.5)
    for k in range(8):
        P.point(1.0, -12.0 + k * 12.0, NU3)
    cp = Y < -13.0 + 0.0006 * (X - 96.0) ** 2
    P.rampe(cp, 0.2 + 0.2 * ((np.floor((X - 96.0) / 12.0) % 2) == 0), [ENCRE, R_CUIVRE[0], NU1, R_CUIVRE[1]], 0.5)
    lisere(P, cp, R_CUIVRE[2], 0, 1, cond=X > 110)
    lisere(P, cp, BM1, 0, 1, cond=X < 70)
    P.rampe(Y > 78.6, 0.12 + 0 * X, R_FROID, 0.5)
    pg.toile_araignee(P, 192.0, -13.0, 9.0, sens=(-1, 1), coul=BM1)
    for i in range(10):
        if (p + hz(i, 1, 1114)) % 1.0 < 0.5:
            P.point(118.0 + 36.0 * hz(i, 2, 1114) + 0.6 * onde(p, hz(i, 4, 1114)), 36.0 + 22.0 * hz(i, 3, 1114), LU4)


# =====================================================================================================================
# La jetée, la nuit : le bout d'une jetée de pierre, dix heures du soir, la brume par paquets. C'est la fin de
# l'histoire : là-bas, la Dent-Creuse éclaire de nouveau (la clé) : deux éclats, un long. Sur l'eau noire, six petits
# feux de mât sortent de la brume et s'alignent sur elle. Au bout de la jetée, des silhouettes attendent, une lanterne
# à la main. La jetée est le sol : elle descend de (4, 61) à (64, 66) et s'arrête là.
# Repères : phare (156..192, 0..36), fanal de la jetée (44, 36) pour les papillons.
# =====================================================================================================================
@decor("phare-eteint", "jetee-nuit", soleil=(174.0, 5.0), tons=PHARE, nom="La jetée, la nuit", matiere=True)
def jetee_nuit(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tout = np.ones(X.shape, dtype=bool)
    HOR = 40.0
    FX, FY = 174.0, 5.6                                         # la lanterne du phare
    # Deux éclats, un long : le rythme de la Dent-Creuse sur les huit images de la boucle.
    eclat = (1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 1.0, 0.0)[int(p * 8) % 8]

    # ============================================================================================================ le ciel
    tab.plan("ciel", 0.0)
    P.horizon, P.ciel_haut, P.halo = HOR, 0.04, 0.0
    vc = pg.valeur_ciel(P, X, Y)
    df = np.hypot(X - FX, (Y - FY) * 1.3)
    P.rampe(tout, 0.02 + 0.5 * vc + eclat * 0.3 * np.exp(-(df / 34.0) ** 2), T.CIEL, 0.75)
    for i in range(60):
        ex, ey = 198.0 * hz(i, 1, 1120) - 3.0, -15.0 + 40.0 * hz(i, 2, 1120) ** 1.5
        if math.hypot(ex - FX, ey - FY) > 20.0 and (p + hz(i, 3, 1120)) % 1.0 < 0.7:
            P.point(ex, ey, T.CIEL[8] if hz(i, 4, 1120) < 0.4 else T.CIEL[5])
    tab.plan("nuages", 0.08)

    def nappe(y, epais, graine, tons, seuil=0.62, zone=None, pas=18.0):
        def dens(yy):
            return (0.4 + pg.fbm((X + 2.0 * onde(p, 0.013 * graine)) / pas, yy / 2.4, 3, graine)) * np.exp(-((yy - y - np.sin(X / 19.0 + graine)) / epais) ** 2) - seuil
        d = dens(Y)
        prox = eclat * np.exp(-(np.hypot(X - FX, (Y - FY) * 1.4) / 54.0) ** 2)
        m = d > 0
        if zone is not None:
            m &= zone
        P.rampe(m, 0.16 + 1.5 * d + 1.6 * (d - dens(Y + 1.0)) + 0.5 * prox, tons, 0.6)

    nappe(-8.0, 4.0, 1121, T.CIEL[1:7], 0.6, pas=30.0)
    nappe(10.0, 2.6, 1122, T.CIEL[2:8], 0.68, pas=26.0)
    nappe(24.0, 2.6, 1123, T.CIEL[2:8], 0.66, pas=22.0)

    # ======================================================================================================== les lointains
    tab.plan("lointains", 0.2)
    # Le faisceau : deux pinceaux de lumière dans la brume, de part et d'autre de la lanterne.
    if eclat:
        for cote in (-1, 1):
            ecart = np.abs(Y - FY - 0.03 * cote * (X - FX)) / (0.5 + 0.07 * np.abs(X - FX))
            val = 0.95 - np.abs(X - FX) / 90.0 - 0.6 * ecart
            fais = (cote * (X - FX) > 2.0) & (ecart < 1.0) & (val > 0.3)
            P.rampe(fais, val, [T.CIEL[3], T.CIEL[4], T.CIEL[5], T.CIEL[7], LU5], 0.6)
    dent_creuse(P, 174.0, HOR - 1.4, 32.0, (190.0, 0.0))
    k = 32.0 / 40.0
    gy = HOR - 1.4 - 32.0 * 0.78
    lant = m_rect(P, 174.0 - 2.0 * k, gy - 6.0 * k, 4.0 * k, 4.8 * k)
    P.remplir(lant, LU5 if eclat else LU1)                                                        # sa lanterne : allumée, enfin
    if eclat:
        halo(P, FX, gy - 3.6 * k, 9.0, LU4, 0.6)
        P.remplir(m_ell(P, FX, gy - 3.6 * k, 2.2, 2.0), BLANC)
        P.rect(174.6, HOR - 12.0, 0.6, 1.2, LU4)                                                   # et la fenêtre de la chambre de veille
    for dx in (-0.8, 0.8):
        P.rect(174.0 + dx * k - 0.2, gy - 6.0 * k, 0.4, 4.8 * k, ENCRE)
    # La Mâchoire, noire, et l'écume ; la brume qui arrive du large par paquets.
    hm = 11.0 * np.clip(pg.fbm(X / 2.0, 0 * X + 0.7, 3, 1124) - 0.38, 0, 1) * np.clip(1 - np.abs(X - 132.0) / 18.0, 0, 1) ** 0.5
    mach = (Y > HOR + 0.3 - hm) & (Y < HOR + 0.7) & (hm > 0.3)
    P.remplir(mach, ENCRE)
    lisere(P, mach, LU1 if eclat else NU2, 1, 0)
    for i in range(6):
        if (p + 0.17 * i) % 1.0 < 0.5:
            P.trait(116.0 + i * 5.6 - 1.4, HOR + 0.8, 116.0 + i * 5.6 + 2.0, HOR + 0.8, BM4)
    nappe(HOR - 2.0, 2.2, 1125, T.CIEL[4:9], 0.6, zone=X < 150)
    nappe(HOR - 9.0, 1.8, 1126, T.CIEL[3:8], 0.7, zone=X < 120)

    # ====================================================================================================== la mer, la jetée
    tab.plan("moyen", 0.5)
    P.soleil = (FX, FY)
    pg.miroir(P, tab.derriere(), HOR, fonce=(52.0, 14.0), eclats=0.9 * eclat + 0.1, rides=0.08, graine=1127, ronds=((120.0, 60.0, 0.2),))
    # Six feux de mât sortent de la brume, à la file, et s'alignent sur la Dent ; le dernier est encore dedans.
    for i in range(6):
        t = i / 5.0
        bx_ = 150.0 - 74.0 * t + 1.0 * onde(p, 0.17 * i)
        by_ = HOR + 1.4 + 9.0 * (1 - t) ** 1.6 + 0.3 * onde(p, 0.3 * i)
        s_ = 0.5 + 0.9 * (1 - t)
        visible = i < 5 or p < 0.6
        if visible:
            if i < 5:
                P.poly([(bx_ - 5.0 * s_, by_ - 1.4 * s_), (bx_ + 5.6 * s_, by_ - 1.8 * s_), (bx_ + 4.0 * s_, by_ + 0.8 * s_), (bx_ - 3.8 * s_, by_ + 0.8 * s_)], ENCRE)
                P.trait(bx_ - 5.0 * s_, by_ - 1.5 * s_, bx_ + 5.6 * s_, by_ - 1.9 * s_, NU3)
                P.trait(bx_ + 0.6 * s_, by_ - 1.6 * s_, bx_ + 0.6 * s_ + 0.3 * onde(p, 0.2 * i), by_ - 12.0 * s_, ENCRE, 2 if s_ > 1 else 1)
                P.poly([(bx_ + 1.0 * s_, by_ - 10.0 * s_), (bx_ + 1.0 * s_, by_ - 3.0 * s_), (bx_ - 4.4 * s_, by_ - 3.0 * s_)], NU1)       # la voile brune, amenée à moitié
            halo(P, bx_ + 0.6 * s_, by_ - 12.4 * s_, 3.0 + 3.0 * s_, LU3, 0.5)
            P.point(bx_ + 0.6 * s_, by_ - 12.6 * s_, LU5, 2 if s_ > 0.9 else 1)
            for j in range(int(3 + 4 * s_)):                     # le feu dans l'eau, en tirets
                if (j + int(p * 8) + i) % 3:
                    P.trait(bx_ - 0.6 * s_ + 0.4 * (j % 2), by_ + 2.0 * s_ + j * 1.3, bx_ + 1.6 * s_ + 0.4 * (j % 2), by_ + 2.0 * s_ + j * 1.3, LU3 if j < 2 else (LU2 if j < 4 else LU1))
    nappe(HOR + 4.0, 1.6, 1128, T.CIEL[3:8], 0.66, zone=X < 110)
    nappe(HOR + 11.0, 1.4, 1129, T.CIEL[2:6], 0.7, zone=(X > 70))
    # ---- La jetée : un quai de gros blocs qui descend doucement vers la droite et s'arrête ; ses flancs dans l'eau.
    fj = lambda x: 59.0 + 5.0 * (x - 4.0) / 60.0                 # son dessus (le fond du tablier)
    bout = 76.0
    dessus = (Y > fj(X)) & (Y < fj(X) + 9.0) & (X < bout + 0.3 * (Y - 60.0))
    Lw = lumiere(P, [(44.0, 64.0, 12.0, 1.0), (70.0, 66.0, 7.0, 0.6)], 0.0)
    Lc = 0.34 + 0.3 * eclat * np.clip((X - 20.0) / 60.0, 0, 1)
    paves(P, dessus, Lc, Lw, 150.0, 30.0, larg=3.0, prof=4.0, graine=1130)
    lisere(P, dessus, BM2 if eclat else GR3, 0, -1, cond=pg.fbm(X / 2.6, 0 * X, 2, 1131) > 0.3)
    flanc = (Y >= fj(X) + 9.0) & (X < bout + 0.3 * (Y - 60.0) + 1.0)
    appareil(P, flanc, 0.5 + 0.3 * eclat * np.clip((X - 30.0) / 50.0, 0, 1) - 0.016 * (Y - 70.0), (FX, FY), lh=3.2, lw=8.0, graine=1132, rampe=R_FROID, alb=0.6)
    museau = (X >= bout + 0.3 * (Y - 60.0) - 2.4) & (X < bout + 0.3 * (Y - 60.0) + 1.0) & (Y > fj(X))
    appareil(P, museau, 0.6 + 0.5 * eclat - 0.01 * (Y - 64.0), (FX, FY), lh=3.2, lw=3.0, graine=1133, rampe=R_FROID, alb=0.66)       # le musoir, face au phare
    P.remplir(flanc & (Y > 76.0) & (pg.fbm(X / 1.4, Y / 0.8, 2, 1134) > 0.5), T.S0)                 # le goémon à la ligne d'eau
    for i in range(5):                                          # le clapot contre le musoir
        t = (p + i / 5.0) % 1.0
        P.trait(bout + 2.0 + i * 2.4, 72.0 + i * 1.5, bout + 5.0 + i * 2.4 + 2 * t, 72.0 + i * 1.5, BM3 if t < 0.5 else BM1)
    # Le fanal de la jetée, sur son fût de fonte ; deux bittes, une aussière, l'échelle de fer.
    lx_ = 44.0
    P.rampe(m_rect(P, lx_ - 0.8, 38.0, 1.6, 26.0), 0.2 + 0.5 * (X > lx_), [ENCRE, NU0, GR1, GR2, GR3], 0.5)
    P.rect(lx_ - 1.8, 62.0, 3.6, 2.6, GR1)
    halo(P, lx_, 35.0, 14.0, LU2, 0.34)
    halo(P, lx_, 35.0, 6.0, LU3, 0.5)
    P.poly([(lx_ - 2.6, 32.6), (lx_ + 2.6, 32.6), (lx_, 30.4)], ENCRE)
    P.rect(lx_ - 1.8, 32.6, 3.6, 5.0, LU4 if int(p * 8) % 5 else LU3)
    P.rect(lx_ - 0.6, 33.6, 1.2, 3.0, LU5)
    P.rect(lx_ - 2.2, 37.6, 4.4, 0.8, ENCRE)
    for dx in (-2.0, 1.6):
        P.rect(lx_ + dx, 32.6, 0.4, 5.0, ENCRE)
    for bx_ in (18.0, 62.0):
        by_ = float(fj(np.array([bx_]))[0]) + 1.0
        bt = m_rect(P, bx_ - 1.5, by_ - 3.6, 3.0, 4.6) | m_ell(P, bx_, by_ - 3.6, 2.3, 1.2)
        P.rampe(bt, 0.3 + 0.4 * (X - bx_) / 2.3 * (1 if eclat else 0.3), [ENCRE, NU0, GR1, GR2, GR3, BM2], 0.5)
    P.courbe([(62.0, 62.6), (70.0, 66.6 + 0.3 * onde(p, 0.3)), (78.0, 70.0), (82.0, 78.0)], GO2, 1)
    for ex in (70.0, 73.0):
        P.courbe([(ex, 68.0), (ex, 62.0), (ex + 1.0, 60.8), (ex + 1.6, 62.0)], GR1, 2)
    # Au bout : ceux qui attendent. Trois silhouettes de dos, une lanterne levée, une écharpe qui vole.
    for i, (sx_, h, larg_) in enumerate(((66.6, 13.0, 3.2), (70.4, 10.0, 2.6), (62.6, 11.6, 3.0))):
        sy_ = float(fj(np.array([sx_]))[0]) + 3.0
        corps = P.masque_poly([(sx_ - larg_ / 2, sy_), (sx_ + larg_ / 2, sy_), (sx_ + larg_ * 0.36, sy_ - h * 0.76), (sx_ - larg_ * 0.36, sy_ - h * 0.76)])
        tete = m_ell(P, sx_, sy_ - h * 0.86, 1.3, 1.4)
        P.remplir(corps | tete, ENCRE if i != 1 else NU0)
        lisere(P, corps | tete, (LU3 if eclat else NU3), 1, 0)                                      # le phare les ourle
    P.trait(67.6, 59.6, 70.6, 54.0, ENCRE, 2)                                                      # un bras levé, la lanterne au bout
    halo(P, 71.0, 53.0, 5.0, LU3, 0.5)
    P.rect(70.2, 52.0, 1.6, 2.2, LU5)
    v_ = onde(p)
    P.poly([(62.0, 56.0), (57.6, 56.6 + 0.6 * v_), (58.0, 58.0 + 0.6 * v_)], R_CUIVRE[2])           # l'écharpe d'Odile
    # Des casiers, une caisse, une corne de brume à soufflet posée là (on aurait pu sonner toute la nuit).
    casier(P, 8.0, 64.6, 1.1)
    casier(P, 14.0, 60.6, 0.9)
    co = m_rect(P, 28.0, 60.6, 5.0, 4.4)
    P.rampe(co, 0.4 + 0.2 * ((np.floor(Y / 1.2) % 2) == 0), R_BOIS, 0.5)
    P.poly([(33.0, 61.4), (33.0, 63.6), (38.0, 65.0), (38.0, 60.0)], LAITON)
    P.ell(38.0, 62.5, 0.8, 2.5, GO1)
    goeland(P, 18.0, float(fj(np.array([18.0]))[0]) - 2.6, sens=1, pose=True)

    # ================================================================================================== premier plan
    tab.plan("premier", 1.0)
    # Tout près, à gauche : le parapet de la jetée, un filet jeté dessus, des flotteurs ; en haut à gauche, un mât de
    # pavillon et sa drisse ; à droite en bas, un rocher noir que la vague lèche.
    par = (X < 12.0 + 1.6 * np.sin(Y / 5.0)) & (Y > 44.0 + 0.5 * X)
    appareil(P, par, 0.34 + 0.2 * eclat + 0 * X, (FX, FY), lh=4.6, lw=7.0, graine=1135, rampe=R_FROID, alb=0.5)
    lisere(P, par, BM1 if eclat else GR2, 1, 0, cond=pg.fbm(Y / 3.0, 0 * Y, 2, 1136) > 0.4)
    for j in range(6):
        P.courbe([(-6.0, 46.0 + j * 2.2), (2.0, 50.0 + j * 2.4 + 0.3 * onde(p, 0.1 * j)), (11.0, 49.6 + j * 2.6)], GO2 if j % 2 else GO1, 1)
    for i, (fx_, fy_) in enumerate(((0.0, 60.0), (6.0, 64.0), (10.0, 58.0))):
        P.ell(fx_, fy_, 1.4, 1.4, LU2)
        P.point(fx_ + 0.5, fy_ - 0.5, LU4)
    P.trait(3.0, -16.0, 3.0, 46.0, ENCRE, 2)
    P.trait(3.4, -16.0, 9.0 + 0.4 * onde(p, 0.2), 44.0, NU2)
    pav = onde(p, 0.1)
    P.poly([(3.6, -12.0), (15.0, -10.0 + 0.8 * pav), (14.0, -5.0 + 0.8 * pav), (3.6, -6.0)], R_TOILE[2])   # le pavillon de la mairie, hissé pour eux
    P.poly([(3.6, -9.0), (14.6, -7.6 + 0.8 * pav), (14.0, -5.0 + 0.8 * pav), (3.6, -6.0)], R_PAPIER[3])
    fr_ = lambda x: 78.6 - 6.0 * np.exp(-((x - 190.0) / 13.0) ** 2) - 2.0 * np.exp(-((x - 150.0) / 9.0) ** 2) + 0.8 * (pg.fbm(x / 3.0, 0 * x, 3, 1137) - 0.5)
    rc = (Y > fr_(X)) & (X > 120)
    P.rampe(rc, 0.2 + 0.4 * (pg.fbm(X / 3.0 + 0.3 * Y, Y / 1.6, 3, 1138) - 0.5), [ENCRE, NU0, T.S0, NU1, NU2], 0.5)
    lisere(P, rc, BM2 if eclat else NU3, 0, -1, cond=pg.fbm(X / 2.0, 0 * X, 2, 1139) > 0.4)
    for i in range(5):
        t = (p + i / 5.0) % 1.0
        ex = 136.0 + i * 12.0
        P.trait(ex - 2.0 - t, float(fr_(np.array([ex]))[0]) - 0.4, ex + 2.0 + t, float(fr_(np.array([ex]))[0]) - 0.4, BM4 if t < 0.5 else BM2)
