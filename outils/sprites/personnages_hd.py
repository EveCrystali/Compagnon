"""Les personnages des campagnes en haute définition (docs/SPRITES.md, « Personnages en haute définition »).

À l'unité de la scène HD (480 × 240 unités, 2 px d'écran par unité ; règle 9 de CLAUDE.md), chaque personnage est
redessiné, pas agrandi : visage lisible, mains, plis, matière, ombrage en trois à cinq tons tramés, lumière en haut à
gauche, cerne teinté. Tout sort des pinceaux de pinceau_hd.py : aucun logiciel de dessin, aucune image importée,
aucun style repris. Jamais d'opposition rouge / vert : joues pêche, bouches prune ; chaque humeur change aussi une
forme (sourcils, paupières, bouche, bras, goutte).

Un personnage est une fonction `dessin(f, e)` qui peint une `Feuille` pour un `Etat` :

    humeur   neutre | joie | peur | triste | surpris | tendre | colere | malice
    paup     0 yeux ouverts, 1 mi-clos, 2 fermés (le clignement a une image intermédiaire)
    bouche   0 fermée, 1 à 3 de plus en plus ouverte (la parole)
    souffle  0 ou 1 : le haut du corps monte d'une unité (ceux qui flottent montent tout entiers)
    t        phase des petits mouvements secondaires (sable qui file, nattes, traîne du nuage), 0 à 3

Les pieds se posent sur la ligne `SOL` de la feuille ; le format d'export (tailles, ancrage, nommage) est celui de
docs/SCENES-HD.md, écrit par le chantier du moteur. Planches de contrôle : planches_personnages_hd.py.
"""
import math

from pinceau_hd import Feuille, Rampe

ENCRE = "#1c2128"
BLANC = "#fbf8f0"
BOUCHE, LANGUE = "#3b1f33", "#c76f9a"
JOUE = "#f2a88a"
LARME = Rampe("#4a8fd0", "#8fc8f0", "#d6efff", cerne="#2a5a96")

HUMEURS = ("neutre", "joie", "peur", "triste", "surpris", "tendre", "colere", "malice")
PERSOS = {}     # (campagne, id) -> dict(nom, description, humeurs, dessin, w, h, sol, vol)
ORDRE = []


class Etat:
    def __init__(self, humeur="neutre", paup=0, bouche=0, souffle=0, t=0):
        self.humeur, self.paup, self.bouche, self.souffle, self.t = humeur, paup, bouche, souffle, t


def perso(campagne, id_, nom, humeurs=(), description="", w=64, h=96, vol=0):
    """vol : unités de vide entre le bas du dessin et le sol (ceux qui flottent)."""
    def poser(dessin):
        PERSOS[(campagne, id_)] = dict(nom=nom, description=description, humeurs=("neutre",) + tuple(humeurs),
                                       dessin=dessin, w=w, h=h, vol=vol)
        ORDRE.append((campagne, id_))
        return dessin
    return poser


def image(cle, e):
    """La feuille d'un personnage dans un état, cernée."""
    p = PERSOS[cle]
    f = Feuille(p["w"], p["h"])
    p["dessin"](f, e)
    f.ox = f.oy = 0
    f.cerner()
    return f


# ---------------------------------------------------------------------------------------------------------------------
# Le visage : yeux, sourcils, bouche (communs à tous ; les mesures viennent de chaque personnage)
# ---------------------------------------------------------------------------------------------------------------------
def oeil(f, x, y, e, cote, rx=2.5, ry=3.0, iris="#3a2a20", pupille=ENCRE, blanc=BLANC, cil=ENCRE, regard=(0.0, 0.0),
         ri=0.8, arc=None):
    """Un œil. cote : -1 celui de gauche à l'image, 1 celui de droite. La paupière dit l'humeur : elle descend vers
    le nez (colère), vers la tempe (tristesse), se relève d'en bas (tendresse) ; la peur et la surprise l'ouvrent grand.
    Renvoie les pixels du blanc de l'œil (vide si l'œil est fermé)."""
    h = e.humeur
    arc = arc or cil
    if e.paup == 2 or h == "joie" or (h == "malice" and cote > 0):
        if h in ("joie", "tendre", "malice"):
            f.courbe([(x - rx, y + 1.2), (x - rx * 0.5, y - 0.6), (x + rx * 0.5, y - 0.6), (x + rx, y + 1.2)], arc)
        else:
            f.courbe([(x - rx, y + 0.2), (x - rx * 0.5, y + 1.4), (x + rx * 0.5, y + 1.4), (x + rx, y + 0.2)], arc)
        return set()
    grand = h in ("surpris", "peur")
    if grand:
        rx, ry = rx * 1.18, ry * 1.2
    haut = {"colere": 0.34, "triste": 0.30, "tendre": 0.30, "malice": 0.26}.get(h, 0.0)
    pente = {"colere": 0.55, "triste": -0.42}.get(h, 0.0)
    if e.paup == 1:
        haut = max(haut, 0.52)
    bas = 0.2 if h == "malice" else 0.0

    def cond(px, py, u, v):
        nez = -(px - x) * cote                       # positif vers le nez
        return y - ry + haut * 2 * ry + pente * nez <= py <= y + ry - bas * 2 * ry
    b = f.disque(x, y, rx, ry, blanc, cond=cond)
    r = min(rx, ry) * ri * (0.72 if grand else 1.0)
    ix, iy = x + regard[0], y + regard[1] + (0.0 if grand else 0.35)
    i = f.disque(ix, iy, r, r * 1.08, iris, dans=b)
    f.disque(ix, iy, r * 0.52, r * 0.56, pupille, dans=i)
    f.px(ix - r * 0.55, iy - r * 0.6, "#ffffff") if (int(math.floor(ix - r * 0.55)) + f.ox,
                                                      int(math.floor(iy - r * 0.6)) + f.oy) in b else None
    # La ligne des cils, juste au-dessus du blanc.
    for (X, Y) in b:
        if (X, Y - 1) not in b:
            f.pose(X, Y - 1, cil)
    return b


