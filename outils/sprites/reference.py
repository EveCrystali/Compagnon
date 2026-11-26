"""Empreintes de référence du rendu de Pilou : les tests C# (RenduTests.cs) et JVM (RenduPilouTest.java) doivent
retrouver exactement les mêmes pixels que ce rendu Python, pose par pose.

    python3 outils/sprites/reference.py  → outils/sprites/rendus-reference.txt
"""
import hashlib
import os
import struct

import rendu

POSES = [
    "expr=repos t=0",
    "expr=repos t=1300 cligne=1",
    "expr=concentre t=450",
    "expr=attente t=900",
    "expr=inquiet t=320",
    "expr=fete t=250",
    "expr=soulage t=700",
    "expr=grimace t=110",
    "expr=caresse t=800",
    "expr=dort t=2100",
    "expr=repos t=500 etourdi=1",
    "expr=repos t=500 baille=1",
    "expr=repos t=500 fatigue=1",
    "expr=repos t=230 marche=1 regard=1",
    "expr=repos t=90 marche=1 course=1 regard=-1",
    "expr=repos t=0 saut=3",
    "expr=repos t=0 assis=1",
    "expr=repos t=300 suspendu=1",
    "expr=repos t=0 chute=0.6",
    "expr=repos t=0 regard=1 clin=1 regard_y=-1",
    "expr=repos t=0 couleur=lavande",
    "expr=inquiet t=0 couleur=sable",
    "expr=repos t=0 accessoire=bonnet",
    "expr=repos t=0 accessoire=couronne",
    "expr=repos t=0 accessoire=lunettes",
    "expr=repos t=400 tenue=code",
    "expr=repos t=400 tenue=musique",
    "expr=concentre t=400 tenue=jeu-mmo",
    "expr=repos t=400 tenue=diaporama",
    "expr=repos t=300 objets=chapeau-sorcier,echarpe,petit-chat",
    "expr=repos t=300 objets=cape,baguette,aura",
    "expr=repos t=300 objets=inconnu,haut-de-forme",
    "expr=repos t=300 stade=1",
    "expr=fete t=300 stade=1",
    "expr=repos t=300 stade=3",
    "expr=dort t=1300 stade=3 accessoire=bonnet",
    "expr=repos t=300 stade=4",
    "expr=fete t=300 stade=4 tenue=code",
    "expr=repos t=0 stade=3 evolution=0.2",
    "expr=repos t=0 stade=3 evolution=0.5",
    "expr=repos t=0 stade=4 evolution=0.9",
    "expr=repos t=600 reaction=sueur",
    "expr=repos t=840 boude=1 objets=boude-nuage",
    "expr=repos t=840 stade=3 boude=1 cligne=1 objets=boude-nuage,boude-bras",
    "expr=repos t=840 stade=1 boude=1 dos=1 objets=boude-eclaircie,variante-calin-2,lunettes-rondes",
    "expr=concentre t=360 assis=1 objets=clavier-mini",
    "expr=concentre t=120 assis=1 stade=3 objets=tenue-code-lunettes,clavier-mini,pouf-4",
    "expr=repos t=0 dos=1 objets=pouf-2",
    "expr=concentre t=0 objets=appareil-photo,photo-flash",
    "expr=fete t=0 stade=1 objets=polaroid-3",
    "expr=attente t=320 regard_y=-1 objets=enveloppe-notif",
    "expr=attente t=0 regard_y=-1 stade=4 objets=enveloppe-close",
    "expr=fete t=200 marche=1 regard=1 objets=baluchon,epee-bois",
    "expr=grimace t=500 regard=-1 objets=baluchon,pansement",
    "expr=repos t=300 stade=3 objets=torche,bouclier-couvercle,casque-passoire,slime-apprivoise",
]


def pose(ligne):
    kw = {}
    for paire in ligne.split():
        k, _, v = paire.partition("=")
        if k in ("expr", "couleur", "accessoire", "tenue", "reaction"):
            kw[k] = v
        elif k == "objets":
            kw[k] = v.split(",")
        elif k in ("cligne", "clin", "marche", "course", "baille", "etourdi", "fatigue", "salue", "boude", "dos"):
            kw[k] = v == "1"
        elif k in ("regard", "regard_y", "stade"):
            kw[k] = int(v)
        else:
            kw[k] = float(v)
    return rendu.Pose(**kw)


def argb(c):
    if c is None:
        return 0
    c = c.lstrip("#")
    a = int(c[6:8], 16) if len(c) == 8 else 255
    return a << 24 | int(c[:6], 16)


def empreinte(g):
    h = hashlib.sha256()
    for ligne in g:
        for c in ligne:
            h.update(struct.pack(">I", argb(c)))
    return h.hexdigest()


def main():
    B, T, TEN = rendu.banque(), rendu.teintes(), rendu.tenues()
    lignes = ["# pose | sha256 des pixels ARGB (gros-boutiste, ligne par ligne, 48 × 56)"]
    for l in POSES:
        lignes.append("%s | %s" % (l, empreinte(rendu.rendre(pose(l), B, T, TEN))))
    with open(os.path.join(rendu.ICI, "rendus-reference.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lignes) + "\n")
    print(len(POSES), "poses")


if __name__ == "__main__":
    main()
