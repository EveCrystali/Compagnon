"""Planches de contrôle des animations de campagne : toutes les images de chaque animation côte à côte, et un GIF.

    python3 outils/sprites/planches_animations.py [dossier] [filtre]
        (par défaut : outils/sprites/planches/animations ; filtre : début d'identifiant, « decor-phare » par exemple)

  decors-<campagne>.png        chaque décor animé : ses images (dessin fin) côte à côte, la première à droite répétée
                               (pour juger la boucle), la durée par image
  decors-<campagne>.gif        tous les décors de la campagne en mosaïque, animés à leur vitesse réelle
  portraits-<campagne>.png     chaque personnage, chaque expression : repos, clignement, parole (fin ×3, 1× ×3)
  portraits-<campagne>.gif     les personnages qui respirent, clignent, parlent (chooser commun, animations.py)

Lit les sprites écrits dans assets/ (lancer generer.py avant).
"""
import os
import sys

from PIL import Image, ImageDraw

import animations
import planches
import rendu

FOND = (24, 28, 38)
TEXTE = (214, 220, 228)


_CACHE = {}


def _img(s, k, z):
    cle = (id(s), k, z)
    if cle not in _CACHE:
        _CACHE[cle] = planches.sprite_image(s, z, k)
    return _CACHE[cle]


def decors(dossier, B2, filtre):
    par = {}
    for sid in sorted(k for k in B2 if k.startswith("decor-") and k.startswith(filtre)):
        c = sid.split("-")[1] if not sid.startswith("decor-grande-panne") else "grande-panne"
        for camp in ("prologue", "grande-panne", "phare-eteint", "petit-nuage"):
            if sid.startswith("decor-" + camp + "-"):
                c = camp
        par.setdefault(c, []).append(sid)
    for c, ids in par.items():
        z = 1
        n = max(len(B2[i].images) for i in ids)
        w, h = 192 * z, 80 * z
        out = Image.new("RGB", ((w + 6) * (n + 1) + 10, (h + 20) * len(ids) + 10), FOND)
        d = ImageDraw.Draw(out)
        for j, sid in enumerate(ids):
            s = B2[sid]
            y = 10 + j * (h + 20)
            d.text((10, y), "%s · %d images · %d ms" % (sid, len(s.images), s.duree), fill=TEXTE)
            for k in range(len(s.images) + 1):
                out.paste(_img(s, k % len(s.images), z), (10 + k * (w + 6), y + 12))
        out.save(os.path.join(dossier, "decors-%s.png" % c))
        # GIF : mosaïque à la vitesse réelle (pas commun : le plus petit diviseur des durées).
        cols = 2
        rang = (len(ids) + cols - 1) // cols
        import math
        pas = 0
        for sid in ids:
            pas = math.gcd(pas, max(B2[sid].duree, 1))
        pas = max(pas, 20)
        total = 1
        for sid in ids:
            s = B2[sid]
            total = _ppcm(total, max(1, len(s.images) * max(s.duree, 1)))
        total = min(total, 12000)
        images = []
        for t in range(0, total, pas):
            im = Image.new("RGB", (cols * (w + 4) + 4, rang * (h + 4) + 4), FOND)
            for j, sid in enumerate(ids):
                s = B2[sid]
                k = int(t // s.duree) % len(s.images) if s.duree else 0
                im.paste(_img(s, k, z), (4 + (j % cols) * (w + 4), 4 + (j // cols) * (h + 4)))
            images.append(im)
        # Images identiques fusionnées (le GIF reste léger).
        sortie, durees = [], []
        for im in images:
            if sortie and im.tobytes() == sortie[-1].tobytes():
                durees[-1] += pas
            else:
                sortie.append(im)
                durees.append(pas)
        sortie[0].save(os.path.join(dossier, "decors-%s.gif" % c), save_all=True, append_images=sortie[1:], duration=durees,
                       loop=0, optimize=False)


def _ppcm(a, b):
    import math
    return a * b // math.gcd(a, b)


def portraits(dossier, B, B2, filtre):
    par = {}
    for sid in sorted(k for k in B2 if k.startswith("portrait-") and k.startswith(filtre)):
        for camp in ("prologue", "grande-panne", "phare-eteint", "petit-nuage"):
            if sid.startswith("portrait-" + camp + "-"):
                par.setdefault(camp, []).append(sid)
    for c, ids in par.items():
        z = 3
        s0 = B2[ids[0]]
        w, h = len(s0.images[0][0]) * z, len(s0.images[0]) * z
        n = max(len(B2[i].images) for i in ids)
        cols = n + 2
        out = Image.new("RGB", (cols * (w + 6) + 20, len(ids) * (h + 22) + 10), FOND)
        d = ImageDraw.Draw(out)
        for j, sid in enumerate(ids):
            s, s1 = B2[sid], B[sid]
            y = 10 + j * (h + 22)
            d.text((10, y), sid, fill=TEXTE)
            for k in range(len(s.images)):
                out.paste(_img(s, k, z), (10 + k * (w + 6), y + 12), _img(s, k, z))
            p = _img(s1, 0, z)
            out.paste(p, (10 + len(s.images) * (w + 6) + 10, y + 12), p)
        out.save(os.path.join(dossier, "portraits-%s.png" % c))
        # GIF : chaque portrait au repos puis qui parle, avec le choix d'image commun (animations.image_portrait).
        cols = min(6, len(ids))
        rang = (len(ids) + cols - 1) // cols
        images = []
        for t in range(0, 8000, 60):
            parle = (t // 2000) % 2 == 1
            im = Image.new("RGB", (cols * (w + 4) + 4, rang * (h + 4) + 4), (60, 66, 92))
            for j, sid in enumerate(ids):
                s = B2[sid]
                k = animations.image_portrait(len(s.images), s.duree, t + j * 377, parle, animations.COMPLETES)
                g = _img(s, k, z)
                im.paste(g, (4 + (j % cols) * (w + 4), 4 + (j // cols) * (h + 4)), g)
            images.append(im)
        images[0].save(os.path.join(dossier, "portraits-%s.gif" % c), save_all=True, append_images=images[1:], duration=60, loop=0)


def main():
    dossier = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "planches",
                                                                 "animations")
    filtre = sys.argv[2] if len(sys.argv) > 2 else ""
    os.makedirs(dossier, exist_ok=True)
    B = rendu.banque()
    B2 = rendu.banque_fine(B)
    if not filtre or filtre.startswith("decor"):
        decors(dossier, B2, filtre)
    if not filtre or filtre.startswith("portrait"):
        portraits(dossier, B, B2, filtre)


if __name__ == "__main__":
    main()
