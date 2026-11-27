"""Décors du « Phare éteint » (mystère) : une côte de granit, la brume, la nuit bleue, les lanternes orange.

Palette : bleus de nuit, gris-bleus de brume, granit ardoise, bois sombre, et une seule famille chaude (lanternes,
bougies, poêle) qui porte la lumière. La brume monte avec la distance (voile), les lueurs orange trouent le bleu.
Le phare de la Dent-Creuse est le même partout : tour effilée, galerie, lanterne vitrée.
"""
import math

import toile
import decors_campagnes as dc
from decors_campagnes import decor
from peinture import (Palette, degrade, relief, voile, eclat, lueur, semis, ell, poly, rect, point, trait, hline, vline, courbe,
                      etoile4, hasard)

N0, N1, N2, N3, N4 = "#0b1630", "#13254a", "#1d3766", "#2e4f86", "#4a6fa8"
BR1, BR2, BR3, BR4 = "#5f7aa6", "#8098bf", "#a9bbd8", "#cfdaea"
MER0, MER1, MER2 = "#08142a", "#0f2443", "#1b3a62"
G1, G2, G3, G4 = "#232a3a", "#3a4357", "#566079", "#7f889c"
L1, L2, L3, L4, L5 = "#8a4a1f", "#d9803a", "#f69d50", "#ffc89a", "#fff1c9"
W1, W2, W3, W4 = "#2e1d12", "#4e321d", "#77502f", "#a87a4c"
W25 = "#5a3a22"
CREME, ENCRE = "#efe4cc", "#0a0f1c"
CIRE, CIRE2 = "#d9a82e", "#f5d76e"
V1, V2 = "#33294f", "#56487e"
GOE1, GOE2 = "#4a3f2a", "#6e6040"
VOLET, VOLET2 = "#3f6fb0", "#6c98d0"
LAITON, LAITON2 = "#b98b2e", "#e8c45e"

PAL = Palette(N0, N1, N2, N3, N4, BR1, BR2, BR3, BR4, MER0, MER1, MER2, G1, G2, G3, G4, L1, L2, L3, L4, L5, W1, W2, W25, W3, W4,
              CREME, ENCRE, CIRE, CIRE2, V1, V2, GOE1, GOE2, VOLET, VOLET2, LAITON, LAITON2).rampes(
    [ENCRE, N0, N1, N2, N3, N4, BR1, BR2, BR3, BR4], [G1, G2, G3, G4, BR3, BR4], [W1, W2, W25, W3, W4, L3, L4, L5],
    [L1, L2, L3, L4, L5], [MER0, MER1, MER2, N3], [V1, V2, BR2], [GOE1, GOE2, W4], [VOLET, VOLET2, BR4],
    [CIRE, CIRE2, L5], [LAITON, LAITON2, L5], [CREME, L5])


def brume(t, y0, y1, force=0.75, couleur=BR3, cadre=None):
    """Banc de brume horizontal : plus épais au milieu de la bande."""
    def k(x, y):
        if y < y0 or y > y1:
            return 0
        u = (y - y0) / (y1 - y0)
        return force * math.sin(u * math.pi) * (0.8 + 0.2 * math.sin(x / 7))
    voile(t, k, couleur, PAL, cadre or (0, y0, 96, y1))


def phare(t, x, base, h=22, w=5, allume=False, c=ENCRE, c2=None):
    """Le phare de la Dent-Creuse, en silhouette (sur son rocher)."""
    c2 = c2 or c
    poly(t, [(x - w / 2, base), (x + w / 2, base), (x + w * 0.32, base - h), (x - w * 0.32, base - h)], c)
    rect(t, x - w * 0.5, base - h - 0.8, w, 0.9, c)                    # galerie
    rect(t, x - w * 0.3, base - h - 3.2, w * 0.6, 2.5, c2 if not allume else L4)
    poly(t, [(x - w * 0.36, base - h - 3.2), (x, base - h - 5), (x + w * 0.36, base - h - 3.2)], c)
    point(t, x, base - h - 5.6, c)
    if allume:
        lueur(t, x, base - h - 2, 9, L4, PAL, force=0.7)
        rect(t, x - w * 0.3, base - h - 3.2, w * 0.6, 2.5, L5)
    # Le rocher.
    ell(t, x, base + 0.8, w * 1.9, 2.2, c, cond=lambda a, b, u, v: v < 0.4)


def mer(t, y0, y1=40, k=0, couleurs=(MER2, MER1, MER0), reflet=BR2, graine=0):
    degrade(t, y0, y1, list(couleurs), trame=0.5)
    for i in range(18):
        x = (hasard(i, 1, graine) * 100 + 1.4 * dc.onde(hasard(i, 4, graine)) * (1 + i % 2)) % 100 - 2
        y = y0 + 1 + hasard(i, 2, graine) * (y1 - y0 - 2)
        l = 2 + hasard(i, 3, graine) * 4 * (y - y0 + 4) / (y1 - y0)
        hline(t, x, x + l, y, reflet)


def ciel_nuit(t, y1, etoiles=12, graine=0):
    degrade(t, 0, y1, [N0, N1, N2, N3])
    for i in range(etoiles):
        x, y = hasard(i, 5, graine) * 96, hasard(i, 6, graine) * y1 * 0.6
        v = dc.onde(hasard(i, 7, graine))
        point(t, x, y, N3 if v < -0.75 else BR4 if i % 3 else L5)


