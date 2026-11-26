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

    jeux = ["etoile", "bulle", "main", "ballon", "canne", "bouchon", "eclaboussure", "bug-scarabee", "bug-araignee", "bug-ver",
            "bug-prod", "bonus-cafe", "bonus-tests", "vie", "po", "po-tourne", "coffre-quete", "parchemin-quete"]
    cases = []
    for k in jeux:
        cases.append((sprite_image(B[k], 6), k))
    planche(cases, 6, (36 * 6 + 10, 30 * 6 + 22), FOND, os.path.join(dossier, "jeux.png"))


if __name__ == "__main__":
    main()
