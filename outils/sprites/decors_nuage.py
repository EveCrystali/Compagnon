"""Décors de « Petit Nuage » (émotion) : du jardin aux montagnes, sous des ciels qui changent.

Palette : ciels lavés (bleus pâles), soirs lavande et pêche, aubes roses, neige blanche et bleutée, roches
ardoise, herbes sarcelle, prés jaunes, mélèzes dorés, terre claire, une lampe orange. Pas de vert : les feuillages
sont sarcelle, l'automne est doré. Les montagnes ont un versant éclairé et un versant d'ombre, la neige en crête.
"""
import math

import toile
import decors_campagnes as dc
from decors_campagnes import decor
from peinture import (Palette, degrade, relief, voile, eclat, lueur, semis, ell, poly, rect, point, trait, hline, vline,
                      courbe, nuage, etoile4, hasard)

C1, C2, C3, C4 = "#9cc3e8", "#bcd7ef", "#dbe9f5", "#f2f6fb"
SO1, SO2, SO3, SO4 = "#5c5a9a", "#8a79b8", "#d9a3b5", "#f5c8a0"
AU1, AU2 = "#e8c8d8", "#f8dcc8"
NE1, NE2, NE3, NE4 = "#93aacb", "#c3d3e6", "#e6eef7", "#ffffff"
R1, R2, R3, R4 = "#3c4252", "#5c6478", "#8790a4", "#b5bccb"
H1, H2, H3, H4 = "#123f52", "#1d6578", "#2f8f9c", "#5bb3ae"
P1, P2, P3, P4 = "#8a6e2a", "#c9a64a", "#e8cf7a", "#f6e6a8"
M1, M2 = "#b8742a", "#e0a040"
TE1, TE2, TE3 = "#6b4a2e", "#a07a52", "#d8bd92"
B1, B2, B3 = "#3b2616", "#5e3c22", "#8a5a33"
EA1, EA2, EA3, EA4 = "#1b3550", "#2c5577", "#4f7fa6", "#8fb6d8"
L1, L2, L3 = "#f69d50", "#ffd29a", "#fff1c9"
ENCRE, NU1, NU2 = "#161a26", "#0f1a33", "#1d2c55"
RO1, RO2 = "#8a4a1f", "#b8652e"
MU1, MU2 = ENCRE, SO1                    # mûres : presque noires, un reflet violet (couleurs de la palette)

PAL = Palette(C1, C2, C3, C4, SO1, SO2, SO3, SO4, AU1, AU2, NE1, NE2, NE3, NE4, R1, R2, R3, R4, H1, H2, H3, H4, P1, P2,
              P3, P4, M1, M2, TE1, TE2, TE3, B1, B2, B3, EA1, EA2, EA3, EA4, L1, L2, L3, ENCRE, NU1, NU2, RO1, RO2).rampes(
    [NU1, NU2, SO1, SO2, SO3, SO4, L2, L3], [C1, C2, C3, C4, NE4], [NE1, NE2, NE3, NE4], [R1, R2, R3, R4, NE3],
    [H1, H2, H3, H4, P3], [P1, P2, P3, P4, L3], [M1, M2, P3], [TE1, TE2, TE3, P4], [B1, B2, B3, M1, M2, L2],
    [EA1, EA2, EA3, EA4, C3], [L1, L2, L3], [RO1, RO2, L1], [AU1, AU2, L3], [ENCRE, NU1, NU2])


def montagnes(t, pics, base, roche=R2, ombre=R1, neige=NE4, neige_o=NE2, limite=0.45, lisere=None):
    """Chaîne de pics : (x, sommet, demi-largeur). Versant gauche à l'ombre, droit éclairé, neige au-dessus de
    `limite` (fraction de la hauteur)."""
    for (x, y, l) in pics:
        poly(t, [(x - l, base), (x, y), (x + l, base)], roche)
        poly(t, [(x - l, base), (x, y), (x - l * 0.1, base)], ombre)
        hn = y + (base - y) * limite
        def dent(u):
            return hn + 1.2 * math.sin(u * 2.3)
        poly(t, [(x - l * (hn - y) / (base - y), hn), (x, y), (x + l * (hn - y) / (base - y), hn),
                 (x + l * 0.2 * (hn - y) / (base - y), hn + 1.5), (x - l * 0.3 * (hn - y) / (base - y), hn + 0.8)], neige)
        poly(t, [(x - l * (hn - y) / (base - y), hn), (x, y), (x - l * 0.05, hn + 1)], neige_o)
        if lisere:
            trait(t, x, y, x + l * 0.5, y + (base - y) * 0.5, lisere, ep=1)


def herbe(t, f, c, lisere=H4, x0=0, x1=None, graine=1, haute=2.0, brins=(H4, P3)):
    relief(t, f, c, lisere=lisere, x0=x0, x1=x1)
    e = t.e
    x1 = t.w if x1 is None else x1
    for X in range(int(x0 * e), int(x1 * e)):
        x = (X + 0.5) / e
        if hasard(X, 0, graine) < 0.2:
            y = f(x)
            trait(t, x, y - 1 - hasard(X, 1, graine) * haute, x, y, brins[int(hasard(X, 2, graine) * len(brins))], ep=1)