def sourcil(f, x, y, e, cote, l=4.0, c=ENCRE, ep=1, repos=0.0):
    """Sourcil : sa pente dit l'humeur. repos : pente au repos (Grumeau fronce même content)."""
    h = e.humeur
    p = {"colere": 1.0, "triste": -0.8, "peur": -0.9, "malice": 0.6 if cote < 0 else -0.5, "tendre": -0.15,
         "joie": -0.1}.get(h, 0.0) + repos * (0.4 if h in ("tendre", "joie", "surpris", "peur", "triste") else 1.0)
    dy = {"surpris": -2.0, "peur": -1.6, "joie": -0.6}.get(h, 0.0)
    xi, xe = x - cote * l / 2.0, x + cote * l / 2.0
    pts = set()
    for k in range(ep):
        pts |= f.trait(xi, y + dy + p * 1.5 + k, xe, y + dy - p * 0.9 + k, c)
    return pts, (xi, y + dy + p * 1.5), (xe, y + dy - p * 0.9)


def bouche(f, x, y, e, l=5.0, ligne=BOUCHE, fond=BOUCHE, langue=LANGUE, dents=BLANC):
    h = e.humeur
    b = e.bouche
    if b:
        rx = l * (0.30, 0.38, 0.44)[b - 1]
        ry = (1.0, 1.7, 2.4)[b - 1]
        if h in ("joie", "tendre", "malice"):
            m = f.disque(x, y - 0.2, rx * 1.25, ry * 1.5, fond, cond=lambda px, py, u, v: v > -0.25)
        elif h in ("surpris", "peur"):
            m = f.disque(x, y + 0.4, rx * 0.8, ry * 1.15, fond)
        else:
            m = f.disque(x, y + 0.3, rx, ry, fond)
        if b >= 2:
            f.disque(x, y + ry * 0.95, rx * 0.7, ry * 0.6, langue, dans=m)
            if h in ("joie", "malice"):
                haut = min(Y for (_, Y) in m)
                for (X, Y) in m:
                    if Y == haut:
                        f.pose(X, Y, dents)
        return m
    if h == "joie":
        return f.courbe([(x - l / 2, y - 1.2), (x - l / 4, y + 0.6), (x + l / 4, y + 0.6), (x + l / 2, y - 1.2)], ligne)
    if h == "tendre":
        return f.courbe([(x - l / 2 + 0.6, y - 0.3), (x - l / 6, y + 0.7), (x + l / 6, y + 0.7), (x + l / 2 - 0.6, y - 0.3)], ligne)
    if h == "malice":
        return f.courbe([(x - l / 2, y + 0.4), (x, y + 0.9), (x + l / 2, y - 1.3)], ligne)
    if h == "triste":
        return f.courbe([(x - l / 2 + 0.5, y + 1.0), (x, y - 0.4), (x + l / 2 - 0.5, y + 1.0)], ligne)
    if h == "colere":
        return f.courbe([(x - l / 2, y + 1.1), (x - l / 4, y - 0.3), (x + l / 4, y - 0.3), (x + l / 2, y + 1.1)], ligne)
    if h == "peur":
        return f.courbe([(x - l / 2, y + 0.6), (x - l / 4, y - 0.6), (x, y + 0.6), (x + l / 4, y - 0.6),
                         (x + l / 2, y + 0.6)], ligne)
    if h == "surpris":
        return f.disque(x, y + 0.3, 1.4, 1.7, fond)
    return f.trait(x - l / 2 + 1, y, x + l / 2 - 1, y, ligne)


