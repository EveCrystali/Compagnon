"""Tenues de voyage des campagnes (docs/CAMPAGNES.md) : Pilou « occupé » pendant une attente.

Appelé par generer.py. Huit tenues (assets/tenues.txt, « voyage-<mode> ») : marche, course, bateau, grimpe, nage,
nuit, cache, attend. La pose que chaque mode impose (pas sur place, tangage, guet…) est dans le rendu commun
(`voyager` : rendu.py, RenduPilou.cs, RenduPilou.java). Les dessins sont faits de formes (ellipses, polygones,
lignes) : rejoués sur la toile fine, ils donnent directement leur version 2× ; ce qui est sous `toile.fin()` ajoute
les détails que seule la grille fine peut porter.
"""
import math

import toile
from toile import Toile, ecrire
from boutique_sprites import (ENCRE, NOIR2, BLANC, CREME, CREME_O, GRIS, GRIS_C, ARDOISE, ARGENT, ARGENT_C, B1, B2, B3, B4,
                              NUIT, NUIT2, O1, O2, O3, O4, O5, J1, J2, J3, J4, V1, V2, V3, V4, S1, S2, S3, BR1, BR2, BR3,
                              T1, T2, T3)

TENUES = {
    "voyage-marche": ["voyage-baluchon", "voyage-baton"],
    "voyage-course": ["voyage-bandeau", "voyage-foulee"],
    "voyage-bateau": ["voyage-barque", "voyage-rame", "voyage-vagues"],
    "voyage-grimpe": ["voyage-corde", "voyage-prises"],
    "voyage-nage": ["voyage-bouee", "voyage-brasse", "voyage-vagues"],
    "voyage-nuit": ["tenue-nuit-bonnet", "voyage-couverture", "voyage-lune"],
    "voyage-cache": ["voyage-buisson"],
    "voyage-attend": ["voyage-montre"],
}

MAIN, MAIN_O, MAIN_C = "@base", "@ombre", "@contour"


def T(w, h):
    return Toile(w, h)


def moufle(t, cx, cy, r=2.2):
    """Petite main ronde à la teinte de Pilou."""
    t.ell(cx, cy, r + 1, r + 1, MAIN_C)
    t.ell(cx, cy, r, r, MAIN_O)
    if toile.fin():
        t.ell(cx - 0.5, cy - 0.6, r * 0.45, r * 0.45, MAIN)


# ---- Marche : baluchon sur l'épaule, bâton de marche
def marche():
    images = []
    for k in range(2):
        t = T(14, 28)
        # Bâton du baluchon : tenu contre le flanc gauche, il monte derrière l'épaule.
        t.ligne(9, 26, 6, 9 + k, BR2)
        t.ligne(10, 26, 7, 9 + k, BR3)
        # Baluchon : toile nouée, pois clairs.
        cy = 7 + k
        t.ell(6.5, cy, 5.5, 5, O2)
        t.ell(5.8, cy - 0.8, 4.2, 3.6, O3)
        t.poly([(7, cy - 4), (11, cy - 7), (10, cy - 3)], O3)      # oreilles du nœud
        t.poly([(6, cy - 4), (3, cy - 7), (8, cy - 5)], O2)
        pois = ((3, cy - 1), (7, cy + 1), (4, cy + 2), (8, cy - 2))
        for (x, y) in pois:
            t.p(x, y, O5)
        if toile.fin():
            # Plis de la toile vers le nœud, reflet, pois ronds.
            for (x, y) in pois:
                t.ell(x + 0.5, y + 0.5, 0.8, 0.8, O5)
            t.ligne(7.5, cy - 3.5, 6.5, cy - 1.5, O1)
            t.ell(3.5, cy - 2.2, 1.4, 0.7, O4)
        t.contour(ENCRE)
        images.append(t)
    ecrire("voyage-baluchon", images, slot="dos", ancre="main-g", point=(9, 26), couche="derriere", duree=160,
           commentaire="Tenue de voyage « marche » : baluchon sur l'épaule (il sautille au rythme du pas)")

    images = []
    for k in range(2):
        t = T(12, 26)
        # Bâton de marche : de la main (4, 10) au sol, il avance d'un pas sur deux.
        x_bas = 7 + 2 * k
        t.ligne(3, 1, x_bas, 24, BR2)
        t.ligne(4, 1, x_bas + 1, 24, BR3)
        t.rect(2, 0, 4, 2, BR1)                       # pommeau
        if toile.fin():
            t.ligne(4.5, 3, 4.5 + (x_bas - 3) * 0.3, 9, S2)   # reflet du bois
            t.rect(x_bas, 23.5, 2, 1, ARGENT)              # embout ferré
        t.contour(ENCRE)
        moufle(t, 4.5 + (x_bas - 3) * 0.4, 10.5)
        images.append(t)
    ecrire("voyage-baton", images, slot="main", ancre="main", point=(5, 11), duree=160,
           commentaire="Tenue de voyage « marche » : bâton de marche")