def meleze(t, x, base, h, k=0, dore=True):
    """Mélèze doré : tronc fin, étages de branches en triangle, aiguilles qui tombent."""
    vline(t, x, base - h, base, B1)
    for i in range(5):
        y = base - h + i * h / 5.5
        l = 1 + i * h / 14
        poly(t, [(x - l, y + h / 6), (x, y), (x + l, y + h / 6)], M1 if dore else H2)
        poly(t, [(x, y), (x + l, y + h / 6), (x + l * 0.2, y + h / 6)], M2 if dore else H3)
    for j in range(3):
        point(t, x + 2 + j * 1.5, base - h / 2 + j * 2 + 0.6 * (1 + dc.onde(j * 0.31 + x * 0.07)), M2)


def nuage_vivant(t, x, y, l, h, c=NE4, cl=NE4, o=NE2, yeux=False):
    nuage(t, x, y, l, h, c, cl, o)
    if yeux:
        point(t, x - 1, y - h * 0.2, R1)
        point(t, x + 1.2, y - h * 0.2, R1)



def ronce(t, x0, y0, x1, y1, haut, graine, baies=3):
    """Une tige de ronce en arc (de (x0, y0) à (x1, y1), bombée de `haut`) : prune sombre, épines d'un pixel fin
    tous les deux pixels, deux ou trois feuilles dentelées et quelques mûres."""
    mx, my = (x0 + x1) / 2, min(y0, y1) - haut
    courbe(t, [(x0, y0), (mx, my), (x1, y1)], B1, ep=2)
    n = 18
    for i in range(1, n):
        u = i / n
        x = (1 - u) ** 2 * x0 + 2 * (1 - u) * u * mx + u * u * x1
        y = (1 - u) ** 2 * y0 + 2 * (1 - u) * u * my + u * u * y1
        if i % 2 == 0:
            point(t, x + 0.5, y - 0.5 if i % 4 else y + 1.5, B1)           # l'épine, dessus puis dessous
        if i in (5, 11):
            ell(t, x, y + 1, 1.4, 0.8, H3)                                  # une feuille
            point(t, x - 0.5, y + 0.8, H4)
        if baies and i in (3, 9, 15)[:baies] and hasard(i, graine, 7) > 0.3:
            ell(t, x, y + 1.3, 0.8, 0.8, MU1)                               # une mûre
            point(t, x - 0.3, y + 1, MU2)


@decor("petit-nuage", "jardin-lave", images=2, duree=1400)
def jardin_lave(t, k):
    degrade(t, 0, 24, [C2, C3, C4])
    nuage(t, 20, 6, 22, 3, NE4, NE4, NE3)
    nuage(t, 74, 9, 16, 2.4, NE4, NE4, NE3)
    # Au fond, le massif de ronces mouillées, sarcelle et violet.
    for i in range(16):
        x = i * 6.4 + hasard(i, 1, 2) * 3
        ell(t, x, 22, 5 + hasard(i, 2, 2) * 2, 5 + hasard(i, 3, 2) * 2, H1 if i % 2 else SO1)
    for i in range(30):
        x, y = hasard(i, 4, 2) * 96, 17 + hasard(i, 5, 2) * 6
        point(t, x, y, NE3 if i % 2 else H4)
    # Les tiges arquées qui sortent du massif : on reconnaît des ronces à leurs épines et à leurs mûres.
    for i in range(8):
        x = 2 + i * 12 + hasard(i, 8, 2) * 3
        ronce(t, x, 21, x + 9 + hasard(i, 9, 2) * 3, 22, 6 + hasard(i, 10, 2) * 3, i, baies=3)
    # L'herbe couchée et luisante, les flaques qui reflètent le ciel.
    relief(t, lambda x: 24 + 0.6 * math.sin(x / 5), H2, lisere=H4)
    for i in range(40):
        x, y = hasard(i, 6, 2) * 96, 26 + hasard(i, 7, 2) * 14
        trait(t, x, y, x + 2.5, y - 0.6, H3, ep=1)
    for (x, y, l) in ((18, 33, 14), (58, 29, 10), (80, 36, 16)):
        ell(t, x, y, l / 2, 1.4, C2)
        hline(t, x - l / 3, x + l / 6, y - 0.4, C4)
        point(t, x + l / 4 - k, y + 0.2, NE4)
    # Le pot de fleurs retourné, l'arrosoir renversé.
    # Le pot de fleurs renversé : la cabane de Pilou (docs/LORE.md). Terre cuite, le bord épais posé dans l'herbe,
    # le trou d'écoulement en haut, une petite porte en arche ; la lumière vient de gauche.
    poly(t, [(33.5, 27.5), (40.5, 27.5), (42.5, 35), (31.5, 35)], RO2)
    poly(t, [(38.5, 27.5), (40.5, 27.5), (42.5, 35), (40, 35)], RO1)
    trait(t, 34.6, 28.4, 33.2, 34, M2, ep=1)
    rect(t, 30.5, 35, 13, 2, RO2)
    rect(t, 40.5, 35, 3, 2, RO1)
    hline(t, 30.5, 43.5, 35, RO1)
    hline(t, 31, 40, 35.5, M2)
    ell(t, 37, 27.6, 1.2, 0.5, B1)
    ell(t, 36.4, 37, 1.6, 2.8, B1, cond=lambda x, y, u, v: y <= 37)
    point(t, 37.2, 35.8, M1)
    ell(t, 66, 33, 6, 3.4, R3)
    ell(t, 66, 32.2, 5, 2.4, R4)
    poly(t, [(71, 32), (79, 30), (79.5, 31.4), (71, 34)], R3)
    ell(t, 80, 30.8, 1.4, 1.6, R4)
    courbe(t, [(62, 30.2), (64, 26.5), (69, 29.8)], R2, ep=t.e)
    # Au premier plan à droite, le roncier où Brouillon s'est pris (lui est dessiné en pied par la scène, à la
    # même échelle partout : pas de petit nuage peint ici).
    for (a, b, h, g) in ((84, 40, 12, 1), (88, 40, 15, 2), (92, 40, 10, 3), (80, 40, 8, 4)):
        ronce(t, a, b, a + 8 + g % 3, b, h, g + 20)


