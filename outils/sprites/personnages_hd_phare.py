"""« Le phare éteint » en haute définition : les six adultes du village, à la suite de Lison (personnages_hd.py).

Même famille que Lison (personnage de livre d'images), mais quatre têtes et demie de haut. La toise de la campagne
(hauteur en unités, Pilou : corps de 62) : Tudal 123, Anselme 117, M. Vernier 117, Perrine 113, Odile 109, Basile 99,
Lison 76. Tous regardent un peu vers la gauche (vers Pilou) ; la lumière vient d'en haut à gauche.
"""
import math

from pinceau_hd import Rampe
from personnages_hd import (perso, Etat, oeil, sourcil, bouche, goutte, _main, ENCRE, BLANC, JOUE, BOIS, PEAU, CREME,
                            BOTTE, ARDOISE)

MARINE = Rampe("#0e1a36", "#13254a", "#1d3766", "#2e4f86", "#5a7ab0")
BARBE = Rampe("#8f9db0", "#b8c4d2", "#e6ecf2", "#ffffff", cerne="#4a5568")
LAITON = Rampe("#8a6a1c", "#b8922a", "#e8c447", "#fff0a0")
ORANGE = Rampe("#8a4410", "#c46a24", "#ff9a3c", "#ffc27a", "#ffe6c0")
VIO = Rampe("#2e2450", "#4a3a7e", "#6a5acd", "#9b8cff", "#c9c0ff")
BLEU = Rampe("#1f4f8a", "#2f6fc0", "#4a8fdc", "#8fc0f0", "#d6ecff")
GRIS = Rampe("#3a3f4b", "#5a6070", "#8890a0", "#b8bfcc", "#e2e6ee")
ARGENT = Rampe("#6c7384", "#9aa2b2", "#c6ccd8", "#e6eaf0", cerne="#3a3f4b")
CHATAIN = Rampe("#4a2e1a", "#6e4526", "#8a5a33", "#b8844f")
BRUN = Rampe("#3a2a1c", "#5a4a32", "#7c6848", "#a08a62")
CUIR = Rampe("#14161c", "#262a34", "#444a58")
TABLIER = Rampe("#c9b890", "#f6ead2", "#fffaf0", cerne="#5a5244")
CHEMISE = Rampe("#b9b4c0", "#e6e2ea", "#fbf8f0", cerne="#4a4658")
PAPIER = Rampe("#b9ad92", "#d9cfb8", "#f6f1e4", "#fffdf6", cerne="#5a5244")
HALE = Rampe("#a86a48", "#c98d66", "#e3ac82", "#f2c9a0", cerne="#4a2a1c")
VIEUX = Rampe("#b87f5c", "#d9a37a", "#e8b892", "#f6d2b0", cerne="#5a3324")
LIGNE = "#a9b4c8"


# ---------------------------------------------------------------------------------------------------------------------
# Le corps commun : jambes, manteau, bras, tête, visage
# ---------------------------------------------------------------------------------------------------------------------
def jambes(f, a, g, haut=44, ecart=4.8, r=3.1, pantalon=ARDOISE, chaussure=CUIR, botte=0):
    for x in (a + ecart, a - ecart):
        f.tube([(x, g - haut, r + 0.5), (x - 0.2, g - 6, r - 0.3)], pantalon)
        if botte:
            b = f.tube([(x, g - botte, r + 0.9), (x - 0.2, g - 5, r + 0.4)], chaussure)
            f.trait(x - r - 1, g - botte, x + r + 1, g - botte, chaussure[len(chaussure) - 1], dans=b)
        s = f.boule(x - 1.9, g - 2.7, 5.2, 2.7, chaussure, biais=0.42)
        f.ourler(s, chaussure[0], cotes=((0, 1),))
        f.px(x - 4.5, g - 4.2, chaussure[len(chaussure) - 1])


def manteau(f, a, g, up, tissu, epaule=84, carrure=11.0, ourlet=40, evase=12.5, ventre=0.0):
    pts = [(a - carrure, g - epaule + up), (a + carrure, g - epaule + up), (a + carrure + 0.8 + ventre, g - epaule + 14 + up),
           (a + evase, g - ourlet - 2), (a + evase - 0.4, g - ourlet), (a - evase + 0.4, g - ourlet), (a - evase, g - ourlet - 2),
           (a - carrure - 0.8 - ventre, g - epaule + 14 + up)]
    s = f.poly(pts, tissu, rond=0.92, gain=0.56, biais=0.36, trame=0.12)
    f.ourler(s, tissu[0], cotes=((0, 1),))
    return s


def epaules(a, g, epaule, carrure):
    return (a - carrure + 0.6, g - epaule + 2.6), (a + carrure - 0.6, g - epaule + 2.6)


def bras_bas(a, g, epaule, carrure, cote, long=27.0, r=3.6):
    """Un bras le long du corps : (points du bras, centre de la main)."""
    sx = a + cote * (carrure - 0.6)
    y = g - epaule + 2.6
    return ([(sx, y, r), (sx + cote * 3.6, y + long * 0.45, r - 0.3), (sx + cote * 4.6, y + long * 0.86, r - 0.6)],
            (sx + cote * 5.0, y + long))


def poser_bras(f, bras, main, cote, tissu, peau=PEAU, sombre=False, r_main=2.8, pouce=True, ouverte=False):
    s = f.tube(bras, tissu, biais=0.24 if sombre else 0.38, gain=0.56, trame=0.12)
    f.ourler(s, tissu[0], cotes=((-cote, 0), (0, 1), (0, -1)), dehors=False)
    if main is not None:
        m = f.boule(main[0], main[1], r_main, r_main * 1.08, peau, biais=0.45)
        if ouverte:
            for dx in (-1.6, -0.2, 1.2):
                f.px(main[0] + dx, main[1] - r_main - 0.6, peau[2], peau.cerne)
        if pouce:
            f.px(main[0] - cote * (r_main + 0.2), main[1] - 0.4, peau[2], peau.cerne)
        f.px(main[0] + cote * 0.4, main[1] + r_main * 0.55, peau[0])
    return s


