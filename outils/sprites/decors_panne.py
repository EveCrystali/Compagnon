"""Décors de « La Grande Panne » (humour) : l'intérieur d'un ordinateur, chaleureux et absurde.

Palette : plastique beige, gris d'administration, violets de circuits, bleu nuit de barre des tâches, deux néons
(cyan froid, orange chaud), le jaune des néons de guichet, cuivre des câbles et une gelée sarcelle (pas de vert).
Tout s'est arrêté à 13 h 37 : les horloges, l'afficheur, la barre de chargement à 37 %.
"""
import math

import toile
from decors_campagnes import decor
from peinture import (Palette, degrade, relief, voile, eclat, lueur, semis, ell, poly, rect, point, trait, hline, vline,
                      courbe, nuage, etoile4, hasard)

N0, N1, N2, N3 = "#141a33", "#1f2a52", "#2f3f78", "#4a5fa8"
E1, E2, E3, E4, E5 = "#5e5446", "#8a7d68", "#b8a98c", "#ddd0b2", "#f3ead2"
G0, G1, G2, G3, G4 = "#262a35", "#3a3f4b", "#5a6070", "#8890a0", "#b8bfcc"
V1, V2, V3, V4 = "#2b2145", "#463670", "#6a55a8", "#9b88d8"
C1, C2, C3 = "#2a8fc0", "#3fd0ff", "#b8f0ff"
O1, O2, O3 = "#c46a24", "#ff9a3c", "#ffd29a"
J1, J2, J3 = "#a8862a", "#e8c447", "#fff0a0"
K1, K2 = "#7a3f1e", "#b8652e"
T1, T2, T3 = "#1a6b70", "#2fb5b0", "#8ff0e0"
B1, B2, B3 = "#4a2e17", "#7a4b26", "#a86f3c"
BLANC, ENCRE = "#fbf7ee", "#11131c"
CIEL1, CIEL2, CIEL3 = "#9fb4de", "#c4d2ec", "#e6ecf6"

PAL = Palette(N0, N1, N2, N3, E1, E2, E3, E4, E5, G0, G1, G2, G3, G4, V1, V2, V3, V4, C1, C2, C3, O1, O2, O3, J1, J2, J3,
              K1, K2, T1, T2, T3, B1, B2, B3, BLANC, ENCRE, CIEL1, CIEL2, CIEL3).rampes(
    [ENCRE, N0, N1, N2, N3, CIEL1, CIEL2, CIEL3, BLANC], [E1, E2, E3, E4, E5, BLANC], [G0, G1, G2, G3, G4, E5],
    [V1, V2, V3, V4, CIEL3], [C1, C2, C3], [O1, O2, O3, E5], [J1, J2, J3, BLANC], [K1, K2, O2], [T1, T2, T3],
    [B1, B2, B3, J2, J3])

SEGMENTS = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc", "7": "abc",
            "8": "abcdefg", "9": "abcdfg"}


def chiffre(t, x, y, ch, c, l=3, h=6, ep=1, penche=0):
    """Chiffre à sept segments, coin haut-gauche (x, y) ; penche : décalage du haut (le 7 qui penche)."""
    s = SEGMENTS[ch]

    def seg(x0, y0, x1, y1):
        dx0, dx1 = penche * (1 - y0 / h), penche * (1 - y1 / h)
        trait(t, x + x0 + dx0, y + y0, x + x1 + dx1, y + y1, c, ep=ep)
    m = h / 2
    if "a" in s:
        seg(0.5, 0, l - 0.5, 0)
    if "b" in s:
        seg(l, 0.5, l, m - 0.5)
    if "c" in s:
        seg(l, m + 0.5, l, h - 0.5)
    if "d" in s:
        seg(0.5, h, l - 0.5, h)
    if "e" in s:
        seg(0, m + 0.5, 0, h - 0.5)
    if "f" in s:
        seg(0, 0.5, 0, m - 0.5)
    if "g" in s:
        seg(0.5, m, l - 0.5, m)


