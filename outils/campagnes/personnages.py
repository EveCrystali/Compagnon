#!/usr/bin/env python3
"""Pose (ou propose) les champs « personnage » et « expression » des nœuds d'une campagne (docs/CAMPAGNES.md).

    python3 outils/campagnes/personnages.py                 rapport : ce qui serait posé, nœud par nœud
    python3 outils/campagnes/personnages.py --ecrire        l'écrit dans les fichiers de chapitre

Un personnage n'apparaît que lorsque le texte le fait parler ou le décrit : on cherche son nom dans les messages du
nœud (le premier nommé l'emporte, le compagnon de route seulement s'il est seul). L'expression vient de quelques mots
du texte (« sourit », « tremble », « grogne »…), si ce personnage a cette expression dessinée.

L'écriture est minimale : une ligne ajoutée après la ligne « humeur » (ou « type ») du nœud ; aucun texte, aucun
libellé n'est touché, et un nœud qui a déjà « personnage » est laissé tel quel (les auteurs peuvent corriger à la main).
"""
import json
import os
import re
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.normpath(os.path.join(ICI, "..", ".."))
sys.path.insert(0, os.path.join(RACINE, "outils", "sprites"))

# Les noms qui désignent chaque personnage dans les textes (expressions régulières, insensibles à la casse sauf mention).
NOMS = {
    "grande-panne": [
        ("brouillon", r"Brouillon|Sans-Titre"), ("tic-tac", r"Tic-Tac"), ("balayeur", r"Balayeur"),
        ("mlle-renvoi", r"Mlle Renvoi"), ("le-rond", r"\ble Rond\b|\bLe Rond\b"), ("golem", r"golem"),
        ("spectre-404", r"spectre|Quatre-Cent-Quatre"), ("dateur", r"Dateur"), ("mme-echeance", r"Échéance|Planificatrice"),
        ("imprimante", r"Imprimante"), ("touche-s", r"petite S\b|touche S\b|: S\.|S se cache|S tremble|« S »"),
        ("raccourcis", r"\bCtrl\b|\bAlt\b|\bSuppr\b|Raccourcis"), ("grumeau", r"Grumeau"),
    ],
    "phare-eteint": [
        ("lison", r"Lison"), ("basile", r"Basile"), ("tudal", r"Tudal"), ("perrine", r"Perrine"), ("odile", r"Odile"),
        ("vernier", r"Vernier"), ("anselme", r"Anselme"),
    ],
    "petit-nuage": [
        ("tournebise", r"Tournebise"), ("ondee", r"Ondée"), ("mi-bemol", r"Mi-Bémol"), ("dentelle", r"Dentelle"),
        ("madame-bocal", r"Madame Bocal|Mme Bocal"), ("froisseuses", r"Froisseuses"), ("enclumes", r"Enclumes"),
        ("bergeronnette", r"bergeronnette"), ("brouillon", r"Brouillon"),
    ],
}
# Verbes qui disent qu'un personnage est là (juste après son nom).
PRESENT = (r"\b(dit|répond|demande|murmure|souffle|soupire|grogne|crie|chuchote|lève|hoche|sourit|rit|regarde|"
           r"me regarde|tremble|recule|s'approche|arrive|apparaît|se tourne|baisse|tend|pose|ouvre|ferme|attend|"
           r"est là|nous|me fixe|cligne|hausse|secoue|rougit|pâlit|s'assoit|s'est|a dit|a répondu|m'a)\b")
# Ceux qu'on ne rencontre qu'à partir d'un chapitre (avant, on ne fait qu'en parler).
DEPUIS = {("grande-panne", "tic-tac"): 8, ("grande-panne", "brouillon"): 8, ("phare-eteint", "anselme"): 7,
          ("phare-eteint", "lison"): 5}
# Compagnons de route : montrés seulement quand aucun autre personnage n'est nommé.
COMPAGNONS = {"grumeau", "brouillon"}
MOTS = [
    ("triste", r"pleur|larme|sanglot|triste|chagrin|renifl"),
    ("peur", r"trembl|peur|terrifi|effray|recule|se cache"),
    ("colere", r"furieu|fâch|colère|grogn|rouspét|bougonn|peste "),
    ("surpris", r"sursaut|surpris|stupéf|écarquill|bouche bée"),
    ("joie", r"sourit|sourire|rit |rire|éclate de rire|ravi|content|rayonn|pouffe"),
    ("tendre", r"doucement|tendre|merci|serre contre|câlin|blotti"),
    ("malice", r"clin d'œil|malice|malicieu|sourire en coin|espiègle"),
]