def tete(f, tx, ty, rx=9.3, ry=10.3, peau=PEAU, oreilles=True, machoire=0.22):
    if oreilles:
        for cote in (-1, 1):
            f.boule(tx + cote * (rx + 0.1), ty + 1.8, 1.9, 2.6, peau, biais=0.3)
    return f.boule(tx, ty, rx, ry, peau, gain=0.42, biais=0.58,
                   cond=lambda x, y, u, v: abs(u) <= 1 - machoire * max(0.0, v) ** 2)


def cou(f, a, g, epaule, peau=PEAU, r=3.0):
    f.tube([(a - 0.3, g - epaule - 5, r), (a - 0.3, g - epaule + 0.5, r)], peau, biais=0.2)


def visage(f, e, tx, ty, peau=PEAU, iris="#4a3a2a", pupille=ENCRE, cil="#3a2a20", brun="#4a2e1a", ep=1, l=4.4, rx=2.3,
           ry=2.7, levres="#6a2a3a", nez=True, bouche_y=6.6, bouche_l=4.8, neutre="neutre", dans=None, joues=False,
           sourcils=True):
    """Yeux, sourcils, nez, bouche d'un adulte, un peu tournés vers la gauche. Renvoie la hauteur des yeux."""
    h = e.humeur
    yo = ty + 1.2
    for cote, x in ((-1, tx - 4.6), (1, tx + 3.8)):
        oeil(f, x, yo, e, cote, rx=rx, ry=ry, iris=iris, pupille=pupille, cil=cil, regard=(-0.3, 0), arc=cil)
        if sourcils:
            sourcil(f, x, yo - 5.4, e, cote, l=l, c=brun, ep=ep)
    if nez:
        f.px(tx - 1.6, yo + 2.6, peau[1]); f.px(tx - 1.6, yo + 3.6, peau[0]); f.px(tx - 0.6, yo + 4.0, peau[0])
    if joues or h in ("joie", "tendre", "malice"):
        for x in (tx - 6.4, tx + 5.4):
            f.disque(x, yo + 4.8, 2.1, 1.2, JOUE, dans=dans)
    if bouche_y is not None:
        bouche(f, tx - 0.5, yo + bouche_y, Etat(neutre if h == "neutre" and not e.bouche else h, e.paup, e.bouche),
               l=bouche_l, ligne=levres)
    return yo


def anneau(f, cx, cy, r, c, k=None):
    pts = set()
    for i in range(48):
        ang = i * math.pi / 24
        pts.add((int(math.floor(cx + r * math.cos(ang))), int(math.floor(cy + r * math.sin(ang)))))
    for (x, y) in pts:
        f.px(x, y, c, k)


# ---------------------------------------------------------------------------------------------------------------------
@perso("phare-eteint", "anselme", "Anselme, le gardien", ("triste", "joie"),
       "gardien du phare depuis trente ans : barbe blanche, casquette marine à insigne de laiton, yeux pâles, voilés",
       w=64, h=122)
