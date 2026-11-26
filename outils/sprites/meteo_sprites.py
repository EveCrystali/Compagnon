"""Sprites météo de Pilou (effets sur la grille 48 × 56) et objets de boutique liés à la météo.

Appelé par generer.py. Effets : posés sur l'ancre « corps » (centre du corps, ≈ (24, 37) au stade 2), ils
couvrent toute la grille ; la pluie et la neige tombent AUTOUR de Pilou (bandeau du haut, colonnes des
côtés), et seul « meteo-mouille » les fait tomber sur lui quand il n'a pas de parapluie.
"""
import math

from toile import Toile, ecrire

ENCRE = "#1c2128"
BLANC = "#ffffff"
CREME = "#f6f8fa"
CREME_O = "#c9d1d9"
GRIS = "#768390"
GRIS_C = "#adbac7"
ARDOISE = "#3b4654"
ARGENT_C = "#e6ecf2"
B1, B2, B3, B4 = "#1f4f8a", "#4a8fdc", "#6cb6ff", "#b4dbff"
O1, O2, O3, O4, O5 = "#8a4a1f", "#d9803a", "#f69d50", "#ffc89a", "#ffd8b0"
J1, J2, J3, J4 = "#7a5a10", "#c9a227", "#f5d76e", "#fff6cc"
V1, V2, V3, V4 = "#3a2a7a", "#6a5acd", "#9b8cff", "#d2caff"
BR1, BR2 = "#4a2e17", "#7a4b26"

CORPS = (24, 37)   # pixel de la grille sous l'ancre « corps » au stade 2


def T(w, h):
    return Toile(w, h)


def autour(x, y):
    """Zone où la pluie tombe sans toucher Pilou ni son parapluie : le ciel (haut) et les côtés."""
    return y < 9 or x < 7 or x > 41


def goutte(t, x, y, longueur=3):
    for k in range(longueur):
        t.p(x, y + k, B3 if k < longueur - 1 else B4)


