"""Petite toile de pixels pour dessiner les sprites de Pilou (outil de fabrication, pas embarqué).

Chaque sprite est une grille de couleurs (#rrggbb ou référence @contour/@ombre/@base/@clair à la teinte
de Pilou). `ecrire` la range dans assets/sprites/<id>.txt, au format lu par le PC (Sprites.cs) et par
l'app Android (Sprites.java) :

    # commentaire
    id: lunettes-rondes
    slot: yeux                 tete | yeux | cou | dos | main | compagnon | effet | visage | objet
    ancre: yeux                point de Pilou où se pose le sprite (voir docs/SPRITES.md)
    decalage: -10 -2           coin haut-gauche du sprite par rapport à l'ancre, en pixels de grille
    couche: devant             devant (défaut) | derriere (avant le corps)
    coiffe: oui                cache l'antenne
    duree: 250                 ms par image (plusieurs images séparées par ---)
    palette: a=#1c2128 b=@contour
    images:
    ..aa..
    .abba.
    ---
    ..aa..
"""
import math
import os

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.normpath(os.path.join(ICI, "..", "..", "assets", "sprites"))
LETTRES = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


# Échelle du dessin : 1 (grille 48 × 56, assets/sprites) ou 2 (dessin fin, grille 96 × 112, assets/sprites2x).
# En 2, les mêmes fonctions de dessin sont rejouées sur une toile deux fois plus fine : les coordonnées restent
# celles de la grille 1× (les demi-unités sont permises), les ellipses, polygones, lignes et cernes sont calculés
# à la finesse double. Voir fin.py et docs/SPRITES.md (« Redessiner un sprite en 2× »).
ECHELLE = 1
# Offsets à moins de √5 pixels : épaisseur 2 partout, diagonales comprises (cerne fin).
DISQUE = [(a, b) for a in range(-2, 3) for b in range(-2, 3) if 0 < a * a + b * b <= 5]
CARRE = [(a, b) for a in range(-2, 3) for b in range(-2, 3) if (a, b) != (0, 0)]
CROIX = [(1, 0), (-1, 0), (0, 1), (0, -1)]
HUIT = CROIX + [(1, 1), (-1, -1), (1, -1), (-1, 1)]


def fin():
    """Vrai pendant le dessin fin (2×) : pour ajouter reflets, motifs et plis que la grille 1× ne peut pas porter."""
    return ECHELLE == 2


