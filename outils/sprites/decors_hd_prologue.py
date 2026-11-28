"""Décors haute définition du prologue « La colline d'en face » (480 × 240), peints avec paysage.py.

Une seule fin de journée, qui avance d'un lieu à l'autre : fin d'après-midi dorée devant la porte et au jardin, heure
dorée à la mare et au pied de la colline, puis le couchant au sommet. Le soleil descend sur la droite de la maison,
vers la colline d'en face (le but du voyage) ; la même maison, la même colline et son arbre unique reviennent de lieu
en lieu. Ce que Pilou raconte doit se voir : les trois nénuphars en ligne, la grenouille, le canard, les roseaux à
compter, le caillou de l'autre rive.

Coordonnées : unités du monde (x de 0 à 192, y de -16 à 80 ; de 0 à 80, celles des scènes d'avant).
Places à laisser dégagées : Pilou vers x = 18 à 24, son interlocuteur vers x = 165, le sol à y = 78.
"""
import math

import numpy as np

import paysage as pg
from decors_hd import decor
from paysage import Tons, hz, onde, profil

# ---- Les tons du prologue, par heure. Le reste de la palette (herbe sarcelle, or, bois, toit violet…) ne change pas.
HERBE = ("#0e2a40", "#123f52", "#1d6578", "#2f8f9c", "#5bb3ae")
LOIN = ("#4a4788", "#5d5a9c", "#7770b0", "#9484bd", "#b596c2", "#d3a5b8")
HEURE_DOREE = Tons(
    ciel=("#5b6fc4", "#7384d0", "#8d96d8", "#a8a3d9", "#c3abd0", "#dbb0bf", "#eeb9a8", "#f8c692", "#fdd394", "#ffe0a2",
          "#ffecb8", "#fff4cf"),
    loin=LOIN, herbe=HERBE,
    eau=("#14244a", "#1c3360", "#284578", "#39578c", "#52689e", "#7178a8", "#9286ac", "#b497ac", "#d5a8a0"))
COUCHANT = Tons(
    ciel=("#262758", "#34316f", "#473c86", "#5f4a99", "#7d5aa6", "#a06aa8", "#c67c9f", "#e4928a", "#f4ab72", "#fbc67c",
          "#ffdf9e", "#fff0c4"),
    loin=LOIN, herbe=HERBE,
    eau=("#101a38", "#182650", "#22346a", "#33437f", "#4d4f92", "#6d5a9a", "#93669a", "#bb7890", "#dc917f"))


# ---- Ce qui revient de lieu en lieu
def colline_en_face(x):
    """La colline du but, vue de la mare : ronde, son sommet vers x = 153."""
    x = np.asarray(x, dtype=float)
    return 47.0 - 22.5 * np.maximum(0, 1 - ((x - 153) / 32.0) ** 2) ** 0.62


def lentilles(P, zones, graine=170):
    """Des lentilles d'eau : de petits semis clairs qui dérivent d'un pixel (Pilou en ressort une sur la tête)."""
    for z, (x, y, rx, ry, n) in enumerate(zones):
        for i in range(n):
            a, r = 6.283 * hz(i, 1, graine + z), hz(i, 2, graine + z) ** 0.5
            px, py = x + rx * r * math.cos(a) + 0.25 * onde(P.p, hz(i, 3, graine + z)), y + ry * r * math.sin(a)
            P.point(px, py, pg.T.S4 if hz(i, 4, graine + z) < 0.6 else pg.T.S3)


