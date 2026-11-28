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


def _boite(cle):
    im = img(cle)
    return im, im.getbbox()


def groupe(campagne, z=2):
    """La planche de groupe : toute la campagne à l'échelle, rangée par taille, Pilou fin pour repère, une toise
    tous les 20 unités ; trois fonds (sombre, clair, décor d'étude) pour vérifier que chacun s'y détache."""
    cles = [c for c in P.ORDRE if c[0] == campagne]
    cles.sort(key=lambda c: -(_boite(c)[1][3] - _boite(c)[1][1] + P.PERSOS[c]["vol"]))
    pilou = _pilou()
    sprites = [(pilou, 0)] + [(_boite(c)[0].crop(_boite(c)[1]), P.PERSOS[c]["vol"]) for c in cles]
    esp, marge, haut = 8, 30, 132
    W = marge + sum(s.width + esp for s, _ in sprites) + 8
    fonds = [(28, 30, 46), (232, 226, 208)]
    decor = Image.open(os.path.join(DOCS, "paysages", "C-decor-1x.png")).convert("RGBA")
    bandes = []
    for k in range(3):
        if k < 2:
            b = Image.new("RGBA", (W, haut), fonds[k] + (255,))
            sol = haut - 10
            ImageDraw.Draw(b).rectangle([0, sol, W, haut], fill=tuple(int(v * 0.8) for v in fonds[k]) + (255,))
        else:
            b = Image.new("RGBA", (W, 240), (0, 0, 0, 255))
            for x in range(0, W, decor.width):
                b.alpha_composite(decor, (x, 0))
            sol = 237
        d = ImageDraw.Draw(b)
        if k < 2:
            for u in range(0, 121, 20):                       # la toise
                c = (120, 130, 160, 255) if k == 0 else (150, 140, 120, 255)
                d.line([(0, sol - u), (W, sol - u)], fill=c[:3] + (70,))
                d.line([(0, sol - u), (6, sol - u)], fill=c)
        x = marge
        for s, vol in sprites:
            b.alpha_composite(s, (x, sol - vol - s.height))
            x += s.width + esp
        bandes.append(b.resize((b.width * z, b.height * z), Image.NEAREST))
    im = Image.new("RGB", (W * z, sum(b.height for b in bandes) + 16), FOND)
    y = 0
    for b in bandes:
        im.paste(b.convert("RGB"), (0, y))
        y += b.height + 8
    return im, [(c[1], _boite(c)[1][3] - _boite(c)[1][1], P.PERSOS[c]["vol"]) for c in cles]


def acteurs(z=4):
    """La planche des acteurs : pour chacun, l'acteur d'aujourd'hui à sa taille d'écran (5 px par unité), le nouveau
    à la sienne (2 px par unité), puis toutes ses images agrandies ; sur fond sombre, puis sur fond clair."""
    import acteurs_hd as A
    import planches as PL
    import rendu
    fins = rendu._dossier("sprites2x")
    W = 1500
    bandes = []
    for fond in ((40, 48, 82), (226, 222, 206)):
        o = Image.new("RGBA", (W, 4000), fond + (255,))
        x, y, hmax = 6, 6, 0
        for nom in A.ORDRE:
            a = A.ACTEURS[nom]
            # Un acteur né en HD (grenouille, canard, escargot) n'a pas d'ancienne version : sa case reste vide.
            vieux = PL.sprite_image(fins["acteur-" + nom], 5, 0) if "acteur-" + nom in fins else \
                Image.new("RGBA", (20, 20), (0, 0, 0, 0))
            large = vieux.width + 8 + a["w"] * 2 + 14 + a["n"] * (a["w"] * z + 4) + 18
            if x + large > W - 6:
                x, y, hmax = 6, y + hmax + 12, 0
            o.alpha_composite(vieux, (x, y))
            x += vieux.width + 8
            o.alpha_composite(en_image(A.image(nom, 0), 2), (x, y))
            x += a["w"] * 2 + 14
            for i in range(a["n"]):
                o.alpha_composite(en_image(A.image(nom, i), z), (x, y))
                x += a["w"] * z + 4
            x += 18
            hmax = max(hmax, a["h"] * z, vieux.height)
        bandes.append(o.crop((0, 0, W, y + hmax + 8)))
    im = Image.new("RGB", (W, sum(b.height for b in bandes)), FOND)
    y = 0
    for b in bandes:
        im.paste(b.convert("RGB"), (0, y))
        y += b.height
    return im


def petits_acteurs():
    """Les acteurs de moins de 16 unités sur le décor HD le plus clair et le plus sombre (ciel, milieu, sol)."""
    import acteurs_hd as A
    import personnages_hd_export as X
    dossier = os.path.normpath(os.path.join(ICI, "..", "..", "assets", "decors"))
    decors = []
    for nom in sorted(os.listdir(dossier)):
        with open(os.path.join(dossier, nom), encoding="utf-8") as fh:
            d = X.decoder(fh.read())
        pal = {k: (int(v[1:3], 16), int(v[3:5], 16), int(v[5:7], 16)) for k, v in d["palette"].items()}
        im = Image.new("RGB", (d["w"], d["h"]))
        px = im.load()
        total = 0
        for y, rang in enumerate(d["images"][0]):
            for x, ch in enumerate(rang):
                px[x, y] = pal[ch]
                total += pal[ch][0] * 3 + pal[ch][1] * 6 + pal[ch][2]
        decors.append((total, im))
    decors.sort(key=lambda t: t[0])
    petits = [n for n in A.ORDRE if max(A.ACTEURS[n]["w"], A.ACTEURS[n]["h"]) <= 16]
    planche = Image.new("RGB", (960, 968), FOND)
    for j, (_, decor) in enumerate((decors[-1], decors[0])):
        sc = decor.convert("RGBA")
        for rang, y in enumerate((40, 120, 200)):
            x = 16 + rang * 9
            for n in petits:
                sc.alpha_composite(en_image(A.image(n, 0)), (x, y - A.ACTEURS[n]["h"]))
                x += A.ACTEURS[n]["w"] + 12
        planche.paste(sc.resize((960, 480), Image.NEAREST).convert("RGB"), (0, j * 488))
    return planche


def main():
    os.makedirs(SORTIE, exist_ok=True)
    quoi = sys.argv[1] if len(sys.argv) > 1 else "tout"
    if quoi == "apercu":
        return apercu(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 6)
    if quoi in ("tout", "acteurs"):
        acteurs().save(os.path.join(SORTIE, "acteurs.png"))
        petits_acteurs().save(os.path.join(SORTIE, "petits-acteurs.png"))
    if quoi == "acteurs":
        return
    if quoi in ("tout", "essai"):
        essai().save(os.path.join(SORTIE, "essai.png"))
    if quoi == "essai":
        return
    for campagne in ("grande-panne", "phare-eteint", "petit-nuage"):
        if quoi in ("tout", campagne) and sum(1 for c in P.ORDRE if c[0] == campagne) > 3:
            im, toise = groupe(campagne)
            im.save(os.path.join(SORTIE, "groupe-%s.png" % campagne))
            print("toise", campagne, toise)
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