class Toile:
    """Toile de w × h pixels de la grille 1×. `g` est la grille réelle (w·e × h·e, e = échelle du dessin)."""

    def __init__(self, w, h):
        self.e = ECHELLE
        self.w, self.h = w, h
        self.g = [[None] * (w * self.e) for _ in range(h * self.e)]

    # ---- accès à la grille réelle (pixels fins en 2×)
    @property
    def W(self):
        return len(self.g[0]) if self.g else 0

    @property
    def H(self):
        return len(self.g)

    def pf(self, X, Y, c):
        """Un pixel de la grille réelle (fin en 2×)."""
        X, Y = int(X), int(Y)
        if 0 <= X < self.W and 0 <= Y < self.H:
            self.g[Y][X] = c

    def getf(self, X, Y):
        if 0 <= X < self.W and 0 <= Y < self.H:
            return self.g[Y][X]
        return None

    def copie(self):
        t = Toile(self.w, self.h)
        t.e = self.e
        t.g = [r[:] for r in self.g]
        return t

    def p(self, x, y, c):
        e = self.e
        if e == 1:
            x, y = int(x), int(y)
            if 0 <= x < self.w and 0 <= y < self.h:
                self.g[y][x] = c
            return
        X, Y = int(x * e), int(y * e)
        cases = [(X + a, Y + b) for b in range(e) for a in range(e) if 0 <= X + a < self.W and 0 <= Y + b < self.H]
        if x == int(x) and y == int(y):
            # Pixel entier de la grille 1× : sur un bord déjà arrondi, on ne repeint que ce qui est dessiné.
            pleins = [k for k in cases if self.g[k[1]][k[0]] is not None]
            if pleins and len(pleins) < len(cases):
                cases = pleins
        for a, b in cases:
            self.g[b][a] = c

    def get(self, x, y):
        e = self.e
        if e == 1:
            if 0 <= x < self.w and 0 <= y < self.h:
                return self.g[y][x]
            return None
        X, Y = int(x * e), int(y * e)
        for b in range(e):
            for a in range(e):
                v = self.getf(X + a, Y + b)
                if v is not None:
                    return v
        return None

    def rect(self, x, y, w, h, c):
        e = self.e
        if e == 1:
            for j in range(h):
                for i in range(w):
                    self.p(x + i, y + j, c)
            return
        X, Y = int(round(x * e)), int(round(y * e))
        for j in range(int(round(h * e))):
            for i in range(int(round(w * e))):
                self.pf(X + i, Y + j, c)

    def ell(self, cx, cy, rx, ry, c, cond=None):
        """Disque plein ; centre et rayons en coordonnées continues (pixel i couvre [i, i+1])."""
        e = self.e
        for Y in range(self.H):
            for X in range(self.W):
                u, v = ((X + 0.5) / e - cx) / rx, ((Y + 0.5) / e - cy) / ry
                if u * u + v * v <= 1 and (cond is None or cond(X // e, Y // e, u, v)):
                    self.g[Y][X] = c

    def anneau(self, cx, cy, rx, ry, c, ep=1.0):
        e = self.e
        for Y in range(self.H):
            for X in range(self.W):
                u, v = ((X + 0.5) / e - cx) / rx, ((Y + 0.5) / e - cy) / ry
                d = math.sqrt(u * u + v * v)
                if 1 - ep / min(rx, ry) <= d <= 1:
                    self.g[Y][X] = c

    def ligne(self, x0, y0, x1, y1, c):
        e = self.e
        if e == 1:
            x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        else:
            x0, y0, x1, y1 = int(round(x0 * e)), int(round(y0 * e)), int(round(x1 * e)), int(round(y1 * e))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            for b in range(e):
                for a in range(e):
                    self.pf(x0 + a, y0 + b, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def poly(self, pts, c):
        """Polygone plein (règle pair-impair), sommets en coordonnées continues."""
        e = self.e
        for Y in range(self.H):
            yc = (Y + 0.5) / e
            xs = []
            for i in range(len(pts)):
                (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
                if (y0 <= yc < y1) or (y1 <= yc < y0):
                    xs.append(x0 + (yc - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for a, b in zip(xs[0::2], xs[1::2]):
                for X in range(self.W):
                    if a <= (X + 0.5) / e < b:
                        self.g[Y][X] = c

    def motif(self, x, y, lignes, pal):
        e = self.e
        if e == 1:
            for j, ligne in enumerate(lignes):
                for i, ch in enumerate(ligne):
                    if ch in pal and pal[ch] is not None:
                        self.p(x + i, y + j, pal[ch])
            return
        # Dessin fin : le motif 1× est agrandi par la règle commune (rendu.agrandir_image), puis posé.
        import rendu
        net = ["".join(ch if ch in pal and pal[ch] is not None else "." for ch in ligne) for ligne in lignes]
        gros = rendu.agrandir_image(net, {k: v for k, v in pal.items() if v is not None})
        X, Y = int(round(x * e)), int(round(y * e))
        for j, ligne in enumerate(gros):
            for i, ch in enumerate(ligne):
                if ch != ".":
                    self.pf(X + i, Y + j, pal[ch])

    def motif_fin(self, x, y, lignes, pal):
        """Motif dessiné directement en pixels fins (2×), posé au point (x, y) de la grille 1×."""
        X, Y = int(round(x * self.e)), int(round(y * self.e))
        for j, ligne in enumerate(lignes):
            for i, ch in enumerate(ligne):
                if ch in pal and pal[ch] is not None:
                    self.pf(X + i, Y + j, pal[ch])

    def _voisins(self, diagonales):
        if self.e == 1:
            return HUIT if diagonales else CROIX
        return CARRE if diagonales else DISQUE

    def contour(self, c, diagonales=False):
        """Cerne extérieur d'un pixel (de la grille 1× : deux pixels fins en 2×) autour de tout ce qui est dessiné."""
        voisins = self._voisins(diagonales)
        a_poser = []
        for Y in range(self.H):
            for X in range(self.W):
                if self.g[Y][X] is not None:
                    continue
                if any(self.getf(X + a, Y + b) is not None for a, b in voisins):
                    a_poser.append((X, Y))
        for X, Y in a_poser:
            self.g[Y][X] = c

    def bord(self, c, sauf=()):
        """Cerne intérieur : les pixels dessinés qui touchent le vide."""
        voisins = self._voisins(False)
        a_poser = []
        for Y in range(self.H):
            for X in range(self.W):
                v = self.g[Y][X]
                if v is None or v in sauf:
                    continue
                if any(self.getf(X + a, Y + b) is None for a, b in voisins):
                    a_poser.append((X, Y))
        for X, Y in a_poser:
            self.g[Y][X] = c

    def remplacer(self, avant, apres, cond=None):
        e = self.e
        for Y in range(self.H):
            for X in range(self.W):
                if self.g[Y][X] == avant and (cond is None or cond(X // e, Y // e)):
                    self.g[Y][X] = apres

    def miroir(self):
        t = Toile(self.w, self.h)
        t.e = self.e
        t.g = [list(reversed(r)) for r in self.g]
        return t

    def coller(self, autre, x, y):
        X, Y = int(round(x * self.e)), int(round(y * self.e))
        for j in range(autre.H):
            for i in range(autre.W):
                if autre.g[j][i] is not None:
                    self.pf(X + i, Y + j, autre.g[j][i])

    def rogner(self):
        """Retire les bords vides ; renvoie (toile, dx, dy) du décalage appliqué (en pixels de la grille 1×)."""
        e = self.e
        ys = [y for y in range(self.H) if any(v is not None for v in self.g[y])]
        xs = [x for x in range(self.W) if any(self.g[y][x] is not None for y in range(self.H))]
        if not ys:
            return self, 0, 0
        x0, x1, y0, y1 = min(xs) // e, max(xs) // e, min(ys) // e, max(ys) // e
        t = Toile(x1 - x0 + 1, y1 - y0 + 1)
        t.e = e
        t.g = [r[x0 * e:(x1 + 1) * e] for r in self.g[y0 * e:(y1 + 1) * e]]
        return t, x0, y0


TOUS = []
SORTIE2 = os.path.normpath(os.path.join(ICI, "..", "..", "assets", "sprites2x"))
TOUS2 = []
# Dessin fin (ECHELLE = 2) : seuls ces identifiants sont écrits dans assets/sprites2x (None : tous) ; les autres
# restent agrandis automatiquement par le rendu. RETOUCHES : id -> fonction(images) appelée avant l'écriture,
# pour ajouter en pixels fins ce que la grille 1× ne peut pas porter (fin.py).
FINS = None
RETOUCHES = {}


def ecrire(id_, images, slot="objet", ancre="aucun", point=(0, 0), couche="devant", coiffe=False, duree=0,
           commentaire=""):
    """images : une Toile ou une liste de Toiles (même taille). point : pixel du sprite posé sur l'ancre."""
    if isinstance(images, Toile):
        images = [images]
    e = images[0].e
    if e != 1:
        if FINS is not None and id_ not in FINS:
            return
        if id_ in RETOUCHES:
            images = RETOUCHES[id_](images) or images
    w, h = images[0].W, images[0].H
    couleurs = []
    for im in images:
        assert im.W == w and im.H == h, id_
        for r in im.g:
            for v in r:
                if v is not None and v not in couleurs:
                    couleurs.append(v)
    assert len(couleurs) <= len(LETTRES), id_
    lettre = {c: LETTRES[i] for i, c in enumerate(couleurs)}
    lignes = []
    if commentaire:
        lignes.append("# " + commentaire)
    lignes.append("id: " + id_)
    lignes.append("slot: " + slot)
    lignes.append("ancre: " + ancre)
    lignes.append("decalage: %d %d" % (-int(round(point[0] * e)), -int(round(point[1] * e))))
    if couche != "devant":
        lignes.append("couche: " + couche)
    if coiffe:
        lignes.append("coiffe: oui")
    if duree:
        lignes.append("duree: %d" % duree)
    lignes.append("palette: " + " ".join("%s=%s" % (lettre[c], c) for c in couleurs))
    lignes.append("images:")
    for k, im in enumerate(images):
        if k:
            lignes.append("---")
        for r in im.g:
            lignes.append("".join(lettre[v] if v is not None else "." for v in r))
    sortie = SORTIE if e == 1 else SORTIE2
    os.makedirs(sortie, exist_ok=True)
    with open(os.path.join(sortie, id_ + ".txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lignes) + "\n")
    (TOUS if e == 1 else TOUS2).append(id_)
