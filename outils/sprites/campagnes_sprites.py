"""Objets exclusifs, souvenirs, vignettes et emblèmes des campagnes (docs/CAMPAGNES.md, docs/SPRITES.md).

- Objets exclusifs portables (`"portable": true` dans campagne.json) : le sprite porte l'identifiant de l'objet,
  son `slot` est l'emplacement de la fiche et son ancre celle de cet emplacement (tete, cou, dos → cou, main).
  Ils se posent sur Pilou aux quatre stades (les ancres suivent le corps).
- Souvenirs : `souvenir-<campagne>-<id>`, petits timbres carrés de 24 × 24 (dentelés, une scène dedans).
- Vignettes : `campagne-<id>`, cartes de 32 × 32 pour la liste des campagnes.
- Emblèmes de ton : `ton-humour` (rond rieur), `ton-mystere` (losange à serrure), `ton-emotion` (cœur),
  `ton-epique` (étoile à pointes), 12 × 12 : la forme dit le ton, la couleur ne fait qu'accompagner.

Tout est dessiné de formes : rejoué sur la toile fine (fin.SERIE), chaque sprite a son dessin 2× natif ; les blocs
`toile.fin()` ajoutent reflets et détails. Palette sans opposition rouge / vert.
"""
import math

import toile
from toile import Toile, ecrire
from peinture import (ell, poly, rect, point, trait, hline, vline, courbe, degrade, relief, etoile4, hasard, nuage,
                      semis)

ENCRE = "#1c2128"
BLANC, CREME, CREME_O = "#ffffff", "#f6f1e4", "#d9cfb8"
GRIS, GRIS_C, ARDOISE = "#768390", "#adbac7", "#3b4654"
ARGENT, ARGENT_C = "#b8c4d2", "#e6ecf2"
B1, B2, B3, B4 = "#1f4f8a", "#4a8fdc", "#6cb6ff", "#b4dbff"
NUIT, NUIT2 = "#0d2a4d", "#16365e"
O1, O2, O3, O4, O5 = "#8a4a1f", "#d9803a", "#f69d50", "#ffc89a", "#ffd8b0"
J1, J2, J3, J4 = "#7a5a10", "#c9a227", "#f5d76e", "#fff6cc"
V1, V2, V3, V4 = "#3a2a7a", "#6a5acd", "#9b8cff", "#d2caff"
S1, S2, S3 = "#8a6e4b", "#c4a77d", "#e8d5b0"
BR1, BR2, BR3 = "#4a2e17", "#7a4b26", "#a86f3c"
T1, T2, T3, T4 = "#0f4a63", "#2689b8", "#3fb8e0", "#a8e4f5"
CU1, CU2, CU3 = "#7a3f1e", "#b8652e", "#e0995a"       # cuivre
RO1, RO2 = "#8a4a1f", "#b8652e"                      # fer rouillé (orange brun)
CIRE1, CIRE2, CIRE3 = "#b8861c", "#e8b23a", "#f8dc7a"
ROSE1, ROSE2 = "#c76f9a", "#f2a8c8"
LAV1, LAV2, LAV3 = "#5c5a9a", "#8a79b8", "#c9bfe8"


def T(w, h):
    return Toile(w, h)


# =====================================================================================================
# Objets exclusifs portables
# =====================================================================================================
def casquette_gardien():
    """Phare : casquette de gardien bleu marine, visière noire vernie, insigne de laiton (un petit phare)."""
    t = T(34, 14)
    t.ell(15, 13, 12, 10, NUIT2, cond=lambda x, y, u, v: v < 0)
    t.ell(15, 13, 12, 10, NUIT, cond=lambda x, y, u, v: v < 0 and u > 0.4)
    rect(t, 3, 9, 24, 3, NUIT)                             # bandeau
    hline(t, 3, 27, 9, B1)
    t.poly([(20, 10.5), (33, 10.5), (32, 13.5), (19, 13.5)], ENCRE)     # visière
    hline(t, 21, 31, 11, ARDOISE)
    # Insigne : un petit phare de laiton dans une couronne.
    t.ell(12, 6.5, 2.6, 2.6, J2)
    rect(t, 11.4, 4.6, 1.2, 3.8, J4)
    rect(t, 11, 4, 2, 0.9 if toile.fin() else 1, J3)
    if toile.fin():
        ell(t, 9.5, 3.2, 3, 1, B1)                      # reflet du drap
        point(t, 12, 4.2, O3)
    t.contour(ENCRE)
    ecrire("casquette-gardien", t, slot="tete", ancre="tete", point=(15, 10), coiffe=True,
           commentaire="Objet exclusif (Le phare éteint) : casquette de gardien")


def corne_de_poche():
    """Phare : petite corne de brume à soufflet, pavillon de laiton."""
    t = T(16, 14)
    rect(t, 1, 6, 5, 5, BR2)                              # soufflet de cuir
    for x in (2, 3.5, 5):
        vline(t, x, 6, 11, BR1)
    t.poly([(6, 7.5), (13, 3), (15, 3), (15, 14), (13, 14), (6, 10)], J2)
    t.poly([(6, 7.5), (13, 3), (15, 3), (15, 6), (6, 8.8)], J3)
    t.ell(14.5, 8.5, 1.2, 5.4, J1)
    if toile.fin():
        trait(t, 7, 8, 13, 4.5, J4, ep=1)
        point(t, 14.4, 5, J4)
    t.contour(ENCRE)
    t.ell(3.5, 12.5, 2, 2, "@contour")
    t.ell(3.5, 12.5, 1.4, 1.4, "@ombre")
    ecrire("corne-de-poche", t, slot="main", ancre="main", point=(3, 8),
           commentaire="Objet exclusif (Le phare éteint) : corne de brume de poche")


