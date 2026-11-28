"""Vie du personnage : les règles communes au PC et au téléphone (référence ; docs/SPRITES.md, « Vie du personnage »).

Pilou a l'air plus vivant sans devenir plus actif : il ne bouge pas plus souvent, il bouge mieux.

  bond(d, vol, haut, niveau)         un saut : (hauteur, étirement, antenne) en millièmes, d ms après le début.
                                     Complètes : il se ramasse (PREP), décolle étiré, retombe en arc (parabole :
                                     ralenti en haut, accéléré en bas), s'écrase et rebondit sur un ressort amorti
                                     (RECEPTION), l'antenne suit avec RETARD_ANTENNE de retard. Réduites : l'arc seul.
  duree_bond(vol, niveau)            durée totale d'un bond
  sautille(d, periode, haut, niveau) petits bonds répétés (la fête) : même arc, petit écrasement à chaque appui
  reception(d, niveau)               le ressort seul (Pilou lâché qui retombe) : (étirement, antenne)
  lumiere(heure, etat, niveau)       la lumière du moment sur Pilou : « matin », « soir », « nuit » ou "" ; par temps
                                     couvert, ni aube dorée ni couchant (la nuit reste)
  eclairer(couleur, moment)          une couleur de la teinte de Pilou, mêlée à la lumière du moment
  bouffee(t, cadence, sens)          image (0 à 2, −1 : rien) de la bouffée de poussière du pied arrière en marchant
  bouffee_atterrissage(d)            image des deux bouffées qui s'écartent à l'atterrissage

Niveau « aucune » (réglage ✧ ou animations coupées par le système) : rien de tout cela ; les appelants gardent les
mouvements d'avant (arc en sinus, écrasement linéaire), sans lumière ni poussière.

Arithmétique entière seulement (divisions arrondies vers le bas, comme // en Python) : mêmes valeurs partout.
`reference.py` écrit `outils/sprites/vie-reference.txt` ; `VieTests.cs` et `VieTest.java` le relisent ligne à ligne.
Le dessin (étirement du corps, antenne, ombre tramée, poussière, lumière) est dans rendu.py, RenduPilou.cs et
RenduPilou.java, vérifié par rendus-reference.txt.
"""
import os

COMPLETES, REDUITES, AUCUNE = "completes", "reduites", "aucune"
NIVEAUX = (COMPLETES, REDUITES, AUCUNE)

PREP = 70            # ms : il se ramasse avant de décoller
RECEPTION = 280      # ms : ressort amorti à l'atterrissage
RETARD_ANTENNE = 60  # ms : l'antenne suit le corps avec ce retard
ETIRE_VOL = 350      # millièmes : étirement au décollage et juste avant de toucher le sol
# Courbes en points clés (ms, millièmes ; négatif : écrasé, positif : étiré), reliés en ligne droite.
PREP_CLES = ((0, 0), (40, -450), (70, -200))
RECEPTION_CLES = ((0, -600), (50, -700), (120, 260), (190, -100), (250, 30), (280, 0))
APPUI_CLES = ((0, -500), (60, 200))       # petits bonds : écrasé à l'appui, puis il repousse
APPUI = 60
ETIRE_SAUTILLE = 220

COUVERT = ("nuageux", "pluie", "averse", "orage", "neige", "brouillard")
# Lumière du moment : (couleur vers laquelle on mêle, part en centièmes). Jamais rouge / vert : crème, violet du crépuscule, bleu nuit.
LUMIERES = {
    "matin": ("#ffd8b0", 10),
    "soir": ("#b98ad9", 16),
    "nuit": ("#1d2448", 18),
}

BOUFFEE_IMAGE = 80   # ms par image de poussière (trois images)


def cles(table, d):
    """Valeur de la courbe à d ms (entiers, division vers le bas)."""
    if d <= table[0][0]:
        return table[0][1]
    for (t0, v0), (t1, v1) in zip(table, table[1:]):
        if d < t1:
            return v0 + (v1 - v0) * (d - t0) // (t1 - t0)
    return table[-1][1]


def _etire_bond(d, vol):
    """Étirement d'un bond complet à d ms (avant le début et après la fin : 0)."""
    if d < 0:
        return 0
    if d < PREP:
        return cles(PREP_CLES, d)
    k = d - PREP
    if k < vol:
        return ETIRE_VOL * abs(vol - 2 * k) // vol
    r = k - vol
    if r < RECEPTION:
        return cles(RECEPTION_CLES, r)
    return 0


def _antenne(etire_avant):
    """L'antenne suit le corps en retard, à contre-sens : le corps s'écrase, elle file encore vers le bas, puis
    rebondit. Valeur en millièmes (positif : pointe plus haute)."""
    return -etire_avant * 8 // 10


def bond(d, vol, haut, niv):
    if niv == AUCUNE or d < 0 or vol <= 0:
        return 0, 0, 0
    if niv != COMPLETES:
        if d >= vol:
            return 0, 0, 0
        return haut * 4 * d * (vol - d) // (vol * vol), 0, 0
    k = d - PREP
    saut = haut * 4 * k * (vol - k) // (vol * vol) if 0 <= k < vol else 0
    return saut, _etire_bond(d, vol), _antenne(_etire_bond(d - RETARD_ANTENNE, vol))


def duree_bond(vol, niv):
    if niv == AUCUNE:
        return 0
    return PREP + vol + RECEPTION + RETARD_ANTENNE if niv == COMPLETES else vol


