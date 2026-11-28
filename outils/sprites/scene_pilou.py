"""Le mini-Pilou de scène (docs/SCENES.md) : Pilou en pied dans les décors des campagnes, à l'échelle du décor fin
(192 × 80). Taille M décidée avec Antoine (docs/maquettes/animations/DECISIONS.md) : corps 20 × 15 pixels fins, toile
34 × 36, les pieds posent sur la ligne 33 (ANCRE_Y), le centre est la colonne 17 (ANCRE_X).

Dessiné nativement en fin, pixel par pixel (il n'a pas de version 1× : la scène est toujours en dessin fin). Le corps,
les pieds et la tige de l'antenne prennent la teinte de Pilou (@contour, @ombre, @base, @clair) ; les yeux, la bouche,
l'étincelle et les joues gardent leurs couleurs.

Chaque image est un jeu de paramètres (écrasement et étirement, saut, regard, pieds, antenne qui traîne derrière le
mouvement, étincelle, expression) : les principes du dessin animé (anticipation, élan, amorti, mouvement secondaire),
tenus en douze images par seconde. Les animations nommées et leur rythme sont dans ANIMS (écrites dans
assets/scenes/animations.txt par theatre.py).
"""
import math

C_CONTOUR, C_OMBRE, C_BASE, C_CLAIR = "@contour", "@ombre", "@base", "@clair"
ENCRE, BLANC = "#1c2128", "#ffffff"
ETIN, ETIN_C, ETIN_F = "#f69d50", "#ffc89a", "#d9803a"
JOUE = "#f2a88a"
SUEUR = "#b4dbff"
LANGUE = "#f69d50"
SOL1, SOL2 = "#080c1e5a", "#080c1e2d"
COEUR = "#f2a88a"

ID = "scene-pilou"
W, H = 34, 36
ANCRE_X, ANCRE_Y = 17, 33
K = 1.25            # facteur du corps (taille M : 8 × 1,25 = 10 de demi-largeur, 6 × 1,25 = 7,5 de demi-hauteur)
EW, GAP, PIED, ANT = 4, 4, 4, 5

YEUX = {
    "repos": [".##.", "#w##", "####", ".##."],
    "grands": [".ww.", "w##w", "w##w", ".ww."],
    "ferme": ["....", "....", "#..#", ".##."],
    "joie": ["....", ".##.", "#..#", "...."],
    "triste": ["....", "####", "#w##", ".##."],
    "fatigue": ["....", "....", "####", ".##."],
    "determine": ["....", "####", "#w##", ".##."],
    "colere_g": ["#...", ".#..", "#w##", ".##."],      # sourcil qui descend vers le nez (œil gauche)
    "colere_d": ["...#", "..#.", "#w##", ".##."],
}
YEUX_MIROIR = {"colere": ("colere_g", "colere_d"), "malice": ("repos", "joie")}


def _vide():
    return [[None] * W for _ in range(H)]


