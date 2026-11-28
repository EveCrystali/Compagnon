"""Décors haute définition des campagnes (480 × 240, 2 px d'écran par pixel) : registre, format « décor compact », référence, planches.

    py outils/sprites/decors_hd.py                 tout écrire : assets/decors/, la référence, les planches
    py outils/sprites/decors_hd.py prologue mare   un seul décor (la référence n'est alors pas réécrite)

Les lieux sont peints dans decors_hd_<campagne>.py avec les briques de paysage.py (docs/PEINTURE.md) ; chacun se
déclare par @decor(campagne, id, soleil, tons). Ce module les joue image par image et écrit :

  assets/decors/decor-<campagne>-<id>.txt     le décor, au format de docs/SCENES-HD.md (§ 3) : des plans, des plages
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
CAMPAGNES = ("prologue", "grande-panne", "phare-eteint", "petit-nuage")
DECORS = {}
# Les deux lieux par campagne qui ont leurs montages PC et téléphone (les autres : image, boucle, avant / après).
MONTAGES = {"prologue": ("mare", "seuil"), "grande-panne": ("hall-pas-comptes", "horloge-systeme"),
            "phare-eteint": ("port-trebrume", "lanterne-du-phare"), "petit-nuage": ("abreuvoir", "terrier-aux-bocaux")}
LIEUX = {}          # id du décor → (campagne, lieu) : les deux peuvent contenir un trait d'union


def decor(campagne, id_, soleil, tons, images=pg.IMAGES, duree=pg.DUREE, nom=""):
    """Déclare un lieu : f(P, tab) peint ses plans. soleil : (x, y) de la lumière ; tons : paysage.Tons."""
    def poser(f):
        DECORS["decor-%s-%s" % (campagne, id_)] = (f, soleil, tons, images, duree, nom or id_)
        LIEUX["decor-%s-%s" % (campagne, id_)] = (campagne, id_)
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
# Le format des décors (docs/SCENES-HD.md, § 3) : des plans, du fond vers l'avant ; pour chacun une palette à lettres,
# des plages, « . » = comme l'image précédente du même plan, « , » = transparent.
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


def plans_du_decor(sid):
    """Les plans d'un décor, image par image : [(nom, profondeur 0..100, [grilles 240 × 480, -1 = transparent])].
    Un plan dont toutes les images sont identiques n'en garde qu'une (il est fixe)."""
    n = DECORS[sid][3]
    tabs = [tableau(sid, i / n) for i in range(n)]
    P = tabs[0].P
    plans = []
    for k, (nom, prof, _) in enumerate(tabs[0].plans):
        ims = [t.plans[k][2][:, P.M:P.M + P.W] for t in tabs]
        if all((im == ims[0]).all() for im in ims[1:]):
            ims = ims[:1]
        if (ims[0] >= 0).any() or len(ims) > 1:
            plans.append((nom, int(round(prof * 100)), ims))
    assert (plans[0][2][0] >= 0).all(), "%s : le premier plan doit être opaque" % sid
    assert len(plans) <= 5, "%s : cinq plans au plus" % sid
    return plans, [t.image() for t in tabs]


def encoder(sid, plans, duree, commentaire=""):
    h, w = plans[0][2][0].shape
    lignes = []
    if commentaire:
        lignes.append("# " + commentaire)
    lignes += ["id: " + sid, "taille: %d %d" % (w, h), "plans: %d" % len(plans)]
    for nom, prof, ims in plans:
        couleurs = sorted({int(v) for im in ims for v in np.unique(im) if v >= 0})
        assert len(couleurs) <= len(LETTRES), "%s, plan %s : %d couleurs, le format en porte %d" % (sid, nom, len(couleurs),
                                                                                                  len(LETTRES))
        lettre = {v: LETTRES[i] for i, v in enumerate(couleurs)}
        lettre[-1] = ","
        lignes += ["plan: %s %d fond" % (nom, prof), "duree: %d" % (duree if len(ims) > 1 else 0),
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
    """Le lecteur de référence : {id, w, h, plans: [{nom, profondeur, couche, duree, palette (lettre → #rrggbb), images
    (listes de rangées de caractères ; « , » = transparent)}]}. C'est cet algorithme que C# et Java refont."""
    lignes = [l.rstrip("\r") for l in texte.split("\n")]
    d = {"plans": []}
    i = 0
    plan = None
    while i < len(lignes):
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
        elif cle == "plans":
            pass
        elif cle == "plan":
            nom, prof, couche = val.split()
            plan = {"nom": nom, "profondeur": int(prof), "couche": couche, "duree": 0, "palette": {}, "images": []}
        elif cle in ("duree", "palette") and plan is None:           # un seul plan, sans ligne « plan: »
            plan = {"nom": "decor", "profondeur": 0, "couche": "fond", "duree": 0, "palette": {}, "images": []}
            i -= 1
        elif cle == "duree":
            plan["duree"] = int(val)
        elif cle == "palette":
            for paire in val.split():
                a, _, b = paire.partition("=")
                plan["palette"][a] = b
        elif cle == "images":
            prec = None
            for _ in range(int(val)):
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
                plan["images"].append(image)
                prec = image
            d["plans"].append(plan)
            plan = None
    return d


def fnv(image, palette):
    """Empreinte FNV-1a d'une image décodée, sur ses pixels ARGB 0xFFrrggbb (transparent : 0x00000000), octets de
    poids faible d'abord, comme theatre.fnv."""
    h = 0x811C9DC5
    octets = {k: (int(v[5:7], 16), int(v[3:5], 16), int(v[1:3], 16), 255) for k, v in palette.items()}
    octets[","] = (0, 0, 0, 0)
    for rang in image:
        for ch in rang:
            for o in octets[ch]:
                h ^= o
                h = (h * 0x01000193) & 0xFFFFFFFF
    return h


def composer(d, k=0):
    """L'image k recomposée d'un décor décodé, caméra à 0 : rangées de couleurs #rrggbb (le contrôle de l'écriture)."""
    out = None
    for plan in d["plans"]:
        im = plan["images"][k % len(plan["images"])]
        coul = [[plan["palette"].get(ch) for ch in rang] for rang in im]
        out = coul if out is None else [[b if b is not None else a for a, b in zip(ra, rb)] for ra, rb in zip(out, coul)]
    return out


def ecrire(sid):
    """Peint, écrit et relit un décor. Renvoie (images composées, texte)."""
    _, _, _, n, duree, nom = DECORS[sid]
    plans, composees = plans_du_decor(sid)
    texte = encoder(sid, plans, duree, "Décor de campagne, haute définition : " + nom)
    relu = decoder(texte)
    for k in (0, n - 1):                                   # ce qu'on relit doit redonner l'image peinte
        assert composer(relu, k) == [[pg.PAL[int(v)] for v in rang] for rang in composees[k]], sid
    os.makedirs(SORTIE, exist_ok=True)
    with open(os.path.join(SORTIE, sid + ".txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(texte)
    return composees, texte


def lignes_reference(texte):
    d = decoder(texte)
    return ["%s %s %d %d %d %d %s" % (d["id"], p["nom"], d["w"], d["h"], len(p["images"]), p["duree"],
                                      " ".join("%08x" % fnv(im, p["palette"]) for im in p["images"])) for p in d["plans"]]


# ---------------------------------------------------------------------------------------------------------------
# Planches : avant / après, boucle, montages (les gabarits et les personnages sont ceux de l'étude)
# ---------------------------------------------------------------------------------------------------------------
def planches(sid, ims):
    from PIL import Image
    import paysages_etude as etude
    import planches as pl
    import rendu
    campagne, lieu = LIEUX[sid]
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
    if lieu not in MONTAGES.get(campagne, ()):
        return
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


def planche_campagnes(premieres):
    """Une planche par campagne : tous ses lieux, un pixel par pixel (480 × 240), trois par rangée."""
    from PIL import Image
    for campagne in sorted({LIEUX[s][0] for s in premieres}):
        sids = [s for s in sorted(DECORS) if LIEUX[s][0] == campagne]
        if any(s not in premieres for s in sids):
            continue                                   # un seul lieu repeint : la planche garde son état
        rangs = (len(sids) + 2) // 3
        planche = Image.new("RGB", (3 * 484 - 4, rangs * 244 - 4), (11, 14, 26))
        for i, s in enumerate(sids):
            planche.paste(pg.en_image(premieres[s]), ((i % 3) * 484, (i // 3) * 244))
        planche.save(os.path.join(PLANCHES, campagne, "planche.png"))


def main():
    charger()
    args = sys.argv[1:]
    choisis = [s for s in sorted(DECORS) if not args or (LIEUX[s][0] == args[0] and (len(args) < 2 or LIEUX[s][1] == args[1]))]
    ref = []
    premieres = {}
    for sid in choisis:
        ims, texte = ecrire(sid)
        premieres[sid] = ims[0]
        ref += lignes_reference(texte)
        planches(sid, ims)
        d = decoder(texte)
        print("%s : %d Ko, plans : %s" % (sid, len(texte.encode("utf-8")) // 1024, ", ".join(
            "%s %d (%s)" % (q["nom"], q["profondeur"], "fixe" if len(q["images"]) == 1 else "%d images" % len(q["images"]))
            for q in d["plans"])))
    planche_campagnes(premieres)
    if not args:
        with open(REFERENCE, "w", encoding="utf-8", newline="\n") as f:
            f.write("# Décors haute définition (decors_hd.py, docs/SCENES-HD.md) : une ligne par plan,\n"
                    "# id plan largeur hauteur images duree, puis l'empreinte FNV-1a de chaque image décodée (pixels ARGB\n"
                    "# 0xFFrrggbb, transparent 0x00000000, rangée par rangée). Lu par les tests C# et Java.\n")
            f.write("\n".join(ref) + "\n")


if __name__ == "__main__":
    import decors_hd          # le registre vit dans le module importé par les décors, pas dans __main__
    decors_hd.main()
