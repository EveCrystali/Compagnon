"""Le fond du jardin de Pilou (docs/LORE.md : « il dort sous un pot de fleurs au fond du jardin ») : le lieu des scènes
d'évolution (assets/evolutions.txt, docs/SCENES.md). Trois heures pour trois évolutions : le matin (Pilou, niveau 10),
le soir (Pilou Nimbus, 25), la nuit étoilée (Pilou Astral, 40). Même jardin, même pot-cabane, autre lumière.

Grille 1× de 96 × 40 comme tous les décors de campagne ; identifiants `decor-evolution-fond-du-jardin-<heure>`.
Palette de Petit Nuage (decors_nuage.py) : les mêmes verts sarcelle, la même terre cuite. Jamais de rouge contre vert :
les fleurs sont pêche, prune, crème et or.
"""
import math

import decors_campagnes as dc
from decors_campagnes import decor
from peinture import degrade, relief, semis, ell, poly, rect, point, trait, hline, vline, nuage, etoile4, hasard
from decors_nuage import (PAL, C1, C2, C3, C4, SO1, SO2, SO3, SO4, AU1, AU2, NE2, NE3, NE4, H1, H2, H3, H4, P3, P4,
                          TE1, TE2, TE3, B1, B2, B3, M1, M2, L1, L2, L3, ENCRE, NU1, NU2, RO1, RO2)


def pot_cabane(t, x, base, nuit=False):
    """Le pot de fleurs renversé, la cabane de Pilou : terre cuite, bord épais posé dans l'herbe, trou d'écoulement en
    haut, petite porte en arche (allumée la nuit). x : le milieu ; base : la ligne de l'herbe."""
    h = 9.5
    poly(t, [(x - 3.5, base - h), (x + 3.5, base - h), (x + 5.5, base - 2), (x - 5.5, base - 2)], RO2)
    poly(t, [(x + 1.5, base - h), (x + 3.5, base - h), (x + 5.5, base - 2), (x + 3, base - 2)], RO1)
    trait(t, x - 2.4, base - h + 0.9, x - 3.8, base - 3, M2, ep=1)
    rect(t, x - 6.5, base - 2, 13, 2, RO2)
    rect(t, x + 3.5, base - 2, 3, 2, RO1)
    hline(t, x - 6.5, x + 6.5, base - 2, RO1)
    hline(t, x - 6, x + 3, base - 1.5, M2)
    ell(t, x, base - h + 0.1, 1.2, 0.5, B1)
    ell(t, x - 0.6, base, 1.6, 2.8, L2 if nuit else B1, cond=lambda a, b, u, v: b <= base)
    point(t, x + 0.2, base - 1.2, M1)


def _jardin(t, k, heure):
    nuit = heure == "nuit"
    # Le ciel, selon l'heure.
    if heure == "matin":
        degrade(t, 0, 30, [C1, C2, C3, AU2, SO4])
        ell(t, 18, 21, 5, 5, L3)
        nuage(t, 64, 6, 18, 2.6, NE4, NE4, NE3)
        nuage(t, 86, 11, 10, 2, NE4, NE4, AU1)
    elif heure == "soir":
        degrade(t, 0, 30, [SO1, SO2, SO3, SO4, AU2])
        ell(t, 78, 22, 6, 6, L1)
        ell(t, 78, 22, 4.5, 4.5, L2)
        nuage(t, 30, 7, 22, 2.4, SO3, AU2, SO2)
        nuage(t, 60, 12, 12, 1.8, SO3, AU2, SO2)
    else:
        degrade(t, 0, 30, [NU1, NU2, SO1])
        semis(t, lambda x, y: y < 20, [NE3, NE4, NE2], 0.035, graine=81)
        for i in range(6):
            etoile4(t, 6 + hasard(i, 1, 82) * 84, 2 + hasard(i, 2, 82) * 12, NE4 if (i + k) % 3 else L3, r=1)
        ell(t, 80, 7, 3.4, 3.4, NE4)
        ell(t, 81.4, 6.2, 3.0, 3.0, NU2)                                     # un croissant
    haie = {"matin": (H1, H2), "soir": (SO1, H1), "nuit": (ENCRE, NU2)}[heure]
    # La haie du fond, ronde, et la barrière de bois devant.
    for i in range(14):
        x = i * 7.2 + hasard(i, 3, 83) * 3
        ell(t, x, 23, 5 + hasard(i, 4, 83) * 2, 4.5 + hasard(i, 5, 83) * 2, haie[i % 2])
    bois = TE2 if not nuit else B2
    hline(t, 0, 96, 22, bois)
    hline(t, 0, 96, 24.5, bois)
    for x in range(2, 96, 6):
        vline(t, x, 20.5, 27, bois)
        point(t, x, 20.5, TE3 if not nuit else B3)
    # L'herbe, qui descend vers nous.
    sol = {"matin": (H2, H4), "soir": (H1, SO2), "nuit": (NU2, H1)}[heure]
    relief(t, lambda x: 26.5 + 0.5 * math.sin(x / 6), sol[0], lisere=sol[1])
    semis(t, lambda x, y: y > 28, [H3 if not nuit else H1, H4 if heure == "matin" else H2], 0.05, graine=84)
    # Les fleurs : roses trémières contre la barrière, et un petit massif à droite.
    fleurs = [P4, SO3, AU2, L2] if not nuit else [SO2, NE2, SO1]
    for i in range(7):
        x = 50 + i * 6.5 + hasard(i, 6, 85) * 2
        haut = 10 + hasard(i, 7, 85) * 5
        vline(t, x, 27 - haut, 28, H1 if not nuit else NU2)
        for j in range(4):
            ell(t, x + (0.6 if j % 2 else -0.6), 27 - haut + 1 + j * 2.2, 1.2, 1, fleurs[(i + j) % len(fleurs)])
    for i in range(9):
        x, y = 70 + hasard(i, 8, 85) * 24, 32 + hasard(i, 9, 85) * 5
        ell(t, x, y, 1.1, 0.9, fleurs[i % len(fleurs)])
        point(t, x, y, P3 if not nuit else NE3)
    # Le pot-cabane de Pilou, et le petit chemin de cailloux qui y mène.
    for i in range(6):
        ell(t, 22 + i * 3.4, 38.5 - i * 0.2, 1.3, 0.6, NE3 if not nuit else SO1)
    pot_cabane(t, 30, 36.5, nuit)
    # La nuit : des lucioles dans l'herbe, qui changent d'une image à l'autre.
    if nuit:
        for i in range(8):
            if (i + k) % 2:
                point(t, 6 + hasard(i, 10, 86) * 88, 27 + hasard(i, 11, 86) * 10, L3)


@decor("evolution", "fond-du-jardin-matin", images=2, duree=1300)
def fond_matin(t, k):
    _jardin(t, k, "matin")


@decor("evolution", "fond-du-jardin-soir", images=2, duree=1300)
def fond_soir(t, k):
    _jardin(t, k, "soir")


@decor("evolution", "fond-du-jardin-nuit", images=2, duree=1300)
def fond_nuit(t, k):
    _jardin(t, k, "nuit")
