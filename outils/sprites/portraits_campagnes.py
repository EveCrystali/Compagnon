"""Portraits animés des personnages des campagnes (docs/SPRITES.md, « Portraits des personnages » ; docs/LORE.md).

Un personnage n'apparaît que lorsque le texte le fait parler ou le décrit : le nœud porte `"personnage": "<id>"` (et
peut-être `"expression"`), l'interface montre alors son portrait à côté de la scène.

Format : `portrait-<campagne>-<personnage>` (expression neutre) et `portrait-<campagne>-<personnage>-<expression>`
(expressions parmi les humeurs de Pilou : joie, peur, triste, surpris, determine, fatigue, tendre, colere, malice), de
32 × 32 (fin : 64 × 64), fond transparent, `ancre: aucun`, cerne sombre d'un pixel. Cinq images, toujours dans le même
ordre (clé `portrait: repos 0 1 cligne 2 parle 3 4`, ignorée des anciens lecteurs) :

  0  repos              1  repos, inspiré (le haut du corps monte d'un pixel : la respiration)
  2  yeux fermés (le clignement)
  3  bouche mi-ouverte  4  bouche ouverte (la parole)

Le choix de l'image à l'instant t est commun au PC et au téléphone (animations.image_portrait). Tout est dessiné de
formes, rejoué en fin (pixels fins : reflets, cils, rides) : aucun personnage, style ou motif repris d'une œuvre.
Palette : jamais d'opposition rouge / vert (les rainettes sont sarcelle, les joues pêche, les bouches prune).
"""
import math

import toile
from toile import Toile, ecrire
from peinture import ell, poly, rect, point, trait, hline, vline, courbe

W, H = 32, 32
CERNE = "#1a1726"
ENCRE = "#1c2128"
BLANC = "#fbf8f0"
BOUCHE, LANGUE = "#3b1f33", "#c76f9a"
JOUE = "#f2a88a"
LARME = "#8fc8f0"

EXPRESSIONS = ("joie", "peur", "triste", "surpris", "determine", "fatigue", "tendre", "colere", "malice")

PERSOS = {}     # (campagne, id) -> (nom, description, expressions, fonction, coupe)
IDS = []


def perso(campagne, id_, nom, expressions=(), description="", coupe=22):
    def poser(f):
        PERSOS[(campagne, id_)] = (nom, description, tuple(expressions), f, coupe)
        return f
    return poser


class Etat:
    def __init__(self, humeur="neutre", yeux="o", bouche=0):
        self.humeur, self.yeux, self.bouche = humeur, yeux, bouche

    @property
    def ferme(self):
        return self.yeux == "f"


# ---------------------------------------------------------------------------------------------------------------------
# Pinceaux communs : volumes, yeux, sourcils, bouches
# ---------------------------------------------------------------------------------------------------------------------
def boule(t, cx, cy, rx, ry, base, ombre=None, clair=None, cond=None):
    """Volume éclairé d'en haut à gauche : base, ombre en croissant en bas à droite, reflet en haut à gauche."""
    ell(t, cx, cy, rx, ry, base, cond=cond)
    if ombre:
        ell(t, cx, cy, rx, ry, ombre, cond=lambda x, y, u, v: u * 0.55 + v * 0.85 > 0.62 and (cond is None or cond(x, y, u, v)))
    if clair:
        ell(t, cx - rx * 0.38, cy - ry * 0.42, rx * 0.32, ry * 0.24, clair,
            cond=lambda x, y, u, v: cond is None or cond(x, y, u, v))


def oeil(t, x, y, e, r=1.0, iris=ENCRE, blanc=None, cote=1, paupiere=None):
    """Un œil. cote : -1 œil gauche, 1 œil droit (pour les sourcils et la malice)."""
    h = e.humeur
    if e.ferme or h in ("tendre", "fatigue") or (h == "malice" and cote > 0):
        if h in ("joie", "tendre"):
            courbe(t, [(x - r, y + 0.4), (x, y - 0.8), (x + r, y + 0.4)], iris, ep=t.e)
        else:
            courbe(t, [(x - r, y - 0.1), (x, y + 0.5), (x + r, y - 0.1)], paupiere or iris, ep=t.e)
        return
    if h == "joie":
        courbe(t, [(x - r, y + 0.6), (x, y - 0.9), (x + r, y + 0.6)], iris, ep=t.e)
        return
    grand = h in ("surpris", "peur")
    if blanc or grand:
        ell(t, x, y, r * (1.25 if grand else 1.05), r * (1.5 if grand else 1.25), blanc or BLANC)
        ell(t, x + 0.1 * cote, y + 0.2, r * (0.5 if grand else 0.62), r * (0.6 if grand else 0.8), iris)
    else:
        ell(t, x, y, r * 0.62, r * 0.95, iris)
    if toile.fin():
        point(t, x - 0.35 * r, y - 0.35 * r, BLANC)


def sourcil(t, x, y, e, l=2.0, c=ENCRE, cote=1, ep=None):
    """Sourcil : sa pente dit l'humeur (colère : bas vers le nez ; tristesse, peur : haut vers le nez)."""
    h = e.humeur
    ep = ep or t.e
    pente = {"colere": 0.9, "determine": 0.6, "triste": -0.8, "peur": -0.9, "fatigue": -0.3, "surpris": 0,
             "malice": 0.5 if cote < 0 else -0.6}.get(h, 0.0)
    haut = -0.8 if h in ("surpris", "peur") else 0
    xi, xe = x - cote * l / 2, x + cote * l / 2     # côté nez, côté extérieur
    trait(t, xi, y + haut + pente * 0.6, xe, y + haut - pente * 0.3, c, ep=ep)


def yeux(t, xg, xd, y, e, r=1.0, iris=ENCRE, blanc=None, sourcils=None, ys=None, ls=2.2, paupiere=None):
    oeil(t, xg, y, e, r, iris, blanc, -1, paupiere)
    oeil(t, xd, y, e, r, iris, blanc, 1, paupiere)
    if sourcils:
        ys = y - r * 1.9 if ys is None else ys
        sourcil(t, xg, ys, e, ls, sourcils, -1)
        sourcil(t, xd, ys, e, ls, sourcils, 1)
    if e.humeur == "peur" and toile.fin():
        ell(t, xd + r * 2.2, y - r * 1.2, 0.5, 0.8, LARME)
    if e.humeur == "triste":
        ell(t, xg - 0.2, y + r * 1.6, 0.45, 0.7, LARME)