def guichet(t, x, y, w, h, rideau=True, k=0, panneau=True):
    """Guichet : encadrement beige, rideau baissé à lamelles, petit panneau « retour à… »."""
    rect(t, x - 1, y - 2, w + 2, h + 2, E2)
    hline(t, x - 1, x + w + 1, y - 2, E4)
    rect(t, x, y, w, h, G2)
    if rideau:
        for j in range(int(h)):
            hline(t, x, x + w, y + j + 0.5, G3)
    if panneau:
        rect(t, x + w / 2 - 2.5, y + h * 0.45, 5, 3, BLANC)
        hline(t, x + w / 2 - 1.8, x + w / 2 + 1.8, y + h * 0.45 + 1, G1)
        hline(t, x + w / 2 - 1.2, x + w / 2 + 1.2, y + h * 0.45 + 2, O1)
        vline(t, x + w / 2, y - 0.5, y + h * 0.45, G1)
    rect(t, x - 1.5, y + h, w + 3, 1.5, E3)


def engrenage(t, cx, cy, r, c, c2, dents=10, a0=0.0):
    for i in range(dents):
        a = a0 + i * 2 * math.pi / dents
        x, y = cx + (r + 0.8) * math.cos(a), cy + (r + 0.8) * math.sin(a)
        ell(t, x, y, max(0.9, r * 0.18), max(0.9, r * 0.18), c)
    ell(t, cx, cy, r, r, c)
    ell(t, cx, cy, r * 0.62, r * 0.62, c2)
    ell(t, cx, cy, r * 0.22, r * 0.22, c)


def dossier(t, x, y, w, h, c=J2, c2=J1, clair=J3):
    """Dossier jaune paille avec son onglet."""
    rect(t, x, y + 1, w, h - 1, c2)
    rect(t, x + 0.5, y, w * 0.4, 1.5, c2)
    rect(t, x, y + 1.6, w, h - 1.6, c)
    hline(t, x, x + w, y + 1.6, clair)


def file_attente(t, pts, couleurs, graine=0, pas=2.6):
    """Une file d'attente de petites feuilles qui patientent, deux points pour les yeux, deux pattes."""
    for i, (x, y) in enumerate(pts):
        c = couleurs[i % len(couleurs)]
        h = 3 + (i % 3 == 1) * 0.6
        rect(t, x - 1, y - h, 2, h, c)
        if toile.fin():
            point(t, x - 0.5, y - h + 1, G1)
            point(t, x + 0.5, y - h + 1, G1)
            point(t, x + 0.5, y - h, G3)
        vline(t, x - 0.5, y, y + 0.8, G0)
        vline(t, x + 0.5, y, y + 0.8, G0)


@decor("grande-panne", "bureau-1337", images=2, duree=700)
def bureau_1337(t, k):
    # Le fond d'écran, pâle et froid du petit matin : une colline lisse, un ciel bleu dégradé.
    degrade(t, 0, 30, [CIEL1, CIEL2, CIEL3])
    relief(t, lambda x: 22 + 3 * math.sin(x / 14 + 1), CIEL1, lisere=BLANC)
    relief(t, lambda x: 26 + 2 * math.sin(x / 9), N3, lisere=CIEL2)
    # Une icône abandonnée sur le bureau : « Nouveau dossier ».
    dossier(t, 6, 4, 7, 5)
    rect(t, 5, 10.5, 9, 1, BLANC)
    # La barre des tâches bleu nuit, vue de tout près, très grande.
    rect(t, 0, 28, 96, 12, N1)
    hline(t, 0, 96, 28, N3)
    rect(t, 2, 30, 8, 8, N2)
    for (a, b) in ((3.5, 31.5), (6.5, 31.5), (3.5, 34.5), (6.5, 34.5)):
        rect(t, a, b, 2, 2, C2)
    for i, c in enumerate((O2, J2, V4)):
        rect(t, 14 + i * 9, 30.5, 7, 7, N2)
        rect(t, 15.5 + i * 9, 32, 4, 4, c)
    hline(t, 14, 21, 38, C2)
    # La grande horloge numérique figée sur 13:37 ; le dernier 7 penche un peu. Deux points qui clignotent.
    x0 = 56
    rect(t, 52, 29.5, 42, 9.5, N0)
    for i, ch in enumerate("13"):
        chiffre(t, x0 + i * 6, 31, ch, C3, l=3.6, h=6.5, ep=t.e)
    if k == 0:
        rect(t, x0 + 12.6, 32.6, 1, 1, C3)
        rect(t, x0 + 12.6, 35.6, 1, 1, C3)
    chiffre(t, x0 + 15.5, 31, "3", C3, l=3.6, h=6.5, ep=t.e)
    chiffre(t, x0 + 21.5, 31.6, "7", C3, l=3.6, h=6.5, ep=t.e, penche=1.6)
    # Petits pictos de la barre : son, réseau.
    trait(t, 87, 33, 88.5, 31.5, G4, ep=1)
    trait(t, 87, 33, 88.5, 34.5, G4, ep=1)
    rect(t, 85.5, 32.4, 1.5, 1.4, G4)
    for i in range(3):
        rect(t, 90 + i * 1.3, 35 - i * 1.2, 0.8 if toile.fin() else 1, 1 + i * 1.2, G4)


