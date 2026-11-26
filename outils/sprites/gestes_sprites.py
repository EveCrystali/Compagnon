"""Petits gestes de Pilou sur le PC : il tape au clavier, il prend une photo quand tu fais une capture
d'écran, il t'apporte une notification. Appelé par generer.py.

    pouf-1 … pouf-5      nuage de fumée (entrée et sortie de scène), une image par étape
    clavier-mini         mini clavier devant Pilou assis, touches qui s'enfoncent, pattes qui tapent
    appareil-photo       appareil tenu devant les yeux (il photographie l'écran)
    photo-flash          éclat du flash (une image, très brève)
    polaroid-1 … -4      la photo sort, tombe en se balançant et se pose au sol (elle se développe)
    enveloppe-notif      enveloppe ouverte brandie au-dessus de la tête (une lettre dépasse)
    enveloppe-close      enveloppe fermée (mode « masquer le contenu »)

Palette bleu / orange / crème / ardoise : jamais d'opposition rouge-vert. Chaque état a aussi un signe de
forme : la touche enfoncée descend d'un pixel (pas seulement orange), l'enveloppe ouverte montre une lettre
alors que la fermée porte un cachet rond, la photo se développe de l'ardoise au bleu.
"""
import math

from toile import Toile, ecrire

ENCRE = "#1c2128"
BLANC = "#ffffff"
CREME = "#f6f8fa"
CREME_O = "#c9d1d9"
GRIS = "#768390"
GRIS_C = "#adbac7"
BRUME = "#e6edf3"
ARDOISE = "#3b4654"
ARDOISE_C = "#545d68"
B1, B2, B3, B4 = "#1f4f8a", "#4a8fdc", "#6cb6ff", "#b4dbff"
O1, O2, O3, O4, O5 = "#8a4a1f", "#d9803a", "#f69d50", "#ffc89a", "#ffd8b0"
J4 = "#fff6cc"


def T(w, h):
    return Toile(w, h)


def etoile(t, x, y, c, centre=None):
    for (u, v) in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
        t.p(x + u, y + v, c)
    if centre:
        t.p(x, y, centre)


# ---- Pouf de fumée : posé sur l'ancre « corps » (≈ (24, 37) au stade 2), il couvre Pilou au plus fort.

POUF_POINT = (23, 26)


def boule(t, cx, cy, r):
    """Une volute : disque brume, ombre grise en bas à droite, reflet blanc en haut à gauche."""
    t.ell(cx, cy, r, r * 0.9, BRUME)
    t.ell(cx + r * 0.25, cy + r * 0.3, r * 0.8, r * 0.6, GRIS_C, cond=lambda x, y, u, v: v > 0.25)
    if r >= 3:
        t.p(int(cx - r * 0.4), int(cy - r * 0.45), BLANC)
        t.p(int(cx - r * 0.4) + 1, int(cy - r * 0.45), BLANC)


def pouf():
    # (cx, cy, r) des volutes de chaque étape, sur une toile 46 × 44 dont le pixel (23, 26) est le centre du corps.
    etapes = [
        # 1 : trois petites bouffées au sol
        [(14, 37, 3.5), (23, 39, 4.5), (32, 37, 3.5)],
        # 2 : le nuage monte
        [(11, 34, 5), (20, 36, 6), (30, 35, 6), (36, 31, 4), (16, 27, 4.5), (27, 26, 5)],
        # 3 : plein nuage, Pilou disparaît dedans
        [(9, 30, 6.5), (19, 33, 8), (31, 32, 8), (38, 25, 6), (12, 19, 6.5), (24, 17, 7.5), (34, 14, 5.5),
         (24, 27, 9), (17, 9, 4)],
        # 4 : il se déchire, des trous apparaissent
        [(6, 31, 4.5), (17, 36, 5), (33, 35, 5.5), (40, 23, 4.5), (8, 17, 4.5), (22, 9, 4.5), (36, 10, 4)],
        # 5 : quelques filets qui s'en vont
        [(3, 28, 2.5), (42, 31, 3), (10, 8, 2.5), (38, 4, 2)],
    ]
    for k, volutes in enumerate(etapes):
        t = T(46, 44)
        for (cx, cy, r) in volutes:
            boule(t, cx, cy, r)
        t.contour(GRIS)
        # Étincelles orange et bleues quand il réapparaît (signe de forme : des croix, pas une couleur seule).
        if k >= 3:
            for i, (x, y) in enumerate(((12, 26), (35, 20), (24, 4), (5, 12), (42, 15))):
                if (i + k) % 2 == 0 or k == 4:
                    etoile(t, x, y, O3 if i % 2 == 0 else B3, J4)
        ecrire("pouf-%d" % (k + 1), t, slot="effet", ancre="corps", point=POUF_POINT,
               commentaire="Pouf de fumée, étape %d sur 5" % (k + 1))