def bouche(t, x, y, e, l=3.0, c=BOUCHE, ligne=ENCRE):
    """Bouche : fermée, elle dit l'humeur ; ouverte (1, 2), elle parle."""
    h = e.humeur
    if e.bouche:
        rx = l * (0.32 if e.bouche == 1 else 0.42)
        ry = 0.55 if e.bouche == 1 else 1.05
        if h in ("joie", "tendre", "malice"):
            ell(t, x, y, rx * 1.2, ry + 0.3, c, cond=lambda a, b, u, v: v > -0.35)
        else:
            ell(t, x, y + (0.2 if h in ("triste", "peur") else 0), rx, ry, c)
        if e.bouche == 2 and toile.fin():
            ell(t, x, y + ry * 0.55, rx * 0.6, ry * 0.4, LANGUE)
        return
    if h in ("joie", "tendre"):
        courbe(t, [(x - l / 2, y - 0.4), (x, y + 0.9), (x + l / 2, y - 0.4)], ligne, ep=t.e)
    elif h == "malice":
        courbe(t, [(x - l / 2, y + 0.2), (x + l * 0.1, y + 0.6), (x + l / 2, y - 0.6)], ligne, ep=t.e)
    elif h in ("triste", "peur", "fatigue"):
        courbe(t, [(x - l / 2, y + 0.6), (x, y - 0.3), (x + l / 2, y + 0.6)], ligne, ep=t.e)
    elif h == "surpris":
        ell(t, x, y, 0.8, 0.9, c)
    elif h == "colere":
        courbe(t, [(x - l / 2, y + 0.4), (x, y - 0.2), (x + l / 2, y + 0.4)], ligne, ep=t.e)
    else:
        trait(t, x - l / 2 + 0.3, y, x + l / 2 - 0.3, y, ligne, ep=t.e)


def joues(t, xg, xd, y, e, c=JOUE):
    if e.humeur in ("joie", "tendre", "malice"):
        ell(t, xg, y, 1.1, 0.6, c)
        ell(t, xd, y, 1.1, 0.6, c)


def buste(t, vetement, ombre, clair=None, col=None, haut=24.0, largeur=13.0):
    """Les épaules d'un humain, posées en bas du cadre."""
    poly(t, [(16 - largeur, 32), (16 - largeur + 2.5, haut), (16 + largeur - 2.5, haut), (16 + largeur, 32)], vetement)
    poly(t, [(16 + 2, haut), (16 + largeur - 2.5, haut), (16 + largeur, 32), (16 + 4, 32)], ombre)
    if clair:
        trait(t, 16 - largeur + 2.6, haut + 0.5, 16 - largeur + 0.8, 31.5, clair, ep=1)
    if col:
        poly(t, [(13, haut), (16, haut + 3.2), (19, haut), (17.5, haut - 0.5), (14.5, haut - 0.5)], col)


def tete(t, cx, cy, rx, ry, peau, peau_o, cou=True, oreilles=True):
    if cou:
        rect(t, cx - 2.2, cy + ry - 2, 4.4, 4.5, peau_o)
    if oreilles:
        ell(t, cx - rx + 0.2, cy + 0.6, 1.3, 1.8, peau_o)
        ell(t, cx + rx - 0.2, cy + 0.6, 1.3, 1.8, peau_o)
    boule(t, cx, cy, rx, ry, peau, peau_o)


# ---------------------------------------------------------------------------------------------------------------------
# La Grande Panne
# ---------------------------------------------------------------------------------------------------------------------
BOIS1, BOIS2, BOIS3 = "#5a3820", "#8a5a33", "#b8844f"
VERRE, VERRE_O, VERRE_C = "#cfe0ea", "#9fb8cc", "#f2f8fb"
SABLE, SABLE_O, SABLE_C = "#e8b45a", "#c08a38", "#f8d898"
GRIS1, GRIS2, GRIS3, GRIS4 = "#3a3f4b", "#5a6070", "#8890a0", "#b8bfcc"
BEIGE1, BEIGE2, BEIGE3 = "#8a7d68", "#b8a98c", "#ddd0b2"
PAPIER, PAPIER_O, PAPIER_L = "#f6f1e4", "#d9cfb8", "#a9b4c8"
VIO1, VIO2, VIO3, VIO4 = "#2e2450", "#4a3a7e", "#6a5acd", "#9b8cff"
BLEU1, BLEU2, BLEU3 = "#1f4f8a", "#4a8fdc", "#8fc0f0"
OR1, OR2, OR3 = "#a8862a", "#e8c447", "#fff0a0"
ORANGE1, ORANGE2, ORANGE3 = "#c46a24", "#ff9a3c", "#ffd29a"
CYAN1, CYAN2 = "#2a8fc0", "#8fe0ff"
PEAU, PEAU_O, PEAU_C = "#f2c9a0", "#d9a37a", "#fbe0c4"


@perso("grande-panne", "grumeau", "Grumeau", ("colere", "tendre", "surpris"),
       "vieux sablier d'attente en bois, verre un peu rayé, sourcils de crin, un grain coincé au col")
def grumeau(t, e):
    # Les deux montants de bois.
    for x in (7, 25):
        rect(t, x - 0.9, 4, 1.8, 24, BOIS2)
        vline(t, x - 0.5, 4, 28, BOIS3)
    # Les deux ampoules de verre et le col.
    boule(t, 16, 10.6, 7, 6, VERRE, VERRE_O)
    boule(t, 16, 21.6, 7, 5.6, VERRE, VERRE_O)
    rect(t, 14.8, 15, 2.4, 2.4, VERRE_O)
    # Le sable : ce qui reste en haut, le tas en bas, le filet, et le grumeau coincé.
    ell(t, 16, 10.6, 7, 6, SABLE, cond=lambda x, y, u, v: y > 13.2)
    ell(t, 16, 10.6, 7, 6, SABLE_O, cond=lambda x, y, u, v: y > 13.2 and u > 0.3)
    poly(t, [(9.5, 26.8), (13, 23.2), (19, 23.2), (22.5, 26.8)], SABLE)
    poly(t, [(16, 23.2), (19, 23.2), (22.5, 26.8), (17, 26.8)], SABLE_O)
    vline(t, 16, 16.5, 23.2, SABLE)
    point(t, 16, 16, SABLE_O)
    if toile.fin():
        trait(t, 11.5, 7, 12.5, 5.6, VERRE_C, ep=1)
        trait(t, 11, 19.4, 11.8, 18.4, VERRE_C, ep=1)
    # Les plateaux de bois.
    for y in (2.2, 27.2):
        rect(t, 5, y, 22, 2.8, BOIS2)
        hline(t, 5, 27, y, BOIS3)
        hline(t, 5, 27, y + 2.6, BOIS1)
    # Le visage, sur le verre du haut ; de gros sourcils de crin gris (il est grognon même content).
    hum = e.humeur if e.humeur != "neutre" else "grognon"
    f = Etat("colere" if hum == "grognon" else e.humeur, e.yeux, e.bouche)
    yeux(t, 13, 19, 9.2, Etat(e.humeur, e.yeux, e.bouche), 1.0)
    sourcil(t, 13, 7.0, f, 3.0, GRIS3, -1, ep=t.e + 1)
    sourcil(t, 19, 7.0, f, 3.0, GRIS3, 1, ep=t.e + 1)
    bouche(t, 16, 12.0, Etat("colere" if hum == "grognon" and not e.bouche else e.humeur, e.yeux, e.bouche), 3)


