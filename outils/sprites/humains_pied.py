"""Les personnages humains en pied (docs/SCENES.md, « Personnages en pied ») : dessinés pixel par pixel à l'échelle de
la scène (le pixel du décor fin), à partir d'une petite silhouette paramétrée — bottes, jambes, manteau, bras, cou,
tête, chevelure, coiffe, barbe, accessoires — puis un cerne sombre d'un pixel tout autour et une ombre à droite
(la lumière vient de la gauche, comme dans les décors).

Cinq images dans l'ordre des portraits (repos ; inspiré : le haut du corps monte d'un pixel ; yeux fermés ; bouche
mi-ouverte ; bouche ouverte), pour que les animations nommées `repos`, `cligne`, `parle` soient les mêmes que celles
des personnages-objets. Tous regardent un peu vers la gauche (le miroir les retourne si Pilou est à droite).
Couleurs : celles de leurs portraits (LORE.md), jamais d'opposition rouge / vert.
"""

CERNE = "#1a1726"
PEAU, PEAU_O = "#e8b48a", "#c98d66"
OEIL = "#1c2128"
BOUCHE = "#3b1f33"


def _vide(w, h):
    return [[None] * w for _ in range(h)]


def _rect(g, x0, y0, x1, y1, c):
    for y in range(max(0, y0), min(len(g), y1)):
        for x in range(max(0, x0), min(len(g[0]), x1)):
            g[y][x] = c


def _px(g, x, y, c):
    if 0 <= y < len(g) and 0 <= x < len(g[0]):
        g[y][x] = c


def _cerner(g):
    """Un cerne d'un pixel autour de tout ce qui est plein (dans la toile)."""
    h, w = len(g), len(g[0])
    plein = {(x, y) for y in range(h) for x in range(w) if g[y][x] is not None}
    for (x, y) in list(plein):
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            X, Y = x + a, y + b
            if 0 <= X < w and 0 <= Y < h and (X, Y) not in plein:
                g[Y][X] = CERNE


def _ombrer(g, couleurs):
    """Le côté droit de chaque masse de couleur s'assombrit d'un cran (la lumière vient de la gauche)."""
    h, w = len(g), len(g[0])
    for y in range(h):
        for x in range(w - 1, -1, -1):
            c = g[y][x]
            if c in couleurs and (x + 1 >= w or g[y][x + 1] != c or x + 2 >= w or g[y][x + 2] != c):
                if x + 1 < w and g[y][x + 1] in (None, CERNE):
                    g[y][x] = couleurs[c]


class Silhouette:
    """Les mesures d'un personnage (pixels de scène). Les pieds sont sur la dernière ligne."""

    def __init__(self, **kw):
        self.taille = 40          # du haut du crâne aux semelles
        self.largeur = 14         # largeur des épaules
        self.tete = 9             # diamètre de la tête
        self.jambes = 12
        self.bottes = 3
        self.manteau = "#2e3f78"
        self.manteau_o = "#1e2a55"
        self.pantalon = "#3b4654"
        self.botte = "#3b2a1e"
        self.long = False         # manteau long (pas de jambes visibles au-dessus des genoux)
        self.peau = PEAU
        self.peau_o = PEAU_O
        self.__dict__.update(kw)


