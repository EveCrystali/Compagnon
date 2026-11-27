"""Dessin fin (2×) : la série des sprites redessinés nativement sur la grille 96 × 112 (assets/sprites2x).

Tout sprite absent de la série est agrandi automatiquement par le rendu (rendu.agrandir, même règle sur le PC et
le téléphone). Pour redessiner un sprite (docs/SPRITES.md, « Redessiner un sprite en 2× ») :

  1. ajouter son identifiant à SERIE : ses fonctions de dessin sont rejouées sur une toile deux fois plus fine
     (ellipses, polygones, lignes et cernes calculés à la finesse double, motifs agrandis par la règle commune) ;
  2. au besoin, lui donner une retouche (@retouche("id")) qui ajoute en pixels fins ce que la grille 1× ne peut
     pas porter : reflets, motifs, plis. Les coordonnées restent celles de la grille 1× (demi-unités permises) ;
  3. python3 outils/sprites/generer.py && python3 outils/sprites/planches_hd.py, regarder, corriger ;
     python3 outils/sprites/reference.py si une pose de référence le porte.

    python3 outils/sprites/fin.py            rapport : sprites redessinés / encore agrandis automatiquement
"""
import os

import toile

# Visage : tout est redessiné (visage_sprites.py). Étincelles de l'antenne, cosmétiques, tenues de voyage : ci-dessous.
SERIE = [
    # Étincelles de l'antenne.
    "etincelle-grand", "etincelle-petit", "etincelle-x", "etincelle-dort", "etincelle-coeur", "etincelle-alerte", "etincelle-roue",
    # Chapeaux.
    "beret", "bonnet-pompon", "chapeau-sorcier", "chapeau-pirate", "haut-de-forme", "chapeau-paille", "casquette",
    "chapeau-explorateur", "couronne-fleurs", "chapeau-melon", "chapeau-cowboy", "acc-bonnet", "acc-couronne", "acc-casque",
    "acc-toque", "tenue-nuit-bonnet", "casque-passoire",
    # Lunettes.
    "lunettes-rondes", "acc-lunettes", "lunettes-coeur", "lunettes-etoiles", "monocle", "lunettes-plage", "masque-plongee",
    "tenue-code-lunettes",
    # Cou et dos.
    "echarpe", "echarpe-tricot", "medaille", "cravate", "foulard-explorateur", "acc-noeud", "cape", "sac-a-dos",
    "sac-explorateur", "astral-cape", "cartable",
    # En main.
    "parapluie", "baluchon", "baguette", "lanterne", "torche", "epee-bois", "bouclier-couvercle", "boussole", "valise",
    "tasse-cafe", "ballon-helium",
    # Compagnons.
    "petit-chat", "petit-poisson-bocal", "oiseau", "slime-apprivoise", "petit-robot", "mini-dragon", "tortue", "escargot",
    # Objets d'expédition.
    "carte-tresor", "coffre-expedition", "pansement", "galette-route", "jus-etoile", "eclat-cristal",
    # Tenues de voyage des campagnes (voyage_sprites.py).
    "voyage-baluchon", "voyage-baton", "voyage-bandeau", "voyage-foulee", "voyage-barque", "voyage-rame", "voyage-vagues",
    "voyage-corde", "voyage-prises", "voyage-bouee", "voyage-brasse", "voyage-couverture", "voyage-lune", "voyage-buisson",
    "voyage-montre",
]

RETOUCHES = {}


def retouche(*ids):
    """Décore une fonction(t, k) appelée pour chaque image k du sprite, avant son écriture en fin."""
    def poser(f):
        def toutes(images):
            for k, t in enumerate(images):
                f(t, k)
            return images
        for i in ids:
            RETOUCHES[i] = toutes
        return f
    return poser


def ids_visage():
    import visage_sprites
    return (["oeil-" + n for n in visage_sprites.YEUX_FINS] + ["oeil-ouvert-g"]
            + ["bouche-" + n for n in visage_sprites.BOUCHES_FINES] + ["marque-" + n for n in visage_sprites.MARQUES_FINES])


def generer(dessiner):
    """Rejoue tous les dessins à l'échelle 2 ; seuls ceux de la série sont écrits (assets/sprites2x, index2x.txt)."""
    import retouches_fines  # noqa: F401  (remplit RETOUCHES)
    toile.ECHELLE = 2
    toile.FINS = set(SERIE) | set(ids_visage())
    toile.RETOUCHES = RETOUCHES
    try:
        dessiner()
    finally:
        toile.ECHELLE = 1
    manquants = sorted(toile.FINS - set(toile.TOUS2))
    assert not manquants, "série fine : identifiants inconnus " + ", ".join(manquants)
    base = os.path.dirname(toile.SORTIE)
    with open(os.path.join(base, "index2x.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# Sprites redessinés en fin (assets/sprites2x) ; les autres sont agrandis automatiquement.\n")
        for k in sorted(toile.TOUS2):
            f.write(k + "\n")


def rapport():
    """(redessinés, automatiques) d'après assets/."""
    base = os.path.dirname(toile.SORTIE)
    tous = sorted(f[:-4] for f in os.listdir(toile.SORTIE) if f.endswith(".txt"))
    fins = set(f[:-4] for f in os.listdir(toile.SORTIE2) if f.endswith(".txt")) if os.path.isdir(toile.SORTIE2) else set()
    return [i for i in tous if i in fins], [i for i in tous if i not in fins]


if __name__ == "__main__":
    natifs, autos = rapport()
    print("Redessinés en fin : %d" % len(natifs))
    print("  " + " ".join(natifs))
    print("Encore agrandis automatiquement : %d" % len(autos))
    print("  " + " ".join(autos))
