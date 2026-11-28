"""Planches de contrôle des personnages en haute définition (Pillow : outil de contrôle, jamais dans le rendu livré).

    py outils/sprites/planches_personnages_hd.py            # tout, dans docs/maquettes/personnages
    py outils/sprites/planches_personnages_hd.py essai      # la planche d'essai seule
    py outils/sprites/planches_personnages_hd.py lison      # un personnage (ou une campagne)

Par personnage : `<campagne>-<id>.png` (toutes ses humeurs, sept images chacune, à la taille d'écran : 2 px par unité,
sans lissage) et `<campagne>-<id>.gif`. `essai.png` : Grumeau, Lison et Brouillon sur le décor d'étude C, sous la
scène actuelle, puis chacun en vis-à-vis avec sa version actuelle à sa taille d'écran (5 px par unité).
"""
import os
import sys

from PIL import Image, ImageDraw

import personnages_hd as P

ICI = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.normpath(os.path.join(ICI, "..", "..", "docs", "maquettes"))
SORTIE = os.path.join(DOCS, "personnages")
FOND, FOND2, TEXTE = (38, 34, 58), (48, 44, 72), (230, 236, 242)


def rgba(c):
    return (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16), 255)


def en_image(f, z=1):
    im = Image.new("RGBA", (f.w, f.h), (0, 0, 0, 0))
    px = im.load()
    for y in range(f.h):
        for x in range(f.w):
            if f.c[y][x] is not None:
                px[x, y] = rgba(f.c[y][x])
    return im.resize((f.w * z, f.h * z), Image.NEAREST) if z != 1 else im


def img(cle, humeur="neutre", paup=0, bouche=0, souffle=0, t=0, z=1):
    return en_image(P.image(cle, P.Etat(humeur, paup, bouche, souffle, t)), z)


def texte(im, x, y, mots, z=2, couleur=TEXTE):
    """Une légende dans la police de Pilou (pas de police système sur les planches)."""
    import police
    return police.poser(im, x, y, mots, z, couleur) if hasattr(police, "poser") else \
        ImageDraw.Draw(im).text((x, y), mots, fill=couleur)


