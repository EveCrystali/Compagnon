"""« Petit Nuage » en haute définition : les huit personnages que Brouillon rencontre (personnages_hd.py).

Des nuages, des bêtes, une girouette. Ceux de profil regardent vers la gauche (vers Pilou) ; la lumière vient d'en
haut à gauche. La toise de la campagne (unités ; Pilou : corps de 62) : Tournebise 114 sur son mât, Madame Bocal 73,
Ondée 74 de haut pluie comprise (à 30 du sol), les Enclumes 60 (à 30), Dentelle au bout de son fil (à 34), les
Froisseuses 39 (à 44), Brouillon 38 (à 24), Mi-Bémol 36, la bergeronnette 35.
"""
import math

from pinceau_hd import Rampe
from personnages_hd import (perso, Etat, oeil, sourcil, bouche, goutte, ENCRE, BLANC, BOUCHE, JOUE, LARME, BOIS, VERRE,
                            CREME)

ROUILLE = Rampe("#5a2e12", "#8a4a1f", "#b8652e", "#e0995a", "#f2c08a")
FER = Rampe("#14161c", "#262a34", "#444a58", "#6a7284")
MAT = Rampe("#2a2f3a", "#444a58", "#6a7284", "#a2aabb", cerne="#14161c")      # le fer du mât : il se lit sur fond sombre
OR = Rampe("#a8862a", "#e8c447", "#fff0a0")
ONDEE = Rampe("#5d667c", "#8790a4", "#a9b1c2", "#c3cad8", "#dfe4ec", cerne="#3a4256")
ORAGE = Rampe("#262a35", "#3c4252", "#5c6478", "#8790a4", "#b4bccb", cerne="#14161c")
SARCELLE = Rampe("#124a5a", "#1d6578", "#2f8f9c", "#5bb3ae", "#9fdcd2")
VIO = Rampe("#2e2450", "#4a3a7e", "#6a5acd", "#9b8cff", "#c9c0ff")
MARMOTTE = Rampe("#4a3018", "#6b4a2e", "#a07a52", "#c8a274", "#e6cfa6")
AILE = Rampe("#2c2850", "#46406e", "#5c5a9a", "#8a79b8", "#b9aee0")
PLUME = Rampe("#5a6070", "#8890a0", "#b8bfcc", "#e2e6ee")
LAITON = Rampe("#8a6a1c", "#b8922a", "#e8c447", "#fff0a0")
PECHE = "#ffd29a"
NUIT = "#262a35"


def nuee(f, bosses, rampe, biais=0.5, gain=0.62):
    corps = set()
    for (x, y, rx, ry) in bosses:
        corps |= f.boule(x, y, rx, ry, rampe, biais=biais, gain=gain)
    return corps


# ---------------------------------------------------------------------------------------------------------------------
@perso("petit-nuage", "tournebise", "Tournebise", ("triste", "tendre"),
       "vieille girouette : coq de fer rouillé de profil, crête et bec dorés, sur sa croix des vents", w=72, h=118)