def cire_jaune():
    """Phare : petit ciré jaune, porté en pèlerine dans le dos, capuche rabattue."""
    t = T(44, 26)
    # Pèlerine qui s'évase depuis les épaules, ourlet arrondi, capuche rabattue sur la nuque.
    t.poly([(12, 2), (32, 2), (42, 22), (36, 25), (22, 26), (8, 25), (2, 22)], CIRE2)
    t.poly([(12, 2), (17, 2), (10, 25.4), (8, 25), (2, 22)], CIRE1)
    t.poly([(28, 2), (32, 2), (42, 22), (37, 24.8), (33, 25)], CIRE3)
    t.ell(22, 3.5, 11, 4.5, CIRE2, cond=lambda x, y, u, v: v < 0.6)
    t.ell(22, 4.2, 8, 2.6, CIRE1, cond=lambda x, y, u, v: v > -0.2)
    if toile.fin():
        for x in (14, 22, 30):
            trait(t, x, 8, x + (x - 22) * 0.3, 25, CIRE1, ep=1)
        trait(t, 33, 5, 40, 21, CIRE3, ep=1)
        hline(t, 10, 34, 24.5, CIRE1)
    t.contour(J1)
    ecrire("cire-jaune", t, slot="dos", ancre="cou", point=(22, 3), couche="derriere",
           commentaire="Objet exclusif (Le phare éteint) : petit ciré jaune")


def sifflet_lison():
    """Phare : sifflet de laiton au bout d'un cordon bleu."""
    t = T(24, 14)
    for i in range(17):
        u = i / 16
        x = 3 + u * 18
        y = math.sin(u * math.pi) * 5
        point(t, x, y, B2)
        if toile.fin():
            point(t, x + 0.5, y + 0.25, B2)
    rect(t, 8.5, 6, 7, 3.4, J2)
    t.ell(15.5, 7.7, 2.2, 2.2, J2)
    rect(t, 8.5, 6, 7, 1.2, J3)
    rect(t, 10.5, 6, 1.6, 1.2, ENCRE)
    t.ell(8.5, 7.7, 1, 1.7, J1)
    if toile.fin():
        point(t, 15.8, 6.6, J4)
    t.contour(J1)
    ecrire("sifflet-lison", t, slot="cou", ancre="cou", point=(12, 1),
           commentaire="Objet exclusif (Le phare éteint) : sifflet de Lison")


def galet_machoire():
    """Phare : galet gris lissé par la mer, une veine blanche en forme de mâchoire."""
    t = T(12, 10)
    t.ell(6, 5, 5.5, 4.2, GRIS)
    t.ell(5, 4, 4, 2.6, GRIS_C)
    courbe(t, [(2, 5.5), (6, 8), (10, 5)], BLANC, ep=1)
    for x in (4, 6, 8):
        point(t, x, 6.8 if x != 6 else 7.4, BLANC)
    if toile.fin():
        ell(t, 4, 2.8, 1.3, 0.6, ARGENT_C)
    t.contour(ARDOISE)
    t.ell(2.5, 8, 1.8, 1.8, "@contour")
    t.ell(2.5, 8, 1.2, 1.2, "@ombre")
    ecrire("galet-machoire", t, slot="main", ancre="main", point=(2, 7),
           commentaire="Objet exclusif (Le phare éteint) : galet de la Mâchoire")


def eteignoir():
    """Phare : éteignoir de cuivre porté en chapeau pointu, manche et petit anneau."""
    t = T(30, 20)
    t.poly([(7, 18), (23, 18), (16, 2), (14, 2)], CU2)
    t.poly([(7, 18), (12, 18), (15, 2), (14, 2)], CU1)
    t.poly([(18, 18), (23, 18), (16, 2), (15.5, 4)], CU3)
    t.ell(15, 18, 8.5, 1.8, CU1)
    t.ell(15, 2, 1.6, 1.6, CU3)
    t.poly([(22, 12), (29, 9), (29, 11), (22, 14)], CU2)              # manche
    t.anneau(28.5, 8, 1.6, 1.6, CU3, ep=0.8)
    if toile.fin():
        trait(t, 17.5, 5, 20.5, 16, "#f3c08a", ep=1)
    t.contour(ENCRE)
    ecrire("eteignoir", t, slot="tete", ancre="tete", point=(15, 17), coiffe=True,
           commentaire="Objet exclusif (Le phare éteint) : éteignoir de cuivre")


