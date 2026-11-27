"""Finition fine (2×) de la Chasse aux bugs et de la Défense du bureau (`bug-*`, `defense-*`).

Les bugs gardent leur caractère d'origine (mêmes masses, mêmes couleurs, mêmes pattes, mêmes deux images) : on affine
les yeux (anneau, pupille, reflet), on ajoute carapaces luisantes, segments, soies fines, crocs. Rien n'est redessiné autrement.
"""
import math

from finition import (finition, disque, trait, arc, points, poly, oeil, scintille, eclaircir, assombrir,
                      ENCRE, BLANC, CREME, GRIS, GRIS_C, ARGENT, ARGENT_C, B1, B2, B3, B4, O1, O2, O3, O4, O5, V1, V2, V3, V4)


def efface(t, x, y, w, h, c):
    t.rect(x, y, w, h, c)


@finition("bug-scarabee")
def _scarabee(t, k):
    efface(t, 7, 2, 1, 1, O2)
    efface(t, 10, 2, 1, 1, O2)
    oeil(t, 7.5, 2.4, 0.45, sur={O2, BLANC})
    oeil(t, 10.5, 2.4, 0.45, sur={O2, BLANC})
    # Élytres : arête de la couture, reflets, points d'ombre.
    trait(t, 8, 4.4, 8, 13.5, assombrir(O1, 0.2), None)
    trait(t, 10, 4.4, 10, 13.5, O2, {O3, O1})
    arc(t, 9, 8.5, 5.4, 4.4, 195, 255, O5, {O3})
    arc(t, 9, 8.5, 5.4, 4.4, 20, 90, O2, {O3})
    points(t, [(10, 22), (24, 20), (13, 25)], assombrir(O3, 0.25), {O3})
    # Pattes : articulation plus sombre. Antennes : petite boule.
    disque(t, 5, 0.3, 0.45, 0.45, O1, None)
    disque(t, 12, 0.3, 0.45, 0.45, O1, None)
    # Tête : sillon.
    trait(t, 7, 5.6, 11, 5.6, O1, {O2})


@finition("bug-araignee")
def _araignee(t, k):
    efface(t, 7, 4, 1, 1, B3)
    efface(t, 10, 4, 1, 1, B3)
    for x in (7.5, 10.5):
        oeil(t, x, 4.5, 0.45, sur={B3, BLANC})
    points(t, [(16, 6), (19, 6)], B4)
    # Abdomen : sablier de lumière, dos luisant, soies.
    arc(t, 9, 9, 4.2, 3.7, 200, 260, B4, {B3})
    disque(t, 8.4, 8, 1.7, 1.6, B4, {B3, B4})
    scintille(t, 16, 16, BLANC, 1)
    arc(t, 9, 9, 4.2, 3.7, 25, 95, B2, {B3})
    for i in range(4):
        y = 5 + i * 2
        points(t, [(int(4.2 * 2), int(y * 2) - 1 - (i + k) % 2), (int(13.2 * 2), int(y * 2) - 1 - (i + k) % 2)], B1, None)
    # Crocs.
    points(t, [(17, 11), (20, 11)], B1, {B3})


@finition("bug-ver")
def _ver(t, k):
    G = ARGENT
    for i in range(6, -1, -1):
        x = 3 + i * 2.2
        y = 8 + math.sin(i * 1.1 + k * 1.6) * 2.2
        c = GRIS if i % 2 else G
        arc(t, x, y, 2.6, 2.6, 20, 100, assombrir(c, 0.25), {c})
        arc(t, x, y, 2.4, 2.4, 200, 260, eclaircir(c, 0.5), {c})
    # Tête : œil rond.
    efface(t, 1, 6, 2, 2, G)
    oeil(t, 2, 7, 0.75, fond=BLANC, sur={G, GRIS, BLANC})
    trait(t, 1.2, 8.7, 2.6, 8.9, assombrir(G, 0.4), {G, GRIS})