# =====================================================================================================================
# La mare : « Devant moi, la mare. Dessus, trois nénuphars. Dessous, je préfère ne pas savoir. La colline est juste de
# l'autre côté. » Heure dorée : le soleil est encore au-dessus des crêtes, entre la maison et la colline.
# =====================================================================================================================
@decor("prologue", "mare", soleil=(112.0, 30.5), tons=HEURE_DOREE, nom="La mare")
def mare(P, tab):
    T = pg.T
    p = P.p
    # ---- Le ciel : dégradé du bleu lavande à l'or, pas encore d'étoiles.
    tab.plan("ciel", 0.0)
    pg.ciel(P, haut=0.08, halo=0.36, disque=5.2)
    tab.plan("nuages", 0.08)
    pg.voiles(P, y=-3.0, epais=10.0, seuil=0.6)
    pg.cumulus(P, [(34, 17, 46, 8.0, 3, 8, 0.0), (171, 19, 34, 5.5, 5, 7, 0.3), (132, 8, 22, 3.6, 9, 5, 0.8),
                   (92, -3.5, 42, 7.5, 7, 8, 0.55)])
    pg.barres(P, [(66, 33.0, 17, 1.2), (150, 30.5, 22, 1.4), (22, 35, 14, 1.0)])
    # ---- Les lointains : trois crêtes, la plus lointaine se creuse sous le soleil.
    tab.plan("lointains", 0.2)

    def loin1(x):
        x = np.asarray(x, dtype=float)
        creux = 0.3 + 0.7 * np.clip(np.abs(x - 112) / 46.0, 0, 1) ** 1.3
        return profil(x, 42.0, 15.0, 34.0, 61) * creux + 42.0 * (1 - creux)

    loin2 = lambda x: profil(x, 43.5, 8.0, 21.0, 62)
    loin3 = lambda x: profil(x, 45.6, 5.0, 12.0, 63)
    pg.crete(P, loin1, [T.L3, T.L4, T.L5, T.CIEL[7]], 0.9)
    pg.crete(P, loin2, [T.L2, T.L3, T.L4, T.L5], 0.7)
    pg.crete(P, loin3, [T.L1, T.L2, T.L3, T.L4], 0.5)
    pg.sapins(P, loin3, sauf=(96, 128))
    pg.moulin(P, 70.0, float(loin3(70.0)) + 0.2)
    pg.oiseaux(P, 90, 18, 5)
    # ---- Le plan moyen : les prés et la maison d'où l'on vient, la colline où l'on va, la mare entre les deux.
    tab.plan("moyen", 0.5)
    f_pre = lambda x: (45.8 + 0.9 * np.sin(np.asarray(x, dtype=float) / 13.0 + 0.6)
                       - 3.2 * np.exp(-((np.asarray(x, dtype=float) - 38) / 25.0) ** 2)
                       + 0.4 * np.sin(np.asarray(x, dtype=float) / 4.7))
    f_rive = lambda x: 47.6 + 0.5 * np.sin(np.asarray(x, dtype=float) / 7.0 + 2.0) + 0.3 * np.sin(
        np.asarray(x, dtype=float) / 2.9)
    terre = P.Y < f_rive(P.X) + 0.8
    m = pg.pre(P, f_pre, jusque=terre)
    pg.champ(P, f_pre, 7, 25, 0.5, 2.6, T.CIEL[3], T.CIEL[2], 1.6)                  # lavande
    pg.champ(P, f_pre, 58, 92, 0.6, 2.8, T.OR2, T.OR1, -1.8)                        # blé
    pg.champ(P, f_pre, 98, 128, 0.9, 2.4, T.S4, T.S3, 1.2)                          # pâture
    P.remplir(P.crete(m), T.OR2)
    P.remplir(P.crete(m) & (P.X > 86), T.OR3)
    fc = colline_en_face(P.X)
    pg.colline(P, colline_en_face, 153, 32.0, jusque=terre & (fc < 46.9))
    pg.bosquets(P, colline_en_face, 124, 182, 45.0, sauf=lambda x, y: abs(x - 146 - (y - 35) * 0.3) < 4.5)
    pg.sentier(P, [(136.5, 46.6), (145, 42.6), (140.5, 39.2), (151.5, 35.2), (146.5, 31.4), (153.5, 27.8), (152.4, 25.2)])
    pg.grand_arbre(P, 153.0, float(colline_en_face(153.0)) + 0.3, balancoire=True)
    for (x, r, g) in ((12, 2.1, 1), (55, 1.8, 2), (97, 2.0, 3), (108, 1.5, 4), (118, 2.2, 5), (1, 2.4, 6)):
        pg.arbre_rond(P, x, float(f_pre(x)) + 0.4, r, 100 + g)
    for i, x in enumerate((27.0, 29.6, 49.5, 52.0)):
        pg.peuplier(P, x, float(f_pre(x)) + 0.3, 6.5 + 1.5 * hz(i, 0, 94))
    pg.maison(P, 20.5, float(f_pre(20.5)) + 0.5, p, grande=False)                    # la remise
    gy = float(f_pre(38.0)) + 0.6
    chx, chy = pg.maison(P, 38.0, gy, p)                                             # la maison de Pilou
    pg.fumee(P, chx, chy, p)
    pg.linge(P, 44.5, gy + 0.2, 55.5, float(f_pre(55.5)) + 0.4, 3.6)
    for i, x in enumerate((63.0, 70.5, 79.0, 86.5)):
        pg.meule(P, x, float(f_pre(x)) + 2.0 + 0.5 * (i % 2))
    for i, (x, dy) in enumerate(((100.5, 1.6), (104.5, 2.3), (111.0, 1.5), (114.0, 2.5), (122.5, 1.9))):
        pg.mouton(P, x, float(f_pre(x)) + dy, broute=(i == 1 and onde(p) > 0))
    pg.cloture(P, f_pre, 22.0, 60.0)
    pg.rive(P, f_rive, sauf=(132, 176))
    # Le caillou de l'autre rive (celui des cinq pièces), au pied de la colline.
    pg.pierre(P, 128.5, 48.6, 1.5, eau=False)
    P.point(129.6, 49.0, T.LUM)
    # L'eau : le miroir de tout ce qui précède.
    f_berge = lambda x: (72.6 + 1.1 * np.sin(np.asarray(x, dtype=float) / 19.0 + 1.0)
                         + 0.5 * np.sin(np.asarray(x, dtype=float) / 6.3)
                         - 6.0 * np.exp(-((np.asarray(x, dtype=float) - 2) / 22.0) ** 2)
                         - 5.0 * np.exp(-((np.asarray(x, dtype=float) - 191) / 19.0) ** 2))
    pg.miroir(P, tab.derriere(), 47.4, ronds=((80.0, 66.5, 0.0), (121.0, 56.5, 0.45), (146.0, 64.0, 0.7)))
    pg.barque(P, 163.0, 51.6, p)
    lentilles(P, [(24, 66.5, 9, 1.6, 26), (166, 66.5, 10, 1.5, 24), (112, 70.5, 8, 1.0, 14), (60, 52.2, 6, 0.8, 10)])
    petits = [(31, 55.5, 2.2, T.VIOLET), (37, 58.6, 1.6, None), (25.5, 59.8, 2.6, T.CREME), (44, 54.2, 1.4, None),
              (20, 63.5, 1.9, None), (152, 58.8, 2.4, T.CREME), (160, 62.4, 1.7, None), (168, 59.5, 2.1, T.VIOLET),
              (174, 64.0, 1.5, None), (143, 67.4, 2.0, None), (52, 68.6, 2.3, T.VIOLET), (112, 66.8, 1.6, None),
              (78, 53.0, 1.3, None), (103, 51.6, 1.1, None), (131, 52.3, 1.2, T.CREME)]
    for i, (x, y, r, fl) in enumerate(petits):
        pg.nenuphar(P, x, y + 0.12 * onde(p, 0.13 * i), r, 200 + i, fl)
    for i, x in enumerate((62.0, 96.0, 130.0)):                                      # les trois nénuphars, en ligne
        pg.nenuphar(P, x, 61.0 + (i % 2) * 1.2, 7.4, 300 + i, T.CREME if i == 2 else None)
    # La grenouille (sur le nénuphar du milieu) et le canard (sur l'eau, vers (76, 56)) sont des acteurs de la scène.
    pg.libellule(P, 119.0, 53.4)
    for (x, y, r) in ((39.0, 69.6, 2.0), (45.5, 71.0, 1.4), (151.0, 70.2, 1.8), (157.0, 71.6, 1.2), (99.0, 73.4, 1.6)):
        pg.pierre(P, x, y, r)
    # ---- Le premier plan : la berge où l'on marche, l'arbre et sa lanterne, les roseaux à compter.
    tab.plan("premier", 1.0)
    pg.sol(P, f_berge)
    pg.cailloux(P, f_berge)
    pg.touffes(P, f_berge)
    pg.fleurs(P, f_berge)
    pg.champignon(P, 10.6, 77.4, 1.2)
    pg.champignon(P, 12.6, 78.3, 0.8)
    bord = lambda y: (6.4 + 1.4 * np.sin((np.asarray(y, dtype=float) - 20) / 21.0)
                      + 1.6 * np.exp(-((np.asarray(y, dtype=float) - 80) / 5.0) ** 2)
                      + 0.4 * np.sin(np.asarray(y, dtype=float) / 3.1))
    pg.tronc(P, bord)
    P.ell(2.6, 52.0, 1.3, 2.0, T.N0)                                                 # un nœud dans l'écorce
    P.ell(2.6, 52.0, 0.7, 1.2, T.N1)
    P.courbe([(5.5, 76.5), (9.5, 77.6), (14.0, 79.2), (17.0, 80.5)], T.N1, P.ep(1.0), 1)            # une racine
    P.courbe([(5.0, 19.0), (16.0, 12.5), (30.0, 9.5), (44.0, 7.0), (58.0, 1.5)], T.N0, P.ep(1.8), 1)  # la branche
    P.courbe([(18.0, 12.0), (24.0, 14.5), (29.0, 18.0)], T.N0, P.ep(0.8), 1)
    pg.feuillage(P, lambda x: 13.0 - 0.33 * np.asarray(x, dtype=float) + 2.6 * np.sin(np.asarray(x, dtype=float) / 6.0)
                 + 1.2 * np.sin(np.asarray(x, dtype=float) / 2.3 + 1.0))
    pg.lanterne(P, 27.5, 15.5)
    pg.roseaux(P, 173.5, 196.5, sauf=(187.0, 1.2))
    pg.roseaux(P, 8.0, 14.0, n=4, haut=(9.0, 17.0), penche=1.0, graine=151)
    # Le panneau de bois : une flèche vers la colline, un dessin gravé (Pilou n'écrit pas encore tout).
    px_, py_ = 187.0, 62.0
    P.rect(px_ - 0.7, py_, 1.5, 19.0, T.BR1)
    P.rect(px_ - 0.7, py_, 0.5, 19.0, T.M2)
    mf = P.poly([(px_ - 8.0, py_ + 1.0), (px_ + 4.0, py_ + 0.4), (px_ + 4.2, py_ + 4.6), (px_ - 7.8, py_ + 5.2),
                 (px_ - 10.4, py_ + 3.3)], T.BR2)
    P.remplir(P.crete(mf), T.M2)
    P.ell(px_ - 2.4, py_ + 4.0, 2.6, 1.9, T.M3, cond=(P.Y < py_ + 4.0) & mf)
    P.trait(px_ - 2.4, py_ + 2.2, px_ - 2.4, py_ + 1.4, T.M3)
    P.point(px_ + 1.8, py_ + 1.6, T.OR2)
    pg.lucioles(P, [(11.5, 68.0), (9.0, 48.0), (15.0, 31.0), (56.0, 76.4), (118.0, 77.0), (141.0, 75.4), (179.5, 56.0),
                    (184.0, 45.0), (176.0, 69.0), (34.0, 24.0), (88.0, 75.2)])


APRES_MIDI = Tons(
    ciel=("#8798de", "#99a8e6", "#adb7ec", "#c0c2ee", "#d3c5e6", "#e5c7cf", "#f2ccb9", "#fbd3a8", "#ffdcae", "#ffe6bb",
          "#ffefc6", "#fff6d8"),
    loin=LOIN, herbe=HERBE,
    eau=("#1b3550", "#234566", "#2c5577", "#3d6a8f", "#4f7fa6", "#6f93b6", "#93a6c2", "#b7b6c6", "#d8c4c0"))


def _a(x):
    return np.asarray(x, dtype=float)


def paquerette(P, x, y, r=0.9, tige=0.0):
    """Une pâquerette : pétales crème autour d'un cœur d'or ; avec une tige, elle se balance."""
    T = pg.T
    d = 0.2 * onde(P.p, x / 19.0) if tige else 0.0
    if tige:
        P.trait(x, y, x + d, y - tige, T.S2)
    cx, cy = x + d, y - tige
    for a in range(0, 360, 45):
        P.ell(cx + r * math.cos(math.radians(a)), cy + r * 0.8 * math.sin(math.radians(a)), r * 0.45, r * 0.4,
              T.CREME if a % 90 == 0 else T.BLANC)
    P.ell(cx, cy, r * 0.42, r * 0.36, T.OR2)


def maison_au_loin(P, x, y, k=0.55, lumiere=False):
    """La maison de Pilou vue de loin : mur crème, toit violet, cheminée, porte ronde ; une fenêtre allumée le soir."""
    T = pg.T
    P.rect(x - 3 * k, y - 3 * k, 6 * k, 3 * k, T.M4)
    P.rect(x - 3 * k, y - 3 * k, 2 * k, 3 * k, T.M3)
    P.poly([(x - 4 * k, y - 3 * k), (x, y - 6 * k), (x + 4 * k, y - 3 * k)], T.D1)
    P.rect(x + 1.5 * k, y - 6.2 * k, 1 * k, 2 * k, T.P1)
    P.ell(x - 0.4 * k, y - 0.9 * k, 0.9 * k, 1.1 * k, T.D2, cond=P.Y < y)
    P.point(x + 1.8 * k, y - 1.9 * k, T.LUM2 if lumiere and int(P.p * 8) % 3 else T.LUM)


def colline_au_loin(P, x, y, l=44.0, h=11.0, tons=None):
    """La colline d'en face vue de loin : ronde, brumeuse, liseré d'or, son arbre unique au sommet."""
    T = pg.T
    f = lambda u: y - h * np.maximum(0, 1 - ((_a(u) - x) / (l / 2)) ** 2) ** 0.6
    m = (P.Y >= f(P.X)) & (np.abs(P.X - x) < l / 2) & (P.Y < y + 3)
    cote = -1.0 if P.soleil[0] < x else 1.0
    P.rampe(m, 0.5 + 0.5 * cote * (P.X - x) / (l / 2) + 0.2 * (pg.fbm(P.X / 5.0, P.Y / 3.0, 2, 77) - 0.5),
            tons or [T.L1, T.L2, T.L3, T.L4], 0.7)
    P.remplir(P.crete(m), T.OR3)
    P.trait(x, y - h - 2.6, x, y - h + 0.4, T.L0, P.ep(0.4))
    P.ell(x, y - h - 3.6, 2.4, 1.9, T.L0)
    P.ell(x + 0.6 * cote, y - h - 3.9, 1.3, 1.0, T.L1)
    return f