@decor("petit-nuage", "chemin-creux", images=1)
def chemin_creux(t, k):
    degrade(t, 0, 24, [C1, C2, C3])
    ell(t, 70, 5, 3, 3, NE4)
    montagnes(t, [(40, 17, 9), (52, 15, 8), (62, 18, 7)], 24, roche=NE1, ombre=R4, neige=NE4, neige_o=NE3, limite=0.6)
    # Le chemin de terre claire qui file vers les montagnes, ornières sèches.
    relief(t, lambda x: 23.5, H3, lisere=H4)
    poly(t, [(46, 24), (54, 24), (96, 40), (4, 40)], TE3)
    for (a, b) in ((49, 30), (51, 66)):
        trait(t, a, 24, b, 40, TE2, ep=t.e)
    semis(t, lambda x, y: abs(x - 50) < (y - 24) * 2.8, [TE2, P4], 0.12, graine=8, cadre=(0, 24, 96, 40))
    # Deux haies basses de noisetiers, à hauteur d'herbe.
    for side in (-1, 1):
        for i in range(9):
            u = i / 8
            x = 48 + side * (4 + u * 44)
            y = 23 + u * 11
            r = 2 + u * 6
            ell(t, x, y, r, r * 0.8, H2)
            ell(t, x - r * 0.25, y - r * 0.3, r * 0.6, r * 0.45, M1 if i % 3 == 0 else H3)
            if i % 2:
                point(t, x + r * 0.3, y - r * 0.1, M2)
    herbe(t, lambda x: 38 + 0.8 * math.sin(x / 2), H2, x1=24, graine=4, brins=(P3, H4))
    herbe(t, lambda x: 38 + 0.8 * math.sin(x / 2), H2, x0=74, graine=5, brins=(P3, H4))
    # Une noisette tombée au milieu du chemin.
    ell(t, 44, 36, 1.4, 1.2, B3)
    rect(t, 43.2, 34.6, 1.6, 0.8, P2)


@decor("petit-nuage", "pre-aux-draps", images=2, duree=500)
def pre_draps(t, k):
    degrade(t, 0, 40, [C1, C2, C3])
    nuage(t, 80, 6, 20, 2.6, NE4, NE4, NE3)
    f = lambda x: 22 + x * 0.12
    relief(t, f, H3, lisere=H4)
    relief(t, lambda x: f(x) + 8, H2)
    # Les cordes à linge et onze grands draps blancs qui claquent au vent (deux images).
    for ligne, (x0, x1, y0, n, s) in enumerate(((6, 50, 9, 5, 0.8), (40, 96, 13, 6, 1))):
        courbe(t, [(x0, y0), ((x0 + x1) / 2, y0 + 1.5), (x1, y0)], R2, ep=1)
        for i in range(n):
            x = x0 + 2 + i * (x1 - x0 - 4) / n
            w = (x1 - x0 - 4) / n - 1.5
            y = y0 + 0.6 * math.sin(i)
            onde = s * (0.25 + 1.25 * dc.onde(i * 0.23 + ligne * 0.5))
            poly(t, [(x, y), (x + w, y), (x + w + onde, y + 9 * s), (x + onde * 0.5, y + 10 * s)], NE4)
            poly(t, [(x + w * 0.6, y), (x + w, y), (x + w + onde, y + 9 * s), (x + w * 0.6 + onde, y + 9.5 * s)], NE3)
            trait(t, x + w * 0.3, y + 0.5, x + w * 0.3 + onde * 0.6, y + 9 * s, NE2, ep=1)
            rect(t, x + 0.5, y - 0.5, 0.5, 1, TE2)
            rect(t, x + w - 1, y - 0.5, 0.5, 1, TE2)
    # Ombres mouvantes sur l'herbe.
    for i in range(6):
        x = 8 + i * 15 + 1.2 * dc.onde(i * 0.23)
        ell(t, x, f(x) + 6, 4, 0.8, H2)
    # Les poteaux, le panier d'osier.
    for x in (5, 49, 95):
        vline(t, x, 8, f(x) + 3, B2)
    poly(t, [(14, 33), (24, 33), (23, 38), (15, 38)], M1)
    for x in range(15, 24, 2):
        vline(t, x, 33, 38, B3)
    hline(t, 14, 24, 33, M2)
    ell(t, 19, 32.5, 4.5, 1.6, NE4)
    courbe(t, [(15, 33), (19, 28), (23, 33)], B3, ep=1)
    semis(t, lambda x, y: y > f(x) + 2, [P3, NE4], 0.04, graine=7)


