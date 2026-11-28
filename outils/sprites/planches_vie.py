"""Planches de contrôle de la vie du personnage (vie.py) : chaque mouvement image par image, et un GIF avant / après.

    python3 outils/sprites/planches_vie.py [dossier]      (par défaut : outils/sprites/planches/vie)

  sauts.png        le petit saut aux trois niveaux (aucune : le saut d'avant ; réduites : l'arc ; complètes : arc,
                   ressorts, antenne en retard, ombre tramée, poussière), une image toutes les 40 ms
  receptions.png   Pilou lâché qui retombe, la fête (petits bonds), la marche (bouffées du pied arrière), sur fond
                   sombre puis clair (la poussière doit rester discrète sur les deux)
  lumieres.png     matin, plein jour, soir, nuit, sur les quatre stades et deux couleurs ; l'alerte (inquiet) ne
                   change pas
  avant-apres.gif  à gauche le saut et la marche d'avant (niveau aucune), à droite les complètes, en temps réel

Les mêmes formules que VieFenetre.cs (PC) et PilouVue.java (téléphone) ; le dessin vient de rendu.py (rendu fin).
"""
import math
import os
import sys

from PIL import Image, ImageDraw

import planches
import rendu
import vie

SOMBRE = (28, 33, 40)
CLAIR = (236, 238, 232)
TEXTE = (214, 220, 228)
TEXTE_SOMBRE = (40, 44, 52)
PAS = 40
Z = 2   # rendu fin (96 × 112) agrandi deux fois


def bondir(niveau, d):
    """(saut, étire, antenne, atterri) du petit saut, d ms après son début (comme VieFenetre.Bondir)."""
    if niveau == vie.AUCUNE:
        return (math.sin(math.pi * d / 600) * 2 if 0 <= d < 600 else 0), 0, 0, -1
    if d >= vie.duree_bond(520, niveau):
        return 0, 0, 0, -1
    s, e, a = vie.bond(d, 520, 2000, niveau)
    atterri = d - vie.PREP - 520 if niveau == vie.COMPLETES else -1
    return s / 1000, e / 1000, a / 1000, atterri if 0 <= atterri < 3 * vie.BOUFFEE_IMAGE else -1


def image(B, T, TEN, fond, **kw):
    g = rendu.rendre(rendu.Pose(**kw), B, T, TEN, 2)
    im = Image.new("RGBA", (96 * Z, 112 * Z), fond + (255,))
    im.alpha_composite(planches.grille_image(g, Z))
    return im.convert("RGB")


def bande(titre, images, fond, encre):
    w, h = 96 * Z, 112 * Z
    out = Image.new("RGB", (len(images) * (w + 4) + 16, h + 34), fond)
    d = ImageDraw.Draw(out)
    d.text((8, 6), titre, fill=encre)
    for i, (legende, im) in enumerate(images):
        out.paste(im, (8 + i * (w + 4), 24))
        d.text((10 + i * (w + 4), 26), legende, fill=encre)
    return out


def empiler(bandes):
    w = max(b.width for b in bandes)
    out = Image.new("RGB", (w, sum(b.height for b in bandes)), SOMBRE)
    y = 0
    for b in bandes:
        out.paste(b, (0, y))
        y += b.height
    return out


def sauts(B, T, TEN):
    bandes = []
    for niveau in (vie.AUCUNE, vie.REDUITES, vie.COMPLETES):
        ims = []
        for d in range(0, 1000, PAS):
            s, e, a, at = bondir(niveau, d)
            ims.append(("%d" % d, image(B, T, TEN, SOMBRE, t=d, saut=s, etire=e, antenne=a, atterri=at,
                                         vie=niveau == vie.COMPLETES)))
        bandes.append(bande("petit saut · %s · une image toutes les %d ms" % (niveau, PAS), ims, SOMBRE, TEXTE))
    return empiler(bandes)


