"""Rendu de Pilou en 48 × 56 à partir des sprites d'assets/ : la même règle que RenduPilou.cs (PC) et
RenduPilou.java (Android). Sert aux planches de contrôle (planches.py)."""
import math
import os

ICI = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(ICI, "..", "..", "assets"))

W, H = 48, 56
C = 24
K = 1.25 * 48 / 26  # anciens pixels (grille 26 × 30 de 2025) → pixels de la grille actuelle

ENCRE = "#1c2128"
JOUE = "#ffb37a"
OMBRE_SOL = "#00000033"  # #rrggbbaa

ORDRE = ["dos", "cou", "visage", "yeux", "tete", "main", "compagnon", "effet", "objet"]


class Sprite:
    def __init__(self, id_):
        self.id, self.slot, self.ancre = id_, "objet", "aucun"
        self.dx = self.dy = 0
        self.couche, self.coiffe, self.duree = "devant", False, 0
        self.palette, self.images = {}, []

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


def banque():
    b = {}
    d = os.path.join(ASSETS, "sprites")
    for f in sorted(os.listdir(d)):
        if f.endswith(".txt"):
            with open(os.path.join(d, f), encoding="utf-8") as fh:
                s = lire(fh.read(), f[:-4])
            b[s.id] = s
    return b


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
        self.expr = "repos"
        self.t = 0
        self.couleur = "bleu"
        self.accessoire = ""
        self.tenue = ""
        self.objets = []
        self.cligne = self.clin = self.marche = self.course = self.baille = self.etourdi = False
        self.fatigue = self.salue = False
        self.regard = self.regard_y = 0
        self.saut = self.chute = self.assis = self.suspendu = self.tremble = 0.0
        self.stade = 2         # 1 Gouttelette, 2 Pilou, 3 Pilou Nimbus, 4 Pilou Astral
        self.evolution = 0.0    # 0..1 : animation d'évolution vers ce stade (0 ou 1 : aucune)
        self.reaction = ""      # "sueur" (gouttes) ; "danse" : le PC balance Pilou, les notes viennent de la tenue
        self.__dict__.update(kw)


SPARK = {"concentre": "etincelle-roue", "attente": "etincelle-roue", "grimace": "etincelle-x", "dort": "etincelle-dort",
         "inquiet": "etincelle-alerte", "caresse": "etincelle-coeur"}
OEIL = {"concentre": "concentre", "attente": "haut", "grimace": "grimace", "fete": "heureux", "caresse": "heureux",
        "soulage": "content", "dort": "dort", "inquiet": "inquiet"}
CHAUDES = {"ambre", "braise", "comete", "corail-orange", "sable"}

# Échelle du corps par stade (largeur, hauteur) : Gouttelette, Pilou, Nimbus, Astral.
STADE_X = {1: 0.72, 2: 1.0, 3: 1.1, 4: 0.9}
STADE_Y = {1: 0.74, 2: 1.0, 3: 1.0, 4: 1.2}
SILHOUETTE, SILHOUETTE_BORD = "#e8f4ff", "#6cb6ff"
ECLAT = ["#ffd8b0", "#fff6cc", "#b4dbff"]


def teinte_de(p, T):
    if p.expr == "inquiet":
        return T["bleu"] if p.couleur in CHAUDES else T["orange"]
    return T.get(p.couleur, T["bleu"])


def copie(p, **kw):
    d = dict(p.__dict__)
    d.update(kw)
    return Pose(**d)


def rendre(p, B, T, TEN):
    """Pilou, avec l'animation d'évolution s'il y en a une en cours (stade = stade d'arrivée)."""
    e = p.evolution
    if 0 < e < 1 and p.stade > 1:
        if e < 0.85:
            # Silhouette claire qui alterne ancien / nouveau stade, de plus en plus vite.
            k = int((e / 0.85) ** 2 * 12) % 2
            q = copie(p, stade=p.stade - 1 if k == 0 else p.stade, evolution=0, expr="repos")
            return silhouette(rendre_stade(q, B, T, TEN))
        g = rendre_stade(copie(p, evolution=0), B, T, TEN)
        eclats(g, (e - 0.85) / 0.15)
        return g
    return rendre_stade(p, B, T, TEN)


