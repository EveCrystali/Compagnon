"""Acteurs des scènes (docs/SCENES.md) : les petites bêtes et les effets qui font vivre un décor, dessinés pixel par
pixel à l'échelle du décor fin (192 × 80). Identifiant `acteur-<nom>` ; dessin fin seulement (comme scene-pilou).

Où et comment chacun bouge est décrit dans assets/scenes/<campagne>.txt (comportement et zone), calculé par
theatre.py (référence), Theatre.cs et Theatre.java. Ici, seulement leurs images : chacune boucle sur sa `duree`.
Jamais d'opposition rouge / vert : bêtes orange, prune, crème, sarcelle, bleu.
"""

# (motifs, palette, durée en ms)
ACTEURS = {}


def acteur(nom, duree, palette, *images):
    larg = max(len(l) for im in images for l in im)
    haut = max(len(im) for im in images)
    norm = []
    for im in images:
        im = [l.ljust(larg, ".") for l in im]
        im = ["." * larg] * (haut - len(im)) + im          # alignées par le bas
        norm.append(im)
    ACTEURS["acteur-" + nom] = (norm, dict(palette), duree)


# ---- Bêtes

acteur("libellule", 50, {"b": "#6e3d86", "t": "#a46cc2", "w": "#e2d9ffb4", "o": "#f5d76e"},
       ["w..w....", ".w..w...", "bbbbbbto", "........", "........"],
       ["........", "........", "bbbbbbto", ".w..w...", "w..w...."])

acteur("papillon", 120, {"o": "#f69d50", "c": "#ffe1a0", "k": "#3b2a3e", "d": "#d9803a"},
       ["oo.oo", "ocoko", ".dkd.", "..k.."],
       [".o.o.", ".okc.", ".dkd.", "..k.."],
       ["..k..", "..k..", "..k..", "..k.."],
       [".o.o.", ".okc.", ".dkd.", "..k.."])

acteur("oiseau", 140, {"k": "#4a3a6e"},
       ["k...k", ".k.k.", "..k.."],
       [".....", "kk.kk", "..k.."],
       [".....", ".kkk.", "k.k.k"],
       [".....", "kk.kk", "..k.."])

acteur("abeille", 60, {"y": "#f2bd3c", "k": "#2a2238", "w": "#ffffffb4"},
       [".ww..", "kyky.", "kykyk", "....."],
       ["..w..", "kykyw", "kykyk", "....."])

acteur("graine", 300, {"w": "#fff8e1", "g": "#d9c9a0", "s": "#8a6e4b"},
       ["w.w.w", ".www.", "..g..", "..s.."],
       [".w.w.", "wwwww", "..g..", "..s.."])

acteur("feuille", 160, {"o": "#f2c46b", "d": "#d9803a", "k": "#8a4a1f"},
       [".oo.", "oddo", "..k."],
       ["..o.", ".od.", ".dk."],
       [".oo.", "oddo", ".k.."],
       [".o..", ".do.", ".kd."])

acteur("poisson", 233, {"o": "#f69d50", "c": "#ffc89a", "d": "#d9803a", "e": "#1c2128"},
       ["..oo.", ".ocee", "do...", "....."],
       [".....", "doooe", ".occ.", "....."],
       [".....", "do...", ".ocoe", "..oo."])


# ---- La Grande Panne (l'intérieur de l'ordinateur : néons cyan et orange, plastique beige)

acteur("paquet", 120, {"k": "#1c2128", "c": "#4fd8ff", "w": "#e8fbff", "o": "#f69d50"},
       ["kkkkk", "kcwck", "kwcwk", "kkkkk"],
       ["kkkkk", "kwcwk", "kcwck", "kkkkk"],
       ["kkkkk", "kcwck", "kwcwk", "kkkko"],
       ["kkkkk", "kwcwk", "kcwck", "okkkk"])

acteur("curseur", 400, {"k": "#1c2128", "w": "#ffffff"},
       ["k....", "kk...", "kwk..", "kwwk.", "kwwwk", "kwkk.", "k.k..", "...k."],
       ["k....", "kk...", "kwk..", "kwwk.", "kwwwk", "kwkk.", "k.k..", "...k."])