def casserole_chapeau():
    """Petit Nuage : une casserole portée à l'envers en chapeau, le manche sur le côté."""
    t = T(40, 13)
    rect(t, 4, 2, 22, 9, ARGENT)
    rect(t, 4, 2, 5, 9, GRIS_C)
    rect(t, 20, 2, 6, 9, ARGENT_C)
    t.ell(15, 2, 11, 1.6, ARGENT_C)
    rect(t, 3, 10, 24, 2.4, GRIS)                       # le rebord
    hline(t, 3, 27, 10, ARGENT_C)
    t.poly([(26, 4), (39, 2), (39.5, 4), (26, 7)], BR2)
    t.ell(38, 3, 1, 1, BR1)
    if toile.fin():
        for x in (8, 12, 17):
            vline(t, x, 3, 10, ARGENT_C)
        ell(t, 21.5, 6, 1.8, 0.8, GRIS)                 # la bosse
        trait(t, 27, 4.8, 37, 3, BR3, ep=1)
    t.contour(ENCRE)
    ecrire("casserole-chapeau", t, slot="tete", ancre="tete", point=(15, 10), coiffe=True,
           commentaire="Objet exclusif (Petit Nuage) : casserole-chapeau")


def baluchon_cabosse():
    """Petit Nuage : baluchon cabossé dans le dos, toile rapiécée, bâton en travers."""
    t = T(34, 26)
    trait(t, 2, 24, 30, 2, BR2, ep=toile.ECHELLE * 2)
    t.ell(22, 9, 9, 7.5, O2)
    t.ell(21, 8, 7.5, 6, O3)
    t.ell(26, 11, 3, 2.4, O2)                           # la bosse
    rect(t, 17, 7, 4, 4, B2)                             # pièce rapportée
    hline(t, 17, 21, 7, B3)
    t.poly([(26, 3), (30, 0), (29.5, 4)], O3)
    t.poly([(24, 3), (21, 0), (25.5, 4)], O2)
    for (x, y) in ((24, 7), (19, 12), (26, 13)):
        point(t, x, y, O5)
    if toile.fin():
        for x in (17.5, 19.5):
            point(t, x, 9.5, B4)
        trait(t, 24, 4, 23, 8, O1, ep=1)
        ell(t, 18.5, 5.5, 2, 0.8, O4)
    t.contour(ENCRE)
    ecrire("baluchon-cabosse", t, slot="dos", ancre="cou", point=(9, 21), couche="derriere",
           commentaire="Objet exclusif (Petit Nuage) : baluchon cabossé")


def bonnet_de_givre():
    """Petit Nuage : bonnet tricoté bleu pâle, revers blanc, givre en étoiles, pompon de neige."""
    t = T(30, 20)
    t.ell(15, 18, 13, 13, B3, cond=lambda x, y, u, v: v < 0)
    t.ell(15, 18, 13, 13, B2, cond=lambda x, y, u, v: v < 0 and u > 0.45)
    rect(t, 2, 14, 26, 4, ARGENT_C)
    for x in range(3, 28, 3):
        vline(t, x, 14, 18, ARGENT)
    t.ell(15, 4, 3.2, 3.2, BLANC)
    for (x, y) in ((8, 10), (15, 8), (22, 11), (11, 13)):
        etoile4(t, x, y, BLANC, r=0.6 if not toile.fin() else 0.8, coeur=B4)
    if toile.fin():
        for y in (9, 11, 13):
            for x in range(4, 27, 2):
                if hasard(x, y, 3) < 0.4:
                    point(t, x + 0.5, y, B4)
        ell(t, 14, 3, 1.2, 1, ARGENT_C)
    t.contour(B1)
    ecrire("bonnet-de-givre", t, slot="tete", ancre="tete", point=(15, 16), coiffe=True,
           commentaire="Objet exclusif (Petit Nuage) : bonnet de givre")


def caillou_du_col():
    """Petit Nuage : un caillou du col, plat, avec un filet de neige qui ne fond pas."""
    t = T(12, 10)
    t.ell(6, 5, 5, 3.8, V2)
    t.ell(5, 4.2, 3.8, 2.4, V3)
    trait(t, 2.5, 5.5, 9.5, 3.8, BLANC, ep=toile.ECHELLE)
    if toile.fin():
        point(t, 4, 3, V4)
        point(t, 9.5, 3.4, B4)
    t.contour(V1)
    t.ell(2.5, 8, 1.8, 1.8, "@contour")
    t.ell(2.5, 8, 1.2, 1.2, "@ombre")
    ecrire("caillou-du-col", t, slot="main", ancre="main", point=(2, 7),
           commentaire="Objet exclusif (Petit Nuage) : caillou du col")


def echarpe_de_veille():
    """Petit Nuage : longue écharpe lavande à rayures crème, un pan qui tombe, une petite étoile brodée."""
    t = T(34, 20)
    t.ell(17, 2, 15, 4, LAV2, cond=lambda x, y, u, v: v > -0.3)
    t.ell(17, 1, 12, 2.4, LAV2, cond=lambda x, y, u, v: v > 0)
    t.poly([(22, 3), (28, 3), (29, 19), (23, 19)], LAV2)
    for y in (7, 11, 15):
        t.poly([(22.2, y), (28.2, y), (28.3, y + 1.4), (22.4, y + 1.4)], CREME)
    for x in range(23, 29, 2):
        vline(t, x, 19, 20, LAV2)
    for x in range(4, 31, 5):
        vline(t, x, 1, 5, CREME)
    etoile4(t, 25.5, 17, J3, r=0.8)
    if toile.fin():
        for y in range(5, 19, 2):
            point(t, 24, y, LAV1)
            point(t, 27, y + 1, LAV1)
        ell(t, 10, 2, 4, 0.6, LAV3)
    t.contour(LAV1)
    ecrire("echarpe-de-veille", t, slot="cou", ancre="cou", point=(17, 2),
           commentaire="Objet exclusif (Petit Nuage) : écharpe de veille")