def personnage(s, image, dessin):
    """Une image (0 repos, 1 inspiré, 2 yeux fermés, 3 et 4 parole) : la silhouette, puis `dessin(g, repere)` pour
    les traits propres au personnage (cheveux, coiffe, barbe, accessoires)."""
    W = s.largeur + 12
    H = s.taille + 3
    g = _vide(W, H)
    cx = W // 2
    sol = H - 1
    inspire = 1 if image == 1 else 0
    # Bottes et jambes.
    yb = sol - s.bottes + 1
    _rect(g, cx - 5, yb, cx - 1, sol + 1, s.botte)
    _rect(g, cx + 1, yb, cx + 5, sol + 1, s.botte)
    yj = yb - s.jambes
    _rect(g, cx - 4, yj, cx - 1, yb, s.pantalon)
    _rect(g, cx + 1, yj, cx + 4, yb, s.pantalon)
    # Le buste (manteau), qui monte d'un pixel à l'inspiration.
    yt = s.taille - s.tete - s.jambes - s.bottes          # hauteur du buste
    haut_buste = sol - s.taille + s.tete + 1 - inspire
    bas_buste = yj + (6 if s.long else 1)
    demi = s.largeur // 2
    _rect(g, cx - demi, haut_buste + 1, cx + demi, bas_buste, s.manteau)
    _rect(g, cx - demi + 1, haut_buste, cx + demi - 1, haut_buste + 1, s.manteau)
    # Les bras, le long du corps, et les mains.
    _rect(g, cx - demi - 2, haut_buste + 2, cx - demi, bas_buste - 3, s.manteau)
    _rect(g, cx + demi, haut_buste + 2, cx + demi + 2, bas_buste - 3, s.manteau_o)
    _rect(g, cx - demi - 2, bas_buste - 3, cx - demi, bas_buste - 1, s.peau)
    _rect(g, cx + demi, bas_buste - 3, cx + demi + 2, bas_buste - 1, s.peau_o)
    # Le cou et la tête.
    r = s.tete / 2.0
    tx, ty = cx, haut_buste - r + 0.5
    _rect(g, cx - 2, haut_buste - 1, cx + 2, haut_buste + 1, s.peau_o)
    for y in range(H):
        for x in range(W):
            if ((x + 0.5 - tx) / r) ** 2 + ((y + 0.5 - ty) / (r * 1.05)) ** 2 <= 1:
                g[y][x] = s.peau
    # Le visage, un peu tourné vers la gauche : deux yeux, la bouche.
    yo = int(round(ty)) - 1
    if image == 2:
        _px(g, cx - 3, yo + 1, OEIL)
        _px(g, cx - 2, yo + 1, OEIL)
        _px(g, cx + 1, yo + 1, OEIL)
        _px(g, cx + 2, yo + 1, OEIL)
    else:
        _rect(g, cx - 3, yo, cx - 2, yo + 2, OEIL)
        _rect(g, cx + 1, yo, cx + 2, yo + 2, OEIL)
    ym = yo + 3
    if image == 3:
        _rect(g, cx - 2, ym, cx + 1, ym + 1, BOUCHE)
    elif image == 4:
        _rect(g, cx - 2, ym, cx + 1, ym + 2, BOUCHE)
    else:
        _rect(g, cx - 2, ym, cx + 1, ym + 1, s.peau_o)
    repere = dict(cx=cx, tx=tx, ty=ty, r=r, haut=haut_buste, bas=bas_buste, demi=demi, yo=yo, ym=ym, sol=sol, yj=yj,
                  image=image, W=W, H=H)
    dessin(g, repere)
    _ombrer(g, {s.manteau: s.manteau_o, s.peau: s.peau_o, s.pantalon: "#2f333d"})
    _cerner(g)
    return g


# ---- Les gens du « Phare éteint »

def _casquette(g, p, couleur, visiere, insigne):
    cx, ty, r = p["cx"], p["ty"], p["r"]
    haut = int(ty - r) - 1
    _rect(g, cx - 5, haut, cx + 5, haut + 3, couleur)
    _rect(g, cx - 6, haut + 3, cx + 3, haut + 4, visiere)
    _px(g, cx - 1, haut + 1, insigne)


