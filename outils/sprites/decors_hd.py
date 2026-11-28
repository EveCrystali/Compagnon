"""Décors haute définition des campagnes (480 × 240, 2 px d'écran par pixel) : registre, format « décor compact », référence, planches.

    py outils/sprites/decors_hd.py                 tout écrire : assets/decors/, la référence, les planches
    py outils/sprites/decors_hd.py prologue mare   un seul décor (la référence n'est alors pas réécrite)

Les lieux sont peints dans decors_hd_<campagne>.py avec les briques de paysage.py (docs/PEINTURE.md) ; chacun se
déclare par @decor(campagne, id, soleil, tons). Ce module les joue image par image et écrit :

  assets/decors/decor-<campagne>-<id>.txt     le décor, au format compact décrit dans docs/SPRITES.md
  outils/sprites/decors-hd-reference.txt      id, taille, nombre d'images, durée, empreinte FNV-1a de chaque image :
                                              ce que les lecteurs C# et Java doivent retrouver
  docs/maquettes/paysages/<campagne>/         avant / après, boucle en GIF, montages PC et téléphone

Dépend de numpy et de Pillow : c'est pourquoi il vit à côté de generer.py et non dedans.
"""
import os
import sys

import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)

import paysage as pg  # noqa: E402

RACINE = os.path.normpath(os.path.join(ICI, "..", ".."))
SORTIE = os.path.join(RACINE, "assets", "decors")
REFERENCE = os.path.join(ICI, "decors-hd-reference.txt")
PLANCHES = os.path.join(RACINE, "docs", "maquettes", "paysages")
# Les lettres de palette : jamais un chiffre (ce sont les longueurs des plages), ni « . » (pixel inchangé).
LETTRES = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!$%&*+-/<>?@^_~"
CAMPAGNES = ("prologue",)
DECORS = {}


def decor(campagne, id_, soleil, tons, images=pg.IMAGES, duree=pg.DUREE, nom=""):
    """Déclare un lieu : f(P, tab) peint ses plans. soleil : (x, y) de la lumière ; tons : paysage.Tons."""
    def poser(f):
        DECORS["decor-%s-%s" % (campagne, id_)] = (f, soleil, tons, images, duree, nom or id_)
        return f
    return poser


def charger():
    for c in CAMPAGNES:
        __import__("decors_hd_" + c.replace("-", "_"))


def tableau(sid, phase=0.0):
    """Le tableau d'une image de la boucle, plans séparés (pour la parallaxe ou le cadrage)."""
    f, soleil, tons, _, _, _ = DECORS[sid]
    pg.utiliser(tons)
    P = pg.Peintre(soleil, phase)
    tab = pg.Tableau(P)
    f(P, tab)
    return tab


def boucle(sid, camera=None):
    """Les images de la boucle (grilles de numéros de couleur de paysage.PAL)."""
    n = DECORS[sid][3]
    return [tableau(sid, i / n).image(camera(i / n) if camera else 0.0) for i in range(n)]


# ---------------------------------------------------------------------------------------------------------------
# Le format « décor compact » (docs/SPRITES.md) : palette à lettres, plages, « . » = comme l'image précédente
# ---------------------------------------------------------------------------------------------------------------
def _plages(s):
    out, i, n = [], 0, len(s)
    while i < n:
        j = i
        while j < n and s[j] == s[i]:
            j += 1
        out.append((str(j - i) if j - i > 1 else "") + s[i])
        i = j
    return "".join(out)


def encoder(sid, ims, duree, commentaire=""):
    couleurs = sorted({int(v) for im in ims for v in np.unique(im)})
    assert len(couleurs) <= len(LETTRES), "%s : %d couleurs, le format en porte %d" % (sid, len(couleurs), len(LETTRES))
    lettre = {v: LETTRES[i] for i, v in enumerate(couleurs)}
    h, w = ims[0].shape
    lignes = []
    if commentaire:
        lignes.append("# " + commentaire)
    lignes += ["id: " + sid, "taille: %d %d" % (w, h), "duree: %d" % duree,
               "palette: " + " ".join("%s=%s" % (lettre[v], pg.PAL[v]) for v in couleurs), "images: %d" % len(ims)]
    prec = None
    for im in ims:
        for y in range(h):
            if prec is None:
                s = "".join(lettre[int(v)] for v in im[y])
            else:
                s = "".join("." if a == b else lettre[int(a)] for a, b in zip(im[y], prec[y]))
            lignes.append(_plages(s))
        prec = im
    return "\n".join(lignes) + "\n"


def decoder(texte):
    """Le lecteur de référence : {id, w, h, duree, palette (lettre → #rrggbb), images (listes de rangées de lettres)}.
    C'est cet algorithme, et rien d'autre, que C# et Java doivent refaire."""
    d = {"palette": {}, "images": []}
    lignes = texte.split("\n")
    i = 0
    while True:
        l = lignes[i]
        i += 1
        if not l or l.startswith("#"):
            continue
        cle, _, val = l.partition(":")
        val = val.strip()
        if cle == "id":
            d["id"] = val
        elif cle == "taille":
            d["w"], d["h"] = (int(v) for v in val.split())
        elif cle == "duree":
            d["duree"] = int(val)
        elif cle == "palette":
            for paire in val.split():
                a, _, b = paire.partition("=")
                d["palette"][a] = b
        elif cle == "images":
            n = int(val)
            break
    prec = None
    for _ in range(n):
        image = []
        for y in range(d["h"]):
            rang, x, k = [], 0, 0
            for ch in lignes[i]:
                if "0" <= ch <= "9":
                    k = k * 10 + ord(ch) - 48
                    continue
                k = k or 1
                rang.extend(prec[y][x:x + k] if ch == "." else ch * k)
                x += k
                k = 0
            assert x == d["w"], "rangée de %d pixels au lieu de %d" % (x, d["w"])
            image.append(rang)
            i += 1
        d["images"].append(image)
        prec = image
    return d