def dessinees():
    import portraits_campagnes as P
    r = {}
    for (c, p), (nom, desc, exprs, f, coupe) in P.PERSOS.items():
        r[(c, p)] = set(exprs)
    return r


def choisir(campagne, noeud, exprs, chapitre=99):
    texte = " ".join(noeud.get("texte", []))
    if not texte:
        return None, ""
    trouves = []
    for pid, motif in NOMS.get(campagne, []):
        if (campagne, pid) not in exprs or chapitre < DEPUIS.get((campagne, pid), 0):
            continue
        for m in re.finditer(motif, texte):
            # Présent dans la scène : il parle (une réplique « … » tout près) ou il agit sous nos yeux.
            autour = texte[max(0, m.start() - 90):m.end() + 140]
            if "«" in autour or re.search(PRESENT, texte[m.end():m.end() + 70]):
                trouves.append((m.start(), pid))
                break
    if not trouves:
        return None, ""
    autres = sorted(x for x in trouves if x[1] not in COMPAGNONS)
    pos, pid = autres[0] if autres else sorted(trouves)[0]
    # L'expression : les mots qui suivent le nom (une phrase ou deux).
    fenetre = texte[pos:pos + 220].lower()
    for ex, motif in MOTS:
        if ex in exprs[(campagne, pid)] and re.search(motif, fenetre):
            return pid, ex
    return pid, ""


def traiter(dossier, ecrire):
    campagne = os.path.basename(os.path.normpath(dossier))
    exprs = dessinees()
    with open(os.path.join(dossier, "campagne.json"), encoding="utf-8") as fh:
        fiche = json.load(fh)
    total = poses = 0
    for ch in fiche["chapitres"]:
        chemin = os.path.join(dossier, ch["fichier"])
        with open(chemin, encoding="utf-8") as fh:
            brut = fh.read()
        data = json.loads(brut)
        lignes = brut.split("\n")
        ajouts = []
        for nid, n in data["noeuds"].items():
            total += 1
            if "personnage" in n:
                continue
            m = re.match(r"ch(\d+)", data.get("chapitre", ""))
            pid, ex = choisir(campagne, n, exprs, int(m.group(1)) if m else 99)
            if not pid:
                continue
            poses += 1
            print("%-14s %-28s %-14s %s" % (campagne, nid, pid, ex))
            # La ligne du nœud, puis sa ligne « humeur » (ou « type ») avant le nœud suivant.
            debut = next(i for i, l in enumerate(lignes) if l.strip().startswith('"%s": {' % nid))
            ind = re.match(r"\s*", lignes[debut]).group(0) + "  "
            cible = None
            for i in range(debut + 1, len(lignes)):
                l = lignes[i]
                if l.startswith(ind + '"humeur"'):
                    cible = i
                    break
                if re.match(r"\s*\"[a-z0-9-]+\": \{\s*$", l) and not l.startswith(ind + " "):
                    break
            if cible is None:
                cible = next(i for i in range(debut + 1, len(lignes)) if lignes[i].startswith(ind + '"type"'))
            champ = ind + '"personnage": "%s",' % pid
            if ex:
                champ += ' "expression": "%s",' % ex
            ajouts.append((cible, champ))
        if ecrire and ajouts:
            for cible, champ in sorted(ajouts, reverse=True):
                lignes.insert(cible + 1, champ)
            nouveau = "\n".join(lignes)
            json.loads(nouveau)   # toujours du JSON valide
            with open(chemin, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(nouveau)
    print("%s : %d nœuds, %d avec un personnage" % (campagne, total, poses), file=sys.stderr)


def main():
    ecrire = "--ecrire" in sys.argv
    base = os.path.join(RACINE, "assets", "campagnes")
    for c in sorted(os.listdir(base)):
        if os.path.isfile(os.path.join(base, c, "campagne.json")):
            traiter(os.path.join(base, c), ecrire)


if __name__ == "__main__":
    main()
