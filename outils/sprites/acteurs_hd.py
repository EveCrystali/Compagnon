"""Les acteurs de scène en haute définition (docs/SCENES-HD.md, § 7) : `acteur-<nom>`, à l'unité 480 × 240.

Les 29 acteurs d'acteurs_scenes.py (bêtes et effets), redessinés environ 2,5 fois plus fins — jamais agrandis — avec
les pinceaux de pinceau_hd.py. Pour que le moteur les anime sans rien changer : **même nombre d'images, même ordre,
même durée, même orientation** que l'acteur d'aujourd'hui (la libellule, la mouette et le poisson ont la tête à
droite, le chat à gauche). Ancre : le milieu du bas.

Les bêtes ont un cerne teinté ; les effets (brume, vapeur, ronds, éclats…) n'en ont pas, et tout ce qui est léger se
dit en trame, jamais en alpha. Jamais d'opposition rouge / vert : orange, prune, crème, sarcelle, bleu.
"""
import math

from pinceau_hd import Feuille, Rampe, seuil

ACTEURS = {}        # nom -> dict(w, h, n, duree, dessin, cerne)
ORDRE = []

ENCRE = "#1c2128"
ORANGE = Rampe("#8a4410", "#d9803a", "#f69d50", "#ffc89a", "#fff6cc")
PRUNE = Rampe("#3b2a3e", "#6e3d86", "#a46cc2", "#d6b8ec")
JAUNE = Rampe("#a8741a", "#f2bd3c", "#ffe08f")
NOIR = Rampe("#141a2e", "#232b48", "#3c4870", "#6a7aa8", cerne="#0a0d18")
BLANC = Rampe("#adbac7", "#d4dde6", "#f3f6fa", "#ffffff", cerne="#3b4654")
NUAGE = Rampe("#b4c2e0", "#dbe3f0", "#f7f5ef", "#ffffff", cerne="#6f7fa6")
PAPIER = Rampe("#b9a98a", "#d9c7a3", "#fbf3e4", "#ffffff", cerne="#5a4a40")
EAU = Rampe("#9fb8e8", "#cfe0ff", "#ffffff")
CREME = Rampe("#b9a98a", "#efe0c0", "#ffffff", cerne="#7a6a50")
NEON = Rampe("#1a8fb8", "#4fd8ff", "#e8fbff")
BRUME, VAPEUR, VENT = "#e3e9f4", "#eef2f8", "#c9d3e8"


def acteur(nom, w, h, n, duree, cerne=True):
    def poser(dessin):
        ACTEURS[nom] = dict(w=w, h=h, n=n, duree=duree, dessin=dessin, cerne=cerne)
        ORDRE.append(nom)
        return dessin
    return poser


def image(nom, i):
    a = ACTEURS[nom]
    f = Feuille(a["w"], a["h"])
    a["dessin"](f, i)
    f.ox = f.oy = 0
    if a["cerne"]:
        f.cerner()
    return f


def voile(f, dedans, boite, c, densite):
    """Une forme légère : en trame, sans cerne."""
    return f.forme(dedans, boite, c, densite=densite, cerne="")


# ---------------------------------------------------------------------------------------------------------------------
# Bêtes
# ---------------------------------------------------------------------------------------------------------------------
@acteur("libellule", 22, 14, 2, 50)
def libellule(f, i):
    haut = i == 0                                           # les ailes : en haut, puis en bas
    for x in (5.5, 11.5):
        y = 3.2 if haut else 10.6
        voile(f, lambda px, py, x=x, y=y: ((px - x) / 4.2) ** 2 + ((py - y) / 2.4) ** 2 <= 1, (x - 5, y - 3, x + 5, y + 3),
              "#e2d9ff", 0.62)
        f.trait(x - 3, y + (1.6 if haut else -1.6), x + 2, y + (-1.6 if haut else 1.6), "#ffffff", "")
    f.tube([(1.5, 7, 0.9), (13, 7, 1.2)], PRUNE)                # l'abdomen, annelé
    for x in (4, 7, 10):
        f.px(x, 7.4, PRUNE[0])
    f.boule(15.5, 7, 2.4, 2.0, PRUNE, biais=0.5)                # le thorax
    f.boule(18.6, 6.8, 2.0, 1.9, JAUNE, biais=0.5)              # la tête, un gros œil doré
    f.px(18.6, 6.4, ENCRE)


