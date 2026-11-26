"""Visites chez un ami (docs/AMIS.md) : baluchon et valise de voyage, pancarte « parti chez… » qui
remplace Pilou pendant son absence, cœurs d'amitié. Palette bleu / orange / crème : jamais de rouge
ni de vert (le cœur d'amitié est orange, le cœur « reçu » bleu)."""

import math

from toile import Toile, ecrire

ENCRE = "#1c2128"
CREME = "#f6f8fa"
CREME_O = "#c9d1d9"
GRIS = "#768390"
B1, B2, B3, B4 = "#1f4f8a", "#4a8fdc", "#6cb6ff", "#b4dbff"
O1, O2, O3, O4, O5 = "#8a4a1f", "#d9803a", "#f69d50", "#ffc89a", "#ffd8b0"
BR1, BR2, BR3 = "#4a2e17", "#7a4b26", "#a8703f"


def T(w, h):
    return Toile(w, h)


def coeur(t, x, y, c, clair):
    t.motif(x, y, [".oo.oo.", "ooooooo", "ooooooo", ".ooooo.", "..ooo..", "...o..."], {"o": c})
    t.p(x + 1, y + 1, clair)


def baluchon():
    # Bâton sur l'épaule, tenu à la main ; le balluchon (foulard orange à pois crème) pend au bout et
    # se balance au rythme de la marche.
    # Compact : il tient dans les onze pixels à droite du flanc (la grille fait 48 de large).
    images = []
    for k in range(2):
        t = T(14, 25)
        dx = (0, 1)[k]
        t.ligne(1, 24, 6, 9, BR2)
        t.ligne(2, 24, 7, 9, BR3)
        cx, cy = 7 + dx, 7
        t.ell(cx, cy + 1, 4.6, 4.2, O3)
        t.ell(cx + 1, cy + 2, 3.4, 3, O2, cond=lambda x, y, u, v: v > 0.2)
        for (px, py) in ((-2, 0), (1, -1), (2, 2), (-1, 3)):
            t.p(cx + px, cy + py, O5)
        # Nœud au-dessus.
        t.rect(cx - 1, cy - 4, 3, 2, O3)
        t.p(cx - 2, cy - 5, O3)
        t.p(cx + 2, cy - 5, O3)
        t.contour(O1)
        images.append(t)
    ecrire("baluchon", images, slot="main", ancre="main", point=(2, 23), duree=260,
           commentaire="Baluchon de voyage (départ en visite)")


def valise():
    # Petite valise bleue, sangle orange, étiquette crème : au retour de visite.
    t = T(20, 18)
    t.rect(7, 0, 6, 2, ENCRE)
    t.rect(8, 1, 4, 1, None)
    t.rect(1, 3, 18, 13, B2)
    t.rect(1, 3, 18, 2, B3)
    t.rect(1, 14, 18, 2, B1)
    t.rect(8, 3, 3, 13, O3)
    t.rect(8, 3, 1, 13, O4)
    t.rect(13, 7, 4, 3, CREME)
    t.p(13, 8, GRIS)
    t.contour(ENCRE)
    ecrire("valise", t, slot="main", ancre="main", point=(9, 2), commentaire="Valise (retour de visite)")


def pancarte():
    # Pancarte plantée au sol : cadre de bois, papier crème (le texte « chez Léo / 14 h 20 » est écrit
    # par-dessus par l'appli), punaise orange, petite flèche bleue vers le bord de l'écran.
    images = []
    for k in range(2):
        t = T(44, 44)
        t.rect(20, 22, 4, 21, BR2)
        t.rect(20, 22, 1, 21, BR3)
        t.rect(23, 22, 1, 21, BR1)
        t.rect(15, 42, 14, 2, BR1)  # touffe de terre
        t.rect(1, 1, 42, 23, BR2)
        t.rect(1, 1, 42, 1, BR3)
        t.rect(1, 23, 42, 1, BR1)
        t.rect(3, 3, 38, 19, CREME)
        t.rect(3, 20, 38, 2, CREME_O)
        t.rect(21, 1, 2, 2, O3)
        t.p(21, 1, O5)
        # Flèche qui pointe vers la sortie ; elle avance d'un pixel sur la seconde image.
        ax = 31 + k
        t.rect(ax, 25, 8, 2, B2)
        t.motif(ax + 7, 23, ["o..", "oo.", "ooo", "ooo", "oo.", "o.."], {"o": B2})
        t.contour(ENCRE)
        images.append(t)
    ecrire("pancarte", images, slot="objet", ancre="aucun", duree=600,
           commentaire="Pancarte « parti chez… » (Pilou en visite)")


def coeurs_amitie():
    # Cœurs d'amitié qui montent au-dessus de deux Pilou (caresse entre amis, tape m'en cinq).
    images = []
    for k in range(6):
        t = T(40, 34)
        for i, (x, base) in enumerate(((4, 28), (29, 26), (16, 22))):
            ph = (k / 6 + i * 0.33) % 1
            y = int(base - ph * 18)
            c, clair = ((O3, O5), (B3, B4), (O2, O4))[i]
            coeur(t, x + int(math.sin(ph * 6 + i) * 2), y, c, clair)
        images.append(t)
    ecrire("coeurs-amitie", images, slot="effet", ancre="tete", point=(20, 30), duree=160,
           commentaire="Cœurs d'amitié")


def tout():
    baluchon()
    valise()
    pancarte()
    coeurs_amitie()
