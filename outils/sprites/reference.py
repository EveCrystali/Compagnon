"""Empreintes de référence du rendu de Pilou : les tests C# (RenduTests.cs) et JVM (RenduPilouTest.java) doivent
retrouver exactement les mêmes pixels que ce rendu Python, pose par pose, aux deux échelles, et le même
agrandissement automatique de chaque sprite.

    python3 outils/sprites/reference.py  → outils/sprites/rendus-reference.txt (échelle 1),
                                           rendus-reference-2x.txt (rendu fin), agrandis-reference.txt
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
    # Boutique garnie : un ensemble complet et son bonus, teintes chaudes, objets animés sur les autres stades.
    "expr=fete t=420 objets=chapeau-explorateur,jumelles,foulard-explorateur,sac-explorateur,boussole,bottines,bonus-explorateur",
    "expr=inquiet t=0 couleur=cuivre objets=plaid,chocolat-chaud",
    "expr=repos t=660 stade=4 couleur=nebuleuse objets=cape-chauve-souris,coiffe-courge,chauve-souris,bonus-frissons",
    "expr=repos t=250 stade=1 objets=ailes-libellule,lunettes-kaleido,orbite-lunes,bottes-nuage",
    "expr=concentre t=900 stade=3 objets=tricorne-moka,bandeau-oeil,sabre-cuillere,perroquet-caramel,aurore-boreale",
    # Humeurs des campagnes.
    "expr=joie t=350",
    "expr=peur t=420 tremble=0.4",
    "expr=triste t=900",
    "expr=surpris t=150 saut=1.5",
    "expr=determine t=640 regard=1",
    "expr=fatigue t=1200",
    "expr=tendre t=700 stade=3",
    "expr=colere t=350 stade=4",
    "expr=malice t=500 stade=1",
    "expr=neutre t=260 cligne=1",
    "expr=triste t=1300 stade=1 objets=echarpe",
    "expr=peur t=800 couleur=miel objets=lanterne",
    # Tenues de voyage des campagnes (la pose vient du rendu : voyager).
    "expr=repos t=250 tenue=voyage-marche",
    "expr=determine t=410 tenue=voyage-course",
    "expr=joie t=780 tenue=voyage-bateau",
    "expr=determine t=630 tenue=voyage-grimpe stade=3",
    "expr=repos t=1150 tenue=voyage-nage",
    "expr=repos t=2100 tenue=voyage-nuit",
    "expr=peur t=950 tenue=voyage-cache",
    "expr=neutre t=3000 tenue=voyage-attend",
    "expr=neutre t=1700 tenue=voyage-attend stade=4",
    "expr=repos t=330 tenue=voyage-marche stade=1 regard=-1",
    "expr=surpris t=2000 tenue=voyage-cache stade=4",
    # Cosmétiques redessinés en fin, sur chaque stade.
    "expr=repos t=300 objets=chapeau-explorateur,lunettes-rondes,sac-a-dos,parapluie,oiseau",
    "expr=joie t=900 stade=3 objets=bonnet-pompon,echarpe-tricot,cartable,ballon-helium,tortue",
    "expr=malice t=120 stade=4 objets=chapeau-pirate,lunettes-etoiles,medaille,epee-bois,mini-dragon",
    "expr=tendre t=640 stade=1 objets=couronne-fleurs,foulard-explorateur,baguette,escargot",
    # Objets exclusifs des campagnes (campagnes_sprites.py), sur chaque stade.
    "expr=determine t=300 objets=casquette-gardien,sifflet-lison,corne-de-poche,cire-jaune",
    "expr=joie t=500 stade=3 objets=bonnet-de-givre,echarpe-de-veille,caillou-du-col,baluchon-cabosse",
    "expr=malice t=800 stade=4 objets=eteignoir,sablier-de-poche,galet-machoire",
    "expr=tendre t=200 stade=1 objets=casserole-chapeau,plume-de-girouette",
    # Vie du personnage (vie.py) : étirement, antenne en retard, ombre tramée, poussière, lumière du moment.
    "expr=repos t=0 saut=1.2 etire=0.45 antenne=-0.36 vie=1",
    "expr=repos t=0 saut=3 vie=1",
    "expr=repos t=0 etire=-1 antenne=0.72 atterri=40 vie=1",
    "expr=repos t=0 etire=0.38 antenne=-0.3 atterri=130 vie=1 stade=1",
    "expr=joie t=0 etire=-0.6 atterri=200 vie=1 stade=3",
    "expr=fete t=250 saut=2.1 etire=0.3 antenne=0.2 vie=1 stade=4",
    "expr=repos t=170 marche=1 regard=1 vie=1",
    "expr=repos t=250 marche=1 regard=1 vie=1",
    "expr=repos t=500 marche=1 regard=-1 vie=1",
    "expr=repos t=170 marche=1 regard=1 vie=1 stade=1",
    "expr=repos t=90 marche=1 course=1 regard=-1 vie=1",
    "expr=repos t=170 marche=1 regard=1 assis=1 vie=1",
    "expr=repos t=0 lumiere=matin",
    "expr=repos t=0 lumiere=soir couleur=lavande",
    "expr=dort t=2100 lumiere=nuit stade=3",
    "expr=inquiet t=320 lumiere=soir",
    "expr=repos t=0 lumiere=nuit couleur=sable objets=chapeau-explorateur",
]


def pose(ligne):
    kw = {}
    for paire in ligne.split():
        k, _, v = paire.partition("=")
        if k in ("expr", "couleur", "accessoire", "tenue", "reaction", "lumiere"):
            kw[k] = v
        elif k == "objets":
            kw[k] = v.split(",")
        elif k in ("cligne", "clin", "marche", "course", "baille", "etourdi", "fatigue", "salue", "boude", "dos", "vie"):
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


def empreinte_sprite(s):
    """Empreinte d'un sprite agrandi : ses images, ligne par ligne (« --- » entre deux images)."""
    return hashlib.sha256("\n---\n".join("\n".join(im) for im in s.images).encode("utf-8")).hexdigest()


