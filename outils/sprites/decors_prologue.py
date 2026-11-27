"""Décors du prologue « La colline d'en face » (humour) : une fin d'après-midi dorée, de la porte au sommet.

Palette : ciel lavande → pêche, soleil crème, herbes sarcelle aux crêtes dorées (pas de vert), bois, pierre mauve,
porte bleu-violet, sac orange. La lumière vient toujours du soleil bas, à droite : crêtes et bords droits éclairés,
ombres longues vers la gauche. La colline d'en face (le but) se voit dans presque tous les décors.
"""
import math

import toile
from decors_campagnes import decor, W, H
from peinture import (Palette, degrade, relief, voile, eclat, lueur, semis, ell, poly, rect, point, trait, trait1, hline, vline,
                      courbe, nuage, etoile4, hasard, seuil)

CIEL = ["#a9b8ec", "#c3c3ee", "#e8c6c6", "#ffd3a6", "#ffe8bf"]
SOLEIL, SOLEIL2 = "#fff8e1", "#ffefb8"
BRUME, BRUME2 = "#b6a9d6", "#9a8fc4"
LOIN, LOIN2 = "#7d86bd", "#6872aa"
S1, S2, S3, S4 = "#123f52", "#1d6578", "#2f8f9c", "#5bb3ae"
OR1, OR2, OR3 = "#d9a441", "#f2c46b", "#ffe08f"
M1, M2, M3, M4 = "#8c6343", "#bf915f", "#e2bd85", "#f4dcae"
P1, P2, P3 = "#6b6183", "#9b8fa8", "#c3b8c9"
D1, D2, D3 = "#3d3f7a", "#5458a0", "#7378c4"
LAITON, LAITON2 = "#c9a227", "#f5d76e"
O1, O2, O3, O4 = "#8a4a1f", "#d9803a", "#f69d50", "#ffc89a"
B1, B2, B3 = "#1f4f8a", "#4a8fdc", "#6cb6ff"
ENCRE, OMBRE = "#1c2128", "#2b2742"
CREME, BLANC = "#fff6e6", "#ffffff"
BR1, BR2 = "#4a2e17", "#7a4b26"
EAU1, EAU2, EAU3 = "#1b3550", "#2c5577", "#4f7fa6"
NENU = "#3f9f9a"

PAL = Palette(CIEL, SOLEIL, SOLEIL2, BRUME, BRUME2, LOIN, LOIN2, S1, S2, S3, S4, OR1, OR2, OR3, M1, M2, M3, M4, P1, P2,
              P3, D1, D2, D3, LAITON, LAITON2, O1, O2, O3, O4, B1, B2, B3, ENCRE, OMBRE, CREME, BLANC, BR1, BR2,
              EAU1, EAU2, EAU3).rampes(
    CIEL + [SOLEIL2, SOLEIL], ["#7d6fb8", "#b679a6", "#e9896b", "#f6a35c", "#ffc879", "#ffe1a0", SOLEIL2, SOLEIL],
    [OMBRE, D1, D2, D3], [S1, S2, S3, S4, OR2, OR3], [M1, M2, M3, M4, CREME, BLANC], [P1, P2, P3, CREME],
    [BR1, BR2, M2], [O1, O2, O3, O4], [B1, B2, B3], [EAU1, EAU2, EAU3, CIEL[0]], [LAITON, LAITON2, SOLEIL],
    [LOIN2, LOIN, BRUME2, BRUME], [OR1, OR2, OR3, SOLEIL2])


def ciel(t, y1=H, soleil=None, r=4.5):
    degrade(t, 0, y1, CIEL)
    if soleil:
        sx, sy = soleil
        lueur(t, sx, sy, r * 4.5, SOLEIL2, PAL, force=0.7)
        ell(t, sx, sy, r, r, SOLEIL)
        if toile.fin():
            ell(t, sx - r * 0.25, sy - r * 0.25, r * 0.55, r * 0.55, BLANC)


def colline_en_face(t, x, y, l=22, h=6):
    """La colline du but, au loin : ronde, brumeuse, crête dorée, son arbre unique au sommet."""
    relief(t, lambda u: y - h * max(0, 1 - ((u - x) / (l / 2)) ** 2) ** 0.6, BRUME2, lisere=OR3, x0=x - l / 2, x1=x + l / 2,
           bas=y + 2)
    trait(t, x, y - h - 1.5, x, y - h + 0.5, LOIN2, ep=t.e)
    ell(t, x, y - h - 2.2, 1.4, 1.1, LOIN2)