def anselme(f, e):
    a, g = 34, 120
    up = -1 if e.souffle else 0
    h = e.humeur
    ep, ca = 86, 12.2
    jambes(f, a, g, haut=40, pantalon=MARINE, chaussure=CUIR, botte=14)
    caban = manteau(f, a, g, up, MARINE, epaule=ep, carrure=ca, ourlet=34, evase=13.6, ventre=0.6)
    f.oy = up
    # Le caban : croisé, deux rangs de boutons de laiton, un grand col relevé.
    f.trait(a + 2.5, g - ep + 6, a + 1.5, g - 35, MARINE[0], dans=caban)
    f.trait(a + 1.5, g - ep + 8, a + 0.5, g - 37, MARINE[3], dans=caban)
    for k, y in enumerate((g - 74, g - 64, g - 54)):
        for x in (a - 4.5, a + 5.5):
            f.px(x, y, LAITON[3]); f.px(x + 1, y, LAITON[2]); f.px(x, y + 1, LAITON[2]); f.px(x + 1, y + 1, LAITON[0])
    for cote in (-1, 1):
        f.poly([(a + cote * 1.5, g - ep + 1), (a + cote * 9.5, g - ep - 0.5), (a + cote * 7.5, g - ep + 9)], MARINE,
               ton=3 if cote < 0 else 2)
        f.trait(a + cote * 1.5, g - ep + 1, a + cote * 7.5, g - ep + 9, MARINE[0])
        f.trait(a + cote * 12, g - 46, a + cote * 6, g - 46, MARINE[0], dans=caban)            # les poches
    f.trait(a - 12, g - 36, a - 2, g - 36, MARINE[3], dans=caban)
    f.courbe([(a - 6.5, g - 50), (a - 8, g - 43), (a - 9.5, g - 36)], MARINE[1], dans=caban)
    cou(f, a, g, ep, VIEUX)
    # Les bras ; à la main gauche, la lanterne de ronde, éteinte (elle se rallume quand il sourit).
    bd, md = bras_bas(a, g, ep, ca, 1)
    if h == "triste":                     # la lanterne retombe
        bg, mg = bras_bas(a, g, ep, ca, -1, long=25)
    else:                                 # son attitude : il la lève devant lui pour mieux voir (plus haut quand il sourit)
        haut = 6.0 if h == "joie" else 0.0
        bg = [(a - ca + 0.6, g - ep + 2.6, 3.6), (a - ca - 3.2, g - ep + 13, 3.3), (a - ca - 6.6, g - ep + 9.5 - haut, 3.0)]
        mg = (a - ca - 7.6, g - ep + 6 - haut)
    poser_bras(f, bd, md, 1, MARINE, VIEUX, sombre=True)
    lx, ly = mg[0] - 0.5, mg[1] + 4
    allumee = h == "joie"
    if allumee:
        f.disque(lx, ly + 7, 9.5, 9.5, ORANGE[3], densite=lambda x, y: 0.42 - 0.035 * math.hypot(x - lx, y - ly - 7), cerne="")
    f.trait(lx - 3, ly + 1, lx, ly - 2, LAITON[1]); f.trait(lx, ly - 2, lx + 3, ly + 1, LAITON[1])     # l'anse
    f.rect(lx - 3.5, ly + 1, 7, 2, LAITON, ton=2); f.px(lx - 3.5, ly + 1, LAITON[3])
    verre = f.rect(lx - 3, ly + 3, 6, 8, ORANGE if allumee else ARDOISE, ton=3 if allumee else 1)
    if allumee:
        f.disque(lx, ly + 7.5, 1.6, 2.6, "#fff6d8", dans=verre)
    else:
        f.px(lx - 2.5, ly + 4, ARDOISE[2]); f.px(lx - 2.5, ly + 5, ARDOISE[2])
    f.trait(lx - 4, ly + 3, lx - 4, ly + 10, LAITON[1]); f.trait(lx + 3, ly + 3, lx + 3, ly + 10, LAITON[0])
    f.rect(lx - 4.5, ly + 11, 9, 2, LAITON, ton=1); f.trait(lx - 4, ly + 11, lx + 2, ly + 11, LAITON[3])
    poser_bras(f, bg, mg, -1, MARINE, VIEUX)
    # La tête : la casquette, la barbe blanche, de gros sourcils blancs.
    tx, ty = a - 1.5 - (1.0 if h == "triste" else 0.0), g - 98.0 + (2.0 if h == "triste" else 0.0)   # la tête en avant
    for cote in (-1, 1):
        f.boule(tx + cote * 8.6, ty - 1.5, 2.6, 4.2, BARBE, biais=0.35)                      # les tempes blanches
    t = tete(f, tx, ty, peau=VIEUX)
    yo = visage(f, e, tx, ty, peau=VIEUX, iris="#9fb3c8", pupille="#6a7f96", cil="#4a3a34", sourcils=False,
                bouche_y=None)
    for cote, x in ((-1, tx - 4.6), (1, tx + 3.8)):
        p = {"triste": -1.6, "joie": -0.4}.get(h, 0.3)
        dy = -1.0 if h == "joie" else 0.0
        xi, xe = x - cote * 2.2, x + cote * 3.2
        f.tube([(xi, yo - 5.2 + dy + p * 0.6, 1.5), (xe, yo - 5.6 + dy - p * 0.5, 1.2)], BARBE, biais=0.5)
        f.px(xe + cote * 1.2, yo - 5.8 + dy - p * 0.5, BARBE[2])
    barbe = f.boule(tx, ty + 6.8, 9.6, 8.6, BARBE, biais=0.46, cond=lambda x, y, u, v: y > ty + 3.2 + 1.8 * abs(u) ** 2 * -1)
    for pts in ([(tx - 5, ty + 8), (tx - 4, ty + 12), (tx - 2, ty + 14.5)], [(tx + 2, ty + 9), (tx + 2.5, ty + 12.5), (tx + 1, ty + 15)],
                [(tx + 6, ty + 6), (tx + 6, ty + 10), (tx + 4, ty + 13)]):
        f.courbe(pts, BARBE[1], dans=barbe)
    f.boule(tx - 3.2, ty + 5.0, 3.4, 1.7, BARBE, biais=0.6); f.boule(tx + 2.4, ty + 5.0, 3.4, 1.7, BARBE, biais=0.5)   # la moustache
    if e.bouche:
        bouche(f, tx - 0.4, ty + 7.6, e, l=4.4)
    elif h == "joie":
        f.courbe([(tx - 2.6, ty + 7), (tx - 0.4, ty + 8.2), (tx + 1.8, ty + 7)], BARBE[0])
    elif h == "triste":
        goutte(f, tx - 7.2, yo + 4.6, 1.1)
    calotte = f.boule(tx + 0.5, ty - 10.4, 10.6, 6.0, MARINE, biais=0.42, cond=lambda x, y, u, v: y < ty - 8.2)
    bandeau = f.rect(tx - 9.6, ty - 9.2, 19.6, 3.0, MARINE, ton=0)
    f.trait(tx - 9, ty - 9.2, tx + 9, ty - 9.2, MARINE[2])
    vis = f.poly([(tx - 12.5, ty - 5.2), (tx - 9.6, ty - 6.6), (tx + 5, ty - 6.6), (tx + 4, ty - 5.2)], CUIR, ton=0)
    f.trait(tx - 11, ty - 6.4, tx + 3, ty - 6.4, CUIR[2])
    for (dx, dy, c) in ((-2, -7, LAITON[2]), (-1, -8, LAITON[3]), (-1, -7, LAITON[2]), (0, -7, LAITON[1]), (-1, -6, LAITON[0])):
        f.px(tx + dx, ty + dy - 1.2, c)                                                      # l'insigne
    f.ox = f.oy = 0


# ---------------------------------------------------------------------------------------------------------------------
@perso("phare-eteint", "tudal", "Tudal", ("colere",),
       "pêcheur : bonnet de laine orange, barbe de trois jours, gros pull marine à côtes", w=68, h=124)