def pilou(sx=1.0, sy=1.0, dy=0, regard=0, regard_y=0, yeux="repos", bouche="sourire", pieds=(0, 0, 0, 0),
          antenne=0, etincelle=0, sueur=False, joues=False, ombre_sol=1.0, dx=0, penche=0, coeur=False):
    """Une image (grille de couleurs, None = transparent). sx, sy : écrasement / étirement ; dy : hauteur du saut ;
    dx : décalage (il tremble) ; pieds : (dx, dy) du pied gauche puis du droit ; antenne : inclinaison de la tige
    (-2..2) ; etincelle : 0..3 ; penche : le haut du corps penche vers l'avant."""
    g = _vide()

    def px(x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < W and 0 <= y < H and c is not None:
            g[y][x] = c

    rx, ry = 8.0 * K * sx, 6.0 * K * sy
    bas = ANCRE_Y - 1 - dy
    cy = bas + 1 - ry
    cx = ANCRE_X + dx
    c0 = int(math.floor(cx))

    # Ombre au sol : elle se resserre quand il saute.
    if ombre_sol > 0:
        lr = max(2.0, 7.5 * K * ombre_sol - dy * 0.35)
        for x in range(W):
            if abs(x + 0.5 - ANCRE_X) <= lr:
                px(x, ANCRE_Y, SOL1)
                if abs(x + 0.5 - ANCRE_X) <= lr - 2:
                    px(x, ANCRE_Y + 1, SOL2)

    # Pieds (derrière le bas du corps).
    pg_dx, pg_dy, pd_dx, pd_dy = pieds
    for (fx, fdy) in ((c0 - round(5 * K) + pg_dx, pg_dy), (c0 + round(5 * K) - PIED + 1 + pd_dx, pd_dy)):
        fy = ANCRE_Y - 1 - dy - fdy
        for j in range(PIED):
            px(fx + j, fy, C_CONTOUR if j in (0, PIED - 1) else C_OMBRE)
        for j in range(1, PIED - 1):
            px(fx + j, fy - 1, C_CONTOUR)

    # Corps : ellipse, cerne d'un pixel, ombre en bas (trame à la frontière), reflet en haut à gauche.
    dedans = set()
    for y in range(H):
        for x in range(W):
            u = (y + 0.5 - cy) / ry
            ox = penche * (-u) * 0.5
            if ((x + 0.5 - cx - ox) / rx) ** 2 + u ** 2 <= 1.0:
                dedans.add((x, y))
    for (x, y) in dedans:
        v = (y + 0.5 - cy) / ry
        c = C_BASE
        if v > 0.42 or (v > 0.22 and (x + y) % 2 == 0):
            c = C_OMBRE
        bord = any((x + a, y + b) not in dedans for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        px(x, y, C_CONTOUR if bord else c)
    hx, hy = cx - rx * 0.48, cy - ry * 0.52
    for (x, y) in dedans:
        if ((x + 0.5 - hx) / (2.2 * K)) ** 2 + ((y + 0.5 - hy) / (1.2 * K)) ** 2 <= 1 and g[y][x] != C_CONTOUR:
            px(x, y, C_CLAIR)
    bx, by = int(hx - K), int(hy + 1)
    if (bx, by) in dedans and g[by][bx] != C_CONTOUR:
        px(bx, by, BLANC)

    # Visage.
    ey = int(round(cy - ry * 0.34)) + regard_y
    gauche, droite = YEUX_MIROIR.get(yeux, (yeux, yeux))
    for nom, ex in ((gauche, c0 - GAP // 2 - EW + regard), (droite, c0 + GAP // 2 + regard)):
        motif = YEUX.get(nom, YEUX["repos"])
        oy = ey - (1 if nom == "grands" else 0)
        for yy, ligne in enumerate(motif):
            for xx, ch in enumerate(ligne):
                if ch == "#":
                    px(ex + xx, oy + yy, ENCRE)
                elif ch == "w":
                    px(ex + xx, oy + yy, BLANC)
    my = ey + 5
    mx = c0 + regard
    if bouche == "sourire":
        px(mx - 2, my, ENCRE)
        px(mx + 1, my, ENCRE)
        px(mx - 1, my + 1, ENCRE)
        px(mx, my + 1, ENCRE)
    elif bouche == "coin":                       # malice : un sourire en coin
        px(mx - 1, my + 1, ENCRE)
        px(mx, my + 1, ENCRE)
        px(mx + 1, my, ENCRE)
        px(mx + 2, my - 1, ENCRE)
    elif bouche == "plat":                       # décidé, fatigué
        for xx in range(-1, 1):
            px(mx + xx, my + 1, ENCRE)
        px(mx - 2, my + 1, ENCRE)
        px(mx + 1, my + 1, ENCRE)
    elif bouche == "ouverte":
        for xx in range(6):
            px(mx - 3 + xx, my, ENCRE)
        for xx in range(1, 5):
            px(mx - 3 + xx, my + 1, ENCRE if xx in (1, 4) else LANGUE)
        for xx in range(2, 4):
            px(mx - 3 + xx, my + 2, ENCRE)
    elif bouche == "o":
        for (a, b) in ((-1, 0), (0, 0), (-1, 1), (0, 1), (-1, 2), (0, 2)):
            px(mx + a, my + b, ENCRE)
    elif bouche == "vague":
        for j, a in enumerate((-2, -1, 0, 1, 2)):
            px(mx + a, my + (1 if j % 2 == 0 else 0), ENCRE)
    elif bouche == "triste":
        px(mx - 2, my + 1, ENCRE)
        px(mx - 1, my, ENCRE)
        px(mx, my, ENCRE)
        px(mx + 1, my + 1, ENCRE)
    if joues:
        lx = c0 - GAP // 2 - EW
        rxj = c0 + GAP // 2 + EW - 1
        for j in range(2):
            px(lx - 1 + j, my - 1, JOUE)
            px(rxj + 1 - j, my - 1, JOUE)

    # Antenne et étincelle : la tige s'incline, l'étincelle au bout (cinq branches, éclat quand il est content).
    top = int(round(cy - ry))
    pts = [(c0 + int(round(antenne * j / ANT)), top - j) for j in range(1, ANT + 1)]
    for (x, y) in pts[:-1]:
        px(x, y, C_CONTOUR)
    ex, ey2 = pts[-1][0], pts[-1][1] - 1
    if coeur:
        for (a, b) in ((-1, -1), (1, -1), (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (-1, 1), (0, 1), (1, 1), (0, 2)):
            px(ex + a, ey2 + b, COEUR)
        px(ex - 1, ey2 - 1, ETIN_C)
    else:
        px(ex, ey2, ETIN_C if etincelle % 2 == 0 else BLANC)
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            px(ex + a, ey2 + b, ETIN)
        for a, b in ((2, 0), (-2, 0), (0, -2)):
            px(ex + a, ey2 + b, ETIN_F)
        if etincelle >= 2:
            for a, b in ((3, 0), (-3, 0), (0, -3)):
                px(ex + a, ey2 + b, ETIN_C)
        if etincelle == 3:
            for a, b in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
                px(ex + a, ey2 + b, ETIN_F)

    if sueur:
        sx0, sy0 = c0 + GAP // 2 + EW + 2, ey - 2
        for (a, b, c) in ((0, 0, SUEUR), (0, 1, SUEUR), (-1, 2, SUEUR), (1, 2, SUEUR), (0, 2, BLANC), (0, 3, SUEUR)):
            px(sx0 + a, sy0 + b, c)
    return g


# Visage de repos selon l'humeur du message (comme le grand portrait) : yeux, bouche, joues, extra.
VISAGES = {
    "neutre": dict(),
    "joie": dict(yeux="joie", bouche="ouverte", joues=True),
    "peur": dict(yeux="grands", bouche="vague", sueur=True),
    "triste": dict(yeux="triste", bouche="triste", antenne=-1),
    "surpris": dict(yeux="grands", bouche="o"),
    "determine": dict(yeux="determine", bouche="plat"),
    "fatigue": dict(yeux="fatigue", bouche="plat", antenne=-2),
    "tendre": dict(yeux="joie", joues=True, coeur=True),
    "colere": dict(yeux="colere", bouche="plat"),
    "malice": dict(yeux="malice", bouche="coin"),
}


def anims():
    """Les animations nommées : nom -> (images, pas en ms, « boucle » ou « tient »)."""
    A = {}
    respire = [1.0, 1.0, 1.04, 1.04]
    for h, v in VISAGES.items():
        nom = "repos" if h == "neutre" else "repos-" + h
        ims = []
        for i in range(4):
            kw = dict(v)
            kw["sy"] = respire[i]
            kw.setdefault("etincelle", 1 if i == 2 else 0)
            if h == "peur":
                kw["dx"] = 0.5 if i % 2 else -0.5      # il tremble un peu
            ims.append(pilou(**kw))
        A[nom] = (ims, 220 if h != "peur" else 90, "boucle")
    A["cligne"] = ([pilou(yeux="ferme")], 150, "tient")
    M = []
    for i in range(8):
        ph = i / 8 * 2 * math.pi
        haut = abs(math.sin(ph))
        M.append(pilou(sx=1.05 - 0.07 * haut, sy=0.94 + 0.1 * haut, dy=round(haut * 1.4), regard=1,
                       pieds=(round(1.5 * math.cos(ph)), max(0, round(1.6 * math.sin(ph))), round(-1.5 * math.cos(ph)),
                              max(0, round(-1.6 * math.sin(ph)))),
                       antenne=-1 - (1 if haut > 0.6 else 0), penche=1.2, etincelle=1 if i % 4 == 0 else 0))
    A["marche"] = (M, 83, "boucle")
    S = [
        dict(sx=1.12, sy=0.86), dict(sx=1.2, sy=0.78, yeux="joie"),
        dict(sx=0.86, sy=1.18, dy=4, antenne=2, yeux="joie", bouche="ouverte", ombre_sol=0.8),
        dict(sx=0.93, sy=1.08, dy=8, antenne=1, yeux="joie", bouche="ouverte", etincelle=2, ombre_sol=0.6, joues=True),
        dict(dy=9, yeux="joie", bouche="ouverte", etincelle=3, ombre_sol=0.55, joues=True),
        dict(sx=0.95, sy=1.06, dy=7, antenne=-1, yeux="joie", bouche="ouverte", etincelle=2, ombre_sol=0.6, joues=True),
        dict(sx=0.88, sy=1.15, dy=3, antenne=-2, yeux="joie", bouche="ouverte", ombre_sol=0.8),
        dict(sx=1.22, sy=0.76, antenne=-1, yeux="joie", bouche="ouverte", joues=True),
        dict(sx=1.08, sy=0.92, antenne=1, yeux="joie", joues=True),
        dict(sy=1.02, yeux="joie", joues=True),
    ]
    A["joie"] = ([pilou(**d) for d in S], 83, "tient")
    A["peur"] = ([pilou(sx=1.04, sy=0.94, dx=(-0.5 if i % 2 else 0.5), yeux="grands", bouche="vague", sueur=True,
                        antenne=(1, -1)[i % 2]) for i in range(4)], 70, "boucle")
    A["regard-g"] = ([pilou(regard=-1)], 83, "tient")
    A["regard-d"] = ([pilou(regard=1)], 83, "tient")
    A["regard-h"] = ([pilou(regard_y=-1)], 83, "tient")
    B = [
        dict(sx=1.14, sy=0.84, regard=1),
        dict(sx=0.9, sy=1.14, dy=3, regard=1, antenne=-2, bouche="o", ombre_sol=0.7),
        dict(sx=0.96, sy=1.06, dy=6, regard=1, antenne=-1, bouche="o", ombre_sol=0.5),
        dict(dy=7, regard=1, bouche="o", ombre_sol=0.5),
        dict(sx=0.96, sy=1.06, dy=6, regard=1, antenne=1, bouche="o", ombre_sol=0.5),
        dict(sx=0.9, sy=1.14, dy=3, regard=1, antenne=2, bouche="o", ombre_sol=0.7),
        dict(sx=1.18, sy=0.8, regard=1, antenne=1),
        dict(sx=1.05, sy=0.96, regard=1),
    ]
    A["bond"] = ([pilou(**d) for d in B], 83, "tient")
    A["coucou"] = ([pilou(antenne=a, etincelle=1 + (abs(a) == 2), bouche="ouverte", joues=True)
                    for a in (-2, -1, 0, 1, 2, 1, 0, -1)], 100, "tient")
    A["parle"] = ([pilou(bouche="ouverte"), pilou(), pilou(bouche="o"), pilou()], 110, "boucle")
    A["pense"] = ([pilou(regard_y=-1, regard=1, etincelle=e) for e in (0, 1, 2, 1)], 200, "boucle")
    A["surpris"] = ([pilou(sx=0.9, sy=1.12, dy=2, yeux="grands", bouche="o", antenne=2, etincelle=3, ombre_sol=0.8),
                     pilou(sy=1.04, dy=1, yeux="grands", bouche="o", antenne=1, etincelle=2),
                     pilou(yeux="grands", bouche="o")], 110, "tient")
    return A


ORDRE = ["repos"] + ["repos-" + h for h in VISAGES if h != "neutre"] + [
    "cligne", "marche", "joie", "peur", "regard-g", "regard-d", "regard-h", "bond", "coucou", "parle", "pense", "surpris"]


def planche():
    """(images à plat, table nom -> (première, nombre, pas, mode)) dans l'ordre ORDRE."""
    A = anims()
    images, table = [], {}
    for nom in ORDRE:
        ims, pas, mode = A[nom]
        table[nom] = (len(images), len(ims), pas, mode)
        images.extend(ims)
    return images, table


def tout():
    """Écrit scene-pilou (dessin fin seulement : appelé aux deux échelles par generer.py, n'écrit qu'en 2)."""
    import toile
    from toile import Toile, ecrire
    if toile.ECHELLE != 2:
        return
    images, _ = planche()
    toiles = []
    for g in images:
        t = Toile(W // 2, H // 2)
        t.e = 2
        t.g = [r[:] for r in g]
        toiles.append(t)
    ecrire(ID, toiles, duree=83, commentaire="Le mini-Pilou de scène (scene_pilou.py, docs/SCENES.md) ; "
           "animations nommées dans assets/scenes/animations.txt")


IDS = [ID]
