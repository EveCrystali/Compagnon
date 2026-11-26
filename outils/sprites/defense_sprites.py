"""Défense du bureau (PC) : les bugs en plus de ceux de Chasse aux bugs (bug-scarabee, bug-araignee, bug-ver,
bug-prod, repris tels quels), les tirs et les bonus. Même grille fine (18 × 14 pour un bug), même style :
corps plein, reflet clair, pattes sombres, deux images (pattes ou ailes). Palette orange / bleu / violet /
argent / crème : jamais d'opposition rouge-vert ; chaque chose a aussi sa forme (étincelle de Pilou en trait
vertical, tir des bugs en losange ou en étoile, un contour différent pour chaque bonus)."""

import math

from toile import Toile, ecrire

ENCRE = "#1c2128"
BLANC = "#ffffff"
CREME = "#f6f8fa"
GRIS = "#768390"
ARGENT = "#b8c4d2"
ARGENT_C = "#e6ecf2"
B1, B2, B3, B4 = "#1f4f8a", "#4a8fdc", "#6cb6ff", "#b4dbff"
O1, O2, O3, O4, O5 = "#8a4a1f", "#d9803a", "#f69d50", "#ffc89a", "#ffd8b0"
V1, V2, V3, V4 = "#3a2a7a", "#6a5acd", "#9b8cff", "#d2caff"
AILE = "#b4dbffb0"


def T(w, h):
    return Toile(w, h)


def blinde(fele):
    # Scarabée à carapace de métal : deux coups pour en venir à bout. Fêlé : plaques ternies, fissure, éclat.
    images = []
    for k in range(2):
        t = T(18, 14)
        for i, y in enumerate((6, 9, 12)):
            d = 1 if (i + k) % 2 else 0
            t.ligne(3, y, 0, y + d, V1)
            t.ligne(14, y, 17, y + d, V1)
        t.ligne(7, 2, 5, 0, V1)
        t.ligne(10, 2, 12, 0, V1)
        t.ell(9, 8.5, 6, 5, V2)
        t.ell(9, 8, 5, 4, V3, cond=lambda x, y, u, v: v < 0.2)
        plaque = GRIS if fele else ARGENT
        t.rect(4, 6, 10, 2, plaque)
        t.rect(4, 10, 10, 1, plaque)
        for x in (5, 12):
            t.p(x, 6, BLANC if not fele else ARGENT)
        t.rect(8, 4, 2, 10, V1)
        t.ell(9, 3.5, 3.5, 2.2, V2)
        t.rect(7, 2, 1, 1, BLANC)
        t.rect(10, 2, 1, 1, BLANC)
        if fele:
            for x, y in ((5, 5), (6, 6), (6, 7), (7, 8), (7, 9), (6, 10), (11, 7), (12, 8), (12, 9), (13, 10)):
                t.p(x, y, ENCRE)
            t.p(14, 7, None)
            t.p(14, 8, None)
            t.p(3, 9, None)
        images.append(t)
    ecrire("defense-blinde-fele" if fele else "defense-blinde", images, slot="objet", duree=300,
           commentaire="Défense du bureau : scarabée blindé%s (18 × 14)" % (", fêlé" if fele else ""))


def diviseur():
    # Deux lobes collés, une couture crème au milieu : touché, il se sépare en deux petits bugs.
    images = []
    for k in range(2):
        t = T(18, 14)
        ecart = k * 0.5
        for i in range(3):
            d = (i + k) % 2
            t.ligne(3 + i * 2, 11, 2 + i * 2 - d, 13, V1)
            t.ligne(14 - i * 2, 11, 15 - i * 2 + d, 13, V1)
        t.ell(5.5 - ecart, 7.5, 5, 4.8, V2)
        t.ell(12.5 + ecart, 7.5, 5, 4.8, V3)
        t.ell(4.5 - ecart, 6, 2.5, 2, V3)
        t.ell(11.5 + ecart, 6, 2.5, 2, V4)
        for y in range(4, 12, 2):
            t.p(9, y, CREME)
        for cx in (5 - int(ecart), 12 + int(ecart)):
            t.rect(cx - 1, 5, 2, 2, BLANC)
            t.p(cx, 6, ENCRE)
        t.ligne(4, 3, 2, 0, V1)
        t.ligne(14, 3, 16, 0, V1)
        images.append(t)
    ecrire("defense-diviseur", images, slot="objet", duree=260, commentaire="Défense du bureau : bug qui se divise (18 × 14)")


