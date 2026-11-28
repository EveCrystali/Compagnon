"""« La Grande Panne » en haute définition : les douze personnages qui accompagnent Grumeau (personnages_hd.py).

Tous sont des objets de l'intérieur de l'ordinateur : papier, touches, laiton, bois, paille. Même lumière que
Grumeau (en haut à gauche), même cerne teinté. La toise de la campagne (hauteur en unités, Pilou : corps de 62) :
Mme Échéance 111, Mlle Renvoi 107, Balayeur 103, golem 95, Dateur 90, Grumeau 87, Imprimante 80, Tic-Tac 77,
Quatre-Cent-Quatre 64 (à 6 du sol), Brouillon 61, les Raccourcis 59 avec la rame, Le Rond 56 (à 8 du sol), S 37.
"""
import math

from pinceau_hd import Rampe, seuil
from personnages_hd import (perso, Etat, oeil, sourcil, bouche, goutte, _main, ENCRE, BLANC, BOUCHE, JOUE, BOIS, VERNIS,
                            CRIN, PEAU, CREME)

GRIS = Rampe("#3a3f4b", "#5a6070", "#8890a0", "#b8bfcc", "#e2e6ee")
PAPIER = Rampe("#b9ad92", "#d9cfb8", "#f6f1e4", "#fffdf6", cerne="#5a5244")
BEIGE = Rampe("#6e6250", "#8a7d68", "#b8a98c", "#ddd0b2", "#efe6cf")
LIGNE = "#a9b4c8"                                       # l'écriture pâle des papiers
VIO = Rampe("#2e2450", "#4a3a7e", "#6a5acd", "#9b8cff", "#c9c0ff")
BLEU = Rampe("#1f4f8a", "#2f6fc0", "#4a8fdc", "#8fc0f0", "#d6ecff")
ORANGE = Rampe("#8a4410", "#c46a24", "#ff9a3c", "#ffc27a", "#ffe6c0")
LAITON = Rampe("#8a6a1c", "#b8922a", "#e8c447", "#fff0a0")
PRUNE = Rampe("#2e1c2a", "#4a2e40", "#6a4a5c", "#8a6a7c")
LAVANDE = Rampe("#8a7fc0", "#b8b0dc", "#d8d2f0", "#efecfb", cerne="#4a4380")
LUNE = Rampe("#9aa8c4", "#c4d0e2", "#e6ecf6", "#f8fafd")
CLAIRE = Rampe("#7c8698", "#a9b3c4", "#d3dae6", "#eef2f8", "#ffffff")
PAILLE = Rampe("#8a6a2a", "#b89450", "#d8b870", "#f0d898", "#fff0c0")
FEUTRE = Rampe("#1c2128", "#2c323c", "#4a5060", "#727a8c", cerne="#0e1016")
NUIT = "#2e2450"

GLYPHES = {
    "0": ["111", "101", "101", "101", "111"], "1": ["010", "110", "010", "010", "111"],
    "3": ["111", "001", "011", "001", "111"], "4": ["101", "101", "111", "001", "001"],
    "7": ["111", "001", "010", "010", "010"],
    "C": ["111", "100", "100", "100", "111"], "A": ["010", "101", "111", "101", "101"],
    "S": ["011", "100", "010", "001", "110"],
    "t": ["010", "111", "010", "010", "011"], "r": ["000", "101", "110", "100", "100"], "l": ["10", "10", "10", "10", "11"],
    "u": ["000", "101", "101", "101", "011"], "p": ["000", "110", "101", "110", "100"],
}
GRAND_S = ["01110", "10001", "10000", "01110", "00001", "10001", "01110"]


def graver(f, x, y, mot, c, dans=None):
    """Un mot en glyphes de 3 × 5, gravé pixel par pixel."""
    for ch in mot:
        g = GLYPHES[ch]
        for j, rang in enumerate(g):
            for i, v in enumerate(rang):
                if v == "1" and (dans is None or (int(x) + i + f.ox, int(y) + j + f.oy) in dans):
                    f.px(x + i, y + j, c)
        x += len(g[0]) + 1


def plaque(f, x, y, w, h, r, v0=0.72, v1=0.5, coins=1, **kw):
    """La face avant d'un bloc : un dégradé doux de haut en bas, les coins rognés."""
    def dedans(px, py):
        if not (x <= px < x + w and y <= py < y + h):
            return False
        dx, dy = min(px - x, x + w - px), min(py - y, y + h - py)
        return dx + dy >= coins
    return f.forme(dedans, (x, y, x + w, y + h - 0.01), r, lambda px, py: v0 + (v1 - v0) * (py - y) / h
                   - 0.12 * max(0.0, (px - x) / w - 0.62), **kw)


def pave(f, x, y, w, h, r, d=3, c=3, **kw):
    """Un bloc vu un peu de dessus : le dessus prend la lumière, le flanc droit est dans l'ombre."""
    n = len(r)
    f.poly([(x, y), (x + w, y), (x + w + c, y - d), (x + c, y - d)], r, ton=n - 1)
    f.poly([(x + w, y), (x + w + c, y - d), (x + w + c, y + h - d), (x + w, y + h)], r, ton=0)
    s = plaque(f, x, y, w, h, r, **kw)
    f.trait(x + 1, y, x + w - 2, y, r[n - 1], dans=s)
    return s


def cadre(f, x0, y0, x1, y1, c):
    f.trait(x0, y0, x1, y0, c); f.trait(x0, y1, x1, y1, c)
    f.trait(x0, y0, x0, y1, c); f.trait(x1, y0, x1, y1, c)


# ---------------------------------------------------------------------------------------------------------------------
@perso("grande-panne", "le-rond", "Le Rond", ("surpris",),
       "curseur d'attente : anneau de huit points bleus dont deux éteints, un visage au milieu", w=64, h=62, vol=8)
def le_rond(f, e):
    h = e.humeur
    f.oy = -1 if e.souffle else 0
    cx, cy = 32.0, 31.0
    rayon = 23.0 if h == "surpris" else 21.5
    for i in range(8):
        ang = math.radians(-90 + i * 45)
        x, y = cx + rayon * math.cos(ang), cy + rayon * math.sin(ang)
        allume, bute = i < 6, i == 5                    # il cale aux trois quarts : le sixième point clignote
        r = 5.3 + (0.7 if bute and e.t % 2 else 0)
        if bute and e.t % 2:
            f.disque(x, y, r + 2.6, r + 2.6, BLEU[3], densite=0.34, cerne="")
        f.boule(x, y, r, r, BLEU if allume else CRIN, biais=0.42 if allume else 0.3)
        if allume:
            f.px(x - r * 0.42, y - r * 0.48, "#ffffff")
    f.boule(cx, cy, 13.2, 13.2, LUNE, biais=0.46)
    yo = cy - 1.6
    for cote, x in ((-1, cx - 5), (1, cx + 5)):
        oeil(f, x, yo, e, cote, rx=2.4, ry=3.0, iris="#2a3a5e", cil="#2a3a5e", ri=0.86)
        if h == "surpris":
            sourcil(f, x, yo - 4.8, e, cote, l=4.0, c="#5a6a8c")
    bouche(f, cx, yo + 6.6, e, l=5.0, ligne="#2a3a5e")
    f.oy = 0