# ---- Course : bandeau au vent, foulée
def course():
    images = []
    for k in range(2):
        t = T(44, 12)
        # Bandeau : il suit la courbe du front (ellipse du corps), entre 3 et 6 pixels sous le sommet.
        t.ell(26, 14.4, 16.2, 13.4, O3, cond=lambda x, y, u, v: 4 <= y <= 6)
        t.ell(26, 14.4, 16.2, 13.4, BLANC, cond=lambda x, y, u, v: y == 5)
        # Nœud et deux pans qui flottent vers l'arrière.
        t.ell(11.5, 6.5, 2, 2, O2)
        if k == 0:
            t.poly([(10, 5), (1, 2), (2, 5), (10, 7)], O3)
            t.poly([(10, 7), (3, 8), (4, 11), (11, 8)], O2)
        else:
            t.poly([(10, 5), (1, 4), (3, 7), (10, 7)], O3)
            t.poly([(10, 7), (2, 10), (5, 11), (11, 8)], O2)
        if toile.fin():
            t.ell(11.2, 6.2, 0.9, 0.9, O4)
            t.ligne(9, 6, 4, 4 + k, O1)                    # pli du pan
        t.contour(ENCRE)
        images.append(t)
    ecrire("voyage-bandeau", images, slot="tete", ancre="tete", point=(26, 1), duree=140,
           commentaire="Tenue de voyage « course » : bandeau noué, pans au vent")

    images = []
    for k in range(3):
        t = T(14, 16)
        # Traits de vitesse derrière lui et petits nuages de poussière au sol.
        for i, (y, l) in enumerate(((1, 7), (5, 9), (9, 6))):
            x0 = (k * 2 + i * 2) % 5
            t.rect(x0, y, l - x0, 1, CREME_O)
        t.ell(10 - 3 * k, 13.5 - 0.5 * k, 2.5 - 0.3 * k, 1.8, CREME_O)
        t.ell(5 - k, 14, 1.6, 1.2, GRIS_C)
        if toile.fin():
            t.ell(9.5 - 3 * k, 13 - 0.5 * k, 1.2, 0.8, CREME)
        images.append(t)
    ecrire("voyage-foulee", images, slot="effet", ancre="pieds", point=(24, 14), duree=90,
           commentaire="Tenue de voyage « course » : traits de vitesse et poussière")


# ---- Bateau : petite barque, rame, vagues
def vagues():
    images = []
    for k in range(4):
        t = T(48, 6)
        t.rect(0, 2, 48, 4, B2)
        t.rect(0, 4, 48, 2, B1)
        for x in range(48):
            # Crête : une ondulation qui avance.
            h = math.sin((x + k * 3) * math.pi / 6)
            if h > 0.3:
                t.p(x, 1, B3)
            if h > 0.85:
                t.p(x, 0, B4)
                t.p(x, 1, BLANC)
            if (x + k * 2) % 9 == 0:
                t.rect(x, 3, 3, 1, B3)
        if toile.fin():
            for x in range(0, 48, 12):
                t.rect(x + (k * 3) % 12 + 0.5, 4.5, 2.5, 0.5, B2)   # reflets fins dans l'eau profonde
        images.append(t)
    ecrire("voyage-vagues", images, slot="effet", ancre="aucun", point=(0, -50), duree=260,
           commentaire="Tenues de voyage « bateau » et « nage » : l'eau, au premier plan")


