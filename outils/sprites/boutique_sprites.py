"""Objets de la boutique rétro (rayons par emplacement, rangées par palier de niveau) et décors.

Appelé par generer.py. Même grille que Pilou (48 × 56) ; mêmes ancres que les objets de la première
boutique (tete, yeux, cou, corps, main, pieds, cote). Décors (« fond-… ») : scènes de 64 × 48 sans ancre,
dessinées derrière Pilou dans l'app et dans l'aperçu de la boutique. Palette sans opposition rouge / vert.
"""
import math

from toile import Toile, ecrire

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
NUIT, NUIT2 = "#0d2a4d", "#16365e"
O1, O2, O3, O4, O5 = "#8a4a1f", "#d9803a", "#f69d50", "#ffc89a", "#ffd8b0"
J1, J2, J3, J4 = "#7a5a10", "#c9a227", "#f5d76e", "#fff6cc"
V1, V2, V3, V4 = "#3a2a7a", "#6a5acd", "#9b8cff", "#d2caff"
S1, S2, S3 = "#8a6e4b", "#c4a77d", "#e8d5b0"
BR1, BR2, BR3 = "#4a2e17", "#7a4b26", "#a86f3c"
T1, T2, T3 = "#0f4a63", "#2689b8", "#3fb8e0"
ROSE = "#ff9ec7"  # cœurs des lunettes : rose orangé, jamais opposé à un vert


def T(w, h):
    return Toile(w, h)


def etoile(t, x, y, c):
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        t.p(x + dx, y + dy, c)