@decor("grande-panne", "hall-pas-comptes", images=2, duree=600)
def hall(t, k):
    # Hall de gare immense : voûte beige, verrière, piliers.
    degrade(t, 0, 40, [E3, E4, E3, E2])
    for i in range(7):
        x = 6 + i * 14
        rect(t, x - 1.2, 4, 2.4, 22, E2)
        vline(t, x - 1.2, 4, 26, E4)
    ell(t, 48, 4, 52, 6, E5, cond=lambda x, y, u, v: v > 0)
    for i in range(12):
        trait(t, 48, 0, 4 + i * 8, 9.5, E3, ep=1)
    # L'afficheur lumineux « 1 337 ».
    rect(t, 34, 7, 28, 9, ENCRE)
    for i, ch in enumerate("1337"):
        chiffre(t, 37 + i * 6.2 + (1.4 if i > 0 else 0), 8.5, ch, O2 if k == 0 or i < 3 else O1, l=3.4, h=6, ep=t.e)
    # Les guichets aux rideaux baissés, « retour à 13 h 38 ».
    for i in range(6):
        guichet(t, 3 + i * 16, 19, 10, 7, k=k)
    # Le sol de dalles, la file en serpentin entre ses poteaux.
    rect(t, 0, 27, 96, 13, G3)
    for i in range(0, 96, 8):
        trait(t, 48 + (i - 48) * 0.4, 27, i, 40, G2, ep=1)
    for y in (29.5, 33):
        hline(t, 0, 96, y, G2)
    for i, y in enumerate((29, 31.5, 34)):
        x0, x1 = (20, 76)
        hline(t, x0, x1, y - 1.5, O1)
        for x in range(int(x0), int(x1) + 1, 8):
            rect(t, x - 0.5, y - 2.5, 1, 3, G1)
            ell(t, x, y - 2.6, 0.8, 0.8, J2)
    pts = [(24 + i * 3, 29) for i in range(17)] + [(72 - i * 3, 31.5) for i in range(14)] + [(30 + i * 3, 34) for i in range(9)]
    file_attente(t, pts, [BLANC, E5, C3], graine=3)
    # Le banc de bois au premier plan.
    rect(t, 2, 35, 30, 1.6, B3)
    rect(t, 2, 37.3, 30, 1.6, B2)
    hline(t, 2, 32, 35, J2)
    for x in (4, 29):
        rect(t, x, 36.6, 1.2, 3.4, B1)
    # Détail : une feuille de papier s'est endormie sur le banc.
    rect(t, 12, 33, 4, 2, BLANC)
    point(t, 16.5, 31.5, G3)
    point(t, 17.3, 30.6, G3)


