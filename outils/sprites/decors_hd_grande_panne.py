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
from paysage import Tons, cs, hz, onde, voile, halo, dallage, rai, poussiere, roue

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
@decor("grande-panne", "bureau-1337", soleil=(40.0, 6.0), tons=PANNE, nom="Le bureau, 13 h 37")
def bureau_1337(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    # ---- Le fond d'écran : une aube froide, des collines floues comme une photo de fond d'écran.
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=52.0, haut=0.28, halo=0.3, disque=0)
    tab.plan("nuages", 0.08)
    pg.cumulus(P, [(52, 4, 44, 7.0, 201, 8, 0.0), (150, 14, 36, 5.5, 203, 7, 0.4), (104, -6, 28, 4.5, 205, 6, 0.7)], dessous=-0.5)
    tab.plan("lointains", 0.2)
    for i, (base, amp, ech, rampe) in enumerate(((44, 12, 40, [T.L3, T.L4, T.L5, T.CIEL[8]]), (50, 9, 26, [T.L2, T.L3, T.L4, T.L5]),
                                                 (56, 6, 17, [N2, N3, T.L3, T.L4]))):
        pg.crete(P, lambda x, b=base, a=amp, e=ech, g=210 + i: pg.profil(x, b, a, e, g), rampe, 0.6)
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
    voile(P, (X > fx + 2) & (X < fx + fw + 2) & (Y > fy + 2) & (Y < fy + fh + 2), N1, 0.5)
    P.rect(fx, fy, fw, fh, E5)
    P.rect(fx, fy, fw, 5.0, N2)
    P.rampe((X > fx) & (X < fx + fw) & (Y > fy) & (Y < fy + 5.0), 0.2 + 0.7 * (X - fx) / fw, [N2, N3, T.CIEL[4]], 0.6)
    for i, c0 in enumerate((O2, J2, G4)):
        P.rect(fx + fw - 5.0 - i * 4.4, fy + 1.2, 3.0, 2.6, c0)
    P.rect(fx + 2, fy + 1.8, 22, 0.6, BLANC)
    voile(P, (X > fx) & (X < fx + fw) & (Y > fy + 5) & (Y < fy + fh), BLANC, 0.5)       # elle blanchit : elle est figée
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
    voile(P, barre & (Y > 72), T.ENCRE, 0.35)
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