@acteur("papillon", 16, 13, 4, 120)
def papillon(f, i):
    ouv = (1.0, 0.55, 0.12, 0.55)[i]                        # ouvert, à demi, fermé, à demi
    for cote in (-1, 1):
        if ouv > 0.2:
            a = f.boule(8 + cote * 3.6 * ouv, 4.4, 3.6 * ouv, 3.4, ORANGE, biais=0.34, gain=0.5)
            f.boule(8 + cote * 2.8 * ouv, 8.6, 2.6 * ouv, 2.4, ORANGE, biais=0.24, gain=0.5)
            if ouv > 0.5:
                f.px(8 + cote * 4.2 * ouv - 0.5, 3.6, "#ffe1a0"); f.px(8 + cote * 5.2 * ouv - 0.5, 4.6, "#ffe1a0")
                f.px(8 + cote * 3 * ouv - 0.5, 8.6, ORANGE[0])
    f.tube([(7.5, 3.6, 0.8), (7.5, 10.4, 0.8)], PRUNE, biais=0.2)
    f.px(6, 1.6, PRUNE[0]); f.px(9, 1.6, PRUNE[0]); f.px(6.6, 2.4, PRUNE[0]); f.px(8.4, 2.4, PRUNE[0])


@acteur("oiseau", 15, 9, 4, 140, cerne=False)
def oiseau(f, i):
    dy = (-3.0, 0.0, 3.0, 0.0)[i]                           # un oiseau au loin : deux traits qui battent
    for cote in (-1, 1):
        f.courbe([(7, 4.6), (7 + cote * 3, 4.2 + dy * 0.5), (7 + cote * 6.4, 4.4 + dy)], "#4a3a6e", "")
        f.courbe([(7, 5.6), (7 + cote * 3, 5.2 + dy * 0.5), (7 + cote * 5.4, 5.4 + dy)], "#6a5a96", "")
    f.px(7, 5, "#4a3a6e", ""); f.px(7, 6, "#4a3a6e", "")


@acteur("abeille", 15, 11, 2, 60)
def abeille(f, i):
    for x in (6.5, 9.5):
        y = 2.6 if i == 0 else 3.4
        voile(f, lambda px, py, x=x, y=y: ((px - x) / (2.6 if i == 0 else 3.2)) ** 2 + ((py - y) / 2.2) ** 2 <= 1,
              (x - 4, y - 3, x + 4, y + 3), "#ffffff", 0.66)
    c = f.boule(7.4, 7, 5.0, 3.2, JAUNE, biais=0.46)
    for x in (5, 8):
        f.trait(x, 3, x, 10, "#2a2238", dans=c); f.trait(x + 1, 3, x + 1, 10, "#2a2238", dans=c)
    f.boule(11.8, 6.8, 2.1, 2.1, Rampe("#2a2238", "#4a3e60", "#6e6090"), biais=0.5)
    f.px(12.4, 6.2, "#ffffff"); f.px(1.4, 7, "#2a2238")


@acteur("graine", 13, 12, 2, 300, cerne=False)
def graine(f, i):
    for k in range(7):                                      # l'aigrette : sept soies qui s'ouvrent et se referment
        ang = math.radians(-160 + k * 23.3)
        r = 5.4 if i == 0 else 4.8
        x, y = 6 + r * math.cos(ang) * (1.0 if i == 0 else 1.12), 5.4 + r * math.sin(ang) * 0.86
        f.trait(6, 5.4, x, y, "#d9c9a0", ""); f.px(x, y, "#fff8e1", "")
    f.px(6, 5, "#fff8e1", "")
    f.trait(6, 6, 6, 8.4, "#d9c9a0", "")
    f.px(6, 9, "#8a6e4b", ""); f.px(6, 10, "#8a6e4b", ""); f.px(5, 9.6, "#6b5236", "")