def goutte(f, x, y, r=1.6):
    """Une goutte (larme, pluie) : pointe en haut, ventre rond, un éclat."""
    f.poly([(x, y - r * 2.2), (x + r, y), (x - r, y)], LARME, rond=0.0, ton=1)
    f.boule(x, y, r, r, LARME)
    f.px(x - r * 0.4, y - r * 0.3, "#ffffff")


# ---------------------------------------------------------------------------------------------------------------------
# La Grande Panne
# ---------------------------------------------------------------------------------------------------------------------
BOIS = Rampe("#3f2614", "#5a3820", "#8a5a33", "#b8844f", "#dcae74")
VERNIS = "#f6d9a4"
VERRE = Rampe("#6f8fae", "#98b6ce", "#bfd6e4", "#dcebf3", "#f4fafc", cerne="#34475f")
SABLE = Rampe("#a8742a", "#c8923c", "#e8b45a", "#f8d898")
CRIN = Rampe("#3e4452", "#5c6374", "#868ea0", "#b4bcca")


def _ampoule(y, centre=46.0, haut=0):
    """Demi-largeur du verre du sablier à la hauteur y (col au centre, les deux ampoules en goutte)."""
    if y < centre:
        y -= haut
    t = min(1.0, abs(y - centre) / 30.0)
    return 3.0 + 13.6 * math.sin(math.pi * 0.80 * t ** 0.8) ** 0.9


@perso("grande-panne", "grumeau", "Grumeau", ("colere", "tendre", "surpris"),
       "vieux sablier d'attente en bois verni, verre un peu rayé, sourcils de crin gris, un grain coincé au col",
       w=66, h=94)