# =====================================================================================================================
# Devant la porte : « Premier problème : mon sac. Le goûter est déjà dedans, il reste de la place pour une seule chose. »
# Fin d'après-midi dorée. Le mur de la maison à gauche, le dehors et la colline d'en face à droite.
# =====================================================================================================================
@decor("prologue", "seuil", soleil=(168.0, 40.0), tons=APRES_MIDI, nom="Devant la maison")
def seuil(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=62.0, haut=0.25, halo=0.4, disque=5.4)
    tab.plan("nuages", 0.08)
    pg.cumulus(P, [(160, 18, 34, 6.0, 31, 7, 0.2), (186, 30, 18, 3.2, 33, 5, 0.6), (172, -4, 30, 5.0, 35, 6, 0.4)])
    pg.barres(P, [(150, 47.0, 14, 1.0), (182, 52.0, 12, 0.9)])
    tab.plan("lointains", 0.2)
    pg.crete(P, lambda x: profil(x, 62.0, 9.0, 24.0, 64), [T.L3, T.L4, T.L5, T.CIEL[7]], 0.8)
    colline_au_loin(P, 160.0, 62.5, 38.0, 10.0)
    pg.oiseaux(P, 150, 26, 3)
    tab.plan("moyen", 0.5)
    f1 = lambda x: 62.0 + 1.6 * np.sin(_a(x) / 9.0) + 0.6 * np.sin(_a(x) / 3.1)
    f2 = lambda x: 68.0 + 1.2 * np.sin(_a(x) / 6.0 + 1.0)
    pg.pre(P, f1, [T.S2, T.S3, T.S4], clair=0.7)
    pg.champ(P, f1, 150, 176, 1.4, 4.2, T.OR2, T.OR1, -1.6)
    pg.pre(P, f2, graine=96)
    for (x, r, g) in ((140, 2.4, 41), (181, 2.0, 42)):
        pg.arbre_rond(P, x, float(f2(x)) + 0.5, r, g)
    pg.cloture(P, f2, 134.0, 198.0, dy=3.5)
    # Le chemin qui part de la maison vers la colline.
    for i in range(26):
        u = i / 25.0
        P.ell(137 + 26 * u + 3 * math.sin(u * 5), 79 - 12 * u, 3.2 * (1 - u) + 0.6, 0.7, T.M4 if i % 2 else T.M3)
    pg.touffes(P, f2, n=60, x0=132, x1=198, haut=2.6, fond=9.0, graine=97)
    for i in range(7):
        paquerette(P, 138 + 8.3 * i + 3 * hz(i, 1, 98), 73.5 + 5 * hz(i, 2, 98), 0.8, tige=1.5 + hz(i, 3, 98))
    # ---- La maison (premier plan) : enduit chaud, plus sombre à gauche ; l'ombre des feuilles y danse.
    tab.plan("premier", 1.0)
    mur = X < 132
    v = 0.52 + 0.012 * (X - 60) + 0.3 * (pg.fbm(X / 14.0, Y / 9.0, 3, 180) - 0.5)
    P.rampe(mur, v, [T.M2, T.M3, T.M4], 0.5)
    feuilles = pg.fbm((X + 0.8 * onde(p)) / 5.0, (Y + 0.5 * onde(p, 0.25)) / 4.0, 3, 181)
    P.remplir(mur & (feuilles > 0.6) & (X + Y * 0.5 > 96) & (X < 128) & (P.T < 0.75), T.M3)
    pan = mur & (X - (Y - 10) * 0.9 > 78) & (X - (Y - 10) * 0.9 < 100) & (Y > 8)          # le pan de lumière rasante
    P.remplir(pan & (P.T < 0.6), T.CREME)
    for i in range(16):                                                                   # écailles de l'enduit
        x, y = 4 + 124 * hz(i, 1, 182), 8 + 54 * hz(i, 2, 182)
        P.trait(x, y, x + 2 + 4 * hz(i, 3, 182), y, T.M2)
        P.trait(x + 1, y + 0.5, x + 3 * hz(i, 4, 182) + 1.5, y + 0.5, T.M2)
    # Soubassement de pierre et dallage du seuil (le sol où l'on se tient : y = 76).
    P.rampe(mur & (Y > 66), 0.5 + 0.5 * (pg.fbm(X / 3.0, Y / 2.0, 2, 183) - 0.5), [T.P1, T.P3], 0.4)
    for j, y in enumerate((66.0, 70.5)):
        P.trait(-6, y, 132, y, T.P1)
        for x in range(-6 + (j % 2) * 5, 132, 10):
            P.trait(x, y, x, y + 4.5, T.P1)
    P.trait(-6, 66.0, 132, 66.0, T.CREME)
    dalle = (Y > 75.0)
    P.rampe(dalle, 0.45 + 0.5 * (pg.fbm(X / 5.0, Y / 1.5, 2, 184) - 0.5) + 0.004 * (X - 60), [T.P1, T.P3, T.CREME], 0.6)
    P.trait(-6, 75.0, 198, 75.0, T.P1)
    for x in range(-2, 198, 13):
        P.trait(x + 3, 75.5, x, 80, T.P1)
    # Avant-toit : tuiles rondes violettes, leur ombre sur le mur.
    P.remplir(mur & (Y < 2.0) & (P.T < 0.5), T.M2)
    toit = P.poly([(-6, pg.HAUT - 1), (142, pg.HAUT - 1), (140, -2.0), (-6, -2.0)], T.D1)
    rang = np.floor((Y - pg.HAUT) / 3.4)
    dans = ((X + rang * 2.5) % 5.0)
    P.rampe(toit, 0.25 + 0.5 * dans / 5.0 + 0.35 * ((Y - pg.HAUT) % 3.4) / 3.4, [T.CIEL[1], T.D1, T.D2, T.L2], 0.5)
    P.remplir(toit & (((Y - pg.HAUT) % 3.4) < 0.45), T.CIEL[0])
    for x in range(-6, 141, 5):                                                           # le rang de rive, en festons
        P.ell(x + 2.5, -2.2, 2.5, 2.2, T.D2, cond=Y > -2.4)
        P.ell(x + 3.3, -1.4, 1.2, 0.9, T.L3, cond=Y > -2.4)
    # Un nid d'hirondelle sous l'avant-toit ; l'hirondelle passe la tête.
    P.ell(118.0, 1.8, 3.4, 2.4, T.BR2, cond=Y > 0.4)
    P.ell(118.0, 2.0, 2.4, 1.5, T.BR1, cond=Y > 0.8)
    if p < 0.6:
        P.ell(118.0, 0.6, 1.3, 1.1, T.ENCRE)
        P.point(119.2, 0.8, T.O3)
        P.point(118.4, 0.2, T.BLANC)
    # Le coin du mur, en plein soleil.
    P.rect(128, -2.0, 4, 77.5, T.M4)
    P.rect(131, -2.0, 1, 77.5, T.OR3)
    # ---- La porte ronde : pierre de taille, planches bleu-violet, hublot de laiton, poignée.
    cx, haut_p, bas_p = 60.0, 30.0, 75.0
    arche = lambda r: (((X - cx) ** 2 + (Y - haut_p) ** 2 <= r * r) & (Y <= haut_p)) | ((np.abs(X - cx) <= r) & (Y > haut_p)
                                                                                       & (Y < bas_p))
    P.rampe(arche(21.5), 0.5 + 0.35 * (X - cx) / 21.5, [T.P1, T.P3, T.CREME], 0.5)
    for a in range(-80, 81, 20):                                                          # joints des claveaux
        r = math.radians(a - 90)
        P.trait(cx + 17.5 * math.cos(r), haut_p + 17.5 * math.sin(r), cx + 21.5 * math.cos(r), haut_p + 21.5 * math.sin(r), T.P1)
    porte = arche(17.5)
    P.rampe(porte, 0.45 + 0.4 * (X - cx) / 17.5 + 0.2 * (pg.fbm(X / 1.2, Y / 12.0, 2, 185) - 0.5), [T.D1, T.D2, T.L2], 0.5)
    for i in range(-2, 3):
        P.remplir(porte & (np.abs(X - (cx + i * 7.0 - 0.3)) < 0.3), T.D1)
    for y in (40.0, 66.0):                                                                # ferrures
        P.remplir(porte & (np.abs(Y - y) < 0.9), T.CIEL[1])
        for i in range(-2, 3):
            P.point(cx + i * 7.0 + 3.2, y - 0.2, T.L4)
    P.ell(cx, 27.0, 5.6, 5.6, T.BR2)
    P.ell(cx, 27.0, 5.0, 5.0, T.LUM)
    P.ell(cx, 27.0, 3.8, 3.8, T.EAU[2])
    P.ell(cx + 1.0, 26.0, 2.2, 1.8, T.EAU[5])
    P.trait(cx - 3.8, 27.0, cx + 3.8, 27.0, T.LUM)
    P.trait(cx, 23.2, cx, 30.8, T.LUM)
    if int(p * 8) in (2, 3):                                                              # un éclat de soleil sur la vitre
        P.point(cx + 1.6, 25.2, T.BLANC, 2)
    P.ell(cx + 12.0, 50.0, 2.0, 2.0, T.LUM2)
    P.ell(cx + 12.3, 50.6, 1.3, 1.2, T.LUM)
    # Le mot punaisé sur la porte, dessiné plutôt qu'écrit : une colline, une flèche, un soleil.
    mot = P.poly([(43.0, 42.0), (54.5, 41.0), (55.2, 54.0), (43.8, 55.0)], T.CREME)
    P.remplir(mot & (Y > 53.2), T.M4)
    P.point(48.8, 42.3, T.O2, 2)
    P.ell(48.5, 52.5, 3.6, 3.4, T.S3, cond=mot & (Y < 52.4))
    P.trait(48.5, 49.0, 48.5, 47.6, T.BR2)
    P.trait(45.0, 46.0, 47.8, 46.0, T.O2)
    P.trait(47.0, 45.2, 47.8, 46.0, T.O2)
    P.ell(52.6, 45.2, 1.1, 1.1, T.O3)
    # Marche de pierre et paillasson.
    P.poly([(34, 71.5), (88, 71.5), (94, 76.5), (28, 76.5)], T.P3)
    P.trait(28, 76.5, 94, 76.5, T.P1)
    P.trait(34, 71.5, 88, 71.5, T.CREME)
    P.poly([(40, 72.6), (82, 72.6), (86, 76.0), (36, 76.0)], T.BR2)
    for i in range(12):
        P.trait(41 + i * 3.6, 73.0, 39.5 + i * 3.9, 75.8, T.O2 if i % 2 else T.BR1)
    # ---- Le sac à dos, trop plein : la lampe de poche, une chaussette, la corde à sauter, le pull roulé.
    sx, sy = 79.0, 72.0
    P.ell(sx - 9, sy + 0.6, 12, 1.2, T.P1, cond=Y > sy - 0.2)                                # son ombre, vers la gauche
    P.poly([(sx + 4, sy - 26), (sx + 13, sy - 37), (sx + 16.5, sy - 34), (sx + 7.5, sy - 23)], T.D1)   # la lampe
    P.poly([(sx + 5.4, sy - 26.5), (sx + 12.6, sy - 35.2), (sx + 13.8, sy - 34.2), (sx + 6.6, sy - 25.5)], T.D2)
    P.ell(sx + 15.0, sy - 35.8, 2.9, 2.9, T.LUM)
    P.ell(sx + 15.4, sy - 36.3, 1.6, 1.6, T.LUM2)
    P.poly([(sx - 6, sy - 25), (sx - 7.4, sy - 34.5), (sx - 2.4, sy - 35), (sx - 1.4, sy - 26)], T.CREME)   # la chaussette
    P.rect(sx - 7.4, sy - 34.6, 5.0, 1.6, T.BLEU)
    P.rect(sx - 7.2, sy - 31.6, 5.2, 0.8, T.O3)
    P.ell(sx, sy - 26.0, 9.2, 3.6, T.O3)                                                      # le pull roulé
    P.ell(sx - 1.5, sy - 27.0, 6.0, 1.8, T.CREME)
    corps = P.poly([(sx - 12, sy - 25), (sx + 12, sy - 25), (sx + 13.2, sy - 0.5), (sx - 13.2, sy - 0.5)], T.O2)
    P.rampe(corps, 0.35 + 0.5 * (X - sx + 13) / 26.0 + 0.2 * (pg.fbm(X / 2.0, Y / 6.0, 2, 186) - 0.5), [T.BR2, T.O2, T.O3], 0.5)
    P.remplir(corps & (X > sx + 10.8), T.LUM)
    rabat = lambda rx, ry, dx=0.0: ((X - sx - dx) / rx) ** 2 + ((Y - (sy - 24.5)) / ry) ** 2 <= 1
    P.remplir(rabat(13.0, 5.6) & (Y > sy - 26.5), T.D1)
    P.remplir(rabat(11.6, 4.4) & (Y > sy - 26.5), T.D2)
    P.remplir(rabat(7.0, 2.4, 2.0) & (Y > sy - 26.0), T.L2)
    P.rect(sx - 1.2, sy - 20.4, 2.4, 5.0, T.D1)
    P.rect(sx - 2.0, sy - 16.0, 4.0, 2.8, T.LUM)
    P.rect(sx - 1.0, sy - 15.2, 2.0, 1.2, T.BR2)
    poche = P.poly([(sx - 9, sy - 12), (sx + 9, sy - 12), (sx + 9, sy - 2.5), (sx - 9, sy - 2.5)], T.BR2)
    P.remplir(poche & (X > sx - 8) & (X < sx + 8) & (Y > sy - 11) & (Y < sy - 3.4), T.O3)
    P.trait(sx - 8, sy - 11.0, sx + 8, sy - 11.0, T.LUM)
    P.trait(sx - 8, sy - 8.6, sx + 8, sy - 8.6, T.O2)
    for dx in (-13.4, 13.0):                                                                  # les bretelles
        P.courbe([(sx + dx, sy - 22), (sx + dx * 1.18, sy - 12), (sx + dx * 1.02, sy - 2)], T.BR1, P.ep(0.9))
    bal = 0.5 * onde(p, 0.3)
    P.courbe([(sx - 11.5, sy - 23), (sx - 18.0 + bal, sy - 17), (sx - 15.5 + bal, sy - 8), (sx - 12.6, sy - 1.5)], T.CREME, 1)
    P.rect(sx - 14.2, sy - 5.8, 3.0, 5.4, T.O3)                                               # la poignée de la corde
    P.rect(sx - 14.2, sy - 5.8, 3.0, 0.9, T.CREME)
    # ---- La boîte aux lettres (c'est sa toute première lettre) et la lanterne de la porte.
    P.rect(98.0, 36.0, 10.0, 7.0, T.D2)
    P.rect(98.0, 36.0, 10.0, 1.2, T.L2)
    P.rect(98.0, 42.0, 10.0, 1.0, T.D1)
    P.rect(100.0, 38.4, 6.0, 0.8, T.ENCRE)
    P.poly([(100.5, 34.2), (106.5, 33.4), (107.0, 38.4), (101.0, 38.4)], T.CREME)
    P.point(105.0, 34.6, T.O3, 2)
    P.trait(108.0, 37.0, 110.6, 34.0 + 0.4 * onde(p), T.O3, P.ep(0.5))                         # le petit drapeau levé
    P.rect(110.0, 32.8 + 0.4 * onde(p), 2.4, 1.8, T.O3)
    P.trait(84.0, 14.0, 90.0, 14.0, T.BR1, P.ep(0.6))
    pg.lanterne(P, 89.5, 14.0, corde=3.4)
    # ---- La fenêtre : volets bleus, rideau qui respire, jardinière fleurie.
    fx, fy, fw, fh = 104.0, 12.0, 16.0, 17.0
    P.rect(fx - 1, fy - 1, fw + 2, fh + 2, T.P3)
    P.rect(fx, fy, fw, fh, T.EAU[1])
    P.rampe((X > fx) & (X < fx + fw) & (Y > fy) & (Y < fy + fh), 0.3 + 0.5 * (X - fx) / fw - 0.02 * (Y - fy),
            [T.EAU[1], T.EAU[3], T.EAU[5]], 0.6)
    r = 3.5 + 0.6 * onde(p, 0.15)
    P.poly([(fx, fy), (fx + r + 2, fy), (fx + r, fy + fh * 0.6), (fx, fy + fh)], T.CREME)      # le rideau
    P.poly([(fx + 1.2, fy), (fx + 2.0, fy), (fx + 1.6, fy + fh * 0.8), (fx + 0.8, fy + fh)], T.M4)
    P.rect(fx + fw / 2 - 0.4, fy, 0.8, fh, T.P3)
    P.rect(fx, fy + fh / 2 - 0.4, fw, 0.8, T.P3)
    for cote in (-1, 1):
        vx = fx - 7.5 if cote < 0 else fx + fw + 1.5
        P.rect(vx, fy - 1, 6, fh + 2, T.D2)
        P.rect(vx, fy - 1, 1, fh + 2, T.L2 if cote > 0 else T.D1)
        for y in np.arange(fy + 0.5, fy + fh, 2.0):
            P.trait(vx + 1, y, vx + 5, y, T.D1)
    P.rect(fx - 2, fy + fh + 1, fw + 4, 3.6, T.BR2)
    P.rect(fx - 2, fy + fh + 1, fw + 4, 0.8, T.M2)
    for i in range(9):
        x = fx - 0.5 + i * 2.1
        d = 0.25 * onde(p, 0.11 * i)
        P.trait(x, fy + fh + 1, x + d, fy + fh - 1.6 - (i % 3) * 0.7, T.S2)
        P.ell(x + d, fy + fh - 2.2 - (i % 3) * 0.7, 1.0, 0.9, (T.O3, T.CREME, T.VIOLET)[i % 3])
        P.point(x + d, fy + fh - 2.3 - (i % 3) * 0.7, T.OR2)
    P.trait(fx + 3.0, fy + fh + 4.6, fx + 2.6, fy + fh + 8.0 + 0.3 * onde(p), T.S2)             # une tige qui retombe
    P.point(fx + 2.6, fy + fh + 8.4 + 0.3 * onde(p), T.S3)
    # ---- Le pot de pâquerettes, les bottes, la vigne qui grimpe sur le coin gauche.
    P.poly([(9, 60.5), (25, 60.5), (22.6, 74.5), (11.4, 74.5)], T.BR2)
    P.rampe((X > 9) & (X < 25) & (Y > 60.5) & (Y < 74.5) & (P.a == T.BR2), 0.3 + 0.6 * (X - 9) / 16.0, [T.BR2, T.O2, T.O3], 0.5)
    P.rect(8, 59.0, 18, 2.6, T.O3)
    P.rect(8, 59.0, 18, 0.8, T.LUM)
    for i, (x, y) in enumerate(((11.5, 51.5), (17.0, 48.0), (22.5, 52.5), (14.5, 55.5), (20.0, 56.5), (9.0, 56.0))):
        d = 0.3 * onde(p, 0.17 * i)
        P.trait(17.0, 59.0, x + d, y, T.S2)
        paquerette(P, x + d, y, 1.7)
    for (bx, k) in ((108.0, 1.0), (114.5, 0.9)):                                              # une paire de bottes
        P.rect(bx, 75.0 - 9 * k, 4.0 * k, 9 * k, T.EAU[2])
        P.rect(bx, 75.0 - 2.6 * k, 6.2 * k, 2.6 * k, T.EAU[2])
        P.rect(bx, 75.0 - 9 * k, 4.0 * k, 1.2, T.EAU[5])
        P.rect(bx + 3.0 * k, 75.0 - 8 * k, 1.0, 5.5 * k, T.EAU[4])
    pg.feuillage(P, lambda x: 20.0 - 2.2 * _a(x) + 3.0 * np.sin(_a(x) / 2.0), x0=-6, x1=12, n=420, graine=187, y_max=28.0,
                 tons=([T.S0, T.S1, T.S1, T.S2], [T.S1, T.S2, T.S3], [T.S2, T.S3, T.S4, T.OR1, T.OR2]))
    P.courbe([(1.0, 75.0), (2.5, 55.0), (0.5, 36.0), (2.0, 18.0)], T.BR1, P.ep(0.8), 1)
    for i in range(14):
        y = 22 + 3.7 * i
        x = 1.4 + 1.2 * math.sin(y / 6.0)
        c0 = (T.S2, T.S3, T.S1)[i % 3]
        P.ell(x + 2.2 + 0.2 * onde(p, 0.1 * i), y, 1.7, 1.1, c0)
        P.ell(x - 1.6, y + 1.6, 1.4, 1.0, T.S2 if i % 2 else T.S1)
    # Un papillon autour de la jardinière.
    bx, by = 126.0 + 2.0 * onde(p), 30.0 + 1.5 * onde(p * 2, 0.2)
    ouvert = int(p * 8) % 2 == 0
    for cote in (-1, 1):
        P.ell(bx + cote * (1.2 if ouvert else 0.5), by, 1.1 if ouvert else 0.5, 1.3, T.O3)
    P.trait(bx, by - 0.8, bx, by + 0.9, T.ENCRE)