@decor("grande-panne", "tour-tampon", images=2, duree=900)
def tour(t, k):
    degrade(t, 0, 40, [G2, G3, E3, J3])
    # La tour de pierre grise qui se perd dans la brume.
    poly(t, [(36, 40), (60, 40), (57, 0), (39, 0)], G1)
    poly(t, [(36, 40), (44, 40), (42, 0), (39, 0)], G2)
    for j in range(0, 40, 4):
        hline(t, 39, 58, j, G0)
        for x in range(38 + (j // 4 % 2) * 3, 58, 6):
            vline(t, x, j, j + 4, G0)
    voile(t, lambda x, y: max(0, 1 - y / 16), G3, PAL, (0, 0, 96, 18), niveaux=3)
    # Néon jaune administratif au-dessus de la porte.
    rect(t, 42, 22, 12, 1.4, J3 if k == 0 else J2)
    lueur(t, 48, 23, 26, J3, PAL, force=0.4, ry=12, teinte=True)
    # La porte basse et le tabouret trop petit.
    ell(t, 48, 32, 3.5, 3.5, ENCRE, cond=lambda x, y, u, v: y < 32)
    rect(t, 44.5, 32, 7, 6, ENCRE)
    rect(t, 52.5, 35, 2.5, 0.8, B3)
    vline(t, 53, 35.8, 37.8, B2)
    vline(t, 54.5, 35.8, 37.8, B2)
    # La file d'attente enroulée trois fois autour de la base (on la voit passer devant et ressortir).
    for tour_ in range(3):
        y = 37.5 - tour_ * 2.4
        pts = [(x, y) for x in range(4 + tour_ * 4, 36, 3)] + [(x, y) for x in range(61, 94 - tour_ * 4, 3)]
        file_attente(t, pts, [BLANC, E5, C3], graine=10 + tour_)
    rect(t, 0, 38, 96, 2, G1)
    hline(t, 0, 96, 38, G3)


@decor("grande-panne", "etage-guichets", images=2, duree=1100)
def etage(t, k):
    rect(t, 0, 0, 96, 40, E2)
    # Casiers de formulaires de toutes les couleurs, jusqu'au plafond.
    for j in range(5):
        for i in range(10):
            x, y = 30 + i * 6.6, 1 + j * 5
            rect(t, x, y, 6.2, 4.6, E1)
            c = (O2, C2, J2, V4, BLANC, O3, T2)[int(hasard(i, j, 4) * 7)]
            rect(t, x + 0.6, y + 1.4 + hasard(i, j, 5) * 1.5, 5, 3, c)
            hline(t, x + 0.6, x + 5.6, y + 1.4 + hasard(i, j, 5) * 1.5, BLANC)
    # Le guichet vitré.
    rect(t, 30, 26, 66, 14, B2)
    hline(t, 30, 96, 26, B3)
    rect(t, 44, 15, 30, 11, C3)
    voile(t, lambda x, y: 0.5, E4, PAL, (44, 15, 74, 26), famille=[C3, E4, E5])
    rect(t, 44, 15, 30, 1, G2)
    rect(t, 58.5, 15, 1, 11, G2)
    ell(t, 59, 24.5, 4, 1.5, ENCRE, cond=lambda x, y, u, v: v < 0)
    # Les tampons sur le comptoir.
    for i, x in enumerate((36, 40, 80, 86)):
        rect(t, x - 1, 24, 2.4, 2, (O2, V3, C1, O1)[i])
        rect(t, x - 0.4, 21.5, 1.2, 2.5, B2)
        ell(t, x + 0.2, 21.3, 1, 0.8, B3)
    # Le palier d'escalier en colimaçon, à gauche.
    rect(t, 0, 0, 28, 40, G1)
    for i in range(8):
        y = 38 - i * 5
        x = 12 + 8 * math.sin(i * 0.8)
        poly(t, [(x - 8, y), (x + 8, y), (x + 7, y + 2), (x - 7, y + 2)], G3)
        hline(t, x - 8, x + 8, y, G4)
    rect(t, 27, 0, 2, 40, E1)
    # Affiches réglementaires.
    rect(t, 3, 6, 8, 10, BLANC)
    for y in (8, 10, 12, 14):
        hline(t, 4, 10, y, G2)
    poly(t, [(5.5, 7), (8.5, 7), (7, 9.5)], O2)
    # Rai de lumière et poussière dorée.
    eclat(t, lambda x, y: 1 if 0 < (x - 30) - (40 - y) * 0.6 < 10 else 0, PAL, n=1, cadre=(28, 0, 96, 40))
    semis(t, lambda x, y: 0 < (x - 30) - (40 - y) * 0.6 < 10, [J3, BLANC], 0.18, graine=7 + k, cadre=(28, 0, 96, 40))


@decor("grande-panne", "bureau-echeance", images=1)
def echeance(t, k):
    rect(t, 0, 0, 96, 40, V2)
    # Le mur couvert de cartes épinglées en rangs serrés : cochées à gauche, vierges à droite.
    for j in range(6):
        for i in range(19):
            x, y = 2 + i * 5, 2 + j * 4.2
            rect(t, x, y, 4, 3.2, E5 if i >= 9 else E4)
            point(t, x + 2, y + 0.3, O2)
            if i < 9:
                trait(t, x + 0.8, y + 1.8, x + 1.6, y + 2.6, V2, ep=1)
                trait(t, x + 1.6, y + 2.6, x + 3.2, y + 0.9, V2, ep=1)
    # Lumière feutrée d'une fin d'après-midi qui n'arrive pas.
    eclat(t, lambda x, y: 1 if x > 70 else 0, PAL, n=1, sens=-1, cadre=(0, 0, 96, 27))
    # Le grand bureau gris, la réussite en cours.
    rect(t, 0, 27, 96, 13, G1)
    poly(t, [(8, 27), (88, 27), (92, 33), (4, 33)], G3)
    hline(t, 8, 88, 27, G4)
    rect(t, 6, 33, 84, 2, G2)
    for i in range(7):
        x = 22 + i * 6
        for j in range(i % 3 + 1):
            rect(t, x, 28 + j * 1.2, 3.4, 2.6, BLANC)
            hline(t, x, x + 3.4, 28 + j * 1.2, G2)
        point(t, x + 1.5, 29.5 + (i % 3) * 1.2, O1 if i % 2 else N2)
    # La lampe à abat-jour sarcelle (pas verte : ici tout est sarcelle).
    rect(t, 79, 22, 1, 5.5, J1)
    rect(t, 76, 27, 7, 1, J1)
    poly(t, [(73, 22), (86, 22), (84, 18.5), (75, 18.5)], T1)
    hline(t, 75, 84, 18.8, T2)
    lueur(t, 79.5, 26, 16, J3, PAL, force=0.45, ry=7, teinte=True)
    # Détail : une carte vient de tomber par terre, ni cochée ni vierge.
    poly(t, [(60, 37), (64, 36), (65, 38.5), (61, 39.5)], E5)
    point(t, 62.4, 37.6, O2)


@decor("grande-panne", "caverne-cables", images=2, duree=500)
def caverne(t, k):
    rect(t, 0, 0, 96, 40, N0)
    ell(t, 60, 20, 20, 14, N1)
    ell(t, 60, 20, 10, 7, N2)
    # Diodes qui clignotent au loin.
    for i in range(10):
        x, y = 44 + hasard(i, 1, 2) * 32, 10 + hasard(i, 2, 2) * 18
        point(t, x, y, (C2, O2, J3)[i % 3] if (i + k) % 2 else N3)
    # Câbles épais comme des troncs, emmêlés du sol au plafond.
    cables = [((-4, 6), (30, 30), (50, -10), (100, 8), K1, K2), ((-5, 34), (20, 0), (60, 50), (100, 26), G1, G3),
              ((10, -5), (25, 30), (40, 30), (34, 45), V2, V3), ((70, -5), (60, 20), (90, 20), (80, 45), N3, CIEL1),
              ((-4, 22), (30, 40), (70, 0), (100, 36), B1, B3), ((84, -5), (100, 20), (70, 30), (100, 44), K1, K2)]
    for (a, b, c, d, f, cl) in cables:
        for ep, coul in ((5, ENCRE), (4, f)):
            for i in range(41):
                u = i / 40
                x = (1 - u) ** 3 * a[0] + 3 * (1 - u) ** 2 * u * b[0] + 3 * (1 - u) * u * u * c[0] + u ** 3 * d[0]
                y = (1 - u) ** 3 * a[1] + 3 * (1 - u) ** 2 * u * b[1] + 3 * (1 - u) * u * u * c[1] + u ** 3 * d[1]
                ell(t, x, y, ep / 2, ep / 2, coul)
        courbe(t, [(a[0], a[1] - 1), (b[0], b[1] - 1), (c[0], c[1] - 1), (d[0], d[1] - 1)], cl, ep=1)
    # La gelée lumineuse au croisement.
    ell(t, 34, 34, 9, 3.5, T1)
    ell(t, 34, 33.4, 7, 2.4, T2)
    ell(t, 32, 32.8, 3, 1, T3)
    lueur(t, 34, 32, 20, T3, PAL, force=0.4, ry=12, teinte=True)
    for (x, y) in ((28, 30), (40, 29.5)):
        ell(t, x, y - k * 0.6, 0.8, 0.8, T3)


@decor("grande-panne", "marais-majs", images=2, duree=800)
def marais(t, k):
    degrade(t, 0, 24, [G2, G3, G4])
    # Au lieu du soleil, la barre de chargement arrêtée à 37 %.
    rect(t, 22, 6, 52, 6, G1)
    rect(t, 23, 7, 50, 4, G0)
    rect(t, 23, 7, 50 * 0.37, 4, C2)
    hline(t, 23, 23 + 50 * 0.37, 7, C3)
    # Eau grise, brume froide.
    degrade(t, 24, 40, [G3, G2, G1])
    rect(t, 22, 25, 52, 2, G2)
    rect(t, 23, 25.6, 18.5, 1, C1)
    voile(t, lambda x, y: 0.5 if 20 < y < 27 else 0, G4, PAL, (0, 18, 96, 28))
    # Roseaux qui clignotent (pointes allumées une image sur deux, en quinconce).
    for i in range(24):
        x = (i * 4.1 + hasard(i, 1, 3) * 3) % 96
        bas = 33 + hasard(i, 2, 3) * 7
        h = 6 + hasard(i, 3, 3) * 9
        if 30 < x < 64 and bas < 36:
            continue
        trait(t, x, bas, x + 1, bas - h, G0, ep=1)
        point(t, x + 1, bas - h, (O2 if i % 3 else C2) if (i + k) % 2 else G1)
    # La barque carrée qui glisse.
    bx = 44 + k
    poly(t, [(bx - 7, 30), (bx + 7, 30), (bx + 6, 33), (bx - 6, 33)], B2)
    hline(t, bx - 7, bx + 7, 30, B3)
    hline(t, bx - 8, bx + 8, 33.5, G4)
    trait(t, bx + 3, 30, bx + 8, 24, B1, ep=1)


@decor("grande-panne", "file-impression", images=2, duree=600)
def file_impression(t, k):
    rect(t, 0, 0, 96, 40, E1)
    for x in range(0, 96, 12):
        rect(t, x, 0, 11, 20, E2)
    # L'estrade et l'énorme imprimante beige au voyant orange.
    rect(t, 56, 22, 40, 6, B2)
    hline(t, 56, 96, 22, B3)
    rect(t, 60, 6, 32, 16, E4)
    rect(t, 60, 6, 32, 3, E5)
    rect(t, 63, 12, 26, 2, E1)
    rect(t, 64, 14, 24, 1.5, BLANC)
    rect(t, 62, 17, 28, 5, E3)
    ell(t, 87, 9.5, 1.2, 1.2, O2 if k == 0 else O1)
    if k == 0:
        lueur(t, 87, 9.5, 8, O3, PAL, force=0.5, teinte=True)
    for x in (66, 71, 76):
        rect(t, x, 9.5, 3, 1, E2)
    # Le quai de rames de papier, les feuilles jaunies qui attendent debout, en rang.
    for i in range(12):
        x = 2 + i * 6.5
        rect(t, x - 0.5, 34, 6, 6, BLANC)
        for j in range(3):
            hline(t, x - 0.5, x + 5.5, 35 + j * 1.8, E4)
    for i in range(9):
        x = 6 + i * 5.6
        h = 9 + (i % 2)
        poly(t, [(x, 34), (x + 3.4, 34), (x + 3.6, 34 - h), (x + 0.4, 34 - h + 0.4)], E5 if i % 3 else E4)
        point(t, x + 1.2, 34 - h + 3, G1)
        point(t, x + 2.4, 34 - h + 3, G1)
        hline(t, x + 0.8, x + 2.8, 34 - h + 5, E2)
    # Lumière de réserve à fournitures : une ampoule nue.
    vline(t, 30, 0, 5, G1)
    ell(t, 30, 6, 1.5, 1.8, J3)
    lueur(t, 30, 6, 28, J3, PAL, force=0.35, ry=18, teinte=True)


@decor("grande-panne", "citadelle-nuage", images=2, duree=1000)
def citadelle(t, k):
    degrade(t, 0, 40, [V1, V2, V3, V4])
    for i in range(14):
        etoile4(t, hasard(i, 1, 6) * 96, hasard(i, 2, 6) * 14, CIEL3 if (i + k) % 3 else J3, r=0)
    # Très loin en dessous, les lumières de l'ordinateur comme une ville la nuit.
    rect(t, 0, 33, 96, 7, N0)
    for i in range(40):
        x, y = hasard(i, 3, 6) * 96, 34 + hasard(i, 4, 6) * 6
        point(t, x, y, (O2, J3, C2)[i % 3] if (i + k) % 5 else N2)
    # La mer de brume.
    for i, (x, y, l) in enumerate(((10, 31, 30), (44, 33, 34), (80, 31, 30), (30, 35, 30), (70, 36, 36))):
        nuage(t, x + (k * 0.5 if i % 2 else 0), y, l, 3, CIEL2, BLANC, V4)
    # Les remparts blancs, le donjon, la gargouille au bord du vide.
    rect(t, 30, 18, 46, 12, E5)
    for x in range(30, 76, 4):
        rect(t, x, 16, 2.4, 2, E5)
    rect(t, 48, 6, 12, 14, E5)
    for x in range(48, 60, 3):
        rect(t, x, 4.5, 1.8, 1.6, E5)
    eclat(t, lambda x, y: 1 if x > 66 or (54 < x < 60 and y < 18) else 0, PAL, n=1, sens=-1, cadre=(30, 4, 76, 30),
          sur=(E5,))
    rect(t, 52.5, 10, 3, 4, N1)
    ell(t, 54, 10, 1.5, 1.5, N1)
    point(t, 54, 11.5, J3)
    rect(t, 36, 22, 2, 3, N1)
    rect(t, 66, 22, 2, 3, N1)
    poly(t, [(76, 18), (79, 17), (81, 18.5), (79, 20), (76, 20)], G3)
    point(t, 80, 18, ENCRE)
    poly(t, [(77, 16.5), (78, 15), (78.5, 17)], G2)
    # L'escalier dont les dernières marches sont encore à moitié transparentes.
    for i in range(6):
        x, y = 26 - i * 4, 28 + i * 1.6
        rect(t, x, y, 5, 1.6, E4)
        if i >= 3:
            voile(t, lambda a, b: 0.5 if i == 3 else 0.9, V3, PAL, (x, y, x + 5, y + 1.6), famille=[V3, V4, E4, CIEL2])


@decor("grande-panne", "dossier-temp", images=1)
def dossier_temp(t, k):
    degrade(t, 0, 40, [G3, G4, E4])
    # Des piles de dossiers jusqu'au ciel : les lointaines dans la brume, les proches bien jaunes.
    for plan, (c, c2, cl, y0, n) in enumerate(((G4, G3, E5, 30, 9), (E3, E2, E4, 33, 7), (J2, J1, J3, 37, 5))):
        for i in range(n):
            x = (i + 0.35 * plan) * 96 / n + hasard(i, plan, 8) * 4 - 2
            h = 12 + hasard(i, plan + 3, 8) * (24 - plan * 4)
            w = 7 + plan * 2.5
            rect(t, x, y0 - h, w, h, c)
            vline(t, x + w - 0.5, y0 - h, y0, c2)
            for j in range(int(h / 2.5)):
                y = y0 - j * 2.5
                hline(t, x, x + w, y - 0.5, c2)
                ox = (hasard(i, j, plan) - 0.5) * 2
                rect(t, x + (1 if j % 2 else w - 3.5) + ox * 0.3, y - 2.9, 2.5, 0.8 if toile.fin() else 1, cl)
            hline(t, x, x + w, y0 - h, cl)
        if plan == 0:
            voile(t, lambda x, y: 0.5, G4, PAL, (0, 0, 96, 31), famille=[G4, G3, E4])
    # Une étiquette « Nouveau dossier (7) » : des traits pour les mots, un chiffre lisible.
    rect(t, 40, 24, 12, 4, BLANC)
    hline(t, 41, 47, 25.5, G2)
    chiffre(t, 48.2, 24.6, "7", O1, l=1.6, h=2.6, ep=1)
    # Les allées poussiéreuses, des mots raturés sur les murs.
    rect(t, 0, 36, 96, 4, E2)
    semis(t, lambda x, y: True, [E3, E1], 0.2, graine=3, cadre=(0, 36, 96, 40))
    for (x, y) in ((8, 12), (70, 9), (84, 20)):
        hline(t, x, x + 7, y, G2)
        trait(t, x - 0.5, y + 0.6, x + 7.5, y - 0.6, O1, ep=1)
    voile(t, lambda x, y: 0.5 if y < 12 else 0, G4, PAL, (0, 0, 96, 14))


@decor("grande-panne", "cabane-brouillon", images=2, duree=900)
def cabane(t, k):
    # Murs de brouillons froissés et collés.
    rect(t, 0, 0, 96, 40, E4)
    for i in range(60):
        x, y = hasard(i, 1, 4) * 96, hasard(i, 2, 4) * 32
        w, h = 6 + hasard(i, 3, 4) * 6, 4 + hasard(i, 5, 4) * 4
        poly(t, [(x, y), (x + w, y + 0.6), (x + w - 0.5, y + h), (x + 0.4, y + h - 0.5)], (E5, E4, BLANC, E3)[i % 4])
        trait(t, x + 1, y + 1, x + w * 0.6, y + h * 0.7, E3, ep=1)
        if i % 5 == 0:
            hline(t, x + 1, x + w - 1, y + 2, G3)
    # Bandes de ruban adhésif, fenêtre de papier calque.
    rect(t, 62, 6, 18, 13, CIEL3)
    voile(t, lambda x, y: 0.5, E5, PAL, (62, 6, 80, 19), famille=[CIEL3, E5, BLANC])
    rect(t, 70.5, 6, 1, 13, E3)
    rect(t, 62, 12, 18, 1, E3)
    # Le hamac en ruban adhésif.
    courbe(t, [(8, 10), (22, 24), (40, 10)], O3, ep=t.e * 2)
    courbe(t, [(8, 10), (22, 22), (40, 10)], E5, ep=1)
    # La table basse, les cartes à jouer.
    rect(t, 40, 30, 30, 2, B3)
    rect(t, 42, 32, 1.6, 5, B2)
    rect(t, 66, 32, 1.6, 5, B2)
    for i in range(4):
        x = 46 + i * 4.5
        rect(t, x, 28.4, 3, 2, BLANC)
        point(t, x + 1, 29.2, (O1, N2, O1, N2)[i])
    # La lampe chaude, et le sol de papier.
    rect(t, 82, 22, 1.4, 8, B1)
    poly(t, [(78, 22), (88, 22), (86, 17), (80, 17)], O2)
    lueur(t, 83, 24, 16, J3, PAL, force=0.35, ry=10)
    rect(t, 0, 36, 96, 4, E3)
    semis(t, lambda x, y: True, [E2, E5], 0.2, graine=9, cadre=(0, 36, 96, 40))
    # Une boulette de papier qui tombe du hamac.
    ell(t, 26, 26 + k * 3, 1.3, 1.3, BLANC)
    point(t, 26.4, 26.4 + k * 3, E3)


@decor("grande-panne", "horloge-systeme", images=1)
def horloge(t, k):
    degrade(t, 0, 40, [N0, N1, N2])
    # Les murs de roues dentées immobiles.
    for i, (x, y, r) in enumerate(((8, 8, 7), (20, 20, 5), (6, 28, 4), (88, 10, 8), (76, 24, 5), (90, 30, 4),
                                    (30, 4, 4), (66, 4, 4))):
        engrenage(t, x, y, r, N3, N1, dents=8 + int(r), a0=i)
    # La lumière bleutée qui tombe d'en haut.
    eclat(t, lambda x, y: 1 if abs(x - 48) < 10 + y * 0.35 else 0, PAL, n=1, cadre=(0, 0, 96, 40))
    # Le grand balancier doré, arrêté, penché d'un côté.
    a = math.radians(14)
    ox, oy, l = 48, 2, 26
    ex, ey = ox + l * math.sin(a), oy + l * math.cos(a)
    trait(t, ox, oy, ex, ey, J1, ep=t.e + 1)
    trait(t, ox + 0.5, oy, ex + 0.5, ey, J3, ep=1)
    ell(t, ex, ey, 4.5, 4.5, J1)
    ell(t, ex, ey, 3.7, 3.7, J2)
    ell(t, ex - 1.2, ey - 1.2, 1.5, 1.2, J3)
    ell(t, ox, oy, 2, 2, J1)
    # Le sol rond, le levier au pied, la trappe ronde au fond.
    ell(t, 48, 40, 50, 6, N3)
    ell(t, 48, 40, 46, 4.5, N2)
    ell(t, 76, 36, 6, 1.8, ENCRE)
    ell(t, 76, 35.6, 4.6, 1.2, N0)
    rect(t, 34, 32, 4, 3, G2)
    trait(t, 36, 32, 32, 26, G4, ep=t.e)
    ell(t, 32, 26, 1.3, 1.3, O2)
