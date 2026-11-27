"""Visage de Pilou : humeurs des campagnes (docs/CAMPAGNES.md) et dessin fin (2×) de tout le visage.

Appelé par generer.py. Un œil tient dans une boîte de 6 × 7 pixels de la grille 1× (12 × 14 en fin) posée par le
rendu ; un sourcil peut dépasser au-dessus (le point du sprite donne alors le coin de la boîte). L'œil dessiné
est celui de gauche à l'écran : le droit est son miroir, sauf si « oeil-<nom>-d » existe (regard dissymétrique).
Une bouche est centrée sur l'axe de Pilou. « marque-<humeur> » : larme, goutte, signe de colère, posés sur
l'ancre des yeux. Aucune opposition rouge / vert : chaque humeur se lit d'abord à sa forme.
"""
import toile
from toile import Toile, ecrire

ENCRE = "#1c2128"
BLANC = "#ffffff"
BOUCHE = "#3a2a2f"
LANGUE = "#f69d50"
LANGUE_C = "#ffc89a"
IRIS = "#34496e"        # reflet bas de l'œil (dessin fin seulement)
GOUTTE, GOUTTE_C = "#1f4f8a", "#b4dbff"
COLERE, COLERE_C = "#8a4a1f", "#f69d50"

PAL = {"k": ENCRE, "w": BLANC, "o": "@ombre", "c": "@contour", "i": IRIS, "m": BOUCHE, "t": LANGUE, "h": LANGUE_C,
       "g": GOUTTE, "b": GOUTTE_C, "r": COLERE, "s": COLERE_C}

# ---- Yeux des humeurs, grille 1× : nom -> (lignes, lignes de sourcil au-dessus de la boîte).
YEUX = {
    "peur": (["....kk", "..kk..", ".kkkk.", "kwwwwk", "kwwkwk", "kwwkwk", "kwwwwk", ".kkkk."], 2),
    "triste": (["....kk", "..kkk.", "kk....", "......", ".kkkk.", "kwwkkk", "kkkkkk", ".kkkk.", "......"], 2),
    "surpris": ([".kkkk.", "k....k", "......", ".kkkk.", "kwwwwk", "kwkkwk", "kwkkwk", "kwwwwk", ".kkkk."], 3),
    "determine": (["kk....", ".kkkk.", "...kkk", "kkkkkk", "kwwkkk", "kkkkkk", "kkkkkk", ".kkkk."], 2),
    "tendre": (["......", ".oooo.", "cccccc", "kwwkkk", "kwwkwk", "kkkkkk", ".kkkk."], 0),
    "colere": (["kk....", "kkkk..", "..kkkk", "....kk", ".kkkkk", "kwwkkk", "kkkkkk", ".kkkk."], 2),
    "malice": ([".kkkk.", "k....k", "......", "......", "cccccc", "kkkkkk", "kkkwwk", ".kkkk.", "......"], 2),
    # Œil droit de la malice (posé tel quel) : sourcil bas, froncé vers le nez.
    "malice-d": (["...kkk", "kkk...", "cccccc", "kkkkkk", "kkkwwk", ".kkkk.", "......"], 0),
}

BOUCHES = {
    "neutre": ["kkkkkk"],
    "joie": ["kkkkkkkkkk", "kwwwwwwwwk", "kmmmmmmmmk", ".kmttttmk.", "..kkkkkk.."],
    "peur": [".kk..kk.", "k..kk..k"],
    "triste": [".kkkk.", "k....k"],
    "surpris": [".kk.", "kmmk", "kmmk", "kmmk", ".kk."],
    "determine": [".....k", "kkkkk."],
    "fatigue": ["kkk...", "...kkk"],
    "tendre": ["k..k", ".kk."],
    "colere": [".kkkkkk.", "kwkwkwwk", ".kkkkkk."],
    "malice": ["......kk", "k...kk..", ".kkk...."],
}

