#!/usr/bin/env python3
"""Tests de l'outil de montage, sans tournage réel : python outils/video/test_monter.py

Une vidéo synthétique est fabriquée par ffmpeg : magenta avant 2 s et après 8 s (le « vrai bureau », interdit),
gris avec un carré bleu entre les deux (le décor). Une chronologie factice dit où sont les étapes.
On vérifie : étapes absentes ou non jouées sautées, durées attendues, cadrages bornés à l'image, plage interdite
jamais lue (ni demandée à ffmpeg, ni visible dans les vidéos produites), refus sans chronologie, decalage_s, et
que rien n'est écrit hors du dossier de sortie. Il faut Pillow et ffmpeg.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ICI = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True  # pas de __pycache__ dans le dépôt
sys.path.insert(0, ICI)
import monter as M  # noqa: E402

FF = shutil.which("ffmpeg")
IPS = 10
TAILLE = (640, 360)


def fabriquer_video(chemin):
    w, h = TAILLE
    filtre = (f"color=c=gray:s={w}x{h}:r={IPS}:d=10,"
              f"drawbox=x='100+40*t':y=200:w=80:h=80:color=0x6cb6ff:t=fill,"
              f"drawbox=x=0:y=0:w={w}:h={h}:color=magenta:t=fill:enable='lt(t,2)+gte(t,8)'")
    subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", filtre,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-g", "1", chemin], check=True)


def cadre(quoi, a, b, x, y, w, h):
    return {"quoi": quoi, "debut_s": a, "fin_s": b, "zone": {"x": x, "y": y, "largeur": w, "hauteur": h}}


CHRONO = {
    "video": "pilou-ecran-gauche.mp4",
    "etapes": [
        {"etape": "accueil", "jouee": True, "debut_s": 2.0, "fin_s": 4.0,
         "cadres": [cadre("pilou+bulle", 2.0, 4.0, 100, 190, 160, 100)]},
        {"etape": "promenade", "jouee": False, "debut_s": 4.0, "fin_s": 4.0, "cadres": []},
        # Un rectangle collé au bord et plus grand que l'écran : le cadre doit rester dans l'image.
        {"etape": "menu", "jouee": True, "debut_s": 4.0, "fin_s": 6.5,
         "cadres": [cadre("pilou+menu", 4.0, 5.0, 560, 300, 200, 200), cadre("boutique", 5.0, 6.5, -50, -40, 900, 500)]},
        {"etape": "fin", "jouee": True, "debut_s": 6.5, "fin_s": 8.0, "cadres": []},
    ],
}

MONTAGE = {
    "format": {"horizontal": [320, 180], "vertical": [180, 320], "ips": IPS},
    "rythme": {"bpm": 140, "pas_mesures": 0},
    "camera": {"lissage_s": 0.2, "marge": 20, "zoom_max": 3},
    "gif": {"largeur": 160, "ips": 5},
    "musique": True,
    "plans": [
        {"etape": "accueil", "vitesse": 1.0, "depuis_large": 0.5, "carton": {"texte": "Pilou", "taille": "titre"}},
        {"etape": "promenade", "vitesse": 1.0, "carton": {"texte": "sautée : non jouée"}},
        {"etape": "peche", "vitesse": 1.0, "carton": {"texte": "sautée : absente"}},
        {"etape": "menu", "de": 0.5, "vitesse": 2.0, "transition": "balayage", "carton": {"texte": "Un clic droit|et voilà."}},
        {"etape": "menu", "vitesse": 1.0, "transition": "fondu", "cadrage": {"quoi": "boutique", "restreindre": True}},
        {"etape": "fin", "vitesse": 1.0, "cadrage": {"quoi": "defense", "restreindre": True}},
        {"carte": "a_venir", "mesures": 1, "lignes": [{"texte": "Pilou", "taille": 120}]},
    ],
}


@unittest.skipUnless(FF, "ffmpeg absent du PATH")
class TestMonter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="pilou-montage-")
        cls.tournage = os.path.join(cls.tmp, "tournage")
        os.makedirs(cls.tournage)
        fabriquer_video(os.path.join(cls.tournage, "pilou-ecran-gauche.mp4"))
        cls.ecrire_chrono(CHRONO)
        cls.montage = os.path.join(cls.tmp, "montage.json")
        with open(cls.montage, "w", encoding="utf-8") as f:
            json.dump(MONTAGE, f, ensure_ascii=False)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    @classmethod
    def ecrire_chrono(cls, chrono):
        with open(os.path.join(cls.tournage, "chronologie.json"), "w", encoding="utf-8") as f:
            json.dump(chrono, f, ensure_ascii=False)

    def monteur(self, sortie="sortie"):
        return M.Monteur(self.tournage, os.path.join(self.tmp, sortie), self.montage)

    def test_etapes_sautees_et_durees(self):
        m = self.monteur()
        self.assertEqual([p.nom for p in m.plans], ["accueil", "menu", "menu", "a_venir"])
        self.assertEqual({n for n, _ in m.sautes}, {"promenade", "peche", "fin"})
        durees = [round(p.duree, 3) for p in m.plans]
        mesure = 4 * 60 / 140
        self.assertEqual(durees, [2.0, 1.0, 1.5, round(mesure, 3)])
        self.assertAlmostEqual(m.duree, 4.5 + mesure, places=3)
        # Le plan « restreindre » ne garde que les instants où la boutique est à l'image.
        self.assertAlmostEqual(m.plans[2].a, 5.0)
        self.assertAlmostEqual(m.plans[2].b, 6.5)

    def test_plage_sure_et_decalage(self):
        m = self.monteur()
        self.assertEqual(m.chrono.plage, (2.0, 8.0))
        with self.assertRaises(M.ErreurMontage):
            next(m.rushes.images(1.0, 3.0))
        with self.assertRaises(M.ErreurMontage):
            next(m.rushes.images(7.5, 8.6))
        # Vidéo recoupée d'une seconde au début : tout recule d'une seconde.
        decale = json.loads(json.dumps(CHRONO))
        decale["decalage_s"] = 1.0
        for e in decale["etapes"]:
            e["debut_s"] += 1.0
            e["fin_s"] += 1.0
            for c in e["cadres"]:
                c["debut_s"] += 1.0
                c["fin_s"] += 1.0
        self.ecrire_chrono(decale)
        try:
            m2 = self.monteur()
            self.assertEqual(m2.chrono.plage, (2.0, 8.0))
            self.assertEqual([round(p.a, 3) for p in m2.plans if not p.carte], [2.0, 4.5, 5.0])
        finally:
            self.ecrire_chrono(CHRONO)

    def test_cadrages_bornes(self):
        m = self.monteur()
        w, h = TAILLE
        for p in m.plans:
            if p.carte:
                continue
            for t, (x0, y0, lw, lh) in M.trajectoire(p, m.m, (w, h), 16 / 9, IPS):
                self.assertTrue(p.a - 1e-6 <= t <= p.b + 1e-6)
                self.assertGreaterEqual(x0, -1e-6)
                self.assertGreaterEqual(y0, -1e-6)
                self.assertLessEqual(x0 + lw, w + 1e-6)
                self.assertLessEqual(y0 + lh, h + 1e-6)
                self.assertAlmostEqual(lw / lh, 16 / 9, places=3)
            for t, (x0, y0, lw, lh) in M.trajectoire(p, m.m, (w, h), 16 / 9, IPS, vertical=True):
                self.assertTrue(x0 >= -1e-6 and y0 >= -1e-6 and x0 + lw <= w + 1e-6 and y0 + lh <= h + 1e-6)
                self.assertAlmostEqual(lw, lh, places=3)  # le carré de la version verticale
        # Zoom maximal respecté : jamais plus étroit qu'un tiers de l'écran (zoom_max 3).
        _, _, lw, _ = M.borner(*M.boite_169((10, 10, 4, 4), 0, (w, h), 3, 16 / 9), (w, h), 16 / 9)
        self.assertGreaterEqual(lw, w / 3 - 1e-6)

    def test_sans_chronologie_refus(self):
        vide = os.path.join(self.tmp, "sans-chrono")
        os.makedirs(vide, exist_ok=True)
        shutil.copy(os.path.join(self.tournage, "pilou-ecran-gauche.mp4"), vide)
        with self.assertRaises(M.ErreurMontage):
            M.Monteur(vide, os.path.join(self.tmp, "sortie-refus"), self.montage)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "sortie-refus")))
        self.assertEqual(M.principal([vide, "--sortie", os.path.join(self.tmp, "sortie-refus"), "--montage", self.montage]), 2)

    def test_montage_complet(self):
        avant = set(os.listdir(self.tmp)) | {"complet"}
        m = self.monteur("complet")
        chemins = m.monter()
        sortie = os.path.join(self.tmp, "complet")
        self.assertEqual(sorted(os.listdir(sortie)), sorted(M.NOMS_SORTIE.values()))
        self.assertEqual(set(os.listdir(self.tmp)), avant)  # rien d'écrit ailleurs
        for a, b in m.rushes.lectures:
            self.assertGreaterEqual(a, 2.0 - 0.5 / IPS)
            self.assertLessEqual(b, 8.0 + 0.5 / IPS)
        ff = M.Ffmpeg()
        for cle, taille in (("horizontale", (320, 180)), ("verticale", (180, 320))):
            w, h, _, duree = ff.sonder(chemins[cle])
            self.assertEqual((w, h), taille)
            self.assertAlmostEqual(duree, m.duree, delta=0.25)
            # Aucune image magenta (le « vrai bureau » de la vidéo synthétique) dans le film.
            p = subprocess.run([FF, "-loglevel", "error", "-i", chemins[cle], "-vf", "scale=32:32", "-f", "rawvideo",
                                "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
            px = p.stdout
            for i in range(0, len(px), 3):
                r, v, b = px[i], px[i + 1], px[i + 2]
                self.assertFalse(r > 200 and b > 200 and v < 80, "image magenta : plage interdite lue")


if __name__ == "__main__":
    unittest.main(verbosity=2)
