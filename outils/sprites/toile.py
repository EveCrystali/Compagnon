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


class Toile:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.g = [[None] * w for _ in range(h)]

    def copie(self):
        t = Toile(self.w, self.h)
        t.g = [r[:] for r in self.g]
        return t

    def p(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.g[y][x] = c

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.g[y][x]
        return None

    def rect(self, x, y, w, h, c):
        for j in range(h):
            for i in range(w):
                self.p(x + i, y + j, c)

    def ell(self, cx, cy, rx, ry, c, cond=None):
        """Disque plein ; centre et rayons en coordonnées continues (pixel i couvre [i, i+1])."""
        for y in range(self.h):
            for x in range(self.w):
                u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                if u * u + v * v <= 1 and (cond is None or cond(x, y, u, v)):
                    self.p(x, y, c)

    def anneau(self, cx, cy, rx, ry, c, ep=1.0):
        for y in range(self.h):
            for x in range(self.w):
                u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                d = math.sqrt(u * u + v * v)
                if 1 - ep / min(rx, ry) <= d <= 1:
                    self.p(x, y, c)

    def ligne(self, x0, y0, x1, y1, c):
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        e = dx + dy
        while True:
            self.p(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * e
            if e2 >= dy:
                e += dy
                x0 += sx
            if e2 <= dx:
                e += dx
                y0 += sy

    def poly(self, pts, c):
        """Polygone plein (règle pair-impair), sommets en coordonnées continues."""
        for y in range(self.h):
            yc = y + 0.5
            xs = []
            for i in range(len(pts)):
                (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
                if (y0 <= yc < y1) or (y1 <= yc < y0):
                    xs.append(x0 + (yc - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for a, b in zip(xs[0::2], xs[1::2]):
                for x in range(self.w):
                    if a <= x + 0.5 < b:
                        self.p(x, y, c)

    def motif(self, x, y, lignes, pal):
        for j, ligne in enumerate(lignes):
            for i, ch in enumerate(ligne):
                if ch in pal and pal[ch] is not None:
                    self.p(x + i, y + j, pal[ch])

    def contour(self, c, diagonales=False):
        """Cerne extérieur d'un pixel autour de tout ce qui est dessiné."""
        a_poser = []
        for y in range(self.h):
            for x in range(self.w):
                if self.g[y][x] is not None:
                    continue
                voisins = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                if diagonales:
                    voisins += [(1, 1), (-1, -1), (1, -1), (-1, 1)]
                if any(self.get(x + a, y + b) is not None for a, b in voisins):
                    a_poser.append((x, y))
        for x, y in a_poser:
            self.p(x, y, c)

    def bord(self, c, sauf=()):
        """Cerne intérieur : les pixels dessinés qui touchent le vide."""
        a_poser = []
        for y in range(self.h):
            for x in range(self.w):
                v = self.g[y][x]
                if v is None or v in sauf:
                    continue
                if any(self.get(x + a, y + b) is None for a, b in [(1, 0), (-1, 0), (0, 1), (0, -1)]):
                    a_poser.append((x, y))
        for x, y in a_poser:
            self.p(x, y, c)

    def remplacer(self, avant, apres, cond=None):
        for y in range(self.h):
            for x in range(self.w):
                if self.g[y][x] == avant and (cond is None or cond(x, y)):
                    self.g[y][x] = apres

    def miroir(self):
        t = Toile(self.w, self.h)
        t.g = [list(reversed(r)) for r in self.g]
        return t

    def coller(self, autre, x, y):
        for j in range(autre.h):
            for i in range(autre.w):
                if autre.g[j][i] is not None:
                    self.p(x + i, y + j, autre.g[j][i])

    def rogner(self):
        """Retire les bords vides ; renvoie (toile, dx, dy) du décalage appliqué."""
        ys = [y for y in range(self.h) if any(v is not None for v in self.g[y])]
        xs = [x for x in range(self.w) if any(self.g[y][x] is not None for y in range(self.h))]
        if not ys:
            return self, 0, 0
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        t = Toile(x1 - x0 + 1, y1 - y0 + 1)
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                t.g[y - y0][x - x0] = self.g[y][x]
        return t, x0, y0


TOUS = []


def ecrire(id_, images, slot="objet", ancre="aucun", point=(0, 0), couche="devant", coiffe=False, duree=0,
           commentaire=""):
    """images : une Toile ou une liste de Toiles (même taille). point : pixel du sprite posé sur l'ancre."""
    if isinstance(images, Toile):
        images = [images]
    w, h = images[0].w, images[0].h
    couleurs = []
    for im in images:
        assert im.w == w and im.h == h, id_
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
    lignes.append("decalage: %d %d" % (-point[0], -point[1]))
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
    os.makedirs(SORTIE, exist_ok=True)
    with open(os.path.join(SORTIE, id_ + ".txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lignes) + "\n")
    TOUS.append(id_)