@perso("grande-panne", "le-rond", "Le Rond", ("surpris",), "curseur d'attente moderne, coincé aux trois quarts de son tour")
def le_rond(t, e):
    for i in range(8):
        a = math.radians(-90 + i * 45)
        x, y = 16 + 10.5 * math.cos(a), 15 + 10.5 * math.sin(a)
        allume = i < 6
        boule(t, x, y, 2.6, 2.6, BLEU2 if allume else GRIS3, BLEU1 if allume else GRIS2, BLEU3 if allume else None)
    boule(t, 16, 15, 6, 6, "#e6ecf6", "#b8c4d6")
    yeux(t, 14, 18, 14.6, e, 0.9)
    bouche(t, 16, 18, e, 2.4)


@perso("grande-panne", "mlle-renvoi", "Mlle Renvoi", ("joie", "colere"),
       "agente d'accueil très droite, chignon, lunettes, un astérisque à la boutonnière")
def mlle_renvoi(t, e):
    buste(t, VIO2, VIO1, VIO3, col=BLANC, haut=24.5, largeur=11)
    # Le badge à astérisque.
    for a in range(0, 180, 60):
        r = math.radians(a)
        trait(t, 21 - 1.2 * math.cos(r), 28 - 1.2 * math.sin(r), 21 + 1.2 * math.cos(r), 28 + 1.2 * math.sin(r), OR2, ep=t.e)
    tete(t, 16, 14.5, 6.6, 7.6, PEAU, PEAU_O)
    # Cheveux tirés, chignon haut.
    ell(t, 16, 10.5, 7, 4.6, "#4a2e40", cond=lambda x, y, u, v: v < 0.2)
    boule(t, 16, 4.2, 3.4, 2.8, "#4a2e40", "#2e1c2a", "#6a4a5c")
    trait(t, 13, 4.5, 19, 3.5, OR2, ep=1)                          # l'épingle
    joues(t, 12.4, 19.6, 17.4, e)
    yeux(t, 13.4, 18.6, 14.6, e, 0.9, sourcils="#4a2e40", ys=12.2, ls=2)
    # Les lunettes rectangulaires.
    for x in (13.4, 18.6):
        hline(t, x - 2, x + 2, 13.0, GRIS1)
        hline(t, x - 2, x + 2, 16.3, GRIS1)
        vline(t, x - 2, 13.0, 16.4, GRIS1)
        vline(t, x + 2, 13.0, 16.4, GRIS1)
    hline(t, 15.4, 16.6, 14, GRIS1)
    bouche(t, 16, 19.2, e, 2.6)


@perso("grande-panne", "golem", "Le golem de tickets", ("colere",), "gardien de file fait de tickets empilés, une fente pour œil")
def golem(t, e):
    for j, (y, l) in enumerate(((24, 12), (18, 13), (12, 11.5), (6.5, 9))):
        rect(t, 16 - l, y, 2 * l, 6.5, PAPIER if j % 2 else BEIGE3)
        hline(t, 16 - l, 16 + l, y, BEIGE2)
        for i in range(3):
            hline(t, 16 - l + 2, 16 - l + 2 + 3 + i * 2, y + 2 + i * 1.4, PAPIER_L)
        rect(t, 16 + l - 3, y + 0.8, 2, 2, ORANGE2 if j == 1 else BLEU2)
    # La fente-œil, un regard qui balaie.
    rect(t, 10, 9, 12, 3, GRIS1)
    if e.ferme:
        hline(t, 10.5, 21.5, 10.5, ORANGE2)
    else:
        boule(t, 16 + (1.5 if e.humeur == "colere" else 0), 10.5, 2, 1.2, ORANGE2, ORANGE1, ORANGE3)
    if e.humeur == "colere":
        trait(t, 10, 8, 15, 9, GRIS1, ep=t.e)
        trait(t, 22, 8, 17, 9, GRIS1, ep=t.e)
    if e.bouche:
        rect(t, 13, 14.5, 6, 0.8 + e.bouche * 0.8, GRIS1)
    else:
        hline(t, 13, 19, 15, GRIS2)


@perso("grande-panne", "spectre-404", "Quatre-Cent-Quatre", ("triste",), "fantôme d'une page effacée : une feuille pâle qui flotte")
def spectre(t, e):
    pts = [(7, 30), (7, 9), (10, 4), (22, 4), (25, 7), (25, 30)]
    poly(t, pts, "#d8d2f0")
    for i in range(4):
        ell(t, 9.2 + i * 4.6, 30.5, 2.2, 1.6, "#b8b0dc" if i % 2 else "#d8d2f0")
    poly(t, [(19, 4), (25, 4), (25, 30), (21, 30)], "#b8b0dc")
    poly(t, [(22, 4), (25, 7), (22, 7)], "#9a90c8")                  # le coin corné
    for i in range(3):
        hline(t, 10, 20 - i * 3, 22 + i * 2, "#b8b0dc")
    yeux(t, 13, 19, 12.5, e, 1.3, iris="#2e2450")
    if not e.bouche and e.humeur == "neutre":
        ell(t, 16, 17.5, 1.1, 1.4, "#2e2450")
    else:
        bouche(t, 16, 17.5, e, 2.6, c="#2e2450", ligne="#2e2450")


@perso("grande-panne", "dateur", "Le Dateur", ("joie", "triste"), "tampon dateur à molette bloqué sur 13 h 37, à sec d'encre")
def dateur(t, e):
    boule(t, 16, 4.6, 3.4, 3.2, BOIS2, BOIS1, BOIS3)                # la poignée
    rect(t, 15, 7, 2, 3, BOIS1)
    rect(t, 7, 10, 18, 15, GRIS3)
    rect(t, 19, 10, 6, 15, GRIS2)
    hline(t, 7, 25, 10, GRIS4)
    # La molette « 13 37 » : quatre petites cases.
    rect(t, 8, 20, 16, 4, GRIS1)
    for i, x in enumerate((9, 12.5, 17, 20.5)):
        rect(t, x, 20.8, 2.6, 2.4, PAPIER)
        vline(t, x + 1.3, 21.2, 23, ENCRE)
    point(t, 16, 21.4, PAPIER)
    point(t, 16, 22.6, PAPIER)
    rect(t, 6, 25, 20, 4, VIO1)                                      # le socle encreur, à sec
    hline(t, 6, 26, 25, VIO2)
    yeux(t, 12.5, 19.5, 14.2, e, 1.0, sourcils=GRIS1)
    bouche(t, 16, 17.6, e, 3)