def bateau():
    t = T(46, 14)
    # Coque : planches brunes, proue relevée à droite, liston clair.
    t.poly([(1, 3), (45, 1), (41, 12), (6, 12), (1, 3)], BR2)
    t.poly([(1, 3), (45, 1), (44.3, 3.4), (1.5, 5)], BR3)
    t.ligne(3, 7, 43, 6, BR1)
    t.ligne(5, 10, 41, 9, BR1)
    t.poly([(41, 0), (46, 0), (45, 2), (41, 2)], BR3)        # tête de proue
    if toile.fin():
        t.ligne(2, 3.5, 44, 1.5, S2)                           # liston : filet clair
        for x in (10, 19, 28, 37):
            t.ligne(x, 5, x - 0.5, 11.5, BR1)                  # joints des planches
            t.p(x + 0.5, 6.5, S2)                               # clous
        t.ell(8, 8.5, 2, 1, BR3)
    t.contour(ENCRE)
    ecrire("voyage-barque", t, slot="dos", ancre="pieds", point=(23, 10),
           commentaire="Tenue de voyage « bateau » : petite barque (devant Pilou assis)")

    images = []
    for k in range(4):
        t = T(18, 22)
        # Rame : de la main (5, 4) à l'eau ; la pale décrit un petit cercle.
        px = 12 + (1, 3, 1, -1)[k]
        py = 17 + (0, 1, 2, 1)[k]
        t.ligne(3, 1, px, py, S2)
        t.ligne(4, 1, px + 1, py, S1)
        t.ell(px + 1, py + 2, 2.6, 3.2, BR3)
        t.ell(px + 0.6, py + 1.6, 1.4, 2, S2)
        if toile.fin():
            t.ligne(px + 1, py, px + 1, py + 4, BR1)            # nervure de la pale
        t.contour(ENCRE)
        moufle(t, 5, 4.5)
        images.append(t)
    ecrire("voyage-rame", images, slot="main", ancre="main", point=(5, 5), duree=260,
           commentaire="Tenue de voyage « bateau » : rame")