def plume_de_girouette():
    """Petit Nuage : une plume de fer rouillé, piquée de côté sur la tête comme une plume de chapeau."""
    t = T(14, 20)
    t.poly([(4, 19), (2, 12), (3, 6), (7, 1), (9, 4), (8, 11), (5, 19)], RO2)
    t.poly([(4, 19), (2, 12), (3, 6), (7, 1), (5, 8), (4.5, 19)], RO1)
    trait(t, 4.5, 19, 7, 2, CU3, ep=1)
    for i in range(5):
        y = 5 + i * 3
        trait(t, 5 + i * 0.1, y + 1, 8 - i * 0.6, y - 0.5, RO1, ep=1)
    if toile.fin():
        for i in range(5):
            point(t, 3 + i * 0.3, 7 + i * 2.6, CU3)
    t.contour(ENCRE)
    ecrire("plume-de-girouette", t, slot="tete", ancre="tete", point=(-2, 18),
           commentaire="Objet exclusif (Petit Nuage) : plume de girouette")


def sablier_de_poche():
    """Grande Panne : petit sablier de laiton en pendentif ; un grain hésite au milieu (quatre secondes de retard)."""
    t = T(24, 16)
    for i in range(17):
        u = i / 16
        point(t, 3 + u * 18, math.sin(u * math.pi) * 5, ARGENT_C)
        if toile.fin():
            point(t, 3.5 + u * 18, math.sin(u * math.pi) * 5 + 0.25, ARGENT_C)
    rect(t, 8, 5, 8, 1.6, J2)
    rect(t, 8, 14, 8, 1.6, J2)
    t.poly([(9, 6.6), (15, 6.6), (12.6, 10.3), (15, 14), (9, 14), (11.4, 10.3)], B4)
    t.poly([(10, 7), (14, 7), (12, 9.4)], S3)
    t.poly([(10.6, 14), (13.4, 14), (12, 12.4)], S3)
    point(t, 12, 10.8, S2)
    vline(t, 8.6, 6.6, 14, J1)
    vline(t, 15.4, 6.6, 14, J1)
    if toile.fin():
        trait(t, 9.8, 7.4, 10.8, 9, BLANC, ep=1)
        hline(t, 8.5, 15.5, 5, J3)
    t.contour(ENCRE)
    ecrire("sablier-de-poche", t, slot="cou", ancre="cou", point=(12, 1),
           commentaire="Objet exclusif (La Grande Panne) : sablier de poche")


EXCLUSIFS = ["casquette-gardien", "corne-de-poche", "cire-jaune", "sifflet-lison", "galet-machoire", "eteignoir",
             "casserole-chapeau", "baluchon-cabosse", "bonnet-de-givre", "caillou-du-col", "echarpe-de-veille",
             "plume-de-girouette", "sablier-de-poche"]


def objets():
    casquette_gardien()
    corne_de_poche()
    cire_jaune()
    sifflet_lison()
    galet_machoire()
    eteignoir()
    casserole_chapeau()
    baluchon_cabosse()
    bonnet_de_givre()
    caillou_du_col()
    echarpe_de_veille()
    plume_de_girouette()
    sablier_de_poche()


# =====================================================================================================
# Souvenirs : timbres dentelés de 24 × 24, une scène de 18 × 18 dedans
# =====================================================================================================
CADRES = {"prologue": (O4, O2), "phare-eteint": (B4, B1), "grande-panne": (V4, V2), "petit-nuage": (ARGENT_C, LAV2)}


def timbre(scene, campagne):
    """Un timbre : bord dentelé (dents rondes), cadre clair, liseré de la couleur de la campagne, la scène."""
    papier, liseré = CADRES[campagne]
    t = T(24, 24)
    rect(t, 0, 0, 24, 24, papier)
    # Dents : des demi-cercles creusés tous les 3 pixels sur les quatre côtés.
    e = t.e
    for i in range(8):
        c = 1.5 + i * 3
        for (cx, cy) in ((c, -0.2), (c, 24.2), (-0.2, c), (24.2, c)):
            for X in range(max(0, int((cx - 1.2) * e)), min(t.W, int((cx + 1.2) * e) + 1)):
                for Y in range(max(0, int((cy - 1.2) * e)), min(t.H, int((cy + 1.2) * e) + 1)):
                    if ((X + 0.5) / e - cx) ** 2 + ((Y + 0.5) / e - cy) ** 2 <= 0.9:
                        t.g[Y][X] = None
    rect(t, 2, 2, 20, 20, liseré)
    s = T(18, 18)
    scene(s)
    t.coller(s, 3, 3)
    if toile.fin():
        hline(t, 3, 21, 21.5, papier)
    return t


