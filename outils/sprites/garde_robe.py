"""Boutique garnie : les articles ajoutés au catalogue d'origine, leurs ensembles, saisons et paliers de collection.

Appelé par generer.py. Écrit assets/catalogue.txt, lu tel quel par le PC (Boutique.cs) et par l'app Android
(Boutique.java) : même source, même ordre, mêmes prix. Les dessins sont dans garde_robe_dessins.py.

Numéros : chaque article garde son numéro pour toujours (la synchronisation entre appareils envoie l'inventaire
comme une suite de bits indexée par ces numéros) ; un nouvel article prend le numéro suivant, un article retiré
laisse un trou. Raretés : 0 commun · 1 peu commun · 2 rare · 3 épique · 4 légendaire · 5 mythique.
Saisons : hiver (déc.–fév.), printemps (mars–mai), ete (juin–août), automne (sept.–nov.), frissons (15 oct.–5 nov.),
fetes (10 déc.–6 janv.) ; hors saison, l'article reste visible mais ne s'achète pas.
Passage : l'article ne s'achète que les quelques jours du mois où il passe en vitrine.
"""
import os

import garde_robe_dessins

C, PC, R, E, L, M = 0, 1, 2, 3, 4, 5

# (n°, id, nom, emplacement, prix, niveau, rareté, saison, ensemble, passage)
ARTICLES = [
    # ---- Explorateur
    (1, "chapeau-explorateur", "Casque d'explorateur", "tete", 90, 1, PC, "", "explorateur", False),
    (2, "jumelles", "Jumelles", "yeux", 70, 1, C, "", "explorateur", False),
    (3, "foulard-explorateur", "Foulard d'explorateur", "cou", 50, 1, C, "", "explorateur", False),
    (4, "sac-explorateur", "Sac d'expédition", "dos", 140, 5, PC, "", "explorateur", False),
    (5, "boussole", "Boussole", "main", 110, 5, PC, "", "explorateur", False),
    (6, "bottines", "Bottines de marche", "pieds", 140, 10, R, "", "explorateur", False),
    # ---- Pâtissier
    (7, "toque-myrtille", "Toque à la myrtille", "tete", 100, 1, PC, "", "patissier", False),
    (8, "foulard-vichy", "Foulard vichy", "cou", 60, 1, C, "", "patissier", False),
    (9, "fouet", "Fouet", "main", 60, 1, C, "", "patissier", False),
    (10, "chaussons-creme", "Chaussons crème", "pieds", 90, 5, PC, "", "patissier", False),
    (11, "macaron", "Macaron vivant", "compagnon", 230, 10, R, "", "patissier", False),
    (12, "fond-patisserie", "Décor pâtisserie", "fond", 250, 15, E, "", "patissier", False),
    # ---- Astronome
    (13, "bonnet-lune", "Bonnet lune", "tete", 140, 5, PC, "", "astronome", False),
    (14, "lunettes-etoiles", "Lunettes étoiles", "yeux", 140, 10, R, "", "astronome", False),
    (15, "telescope", "Lunette astronomique", "main", 230, 15, R, "", "astronome", False),
    (16, "cape-constellation", "Cape constellation", "dos", 290, 20, E, "", "astronome", False),
    (17, "mini-planete", "Mini-planète", "compagnon", 390, 30, E, "", "astronome", False),
    (18, "fond-observatoire", "Décor observatoire", "fond", 660, 30, L, "", "astronome", False),
    # ---- Pirate des mers de café
    (19, "bandeau-oeil", "Bandeau d'œil", "yeux", 70, 5, C, "", "pirate", False),
    (20, "mariniere", "Col marin", "cou", 100, 5, PC, "", "pirate", False),
    (21, "tricorne-moka", "Tricorne moka", "tete", 170, 10, R, "", "pirate", False),
    (22, "sabre-cuillere", "Sabre-cuillère", "main", 180, 10, R, "", "pirate", False),
    (23, "perroquet-caramel", "Perroquet caramel", "compagnon", 330, 20, E, "", "pirate", False),
    (24, "fond-mer-cafe", "Décor mer de café", "fond", 430, 30, E, "", "pirate", False),
    # ---- Jardinier
    (25, "chapeau-paille", "Chapeau de paille", "tete", 60, 1, C, "", "jardinier", False),
    (26, "bottes-jardin", "Bottes de jardin", "pieds", 70, 1, C, "", "jardinier", False),
    (27, "arrosoir", "Arrosoir", "main", 80, 1, PC, "", "jardinier", False),
    (28, "panier-dos", "Hotte de légumes", "dos", 140, 5, PC, "", "jardinier", False),
    (29, "escargot", "Escargot", "compagnon", 180, 10, R, "", "jardinier", False),
    (30, "fond-potager", "Décor potager", "fond", 200, 10, R, "", "jardinier", False),
    # ---- Rétro-arcade (avec le décor salle d'arcade du catalogue d'origine)
    (31, "jeton-arcade", "Jeton d'arcade", "cou", 80, 5, PC, "", "arcade", False),
    (32, "casquette-pixel", "Casquette pixel", "tete", 120, 5, PC, "", "arcade", False),
    (33, "lunettes-pixel", "Lunettes pixel", "yeux", 130, 10, R, "", "arcade", False),
    (34, "manette", "Manette", "main", 200, 15, R, "", "arcade", False),
    (35, "cube-pixel", "Cube pixel", "compagnon", 310, 20, E, "", "arcade", False),
    # ---- Hiver douillet (hiver)
    (36, "chocolat-chaud", "Chocolat chaud", "main", 60, 1, C, "hiver", "hiver", False),
    (37, "echarpe-tricot", "Grande écharpe tricotée", "cou", 90, 1, PC, "hiver", "hiver", False),
    (38, "bonnet-oreillettes", "Bonnet à oreillettes", "tete", 100, 1, PC, "hiver", "hiver", False),
    (39, "chaussons-moumoute", "Chaussons moumoute", "pieds", 130, 5, PC, "hiver", "hiver", False),
    (40, "plaid", "Plaid", "dos", 140, 5, R, "hiver", "hiver", False),
    (41, "bonhomme-neige", "Petit bonhomme de neige", "compagnon", 290, 15, E, "hiver", "hiver", False),
    # ---- Plage (été ; avec le décor plage du catalogue d'origine)
    (42, "tongs", "Tongs", "pieds", 40, 1, C, "ete", "plage", False),
    (43, "pelle-seau", "Seau et pelle", "main", 50, 1, C, "ete", "plage", False),
    (44, "lunettes-plage", "Lunettes de plage", "yeux", 60, 1, C, "ete", "plage", False),
    (45, "chapeau-plage", "Chapeau de plage", "tete", 100, 1, PC, "ete", "plage", False),
    (46, "collier-coquillages", "Collier de coquillages", "cou", 110, 5, PC, "ete", "plage", False),
    # ---- Nuit des frissons (15 oct. – 5 nov.)
    (47, "masque-loup", "Loup de bal", "yeux", 140, 5, PC, "frissons", "frissons", False),
    (48, "coiffe-courge", "Coiffe courge", "tete", 140, 5, R, "frissons", "frissons", False),
    (49, "lanterne-courge", "Lanterne-courge", "main", 160, 5, R, "frissons", "frissons", False),
    (50, "cape-chauve-souris", "Cape chauve-souris", "dos", 260, 10, E, "frissons", "frissons", False),
    (51, "chauve-souris", "Chauve-souris", "compagnon", 320, 15, E, "frissons", "frissons", False),
    (52, "fond-frissons", "Décor nuit des frissons", "fond", 400, 20, E, "frissons", "frissons", False),
    # ---- Fêtes de l'hiver (10 déc. – 6 janv.)
    (53, "sucre-orge", "Sucre d'orge", "main", 50, 1, C, "fetes", "fetes", False),
    (54, "bonnet-lutin", "Bonnet de lutin", "tete", 110, 1, PC, "fetes", "fetes", False),
    (55, "guirlande", "Guirlande lumineuse", "cou", 130, 5, R, "fetes", "fetes", False),
    (56, "hotte-cadeaux", "Hotte de cadeaux", "dos", 240, 10, E, "fetes", "fetes", False),
    (57, "renne", "Petit renne", "compagnon", 370, 20, E, "fetes", "fetes", False),
    (58, "fond-fetes", "Décor village en fête", "fond", 630, 30, L, "fetes", "fetes", False),
    # ---- Tête
    (59, "bandeau-eponge", "Bandeau éponge", "tete", 30, 1, C, "", "", False),
    (60, "chapeau-melon", "Chapeau melon", "tete", 100, 5, PC, "", "", False),
    (61, "chapeau-champi", "Chapeau champignon", "tete", 160, 10, R, "", "", False),
    (62, "nid-oiseau", "Nid d'oiseau", "tete", 310, 20, E, "", "", True),
    (63, "couronne-cristal", "Couronne de cristal", "tete", 1620, 50, M, "", "", True),
    # ---- Yeux
    (64, "masque-sommeil", "Masque de sommeil", "yeux", 40, 1, C, "", "", False),
    (65, "lunettes-loupe", "Lunettes-loupes", "yeux", 80, 5, PC, "", "", False),
    (66, "lunettes-ski", "Masque de ski", "yeux", 130, 10, R, "hiver", "", False),
    (67, "lunettes-kaleido", "Lunettes kaléidoscope", "yeux", 400, 30, E, "", "", True),
    # ---- Cou
    (68, "clochette", "Clochette", "cou", 40, 1, C, "", "", False),
    (69, "pendentif-goutte", "Pendentif goutte", "cou", 120, 5, PC, "", "", False),
    (70, "noeud-geant", "Nœud géant", "cou", 170, 15, R, "", "", False),
    (71, "collier-comete", "Collier comète", "cou", 740, 40, L, "", "", False),
    # ---- Dos
    (72, "bouclier-couvercle", "Bouclier-couvercle", "dos", 70, 1, PC, "", "", False),
    (73, "cerf-volant", "Cerf-volant", "dos", 190, 10, R, "printemps", "", False),
    (74, "ailes-libellule", "Ailes de libellule", "dos", 630, 30, L, "", "", True),
    (75, "ailes-nuage", "Ailes de nuage", "dos", 980, 40, L, "", "", False),
    # ---- Main
    (76, "loupe", "Loupe", "main", 40, 1, C, "", "", False),
    (77, "souffleur-bulles", "Souffleur de bulles", "main", 50, 1, C, "", "", False),
    (78, "pinceau", "Pinceau", "main", 70, 1, C, "", "", False),
    (79, "livre", "Livre ouvert", "main", 90, 5, PC, "", "", False),
    (80, "lampe-poche", "Lampe de poche", "main", 100, 5, PC, "", "", False),
    (81, "fourchette-geante", "Fourchette géante", "main", 140, 10, R, "", "", False),
    (82, "ombrelle", "Ombrelle", "main", 140, 10, R, "printemps", "", False),
    (83, "micro", "Micro", "main", 220, 15, R, "", "", False),
    # ---- Pieds
    (84, "chaussettes-rayees", "Chaussettes rayées", "pieds", 30, 1, C, "", "", False),
    (85, "sabots", "Sabots", "pieds", 70, 1, C, "", "", False),
    (86, "pantoufles-lapin", "Pantoufles lapin", "pieds", 140, 10, R, "", "", False),
    (87, "rollers", "Rollers", "pieds", 250, 20, E, "", "", False),
    (88, "bottes-nuage", "Bottes-nuages", "pieds", 770, 40, L, "", "", False),
    # ---- Compagnons
    (89, "luciole", "Luciole", "compagnon", 130, 5, R, "ete", "", False),
    (90, "petit-crabe", "Petit crabe", "compagnon", 160, 5, R, "ete", "", False),
    (91, "herisson", "Hérisson", "compagnon", 200, 10, R, "automne", "", False),
    (92, "tortue", "Tortue", "compagnon", 240, 15, E, "", "", False),
    (93, "mini-goutte", "Gouttinette", "compagnon", 360, 20, E, "", "", False),
    (94, "meduse", "Méduse céleste", "compagnon", 800, 30, L, "", "", True),
    (95, "phenix", "Phénix de braise", "compagnon", 1870, 50, M, "", "", True),
    # ---- Effets
    (96, "etincelles", "Étincelles", "effet", 80, 1, C, "", "", False),
    (97, "pluie-petales", "Pluie de pétales", "effet", 170, 5, R, "printemps", "", False),
    (98, "feuilles-tourbillon", "Tourbillon de feuilles", "effet", 170, 5, R, "automne", "", False),
    (99, "cercle-glyphes", "Cercle de glyphes", "effet", 440, 30, E, "", "", True),
    (100, "aurore-boreale", "Aurore boréale", "effet", 910, 40, L, "", "", False),
    (101, "orbite-lunes", "Orbite de lunes", "effet", 1780, 50, M, "", "", True),
    # ---- Couleurs (teintes de Pilou)
    (102, "turquoise", "Couleur turquoise", "couleur", 140, 1, PC, "", "", False),
    (103, "caramel", "Couleur caramel", "couleur", 180, 5, PC, "", "", False),
    (104, "givre", "Couleur givre", "couleur", 160, 5, R, "hiver", "", False),
    (105, "potiron", "Couleur potiron", "couleur", 160, 5, R, "frissons", "", False),
    (106, "lilas", "Couleur lilas", "couleur", 170, 10, R, "printemps", "", False),
    (107, "cuivre", "Couleur cuivre", "couleur", 240, 20, E, "", "", False),
    (108, "minuit", "Couleur minuit", "couleur", 310, 30, E, "", "", False),
    (109, "opale", "Couleur opale", "couleur", 800, 40, L, "", "", False),
    (110, "nebuleuse", "Couleur nébuleuse", "couleur", 1700, 50, M, "", "", True),
    # ---- Décors
    (111, "fond-montagne", "Décor montagne", "fond", 180, 5, PC, "", "", False),
    (112, "fond-bibliotheque", "Décor bibliothèque", "fond", 190, 10, R, "", "", False),
    (113, "fond-ville", "Décor ville la nuit", "fond", 240, 15, R, "", "", False),
    (114, "fond-cerisiers", "Décor cerisiers", "fond", 260, 10, E, "printemps", "", False),
    (115, "fond-automne", "Décor sous-bois d'automne", "fond", 260, 10, E, "automne", "", False),
    (116, "fond-aurore", "Décor aurore", "fond", 880, 40, L, "", "", True),
    # ---- Cadres de bulle
    (117, "bulle-bois", "Bulle en bois", "bulle", 70, 1, C, "", "", False),
    (118, "bulle-lagon", "Bulle lagon", "bulle", 100, 1, PC, "", "", False),
    (119, "bulle-parchemin", "Bulle parchemin", "bulle", 140, 5, PC, "", "", False),
    (120, "bulle-givre", "Bulle de givre", "bulle", 140, 5, R, "hiver", "", False),
    (121, "bulle-guirlande", "Bulle guirlande", "bulle", 160, 5, R, "fetes", "", False),
    (122, "bulle-ronde", "Bulle toute ronde", "bulle", 130, 10, R, "", "", False),
    (123, "bulle-encre", "Bulle d'encre", "bulle", 180, 15, R, "", "", False),
    (124, "bulle-ambre", "Bulle d'ambre", "bulle", 240, 20, E, "", "", False),
    (125, "bulle-cristal", "Bulle de cristal", "bulle", 660, 40, L, "", "", True),
    # ---- Titres affichés (nouvel emplacement : sous le nom de Pilou, dans le bandeau)
    (126, "titre-reveur", "« Rêveur »", "titre", 30, 1, C, "", "", False),
    (127, "titre-gourmand", "« Gourmand »", "titre", 30, 1, C, "", "", False),
    (128, "titre-curieux", "« Petit curieux »", "titre", 40, 1, C, "", "", False),
    (129, "titre-siesteur", "« Siesteur pro »", "titre", 40, 1, C, "", "", False),
    (130, "titre-pecheur", "« Pêcheur du dimanche »", "titre", 50, 1, C, "", "", False),
    (131, "titre-codeur", "« Codeur nocturne »", "titre", 50, 1, C, "", "", False),
    (132, "titre-cafe", "« Accro au café »", "titre", 60, 1, C, "", "", False),
    (133, "titre-matinal", "« Lève-tôt »", "titre", 80, 5, PC, "", "", False),
    (134, "titre-zen", "« Zen absolu »", "titre", 100, 5, PC, "", "", False),
    (135, "titre-flocon", "« Flocon de neige »", "titre", 100, 1, PC, "hiver", "", False),
    (136, "titre-frissons", "« Âme frissonnante »", "titre", 130, 1, PC, "frissons", "", False),
    (137, "titre-artiste", "« Artiste incompris »", "titre", 120, 10, PC, "", "", False),
    (138, "titre-aventurier", "« Aventurier du clavier »", "titre", 160, 15, R, "", "", False),
    (139, "titre-sage", "« Sage des nuages »", "titre", 260, 30, E, "", "", False),
    (140, "titre-legende", "« Légende vivante »", "titre", 770, 50, L, "", "", False),
]

