"""Décors haute définition des scènes d'évolution (480 × 240) : le fond du jardin de Pilou, à trois heures.

docs/LORE.md : « il dort sous un pot de fleurs au fond du jardin ». C'est là qu'il se métamorphose : le matin (Pilou,
niveau 10), le soir (Pilou Nimbus, 25), la nuit étoilée (Pilou Astral, 40). Même jardin, même pot-cabane, autre lumière.
Le croquis 192 × 80 est dans decors_evolution.py ; ici le lieu est repeint, pas agrandi.

Une haie ronde au fond, une barrière de bois, des roses trémières et un petit massif à droite, l'herbe qui descend vers
nous ; au centre-gauche, le pot de terre cuite renversé qui lui sert de cabane (bord épais posé dans l'herbe, trou
d'écoulement en haut, petite porte en arche, allumée la nuit), un chemin de cailloux. Jamais de rouge contre vert : les
fleurs sont pêche, prune, crème et or ; le feuillage est sarcelle.

Coordonnées : unités du monde (x de 0 à 192, y de -16 à 80 ; pixel = 2,5 x, 2,5 y + 40). Le pot vers x = 30 ; Pilou se
tient vers x = 100, pieds à y = 76 ; la droite reste dégagée pour un personnage.
"""
import math

import numpy as np

import paysage as pg
from decors_hd import decor
from decors_hd_petit_nuage import LAVE, SOIR, NUIT, RO1, RO2, TE1, TE2, TE3, BO1, BO2, BO3, PJ2, PJ3, PJ4, LA1, LA2, LA3, ENCRE, NU1, NU2, R2, R3, R4, CREME, BLANC, dents, sommets
from paysage import hz, onde, voile, halo

PRUNE, PECHE = pg.cs("#8a79b8", "#f5c8a0")


def _a(x):
    return np.asarray(x, dtype=float)


