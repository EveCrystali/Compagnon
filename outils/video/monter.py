#!/usr/bin/env python3
"""Monte la vidéo de promo de Pilou à partir d'un tournage (outils/tourner-ecran-gauche.ps1).

    python outils/video/monter.py <dossier-du-tournage> [--sortie docs/promo] [--apercu]
                                  [--montage outils/video/montage.json] [--ffmpeg chemin] [--plan]

Le dossier du tournage contient la vidéo et chronologie.json (le zip posé sur le Bureau, décompressé).
Sortie : pilou-promo.mp4 (16:9), pilou-promo-vertical.mp4 (9:16), pilou-promo.gif (léger, pour le README) et
pilou-promo-planche.png (une image par plan, pour vérifier cadrages et cartons). --apercu : la planche seule
(rapide). --plan : le déroulé seul, sans rien écrire.

Le plan de montage est un fichier de données (montage.json, à côté de ce script) ; docs/VIDEO.md l'explique.
Il faut Python 3, Pillow et ffmpeg (dans le PATH ou --ffmpeg). Rien d'autre.

Vie privée (docs/VIDEO.md) : seules les images entre le début de la première étape jouée et la fin de la
dernière sont lues (avant et après, c'est le vrai bureau) ; sans chronologie, l'outil refuse de monter ; il
n'écrit que dans le dossier de sortie.
"""
import argparse
import array
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import wave

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - message clair plutôt qu'une trace
    sys.exit("Pillow manque : python -m pip install Pillow")

ICI = os.path.dirname(os.path.abspath(__file__))
DEPOT = os.path.normpath(os.path.join(ICI, "..", ".."))
MONTAGE_PAR_DEFAUT = os.path.join(ICI, "montage.json")

NOMS_SORTIE = {
    "horizontale": "pilou-promo.mp4",
    "verticale": "pilou-promo-vertical.mp4",
    "gif": "pilou-promo.gif",
    "planche": "pilou-promo-planche.png",
}

# Palette du projet : orange, bleu, violet, crème, sur une encre sombre. Jamais de rouge contre vert.
COULEURS = {
    "creme": (246, 238, 222),
    "orange": (246, 157, 80),
    "bleu": (108, 182, 255),
    "bleu_fonce": (47, 126, 216),
    "violet": (178, 146, 240),
    "gris": (160, 172, 188),
    "encre": (14, 17, 23),
}

# Format de référence : toutes les mises en page sont pensées en 1920 × 1080 et 1080 × 1920.
REF_H, REF_V = (1920, 1080), (1080, 1920)


class ErreurMontage(Exception):
    """Une erreur à expliquer en une phrase (pas de trace Python)."""


def dire(*morceaux):
    print(*morceaux, flush=True)


# ============================================================================================ ffmpeg

class Ffmpeg:
    """L'exécutable ffmpeg et la lecture des propriétés d'une vidéo (sans ffprobe : seul ffmpeg est exigé)."""

    def __init__(self, chemin=None):
        chemin = chemin or os.environ.get("PILOU_FFMPEG") or shutil.which("ffmpeg")
        if not chemin or not (os.path.isfile(chemin) or shutil.which(chemin)):
            raise ErreurMontage("ffmpeg introuvable : installe-le (Windows : winget install --id Gyan.FFmpeg -e) "
                                "ou donne son chemin avec --ffmpeg")
        self.exe = chemin

    def sonder(self, video):
        """(largeur, hauteur, images par seconde, durée en s) d'une vidéo."""
        p = subprocess.run([self.exe, "-hide_banner", "-i", video], capture_output=True)
        texte = p.stderr.decode("utf-8", errors="replace")
        m = re.search(r"Stream #.*?Video:.*?(\d{2,5})x(\d{2,5})", texte)
        if not m:
            raise ErreurMontage(f"vidéo illisible : {os.path.basename(video)}")
        ips = re.search(r"(\d+(?:\.\d+)?) fps", texte) or re.search(r"(\d+(?:\.\d+)?) tbr", texte)
        d = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", texte)
        duree = int(d.group(1)) * 3600 + int(d.group(2)) * 60 + float(d.group(3)) if d else 0.0
        return int(m.group(1)), int(m.group(2)), float(ips.group(1)) if ips else 30.0, duree

    def lancer(self, args, **kw):
        return subprocess.Popen([self.exe, "-hide_banner", "-loglevel", "error", *args], **kw)

    def executer(self, args):
        p = subprocess.run([self.exe, "-hide_banner", "-loglevel", "error", *args], capture_output=True)
        if p.returncode != 0:
            raise ErreurMontage("ffmpeg a échoué : " + p.stderr.decode("utf-8", errors="replace").strip()[-400:])


# ============================================================================================ polices

# Aucune police n'est embarquée dans le dépôt (la police pixel 3 × 5 de Police.cs n'a pas de minuscules) :
# on cherche une police système par son nom de fichier, Windows d'abord, puis Linux et macOS.
CANDIDATS = {
    "gras": ["segoeuib.ttf", "seguisb.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf",
             "NotoSans-Bold.ttf", "Ubuntu-B.ttf", "Arial Bold.ttf", "Helvetica.ttc"],
    "mono": ["consola.ttf", "CascadiaMono.ttf", "DejaVuSansMono.ttf", "LiberationMono-Regular.ttf",
             "NotoSansMono-Regular.ttf", "UbuntuMono-R.ttf", "Menlo.ttc"],
    "mono_gras": ["consolab.ttf", "CascadiaMono.ttf", "DejaVuSansMono-Bold.ttf", "LiberationMono-Bold.ttf",
                  "NotoSansMono-Bold.ttf", "UbuntuMono-B.ttf", "Menlo.ttc"],
}
FC_MATCH = {"gras": "sans:bold", "mono": "monospace", "mono_gras": "monospace:bold"}


def dossiers_de_polices():
    """Les dossiers de polices de cette machine, tirés de l'environnement (aucun chemin en dur)."""
    d = []
    if os.environ.get("WINDIR"):
        d.append(os.path.join(os.environ["WINDIR"], "Fonts"))
    if os.environ.get("LOCALAPPDATA"):
        d.append(os.path.join(os.environ["LOCALAPPDATA"], "Microsoft", "Windows", "Fonts"))
    maison = os.path.expanduser("~")
    d += [os.path.join(maison, ".fonts"), os.path.join(maison, ".local", "share", "fonts"),
          os.path.join(maison, "Library", "Fonts")]
    xdg = os.environ.get("XDG_DATA_DIRS") or os.pathsep.join([os.sep + os.path.join("usr", "local", "share"),
                                                                 os.sep + os.path.join("usr", "share")])
    d += [os.path.join(x, "fonts") for x in xdg.split(os.pathsep) if x]
    return [x for x in d if os.path.isdir(x)]