def tudal(f, e):
    a, g = 34, 122
    up = -1 if e.souffle else 0
    h = e.humeur
    ep, ca = 88, 14.0
    jambes(f, a, g, haut=46, ecart=5.4, r=3.5, pantalon=BRUN, chaussure=CUIR, botte=22)
    pull = manteau(f, a, g, up, MARINE, epaule=ep, carrure=ca, ourlet=44, evase=13.2, ventre=0.4)
    for x in range(int(a - 13), int(a + 14), 3):                                             # les côtes du tricot
        f.trait(x, g - ep + 4 + up, x, g - 49, MARINE[1] if x < a + 3 else MARINE[0], dans=pull)
    for x in range(int(a - 13), int(a + 14), 2):                                             # le bord-côte
        f.trait(x, g - 48, x, g - 45, MARINE[3] if x < a else MARINE[2], dans=pull)
    f.trait(a - 13, g - 49, a + 13, g - 49, MARINE[0], dans=pull)
    f.oy = up
    cou(f, a, g, ep, HALE, r=3.4)
    col = f.boule(a - 0.3, g - ep + 0.4, 6.6, 2.8, MARINE, biais=0.44)                        # le col roulé
    for x in range(int(a - 6), int(a + 6), 2):
        f.trait(x, g - ep - 1, x, g - ep + 2, MARINE[1], dans=col)
    # Les bras : pendants, poings fermés ; croisés quand il se fâche.
    if h != "colere":                     # son attitude : les bras croisés, boudeur
        bd = [(a + ca - 0.6, g - ep + 2.6, 4.0), (a + ca + 2.4, g - ep + 13, 3.8), (a - 3, g - ep + 16.5, 3.4)]
        bg = [(a - ca + 0.6, g - ep + 2.6, 4.0), (a - ca - 2.4, g - ep + 14, 3.8), (a + 4, g - ep + 19.5, 3.4)]
        s = poser_bras(f, bd, (a - 6.4, g - ep + 16.2), 1, MARINE, HALE, sombre=True, pouce=False)
        s = poser_bras(f, bg, (a + 7.4, g - ep + 19.6), -1, MARINE, HALE, pouce=False)
    else:                                 # en colère : penché en avant, un poing levé, l'autre sur la hanche
        f.ox = -1
        bd = [(a + ca - 0.6, g - ep + 2.6, 4.0), (a + ca + 5.4, g - ep + 9, 3.8), (a + ca + 7.4, g - ep - 1.5, 3.4)]
        md = (a + ca + 7.8, g - ep - 6.4 - (e.t % 2))
        bg = [(a - ca + 0.6, g - ep + 2.6, 4.0), (a - ca - 5.4, g - ep + 13, 3.8), (a - ca + 0.6, g - ep + 22.5, 3.4)]
        mg = (a - ca + 3.0, g - ep + 25)
        for bras, main, cote in ((bd, md, 1), (bg, mg, -1)):
            s = poser_bras(f, bras, main, cote, MARINE, HALE, sombre=cote > 0, r_main=3.1)
            f.trait(main[0] - 2, main[1] - 4.4, main[0] + 2, main[1] - 4.4, MARINE[3] if cote < 0 else MARINE[2], dans=s)
    # La tête : hâlée, le nez fort, la barbe de trois jours en trame.
    tx, ty = a - 0.5 - (1.5 if h == "colere" else 0.0), g - 101.0 + (1.0 if h == "colere" else 0.0)
    t = tete(f, tx, ty, rx=9.8, ry=10.4, peau=HALE, machoire=0.14)
    f.disque(tx, ty + 5.4, 8.6, 6.0, "#a07656", dans=t, densite=0.5,
             cond=lambda x, y, u, v: y > ty + 3.2 and not (abs(x - tx + 0.5) < 2.6 and y < ty + 8.6))
    yo = visage(f, e, tx, ty, peau=HALE, iris="#3a2a20", cil="#2a1a14", brun="#3a2416", ep=2, l=5.0, levres="#5a2a2a",
                nez=False, bouche_y=7.0, bouche_l=5.6, dans=t, neutre="colere")
    f.boule(tx - 0.9, yo + 3.2, 2.0, 2.3, HALE, biais=0.5)
    f.px(tx - 2.4, yo + 4.6, HALE[0]); f.px(tx + 0.6, yo + 4.6, HALE[0])
    # Le bonnet : laine tricotée, revers côtelé, pompon.
    pom = f.boule(tx + 1.5, ty - 18.0, 3.3, 3.1, ORANGE, biais=0.5, trame=0.4)
    bonnet = f.boule(tx, ty - 8.0, 10.6, 9.4, ORANGE, biais=0.42, trame=0.3, cond=lambda x, y, u, v: y < ty - 7.2)
    for k in range(-3, 4):                                                                    # les mailles
        f.courbe([(tx + k * 3.0, ty - 8), (tx + k * 2.6, ty - 12), (tx + k * 1.6, ty - 16)], ORANGE[1], dans=bonnet)
    rev = f.rect(tx - 10.8, ty - 9.6, 21.6, 4.6, ORANGE, rond=0.9, gain=0.6, biais=0.36)
    for x in range(int(tx - 10), int(tx + 11), 2):
        f.trait(x, ty - 9.6, x, ty - 5.2, ORANGE[1] if x > tx + 3 else ORANGE[3], dans=rev)
    f.ourler(rev, ORANGE[0], cotes=((0, 1),), dehors=False)
    f.ox = f.oy = 0


# ---------------------------------------------------------------------------------------------------------------------
@perso("phare-eteint", "perrine", "Perrine", ("joie",),
       "aubergiste du Bigorneau : chignon châtain, joues rondes, tablier crème, un torchon sur l'épaule", w=68, h=114)