@perso("grande-panne", "mme-echeance", "Mme Échéance", ("malice",), "la Planificatrice : une dame-calendrier, anneaux sur le front")
def echeance(t, e):
    buste(t, BEIGE2, BEIGE1, BEIGE3, haut=25, largeur=12)
    for i in range(3):
        rect(t, 7 + i * 6.5, 26.5 + (i % 2), 5, 3.5, PAPIER)
        hline(t, 7 + i * 6.5, 12 + i * 6.5, 26.5 + (i % 2), ORANGE2)
    rect(t, 8, 5, 16, 18, PAPIER)
    rect(t, 20, 5, 4, 18, PAPIER_O)
    rect(t, 8, 5, 16, 3.5, ORANGE2)
    hline(t, 8, 24, 8.5, ORANGE1)
    for x in (11, 16, 21):
        ell(t, x, 4.6, 1, 1.6, GRIS2)
        point(t, x, 3.6, GRIS4)
    for j in range(2):
        for i in range(4):
            point(t, 10 + i * 3.6, 20 + j * 1.4, PAPIER_L)
    yeux(t, 13, 19, 12.6, e, 0.95, sourcils=GRIS1, ys=10.4)
    bouche(t, 16, 16.6, e, 3)


@perso("grande-panne", "raccourcis", "Ctrl, Alt et Suppr", ("peur",), "les Raccourcis, passeurs du Marais : trois touches")
def raccourcis(t, e):
    for (x, w, h, c, co, y) in ((2, 11, 12, GRIS3, GRIS2, 15), (14, 8, 11, VIO3, VIO2, 16), (23, 7, 8, ORANGE2, ORANGE1, 19)):
        rect(t, x, y, w, h, co)
        rect(t, x + 0.8, y, w - 1.6, h - 2.2, c)
        hline(t, x + 0.8, x + w - 0.8, y, BLANC if c != GRIS3 else GRIS4)
        cx = x + w / 2
        yeux(t, cx - w * 0.2, cx + w * 0.2, y + h * 0.35, e, 0.7)
        bouche(t, cx, y + h * 0.62, e, w * 0.3)
    # Une petite rame en travers : ils sont passeurs.
    trait(t, 3, 6, 12, 14, BOIS2, ep=t.e)
    ell(t, 3, 6, 1.6, 2.8, BOIS3)


@perso("grande-panne", "touche-s", "S", ("joie",), "petite touche timide qui n'ose plus sauver personne")
def touche_s(t, e):
    rect(t, 7, 9, 18, 18, GRIS2)
    rect(t, 8, 9, 16, 15, "#e6ecf6")
    hline(t, 8, 24, 9, BLANC)
    # Un S gravé, en haut à gauche.
    courbe(t, [(12.8, 11.2), (10, 10.4), (10.2, 13.2), (11.4, 13.3)], BLEU1, ep=t.e)
    courbe(t, [(11.4, 13.3), (13.2, 13.6), (13, 16.2), (10, 15.6)], BLEU1, ep=t.e)
    regard = Etat(e.humeur, e.yeux, e.bouche)
    yeux(t, 14.5, 19.5, 17.5 + (0 if e.humeur == "joie" else 0.6), regard, 0.85, sourcils=GRIS2 if e.humeur != "joie" else None)
    joues(t, 13, 21, 19.6, Etat("tendre"))
    bouche(t, 17, 21.5, e, 2)


@perso("grande-panne", "imprimante", "L'Imprimante", ("colere",), "diva de la file d'impression ; il lui manque toujours du cyan")
def imprimante(t, e):
    rect(t, 9, 3, 14, 7, PAPIER)                                     # la feuille qui sort, en haut
    for i in range(3):
        hline(t, 11, 20 - i * 2, 5 + i * 1.5, PAPIER_L)
    rect(t, 4, 9, 24, 15, BEIGE3)
    rect(t, 20, 9, 8, 15, BEIGE2)
    hline(t, 4, 28, 9, PAPIER)
    rect(t, 6, 24, 20, 5, BEIGE2)
    rect(t, 8, 25, 16, 2, GRIS1)                                     # le bac
    for i, c in enumerate((CYAN1, VIO3, OR2)):
        rect(t, 21 + i * 2, 11, 1.4, 2.4, c if not (i == 0 and e.humeur == "colere") else GRIS3)
    yeux(t, 11, 17, 16, e, 1.0)
    # De longs cils de diva.
    if not e.ferme and e.humeur != "joie":
        for x in (11, 17):
            trait(t, x + 0.6, 14.7, x + 1.6, 13.9, ENCRE, ep=t.e)
            trait(t, x + 1.4, 15.3, x + 2.4, 14.8, ENCRE, ep=1)
    if e.humeur == "colere":
        sourcil(t, 11, 13, e, 3, ENCRE, -1)
        sourcil(t, 17, 13, e, 3, ENCRE, 1)
    bouche(t, 14, 20.6, e, 3.4, c=BOUCHE)


@perso("grande-panne", "brouillon", "Brouillon, le Sans-Titre", ("peur", "tendre", "joie"),
       "« Document sans titre (récupéré) » : une feuille qui tremble, une phrase inachevée")
def brouillon_feuille(t, e):
    pts = [(8, 4), (21, 4), (25, 8), (25, 29), (8, 29)]
    poly(t, pts, PAPIER)
    poly(t, [(20, 4), (21, 4), (25, 8), (25, 29), (21, 29)], PAPIER_O)
    poly(t, [(21, 4), (25, 8), (21, 8)], BEIGE2)
    # La phrase inachevée, au crayon, et les points de suspension.
    hline(t, 10, 22, 21.5, PAPIER_L)
    hline(t, 10, 17, 23.5, PAPIER_L)
    for i in range(3):
        point(t, 18.5 + i * 1.3, 23.5, BLEU1)
    yeux(t, 13, 19, 12.4, e, 1.2, sourcils=PAPIER_L, ys=9.6)
    joues(t, 11.4, 20.6, 15.2, e)
    bouche(t, 16, 16.2, e, 2.6)