# ---- Marques, grille 1× : (images, point = pixel posé sur l'ancre des yeux, durée).
MARQUES = {
    # Larme qui glisse sous l'œil gauche.
    "triste": ([["g", "b", "g"], [".", "g", "b", "g"], [".", ".", "g", "b", "g"]], (9, -7), 420),
    # Goutte de sueur sur la tempe droite.
    "peur": ([[".g.", "gbg", "gbg", ".g."], ["...", ".g.", "gbg", "gbg", ".g."]], (-11, 4), 380),
    # Signe de colère (quatre coins), en haut à droite du front ; il bat.
    "colere": ([["rr.rr", "r...r", ".....", "r...r", "rr.rr"], [".....", ".r.r.", ".....", ".r.r.", "....."]], (-10, 7), 300),
}


def _hauteur(images):
    return max(len(im) for im in images)


def humeurs():
    """Sprites 1× des humeurs de campagne (les humeurs d'origine restent dans generer.visage)."""
    for nom, (lignes, sourcil) in YEUX.items():
        t = Toile(6, len(lignes))
        t.motif(0, 0, lignes, PAL)
        ecrire("oeil-" + nom, t, slot="visage", point=(0, sourcil), commentaire="œil d'humeur (campagnes)")
    for nom, lignes in BOUCHES.items():
        t = Toile(len(lignes[0]), len(lignes))
        t.motif(0, 0, lignes, PAL)
        ecrire("bouche-" + nom, t, slot="visage", commentaire="bouche d'humeur (campagnes), centrée sur l'axe de Pilou")
    for nom, (images, point, duree) in MARQUES.items():
        w, h = max(len(l) for im in images for l in im), _hauteur(images)
        toiles = []
        for im in images:
            t = Toile(w, h)
            t.motif(0, 0, im, PAL)
            toiles.append(t)
        ecrire("marque-" + nom, toiles, slot="visage", ancre="yeux", point=point, duree=duree,
               commentaire="marque d'humeur (campagnes), posée sur l'ancre des yeux")