class Polices:
    def __init__(self, imposee=None):
        self._cache = {}
        self.fichiers = {}
        index = {}
        for dossier in dossiers_de_polices():
            for racine, _, fichiers in os.walk(dossier):
                for f in fichiers:
                    index.setdefault(f.lower(), os.path.join(racine, f))
        for genre, noms in CANDIDATS.items():
            trouve = imposee if (imposee and genre == "gras") else None
            for n in noms:
                if trouve:
                    break
                trouve = index.get(n.lower())
            if not trouve and shutil.which("fc-match"):
                p = subprocess.run(["fc-match", "-f", "%{file}", FC_MATCH[genre]], capture_output=True)
                f = p.stdout.decode("utf-8", errors="replace").strip()
                trouve = f if f and os.path.isfile(f) else None
            self.fichiers[genre] = trouve
        if not self.fichiers["gras"]:
            dire("Attention : aucune police système trouvée, police de secours de Pillow (moins jolie).")

    def __call__(self, taille, genre="gras"):
        cle = (genre, int(taille))
        if cle not in self._cache:
            f = self.fichiers.get(genre) or self.fichiers.get("gras")
            try:
                self._cache[cle] = ImageFont.truetype(f, int(taille)) if f else ImageFont.load_default(int(taille))
            except (OSError, TypeError):
                self._cache[cle] = ImageFont.load_default()
        return self._cache[cle]


# ============================================================================================ chronologie

class Chronologie:
    """chronologie.json d'un tournage, en secondes de la vidéo (champ decalage_s : vidéo recoupée au début).

    Chaque étape : debut_s, fin_s (sinon le début de l'étape suivante), jouee, et ses cadres (rectangles
    d'intérêt successifs, en pixels de la vidéo : quoi, debut_s, fin_s, zone)."""

    def __init__(self, chemin, duree_video):
        if not os.path.isfile(chemin):
            raise ErreurMontage("chronologie.json manque dans le dossier du tournage : sans elle, on ne sait pas où "
                                "commence le décor fictif, donc on ne monte rien (vie privée).")
        with open(chemin, encoding="utf-8-sig") as f:
            brut = json.load(f)
        self.brut = brut
        self.decalage = float(brut.get("decalage_s") or 0)
        self.video = brut.get("video")
        etapes = []
        for e in brut.get("etapes") or []:
            if e.get("debut_s") is None or not e.get("etape"):
                continue
            etapes.append({
                "nom": str(e["etape"]),
                "jouee": bool(e.get("jouee", True)),
                "debut": float(e["debut_s"]) - self.decalage,
                "fin": None if e.get("fin_s") is None else float(e["fin_s"]) - self.decalage,
                "cadres": [self._cadre(c) for c in (e.get("cadres") or []) if c.get("zone")],
            })
        # Fin manquante (anciennes chronologies) : le début de l'étape suivante, sinon son propre début.
        for i, e in enumerate(etapes):
            if e["fin"] is None:
                suivants = [x["debut"] for x in etapes[i + 1:] if x["debut"] > e["debut"]]
                e["fin"] = suivants[0] if suivants else e["debut"]
        self.etapes = etapes
        jouees = [e for e in etapes if e["jouee"] and e["fin"] > e["debut"]]
        if not jouees:
            raise ErreurMontage("la chronologie ne contient aucune étape jouée : rien à monter.")
        # La plage sûre : du début de la première étape jouée à la fin de la dernière, dans la vidéo.
        debut = min(e["debut"] for e in jouees)
        fin = max(e["fin"] for e in jouees)
        if duree_video > 0:
            fin = min(fin, duree_video)
        self.plage = (max(0.0, debut), fin)
        if self.plage[1] - self.plage[0] < 0.5:
            raise ErreurMontage("la plage utile de la vidéo est vide (chronologie et vidéo ne correspondent pas ?).")

    def _cadre(self, c):
        z = c["zone"]
        return {"quoi": set(str(c.get("quoi", "")).split("+")) - {""},
                "debut": float(c.get("debut_s", 0)) - self.decalage, "fin": float(c.get("fin_s", 0)) - self.decalage,
                "zone": (float(z["x"]), float(z["y"]), float(z["largeur"]), float(z["hauteur"]))}

    def etape(self, nom):
        """L'étape jouée de ce nom (la première), ou None."""
        for e in self.etapes:
            if e["nom"] == nom and e["jouee"] and e["fin"] > e["debut"]:
                return e
        return None


# ============================================================================================ plan de montage

def mesure_s(rythme):
    return 4 * 60.0 / float(rythme.get("bpm", 140))


class Plan:
    """Un plan résolu : ce qu'on lit (source a → b, en s de la vidéo) ou la carte à dessiner, sa durée."""

    def __init__(self, spec, rang):
        self.spec, self.rang = spec, rang
        self.carte = spec.get("carte")
        self.nom = self.carte or spec.get("etape")
        self.a = self.b = 0.0
        self.vitesse = 1.0
        self.duree = 0.0
        self.etape = None
        self.cadres = []
        self.transition = spec.get("transition", "coupe")
        cartons = spec.get("cartons") or ([dict(spec["carton"], a=0)] if spec.get("carton") else [])
        self.cartons = sorted(cartons, key=lambda c: c.get("a", 0))

    def carton_a(self, s):
        actifs = [c for c in self.cartons if s >= c.get("a", 0)]
        return actifs[-1] if actifs else None


