"""Expéditions de Pilou (docs/EXPEDITIONS.md) : son équipement d'aventurier, le butin introuvable en boutique,
les créatures qu'il croise, les coffres, les trophées de boss, l'éclair d'énergie, les en-cas de route et le
pansement des jours de défaite.

Appelé par generer.py. Palette orange / bleu / crème / ardoise (et sable, bois, sarcelle) : jamais
d'opposition rouge / vert ; chaque état garde un signe de forme (coffre fermé / ouvert, trophée gravé d'un
emblème différent par boss, cœur barré du pansement…). Tout est original : aucune créature, aucun objet
d'un jeu existant.
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
ARDOISE_C = "#57606a"
ARGENT = "#b8c4d2"
ARGENT_C = "#e6ecf2"
B1, B2, B3, B4 = "#1f4f8a", "#4a8fdc", "#6cb6ff", "#b4dbff"
NUIT = "#0d2a4d"
O1, O2, O3, O4, O5 = "#8a4a1f", "#d9803a", "#f69d50", "#ffc89a", "#ffd8b0"
J1, J2, J3, J4 = "#7a5a10", "#c9a227", "#f5d76e", "#fff6cc"
V1, V2, V3, V4 = "#3a2a7a", "#6a5acd", "#9b8cff", "#d2caff"
S1, S2, S3 = "#8a6e4b", "#c4a77d", "#e8d5b0"
BR1, BR2, BR3 = "#4a2e17", "#7a4b26", "#a86f3c"
T1, T2, T3, T4 = "#0f4a63", "#2689b8", "#3fb8e0", "#a8e4f5"  # sarcelle (slimes), sans vert


def T(w, h):
    return Toile(w, h)


# =====================================================================================================
# Équipement de Pilou
# =====================================================================================================
def epee_bois():
    # Épée en bois portée en travers du dos : la lame dépasse au-dessus de l'épaule gauche, la poignée
    # (cuir orange, pommeau rond) en bas à droite, cachée en partie par Pilou.
    t = T(30, 30)
    for i in range(20):
        x, y = 2 + i, 2 + i
        t.rect(x, y, 3, 2, S3)
        t.p(x + 2, y + 1, S2)
    t.p(2, 2, S2)
    t.p(3, 2, S3)
    t.ligne(4, 3, 20, 19, S1)          # le fil du bois
    # Garde (une traverse en travers de la lame) et poignée.
    t.ligne(18, 25, 25, 18, BR2)
    t.ligne(19, 25, 25, 19, BR3)
    for i in range(4):
        t.rect(23 + i, 23 + i, 2, 2, O2)
    t.ell(28, 28, 1.6, 1.6, O3)
    t.contour(BR1)
    ecrire("epee-bois", t, slot="dos", ancre="corps", point=(18, 20), couche="derriere",
           commentaire="Épée en bois (expédition : portée dans le dos)")


def bouclier_couvercle():
    # Un couvercle de casserole en guise de bouclier, tenu au flanc gauche : bord argent, bouton orange,
    # une bosse (il a servi).
    t = T(16, 18)
    t.ell(8, 9, 7.6, 8.6, GRIS)
    t.ell(8, 9, 6.4, 7.4, ARGENT)
    t.ell(6.5, 6.5, 3.4, 3.2, ARGENT_C)
    t.ell(8, 9, 2.2, 2.2, O3)
    t.p(7, 8, O5)
    t.p(11, 13, GRIS)
    t.p(12, 12, GRIS)
    t.contour(ENCRE)
    ecrire("bouclier-couvercle", t, slot="dos", ancre="main-g", point=(12, 9),
           commentaire="Bouclier-couvercle (butin d'expédition)")


def torche():
    # Torche : manche de bois, bandes de tissu sable, flamme orange et jaune qui danse (trois images).
    images = []
    for k in range(3):
        t = T(12, 26)
        t.rect(5, 11, 3, 15, BR2)
        t.rect(5, 11, 1, 15, BR3)
        t.rect(4, 10, 5, 4, S2)
        t.ligne(4, 11, 8, 11, S1)
        h = (9, 10, 8)[k]
        dx = (0, 1, -1)[k]
        t.poly([(2.5, 10), (9.5, 10), (6.5 + dx, 10 - h), (4.5, 6)], O3)
        t.poly([(4, 10), (8, 10), (6 + dx * 0.5, 10 - h * 0.6)], J3)
        t.ell(6, 9, 1.4, 1.2, J4)
        t.contour(O1)
        images.append(t)
    ecrire("torche", images, slot="main", ancre="main", point=(6, 20), duree=170, commentaire="Torche (butin d'expédition)")


def casque_passoire():
    # Une passoire en guise de casque : dôme argent percé de trous, petite poignée sur le côté.
    t = T(26, 13)
    t.ell(12, 12, 10.5, 10.5, ARGENT, cond=lambda x, y, u, v: v <= 0.05)
    t.ell(10, 9, 6, 5, ARGENT_C, cond=lambda x, y, u, v: v < 0)
    for (x, y) in ((6, 9), (10, 7), (14, 8), (18, 10), (8, 4), (13, 4), (16, 5), (11, 10), (5, 11), (19, 7)):
        t.p(x, y, GRIS)
    t.rect(0, 11, 24, 2, GRIS)
    t.rect(22, 7, 4, 2, ARDOISE_C)
    t.contour(ENCRE)
    ecrire("casque-passoire", t, slot="tete", ancre="tete", point=(12, 9), coiffe=True,
           commentaire="Casque-passoire (butin d'expédition)")


def slime_apprivoise():
    # Petit slime sarcelle apprivoisé : il rebondit à côté de Pilou, l'air ravi.
    images = []
    for k in range(4):
        t = T(16, 16)
        e = (0, 1, 2, 1)[k]            # écrasement
        h = 10 - e
        t.ell(8, 15 - h / 2, 7 + e * 0.4, h / 2 + 0.6, T3)
        t.ell(8, 15 - h * 0.55, 5, h * 0.3, T4, cond=lambda x, y, u, v: v < 0)
        t.ell(5, 15 - h * 0.7, 1.4, 1.2, BLANC)
        t.p(6, 15 - int(h * 0.45), ENCRE)
        t.p(10, 15 - int(h * 0.45), ENCRE)
        t.p(7, 15 - int(h * 0.45) + 2, ENCRE)
        t.p(8, 15 - int(h * 0.45) + 2, ENCRE)
        t.p(9, 15 - int(h * 0.45) + 2, ENCRE)
        t.contour(T1)
        images.append(t)
    ecrire("slime-apprivoise", images, slot="compagnon", ancre="cote", point=(0, 15), duree=220,
           commentaire="Slime apprivoisé (butin d'expédition)")


def carte_tresor():
    # Carte au trésor : parchemin sable, chemin en pointillés bleus, une croix orange (le trésor), rose des vents.
    t = T(22, 16)
    t.rect(1, 1, 20, 14, S3)
    t.rect(1, 1, 20, 1, S2)
    t.rect(1, 14, 20, 1, S2)
    t.ell(1, 8, 1.6, 7.5, S2)
    t.ell(21, 8, 1.6, 7.5, S2)
    for i, (x, y) in enumerate(((4, 11), (6, 10), (8, 10), (9, 8), (11, 7), (13, 7), (14, 5))):
        t.p(x, y, B2)
    t.ligne(15, 3, 18, 6, O2)
    t.ligne(18, 3, 15, 6, O2)
    t.p(5, 4, B1)
    t.p(5, 2, B1)
    t.p(4, 3, B1)
    t.p(6, 3, B1)
    t.contour(BR1)
    ecrire("carte-tresor", t, commentaire="Carte au trésor (butin d'expédition, talisman)")


# =====================================================================================================
# Coffres, éclats, trophées, énergie, en-cas, pansement
# =====================================================================================================
def coffres():
    # Coffre d'expédition fermé (badge près de Pilou : « journal à lire ») : bois, ferrures argent, serrure jaune
    # qui scintille. Ouvert : couvercle relevé, pièces et un éclat.
    images = []
    for k in range(2):
        t = T(16, 14)
        t.rect(1, 5, 14, 8, BR2)
        t.rect(1, 1, 14, 5, BR3)
        t.rect(1, 5, 14, 1, BR1)
        for x in (3, 12):
            t.rect(x, 1, 1, 12, ARGENT)
        t.rect(7, 4, 2, 3, J3 if k == 0 else J4)
        t.p(7, 6, J1)
        if k == 1:
            t.p(9, 2, BLANC)
        t.contour(ENCRE)
        images.append(t)
    ecrire("coffre-expedition", images, duree=700, commentaire="Coffre d'expédition (fermé : un journal à lire)")
    t = T(18, 17)
    t.poly([(2, 7), (16, 7), (14, 1), (4, 1)], BR3)
    t.rect(4, 2, 10, 4, BR1)
    t.rect(2, 9, 14, 7, BR2)
    t.rect(2, 9, 14, 1, BR1)
    for (x, y) in ((5, 8), (8, 7), (11, 8), (6, 7), (10, 7), (13, 8)):
        t.p(x, y, J3)
    t.p(8, 6, J4)
    t.motif(12, 5, [".b.", "bcb", ".b."], {"b": B3, "c": B4})
    for x in (4, 13):
        t.rect(x, 9, 1, 7, ARGENT)
    t.contour(ENCRE)
    ecrire("coffre-expedition-ouvert", t, commentaire="Coffre d'expédition ouvert")


def eclat():
    # Éclat de cristal (les « fragments ») : losange bleu à facettes.
    t = T(9, 12)
    t.poly([(4.5, 0), (9, 5), (4.5, 12), (0, 5)], B3)
    t.poly([(4.5, 0), (9, 5), (4.5, 5)], B4)
    t.poly([(0, 5), (4.5, 5), (4.5, 12)], B2)
    t.p(3, 3, BLANC)
    t.contour(B1)
    ecrire("eclat-cristal", t, commentaire="Éclat de cristal (expéditions)")


def eclair():
    # Éclair d'énergie ⚡ (jauge) : jaune et crème, cerné d'encre ; un reflet passe.
    images = []
    for k in range(2):
        t = T(10, 15)
        t.poly([(6, 0), (1, 8), (4.5, 8), (3, 15), (9, 5.5), (5.5, 5.5), (7.5, 0)], J3)
        t.poly([(6, 0), (2.5, 6.5), (4.5, 6.5)], J4 if k == 0 else BLANC)
        t.contour(ENCRE)
        images.append(t)
    ecrire("eclair-energie", images, duree=600, commentaire="Éclair d'énergie (jauge des expéditions)")


def trophees():
    # Trophées de boss : la même coupe dorée, un emblème différent gravé par boss (signe de forme).
    emblemes = {
        "bug-geant": ["k.k.k", ".kkk.", "kkkkk", ".kkk.", "k...k"],       # un bug
        "slime-cache": ["..k..", ".kkk.", "kkkkk", "kkkkk", ".kkk."],     # une goutte
        "golem-tickets": ["kkkkk", "k...k", "kkkkk", "k...k", "kkkkk"],   # une pile de tickets
        "hydre-dependances": ["k.k.k", "k.k.k", ".kkk.", "..k..", "..k.."],  # trois têtes, un tronc
        "gargouille-latence": ["kkkkk", ".k.k.", "..k..", ".k.k.", "kkkkk"],  # un sablier
    }
    for boss, emb in emblemes.items():
        t = T(18, 20)
        t.ell(9, 6, 7, 6.5, J2, cond=lambda x, y, u, v: v >= -0.2)
        t.rect(2, 1, 14, 2, J2)
        t.ell(8, 6, 5, 5, J3, cond=lambda x, y, u, v: v >= -0.2)
        t.anneau(2, 6, 2.5, 3, J2, ep=1)
        t.anneau(16, 6, 2.5, 3, J2, ep=1)
        t.rect(7, 12, 4, 3, J2)
        t.rect(4, 15, 10, 2, J1)
        t.rect(3, 17, 12, 3, ARDOISE)
        t.rect(4, 18, 10, 1, ARDOISE_C)
        t.motif(7, 4, emb, {"k": J1})
        t.p(5, 3, J4)
        t.contour(ENCRE)
        ecrire("trophee-" + boss, t, commentaire="Trophée de boss : " + boss)


def encas():
    # En-cas de route (boutique) : galette ronde marquée d'un éclair ; jus d'étoile en fiole bleue.
    t = T(14, 11)
    t.ell(7, 5.5, 6.8, 5.2, S2)
    t.ell(6.5, 5, 5.6, 4.2, S3)
    for (x, y) in ((3, 4), (10, 3), (9, 8), (4, 8)):
        t.p(x, y, S1)
    t.motif(5, 2, ["..k", ".k.", "kkk", ".k.", "k.."], {"k": O2})
    t.contour(BR1)
    ecrire("galette-route", t, commentaire="En-cas de route : galette (+15 énergie)")
    t = T(10, 17)
    t.rect(3, 0, 4, 3, BR2)
    t.rect(4, 3, 2, 2, CREME_O)
    t.ell(5, 11, 4.6, 5.8, B2)
    t.ell(5, 12, 3.6, 4.4, B3)
    t.poly([(5, 8), (6, 10.3), (8.4, 10.5), (6.5, 12), (7.2, 14.4), (5, 13), (2.8, 14.4), (3.5, 12), (1.6, 10.5), (4, 10.3)], J3)
    t.p(3, 8, B4)
    t.contour(B1)
    ecrire("jus-etoile", t, commentaire="En-cas de route : jus d'étoile (+30 énergie)")


def pansement():
    # Cabossé : un pansement en croix sur le haut de la tête (et une petite bosse), après une défaite.
    t = T(11, 11)
    for i in range(9):
        t.rect(1 + i, 1 + i, 2, 2, S3)
        t.rect(8 - i, 1 + i, 2, 2, S3)
    t.rect(4, 4, 3, 3, CREME)
    t.p(5, 5, S2)
    t.p(2, 2, S2)
    t.p(8, 2, S2)
    t.contour(S1)
    ecrire("pansement", t, slot="effet", ancre="tete", point=(11, 4), commentaire="Pansement (rentré cabossé d'expédition)")


# =====================================================================================================
# Créatures (petites, deux images chacune) : on les voit dans la fenêtre des expéditions et la planche
# =====================================================================================================
def creatures():
    # Bug géant : scarabée ardoise à taches orange, six pattes qui trottinent, antennes.
    images = []
    for k in range(2):
        t = T(22, 16)
        t.ell(11, 9, 8, 5.6, ARDOISE)
        t.ell(11, 8, 6.5, 4, ARDOISE_C)
        t.ligne(11, 4, 11, 13, ENCRE)
        for (x, y) in ((7, 7), (15, 7), (8, 11), (14, 11)):
            t.p(x, y, O3)
        t.ell(11, 3.5, 3.5, 2.4, NOIR2)
        t.p(10, 3, O5)
        t.p(12, 3, O5)
        t.ligne(9, 2, 6 - k, 0, GRIS_C)
        t.ligne(13, 2, 16 + k, 0, GRIS_C)
        for i, y in enumerate((7, 10, 13)):
            d = (k + i) % 2
            t.ligne(3, y, 0, y - 1 + d * 2, GRIS_C)
            t.ligne(19, y, 21, y - 1 + (1 - d) * 2, GRIS_C)
        t.contour(ENCRE)
        images.append(t)
    ecrire("crea-bug-geant", images, duree=260, commentaire="Créature : bug géant")

    # Slime de cache : gelée sarcelle, une petite disquette en suspension dedans, deux yeux ronds.
    images = []
    for k in range(2):
        t = T(20, 16)
        h = 12 - k * 2
        t.ell(10, 16 - h / 2, 9 + k, h / 2, T2)
        t.ell(9, 16 - h * 0.65, 6, h * 0.25, T3)
        t.rect(12, 16 - h // 2, 4, 4, B1)
        t.rect(13, 16 - h // 2, 2, 1, CREME)
        t.rect(5, 16 - int(h * 0.7), 2, 2, BLANC)
        t.rect(9, 16 - int(h * 0.7), 2, 2, BLANC)
        t.p(6, 17 - int(h * 0.7), ENCRE)
        t.p(10, 17 - int(h * 0.7), ENCRE)
        t.contour(T1)
        images.append(t)
    ecrire("crea-slime-cache", images, duree=400, commentaire="Créature : slime de cache")

    # Spectre 404 : drap violet pâle, « 404 » sur le ventre, le bas qui ondule.
    chiffres = {"4": ["k.k", "k.k", "kkk", "..k", "..k"], "0": ["kkk", "k.k", "k.k", "k.k", "kkk"]}
    images = []
    for k in range(2):
        t = T(18, 20)
        t.ell(9, 8, 8, 8, V3, cond=lambda x, y, u, v: v <= 0)
        t.rect(1, 8, 16, 9, V3)
        for i in range(4):
            x = 1 + i * 4 + (k * 2)
            t.ell(x + 1, 17, 2, 2, V3)
        t.ell(6, 5, 1.4, 1.8, NUIT)
        t.ell(12, 5, 1.4, 1.8, NUIT)
        for i, c in enumerate("404"):
            t.motif(3 + i * 4, 10, chiffres[c], {"k": V1})
        t.contour(V1)
        images.append(t)
    ecrire("crea-spectre-404", images, duree=380, commentaire="Créature : spectre 404")

    # Golem de tickets : un tas de tickets crème empilés (lignes de texte), bras de pierre, yeux orange.
    images = []
    for k in range(2):
        t = T(24, 24)
        t.rect(5, 4 + k, 14, 19 - k, ARDOISE)
        for i, y in enumerate(range(5 + k, 22, 4)):
            dx = (0, 1, -1, 1, 0)[i % 5]
            t.rect(6 + dx, y, 12, 3, CREME)
            t.ligne(7 + dx, y + 1, 14 + dx, y + 1, GRIS)
        t.rect(8, 1 + k, 8, 4, GRIS)
        t.p(10, 3 + k, O3)
        t.p(13, 3 + k, O3)
        t.rect(0, 8 + k, 5, 4, GRIS)
        t.rect(19, 8 - k, 5, 4, GRIS)
        t.rect(0, 12 + k, 3, 4, ARDOISE_C)
        t.rect(21, 12 - k, 3, 4, ARDOISE_C)
        t.contour(ENCRE)
        images.append(t)
    ecrire("crea-golem-tickets", images, duree=500, commentaire="Créature : golem de tickets (boss)")

    # Hydre des dépendances : trois têtes bleu nuit sur des cous reliés comme un graphe, yeux orange.
    images = []
    for k in range(2):
        t = T(26, 22)
        t.ell(13, 18, 9, 4, B1)
        t.ell(13, 17, 7, 2.5, B2)
        for i, (hx, hy) in enumerate(((4, 5), (13, 2), (22, 5))):
            hy += (k + i) % 2
            t.ligne(13, 16, hx, hy + 2, B2)
            t.ligne(12 + (i - 1), 16, hx - 1 + (i == 0), hy + 3, B2)
            t.ell(hx, hy, 3, 2.4, B2)
            t.p(hx + (1 if i else -1), hy - 1, O3)
            t.p(hx + (2 if i else -2), hy + 1, B4)
        t.p(8, 11, O2)
        t.p(18, 11, O2)
        t.p(13, 9, O2)
        t.contour(NUIT)
        images.append(t)
    ecrire("crea-hydre-dependances", images, duree=340, commentaire="Créature : hydre des dépendances (boss)")

    # Gargouille de latence : pierre grise, ailes repliées qui battent, sablier jaune sur la poitrine.
    images = []
    for k in range(2):
        t = T(26, 22)
        w = 4 if k == 0 else 2
        t.poly([(9, 8), (1, 2 + w), (3, 14), (9, 14)], ARDOISE)
        t.poly([(17, 8), (25, 2 + w), (23, 14), (17, 14)], ARDOISE)
        t.ell(13, 13, 5.5, 7, GRIS)
        t.ell(13, 5, 4, 3.6, GRIS)
        t.p(10, 1, GRIS_C)
        t.p(16, 1, GRIS_C)
        t.p(11, 5, O3)
        t.p(15, 5, O3)
        t.motif(11, 10, ["kkkkk", ".kjk.", "..k..", ".kjk.", "kkkkk"], {"k": J1, "j": J3})
        t.rect(9, 19, 3, 2, ARDOISE)
        t.rect(14, 19, 3, 2, ARDOISE)
        t.contour(ENCRE)
        images.append(t)
    ecrire("crea-gargouille-latence", images, duree=450, commentaire="Créature : gargouille de latence (boss)")


def tout():
    epee_bois()
    bouclier_couvercle()
    torche()
    casque_passoire()
    slime_apprivoise()
    carte_tresor()
    coffres()
    eclat()
    eclair()
    trophees()
    encas()
    pansement()
    creatures()
