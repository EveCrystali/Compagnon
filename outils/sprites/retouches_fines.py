"""Retouches du dessin fin (2×) : reflets, motifs et plis ajoutés aux sprites de la série (fin.SERIE).

Chaque sprite de la série est d'abord rejoué tel quel sur la toile fine (formes calculées à la finesse double).
Les retouches ajoutent ce que la grille 1× ne peut pas porter. Elles sont décrites en peu de mots (RETOUCHES_SIMPLES) :

    L:<couleur>            liseré clair d'un pixel fin en haut des zones de cette couleur (volume, lumière d'en haut)
    G:<couleur>            liseré clair à gauche
    O:<couleur>            ombre d'un pixel fin en bas des zones
    D:<couleur>            ombre à droite
    P:<couleur>:<pas>      plis : filets sombres verticaux tous les <pas> pixels fins (étoffes)
    M:<couleur>            mailles : petits points sombres en quinconce (tricot, paille)
    C:<couleur>            couture : pointillé clair à deux pixels du bas des zones
    R:<couleur>:x,y,rx,ry  reflet : ellipse claire (coordonnées de la grille 1×), seulement sur cette couleur

Une couleur est celle du sprite 1× (#rrggbb ou @base…) ; la couleur ajoutée en est dérivée (plus claire ou plus
sombre) : la palette reste dans la même famille, sans rouge ni vert opposés. Pour un dessin plus particulier,
écrire une fonction décorée par @retouche("id") (fin.py).
"""
from fin import retouche, RETOUCHES  # noqa: F401

TEINTE = {"@contour": "#1f4f8a", "@ombre": "#4a8fdc", "@base": "#6cb6ff", "@clair": "#b4dbff"}


def _rvb(c):
    c = TEINTE.get(c, c)
    return int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)


def eclaircir(c, k=0.38):
    r, v, b = _rvb(c)
    return "#%02x%02x%02x" % tuple(int(round(x + (255 - x) * k)) for x in (r, v, b))


def assombrir(c, k=0.2):
    r, v, b = _rvb(c)
    # Vers un bleu nuit plutôt que vers le noir : les ombres restent colorées.
    return "#%02x%02x%02x" % tuple(int(round(x + (n - x) * k)) for x, n in zip((r, v, b), (20, 24, 48)))


def _bord(t, c, vers, a, b, epais=3):
    """Pixels de couleur c dont le voisin (a, b) n'est pas c, et qui ont `epais` pixels de c derrière eux."""
    poses = []
    for Y in range(t.H):
        for X in range(t.W):
            if t.g[Y][X] != c or t.getf(X + a, Y + b) == c:
                continue
            if all(t.getf(X - a * n, Y - b * n) == c for n in range(1, epais + 1)):
                poses.append((X, Y))
    for X, Y in poses:
        t.g[Y][X] = vers


def lisere(t, c, cote="haut"):
    a, b = {"haut": (0, -1), "gauche": (-1, 0)}[cote]
    _bord(t, c, eclaircir(c), a, b)


def ombre(t, c, cote="bas"):
    a, b = {"bas": (0, 1), "droite": (1, 0)}[cote]
    _bord(t, c, assombrir(c), a, b)


