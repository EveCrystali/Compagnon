"""Fabrique toute la banque de sprites de Pilou (assets/sprites/*.txt), les teintes, les tenues et les plats.

    python3 outils/sprites/generer.py && python3 outils/sprites/planches.py

Les fichiers .txt produits sont la source lue par le PC et par l'app Android ; ce script n'est qu'un
outil pour les (re)dessiner. Palette : bleus, oranges, argent, violets, jaunes, sables, neutres —
jamais d'opposition rouge / vert (deutéranopie) ; chaque rareté ou état a aussi un signe de forme.
"""
import math
import os
import shutil

import toile
import fins
from toile import Toile, ecrire, SORTIE, TOUS
import visage_sprites
import boutique_sprites
import meteo_sprites
import visites_sprites
import gestes_sprites
import saynetes_sprites
import expedition_sprites
import defense_sprites
import garde_robe
import voyage_sprites
import decors_campagnes
import campagnes_sprites
import portraits_campagnes
import scene_pilou
import acteurs_scenes
import traits_sprites

# ---- Couleurs
ENCRE = "#1c2128"
NOIR2 = "#2d333b"
BLANC = "#ffffff"
CREME = "#f6f8fa"
CREME_O = "#c9d1d9"
GRIS = "#768390"
GRIS_C = "#adbac7"
ARDOISE = "#3b4654"
ARGENT = "#b8c4d2"
ARGENT_C = "#e6ecf2"
B1, B2, B3, B4 = "#1f4f8a", "#4a8fdc", "#6cb6ff", "#b4dbff"
NUIT = "#0d2a4d"
O1, O2, O3, O4, O5 = "#8a4a1f", "#d9803a", "#f69d50", "#ffc89a", "#ffd8b0"
J1, J2, J3, J4 = "#7a5a10", "#c9a227", "#f5d76e", "#fff6cc"
V1, V2, V3, V4 = "#3a2a7a", "#6a5acd", "#9b8cff", "#d2caff"
S1, S2, S3 = "#8a6e4b", "#c4a77d", "#e8d5b0"
BR1, BR2, BR3 = "#4a2e17", "#7a4b26", "#a86f3c"
T1, T2, T3 = "#0f4a63", "#2689b8", "#3fb8e0"  # sarcelle (feuillages, sans vert)
BOUCHE = "#3a2a2f"
LANGUE = O3


def T(w, h):
    return Toile(w, h)


# =====================================================================================================
# Visage : yeux (œil gauche ; le droit est son miroir) et bouches
# =====================================================================================================
def visage():
    if toile.fin():
        # Dessin fin : tout le visage est redessiné en pixels fins (visage_sprites.py).
        visage_sprites.fins()
        return
    visage_sprites.humeurs()
    pal = {"k": ENCRE, "w": BLANC, "o": "@ombre", "c": "@contour"}
    yeux = {
        "ouvert": [".kkkk.", "kwwkkk", "kwwkkk", "kkkkkk", "kkkkwk", "kkkkkk", ".kkkk."],
        "cligne": ["......", "......", "......", "k....k", ".kkkk.", "......", "......"],
        "dort": ["......", "......", "......", "......", "kk..kk", "..kk..", "......"],
        "fatigue": [".oooo.", "oooooo", "cccccc", "kwwkkk", "kkkkkk", "kkkkkk", ".kkkk."],
        "concentre": ["......", "oooooo", "cccccc", "kwwkkk", "kkkkkk", ".kkkk.", "......"],
        "haut": [".kkkk.", "kkwwkk", "kkwwkk", "kkkkkk", ".kkkk.", "......", "......"],
        "grimace": ["kk....", ".kkk..", "...kkk", "....kk", "...kkk", ".kkk..", "kk...."],
        "heureux": ["......", "..kk..", ".kkkk.", "kk..kk", "k....k", "......", "......"],
        "content": ["......", "......", "k....k", "kk..kk", ".kkkk.", "..kk..", "......"],
        "inquiet": [".kkkk.", "kwwwwk", "kwkkwk", "kwkkwk", "kwwwwk", ".kkkk.", "......"],
        "spirale": ["kkkkk.", "k...k.", "k.k.k.", "k.kkk.", "k.....", "kkkkkk", "......"],
        # Il boude : sourcil froncé (bas côté nez), paupière lourde, regard en coin.
        "boude": ["kk....", ".kkk..", "...kkk", "oooooo", "cccccc", "kkwwkk", ".kkkk."],
    }
    for nom, lignes in yeux.items():
        t = T(6, 7)
        t.motif(0, 0, lignes, pal)
        ecrire("oeil-" + nom, t, slot="visage", commentaire="œil gauche (le droit est son miroir), 6 × 7")

    t = T(8, 9)
    t.motif(0, 0, ["..kkkk..", ".kwwkkk.", "kwwwkkkk", "kwwkkkkk", "kkkkkkkk", "kkkkkkwk", "kkkkkwwk", ".kkkkkk.", "..kkkk.."], pal)
    ecrire("oeil-ouvert-g", t, slot="visage", commentaire="œil immense de la Gouttelette (stade 1)")
    t = T(6, 7)
    t.motif(0, 0, ["......", "......", "cccccc", "kkkkkk", "kwwkkk", ".kkkk.", "......"], pal)
    ecrire("oeil-serein", t, slot="visage", commentaire="regard serein de Pilou Astral (stade 4)")

    palb = {"k": ENCRE, "m": BOUCHE, "t": LANGUE, "w": BLANC}
    bouches = {
        "repos": ["k......k", ".k....k.", "..kkkk.."],
        "soulage": ["k....k", ".kkkk."],
        "concentre": ["kkkk"],
        "attente": [".kk.", "k..k", ".kk."],
        "dort": [".kk.", "k..k", ".kk."],
        "grimace": ["k.k.k.k.k.", ".k.k.k.k.k"],
        "fete": ["kkkkkkkk", "kmmmmmmk", "kmttttmk", ".kttttk.", "..kkkk.."],
        "inquiet": ["..kkkk..", ".k....k.", "k......k"],
        "caresse": ["k..kk..k", ".kk..kk."],
        "baille": [".kkkk.", "kmmmmk", "kmmmmk", "kmttmk", "kttttk", ".kkkk."],
        "boude": ["..kk..", ".k..k.", "k....k"],
    }
    for nom, lignes in bouches.items():
        t = T(len(lignes[0]), len(lignes))
        t.motif(0, 0, lignes, palb)
        ecrire("bouche-" + nom, t, slot="visage", commentaire="bouche, centrée sur l'axe de Pilou")


# =====================================================================================================
# Étincelle au bout de l'antenne (8 × 8, posée sur l'ancre « antenne » : bas au centre)
# =====================================================================================================
def etincelles():
    pal = {"o": O3, "l": O5, "w": BLANC, "g": GRIS}
    point = (4, 8)
    motifs = {
        "grand": ["...oo...", "...oo...", "..olloo.", "oolwwloo", "oolwwloo", ".ooll o.".replace(" ", "o"), "...oo...", "...oo..."],
        "petit": ["........", ".l....l.", "..l..l..", "...oo...", "...oo...", "..l..l..", ".l....l.", "........"],
        "x": [".o....o.", "..o..o..", "...oo...", "...oo...", "..o..o..", ".o....o.", "........", "........"],
        "dort": ["........", "........", "........", "........", "........", "...gg...", "...gg...", "........"],
        "coeur": [".oo..oo.", "olloooo o".replace(" ", ""), "oloooooo", "oooooooo", ".oooooo.", "..oooo..", "...oo...", "........"],
    }
    for nom, lignes in motifs.items():
        t = T(8, 8)
        t.motif(0, 0, [l[:8].ljust(8, ".") for l in lignes], pal)
        ecrire("etincelle-" + nom, t, slot="effet", ancre="antenne", point=point)
    # Alerte « ! » qui clignote.
    a = T(8, 8)
    a.motif(0, 0, ["...oo...", "...oo...", "...oo...", "...oo...", "........", "...oo...", "...oo...", "........"], pal)
    ecrire("etincelle-alerte", [a, T(8, 8)], slot="effet", ancre="antenne", point=point, duree=300)
    # Roue : huit points sur un anneau, deux lumineux qui tournent.
    pos = [(3, 0), (5, 1), (6, 3), (5, 5), (3, 6), (1, 5), (0, 3), (1, 1)]
    images = []
    for k in range(8):
        t = T(8, 8)
        for i, (x, y) in enumerate(pos):
            c = O3 if i in (k, (k + 7) % 8) else O5
            t.rect(x, y, 2, 2, c)
        images.append(t)
    ecrire("etincelle-roue", images, slot="effet", ancre="antenne", point=point, duree=90)


# =====================================================================================================
# Accessoires (récompenses de niveau)
# =====================================================================================================
def accessoires():
    # Feuille d'automne, piquée de travers à gauche de l'antenne.
    t = T(12, 12)
    t.poly([(1, 11), (3, 5), (8, 1), (11, 0), (10, 4), (7, 9)], O2)
    t.poly([(2, 10), (4, 5), (8, 2), (10, 1), (9, 4), (6, 8)], O3)
    t.ligne(1, 11, 9, 2, O1)
    t.ligne(5, 6, 4, 4, O1)
    t.ligne(7, 5, 8, 7, O1)
    t.contour(O1)
    t, _, _ = t.rogner()
    ecrire("acc-feuille", t, slot="tete", ancre="tete", point=(t.w + 2, t.h - 2))

    # Nœud papillon orange, sous la bouche.
    t = T(14, 7)
    t.poly([(0, 0), (6, 2.5), (6, 4.5), (0, 7)], O3)
    t.poly([(14, 0), (8, 2.5), (8, 4.5), (14, 7)], O3)
    t.rect(5, 2, 4, 3, O2)
    t.ligne(1, 2, 4, 3, O4)
    t.ligne(13, 2, 10, 3, O4)
    t.contour(O1)
    ecrire("acc-noeud", t, slot="cou", ancre="cou", point=(8, 2))

    # Casque audio : arceau gris par-dessus la tête, écouteurs orange.
    ecrire("acc-casque", casque(GRIS, GRIS_C, O3, O2, O5), slot="tete", ancre="tete", point=(19, 3))

    # Bonnet de laine à revers et pompon.
    t = T(34, 18)
    t.ell(17, 15, 15, 12, O3, cond=lambda x, y, u, v: v < 0.0)
    for x in range(t.w):
        for y in range(t.h):
            if t.get(x, y) == O3 and x % 3 == 0:
                t.p(x, y, O2)
    t.rect(2, 13, 30, 4, CREME)
    for x in range(2, 32, 3):
        t.rect(x, 13, 1, 4, CREME_O)
    t.ell(17, 3, 3.5, 3.5, CREME)
    t.p(16, 1, BLANC)
    t.p(15, 2, BLANC)
    t.contour(O1)
    ecrire("acc-bonnet", t, slot="tete", ancre="tete", point=(17, 14), coiffe=True)

    # Lunettes de soleil : deux verres sombres, un reflet chacun.
    ecrire("acc-lunettes", lunettes(ENCRE, NOIR2, B4, rond=False, verre=True), slot="yeux", ancre="yeux", point=(13, 1))

    # Couronne dorée à trois pointes, pierres bleues.
    t = T(18, 10)
    t.poly([(0, 10), (0, 2), (4, 6), (9, 0), (14, 6), (18, 2), (18, 10)], J3)
    t.rect(0, 7, 18, 3, J2)
    t.rect(4, 8, 2, 1, B3)
    t.rect(8, 8, 2, 1, B4)
    t.rect(12, 8, 2, 1, B3)
    t.p(9, 1, J4)
    t.contour(J1)
    ecrire("acc-couronne", t, slot="tete", ancre="tete", point=(10, 10), coiffe=True)

    # Chapeau de pêcheur (bob) : bord large, calotte grise, mouche orange.
    t = T(34, 12)
    t.ell(17, 11, 11, 9, GRIS_C, cond=lambda x, y, u, v: v < 0.1)
    for x in range(t.w):
        for y in range(t.h):
            if t.get(x, y) == GRIS_C and (x + y) % 4 == 0:
                t.p(x, y, ARGENT)
    t.rect(6, 7, 22, 2, GRIS)
    t.poly([(1, 9), (33, 9), (31, 12), (3, 12)], GRIS_C)
    t.rect(2, 11, 30, 1, GRIS)
    t.rect(21, 3, 2, 2, O3)
    t.p(23, 2, O5)
    t.p(20, 2, B3)
    t.contour(ARDOISE)
    ecrire("acc-chapeaupeche", t, slot="tete", ancre="tete", point=(18, 11), coiffe=True)

    # Toque de chef, bouffante.
    ecrire("acc-toque", toque(), slot="tete", ancre="tete", point=(12, 17), coiffe=True)

    # Tablier crème, poche orange.
    t = T(20, 18)
    t.poly([(3, 0), (17, 0), (19, 17), (1, 17)], CREME)
    t.rect(3, 0, 14, 2, CREME_O)
    t.rect(6, 7, 8, 5, O3)
    t.rect(6, 7, 8, 1, O2)
    t.ligne(10, 8, 10, 11, O2)
    t.contour(GRIS)
    t.ligne(2, -1, 0, -3, GRIS)
    ecrire("acc-tablier", t, slot="cou", ancre="cou", point=(10, 4))

    # Étoile de mer posée sur le côté de la tête.
    ecrire("acc-etoilemer", etoile_mer(), slot="tete", ancre="tete", point=(-6, 4))