def tournebise(f, e):
    a, g = 37, 116
    h = e.humeur
    up = -1 if e.souffle else 0
    # Le mât, son pied de faîtage, la croix des vents.
    f.poly([(a - 7, g), (a + 7, g), (a + 1.5, g - 10), (a - 1.5, g - 10)], MAT, rond=0.8)
    mat = f.rect(a - 1, g - 72, 2, 62, MAT, ton=1)
    f.trait(a - 1, g - 72, a - 1, g - 11, MAT[3])
    f.boule(a, g - 46, 2.6, 2.6, MAT, biais=0.45)
    for cote in (-1, 1):
        f.rect(a + cote * 9 - 7, g - 53, 14, 2, MAT, ton=1)
        f.trait(a + cote * 9 - 7, g - 53, a + cote * 9 + 6, g - 53, MAT[3])
        f.boule(a + cote * 17, g - 52, 2.2, 2.2, MAT, biais=0.45)
    f.rect(a - 1, g - 60, 2, 6, MAT, ton=1); f.boule(a, g - 61, 2.0, 2.0, MAT, biais=0.45)
    # La flèche : elle pointe vers la montagne.
    fl = f.rect(a - 22, g - 73 + up, 46, 2, MAT, ton=1)
    f.trait(a - 22, g - 73 + up, a + 23, g - 73 + up, MAT[3])
    f.poly([(a - 29, g - 72 + up), (a - 21, g - 76.5 + up), (a - 21, g - 67.5 + up)], MAT, rond=0.5)
    f.poly([(a + 20, g - 77 + up), (a + 27, g - 77 + up), (a + 23, g - 72 + up), (a + 27, g - 67 + up), (a + 20, g - 67 + up)], MAT, ton=1)
    f.oy = up
    bas = 2.0 if h == "triste" else 0.0                   # la tête tombe quand il est triste
    # La queue en faucilles, le corps, l'aile, le cou.
    for k, pts in enumerate(([(a + 11, g - 81, 2.2), (a + 19, g - 84, 1.5), (a + 24, g - 80, 0.6)],
                             [(a + 12, g - 84, 2.8), (a + 21, g - 92, 2.0), (a + 28, g - 92, 1.2), (a + 31, g - 86, 0.6)],
                             [(a + 11, g - 88, 3.0), (a + 19, g - 100, 2.2), (a + 27, g - 103, 1.4), (a + 32, g - 97, 0.7)])):
        f.tube(pts, ROUILLE, biais=0.24 + 0.06 * k)
    f.trait(a - 3, g - 77, a - 3, g - 74, FER[1]); f.trait(a + 5, g - 77, a + 5, g - 74, FER[1])     # les pattes
    corps = f.boule(a + 2, g - 86, 13.4, 10.2, ROUILLE)
    corps |= f.tube([(a - 6, g - 90, 5.6), (a - 11, g - 101 + bas, 4.4)], ROUILLE)
    aile = f.boule(a + 4, g - 85, 8.4, 5.6, ROUILLE, biais=0.26)
    for k in range(3):
        f.courbe([(a - 1 + k * 3.4, g - 87), (a + 1 + k * 3.4, g - 83.5), (a + 4 + k * 3.4, g - 81.5)], ROUILLE[0], dans=aile)
    tete = f.boule(a - 11.5, g - 103.5 + bas, 5.2, 5.0, ROUILLE, biais=0.42)
    # La rouille : des piqûres sombres en trame, des écailles claires, trois rivets.
    f.disque(a + 2, g - 84, 13, 9, ROUILLE[0], dans=corps, densite=lambda x, y: 0.16 if (int(x) * 5 + int(y) * 3) % 7 < 2 else 0.0)
    for (x, y) in ((a - 4, g - 91), (a + 8, g - 92), (a - 2, g - 80), (a - 9, g - 96)):
        f.px(x, y, ROUILLE[4])
    for (x, y) in ((a - 7, g - 88), (a + 12, g - 87), (a + 2, g - 78)):
        f.px(x, y, FER[2]); f.px(x + 1, y + 1, ROUILLE[0])
    # La crête et le bec, dorés ; le barbillon.
    for (x, y, r) in ((a - 14, g - 108.6, 1.9), (a - 11.2, g - 110, 2.1), (a - 8.4, g - 108.8, 1.9)):
        f.boule(x, y + bas, r, r, OR, biais=0.5)
    f.poly([(a - 15.5, g - 105 + bas), (a - 21.5, g - 103.2 + bas), (a - 15.5, g - 102 + bas)], OR, ton=1)
    f.px(a - 17.5, g - 104.4 + bas, OR[2])
    if e.bouche:
        f.poly([(a - 15.5, g - 102 + bas), (a - 20, g - 101.4 + e.bouche * 0.8 + bas), (a - 15.5, g - 100.4 + bas)], OR, ton=0)
        f.px(a - 16.5, g - 101.4 + bas, BOUCHE)
    f.boule(a - 13.6, g - 99 + bas, 1.5, 2.1, OR, biais=0.3)
    yo = g - 104.4 + bas
    oeil(f, a - 12.6, yo, e, -1, rx=1.9, ry=2.2, iris=ENCRE, blanc="#fff0a0", cil=ROUILLE[0], ri=0.7, regard=(-0.4, 0),
         arc=ROUILLE[0])
    if h == "triste":
        f.trait(a - 15, yo - 2.4, a - 10.6, yo - 4.2, ROUILLE[0])
        goutte(f, a - 16.5, yo + 6, 1.1)
    f.oy = 0