def s_coucher(s):
    degrade(s, 0, 12, [V2, ROSE1, O2, O3, O4])
    ell(s, 9, 12, 4, 4, J4, cond=lambda x, y, u, v: y < 12)
    for y in (13, 14.5, 16):
        hline(s, 9 - (17 - y) * 0.9, 9 + (17 - y) * 0.9, y, O4)
    relief(s, lambda x: 12 + 0.05 * (x - 9) ** 2, T1, lisere=O3)
    trait(s, 3, 11, 3, 7.5, BR1, ep=s.e)
    ell(s, 3, 7, 2, 1.6, T1)


def s_question(s):
    degrade(s, 0, 18, [NUIT, NUIT2, V1])
    for (x, y) in ((3, 3), (14, 2), (8, 5), (16, 8)):
        point(s, x, y, B4)
    relief(s, lambda x: 13 + 0.6 * math.sin(x / 2), T1, lisere=B1)
    rect(s, 6, 9, 6, 5, S3)
    poly(s, [(5, 9.2), (9, 6), (13, 9.2)], V1)
    rect(s, 9.5, 10.5, 1.6, 1.6, J3)
    # Le soleil garde son secret : un point d'interrogation d'étoiles.
    courbe(s, [(12.5, 3.5), (15.5, 1.5), (15.5, 5), (13.8, 6.2)], J3, ep=1)
    point(s, 13.8, 7.8, J3)


def phare_mini(s, x, base, h, allume=True, c=ENCRE):
    poly(s, [(x - 1.6, base), (x + 1.6, base), (x + 1, base - h), (x - 1, base - h)], c)
    rect(s, x - 1.3, base - h - 0.8, 2.6, 0.8, c)
    rect(s, x - 0.8, base - h - 2.4, 1.6, 1.6, J4 if allume else c)
    poly(s, [(x - 1.1, base - h - 2.4), (x, base - h - 3.5), (x + 1.1, base - h - 2.4)], c)


def s_tout_le_monde(s):
    degrade(s, 0, 18, [NUIT, NUIT2, B1])
    phare_mini(s, 9, 13, 8)
    for a in (-1, 1):
        poly(s, [(9, 3.5), (9 + a * 9, 1), (9 + a * 9, 6)], "#2f5c8e")
    rect(s, 0, 13, 18, 5, ARDOISE)
    for i, x in enumerate((2, 4.5, 7, 11, 13.5, 16)):
        rect(s, x - 0.6, 12.5, 1.2, 2.5, ENCRE)
        point(s, x, 11.6, O3)
        if s.e == 2:
            point(s, x, 11.3, J4)


def s_deux_eclats(s):
    degrade(s, 0, 18, [NUIT, NUIT2])
    phare_mini(s, 4, 16, 9)
    rect(s, 0, 16, 18, 2, B1)
    for (x, l) in ((8, 1.5), (10.5, 1.5), (13, 4)):
        rect(s, x, 6, l, 1.6, J3)
        if s.e == 2:
            hline(s, x, x + l, 6, J4)


def s_feu_auto(s):
    degrade(s, 0, 18, [B1, B2, B3])
    phare_mini(s, 9, 15, 8, c=ARDOISE)
    for a in range(8):
        r = math.radians(a * 45)
        point(s, 9 + 3.5 * math.cos(r), 4.2 + 3.5 * math.sin(r), ARGENT)
    s.anneau(9, 4.2, 2.6, 2.6, ARGENT, ep=0.8)
    rect(s, 0, 15, 18, 3, ARDOISE)


def s_sursis(s):
    degrade(s, 0, 18, [NUIT, NUIT2])
    rect(s, 3, 6, 4, 6, BR2)
    rect(s, 3.6, 6.8, 2.8, 4.4, J3)
    poly(s, [(2.5, 6), (5, 4), (7.5, 6)], BR2)
    trait(s, 7, 9, 9, 11, ARGENT, ep=s.e)
    for i in range(4):
        vline(s, 10.5 + i * 1.5, 5, 10, CREME)
    trait(s, 10, 9, 15.5, 5.5, CREME, ep=1)
    for (x, y) in ((12, 14), (14.5, 13)):
        ell(s, x, y, 1, 1, ROSE2)
        point(s, x, y, J3)
    rect(s, 0, 15, 18, 3, ARDOISE)


def s_mauvais_coupable(s):
    rect(s, 0, 0, 18, 18, S3)
    ell(s, 7, 7, 4.5, 4.5, BR2)
    ell(s, 7, 7, 3.6, 3.6, B4)
    trait(s, 10, 10, 15, 15, BR1, ep=s.e * 2)
    # La loupe fêlée : elle a regardé le mauvais côté.
    trait(s, 5, 4.5, 8.5, 8.5, BLANC, ep=1)
    trait(s, 8.5, 8.5, 6.8, 10, BLANC, ep=1)
    for (x, y) in ((13, 3), (15, 5)):
        ell(s, x, y, 0.8, 1.1, GRIS)


def s_celui_qui_eteint(s):
    degrade(s, 0, 18, [NUIT, V1])
    rect(s, 7, 10, 4, 6, CREME)
    rect(s, 5, 15.5, 8, 1.5, J2)
    poly(s, [(5.5, 10), (12.5, 10), (9.5, 3), (8.5, 3)], CU2)
    poly(s, [(11.5, 6.5), (16, 4.5), (16, 5.6), (11.8, 7.8)], CU2)
    for i in range(3):
        ell(s, 3 + i * 0.4, 3 + i * 2.2, 0.8, 0.8, J3)