@perso("grande-panne", "tic-tac", "Le Tic-Tac", ("joie", "triste"),
       "petit balancier à pattes : un côté tic inquiet, un côté tac détendu")
def tic_tac(t, e):
    ell(t, 16, 3, 1.6, 1.6, OR1)
    rect(t, 15.3, 3, 1.4, 9, OR1)
    vline(t, 15.6, 3, 12, OR3)
    # Le disque, mi-tic (froid, à gauche) mi-tac (chaud, à droite).
    boule(t, 16, 18, 8.5, 8.5, OR2, OR1, OR3)
    ell(t, 16, 18, 7.3, 7.3, "#f3e3a0", cond=lambda x, y, u, v: x < 16)
    ell(t, 16, 18, 7.3, 7.3, "#ffd8a8", cond=lambda x, y, u, v: x >= 16)
    vline(t, 16, 11, 25, OR1)
    for x in (12.5, 19.5):
        rect(t, x - 0.6, 26, 1.2, 4, GRIS1)
        rect(t, x - 1.6, 29.6, 2.6, 1.2, GRIS1)
    # Côté tic : sourcil inquiet. Côté tac : paupière tranquille.
    tic = Etat("triste" if e.humeur in ("neutre", "triste") else e.humeur, e.yeux, e.bouche)
    tac = Etat("tendre" if e.humeur == "neutre" else e.humeur, e.yeux, e.bouche)
    oeil(t, 13, 17, tic, 1.1, cote=-1)
    sourcil(t, 13, 14.6, tic, 2.4, OR1, -1)
    oeil(t, 19, 17, tac, 1.1, cote=1)
    bouche(t, 16, 21.4, e, 3)


@perso("grande-panne", "balayeur", "Le Balayeur", ("triste",), "le Grand Nettoyage : un balai très poli, chapeau rond")
def balayeur(t, e):
    trait(t, 22, 0, 18, 12, BOIS2, ep=t.e + 1)
    poly(t, [(9, 14), (23, 14), (27, 30), (5, 30)], "#d8b870")
    poly(t, [(17, 14), (23, 14), (27, 30), (19, 30)], "#b89450")
    for x in range(7, 27, 2):
        trait(t, 9 + (x - 7) * 0.7, 20, x, 30, "#a88440", ep=1)
    rect(t, 8, 12, 16, 4, GRIS2)
    hline(t, 8, 24, 12, GRIS3)
    # Le chapeau rond, posé de travers sur le manche.
    ell(t, 21, 5.5, 5, 1.2, ENCRE)
    boule(t, 21, 3.6, 3, 2.6, GRIS1, ENCRE, GRIS2, cond=lambda x, y, u, v: v < 0.6)
    yeux(t, 13, 19, 19.6, e, 1.0, iris=ENCRE, sourcils=BOIS1)
    bouche(t, 16, 23.6, e, 3, c=BOUCHE)


# ---------------------------------------------------------------------------------------------------------------------
# Le phare éteint
# ---------------------------------------------------------------------------------------------------------------------
MARINE, MARINE_O, MARINE_C = "#1d3766", "#13254a", "#2e4f86"
BARBE, BARBE_O = "#e6ecf2", "#b8c4d2"
LAITON = "#e8c45e"


@perso("phare-eteint", "anselme", "Anselme, le gardien", ("triste", "joie"),
       "gardien du phare depuis trente ans : barbe blanche, casquette marine, regard voilé")
def anselme(t, e):
    buste(t, MARINE, MARINE_O, MARINE_C, haut=25, largeur=12)
    for y in (27, 30):
        point(t, 16, y, LAITON)
    tete(t, 16, 15.5, 6.6, 7.4, "#e8b892", "#c88f6a")
    # La barbe blanche, large.
    ell(t, 16, 20.5, 7.4, 5.6, BARBE, cond=lambda x, y, u, v: v > -0.45)
    ell(t, 16, 20.5, 7.4, 5.6, BARBE_O, cond=lambda x, y, u, v: v > -0.45 and u > 0.35)
    ell(t, 16, 17.6, 3.6, 1.2, BARBE)                                 # la moustache
    # La casquette de gardien et son insigne.
    ell(t, 16, 10, 7.4, 4.2, MARINE, cond=lambda x, y, u, v: v < 0.25)
    rect(t, 8.6, 9.4, 14.8, 2, MARINE_O)
    poly(t, [(9, 11.2), (23, 11.2), (24, 12.4), (8, 12.4)], ENCRE)
    ell(t, 16, 8.2, 1.2, 1.2, LAITON)
    # Le regard voilé : des yeux pâles, de gros sourcils blancs.
    yeux(t, 13.4, 18.6, 14.6, e, 0.95, iris="#8fa3b8", sourcils=BARBE, ys=13, ls=2.6)
    if e.bouche:
        bouche(t, 16, 19.4, e, 2.6)
    elif e.humeur == "joie":
        courbe(t, [(14.6, 19), (16, 19.8), (17.4, 19)], BARBE_O, ep=t.e)


@perso("phare-eteint", "lison", "Lison", ("malice", "peur", "joie"),
       "onze ans, deux nattes cuivrées, des taches de son, un ciré bleu, les yeux du gardien")
def lison(t, e):
    buste(t, BLEU2, BLEU1, BLEU3, col="#f6e6a8", haut=25.5, largeur=10.5)
    hline(t, 12, 20, 29, BLEU1)
    tete(t, 16, 15.5, 6.2, 7, PEAU, PEAU_O)
    # Cheveux cuivrés, frange, deux nattes.
    ell(t, 16, 11.4, 6.8, 4.6, "#b8652e", cond=lambda x, y, u, v: v < 0.35)
    for x in (9.2, 22.8):
        for j in range(3):
            ell(t, x, 19 + j * 2.4, 1.6, 1.4, "#b8652e" if j % 2 else "#d9803a")
        rect(t, x - 1, 26, 2, 1, BLEU3)
    for i in range(4):
        point(t, 12.4 + i * 0.8 + (2.2 if i > 1 else 0), 18.2 + (i % 2) * 0.5, "#c88f6a")   # taches de son
    yeux(t, 13.4, 18.6, 15.2, e, 1.05, sourcils="#8a4a1f", ys=13.1, ls=1.8)
    joues(t, 12, 20, 18.4, e)
    bouche(t, 16, 20.2, e, 2.4)