# ---------------------------------------------------------------------------------------------------------------------
@perso("petit-nuage", "ondee", "Ondée", ("tendre",),
       "la plus vieille du troupeau : nuage gris très large, paupières tranquilles, une pluie douce dessous",
       w=132, h=84, vol=30)
def ondee(f, e):
    h = e.humeur
    f.oy = -1 if e.souffle else 0
    cx = 66.0
    # La pluie, très douce : des traits courts qui descendent, en trame (ils ne se cernent pas).
    for i in range(11):
        x = 22 + i * 8.6 + (3 if i % 2 else 0)
        y = 56 + ((i * 7 + e.t * 4) % 16)
        for k in range(4):
            f.px(x - k * 0.5, y + k, LARME[1 if k % 2 else 0], "")
        f.px(x - 2, y + 4, LARME[2], "")
    corps = nuee(f, ((38, 23, 17, 14), (64, 18, 19, 15), (92, 21, 18, 14), (20, 35, 15, 12), (112, 36, 15, 12),
                     (66, 33, 36, 18), (44, 43, 21, 9.5), (88, 44, 21, 9.5)), ONDEE)
    for pts in ([(26, 30), (31, 25), (38, 24)], [(84, 23), (91, 20), (98, 22)], [(52, 49), (62, 51), (72, 49)],
                [(100, 40), (106, 36), (112, 37)]):
        f.courbe(pts, ONDEE[2], dans=corps)
    f.px(30, 12, "#ffffff"); f.px(31, 11, "#ffffff"); f.px(58, 6, "#ffffff")
    yo = 32.0
    calme = Etat("tendre" if h == "neutre" else h, e.paup, e.bouche)
    for cote, x in ((-1, cx - 9), (1, cx + 9)):
        oeil(f, x, yo, calme, cote, rx=3.2, ry=3.7, iris="#3c4252", pupille="#262a35", blanc="#eef1f6", cil="#3c4252",
             ri=0.62, arc="#3c4252")
        f.trait(x + cote * 4.6, yo - 1, x + cote * 6.4, yo - 2, ONDEE[0])            # les rides au coin de l'œil
        f.trait(x + cote * 4.6, yo + 1, x + cote * 6.6, yo + 1.6, ONDEE[0])
        f.courbe([(x - 3, yo + 5.2), (x, yo + 6.2), (x + 3, yo + 5.2)], ONDEE[1], dans=corps)
        f.trait(x - 3, yo - 6.6, x + 3, yo - 7.2 - cote * 0.3, ONDEE[0])               # un sourcil lourd
    if h == "tendre":
        for x in (cx - 16.5, cx + 16.5):
            f.disque(x, yo + 6, 3.0, 1.6, "#d8b4c4", dans=corps)
    bouche(f, cx, yo + 8.4, Etat("tendre" if h == "neutre" and not e.bouche else h, e.paup, e.bouche), l=7.0, ligne="#3c4252")
    f.oy = 0


# ---------------------------------------------------------------------------------------------------------------------
@perso("petit-nuage", "mi-bemol", "Mi-Bémol", ("joie",),
       "cheffe du chœur : rainette sarcelle au ventre crème, une baguette de jonc", w=60, h=58)