def s_point_final(s):
    rect(s, 0, 0, 18, 18, BLANC)
    for y in (3, 5.5, 8, 10.5):
        hline(s, 2, 15 if y < 10 else 9, y, GRIS_C)
    ell(s, 11, 10.6, 1.4, 1.4, ENCRE)
    rect(s, 10, 12.5, 7, 5, V2)
    rect(s, 11.5, 12.5, 4, 2, ARGENT_C)
    rect(s, 11.5, 15.4, 4, 2.1, V1)


def s_registre(s):
    degrade(s, 0, 18, [B3, B4])
    poly(s, [(4, 7), (14, 7), (13, 16), (5, 16)], GRIS)
    rect(s, 3.5, 5.5, 11, 1.6, GRIS_C)
    for x in (7, 9, 11):
        vline(s, x, 8, 15, ARDOISE)
    poly(s, [(5, 3), (13, 3), (14, 5.5), (4, 5.5)], CREME)
    vline(s, 9, 3, 5.5, S2)


def s_page_bleue(s):
    rect(s, 0, 0, 18, 18, V4)
    poly(s, [(3, 2), (15, 2), (15, 16), (3, 16)], BLANC)
    for y in (4.5, 7, 9.5):
        hline(s, 5, 13, y, B2)
    hline(s, 5, 9, 12, B2)
    point(s, 11, 12, B3)


def s_panneau(s):
    rect(s, 0, 0, 18, 18, GRIS)
    for y in range(1, 18, 2):
        hline(s, 0, 18, y, GRIS_C)
    vline(s, 9, 0, 6, ARDOISE)
    rect(s, 3, 6, 12, 7, BLANC)
    import decors_panne
    for i, ch in enumerate("38"):
        decors_panne.chiffre(s, 9.6 + i * 2.6, 7.6, ch, O1, l=1.6, h=3.6, ep=1)
    decors_panne.chiffre(s, 4.4, 7.6, "1", B1, l=1.6, h=3.6, ep=1)
    decors_panne.chiffre(s, 6.4, 7.6, "3", B1, l=1.6, h=3.6, ep=1)
    point(s, 8.6, 9, ENCRE)


def s_demi_tic(s):
    rect(s, 0, 0, 18, 18, V3)
    ell(s, 8, 10, 6.5, 6.5, J2)
    ell(s, 8, 10, 5.4, 5.4, CREME)
    trait(s, 8, 10, 8, 6, ENCRE, ep=1)
    trait(s, 8, 10, 10.5, 11.5, ENCRE, ep=1)
    for (x, y, h) in ((13, 5, 2), (15.5, 2.5, 1.5)):
        hline(s, x, x + h, y, BLANC)
        trait(s, x + h, y, x, y + h, BLANC, ep=1)
        hline(s, x, x + h, y + h, BLANC)


def s_seconde(s):
    rect(s, 0, 0, 18, 18, NUIT2)
    ell(s, 9, 9, 7, 7, J2)
    ell(s, 9, 9, 6, 6, CREME)
    for a in range(0, 360, 30):
        r = math.radians(a)
        point(s, 9 + 5 * math.cos(r), 9 + 5 * math.sin(r), GRIS)
    trait(s, 9, 9, 9, 4, O1, ep=1)
    trait(s, 9, 9, 12, 9, ENCRE, ep=1)
    etoile4(s, 13.5, 4.5, J3, r=1, coeur=BLANC)


def s_rond_sec(s):
    degrade(s, 0, 18, [GRIS, GRIS_C])
    rect(s, 0, 11, 18, 7, T1)
    ell(s, 9, 14, 5.5, 2.2, J3)
    ell(s, 9, 13.6, 4, 1.4, J4)
    for i in range(18):
        x, y = hasard(i, 1, 4) * 18, hasard(i, 2, 4) * 16
        if abs(x - 9) < 5 and y > 9:
            continue
        trait(s, x, y, x - 0.5, y + 1.5, B4, ep=1)


def s_main_levee(s):
    degrade(s, 0, 18, [B3, B4, O4])
    nuage(s, 12, 5, 7, 2.2, BLANC, BLANC, ARGENT_C)
    ell(s, 5, 14, 3.2, 3.6, "#6cb6ff")
    ell(s, 5, 10.5, 1.4, 1.8, "#6cb6ff")
    for i, a in enumerate((-30, 0, 30)):
        r = math.radians(a - 90)
        trait(s, 5 + 2.6 * math.cos(r), 8 + 2.6 * math.sin(r), 5 + 3.6 * math.cos(r), 8 + 3.6 * math.sin(r), BLANC, ep=1)


def s_buee(s):
    rect(s, 0, 0, 18, 18, LAV2)
    rect(s, 1, 1, 16, 12, ARGENT_C)
    vline(s, 9, 1, 13, BR2)
    for a in range(0, 181, 20):
        r = math.radians(a)
        point(s, 5 + 3 * math.cos(r), 8 - 2 * math.sin(r), LAV1)
    hline(s, 2, 8, 8.5, LAV1)
    rect(s, 0, 13, 18, 5, BR3)
    hline(s, 0, 18, 13, O4)