# ---- Grimpe : corde, mains qui se hissent
def grimpe():
    t = T(4, 56)
    for y in range(56):
        t.rect(1, y, 2, 1, S2 if (y // 2) % 2 == 0 else S1)
        if toile.fin():
            # Torons : un filet clair en biais tous les deux pixels.
            t.pf(2 + (y * 2) % 4 // 2, y * 2, S3)
            t.pf(3 + (y * 2 + 1) % 4 // 2, y * 2 + 1, S3)
    for y in (9, 31, 50):
        t.rect(0, y, 4, 3, S1)                                 # nœuds
        t.rect(1, y + 1, 2, 1, S3)
    t.contour(ENCRE)
    ecrire("voyage-corde", t, slot="dos", ancre="aucun", point=(-36, 0), couche="derriere",
           commentaire="Tenue de voyage « grimpe » : corde à nœuds (derrière Pilou)")

    images = []
    for k in range(2):
        t = T(10, 16)
        # Deux mains sur la corde, l'une au-dessus de l'autre ; elles alternent.
        t.rect(4, 0, 2, 16, S2)
        haute, basse = (3, 10) if k == 0 else (5, 12)
        moufle(t, 5, haute)
        moufle(t, 5, basse)
        t.rect(4, 0, 2, haute - 3, S2)
        if toile.fin():
            for y in range(0, (haute - 3) * 2, 2):
                t.pf(9 + (y % 4) // 2, y, S3)
        images.append(t)
    ecrire("voyage-prises", images, slot="main", ancre="tete", point=(-9, 0), duree=420,
           commentaire="Tenue de voyage « grimpe » : les mains sur la corde")


# ---- Nage : bouée, bras qui brassent
def nage():
    t = T(42, 12)
    # Bouée : anneau vu de face, quartiers orange et crème.
    t.ell(21, 6, 20, 5.2, O3)
    for x in range(42):
        for y in range(12):
            if t.get(x, y) == O3 and ((x + 3) // 7) % 2 == 0:
                t.p(x, y, CREME)
    t.ell(21, 3.2, 15, 2.2, O2, cond=lambda x, y, u, v: v < 0.2)   # bord intérieur, dans l'ombre
    if toile.fin():
        t.ell(21, 8.2, 16, 1.3, O4, cond=lambda x, y, u, v: ((x + 3) // 7) % 2 == 1)     # reflet sur le boudin
        t.ell(21, 8.2, 16, 1.3, BLANC, cond=lambda x, y, u, v: ((x + 3) // 7) % 2 == 0)
        for x in range(4, 42, 7):
            t.ligne(x, 2.5, x - 0.5, 10, O1)                       # coutures des quartiers
    t.contour(ENCRE)
    ecrire("voyage-bouee", t, slot="dos", ancre="cou", point=(21, 2),
           commentaire="Tenue de voyage « nage » : bouée")

    images = []
    for k in range(2):
        t = T(48, 10)
        # Deux mains qui brassent de part et d'autre, et quelques gouttes.
        ya, yb = (5, 3) if k == 0 else (3, 5)
        moufle(t, 4, ya)
        moufle(t, 43, yb)
        for (x, y) in ((1, ya - 4), (7, ya - 3), (46, yb - 4), (40, yb - 3)):
            t.p(x, y, B4)
            if toile.fin():
                t.ell(x + 0.5, y + 0.5, 0.7, 0.9, B4)
                t.p(x + 0.5, y, BLANC)
        images.append(t)
    ecrire("voyage-brasse", images, slot="main", ancre="cou", point=(24, 0), duree=450,
           commentaire="Tenue de voyage « nage » : les mains qui brassent")


# ---- Nuit : couverture, lune
def nuit():
    t = T(44, 12)
    # Couverture en patchwork, bord ondulé, remontée jusqu'au menton.
    t.poly([(2, 4), (8, 2), (15, 4), (22, 2), (29, 4), (36, 2), (42, 4), (44, 12), (0, 12)], V2)
    for x in range(44):
        for y in range(12):
            if t.get(x, y) == V2:
                cx, cy = x // 6, (y + 2) // 5
                if (cx + cy) % 2 == 0:
                    t.p(x, y, V3 if (cx * 3 + cy) % 4 else B2)
    t.poly([(2, 4), (8, 2), (15, 4), (22, 2), (29, 4), (36, 2), (42, 4), (42.4, 6), (36, 4), (29, 6), (22, 4), (15, 6), (8, 4),
            (1.6, 6)], CREME)
    if toile.fin():
        for x in range(6, 44, 6):
            for y in range(7, 12, 2):
                t.pf(x * 2, y * 2, V1)                              # coutures en pointillé
        for y in (8,):
            for x in range(1, 44, 2):
                t.pf(x * 2, y * 2 - 1, V1)
        t.poly([(2, 5), (8, 3), (15, 5), (22, 3), (29, 5), (36, 3), (42, 5), (42, 5.5), (36, 3.5), (29, 5.5), (22, 3.5),
                (15, 5.5), (8, 3.5), (2, 5.5)], CREME_O)            # ourlet
    t.contour(ENCRE)
    ecrire("voyage-couverture", t, slot="cou", ancre="pieds", point=(22, 6),
           commentaire="Tenue de voyage « nuit » : couverture en patchwork")

    images = []
    for k in range(3):
        t = T(20, 16)
        # Croissant de lune et trois étoiles qui scintillent tour à tour.
        t.ell(13, 6, 5, 5, J3)
        t.ell(11, 4.6, 4.4, 4.4, None)
        if toile.fin():
            t.ell(14.6, 8, 1, 1, J2)                              # cratères
            t.ell(16, 5.5, 0.6, 0.6, J2)
            t.ell(13, 6, 5, 5, J4, cond=lambda x, y, u, v: u * u + v * v > 0.72 and u > 0.2)
            t.ell(11, 4.6, 4.4, 4.4, None)
        t.contour(J1)
        for i, (x, y) in enumerate(((3, 3), (7, 11), (17, 13))):
            grande = (i == k)
            t.p(x, y, J4)
            if grande:
                for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    t.p(x + a, y + b, J3)
                if toile.fin():
                    t.pf(x * 2 + 4, y * 2, J3)
                    t.pf(x * 2 - 3, y * 2 + 1, J3)
                    t.pf(x * 2, y * 2 + 4, J3)
                    t.pf(x * 2 + 1, y * 2 - 3, J3)
        images.append(t)
    ecrire("voyage-lune", images, slot="effet", ancre="aucun", point=(-27, -1), duree=700,
           commentaire="Tenue de voyage « nuit » : lune et étoiles")


# ---- Cache : buisson derrière lequel il guette
def cache():
    images = []
    for k in range(2):
        t = T(48, 20)
        # Buisson : touffes rondes, bleu sarcelle (jamais de vert), quelques baies orange.
        touffes = [(8, 9, 6, 6), (15, 6, 7, 6), (24, 8, 8, 6), (33, 6, 7, 6), (40, 9, 6, 6), (11, 14, 9, 6), (24, 14, 12, 7),
                   (37, 14, 9, 6)]
        for i, (cx, cy, rx, ry) in enumerate(touffes):
            dy = (1 if (i + k) % 2 == 0 and i < 5 else 0) * 0.6
            t.ell(cx, cy + dy, rx, ry, T1)
        for i, (cx, cy, rx, ry) in enumerate(touffes):
            dy = (1 if (i + k) % 2 == 0 and i < 5 else 0) * 0.6
            t.ell(cx - 0.8, cy - 1 + dy, rx - 1.6, ry - 1.8, T2)
        for i, (cx, cy, rx, ry) in enumerate(touffes[:5]):
            dy = (1 if (i + k) % 2 == 0 else 0) * 0.6
            t.ell(cx - 2, cy - 2.6 + dy, 2.2, 1.3, T3)
        for (x, y) in ((8, 12), (20, 15), (31, 12), (40, 16), (15, 17)):
            t.rect(x, y, 2, 2, O3)
            t.p(x, y, O5)
        if toile.fin():
            # Feuilles : petites virgules claires et sombres, baies rondes.
            for i in range(26):
                x, y = (i * 37) % 44 + 2, (i * 23) % 13 + 5
                if t.get(x, y) == T2:
                    t.pf(x * 2, y * 2, T3)
                    t.pf(x * 2 + 1, y * 2 + 1, T3)
                    t.pf(x * 2 + 2, y * 2 + 1, T1)
            for (x, y) in ((8, 12), (20, 15), (31, 12), (40, 16), (15, 17)):
                t.ell(x + 1, y + 1, 1.2, 1.2, O3)
                t.ell(x + 0.6, y + 0.6, 0.45, 0.45, O5)
                t.pf(x * 2 + 3, y * 2 + 3, O1)
        t.contour(ENCRE)
        images.append(t)
    ecrire("voyage-buisson", images, slot="effet", ancre="aucun", point=(0, -38), duree=900,
           commentaire="Tenue de voyage « cache » : buisson (devant Pilou, seuls les yeux dépassent)")


# ---- Attend : montre de gousset
def attend():
    images = []
    for k in range(4):
        t = T(16, 18)
        # Boîtier doré, cadran, aiguilles (la trotteuse fait un quart de tour par image).
        t.rect(7, 2, 2, 2, J2)                                  # bélière
        t.ell(8, 9, 5.5, 5.5, J2)
        t.ell(8, 9, 4.5, 4.5, J3)
        t.ell(8, 9, 3.6, 3.6, CREME)
        t.ligne(8, 9, 8, 7, ENCRE)                              # petite aiguille
        fx, fy = ((0, -3), (3, 0), (0, 3), (-3, 0))[k]
        t.ligne(8, 9, 8 + fx * 0.9, 9 + fy * 0.9, O2)           # trotteuse
        if toile.fin():
            for a in range(12):
                x, y = 8 + math.cos(a * math.pi / 6) * 3.1, 9 + math.sin(a * math.pi / 6) * 3.1
                t.pf(round(x * 2 - 0.5), round(y * 2 - 0.5), GRIS if a % 3 else ENCRE)   # graduations
            t.ell(6, 6.6, 1.6, 0.8, J4)                         # reflet du boîtier
            t.ell(8, 9, 0.5, 0.5, ENCRE)
        t.contour(ENCRE)
        moufle(t, 5, 15)
        images.append(t)
    ecrire("voyage-montre", images, slot="main", ancre="cou", point=(19, 6), duree=500,
           commentaire="Tenue de voyage « attend » : montre de gousset qu'il regarde")


def tout():
    marche()
    course()
    vagues()
    bateau()
    grimpe()
    nage()
    nuit()
    cache()
    attend()