def mi_bemol(f, e):
    a, g = 27, 56
    h = e.humeur
    up = -1 if e.souffle else 0
    leve = h == "joie" or e.bouche >= 2
    # La baguette de jonc, dans la main droite ; elle bat la mesure.
    bx, by = (a + 25, g - 44 - (e.t % 2) * 2) if leve else (a + 26, g - 30)
    f.trait(a + 13, g - 14, bx, by, "#b8a060"); f.px(bx, by, "#6b4a2e"); f.px(bx, by - 1, "#6b4a2e")
    # Les cuisses repliées, les pieds palmés.
    for cote in (-1, 1):
        f.boule(a + cote * 13.5, g - 7.4, 6.4, 6.8, SARCELLE, biais=0.3 if cote > 0 else 0.4)
        p = f.boule(a + cote * 15, g - 1.8, 5.4, 1.8, SARCELLE, biais=0.44)
        for k in (-1, 0, 1):
            f.px(a + cote * 15 + k * 3 - cote, g - 0.6, SARCELLE[4])
    f.oy = up
    corps = f.boule(a, g - 15, 15.4, 12.6, SARCELLE)
    for (x, y) in ((a + 7, g - 23), (a + 10, g - 18), (a - 9, g - 21)):                   # les taches du dos
        f.px(x, y, SARCELLE[0]); f.px(x + 1, y, SARCELLE[0]); f.px(x, y + 1, SARCELLE[0])
    ventre = f.boule(a - 0.5, g - 10, 9.8, 7.8, CREME, biais=0.5, dans=corps)
    f.ourler(ventre, CREME[0], cotes=((0, -1),), dehors=False)
    # Les yeux, en haut du crâne.
    yo = g - 28.0
    for cote, x in ((-1, a - 8), (1, a + 7)):
        f.boule(x, yo, 5.8, 5.6, SARCELLE, biais=0.44)
        oeil(f, x - 0.2, yo + 0.2, e, cote, rx=3.4, ry=3.6, iris=ENCRE, blanc=BLANC, cil=SARCELLE[0], ri=0.62, regard=(-0.4, 0),
             arc=SARCELLE[0])
    # La grande bouche, et la gorge qui se gonfle quand elle chante.
    if e.bouche:
        gorge = f.boule(a - 0.5, g - 13.5 + e.bouche, 5.0 + e.bouche * 1.2, 3.6 + e.bouche, CREME, biais=0.6)
        bouche(f, a - 0.5, g - 19.5, Etat("joie", e.paup, e.bouche), l=11.0)
    else:
        f.courbe([(a - 8.5, g - 20.4), (a - 4, g - 18.2), (a + 3, g - 18.2), (a + 7.5, g - 20.4)], "#0e3a48")
        if h == "joie":
            for x in (a - 11.5, a + 10.5):
                f.disque(x, g - 20.6, 2.0, 1.1, JOUE, dans=corps)
    f.px(a - 2, g - 22.4, SARCELLE[0]); f.px(a + 1, g - 22.4, SARCELLE[0])              # les narines
    # Les mains : l'une sur le ventre, l'autre tient la baguette.
    f.boule(a - 8, g - 9.5, 2.6, 2.0, SARCELLE, biais=0.5)
    for k in (-1, 0, 1):
        f.px(a - 8 + k * 1.6, g - 7.4, SARCELLE[4])
    f.tube([(a + 9, g - 15, 2.2), (a + 13, g - 13.5, 2.0)], SARCELLE, biais=0.32)
    f.oy = 0


# ---------------------------------------------------------------------------------------------------------------------
@perso("petit-nuage", "dentelle", "Dentelle", ("malice",),
       "araignée violette pendue à son fil, marchande de rosée : une goutte à vendre", w=70, h=112, vol=34)