@decor("petit-nuage", "etang-qui-fume", images=2, duree=1200)
def etang(t, k):
    degrade(t, 0, 24, [R3, NE1, NE2])
    # Rive d'en face, le saule, les toiles d'araignée chargées de rosée.
    relief(t, lambda x: 20 + 1.2 * math.sin(x / 6), H1, lisere=R3)
    tx = 74
    trait(t, tx, 21, tx + 1, 6, B1, ep=t.e + 1)
    ell(t, tx, 8, 11, 5, H2, cond=lambda x, y, u, v: v < 0.4)
    for i in range(14):
        x = tx - 10 + i * 1.5
        trait(t, x, 8, x + 0.3, 17 + hasard(i, 1, 4) * 4, H2 if i % 2 else H3, ep=1)
    for (cx, cy, r) in ((20, 15, 4), (34, 17, 3)):
        for a in range(0, 360, 45):
            ra = math.radians(a)
            trait(t, cx, cy, cx + r * math.cos(ra), cy + r * math.sin(ra), NE3, ep=1)
        for rr in (r * 0.4, r * 0.75):
            for a in range(0, 360, 30):
                ra = math.radians(a)
                point(t, cx + rr * math.cos(ra), cy + rr * math.sin(ra), NE4 if a % 60 else NE2)
    # L'étang rond, ses nénuphars.
    ell(t, 48, 30, 46, 9, EA2)
    ell(t, 48, 29, 42, 5.5, EA3, cond=lambda x, y, u, v: v < -0.2)
    for (x, y) in ((30, 30), (40, 33), (62, 31), (70, 34)):
        ell(t, x, y, 3, 1.2, H3, cond=lambda a, b, u, v: not (u > 0 and abs(v) < 0.3))
        point(t, x - 1, y - 0.4, H4)
    # La brume épaisse posée sur l'eau, qui glisse.
    voile(t, lambda x, y: math.sin((y - 19) / 11 * math.pi) * (0.75 + 0.35 * math.sin(x / 9 + 0.5 * dc.onde())) if 19 < y < 30 else 0,
          NE3, PAL, (0, 18, 96, 30), famille=[NE1, NE2, NE3])
    # Roseaux au premier plan.
    for i in range(30):
        x = (i * 3.3 + hasard(i, 1, 5) * 2) % 96
        if 20 < x < 78:
            continue
        h = 8 + hasard(i, 2, 5) * 10
        trait(t, x, 40, x + (hasard(i, 3, 5) - 0.5) * 3, 40 - h, H1, ep=1)
        if i % 4 == 0:
            ell(t, x, 40 - h + 2, 0.7, 1.6, B2)


@decor("petit-nuage", "plateau-rape", images=2, duree=300)
def plateau(t, k):
    degrade(t, 0, 26, [C1, C2, C4])
    # Au loin, de hauts nuages d'orage noirs en forme d'enclume.
    for (x, l) in ((20, 20), (70, 28)):
        # Tour de nuage bouillonnante, sommet étalé en enclume, base sombre.
        ell(t, x + l * 0.1, 7, l * 0.62, 2.2, R2)
        ell(t, x + l * 0.15, 6.4, l * 0.5, 1.4, R3)
        for j in range(5):
            y = 22 - j * 3.2
            r = l * (0.22 + 0.04 * math.sin(j * 1.7))
            ell(t, x - r * 0.4, y, r, 2.6, R1)
            ell(t, x + r * 0.5, y - 0.6, r * 0.9, 2.4, R1)
            ell(t, x + r * 0.7, y - 1.2, r * 0.5, 1.4, R2)
        nuage(t, x, 23, l * 0.7, 2.4, R1, R2, NU2)
    # Le plateau immense, plat et jaune, herbe rase et cailloux.
    rect(t, 0, 25, 96, 15, P3)
    hline(t, 0, 96, 25, P4)
    for j, y in enumerate((27, 30, 34)):
        rect(t, 0, y, 96, 40 - y, (P3, P2, P2)[j])
    semis(t, lambda x, y: y > 26, [P1, R3, P4], 0.12, graine=3, cadre=(0, 26, 96, 40))
    # L'air qui tremble au ras du sol (deux images).
    for i in range(10):
        x = i * 10 + k * 3
        hline(t, x, x + 4, 24.5 + (i % 2) * 0.5, C4)
    # Un seul arbre mort au milieu, pas une ombre.
    x = 50
    trait(t, x, 29, x, 17, B2, ep=t.e)
    trait(t, x, 22, x - 4, 17, B2, ep=1)
    trait(t, x, 20, x + 3, 15, B2, ep=1)
    trait(t, x - 2.5, 19, x - 4.5, 18, B2, ep=1)
    trait(t, x + 2, 16.5, x + 4.5, 16, B2, ep=1)
    # Un caillou, au premier plan, avec un tout petit lézard couleur de sable.
    ell(t, 76, 37, 4, 2, R3)
    ell(t, 75, 36.4, 2.6, 1.1, R4)
    rect(t, 74, 35, 3.6, 0.8, P1)
    point(t, 77.8, 35.2, P1)


