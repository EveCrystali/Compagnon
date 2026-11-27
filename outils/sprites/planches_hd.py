"""Planches de contrôle du rendu fin (2×) : avant (rendu 1× agrandi au plus proche voisin) / après (rendu fin).

    python3 outils/sprites/planches_hd.py [dossier]        (par défaut : outils/sprites/planches/hd)

  stades.png, humeurs.png, voyages.png      Pilou aux 4 stades, les 10 humeurs des campagnes, les 8 tenues de voyage
  cosmetiques-redessines.png                20 cosmétiques redessinés en fin (seuls et portés)
  cosmetiques-automatiques.png              20 cosmétiques encore agrandis automatiquement
  portrait-dialogue.png                     Pilou en grand (portrait de dialogue des campagnes), plusieurs humeurs
  bureau.png                                le bureau Windows à 100, 125, 150, 175 et 200 %, en pixels physiques :
                                            dessin d'origine et dessin fin, sur fond clair et sombre
  rapport.txt                               sprites redessinés / encore agrandis automatiquement
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

import fin
import planches
import rendu
import reference

FOND = (28, 33, 40)
CLAIR = (238, 242, 246)
TEXTE = (200, 208, 216)


def _police():
    """Une police qui sait les accents, si la machine en a une (sinon celle de PIL, sans accents)."""
    for nom in ("DejaVuSans.ttf", "LiberationSans-Regular.ttf", "arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(nom, 13)
        except OSError:
            continue
    return ImageFont.load_default()


POLICE = _police()
B, T, TEN = rendu.banque(), rendu.teintes(), rendu.tenues()
B2 = rendu.banque_fine(B)


def pilou(e, z, **kw):
    return planches.grille_image(rendu.rendre(rendu.Pose(**kw), B, T, TEN, e, B2), z)


def paire(z, **kw):
    """Avant / après côte à côte, à la même taille : 1× agrandi z fois, rendu fin agrandi z / 2 fois."""
    a, b = pilou(1, z, **kw), pilou(2, z // 2, **kw)
    im = Image.new("RGBA", (a.width + b.width + 6, a.height), (0, 0, 0, 0))
    im.alpha_composite(a, (0, 0))
    im.alpha_composite(b, (a.width + 6, 0))
    return im


def planche(cases, colonnes, chemin, fond=FOND, titre=""):
    cw = max(im.width for im, _ in cases) + 16
    ch = max(im.height for im, _ in cases) + 26
    lignes = (len(cases) + colonnes - 1) // colonnes
    haut = 30 if titre else 0
    out = Image.new("RGBA", (cw * colonnes, ch * lignes + haut), fond + (255,))
    d = ImageDraw.Draw(out)
    if titre:
        d.text((8, 8), titre, fill=TEXTE if fond == FOND else (60, 70, 80), font=POLICE)
    for i, (im, nom) in enumerate(cases):
        x, y = (i % colonnes) * cw, (i // colonnes) * ch + haut
        out.alpha_composite(im, (x + (cw - im.width) // 2, y + 4))
        d.text((x + 8, y + ch - 18), nom, fill=TEXTE if fond == FOND else (60, 70, 80), font=POLICE)
    out.save(chemin)
    print(chemin, out.size)


def sprite_seul(s, z):
    return planches.sprite_image(s, z)


REDESSINES = ["chapeau-sorcier", "bonnet-pompon", "chapeau-explorateur", "chapeau-paille", "chapeau-cowboy", "beret",
              "lunettes-rondes", "lunettes-plage", "lunettes-etoiles", "masque-plongee", "echarpe", "cape", "sac-a-dos",
              "cartable", "parapluie", "baluchon", "lanterne", "oiseau", "petit-poisson-bocal", "mini-dragon"]
AUTOMATIQUES = ["tricorne-moka", "cornes-viking", "sombrero", "couronne-cristal", "lunettes-ski", "masque-loup", "noeud-geant",
                "collier-perles", "ailes-papillon", "jetpack", "guitare", "telescope", "eventail", "cerf-volant", "herisson",
                "perroquet-caramel", "fantome", "bottes-pluie", "patins", "aureole"]
HUMEURS = ["joie", "peur", "triste", "surpris", "determine", "fatigue", "tendre", "colere", "malice", "neutre"]


def cosmetiques(ids, chemin, titre):
    cases = []
    for i in ids:
        s, f = B[i], B2[i]
        seul_a, seul_b = sprite_seul(s, 6), sprite_seul(f, 3)
        porte = paire(4, objets=[i], t=300)
        w = seul_a.width + seul_b.width + 10 + porte.width + 14
        im = Image.new("RGBA", (w, max(seul_a.height, porte.height)), (0, 0, 0, 0))
        im.alpha_composite(seul_a, (0, (im.height - seul_a.height) // 2))
        im.alpha_composite(seul_b, (seul_a.width + 10, (im.height - seul_b.height) // 2))
        im.alpha_composite(porte, (seul_a.width + seul_b.width + 24, 0))
        cases.append((im, "%s%s" % (i, "" if f.natif else "  (automatique)")))
    planche(cases, 2, chemin, titre=titre)


def portrait(chemin):
    """Portrait de dialogue : Pilou en rendu fin, 6 pixels d'écran par pixel fin, au-dessus d'une bulle de récit."""
    humeurs = [("joie", dict(objets=["medaille"])), ("peur", dict(objets=["lanterne"])), ("triste", {}),
               ("determine", dict(objets=["chapeau-explorateur", "sac-a-dos"])), ("malice", {}), ("tendre", dict(stade=3)),
               ("surpris", dict(stade=4)), ("colere", dict(stade=1))]
    z = 5
    w, h = 96 * z, 112 * z
    out = Image.new("RGBA", ((w + 24) * 4, (h + 70) * 2), (22, 27, 44, 255))
    d = ImageDraw.Draw(out)
    for i, (hm, kw) in enumerate(humeurs):
        x, y = (i % 4) * (w + 24) + 12, (i // 4) * (h + 70) + 8
        d.rectangle([x, y, x + w - 1, y + h - 1], fill=(36, 44, 70, 255), outline=(106, 90, 205, 255), width=3)
        out.alpha_composite(pilou(2, z, expr=hm, t=400, **kw), (x, y))
        d.rectangle([x, y + h + 6, x + w - 1, y + h + 48], fill=(246, 248, 250, 255), outline=(31, 79, 138, 255), width=3)
        d.text((x + 12, y + h + 20), "humeur « %s »   (rendu fin, %d px par pixel fin)" % (hm, z), fill=(28, 33, 40), font=POLICE)
    out.save(chemin)
    print(chemin, out.size)


def ppv(im, w, h):
    """Agrandissement au plus proche voisin vers w × h pixels (comme WPF en NearestNeighbor)."""
    return im.resize((w, h), Image.NEAREST)


def pixels_par_pixel_fin(taille, dpi):
    """Placement.PixelsParPixelFin : entier le plus proche de (104 / 48) × taille × dpi / 2, tailles ordonnées."""
    def proche(t):
        return max(1, int((104 / 48) * t * dpi / 2 + 0.5))
    normal, n = proche(1), proche(taille)
    if taille > 1.15:
        n = max(n, normal + 1)
    elif taille < 0.9:
        n = max(1, min(n, normal - 1))
    return n


def bureau(chemin):
    """Pilou sur le bureau Windows, en pixels physiques : dessin d'origine (grille 48 × 56 étirée à 104 unités) et
    dessin fin (96 × n pixels), à chaque mise à l'échelle, sur fond clair et sombre ; puis un détail grossi 3 fois."""
    poses = [dict(t=300), dict(expr="joie", t=300, objets=["chapeau-explorateur", "echarpe", "oiseau"])]
    echelles = [1.0, 1.25, 1.5, 1.75, 2.0]
    lignes = []
    for dpi in echelles:
        n = pixels_par_pixel_fin(1.0, dpi)
        avant_w, avant_h = int(round(104 * dpi)), int(round(104 * dpi * 56 / 48))
        apres_w, apres_h = 96 * n, 112 * n
        lignes.append((dpi, n, avant_w, avant_h, apres_w, apres_h))
    case_w = 2 * (max(l[2] for l in lignes) + 20) + 2 * (max(l[4] for l in lignes) + 20)
    haut = sum(max(l[3], l[5]) + 44 for l in lignes) + 20
    detail_w = 520
    out = Image.new("RGBA", (2 * case_w + detail_w, haut), FOND + (255,))
    d = ImageDraw.Draw(out)
    d.rectangle([case_w, 0, 2 * case_w - 1, haut], fill=CLAIR + (255,))
    y = 10
    for dpi, n, aw, ah, pw, ph in lignes:
        hl = max(ah, ph)
        for k, fond in enumerate((FOND, CLAIR)):
            x = k * case_w + 10
            encre = TEXTE if k == 0 else (50, 60, 70)
            d.text((x, y), "%d %% — origine : %d px de large · fin : %d px (%d px par pixel fin)" % (round(dpi * 100), aw, pw, n),
                   fill=encre, font=POLICE)
            for j, kw in enumerate(poses):
                a = ppv(pilou(1, 1, **kw), aw, ah)
                b = ppv(pilou(2, 1, **kw), pw, ph)
                out.alpha_composite(a, (x, y + 18 + hl - ah))
                x += aw + 20
                out.alpha_composite(b, (x, y + 18 + hl - ph))
                x += pw + 20
        # Détail grossi trois fois : le visage, origine puis fin (fond sombre).
        a = ppv(pilou(1, 1, **poses[0]), aw, ah)
        b = ppv(pilou(2, 1, **poses[0]), pw, ph)
        za = a.crop((0, int(ah * 0.36), aw, int(ah * 0.86)))
        zb = b.crop((0, int(ph * 0.36), pw, int(ph * 0.86)))
        f = max(1, min(3, 250 // max(za.width, zb.width)))
        za, zb = ppv(za, za.width * f, za.height * f), ppv(zb, zb.width * f, zb.height * f)
        x = 2 * case_w + 6
        out.alpha_composite(za, (x, y + 18))
        out.alpha_composite(zb, (x + 256, y + 18))
        d.text((x, y), "détail × %d : origine" % f, fill=TEXTE, font=POLICE)
        d.text((x + 256, y), "fin", fill=TEXTE, font=POLICE)
        y += hl + 44
    out.save(chemin)
    print(chemin, out.size)
    return lignes


def tailles(chemin):
    """Tableau des tailles réelles de Pilou sur le bureau (largeur de la grille, en pixels physiques)."""
    l = ["Largeur de Pilou sur le bureau Windows, en pixels physiques (grille entière : 48 pixels de grille).",
         "échelle | taille | origine (104 × taille × échelle) | dessin fin (96 × n) | n = px physiques par pixel fin"]
    for dpi in (1.0, 1.25, 1.5, 1.75, 2.0):
        for nom, t in (("Petit", 0.75), ("Normal", 1.0), ("Grand", 1.3)):
            n = pixels_par_pixel_fin(t, dpi)
            l.append("%4d %% | %-6s | %7.1f | %4d | %d" % (round(dpi * 100), nom, 104 * t * dpi, 96 * n, n))
    with open(chemin, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(l) + "\n")
    print(chemin)


def main():
    dossier = sys.argv[1] if len(sys.argv) > 1 else os.path.join(rendu.ICI, "planches", "hd")
    os.makedirs(dossier, exist_ok=True)

    def ou(nom):
        return os.path.join(dossier, nom)

    noms = {1: "1 Gouttelette", 2: "2 Pilou", 3: "3 Nimbus", 4: "4 Astral"}
    planche([(paire(8, stade=s, t=300), noms[s] + " — 1× agrandi | rendu fin") for s in (1, 2, 3, 4)], 2, ou("stades.png"),
            titre="Les 4 stades : à gauche le rendu 1× agrandi au plus proche voisin, à droite le rendu fin (2×)")
    planche([(paire(6, expr=h, t=400), h) for h in HUMEURS], 5, ou("humeurs.png"),
            titre="Les 10 humeurs des campagnes : 1× agrandi | rendu fin")
    planche([(paire(6, tenue="voyage-" + m, t=t), "voyage-" + m)
             for m, t in zip(rendu.VOYAGES, (250, 410, 780, 630, 1150, 2100, 950, 3000))], 4, ou("voyages.png"),
            titre="Les 8 tenues de voyage : 1× agrandi | rendu fin")
    cosmetiques(REDESSINES, ou("cosmetiques-redessines.png"),
                "20 cosmétiques redessinés en fin : sprite 1× agrandi, sprite fin, puis portés (1× | fin)")
    cosmetiques(AUTOMATIQUES, ou("cosmetiques-automatiques.png"),
                "20 cosmétiques en agrandissement automatique : sprite 1× (plus proche voisin), sprite agrandi (MMPX), portés")
    portrait(ou("portrait-dialogue.png"))
    bureau(ou("bureau.png"))
    tailles(ou("bureau-tailles.txt"))
    natifs, autos = fin.rapport()
    with open(ou("rapport.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("Sprites redessinés en fin (assets/sprites2x) : %d\n%s\n\n" % (len(natifs), " ".join(natifs)))
        f.write("Sprites encore agrandis automatiquement : %d\n%s\n" % (len(autos), " ".join(autos)))
    print(ou("rapport.txt"), len(natifs), "redessinés,", len(autos), "automatiques")


if __name__ == "__main__":
    main()