@perso("phare-eteint", "tudal", "Tudal", ("colere",), "pêcheur : bonnet de laine orange, barbe de trois jours, gros pull marine")
def tudal(t, e):
    buste(t, MARINE, MARINE_O, MARINE_C, haut=24.5, largeur=13)
    for x in range(6, 27, 3):
        vline(t, x, 25.5, 32, MARINE_O)
    tete(t, 16, 15.5, 6.8, 7.4, "#d9a37a", "#b8805a")
    for i in range(18):
        x, y = 11 + (i * 37 % 10), 18.5 + (i * 13 % 4) * 0.9
        point(t, x, y, "#8a6a52")                                    # la barbe de trois jours
    ell(t, 16, 9.4, 7.4, 4.6, ORANGE2, cond=lambda x, y, u, v: v < 0.55)
    rect(t, 8.6, 10.6, 14.8, 2.4, ORANGE1)
    for x in range(9, 24, 2):
        vline(t, x, 10.8, 13, ORANGE2)
    ell(t, 16, 4.8, 1.8, 1.6, ORANGE3)
    ell(t, 16.4, 16.6, 1.3, 1.6, "#c88f6a")                          # le nez
    yeux(t, 13.2, 18.8, 14.8, e, 0.9, sourcils="#5a3820", ys=13, ls=2.6)
    bouche(t, 16, 19.8, e, 3)


@perso("phare-eteint", "perrine", "Perrine", ("joie",), "aubergiste du Bigorneau : chignon, joues rondes, tablier crème")
def perrine(t, e):
    buste(t, VIO3, VIO2, VIO4, haut=25, largeur=12.5)
    poly(t, [(11, 25), (21, 25), (22, 32), (10, 32)], PAPIER)
    hline(t, 11, 21, 25, PAPIER_O)
    tete(t, 16, 15.5, 7.2, 7.2, PEAU, PEAU_O)
    ell(t, 16, 11, 7.6, 4.4, "#8a5a33", cond=lambda x, y, u, v: v < 0.25)
    boule(t, 16, 5.4, 3.6, 2.8, "#8a5a33", "#5a3820", "#b8844f")
    joues(t, 11.6, 20.4, 18, Etat("joie"))
    yeux(t, 13.2, 18.8, 15, e, 0.95, sourcils="#5a3820", ys=12.8)
    bouche(t, 16, 19.8, e, 3)


@perso("phare-eteint", "odile", "Odile, la maire", ("triste",), "la maire : cheveux gris au carré, lunettes rondes, écharpe bleue")
def odile(t, e):
    buste(t, GRIS2, GRIS1, GRIS3, haut=25, largeur=12)
    poly(t, [(9, 26), (12, 25), (23, 32), (19, 32)], BLEU2)          # l'écharpe en travers
    poly(t, [(11, 25.5), (12, 25), (23, 32), (21.5, 32)], BLEU3)
    tete(t, 16, 15.5, 6.6, 7.4, PEAU, PEAU_O)
    ell(t, 16, 13, 7.8, 6.2, GRIS3, cond=lambda x, y, u, v: v < -0.05 or abs(u) > 0.78)
    ell(t, 16, 13, 7.8, 6.2, GRIS2, cond=lambda x, y, u, v: (v < -0.05 or abs(u) > 0.78) and u > 0.5)
    yeux(t, 13.4, 18.6, 15.2, e, 0.85, sourcils=GRIS1, ys=12.9, ls=1.8)
    for x in (13.4, 18.6):
        t.anneau(x, 15.2, 2.1, 2.1, GRIS1, ep=0.5 if toile.fin() else 1)
    hline(t, 15.4, 16.6, 15, GRIS1)
    bouche(t, 16, 19.8, e, 2.6)


@perso("phare-eteint", "basile", "Basile, l'horloger", ("peur", "triste"),
       "horloger-mécanicien : crâne lisse, couronne de cheveux, loupe vissée à l'œil, moustache")
def basile(t, e):
    buste(t, BOIS2, BOIS1, BOIS3, col=PAPIER, haut=25, largeur=12)
    rect(t, 19, 27, 3, 3, LAITON)                                     # une montre à gousset
    tete(t, 16, 15, 6.8, 7.6, PEAU, PEAU_O)
    ell(t, 16, 15, 6.8, 7.6, "#8a8070", cond=lambda x, y, u, v: abs(u) > 0.82 and v < 0.25)
    if toile.fin():
        trait(t, 13, 9, 15, 8.4, PEAU_C, ep=1)                       # le crâne qui brille
    yeux(t, 13.2, 18.8, 15, e, 0.95, sourcils="#5a5040", ys=12.8)
    # La loupe d'horloger sur l'œil droit.
    t.anneau(18.8, 15, 2.6, 2.6, LAITON, ep=0.6 if toile.fin() else 1)
    ell(t, 16, 19, 3.4, 1.1, "#6a5a48")                                # la moustache
    bouche(t, 16, 20.6, e, 2.4)


@perso("phare-eteint", "vernier", "M. Vernier", (), "inspecteur du Service des Feux : chapeau de pluie et ciré jaunes, jumelles")
def vernier(t, e):
    buste(t, OR2, OR1, OR3, haut=24.5, largeur=12.5)
    for x in (13, 19):
        boule(t, x, 28, 1.8, 2.2, GRIS1, ENCRE, GRIS3)               # les jumelles
    hline(t, 13, 19, 27.4, GRIS1)
    tete(t, 16, 15.8, 6, 7.6, PEAU, PEAU_O)
    ell(t, 16, 10.2, 9.8, 3.2, OR2, cond=lambda x, y, u, v: v > -0.1)  # le chapeau de pluie
    ell(t, 16, 8.6, 6.4, 4.4, OR2, cond=lambda x, y, u, v: v < 0.45)
    ell(t, 16, 8.6, 6.4, 4.4, OR1, cond=lambda x, y, u, v: v < 0.45 and u > 0.45)
    hline(t, 7, 25, 11.8, OR1)
    yeux(t, 13.6, 18.4, 15.4, e, 0.8, sourcils=GRIS1, ys=13.5, ls=2)
    trait(t, 16, 15.4, 16.6, 18, PEAU_O, ep=1)
    bouche(t, 16, 20.6, e, 2.2)


# ---------------------------------------------------------------------------------------------------------------------
# Petit Nuage
# ---------------------------------------------------------------------------------------------------------------------
NU, NU_O, NU_C = "#ffffff", "#c3d3e6", "#ffffff"
FER1, FER2, FER3 = "#8a4a1f", "#b8652e", "#e0995a"


def nuage_corps(t, cx, cy, l, h, c=NU, o=NU_O):
    boules = [(-0.55, 0.2, 0.42), (-0.2, -0.2, 0.55), (0.25, -0.1, 0.5), (0.55, 0.25, 0.38), (0, 0.35, 0.5)]
    for (u, v, r) in boules:
        ell(t, cx + u * l, cy + v * h, r * l, r * l * h / l * 1.6, o)
    for (u, v, r) in boules:
        ell(t, cx + u * l - 0.4, cy + v * h - 0.5, r * l * 0.92, r * l * h / l * 1.5, c)


