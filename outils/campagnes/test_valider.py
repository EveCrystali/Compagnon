#!/usr/bin/env python3
"""Tests du validateur des campagnes : une petite campagne juste, puis une faute à la fois.

    python3 outils/campagnes/test_valider.py
"""
import copy
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import valider  # noqa: E402

RACINE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

FICHE = {
    "v": 1, "id": "essai", "titre": "Essai", "ton": "humour", "accroche": "Une campagne pour les tests.", "niveau": 1, "duree": "≈ 1 h",
    "depart": "a-debut",
    "chapitres": [{"id": "a", "titre": "Un", "fichier": "chapitre-01.json"}, {"id": "b", "titre": "Deux", "fichier": "chapitre-02.json"}],
    "variables": {"courage": 0},
    "objets": [{"id": "cle", "nom": "Clé"}],
    "souvenirs": [{"id": "s-bon", "nom": "Bon", "texte": "Bien joué."}],
}
A = {"chapitre": "a", "noeuds": {
    "a-debut": {"type": "recit", "checkpoint": True, "texte": ["Je pars."], "effets": [{"drapeau": "parti"}], "suite": "a-choix"},
    "a-choix": {"type": "choix", "texte": ["Par où ?"], "options": [
        {"id": "nord", "libelle": "Le nord", "vers": "a-attente", "effets": [{"var": "courage", "plus": 1}, {"objet": "cle", "donne": True}]},
        {"id": "sud", "libelle": "Le sud", "vers": "a-epreuve", "si": {"tous": [{"drapeau": "parti"}, {"non": {"objet": "cle"}}]}},
    ]},
    "a-attente": {"type": "attente", "texte": ["J'y vais."], "duree_min": 10, "duree_max": 20, "pendant": "Pilou marche", "tenue": "marche", "suite": "b-entree"},
    "a-epreuve": {"type": "epreuve", "texte": ["Un pont."], "jeu": "reflexe", "difficulte": 2, "bonus": "courage", "reussite": "b-entree", "echec": "a-chute"},
    "a-chute": {"type": "echec", "texte": ["Aïe."], "repos_min": 15},
}}
B = {"chapitre": "b", "noeuds": {
    "b-entree": {"type": "choix", "checkpoint": True, "recompense": {"po": 20, "xp": 10}, "texte": ["La porte."], "options": [
        {"id": "ouvrir", "libelle": "Ouvrir", "vers": "b-fin", "si": {"var": "courage", "min": 1}},
        {"id": "frapper", "libelle": "Frapper", "vers": "b-hasard"},
    ]},
    "b-hasard": {"type": "hasard", "issues": [{"poids": 2, "vers": "b-fin"}, {"poids": 1, "vers": "b-triste"}]},
    "b-fin": {"type": "fin", "issue": "bonne", "titre": "Entré", "texte": ["Gagné."], "recompenses": {"po": 50, "xp": 20, "souvenir": "s-bon"}},
    "b-triste": {"type": "fin", "issue": "mauvaise", "titre": "Dehors", "texte": ["Raté."], "recompenses": {"po": 0, "xp": 1}},
}}