def casque(arc, arc_c, coque, coque_o, eclat):
    t = T(40, 18)
    for a in range(0, 181, 2):
        r = math.radians(180 + a)
        x, y = 19.5 + math.cos(r) * 17.5, 16 + math.sin(r) * 14.5
        t.rect(int(x), int(y), 2, 2, arc_c if a < 60 else arc)
    for x0 in (0, 35):
        t.rect(x0, 9, 5, 9, coque)
        t.rect(x0 + (3 if x0 == 0 else 0), 9, 2, 9, coque_o)
        t.p(x0 + 1, 10, eclat)
    t.contour(ENCRE)
    return t


def lunettes(cadre, verre_c, reflet, rond=False, verre=True, largeur=10):
    t = T(28, 9)
    for x0 in (0, 16):
        if rond:
            t.ell(x0 + 6, 4.5, 6, 4.5, cadre)
            if verre:
                t.ell(x0 + 6, 4.5, 4.8, 3.4, verre_c)
            else:
                t.ell(x0 + 6, 4.5, 4.8, 3.4, None)
        else:
            t.rect(x0, 1, 12, 7, cadre)
            t.rect(x0 + 1, 2, 10, 5, verre_c)
            t.p(x0, 1, None)
            t.p(x0 + 11, 1, None)
        if reflet:
            t.rect(x0 + 2, 2 if not rond else 3, 2, 1, reflet)
            t.p(x0 + 2, 3 if not rond else 4, reflet)
    t.rect(12, 2, 4, 2, cadre)
    return t


def toque():
    t = T(24, 18)
    for cx, cy, r in ((6, 6, 5.5), (12, 4.5, 6), (18, 6, 5.5), (9, 9, 5), (15, 9, 5)):
        t.ell(cx, cy, r, r, BLANC)
    t.rect(4, 10, 16, 6, BLANC)
    t.rect(4, 13, 16, 4, CREME)
    t.rect(4, 13, 16, 1, CREME_O)
    t.p(9, 4, CREME_O)
    t.p(15, 5, CREME_O)
    t.p(12, 8, CREME_O)
    t.contour(GRIS)
    return t


def etoile_mer():
    t = T(13, 13)
    pts = []
    for k in range(10):
        a = math.radians(-90 + k * 36)
        r = 6.3 if k % 2 == 0 else 2.6
        pts.append((6.5 + math.cos(a) * r, 6.8 + math.sin(a) * r))
    t.poly(pts, O3)
    for (x, y) in [(6, 4), (4, 7), (8, 7), (6, 9), (3, 5), (9, 5)]:
        t.p(x, y, O5)
    t.contour(O1)
    return t