def flamme(t, x, y, k=0, r=1.0, froid=True):
    """Flamme de bougie ou de lanterne, qui vacille d'une image à l'autre. froid : la lueur réchauffe une scène bleue
    (mélange vers l'orange) ; sinon elle éclaire le bois le long de sa rampe."""
    lueur(t, x, y, 8 * r, L4, PAL, force=0.55 if froid else 0.4, teinte=froid)
    v, w = dc.onde(x * 0.137), dc.onde(x * 0.137 + 0.3)
    ell(t, x + 0.25 * v, y - 0.15 * w, 0.9 * r, 1.6 * r * (1 + 0.1 * w), L3)
    ell(t, x + 0.1 * v, y + 0.4, 0.5 * r, 0.9 * r, L5)


def bougie(t, x, y, allumee=True, k=0, froid=False):
    rect(t, x - 1, y, 2, 4, CREME)
    vline(t, x + 0.5, y, y + 4, BR3)
    rect(t, x - 2, y + 4, 4, 1, LAITON)
    if allumee:
        flamme(t, x, y - 1.8, k, froid=froid)
    else:
        trait(t, x, y, x, y - 1, ENCRE, ep=1)
        for i in range(3):
            point(t, x + 0.3 * (i % 2), y - 2 - i * 1.2, BR2)


def planches_mur(t, x0, y0, x1, y1, c, joint, pas=4):
    rect(t, x0, y0, x1 - x0, y1 - y0, c)
    for x in range(int(x0), int(x1), pas):
        vline(t, x, y0, y1, joint)


def pierres(t, x0, y0, x1, y1, c, joint, clair, h=3, l=6):
    rect(t, x0, y0, x1 - x0, y1 - y0, c)
    j = 0
    y = y0
    while y < y1:
        hline(t, x0, x1, y, joint)
        x = x0 - (l / 2 if j % 2 else 0)
        while x < x1:
            vline(t, x, y, min(y + h, y1), joint)
            hline(t, max(x + 0.6, x0), min(x + l - 0.6, x1), y + (0.5 if toile.fin() else 1), clair)
            x += l
        y += h
        j += 1


@decor("phare-eteint", "chez-pilou", images=2, duree=500)
def chez_pilou(t, k):
    # Le mur et la fenêtre de l'aube.
    rect(t, 0, 0, 96, 40, W2)
    planches_mur(t, 0, 0, 96, 26, W2, W1, pas=5)
    rect(t, 56, 3, 30, 19, W1)
    degrade(t, 4, 21, [V2, BR2, L4, L5], x0=57, x1=85)
    relief(t, lambda x: 17 + 1.5 * math.sin(x / 3), BR1, x0=57, x1=85, bas=21)
    ell(t, 74, 18, 2.4, 2.4, L5, cond=lambda x, y, u, v: y < 17.6 + 1.5 * math.sin(x / 3))
    rect(t, 70.5, 3, 1.2, 19, W1)
    rect(t, 56, 12, 30, 1.2, W1)
    rect(t, 55, 21.5, 32, 1.6, W3)
    # Rai de lumière dorée sur le mur et le bureau.
    eclat(t, lambda x, y: 1 if 0 < (x - 30) + (y - 22) * 1.4 < 28 and y > 21 else 0, PAL, n=1, cadre=(0, 20, 96, 40))
    # Le plateau du bureau, en perspective.
    poly(t, [(0, 26), (96, 26), (96, 40), (0, 40)], W3)
    for i in range(5):
        hline(t, 0, 96, 28 + i * 3, W2)
    hline(t, 0, 96, 26, W4)
    eclat(t, lambda x, y: 1 if 0 < (x - 30) + (y - 22) * 1.4 < 28 else 0, PAL, n=1, cadre=(0, 26, 96, 40))
    # Encrier ouvert, plume, enveloppe sans timbre appuyée contre lui.
    ell(t, 40, 30, 5, 1.6, ENCRE)
    rect(t, 35.5, 23, 9, 7, N1)
    ell(t, 40, 23, 4.5, 1.4, N2)
    ell(t, 40, 23, 2.6, 0.8, ENCRE)
    vline(t, 37, 24, 29, N3)
    courbe(t, [(41, 23), (44, 14), (49, 9)], CREME, ep=1)
    poly(t, [(44, 15), (49, 9), (47, 14)], CREME)
    poly(t, [(24, 31), (34, 30), (35.5, 20), (25.5, 21)], CREME)
    trait(t, 25.5, 21, 30.5, 26, BR3, ep=1)
    trait(t, 30.5, 26, 35.5, 20, BR3, ep=1)
    point(t, 30.5, 26.2, L2)
    # Bougie allumée, à gauche, dont la flamme bouge à peine.
    bougie(t, 14, 22, True, k)
    # Une petite tasse et une miette : on a veillé.
    ell(t, 66, 29, 3, 1, ENCRE)
    rect(t, 63.5, 25.5, 5, 3.5, VOLET)
    ell(t, 66, 25.5, 2.5, 0.7, W1)
    ell(t, 69, 27, 1.2, 1.2, VOLET, cond=lambda x, y, u, v: u > 0)
    for (x, y) in ((72, 31), (73.5, 31.5)):
        point(t, x, y, L4)


