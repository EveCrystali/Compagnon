"""Les scènes d'évolution (docs/SCENES.md, « Scènes d'évolution ») : lecteur de référence de assets/evolutions.txt.

Evolutions.cs (PC) et Evolutions.java (Android) en sont la traduction exacte : mêmes scènes, mêmes répliques dans le
même ordre pour une variante et un choix donnés, même temps d'écriture. Le fichier evolutions-reference.txt, écrit
ici, est rejoué par les tests des deux côtés.

    py outils/sprites/evolutions.py         # réécrit outils/sprites/evolutions-reference.txt
"""
import os

ICI = os.path.dirname(os.path.abspath(__file__))
FICHIER = os.path.normpath(os.path.join(ICI, "..", "..", "assets", "evolutions.txt"))
REFERENCE = os.path.join(ICI, "evolutions-reference.txt")

VARIANTES = ("calin", "espiegle")
MS_LETTRE = 30          # Pilou écrit une lettre toutes les 30 ms (il parle pendant ce temps-là)
MS_MIN, MS_MAX = 900, 7000


class Scene:
    def __init__(self, stade):
        self.stade = stade
        self.titre = ""
        self.decor = ""
        self.musique = ""           # morceau de assets/musiques.txt (vide : la boucle du ton « émotion »)
        self.question = ""
        self.options = []            # [(id, libellé)]
        self.elements = []           # [(sorte, cle, humeur, texte)] : sorte pilou | calin | espiegle | choix | apres


def lire(texte):
    """{stade: Scene} ; une ligne inconnue est ignorée (un fichier plus récent reste lisible)."""
    scenes = {}
    sc = None
    for brute in texte.splitlines():
        ligne = brute.strip()
        if not ligne or ligne.startswith("#"):
            continue
        mot, _, reste = ligne.partition(" ")
        if mot == "scene":
            sc = Scene(int(reste))
            scenes[sc.stade] = sc
        elif sc is None:
            continue
        elif mot == "titre":
            sc.titre = reste
        elif mot == "decor":
            sc.decor = reste
        elif mot == "musique":
            sc.musique = reste
        elif mot in ("pilou", "calin", "espiegle"):
            humeur, _, t = reste.partition(" ")
            sc.elements.append((mot, "", humeur, t))
        elif mot == "choix":
            sc.question = reste
            sc.elements.append(("choix", "", "", reste))
        elif mot == "option":
            oid, _, lib = reste.partition(" ")
            sc.options.append((oid, lib))
        elif mot == "apres":
            oid, _, r = reste.partition(" ")
            humeur, _, t = r.partition(" ")
            sc.elements.append(("apres", oid, humeur, t))
    return scenes


def variante(v):
    """La variante du stade (Soins.Variante) ; inconnue ou absente : câline."""
    return v if v in VARIANTES else "calin"


def deroule(sc, var, choix):
    """Les répliques dites, dans l'ordre : [(humeur, texte)]. choix None : jusqu'à la question (incluse, sans
    humeur) ; sinon, toute la scène avec la réplique de ce choix."""
    var = variante(var)
    out = []
    for (sorte, cle, humeur, t) in sc.elements:
        if sorte == "pilou" or sorte == var:
            out.append((humeur, t))
        elif sorte == "choix":
            if choix is None:
                out.append(("", t))
                return out
        elif sorte == "apres" and cle == choix:
            out.append((humeur, t))
    return out


def ms_ecriture(texte):
    """Le temps que Pilou met à écrire une réplique (et à la dire dans la scène)."""
    return max(MS_MIN, min(MS_MAX, MS_LETTRE * len(texte)))


def charger():
    with open(FICHIER, encoding="utf-8") as fh:
        return lire(fh.read())


def ecrire_reference():
    scenes = charger()
    lignes = ["# Référence des scènes d'évolution (outils/sprites/evolutions.py) : rejouée par EvolutionsTests.cs et",
              "# EvolutionsTest.java. Ne pas modifier à la main."]
    for stade in sorted(scenes):
        sc = scenes[stade]
        lignes.append("scene %d %s | %s | %s | %s" % (stade, sc.decor, sc.titre, sc.question, sc.musique or "-"))
        for (oid, lib) in sc.options:
            lignes.append("option %s %s" % (oid, lib))
        for var in VARIANTES + ("autre",):
            for choix in [None] + [o for o, _ in sc.options]:
                d = deroule(sc, var, choix)
                lignes.append("deroule %d %s %s %d" % (stade, var, choix or "-", len(d)))
                for (h, t) in d:
                    lignes.append("  %s %d %s" % (h or "-", ms_ecriture(t), t))
    with open(REFERENCE, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lignes) + "\n")
    return len(lignes)


if __name__ == "__main__":
    print(ecrire_reference(), "lignes dans", os.path.basename(REFERENCE))