@acteur("feuille", 11, 10, 4, 160)
def feuille(f, i):
    ang = (20, 65, 110, 155)[i]                             # elle tourne en tombant
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    def dedans(px, py):
        u, v = (px - 5.5) * c + (py - 5) * s, -(px - 5.5) * s + (py - 5) * c
        return (u / 4.2) ** 2 + (v / (2.3 * (1 - 0.5 * abs(u) / 4.2))) ** 2 <= 1
    b = f.forme(dedans, (0, 0, 11, 10), Rampe("#8a4a1f", "#d9803a", "#f2c46b", "#ffe6a8"),
                lambda px, py: 0.72 - 0.08 * (px - 5.5) - 0.1 * (py - 5))
    f.trait(5.5 - 3.4 * c, 5 - 3.4 * s, 5.5 + 4.6 * c, 5 + 4.6 * s, "#8a4a1f")


@acteur("poisson", 16, 11, 3, 233)
def poisson(f, i):
    pente = (-0.5, 0.0, 0.5)[i]                             # il monte, passe, replonge
    y = (6.4, 5.0, 4.6)[i]
    f.poly([(1, y - 3 - pente * 6), (5, y - pente * 3), (1, y + 3 - pente * 6)], ORANGE, ton=1)            # la queue
    c = f.tube([(4.5, y - pente * 3, 1.8), (9, y, 3.0), (13, y + pente * 3.4, 2.0)], ORANGE)
    f.boule(9, y + 1.4, 3.4, 1.4, ORANGE, biais=0.8, gain=0.3, dans=c)                                   # le ventre clair
    f.poly([(7, y - 2.6), (10, y - 4.8), (10.6, y - 2.4)], ORANGE, ton=1)                                  # la nageoire
    f.px(12.4, y + pente * 3 - 0.8, ENCRE); f.px(12.4, y + pente * 3 - 1.6, "#ffffff")


# ---------------------------------------------------------------------------------------------------------------------
# La Grande Panne
# ---------------------------------------------------------------------------------------------------------------------
@acteur("paquet", 15, 11, 4, 120, cerne=False)
def paquet(f, i):
    f.rect(0, 0, 14, 10, ENCRE)
    f.rect(1, 1, 12, 8, "#232b48")
    for r in range(2):                                      # les données clignotent, en damier
        for k in range(3):
            c = NEON[1] if (r + k + i) % 2 == 0 else NEON[2]
            f.rect(2 + k * 4, 2 + r * 3, 3, 2, c)
            f.px(2 + k * 4, 2 + r * 3, "#ffffff") if c == NEON[1] else None
    if i == 2:
        f.rect(12, 8, 2, 2, ORANGE[2])
    if i == 3:
        f.rect(0, 8, 2, 2, ORANGE[2])


@acteur("curseur", 14, 21, 2, 400, cerne=False)
def curseur(f, i):
    pts = [(1, 1), (1, 16), (4.6, 12.6), (7.4, 18.6), (9.8, 17.4), (7, 11.6), (12, 11.6)]
    noir = f.poly([(0, -1), (0, 18.4), (4.3, 14.4), (7, 20.2), (11.4, 18), (8.6, 12.6), (14, 12.6)], ENCRE)
    b = f.poly(pts, "#ffffff")
    f.trait(2, 4, 2, 13, "#dbe3f0", dans=b)


@acteur("ticket", 11, 11, 4, 160)
def ticket(f, i):
    l = (9, 6, 2, 6)[i]                                     # il tourne sur lui-même
    x0 = 5.5 - l / 2.0
    b = f.rect(x0, 1, l, 9, PAPIER, rond=0.5, gain=0.4, biais=0.56)
    if l > 2:
        f.trait(x0 + 1, 3, x0 + l - 2, 3, "#5a4a40", dans=b); f.trait(x0 + 1, 5, x0 + l - 3, 5, "#a9b4c8", dans=b)
        f.rect(x0 + l - 3, 6, 2, 2, ORANGE[2], dans=b)
        f.trait(x0, 9, x0 + l - 1, 9, PAPIER[0], dans=b)


