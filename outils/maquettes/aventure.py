#!/usr/bin/env python3
"""Maquettes de la fenêtre « Aventure » du PC (apps/PilouBureau/FenetreAventure.cs), rendues hors WPF.

La mise en page reprend celle de la fenêtre (marges, tailles, couleurs, police pixel de Police.cs) ; Segoe UI est
remplacée par Inter (et DejaVu Sans pour les signes), un peu plus large : les retours à la ligne peuvent différer.

    PILOU_PLANCHES_AVENTURE=/tmp/aventure/matiere dotnet test apps/PilouBureau/tests --filter PlanchesAventure
    python3 outils/maquettes/aventure.py /tmp/aventure/matiere /tmp/aventure
"""
import json
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

S = 2  # rendu à 200 % (unités WPF × 2)
RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---- Couleurs (FenetreAventure.cs, Bandeau.cs)
FOND, CASE, CASE_CLAIRE, FERME = "#0f1324", "#1f2540", "#2a3156", "#3b4654"
NUIT, NUIT2, BORD, ARGENT, ARGENT_CLAIR = "#151a2e", "#1f2540", "#6a5acd", "#adbac7", "#e6ecf2"
BLEU, BLEU_SOMBRE, ORANGE, VIOLET, ENCRE, BLEU_CLAIR = "#6cb6ff", "#2d333b", "#f69d50", "#9b8cff", "#1c2128", "#b4dbff"
PARCHEMIN, PARCHEMIN_BORD, ENCRE_PALE, OMBRE, CREME, ARDOISE, OR = "#efe0c0", "#8a6e4b", "#5b4a34", "#0a0d1a", "#fff6e0", "#768390", "#f5d76e"
TEINTES_TON = {"humour": ORANGE, "mystere": VIOLET, "emotion": "#e8d5b0", "epique": BLEU}
CIELS = {"humour": ("#1c2a55", "#c9774a"), "mystere": ("#0d1022", "#3a2f6b"), "emotion": ("#1d2440", "#8d7a96"), "epique": ("#071a33", "#2f6fb0")}
COLLINES = {"humour": ("#3a3f6e", "#252a4d"), "mystere": ("#221f44", "#14142b"), "emotion": ("#4a4466", "#2d2a45"), "epique": ("#173d66", "#0f2645")}

INTER = "/usr/share/fonts/opentype/inter/Inter-{}.otf"
DEJAVU = "/usr/share/fonts/truetype/dejavu/DejaVuSans{}.ttf"
_polices = {}


def police(taille, gras=False, italique=False, symbole=False, mono=False):
    cle = (taille, gras, italique, symbole, mono)
    if cle not in _polices:
        if mono:
            chemin = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono{}.ttf".format("-Bold" if gras else "")
            t = taille * 0.92
        elif symbole:
            chemin, t = DEJAVU.format("-Bold" if gras else ""), taille * 0.95
        else:
            nom = ("SemiBold" if gras else "Regular") + ("Italic" if italique else "")
            if nom == "RegularItalic":
                nom = "Italic"
            chemin, t = INTER.format(nom), taille * 0.93
        _polices[cle] = ImageFont.truetype(chemin, int(round(t * S)))
    return _polices[cle]


def symbole(c):
    return ord(c) > 0x2000 and c not in "’…«»–—·"