# ---------------------------------------------------------------------------------------------------------------------
BAS = Rampe("#b8805a", "#d9a37a", "#ecc09a", cerne="#5a3324")


@perso("grande-panne", "mlle-renvoi", "Mlle Renvoi", ("joie", "colere"),
       "agente d'accueil très droite : chignon prune, lunettes rectangulaires, tailleur violet, astérisque doré",
       w=62, h=114)
def mlle_renvoi(f, e):
    a, g = 27, 112
    up = -1 if e.souffle else 0
    h = e.humeur
    for x in (a + 4.4, a - 4.4):
        f.tube([(x, g - 27, 2.7), (x, g - 5, 2.0)], BAS)
        s = f.boule(x - 1.4, g - 2.3, 4.4, 2.3, PRUNE, biais=0.45)
        f.px(x - 3.5, g - 3.6, PRUNE[3])
    jupe = f.poly([(a - 9.5, g - 48), (a + 9.5, g - 48), (a + 8.6, g - 25), (a - 8.6, g - 25)], VIO, rond=0.9, gain=0.5,
                  biais=0.24, trame=0.06)
    f.ourler(jupe, VIO[0], cotes=((0, 1),))
    f.trait(a + 4, g - 33, a + 4, g - 26, VIO[0], dans=jupe)
    veste = f.poly([(a - 10.5, g - 73 + up), (a + 10.5, g - 73 + up), (a + 9.2, g - 58), (a + 10.8, g - 45),
                    (a - 10.8, g - 45), (a - 9.2, g - 58)], VIO, rond=0.9, gain=0.56, biais=0.36, trame=0.12)
    f.ourler(veste, VIO[0], cotes=((0, 1),))
    f.oy = up
    f.poly([(a - 4.5, g - 73), (a + 4.5, g - 73), (a, g - 63)], BLANC)                 # le chemisier
    f.trait(a - 4.5, g - 73, a - 0.5, g - 62, VIO[0]); f.trait(a + 4.5, g - 73, a + 0.5, g - 62, VIO[0])
    f.trait(a - 5.5, g - 72, a - 1.5, g - 61, VIO[3], dans=veste)                     # le revers qui luit
    f.trait(a, g - 62, a, g - 46, VIO[0], dans=veste)
    for y in (g - 58, g - 53):
        f.px(a - 1.5, y, LAITON[3]); f.px(a - 1.5, y + 1, LAITON[1])
    f.trait(a - 8, g - 52, a - 4, g - 52, VIO[1], dans=veste)
    # L'astérisque doré à la boutonnière : il renvoie toujours à une autre ligne.
    ax, ay = a + 6, g - 67
    for (dx, dy) in ((0, -2), (0, -1), (0, 0), (0, 1), (0, 2), (-2, -1), (-1, 0), (1, 0), (2, 1), (-2, 1), (2, -1)):
        f.px(ax + dx, ay + dy, LAITON[2] if (dx, dy) != (0, 0) else LAITON[3], VIO.cerne)
    f.tube([(a, g - 77, 2.6), (a, g - 72.5, 2.6)], PEAU, biais=0.2)
    # Les bras : les mains jointes sur un formulaire ; en colère, elle montre le guichet d'à côté.
    eg, ed = (a - 10.3, g - 70.5), (a + 10.3, g - 70.5)
    bras_g = [eg + (3.0,), (a - 12.2, g - 60, 2.7), (a - 4.5, g - 52.5, 2.4)]
    bras_d = [ed + (3.0,), (a + 12.2, g - 60, 2.7), (a + 4.5, g - 52.5, 2.4)]
    main_g, main_d = (a - 3.4, g - 50.6), (a + 3.4, g - 50.6)
    if h == "colere":
        bras_d = [ed + (3.0,), (a + 17.5, g - 67.5, 2.6), (a + 24, g - 71.5, 2.3)]
        main_d = (a + 26.6, g - 73)
        bras_g = [eg + (3.0,), (a - 12.6, g - 60, 2.7), (a - 8, g - 52.5, 2.4)]
        main_g = (a - 6.6, g - 50.6)
    px0 = main_g[0] - 2.5
    f.poly([(px0, g - 54), (px0 + 11, g - 55), (px0 + 11.5, g - 46), (px0 + 0.5, g - 45)], PAPIER, rond=0.3)   # le formulaire
    for k in range(3):
        f.trait(px0 + 2, g - 52 + k * 2, px0 + 8 - k * 2, g - 52.3 + k * 2, LIGNE)
    for bras, main, cote, biais in ((bras_d, main_d, 1, 0.24), (bras_g, main_g, -1, 0.38)):
        s = f.tube(bras, VIO, biais=biais, gain=0.56, trame=0.12)
        f.ourler(s, VIO[0], cotes=((-cote, 0), (0, 1), (0, -1)), dehors=False)
        _main(f, main[0], main[1], cote, r=2.3, pouce=False)
    if h == "colere":
        f.px(main_d[0] + 2.8, main_d[1] - 0.6, PEAU[2], PEAU.cerne); f.px(main_d[0] + 3.8, main_d[1] - 0.8, PEAU[3], PEAU.cerne)
    # La tête : cheveux tirés, chignon haut piqué d'une épingle.
    tx, ty = a - 0.4, g - 87.0
    f.boule(tx + 0.6, ty - 13.4, 4.8, 4.3, PRUNE, biais=0.4)
    f.trait(tx - 4.5, ty - 12.4, tx + 5.5, ty - 15, LAITON[2]); f.px(tx - 5.5, ty - 12.2, LAITON[3])
    f.boule(tx, ty - 1.4, 9.7, 10.0, PRUNE, biais=0.28)
    for cote in (-1, 1):
        f.boule(tx + cote * 8.9, ty + 1.6, 1.8, 2.4, PEAU, biais=0.3)
    tete = f.boule(tx, ty, 8.9, 9.7, PEAU, gain=0.42, biais=0.58,
                   cond=lambda x, y, u, v: abs(u) <= 1 - 0.24 * max(0.0, v) ** 2)
    chev = f.boule(tx, ty - 1.6, 9.5, 9.6, PRUNE, biais=0.44,
                   cond=lambda x, y, u, v: y < ty - 5.6 + 2.6 * ((x - tx) / 9.0) ** 2)
    f.ourler(chev, PRUNE[0], cotes=((0, 1),), dehors=False)
    f.courbe([(tx - 6, ty - 7.5), (tx - 2, ty - 9.4), (tx + 3, ty - 9.6)], PRUNE[3], dans=chev)
    yo = ty + 1.2
    for cote, x in ((-1, tx - 4.2), (1, tx + 3.6)):
        oeil(f, x, yo, e, cote, rx=1.9, ry=2.3, iris="#4a3a5e", cil="#2e1c2a", regard=(-0.3, 0))
        sourcil(f, x, yo - 5.0, e, cote, l=3.8, c="#3a2232")
        cadre(f, x - 3, yo - 3, x + 3, yo + 3, GRIS[0])                              # les lunettes rectangulaires
        f.px(x - 2, yo - 2, "#ffffff")
    f.trait(tx - 1.2, yo - 1, tx + 0.6, yo - 1, GRIS[0])
    f.px(tx - 0.8, yo + 3.6, PEAU[0])
    if h == "joie":
        for x in (tx - 5.6, tx + 5.0):
            f.disque(x, yo + 4.6, 1.8, 1.1, JOUE, dans=tete)
    bouche(f, tx - 0.3, yo + 6.0, e, l=4.4, ligne="#6a2a4a")
    f.oy = 0