def herbe(t, f, base, x0=0, x1=None, graine=1, haute=2.5):
    """Prairie sous la courbe f : crête dorée, brins semés, ombres tramées vers le bas."""
    relief(t, f, base, lisere=OR2, x0=x0, x1=x1)
    e = t.e
    x1 = t.w if x1 is None else x1
    # Brins : petits traits verticaux plus clairs, dorés en crête.
    for X in range(int(x0 * e), int(x1 * e)):
        x = (X + 0.5) / e
        if hasard(X, 0, graine) < (0.18 if e == 1 else 0.24):
            y = f(x)
            h = 1 + hasard(X, 1, graine) * haute
            trait(t, x, y - h, x, y, OR2 if hasard(X, 2, graine) < 0.5 else S4, ep=1)


@decor("prologue", "seuil")
def seuil_maison(t, k):
    # Fond, à droite : le dehors, le soleil bas, la colline d'en face.
    ciel(t, 32, soleil=(84, 22), r=3.6)
    colline_en_face(t, 79, 29, 17, 4)
    relief(t, lambda x: 30 + 1.6 * math.sin(x / 5), S3, lisere=OR3, x0=62)
    relief(t, lambda x: 32.5 + 0.8 * math.sin(x / 3 + 1), S2, lisere=OR2, x0=62)
    # Mur de la maison : enduit chaud, plus sombre à gauche, plinthe de pierre.
    rect(t, 0, 0, 66, 40, M3)
    eclat(t, lambda x, y: 1 if x < 12 else (0.5 if x < 20 else 0), PAL, n=1, sens=-1, cadre=(0, 0, 66, 40))
    for i, (x, y, w) in enumerate(((4, 6, 5), (14, 3, 4), (50, 8, 6), (56, 18, 4), (6, 22, 4))):
        hline(t, x, x + w, y, M2)
        hline(t, x + 1, x + w - 1, y + 0.5 if toile.fin() else y + 1, M2)
    rect(t, 0, 33, 66, 7, P2)
    for x in range(0, 66, 6):
        vline(t, x + (3 if (x // 6) % 2 else 0), 33, 36.5, P1)
    hline(t, 0, 66, 36.5, P1)
    for x in range(2, 66, 6):
        vline(t, x, 36.5, 40, P1)
    hline(t, 0, 66, 33, P3)
    # Avant-toit et coin du mur éclairé par le soleil.
    poly(t, [(-1, 0), (68, 0), (70, 3), (-1, 3)], OMBRE)
    for x in range(0, 69, 3):
        ell(t, x + 1.5, 3, 1.5, 1.2, D1, cond=lambda x, y, u, v: v > 0)
    rect(t, 64, 3, 2, 37, M4)
    vline(t, 66, 3, 40, OR3)
    # Porte : arche bleu-violet dans un chambranle de pierre, hublot, poignée de laiton.
    cx = 30
    ell(t, cx, 18, 11.5, 11.5, P2, cond=lambda x, y, u, v: y < 18.5)
    rect(t, cx - 11.5, 18, 23, 15, P2)
    ell(t, cx, 18, 11.5, 11.5, P3, cond=lambda x, y, u, v: y < 18.5 and u > 0.55)
    rect(t, cx + 9, 18, 2.5, 15, P3)
    ell(t, cx, 18, 9, 9, D2, cond=lambda x, y, u, v: y < 18.5)
    rect(t, cx - 9, 18, 18, 15, D2)
    for i in range(-2, 3):
        vline(t, cx + i * 3.6 - 0.5, 9.5 if abs(i) < 2 else 12, 33, D1)
    ell(t, cx, 18, 9, 9, D3, cond=lambda x, y, u, v: u > 0.78 and y < 33)
    rect(t, cx + 7.6, 18, 1.4, 15, D3)
    ell(t, cx, 14, 3, 3, LAITON)
    ell(t, cx, 14, 2.2, 2.2, EAU2)
    ell(t, cx + 0.6, 13.4, 1, 0.9, B3)
    trait(t, cx - 2.2, 14, cx + 2.2, 14, LAITON, ep=1)
    ell(t, cx + 6, 24, 1.3, 1.3, LAITON2)
    point(t, cx + 6, 24.5, LAITON)
    # Lumière rasante qui traverse le seuil : un grand pan doré sur le mur et la porte.
    eclat(t, lambda x, y: 1 if 0 < (x - 30) - (y - 10) * 0.9 < 22 else 0, PAL, n=1, cadre=(0, 4, 64, 33))
    # Marche de pierre, paillasson, sac à dos trop plein (lampe de poche, corde à sauter).
    poly(t, [(14, 33), (46, 33), (50, 37), (10, 37)], P3)
    hline(t, 10, 50, 37, P1)
    poly(t, [(17, 34.5), (42, 34.5), (44, 37), (15, 37)], O1)
    for i in range(6):
        trait(t, 18 + i * 4.2, 35, 17 + i * 4.4, 37, O2, ep=t.e)
    # Le sac (ombre longue à gauche) : bien droit, rabat qui ne ferme plus, poches pleines.
    eclat(t, lambda x, y: 1 if (y > 34.5 and 24 < x < 36 and (36 - x) > (37 - y) * 2.5) else 0, PAL, n=1, sens=-1,
          cadre=(20, 33, 40, 37))
    # Ce qui dépasse, derrière le rabat : la lampe de poche, une chaussette, la corde à sauter.
    poly(t, [(41.5, 22.5), (46, 17.5), (47.8, 19), (43.3, 24)], B1)
    ell(t, 47, 18.2, 1.5, 1.5, LAITON2)
    point(t, 47.3, 17.8, BLANC)
    poly(t, [(36.5, 23), (35.8, 18.5), (38.3, 18.2), (38.8, 22.5)], CREME)
    rect(t, 35.8, 18.4, 2.5, 0.8 if toile.fin() else 1, B2)
    ell(t, 39.5, 22.5, 4.6, 1.8, O4)       # le pull roulé
    poly(t, [(33.5, 23), (45.5, 23), (46, 35), (33, 35)], O1)
    poly(t, [(34.3, 23.5), (44.7, 23.5), (45.2, 34.3), (33.8, 34.3)], O2)
    poly(t, [(36, 23.5), (44.7, 23.5), (45.2, 34.3), (36, 34.3)], O3)
    ell(t, 39.5, 23.6, 6.3, 2.6, B1, cond=lambda x, y, u, v: v > -0.3)    # rabat
    ell(t, 39.5, 23.4, 5.6, 2.0, B2, cond=lambda x, y, u, v: v > -0.3)
    ell(t, 40.5, 23.2, 3.4, 1.2, B3, cond=lambda x, y, u, v: v > -0.3)
    rect(t, 39, 25.4, 1.2, 2.6, B1)
    rect(t, 38.6, 27.5, 2, 1.4, LAITON)
    poly(t, [(35, 29), (44, 29), (44, 33.5), (35, 33.5)], O1)          # poche
    poly(t, [(35.6, 29.5), (43.4, 29.5), (43.4, 33), (35.6, 33)], O3)
    hline(t, 35.6, 43.4, 29.5, O4)
    trait(t, 35.5, 30.6, 43.5, 30.6, O2, ep=1)
    # Corde à sauter : une poignée pend sur le côté.
    courbe(t, [(33.6, 24), (30.5, 27), (32, 32), (33.2, 34.5)], CREME, ep=1)
    rect(t, 32.4, 32.2, 1.6, 2.8, O4)
    hline(t, 32.4, 34, 32.2, BLANC)
    # Pot de pâquerettes, à gauche, dans l'ombre.
    poly(t, [(5, 30), (12, 30), (11, 36), (6, 36)], O1)
    rect(t, 4.5, 29.5, 8, 1.5, O2)
    for i, (x, y) in enumerate(((6, 26), (8.5, 24.5), (11, 26.5), (7.5, 28), (10, 28.5))):
        trait(t, x, y, 8.5, 30, S2, ep=1)
        ell(t, x, y, 1.3, 1.3, CREME)
        point(t, x, y, OR2)
    # Détail : un mot punaisé sur la porte, dessiné plutôt qu'écrit : une colline, une flèche, un soleil.
    poly(t, [(21.5, 18), (27, 17.5), (27.3, 23.5), (21.8, 24)], CREME)
    point(t, 24.4, 18, O2)
    trait(t, 22.3, 22.8, 24.4, 20.6, B1, ep=1)
    trait(t, 24.4, 20.6, 26.5, 22.6, B1, ep=1)
    point(t, 26, 19.4, O3)
    trait(t, 22.4, 20, 23.5, 20, O1, ep=1)
    # Herbe dorée au pied du mur, côté soleil.
    herbe(t, lambda x: 37 + 0.6 * math.sin(x), S2, x0=66, graine=4)


def escargot(t, x, y, d=1):
    """Escargot : coquille spirale orange, corps crème, cornes (d : 1 vers la droite, -1 vers la gauche)."""
    rect(t, min(x - 2.5 * d, x + 3.5 * d), y + 1.8, 6, 1, CREME)
    ell(t, x, y, 2.4, 2.4, O1)
    ell(t, x, y, 1.9, 1.9, O3)
    ell(t, x + 0.3 * d, y + 0.2, 1.0, 1.0, O2)
    point(t, x + 0.3 * d, y + 0.2, O4)
    if toile.fin():
        ell(t, x - 0.6 * d, y - 0.9, 0.7, 0.5, O4)
    tx = x + 3.5 * d
    trait(t, tx, y + 1.8, tx + 0.6 * d, y - 0.5, CREME, ep=1)
    trait(t, tx - 0.8 * d, y + 1.8, tx - 0.6 * d, y - 0.2, CREME, ep=1)
    point(t, tx + 0.6 * d, y - 0.7, ENCRE)


def maison_minuscule(t, x, y):
    """La maison, au loin : mur crème, toit violet, porte ronde, cheminée."""
    rect(t, x - 3, y - 3, 6, 3, M4)
    poly(t, [(x - 4, y - 3), (x, y - 6), (x + 4, y - 3)], D1)
    rect(t, x + 1.5, y - 6.5, 1, 2, P1)
    ell(t, x - 0.5, y - 0.9, 1.0, 1.1, D2, cond=lambda a, b, u, v: b < y)
    point(t, x + 2, y - 2, OR3)


def nenuphar(t, x, y, r, c=NENU, clair=S4):
    ell(t, x, y, r, r * 0.42, c, cond=lambda a, b, u, v: not (u > 0 and abs(v) < 0.25))
    ell(t, x - r * 0.2, y - r * 0.1, r * 0.55, r * 0.2, clair, cond=lambda a, b, u, v: not (a > x and abs(b - y) < 0.4))


def roseaux(t, x0, x1, bas, graine, haut=14, quenouilles=True):
    for X in range(int(x0 * t.e), int(x1 * t.e)):
        x = (X + 0.5) / t.e
        if hasard(X // t.e, 9, graine) < 0.35 and X % t.e == 0:
            h = haut * (0.5 + 0.5 * hasard(X, 10, graine))
            pench = (hasard(X, 11, graine) - 0.5) * 3
            c = S1 if hasard(X, 12, graine) < 0.5 else S2
            trait(t, x, bas, x + pench, bas - h, c, ep=1)
            if quenouilles and hasard(X, 13, graine) < 0.25:
                ell(t, x + pench, bas - h + 1.5, 0.7, 1.8, BR2)


@decor("prologue", "jardin")
def jardin(t, k):
    ciel(t, 30, soleil=(76, 9), r=3)
    nuage(t, 24, 9, 16, 3.2, CREME, BLANC, CIEL[2])
    colline_en_face(t, 76, 26, 24, 5)
    relief(t, lambda x: 24 + 2.5 * math.sin(x / 9 + 1) + 1.5 * math.sin(x / 4), S3, lisere=OR3)
    maison_minuscule(t, 22, 22.5 + 2.5 * math.sin(22 / 9 + 1) + 1.5 * math.sin(22 / 4))
    herbe(t, lambda x: 29 + 1.2 * math.sin(x / 5), S2, graine=2, haute=2)
    # Premier plan : brins géants, vus d'une fourmi.
    brins = [(4, -6, 9), (9, -2, 8), (14, 3, 6), (66, 5, 7), (84, -4, 9), (90, 3, 10), (94, -1, 8)]
    for i, (x, pench, larg) in enumerate(brins):
        top = 2 + (i * 7) % 9
        poly(t, [(x - larg / 3, 41), (x + larg / 3, 41), (x + pench + 0.6, top), (x + pench - 0.6, top + 2)],
             S1 if i % 2 else S2)
        trait(t, x + larg / 3 - 0.5, 40, x + pench + 0.4, top + 1, OR2, ep=1)
    # La feuille de l'escargot, au premier plan, et son escargot.
    poly(t, [(30, 41), (36, 34), (50, 30.5), (60, 32), (52, 37), (40, 41)], S2)
    poly(t, [(36, 34), (50, 30.5), (60, 32), (54, 33), (44, 35)], S3)
    courbe(t, [(32, 40), (42, 34), (52, 32.5), (59, 32)], S4, ep=1)
    for i in range(4):
        trait(t, 38 + i * 5, 35.5 - i * 0.9, 41 + i * 5, 33.3 - i * 0.6, S4, ep=1)
    trait(t, 51, 31, 59.5, 32, OR3, ep=1)
    escargot(t, 47, 29.5, 1)
    # Graines de pissenlit qui flottent.
    for (x, y) in ((60, 14), (70, 19), (55, 8)):
        etoile4(t, x, y, CREME, r=0.5)
        trait(t, x, y, x - 0.5, y + 1.5, CREME, ep=1)


@decor("prologue", "mare", images=2, duree=700)
def mare(t, k):
    ciel(t, 22, soleil=(18, 8), r=3)
    nuage(t, 66, 8, 20, 3, CREME, BLANC, CIEL[2])
    colline_en_face(t, 70, 20, 22, 5)
    relief(t, lambda x: 19.5 + 1.5 * math.sin(x / 7), S3, lisere=OR3)
    relief(t, lambda x: 22 + 0.8 * math.sin(x / 4 + 2), S2, lisere=OR2)
    # La mare : un grand ovale d'eau sombre qui reflète le ciel en haut.
    ell(t, 48, 31, 40, 8.5, EAU1)
    ell(t, 48, 30, 37, 5.6, EAU2, cond=lambda x, y, u, v: v < 0)
    ell(t, 48, 30, 30, 3.5, EAU3, cond=lambda x, y, u, v: v < -0.3)
    # Reflet du soleil, des risées qui glissent (deux images).
    for i in range(7):
        x = 14 + i * 11 + (2 if k else 0)
        y = 30 + (i % 3) * 2
        hline(t, x, x + 3 + i % 2, y, EAU3)
    hline(t, 16, 20, 25.5, SOLEIL2)
    hline(t, 17, 19, 26.5, OR3)
    # Trois nénuphars en ligne, et la grenouille sur celui du milieu.
    for i, x in enumerate((30, 48, 66)):
        nenuphar(t, x, 31.5 + (i % 2) * 0.5, 5)
    ell(t, 48, 28.5, 2.6, 2.1, S3)
    ell(t, 48, 29.4, 1.6, 1.2, CREME)
    ell(t, 46.7, 26.8, 1.1, 1.1, S4)
    ell(t, 49.3, 26.8, 1.1, 1.1, S4)
    point(t, 46.7, 26.8 if k else 26.4, ENCRE)
    point(t, 49.3, 26.8 if k else 26.4, ENCRE)
    hline(t, 46.8, 49.2, 28.6, S1)
    rect(t, 45.5, 30, 1.2, 1, S2)
    rect(t, 49.3, 30, 1.2, 1, S2)
    # Roseaux et quenouilles des deux côtés.
    roseaux(t, 0, 14, 40, 3, haut=18)
    roseaux(t, 82, 96, 40, 5, haut=16)
    herbe(t, lambda x: 38.5 + 0.8 * math.sin(x / 3), S1, x1=20, graine=8)
    herbe(t, lambda x: 38.5 + 0.8 * math.sin(x / 3), S1, x0=78, graine=9)
    # Une libellule, ailes qui battent.
    trait(t, 76, 15, 80, 15, B1, ep=t.e)
    for dy in ((-1, 1) if k == 0 else (-0.5, 0.5)):
        ell(t, 78, 15 + dy, 1.8, 0.7, BLANC if toile.fin() else B3)


def chemin(t, pts, l, c):
    """Chemin qui s'élargit en approchant (perspective) : une suite de segments."""
    for i in range(len(pts) - 1):
        (a, b), (cx, d) = pts[i], pts[i + 1]
        n = 30
        for j in range(n + 1):
            u = j / n
            x, y = a + (cx - a) * u, b + (d - b) * u
            w = l * (0.3 + 0.7 * max(0, (y - 10)) / 30)
            rect(t, x - w / 2, y, w, 0.6, c)


@decor("prologue", "pied-colline", images=2, duree=800)
def pied_colline(t, k):
    ciel(t, 26, soleil=(88, 14), r=3.2)
    nuage(t, 18, 7, 18, 3, CREME, BLANC, CIEL[2])
    relief(t, lambda x: 22 + 2 * math.sin(x / 10), BRUME2, lisere=OR3)
    # La grande colline ronde qui remplit la droite, son flanc gauche à l'ombre.
    relief(t, lambda x: 40 - 32 * max(0, 1 - ((x - 64) / 40) ** 2) ** 0.7, S3, lisere=OR3)
    eclat(t, lambda x, y: 1 if x < 54 - (y - 8) * 0.3 else 0, PAL, n=1, sens=-1, cadre=(20, 5, 70, 40), sur=(S3,))
    relief(t, lambda x: 31 + 1.2 * math.sin(x / 6), S2, lisere=OR2, x1=96)
    # Deux chemins qui se séparent : l'un grimpe en lacets, l'autre contourne par la gauche.
    chemin(t, [(46, 40), (48, 35), (54, 31), (62, 27), (58, 22), (66, 17), (64, 12)], 7, M4)
    chemin(t, [(46, 40), (40, 35), (30, 32), (18, 31), (4, 30)], 7, M4)
    semis(t, lambda x, y: y > 32, [M3], 0.15, graine=4, cadre=(0, 30, 96, 40))
    # Le bâton planté bien droit à la fourche, un ruban qui flotte, un oiseau dessus.
    rect(t, 45.5, 22, 1.2, 14, BR2)
    vline(t, 46.5, 22, 36, BR1)
    poly(t, [(46.5, 24), (51, 23 + k), (50, 25.5), (46.5, 25.5)], O3)
    ell(t, 46, 21, 1.6, 1.2, B2)
    ell(t, 47.2, 20.3, 0.9, 0.9, B2)
    point(t, 47.6, 20.2, ENCRE)
    point(t, 48.4, 20.5, OR1)
    rect(t, 44.2, 20.8, 1.3, 0.8, B1)
    herbe(t, lambda x: 38 + 0.6 * math.sin(x * 1.7), S1, graine=12, haute=2)


@decor("prologue", "pente", images=2, duree=900)
def pente(t, k):
    ciel(t, 40, soleil=(14, 10), r=3)
    nuage(t, 40, 6, 22, 3, CREME, BLANC, CIEL[2])
    relief(t, lambda x: 30 + 3 * math.sin(x / 9), BRUME2, lisere=OR3, x1=40)
    # La pente, raide, de bas à gauche vers le haut à droite.
    f = lambda x: 40 - x * 0.36 - 1.5 * math.sin(x / 7)
    relief(t, f, S3, lisere=OR3)
    relief(t, lambda x: f(x) + 6, S2)
    relief(t, lambda x: f(x) + 13, S1)
    semis(t, lambda x, y: y > f(x) + 2, [S4, OR2], 0.05, graine=21)
    # Le panneau de bois de travers, flèche vers le haut.
    px, py = 26, f(26)
    trait(t, px, py + 1, px + 1.5, py - 9, BR2, ep=t.e)
    poly(t, [(px - 4, py - 12), (px + 6, py - 13.5), (px + 6.5, py - 9), (px - 3.5, py - 7.5)], BR2)
    poly(t, [(px - 3.4, py - 11.5), (px + 5.6, py - 12.8), (px + 5.9, py - 9.6), (px - 3, py - 8.3)], M2)
    poly(t, [(px - 1, py - 9.5), (px + 2.5, py - 10), (px + 2.6, py - 11.2), (px + 4, py - 10.2),
             (px + 2.8, py - 9), (px + 2.7, py - 9.4), (px - 0.8, py - 8.9)], BR1)
    # Le pissenlit géant, tête en aigrette, graines qui s'envolent (deux images).
    dx, dy = 80, 34
    courbe(t, [(dx, dy + 6), (dx - 2, dy - 8), (dx + 1, dy - 16)], S1, ep=t.e)
    ell(t, dx + 1, dy - 19, 5.5, 5.5, CREME)
    for a in range(0, 360, 20):
        r = math.radians(a)
        trait(t, dx + 1, dy - 19, dx + 1 + 5.5 * math.cos(r), dy - 19 + 5.5 * math.sin(r), BLANC, ep=1)
        etoile4(t, dx + 1 + 5.7 * math.cos(r), dy - 19 + 5.7 * math.sin(r), BLANC, r=0)
    ell(t, dx + 1, dy - 19, 1.2, 1.2, OR1)
    for i, (x, y) in enumerate(((84, 12), (88, 7), (80, 6), (92, 15))):
        x += k * 1.5
        y -= k * 1
        etoile4(t, x, y, BLANC, r=0.5)
        trait(t, x, y, x - 0.6, y + 1.6, CREME, ep=1)
    # Pâquerettes au premier plan.
    for (x, y) in ((8, 37), (14, 38.5), (40, 33), (52, 30), (60, 34)):
        for a in range(0, 360, 60):
            r = math.radians(a)
            point(t, x + 0.9 * math.cos(r), y + 0.9 * math.sin(r), BLANC)
        point(t, x, y, OR2)


@decor("prologue", "sommet", images=2, duree=1200)
def sommet(t, k):
    degrade(t, 0, 30, ["#7d6fb8", "#b679a6", "#e9896b", "#f6a35c", "#ffc879", "#ffe1a0"])
    lueur(t, 66, 29, 26, SOLEIL2, PAL, force=0.7, ry=12)
    ell(t, 66, 29, 6, 6, SOLEIL, cond=lambda x, y, u, v: y < 29.5)
    if toile.fin():
        ell(t, 66, 29, 4.5, 4.5, BLANC, cond=lambda x, y, u, v: y < 29.5)
    for i, (x, y, l) in enumerate(((20, 10, 26), (52, 6, 18), (84, 14, 16))):
        x += k * 0.5
        nuage(t, x, y, l, 2.2, "#f6a35c", "#ffd3a6", "#b679a6")
    # L'horizon, très loin, et la vallée en contrebas : la maison et la mare toutes petites.
    relief(t, lambda x: 29 + 1.2 * math.sin(x / 6), LOIN, lisere=OR3)
    relief(t, lambda x: 31 + 0.8 * math.sin(x / 4 + 1), LOIN2, lisere=OR2)
    maison_minuscule(t, 30, 32.5)
    ell(t, 42, 33.6, 4, 0.9, EAU3)
    hline(t, 40, 43, 33.6, SOLEIL2)
    # Le haut de la colline, herbe rase, son arbre unique ; des oiseaux rentrent.
    relief(t, lambda x: 33 + 7 * ((x - 70) / 70) ** 2, S2, lisere=OR3)
    relief(t, lambda x: 36 + 5 * ((x - 70) / 70) ** 2, S1)
    semis(t, lambda x, y: True, [OR2], 0.1, graine=33, cadre=(0, 34, 96, 40))
    tx = 18
    trait(t, tx, 34, tx + 0.5, 22, BR1, ep=t.e + 1)
    trait(t, tx + 0.5, 26, tx - 3, 22, BR1, ep=1)
    trait(t, tx + 0.5, 25, tx + 4, 21, BR1, ep=1)
    ell(t, tx, 19, 6, 4.5, S1)
    ell(t, tx + 1.5, 18, 4.5, 3.4, S2)
    ell(t, tx + 2.5, 17.5, 2.5, 2, OR1)
    for (x, y) in ((50, 15), (56, 12), (61, 16)):
        x += k
        trait(t, x - 1, y - 0.6, x, y, OMBRE, ep=1)
        trait(t, x, y, x + 1, y - 0.6, OMBRE, ep=1)