def resoudre(montage, chrono, ips_sortie):
    """Les plans à jouer, dans l'ordre : étapes absentes, non jouées ou trop courtes sautées (le suivant
    enchaîne). Les durées se calent sur la musique (multiple d'un pas, une demi-mesure par défaut)."""
    rythme = montage.get("rythme", {})
    pas = mesure_s(rythme) * float(rythme.get("pas_mesures", 0.5))
    pas_min = int(rythme.get("pas_min", 2))
    plans, sautes = [], []
    for rang, spec in enumerate(montage.get("plans", [])):
        p = Plan(spec, rang)
        if p.carte:
            p.duree = float(spec["mesures"]) * mesure_s(rythme) if "mesures" in spec else float(spec.get("duree", 3))
            plans.append(p)
            continue
        e = chrono.etape(p.nom) if chrono else None
        if e is None:
            sautes.append((p.nom, "absente ou non jouée"))
            continue
        a = e["debut"] + float(spec.get("de", 0))
        b = e["fin"] if spec.get("a") is None else min(e["fin"], e["debut"] + float(spec["a"]))
        cad = spec.get("cadrage", {})
        voulus = set(str(cad.get("quoi", "")).split("+")) - {""}
        p.cadres = [c for c in e["cadres"] if not voulus or c["quoi"] & voulus] or e["cadres"]
        if cad.get("restreindre") and voulus:
            justes = [c for c in e["cadres"] if c["quoi"] & voulus]
            if not justes:
                sautes.append((p.nom, "rien de « " + "+".join(sorted(voulus)) + " » à l'image"))
                continue
            a = max(a, min(c["debut"] for c in justes))
            b = min(b, max(c["fin"] for c in justes))
        # Garde-fou : jamais hors de la plage sûre (une image avant ou après, c'est le vrai bureau).
        a, b = max(a, chrono.plage[0]), min(b, chrono.plage[1])
        if b - a < 0.4:
            sautes.append((p.nom, "trop courte"))
            continue
        # « duree » (secondes voulues à l'écran) prime sur « vitesse » ; puis calage sur le pas de la musique.
        duree = float(spec["duree"]) if spec.get("duree") else (b - a) / float(spec.get("vitesse", 1.0))
        if pas > 0:
            duree = max(1 if spec.get("duree") else pas_min, round(duree / pas)) * pas
            # Pas de ralenti visible : une étape trop courte pour sa durée raccourcit le plan.
            v_min = float(rythme.get("vitesse_min", 0.8))
            while duree > pas and (b - a) / duree < v_min:
                duree -= pas
        p.a, p.b, p.etape, p.duree, p.vitesse = a, b, e, duree, (b - a) / duree
        plans.append(p)
    # Images de sortie : arrondi cumulé, pour que la vidéo tombe juste sur la musique.
    t = 0.0
    for p in plans:
        p.debut_sortie = t
        p.n = int(round((t + p.duree) * ips_sortie)) - int(round(t * ips_sortie))
        t += p.duree
    return plans, sautes, t


# ============================================================================================ caméra

def boite_169(zone, marge, ecran, zoom_max, aspect):
    """Le cadre (cx, cy, largeur) qui montre la zone plus sa marge, au format de sortie, sans zoomer au-delà de
    zoom_max (sinon le pixel art devient flou) et sans sortir de l'écran."""
    sw, sh = ecran
    x, y, w, h = zone
    larg = max(w + 2 * marge, (h + 2 * marge) * aspect, sw / max(1.0, zoom_max))
    larg = min(larg, sw, sh * aspect)
    return (x + w / 2, y + h / 2, larg)


def borner(cx, cy, larg, ecran, aspect):
    """(x0, y0, l, h) : le cadre poussé dans l'écran (jamais hors de l'image)."""
    sw, sh = ecran
    larg = max(16.0, min(larg, sw, sh * aspect))
    haut = larg / aspect
    x0 = min(max(cx - larg / 2, 0.0), sw - larg)
    y0 = min(max(cy - haut / 2, 0.0), sh - haut)
    return x0, y0, larg, haut


def zone_a(cadres, t):
    """Le rectangle d'intérêt à l'instant t : celui en cours, sinon le plus proche (le précédent d'abord)."""
    en_cours = [c for c in cadres if c["debut"] <= t <= c["fin"]]
    if en_cours:
        return en_cours[-1]["zone"]
    avant = [c for c in cadres if c["fin"] < t]
    if avant:
        return max(avant, key=lambda c: c["fin"])["zone"]
    return min(cadres, key=lambda c: c["debut"])["zone"]


def lisser(valeurs, alpha):
    """Lissage exponentiel aller puis retour : la caméra glisse sans retard ni à-coup."""
    out = list(valeurs)
    for i in range(1, len(out)):
        out[i] = tuple(p + alpha * (q - p) for p, q in zip(out[i - 1], out[i]))
    for i in range(len(out) - 2, -1, -1):
        out[i] = tuple(p + alpha * (q - p) for p, q in zip(out[i + 1], out[i]))
    return out