def damier(w, h, pas=16):
    im = Image.new("RGBA", (w, h), FOND + (255,))
    d = ImageDraw.Draw(im)
    for y in range(0, h, pas):
        for x in range(0, w, pas):
            if (x // pas + y // pas) % 2:
                d.rectangle([x, y, x + pas - 1, y + pas - 1], fill=FOND2 + (255,))
    return im


def planche(cle, z=2):
    p = P.PERSOS[cle]
    etats = P.etats_planche()
    w, h = p["w"] * z, p["h"] * z
    marge, titre = 8, 14
    W = marge + len(etats) * (w + marge)
    H = marge + len(p["humeurs"]) * (h + titre + marge)
    im = damier(W, H)
    for j, hum in enumerate(p["humeurs"]):
        y = marge + j * (h + titre + marge)
        texte(im, marge, y, hum)
        for i, (paup, bou, souffle, t) in enumerate(etats):
            im.alpha_composite(img(cle, hum, paup, bou, souffle, t, z), (marge + i * (w + marge), y + titre))
    return im.convert("RGB")


SEQUENCE = [(0, 0, 0, 0)] * 3 + [(0, 0, 1, 1)] * 3 + [(0, 0, 0, 2), (1, 0, 0, 2), (2, 0, 0, 2), (1, 0, 0, 3)] + \
           [(0, 0, 1, 3)] * 2 + [(0, 1, 1, 0), (0, 2, 0, 0), (0, 3, 0, 1), (0, 2, 0, 1), (0, 1, 0, 2), (0, 0, 0, 2),
                                 (0, 2, 1, 3), (0, 3, 1, 3), (0, 1, 1, 0), (0, 0, 0, 0)]


def gif(cle, chemin, z=4, fond=(96, 110, 150)):
    p = P.PERSOS[cle]
    ims = []
    for hum in p["humeurs"]:
        for (paup, bou, souffle, t) in SEQUENCE:
            im = Image.new("RGBA", (p["w"] * z, p["h"] * z), fond + (255,))
            im.alpha_composite(img(cle, hum, paup, bou, souffle, t, z))
            ims.append(im.convert("RGB").quantize(colors=64, dither=Image.Dither.NONE))
    ims[0].save(chemin, save_all=True, append_images=ims[1:], duration=150, loop=0)


ESSAI = (("grande-panne", "grumeau"), ("phare-eteint", "lison"), ("petit-nuage", "brouillon"))


def _actuel(cle):
    import planches
    import rendu
    fins = rendu._dossier("sprites2x")
    im = planches.sprite_image(fins["pied-%s-%s" % cle], 1, 0)
    return im.crop(im.getbbox())


def _pilou():
    import planches
    import rendu
    g = rendu.rendre(rendu.Pose(expr="joie"), rendu.banque(), rendu.teintes(), rendu.tenues(), 2)
    im = planches.grille_image(g, 1)
    return im.crop(im.getbbox())


def _poser(scene, spr, x, sol, z, vol=0):
    """Pose un sprite (un pixel par unité) : x du centre et sol en unités de la scène, z px d'écran par unité."""
    g = spr.resize((spr.width * z, spr.height * z), Image.NEAREST)
    scene.alpha_composite(g, (int(x * z) - g.width // 2, (sol - vol) * z - g.height))


def essai():
    pays = os.path.join(DOCS, "paysages")
    avant = Image.open(os.path.join(pays, "actuel-decor.png")).convert("RGBA")      # 960 × 400, 5 px par unité
    apres = Image.open(os.path.join(pays, "C-decor.png")).convert("RGBA")           # 960 × 480, 2 px par unité
    places = {ESSAI[0]: 166, ESSAI[1]: 130, ESSAI[2]: 92}                            # x en unités actuelles (192)
    for cle in ESSAI:
        _poser(avant, _actuel(cle), places[cle], 79, 5, 10 if cle == ESSAI[2] else 0)
    _poser(avant, _actuel_pilou(), 24, 79, 5)
    sol = 237
    _poser(apres, _pilou(), 60, sol, 2)
    for cle, hum in zip(ESSAI, ("neutre", "malice", "joie")):
        f = P.image(cle, P.Etat(hum))
        _poser(apres, en_image(f), places[cle] * 2.5, sol + 1, 2, P.PERSOS[cle]["vol"])
    # Les vis-à-vis : actuel à 5 px, nouveau à 2 px (taille d'écran), puis le nouveau agrandi deux fois.
    case_w, haut1, haut2 = 320, 210, 400
    bas = damier(960, haut1 + haut2)
    for i, cle in enumerate(ESSAI):
        x0 = i * case_w
        a = _actuel(cle)
        a = a.resize((a.width * 5, a.height * 5), Image.NEAREST)
        n = img(cle, z=2)
        n = n.crop(n.getbbox())
        n4 = img(cle, z=4)
        n4 = n4.crop(n4.getbbox())
        bas.alpha_composite(a, (x0 + 80 - a.width // 2, haut1 - 8 - a.height))
        bas.alpha_composite(n, (x0 + 240 - n.width // 2, haut1 - 8 - n.height))
        bas.alpha_composite(n4, (x0 + (case_w - n4.width) // 2, haut1 + haut2 - 8 - n4.height))
        texte(bas, x0 + 8, 6, "actuel, 5 px")
        texte(bas, x0 + 170, 6, "HD, 2 px")
        texte(bas, x0 + 8, haut1 + 6, "HD agrandi 2 fois")
    im = Image.new("RGB", (960, 400 + 8 + 480 + 8 + haut1 + haut2), FOND)
    im.paste(avant.convert("RGB"), (0, 0))
    im.paste(apres.convert("RGB"), (0, 408))
    im.paste(bas.convert("RGB"), (0, 896))
    return im


def _actuel_pilou():
    import planches
    import rendu
    im = planches.sprite_image(rendu._dossier("sprites2x")["scene-pilou"], 1, 0)
    return im.crop(im.getbbox())


def apercu(chemin, z=6, humeurs=None):
    """Aperçu de travail : les personnages côte à côte, très agrandis."""
    ims = [img(c, (humeurs or {}).get(c, "neutre"), z=z) for c in P.ORDRE]
    W = sum(i.width for i in ims) + 10 * (len(ims) + 1)
    o = Image.new("RGBA", (W, max(i.height for i in ims) + 20), (110, 125, 165, 255))
    x = 10
    for i in ims:
        o.alpha_composite(i, (x, 10))
        x += i.width + 10
    o.convert("RGB").save(chemin)


def main():
    os.makedirs(SORTIE, exist_ok=True)
    quoi = sys.argv[1] if len(sys.argv) > 1 else "tout"
    if quoi == "apercu":
        return apercu(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 6)
    if quoi in ("tout", "essai"):
        essai().save(os.path.join(SORTIE, "essai.png"))
    if quoi == "essai":
        return
    for cle in P.ORDRE:
        if quoi not in ("tout", cle[1], cle[0]):
            continue
        nom = "%s-%s" % cle
        planche(cle).save(os.path.join(SORTIE, nom + ".png"))
        gif(cle, os.path.join(SORTIE, nom + ".gif"))
        print(nom, len(P.image(cle, P.Etat()).couleurs()), "couleurs")


if __name__ == "__main__":
    main()


def revue(cle, chemin, z=6, etats=((0, 0, 0, 0), (1, 0, 1, 1), (0, 3, 0, 2))):
    """Relecture à l'œil : chaque humeur, très agrandie (repos, mi-clos inspiré, bouche ouverte)."""
    p = P.PERSOS[cle]
    w, h = p["w"] * z, p["h"] * z
    o = Image.new("RGBA", (len(p["humeurs"]) * (w + 6) + 6, len(etats) * (h + 6) + 6), (110, 125, 165, 255))
    for i, hum in enumerate(p["humeurs"]):
        for j, (paup, bou, souffle, t) in enumerate(etats):
            o.alpha_composite(img(cle, hum, paup, bou, souffle, t, z), (6 + i * (w + 6), 6 + j * (h + 6)))
    o.convert("RGB").save(chemin)
