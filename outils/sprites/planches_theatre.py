"""Planches du théâtre (docs/SCENES.md) : chaque scène d'une campagne jouée par la référence, en GIF à la vitesse réelle
et en planche d'images clés, pour juger un décor animé, ses acteurs et les réactions aux clics sans lancer l'application.

    python3 outils/sprites/planches_theatre.py [dossier] [campagne] [décor]

Par scène : Pilou entre, vit, se fait cliquer (et ce qui répond au clic dans la scène), puis s'en va.
`theatre-<campagne>-<décor>.gif` (×3) et `theatre-<campagne>.png` (deux images par scène).
"""
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)

import theatre as T  # noqa: E402


def image(px, e):
    from PIL import Image
    im = Image.new("RGB", (T.W, T.H))
    im.putdata([((v >> 16) & 255, (v >> 8) & 255, v & 255) for v in px])
    return im.resize((T.W * e, T.H * e), Image.NEAREST)


def scenario(sc):
    """Une petite vie : entrée, un clic sur Pilou, un clic sur chaque chose sensible, une humeur, le départ."""
    evts = [(0, "entree", 0, 0), (3500, "clic", sc.place, T.sol(sc, sc.place) - 8)]
    t = 6000
    for s in sc.sensibles:
        evts.append((t, "clic", (s[1] + s[3]) // 2, (s[2] + s[4]) // 2))
        t += 2500
    evts.append((t, "humeur", "joie", 0))
    evts.append((t + 2500, "depart", 1, 0))
    return evts, t + 2500 + 9000


def main():
    from PIL import Image
    dossier = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ICI, "planches")
    seule = sys.argv[2] if len(sys.argv) > 2 else None
    decor_seul = sys.argv[3] if len(sys.argv) > 3 else None
    os.makedirs(dossier, exist_ok=True)
    B, A = T.charger()
    for f in sorted(os.listdir(os.path.join(T.ASSETS, "scenes"))):
        camp = f[:-4]
        if not f.endswith(".txt") or camp == "animations" or (seule and camp != seule):
            continue
        scenes = T.scenes_de(camp)
        cles = []
        for nom, sc in scenes.items():
            if decor_seul and nom != decor_seul:
                continue
            decor = B.get("decor-%s-%s" % (camp, nom))
            evts, fin = scenario(sc)
            ims = [image(T.composer(B, T.TEINTES["bleu"], decor, sc, A, evts, t), 3) for t in range(0, fin, T.PAS)]
            ims[0].save(os.path.join(dossier, "theatre-%s-%s.gif" % (camp, nom)), save_all=True, append_images=ims[1:],
                        duration=T.PAS, loop=0)
            cles.append((ims[len(ims) // 5], ims[len(ims) // 2]))
            print("theatre-%s-%s.gif" % (camp, nom), len(ims), "images")
        if cles:
            w, h = cles[0][0].size
            planche = Image.new("RGB", (w * 2, h * len(cles)))
            for i, (a, b) in enumerate(cles):
                planche.paste(a, (0, i * h))
                planche.paste(b, (w, i * h))
            planche.save(os.path.join(dossier, "theatre-%s.png" % camp))


if __name__ == "__main__":
    main()