# =====================================================================================================
# Tenues d'activité
# =====================================================================================================
def tenues():
    # code : lunettes de geek épaisses (scotch au milieu) + mini-clavier devant les pieds.
    t = T(30, 10)
    for x0 in (0, 17):
        t.rect(x0, 0, 13, 10, ENCRE)
        t.rect(x0 + 2, 2, 9, 6, None)
        t.rect(x0 + 2, 2, 2, 1, B4)
        t.p(x0 + 2, 3, B4)
    t.rect(13, 3, 4, 3, ENCRE)
    t.rect(14, 2, 2, 5, CREME)
    t.p(14, 4, CREME_O)
    ecrire("tenue-code-lunettes", t, slot="yeux", ancre="yeux", point=(15, 2))
    images = []
    for k in range(3):
        t = T(30, 8)
        t.poly([(2, 0), (28, 0), (30, 8), (0, 8)], ARDOISE)
        t.rect(1, 7, 28, 1, ENCRE)
        for r, (x0, n) in enumerate(((4, 11), (3, 12), (5, 10))):
            for i in range(n):
                xx = x0 + i * 2
                lit = (i * 7 + r * 3 + k * 5) % 11 == 0
                t.rect(xx, 1 + r * 2, 1, 1, O3 if lit else GRIS_C)
        t.rect(10, 6, 10, 1, GRIS_C)
        t.contour(ENCRE)
        images.append(t)
    ecrire("tenue-code-clavier", images, slot="objet", ancre="pieds", point=(16, 4), duree=140)

    # tableur : lunettes demi-lune dorées + calculatrice.
    t = T(28, 6)
    for x0 in (0, 16):
        t.ell(x0 + 6, 0, 6, 5.5, J2, cond=lambda x, y, u, v: v > 0)
        t.ell(x0 + 6, 0, 4.8, 4.3, None, cond=lambda x, y, u, v: v > 0)
        t.rect(x0 + 1, 0, 10, 1, J2)
        t.rect(x0 + 2, 1, 8, 3, "#ffffff40") if False else None
    t.rect(12, 0, 4, 1, J2)
    t.rect(3, 2, 2, 1, J4)
    t.rect(19, 2, 2, 1, J4)
    ecrire("tenue-tableur-lunettes", t, slot="yeux", ancre="yeux", point=(14, -3))
    images = []
    for k in range(3):
        t = T(12, 16)
        t.rect(0, 0, 12, 16, ARDOISE)
        t.rect(1, 1, 10, 4, "#c8e1c8" if False else B4)
        chiffres = ["  3,14", "42,00", " 1337"][k]
        t.rect(2, 3, 8, 1, B1)
        t.rect(2, 2, 2 + k * 2, 1, B1)
        for r in range(3):
            for c in range(3):
                t.rect(1 + c * 3 + 1, 6 + r * 3, 2, 2, CREME if (r, c) != (2, 2) else O3)
        t.rect(10, 6, 1, 8, O2)
        t.contour(ENCRE)
        images.append(t)
    ecrire("tenue-tableur-calculatrice", images, slot="main", ancre="main", point=(2, 6), duree=700)

    # jeu-mmo : petite épée et bouclier rond.
    t = T(9, 22)
    t.rect(3, 0, 3, 13, ARGENT_C)
    t.rect(5, 1, 1, 12, ARGENT)
    t.p(4, 0, BLANC)
    t.rect(0, 13, 9, 2, J2)
    t.rect(0, 13, 9, 1, J3)
    t.rect(3, 15, 3, 5, BR2)
    t.rect(3, 20, 3, 2, J2)
    t.contour(ENCRE)
    ecrire("tenue-mmo-epee", t, slot="main", ancre="main", point=(3, 16))
    t = T(16, 16)
    t.ell(8, 8, 8, 8, BR2)
    t.ell(8, 8, 6.5, 6.5, B2)
    t.ell(8, 8, 6.5, 6.5, B3, cond=lambda x, y, u, v: u + v < -0.3)
    t.rect(7, 2, 2, 12, J2)
    t.rect(2, 7, 12, 2, J2)
    t.ell(8, 8, 2, 2, J3)
    t.contour(ENCRE)
    ecrire("tenue-mmo-bouclier", t, slot="main", ancre="main-g", point=(11, 6))

    # jeu : casque gamer (micro) + manette tenue devant.
    t = casque(ENCRE, NOIR2, V2, V1, V4)
    t.ligne(4, 17, 9, 21, GRIS) if False else None
    big = T(40, 24)
    big.coller(t, 0, 0)
    big.ligne(3, 18, 10, 22, GRIS)
    big.rect(10, 21, 3, 3, ENCRE)
    big.p(11, 22, O3)
    ecrire("tenue-jeu-casque", big, slot="tete", ancre="tete", point=(19, 3))
    t = T(20, 10)
    t.ell(4, 5, 4, 5, NOIR2)
    t.ell(16, 5, 4, 5, NOIR2)
    t.rect(4, 1, 12, 6, NOIR2)
    t.rect(3, 4, 3, 1, GRIS_C)
    t.rect(4, 3, 1, 3, GRIS_C)
    t.p(15, 3, B3)
    t.p(17, 4, O3)
    t.p(15, 5, V3)
    t.p(13, 4, J3)
    t.rect(8, 3, 1, 1, GRIS)
    t.rect(11, 3, 1, 1, GRIS)
    t.contour(ENCRE)
    ecrire("tenue-jeu-manette", t, slot="main", ancre="corps", point=(10, -4))

    # musique : gros écouteurs bleus + notes qui montent.
    ecrire("tenue-musique-ecouteurs", casque(B1, B2, B3, B2, B4), slot="tete", ancre="tete", point=(19, 3))
    images = []
    for k in range(6):
        t = T(48, 34)
        for i, (x, base) in enumerate(((2, 30), (40, 26), (8, 18), (36, 12))):
            ph = (k / 6 + i * 0.27) % 1
            y = int(base - ph * 12)
            note(t, x + int(math.sin(ph * 6) * 2), y, [O3, B3, V3, J3][i])
        images.append(t)
    ecrire("tenue-musique-notes", images, slot="effet", ancre="corps", point=(24, 30), duree=180)

    # video : cornet de pop-corn rayé.
    t = T(14, 16)
    t.poly([(1, 5), (13, 5), (11, 16), (3, 16)], CREME)
    for x in range(1, 14, 4):
        t.poly([(x, 5), (x + 2, 5), (x + 1.4, 16), (x + 0.4, 16)], O3)
    for cx, cy in ((3, 4), (6, 2.5), (9, 3), (11.5, 4.5), (5, 5), (8, 5.5), (7, 1)):
        t.ell(cx, cy, 2, 2, J4)
    t.p(6, 2, J3)
    t.p(9, 3, J3)
    t.contour(O1)
    ecrire("tenue-video-popcorn", t, slot="main", ancre="main", point=(4, 9))

    # lecture : lunettes rondes fines + livre ouvert tenu devant.
    ecrire("tenue-lecture-lunettes", lunettes(J1, None, B4, rond=True, verre=False), slot="yeux", ancre="yeux", point=(14, 1))
    t = T(26, 12)
    t.poly([(0, 2), (12, 0), (13, 1), (14, 0), (26, 2), (26, 12), (14, 10), (13, 11), (12, 10), (0, 12)], B2)
    t.poly([(1, 2), (12, 1), (12, 10), (1, 11)], CREME)
    t.poly([(14, 1), (25, 2), (25, 11), (14, 10)], BLANC)
    for y in range(3, 10, 2):
        t.ligne(3, y, 10, y - 1, GRIS_C)
        t.ligne(16, y - 1, 23, y, GRIS_C)
    t.contour(B1)
    ecrire("tenue-lecture-livre", t, slot="main", ancre="corps", point=(13, -5))

    # dessin : béret + palette et pinceau.
    t = T(30, 10)
    t.ell(14, 7, 14, 6, V2, cond=lambda x, y, u, v: v < 0.45)
    t.ell(10, 5, 7, 3, V3, cond=lambda x, y, u, v: v < 0)
    t.rect(13, 0, 2, 2, V1)
    t.contour(V1)
    ecrire("tenue-dessin-beret", t, slot="tete", ancre="tete", point=(13, 6), coiffe=True)
    t = T(20, 16)
    t.ell(9, 9, 9, 7, S3)
    t.ell(13, 12, 2, 1.6, None)
    for (x, y, c) in ((4, 7, B3), (7, 5, O3), (11, 5, J3), (5, 11, V3), (14, 8, CREME)):
        t.rect(x, y, 2, 2, c)
    t.contour(S1)
    t.ligne(15, 0, 19, 8, BR2)
    t.rect(14, 0, 2, 2, O3)
    ecrire("tenue-dessin-palette", t, slot="main", ancre="main", point=(4, 8))

    # visio : micro-casque (un écouteur, une perche).
    t = T(40, 24)
    for a in range(0, 181, 2):
        r = math.radians(180 + a)
        x, y = 19.5 + math.cos(r) * 17.5, 16 + math.sin(r) * 14.5
        t.rect(int(x), int(y), 2, 1, GRIS)
    t.rect(35, 10, 5, 7, ARDOISE)
    t.p(36, 11, GRIS_C)
    t.ligne(36, 17, 27, 22, GRIS)
    t.rect(25, 21, 3, 3, ENCRE)
    t.p(26, 22, O3)
    t.contour(ENCRE)
    ecrire("tenue-visio-micro", t, slot="tete", ancre="tete", point=(19, 3))

    # nuit : bonnet de nuit rayé qui retombe, pompon.
    t = T(36, 18)
    t.poly([(2, 17), (8, 7), (18, 3), (28, 5), (33, 10), (35, 14), (31, 12), (28, 17)], B4)
    for x in range(t.w):
        for y in range(t.h):
            if t.get(x, y) == B4 and (x - y) % 6 < 2:
                t.p(x, y, B3)
    t.rect(2, 15, 27, 3, CREME)
    t.ell(33.5, 14.5, 2.5, 2.5, CREME)
    t.contour(B1)
    ecrire("tenue-nuit-bonnet", t, slot="tete", ancre="tete", point=(15, 14), coiffe=True)

    # mail : casquette de facteur, enveloppe.
    t = T(30, 13)
    t.ell(14, 10, 12, 9, NUIT, cond=lambda x, y, u, v: v < 0)
    t.rect(2, 8, 24, 3, B1)
    t.poly([(10, 10), (30, 10), (27, 13), (12, 13)], ENCRE)
    t.ell(14, 5, 2.5, 2.5, J3)
    t.p(14, 5, J1)
    t.contour(ENCRE)
    ecrire("tenue-mail-casquette", t, slot="tete", ancre="tete", point=(14, 10), coiffe=True)
    t = T(16, 11)
    t.rect(0, 0, 16, 11, CREME)
    t.ligne(0, 0, 8, 6, CREME_O)
    t.ligne(15, 0, 8, 6, CREME_O)
    t.ell(8, 6.5, 2, 2, O3)
    t.p(8, 6, O5)
    t.contour(GRIS)
    ecrire("tenue-mail-enveloppe", t, slot="main", ancre="main", point=(3, 5))

    # texte : plume piquée sur le côté.
    t = T(10, 18)
    t.poly([(8, 0), (10, 2), (5, 14), (3, 13)], CREME)
    t.poly([(8, 0), (9, 1), (5, 12), (4, 12)], BLANC)
    for y in range(3, 13, 2):
        t.p(4 + (13 - y) // 3, y, CREME_O)
    t.ligne(4, 13, 1, 17, BR2)
    t.contour(GRIS)
    ecrire("tenue-texte-plume", t, slot="tete", ancre="tete", point=(-8, 10))

    # diaporama : télécommande et point laser qui se promène.
    images = []
    for k in range(4):
        t = T(14, 20)
        t.rect(0, 9, 5, 11, ARDOISE)
        t.rect(1, 10, 3, 2, GRIS_C)
        t.p(2, 13, O3)
        t.p(2, 15, B3)
        t.contour(ENCRE)
        lx, ly = [(8, 2), (11, 5), (10, 0), (7, 4)][k]
        t.rect(lx, ly, 2, 2, O3)
        t.p(lx - 1, ly, O5)
        t.p(lx + 2, ly + 1, O5)
        images.append(t)
    ecrire("tenue-diaporama-pointeur", images, slot="main", ancre="main", point=(1, 12), duree=260)


def note(t, x, y, c):
    if toile.fin() and fins.ACTIF:
        fins.note_fin(t, x, y, c)
        return
    t.rect(x, y + 3, 3, 2, c)
    t.rect(x + 2, y - 2, 1, 5, c)
    t.rect(x + 3, y - 2, 2, 1, c)
    t.p(x + 4, y - 1, c)


# =====================================================================================================
# Boutique (objets cosmétiques)
# =====================================================================================================
def boutique():
    # Tête
    t = T(36, 14)
    t.poly([(0, 13), (5, 4), (12, 7), (18, 0), (24, 7), (31, 4), (36, 13)], NOIR2)
    t.poly([(5, 6), (12, 8), (18, 2), (17, 9), (6, 11)], ARDOISE)
    t.rect(2, 11, 32, 3, ENCRE)
    t.rect(2, 11, 32, 1, J2)
    t.ell(18, 7.5, 2.5, 2.5, CREME)
    t.rect(17, 8, 1, 1, ENCRE)
    t.rect(19, 8, 1, 1, ENCRE)
    t.ligne(14, 10, 22, 6, CREME)
    t.ligne(14, 6, 22, 10, CREME)
    t.ell(18, 7.5, 2.5, 2.5, CREME)
    t.contour(GRIS)
    ecrire("chapeau-pirate", t, slot="tete", ancre="tete", point=(18, 10), coiffe=True)

    t = T(28, 20)
    t.rect(5, 0, 18, 16, NOIR2)
    t.rect(7, 1, 2, 13, ARDOISE)
    t.rect(5, 11, 18, 3, O3)
    t.rect(5, 11, 18, 1, O5)
    t.rect(0, 16, 28, 3, NOIR2)
    t.rect(1, 16, 26, 1, ARDOISE)
    t.contour(GRIS)
    ecrire("haut-de-forme", t, slot="tete", ancre="tete", point=(14, 16), coiffe=True)

    t = T(36, 12)
    t.ell(15, 11, 12, 10, B3, cond=lambda x, y, u, v: v < 0)
    t.ell(15, 11, 12, 10, B2, cond=lambda x, y, u, v: v < 0 and u > 0.35)
    t.rect(14, 1, 2, 1, B1)
    t.poly([(22, 8), (35, 8), (34, 11), (22, 11)], B1)
    t.rect(8, 4, 5, 3, CREME)
    t.contour(ENCRE)
    ecrire("casquette", t, slot="tete", ancre="tete", point=(15, 8), coiffe=True)

    images = []
    for k in range(4):
        t = T(46, 10)
        t.rect(6, 0, 32, 5, NOIR2)
        t.rect(6, 1, 32, 1, ARDOISE)
        t.rect(20, 0, 5, 5, ARGENT)
        t.rect(21, 1, 3, 3, ARGENT_C)
        w = [0, 1, 2, 1][k]
        t.poly([(38, 1), (45, 2 + w), (44, 4 + w), (38, 4)], NOIR2)
        t.poly([(38, 3), (44, 6 + w), (42, 8 + w), (38, 5)], ARDOISE)
        t.contour(ENCRE)
        images.append(t)
    ecrire("bandeau-ninja", images, slot="tete", ancre="tete", point=(22, -2), duree=200)

    t = T(44, 20)
    t.ell(22, 19, 13, 12, ARGENT, cond=lambda x, y, u, v: v < 0)
    t.ell(22, 19, 13, 12, ARGENT_C, cond=lambda x, y, u, v: v < -0.4 and u < -0.1)
    t.rect(9, 15, 26, 4, J2)
    for x in range(11, 34, 5):
        t.p(x, 16, J4)
    t.rect(21, 7, 2, 9, GRIS)
    t.poly([(10, 15), (4, 12), (1, 5), (2, 0), (5, 6), (9, 10)], CREME)
    t.poly([(34, 15), (40, 12), (43, 5), (42, 0), (39, 6), (35, 10)], CREME)
    t.poly([(4, 12), (1, 5), (2, 0), (3, 7)], CREME_O)
    t.poly([(40, 12), (43, 5), (42, 0), (41, 7)], CREME_O)
    t.contour(ARDOISE)
    ecrire("cornes-viking", t, slot="tete", ancre="tete", point=(22, 17), coiffe=True)

    images = []
    for k in range(4):
        t = T(24, 7)
        t.anneau(12, 3.5, 12, 3.5, J3, ep=2.2)
        t.anneau(12, 3.5, 12, 3.5, J2, ep=1)
        for i in range(4):
            x = int((k * 6 + i * 6) % 24)
            if t.get(x, 0) or t.get(x, 6):
                t.p(x, 0 if i % 2 else 6, J4)
        images.append(t)
    ecrire("aureole", images, slot="tete", ancre="tete", point=(12, 16), duree=220)

    t = T(34, 26)
    t.poly([(4, 22), (14, 6), (19, 0), (17, 5), (24, 10), (30, 22)], V2)
    t.poly([(14, 6), (19, 0), (17, 5), (16, 9)], V3)
    t.rect(0, 21, 34, 4, V1)
    t.rect(1, 21, 32, 1, V2)
    t.rect(8, 17, 18, 3, J2)
    t.p(12, 18, J4)
    etoile_pixel(t, 20, 12, J3)
    etoile_pixel(t, 11, 13, J4)
    t.contour(ENCRE)
    ecrire("chapeau-sorcier", t, slot="tete", ancre="tete", point=(17, 22), coiffe=True)

    t = T(34, 10)
    for i, x in enumerate(range(2, 33, 5)):
        y = 6 - int(round(math.sin(i / 6 * math.pi) * 3))
        t.ell(x + 1, y + 1, 1.8, 1.4, T2)
    for i, x in enumerate(range(0, 33, 5)):
        y = 5 - int(round(math.sin((i + 0.5) / 7 * math.pi) * 3))
        c = [O3, J3, B3, V3, O4, J3, B4][i % 7]
        t.ell(x + 2, y + 2, 2.6, 2.6, c)
        t.p(x + 2, y + 2, J4 if c != J3 else O3)
    t.contour(T1)
    ecrire("couronne-fleurs", t, slot="tete", ancre="tete", point=(17, 7))

    # Yeux
    ecrire("lunettes-rondes", lunettes(ENCRE, None, B4, rond=True, verre=False), slot="yeux", ancre="yeux", point=(14, 1))
    t = T(16, 22)
    t.anneau(10.5, 5.5, 5.5, 5.5, J2, ep=1.4)
    t.ell(10.5, 5.5, 4.2, 4.2, "#e6ecf2")
    t.ell(10.5, 5.5, 4.2, 4.2, None)
    t.rect(8, 3, 2, 1, B4)
    for y in range(11, 21, 2):
        t.p(15 - (y - 11) // 3, y, J3)
        t.p(15 - (y - 11) // 3, y + 1, J1)
    ecrire("monocle", t, slot="yeux", ancre="yeux", point=(-1, 2))
    t = T(34, 20)
    t.rect(2, 6, 30, 11, B2)
    t.rect(4, 8, 26, 7, "#d8ecff")
    t.rect(4, 8, 26, 2, BLANC)
    t.rect(16, 8, 2, 7, B2)
    t.rect(0, 9, 2, 5, ENCRE)
    t.rect(32, 9, 2, 5, ENCRE)
    t.rect(28, 0, 3, 7, O3)
    t.rect(28, 0, 5, 2, O3)
    t.rect(29, 1, 1, 5, O5)
    t.contour(B1)
    ecrire("masque-plongee", t, slot="yeux", ancre="yeux", point=(17, 8))

    # Cou
    t = T(34, 20)
    t.ell(17, 3.5, 16, 4, O3)
    for x in range(0, 34):
        for y in range(0, 8):
            if t.get(x, y) == O3 and (x // 3) % 2 == 0:
                t.p(x, y, CREME)
    t.poly([(22, 5), (28, 5), (29, 19), (23, 19)], O3)
    for y in range(6, 19, 4):
        t.rect(23, y, 6, 2, CREME)
    for x in range(23, 30, 2):
        t.p(x, 19, O2)
    t.contour(O1)
    ecrire("echarpe", t, slot="cou", ancre="cou", point=(17, 5))
    t = T(12, 16)
    t.poly([(1, 0), (5, 0), (7, 7), (5, 8)], B3)
    t.poly([(11, 0), (7, 0), (5, 7), (7, 8)], B2)
    t.ell(6, 11, 4.5, 4.5, J3)
    t.ell(6, 11, 3, 3, J2)
    etoile_pixel(t, 6, 11, J4)
    t.contour(ENCRE)
    ecrire("medaille", t, slot="cou", ancre="cou", point=(6, 2))

    # Dos
    images = []
    for k in range(3):
        t = T(46, 30)
        ond = [0, 1, 0][k]
        t.poly([(9, 0), (37, 0), (44, 27 + ond), (34, 29 - ond), (23, 28 + ond), (12, 29 - ond), (2, 27 + ond)], V2)
        t.poly([(9, 0), (16, 0), (8, 28), (2, 27 + ond)], V1)
        t.poly([(30, 0), (37, 0), (44, 27 + ond), (38, 28)], V3)
        t.contour(ENCRE)
        images.append(t)
    ecrire("cape", images, slot="dos", ancre="cou", point=(23, 4), couche="derriere", duree=300)

    # Main
    images = []
    for k in range(4):
        t = T(14, 22)
        t.ligne(2, 21, 9, 7, BR2)
        t.ligne(3, 21, 10, 7, BR1)
        etoile_grande(t, 10, 4, J3, J4)
        for i, (x, y) in enumerate(((2, 2), (13, 9), (5, 6), (12, 0))):
            if (i + k) % 2 == 0:
                t.p(x, y, J4)
        images.append(t)
    ecrire("baguette", images, slot="main", ancre="main", point=(2, 18), duree=200)

    images = []
    for k in range(4):
        t = T(16, 38)
        sw = [0, 1, 0, -1][k]
        t.ell(8 + sw * 0.5, 7, 7, 7.5, O3)
        t.ell(6 + sw * 0.5, 4.5, 2, 2.5, O5)
        t.poly([(7 + sw * 0.5, 14), (9 + sw * 0.5, 14), (8 + sw * 0.5, 16)], O2)
        t.contour(O1)
        for y in range(16, 38):
            t.p(int(8 + sw * math.sin((y - 16) / 4) * 1.2), y, GRIS)
        images.append(t)
    ecrire("ballon-helium", images, slot="main", ancre="main", point=(8, 33), duree=350)

    t = T(40, 34)
    t.ell(20, 13, 19, 12, B2, cond=lambda x, y, u, v: v < 0)
    t.ell(20, 13, 19, 12, B3, cond=lambda x, y, u, v: v < 0 and int((u + 1) * 2.5) % 2 == 0)
    for i in range(5):
        t.ell(4 + i * 8, 13, 4.2, 2.4, None, cond=lambda x, y, u, v: v < 0.2)
    t.rect(19, 0, 2, 2, B1)
    t.rect(19, 12, 2, 18, ARDOISE)
    t.ligne(20, 30, 17, 33, ARDOISE)
    t.ligne(16, 33, 15, 31, ARDOISE)
    t.contour(B1)
    ecrire("parapluie", t, slot="main", ancre="main", point=(19, 28))

    images = []
    for k in range(4):
        t = T(14, 20)
        t.rect(1, 9, 9, 10, CREME)
        t.rect(1, 9, 9, 2, BR2)
        t.rect(3, 13, 5, 3, O3)
        t.anneau(11, 14, 3, 3.2, CREME, ep=1.4)
        for i in range(2):
            ph = (k / 4 + i * 0.5) % 1
            y = int(7 - ph * 7)
            x = 3 + i * 4 + int(math.sin(ph * 6) * 1.5)
            t.p(x, y, GRIS_C)
            t.p(x, y + 1, GRIS_C)
        t.contour(GRIS)
        images.append(t)
    ecrire("tasse-cafe", images, slot="main", ancre="main", point=(1, 13), duree=240)

    # Compagnons (à côté de Pilou, posés au sol)
    images = []
    for k in range(4):
        t = T(16, 17)
        t.ell(7, 13, 6, 4.5, GRIS_C)
        t.ell(7, 7, 5.5, 4.8, GRIS_C)
        t.poly([(2, 5), (2.5, 0), (6, 3)], GRIS_C)
        t.poly([(8, 3), (11.5, 0), (12, 5)], GRIS_C)
        t.p(3, 2, O4); t.p(11, 2, O4)
        q = [(13, 15), (14, 13), (15, 11), (15, 9)] if k % 2 == 0 else [(13, 15), (15, 14), (16, 12), (16, 10)]
        for (x, y) in q:
            t.rect(x - 1, y - 1, 2, 2, GRIS_C)
        for x in (4, 7, 10):
            t.p(x, 11, GRIS)
        if k == 3:
            t.rect(4, 7, 2, 1, ENCRE); t.rect(9, 7, 2, 1, ENCRE)
        else:
            t.rect(4, 6, 2, 2, ENCRE); t.rect(9, 6, 2, 2, ENCRE)
            t.p(4, 6, B4); t.p(9, 6, B4)
        t.p(7, 8, O3)
        t.ligne(6, 9, 5, 10, ENCRE); t.ligne(8, 9, 9, 10, ENCRE)
        t.contour(ARDOISE)
        images.append(t)
    ecrire("petit-chat", images, slot="compagnon", ancre="cote", point=(1, 17), duree=320)
    images = []
    for k in range(4):
        t = T(18, 15)
        t.ell(7, 10, 6, 4.5, GRIS_C)
        t.ell(5, 5, 4.5, 4, GRIS_C)
        t.poly([(1, 3), (2, -1), (4, 2)], GRIS_C)
        t.poly([(6, 2), (8, -1), (9, 3)], GRIS_C)
        t.p(2, 1, O4)
        t.p(8, 1, O4)
        queue = [(12, 10), (14, 8), (15, 5), (14, 3)] if k % 2 == 0 else [(12, 10), (15, 9), (17, 7), (17, 4)]
        for (x, y) in queue:
            t.rect(x, y, 2, 2, GRIS_C)
        for x in range(3, 12, 3):
            t.p(x, 8, GRIS)
        if k == 3:
            t.p(3, 5, ENCRE)
            t.p(4, 5, ENCRE)
            t.p(6, 5, ENCRE)
            t.p(7, 5, ENCRE)
        else:
            t.rect(3, 4, 1, 2, ENCRE)
            t.rect(7, 4, 1, 2, ENCRE)
        t.p(5, 6, O3)
        t.rect(3, 13, 2, 1, GRIS)
        t.rect(9, 13, 2, 1, GRIS)
        t.contour(ARDOISE)
        images.append(t)
    images = []

    images = []
    for k in range(6):
        t = T(16, 16)
        t.ell(8, 9, 7.5, 6.5, B4)
        t.ell(8, 9, 7.5, 6.5, B3, cond=lambda x, y, u, v: v > 0.25)
        t.rect(3, 2, 10, 2, None)
        t.rect(4, 2, 8, 1, ARGENT)
        fx = 4 + [0, 1, 2, 3, 2, 1][k]
        t.ell(fx + 2, 9, 2.5, 1.8, O3)
        t.poly([(fx - 0.5, 8), (fx + 0.5, 9), (fx - 0.5, 10.5)], O2)
        t.p(fx + 3, 8, ENCRE)
        t.rect(5, 14, 6, 1, S2)
        t.p(12, 6, BLANC)
        t.contour(B1)
        images.append(t)
    ecrire("petit-poisson-bocal", images, slot="compagnon", ancre="cote", point=(0, 16), duree=260)

    # Effets
    fins.ACTIF = True
    images = []
    for k in range(6):
        t = T(52, 40)
        for i, (x, base) in enumerate(((2, 36), (44, 30), (6, 22), (40, 16))):
            ph = (k / 6 + i * 0.29) % 1
            y = int(base - ph * 14)
            coeur(t, x + int(math.sin(ph * 6 + i) * 2), y, O3 if i % 2 == 0 else O4)
        images.append(t)
    ecrire("trainee-coeurs", images, slot="effet", ancre="corps", point=(26, 34), duree=170)
    images = []
    for k in range(6):
        t = T(52, 40)
        for i, (x, base) in enumerate(((3, 34), (45, 30), (7, 20), (41, 14))):
            ph = (k / 6 + i * 0.29) % 1
            y = int(base - ph * 14)
            note(t, x + int(math.sin(ph * 6 + i) * 2), y, [B3, V3, J3, O3][i])
        images.append(t)
    ecrire("trainee-notes", images, slot="effet", ancre="corps", point=(26, 34), duree=170)
    fins.ACTIF = False
    images = []
    for k in range(4):
        t = T(44, 40)
        r = [0, 0.8, 1.4, 0.8][k]
        t.anneau(22, 21, 20 + r, 18 + r, V4, ep=1.2)
        t.anneau(22, 21, 18 + r, 16 + r, V3, ep=1)
        for i in range(6):
            a = i * math.pi / 3 + k * 0.4
            t.p(int(22 + math.cos(a) * (21 + r)), int(21 + math.sin(a) * (19 + r)), J4)
        images.append(t)
    ecrire("aura", images, slot="effet", ancre="corps", point=(22, 19), couche="derriere", duree=260)


def stades():
    # Cape-comète de Pilou Astral : derrière le corps, une traîne qui scintille.
    images = []
    for k in range(4):
        t = T(52, 40)
        t.poly([(14, 0), (38, 0), (48, 30), (40, 38), (30, 34), (22, 38), (12, 34), (4, 30)], V1)
        t.poly([(16, 0), (36, 0), (44, 28), (26, 33), (8, 28)], V2)
        t.poly([(30, 0), (36, 0), (46, 28), (40, 30)], V3)
        for i in range(9):
            x = int((i * 11 + k * 3) % 40) + 6
            y = int((i * 7 + k * 5) % 30) + 3
            if t.get(x, y) in (V1, V2, V3):
                t.p(x, y, J4 if (i + k) % 3 else BLANC)
        t.contour(ENCRE)
        images.append(t)
    ecrire("astral-cape", images, slot="dos", ancre="cou", point=(26, 6), couche="derriere", duree=200,
           commentaire="stade 4 : cape-comète")


def etoile_pixel(t, x, y, c):
    if toile.fin() and fins.ACTIF:
        fins.etincelle(t, x + 0.5, y + 0.5, c, bras=3, coeur=fins.clair(c, 0.7))
        return
    for a, b in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
        t.p(x + a, y + b, c)


def etoile_grande(t, cx, cy, c, cc):
    pts = []
    for k in range(10):
        a = math.radians(-90 + k * 36)
        r = 4.5 if k % 2 == 0 else 1.9
        pts.append((cx + 0.5 + math.cos(a) * r, cy + 0.5 + math.sin(a) * r))
    t.poly(pts, c)
    t.p(cx, cy, cc)


def coeur(t, x, y, c):
    if toile.fin() and fins.ACTIF:
        fins.coeur_fin(t, x, y, 7, 6, c, lueur=O5)
        return
    t.motif(x, y, [".oo.oo.", "oooooooo"[:7], "ooooooo", ".ooooo.", "..ooo..", "...o..."], {"o": c})
    t.p(x + 1, y + 1, O5)


# =====================================================================================================
# Pièces d'or, quêtes
# =====================================================================================================
def quetes():
    for k, larg in enumerate((12, 10, 6, 2, 6, 10)):
        pass
    images = []
    for k, larg in enumerate((12, 9, 4, 2, 4, 9)):
        t = T(12, 12)
        x0 = (12 - larg) / 2
        t.ell(6, 6, larg / 2, 6, J3)
        if larg >= 9:
            t.ell(6, 6, larg / 2 - 1.6, 4.4, J2)
            t.ell(6, 6, larg / 2 - 2.6, 3.4, J3)
            t.rect(5, 3, 2, 6, J1) if larg >= 12 else t.rect(5, 3, 1, 6, J1)
            t.p(4, 2, J4)
        elif larg >= 4:
            t.ell(6, 6, larg / 2 - 1, 4.5, J2)
        t.contour(J1)
        images.append(t)
    t0 = images[0].copie()
    ecrire("po", t0, slot="objet", commentaire="pièce d'or (icône)")
    big = []
    for im in images:
        tt = T(14, 14)
        tt.coller(im, 1, 1)
        big.append(tt)
    ecrire("po-tourne", big, slot="objet", duree=110, commentaire="pièce d'or qui tourne")

    t = T(22, 18)
    t.rect(1, 6, 20, 11, BR2)
    t.ell(11, 7, 10, 6, BR3, cond=lambda x, y, u, v: v < 0)
    t.rect(1, 6, 20, 2, J2)
    t.rect(1, 15, 20, 2, J2)
    t.rect(4, 1, 2, 16, J2)
    t.rect(16, 1, 2, 16, J2)
    t.rect(9, 7, 4, 5, J3)
    t.rect(10, 9, 2, 2, ENCRE)
    for x in range(2, 21, 3):
        t.p(x, 11, BR1)
    t.contour(ENCRE)
    ecrire("coffre-quete", t, slot="objet")
    t = T(20, 18)
    t.rect(3, 2, 14, 14, S3)
    t.ell(3, 9, 2.5, 7.5, S2)
    t.ell(17, 9, 2.5, 7.5, S2)
    t.ell(3, 9, 1, 6, S1)
    for y in range(5, 14, 2):
        t.ligne(6, y, 14, y, S1 if y != 9 else S2)
    t.rect(9, 14, 3, 3, O3)
    t.poly([(9, 17), (8, 18), (10, 17)], O2)
    t.poly([(11, 17), (13, 18), (12, 17)], O2)
    t.contour(BR1)
    ecrire("parchemin-quete", t, slot="objet")


# =====================================================================================================
# Pêche : 23 prises, une silhouette chacune
# =====================================================================================================
def poisson(t, x, y, w, h, corps, clair, detail, queue="fourche", nageoire=True, rayures=0, taches=False, lanterne=False):
    cx, cy = x + w * 0.45, y + h / 2
    t.ell(cx, cy, w * 0.42, h / 2, corps)
    t.ell(cx, cy + h * 0.15, w * 0.38, h * 0.3, clair, cond=lambda xx, yy, u, v: v > 0.1)
    qx = x + w * 0.83
    if queue == "fourche":
        t.poly([(qx - 2, cy), (x + w, cy - h * 0.5), (x + w - 1.5, cy), (x + w, cy + h * 0.5)], corps)
    else:
        t.poly([(qx - 2, cy), (x + w, cy - h * 0.4), (x + w, cy + h * 0.4)], corps)
    if nageoire:
        t.poly([(cx - 1, cy - h / 2 + 0.5), (cx + 3, cy - h / 2 - 2), (cx + 4, cy - h / 2 + 1)], detail)
    for i in range(rayures):
        xx = int(cx - w * 0.2 + i * 3)
        for yy in range(int(cy - h / 2) + 1, int(cy + h / 2)):
            if t.get(xx, yy) in (corps, clair):
                t.p(xx, yy, detail)
    if taches:
        for (a, b) in ((-3, -1), (0, 1), (3, -2), (-1, -3)):
            t.p(int(cx + a), int(cy + b), detail)
    ex = int(cx - w * 0.28)
    t.rect(ex, int(cy - h * 0.15), 2, 2, ENCRE)
    t.p(ex, int(cy - h * 0.15), BLANC)
    if lanterne:
        t.ligne(ex + 1, int(cy - h / 2), ex - 2, int(cy - h / 2) - 4, detail)
        t.ell(ex - 2.5, cy - h / 2 - 5, 1.8, 1.8, O5)
    if toile.fin():
        import finition_prises
        finition_prises.poisson_fin(t, x, y, w, h, corps, clair, detail, queue, taches, lanterne)


def prises():
    # Au fin, les positions gardent leurs demi-unités et les rubans avancent d'un demi-pixel (courbes lisses).
    ent = (lambda v: v) if toile.fin() else int
    pas = 0.5 if toile.fin() else 1
    rangef = (lambda a, b: [v / 2 for v in range(a * 2, b * 2)]) if toile.fin() else range

    def fin(t, id_, contour):
        t.contour(contour)
        if toile.fin():
            import finition
            finition.poser_detail("prise-" + id_, t)
        t, _, _ = t.rogner()
        ecrire("prise-" + id_, t, slot="objet", commentaire="prise de pêche")

    t = T(24, 12); poisson(t, 1, 1, 22, 10, B2, B4, B1, rayures=0, taches=True); fin(t, "goujon", B1)
    t = T(24, 10); poisson(t, 1, 1, 22, 8, GRIS_C, ARGENT_C, GRIS); fin(t, "ablette", ARDOISE)
    t = T(16, 22)
    for i, x in enumerate((3, 7, 11)):
        for y in rangef(1, 21):
            xx = x + ent(math.sin(y / 2.5 + i) * 1.6)
            t.rect(xx, y, 2, pas, [B2, B3, T2][i])
        t.ell(x + 1 + ent(math.sin(1 / 2.5 + i) * 1.6), 1.5, 1.5, 1.5, B4)
    fin(t, "algue", B1)
    t = T(18, 22)
    t.rect(4, 1, 9, 13, GRIS)
    t.rect(5, 1, 3, 12, GRIS_C)
    t.poly([(4, 13), (13, 13), (17, 16), (17, 20), (1, 20), (1, 16)], GRIS)
    t.rect(1, 18, 17, 3, ARDOISE)
    t.rect(4, 1, 9, 2, ARDOISE)
    for y in range(5, 13, 3):
        t.rect(10, y, 2, 1, GRIS_C)
    t.p(15, 21, B3); t.p(16, 21, B3)
    fin(t, "botte", ENCRE)
    t = T(18, 12)
    t.ell(9, 6.5, 8, 5, GRIS_C)
    t.ell(7, 4.5, 4, 2, CREME_O)
    t.ell(11, 8.5, 5, 2, "#909dab")
    t.p(6, 4, BLANC)
    fin(t, "caillou", ARDOISE)
    t = T(26, 14); poisson(t, 1, 1, 24, 12, J2 if False else "#f2a94e", "#ffd59a", "#7a4210", rayures=4); fin(t, "perche", O1)
    t = T(24, 18)
    t.ell(12, 10, 6, 4, O2)
    t.ell(12, 9, 4, 2.5, O3)
    for s in (-1, 1):
        x = 12 + s * 8
        t.ell(x, 5, 3, 2.5, O2)
        t.rect(x - (2 if s < 0 else -1), 3, 2, 2, None)
        t.ligne(12 + s * 4, 8, x, 7, O2)
        for i in range(3):
            t.ligne(12 + s * (3 + i * 2), 13, 12 + s * (5 + i * 2), 16, O1)
    t.rect(10, 6, 1, 2, ENCRE); t.rect(13, 6, 1, 2, ENCRE)
    t.ligne(10, 5, 7, 0, O1); t.ligne(13, 5, 16, 0, O1)
    t.poly([(17, 10), (23, 8), (23, 12)], O3)
    fin(t, "ecrevisse", O1)
    t = T(18, 18)
    for k in (range(70) if not toile.fin() else range(900)):
        a = k * 0.18 if not toile.fin() else k * 0.014
        r = 0.9 + a * 0.75
        x, y = 9 + math.cos(a) * r, 9 + math.sin(a) * r
        if toile.fin():
            # Coquille en spirale tracée au demi-pixel : un ruban crème, une arête plus sombre à chaque quart de tour.
            t.ell(x + 1, y + 1, 1.15, 1.15, CREME_O if (a % 1.57) < 0.3 else CREME)
            continue
        t.rect(ent(x), ent(y), 2, 2, CREME if k % 9 else CREME_O)
    t.ell(9, 9, 2, 2, O4)
    t.p(9, 9, O3)
    fin(t, "spirale", GRIS)
    t = T(12, 26)
    t.rect(3, 0, 6, 3, BR3)
    t.rect(4, 3, 4, 5, B3)
    t.ell(6, 15, 5.5, 9, B3)
    t.ell(5, 12, 2, 4, B4)
    t.rect(3, 12, 6, 7, CREME)
    t.rect(4, 14, 4, 1, GRIS)
    t.rect(4, 16, 3, 1, GRIS)
    t.rect(6, 11, 1, 1, O3)
    fin(t, "bouteille", B1)
    t = T(28, 14); poisson(t, 1, 1, 26, 12, ARGENT, BLANC, ARDOISE, taches=True); fin(t, "truite", ARDOISE)
    t = T(32, 10)
    for x in range(1, 30):
        y = 5 + math.sin(x / 4) * 2.5
        t.ell(x, y, 2.6, 2.6 if x < 26 else 1.6, "#2a5ea8")
        t.p(x, int(y) + 1, B3) if not toile.fin() else t.p(x - 0.5, y + 1.2, B3)
    t.rect(4, 4, 2, 2, ENCRE)
    t.p(4, 4, BLANC)
    t.ell(29.5, 5 + math.sin(29.5 / 4) * 2.5, 2.5, 3, "#2a5ea8")
    fin(t, "anguille", NUIT)
    t = T(26, 18)
    t.ell(13, 10, 7, 5, B3)
    t.ell(13, 9, 5, 3, B4)
    for s in (-1, 1):
        x = 13 + s * 9
        t.ell(x, 4, 3.5, 3, B3)
        t.rect(x - (1 if s < 0 else 0), 1, 2, 3, None)
        t.ligne(13 + s * 5, 8, x, 6, B3)
        for i in range(3):
            t.ligne(13 + s * (4 + i * 2), 14, 13 + s * (6 + i * 2), 17, B2)
    t.rect(11, 6, 1, 2, ENCRE); t.rect(15, 6, 1, 2, ENCRE)
    t.ligne(11, 5, 10, 3, B1); t.ligne(15, 5, 16, 3, B1)
    fin(t, "crabe", B1)
    t = T(26, 12)
    t.anneau(5.5, 6, 5, 5, "#c97a28", ep=2.3)
    t.rect(10, 5, 15, 3, "#c97a28")
    t.rect(19, 8, 2, 3, "#c97a28")
    t.rect(23, 8, 2, 3, "#c97a28")
    for (x, y) in ((3, 2), (12, 6), (20, 6), (7, 9)):
        t.p(x, y, O1)
    t.rect(11, 5, 12, 1, "#f2a94e")
    fin(t, "cle", O1)
    t = T(24, 22)
    t.ell(12, 8, 8, 7.5, V3)
    t.ell(10, 5, 3, 2.5, V4)
    for i in range(6):
        x0 = 5 + i * 2.8
        for y in rangef(13, 21):
            xx = ent(x0 + math.sin(y / 2 + i) * 1.3)
            t.rect(xx, y, 2, pas, V3 if i % 2 else V2)
    t.rect(8, 8, 2, 2, ENCRE); t.rect(14, 8, 2, 2, ENCRE)
    t.p(8, 8, BLANC); t.p(14, 8, BLANC)
    t.rect(11, 11, 2, 1, V1)
    fin(t, "pieuvre", V1)
    t = T(30, 14); poisson(t, 1, 1, 28, 12, O3, O5, O1, taches=True); fin(t, "saumon", O1)
    t = T(26, 20); poisson(t, 1, 7, 24, 12, NUIT, B1, O3, lanterne=True); fin(t, "lanterne", ENCRE)
    t = T(14, 26)
    t.ell(8, 5, 4.5, 4, "#f2a94e")
    t.poly([(10, 3), (14, 4), (10, 6)], "#f2a94e")
    t.ell(7, 12, 4, 5, "#f2a94e")
    for y in rangef(15, 24):
        x = 7 - (y - 15) * 0.3 + math.sin((y - 15) / 2.5) * 1.5
        t.rect(ent(x), y, 3 if y < 20 else 2, pas, "#f2a94e")
    t.ell(5, 24, 2.2, 2, "#f2a94e")
    t.ell(5, 24, 1, 1, None)
    for y in range(8, 17, 2):
        t.rect(5, y, 4, 1, "#ffe7b8")
    t.poly([(3, 8), (0, 10), (3, 12)], "#c97a28")
    t.rect(7, 3, 2, 2, ENCRE)
    fin(t, "hippocampe", O1)
    t = T(22, 18)
    t.rect(1, 7, 20, 10, "#c97a28")
    t.ell(11, 8, 10, 6, "#f2a94e", cond=lambda x, y, u, v: v < 0)
    t.rect(1, 7, 20, 2, ARDOISE)
    t.rect(1, 15, 20, 2, ARDOISE)
    t.rect(9, 8, 4, 5, J3)
    t.rect(10, 10, 2, 2, ENCRE)
    t.p(3, 4, B3); t.p(17, 3, B4); t.p(15, 12, J4)
    fin(t, "coffre", ENCRE)
    t = T(28, 20)
    t.poly([(14, 1), (27, 9), (14, 15), (1, 9)], V2)
    t.poly([(14, 3), (23, 9), (14, 12), (5, 9)], V3)
    t.ligne(14, 15, 15, 19, V2)
    t.ligne(15, 19, 18, 19, V2)
    etoile_pixel(t, 10, 8, O5)
    etoile_pixel(t, 17, 7, O5)
    etoile_pixel(t, 14, 11, J4)
    t.rect(11, 5, 1, 1, ENCRE); t.rect(16, 5, 1, 1, ENCRE)
    fin(t, "raie", V1)
    t = T(18, 16)
    t.ell(9, 10, 8.5, 5, S3, cond=lambda x, y, u, v: v > -0.2)
    t.ell(9, 7, 5.5, 5.5, ARGENT_C)
    t.ell(7.5, 5.5, 2.5, 2.5, BLANC)
    t.ell(10.5, 8.5, 2, 2, V4)
    t.p(6, 5, BLANC)
    fin(t, "perle", V1)
    t = T(32, 18)
    poisson(t, 1, 1, 30, 16, O3, BLANC, B2, taches=True)
    for (x, y) in ((10, 6), (14, 10), (18, 5), (20, 11)):
        if toile.fin():
            # Taches rondes de la carpe koï, un point bleu à l'ombre.
            t.ell(x + 1.5, y + 1.5, 1.7, 1.5, BLANC)
            t.ell(x + 0.8, y + 0.8, 0.5, 0.5, B2)
            continue
        t.rect(x, y, 3, 3, BLANC)
        t.rect(x, y, 1, 1, B2)
    fin(t, "carpe", O1)
    t = T(34, 12)
    t.ell(8, 6, 6.5, 5, O5)
    t.ell(7, 5, 3, 2, BLANC)
    for x in (range(13, 33) if not toile.fin() else [v / 2 for v in range(26, 66)]):
        h = max(0.6, 4.5 - (x - 13) * 0.21)
        if toile.fin():
            # Traînée lisse : le biseau de la queue se calcule au demi-pixel, bandes plus claires au cœur.
            t.rect(x, 6 - h, 0.5, h * 2, O3 if (int(x) // 3) % 2 else O4)
            t.rect(x, 6 - h * 0.34, 0.5, h * 0.68, O4 if (int(x) // 3) % 2 else O5)
            continue
        t.rect(x, int(6 - h), 1, int(h * 2), O3 if (x // 3) % 2 else O4)
    for (x, y) in ((20, 2), (26, 9), (30, 4)):
        t.p(x, y, BLANC)
    t.rect(4, 5, 2, 2, ENCRE)
    fin(t, "comete", O1)
    t = T(34, 20)
    t.ell(14, 11, 13, 7.5, B4)
    t.ell(14, 14, 11, 3.5, BLANC, cond=lambda x, y, u, v: v > 0)
    t.poly([(26, 10), (33, 3), (31, 10), (33, 16)], B4)
    t.rect(7, 2, 2, 3, BLANC); t.rect(5, 1, 2, 1, BLANC); t.rect(9, 0, 2, 1, BLANC)
    t.rect(6, 9, 2, 2, ENCRE)
    t.ell(4, 13, 2.5, 1.5, O4)
    for x in (10, 14, 18):
        t.p(x, 16, B3)
    fin(t, "baleineau", B2)


# =====================================================================================================
# Cuisine
# =====================================================================================================
def assiette(t, cx, cy, rx=11, ry=3.5):
    t.ell(cx, cy, rx, ry, CREME)
    t.ell(cx, cy - 0.5, rx - 2.5, ry - 1.2, BLANC)
    t.ell(cx, cy + 1, rx, ry - 1, CREME_O, cond=lambda x, y, u, v: v > 0.55)


def cuisine():
    images = []
    for k in range(3):
        t = T(28, 22)
        t.ell(14, 10, 12, 3, ARDOISE)
        t.ell(14, 10, 10.5, 2, B2)
        for i in range(4):
            x = 6 + i * 5 + (k + i) % 3
            t.ell(x, 9.5 + ((k + i) % 2) * 0.5, 1.4, 1, B4)
        t.rect(2, 10, 24, 10, GRIS)
        t.rect(4, 11, 5, 8, GRIS_C)
        t.rect(2, 18, 24, 2, ARDOISE)
        t.rect(0, 12, 3, 2, ARDOISE)
        t.rect(25, 12, 3, 2, ARDOISE)
        t.contour(ENCRE)
        images.append(t)
    ecrire("marmite", images, slot="objet", duree=220)
    images = []
    for k in range(3):
        t = T(26, 10)
        for i in range(6):
            x = 2 + i * 4
            h = 4 + ((i * 3 + k * 2) % 5)
            t.poly([(x, 10), (x + 1.8, 10 - h), (x + 3.6, 10)], O3)
            t.poly([(x + 1, 10), (x + 1.8, 10 - h + 3), (x + 2.6, 10)], O5)
        images.append(t)
    ecrire("feu", images, slot="objet", duree=150)
    images = []
    for k in range(4):
        t = T(20, 14)
        for i in range(3):
            ph = (k / 4 + i / 3) % 1
            y = int(12 - ph * 12)
            x = 4 + i * 6 + int(math.sin(ph * 6 + i) * 2)
            t.ell(x, y, 2 - ph, 1.6 - ph * 0.8, CREME)
        images.append(t)
    ecrire("vapeur", images, slot="objet", duree=180)

    t = T(26, 16)
    assiette(t, 13, 12)
    t.ell(12, 7.5, 8, 3.5, O3)
    t.poly([(19, 7.5), (24, 4), (24, 11)], O3)
    t.rect(6, 6, 2, 2, ENCRE)
    for x in range(9, 18, 3):
        t.ligne(x, 5, x + 2, 9, O1)
    t.ell(17, 4, 2, 1, B3)
    t.contour(GRIS)
    ecrire("plat-assiette", t, slot="objet", commentaire="poisson grillé sur assiette")

    t = T(24, 16)
    t.ell(12, 6, 11, 3.5, CREME)
    t.ell(12, 6, 9.5, 2.3, O4)
    for (x, y) in ((7, 6), (12, 5), (16, 6), (10, 7)):
        t.p(x, y, O2)
    t.ell(12, 7, 11, 8, CREME, cond=lambda x, y, u, v: v > 0.1)
    t.ell(12, 7, 11, 8, B3, cond=lambda x, y, u, v: 0.45 < v < 0.65)
    t.contour(GRIS)
    images = [t]
    for k in range(1, 3):
        tt = t.copie()
        for i in range(2):
            tt.p(9 + i * 5 + k, 1 - (k % 2), GRIS_C)
            tt.p(9 + i * 5 + k, 2 - (k % 2), GRIS_C)
        images.append(tt)
    t0 = images[0]
    t0.p(9, 1, GRIS_C); t0.p(9, 2, GRIS_C)
    ecrire("plat-bol", images, slot="objet", duree=260, commentaire="soupe, bouillon, velouté")

    t = T(24, 18)
    t.ell(12, 9, 11, 3.5, CREME)
    t.ell(12, 9, 9.5, 2.3, J4)
    t.ligne(5, 8, 18, 7, J3)
    t.ell(9, 7.5, 2.5, 1.2, O4)
    t.ell(15, 7.5, 1.6, 1.6, NUIT)
    t.ell(12, 10, 11, 8, B2, cond=lambda x, y, u, v: v > 0.15)
    t.ell(12, 10, 11, 8, B3, cond=lambda x, y, u, v: 0.4 < v < 0.55)
    t.ligne(18, 0, 14, 9, BR3)
    t.ligne(21, 0, 16, 9, BR3)
    t.contour(GRIS)
    ecrire("plat-ramen", t, slot="objet")

    t = T(26, 16)
    t.poly([(2, 4), (24, 4), (21, 15), (5, 15)], BR3)
    for x in range(4, 23, 3):
        t.ligne(x, 5, x - 1, 14, BR2)
    for (x, y) in ((5, 3), (9, 2), (13, 3), (17, 2), (20, 3), (11, 1)):
        t.ell(x, y, 2.6, 2, "#f2a94e")
        t.p(x - 1, y - 1, J4)
    t.contour(BR1)
    ecrire("plat-friture", t, slot="objet", commentaire="croquettes, beignets, tempura")

    t = T(28, 10)
    t.ligne(0, 5, 27, 5, BR3)
    t.ligne(0, 6, 27, 6, BR2)
    for i, x in enumerate((5, 11, 17, 23)):
        c = [O3, CREME, O2, J3][i]
        t.ell(x, 5.5, 3, 3.5, c)
        t.p(x - 1, 4, O5 if c != CREME else CREME_O)
    t.contour(O1)
    ecrire("plat-brochette", t, slot="objet")

    t = T(26, 16)
    assiette(t, 13, 12)
    t.poly([(4, 8), (13, 2), (22, 8), (13, 13)], ARGENT)
    t.poly([(4, 8), (13, 2), (22, 8)], ARGENT_C)
    t.ligne(13, 2, 13, 12, GRIS_C)
    t.contour(GRIS)
    ecrire("plat-papillote", t, slot="objet")

    t = T(28, 14)
    t.rect(1, 9, 26, 4, BR3)
    for x in (3, 11, 19):
        t.ell(x + 3, 6, 3.5, 3.5, NUIT)
        t.ell(x + 3, 6, 2.4, 2.4, CREME)
        t.ell(x + 3, 6, 1.2, 1.2, O3)
    t.contour(BR1)
    ecrire("plat-sushi", t, slot="objet", commentaire="makis")

    t = T(30, 14)
    t.ell(13, 7, 12, 5, ARDOISE)
    t.ell(13, 6.5, 10.5, 3.8, J3)
    for (x, y, c) in ((7, 6, O3), (12, 5, O2), (17, 7, B3), (10, 8, O4), (15, 5, V3), (19, 5, O3)):
        t.rect(x, y, 2, 2, c)
    t.rect(24, 6, 6, 2, ENCRE)
    t.contour(ENCRE)
    ecrire("plat-poelon", t, slot="objet", commentaire="gratin, risotto, riz, curry")

    t = T(26, 16)
    t.ell(13, 10, 12, 5, "#f2a94e")
    t.ell(13, 8, 12, 5, O4, cond=lambda x, y, u, v: v < 0.5)
    for x in range(3, 24, 4):
        t.rect(x, 5 + abs(13 - x) // 6, 2, 1, O2)
    etoile_pixel(t, 13, 8, J3)
    t.ell(13, 13, 12, 3, BR3, cond=lambda x, y, u, v: v > 0)
    t.contour(O1)
    ecrire("plat-tarte", t, slot="objet", commentaire="tourte, feuilleté, tarte")

    t = T(32, 18)
    t.ell(16, 12, 15, 5, ARGENT)
    t.ell(16, 11.5, 13, 3.6, ARGENT_C)
    t.ell(9, 9, 4, 2.5, O3)
    t.ell(16, 8, 3, 3, CREME)
    t.ell(23, 9, 4, 2.5, B3)
    t.ell(13, 12, 2.5, 1.6, O2)
    t.ell(20, 12, 2.5, 1.6, J3)
    t.rect(15, 5, 2, 2, O5)
    t.contour(ARDOISE)
    ecrire("plat-plateau", t, slot="objet", commentaire="plateau, banquet, festin")

    t = T(20, 20)
    t.rect(3, 11, 14, 8, CREME)
    for x in range(3, 17, 2):
        t.rect(x, 11, 1, 8, CREME_O)
    t.ell(10, 9, 8, 6, J4, cond=lambda x, y, u, v: v < 0.4)
    t.ell(8, 6, 3, 2, BLANC)
    t.contour(GRIS)
    ecrire("plat-souffle", t, slot="objet")

    t = T(22, 14)
    t.rect(2, 5, 18, 7, CREME)
    t.ell(11, 5, 9, 4, CREME, cond=lambda x, y, u, v: v < 0)
    t.ell(9, 3, 3, 1.5, O4)
    t.ell(14, 4, 2.5, 1.5, B3)
    t.rect(2, 11, 18, 1, CREME_O)
    t.contour(BR2)
    ecrire("plat-tartine", t, slot="objet")

    t = T(24, 18)
    t.ell(12, 13, 11, 3.5, CREME)
    t.ell(12, 13, 9.5, 2.3, BLANC)
    t.ell(12, 9.5, 8, 6.5, GRIS_C, cond=lambda x, y, u, v: v < 0.5)
    t.ell(9, 7, 2.5, 2, BLANC)
    t.rect(11, 2, 2, 2, ARGENT)
    t.contour(GRIS)
    ecrire("plat-invente", t, slot="objet", commentaire="plat inventé (cloche)")

    images = []
    for k in range(3):
        t = T(26, 20)
        assiette(t, 13, 16)
        t.ell(13, 12, 8, 4, ENCRE)
        t.ell(11, 11, 3, 1.5, NOIR2)
        for i in range(3):
            ph = (k / 3 + i / 3) % 1
            t.ell(7 + i * 6 + math.sin(ph * 6), 8 - ph * 8, 2.2, 1.6, GRIS)
        images.append(t)
    ecrire("plat-rate", images, slot="objet", duree=220, commentaire="plat brûlé")


# =====================================================================================================
# Petits jeux et Chasse aux bugs
# =====================================================================================================
def jeux():
    images = []
    for k in range(4):
        t = T(18, 18)
        r = 8.5 if k % 2 == 0 else 7.8
        pts = []
        for i in range(10):
            a = math.radians(-90 + i * 36 + k * 4)
            rr = r if i % 2 == 0 else r * 0.45
            pts.append((9 + math.cos(a) * rr, 9.5 + math.sin(a) * rr))
        t.poly(pts, J3)
        t.ell(8, 8, 2.5, 2.5, J4)
        t.p(7, 7, BLANC)
        t.contour(O1)
        images.append(t)
    ecrire("etoile", images, slot="objet", duree=120, commentaire="étoile filante")

    t = T(16, 16)
    t.ell(8, 8, 7.5, 7.5, B4)
    t.ell(8, 8, 6.3, 6.3, "#d8ecff")
    t.ell(5, 5, 2, 1.5, BLANC)
    t.p(11, 11, BLANC)
    t.contour(B2)
    ecrire("bulle", t, slot="objet", commentaire="bulle à éclater")

    t = T(18, 20)
    t.rect(3, 7, 12, 11, O4)
    for i, h in enumerate((7, 8, 8, 7)):
        t.rect(3 + i * 3, 7 - h + 1, 2, h, O4)
        t.p(3 + i * 3, 7 - h + 1, O5)
    t.poly([(15, 13), (18, 9), (18, 11), (15, 17)], O4)
    t.rect(3, 18, 12, 2, B3)
    t.ligne(6, 12, 11, 12, O3)
    t.contour(O1)
    ecrire("main", t, slot="objet", commentaire="tape m'en cinq")

    images = []
    for k in range(4):
        t = T(16, 16)
        t.ell(8, 8, 7.5, 7.5, CREME)
        t.ell(8, 8, 7.5, 7.5, CREME_O, cond=lambda x, y, u, v: u + v > 0.9)
        a = k * math.pi / 4
        for s in range(-7, 8):
            x, y = 8 + math.cos(a) * s, 8 + math.sin(a) * s
            if t.get(int(x), int(y)):
                t.rect(int(x), int(y), 2, 1, O3)
        t.contour(B1)
        images.append(t)
    ecrire("ballon", images, slot="objet", duree=90, commentaire="ballon (tourne)")

    t = T(30, 30)
    t.ligne(0, 29, 26, 3, BR2)
    t.ligne(1, 29, 27, 3, BR3)
    t.rect(0, 25, 4, 5, ARDOISE)
    t.rect(5, 23, 3, 3, ARGENT)
    t.ligne(27, 3, 29, 1, GRIS)
    ecrire("canne", t, slot="objet", commentaire="canne à pêche (côté droit)")

    images = []
    for k in range(2):
        t = T(8, 12)
        y0 = k
        t.ell(4, 4 + y0, 3.5, 3.5, O3, cond=lambda x, y, u, v: v < 0.1)
        t.ell(4, 4 + y0, 3.5, 3.5, CREME, cond=lambda x, y, u, v: v >= 0.1)
        t.rect(3, 0 + y0, 2, 1, ENCRE)
        t.rect(3, 8 + y0, 2, 3, GRIS)
        t.contour(ENCRE)
        images.append(t)
    ecrire("bouchon", images, slot="objet", duree=400)

    images = []
    for k in range(3):
        t = T(22, 14)
        for i in range(7):
            a = math.pi * (0.1 + i * 0.8 / 6)
            r = 3 + k * 3.5
            x, y = 11 + math.cos(a) * r, 13 - math.sin(a) * r * 0.9
            t.ell(x, y, 1.6, 2.2 - k * 0.4, B4 if i % 2 else BLANC)
        t.ell(11, 13, 4 + k * 2, 1.2, B3)
        images.append(t)
    ecrire("eclaboussure", images, slot="objet", duree=120)

    # Chasse aux bugs : deux fois plus fins que le monde du jeu (un pixel = une demi-unité).
    def bug(id_, corps, clair, dessin):
        images = []
        for k in range(2):
            t = T(18, 14)
            dessin(t, k, corps, clair)
            images.append(t)
        ecrire(id_, images, slot="objet", duree=300, commentaire="bug de Chasse aux bugs (18 × 14 = 9 × 7 unités)")

    def scarabee(t, k, c, cl):
        for i, y in enumerate((6, 9, 12)):
            d = 1 if (i + k) % 2 else 0
            t.ligne(3, y, 0, y + d, O1)
            t.ligne(14, y, 17, y + d, O1)
        t.ligne(7, 2, 5, 0, O1)
        t.ligne(10, 2, 12, 0, O1)
        t.ell(9, 8.5, 6, 5, c)
        t.ell(9, 3.5, 3.5, 2.2, O2)
        t.rect(8, 4, 2, 10, O1)
        t.ell(6, 7, 2, 1.5, cl)
        t.ell(12, 7, 1.5, 1.2, cl)
        t.rect(7, 2, 1, 1, BLANC); t.rect(10, 2, 1, 1, BLANC)

    def araignee(t, k, c, cl):
        for i in range(4):
            d = (i + k) % 2
            y = 5 + i * 2
            t.ligne(6, y, 2, y - 2 + d * 2, B2)
            t.ligne(2, y - 2 + d * 2, 0, y + 2, B2)
            t.ligne(11, y, 15, y - 2 + d * 2, B2)
            t.ligne(15, y - 2 + d * 2, 17, y + 2, B2)
        t.ell(9, 9, 4.5, 4, c)
        t.ell(9, 4.5, 3, 2.5, c)
        t.ell(8, 8, 1.5, 1.5, cl)
        t.rect(7, 4, 1, 1, BLANC); t.rect(10, 4, 1, 1, BLANC); t.p(8, 3, cl); t.p(9, 3, cl)

    def ver(t, k, c, cl):
        for i in range(6, -1, -1):
            x = 3 + i * 2.2
            y = 8 + math.sin(i * 1.1 + k * 1.6) * 2.2
            t.ell(x, y, 2.8, 2.8, GRIS if i % 2 else c)
            t.ell(x - 0.5, y - 0.8, 1.2, 1, cl)
        t.rect(1, 6, 2, 2, ENCRE)
        t.p(1, 6, BLANC)

    bug("bug-scarabee", O3, O5, scarabee)
    bug("bug-araignee", B3, B4, araignee)
    bug("bug-ver", ARGENT, ARGENT_C, ver)
    images = []
    for k in range(2):
        t = T(36, 22)
        t.ell(18, 12, 17, 9, O3)
        t.ell(18, 8, 13, 4, O4, cond=lambda x, y, u, v: v < 0)
        t.rect(6, 9, 5, 4, BLANC); t.rect(25, 9, 5, 4, BLANC)
        t.rect(8 + k, 10, 2, 2, ENCRE); t.rect(27 + k, 10, 2, 2, ENCRE)
        t.rect(11, 15, 14, 2, ENCRE)
        for x in range(12, 25, 3):
            t.rect(x, 15, 1, 1, BLANC)
        t.ligne(10, 3, 6, 0, ENCRE); t.ligne(26, 3, 30, 0, ENCRE)
        for i in range(5):
            x = 4 + i * 7
            t.ligne(x, 19, x - 1 + (i + k) % 2 * 2, 21, ENCRE)
        images.append(t)
    for t in images:
        t.contour(ENCRE)
    ecrire("bug-prod", images, slot="objet", duree=300, commentaire="boss « Bug de prod » (36 × 22 = 18 × 11 unités)")
    t = T(12, 12)
    t.rect(1, 4, 8, 7, CREME)
    t.rect(2, 6, 6, 3, BR2)
    t.anneau(9.5, 7.5, 2.5, 2.5, CREME, ep=1.2)
    t.p(3, 1, GRIS_C); t.p(4, 2, GRIS_C); t.p(6, 0, GRIS_C); t.p(6, 2, GRIS_C)
    t.contour(GRIS)
    ecrire("bonus-cafe", t, slot="objet")
    t = T(12, 12)
    t.rect(0, 0, 12, 12, B2)
    t.rect(1, 1, 10, 10, B4)
    t.motif(2, 3, ["......kk", ".....kk.", "k...kk..", "kk.kk...", ".kkk....", "..k....."], {"k": B1})
    ecrire("bonus-tests", t, slot="objet")
    fins.ACTIF = True
    t = T(10, 9)
    coeur(t, 1, 1, O3)
    t.contour(O1)
    ecrire("vie", t, slot="objet")
    fins.ACTIF = False


# =====================================================================================================
# Soins : icônes de besoin (une forme chacune), en-cas, mousse, rayonnement, variantes d'évolution
# =====================================================================================================
def soins():
    # Faim : un bol fumant (demi-disque, deux volutes au-dessus).
    t = T(11, 10)
    t.ell(5.5, 4, 5, 5, O3, cond=lambda x, y, u, v: v > 0.05)
    t.ell(5.5, 4, 3.5, 3.5, O4, cond=lambda x, y, u, v: v > 0.2)
    t.rect(0, 4, 11, 1, O2)
    t.rect(3, 9, 5, 1, O2)
    t.p(3, 1, CREME_O)
    t.p(4, 0, CREME_O)
    t.p(6, 2, CREME_O)
    t.p(7, 1, CREME_O)
    t.contour(O1)
    ecrire("soin-faim", t, slot="objet", commentaire="besoin : faim (bol fumant)")
    # Propreté : une étoile à quatre branches et deux bulles.
    t = T(12, 12)
    if toile.fin():
        # Étincelle à quatre branches effilées, cœur blanc ; la bulle garde son anneau et son reflet.
        cx, cy = 5.5, 6.5
        t.poly([(cx, cy - 5.5), (cx + 1.2, cy - 1.2), (cx + 5.5, cy), (cx + 1.2, cy + 1.2), (cx, cy + 5.5),
                (cx - 1.2, cy + 1.2), (cx - 5.5, cy), (cx - 1.2, cy - 1.2)], B4)
        t.ell(cx, cy, 1.5, 1.5, BLANC)
        t.contour(B1)
        t.anneau(10, 1.8, 1.8, 1.8, B3, 1)
        t.ell(9.3, 1.2, 0.5, 0.5, BLANC)
    else:
        for d in range(5):
            t.p(5 - d, 6, B4)
            t.p(5 + d, 6, B4)
            t.p(5, 6 - d, B4)
            t.p(5, 6 + d, B4)
        t.rect(4, 5, 3, 3, B4)
        t.p(5, 6, BLANC)
        t.contour(B1)
        t.anneau(10, 1.8, 1.8, 1.8, B3, 1)
        t.p(9, 1, BLANC)
    ecrire("soin-proprete", t, slot="objet", commentaire="besoin : propreté (étincelle et bulles)")
    # Moral : un cœur.
    t = T(11, 10)
    if toile.fin():
        # Cœur rond : deux lobes et une pointe, reflet en arc sur le lobe gauche.
        t.ell(3.1, 3.5, 2.7, 2.6, O3)
        t.ell(6.5, 3.5, 2.7, 2.6, O3)
        t.poly([(0.5, 4.6), (9.1, 4.6), (4.8, 8.6)], O3)
        t.ell(2.4, 2.6, 1.0, 0.7, O5)
    else:
        t.motif(0, 1, [".ooo.ooo..", "ooooooooo.", "ooooooooo.", ".ooooooo..", "..ooooo...", "...ooo....", "....o....."], {"o": O3})
        t.p(2, 2, O5)
        t.p(3, 2, O5)
    t.contour(O1)
    ecrire("soin-moral", t, slot="objet", commentaire="besoin : moral (cœur)")

    # En-cas (consommables de la boutique) : croquettes, pomme dorée, gâteau, soupe.
    t = T(12, 8)
    assiette(t, 6, 6, 6, 2)
    for x, y in ((3, 3), (6, 2), (8, 4), (5, 4), (9, 2)):
        t.ell(x + 0.5, y + 0.5, 1.3, 1.1, BR3)
        t.p(x, y, S3)
    t.contour(BR1)
    ecrire("encas-croquettes", t, slot="objet", commentaire="en-cas : croquettes")
    t = T(10, 11)
    t.ell(5, 6.5, 4.5, 4.2, J3)
    t.ell(4, 5.5, 2, 2, J4)
    t.ell(5, 9, 3.5, 1.5, J2, cond=lambda x, y, u, v: v > 0)
    t.rect(5, 0, 1, 3, BR2)
    t.poly([(6, 1), (9, 0), (8, 2)], T2)
    t.contour(J1)
    ecrire("encas-pomme", t, slot="objet", commentaire="en-cas : pomme dorée")
    t = T(12, 11)
    t.rect(1, 5, 10, 5, S2)
    t.rect(1, 5, 10, 1, CREME)
    t.rect(1, 7, 10, 1, O4)
    t.ell(6, 4.5, 5, 2, CREME)
    t.ell(6, 2, 1.4, 1.4, O3)
    t.p(6, 1, O5)
    t.contour(BR1)
    ecrire("encas-gateau", t, slot="objet", commentaire="en-cas : gâteau")
    t = T(12, 11)
    t.ell(6, 6, 5.5, 4.5, B3, cond=lambda x, y, u, v: v > 0)
    t.ell(6, 6, 4.5, 1.3, S3)
    t.rect(0, 6, 12, 1, B2)
    t.p(4, 2, CREME_O)
    t.p(5, 1, CREME_O)
    t.p(7, 3, CREME_O)
    t.p(8, 2, CREME_O)
    t.contour(B1)
    ecrire("encas-soupe", t, slot="objet", commentaire="en-cas : soupe chaude")

    # Mousse : bulles de savon qui grossissent et éclatent (toilette de 2 s).
    # Mousse blanche sur le haut du crâne et les flancs, bulles qui montent et éclatent autour.
    images = []
    bulles = [(4, 20, 3.2), (43, 17, 3.0), (9, 6, 2.6), (39, 5, 2.8), (24, 1.5, 2.2), (2, 31, 2.4), (46, 30, 2.4)]
    for k in range(4):
        t = T(50, 36)
        # Mousse : grappe de petits disques sur le crâne et les côtés.
        for i, (x, y) in enumerate(((14, 12), (18, 9), (23, 8), (28, 9), (33, 11), (36, 15), (11, 16), (10, 22), (38, 21))):
            r = 2.6 + 0.6 * ((i + k) % 2)
            t.ell(x, y, r, r, BLANC)
            t.p(int(x) - 1, int(y) - 1, B4)
        for i, (x, y, r) in enumerate(bulles):
            ph = (k + i) % 4
            yy = y - ph * 1.5
            if ph == 3:
                for a, b in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                    t.p(x + a * 2, yy + b * 2, B4)
                continue
            rr = r * (0.7 + 0.15 * ph)
            t.anneau(x, yy, rr, rr, B3, 1)
            t.p(int(x - rr * 0.4), int(yy - rr * 0.4), BLANC)
        t.contour(CREME_O)
        images.append(t)
    ecrire("mousse", images, slot="effet", ancre="corps", point=(24, 26), duree=160,
           commentaire="toilette : mousse et bulles")

    fins.ACTIF = True
    # Rayonnant : quelques étincelles discrètes qui scintillent autour de lui.
    images = []
    pts = [(2, 14), (40, 10), (6, 30), (37, 28), (20, 1)]
    for k in range(4):
        t = T(44, 34)
        for i, (x, y) in enumerate(pts):
            if (i + k) % 4 == 0:
                etoile_pixel(t, x, y, J4)
            elif (i + k) % 4 == 1:
                t.p(x, y, J3)
        images.append(t)
    ecrire("rayonnant", images, slot="effet", ancre="corps", point=(22, 19), duree=260,
           commentaire="bien soigné : il rayonne (étincelles discrètes)")
    fins.ACTIF = False

    # Bouderie (Pilou négligé) : petit nuage gris qui bruine au-dessus de lui, en haut à droite (loin des
    # antennes) ; amadoué, le nuage s'éclaircit et un soleil pointe. Gris et bleus, soleil jaune-orangé.
    images = []
    for k in range(4):
        t = T(13, 12)
        h = 1 if k in (1, 2) else 0  # le nuage flotte d'un pixel
        for x, y, rx, ry in ((3.6, 5.2, 2.8, 2.3), (7, 3.8, 3.2, 2.9), (10, 5.4, 2.4, 2.1)):
            t.ell(x, y + h, rx, ry, GRIS)
        t.rect(2, 5 + h, 9, 2, GRIS)
        t.ell(6.2, 2.8 + h, 1.8, 1, GRIS_C)
        t.contour(ARDOISE)
        for i, x in enumerate((3, 7, 10)):
            y = 9 + (k + i * 2) % 4
            if y < 12:
                t.p(x, y, B3)
        images.append(t)
    ecrire("boude-nuage", images, slot="effet", ancre="tete", point=(-11, 17), duree=420,
           commentaire="il boude : petit nuage gris qui bruine")
    images = []
    for k in range(4):
        t = T(13, 12)
        t.ell(8.5, 4, 3, 3, J3)
        t.ell(7.8, 3.2, 1.1, 1.1, J4)
        for i, (x, y) in enumerate(((8, 0), (12, 4), (11, 1), (5, 1))):
            if (i + k) % 2 == 0:
                t.p(x, y, O3)
        for x, y, rx, ry in ((3.4, 7, 2.6, 2.2), (6.5, 6, 2.8, 2.4), (9.4, 7.6, 2.3, 1.9)):
            t.ell(x, y, rx, ry, CREME_O)
        t.rect(2, 7, 9, 2, CREME_O)
        t.ell(5.6, 5.4, 1.4, 0.8, CREME)
        t.contour(GRIS)
        images.append(t)
    ecrire("boude-eclaircie", images, slot="effet", ancre="tete", point=(-11, 17), duree=500,
           commentaire="il se laisse amadouer : le nuage s'éclaircit, un soleil pointe")
    # Bras croisés du Nimbus (le seul stade qui a des bras) : vus de face, deux avant-bras l'un sur l'autre qui
    # partent des coudes (ses bras habituels) et passent sous la bouche ; celui du bas, devant, recouvre l'autre.
    t = T(33, 7)
    for (g, d, haut) in ((2, 27, 1), (5, 30, 3)):
        lignes = {haut: (g + 1, d - 1, "@contour"), haut + 1: (g, d, "@clair" if haut > 1 else "@base"), haut + 2: (g, d, "@base"),
                  haut + 3: (g + 1, d - 1, "@contour")}
        for y, (x0, x1, c) in lignes.items():
            for x in range(x0, x1 + 1):
                t.p(x, y, "@contour" if c != "@contour" and x in (g, d) else c)
    ecrire("boude-bras", t, slot="main", ancre="corps", point=(16, -4),
           commentaire="il boude (Nimbus) : bras croisés")

    # Variantes d'évolution (stades 2 à 4) : « câlin » (joues roses, petit cœur), « espiègle » (mèche
    # rebelle, tache d'étoile). Les joues suivent la largeur du corps de chaque stade.
    k_ = 1.25 * 48 / 26
    joues = {2: 1.0, 3: 1.1, 4: 0.9}
    for stade, sx in joues.items():
        j = int(round(6.8 * k_ * sx)) - 1
        larg = 2 * j
        t = T(larg, 3)
        for x0 in (0, larg - 4):
            t.rect(x0, 0, 4, 2, O4)
            t.p(x0 + 1, 0, O5)
        ecrire("variante-calin-%d" % stade, t, slot="visage", ancre="yeux", point=(j, -8),
               commentaire="variante câlin, stade %d : joues roses" % stade)
        t = T(9, 8)
        fins.ACTIF = True
        coeur(t, 1, 1, O3)
        fins.ACTIF = False
        t.contour(O1)
        ecrire("variante-calin-%d-tete" % stade, t, slot="tete", ancre="tete",
               point=(-5 if stade != 3 else -8, 4), commentaire="variante câlin, stade %d : petit cœur" % stade)
        t = T(larg, 4)
        etoile_pixel(t, larg - 3, 1, J3)
        ecrire("variante-espiegle-%d" % stade, t, slot="visage", ancre="yeux", point=(j, -7),
               commentaire="variante espiègle, stade %d : tache d'étoile" % stade)
        t = T(9, 7)
        t.ligne(1, 6, 3, 1, "@contour")
        t.ligne(4, 6, 5, 0, "@contour")
        t.ligne(6, 6, 8, 2, "@contour")
        t.ligne(2, 6, 3, 3, "@base")
        t.ligne(5, 6, 5, 3, "@base")
        ecrire("variante-espiegle-%d-tete" % stade, t, slot="tete", ancre="tete",
               point=(9 if stade != 3 else 12, 6), commentaire="variante espiègle, stade %d : mèche rebelle" % stade)


# =====================================================================================================
# Teintes, tenues, plats
# =====================================================================================================
TEINTES = {
    "bleu": ["#1f4f8a", "#4a8fdc", "#6cb6ff", "#b4dbff"],
    "orange": ["#8a4a1f", "#d9803a", "#f69d50", "#ffc89a"],
    "nuit": ["#0d2a4d", "#2a5ea8", "#3f7fd6", "#8fbaf0"],
    "ambre": ["#7a4210", "#c97a28", "#f2a94e", "#ffd59a"],
    "argent": ["#3b4654", "#8796a8", "#b8c4d2", "#e6ecf2"],
    "aurore": ["#3a2a7a", "#6a5acd", "#9b8cff", "#d2caff"],
    "lagon": ["#0f4a63", "#2689b8", "#3fb8e0", "#a8e4f7"],
    "braise": ["#6b2f0c", "#c45a1a", "#f07c2a", "#ffc08a"],
    "nacre": ["#4d5566", "#b9b4cf", "#e4def5", "#ffffff"],
    "abysse": ["#0a1230", "#1b2a6b", "#2f45a8", "#7f93e8"],
    "comete": ["#5a4410", "#c9a227", "#f5d76e", "#fff6cc"],
    # Boutique
    "lavande": ["#3d2f63", "#7a66c2", "#a996f0", "#e2d9ff"],
    "corail-orange": ["#7a3414", "#d0662e", "#ff9a5c", "#ffd2b3"],
    "ardoise": ["#1f262e", "#4a5563", "#6b7787", "#a9b4c2"],
    "sable": ["#6b5235", "#b08f62", "#dcc193", "#f6ead2"],
    "glacier": ["#24506b", "#6aa6c7", "#a9d7ee", "#e8f7ff"],
    **boutique_sprites.TEINTES,
    **garde_robe.TEINTES,
    # Soins : Pilou négligé a juste l'air terne (gris-bleu délavé), sans autre conséquence.
    "terne": ["#3e4957", "#76838f", "#9fabb7", "#c9d2db"],
}

TENUES = {
    "code": ["tenue-code-lunettes", "tenue-code-clavier"],
    "tableur": ["tenue-tableur-lunettes", "tenue-tableur-calculatrice"],
    "jeu-mmo": ["tenue-mmo-epee", "tenue-mmo-bouclier"],
    "jeu": ["tenue-jeu-casque", "tenue-jeu-manette"],
    "musique": ["tenue-musique-ecouteurs", "tenue-musique-notes"],
    "video": ["tenue-video-popcorn"],
    "lecture": ["tenue-lecture-lunettes", "tenue-lecture-livre"],
    "dessin": ["tenue-dessin-beret", "tenue-dessin-palette"],
    "visio": ["tenue-visio-micro"],
    "nuit": ["tenue-nuit-bonnet"],
    "mail": ["tenue-mail-casquette", "tenue-mail-enveloppe"],
    "texte": ["tenue-texte-plume"],
    "diaporama": ["tenue-diaporama-pointeur"],
    # Tenues de voyage des campagnes (voyage_sprites.py) : « voyage-marche », « voyage-bateau »…
    **voyage_sprites.TENUES,
}

PLATS = {
    "grille": "plat-assiette", "carpaccio": "plat-assiette", "ceviche": "plat-assiette",
    "tartine": "plat-tartine",
    "soupe": "plat-bol", "ecume": "plat-bol", "chaudree": "plat-bol", "bisque": "plat-bol", "fumet": "plat-bol",
    "lune": "plat-bol", "bouillabaisse": "plat-bol",
    "ramen": "plat-ramen",
    "croquettes": "plat-friture", "beignets": "plat-friture", "tempura": "plat-friture",
    "brochette": "plat-brochette", "papillote": "plat-papillote", "maki": "plat-sushi",
    "gratin": "plat-poelon", "risotto": "plat-poelon", "paella": "plat-poelon", "curry": "plat-poelon",
    "tourte": "plat-tarte", "feuillete": "plat-tarte", "etoile": "plat-tarte",
    "plateau": "plat-plateau", "banquet": "plat-plateau", "festin": "plat-plateau", "legende": "plat-plateau",
    "nuage": "plat-souffle",
}


def tables():
    base = os.path.dirname(SORTIE)
    with open(os.path.join(base, "teintes.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# Teintes de Pilou : contour, ombre, base, clair. Lavande et les suivantes viennent de la boutique.\n")
        for k, v in TEINTES.items():
            f.write("%s: %s\n" % (k, " ".join(v)))
    with open(os.path.join(base, "tenues.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# Tenues d'activité et de voyage : identifiant (Pose.Tenue) -> sprites portés.\n")
        for k, v in TENUES.items():
            f.write("%s: %s\n" % (k, " ".join(v)))
    with open(os.path.join(base, "index.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# Liste des sprites (Android les lit comme ressources, sans pouvoir lister le dossier).\n")
        for k in sorted(TOUS):
            f.write(k + "\n")
    with open(os.path.join(base, "plats.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# Recette -> sprite du plat ; plat inventé : plat-invente ; plat brûlé : plat-rate.\n")
        for k, v in PLATS.items():
            f.write("%s: %s\n" % (k, v))
    garde_robe.ecrire_catalogue(base)


def dessiner():
    """Tous les dessins, à l'échelle courante de la toile (toile.ECHELLE)."""
    visage()
    etincelles()
    accessoires()
    tenues()
    boutique()
    quetes()
    stades()
    prises()
    cuisine()
    jeux()
    soins()
    meteo_sprites.effets()
    meteo_sprites.objets()
    boutique_sprites.objets()
    garde_robe.objets()
    visites_sprites.tout()
    gestes_sprites.tout()
    saynetes_sprites.tout()
    expedition_sprites.tout()
    defense_sprites.tout()
    voyage_sprites.tout()
    decors_campagnes.tout()
    campagnes_sprites.tout()
    portraits_campagnes.tout()
    scene_pilou.tout()
    acteurs_scenes.tout()
    traits_sprites.tout()


if __name__ == "__main__":
    for d in (SORTIE, toile.SORTIE2):
        if os.path.isdir(d):
            shutil.rmtree(d)
    dessiner()
    tables()
    # Dessin fin (2×) : les mêmes fonctions, rejouées sur une toile deux fois plus fine, pour la série de fin.py.
    import fin
    fin.generer(dessiner)
    # La police pixel de Pilou (assets/police, docs/POLICE.md).
    import police
    police.fichiers()
    print(len(TOUS), "sprites dans", SORTIE, "dont", len(toile.TOUS2), "redessinés en fin dans", toile.SORTIE2)