def silhouette(g):
    out = [[None] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            c = g[y][x]
            if c is None or c == OMBRE_SOL:
                out[y][x] = c
                continue
            bord = any(not (0 <= x + a < W and 0 <= y + b < H) or g[y + b][x + a] in (None, OMBRE_SOL)
                       for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            out[y][x] = SILHOUETTE_BORD if bord else SILHOUETTE
    return out


def eclats(g, k):
    """Gerbe d'étincelles qui part du centre de Pilou (k de 0 à 1)."""
    r = 4 + k * 20
    for i in range(12):
        a = i * math.pi / 6
        x, y = int(round(C + math.cos(a) * r)), int(round(36 + math.sin(a) * r * 0.85))
        for a2, b2 in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
            if 0 <= x + a2 < W and 0 <= y + b2 < H:
                g[y + b2][x + a2] = ECLAT[i % 3]


def rendre_stade(p, B, T, TEN):
    """Renvoie une grille H × W de couleurs (#rrggbb, #rrggbbaa ou None)."""
    g = [[None] * W for _ in range(H)]

    def px(x, y, c):
        if 0 <= x < W and 0 <= y < H and c is not None:
            g[y][x] = c

    st = p.stade if p.stade in STADE_X else 2
    te = teinte_de(p, T)
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
    rx, ry = rx * STADE_X[st], ry * STADE_Y[st]
    cadence = 70 if p.course else 160
    marche = abs(math.sin(t / cadence)) * (1.3 if p.course else 0.8) if p.marche else 0
    sol = (21.6 - p.saut - marche + p.assis) * K
    cx = C + (p.tremble + p.suspendu * math.sin(t / 260) * 1.2) * K
    rx, ry = rx * K, ry * K
    cy = sol - ry
    dx = int(round(cx - C))

    # Ce que Pilou porte : cape du stade 4, accessoire, tenue d'activité, objets ; inconnus ignorés.
    ids = []
    if st == 4:
        ids.append("astral-cape")
    if p.accessoire:
        ids.append("acc-" + p.accessoire)
    ids += TEN.get(p.tenue, []) if p.tenue else []
    ids += p.objets
    portes = [B[i] for i in ids if i in B]
    coiffe = any(s.coiffe for s in portes)

    pied = int(round(sol))
    sommet = int(math.ceil(cy - ry))
    ey = int(math.floor(cy - 6.6 * STADE_Y[st])) + p.regard_y * 2
    dxf = dx + p.regard * 2
    vitesse = 90 if (p.salue or p.expr == "fete") else 300 if p.expr == "concentre" else 650
    balance = 0 if p.expr == "dort" else max(-1, min(1, int(round(math.sin(t / vitesse) * 0.9)) +
                                                     ((-1 if p.regard > 0 else 1 if p.regard < 0 else 0) if p.marche else 0)))
    haut_antenne = 3 if st == 1 else 6
    ancres = {
        "tete": (C + dx, sommet), "yeux": (C + dxf, ey), "bouche": (C + dxf, ey + 9),
        "cou": (C + dx, int(round(cy + ry * 0.45))), "corps": (C + dx, int(round(cy))),
        "main": (int(round(cx + rx)) - 1, int(round(cy + ry * 0.15))), "main-g": (int(round(cx - rx)), int(round(cy + ry * 0.15))),
        "pieds": (C + dx, pied), "cote": (int(round(cx + rx * 0.45)), pied + 2),
        "antenne": (C + dx + 2 * balance, sommet - haut_antenne),
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

    def ordre(s):
        return ORDRE.index(s.slot) if s.slot in ORDRE else 9

    def etoile(x, y, c):
        for a2, b2 in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
            px(x + a2, y + b2, c)

    # Astral : couronne d'étincelles en orbite (la moitié arrière passe derrière le corps).
    orbite = []
    if st == 4:
        for i in range(5):
            a = t / 700 + i * 2 * math.pi / 5
            orbite.append((int(round(cx + math.cos(a) * (rx + 4))), int(round(sommet + 4 + math.sin(a) * 3.5)),
                           math.sin(a) > 0, ECLAT[i % 3]))

    # Couche arrière (cape, aura…).
    for s in sorted([s for s in portes if s.couche == "derriere"], key=ordre):
        poser(s)
    for x, y, devant, c in orbite:
        if not devant:
            etoile(x, y, c)

    # Ombre au sol.
    if p.suspendu < 0.1:
        demi = int(max(6, 15 * STADE_X[st] - p.saut * 2.8))
        for x in range(C - demi, C + demi):
            if g[52][x] is None:
                g[52][x] = OMBRE_SOL
            if abs(x - C + 0.5) < demi - 3 and g[53][x] is None:
                g[53][x] = OMBRE_SOL

    # Corps : ombrage tramé, reflet ; Nimbus : volutes et bras ; puis cerne.
    m = [[None] * W for _ in range(H)]
    bosses = []
    if st == 3:
        for deg in (-160, -125, -90, -55, -20, 170, 10):
            a = math.radians(deg)
            bosses.append((cx + math.cos(a) * rx * 0.84, cy + math.sin(a) * ry * 0.84, ry * (0.3 if deg < 0 else 0.24)))
    for y in range(H):
        for x in range(W):
            u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            r2 = u * u + v * v
            dans = r2 <= 1
            if not dans and bosses:
                dans = any((x + 0.5 - bx) ** 2 + (y + 0.5 - by) ** 2 <= br * br for bx, by, br in bosses)
                r2 = min(r2, 0.9)
            if not dans:
                continue
            damier = (x + y) % 2 == 0
            reflet = u < -0.25 and v < -0.3
            if reflet and (r2 > 0.45 or (r2 > 0.34 and damier)):
                m[y][x] = te[3]
            elif v > 0.62 or (v > 0.46 and damier):
                m[y][x] = te[1]
            else:
                m[y][x] = te[2]
    if st == 3:
        for sgn in (-1, 1):
            bx, by = cx + sgn * (rx + 1.2), cy + ry * 0.28 + math.sin(t / 300 + sgn) * 0.8
            for y in range(H):
                for x in range(W):
                    if ((x + 0.5 - bx) / 3.2) ** 2 + ((y + 0.5 - by) / 2.4) ** 2 <= 1:
                        m[y][x] = te[1]
    if p.assis <= 0.5:
        pas = int(t // cadence) % 2 if p.marche else -1
        largeur = 5 if st == 1 else 6
        pieds = ((0, C - 8), (1, C + 3)) if st == 1 else ((0, C - 10), (1, C + 4))
        for cote, x0 in pieds:
            haut = pied - (2 if pas == cote else 0)
            for x in range(x0, x0 + largeur):
                for y in (haut, haut + 1):
                    if 0 <= x + dx < W and 0 <= y < H and (y == haut or x0 < x < x0 + largeur - 1):
                        m[y][x + dx] = te[1]
    for y in range(H):
        for x in range(W):
            if m[y][x] is None:
                continue
            bord = x in (0, W - 1) or y in (0, H - 1) or m[y][x - 1] is None or m[y][x + 1] is None \
                or m[y - 1][x] is None or m[y + 1][x] is None
            g[y][x] = te[0] if bord else m[y][x]
    if st == 3:
        # Volutes : deux arcs clairs dans le nuage.
        for sgn in (-1, 1):
            for k in range(7):
                a = math.radians(200 + k * 22) if sgn < 0 else math.radians(-20 - k * 22)
                px(int(round(cx + sgn * rx * 0.55 + math.cos(a) * 3)), int(round(cy - ry * 0.55 + math.sin(a) * 2)), te[3])

    # Visage.
    nom = "spirale" if p.etourdi else OEIL.get(p.expr, "fatigue" if p.fatigue else "ouvert")
    if p.baille:
        nom = "dort"
    if st == 4 and nom == "ouvert":
        nom = "serein"
    peut = p.expr in ("repos", "inquiet", "attente") and not p.etourdi
    og = "cligne" if peut and p.cligne else nom
    od = "cligne" if peut and (p.cligne or p.clin) else nom
    if st == 1 and og == "ouvert" and "oeil-ouvert-g" in B:
        poser(B["oeil-ouvert-g"], False, C - 10 + dxf, ey - 1)
        if od == "ouvert":
            poser(B["oeil-ouvert-g"], True, C + 2 + dxf, ey - 1)
        elif "oeil-" + od in B:
            poser(B["oeil-" + od], True, C + 3 + dxf, ey)
    else:
        ecart = 1 if st == 1 else 0
        if "oeil-" + og in B:
            poser(B["oeil-" + og], False, C - 10 + ecart + dxf, ey)
        if "oeil-" + od in B:
            poser(B["oeil-" + od], True, C + 4 - ecart + dxf, ey)
    bo = B.get("bouche-baille" if p.baille else "bouche-" + p.expr) or B.get("bouche-repos")
    if bo:
        poser(bo, False, C - bo.w // 2 + dxf, ey + 9)
    if p.expr in ("fete", "caresse"):
        joue = int(round(rx)) - 1
        for x0 in (C - joue + dxf, C + joue - 3 + dxf):
            for i in range(3):
                for j in range(2):
                    px(x0 + i, ey + 7 + j, JOUE)

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
        tiges = [(C - 1 + dx, 0)] if st != 3 else [(C - 7 + dx, -1), (C + 5 + dx, 1)]
        base = sommet + (3 if st == 3 else 0)
        for x0, pente in tiges:
            for k in range(1, haut_antenne + 1):
                dec = (balance if k > haut_antenne // 2 else 0) + pente * (k // 3)
                px(x0 + dec, base - k, te[0])
                px(x0 + 1 + dec, base - k, te[0])
            if sp in B:
                s = B[sp]
                tip = x0 + 1 + balance + pente * (haut_antenne // 3)
                poser(s, x=tip + s.dx, y=base - haut_antenne + s.dy, im=im)

    # Nimbus : petite traînée de gouttes qui tombent.
    if st == 3:
        for i, fx in enumerate((-0.6, 0.55, -0.1)):
            ph = (t / 900 + i / 3) % 1
            x, y = int(round(cx + rx * fx)), int(round(cy + ry * 0.7 + ph * 9))
            if y < pied:
                continue
            px(x, y, te[3])
            px(x, y + 1, te[2])
            px(x - 1, y + 1, te[0])
            px(x + 1, y + 1, te[0])
            px(x, y + 2, te[0])

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
            x, y = int(round(cx + sgn * (rx - 2))), int(round(ey - 2 + ph * 8))
            px(x, y - 1, "#1f4f8a")
            for a2, b2 in ((-1, 0), (1, 0), (-1, 1), (1, 1), (0, 2)):
                px(x + a2, y + b2, "#1f4f8a")
            px(x, y, "#b4dbff")
            px(x, y + 1, "#ffffff")
    return g