def grumeau(f, e):
    a = 33
    up = -1 if e.souffle else 0
    h = e.humeur

    def verre_demi(y):
        return _ampoule(y, 46.0, up)

    # Les deux fuseaux tournés, derrière le verre.
    for x in (11.5, 54.5):
        fuseau = [(x, 16 + up, 2.4), (x, 19 + up, 3.3), (x, 22.5 + up, 1.7), (x, 34, 2.3), (x, 46, 3.0), (x, 58, 2.3),
                  (x, 69.5, 1.7), (x, 73, 3.3), (x, 76, 2.4)]
        s = f.tube(fuseau, BOIS)
        for y in (21 + up, 44, 48, 71):                    # les gorges du tournage
            f.trait(x - 3, y, x + 3, y, BOIS[0], dans=s)
        f.trait(x - 1.2, 26 + up, x - 1.2, 40, BOIS[4], dans=s)   # le vernis qui accroche la lumière
        f.trait(x - 1.4, 52, x - 1.4, 64, BOIS[4], dans=s)
    # Le verre : ampoule du bas, ampoule du haut (qui monte quand il respire), le col entre les deux.
    verre = f.tour(a, 16 + up, 76, verre_demi, VERRE, biais=0.30, gain=0.66)
    dedans = {(X, Y) for (X, Y) in verre if abs(X + 0.5 - a) < verre_demi(Y + 0.5) - 2.2}
    # Le sable : ce qui reste en haut (creusé au milieu), le tas en bas.
    def clair(x, y):
        return 0.78 - 0.34 * (x - a) / 13.0 + 0.10 * math.sin(x * 2.3 + y * 1.7)
    f.forme(lambda x, y: 39.5 + up + 2.6 * math.exp(-((x - a) / 4.0) ** 2) <= y < 44.5 + up, (a - 16, 34, a + 16, 46),
            SABLE, clair, dans=dedans, trame=0.3)
    f.forme(lambda x, y: y >= 74.0 - 9.5 * math.exp(-((x - a) / 10.5) ** 2), (a - 16, 60, a + 16, 76), SABLE, clair,
            dans=dedans, trame=0.3)
    # Le filet, en pointillés qui descendent, et le grumeau coincé au col (c'est lui qui le met en retard).
    for y in range(48, 63):
        if (y - e.t) % 4 < 2:
            f.px(a - 0.5, y, SABLE[2 if (y - e.t) % 4 else 3])
    f.px(a - 1.5, 45, SABLE[0]); f.px(a - 0.5, 45, SABLE[1]); f.px(a + 0.5, 45, SABLE[0])
    f.px(a - 0.5, 44, SABLE[1]); f.px(a - 1.5, 44, SABLE[3])
    for (x, y) in ((a - 5, 70), (a + 4, 69), (a + 8, 72), (a - 10, 73), (a + 1, 67)):
        f.px(x, y, SABLE[3])                               # des grains qui brillent sur le tas
    # Reflets et rayures du verre.
    f.oy = up
    f.courbe([(21, 31), (21.5, 25), (24.5, 20.5), (28, 18.5)], "#ffffff", dans=verre)
    f.px(20, 34, VERRE[4])
    f.courbe([(46.5, 36), (47.5, 31), (46.5, 26)], VERRE[3], dans=verre)
    f.trait(41, 18, 44, 21, VERRE[4], dans=verre)          # rayures : il a servi
    f.trait(44, 19, 46, 21, VERRE[3], dans=verre)
    f.oy = 0
    f.courbe([(20.5, 60), (21, 55.5), (23.5, 52)], "#ffffff", dans=verre)
    f.courbe([(46.5, 66), (47.5, 62), (46.5, 58)], VERRE[3], dans=verre)
    f.trait(38, 52, 41, 56, VERRE[4], dans=verre)
    f.trait(26, 57, 27, 59, VERRE[1], dans=verre)
    # Les plateaux tournés, et deux petits pieds en boule.
    def plateau_haut(y):
        y -= up
        return 19.5 if y < 8 else (25.0 if y < 13 else (22.0 if y < 15 else 19.0))

    def plateau_bas(y):
        return 19.0 if y < 77 else (22.0 if y < 79 else (25.0 if y < 84 else 20.5))
    for x in (a - 15.5, a + 15.5):
        f.boule(x, 87.6, 4.2, 3.6, BOIS, biais=0.3)
    haut = f.tour(a, 6 + up, 16 + up, plateau_haut, BOIS)
    bas = f.tour(a, 76, 86, plateau_bas, BOIS)
    f.oy = up
    f.trait(a - 20, 9, a - 9, 9, VERNIS, dans=haut)
    f.trait(a - 6, 9, a - 3, 9, BOIS[4], dans=haut)
    f.trait(a - 16, 11, a + 2, 11, BOIS[2], dans=haut)     # le fil du bois
    f.trait(a + 6, 10, a + 19, 10, BOIS[1], dans=haut)
    f.trait(a - 24, 12, a + 24, 12, BOIS[1], dans=haut)
    f.trait(a - 18, 6, a - 8, 6, BOIS[4], dans=haut)
    f.oy = 0
    f.trait(a - 20, 80, a - 10, 80, VERNIS, dans=bas)
    f.trait(a - 7, 80, a - 4, 80, BOIS[4], dans=bas)
    f.trait(a - 14, 82, a + 4, 82, BOIS[2], dans=bas)
    f.trait(a + 7, 81, a + 20, 81, BOIS[1], dans=bas)
    f.trait(a - 24, 83, a + 24, 83, BOIS[0], dans=bas)
    # Le visage, sur le verre du haut. Grognon même content : les sourcils de crin ne se détendent jamais tout à fait.
    f.oy = up
    yo = 30.6
    for cote, x in ((-1, a - 6.5), (1, a + 6.5)):
        oeil(f, x, yo, e, cote, rx=2.6, ry=3.0, iris="#4a3524", cil="#2a2230", ri=0.72)
        if h != "joie":
            f.courbe([(x - 2.6, yo + 4.4), (x, yo + 5.3), (x + 2.6, yo + 4.4)], VERRE[1], dans=verre)   # les cernes
        # Le sourcil : un boudin de crin, hérissé.
        dy = {"surpris": -3.0, "tendre": -0.6}.get(h, 0.0)
        p = {"colere": 3.4, "tendre": 0.9, "surpris": 0.4}.get(h, 2.0)
        xi, xe = x - cote * 4.3, x + cote * 5.6
        yi, ye = yo - 5.4 + dy + p * 0.55, yo - 6.6 + dy - p * 0.45
        s = f.tube([(xi, yi, 1.5), (x, (yi + ye) / 2 - 0.4, 2.0), (xe, ye, 1.4)], CRIN, biais=0.22)
        for k in range(5):                                  # les crins qui dépassent
            q = k / 4.0
            bx, by = xi + (xe - xi) * q, yi + (ye - yi) * q - 2.4
            f.px(bx, by, CRIN[3 if k % 2 else 2])
            if k % 2 == 0:
                f.px(bx + cote, by - 1, CRIN[2])
        f.px(xe + cote * 1.6, ye - 0.6, CRIN[2])
        f.px(xe + cote * 2.4, ye - 1.4, CRIN[1])
    if h == "tendre":
        for x in (a - 10.5, a + 10.5):
            f.disque(x, yo + 4.8, 2.3, 1.2, JOUE, dans=verre)
    eb = Etat("colere" if h == "neutre" and not e.bouche else h, e.paup, e.bouche)
    if h == "colere" and not e.bouche:                     # les dents serrées
        m = f.rect(a - 4, yo + 6.4, 8, 3, BLANC, rond=0)
        f.ourler(m, "#2a2230", cotes=((1, 0), (-1, 0), (0, 1), (0, -1)))
        for x in (a - 1.5, a + 0.5):
            f.px(x, yo + 7.5, VERRE[0])
    else:
        bouche(f, a, yo + 7.2, eb, l=8.0 if h in ("neutre", "colere") else 6.0, ligne="#2a2230")
    f.oy = 0