@perso("petit-nuage", "brouillon", "Brouillon, le petit nuage", ("joie", "triste", "peur"),
       "un tout petit nuage tombé du ciel, trois Pilou de large, qui ne sait pas encore pleuvoir")
def petit_nuage(t, e):
    nuage_corps(t, 16, 17, 12, 7.5)
    if toile.fin():
        ell(t, 11, 12.6, 2, 0.8, "#eef4fb")
    yeux(t, 13, 19, 16.4, e, 1.2, iris="#2e3a5c")
    joues(t, 10.6, 21.4, 19.2, Etat("tendre"), "#f5c8d6")
    bouche(t, 16, 20.2, e, 2.2)
    if e.humeur == "triste":
        ell(t, 22, 27.5, 0.7, 1.1, LARME)                               # une goutte, enfin


@perso("petit-nuage", "tournebise", "Tournebise", ("triste", "tendre"),
       "vieille girouette en fer rouillé, un coq, qui pointe toujours vers la montagne")
def tournebise(t, e):
    vline(t, 16, 20, 32, ENCRE)
    hline(t, 9, 23, 26, ENCRE)
    poly(t, [(23, 24.8), (25.6, 26), (23, 27.2)], ENCRE)
    # Le coq de fer, de profil (il regarde à droite).
    poly(t, [(7, 18), (10, 12), (15, 11), (19, 7), (23, 6), (25, 9), (23.5, 12), (21, 16), (17, 20), (11, 20)], FER2)
    poly(t, [(15, 15), (21, 16), (17, 20), (11, 20)], FER1)
    poly(t, [(7, 18), (4, 9), (8, 12), (6, 5), (10, 11)], FER1)       # la queue en faucille
    poly(t, [(19, 6.5), (20, 3.5), (21.5, 5.5), (22.5, 3), (23.5, 6)], FER3)   # la crête
    poly(t, [(25, 8.5), (28, 9.6), (25, 10.6)], OR2)                  # le bec
    for (x, y) in ((12, 13), (17, 17.5), (9, 16)):
        point(t, x, y, FER3)                                          # rouille claire
    oeil(t, 22.6, 8.4, e, 0.85, iris=ENCRE, blanc=OR3, cote=1)
    if e.humeur == "triste":
        sourcil(t, 22.6, 6.8, e, 1.8, ENCRE, 1)
    if e.bouche:
        poly(t, [(25, 9.6), (27.4, 10.2 + e.bouche * 0.6), (25, 10.8)], BOUCHE)


@perso("petit-nuage", "ondee", "Ondée", ("tendre",), "la plus vieille du troupeau : grise, large comme une vallée")
def ondee(t, e):
    nuage_corps(t, 16, 16, 15, 10, "#c3cad8", "#8790a4")
    for i in range(5):
        trait(t, 8 + i * 4, 27, 7.4 + i * 4, 29.5, "#8fb6d8", ep=1)       # une pluie très douce
    yeux(t, 12.4, 19.6, 15.6, Etat("tendre" if e.humeur == "neutre" and not e.bouche else e.humeur, e.yeux, e.bouche), 1.2,
         iris="#3c4252", paupiere="#3c4252")
    for x in (10, 22):
        trait(t, x - 1, 13.2, x + 0.6, 13.8, "#8790a4", ep=1)            # des rides de vieux nuage
    bouche(t, 16, 20, Etat("tendre", e.yeux, e.bouche) if e.humeur == "neutre" else e, 3)


@perso("petit-nuage", "mi-bemol", "Mi-Bémol", ("joie",), "cheffe du chœur des rainettes, sarcelle, une baguette de jonc")
def mi_bemol(t, e):
    RA, RA_O, RA_C = "#2f8f9c", "#1d6578", "#5bb3ae"
    boule(t, 16, 21, 10, 8, RA, RA_O, RA_C)
    ell(t, 16, 24.5, 6, 4, "#f6e6a8")                                  # le ventre clair
    for x in (10.5, 21.5):
        boule(t, x, 12.6, 3.6, 3.4, RA, RA_O)
        ell(t, x, 12.6, 2.6, 2.6, BLANC)
    yeux(t, 10.5, 21.5, 12.8, e, 1.1, iris=ENCRE)
    bouche(t, 16, 19.4, Etat("joie" if e.humeur == "neutre" and not e.bouche else e.humeur, e.yeux, e.bouche), 6)
    trait(t, 26, 26, 30, 17, BOIS3, ep=1)                              # la baguette
    ell(t, 25.5, 26, 1.4, 1.1, RA)


@perso("petit-nuage", "dentelle", "Dentelle", ("malice",), "araignée marchande de rosée, qui se fait payer en fil")
def dentelle(t, e):
    for i in range(4):
        for s in (-1, 1):
            a = 0.35 + i * 0.32
            x1, y1 = 16 + s * 9, 16 + (i - 1.5) * 4
            courbe(t, [(16 + s * 4, 18), (16 + s * 7, 11 + i * 3), (x1 + s * 4, y1 + 6)], VIO1, ep=t.e)
    vline(t, 16, 0, 8, "#c9bfe8")
    boule(t, 16, 21, 6.4, 5.6, VIO2, VIO1, VIO3)
    boule(t, 16, 13.5, 4.8, 4.2, VIO2, VIO1, VIO3)
    for (x, y) in ((13.4, 11.6), (18.6, 11.6)):
        point(t, x, y, "#ffd29a")                                    # les petits yeux du haut
    yeux(t, 14, 18, 14, e, 1.0, iris=ENCRE, blanc="#f2eefc")
    bouche(t, 16, 16.8, e, 2)
    ell(t, 25, 26, 2, 2, "#b4dbff")                                   # une goutte de rosée à vendre
    if toile.fin():
        point(t, 24.4, 25.4, BLANC)


@perso("petit-nuage", "madame-bocal", "Madame Bocal", ("joie",), "marmotte du col, qui met tout en conserve avant l'hiver")
def bocal(t, e):
    MA, MA_O, MA_C = "#a07a52", "#6b4a2e", "#d8bd92"
    boule(t, 16, 20, 10, 10, MA, MA_O, MA_C)
    boule(t, 16, 11, 7, 6.4, MA, MA_O, MA_C)
    for x in (10.2, 21.8):
        ell(t, x, 6.4, 1.6, 1.4, MA_O)
    ell(t, 16, 13.6, 3.6, 2.4, MA_C)
    ell(t, 16, 12.4, 1.2, 0.8, ENCRE)                                  # la truffe
    yeux(t, 13, 19, 9.6, e, 0.9)
    bouche(t, 16, 14.8, e, 2)
    if e.bouche == 0 and e.humeur != "joie":
        rect(t, 15.2, 15, 1.6, 1.2, BLANC)                              # les incisives
    # Le bocal serré contre elle (un courant d'air dedans).
    rect(t, 11, 20, 10, 9, "#cfe0ea")
    rect(t, 11, 19, 10, 1.6, OR1)
    courbe(t, [(12.5, 25), (15, 22.5), (17, 26), (19.5, 23)], "#8fb6d8", ep=1)
    for x in (10, 22):
        ell(t, x, 24, 2, 1.6, MA_O)


