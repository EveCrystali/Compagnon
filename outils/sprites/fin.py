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



# Seconde série : boutique garnie, tenues d'activité, météo, créatures et trophées d'expédition. Chacun est rejoué en
# fin ; s'il est fait de pixels posés à la main (le rejeu ne serait qu'un agrandissement au plus proche voisin), sa
# base est l'agrandissement commun (rendu.agrandir_image). Puis la retouche ajoute liserés, ombres et reflets
# (retouches_fines.retouche_auto, ou une recette de RETOUCHES_SIMPLES).
SERIE2 = [
    "ailes-libellule", "ailes-nuage", "ailes-papillon", "antenne-neon", "aura", "aura-feu", "aureole",
    "aurore-boreale", "bandana", "bandeau-eponge", "bandeau-ninja", "bandeau-oeil", "baskets", "bonhomme-neige",
    "bonnet-lune", "bonnet-lutin", "bonnet-oreillettes", "bottes-jardin", "bottes-nuage", "bottes-pluie",
    "bottines", "canne", "canne-doree", "canne-or", "cape-chauve-souris", "cape-constellation", "casque-chantier",
    "casquette-pixel", "cerf-volant", "chapeau-champi", "chapeau-plage", "chaussettes-rayees", "chaussons-creme",
    "chaussons-moumoute", "chauve-souris", "chocolat-chaud", "coiffe-courge", "collier-comete",
    "collier-coquillages", "collier-perles", "cornes-viking", "couronne-cristal", "couronne-laurier",
    "crea-bug-geant", "crea-gargouille-latence", "crea-golem-tickets", "crea-hydre-dependances", "crea-slime-cache",
    "crea-spectre-404", "epee-mousse", "eventail", "fantome", "foulard-vichy", "guitare", "herisson",
    "hotte-cadeaux", "impermeable", "jetpack", "jumelles", "livre", "loupe", "luciole", "lunettes-3d",
    "lunettes-kaleido", "lunettes-loupe", "lunettes-pixel", "lunettes-ski", "mariniere", "masque-loup",
    "masque-sommeil", "meduse", "meteo-averse", "meteo-brouillard", "meteo-eclair", "meteo-givre", "meteo-mouille",
    "meteo-neige", "meteo-pluie", "meteo-soleil", "meteo-vent", "micro", "mini-goutte", "mini-planete", "moufles",
    "noeud-geant", "noeud-pois", "ombrelle", "oreilles-chat", "palmes", "panier-dos", "pantoufles-lapin",
    "parapluie-etoile", "patins", "pendentif-goutte", "perroquet-caramel", "petit-crabe", "phenix", "plaid",
    "renne", "rollers", "sabots", "sabre-cuillere", "sombrero", "souffleur-bulles", "telescope",
    "tenue-code-clavier", "tenue-dessin-beret", "tenue-dessin-palette", "tenue-diaporama-pointeur",
    "tenue-jeu-casque", "tenue-jeu-manette", "tenue-lecture-livre", "tenue-lecture-lunettes",
    "tenue-mail-casquette", "tenue-mail-enveloppe", "tenue-mmo-bouclier", "tenue-mmo-epee",
    "tenue-musique-ecouteurs", "tenue-musique-notes", "tenue-tableur-calculatrice", "tenue-tableur-lunettes",
    "tenue-texte-plume", "tenue-video-popcorn", "tenue-visio-micro", "tongs", "toque-myrtille", "tricorne-moka",
    "trophee-bug-geant", "trophee-gargouille-latence", "trophee-golem-tickets", "trophee-hydre-dependances",
    "trophee-slime-cache", "visiere-pilote",
]