def perrine(f, e):
    a, g = 34, 112
    up = -1 if e.souffle else 0
    h = e.humeur
    ep, ca = 80, 11.4
    for x in (a + 5, a - 5):
        f.boule(x - 1.4, g - 2.2, 4.4, 2.2, CUIR, biais=0.45)
    robe = f.poly([(a - ca, g - ep + up), (a + ca, g - ep + up), (a + ca + 1.4, g - ep + 14 + up), (a + 9.5, g - 50),
                   (a + 16.2, g - 7), (a + 14.5, g - 4), (a - 14.5, g - 4), (a - 16.2, g - 7), (a - 9.5, g - 50),
                   (a - ca - 1.4, g - ep + 14 + up)], VIO, rond=0.92, gain=0.56, biais=0.36, trame=0.12)
    f.ourler(robe, VIO[0], cotes=((0, 1),))
    f.courbe([(a + 10.5, g - 46), (a + 12.5, g - 28), (a + 14.8, g - 8)], VIO[0], dans=robe)
    f.courbe([(a - 10.5, g - 46), (a - 12.5, g - 28), (a - 14.6, g - 8)], VIO[3], dans=robe)
    # Le tablier crème : bavette, ceinture nouée, une grande poche, un feston en bas.
    tab = f.poly([(a - 5.5, g - ep + 9 + up), (a + 5.5, g - ep + 9 + up), (a + 6.5, g - 52), (a + 11.5, g - 12), (a - 11.5, g - 12),
                  (a - 6.5, g - 52)], TABLIER, rond=0.7, gain=0.5, biais=0.5, trame=0.1)
    f.ourler(tab, TABLIER[0], cotes=((0, 1),), dehors=False)
    for x in range(int(a - 10), int(a + 11), 3):
        f.px(x, g - 14, TABLIER[0])
    f.trait(a - 9, g - 52, a + 8, g - 52, TABLIER[0], dans=tab); f.trait(a - 9, g - 53, a + 8, g - 53, TABLIER[2], dans=tab)
    f.trait(a - 5, g - 36, a + 4, g - 36, TABLIER[0], dans=tab); f.trait(a - 5, g - 36, a - 5, g - 27, TABLIER[0], dans=tab)
    f.trait(a + 4, g - 36, a + 4, g - 27, TABLIER[0], dans=tab); f.trait(a - 5, g - 27, a + 4, g - 27, TABLIER[0], dans=tab)
    f.oy = up
    for cote in (-1, 1):                                                                       # les bretelles
        f.trait(a + cote * 5, g - ep + 9, a + cote * 6.5, g - ep + 0.5, TABLIER[1 if cote < 0 else 0])
    cou(f, a, g, ep)
    # Le torchon, sur l'épaule : blanc à liseré bleu.
    tor = f.poly([(a + 6, g - ep - 1.5), (a + 12, g - ep - 0.5), (a + 13, g - ep + 15), (a + 7.5, g - ep + 16)], CHEMISE, rond=0.6)
    f.trait(a + 7.5, g - ep + 13, a + 12.5, g - ep + 12.4, BLEU[2], dans=tor); f.trait(a + 7.5, g - ep + 11, a + 12.5, g - ep + 10.4, BLEU[3], dans=tor)
    # Les bras : manches retroussées, mains jointes sur le tablier ; grands ouverts quand elle rit.
    if h == "joie":
        bd = [(a + ca - 0.6, g - ep + 2.6, 3.6), (a + ca + 6, g - ep + 7, 3.3), (a + ca + 10.5, g - ep - 1, 3.0)]
        bg = [(a - ca + 0.6, g - ep + 2.6, 3.6), (a - ca - 6, g - ep + 7, 3.3), (a - ca - 10.5, g - ep - 1, 3.0)]
        md, mg = (a + ca + 11.6, g - ep - 5), (a - ca - 11.6, g - ep - 5)
    else:
        bd = [(a + ca - 0.6, g - ep + 2.6, 3.6), (a + ca + 2.6, g - ep + 14, 3.3), (a + 5.5, g - ep + 24, 3.0)]
        bg = [(a - ca + 0.6, g - ep + 2.6, 3.6), (a - ca - 2.6, g - ep + 14, 3.3), (a - 5.5, g - ep + 24, 3.0)]
        md, mg = (a + 2.6, g - ep + 25.6), (a - 2.8, g - ep + 25.2)
    for bras, main, cote in ((bd, md, 1), (bg, mg, -1)):
        s = poser_bras(f, bras[:2], None, cote, VIO, sombre=cote > 0)
        f.tube(bras[1:], PEAU, biais=0.3 if cote > 0 else 0.42)                                # l'avant-bras nu
        f.trait(bras[1][0] - 3, bras[1][1], bras[1][0] + 3, bras[1][1], VIO[4] if cote < 0 else VIO[3])
        _main(f, main[0], main[1], cote, r=2.8, ouverte=(h == "joie"))
    # La tête : ronde, les joues pleines, un chignon haut.
    tx, ty = a - 0.5, g - 93.0 - (1.0 if h == "joie" else 0.0)
    f.boule(tx + 0.5, ty - 13.2, 5.4, 4.8, CHATAIN, biais=0.42)
    f.courbe([(tx - 3, ty - 14), (tx + 0.5, ty - 16), (tx + 4, ty - 14.5)], CHATAIN[3])
    f.boule(tx, ty - 1.2, 10.6, 10.6, CHATAIN, biais=0.28)
    t = tete(f, tx, ty, rx=9.9, ry=10.0, machoire=0.08)
    raie = tx + 0.5
    chev = f.boule(tx, ty - 1.6, 10.4, 10.2, CHATAIN, biais=0.44,
                   cond=lambda x, y, u, v: y < ty - 7.2 + 5.2 * abs((x - raie) / 10.5) ** 1.6)
    f.ourler(chev, CHATAIN[0], cotes=((0, 1),), dehors=False)
    f.trait(raie, ty - 11, raie, ty - 7.4, CHATAIN[0], dans=chev)
    f.courbe([(raie - 2, ty - 10), (tx - 6, ty - 8), (tx - 9, ty - 4)], CHATAIN[3], dans=chev)
    visage(f, e, tx, ty, iris="#5a3a22", brun="#4a2e1a", bouche_y=6.4, bouche_l=5.4, neutre="tendre", dans=t, joues=True)
    f.ox = f.oy = 0