@acteur("bulle-marais", 14, 14, 3, 200, cerne=False)
def bulle_marais(f, i):
    r = (2.6, 4.4, 6.2)[i]
    for k in range(40):                                     # elle gonfle ; à la fin son bord se défait en pointillés
        ang = k * math.pi / 20
        if i == 2 and k % 3 == 0:
            continue
        f.px(7 + r * math.cos(ang), 7 + r * math.sin(ang), "#a9c8ee", "")
    if i < 2:
        voile(f, lambda px, py: (px - 7) ** 2 + (py - 7) ** 2 <= (r - 1) ** 2, (0, 0, 14, 14), "#d6e6fa", 0.3)
    f.px(7 - r * 0.45, 7 - r * 0.45, "#ffffff", ""); f.px(7 - r * 0.45 + 1, 7 - r * 0.45 - 1, "#ffffff", "")


def _etoile(f, cx, cy, r, c, coeur, diag=False):
    for k in range(4):
        ang = k * math.pi / 2 + (math.pi / 4 if diag else 0)
        for d in range(1, int(r) + 1):
            f.px(cx + d * math.cos(ang) * (0.75 if diag else 1), cy + d * math.sin(ang) * (0.75 if diag else 1),
                 c if d > r * 0.5 else coeur, "")
    f.px(cx, cy, "#ffffff", "")


@acteur("etincelle", 13, 13, 3, 80, cerne=False)
def etincelle(f, i):
    if i == 0:
        _etoile(f, 6, 6, 5, ORANGE[2], ORANGE[4]); _etoile(f, 6, 6, 2, ORANGE[3], ORANGE[4], diag=True)
    elif i == 1:
        _etoile(f, 6, 6, 2, ORANGE[3], ORANGE[4])
    else:
        _etoile(f, 6, 6, 6, ORANGE[2], ORANGE[3], diag=True)


# ---------------------------------------------------------------------------------------------------------------------
# Le phare éteint
# ---------------------------------------------------------------------------------------------------------------------
@acteur("mouette", 26, 16, 4, 140)
def mouette(f, i):
    dy = (-5.0, -1.0, 4.0, -1.0)[i]                         # ailes hautes, à plat, basses, à plat
    for cote in (-1, 1):
        a = f.tube([(12.5 + cote * 2, 8.4, 2.0), (12.5 + cote * 6.5, 8.2 + dy * 0.6, 1.6), (12.5 + cote * 11.4, 8.4 + dy, 0.9)],
                   BLANC, biais=0.3 if cote > 0 else 0.42)
        f.px(12.5 + cote * 11.4, 8.4 + dy, "#3b4654"); f.px(12.5 + cote * 10.4, 8.2 + dy * 0.92, "#3b4654")   # le bout noir
    f.tube([(9.5, 9.6, 1.8), (15.4, 9.4, 2.4)], BLANC, biais=0.5)
    f.boule(17.6, 8.4, 2.3, 2.1, BLANC, biais=0.56)
    f.px(19.8, 8.6, ORANGE[2]); f.px(20.8, 8.8, ORANGE[1]); f.px(18.2, 7.8, ENCRE)
    f.px(8, 10, BLANC[0]); f.px(7, 10.4, BLANC[0])


@acteur("chat", 28, 23, 4, 260)
def chat(f, i):
    g = 21
    # La queue, qui bat : couchée, relevée, dressée, relevée.
    queue = ([(15, g - 3, 2.0), (21, g - 2.4, 1.7), (25.4, g - 3.4, 1.2)], [(15, g - 3, 2.0), (20, g - 4, 1.7), (22.6, g - 8, 1.2)],
             [(15, g - 3, 2.0), (20.4, g - 5, 1.7), (24, g - 10.6, 1.2)], [(15, g - 3, 2.0), (20, g - 4, 1.7), (22.6, g - 8, 1.2)])[i]
    f.tube(queue, NOIR, biais=0.3)
    f.boule(9.6, g - 5.4, 7.2, 6.4, NOIR, biais=0.36)           # le corps, assis
    f.boule(7, g - 2, 3.2, 2.0, NOIR, biais=0.4); f.boule(12.6, g - 2, 3.2, 2.0, NOIR, biais=0.3)
    for x in (4.4, 10.6):                                    # les oreilles
        f.poly([(x - 2, g - 15), (x + 0.4, g - 20.4), (x + 2.2, g - 15)], NOIR, ton=1)
        f.px(x, g - 17, "#6a4a66")
    t = f.boule(7.4, g - 13.4, 5.6, 4.8, NOIR, biais=0.42)
    f.courbe([(3.4, g - 16), (5.6, g - 17.6), (8.6, g - 17.8)], NOIR[3], dans=t)     # le liseré de lune : il se lit la nuit
    f.trait(3.4, g - 8, 3.4, g - 4, NOIR[3])
    if i == 3:                                               # il cligne
        f.trait(4.4, g - 13.4, 6.4, g - 13.4, "#f2a94e"); f.trait(8.6, g - 13.4, 10.6, g - 13.4, "#f2a94e")
    else:
        for x in (5.4, 9.6):
            f.rect(x - 1, g - 14.6, 2, 3, "#f2a94e"); f.px(x - 0.5, g - 14.6, "#ffe1a0"); f.px(x, g - 13.4, ENCRE)
    f.px(7, g - 11.4, "#c98d9a")
    f.px(2, g - 11.6, NOIR[3], ""); f.px(1, g - 12, NOIR[3], ""); f.px(13, g - 11.6, NOIR[3], ""); f.px(14, g - 12, NOIR[3], "")