# ---------------------------------------------------------------------------------------------------------------------
# Le phare éteint
# ---------------------------------------------------------------------------------------------------------------------
PEAU = Rampe("#c98d66", "#e3ac82", "#f2c9a0", "#fbe0c4", cerne="#5a3324")
CUIVRE = Rampe("#6e3414", "#94491c", "#b8652e", "#d9803a", "#f0a55c")
CIRE = Rampe("#163a70", "#1f5fae", "#2f7ed8", "#5aa2ee", "#a8d2ff")
BOTTE = Rampe("#9a6a16", "#d0921e", "#f2bd3c", "#ffdc6e", "#fff2b0")
ARDOISE = Rampe("#232a38", "#353f50", "#4c586e")
CREME = Rampe("#c9b06c", "#f6e6a8", "#fff6d2")


def _main(f, x, y, cote, r=2.5, pouce=True, ouverte=False):
    """Une main : la paume en boule, le pouce vers le corps, un pli entre les doigts ; ouverte, les doigts levés."""
    if ouverte:
        for dx in (-1.6, -0.2, 1.2):
            f.px(x + dx, y - r - 0.4, PEAU[2], PEAU.cerne)
            f.px(x + dx, y - r - 1.2 + abs(dx) * 0.4, PEAU[3], PEAU.cerne)
    m = f.boule(x, y, r, r * 1.08, PEAU, biais=0.45)
    if pouce:
        f.px(x - cote * (r + 0.2), y - 0.6, PEAU[2], PEAU.cerne)
        f.px(x - cote * (r + 0.2), y + 0.4, PEAU[1], PEAU.cerne)
    f.px(x + cote * 0.4, y + r * 0.55, PEAU[0])
    return m


@perso("phare-eteint", "lison", "Lison", ("malice", "peur", "joie"),
       "onze ans, deux nattes cuivrées, des taches de son, un ciré bleu, des bottes jaunes trop grandes", w=62, h=84)
