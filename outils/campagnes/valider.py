#!/usr/bin/env python3
"""Validateur des campagnes de Pilou (docs/CAMPAGNES.md). Python 3, aucune dépendance.

    python3 outils/campagnes/valider.py                      toutes les campagnes de assets/campagnes/
    python3 outils/campagnes/valider.py assets/campagnes/x   une campagne (ou un dossier de campagnes)
    python3 outils/campagnes/valider.py --parcours 2000      plus de parcours tirés pour les statistiques

Il applique « Ce que le validateur exige » et les plafonds de récompenses, puis rend des statistiques (nœuds, mots,
choix et attentes par parcours, temps réel, fins atteignables). Chaque message dit le fichier, le nœud et la raison.
Les ERREURS font échouer (code de sortie 1) ; les AVERTISSEMENTS ne bloquent pas ; les notes situent la campagne par
rapport à la taille visée. Les mêmes règles que le moteur (apps/PilouBureau/Campagnes.cs, android/.../Campagnes.java).
"""
import argparse
import json
import os
import random
import re
import statistics
import sys

TONS = ("humour", "mystere", "emotion", "epique")
TYPES = ("recit", "choix", "attente", "epreuve", "hasard", "echec", "fin")
TENUES = ("marche", "course", "bateau", "grimpe", "nage", "nuit", "cache", "attend")
JEUX = ("reflexe", "memoire", "rythme", "visee", "des")
ISSUES = ("bonne", "douce-amere", "mauvaise", "secrete")
HUMEURS = ("joie", "peur", "triste", "surpris", "determine", "fatigue", "tendre", "colere", "malice", "neutre")
ID = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

COMMUNS = {"type", "texte", "checkpoint", "effets", "recompense", "lieu", "humeur", "decor"}
PROPRES = {
    "recit": {"suite"},
    "choix": {"options"},
    "attente": {"duree_min", "duree_max", "pendant", "tenue", "suite"},
    "epreuve": {"jeu", "difficulte", "bonus", "reussite", "echec"},
    "hasard": {"issues"},
    "echec": {"repos_min"},
    "fin": {"issue", "titre", "recompenses"},
}
FICHE = {"v", "id", "titre", "ton", "accroche", "niveau", "duree", "depart", "chapitres", "variables", "objets", "souvenirs", "decors"}

# Plafonds (docs/CAMPAGNES.md, « Récompenses »).
PO_CAMPAGNE, XP_CAMPAGNE, PO_CHAPITRE, XP_CHAPITRE = 600, 300, 40, 20
MOTS_MAX, MOTS_TROP = 110, 160
ALPHABET64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"