# =====================================================================================================
# Dessin fin (2×) : chaque motif est écrit en pixels fins.
# =====================================================================================================
YEUX_FINS = {
    "ouvert": ([
        "....kkkk....",
        "..kkkkkkkk..",
        ".kkwwwkkkkk.",
        ".kwwwwwkkkk.",
        "kkwwwwwkkkkk",
        "kkwwwwwkkkkk",
        "kkkwwwkkkkkk",
        "kkkkkkkkkkkk",
        "kkkkkkkkwwkk",
        "kkkkkkkkwwkk",
        ".kkiikkkkkk.",
        ".kkkiiiikkk.",
        "..kkkkkkkk..",
        "....kkkk....",
    ], 0),
    "cligne": ([
        "............",
        "............",
        "............",
        "............",
        "............",
        "............",
        "kk........kk",
        "kkk......kkk",
        ".kkkk..kkkk.",
        "..kkkkkkkk..",
        "....kkkk....",
        "............",
        "............",
        "............",
    ], 0),
    "dort": ([
        "............",
        "............",
        "............",
        "............",
        "............",
        "............",
        "............",
        "............",
        "kk........kk",
        "kkkk....kkkk",
        "..kkkkkkkk..",
        "....kkkk....",
        "............",
        "............",
    ], 0),
    "fatigue": ([
        "...oooooo...",
        ".oooooooooo.",
        "oooooooooooo",
        "oooooooooooo",
        "cccccccccccc",
        "cccccccccccc",
        "kkwwwwkkkkkk",
        "kkwwwwkkkkkk",
        "kkkwwkkkkkkk",
        "kkkkkkkkkkkk",
        "kkkkkkkkkkkk",
        ".kkkiiiikkk.",
        "..kkkkkkkk..",
        "....kkkk....",
    ], 0),
    "concentre": ([
        "............",
        "............",
        ".oooooooooo.",
        "oooooooooooo",
        "cccccccccccc",
        "cccccccccccc",
        "kkwwwwkkkkkk",
        "kkwwwwkkkkkk",
        "kkkwwkkkkkkk",
        ".kkkkkkkkkk.",
        "..kkkkkkkk..",
        "....kkkk....",
        "............",
        "............",
    ], 0),
    "haut": ([
        "....kkkk....",
        "..kkkkkkkk..",
        ".kkkwwwwkkk.",
        "kkkwwwwwwkkk",
        "kkkwwwwwwkkk",
        "kkkkwwwwkkkk",
        "kkkkkkkkkkkk",
        "kkkkkkkkkkkk",
        ".kkkkkkkkkk.",
        "...kkkkkk...",
        "............",
        "............",
        "............",
        "............",
    ], 0),
    "grimace": ([
        "kk..........",
        "kkkk........",
        ".kkkkk......",
        "...kkkkk....",
        ".....kkkkk..",
        ".......kkkkk",
        ".........kkk",
        ".........kkk",
        ".......kkkkk",
        ".....kkkkk..",
        "...kkkkk....",
        ".kkkkk......",
        "kkkk........",
        "kk..........",
    ], 0),
    "heureux": ([
        "............",
        "............",
        "....kkkk....",
        "..kkkkkkkk..",
        ".kkkk..kkkk.",
        "kkk......kkk",
        "kkk......kkk",
        "kk........kk",
        "kk........kk",
        "kk........kk",
        "............",
        "............",
        "............",
        "............",
    ], 0),
    "content": ([
        "............",
        "............",
        "............",
        "............",
        "kk........kk",
        "kk........kk",
        "kkk......kkk",
        "kkk......kkk",
        ".kkkk..kkkk.",
        "..kkkkkkkk..",
        "....kkkk....",
        "............",
        "............",
        "............",
    ], 0),
    "inquiet": ([
        "....kkkk....",
        "..kkkkkkkk..",
        ".kkwwwwwwkk.",
        ".kwwwwwwwwk.",
        "kkwwwkkwwwkk",
        "kkwwkkkkwwkk",
        "kkwwkkkkwwkk",
        "kkwwwkkwwwkk",
        ".kwwwwwwwwk.",
        ".kkwwwwwwkk.",
        "..kkkkkkkk..",
        "....kkkk....",
        "............",
        "............",
    ], 0),
    "spirale": ([
        ".kkkkkkkk...",
        "kkkkkkkkkk..",
        "kk......kk..",
        "kk......kk..",
        "kk..kk..kk..",
        "kk..kk..kk..",
        "kk..kkkkkk..",
        "kk...kkkk...",
        "kk..........",
        "kk..........",
        "kkkkkkkkkkkk",
        ".kkkkkkkkkkk",
        "............",
        "............",
    ], 0),
    "boude": ([
        "kkk.........",
        "kkkkk.......",
        "..kkkkk.....",
        "....kkkkk...",
        "......kkkkkk",
        "........kkkk",
        ".oooooooooo.",
        "oooooooooooo",
        "cccccccccccc",
        "cccccccccccc",
        "kkkkwwwwkkkk",
        "kkkkkwwkkkkk",
        ".kkkkkkkkkk.",
        "...kkkkkk...",
    ], 0),
    "serein": ([
        "............",
        "............",
        "............",
        "............",
        ".cccccccccc.",
        "cccccccccccc",
        "kkkkkkkkkkkk",
        "kkwwwwkkkkkk",
        "kkwwwwkkkkkk",
        ".kkwwkkkkkk.",
        "..kkkkkkkk..",
        "....kkkk....",
        "............",
        "............",
    ], 0),
    # ---- humeurs de campagne
    "peur": ([
        ".........kkk",
        "......kkkkk.",
        "...kkkkk....",
        "..kkk.......",
        "....kkkk....",
        "..kkkkkkkk..",
        ".kkwwwwwwkk.",
        ".kwwwwwwwwk.",
        "kkwwwwwwwwkk",
        "kkwwwwkkwwkk",
        "kkwwwwkkwwkk",
        "kkwwwwwwwwkk",
        "kkwwwwwwwwkk",
        ".kwwwwwwwwk.",
        ".kkkwwwwkkk.",
        "...kkkkkk...",
    ], 2),
    "triste": ([
        ".........kkk",
        ".......kkkkk",
        "....kkkkkk..",
        ".kkkkkk.....",
        "kkk.........",
        "............",
        "............",
        "............",
        "....kkkk....",
        "..kkkkkkkk..",
        ".kkwwwwkkkk.",
        "kkwwwwwwkkkk",
        "kkwwwwwwkkkk",
        "kkkwwwwkkwkk",
        "kkkkkkkkkkkk",
        ".kkiiiikkkk.",
        "..kkkkkkkk..",
        "....kkkk....",
    ], 2),
    "surpris": ([
        "...kkkkkk...",
        ".kkkkkkkkkk.",
        "kkk......kkk",
        "kk........kk",
        "............",
        "............",
        "....kkkk....",
        "..kkkkkkkk..",
        ".kkwwwwwwkk.",
        ".kwwwwwwwwk.",
        "kkwwwkkwwwkk",
        "kkwwkkkkwwkk",
        "kkwwkwkkwwkk",
        "kkwwwkkwwwkk",
        ".kwwwwwwwwk.",
        ".kkwwwwwwkk.",
        "..kkkkkkkk..",
        "....kkkk....",
    ], 3),
    "determine": ([
        "kkk.........",
        "kkkkkk......",
        "..kkkkkkk...",
        ".....kkkkkk.",
        "........kkkk",
        "..........kk",
        "kkkkkkkkkkkk",
        "kkkwwwkkkkkk",
        "kkwwwwwkkkkk",
        "kkwwwwwkkkkk",
        "kkkwwwkkkkkk",
        "kkkkkkkkwwkk",
        "kkkkkkkkkkkk",
        ".kkkiiiikkk.",
        "..kkkkkkkk..",
        "....kkkk....",
    ], 2),
    "tendre": ([
        "............",
        "............",
        "...oooooo...",
        ".oooooooooo.",
        "cccccccccccc",
        "kkkkkkkkkkkk",
        "kkwwwwkkkkkk",
        "kwwwwwwkkkkk",
        "kwwwwwwkwwkk",
        "kkwwwwkkwwkk",
        "kkkkkkkkkkkk",
        ".kkiiiiikkk.",
        "..kkkkkkkk..",
        "....kkkk....",
    ], 0),
    "colere": ([
        "kkk.........",
        "kkkkkk......",
        "kkkkkkkk....",
        "...kkkkkkk..",
        ".....kkkkkkk",
        ".......kkkkk",
        ".........kkk",
        "............",
        "..kkkkkkkkkk",
        ".kkwwwkkkkkk",
        "kkwwwwwkkkkk",
        "kkkwwwkkkkkk",
        "kkkkkkkkkkkk",
        ".kkkkkkkkkk.",
        "..kkkkkkkk..",
        "....kkkk....",
    ], 2),
    "malice": ([
        "...kkkkkk...",
        ".kkkkkkkkkk.",
        "kkk......kkk",
        "kk........kk",
        "............",
        "............",
        "............",
        "............",
        ".cccccccccc.",
        "cccccccccccc",
        "kkkkkkkkkkkk",
        "kkkkkkwwwwkk",
        "kkkkkkwwwwkk",
        ".kkkkkkwwkk.",
        "..kkkkkkkk..",
        "....kkkk....",
        "............",
        "............",
    ], 2),
    "malice-d": ([
        "......kkkkkk",
        "...kkkkkkkk.",
        "kkkkkkk.....",
        "kkkk........",
        ".cccccccccc.",
        "cccccccccccc",
        "kkkkkkkkkkkk",
        "kkkkkkwwwwkk",
        "kkkkkkwwwwkk",
        ".kkkkkkwwkk.",
        "..kkkkkkkk..",
        "....kkkk....",
        "............",
        "............",
    ], 0),
}

