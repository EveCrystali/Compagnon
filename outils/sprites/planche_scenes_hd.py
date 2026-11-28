"""Planche de contrôle des scènes HD (docs/SCENES-HD.md) : une image par scène d'une campagne, jouée par la référence,
pour relire un décor repeint sans lancer l'application. Sur chaque image : Pilou à sa place, le premier personnage
qui parle dans ce lieu, l'accessoire clé en orange, le panneau des choix en bleu (à la place que calcule
Theatre.PlacerPanneau), la légende du lieu en haut à gauche.

    python3 outils/sprites/planche_scenes_hd.py [dossier de sortie] [campagne…]

Sans campagne : toutes celles qui ont des scènes HD. Écrit hd-<campagne>.png (trois scènes par ligne, 480 × 240 chacune).
À vérifier : pieds sur le sol, personnage ni coupé ni caché, accessoire clé dégagé, panneau qui ne couvre ni Pilou ni
le personnage.
"""
import glob
import json
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(ICI))
APPEL = os.getcwd()                     # le dossier de sortie donné est relatif à l'endroit d'où on lance
sys.path.insert(0, ICI)
os.chdir(ICI)
import theatre  # noqa: E402
import theatre_hd  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402


def persos(c):
    """{décor: premier personnage qui y parle} d'après les nœuds de la campagne (le décor est hérité d'un nœud à l'autre)."""
    r, dec = {}, None
    for f in sorted(glob.glob(os.path.join(RACINE, "assets", "campagnes", c, "chapitre-*.json"))):
        with open(f, encoding="utf-8") as fh:
            noeuds = json.load(fh)["noeuds"]
        for _, n in noeuds.items():
            dec = n.get("decor") or dec
            if n.get("personnage") and dec and dec not in r:
                r[dec] = n["personnage"]
    return r


def recouvre(a, b):
    return max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))


def placer(sc, w, h, pilou_x, perso, taille, gene):
    """Theatre.PlacerPanneau (apps/PilouBureau/Theatre.cs), en HD : le coin haut gauche du panneau des choix."""
    W, H = sc.d.w, sc.d.h
    marge = pas = theatre.E(sc, 2)
    sp, sx = theatre.sol(sc, sc.interlocuteur), theatre.sol(sc, pilou_x)
    pl, ph = taille or (theatre.E(sc, 26), theatre.E(sc, 33))
    perso_r = (sc.interlocuteur - pl // 2 - 1, sp - ph, sc.interlocuteur + pl // 2 + 1, sp + 1)
    pilou_r = (pilou_x - 31, sx - 87, pilou_x + 31, sx + 1)
    meilleur, note = (marge, marge), None
    for x in range(marge, W - w - marge + 1, pas):
        for y in range(marge, H - h - marge + 1, pas):
            r = (x, y, x + w, y + h)
            n = sum(100000000 * recouvre(r, z) for z in gene)
            if sc.cle:
                n += 1000000 * recouvre(r, sc.cle)
            if perso:
                n += 1000 * recouvre(r, perso_r)
            n += 1000 * recouvre(r, pilou_r) // 2
            centre = x + w // 2
            n = n * 1000 + (max(0, W - abs(centre - sc.interlocuteur)) if perso else 0) * 4 + y
            if note is None or n < note:
                note, meilleur = n, (x, y)
    return meilleur


def planche(c, sortie, A, B, rendre):
    scs = theatre_hd.scenes_hd(c)
    if not scs:
        return 0
    ps = persos(c)
    noms = list(scs)
    cols = 3
    img = Image.new("RGB", (cols * 490, ((len(noms) + cols - 1) // cols) * 250), (10, 10, 20))
    for k, n in enumerate(noms):
        sc = scs[n]
        dec = theatre_hd.charger_decor_hd(c, n)
        if dec is None:
            continue
        sid = "pied-%s-%s" % (c, ps[n]) if n in ps else ""
        ev = [(0, "entree", 0, 0)] + ([(300, "perso", sid, 0)] if sid else [])
        px = theatre_hd.composer_hd(dec, sc, A, B, ev, 7000, rendre)
        im = Image.new("RGB", (sc.d.w, sc.d.h))
        im.putdata([((v >> 16) & 255, (v >> 8) & 255, v & 255) for v in px])
        d = ImageDraw.Draw(im)
        legende = (5, 5, 5 + 12 + 7 * len(n), 25)
        boutons = (390, 5, 475, 20)
        d.rectangle(legende, outline=(220, 220, 255))
        d.text((legende[0] + 3, legende[1] + 4), n, fill=(255, 255, 255))
        if sc.cle:
            d.rectangle(sc.cle, outline=(255, 150, 30))
        taille = theatre.TAILLES_HD.get(sid) if sid else None
        x, y = placer(sc, 185, 85, sc.place, bool(sid), taille, [legende, boutons])
        d.rectangle((x, y, x + 185, y + 85), outline=(90, 170, 255))
        d.text((4, 228), "%s%s" % (n, " · " + ps[n] if n in ps else ""), fill=(255, 255, 120))
        img.paste(im, ((k % cols) * 490, (k // cols) * 250))
    img.save(os.path.join(sortie, "hd-%s.png" % c))
    return len(noms)


def main(argv):
    sortie = os.path.join(APPEL, argv[1]) if len(argv) > 1 else os.path.join(RACINE, "planches-hd")
    os.makedirs(sortie, exist_ok=True)
    campagnes = argv[2:] or sorted(os.path.splitext(f)[0] for f in os.listdir(os.path.join(RACINE, "assets", "scenes-hd")) if f.endswith(".txt"))
    _, A = theatre.charger()
    B = theatre_hd.charger_sprites_hd()
    rendre = theatre_hd.rendeur_pilou()
    for c in campagnes:
        print(c, planche(c, sortie, A, B, rendre), "scènes :", os.path.join(sortie, "hd-%s.png" % c))


if __name__ == "__main__":
    main(sys.argv)
