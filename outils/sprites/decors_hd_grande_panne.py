"""Décors haute définition de « La Grande Panne » (480 × 240), peints avec paysage.py.

L'intérieur d'un ordinateur, chaleureux et absurde : une administration où tout s'est arrêté à 13 h 37. Palette de la
campagne : plastique beige, gris de bureau, violets de circuits, bleu nuit de barre des tâches, deux néons (cyan froid,
orange chaud), le jaune des guichets, le cuivre des câbles, une gelée sarcelle (jamais de vert franc).

Ici presque tout est intérieur : la profondeur vient de la perspective (un point de fuite par salle), des éclairages
(néons, écrans, fenêtres hautes, rais de lumière et leur poussière) et des plans (fond, milieu, premier plan sombre).
Les briques d'intérieur sont en tête de ce fichier ; elles monteront dans paysage.py quand une autre campagne s'en
servira (docs/PEINTURE.md).

Coordonnées : unités du monde (x de 0 à 192, y de -16 à 80). Places de Pilou et de son interlocuteur : celles
d'assets/scenes/grande-panne.txt (sol à y = 78, sauf la citadelle : 70). L'accessoire clé de chaque scène (champ `cle`)
reste dégagé et lisible.
"""
import math

import numpy as np

import paysage as pg
from decors_hd import decor
from paysage import Tons, cs, hz, onde, voile, halo, dallage, rai, poussiere, roue, reflet

N0, N1, N2, N3 = cs("#141a33", "#1f2a52", "#2f3f78", "#4a5fa8")
E1, E2, E3, E4, E5 = cs("#5e5446", "#8a7d68", "#b8a98c", "#ddd0b2", "#f3ead2")
G0, G1, G2, G3, G4 = cs("#262a35", "#3a3f4b", "#5a6070", "#8890a0", "#b8bfcc")
V1, V2, V3, V4 = cs("#2b2145", "#463670", "#6a55a8", "#9b88d8")
C1, C2, C3 = cs("#2a8fc0", "#3fd0ff", "#b8f0ff")
O1, O2, O3 = cs("#c46a24", "#ff9a3c", "#ffd29a")
J1, J2, J3 = cs("#a8862a", "#e8c447", "#fff0a0")
K1, K2 = cs("#7a3f1e", "#b8652e")
Q1, Q2, Q3 = cs("#1a6b70", "#2fb5b0", "#8ff0e0")
B1, B2, B3 = cs("#4a2e17", "#7a4b26", "#a86f3c")
BLANC, ENCRE = cs("#fbf7ee", "#11131c")

PANNE = Tons(
    ciel=("#141a33", "#1f2a52", "#2f3f78", "#4a5fa8", "#6f86c0", "#9fb4de", "#b3c4e6", "#c4d2ec", "#d6dff1", "#e6ecf6",
          "#f2f4f8", "#fbf7ee"),
    loin=("#2b2145", "#463670", "#6a55a8", "#9b88d8", "#b8a8e0", "#d6ccec"),
    herbe=("#0f3a44", "#1a6b70", "#2fb5b0", "#5fd6cc", "#8ff0e0"),
    eau=("#141a33", "#1f2a52", "#2a3a5e", "#3a4f78", "#56698f", "#7483a6", "#939fba", "#b3bbcd", "#d2d6df"),
    soleil="#fbf7ee", or_=("#a8862a", "#e8c447", "#fff0a0"), nuit=("#11131c", "#141a33", "#1f2a52"),
    bois=("#4a2e17", "#7a4b26", "#a86f3c", "#ddd0b2", "#f3ead2"), toit=("#2b2145", "#463670"),
    pierre=("#5a6070", "#b8bfcc"), orange=("#c46a24", "#ff9a3c"), lueur=("#ffd29a", "#fff0a0"), creme="#f3ead2",
    encre="#11131c", violet="#9b88d8", bleu="#3fd0ff")

SEGMENTS = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc", "7": "abc",
            "8": "abcdefg", "9": "abcdfg"}


# ---------------------------------------------------------------------------------------------------------------
# Briques d'intérieur
# ---------------------------------------------------------------------------------------------------------------
def _a(x):
    return np.asarray(x, dtype=float)


def neon(P, x0, x1, y, coul, clair, vacille=0.0, lueur=7.0):
    """Un tube de néon horizontal et sa lueur ; vacille : part de la boucle où il baisse."""
    eteint = vacille and (P.p % 1.0) < vacille
    P.rect(x0 - 0.8, y - 1.0, x1 - x0 + 1.6, 0.6, G1)
    if not eteint:
        halo(P, (x0 + x1) / 2, y + 1.0, (x1 - x0) / 2 + lueur, coul, 0.34, ry=lueur)
    P.rect(x0, y - 0.4, x1 - x0, 1.0, coul if eteint else clair)
    P.rect(x0, y + 0.3, x1 - x0, 0.4, coul)


def sept(P, x, y, texte, coul, l=3.0, h=6.0, ep=1, pas=None, penche=None):
    """Un afficheur à sept segments ; penche : {indice du chiffre: décalage du haut} (le 7 qui penche)."""
    pas = pas or l + 2.0
    for i, ch in enumerate(texte):
        ox = x + i * pas
        if ch == ":":
            P.point(ox + l / 2 - 0.6, y + h * 0.3, coul, ep)
            P.point(ox + l / 2 - 0.6, y + h * 0.7, coul, ep)
            continue
        if ch not in SEGMENTS:
            continue
        pen = (penche or {}).get(i, 0.0)
        m = h / 2
        segs = {"a": (0, 0, l, 0), "b": (l, 0, l, m), "c": (l, m, l, h), "d": (0, h, l, h), "e": (0, m, 0, h),
                "f": (0, 0, 0, m), "g": (0, m, l, m)}
        for s in SEGMENTS[ch]:
            x0, y0, x1, y1 = segs[s]
            P.trait(ox + x0 + pen * (1 - y0 / h), y + y0, ox + x1 + pen * (1 - y1 / h), y + y1, coul, ep)


def papiers(P, x, y, w, n, graine=0, clair=None, ombre=None):
    """Une pile de feuilles posée en (x, y) (son bas), n feuilles : des liserés qui se décalent."""
    clair, ombre = E5 if clair is None else clair, E3 if ombre is None else ombre
    for i in range(n):
        d = (hz(i, 1, graine) - 0.5) * 1.2
        P.rect(x + d, y - (i + 1) * 0.8, w, 0.8, clair if i % 2 else E4)
        P.rect(x + d, y - (i + 1) * 0.8 + 0.4, w, 0.4, ombre)
    return y - n * 0.8


def affiche(P, x, y, w, h, fond, trait, signe=0):
    """Une affiche réglementaire sans un mot : un pictogramme inventé et des lignes de « texte »."""
    P.rect(x, y, w, h, fond)
    P.rect(x, y, w, 0.4, BLANC)
    cx, cy = x + w / 2, y + h * 0.32
    if signe == 0:                                          # un rond barré
        P.ell(cx, cy, w * 0.26, w * 0.26, trait)
        P.ell(cx, cy, w * 0.16, w * 0.16, fond)
        P.trait(cx - w * 0.2, cy + w * 0.2, cx + w * 0.2, cy - w * 0.2, trait)
    elif signe == 1:                                        # une flèche
        P.trait(cx - w * 0.28, cy, cx + w * 0.28, cy, trait, P.ep(0.5))
        P.trait(cx + w * 0.28, cy, cx + w * 0.1, cy - w * 0.16, trait, P.ep(0.5))
        P.trait(cx + w * 0.28, cy, cx + w * 0.1, cy + w * 0.16, trait, P.ep(0.5))
    else:                                                   # un sablier
        P.poly([(cx - w * 0.2, cy - w * 0.26), (cx + w * 0.2, cy - w * 0.26), (cx, cy)], trait)
        P.poly([(cx - w * 0.2, cy + w * 0.26), (cx + w * 0.2, cy + w * 0.26), (cx, cy)], trait)
    for j in range(int(h * 0.36 / 1.2)):
        P.rect(x + w * 0.14, y + h * 0.62 + j * 1.2, w * (0.72 if j % 2 == 0 else 0.5), 0.4, trait)


def voyant(P, x, y, allume, eteint, d=0.0, part=0.5, r=0.5):
    vif = (P.p + d) % 1.0 < part
    if vif:
        halo(P, x, y, r * 4.0, allume, 0.5)
    P.ell(x, y, r, r, allume if vif else eteint)


def cable(P, pts, ep, sombre, clair, reflet=None):
    """Un gros câble : un boudin sombre, sa face éclairée, un reflet fin."""
    P.courbe(pts, sombre, P.ep(ep))
    P.courbe([(x, y - ep * 0.22) for x, y in pts], clair, max(1, P.ep(ep * 0.45)))
    if reflet is not None:
        P.courbe([(x, y - ep * 0.36) for x, y in pts], reflet, 1)


def tickets(P, x, y0, y1, n=4, graine=0, coul=None):
    """Des tickets qui tombent en voletant de y0 à y1."""
    for i in range(n):
        t = (P.p + i / n + hz(i, 1, graine) * 0.2) % 1.0
        tx, ty = x + 3.0 * math.sin(t * 7 + i) + (hz(i, 2, graine) - 0.5) * 6, y0 + (y1 - y0) * t
        if int(t * 8 + i) % 2:
            P.rect(tx, ty, 2.2, 1.2, coul or BLANC)
            P.rect(tx + 0.4, ty + 0.4, 1.2, 0.4, O2)
        else:
            P.rect(tx + 0.4, ty - 0.3, 1.2, 2.0, coul or BLANC)