def dentelle(f, e):
    a = 37
    h = e.humeur
    f.oy = -1 if e.souffle else 0
    f.ox = (0, 1, 0, -1)[e.t % 4]                         # elle se balance au bout du fil
    for y in range(-2, 62):
        f.px(a - 0.5, y, "#c9bfe8" if y % 5 else "#ffffff", "")
    cy = 70.0
    # Les huit pattes, fines, coudées.
    for i in range(4):
        for cote in (-1, 1):
            if cote < 0 and i == 3:
                continue                                   # celle-là tient la goutte
            genou = (a + cote * (13 + i * 2.2), cy - 9 + i * 5.0)
            pied = (a + cote * (18.5 + i * 1.6), cy + 1 + i * 6.6)
            f.tube([(a + cote * 5, cy + 2 + i * 1.2, 1.2), genou + (1.0,), pied + (0.7,)], VIO, biais=0.2 if cote > 0 else 0.3)
    # L'abdomen et sa dentelle : un napperon de points clairs.
    abd = f.boule(a, cy + 13, 11.4, 10.4, VIO)
    for r, n in ((3.2, 6), (6.4, 10), (9.0, 14)):
        for k in range(n):
            ang = k * 2 * math.pi / n + r
            x, y = a - 0.5 + r * math.cos(ang), cy + 13 + r * 0.9 * math.sin(ang)
            if (int(math.floor(x)) + f.ox, int(math.floor(y)) + f.oy) in abd:
                f.px(x, y, VIO[4] if x < a + 2 else VIO[3])
    f.px(a - 0.5, cy + 13, "#ffffff")
    tete = f.boule(a, cy, 8.4, 7.2, VIO, biais=0.42)
    # La patte qui tient la goutte de rosée.
    f.tube([(a - 5, cy + 5.6, 1.2), (a - 15, cy + 12, 1.0), (a - 21, cy + 17, 0.8)], VIO, biais=0.3)
    gx, gy = a - 23, cy + 22
    f.poly([(gx, gy - 6.5), (gx + 3, gy), (gx - 3, gy)], LARME, rond=0.0, ton=1)
    f.boule(gx, gy, 3.3, 3.3, LARME)
    f.px(gx - 1.5, gy - 1.5, "#ffffff"); f.px(gx - 0.5, gy - 2.5, "#ffffff"); f.px(gx + 1.5, gy + 1.5, LARME[2])
    if e.t % 2:
        f.px(gx + 4.5, gy - 6, "#ffffff", ""); f.px(gx + 5.5, gy - 6, "#ffffff", ""); f.px(gx + 4.5, gy - 7, "#ffffff", "")
    # Le visage : deux grands yeux, deux petits au-dessus, couleur pêche.
    yo = cy + 0.4
    for cote, x in ((-1, a - 3.8), (1, a + 3.4)):
        oeil(f, x, yo, e, cote, rx=2.3, ry=2.7, iris=ENCRE, blanc="#f2eefc", cil=VIO[0], ri=0.72, regard=(-0.4, 0), arc="#f2eefc")
        f.px(x - cote * 0.6 + cote * 1.8, yo - 4.8, PECHE)
    bouche(f, a - 0.4, yo + 4.6, Etat("tendre" if h == "neutre" and not e.bouche else h, e.paup, e.bouche), l=4.4, ligne="#f2eefc")
    f.ox = f.oy = 0


# ---------------------------------------------------------------------------------------------------------------------
@perso("petit-nuage", "madame-bocal", "Madame Bocal", ("joie",),
       "marmotte ronde du col : un bocal serré contre elle, un courant d'air dedans", w=70, h=86)
