"""Planche de contrôle des icônes de traits (traits_sprites.py) : chaque icône en dessin 1× et en dessin fin, sur la
case sombre du PC et sur une case claire (téléphone, thème clair), avec son nom ; puis la silhouette « ? ».

    python3 outils/sprites/planches_traits.py [dossier]      (par défaut : outils/sprites/planches/traits)
"""
import os
import sys

from PIL import Image, ImageDraw

import planches
import rendu
import traits_sprites

SOMBRE = (21, 26, 46)
CLAIR = (246, 244, 238)
FOND = (15, 19, 36)
TEXTE = (214, 220, 228)


def main():
    dossier = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "planches", "traits")
    os.makedirs(dossier, exist_ok=True)
    B = rendu.banque()
    F = rendu.banque_fine(B)
    ids = traits_sprites.ids()
    z, case, colonnes = 6, 124, 7
    lignes = (len(ids) + colonnes - 1) // colonnes
    out = Image.new("RGB", (colonnes * (case * 2 + 12) + 12, lignes * (case * 2 + 40) + 12), FOND)
    d = ImageDraw.Draw(out)
    for i, sid in enumerate(ids):
        x0, y0 = 12 + (i % colonnes) * (case * 2 + 12), 12 + (i // colonnes) * (case * 2 + 40)
        d.text((x0, y0), sid[len("trait-"):], fill=TEXTE)
        for k, (fond, fin) in enumerate(((SOMBRE, False), (CLAIR, False), (SOMBRE, True), (CLAIR, True))):
            s = F[sid] if fin else B[sid]
            im = planches.sprite_image(s, z // 2 if fin else z)
            cx, cy = x0 + (k % 2) * case, y0 + 16 + (k // 2) * case
            tuile = Image.new("RGBA", (case - 4, case - 4), fond + (255,))
            tuile.alpha_composite(im, ((case - 4 - im.width) // 2, (case - 4 - im.height) // 2))
            out.paste(tuile.convert("RGB"), (cx, cy))
    chemin = os.path.join(dossier, "traits.png")
    out.save(chemin)
    print(chemin)


if __name__ == "__main__":
    main()