@decor("petit-nuage", "halte-girouette", images=2, duree=900)
def halte(t, k):
    degrade(t, 0, 32, [NU1, NU2, SO1, SO2, SO3])
    for i in range(10):
        point(t, hasard(i, 1, 9) * 96, hasard(i, 2, 9) * 10, NE3)
    montagnes(t, [(14, 6, 12), (34, 9, 11), (70, 5, 14), (88, 10, 10)], 28, roche=SO1, ombre=NU2, neige=NE3, neige_o=NE1,
              limite=0.5)
    relief(t, lambda x: 30 + math.sin(x / 7), H1, lisere=SO2)
    # La petite halte de pierre, toit d'ardoise, cheminée qui fume.
    rect(t, 34, 22, 26, 13, R3)
    for j in range(4):
        hline(t, 34, 60, 22 + j * 3.3, R2)
        for x in range(34 + (j % 2) * 3, 60, 6):
            vline(t, x, 22 + j * 3.3, 25.3 + j * 3.3, R2)
    poly(t, [(32, 22.5), (47, 15), (62, 22.5)], R1)
    for i in range(5):
        hline(t, 34 + i * 1.5, 60 - i * 1.5, 21.5 - i * 1.4, R2)
    rect(t, 53, 14, 3, 5, R2)
    for i in range(3):
        ell(t, 54.5 + i * 1.5 + k * 0.5, 12 - i * 2.4, 1.2 + i * 0.4, 1 + i * 0.3, R4 if i else NE2)
    rect(t, 38, 26, 4, 4, L2)
    rect(t, 50, 26, 4, 4, L2)
    vline(t, 40, 26, 30, B2)
    vline(t, 52, 26, 30, B2)
    lueur(t, 46, 28, 14, L2, PAL, force=0.35, teinte=True)
    rect(t, 44, 28, 4, 7, B2)
    # Sur le faîte, la girouette en fer rouillé (un coq) avec une lanterne accrochée au bec.
    vline(t, 47, 9, 15, ENCRE)
    hline(t, 45, 49, 12, ENCRE)
    gx = 47
    poly(t, [(gx - 3, 9), (gx - 1, 7), (gx + 1.5, 7), (gx + 2.5, 5.5), (gx + 3.5, 6.5), (gx + 2.5, 8.5), (gx + 1, 9)], RO1)
    poly(t, [(gx - 3, 9), (gx - 4.5, 6), (gx - 3, 7)], RO2)
    point(t, gx + 4, 6.5, RO2)
    vline(t, gx + 4.3, 6.8, 8, ENCRE)
    rect(t, gx + 3.6, 8, 1.4, 1.6, L1)
    lueur(t, gx + 4.3, 8.8, 6, L2, PAL, force=0.5, teinte=True)
    # Premier plan : un muret et un banc de pierre.
    rect(t, 0, 35, 96, 5, R1)
    for x in range(0, 96, 5):
        ell(t, x + 2.5, 35.5, 2.4, 1.2, R2)


@decor("petit-nuage", "sentier-des-melezes", images=2, duree=1100)
def sentier_meleze(t, k):
    degrade(t, 0, 40, [C1, C2, C3])
    # Deux sommets blancs en forme de dents, un col arrondi entre eux.
    montagnes(t, [(56, 3, 9), (78, 4, 9)], 22, roche=R3, ombre=R2, neige=NE4, neige_o=NE2, limite=0.55)
    # Le col arrondi entre les deux dents : une selle de neige.
    relief(t, lambda x: 16 - 5 * ((x - 67) / 8) ** 2, NE3, lisere=NE4, x0=60, x1=74, bas=22)
    relief(t, lambda x: 19 - 2 * ((x - 67) / 8) ** 2, NE2, x0=60, x1=74, bas=22)
    # La pente raide, rochers gris, premières plaques de neige.
    f = lambda x: 18 + (96 - x) * 0.18
    relief(t, f, H2, lisere=H4)
    for (x, y, l) in ((70, 24, 8), (28, 30, 6), (86, 22, 5)):
        ell(t, x, y, l, 1.2, NE4)
        hline(t, x - l * 0.6, x, y - 0.5, NE3)
    for (x, y, r) in ((12, 30, 3), (40, 34, 4), (82, 30, 2.5), (58, 27, 2)):
        ell(t, x, y, r, r * 0.7, R2)
        ell(t, x - r * 0.25, y - r * 0.25, r * 0.6, r * 0.4, R4)
    # Le sentier en lacets.
    pts = [(10, 40), (60, 36), (30, 31), (70, 27), (50, 23.5)]
    for i in range(len(pts) - 1):
        (a, b), (c, d) = pts[i], pts[i + 1]
        for j in range(31):
            u = j / 30
            rect(t, a + (c - a) * u - 1, b + (d - b) * u, 2.5, 0.6 + (b - 22) / 12, TE3)
    # Les mélèzes dorés qui perdent leurs aiguilles.
    for (x, base, h) in ((6, 36, 20), (22, 33, 14), (88, 31, 12), (44, 30, 10), (94, 39, 16)):
        meleze(t, x, base, h, k)
    semis(t, lambda x, y: y > f(x), [M2, M1], 0.05, graine=11 + k)