def madame_bocal(f, e):
    a, g = 35, 84
    h = e.humeur
    up = -1 if e.souffle else 0
    for cote in (-1, 1):
        p = f.boule(a + cote * 10, g - 3.2, 7.6, 3.2, MARMOTTE, biais=0.3)
        for k in (-1, 0, 1):
            f.px(a + cote * 10 + k * 3 - 2, g - 1.4, MARMOTTE[0])
    f.boule(a + 20, g - 10, 6.5, 5.0, MARMOTTE, biais=0.24)                                  # la queue
    corps = f.boule(a, g - 27, 21.6, 25.2, MARMOTTE)
    f.boule(a - 1, g - 22, 13.5, 17.5, MARMOTTE, biais=0.72, gain=0.4, dans=corps)            # le ventre clair
    for (x, y) in ((a - 17, g - 30), (a - 18, g - 22), (a + 16, g - 34), (a + 18, g - 24), (a - 14, g - 40), (a + 13, g - 43)):
        f.px(x, y, MARMOTTE[1]); f.px(x + 1, y + 1, MARMOTTE[1])                             # le poil
    f.oy = up
    # Le bocal : verre, couvercle de laiton, et le courant d'air qui tourne dedans.
    verre = f.tour(a - 0.5, g - 39, g - 14, lambda y: 9.6 if y > g - 36 else 8.4, VERRE, biais=0.34)
    f.trait(a - 8, g - 34, a - 8, g - 20, "#ffffff", dans=verre)
    ph = e.t % 4
    f.courbe([(a - 6, g - 20 - ph), (a - 2, g - 25 - ph * 0.5), (a + 3, g - 21), (a + 6, g - 27 + ph)], "#5a9fd8", dans=verre)
    f.courbe([(a - 5, g - 29 + ph), (a - 0.5, g - 32), (a + 4.5, g - 30 - ph * 0.5)], "#8fc8f0", dans=verre)
    f.px(a + 2 - ph, g - 24 + ph, "#ff9a3c") if (int(a + 2 - ph), int(g - 24 + ph) + up) in verre else None   # une feuille prise dedans
    couv = f.rect(a - 10, g - 42.5, 19, 4, LAITON, rond=0.8)
    f.trait(a - 9, g - 42.5, a + 4, g - 42.5, LAITON[3]); f.trait(a - 10, g - 39.5, a + 8, g - 39.5, LAITON[0], dans=couv)
    # Les bras, serrés autour.
    for cote in (-1, 1):
        s = f.tube([(a + cote * 16, g - 40, 4.4), (a + cote * 15, g - 30, 4.0), (a + cote * 9.5, g - 25, 3.6)], MARMOTTE,
                   biais=0.3 if cote > 0 else 0.4)
        f.ourler(s, MARMOTTE[0], cotes=((0, 1), (-cote, 0)), dehors=False)
        f.boule(a + cote * 8, g - 25.5, 3.4, 3.0, MARMOTTE, biais=0.2)
        for k in (-1, 0, 1):
            f.px(a + cote * 7.5, g - 25.5 + k * 1.6, MARMOTTE[0])
    # La tête : oreilles rondes, museau clair, truffe, deux incisives.
    tx, ty = a - 0.5, g - 58.0
    for cote in (-1, 1):
        o = f.boule(tx + cote * 11.2, ty - 10.2, 3.4, 3.2, MARMOTTE, biais=0.3)
        f.px(tx + cote * 11.2 - 0.5, ty - 9.8, MARMOTTE[0])
    tete = f.boule(tx, ty, 15.2, 13.4, MARMOTTE)
    mus = f.boule(tx - 1, ty + 5.4, 7.4, 5.2, MARMOTTE, biais=0.74, gain=0.4)
    f.disque(tx - 1.4, ty + 2.6, 2.4, 1.6, ENCRE)
    f.px(tx - 2.4, ty + 1.8, "#8890a0")
    yo = ty - 2.6
    for cote, x in ((-1, tx - 7.2), (1, tx + 5.8)):
        oeil(f, x, yo, e, cote, rx=2.3, ry=2.8, iris=ENCRE, cil=MARMOTTE[0], ri=0.8, regard=(-0.3, 0), arc=MARMOTTE[0])
    for x in (tx - 10.5, tx + 9.5):
        f.disque(x, yo + 5.4, 2.6 if h == "joie" else 2.0, 1.4 if h == "joie" else 1.0, JOUE, dans=tete)
    if e.bouche or h == "joie":
        bouche(f, tx - 1.2, ty + 7.6, e, l=5.0, ligne=MARMOTTE[0])
    else:
        f.trait(tx - 3, ty + 6.4, tx + 0.6, ty + 6.4, MARMOTTE[0])
        f.px(tx - 2, ty + 7.4, BLANC); f.px(tx - 1, ty + 7.4, BLANC); f.px(tx - 2, ty + 8.4, BLANC); f.px(tx - 1, ty + 8.4, "#d9cfb8")
    f.oy = 0