def main():
    B, T, TEN = rendu.banque(), rendu.teintes(), rendu.tenues()
    lignes = ["# pose | sha256 des pixels ARGB (gros-boutiste, ligne par ligne, 48 × 56)"]
    for l in POSES:
        lignes.append("%s | %s" % (l, empreinte(rendu.rendre(pose(l), B, T, TEN))))
    with open(os.path.join(rendu.ICI, "rendus-reference.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lignes) + "\n")
    # Rendu fin (échelle 2) : les mêmes poses sur la grille 96 × 112.
    lignes = ["# pose | sha256 des pixels ARGB du rendu fin (échelle 2, gros-boutiste, ligne par ligne, 96 × 112)"]
    for l in POSES:
        lignes.append("%s | %s" % (l, empreinte(rendu.rendre(pose(l), B, T, TEN, 2))))
    with open(os.path.join(rendu.ICI, "rendus-reference-2x.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lignes) + "\n")
    # Agrandissement automatique : chaque sprite 1× agrandi par la règle commune (rendu.agrandir).
    lignes = ["# sprite | sha256 du sprite 1× agrandi (lignes de lettres, « --- » entre deux images)"]
    for i in sorted(B):
        lignes.append("%s | %s" % (i, empreinte_sprite(rendu.agrandir(B[i]))))
    with open(os.path.join(rendu.ICI, "agrandis-reference.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lignes) + "\n")
    # Animations des campagnes : les règles communes (animations.py) ; relues par le PC et le téléphone.
    import animations
    animations.ecrire_reference()
    # La police pixel : mise en page et pixels de vrais textes (police-reference.txt).
    import police
    police.reference()
    # Vie du personnage : les règles communes (vie.py) ; relues par le PC et le téléphone.
    import vie
    vie.ecrire_reference()
    print(len(POSES), "poses, deux échelles ;", len(B), "sprites agrandis ; animations-reference.txt ; vie-reference.txt ; police-reference.txt")


if __name__ == "__main__":
    main()