def plis(t, c, pas=10):
    s = assombrir(c, 0.16)
    poses = [(X, Y) for Y in range(t.H) for X in range(t.W)
             if t.g[Y][X] == c and (X + Y // 6) % pas == pas // 2 and t.getf(X - 1, Y) == c and t.getf(X + 1, Y) == c
             and t.getf(X, Y - 2) == c]
    for X, Y in poses:
        t.g[Y][X] = s


def mailles(t, c):
    s = assombrir(c, 0.16)
    poses = [(X, Y) for Y in range(t.H) for X in range(t.W)
             if t.g[Y][X] == c and Y % 4 == 1 and (X + (Y // 4) * 2) % 4 == 0 and t.getf(X, Y - 1) == c and t.getf(X, Y + 1) == c]
    for X, Y in poses:
        t.g[Y][X] = s


def couture(t, c):
    s = eclaircir(c, 0.45)
    poses = [(X, Y) for Y in range(t.H) for X in range(t.W)
             if t.g[Y][X] == c and X % 4 < 2 and t.getf(X, Y + 1) == c and t.getf(X, Y + 2) == c and t.getf(X, Y + 3) != c
             and t.getf(X, Y - 2) == c]
    for X, Y in poses:
        t.g[Y][X] = s


def reflet(t, c, x, y, rx, ry):
    s = eclaircir(c, 0.5)
    for Y in range(t.H):
        for X in range(t.W):
            if t.g[Y][X] == c:
                u, v = ((X + 0.5) / 2 - x) / rx, ((Y + 0.5) / 2 - y) / ry
                if u * u + v * v <= 1:
                    t.g[Y][X] = s


def appliquer(t, recette):
    for mot in recette.split():
        p = mot.split(":")
        op, c = p[0], p[1]
        if op == "L":
            lisere(t, c)
        elif op == "G":
            lisere(t, c, "gauche")
        elif op == "O":
            ombre(t, c)
        elif op == "D":
            ombre(t, c, "droite")
        elif op == "P":
            plis(t, c, int(p[2]) if len(p) > 2 else 10)
        elif op == "M":
            mailles(t, c)
        elif op == "C":
            couture(t, c)
        elif op == "R":
            reflet(t, c, *[float(v) for v in p[2].split(",")])
        else:
            raise ValueError(mot)


VIOLET1, VIOLET2, VIOLET3 = "#3a2a7a", "#6a5acd", "#9b8cff"
ORANGE1, ORANGE2, ORANGE3, ORANGE4 = "#8a4a1f", "#d9803a", "#f69d50", "#ffc89a"
BLEU1, BLEU2, BLEU3, BLEU4 = "#1f4f8a", "#4a8fdc", "#6cb6ff", "#b4dbff"
JAUNE2, JAUNE3 = "#c9a227", "#f5d76e"
SABLE2, SABLE3 = "#c4a77d", "#e8d5b0"
BRUN2, BRUN3 = "#7a4b26", "#a86f3c"
NOIR2, ARDOISE, ARGENT, CREME, BLANC = "#2d333b", "#3b4654", "#b8c4d2", "#f6f8fa", "#ffffff"

RETOUCHES_SIMPLES = {
    # Étincelles : un cœur de lumière plus rond.
    "etincelle-grand": "L:#f69d50 O:#f69d50",
    "etincelle-coeur": "L:#f69d50 O:#f69d50 R:#f69d50:2.2,2.2,1.1,0.9",
    # Chapeaux.
    "beret": "L:#6a5acd O:#3a2a7a L:#3a2a7a",
    "bonnet-pompon": "L:#f69d50 O:#f69d50 O:#f6f8fa L:#4a8fdc M:#4a8fdc M:#f6f8fa O:#1f4f8a",
    "chapeau-sorcier": "L:#6a5acd O:#6a5acd P:#6a5acd:14 L:#3a2a7a O:#c9a227 L:#c9a227",
    "chapeau-pirate": "L:#2d333b O:#2d333b L:#c9a227",
    "haut-de-forme": "G:#2d333b D:#2d333b L:#f69d50 O:#f69d50",
    "chapeau-paille": "M:#f5d76e L:#f5d76e O:#c9a227 L:#4a8fdc",
    "casquette": "L:#6cb6ff O:#4a8fdc L:#1f4f8a C:#6cb6ff",
    "chapeau-explorateur": "L:#e8d5b0 O:#c4a77d L:#a86f3c C:#c4a77d",
    "chapeau-melon": "L:#2d333b O:#2d333b L:#f69d50 O:#f69d50",
    "chapeau-cowboy": "L:#7a4b26 O:#7a4b26 L:#a86f3c C:#a86f3c",
    "acc-bonnet": "L:#f69d50 O:#f69d50 O:#f6f8fa",
    "acc-couronne": "L:#f5d76e O:#f5d76e O:#c9a227 L:#6cb6ff",
    "acc-casque": "L:#768390 L:#f69d50 O:#f69d50",
    "acc-toque": "O:#ffffff O:#f6f8fa",
    "tenue-nuit-bonnet": "L:#b4dbff O:#b4dbff O:#f6f8fa",
    "casque-passoire": "L:#b8c4d2 O:#b8c4d2 L:#768390",
    "couronne-fleurs": "L:#6cb6ff L:#9b8cff L:#f69d50 L:#f5d76e",
    # Lunettes : un trait de lumière sur les verres.
    "lunettes-rondes": "",
    "lunettes-coeur": "L:#ff9ec7 O:#ff9ec7",
    "lunettes-etoiles": "L:#f5d76e O:#f5d76e",
    "lunettes-plage": "L:#f69d50 O:#f69d50 L:#1f4f8a",
    "masque-plongee": "L:#4a8fdc O:#4a8fdc L:#f69d50",
    "monocle": "L:#c9a227",
    # Cou et dos.
    "echarpe": "M:#f69d50 M:#f6f8fa L:#f69d50 O:#f69d50 O:#f6f8fa",
    "echarpe-tricot": "M:#f69d50 M:#f6f8fa O:#f69d50 O:#f6f8fa",
    "medaille": "L:#f5d76e O:#f5d76e L:#6cb6ff",
    "cravate": "L:#1f4f8a",
    "foulard-explorateur": "L:#f69d50 O:#f69d50 P:#f69d50:8",
    "acc-noeud": "L:#f69d50 O:#f69d50",
    "cape": "P:#6a5acd:12 P:#9b8cff:10 P:#3a2a7a:10 O:#6a5acd L:#6a5acd",
    "astral-cape": "P:#6a5acd:12 P:#9b8cff:10 O:#6a5acd",
    "sac-a-dos": "L:#f69d50 O:#f69d50 C:#f69d50 L:#d9803a",
    "sac-explorateur": "L:#f69d50 M:#f69d50 L:#e8d5b0 O:#e8d5b0 L:#c4a77d C:#8a6e4b L:#4a8fdc",
    "cartable": "L:#f69d50 O:#f69d50 C:#f69d50 L:#7a4b26",
    # En main.
    "parapluie": "L:#6cb6ff L:#4a8fdc O:#6cb6ff O:#4a8fdc G:#3b4654",
    "baluchon": "L:#f69d50 O:#f69d50 G:#7a4b26",
    "lanterne": "L:#7a4b26 G:#fff6cc O:#f69d50",
    "torche": "G:#a86f3c D:#a86f3c L:#c4a77d",
    "epee-bois": "",
    "bouclier-couvercle": "L:#b8c4d2 O:#b8c4d2 L:#f69d50",
    "boussole": "L:#c9a227 O:#c9a227 O:#f6f8fa",
    "valise": "L:#6cb6ff O:#6cb6ff C:#6cb6ff L:#4a8fdc",
    "tasse-cafe": "O:#f6f8fa G:#f6f8fa L:#7a4b26",
    "ballon-helium": "O:#f69d50 D:#f69d50",
    "baguette": "",
    # Compagnons.
    "petit-poisson-bocal": "L:#f69d50",
    "oiseau": "L:#6cb6ff O:#6cb6ff O:#f6f8fa L:#4a8fdc",
    "slime-apprivoise": "O:#3fb8e0",
    "petit-robot": "L:#b8c4d2 O:#b8c4d2 L:#768390 L:#f5d76e",
    "mini-dragon": "L:#6a5acd O:#6a5acd L:#f69d50 O:#f5d76e",
    "tortue": "L:#2689b8 O:#2689b8 L:#c4a77d",
    "escargot": "L:#6a5acd O:#6a5acd O:#f6f8fa",
    # Objets d'expédition.
    "carte-tresor": "L:#e8d5b0 O:#e8d5b0",
    "coffre-expedition": "L:#a86f3c O:#a86f3c L:#b8c4d2 L:#f5d76e",
    "galette-route": "L:#c4a77d O:#c4a77d",
    "jus-etoile": "G:#4a8fdc D:#4a8fdc L:#f5d76e",
    "eclat-cristal": "",
}


def _simple(recette):
    def toutes(images):
        for t in images:
            appliquer(t, recette)
        return images
    return toutes


for _id, _recette in RETOUCHES_SIMPLES.items():
    if _recette:
        RETOUCHES[_id] = _simple(_recette)