@finition("bug-prod")
def _prod(t, k):
    # Yeux ronds, regard qui suit l'image.
    efface(t, 6, 9, 5, 4, O3)
    efface(t, 25, 9, 5, 4, O3)
    efface(t, 8 + k, 10, 2, 2, BLANC)
    efface(t, 27 + k, 10, 2, 2, BLANC)
    for cx in (8.5, 27.5):
        disque(t, cx, 11, 3.0, 2.8, BLANC, None)
        disque(t, cx + 0.2 + k * 0.4, 11.2, 1.5, 1.5, ENCRE, None)
        disque(t, cx - 0.4 + k * 0.4, 10.6, 0.5, 0.5, BLANC, None)
        arc(t, cx, 11, 3.0, 2.8, 200, 340, ENCRE, None)
    # Sourcils lourds.
    trait(t, 5.5, 7.6, 11, 8.6, ENCRE, None)
    trait(t, 30.5, 7.6, 25, 8.6, ENCRE, None)
    # Bouche : dents triangulaires.
    efface(t, 11, 15, 14, 2, O3)
    t.rect(11, 15, 14, 2, ENCRE)
    for x in range(12, 25, 3):
        t.poly([(x - 0.2, 15), (x + 1.4, 15), (x + 0.6, 16.6)], BLANC)
    # Reflet du dos, ombre du ventre, taches.
    arc(t, 18, 12, 16.4, 8.4, 200, 300, O5, {O3, O4})
    arc(t, 18, 12, 16.6, 8.6, 20, 100, O2, {O3})
    for (x, y, r) in ((14, 7, 0.7), (22, 6, 0.6), (18, 5, 0.5)):
        disque(t, x, y, r, r * 0.7, O3, {O4})


@finition("defense-blinde", "defense-blinde-fele")
def _blinde(t, k):
    efface(t, 7, 2, 1, 1, V2)
    efface(t, 10, 2, 1, 1, V2)
    for x in (7.5, 10.5):
        oeil(t, x, 2.4, 0.45, sur={V2, BLANC})
    # Plaques d'acier : rivets ronds, arête claire, jonction sombre.
    for X in range(t.W):
        for Y in range(t.H):
            if t.g[Y][X] in (ARGENT, GRIS) and t.getf(X, Y - 1) not in (ARGENT, GRIS) and t.getf(X, Y - 1) is not None:
                t.g[Y][X] = eclaircir(t.g[Y][X], 0.5)
    for x in (5.2, 12.8):
        disque(t, x, 6.9, 0.45, 0.4, ENCRE, {ARGENT, GRIS, BLANC})
        points(t, [(int((x - 0.2) * 2), int(6.7 * 2))], BLANC, {ENCRE})
    arc(t, 9, 8.5, 5.6, 4.6, 195, 250, V4, {V3, V2})
    trait(t, 4.4, 10.6, 13.6, 10.6, V1, {ARGENT, GRIS, V3})


@finition("defense-diviseur")
def _diviseur(t, k):
    ecart = k * 0.5
    for cx in (5 - int(ecart), 12 + int(ecart)):
        efface(t, cx - 1, 5, 2, 2, V2 if cx < 9 else V3)
        oeil(t, cx, 6, 0.8, fond=BLANC, sur={V2, V3, V4, BLANC})
    for y in range(4, 12, 2):
        disque(t, 9.5, y + 0.5, 0.45, 0.45, CREME, None)
    arc(t, 5.5 - ecart, 7.5, 4.6, 4.4, 20, 100, V1, {V2})
    arc(t, 12.5 + ecart, 7.5, 4.6, 4.4, 80, 160, V2, {V3})


@finition("defense-mini")
def _mini(t, k):
    efface(t, 4, 3, 2, 2, V3)
    oeil(t, 5, 4, 0.7, fond=BLANC, sur={V3, V4, BLANC})
    arc(t, 5, 4.5, 3.8, 3.0, 20, 100, V2, {V3})


@finition("defense-rapide")
def _rapide(t, k):
    efface(t, 3, 6, 2, 1, O2)
    oeil(t, 3.6, 6.4, 0.7, fond=BLANC, sur={O2, BLANC})
    for x in (8.5, 11.5):
        trait(t, x, 4.5, x, 9.5, ENCRE, None)
    arc(t, 9.5, 7, 4.8, 2.8, 200, 260, O5, {O3})
    # Ailes : nervures.
    if k == 0:
        trait(t, 7, 2.5, 8, 1, "#ffffff", None)
        trait(t, 10, 3, 11.4, 1.6, "#ffffff", None)
    else:
        trait(t, 6, 4.6, 9, 4.2, "#ffffff", None)
        trait(t, 10, 4.8, 12.6, 4.6, "#ffffff", None)