def anselme(g, p):
    """Le gardien : barbe blanche, casquette marine à insigne de laiton, yeux pâles."""
    cx, yo, ym = p["cx"], p["yo"], p["ym"]
    _casquette(g, p, "#24305a", "#141a2e", "#e8b45a")
    blanc = "#eef0f4"
    _rect(g, cx - 4, ym - 1, cx + 4, ym + 4, blanc)
    _rect(g, cx - 3, ym + 4, cx + 3, ym + 6, blanc)
    if p["image"] in (3, 4):
        _rect(g, cx - 2, ym, cx + 1, ym + (1 if p["image"] == 3 else 2), BOUCHE)
    if p["image"] != 2:                                # les yeux pâles, voilés
        _px(g, cx - 3, yo, "#9fb8cc")
        _px(g, cx + 1, yo, "#9fb8cc")
    # Les boutons de laiton du caban.
    for y in (p["haut"] + 4, p["haut"] + 8, p["haut"] + 12):
        _px(g, cx - 1, y, "#e8b45a")


def lison(g, p):
    """Lison : deux nattes cuivrées, taches de son, ciré bleu, des bottes jaunes bien trop grandes."""
    cx, ty, r, yo = p["cx"], p["ty"], p["r"], p["yo"]
    cuivre, cuivre_o = "#c4621a", "#8a4a1f"
    haut = int(ty - r)
    _rect(g, cx - 4, haut, cx + 4, haut + 3, cuivre)
    _rect(g, cx - 5, haut + 2, cx - 3, haut + 9, cuivre_o)
    _rect(g, cx + 3, haut + 2, cx + 5, haut + 9, cuivre_o)
    _px(g, cx - 5, haut + 9, "#4a5ea8")                 # les rubans
    _px(g, cx + 4, haut + 9, "#4a5ea8")
    _px(g, cx - 4, yo + 2, "#c98d66")                   # taches de son
    _px(g, cx + 2, yo + 2, "#c98d66")


def tudal(g, p):
    """Tudal : bonnet de laine orange, barbe de trois jours, pull marine à côtes."""
    cx, ty, r, ym = p["cx"], p["ty"], p["r"], p["ym"]
    haut = int(ty - r) - 1
    _rect(g, cx - 5, haut, cx + 5, haut + 4, "#f08a2c")
    _rect(g, cx - 5, haut + 3, cx + 5, haut + 4, "#c4621a")
    for x in range(cx - 5, cx + 5, 2):
        _px(g, x, haut + 3, "#ffd0a0")
    barbe = "#8a7a6c"
    for x in range(cx - 4, cx + 4):
        for y in range(ym - 1, ym + 3):
            if (x + y) % 2 == 0 and g[y][x] in (PEAU, PEAU_O):
                g[y][x] = barbe
    if p["image"] in (3, 4):
        _rect(g, cx - 2, ym, cx + 1, ym + (1 if p["image"] == 3 else 2), BOUCHE)
    for x in range(cx - p["demi"] + 2, cx + p["demi"] - 1, 3):     # les côtes du pull
        _rect(g, x, p["haut"] + 3, x + 1, p["bas"] - 1, "#4a5ea8")


def perrine(g, p):
    """Perrine : chignon châtain, joues rondes, tablier crème, un torchon sur l'épaule."""
    cx, ty, r, yo = p["cx"], p["ty"], p["r"], p["yo"]
    chatain = "#8a5a33"
    haut = int(ty - r)
    _rect(g, cx - 4, haut, cx + 4, haut + 3, chatain)
    _rect(g, cx - 2, haut - 3, cx + 2, haut, chatain)
    _px(g, cx - 4, yo + 2, "#f2a88a")
    _px(g, cx + 3, yo + 2, "#f2a88a")
    _rect(g, cx - 4, p["haut"] + 5, cx + 4, p["bas"], "#f6ead2")    # le tablier
    _rect(g, cx + 2, p["haut"], cx + p["demi"], p["haut"] + 4, "#fbf3e4")  # le torchon