class Cas(unittest.TestCase):
    def valider(self, changer=None, brut=None):
        fiche, a, b = copy.deepcopy(FICHE), copy.deepcopy(A), copy.deepcopy(B)
        if changer:
            changer(fiche, a["noeuds"], b["noeuds"])
        with tempfile.TemporaryDirectory() as d:
            dossier = os.path.join(d, "essai")
            os.mkdir(dossier)
            for nom, contenu in (("campagne.json", fiche), ("chapitre-01.json", a), ("chapitre-02.json", b)):
                with open(os.path.join(dossier, nom), "w", encoding="utf-8") as f:
                    json.dump(contenu, f, ensure_ascii=False)
            for nom, texte in (brut or {}).items():
                with open(os.path.join(dossier, nom), "w", encoding="utf-8") as f:
                    f.write(texte)
            return valider.Validateur(dossier, parcours=200).valider()

    def erreur(self, changer, *morceaux, brut=None):
        r = self.valider(changer, brut)
        self.assertTrue(r.erreurs, "aucune erreur signalée")
        for m in morceaux:
            self.assertTrue(any(m in e for e in r.erreurs), f"« {m} » absent de :\n" + "\n".join(r.erreurs))
        return r

    def test_campagne_juste(self):
        r = self.valider()
        self.assertEqual([], r.erreurs)
        self.assertEqual([], [a for a in r.avertissements if "moins de 30 mots" not in a])
        self.assertTrue(any("2 fins atteignables" in s for s in r.stats), r.stats)
        self.assertTrue(any("meilleur parcours possible : 70 po, 30 xp" in s for s in r.stats), r.stats)

    def test_le_prologue_et_la_campagne_d_essai_du_moteur(self):
        for dossier in ("assets/campagnes/prologue", "android/app/src/test/resources/campagnes-essai/essai"):
            r = valider.Validateur(os.path.join(RACINE, dossier)).valider()
            self.assertEqual([], r.erreurs, dossier)
        self.assertEqual([], valider.Validateur(os.path.join(RACINE, "assets/campagnes/prologue")).valider().avertissements)

    def test_code_court_comme_le_moteur(self):
        # Mêmes valeurs que Campagnes.Code (android/app/src/test/resources/campagnes-vecteurs.txt).
        self.assertEqual("nfeZ", valider.code("p1-lettre"))
        self.assertEqual("Qb4v", valider.code("porte-du-phare"))
        vecteurs = os.path.join(RACINE, "android/app/src/test/resources/campagnes-vecteurs.txt")
        with open(vecteurs, encoding="utf-8") as f:
            for ligne in f:
                if ligne.startswith("code "):
                    _, ident, attendu = ligne.split()
                    self.assertEqual(attendu, valider.code(ident))
                if ligne.startswith("chance "):
                    _, d, b, attendu = ligne.split()
                    self.assertEqual(int(attendu), valider.chance_de(int(d), int(b)))

    def test_references(self):
        self.erreur(lambda f, a, b: a["a-debut"].update(suite="nulle-part"), "chapitre-01.json · a-debut", "« suite » pointe sur un nœud qui n'existe pas : « nulle-part »")
        self.erreur(lambda f, a, b: a["a-choix"]["options"][0].update(vers="x"), "a-choix", "option « nord » : vers")
        self.erreur(lambda f, a, b: a["a-epreuve"].update(echec="x"), "« echec » pointe")
        self.erreur(lambda f, a, b: b["b-hasard"]["issues"][0].update(vers="x"), "issue 1 : vers")
        self.erreur(lambda f, a, b: f.update(depart="x"), "« depart » pointe")

    def test_atteignable_et_fins(self):
        self.erreur(lambda f, a, b: b.update({"b-seul": {"type": "recit", "texte": ["Seul."], "suite": "b-fin"}}), "b-seul", "jamais atteint")
        self.erreur(lambda f, a, b: (b.update({"b-puits": {"type": "recit", "texte": ["Trou."], "suite": "b-puits2"},
                                               "b-puits2": {"type": "attente", "texte": ["…"], "duree_min": 5, "pendant": "Pilou tourne", "tenue": "marche", "suite": "b-puits"}}),
                                     b["b-hasard"]["issues"].append({"poids": 1, "vers": "b-puits"})), "b-puits", "aucune fin n'est atteignable")
        self.erreur(lambda f, a, b: b["b-fin"].update(issue="mauvaise"), "aucune fin « bonne »")

    def test_boucle_sans_attente_ni_choix(self):
        def boucle(f, a, b):
            b["b-r1"] = {"type": "recit", "texte": ["Un."], "suite": "b-r2"}
            b["b-r2"] = {"type": "hasard", "issues": [{"poids": 1, "vers": "b-r1"}, {"poids": 1, "vers": "b-fin"}]}
            b["b-hasard"]["issues"].append({"poids": 1, "vers": "b-r1"})
        self.erreur(boucle, "boucle sans attente ni choix : b-r1 → b-r2")

    def test_checkpoints(self):
        self.erreur(lambda f, a, b: b["b-entree"].pop("checkpoint"), "chapitre-02.json · b-entree", "on entre dans le chapitre « b » par ce nœud")
        self.erreur(lambda f, a, b: a["a-debut"].pop("checkpoint"), "a-debut", "checkpoint", "a-chute", "avant le premier check-point")

    def test_choix(self):
        self.erreur(lambda f, a, b: [o.update(si={"objet": "cle"}) for o in a["a-choix"]["options"]], "a-choix", "au moins une sans condition")
        self.erreur(lambda f, a, b: a["a-choix"]["options"].pop(), "de 2 à 4 options")
        self.erreur(lambda f, a, b: a["a-choix"]["options"][1].update(id="nord"), "identifiant déjà pris")
        self.erreur(lambda f, a, b: a["a-choix"]["options"][0].pop("libelle"), "« libelle » manque")

    def test_declarations(self):
        self.erreur(lambda f, a, b: a["a-choix"]["options"][0]["effets"].append({"var": "ruse", "plus": 1}), "variable « ruse » non déclarée")
        self.erreur(lambda f, a, b: a["a-choix"]["options"][1].update(si={"objet": "lanterne"}), "objet « lanterne » non déclaré")
        self.erreur(lambda f, a, b: a["a-choix"]["options"][1].update(si={"drapeau": "jamais-pose"}), "drapeau « jamais-pose » testé mais jamais posé")
        self.erreur(lambda f, a, b: b["b-fin"]["recompenses"].update(souvenir="s-inconnu"), "souvenir « s-inconnu » non déclaré")
        self.erreur(lambda f, a, b: a["a-epreuve"].update(bonus="chance"), "« bonus » : variable « chance » non déclarée")
        self.erreur(lambda f, a, b: a["a-debut"].update(decor="jetee"), "décor « jetee » non déclaré")
        self.erreur(lambda f, a, b: a["a-debut"].update(humeur="content"), "« humeur » vaut « content »")
        r = self.valider(lambda f, a, b: (f.update(decors=[{"id": "jetee", "nom": "La jetée", "description": "une jetée dans le brouillard"}]),
                                          a["a-debut"].update(decor="jetee", humeur="peur")))
        self.assertEqual([], r.erreurs)
        self.assertTrue(any("1 décors déclarés" in x for x in r.avertissements), r.avertissements)

    def test_bornes(self):
        self.erreur(lambda f, a, b: a["a-attente"].update(duree_min=0), "« duree_min » = 0 : un entier de 1 à 600")
        self.erreur(lambda f, a, b: a["a-attente"].update(duree_max=601), "« duree_max » = 601")
        self.erreur(lambda f, a, b: a["a-attente"].update(tenue="volant"), "« tenue » = 'volant'")
        self.erreur(lambda f, a, b: a["a-attente"].pop("pendant"), "« pendant » manque")
        self.erreur(lambda f, a, b: a["a-chute"].update(repos_min=5), "« repos_min » = 5 : un entier de 10 à 180")
        self.erreur(lambda f, a, b: a["a-epreuve"].update(difficulte=4), "« difficulte » = 4")
        self.erreur(lambda f, a, b: b["b-hasard"]["issues"][0].update(poids=0), "« poids » = 0")
        self.erreur(lambda f, a, b: a["a-debut"].update(texte=[" ".join(["mot"] * 161)]), "message 1 : 161 mots")
        self.erreur(lambda f, a, b: a["a-debut"].update(texte=['Il dit "bonjour".']), "guillemet droit")
        self.erreur(lambda f, a, b: a["a-debut"].update(type="teleportation"), "type « teleportation » inconnu")
        r = self.valider(lambda f, a, b: a["a-debut"].update(texte=[" ".join(["mot"] * 120)]))
        self.assertEqual([], r.erreurs)
        self.assertTrue(any("message 1 : 120 mots" in x for x in r.avertissements))

    def test_plafonds(self):
        self.erreur(lambda f, a, b: b["b-entree"].update(recompense={"po": 41, "xp": 10}), "le chapitre « b » peut rapporter 41 po")
        self.erreur(lambda f, a, b: b["b-entree"].update(recompense={"po": 10, "xp": 21}), "le chapitre « b » peut rapporter 21 xp")
        self.erreur(lambda f, a, b: b["b-fin"]["recompenses"].update(po=590), "le meilleur parcours rapporte 610 po")
        self.erreur(lambda f, a, b: b["b-fin"]["recompenses"].update(xp=295), "le meilleur parcours rapporte 305 xp")
        self.erreur(lambda f, a, b: (b["b-fin"]["recompenses"].update(titre="Un"), b["b-triste"]["recompenses"].update(titre="Deux")), "plusieurs titres différents")
        self.erreur(lambda f, a, b: b["b-entree"].update(recompense={"po": 10, "souvenir": "s-bon"}), "champ « souvenir » inattendu")
        self.erreur(lambda f, a, b: b["b-fin"].update(recompense={"po": 1}), "« recompenses » (au pluriel)")

    def test_fiche_et_fichiers(self):
        self.erreur(lambda f, a, b: f.update(id="autre"), "« id » (autre) doit être le nom du dossier (essai)")
        self.erreur(lambda f, a, b: f.update(ton="polar"), "« ton » doit être")
        self.erreur(lambda f, a, b: f.update(niveau=0), "« niveau »")
        self.erreur(lambda f, a, b: f["chapitres"].append({"id": "c", "titre": "Trois", "fichier": "chapitre-03.json"}), "chapitre-03.json", "fichier illisible")
        self.erreur(lambda f, a, b: b.update({"a-debut": {"type": "recit", "texte": ["Encore."], "suite": "b-fin"}}), "identifiant déjà utilisé dans chapitre-01.json")
        self.erreur(lambda f, a, b: b.update({"B_Majuscule": {"type": "recit", "texte": ["x"], "suite": "b-fin"}}), "minuscules ASCII")
        self.erreur(None, "chapitre-02.json", "JSON invalide, ligne 1", brut={"chapitre-02.json": '{"chapitre": "b", "noeuds": {'})
        self.erreur(None, "la clé « a-debut » apparaît deux fois", brut={"chapitre-01.json": '{"chapitre":"a","noeuds":{"a-debut":{},"a-debut":{}}}'})
        r = self.valider(brut={"chapitre-09.json": "{}"})
        self.assertTrue(any("chapitre-09.json" in x and "absent de « chapitres »" in x for x in r.avertissements))

    def test_avertissements(self):
        r = self.valider(lambda f, a, b: a["a-epreuve"].update(jeu="marelle"))
        self.assertEqual([], r.erreurs)
        self.assertTrue(any("jeu « marelle » inconnu" in x for x in r.avertissements))
        r = self.valider(lambda f, a, b: a["a-debut"].update(nouveau=1))
        self.assertTrue(any("champ « nouveau » ignoré" in x for x in r.avertissements))
        r = self.valider(lambda f, a, b: f["objets"].append({"id": "pain", "nom": "Pain"}))
        self.assertTrue(any("objet « pain » déclaré mais jamais testé" in x for x in r.avertissements))

    def test_echec_en_boucle(self):
        # Du check-point à l'échec sans que le joueur ait la main : Pilou échouerait en boucle, tout seul.
        self.erreur(lambda f, a, b: (b.update({"b-piege": {"type": "echec", "texte": ["Aïe."], "repos_min": 10}}),
                                     b["b-entree"].update(type="hasard", issues=[{"poids": 1, "vers": "b-fin"}, {"poids": 1, "vers": "b-piege"}]),
                                     b["b-entree"].pop("options"), b.pop("b-hasard"), b.pop("b-triste")),
                    "b-piege", "échec atteignable depuis le check-point « b-entree » sans choix")

    def test_code_de_sortie(self):
        self.assertEqual(0, valider.main([os.path.join(RACINE, "assets/campagnes"), "--sans-stats"]))
        with tempfile.TemporaryDirectory() as d:
            os.mkdir(os.path.join(d, "vide"))
            self.assertEqual(1, valider.main([d, "--sans-stats"]))
            self.assertEqual(1, valider.main([os.path.join(d, "absent"), "--sans-stats"]))


if __name__ == "__main__":
    unittest.main()
