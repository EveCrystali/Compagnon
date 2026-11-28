"""Rendu de Pilou à partir des sprites d'assets/ : la même règle que RenduPilou.cs (PC) et RenduPilou.java
(Android). Deux échelles : 1 (grille 48 × 56, le rendu de toujours) et 2 (rendu fin, grille 96 × 112 : corps
calculé à la finesse double, sprites d'assets/sprites2x ou, à défaut, sprites 1× agrandis par `agrandir`).
Sert aux planches de contrôle (planches.py, planches_hd.py) et aux empreintes de référence (reference.py)."""
import math
import os

import vie

ICI = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(ICI, "..", "..", "assets"))

W, H = 48, 56
C = 24
K = 1.25 * 48 / 26  # anciens pixels (grille 26 × 30 de 2025) → pixels de la grille 1×

ENCRE = "#1c2128"
JOUE = "#ffb37a"
JOUE_CLAIRE = "#ffc89a"
OMBRE_SOL = "#00000033"  # #rrggbbaa

ORDRE = ["dos", "cou", "visage", "yeux", "tete", "main", "compagnon", "effet", "objet"]


class Sprite:
    def __init__(self, id_):
        self.id, self.slot, self.ancre = id_, "objet", "aucun"
        self.dx = self.dy = 0
        self.couche, self.coiffe, self.duree = "devant", False, 0
        self.palette, self.images = {}, []
        self.natif = True   # faux : sprite 2× obtenu par agrandissement automatique

    @property
    def w(self):
        return max(len(r) for r in self.images[0]) if self.images else 0

    @property
    def h(self):
        return len(self.images[0]) if self.images else 0

    def image(self, t):
        if not self.images:
            return []
        n = len(self.images)
        return self.images[int(t // self.duree) % n if self.duree > 0 and n > 1 else 0]


def lire(texte, id_=""):
    s = Sprite(id_)
    image, dans = [], False
    for brut in texte.splitlines():
        ligne = brut.rstrip()
        if not dans:
            if not ligne or ligne.startswith("#"):
                continue
            cle, _, val = ligne.partition(":")
            cle, val = cle.strip(), val.strip()
            if cle == "images":
                dans = True
            elif cle == "id":
                s.id = val
            elif cle == "slot":
                s.slot = val
            elif cle == "ancre":
                s.ancre = val
            elif cle == "decalage":
                a, b = val.split()
                s.dx, s.dy = int(a), int(b)
            elif cle == "couche":
                s.couche = val
            elif cle == "coiffe":
                s.coiffe = val == "oui"
            elif cle == "duree":
                s.duree = int(val)
            elif cle == "palette":
                for paire in val.split():
                    l, _, c = paire.partition("=")
                    s.palette[l] = c
        else:
            if ligne == "---":
                s.images.append(image)
                image = []
            else:
                image.append(ligne)
    if image:
        s.images.append(image)
    return s


def _dossier(nom):
    b = {}
    d = os.path.join(ASSETS, nom)
    if not os.path.isdir(d):
        return b
    for f in sorted(os.listdir(d)):
        if f.endswith(".txt"):
            with open(os.path.join(d, f), encoding="utf-8") as fh:
                s = lire(fh.read(), f[:-4])
            b[s.id] = s
    return b


def banque():
    return _dossier("sprites")


def banque_fine(B):
    """Banque du rendu fin : le dessin natif d'assets/sprites2x s'il existe, sinon le sprite 1× agrandi."""
    natifs = _dossier("sprites2x")
    b = {}
    for i, s in B.items():
        b[i] = natifs[i] if i in natifs else agrandir(s)
    return b


# =====================================================================================================
# Agrandissement automatique d'un sprite 1× (sans flou ni nouvelle couleur)
# =====================================================================================================
# Règle « MMPX » (Morgan McGuire et Mara Gagiu, « MMPX Style-Preserving Pixel Art Magnification », 2021) :
# chaque pixel devient 2 × 2 pixels pris parmi lui-même et ses voisins. Par rapport à EPX / Scale2x, elle garde
# les traits sombres d'un pixel (cernes), traite les croisements et lisse aussi les pentes 2:1. Les couleurs
# sont comparées par leur lettre de palette ; le vide (« . » ou hors de l'image) compte comme une couleur.
# « Clarté » d'une couleur : (r + v + b + 1) × (256 − alpha) ; le vide vaut 256 ; les références à la teinte de
# Pilou prennent les valeurs du bleu, pour que le résultat ne dépende pas de la teinte portée.
TEINTE_REFERENCE = {"@contour": "#1f4f8a", "@ombre": "#4a8fdc", "@base": "#6cb6ff", "@clair": "#b4dbff"}


def clarte(code):
    code = TEINTE_REFERENCE.get(code, code)
    if not code or len(code) < 7 or code[0] != "#":
        return 256
    r, v, b = int(code[1:3], 16), int(code[3:5], 16), int(code[5:7], 16)
    a = int(code[7:9], 16) if len(code) >= 9 else 255
    return (r + v + b + 1) * (256 - a)


def agrandir_image(im, palette):
    """Image (liste de lignes de lettres) deux fois plus grande, mêmes lettres."""
    h = len(im)
    w = max((len(l) for l in im), default=0)
    lum = {".": 256}
    for k, c in palette.items():
        lum[k] = clarte(c)

    def src(x, y):
        if 0 <= y < h and 0 <= x < len(im[y]):
            return im[y][x]
        return "."

    def cl(ch):
        return lum.get(ch, 256)

    out = []
    for y in range(h):
        haut, bas = [], []
        for x in range(w):
            A, B, C_ = src(x - 1, y - 1), src(x, y - 1), src(x + 1, y - 1)
            D, E, F = src(x - 1, y), src(x, y), src(x + 1, y)
            G, H_, I = src(x - 1, y + 1), src(x, y + 1), src(x + 1, y + 1)
            J = K_ = L = M = E
            if not (A == E and B == E and C_ == E and D == E and F == E and G == E and H_ == E and I == E):
                P, S, Q, R = src(x, y - 2), src(x, y + 2), src(x - 2, y), src(x + 2, y)
                Bl, Dl, El, Fl, Hl = cl(B), cl(D), cl(E), cl(F), cl(H_)
                # Pentes 1:1 (coins arrondis, diagonales lissées).
                if D == B and D != H_ and D != F and (El >= Dl or E == A) and (E == A or E == C_ or E == G) \
                        and (El < Dl or A != D or E != P or E != Q):
                    J = D
                if B == F and B != D and B != H_ and (El >= Bl or E == C_) and (E == A or E == C_ or E == I) \
                        and (El < Bl or C_ != B or E != P or E != R):
                    K_ = B
                if H_ == D and H_ != F and H_ != B and (El >= Hl or E == G) and (E == A or E == G or E == I) \
                        and (El < Hl or G != H_ or E != S or E != Q):
                    L = H_
                if F == H_ and F != B and F != D and (El >= Fl or E == I) and (E == C_ or E == G or E == I) \
                        and (El < Fl or I != H_ or E != R or E != S):
                    M = F
                # Croisements.
                if E != F and E == C_ and E == I and E == D and E == Q and F == B and F == H_ and F != src(x + 3, y):
                    K_ = M = F
                if E != D and E == A and E == G and E == F and E == R and D == B and D == H_ and D != src(x - 3, y):
                    J = L = D
                if E != H_ and E == G and E == I and E == B and E == P and H_ == D and H_ == F and H_ != src(x, y + 3):
                    L = M = H_
                if E != B and E == A and E == C_ and E == H_ and E == S and B == D and B == F and B != src(x, y - 3):
                    J = K_ = B
                if Bl < El and E == G and E == H_ and E == I and E == S and E != A and E != D and E != C_ and E != F:
                    J = K_ = B
                if Hl < El and E == A and E == B and E == C_ and E == P and E != D and E != G and E != I and E != F:
                    L = M = H_
                if Fl < El and E == A and E == D and E == G and E == Q and E != B and E != C_ and E != I and E != H_:
                    K_ = M = F
                if Dl < El and E == C_ and E == F and E == I and E == R and E != B and E != A and E != G and E != H_:
                    J = L = D
                # Pentes 2:1.
                if H_ != B:
                    if H_ != A and H_ != E and H_ != C_:
                        if H_ == G and H_ == F and H_ == R and H_ != D and H_ != src(x + 2, y - 1):
                            L = M
                        if H_ == I and H_ == D and H_ == Q and H_ != F and H_ != src(x - 2, y - 1):
                            M = L
                    if B != I and B != G and B != E:
                        if B == A and B == F and B == R and B != D and B != src(x + 2, y + 1):
                            J = K_
                        if B == C_ and B == D and B == Q and B != F and B != src(x - 2, y + 1):
                            K_ = J
                if F != D:
                    if D != I and D != E and D != C_:
                        if D == A and D == H_ and D == S and D != B and D != src(x + 1, y + 2):
                            J = L
                        if D == G and D == B and D == P and D != H_ and D != src(x + 1, y - 2):
                            L = J
                    if F != E and F != A and F != G:
                        if F == C_ and F == H_ and F == S and F != B and F != src(x - 1, y + 2):
                            K_ = M
                        if F == I and F == B and F == P and F != H_ and F != src(x - 1, y - 2):
                            M = K_
            haut.append(J + K_)
            bas.append(L + M)
        out.append("".join(haut))
        out.append("".join(bas))
    return out


def agrandir(s):
    """Sprite deux fois plus fin, mêmes couleurs, mêmes ancrages (× 2)."""
    g = Sprite(s.id)
    g.slot, g.ancre, g.couche, g.coiffe, g.duree = s.slot, s.ancre, s.couche, s.coiffe, s.duree
    g.dx, g.dy = s.dx * 2, s.dy * 2
    g.palette = dict(s.palette)
    g.images = [agrandir_image(im, s.palette) for im in s.images]
    g.natif = False
    return g


def teintes():
    t = {}
    with open(os.path.join(ASSETS, "teintes.txt"), encoding="utf-8") as fh:
        for l in fh:
            l = l.strip()
            if l and not l.startswith("#"):
                nom, _, v = l.partition(":")
                t[nom.strip()] = v.split()
    return t


def tenues():
    t = {}
    with open(os.path.join(ASSETS, "tenues.txt"), encoding="utf-8") as fh:
        for l in fh:
            l = l.strip()
            if l and not l.startswith("#"):
                nom, _, v = l.partition(":")
                t[nom.strip()] = v.split()
    return t


class Pose:
    def __init__(self, **kw):
        # repos, concentre, attente, grimace, fete, soulage, dort, inquiet, caresse ; humeurs des campagnes :
        # joie, peur, triste, surpris, determine, fatigue, tendre, colere, malice, neutre.
        self.expr = "repos"
        self.t = 0
        self.couleur = "bleu"
        self.accessoire = ""
        self.tenue = ""        # tenue d'activité, ou tenue de voyage « voyage-<mode> » (voir voyager)
        self.objets = []
        self.cligne = self.clin = self.marche = self.course = self.baille = self.etourdi = False
        self.fatigue = self.salue = False
        self.boude = self.dos = False   # il boude (moue, sourcils froncés au repos) ; dos tourné (pas de visage)
        self.regard = self.regard_y = 0
        self.saut = self.chute = self.assis = self.suspendu = self.tremble = 0.0
        self.stade = 2         # 1 Gouttelette, 2 Pilou, 3 Pilou Nimbus, 4 Pilou Astral
        self.evolution = 0.0    # 0..1 : animation d'évolution vers ce stade (0 ou 1 : aucune)
        self.reaction = ""      # "sueur" (gouttes) ; "danse" : le PC balance Pilou, les notes viennent de la tenue
        # Vie du personnage (vie.py) : étirement du corps (−1 écrasé … 1 étiré), retard de l'antenne (−1 … 1, positif :
        # pointe plus haute), ms depuis l'atterrissage (−1 : aucun), lumière du moment (« matin », « soir », « nuit »
        # ou "") ; vie : animations complètes (ombre tramée en l'air, bouffées de poussière).
        self.etire = self.antenne = 0.0
        self.atterri = -1.0
        self.lumiere = ""
        self.vie = False
        self.__dict__.update(kw)


SPARK = {"concentre": "etincelle-roue", "attente": "etincelle-roue", "grimace": "etincelle-x", "dort": "etincelle-dort",
         "inquiet": "etincelle-alerte", "caresse": "etincelle-coeur", "surpris": "etincelle-alerte", "fatigue": "etincelle-dort",
         "tendre": "etincelle-coeur"}
OEIL = {"concentre": "concentre", "attente": "haut", "grimace": "grimace", "fete": "heureux", "caresse": "heureux",
        "soulage": "content", "dort": "dort", "inquiet": "inquiet",
        "joie": "heureux", "peur": "peur", "triste": "triste", "surpris": "surpris", "determine": "determine",
        "fatigue": "fatigue", "tendre": "tendre", "colere": "colere", "malice": "malice"}
JOUES = ("fete", "caresse", "joie", "tendre")
CLIGNE = ("repos", "inquiet", "attente", "neutre")
CHAUDES = {"ambre", "braise", "comete", "corail-orange", "sable", "mandarine", "miel", "peche", "caramel", "potiron", "cuivre"}

# Tenues de voyage (campagnes, docs/CAMPAGNES.md) : Pilou est « occupé » pendant une attente.
VOYAGES = ("marche", "course", "bateau", "grimpe", "nage", "nuit", "cache", "attend")

# Échelle du corps par stade (largeur, hauteur) : Gouttelette, Pilou, Nimbus, Astral.
STADE_X = {1: 0.72, 2: 1.0, 3: 1.1, 4: 0.9}
STADE_Y = {1: 0.74, 2: 1.0, 3: 1.0, 4: 1.2}
SILHOUETTE, SILHOUETTE_BORD = "#e8f4ff", "#6cb6ff"
ECLAT = ["#ffd8b0", "#fff6cc", "#b4dbff"]
GOUTTE, GOUTTE_CLAIRE, BLANC = "#1f4f8a", "#b4dbff", "#ffffff"

CROIX = ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))
# Dessins fins (2×) des petites formes que le rendu pose lui-même. « # » : couleur demandée.
ETOILE_FINE = ["...#...", "...#...", "..###..", "#######", "..###..", "...#...", "...#..."]          # centre (3, 3)
JOUE_FINE = [".####.", "######", "#o####", ".####."]                                                   # o : reflet
GOUTTE_NIMBUS_FINE = ["..c..", "..c..", ".clc.", ".clc.", "clbbc", "cbbbc", ".ccc."]                   # sommet (2, 0)
SUEUR_FINE = ["..gg..", "..gg..", ".gccg.", ".gccg.", "gcwccg", "gcwccg", "gccccg", ".gggg."]          # sommet (2, 0)


