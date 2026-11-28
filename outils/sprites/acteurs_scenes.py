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