@perso("petit-nuage", "froisseuses", "Les Froisseuses", (), "chauves-souris du Trou-qui-Siffle, au bruit de papier froissé")
def froisseuses(t, e):
    for s in (-1, 1):
        poly(t, [(16, 16), (16 + s * 15, 8), (16 + s * 13, 15), (16 + s * 15, 20), (16 + s * 10, 18), (16 + s * 7, 22)], "#46406e")
        for k in range(3):
            trait(t, 16 + s * 3, 17, 16 + s * (8 + k * 3), 9 + k * 4, "#5c5a9a", ep=1)
    boule(t, 16, 17, 5, 5.4, "#5c5a9a", "#3a3466", "#8a79b8")
    for s in (-1, 1):
        poly(t, [(16 + s * 2, 13), (16 + s * 4.5, 8.5), (16 + s * 4.5, 13.5)], "#5c5a9a")
    yeux(t, 14, 18, 16.4, e, 0.9, iris="#ffd29a")
    bouche(t, 16, 19.6, e, 1.8)


@perso("petit-nuage", "enclumes", "Les Enclumes", ("colere",), "nuages d'orage, larges et plats dessus : ils avalent, c'est tout")
def enclumes(t, e):
    nuage_corps(t, 16, 19, 13, 9, "#5c6478", "#3c4252")
    ell(t, 16, 9.6, 14, 2.6, "#3c4252")                               # le dessus plat, en enclume
    ell(t, 16, 9.2, 13, 1.8, "#5c6478")
    hline(t, 5, 27, 8, "#8790a4")
    yeux(t, 12, 20, 17.4, e, 1.2, iris="#ffd29a", sourcils="#262a35", ls=3.2, ys=15)
    bouche(t, 16, 22, e, 4, c="#262a35")
    if e.humeur == "colere":
        poly(t, [(23, 25), (21, 29), (23, 29), (21.5, 32)], OR2)       # un petit éclair (une forme, pas une couleur)


@perso("petit-nuage", "bergeronnette", "La bergeronnette", (), "petit oiseau gris et blanc, pressé, à la longue queue")
def bergeronnette(t, e):
    poly(t, [(4, 24), (12, 19), (13, 22), (5, 26)], ENCRE)                 # la longue queue
    boule(t, 16, 19, 6.4, 4.6, GRIS3, GRIS2, GRIS4)
    ell(t, 17, 21, 4, 2.4, BLANC)
    boule(t, 21, 12.5, 4, 3.8, GRIS4, GRIS3)
    ell(t, 21, 10, 4, 2, ENCRE, cond=lambda x, y, u, v: v < 0.3)         # la calotte noire
    ell(t, 21.5, 14.6, 3, 1.4, BLANC)
    poly(t, [(24.6, 12), (28, 12.8), (24.6, 13.6)], "#3b4654")
    oeil(t, 22.6, 12, e, 0.75, iris=ENCRE, cote=1)
    if e.bouche:
        poly(t, [(24.6, 13.2), (27, 13.8 + e.bouche * 0.5), (24.6, 14.2)], BOUCHE)
    for x in (15, 18):
        vline(t, x, 23.5, 27, "#3b4654")


# ---------------------------------------------------------------------------------------------------------------------
# Fabrication
# ---------------------------------------------------------------------------------------------------------------------
IMAGES = (("o", 0, False), ("o", 0, True), ("f", 0, False), ("o", 1, False), ("o", 2, False))
DUREE = 150


def lever(t, coupe):
    """Respiration : tout ce qui est au-dessus de la coupe monte d'un pixel réel (le bas reste posé)."""
    Y = int(coupe * t.e)
    for y in range(0, Y):
        t.g[y] = t.g[y + 1][:] if y + 1 < t.H else [None] * t.W


def images(f, humeur, coupe):
    ims = []
    for (yeux_, bouche_, souffle) in IMAGES:
        t = Toile(W, H)
        f(t, Etat(humeur, yeux_, bouche_))
        t.contour(CERNE)
        if souffle:
            lever(t, coupe)
        ims.append(t)
    return ims


def id_portrait(campagne, perso_, expression=""):
    base = "portrait-%s-%s" % (campagne, perso_)
    return base if expression in ("", "neutre") else base + "-" + expression


def ids():
    r = []
    for (c, p), (nom, desc, exprs, f, coupe) in sorted(PERSOS.items()):
        r.append(id_portrait(c, p))
        r.extend(id_portrait(c, p, x) for x in exprs)
    return r


def tout():
    if toile.FINS is not None:
        toile.FINS.update(ids())
    for (c, p), (nom, desc, exprs, f, coupe) in sorted(PERSOS.items()):
        for x in ("neutre",) + exprs:
            sid = id_portrait(c, p, x)
            ims = images(f, x, coupe)
            ecrire(sid, ims, slot="objet", ancre="aucun", duree=DUREE,
                   commentaire="Portrait de campagne : %s (%s) — %s" % (nom, x, desc))
            # La disposition des images (docs/SPRITES.md) : une clé que les anciens lecteurs ignorent.
            _poser_cle(sid, ims[0].e)
            if ims[0].e == 1:
                IDS.append(sid)


def _poser_cle(sid, e):
    import os
    chemin = os.path.join(toile.SORTIE if e == 1 else toile.SORTIE2, sid + ".txt")
    if not os.path.isfile(chemin):
        return
    with open(chemin, encoding="utf-8") as fh:
        lignes = fh.read().split("\n")
    if any(l.startswith("portrait:") for l in lignes):
        return
    i = next(k for k, l in enumerate(lignes) if l.startswith("duree:"))
    lignes.insert(i + 1, "portrait: repos 0 1 cligne 2 parle 3 4")
    with open(chemin, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lignes))


def personnages():
    """{campagne: {id: nom}} : pour le validateur et la documentation."""
    r = {}
    for (c, p), (nom, *_rest) in PERSOS.items():
        r.setdefault(c, {})[p] = nom
    return r