# Ensembles : (id, nom, signe, pièces, bonus porté (sprite), titre gagné quand l'ensemble est complet).
ENSEMBLES = [
    ("explorateur", "Explorateur", "⌖",
     ["chapeau-explorateur", "jumelles", "foulard-explorateur", "sac-explorateur", "boussole", "bottines"],
     "bonus-explorateur", "« Grand explorateur »"),
    ("patissier", "Pâtissier", "◒",
     ["toque-myrtille", "foulard-vichy", "fouet", "chaussons-creme", "macaron", "fond-patisserie"],
     "bonus-patissier", "« Maître pâtissier »"),
    ("astronome", "Astronome", "☾",
     ["bonnet-lune", "lunettes-etoiles", "telescope", "cape-constellation", "mini-planete", "fond-observatoire"],
     "bonus-astronome", "« Liseur d'étoiles »"),
    ("pirate", "Pirate des mers de café", "⚓",
     ["tricorne-moka", "bandeau-oeil", "mariniere", "sabre-cuillere", "perroquet-caramel", "fond-mer-cafe"],
     "bonus-pirate", "« Capitaine Moka »"),
    ("jardinier", "Jardinier", "❀",
     ["chapeau-paille", "arrosoir", "panier-dos", "bottes-jardin", "escargot", "fond-potager"],
     "bonus-jardinier", "« Jardinier émérite »"),
    ("arcade", "Rétro-arcade", "▣",
     ["casquette-pixel", "lunettes-pixel", "jeton-arcade", "manette", "cube-pixel", "fond-arcade"],
     "bonus-arcade", "« Champion 8 bits »"),
    ("hiver", "Hiver douillet", "❄",
     ["bonnet-oreillettes", "echarpe-tricot", "chocolat-chaud", "plaid", "chaussons-moumoute", "bonhomme-neige"],
     "bonus-hiver", "« Douillet de l'hiver »"),
    ("plage", "Plage", "☼",
     ["chapeau-plage", "lunettes-plage", "collier-coquillages", "pelle-seau", "tongs", "fond-plage"],
     "bonus-plage", "« Roi du sable »"),
    ("frissons", "Nuit des frissons", "☽",
     ["coiffe-courge", "masque-loup", "cape-chauve-souris", "lanterne-courge", "chauve-souris", "fond-frissons"],
     "bonus-frissons", "« Frissonnant »"),
    ("fetes", "Fêtes de l'hiver", "✶",
     ["bonnet-lutin", "guirlande", "sucre-orge", "hotte-cadeaux", "renne", "fond-fetes"],
     "bonus-fetes", "« Lutin des fêtes »"),
]