def code(ident):
    """Le code court du moteur (Campagnes.Code) : 4 caractères tirés du FNV-1a 64 bits de l'identifiant."""
    h = 0xCBF29CE484222325
    for ch in ident:
        for unite in _utf16(ch):
            h ^= unite
            h = (h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return "".join(ALPHABET64[(h >> (6 * i)) & 63] for i in range(4))


def _utf16(ch):
    o = ord(ch)
    if o < 0x10000:
        return (o,)
    o -= 0x10000
    return (0xD800 + (o >> 10), 0xDC00 + (o & 0x3FF))


def chance_de(difficulte, bonus):
    return max(10, min(95, 85 - 15 * max(1, min(3, difficulte)) + 5 * max(-20, min(20, bonus))))


def mots(texte):
    return len([m for m in re.split(r"\s+", texte.strip()) if re.search(r"\w", m)])


class Doublon(Exception):
    pass


def _sans_doublon(paires):
    d = {}
    for cle, valeur in paires:
        if cle in d:
            raise Doublon(cle)
        d[cle] = valeur
    return d


def lire_json(chemin):
    """(objet, None) ou (None, raison)."""
    try:
        with open(chemin, "rb") as f:
            brut = f.read()
    except OSError as e:
        return None, f"fichier illisible ({e.strerror})"
    if brut.startswith(b"\xef\xbb\xbf"):
        return None, "le fichier commence par un BOM : l'enregistrer en UTF-8 sans BOM"
    try:
        texte = brut.decode("utf-8")
    except UnicodeDecodeError as e:
        return None, f"le fichier n'est pas en UTF-8 (octet {e.start})"
    try:
        return json.loads(texte, object_pairs_hook=_sans_doublon), None
    except Doublon as e:
        return None, f"la clé « {e.args[0]} » apparaît deux fois dans le même objet"
    except json.JSONDecodeError as e:
        return None, f"JSON invalide, ligne {e.lineno}, colonne {e.colno} : {e.msg}"


def entier(v):
    return isinstance(v, int) and not isinstance(v, bool)


class Rapport:
    def __init__(self, nom, dossier):
        self.nom, self.dossier = nom, dossier
        self.erreurs, self.avertissements, self.notes, self.stats = [], [], [], []

    @staticmethod
    def _ou(fichier, noeud):
        return " · ".join(x for x in (fichier, noeud) if x)

    def erreur(self, fichier, noeud, raison):
        self.erreurs.append(f"{self._ou(fichier, noeud)} : {raison}")

    def avert(self, fichier, noeud, raison):
        self.avertissements.append(f"{self._ou(fichier, noeud)} : {raison}")

    def note(self, texte):
        self.notes.append(texte)


class Validateur:
    def __init__(self, dossier, parcours=400, graine=1):
        self.dossier = dossier
        self.nom = os.path.basename(os.path.normpath(dossier))
        self.r = Rapport(self.nom, dossier)
        self.n_parcours, self.graine = parcours, graine
        self.fiche = {}
        self.noeuds = {}      # id → nœud
        self.fichier = {}     # id → fichier de chapitre
        self.chapitre = {}    # id → id du chapitre
        self.chapitres = []   # ids, dans l'ordre
        self.variables, self.objets, self.souvenirs, self.decors = {}, set(), set(), set()
        self.drapeaux_poses, self.drapeaux_lus = set(), {}
        self.vars_lues, self.objets_lus, self.souvenirs_lus, self.decors_lus = set(), set(), set(), set()

    # ---- Petites vérifications communes

    def prose(self, fichier, noeud, champ, texte):
        if '"' in texte:
            self.r.erreur(fichier, noeud, f"guillemet droit \" dans « {champ} » : utiliser « » (ou l'apostrophe)")

    def ident(self, fichier, noeud, quoi, valeur):
        if not isinstance(valeur, str) or not ID.match(valeur):
            self.r.erreur(fichier, noeud, f"{quoi} « {valeur} » : minuscules ASCII, chiffres et tirets seulement (comme porte-du-phare)")
            return False
        return True

    def cible(self, fichier, noeud, champ, valeur):
        if not isinstance(valeur, str) or valeur == "":
            self.r.erreur(fichier, noeud, f"« {champ} » manque (l'identifiant du nœud suivant)")
            return False
        if valeur not in self.noeuds:
            self.r.erreur(fichier, noeud, f"« {champ} » pointe sur un nœud qui n'existe pas : « {valeur} »")
            return False
        return True

    def condition(self, fichier, noeud, ou, c):
        if not isinstance(c, dict):
            self.r.erreur(fichier, noeud, f"{ou} : une condition est un objet, par exemple {{ \"objet\": \"lanterne\" }}")
            return
        cles = set(c)
        if "non" in c:
            if cles != {"non"}:
                self.r.erreur(fichier, noeud, f"{ou} : « non » ne se combine pas avec {sorted(cles - {'non'})}")
            self.condition(fichier, noeud, ou, c["non"])
        elif "tous" in c or "un" in c:
            sorte = "tous" if "tous" in c else "un"
            if cles != {sorte}:
                self.r.erreur(fichier, noeud, f"{ou} : « {sorte} » ne se combine pas avec {sorted(cles - {sorte})}")
            if not isinstance(c[sorte], list) or not c[sorte]:
                self.r.erreur(fichier, noeud, f"{ou} : « {sorte} » attend une liste de conditions, non vide")
            else:
                for x in c[sorte]:
                    self.condition(fichier, noeud, ou, x)
        elif "var" in c:
            if cles - {"var", "min", "max"} or not ({"min", "max"} & cles):
                self.r.erreur(fichier, noeud, f"{ou} : une condition sur une variable s'écrit {{ \"var\": …, \"min\": n }} ou {{ \"var\": …, \"max\": n }}")
            for k in ("min", "max"):
                if k in c and not entier(c[k]):
                    self.r.erreur(fichier, noeud, f"{ou} : « {k} » doit être un entier")
            if c["var"] not in self.variables:
                self.r.erreur(fichier, noeud, f"{ou} : variable « {c['var']} » non déclarée dans campagne.json")
            self.vars_lues.add(c["var"])
        elif "objet" in c:
            if cles != {"objet"}:
                self.r.erreur(fichier, noeud, f"{ou} : une condition sur un objet s'écrit {{ \"objet\": \"…\" }} (pour « ne l'a pas » : {{ \"non\": {{ \"objet\": … }} }})")
            if c["objet"] not in self.objets:
                self.r.erreur(fichier, noeud, f"{ou} : objet « {c['objet']} » non déclaré dans campagne.json")
            self.objets_lus.add(c["objet"])
        elif "drapeau" in c:
            if cles != {"drapeau"}:
                self.r.erreur(fichier, noeud, f"{ou} : une condition sur un drapeau s'écrit {{ \"drapeau\": \"…\" }}")
            if isinstance(c["drapeau"], str):
                self.drapeaux_lus.setdefault(c["drapeau"], (fichier, noeud))
        else:
            self.r.erreur(fichier, noeud, f"{ou} : condition inconnue {sorted(cles)} (var, objet, drapeau, non, tous, un)")

    def effets(self, fichier, noeud, ou, liste):
        if not isinstance(liste, list):
            self.r.erreur(fichier, noeud, f"{ou} : « effets » est une liste")
            return
        for e in liste:
            if not isinstance(e, dict):
                self.r.erreur(fichier, noeud, f"{ou} : un effet est un objet, par exemple {{ \"var\": \"courage\", \"plus\": 1 }}")
            elif "var" in e:
                if set(e) != {"var", "plus"} or not entier(e.get("plus")):
                    self.r.erreur(fichier, noeud, f"{ou} : un effet sur une variable s'écrit {{ \"var\": …, \"plus\": entier }}")
                if e["var"] not in self.variables:
                    self.r.erreur(fichier, noeud, f"{ou} : variable « {e['var']} » non déclarée dans campagne.json")
            elif "objet" in e:
                if set(e) != {"objet", "donne"} or not isinstance(e.get("donne"), bool):
                    self.r.erreur(fichier, noeud, f"{ou} : un effet sur un objet s'écrit {{ \"objet\": …, \"donne\": true ou false }}")
                if e["objet"] not in self.objets:
                    self.r.erreur(fichier, noeud, f"{ou} : objet « {e['objet']} » non déclaré dans campagne.json")
            elif "drapeau" in e:
                if set(e) - {"drapeau", "ote"} or ("ote" in e and not isinstance(e["ote"], bool)):
                    self.r.erreur(fichier, noeud, f"{ou} : un effet sur un drapeau s'écrit {{ \"drapeau\": … }} ou {{ \"drapeau\": …, \"ote\": true }}")
                if self.ident(fichier, noeud, f"{ou} : drapeau", e["drapeau"]) and not e.get("ote"):
                    self.drapeaux_poses.add(e["drapeau"])
            else:
                self.r.erreur(fichier, noeud, f"{ou} : effet inconnu {sorted(e)} (var, objet, drapeau)")

    def prime(self, fichier, noeud, champ, p, fin):
        if not isinstance(p, dict):
            self.r.erreur(fichier, noeud, f"« {champ} » est un objet {{ \"po\": …, \"xp\": … }}")
            return 0, 0
        permis = {"po", "xp", "souvenir", "titre", "objet"} if fin else {"po", "xp"}
        for k in set(p) - permis:
            self.r.erreur(fichier, noeud, f"« {champ} » : champ « {k} » inattendu" + ("" if fin else " (souvenir, titre et objet se donnent à une fin)"))
        for k in ("po", "xp"):
            if k in p and (not entier(p[k]) or p[k] < 0):
                self.r.erreur(fichier, noeud, f"« {champ} » : « {k} » doit être un entier positif ou nul")
        if fin:
            if "souvenir" in p:
                if p["souvenir"] not in self.souvenirs:
                    self.r.erreur(fichier, noeud, f"souvenir « {p['souvenir']} » non déclaré dans campagne.json")
                self.souvenirs_lus.add(p["souvenir"])
            if "titre" in p and (not isinstance(p["titre"], str) or not p["titre"].strip() or len(p["titre"]) > 40):
                self.r.erreur(fichier, noeud, "le titre offert est un texte de 1 à 40 caractères")
            elif "titre" in p:
                self.prose(fichier, noeud, "recompenses.titre", p["titre"])
            if "objet" in p:
                self.ident(fichier, noeud, "objet exclusif", p["objet"])
        po, xp = p.get("po", 0), p.get("xp", 0)
        return (po if entier(po) else 0), (xp if entier(xp) else 0)

    # ---- Lecture

    def lire(self):
        r = self.r
        fiche, raison = lire_json(os.path.join(self.dossier, "campagne.json"))
        if fiche is None:
            r.erreur("campagne.json", "", raison)
            return False
        if not isinstance(fiche, dict):
            r.erreur("campagne.json", "", "la fiche doit être un objet JSON")
            return False
        self.fiche = fiche
        f = "campagne.json"
        for k in sorted(set(fiche) - FICHE):
            r.avert(f, "", f"champ inconnu « {k} » (ignoré par le moteur)")
        if fiche.get("v") != 1:
            r.erreur(f, "", "« v » doit valoir 1")
        if self.ident(f, "", "identifiant de campagne", fiche.get("id")) and fiche.get("id") != self.nom:
            r.erreur(f, "", f"« id » ({fiche.get('id')}) doit être le nom du dossier ({self.nom})")
        for k in ("titre", "accroche", "duree"):
            if not isinstance(fiche.get(k), str) or not fiche.get(k, "").strip():
                r.erreur(f, "", f"« {k} » manque")
            else:
                self.prose(f, "", k, fiche[k])
        if fiche.get("ton") not in TONS:
            r.erreur(f, "", f"« ton » doit être l'un de : {', '.join(TONS)}")
        if not entier(fiche.get("niveau")) or fiche.get("niveau") < 1:
            r.erreur(f, "", "« niveau » doit être un entier ≥ 1 (le niveau de Pilou requis)")

        variables = fiche.get("variables", {})
        if not isinstance(variables, dict):
            r.erreur(f, "", "« variables » est un objet { nom: valeur de départ }")
            variables = {}
        for nom, v in variables.items():
            self.ident(f, "", "variable", nom)
            if not entier(v):
                r.erreur(f, "", f"variable « {nom} » : la valeur de départ doit être un entier")
        self.variables = variables

        def declares(cle, avec_texte):
            vus = set()
            liste = fiche.get(cle, [])
            if not isinstance(liste, list):
                r.erreur(f, "", f"« {cle} » est une liste")
                return vus
            for x in liste:
                if not isinstance(x, dict) or not isinstance(x.get("id"), str):
                    r.erreur(f, "", f"« {cle} » : chaque entrée a un « id » et un « nom »")
                    continue
                self.ident(f, "", f"{cle} : identifiant", x["id"])
                if x["id"] in vus:
                    r.erreur(f, "", f"« {cle} » : « {x['id']} » déclaré deux fois")
                vus.add(x["id"])
                for k in ("nom",) + ((avec_texte,) if avec_texte else ()):
                    if not isinstance(x.get(k), str) or not x.get(k, "").strip():
                        r.erreur(f, "", f"« {cle} » · {x['id']} : « {k} » manque")
                    else:
                        self.prose(f, "", f"{cle}.{x['id']}.{k}", x[k])
            return vus

        self.objets = declares("objets", None)
        self.souvenirs = declares("souvenirs", "texte")
        self.decors = declares("decors", "description")

        chapitres = fiche.get("chapitres")
        if not isinstance(chapitres, list) or not chapitres:
            r.erreur(f, "", "« chapitres » manque : au moins un chapitre { id, titre, fichier }")
            return False
        fichiers_vus = set()
        for ch in chapitres:
            if not isinstance(ch, dict) or not all(isinstance(ch.get(k), str) and ch.get(k) for k in ("id", "titre", "fichier")):
                r.erreur(f, "", "« chapitres » : chaque chapitre a un « id », un « titre » et un « fichier »")
                continue
            self.ident(f, "", "identifiant de chapitre", ch["id"])
            self.prose(f, "", f"chapitres.{ch['id']}.titre", ch["titre"])
            if ch["id"] in self.chapitres:
                r.erreur(f, "", f"chapitre « {ch['id']} » déclaré deux fois")
                continue
            self.chapitres.append(ch["id"])
            nom = ch["fichier"]
            if nom in fichiers_vus or os.path.basename(nom) != nom:
                r.erreur(f, "", f"chapitre « {ch['id']} » : fichier « {nom} » déjà utilisé, ou hors du dossier")
                continue
            fichiers_vus.add(nom)
            contenu, raison = lire_json(os.path.join(self.dossier, nom))
            if contenu is None:
                r.erreur(nom, "", raison)
                continue
            if not isinstance(contenu, dict) or not isinstance(contenu.get("noeuds"), dict):
                r.erreur(nom, "", "un fichier de chapitre est { \"chapitre\": id, \"noeuds\": { … } }")
                continue
            if contenu.get("chapitre") != ch["id"]:
                r.erreur(nom, "", f"« chapitre » vaut « {contenu.get('chapitre')} » : attendu « {ch['id']} » (campagne.json)")
            for k in sorted(set(contenu) - {"chapitre", "noeuds"}):
                r.avert(nom, "", f"champ inconnu « {k} » (ignoré par le moteur)")
            if not contenu["noeuds"]:
                r.erreur(nom, "", "aucun nœud dans ce chapitre")
            for ident, n in contenu["noeuds"].items():
                self.ident(nom, ident, "identifiant de nœud", ident)
                if ident in self.noeuds:
                    r.erreur(nom, ident, f"identifiant déjà utilisé dans {self.fichier[ident]} (ils sont uniques dans toute la campagne)")
                    continue
                if not isinstance(n, dict):
                    r.erreur(nom, ident, "un nœud est un objet JSON")
                    continue
                self.noeuds[ident], self.fichier[ident], self.chapitre[ident] = n, nom, ch["id"]
        for nom in sorted(os.listdir(self.dossier)):
            if nom.endswith(".json") and nom != "campagne.json" and nom not in fichiers_vus:
                r.avert(nom, "", "fichier présent dans le dossier mais absent de « chapitres » (campagne.json) : il ne sera pas lu")
        return bool(self.noeuds)

    # ---- Les nœuds, un par un

    def textes(self, ident):
        t = self.noeuds[ident].get("texte", [])
        return [x for x in t if isinstance(x, str)] if isinstance(t, list) else []

    def suivants(self, ident):
        n = self.noeuds[ident]
        t = n.get("type")
        if t in ("recit", "attente"):
            l = [n.get("suite")]
        elif t == "choix":
            l = [o.get("vers") for o in n.get("options", []) if isinstance(o, dict)] if isinstance(n.get("options"), list) else []
        elif t == "epreuve":
            l = [n.get("reussite"), n.get("echec")]
        elif t == "hasard":
            l = [o.get("vers") for o in n.get("issues", []) if isinstance(o, dict)] if isinstance(n.get("issues"), list) else []
        else:
            l = []
        return [x for x in l if isinstance(x, str) and x in self.noeuds]

    def noeud(self, ident):
        r, n, f = self.r, self.noeuds[ident], self.fichier[ident]
        t = n.get("type")
        if t not in TYPES:
            r.erreur(f, ident, f"type « {t} » inconnu ({', '.join(TYPES)})")
            return
        for k in sorted(set(n) - COMMUNS - PROPRES[t]):
            ailleurs = [x for x in TYPES if k in PROPRES[x]]
            r.avert(f, ident, f"champ « {k} » ignoré pour un nœud « {t} »" + (f" (il sert aux nœuds {', '.join(ailleurs)})" if ailleurs else " (champ inconnu)"))

        texte = n.get("texte")
        if texte is None:
            if t in ("recit", "choix", "attente", "echec", "fin"):
                r.erreur(f, ident, f"« texte » manque (un nœud « {t} » dit toujours quelque chose)")
        elif not isinstance(texte, list) or not texte or not all(isinstance(x, str) and x.strip() for x in texte):
            r.erreur(f, ident, "« texte » est une liste de paragraphes non vides")
        else:
            for i, x in enumerate(texte):
                self.prose(f, ident, f"texte[{i + 1}]", x)
                m = mots(x)
                if m > MOTS_TROP:
                    r.erreur(f, ident, f"message {i + 1} : {m} mots (au plus {MOTS_MAX} ; le couper en deux messages)")
                elif m > MOTS_MAX:
                    r.avert(f, ident, f"message {i + 1} : {m} mots (visé : 30 à {MOTS_MAX})")
        if "checkpoint" in n and not isinstance(n["checkpoint"], bool):
            r.erreur(f, ident, "« checkpoint » vaut true ou false")
        if "effets" in n:
            self.effets(f, ident, "effets", n["effets"])
        if "lieu" in n:
            if not isinstance(n["lieu"], str) or not n["lieu"].strip():
                r.erreur(f, ident, "« lieu » est un court libellé")
            else:
                self.prose(f, ident, "lieu", n["lieu"])
                if len(n["lieu"]) > 40:
                    r.avert(f, ident, f"« lieu » fait {len(n['lieu'])} caractères (c'est un libellé d'en-tête : 40 au plus)")
        if "humeur" in n and n["humeur"] not in HUMEURS:
            r.erreur(f, ident, f"« humeur » vaut « {n['humeur']} » : attendu l'une de {', '.join(HUMEURS)}")
        if "decor" in n:
            if n["decor"] not in self.decors:
                r.erreur(f, ident, f"décor « {n['decor']} » non déclaré dans « decors » (campagne.json)")
            if isinstance(n["decor"], str):
                self.decors_lus.add(n["decor"])
        if "recompense" in n:
            if t == "fin":
                r.erreur(f, ident, "une fin donne ses récompenses dans « recompenses » (au pluriel), pas « recompense »")
            else:
                self.prime(f, ident, "recompense", n["recompense"], False)

        if t in ("recit", "attente"):
            self.cible(f, ident, "suite", n.get("suite"))
        if t == "choix":
            options = n.get("options")
            if not isinstance(options, list) or not 2 <= len(options) <= 4:
                r.erreur(f, ident, "« options » : de 2 à 4 options")
                options = options if isinstance(options, list) else []
            ids, libres = set(), 0
            for i, o in enumerate(options):
                ou = f"option {i + 1}"
                if not isinstance(o, dict):
                    r.erreur(f, ident, f"{ou} : une option est {{ \"id\", \"libelle\", \"vers\" }}")
                    continue
                for k in sorted(set(o) - {"id", "libelle", "vers", "si", "effets"}):
                    r.avert(f, ident, f"{ou} : champ inconnu « {k} » (ignoré par le moteur)")
                if self.ident(f, ident, f"{ou} : identifiant", o.get("id")):
                    ou = f"option « {o['id']} »"
                    if o["id"] in ids:
                        r.erreur(f, ident, f"{ou} : identifiant déjà pris par une autre option de ce choix")
                    ids.add(o["id"])
                if not isinstance(o.get("libelle"), str) or not o.get("libelle", "").strip():
                    r.erreur(f, ident, f"{ou} : « libelle » manque")
                else:
                    self.prose(f, ident, f"{ou}.libelle", o["libelle"])
                    if len(o["libelle"]) > 60:
                        r.avert(f, ident, f"{ou} : libellé de {len(o['libelle'])} caractères (un bouton : 60 au plus)")
                self.cible(f, ident, f"{ou} : vers", o.get("vers"))
                if "si" in o:
                    self.condition(f, ident, f"{ou} : si", o["si"])
                else:
                    libres += 1
                if "effets" in o:
                    self.effets(f, ident, f"{ou} : effets", o["effets"])
            if options and libres == 0:
                r.erreur(f, ident, "toutes les options ont une condition « si » : il doit en rester au moins une sans condition")
        if t == "attente":
            d, dmax = n.get("duree_min"), n.get("duree_max")
            if not entier(d) or not 1 <= d <= 600:
                r.erreur(f, ident, f"« duree_min » = {d!r} : un entier de 1 à 600 minutes")
            if dmax is not None and (not entier(dmax) or not entier(d) or dmax < d or dmax > 600):
                r.erreur(f, ident, f"« duree_max » = {dmax!r} : un entier entre duree_min et 600 minutes")
            if not isinstance(n.get("pendant"), str) or not n.get("pendant", "").strip():
                r.erreur(f, ident, "« pendant » manque (la ligne d'état : « Pilou longe la falaise »)")
            else:
                self.prose(f, ident, "pendant", n["pendant"])
                if len(n["pendant"]) > 60:
                    r.avert(f, ident, f"« pendant » fait {len(n['pendant'])} caractères (une ligne d'état : 60 au plus)")
            if n.get("tenue") not in TENUES:
                r.erreur(f, ident, f"« tenue » = {n.get('tenue')!r} : attendu l'une de {', '.join(TENUES)}")
        if t == "epreuve":
            if not isinstance(n.get("jeu"), str) or not n.get("jeu"):
                r.erreur(f, ident, f"« jeu » manque ({', '.join(JEUX)})")
            elif n["jeu"] not in JEUX:
                r.avert(f, ident, f"jeu « {n['jeu']} » inconnu : il sera remplacé par un tirage « des » ({', '.join(JEUX)})")
            if not entier(n.get("difficulte")) or not 1 <= n.get("difficulte") <= 3:
                r.erreur(f, ident, f"« difficulte » = {n.get('difficulte')!r} : 1, 2 ou 3")
            if "bonus" in n:
                if n["bonus"] not in self.variables:
                    r.erreur(f, ident, f"« bonus » : variable « {n['bonus']} » non déclarée dans campagne.json")
                self.vars_lues.add(n["bonus"])
            self.cible(f, ident, "reussite", n.get("reussite"))
            self.cible(f, ident, "echec", n.get("echec"))
        if t == "hasard":
            issues = n.get("issues")
            if not isinstance(issues, list) or not issues:
                r.erreur(f, ident, "« issues » : au moins une issue { \"poids\", \"vers\" }")
                issues = []
            libres = 0
            for i, o in enumerate(issues):
                ou = f"issue {i + 1}"
                if not isinstance(o, dict):
                    r.erreur(f, ident, f"{ou} : une issue est {{ \"poids\", \"vers\" }}")
                    continue
                for k in sorted(set(o) - {"poids", "vers", "si"}):
                    r.avert(f, ident, f"{ou} : champ inconnu « {k} » (ignoré par le moteur)")
                if not entier(o.get("poids")) or o.get("poids") < 1:
                    r.erreur(f, ident, f"{ou} : « poids » = {o.get('poids')!r} : un entier ≥ 1")
                self.cible(f, ident, f"{ou} : vers", o.get("vers"))
                if "si" in o:
                    self.condition(f, ident, f"{ou} : si", o["si"])
                else:
                    libres += 1
            if len(issues) == 1:
                r.avert(f, ident, "une seule issue : ce n'est pas un hasard (un nœud « recit » suffit)")
            elif issues and libres == 0:
                r.avert(f, ident, "toutes les issues ont une condition : si aucune n'est vraie, le moteur tire parmi toutes")
        if t == "echec":
            if not entier(n.get("repos_min")) or not 10 <= n.get("repos_min") <= 180:
                r.erreur(f, ident, f"« repos_min » = {n.get('repos_min')!r} : un entier de 10 à 180 minutes")
        if t == "fin":
            if n.get("issue") not in ISSUES:
                r.erreur(f, ident, f"« issue » = {n.get('issue')!r} : attendu l'une de {', '.join(ISSUES)}")
            if not isinstance(n.get("titre"), str) or not n.get("titre", "").strip():
                r.erreur(f, ident, "« titre » manque (le nom de cette fin)")
            else:
                self.prose(f, ident, "titre", n["titre"])
            if "recompenses" not in n:
                r.erreur(f, ident, "« recompenses » manque ({ \"po\", \"xp\", \"souvenir\"? … })")
            else:
                self.prime(f, ident, "recompenses", n["recompenses"], True)

    # ---- Le graphe

    def graphe(self):
        r, noeuds = self.r, self.noeuds
        depart = self.fiche.get("depart")
        if not isinstance(depart, str) or depart not in noeuds:
            r.erreur("campagne.json", "", f"« depart » pointe sur un nœud qui n'existe pas : « {depart} »")
            return
        suiv = {i: self.suivants(i) for i in noeuds}
        typ = {i: noeuds[i].get("type") for i in noeuds}
        cp = {i for i in noeuds if noeuds[i].get("checkpoint") is True}

        # Tout nœud est atteignable depuis le départ.
        vus, pile = {depart}, [depart]
        while pile:
            for s in suiv[pile.pop()]:
                if s not in vus:
                    vus.add(s)
                    pile.append(s)
        for i in sorted(set(noeuds) - vus):
            r.erreur(self.fichier[i], i, "nœud jamais atteint depuis le départ (aucun « vers », « suite », « reussite » ou « echec » n'y mène)")

        # Depuis tout nœud, une fin est atteignable (un échec ramène au check-point, qui doit lui-même mener à une fin).
        vers = {i: [] for i in noeuds}
        for i, l in suiv.items():
            for s in l:
                vers[s].append(i)
        fins = [i for i in noeuds if typ[i] == "fin"]
        ok, pile = set(fins), list(fins)
        while pile:
            for p in vers[pile.pop()]:
                if p not in ok:
                    ok.add(p)
                    pile.append(p)
        for i in sorted(vus - ok):
            if typ[i] != "echec" and typ[i] in TYPES:
                r.erreur(self.fichier[i], i, "aucune fin n'est atteignable depuis ce nœud (cul-de-sac, ou boucle sans sortie)")
        if not fins:
            r.erreur("campagne.json", "", "aucun nœud « fin »")
        elif not any(noeuds[i].get("issue") == "bonne" for i in fins):
            r.erreur("campagne.json", "", "aucune fin « bonne »")

        # Un check-point au début de chaque chapitre (là où l'on y entre) ; pas d'échec avant le premier check-point.
        entrees = {depart}
        for i, l in suiv.items():
            for s in l:
                if self.chapitre[s] != self.chapitre[i]:
                    entrees.add(s)
        for i in sorted(entrees):
            if i not in cp:
                r.erreur(self.fichier[i], i, f"on entre dans le chapitre « {self.chapitre[i]} » par ce nœud : il lui faut \"checkpoint\": true")
        for ch in self.chapitres:
            if not any(self.chapitre[i] == ch for i in cp) and any(self.chapitre[i] == ch for i in noeuds):
                r.erreur(next(self.fichier[i] for i in noeuds if self.chapitre[i] == ch), "", f"aucun check-point dans le chapitre « {ch} »")
        if depart not in cp:
            avant, pile = {depart}, [depart]
            while pile:
                for s in suiv[pile.pop()]:
                    if s not in avant and s not in cp:
                        avant.add(s)
                        pile.append(s)
            for i in sorted(avant):
                if typ[i] == "echec":
                    r.erreur(self.fichier[i], i, "échec atteignable avant le premier check-point (Pilou n'aurait nulle part où revenir)")

        # Aucune boucle sans attente ni choix (récits, hasards et épreuves qui tournent en rond).
        autos = {i for i in noeuds if typ[i] in ("recit", "hasard", "epreuve")}
        for comp in self.composantes({i: [s for s in suiv[i] if s in autos] for i in autos}):
            if len(comp) > 1 or comp[0] in suiv[comp[0]]:
                premier = sorted(comp)[0]
                r.erreur(self.fichier[premier], premier, "boucle sans attente ni choix : " + " → ".join(sorted(comp)))

        # Du check-point à l'échec sans que le joueur ait la main (récits, hasards, épreuves aux dés) : Pilou échouerait
        # en boucle, tout seul, à chaque fin de repos.
        sans_geste = {i for i in noeuds if typ[i] in ("recit", "hasard") or (typ[i] == "epreuve" and noeuds[i].get("jeu") not in JEUX[:4])}
        for c in sorted(cp):
            vus2, pile = {c}, [c]
            while pile:
                x = pile.pop()
                if x not in sans_geste:
                    continue
                for s in suiv[x]:
                    if s not in vus2:
                        vus2.add(s)
                        pile.append(s)
            for i in sorted(vus2):
                if typ[i] == "echec":
                    r.erreur(self.fichier[i], i, f"échec atteignable depuis le check-point « {c} » sans choix, attente ni mini-jeu : après le repos, "
                                                 "Pilou y retomberait tout seul, en boucle (mettre un choix ou une attente entre les deux)")

        self.plafonds(suiv, typ)
        self.fins_graphe = sorted(i for i in fins if i in vus)

    @staticmethod
    def composantes(g):
        """Composantes fortement connexes (Tarjan, sans récursion), dans l'ordre topologique inverse."""
        index, bas, sur, pile, r, n = {}, {}, set(), [], [], [0]
        for racine in g:
            if racine in index:
                continue
            travail = [(racine, iter(g[racine]))]
            index[racine] = bas[racine] = n[0]
            n[0] += 1
            pile.append(racine)
            sur.add(racine)
            while travail:
                v, it = travail[-1]
                avance = False
                for w in it:
                    if w not in index:
                        index[w] = bas[w] = n[0]
                        n[0] += 1
                        pile.append(w)
                        sur.add(w)
                        travail.append((w, iter(g[w])))
                        avance = True
                        break
                    if w in sur:
                        bas[v] = min(bas[v], index[w])
                if avance:
                    continue
                travail.pop()
                if travail:
                    bas[travail[-1][0]] = min(bas[travail[-1][0]], bas[v])
                if bas[v] == index[v]:
                    comp = []
                    while True:
                        w = pile.pop()
                        sur.discard(w)
                        comp.append(w)
                        if w == v:
                            break
                    r.append(comp)
        return r

    def gain(self, ident, cle):
        n = self.noeuds[ident]
        p = n.get("recompenses" if n.get("type") == "fin" else "recompense")
        v = p.get(cle, 0) if isinstance(p, dict) else 0
        return v if entier(v) and v > 0 else 0

    def meilleur(self, suiv, garde, cle):
        """Le plus qu'un parcours puisse gagner (une récompense ne se touche qu'une fois) parmi les nœuds gardés."""
        g = {i: [s for s in suiv[i] if s in garde] for i in garde}
        comps = self.composantes(g)
        de = {}
        for k, comp in enumerate(comps):
            for i in comp:
                de[i] = k
        total = [0] * len(comps)
        for k, comp in enumerate(comps):          # ordre topologique inverse : les suivants sont déjà calculés
            apres = max([total[de[s]] for i in comp for s in g[i] if de[s] != k], default=0)
            total[k] = sum(self.gain(i, cle) for i in comp) + apres
        return max(total, default=0)

    def plafonds(self, suiv, typ):
        r = self.r
        tous = set(self.noeuds)
        po, xp = self.meilleur(suiv, tous, "po"), self.meilleur(suiv, tous, "xp")
        self.po_max, self.xp_max = po, xp
        if po > PO_CAMPAGNE:
            r.erreur("campagne.json", "", f"le meilleur parcours rapporte {po} po : au plus {PO_CAMPAGNE} pour une campagne (fins de chapitre comprises)")
        if xp > XP_CAMPAGNE:
            r.erreur("campagne.json", "", f"le meilleur parcours rapporte {xp} xp : au plus {XP_CAMPAGNE} pour une campagne (fins de chapitre comprises)")
        for ch in self.chapitres:
            garde = {i for i in tous if self.chapitre[i] == ch and typ[i] != "fin"}
            if not garde:
                continue
            po, xp = self.meilleur(suiv, garde, "po"), self.meilleur(suiv, garde, "xp")
            f = next(self.fichier[i] for i in garde)
            if po > PO_CHAPITRE:
                r.erreur(f, "", f"le chapitre « {ch} » peut rapporter {po} po sur un parcours : au plus {PO_CHAPITRE} par chapitre (hors fin)")
            if xp > XP_CHAPITRE:
                r.erreur(f, "", f"le chapitre « {ch} » peut rapporter {xp} xp sur un parcours : au plus {XP_CHAPITRE} par chapitre (hors fin)")
        for cle, nom in (("titre", "titre"), ("objet", "objet exclusif")):
            donnes = sorted({self.noeuds[i]["recompenses"][cle] for i in tous if typ[i] == "fin" and isinstance(self.noeuds[i].get("recompenses"), dict)
                             and isinstance(self.noeuds[i]["recompenses"].get(cle), str)})
            if len(donnes) > 1:
                r.erreur("campagne.json", "", f"plusieurs {nom}s différents selon les fins ({', '.join(donnes)}) : un seul par campagne")

    # ---- Déclarations, codes courts

    def declarations(self):
        r = self.r
        for nom, (f, ident) in sorted(self.drapeaux_lus.items()):
            if nom not in self.drapeaux_poses:
                r.erreur(f, ident, f"drapeau « {nom} » testé mais jamais posé par un effet (un drapeau se déclare par son premier {{ \"drapeau\": … }} en effet)")
        modifiees = set()
        for n in self.noeuds.values():
            for bloc in [n] + [o for o in n.get("options", []) if isinstance(o, dict)] if isinstance(n.get("options", []), list) else [n]:
                for e in bloc.get("effets", []) if isinstance(bloc.get("effets", []), list) else []:
                    if isinstance(e, dict) and "var" in e:
                        modifiees.add(e["var"])
        for v in sorted(set(self.variables) - self.vars_lues):
            r.avert("campagne.json", "", f"variable « {v} » déclarée mais jamais testée (ni condition, ni bonus d'épreuve)")
        for v in sorted(set(self.variables) - modifiees):
            r.avert("campagne.json", "", f"variable « {v} » déclarée mais jamais modifiée par un effet")
        for o in sorted(self.objets - self.objets_lus):
            r.avert("campagne.json", "", f"objet « {o} » déclaré mais jamais testé par une condition")
        for d in sorted(self.drapeaux_poses - set(self.drapeaux_lus)):
            r.avert("campagne.json", "", f"drapeau « {d} » posé mais jamais testé par une condition")
        for s in sorted(self.souvenirs - self.souvenirs_lus):
            r.avert("campagne.json", "", f"souvenir « {s} » déclaré mais donné par aucune fin")
        for d in sorted(self.decors - self.decors_lus):
            r.avert("campagne.json", "", f"décor « {d} » déclaré mais utilisé par aucun nœud")
        if self.decors and not 6 <= len(self.decors) <= 14:
            r.avert("campagne.json", "", f"{len(self.decors)} décors déclarés (visé : 6 à 14 par campagne)")
        # Les messages de synchronisation désignent nœuds, variables, objets, drapeaux et décors par un code de 4 caractères.
        for quoi, ids in (("nœuds", self.noeuds), ("variables", self.variables), ("objets", self.objets),
                          ("drapeaux", self.drapeaux_poses), ("décors", self.decors)):
            par_code = {}
            for i in sorted(x for x in ids if isinstance(x, str)):
                c = code(i)
                if c in par_code:
                    f = self.fichier.get(i, "campagne.json")
                    r.erreur(f, i if i in self.noeuds else "", f"{quoi} « {par_code[c]} » et « {i} » ont le même code court ({c}) : "
                                                               "renommer l'un des deux (les messages entre appareils les confondraient)")
                else:
                    par_code[c] = i

    # ---- Statistiques : des parcours tirés au hasard, joués comme le moteur

    def vrai(self, c, e):
        if c is None:
            return True
        if not isinstance(c, dict):
            return False
        if "non" in c:
            return not self.vrai(c["non"], e)
        if "tous" in c:
            return all(self.vrai(x, e) for x in c["tous"])
        if "un" in c:
            return any(self.vrai(x, e) for x in c["un"])
        if "var" in c:
            v = e["vars"].get(c["var"], 0)
            return ("min" not in c or v >= c["min"]) and ("max" not in c or v <= c["max"])
        if "objet" in c:
            return c["objet"] in e["objets"]
        if "drapeau" in c:
            return c["drapeau"] in e["drapeaux"]
        return False

    @staticmethod
    def appliquer(effets, e):
        for x in effets or []:
            if "var" in x:
                e["vars"][x["var"]] = e["vars"].get(x["var"], 0) + x.get("plus", 0)
            elif "objet" in x:
                (e["objets"].add if x.get("donne", True) else e["objets"].discard)(x["objet"])
            elif "drapeau" in x:
                (e["drapeaux"].discard if x.get("ote") else e["drapeaux"].add)(x["drapeau"])

    def parcours(self, h):
        """Un parcours : (fin atteinte ou None, compteurs)."""
        e = {"vars": dict(self.variables), "objets": set(), "drapeaux": set()}
        photo = lambda: {"vars": dict(e["vars"]), "objets": set(e["objets"]), "drapeaux": set(e["drapeaux"])}
        c = {"noeuds": 0, "mots": 0, "choix": 0, "attentes": 0, "longues": 0, "minutes": 0, "echecs": 0, "po": 0, "xp": 0}
        payes = set()
        ident, cp = self.fiche["depart"], None
        for _ in range(20000):
            n = self.noeuds[ident]
            t = n["type"]
            if n.get("checkpoint") is True or cp is None:
                cp = (ident, photo())
            self.appliquer(n.get("effets"), e)
            c["noeuds"] += 1
            c["mots"] += sum(mots(x) for x in self.textes(ident))
            if ident not in payes:
                payes.add(ident)
                c["po"] += self.gain(ident, "po")
                c["xp"] += self.gain(ident, "xp")
            if t == "recit":
                ident = n["suite"]
            elif t == "choix":
                possibles = [o for o in n["options"] if self.vrai(o.get("si"), e)]
                o = h.choice(possibles)
                c["choix"] += 1
                self.appliquer(o.get("effets"), e)
                ident = o["vers"]
            elif t == "attente":
                d = h.randint(n["duree_min"], n.get("duree_max", n["duree_min"]))
                c["attentes"] += 1
                c["longues"] += 1 if d >= 60 else 0
                c["minutes"] += d
                ident = n["suite"]
            elif t == "epreuve":
                ok = h.randrange(100) < chance_de(n["difficulte"], e["vars"].get(n.get("bonus"), 0) if n.get("bonus") else 0)
                ident = n["reussite"] if ok else n["echec"]
            elif t == "hasard":
                possibles = [o for o in n["issues"] if self.vrai(o.get("si"), e)] or n["issues"]
                ident = h.choices(possibles, weights=[o["poids"] for o in possibles])[0]["vers"]
            elif t == "echec":
                c["echecs"] += 1
                c["minutes"] += n["repos_min"]
                ident = cp[0]
                e = {"vars": dict(cp[1]["vars"]), "objets": set(cp[1]["objets"]), "drapeaux": set(cp[1]["drapeaux"])}
            else:
                return ident, c
        return None, c

    @staticmethod
    def duree(minutes):
        minutes = int(round(minutes))
        if minutes < 60:
            return f"{minutes} min"
        if minutes < 48 * 60:
            return f"{minutes // 60} h {minutes % 60:02d}"
        return f"{minutes / 1440:.1f} j".replace(".", ",")

    def statistiques(self):
        r, noeuds = self.r, self.noeuds
        par_type = {t: sum(1 for n in noeuds.values() if n.get("type") == t) for t in TYPES}
        messages = [mots(x) for i in noeuds for x in self.textes(i)]
        r.stats.append(f"{len(noeuds)} nœuds en {len(self.chapitres)} chapitres (" + ", ".join(f"{v} {k}" for k, v in par_type.items() if v) + ")")
        r.stats.append(f"{sum(messages)} mots en {len(messages)} messages" + (f" (médiane {int(statistics.median(messages))} mots par message)" if messages else ""))
        courts = sum(1 for m in messages if m < 30)
        if messages and courts * 3 > len(messages):
            r.avert("campagne.json", "", f"{courts} messages sur {len(messages)} font moins de 30 mots (visé : 30 à {MOTS_MAX} mots par message)")
        h = random.Random(self.graine)
        finis, perdus, atteintes = [], 0, {}
        for _ in range(self.n_parcours):
            fin, c = self.parcours(h)
            if fin is None:
                perdus += 1
            else:
                finis.append(c)
                atteintes[fin] = atteintes.get(fin, 0) + 1
        if perdus:
            r.avert("campagne.json", "", f"{perdus} parcours sur {self.n_parcours} n'ont pas trouvé de fin en 20 000 nœuds (boucle dont on sort trop rarement ?)")
        if finis:
            def trio(cle, f=str):
                v = sorted(c[cle] for c in finis)
                return f"min {f(v[0])}, médiane {f(statistics.median(v))}, max {f(v[-1])}"
            entier_ = lambda x: str(int(x))
            r.stats.append(f"sur {len(finis)} parcours tirés au hasard (choix au hasard, épreuves aux dés) :")
            r.stats.append(f"  choix par parcours : {trio('choix', entier_)}")
            r.stats.append(f"  attentes par parcours : {trio('attentes', entier_)} (dont longues, ≥ 1 h : {trio('longues', entier_)})")
            r.stats.append(f"  temps réel total (attentes et repos) : {trio('minutes', self.duree)}")
            r.stats.append(f"  nœuds traversés : {trio('noeuds', entier_)} · mots lus : {trio('mots', entier_)} · échecs : {trio('echecs', entier_)}")
            r.stats.append(f"  récompenses : po {trio('po', entier_)} · xp {trio('xp', entier_)}")
        r.stats.append(f"meilleur parcours possible : {self.po_max} po, {self.xp_max} xp (plafond : {PO_CAMPAGNE} po, {XP_CAMPAGNE} xp)")
        issues = {}
        for i in self.fins_graphe:
            issues.setdefault(noeuds[i].get("issue"), []).append(i)
        r.stats.append(f"{len(self.fins_graphe)} fins atteignables : " + " ; ".join(f"{k} ({len(v)})" for k, v in sorted(issues.items(), key=lambda kv: str(kv[0]))))
        for i in self.fins_graphe:
            n = atteintes.get(i, 0)
            r.stats.append(f"  {i} [{noeuds[i].get('issue')}] « {noeuds[i].get('titre', '')} » : {100 * n / max(1, len(finis)):.1f} % des parcours".replace(".", ","))
            if finis and n == 0:
                r.avert(self.fichier[i], i, f"fin jamais atteinte sur {len(finis)} parcours tirés au hasard (conditions impossibles à réunir ?)")
        # Repères : la taille visée d'une vraie campagne (le prologue, lui, est court exprès).
        if finis:
            med = lambda cle: statistics.median(c[cle] for c in finis)
            reperes = [
                ("chapitres", len(self.chapitres), 8, 12), ("nœuds", len(noeuds), 120, 200), ("mots", sum(messages), 12000, 20000),
                ("fins", len(self.fins_graphe), 4, 6), ("choix par parcours (médiane)", med("choix"), 30, 45),
                ("attentes par parcours (médiane)", med("attentes"), 14, 22), ("attentes longues par parcours (médiane)", med("longues"), 3, 5),
            ]
            hors = [f"{nom} : {int(v)} (visé {a} à {b})" for nom, v, a, b in reperes if not a <= v <= b]
            if hors:
                r.note("hors de la taille visée d'une campagne : " + " ; ".join(hors))

    def valider(self):
        if self.lire():
            for i in self.noeuds:
                self.noeud(i)
            self.fins_graphe, self.po_max, self.xp_max = [], 0, 0
            self.graphe()
            self.declarations()
            if not self.r.erreurs:
                self.statistiques()
        return self.r


def campagnes(chemins):
    for chemin in chemins:
        if os.path.isfile(os.path.join(chemin, "campagne.json")):
            yield chemin
        elif os.path.isdir(chemin):
            sous = sorted(d for d in os.listdir(chemin) if os.path.isdir(os.path.join(chemin, d)))
            trouve = False
            for d in sous:
                if os.path.isfile(os.path.join(chemin, d, "campagne.json")):
                    trouve = True
                    yield os.path.join(chemin, d)
                else:
                    print(f"ERREUR  {os.path.join(chemin, d)} : dossier sans campagne.json", file=sys.stderr)
                    yield None
            if not trouve and not sous:
                print(f"ERREUR  {chemin} : aucune campagne", file=sys.stderr)
                yield None
        else:
            print(f"ERREUR  {chemin} : dossier introuvable", file=sys.stderr)
            yield None


def main(argv=None):
    ici = os.path.dirname(os.path.abspath(__file__))
    defaut = os.path.normpath(os.path.join(ici, "..", "..", "assets", "campagnes"))
    p = argparse.ArgumentParser(description="Valide les campagnes de Pilou (docs/CAMPAGNES.md).")
    p.add_argument("chemins", nargs="*", default=[defaut], help="dossier d'une campagne, ou dossier de campagnes (défaut : assets/campagnes)")
    p.add_argument("--parcours", type=int, default=400, help="parcours tirés au hasard pour les statistiques (défaut : 400)")
    p.add_argument("--graine", type=int, default=1, help="graine des parcours (défaut : 1)")
    p.add_argument("--sans-stats", action="store_true", help="ne rend que les erreurs et les avertissements")
    a = p.parse_args(argv)
    erreurs = avertissements = total = 0
    for dossier in campagnes(a.chemins):
        if dossier is None:
            erreurs += 1
            continue
        total += 1
        r = Validateur(dossier, a.parcours, a.graine).valider()
        print(f"== {r.nom} ({os.path.relpath(dossier)}) ==")
        for x in r.erreurs:
            print(f"ERREUR  {x}")
        for x in r.avertissements:
            print(f"AVERT.  {x}")
        if not a.sans_stats:
            for x in r.stats:
                print(f"        {x}")
            for x in r.notes:
                print(f"note    {x}")
        print(f"        → {len(r.erreurs)} erreur(s), {len(r.avertissements)} avertissement(s)")
        print()
        erreurs += len(r.erreurs)
        avertissements += len(r.avertissements)
    print(f"{total} campagne(s) : {erreurs} erreur(s), {avertissements} avertissement(s)")
    return 1 if erreurs else 0


if __name__ == "__main__":
    sys.exit(main())