def lison(f, e):
    a, g = 31, 82
    up = -1 if e.souffle else 0
    h = e.humeur
    sw = (0, 1, 0, -1)[e.t % 4]
    # Les jambes, puis les bottes jaunes bien trop grandes (la pointe vers la gauche : elle regarde Pilou).
    for x in (a - 5.8, a + 5.8):
        f.tube([(x, g - 22, 2.8), (x - 0.3, g - 13, 2.6)], ARDOISE)
    for x in (a + 5.6, a - 6.0):
        b = f.boule(x - 2.6, g - 3.3, 6.4, 3.3, BOTTE)
        b |= f.tube([(x, g - 12.5, 4.4), (x - 0.3, g - 5, 4.1)], BOTTE)
        f.ourler(b, BOTTE[0], cotes=((0, 1),))                                   # la semelle
        f.trait(x - 4, g - 16, x + 4, g - 16, BOTTE[3], dans=b)                # le revers de la tige
        f.trait(x - 4, g - 15, x + 4, g - 15, BOTTE[1], dans=b)
        f.px(x - 2.5, g - 11, BOTTE[4]); f.px(x - 2.5, g - 10, BOTTE[4]); f.px(x - 2.5, g - 9, BOTTE[4])   # ça brille
        f.px(x - 6.5, g - 4.5, BOTTE[4]); f.px(x - 5.5, g - 5.5, BOTTE[4])
    # Le ciré : une cloche qui s'évase, la patte de boutonnage, trois brandebourgs, deux poches, l'ourlet.
    cire = f.poly([(a - 9.5, g - 47 + up), (a + 9.5, g - 47 + up), (a + 11.5, g - 37 + up), (a + 13.6, g - 22),
                   (a + 13.2, g - 19.6), (a - 13.2, g - 19.6), (a - 13.6, g - 22), (a - 11.5, g - 37 + up)], CIRE, rond=0.92, gain=0.56,
                  biais=0.34, trame=0.12)
    f.ourler(cire, CIRE[0], cotes=((0, 1),))
    f.trait(a - 12, g - 22, a - 3, g - 22, CIRE[3], dans=cire)                  # l'ourlet accroche la lumière
    f.trait(a + 0.5, g - 44 + up, a + 0.5, g - 21, CIRE[0], dans=cire)
    f.trait(a - 0.5, g - 42 + up, a - 0.5, g - 24, CIRE[3], dans=cire)
    for k, y in enumerate((g - 41 + up, g - 34 + up, g - 27)):
        f.px(a - 1.5, y, BOTTE[3]); f.px(a - 0.5, y, BOTTE[2]); f.px(a - 1.5, y + 1, BOTTE[2]); f.px(a - 0.5, y + 1, BOTTE[0])
        f.px(a + 1.5, y, CIRE[0]); f.px(a + 2.5, y, CIRE[0])                    # la bride
    for cote in (-1, 1):
        x0, x1 = a + cote * 4.5, a + cote * 10.5
        f.trait(x0, g - 30, x1, g - 30, CIRE[0], dans=cire)                     # le rabat de la poche
        f.trait(x0, g - 31, x1, g - 31, CIRE[3] if cote < 0 else CIRE[2], dans=cire)
        f.px(x0, g - 29, CIRE[0]); f.px(x1, g - 29, CIRE[0])
    f.courbe([(a - 4.5, g - 28), (a - 5.5, g - 25), (a - 7, g - 22)], CIRE[1], dans=cire)          # les plis du bas
    f.courbe([(a + 5, g - 28), (a + 6.5, g - 25), (a + 8.5, g - 22)], CIRE[0], dans=cire)
    f.courbe([(a + 3.5, g - 42 + up), (a + 5, g - 38 + up), (a + 5.5, g - 34)], CIRE[1], dans=cire)
    for (x, y0, y1) in ((a - 8.5, g - 44, g - 40), (a - 10.5, g - 28, g - 24)):      # le ciré luit
        f.trait(x, y0 + up, x, y1 + up, CIRE[4], dans=cire)
    f.px(a - 7.5, g - 45 + up, "#ffffff") if (int(a - 7.5), g - 45 + up) in cire else None
    f.oy = up
    # La capuche, rabattue derrière la nuque, et le col crème.
    f.boule(a, g - 48.2, 12.6, 5.2, CIRE, biais=0.22)
    f.tube([(a - 0.5, g - 52, 3.2), (a - 0.5, g - 47.5, 3.2)], PEAU, biais=0.2)
    f.poly([(a - 5, g - 49), (a + 4.5, g - 49), (a + 0.5, g - 44)], CREME, rond=0.6)
    f.trait(a - 0.5, g - 48, a - 0.5, g - 45, CREME[0])
    # Les bras : l'humeur les pose.
    eg, ed = (a - 9.8, g - 44.5), (a + 9.8, g - 44.5)
    bras_g = [eg + (3.5,), (a - 13.6, g - 36.5, 3.3), (a - 15.6, g - 29, 3.0)]
    bras_d = [ed + (3.5,), (a + 13.6, g - 36.5, 3.3), (a + 15.6, g - 29, 3.0)]
    main_g, main_d = (a - 16.2, g - 25.2), (a + 16.2, g - 25.2)
    if h == "joie":                       # elle fait signe
        bras_g = [eg + (3.5,), (a - 15.5, g - 46.5, 3.1), (a - 18.6, g - 54, 2.8)]
        main_g = (a - 19.4 + (0.8 if e.t % 2 else 0), g - 58)
    elif h == "peur":                     # les deux mains serrées sur la poitrine
        bras_g = [eg + (3.5,), (a - 12.2, g - 37, 3.1), (a - 5.5, g - 37.6, 2.8)]
        bras_d = [ed + (3.5,), (a + 12.2, g - 37, 3.1), (a + 5.5, g - 37.6, 2.8)]
        main_g, main_d = (a - 2.6, g - 39.4), (a + 2.4, g - 39.0)
    elif h == "malice":                   # un poing sur la hanche
        bras_d = [ed + (3.5,), (a + 16.4, g - 37.5, 3.0), (a + 12.6, g - 31.5, 2.8)]
        main_d = (a + 10.4, g - 30.4)
    for bras, main, cote, biais in ((bras_d, main_d, 1, 0.24), (bras_g, main_g, -1, 0.40)):
        s = f.tube(bras, CIRE, biais=biais, gain=0.56, trame=0.12)
        f.ourler(s, CIRE[0], cotes=((-cote, 0), (0, 1), (0, -1)), dehors=False)
        fin = bras[-1]
        f.px(fin[0] - 1.5, fin[1] + 1.2, CIRE[3] if cote < 0 else CIRE[2])     # le poignet resserré
        f.px(fin[0] + 0.5, fin[1] + 1.2, CIRE[3] if cote < 0 else CIRE[2])
        _main(f, main[0], main[1], cote, ouverte=(h == 'joie' and cote < 0))
    tx, ty = a - 0.5, g - 61.0
    # Les nattes, par-dessus les épaules, nouées d'un ruban ; elles se balancent.
    for cote in (-1, 1):
        bx, by = tx + cote * 12.2, ty + 8.6
        for i in range(4):
            x = bx + cote * 0.25 * i + sw * 0.3 * i + (0.7 if i % 2 else -0.7)
            s = f.boule(x, by + i * 3.9, 2.9 - 0.15 * i, 2.7, CUIVRE, biais=0.42 if cote < 0 else 0.3)
            f.px(x - 1.2, by + i * 3.9 - 1.2, CUIVRE[4])
            f.ourler(s, CUIVRE[0], cotes=((0, 1),), dehors=False)
        x = bx + cote * 1.2 + sw * 1.5
        y = by + 4 * 3.9 - 1.2
        f.rect(x - 2.0, y, 4.0, 2.0, CREME, rond=0.7)
        f.px(x + cote * 2.4, y - 0.8, CREME[2]); f.px(x + cote * 2.4, y + 2.2, CREME[1])       # les coques du nœud
        f.boule(x + sw * 0.4, y + 4.2, 2.1, 2.6, CUIVRE, biais=0.35)
        f.px(x + sw * 0.6 - 0.5, y + 7.2, CUIVRE[1])
    # Les cheveux de derrière, les oreilles, la tête.
    tx, ty = a - 0.5, g - 61.0
    f.boule(tx, ty - 1.4, 12.5, 12.0, CUIVRE, biais=0.25)
    for cote in (-1, 1):
        f.boule(tx + cote * 11.8, ty + 1.8, 2.2, 2.9, PEAU, biais=0.3)
    tete = f.boule(tx, ty, 11.6, 11.4, PEAU, gain=0.42, biais=0.58,
                   cond=lambda x, y, u, v: abs(u) <= 1 - 0.20 * max(0.0, v) ** 2)
    # La frange : une raie sur le côté, deux mèches qui descendent vers les tempes.
    raie = tx + 3.5

    def frange(x, y):
        return y < ty - 7.8 + 5.4 * abs((x - raie) / 13.0) ** 1.5 + 0.7 * math.sin(x * 1.5)
    chev = f.boule(tx, ty - 1.8, 12.4, 11.6, CUIVRE, cond=lambda x, y, u, v: frange(x, y), biais=0.42)
    f.ourler(chev, CUIVRE[0], cotes=((0, 1),), dehors=False)
    f.trait(raie, ty - 13.5, raie - 0.6, ty - 8, CUIVRE[0], dans=chev)
    for pts in ([(raie - 2, ty - 12.5), (tx - 6, ty - 10.5), (tx - 10.5, ty - 5)],
                [(raie - 1.5, ty - 10), (tx - 4, ty - 8.6), (tx - 8, ty - 5)],
                [(raie + 2, ty - 12), (tx + 8.5, ty - 9.5), (tx + 11, ty - 4.5)]):
        f.courbe(pts, CUIVRE[4] if pts[1][0] < tx else CUIVRE[3], dans=chev)
    # Le visage, un peu tourné vers la gauche.
    yo = ty + 1.6
    xg, xd = tx - 5.2, tx + 4.4
    for cote, x in ((-1, xg), (1, xd)):
        oeil(f, x, yo, e, cote, rx=2.5, ry=3.0, iris="#6f8fb0", pupille="#22324a", cil="#4a2414", regard=(-0.4, 0),
             arc="#4a2414")
        sourcil(f, x, yo - 5.2, e, cote, l=4.4, c="#8a4a1f")
    f.px(tx - 1.5, yo + 3.6, PEAU[1]); f.px(tx - 0.5, yo + 4.4, PEAU[0])            # le nez
    for (dx, dy) in ((-8.5, 3.2), (-6.5, 4.4), (-4.5, 3.0), (2.5, 3.0), (4.5, 4.4), (6.5, 3.2)):
        f.px(tx + dx, yo + dy, PEAU[0])                                             # les taches de son
    plein = h in ("joie", "malice", "tendre")
    for x in (tx - 7.6, tx + 6.4):
        f.disque(x, yo + 5.2, 2.4, 1.4, JOUE, dans=tete, densite=None if plein else 0.5)
    bouche(f, tx - 0.6, yo + 7.4, Etat('tendre' if h == 'neutre' and not e.bouche else h, e.paup, e.bouche), l=5.4)
    if h == "peur":
        goutte(f, tx + 10.5, ty - 5.5, 1.3)                                         # une goutte de sueur
    f.oy = 0