def rgb(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


# ---- Police pixel : les glyphes lus dans Police.cs

def glyphes():
    src = open(os.path.join(RACINE, "apps/PilouBureau/Police.cs"), encoding="utf-8").read()
    g = {}
    for m in re.finditer(r"\['(.|\\')'\] = new\[\] \{ ([^}]*) \}", src):
        c = m.group(1).replace("\\'", "'")
        g[c] = re.findall(r'"([01]+)"', m.group(2))
    return g


GLYPHES = glyphes()


def motif_texte(texte):
    lignes = [""] * 5
    for i, c in enumerate(texte):
        gl = GLYPHES.get(c, GLYPHES[" "])
        for r in range(5):
            lignes[r] += ("0" if i else "") + gl[r]
    return lignes


class Toile:
    def __init__(self, w, h, fond=FOND):
        self.w, self.h = w, h
        self.im = Image.new("RGBA", (w * S, h * S), rgb(fond))
        self.d = ImageDraw.Draw(self.im)

    def rect(self, x, y, w, h, c, a=255):
        if w <= 0 or h <= 0:
            return
        if a < 255:
            calque = Image.new("RGBA", self.im.size, (0, 0, 0, 0))
            ImageDraw.Draw(calque).rectangle([x * S, y * S, (x + w) * S - 1, (y + h) * S - 1], fill=rgb(c, a))
            self.im.alpha_composite(calque)
        else:
            self.d.rectangle([round(x * S), round(y * S), round((x + w) * S) - 1, round((y + h) * S) - 1], fill=rgb(c))

    def cadre(self, x, y, w, h, c, e=2):
        self.rect(x, y, w, e, c)
        self.rect(x, y + h - e, w, e, c)
        self.rect(x, y, e, h, c)
        self.rect(x + w - e, y, e, h, c)

    def boite(self, x, y, w, h, fond, bord=None, e=2):
        self.rect(x, y, w, h, fond)
        if bord:
            self.cadre(x, y, w, h, bord, e)

    def degrade(self, x, y, w, h, haut, bas):
        a, b = rgb(haut), rgb(bas)
        for i in range(int(h * S)):
            k = i / max(1, h * S - 1)
            c = tuple(int(a[j] + (b[j] - a[j]) * k) for j in range(3)) + (255,)
            self.d.line([(x * S, y * S + i), ((x + w) * S - 1, y * S + i)], fill=c)

    def image(self, chemin, x, y, w, h):
        im = Image.open(chemin).convert("RGBA").resize((int(w * S), int(h * S)), Image.NEAREST)
        self.im.alpha_composite(im, (int(x * S), int(y * S)))

    # Texte en police pixel ; contour comme Pixels (cellules voisines), marge d'une cellule.
    def pixel(self, texte, x, y, cellule, c, contour=None):
        m = motif_texte(texte.upper())
        h, w = 5, len(m[0])
        plein = lambda r, k: 0 <= r < h and 0 <= k < w and m[r][k] == "1"
        for r in range(-1, h + 1):
            for k in range(-1, w + 1):
                if plein(r, k):
                    col = c
                elif contour and (plein(r - 1, k) or plein(r + 1, k) or plein(r, k - 1) or plein(r, k + 1)):
                    col = contour
                else:
                    continue
                self.rect(x + (k + 1) * cellule, y + (r + 1) * cellule, cellule, cellule, col)
        return (w + 2) * cellule, (h + 2) * cellule

    # Texte (Segoe UI → Inter, signes → DejaVu), retours à la ligne au mot ; rend la hauteur.
    def largeur(self, texte, taille, gras=False, italique=False):
        return sum(police(taille, gras, italique, symbole(c)).getlength(c) for c in texte) / S

    def texte(self, texte, x, y, taille, c, gras=False, italique=False, largeur=None, interligne=None, centre=False, mono=False):
        interligne = interligne or taille * 1.33
        lignes = [texte] if largeur is None else self.couper(texte, taille, gras, italique, largeur)
        for i, l in enumerate(lignes):
            lx = x
            if centre and largeur:
                lx = x + (largeur - self.largeur(l, taille, gras, italique)) / 2
            for ch in l:
                f = police(taille, gras, italique, symbole(ch), mono)
                self.d.text((lx * S, (y + i * interligne + (interligne - taille * 1.2) / 2) * S), ch, font=f, fill=rgb(c))
                lx += f.getlength(ch) / S
        return len(lignes) * interligne

    def couper(self, texte, taille, gras, italique, largeur):
        lignes, l = [], ""
        for mot in texte.split(" "):
            essai = (l + " " + mot).strip()
            if self.largeur(essai, taille, gras, italique) <= largeur or not l:
                l = essai
            else:
                lignes.append(l)
                l = mot
        lignes.append(l)
        return lignes

    def hauteur(self, texte, taille, largeur, gras=False, interligne=None):
        return len(self.couper(texte, taille, gras, False, largeur)) * (interligne or taille * 1.33)

    def bouton(self, x, y, texte, principal=False, taille=13, largeur_min=90, survol=False):
        w = max(largeur_min, self.largeur(texte, taille, True) + 28 + 4)
        h = taille * 1.33 + 14 + 4
        self.rect(x + 3, y + 3, w, h, OMBRE)
        dx = -1 if survol else 0
        self.boite(x + dx, y + dx, w, h, ORANGE if principal else CASE_CLAIRE, ORANGE if survol else (ENCRE if principal else BORD))
        self.texte(texte, x + 16 + dx, y + 9 + dx, taille, ENCRE if principal else ARGENT_CLAIR, gras=True)
        return w, h

    def sauver(self, chemin):
        self.im.convert("RGB").save(chemin)


class Hasard:
    """Boutique.cs, Hasard (xorshift*), pour les mêmes étoiles et collines que la fenêtre."""
    def __init__(self, graine):
        self.s = graine or 0x9E3779B97F4A7C15

    @staticmethod
    def graine(s):
        h = 14695981039346656037
        for c in s:
            h ^= ord(c)
            h = (h * 1099511628211) & 0xFFFFFFFFFFFFFFFF
        return h

    def brut(self):
        m = 0xFFFFFFFFFFFFFFFF
        self.s ^= self.s >> 12
        self.s ^= (self.s << 25) & m
        self.s ^= self.s >> 27
        return (self.s * 2685821657736338717) & m

    def suivant(self, n):
        return self.brut() % n if n > 0 else 0


def ciel(t, x, y, w, h, ton, graine, collines=True):
    haut, bas = CIELS.get(ton, (NUIT, FERME))
    t.degrade(x, y, w, h, haut, bas)
    r = Hasard(graine)
    for _ in range(int(w * h / 900)):
        sx, sy = r.suivant(int(w)), r.suivant(int(h * 0.6))
        s = 3 if r.suivant(5) == 0 else 2
        c = "#ffd8b0" if r.suivant(4) == 0 else "#e6ecf2"
        t.rect(x + sx, y + sy, s, s, c, int(255 * (0.35 + r.suivant(60) / 100)))
    if collines:
        import math
        r = Hasard(graine ^ 0x5bd1e995)
        loin, pres = COLLINES.get(ton, (BLEU_SOMBRE, NUIT2))
        for teinte, base, ampleur in ((loin, 0.62, 0.16), (pres, 0.78, 0.12)):
            phase, f = r.suivant(628) / 100, 1.5 + r.suivant(150) / 100
            for xx in range(0, int(w), 4):
                yy = h * (base - ampleur * math.sin(xx / w * math.pi * f + phase) * math.sin(xx / w * 2.3 + phase / 2))
                yy = round(yy / 4) * 4
                t.rect(x + xx, y + yy, 4, h - yy, teinte)


def cases(t, x, y, part, n, plein, w=9, h=8):
    pleines = round(max(0, min(1, part)) * n)
    for i in range(n):
        if i < pleines:
            t.rect(x + i * (w + 2), y, w, h, plein)
        else:
            t.boite(x + i * (w + 2), y, w, h, NUIT, BORD, 1)
    return n * (w + 2)


def bandeau(t, x, y, w):
    h = 54
    t.boite(x, y, w, h, NUIT, BORD)
    t.boite(x + 12, y + 8, 52, 38, NUIT2, VIOLET)
    t.pixel("NIV", x + 26, y + 9, 2, ARGENT)
    t.pixel("6", x + 30, y + 21, 4, ARGENT_CLAIR, ENCRE)
    t.texte("Explorateur du bureau", x + 76, y + 8, 11, ARGENT)
    for i in range(20):
        c = BLEU if i < 13 else BLEU_SOMBRE
        t.rect(x + 76 + i * 8, y + 25, 7, 8, c)
        t.rect(x + 76 + i * 8, y + 25, 7, 1, BLEU_CLAIR if i < 13 else ENCRE)
    t.texte("312 / 480 xp · encore 168 xp avant le niveau 7", x + 76, y + 35, 10.5, ARGENT)
    t.texte("1 440 po", x + w - 98, y + 15, 17, ORANGE, gras=True, mono=True)
    t.rect(x + w - 118, y + 19, 14, 14, ORANGE)
    t.rect(x + w - 115, y + 22, 8, 8, "#ffc89a")
    return h


def tete(t, x, y, w, onglets, actif):
    larg, haut = t.pixel("AVENTURE", x, y, 5, ORANGE, BORD)
    t.texte("Pilou t'écrit, tu choisis, il part pour de vrai.", x + larg + 14, y + haut - 20, 12, ARGENT, italique=True)
    ox = x + w
    for nom in reversed(onglets):
        lw = t.largeur(nom, 12, True) + 24 + 4
        ox -= lw + 8
        t.rect(ox + 3, y + 12 + 3, lw, 30, OMBRE)
        t.boite(ox, y + 12, lw, 30, BORD if nom == actif else CASE, VIOLET if nom == actif else BORD)
        t.texte(nom, ox + 14, y + 18, 12, ARGENT_CLAIR, gras=True)
    return haut


def bulle_pilou(t, x, y, w, texte, mat, humeur, tete_=True, ecrit=None):
    """Un message de Pilou : parchemin, petite tête au début d'une série. Rend la hauteur (marge comprise)."""
    bw = min(560, w - 40 - 60)
    contenu = texte if ecrit is None else texte[:ecrit] + "▌"
    th = t.hauteur(texte if ecrit is None else contenu, 13.5, bw - 28, interligne=20)
    bh = th + 17 + 4
    if tete_:
        t.image(os.path.join(mat, f"pilou-{humeur if humeur not in ('', 'neutre') else 'repos'}.png"), x, y, 34, 40)
        # la pointe en escalier
        for r, ligne in enumerate(["0001", "0012", "0122", "0012", "0001"]):
            for k, v in enumerate(ligne):
                if v != "0":
                    t.rect(x + 40 - 8 + 2 + k * 2, y + 10 + r * 2, 2, 2, PARCHEMIN_BORD if v == "1" else PARCHEMIN)
    real = min(bw, max(t.largeur(l, 13.5) for l in t.couper(contenu, 13.5, False, False, bw - 28)) + 28)
    t.boite(x + 40, y, real, bh, PARCHEMIN, PARCHEMIN_BORD)
    t.texte(contenu, x + 40 + 14, y + 10, 13.5, ENCRE, largeur=bw - 28, interligne=20)
    return bh + 10


def bulle_joueur(t, x, y, w, texte):
    tw = min(460 - 28, t.largeur("▶ " + texte, 13, True))
    th = t.hauteur("▶ " + texte, 13, 460 - 28, gras=True)
    bx = x + w - tw - 28
    t.texte("toi", bx + tw + 28 - 4 - t.largeur("toi", 10.5), y, 10.5, VIOLET)
    t.boite(bx, y + 16, tw + 28, th + 15 + 4, CASE_CLAIRE, VIOLET)
    t.texte("▶ " + texte, bx + 14, y + 16 + 9, 13, ARGENT_CLAIR, gras=True, largeur=460 - 28)
    return 16 + th + 19 + 14


def separateur(t, x, y, w, texte):
    m = motif_texte(texte.upper())
    lw = (len(m[0]) + 2) * 2
    t.rect(x, y + 10 + 7, (w - lw) / 2 - 10, 2, BORD)
    t.pixel(texte, x + (w - lw) / 2, y + 10, 2, ORANGE, ENCRE)
    t.rect(x + (w + lw) / 2 + 10, y + 10 + 7, (w - lw) / 2 - 10, 2, BORD)
    return 10 + 14 + 14


def option(t, x, y, n, libelle, survol=False):
    lw = min(300, t.largeur(libelle, 13.5, True))
    lignes = t.couper(libelle, 13.5, True, False, 300)
    lw = max(t.largeur(l, 13.5, True) for l in lignes)
    w = max(220, min(360, lw + 28 + 4 + 30))
    h = max(len(lignes) * 18, 21) + 14 + 4
    t.rect(x + 3, y + 3, w, h, OMBRE)
    d = -1 if survol else 0
    t.boite(x + d, y + d, w, h, CASE_CLAIRE, ORANGE if survol else BORD)
    t.boite(x + 16 + d, y + (h - 21) / 2 + d, 20, 21, NUIT, BORD, 1)
    t.pixel(str(n), x + 16 + 4 + d, y + (h - 21) / 2 + 2 + d, 2, ORANGE)
    yy = y + (h - len(lignes) * 18) / 2 + d
    for l in lignes:
        t.texte(l, x + 16 + 30 + d, yy, 13.5, ARGENT_CLAIR, gras=True, interligne=18)
        yy += 18
    return w, h


NOM_HUMEUR = {"joie": "◠ Pilou est tout content", "peur": "◌ Pilou a un peu peur", "triste": "◡ Pilou est triste", "surpris": "◯ Pilou est surpris",
              "determine": "▲ Pilou est décidé", "fatigue": "◡ Pilou est fatigué", "tendre": "♥ Pilou est attendri", "colere": "◆ Pilou est fâché",
              "malice": "◠ Pilou a une idée"}


def lecture(mat, v, sortie, mode, epreuves=None):
    W, H = 1020, 720
    t = Toile(W, H)
    x0, y0, w0 = 14, 10, W - 28
    y = y0 + bandeau(t, x0, y0, w0) + 10
    y += tete(t, x0, y, w0, ["✉ En cours", "☰ Bibliothèque", "❖ Carnet"], "✉ En cours") + 10
    corps_y, corps_h = y, H - 12 - y
    ton = v["ton"]

    # ---- À gauche
    gx, gw = x0, 232 - 12
    t.boite(gx, corps_y, gw, corps_h, NUIT, BORD)
    px, py, pw = gx + 2 + 12, corps_y + 2 + 12, gw - 4 - 24
    ciel(t, px, py, pw, 206, ton, 7, collines=False)
    t.rect(px, py + 206 - 26, pw, 26, "#16365e")
    humeur = v["fil"][-1]["humeur"] if v["fil"] else v["humeur"]
    if mode == "epreuve":
        humeur = "determine"
    t.image(os.path.join(mat, f"pilou-{humeur if humeur not in ('', 'neutre') else 'repos'}.png"), px + (pw - 168) / 2, py + 206 - 6 - 196, 168, 196)
    t.cadre(px, py, pw, 206, OMBRE)
    yy = py + 206 + 6
    nh = NOM_HUMEUR.get(humeur, "· Pilou t'écoute")
    t.texte(nh, px + (pw - t.largeur(nh, 11.5, italique=True)) / 2, yy, 11.5, VIOLET, italique=True)
    yy += 16 + 10
    t.pixel(f"CHAPITRE {v['chapitre']}/{v['chapitres']}", px, yy, 2, ORANGE, ENCRE)
    yy += 14 + 6
    yy += t.texte(v["chapitreTitre"], px, yy, 14, ARGENT_CLAIR, gras=True, largeur=pw)
    yy += 6
    cw = cases(t, px, yy + 2, v["progression"], 14, ORANGE)
    t.texte(f"  {round(v['progression'] * 100)} %", px + cw, yy - 1, 11, ARGENT)
    yy += 14 + 6
    yy += t.texte("▸ " + v["lieu"], px, yy, 12, BLEU_CLAIR) + 12
    t.pixel("SAC", px, yy, 2, VIOLET, ENCRE)
    yy += 14 + 6
    for o in v["objets"] or []:
        ow = t.largeur(o, 12, True) + 16
        t.boite(px, yy, ow + 2, 22, NUIT, ARGENT_CLAIR, 1)
        t.texte(o, px + 9, yy + 2, 12, ARGENT_CLAIR, gras=True)
        yy += 28
    if not v["objets"]:
        t.texte("rien pour l'instant", px, yy, 11.5, ARGENT)
    by = corps_y + corps_h - 2 - 12 - 2 * (13 + 14 + 4 + 8)
    for lib in ("☰ Bibliothèque", "◌ Mettre de côté…"):
        bh = 12 * 1.33 + 14 + 4
        t.rect(px + 3, by + 3, pw, bh, OMBRE)
        t.boite(px, by, pw, bh, CASE_CLAIRE, BORD)
        t.texte(lib, px + 14, by + 9, 12, ARGENT_CLAIR, gras=True)
        by += bh + 8

    # ---- À droite
    dx, dw = x0 + 232, w0 - 232
    t.boite(dx, corps_y, dw, corps_h, "#121729", BORD)
    ix, iw = dx + 2, dw - 4
    ciel(t, ix, corps_y + 2, iw, 118, ton, Hasard.graine(v["decor"] + "|" + v["lieu"]))
    for i in range(56):
        t.rect(ix, corps_y + 2 + 118 - 56 + i, iw, 1, "#0f1324", int(200 * i / 55))
    t.texte(f"{v['campagne']} · chapitre {v['chapitre']} · {v['chapitreTitre']}", ix + 14, corps_y + 2 + 118 - 10 - 21 - 16, 11.5, CREME)
    t.pixel(v["lieu"], ix + 14, corps_y + 2 + 118 - 10 - 21, 3, CREME, NUIT)
    t.rect(ix, corps_y + 2 + 118 - 2, iw, 2, BORD)

    # zone d'action (mesurée d'abord : elle pousse le fil)
    action = construire_action(t, v, mode, iw, epreuves, mat, mesure=True)
    ah = action
    ay = corps_y + corps_h - 2 - ah
    fy0, fy1 = corps_y + 2 + 118, ay
    # le fil, aligné en bas (il défile vers la fin)
    elems = []
    prec = None
    fil = v["fil"]
    if mode == "lecture_ecrit":
        fil = fil
    for i, x in enumerate(fil):
        elems.append((x, prec))
        prec = x["sorte"]
    fx, fw = ix + 18, iw - 36
    hauteurs = []
    calque = Toile(int(fw) + 10, 3000, "#121729")
    yy = 0
    for i, (x, prec) in enumerate(elems):
        ecrit = None
        if mode == "lecture" and i == len(elems) - 1:
            ecrit = int(len(x["texte"]) * 0.62)
        if x["sorte"] == "Pilou":
            yy += bulle_pilou(calque, 0, yy, fw, x["texte"], mat, x["humeur"], prec != "Pilou", ecrit)
        elif x["sorte"] == "Joueur":
            yy += bulle_joueur(calque, 90, yy + 2, fw - 90, x["texte"]) + 2
        elif x["sorte"] == "Chapitre":
            yy += separateur(calque, 0, yy, fw, x["texte"])
        hauteurs.append(yy)
    if mode == "lecture":
        calque.texte("Pilou écrit", 46, yy + 4, 11.5, ARGENT)
        for k in range(3):
            calque.rect(46 + calque.largeur("Pilou écrit", 11.5) + 6 + k * 7, yy + 12, 4, 4, ARGENT, 255 if k == 1 else 80)
        yy += 24
    yy += 18
    visible = fy1 - fy0 - 14
    haut = max(0, yy - visible)
    morceau = calque.im.crop((0, int(haut * S), int((fw + 10) * S), int(yy * S)))
    t.im.alpha_composite(morceau, (int(fx * S), int((fy0 + 14 + max(0, visible - yy)) * S)))
    for i in range(22):  # le haut du fil s'efface sous la bande de décor
        t.rect(ix, fy0 + i, iw - 10, 1, "#121729", int(255 * (1 - i / 22)))
    # barre de défilement
    if yy > visible:
        t.rect(ix + iw - 10, fy0, 10, fy1 - fy0, "#121729")
        t.rect(ix + iw - 10, fy0, 1, fy1 - fy0, CASE)
        part = visible / yy
        th = max(30, (fy1 - fy0) * part)
        t.boite(ix + iw - 8, fy1 - th - 2, 6, th, FERME, BORD, 1)
    t.rect(ix, ay, iw, ah, NUIT2)
    t.rect(ix, ay, iw, 2, BORD)
    construire_action(t, v, mode, iw, epreuves, mat, x=ix, y=ay)
    if mode == "epreuve":
        arene(t, ix, fy0, iw, fy1 - fy0, v, epreuves)
    t.sauver(sortie)


def construire_action(t, v, mode, w, epreuves, mat, x=0, y=0, mesure=False):
    px, py = x + 16, y + 2 + 12
    if mode == "lecture":
        h = 12 + 14 + 12 + 38 + 12
        if mesure:
            return 2 + 12 + 14 + 8 + 40 + 8 + 14
        t.texte("… (clic dans le fil : il écrit plus vite)", px, py, 11.5, ARGENT)
        return h
    if mode == "lecture_options":
        if mesure:
            return 2 + 12 + 14 + 8 + 40 + 8 + 14
        t.pixel("QUE FAIT PILOU ?", px, py, 2, ORANGE, ENCRE)
        ox = px
        for i, o in enumerate(v["options"]):
            ow, oh = option(t, ox, py + 14 + 8, i + 1, o, survol=(i == 0))
            ox += ow + 10
        return 0
    if mode == "attente":
        if mesure:
            return 2 + 12 + 132 + 14
        ciel(t, px, py, 132, 132, v["ton"], 3, collines=False)
        t.rect(px, py + 132 - 18, 132, 18, "#16365e")
        t.image(os.path.join(mat, "voyage-marche-1.png"), px + 10, py + 1, 112, 131)
        t.cadre(px, py, 132, 132, OMBRE)
        cx = px + 132 + 16
        cy = py + 10
        t.pixel("PILOU EST EN ROUTE", cx, cy, 2, ORANGE, ENCRE)
        cy += 14 + 6
        cy += t.texte(v["pendant"], cx, cy, 16, ARGENT_CLAIR, gras=True) + 2
        cy += t.texte("retour vers 15 h 40", cx, cy, 13, ARGENT) + 6
        t.texte("encore 12 min", cx, cy, 20, ORANGE, gras=True, mono=True)
        cases(t, cx + police(20, True, mono=True).getlength("encore 12 min") / S + 14, cy + 9, 0.6, 24, ORANGE)
        cy += 30 + 6
        t.texte("Tu peux fermer cette fenêtre : je te préviens à mon retour. (Je reste en bas de ton écran, en route.)", cx, cy, 12, VIOLET, largeur=w - 132 - 64)
        return 0
    if mode == "epreuve":
        if mesure:
            return 2 + 12 + 18 + 14
        t.texte("Concentre-toi… (Échap : laisser faire les dés)", px, py, 12, ARGENT)
        return 0
    if mode == "fin":
        if mesure:
            return 2 + 12 + 196 + 14
        t.texte(v["signeIssue"], px + 6, py + 50, 56, v["teinteIssue"], gras=True)
        cx = px + 6 + 60 + 22
        cy = py
        t.pixel(v["nomIssue"], cx, cy, 2.5, v["teinteIssue"], ENCRE)
        cy += 17.5 + 6
        cy += t.texte(f"« {v['titreFin']} »", cx, cy, 18, ARGENT_CLAIR, gras=True) + 6
        gx = cx
        for g in v["gains"]:
            teinte = ORANGE if g.startswith("+") else OR if g.startswith("✦") else VIOLET
            gw = t.largeur(g, 12, True) + 18
            t.boite(gx, cy, gw, 24, NUIT, teinte, 1)
            t.texte(g, gx + 9, cy + 3, 12, teinte, gras=True)
            gx += gw + 8
        cy += 30
        cy += t.texte(f"Fins trouvées : {v['fins']}", cx, cy, 13, ARGENT_CLAIR, gras=True) + 10
        bx = cx
        for lib, p in (("❖ Le carnet", True), ("↻ Rejouer", False), ("☰ Bibliothèque", False)):
            bw, _ = t.bouton(bx, cy, lib, p)
            bx += bw + 10
        return 0
    return 0


def arene(t, x, y, w, h, v, ep):
    """L'épreuve au-dessus du fil (VueEpreuve.cs) : réflexe, l'étoile vient de s'allumer."""
    t.rect(x, y, w, h, "#0f1324", 236)
    K = 1.4
    aw, ah = 400 * K, 200 * K
    total = 17 + 6 + 17 + 10 + ah + 6 + 12 + 30
    ty = y + (h - total) / 2
    titre = f"ÉPREUVE · {v['nomJeu'].upper()}"
    m = motif_texte(titre)
    lw = (len(m[0]) + 2) * 3
    pw = t.largeur("   " + v["difficulte"], 15, True)
    t.pixel(titre, x + (w - lw - pw) / 2, ty, 3, ORANGE, ENCRE)
    t.texte("   " + v["difficulte"], x + (w - lw - pw) / 2 + lw, ty + 1, 15, VIOLET, gras=True)
    ty += 21 + 6
    t.texte(v["consigne"], x, ty, 12.5, ARGENT, largeur=w, centre=True)
    ty += 17 + 10
    ax = x + (w - aw - 6) / 2
    t.cadre(ax, ty, aw + 6, ah + 6, BORD, 3)
    ax += 3
    ty += 3
    t.rect(ax, ty, aw, ah, "#0d1022")
    for i in range(18):
        t.rect(ax + ((i * 53 + 17) % 400) * K, ty + ((i * 37 + 11) % 120) * K, 2 * K, 2 * K, NUIT)
    for i in range(40):
        t.rect(ax + (10 + i * 9.5) * K, ty + 6 * K, 7.5 * K, 4 * K, BLEU if i < 31 else BLEU_SOMBRE)
    # halo et étoile allumée
    for i in (3, 2, 1):
        r_, c_ = 30 + 6 * i, (30 + 6 * i) * 0.55
        t.rect(ax + (200 - r_) * K, ty + (92 - c_) * K, 2 * r_ * K, 2 * c_ * K, OR, 34 * (4 - i))
        t.rect(ax + (200 - c_) * K, ty + (92 - r_) * K, 2 * c_ * K, 2 * r_ * K, OR, 34 * (4 - i))
    etoile = ["....#....", "....#....", "...###...", "#########", ".#######.", "..#####..", ".###.###.", ".##...##.", "#.......#"]
    for r, ligne in enumerate(etoile):
        for k, c in enumerate(ligne):
            if c == "#":
                t.rect(ax + (200 + (k - 4.5) * 7) * K, ty + (92 + (r - 4.5) * 7) * K, 7 * K, 7 * K, OR)
    losange = ["..#..", ".###.", "#####", ".###.", "..#.."]
    for i in range(5):
        cx = 200 - 4 * 15 + i * 30
        if i < 2:
            for r, ligne in enumerate(losange):
                for k, c in enumerate(ligne):
                    if c == "#":
                        t.rect(ax + (cx + (k - 2.5) * 2.4) * K, ty + (160 + (r - 2.5) * 2.4) * K, 2.4 * K, 2.4 * K, ORANGE)
        elif i == 2:
            t.texte("✕", ax + (cx - 5) * K, ty + (160 - 10) * K, 15, ARDOISE, gras=True)
        else:
            t.cadre(ax + (cx - 7) * K, ty + 153 * K, 14 * K, 14 * K, BLEU_SOMBRE, 1.5 * K)
    lib = f"il en faut {ep['reflexe']['besoin']} sur 5"
    t.texte(lib, ax + (aw - t.largeur(lib, 11.5)) / 2, ty + 26 * K - 8, 11.5, ARGENT)
    t.texte("327 ms !", ax + (aw - t.largeur("327 ms !", 13, True)) / 2, ty + 186 * K - 9, 13, CREME, gras=True)
    ty += ah + 3 + 12
    lab = f"⚄ Laisser faire les dés ({v['chance']} %)"
    bw = t.largeur(lab, 12.5, True) + 24 + 4
    t.boite(x + (w - bw) / 2, ty, bw, 28, CASE_CLAIRE, BORD)
    t.texte(lab, x + (w - bw) / 2 + 14, ty + 5, 12.5, ARGENT_CLAIR, gras=True)


def bibliotheque(mat, fiches, sortie):
    W, H = 1020, 720
    t = Toile(W, H)
    x0, y0, w0 = 14, 10, W - 28
    y = y0 + bandeau(t, x0, y0, w0) + 10
    y += tete(t, x0, y, w0, ["✉ En cours", "☰ Bibliothèque", "❖ Carnet"], "☰ Bibliothèque") + 10
    for f in fiches:
        ferme = f["statut"] == "Verrouillee"
        en_cours = f["statut"] == "EnCours"
        teinte = TEINTES_TON.get(f["ton"], BLEU_CLAIR)
        w = w0 - 8
        cw_ = w - 150 - 14 - 10 - 180
        nl = min(2, len(t.couper(f["accroche"], 12.5, False, False, cw_)))
        h = max(96 + 20, 2 + 10 + 22 + 16 + 4 + nl * 16.6 + 6 + 17 + 16 + 10 + 2)
        t.boite(x0, y, w, h, CASE_CLAIRE if en_cours else CASE, FERME if ferme else teinte, 3 if en_cours else 2)
        vx, vy = x0 + 12 + 2, y + 10 + 2
        ciel(t, vx, vy, 150, 96, f["ton"], Hasard.graine(f["id"]))
        sym = f["signeTon"]
        t.texte(sym, vx + (150 - t.largeur(sym, 34)) / 2, vy + 18, 34, teinte)
        t.cadre(vx, vy, 150, 96, OMBRE)
        cx = vx + 150 + 14
        cw = w - 150 - 14 - 10 - 180
        titre = ("▣ " if ferme else "") + f["titre"]
        t.texte(titre, cx, vy - 2, 17, ARGENT_CLAIR if not ferme else ARGENT, gras=True)
        if f["id"] == "prologue" and f["statut"] == "Nouvelle":
            tw = t.largeur(titre, 17, True)
            t.rect(cx + tw + 10, vy + 3, 66, 14, ORANGE)
        yy = vy + 22
        yy += t.texte(f"{f['signeTon']} {f['nomTon']}  ·  ◔ {f['duree']}  ·  niveau {f['niveau']}", cx, yy, 12, ARGENT if ferme else teinte, gras=True)
        lignes = t.couper(f["accroche"], 12.5, False, False, cw)
        acc = " ".join(lignes[:2]) + ("…" if len(lignes) > 2 else "")
        yy += 4 + t.texte(acc, cx, yy + 4, 12.5, ARGENT, largeur=cw) + 6
        cwid = cases(t, cx, yy + 4, f["progression"], 16, teinte)
        t.texte(f"   fins : {f['fins']}", cx + cwid, yy, 12, ARGENT_CLAIR)
        yy += 17
        t.texte(f"{f['signe']} {f['detail']}", cx, yy, 11.5, ORANGE if en_cours else VIOLET)
        bx = x0 + w - 12 - 2 - 150
        if ferme:
            t.texte(f"▣ niveau {f['niveau']}", bx + 20, y + h / 2 - 9, 12.5, ARGENT, gras=True)
        else:
            sig = {"EnCours": "◉", "Suspendue": "◌", "Finie": "↻"}.get(f["statut"], "▶")
            lab = f"{sig} {f['action']}"
            principal = f["statut"] in ("Nouvelle", "EnCours", "Suspendue")
            bw = 150
            bh = 13.5 * 1.33 + 18
            by = y + (h - bh) / 2
            calque = Toile(int(bw + 6), int(bh + 6), FOND)
            calque.im = Image.new("RGBA", calque.im.size, (0, 0, 0, 0))
            calque.d = ImageDraw.Draw(calque.im)
            calque.rect(3, 3, bw, bh, OMBRE)
            calque.boite(0, 0, bw, bh, ORANGE if principal else CASE_CLAIRE, ENCRE if principal else BORD)
            calque.texte(lab, 16, 9, 13.5, ENCRE if principal else ARGENT_CLAIR, gras=True)
            if f["bloquee"]:
                calque.im.putalpha(calque.im.getchannel("A").point(lambda a: int(a * 0.45)))
            t.im.alpha_composite(calque.im, (int(bx * S), int(by * S)))
        if ferme:
            t.rect(x0 + 2, y + 2, w - 4, h - 4, FOND, 100)
        y += h + 10
    t.texte("Une seule aventure à la fois. Pilou part pour de vrai : quelques minutes, parfois une heure ou deux. Tu peux fermer cette fenêtre, "
            "il te prévient à son retour (une fois, sans insister).", x0, y, 11.5, ARGENT, largeur=w0 - 8)
    t.sauver(sortie)


def main():
    mat, sortie = sys.argv[1], sys.argv[2]
    d = json.load(open(os.path.join(mat, "donnees.json"), encoding="utf-8"))
    ep = json.load(open(os.path.join(mat, "epreuves.json"), encoding="utf-8"))
    os.makedirs(sortie, exist_ok=True)
    lecture(mat, d["lecture"], os.path.join(sortie, "1-lecture-ecriture.png"), "lecture")
    lecture(mat, d["lecture"], os.path.join(sortie, "2-lecture-options.png"), "lecture_options")
    lecture(mat, d["attente"], os.path.join(sortie, "3-attente.png"), "attente")
    lecture(mat, d["epreuve"], os.path.join(sortie, "4-epreuve.png"), "epreuve", ep)
    lecture(mat, d["fin"], os.path.join(sortie, "5-fin.png"), "fin")
    bibliotheque(mat, d["bibliotheque"], os.path.join(sortie, "6-bibliotheque.png"))
    print("maquettes :", sortie)


if __name__ == "__main__":
    main()