acteur("ticket", 160, {"w": "#fbf3e4", "g": "#d9c7a3", "o": "#f69d50", "k": "#5a4a40"},
       ["wwww", "wkkw", "wwow", "gggg"],
       [".ww.", "wkkw", "wwow", ".gg."],
       ["..w.", ".wk.", ".wo.", "..g."],
       [".ww.", "wkkw", "wwow", ".gg."])

acteur("bulle-marais", 200, {"c": "#a9c8ee", "w": "#ffffff"},
       [".c.", "cwc", ".c."],
       [".cc.", "cw.c", "c..c", ".cc."],
       ["..c..", ".c.c.", "cw..c", ".c.c.", "..c.."])

acteur("etincelle", 80, {"o": "#f69d50", "c": "#ffc89a", "w": "#fff6cc"},
       ["..o..", ".ccc.", "ocwco", ".ccc.", "..o.."],
       [".....", "..c..", ".cwc.", "..c..", "....."],
       ["o...o", ".c.c.", "..w..", ".c.c.", "o...o"])


# ---- Le phare éteint (la côte : nuit bleue, brume, granit, lanternes orange)

acteur("mouette", 140, {"w": "#e6ecf2", "g": "#adbac7", "d": "#3b4654", "o": "#f2a94e"},
       ["d.......d", ".g.....g.", "..gwwwg..", "...wwwo..", "........."],
       [".........", "dg.....gd", "..gwwwg..", "...wwwo..", "........."],
       [".........", ".........", "..gwwwg..", ".g.wwwog.", "d.......d"],
       [".........", "dg.....gd", "..gwwwg..", "...wwwo..", "........."])

acteur("chat", 260, {"n": "#141a2e", "o": "#f2a94e"},
       [".n..n.....", ".nnnn.....", ".nono.....", ".nnnn.....", "..nnn.....", ".nnnnn....", ".nnnnn.nn.", "nnnnnnnnn."],
       [".n..n.....", ".nnnn.....", ".nono.....", ".nnnn.....", "..nnn.....", ".nnnnn.n..", ".nnnnn.n..", "nnnnnnnn.."],
       [".n..n.....", ".nnnn.....", ".nono.....", ".nnnn.....", "..nnn...n.", ".nnnnn..n.", ".nnnnn.n..", "nnnnnnnn.."],
       [".n..n.....", ".nnnn.....", ".nnnn.....", ".nnnn.....", "..nnn.....", ".nnnnn.n..", ".nnnnn.n..", "nnnnnnnn.."])

acteur("papillon-nuit", 70, {"w": "#ffe8bf", "g": "#d9c9a0"},
       ["w.w", ".g."],
       ["...", "wgw"])

acteur("crabe", 120, {"o": "#d0662e", "c": "#f69d50", "k": "#1c2128"},
       [".k...k.", "oo.o.oo", ".ocooo.", "o.o.o.o"],
       [".k...k.", "oo.o.oo", ".ocooo.", ".o.o.o."])

# ---- Petit Nuage (la montagne, le ciel : nuages, brume, vapeur, neige). Aucune couleur semi-transparente : le
# léger se dit en trame (un pixel sur deux, un sur quatre), comme dans les décors.

def _trame(x, y, densite):
    """Garde-t-on ce pixel ? densite 4 : tous, 2 : un sur deux (damier), 1 : un sur quatre, 0 : aucun."""
    if densite >= 4:
        return True
    if densite >= 2:
        return (x + y) % 2 == 0
    if densite >= 1:
        return x % 2 == 0 and y % 2 == 0
    return False