# =====================================================================================================================
# Le bureau, 13 h 37 : le bas d'un écran vu de près, au petit matin. La barre des tâches est le sol ; la grande horloge
# figée (le 7 penche) est la clé.
# =====================================================================================================================
@decor("grande-panne", "bureau-1337", soleil=(40.0, 41.0), tons=PANNE, nom="Le bureau, 13 h 37", matiere=True)
def bureau_1337(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    # ---- Le fond d'écran : une aube sur un lac, peinte ; le soleil sort derrière les collines, à gauche.
    C = T.CIEL
    sx, sy = 40.0, 29.0
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=50.0, haut=0.28, halo=0.3, disque=0)
    for k, (r_, c0, f_) in enumerate(((20.0, J2, 0.2), (11.0, J2, 0.3), (7.0, J3, 0.45))):       # l'aube : des anneaux de lumière chaude
        halo(P, sx, sy, r_, c0, f_)
    P.ell(sx, sy, 4.6, 4.6, J3)
    P.ell(sx, sy, 3.4, 3.4, BLANC)
    for k in range(7):                                          # des rayons fins, entre les nuages
        a = -math.pi * (0.1 + 0.13 * k)
        m = (np.abs((X - sx) * math.sin(a) - (Y - sy) * math.cos(a)) < 0.25 + 0.012 * np.hypot(X - sx, Y - sy)) & (
            (X - sx) * math.cos(a) + (Y - sy) * math.sin(a) > 8.0) & (np.hypot(X - sx, Y - sy) < 30.0 + 10.0 * hz(k, 0, 277))
        voile(P, m, J2, 0.12 + 0.05 * onde(p, k * 0.13), lumiere=True)
    tab.plan("nuages", 0.08)
    pg.cumulus(P, [(60, 4, 46, 7.5, 201, 9, 0.0), (150, 16, 40, 6.0, 203, 8, 0.4), (104, -8, 34, 5.0, 205, 7, 0.7),
                   (14, -6, 36, 5.5, 278, 7, 0.2), (112, 26, 44, 5.0, 279, 7, 0.55), (176, -4, 30, 5.0, 280, 6, 0.85)], dessous=-0.5)
    for k in range(5):                                          # des filets de nuages, dorés par-dessous
        y_ = 24.0 + k * 2.4
        m = (np.abs(Y - y_ - 1.2 * np.sin(X / 17.0 + k)) < 0.5 + 0.9 * (pg.fbm((X + 3.0 * p) / 20.0, Y / 2.0, 2, 281 + k) - 0.35)) & (X > 4 + 20 * k)
        P.remplir(m, C[9] if k % 2 else C[10])
        P.remplir(m & (X < 80) & (Y > y_ + 0.4) & (np.abs(X - sx) < 30), E5)
    for i in range(5):                                          # un vol d'oiseaux, loin
        bx_, by_ = 66.0 + i * 3.4 + 8.0 * p, 22.0 + abs(i - 2) * 1.5 - 2.0 * p
        P.trait(bx_ - 1.0, by_ - 0.5 * onde(p * 2, i * 0.2), bx_, by_, C[4])
        P.trait(bx_, by_, bx_ + 1.0, by_ - 0.5 * onde(p * 2, i * 0.2), C[4])
    tab.plan("lointains", 0.2)
    # Les collines : quatre crêtes ; les plus lointaines sont pâles et bleues, les plus proches sombres et violettes.
    for i, (base, amp, ech, rampe) in enumerate(((35, 9, 46, [C[7], C[8], C[9], C[10]]), (38, 8, 34, [C[5], C[6], C[7], C[8]]),
                                                 (41, 6, 25, [T.L3, T.L4, T.L5, C[7]]), (43.5, 4, 18, [T.L2, T.L3, T.L4, T.L5]))):
        avant = P.a.copy()
        pg.crete(P, lambda x, b=base, a=amp, e=ech, g=210 + i: pg.profil(x, b, a, e, g), rampe, 0.5)
        neuf = (P.a != avant)
        voile(P, neuf & (np.hypot((X - sx) / 1.6, Y - sy) < 26.0) & (Y < base + 2), J2, 0.3 - 0.05 * i, lumiere=True)   # le liseré d'aube sur chaque crête
        m = np.abs(Y - (base + 3.0 + 1.0 * np.sin(X / 13.0 + i))) < 0.7 * pg.fbm((X + 4.0 * p * (1 + i)) / 15.0, Y, 2, 283 + i)   # la brume dans les creux
        voile(P, m & (P.a >= 0), C[10], 0.4)
    # Le lac : il prend le ciel, et le soleil y pose une colonne d'éclats.
    lac = (Y > 46.0) & (Y < 56.5)
    P.rampe(lac, 0.2 + 0.075 * (Y - 46.0) + 0.2 * (pg.fbm(X / 12.0, Y * 2.0, 2, 287) - 0.5), [C[9], C[8], C[7], C[6], C[5]], 0.4)
    P.remplir(lac & (hz(P.YI, (P.XI + int(p * 8) * (P.YI % 3)) // 6, 288) < 0.12), C[10])        # les rides
    voile(P, lac & (Y < 49.0), T.L4, np.clip((49.0 - Y) / 3.0, 0, 0.5))                           # le reflet des collines, au bord
    eclat = lac & (np.abs(X - sx) < 1.2 + (Y - 46.0) * 0.45) & (hz(P.YI, (P.XI + int(p * 8)) // 2, 289) < 0.6)
    P.remplir(eclat, J3)
    P.remplir(eclat & (np.abs(X - sx) < 1.6), BLANC)
    for k in range(3):                                          # une île et ses sapins, une barque
        P.ell(120.0 + k * 3.0, 49.6, 5.0 - k, 0.9, T.L3)
    for x in (116.0, 119.0, 123.0):
        P.poly([(x - 1.2, 49.0), (x + 1.2, 49.0), (x, 45.4 - (x % 2))], N3)
        P.rect(x - 0.8, 50.4, 1.6, 1.6, C[6])                       # et leur reflet
    P.rect(74.0 + 1.0 * onde(p, 0.3), 51.2, 4.4, 0.7, N2)
    P.rect(75.6 + 1.0 * onde(p, 0.3), 49.4, 0.4, 1.8, N2)
    P.rect(74.4 + 1.0 * onde(p, 0.3), 52.0, 3.6, 0.4, C[6])
    # La rive proche : une lisière de sapins sombres, à contre-jour, qui porte la barre des tâches.
    pg.crete(P, lambda x: pg.profil(x, 55.6, 1.0, 14, 290), [N1, N2, N3, T.L3], 0.4)
    for i in range(46):
        x = -4.0 + i * 4.4 + 2.0 * hz(i, 0, 291)
        h_ = 2.2 + 2.6 * hz(i, 1, 291)
        if 28 < x < 92:
            h_ *= 0.35                                           # une trouée : on voit le lac
        yb = float(np.asarray(pg.profil(np.array([x]), 55.6, 1.0, 14, 290)).ravel()[0]) + 0.6
        P.poly([(x - 1.5, yb), (x + 1.5, yb), (x, yb - h_)], N1)
        P.poly([(x - 1.5, yb), (x, yb), (x, yb - h_)], N2 if abs(x - sx) > 26 else J1)            # le côté tourné vers l'aube
    tab.plan("moyen", 0.5)
    # ---- Les icônes du bureau, la fenêtre qui ne répond plus, le curseur et son sablier.
    for i, (x, y, sorte) in enumerate(((8, -8, 0), (8, 6, 1), (8, 20, 2), (24, -8, 1), (24, 6, 0), (8, 34, 3))):
        if sorte == 0:                                       # un dossier
            P.rect(x, y + 1.6, 8, 5.4, J1)
            P.rect(x, y, 3.6, 2.0, J1)
            P.rect(x + 0.6, y + 2.4, 7.4, 4.6, J2)
            P.rect(x + 0.6, y + 2.4, 7.4, 0.5, J3)
        elif sorte == 1:                                     # une feuille
            P.poly([(x + 1, y), (x + 5.4, y), (x + 7.2, y + 1.8), (x + 7.2, y + 7), (x + 1, y + 7)], BLANC)
            P.poly([(x + 5.4, y), (x + 7.2, y + 1.8), (x + 5.4, y + 1.8)], G3)
            for j in range(3):
                P.rect(x + 2, y + 2.6 + j * 1.3, 4 - j * 0.8, 0.4, G2)
        elif sorte == 2:                                     # une corbeille
            P.poly([(x + 0.8, y + 1.4), (x + 7.4, y + 1.4), (x + 6.6, y + 7), (x + 1.6, y + 7)], G3)
            P.rect(x + 0.2, y + 0.6, 7.8, 0.9, G4)
            for j in range(3):
                P.trait(x + 2.4 + j * 1.7, y + 2.2, x + 2.6 + j * 1.5, y + 6.2, G1)
        else:                                                # un sablier d'attente
            P.poly([(x + 1.4, y), (x + 6.6, y), (x + 4, y + 3.5)], C3)
            P.poly([(x + 1.4, y + 7), (x + 6.6, y + 7), (x + 4, y + 3.5)], C2)
            P.rect(x + 1, y - 0.4, 6, 0.6, B2)
            P.rect(x + 1, y + 6.8, 6, 0.6, B2)
        P.rect(x + 0.6, y + 8.4, 6.8, 0.5, BLANC)             # son nom, illisible
        P.rect(x + 1.8, y + 9.5, 4.4, 0.5, T.CIEL[9])
    fx, fy, fw, fh = 104.0, -10.0, 70.0, 46.0                # la fenêtre « ne répond pas »
    for k in (3, 2, 1):                                        # la traînée de la fenêtre qu'on a secouée
        gx_, gy_ = fx - 3.2 * k, fy + 2.4 * k
        c0 = (BLANC, T.CIEL[11], T.CIEL[10])[k - 1]
        P.rect(gx_, gy_, fw, 0.5, c0)
        P.rect(gx_, gy_, 0.5, fh, c0)
        P.rect(gx_, gy_ + fh - 0.5, 3.2, 0.5, c0)
        P.rect(gx_, gy_ + 1.6, fw * 0.3, 0.4, c0)
    voile(P, (X > fx + 2) & (X < fx + fw + 2) & (Y > fy + 2) & (Y < fy + fh + 2), N1, 0.5)
    P.rect(fx, fy, fw, fh, E5)
    P.rect(fx, fy, fw, 5.0, N2)
    P.rampe((X > fx) & (X < fx + fw) & (Y > fy) & (Y < fy + 5.0), 0.2 + 0.7 * (X - fx) / fw, [N2, N3, T.CIEL[4]], 0.6)
    for i, c0 in enumerate((O2, J2, G4)):
        P.rect(fx + fw - 5.0 - i * 4.4, fy + 1.2, 3.0, 2.6, c0)
    P.rect(fx + 2, fy + 1.8, 22, 0.6, BLANC)
    voile(P, (X > fx) & (X < fx + fw) & (Y > fy + 5) & (Y < fy + fh), BLANC, 0.5)       # elle blanchit : elle est figée
    vitre = (X > fx) & (X < fx + fw) & (Y > fy + 5) & (Y < fy + fh)
    P.rampe(vitre, 0.5 + 0.3 * (X - fx) / fw - 0.3 * (Y - fy) / fh + 0.2 * (pg.fbm(X / 8.0, Y / 6.0, 2, 292) - 0.5), [E4, E5, BLANC], 0.4)
    P.remplir(vitre & (np.abs(X - fx - 46.0 + (Y - fy) * 0.5) < 3.0), BLANC)                     # un reflet de vitre, en biais
    P.remplir(vitre & (np.abs(X - fx - 53.0 + (Y - fy) * 0.5) < 0.8), BLANC)
    P.rect(fx, fy + 5.0, fw, 0.5, E3)
    P.rect(fx + fw - 2.6, fy + 7.0, 1.4, fh - 9.0, E4)                                          # l'ascenseur de défilement
    P.rect(fx + fw - 2.6, fy + 9.0, 1.4, 8.0, G3)
    for j in range(7):
        P.rect(fx + 5, fy + 10 + j * 4.2, (44, 58, 30, 52, 40, 56, 22)[j], 0.8, G4 if j % 3 else G3)
    P.rect(fx + 5, fy + 40.2, 60, 2.6, G4)                    # sa barre de progression, arrêtée
    P.rect(fx + 5, fy + 40.2, 60 * 0.37, 2.6, C2)
    P.rect(fx + 5, fy + 40.2, 60 * 0.37, 0.6, C3)
    cxs, cys = fx + 35, fy + 26                              # le rond qui tourne (lui seul bouge encore)
    for k in range(8):
        a = k * math.pi / 4
        vif = (k - int(p * 8)) % 8
        P.ell(cxs + 5.2 * math.cos(a), cys + 5.2 * math.sin(a), 1.1, 1.1, (C1, C2, C3, BLANC)[3 - min(3, vif)] if vif < 4 else G4)
    mx, my = 86.0 + 1.0 * onde(p), 30.0 + 0.6 * onde(p, 0.25)                           # le curseur, qui tremble
    P.poly([(mx, my), (mx, my + 8), (mx + 2.2, my + 6), (mx + 3.8, my + 9.4), (mx + 5.2, my + 8.6), (mx + 3.6, my + 5.4),
            (mx + 6, my + 5.2)], ENCRE)
    P.poly([(mx + 0.6, my + 1.4), (mx + 0.6, my + 6.6), (mx + 2.4, my + 5.0), (mx + 4.2, my + 8.4), (mx + 4.6, my + 8.2),
            (mx + 3.0, my + 4.8), (mx + 4.6, my + 4.6)], BLANC)
    if int(p * 8) % 4 < 2:                                   # une notification qui clignote, en haut à droite
        P.rect(180, -13, 10, 6, O2)
        P.rect(181, -12, 8, 0.6, O3)
        P.rect(181.6, -10.4, 5, 0.5, BLANC)
    poussiere(P, 40, -14, 190, 50, 26, T.CIEL[10], 220)
    # ---- La barre des tâches : bleu nuit, vue de si près qu'on marche dessus.
    tab.plan("premier", 1.0)
    barre = Y >= 56.0
    P.rampe(barre, 0.75 - 0.03 * (Y - 56) + 0.25 * (pg.fbm(X / 30.0, Y / 3.0, 2, 221) - 0.5), [N0, N1, N2], 0.7)
    P.remplir(barre & (Y < 56.5), N3)
    P.remplir(barre & (Y >= 56.5) & (Y < 57.0), T.CIEL[4])
    reflet(P, barre & (Y > 57.0), tab.derriere(), 56.5, force=0.32, etire=0.55)
    glace = barre & (np.abs(X - 40.0) < 1.4 + (Y - 56.0) * 0.16) & (Y < 71.0) & (hz(P.YI + int(p * 8), 0, 293) < 0.5)
    P.remplir(glace, J1)                                        # la colonne du soleil, jusque dans la barre
    P.remplir(glace & (np.abs(X - 40.0) < 1.0) & (Y < 63.0), J2)
    voile(P, barre & (Y > 73), T.ENCRE, 0.35)
    dallage(P, barre & (Y > 74.0) & (P.T < 0.45), 96.0, 50.0, N2, N1, larg=9.0, prof=1.2)   # le grain de la dalle d'écran
    # Le bouton de démarrage et les icônes épinglées, à gauche.
    P.rect(4, 59.5, 12, 9, N2)
    for (dx, dy, c0) in ((0, 0, C2), (4.4, 0, O2), (0, 3.6, J2), (4.4, 3.6, Q2)):
        P.rect(6 + dx, 61 + dy, 3.6, 2.8, c0)
    for i, c0 in enumerate((Q2, V4, O2)):
        P.rect(20 + i * 8, 61, 5.4, 5.4, N2)
        P.rect(21 + i * 8, 62, 3.4, 3.4, c0)
        if i == 0:
            P.rect(20 + i * 8, 67.4, 5.4, 0.6, C2)
    # La grande horloge : 13:37, le 7 qui penche. Ses chiffres bavent un peu de lumière sur la barre.
    hx, hy = 110.0, 60.5
    P.rect(hx - 4, hy - 2.5, 84, 19, N0)
    P.rect(hx - 4, hy - 2.5, 84, 0.6, N3)
    P.rect(hx - 4, hy + 16.0, 84, 0.5, ENCRE)
    for i in range(5):                                       # les segments éteints, en filigrane
        if i != 2:
            sept(P, hx + i * 15.6, hy, "8", N1, l=9.0, h=13.0, ep=P.ep(1.0))
    halo(P, hx + 38, hy + 7, 44, C1, 0.3, ry=12)
    vif = C3 if int(p * 8) % 5 else C2
    sept(P, hx, hy, "13:37", C1, l=9.0, h=13.0, ep=P.ep(1.3), pas=15.6, penche={4: 2.2})
    sept(P, hx, hy, "13:37", vif, l=9.0, h=13.0, ep=P.ep(0.7), pas=15.6, penche={4: 2.2})
    voile(P, (Y > hy + 16.6) & (Y < 80) & (X > hx) & (X < hx + 76), C1, 0.18)
    # Dans le coin : le son coupé, la batterie, un petit drapeau d'alerte.
    P.rect(98, 62, 3.0, 4.0, G4)
    P.poly([(101, 62), (104, 60), (104, 68), (101, 66)], G4)
    P.trait(105.2, 61.4, 107.6, 66.6, O2)
    P.rect(96, 70, 9.0, 4.4, G3)
    P.rect(105, 71.2, 0.8, 2.0, G3)
    P.rect(96.8, 70.8, 7.4, 2.8, N0)
    P.rect(96.8, 70.8, 2.0 + 0.8 * (int(p * 8) % 2), 2.8, O2)
    # ---- Seconde passe : la petite vie de l'écran.
    if int(p * 8) % 2:                                          # le curseur de texte de la fenêtre figée clignote encore
        P.rect(104.0 + 5 + 22.6, -10.0 + 39.0, 0.5, 3.0, N2)
    P.poly([(22.0, 22.0), (34.0, 21.0), (34.6, 32.0 + 0.5 * onde(p)), (23.0, 33.0)], J3)          # un pense-bête collé sur l'écran
    P.poly([(30.6, 32.4 + 0.5 * onde(p)), (34.6, 32.0 + 0.5 * onde(p)), (34.0, 29.0)], J1)
    for j in range(3):
        P.rect(24.0, 24.0 + j * 2.2, 8.0 - j * 2, 0.4, B2)
    pg.toile_araignee(P, 198.0, -16.0, 14.0, sens=(-1, 1), coul=T.CIEL[10])
    pg.araignee(P, 186.0, -16.0, 9.0, d=0.3)
    pg.papillon_de_nuit(P, 185.0, -10.0, 5.0, coul=BLANC)
    pg.souris(P, 22.0, 77.6, sens=1, coul=G3)
    if (p * 2) % 1.0 < 0.5:                                     # un pixel mort qui se rallume, parfois
        P.point(150.0, 44.0, C2)
    for i in range(6):                                          # la neige de l'écran : quelques pixels qui tombent
        t = (p + i / 6.0) % 1.0
        P.point(60 + 22 * i, -14 + 60 * t, T.CIEL[10])
    # Le cadre de l'écran : on est dedans. Coins arrondis, un liseré où le jour accroche, une étiquette collée.
    coin = lambda cx_, cy_: (np.hypot(X - cx_, Y - cy_) > 5.0) & ((X - cx_) * (96 - cx_) < 0) & ((Y - cy_) * (30 - cy_) < 0)
    cadre = (X < 2.6) | (X > 189.4) | (Y < -14.0) | coin(7.6, -9.0) | coin(184.4, -9.0)
    P.remplir(cadre, ENCRE)
    P.remplir(cadre & ((X < 0.8) | (X > 191.2) | (Y < -15.4)), N0)
    bord = ~cadre & (np.roll(cadre, 1, axis=1) | np.roll(cadre, 1, axis=0))
    P.remplir(bord, N2)
    P.remplir(cadre & (X < 2.6) & (X > 1.6) & (np.abs(Y - 20.0 - 6.0 * onde(p)) < 7.0), N1)       # un reflet glisse sur le montant
    P.poly([(183.0, 40.0), (192.0, 39.4), (192.0, 47.0), (183.6, 47.4 + 0.4 * onde(p, 0.4))], J2)   # une étiquette collée sur le bord
    P.poly([(183.0, 40.0), (192.0, 39.4), (192.0, 40.6), (183.0, 41.2)], J3)
    for j in range(2):
        P.rect(185.0, 42.6 + j * 1.8, 5.0 - j * 1.6, 0.4, B2)
    for i in range(7):                                          # des grains de poussière sur la vitre, devant tout
        P.point(20.0 + 24.0 * i + 3.0 * hz(i, 0, 294), 4.0 + 44.0 * hz(i, 1, 294) + 0.6 * onde(p, i * 0.14), BLANC)


# =====================================================================================================================
# Le Hall des Pas Comptés : un hall de gare immense, des guichets aux rideaux baissés (« Retour à 13 h 38 »), une file
# en serpentin, l'afficheur « 1 337 » (la clé), un banc de bois au premier plan.
# =====================================================================================================================
@decor("grande-panne", "hall-pas-comptes", soleil=(30.0, -40.0), tons=PANNE, nom="Le Hall des Pas Comptés", matiere=True)
def hall(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    # ---- La géométrie : une nef en perspective. Point de fuite (fx, fy) ; une profondeur d vaut 1 au ras du cadre et
    # DB au mur du fond ; sur un mur latéral, h va de HT (la naissance de la voûte) à HS (le sol).
    fx, fy = 96.0, 44.0
    DB, HT, HS = 2.6, -0.75, 0.6
    px_ = lambda d, cote: fx + cote * 104.0 / d
    py_ = lambda d, h: fy + h * 60.0 / d
    ax = np.abs(X - fx)
    dw = 104.0 / np.maximum(ax, 1e-3)
    hw = (Y - fy) * dw / 60.0
    mur = (ax >= 40.0) & (hw >= HT) & (hw <= HS)
    fond = (ax < 40.0) & (Y >= py_(DB, HT)) & (Y <= py_(DB, HS))
    df = 36.0 / np.maximum(Y - fy, 1e-3)
    uf = (X - fx) * df / 104.0
    sol = (Y > fy) & (df <= DB) & (np.abs(uf) <= 1.0)
    # La voûte en berceau : pour chaque pixel, à quelle profondeur dv et sous quel angle th on la touche.
    a_, b_ = X - fx, fy - Y
    qa = a_ * a_ / 104.0 ** 2 + b_ * b_ / 93.6 ** 2
    qb = -2 * 45.0 * b_ / 93.6 ** 2
    qc = 45.0 ** 2 / 93.6 ** 2 - 1
    dv = (-qb + np.sqrt(np.maximum(qb * qb - 4 * qa * qc, 0))) / (2 * np.maximum(qa, 1e-9))
    th = np.arctan2((b_ * dv - 45.0) / 93.6, a_ * dv / 104.0)
    voute = ~mur & ~fond & ~sol & (Y < fy) & (b_ * dv >= 45.0)
    lunette = voute & (dv > DB)
    berceau = voute & (dv <= DB)
    LUM = 2.15                                                  # l'angle d'où vient le jour (haut, à gauche)
    TRAVEES = [1.0, 1.21, 1.46, 1.77, 2.14, 2.6]
    # ---- Le ciel, dehors : on le voit à travers les carreaux clairs ; ses nuages passent.
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=70.0, haut=0.3, halo=0.36, disque=0)
    pg.cumulus(P, [(40, 4, 50, 9.0, 231, 9, 0.0), (130, -4, 44, 8.0, 232, 8, 0.4), (90, 18, 34, 6.0, 233, 7, 0.7)], dessous=-0.5)
    # ---- La verrière : fer peint et verre. Des arcs à chaque travée, des pannes qui fuient, des carreaux dépolis, clairs
    # ou sales ; le jour entre par la gauche.
    tab.plan("lointains", 0.2)
    ci = np.searchsorted(np.array(TRAVEES), dv)
    ki = np.floor(th / (math.pi / 12.0)).astype(np.int64)
    sous = np.floor((th / (math.pi / 12.0) - ki) * 2).astype(np.int64)       # deux carreaux par panne
    hc = hz(ci * 31 + ki, sous, 234)
    jour = 0.5 + 0.5 * np.cos(th - LUM)
    depoli = berceau & (hc < 0.62)
    P.rampe(depoli, 0.42 + 0.42 * jour + 0.3 * (hc - 0.3) + 0.1 * (pg.fbm(X / 6.0, Y / 4.0, 2, 235) - 0.5), [T.CIEL[6], T.CIEL[8], T.CIEL[10], T.CIEL[11], BLANC], 0.5)
    P.remplir(berceau & (hc > 0.9), E4)                                       # des carreaux jaunis, jamais remplacés
    voile(P, berceau & (hc > 0.9) & (pg.fbm(X / 2.0, Y / 2.0, 2, 236) > 0.5), E3, 0.6)
    casse = berceau & (hc > 0.62) & (hc < 0.66)                              # un carreau fêlé
    P.remplir(casse & (np.abs(((X * 0.7 + Y) % 5.0) - 2.5) < 0.3), T.CIEL[11])
    # Le fer : petits bois entre les carreaux, pannes, arcs (plus épais), faîtage ; l'arête tournée vers le jour est claire.
    fr = th / (math.pi / 12.0) - ki
    petit_bois = berceau & (np.abs(fr - 0.5) < 0.035)
    panne = berceau & ((fr < 0.07) | (fr > 0.93))
    arc = np.zeros(X.shape, dtype=bool)
    arc_clair = np.zeros(X.shape, dtype=bool)
    for t in TRAVEES[1:]:
        arc |= berceau & (np.abs(dv - t) < 0.022 * dv)
        arc_clair |= berceau & (dv - t > -0.022 * dv) & (dv - t < -0.008 * dv)
    faite = berceau & (np.abs(th - math.pi / 2) < 0.045)
    P.remplir(petit_bois, G3)
    P.remplir(panne, G1)
    P.remplir(panne & (fr > 0.93) & (th < LUM) | panne & (fr < 0.07) & (th >= LUM), G3)
    P.remplir(arc, N1)
    P.remplir(arc & arc_clair, G3)
    P.remplir(arc & (np.abs(((th * 14.0) % 1.0) - 0.5) < 0.12) & ~arc_clair, G2)     # les rivets
    P.remplir(faite, N1)
    P.remplir(faite & (th > math.pi / 2), G2)
    for t in TRAVEES[1:-1]:                                                  # des tirants de fer d'un mur à l'autre, et leurs lanternes
        yy = py_(t, HT) + 1.0 / t
        P.trait(px_(t, -1) + 2, yy, px_(t, 1) - 2, yy, N1)
        for cote in (-1, 1):
            lx_ = fx + cote * 46.0 / t
            P.trait(lx_, yy, lx_, yy + 5.0 / t, N1)
            vif = (p + 0.21 * t + 0.3 * cote) % 1.0 > 0.1
            P.ell(lx_, yy + 6.6 / t, 1.9 / t + 0.3, 2.2 / t + 0.3, J3 if vif else J1)
            if vif:
                halo(P, lx_, yy + 6.6 / t, 9.0 / t + 2, J2, 0.4)
    # Les ombres des nuages glissent sur le verre.
    passe = pg.fbm((X + 30.0 * p) / 34.0, Y / 16.0, 3, 237)
    voile(P, depoli & (passe > 0.6), T.CIEL[7], 0.35)
    # La brume de la distance : plus c'est loin, plus c'est pâle.
    voile(P, berceau, T.CIEL[10], np.clip((dv - 1.5) / 2.2, 0, 0.45))
    # ---- Le tympan du fond : une grande rosace en éventail, quelques carreaux de couleur ; elle est à contre-jour de
    # l'afficheur et l'auréole.
    yl = py_(DB, HT)
    rl = np.hypot((X - fx) / 40.0, (Y - yl) / 36.0)
    al = np.arctan2(yl - Y, X - fx)
    P.rampe(lunette, 0.6 + 0.3 * (1 - rl) + 0.1 * (pg.fbm(X / 5.0, Y / 4.0, 2, 238) - 0.5), [T.CIEL[8], T.CIEL[10], T.CIEL[11], BLANC], 0.5)
    sect = np.floor(al / (math.pi / 9.0)).astype(np.int64)
    anneau = np.searchsorted(np.array([0.34, 0.66, 0.9]), rl)
    hv = hz(sect, anneau, 239)
    for seuil, coul in ((0.12, J3), (0.22, C3), (0.3, O3), (0.36, V4)):
        P.remplir(lunette & (anneau == 2) & (hv < seuil) & (hv >= seuil - 0.1), coul)
    P.remplir(lunette & (anneau == 0), J3)
    P.remplir(lunette & (np.abs((al / (math.pi / 9.0)) - sect - 0.5) > 0.44), N1)
    for r0 in (0.34, 0.66, 0.9):
        P.remplir(lunette & (np.abs(rl - r0) < 0.022), N1)
    P.remplir(lunette & (rl > 0.94), E3)
    P.remplir(lunette & (rl > 0.97), E2)
    # ---- Le mur du fond, déjà pâli par la distance : corniche, frise de petites baies, arcade de guichets, deux passages.
    P.rampe(fond, 0.62 + 0.012 * (Y - yl) + 0.12 * (pg.fbm(X / 9.0, Y / 6.0, 3, 240) - 0.5), [E3, E4, E5, BLANC], 0.5)
    P.remplir(fond & (Y < yl + 1.0), BLANC)
    P.remplir(fond & (Y >= yl + 1.0) & (Y < yl + 1.6), E2)
    for i in range(11):                                                       # la frise de petites baies
        bx_ = fx - 35.0 + i * 7.0
        vif = hz(i, 0, 241) < 0.45 and (p + hz(i, 1, 241)) % 1.0 < 0.9
        P.rect(bx_ - 1.6, yl + 3.4, 3.2, 4.0, E2)
        P.rect(bx_ - 1.1, yl + 3.9, 2.2, 3.0, J3 if vif else N2)
    P.rect(fx - 40.0, yl + 9.0, 80.0, 0.7, E2)
    for i in range(7):                                                        # l'arcade des guichets du fond
        gx_ = fx - 27.0 + i * 9.0
        if i in (0, 6):                                                       # aux deux bouts : un passage vers un autre hall
            P.ell(gx_, 45.6, 3.4, 4.0, N1, cond=Y < 46.0)
            P.rect(gx_ - 3.4, 45.6, 6.8, 12.2, N1)
            P.rect(gx_ - 2.0, 48.0, 4.0, 9.8, N2)
            P.rect(gx_ - 1.0, 50.6, 2.0, 7.2, T.CIEL[4])
            P.point(gx_, 52.0, J3)
            continue
        P.ell(gx_, 46.6, 3.2, 3.6, E2, cond=Y < 47.0)
        P.rect(gx_ - 3.2, 46.6, 6.4, 8.4, E2)
        P.ell(gx_, 47.0, 2.5, 2.9, G2, cond=Y < 47.4)
        P.rect(gx_ - 2.5, 47.0, 5.0, 6.4, G2)
        for j in range(5):
            P.rect(gx_ - 2.5, 47.6 + j * 1.2, 5.0, 0.4, G3)
        P.rect(gx_ - 1.4, 49.4, 2.8, 1.8, BLANC)
        P.rect(gx_ - 0.8, 50.0, 1.6, 0.5, O2)
        P.rect(gx_ - 3.2, 53.4, 6.4, 1.2, B3)
        P.rect(gx_ - 3.2, 54.6, 6.4, 3.3, B2)
        P.point(gx_, 44.0, J3 if (p + 0.13 * i) % 1.0 > 0.1 else J1)
    for cote in (-1, 1):                                                      # deux tableaux des départs, lignes qui clignotent
        tx_ = fx + cote * 21.0
        P.rect(tx_ - 9.5, 36.2, 19.0, 6.2, N1)
        P.rect(tx_ - 9.0, 36.7, 18.0, 5.2, N0)
        for j in range(4):
            vif = (int(p * 8) + j + (cote > 0)) % 5 != 0
            P.rect(tx_ - 8.0, 37.3 + j * 1.2, 5.0 + 3.0 * hz(j, cote, 247), 0.5, J2 if vif else B1)
            P.rect(tx_ + 3.0, 37.3 + j * 1.2, 4.0, 0.5, O2 if j == 1 else C3)
    P.ell(fx, 36.4, 4.6, 4.6, B2)                                             # l'horloge du hall, sous l'afficheur
    P.ell(fx, 36.4, 3.8, 3.8, T.CREME)
    for k in range(12):
        P.point(fx + 3.1 * math.cos(k * math.pi / 6), 36.4 + 3.1 * math.sin(k * math.pi / 6), G1)
    P.trait(fx, 36.4, fx + 1.3, 34.9, ENCRE)                                  # 13 h 37
    P.trait(fx, 36.4, fx + 0.9 + 0.2 * (int(p * 8) % 2), 39.2, ENCRE)
    voile(P, fond, T.CIEL[11], 0.3)
    halo(P, fx, yl - 12.0, 64.0, BLANC, 0.5, ry=44)
    # ---- Les murs latéraux : celui de gauche dans l'ombre, celui de droite au jour ; cinq guichets de chaque côté.
    tab.plan("moyen", 0.5)
    cote_px = np.where(X < fx, -1.0, 1.0)
    v = 0.46 + 0.24 * cote_px - 0.16 * hw + 0.16 * (pg.fbm(X / 10.0, Y / 7.0, 3, 242) - 0.5)
    P.rampe(mur, v, [E1, E2, E3, E4, E5], 0.5)
    assise = np.floor(hw * 11.0)
    joint = (hw * 11.0 - assise < 0.07) | (((np.log(dw) * 9.0 + 0.5 * (assise % 2)) % 1.0) < 0.05)
    voile(P, mur & joint & (hw < 0.2), E2, 0.45)
    voile(P, mur & (hz(assise, np.floor(np.log(dw) * 9.0 + 0.5 * (assise % 2)), 246) > 0.8) & (hw < 0.2), E3, 0.3)       # des pierres plus sombres
    P.remplir(mur & (hw < HT + 0.035), BLANC)                                 # la corniche et son ombre
    P.remplir(mur & (hw >= HT + 0.035) & (hw < HT + 0.07), E1)
    P.remplir(mur & (np.abs(hw + 0.6) < 0.012), E2)
    for cote in (-1, 1):
        clair, moyen, sombre = (E4, E3, E2) if cote > 0 else (E3, E2, E1)
        for i in range(5):
            d0, d1 = TRAVEES[i] * 1.03, TRAVEES[i + 1] * 0.94
            dm = (d0 + d1) / 2
            k = 1.0 / dm
            q = lambda d, h: (px_(d, cote), py_(d, h))
            # Le pilastre entre deux travées, son arête éclairée, son chapiteau.
            P.poly([q(d1, HT + 0.07), q(TRAVEES[i + 1] * 1.03, HT + 0.07), q(TRAVEES[i + 1] * 1.03, HS), q(d1, HS)], clair)
            P.poly([q(d1, HT + 0.07), q(d1 * 1.012, HT + 0.07), q(d1 * 1.012, HS), q(d1, HS)], BLANC if cote > 0 else moyen)
            P.poly([q(d1 * 0.985, HT + 0.07), q(TRAVEES[i + 1] * 1.045, HT + 0.07), q(TRAVEES[i + 1] * 1.045, HT + 0.12), q(d1 * 0.985, HT + 0.12)], clair)
            # La baie : une arche, un renfoncement sombre, le rideau de fer baissé (pas tout à fait).
            baie = [q(d0, -0.4), q(d0 + (d1 - d0) * 0.22, -0.5), q(d1 - (d1 - d0) * 0.22, -0.5), q(d1, -0.4), q(d1, 0.22), q(d0, 0.22)]
            P.poly(baie, N1)
            P.poly([q(d0, -0.4), q(d0 + (d1 - d0) * 0.22, -0.5), q(d1 - (d1 - d0) * 0.22, -0.5), q(d1, -0.4), q(d1, -0.37), q(d0, -0.37)], N0)
            n = 12
            for j in range(n):
                hj = -0.37 + (0.52 if (i == 2 and cote < 0) else 0.55) * (j + 0.5) / n      # un rideau est resté entrouvert
                P.trait(q(d0, hj)[0], q(d0, hj)[1], q(d1, hj)[0], q(d1, hj)[1], (G3 if cote > 0 else G2) if j % 2 else G1, max(1, P.ep(0.5 * k)))
            P.trait(q(d0, 0.17)[0], q(d0, 0.17)[1], q(d1, 0.17)[0], q(d1, 0.17)[1], G4)
            P.poly([q(d0, -0.4), q(d0 * 1.02, -0.4), q(d0 * 1.02, 0.22), q(d0, 0.22)], sombre)                 # l'épaisseur du mur
            # Le néon jaune au-dessus, le numéro du guichet, le petit panneau « retour à 13 h 38 » qui se balance.
            allume = (p + 0.17 * i + (0.4 if cote > 0 else 0)) % 1.0 > 0.12
            P.trait(q(d0 * 1.03, -0.56)[0], q(d0 * 1.03, -0.56)[1], q(d1 * 0.97, -0.56)[0], q(d1 * 0.97, -0.56)[1], J3 if allume else J1, max(1, P.ep(0.7 * k)))
            if allume:
                halo(P, q(dm, -0.5)[0], q(dm, -0.42)[1], 13.0 * k + 2, J2, 0.45)
            nx_, ny_ = q(dm, -0.66)
            P.rect(nx_ - 2.4 * k, ny_ - 1.4 * k, 4.8 * k, 2.8 * k, N0)
            P.point(nx_ - 0.8 * k, ny_, J2)
            P.point(nx_ + 0.8 * k, ny_, J2 if (i + (cote > 0)) % 2 else J3)
            bal = 0.5 * k * onde(p, 0.19 * i + 0.3 * cote)
            sx_, sy_ = q(dm, -0.22)
            sw, sh = 8.5 * k, 6.5 * k
            P.trait(sx_, q(dm, -0.37)[1], sx_ + bal, sy_, G4)
            P.rect(sx_ - sw / 2 + bal, sy_, sw, sh, BLANC)
            P.rect(sx_ - sw / 2 + bal, sy_ + sh - 0.5 * k - 0.2, sw, 0.5 * k + 0.2, E3)
            P.ell(sx_ - sw * 0.22 + bal, sy_ + sh * 0.46, sh * 0.3, sh * 0.3, O2)                              # une horloge
            P.trait(sx_ - sw * 0.22 + bal, sy_ + sh * 0.46, sx_ - sw * 0.22 + bal, sy_ + sh * 0.26, BLANC)
            P.rect(sx_ + sw * 0.05 + bal, sy_ + sh * 0.34, sw * 0.3, max(0.4, 0.14 * sh), ENCRE)                # une flèche
            P.rect(sx_ + sw * 0.05 + bal, sy_ + sh * 0.62, sw * 0.2, max(0.4, 0.1 * sh), G3)
            # Le comptoir : tablette de bois, panneaux, plinthe ; dessus, ce qu'on y a laissé.
            P.poly([q(d0 * 0.99, 0.2), q(d1 * 1.01, 0.2), q(d1 * 1.01, 0.26), q(d0 * 0.99, 0.26)], B3)
            P.trait(q(d0 * 0.99, 0.2)[0], q(d0 * 0.99, 0.2)[1], q(d1 * 1.01, 0.2)[0], q(d1 * 1.01, 0.2)[1], E4)
            P.poly([q(d0, 0.26), q(d1, 0.26), q(d1, HS), q(d0, HS)], B2 if cote > 0 else B1)
            P.poly([q(d0 * 1.03, 0.3), q(d1 * 0.97, 0.3), q(d1 * 0.97, 0.52), q(d0 * 1.03, 0.52)], B3 if cote > 0 else B2)
            P.poly([q(d0 * 1.05, 0.32), q(d1 * 0.95, 0.32), q(d1 * 0.95, 0.5), q(d0 * 1.05, 0.5)], B2 if cote > 0 else B1)
            P.poly([q(d0, 0.55), q(d1, 0.55), q(d1, HS), q(d0, HS)], G2)
            ox, oy = q(dm, 0.2)
            objet = (i + (2 if cote > 0 else 0)) % 5
            if objet == 0:                                                    # une sonnette
                P.ell(ox, oy - 1.2 * k, 2.2 * k, 1.4 * k, J2, cond=Y < oy)
                P.point(ox, oy - 2.8 * k, J3)
            elif objet == 1:                                                  # une pile de formulaires
                for j in range(4):
                    P.rect(ox - 3.0 * k, oy - (j + 1) * 0.9 * k, 6.0 * k, 0.9 * k, BLANC if j % 2 else E5)
            elif objet == 2:                                                  # une plante verte (sarcelle) qui a soif
                P.rect(ox - 1.4 * k, oy - 2.6 * k, 2.8 * k, 2.6 * k, O1)
                for j in range(4):
                    P.trait(ox, oy - 2.6 * k, ox + (j - 1.5) * 1.6 * k + 0.2 * onde(p, 0.1 * j), oy - 7.0 * k, T.S2 if j % 2 else T.S1)
            elif objet == 3:                                                  # un tampon sur son encrier
                P.rect(ox - 1.8 * k, oy - 1.0 * k, 3.6 * k, 1.0 * k, V2)
                P.rect(ox - 0.6 * k, oy - 4.2 * k, 1.2 * k, 3.2 * k, B3)
            else:                                                             # un gobelet oublié
                P.rect(ox - 1.0 * k, oy - 2.6 * k, 2.0 * k, 2.6 * k, E5)
                P.rect(ox - 1.0 * k, oy - 2.6 * k, 2.0 * k, 0.6 * k, O2)
    yeux_x, yeux_y = (px_(1.58, -1), py_(1.58, 0.19))                         # dans la baie entrouverte : quelqu'un regarde
    pg.yeux(P, yeux_x - 1.0, yeux_y - 1.2, coul=J3, d=0.4)
    voile(P, mur, T.CIEL[11], np.clip((dw - 1.5) / 2.4, 0, 0.4))               # la distance pâlit les murs aussi
    voile(P, mur & (X < fx), N2, 0.22)                                         # le mur de gauche, à l'ombre
    voile(P, mur & (X < fx) & (hw > -0.1), N2, 0.15)
    carreau = (((np.log(dw) * 5.0 + hw * 1.6) % 1.0) < 0.62) & (((np.log(dw) * 5.0 - hw * 2.4) % 1.0) > 0.08)
    voile(P, mur & (X > fx) & carreau & (hw > -0.7) & (hw < 0.3), BLANC, 0.4, lumiere=True)
    # ---- Le sol : un dallage de marbre en damier, veiné, ciré ; une bordure de pierre grise, un filet de laiton, une
    # allée centrale. Il fuit vers le fond et pâlit avec lui.
    cu, cz = np.floor(uf * 5.0 + 50.0), np.floor(df * 7.0)
    pair = ((cu + cz) % 2 == 0)
    veine = pg.fbm(uf * 14.0 + cz * 3.1, df * 9.0 + cu * 1.7, 3, 243)
    vs = 0.4 + 0.24 * pair + 0.22 * (veine - 0.5) + 0.1 * uf - 0.1 * np.abs(uf)
    P.rampe(sol, vs, [E1, E2, E3, E4, E5], 0.4)
    P.remplir(sol & (np.abs(veine - 0.5) < 0.012) & pair, E3)                  # les veines du marbre clair
    P.remplir(sol & (np.abs(veine - 0.62) < 0.01) & ~pair, E2)
    fu, fz = uf * 5.0 + 50.0 - cu, df * 7.0 - cz
    P.remplir(sol & ((fu < 0.035 * df) | (fz < 0.05)), E2)                     # les joints
    bordure = sol & (np.abs(uf) > 0.88)
    P.rampe(bordure, 0.5 + 0.3 * (pg.fbm(uf * 30.0, df * 6.0, 2, 244) - 0.5) + 0.1 * cote_px, [G2, G3, G4], 0.4)
    P.remplir(sol & (np.abs(np.abs(uf) - 0.86) < 0.012), J1)                   # le filet de laiton
    P.remplir(sol & (np.abs(np.abs(uf) - 0.86) < 0.005), J2)
    allee = sol & (np.abs(uf) < 0.1)
    los = (np.abs(((df * 7.0) % 1.0) - 0.5) + np.abs(uf) * 5.0 < 0.42)
    P.remplir(allee, E4)
    P.remplir(allee & los, G3)
    P.remplir(sol & (np.abs(np.abs(uf) - 0.1) < 0.008), J1)
    voile(P, sol, T.CIEL[11], np.clip((df - 1.5) / 1.6, 0, 0.5))                # la distance
    # Le reflet du mur du fond dans le marbre ciré ; la flaque de lumière orange de l'afficheur ; les néons des guichets.
    reflet(P, sol & (ax < 44.0) & (Y < py_(DB, HS) + 9.0), tab.derriere(), py_(DB, HS), force=0.55, etire=0.8, ondule=0.0)
    lueur_aff = 0.8 if int(p * 8) % 4 else 1.0
    ell_aff = np.hypot((X - fx) / 40.0, (Y - 69.0) / 9.0)
    voile(P, sol & (ell_aff < 1.0), O2, 0.5 * lueur_aff * (1 - ell_aff))
    for i in range(4):                                                        # les quatre chiffres, en traînées dans le marbre ciré
        tx_ = fx - 20.0 + i * 13.4
        tr_ = sol & (np.abs(X - tx_ - (X - fx) * 0.0) < (1.2 if i == 0 else 3.6)) & (Y > 62.5) & (Y < 76.5) & ((P.YI + int(p * 8)) % 3 != 0)
        P.remplir(tr_ & (hz(P.YI, P.XI // 2, 248 + i) < 0.75 * lueur_aff * np.clip(1.0 - np.abs(Y - 68.5) / 8.0, 0, 1)), O2)
        P.remplir(tr_ & (np.abs(X - tx_) < 0.8) & (hz(P.YI, 0, 252 + i) < 0.6) & (np.abs(Y - 68.0) < 5.0), O3)
    eclat = sol & (ell_aff < 1.0) & (hz(P.YI, (P.XI + P.YI % 2 * 2) // 4, 256) < 0.3 * lueur_aff * (1 - ell_aff))
    P.remplir(eclat, O1)                                                      # et des éclats orange épars autour
    voile(P, sol & (np.hypot((X - fx) / 26.0, (Y - 68.0) / 5.0) < 1.0), O2, 0.3 * lueur_aff)
    for cote in (-1, 1):
        for i in range(5):
            dm = (TRAVEES[i] * 1.03 + TRAVEES[i + 1] * 0.94) / 2
            if (p + 0.17 * i + (0.4 if cote > 0 else 0)) % 1.0 > 0.12:
                gx_, gy_ = px_(dm, cote) - cote * 9.0 / dm, py_(dm, HS) + 1.0 / dm
                voile(P, sol & (np.hypot((X - gx_) / (11.0 / dm), (Y - gy_) / (3.4 / dm)) < 1.0), J2, 0.4, lumiere=True)
    # ---- Le jour : trois rais tombent de la verrière, à gauche, et posent leurs carreaux de lumière sur le dallage.
    for i, (x0, largeur, y_sol) in enumerate(((44.0, 13.0, 66.0), (70.0, 10.0, 62.0), (22.0, 15.0, 73.0))):
        pg.rai(P, x0, -16.0, y_sol, largeur, 0.36, BLANC, 0.46, 16, 245 + i)
        cx_ = x0 + (y_sol + 16.0) * 0.36
        tache = sol & (np.abs(X - cx_ - (Y - y_sol) * 1.6) < largeur * 0.8) & (np.abs(Y - y_sol) < 2.6 + 0.02 * y_sol)
        voile(P, tache, BLANC, 0.6, lumiere=True)
        voile(P, tache & (((X - (Y - y_sol) * 1.6) % (largeur * 0.4)) < 0.6), E4, 0.5)                          # l'ombre des petits bois
    # ---- L'afficheur « 1 337 » : suspendu à sa poutrelle, orange ; c'est lui qu'on regarde.
    axb, ayb, awb, ahb = 66.0, 6.0, 60.0, 24.0
    P.rect(axb - 6.0, -16.0, awb + 12.0, 2.0, N1)                              # la poutrelle en treillis
    for x in np.arange(axb - 6.0, axb + awb + 6.0, 6.0):
        P.trait(x, -14.0, x + 3.0, -10.6, N1)
        P.trait(x + 3.0, -10.6, x + 6.0, -14.0, N1)
    P.rect(axb - 6.0, -10.6, awb + 12.0, 1.2, N1)
    P.rect(axb - 6.0, -10.6, awb + 12.0, 0.4, G3)
    for dx in (8.0, 52.0):
        P.rect(axb + dx, -9.4, 1.4, 14.0, G1)
        P.rect(axb + dx, -9.4, 0.5, 14.0, G3)
    P.courbe([(axb + 30.0, -9.4), (axb + 34.0, -2.0), (axb + 30.0, 4.6)], ENCRE, 1)                             # son câble
    P.poly([(axb + awb + 1.5, ayb - 1.5), (axb + awb + 5.0, ayb + 0.5), (axb + awb + 5.0, ayb + ahb + 0.5), (axb + awb + 1.5, ayb + ahb + 1.5)], G0)   # son flanc
    P.rect(axb - 1.5, ayb - 1.5, awb + 3, ahb + 3, G1)
    P.rect(axb - 1.5, ayb - 1.5, awb + 3, 0.6, G4)
    P.rect(axb - 1.5, ayb - 1.5, 0.6, ahb + 3, G3)
    P.rect(axb, ayb, awb, ahb, ENCRE)
    P.remplir((X > axb) & (X < axb + awb) & (Y > ayb) & (Y < ayb + ahb) & (P.XI % 2 == 0) & (P.YI % 2 == 0), B1)   # la trame des diodes
    for i in range(4):                                                        # les segments éteints, en filigrane
        sept(P, axb + 5.5 + i * 13.4, ayb + 4.5, "8", B1, l=9.0, h=15.0, ep=P.ep(1.4))
    halo(P, axb + awb / 2, ayb + ahb / 2, 40, O1, 0.5 * lueur_aff, ry=18)
    sept(P, axb + 5.5, ayb + 4.5, "1337", K1, l=9.0, h=15.0, ep=P.ep(2.0), pas=13.4)
    sept(P, axb + 5.5, ayb + 4.5, "1337", O2, l=9.0, h=15.0, ep=P.ep(1.4), pas=13.4)
    if int(p * 8) % 4:
        sept(P, axb + 5.5, ayb + 4.5, "1337", O3, l=9.0, h=15.0, ep=P.ep(0.5), pas=13.4)
    for i in range(6):                                                        # des voyants courent sous les chiffres
        voyant(P, axb + 6 + i * 9.6, ayb + ahb - 2.0, J3, B1, d=i / 6.0, part=0.3, r=0.6)
    P.rect(axb + 6.0, ayb + ahb + 1.5, awb - 12.0, 2.4, N1)                    # le bandeau : un pictogramme de file, une flèche
    for i in range(5):
        P.rect(axb + 10.0 + i * 3.0, ayb + ahb + 2.1, 1.6, 1.2, E5)
    P.trait(axb + 40.0, ayb + ahb + 2.7, axb + 50.0, ayb + ahb + 2.7, O2)
    # ---- La file en serpentin : poteaux de laiton, cordons, ceux qui attendent debout ; leurs ombres vers la droite.
    for rang, dq in enumerate((2.3, 1.95, 1.62)):
        k = 1.0 / dq * 1.6
        yq = py_(dq, HS)
        x0, x1 = fx - 72.0 / dq, fx + 72.0 / dq
        nb = 6 + rang
        for i in range(nb + 1):
            x = x0 + (x1 - x0) * i / nb
            voile(P, sol & (np.hypot((X - x - 2.4 * k) / (3.0 * k), (Y - yq - 0.2) / (0.5 * k)) < 1.0), E1, 0.45)
            if i < nb:
                P.courbe([(x, yq - 4.4 * k), (x + (x1 - x0) / nb / 2, yq - 3.0 * k), (x + (x1 - x0) / nb, yq - 4.4 * k)], O2 if rang else O1, 1)
            P.rect(x - 0.4 * k, yq - 5.0 * k, 0.9 * k, 5.0 * k, J1)
            P.rect(x - 0.4 * k, yq - 5.0 * k, 0.35 * k, 5.0 * k, J3)
            P.ell(x, yq - 5.2 * k, 0.8 * k, 0.8 * k, J2)
            P.ell(x, yq, 1.2 * k, 0.4 * k, G1)
        for i in range(nb * 2):
            x = x0 + 3 + (x1 - x0 - 6) * i / (nb * 2 - 1)
            if rang == 2 and (26 < x < 66 or 128 < x < 170):
                continue                                                      # la place de Pilou et de son interlocuteur
            hgt = (3.8 + 1.2 * hz(i, rang, 232)) * k
            dy = 0.3 * k * (1 if int(p * 8 + i) % 5 == 0 else 0)
            voile(P, sol & (np.hypot((X - x - 1.8 * k) / (2.2 * k), (Y - yq - 0.2) / (0.4 * k)) < 1.0), E1, 0.45)
            c0 = (BLANC, E5, C3, E5)[(i + rang) % 4]
            P.rect(x - 0.8 * k, yq - hgt - dy, 1.7 * k, hgt, c0)
            P.rect(x + 0.5 * k, yq - hgt - dy, 0.4 * k, hgt, E3 if c0 != C3 else C1)       # leur côté à l'ombre
            P.point(x - 0.4 * k, yq - hgt * 0.72 - dy, ENCRE)
            P.point(x + 0.2 * k, yq - hgt * 0.72 - dy, ENCRE)
            if (i + rang * 3) % 7 == 0:
                P.rect(x - 1.4 * k, yq - hgt * 0.5 - dy, 0.8 * k, 1.0 * k, O2)              # un ticket, à la main
    # Un moineau vole sous la verrière ; un avion de papier plane ; un papillon tourne près de la rosace.
    t = (p + 0.3) % 1.0
    mx_, my_ = 30.0 + 130.0 * t, 14.0 + 10.0 * math.sin(t * 6.283 * 1.5)
    aile = onde(p * 2)
    P.trait(mx_ - 1.6, my_ - 0.8 * aile, mx_, my_, B1)
    P.trait(mx_, my_, mx_ + 1.6, my_ - 0.8 * aile, B1)
    pg.avion_papier(P, 20.0, 34.0, 172.0, 46.0, d=0.1)
    pg.papillon_de_nuit(P, 140.0, 4.0, 8.0, coul=T.CREME, d=0.5)
    poussiere(P, 20, -6, 150, 60, 30, BLANC, 237)
    # ---- Premier plan : deux colonnes de fonte qui cadrent, la lampe-globe, le banc, ce qui traîne.
    tab.plan("premier", 1.0)
    for (cx_, cote) in ((4.0, 1), (188.0, -1)):
        col = (np.abs(X - cx_) < 5.0 + 0.6 * np.cos((Y - 30.0) / 30.0))
        uc = (X - cx_) / 5.6
        P.rampe(col, 0.34 + 0.3 * uc * (-1 if cx_ < fx else 1) * -1 + 0.2 * (uc * uc) + 0.06 * np.sin(X * 3.0), [ENCRE, N0, N1, G1, G2], 0.4)
        P.remplir(col & (np.abs(uc - 0.55 * cote) < 0.12), G3)                 # l'arête que le jour touche
        for yb in (60.0, 64.0, 6.0, 2.0):                                      # bagues, base et chapiteau
            P.rect(cx_ - 6.8, yb, 13.6, 1.6, N0)
            P.rect(cx_ - 6.8, yb, 13.6, 0.5, G2)
        P.poly([(cx_ - 8.0, 66.0), (cx_ + 8.0, 66.0), (cx_ + 9.0, 80.0), (cx_ - 9.0, 80.0)], N0)
        P.rect(cx_ - 8.0, 66.0, 16.0, 0.6, G2)
        P.poly([(cx_ - 5.6, 2.0), (cx_ + 5.6, 2.0), (cx_ + 10.0, -8.0), (cx_ - 10.0, -8.0)], N0)
        for j in range(5):                                                    # les volutes de la console
            P.courbe([(cx_ + cote * 4.0, -2.0 - j * 2.6), (cx_ + cote * (9.0 + j * 2.0), -5.0 - j * 2.2), (cx_ + cote * (11.0 + j * 2.4), -16.0)], N0, P.ep(0.7))
        voile(P, sol & (np.abs(Y - 77.0 - (X - cx_) * 0.06) < 2.2) & (X > cx_) & (X < cx_ + 60.0), E1, 0.4)      # son ombre sur le dallage
    lgx, lgy = 20.0, 4.0                                                      # la lampe-globe, à la console de gauche
    P.courbe([(7.0, -6.0), (15.0, -8.0), (lgx, -3.0)], N0, P.ep(0.8))
    P.trait(lgx, -3.0, lgx + 0.3 * onde(p), lgy - 3.2, N0)
    halo(P, lgx, lgy, 20.0, J2, 0.5)
    P.ell(lgx + 0.3 * onde(p), lgy, 3.4, 3.4, J3 if int(p * 8) % 7 else J2)
    P.ell(lgx - 0.8 + 0.3 * onde(p), lgy - 0.9, 1.4, 1.4, BLANC)
    P.rect(lgx - 1.4 + 0.3 * onde(p), lgy - 3.6, 2.8, 0.8, N0)
    pg.papillon_de_nuit(P, lgx, lgy, 5.0, coul=T.CREME)
    # Le banc de bois, au milieu, bas : son ombre, son reflet ciré, le journal oublié, le ballon noué.
    bx0, bx1, by = 74.0, 120.0, 72.0
    voile(P, (X > bx0 + 4) & (X < bx1 + 12) & (Y > 77.0) & (Y < 79.8) & (P.a >= 0), E1, 0.5)
    for x in (bx0 + 3, bx1 - 5):
        P.rect(x, by, 2.4, 7.0, B1)
        P.rect(x, by, 0.8, 7.0, B3)
    P.rect(bx0, by - 1.8, bx1 - bx0, 2.6, B2)
    P.rect(bx0, by - 1.8, bx1 - bx0, 0.8, B3)
    P.rect(bx0, by - 1.8, bx1 - bx0, 0.3, E4)
    P.rect(bx0, by + 0.6, bx1 - bx0, 0.4, B1)
    for x in np.arange(bx0 + 6, bx1, 7.5):
        P.trait(x, by - 1.0, x + 2.0, by - 1.0, B1)
    P.rect(bx0 + 3, by - 8.0, bx1 - bx0 - 6, 1.6, B2)
    P.rect(bx0 + 3, by - 8.0, bx1 - bx0 - 6, 0.5, E4)
    P.rect(bx0 + 3, by - 5.2, bx1 - bx0 - 6, 1.4, B2)
    P.rect(bx0 + 3, by - 5.2, bx1 - bx0 - 6, 0.4, B3)
    P.rect(bx0 + 4, by - 8.0, 1.2, 6.4, B1)
    P.rect(bx1 - 5.2, by - 8.0, 1.2, 6.4, B1)
    papiers(P, 100.0, by - 1.8, 7.0, 3, 235)
    bal = 0.8 * onde(p)
    P.trait(118.0, by - 7.6, 119.0 + bal, 52.0, G1)
    P.ell(119.0 + bal, 47.6, 3.4, 4.4, O2)
    P.ell(118.0 + bal, 46.0, 1.3, 1.7, O3)
    P.point(119.0 + bal, 52.2, O1)
    # Le distributeur de tickets : il en sort un, qui rentre ; d'autres sont tombés.
    dx_ = 176.0
    voile(P, (X > dx_ + 13) & (X < dx_ + 22) & (Y > 76.0) & (P.a >= 0), E1, 0.4)
    P.rect(dx_, 50.0, 13.0, 28.0, G2)
    P.rampe((X > dx_) & (X < dx_ + 13.0) & (Y > 50.0) & (Y < 78.0), 0.3 + 0.5 * (dx_ + 13.0 - X) / 13.0, [G1, G2, G3, G4], 0.4)
    P.rect(dx_, 50.0, 13.0, 0.8, G4)
    P.rect(dx_ + 2.6, 52.6, 7.8, 5.0, ENCRE)
    sept(P, dx_ + 3.2, 53.4, "1338", O2, l=1.2, h=3.2, ep=1, pas=1.9)
    P.ell(dx_ + 6.5, 63.0, 2.6, 2.6, O1)
    P.ell(dx_ + 6.2, 62.6, 1.8, 1.8, O2)
    P.point(dx_ + 5.4, 61.8, O3)
    P.rect(dx_ + 3.0, 68.0, 7.0, 1.0, ENCRE)
    P.rect(dx_ + 4.4, 68.4, 4.0, 2.2 + 0.6 * onde(p), BLANC)
    tickets(P, dx_ + 5.0, 70.0, 79.5, 3, 236)
    # La fuite de la verrière et son seau ; la valise oubliée ; les pigeons ; la souris.
    P.poly([(124.0, 71.0), (131.0, 71.0), (130.0, 78.0), (125.0, 78.0)], G3)
    P.rect(123.6, 70.4, 7.8, 1.0, G4)
    P.ell(127.5, 70.9, 3.0, 0.5, C3)
    pg.goutte(P, 127.5, -10.0, 70.9, coul=C3, d=0.2, flaque=BLANC)
    P.rect(12.0, 68.0, 10.0, 8.0, B2)
    P.rect(12.0, 68.0, 10.0, 1.0, B3)
    P.rect(12.0, 71.6, 10.0, 0.6, B1)
    P.rect(15.4, 66.2, 3.2, 1.8, B1)
    P.poly([(22.0, 69.0), (24.8, 69.4 + 0.5 * onde(p, 0.3)), (24.4, 71.6 + 0.5 * onde(p, 0.3)), (22.0, 71.0)], BLANC)
    for i, (x, sens) in enumerate(((60.0, 1), (66.5, -1))):
        picore = int(p * 8 + i * 3) % 4 == 0
        voile(P, (np.hypot((X - x - 1.6) / 3.0, (Y - 78.4) / 0.5) < 1.0) & (P.a >= 0), E1, 0.45)
        P.ell(x, 76.8, 2.4, 1.5, G3)
        P.ell(x - sens * 0.8, 77.1, 1.5, 0.9, G4)
        P.poly([(x - sens * 2.0, 76.6), (x - sens * 4.0, 75.8), (x - sens * 2.2, 77.8)], G2)
        hx_, hy_ = x + sens * 2.1, 77.0 if picore else 75.0
        P.ell(hx_, hy_, 1.0, 1.0, V3)
        P.point(hx_ + sens * 0.3, hy_ - 0.3, ENCRE)
        P.rect(min(hx_ + sens * 0.9, hx_ + sens * 1.8), hy_ + 0.1, 0.9, 0.5, O2)
        P.trait(x, 78.2, x, 79.2, O1)
    pg.souris(P, 140.0, 78.6, sens=-1, coul=G3)
    voile(P, (Y > 78.6) & (P.a >= 0), E1, 0.25)


# =====================================================================================================================
# Le pied de la Tour du tampon : une tour de pierre grise qui se perd dans la brume (la clé), la file enroulée trois
# fois autour de sa base, une porte basse gardée par un tabouret trop petit, la lumière jaune des néons.
# =====================================================================================================================
@decor("grande-panne", "tour-tampon", soleil=(30.0, -30.0), tons=PANNE, nom="Le pied de la Tour du tampon", matiere=True)
def tour_tampon(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    cx = 96.0
    C = T.CIEL
    # ---- Le ciel : un jour gris-bleu, des bancs de nuages en volumes ; la lumière vient d'en haut à gauche.
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=74.0, haut=0.2, halo=0.34, disque=0)
    pg.cumulus(P, [(26, 4, 74, 12.0, 260, 10, 0.0), (150, -6, 84, 13.0, 261, 11, 0.3), (100, 26, 96, 9.0, 262, 9, 0.6),
                   (8, 42, 66, 7.0, 263, 7, 0.8), (178, 38, 64, 8.0, 264, 7, 0.5)], dessous=-0.4)
    brume = lambda y0, ep, g, f=0.55, ton=7: voile(P, np.abs(Y - y0 - 3 * np.sin(X / 23.0 + g)) < ep * (0.6 + 0.8 * pg.fbm(
        (X + 2.0 * onde(p, g * 0.1)) / 26.0, Y / 5.0, 3, 240 + g)), C[ton], f * 0.8)
    # ---- Les autres tours de l'administration : trois rangs, de plus en plus pâles et bleus en s'éloignant.
    tab.plan("lointains", 0.2)
    rangs = (([(26, 7, 30, 0), (54, 5, 38, 1), (74, 6, 33, 2), (120, 5, 40, 0), (138, 8, 28, 1), (162, 6, 36, 2)], 8),
             ([(8, 12, 14, 1), (44, 9, 24, 2), (150, 11, 18, 0), (186, 10, 26, 1)], 6),
             ([(22, 13, 2, 2), (170, 15, -6, 0)], 4))
    for r, (tours, b) in enumerate(rangs):
        tons_r = [C[max(b - 2, 0)], C[b - 1], C[b], C[min(b + 1, 11)], C[min(b + 2, 11)]]
        for i, (x, w, top, style) in enumerate(tours):
            dm = w / 2 * (1 + (Y - top) / 300.0)
            m = (np.abs(X - x) < dm) & (Y > top)
            uu = (X - x) / np.maximum(dm, 1e-3)
            P.rampe(m, 0.62 - 0.36 * uu - 0.1 * uu * uu + 0.004 * (Y - top) + 0.12 * (pg.fbm(X / 4.0, Y / 3.0, 2, 265 + r) - 0.5), tons_r, 0.5)
            P.remplir(m & (uu < -0.82), tons_r[4])                              # l'arête au jour
            if r > 0:
                P.remplir(m & (((Y - top) % 7.0) < 0.5), tons_r[1])             # les corniches d'étage
                P.remplir(m & (((Y - top) % 7.0) > 0.5) & (((Y - top) % 7.0) < 1.0) & (uu > -0.8), tons_r[0])
            if style == 0:                                                      # créneaux
                for k in range(int(w // 2) + 1):
                    P.rect(x - w / 2 + k * 2.2, top - 1.6, 1.2, 1.6, tons_r[2])
                P.rect(x - w / 2 - 0.8, top, w + 1.6, 1.0, tons_r[1])
            elif style == 1:                                                    # toit pointu et sa hampe
                P.poly([(x - w / 2 - 1, top), (x + w / 2 + 1, top), (x, top - w * 0.9)], tons_r[1])
                P.poly([(x - w / 2 - 1, top), (x, top), (x, top - w * 0.9)], tons_r[3])
                P.trait(x, top - w * 0.9, x, top - w * 0.9 - 3.0, tons_r[0])
            else:                                                               # une citerne sur ses pattes
                P.rect(x - w * 0.3, top - 2.0, 0.5, 2.0, tons_r[0])
                P.rect(x + w * 0.25, top - 2.0, 0.5, 2.0, tons_r[0])
                P.ell(x, top - 4.4, w * 0.42, 2.8, tons_r[2])
                P.ell(x - w * 0.12, top - 5.0, w * 0.2, 1.4, tons_r[4])
                P.rect(x - w / 2 - 0.8, top, w + 1.6, 1.0, tons_r[1])
            for j in range(8):                                                  # les lucarnes ; certaines veillent
                if hz(i + 10 * r, j, 241) < 0.6 and top + 5 + j * 7 < 72:
                    vif = (p + hz(i + 10 * r, j, 242)) % 1.0 < 0.8
                    wx = x - w * 0.25 + (j % 2) * w * 0.3
                    P.rect(wx, top + 5 + j * 7, 1.0 + 0.2 * r, 1.6 + 0.3 * r, (J3 if r else J2) if vif else tons_r[0])
        if r == 1:                                                              # une passerelle à arches, de tour en tour
            P.rect(44, 39.4, 106, 1.2, C[5])
            P.rect(44, 39.4, 106, 0.4, C[8])
            for x in range(47, 150, 8):
                P.rect(x, 40.6, 0.8, 4.0 + (x % 16) * 0.1, C[5])
                P.courbe([(x + 0.8, 43.0), (x + 4.4, 40.8), (x + 8.0, 43.0)], C[5], 1)
            t = (p + 0.2) % 1.0                                                 # quelqu'un la traverse, un dossier sous le bras
            P.rect(60 + 70 * t, 37.4, 0.9, 2.0, C[3])
            P.rect(60.8 + 70 * t, 38.2, 0.8, 0.8, E5)
        brume(30.0 + 12 * r, 5.0 + r, 1 + r, 0.5, ton=9 - r)
    pg.fumee(P, 44.0, 20.0, p)
    v = onde(p)                                                 # le fanion d'une tour lointaine
    P.trait(170.0, -6.0, 170.0, -14.0, C[2])
    P.poly([(170.0, -14.0), (176.0, -13.0 + 0.6 * v), (170.0, -11.0)], O2)
    for i in range(5):                                          # un vol de pigeons tourne autour des tours
        a = 2 * math.pi * (p + i * 0.05)
        bx_, by_ = 60.0 + 34.0 * math.cos(a) + i * 2.0, 12.0 + 7.0 * math.sin(a) + i
        P.trait(bx_ - 1.2, by_ - 0.6 * onde(p * 2, i * 0.2), bx_, by_, C[3])
        P.trait(bx_, by_, bx_ + 1.2, by_ - 0.6 * onde(p * 2, i * 0.2), C[3])
    tab.plan("moyen", 0.5)
    # ---- La tour : un fût de pierre grise, éclairé par la gauche, cerclé de corniches ; elle se perd dans la brume.
    demi = lambda y: 25.0 + (_a(y) - 30) * 0.05
    tour = np.abs(X - cx) < demi(Y)
    u = np.clip((X - cx) / demi(Y), -1, 1)
    rond = np.sqrt(1 - u * u)
    yc_ = Y + 0.05 * (72.0 - Y) * rond                           # les anneaux se cintrent : on la regarde d'en bas
    jour = np.clip(-0.62 * u + 0.78 * rond, 0, 1)
    grain = pg.fbm(X / 3.0, Y / 2.0, 3, 243)
    assise = np.floor((yc_ + 16) / 3.0)
    col_ = np.floor(np.arcsin(u) / 0.24 + 0.5 * (assise % 2))
    vp = 0.16 + 0.62 * jour + 0.16 * (grain - 0.5) + 0.12 * (hz(assise, col_, 266) - 0.5) + 0.1 * (u > 0.9)
    P.rampe(tour, vp, [G0, G1, G2, G3, G3, G4], 0.5)
    P.remplir(tour & (u < -0.93) & (Y > 4), E5)                                 # le liseré de jour, à gauche
    joint_h = ((yc_ + 16) % 3.0) < 0.4
    joint_v = (np.abs((np.arcsin(u) / 0.24 + 0.5 * (assise % 2)) % 1.0) < 0.07) & ~joint_h
    voile(P, tour & (joint_h | joint_v), G0, 0.5)
    P.remplir(tour & (((yc_ + 16) % 3.0) > 0.4) & (((yc_ + 16) % 3.0) < 0.75) & (u < 0.1), G4)      # le haut de chaque pierre accroche le jour
    voile(P, tour & (pg.fbm(X / 5.0, Y / 9.0, 3, 267) > 0.62) & (u > -0.4), G0, 0.3)                 # coulures d'humidité
    voile(P, tour & (np.abs(u + 0.2 - 0.1 * np.sin(Y / 6.0)) < 0.02) & (Y > 2) & (Y < 26), G0, 0.6)   # une lézarde
    for yb in (0.0, 30.0, 54.0):                                # corniches : dessus clair, ombre portée dessous
        co = (np.abs(X - cx) < demi(Y) + 1.8) & (np.abs(yc_ - yb) < 1.2)
        P.rampe(co, 0.2 + 0.7 * jour, [G1, G2, G3, G4, E5], 0.4)
        P.remplir((np.abs(X - cx) < demi(Y) + 1.8) & (np.abs(yc_ - yb + 1.0) < 0.3) & (u < 0.3), E5)
        voile(P, tour & (yc_ - yb > 1.2) & (yc_ - yb < 3.4), G0, 0.5)
        for k in range(-5, 6):                                  # les modillons
            a = k * 0.27
            P.rect(cx + demi(yb) * math.sin(a) - 0.5, yb + 1.2 - 0.05 * (72 - yb) * math.cos(a), 1.0, 1.4, G1)
    # Les tampons géants frappés dans la pierre : encre un peu passée, un peu de travers.
    for i, (dx, y, a, c0) in enumerate(((-11, 12, -0.3, V4), (10, 22, 0.25, O2), (-8, 42, 0.15, C2), (13, 47, -0.2, V4))):
        d = np.hypot(X - cx - dx, Y - y)
        use = pg.fbm(X / 1.5, Y / 1.5, 2, 268 + i) > 0.3
        voile(P, tour & (np.abs(d - 4.6) < 0.5) & use, c0, 0.8)
        voile(P, tour & (np.abs(d - 3.6) < 0.25) & use, c0, 0.6)
        voile(P, tour & (np.abs((X - cx - dx) * math.cos(a) + (Y - y) * math.sin(a)) < 2.6) & (np.abs(
            -(X - cx - dx) * math.sin(a) + (Y - y) * math.cos(a)) < 0.5) & use, c0, 0.8)
        voile(P, tour & (d < 3.4) & (((X + Y * 0.6) % 1.6) < 0.4) & use, c0, 0.25)
    # À chaque étage, un guichet : fenêtre en arche, appui de pierre, store, lumière jaune.
    for j, y in enumerate((-8.0, 6.0, 18.0, 36.0)):
        for i in (-1, 0, 1):
            if (i + j) % 2 == 0:
                vif = (p + hz(i + 2, j, 244)) % 1.0 < 0.85
                wx = cx + demi(y) * math.sin(i * 0.38)
                ww = 1.5 * math.cos(i * 0.38) + 0.3
                P.ell(wx, y + 0.6, ww + 0.5, 1.6, G0, cond=Y < y + 0.8)
                P.rect(wx - ww - 0.5, y + 0.6, 2 * ww + 1.0, 4.2, G0)
                P.rect(wx - ww, y + 0.8, 2 * ww, 3.6, J3 if vif else J1)
                P.rect(wx - ww, y + 0.8, 2 * ww, 1.0 + 0.6 * hz(i, j, 269), E4 if vif else G2)       # le store, plus ou moins baissé
                P.rect(wx - 0.15, y + 0.8, 0.3, 3.6, G0)
                P.rect(wx - ww - 1.0, y + 4.8, 2 * ww + 2.0, 0.7, G4)
                P.rect(wx - ww - 1.0, y + 5.5, 2 * ww + 2.0, 0.4, G0)
                if vif:
                    halo(P, wx, y + 2.6, 5.0, J2, 0.35)
    P.rect(cx - demi(20) + 2.0, 1.0, 1.0, 53.0, G1)             # une descente de gouttière, et ses colliers
    P.rect(cx - demi(20) + 2.0, 1.0, 0.4, 53.0, G4)
    for yb in (8.0, 20.0, 40.0, 50.0):
        P.rect(cx - demi(20) + 1.6, yb, 1.8, 0.6, G0)
    pg.goutte(P, cx - demi(20) + 2.5, 54.0, 75.0, coul=C[9], d=0.3)
    voile(P, tour & (Y < 4), C[7], np.clip((4 - Y) / 20.0, 0, 0.95))                   # elle se perd dans la brume
    # La porte basse : arche de pierre, vantaux de bois cloutés, la règle gravée au-dessus, le néon jaune.
    P.rect(cx - 12.0, 55.6, 24.0, 3.0, G3)                       # la plaque : « Chaque étage attend que le précédent se vide. »
    P.rect(cx - 12.0, 55.6, 24.0, 0.4, E5)
    P.rect(cx - 12.0, 58.2, 24.0, 0.4, G0)
    for k in range(2):
        for x in np.arange(cx - 10.6 + k * 1.4, cx + 10.0 - k * 3, 2.3):
            P.rect(x, 56.4 + k * 0.9, 1.5, 0.4, G0)
    for k in range(9):                                          # les claveaux de l'arche
        a = math.pi * (1.0 + k / 8.0)
        P.poly([(cx + 6.0 * math.cos(a), 67.0 + 6.0 * math.sin(a)), (cx + 8.2 * math.cos(a), 67.0 + 8.2 * math.sin(a)),
                (cx + 8.2 * math.cos(a + 0.36), 67.0 + 8.2 * math.sin(a + 0.36)), (cx + 6.0 * math.cos(a + 0.36), 67.0 + 6.0 * math.sin(a + 0.36))], G4 if k % 2 else G3)
    P.rect(cx - 8.2, 67.0, 2.2, 9.0, G3)
    P.rect(cx + 6.0, 67.0, 2.2, 9.0, G2)
    P.ell(cx, 67.0, 6.0, 6.0, G0, cond=Y < 67.5)
    P.rect(cx - 6.0, 67.0, 12.0, 9.0, G0)
    P.ell(cx, 67.5, 4.8, 4.8, B1, cond=Y < 68)
    P.rect(cx - 4.8, 67.5, 9.6, 8.5, B1)
    P.rampe((np.abs(X - cx) < 4.8) & (Y > 63.0) & (Y < 76.0) & (P.a == B1), 0.5 - 0.3 * (X - cx) / 4.8 + 0.2 * (pg.fbm(X * 2.0, Y / 3.0, 2, 270) - 0.5), [B1, B2, B3], 0.4)
    for i in range(-2, 3):
        P.rect(cx + i * 1.9 - 0.2, 64.0 if abs(i) < 2 else 66.0, 0.4, 12.0, B1)
    P.rect(cx - 0.2, 62.8, 0.4, 13.2, G0)
    for yb in (66.0, 72.0):                                     # les pentures de fer et leurs clous
        P.rect(cx - 4.6, yb, 9.2, 0.6, G1)
        for i in range(-2, 3):
            P.point(cx + i * 1.9 + 0.8, yb + 0.2, G4)
    P.ell(cx + 1.6, 70.0, 0.7, 0.7, J2)
    P.rect(cx - 2.2, 68.0, 1.6, 1.0, G0)                         # le judas
    neon(P, cx - 9.0, cx + 9.0, 60.0, J2, J3, vacille=0.12, lueur=10.0)
    P.rect(cx - 9.6, 59.2, 0.6, 1.6, G0)
    P.rect(cx + 9.0, 59.2, 0.6, 1.6, G0)
    halo(P, cx, 66.0, 34.0, J2, 0.5, ry=16)
    for k, (w_, y_) in enumerate(((13.0, 76.0), (16.0, 77.2))):  # deux marches usées
        P.rect(cx - w_, y_, 2 * w_, 1.2, G4 if k == 0 else G3)
        P.rect(cx - w_, y_, 2 * w_, 0.4, E5)
    brume(2.0, 4.0, 3, 0.45)
    brume(-10.0, 7.0, 4, 0.8)
    # ---- Le parvis : des pavés mouillés, en perspective ; la tour y pose son ombre (vers la droite) et son reflet, le néon
    # y coule en traînées jaunes.
    sol = (Y > 68.0) & ~(tour & (Y < 75.0))
    dp = 10.0 / np.maximum(Y - 58.0, 1e-3)
    rang_ = np.floor(dp * 22.0)
    colp = np.floor((X - cx) * dp * 0.42 + 0.5 * (rang_ % 2))
    hp = hz(rang_, colp, 271)
    P.rampe(sol, 0.42 + 0.3 * (hp - 0.5) + 0.2 * (pg.fbm(X / 14.0, Y / 3.0, 3, 272) - 0.5) - 0.0016 * (X - 40.0), [G1, G2, G3, G4, E4], 0.4)
    fr_ = dp * 22.0 - rang_
    fc_ = (X - cx) * dp * 0.42 + 0.5 * (rang_ % 2) - colp
    P.remplir(sol & ((fr_ < 0.12) | (fc_ < 0.09)), G1)
    P.remplir(sol & (fr_ > 0.8) & (fc_ > 0.2) & (hp > 0.45), E5)                 # le bord de chaque pavé accroche le jour
    voile(P, sol & (X > cx + 8) & (X - cx < 24 + (Y - 68.0) * 9.0) & (Y < 79.5), G0, 0.5)          # l'ombre de la tour
    flaque = sol & (pg.fbm(X / 11.0, Y / 2.2, 3, 273) > 0.58)
    voile(P, flaque, C[8], 0.5)
    P.remplir(flaque & (hz(P.YI, (P.XI + int(p * 8)) // 5, 276) < 0.08), BLANC)   # un éclat, ici ou là                                # les flaques prennent le ciel
    voile(P, flaque & (np.abs(X - cx) < 24) & (Y > 75.5), G0, 0.4)               # et le pied de la tour
    lueur = sol & (np.hypot(X - cx, (Y - 77) * 3.2) < 46)
    voile(P, lueur, J2, 0.3)
    coulee = sol & (np.abs(X - cx) < 10.0 + (Y - 76.0)) & (Y > 77.8) & (hz(P.YI, (P.XI + int(p * 8)) // 3, 274) < 0.5)
    P.remplir(coulee & (np.abs(X - cx) < 5.0), J3)
    P.remplir(coulee & (np.abs(X - cx) >= 5.0), J2)
    voile(P, sol & (np.abs(X - cx) > 62), G1, 0.25)
    voile(P, sol & (Y < 71.5), C[8], np.clip((71.5 - Y) / 3.5, 0, 0.6))          # la brume traîne au ras du parvis, au loin
    # La file enroulée trois fois autour de la base : poteaux de laiton, cordons, ceux qui attendent, leurs ombres.
    for tour_n, (rx, ry, yc) in enumerate(((34.0, 3.4, 71.0), (52.0, 4.6, 72.0), (74.0, 5.4, 73.4))):
        nb = 14 + tour_n * 6
        k = 0.7 + 0.2 * tour_n
        for i in range(nb):
            a = math.pi * (1.0 + i / (nb - 1.0))                # la moitié de l'ellipse qui passe devant la tour
            x, y = cx + rx * math.cos(a), yc - ry * math.sin(a)
            a2 = math.pi * (1.0 + (i + 1) / (nb - 1.0))
            if i < nb - 1:
                x2, y2 = cx + rx * math.cos(a2), yc - ry * math.sin(a2)
                P.courbe([(x, y - 4.0 * k), ((x + x2) / 2, (y + y2) / 2 - 3.0 * k), (x2, y2 - 4.0 * k)], O2 if tour_n else O1, 1)
            if (34 < x < 72 or 122 < x < 162) and tour_n > 0:
                continue                                      # la place de Pilou et de son interlocuteur
            voile(P, sol & (np.hypot((X - x - 1.6 * k) / (2.4 * k), (Y - y - 0.2) / 0.5) < 1.0), G0, 0.45)
            P.rect(x - 0.4, y - 4.6 * k, 0.9, 4.6 * k, J1)
            P.rect(x - 0.4, y - 4.6 * k, 0.4, 4.6 * k, J3)
            P.ell(x, y - 4.8 * k, 0.7 * k, 0.7 * k, J2)
            P.ell(x, y, 1.0 * k, 0.4, G0)
            if i % 2 == 0 and tour_n < 2:
                hgt = (3.0 + hz(i, tour_n, 245)) * k
                dy = 0.3 if int(p * 8 + i) % 6 == 0 else 0.0
                c0 = (BLANC, E5, C3)[i % 3]
                P.rect(x + 1.2, y - hgt - dy, 1.6 * k, hgt, c0)
                P.rect(x + 1.2 + 1.2 * k, y - hgt - dy, 0.4 * k, hgt, E3 if c0 != C3 else C1)
                P.point(x + 1.5, y - hgt * 0.7 - dy, ENCRE)
    P.rect(cx + 9.0, 73.4, 3.2, 0.7, B3)                         # le tabouret trop petit
    for dx in (9.3, 11.6):
        P.rect(cx + dx, 74.0, 0.5, 2.2, B2)
    P.rect(cx + 9.6, 71.0, 2.0, 2.4, E5)                         # le képi posé dessus : le gardien s'est absenté
    P.rect(cx + 9.2, 73.0, 3.0, 0.5, N1)
    P.rect(cx + 9.6, 71.0, 2.0, 0.5, O2)
    for i in range(3):                                          # des pigeons sur la corniche ; l'un s'ébroue
        x = 82.0 + i * 5.0
        P.ell(x, 27.6, 1.8, 1.2, G4)
        P.ell(x + 1.2, 26.4 - (0.5 if (i == 1 and int(p * 8) % 4 == 0) else 0), 0.8, 0.8, V3)
    pg.yeux(P, cx - 1.4, 68.4, coul=J3, d=0.6)                   # derrière le judas
    t = p % 1.0                                                 # là-haut, un grand tampon s'abat sur une feuille, et remonte
    ty = 10.0 + 6.0 * (1 - abs(math.sin(math.pi * t)) ** 6)
    P.poly([(118.0, 17.6), (131.0, 17.6), (131.0, 19.0), (119.0, 24.0), (118.0, 24.0)], G1)      # la console de pierre du guichet extérieur
    P.rect(117.0, 17.2, 14.6, 0.8, G4)
    P.trait(131.0, 17.2, 131.0, 12.0, G1)                       # son garde-corps
    P.trait(120.0, 12.4, 131.0, 12.4, G1)
    P.rect(120.0, 16.2, 9.0, 1.0, BLANC)
    P.rect(123.0, ty - 6.0, 3.0, 6.0, B2)
    P.rect(123.0, ty - 6.0, 1.0, 6.0, B3)
    P.rect(121.6, ty, 5.8, 1.6, V3)
    tab.plan("premier", 1.0)
    # ---- Premier plan : deux réverbères de fonte qui cadrent, un fil de formulaires tendu de l'un à l'autre, un panneau
    # fléché, des cartons d'archives ; des formulaires passent dans le courant d'air.
    for (x, cote) in ((10.0, 1), (184.0, -1)):
        P.rect(x - 1.3, 10.0, 2.6, 70.0, ENCRE)
        P.rect(x - 1.3 if cote > 0 else x + 0.5, 10.0, 0.8, 70.0, N1)
        P.rect(x - 0.3, 10.0, 0.5, 70.0, G1 if cote > 0 else N0)
        for yb in (22.0, 58.0):
            P.rect(x - 2.0, yb, 4.0, 1.4, ENCRE)
            P.rect(x - 2.0, yb, 4.0, 0.4, G1)
        P.poly([(x - 2.0, 70.0), (x + 2.0, 70.0), (x + 3.6, 80.0), (x - 3.6, 80.0)], ENCRE)
        P.rect(x - 2.6, 70.0, 5.2, 0.5, G1)
        P.courbe([(x, 10.0), (x + cote * 2, 3.0), (x + cote * 13, 2.4)], ENCRE, P.ep(1.4))
        P.courbe([(x, 16.0), (x + cote * 5, 12.0), (x + cote * 9, 3.6)], ENCRE, P.ep(0.6))             # la volute
        P.poly([(x + cote * 2, 3.6), (x + cote * 13, 3.6), (x + cote * 12, 6.0), (x + cote * 3, 6.0)], N0)
        neon(P, x + cote * 7.5 - 4.5, x + cote * 7.5 + 4.5, 6.6, J2, J3, vacille=0.1 if cote > 0 else 0.0, lueur=9.0)
        voile(P, (np.abs(X - x - cote * 7.5) < 4 + (Y - 6) * 0.22) & (Y > 7) & (Y < 80) & (P.a >= 0), J2, 0.1, lumiere=True)
    P.rect(12.0, 44.0, 12.0, 7.0, N0)                            # le panneau : « file → », et le temps d'attente
    P.rect(12.6, 44.6, 10.8, 5.8, E4)
    P.trait(14.0, 46.4, 20.0, 46.4, ENCRE, P.ep(0.5))
    P.poly([(20.0, 45.2), (22.4, 46.4), (20.0, 47.6)], ENCRE)
    sept(P, 14.0, 48.0, "3" if int(p * 8) % 8 < 6 else "4", O2, l=1.2, h=2.0, ep=1)
    P.rect(16.4, 49.4, 5.0, 0.4, G3)
    fil = lambda x: -9.0 + 7.0 * (1 - ((x - 97.0) / 87.0) ** 2) + 0.4 * onde(p)                         # le fil de formulaires
    for x in np.arange(11.0, 183.0, 1.0):
        P.point(x, fil(x), ENCRE)
    for i, x in enumerate(np.arange(22.0, 176.0, 9.5)):
        bal = 0.5 * onde(p, i * 0.17)
        c0 = (BLANC, E5, J2, BLANC, C3, E5, O2)[i % 7]
        P.poly([(x, fil(x) + 0.4), (x + 4.0, fil(x + 4.0) + 0.4), (x + 4.0 + bal, fil(x + 4.0) + 5.6), (x + bal, fil(x) + 5.6)], c0)
        P.trait(x + 0.8 + bal * 0.5, fil(x) + 2.2, x + 3.2 + bal * 0.5, fil(x) + 2.2, G2)
        P.trait(x + 0.8 + bal * 0.7, fil(x) + 3.6, x + 2.6 + bal * 0.7, fil(x) + 3.6, G2)
        P.point(x + 2.0, fil(x + 2.0) + 0.2, O1)
    for k, (bx_, by_, bw, bh) in enumerate(((171.0, 70.0, 11.0, 10.0), (178.0, 62.0, 10.0, 8.0), (166.0, 75.0, 7.0, 5.0))):   # les cartons d'archives
        P.rect(bx_, by_, bw, bh, B1)
        P.rect(bx_, by_, bw, 1.2, B2)
        P.rect(bx_, by_, 0.6, bh, B3)
        P.rect(bx_ + bw * 0.3, by_ + bh * 0.4, bw * 0.4, 2.0, E4)
        P.trait(bx_ + bw * 0.36, by_ + bh * 0.4 + 0.9, bx_ + bw * 0.62, by_ + bh * 0.4 + 0.9, G1)
    papiers(P, 179.0, 62.0, 7.0, 3, 275)
    for i in range(6):                                          # des formulaires emportés par le courant d'air
        t = (p + i / 6.0) % 1.0
        x, y = 20 + 150 * ((hz(i, 1, 246) + t * 0.2) % 1.0), 10 + 50 * hz(i, 2, 246) + 5 * math.sin(t * 6.28 + i)
        if int(t * 8 + i) % 2:
            P.poly([(x, y), (x + 3.0, y - 0.8), (x + 3.4, y + 1.6), (x + 0.4, y + 2.4)], BLANC)
            P.trait(x + 0.8, y + 0.6, x + 2.6, y + 0.2, G3)
        else:
            P.poly([(x, y + 0.6), (x + 3.2, y), (x + 3.0, y + 1.0), (x + 0.2, y + 1.4)], E5)
    pg.papillon_de_nuit(P, 17.5, 8.0, 5.0, coul=BLANC)
    pg.papillon_de_nuit(P, 176.5, 8.0, 5.0, coul=BLANC, d=0.4)


# =====================================================================================================================
# Les étages de la Tour : un palier d'escalier en colimaçon qui donne sur un bureau encombré. Casiers de formulaires de
# toutes les couleurs jusqu'au plafond, guichet vitré, tampons, affiches réglementaires, poussière dorée dans un rai.
# =====================================================================================================================
@decor("grande-panne", "etage-guichets", soleil=(150.0, -20.0), tons=PANNE, nom="Les étages de la Tour", matiere=True)
def etage_guichets(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    P.rampe(np.ones(X.shape, dtype=bool), 0.5 + 0.004 * (X - 96) - 0.004 * (Y - 30) + 0.2 * (pg.fbm(X / 16.0, Y / 10.0, 3, 250) - 0.5),
            [E1, E2, E3, E4], 0.7)                            # le mur du fond, plâtre jauni
    tab.plan("lointains", 0.2)
    # ---- Le mur de casiers : jusqu'au plafond, des formulaires de toutes les couleurs, des étiquettes, une échelle.
    cx0, cx1, cy0, cy1 = 6.0, 112.0, -16.0, 62.0
    P.rect(cx0 - 1.5, cy0, cx1 - cx0 + 3, cy1 - cy0 + 1.5, B1)
    nc, nl = 14, 11
    lw, lh = (cx1 - cx0) / nc, (cy1 - cy0) / nl
    teintes = (O2, C2, V4, E5, Q2, J2, O3, C3, V3, BLANC)
    for j in range(nl):
        for i in range(nc):
            x, y = cx0 + i * lw, cy0 + j * lh
            P.rect(x + 0.4, y + 0.4, lw - 0.8, lh - 0.8, ENCRE if (i + j) % 5 else V1)
            plein = hz(i, j, 251)
            if plein > 0.12:
                n = int(2 + plein * (lh - 2.6) / 0.6)
                c0 = teintes[int(hz(i, j, 252) * len(teintes))]
                for k in range(n):
                    P.rect(x + 0.8 + (hz(i * 31 + j, k, 253) - 0.5) * 0.6, y + lh - 0.9 - k * 0.6, lw - 1.8, 0.5,
                           c0 if k % 2 else E4)
                if hz(i, j, 254) < 0.2:                        # une feuille qui dépasse et frémit
                    P.rect(x + lw - 1.6, y + lh - 2.2 + 0.3 * onde(p, hz(i, j, 255)), 1.6, 0.5, BLANC)
            P.rect(x + lw / 2 - 1.0, y + lh - 0.5, 2.0, 0.5, E5)                         # l'étiquette
    voile(P, (X > cx0) & (X < cx0 + 30) & (Y < cy1), V1, np.clip(0.5 - (X - cx0) / 60.0, 0, 0.5))
    ex = 84.0                                                 # l'échelle à roulettes
    for dx in (0.0, 7.0):
        P.trait(ex + dx, 62.0, ex + dx + 3.0, -16.0, B2, P.ep(0.7))
    for j in range(13):
        y = 60.0 - j * 6.0
        P.trait(ex + (62 - y) * 3 / 78.0, y, ex + 7 + (62 - y) * 3 / 78.0, y, B3, P.ep(0.5))
    tab.plan("moyen", 0.5)
    # ---- La fenêtre haute, à droite : c'est d'elle que tombe le rai doré.
    wx, wy, ww, wh = 136.0, -12.0, 28.0, 30.0
    P.rect(wx - 2, wy - 2, ww + 4, wh + 4, E1)
    P.rampe((X > wx) & (X < wx + ww) & (Y > wy) & (Y < wy + wh), 0.75 - 0.012 * (Y - wy) + 0.1 * (pg.fbm(X / 8.0, Y / 4.0, 2, 256) - 0.5),
            [T.CIEL[7], T.CIEL[9], J3, BLANC], 0.6)
    for i in range(1, 3):
        P.rect(wx + i * ww / 3 - 0.4, wy, 0.8, wh, E1)
    for j in range(1, 3):
        P.rect(wx, wy + j * wh / 3 - 0.4, ww, 0.8, E1)
    P.rect(wx - 3, wy + wh + 2, ww + 6, 1.4, E2)
    # Les affiches réglementaires, et l'horloge de bureau arrêtée.
    affiche(P, 118.0, 26.0, 11.0, 15.0, E5, O1, 0)
    affiche(P, 131.0, 28.0, 9.0, 12.0, C3, N2, 1)
    affiche(P, 170.0, -6.0, 12.0, 16.0, J3, B1, 2)
    affiche(P, 172.0, 14.0, 9.0, 11.0, E5, V2, 1)
    P.ell(124.0, 12.0, 4.6, 4.6, G1)
    P.ell(124.0, 12.0, 3.8, 3.8, BLANC)
    P.trait(124.0, 12.0, 125.2, 10.4, ENCRE)
    P.trait(124.0, 12.0, 124.6 + 0.2 * (int(p * 8) % 2), 15.0, ENCRE)
    # ---- Le guichet vitré : comptoir de bois, vitre et son hygiaphone, la sonnette, le tampon et son encrier.
    gx0, gx1, gy = 116.0, 190.0, 58.0
    P.rect(gx0, gy, gx1 - gx0, 20.0, B2)
    P.rampe((X > gx0) & (X < gx1) & (Y > gy) & (Y < 78), 0.4 + 0.5 * (X - gx0) / (gx1 - gx0) + 0.2 * (pg.fbm(X / 1.5, Y / 14.0, 2, 257) - 0.5),
            [B1, B2, B3], 0.6)
    for x in np.arange(gx0 + 6, gx1, 12.0):
        P.rect(x, gy + 4, 8.0, 12.0, B1)
        P.rect(x + 0.6, gy + 4.6, 6.8, 10.8, B2)
    P.rect(gx0 - 1.5, gy - 1.6, gx1 - gx0 + 3, 2.2, B3)
    P.rect(gx0 - 1.5, gy - 1.6, gx1 - gx0 + 3, 0.6, E4)
    vitre = (X > gx0 + 4) & (X < gx1 - 2) & (Y > 40.0) & (Y < gy - 1.6)
    voile(P, vitre, C3, 0.3)
    voile(P, vitre & (np.abs((X - gx0) - (Y - 40) * 1.6 - 20) < 3), BLANC, 0.5)
    P.rect(gx0 + 3, 39.0, gx1 - gx0 - 4, 1.0, B1)
    P.rect(gx0 + 3, 39.0, 1.0, gy - 40.6, B1)
    P.ell(150.0, 49.0, 3.0, 3.0, B1)
    for k in range(6):
        P.point(150.0 + 1.6 * math.cos(k * 1.05), 49.0 + 1.6 * math.sin(k * 1.05), E5)
    haut_pile = papiers(P, 122.0, gy - 1.6, 9.0, 9, 258)
    papiers(P, 176.0, gy - 1.6, 8.0, 14, 259, clair=C3, ombre=C1)
    P.ell(138.0, gy - 2.6, 2.6, 1.2, J1)                        # la sonnette
    P.ell(138.0, gy - 3.4, 2.0, 1.4, J2, cond=Y < gy - 2.8)
    P.point(138.0, gy - 5.0, J3)
    tape = 1.6 if int(p * 8) in (2, 3) else 0.0                  # le tampon qui retombe tout seul
    P.rect(162.0, gy - 9.0 + tape, 2.0, 4.6, B2)
    P.ell(163.0, gy - 9.4 + tape, 1.6, 1.3, B3)
    P.rect(160.6, gy - 4.6 + tape, 4.8, 1.6, G1)
    P.rect(167.0, gy - 3.2, 5.0, 1.6, V2)
    P.rect(167.4, gy - 3.0, 4.2, 0.5, V4)
    # Le rai doré et sa poussière.
    rai(P, 150.0, -12.0, 78.0, 20.0, -0.72, J3, 0.42, 34, 260)
    # ---- Le palier : parquet en fuite, tapis usé, la rampe de l'escalier en colimaçon à gauche.
    sol = Y > 62.0
    dallage(P, sol & (X < gx0), 150.0, 46.0, B3, B2, larg=4.0, prof=0.9, joint=B1)
    voile(P, sol & (X < gx0) & (np.abs(X - (150 - (Y - 0) * 0.72 - 10)) < 12), J3, 0.3)
    P.rect(30.0, 75.4, 78.0, 4.8, V2)
    P.rect(30.0, 75.4, 78.0, 0.6, V4)
    for x in range(32, 108, 4):
        P.point(x, 77.6, O2 if x % 8 else J2)
    tab.plan("premier", 1.0)
    # L'escalier en colimaçon : le noyau, les marches en éventail, la rampe de fer forgé (contre-jour).
    nx = 2.0
    P.rect(nx - 3.0, -16.0, 6.0, 96.0, N0)
    P.rect(nx + 2.0, -16.0, 1.0, 96.0, G1)
    for i in range(9):
        y = 78.0 - i * 9.0
        l = 26.0 - i * 2.2
        P.poly([(nx, y), (nx + l, y + 2.4 - i * 0.2), (nx + l, y + 4.2 - i * 0.2), (nx, y + 2.4)], N1 if i % 2 else N0)
        P.trait(nx, y, nx + l, y + 2.4 - i * 0.2, G1)
        if i < 8:
            P.trait(nx + l - 1.0, y + 2.2, nx + l - 3.2, y - 14.0, N0)                   # un barreau
            P.ell(nx + l - 2.1, y - 6.0, 0.8, 1.2, N0)
    P.courbe([(nx + 25.0, 66.0), (nx + 20.0, 46.0), (nx + 15.0, 26.0), (nx + 10.0, 6.0), (nx + 6.0, -16.0)], N0, P.ep(1.2))
    P.courbe([(nx + 25.4, 65.6), (nx + 20.4, 45.6), (nx + 15.4, 25.6)], J1, 1)
    papiers(P, 186.0, 80.0, 9.0, 7, 261)                         # une pile oubliée dans le coin
    poussiere(P, 20, -10, 180, 70, 30, J3, 262)
    # ---- Seconde passe : la vie du guichet.
    pg.araignee(P, 142.0, -12.0, 10.0, d=0.2)
    pg.toile_araignee(P, 112.0, -16.0, 10.0, sens=(1, 1), coul=E5)
    pg.avion_papier(P, 30.0, 10.0, 110.0, 40.0, d=0.6)
    pg.vapeur(P, 146.0, 55.0, coul=BLANC, h=9.0)                # un gobelet de café, encore chaud
    P.rect(144.6, 54.8, 3.0, 2.6, E5)
    P.rect(144.6, 54.8, 3.0, 0.6, O2)
    if int(p * 8) in (2, 3):                                    # la sonnette vibre quand le tampon retombe
        P.trait(134.0, 52.0, 133.0, 50.6, J3)
        P.trait(142.0, 52.0, 143.0, 50.6, J3)
    tir = 1.5 + 1.5 * onde(p)                                   # un tiroir du comptoir qui bâille
    P.rect(134.0, 62.0 + 0, 8.0, 4.0, B3)
    P.rect(134.0, 62.0, 8.0, 0.6, E4)
    P.rect(135.0, 60.6 - tir * 0.3, 6.0, 1.6, BLANC)
    P.poly([(182.0, 50.0), (190.0, 50.0), (188.6, 56.4), (183.4, 56.4)], O1)                      # une plante sur le comptoir
    for i in range(5):
        a = -2.5 + i * 0.45 + 0.04 * onde(p, 0.1 * i)
        P.courbe([(186.0, 50.0), (186.0 + 4 * math.cos(a), 50.0 + 5 * math.sin(a)), (186.0 + 7 * math.cos(a), 50.0 + 7 * math.sin(a) + 2)], T.S2, 1)
    pg.souris(P, 70.0, 74.6, sens=1, coul=G3)
    pg.papillon_de_nuit(P, 150.0, 4.0, 6.0, coul=BLANC, d=0.3)


# =====================================================================================================================
# Le bureau de la Planificatrice : un mur entier de petites cartes épinglées en rangs serrés (cochées à gauche, vierges à
# droite), un grand bureau gris avec une réussite en cours, la lampe de bureau, une fin d'après-midi qui n'arrive pas.
# =====================================================================================================================
@decor("grande-panne", "bureau-echeance", soleil=(176.0, 10.0), tons=PANNE, nom="Le bureau de la Planificatrice", matiere=True)
def bureau_echeance(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    P.rampe(np.ones(X.shape, dtype=bool), 0.45 + 0.003 * (X - 60) + 0.004 * (Y + 16) + 0.18 * (pg.fbm(X / 18.0, Y / 12.0, 3, 270) - 0.5),
            [V1, V2, V3, T.L4], 0.7)                          # le papier peint, violet feutré
    P.remplir((((X + Y * 0.5) % 6.0) < 0.5) & (P.T < 0.3), V3)
    tab.plan("lointains", 0.2)
    # ---- Le mur de cartes : à gauche, cochées et un peu jaunies ; à droite, vierges. Entre les deux, la carte du jour.
    mx0, my0, lw, lh, nc, nl = 6.0, -12.0, 5.0, 6.2, 27, 9
    P.rect(mx0 - 2.0, my0 - 2.0, nc * lw + 3.0, nl * lh + 3.0, B1)
    P.rect(mx0 - 1.2, my0 - 1.2, nc * lw + 1.4, nl * lh + 1.4, K2)
    P.remplir((X > mx0 - 1.2) & (X < mx0 + nc * lw + 0.2) & (Y > my0 - 1.2) & (Y < my0 + nl * lh + 0.2) & (P.T < 0.35), K1)   # le liège
    jour = (13, 4)
    for j in range(nl):
        for i in range(nc):
            x, y = mx0 + i * lw + (hz(i, j, 271) - 0.5) * 0.5, my0 + j * lh + (hz(i, j, 272) - 0.5) * 0.5
            faite = i * nl + j < jour[0] * nl + jour[1]
            if (i, j) == jour:
                bat = 0.4 * onde(p)
                P.rect(x - 0.3, y - 0.3, lw - 0.4, lh - 0.8, O2)
                P.rect(x, y, lw - 1.0, lh - 1.4 + bat, J3)
                P.point(x + lw / 2 - 0.5, y + 0.3, O1, 2)
                continue
            P.rect(x, y, lw - 1.0, lh - 1.4, (E4 if hz(i, j, 273) < 0.5 else E5) if faite else BLANC)
            P.point(x + lw / 2 - 0.5, y + 0.2, (O2, C2, V4)[int(hz(i, j, 274) * 3)])                # la punaise
            if faite:
                P.trait(x + 0.8, y + 2.6, x + 1.6, y + 3.6, N2)                                 # la coche
                P.trait(x + 1.6, y + 3.6, x + 3.2, y + 1.4, N2)
            else:
                P.rect(x + 0.7, y + 1.6, lw - 2.4, 0.4, G4)
                P.rect(x + 0.7, y + 2.8, lw - 3.2, 0.4, G4)
    P.courbe([(mx0 + jour[0] * lw + 2, my0 + jour[1] * lh + 5), (mx0 + 96, my0 + 52), (mx0 + 118, my0 + 46 + 0.5 * onde(p))], O2, 1)   # un fil
    tab.plan("moyen", 0.5)
    # ---- La haute fenêtre, à droite : une lumière orangée, toujours la même ; le store à moitié baissé.
    wx, wy, ww, wh = 152.0, -14.0, 30.0, 56.0
    P.rect(wx - 2, wy - 2, ww + 4, wh + 4, V1)
    P.rampe((X > wx) & (X < wx + ww) & (Y > wy) & (Y < wy + wh), 0.25 + 0.012 * (Y - wy), [T.CIEL[6], T.CIEL[8], O3, J3], 0.7)
    P.ell(wx + 20, wy + 40, 5.0, 5.0, BLANC, cond=(X < wx + ww) & (Y < wy + wh))
    for j in range(9):                                        # les lames du store
        y = wy + j * 2.6
        P.rect(wx, y, ww, 1.6, E4)
        P.rect(wx, y + 1.2, ww, 0.4, E2)
    P.trait(wx + ww - 3, wy + 23.4, wx + ww - 3, wy + 34 + 0.6 * onde(p), E4)
    P.rect(wx + ww / 2 - 0.5, wy, 1.0, wh, V1)
    P.rect(wx - 3, wy + wh + 2, ww + 6, 1.6, V2)
    rai(P, wx + 6, wy + 26.0, 80.0, 24.0, -1.15, O3, 0.36, 26, 275)
    # Le classeur à tiroirs, la plante en pot, l'horloge murale arrêtée.
    P.rect(186.0, 30.0, 12.0, 48.0, G2)
    for j in range(4):
        P.rect(187.0, 32.0 + j * 11.4, 10.0, 10.0, G3)
        P.rect(190.0, 36.0 + j * 11.4, 4.0, 1.0, G1)
        P.rect(189.6, 33.6 + j * 11.4, 4.8, 1.6, BLANC)
    P.poly([(141.0, 70.0), (150.0, 70.0), (148.6, 78.0), (142.4, 78.0)], O1)
    P.rect(140.4, 69.0, 10.2, 1.6, O2)
    for i in range(7):
        a = -2.6 + i * 0.36 + 0.03 * onde(p, 0.1 * i)
        P.courbe([(145.5, 69.0), (145.5 + 6 * math.cos(a), 69.0 + 7 * math.sin(a)), (145.5 + 11 * math.cos(a), 69.0 + 10 * math.sin(a) + 3)],
                 T.S1 if i % 2 else T.S2, P.ep(0.7), 1)
    P.ell(140.0, -4.0, 5.0, 5.0, B2)
    P.ell(140.0, -4.0, 4.2, 4.2, E5)
    P.trait(140.0, -4.0, 141.4, -5.8, ENCRE)
    P.trait(140.0, -4.0, 140.9 + 0.2 * (int(p * 8) % 2), -0.6, ENCRE)
    # ---- Le parquet, puis le grand bureau gris : la réussite en cours, la lampe (abat-jour sarcelle), le téléphone.
    sol = Y > 62.0
    dallage(P, sol, 60.0, 44.0, B2, B1, larg=4.0, prof=0.8, joint=ENCRE)
    voile(P, sol & (np.abs(X - (wx + 6 - (Y - 12) * 1.15)) < 16), O3, 0.3)
    bx0, bx1, by = 64.0, 132.0, 60.0
    P.poly([(bx0, by), (bx1, by), (bx1 + 4, by + 6), (bx0 - 4, by + 6)], G3)                   # le plateau
    P.rampe(P.masque_poly([(bx0, by), (bx1, by), (bx1 + 4, by + 6), (bx0 - 4, by + 6)]), 0.45 + 0.5 * (X - bx0) / (bx1 - bx0),
            [G2, G3, G4], 0.6)
    P.rect(bx0 - 4, by + 6, bx1 - bx0 + 8, 1.4, G1)
    P.rect(bx0 - 2, by + 7.4, 22.0, 10.6, G2)
    P.rect(bx1 - 20, by + 7.4, 22.0, 10.6, G2)
    for x in (bx0, bx1 - 18):
        for j in range(2):
            P.rect(x, by + 8.4 + j * 4.8, 18.0, 4.0, G3)
            P.rect(x + 7.0, by + 10.0 + j * 4.8, 4.0, 0.8, G1)
    voile(P, (X > bx0 + 20) & (X < bx1 - 20) & (Y > by + 7.4) & (Y < 78), ENCRE, 0.75)
    for i, (dx, dy, c0) in enumerate(((0, 0, BLANC), (4.6, 0, BLANC), (9.2, 0, BLANC), (13.8, 0.2, V4), (18.4, 0, BLANC), (23.0, 0, BLANC),
                                      (2.3, 2.2, BLANC), (6.9, 2.2, BLANC), (16.1, 2.2, BLANC))):       # la réussite
        x, y = bx0 + 18 + dx + dy * 0.6, by + 1.0 + dy
        P.poly([(x, y), (x + 3.6, y), (x + 4.0, y + 1.8), (x + 0.4, y + 1.8)], c0)
        if c0 == BLANC:
            P.point(x + 1.0, y + 0.5, (O2, N2)[i % 2])
            P.point(x + 2.6, y + 1.0, (O2, N2)[i % 2])
    lx, ly = 118.0, by + 1.0                                   # la lampe de bureau
    halo(P, lx - 6, ly + 2, 22, J3, 0.45, ry=9)
    P.ell(lx, ly + 0.6, 4.0, 1.2, J1)
    P.rect(lx - 0.5, ly - 9.0, 1.0, 9.6, J1)
    P.poly([(lx - 9.0, ly - 9.0), (lx + 5.0, ly - 9.0), (lx + 3.0, ly - 13.0), (lx - 7.0, ly - 13.0)], T.S1)
    P.poly([(lx - 8.0, ly - 9.6), (lx + 1.0, ly - 9.6), (lx + 0.0, ly - 12.4), (lx - 6.4, ly - 12.4)], T.S2)
    P.rect(lx - 9.0, ly - 9.0, 14.0, 0.6, J3)
    P.trait(lx + 2.0, ly - 8.4, lx + 2.0, ly - 5.6 + 0.4 * onde(p), J2)                         # la chaînette
    P.rect(bx0 + 4, by + 0.6, 9.0, 3.4, ENCRE)                  # le téléphone à cadran
    P.rect(bx0 + 3, by - 0.8, 11.0, 1.6, G1)
    P.ell(bx0 + 8.5, by + 2.4, 1.8, 1.0, G3)
    papiers(P, bx1 - 14, by + 3.6, 8.0, 5, 276)
    P.ell(98.0, 50.0, 11.0, 8.0, V1)                            # le grand fauteuil capitonné, derrière le bureau
    P.rect(87.0, 50.0, 22.0, 10.0, V1)
    P.ell(98.0, 50.6, 9.6, 6.8, V2)
    P.rect(88.4, 50.6, 19.2, 9.4, V2)
    for (x, y) in ((92.0, 49.0), (98.0, 47.6), (104.0, 49.0), (95.0, 54.0), (101.0, 54.0)):
        P.point(x, y, V4)
    tab.plan("premier", 1.0)
    # Premier plan sombre : le bord d'une étagère à gauche (classeurs), un lampadaire éteint à droite.
    P.rect(-6.0, 40.0, 12.0, 40.0, N0)
    for j in range(4):
        P.rect(-6.0, 42.0 + j * 9.4, 11.0, 0.8, G1)
        for i in range(4):
            P.rect(-5.0 + i * 2.6, 43.4 + j * 9.4, 2.0, 7.4, (V2, N2, V1, N1)[(i + j) % 4])
            P.rect(-4.6 + i * 2.6, 45.0 + j * 9.4, 1.2, 1.6, E4 if (i + j) % 3 else O2)
    voile(P, Y > 76.8, ENCRE, 0.3)
    poussiere(P, 60, -10, 186, 70, 26, O3, 277)
    # ---- Seconde passe : la vie du bureau.
    pg.vapeur(P, 82.0, 58.4, coul=BLANC, h=10.0)                 # une tasse de thé qui n'a pas refroidi
    P.rect(80.6, 58.4, 3.0, 2.4, C3)
    P.rect(83.6, 59.0, 0.8, 1.2, C3)
    pg.papillon_de_nuit(P, 112.0, 50.0, 6.0, coul=BLANC)
    pg.araignee(P, 176.0, -14.0, 12.0, d=0.5)
    t = (p + 0.3) % 1.0                                         # une carte se décroche du mur et tombe en feuille morte
    P.rect(120.0 + 4 * math.sin(t * 9), 46.0 + 16 * t, 3.0, 2.2, BLANC)
    P.point(121.0 + 4 * math.sin(t * 9), 46.6 + 16 * t, G4)
    P.courbe([(72.0, 62.0), (66.0, 66.0 + 0.5 * onde(p)), (60.0, 64.0), (56.0, 70.0)], ENCRE, 1)   # le fil du téléphone
    pg.souris(P, 180.0, 77.6, sens=-1, coul=G3)
    pg.toile_araignee(P, -6.0, -16.0, 12.0, sens=(1, 1), coul=T.L4)


# =====================================================================================================================
# La Caverne des câbles : un tunnel sombre envahi de câbles épais comme des troncs, emmêlés du sol au plafond ; quelques
# diodes clignotent au loin ; la lueur sarcelle d'une gelée lumineuse à un croisement.
# =====================================================================================================================
@decor("grande-panne", "caverne-cables", soleil=(46.0, 52.0), tons=PANNE, nom="La Caverne des câbles", matiere=True)
def caverne_cables(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    fx, fy = 62.0, 40.0                                       # le fond du tunnel, à gauche
    tab.plan("ciel", 0.0)
    r = np.hypot(X - fx, (Y - fy) * 1.3)
    P.rampe(np.ones(X.shape, dtype=bool), 0.9 - r / 120.0 + 0.2 * (pg.fbm(X / 10.0, Y / 7.0, 3, 280) - 0.5), [ENCRE, N0, V1, V2, N2], 0.8)
    tab.plan("lointains", 0.2)
    # ---- Le fond : le croisement, la gelée lumineuse sarcelle qui éclaire les parois, des diodes lointaines.
    halo(P, fx - 8, fy + 14, 46, Q1, 0.75, ry=30)
    halo(P, fx - 8, fy + 16, 26, Q2, 0.7, ry=16)
    for i, (x, y, rr) in enumerate(((fx - 10, fy + 20, 7.0), (fx - 1, fy + 22, 4.6), (fx - 19, fy + 22.5, 3.8), (fx - 6, fy + 14, 3.0))):
        souffle = 0.4 * onde(p, 0.2 * i)
        P.ell(x, y, rr + souffle, rr * 0.8 + souffle, Q2, cond=Y < fy + 25)
        P.ell(x - rr * 0.2, y - rr * 0.2, rr * 0.6, rr * 0.5, Q3, cond=Y < fy + 25)
        P.ell(x - rr * 0.4, y - rr * 0.4, rr * 0.2, rr * 0.16, BLANC)
    for i in range(22):
        a, d = 6.283 * hz(i, 1, 281), 12 + 34 * hz(i, 2, 281)
        voyant(P, fx + d * math.cos(a), fy + d * 0.7 * math.sin(a), (O2, C2, J3, Q3)[i % 4], V1, d=hz(i, 3, 281), part=0.3 + 0.4 * hz(i, 4, 281), r=0.35)
    for i, (x, ep) in enumerate(((20, 5.0), (44, 3.4), (92, 4.2), (112, 3.0), (136, 5.4), (160, 3.6), (180, 4.6))):
        d = 5 * hz(i, 1, 288)                                # des troncs de câbles, loin, du sol au plafond
        pts = [(x - d, 82), (x + 4 - d, 56), (x - 3 + d, 30), (x + 5, 6), (x + d, -18)]
        cable(P, pts, ep, N0, V1 if i % 2 else N1, None)
        cable(P, [(px + ep * 0.7, py) for px, py in pts], ep * 0.5, ENCRE, N1, None)
    voile(P, np.ones(X.shape, dtype=bool) & (P.a >= 0), Q1, 0.3 * np.exp(-(np.hypot(X - fx + 8, (Y - fy - 16) * 1.3) / 44.0) ** 2))
    tab.plan("moyen", 0.5)
    # ---- Les câbles du milieu : des faisceaux qui pendent en guirlandes et rampent au sol, cuivre, violets, gris.
    for i, (x, ep) in enumerate(((6, 6.0), (70, 5.0), (148, 6.4))):
        pts = [(x, 82), (x + 6, 58), (x - 4, 34), (x + 7, 10), (x + 2, -18)]
        coul = ((K1, K2, O2), (V1, V2, V3), (G0, G1, G2))[i]
        cable(P, pts, ep, coul[0], coul[1], coul[2])
        cable(P, [(px - ep * 0.8, py + 3) for px, py in pts], ep * 0.45, N0, N2, None)
    for i in range(16):
        x0 = -6 + 13.5 * i + 5 * hz(i, 1, 282)
        y0 = -18.0
        creux = 8 + 26 * hz(i, 2, 282)
        x1 = x0 + 20 + 30 * hz(i, 3, 282)
        bal = 0.6 * onde(p, hz(i, 4, 282))
        coul = ((V1, V2, V3), (K1, K2, O2), (G0, G1, G2), (N0, N1, N2))[i % 4]
        cable(P, [(x0, y0), (x0 + (x1 - x0) * 0.3 + bal, y0 + creux), (x0 + (x1 - x0) * 0.7 + bal, y0 + creux * 0.9), (x1, y0)],
              1.4 + 1.6 * hz(i, 5, 282), coul[0], coul[1], coul[2] if i % 3 == 0 else None)
    for i in range(7):                                        # des câbles qui tombent droit, avec leur prise
        x = 14 + 27 * i + 6 * hz(i, 1, 283)
        l = 14 + 26 * hz(i, 2, 283)
        bal = 0.8 * onde(p, hz(i, 3, 283))
        P.courbe([(x, -18), (x + bal * 0.4, -18 + l * 0.6), (x + bal, -18 + l)], G1, P.ep(0.7))
        P.rect(x + bal - 1.0, -18 + l, 2.0, 2.6, G3)
        P.rect(x + bal - 0.6, -18 + l + 2.6, 0.4, 1.0, J2)
        P.rect(x + bal + 0.3, -18 + l + 2.6, 0.4, 1.0, J2)
    sol = Y > 70.0 + 2.0 * np.sin(X / 17.0) + 1.0 * np.sin(X / 5.0)
    P.rampe(sol, 0.4 + 0.3 * (pg.fbm(X / 6.0, Y / 2.0, 3, 284) - 0.5) + 0.3 * np.exp(-((X - fx + 8) / 40.0) ** 2), [ENCRE, N0, N1, Q1], 0.8)
    for i in range(9):                                        # les câbles qui rampent sur le sol
        x0 = -8 + 24 * i
        coul = ((K1, K2, O2), (V1, V2, V3), (G0, G1, G2))[i % 3]
        cable(P, [(x0, 74 + 3 * hz(i, 1, 285)), (x0 + 12, 71.5 + 2 * hz(i, 2, 285)), (x0 + 24, 75 + 3 * hz(i, 3, 285)), (x0 + 38, 72 + 2 * hz(i, 4, 285))],
              1.6, coul[0], coul[1], None)
    voile(P, sol & (Y > 75.5), N0, 0.55)                        # le chemin où l'on marche reste dégagé
    # Un boîtier de dérivation au mur : voyants qui courent, un interrupteur.
    P.rect(150.0, 20.0, 18.0, 13.0, G1)
    P.rect(150.0, 20.0, 18.0, 1.0, G3)
    for i in range(5):
        voyant(P, 153.0 + i * 3.0, 24.0, (Q3, O2)[i % 2], G0, d=i / 5.0, part=0.3, r=0.6)
    P.rect(155.0, 27.4, 8.0, 3.0, ENCRE)
    P.rect(155.6 + 3.0 * (int(p * 8) % 8 < 4), 27.8, 2.6, 2.2, O2)
    tab.plan("premier", 1.0)
    # ---- Premier plan : trois câbles épais comme des troncs, à contre-jour, le liseré sarcelle de la gelée sur leur flanc.
    for i, pts in enumerate(([(-10, 82), (2, 50), (-4, 20), (10, -18)], [(196, 84), (182, 56), (190, 26), (176, -18)],
                             [(-12, 30), (10, 34), (22, 22), (16, -18)], [(202, 40), (178, 30), (170, 8), (184, -18)])):
        ep = (9.0, 10.0, 5.0, 6.0)[i]
        P.courbe(pts, ENCRE, P.ep(ep))
        d = ep * 0.42 * (1 if i % 2 == 0 else -1)
        P.courbe([(x + d, y) for x, y in pts], Q1 if i % 2 == 0 else N1, 1)
        for j in range(6):                                    # les bagues du câble
            t = (j + 0.5) / 6.0
            k = min(int(t * 3), 2)
            xa = pts[k][0] + (pts[k + 1][0] - pts[k][0]) * (t * 3 - k)
            ya = pts[k][1] + (pts[k + 1][1] - pts[k][1]) * (t * 3 - k)
            P.trait(xa - ep * 0.45, ya + 0.6, xa + ep * 0.45, ya - 0.6, N1, P.ep(0.5))
    pg.lucioles(P, [(30.0, 60.0), (84.0, 52.0), (100.0, 30.0), (140.0, 48.0), (24.0, 30.0), (160.0, 66.0), (118.0, 10.0)], graine=286)
    poussiere(P, 20, 0, 180, 70, 22, Q3, 287)
    # ---- Seconde passe : la vie de la caverne.
    pg.etincelle(P, 44.0, 22.0, coul=J3, d=0.1)
    pg.etincelle(P, 150.0, 52.0, coul=C3, d=0.6)
    pg.goutte(P, 88.0, -10.0, 71.0, coul=Q3, d=0.4, flaque=Q2)
    pg.yeux(P, 30.0, 66.0, coul=J3, d=0.2)
    pg.yeux(P, 176.0, 14.0, coul=O3, d=0.7, ecart=1.6)
    pg.souris(P, 96.0, 73.0, sens=-1, coul=G2)
    for i in range(5):                                          # les spores de la gelée, qui montent
        t = (p + i / 5.0) % 1.0
        P.point(50 + 6 * math.sin(t * 6 + i) + i * 2, 56 - 30 * t, Q3 if t < 0.6 else Q2)
    pg.papillon_de_nuit(P, 54.0, 58.0, 9.0, coul=Q3, d=0.3)


# =====================================================================================================================
# Le Marais des mises à jour : une eau grise et des roseaux qui clignotent sous un ciel bas où flotte, à la place du
# soleil, une immense barre de chargement arrêtée à 37 % ; une barque carrée glisse entre les roseaux ; brume froide.
# =====================================================================================================================
@decor("grande-panne", "marais-majs", soleil=(96.0, 14.0), tons=PANNE, nom="Le Marais des mises à jour", matiere=True)
def marais_majs(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=50.0, haut=0.16, halo=0.22, disque=0)
    tab.plan("nuages", 0.08)
    pg.voiles(P, y=-6.0, epais=9.0, seuil=0.52, graine=301)
    pg.voiles(P, y=30.0, epais=7.0, seuil=0.56, graine=302)
    # ---- La barre de chargement, immense, à la place du soleil : 37 %, et ses petits carreaux qui hésitent.
    bx, by, bw, bh = 44.0, 6.0, 104.0, 13.0
    halo(P, bx + bw * 0.2, by + bh / 2, 60, C1, 0.34, ry=26)
    P.rect(bx - 1.6, by - 1.6, bw + 3.2, bh + 3.2, T.CIEL[2])
    P.rect(bx - 1.6, by - 1.6, bw + 3.2, 0.6, T.CIEL[6])
    P.rect(bx, by, bw, bh, N0)
    plein = bw * 0.37
    P.rampe((X > bx) & (X < bx + plein) & (Y > by) & (Y < by + bh), 0.3 + 0.5 * (by + bh - Y) / bh + 0.25 * np.sin((X - bx) * 1.2 - p * 6.283),
            [C1, C2, C3], 0.5)
    for i in range(3):                                        # les trois carreaux suivants essaient, et renoncent
        if (int(p * 8) + i) % 4 == 0:
            P.rect(bx + plein + 1.2 + i * 3.6, by + 1.6, 2.6, bh - 3.2, C1)
    sept(P, bx + bw + 4.0, by + 2.0, "37", T.CIEL[8], l=4.0, h=8.0, ep=P.ep(0.7), pas=6.2)
    P.ell(bx + bw + 17.4, by + 3.2, 1.0, 1.0, T.CIEL[8])
    P.ell(bx + bw + 20.4, by + 9.0, 1.0, 1.0, T.CIEL[8])
    P.trait(bx + bw + 21.0, by + 2.0, bx + bw + 17.0, by + 10.0, T.CIEL[8])
    tab.plan("lointains", 0.2)
    pg.crete(P, lambda x: pg.profil(x, 49.0, 7.0, 30.0, 303), [T.CIEL[4], T.CIEL[5], T.CIEL[6], T.CIEL[7]], 0.6)
    for i in range(14):                                       # des pylônes et des arbres morts, loin, dans la brume
        x = 4 + 14 * i + 6 * hz(i, 1, 304)
        h = 5 + 9 * hz(i, 2, 304)
        P.trait(x, 50.0, x + (hz(i, 3, 304) - 0.5) * 2, 50.0 - h, T.CIEL[3])
        P.trait(x, 50.0 - h * 0.6, x + 2.0, 50.0 - h * 0.85, T.CIEL[3])
        P.trait(x, 50.0 - h * 0.4, x - 1.8, 50.0 - h * 0.7, T.CIEL[3])
    tab.plan("moyen", 0.5)
    # ---- La rive d'en face, ses roseaux ; puis l'eau, miroir gris du ciel et de la barre.
    f_rive = lambda x: 50.0 + 0.6 * np.sin(_a(x) / 9.0)
    pg.rive(P, f_rive, epais=1.8, joncs=170, graine=305)
    f_berge = lambda x: 73.0 + 1.0 * np.sin(_a(x) / 21.0) + 0.4 * np.sin(_a(x) / 5.0)
    pg.miroir(P, tab.derriere(), 51.0, ronds=((60.0, 62.0, 0.0), (130.0, 66.0, 0.5)), fonce=(60.0, 16.0), eclats=0.5, rides=0.07, graine=306)
    # Des îlots de roseaux qui clignotent : chaque quenouille est un voyant.
    for k, (ix, iy, n) in enumerate(((18, 58, 9), (46, 55, 6), (150, 57, 10), (176, 61, 8), (112, 54, 5), (84, 66, 7))):
        P.ell(ix, iy + 0.6, 2.2 + n * 0.6, 0.9, T.EAU[0])
        for i in range(n):
            x = ix + (i - n / 2) * 1.5 + hz(i, k, 307)
            h = 4 + 7 * hz(i, k + 9, 307)
            bal = 0.4 * onde(p, 0.1 * i + 0.3 * k)
            P.trait(x, iy, x + bal, iy - h, T.S0 if i % 2 else T.S1)
            if hz(i, k + 20, 307) < 0.6:
                vif = (p + hz(i, k + 30, 307)) % 1.0 < 0.4
                P.rect(x + bal - 0.4, iy - h - 1.6, 0.9, 1.8, (C3 if (i + k) % 3 else O3) if vif else T.S0)
                if vif:
                    halo(P, x + bal, iy - h - 0.8, 2.6, C2 if (i + k) % 3 else O2, 0.5)
    # La barque carrée (un pixel de bateau) et son passeur absent ; une lanterne à la proue.
    qx, qy = 100.0 + 1.5 * onde(p), 60.0 + 0.2 * onde(p, 0.25)
    for i in range(4):
        P.trait(qx - 9 + i, qy + 2.4 + i * 0.6, qx + 9 - i, qy + 2.4 + i * 0.6, T.EAU[0])
    P.rect(qx - 9.0, qy - 2.0, 18.0, 4.2, B1)
    P.rect(qx - 9.0, qy - 2.0, 18.0, 0.9, B3)
    P.rect(qx - 8.0, qy - 1.0, 16.0, 1.4, B2)
    P.rect(qx - 2.0, qy - 2.6, 4.0, 0.8, E4)
    P.trait(qx + 6.0, qy - 2.0, qx + 6.0, qy - 8.0, B1)
    pg.lanterne(P, qx + 6.0, qy - 8.2, corde=2.6)
    P.trait(qx - 6.0, qy - 2.4, qx - 13.0, qy + 3.0, B3)        # la perche
    # (un canard peut passer ici, vers (142, 64) : c'est un acteur de la scène, pas du décor)
    # Brume froide au ras de l'eau.
    for g, (y0, ep) in enumerate(((52.5, 2.2), (57.0, 1.6), (66.0, 1.8))):
        voile(P, np.abs(Y - y0 - np.sin(X / 19.0 + g)) < ep * (0.4 + pg.fbm((X + 3.0 * onde(p, 0.2 * g)) / 22.0, Y / 3.0, 3, 308 + g)),
              T.CIEL[9], 0.5)
    tab.plan("premier", 1.0)
    # ---- La berge : boue grise, planches d'un ponton, roseaux sombres qui encadrent, voyants qui veillent.
    pg.sol(P, f_berge, [T.N0, T.N1, T.N2, T.EAU[3], T.EAU[4]], chemin=77.6, graine=309, lisere=2.0)
    for x in np.arange(64.0, 132.0, 5.6):                      # le ponton
        P.poly([(x, 73.4), (x + 4.8, 73.4), (x + 5.4, 76.0), (x - 0.6, 76.0)], B2)
        P.trait(x, 73.4, x + 4.8, 73.4, B3)
    for x in (66.0, 96.0, 128.0):
        P.rect(x, 71.0, 1.4, 6.0, B1)
        P.point(x + 0.3, 71.0, B3)
    pg.touffes(P, f_berge, n=120, haut=3.0, graine=310)
    pg.roseaux(P, -6.0, 14.0, n=10, haut=(14.0, 34.0), penche=1.0, graine=311)
    pg.roseaux(P, 178.0, 198.0, n=10, haut=(14.0, 36.0), penche=-1.0, graine=312)
    for i, (x, y) in enumerate(((4.0, 52.0), (11.0, 46.0), (186.0, 50.0), (192.0, 58.0), (180.0, 44.0))):
        voyant(P, x, y, C3, T.N1, d=0.2 * i, part=0.4, r=0.6)
    pg.lucioles(P, [(30.0, 70.0), (150.0, 71.0), (60.0, 77.0), (120.0, 78.0)], graine=313)
    # ---- Seconde passe : le marais se peuple.
    # La pluie s'est arrêtée en l'air, à 37 % de sa chute : des gouttes immobiles, qui tremblent.
    for i in range(46):
        x, y = 4 + 184 * hz(i, 1, 314), -10 + 54 * hz(i, 2, 314)
        tr = 0.2 * onde(p, hz(i, 3, 314))
        P.trait(x, y + tr, x - 0.3, y + 1.6 + tr, T.CIEL[9] if i % 3 else C3)
    # Un héron gris, immobile sur une patte ; il cligne ; son reflet tremble.
    hx_, hy_ = 34.0, 70.0
    P.trait(hx_, hy_, hx_, hy_ - 7.0, O1)
    P.ell(hx_ + 0.4, hy_ - 9.0, 3.0, 2.2, G3)
    P.ell(hx_ - 1.0, hy_ - 8.6, 2.0, 1.4, G4)
    P.courbe([(hx_ + 2.4, hy_ - 10.0), (hx_ + 4.0, hy_ - 13.0), (hx_ + 2.6, hy_ - 16.0)], G4, P.ep(0.6))
    P.ell(hx_ + 2.8, hy_ - 16.6, 1.1, 0.9, G4)
    P.trait(hx_ + 3.6, hy_ - 16.4, hx_ + 6.6, hy_ - 15.8, O2)
    P.point(hx_ + 3.0, hy_ - 16.8, ENCRE if int(p * 8) % 8 else G4)
    for j in range(4):
        if (j + int(p * 8)) % 3:
            P.trait(hx_ - 1.2, hy_ + 1.4 + j * 1.2, hx_ + 1.6, hy_ + 1.4 + j * 1.2, T.EAU[6])
    # Des nénuphars-mises à jour : une flèche qui tourne sur chacun, sans jamais finir son tour.
    for i, (x, y, r) in enumerate(((66.0, 64.0, 4.4), (126.0, 61.0, 3.6), (160.0, 68.0, 4.8), (86.0, 56.0, 2.6))):
        P.ell(x, y + 0.5, r, r * 0.36, T.EAU[0])
        P.ell(x, y, r, r * 0.36, T.S2)
        P.ell(x - r * 0.2, y - r * 0.08, r * 0.6, r * 0.18, T.S3)
        a = 2 * math.pi * (p + 0.25 * i)
        P.trait(x, y, x + r * 0.7 * math.cos(a), y + r * 0.26 * math.sin(a), C3)
        P.point(x + r * 0.7 * math.cos(a), y + r * 0.26 * math.sin(a), BLANC)
    # Une bouée de signalisation et son voyant orange ; elle penche avec le clapot.
    bx_ = 172.0
    pen = 0.8 * onde(p, 0.3)
    P.poly([(bx_ - 3, 60.0), (bx_ + 3, 60.0), (bx_ + 1.4 + pen, 51.0), (bx_ - 1.4 + pen, 51.0)], O1)
    P.rect(bx_ - 2.4 + pen * 0.5, 55.0, 4.8, 1.4, BLANC)
    voyant(P, bx_ + pen, 49.6, O3, K1, d=0.2, part=0.4, r=0.9)
    P.ell(bx_, 60.4, 4.0, 0.9, T.EAU[1])
    # Sur le ponton : une lanterne, une canne à pêche et son bouchon qui danse, un seau de pixels.
    P.courbe([(70.0, 73.0), (86.0, 58.0), (104.0, 50.0)], B1, 1)
    P.trait(104.0, 50.0, 104.0, 64.0 + 0.5 * onde(p), T.CIEL[8])
    P.ell(104.0, 64.6 + 0.5 * onde(p), 0.9, 0.9, O2)
    pg.goutte(P, 104.0, 64.6, 64.6, coul=T.EAU[8], d=0.0, flaque=T.EAU[8])
    P.poly([(58.0, 69.0), (64.0, 69.0), (63.2, 73.4), (58.8, 73.4)], G3)
    P.rect(57.6, 68.4, 6.8, 0.9, G4)
    for i in range(4):
        P.rect(59.0 + (i % 2) * 2.4, 66.6 - (i // 2) * 1.6, 1.6, 1.6, (C2, O2, J2, V4)[i])
    pg.papillon_de_nuit(P, 106.0, 50.0, 5.0, coul=BLANC, d=0.2)
    pg.yeux(P, 8.0, 64.0, coul=J3, d=0.5)                       # une grenouille ? non : quelque chose, dans les roseaux
    pg.araignee(P, 190.0, 44.0, 6.0, d=0.6)


# =====================================================================================================================
# La file d'impression : un quai fait de rames de papier où des feuilles jaunies attendent debout en rang, devant une
# estrade où trône une énorme imprimante beige au voyant orange (la clé) ; lumière de réserve à fournitures.
# =====================================================================================================================
@decor("grande-panne", "file-impression", soleil=(60.0, -14.0), tons=PANNE, nom="La file d'impression", matiere=True)
def file_impression(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    P.rampe(np.ones(X.shape, dtype=bool), 0.42 + 0.0035 * (Y + 16) + 0.18 * (pg.fbm(X / 14.0, Y / 9.0, 3, 320) - 0.5), [G0, G1, G2, G3], 0.7)
    tab.plan("lointains", 0.2)
    # ---- Le fond de la réserve : étagères métalliques en fuite, cartons, ramettes, cartouches ; un néon qui grésille.
    for j, y in enumerate((-12.0, 4.0, 20.0, 36.0)):
        P.rect(-6.0, y + 12.0, 112.0, 1.0, G0)
        x = -4.0
        i = 0
        while x < 104:
            w = 6 + 8 * hz(i, j, 321)
            h = 5 + 6 * hz(i, j + 7, 321)
            sorte = int(hz(i, j + 14, 321) * 4)
            if sorte == 0:                                    # un carton
                P.rect(x, y + 12 - h, w, h, B3)
                P.rect(x, y + 12 - h, w, 0.8, E3)
                P.rect(x + w / 2 - 0.4, y + 12 - h, 0.8, h, B2)
            elif sorte == 1:                                  # des ramettes
                papiers(P, x, y + 12.0, w, int(h / 0.8), 322 + i + j * 40)
            elif sorte == 2:                                  # des cartouches
                for k in range(int(w / 2.4)):
                    P.rect(x + k * 2.4, y + 12 - 4.0, 2.0, 4.0, (C2, O2, J2, ENCRE)[k % 4])
                    P.rect(x + k * 2.4, y + 12 - 4.0, 2.0, 0.6, G4)
            x += w + 1.2
            i += 1
    for x in (-2.0, 34.0, 70.0, 104.0):
        P.rect(x, -16.0, 1.2, 68.0, G0)
    voile(P, (X < 108) & (Y < 52), G0, np.clip(0.5 - (X + 6) / 200.0, 0, 0.5))
    neon(P, 20.0, 70.0, -11.0, C2, C3, vacille=0.14, lueur=9.0)
    tab.plan("moyen", 0.5)
    # ---- L'estrade et l'imprimante : énorme, beige, un seul voyant orange, une feuille coincée à mi-chemin.
    ex0 = 112.0
    P.rect(ex0, 50.0, 86.0, 30.0, B1)
    P.rampe((X > ex0) & (Y > 50) & (Y < 80), 0.4 + 0.3 * (pg.fbm(X / 1.4, Y / 16.0, 2, 323) - 0.5) + 0.01 * (X - ex0), [B1, B2, B3], 0.6)
    P.rect(ex0 - 1.5, 48.6, 90.0, 1.8, B3)
    for j in range(3):                                        # les marches
        P.rect(ex0 - 16 + j * 5.4, 70.0 - j * 7.0 + 8, 16.0 - j * 5.4, 7.0, B2)
        P.rect(ex0 - 16 + j * 5.4, 70.0 - j * 7.0 + 8, 16.0 - j * 5.4, 0.8, B3)
    ix0, iy0, iw, ih = 120.0, 10.0, 68.0, 38.6
    corps = (X > ix0) & (X < ix0 + iw) & (Y > iy0) & (Y < iy0 + ih)
    P.rampe(corps, 0.55 - 0.3 * (X - ix0 - iw * 0.3) / iw + 0.012 * (iy0 + ih / 2 - Y) + 0.1 * (pg.fbm(X / 7.0, Y / 5.0, 2, 324) - 0.5),
            [E1, E2, E3, E4, E5], 0.6)
    P.rect(ix0 - 2.0, iy0 - 3.0, iw + 4.0, 4.0, E4)             # le capot
    P.rect(ix0 - 2.0, iy0 - 3.0, iw + 4.0, 0.8, E5)
    P.rect(ix0 - 2.0, iy0 + 0.6, iw + 4.0, 0.5, E2)
    P.poly([(ix0 + 8, iy0 - 3.0), (ix0 + iw - 8, iy0 - 3.0), (ix0 + iw - 14, iy0 - 15.0), (ix0 + 14, iy0 - 15.0)], E2)     # le bac d'entrée
    papiers(P, ix0 + 16.0, iy0 - 3.4, iw - 32.0, 12, 325)
    P.rect(ix0 + 6, iy0 + 14.0, iw - 12, 3.6, ENCRE)             # la fente de sortie
    sort = 5.0 + 1.2 * onde(p)                                  # la feuille coincée : elle sort, elle rentre
    P.poly([(ix0 + 16, iy0 + 15.6), (ix0 + iw - 16, iy0 + 15.6), (ix0 + iw - 14, iy0 + 15.6 + sort), (ix0 + 14, iy0 + 15.6 + sort)], BLANC)
    for j in range(int(sort / 1.3)):
        P.rect(ix0 + 19, iy0 + 16.6 + j * 1.3, iw - 40 + (j % 2) * 6, 0.4, G3)
    P.rect(ix0 + 4, iy0 + 26.0, iw - 8, 10.0, E2)               # le bac de papier, tiroir entrouvert
    P.rect(ix0 + 5, iy0 + 27.0, iw - 10, 8.0, E3)
    P.rect(ix0 + iw / 2 - 5, iy0 + 30.0, 10.0, 1.6, E1)
    P.rect(ix0 + iw - 20, iy0 + 3.6, 15.0, 8.0, G1)             # le panneau de commande
    P.rect(ix0 + iw - 19, iy0 + 4.4, 8.0, 3.4, ENCRE)
    sept(P, ix0 + iw - 18.4, iy0 + 5.0, "37", O2, l=1.6, h=2.2, ep=1, pas=2.6)
    for i in range(3):
        P.rect(ix0 + iw - 19 + i * 3.0, iy0 + 9.0, 2.0, 1.6, G3)
    voyant(P, ix0 + iw - 8.0, iy0 + 6.0, O2, K1, part=0.5, r=1.3)
    halo(P, ix0 + iw - 8.0, iy0 + 6.0, 14.0, O2, 0.35 if (p % 1.0) < 0.5 else 0.0)
    for i in range(5):                                        # la grille d'aération : un souffle de papier
        P.rect(ix0 + 6, iy0 + 4.0 + i * 1.6, 18.0, 0.6, E1)
    cable(P, [(ix0 + iw, iy0 + 30), (ix0 + iw + 8, iy0 + 40), (ix0 + iw + 6, 49.0)], 1.2, G0, G2, None)
    rai(P, 60.0, -16.0, 78.0, 22.0, 0.5, BLANC, 0.3, 26, 326)
    # ---- Le quai : des rames de papier empilées en dalles ; les feuilles jaunies qui attendent debout, en rang.
    sol = Y > 62.0
    quai = sol & (X < ex0 - 1.5)
    dallage(P, quai, 150.0, 46.0, E5, E4, larg=7.0, prof=1.0, joint=E2)
    P.remplir(quai & (((Y - 62) % 3.0) < 0.5) & (P.T < 0.5), E3)
    P.rect(-6.0, 61.0, ex0 - 10, 1.2, E3)
    for rang, (yq, k) in enumerate(((64.5, 0.8), (68.5, 1.0))):
        for i in range(13 - rang * 2):
            x = 6 + i * (7.6 + rang * 1.6) + rang * 3
            if x > 92:
                continue
            hgt = (7.0 + 1.6 * hz(i, rang, 327)) * k
            dy = 0.4 * k if int(p * 8 + i * 3 + rang) % 7 == 0 else 0.0
            penche = (hz(i, rang + 5, 327) - 0.5) * 1.2
            P.ell(x + 1.6 * k, yq + 0.3, 2.4 * k, 0.5 * k, E2)
            P.poly([(x, yq), (x + 3.4 * k, yq), (x + 3.4 * k + penche, yq - hgt - dy), (x + penche, yq - hgt - dy)], (J3, E5, E4)[(i + rang) % 3])
            P.trait(x + 3.4 * k, yq, x + 3.4 * k + penche, yq - hgt - dy, E3)
            for j in range(3):
                P.rect(x + 0.7 * k + penche * 0.5, yq - hgt * (0.3 + 0.12 * j) - dy, 2.0 * k, 0.4, G3)
            P.point(x + 0.9 * k + penche, yq - hgt * 0.8 - dy, ENCRE)
            P.point(x + 2.2 * k + penche, yq - hgt * 0.8 - dy, ENCRE)
    tab.plan("premier", 1.0)
    # ---- Premier plan : à gauche, une palette de rames et un diable ; des feuilles qui volent ; l'ombre du bas.
    P.rect(-6.0, 70.0, 26.0, 2.0, B2)
    for x in (-4.0, 6.0, 16.0):
        P.rect(x, 72.0, 3.0, 8.0, B1)
    for j in range(4):
        for i in range(2 + (j % 2)):
            papiers(P, -5.0 + i * 9.0 + (j % 2) * -3.0, 70.0 - j * 8.0, 8.4, 9, 328 + i + j * 4)
            P.rect(-5.0 + i * 9.0 + (j % 2) * -3.0, 70.0 - j * 8.0 - 4.6, 8.4, 1.6, (C2, O2, V4)[(i + j) % 3])
    voile(P, (X < 22) & (Y > 36), N0, 0.35)
    tickets(P, 100.0, 20.0, 60.0, 5, 329, coul=BLANC)
    voile(P, Y > 77.0, G0, 0.25)
    poussiere(P, 30, -10, 150, 60, 28, BLANC, 330)
    # ---- Seconde passe : la vie de la réserve.
    pg.souris(P, 44.0, 15.6, sens=1, coul=G3)                   # sur une étagère
    pg.araignee(P, 96.0, -16.0, 12.0, d=0.1)
    pg.toile_araignee(P, 108.0, -16.0, 9.0, sens=(-1, 1), coul=G4)
    pg.goutte(P, 150.0, 49.0, 58.0, coul=ENCRE, d=0.5)           # une cartouche qui fuit, sous l'estrade
    for i in range(5):                                          # la grille d'aération souffle : des rubans de papier y flottent
        l = 3.0 + 1.5 * onde(p, 0.2 * i)
        P.trait(126.0, 14.0 + i * 1.6, 126.0 - l, 14.4 + i * 1.6 + 0.6 * onde(p * 2, 0.1 * i), BLANC)
    pg.papillon_de_nuit(P, 45.0, -10.0, 7.0, coul=BLANC, d=0.4)
    P.rect(98.0, 56.0, 6.0, 5.0, B3)                             # un carton dont le rabat bat
    P.poly([(98.0, 56.0), (104.0, 56.0), (105.0, 54.0 - 0.8 * onde(p)), (99.0, 54.0 - 0.8 * onde(p))], E3)
    pg.vapeur(P, 154.0, 8.0, coul=G4, h=12.0, d=0.3)             # l'imprimante chauffe
    pg.yeux(P, 12.0, 44.0, coul=J3, d=0.7)


# =====================================================================================================================
# La Citadelle du nuage : des remparts blancs posés sur une mer de brume, un donjon et sa gargouille au bord du vide (la
# clé), un escalier dont les dernières marches sont à moitié transparentes ; très loin dessous, les lumières de
# l'ordinateur comme une ville la nuit. Le sol est à y = 70.
# =====================================================================================================================
@decor("grande-panne", "citadelle-nuage", soleil=(30.0, -4.0), tons=PANNE, nom="La Citadelle du nuage", matiere=True)
def citadelle_nuage(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=100.0, haut=0.0, halo=0.2, etoiles=0.5, lune=(30.0, -4.0, 4.2), disque=0)
    halo(P, 30.0, -4.0, 26.0, T.CIEL[5], 0.4)
    # ---- Tout en bas, très loin : l'ordinateur, une ville de voyants, vue à travers les trouées de la brume.
    ville = Y > 56.0
    P.rampe(ville, 0.2 + 0.2 * (pg.fbm(X / 12.0, Y / 4.0, 3, 340) - 0.5), [ENCRE, N0, N1], 0.8)
    for i in range(150):
        x, y = -6 + 204 * hz(i, 1, 341), 58 + 22 * hz(i, 2, 341)
        if (p + hz(i, 3, 341)) % 1.0 < 0.75:
            P.point(x, y, (J3, O2, C2, J2, BLANC, O3)[i % 6])
    for j in range(5):                                        # les avenues : des lignes de voyants
        y = 60 + j * 4.2
        for x in np.arange(-6, 198, 3.0 + j * 0.8):
            if (int(x * 3) + int(p * 8)) % 5:
                P.point(x + j * 1.3, y, J2 if j % 2 else O2)
    tab.plan("nuages", 0.08)
    pg.cumulus(P, [(150, 16, 50, 9.0, 342, 9, 0.0), (60, 30, 36, 6.0, 343, 7, 0.4), (176, -6, 30, 5.0, 344, 6, 0.7)], dessous=-0.6)
    tab.plan("lointains", 0.2)
    # ---- La mer de brume : des bancs qui roulent lentement, avec des trouées sur la ville.
    for g, (y0, ep, c0) in enumerate(((58.0, 5.0, T.CIEL[6]), (63.0, 4.0, T.CIEL[8]), (69.0, 4.0, T.CIEL[9]), (76.0, 5.0, T.CIEL[10]))):
        d = pg.fbm((X + 2.5 * onde(p, 0.2 * g)) / 24.0, Y / 6.0, 3, 345 + g)
        m = (Y > y0 - ep * d * 1.6) & (d > 0.5 - 0.03 * g) & (Y > 54)
        P.rampe(m, 0.3 + 1.6 * (d - 0.5) - 0.04 * (Y - y0), [T.CIEL[3], T.CIEL[5], T.CIEL[7], c0], 0.7)
    # D'autres tours de la citadelle, loin, sur leurs propres nuages.
    for i, (x, w, top) in enumerate(((158.0, 9.0, 34.0), (176.0, 6.0, 42.0), (18.0, 7.0, 44.0))):
        P.rampe((np.abs(X - x) < w / 2) & (Y > top) & (Y < 60), 0.5 + 0.4 * (X - x) / w, [T.CIEL[6], T.CIEL[8], T.CIEL[10]], 0.5)
        for k in range(int(w / 2)):
            P.rect(x - w / 2 + k * 2.0, top - 1.2, 1.2, 1.4, T.CIEL[8])
        P.poly([(x - w / 2 - 0.6, top - 1.0), (x + w / 2 + 0.6, top - 1.0), (x, top - 8.0)], T.CIEL[4])
        P.rect(x - 0.6, top + 5, 1.2, 2.2, J3 if (p + 0.3 * i) % 1.0 < 0.8 else T.CIEL[4])
    tab.plan("moyen", 0.5)
    # ---- Le donjon : pierre blanche, créneaux, toit bleu nuit, fenêtres en ogive ; le drapeau à l'emblème du nuage.
    dx, dw, dtop, dbas = 108.0, 34.0, 4.0, 66.0
    don = (np.abs(X - dx) < dw / 2) & (Y > dtop) & (Y < dbas)
    u = (X - dx) / (dw / 2)
    P.rampe(don, 0.72 - 0.34 * u + 0.12 * (pg.fbm(X / 3.0, Y / 2.0, 3, 349) - 0.5), [T.CIEL[5], T.CIEL[7], T.CIEL[9], T.CIEL[11], BLANC], 0.6)
    P.remplir(don & (((Y - dtop) % 4.0) < 0.4), T.CIEL[7])
    P.remplir(don & ((((X - dx) / 5.0 + np.floor((Y - dtop) / 4.0) * 0.5) % 1.0) < 0.08), T.CIEL[7])
    for k in range(7):                                        # créneaux
        P.rect(dx - dw / 2 - 1.5 + k * 5.4, dtop - 4.0, 3.4, 4.4, BLANC if k < 4 else T.CIEL[9])
    P.rect(dx - dw / 2 - 1.5, dtop, dw + 3.0, 1.6, T.CIEL[8])
    P.poly([(dx - dw / 2 + 4, dtop - 4.0), (dx + dw / 2 - 4, dtop - 4.0), (dx, dtop - 20.0)], N1)
    P.poly([(dx - 2, dtop - 4.0), (dx + dw / 2 - 4, dtop - 4.0), (dx, dtop - 20.0)], N0)
    P.poly([(dx - dw / 2 + 4, dtop - 4.0), (dx - dw / 2 + 8, dtop - 4.0), (dx, dtop - 20.0)], N3)
    P.trait(dx, dtop - 20.0, dx, dtop - 28.0, G1)
    v = onde(p)
    P.poly([(dx, dtop - 28.0), (dx + 6.0, dtop - 27.0 + 0.6 * v), (dx + 11.0, dtop - 28.4 - 0.6 * v), (dx + 11.0, dtop - 24.4 - 0.6 * v),
            (dx + 6.0, dtop - 23.0 + 0.6 * v), (dx, dtop - 24.0)], C2)
    P.ell(dx + 5.6, dtop - 25.6 + 0.4 * v, 2.0, 1.1, BLANC)
    for (wx_, wy_) in ((dx - 7.0, 16.0), (dx + 6.0, 16.0), (dx - 0.5, 34.0)):
        P.ell(wx_, wy_, 2.2, 2.6, N0, cond=Y < wy_ + 0.4)
        P.rect(wx_ - 2.2, wy_, 4.4, 6.0, N0)
        vif = (p + wx_ * 0.01) % 1.0 < 0.85
        P.ell(wx_, wy_ + 0.4, 1.5, 1.9, J3 if vif else J1, cond=Y < wy_ + 0.8)
        P.rect(wx_ - 1.5, wy_ + 0.4, 3.0, 5.0, J3 if vif else J1)
        P.rect(wx_ - 0.2, wy_ - 1.2, 0.4, 6.6, N0)
    P.ell(dx, 60.0, 5.0, 6.0, N0, cond=Y < 60.5)                # la porte
    P.rect(dx - 5.0, 60.0, 10.0, 6.0, N0)
    P.ell(dx, 60.5, 4.0, 5.0, B2, cond=Y < 61)
    P.rect(dx - 4.0, 60.5, 8.0, 5.5, B2)
    P.rect(dx - 0.2, 56.0, 0.4, 10.0, B1)
    # La gargouille de pierre grise, au bord du vide : elle crache un filet de brume, sa queue remue.
    gx, gy = dx - dw / 2 - 1.0, 26.0
    P.poly([(gx + 2, gy - 2.0), (gx - 10, gy - 3.4), (gx - 15, gy - 1.0), (gx - 10, gy + 1.6), (gx + 2, gy + 2.0)], G2)
    P.poly([(gx + 2, gy - 2.0), (gx - 10, gy - 3.4), (gx - 15, gy - 1.0), (gx - 10, gy - 1.0), (gx + 2, gy)], G3)
    P.ell(gx - 13.0, gy - 2.6, 3.4, 2.8, G3)
    P.ell(gx - 13.6, gy - 3.2, 2.2, 1.6, G4)
    P.poly([(gx - 12.0, gy - 5.0), (gx - 10.6, gy - 8.4), (gx - 10.0, gy - 4.6)], G2)        # les cornes
    P.poly([(gx - 15.0, gy - 5.0), (gx - 15.4, gy - 8.0), (gx - 13.6, gy - 5.0)], G2)
    P.point(gx - 14.6, gy - 3.0, J3 if int(p * 8) % 8 else G1, 2)                           # son œil cligne
    P.poly([(gx - 16.2, gy - 2.2), (gx - 18.6, gy - 1.2), (gx - 16.0, gy - 0.6)], G1)        # la gueule ouverte
    P.poly([(gx - 4, gy - 3.0), (gx - 1.0, gy - 8.6), (gx + 1.6, gy - 2.6)], G1)             # une aile repliée
    P.courbe([(gx + 1, gy + 1.6), (gx - 2, gy + 5.0), (gx + 1.0 + 0.8 * onde(p), gy + 8.0)], G2, P.ep(0.7), 1)
    for i in range(5):
        t = (p + i / 5.0) % 1.0
        voile(P, np.hypot(X - (gx - 18.6 - 1.5 * t), Y - (gy - 1.0 + 16 * t)) < 0.8 + 1.6 * t, T.CIEL[10], 0.8 - 0.7 * t)
    # ---- Les remparts : le chemin de ronde où l'on marche (y = 70), créneaux, braseros bleus.
    trou = ((np.abs(X - 60) < 18) & (Y > 72.0)) | ((np.abs(X - 150) < 12) & (Y > 73.0))        # deux brèches dans le rempart
    rem = (Y > 66.0) & ~trou
    P.rampe(trou, 0.25 + 0.3 * (pg.fbm(X / 6.0, Y / 2.0, 2, 354) - 0.5), [ENCRE, N0, N1], 0.8)   # par elles, la ville, tout en bas
    for i in range(60):
        x, y = (42 + 36 * hz(i, 1, 355), 72.6 + 7 * hz(i, 2, 355)) if i % 3 else (138 + 24 * hz(i, 1, 355), 73.6 + 6 * hz(i, 2, 355))
        if (p + hz(i, 3, 355)) % 1.0 < 0.75:
            P.point(x, y, (J3, O2, C2, J2, BLANC, O3)[i % 6])
    P.rampe(rem, 0.7 - 0.045 * (Y - 66) + 0.12 * (pg.fbm(X / 4.0, Y / 2.0, 3, 350) - 0.5), [T.CIEL[4], T.CIEL[6], T.CIEL[8], T.CIEL[10], BLANC], 0.6)
    P.remplir(rem & (((Y - 66) % 3.6) < 0.4), T.CIEL[6])
    P.remplir(rem & ((((X) / 6.0 + np.floor((Y - 66) / 3.6) * 0.5) % 1.0) < 0.07), T.CIEL[6])
    P.remplir((Y > 66.0) & (Y < 66.7), BLANC)
    for x in np.arange(-6.0, 198.0, 9.0):                       # les créneaux du parapet, derrière le chemin
        if abs(x + 2.5 - dx) > dw / 2 + 2:
            P.rect(x, 60.6, 5.0, 5.6, T.CIEL[9])
            P.rect(x, 60.6, 5.0, 0.8, BLANC)
            P.rect(x + 4.2, 60.6, 0.8, 5.6, T.CIEL[6])
    for bx_ in (20.0, 178.0):                                   # braseros : une flamme cyan
        P.rect(bx_ - 0.6, 56.0, 1.2, 10.0, G1)
        P.poly([(bx_ - 2.6, 53.0), (bx_ + 2.6, 53.0), (bx_ + 1.6, 56.0), (bx_ - 1.6, 56.0)], G0)
        f = 0.8 * onde(p * 2, bx_ * 0.01)
        P.poly([(bx_ - 1.8, 53.0), (bx_ + 1.8, 53.0), (bx_ + f, 46.6)], C2)
        P.poly([(bx_ - 0.9, 53.0), (bx_ + 0.9, 53.0), (bx_ + f * 0.6, 49.4)], C3)
        halo(P, bx_, 50.0, 12.0, C1, 0.36)
    # L'escalier qui monte vers le vide : ses dernières marches sont encore à moitié transparentes.
    for i in range(9):
        x, y = 150.0 + i * 4.4, 66.0 - i * 3.2
        solide = max(0.0, 1.0 - i / 6.5)
        m = (X > x) & (X < x + 5.0) & (Y > y - 3.2) & (Y < y)
        voile(P, m, T.CIEL[9], 0.2 + 0.8 * solide if i < 8 else 0.14)
        voile(P, m & (Y < y - 2.4), BLANC, 0.3 + 0.7 * solide)
        if i > 5 and (p + 0.2 * i) % 1.0 < 0.5:
            P.point(x + 2.5, y - 4.4, C3)
    tab.plan("premier", 1.0)
    # ---- Premier plan : le merlon sombre du rempart en bas, deux hampes et leurs fanions, la brume qui déborde.
    bas = (Y > 77.0) & ~((np.abs(X - 60) < 18) | (np.abs(X - 150) < 12))
    P.rampe(bas, 0.3 + 0.3 * (pg.fbm(X / 5.0, Y / 2.0, 2, 351) - 0.5), [N0, N1, N2], 0.8)
    for x in np.arange(-6.0, 198.0, 14.0):
        if abs(x + 4 - 60) < 20 or abs(x + 4 - 150) < 14:
            continue
        P.rect(x, 74.0, 8.0, 3.4, N1)
        P.rect(x, 74.0, 8.0, 0.6, T.CIEL[5])
    for (x, cote) in ((6.0, 1), (188.0, -1)):
        P.rect(x - 0.6, 20.0, 1.2, 60.0, N0)
        P.poly([(x, 20.0), (x + cote * 9.0, 22.0 + v), (x + cote * 15.0, 20.6 - v), (x + cote * 9.0, 26.0 + v), (x, 27.0)], V3)
        P.poly([(x, 20.0), (x + cote * 9.0, 22.0 + v), (x + cote * 9.0, 24.0 + v), (x, 23.6)], V4)
    d = pg.fbm((X + 3.0 * onde(p)) / 18.0, Y / 4.0, 3, 352)
    voile(P, (Y > 70.0 + 8 * (1 - d)) & ((X < 30) | (X > 162)), T.CIEL[10], 0.6)
    pg.lucioles(P, [(40.0, 40.0), (70.0, 22.0), (140.0, 8.0), (166.0, 30.0), (12.0, 10.0)], graine=353)
    # ---- Seconde passe : la vie du rempart.
    pg.papillon_de_nuit(P, 20.0, 48.0, 5.0, coul=BLANC)
    pg.papillon_de_nuit(P, 178.0, 48.0, 5.0, coul=BLANC, d=0.5)
    pg.avion_papier(P, 190.0, 10.0, 30.0, 40.0, coul=BLANC, d=0.2)     # un message qui s'envole de la tour
    # Une étoile filante, de loin en loin.
    if int(p * 8) in (1, 2):
        P.trait(60.0 + int(p * 8) * 8, -10.0 + int(p * 8) * 2, 54.0 + int(p * 8) * 8, -11.6 + int(p * 8) * 2, BLANC)
    P.ell(92.0, 65.0, 2.2, 1.4, G4)                              # un chat de pierre ? non : un vrai, endormi sur le parapet
    P.ell(94.0, 64.2, 1.2, 1.0, G4)
    P.poly([(93.4, 63.4), (93.8, 62.4), (94.4, 63.4)], G4)
    P.courbe([(90.0, 65.6), (88.0, 66.4), (87.0, 65.4 + 0.5 * onde(p))], G4, 1)


# =====================================================================================================================
# Le dossier Temp : un grenier grand comme une ville. Des piles de dossiers étiquetés qui montent jusqu'au ciel, des
# allées poussiéreuses, des mots raturés sur les murs, une lumière grise et provisoire.
# =====================================================================================================================
def tour_dossiers(P, x, w, top, bas, graine, sombre=0.0, teintes=None):
    """Une pile de dossiers haute comme un immeuble : des tranches de couleurs passées, des étiquettes, des feuilles qui
    dépassent ; elle penche un peu."""
    teintes = teintes or (E3, E4, J1, K2, G3, E2, O1, V3, G2, E4)
    y = bas
    i = 0
    while y > top:
        h = 1.6 + 2.2 * hz(i, 1, graine)
        d = (hz(i, 2, graine) - 0.5) * 2.0 + (bas - y) * 0.012 * (1 if graine % 2 else -1)
        c0 = teintes[int(hz(i, 3, graine) * len(teintes))]
        P.rect(x - w / 2 + d, y - h, w, h, c0)
        P.rect(x - w / 2 + d, y - h, w, 0.4, E5)
        P.rect(x + w / 2 + d - 0.8, y - h, 0.8, h, G1)
        if hz(i, 4, graine) < 0.45 and h > 2.2:
            P.rect(x - w / 2 + d + 1.0, y - h + 0.8, min(w * 0.4, 4.0), 1.0, BLANC)        # l'étiquette
            P.rect(x - w / 2 + d + 1.4, y - h + 1.2, min(w * 0.25, 2.4), 0.4, G1)
        if hz(i, 5, graine) < 0.2:
            P.rect(x + w / 2 + d, y - h + 0.6 + 0.2 * onde(P.p, hz(i, 6, graine)), 1.6, 0.5, BLANC)   # une feuille qui dépasse
        y -= h
        i += 1
    if sombre:
        voile(P, (np.abs(P.X - x) < w / 2 + 2) & (P.Y > top) & (P.Y < bas), G0, sombre)


@decor("grande-panne", "dossier-temp", soleil=(120.0, -30.0), tons=PANNE, nom="Le dossier Temp", matiere=True)
def dossier_temp(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    # ---- Le « ciel » du grenier : une charpente très haute, perdue dans une lumière grise ; une lucarne.
    P.rampe(np.ones(X.shape, dtype=bool), 0.75 - 0.006 * (Y + 16) - 0.002 * np.abs(X - 120) + 0.14 * (pg.fbm(X / 22.0, Y / 12.0, 3, 360) - 0.5),
            [G1, G2, G3, G4, T.CIEL[9]], 0.8)
    for i in range(9):                                        # les chevrons
        x = -10 + i * 26
        P.poly([(x, -16.0), (x + 3.0, -16.0), (x + 43.0, 30.0), (x + 40.0, 30.0)], G2)
    P.rect(-6.0, 8.0, 204.0, 1.6, G2)
    voile(P, Y < 30, G3, 0.4)
    tab.plan("lointains", 0.2)
    # ---- Les piles lointaines : une ville de dossiers, pâle dans la poussière.
    pale = (G3, G4, T.CIEL[7], G3, G4, T.CIEL[8])
    for i in range(16):
        x = -2 + 13 * i + 4 * hz(i, 1, 361)
        tour_dossiers(P, x, 6 + 4 * hz(i, 2, 361), 6 + 30 * hz(i, 3, 361), 62.0, 362 + i, teintes=pale)
    rai(P, 120.0, -16.0, 78.0, 30.0, -0.3, T.CIEL[10], 0.34, 40, 363)
    tab.plan("moyen", 0.5)
    # ---- L'allée : un plancher gris de poussière qui fuit entre les piles ; des traces de pas (les seuls, les nôtres).
    sol = Y > 60.0
    dallage(P, sol, 104.0, 48.0, G3, G2, larg=5.0, prof=0.9, joint=G1)
    voile(P, sol & (np.abs(X - 104 - (Y - 48) * -0.3) < (Y - 48) * 0.5), T.CIEL[9], 0.3)
    # Les piles du milieu : de chaque côté de l'allée, hautes, colorées, étiquetées ; elles penchent.
    for i, (x, w, top) in enumerate(((10, 15, -18), (30, 12, 6), (52, 10, 20), (154, 12, 12), (174, 15, -18), (136, 9, 26), (70, 8, 30))):
        tour_dossiers(P, x, w, top, 72.0 - abs(x - 100) * 0.06, 380 + i, sombre=0.12 if x < 100 else 0.0)
    # Les mots raturés sur le mur de carton du fond : des lignes barrées, une seule épargnée.
    P.rect(84.0, 30.0, 40.0, 24.0, E3)
    P.rect(84.0, 30.0, 40.0, 0.8, E4)
    for j in range(6):
        l = (26, 32, 18, 30, 22, 28)[j]
        P.rect(88.0, 33.4 + j * 3.4, l, 0.9, G1)
        if j != 4:
            P.trait(87.0, 33.0 + j * 3.4 + 1.4, 89.0 + l, 33.0 + j * 3.4 - 0.2, O1)
    voile(P, (X > 86.6) & (X < 112.6) & (Y > 46.0) & (Y < 48.8), J3, 0.5)
    P.trait(104.0, 56.0, 104.0, 60.0, G1)                       # un panneau planté dans l'allée : « provisoire » en dessin
    P.poly([(98.0, 52.0), (110.0, 52.0), (110.0, 56.4), (98.0, 56.4)], J2)
    for k in range(5):
        P.poly([(98.0 + k * 2.6, 52.0), (99.2 + k * 2.6, 52.0), (98.0 + k * 2.6 + 0.4, 56.4), (98.0 + k * 2.6 - 0.8, 56.4)], ENCRE)
    for i in range(6):                                        # les traces de pas dans la poussière
        P.ell(96.0 + i * 3.4 + (i % 2) * 1.6, 64.0 + i * 2.4, 1.3 + i * 0.16, 0.5 + i * 0.05, G1)
    # Une lampe de chantier sur trépied : lumière provisoire, elle aussi.
    lx = 128.0
    for dx in (-3.0, 0.0, 3.0):
        P.trait(lx, 52.0, lx + dx, 64.0, G0)
    P.rect(lx - 3.0, 46.0, 6.0, 5.0, J1)
    P.rect(lx - 2.4, 46.6, 4.8, 3.8, J3 if int(p * 8) % 7 else J2)
    halo(P, lx, 48.0, 20.0, J3, 0.4)
    tab.plan("premier", 1.0)
    # ---- Premier plan : deux piles toutes proches, à contre-jour, un carton éventré d'où s'échappent des feuilles.
    for i, (x, w) in enumerate(((-2.0, 18.0), (192.0, 20.0))):
        tour_dossiers(P, x, w, -18.0, 82.0, 390 + i, sombre=0.0, teintes=(N0, N1, G0, V1, N1, G1))
    P.poly([(150.0, 72.0), (170.0, 71.0), (172.0, 80.0), (149.0, 80.0)], B2)
    P.poly([(150.0, 72.0), (170.0, 71.0), (166.0, 67.0), (147.0, 69.0)], B3)
    P.poly([(170.0, 71.0), (176.0, 69.0), (172.0, 80.0)], B1)
    for i in range(5):
        t = (p + i / 5.0) % 1.0
        x, y = 156.0 + 10 * hz(i, 1, 392) + 4 * math.sin(t * 6.283 + i), 68.0 - 26 * t
        if t < 0.9:
            P.poly([(x, y), (x + 3.0, y - 0.6), (x + 3.2, y + 1.4), (x + 0.2, y + 2.0)], BLANC if i % 2 else E5)
    voile(P, Y > 77.0, G0, 0.3)
    poussiere(P, 20, -10, 180, 74, 46, T.CIEL[11], 393)
    pg.lucioles(P, [(22.0, 40.0), (176.0, 30.0)], graine=394)
    # ---- Seconde passe : la vie du grenier.
    pg.araignee(P, 66.0, -16.0, 14.0, d=0.2)
    pg.toile_araignee(P, 22.0, 4.0, 9.0, sens=(1, 1), coul=T.CIEL[10])
    pg.souris(P, 82.0, 62.0, sens=1, coul=G3)
    pg.avion_papier(P, 40.0, 0.0, 150.0, 30.0, d=0.4)
    pg.papillon_de_nuit(P, 128.0, 46.0, 6.0, coul=BLANC, d=0.1)
    pg.goutte(P, 112.0, 9.6, 62.0, coul=T.CIEL[9], d=0.6, flaque=G4)
    bal = 0.7 * onde(p)                                         # une étiquette qui pend au bout de sa ficelle
    P.trait(160.0, 12.0, 160.0 + bal, 20.0, E5)
    P.rect(158.6 + bal, 20.0, 3.0, 2.0, BLANC)
    dos = 0.5 * onde(p, 0.3)                                    # le dossier du dessus d'une pile, qui va tomber (il hésite)
    P.poly([(26.0 + dos, 3.0), (38.0 + dos, 2.0 - dos), (38.6 + dos, 4.4 - dos), (26.4 + dos, 5.6)], O1)
    P.rect(28.0 + dos, 3.4, 3.0, 1.0, BLANC)
    pg.yeux(P, 186.0, 60.0, coul=J3, d=0.3)


# =====================================================================================================================
# La cabane de papier : l'intérieur d'une petite cabane faite de brouillons froissés et collés, éclairée par une lampe
# chaude, avec un hamac en ruban adhésif, une table basse, des cartes à jouer et une fenêtre en papier calque.
# =====================================================================================================================
@decor("grande-panne", "cabane-brouillon", soleil=(96.0, 6.0), tons=PANNE, nom="La cabane de papier", matiere=True)
def cabane_brouillon(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    lx, ly = 96.0, 6.0                                          # la lampe
    tab.plan("ciel", 0.0)
    # ---- Les murs : des feuilles froissées, collées en écailles, chacune avec ses lignes de texte abandonnées.
    d = np.hypot(X - lx, (Y - ly) * 1.2)
    P.rampe(np.ones(X.shape, dtype=bool), 1.0 - d / 130.0 + 0.2 * (pg.fbm(X / 9.0, Y / 7.0, 3, 400) - 0.5), [B1, B2, E2, E3, E4, E5], 0.7)
    for j in range(9):
        for i in range(13):
            x = -8 + i * 16.4 + (j % 2) * 8 + 3 * hz(i, j, 401)
            y = -18 + j * 11.4 + 3 * hz(i, j + 20, 401)
            a = (hz(i, j + 40, 401) - 0.5) * 0.5
            w, h = 13.0, 9.0
            pts = [(x, y), (x + w * math.cos(a), y + w * math.sin(a)), (x + w * math.cos(a) - h * math.sin(a), y + w * math.sin(a) + h * math.cos(a)),
                   (x - h * math.sin(a), y + h * math.cos(a))]
            m = P.masque_poly(pts)
            dd = math.hypot(x + 6 - lx, (y + 4 - ly) * 1.2)
            clair = max(0.0, 1.0 - dd / 120.0)
            voile(P, m, (E5, E4, BLANC)[(i + j) % 3], 0.25 + 0.5 * clair)
            P.remplir(P.crete(m), E5 if clair > 0.4 else E3)
            for k in range(3):
                xa, ya = x + 2.0 * math.cos(a) - (2.4 + k * 2.0) * math.sin(a), y + 2.0 * math.sin(a) + (2.4 + k * 2.0) * math.cos(a)
                l = 5 + 5 * hz(i * 7 + j, k, 402)
                P.trait(xa, ya, xa + l * math.cos(a), ya + l * math.sin(a), G3 if clair > 0.3 else E1)
            if hz(i, j + 60, 401) < 0.25:                       # une rature
                P.trait(x + 2, y + 3, x + 10, y + 6, O1)
    voile(P, d > 70, B1, np.clip((d - 70) / 90.0, 0, 0.6))
    tab.plan("lointains", 0.2)
    # ---- La fenêtre en papier calque : le dehors y passe en ombres bleues ; une croisée de ruban adhésif.
    wx, wy, ww, wh = 132.0, 14.0, 34.0, 28.0
    P.rect(wx - 2.0, wy - 2.0, ww + 4.0, wh + 4.0, B2)
    fen = (X > wx) & (X < wx + ww) & (Y > wy) & (Y < wy + wh)
    P.rampe(fen, 0.6 + 0.3 * (pg.fbm((X + 2 * onde(p)) / 10.0, Y / 8.0, 3, 403) - 0.5), [T.CIEL[5], T.CIEL[7], T.CIEL[9], BLANC], 0.8)
    for i in range(4):                                        # des ombres de piles de dossiers, dehors
        P.remplir(fen & (np.abs(X - (wx + 5 + i * 8.4)) < 2.0 + i % 2) & (Y > wy + 8 + (i * 5) % 9) & (P.T < 0.6), T.CIEL[6])
    P.rect(wx + ww / 2 - 0.9, wy, 1.8, wh, J2)
    P.rect(wx, wy + wh / 2 - 0.9, ww, 1.8, J2)
    voile(P, (X > wx - 30 + (Y - wy) * 0.2) & (X < wx + ww - 20 + (Y - wy) * 0.2) & (Y > wy + wh + 2) & (Y < 80), T.CIEL[9], 0.16)
    # Des dessins punaisés : un plan de l'ordinateur, un portrait de sablier, une guirlande de trombones.
    P.rect(22.0, 12.0, 20.0, 15.0, BLANC)
    for k in range(4):
        P.rect(24.0 + k * 4.4, 15.0 + (k % 2) * 4.0, 3.4, 3.0, (C2, O2, V4, J2)[k])
        if k < 3:
            P.trait(27.4 + k * 4.4, 16.6 + (k % 2) * 4.0, 28.4 + k * 4.4, 16.6 + ((k + 1) % 2) * 4.0, G2)
    P.point(32.0, 12.4, O2, 2)
    P.rect(48.0, 20.0, 10.0, 13.0, E5)
    P.poly([(50.0, 22.0), (56.0, 22.0), (53.0, 26.0)], C2)
    P.poly([(50.0, 30.0), (56.0, 30.0), (53.0, 26.0)], J2)
    P.point(53.0, 20.4, C2, 2)
    for i in range(14):
        x = 60 + i * 5.0
        y = -8.0 + 5.0 * math.sin(i / 13.0 * math.pi) + 0.3 * onde(p, 0.07 * i)
        P.ell(x, y, 1.6, 0.9, G4)
        P.ell(x, y, 0.9, 0.4, B2)
    tab.plan("moyen", 0.5)
    # ---- Le plancher : des cartons aplatis, un tapis de buvards ; puis les meubles.
    sol = Y > 62.0
    dallage(P, sol, 96.0, 46.0, K2, B3, larg=8.0, prof=0.7, joint=B2)
    voile(P, sol & (np.hypot(X - lx, (Y - 70) * 3.0) < 60), J3, 0.3)
    voile(P, sol & (np.hypot(X - lx, (Y - 70) * 3.0) > 80), B1, 0.5)
    P.ell(96.0, 73.0, 34.0, 4.6, V2)                            # le tapis
    P.ell(96.0, 73.0, 31.0, 3.8, V3)
    P.ell(96.0, 73.0, 22.0, 2.4, V2)
    for k in range(16):
        P.point(96.0 + 27.0 * math.cos(k * 0.3927), 73.0 + 3.2 * math.sin(k * 0.3927), J2)
    # Le hamac en ruban adhésif, tendu entre deux crayons plantés ; un coussin, une couverture qui pend.
    hx0, hx1, hy = 8.0, 62.0, 40.0
    for (x, c0) in ((hx0, J2), (hx1, O2)):
        P.rect(x - 1.2, 22.0, 2.4, 44.0, c0)
        P.rect(x + 0.4, 22.0, 0.8, 44.0, B3 if c0 == J2 else K1)
        P.poly([(x - 1.2, 22.0), (x + 1.2, 22.0), (x, 17.0)], E4)
        P.poly([(x - 0.5, 19.0), (x + 0.5, 19.0), (x, 17.0)], ENCRE)
    bal = 0.6 * onde(p)
    toile_pts = [(hx0, hy - 6), (hx0 + 14, hy + 4 + bal), (hx0 + 27, hy + 7 + bal), (hx0 + 40, hy + 4 + bal), (hx1, hy - 6)]
    P.courbe(toile_pts, J1, P.ep(3.2))
    P.courbe([(x, y - 0.8) for x, y in toile_pts], J3, P.ep(1.4))
    for i in range(9):
        t = i / 8.0
        x = hx0 + (hx1 - hx0) * t
        y = hy - 6 + 13.2 * math.sin(math.pi * t) + bal * math.sin(math.pi * t)
        P.trait(x, y - 1.6, x + 0.8, y + 1.6, J2)
    P.ell(hx0 + 14, hy + 0.6 + bal, 5.0, 2.4, C2)
    P.ell(hx0 + 13, hy + 0.0 + bal, 3.4, 1.4, C3)
    P.poly([(hx0 + 30, hy + 6 + bal), (hx0 + 44, hy + 2 + bal), (hx0 + 46, hy + 14 + bal), (hx0 + 36, hy + 17 + bal)], O2)
    P.poly([(hx0 + 32, hy + 7 + bal), (hx0 + 43, hy + 4 + bal), (hx0 + 44, hy + 9 + bal), (hx0 + 34, hy + 11 + bal)], O3)
    # La table basse (une gomme sur quatre punaises) : les cartes à jouer, deux tasses qui fument, un sablier.
    tx0, tx1, ty = 80.0, 122.0, 62.0
    P.poly([(tx0, ty), (tx1, ty), (tx1 + 3, ty + 4.4), (tx0 - 3, ty + 4.4)], O3)
    P.rect(tx0 - 3, ty + 4.4, tx1 - tx0 + 6, 3.0, O1)
    P.rect(tx0 - 3, ty + 4.4, tx1 - tx0 + 6, 0.6, T.CREME)
    for x in (tx0, tx1 - 2.4):
        P.rect(x, ty + 7.4, 1.0, 4.0, G3)
        P.ell(x + 0.5, ty + 7.6, 1.8, 0.7, J2)
    for i, (dx, dy, c0) in enumerate(((0, 0, BLANC), (4.0, 0.4, BLANC), (8.2, 0, BLANC), (12.4, 0.6, V4), (5.0, 2.2, BLANC), (15.0, 2.6, BLANC))):
        x, y = tx0 + 5 + dx, ty + 0.6 + dy
        P.poly([(x, y), (x + 3.4, y), (x + 3.8, y + 1.6), (x + 0.4, y + 1.6)], c0)
        if c0 == BLANC:
            P.point(x + 1.4, y + 0.6, (O2, N2)[i % 2])
    for (x, c0) in ((tx0 + 26, C2), (tx0 + 33, V4)):
        P.rect(x, ty - 2.6, 3.2, 3.4, c0)
        P.rect(x, ty - 2.6, 3.2, 0.6, BLANC)
        P.rect(x + 3.2, ty - 1.8, 1.0, 1.6, c0)
        for k in range(3):
            t = (p + k / 3.0 + x * 0.01) % 1.0
            voile(P, np.hypot(X - (x + 1.6 + 1.2 * math.sin(t * 6.0)), Y - (ty - 3.6 - 9 * t)) < 0.6 + 1.0 * t, BLANC, 0.6 - 0.5 * t)
    # ---- La lampe : une ampoule nue sous un abat-jour de papier plié ; c'est elle qui tient la pièce.
    P.trait(lx, -16.0, lx + 0.4 * onde(p), ly - 6.0, B1)
    halo(P, lx, ly + 2.0, 54.0, J3, 0.5, ry=40)
    halo(P, lx, ly + 2.0, 22.0, BLANC, 0.5)
    P.poly([(lx - 2.0, ly - 6.0), (lx + 2.0, ly - 6.0), (lx + 10.0, ly + 2.0), (lx - 10.0, ly + 2.0)], O3)
    for k in range(-4, 5):
        P.trait(lx + k * 0.5, ly - 6.0, lx + k * 2.4, ly + 2.0, O2 if k % 2 else J3)
    P.ell(lx, ly + 3.0, 2.2, 2.4, BLANC)
    P.ell(lx, ly + 3.0, 1.2, 1.4, J3 if int(p * 8) % 6 else BLANC)
    tab.plan("premier", 1.0)
    # ---- Premier plan : le bord de la porte (un rabat de carton), une pile de brouillons froissés en boule, une plante.
    P.poly([(-6.0, -16.0), (4.0, -16.0), (7.0, 80.0), (-6.0, 80.0)], B1)
    P.poly([(4.0, -16.0), (5.2, -16.0), (8.2, 80.0), (7.0, 80.0)], K2)
    for i, (x, y, r) in enumerate(((172.0, 76.0, 4.4), (180.0, 73.0, 3.6), (186.0, 77.0, 4.0), (176.0, 70.4, 2.8), (166.0, 78.2, 2.6))):
        P.volumes([(x, y, r), (x + r * 0.5, y - r * 0.3, r * 0.6), (x - r * 0.5, y + r * 0.2, r * 0.6)], [B2, E2, E3, E4, E5, BLANC],
                  (-0.6, -0.5, 0.4), grain=1.2, graine=410 + i, gain=0.6, base=0.5, trame=0.5)
    P.poly([(18.0, 72.0), (28.0, 72.0), (26.6, 80.0), (19.4, 80.0)], C1)
    P.rect(17.4, 71.0, 11.2, 1.6, C2)
    for i in range(6):
        a = -2.7 + i * 0.42 + 0.03 * onde(p, 0.1 * i)
        P.courbe([(23.0, 71.0), (23.0 + 6 * math.cos(a), 71.0 + 7 * math.sin(a)), (23.0 + 10 * math.cos(a), 71.0 + 9 * math.sin(a) + 3)],
                 T.S1 if i % 2 else T.S2, P.ep(0.8), 1)
    voile(P, Y > 77.4, B1, 0.3)
    poussiere(P, 50, -6, 150, 50, 26, J3, 415)
    # ---- Seconde passe : la vie de la cabane.
    pg.papillon_de_nuit(P, 96.0, 8.0, 9.0, coul=BLANC)
    pg.araignee(P, 170.0, -16.0, 10.0, d=0.3)
    for (x, y) in ((76.0, 30.0), (120.0, 52.0)):                 # le coin d'une feuille du mur qui se décolle et bat
        b = 1.0 * onde(p, x * 0.01)
        P.poly([(x, y), (x + 5.0, y), (x + 5.0 + b, y + 3.0 + b)], E5)
        P.poly([(x + 5.0, y), (x + 5.0 + b, y + 3.0 + b), (x + 3.4, y + 2.0)], E3)
    t = (p + 0.5) % 1.0                                         # une carte glisse de la table
    P.poly([(118.0 + 3 * t, 62.0 + 9 * t * t), (121.4 + 3 * t, 62.0 + 9 * t * t), (121.8 + 3 * t, 63.6 + 9 * t * t), (118.4 + 3 * t, 63.6 + 9 * t * t)], BLANC)
    pg.souris(P, 150.0, 77.4, sens=-1, coul=G3)
    P.rect(66.0, 70.0, 5.0, 6.0, K2)                             # un réveil sur une boîte : son aiguille tique
    P.ell(68.5, 67.0, 2.6, 2.6, J2)
    P.ell(68.5, 67.0, 1.9, 1.9, BLANC)
    P.trait(68.5, 67.0, 68.5 + 1.4 * math.sin(int(p * 8) * 0.785), 67.0 - 1.4 * math.cos(int(p * 8) * 0.785), ENCRE)


# =====================================================================================================================
# L'Horloge système : une vaste salle ronde et silencieuse aux murs de roues dentées immobiles ; au centre, un grand
# balancier doré arrêté, penché d'un côté (la clé) ; un levier à son pied ; une trappe ronde au fond ; une lumière
# bleutée qui tombe d'en haut.
# =====================================================================================================================


@decor("grande-panne", "horloge-systeme", soleil=(104.0, -40.0), tons=PANNE, nom="L'Horloge système", matiere=True)
def horloge_systeme(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    # ---- La salle ronde : un mur courbe bleu nuit, plus clair là où tombe la lumière d'en haut.
    P.rampe(np.ones(X.shape, dtype=bool), 0.62 - np.abs(X - 104) / 150.0 - 0.004 * (Y + 16) + 0.16 * (pg.fbm(X / 16.0, Y / 12.0, 3, 420) - 0.5),
            [ENCRE, N0, N1, N2, N3], 0.8)
    tab.plan("lointains", 0.2)
    # ---- Les roues dentées du mur, immobiles : de toutes tailles, cuivre, laiton, acier bleui, engrenées les unes dans
    # les autres. Une seule, toute petite, tressaille encore.
    roues = ((22, 4, 20, 22, 0), (52, 30, 12, 14, 1), (30, 46, 14, 16, 2), (66, -6, 13, 15, 2), (150, 0, 22, 24, 1), (178, 34, 15, 17, 0),
             (142, 40, 11, 13, 2), (6, 32, 9, 11, 1), (188, -4, 9, 11, 2), (76, 20, 7, 9, 0), (132, 18, 7, 9, 0), (166, 54, 8, 10, 1),
             (48, 56, 8, 10, 0))
    tons3 = ((K1, K2, N0), (J1, J2, N0), (N2, N3, N0))
    for i, (x, y, r, dents, t) in enumerate(roues):
        a = 0.06 * math.sin(p * 4 * math.pi) if i == 9 else 0.3 * i
        roue(P, x, y, r, dents, tons3[t][0], tons3[t][1], tons3[t][2], angle=a)
    voile(P, np.abs(X - 104) > 44, N0, np.clip((np.abs(X - 104) - 44) / 110.0, 0, 0.45))
    # La trappe ronde, au fond : un hublot de laiton entrouvert, une lueur orange dessous.
    tx, ty = 160.0, 60.0
    halo(P, tx, ty, 12.0, O2, 0.4)
    P.ell(tx, ty, 7.0, 3.4, J1)
    P.ell(tx, ty, 5.8, 2.6, ENCRE)
    P.ell(tx, ty + 0.6, 4.6, 1.6, O1 if int(p * 8) % 5 else O2)
    P.poly([(tx - 6.0, ty - 1.0), (tx + 6.0, ty - 1.0), (tx + 5.0, ty - 8.0), (tx - 5.0, ty - 8.0)], J1)
    P.poly([(tx - 5.0, ty - 1.6), (tx + 5.0, ty - 1.6), (tx + 4.2, ty - 7.4), (tx - 4.2, ty - 7.4)], J2)
    P.ell(tx, ty - 4.6, 1.6, 1.6, J1)
    for k in range(8):
        P.point(tx + 5.8 * math.cos(k * 0.785), ty + 2.6 * math.sin(k * 0.785), J3)
    tab.plan("moyen", 0.5)
    # ---- La lumière bleutée qui tombe d'en haut, sur le balancier.
    rai(P, 104.0, -16.0, 78.0, 36.0, 0.0, T.CIEL[5], 0.2, 44, 421)
    rai(P, 104.0, -16.0, 78.0, 12.0, 0.0, T.CIEL[8], 0.16, 0, 422)
    # ---- Le sol : un cadran géant, ses chiffres en bâtons, vu en perspective ; il est à 13 h 37.
    sol = Y > 62.0
    P.rampe(sol, 0.5 - 0.02 * (Y - 62) + 0.15 * (pg.fbm(X / 8.0, Y / 2.0, 3, 423) - 0.5), [N0, N1, N2, G2], 0.8)
    for rr, c0 in ((92.0, G2), (78.0, N3), (40.0, N3)):
        dd = np.hypot(X - 104, (Y - 76) * 4.2)
        P.remplir(sol & (np.abs(dd - rr) < 0.9), c0)
    for k in range(24):
        a = k * math.pi / 12
        x0, y0 = 104 + 80 * math.cos(a), 76 + 80 / 4.2 * math.sin(a)
        x1, y1 = 104 + (88 if k % 2 else 91) * math.cos(a), 76 + (88 if k % 2 else 91) / 4.2 * math.sin(a)
        if y0 > 62:
            P.trait(x0, y0, x1, y1, J2 if k % 2 == 0 else G3, P.ep(0.6 if k % 2 == 0 else 0.3))
    voile(P, sol & (np.hypot(X - 104, (Y - 74) * 3.4) < 30), T.CIEL[6], 0.3)
    # ---- Le grand balancier doré : arrêté, penché d'un côté. Sa tige descend du plafond, sa lentille luit.
    px_, py_ = 104.0, -18.0
    ang = 0.2 + 0.006 * math.sin(p * 2 * math.pi)                # il frémit à peine
    L = 80.0
    bx, by = px_ + L * math.sin(ang), py_ + L * math.cos(ang)
    P.trait(px_, py_, bx, by, J1, P.ep(1.6))
    P.trait(px_ - 0.4, py_, bx - 0.4, by, J3, 1)
    for t in (0.3, 0.5, 0.7):                                   # les bagues de la tige
        P.rect(px_ + L * t * math.sin(ang) - 1.4, py_ + L * t * math.cos(ang) - 0.6, 2.8, 1.2, J2)
    halo(P, bx, by, 22.0, J2, 0.4)
    P.ell(bx, by, 11.0, 11.0, J1)
    P.ell(bx, by, 10.0, 10.0, J2)
    dd = np.hypot(X - bx + 3.0, Y - by + 3.0)
    P.remplir((np.hypot(X - bx, Y - by) < 10.0) & (dd < 7.0) & (P.T < 0.7), J3)
    P.remplir((np.hypot(X - bx, Y - by) < 10.0) & (dd < 3.4), BLANC)
    P.remplir((np.hypot(X - bx, Y - by) < 10.0) & (np.hypot(X - bx - 3.5, Y - by - 3.5) < 5.0) & (P.T < 0.5), K2)
    P.ell(bx, by, 3.0, 3.0, J1)
    P.ell(bx, by, 1.4, 1.4, K1)
    P.ell(bx + 2.0, 76.6, 13.0, 1.6, ENCRE)                     # son ombre sur le cadran
    voile(P, np.hypot(X - bx - 2.0, (Y - 76.6) * 6.0) < 16, N0, 0.6)
    # Le levier, à son pied : socle de fonte, manche de laiton, pommeau orange ; un voyant qui attend.
    lx, ly = 84.0, 78.0
    P.poly([(lx - 6.0, ly), (lx + 6.0, ly), (lx + 4.4, ly - 4.0), (lx - 4.4, ly - 4.0)], G1)
    P.rect(lx - 4.4, ly - 4.0, 8.8, 0.8, G3)
    P.rect(lx - 2.0, ly - 3.2, 4.0, 1.6, ENCRE)
    P.trait(lx, ly - 3.0, lx - 6.0, ly - 15.0, J1, P.ep(1.0))
    P.trait(lx - 0.4, ly - 3.0, lx - 6.4, ly - 15.0, J3, 1)
    P.ell(lx - 6.4, ly - 16.0, 2.0, 2.0, O1)
    P.ell(lx - 6.8, ly - 16.4, 1.2, 1.2, O2)
    P.point(lx - 7.2, ly - 16.9, O3)
    voyant(P, lx + 3.0, ly - 1.8, O2, K1, part=0.5, r=0.6)
    tab.plan("premier", 1.0)
    # ---- Premier plan : deux grandes roues à contre-jour dans les coins du bas, une chaîne qui pend, des contrepoids.
    roue(P, -4.0, 86.0, 26.0, 20, ENCRE, N1, N0, angle=0.2, moyeu=N2)
    roue(P, 198.0, 90.0, 30.0, 24, ENCRE, N1, N0, angle=0.5, moyeu=N2)
    for (x, l, d) in ((14.0, 46.0, 0.0), (20.0, 30.0, 0.3), (182.0, 40.0, 0.6)):
        bal = 0.5 * onde(p, d)
        for j in range(int(l / 2.0)):
            P.ell(x + bal * j / (l / 2.0), -16.0 + j * 2.0, 0.7, 1.1, G2 if j % 2 else G1)
        P.poly([(x + bal - 2.2, -16.0 + l), (x + bal + 2.2, -16.0 + l), (x + bal + 1.6, -16.0 + l + 7.0), (x + bal - 1.6, -16.0 + l + 7.0)], J1)
        P.rect(x + bal - 2.2, -16.0 + l, 4.4, 0.8, J2)
    poussiere(P, 86, -14, 122, 70, 20, T.CIEL[11], 424)
    pg.lucioles(P, [(40.0, 66.0), (150.0, 70.0), (126.0, 50.0)], graine=425)
    # ---- Seconde passe : ce qui bouge encore dans une horloge arrêtée.
    pg.goutte(P, 150.0, 22.0, 70.0, coul=J2, d=0.2, flaque=J1)   # une goutte d'huile tombe d'une roue
    pg.vapeur(P, 160.0, 54.0, coul=O3, h=9.0, d=0.4)             # la trappe respire
    pg.papillon_de_nuit(P, 104.0, 0.0, 10.0, coul=T.CIEL[11])
    pg.etincelle(P, 76.0, 20.0, coul=J3, d=0.5)                  # deux dents qui frottent
    a = 0.1 * math.sin(p * 4 * math.pi)                         # la trotteuse du cadran essaie d'avancer, et revient
    P.trait(104.0, 76.0, 104.0 + 30 * math.cos(-0.4 + a), 76.0 + 30 / 4.2 * math.sin(-0.4 + a), O2)
    pg.araignee(P, 62.0, -16.0, 12.0, d=0.7)
    pg.souris(P, 128.0, 77.6, sens=1, coul=G3)
    pg.yeux(P, 186.0, 66.0, coul=J3, d=0.1)