# ---- Mini clavier : devant Pilou assis, sur l'ancre « pieds » (≈ (24, 52) assis). Deux pattes à la teinte
# de Pilou tapent à tour de rôle ; la touche frappée s'enfonce d'un pixel et passe à l'orange.

def clavier():
    images = []
    frappes = [(0, 3), (1, 8), (0, 6), (2, 4), (1, 2), (0, 9)]  # (rangée, colonne) de la touche frappée
    for k, (rf, cf) in enumerate(frappes):
        t = T(36, 11)
        # Socle en légère perspective : dessus ardoise clair, tranche ardoise sombre.
        t.poly([(3, 2), (33, 2), (36, 9), (0, 9)], ARDOISE_C)
        t.rect(0, 9, 36, 2, ARDOISE)
        for r in range(3):
            n = 12 - (1 if r == 2 else 0)
            x0 = 5 - r + (1 if r == 2 else 0)
            for i in range(n):
                x = x0 + i * 2 + (r * 0)
                y = 3 + r * 2
                if r == rf and i == cf:
                    t.p(x, y + 1, O3)        # enfoncée : un pixel plus bas
                    t.p(x, y, ARDOISE)
                else:
                    t.p(x, y, CREME)
                    t.p(x, y + 1, CREME_O)
        # Barre d'espace.
        t.rect(12, 8, 12, 1, CREME_O if k % 3 else O4)
        t.contour(ENCRE)
        # Pattes : la gauche frappe aux images paires, la droite aux impaires (elle descend sur le clavier).
        for cote, x in ((0, 7), (1, 21)):
            bas = 1 if (k % 2) == cote else 0
            t.motif(x, bas, [".cccccc.", "caabbbbc", "cbbbbbbc", ".cccccc."],
                    {"c": "@contour", "a": "@clair", "b": "@base"})
        images.append(t)
    ecrire("clavier-mini", images, slot="objet", ancre="pieds", point=(18, 5), duree=120,
           commentaire="Mini clavier devant Pilou assis (pattes qui tapent, touche enfoncée)")


# ---- Appareil photo : tenu devant les yeux (ancre « yeux »), l'objectif vers toi.

def appareil():
    t = T(22, 14)
    t.rect(3, 0, 6, 2, ARDOISE)          # viseur
    t.rect(15, 1, 3, 1, O3)              # déclencheur
    t.rect(0, 2, 22, 11, ARDOISE)
    t.rect(0, 2, 22, 2, ARDOISE_C)
    t.rect(1, 11, 20, 1, ENCRE)
    t.rect(2, 4, 4, 2, CREME_O)          # fenêtre du flash
    t.p(2, 4, BLANC)
    t.ell(13, 8, 5.2, 5, ENCRE)          # objectif
    t.ell(13, 8, 4, 3.8, B1)
    t.ell(13, 8, 2.6, 2.5, B2)
    t.p(11, 6, B4)
    t.p(12, 6, BLANC)
    t.p(11, 7, B4)
    t.contour(ENCRE)
    ecrire("appareil-photo", t, slot="main", ancre="yeux", point=(12, 4),
           commentaire="Appareil photo tenu devant les yeux")

    # Éclat du flash, au-dessus de la fenêtre du flash : rayons crème autour d'un cœur blanc.
    t = T(21, 17)
    cx, cy = 10, 8
    for a in range(8):
        an = a * math.pi / 4
        lg = 8 if a % 2 == 0 else 5
        for r in range(2, lg):
            t.p(round(cx + math.cos(an) * r), round(cy + math.sin(an) * r * 0.8), J4 if r < lg - 2 else CREME)
    t.ell(cx + 0.5, cy + 0.5, 3, 2.6, BLANC)
    ecrire("photo-flash", t, slot="effet", ancre="yeux", point=(18, 6), commentaire="Éclat du flash")


