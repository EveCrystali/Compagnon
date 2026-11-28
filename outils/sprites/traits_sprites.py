"""Icônes des traits de personnalité (docs/TRAITS.md) : une par trait de assets/traits.txt, plus la silhouette « ? »
des traits pas encore découverts. 16 × 16 sur la grille 1× (32 × 32 en dessin fin), sans fond : la case de
l'interface le fournit, sombre sur le PC, claire ou sombre sur le téléphone. Chaque icône a donc un cerne encre.

Palette de Pilou : bleus, oranges, jaunes, violets, crème, sable, sarcelle. Jamais de rouge contre vert : deux traits
ne se distinguent jamais par la seule couleur, chacun a sa forme (lune, soleil, poisson, bol, livre…).

    python3 outils/sprites/generer.py && python3 outils/sprites/planches_traits.py
"""
import math

import toile
from toile import Toile, ecrire

ENCRE = "#1c2128"
CREME = "#f6f8fa"
CREME_O = "#c9d1d9"
GRIS = "#768390"
ARDOISE = "#3b4654"
ARGENT = "#b8c4d2"
B1, B2, B3, B4 = "#1f4f8a", "#4a8fdc", "#6cb6ff", "#b4dbff"
O1, O2, O3, O4 = "#8a4a1f", "#d9803a", "#f69d50", "#ffc89a"
J1, J2, J3, J4 = "#7a5a10", "#c9a227", "#f5d76e", "#fff6cc"
V1, V2, V3, V4 = "#3a2a7a", "#6a5acd", "#9b8cff", "#d2caff"
S1, S2, S3 = "#8a6e4b", "#c4a77d", "#e8d5b0"
BR1, BR2, BR3 = "#4a2e17", "#7a4b26", "#a86f3c"
T1, T2, T3 = "#0f4a63", "#2689b8", "#3fb8e0"

N = 16


def T():
    return Toile(N, N)


def etoile(t, x, y, c, cc=None):
    """Petite étoile à quatre branches (une croix de cinq pixels)."""
    for a, b in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
        t.p(x + a, y + b, c)
    if cc:
        t.p(x, y, cc)


def couche_tard():
    # Croissant de lune et deux étoiles.
    t = T()
    t.ell(7.5, 8.5, 5.6, 5.6, J3, cond=lambda x, y, u, v: (u - 0.52) ** 2 + (v + 0.3) ** 2 > 0.62)
    t.ell(6.2, 10, 3, 3.4, J2, cond=lambda x, y, u, v: u < -0.35 and t.get(x, y) == J3)
    etoile(t, 12, 4, J4)
    t.p(13, 10, J4)
    t.contour(ENCRE)
    return t


def leve_tot():
    # Soleil qui se lève sur l'horizon, trois rayons.
    t = T()
    t.ell(8, 11, 4.6, 4.6, O3, cond=lambda x, y, u, v: v <= 0)
    t.ell(8, 11, 3, 3, J3, cond=lambda x, y, u, v: v <= 0)
    t.rect(1, 11, 14, 1, B2)
    t.rect(3, 13, 10, 1, B3)
    t.rect(6, 15, 4, 1, B4)
    t.contour(ENCRE)
    t.rect(8, 1, 1, 3, J3)
    t.ligne(2, 4, 3, 5, J3)
    t.ligne(13, 4, 12, 5, J3)
    return t


def pecheur_du_dimanche():
    # Un poisson au bout de la ligne.
    t = T()
    t.ell(7.5, 10, 4.8, 3.2, B3)
    t.ell(7.5, 11, 4, 2, B4, cond=lambda x, y, u, v: v > 0.1)
    t.poly([(2.6, 10), (0, 7), (0, 13)], B2)
    t.poly([(6, 7.2), (9, 7.2), (8, 5.6)], B2)
    t.rect(10, 9, 1, 1, ENCRE)
    t.contour(ENCRE)
    t.rect(13, 0, 1, 7, GRIS)
    t.rect(13, 7, 1, 2, O3)
    return t


def gourmand():
    # Un bol fumant.
    t = T()
    t.ell(8, 9, 6, 6, O3, cond=lambda x, y, u, v: v >= 0)
    t.ell(8, 9, 6, 6, O2, cond=lambda x, y, u, v: v >= 0.55)
    t.rect(2, 8, 12, 1, CREME)
    t.rect(6, 15, 4, 1, O2)
    t.contour(ENCRE)
    for x, y in ((6, 5), (5, 4), (6, 3), (6, 2), (10, 5), (9, 4), (10, 3), (10, 2)):
        t.p(x, y, GRIS)
    return t


def grand_lecteur():
    # Un livre ouvert, un signet orange.
    t = T()
    t.poly([(1, 4), (8, 5.4), (8, 13.4), (1, 12)], CREME)
    t.poly([(15, 4), (8, 5.4), (8, 13.4), (15, 12)], CREME)
    t.poly([(1, 12), (8, 13.4), (15, 12), (15, 13.4), (8, 14.8), (1, 13.4)], V2)
    t.rect(8, 5, 1, 9, CREME_O)
    for y in (7, 9):
        t.ligne(3, y, 6, y + 1, GRIS)
        t.ligne(10, y + 1, 13, y, GRIS)
    t.rect(11, 3, 2, 4, O3)
    t.contour(ENCRE)
    return t