@decor("phare-eteint", "port-trebrume", images=2, duree=900)
def port(t, k):
    degrade(t, 0, 24, [N1, V2, BR2, L4])
    phare(t, 74, 23, 15, 4, c=G1)
    mer(t, 23, 31, k, graine=2)
    brume(t, 14, 28, 0.8)
    # Le quai de pierre, au premier plan.
    pierres(t, 0, 31, 96, 40, G2, G1, G3, h=3, l=7)
    hline(t, 0, 96, 31, G4)
    # Barques tirées au sec, casiers à homards, filets.
    for (x, c, c2) in ((14, W3, VOLET), (34, VOLET, W3)):
        poly(t, [(x - 7, 27.5), (x + 7, 27.5), (x + 5, 31), (x - 5, 31)], c)
        hline(t, x - 7, x + 7, 27.5, c2)
        rect(t, x - 1, 24, 0.8, 4, W1) if x == 14 else None
    for i, x in enumerate((50, 55.5)):
        rect(t, x, 26 - i, 5, 5 + i, W2)
        for a in range(4):
            vline(t, x + 1 + a * 1.3, 26 - i, 31, W4)
        hline(t, x, x + 5, 28, W4)
    for X in range(int(60 * t.e), int(72 * t.e)):
        for Y in range(int(27 * t.e), int(31 * t.e)):
            if (X + Y) % (2 * t.e) == 0 or (X - Y) % (2 * t.e) == 0:
                t.pf(X, Y, BR3)
    # Bollard, une lanterne de quai allumée, un goéland.
    rect(t, 80, 27, 3, 4, G3)
    ell(t, 81.5, 27, 1.8, 0.8, G4)
    rect(t, 88, 18, 0.8, 13, W1)
    rect(t, 86.8, 15, 3.2, 3.5, ENCRE)
    flamme(t, 88.4, 16.8, k, 0.8)
    ell(t, 6, 28.5, 1.8, 1.1, CREME)
    point(t, 7.6, 27.8, CREME)
    point(t, 8.3, 28, L2)
    hline(t, 4.6, 6.4, 28.3, G4)


@decor("phare-eteint", "auberge-bigorneau", images=2, duree=600)
def auberge(t, k):
    rect(t, 0, 0, 96, 40, W2)
    planches_mur(t, 0, 4, 96, 28, W25, W1, pas=6)
    # Poutres basses.
    rect(t, 0, 0, 96, 4, W1)
    for x in (10, 44, 78):
        rect(t, x, 0, 5, 5, W1)
        hline(t, x, x + 5, 5, W3)
    # Fenêtres jaunes embuées.
    for x in (6, 60):
        rect(t, x, 8, 14, 11, W1)
        rect(t, x + 1, 9, 12, 9, CIRE)
        voile(t, lambda a, b: 0.5, CREME, PAL, (x + 1, 9, x + 13, 18), niveaux=2)
        rect(t, x + 6.5, 9, 1, 9, W1)
        rect(t, x + 1, 13, 12, 1, W1)
        lueur(t, x + 7, 13, 12, L4, PAL, force=0.35)
    # Grande horloge.
    rect(t, 26, 6, 7, 22, W1)
    rect(t, 26.5, 6.5, 6, 21, W3)
    ell(t, 29.5, 11, 2.6, 2.6, CREME)
    trait(t, 29.5, 11, 29.5, 9.2, ENCRE, ep=1)
    trait(t, 29.5, 11, 30.8, 11.8, ENCRE, ep=1)
    rect(t, 28, 16, 3, 10, W2)
    ell(t, 29.5 + (0.8 if k else -0.8), 23, 1.1, 1.1, LAITON2)
    # Ciré jaune pendu à une patère.
    rect(t, 84, 6, 3, 1, W4)
    poly(t, [(85.5, 7), (90, 11), (91, 25), (80, 25), (81, 11)], CIRE)
    poly(t, [(85.5, 7), (88, 10), (87, 25), (84, 25), (83, 10)], CIRE2)
    ell(t, 85.5, 8, 2, 1.5, CIRE)
    # Comptoir au premier plan, marmite de soupe qui fume.
    rect(t, 0, 28, 96, 12, W1)
    rect(t, 0, 28, 96, 2, W4)
    for x in range(4, 96, 12):
        vline(t, x, 30, 40, W2)
    ell(t, 48, 27, 7, 2.2, G1)
    rect(t, 41, 21, 14, 6, G2)
    ell(t, 48, 21, 7, 1.6, G3)
    ell(t, 48, 21, 5.5, 1, L3)
    hline(t, 42, 54, 23, G3)
    for i in range(3):
        x = 45 + i * 3
        courbe(t, [(x, 19), (x + (1.5 if (i + k) % 2 else -1.5), 15), (x, 11 - i)], BR4, ep=1)
    # Des bols, une cuillère, une bougie au comptoir.
    for x in (24, 30):
        ell(t, x, 27, 2.4, 1.3, VOLET, cond=lambda a, b, u, v: v > -0.2)
    bougie(t, 70, 23.5, True, k)
    lueur(t, 48, 21, 16, L4, PAL, force=0.3)


