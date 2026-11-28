"""Planche de contrôle des saynètes de repos (saynetes.py) : chaque saynète image par image, rendu fin.

    python3 outils/sprites/planches_saynetes.py [dossier] [pas_ms]    (défaut : outils/sprites/planches/saynetes, 250)

  <id>.png      une bande par saynète, une image tous les pas_ms, au niveau « complètes » (stade 2 ; le livre et la
                lecture au stade 3 en plus) ; les objets nécessaires (tasse, lunette, compagnon) sont portés
  toutes.png    toutes les bandes empilées

Même application de la saynète que SaynetesFenetre.cs (PC) et PilouVue.java (téléphone).
"""
import os
import sys

from PIL import Image

import planches_vie as pv
import rendu
import saynetes

PORTES = {"boit": ["tasse-cafe"], "guette": ["jumelles"], "compagnon": ["petit-chat"]}


def pose(s, d, stade=2, niveau=saynetes.COMPLETES, sens=1):
    j = saynetes.jeu(s, d, niveau, sens)
    kw = dict(t=d, stade=stade, vie=True, objets=list(PORTES.get(s.id, [])))
    if j:
        kw.update(expr=j["expr"], regard=j["regard"], regard_y=j["regard_y"], cligne=bool(j["cligne"]),
                  baille=bool(j["baille"]), salue=bool(j["salue"]), assis=j["assis"] / 1000, saut=j["saut"] / 1000,
                  etire=j["etire"] / 1000, tremble=j["penche"] / 1000)
        kw["objets"] += list(j["objets"])
    return kw


def bande(B, T, TEN, s, pas, stade=2):
    ims = [("%d" % d, pv.image(B, T, TEN, pv.SOMBRE, **pose(s, d, stade))) for d in range(0, s.duree, pas)]
    return pv.bande("%s (poids %d, %d ms, stade %d)" % (s.id, s.poids, s.duree, stade), ims, pv.SOMBRE, pv.TEXTE)


def main():
    dossier = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "planches",
                                                                   "saynetes")
    pas = int(sys.argv[2]) if len(sys.argv) > 2 else 250
    os.makedirs(dossier, exist_ok=True)
    B, T, TEN = rendu.banque(), rendu.teintes(), rendu.tenues()
    banque = saynetes.lire(saynetes.texte_banque())
    bandes = []
    for s in banque:
        b = bande(B, T, TEN, s, pas)
        b.save(os.path.join(dossier, s.id + ".png"))
        bandes.append(b)
    w = max(b.width for b in bandes)
    out = Image.new("RGB", (w, sum(b.height for b in bandes)), pv.SOMBRE)
    y = 0
    for b in bandes:
        out.paste(b, (0, y))
        y += b.height
    out.save(os.path.join(dossier, "toutes.png"))
    print(len(bandes), "saynètes dans", dossier)


if __name__ == "__main__":
    main()