@acteur("papillon-nuit", 10, 7, 2, 70, cerne=False)
def papillon_nuit(f, i):
    for cote in (-1, 1):
        if i == 0:
            f.poly([(5, 4), (5 + cote * 4.4, 0.4), (5 + cote * 3.4, 4.6)], "#ffe8bf", cerne="")
        else:
            f.poly([(5, 3.4), (5 + cote * 4.6, 3.6), (5 + cote * 3, 6.2)], "#ffe8bf", cerne="")
    f.px(4.5, 3, "#d9c9a0", ""); f.px(4.5, 4, "#d9c9a0", ""); f.px(4.5, 5, "#b9a98a", "")


@acteur("crabe", 20, 13, 2, 120)
def crabe(f, i):
    for cote in (-1, 1):
        for k in range(3):                                   # les pattes, un pas sur deux
            x = 10 + cote * (4.6 + k * 1.6)
            dy = 1 if (k + i) % 2 else 0
            f.trait(x, 8, x + cote * 1.6, 10.6 + dy, ORANGE[1]); f.px(x + cote * 1.6, 11 + dy, ORANGE[0])
        f.tube([(10 + cote * 5, 6.4, 1.0), (10 + cote * 7.6, 4.4 - i, 1.0)], ORANGE, biais=0.3)
        f.boule(10 + cote * 8, 3.2 - i, 2.0, 1.8, ORANGE, biais=0.5)                                    # la pince
        f.px(10 + cote * 8 + (0 if cote > 0 else -1), 2.4 - i, ORANGE[0])
        f.trait(10 + cote * 2 - (1 if cote < 0 else 0), 4.4, 10 + cote * 2 - (1 if cote < 0 else 0), 2.6, ORANGE[1])
        f.px(10 + cote * 2 - (1 if cote < 0 else 0), 1.8, ENCRE)                                         # les yeux, au bout
    c = f.boule(10, 7, 5.6, 3.4, ORANGE, biais=0.44)
    f.px(8, 5.6, ORANGE[4]); f.px(9, 5.2, ORANGE[4]); f.trait(8, 8.6, 11, 8.6, ORANGE[0], dans=c)


# ---------------------------------------------------------------------------------------------------------------------
# Petit Nuage : nuages, brume, vapeur, neige — tout le léger en trame
# ---------------------------------------------------------------------------------------------------------------------
@acteur("nuage", 52, 20, 4, 520)
def nuage(f, i):
    d = (0.0, 0.8, 1.2, 0.4)[i]                              # ses bosses respirent
    corps = set()
    for (x, y, rx, ry) in ((18 - d, 7, 8, 5.6), (30 + d, 6.4 - d * 0.4, 9, 6), (40, 9.4, 6.4 + d * 0.6, 4.6), (10, 10.6, 7, 4.4),
                           (26, 10.6, 20, 5.2)):
        corps |= f.boule(x, y, rx, ry, NUAGE, biais=0.56, gain=0.6)
    for x in range(8 + (i % 2), 46, 2):                     # la frange en damier, dessous
        f.px(x, 16.4, NUAGE[0], "")
        if x % 4 == 0:
            f.px(x + 1, 17.6, NUAGE[0], "")