def codeur_au_long_cours():
    # Chevrons et barre oblique : < / >.
    t = T()
    for k in range(2):
        t.ligne(4, 4 + k, 1, 7 + k, B3)
        t.ligne(1, 8 + k, 4, 11 + k, B3)
        t.ligne(11, 4 + k, 14, 7 + k, O3)
        t.ligne(14, 8 + k, 11, 11 + k, O3)
    t.ligne(9, 3, 6, 13, CREME)
    t.ligne(10, 3, 7, 13, CREME)
    t.contour(ENCRE)
    return t


def casanier():
    # Son pot de fleurs, une fleur dedans.
    t = T()
    t.poly([(3, 9), (13, 9), (11.6, 16), (4.4, 16)], O2)
    t.rect(2, 8, 12, 2, O3)
    t.rect(5, 11, 1, 4, O4)
    t.rect(7, 4, 1, 4, T2)
    t.rect(8, 6, 2, 1, T2)
    t.ell(7.5, 2.5, 2.4, 2.4, J3)
    t.rect(7, 2, 1, 1, O3)
    t.contour(ENCRE)
    return t


def voyageur():
    # Le baluchon au bout du bâton.
    t = T()
    t.ligne(1, 15, 9, 5, BR3)
    t.ligne(2, 15, 10, 5, BR2)
    t.ell(10.5, 6, 4.2, 4, O3)
    t.ell(11, 7, 3.2, 2.8, O2, cond=lambda x, y, u, v: v > 0.2)
    for x, y in ((9, 4), (12, 5), (10, 7), (13, 8)):
        t.p(x, y, CREME)
    t.rect(10, 1, 2, 1, O3)
    t.contour(ENCRE)
    return t


def calin():
    # Un cœur.
    t = T()
    t.ell(4.8, 6, 3.2, 3.2, O3)
    t.ell(11.2, 6, 3.2, 3.2, O3)
    t.poly([(1.9, 7.2), (14.1, 7.2), (8, 14.6)], O3)
    t.ell(10.6, 8.2, 3.6, 4.6, O2, cond=lambda x, y, u, v: u > 0.25 and t.get(x, y) == O3)
    t.rect(4, 4, 2, 1, O4)
    t.rect(4, 5, 1, 1, O4)
    t.contour(ENCRE)
    return t


def tete_en_l_air():
    # La tête dans les nuages : un nuage de pensée et ses trois bulles qui montent.
    t = T()
    t.ell(6, 5.5, 3.6, 3.2, CREME)
    t.ell(10.4, 4.6, 3.4, 3.4, CREME)
    t.ell(8.2, 7, 5.6, 2.4, CREME)
    t.rect(4, 8, 8, 1, CREME_O)
    t.ell(6, 11.5, 1.5, 1.5, CREME)
    t.rect(3, 14, 1, 1, CREME)
    t.contour(ENCRE)
    return t


def siffloteur():
    # Deux croches liées.
    t = T()
    t.rect(5, 2, 8, 2, V3)
    t.rect(5, 2, 1, 10, V3)
    t.rect(12, 2, 1, 9, V3)
    t.ell(4, 12, 2.4, 2, V3)
    t.ell(11, 11, 2.4, 2, V3)
    t.rect(3, 11, 1, 1, V4)
    t.rect(10, 10, 1, 1, V4)
    t.contour(ENCRE)
    return t


def bon_joueur():
    # Un dé, face cinq.
    t = T()
    t.rect(3, 2, 10, 12, CREME)
    t.rect(2, 3, 12, 10, CREME)
    t.rect(3, 13, 10, 1, CREME_O)
    t.rect(13, 3, 1, 10, CREME_O)
    for x, y in ((4, 4), (10, 4), (7, 7), (4, 10), (10, 10)):
        t.rect(x, y, 2, 2, B1)
    t.contour(ENCRE)
    return t


def bon_voisin():
    # Une petite maison, la porte ouverte.
    t = T()
    t.rect(3, 8, 10, 7, CREME)
    t.rect(3, 14, 10, 1, CREME_O)
    t.poly([(8, 1.6), (15, 8.6), (1, 8.6)], O3)
    t.poly([(8, 5), (11.6, 8.6), (4.4, 8.6)], O2)
    t.rect(7, 11, 3, 4, B2)
    t.rect(9, 13, 1, 1, J3)
    t.rect(11, 2, 2, 3, BR2)
    t.contour(ENCRE)
    return t


def douillet():
    # Trois bulles de savon et un éclat.
    t = T()
    for cx, cy, r in ((6, 9.5, 4.6), (12, 4.5, 2.6), (12.5, 12.5, 2)):
        t.ell(cx, cy, r, r, B4)
        t.ell(cx, cy, r - 1, r - 1, B3)
    t.rect(4, 7, 2, 1, CREME)
    t.rect(4, 8, 1, 1, CREME)
    t.rect(11, 3, 1, 1, CREME)
    t.contour(ENCRE)
    etoile(t, 2, 3, J3, J4)
    return t