def lisse01(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def trajectoire(plan, montage, ecran, aspect, ips, vertical=False):
    """Pour chaque image de sortie du plan : (instant source, cadre x0, y0, l, h).

    Horizontal : un cadre au format de sortie, avec de la place en haut pour le carton. Vertical : un carré
    (posé sous le carton), un peu plus serré, puisqu'il n'a que 1080 pixels de large."""
    cam = dict(montage.get("camera", {}))
    cam.update(plan.spec.get("cadrage", {}))
    marge = float(cam.get("marge", 60))
    zoom_max = float(cam.get("zoom_max", 2.8))
    haut = 0.0 if vertical or not plan.cartons or plan.cartons[0].get("position") == "bas" else float(cam.get("marge_carton", 90))
    if vertical:
        aspect, zoom_max = 1.0, zoom_max * float(cam.get("zoom_vertical", 1.5))
    sw, sh = ecran
    plein = (sw / 2, sh / 2, min(sw, sh * aspect))
    instants = [plan.a + k * plan.vitesse / ips for k in range(plan.n)]
    if plan.cadres:
        def zone(t):
            x, y, w, h = zone_a(plan.cadres, t)
            return x, y - haut, w, h + haut
        cibles = [boite_169(zone(t), marge, ecran, zoom_max, aspect) for t in instants]
    else:
        cibles = [plein] * plan.n  # pas de rectangles (ancienne chronologie) : plan large
    tau = float(cam.get("lissage_s", 0.22))
    if cibles and tau > 0:
        cibles = lisser(cibles, 1 - math.exp(-1.0 / (ips * tau)))
    large = float(plan.spec.get("depuis_large", 0))
    if large > 0:
        cibles = [tuple(p + (q - p) * lisse01(k / ips / large) for p, q in zip(plein, c)) for k, c in enumerate(cibles)]
    return [(t, borner(*c, ecran, aspect)) for t, c in zip(instants, cibles)]


# ============================================================================================ lecture des rushes

class Rushes:
    """La vidéo du tournage. Toute lecture passe par ici et vérifie la plage sûre."""

    def __init__(self, ff, chemin, plage):
        self.ff, self.chemin, self.plage = ff, chemin, plage
        self.largeur, self.hauteur, self.ips, self.duree = ff.sonder(chemin)
        self.lectures = []  # (a, b) réellement demandées : le test vérifie qu'elles restent dans la plage

    def _verifier(self, a, b):
        marge = 0.5 / self.ips
        if a < self.plage[0] - marge or b > self.plage[1] + marge:
            raise ErreurMontage(f"lecture refusée hors de la plage sûre ({a:.2f} → {b:.2f} s, "
                                f"plage {self.plage[0]:.2f} → {self.plage[1]:.2f} s)")
        self.lectures.append((a, b))

    def images(self, a, b):
        """Les images de a à b (exclu), dans l'ordre, en RGB."""
        n = max(1, int(math.floor((b - a) * self.ips + 1e-6)))
        self._verifier(a, a + n / self.ips)
        p = self.ff.lancer(["-ss", f"{a:.3f}", "-i", self.chemin, "-frames:v", str(n), "-an",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)  # « broken pipe » quand on s'arrête avant la fin
        taille = self.largeur * self.hauteur * 3
        try:
            for _ in range(n):
                buf = p.stdout.read(taille)
                if len(buf) < taille:
                    break
                yield Image.frombytes("RGB", (self.largeur, self.hauteur), buf)
        finally:
            p.stdout.close()
            p.wait()

    def image(self, t):
        """Une seule image, à l'instant t."""
        t = min(max(t, self.plage[0]), self.plage[1] - 1.0 / self.ips)
        for im in self.images(t, t + 1.0 / self.ips):
            return im
        return Image.new("RGB", (self.largeur, self.hauteur), COULEURS["encre"])


# ============================================================================================ Pilou HD

class PilouHD:
    """Pilou dessiné par le moteur de référence du dépôt (outils/sprites/rendu.py), pour les cartes de fin.
    Les mêmes pixels que le PC et Android ; habillé comme le Pilou du tournage."""

    TENUE = dict(couleur="glacier", objets=["chapeau-pirate", "echarpe", "petit-chat"])

    def __init__(self):
        self._hd = None
        self._cache = {}

    def _moteur(self):
        if self._hd is None:
            sys.path.insert(0, os.path.join(DEPOT, "outils", "sprites"))
            ecrire_pyc, sys.dont_write_bytecode = sys.dont_write_bytecode, True  # rien d'écrit hors de la sortie
            try:
                import rendu as hd  # noqa: E402  (moteur de référence des sprites)
                self._hd = (hd, hd.banque(), hd.teintes(), hd.tenues())
            except Exception as e:  # le moteur manque : on fera sans Pilou plutôt que d'échouer
                dire(f"Attention : moteur de sprites indisponible ({e}) ; cartes sans Pilou.")
                self._hd = False
            finally:
                sys.path.pop(0)
                sys.dont_write_bytecode = ecrire_pyc
        return self._hd

    def image(self, t_ms, **pose):
        m = self._moteur()
        if not m:
            return None
        hd, b, te, tn = m
        kw = dict(self.TENUE)
        kw["objets"] = list(kw["objets"]) + pose.pop("objets", [])
        kw.update(pose)
        kw["t"] = int(t_ms // 50) * 50
        cle = repr(sorted(kw.items()))
        if cle not in self._cache:
            g = hd.rendre(hd.Pose(**kw), b, te, tn, e=2)
            im = Image.new("RGBA", (len(g[0]), len(g)))
            im.putdata([_rgba(c) for ligne in g for c in ligne])
            if len(self._cache) > 400:
                self._cache.clear()
            self._cache[cle] = im
        return self._cache[cle]

    def poser(self, fond, cx, pieds, z, t_ms, sx=1.0, sy=1.0, **pose):
        """Pilou posé par ses pieds en (cx, pieds), pixel × z ; renvoie le haut de sa tête (pour la bulle)."""
        g = self.image(t_ms, **pose)
        if g is None:
            return pieds - 100 * z
        w, h = int(g.width * z * sx), int(g.height * z * sy)
        gros = g.resize((w, h), Image.NEAREST)
        y = int(pieds - 108 / 112 * h)
        fond.alpha_composite(gros, (int(cx - w / 2), y))
        bb = g.getchannel("A").point(lambda v: 255 if v > 60 else 0).getbbox()
        return y + (bb[1] if bb else 0) * z * sy


def _rgba(c):
    if not c:
        return (0, 0, 0, 0)
    h = c.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16) if len(h) >= 8 else 255)


def ecrase(u, force=0.22):
    """Écrasement à l'atterrissage (u secondes après l'impact) : (sx, sy)."""
    if u < 0 or u > 0.6:
        return 1.0, 1.0
    sy = 1 - force * math.exp(-u * 9) * math.cos(u * 28)
    return 1 / sy, sy


# ============================================================================================ dessin

def degrade(im, haut, bas):
    d = ImageDraw.Draw(im)
    w, h = im.size
    for y in range(h):
        a = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(haut[i] + (bas[i] - haut[i]) * a) for i in range(3)))