def _etire_sautille(d, periode):
    k = d % periode
    if k < APPUI:
        return cles(APPUI_CLES, k)
    return ETIRE_SAUTILLE * abs(periode - 2 * k) // periode


def sautille(d, periode, haut, niv):
    if niv == AUCUNE or d < 0 or periode <= 0:
        return 0, 0, 0
    k = d % periode
    saut = haut * 4 * k * (periode - k) // (periode * periode)
    if niv != COMPLETES:
        return saut, 0, 0
    return saut, _etire_sautille(d, periode), _antenne(_etire_sautille(d - RETARD_ANTENNE, periode))


def _etire_reception(d):
    return cles(RECEPTION_CLES, d) if 0 <= d < RECEPTION else 0


def reception(d, niv):
    if niv != COMPLETES or d < 0 or d >= RECEPTION + RETARD_ANTENNE:
        return 0, 0
    return _etire_reception(d), _antenne(_etire_reception(d - RETARD_ANTENNE))


def lumiere(heure, etat, niv):
    if niv == AUCUNE:
        return ""
    h = heure % 24
    if 6 <= h < 9:
        m = "matin"
    elif 17 <= h < 21:
        m = "soir"
    elif h >= 21 or h < 6:
        m = "nuit"
    else:
        return ""
    if m != "nuit" and etat in COUVERT:
        return ""
    return m


def eclairer(couleur, moment):
    """couleur « #rrggbb » ; même mélange que animations._melange (entiers, vers le bas)."""
    if moment not in LUMIERES:
        return couleur
    vers, cent = LUMIERES[moment]
    a = [int(couleur[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(vers[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(x + (y - x) * cent // 100 for x, y in zip(a, b))


def bouffee(t, cadence, sens):
    """Image de la bouffée du pied arrière (−1 : aucune). Le pied levé est (t // cadence) % 2 (rendu.py) ; le pied
    arrière (0, à gauche, quand il va à droite) se pose quand l'autre se lève : une bouffée tous les deux pas."""
    if cadence <= 0:
        return -1
    arriere = 0 if sens >= 0 else 1
    age = (t - cadence * (1 - arriere)) % (2 * cadence)
    return age // BOUFFEE_IMAGE if age < 3 * BOUFFEE_IMAGE else -1


def bouffee_atterrissage(d):
    return d // BOUFFEE_IMAGE if 0 <= d < 3 * BOUFFEE_IMAGE else -1


# Bouffées, en pixels de la grille 1× (un pixel de la grille fine en fait 2 × 2) : (recul, hauteur, opaque ?) depuis
# le talon, au ras du sol ; le recul va vers l'arrière (bouffée de marche) ou vers l'extérieur (atterrissage).
POUSSIERE, POUSSIERE_LEGERE = "#b5a690c0", "#b5a69078"
BOUFFEES = (((0, 0, True), (1, 0, False)), ((1, -1, True), (2, 0, False)), ((2, -1, False),))
BOUFFEES_ATTERRISSAGE = (((0, 0, True),), ((1, 0, True), (1, -1, False)), ((2, -1, False),))


# ---------------------------------------------------------------------------------------------------------------------
# Fichier de référence
# ---------------------------------------------------------------------------------------------------------------------
def reference():
    l = ["# Vie du personnage : valeurs de référence (outils/sprites/vie.py, écrites par reference.py).",
         "# Relues par VieTests.cs (PC) et VieTest.java (téléphone)."]
    ds = (-5, 0, 20, 40, 69, 70, 100, 200, 330, 589, 590, 600, 640, 700, 760, 869, 870, 930, 2000)
    for niv in NIVEAUX:
        for vol, haut in ((520, 2000), (340, 1500), (520, 3000)):
            l.append("duree %s %d %d" % (niv, vol, duree_bond(vol, niv)))
            for d in ds:
                l.append("bond %s %d %d %d %d %d %d" % ((niv, vol, haut, d) + bond(d, vol, haut, niv)))
        for d in (-1, 0, 30, 59, 60, 61, 225, 449, 450, 470, 900, 1349, 12345):
            l.append("sautille %s 450 3000 %d %d %d %d" % ((niv, d) + sautille(d, 450, 3000, niv)))
        for d in (-1, 0, 25, 50, 85, 120, 190, 250, 279, 280, 300, 339, 340):
            l.append("reception %s %d %d %d" % ((niv, d) + reception(d, niv)))
        for h in (0, 5, 6, 8, 9, 12, 16, 17, 20, 21, 23, 24, 30):
            for etat in ("", "degage", "nuageux", "pluie", "neige", "chaleur"):
                l.append("lumiere %d %s %s %s" % (h, etat or "-", niv, lumiere(h, etat, niv) or "-"))
    for m in ("matin", "soir", "nuit", "jour"):
        for c in ("#1f4f8a", "#4a8fdc", "#6cb6ff", "#b4dbff", "#000000", "#ffffff"):
            l.append("eclaire %s %s %s" % (m, c, eclairer(c, m)))
    for cad in (160, 70):
        for sens in (1, -1):
            l.append("bouffee %d %d %s" % (cad, sens, " ".join(str(bouffee(t, cad, sens)) for t in range(0, 700, 10))))
    l.append("atterrissage %s" % " ".join(str(bouffee_atterrissage(d)) for d in range(-20, 300, 10)))
    return "\n".join(l) + "\n"


CHEMIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vie-reference.txt")


def ecrire_reference():
    with open(CHEMIN, "w", encoding="utf-8", newline="\n") as f:
        f.write(reference())


if __name__ == "__main__":
    ecrire_reference()