# ---------------------------------------------------------------------------------------------------------------------
@perso("grande-panne", "golem", "Le golem de tickets", ("colere",),
       "gardien de file fait de tickets empilés, une fente pour œil orange", w=88, h=108)
def golem(f, e):
    a, g = 43, 106
    up = -1 if e.souffle else 0
    h = e.humeur
    blocs = ((0, 29, g - 24, 24, 0), (-3, 30, g - 47, 23, 0), (2, 27, g - 69 + up, 22, up), (-1, 22, g - 90 + up, 21, up))
    # Les bras : trois tickets en accordéon de chaque côté, levés quand il se fâche.
    for cote in (-1, 1):
        ex = a + 2 + cote * 28 + (4 if cote > 0 else 0)
        for k in range(3):
            if h == "colere":
                x, y = ex + cote * (5 + (3 if k == 1 else 0)), g - 68 - k * 7 + up
            else:
                x, y = ex + cote * (5 + (2 if k == 1 else 0)), g - 62 + k * 6 + up
            s = plaque(f, x - 4.5, y, 9, 6, PAPIER if k % 2 else BEIGE, v0=0.8, v1=0.6)
            f.trait(x - 2.5, y + 2, x + 1.5, y + 2, LIGNE, dans=s)
            f.ourler(s, PAPIER[0], cotes=((0, 1),))
            if k == 2:
                f.px(x + 2.5, y + 3, ORANGE[2]); f.px(x + 2.5, y + 4, ORANGE[1])
    tete = None
    for j, (dx, l, y, ht, dy) in enumerate(blocs):
        r = PAPIER if j % 2 else BEIGE
        x0 = a + dx - l
        s = pave(f, x0, y, 2 * l, ht, r, d=3, c=4, v0=0.86, v1=0.6)
        f.ourler(s, r[0], cotes=((0, 1),))
        for yy in range(int(y) + 7, int(y + ht) - 2, 7):                  # les tickets, un par un
            f.trait(x0, yy, x0 + 2 * l - 1, yy, r[1], dans=s)
        for yy in range(int(y) + 2, int(y + ht) - 1, 2):                  # le pointillé à détacher
            f.px(x0 + 5, yy, r[0])
        if j < 3:
            for k in range(3):
                f.trait(x0 + 9, y + 3 + k * 2, x0 + 20 - k * 3 + (j * 5) % 7, y + 3 + k * 2, LIGNE, dans=s)
            c = ORANGE if j == 1 else BLEU
            b = f.rect(x0 + 2 * l - 12, y + 3, 8, 6, c, ton=2, dans=s)
            f.px(x0 + 2 * l - 10, y + 5, "#ffffff"); f.px(x0 + 2 * l - 8, y + 5, "#ffffff"); f.px(x0 + 2 * l - 7, y + 6, "#ffffff")
            f.ourler(b, c[0], cotes=((0, 1), (1, 0)), dehors=False)
        else:
            tete = (x0, y, l, s)
    # La tête : une fente, un œil orange qui balaie la file.
    x0, y, l, s = tete
    fx, fy = a - 1 - 15, y + 5
    f.rect(fx, fy, 30, 7, GRIS, ton=0, dans=s)
    f.trait(fx, fy + 7, fx + 29, fy + 7, PAPIER[3], dans=s)
    ox = a - 1 + (0 if h == "colere" else (-5, 0, 5, 0)[e.t % 4])
    if e.paup == 2:
        f.trait(ox - 5, fy + 3, ox + 5, fy + 3, ORANGE[2])
    else:
        o = f.boule(ox, fy + 3.5, 4.4 if h == "colere" else 3.6, 2.9 if e.paup == 0 else 1.5, ORANGE, biais=0.5)
        f.px(ox - 1.5, fy + 2.5, "#fff6d8") if o else None
        f.rect(ox - 0.5, fy + 2, 1, 3, GRIS, ton=0, dans=o) if e.paup == 0 else None
    if h == "colere":
        f.poly([(fx, fy), (fx + 13, fy), (fx, fy + 4)], GRIS, ton=1)
        f.poly([(fx + 30, fy), (fx + 17, fy), (fx + 30, fy + 4)], GRIS, ton=1)
        for k in (0, 1):
            f.trait(fx - 1, fy - 4 + k, fx + 11, fy - 1 + k, GRIS[0], dans=s)
            f.trait(fx + 30, fy - 4 + k, fx + 18, fy - 1 + k, GRIS[0], dans=s)
    by = y + 15.5
    if e.bouche:
        f.rect(a - 6, by, 10, 1 + e.bouche, GRIS, ton=0, dans=s)
    elif h == "colere":
        f.courbe([(a - 7, by + 2), (a - 3, by), (a + 1, by), (a + 5, by + 2)], GRIS[0], dans=s)
    else:
        f.trait(a - 6, by + 1, a + 3, by + 1, GRIS[1], dans=s)


# ---------------------------------------------------------------------------------------------------------------------
@perso("grande-panne", "spectre-404", "Quatre-Cent-Quatre", ("triste",),
       "fantôme d'une page effacée : feuille pâle lavande au coin corné, au bas ondulé", w=56, h=80, vol=6)
