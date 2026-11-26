"""Planches PNG de contrôle : chaque sprite doit se reconnaître sans légende.

    python3 outils/sprites/planches.py [dossier]
"""
import os
import sys

from PIL import Image, ImageDraw

import rendu

FOND = (28, 33, 40)
FOND2 = (238, 242, 246)


def rgba(c):
    c = c.lstrip("#")
    if len(c) == 6:
        return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4, 6))


def grille_image(g, z):
    h, w = len(g), len(g[0])
    im = Image.new("RGBA", (w * z, h * z), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for y in range(h):
        for x in range(w):
            if g[y][x]:
                d.rectangle([x * z, y * z, x * z + z - 1, y * z + z - 1], fill=rgba(g[y][x]))
    return im


def sprite_image(s, z, k=0):
    im = s.images[k]
    w = max(len(l) for l in im)
    g = [[None] * w for _ in im]
    for j, l in enumerate(im):
        for i, ch in enumerate(l):
            if ch != ".":
                c = s.palette.get(ch)
                c = {"@contour": "#1f4f8a", "@ombre": "#4a8fdc", "@base": "#6cb6ff", "@clair": "#b4dbff"}.get(c, c)
                g[j][i] = c
    return grille_image(g, z)


def planche(cases, colonnes, case, fond, chemin, titre_h=0):
    lignes = (len(cases) + colonnes - 1) // colonnes
    W, H = case[0] * colonnes, case[1] * lignes
    out = Image.new("RGBA", (W, H), fond + (255,))
    d = ImageDraw.Draw(out)
    for i, (im, nom) in enumerate(cases):
        cx, cy = (i % colonnes) * case[0], (i // colonnes) * case[1]
        ox = cx + (case[0] - im.width) // 2
        oy = cy + (case[1] - 16 - im.height) // 2
        out.alpha_composite(im, (max(cx, ox), max(cy, oy)))
        d.text((cx + 4, cy + case[1] - 14), nom, fill=(150, 160, 170) if fond == FOND else (80, 90, 100))
    out.save(chemin)
    print(chemin, out.size)


def catalogue_garni():
    """Articles de la boutique garnie (assets/catalogue.txt) : [(id, nom, emplacement, ensemble)] et ensembles."""
    articles, ensembles = [], []
    with open(os.path.join(rendu.ASSETS, "catalogue.txt"), encoding="utf-8") as f:
        for ligne in f:
            c = ligne.rstrip("\n").split("|")
            if c[0] == "article":
                articles.append((c[2], c[3], c[4], c[9]))
            elif c[0] == "ensemble":
                ensembles.append((c[1], c[2], c[4], c[6:]))
    return articles, ensembles


def garnie(dossier, B, T, TEN, z=4):
    os.makedirs(dossier, exist_ok=True)
    """Planches de la boutique garnie, une par rayon, plus les ensembles complets (bonus compris) et les stades."""
    def pilou(**kw):
        return grille_image(rendu.rendre(rendu.Pose(**kw), B, T, TEN), z)

    articles, ensembles = catalogue_garni()
    case = (48 * z + 8, 56 * z + 20)
    for slot in ("tete", "yeux", "cou", "dos", "main", "pieds", "compagnon", "effet", "couleur"):
        ids = [a[0] for a in articles if a[2] == slot]
        if slot == "couleur":
            cases = [(pilou(couleur=i), i) for i in ids] + [(pilou(couleur=i, expr="inquiet"), i + " inquiet") for i in ids[:3]]
        else:
            cases = [(pilou(objets=[i], t=300), i) for i in ids] + [(pilou(objets=[i], t=660), i + " ·2") for i in ids
                                                                   if len(B[i].images) > 1][:4]
        planche(cases, 7, case, FOND, os.path.join(dossier, "rayon-%s.png" % slot))
    fonds = [a[0] for a in articles if a[2] == "fond"]
    cases = []
    for f in fonds:
        im = sprite_image(B[f], 4)
        p = grille_image(rendu.rendre(rendu.Pose(), B, T, TEN), 3)
        im.alpha_composite(p, ((im.width - p.width) // 2, im.height - p.height - 4))
        cases.append((im, f))
    planche(cases, 4, (64 * 4 + 12, 48 * 4 + 24), FOND, os.path.join(dossier, "rayon-fond.png"))
    # Vignettes à la taille de la boutique (1,5 px par pixel) : reconnaissables sans légende ?
    petites = [(grille_image(rendu.rendre(rendu.Pose(objets=[a[0]], t=300), B, T, TEN), 2), a[0]) for a in articles
               if a[2] not in ("couleur", "fond", "bulle", "titre")]
    planche(petites, 12, (48 * 2 + 30, 56 * 2 + 20), FOND, os.path.join(dossier, "vignettes-petites.png"))
    # Ensembles complets, portés ensemble, avec leur bonus (et le décor de l'ensemble derrière).
    cases = []
    for id_, nom, bonus, pieces in ensembles:
        objets = [p for p in pieces if p in B and not p.startswith("fond-")] + [bonus]
        im = sprite_image(B[next((p for p in pieces if p.startswith("fond-")), "fond-montagne")], 4)
        p = grille_image(rendu.rendre(rendu.Pose(objets=objets, t=420, expr="fete"), B, T, TEN), 3)
        im.alpha_composite(p, ((im.width - p.width) // 2, im.height - p.height - 2))
        cases.append((im, nom))
    planche(cases, 4, (64 * 4 + 12, 48 * 4 + 24), FOND, os.path.join(dossier, "ensembles.png"))
    cases = []
    for st in (1, 3, 4):
        for id_, nom, bonus, pieces in ensembles[::2]:
            objets = [p for p in pieces if p in B and not p.startswith("fond-")] + [bonus]
            cases.append((pilou(stade=st, objets=objets, t=300), "%d %s" % (st, id_)))
    planche(cases, 5, case, FOND, os.path.join(dossier, "ensembles-stades.png"))


def main():
    dossier = sys.argv[1] if len(sys.argv) > 1 else os.path.join(rendu.ICI, "planches")
    os.makedirs(dossier, exist_ok=True)
    B, T, TEN = rendu.banque(), rendu.teintes(), rendu.tenues()
    z = 4

    def pilou(**kw):
        return grille_image(rendu.rendre(rendu.Pose(**kw), B, T, TEN), z)

    exprs = ["repos", "concentre", "attente", "inquiet", "fete", "soulage", "grimace", "caresse", "dort"]
    cases = [(pilou(expr=e, t=0), e) for e in exprs]
    cases += [(pilou(expr="repos", cligne=True), "cligne"), (pilou(expr="repos", etourdi=True), "étourdi"),
              (pilou(expr="repos", baille=True), "bâille"), (pilou(expr="repos", fatigue=True), "fatigué"),
              (pilou(expr="repos", marche=True, t=200), "marche"), (pilou(expr="repos", saut=3), "saut"),
              (pilou(expr="repos", assis=1), "assis"), (pilou(expr="repos", suspendu=1, t=300), "accroché"),
              (pilou(expr="repos", regard=1, clin=True), "clin d'œil")]
    planche(cases, 6, (48 * z + 8, 56 * z + 20), FOND, os.path.join(dossier, "pilou-expressions.png"))

    couleurs = list(T.keys())
    cases = [(pilou(couleur=c), c) for c in couleurs if c != "orange"]
    planche(cases, 8, (48 * z + 8, 56 * z + 20), FOND, os.path.join(dossier, "pilou-couleurs.png"))

    accs = ["feuille", "noeud", "casque", "bonnet", "lunettes", "couronne", "chapeaupeche", "toque", "tablier", "etoilemer"]
    cases = [(pilou(accessoire=a), a) for a in accs]
    planche(cases, 5, (48 * z + 8, 56 * z + 20), FOND, os.path.join(dossier, "accessoires.png"))

    cases = [(pilou(tenue=k, t=400), k) for k in TEN]
    planche(cases, 5, (48 * z + 8, 56 * z + 20), FOND, os.path.join(dossier, "tenues.png"))

    objets = ["chapeau-pirate", "haut-de-forme", "casquette", "bandeau-ninja", "cornes-viking", "aureole", "chapeau-sorcier",
              "couronne-fleurs", "lunettes-rondes", "monocle", "masque-plongee", "echarpe", "cape", "medaille", "baguette",
              "ballon-helium", "parapluie", "tasse-cafe", "petit-chat", "petit-poisson-bocal", "trainee-coeurs",
              "trainee-notes", "aura"]
    cases = [(pilou(objets=[o], t=300), o) for o in objets]
    cases += [(pilou(couleur=c), c) for c in ("lavande", "corail-orange", "ardoise", "sable", "glacier")]
    planche(cases, 7, (48 * z + 8, 56 * z + 20), FOND, os.path.join(dossier, "boutique.png"))

    prises = sorted(k for k in B if k.startswith("prise-"))
    cases = [(sprite_image(B[k], 6), k[6:]) for k in prises]
    planche(cases, 6, (34 * 6 + 10, 26 * 6 + 22), FOND2, os.path.join(dossier, "prises.png"))

    plats = sorted(k for k in B if k.startswith("plat-")) + ["marmite", "feu", "vapeur"]
    cases = [(sprite_image(B[k], 6), k) for k in plats]
    planche(cases, 6, (32 * 6 + 10, 22 * 6 + 22), FOND2, os.path.join(dossier, "plats.png"))

    cases = []
    for st in (1, 2, 3, 4):
        for e in ("repos", "fete", "dort"):
            cases.append((pilou(stade=st, expr=e, t=300), "stade %d %s" % (st, e)))
    cases += [(pilou(stade=3, accessoire="bonnet"), "3 bonnet"), (pilou(stade=4, tenue="code"), "4 code"),
              (pilou(stade=1, objets=["petit-chat"]), "1 chat"), (pilou(stade=4, objets=["haut-de-forme", "echarpe"]), "4 chapeau")]
    planche(cases, 6, (48 * z + 8, 56 * z + 20), FOND, os.path.join(dossier, "stades.png"))
    cases = []
    for i in range(12):
        e = min(0.99, 0.02 + i * 0.085)
        cases.append((pilou(stade=3, evolution=e, t=i * 120), "%.2f" % e))
    planche(cases, 6, (48 * z + 8, 56 * z + 20), FOND, os.path.join(dossier, "evolution.png"))
    # Soins : il boude (moue, sourcils, nuage gris, bras croisés du Nimbus), dos tourné, amadoué.
    cases = []
    for st in (1, 2, 3, 4):
        bras = ["boude-bras"] if st == 3 else []
        cases += [(pilou(stade=st, boude=True, objets=["boude-nuage"] + bras, t=840), "%d boude" % st),
                  (pilou(stade=st, boude=True, dos=True, objets=["boude-nuage"], t=840), "%d dos" % st),
                  (pilou(stade=st, boude=True, objets=["boude-eclaircie"], t=840), "%d amadoue" % st)]
    planche(cases, 6, (48 * z + 8, 56 * z + 20), FOND, os.path.join(dossier, "bouderie.png"))
    cases = [(pilou(reaction="sueur", t=200), "sueur"), (pilou(tenue="musique", t=500), "danse : notes")]
    planche(cases, 2, (48 * z + 8, 56 * z + 20), FOND, os.path.join(dossier, "reactions.png"))

    # Météo : ce que Pilou vit selon le temps et ce qu'il porte (mêmes règles que Meteo.Effet).
    meteo = [
        ("pluie, sans rien", dict(objets=["meteo-pluie", "meteo-mouille"], expr="grimace", tremble=0.35)),
        ("pluie + parapluie", dict(objets=["parapluie", "meteo-pluie"], expr="soulage")),
        ("averse + impermeable", dict(objets=["impermeable", "bottes-pluie", "meteo-averse"])),
        ("orage, sans rien", dict(objets=["meteo-averse", "meteo-eclair", "meteo-mouille"], expr="grimace", tremble=-0.35)),
        ("orage + parapluie etoile", dict(objets=["parapluie-etoile", "meteo-averse", "meteo-eclair"])),
        ("neige, sans rien", dict(objets=["meteo-neige", "meteo-givre"], expr="grimace", tremble=0.3)),
        ("neige + echarpe, moufles", dict(objets=["echarpe", "moufles", "meteo-neige"], expr="soulage")),
        ("canicule, sans rien", dict(objets=["meteo-soleil"], reaction="sueur")),
        ("canicule + eventail", dict(objets=["eventail", "meteo-soleil"], accessoire="lunettes")),
        ("vent fort", dict(objets=["meteo-vent"])),
        ("brouillard", dict(objets=["meteo-brouillard"])),
        ("Nimbus sous la pluie", dict(stade=3, objets=["parapluie", "meteo-pluie"])),
    ]
    for t0, nom in ((0, "meteo.png"), (330, "meteo-2.png")):
        cases = [(pilou(t=t0, **kw), titre) for titre, kw in meteo]
        planche(cases, 4, (48 * z + 8, 56 * z + 20), FOND, os.path.join(dossier, nom))
    cases = [(pilou(objets=[o], t=300), o) for o in ("impermeable", "bottes-pluie", "moufles", "eventail", "parapluie-etoile")]
    planche(cases, 5, (48 * z + 8, 56 * z + 20), FOND, os.path.join(dossier, "boutique-meteo.png"))

    # Boutique rétro : nouveaux objets par rayon, portés au stade 2 et sur les autres stades.
    nouveaux = ["beret", "bonnet-pompon", "casque-chantier", "sombrero", "chapeau-cowboy", "oreilles-chat",
                "couronne-laurier", "antenne-neon", "lunettes-3d", "visiere-pilote", "lunettes-coeur", "bandana",
                "noeud-pois", "cravate", "collier-perles", "sac-a-dos", "carapace", "ailes-papillon", "jetpack", "sucette",
                "epee-mousse", "lanterne", "guitare", "canne-or", "baskets", "palmes", "patins", "oiseau", "petit-robot",
                "fantome", "mini-dragon", "bulles-savon", "confettis", "trainee-prisme", "aura-feu"]
    cases = [(pilou(objets=[o], t=300), o) for o in nouveaux]
    cases += [(pilou(couleur=c), c) for c in ("pervenche", "mandarine", "miel", "prune", "acier", "peche")]
    planche(cases, 7, (48 * z + 8, 56 * z + 20), FOND, os.path.join(dossier, "boutique-retro.png"))
    cases = []
    for st in (1, 3, 4):
        for o in ("sombrero", "antenne-neon", "jetpack", "guitare", "ailes-papillon", "mini-dragon", "lunettes-coeur"):
            cases.append((pilou(stade=st, objets=[o], t=300), "%d %s" % (st, o)))
    cases += [(pilou(objets=["chapeau-cowboy", "bandana", "baskets"], fatigue=True), "négligé"),
              (pilou(objets=["oreilles-chat", "noeud-pois"], couleur="terne"), "terne")]
    planche(cases, 7, (48 * z + 8, 56 * z + 20), FOND, os.path.join(dossier, "boutique-retro-stades.png"))
    cases = []
    for f in ("fond-nuit", "fond-foret", "fond-plage", "fond-arcade", "fond-espace"):
        im = sprite_image(B[f], 4)
        p = grille_image(rendu.rendre(rendu.Pose(objets=["bonnet-pompon"] if f == "fond-nuit" else []), B, T, TEN), 3)
        im.alpha_composite(p, ((im.width - p.width) // 2, im.height - p.height - 4))
        cases.append((im, f))
    planche(cases, 5, (64 * 4 + 12, 48 * 4 + 24), FOND, os.path.join(dossier, "boutique-decors.png"))

    jeux = ["etoile", "bulle", "main", "ballon", "canne", "bouchon", "eclaboussure", "bug-scarabee", "bug-araignee", "bug-ver",
            "bug-prod", "bonus-cafe", "bonus-tests", "vie", "po", "po-tourne", "coffre-quete", "parchemin-quete"]
    cases = []
    for k in jeux:
        cases.append((sprite_image(B[k], 6), k))
    planche(cases, 6, (36 * 6 + 10, 30 * 6 + 22), FOND, os.path.join(dossier, "jeux.png"))
    garnie(os.path.join(dossier, "boutique2"), B, T, TEN)


if __name__ == "__main__":
    main()