def pot_cabane(P, x, base, nuit, soir, k=2.0):
    """Le pot de fleurs renversé, la cabane de Pilou : plus haut que lui (Pilou fait 35 unités). x : son milieu ; base :
    la ligne de l'herbe ; k : sa taille."""
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    h, bas, haut = 23.0 * k, 13.0 * k, 8.4 * k                    # hauteur, demi-largeur en bas, en haut
    cote = 1.0 if P.soleil[0] > x else -1.0
    terre = [BO1, BO2, BO2, RO1, RO2] if nuit else ([BO2, RO1, RO1, RO2, LA1] if soir else [BO2, RO1, RO2, LA1, LA2])
    # Son ombre sur l'herbe, à l'opposé de la lumière.
    voile(P, (np.hypot((X - x + cote * 9.0 * k) / (18.0 * k), (Y - base - 0.6) / (1.6 * k)) < 1.0) & (P.a >= 0), T.S0, 0.5)
    corps = P.masque_poly([(x - haut, base - h), (x + haut, base - h), (x + bas, base - 4.0 * k), (x - bas, base - 4.0 * k)])
    u = (X - x) / (haut + (bas - haut) * np.clip((Y - base + h) / (h - 4.0 * k), 0, 1))
    v = 0.56 + 0.34 * u * cote - 0.16 * u * u + 0.16 * (pg.fbm(X / 4.0, Y / 3.0, 3, 1200) - 0.5)
    P.rampe(corps, v, terre, 0.6)
    for j in range(6):                                          # les cernes du tour de potier
        P.remplir(corps & (np.abs(Y - (base - h + 3.0 * k + j * 2.9 * k) - 0.5 * k * u * u) < 0.22), terre[1])
    # Des traces : une coulure de mousse, une fêlure recollée, des taches de terre.
    voile(P, corps & (np.abs(X - x + 6.0 * k - 0.8 * np.sin(Y / 2.0)) < 1.2 * k) & (Y < base - 11.0 * k), T.S2, 0.6)
    voile(P, corps & (pg.fbm(X / 2.4, Y / 2.0, 3, 1203) > 0.68) & (Y > base - 12.0 * k), BO2, 0.5)
    P.courbe([(x + 5.0 * k, base - 20.0 * k), (x + 6.4 * k, base - 15.0 * k), (x + 5.4 * k, base - 12.0 * k), (x + 6.6 * k, base - 9.0 * k)], BO2, 1)
    # Le bord épais, posé dans l'herbe.
    bord = (np.abs(X - x) < bas + 1.8 * k) & (Y >= base - 4.4 * k) & (Y < base + 0.6)
    P.rampe(bord, 0.56 + 0.36 * (X - x) / (bas + 1.8 * k) * cote + 0.1 * (pg.fbm(X / 3.0, Y, 2, 1201) - 0.5), terre, 0.6)
    P.remplir(bord & (Y < base - 4.4 * k + 0.6), terre[4])
    P.remplir(bord & (Y > base - 0.6), BO2)
    # Le dessus : le fond du pot, son trou d'écoulement (la cheminée : il en sort un fil de fumée).
    P.ell(x, base - h, haut, 1.6 * k, terre[3])
    P.ell(x, base - h - 0.2, haut - 1.0 * k, 1.1 * k, terre[4])
    P.ell(x, base - h - 0.2, 2.2 * k, 0.7 * k, ENCRE)
    pg.fumee(P, x, base - h - 0.6, p)
    # La porte en arche : planches, ferrures, heurtoir ; la nuit, elle est entrouverte sur une lumière chaude.
    dx_ = x - 1.0 * k
    r_ext, r_int, hh = 5.2 * k, 4.2 * k, 7.0 * k
    arche = lambda r: ((np.hypot(X - dx_, Y - (base - hh)) < r) & (Y <= base - hh)) | ((np.abs(X - dx_) < r) & (Y > base - hh) & (Y < base))
    P.remplir(arche(r_ext), BO1)
    porte = arche(r_int)
    if nuit:
        vif = LA3 if int(p * 8) % 5 else LA2
        P.remplir(porte, LA2)
        P.remplir(porte & (X > dx_ - 1.6 * k), vif)
        P.remplir(porte & (X < dx_ - 2.2 * k), BO2)               # le battant, entrouvert
        P.remplir(porte & (np.abs(X - dx_ + 2.2 * k) < 0.3), BO1)
        P.remplir(porte & (Y > base - 3.0) & (X > dx_ - 1.0 * k) & (X < dx_ + 2.0 * k), TE3)   # un bout de tapis, dedans
    else:
        P.rampe(porte, 0.4 + 0.06 * (X - dx_) * cote + 0.3 * (pg.fbm(X / 1.0, Y / 9.0, 2, 1202) - 0.5), [BO1, BO2, BO3], 0.5)
        for i in (-1, 0, 1):
            P.remplir(porte & (np.abs(X - dx_ - i * 2.4 * k) < 0.25), BO1)
        for y in (base - 9.0 * k, base - 3.0 * k):
            P.remplir(porte & (np.abs(Y - y) < 0.5), R2)
        P.ell(dx_ + 2.4 * k, base - 5.6 * k, 0.9, 0.9, PJ3)
    # La petite fenêtre ronde et son rebord fleuri ; le paillasson ; la boîte aux lettres et son drapeau.
    wx, wy = x + 7.2 * k, base - 13.0 * k
    P.ell(wx, wy, 2.6 * k, 2.6 * k, BO1)
    P.ell(wx, wy, 2.0 * k, 2.0 * k, (LA3 if int(p * 8) % 6 else LA2) if nuit else (T.CIEL[8] if not soir else LA2))
    P.rect(wx - 0.3, wy - 2.0 * k, 0.6, 4.0 * k, BO1)
    P.rect(wx - 2.0 * k, wy - 0.3, 4.0 * k, 0.6, BO1)
    P.rect(wx - 3.0 * k, wy + 2.4 * k, 6.0 * k, 1.2, BO2)
    for i in range(5):
        bal = 0.2 * onde(p, 0.2 * i)
        P.trait(wx - 4.4 + i * 2.2, wy + 2.4 * k, wx - 4.4 + i * 2.2 + bal, wy + 2.4 * k - 2.4, T.S2 if not nuit else T.S0)
        P.ell(wx - 4.4 + i * 2.2 + bal, wy + 2.4 * k - 2.8, 0.9, 0.8, (PECHE, CREME, PRUNE)[i % 3])
    P.poly([(dx_ - 5.0 * k, base + 0.4), (dx_ + 5.0 * k, base + 0.4), (dx_ + 6.0 * k, base + 3.4), (dx_ - 6.0 * k, base + 3.4)], TE2)
    for i in range(10):
        P.trait(dx_ - 4.6 * k + i * 2.0, base + 0.8, dx_ - 5.2 * k + i * 2.3, base + 3.2, TE1)
    bx_ = x + bas + 7.0
    P.rect(bx_, base - 14.0, 1.2, 14.4, BO2)
    P.rect(bx_ - 3.6, base - 20.0, 8.4, 6.0, T.BLEU if not nuit else T.CIEL[4])
    P.rect(bx_ - 3.6, base - 20.0, 8.4, 1.2, CREME if not nuit else T.CIEL[7])
    P.rect(bx_ - 2.2, base - 17.4, 5.6, 0.7, ENCRE)
    P.trait(bx_ + 4.8, base - 15.0, bx_ + 4.8, base - 22.0 + 0.4 * onde(p), LA1)
    P.rect(bx_ + 4.8, base - 23.4 + 0.4 * onde(p), 3.0, 2.0, LA1)
    for (bx2, c0) in ((dx_ + 6.6 * k, T.BLEU), (dx_ + 6.6 * k + 3.4, T.BLEU)):                 # ses bottes, devant la porte
        P.rect(bx2, base - 5.0, 2.4, 5.0, c0 if not nuit else T.CIEL[3])
        P.rect(bx2, base - 1.4, 3.6, 1.4, c0 if not nuit else T.CIEL[3])
    if nuit:                                                    # la lumière de la porte et de la fenêtre, sur l'herbe
        halo(P, dx_, base - 3.0 * k, 20.0 * k, LA1, 0.55, ry=11 * k)
        halo(P, wx, wy, 8.0 * k, LA1, 0.45)
        voile(P, (np.abs(X - dx_ - (Y - base) * 0.3) < 4.0 * k + (Y - base) * 1.6) & (Y > base) & (Y < base + 9.0) & (P.a >= 0), LA2, 0.5, lumiere=True)
        pg.lanterne(P, x + bas + 2.0, base - 12.0 * k, corde=3.0)   # une lanterne pendue au bord du pot