def spectre(f, e):
    h = e.humeur
    f.oy = -1 if e.souffle else 0
    x0, x1, y0 = 11, 45, 6
    corps = f.poly([(x0, y0), (x1 - 8, y0), (x1, y0 + 8), (x1, 64), (x0, 64)], LAVANDE, rond=0.55, gain=0.5, biais=0.5, trame=0.08)
    for i in range(4):                                                    # le bas ondule
        ry = 5.0 + 1.6 * math.sin(i * 1.7 + e.t * math.pi / 2)
        corps |= f.boule(x0 + 4.25 + 8.5 * i, 63.5, 4.25, ry, LAVANDE, biais=0.5 - 0.06 * i, gain=0.4)
    pli = f.poly([(x1 - 8, y0), (x1, y0 + 8), (x1 - 8, y0 + 8)], LAVANDE, ton=1)   # le coin corné
    f.trait(x1 - 8, y0 + 1, x1 - 8, y0 + 8, LAVANDE[0]); f.trait(x1 - 8, y0 + 8, x1 - 1, y0 + 8, LAVANDE[0])
    f.trait(x1 - 7, y0 + 1, x1 - 1, y0 + 7, LAVANDE[3])
    for k in range(3):                                                    # ce qu'il reste du texte
        f.trait(x0 + 5, 43 + k * 4, x1 - 8 - k * 6, 43 + k * 4, LAVANDE[1], dans=corps)
    graver(f, 22, 55, "404", LAVANDE[1], dans=corps)
    f.trait(x0 + 1, y0 + 3, x0 + 1, 40, LAVANDE[3], dans=corps)
    # Il s'efface par le bas : une trame de plus en plus claire, sans cerne.
    bas = {(X, Y) for (X, Y) in corps if Y - f.oy >= 58}
    f.gommer(bas, garde=lambda X, Y: 1 - (Y - f.oy - 57) / 13.0 > seuil(X, Y - f.oy))
    yo = 26.0
    for cote, x in ((-1, 22), (1, 34)):
        oeil(f, x, yo, e, cote, rx=3.0, ry=3.8, iris=NUIT, pupille="#1a1438", blanc="#ffffff", cil=NUIT, ri=0.92, arc=NUIT)
        if h == "triste":
            sourcil(f, x, yo - 6.4, e, cote, l=5.0, c="#6a60a8")
    if h == "neutre" and not e.bouche:
        f.disque(28, yo + 9.4, 1.6, 2.0, NUIT)                           # un petit « o » : il est toujours un peu perdu
    else:
        bouche(f, 28, yo + 9.2, e, l=6.0, ligne=NUIT, fond=NUIT)
    if h == "triste":
        goutte(f, 19.5, yo + 7.5 + e.t % 2, 1.4)
    f.oy = 0


# ---------------------------------------------------------------------------------------------------------------------
ENCREUR = Rampe("#1e1838", "#2e2450", "#4a3a7e", "#6a5acd")
GOMME = Rampe("#1a1726", "#2a2230", "#4a4258")


@perso("grande-panne", "dateur", "Le Dateur", ("joie", "triste"),
       "tampon dateur à poignée de bois, molette bloquée sur 13 h 37, socle encreur à sec", w=68, h=96)
def dateur(f, e):
    a, g = 32, 94
    up = -1 if e.souffle else 0
    # Le socle encreur, à sec : des craquelures claires.
    socle = pave(f, a - 26, g - 11, 52, 11, ENCREUR, d=3, c=3, v0=0.62, v1=0.3)
    f.ourler(socle, ENCREUR[0], cotes=((0, 1),))
    f.trait(a - 22, g - 13, a + 24, g - 13, ENCREUR[1])
    for (x, l) in ((a - 14, 4), (a + 2, 6), (a + 15, 3)):
        f.trait(x, g - 13, x + l, g - 12.2, ENCREUR[3])
    f.trait(a - 20, g - 6, a - 8, g - 6, ENCREUR[3], dans=socle); f.px(a - 22, g - 8, ENCREUR[3])
    f.oy = up
    # Le caoutchouc, le corps de métal, le col et la poignée.
    f.rect(a - 19, g - 19, 40, 6, GOMME, rond=0.5)
    corps = pave(f, a - 21, g - 56, 42, 37, GRIS, d=3, c=3, v0=0.78, v1=0.5)
    f.ourler(corps, GRIS[0], cotes=((0, 1),))
    f.trait(a - 20, g - 55, a - 20, g - 24, GRIS[4], dans=corps)
    for (x, y) in ((a - 18, g - 53), (a + 17, g - 53), (a - 18, g - 23), (a + 17, g - 23)):
        f.px(x, y, GRIS[4]); f.px(x + 1, y + 1, GRIS[0])                   # les rivets
    f.tour(a + 1, g - 71, g - 58.5, lambda y: 3.2 + (2.6 if y > g - 62.5 else 0) + (1.2 if y < g - 68 else 0), BOIS)
    pom = f.boule(a + 1, g - 79, 9.6, 8.8, BOIS, biais=0.4)
    f.courbe([(a - 5, g - 80), (a - 3.5, g - 84), (a + 0.5, g - 85.5)], VERNIS, dans=pom)
    f.courbe([(a - 2, g - 73), (a + 4, g - 72.4), (a + 8, g - 75)], BOIS[1], dans=pom)
    # La molette : quatre chiffres bloqués, 13 37.
    f.rect(a - 17, g - 34, 34, 11, GRIS, ton=0, dans=corps)
    for i, (x, ch) in enumerate(((a - 16, "1"), (a - 9, "3"), (a + 3, "3"), (a + 10, "7"))):
        c = f.rect(x, g - 33, 6, 9, PAPIER, ton=2)
        f.trait(x, g - 25, x + 5, g - 25, PAPIER[0])
        graver(f, x + 1.5, g - 31, ch, ENCRE)
    f.px(a - 1, g - 31, PAPIER[2]); f.px(a - 1, g - 27, PAPIER[2])
    for y in range(g - 33, g - 24, 2):                                     # la roue crantée, sur le flanc
        f.px(a + 22, y, GRIS[2]); f.px(a + 23, y, GRIS[1])
    yo = g - 46.0
    for cote, x in ((-1, a - 7), (1, a + 6)):
        oeil(f, x, yo, e, cote, rx=2.5, ry=3.0, iris="#2a2f3a", cil=GRIS[0], ri=0.8)
        sourcil(f, x, yo - 5.2, e, cote, l=4.6, c=GRIS[0])
    if e.humeur == "joie":
        for x in (a - 12.5, a + 11.5):
            f.disque(x, yo + 4.2, 2.0, 1.1, JOUE, dans=corps)
    bouche(f, a - 0.5, yo + 7.4, e, l=6.0, ligne=GRIS[0])
    if e.humeur == "triste":
        goutte(f, a - 9.5, yo + 6.4, 1.2)
    f.oy = 0


