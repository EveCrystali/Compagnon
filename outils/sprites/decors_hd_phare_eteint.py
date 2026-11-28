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
# Chez Pilou : un coin de bureau en bois au petit matin. Un encrier ouvert, une bougie, une enveloppe sans timbre
# appuyée contre l'encrier (la clé) ; lumière dorée et calme. On est si petit que le plateau du bureau est le sol (y = 52).
# =====================================================================================================================
@decor("phare-eteint", "chez-pilou", soleil=(30.0, -6.0), tons=AUBE, nom="Chez Pilou")
def chez_pilou(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    # ---- Le mur : lambris de bois clair, la fenêtre de l'aube à gauche, une étagère de livres.
    P.rampe(np.ones(X.shape, dtype=bool), 0.62 - 0.004 * (X - 30) + 0.2 * (pg.fbm(X / 3.0, Y / 22.0, 3, 510) - 0.5) - 0.003 * (Y + 16),
            [BO2, BO3, BO4, LU4], 0.7)
    P.remplir((np.abs((X % 16.0) - 8.0) < 0.3) & (Y < 40), BO2)                               # les lames du lambris
    tab.plan("lointains", 0.2)
    wx, wy, ww, wh = 6.0, -12.0, 40.0, 42.0
    P.rect(wx - 2.5, wy - 2.5, ww + 5, wh + 5, BO1)
    fen = (X > wx) & (X < wx + ww) & (Y > wy) & (Y < wy + wh)
    P.rampe(fen, 0.25 + 0.015 * (Y - wy) + 0.1 * (pg.fbm(X / 12.0, Y / 5.0, 2, 511) - 0.5), [T.CIEL[5], T.CIEL[8], T.CIEL[10], T.CIEL[11]], 0.7)
    for i, (x, w, top) in enumerate(((wx + 6, 7, 18), (wx + 16, 5, 12), (wx + 26, 8, 20), (wx + 35, 5, 16))):   # les toits d'en face
        P.remplir(fen & (np.abs(X - x) < w / 2) & (Y > top), T.CIEL[4] if i % 2 else T.CIEL[5])
        P.remplir(fen & (np.abs(X - x) < w / 2 + 1 - (Y - top + 4) * 0.4) & (Y > top - 4) & (Y <= top), T.CIEL[3])
    P.remplir(fen & (Y > 24), T.CIEL[4])
    P.rect(wx + ww / 2 - 0.8, wy, 1.6, wh, BO1)
    P.rect(wx, wy + wh / 2 - 0.8, ww, 1.6, BO1)
    P.rect(wx - 4, wy + wh + 2.5, ww + 8, 2.0, BO3)
    P.poly([(wx + ww + 2.5, wy - 2.5), (wx + ww + 9, wy - 2.5), (wx + ww + 7, wy + wh + 2.5), (wx + ww + 2.5, wy + wh + 2.5)], VOLET)   # le rideau
    for j in range(4):
        P.trait(wx + ww + 4 + j * 1.4 + 0.3 * onde(p, 0.1 * j), wy - 2, wx + ww + 3.6 + j * 1.2, wy + wh + 2, VOLET2)
    rai(P, wx + ww * 0.6, wy + wh * 0.3, 78.0, 26.0, 1.1, LU5, 0.34, 30, 512)
    ex, ey = 104.0, 2.0                                         # l'étagère : livres, un coquillage, une boussole
    P.rect(ex, ey + 12.0, 84.0, 1.6, BO1)
    P.rect(ex, ey + 12.0, 84.0, 0.5, BO3)
    x = ex + 2.0
    i = 0
    while x < ex + 60:
        w, h = 2.4 + 2.2 * hz(i, 1, 513), 8 + 3.6 * hz(i, 2, 513)
        c0 = (VI1, NU2, LU1, GO1, VOLET, BO2, NU3)[int(hz(i, 3, 513) * 7)]
        P.rect(x, ey + 12.0 - h, w, h, c0)
        P.rect(x, ey + 12.0 - h, 0.5, h, BM2)
        P.rect(x, ey + 12.0 - h * 0.7, w, 0.5, LAITON)
        x += w + 0.3
        i += 1
    P.ell(ex + 68, ey + 10.2, 3.2, 1.9, CREME)
    P.ell(ex + 67, ey + 9.8, 1.8, 1.0, LU4)
    P.ell(ex + 78, ey + 9.0, 3.0, 3.0, LAITON)
    P.ell(ex + 78, ey + 9.0, 2.2, 2.2, CREME)
    P.trait(ex + 78, ey + 9.0, ex + 79.2 + 0.3 * onde(p), ey + 7.6, LU2)
    for (x, y, w, h, c0) in ((118.0, 20.0, 14.0, 11.0, CREME), (136.0, 22.0, 10.0, 13.0, BM4)):  # une carte marine, une gravure
        P.rect(x, y, w, h, c0)
        P.courbe([(x + 1, y + h * 0.7), (x + w * 0.4, y + h * 0.4), (x + w - 1, y + h * 0.6)], NU3, 1)
        P.point(x + w / 2, y + 0.6, LU2, 2)
    tab.plan("moyen", 0.5)
    # ---- Le plateau du bureau : un vieux bois ciré vu de tout près, qui fuit vers le mur ; la lumière y dessine la fenêtre.
    sol = Y > 44.0
    P.rampe(sol, 0.45 + 0.3 * (pg.fbm(X / 26.0, (Y - 44) * (1 + (80 - Y) / 30.0) / 2.0, 3, 514) - 0.5) + 0.006 * (80 - Y), [BO1, BO2, BO3, BO4], 0.7)
    dallage(P, sol & (P.T < 0.3), 80.0, 30.0, BO2, BO3, larg=14.0, prof=0.0, joint=BO1)
    voile(P, sol & (np.abs(X - (60 + (Y - 44) * 1.1)) < 18 + (Y - 44) * 0.5), LU5, 0.3)
    P.remplir((Y > 44.0) & (Y < 44.7), LU4)
    # L'encrier ouvert et sa plume ; l'enveloppe sans timbre, appuyée contre lui.
    kx, ky = 62.0, 51.0
    P.ell(kx, ky + 0.6, 9.5, 2.0, BO1)                          # son ombre
    P.ell(kx, ky - 5.0, 7.0, 6.0, NU1, cond=Y < ky)
    P.rect(kx - 7.0, ky - 5.0, 14.0, 5.0, NU1)
    P.ell(kx, ky, 7.0, 1.6, NU0)
    P.ell(kx - 2.0, ky - 6.0, 2.6, 3.6, NU3)                    # le reflet du verre
    P.ell(kx - 2.4, ky - 7.0, 1.0, 1.6, BM3)
    P.rect(kx - 3.4, ky - 13.0, 6.8, 3.0, NU2)
    P.ell(kx, ky - 13.0, 3.4, 1.0, NU0)
    P.ell(kx, ky - 13.0, 2.4, 0.6, ENCRE)
    P.poly([(kx + 1.0, ky - 12.6), (kx + 15.0, ky - 34.0 + 0.5 * onde(p)), (kx + 19.0, ky - 31.0 + 0.5 * onde(p)), (kx + 3.0, ky - 12.6)], CREME)
    P.trait(kx + 1.6, ky - 12.6, kx + 17.0, ky - 32.6 + 0.5 * onde(p), BM3)
    for j in range(7):
        P.trait(kx + 5 + j * 1.7, ky - 18 - j * 2.2, kx + 8.4 + j * 1.7, ky - 17.4 - j * 2.2, BM3)
    env = [(kx - 30.0, ky - 2.0), (kx - 7.0, ky - 4.0), (kx - 5.0, ky - 19.0), (kx - 28.0, ky - 17.0)]
    P.poly([(q[0] + 1.4, q[1] + 1.2) for q in env], BO1)
    me = P.poly(env, CREME)
    P.rampe(me, 0.6 + 0.02 * (X - kx + 30) - 0.02 * (Y - ky + 19), [BM4, CREME, T.CIEL[11]], 0.5)
    P.trait(env[3][0], env[3][1], kx - 17.0, ky - 9.6, BM3)     # le rabat
    P.trait(env[2][0], env[2][1], kx - 17.0, ky - 9.6, BM3)
    P.ell(kx - 17.0, ky - 9.8, 1.6, 1.4, LU2)                   # le cachet de cire
    P.point(kx - 17.3, ky - 10.2, LU4)
    P.rect(kx - 25.0, ky - 6.6, 10.0, 0.5, BM2)                 # l'adresse : un trait, pas de timbre
    bougie(P, 98.0, 51.6, h=9.0, lueur=20.0)
    # Autres habitants du bureau : un buvard, des lettres, une tasse qui fume, une loupe, des miettes.
    P.poly([(12.0, 62.0), (44.0, 60.0), (48.0, 74.0), (10.0, 77.0)], VI2)
    P.poly([(14.0, 63.2), (43.0, 61.4), (46.0, 72.8), (12.4, 75.4)], BM4)
    for j in range(5):
        P.trait(17.0, 65.0 + j * 2.0, 40.0 - j * 3, 64.0 + j * 2.0, NU3)
    tx, ty = 146.0, 50.0
    P.ell(tx, ty + 0.5, 6.0, 1.4, BO1)
    P.rect(tx - 4.0, ty - 7.0, 8.0, 7.0, VOLET)
    P.rect(tx - 4.0, ty - 7.0, 2.0, 7.0, VOLET2)
    P.ell(tx, ty - 7.0, 4.0, 1.1, CREME)
    P.ell(tx, ty - 7.0, 3.0, 0.7, BO3)
    P.courbe([(tx + 4.0, ty - 5.6), (tx + 7.0, ty - 3.6), (tx + 4.0, ty - 1.4)], VOLET, P.ep(0.7))
    for k in range(4):
        t = (p + k / 4.0) % 1.0
        voile(P, np.hypot(X - (tx + 1.6 * math.sin(t * 6.0 + k)), Y - (ty - 9.0 - 14 * t)) < 0.8 + 1.6 * t, T.CIEL[11], 0.55 - 0.5 * t)
    P.ell(172.0, 66.0, 5.0, 2.4, LAITON)
    P.ell(172.0, 66.0, 3.8, 1.7, BM4)
    P.trait(176.0, 67.6, 186.0, 72.0, BO1, P.ep(1.0))
    for i in range(9):
        P.point(120 + 40 * hz(i, 1, 515), 58 + 16 * hz(i, 2, 515), BO4)
    tab.plan("premier", 1.0)
    # ---- Premier plan : le dos d'un gros livre à gauche, le bord du bureau en bas, dans l'ombre.
    P.poly([(-6.0, 80.0), (-6.0, 56.0), (8.0, 54.0), (12.0, 80.0)], VI1)
    P.poly([(-6.0, 56.0), (8.0, 54.0), (9.0, 57.0), (-6.0, 59.0)], BM3)
    P.rect(-6.0, 64.0, 16.0, 1.0, LAITON)
    voile(P, Y > 77.6, BO1, 0.4)
    poussiere(P, 40, -10, 150, 50, 30, LU5, 516)


# =====================================================================================================================
# Le quai de Trébrume : un petit quai de pierre au crépuscule, dans une brume épaisse. Barques tirées au sec, casiers à
# homards, filets ; au large, la silhouette noire d'un phare éteint sur son rocher (la clé). Le quai est le sol (y = 66).
# =====================================================================================================================
@decor("phare-eteint", "port-trebrume", soleil=(143.0, 30.0), tons=PHARE, nom="Le quai de Trébrume")
def port_trebrume(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=46.0, haut=0.24, halo=0.14, disque=0)
    tab.plan("nuages", 0.08)
    pg.voiles(P, y=-4.0, epais=10.0, seuil=0.54, graine=520)
    pg.voiles(P, y=22.0, epais=8.0, seuil=0.56, graine=521)
    tab.plan("lointains", 0.2)
    # ---- Le large : la Dent-Creuse et son phare noir, sans lumière ; la brume l'efface par le bas.
    phare(P, 143.0, 44.0, 44.0, T.CIEL[2], T.CIEL[3])
    for i in range(5):
        goeland(P, 108 + 9 * i + 3 * onde(p, 0.2 * i), 6 + 5 * hz(i, 1, 522) + onde(p, 0.3 * i), pose=False)
    brume(P, 40.0, 5.0, 1, T.CIEL[7], 0.6)
    brume(P, 30.0, 4.0, 2, T.CIEL[6], 0.4)
    tab.plan("moyen", 0.5)
    # ---- La mer, plate et sombre, qui reflète le peu de ciel ; les maisons du port à gauche, fenêtres allumées.
    for i, (x, w, top, c0) in enumerate(((-2, 22, 20, GR2), (18, 16, 26, GR1), (34, 20, 16, GR2), (54, 14, 28, GR1))):
        P.rect(x, top, w, 46 - top, c0)
        P.poly([(x - 1.5, top), (x + w + 1.5, top), (x + w / 2, top - 8)], VI1)
        P.poly([(x + w / 2, top - 8), (x + w + 1.5, top), (x + w / 2 + 2, top)], VI2)
        P.rect(x + w * 0.7, top - 9.0, 2.0, 5.0, GR1)
        for j in range(2):
            for k in range(2):
                vif = hz(i * 4 + j, k, 523) < 0.6 and (p + hz(i, j * 2 + k, 524)) % 1.0 < 0.9
                P.rect(x + 3 + k * (w - 9), top + 4 + j * 8, 3.0, 4.0, LU4 if vif else NU1)
                if vif:
                    halo(P, x + 4.5 + k * (w - 9), top + 6 + j * 8, 6.0, LU3, 0.35)
    pg.miroir(P, tab.derriere(), 46.0, fonce=(54.0, 14.0), eclats=0.0, rides=0.05, graine=525)
    for i, (x, y) in enumerate(((96.0, 54.0), (120.0, 50.0))):   # deux barques au mouillage, leurs feux
        y = y + 0.3 * onde(p, 0.3 * i)
        P.poly([(x - 7, y - 1.6), (x + 7.6, y - 2.0), (x + 5.6, y + 0.8), (x - 5.4, y + 0.8)], ENCRE)
        P.trait(x - 7, y - 1.7, x + 7.6, y - 2.1, GR3)
        P.trait(x, y - 1.8, x, y - 13.0, ENCRE)
        P.point(x, y - 13.4, LU4 if (p + 0.4 * i) % 1.0 < 0.8 else LU2)
        halo(P, x, y - 13.0, 4.0, LU3, 0.4)
        for j in range(4):
            if (j + int(p * 8)) % 3:
                P.trait(x - 1.5, y + 2 + j * 1.5, x + 1.5, y + 2 + j * 1.5, LU2)
    brume(P, 50.0, 3.0, 3, T.CIEL[7], 0.5)
    brume(P, 57.0, 2.4, 4, T.CIEL[6], 0.4, x0=70)
    # ---- Le quai : de grosses pierres de taille, mouillées ; un escalier qui descend à l'eau ; deux bittes d'amarrage.
    quai = (Y > 58.0) & (X < 118.0 + (Y - 58) * 0.5)
    P.rampe(quai, 0.5 + 0.2 * (pg.fbm(X / 5.0, Y / 2.0, 3, 526) - 0.5) - 0.012 * (Y - 58), [GR1, GR2, GR3, GR4], 0.7)
    dessus = quai & (Y < 68.0)
    dallage(P, dessus, 143.0, 40.0, GR3, GR2, larg=7.0, prof=1.1, joint=GR1)
    voile(P, dessus, BM2, 0.2)
    pierres_de_taille(P, quai & (Y >= 68.0), GR2, GR1, lh=4.0, lw=9.0)
    P.remplir(quai & (np.abs(Y - 68.0) < 0.5), GR4)
    for j in range(5):                                          # l'escalier vers l'eau
        P.rect(100.0 + j * 4.0, 68.0 + j * 2.4, 22.0 - j * 4.0, 2.4, GR3 if j % 2 else GR2)
        P.rect(100.0 + j * 4.0, 68.0 + j * 2.4, 22.0 - j * 4.0, 0.5, GR4)
    for x in (58.0, 112.0):
        P.rect(x - 1.4, 60.6, 2.8, 5.4, ENCRE)
        P.ell(x, 60.6, 2.2, 1.0, GR2)
        P.courbe([(x, 62.0), (x + 12, 66.0 + 0.4 * onde(p)), (x + 22, 60.0)], GO2, 1)
    # Les barques au sec, les casiers, les filets qui sèchent, un tonneau, le fanal du quai.
    barque_a_sec(P, 46.0, 62.0, 26.0)
    barque_a_sec(P, 92.0, 60.0, 18.0, coul=(NU0, NU2, BM2), sens=-1)
    for i, (x, y, k) in enumerate(((4.0, 62.0, 1.2), (12.0, 61.0, 1.0), (8.0, 57.0, 1.0), (70.0, 61.0, 0.9))):
        casier(P, x, y, k)
    P.trait(-4.0, 34.0, -4.0, 62.0, BO1, P.ep(0.9))               # le séchoir à filets
    P.trait(22.0, 36.0, 22.0, 61.0, BO1, P.ep(0.9))
    for j in range(9):
        y0 = 36.0 + j * 2.0
        P.courbe([(-4.0, y0), (9.0, y0 + 4.0 + 0.4 * onde(p, 0.1 * j)), (22.0, y0 + 1.0)], GO2 if j % 2 else GO1, 1)
    for x in np.arange(-2.0, 22.0, 2.4):
        P.trait(x, 37.0 + abs(x - 9) * -0.2 + 3.6, x + 0.6, 56.0, GO1)
    for x in (2.0, 10.0, 17.0):
        P.ell(x, 55.0 + (x % 3), 1.1, 1.1, LU2)                  # les flotteurs
    P.trait(128.0, 40.0, 128.0, 60.0, ENCRE, P.ep(0.8))           # le poteau du fanal
    P.trait(128.0, 41.0, 133.0, 41.0, ENCRE, P.ep(0.6))
    fanal(P, 133.0, 47.6 + 0.3 * onde(p), 1.1, lueur=16.0)
    tab.plan("premier", 1.0)
    # ---- Premier plan : le bord du quai dans l'ombre, une ancre, des cordages lovés, la brume qui passe devant.
    bas = Y > 76.0
    P.rampe(bas, 0.3 + 0.3 * (pg.fbm(X / 5.0, Y / 2.0, 2, 527) - 0.5), [ENCRE, NU0, GR1], 0.8)
    ax, ay = 160.0, 76.0
    P.trait(ax, ay - 18.0, ax, ay, ENCRE, P.ep(1.4))
    P.courbe([(ax - 8.0, ay - 6.0), (ax - 5.0, ay), (ax, ay + 1.0), (ax + 5.0, ay), (ax + 8.0, ay - 6.0)], ENCRE, P.ep(1.4))
    P.trait(ax - 5.0, ay - 15.0, ax + 5.0, ay - 15.0, ENCRE, P.ep(1.0))
    P.ell(ax, ay - 19.6, 2.0, 2.0, ENCRE)
    P.ell(ax, ay - 19.6, 1.0, 1.0, NU1)
    P.trait(ax + 0.6, ay - 17.0, ax + 0.6, ay - 2.0, GR2)
    for r in (5.0, 3.6, 2.2):
        P.ell(178.0, 76.0, r, r * 0.4, GO1 if r != 3.6 else GO2)
    brume(P, 72.0, 3.0, 5, T.CIEL[6], 0.35)


# =====================================================================================================================
# Le Bigorneau Qui Tousse : la salle basse d'une auberge de pêcheurs. Poutres, comptoir, marmite de soupe fumante, la
# grande horloge (la clé), fenêtres jaunes embuées, un ciré jaune pendu à une patère.
# =====================================================================================================================
@decor("phare-eteint", "auberge-bigorneau", soleil=(150.0, 40.0), tons=PHARE, nom="Le Bigorneau Qui Tousse")
def auberge_bigorneau(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    fx_, fy_ = 150.0, 46.0                                      # l'âtre : la source de lumière
    tab.plan("ciel", 0.0)
    d = np.hypot(X - fx_, (Y - fy_) * 1.2)
    P.rampe(np.ones(X.shape, dtype=bool), 0.95 - d / 150.0 + 0.16 * (pg.fbm(X / 10.0, Y / 8.0, 3, 530) - 0.5), [BO1, BO2, BO3, LU2, LU4], 0.8)
    P.remplir((Y > 30) & (Y < 62) & (np.abs((X % 9.0) - 4.5) < 0.3), BO1)                    # le lambris bas
    P.remplir((np.abs(Y - 30.0) < 0.6), BO1)
    tab.plan("lointains", 0.2)
    # ---- Les deux fenêtres embuées, jaunes de l'intérieur, bleues du dehors ; on y a dessiné du doigt.
    for i, wx in enumerate((84.0, 112.0)):
        P.rect(wx - 2, 2.0, 22.0, 24.0, BO1)
        fen = (X > wx) & (X < wx + 18) & (Y > 4.0) & (Y < 24.0)
        P.rampe(fen, 0.4 + 0.3 * (pg.fbm(X / 6.0, Y / 5.0, 3, 531 + i) - 0.5), [NU2, NU3, BM1, BM2], 0.8)
        voile(P, fen, LU4, 0.25)
        P.rect(wx + 8.4, 4.0, 1.2, 20.0, BO1)
        P.rect(wx, 13.4, 18.0, 1.2, BO1)
        if i == 0:
            P.ell(wx + 4.4, 9.0, 2.0, 2.0, NU1)                 # un bonhomme tracé dans la buée
            P.trait(wx + 4.4, 11.0, wx + 4.4, 12.6, NU1)
        for k in range(3):                                      # des gouttes qui glissent
            t = (p + k / 3.0 + i * 0.2) % 1.0
            P.trait(wx + 11 + k * 2.2, 5 + 16 * t, wx + 11 + k * 2.2, 6.6 + 16 * t, BM3)
    # ---- Les poutres du plafond, noircies ; ce qui y pend : des filets, des bouées de verre, un jambon, des oignons.
    P.rect(-6.0, -16.0, 204.0, 5.0, BO1)
    for i in range(7):
        x = -8 + i * 32
        P.poly([(x, -11.0), (x + 7, -11.0), (x + 5, -4.0), (x - 2, -4.0)], BO1)
        P.poly([(x + 5, -11.0), (x + 7, -11.0), (x + 5, -4.0), (x + 3, -4.0)], BO2)
    for i, (x, l, sorte) in enumerate(((20.0, 9.0, 0), (36.0, 12.0, 1), (62.0, 8.0, 2), (76.0, 11.0, 0), (130.0, 7.0, 1), (174.0, 10.0, 2))):
        bal = 0.5 * onde(p, 0.17 * i)
        P.trait(x, -4.0, x + bal, -4.0 + l, GO1)
        if sorte == 0:                                          # une bouée de verre dans son filet
            P.ell(x + bal, -4.0 + l + 3.0, 3.0, 3.0, T.S2)
            P.ell(x + bal - 0.8, -4.0 + l + 2.0, 1.2, 1.2, T.S4)
            P.remplir((np.hypot(X - x - bal, Y + 4.0 - l - 3.0) < 3.0) & ((P.XI + P.YI) % 4 == 0), GO2)
        elif sorte == 1:                                        # une tresse d'oignons
            for j in range(4):
                P.ell(x + bal + (j % 2) * 1.6 - 0.8, -4.0 + l + 1.6 + j * 2.4, 1.6, 1.5, LU3 if j % 2 else LU2)
        else:                                                   # un jambon
            P.ell(x + bal, -4.0 + l + 4.0, 2.8, 4.2, LU1)
            P.ell(x + bal - 0.6, -4.0 + l + 3.4, 1.6, 2.6, LU2)
    tab.plan("moyen", 0.5)
    # ---- Le plancher, puis l'âtre et sa marmite (la soupe fume), le comptoir, les tables.
    sol = Y > 62.0
    dallage(P, sol, 96.0, 46.0, BO3, BO2, larg=3.4, prof=0.0, joint=BO1)
    voile(P, sol & (np.hypot(X - fx_, (Y - 70) * 3.0) < 70), LU3, 0.3)
    voile(P, sol & (np.hypot(X - fx_, (Y - 70) * 3.0) > 96), BO1, 0.5)
    ax0, ax1 = 130.0, 172.0                                     # la cheminée de granit
    P.rect(ax0 - 4, 14.0, ax1 - ax0 + 8, 50.0, GR2)
    pierres_de_taille(P, (X > ax0 - 4) & (X < ax1 + 4) & (Y > 14.0) & (Y < 64.0), GR2, GR1, lh=4.4, lw=8.0)
    P.rect(ax0 - 6, 28.0, ax1 - ax0 + 12, 3.0, BO2)
    P.rect(ax0 - 6, 28.0, ax1 - ax0 + 12, 0.7, BO4)
    P.rect(ax0, 34.0, ax1 - ax0, 30.0, ENCRE)
    halo(P, fx_ + 1, 56.0, 30.0, LU2, 0.7, ry=22)
    for i in range(7):                                          # les flammes
        f = onde(p * 2, 0.14 * i)
        bx_ = ax0 + 8 + i * 4.4
        P.poly([(bx_ - 2.4, 63.0), (bx_ + 2.4, 63.0), (bx_ + f, 63.0 - 9 - 4 * hz(i, 1, 532) - 2 * abs(f))], LU2)
        P.poly([(bx_ - 1.4, 63.0), (bx_ + 1.4, 63.0), (bx_ + f * 0.6, 63.0 - 5 - 2 * hz(i, 2, 532))], LU4)
    P.rect(ax0 + 4, 61.0, ax1 - ax0 - 8, 2.6, BO1)                # les bûches
    P.trait(fx_ + 1, 34.0, fx_ + 1, 44.0, ENCRE)                  # la crémaillère
    P.ell(fx_ + 1, 50.0, 8.0, 6.0, GR1)                           # la marmite
    P.rect(fx_ - 7, 44.6, 16.0, 2.0, GR1)
    P.ell(fx_ + 1, 44.6, 8.0, 1.6, GR3)
    P.ell(fx_ + 1, 44.6, 6.6, 1.0, LU2)
    P.ell(fx_ - 3, 50.0, 1.6, 2.6, GR3)
    for k in range(5):
        t = (p + k / 5.0) % 1.0
        voile(P, np.hypot(X - (fx_ + 1 + 2.4 * math.sin(t * 6.0 + k)), Y - (43.0 - 16 * t)) < 1.0 + 2.6 * t, BM4, 0.6 - 0.55 * t)
    for (x, c0) in ((ax0 + 4, LAITON), (ax0 + 12, CREME), (ax1 - 10, VOLET)):              # sur le manteau : pots, coquillages
        P.rect(x, 24.0, 4.0, 4.0, c0)
        P.rect(x, 24.0, 4.0, 0.6, LU5)
    # La grande horloge de parquet : caisse sombre, cadran crème, le balancier de laiton qui bat.
    hx_, hy_ = 59.0, 10.0
    P.rect(hx_ - 7.0, hy_, 14.0, 52.0, BO1)
    P.rect(hx_ - 7.0, hy_, 2.0, 52.0, BO2)
    P.poly([(hx_ - 8.5, hy_), (hx_ + 8.5, hy_), (hx_ + 6.0, hy_ - 4.0), (hx_ - 6.0, hy_ - 4.0)], BO2)
    P.rect(hx_ - 8.5, hy_ + 50.0, 17.0, 3.0, BO2)
    P.ell(hx_, hy_ + 9.0, 5.6, 5.6, LAITON)
    P.ell(hx_, hy_ + 9.0, 4.8, 4.8, CREME)
    for k in range(12):
        P.point(hx_ + 4.0 * math.cos(k * math.pi / 6), hy_ + 9.0 + 4.0 * math.sin(k * math.pi / 6), ENCRE)
    P.trait(hx_, hy_ + 9.0, hx_ - 2.4, hy_ + 7.6, ENCRE)
    a = int(p * 8) * math.pi / 4
    P.trait(hx_, hy_ + 9.0, hx_ + 3.6 * math.sin(a), hy_ + 9.0 - 3.6 * math.cos(a), LU1)
    P.rect(hx_ - 4.0, hy_ + 18.0, 8.0, 28.0, ENCRE)
    P.rect(hx_ - 4.0, hy_ + 18.0, 8.0, 0.6, BO3)
    ang = 0.26 * onde(p)
    bx_, by_ = hx_ + 22.0 * math.sin(ang), hy_ + 19.0 + 22.0 * math.cos(ang)
    P.trait(hx_, hy_ + 19.0, bx_, by_, LAITON)
    P.ell(bx_, by_, 2.4, 2.4, LAITON)
    P.ell(bx_ - 0.6, by_ - 0.6, 1.2, 1.2, LAITON2)
    # Le comptoir, à gauche : tonneau, chopes d'étain, une bouteille ; le ciré jaune à sa patère.
    P.rect(-6.0, 46.0, 44.0, 18.0, BO2)
    P.rampe((X < 38) & (Y > 46) & (Y < 64), 0.3 + 0.012 * X + 0.25 * (pg.fbm(X / 1.4, Y / 14.0, 2, 533) - 0.5), [BO1, BO2, BO3], 0.6)
    P.rect(-6.0, 44.0, 46.0, 2.4, BO3)
    P.rect(-6.0, 44.0, 46.0, 0.6, BO4)
    P.ell(6.0, 38.0, 6.0, 6.4, BO2)
    P.ell(6.0, 38.0, 4.6, 5.0, BO3)
    for y in (33.6, 42.4):
        P.rect(0.4, y, 11.2, 0.8, GR3)
    P.rect(5.0, 37.0, 3.4, 1.4, LAITON)
    for i, x in enumerate((18.0, 24.0, 31.0)):
        P.rect(x, 39.6, 3.6, 4.4, GR3)
        P.rect(x, 39.6, 1.0, 4.4, GR4)
        P.ell(x + 1.8, 39.6, 1.8, 0.6, CREME)
    px_, py_ = 44.0, 14.0                                       # le ciré
    P.rect(px_ - 1.0, py_ - 2.0, 2.0, 2.0, BO1)
    cire = [(px_ - 5.0, py_), (px_ + 5.0, py_), (px_ + 7.6 + 0.3 * onde(p), py_ + 30.0), (px_ - 7.6 + 0.3 * onde(p), py_ + 30.0)]
    mc = P.poly(cire, CIRE)
    P.rampe(mc, 0.3 + 0.07 * (X - px_ + 7) + 0.3 * (pg.fbm(X / 2.0, Y / 9.0, 2, 534) - 0.5), [LAITON, CIRE, CIRE2], 0.6)
    P.trait(px_, py_ + 2.0, px_ + 0.3, py_ + 29.0, LAITON)
    P.ell(px_, py_ - 0.4, 4.4, 2.6, CIRE)                         # le capuchon
    for j in range(4):
        P.point(px_ + 1.0, py_ + 6 + j * 5.0, ENCRE)
    P.ell(px_ - 2.0, 64.6, 1.4, 0.5, BM2) if int(p * 8) % 4 == 0 else None                  # il goutte
    # Deux tables et leurs tabourets, une chandelle sur chacune.
    for (x, y) in ((92.0, 66.0), (118.0, 70.0)):
        P.ell(x, y, 11.0, 2.6, BO3)
        P.ell(x, y + 1.0, 11.0, 2.6, BO1, cond=Y > y + 1.0)
        P.rect(x - 1.0, y + 2.0, 2.0, 8.0, BO1)
        bougie(P, x - 3.0, y - 0.4, h=4.0, lueur=10.0)
        P.rect(x + 2.6, y - 3.2, 3.0, 3.0, GR3)
        P.ell(x + 4.1, y - 3.2, 1.5, 0.5, LU2)
    tab.plan("premier", 1.0)
    # ---- Premier plan : un pilier de bois à gauche, un tonneau à droite, dans l'ombre.
    P.rect(-6.0, -16.0, 8.0, 96.0, ENCRE)
    P.rect(1.0, -16.0, 1.0, 96.0, BO2)
    P.ell(190.0, 70.0, 10.0, 11.0, ENCRE)
    P.ell(189.0, 70.0, 8.0, 9.6, BO1)
    for y in (63.0, 77.0):
        P.rect(181.0, y, 17.0, 1.0, GR2)
    voile(P, Y > 77.6, ENCRE, 0.3)
    poussiere(P, 60, 0, 170, 60, 20, LU4, 535)


# =====================================================================================================================
# Le guet : vu de nuit, à travers un petit carreau (la clé). Au premier plan le rebord et une bougie éteinte ; dehors la
# brume bleu sombre et, très loin, une minuscule lueur à une fenêtre du phare noir.
# =====================================================================================================================
@decor("phare-eteint", "guet-de-nuit", soleil=(112.0, 22.0), tons=PHARE, nom="Le guet")
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


# =====================================================================================================================
# Le Passe-Pied : une chaussée de pierres claires et de goémon à marée basse, entre des flaques et de la vase luisante,
# qui file dans la brume de l'aube vers un rocher surmonté d'un phare (la clé, en haut à droite).
# =====================================================================================================================
@decor("phare-eteint", "passe-pied", soleil=(60.0, 26.0), tons=AUBE, nom="Le Passe-Pied")
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


# =====================================================================================================================
# Au pied de la Dent-Creuse : le bas de la tour de granit, vue de tout près. Une lourde porte cloutée sans poignée (la
# clé), des marches mouillées, des traces de goudron ; la mer remonte autour du rocher. Le sol est à y = 68.
# =====================================================================================================================
@decor("phare-eteint", "pied-du-phare", soleil=(20.0, 6.0), tons=PHARE, nom="Au pied de la Dent-Creuse")
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


# =====================================================================================================================
# La place de Trébrume : une placette pavée par temps gris. Une mairie minuscule à volets bleus et drapeau mouillé (la
# clé), un panneau d'affichage, une fontaine, un banc, des goélands sur le toit.
# =====================================================================================================================
@decor("phare-eteint", "place-mairie", soleil=(40.0, -10.0), tons=AUBE, nom="La place de Trébrume")
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
@decor("phare-eteint", "atelier-basile", soleil=(150.0, -10.0), tons=PHARE, nom="L'atelier de Basile")
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


# =====================================================================================================================
# Le sentier des douaniers : un sentier étroit en haut d'une falaise, dans le brouillard. Ajoncs, bord incertain, une
# cabane de guet en planches grises avec une petite fenêtre tournée vers le phare. Le sol : y = 64, de x = 4 à 130.
# =====================================================================================================================
@decor("phare-eteint", "sentier-douaniers", soleil=(170.0, 0.0), tons=AUBE, nom="Le sentier des douaniers")
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


# =====================================================================================================================
# Le Souffleur : une grotte marine à marée basse. Sable mouillé, goémon, une barque à sec, des bidons alignés, une
# lanterne posée sur un rocher, un conduit sombre qui monte dans la pierre.
# =====================================================================================================================
@decor("phare-eteint", "grotte-souffleur", soleil=(52.0, 30.0), tons=PHARE, nom="Le Souffleur")
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


# =====================================================================================================================
# La cave du phare : le sous-sol rond, à la lueur d'une lanterne. Un tas de charbon, des rangées de bidons d'huile, un
# panier pendu à une poulie (la clé), un escalier de pierre en colimaçon qui monte dans le noir. Le sol : y = 76.
# =====================================================================================================================
@decor("phare-eteint", "cave-du-phare", soleil=(60.0, 40.0), tons=PHARE, nom="La cave du phare")
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


# =====================================================================================================================
# La chambre de veille : une pièce ronde et chaude dans le phare. Poêle, lit étroit, fauteuil, table avec un gros carnet
# relié et une boîte en fer, une corne de brume à soufflet, une bougie, la nuit derrière la meurtrière.
# =====================================================================================================================
@decor("phare-eteint", "chambre-de-veille", soleil=(160.0, 50.0), tons=PHARE, nom="La chambre de veille")
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


# =====================================================================================================================
# La lanterne : le sommet du phare. Une grande lentille de verre à échelons (la clé), une machine d'horlogerie en laiton
# avec cadran et manivelle, un poids au bout de sa chaîne, des vitres tout autour ouvertes sur la brume. Le sol : y = 76.
# =====================================================================================================================
@decor("phare-eteint", "lanterne-du-phare", soleil=(96.0, 20.0), tons=PHARE, nom="La lanterne")
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


# =====================================================================================================================
# La jetée, la nuit : le bout d'une jetée de pierre en pleine nuit de brume. Des silhouettes qui attendent, des petits
# feux de mât flous qui approchent sur l'eau noire, le phare au loin (la clé, en haut à droite) : rallumé.
# Le sol monte un peu : de (4, 61) à (64, 66).
# =====================================================================================================================
@decor("phare-eteint", "jetee-nuit", soleil=(174.0, 6.0), tons=PHARE, nom="La jetée, la nuit")
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