# Œil immense de la Gouttelette (stade 1) : 16 × 18.
OEIL_GOUTTELETTE = [
    ".....kkkkkk.....",
    "...kkkkkkkkkk...",
    "..kkkwwwwkkkkk..",
    ".kkwwwwwwwkkkkk.",
    ".kwwwwwwwwkkkkk.",
    "kkwwwwwwwkkkkkkk",
    "kkwwwwwwwkkkkkkk",
    "kkkwwwwwkkkkkkkk",
    "kkkkkkkkkkkkkkkk",
    "kkkkkkkkkkkkkkkk",
    "kkkkkkkkkkkkwkkk",
    "kkkkkkkkkkkwwwkk",
    "kkkkkkkkkkwwwwkk",
    ".kkiikkkkkkwwkk.",
    ".kkkiiikkkkkkkk.",
    "..kkkiiiiikkkk..",
    "...kkkkkkkkkk...",
    ".....kkkkkk.....",
]

BOUCHES_FINES = {
    "repos": [
        "kk............kk",
        "kkk..........kkk",
        ".kkk........kkk.",
        "..kkkk....kkkk..",
        "...kkkkkkkkkk...",
        ".....kkkkkk.....",
    ],
    "soulage": [
        "kk........kk",
        "kkk......kkk",
        ".kkkkkkkkkk.",
        "...kkkkkk...",
    ],
    "concentre": [
        ".kkkkkk.",
        ".kkkkkk.",
    ],
    "attente": [
        "..kkkk..",
        ".kk..kk.",
        "kk....kk",
        "kk....kk",
        ".kk..kk.",
        "..kkkk..",
    ],
    "dort": [
        "..kkkk..",
        ".kk..kk.",
        "kk....kk",
        "kk....kk",
        ".kk..kk.",
        "..kkkk..",
    ],
    "grimace": [
        "kk..kk..kk..kk..kk..",
        "kkkkkkkkkkkkkkkkkkkk",
        "kkkkkkkkkkkkkkkkkkkk",
        "..kk..kk..kk..kk..kk",
    ],
    "fete": [
        "kkkkkkkkkkkkkkkk",
        "kkmmmmmmmmmmmmkk",
        "kkmmmmmmmmmmmmkk",
        "kkmmmmmmmmmmmmkk",
        "kkmmtttttttttmkk",
        ".kkmthhhhttttkk.",
        ".kkkttttttttkkk.",
        "..kkkttttttkkk..",
        "...kkkkkkkkkk...",
        ".....kkkkkk.....",
    ],
    "inquiet": [
        ".....kkkkkk.....",
        "...kkkkkkkkkk...",
        "..kkkk....kkkk..",
        ".kkk........kkk.",
        "kkk..........kkk",
        "kk............kk",
    ],
    "caresse": [
        "kk....kkkk....kk",
        "kkk..kkkkkk..kkk",
        ".kkkkkk..kkkkkk.",
        "..kkkk....kkkk..",
    ],
    "baille": [
        "...kkkkkk...",
        ".kkkkkkkkkk.",
        ".kkmmmmmmkk.",
        "kkmmmmmmmmkk",
        "kkmmmmmmmmkk",
        "kkmmmmmmmmkk",
        "kkmmmttmmmkk",
        "kkmmtttttmkk",
        "kkmthhtttmkk",
        ".kkttttttkk.",
        ".kkkkkkkkkk.",
        "...kkkkkk...",
    ],
    "boude": [
        "....kkkk....",
        "..kkkkkkkk..",
        ".kkk....kkk.",
        "kkk......kkk",
        "kk........kk",
        "kk........kk",
    ],
    # ---- humeurs de campagne
    "neutre": [
        ".kkkkkkkkkk.",
        ".kkkkkkkkkk.",
    ],
    "joie": [
        "kkkkkkkkkkkkkkkkkkkk",
        "kkwwwwwwwwwwwwwwwwkk",
        "kkwwwwwwwwwwwwwwwwkk",
        "kkmmmmmmmmmmmmmmmmkk",
        ".kkmmmmmmmmmmmmmmkk.",
        ".kkmmmmtttttttmmmkk.",
        "..kkmmtthhhttttmkk..",
        "...kkkttttttttkkk...",
        "....kkkkkkkkkkkk....",
        "......kkkkkkkk......",
    ],
    "peur": [
        "..kkk......kkk..",
        ".kkkkk....kkkkk.",
        "kk..kkk..kkk..kk",
        "k....kkkkkk....k",
    ],
    "triste": [
        "...kkkkkk...",
        ".kkkkkkkkkk.",
        "kkk......kkk",
        "kk........kk",
    ],
    "surpris": [
        "..kkkk..",
        ".kkkkkk.",
        "kkmmmmkk",
        "kkmmmmkk",
        "kkmmmmkk",
        "kkmmmmkk",
        "kkmmmmkk",
        "kkmmmmkk",
        ".kkkkkk.",
        "..kkkk..",
    ],
    "determine": [
        "..........kk",
        ".........kkk",
        "kkkkkkkkkkk.",
        "kkkkkkkkk...",
    ],
    "fatigue": [
        "kkkkk.......",
        "kkkkkkk.....",
        ".....kkkkkkk",
        ".......kkkkk",
    ],
    "tendre": [
        "kk....kk",
        "kkk..kkk",
        ".kkkkkk.",
        "..kkkk..",
    ],
    "colere": [
        "..kkkkkkkkkkkk..",
        ".kkkkkkkkkkkkkk.",
        "kkwwkwwkwwkwwwkk",
        "kkwwkwwkwwkwwwkk",
        ".kkkkkkkkkkkkkk.",
        "..kkkkkkkkkkkk..",
    ],
    "malice": [
        "............kkk.",
        "..........kkkkk.",
        "kk......kkkkk...",
        "kkk..kkkkkk.....",
        ".kkkkkkkk.......",
        "..kkkkk.........",
    ],
}