# ---------------------------------------------------------------------------------------------------------------------
# Petit Nuage
# ---------------------------------------------------------------------------------------------------------------------
NUAGE = Rampe("#8f9fc8", "#b4c2e0", "#d6e0f0", "#eef3fa", "#ffffff", cerne="#5b6a96")
ROSE = Rampe("#eda5bd", "#f5c8d6", "#fbe3ea")
NUIT = "#2e3a5c"


@perso("petit-nuage", "brouillon", "Brouillon, le petit nuage", ("joie", "triste", "peur"),
       "un tout petit nuage blanc tombé du ciel, joues roses, grands yeux, qui ne sait pas encore pleuvoir",
       w=86, h=62, vol=24)
def petit_nuage(f, e):
    h = e.humeur
    f.oy = -1 if e.souffle else 0            # il flotte : tout le corps monte
    tr = (0, 1, 2, 1)[e.t % 4]
    serre = 0.94 if h == "peur" else 1.0     # la peur le ramasse sur lui-même
    cx, cy = 39.0, 28.0

    def b(x, y, rx, ry, **kw):
        return f.boule(cx + (x - cx) * serre, cy + (y - cy) * serre, rx * serre, ry * serre, NUAGE, biais=0.50,
                       gain=0.62, **kw)
    # La traîne : deux petits flocons qui le suivent.
    b(67.5 + tr * 0.8, 37.5 - tr * 0.4, 5.2, 3.2)
    b(75.5 + tr * 1.4, 40.5 - tr * 0.6, 2.9, 1.9)
    # Le corps, des bosses du fond vers l'avant.
    corps = set()
    for (x, y, rx, ry) in ((29, 19.5, 11, 10.5), (48.5, 21.5, 10, 9.5), (39, 16.5, 9.5, 8.5), (20, 31, 10, 9.5),
                           (58, 31.5, 9.5, 9), (39, 28, 16.5, 13.5), (29, 36.5, 10.5, 7), (49, 37, 10.5, 6.6)):
        corps |= b(x, y, rx, ry)
    # Des volutes : le dessin des bosses, en demi-teinte.
    for pts in ([(23, 27), (26, 23.5), (30.5, 23)], [(46, 24.5), (50, 22.5), (54, 24)], [(33, 40), (38, 41.5), (44, 40)]):
        f.courbe([(cx + (x - cx) * serre, cy + (y - cy) * serre) for (x, y) in pts], NUAGE[2], dans=corps)
    f.px(26, 14, "#ffffff"); f.px(27, 13, "#ffffff")
    # Le visage : de grands yeux bleu nuit, des joues roses.
    yo = 28.6
    for cote, x in ((-1, cx - 7.2), (1, cx + 7.2)):
        o = oeil(f, x, yo, e, cote, rx=3.0, ry=3.7, iris=NUIT, pupille="#1a2340", blanc="#ffffff", cil=NUIT, ri=0.98,
                 arc=NUIT)
        if o and h != "peur":
            f.px(x + 1.2, yo + 2.0, "#8fa8d8")               # le second éclat, en bas
        if h in ("peur", "triste", "surpris"):
            sourcil(f, x, yo - 6.2, e, cote, l=4.6, c="#7584ad")
    for x in (cx - 12.6, cx + 12.6):
        j = f.disque(x, yo + 5.6, 3.3 if h == "joie" else 2.9, 1.9, ROSE[1], dans=corps)
        f.px(x - 1, yo + 5.0, ROSE[2]) if j else None
        f.px(x + 1.5, yo + 6.4, ROSE[0]) if j else None
    bouche(f, cx, yo + 6.4, Etat('tendre' if h == 'neutre' and not e.bouche else h, e.paup, e.bouche), l=5.6, ligne=NUIT)
    if h == "triste":
        goutte(f, cx + 15, 47 + tr * 1.5, 1.9)                     # une goutte, enfin
        f.px(cx - 9.5, yo + 3.4, LARME[1]); f.px(cx - 9.5, yo + 4.4, LARME[2])
    if h == "peur":
        goutte(f, cx + 19.5, 15.5, 1.4)
        for cote in (-1, 1):                                  # il tremble : deux petites vagues de chaque côté
            x = cx + cote * (32 + tr * 0.6)
            f.courbe([(x, 22), (x + cote * 1.4, 25), (x, 28)], NUAGE[0], k="")
            f.courbe([(x + cote * 3, 30), (x + cote * 4.4, 33), (x + cote * 3, 36)], NUAGE[1], k="")
    f.oy = 0


def etats_planche():
    """Les images de contrôle d'une humeur : repos, inspiré, mi-clos, fermé, parole 1 à 3."""
    return [(0, 0, 0, 0), (0, 0, 1, 1), (1, 0, 0, 2), (2, 0, 0, 2), (0, 1, 0, 0), (0, 2, 1, 1), (0, 3, 0, 2)]


# Les autres personnages, campagne par campagne (ils s'inscrivent dans PERSOS à l'import).
import personnages_hd_panne  # noqa: E402,F401
import personnages_hd_phare  # noqa: E402,F401
import personnages_hd_nuage  # noqa: E402,F401