def odile(g, p):
    """Odile : carré gris, lunettes rondes, une écharpe bleue en travers."""
    cx, ty, r, yo = p["cx"], p["ty"], p["r"], p["yo"]
    gris = "#adbac7"
    haut = int(ty - r)
    _rect(g, cx - 5, haut, cx + 5, haut + 3, gris)
    _rect(g, cx - 5, haut + 3, cx - 3, yo + 4, gris)
    _rect(g, cx + 3, haut + 3, cx + 5, yo + 4, gris)
    monture = "#e6ecf2"                                            # les lunettes rondes : montures claires
    for x in (cx - 4, cx - 1, cx, cx + 2):
        _px(g, x, yo, monture)
        _px(g, x, yo + 1, monture)
    for k in range(9):                                             # l'écharpe en travers
        _px(g, cx - 5 + k, p["haut"] + 1 + k // 2, "#6aa6c7")
        _px(g, cx - 5 + k, p["haut"] + 2 + k // 2, "#4f7fa6")


def basile(g, p):
    """Basile : crâne lisse, couronne de cheveux, loupe d'horloger vissée à l'œil, moustache, montre à gousset."""
    cx, ty, r, yo, ym = p["cx"], p["ty"], p["r"], p["yo"], p["ym"]
    gris = "#d4e0ea"
    _rect(g, cx - 5, int(ty) - 2, cx - 3, int(ty) + 1, gris)
    _rect(g, cx + 3, int(ty) - 2, cx + 5, int(ty) + 1, gris)
    _rect(g, cx - 4, yo - 1, cx - 1, yo + 2, "#3b4654")            # la loupe
    _px(g, cx - 3, yo, "#b4dbff")
    _rect(g, cx - 3, ym - 1, cx + 2, ym, "#d4e0ea")                # la moustache
    _rect(g, cx - 4, p["haut"] + 2, cx + 4, p["bas"] - 1, "#6e4c2a")  # le gilet
    _px(g, cx + 2, p["haut"] + 6, "#e8b45a")                       # la montre et sa chaîne
    _px(g, cx + 1, p["haut"] + 5, "#e8b45a")
    _px(g, cx, p["haut"] + 5, "#e8b45a")


def vernier(g, p):
    """M. Vernier : chapeau de pluie et ciré jaunes, des jumelles au cou."""
    cx, ty, r = p["cx"], p["ty"], p["r"]
    jaune, jaune_o = "#f2bd3c", "#c08a1c"
    haut = int(ty - r) - 1
    _rect(g, cx - 4, haut, cx + 4, haut + 3, jaune)
    _rect(g, cx - 7, haut + 3, cx + 7, haut + 4, jaune_o)
    _rect(g, cx - 3, p["haut"] + 3, cx + 3, p["haut"] + 6, "#1c2128")  # les jumelles
    _px(g, cx - 2, p["haut"] + 4, "#8796a8")
    _px(g, cx + 1, p["haut"] + 4, "#8796a8")


GENS = {
    ("phare-eteint", "anselme"): (Silhouette(taille=44, largeur=14, long=True, manteau="#24305a", manteau_o="#141a2e"), anselme),
    ("phare-eteint", "lison"): (Silhouette(taille=30, largeur=10, tete=9, jambes=6, bottes=4, manteau="#2f7ed8",
                                           manteau_o="#1f5fae", pantalon="#3b4654", botte="#f2bd3c"), lison),
    ("phare-eteint", "tudal"): (Silhouette(taille=44, largeur=18, manteau="#2e3f78", manteau_o="#1e2a55"), tudal),
    ("phare-eteint", "perrine"): (Silhouette(taille=40, largeur=16, long=True, manteau="#6e3d86", manteau_o="#4a2a5a"), perrine),
    ("phare-eteint", "odile"): (Silhouette(taille=40, largeur=14, long=True, manteau="#3b4654", manteau_o="#2f333d"), odile),
    ("phare-eteint", "basile"): (Silhouette(taille=38, largeur=14, manteau="#4a4f5c", manteau_o="#2f333d"), basile),
    ("phare-eteint", "vernier"): (Silhouette(taille=42, largeur=16, long=True, manteau="#f2bd3c", manteau_o="#c08a1c",
                                             pantalon="#3b4654", botte="#1c2128"), vernier),
}


def images(cle):
    s, dessin = GENS[cle]
    return [personnage(s, k, dessin) for k in range(5)]