# Paliers de collection : (nombre d'articles possédés — 0 : tout le catalogue —, id, emplacement, nom). Rien en po.
PALIERS = [
    (10, "titre-col-herbe", "titre", "« Collectionneur en herbe »"),
    (25, "cadre-bronze", "bulle", "Cadre bronze"),
    (50, "titre-col-connaisseur", "titre", "« Fin connaisseur »"),
    (80, "cadre-argent", "bulle", "Cadre argent"),
    (120, "titre-col-grand", "titre", "« Grand collectionneur »"),
    (160, "cadre-or", "bulle", "Cadre or"),
    (200, "titre-col-musee", "titre", "« Conservateur du musée »"),
    (0, "cadre-prisme", "bulle", "Cadre prisme"),
]

# Nouvelles teintes : contour, ombre, base, clair (jamais d'opposition rouge / vert).
TEINTES = {
    "turquoise": ["#0f4a63", "#2689b8", "#3fb8e0", "#bfeaf7"],
    "caramel": ["#5e3410", "#a8652a", "#d99a52", "#f6d2a2"],
    "givre": ["#3a5a7a", "#8fb4d8", "#d6ecff", "#ffffff"],
    "potiron": ["#6e3208", "#c4621a", "#f08a2c", "#ffd0a0"],
    "lilas": ["#4a3a7a", "#8a72c8", "#b9a4ee", "#ece4ff"],
    "cuivre": ["#5a2a12", "#a3532a", "#d07a45", "#f3c2a0"],
    "minuit": ["#120f33", "#2e2a6e", "#46429e", "#9c98e0"],
    "opale": ["#5a6290", "#a9b6e0", "#e6ecff", "#fff6cc"],
    "nebuleuse": ["#2a1450", "#5a3aa8", "#8f6fe0", "#c6f0ff"],
}
CHAUDES = ["caramel", "potiron", "cuivre"]