@decor("petit-nuage", "terrier-aux-bocaux", images=2, duree=700)
def terrier(t, k):
    rect(t, 0, 0, 96, 40, TE1)
    ell(t, 48, 40, 60, 42, B2)
    # Étagères de bois du sol au plafond, couvertes de bocaux étiquetés.
    for j in range(4):
        y = 9 + j * 8
        rect(t, 4, y, 88, 1.4, B3)
        hline(t, 4, 92, y, M2)
        for i in range(14):
            x = 6 + i * 6.2 + (j % 2) * 1.5
            if 36 < x < 58 and j >= 2:
                continue
            h = 4 + hasard(i, j, 1) * 2.4
            c = (L1, SO3, NE3, M2, EA4, L2, SO2)[int(hasard(i, j, 2) * 7)]
            rect(t, x, y - h, 4, h, c)
            rect(t, x + 0.4, y - h - 0.9, 3.2, 1, TE2)
            rect(t, x + 0.6, y - h * 0.55, 2.8, 1.4, NE4)
            vline(t, x + 0.6, y - h + 0.6, y - h * 0.6, NE4)
            if c in (L2, L1) and (i + k) % 2:
                point(t, x + 2, y - 1.5, L3)
    for x in (4, 48, 91):
        rect(t, x, 0, 1.8, 40, B2)
    # La lampe à huile, le fauteuil de foin.
    rect(t, 46, 22, 4, 3, B1)
    ell(t, 48, 20, 2.2, 2.6, L2)
    ell(t, 48, 20.6 - k * 0.3, 1, 1.4, L3)
    lueur(t, 48, 20.5, 12, L2, PAL, force=0.3, ry=9)
    ell(t, 48, 36, 12, 6, P2)
    ell(t, 48, 32, 9, 6, P3, cond=lambda x, y, u, v: v < 0.3)
    semis(t, lambda x, y: ((x - 48) / 12) ** 2 + ((y - 34) / 6) ** 2 < 1, [P1, P4], 0.25, graine=4,
          cadre=(36, 26, 60, 40))


@decor("petit-nuage", "col-blanc", images=2, duree=1300)
def col_blanc(t, k):
    degrade(t, 0, 40, [NE3, NE4, NE3])
    # Brouillard blanc, horizon effacé : le col se devine à peine.
    relief(t, lambda x: 18 + 3 * math.cos(x / 12), NE3, lisere=NE4)
    relief(t, lambda x: 26 + 1.2 * math.sin(x / 8), NE4, lisere=NE2)
    # La faille bleutée, le pont de neige au-dessus.
    poly(t, [(36, 30), (64, 29), (66, 33), (34, 34)], NE1)
    poly(t, [(38, 31), (62, 30.4), (63, 32.4), (37, 32.8)], EA3)
    courbe(t, [(34, 30.5), (50, 26), (66, 30)], NE4, ep=t.e * 2)
    hline(t, 40, 60, 29.6, NE2)
    # La file de cairns à demi enfouis, qui s'efface.
    for i, (x, y, s) in enumerate(((10, 36, 1.4), (24, 31, 1.1), (76, 26, 0.9), (86, 22, 0.7))):
        for j in range(3):
            ell(t, x, y - j * 1.6 * s, (2.4 - j * 0.6) * s, 0.9 * s, R3 if i < 2 else R4)
        ell(t, x, y + 0.6, 3 * s, 1 * s, NE4)
    voile(t, lambda x, y: math.sin(y / 28 * math.pi) * (0.7 + 0.3 * math.sin(x / 14 + 0.6 * dc.onde())) if y < 28 else 0, NE4, PAL,
          (0, 0, 96, 30), famille=[NE3, NE4])
    eclat(t, lambda x, y: 1 if y > 26 and x < 30 + (y - 26) * 2 else 0, PAL, n=1, sens=-1, cadre=(0, 26, 96, 40),
          sur=(NE4,))
    # Des traces de pas, toutes petites, qui s'arrêtent au bord.
    for i in range(5):
        point(t, 14 + i * 4, 37 - i * 1.3, NE1)