@decor("phare-eteint", "guet-de-nuit", images=2, duree=700)
def guet(t, k):
    # Le mur, sombre, et le petit carreau ouvert sur la nuit.
    rect(t, 0, 0, 96, 40, W1)
    planches_mur(t, 0, 0, 96, 40, W1, ENCRE, pas=7)
    ciel_nuit(t, 30, 10, graine=4)
    sx0, sx1, sy0, sy1 = 24, 72, 4, 29
    mer(t, 22, sy1, k, couleurs=(N1, N0, MER0), reflet=N2, graine=4)
    # remettre le mur hors du carreau
    rect(t, 0, 0, sx0, 40, W1)
    rect(t, sx1, 0, 96 - sx1, 40, W1)
    rect(t, 0, 0, 96, sy0, W1)
    for x in range(0, 96, 7):
        vline(t, x, 0, 40, ENCRE) if (x < sx0 or x > sx1) else vline(t, x, 0, sy0, ENCRE)
    phare(t, 58, 22, 13, 3.4, c=ENCRE)
    # La minuscule lueur à une fenêtre du phare, qui s'allume et s'éteint.
    if k == 0:
        lueur(t, 58, 15, 3, L4, PAL, force=0.8)
        point(t, 58, 15, L5)
    else:
        point(t, 58, 15, L2)
    brume(t, 8, 28, 0.6, couleur=N3, cadre=(sx0, 8, sx1, 28))
    # Montants du carreau.
    rect(t, sx0 - 1.5, sy0 - 1.5, sx1 - sx0 + 3, 1.5, W3)
    rect(t, sx0 - 1.5, sy0, 1.5, sy1 - sy0, W3)
    rect(t, sx1, sy0, 1.5, sy1 - sy0, W3)
    rect(t, (sx0 + sx1) / 2 - 0.6, sy0, 1.2, sy1 - sy0, W2)
    rect(t, sx0, 16, sx1 - sx0, 1.2, W2)
    # Rebord, bougie éteinte qui fume, un buvard.
    rect(t, 0, 29, 96, 11, W2)
    rect(t, 0, 29, 96, 1.5, W4)
    bougie(t, 36, 25.5, False)
    poly(t, [(60, 33), (76, 32), (77, 36), (61, 37)], CREME)
    trait(t, 63, 34, 72, 33.5, BR2, ep=1)
    trait(t, 63, 35.3, 69, 35, BR2, ep=1)


@decor("phare-eteint", "passe-pied", images=2, duree=900)
def passe_pied(t, k):
    degrade(t, 0, 22, [BR2, BR3, L4, BR4])
    phare(t, 74, 18, 13, 3.6, c=G2)
    brume(t, 4, 22, 0.7, couleur=BR4)
    # La vase luisante et les flaques.
    degrade(t, 19, 40, [BR3, G4, G3, G2])
    for i, (x, y, l) in enumerate(((10, 27, 12), (40, 31, 16), (78, 26, 10), (60, 36, 18), (6, 36, 10))):
        ell(t, x, y, l / 2, 1 + l / 14, BR2)
        hline(t, x - l / 4 + 0.8 * dc.onde(i * 0.21), x + 0.6 * dc.onde(i * 0.21 + 0.1), y - 0.3, BR4)
    # La chaussée de pierres claires qui file en zigzag vers le rocher.
    pts = [(40, 40), (46, 34), (54, 29), (62, 24), (70, 20)]
    for i in range(len(pts) - 1):
        (a, b), (c, d) = pts[i], pts[i + 1]
        n = 7
        for j in range(n):
            u = j / n
            x, y = a + (c - a) * u, b + (d - b) * u
            s = 0.4 + 0.6 * (y - 18) / 22
            ell(t, x + (hasard(i, j, 3) - 0.5) * 3, y, 3 * s, 1.4 * s, G4)
            ell(t, x - 0.4 * s + (hasard(i, j, 3) - 0.5) * 3, y - 0.4 * s, 2 * s, 0.7 * s, BR4)
    # Goémon en touffes.
    for i in range(14):
        x, y = hasard(i, 1, 9) * 96, 24 + hasard(i, 2, 9) * 16
        ell(t, x, y, 2 + hasard(i, 3, 9), 0.9, GOE1)
        hline(t, x - 1, x + 1, y - 0.5, GOE2)
    brume(t, 18, 30, 0.45, couleur=BR4)
    # Une étoile de mer : le détail qu'on remarque.
    for a in range(5):
        r = math.radians(a * 72 - 90)
        trait(t, 30, 37, 30 + 1.8 * math.cos(r), 37 + 1.8 * math.sin(r), L3, ep=t.e)
    point(t, 30, 37, L4)


@decor("phare-eteint", "pied-du-phare", images=3, duree=500)
def pied_phare(t, k):
    degrade(t, 0, 40, [BR1, BR2, BR3])
    # La tour de granit, de tout près : blocs, joints, traces de goudron.
    pierres(t, 18, 0, 78, 34, G3, G2, G4, h=4, l=9)
    eclat(t, lambda x, y: 1 if x > 64 else (0.5 if x > 56 else 0), PAL, n=1, sens=-1, cadre=(18, 0, 78, 34))
    eclat(t, lambda x, y: 1 if x < 24 else 0, PAL, n=1, cadre=(18, 0, 78, 34))
    for (x, y) in ((30, 12), (58, 20), (64, 6)):
        ell(t, x, y, 1.4, 2.4, ENCRE)
        trait(t, x, y + 2, x - 0.3, y + 5, ENCRE, ep=1)
    # La lourde porte cloutée, sans poignée.
    ell(t, 48, 14, 9, 7, G1, cond=lambda x, y, u, v: y < 14)
    rect(t, 39, 14, 18, 16, G1)
    ell(t, 48, 14, 7.5, 6, W2, cond=lambda x, y, u, v: y < 14)
    rect(t, 40.5, 14, 15, 16, W2)
    for x in (44, 48, 52):
        vline(t, x, 8.5, 30, W1)
    for y in (13, 20, 27):
        for x in (42, 46, 50, 54):
            point(t, x, y, LAITON2)
    hline(t, 40.5, 55.5, 16.5, W1)
    hline(t, 40.5, 55.5, 23.5, W1)
    # Les marches mouillées.
    for i in range(3):
        y = 30 + i * 2.5
        rect(t, 36 - i * 3, y, 24 + i * 6, 2.5, G2)
        hline(t, 36 - i * 3, 60 + i * 3, y, BR3)
    # La mer qui remonte autour du rocher (trois images).
    def vague(x):
        return 34.5 + 1.2 * math.sin(x / 3 + 2 * math.pi * dc.PHASE) - 0.4 * (1 + dc.onde())
    monte = 0.3 * (1 + dc.onde())
    relief(t, vague, MER1, lisere=BR4, cond=lambda x, y: not (30 < x < 66 and y < 37.5 - monte))
    relief(t, lambda x: vague(x) + 2.5, MER0, cond=lambda x, y: not (27 < x < 69 and y < 37.5 - monte))
    for i in range(6):
        x = (i * 17 + 2.5 * dc.onde(i * 0.17)) % 96
        hline(t, x, x + 3, 37 + (i % 2) * 1.5, BR3)