def receptions(B, T, TEN):
    bandes = []
    for fond, encre, nom in ((SOMBRE, TEXTE, "fond sombre"), (CLAIR, TEXTE_SOMBRE, "fond clair")):
        ims = []
        for d in range(0, 400, PAS):
            e, a = vie.reception(d, vie.COMPLETES)
            ims.append(("%d" % d, image(B, T, TEN, fond, t=d, etire=e / 1000, antenne=a / 1000,
                                         atterri=d if d < 240 else -1, vie=True)))
        bandes.append(bande("lâché, il retombe · complètes · %s" % nom, ims, fond, encre))
        ims = []
        for t in range(0, 680, PAS):
            ims.append(("%d" % t, image(B, T, TEN, fond, t=t, marche=True, regard=1, vie=True)))
        bandes.append(bande("marche vers la droite · bouffée du pied arrière · %s" % nom, ims, fond, encre))
    ims = []
    for d in range(0, 920, PAS):
        s, e, a = vie.sautille(d, 450, 3000, vie.COMPLETES)
        ims.append(("%d" % d, image(B, T, TEN, SOMBRE, expr="fete", t=d, saut=s / 1000, etire=e / 1000, antenne=a / 1000,
                                     vie=True)))
    bandes.append(bande("fête · petits bonds · complètes", ims, SOMBRE, TEXTE))
    return empiler(bandes)


def lumieres(B, T, TEN):
    bandes = []
    for couleur in ("bleu", "sable"):
        for st in (1, 2, 3, 4):
            ims = [(m or "jour", image(B, T, TEN, SOMBRE, stade=st, couleur=couleur, lumiere=m)) for m in ("matin", "", "soir", "nuit")]
            ims.append(("inquiet soir", image(B, T, TEN, SOMBRE, stade=st, couleur=couleur, expr="inquiet", t=320, lumiere="soir")))
            bandes.append(bande("lumière du moment · stade %d · %s" % (st, couleur), ims, SOMBRE, TEXTE))
    return empiler(bandes)


def avant_apres(B, T, TEN):
    """Saut (0–1,2 s), puis marche (1,2–2,4 s), en boucle ; 40 ms par image."""
    w, h = 96 * Z, 112 * Z
    images = []
    for k in range(0, 2400, PAS):
        out = Image.new("RGB", (2 * w + 30, h + 24), SOMBRE)
        d = ImageDraw.Draw(out)
        for i, niveau in enumerate((vie.AUCUNE, vie.COMPLETES)):
            if k < 1200:
                s, e, a, at = bondir(niveau, k)
                im = image(B, T, TEN, SOMBRE, t=k, saut=s, etire=e, antenne=a, atterri=at, vie=niveau == vie.COMPLETES)
            else:
                im = image(B, T, TEN, SOMBRE, t=k, marche=True, regard=1, vie=niveau == vie.COMPLETES)
            out.paste(im, (10 + i * (w + 10), 20))
            d.text((12 + i * (w + 10), 4), "avant" if niveau == vie.AUCUNE else "après", fill=TEXTE)
        images.append(out)
    return images


def main():
    dossier = sys.argv[1] if len(sys.argv) > 1 else os.path.join(rendu.ICI, "planches", "vie")
    os.makedirs(dossier, exist_ok=True)
    B, T, TEN = rendu.banque(), rendu.teintes(), rendu.tenues()
    sauts(B, T, TEN).save(os.path.join(dossier, "sauts.png"))
    receptions(B, T, TEN).save(os.path.join(dossier, "receptions.png"))
    lumieres(B, T, TEN).save(os.path.join(dossier, "lumieres.png"))
    im = avant_apres(B, T, TEN)
    im[0].save(os.path.join(dossier, "avant-apres.gif"), save_all=True, append_images=im[1:], duration=PAS, loop=0)
    print("planches écrites dans", dossier)


if __name__ == "__main__":
    main()