# ---------------------------------------------------------------------------------------------------------------------
def _froisseuse(f, cx, cy, s, e, phase, grande):
    bat = (0, -3, 0, 3)[phase % 4] * s
    for cote in (-1, 1):
        pts = [(cx + cote * 2 * s, cy - 2 * s), (cx + cote * 26 * s, cy - 14 * s + bat), (cx + cote * 23 * s, cy - 3 * s + bat * 0.6),
               (cx + cote * 27 * s, cy + 6 * s + bat * 0.5), (cx + cote * 17 * s, cy + 3 * s), (cx + cote * 12.5 * s, cy + 9.5 * s),
               (cx + cote * 6 * s, cy + 4.5 * s)]
        # Le papier froissé : des facettes nettes, claires et sombres.
        aile = f.poly(pts, AILE, val=lambda x, y: 0.46 + 0.34 * math.sin(x * 0.83 + y * 0.47) * math.sin(y * 0.71 - x * 0.29)
                      - 0.1 * cote, trame=0.06)
        for (px_, py_) in (pts[1], pts[3], pts[5]):
            f.trait(cx + cote * 3 * s, cy, px_, py_, AILE[4 if cote < 0 else 3], dans=aile)
    for cote in (-1, 1):
        f.poly([(cx + cote * 1.6 * s, cy - 4 * s), (cx + cote * 5 * s, cy - 10.5 * s), (cx + cote * 5.4 * s, cy - 3 * s)], AILE,
               ton=2 if cote < 0 else 1)
    corps = f.boule(cx, cy + 1 * s, 5.6 * s, 6.4 * s, AILE, biais=0.46)
    yo = cy - 0.4 * s
    if grande:
        for cote, x in ((-1, cx - 2.6), (1, cx + 2.4)):
            oeil(f, x, yo, e, cote, rx=1.9, ry=2.2, iris=ENCRE, blanc=PECHE, cil=AILE[0], ri=0.6, arc=PECHE)
        if e.bouche:
            bouche(f, cx, yo + 4.4, e, l=4.0)
        else:
            f.trait(cx - 1.5, yo + 4, cx + 1, yo + 4, AILE[0])
        f.px(cx - 1.5, yo + 5, BLANC); f.px(cx + 0.5, yo + 5, BLANC)                       # deux petits crocs
    else:
        f.px(cx - 2 * s, yo, PECHE); f.px(cx + 1.4 * s, yo, PECHE)


@perso("petit-nuage", "froisseuses", "Les Froisseuses", (),
       "chauves-souris du Trou-qui-Siffle, aux ailes froissées comme du papier", w=112, h=64, vol=44)
def froisseuses(f, e):
    f.oy = -1 if e.souffle else 0
    _froisseuse(f, 24, 20, 0.6, e, e.t + 1, False)
    _froisseuse(f, 90, 24, 0.68, e, e.t + 2, False)
    _froisseuse(f, 55, 38, 1.0, e, e.t, True)
    f.oy = 0


# ---------------------------------------------------------------------------------------------------------------------
@perso("petit-nuage", "enclumes", "Les Enclumes", ("colere",),
       "nuages d'orage, larges et plats dessus ; un éclair quand ils se fâchent", w=126, h=94, vol=30)
def enclumes(f, e):
    h = e.humeur
    f.oy = -1 if e.souffle else 0
    # Le second, derrière, plus sombre.
    f.disque(100, 22, 23, 6.5, ORAGE, ton=0)
    nuee(f, ((100, 30, 20, 8), (92, 38, 14, 10), (109, 39, 12, 9)), ORAGE, biais=0.3)
    # L'éclair, sous le ventre (une forme, pas une couleur) ; il change de dessin d'une image à l'autre.
    if h == "colere":
        z = e.t % 2
        pts = [(58, 58), (66, 58), (61 - z, 68), (66, 68), (55 + z * 2, 84), (58, 72), (53, 72)]
        ecl = f.poly(pts, OR, ton=1)
        f.trait(61, 60, 58, 70, "#ffffff", dans=ecl)
        f.poly([(84, 58), (88, 58), (85, 65), (88, 65), (82 + z, 74), (83, 67), (80, 67)], OR, ton=1)
    # Le grand : la table de l'enclume, le col, les bosses du ventre.
    table = f.disque(56, 17, 54, 9.5, ORAGE, ton=2)
    f.ourler(table, ORAGE[4], cotes=((0, -1),))
    f.disque(56, 21, 52, 5.5, ORAGE, ton=1, dans=table)
    corps = nuee(f, ((56, 28, 45, 11), (30, 42, 20, 15), (58, 39, 27, 18), (86, 43, 20, 14), (44, 55, 23, 11), (74, 56, 22, 10)),
                 ORAGE, biais=0.4)
    for pts in ([(24, 42), (28, 37), (35, 36)], [(72, 34), (79, 32), (86, 35)], [(48, 60), (57, 62), (66, 60)]):
        f.courbe(pts, ORAGE[1], dans=corps)
    yo = 41.0
    for cote, x in ((-1, 48), (1, 66)):
        oeil(f, x, yo, e, cote, rx=3.3, ry=3.6, iris=NUIT, pupille="#14161c", blanc=PECHE, cil="#14161c", ri=0.6, arc=PECHE)
        p = 3.4 if h == "colere" else 1.8                               # les sourcils, toujours froncés
        s = f.tube([(x - cote * 5.5, yo - 5.6 + p * 0.5, 1.4), (x + cote * 5.5, yo - 7.0 - p * 0.4, 1.6)], ORAGE, biais=0.05, gain=0.3)
    eb = Etat("colere" if h == "neutre" and not e.bouche else h, e.paup, e.bouche)
    bouche(f, 57, yo + 9.4, eb, l=10.0, ligne="#14161c", fond="#14161c")
    f.oy = 0