# ---------------------------------------------------------------------------------------------------------------------
@perso("phare-eteint", "odile", "Odile, la maire", ("triste",),
       "la maire : cheveux gris au carré, lunettes rondes, écharpe bleue en travers, un dossier sous le bras",
       w=62, h=112)
def odile(f, e):
    a, g = 31, 110
    up = -1 if e.souffle else 0
    h = e.humeur
    ep, ca = 82, 10.6
    jambes(f, a, g, haut=30, ecart=4.2, r=2.6, pantalon=ARDOISE, chaussure=CUIR)
    mant = manteau(f, a, g, up, GRIS, epaule=ep, carrure=ca, ourlet=24, evase=12.4)
    f.trait(a + 0.5, g - ep + 9 + up, a + 0.5, g - 25, GRIS[0], dans=mant)
    for y in (g - 62, g - 52, g - 42):
        f.px(a - 1.5, y, GRIS[4]); f.px(a - 1.5, y + 1, GRIS[0])
    f.trait(a - 12, g - 26, a - 2, g - 26, GRIS[3], dans=mant)
    f.oy = up
    for cote in (-1, 1):                                                                       # le col
        f.poly([(a + cote * 1, g - ep + 1), (a + cote * 7.5, g - ep), (a + cote * 5.5, g - ep + 10)], GRIS, ton=3 if cote < 0 else 2)
        f.trait(a + cote * 1, g - ep + 1, a + cote * 5.5, g - ep + 10, GRIS[0])
    # L'écharpe bleue, en travers, et ses franges sur la hanche.
    ech = f.poly([(a - ca - 0.5, g - ep + 1), (a - ca + 5.5, g - ep - 0.5), (a + 11.5, g - 50), (a + 9, g - 44.5)], BLEU, rond=0.5,
                 gain=0.5, biais=0.46, dans=mant | f.pleins())
    f.ourler(ech, BLEU[0], cotes=((0, 1),), dehors=False)
    f.trait(a - ca + 3, g - ep + 1, a + 10.5, g - 49.5, BLEU[4], dans=ech)
    for k in range(4):
        f.trait(a + 8.5 + k * 1.2, g - 44, a + 8 + k * 1.2, g - 39, BLEU[2 if k % 2 else 1])
    cou(f, a, g, ep)
    # Le bras droit serre un dossier ; le gauche pend.
    bg, mg = bras_bas(a, g, ep, ca, -1, long=25)
    poser_bras(f, bg, mg, -1, GRIS)
    dos = f.poly([(a + 6, g - ep + 13), (a + 16, g - ep + 12), (a + 17, g - ep + 27), (a + 7, g - ep + 28)], PAPIER, rond=0.3)
    f.trait(a + 6, g - ep + 13, a + 15, g - ep + 12, PAPIER[3]); f.trait(a + 8, g - ep + 17, a + 14, g - ep + 16.6, ORANGE[2])
    for k in range(2):
        f.trait(a + 8, g - ep + 20 + k * 3, a + 15, g - ep + 19.6 + k * 3, LIGNE)
    bd = [(a + ca - 0.6, g - ep + 2.6, 3.4), (a + ca + 4.6, g - ep + 13, 3.2), (a + ca + 2.5, g - ep + 22, 2.9)]
    poser_bras(f, bd, (a + ca + 0.4, g - ep + 24.6), 1, GRIS, sombre=True)
    # La tête : le carré gris, la frange droite, les lunettes rondes.
    tx, ty = a - 0.5 - (1.0 if h == "triste" else 0.0), g - 95.0 + (2.0 if h == "triste" else 0.0)
    f.boule(tx, ty - 0.6, 10.6, 11.0, ARGENT, biais=0.3, cond=lambda x, y, u, v: y < ty + 7.4)
    t = tete(f, tx, ty, oreilles=False)
    chev = f.boule(tx, ty - 1.4, 10.4, 10.6, ARGENT, biais=0.46,
                   cond=lambda x, y, u, v: y < ty - 5.6 + 1.2 * abs((x - tx) / 9.0) or (abs(x - tx) > 8.6 and y < ty + 6.6))
    f.ourler(chev, ARGENT[0], cotes=((0, 1),), dehors=False)
    for pts in ([(tx - 4, ty - 10), (tx - 6.5, ty - 7), (tx - 8.5, ty - 3)], [(tx + 3, ty - 10), (tx + 6, ty - 8), (tx + 8.6, ty - 2)]):
        f.courbe(pts, ARGENT[3] if pts[1][0] < tx else ARGENT[1], dans=chev)
    yo = visage(f, e, tx, ty, iris="#4a5a6e", brun="#6c7384", bouche_y=6.6, bouche_l=4.4, levres="#6a3a4a", dans=t)
    for x in (tx - 4.6, tx + 3.8):
        anneau(f, x + 0.5, yo + 0.5, 3.7, GRIS[0])
        f.px(x - 1.6, yo - 1.8, "#ffffff")
    f.trait(tx - 0.6, yo, tx + 0.2, yo, GRIS[0])
    if h == "triste":
        goutte(f, tx - 7.4, yo + 5.4, 1.1)
    f.ox = f.oy = 0


# ---------------------------------------------------------------------------------------------------------------------
@perso("phare-eteint", "basile", "Basile, l'horloger", ("peur", "triste"),
       "horloger-mécanicien : crâne lisse, couronne de cheveux, loupe vissée à l'œil, moustache, montre à gousset",
       w=66, h=106)