# Un petit nuage qui passe, dans le style des nuages des décors : corps blanc à bosses, dessous bleuté, et dessous
# encore une frange en damier. Ses bosses bougent un peu d'une image à l'autre (il respire).
acteur("nuage", 520, {"w": "#f7f5ef", "c": "#dbe3f0"},
       ["......wwww..........", "....wwwwwwww..ww....", "..wwwwwwwwwwwwwwww..", ".wwwwwwwwwwwwwwwwww.",
        "wwwwwwwwwwwwwwwwwwww", ".cccccccccccccccccc.", "..c.c.c.c.c.c.c.c..."],
       [".....wwwww..........", "....wwwwwwww.www....", "..wwwwwwwwwwwwwwww..", ".wwwwwwwwwwwwwwwwww.",
        "wwwwwwwwwwwwwwwwwwww", ".cccccccccccccccccc.", "...c.c.c.c.c.c.c.c.."],
       [".....wwwww..........", "...wwwwwwwww.wwww...", "..wwwwwwwwwwwwwwww..", ".wwwwwwwwwwwwwwwwww.",
        "wwwwwwwwwwwwwwwwwwww", ".cccccccccccccccccc.", "..c.c.c.c.c.c.c.c..."],
       ["......wwww..........", "....wwwwwwww..www...", "..wwwwwwwwwwwwwwww..", ".wwwwwwwwwwwwwwwwww.",
        "wwwwwwwwwwwwwwwwwwww", ".cccccccccccccccccc.", "...c.c.c.c.c.c.c.c.."])


def _brume(w, h, decalage):
    """Une traînée de brume : un damier au cœur, un pixel sur quatre au bord ; le motif glisse d'une image à l'autre."""
    lignes = []
    for y in range(h):
        l = ""
        for x in range(w):
            u, v = (x + 0.5 - w / 2) / (w / 2), (y + 0.5 - h / 2) / (h / 2)
            d = u * u + v * v
            dens = 2 if d <= 0.45 else 1 if d <= 1.0 else 0
            l += "b" if _trame(x + decalage, y, dens) else "."
        lignes.append(l)
    return lignes


acteur("brume", 600, {"b": "#e3e9f4"}, _brume(22, 5, 0), _brume(22, 5, 1), _brume(22, 5, 2), _brume(22, 5, 3))


def _vapeur(etape):
    """Un filet de vapeur qui monte : dense en bas au début, puis il s'élargit et s'éclaircit (trame)."""
    w, h = 7, 10
    lignes = []
    for y in range(h):
        l = ""
        for x in range(w):
            ondule = [0, 1, 1, 0, -1, -1, 0, 1, 1, 0][(y + etape) % 10]
            dx = abs(x - 3 - ondule)
            large = 1 + etape // 2
            dens = (2 if dx <= large - 1 else 1 if dx <= large else 0) if y >= 2 * (4 - etape) - 4 else 0
            dens = max(0, dens - (1 if etape >= 3 else 0))
            l += "v" if dens and _trame(x, y + etape, dens + (1 if dens == 1 and etape < 2 else 0)) else "."
        lignes.append(l)
    return lignes


acteur("vapeur", 1000, {"v": "#eef2f8"}, *[_vapeur(e) for e in range(5)])

acteur("flocon", 300, {"w": "#ffffff", "c": "#9fb4d8"},
       [".w.", "wcw", ".w."],
       [".c.", "cwc", ".c."],
       ["w.w", ".w.", "w.w"],
       [".c.", "cwc", ".c."])

acteur("aiguille", 220, {"o": "#e8a03a", "d": "#b8732a"},
       ["oo.", ".do"],
       [".o.", "odo"],
       [".oo", "od."],
       [".o.", "odo"])

acteur("rafale", 90, {"c": "#c9d3e8", "w": "#eef2f8"},
       ["..cc.cw.......", "..............", "......cc.cwww."],
       ["...cc.cw......", "..............", ".......cc.cwww"],
       ["....cc.cw.....", "..............", "c.......cc.cww"],
       [".....cc.cw....", "..............", "cc.......cc.cw"])

acteur("poussiere", 160, {"o": "#ffd98a", "w": "#fff6d6"},
       ["w.", ".."], ["o.", ".."], ["..", ".o"], ["..", ".w"])


# ---- Eau