# ---------------------------------------------------------------------------------------------------------------------
@perso("petit-nuage", "bergeronnette", "La bergeronnette", (),
       "petit oiseau gris et blanc, calotte noire, longue queue qui hoche", w=60, h=44)
def bergeronnette(f, e):
    a, g = 26, 42
    up = -1 if e.souffle else 0
    hoche = (0, -2, 0, 2)[e.t % 4]
    # La longue queue, qui hoche sans arrêt.
    q = f.poly([(a + 9, g - 19), (a + 31, g - 27 + hoche), (a + 31.5, g - 24 + hoche), (a + 10, g - 14)], FER, ton=1)
    f.trait(a + 11, g - 15, a + 31, g - 24.5 + hoche, BLANC, dans=q)
    for x in (a - 1, a + 4):                                             # les pattes fines
        f.trait(x, g - 10, x - 1, g - 2, FER[2])
        f.trait(x - 3, g - 1, x + 1, g - 1, FER[2])
    f.oy = up
    corps = f.boule(a + 2, g - 17, 11.4, 8.2, PLUME)
    f.boule(a, g - 13.6, 8.6, 5.2, PLUME, biais=0.8, gain=0.3, dans=corps)                   # le ventre blanc
    aile = f.boule(a + 5.5, g - 18.5, 8.2, 5.0, PLUME, biais=0.2)
    f.trait(a + 1, g - 17.5, a + 12, g - 16, BLANC, dans=aile); f.trait(a + 2, g - 20, a + 11, g - 19.4, PLUME[3], dans=aile)
    f.trait(a + 4, g - 15.6, a + 13, g - 14.2, FER[1], dans=aile)
    tete = f.boule(a - 8.6, g - 27, 6.6, 6.2, PLUME, biais=0.78, gain=0.34)                   # la joue blanche
    f.boule(a - 8.6, g - 27, 6.6, 6.2, FER, biais=0.5, cond=lambda x, y, u, v: y < g - 29.4 or x > a - 4.6)   # calotte et nuque
    f.disque(a - 9.4, g - 21.4, 4.4, 2.2, FER, ton=1)                                        # la bavette noire
    f.poly([(a - 14.6, g - 28), (a - 21, g - 26.8), (a - 14.6, g - 25.8)], FER, ton=1)        # le bec
    if e.bouche:
        f.poly([(a - 14.6, g - 25.8), (a - 19.6, g - 25.6 + e.bouche * 0.7), (a - 14.6, g - 24.6)], FER, ton=0)
    ex, ey = a - 10.6, g - 27.4
    if e.paup == 2:
        f.trait(ex - 1, ey, ex + 1, ey, FER[1])
    else:
        f.px(ex, ey, ENCRE); f.px(ex - 1, ey, ENCRE); f.px(ex, ey - 1, ENCRE) if e.paup == 0 else None
        f.px(ex - 1, ey - 1, "#ffffff") if e.paup == 0 else None
    f.oy = 0