def s_arc_beige(s):
    degrade(s, 0, 12, [B3, B4])
    for i, c in enumerate((S1, S2, S3, CREME)):
        s.anneau(9, 12, 7 - i, 6 - i, c, ep=1)
    rect(s, 0, 12, 18, 6, T2)
    hline(s, 2, 16, 12.5, B4)


def s_au_revoir(s):
    degrade(s, 0, 18, [LAV1, LAV2, ROSE2, O4])
    for (x, y, l) in ((5, 7, 6), (13, 11, 7)):
        nuage(s, x, y, l, 1.8, O4, CREME, ROSE1)
    etoile4(s, 14, 3, J4, r=0.8)
    rect(s, 0, 15, 18, 3, LAV1)


def s_girouette(s):
    degrade(s, 0, 18, [GRIS, GRIS_C])
    vline(s, 9, 9, 18, ENCRE)
    poly(s, [(5, 9), (7, 6.5), (10, 6.5), (11, 4.5), (12.5, 5.5), (11.5, 8), (10, 9)], RO2)
    poly(s, [(5, 9), (3.5, 5.5), (5, 6.5)], RO1)
    courbe(s, [(3, 13), (9, 15), (15, 13)], CREME, ep=1)
    poly(s, [(14.5, 11.8), (16, 13), (14.4, 14)], CREME)
    for i in range(6):
        x, y = hasard(i, 1, 9) * 18, hasard(i, 2, 9) * 8
        trait(s, x, y, x - 0.4, y + 1.2, B4, ep=1)


SOUVENIRS = {
    ("prologue", "coucher-de-soleil"): s_coucher, ("prologue", "question-gardee"): s_question,
    ("phare-eteint", "tout-le-monde-savait"): s_tout_le_monde, ("phare-eteint", "deux-eclats-un-long"): s_deux_eclats,
    ("phare-eteint", "feu-automatique"): s_feu_auto, ("phare-eteint", "un-sursis"): s_sursis,
    ("phare-eteint", "mauvais-coupable"): s_mauvais_coupable, ("phare-eteint", "celui-qui-eteint"): s_celui_qui_eteint,
    ("grande-panne", "point-final"): s_point_final, ("grande-panne", "registre-corbeille"): s_registre,
    ("grande-panne", "page-bleue"): s_page_bleue, ("grande-panne", "panneau-guichet"): s_panneau,
    ("grande-panne", "demi-tic"): s_demi_tic, ("grande-panne", "seconde-en-plus"): s_seconde,
    ("petit-nuage", "rond-sec"): s_rond_sec, ("petit-nuage", "main-levee"): s_main_levee,
    ("petit-nuage", "buee-du-matin"): s_buee, ("petit-nuage", "arc-beige"): s_arc_beige,
    ("petit-nuage", "au-revoir-du-soir"): s_au_revoir, ("petit-nuage", "girouette-qui-tourne"): s_girouette,
}


def souvenirs():
    for (c, i), f in SOUVENIRS.items():
        ecrire("souvenir-%s-%s" % (c, i), timbre(f, c), commentaire="Souvenir de campagne (%s)" % c)


# =====================================================================================================
# Vignettes des campagnes (32 × 32) et emblèmes de ton (12 × 12)
# =====================================================================================================
def carte(scene, bord):
    """Carte aux coins arrondis : liseré `bord`, la scène de 28 × 28 dedans."""
    t = T(32, 32)
    s = T(28, 28)
    scene(s)
    t.coller(s, 2, 2)
    for X in range(t.W):
        for Y in range(t.H):
            x, y = (X + 0.5) / t.e, (Y + 0.5) / t.e
            dx, dy = max(3 - x, x - 29, 0), max(3 - y, y - 29, 0)
            d = math.hypot(dx, dy)
            if d > 3:
                t.g[Y][X] = None
            elif d > 1.8 or x < 2 or y < 2 or x > 30 or y > 30:
                t.g[Y][X] = bord
    return t


def v_prologue(s):
    degrade(s, 0, 28, [V3, ROSE2, O3, O4])
    ell(s, 19, 15, 4, 4, J4)
    relief(s, lambda x: 20 - 7 * max(0, 1 - ((x - 12) / 13) ** 2), T2, lisere=J3)
    relief(s, lambda x: 23 + math.sin(x / 3), T1, lisere=O3)
    trait(s, 12, 13.5, 12, 9, BR1, ep=s.e)
    ell(s, 12, 8.5, 2.4, 2, T1)


def v_panne(s):
    rect(s, 0, 0, 28, 28, V1)
    rect(s, 2, 4, 24, 16, S3)
    rect(s, 3.5, 5.5, 21, 13, NUIT)
    import decors_panne
    for i, ch in enumerate("1337"):
        decors_panne.chiffre(s, 4.6 + i * 5 + (1.2 if i > 1 else 0), 9, ch, T3, l=2.6, h=5, ep=s.e if i < 3 else 1,
                             penche=1.2 if i == 3 else 0)
    point(s, 14.6, 10.4, T3)
    point(s, 14.6, 12.6, T3)
    rect(s, 11, 20, 6, 3, S2)
    rect(s, 7, 23, 14, 2, S2)
    for (x, y) in ((4, 26), (22, 2)):
        etoile4(s, x, y, O3, r=0.8)