# =====================================================================================================================
# Le jardin, vu à hauteur d'herbe : « J'ai croisé un escargot qui allait dans l'autre sens. On s'est salués, entre
# voyageurs. » Brins géants, la maison minuscule derrière, la colline d'en face devant.
# =====================================================================================================================
def brin(P, x, y, h, penche, larg, sombre, clair, lisere):
    """Un brin d'herbe géant : une lame qui s'effile, sa nervure éclairée du côté du soleil."""
    d = 0.6 * h / 40.0 * onde(P.p, x / 31.0)
    haut = (x + penche + d, y - h)
    mi = (x + penche * 0.35 + d * 0.3, y - h * 0.55)
    P.poly([(x - larg / 2, y), (x + larg / 2, y), (mi[0] + larg * 0.32, mi[1]), haut, (mi[0] - larg * 0.32, mi[1])], sombre)
    P.poly([(x, y), (x + larg / 2, y), (mi[0] + larg * 0.32, mi[1]), haut, (mi[0] + larg * 0.05, mi[1])], clair)
    P.courbe([(x + larg / 2 - 0.3, y), (mi[0] + larg * 0.3, mi[1]), haut], lisere, 1)


@decor("prologue", "jardin", soleil=(146.0, 20.0), tons=APRES_MIDI, nom="Le jardin")
def jardin(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=62.0, haut=0.0, halo=0.3, disque=5.8)
    tab.plan("nuages", 0.08)
    pg.voiles(P, y=-4.0, epais=9.0, seuil=0.6, graine=23)
    pg.cumulus(P, [(46, 19, 40, 7.5, 51, 8, 0.0), (104, 5, 30, 5.4, 53, 6, 0.4), (184, 30, 24, 4.2, 55, 6, 0.7),
                   (20, -5, 34, 6.0, 57, 7, 0.2)])
    tab.plan("lointains", 0.2)
    pg.crete(P, lambda x: profil(x, 55.0, 9.0, 26.0, 65), [T.L3, T.L4, T.L5, T.CIEL[7]], 0.8)
    colline_au_loin(P, 150.0, 55.5, 50.0, 12.0)
    pg.oiseaux(P, 78, 24, 4)
    tab.plan("moyen", 0.5)
    f1 = lambda x: 52.0 + 4.0 * np.sin(_a(x) / 19.0 + 1.0) + 2.0 * np.sin(_a(x) / 7.0)
    f2 = lambda x: 60.0 + 2.2 * np.sin(_a(x) / 11.0) + 0.8 * np.sin(_a(x) / 3.7)
    pg.pre(P, f1, [T.S2, T.S3, T.S4], clair=0.72)
    gy = float(f1(40.0)) + 0.6
    maison_au_loin(P, 40.0, gy, 1.0)
    pg.fumee(P, 42.2, gy - 6.2, p)
    pg.peuplier(P, 30.0, gy + 0.3, 6.0)
    pg.linge(P, 46.0, gy + 0.4, 56.0, float(f1(56.0)) + 0.5, 3.0)
    pg.arbre_rond(P, 70.0, float(f1(70.0)) + 0.5, 2.2, 56)
    pg.cloture(P, f1, 8.0, 34.0, dy=1.6)
    pg.pre(P, f2, graine=57)
    pg.touffes(P, f2, n=260, haut=5.0, fond=14.0, graine=58, bas=80.0)
    for i in range(16):                                                                       # pâquerettes du gazon
        paquerette(P, 6 + 11.6 * i + 5 * hz(i, 1, 59), 64 + 8 * hz(i, 2, 59), 1.0 + 0.5 * hz(i, 4, 59),
                   tige=2.0 + 2 * hz(i, 3, 59))
    # Graines de pissenlit qui passent dans la lumière.
    for i in range(7):
        u = (p + hz(i, 1, 60)) % 1.0
        x, y = 70 + 80 * hz(i, 2, 60) + 3.0 * onde(p, hz(i, 3, 60)), 16 + 32 * hz(i, 4, 60) + 1.2 * onde(p, 0.3 + hz(i, 5, 60))
        P.point(x, y, T.BLANC)
        for (ax, ay) in ((1, -1), (-1, -1), (0, -2), (2, 0), (-2, 0)):
            P.bloc(P.px(x) + ax, P.py(y) + ay, T.CREME if u < 0.5 else T.BLANC)
        P.trait(x, y + 0.6, x - 0.3, y + 2.0, T.M4)
    # ---- Premier plan : la terre, les brins géants, la grande feuille (celle de l'escargot).
    tab.plan("premier", 1.0)
    f_sol = lambda x: 76.2 + 0.6 * np.sin(_a(x) / 9.0)
    pg.sol(P, f_sol, [T.S0, T.S1, T.S2, T.S3], chemin=78.4, graine=61, lisere=0.52)
    pg.cailloux(P, f_sol, n=30, y0=77.0, graine=62)
    for i, (x, h, pen, l) in enumerate(((-2, 70, 6, 9), (6, 52, -5, 7), (12, 34, 7, 6), (58, 26, -6, 6), (128, 30, 8, 6),
                                        (170, 46, 7, 8), (180, 72, -9, 10), (189, 58, -5, 8), (195, 40, -8, 7), (22, 20, -4, 5),
                                        (136, 18, -5, 5), (150, 24, 5, 5), (64, 16, 5, 4), (30, 44, 9, 7), (160, 60, -6, 8),
                                        (-4, 92, 10, 11), (184, 90, -12, 12))):
        brin(P, x, 81.0, h, pen, l, T.S0 if i % 2 else T.S1, T.S1 if i % 2 else T.S2, T.OR2 if i % 3 else T.OR3)
    # La feuille : large, nervurée, une goutte qui brille.
    fe = P.poly([(66, 81), (72, 70), (88, 62.5), (112, 60), (126, 63), (116, 72), (96, 81)], T.S2)
    P.rampe(fe, 0.25 + 0.03 * (X - 66) - 0.035 * (Y - 60) + 0.25 * (pg.fbm(X / 4.0, Y / 2.0, 2, 63) - 0.5),
            [T.S1, T.S2, T.S3, T.S4], 0.6)
    P.remplir(P.crete(fe) & (X > 86), T.OR3)
    P.courbe([(68, 80), (84, 69), (104, 64), (125, 63)], T.S4, 1)
    for i in range(6):
        P.trait(78 + i * 7, 72.5 - i * 1.5, 84 + i * 7, 66.6 - i * 0.8, T.S4)
        P.trait(79 + i * 7, 72.9 - i * 1.5, 82 + i * 7, 78.0 - i * 1.4, T.S3)
    P.ell(112.0, 64.2, 1.3, 1.0, T.EAU[6])
    P.point(111.6, 63.8, T.BLANC)
    # L'escargot du texte est un acteur de la scène (acteur-escargot) : la feuille l'attend, vers (94, 64).
    # Une coccinelle (orange, pas rouge) qui grimpe sur un brin, deux fourmis sur le sol, trèfles et champignon.
    cy = 44.0 - 3.0 * abs(onde(p * 0.5))
    P.ell(172.6, cy, 1.5, 1.3, T.O3)
    P.point(172.0, cy - 0.3, T.ENCRE)
    P.point(173.2, cy + 0.3, T.ENCRE)
    P.ell(172.6, cy - 1.4, 0.7, 0.5, T.ENCRE)
    for i in range(3):
        ax = 140 + 6 * i + 2.0 * ((p + 0.2 * i) % 1.0)
        P.rect(ax, 78.6, 1.5, 0.6, T.ENCRE)
        P.point(ax + 1.6, 78.3, T.ENCRE)
    for (x, y) in ((24, 77.5), (52, 78.3), (134, 77.8), (160, 78.6)):
        for (ax, ay) in ((-0.9, 0), (0.9, 0), (0, -0.9)):
            P.ell(x + ax, y + ay - 1.2, 0.9, 0.8, T.S3)
        P.trait(x, y, x, y - 1.0, T.S2)
    pg.champignon(P, 124.0, 78.6, 1.6)
    pg.champignon(P, 127.0, 79.2, 1.0)