@finition("defense-tir", auto=False)
def _tir(t, k):
    for r in t.g:
        for X in range(len(r)):
            r[X] = None
    c = 3.5
    if k == 0:
        t.poly([(c, 0), (7, c), (c, 7), (0, c)], V1)
        t.poly([(c, 1), (6, c), (c, 6), (1, c)], V3)
        t.poly([(c, 2), (5, c), (c, 5), (2, c)], V4)
        disque(t, c, c, 1.0, 1.0, BLANC, None)
        trait(t, 1.4, c - 0.4, c - 0.6, 1.4, V4, None)
    else:
        t.poly([(c, 0), (c + 1.1, c - 1.1), (7, c), (c + 1.1, c + 1.1), (c, 7), (c - 1.1, c + 1.1), (0, c), (c - 1.1, c - 1.1)], V1)
        t.poly([(c, 1), (c + 0.8, c - 0.8), (6, c), (c + 0.8, c + 0.8), (c, 6), (c - 0.8, c + 0.8), (1, c), (c - 0.8, c - 0.8)], V3)
        t.poly([(c, 1.9), (c + 0.5, c - 0.5), (5.1, c), (c + 0.5, c + 0.5), (c, 5.1), (c - 0.5, c + 0.5), (1.9, c), (c - 0.5, c - 0.5)], V4)
        disque(t, c, c, 0.9, 0.9, BLANC, None)


@finition("defense-etincelle", auto=False)
def _etincelle(t, k):
    for r in t.g:
        for X in range(len(r)):
            r[X] = None
    # Trait effilé : tête ronde blanche, corps orange clair qui fonce et s'amincit vers la queue.
    t.poly([(1.5, 0), (2.6, 1.6), (3, 3.2), (2.6, 5.5), (1.5, 8.8), (0.4, 5.5), (0, 3.2), (0.4, 1.6)], O2)
    t.poly([(1.5, 0.4), (2.4, 1.8), (2.7, 3.2), (2.3, 5), (1.5, 7.2), (0.7, 5), (0.3, 3.2), (0.6, 1.8)], O3)
    t.poly([(1.5, 0.7), (2.1, 1.8), (2.3, 3.2), (1.9, 4.6), (1.5, 5.6), (1.1, 4.6), (0.7, 3.2), (0.9, 1.8)], O4)
    disque(t, 1.5, 1.4, 0.9, 1.1, BLANC, None)
    points(t, [(3, 14), (3, 15), (3, 16)], O2)


@finition("defense-bonus-double")
def _double(t, k):
    # Capsule : biseau (arête claire en haut, ombre en bas), deux étincelles pointues.
    trait(t, 1.2, 1.2, 10.8, 1.2, BLANC, {O5})
    trait(t, 1.2, 10.8, 10.8, 10.8, O3, {O5})
    for x in (4, 8):
        t.poly([(x, 2.6), (x + 0.8, 3.4), (x + 0.8, 8.6), (x, 9.4), (x - 0.8, 8.6), (x - 0.8, 3.4)], O3)
        t.poly([(x, 2.6), (x + 0.5, 3.2), (x - 0.5, 3.2)], BLANC)
        points(t, [(int((x - 0.2) * 2), 9)], O4, {O3})


@finition("defense-bonus-bouclier")
def _bouclier(t, k):
    arc(t, 6, 6, 4.5, 4.5, 190, 270, BLANC, {B4})
    arc(t, 6, 6, 5.4, 5.4, 20, 110, B2, {B1, B4})
    # Écusson : petite pointe au centre.
    t.poly([(6, 4.6), (7.6, 5.4), (7.2, 7.6), (6, 8.4), (4.8, 7.6), (4.4, 5.4)], B2)
    t.poly([(6, 5.0), (7.2, 5.6), (6.9, 7.3), (6, 7.9), (5.1, 7.3), (4.8, 5.6)], B3)
    trait(t, 6, 5.2, 6, 7.8, B4, None)


@finition("defense-bonus-ralenti", auto=False)
def _ralenti(t, k):
    for r in t.g:
        for X in range(len(r)):
            r[X] = None
    t.poly([(6, -0.5), (12.5, 6), (6, 12.5), (-0.5, 6)], V1)
    t.poly([(6, 0.6), (11.4, 6), (6, 11.4), (0.6, 6)], V4)
    arc(t, 6, 6, 5.0, 5.0, 190, 260, BLANC, {V4})
    # Sablier : verre, deux ampoules, sable qui coule, socles.
    t.poly([(3.2, 3.0), (8.8, 3.0), (6.9, 6), (8.8, 9.0), (3.2, 9.0), (5.1, 6)], V3)
    t.poly([(3.8, 3.5), (8.2, 3.5), (6.5, 6), (8.2, 8.5), (3.8, 8.5), (5.5, 6)], CREME)
    t.poly([(4.4, 7.6), (7.6, 7.6), (8.0, 8.5), (4.0, 8.5)], V2)
    t.poly([(5.1, 3.8), (6.9, 3.8), (6.1, 5.6), (5.9, 5.6)], V2)
    t.rect(3, 2.4, 6, 0.8, V1)
    t.rect(3, 8.9, 6, 0.8, V1)
    trait(t, 6, 6, 6, 7.4, V2, None)