def rose_tremiere(P, x, y, h, graine, nuit):
    """Une rose trémière : une haute tige, des feuilles rondes en bas, des fleurs étagées (pêche, prune, crème, or)."""
    T = pg.T
    bal = 0.7 * onde(P.p, x / 31.0) * h / 24.0
    tete = (x + bal, y - h)
    P.courbe([(x, y), (x + bal * 0.3, y - h * 0.5), tete], T.S1, P.ep(0.6))
    for i in range(3):
        P.ell(x + (i - 1) * 2.4, y - 2.0 - i * 1.6, 2.2, 1.5, T.S1 if i % 2 else T.S2)
    teinte = (PECHE, PRUNE, CREME, PJ3)[graine % 4]
    sombre = {PECHE: LA1, PRUNE: T.CIEL[2] if nuit else NU2, CREME: TE3, PJ3: PJ2}[teinte]
    n = int(h / 3.4)
    for i in range(n):
        u = (i + 1.0) / n
        fx_ = x + bal * u ** 2 + (1.6 if i % 2 else -1.6) * (1 - u * 0.6)
        fy_ = y - h * (0.28 + 0.72 * u)
        r = 2.0 * (1 - 0.55 * u)
        P.ell(fx_, fy_, r, r * 0.9, sombre)
        P.ell(fx_ - r * 0.15, fy_ - r * 0.15, r * 0.75, r * 0.65, teinte)
        P.point(fx_, fy_, PJ4 if teinte != PJ3 else BO2)
    P.ell(tete[0], tete[1], 0.8, 1.2, T.S3)