@decor("phare-eteint", "place-mairie", images=2, duree=800)
def place(t, k):
    degrade(t, 0, 27, [G4, BR2, BR3])
    # Les toits du fond, la mairie minuscule au milieu.
    for i, x in enumerate((0, 14, 70, 82)):
        h = 12 + (i % 2) * 3
        rect(t, x, 24 - h, 14, h, G3 if i % 2 else G4)
        poly(t, [(x - 1, 24 - h), (x + 7, 24 - h - 5), (x + 15, 24 - h)], G2)
        rect(t, x + 4, 24 - h + 3, 3, 3, G1)
    brume(t, 2, 22, 0.35, couleur=BR3)
    rect(t, 32, 8, 32, 18, CREME)
    poly(t, [(30, 8.5), (48, 2), (66, 8.5)], G2)
    for i, x in enumerate((35, 44, 53)):
        rect(t, x, 12, 4, 6, N2)
        rect(t, x - 2, 12, 2, 6, VOLET)
        rect(t, x + 4, 12, 2, 6, VOLET)
        vline(t, x - 1, 12, 18, VOLET2)
    rect(t, 45.5, 19, 5, 7, W2)
    ell(t, 48, 4.5, 1.6, 1.6, CREME)
    point(t, 48, 4.5, ENCRE)
    # Le drapeau mouillé, qui pend.
    vline(t, 63, 0, 9, G1)
    fl = 0.3 * (1 + dc.onde())
    poly(t, [(63.2, 1), (67, 1.5 + fl), (66.5 + fl * 0.3, 5.5), (63.2, 5)], VOLET)
    poly(t, [(65, 1.2), (67, 1.5 + fl), (66.5 + fl * 0.3, 5.5), (65, 5.3)], CREME)
    # Les goélands sur le toit.
    for x in (38, 41, 57):
        ell(t, x, 6.8 - (x - 38) * 0.0, 1.2, 0.8, CREME)
        point(t, x + 1, 6.3, CREME)
        point(t, x + 1.6, 6.4, L3)
    # Les pavés mouillés, la fontaine, le banc, le panneau d'affichage.
    rect(t, 0, 26, 96, 14, G2)
    for j in range(5):
        y = 27 + j * 2.6
        for i in range(0, 100, 4):
            x = i + (2 if j % 2 else 0)
            ell(t, x, y, 1.6, 0.8, G3)
            point(t, x - 0.5, y - 0.3, G4)
    for i in range(5):
        hline(t, 10 + i * 18, 14 + i * 18, 30 + (i % 3) * 3, BR3)
    ell(t, 22, 31, 7, 2.2, G4)
    ell(t, 22, 30.5, 5.6, 1.5, N3)
    rect(t, 21, 22, 2, 8, G4)
    ell(t, 22, 22, 2.4, 1, G3)
    trait(t, 23, 22, 25 + 0.3 * dc.onde(0.25), 25.5 + 0.5 * dc.onde(), BR4, ep=1)
    rect(t, 70, 30, 14, 1.4, W3)
    rect(t, 70, 27.5, 14, 1.4, W3)
    rect(t, 71, 31.4, 1, 3, W1)
    rect(t, 82, 31.4, 1, 3, W1)
    rect(t, 88, 18, 7, 9, W2)
    rect(t, 88.8, 18.8, 5.4, 7.4, CREME)
    for y in (20, 22, 24):
        hline(t, 89.4, 93.5, y, G3)
    rect(t, 90.5, 27, 1, 5, W1)
    point(t, 92.5, 19.6, L2)
    # La bruine : ambiances_decors (pluie qui tombe en boucle).