# ---------------------------------------------------------------------------------------------------------------------
GANT = Rampe("#c9b890", "#f6f1e4", "#fffdf6", cerne="#5a5244")
CRAYON = Rampe("#a8742a", "#e8b45a", "#f8d898")


def _feuillet(f, x, y, c):
    s = f.rect(x, y, 6, 6, c, ton=2)
    f.trait(x, y, x + 5, y, c[3]); f.trait(x + 1, y + 3, x + 4, y + 3, c[0])
    f.px(x + 5, y + 5, c[0])
    return s


@perso("grande-panne", "mme-echeance", "Mme Échéance", ("malice",),
       "la Planificatrice : une dame-calendrier, anneaux sur le front, un grand crayon pour canne", w=64, h=112)
def echeance(f, e):
    a, g = 28, 110
    up = -1 if e.souffle else 0
    h = e.humeur
    # La robe en cloche, des feuillets épinglés dessus.
    for x in (a - 5, a + 6):
        f.boule(x, g - 1.6, 3.4, 1.6, PRUNE, biais=0.45)
    robe = f.poly([(a - 7, g - 52), (a + 7, g - 52), (a + 11, g - 30), (a + 15.4, g - 4), (a + 13.5, g - 2), (a - 13.5, g - 2),
                   (a - 15.4, g - 4), (a - 11, g - 30)], BEIGE, rond=0.92, gain=0.56, biais=0.36, trame=0.14)
    f.ourler(robe, BEIGE[0], cotes=((0, 1),))
    f.trait(a - 13, g - 5, a - 2, g - 5, BEIGE[4], dans=robe)
    f.courbe([(a - 3, g - 48), (a - 5.5, g - 30), (a - 8, g - 6)], BEIGE[1], dans=robe)
    f.courbe([(a + 4, g - 48), (a + 7, g - 28), (a + 10.5, g - 6)], BEIGE[0], dans=robe)
    _feuillet(f, a - 10, g - 25, ORANGE); _feuillet(f, a + 1, g - 18, BLEU); _feuillet(f, a - 3, g - 37, VIO)
    corsage = f.poly([(a - 9, g - 72 + up), (a + 9, g - 72 + up), (a + 7, g - 52), (a - 7, g - 52)], BEIGE, rond=0.9,
                     gain=0.5, biais=0.3, trame=0.14)
    f.trait(a - 7, g - 53, a + 6, g - 53, ORANGE[2], dans=corsage); f.trait(a - 7, g - 52, a + 6, g - 52, ORANGE[0], dans=corsage)
    f.oy = up
    f.rect(a - 2.5, g - 76, 5, 5, PAPIER, ton=1)
    # Le grand crayon, tenu comme une canne (il penche quand elle a une idée derrière la tête).
    pen = 3.0 if h == "malice" else 0.0
    cx0, cx1 = a + 19.5, a + 19.5 + pen
    f.oy = 0
    f.tube([(cx1, g - 62, 2.0), (cx0, g - 9, 2.0)], CRAYON)
    f.poly([(cx0 - 2, g - 9), (cx0 + 2, g - 9), (cx0, g - 2)], CREME, rond=0.4)
    f.px(cx0 - 0.5, g - 3, ENCRE); f.px(cx0 - 0.5, g - 4, ENCRE)
    f.rect(cx1 - 2, g - 66, 4, 2, GRIS, ton=3); f.rect(cx1 - 2, g - 70, 4, 4, PRUNE, ton=2)
    f.oy = up
    bras_d = [(a + 9, g - 70, 2.9), (a + 13, g - 60, 2.6), (cx0 - 1.5 + pen * 0.6, g - 49, 2.3)]
    bras_g = [(a - 9, g - 70, 2.9), (a - 14.5, g - 61, 2.6), (a - 10, g - 53.5, 2.3)]    # un poing sur la hanche
    for bras, cote, biais in ((bras_d, 1, 0.24), (bras_g, -1, 0.38)):
        s = f.tube(bras, BEIGE, biais=biais, gain=0.5, trame=0.14)
        f.ourler(s, BEIGE[0], cotes=((-cote, 0), (0, 1), (0, -1)), dehors=False)
        f.boule(bras[-1][0] + (cote * 1.2 if cote > 0 else 1.6), bras[-1][1] + 1.6, 2.4, 2.4, GANT, biais=0.5)
    # La tête : un bloc d'éphéméride, bandeau orange, trois anneaux.
    hx, hy = a - 15, g - 106
    tete = pave(f, hx, hy, 29, 31, PAPIER, d=2, c=3, v0=0.9, v1=0.68)
    f.ourler(tete, PAPIER[0], cotes=((0, 1),))
    bandeau = f.rect(hx, hy, 29, 7, ORANGE, ton=2, dans=tete)
    f.trait(hx + 1, hy, hx + 27, hy, ORANGE[4], dans=tete); f.trait(hx, hy + 6, hx + 28, hy + 6, ORANGE[0], dans=tete)
    for k in range(4):
        f.trait(hx + 4 + k * 6, hy + 3, hx + 6 + k * 6, hy + 3, ORANGE[4], dans=tete)
    for x in (hx + 6, hx + 14, hx + 22):                                  # les anneaux
        f.rect(x, hy - 4, 2, 6, GRIS, ton=2); f.px(x, hy - 4, GRIS[4]); f.px(x + 1, hy + 1, GRIS[0])
    for j in range(2):                                                    # les jours qui restent
        for i in range(6):
            f.px(hx + 4 + i * 4, hy + 25 + j * 3, LIGNE)
    cadre(f, hx + 14, hy + 23, hx + 18, hy + 27, ORANGE[2]); f.px(hx + 16, hy + 25, ORANGE[1])   # l'échéance, entourée
    f.poly([(hx + 29, hy + 26), (hx + 29, hy + 31), (hx + 24, hy + 31)], PAPIER, ton=0)       # la page qui se lève
    f.trait(hx + 24, hy + 30, hx + 28, hy + 26, PAPIER[3])
    yo = hy + 14.0
    for cote, x in ((-1, hx + 8.5), (1, hx + 19.5)):
        oeil(f, x, yo, e, cote, rx=2.3, ry=2.8, iris="#4a3a2a", cil=GRIS[0], ri=0.8)
        sourcil(f, x, yo - 4.6, e, cote, l=4.4, c=GRIS[0])
    if h == "malice":
        for x in (hx + 4.5, hx + 23.5):
            f.disque(x, yo + 3.8, 1.9, 1.0, JOUE, dans=tete)
    bouche(f, hx + 14, yo + 6.2, Etat("tendre" if h == "neutre" and not e.bouche else h, e.paup, e.bouche), l=5.4,
           ligne="#5a3a2a")
    f.oy = 0