class Atelier:
    """Tout ce qui se dessine : cartons, transitions, cartes de fin, images horizontales et verticales."""

    def __init__(self, montage, polices, pilou):
        self.m = montage
        self.pol = polices
        self.pilou = pilou
        fmt = montage.get("format", {})
        self.taille_h = tuple(fmt.get("horizontal", REF_H))
        self.taille_v = tuple(fmt.get("vertical", REF_V))
        self.marque = montage.get("marque", "")
        self._fond_v = None
        self._cartons = {}

    # ---- cartons

    def _boite(self, lignes, taille, couleur):
        cle = (tuple(lignes), taille, couleur)
        if cle not in self._cartons:
            f = self.pol(taille)
            tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
            w = int(max(tmp.textlength(x, font=f) for x in lignes)) + 64
            h = int((taille * 1.22) * len(lignes) + 40)
            im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            d = ImageDraw.Draw(im)
            d.rounded_rectangle([0, 0, w - 1, h - 1], 26, fill=COULEURS["encre"] + (218,))
            d.rounded_rectangle([0, h - 7, w - 1, h - 1], 3, fill=couleur + (200,))  # liseré : un signe de forme
            for i, x in enumerate(lignes):
                tw = tmp.textlength(x, font=f)
                d.text(((w - tw) / 2, 16 + i * taille * 1.22), x, font=f, fill=couleur)
            self._cartons[cle] = im
        return self._cartons[cle]

    def carton(self, im, carton, s, vertical):
        """Pose le carton (texte gros et gras qui « tape » : 1,25 → 1 en 0,12 s) sur l'image RGBA (référence)."""
        if not carton:
            return
        texte = carton["texte"]
        couleur = COULEURS.get(carton.get("couleur", "creme"), COULEURS["creme"])
        titre = carton.get("taille") == "titre"
        lignes = texte.split("|")
        tmp = ImageDraw.Draw(im)
        if vertical:
            taille, limite = (150 if titre else 84), 980
            coupees = []
            for x in lignes:  # une ligne trop longue passe sur deux lignes
                if tmp.textlength(x, font=self.pol(taille)) > limite and " " in x:
                    mots = x.split(" ")
                    m = (len(mots) + 1) // 2
                    coupees += [" ".join(mots[:m]), " ".join(mots[m:])]
                else:
                    coupees.append(x)
            lignes = coupees
            while taille > 30 and max(tmp.textlength(x, font=self.pol(taille)) for x in lignes) > limite:
                taille -= 4
        else:
            taille = 170 if titre else 80
            if tmp.textlength(" ".join(lignes), font=self.pol(taille)) < 1680:
                lignes = [" ".join(lignes)]
        boite = self._boite(lignes, taille, couleur)
        k = 1.25 - 0.25 * min(1.0, max(0.0, s) / 0.12)
        if k != 1:
            boite = boite.resize((int(boite.width * k), int(boite.height * k)), Image.BILINEAR)
        w, h = im.size
        if vertical:
            y = 300 - boite.height // 2
        elif carton.get("position") == "bas":
            y = h - boite.height - 40
        else:
            y = 34
        im.alpha_composite(boite, ((w - boite.width) // 2, int(y)))

    # ---- transitions

    @staticmethod
    def balayage(im, s, duree=0.22):
        """Des pixels qui balaient l'image en diagonale (début de séquence)."""
        if s >= duree:
            return im
        d = ImageDraw.Draw(im)
        w, h = im.size
        q = 60
        seuil = s / duree * (w / q + h / q)
        for j in range(h // q + 1):
            for i in range(w // q + 1):
                if i + j > seuil:
                    c = COULEURS["bleu_fonce"] if (i + j) % 3 == 0 else COULEURS["orange"] if (i + j) % 7 == 0 else (22, 27, 34)
                    d.rectangle([i * q, j * q, i * q + q - 2, j * q + q - 2], fill=c)
        return im

    # ---- images tirées des rushes

    def fond_vertical(self):
        if self._fond_v is None:
            self._fond_v = Image.new("RGB", REF_V)
            degrade(self._fond_v, (24, 32, 52), (12, 14, 19))
        return self._fond_v.copy()

    def depuis_rush(self, src, cadre, carre, plan, s):
        """(horizontale, verticale) à la taille de référence, pour une image source et les deux caméras
        (cadre 16:9 pour l'horizontale, carré pour la verticale)."""
        x0, y0, w, h = cadre
        hz = src.resize(REF_H, Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h)).convert("RGBA")
        carton = plan.carton_a(s)
        s_carton = s - carton.get("a", 0) + plan.suite if carton else 0
        self.carton(hz, carton, s_carton, False)
        # Vertical : le carré sur la zone d'intérêt, le carton au-dessus, la marque en dessous.
        vx, vy, c, _ = carre
        vt = self.fond_vertical()
        vt.paste(src.resize((1080, 1080), Image.BICUBIC, box=(vx, vy, vx + c, vy + c)), (0, 520))
        vt = vt.convert("RGBA")
        self.carton(vt, carton, s_carton, True)
        self._marque(vt)
        return hz.convert("RGB"), vt.convert("RGB")

    def _marque(self, vt):
        if self.marque:
            d = ImageDraw.Draw(vt)
            f = self.pol(40)
            d.text(((1080 - d.textlength(self.marque, font=f)) / 2, 1700), self.marque, font=f, fill=COULEURS["gris"])

    # ---- cartes de fin

    def bulle(self, im, cx, bas, texte):
        f = self.pol(30)
        d = ImageDraw.Draw(im)
        larg, haut = int(d.textlength(texte, font=f)) + 48, 64
        x0, y0 = int(cx - larg / 2), int(bas - haut - 36)
        b = 5
        d.rectangle([x0, y0, x0 + larg, y0 + haut], fill=COULEURS["bleu"])
        d.rectangle([x0 + b, y0 + b, x0 + larg - b, y0 + haut - b], fill=(45, 51, 59))
        for i, k in enumerate((5, 3, 1)):
            xx = int(cx - k * b / 2)
            d.rectangle([xx, y0 + haut + i * b, xx + k * b - 1, y0 + haut + (i + 1) * b - 1], fill=COULEURS["bleu"])
        d.text((x0 + 24, y0 + 14), texte, font=f, fill=COULEURS["creme"])

    def carte(self, plan, s, vertical):
        if plan.carte == "installation":
            return self.carte_installation(plan, s, vertical)
        if plan.carte == "a_venir":
            return self.carte_a_venir(plan, s, vertical)
        raise ErreurMontage(f"carte inconnue : {plan.carte} (installation ou a_venir)")

    def _terminal(self, im, x, y, w, h, s, plan, taille, largeur_max):
        """Une fenêtre de terminal sobre ; la commande se tape lettre par lettre, puis la sortie."""
        spec = plan.spec
        commande = spec.get("commande", "")
        sortie = spec.get("sortie", [])
        d_total = plan.duree
        f, fb = self.pol(taille, "mono"), self.pol(taille, "mono_gras")
        cal = Image.new("RGBA", (w + 16, h + 16), (0, 0, 0, 0))
        d = ImageDraw.Draw(cal)
        d.rounded_rectangle([8, 10, w + 8, h + 10], 14, fill=(6, 8, 12, 170))
        d.rounded_rectangle([0, 0, w, h], 14, fill=(14, 24, 44))
        d.rounded_rectangle([0, 0, w, 46], 14, fill=(28, 40, 64))
        d.rectangle([0, 30, w, 46], fill=(28, 40, 64))
        d.text((20, 10), "PowerShell", font=self.pol(22), fill=(180, 200, 225))
        # La commande, coupée en morceaux qui tiennent dans la largeur.
        invite = "PS C:\\> "
        morceaux, reste = [], commande
        while reste:
            dispo = largeur_max - (d.textlength(invite, font=fb) if not morceaux else d.textlength("  ", font=f))
            n = len(reste)
            while n > 1 and d.textlength(reste[:n], font=f) > dispo:
                n -= 1
            if n < len(reste) and " " in reste[:n]:
                coupe = max(reste.rfind(" ", 0, n), reste.rfind("/", 0, n) + 1)
                n = coupe if coupe > 0 else n
            morceaux.append(reste[:n])
            reste = reste[n:]
        t_frappe = 0.38 * d_total
        tape = int(len(commande) * lisse01((s - 0.25) / max(0.3, t_frappe - 0.25)) ** 0.85)
        pas, yy = taille * 1.45, 70
        for i, m in enumerate(morceaux):
            pre = invite if i == 0 else "  "
            n = max(0, min(len(m), tape))
            tape -= len(m)
            d.text((24, yy), pre, font=fb, fill=COULEURS["bleu"])
            xx = 24 + d.textlength(pre, font=fb)
            d.text((xx, yy), m[:n], font=f, fill=(236, 242, 248))
            if n < len(m) or (i == len(morceaux) - 1 and s < t_frappe + 0.3):
                if int(s * 4) % 2 == 0 or n < len(m):
                    cx = xx + d.textlength(m[:n], font=f)
                    d.rectangle([cx + 2, yy + 4, cx + taille * 0.6, yy + taille + 2], fill=COULEURS["orange"])
            yy += pas
            if n < len(m):
                break
        if s > t_frappe + 0.2:
            yy += pas * 0.3
            for j, ligne in enumerate(sortie):
                if s > t_frappe + 0.25 + j * 0.25:
                    derniere = j == len(sortie) - 1
                    if derniere:  # la ligne finale porte aussi un signe de forme : un petit losange
                        d.polygon([(30, yy + taille * 0.55), (40, yy + taille * 0.2), (50, yy + taille * 0.55),
                                   (40, yy + taille * 0.9)], fill=COULEURS["bleu"])
                    d.text((60 if derniere else 24, yy), ligne if derniere else "  " + ligne,
                           font=fb if derniere else f, fill=COULEURS["bleu"] if derniere else (150, 170, 196))
                    yy += pas
        im.alpha_composite(cal, (int(x), int(y)))
        return t_frappe + 0.25 + len(sortie) * 0.25

    def carte_installation(self, plan, s, vertical):
        spec = plan.spec
        t_ms = s * 1000
        if vertical:
            im = Image.new("RGBA", REF_V)
            degrade(im, (40, 60, 96), (14, 17, 23))
            w, h = REF_V
            k = lisse01(s / 0.25)
            fin = self._terminal(im, 30, 470 + (1 - k) * 60, 1020, 640, s, plan, 34, 960)
            sol = 1660
            ImageDraw.Draw(im).rectangle([0, sol, w, sol + 70], fill=(30, 35, 44))
            px = w // 2
        else:
            im = Image.new("RGBA", REF_H)
            degrade(im, (58, 84, 120), (27, 36, 52))
            w, h = REF_H
            k = lisse01(s / 0.25)
            fin = self._terminal(im, 70, 150 + (1 - k) * 60, 1780, 560, s, plan, 32, 1700)
            sol = h - 64
            ImageDraw.Draw(im).rectangle([0, sol, w, h], fill=(30, 35, 44))
            px = w - 260
        if s > fin:  # Pilou surgit sur le bureau et salue
            u = s - fin
            saut = max(0.0, math.sin(min(1.0, u / 0.3) * math.pi)) * 14 if u < 0.3 else 0
            sx, sy = ecrase(u - 0.3, 0.3)
            sommet = self.pilou.poser(im, px, sol + 4, 4, t_ms, sx, sy, expr="fete", salue=True, saut=saut)
            if u > 0.35:
                self.bulle(im, px, sommet, "salut !")
        d = ImageDraw.Draw(im)
        if s > 1.0 and spec.get("android"):
            fa = self.pol(34 if vertical else 32)
            ya = 1150 if vertical else 740
            xa = (w - d.textlength(spec["android"], font=fa)) / 2 if vertical else 90
            d.text((xa, ya), spec["android"], font=fa, fill=COULEURS["gris"])
        titre = {"texte": spec.get("titre", ""), "couleur": "creme"}
        if vertical:
            self.carton(im, titre, s, True)
        else:
            self.carton(im, titre, s, False)
        if spec.get("sous_titre") and s > 0.5:
            f = self.pol(52 if vertical else 48)
            st = spec["sous_titre"]
            y = 1260 if vertical else 820
            d.text(((w - d.textlength(st, font=f)) / 2 if vertical else 90, y), st, font=f, fill=COULEURS["orange"])
        return im

    def carte_a_venir(self, plan, s, vertical):
        t_ms = s * 1000
        w, h = REF_V if vertical else REF_H
        im = Image.new("RGBA", (w, h))
        degrade(im, (30, 44, 70), (14, 17, 23))
        d = ImageDraw.Draw(im)
        for i in range(60):  # petites étoiles qui descendent
            x, y = (i * 467) % w, (i * 283 + int(t_ms / 20)) % h
            d.rectangle([x, y, x + 2, y + 2], fill=(120, 150, 200))
        saut = max(0.0, math.sin(min(1.0, s / 0.4) * math.pi)) * 14 if s < 0.4 else 0
        sx, sy = ecrase(s - 0.4)
        if vertical:
            self.pilou.poser(im, w // 2, 1010, 6, t_ms, sx, sy, expr="fete", saut=saut, objets=["couronne-fleurs"])
        else:
            self.pilou.poser(im, 420, 930, 6, t_ms, sx, sy, expr="fete", saut=saut, objets=["couronne-fleurs"])
        y = 1060 if vertical else 170
        for i, ligne in enumerate(plan.spec.get("lignes", [])):
            a = min(1.0, max(0.0, (s - 0.12 - i * 0.14) / 0.15))
            n = int(ligne.get("taille", 60) * (0.92 if vertical else 1))
            f = self.pol(n)
            tx = ligne["texte"]
            while vertical and d.textlength(tx, font=f) > 1000 and n > 24:
                n -= 4
                f = self.pol(n)
            tw = d.textlength(tx, font=f)
            x = (w - tw) / 2 if vertical else 780
            if a > 0:
                c = COULEURS.get(ligne.get("couleur", "creme"), COULEURS["creme"])
                cal = Image.new("RGBA", (w, h), (0, 0, 0, 0))
                dc = ImageDraw.Draw(cal)
                if ligne.get("cadre"):
                    dc.rounded_rectangle([x - 26, y - 16, x + tw + 26, y + n + 22], 18,
                                         fill=COULEURS["bleu_fonce"] + (int(90 * a),), outline=COULEURS["bleu"] + (int(255 * a),), width=3)
                dc.text((x, y), tx, font=f, fill=c + (int(255 * a),))
                im.alpha_composite(cal)
            y += int(n * 1.25) + (60 if i == 0 else 50)
        return im


def a_la_taille(im, taille):
    return im if im.size == tuple(taille) else im.resize(tuple(taille), Image.LANCZOS)


def fondre(a, b, u):
    return Image.blend(a, b, max(0.0, min(1.0, u)))


# ============================================================================================ musique

def musique(chemin, duree, bpm=140, taux=32000):
    """Une petite boucle chiptune à 140 bpm (do, sol, la mineur, fa), synthétisée ici : aucun échantillon,
    libre de droits. Les coupes du montage tombent sur les temps."""
    temps = 60.0 / bpm
    mesure = 4 * temps
    n = int(taux * duree) + taux
    out = array.array("d", bytes(8 * n))
    alea = random.Random(7)

    def note(f, t0, dur, forme="carre", vol=0.2, rapport=0.25):
        i0, i1 = int(t0 * taux), min(n, int((t0 + dur) * taux))
        if i0 >= n or f <= 0:
            return
        for i in range(i1 - i0):
            t = i / taux
            if forme == "carre":
                o = 1.0 if (f * t) % 1 < rapport else -1.0
            elif forme == "triangle":
                o = 4 * abs((f * t) % 1 - 0.5) - 1
            elif forme == "grosse":  # grosse caisse : sinus qui descend de 150 à 40 Hz
                o = math.sin(2 * math.pi * (150 * t - 110 * t * t / (2 * dur)))
            else:
                o = alea.uniform(-1, 1)
            env = min(1.0, t / 0.004) * math.exp(-t / (dur * 0.55)) * min(1.0, (dur - t) / 0.006)
            out[i0 + i] += o * env * vol

    def hz(m):
        return 440 * 2 ** ((m - 69) / 12)

    accords = [(60, [60, 64, 67]), (55, [55, 59, 62]), (57, [57, 60, 64]), (53, [53, 57, 60])]
    melodie = [76, 79, 84, 79, 81, 79, 76, 74, 74, 79, 83, 79, 81, 83, 86, 83,
               76, 72, 76, 81, 79, 76, 72, 76, 77, 81, 84, 81, 79, 77, 76, 74]
    nb = int(duree / mesure) + 1
    for k in range(nb):
        t0 = k * mesure
        finale = k >= nb - 2  # les cartes de fin : la mélodie se tait, le motif reste
        racine, acc = accords[k % 4]
        for b in range(4):
            note(1, t0 + b * temps, 0.16, "grosse", 0.55)
            note(hz(racine - 24), t0 + b * temps, temps * 0.45, "triangle", 0.30)
            note(hz(racine - 12), t0 + b * temps + temps / 2, temps * 0.4, "triangle", 0.22)
        for c in range(8):
            note(hz(acc[c % 3] + 12), t0 + c * temps / 2, temps / 2 * 0.7, "carre", 0.04, 0.125)
            note(1, t0 + c * temps / 2, 0.025, "bruit", 0.05 if c % 2 else 0.03)
        for b in (1, 3):
            note(1, t0 + b * temps, 0.09, "bruit", 0.12)
        if k >= 1 and not finale:
            for c in range(8):
                note(hz(melodie[(k % 4) * 8 + c]), t0 + c * temps / 2, temps / 2 * 0.85, "carre", 0.075, 0.25)
    total = int(taux * duree)
    fondu = int(1.2 * taux)
    pic = max(1e-9, max(abs(x) for x in out[:total]))
    echantillons = array.array("h")
    for i in range(total):
        g = 0.5 / pic * (min(1.0, (total - i) / fondu))
        echantillons.append(int(max(-1.0, min(1.0, out[i] * g)) * 32767))
    if sys.byteorder == "big":
        echantillons.byteswap()
    with wave.open(chemin, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(taux)
        w.writeframes(echantillons.tobytes())


# ============================================================================================ montage

class Monteur:
    def __init__(self, dossier, sortie, montage_json=None, ffmpeg=None, police=None):
        self.dossier = os.path.abspath(dossier)
        self.sortie = os.path.abspath(sortie)
        with open(montage_json or MONTAGE_PAR_DEFAUT, encoding="utf-8-sig") as f:
            self.m = json.load(f)
        self.ff = Ffmpeg(ffmpeg)
        if not os.path.isdir(self.dossier):
            raise ErreurMontage(f"dossier du tournage introuvable : {dossier}")
        chemin_chrono = os.path.join(self.dossier, "chronologie.json")
        video = self._video(chemin_chrono)
        _, _, _, duree = self.ff.sonder(video)
        self.chrono = Chronologie(chemin_chrono, duree)
        self.rushes = Rushes(self.ff, video, self.chrono.plage)
        fmt = self.m.get("format", {})
        self.ips = int(fmt.get("ips", 30))
        self.taille_h = tuple(fmt.get("horizontal", REF_H))
        self.taille_v = tuple(fmt.get("vertical", REF_V))
        self.aspect = REF_H[0] / REF_H[1]
        self.plans, self.sautes, self.duree = resoudre(self.m, self.chrono, self.ips)
        if not any(not p.carte for p in self.plans):
            raise ErreurMontage("aucun plan du montage ne correspond à une étape jouée de ce tournage.")
        # Un carton identique au plan précédent ne « tape » pas une seconde fois.
        precedent = None
        for p in self.plans:
            premier = p.cartons[0]["texte"] if p.cartons else None
            p.suite = 5.0 if premier and premier == precedent else 0.0
            precedent = p.cartons[-1]["texte"] if p.cartons else None
        self.atelier = Atelier(self.m, Polices(police), PilouHD())

    def _video(self, chemin_chrono):
        nom = None
        if os.path.isfile(chemin_chrono):
            try:
                with open(chemin_chrono, encoding="utf-8-sig") as f:
                    nom = json.load(f).get("video")
            except (OSError, ValueError):
                nom = None
        else:
            raise ErreurMontage("chronologie.json manque dans le dossier du tournage : sans elle, on ne sait pas où "
                                "commence le décor fictif, donc on ne monte rien (vie privée).")
        if nom and os.path.isfile(os.path.join(self.dossier, os.path.basename(nom))):
            return os.path.join(self.dossier, os.path.basename(nom))
        mp4 = [f for f in sorted(os.listdir(self.dossier)) if f.lower().endswith(".mp4")]
        if len(mp4) != 1:
            raise ErreurMontage("vidéo du tournage introuvable (une seule .mp4 attendue à côté de chronologie.json)")
        return os.path.join(self.dossier, mp4[0])

    # ---- déroulé

    def deroule(self):
        lignes = []
        for i, p in enumerate(self.plans, 1):
            carton = " / ".join(c["texte"].replace("|", " ") for c in p.cartons) or p.spec.get("titre", "")
            source = f"{p.a:6.2f} → {p.b:6.2f} s ×{p.vitesse:.2f}" if not p.carte else "carte".ljust(25)
            lignes.append(f"{i:2d}. {p.debut_sortie:5.1f} s  {p.duree:4.1f} s  {p.nom:<20} {source}  {carton}")
        lignes.append(f"Durée : {self.duree:.1f} s ({len(self.plans)} plans)")
        for nom, raison in self.sautes:
            lignes.append(f"   sauté : {nom} ({raison})")
        a, b = self.chrono.plage
        lignes.append(f"Plage lue dans la vidéo : {a:.2f} → {b:.2f} s (le reste n'est jamais lu)")
        if not any(p.cadres for p in self.plans if not p.carte):
            lignes.append("Attention : la chronologie n'a pas de rectangles à cadrer : plans larges.")
        return "\n".join(lignes)

    # ---- images

    def _images_plan(self, p, seulement=None):
        """(k, horizontale, verticale) à la taille de référence pour les images k du plan (toutes, ou celles
        de `seulement`)."""
        if p.carte:
            for k in range(p.n) if seulement is None else seulement:
                s = k / self.ips
                yield k, self.atelier.carte(p, s, False).convert("RGB"), self.atelier.carte(p, s, True).convert("RGB")
            return
        ecran = (self.rushes.largeur, self.rushes.hauteur)
        traj = trajectoire(p, self.m, ecran, self.aspect, self.ips)
        carres = [c for _, c in trajectoire(p, self.m, ecran, self.aspect, self.ips, vertical=True)]
        if seulement is not None:
            for k in seulement:
                t, cadre = traj[k]
                hz, vt = self.atelier.depuis_rush(self.rushes.image(t), cadre, carres[k], p, k / self.ips)
                yield k, hz, vt
            return
        flux = self.rushes.images(p.a, p.b)
        courant, j = next(flux, None), 0
        for k, (t, cadre) in enumerate(traj):
            voulu = int((t - p.a) * self.rushes.ips + 1e-6)
            while j < voulu:
                suivant = next(flux, None)
                if suivant is None:
                    break
                courant, j = suivant, j + 1
            if courant is None:
                courant = Image.new("RGB", ecran, COULEURS["encre"])
            hz, vt = self.atelier.depuis_rush(courant, cadre, carres[k], p, k / self.ips)
            yield k, hz, vt
        flux.close()

    def _finir(self, p, k, hz, vt, precedentes):
        """Transitions et fondus d'ouverture et de fermeture, puis mise au format de sortie."""
        s = k / self.ips
        if p.transition == "balayage":
            hz, vt = Atelier.balayage(hz, s), Atelier.balayage(vt, s)
        elif p.transition == "fondu" and precedentes and s < 0.3:
            hz, vt = fondre(precedentes[0], hz, s / 0.3), fondre(precedentes[1], vt, s / 0.3)
        t_abs = p.debut_sortie + s
        noir = min(1.0, t_abs / 0.3, (self.duree - t_abs) / 0.7)
        if noir < 1:
            hz = fondre(Image.new("RGB", hz.size, COULEURS["encre"]), hz, noir)
            vt = fondre(Image.new("RGB", vt.size, COULEURS["encre"]), vt, noir)
        return hz, vt

    def planche(self, chemin):
        """Une image par plan (au milieu du plan) : horizontale et verticale côte à côte, avec son étiquette."""
        tw, th, vw = 480, 270, 152
        cols = 4
        lignes = (len(self.plans) + cols - 1) // cols
        pl = Image.new("RGB", (cols * (tw + vw + 12), lignes * (th + 40)), (8, 10, 14))
        d = ImageDraw.Draw(pl)
        f = self.atelier.pol(18)
        for i, p in enumerate(self.plans):
            k = max(0, min(p.n - 1, p.n // 2))
            _, hz, vt = next(self._images_plan(p, [k]))
            x, y = (i % cols) * (tw + vw + 12), (i // cols) * (th + 40)
            pl.paste(hz.resize((tw, th), Image.LANCZOS), (x, y + 30))
            pl.paste(vt.resize((vw, th), Image.LANCZOS), (x + tw + 2, y + 30))
            d.text((x + 6, y + 5), f"{i + 1}. {p.nom}  ·  {p.debut_sortie:.1f} s  ·  {p.duree:.1f} s", font=f, fill=COULEURS["creme"])
        pl.save(chemin)

    def encodeur(self, chemin, taille, wav):
        args = ["-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{taille[0]}x{taille[1]}", "-r", str(self.ips), "-i", "-"]
        if wav:
            args += ["-i", wav, "-c:a", "aac", "-b:a", "160k", "-shortest"]
        args += ["-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", "-movflags", "+faststart", chemin]
        return self.ff.lancer(args, stdin=subprocess.PIPE)

    def monter(self, apercu=False):
        os.makedirs(self.sortie, exist_ok=True)
        dire(self.deroule())
        chemins = {k: os.path.join(self.sortie, v) for k, v in NOMS_SORTIE.items()}
        dire("Planche de contrôle…")
        self.planche(chemins["planche"])
        if apercu:
            dire(f"Aperçu : {chemins['planche']}")
            return chemins
        wav = None
        if self.m.get("musique", True):
            dire("Musique…")
            wav = os.path.join(self.sortie, ".pilou-musique.wav")
            musique(wav, self.duree, float(self.m.get("rythme", {}).get("bpm", 140)))
        try:
            eh = self.encodeur(chemins["horizontale"], self.taille_h, wav)
            ev = self.encodeur(chemins["verticale"], self.taille_v, wav)
            precedentes = None
            for i, p in enumerate(self.plans, 1):
                dire(f"  plan {i}/{len(self.plans)} : {p.nom}")
                derniere = None
                for k, hz, vt in self._images_plan(p):
                    hz, vt = self._finir(p, k, hz, vt, precedentes)
                    eh.stdin.write(a_la_taille(hz, self.taille_h).tobytes())
                    ev.stdin.write(a_la_taille(vt, self.taille_v).tobytes())
                    derniere = (hz, vt)
                precedentes = derniere
            for e in (eh, ev):
                e.stdin.close()
                if e.wait() != 0:
                    raise ErreurMontage("ffmpeg n'a pas pu encoder la vidéo")
        finally:
            if wav and os.path.exists(wav):
                os.remove(wav)
        dire("GIF…")
        g = self.m.get("gif", {})
        filtre = (f"fps={g.get('ips', 10)},scale={g.get('largeur', 480)}:-2:flags=lanczos,split[a][b];"
                  "[a]palettegen=max_colors=128:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle")
        self.ff.executer(["-y", "-i", chemins["horizontale"], "-filter_complex", filtre, "-loop", "0", chemins["gif"]])
        for k in ("horizontale", "verticale", "gif", "planche"):
            dire(f"  {chemins[k]}  ({os.path.getsize(chemins[k]) / 1e6:.1f} Mo)")
        return chemins


def principal(argv=None):
    for flux in (sys.stdout, sys.stderr):  # console Windows : jamais d'erreur sur un « … » ou un « → »
        try:
            flux.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="Monte la vidéo de promo de Pilou à partir d'un tournage.")
    ap.add_argument("tournage", help="dossier qui contient la vidéo et chronologie.json")
    ap.add_argument("--sortie", default=os.path.join(DEPOT, "docs", "promo"), help="dossier de sortie (docs/promo par défaut)")
    ap.add_argument("--montage", default=MONTAGE_PAR_DEFAUT, help="plan de montage (outils/video/montage.json)")
    ap.add_argument("--ffmpeg", default=None, help="chemin de ffmpeg s'il n'est pas dans le PATH")
    ap.add_argument("--police", default=None, help="police (.ttf) à utiliser pour les cartons")
    ap.add_argument("--apercu", action="store_true", help="planche de contrôle seule, sans vidéo (rapide)")
    ap.add_argument("--plan", action="store_true", help="affiche le déroulé et s'arrête (n'écrit rien)")
    a = ap.parse_args(argv)
    try:
        m = Monteur(a.tournage, a.sortie, a.montage, a.ffmpeg, a.police)
        if a.plan:
            dire(m.deroule())
            return 0
        m.monter(apercu=a.apercu)
        return 0
    except ErreurMontage as e:
        dire(f"Erreur : {e}")
        return 2


if __name__ == "__main__":
    sys.exit(principal())