def basile(f, e):
    a, g = 33, 104
    up = -1 if e.souffle else 0
    h = e.humeur
    ep, ca = 74, 11.6
    jambes(f, a, g, haut=38, ecart=5.0, r=3.2, pantalon=GRIS, chaussure=CUIR)
    chem = manteau(f, a, g, up, CHEMISE, epaule=ep, carrure=ca, ourlet=37, evase=12.6, ventre=1.6)
    # Le gilet brun, ouvert sur la chemise ; la chaîne et la montre à gousset.
    for cote in (-1, 1):
        gil = f.poly([(a + cote * 3.5, g - ep + 2 + up), (a + cote * (ca - 0.5), g - ep + 1 + up), (a + cote * (ca + 2.2), g - ep + 15 + up),
                      (a + cote * 12.4, g - 40), (a + cote * 6, g - 38), (a + cote * 1.2, g - 43), (a + cote * 1.2, g - ep + 12 + up)],
                     BOIS, rond=0.0, ton=3 if cote < 0 else 2, dans=chem)
        f.ourler(gil, BOIS[0], cotes=((-cote, 0), (0, 1)), dehors=False)
        f.trait(a + cote * 5, g - 50, a + cote * 10, g - 50, BOIS[0], dans=gil)                # la poche du gilet
    for y in (g - 58 + up, g - 52, g - 46):
        f.px(a - 0.5, y, LAITON[3]); f.px(a - 0.5, y + 1, LAITON[1])
    f.courbe([(a + 0.5, g - 52), (a + 4, g - 47.5), (a + 8, g - 49.5)], LAITON[2])
    f.px(a + 8, g - 49, LAITON[3]); f.px(a + 9, g - 49, LAITON[2]); f.px(a + 8, g - 48, LAITON[2]); f.px(a + 9, g - 48, LAITON[0])
    f.oy = up
    f.poly([(a - 3.5, g - ep + 1), (a + 3.5, g - ep + 1), (a, g - ep + 6)], ORANGE, ton=1)      # un petit nœud
    cou(f, a - 1.5, g, ep, r=3.2)
    # Les bras : manches de chemise retenues par des élastiques ; les mains levées quand il a peur.
    if h == "peur":
        bd = [(a + ca - 0.6, g - ep + 2.6, 3.5), (a + ca + 5, g - ep + 8, 3.2), (a + ca + 6.5, g - ep - 1, 2.9)]
        bg = [(a - ca + 0.6, g - ep + 2.6, 3.5), (a - ca - 5, g - ep + 8, 3.2), (a - ca - 6.5, g - ep - 1, 2.9)]
        md, mg = (a + ca + 7, g - ep - 5), (a - ca - 7, g - ep - 5)
    else:
        bd, md = bras_bas(a, g, ep, ca, 1, long=24, r=3.5)
        bg, mg = bras_bas(a, g, ep, ca, -1, long=24, r=3.5)
        if h == "neutre":                 # son attitude : une main qui règle la loupe
            bd = [(a + ca - 0.6, g - ep + 2.6, 3.5), (a + ca + 4.6, g - ep + 7, 3.2), (a + ca + 1.6, g - ep - 3.5, 2.9)]
            md = (a + ca - 0.2, g - ep - 7.4)
    for bras, main, cote in ((bd, md, 1), (bg, mg, -1)):
        s = poser_bras(f, bras, main, cote, CHEMISE, sombre=cote > 0, ouverte=(h == "peur"))
        f.trait(bras[1][0] - 3, bras[1][1] - 1, bras[1][0] + 3, bras[1][1] - 1, GRIS[1], dans=s)   # l'élastique
    # La tête : le crâne qui brille, la couronne de cheveux, la moustache, la loupe de laiton sur l'œil.
    tx, ty = a - 2.5, g - 85.5 + (2.0 if h == "triste" else 0.0)   # voûté : la tête en avant, rentrée dans les épaules
    for cote in (-1, 1):
        f.boule(tx + cote * 9.2, ty + 0.4, 3.2, 4.6, ARGENT, biais=0.4 if cote < 0 else 0.3)
    t = tete(f, tx, ty, rx=9.6, ry=10.4, machoire=0.12)
    f.courbe([(tx - 5.5, ty - 6.5), (tx - 3, ty - 8.6), (tx + 0.5, ty - 9.2)], PEAU[3], dans=t)
    f.px(tx - 6, ty - 5, PEAU[3])
    yo = visage(f, e, tx, ty, iris="#4a3a2a", brun="#6a5a48", bouche_y=None, dans=t)
    lx, ly = tx + 4.3, yo + 0.4                                                                  # la loupe
    anneau(f, lx, ly, 3.9, LAITON[1]); anneau(f, lx, ly, 3.0, LAITON[3])
    f.px(lx - 1.5, ly - 1.6, "#ffffff")
    f.trait(lx + 3.6, ly - 2.6, tx + 9.4, ty - 3.4, GRIS[0])                                     # la bride
    mous = f.boule(tx - 3.6, yo + 5.2, 3.8, 1.9, BRUN, biais=0.5)
    mous |= f.boule(tx + 2.6, yo + 5.2, 3.8, 1.9, BRUN, biais=0.4)
    f.px(tx - 7.6, yo + 4.4, BRUN[2]); f.px(tx + 6.6, yo + 4.4, BRUN[1])
    if e.bouche or h != "neutre":
        bouche(f, tx - 0.5, yo + 8.2, e, l=4.4, ligne="#5a2a2a")
    if h == "peur":
        goutte(f, tx - 8.5, ty - 6.5, 1.3)
    if h == "triste":
        goutte(f, tx - 7.6, yo + 4.4, 1.1)
    f.ox = f.oy = 0