# ---------------------------------------------------------------------------------------------------------------------
def touche(f, x, y, w, h, r, legende=None, c_leg=None, enfonce=0):
    """Une touche : la jupe sombre, le dessus clair un peu creusé, la légende gravée."""
    plaque(f, x, y + 3, w, h - 3, r, v0=0.3, v1=0.08, coins=1.5)
    s = plaque(f, x + 2, y + enfonce, w - 4, h - 6, r, v0=0.92, v1=0.62, coins=2)
    f.ourler(s, r[1], cotes=((0, 1), (1, 0)), dehors=False)
    f.trait(x + 4, y + enfonce, x + w - 5, y + enfonce, r[len(r) - 1], dans=s)
    f.trait(x + 2, y + enfonce + 2, x + 2, y + enfonce + h - 9, r[len(r) - 1], dans=s)
    if legende:
        graver(f, x + 5, y + enfonce + 3, legende, c_leg or r[0], dans=s)
    return s


@perso("grande-panne", "raccourcis", "Ctrl, Alt et Suppr", ("peur",),
       "les passeurs du Marais : trois touches, ardoise, violette et orange, une rame en travers", w=102, h=62)
def raccourcis(f, e):
    g = 60
    h = e.humeur
    # La rame, derrière eux.
    f.tube([(9, g - 51, 1.5), (58, g - 30, 1.5)], BOIS)
    pale = f.boule(8, g - 51.5, 4.0, 6.6, BOIS, biais=0.45)
    f.trait(8, g - 56, 8, g - 47, BOIS[1], dans=pale)
    for i, (x, w, ht, r, leg) in enumerate(((4, 36, 31, GRIS, "Ctrl"), (43, 25, 28, VIO, "Alt"), (71, 27, 25, ORANGE, "Suppr"))):
        bas = (e.souffle if i != 1 else 1 - e.souffle)                    # ils s'enfoncent tour à tour
        f.ox = ((1, -1, 1)[i] * (1 if e.t % 2 else -1)) if h == "peur" and e.t % 2 else 0   # la peur les fait trembler
        y = g - ht - 1
        s = touche(f, x, y, w, ht, r, leg, r[0] if r is not GRIS else GRIS[0], enfonce=bas)
        cx, yo = x + w / 2.0, y + bas + ht * 0.50
        d = min(5.4, w * 0.2)
        for cote, ex in ((-1, cx - d), (1, cx + d)):
            oeil(f, ex, yo, e, cote, rx=2.0, ry=2.5, iris=ENCRE, cil=r[0], ri=0.84, regard=((-0.4, 0.3, 0.5)[i], 0))
            if h == "peur":
                sourcil(f, ex, yo - 4.2, e, cote, l=3.6, c=r[0])
        bouche(f, cx, yo + 5.6, e, l=4.6, ligne=r[0] if r is not ORANGE else ORANGE[0])
        if h == "peur" and i == 2:
            goutte(f, x + w - 4, y + 4, 1.2)
        f.ox = 0


@perso("grande-panne", "touche-s", "S", ("joie",), "petite touche timide, un S gravé, qui n'ose plus sauver personne",
       w=42, h=46)
def touche_s(f, e):
    a, g = 21, 44
    h = e.humeur
    for cote in (-1, 1):                                                  # deux petits pieds, pointes en dedans
        f.boule(a + cote * 6.5 - cote * 0.8, g - 1.8, 3.2, 1.8, GRIS, biais=0.3)
    y = g - 35 - (1 if e.souffle else 0)
    s = touche(f, a - 15, y, 30, 33, CLAIRE)
    for j, rang in enumerate(GRAND_S):
        for i, v in enumerate(rang):
            if v == "1":
                f.px(a - 11 + i, y + 3 + j, BLEU[1] if j < 6 else BLEU[0])
    timide = h != "joie"
    yo = y + 16.5 + (0.6 if timide else 0)
    for cote, x in ((-1, a - 3.5), (1, a + 6)):
        oeil(f, x, yo, e, cote, rx=2.3, ry=2.9, iris="#2a3a5e", cil=CLAIRE[0], ri=0.84, regard=(0.5, 0.5) if timide else (0, 0),
             arc="#2a3a5e")
        if timide:
            sourcil(f, x, yo - 4.8, Etat("triste"), cote, l=3.6, c=CLAIRE[0])
    for x in (a - 8.5, a + 10.5):
        f.disque(x, yo + 4.4, 2.2, 1.2, "#f5c8d6", dans=s)
    bouche(f, a + 1.2, yo + 6.2, e, l=4.0 if timide else 5.0, ligne="#2a3a5e")


# ---------------------------------------------------------------------------------------------------------------------
CYAN = Rampe("#1a6a96", "#2a8fc0", "#8fe0ff")


@perso("grande-panne", "imprimante", "L'Imprimante", ("colere",),
       "diva de la file d'impression : longs cils, cartouches dont la cyan est vide quand elle se fâche", w=96, h=88)