@decor("phare-eteint", "atelier-basile", images=2, duree=1000)
def atelier(t, k):
    rect(t, 0, 0, 96, 40, W1)
    planches_mur(t, 0, 0, 96, 30, "#3d2818", W1, pas=8)
    # Des dizaines de pendules, aucune à la même heure.
    for i in range(16):
        x = 4 + (i % 8) * 11.5 + (i // 8) * 4
        y = 6 + (i // 8) * 11 + (i % 3)
        r = 2.4 + (i * 7 % 5) * 0.35
        forme = i % 3
        if forme == 0:
            ell(t, x, y, r + 0.8, r + 0.8, LAITON)
        elif forme == 1:
            rect(t, x - r - 0.8, y - r - 0.8, 2 * r + 1.6, 2 * r + 1.6, W3)
        else:
            ell(t, x, y, r + 0.8, r + 0.8, W4)
            rect(t, x - 0.6 + 0.7 * dc.onde(i * 0.17), y + r, 1.2, 3, W4)
        ell(t, x, y, r, r, CREME)
        a = math.radians(i * 47 + (6 if k else 0))
        b = math.radians(i * 113)
        trait(t, x, y, x + r * 0.8 * math.sin(a), y - r * 0.8 * math.cos(a), ENCRE, ep=1)
        trait(t, x, y, x + r * 0.55 * math.sin(b), y - r * 0.55 * math.cos(b), ENCRE, ep=1)
    # Poussière dorée de laiton dans la lumière.
    lueur(t, 30, 30, 26, LAITON2, PAL, force=0.35, ry=14)
    semis(t, lambda x, y: y < 30, [LAITON2, L4], 0.03, graine=k + 40)
    # L'établi : loupe, limes, rouages.
    rect(t, 0, 30, 96, 10, W3)
    hline(t, 0, 96, 30, W4)
    for x in range(6, 96, 14):
        vline(t, x, 31, 40, W2)
    ell(t, 18, 27, 4, 4, LAITON)
    ell(t, 18, 27, 3, 3, BR4)
    ell(t, 17, 26, 1.2, 1, CREME)
    trait(t, 21, 30, 26, 32, W1, ep=t.e)
    for i in range(3):
        trait(t, 30 + i * 3, 33, 34 + i * 3, 30.5, G4, ep=1)
    for (x, y, r) in ((44, 33, 2), (48, 34, 1.4), (41, 35, 1.1)):
        ell(t, x, y, r, r, LAITON)
        ell(t, x, y, r * 0.4, r * 0.4, W3)
    # La forme sous un drap, à droite : on ne sait pas ce que c'est.
    poly(t, [(62, 30), (64, 18), (70, 12), (78, 13), (84, 20), (88, 30)], CREME)
    poly(t, [(70, 12), (78, 13), (84, 20), (88, 30), (80, 30), (76, 18)], BR3)
    trait(t, 67, 30, 70, 17, BR3, ep=1)
    trait(t, 74, 30, 73, 15, BR2, ep=1)


@decor("phare-eteint", "sentier-douaniers", images=2, duree=1100)
def sentier(t, k):
    degrade(t, 0, 40, [BR2, BR3, BR4])
    phare(t, 80, 22, 12, 3, c=BR1)
    mer(t, 22, 40, k, couleurs=(BR2, BR1, N3), reflet=BR3, graine=7)
    brume(t, 10, 30, 0.8, couleur=BR4)
    # La falaise et le sentier étroit, bord incertain.
    f = lambda x: 20 + x * 0.12 + 1.5 * math.sin(x / 4) if x < 60 else 27 + (x - 60) * 0.9
    relief(t, lambda x: f(x) if x < 66 else 40, G3, lisere=G4)
    relief(t, lambda x: f(x) + 3 if x < 64 else 40, G2)
    relief(t, lambda x: 29 + x * 0.05 + 0.6 * math.sin(x), "#b5a27a", x1=58, cond=lambda x, y: y < 32 + x * 0.05)
    # Ajoncs en boules, fleurs jaunes.
    for (x, y, r) in ((6, 30, 4), (14, 33, 3), (40, 34, 4.5), (52, 31, 3)):
        ell(t, x, y, r, r * 0.8, G2)
        semis(t, lambda a, b: (a - x) ** 2 / r ** 2 + (b - y) ** 2 / (0.64 * r * r) < 1, [CIRE2, CIRE], 0.35, graine=int(x),
              cadre=(x - r, y - r, x + r, y + r))
    # La cabane de guet en planches grises, sa petite fenêtre tournée vers le phare.
    rect(t, 22, 14, 14, 11, G4)
    for x in range(22, 36, 3):
        vline(t, x, 14, 25, G3)
    poly(t, [(20.5, 14.5), (29, 9), (37.5, 14.5)], G2)
    rect(t, 31, 17, 3, 3, N2)
    point(t, 32.5, 18.5, L3)
    rect(t, 24, 19, 3, 6, G2)
    brume(t, 16, 40, 0.5, couleur=BR4)


@decor("phare-eteint", "grotte-souffleur", images=2, duree=600)
def grotte(t, k):
    rect(t, 0, 0, 96, 40, G1)
    # Ouverture sur la mer, au fond, encadrée de roche.
    ell(t, 70, 22, 22, 16, BR2, cond=lambda x, y, u, v: y < 30)
    degrade(t, 6, 30, [BR3, BR4, BR3], x0=48, x1=92)
    ell(t, 70, 22, 22, 16, BR3, cond=lambda x, y, u, v: y < 30 and u * u + v * v > 0.85)
    relief(t, lambda x: 24 + 0.5 * math.sin(x / 2 + k), BR1, x0=48, x1=92, bas=30)
    voile(t, lambda x, y: 1 if ((x - 70) / 22) ** 2 + ((y - 22) / 16) ** 2 > 1 else 0, G1, PAL, (40, 0, 96, 32))
    # Le conduit sombre qui monte dans la pierre, à gauche.
    poly(t, [(14, 0), (24, 0), (22, 20), (16, 22)], ENCRE)
    poly(t, [(16, 0), (20, 0), (19.5, 16), (17.5, 17)], N0)
    for (x, y) in ((10, 6), (30, 10), (36, 3), (6, 18), (90, 4)):
        ell(t, x, y, 3, 2, G2)
        hline(t, x - 2, x + 1, y - 1.5, G3)
    # Sable mouillé, goémon.
    degrade(t, 28, 40, [G4, BR2, G3])
    for i in range(10):
        x, y = hasard(i, 1, 12) * 96, 30 + hasard(i, 2, 12) * 10
        ell(t, x, y, 2.2, 0.8, GOE1)
        hline(t, x - 1, x + 1, y - 0.4, GOE2)
    # La barque à sec, les bidons alignés.
    poly(t, [(44, 30), (62, 30), (59, 35), (47, 35)], W2)
    hline(t, 44, 62, 30, W4)
    rect(t, 52, 30, 1, 5, W1)
    for i in range(5):
        x = 66 + i * 4.2
        rect(t, x, 30, 3, 5, G3)
        rect(t, x, 30, 3, 0.8, G4)
        rect(t, x + 1, 29, 1, 1, G4)
    # La lanterne posée sur un rocher : la seule chaleur.
    ell(t, 28, 34, 6, 3, G2, cond=lambda x, y, u, v: v < 0.5)
    rect(t, 26.5, 26.5, 3, 4.5, W1)
    rect(t, 27, 27, 2, 3.5, L4)
    poly(t, [(26, 26.5), (28, 25), (30, 26.5)], W1)
    flamme(t, 28, 28.6, k, 0.7)
    lueur(t, 28, 29, 18, L3, PAL, force=0.45, teinte=True)


@decor("phare-eteint", "cave-du-phare", images=2, duree=500)
def cave(t, k):
    rect(t, 0, 0, 96, 40, G1)
    # Le mur rond, pierres en arc.
    for j in range(8):
        y = j * 4
        for i in range(-1, 16):
            x = i * 7 + (3.5 if j % 2 else 0)
            ell(t, x + 3.5, y + 2, 3.2, 1.7, G2)
            hline(t, x + 1.5, x + 4.5, y + 1, G3)
    # L'escalier en colimaçon qui monte dans le noir.
    for i in range(7):
        y = 30 - i * 4.2
        x = 64 + 10 * math.sin(i * 0.9)
        poly(t, [(x - 6, y), (x + 6, y), (x + 5, y + 2.2), (x - 5, y + 2.2)], G3)
        hline(t, x - 6, x + 6, y, G4)
    voile(t, lambda x, y: max(0, 1 - y / 18), ENCRE, PAL, (50, 0, 82, 30))
    vline(t, 64, 0, 40, G2)
    # Tas de charbon, rangées de bidons d'huile.
    ell(t, 14, 38, 13, 8, ENCRE, cond=lambda x, y, u, v: v < 0)
    semis(t, lambda x, y: ((x - 14) / 13) ** 2 + ((y - 38) / 8) ** 2 < 1, [G2, N1], 0.4, graine=5, cadre=(0, 29, 28, 40))
    for i in range(4):
        x = 32 + i * 5
        rect(t, x, 28, 4, 8, VOLET if i % 2 else N3)
        rect(t, x, 28, 4, 1, VOLET2)
        rect(t, x + 1.4, 27, 1.2, 1, G4)
    # Le panier pendu à une poulie.
    ell(t, 86, 3, 2, 2, G4)
    vline(t, 86, 3, 18, CREME)
    poly(t, [(82, 18), (90, 18), (89, 24), (83, 24)], W3)
    for x in (83.5, 85.5, 87.5):
        vline(t, x, 18, 24, W2)
    # Le sol, la lanterne posée qui éclaire tout.
    rect(t, 0, 36, 96, 4, G2)
    hline(t, 0, 96, 36, G3)
    rect(t, 46.5, 30.5, 3, 5, W1)
    rect(t, 47, 31, 2, 4, L4)
    poly(t, [(46, 30.5), (48, 29), (50, 30.5)], W1)
    flamme(t, 48, 32.5, k, 0.7)
    lueur(t, 48, 32, 34, L3, PAL, force=0.4, ry=20, teinte=True)


@decor("phare-eteint", "chambre-de-veille", images=2, duree=500)
def chambre(t, k):
    rect(t, 0, 0, 96, 40, W2)
    planches_mur(t, 0, 0, 96, 30, W25, W1, pas=6)
    # La meurtrière sur la nuit.
    rect(t, 45, 4, 6, 14, G2)
    degrade(t, 5, 17, [N0, N2], x0=46, x1=50)
    point(t, 47, 8, BR4)
    point(t, 49, 13, L5)
    # Le poêle, sa porte rougeoyante (orange), son tuyau.
    rect(t, 6, 0, 3, 18, ENCRE)
    rect(t, 2, 18, 11, 12, ENCRE)
    rect(t, 3, 17, 9, 1.5, G2)
    rect(t, 4.5, 22, 6, 4, L2)
    for x in (5.5, 7.5, 9.5):
        vline(t, x, 22, 26, L1)
    lueur(t, 7.5, 24, 18, L3, PAL, force=0.4)
    # Le lit étroit, couverture bleue.
    rect(t, 14, 24, 22, 6, W3)
    rect(t, 14, 21, 22, 4, VOLET)
    ell(t, 17, 21, 3, 1.5, CREME)
    rect(t, 14, 18, 1.6, 12, W1)
    # La table : le gros carnet relié, la boîte en fer, la bougie.
    rect(t, 54, 24, 22, 2, W4)
    rect(t, 56, 26, 1.6, 6, W1)
    rect(t, 72, 26, 1.6, 6, W1)
    rect(t, 56, 21, 9, 3, L1)
    rect(t, 56.5, 21.5, 8, 2, CREME)
    vline(t, 60.5, 21, 24, L1)
    rect(t, 66, 20.5, 5, 3.5, G3)
    hline(t, 66, 71, 20.5, G4)
    bougie(t, 74, 20, True, k)
    # La corne de brume à soufflet, le fauteuil.
    poly(t, [(80, 14), (92, 8), (92, 18)], LAITON)
    poly(t, [(80, 14), (92, 8), (92, 11), (80, 14)], LAITON2)
    rect(t, 76, 13, 5, 3, W3)
    for x in range(77, 81):
        vline(t, x, 13, 16, W1)
    rect(t, 36, 22, 8, 8, VOLET)
    rect(t, 36, 18, 8, 5, N3)
    rect(t, 35, 22, 2, 8, N3)
    rect(t, 43, 22, 2, 8, N3)
    # Le plancher.
    rect(t, 0, 30, 96, 10, W1)
    for i in range(4):
        hline(t, 0, 96, 31 + i * 2.5, W2)
    lueur(t, 74, 18, 20, L4, PAL, force=0.3)


@decor("phare-eteint", "lanterne-du-phare", images=2, duree=700)
def lanterne(t, k):
    # Les vitres tout autour, ouvertes sur la brume.
    degrade(t, 0, 40, [BR2, BR3, BR4, BR3])
    brume(t, 0, 40, 0.5, couleur=BR4)
    for x in range(0, 100, 16):
        rect(t, x, 0, 1.8, 30, ENCRE)
    rect(t, 0, 0, 96, 2, ENCRE)
    # La grande lentille à échelons, au centre.
    ell(t, 48, 16, 12, 14, LAITON)
    ell(t, 48, 16, 11, 13, BR4)
    for i in range(6):
        ell(t, 48, 16, 11 - i * 1.6, 13, CREME if i % 2 else BR4, cond=lambda x, y, u, v: abs(u) > 0.82)
        hline(t, 37.5, 58.5, 5 + i * 4, BR3)
    ell(t, 48, 16, 3.5, 4, L5 if k else CREME)
    if k:
        lueur(t, 48, 16, 14, L5, PAL, force=0.5)
    # La machine d'horlogerie : cadran, manivelle, poids au bout de sa chaîne.
    rect(t, 6, 22, 22, 10, LAITON)
    rect(t, 7, 23, 20, 8, W3)
    ell(t, 14, 27, 3, 3, CREME)
    trait(t, 14, 27, 14 + (1.5 if k else 0), 25 if k else 24.5, ENCRE, ep=1)
    for (x, r) in ((21, 2.5), (24.5, 1.6)):
        ell(t, x, 26, r, r, LAITON2)
        ell(t, x, 26, r * 0.4, r * 0.4, W1)
    trait(t, 28, 26, 32, 22, G4, ep=t.e)
    ell(t, 32.5, 21.5, 1.2, 1.2, W4)
    for y in range(32, 38, 1):
        point(t, 76, y, G4)
    vline(t, 76, 2, 32, G4)
    rect(t, 73, 32, 6, 5, G2)
    hline(t, 73, 79, 32, G4)
    # Le plancher de fer, la rambarde.
    rect(t, 0, 30, 96, 10, G2)
    for x in range(0, 96, 4):
        vline(t, x, 30, 34, G1)
    hline(t, 0, 96, 30, G4)
    rect(t, 0, 34, 96, 6, G1)


@decor("phare-eteint", "jetee-nuit", images=2, duree=800)
def jetee(t, k):
    ciel_nuit(t, 22, 16, graine=9)
    phare(t, 84, 21, 12, 3, c=ENCRE, allume=True)
    mer(t, 21, 40, k, couleurs=(N1, N0, MER0), reflet=N3, graine=11)
    # Les petits feux de mât, flous, qui approchent.
    for i, (x, y) in enumerate(((30, 23), (44, 25), (60, 24), (70, 27))):
        x += k * (0.5 + i * 0.2)
        lueur(t, x, y, 3.5, L3, PAL, force=0.7)
        point(t, x, y, L5)
        vline(t, x, y + 1, y + 3, N3)
        for j in range(3):
            hline(t, x - 0.5, x + 0.5, y + 4 + j * 1.5, L2)
    brume(t, 16, 32, 0.55, couleur=N4)
    # La jetée de pierre, en perspective vers la droite.
    poly(t, [(0, 30), (34, 34), (34, 40), (0, 40)], G2)
    poly(t, [(0, 29), (34, 33.5), (34, 34.5), (0, 30.5)], G3)
    for i in range(5):
        vline(t, 6 + i * 6, 31 + i * 0.6, 40, G1)
    # Les silhouettes qui attendent, une lanterne levée.
    for i, (x, h) in enumerate(((8, 9), (13, 7.5), (18, 10), (25, 8))):
        y = 30 + x * 0.12
        ell(t, x, y - h + 1.2, 1.2, 1.3, ENCRE)
        poly(t, [(x - 1.8, y), (x + 1.8, y), (x + 1.1, y - h + 2.3), (x - 1.1, y - h + 2.3)], ENCRE)
    trait(t, 19.5, 22.5, 21.5, 20, ENCRE, ep=1)
    rect(t, 21, 18.5, 1.6, 2, L4)
    lueur(t, 21.8, 19.5, 7, L3, PAL, force=0.6, teinte=True)