# ---------------------------------------------------------------------------------------------------------------------
@perso("phare-eteint", "vernier", "M. Vernier", (),
       "inspecteur du Service des Feux : chapeau de pluie et ciré jaunes, jumelles au cou, une écritoire", w=64, h=120)
def vernier(f, e):
    a, g = 33, 118
    up = -1 if e.souffle else 0
    ep, ca = 86, 11.4
    jambes(f, a, g, haut=34, ecart=4.6, r=2.9, pantalon=ARDOISE, chaussure=CUIR, botte=16)
    cire = manteau(f, a, g, up, BOTTE, epaule=ep, carrure=ca, ourlet=27, evase=13.4)
    f.trait(a + 0.5, g - ep + 8 + up, a + 0.5, g - 28, BOTTE[0], dans=cire)
    for y in (g - 72 + up, g - 62, g - 52, g - 42):
        f.px(a - 1.5, y, CUIR[1]); f.px(a - 1.5, y + 1, CUIR[0])
    for cote in (-1, 1):
        f.trait(a + cote * 5, g - 46, a + cote * 11, g - 46, BOTTE[0], dans=cire); f.trait(a + cote * 5, g - 47, a + cote * 11, g - 47, BOTTE[3], dans=cire)
    f.trait(a - 13, g - 29, a - 3, g - 29, BOTTE[4], dans=cire)
    for (x, y0, y1) in ((a - 8.5, g - 80, g - 74), (a - 10.5, g - 40, g - 33)):                 # le ciré luit
        f.trait(x, y0 + up, x, y1, BOTTE[4], dans=cire)
    f.oy = up
    for cote in (-1, 1):
        f.poly([(a + cote * 1, g - ep + 1), (a + cote * 7, g - ep), (a + cote * 5, g - ep + 8)], BOTTE, ton=3 if cote < 0 else 1)
    cou(f, a, g, ep, r=2.7)
    # Les jumelles, au bout de leur courroie.
    f.trait(a - 4.5, g - ep + 1, a - 3.5, g - ep + 12, CUIR[1]); f.trait(a + 3.5, g - ep + 1, a + 3.5, g - ep + 12, CUIR[0])
    for x in (a - 3.4, a + 3.4):
        j = f.tube([(x, g - ep + 12.5, 2.6), (x, g - ep + 18, 3.2)], GRIS, biais=0.3)
        f.px(x - 1.5, g - ep + 14, GRIS[4])
        f.trait(x - 2, g - ep + 20, x + 1, g - ep + 20, BLEU[3], dans=j)
    f.rect(a - 1, g - ep + 13.5, 2, 3, GRIS, ton=0)
    # Le bras gauche tient l'écritoire, le droit un crayon : il note tout.
    bd = [(a + ca - 0.6, g - ep + 2.6, 3.5), (a + ca + 3.6, g - ep + 14, 3.2), (a + 9, g - ep + 25, 2.9)]
    bg = [(a - ca + 0.6, g - ep + 2.6, 3.5), (a - ca - 3.6, g - ep + 14, 3.2), (a - 9.5, g - ep + 27, 2.9)]
    ecr = f.poly([(a - 12, g - ep + 22), (a + 2, g - ep + 23), (a + 1.5, g - ep + 38), (a - 12.5, g - ep + 37)], BOIS, rond=0.2)
    pap = f.poly([(a - 10.5, g - ep + 24.5), (a + 0.5, g - ep + 25.2), (a + 0.2, g - ep + 36), (a - 11, g - ep + 35.4)], PAPIER, ton=2)
    for k in range(3):
        f.trait(a - 9, g - ep + 28 + k * 2.4, a - 2 - k, g - ep + 28.3 + k * 2.4, LIGNE)
    f.rect(a - 7, g - ep + 22.5, 4, 2, GRIS, ton=3)
    poser_bras(f, bd, (a + 6.6, g - ep + 27), 1, BOTTE, sombre=True)
    f.trait(a + 4.5, g - ep + 30, a + 8, g - ep + 23, ORANGE[2]); f.px(a + 4, g - ep + 31, ENCRE)   # le crayon
    poser_bras(f, bg, (a - 11.5, g - ep + 30), -1, BOTTE)
    # La tête : longue, pincée, sous le chapeau de pluie.
    tx, ty = a - 0.5, g - 98.0
    t = tete(f, tx, ty, rx=8.6, ry=10.6, machoire=0.3)
    yo = visage(f, e, tx, ty, iris="#3a4658", brun="#5a6070", rx=1.8, ry=2.1, l=4.4, bouche_y=7.2, bouche_l=4.0, nez=False,
                levres="#5a3a3a", dans=t)
    f.trait(tx - 1.2, yo + 0.5, tx - 1.8, yo + 4.4, PEAU[0]); f.px(tx - 0.8, yo + 4.6, PEAU[0])    # le nez long
    arr = f.disque(tx + 1.5, ty - 4.6, 13.6, 3.8, BOTTE, ton=1)                                   # le bord, plus long derrière
    cal = f.boule(tx, ty - 9.4, 9.2, 7.2, BOTTE, biais=0.42, cond=lambda x, y, u, v: y < ty - 5.2)
    bord = f.disque(tx - 0.5, ty - 5.0, 12.4, 2.6, BOTTE, ton=2)
    f.trait(tx - 10, ty - 6.4, tx + 4, ty - 6.4, BOTTE[4], dans=bord)
    f.ourler(bord, BOTTE[0], cotes=((0, 1),))
    f.trait(tx - 8, ty - 7.6, tx + 8, ty - 7.6, BOTTE[0], dans=cal)
    f.courbe([(tx - 5.5, ty - 11), (tx - 3.5, ty - 14), (tx, ty - 15.4)], BOTTE[4], dans=cal)
    f.ox = f.oy = 0