MARQUES_FINES = {
    "triste": [
        ["..gg..", ".gbbg.", ".gbbg.", "gbwbbg", "gbbbbg", ".gggg.", "......", "......", "......", "......"],
        ["......", "......", "..gg..", ".gbbg.", ".gbbg.", "gbwbbg", "gbbbbg", ".gggg.", "......", "......"],
        ["......", "......", "......", "......", "..gg..", ".gbbg.", ".gbbg.", "gbwbbg", "gbbbbg", ".gggg."],
    ],
    "peur": [
        ["..gg..", ".gbbg.", ".gbbg.", "gbwbbg", "gbwbbg", "gbbbbg", ".gggg.", "......", "......", "......"],
        ["......", "......", "..gg..", ".gbbg.", ".gbbg.", "gbwbbg", "gbwbbg", "gbbbbg", ".gggg.", "......"],
    ],
    "colere": [
        ["rrrr..rrrr", "rssr..rssr", "rsr....rsr", "rrr....rrr", "..........", "..........", "rrr....rrr", "rsr....rsr",
         "rssr..rssr", "rrrr..rrrr"],
        ["..........", "..........", "..rr..rr..", "..rr..rr..", "..........", "..........", "..rr..rr..", "..rr..rr..",
         "..........", ".........."],
    ],
}


