"""Décors des campagnes (docs/CAMPAGNES.md, docs/SPRITES.md « Décors des campagnes ») : un bandeau illustré par
décor déclaré dans `assets/campagnes/<campagne>/campagne.json`.

Format commun : paysage de 96 × 40 pixels (1×), redessiné nativement en 192 × 80 (assets/sprites2x), opaque,
`ancre: aucun`. Identifiant : `decor-<campagne>-<décor>`. Trois plans au moins (fond, milieu, premier plan), une
lumière lisible, un détail charmant ; une palette restreinte par campagne (`Palette` de chaque module). Quelques
décors s'animent (deux ou trois images : vagues, néon, nuages).

Les dessins sont dans decors_prologue.py, decors_panne.py, decors_phare.py, decors_nuage.py ; chacun déclare ses
décors avec @decor(campagne, id, images, duree). Appelé par generer.py (tout()) aux deux échelles.
"""
import json
import os

from toile import Toile, ecrire

W, H = 96, 40
DECORS = {}
# Phase de la boucle d'ambiance en cours de dessin (0 ≤ PHASE < 1) : les outils des décors (flamme, mer, ciel de nuit,
# engrenages…) s'en servent pour bouger d'une image à l'autre sans à-coup (ambiances_decors.py).
PHASE = 0.0


def onde(decalage=0.0):
    """Sinus de la boucle d'ambiance (vaut 0 hors animation)."""
    import math
    return math.sin(2 * math.pi * (PHASE + decalage))


def decor(campagne, id_, images=1, duree=0):
    def poser(f):
        DECORS["decor-%s-%s" % (campagne, id_)] = (f, images, duree, campagne, id_)
        return f
    return poser


def toiles(sid):
    """Les images d'un décor à l'échelle courante (toile.ECHELLE) : sa boucle d'ambiance (ambiances_decors.py), ou ses
    images d'origine s'il n'en a pas."""
    global PHASE
    import ambiances_decors
    import sys
    f, n, duree, _, _ = DECORS[sid]
    regle = ambiances_decors.regle(sid)
    ims = []
    if regle is None:
        for k in range(n):
            PHASE = 0.0
            t = Toile(W, H)
            f(t, k)
            ims.append(t)
    else:
        images, duree, garder, effets = regle
        pal = sys.modules[f.__module__].PAL
        for k in range(images):
            PHASE = k / images
            t = Toile(W, H)
            f(t, (k * n) // images if garder else 0)
            for effet in effets:
                effet(t, PHASE, pal)
            ims.append(t)
        PHASE = 0.0
    for t in ims:
        for r in t.g:
            assert None not in r, "%s : pixel vide (un décor est opaque)" % sid
    return ims, duree


def charger():
    import decors_prologue  # noqa: F401
    import decors_panne  # noqa: F401
    import decors_phare  # noqa: F401
    import decors_nuage  # noqa: F401
    import decors_evolution  # noqa: F401


def declares():
    """Décors déclarés dans les fiches de campagne : [(campagne, id, nom)]."""
    racine = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "campagnes"))
    r = []
    for c in sorted(os.listdir(racine)):
        f = os.path.join(racine, c, "campagne.json")
        if os.path.isfile(f):
            with open(f, encoding="utf-8") as fh:
                d = json.load(fh)
            for x in d.get("decors", []):
                r.append((c, x["id"], x.get("nom", "")))
    return r


def tout():
    charger()
    noms = {"decor-%s-%s" % (c, i): n for c, i, n in declares()}
    for sid in sorted(DECORS):
        ims, duree = toiles(sid)
        ecrire(sid, ims, duree=duree, commentaire="Décor de campagne : " + noms.get(sid, sid))