# =====================================================================================================
# Tête
# =====================================================================================================
def tetes():
    # Béret : galette penchée, petite queue.
    t = T(30, 10)
    t.ell(14, 6, 13, 4.2, V1)
    t.ell(11, 4.5, 8, 2.2, V2)
    t.ell(8, 4, 3, 1, V3)
    t.rect(14, 0, 2, 2, V1)
    t.rect(3, 8, 22, 2, NOIR2)
    t.contour(ENCRE)
    ecrire("beret", t, slot="tete", ancre="tete", point=(14, 8), coiffe=True, commentaire="Béret")

    # Bonnet à pompon : rayures bleu / crème, gros pompon orange.
    t = T(30, 22)
    t.ell(15, 17, 13, 13, B2, cond=lambda x, y, u, v: v < 0)
    for y in range(4, 17):
        for x in range(30):
            if t.get(x, y) == B2 and (y // 3) % 2 == 0:
                t.p(x, y, CREME)
    t.rect(1, 15, 28, 5, B1)
    for x in range(2, 28, 2):
        t.p(x, 16, B3)
        t.p(x + 1, 18, B3)
    t.ell(15, 3.5, 4, 3.5, O3)
    t.ell(14, 2.5, 1.8, 1.4, O5)
    t.contour(ENCRE)
    ecrire("bonnet-pompon", t, slot="tete", ancre="tete", point=(15, 17), coiffe=True, commentaire="Bonnet à pompon")

    # Casque de chantier : coque jaune, visière, bande orange.
    t = T(34, 14)
    t.ell(17, 12, 13, 11, J3, cond=lambda x, y, u, v: v < 0)
    t.ell(13, 6, 5, 3, J4, cond=lambda x, y, u, v: u < 0.3)
    t.rect(15, 1, 4, 11, J2)
    t.rect(0, 11, 34, 3, J2)
    t.rect(0, 11, 34, 1, J3)
    t.rect(6, 8, 22, 2, O3)
    t.contour(J1)
    ecrire("casque-chantier", t, slot="tete", ancre="tete", point=(17, 11), coiffe=True, commentaire="Casque de chantier")

    # Sombrero : très large bord, calotte haute, frise.
    t = T(48, 18)
    t.ell(24, 15, 23.5, 3.2, S2)
    t.ell(24, 14.5, 23.5, 2, S3, cond=lambda x, y, u, v: v < 0)
    t.ell(24, 13, 8, 12, S2, cond=lambda x, y, u, v: v < 0)
    t.ell(22, 6, 3, 4, S3)
    t.rect(16, 9, 16, 2, O3)
    for x in range(17, 32, 3):
        t.p(x, 9, V3)
    t.contour(S1)
    ecrire("sombrero", t, slot="tete", ancre="tete", point=(24, 14), coiffe=True, commentaire="Sombrero")

    # Chapeau de cowboy : bords relevés, calotte pincée, cordon.
    t = T(40, 16)
    t.poly([(0, 9), (6, 13), (34, 13), (40, 9), (36, 15), (4, 15)], BR3)
    t.poly([(9, 13), (11, 3), (16, 1), (20, 4), (24, 1), (29, 3), (31, 13)], BR2)
    t.poly([(16, 1), (20, 4), (24, 1), (20, 7)], BR1)
    t.rect(10, 10, 20, 2, ENCRE)
    t.p(12, 10, J3)
    t.contour(BR1)
    ecrire("chapeau-cowboy", t, slot="tete", ancre="tete", point=(20, 13), coiffe=True, commentaire="Chapeau de cowboy")

    # Oreilles de chat : serre-tête et deux oreilles pointues.
    t = T(36, 16)
    t.anneau(18, 16, 16, 10, ARDOISE, ep=1.6)
    for cx in (7, 29):
        t.poly([(cx - 7, 13), (cx, 0), (cx + 7, 13)], NOIR2)
        t.poly([(cx - 4, 11), (cx, 4), (cx + 4, 11)], O4)
    t.contour(ENCRE)
    ecrire("oreilles-chat", t, slot="tete", ancre="tete", point=(18, 13), commentaire="Oreilles de chat")

    # Couronne de laurier : deux branches de feuilles dorées.
    t = T(34, 12)
    for i in range(7):
        a = math.pi * (0.1 + 0.8 * i / 6)
        for s in (-1, 1):
            x = 17 + s * math.cos(a) * 15
            y = 9 - math.sin(a) * 6
            t.ell(x, y, 2.2, 1.3, J3 if i % 2 else J2)
    t.ell(17, 10, 2, 1.5, O3)
    t.contour(J1)
    ecrire("couronne-laurier", t, slot="tete", ancre="tete", point=(17, 8), commentaire="Couronne de laurier")

    # Antenne néon : double tige qui clignote (bleu / violet), boules lumineuses.
    images = []
    for k in range(4):
        t = T(26, 20)
        c1, c2 = ((B3, V3), (V3, B3), (B4, V4), (V4, B4))[k]
        t.rect(1, 17, 24, 3, NOIR2)
        t.ligne(6, 17, 3, 6, ARGENT)
        t.ligne(20, 17, 23, 6, ARGENT)
        t.ell(3.5, 4, 3.5, 3.5, c1)
        t.ell(22.5, 4, 3.5, 3.5, c2)
        t.p(2, 3, BLANC)
        t.p(21, 3, BLANC)
        if k % 2 == 0:
            for x, y in ((0, 0), (8, 2), (17, 1), (25, 0)):
                t.p(x, y, J4)
        t.contour(ENCRE)
        images.append(t)
    ecrire("antenne-neon", images, slot="tete", ancre="tete", point=(13, 18), coiffe=True, duree=180, commentaire="Antenne néon")


# =====================================================================================================
# Yeux
# =====================================================================================================
def yeux():
    # Lunettes 3D : verres bleu / orange, monture blanche.
    t = T(30, 10)
    t.rect(0, 0, 30, 10, CREME)
    t.rect(2, 2, 11, 6, B3)
    t.rect(17, 2, 11, 6, O3)
    t.rect(13, 3, 4, 2, None)
    t.rect(13, 0, 4, 3, CREME)
    t.rect(3, 3, 3, 1, B4)
    t.rect(18, 3, 3, 1, O5)
    t.contour(ENCRE)
    ecrire("lunettes-3d", t, slot="yeux", ancre="yeux", point=(15, 2), commentaire="Lunettes 3D")

    # Visière de pilote : bandeau miroir qui scintille.
    images = []
    for k in range(3):
        t = T(34, 10)
        t.poly([(0, 2), (34, 2), (32, 9), (2, 9)], NUIT)
        t.poly([(2, 3), (32, 3), (30, 8), (4, 8)], B2)
        x = 6 + k * 9
        t.ligne(x, 8, x + 4, 3, B4)
        t.ligne(x + 1, 8, x + 5, 3, BLANC)
        t.rect(0, 0, 34, 2, ARGENT)
        t.contour(ENCRE)
        images.append(t)
    ecrire("visiere-pilote", images, slot="yeux", ancre="yeux", point=(17, 3), duree=260, commentaire="Visière de pilote")

    # Lunettes cœur : deux cœurs roses orangés.
    t = T(30, 11)
    for cx in (7, 23):
        t.ell(cx - 3, 3.5, 3.6, 3.4, ROSE)
        t.ell(cx + 3, 3.5, 3.6, 3.4, ROSE)
        t.poly([(cx - 6.5, 4), (cx + 6.5, 4), (cx, 11)], ROSE)
        t.p(cx - 4, 2, BLANC)
        t.p(cx - 3, 2, BLANC)
    t.rect(13, 3, 4, 1, O2)
    t.contour(O1)
    ecrire("lunettes-coeur", t, slot="yeux", ancre="yeux", point=(15, 2), commentaire="Lunettes cœur")


# =====================================================================================================
# Cou
# =====================================================================================================
def cous():
    # Bandana : triangle bleu à pois blancs, nœud sur le côté.
    t = T(34, 14)
    t.poly([(1, 1), (33, 1), (17, 14)], B2)
    t.rect(1, 1, 32, 2, B1)
    for x in range(5, 31, 4):
        for y in range(4, 12, 3):
            if t.get(x, y) == B2:
                t.p(x, y, CREME)
    t.poly([(28, 0), (34, 0), (33, 4)], B1)
    t.contour(ENCRE)
    ecrire("bandana", t, slot="cou", ancre="cou", point=(17, 2), commentaire="Bandana")

    # Nœud papillon à pois : violet à pois jaunes.
    t = T(18, 10)
    t.poly([(0, 0), (8, 4), (8, 6), (0, 10)], V2)
    t.poly([(18, 0), (10, 4), (10, 6), (18, 10)], V2)
    t.rect(7, 3, 4, 4, V1)
    for x, y in ((2, 3), (4, 6), (2, 7), (15, 3), (13, 6), (15, 7), (5, 4), (12, 4)):
        t.p(x, y, J3)
    t.contour(ENCRE)
    ecrire("noeud-pois", t, slot="cou", ancre="cou", point=(9, 2), commentaire="Nœud papillon à pois")

    # Cravate : bleu nuit à rayures orange.
    t = T(10, 22)
    t.poly([(2, 0), (8, 0), (6, 4), (4, 4)], B1)
    t.poly([(4, 4), (6, 4), (9, 19), (5, 22), (1, 19)], B1)
    for y in range(6, 20, 4):
        t.ligne(1, y + 3, 9, y, O3)
    t.contour(ENCRE)
    ecrire("cravate", t, slot="cou", ancre="cou", point=(5, 1), commentaire="Cravate")

    # Collier de perles : arc de perles nacrées.
    t = T(30, 10)
    for i in range(13):
        a = math.pi * i / 12
        x = 15 - math.cos(a) * 13
        y = 1 + math.sin(a) * 5
        t.ell(x, y, 1.7, 1.7, ARGENT_C)
        t.p(int(x), int(y) - 1, BLANC)
    t.ell(15, 7, 2.4, 2.4, CREME)
    t.contour(GRIS)
    ecrire("collier-perles", t, slot="cou", ancre="cou", point=(15, 2), commentaire="Collier de perles")


# =====================================================================================================
# Dos
# =====================================================================================================
def dos():
    # Sac à dos : sac orange avec poche, bretelles.
    t = T(40, 24)
    t.rect(29, 2, 11, 20, O2)
    t.rect(30, 3, 9, 6, O3)
    t.rect(30, 12, 9, 7, O1)
    t.rect(31, 13, 7, 5, O2)
    t.rect(33, 14, 3, 1, J3)
    t.rect(29, 0, 11, 2, O1)
    t.contour(ENCRE)
    ecrire("sac-a-dos", t, slot="dos", ancre="cou", point=(20, 14), couche="derriere", commentaire="Sac à dos")

    # Carapace : dôme de tortue écailleux derrière Pilou.
    t = T(46, 32)
    t.ell(23, 22, 23, 21, S1, cond=lambda x, y, u, v: v < 0.45)
    t.ell(23, 22, 20, 18, S2, cond=lambda x, y, u, v: v < 0.45)
    for cx, cy in ((23, 9), (12, 16), (34, 16), (17, 25), (29, 25)):
        t.ell(cx, cy, 5, 4, S3)
        t.anneau(cx, cy, 5, 4, S1, ep=1)
    t.contour(BR1)
    ecrire("carapace", t, slot="dos", ancre="corps", point=(23, 24), couche="derriere", commentaire="Carapace")

    # Ailes de papillon : grandes ailes violet / orange qui battent.
    images = []
    for k in range(4):
        t = T(60, 34)
        e = [0, 2, 4, 2][k]
        for s in (-1, 1):
            cx = 30 + s * (16 - e)
            t.ell(cx, 11 + e * 0.3, 13 - e, 10, V2)
            t.ell(cx, 25, 9 - e * 0.6, 7, O3)
            t.ell(cx + s * 2, 10, 5 - e * 0.5, 4, V3)
            t.ell(cx, 25, 4, 3, O5)
            t.ell(cx - s * 3, 8, 1.6, 1.6, J4)
        t.contour(ENCRE)
        images.append(t)
    ecrire("ailes-papillon", images, slot="dos", ancre="corps", point=(30, 22), couche="derriere", duree=150,
           commentaire="Ailes de papillon")

    # Jetpack : deux réservoirs argent, flammes orange animées.
    images = []
    for k in range(4):
        t = T(50, 34)
        for x0 in (1, 41):
            t.rect(x0, 2, 8, 20, ARGENT)
            t.rect(x0 + 1, 3, 2, 18, ARGENT_C)
            t.ell(x0 + 4, 2, 4, 2, GRIS_C)
            t.rect(x0 + 1, 22, 6, 3, ARDOISE)
            f = [5, 8, 6, 9][(k + (x0 > 20)) % 4]
            t.poly([(x0 + 1, 25), (x0 + 7, 25), (x0 + 4, 25 + f)], O3)
            t.poly([(x0 + 2.5, 25), (x0 + 5.5, 25), (x0 + 4, 25 + f * 0.6)], J4)
        t.rect(9, 8, 32, 3, ARDOISE)
        t.contour(ENCRE)
        images.append(t)
    ecrire("jetpack", images, slot="dos", ancre="corps", point=(25, 16), couche="derriere", duree=110, commentaire="Jetpack")


# =====================================================================================================
# Main
# =====================================================================================================
def mains():
    # Sucette : grosse spirale bleu / violet / crème sur bâton.
    t = T(14, 24)
    t.ell(7, 6.5, 6.5, 6.5, CREME)
    for r in range(1, 30):
        a = r * 0.55
        rr = r * 0.22
        t.p(int(7 + math.cos(a) * rr), int(6.5 + math.sin(a) * rr), V3 if r % 2 else B3)
    t.contour(V1)
    t.rect(6, 14, 2, 10, CREME_O)
    ecrire("sucette", t, slot="main", ancre="main", point=(6, 20), commentaire="Sucette")

    # Épée en mousse : lame bleue ronde, garde orange.
    t = T(10, 28)
    t.rect(3, 0, 5, 19, B3)
    t.rect(4, 0, 2, 18, B4)
    t.ell(5.5, 1, 2.6, 2, B3)
    t.rect(0, 19, 11, 3, O3)
    t.rect(4, 22, 3, 5, BR2)
    t.contour(B1)
    ecrire("epee-mousse", t, slot="main", ancre="main", point=(5, 24), commentaire="Épée en mousse")

    # Lanterne : cage de laiton, flamme qui danse.
    images = []
    for k in range(3):
        t = T(14, 22)
        t.anneau(7, 3, 3, 3, BR2, ep=1)
        t.rect(2, 5, 10, 2, BR1)
        t.rect(2, 18, 10, 2, BR1)
        t.rect(3, 7, 8, 11, J4)
        for x in (3, 10):
            t.rect(x, 7, 1, 11, BR2)
        fl = [0, 1, -1][k]
        t.ell(7 + fl * 0.4, 13, 2.2, 3.5, O3)
        t.ell(7, 14, 1.2, 2, J3)
        t.contour(ENCRE)
        images.append(t)
    ecrire("lanterne", images, slot="main", ancre="main", point=(7, 16), duree=200, commentaire="Lanterne")

    # Guitare : caisse orange, manche, cordes.
    t = T(16, 34)
    t.ell(8, 26, 7.5, 7, O3)
    t.ell(8, 18, 5.5, 5, O3)
    t.ell(8, 23, 2.4, 2.4, BR1)
    t.rect(7, 0, 3, 17, BR2)
    t.rect(6, 0, 5, 3, BR1)
    for x in (7, 9):
        t.ligne(x, 2, x, 30, CREME)
    t.rect(5, 29, 7, 1, BR1)
    t.contour(ENCRE)
    ecrire("guitare", t, slot="main", ancre="main", point=(4, 24), commentaire="Guitare")

    # Canne à pêche dorée (cosmétique) : canne d'or, fil et petit poisson pendu.
    images = []
    for k in range(4):
        t = T(16, 36)
        t.ligne(2, 35, 11, 2, J2)
        t.ligne(3, 35, 12, 2, J3)
        t.ell(4, 30, 2.4, 2.4, ARGENT)
        oscil = [0, 1, 0, -1][k]
        for y in range(3, 20):
            t.p(12 + oscil * (y - 3) // 12, y, GRIS_C)
        fx = 12 + oscil
        t.ell(fx, 22, 2.5, 1.6, O3)
        t.poly([(fx - 2, 22), (fx - 4, 20), (fx - 4, 24)], O2)
        t.contour(ENCRE)
        images.append(t)
    ecrire("canne-or", images, slot="main", ancre="main", point=(3, 32), duree=320, commentaire="Canne à pêche dorée")


# =====================================================================================================
# Pieds
# =====================================================================================================
def pieds():
    # Baskets : deux chaussures blanches à bande bleue.
    t = T(28, 8)
    for x0 in (0, 15):
        t.rect(x0 + 1, 1, 10, 5, CREME)
        t.ell(x0 + 10, 4, 3, 2.5, CREME)
        t.rect(x0 + 3, 2, 6, 1, B3)
        t.rect(x0, 6, 13, 2, B1)
        t.p(x0 + 5, 1, O3)
        t.p(x0 + 7, 1, O3)
    t.contour(ENCRE)
    ecrire("baskets", t, slot="pieds", ancre="pieds", point=(14, 5), commentaire="Baskets")

    # Patins : bottines orange sur lames argent.
    t = T(30, 11)
    for x0 in (0, 16):
        t.rect(x0 + 2, 0, 8, 6, O3)
        t.rect(x0 + 2, 0, 8, 1, O5)
        t.rect(x0 + 2, 6, 11, 2, O2)
        t.rect(x0 + 1, 9, 13, 1, ARGENT_C)
        t.rect(x0 + 3, 8, 1, 1, GRIS)
        t.rect(x0 + 10, 8, 1, 1, GRIS)
    t.contour(ENCRE)
    ecrire("patins", t, slot="pieds", ancre="pieds", point=(15, 6), commentaire="Patins")

    # Palmes : larges palmes bleues nervurées.
    t = T(36, 8)
    for x0, s in ((0, -1), (19, 1)):
        t.poly([(x0 + 4, 0), (x0 + 13, 0), (x0 + 17, 7), (x0, 7)], B2)
        for i in range(3):
            t.ligne(x0 + 6 + i * 3, 1, x0 + 3 + i * 5, 6, B1)
    t.contour(ENCRE)
    ecrire("palmes", t, slot="pieds", ancre="pieds", point=(18, 3), commentaire="Palmes")


# =====================================================================================================
# Compagnons (au sol, à côté de Pilou)
# =====================================================================================================
def compagnons():
    # Oiseau : petit oiseau bleu qui sautille et pépie.
    images = []
    for k in range(4):
        t = T(16, 16)
        h = [0, 2, 0, 1][k]
        t.ell(7, 10 - h, 5.5, 4.5, B3)
        t.ell(10, 6 - h, 3.5, 3.5, B3)
        t.ell(6, 10 - h, 3.5, 2.5, B2)
        t.poly([(13, 6 - h), (16, 7 - h), (13, 8 - h)], O3)
        t.p(11, 5 - h, ENCRE)
        t.ell(8, 12 - h, 2.5, 1.5, CREME)
        t.rect(6, 15 - h, 1, h + 1, O2)
        t.rect(9, 15 - h, 1, h + 1, O2)
        t.contour(B1)
        images.append(t)
    ecrire("oiseau", images, slot="compagnon", ancre="cote", point=(1, 16), duree=260, commentaire="Oiseau")

    # Petit robot : boîte argent, antenne lumineuse, chenilles.
    images = []
    for k in range(4):
        t = T(16, 20)
        t.rect(2, 6, 12, 9, ARGENT)
        t.rect(3, 7, 10, 3, NUIT)
        e = B3 if k != 3 else NUIT
        t.rect(4, 8, 2, 1, e)
        t.rect(10, 8, 2, 1, e)
        t.rect(6, 12, 4, 1, GRIS)
        t.rect(7, 2, 1, 4, GRIS)
        t.ell(7.5, 2, 1.6, 1.6, O3 if k % 2 else J3)
        t.rect(1, 15, 14, 4, ARDOISE)
        for x in range(2, 15, 3):
            t.p(x + k % 3, 17, GRIS_C)
        t.contour(ENCRE)
        images.append(t)
    ecrire("petit-robot", images, slot="compagnon", ancre="cote", point=(0, 19), duree=240, commentaire="Petit robot")

    # Fantôme : drap blanc qui flotte, joues orange.
    images = []
    for k in range(4):
        t = T(16, 20)
        f = [0, 1, 2, 1][k]
        t.ell(8, 7 - f, 7, 7, CREME)
        t.rect(1, 7 - f, 14, 8, CREME)
        for i in range(4):
            x = 1 + i * 4
            t.ell(x + 1.5, 15 - f + (i + k) % 2, 2, 2, CREME)
        t.rect(5, 6 - f, 2, 3, ENCRE)
        t.rect(9, 6 - f, 2, 3, ENCRE)
        t.p(4, 10 - f, O4)
        t.p(12, 10 - f, O4)
        t.rect(7, 11 - f, 2, 1, ENCRE)
        t.contour(GRIS_C)
        images.append(t)
    ecrire("fantome", images, slot="compagnon", ancre="cote", point=(0, 19), duree=280, commentaire="Fantôme")

    # Mini-dragon : dragonnet violet, ailes orange, crache une étincelle.
    images = []
    for k in range(4):
        t = T(22, 20)
        t.ell(9, 13, 6.5, 5, V2)
        t.ell(15, 7, 4.5, 4, V2)
        t.ell(9, 15, 4, 2.5, J3)
        a = [0, 2, 3, 1][k]
        t.poly([(6, 9), (2 - a * 0.3, 1 + a), (10, 7)], O3)
        t.poly([(15, 3), (14, 0), (17, 3)], J4)
        t.p(16, 6, ENCRE)
        t.poly([(3, 15), (0, 12), (1, 17)], V2)
        t.rect(6, 18, 2, 2, V1)
        t.rect(11, 18, 2, 2, V1)
        if k == 2:
            t.ell(20, 9, 1.6, 1.2, O3)
            t.p(21, 8, J4)
        t.contour(V1)
        images.append(t)
    ecrire("mini-dragon", images, slot="compagnon", ancre="cote", point=(0, 19), duree=260, commentaire="Mini-dragon")


# =====================================================================================================
# Effets
# =====================================================================================================
def effets():
    # Bulles de savon qui montent autour de Pilou.
    images = []
    for k in range(6):
        t = T(54, 44)
        for i, (x, base, r) in enumerate(((3, 40, 3), (48, 34, 2.5), (8, 26, 2), (44, 20, 3), (2, 14, 2.5))):
            ph = (k / 6 + i * 0.23) % 1
            y = base - ph * 14
            t.anneau(x + 2 + math.sin(ph * 6 + i) * 1.5, y, r, r, B4, ep=1)
            t.p(int(x + 1), int(y - r + 1), BLANC)
        images.append(t)
    ecrire("bulles-savon", images, slot="effet", ancre="corps", point=(27, 37), duree=170, commentaire="Bulles de savon")

    # Confettis : petits rectangles colorés qui tombent.
    images = []
    cols = [B3, O3, J3, V3, B4, O4]
    for k in range(6):
        t = T(46, 50)
        for i in range(26):
            x = (i * 37 + 5) % 45
            y = (i * 13 + k * 8) % 48
            if 7 < x < 38 and 8 < y < 46:
                continue
            c = cols[i % len(cols)]
            if (i + k) % 2:
                t.rect(x, y, 2, 1, c)
            else:
                t.rect(x, y, 1, 2, c)
        images.append(t)
    ecrire("confettis", images, slot="effet", ancre="corps", point=(23, 40), duree=150, commentaire="Confettis")

    # Traînée prisme : arc dégradé bleu → violet → orange (jamais rouge / vert) qui scintille derrière Pilou.
    images = []
    bandes = [B4, B3, V3, V2, O3, J3]
    for k in range(4):
        t = T(48, 30)
        for i, c in enumerate(bandes):
            r = 23.5 - i * 1.6
            for x in range(48):
                for y in range(30):
                    d = math.hypot(x + 0.5 - 24, (y + 0.5 - 27) * 1.15)
                    if r - 1.6 < d <= r and (x + y + k * 2) % 9 != 0:
                        t.p(x, y, c)
        for i in range(3):
            etoile(t, 4 + ((i * 17 + k * 7) % 40), 2 + (i * 5 + k * 3) % 8, J4)
        images.append(t)
    ecrire("trainee-prisme", images, slot="effet", ancre="corps", point=(24, 27), couche="derriere", duree=180,
           commentaire="Traînée prisme")

    # Aura de feu : flammes orange / jaunes qui lèchent la silhouette.
    images = []
    for k in range(4):
        t = T(50, 50)
        for i in range(16):
            a = i / 16 * 2 * math.pi
            r = 21 + ((i + k) % 3) * 1.5
            x, y = 25 + math.cos(a) * r, 27 + math.sin(a) * r * 1.05
            hgt = 4 + (i + k) % 3 * 2
            t.poly([(x - 2.5, y + 1), (x + 2.5, y + 1), (x + math.cos(a) * 1.5, y - hgt)], O3 if i % 2 else O2)
            t.poly([(x - 1, y + 1), (x + 1, y + 1), (x, y - hgt * 0.5)], J3)
        images.append(t)
    ecrire("aura-feu", images, slot="effet", ancre="corps", point=(25, 27), couche="derriere", duree=140,
           commentaire="Aura de feu")


# =====================================================================================================
# Décors (fond) : scènes de 64 × 48, derrière Pilou (app, aperçu de la boutique)
# =====================================================================================================
def ciel(t, haut, bas, h):
    for y in range(h):
        c = haut if y < h * 0.55 else bas
        t.rect(0, y, 64, 1, c)


def fonds():
    W, H = 64, 48
    # Nuit étoilée : ciel nuit, lune, étoiles qui scintillent, collines.
    images = []
    for k in range(2):
        t = T(W, H)
        ciel(t, NUIT, NUIT2, H)
        t.ell(50, 10, 5, 5, J4)
        t.ell(52, 9, 4.5, 4.5, NUIT)
        for i, (x, y) in enumerate(((6, 5), (14, 12), (22, 4), (31, 9), (40, 3), (9, 20), (27, 18), (58, 22), (45, 17))):
            t.p(x, y, J4 if (i + k) % 2 else B4)
            if (i + k) % 3 == 0:
                etoile(t, x, y, B4)
        t.ell(14, 50, 26, 12, B1)
        t.ell(50, 52, 24, 12, NUIT2)
        images.append(t)
    ecrire("fond-nuit", images, duree=600, commentaire="Décor : nuit étoilée")

    # Forêt bleutée : sapins sarcelle, brume, lucioles.
    images = []
    for k in range(2):
        t = T(W, H)
        ciel(t, "#12324a", "#1b4560", H)
        for i, x in enumerate(range(-2, 66, 9)):
            h = 18 + (i * 7) % 10
            base = 46
            t.poly([(x, base), (x + 4.5, base - h), (x + 9, base)], B1 if i % 2 else T2)
            t.ligne(x + 4.5, base - h + 3, x + 2, base - h + 7, B3 if i % 2 else T3)
        t.rect(0, 40, 64, 8, T1)
        for x in range(0, 64, 2):
            t.p(x, 38 + (x // 2 + k) % 2, "#5c8fa8")
        for i, (x, y) in enumerate(((10, 30), (30, 26), (52, 32), (42, 18))):
            if (i + k) % 2 == 0:
                t.p(x, y, J3)
        images.append(t)
    ecrire("fond-foret", images, duree=500, commentaire="Décor : forêt bleutée")

    # Plage : ciel, soleil, mer à vaguelettes, sable.
    images = []
    for k in range(2):
        t = T(W, H)
        ciel(t, B4, "#d8ecff", H)
        t.ell(12, 10, 6, 6, J3)
        t.ell(12, 10, 4, 4, J4)
        t.rect(0, 24, 64, 12, B2)
        for x in range(0, 64, 6):
            t.rect(x + (k * 3) % 6, 26 + (x // 6) % 3 * 3, 3, 1, B4)
        t.rect(0, 36, 64, 12, S3)
        for x in range(2, 64, 7):
            t.p(x, 40 + x % 5, S2)
        t.ell(52, 42, 3, 1.5, O4)
        t.rect(48, 24, 1, 14, BR2)
        t.ell(48.5, 25, 9, 5, O3, cond=lambda x, y, u, v: v < 0)
        for x in range(40, 58, 4):
            t.rect(x, 20, 2, 5, CREME)
        t.ell(48.5, 25, 9, 5, O3, cond=lambda x, y, u, v: v < -0.85)
        images.append(t)
    ecrire("fond-plage", images, duree=500, commentaire="Décor : plage")

    # Salle d'arcade : sol damier, bornes aux écrans lumineux, néons.
    images = []
    for k in range(2):
        t = T(W, H)
        t.rect(0, 0, 64, 48, "#151a2e")
        t.rect(0, 6, 64, 1, V3 if k else B3)
        t.rect(0, 8, 64, 1, O3 if k else V3)
        for i, x in enumerate((4, 26, 48)):
            t.rect(x, 14, 12, 24, V1)
            t.rect(x + 2, 16, 8, 7, (B3, O3, V3)[(i + k) % 3])
            t.rect(x + 3, 17, 3, 2, BLANC)
            t.rect(x + 3, 27, 2, 2, O3)
            t.rect(x + 7, 27, 2, 2, B3)
        for y in range(38, 48, 2):
            for x in range(0, 64, 2):
                if (x // 2 + y // 2) % 2 == 0:
                    t.rect(x, y, 2, 2, "#262c45")
        images.append(t)
    ecrire("fond-arcade", images, duree=400, commentaire="Décor : salle d'arcade")

    # Espace : nébuleuse violette, planète à anneau, étoiles.
    images = []
    for k in range(2):
        t = T(W, H)
        t.rect(0, 0, 64, 48, "#090b1f")
        t.ell(18, 30, 22, 10, "#1f1846")
        t.ell(24, 28, 12, 5, "#2e2466")
        t.ell(46, 16, 8, 8, O3)
        t.ell(44, 14, 4, 3, O5)
        t.anneau(46, 17, 14, 3.5, J3, ep=1)
        for i in range(18):
            x, y = (i * 29 + 7) % 64, (i * 17 + 3) % 48
            t.p(x, y, B4 if (i + k) % 3 else J4)
        images.append(t)
    ecrire("fond-espace", images, duree=700, commentaire="Décor : espace")


# =====================================================================================================
# Icônes de l'interface de la boutique (pas portées)
# =====================================================================================================
def icones():
    # Cadenas : rangée fermée (signe de forme, pas de couleur seule).
    t = T(10, 12)
    t.anneau(5, 4.5, 3.5, 4, ARGENT, ep=1.4)
    t.rect(0, 5, 10, 7, ARGENT)
    t.rect(1, 6, 8, 1, ARGENT_C)
    t.rect(4, 7, 2, 3, ENCRE)
    t.contour(ENCRE)
    ecrire("cadenas", t, commentaire="Icône : rangée fermée")

    # Sac de boutique avec étoile : badge près de Pilou (nouvelle rangée, offre du jour).
    images = []
    for k in range(2):
        t = T(14, 15)
        t.rect(1, 4, 12, 11, O3)
        t.rect(1, 4, 12, 2, O2)
        t.anneau(7, 4, 3.5, 3.5, O1, ep=1.2)
        t.rect(0, 3, 14, 0, O1)
        c = J4 if k == 0 else BLANC
        t.poly([(7, 6), (8.3, 8.6), (11, 9), (8.8, 10.6), (9.6, 13.4), (7, 11.8), (4.4, 13.4), (5.2, 10.6), (3, 9), (5.7, 8.6)], c)
        t.contour(ENCRE)
        images.append(t)
    ecrire("badge-boutique", images, duree=500, commentaire="Icône : du nouveau en boutique")

    # Pierre de calme : galet bleu-gris lisse, spirale claire.
    t = T(14, 10)
    t.ell(7, 5.5, 6.8, 4.4, ARDOISE)
    t.ell(6, 4.5, 5, 3, GRIS)
    for i in range(10):
        a = i * 0.7
        r = 0.4 + i * 0.28
        t.p(int(7 + math.cos(a) * r * 1.4), int(5 + math.sin(a) * r * 0.8), B4)
    t.contour(ENCRE)
    ecrire("pierre-calme", t, commentaire="Icône : pierre de calme")

    # Marmite en cuivre (bonus de cuisine).
    t = T(16, 12)
    t.ell(8, 6.5, 7, 5, O2, cond=lambda x, y, u, v: v > -0.6)
    t.rect(1, 3, 14, 2, O3)
    t.rect(0, 4, 2, 2, O1)
    t.rect(14, 4, 2, 2, O1)
    t.rect(3, 6, 2, 3, O4)
    t.contour(ENCRE)
    ecrire("marmite-cuivre", t, commentaire="Icône : marmite en cuivre")

    # Canne dorée (bonus de pêche).
    t = T(14, 16)
    t.ligne(1, 15, 12, 1, J2)
    t.ligne(2, 15, 13, 1, J3)
    t.ell(3, 12, 2, 2, ARGENT)
    t.ligne(12, 2, 12, 9, GRIS_C)
    t.ell(12, 10.5, 1.5, 1.5, O3)
    t.contour(ENCRE)
    ecrire("canne-doree", t, commentaire="Icône : canne dorée")


def objets():
    icones()
    tetes()
    yeux()
    cous()
    dos()
    mains()
    pieds()
    compagnons()
    effets()
    fonds()


# Nouvelles teintes (couleurs de Pilou) : contour, ombre, base, clair. Aucune opposition rouge / vert.
TEINTES = {
    "pervenche": ["#2c3570", "#5a6fd0", "#8fa2ff", "#d3dbff"],
    "mandarine": ["#7a3a08", "#d06a14", "#ff9933", "#ffd2a0"],
    "miel": ["#6e4c0c", "#c08a1c", "#f2bd3c", "#fff0b8"],
    "prune": ["#3a1a46", "#6e3d86", "#a46cc2", "#e3c9f0"],
    "acier": ["#22303d", "#556b80", "#8aa1b6", "#d4e0ea"],
    "peche": ["#7a4430", "#d0866a", "#ffb89a", "#ffe6da"],
}
