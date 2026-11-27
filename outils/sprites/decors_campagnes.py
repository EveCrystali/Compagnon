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


def decor(campagne, id_, images=1, duree=0):
    def poser(f):
        DECORS["decor-%s-%s" % (campagne, id_)] = (f, images, duree, campagne, id_)
        return f
    return poser


def toiles(sid):
    """Les images d'un décor à l'échelle courante (toile.ECHELLE)."""
    f, n, duree, _, _ = DECORS[sid]
    ims = []
    for k in range(n):
        t = Toile(W, H)
        f(t, k)
        for r in t.g:
            assert None not in r, "%s : pixel vide (un décor est opaque)" % sid
        ims.append(t)
    return ims, duree


def charger():
    import decors_prologue  # noqa: F401
    import decors_panne  # noqa: F401
    import decors_phare  # noqa: F401
    import decors_nuage  # noqa: F401


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