def fond_du_jardin(P, tab, heure):
    T = pg.T
    p = P.p
    X, Y = P.X, P.Y
    nuit, soir, matin = heure == "nuit", heure == "soir", heure == "matin"
    # ---- Le ciel de l'heure.
    tab.plan("ciel", 0.0)
    if matin:
        pg.ciel(P, horizon=40.0, haut=0.0, halo=0.36, disque=4.8)
    elif soir:
        pg.ciel(P, horizon=40.0, haut=0.0, halo=0.4, etoiles=0.12, disque=6.0)
    else:
        pg.ciel(P, horizon=44.0, haut=0.0, halo=0.14, etoiles=0.5, lune=(150.0, -2.0, 4.4), disque=0)
        halo(P, 150.0, -2.0, 20.0, T.CIEL[6], 0.4)
    tab.plan("nuages", 0.08)
    if nuit:
        pg.voiles(P, y=14.0, epais=8.0, seuil=0.6, graine=1210)
        if int(p * 8) in (2, 3):                                # une étoile filante
            P.trait(60.0 + int(p * 8) * 6, -10.0 + int(p * 8), 54.0 + int(p * 8) * 6, -11.4 + int(p * 8), BLANC)
    else:
        pg.cumulus(P, [(40, 6, 46, 8.0, 1211, 9, 0.0), (128, -4, 34, 5.6, 1212, 7, 0.4), (176, 16, 22, 3.6, 1213, 5, 0.7)], dessous=0.7 if soir else -0.5)
        pg.voiles(P, y=-8.0, epais=8.0, seuil=0.6, graine=1214)
        if soir:
            pg.barres(P, [(60, 30.0, 18, 1.2), (140, 26.0, 16, 1.0)])
    # ---- Les lointains : deux crêtes, les deux dents minuscules, et la colline d'en face avec son arbre.
    tab.plan("lointains", 0.2)
    tons_l = [T.L2, T.L3, T.L4, T.L5] if not nuit else [T.CIEL[2], T.CIEL[3], T.CIEL[4], T.CIEL[5]]
    sommets(P, lambda x: dents(x, cx=40.0, k=0.36, base=40.6), tons_l, neige=1.4 if not nuit else 2.4, graine=11)
    pg.crete(P, lambda x: pg.profil(x, 41.0, 6.0, 26.0, 1215), tons_l, 0.5)
    cx_, cy_ = 150.0, 41.0                                      # la colline d'en face (celle du prologue)
    fcol = lambda x: cy_ - 9.0 * np.maximum(0, 1 - ((_a(x) - cx_) / 22.0) ** 2) ** 0.6
    mcol = (Y >= fcol(X)) & (np.abs(X - cx_) < 22.0)
    P.rampe(mcol, 0.5 + 0.4 * (X - cx_) / 22.0 * (1 if P.soleil[0] > cx_ else -1), tons_l[1:] + [tons_l[3]], 0.5)
    P.remplir(P.crete(mcol), T.OR3 if not nuit else T.CIEL[7])
    P.trait(cx_, cy_ - 9.0, cx_, cy_ - 12.0, tons_l[0])
    P.ell(cx_, cy_ - 13.4, 2.2, 1.8, tons_l[0])
    if not nuit:
        pg.oiseaux(P, 96.0, 10.0, 5, coul=T.CIEL[0] if matin else T.CIEL[1])
    # ---- Le plan moyen : la haie ronde, la barrière, les roses trémières, le massif ; la pelouse qui descend.
    tab.plan("moyen", 0.5)
    haie_tons = [T.S0, T.S1, T.S2, T.S3, T.OR1] if not nuit else [ENCRE, NU1, NU2, T.S0, T.S1]
    boules = [(-4 + 13.5 * i + 4 * float(hz(i, 1, 1216)), 40.0 - 3 * float(hz(i, 2, 1216)), 8.0 + 3.0 * float(hz(i, 3, 1216))) for i in range(16)]
    lum = (0.5 if P.soleil[0] > 96 else -0.5, -0.6, 0.35)
    P.volumes(boules, haie_tons, lum, plancher=48.0, grain=1.4, graine=1217, gain=0.55, base=0.42, trame=0.9)
    for i in range(30):                                         # de petites fleurs blanches dans la haie ; un nid
        x, y = 4 + 184 * hz(i, 1, 1218), 34 + 10 * hz(i, 2, 1218)
        if P.a[min(P.H - 1, P.py(y)), min(P.Wt - 1, P.px(x))] >= 0 and hz(i, 3, 1218) < 0.7:
            P.point(x, y, CREME if not nuit else T.CIEL[6])
    f_pre = lambda x: 47.0 + 1.2 * np.sin(_a(x) / 21.0) + 0.5 * np.sin(_a(x) / 6.0)
    pre_tons = [T.S1, T.S2, T.S3, T.S4, PJ3] if matin else ([T.S0, T.S1, T.S2, T.S3, PJ2] if soir else [NU1, NU2, T.S0, T.S1, T.S2])
    pre = Y > f_pre(X)
    tonte = np.floor((X + (Y - 47) * 0.9) / 9.0) % 2                # les bandes de la tondeuse, qui fuient
    v = 0.6 + 0.08 * tonte + 0.24 * (pg.fbm(X / 9.0, Y / 2.0, 3, 1219) - 0.5) - 0.008 * (Y - 47)
    P.rampe(pre, v, pre_tons, 0.6)
    # La barrière de bois, devant la haie : planches inégales, une qui manque, un portillon.
    for i, x in enumerate(np.arange(-6.0, 198.0, 4.6)):
        if i in (9, 27):
            continue
        hh = 11.0 + 1.6 * hz(i, 1, 1220)
        pen = 0.8 if i == 18 else 0.0
        c0, c1 = (TE2, TE3) if not nuit else (NU2, T.CIEL[3])
        P.poly([(x, 49.0), (x + 3.6, 49.0), (x + 3.6 + pen, 49.0 - hh), (x + 1.8 + pen, 49.0 - hh - 1.8), (x + pen, 49.0 - hh)], c0)
        P.poly([(x, 49.0), (x + 0.9, 49.0), (x + 0.9 + pen, 49.0 - hh), (x + pen, 49.0 - hh)], c1)
    P.rect(-6.0, 41.0, 204.0, 1.0, TE1 if not nuit else NU1)
    P.rect(-6.0, 46.0, 204.0, 0.8, TE1 if not nuit else NU1)
    # Les roses trémières contre la barrière ; le petit massif à droite (œillets d'Inde, lavande, un tuteur et sa girouette).
    for i, (x, h) in enumerate(((112.0, 24.0), (120.0, 30.0), (128.0, 22.0), (137.0, 27.0), (146.0, 20.0), (64.0, 18.0), (71.0, 23.0))):
        rose_tremiere(P, x, 50.0, h, i, nuit)
    mx0, mx1 = 152.0, 192.0
    P.ell((mx0 + mx1) / 2, 55.0, (mx1 - mx0) / 2 + 2, 3.4, TE1 if not nuit else NU1)
    for i in range(34):
        x = mx0 + (mx1 - mx0) * hz(i, 1, 1221)
        y = 53.0 + 3.6 * hz(i, 2, 1221)
        hh = 2.0 + 4.0 * hz(i, 3, 1221)
        bal = 0.3 * onde(p, x / 17.0)
        P.trait(x, y, x + bal, y - hh, T.S2 if not nuit else T.S0)
        c0 = (PECHE, PRUNE, CREME, PJ3, LA1)[i % 5]
        P.ell(x + bal, y - hh, 1.0, 0.9, c0 if not nuit else (T.CIEL[5] if i % 2 else PRUNE))
        if not nuit:
            P.point(x + bal, y - hh, PJ4)
    P.trait(172.0, 55.0, 172.0, 40.0, BO2)                        # le tuteur et son moulinet, qui tourne
    for q in range(4):
        a = (p + q) * math.pi / 2
        P.poly([(172.0, 39.6), (172.0 + 3.0 * math.cos(a), 39.6 + 3.0 * math.sin(a)), (172.0 + 2.2 * math.cos(a + 0.7), 39.6 + 2.2 * math.sin(a + 0.7))],
               (LA1, T.BLEU, CREME, PRUNE)[q])
    # Un pommier nain à gauche du pot, ses pommes ; une corde à linge minuscule (une écharpe y sèche).
    pg.arbre_rond(P, 2.0, 52.0, 8.0, 1222, tronc=16.0)
    for i in range(5):
        P.ell(-3.0 + i * 3.0, 26.0 + (i % 2) * 3.4, 0.9, 0.9, LA1)
    P.trait(92.0, 50.0, 92.0, 38.0, BO2)
    P.trait(106.0, 50.0, 106.0, 38.0, BO2)
    P.courbe([(92.0, 38.4), (99.0, 40.4), (106.0, 38.4)], TE3, 1)
    P.poly([(96.0, 39.8), (99.6, 40.2), (100.0 + 0.5 * onde(p), 46.4), (96.2 + 0.5 * onde(p), 46.0)], LA1)
    P.poly([(101.0, 40.0), (103.4, 39.6), (103.8 + 0.4 * onde(p, 0.2), 43.6), (101.2 + 0.4 * onde(p, 0.2), 43.8)], CREME)
    # ---- Le pot-cabane et le chemin de cailloux qui y mène, depuis le premier plan.
    pot_cabane(P, 30.0, 70.0, nuit, soir)
    for i in range(11):
        u = i / 10.0
        x, y = 34.0 + 44.0 * u ** 1.2, 74.6 + 4.6 * u
        r = 1.6 + 1.6 * u
        P.ell(x + 2.4 * math.sin(i * 1.7), y + 0.4, r * 1.1, r * 0.4, T.S0 if not nuit else NU1)
        P.ell(x + 2.4 * math.sin(i * 1.7), y, r, r * 0.42, R3 if not nuit else R2)
        P.ell(x + 2.4 * math.sin(i * 1.7) - r * 0.2, y - r * 0.1, r * 0.6, r * 0.2, R4 if not nuit else R3)
    # Ce qui traîne autour : un arrosoir sur la pelouse, une bêche et un râteau contre la barrière.
    c_fer = R3 if not nuit else R2
    P.ell(74.0, 66.6, 6.0, 1.0, T.S0 if not nuit else NU1)
    P.poly([(69.0, 59.0), (79.0, 59.0), (78.0, 66.4), (70.0, 66.4)], c_fer)
    P.rect(69.0, 59.0, 2.4, 7.4, R4 if not nuit else R3)
    P.poly([(79.0, 61.0), (85.0, 57.6), (85.8, 58.8), (79.0, 63.6)], c_fer)
    P.ell(85.8, 58.0, 1.2, 1.6, R2)
    P.courbe([(70.4, 59.0), (74.0, 54.6), (77.6, 59.0)], R2, P.ep(0.7))
    P.trait(82.0, 50.0, 84.0, 36.0, BO2, P.ep(0.6))               # la bêche
    P.rect(80.8, 46.0, 2.6, 4.4, c_fer)
    P.trait(88.0, 50.0, 86.6, 37.0, BO2, P.ep(0.6))               # le râteau
    P.rect(85.0, 36.4, 3.6, 0.8, R2)
    # ---- La vie de l'heure.
    if matin:
        pg.rai(P, P.soleil[0] - 6, 2.0, 44.0, 16.0, -0.5, T.CIEL[11], 0.22, 26, 1223)
        for i in range(30):                                     # la rosée : des perles qui s'allument dans l'herbe
            if (p + hz(i, 1, 1224)) % 1.0 < 0.4:
                P.point(4 + 184 * hz(i, 2, 1224), 50 + 28 * hz(i, 3, 1224), BLANC)
        pg.papillon_de_nuit(P, 124.0, 28.0, 6.0, coul=CREME)
        pg.papillon_de_nuit(P, 170.0, 48.0, 5.0, coul=PECHE, d=0.5)
        # Un merle sur la barrière, deux moineaux dans l'herbe.
        P.ell(84.0, 36.6, 1.8, 1.2, ENCRE)
        P.ell(85.4, 35.6 - (0.5 if int(p * 8) % 4 == 0 else 0), 0.8, 0.8, ENCRE)
        P.point(86.4, 35.6, PJ3)
        for i in range(2):
            P.ell(140.0 + i * 5.0, 60.6, 1.3, 0.9, TE2)
            P.ell(141.0 + i * 5.0, 59.8 + (0.8 if int(p * 8 + i * 2) % 3 == 0 else 0), 0.7, 0.7, TE1)
        pg.vapeur(P, 100.0, 54.0, coul=T.CIEL[11], h=12.0, n=3)   # la terre fume
    elif soir:
        for i in range(8):                                      # les moucherons dansent dans la lumière rasante
            P.point(110.0 + 6 * math.sin(p * 6.283 + i) + i * 2, 30.0 + 4 * math.cos(p * 6.283 * 2 + i * 1.3), LA3)
        for i in range(3):                                      # des hirondelles rentrent
            t = (p + i / 3.0) % 1.0
            x, y = 190 - 180 * t, 6 + 8 * i + 5 * math.sin(t * 6.283 * 2 + i)
            a = onde(p * 2, 0.3 * i)
            P.trait(x - 2.0, y - 0.9 * a, x, y, ENCRE)
            P.trait(x, y, x + 2.0, y - 0.9 * a, ENCRE)
        for i, (x, y, l) in enumerate(((112.0, 50.0, 14.0), (137.0, 50.0, 16.0), (172.0, 55.0, 12.0))):    # les ombres longues
            voile(P, (np.abs(Y - y - (X - x) * -0.12) < 0.8) & (X < x) & (X > x - l) & (P.a >= 0), T.S0, 0.5)
        pg.papillon_de_nuit(P, 160.0, 46.0, 5.0, coul=CREME, d=0.2)
        # Un hérisson sort de sous la haie.
        hx_ = 176.0 - 6.0 * abs(onde(p * 0.5))
        P.ell(hx_, 62.0, 2.6, 1.6, BO1)
        P.ell(hx_ - 2.4, 62.4, 1.0, 0.8, TE3)
        P.point(hx_ - 3.0, 62.2, ENCRE)
    else:
        pg.lucioles(P, [(64.0, 58.0), (90.0, 50.0), (112.0, 62.0), (130.0, 44.0), (150.0, 60.0), (170.0, 50.0), (186.0, 66.0), (12.0, 58.0),
                        (48.0, 44.0), (100.0, 36.0), (142.0, 30.0), (20.0, 30.0), (76.0, 70.0), (160.0, 72.0)], graine=1225)
        pg.papillon_de_nuit(P, 58.0, 50.0, 6.0, coul=CREME)       # autour de la lanterne du pot
        pg.yeux(P, 84.0, 44.0, coul=LA3, d=0.3)                   # un chat sur la barrière ? deux yeux, en tout cas
        pg.yeux(P, 180.0, 40.0, coul=PJ3, d=0.7, ecart=1.6)       # une chouette dans la haie
        # Un hérisson traverse la pelouse.
        hx_ = 150.0 + 8.0 * onde(p * 0.5)
        P.ell(hx_, 64.0, 2.6, 1.6, NU1)
        P.ell(hx_ + 2.4, 64.4, 1.0, 0.8, T.CIEL[5])
    # ---- Le premier plan : l'herbe la plus proche, quelques fleurs, de grandes feuilles dans les coins.
    tab.plan("premier", 1.0)
    f_sol = lambda x: 77.4 + 0.5 * np.sin(_a(x) / 13.0)
    sol_tons = [T.S0, T.S1, T.S2, T.S3, T.S4] if matin else ([T.N1, T.S0, T.S1, T.S2, T.S3] if soir else [T.N0, T.N1, T.N2, T.S0, T.S1])
    m = Y > f_sol(X)
    P.rampe(m, 0.5 + 0.4 * (pg.fbm(X / 6.0, Y / 2.0, 3, 1226) - 0.5), sol_tons, 0.6)
    for i in range(110):
        x = -6 + 204 * hz(i, 1, 1227)
        if 84 < x < 118 or 140 < x < 178:                        # la place de Pilou et celle du personnage restent rases
            hh = 1.0 + 1.4 * hz(i, 2, 1227)
        else:
            hh = 2.0 + 5.0 * hz(i, 2, 1227) ** 2
        bal = 0.5 * onde(p, x / 37.0) * hh / 5.0
        c0 = sol_tons[1 + int(hz(i, 3, 1227) * 3)] if hz(i, 4, 1227) > 0.12 else (T.OR2 if not nuit else T.S2)
        P.trait(x, 79.6, x + (hz(i, 5, 1227) - 0.5) * 1.6 + bal, 79.6 - hh, c0)
    for i in range(9):
        x = 4 + 22 * i + 6 * hz(i, 1, 1228)
        if 84 < x < 118 or 140 < x < 178:
            continue
        pg.fleur(P, x, 79.4, 2.0 + 1.6 * hz(i, 2, 1228), (CREME, PECHE, PRUNE, PJ3)[i % 4] if not nuit else (T.CIEL[6], PRUNE)[i % 2], PJ4 if not nuit else T.CIEL[8])
    for (x0, cote, g) in ((-6.0, 1, 1229), (198.0, -1, 1230)):
        for i in range(4):
            a = -1.25 + i * 0.3 + 0.03 * onde(p, 0.1 * i)
            l = 16 + 8 * hz(i, 1, g)
            bx_, by_ = x0 + cote * l * math.cos(a) * 0.9, 82.0 + l * math.sin(a)
            P.poly([(x0, 82.0), (x0 + cote * l * 0.5 * math.cos(a) - 2.4, 82.0 + l * 0.5 * math.sin(a) - 1.6), (bx_, by_),
                    (x0 + cote * l * 0.5 * math.cos(a) + 2.4, 82.0 + l * 0.5 * math.sin(a) + 2.4)], sol_tons[0] if i % 2 else sol_tons[1])
            P.trait(x0, 82.0, bx_, by_, sol_tons[2])


@decor("evolution", "fond-du-jardin-matin", soleil=(150.0, 22.0), tons=LAVE, nom="Le fond du jardin, le matin", matiere=True)
def fond_du_jardin_matin(P, tab):
    fond_du_jardin(P, tab, "matin")


@decor("evolution", "fond-du-jardin-soir", soleil=(128.0, 33.0), tons=SOIR, nom="Le fond du jardin, le soir", matiere=True)
def fond_du_jardin_soir(P, tab):
    fond_du_jardin(P, tab, "soir")


@decor("evolution", "fond-du-jardin-nuit", soleil=(150.0, -2.0), tons=NUIT, nom="Le fond du jardin, la nuit", matiere=True)
def fond_du_jardin_nuit(P, tab):
    fond_du_jardin(P, tab, "nuit")