# ---- Polaroïd : sort de l'appareil, tombe en se balançant, se pose au sol ; l'image se développe
# (ardoise → bleu nuit → paysage bleu et soleil orange).

def photo(t, x, y, dev, penche=0):
    t.rect(x, y, 9, 11, CREME)
    t.rect(x, y + 9, 9, 2, CREME_O)
    ciel = (ARDOISE, B1, B3, B3)[dev]
    t.rect(x + 1, y + 1, 7, 7, ciel)
    if dev >= 2:
        t.rect(x + 5, y + 2, 2, 2, O3)
        t.poly([(x + 1, y + 8), (x + 3.5, y + 4.5), (x + 6, y + 8)], B1)
        t.poly([(x + 4, y + 8), (x + 6.5, y + 5.5), (x + 8, y + 8)], B2)
    if penche:
        # léger biais : on décale la moitié basse d'un pixel
        g = [r[:] for r in t.g]
        for j in range(y + 6, y + 11):
            for i in range(t.w):
                t.g[j][i] = g[j][i - penche] if 0 <= i - penche < t.w else None
    t.contour(ENCRE)


def polaroid():
    # Toile 12 × 25 posée sur l'ancre « main » (flanc droit) : la photo glisse le long de Pilou jusqu'au sol.
    etapes = [(0, 0, 0), (1, 6, 1), (2, 11, -1)]
    for k, (dev, y, pen) in enumerate(etapes):
        t = T(12, 25)
        photo(t, 1, y + 1, dev, pen)
        ecrire("polaroid-%d" % (k + 1), t, slot="effet", ancre="main", point=(2, 10),
               commentaire="Polaroïd qui tombe, étape %d" % (k + 1))
    # Posé au sol, à plat (vu de biais), développé.
    t = T(12, 25)
    t.poly([(1, 21), (9, 20), (11, 23), (2, 24)], CREME)
    t.poly([(2.5, 21), (8.5, 20.5), (9.5, 22.5), (3, 23)], B3)
    t.p(7, 21, O3)
    t.contour(ENCRE)
    ecrire("polaroid-4", t, slot="effet", ancre="main", point=(2, 10), commentaire="Polaroïd posé au sol")


# ---- Enveloppe : brandie au-dessus de la tête (ancre « tete »), elle sautille.

def enveloppe(ouverte):
    images = []
    for k in range(2):
        t = T(18, 16)
        y = 4 - k
        if ouverte:
            # la lettre dépasse, avec trois lignes d'écriture bleues
            t.rect(3, y - 3, 12, 6, BLANC)
            for j in range(3):
                t.rect(5, y - 2 + j * 2, 7 - j * 2, 1, B2)
        t.rect(1, y, 16, 10, CREME)
        t.rect(1, y + 8, 16, 2, CREME_O)
        # rabat en V
        for i in range(8):
            t.p(1 + i, y + i // 2 + (0 if ouverte else 1), CREME_O)
            t.p(16 - i, y + i // 2 + (0 if ouverte else 1), CREME_O)
        if not ouverte:
            # cachet rond orange (fermé = rond plein, signe de forme)
            t.ell(9, y + 5, 2.6, 2.4, O2)
            t.p(8, y + 4, O4)
        else:
            t.rect(7, y + 5, 4, 2, O3)
        t.contour(ENCRE)
        images.append(t)
    nom = "enveloppe-notif" if ouverte else "enveloppe-close"
    ecrire(nom, images, slot="main", ancre="tete", point=(7, 17), duree=320,
           commentaire="Enveloppe brandie (%s)" % ("ouverte, une lettre dépasse" if ouverte else "fermée, cachet rond"))


def tout():
    pouf()
    clavier()
    appareil()
    polaroid()
    enveloppe(True)
    enveloppe(False)