def fnv(image, palette):
    """Empreinte FNV-1a d'une image décodée, sur ses pixels ARGB 0xFFrrggbb (octets de poids faible d'abord), comme
    theatre.fnv."""
    h = 0x811C9DC5
    octets = {k: (int(v[5:7], 16), int(v[3:5], 16), int(v[1:3], 16), 255) for k, v in palette.items()}
    for rang in image:
        for ch in rang:
            for o in octets[ch]:
                h ^= o
                h = (h * 0x01000193) & 0xFFFFFFFF
    return h


def ecrire(sid):
    """Peint, écrit et relit un décor. Renvoie (images, texte)."""
    _, _, _, _, duree, nom = DECORS[sid]
    ims = boucle(sid)
    texte = encoder(sid, ims, duree, "Décor de campagne, haute définition : " + nom)
    relu = decoder(texte)
    lettres = {v: k for k, v in relu["palette"].items()}
    for im, image in zip(ims, relu["images"]):
        assert ["".join(r) for r in image] == ["".join(lettres[pg.PAL[int(v)]] for v in rang) for rang in im], sid
    os.makedirs(SORTIE, exist_ok=True)
    with open(os.path.join(SORTIE, sid + ".txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(texte)
    return ims, texte


def ligne_reference(texte):
    d = decoder(texte)
    return "%s %d %d %d %d %s" % (d["id"], d["w"], d["h"], len(d["images"]), d["duree"],
                                  " ".join("%08x" % fnv(im, d["palette"]) for im in d["images"]))


# ---------------------------------------------------------------------------------------------------------------
# Planches : avant / après, boucle, montages (les gabarits et les personnages sont ceux de l'étude)
# ---------------------------------------------------------------------------------------------------------------
def planches(sid, ims):
    from PIL import Image
    import paysages_etude as etude
    import planches as pl
    import rendu
    _, campagne, lieu = sid.split("-", 2)
    dossier = os.path.join(PLANCHES, campagne)
    os.makedirs(dossier, exist_ok=True)
    vues = [pg.en_image(im, 2) for im in ims]
    vues[0].save(os.path.join(dossier, lieu + ".png"))
    vues[0].save(os.path.join(dossier, lieu + ".gif"), save_all=True, append_images=vues[1:], duration=DECORS[sid][4],
                 loop=0)
    # Avant (le décor 192 × 80 en service, à 5 px) au-dessus d'après (480 × 240 à 2 px), chacun à sa taille d'écran.
    ancien = rendu._dossier("sprites2x").get(sid)
    planche = Image.new("RGB", (960, 400 + 16 + 480), (11, 14, 26))
    if ancien is not None:
        planche.paste(pl.sprite_image(ancien, 5, 0).convert("RGB"), (0, 0))
    planche.paste(vues[0], (0, 416))
    planche.save(os.path.join(dossier, lieu + "-avant-apres.png"))
    # Montages : la scène avec Pilou et un personnage, dans la fenêtre du PC et sur un téléphone de 1078 × 2400.
    def scene(fmt, idx):
        im = vues[0].convert("RGBA")
        for spr, x in zip(etude.personnages("C"), (etude.PLACE + 4, etude.INTERLOCUTEUR)):
            g = spr.resize((spr.width * 2, spr.height * 2), Image.NEAREST)
            im.alpha_composite(g, ((int(round(x * 2.5)) - spr.width // 2) * 2,
                                   int(round((etude.SOL_Y - pg.HAUT) * 2.5)) * 2 - g.height))
        return im.convert("RGB")

    vraie, etude.scene = etude.scene, scene
    try:
        scene("C", None).save(os.path.join(dossier, lieu + "-scene.png"))
        etude.montage_pc("C", None).save(os.path.join(dossier, lieu + "-pc.png"))
        etude.montage_telephone("C", None).save(os.path.join(dossier, lieu + "-telephone.png"))
    finally:
        etude.scene = vraie


def main():
    charger()
    args = sys.argv[1:]
    choisis = [s for s in sorted(DECORS) if not args or (s.split("-")[1] == args[0] and (len(args) < 2 or
                                                                                         s.endswith("-" + args[1])))]
    ref = []
    for sid in choisis:
        ims, texte = ecrire(sid)
        ref.append(ligne_reference(texte))
        planches(sid, ims)
        brut = len(ims) * ims[0].size + len(ims) * ims[0].shape[0]
        print("%s : %d images, %d couleurs, %d Ko (une lettre par pixel : %d Ko)" % (
            sid, len(ims), len({int(v) for im in ims for v in np.unique(im)}), len(texte.encode("utf-8")) // 1024,
            brut // 1024))
    if not args:
        with open(REFERENCE, "w", encoding="utf-8", newline="\n") as f:
            f.write("# Décors haute définition (decors_hd.py) : id largeur hauteur images duree, puis l'empreinte FNV-1a de\n"
                    "# chaque image décodée (pixels ARGB 0xFFrrggbb, rangée par rangée). Lu par les tests C# et Java.\n")
            f.write("\n".join(ref) + "\n")


if __name__ == "__main__":
    import decors_hd          # le registre vit dans le module importé par les décors, pas dans __main__
    decors_hd.main()