def imprimante(f, e):
    a, g = 46, 86
    up = -1 if e.souffle else 0
    h = e.humeur
    for x in (a - 31, a + 25):
        f.rect(x, g - 3, 7, 3, GRIS, ton=0)
    base = plaque(f, a - 35, g - 15, 70, 12, BEIGE, v0=0.5, v1=0.3)
    f.rect(a - 28, g - 13, 52, 5, GRIS, ton=0, dans=base)
    lang = f.rect(a - 22, g - 12, 38, 3, PAPIER, ton=2)                      # la page qui sort, en bas
    f.trait(a - 18, g - 11, a + 6, g - 11, LIGNE, dans=lang)
    f.oy = up
    # La feuille engagée en haut, qui se courbe.
    feuille = f.poly([(a - 22, g - 77), (a + 17, g - 78), (a + 19, g - 50), (a - 21, g - 50)], PAPIER, rond=0.35, gain=0.5,
                     biais=0.52)
    f.trait(a - 21, g - 77, a + 16, g - 78, PAPIER[3], dans=feuille)
    for k in range(5):
        f.trait(a - 17, g - 72 + k * 3, a + 11 - (k * 5) % 9, g - 72 + k * 3, LIGNE, dans=feuille)
    corps = pave(f, a - 39, g - 51, 76, 37, BEIGE, d=4, c=4, v0=0.86, v1=0.58)
    f.ourler(corps, BEIGE[0], cotes=((0, 1),))
    f.trait(a - 24, g - 53, a + 22, g - 53, BEIGE[0])                        # la fente, sur le dessus
    f.trait(a - 38, g - 50, a - 38, g - 18, BEIGE[4], dans=corps)
    # Le pupitre : trois cartouches (cyan, violet, or) et un bouton.
    f.rect(a + 15, g - 47, 20, 12, BEIGE, ton=1, dans=corps)
    for i, r in enumerate((CYAN, VIO, LAITON)):
        vide = i == 0 and h == "colere"
        x = a + 17 + i * 6
        c = f.rect(x, g - 45, 4, 8, GRIS if vide else r, ton=1 if vide else (2 if r is not CYAN else 1), dans=corps)
        if not vide:
            f.px(x, g - 45, "#ffffff")
        elif e.t % 2:
            cadre(f, x - 1, g - 46, x + 4, g - 37, ORANGE[2])                # elle réclame
    f.px(a + 19, g - 30, GRIS[4]); f.px(a + 20, g - 30, GRIS[2]); f.px(a + 19, g - 29, GRIS[2]); f.px(a + 20, g - 29, GRIS[0])
    f.trait(a + 24, g - 30, a + 32, g - 30, BEIGE[0], dans=corps); f.trait(a + 24, g - 28, a + 30, g - 28, BEIGE[1], dans=corps)
    for y in range(g - 46, g - 22, 3):                                      # les ouïes, sur le flanc
        f.px(a + 38, y, BEIGE[1]); f.px(a + 39, y - 1, BEIGE[1])
    # Le visage : de grands yeux, de longs cils, une bouche prune.
    yo = g - 37.0
    for cote, x in ((-1, a - 21), (1, a - 5)):
        o = oeil(f, x, yo, e, cote, rx=3.2, ry=3.7, iris="#4a3a6e", cil=ENCRE, ri=0.82)
        if o:
            haut = min(Y for (_, Y) in o) - f.oy
            for (dx, dy) in ((4, 0), (5, -1), (6, -2)):                       # un long cil, vers la tempe
                f.px(x + cote * dx + (0 if cote > 0 else -1), haut + dy, ENCRE)
            for (X, Y) in o:                                                   # le fard, sur la paupière
                if (X, Y - 1) not in o and corps and (X, Y - 2) in corps:
                    f.pose(X, Y - 2, VIO[3])
        if h == "colere":
            sourcil(f, x, yo - 7.2, e, cote, l=6.0, c=ENCRE, ep=2)
    eb = e
    bouche(f, a - 13, yo + 9.6, eb, l=7.0, ligne=BOUCHE)
    if not e.bouche and h != "colere":
        f.px(a - 14, yo + 10.8, "#c76f9a"); f.px(a - 13, yo + 10.8, "#c76f9a")   # la lèvre
    f.oy = 0


# ---------------------------------------------------------------------------------------------------------------------
@perso("grande-panne", "brouillon", "Brouillon, le Sans-Titre", ("peur", "tendre", "joie"),
       "« Document sans titre (récupéré) » : une feuille qui tremble, une phrase inachevée et ses trois points",
       w=50, h=72)
def brouillon_feuille(f, e):
    a, g = 25, 70
    h = e.humeur
    f.oy = -1 if e.souffle else 0
    f.ox = (1 if e.t % 2 else -1) if h == "peur" and e.t % 2 else 0
    x0, x1, y0, y1 = a - 17, a + 17, g - 60, g - 3
    corps = f.poly([(x0, y0), (x1 - 8, y0), (x1, y0 + 8), (x1 + 0.6, y1), (x0 + 0.6, y1)], PAPIER, rond=0.5, gain=0.46,
                   biais=0.56)
    f.poly([(x1 - 8, y0), (x1, y0 + 8), (x1 - 8, y0 + 8)], BEIGE, ton=3)        # le coin corné
    f.trait(x1 - 8, y0 + 1, x1 - 8, y0 + 8, PAPIER[0]); f.trait(x1 - 8, y0 + 8, x1 - 1, y0 + 8, PAPIER[0])
    f.trait(x0 + 1, y0 + 2, x0 + 1, y1 - 8, PAPIER[3], dans=corps)
    # Les deux coins du bas se retroussent : ses pieds.
    for cote in (-1, 1):
        x = a + cote * 13
        f.px(x, y1, PAPIER[1]); f.px(x + cote, y1, PAPIER[1]); f.px(x + cote, y1 + 1, PAPIER[2]); f.px(x + cote * 2, y1 + 1, PAPIER[2])
    for x in range(x0 + 5, x0 + 19, 3):                                     # le titre, absent : des tirets
        f.px(x, y0 + 6, LIGNE); f.px(x + 1, y0 + 6, LIGNE)
    # La phrase inachevée, au crayon, ses trois points, et le curseur qui attend la suite.
    f.trait(x0 + 5, g - 21, x1 - 5, g - 21, LIGNE, dans=corps)
    f.trait(x0 + 5, g - 17, x1 - 9, g - 17, LIGNE, dans=corps)
    f.trait(x0 + 5, g - 13, x0 + 14, g - 13, LIGNE, dans=corps)
    for k in range(3):
        f.px(x0 + 16 + k * 2, g - 13, BLEU[0])
    if e.t % 2 == 0:
        f.trait(x0 + 23, g - 15, x0 + 23, g - 12, BLEU[1])
    yo = g - 40.0
    for cote, x in ((-1, a - 6.2), (1, a + 5.8)):
        oeil(f, x, yo, e, cote, rx=2.9, ry=3.5, iris="#3a3028", cil="#5a5244", ri=0.7)
        sourcil(f, x, yo - 6.2, e, cote, l=4.6, c="#8a8f9e")
    plein = h in ("joie", "tendre")
    for x in (a - 11.6, a + 11.2):
        f.disque(x, yo + 5.2, 2.4 if plein else 1.8, 1.3 if plein else 0.9, JOUE if plein else '#f6c9b4', dans=corps)
    bouche(f, a - 0.2, yo + 8.2, e, l=5.4, ligne="#5a4a3a")
    if h == "peur":
        goutte(f, x1 - 3, y0 + 13, 1.3)
    f.ox = f.oy = 0


# ---------------------------------------------------------------------------------------------------------------------
TIC = Rampe("#bfc4a4", "#e2e3c2", "#f4f4de", cerne="#5a4a1c")
TAC = Rampe("#dc9a66", "#ffc890", "#ffe4c4", cerne="#5a4a1c")


@perso("grande-panne", "tic-tac", "Le Tic-Tac", ("joie", "triste"),
       "petit balancier de laiton à pattes : côté tic pâle et inquiet, côté tac chaud et paisible", w=46, h=78)
