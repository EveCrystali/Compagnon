"""Décors haute définition du prologue « La colline d'en face » (384 × 160), peints avec paysage.py.

Une seule fin de journée, qui avance d'un lieu à l'autre : fin d'après-midi dorée devant la porte et au jardin, heure
dorée à la mare et au pied de la colline, puis le couchant au sommet. Le soleil descend sur la droite de la maison,
vers la colline d'en face (le but du voyage) ; la même maison, la même colline et son arbre unique reviennent de lieu
en lieu. Ce que Pilou raconte doit se voir : les trois nénuphars en ligne, la grenouille, le canard, les roseaux à
compter, le caillou de l'autre rive.

Coordonnées : unités du monde (192 × 80, celles des scènes d'avant) ; la grille est deux fois plus fine.
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
    pg.voiles(P, y=11.0, epais=8.0, seuil=0.6)
    pg.cumulus(P, [(34, 17, 46, 8.0, 3, 8, 0.0), (171, 19, 34, 5.5, 5, 7, 0.3), (132, 8, 22, 3.6, 9, 5, 0.8)])
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
    pg.grenouille(P, 96.0, 60.0, p)
    pg.canard(P, 76.0 + 0.6 * onde(p, 0.2), 55.2, sens=1)
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