# =====================================================================================================================
# Le Hall des Pas Comptés : un hall de gare immense, des guichets aux rideaux baissés (« Retour à 13 h 38 »), une file
# en serpentin, l'afficheur « 1 337 » (la clé), un banc de bois au premier plan.
# =====================================================================================================================
@decor("grande-panne", "hall-pas-comptes", soleil=(96.0, -10.0), tons=PANNE, nom="Le Hall des Pas Comptés")
def hall(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    fx, fy = 96.0, 44.0                                       # le point de fuite
    tab.plan("ciel", 0.0)
    # ---- La verrière : une voûte de verre laiteux à nervures, le jour blanc qui tombe.
    r = np.hypot(X - fx, (Y - fy) * 1.25)
    P.rampe(np.ones(X.shape, dtype=bool), 0.95 - r / 150.0 + 0.1 * (pg.fbm(X / 20.0, Y / 9.0, 2, 230) - 0.5),
            [E2, E3, E4, E5, BLANC], 0.7)
    ang = np.arctan2(Y - fy, X - fx)
    P.remplir((np.abs(((ang * 14 / math.pi) % 1.0) - 0.5) > 0.44) & (Y < fy) & (r > 16), E2)     # les nervures
    for rr in (30, 52, 78, 108):
        P.remplir((np.abs(r - rr) < 0.5 + rr / 160.0) & (Y < fy), E2)
    P.remplir((np.abs(((ang * 14 / math.pi) % 1.0) - 0.5) < 0.2) & (Y < fy) & (r > 30) & (r < 52) & (P.T < 0.4), T.CIEL[8])
    tab.plan("lointains", 0.2)
    # ---- Le mur du fond : la grande horloge de gare (arrêtée), une arcade, des guichets minuscules.
    fond = (np.abs(X - fx) < 40) & (Y > 24) & (Y < 52)
    P.rampe(fond, 0.5 + 0.02 * (Y - 24), [E2, E3, E4], 0.5)
    for i in range(7):
        ax = fx - 33 + i * 11
        P.ell(ax, 40.0, 3.6, 5.0, E1, cond=Y < 40.5)
        P.rect(ax - 3.6, 40.0, 7.2, 9.0, E1)
        P.rect(ax - 2.8, 41.0, 5.6, 6.0, G2)
        for j in range(4):
            P.rect(ax - 2.8, 41.6 + j * 1.5, 5.6, 0.4, G1)
        P.rect(ax - 1.6, 43.0, 3.2, 2.0, BLANC)
        P.rect(ax - 1.0, 43.8, 2.0, 0.5, O2)
    P.ell(fx, 31.0, 5.0, 5.0, B2)
    P.ell(fx, 31.0, 4.2, 4.2, E5)
    for k in range(12):
        P.point(fx + 3.5 * math.cos(k * math.pi / 6), 31.0 + 3.5 * math.sin(k * math.pi / 6), G1)
    P.trait(fx, 31.0, fx + 1.4, 29.4, ENCRE)                    # 13 h 37
    P.trait(fx, 31.0, fx + 0.9 + 0.2 * (int(p * 8) % 2), 34.0, ENCRE)      # la grande aiguille frémit, sans avancer
    tab.plan("moyen", 0.5)
    # ---- Les deux murs latéraux, en fuite : une rangée de guichets, rideau de fer baissé, néon jaune, petit panneau.
    for cote in (-1, 1):
        mur = ((X - fx) * cote > 40 + (0)) & (Y < fy + ((X - fx) * cote - 40) * 0.62) & (Y > fy - ((X - fx) * cote - 40) * 0.9)
        P.rampe(mur, 0.42 + 0.004 * (X - fx) * cote + 0.2 * (pg.fbm(X / 12.0, Y / 8.0, 2, 231) - 0.5), [E1, E2, E3, E4], 0.6)
        for i in range(5):
            d0, d1 = 42 + i * 13 + i * i * 1.4, 42 + (i + 1) * 13 + (i + 1) ** 2 * 1.4 - 3
            xa, xb = fx + cote * d0, fx + cote * d1
            k0, k1 = (d0 - 40) / 60.0, (d1 - 40) / 60.0
            haut = lambda k: fy - 4 - 22 * k
            bas = lambda k: fy + 2 + 36 * k
            # pilier, linteau, guichet
            P.poly([(xa, haut(k0)), (xb, haut(k1)), (xb, bas(k1)), (xa, bas(k0))], G2)
            P.poly([(xa, haut(k0) + 3 + 5 * k0), (xb, haut(k1) + 3 + 5 * k1), (xb, bas(k1) - 8 - 14 * k1),
                    (xa, bas(k0) - 8 - 14 * k0)], G1)
            n = 9
            for j in range(n):                                # les lames du rideau de fer
                u = (j + 0.5) / n
                ya = haut(k0) + 3 + 5 * k0 + (bas(k0) - 8 - 14 * k0 - haut(k0) - 3 - 5 * k0) * u
                yb = haut(k1) + 3 + 5 * k1 + (bas(k1) - 8 - 14 * k1 - haut(k1) - 3 - 5 * k1) * u
                P.trait(xa, ya, xb, yb, G3 if j % 2 else G0)
            mxp, kp = (xa + xb) / 2, (k0 + k1) / 2            # le panneau « Retour à 13 h 38 », dessiné : une horloge, une flèche
            ph = 3.0 + 5.0 * kp
            P.rect(mxp - ph, fy + 2 * kp, ph * 2, ph * 1.2, BLANC)
            P.ell(mxp - ph * 0.45, fy + 2 * kp + ph * 0.6, ph * 0.36, ph * 0.36, O2)
            P.rect(mxp, fy + 2 * kp + ph * 0.5, ph * 0.7, max(0.4, ph * 0.14), ENCRE)
            P.poly([(xa, bas(k0) - 8 - 14 * k0), (xb, bas(k1) - 8 - 14 * k1), (xb, bas(k1) - 5 - 10 * k1), (xa, bas(k0) - 5 - 10 * k0)], B2)
            P.trait(xa, bas(k0) - 8 - 14 * k0, xb, bas(k1) - 8 - 14 * k1, B3)
            if (p + 0.17 * i + (0.4 if cote > 0 else 0)) % 1.0 > 0.12:                     # le néon du guichet
                P.trait(xa + cote * 1, haut(k0) + 1.2 + 2 * k0, xb - cote * 1, haut(k1) + 1.2 + 2 * k1, J3, P.ep(0.5))
                halo(P, mxp, haut(kp) + 4 + 4 * kp, 6 + 8 * kp, J2, 0.3)
    # ---- Le sol : un dallage beige et gris qui fuit, ciré, où tombe la lumière de la verrière.
    sol = (Y > fy + np.maximum(np.abs(X - fx) - 40, 0) * 0.62) & (Y > fy + 6)
    dallage(P, sol, fx, fy, E4, E3, larg=6.0, prof=1.5, joint=E2)
    voile(P, sol, G3, np.clip((np.abs(X - fx) - 30) / 110.0, 0, 0.5))
    voile(P, sol & (np.abs(X - fx) < (Y - fy) * 0.55), BLANC, 0.22)
    # La file en serpentin : poteaux dorés et cordons orange, des feuilles qui attendent debout.
    for rang, yq in enumerate((57.0, 61.5, 67.0)):
        k = 0.5 + 0.25 * rang
        x0, x1 = fx - 34 * (0.7 + 0.3 * rang), fx + 34 * (0.7 + 0.3 * rang)
        nb = 6 + rang
        for i in range(nb + 1):
            x = x0 + (x1 - x0) * i / nb
            if i < nb:
                P.courbe([(x, yq - 4.4 * k), (x + (x1 - x0) / nb / 2, yq - 3.2 * k), (x + (x1 - x0) / nb, yq - 4.4 * k)], O2, 1)
            P.rect(x - 0.4 * k, yq - 5.0 * k, 0.9 * k, 5.0 * k, J1)
            P.ell(x, yq - 5.2 * k, 0.8 * k, 0.8 * k, J2)
            P.ell(x, yq, 1.2 * k, 0.4 * k, G1)
        for i in range(nb * 2):                              # ceux qui attendent : de petites feuilles debout
            x = x0 + 3 + (x1 - x0 - 6) * i / (nb * 2 - 1)
            if 128 < x < 170 and rang == 2 or 26 < x < 66 and rang == 2:
                continue
            hgt = (3.6 + 1.0 * hz(i, rang, 232)) * k
            dy = 0.25 * k * (1 if int(p * 8 + i) % 5 == 0 else 0)
            P.rect(x - 0.8 * k, yq - hgt - dy, 1.7 * k, hgt, (BLANC, E5, C3, E5)[(i + rang) % 4])
            P.point(x - 0.3 * k, yq - hgt * 0.72 - dy, ENCRE)
            P.point(x + 0.4 * k, yq - hgt * 0.72 - dy, ENCRE)
    # ---- L'afficheur « 1 337 » : suspendu sous la verrière, orange, c'est lui qu'on regarde.
    ax, ay, aw, ah = 66.0, 6.0, 60.0, 24.0
    for dx in (8.0, 52.0):
        P.rect(ax + dx, -17.0, 1.0, 23.5, G1)
    P.rect(ax - 1.5, ay - 1.5, aw + 3, ah + 3, G1)
    P.rect(ax - 1.5, ay - 1.5, aw + 3, 0.6, G3)
    P.rect(ax, ay, aw, ah, ENCRE)
    trame_led = ((P.XI % 2 == 0) & (P.YI % 2 == 0))
    P.remplir((X > ax) & (X < ax + aw) & (Y > ay) & (Y < ay + ah) & trame_led, B1)
    halo(P, ax + aw / 2, ay + ah / 2, 44, O1, 0.4, ry=20)
    sept(P, ax + 5.5, ay + 4.5, "1337", K1, l=9.0, h=15.0, ep=P.ep(2.0), pas=13.4)
    sept(P, ax + 5.5, ay + 4.5, "1337", O2, l=9.0, h=15.0, ep=P.ep(1.4), pas=13.4)
    if int(p * 8) % 4:
        sept(P, ax + 5.5, ay + 4.5, "1337", O3, l=9.0, h=15.0, ep=P.ep(0.5), pas=13.4)
    for i in range(6):                                       # des voyants courent sous les chiffres
        voyant(P, ax + 6 + i * 9.6, ay + ah - 2.0, J3, B1, d=i / 6.0, part=0.3, r=0.6)
    rai(P, 60.0, -16.0, 78.0, 16.0, -0.34, BLANC, 0.3, 22, 233)
    rai(P, 138.0, -16.0, 78.0, 13.0, 0.3, BLANC, 0.26, 18, 234)
    # ---- Premier plan : le banc de bois (au milieu, bas), le distributeur de tickets, deux pigeons de gare.
    tab.plan("premier", 1.0)
    bx0, bx1, by = 74.0, 120.0, 72.0
    voile(P, (X > bx0 - 2) & (X < bx1 + 2) & (Y > 77.5) & (Y < 79.6), G1, 0.6)
    for x in (bx0 + 3, bx1 - 5):
        P.rect(x, by, 2.4, 7.0, B1)
        P.rect(x, by, 0.8, 7.0, B2)
    P.rect(bx0, by - 1.8, bx1 - bx0, 2.6, B2)
    P.rect(bx0, by - 1.8, bx1 - bx0, 0.8, B3)
    P.rect(bx0, by + 0.6, bx1 - bx0, 0.4, B1)
    for x in np.arange(bx0 + 6, bx1, 7.5):
        P.trait(x, by - 1.0, x + 2.0, by - 1.0, B1)
    P.rect(bx0 + 3, by - 8.0, bx1 - bx0 - 6, 1.6, B2)           # le dossier du banc
    P.rect(bx0 + 3, by - 8.0, bx1 - bx0 - 6, 0.5, B3)
    P.rect(bx0 + 3, by - 5.2, bx1 - bx0 - 6, 1.4, B2)
    P.rect(bx0 + 4, by - 8.0, 1.2, 6.4, B1)
    P.rect(bx1 - 5.2, by - 8.0, 1.2, 6.4, B1)
    papiers(P, 100.0, by - 1.8, 7.0, 3, 235)                    # un journal oublié
    dx_ = 176.0                                               # le distributeur de tickets
    P.rect(dx_, 50.0, 13.0, 28.0, G2)
    P.rect(dx_, 50.0, 2.0, 28.0, G3)
    P.rect(dx_ + 11.6, 50.0, 1.4, 28.0, G1)
    P.rect(dx_ + 2.6, 52.6, 7.8, 5.0, ENCRE)
    sept(P, dx_ + 3.2, 53.4, "1338", O2, l=1.2, h=3.2, ep=1, pas=1.9)
    P.ell(dx_ + 6.5, 63.0, 2.6, 2.6, O1)
    P.ell(dx_ + 6.2, 62.6, 1.8, 1.8, O2)
    P.rect(dx_ + 3.0, 68.0, 7.0, 1.0, ENCRE)
    P.rect(dx_ + 4.4, 68.4, 4.0, 2.2 + 0.6 * onde(p), BLANC)
    tickets(P, dx_ + 5.0, 70.0, 79.5, 3, 236)
    for i, (x, sens) in enumerate(((16.0, 1), (22.5, -1))):                               # les pigeons
        picore = int(p * 8 + i * 3) % 4 == 0
        P.ell(x, 76.6, 2.4, 1.5, G3)
        P.ell(x - sens * 0.8, 76.9, 1.5, 0.9, G4)
        P.poly([(x - sens * 2.0, 76.4), (x - sens * 4.0, 75.6), (x - sens * 2.2, 77.6)], G2)
        hx_, hy_ = x + sens * 2.1, 76.8 if picore else 74.8
        P.ell(hx_, hy_, 1.0, 1.0, V3)
        P.point(hx_ + sens * 0.3, hy_ - 0.3, ENCRE)
        P.rect(min(hx_ + sens * 0.9, hx_ + sens * 1.8), hy_ + 0.1, 0.9, 0.5, O2)
        P.trait(x, 78.0, x, 79.0, O1)
    poussiere(P, 30, 0, 160, 60, 24, BLANC, 237)


# =====================================================================================================================
# Le pied de la Tour du tampon : une tour de pierre grise qui se perd dans la brume (la clé), la file enroulée trois
# fois autour de sa base, une porte basse gardée par un tabouret trop petit, la lumière jaune des néons.
# =====================================================================================================================
@decor("grande-panne", "tour-tampon", soleil=(96.0, -30.0), tons=PANNE, nom="Le pied de la Tour du tampon")
def tour_tampon(P, tab):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    tab.plan("ciel", 0.0)
    pg.ciel(P, horizon=74.0, haut=0.14, halo=0.0, disque=0)
    brume = lambda y0, ep, g, f=0.55: voile(P, np.abs(Y - y0 - 3 * np.sin(X / 23.0 + g)) < ep * (0.6 + 0.8 * pg.fbm(
        (X + 2.0 * onde(p, g * 0.1)) / 26.0, Y / 5.0, 3, 240 + g)), T.CIEL[7], f * 0.8)
    tab.plan("lointains", 0.2)
    # ---- Au loin, d'autres tours dans la brume, des passerelles, des lucarnes allumées.
    for i, (x, w, top) in enumerate(((14, 14, 8), (40, 9, 22), (148, 11, 14), (174, 16, 0), (126, 7, 30), (62, 6, 34))):
        m = (np.abs(X - x) < w / 2 * (1 + (Y - top) / 300.0)) & (Y > top)
        P.rampe(m, 0.3 + 0.012 * (Y - top) + 0.2 * (X - x) / w, [T.CIEL[2], T.CIEL[3], T.CIEL[4], T.CIEL[5]], 0.6)
        P.rect(x - w / 2 - 1, top, w + 2, 1.4, T.CIEL[2])
        for j in range(6):
            if hz(i, j, 241) < 0.6:
                vif = (p + hz(i, j, 242)) % 1.0 < 0.8
                P.rect(x - w * 0.25 + (j % 2) * w * 0.3, top + 6 + j * 7, 1.4, 2.2, J3 if vif else T.CIEL[1])
    P.rect(40, 40, 88, 1.0, T.CIEL[2])                         # une passerelle
    for x in range(42, 128, 6):
        P.rect(x, 41, 0.5, 3.0, T.CIEL[3])
    brume(30.0, 6.0, 1)
    brume(54.0, 7.0, 2, 0.6)
    tab.plan("moyen", 0.5)
    # ---- La tour : pierre grise, cerclée de corniches, elle se perd dans la brume du haut ; des tampons géants y sont
    # frappés, des fenêtres de bureau s'allument.
    cx = 96.0
    demi = lambda y: 25.0 + (_a(y) - 30) * 0.05
    tour = np.abs(X - cx) < demi(Y)
    u = (X - cx) / demi(Y)
    v = 0.58 - 0.34 * u + 0.16 * (pg.fbm(X / 3.0, Y / 2.0, 3, 243) - 0.5) - 0.1 * u * u
    P.rampe(tour, v, [G0, G1, G2, G3, G4], 0.7)
    assise = np.floor((Y + 16) / 3.0)                           # les assises de pierre, joints décalés
    P.remplir(tour & (((Y + 16) % 3.0) < 0.4), G1)
    P.remplir(tour & ((((X - cx) / demi(Y) * 7 + assise * 0.5) % 1.0) < 0.06) & (((Y + 16) % 3.0) > 0.4), G1)
    for yc in (0.0, 30.0, 54.0):                               # corniches
        P.remplir((np.abs(X - cx) < demi(Y) + 1.6) & (np.abs(Y - yc) < 1.1), G3)
        P.remplir((np.abs(X - cx) < demi(Y) + 1.6) & (np.abs(Y - yc - 1.1) < 0.4), G0)
    for i, (dx, y, a, c0) in enumerate(((-11, 12, -0.3, V4), (10, 22, 0.25, O2), (-8, 42, 0.15, C2), (13, 47, -0.2, V4))):
        d = np.hypot(X - cx - dx, Y - y)                        # les tampons : un cercle, une étoile ou des barres au milieu
        voile(P, tour & (np.abs(d - 4.6) < 0.5), c0, 0.8)
        voile(P, tour & (np.abs(d - 3.6) < 0.25), c0, 0.6)
        voile(P, tour & (np.abs((X - cx - dx) * math.cos(a) + (Y - y) * math.sin(a)) < 2.6) & (np.abs(
            -(X - cx - dx) * math.sin(a) + (Y - y) * math.cos(a)) < 0.5), c0, 0.8)
    for j, y in enumerate((-8.0, 6.0, 18.0, 36.0)):
        for i in (-1, 0, 1):
            if (i + j) % 2 == 0:
                vif = (p + hz(i + 2, j, 244)) % 1.0 < 0.85
                P.rect(cx + i * 9.0 - 1.4, y, 2.8, 4.4, G0)
                P.rect(cx + i * 9.0 - 1.0, y + 0.4, 2.0, 3.6, J3 if vif else J1)
                P.rect(cx + i * 9.0 - 1.0, y + 2.0, 2.0, 0.4, G0)
    voile(P, tour & (Y < 8), T.CIEL[6], np.clip((8 - Y) / 26.0, 0, 0.95))                   # elle se perd dans la brume
    # La porte basse et son néon jaune ; le tabouret trop petit qui la garde.
    P.ell(cx, 67.0, 6.0, 6.0, G0, cond=Y < 67.5)
    P.rect(cx - 6.0, 67.0, 12.0, 9.0, G0)
    P.ell(cx, 67.5, 4.8, 4.8, B1, cond=Y < 68)
    P.rect(cx - 4.8, 67.5, 9.6, 8.5, B1)
    for i in range(-2, 3):
        P.rect(cx + i * 1.9 - 0.2, 64.0 if abs(i) < 2 else 66.0, 0.4, 12.0, B2)
    P.ell(cx + 3.0, 71.0, 0.6, 0.6, J2)
    neon(P, cx - 8.0, cx + 8.0, 58.6, J2, J3, vacille=0.12, lueur=10.0)
    halo(P, cx, 66.0, 34.0, J2, 0.5, ry=16)
    voile(P, (np.abs(X - cx) < 26 - (78 - Y) * 0.8) & (Y > 60) & (Y < 80), J3, 0.3)
    brume(6.0, 6.0, 3, 0.6)
    brume(-9.0, 8.0, 4, 0.8)
    # ---- Le parvis : pavés gris, la file enroulée trois fois autour de la base (poteaux, cordons, ceux qui attendent).
    sol = (Y > 68.0) & ~(tour & (Y < 75.0))
    dallage(P, sol, cx, 58.0, G3, G2, larg=7.0, prof=1.6, joint=G1)
    voile(P, sol & (np.hypot(X - cx, (Y - 76) * 3) < 46), J2, 0.3)
    voile(P, sol & (np.abs(X - cx) > 60), G1, 0.4)
    for tour_n, (rx, ry, yc) in enumerate(((34.0, 3.4, 71.0), (52.0, 4.6, 72.0), (74.0, 5.4, 73.4))):
        nb = 14 + tour_n * 6
        k = 0.7 + 0.2 * tour_n
        for i in range(nb):
            a = math.pi * (1.0 + i / (nb - 1.0))                # la moitié de l'ellipse qui passe devant la tour
            x, y = cx + rx * math.cos(a), yc - ry * math.sin(a)
            a2 = math.pi * (1.0 + (i + 1) / (nb - 1.0))
            if i < nb - 1:
                P.trait(x, y - 4.0 * k, cx + rx * math.cos(a2), yc - ry * math.sin(a2) - 4.0 * k, O2)
            if (34 < x < 72 or 122 < x < 162) and tour_n > 0:
                continue                                      # la place de Pilou et de son interlocuteur
            P.rect(x - 0.3, y - 4.6 * k, 0.7, 4.6 * k, J1)
            P.point(x - 0.3, y - 4.8 * k, J3)
            if i % 2 == 0 and tour_n < 2:
                hgt = (3.0 + hz(i, tour_n, 245)) * k
                dy = 0.3 if int(p * 8 + i) % 6 == 0 else 0.0
                P.rect(x + 1.2, y - hgt - dy, 1.6 * k, hgt, (BLANC, E5, C3)[i % 3])
                P.point(x + 1.5, y - hgt * 0.7 - dy, ENCRE)
    P.rect(cx + 9.0, 73.4, 3.2, 0.7, B3)                         # le tabouret
    for dx in (9.3, 11.6):
        P.rect(cx + dx, 74.0, 0.5, 2.2, B2)
    P.rect(cx + 9.6, 71.0, 2.0, 2.4, E5)                         # le képi posé dessus : le gardien s'est absenté
    P.rect(cx + 9.2, 73.0, 3.0, 0.5, N1)
    tab.plan("premier", 1.0)
    # ---- Premier plan : deux réverbères à néon qui encadrent, des formulaires qui volent, un panneau fléché.
    for (x, cote) in ((10.0, 1), (184.0, -1)):
        P.rect(x - 0.9, 12.0, 1.8, 68.0, N0)
        P.rect(x - 0.9 + (1.2 if cote > 0 else 0), 12.0, 0.6, 68.0, G1)
        P.courbe([(x, 12.0), (x + cote * 2, 5.0), (x + cote * 12, 4.0)], N0, P.ep(1.2))
        neon(P, x + cote * 7 - 5, x + cote * 7 + 5, 6.6, J2, J3, vacille=0.1 if cote > 0 else 0.0, lueur=9.0)
        voile(P, (np.abs(X - x - cote * 7) < 4 + (Y - 6) * 0.2) & (Y > 7) & (Y < 80), J2, 0.07)
        P.rect(x - 2.4, 76.0, 4.8, 4.0, N0)
    for i in range(6):                                        # des formulaires emportés par le courant d'air
        t = (p + i / 6.0) % 1.0
        x, y = 20 + 150 * ((hz(i, 1, 246) + t * 0.2) % 1.0), 10 + 50 * hz(i, 2, 246) + 5 * math.sin(t * 6.28 + i)
        if int(t * 8 + i) % 2:
            P.poly([(x, y), (x + 3.0, y - 0.8), (x + 3.4, y + 1.6), (x + 0.4, y + 2.4)], BLANC)
            P.trait(x + 0.8, y + 0.6, x + 2.6, y + 0.2, G3)
        else:
            P.poly([(x, y + 0.6), (x + 3.2, y), (x + 3.0, y + 1.0), (x + 0.2, y + 1.4)], E5)
    voile(P, (Y > 76.5), N0, 0.25)


# =====================================================================================================================
# Les étages de la Tour : un palier d'escalier en colimaçon qui donne sur un bureau encombré. Casiers de formulaires de
# toutes les couleurs jusqu'au plafond, guichet vitré, tampons, affiches réglementaires, poussière dorée dans un rai.
# =====================================================================================================================
@decor("grande-panne", "etage-guichets", soleil=(150.0, -20.0), tons=PANNE, nom="Les étages de la Tour")
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


# =====================================================================================================================
# Le bureau de la Planificatrice : un mur entier de petites cartes épinglées en rangs serrés (cochées à gauche, vierges à
# droite), un grand bureau gris avec une réussite en cours, la lampe de bureau, une fin d'après-midi qui n'arrive pas.
# =====================================================================================================================
@decor("grande-panne", "bureau-echeance", soleil=(176.0, 10.0), tons=PANNE, nom="Le bureau de la Planificatrice")
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


# =====================================================================================================================
# La Caverne des câbles : un tunnel sombre envahi de câbles épais comme des troncs, emmêlés du sol au plafond ; quelques
# diodes clignotent au loin ; la lueur sarcelle d'une gelée lumineuse à un croisement.
# =====================================================================================================================
@decor("grande-panne", "caverne-cables", soleil=(46.0, 52.0), tons=PANNE, nom="La Caverne des câbles")
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


# =====================================================================================================================
# Le Marais des mises à jour : une eau grise et des roseaux qui clignotent sous un ciel bas où flotte, à la place du
# soleil, une immense barre de chargement arrêtée à 37 % ; une barque carrée glisse entre les roseaux ; brume froide.
# =====================================================================================================================
@decor("grande-panne", "marais-majs", soleil=(96.0, 14.0), tons=PANNE, nom="Le Marais des mises à jour")
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
    pg.canard(P, 142.0 + 0.8 * onde(p, 0.3), 63.0, sens=-1)
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


# =====================================================================================================================
# La file d'impression : un quai fait de rames de papier où des feuilles jaunies attendent debout en rang, devant une
# estrade où trône une énorme imprimante beige au voyant orange (la clé) ; lumière de réserve à fournitures.
# =====================================================================================================================
@decor("grande-panne", "file-impression", soleil=(60.0, -14.0), tons=PANNE, nom="La file d'impression")
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


# =====================================================================================================================
# La Citadelle du nuage : des remparts blancs posés sur une mer de brume, un donjon et sa gargouille au bord du vide (la
# clé), un escalier dont les dernières marches sont à moitié transparentes ; très loin dessous, les lumières de
# l'ordinateur comme une ville la nuit. Le sol est à y = 70.
# =====================================================================================================================
@decor("grande-panne", "citadelle-nuage", soleil=(30.0, -4.0), tons=PANNE, nom="La Citadelle du nuage")
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


@decor("grande-panne", "dossier-temp", soleil=(120.0, -30.0), tons=PANNE, nom="Le dossier Temp")
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
    voile(P, (Y < 62), T.CIEL[8], 0.45)
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


# =====================================================================================================================
# La cabane de papier : l'intérieur d'une petite cabane faite de brouillons froissés et collés, éclairée par une lampe
# chaude, avec un hamac en ruban adhésif, une table basse, des cartes à jouer et une fenêtre en papier calque.
# =====================================================================================================================
@decor("grande-panne", "cabane-brouillon", soleil=(96.0, 6.0), tons=PANNE, nom="La cabane de papier")
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


# =====================================================================================================================
# L'Horloge système : une vaste salle ronde et silencieuse aux murs de roues dentées immobiles ; au centre, un grand
# balancier doré arrêté, penché d'un côté (la clé) ; un levier à son pied ; une trappe ronde au fond ; une lumière
# bleutée qui tombe d'en haut.
# =====================================================================================================================


@decor("grande-panne", "horloge-systeme", soleil=(104.0, -40.0), tons=PANNE, nom="L'Horloge système")
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