# =====================================================================================================================
# Au pied de la colline : « Je plante un bâton dans le sol, bien droit. […] Deux chemins. À gauche, le sentier : long,
# tranquille, bordé de pâquerettes. À droite, le raccourci : court, raide. » Heure dorée.
# =====================================================================================================================
@decor("prologue", "pied-colline", soleil=(34.0, 33.0), tons=HEURE_DOREE, nom="Au pied de la colline")
def pied_colline(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=52.0, haut=0.06, halo=0.4, disque=5.4)
    tab.plan("nuages", 0.08)
    pg.voiles(P, y=-5.0, epais=9.0, seuil=0.6, graine=25)
    pg.cumulus(P, [(70, 16, 40, 7.0, 71, 8, 0.1), (16, 13, 22, 4.0, 73, 5, 0.5)])
    pg.barres(P, [(52, 38.0, 16, 1.1), (10, 41.0, 12, 0.9)])
    tab.plan("lointains", 0.2)
    pg.crete(P, lambda x: profil(x, 50.0, 10.0, 30.0, 66), [T.L3, T.L4, T.L5, T.CIEL[7]], 0.9)
    loin2 = lambda x: profil(x, 53.0, 6.0, 15.0, 67)
    pg.crete(P, loin2, [T.L2, T.L3, T.L4, T.L5], 0.6)
    pg.sapins(P, loin2, graine=83)
    pg.oiseaux(P, 58, 24, 5)
    tab.plan("moyen", 0.5)
    # La vallée d'où l'on vient, à gauche : la mare qui brille, la maison toute petite.
    f_val = lambda x: 57.0 + 1.5 * np.sin(_a(x) / 12.0) + 0.5 * np.sin(_a(x) / 4.0)
    pg.pre(P, f_val, [T.S2, T.S3, T.S4], clair=0.7, graine=74)
    P.ell(30.0, 60.6, 9.0, 1.3, T.EAU[5])
    P.ell(30.0, 60.3, 7.0, 0.7, T.EAU[8])
    for i in range(5):
        if (i + int(p * 8)) % 3:
            P.point(27 + 1.6 * i, 60.2 + 0.3 * (i % 2), T.SOL)
    maison_au_loin(P, 12.0, float(f_val(12.0)) + 0.4, 0.5)
    for (x, r, g) in ((44, 1.6, 75), (52, 2.0, 76), (3, 1.8, 77)):
        pg.arbre_rond(P, x, float(f_val(x)) + 0.4, r, g)
    # La colline : elle remplit la droite et sort du cadre ; son flanc gauche prend la lumière.
    f_col = lambda x: 70.0 - 78.0 * np.maximum(0, 1 - ((_a(x) - 150) / 96.0) ** 2) ** 0.75
    pg.colline(P, f_col, 196, 120.0, graine=78, fonce=0.004)             # la lumière court loin sur son flanc
    pg.bosquets(P, f_col, 70, 198, 62.0, n=26, graine=79, sauf=lambda x, y: abs(x - (98 + (64 - y) * 0.9)) < 7 or (
        abs(x - (84 - (64 - y) * 0.1)) < 5))
    # Le sentier (à gauche, long, en lacets, bordé de pâquerettes) et le raccourci (à droite, tout droit, raide).
    lacets = [(88, 72), (76, 64), (96, 55), (80, 46), (104, 37), (92, 28), (112, 19), (104, 10), (122, 3), (116, -3),
              (136, -6.4), (147, -7.4)]
    for i in range(len(lacets) - 1):
        (xa, ya), (xb, yb) = lacets[i], lacets[i + 1]
        l = max(0.7, 2.6 - 0.2 * i)
        for j in range(25):
            u = j / 24.0
            P.ell(xa + (xb - xa) * u, ya + (yb - ya) * u, l, l * 0.45, T.M4 if (i + j // 6) % 2 else T.OR3)
        for j in range(4):
            u = (j + 0.5) / 4.0
            paquerette(P, xa + (xb - xa) * u + (3.4 - 0.2 * i) * (1 if j % 2 else -1), ya + (yb - ya) * u - 0.6,
                       max(0.5, 1.0 - 0.08 * i))
    pg.grand_arbre(P, 150.0, float(f_col(150.0)) + 0.3, k=0.7, graine=80)
    for j in range(46):
        u = j / 45.0
        P.ell(98 + 51 * u + 1.5 * math.sin(u * 9), 72 - 79 * u, 2.2 - 1.5 * u, 0.8, T.M2 if j % 3 else T.M3)
    for (x, y, r) in ((112, 52, 1.6), (124, 36, 1.3), (106, 62, 1.2), (133, 20, 1.0)):
        pg.pierre(P, x, y, r, eau=False)
    P.courbe([(116, 46), (120, 44.4), (125, 45.2)], T.BR1, P.ep(0.6))                           # une racine à attraper
    tab.plan("premier", 1.0)
    f_sol = lambda x: 72.6 + 0.7 * np.sin(_a(x) / 15.0) + 0.3 * np.sin(_a(x) / 4.0)
    pg.sol(P, f_sol, [T.N1, T.N2, T.S1, T.S2, T.S3], chemin=75.6, graine=84)
    for j in range(30):                                                                        # la fourche des chemins
        u = j / 29.0
        P.ell(92 - 6 * u, 80 - 8 * u, 7 - 3 * u, 0.8, T.M2 if j % 2 else T.S2)
    pg.cailloux(P, f_sol, y0=74.0, graine=85)
    pg.touffes(P, f_sol, graine=86)
    pg.fleurs(P, f_sol, libres=((22, 52), (136, 166), (84, 100)), graine=87)
    # Le bâton planté bien droit : le point de repère. Un ruban orange y flotte, un oiseau bleu s'y pose.
    bx = 92.0
    P.rect(bx - 0.8, 44.0, 1.8, 30.0, T.BR2)
    P.rect(bx + 0.5, 44.0, 0.5, 30.0, T.BR1)
    P.rect(bx - 0.8, 44.0, 0.5, 30.0, T.M2)
    P.ell(bx + 0.1, 74.0, 3.0, 0.9, T.N1)
    v = onde(p)
    P.poly([(bx + 1.0, 47.0), (bx + 6.0, 46.0 + v), (bx + 10.5, 47.6 - v), (bx + 9.5, 50.4 - v), (bx + 5.5, 49.2 + v),
            (bx + 1.0, 50.0)], T.O3)
    P.trait(bx + 1.0, 50.0, bx + 9.5, 50.4 - v, T.O2)
    hoche = int(p * 8) in (5, 6)
    P.ell(bx - 0.4, 41.6, 2.6, 2.0, T.BLEU)
    P.ell(bx - 0.9, 42.2, 1.6, 1.1, T.CREME)
    P.ell(bx + 1.6, 40.2 + (0.5 if hoche else 0), 1.5, 1.4, T.BLEU)
    P.point(bx + 2.0, 39.8 + (0.5 if hoche else 0), T.ENCRE)
    P.rect(bx + 3.0, 40.2 + (0.5 if hoche else 0), 1.2, 0.6, T.OR1)
    P.poly([(bx - 2.6, 41.6), (bx - 5.4, 40.4), (bx - 2.8, 43.0)], T.D2)
    # Le panneau du raccourci : une flèche qui monte tout droit, dessinée par quelqu'un qui devait bien rire.
    qx, qy = 124.0, 73.5
    P.trait(qx, qy, qx + 1.0, qy - 14, T.BR1, P.ep(0.9))
    pm = P.poly([(qx - 6, qy - 20), (qx + 8, qy - 21.5), (qx + 8.6, qy - 13.5), (qx - 5.4, qy - 12)], T.BR2)
    P.remplir(P.crete(pm), T.M2)
    P.trait(qx - 2.5, qy - 13.6, qx + 4.5, qy - 19.6, T.M4, P.ep(0.6))
    P.trait(qx + 4.5, qy - 19.6, qx + 1.8, qy - 19.2, T.M4, P.ep(0.6))
    P.trait(qx + 4.5, qy - 19.6, qx + 4.4, qy - 17.0, T.M4, P.ep(0.6))
    P.ell(qx - 3.2, qy - 17.8, 1.0, 1.0, T.OR2)
    P.point(qx - 3.6, qy - 18.0, T.ENCRE)
    P.point(qx - 2.8, qy - 18.0, T.ENCRE)
    P.trait(qx - 3.7, qy - 17.3, qx - 2.7, qy - 17.3, T.ENCRE)
    # Un buisson et des roseaux secs sur les bords, pour fermer le cadre.
    P.volumes([(4, 70, 7), (-2, 63, 6), (10, 73, 5), (188, 71, 7), (195, 64, 6)], [T.N0, T.N1, T.N2, T.S1, T.OR1],
              (-0.7, -0.4, 0.3), grain=0.6, graine=88, gain=0.6, base=0.34, trame=0.8)
    pg.roseaux(P, 176.0, 197.0, n=7, haut=(12.0, 24.0), graine=89)
    pg.lucioles(P, [(8.0, 62.0), (184.0, 60.0), (60.0, 77.0), (150.0, 76.5), (192.0, 52.0)], graine=90)


# =====================================================================================================================
# La pente : « Je regarde en haut : c'est haut. Je regarde en bas : c'est déjà un peu haut aussi. […] Une touffe
# d'herbe, un caillou, une racine, et hop. » Le sol monte de (6, 77) à (186, 25). Le soleil a encore baissé.
# =====================================================================================================================
@decor("prologue", "pente", soleil=(30.0, 40.0), tons=HEURE_DOREE, nom="La pente")
def pente(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=58.0, haut=0.02, halo=0.46, disque=5.8)
    tab.plan("nuages", 0.08)
    pg.voiles(P, y=-4.0, epais=9.0, seuil=0.58, graine=27)
    pg.cumulus(P, [(78, 15, 44, 7.5, 111, 8, 0.0), (22, 20, 24, 4.2, 113, 6, 0.4), (120, -2, 36, 6.0, 115, 7, 0.6)])
    pg.barres(P, [(60, 44.0, 18, 1.2), (14, 50.0, 12, 1.0), (96, 36.0, 12, 0.9)])
    tab.plan("lointains", 0.2)
    pg.crete(P, lambda x: profil(x, 57.0, 10.0, 30.0, 68), [T.L3, T.L4, T.L5, T.CIEL[7]], 0.9)
    loin2 = lambda x: profil(x, 60.5, 6.0, 16.0, 69)
    pg.crete(P, loin2, [T.L2, T.L3, T.L4, T.L5], 0.6)
    pg.sapins(P, loin2, graine=114)
    pg.moulin(P, 52.0, float(loin2(52.0)) + 0.2)
    pg.oiseaux(P, 66, 26, 6)
    tab.plan("moyen", 0.5)
    # En contrebas, déjà loin : la vallée, la mare, la maison.
    f_val = lambda x: 66.0 + 1.5 * np.sin(_a(x) / 13.0) + 0.5 * np.sin(_a(x) / 4.0)
    pg.pre(P, f_val, [T.S1, T.S2, T.S3, T.S4], clair=0.66, graine=115)
    pg.champ(P, f_val, 4, 30, 1.0, 3.6, T.OR2, T.OR1, 1.5)
    P.ell(52.0, 70.2, 8.0, 1.2, T.EAU[5])
    P.ell(52.0, 69.9, 6.0, 0.6, T.EAU[8])
    for i in range(4):
        if (i + int(p * 8)) % 3:
            P.point(49 + 1.8 * i, 69.9, T.SOL)
    maison_au_loin(P, 34.0, float(f_val(34.0)) + 0.4, 0.5)
    for (x, r, g) in ((20, 1.5, 116), (44, 1.7, 117), (63, 1.4, 118)):
        pg.arbre_rond(P, x, float(f_val(x)) + 0.4, r, g)
    tab.plan("premier", 1.0)
    # La pente : raide, de bas à gauche vers le haut à droite ; herbe en gradins, lumière rasante.
    f_p = lambda x: 77.0 - (_a(x) - 6.0) * 0.289 + 0.5 * np.sin(_a(x) / 7.0)
    fp = f_p(X)
    m = Y >= fp
    prof = Y - fp
    v = 0.7 - 0.017 * prof + 0.3 * (pg.fbm(X / 7.0, (Y + X * 0.289) / 2.0, 3, 119) - 0.5) + 0.07 * np.sin(prof * 0.9 + X * 0.1)
    P.rampe(m, v, [T.N1, T.N2, T.S1, T.S2, T.S3], 0.8)
    P.remplir(P.crete(m), T.OR2)
    P.remplir(P.crete(m) & (pg.fbm(X / 5.0, Y * 0, 2, 120) > 0.5), T.OR3)
    pg.touffes(P, f_p, n=300, haut=3.4, fond=40.0, bord=0.4, graine=121, bas=80.0)
    for i in range(22):                                                                        # les pâquerettes du sentier
        x = 4 + 186 * hz(i, 1, 122)
        y = float(f_p(x)) + 2.5 + 16 * hz(i, 2, 122)
        if y < 79 and not (26 < x < 44) and not (112 < x < 130):
            paquerette(P, x, y, 0.9 + 0.5 * hz(i, 3, 122), tige=1.2 + hz(i, 4, 122))
    for (x, dy, r) in ((70, 2.2, 1.8), (104, 3.0, 1.4), (142, 2.0, 1.6), (88, 12.0, 2.0), (18, 1.8, 1.2)):
        pg.pierre(P, x, float(f_p(x)) + dy, r, eau=False)
    P.courbe([(150, float(f_p(150)) + 1.2), (156, float(f_p(156)) - 0.6), (163, float(f_p(163)) + 1.4)], T.BR1, P.ep(0.8))
    # Le panneau de bois, de travers : une flèche vers le haut.
    qx = 52.0
    qy = float(f_p(qx)) + 0.5
    P.trait(qx, qy, qx + 3.0, qy - 17, T.BR1, P.ep(1.0))
    pm = P.poly([(qx - 7, qy - 23), (qx + 12, qy - 26), (qx + 13, qy - 17.5), (qx - 6, qy - 14.5)], T.BR2)
    P.remplir(P.crete(pm), T.M2)
    P.remplir(pm & (pg.fbm(X / 6.0, Y / 0.6, 2, 123) > 0.62), T.BR1)
    fl = [(qx - 2, qy - 17.2), (qx + 5, qy - 18.3), (qx + 5.2, qy - 16.6), (qx + 9.4, qy - 20.6), (qx + 4.6, qy - 23.2),
          (qx + 4.8, qy - 21.2), (qx - 2.2, qy - 20.1)]
    P.poly(fl, T.M4)
    # Le pissenlit géant, en aigrette : ses graines s'envolent vers la vallée.
    dx, dy_ = 162.0, 31.0
    P.courbe([(158.0, 81.0), (156.0, 62.0), (160.5, 46.0), (dx, dy_ + 4)], T.S1, P.ep(1.3), P.ep(0.7))
    P.courbe([(158.6, 81.0), (156.6, 62.0), (161.0, 46.0)], T.S3, 1)
    P.poly([(156.5, 81), (150, 70), (141, 66), (148, 74), (152, 81)], T.S1)                      # ses feuilles dentelées
    P.poly([(160, 81), (168, 69), (178, 66), (171, 74), (166, 81)], T.S2)
    P.trait(160.5, 80, 177, 66.4, T.OR2)
    tete = (X - dx) ** 2 + (Y - dy_) ** 2
    P.remplir((tete < 10.5 ** 2) & (P.T < 0.42), T.CREME)
    P.remplir((tete < 7.0 ** 2) & (P.T < 0.7), T.CREME)
    for a in range(0, 360, 12):
        r = math.radians(a + 4 * onde(p, a / 360.0))
        l = 10.2 + 0.8 * hz(a, 1, 124)
        P.trait(dx, dy_, dx + l * math.cos(r), dy_ + l * math.sin(r), T.BLANC if a % 24 else T.CREME)
        ex, ey = dx + (l + 0.6) * math.cos(r), dy_ + (l + 0.6) * math.sin(r)
        for (ax, ay) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            P.bloc(P.px(ex) + ax, P.py(ey) + ay, T.BLANC)
    P.ell(dx, dy_, 2.2, 2.0, T.OR1)
    P.ell(dx - 0.5, dy_ - 0.5, 1.1, 0.9, T.OR3)
    for i in range(8):                                                                         # les graines qui partent
        u = (p + i / 8.0) % 1.0
        x, y = dx - 12 - 70 * u + 2.5 * math.sin(u * 9 + i), dy_ - 6 - 14 * u + 10 * u * u + 3 * hz(i, 1, 125)
        if u > 0.92:
            continue
        P.trait(x, y, x + 0.5, y + 2.0, T.M4)
        for (ax, ay) in ((0, 0), (1, -1), (-1, -1), (2, 0), (-2, 0), (0, -2)):
            P.bloc(P.px(x) + ax, P.py(y) + ay, T.BLANC if u < 0.7 else T.CREME)
    # Le coin bas à gauche et le haut à droite, dans l'ombre : un buisson, des herbes hautes.
    P.volumes([(190, 16, 7), (197, 22, 6), (184, 20, 4)], [T.N0, T.N1, T.N2, T.S1, T.OR1], (-0.8, -0.2, 0.3), grain=0.6,
              graine=126, gain=0.6, base=0.34, trame=0.8)
    pg.lucioles(P, [(186.0, 12.0), (120.0, 70.0), (94.0, 74.0), (176.0, 50.0)], graine=127)


# =====================================================================================================================
# Le sommet : « D'ici on voit la maison, la mare, et même mon bâton, tout petit. […] Le soleil descend. Il est orange,
# il prend son temps. » Et, derrière l'horizon, toute une mer où il se glisse comme dans un bain.
# =====================================================================================================================
@decor("prologue", "sommet", soleil=(132.0, 55.0), tons=COUCHANT, nom="Le sommet")
def sommet(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=57.0, haut=0.0, halo=0.44, etoiles=0.3, lune=(96.0, -7.0, 3.0), disque=7.4)
    tab.plan("nuages", 0.08)
    pg.voiles(P, y=4.0, epais=12.0, seuil=0.56, graine=29)
    pg.cumulus(P, [(60, 26, 50, 8.5, 141, 9, 0.0), (168, 22, 36, 6.0, 143, 7, 0.4), (112, 10, 26, 4.2, 145, 6, 0.7)])
    pg.barres(P, [(100, 44.0, 20, 1.3), (160, 47.5, 18, 1.1), (132, 40.0, 12, 0.9), (58, 49.0, 16, 1.0)])
    pg.oiseaux(P, 104, 31, 8)
    # ---- La mer derrière l'horizon : le soleil s'y glisse ; son chemin de lumière vient jusqu'à la côte.
    tab.plan("lointains", 0.2)
    mer = (Y >= 55.0) & (Y < 61.5)
    force = np.exp(-((X - 132) / (4.0 + (Y - 55) * 2.2)) ** 2)
    P.rampe(mer, 0.45 + 0.5 * force - 0.05 * (Y - 55) + 0.15 * (pg.fbm(X / 9.0, Y / 0.7, 2, 146) - 0.5), T.EAU[3:], 0.7)
    cell = (P.XI + (P.YI % 3) * 2) // 3
    vif = (hz(cell, P.YI, 147) < 0.8 * force) & (np.floor(((p + hz(cell, P.YI, 148)) % 1.0) * 4) < 2)
    P.remplir(mer & vif & (Y > 55.6), T.SOL)
    P.remplir((Y >= 55.0) & (Y < 55.5) & (np.abs(X - 132) < 9), T.BLANC)
    cote = lambda x: profil(x, 60.5, 3.2, 18.0, 149)
    pg.crete(P, cote, [T.L1, T.L2, T.L3, T.L4], 0.5)
    for (x, k) in ((22.0, 1.0), (178.0, 0.8)):                                                  # un phare lointain, un clocher
        y = float(cote(x)) + 0.2
        P.rect(x - 0.5 * k, y - 4.4 * k, 1.0 * k, 4.4 * k, T.L0)
        P.point(x, y - 4.8 * k, T.LUM2 if (int(p * 8) + int(x)) % 4 < 2 else T.L0)
    tab.plan("moyen", 0.5)
    # ---- La vallée en contrebas : les prés bleuis par le soir, la maison (une fenêtre allumée), la mare, le bâton.
    f_val = lambda x: 62.5 + 1.2 * np.sin(_a(x) / 15.0) + 0.5 * np.sin(_a(x) / 5.0)
    pg.pre(P, f_val, [T.L0, T.S1, T.S2, T.S3], clair=0.6, graine=150, pente=0.06)
    pg.champ(P, f_val, 96, 122, 1.2, 3.4, T.CIEL[4], T.CIEL[3], 1.5)
    pg.champ(P, f_val, 140, 168, 1.6, 4.0, T.OR1, T.O2, -1.6)
    hx, hy = 62.0, float(f_val(62.0)) + 1.6
    maison_au_loin(P, hx, hy, 0.62, lumiere=True)
    pg.fumee(P, hx + 1.3, hy - 3.9, p)
    for i in range(10):                                                                        # le jardin, le chemin
        P.point(hx + 4 + 1.5 * i, hy + 0.6 + 0.24 * i, T.M3)
    P.ell(84.0, 66.6, 6.6, 1.2, T.EAU[4])                                                       # la mare
    P.ell(84.0, 66.3, 5.0, 0.6, T.EAU[9])
    for i in range(3):
        P.point(81.6 + 2.4 * i, 66.7, T.S3)                                                     # les trois nénuphars
    P.trait(98.0, 67.6, 98.0, 65.8, T.BR2)                                                      # le bâton, tout petit
    P.point(98.6, 65.9, T.O3)
    for i, (x, r) in enumerate(((50, 1.5), (74, 1.3), (106, 1.6), (128, 1.4), (150, 1.7), (172, 1.5), (186, 1.3), (12, 1.6),
                                (30, 1.4))):
        pg.arbre_rond(P, x, float(f_val(x)) + 1.5 + 2.0 * hz(i, 1, 151), r, 152 + i)
    pg.cloture(P, f_val, 44.0, 58.0, dy=2.4)
    tab.plan("premier", 1.0)
    # ---- Le haut de la colline : herbe rase, à contre-jour, la crête en or. Le grand arbre et sa balançoire.
    f_s = lambda x: 72.0 + 5.0 * ((_a(x) - 96) / 100.0) ** 2 + 0.5 * np.sin(_a(x) / 9.0)
    pg.sol(P, f_s, chemin=78.0, graine=160, lisere=0.42)
    pg.touffes(P, f_s, n=300, haut=2.6, fond=7.0, bord=0.7, graine=161)
    pg.fleurs(P, f_s, n=14, libres=((54, 88), (134, 166)), graine=162)
    tx = 22.0
    P.courbe([(tx - 4, 81), (tx - 1.5, 62), (tx + 0.5, 46), (tx + 2.5, 30)], T.N0, P.ep(4.6), P.ep(2.2))
    P.courbe([(tx + 1.0, 76), (tx + 2.4, 60), (tx + 3.6, 44)], T.O2, 1)
    P.courbe([(tx + 1.6, 44), (tx + 12, 36), (tx + 24, 33)], T.N0, P.ep(1.6), 1)
    P.courbe([(tx, 50), (tx - 10, 42), (tx - 20, 40)], T.N0, P.ep(1.4), 1)
    P.courbe([(tx - 5, 79.5), (tx - 12, 78.4), (tx - 18, 80.5)], T.N1, P.ep(1.2), 1)
    P.courbe([(tx + 3, 79.0), (tx + 9, 78.4), (tx + 13, 80.5)], T.N1, P.ep(1.0), 1)
    bal = 0.9 * onde(p)
    for dx in (15.0, 21.0):                                                                    # la balançoire
        P.trait(tx + dx, 35.2, tx + dx + bal, 66.0, T.M2)
    P.rect(tx + 14.0 + bal, 66.0, 8.4, 1.4, T.O3)
    P.rect(tx + 14.0 + bal, 67.2, 8.4, 0.5, T.BR2)
    pg.feuillage(P, lambda x: 36.0 - 0.0045 * (_a(x) - 22) ** 2 * 6 + 3.0 * np.sin(_a(x) / 6.0) + 1.4 * np.sin(_a(x) / 2.2),
                 x0=-6, x1=62, n=1300, epais=14.0, graine=163, y_max=42.0,
                 tons=([T.N0, T.N1, T.N2, T.S1], [T.N2, T.S1, T.S2], [T.S1, T.S2, T.OR1, T.O2, T.O3]))
    # Les buissons qui font des bruits : deux yeux y clignent (ce sont des hérissons, ils sont polis).
    P.volumes([(180, 74, 8), (190, 70, 7), (172, 77, 5), (197, 76, 6)], [T.N0, T.N1, T.N2, T.S1, T.OR1],
              (-0.8, -0.3, 0.3), grain=0.6, graine=164, gain=0.6, base=0.34, trame=0.8)
    if not 0.55 < p < 0.7:
        P.point(181.0, 75.0, T.LUM2)
        P.point(183.4, 75.0, T.LUM2)
    P.ell(170.0, 78.6, 2.2, 1.3, T.BR1)                                                         # un hérisson sorti
    P.ell(172.2, 79.0, 1.0, 0.7, T.M3)
    P.point(172.8, 78.8, T.ENCRE)
    for i in range(5):
        P.trait(168.4 + i * 0.8, 77.6, 168.0 + i * 0.8, 76.8, T.BR2)
    # Le goûter de Pilou, fini : la serviette à carreaux et les miettes.
    P.poly([(104, 76.4), (116, 75.8), (118, 79.0), (105, 79.6)], T.CREME)
    for i in range(5):
        P.trait(105.6 + i * 2.4, 76.4, 106.4 + i * 2.4, 79.4, T.BLEU)
    P.trait(104.6, 77.9, 117.4, 77.3, T.BLEU)
    P.ell(111.0, 76.6, 1.4, 0.8, T.O3)
    P.point(113.6, 77.2, T.OR2)
    P.point(108.6, 78.4, T.OR2)
    pg.lucioles(P, [(40.0, 60.0), (10.0, 70.0), (150.0, 77.0), (186.0, 62.0), (126.0, 78.6), (60.0, 77.4), (8.0, 54.0),
                    (194.0, 58.0), (92.0, 75.6), (48.0, 44.0), (166.0, 72.4), (30.0, 76.0)], graine=165)