def flaneur():
    # Un parasol rayé planté dans le sable.
    t = T()
    t.rect(8, 6, 1, 9, BR2)
    t.ell(8.5, 8, 7, 6.4, O3, cond=lambda x, y, u, v: v <= 0)
    t.ell(8.5, 8, 7, 6.4, CREME, cond=lambda x, y, u, v: v <= 0 and (abs(u) < 0.2 or 0.56 < abs(u) < 0.86))
    t.rect(8, 0, 1, 1, O2)
    t.rect(3, 15, 11, 1, S2)
    t.contour(ENCRE)
    return t


def amateur_d_histoires():
    # Une lettre cachetée : les aventures arrivent par courrier.
    t = T()
    t.rect(1, 4, 14, 9, CREME)
    t.rect(1, 12, 14, 1, CREME_O)
    t.ligne(1, 4, 7, 9, GRIS)
    t.ligne(14, 4, 8, 9, GRIS)
    t.ell(8, 9.5, 2.2, 2.2, O3)
    t.rect(7, 9, 1, 1, O4)
    t.contour(ENCRE)
    return t


def barbouilleur():
    # Un pinceau trempé d'encre bleue, et sa tache.
    t = T()
    t.ligne(14, 1, 8, 7, BR3)
    t.ligne(15, 2, 9, 8, BR2)
    t.rect(7, 7, 2, 2, ARGENT)
    t.poly([(4.4, 9), (7.6, 8.4), (8.6, 9.4), (8, 12.6), (3, 13.6)], B3)
    t.rect(5, 11, 1, 1, B4)
    t.contour(ENCRE)
    t.ell(4.5, 14.6, 3.6, 1.2, B2)
    t.rect(10, 14, 2, 1, B2)
    return t


def bon_public():
    # Un écran, et le triangle de lecture.
    t = T()
    t.rect(1, 2, 14, 10, ARDOISE)
    t.rect(2, 3, 12, 8, B1)
    t.poly([(6, 4.6), (11, 7), (6, 9.4)], O3)
    t.rect(7, 12, 2, 2, GRIS)
    t.rect(4, 14, 8, 1, GRIS)
    t.contour(ENCRE)
    return t


def veinard():
    # Un fer à cheval doré et son étincelle.
    t = T()
    t.ell(8, 8, 6, 6.4, J3, cond=lambda x, y, u, v: u * u + v * v > 0.3 and not (v > 0.35 and abs(u) < 0.42))
    t.ell(8, 8, 6, 6.4, J2, cond=lambda x, y, u, v: u > 0.45 and t.get(x, y) == J3)
    for x, y in ((3, 6), (4, 3), (11, 3), (12, 6)):
        t.rect(x, y, 1, 1, J1)
    t.contour(ENCRE)
    etoile(t, 8, 12, J4)
    return t


def chineur():
    # Une étiquette de brocante, au bout de sa ficelle.
    t = T()
    t.poly([(6, 5), (15, 5), (15, 14), (6, 14), (2, 9.5)], S3)
    t.poly([(6, 13), (15, 13), (15, 14), (6, 14), (5.2, 13)], S2)
    t.ell(5.5, 9.5, 1.2, 1.2, ENCRE)
    etoile(t, 11, 9, O3, O4)
    t.contour(ENCRE)
    t.ligne(5, 9, 2, 4, GRIS)
    t.ligne(2, 4, 5, 1, GRIS)
    return t


def inconnu():
    # Un trait pas encore découvert : une goutte éteinte, un point d'interrogation. Rien ne dit lequel.
    t = T()
    t.ell(8, 9.4, 5.4, 5.4, ARDOISE)
    t.poly([(8, 0.6), (12.6, 7), (3.4, 7)], ARDOISE)
    t.motif(6, 5, [".###.", "#...#", "...#.", "..#..", "..#..", ".....", "..#.."], {"#": GRIS})
    return t


DESSINS = {
    "couche-tard": couche_tard, "leve-tot": leve_tot, "pecheur-du-dimanche": pecheur_du_dimanche, "gourmand": gourmand,
    "grand-lecteur": grand_lecteur, "codeur-au-long-cours": codeur_au_long_cours, "casanier": casanier, "voyageur": voyageur,
    "calin": calin, "tete-en-l-air": tete_en_l_air, "siffloteur": siffloteur, "bon-joueur": bon_joueur,
    "bon-voisin": bon_voisin, "douillet": douillet, "flaneur": flaneur, "amateur-d-histoires": amateur_d_histoires,
    "barbouilleur": barbouilleur, "bon-public": bon_public, "veinard": veinard, "chineur": chineur, "inconnu": inconnu,
}


def ids():
    return ["trait-" + k for k in DESSINS]


def tout():
    if toile.FINS is not None:
        toile.FINS.update(ids())
    for k, f in DESSINS.items():
        ecrire("trait-" + k, f(), slot="objet", commentaire="trait de personnalité : " + k)