def teinte_de(p, T):
    if p.expr == "inquiet":
        return T["bleu"] if p.couleur in CHAUDES else T["orange"]
    return T.get(p.couleur, T["bleu"])


def copie(p, **kw):
    d = dict(p.__dict__)
    d.update(kw)
    return Pose(**d)


def voyager(p):
    """Tenue de voyage « voyage-<mode> » : la pose que le mode impose (il marche sur place, rame, grimpe, dort…).
    Ce que l'appelant a déjà demandé (regard, humeur) est gardé quand le mode ne dit rien."""
    if not p.tenue.startswith("voyage-"):
        return p
    mode, t = p.tenue[7:], p.t
    if mode not in VOYAGES:
        return p
    q = copie(p)
    if mode == "marche":
        q.marche = True
        q.regard = p.regard if p.regard != 0 else 1
    elif mode == "course":
        q.marche = q.course = True
        q.regard = p.regard if p.regard != 0 else 1
    elif mode == "bateau":
        q.assis = 1.0
        q.saut = 0.5 + 0.5 * math.sin(t / 520)          # tangage
        q.regard = p.regard if p.regard != 0 else 1
    elif mode == "grimpe":
        q.saut = 2.0 + 1.2 * abs(math.sin(t / 420))     # il se hisse, bras après bras
        q.regard_y = -1
    elif mode == "nage":
        q.assis = 1.0
        q.saut = 0.4 + 0.4 * math.sin(t / 450)
    elif mode == "nuit":
        q.expr = "dort"
    elif mode == "cache":
        q.assis = 1.0
        q.chute = 0.25
        q.regard = (-1, 0, 1, 0)[int(t // 900) % 4]     # il guette d'un côté puis de l'autre
    elif mode == "attend":
        q.assis = 1.0
        leve = int(t // 1400) % 3 == 2                    # il regarde sa montre, puis relève les yeux
        q.regard_y = 0 if leve else 1
        q.regard = p.regard if leve else -1
    return q


_FINES = {}


def rendre(p, B, T, TEN, e=1, B2=None):
    """Pilou, avec l'animation d'évolution s'il y en a une en cours (stade = stade d'arrivée).
    e : échelle (1 : grille 48 × 56 ; 2 : rendu fin 96 × 112, sprites de B2 ou de banque_fine(B))."""
    if e != 1:
        if B2 is None:
            B2 = _FINES.get(id(B))
            if B2 is None:
                B2 = _FINES[id(B)] = banque_fine(B)
        B = B2
    p = voyager(p)
    ev = p.evolution
    if 0 < ev < 1 and p.stade > 1:
        if ev < 0.85:
            # Silhouette claire qui alterne ancien / nouveau stade, de plus en plus vite.
            k = int((ev / 0.85) ** 2 * 12) % 2
            q = copie(p, stade=p.stade - 1 if k == 0 else p.stade, evolution=0, expr="repos")
            return silhouette(rendre_stade(q, B, T, TEN, e), e)
        g = rendre_stade(copie(p, evolution=0), B, T, TEN, e)
        eclats(g, (ev - 0.85) / 0.15, e)
        return g
    return rendre_stade(p, B, T, TEN, e)


def silhouette(g, e=1):
    w, h = W * e, H * e
    out = [[None] * w for _ in range(h)]

    def vide(x, y):
        return not (0 <= x < w and 0 <= y < h) or g[y][x] in (None, OMBRE_SOL)

    for y in range(h):
        for x in range(w):
            c = g[y][x]
            if c is None or c == OMBRE_SOL:
                out[y][x] = c
                continue
            bord = any(vide(x + a * n, y + b * n) for n in range(1, e + 1) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            out[y][x] = SILHOUETTE_BORD if bord else SILHOUETTE
    return out


def _etoile(g, x, y, c, e):
    """Petite étoile centrée en (x, y) : croix de 3 pixels en 1×, étoile à quatre branches de 7 pixels en 2×."""
    w, h = W * e, H * e
    if e == 1:
        for a2, b2 in CROIX:
            if 0 <= x + a2 < w and 0 <= y + b2 < h:
                g[y + b2][x + a2] = c
        return
    for j, ligne in enumerate(ETOILE_FINE):
        for i, ch in enumerate(ligne):
            if ch == "#" and 0 <= x + i - 3 < w and 0 <= y + j - 3 < h:
                g[y + j - 3][x + i - 3] = c


def eclats(g, k, e=1):
    """Gerbe d'étincelles qui part du centre de Pilou (k de 0 à 1)."""
    r = (4 + k * 20) * e
    for i in range(12):
        a = i * math.pi / 6
        x, y = int(round(C * e + math.cos(a) * r)), int(round(36 * e + math.sin(a) * r * 0.85))
        _etoile(g, x, y, ECLAT[i % 3], e)


def rendre_stade(p, B, T, TEN, e=1):
    """Renvoie une grille H·e × W·e de couleurs (#rrggbb, #rrggbbaa ou None)."""
    w, h = W * e, H * e
    c0 = C * e
    g = [[None] * w for _ in range(h)]

    def px(x, y, c):
        if 0 <= x < w and 0 <= y < h and c is not None:
            g[y][x] = c

    st = p.stade if p.stade in STADE_X else 2
    te = teinte_de(p, T)
    if p.lumiere and p.expr != "inquiet":   # l'alerte garde sa couleur franche
        te = [vie.eclairer(c, p.lumiere) for c in te]
    ref = {"@contour": te[0], "@ombre": te[1], "@base": te[2], "@clair": te[3]}
    t = p.t
    periode = 4200 if p.expr == "dort" else 1600 if p.expr in ("concentre", "attente") else 2600
    b = math.sin(2 * math.pi * t / periode)
    rx, ry = 6.8 - 0.2 * b, 5.6 + 0.3 * b
    if p.expr == "caresse":
        rx, ry = rx + 0.5, ry - 0.5
    if p.expr == "dort":
        rx, ry = rx + 0.6, ry - 0.9
    rx += 1.2 * p.chute + 0.7 * p.assis - 0.8 * p.suspendu
    ry -= 1.4 * p.chute + 0.8 * p.assis - 1.1 * p.suspendu
    rx -= 0.9 * p.etire
    ry += 1.1 * p.etire
    rx, ry = rx * STADE_X[st], ry * STADE_Y[st]
    cadence = 70 if p.course else 160
    marche = abs(math.sin(t / cadence)) * (1.3 if p.course else 0.8) if p.marche else 0
    sol = (21.6 - p.saut - marche + p.assis) * K
    cx = C + (p.tremble + p.suspendu * math.sin(t / 260) * 1.2) * K
    rx, ry = rx * K, ry * K
    # Rendu fin : les mêmes grandeurs, deux fois plus grandes ; tout ce qui suit s'arrondit au pixel fin.
    if e != 1:
        sol, cx, rx, ry = sol * e, c0 + (cx - C) * e, rx * e, ry * e
    cy = sol - ry
    dx = int(round(cx - c0))

    # Ce que Pilou porte : cape du stade 4, accessoire, tenue d'activité, objets ; inconnus ignorés.
    ids = []
    if st == 4:
        ids.append("astral-cape")
    if p.accessoire:
        ids.append("acc-" + p.accessoire)
    ids += TEN.get(p.tenue, []) if p.tenue else []
    ids += p.objets
    portes = [B[i] for i in ids if i in B and not (p.dos and B[i].slot in ("visage", "yeux"))]
    coiffe = any(s.coiffe for s in portes)

    pied = int(round(sol))
    sommet = int(math.ceil(cy - ry))
    ey = int(math.floor(cy - 6.6 * STADE_Y[st] * e)) + p.regard_y * 2 * e
    dxf = dx + p.regard * 2 * e
    vitesse = 90 if (p.salue or p.expr == "fete") else 300 if p.expr == "concentre" else 650
    balance = 0 if p.expr == "dort" else max(-e, min(e, int(round(math.sin(t / vitesse) * 0.9 * e)) +
                                                     ((-e if p.regard > 0 else e if p.regard < 0 else 0) if p.marche else 0)))
    haut_antenne = max(2 * e, (3 if st == 1 else 6) * e + int(round(p.antenne * 2 * e)))
    ancres = {
        "tete": (c0 + dx, sommet), "yeux": (c0 + dxf, ey), "bouche": (c0 + dxf, ey + 9 * e),
        "cou": (c0 + dx, int(round(cy + ry * 0.45))), "corps": (c0 + dx, int(round(cy))),
        "main": (int(round(cx + rx)) - e, int(round(cy + ry * 0.15))), "main-g": (int(round(cx - rx)), int(round(cy + ry * 0.15))),
        "pieds": (c0 + dx, pied), "cote": (int(round(cx + rx * 0.45)), pied + 2 * e),
        "antenne": (c0 + dx + 2 * balance, sommet - haut_antenne),
        "aucun": (0, 0),
    }

    def poser(s, miroir=False, x=None, y=None, im=None):
        if x is None:
            ax, ay = ancres.get(s.ancre, (0, 0))
            x, y = ax + s.dx, ay + s.dy
        im = im if im is not None else s.image(t)
        for j, ligne in enumerate(im):
            for i, ch in enumerate(ligne):
                if ch == ".":
                    continue
                c = s.palette.get(ch)
                c = ref.get(c, c)
                px(x + (len(ligne) - 1 - i if miroir else i), y + j, c)

    def motif(x, y, lignes, pal):
        for j, ligne in enumerate(lignes):
            for i, ch in enumerate(ligne):
                if ch in pal:
                    px(x + i, y + j, pal[ch])

    def ordre(s):
        return ORDRE.index(s.slot) if s.slot in ORDRE else 9

    def etoile(x, y, c):
        if e == 1:
            for a2, b2 in CROIX:
                px(x + a2, y + b2, c)
        else:
            motif(x - 3, y - 3, ETOILE_FINE, {"#": c})

    # Astral : couronne d'étincelles en orbite (la moitié arrière passe derrière le corps).
    orbite = []
    if st == 4:
        for i in range(5):
            a = t / 700 + i * 2 * math.pi / 5
            orbite.append((int(round(cx + math.cos(a) * (rx + 4 * e))), int(round(sommet + 4 * e + math.sin(a) * 3.5 * e)),
                           math.sin(a) > 0, ECLAT[i % 3]))

    # Couche arrière (cape, aura…).
    for s in sorted([s for s in portes if s.couche == "derriere"], key=ordre):
        poser(s)
    for x, y, devant, c in orbite:
        if not devant:
            etoile(x, y, c)

    # Ombre au sol.
    if p.suspendu < 0.1:
        demi = int(max(6, 15 * STADE_X[st] - p.saut * 2.8) * e)
        # Vie : en l'air, l'ombre s'éclaircit en trame (d'abord le bas de l'ombre, puis toute l'ombre).
        trame = (2 if p.saut >= 2.4 else 1 if p.saut >= 1.0 else 0) if p.vie else 0

        def ombre(x, j, bas):
            return trame == 0 or (trame == 1 and not bas) or (x + j) % 2 == 0

        if e == 1:
            for x in range(C - demi, C + demi):
                if g[52][x] is None and ombre(x, 0, False):
                    g[52][x] = OMBRE_SOL
                if abs(x - C + 0.5) < demi - 3 and g[53][x] is None and ombre(x, 1, True):
                    g[53][x] = OMBRE_SOL
        else:
            # Quatre lignes fines, bouts arrondis.
            for j, retrait in enumerate((2, 0, 3, 7)):
                for x in range(c0 - demi + retrait, c0 + demi - retrait):
                    if 0 <= x < w and g[104 + j][x] is None and ombre(x, j, j >= 2):
                        g[104 + j][x] = OMBRE_SOL

    # Corps : ombrage tramé, reflet ; Nimbus : volutes et bras ; puis cerne.
    m = [[None] * w for _ in range(h)]
    bosses = []
    if st == 3:
        for deg in (-160, -125, -90, -55, -20, 170, 10):
            a = math.radians(deg)
            bosses.append((cx + math.cos(a) * rx * 0.84, cy + math.sin(a) * ry * 0.84, ry * (0.3 if deg < 0 else 0.24)))
    for y in range(h):
        for x in range(w):
            u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            r2 = u * u + v * v
            dans = r2 <= 1
            if not dans and bosses:
                dans = any((x + 0.5 - bx) ** 2 + (y + 0.5 - by) ** 2 <= br * br for bx, by, br in bosses)
                r2 = min(r2, 0.9)
            if not dans:
                continue
            if e == 1:
                damier = (x + y) % 2 == 0
                reflet = u < -0.25 and v < -0.3
                if reflet and (r2 > 0.45 or (r2 > 0.34 and damier)):
                    m[y][x] = te[3]
                elif v > 0.62 or (v > 0.46 and damier):
                    m[y][x] = te[1]
                else:
                    m[y][x] = te[2]
            else:
                m[y][x] = te[_ton_fin(x, y, u, v, r2)]
    if st == 3:
        for sgn in (-1, 1):
            bx, by = cx + sgn * (rx + 1.2 * e), cy + ry * 0.28 + math.sin(t / 300 + sgn) * 0.8 * e
            for y in range(h):
                for x in range(w):
                    if ((x + 0.5 - bx) / (3.2 * e)) ** 2 + ((y + 0.5 - by) / (2.4 * e)) ** 2 <= 1:
                        m[y][x] = te[1]
    if p.assis <= 0.5:
        pas = int(t // cadence) % 2 if p.marche else -1
        largeur = (5 if st == 1 else 6) * e
        pieds = ((0, C - 8), (1, C + 3)) if st == 1 else ((0, C - 10), (1, C + 4))
        for cote, x0 in pieds:
            x0 *= e
            haut = pied - (2 * e if pas == cote else 0)
            if e == 1:
                for x in range(x0, x0 + largeur):
                    for y in (haut, haut + 1):
                        if 0 <= x + dx < w and 0 <= y < h and (y == haut or x0 < x < x0 + largeur - 1):
                            m[y][x + dx] = te[1]
            else:
                # Pied fin : quatre lignes, semelle arrondie.
                for j, retrait in enumerate((0, 0, 1, 3)):
                    for x in range(x0 + retrait, x0 + largeur - retrait):
                        if 0 <= x + dx < w and 0 <= haut + j < h:
                            m[haut + j][x + dx] = te[1]
    if e == 1:
        for y in range(h):
            for x in range(w):
                if m[y][x] is None:
                    continue
                bord = x in (0, w - 1) or y in (0, h - 1) or m[y][x - 1] is None or m[y][x + 1] is None \
                    or m[y - 1][x] is None or m[y + 1][x] is None
                g[y][x] = te[0] if bord else m[y][x]
    else:
        # Cerne fin : deux pixels d'épaisseur, diagonales comprises (tout ce qui est à moins de √5 du vide).
        def vide(x, y):
            return not (0 <= x < w and 0 <= y < h) or m[y][x] is None

        bord1 = [[m[y][x] is not None and (vide(x - 1, y) or vide(x + 1, y) or vide(x, y - 1) or vide(x, y + 1))
                  for x in range(w)] for y in range(h)]
        for y in range(h):
            for x in range(w):
                if m[y][x] is None:
                    continue
                bord = False
                for b2 in (-1, 0, 1):
                    for a2 in (-1, 0, 1):
                        if vide(x + a2, y + b2) or bord1[y + b2][x + a2]:
                            bord = True
                g[y][x] = te[0] if bord else m[y][x]
    if st == 3:
        # Volutes : deux arcs clairs dans le nuage.
        for sgn in (-1, 1):
            for k in range(7 * e):
                pas_k = k / e
                a = math.radians(200 + pas_k * 22) if sgn < 0 else math.radians(-20 - pas_k * 22)
                x, y = int(round(cx + sgn * rx * 0.55 + math.cos(a) * 3 * e)), int(round(cy - ry * 0.55 + math.sin(a) * 2 * e))
                px(x, y, te[3])
                if e == 2:
                    px(x, y + 1, te[3])

    # Visage (aucun s'il tourne le dos).
    moue = p.boude and p.expr == "repos"
    nom = "spirale" if p.etourdi else OEIL.get(p.expr, "boude" if moue else "fatigue" if p.fatigue else "ouvert")
    if p.baille:
        nom = "dort"
    if st == 4 and nom == "ouvert":
        nom = "serein"
    peut = p.expr in CLIGNE and not p.etourdi
    og = "cligne" if peut and p.cligne else nom
    od = "cligne" if peut and (p.cligne or p.clin) else nom
    if p.dos:
        pass  # vu de dos : ni yeux, ni bouche, ni joues
    elif st == 1 and og == "ouvert" and "oeil-ouvert-g" in B:
        poser(B["oeil-ouvert-g"], False, (C - 10) * e + dxf, ey - e)
        if od == "ouvert":
            poser(B["oeil-ouvert-g"], True, (C + 2) * e + dxf, ey - e)
        elif "oeil-" + od in B:
            poser(B["oeil-" + od], True, (C + 3) * e + dxf, ey)
    else:
        ecart = 1 if st == 1 else 0
        if "oeil-" + og in B:
            s = B["oeil-" + og]
            poser(s, False, (C - 10 + ecart) * e + dxf + s.dx, ey + s.dy)
        if "oeil-" + od + "-d" in B:
            # Œil droit dessiné à part (regard dissymétrique : malice) : posé tel quel, sans miroir.
            s = B["oeil-" + od + "-d"]
            poser(s, False, (C + 4 - ecart) * e + dxf + s.dx, ey + s.dy)
        elif "oeil-" + od in B:
            s = B["oeil-" + od]
            poser(s, True, (C + 10 - ecart) * e + dxf - s.dx - s.w, ey + s.dy)
    bo = None if p.dos else B.get("bouche-baille" if p.baille else "bouche-boude" if moue else "bouche-" + p.expr) or B.get("bouche-repos")
    if bo:
        poser(bo, False, c0 - bo.w // 2 + dxf, ey + 9 * e + bo.dy)
    if p.expr in JOUES and not p.dos:
        joue = int(round(rx)) - e
        if e == 1:
            for x0 in (C - joue + dxf, C + joue - 3 + dxf):
                for i in range(3):
                    for j in range(2):
                        px(x0 + i, ey + 7 + j, JOUE)
        else:
            motif(c0 - joue + dxf, ey + 14, JOUE_FINE, {"#": JOUE, "o": JOUE_CLAIRE})
            motif(c0 + joue - 6 + dxf, ey + 14, JOUE_FINE, {"#": JOUE, "o": JOUE_CLAIRE})
    # Marque de l'humeur (larme, goutte, éclair de colère…) : sprite « marque-<humeur> », posé sur l'ancre des yeux.
    if not p.dos and "marque-" + p.expr in B:
        poser(B["marque-" + p.expr])

    # Antenne(s) et étincelle(s), sauf sous un chapeau.
    if not coiffe:
        sp = SPARK.get(p.expr)
        if sp is None:
            grand = (t // 120) % 2 == 0 if p.expr == "fete" else (t // 900) % 2 == 0
            sp = "etincelle-grand" if grand else "etincelle-petit"
        im = None
        if sp == "etincelle-roue" and sp in B:
            s = B[sp]
            im = s.images[int(t // (90 if p.expr == "concentre" else 260)) % len(s.images)]
        tiges = [(c0 - e + dx, 0)] if st != 3 else [(c0 - 7 * e + dx, -1), (c0 + 5 * e + dx, 1)]
        base = sommet + (3 * e if st == 3 else 0)
        for x0, pente in tiges:
            for k in range(1, haut_antenne + 1):
                if e == 1:
                    dec = (balance if k > haut_antenne // 2 else 0) + pente * (k // 3)
                    px(x0 + dec, base - k, te[0])
                    px(x0 + 1 + dec, base - k, te[0])
                else:
                    # Tige fine : elle se courbe peu à peu vers la pointe ; un filet d'ombre lui donne du volume.
                    courbe = abs(balance) * max(0, 2 * k - haut_antenne + 2) // (haut_antenne + 2)
                    dec = (courbe if balance > 0 else -courbe) + pente * (k // 3)
                    for i in range(4):
                        px(x0 + i + dec, base - k, te[1] if i == 1 else te[0])
            if sp in B:
                s = B[sp]
                tip = x0 + e + balance + pente * (haut_antenne // 3)
                poser(s, x=tip + s.dx, y=base - haut_antenne + s.dy, im=im)

    # Nimbus : petite traînée de gouttes qui tombent.
    if st == 3:
        for i, fx in enumerate((-0.6, 0.55, -0.1)):
            ph = (t / 900 + i / 3) % 1
            x, y = int(round(cx + rx * fx)), int(round(cy + ry * 0.7 + ph * 9 * e))
            if y < pied:
                continue
            if e == 1:
                px(x, y, te[3])
                px(x, y + 1, te[2])
                px(x - 1, y + 1, te[0])
                px(x + 1, y + 1, te[0])
                px(x, y + 2, te[0])
            else:
                motif(x - 2, y, GOUTTE_NIMBUS_FINE, {"c": te[0], "l": te[3], "b": te[2]})

    # Couche avant, dans l'ordre des emplacements.
    for s in sorted([s for s in portes if s.couche != "derriere"], key=ordre):
        poser(s)
    for x, y, devant, c in orbite:
        if devant:
            etoile(x, y, c)

    # Réaction « sueur » : deux gouttes qui glissent sur les tempes.
    if p.reaction == "sueur":
        for i, sgn in enumerate((-1, 1)):
            ph = (t / 1100 + i * 0.5) % 1
            x, y = int(round(cx + sgn * (rx - 2 * e))), int(round(ey - 2 * e + ph * 8 * e))
            if e == 1:
                px(x, y - 1, GOUTTE)
                for a2, b2 in ((-1, 0), (1, 0), (-1, 1), (1, 1), (0, 2)):
                    px(x + a2, y + b2, GOUTTE)
                px(x, y, GOUTTE_CLAIRE)
                px(x, y + 1, BLANC)
            else:
                motif(x - 2, y - 2, SUEUR_FINE, {"g": GOUTTE, "c": GOUTTE_CLAIRE, "w": BLANC})

    # Vie : bouffées de poussière au ras du sol (le pied arrière en marchant, les deux côtés à l'atterrissage), en
    # blocs d'un pixel de la grille 1× ; posées seulement sur le vide ou l'ombre, jamais sur Pilou.
    if p.vie and p.suspendu < 0.1 and p.assis <= 0.5:
        pieds_x = ((C - 8) * e, (C + 3) * e) if st == 1 else ((C - 10) * e, (C + 4) * e)
        largeur = (5 if st == 1 else 6) * e
        bouffees = []
        if p.marche and not p.course:
            sens = 1 if p.regard >= 0 else -1
            im_b = vie.bouffee(int(math.floor(t)), cadence, sens)
            if im_b >= 0:
                talon = pieds_x[0] + dx - e if sens > 0 else pieds_x[1] + dx + largeur
                bouffees.append((talon, -sens, vie.BOUFFEES[im_b]))
        im_a = vie.bouffee_atterrissage(int(math.floor(p.atterri))) if p.atterri >= 0 else -1
        if im_a >= 0:
            bouffees.append((pieds_x[0] + dx - e, -1, vie.BOUFFEES_ATTERRISSAGE[im_a]))
            bouffees.append((pieds_x[1] + dx + largeur, 1, vie.BOUFFEES_ATTERRISSAGE[im_a]))
        for x0, sg, points in bouffees:
            for recul, haut, plein in points:
                c = vie.POUSSIERE if plein else vie.POUSSIERE_LEGERE
                for j in range(e):
                    for i in range(e):
                        x, y = x0 + sg * recul * e + i, pied + e + haut * e + j
                        if 0 <= x < w and 0 <= y < h and g[y][x] in (None, OMBRE_SOL):
                            g[y][x] = c
    return g


def _ton_fin(x, y, u, v, r2):
    """Ton du corps au rendu fin (indice dans la teinte : 1 ombre, 2 base, 3 clair). Trame à trois paliers
    (un quart, un demi, trois quarts) au lieu du seul damier, ombre qui épouse le volume, reflet en croissant."""
    # Reflet : croissant en haut à gauche, entre le bord et un cercle intérieur, borné par un disque posé sur le bord.
    d2 = (u + 0.62) * (u + 0.62) + (v + 0.62) * (v + 0.62)
    if r2 > 0.47 and d2 < 0.2025:
        return 3
    if r2 > 0.40 and d2 < 0.16 and (x + y) % 2 == 0:
        return 3
    # Ombre : la bande du bas remonte un peu sur les côtés.
    s = v + 0.16 * u * u
    if s > 0.66:
        return 1
    if s > 0.58:
        return 2 if (x % 2 == 0 and y % 2 == 1) else 1
    if s > 0.50:
        return 1 if (x + y) % 2 == 0 else 2
    if s > 0.42:
        return 1 if (x % 2 == 0 and y % 2 == 0) else 2
    return 2