def mini():
    images = []
    for k in range(2):
        t = T(10, 8)
        for i in range(2):
            d = (i + k) % 2
            t.ligne(2 + i * 2, 6, 1 + i * 2 - d, 7, V1)
            t.ligne(7 - i * 2, 6, 8 - i * 2 + d, 7, V1)
        t.ell(5, 4.5, 4, 3.2, V3)
        t.ell(4, 3.5, 2, 1.5, V4)
        t.rect(4, 3, 2, 2, BLANC)
        t.p(5, 4, ENCRE)
        t.p(2, 0, V1)
        t.p(3, 1, V1)
        t.p(7, 0, V1)
        t.p(6, 1, V1)
        images.append(t)
    ecrire("defense-mini", images, slot="objet", duree=200, commentaire="Défense du bureau : moitié d'un bug divisé (10 × 8)")


def rapide():
    # Moucheron rayé qui pique vers Pilou : ailes qui battent (deux images).
    images = []
    for k in range(2):
        t = T(16, 12)
        if k == 0:
            t.ell(7, 2.5, 3, 2.2, AILE)
            t.ell(10.5, 3, 2.4, 1.8, AILE)
        else:
            t.ell(7.5, 4.5, 4, 1.4, AILE)
            t.ell(11, 4.8, 3, 1.1, AILE)
        t.ell(9.5, 7, 5, 3, O3)
        t.ell(9, 6, 3.5, 1.5, O5)
        t.rect(8, 4, 1, 6, ENCRE)
        t.rect(11, 4, 1, 6, ENCRE)
        t.p(15, 7, O1)
        t.ell(4, 7, 2.6, 2.6, O2)
        t.p(3, 6, BLANC)
        t.p(4, 6, BLANC)
        t.p(3, 7, ENCRE)
        t.ligne(2, 5, 0, 3, O1)
        t.ligne(5, 10, 4, 11, O1)
        t.ligne(9, 10, 9, 11, O1)
        images.append(t)
    ecrire("defense-rapide", images, slot="objet", duree=80, commentaire="Défense du bureau : moucheron rapide (16 × 12)")


def tirs():
    # Tir des bugs : losange violet, puis étoile à quatre branches (il tourne) ; cerné d'encre.
    a = T(7, 7)
    a.motif(0, 0, ["...a...", "..aba..", ".abcba.", "abcdcba", ".abcba.", "..aba..", "...a..."],
            {"a": V1, "b": V3, "c": V4, "d": BLANC})
    b = T(7, 7)
    b.motif(0, 0, ["...a...", "...b...", "..aca..", "abcdcba", "..aca..", "...b...", "...a..."],
            {"a": V1, "b": V3, "c": V4, "d": BLANC})
    ecrire("defense-tir", [a, b], slot="objet", duree=120, commentaire="Défense du bureau : tir des bugs (losange violet)")
    # Étincelle de Pilou : un trait vertical, tête blanche, traîne orange.
    t = T(3, 9)
    t.motif(0, 0, [".w.", "wow", "ooo", "ooo", ".o.", ".O.", ".O.", ".P.", "..."],
            {"w": BLANC, "o": O4, "O": O3, "P": O2})
    ecrire("defense-etincelle", t, slot="objet", commentaire="Défense du bureau : étincelle de Pilou (trait orange)")


def bonus():
    # Tir double : capsule carrée orange, deux étincelles.
    t = T(12, 12)
    t.rect(1, 0, 10, 12, O1)
    t.rect(0, 1, 12, 10, O1)
    t.rect(1, 1, 10, 10, O5)
    for x in (3, 7):
        t.rect(x, 3, 2, 6, O3)
        t.rect(x, 2, 2, 1, BLANC)
    ecrire("defense-bonus-double", t, slot="objet", commentaire="Défense du bureau : bonus tir double (carré orange)")
    # Bouclier : capsule ronde bleue, anneau.
    t = T(12, 12)
    t.ell(6, 6, 6, 6, B1)
    t.ell(6, 6, 5, 5, B4)
    t.anneau(6, 6, 3.6, 3.6, B2, ep=1.3)
    t.p(4, 3, BLANC)
    t.p(3, 4, BLANC)
    ecrire("defense-bonus-bouclier", t, slot="objet", commentaire="Défense du bureau : bonus bouclier (rond bleu)")
    # Ralenti : losange violet, sablier.
    t = T(12, 12)
    t.poly([(6, -0.5), (12.5, 6), (6, 12.5), (-0.5, 6)], V1)
    t.poly([(6, 1), (11, 6), (6, 11), (1, 6)], V4)
    t.motif(3, 3, ["aaaaaa", ".abba.", "..aa..", "..aa..", ".abba.", "aaaaaa"], {"a": V2, "b": CREME})
    ecrire("defense-bonus-ralenti", t, slot="objet", commentaire="Défense du bureau : bonus ralenti (losange violet)")


def tout():
    blinde(False)
    blinde(True)
    diviseur()
    mini()
    rapide()
    tirs()
    bonus()