def fins():
    """Tout le visage, dessiné en pixels fins (assets/sprites2x)."""
    for nom, (lignes, sourcil) in YEUX_FINS.items():
        assert all(len(l) == 12 for l in lignes) and len(lignes) % 2 == 0, nom
        t = Toile(6, len(lignes) // 2)
        t.motif_fin(0, 0, lignes, PAL)
        ecrire("oeil-" + nom, t, slot="visage", point=(0, sourcil), commentaire="œil gauche, dessin fin (le droit est son miroir)")
    assert all(len(l) == 16 for l in OEIL_GOUTTELETTE) and len(OEIL_GOUTTELETTE) == 18
    t = Toile(8, 9)
    t.motif_fin(0, 0, OEIL_GOUTTELETTE, PAL)
    ecrire("oeil-ouvert-g", t, slot="visage", commentaire="œil immense de la Gouttelette (stade 1), dessin fin")
    for nom, lignes in BOUCHES_FINES.items():
        w = len(lignes[0])
        assert all(len(l) == w for l in lignes) and w % 2 == 0 and len(lignes) % 2 == 0, nom
        t = Toile(w // 2, len(lignes) // 2)
        t.motif_fin(0, 0, lignes, PAL)
        ecrire("bouche-" + nom, t, slot="visage", commentaire="bouche, dessin fin, centrée sur l'axe de Pilou")
    for nom, images in MARQUES_FINES.items():
        _, point, duree = MARQUES[nom]
        w, h = len(images[0][0]), len(images[0])
        toiles = []
        for im in images:
            assert all(len(l) == w for l in im) and len(im) == h, nom
            t = Toile(w // 2, h // 2)
            t.motif_fin(0, 0, im, PAL)
            toiles.append(t)
        ecrire("marque-" + nom, toiles, slot="visage", ancre="yeux", point=point, duree=duree,
               commentaire="marque d'humeur, dessin fin")