@acteur("brume", 56, 14, 4, 600, cerne=False)
def brume(f, i):
    def dens(px, py):
        u, v = (px - 28) / 28.0, (py - 7) / 7.0
        d = u * u + v * v
        return 0.0 if d > 1 else (0.62 if d < 0.4 else 0.62 * (1 - d) / 0.6)
    f.ox = i                                                  # la trame glisse
    voile(f, lambda px, py: abs(px - 28 + i) <= 28 and abs(py - 7) <= 7, (-i, 0, 56 - i, 14), BRUME,
          lambda px, py: dens(px + i, py))
    f.ox = 0


@acteur("vapeur", 19, 26, 5, 1000, cerne=False)
def vapeur(f, i):
    haut = 24 - i * 5.2                                       # elle monte, s'élargit, se défait
    def dens(px, py):
        if py < haut - 4 or py > 25:
            return 0.0
        axe = 9.5 + 2.2 * math.sin((py + i * 3) * 0.55)
        large = 1.6 + i * 0.9 + (25 - py) * 0.08
        d = abs(px - axe) / large
        return 0.0 if d > 1 else (0.8 - i * 0.13) * (1 - d * d) * min(1.0, (py - haut + 4) / 4.0 + 0.3)
    voile(f, lambda px, py: True, (0, 0, 19, 26), VAPEUR, dens)


@acteur("flocon", 9, 9, 4, 300, cerne=False)
def flocon(f, i):
    c, p = ("#ffffff", "#9fb4d8") if i % 2 == 0 else ("#dbe6f6", "#ffffff")
    diag = i == 2
    for k in range(4):
        ang = k * math.pi / 2 + (math.pi / 4 if diag else 0)
        for d in (1, 2, 3):
            f.px(4 + round(d * math.cos(ang) * (0.8 if diag else 1)), 4 + round(d * math.sin(ang) * (0.8 if diag else 1)),
                 c if d < 3 else p, "")
    if not diag:
        for (dx, dy) in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            f.px(4 + dx, 4 + dy, p, "")
    f.px(4, 4, "#ffffff", "")


@acteur("aiguille", 10, 6, 4, 220, cerne=False)
def aiguille(f, i):
    ang = (15, 60, 115, 160)[i]
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang)) * 0.6
    f.trait(4.5 - 4 * c, 2.5 - 4 * s, 4.5 + 4 * c, 2.5 + 4 * s, "#e8a03a", "")
    f.trait(4.5 - 4 * c, 3.5 - 4 * s, 4.5 + 3 * c, 3.5 + 3 * s, "#b8732a", "")
    f.px(4.5 + 4 * c, 2.5 + 4 * s, "#ffd08a", "")


@acteur("rafale", 36, 10, 4, 90, cerne=False)
def rafale(f, i):
    for (x0, y, l) in ((4, 1, 14), (0, 4, 9), (14, 7, 18)):   # trois filets qui filent vers la droite
        x = (x0 + i * 3) % 36
        for k in range(l):
            xx = (x + k) % 36
            if k > l - 5:
                f.px(xx, y, "#eef2f8", "")
            elif (k + i) % 3:
                f.px(xx, y, VENT, "")
        f.px((x + l) % 36, y - 1, "#eef2f8", "")


@acteur("poussiere", 5, 5, 4, 160, cerne=False)
def poussiere(f, i):
    x, y = ((1, 1), (1, 1), (3, 3), (3, 3))[i]
    c = ("#fff6d6", "#ffd98a", "#ffd98a", "#fff6d6")[i]
    f.px(x, y, c, "")
    if i in (0, 3):
        for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            f.px(x + dx, y + dy, "#ffd98a", "")


# ---------------------------------------------------------------------------------------------------------------------
# Eau et effets de réaction
# ---------------------------------------------------------------------------------------------------------------------
def _rond(f, i, c):
    r = (5.0, 8.8, 12.6, 16.0, 18.6)[i]                       # il s'élargit, puis se défait en trame
    dens = (1.0, 1.0, 0.75, 0.5, 0.25)[i]
    n = int(r * 8)
    for k in range(n):                                        # le bord de l'ellipse, deux pixels d'épaisseur sur les côtés
        ang = k * 2 * math.pi / n
        for rr in (r, r - 1):
            x, y = 19.5 + rr * math.cos(ang), 6.5 + rr * 0.3 * math.sin(ang)
            if dens >= 1 or dens > seuil(int(x), int(y)):
                f.px(x, y, c, "")
    if i < 2:
        f.px(19.5 - r * 0.6, 6.5 - r * 0.24, "#ffffff", "")