def effets():
    # ---- Pluie : gouttes qui tombent dans le ciel et sur les côtés (4 images, 110 ms).
    graines = [(3, 2), (11, 6), (19, 1), (28, 4), (36, 0), (44, 5), (2, 14), (45, 18), (4, 27), (43, 31), (1, 40),
               (46, 44), (5, 49), (42, 52), (24, 3), (32, 7), (15, 4), (40, 9)]
    images = []
    for k in range(4):
        t = T(48, 56)
        for (x, y0) in graines:
            for rep in range(0, 56, 18):
                y = (y0 + rep + k * 5) % 56
                if autour(x, y) and autour(x, y + 2):
                    goutte(t, x, y)
        images.append(t)
    ecrire("meteo-pluie", images, slot="effet", ancre="corps", point=CORPS, duree=110,
           commentaire="Pluie autour de Pilou (ciel et côtés)")

    # ---- Averse (et orage) : deux fois plus de gouttes, en biais.
    images = []
    for k in range(4):
        t = T(48, 56)
        for (x0, y0) in graines + [(x + 3, (y + 9) % 56) for x, y in graines]:
            for rep in range(0, 56, 14):
                y = (y0 + rep + k * 7) % 56
                x = x0 - (y // 8)
                if 0 <= x < 48 and autour(x, y) and autour(x - 1, y + 2):
                    t.p(x, y, B3)
                    t.p(x - 1, y + 1, B3)
                    t.p(x - 1, y + 2, B4)
        images.append(t)
    ecrire("meteo-averse", images, slot="effet", ancre="corps", point=CORPS, duree=90,
           commentaire="Averse : pluie dense, en biais")

    # ---- Éclair : un zigzag jaune dans le ciel, visible une image sur six.
    images = []
    for k in range(6):
        t = T(48, 56)
        if k in (0, 1):
            pts = [(8, 0), (5, 4), (8, 4), (4, 9), (7, 9), (3, 15)]
            for (a, b), (c, d) in zip(pts, pts[1:]):
                t.ligne(a, b, c, d, J4 if k == 0 else J3)
                t.ligne(a + 1, b, c + 1, d, J3)
        images.append(t)
    ecrire("meteo-eclair", images, slot="effet", ancre="corps", point=CORPS, duree=140,
           commentaire="Éclair d'orage (une image sur six)")

    # ---- Mouillé : gouttes qui lui tombent dessus et ruissellent, flaque à ses pieds.
    images = []
    for k in range(4):
        t = T(48, 56)
        # gouttes qui tombent sur la tête (dans la zone protégée par le parapluie)
        for i, x in enumerate((12, 20, 27, 35)):
            y = (k * 4 + i * 5) % 16
            goutte(t, x, y + 2)
        # ruissellement sur les flancs et gouttelettes collées au corps
        for i, (x, y) in enumerate(((10, 30), (38, 32), (12, 40), (36, 42), (17, 27), (31, 28))):
            dy = (k + i) % 4
            t.p(x, y + dy, B4)
            t.p(x, y + dy + 1, BLANC if (k + i) % 2 else B4)
        # goutte au bout de l'antenne
        t.p(24 + (k % 2), 15 + k, B4)
        # flaque sous ses pieds, qui ondule
        r = 15 + (k % 2)
        t.ell(24, 54.5, r, 1.8, B2)
        t.ell(24, 54.5, r - 3, 1.0, B3)
        for x in range(24 - r + 2, 24 + r - 2, 5):
            t.p(x + k % 3, 54, B4)
        images.append(t)
    ecrire("meteo-mouille", images, slot="effet", ancre="corps", point=CORPS, duree=160,
           commentaire="Pilou mouillé : gouttes sur lui, ruissellement, flaque")

    # ---- Neige : flocons qui descendent lentement autour de lui.
    images = []
    flocons = [(4, 3, True), (13, 7, False), (22, 2, False), (33, 5, True), (43, 1, False), (2, 18, False), (45, 22, True),
               (5, 33, True), (44, 38, False), (3, 47, False), (43, 50, True), (29, 8, False), (17, 1, True)]
    for k in range(4):
        t = T(48, 56)
        for (x, y0, gros) in flocons:
            y = (y0 + k * 2) % 56
            xx = x + (1 if (k + y0) % 4 == 0 else 0)
            if autour(xx, y):
                if gros:
                    t.p(xx, y, BLANC)
                    for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        t.p(xx + a, y + b, ARGENT_C)
                else:
                    t.p(xx, y, BLANC)
        images.append(t)
    ecrire("meteo-neige", images, slot="effet", ancre="corps", point=CORPS, duree=260,
           commentaire="Neige autour de Pilou")

    # ---- Givre : petit tas de neige sur la tête, glaçons, nuage de buée « brr ».
    images = []
    for k in range(2):
        t = T(30, 16)
        t.ell(15, 5.5, 9, 3.2, BLANC, cond=lambda x, y, u, v: v < 0.6)
        t.ell(15, 5.5, 9, 3.2, ARGENT_C, cond=lambda x, y, u, v: v >= 0.2 and v < 0.6)
        for x, l in ((9, 2), (13, 3), (18, 2), (21, 3)):
            for j in range(l):
                t.p(x, 7 + j, B4)
        t.contour(GRIS_C)
        # buée qui sort à droite
        bx = 25 + k
        t.ell(bx, 12, 2.2 + k * 0.6, 1.6 + k * 0.4, CREME)
        images.append(t)
    ecrire("meteo-givre", images, slot="effet", ancre="tete", point=(15, 6), duree=500,
           commentaire="Pilou gelé : neige sur la tête, glaçons, buée")

    # ---- Soleil : astre dans le coin, rayons qui tournent.
    images = []
    for k in range(2):
        t = T(48, 56)
        t.ell(6, 6, 4.5, 4.5, J3)
        t.ell(5, 5, 2, 2, J4)
        for i in range(8):
            a = i * math.pi / 4 + k * math.pi / 8
            x0, y0 = 6 + math.cos(a) * 6, 6 + math.sin(a) * 6
            x1, y1 = 6 + math.cos(a) * 8.5, 6 + math.sin(a) * 8.5
            t.ligne(round(x0), round(y0), round(x1), round(y1), O3 if i % 2 else J3)
        images.append(t)
    ecrire("meteo-soleil", images, slot="effet", ancre="corps", point=CORPS, duree=400,
           commentaire="Grand soleil (canicule)")

    # ---- Vent : traits qui filent de gauche à droite, une feuille emportée.
    images = []
    for k in range(3):
        t = T(48, 56)
        def libre(x, y):
            return not (7 <= x <= 41 and 19 <= y <= 51) and not (20 <= x <= 28 and y < 19)
        for i, (y, l) in enumerate(((3, 12), (8, 9), (13, 11), (17, 7), (24, 6), (31, 6), (39, 6), (46, 5), (53, 12))):
            x = (i * 13 + k * 11) % 48
            for j in range(l):
                if 0 <= x + j < 48 and libre(x + j, y):
                    t.p(x + j, y, ARGENT_C if j >= l - 3 else GRIS_C)
        fx, fy = (k * 15 + 4) % 48, 10 + k * 2
        t.rect(fx, fy, 2, 1, O3)
        t.p(fx + 1, fy + 1, O2)
        images.append(t)
    ecrire("meteo-vent", images, slot="effet", ancre="corps", point=CORPS, duree=150,
           commentaire="Vent fort : traits et feuille emportée")

    # ---- Brouillard : voile pâle sur le bas et les côtés.
    images = []
    for k in range(2):
        t = T(48, 56)
        for (y, x0, l, c) in ((4, 2, 18, "#c9d1d966"), (9, 26, 20, "#c9d1d955"), (15, 0, 10, "#adbac766"),
                              (28, 40, 8, "#adbac766"), (36, 0, 9, "#adbac766"), (47, 3, 42, "#c9d1d977"),
                              (50, 0, 48, "#c9d1d999"), (53, 2, 44, "#e6ecf2aa")):
            xs = (x0 + k * 3) % 48
            for j in range(l):
                x = (xs + j) % 48
                if y < 19 and 18 <= x <= 30:
                    continue
                t.p(x, y, c)
                if j % 3 != 1:
                    t.p(x, y + 1, c)
        images.append(t)
    ecrire("meteo-brouillard", images, slot="effet", ancre="corps", point=CORPS, duree=900,
           commentaire="Brouillard : voile pâle")


def objets():
    # Imperméable : poncho jaune sur le bas du corps, boutons, capuche repliée dans le dos.
    t = T(36, 9)
    t.poly([(5, 0), (31, 0), (34, 7), (2, 7)], J3)
    t.poly([(5, 0), (10, 0), (6, 7), (2, 7)], J2)
    t.poly([(27, 0), (31, 0), (34, 7), (30, 7)], J4)
    t.rect(17, 1, 2, 6, J2)
    for y in (2, 5):
        t.rect(15, y, 1, 1, ENCRE)
        t.rect(20, y, 1, 1, ENCRE)
    t.contour(J1)
    ecrire("impermeable", t, slot="dos", ancre="cou", point=(18, 1), commentaire="Imperméable jaune")

    # Bottes de pluie : une botte sur chaque pied.
    t = T(26, 8)
    for x0 in (1, 15):
        t.rect(x0, 0, 8, 6, B2)
        t.rect(x0, 0, 8, 1, B4)
        t.rect(x0 + 1, 1, 2, 4, B3)
        t.rect(x0 - (1 if x0 == 1 else 0), 6, 9, 1, ENCRE)
    t.contour(B1)
    ecrire("bottes-pluie", t, slot="pieds", ancre="pieds", point=(13, 5), commentaire="Bottes de pluie")

    # Moufles : une moufle tricotée orange, revers crème, cordon.
    t = T(12, 12)
    t.ell(6, 5, 4.5, 4.5, O3)
    t.ell(2, 6, 1.8, 2.4, O3)
    for x in range(2, 11, 2):
        t.p(x, 4, O4)
        t.p(x + 1, 6, O2)
    t.rect(2, 9, 8, 2, CREME)
    t.rect(2, 10, 8, 1, CREME_O)
    t.contour(O1)
    t.p(6, 11, GRIS)
    ecrire("moufles", t, slot="main", ancre="main", point=(4, 6), commentaire="Moufles")

    # Éventail : demi-cercle plissé qui s'agite.
    images = []
    for k in range(2):
        t = T(20, 16)
        a0 = -0.25 if k else 0.0
        for i in range(9):
            a = math.pi + i * math.pi / 8 + a0
            x1, y1 = 10 + math.cos(a) * 9, 13 + math.sin(a) * 9
            t.ligne(10, 13, round(x1), round(y1), B3 if i % 2 else CREME)
        t.rect(9, 12, 3, 4, BR2)
        t.contour(B1)
        images.append(t)
    ecrire("eventail", images, slot="main", ancre="main", point=(10, 14), duree=180, commentaire="Éventail")

    # Parapluie étoilé : violet, étoiles qui scintillent.
    images = []
    for k in range(2):
        t = T(40, 34)
        t.ell(20, 13, 19, 12, V2, cond=lambda x, y, u, v: v < 0)
        t.ell(20, 13, 19, 12, V3, cond=lambda x, y, u, v: v < 0 and int((u + 1) * 2.5) % 2 == 0)
        for i in range(5):
            t.ell(4 + i * 8, 13, 4.2, 2.4, None, cond=lambda x, y, u, v: v < 0.2)
        for i, (x, y) in enumerate(((8, 7), (17, 4), (26, 6), (33, 9), (13, 10), (22, 9))):
            c = J4 if (i + k) % 2 else J3
            t.p(x, y, c)
            if (i + k) % 3 == 0:
                for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    t.p(x + a, y + b, J3)
        t.rect(19, 0, 2, 2, J2)
        t.rect(19, 12, 2, 18, ARDOISE)
        t.ligne(20, 30, 17, 33, ARDOISE)
        t.ligne(16, 33, 15, 31, ARDOISE)
        t.contour(V1)
        images.append(t)
    ecrire("parapluie-etoile", images, slot="main", ancre="main", point=(19, 28), duree=400, commentaire="Parapluie étoilé")