def _rond(r, a):
    W, H = 15, 5
    lignes = []
    for y in range(H):
        l = ""
        for x in range(W):
            u, v = (x + 0.5 - W / 2) / max(0.5, r), (y + 0.5 - H / 2) / max(0.5, r * 0.3)
            d = u * u + v * v
            l += a if 0.62 <= d <= 1.25 else "."
        lignes.append(l)
    return lignes


acteur("rond", 280, {"c": "#c7d5f4cc", "p": "#c7d5f488"},
       _rond(2, "c"), _rond(3.5, "c"), _rond(5, "c"), _rond(6.5, "p"), _rond(7.5, "p"))

def _rond_trame(r, densite):
    return ["".join(ch if ch == "." or _trame(x, y, densite) else "." for x, ch in enumerate(l))
            for y, l in enumerate(_rond(r, "c"))]


# Le rond sans alpha (Petit Nuage) : opaque, puis en damier, puis un pixel sur quatre en s'élargissant.
acteur("rond-trame", 280, {"c": "#d6e3f4"},
       _rond_trame(2, 4), _rond_trame(3.5, 4), _rond_trame(5, 2), _rond_trame(6.5, 2), _rond_trame(7.5, 1))

acteur("plouf", 90, {"w": "#ffffff", "c": "#cfe0ff", "b": "#9fb8e8"},
       [".........", "....w....", "...c.c...", "..b...b.."],
       ["....w....", "..c...c..", ".c..w..c.", "b.......b"],
       ["..c...c..", ".c.....c.", "c.......c", "........."],
       [".c.....c.", ".........", ".........", "........."])

acteur("bulle", 150, {"c": "#efe0c0", "w": "#ffffff", "o": "#b9a98a"},
       [".cc..", "cwcc.", ".cc.."],
       [".ccc.", "cwccc", "ccccc", ".ccc."],
       ["..ccc..", ".cwcccc", "ccccccc", "ccccccc", ".ccccc."],
       [".ccc.", "cwccc", "ccccc", ".ccc."])

# ---- Effets de réaction (posés par le théâtre, une fois)

acteur("eclats", 70, {"o": "#f69d50", "c": "#ffc89a", "w": "#fff6cc"},
       [".............", ".............", ".............", ".............", ".....c.c.....", "......w......",
        ".....c.c.....", ".............", ".............", ".............", "............."],
       [".............", ".............", "......o......", ".............", "..o..c.c..o..", "......w......",
        "..o..c.c..o..", ".............", "......o......", ".............", "............."],
       ["......o......", ".............", "..c.......c..", ".............", ".............", "o...........o",
        ".............", ".............", "..c.......c..", ".............", "......o......"],
       ["......c......", "..o.......o..", ".............", ".............", ".............", "c...........c",
        ".............", ".............", ".............", "..o.......o..", "......c......"],
       [".............", "..c.......c..", ".............", ".............", ".............", ".............",
        ".............", ".............", ".............", "..c.......c..", "............."])

acteur("note", 180, {"k": "#3d2f63", "c": "#efe0c0"},
       ["..kk", "..kc", "..k.", "kkk.", "kkk."],
       ["..kk", "..k.", "..kc", "kkk.", "kkk."])


def tout():
    """Écrit les acteurs (dessin fin seulement)."""
    import toile
    from toile import Toile, ecrire
    if toile.ECHELLE != 2:
        return
    for sid, (images, pal, duree) in ACTEURS.items():
        h, w = len(images[0]), len(images[0][0])
        assert w % 2 == 0 or True
        toiles = []
        for im in images:
            t = Toile((w + 1) // 2, (h + 1) // 2)
            t.e = 2
            t.g = [[None] * ((w + 1) // 2 * 2) for _ in range((h + 1) // 2 * 2)]
            dy = len(t.g) - h                                      # aligné en bas, à gauche
            for y, l in enumerate(im):
                for x, ch in enumerate(l):
                    if ch != ".":
                        t.g[y + dy][x] = pal[ch]
            toiles.append(t)
        ecrire(sid, toiles, duree=duree, commentaire="Acteur de scène (acteurs_scenes.py, docs/SCENES.md)")


IDS = sorted(ACTEURS)