@decor("petit-nuage", "trou-qui-siffle", images=3, duree=180)
def trou(t, k):
    rect(t, 0, 0, 96, 40, NU1)
    # Galerie sombre, parois lisses polies par le vent, en perspective vers la lueur.
    ell(t, 70, 20, 30, 16, NU2)
    ell(t, 70, 20, 16, 9, SO1)
    ell(t, 70, 20, 7, 4.5, SO2)
    ell(t, 70, 20, 2.6, 2, NE3)
    for i in range(6):
        y = 4 + i * 6.5
        courbe(t, [(0, y), (40, y + (20 - y) * 0.4), (70, 20 + (y - 20) * 0.2)], R1, ep=1)
    # Alcôves de part et d'autre.
    for (x, y, w, h) in ((8, 8, 8, 6), (24, 12, 6, 5), (12, 24, 7, 6), (88, 6, 5, 6)):
        ell(t, x, y, w / 2, h / 2, ENCRE)
        hline(t, x - w / 2.5, x + w / 4, y - h / 2 + 0.5, R2)
    # La poussière qui file à l'horizontale (trois images).
    for i in range(36):
        y = hasard(i, 1, 3) * 38 + 1
        x = (hasard(i, 2, 3) * 110 - 10 + k * 7) % 100 - 2
        l = 1 + hasard(i, 3, 3) * 4
        hline(t, x, x + l, y, R3 if i % 3 else R4)
    rect(t, 0, 35, 96, 5, R1)
    hline(t, 0, 96, 35, R2)