def verifier():
    ids = [a[1] for a in ARTICLES]
    nums = [a[0] for a in ARTICLES]
    assert len(set(ids)) == len(ids), "identifiant en double"
    assert len(set(nums)) == len(nums), "numéro en double"
    for a in ARTICLES:
        assert "|" not in a[2]
        if a[3] not in ("couleur", "bulle", "titre"):
            assert a[1] in garde_robe_dessins.DESSINS, "pas de dessin : " + a[1]
        if a[3] == "couleur":
            assert a[1] in TEINTES, a[1]
    for e in ENSEMBLES:
        assert e[4] in garde_robe_dessins.DESSINS, e[4]
        slots = [next((a[3] for a in ARTICLES if a[1] == p), "fond") for p in e[3]]
        assert len(set(slots)) == len(slots), "deux pièces au même emplacement : " + e[0]


def ecrire_catalogue(base):
    verifier()
    lignes = [
        "# Boutique garnie (outils/sprites/garde_robe.py) : lu par Boutique.cs et Boutique.java.",
        "# article|n°|id|nom|emplacement|prix|niveau|rareté 0-5|saison|ensemble|passage",
        "# ensemble|id|nom|signe|bonus|titre|pièces…",
        "# palier|nombre (0 : tout)|id|emplacement|nom",
    ]
    for n, id_, nom, slot, prix, niv, rar, saison, ens, passage in ARTICLES:
        lignes.append("article|%d|%s|%s|%s|%d|%d|%d|%s|%s|%d" % (n, id_, nom, slot, prix, niv, rar, saison, ens, 1 if passage else 0))
    for id_, nom, signe, pieces, bonus, titre in ENSEMBLES:
        lignes.append("ensemble|%s|%s|%s|%s|%s|%s" % (id_, nom, signe, bonus, titre, "|".join(pieces)))
    for nombre, id_, slot, nom in PALIERS:
        lignes.append("palier|%d|%s|%s|%s" % (nombre, id_, slot, nom))
    with open(os.path.join(base, "catalogue.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lignes) + "\n")


def objets():
    garde_robe_dessins.tout()