def v_phare(s):
    degrade(s, 0, 28, [NUIT, NUIT2, B1])
    for a in (-1, 1):
        poly(s, [(15, 8), (15 + a * 15, 4), (15 + a * 15, 12)], "#2f5c8e")
    phare_mini(s, 15, 22, 11)
    rect(s, 0, 22, 28, 6, NUIT)
    for i in range(5):
        hline(s, 2 + i * 5, 5 + i * 5, 24 + (i % 2) * 2, B2)
    ell(s, 15, 22.5, 5, 1.2, ENCRE)
    for i, x in enumerate((4, 25)):
        point(s, x, 3 + i * 4, B4)


def v_nuage(s):
    degrade(s, 0, 28, [B3, B4, ARGENT_C])
    for (x, y, l) in ((6, 21, 10), (20, 20, 11), (13, 17, 9)):
        poly(s, [(x - l / 2, 25), (x, y - 8), (x + l / 2, 25)], ARGENT)
        poly(s, [(x - l / 6, y - 4), (x, y - 8), (x + l / 6, y - 4)], BLANC)
    rect(s, 0, 24, 28, 4, T2)
    nuage(s, 14, 9, 11, 3.2, BLANC, BLANC, B4)
    point(s, 12.5, 8.6, ENCRE)
    point(s, 15.5, 8.6, ENCRE)
    if s.e == 2:
        point(s, 11.5, 9.6, ROSE2)
        point(s, 16.5, 9.6, ROSE2)


VIGNETTES = {"prologue": (v_prologue, O2), "grande-panne": (v_panne, V2), "phare-eteint": (v_phare, B1),
             "petit-nuage": (v_nuage, LAV2)}


def emblemes():
    # Humour : un rond rieur (soleil), rayons courts.
    t = T(12, 12)
    for a in range(0, 360, 45):
        r = math.radians(a)
        trait(t, 6 + 4.2 * math.cos(r), 6 + 4.2 * math.sin(r), 6 + 5.6 * math.cos(r), 6 + 5.6 * math.sin(r), O2, ep=t.e)
    ell(t, 6, 6, 3.8, 3.8, O3)
    point(t, 4.8, 5, ENCRE)
    point(t, 7.2, 5, ENCRE)
    courbe(t, [(4.2, 6.8), (6, 8.6), (7.8, 6.8)], ENCRE, ep=1)
    if toile.fin():
        ell(t, 4.8, 4.2, 1, 0.6, O5)
    ecrire("ton-humour", t, commentaire="Emblème de ton : humour (rond rieur)")
    # Mystère : un losange à serrure.
    t = T(12, 12)
    poly(t, [(6, 0), (12, 6), (6, 12), (0, 6)], V1)
    poly(t, [(6, 1.4), (10.6, 6), (6, 10.6), (1.4, 6)], V2)
    ell(t, 6, 4.8, 1.9, 1.9, ENCRE)
    poly(t, [(5.4, 5.5), (6.6, 5.5), (7.3, 9), (4.7, 9)], ENCRE)
    ell(t, 6, 4.8, 1.2, 1.2, J3)
    poly(t, [(5.6, 5.5), (6.4, 5.5), (6.8, 8.4), (5.2, 8.4)], J3)
    if toile.fin():
        trait(t, 6, 1.6, 9.6, 5.2, V3, ep=1)
    ecrire("ton-mystere", t, commentaire="Emblème de ton : mystère (losange à serrure)")
    # Émotion : un cœur.
    t = T(12, 12)
    ell(t, 3.6, 4.4, 3.1, 3.1, ROSE1)
    ell(t, 8.4, 4.4, 3.1, 3.1, ROSE1)
    poly(t, [(0.7, 5.2), (11.3, 5.2), (6, 11.4)], ROSE1)
    ell(t, 3.4, 3.8, 1.4, 1.1, ROSE2)
    if toile.fin():
        point(t, 3, 3.4, BLANC)
    ecrire("ton-emotion", t, commentaire="Emblème de ton : émotion (cœur)")
    # Épique : une étoile à cinq pointes.
    t = T(12, 12)
    pts = []
    for i in range(10):
        r = 5.9 if i % 2 == 0 else 2.5
        a = math.radians(-90 + i * 36)
        pts.append((6 + r * math.cos(a), 6.4 + r * math.sin(a)))
    poly(t, pts, J2)
    poly(t, [(6, 6.4)] + pts[0:3], J3)
    ecrire("ton-epique", t, commentaire="Emblème de ton : épique (étoile)")


def vignettes():
    for c, (f, bord) in VIGNETTES.items():
        ecrire("campagne-" + c, carte(f, bord), commentaire="Vignette de campagne : " + c)
    emblemes()


def tout():
    objets()
    souvenirs()
    vignettes()


IDS = (EXCLUSIFS + ["souvenir-%s-%s" % k for k in SOUVENIRS] + ["campagne-" + c for c in VIGNETTES]
       + ["ton-humour", "ton-mystere", "ton-emotion", "ton-epique"])