def tic_tac(f, e):
    a, g = 23, 76
    h = e.humeur
    up = -1 if e.souffle else 0
    s = (0, 1, 0, -1)[e.t % 4]                                              # tic… tac…
    for cote in (-1, 1):
        f.rect(a + cote * 5.5 - 1, g - 15, 2, 12, GRIS, ton=1)
        f.trait(a + cote * 5.5 - 1, g - 15, a + cote * 5.5 - 1, g - 4, GRIS[2])
        f.boule(a + cote * 7, g - 1.8, 3.4, 1.8, GRIS, biais=0.4)
    f.oy = up
    # La tige et son anneau : ils battent d'un côté, de l'autre.
    f.poly([(a + s * 2 - 1.5, g - 71), (a + s * 2 + 1.5, g - 71), (a + 1.5, g - 43), (a - 1.5, g - 43)], LAITON, rond=0.8)
    an = f.boule(a + s * 2, g - 72, 3.4, 3.4, LAITON)
    f.px(a + s * 2 - 0.5, g - 72.5, LAITON.cerne)
    # Le disque : jante de laiton, moitié tic, moitié tac.
    f.boule(a, g - 29, 16.2, 16.2, LAITON, biais=0.42)
    tic = f.boule(a, g - 29, 13.2, 13.2, TIC, biais=0.5, gain=0.5, cond=lambda x, y, u, v: x < a)
    tac = f.boule(a, g - 29, 13.2, 13.2, TAC, biais=0.56, gain=0.5, cond=lambda x, y, u, v: x >= a)
    f.trait(a - 0.5, g - 42, a - 0.5, g - 16, LAITON[0])
    for (dx, dy) in ((0, -11.5), (0, 11.5), (-11.5, 0), (11.5, 0)):
        f.px(a + dx - 0.5, g - 29 + dy, LAITON[0])                        # quatre repères d'heure
    f.courbe([(a - 13.5, g - 33), (a - 11.5, g - 39), (a - 7, g - 43)], LAITON[3])
    yo = g - 31.0
    e_tic = Etat("triste" if h in ("neutre", "triste") else h, e.paup, e.bouche)
    e_tac = Etat("tendre" if h == "neutre" else h, e.paup, e.bouche)
    oeil(f, a - 6.2, yo, e_tic, -1, rx=2.4, ry=3.0, iris="#3a3a2a", cil="#5a4a1c", ri=0.82)
    sourcil(f, a - 6.2, yo - 5.0, e_tic, -1, l=4.4, c="#8a6a1c")
    oeil(f, a + 6.2, yo, e_tac, 1, rx=2.4, ry=3.0, iris="#4a2e1a", cil="#5a4a1c", ri=0.82)
    if h != "triste":
        f.disque(a + 9.6, yo + 4.6, 2.0, 1.1, JOUE, dans=tac)
    bouche(f, a, yo + 8.0, Etat("malice" if h == "neutre" and not e.bouche else h, e.paup, e.bouche), l=6.0, ligne="#5a3a1c")
    if h == "triste":
        goutte(f, a - 8.5, yo + 6.6, 1.2)
    f.oy = 0


# ---------------------------------------------------------------------------------------------------------------------
@perso("grande-panne", "balayeur", "Le Balayeur", ("triste",),
       "le Grand Nettoyage : un balai de paille au chapeau rond, très poli, un nœud au col", w=58, h=106)
def balayeur(f, e):
    a, g = 28, 104
    up = -1 if e.souffle else 0
    h = e.humeur
    # La paille : une gerbe qui s'évase, brin par brin, le bas inégal.
    paille = f.poly([(a - 11.5, g - 46), (a + 11.5, g - 46), (a + 20.5, g - 2), (a - 20.5, g - 2)], PAILLE, rond=0.75,
                    gain=0.56, biais=0.36, trame=0.14)
    for k in range(-9, 10, 2):
        f.trait(a + k * 1.15, g - 45, a + k * 2.15, g - 3, PAILLE[1] if k % 4 else PAILLE[4 if k < 0 else 0], dans=paille)
    f.gommer({(X, Y) for (X, Y) in paille if Y >= g - 4 and (X * 7 + 3) % 5 < 2 and (Y >= g - 3 or X % 3 == 0)})
    # Le manche et le chapeau melon, qui respirent ; la virole et son nœud papillon.
    f.oy = up
    f.tube([(a + 1, g - 50, 2.3), (a + 3.4, g - 92, 2.0)], BOIS)
    f.trait(a + 1, g - 86, a - 0.2, g - 56, BOIS[4])
    bord = f.disque(a + 4, g - 92.6, 9.4, 2.4, FEUTRE, ton=1)
    f.ourler(bord, FEUTRE[3], cotes=((0, -1),))                             # un liseré clair : il se lit sur fond sombre
    ch = f.boule(a + 4, g - 96.6, 6.2, 6.0, FEUTRE, biais=0.4, cond=lambda x, y, u, v: v < 0.62)
    f.trait(a - 2, g - 93.6, a + 10, g - 93.6, FEUTRE[3], dans=ch)
    f.ourler(ch, FEUTRE[3], cotes=((-1, 0), (0, -1)))
    f.px(a + 1.5, g - 99.5, "#aab2c2")
    f.oy = 0
    vir = plaque(f, a - 12.5, g - 53, 25, 8, GRIS, v0=0.85, v1=0.5)
    f.ourler(vir, GRIS[0], cotes=((0, 1),))
    f.trait(a - 11, g - 53, a + 10, g - 53, GRIS[4], dans=vir)
    for y in (g - 51, g - 48):
        for x in range(a - 10, a + 11, 3):
            f.px(x, y, GRIS[0])                                             # la couture
    f.poly([(a - 6, g - 52.5), (a, g - 49.5), (a - 6, g - 46)], PRUNE, ton=2); f.poly([(a + 6, g - 52.5), (a, g - 49.5), (a + 6, g - 46)], PRUNE, ton=1)
    f.rect(a - 1, g - 51, 2, 3, PRUNE, ton=3)
    yo = g - 35.0
    for cote, x in ((-1, a - 5.4), (1, a + 5.0)):
        oeil(f, x, yo, e, cote, rx=2.5, ry=3.0, iris=ENCRE, cil=PAILLE[0], ri=0.82)
        sourcil(f, x, yo - 5.2, e, cote, l=4.6, c=BOIS[0])
    bouche(f, a - 0.2, yo + 8.0, Etat("tendre" if h == "neutre" and not e.bouche else h, e.paup, e.bouche), l=6.0,
           ligne=BOIS[0])
    if h == "triste":
        goutte(f, a - 8, yo + 6.4, 1.2)