# Troisième série : fonds de boutique, prises et plats, défense du bureau, variantes, gestes, bonus, en-cas, soins,
# objets d'interface. Même mécanique que la seconde (base fine, puis finition.py : lumière commune + détails propres).
SERIE3 = [
    "encas-croquettes", "encas-gateau", "encas-pomme", "encas-soupe", "plat-assiette", "plat-bol", "plat-brochette",
    "plat-friture", "plat-invente", "plat-papillote", "plat-plateau", "plat-poelon", "plat-ramen", "plat-rate",
    "plat-souffle", "plat-sushi", "plat-tarte", "plat-tartine", "prise-ablette", "prise-algue", "prise-anguille",
    "prise-baleineau", "prise-botte", "prise-bouteille", "prise-caillou", "prise-carpe", "prise-cle",
    "prise-coffre", "prise-comete", "prise-crabe", "prise-ecrevisse", "prise-goujon", "prise-hippocampe",
    "prise-lanterne", "prise-perche", "prise-perle", "prise-pieuvre", "prise-raie", "prise-saumon", "prise-spirale",
    "prise-truite", "soin-faim", "soin-moral", "soin-proprete", "fond-arcade", "fond-aurore", "fond-automne",
    "fond-bibliotheque", "fond-cerisiers", "fond-espace", "fond-fetes", "fond-foret", "fond-frissons",
    "fond-mer-cafe", "fond-montagne", "fond-nuit", "fond-observatoire", "fond-patisserie", "fond-plage",
    "fond-potager", "fond-ville", "bug-araignee", "bug-prod", "bug-scarabee", "bug-ver", "defense-blinde",
    "defense-blinde-fele", "defense-bonus-bouclier", "defense-bonus-double", "defense-bonus-ralenti",
    "defense-diviseur", "defense-etincelle", "defense-mini", "defense-rapide", "defense-tir"
]


# Quatrième série : ce qui restait agrandi automatiquement (variantes, poufs, polaroïds, bonus d'ensemble, icônes,
# accessoires, particules). Dessin fin propre à chaque sprite (finition_lot3.py), sans finition générique.
SERIE4 = [
    "acc-chapeaupeche", "acc-etoilemer", "acc-feuille", "acc-tablier", "appareil-photo", "arrosoir", "badge-boutique",
    "ballon", "bonus-arcade", "bonus-astronome", "bonus-cafe", "bonus-explorateur", "bonus-fetes", "bonus-frissons",
    "bonus-hiver", "bonus-jardinier", "bonus-patissier", "bonus-pirate", "bonus-plage", "bonus-tests", "bouchon",
    "boude-bras", "boude-eclaircie", "boude-nuage", "bulle", "bulles-savon", "cadenas", "carapace", "cercle-glyphes",
    "clavier-mini", "clochette", "coeurs-amitie", "coffre-expedition-ouvert", "coffre-quete", "confettis",
    "cube-pixel", "eclaboussure", "eclair-energie", "enveloppe-close", "enveloppe-notif", "etincelles", "etoile",
    "feu", "feuilles-tourbillon", "fouet", "fourchette-geante", "guirlande", "jeton-arcade", "lampe-poche",
    "lanterne-courge", "macaron", "main", "manette", "marmite", "marmite-cuivre", "mousse", "nid-oiseau",
    "orbite-lunes", "pancarte", "parchemin-quete", "pelle-seau", "photo-flash", "pierre-calme", "pinceau",
    "pluie-petales", "po", "po-tourne", "polaroid-1", "polaroid-2", "polaroid-3", "polaroid-4", "pouf-1", "pouf-2",
    "pouf-3", "pouf-4", "pouf-5", "rayonnant", "sucette", "sucre-orge", "trainee-coeurs", "trainee-notes",
    "trainee-prisme", "vapeur", "variante-calin-2", "variante-calin-2-tete", "variante-calin-3",
    "variante-calin-3-tete", "variante-calin-4", "variante-calin-4-tete", "variante-espiegle-2",
    "variante-espiegle-2-tete", "variante-espiegle-3", "variante-espiegle-3-tete", "variante-espiegle-4",
    "variante-espiegle-4-tete", "vie",
]


def ids_campagnes():
    """Décors, objets exclusifs, souvenirs, vignettes et emblèmes des campagnes : tous dessinés nativement en fin."""
    import campagnes_sprites
    import decors_campagnes
    decors_campagnes.charger()
    return sorted(decors_campagnes.DECORS) + list(campagnes_sprites.IDS)


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
    import finition
    finition.inscrire()
    toile.ECHELLE = 2
    toile.FINS = set(SERIE) | set(SERIE2) | set(SERIE3) | set(SERIE4) | set(ids_visage()) | set(ids_campagnes())
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
