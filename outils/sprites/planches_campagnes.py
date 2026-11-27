"""Planches de contrôle des illustrations de campagne (décors, objets exclusifs portés, souvenirs, vignettes) et
avant / après du redessin fin.

    python3 outils/sprites/planches_campagnes.py [dossier]      (par défaut : outils/sprites/planches/campagnes)

  decors-<campagne>.png     chaque décor : 1× agrandi 4 fois, dessin fin agrandi 2 fois, taille réelle (1× et fin)
  exclusifs-portes.png      les objets exclusifs portés par Pilou aux quatre stades (portrait fin) et en 1×
  souvenirs.png             les timbres-souvenirs (fin ×4, 1× ×4, taille réelle)
  vignettes.png             vignettes de campagne et emblèmes de ton
  redessines-<n>.png        avant (1× agrandi automatiquement) / après (dessin fin natif), sprites redessinés
"""
import json
import os
import sys

from PIL import Image, ImageDraw

import campagnes_sprites
import planches
import planches_hd
import rendu

FOND = (28, 33, 40)
TEXTE = (200, 208, 216)
POLICE = planches_hd.POLICE


def image_sprite(s, z, k=0):
    return planches.sprite_image(s, z, k)


def colonne(images, ecart=6):
    w = max(i.width for i in images)
    h = sum(i.height for i in images) + ecart * (len(images) - 1)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    y = 0
    for i in images:
        out.alpha_composite(i, (0, y))
        y += i.height + ecart
    return out


def ligne(images, ecart=8):
    w = sum(i.width for i in images) + ecart * (len(images) - 1)
    h = max(i.height for i in images)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    x = 0
    for i in images:
        out.alpha_composite(i, (x, h - i.height))
        x += i.width + ecart
    return out


def decors(dossier, B, B2):
    racine = os.path.join(rendu.ASSETS, "campagnes")
    for c in sorted(os.listdir(racine)):
        f = os.path.join(racine, c, "campagne.json")
        if not os.path.isfile(f):
            continue
        with open(f, encoding="utf-8") as fh:
            fiche = json.load(fh)
        cases = []
        for d in fiche.get("decors", []):
            sid = "decor-%s-%s" % (c, d["id"])
            if sid not in B:
                continue
            s, s2 = B[sid], B2[sid]
            for k in range(len(s.images)):
                petit = ligne([image_sprite(s, 1, k), image_sprite(s2, 1, k)])
                im = ligne([image_sprite(s, 4, k), image_sprite(s2, 2, k), petit], 10)
                cases.append((im, "%s — %s%s" % (sid, d.get("nom", ""), " (image %d)" % (k + 1) if len(s.images) > 1 else "")))
        planches_hd.planche(cases, 1, os.path.join(dossier, "decors-%s.png" % c), titre="Décors : " + fiche.get("titre", c))


def exclusifs(dossier, B, T, TEN, B2):
    cases = []
    for i in campagnes_sprites.EXCLUSIFS:
        fins = [planches.grille_image(rendu.rendre(rendu.Pose(objets=[i], stade=st, t=300), B, T, TEN, 2, B2), 3)
                for st in (1, 2, 3, 4)]
        petits = [planches.grille_image(rendu.rendre(rendu.Pose(objets=[i], stade=st, t=300), B, T, TEN, 1), 2)
                  for st in (2, 4)]
        cases.append((ligne(fins + [colonne(petits)], 6), "%s (%s, ancre %s)" % (i, B[i].slot, B[i].ancre)))
    planches_hd.planche(cases, 2, os.path.join(dossier, "exclusifs-portes.png"), fond=(238, 242, 246),
                        titre="Objets exclusifs des campagnes, portés aux stades 1 à 4 (dessin fin) et en 1×")


def souvenirs(dossier, B, B2):
    cases = []
    for i in sorted(k for k in B if k.startswith("souvenir-")):
        cases.append((ligne([image_sprite(B2[i], 4), image_sprite(B[i], 4), image_sprite(B[i], 1), image_sprite(B2[i], 1)]),
                      i[len("souvenir-"):]))
    planches_hd.planche(cases, 3, os.path.join(dossier, "souvenirs.png"), titre="Souvenirs (fin ×4, 1× ×4, tailles réelles)")


def vignettes(dossier, B, B2):
    cases = []
    for i in sorted(k for k in B if k.startswith("campagne-") or k.startswith("ton-")):
        z = 4 if i.startswith("campagne-") else 6
        cases.append((ligne([image_sprite(B2[i], z), image_sprite(B[i], z), image_sprite(B[i], 1), image_sprite(B2[i], 1)]), i))
    planches_hd.planche(cases, 4, os.path.join(dossier, "vignettes.png"), titre="Vignettes de campagne et emblèmes de ton")


def redessines(dossier, B, ids, par=24):
    natifs = rendu._dossier("sprites2x")
    for n in range(0, len(ids), par):
        cases = []
        for i in ids[n:n + par]:
            if i not in B or i not in natifs:
                continue
            avant, apres = rendu.agrandir(B[i]), natifs[i]
            z = 3 if max(len(B[i].images[0][0]), len(B[i].images[0])) <= 40 else 2
            cases.append((ligne([image_sprite(avant, z), image_sprite(apres, z)], 10), i))
        planches_hd.planche(cases, 4, os.path.join(dossier, "redessines-%d.png" % (n // par + 1)),
                            titre="Avant (agrandi automatiquement) / après (dessin fin)")


def main():
    dossier = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "planches",
                                                                 "campagnes")
    os.makedirs(dossier, exist_ok=True)
    B, T, TEN = rendu.banque(), rendu.teintes(), rendu.tenues()
    B2 = rendu.banque_fine(B)
    decors(dossier, B, B2)
    exclusifs(dossier, B, T, TEN, B2)
    souvenirs(dossier, B, B2)
    vignettes(dossier, B, B2)
    ids = [l.strip() for l in sys.argv[2:]] if len(sys.argv) > 2 else []
    if ids:
        redessines(dossier, B, ids)


if __name__ == "__main__":
    main()