@acteur("rond", 39, 13, 5, 280, cerne=False)
def rond(f, i):
    _rond(f, i, "#c7d5f4")


@acteur("rond-trame", 39, 13, 5, 280, cerne=False)
def rond_trame(f, i):
    _rond(f, i, "#d6e3f4")


@acteur("plouf", 24, 12, 4, 90, cerne=False)
def plouf(f, i):
    e = (2.0, 5.0, 8.4, 10.6)[i]                              # les gouttes jaillissent, s'écartent, retombent
    h = (4.0, 8.0, 9.0, 6.0)[i]
    for k, (cote, m) in enumerate(((-1, 1.0), (1, 1.0), (-1, 0.55), (1, 0.55))):
        x, y = 11.5 + cote * e * m, 11 - h * (1.0 if m < 1 else 0.6)
        if i == 3 and m < 1:
            continue
        f.px(x, y, EAU[1], ""); f.px(x, y + 1, EAU[0], "")
        if i < 3:
            f.px(x, y - 1, EAU[2], "")
    if i < 2:
        f.trait(11.5, 11 - h - 2, 11.5, 11 - h + 1, "#ffffff", ""); f.px(10.5, 11 - h, EAU[1], ""); f.px(12.5, 11 - h, EAU[1], "")
    if i < 3:
        f.trait(11.5 - e, 11, 11.5 + e, 11, EAU[0], "") if i == 0 else None


@acteur("bulle", 20, 15, 4, 150)
def bulle(f, i):
    rx, ry = ((3.6, 2.8), (5.6, 4.4), (8.6, 6.2), (5.6, 4.4))[i]
    b = f.boule(9.5, 13 - ry, rx, ry, CREME, biais=0.6, gain=0.5)
    f.px(9.5 - rx * 0.45, 13 - ry - ry * 0.4, "#ffffff"); f.px(9.5 - rx * 0.45 + 1, 13 - ry - ry * 0.4 - 1, "#ffffff")


@acteur("eclats", 35, 31, 5, 70, cerne=False)
def eclats(f, i):
    cx, cy = 17, 15
    if i == 0:
        _etoile(f, cx, cy, 3, ORANGE[3], ORANGE[4], diag=True)
        return
    r = (0, 7.0, 11.5, 14.0, 15.0)[i]
    for k in range(8):                                        # huit éclats qui s'éloignent et s'éteignent
        ang = k * math.pi / 4 + (math.pi / 8 if i % 2 == 0 else 0)
        x, y = cx + r * math.cos(ang), cy + r * 0.86 * math.sin(ang)
        c = (ORANGE[2] if k % 2 == 0 else ORANGE[3]) if i < 4 else ORANGE[3]
        if i < 3:
            _etoile(f, int(x), int(y), 2 if i == 1 else 1, c, ORANGE[4])
            f.px(cx + (r - 3) * math.cos(ang), cy + (r - 3) * 0.86 * math.sin(ang), ORANGE[3], "")
        elif i == 3 or k % 2 == 0:
            f.px(x, y, c, "")
    if i == 1:
        _etoile(f, cx, cy, 2, ORANGE[4], "#ffffff")


@acteur("note", 11, 15, 2, 180)
def note(f, i):
    k = "#3d2f63"
    dy = i                                                    # elle sautille
    f.boule(3.6, 11.4 + dy - i, 3.0, 2.4, Rampe("#2a2048", "#3d2f63", "#6a5a96"), biais=0.5)
    f.rect(5.6, 2 + dy - i, 2, 9.4, k)
    f.poly([(7.6, 2 + dy - i), (10, 4.4 + dy - i), (10, 7.4 + dy - i), (7.6, 5 + dy - i)], k)
    f.px(2.6, 10.6, "#efe0c0") if i == 0 else f.px(8, 4.4, "#efe0c0")