@decor("petit-nuage", "grande-salle", images=2, duree=400)
def grande_salle(t, k):
    degrade(t, 0, 40, [ENCRE, NU1, NU2])
    # Le puits de lumière vertical, tout au fond.
    voile(t, lambda x, y: 1 - abs(x - 64) / (4 + y * 0.12), SO2, PAL, (50, 0, 80, 34), niveaux=3,
          famille=[NU2, SO1, SO2])
    voile(t, lambda x, y: 1 - abs(x - 64) / (1.5 + y * 0.05), SO3, PAL, (55, 0, 75, 34), niveaux=2, famille=[SO2, SO3])
    ell(t, 64, 34, 9, 1.5, SO2)
    ell(t, 64, 34, 5, 0.8, SO3)
    # Les parois de la caverne, stalactites.
    relief(t, lambda x: 0, R1, bas=4)
    for i in range(14):
        x = i * 7 + hasard(i, 1, 2) * 4
        poly(t, [(x - 2, 0), (x + 2, 0), (x, 4 + hasard(i, 2, 2) * 6)], R1)
    poly(t, [(-1, 0), (10, 0), (6, 20), (12, 40), (-1, 40)], R1)
    poly(t, [(97, 0), (88, 0), (92, 18), (86, 40), (97, 40)], R1)
    # Le fleuve de vent, visible à la poussière qu'il charrie.
    for i in range(80):
        u = hasard(i, 1, 5)
        x = (u * 120 + k * 5) % 100 - 2
        y = 18 + 6 * math.sin(x / 15) + (hasard(i, 2, 5) - 0.5) * 8
        hline(t, x, x + 1 + hasard(i, 3, 5) * 2, y, R3 if i % 2 else R2)
    # Les grappes de chauves-souris au plafond.
    for (x, n) in ((14, 5), (34, 4), (84, 6)):
        for j in range(n):
            px = x + (j % 3) * 2 - 2
            py = 1 + (j // 3) * 2
            ell(t, px, py + 0.8, 0.8, 1.1, ENCRE)
            point(t, px - 0.3, py + 0.6, SO3)
    rect(t, 0, 0, 96, 1, ENCRE)
    # La corniche étroite le long de la paroi, au premier plan.
    poly(t, [(0, 32), (40, 30), (96, 33), (96, 40), (0, 40)], R1)
    poly(t, [(0, 32), (40, 30), (96, 33), (96, 34), (40, 31.4), (0, 33.4)], R2)
    hline(t, 0, 96, 40, R1)


@decor("petit-nuage", "abreuvoir", images=2, duree=1500)
def abreuvoir(t, k, aube=False):
    if aube:
        degrade(t, 0, 22, [C1, C2, AU1, AU2])
    else:
        degrade(t, 0, 22, [SO2, SO3, SO4, L2])
    # Le lac d'altitude cerné de sommets.
    montagnes(t, [(8, 4, 14), (30, 8, 12), (56, 2, 15), (82, 6, 13), (98, 9, 9)], 22, roche=SO1 if not aube else R3,
              ombre=NU2 if not aube else R2, neige=NE4 if aube else SO4, neige_o=NE2 if aube else SO3, limite=0.5)
    # Le lac et ses reflets immenses (les montagnes à l'envers, plus sombres).
    degrade(t, 22, 34, [SO2, SO1, NU2] if not aube else [AU1, C1, EA3])
    for (x, y, l) in ((8, 4, 14), (30, 8, 12), (56, 2, 15), (82, 6, 13)):
        poly(t, [(x - l * 0.6, 22), (x, 22 + (22 - y) * 0.3), (x + l * 0.6, 22)], SO1 if not aube else C1)
    for i in range(12):
        hline(t, hasard(i, 1, 4) * 90, hasard(i, 1, 4) * 90 + 4, 23 + hasard(i, 2, 4) * 10, SO3 if not aube else C3)
    # Les nuages descendus boire, le ventre posé sur l'eau (ou qui s'élèvent en file vers le sud, à l'aube).
    if not aube:
        for i, (x, y, l) in enumerate(((14, 24, 10), (30, 25, 8), (46, 23.5, 12), (64, 25, 9), (80, 24, 11),
                                         (90, 26, 6), (22, 28, 7), (56, 29, 8))):
            nuage(t, x, y + 0.3 * dc.onde(i * 0.29), l, 2.2, L3, NE4, SO3)
    else:
        for i in range(7):
            x, y = 18 + i * 11 + 0.4 * dc.onde(i * 0.21), 22 - i * 2.6 - 0.4 * (1 + dc.onde(i * 0.17))
            nuage(t, x, y, 8 - i * 0.6, 2 - i * 0.12, NE4, NE4, AU1)
        voile(t, lambda x, y: 0.5 if (y < 30 and math.sin(x / 3 + 0.8 * dc.onde()) > 0.3) else 0, NE3, PAL, (0, 23, 96, 31),
              famille=[NE2, NE3, C3])
    # La rive de galets, le rocher plat.
    rect(t, 0, 34, 96, 6, R2 if not aube else NE3)
    for i in range(40):
        x, y = hasard(i, 5, 7) * 96, 34.5 + hasard(i, 6, 7) * 5.5
        ell(t, x, y, 1.2, 0.6, (R3, R4, R1)[i % 3] if not aube else (NE4, NE2, R4)[i % 3])
    poly(t, [(60, 33), (80, 32), (84, 35), (58, 36)], R3)
    hline(t, 61, 80, 32.6, R4 if not aube else NE4)
    if aube:
        semis(t, lambda x, y: True, [NE4], 0.3, graine=2, cadre=(0, 34, 96, 40))
    else:
        eclat(t, lambda x, y: 1 if x > 50 else 0, PAL, n=1, cadre=(0, 34, 96, 40))


@decor("petit-nuage", "abreuvoir-aube", images=2, duree=1500)
def abreuvoir_aube(t, k):
    abreuvoir(t, k, aube=True)


@decor("petit-nuage", "fenetre-maison", images=2, duree=1300)
def fenetre(t, k):
    rect(t, 0, 0, 96, 40, B2)
    # La vitre : le ciel d'hiver dehors, traversé de nuages.
    rect(t, 14, 2, 68, 28, B1)
    degrade(t, 3, 29, [SO1, SO2, SO3, SO4], x0=15, x1=81)
    for i, (x, y, l) in enumerate(((26, 10, 16), (58, 7, 20), (72, 16, 12), (40, 20, 14))):
        nuage(t, x + 0.7 * (1 + i % 2) * dc.onde(i * 0.19), y, l, 2.2, SO4, L2, SO2)
    relief(t, lambda x: 26 + 1.5 * math.sin(x / 6), NE2, lisere=NE4, x0=15, x1=81, bas=29)
    # La buée, et ce qu'on y a dessiné du doigt : un petit nuage qui sourit.
    voile(t, lambda x, y: (y - 8) / 16 + 0.15 * math.sin(x / 4) if x < 47 else (y - 16) / 20, NE2, PAL, (15, 3, 81, 29),
          famille=[SO2, SO3, NE1, NE2, NE3])
    for a in range(0, 181, 15):
        r = math.radians(a)
        point(t, 26 + 5 * math.cos(r), 24 - 2.5 * math.sin(r), SO2)
    hline(t, 21, 31, 24.6, SO2)
    point(t, 24.5, 22.6, SO2)
    point(t, 27.5, 22.6, SO2)
    rect(t, 47.5, 2, 1.4, 28, B1)
    rect(t, 14, 15, 68, 1.2, B1)
    # Le rebord intérieur, la lumière de lampe, la petite casserole et le baluchon posé.
    rect(t, 0, 30, 96, 10, B3)
    hline(t, 0, 96, 30, M2)
    rect(t, 0, 32, 96, 1, B2)
    lueur(t, 10, 26, 30, L2, PAL, force=0.4, ry=18)
    ell(t, 34, 30, 5, 1.2, R3)
    rect(t, 29, 26, 10, 4, R3)
    ell(t, 34, 26, 5, 1, R4)
    rect(t, 39, 27, 6, 1, B1)
    ell(t, 66, 26.5, 6, 4.5, RO2)
    ell(t, 65, 25.5, 4, 3, L1)
    poly(t, [(65, 22), (63, 19), (66, 21), (69, 19), (67, 22.5)], RO2)
    for (x, y) in ((63, 26), (67, 28), (68, 24.5)):
        point(t, x, y, L3)
