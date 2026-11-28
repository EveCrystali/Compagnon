"""Animations des campagnes : les règles communes au PC et au téléphone (référence ; docs/SPRITES.md, « Animations des
campagnes »).

Tout ce que les deux appareils doivent calculer de la même façon est ici, en arithmétique simple (pas de sinus : les
bibliothèques ne tombent pas toujours sur le même dernier chiffre) :

  niveau(reglage, systeme)                le niveau effectif : « completes », « reduites » ou « aucune ». Le réglage du
                                          joueur (bouton « ✧ ») décide ; tant qu'il n'a rien choisi (réglage vide), le
                                          système donne la valeur de départ : « aucune » s'il demande moins d'animations
                                          (Windows : animations coupées ; Android : échelle des animations à 0), sinon
                                          « completes » (décidé avec Antoine le 28 novembre 2026)
  image_decor(n, duree, t, niveau)        l'image d'un décor animé à l'instant t (ms) ; image 0 si réduites ou aucune
  image_portrait(n, duree, t, parle, niveau)
                                          l'image d'un portrait de personnage (disposition fixe : 0 et 1 repos, la
                                          respiration ; 2 yeux fermés ; 3 et 4 bouche mi-ouverte, ouverte)
  cligne(t)                               Pilou (ou un personnage) a-t-il les yeux fermés à l'instant t ?
  lettres(texte, ms)                      combien de lettres d'un message sont écrites après ms (rythme : une lettre,
                                          une petite pause aux virgules, une plus longue aux points ; un long message
                                          ne dure jamais plus de DUREE_MAX)
  duree_ecriture(texte), attente(texte)   durée de l'écriture lettre à lettre, et des « … » qui la précèdent
  ordre_volet(bx, by, nbx)                ordre d'apparition d'un bloc du volet pixelisé (transition entre décors)
  teintes_fond(ton, heure)                trois couleurs du fond animé (haut, bas, particules) selon le ton et l'heure
  particule_fond(ton, i, t)               position (dix-millièmes de la largeur / hauteur) et opacité d'une particule
  delai_recompense(i)                     quand la i-ème récompense tombe sur l'écran de fin

`reference.py` écrit `outils/sprites/animations-reference.txt` d'après ces fonctions ; `AnimationsCampagneTests.cs`
et `AnimationsTest.java` le relisent ligne à ligne.
"""
import os

COMPLETES, REDUITES, AUCUNE = "completes", "reduites", "aucune"
NIVEAUX = (COMPLETES, REDUITES, AUCUNE)

# Portraits : respiration, clignement, parole (ms).
RESPIRATION = 900
CLIGNE_PERIODE = 4300
CLIGNE_DUREE = 150
PAS_PAROLE = 140
PAROLE = (3, 4, 3, 0)

# Écriture lettre à lettre (ms).
PAR_LETTRE = 22
PAUSE_POINT = 230
PAUSE_VIRGULE = 90
DUREE_MAX = 5200
TRANSITION = 360          # fondu ou volet entre deux décors
VOLET_BLOC = 8            # un bloc du volet : 8 pixels de la grille 1× du décor (12 × 5 blocs)


def niveau(reglage, systeme):
    if reglage in NIVEAUX:
        return reglage
    return COMPLETES if systeme else AUCUNE


def image_decor(n, duree, t, niv):
    if niv != COMPLETES or n <= 1 or duree <= 0 or t < 0:
        return 0
    return (t // duree) % n


def cligne(t):
    return t >= 0 and t % CLIGNE_PERIODE >= CLIGNE_PERIODE - CLIGNE_DUREE


def image_portrait(n, duree, t, parle, niv):
    if n <= 1 or niv == AUCUNE or t < 0:
        return 0
    if n > 2 and cligne(t):
        return 2
    if niv != COMPLETES:
        return 0
    if parle and n >= 5:
        return PAROLE[(t // PAS_PAROLE) % len(PAROLE)]
    return (t // RESPIRATION) % 2


def _cout(ch):
    if ch in ".!?…":
        return PAR_LETTRE + PAUSE_POINT
    if ch in ",;:":
        return PAR_LETTRE + PAUSE_VIRGULE
    return PAR_LETTRE


def _brut(texte):
    return sum(_cout(c) for c in texte)


def duree_ecriture(texte):
    return min(_brut(texte), DUREE_MAX)


def lettres(texte, ms):
    """Lettres écrites après ms. Les durées sont en millièmes de milliseconde (entiers) : même résultat partout."""
    if ms <= 0:
        return 0
    brut = _brut(texte)
    if brut <= 0:
        return len(texte)
    total = min(brut, DUREE_MAX)
    # Chaque lettre coûte cout × total / brut ; on compare en entiers : somme(cout) × total ≤ ms × brut.
    lim = ms * brut
    acc = 0
    for i, ch in enumerate(texte):
        acc += _cout(ch) * total
        if acc > lim:
            return i
    return len(texte)


def attente(texte):
    return max(600, min(1500, 450 + 3 * len(texte)))


BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))


def ordre_volet(bx, by, nbx):
    """Ordre d'apparition d'un bloc, en dix-millièmes (0 : le premier) : la trame ordonnée, poussée de gauche à
    droite. Un bloc est montré quand ordre < progression × 10000."""
    trame = (BAYER[by % 4][bx % 4] * 2 + 1) * 10000 // 32
    balaye = bx * 10000 // max(1, nbx - 1)
    return (trame * 6 + balaye * 4) // 10


# Fond animé : couleurs par ton (jamais rouge / vert), assombries ou dorées selon l'heure.
FONDS = {
    "humour": ("#1c2448", "#3a3263", "#ffc89a"),
    "mystere": ("#0b1022", "#1d2448", "#a9bbd8"),
    "emotion": ("#1d2240", "#4a3f66", "#f2c6d6"),
    "epique": ("#071a33", "#173d66", "#ffd29a"),
}
MOMENTS = {  # (mélange vers, part en centièmes) appliqué aux deux couleurs du fond
    "matin": ("#f6c89a", 12),
    "jour": ("#9fb4de", 8),
    "soir": ("#d9803a", 14),
    "nuit": ("#05070f", 30),
}


def moment(heure):
    if 6 <= heure < 11:
        return "matin"
    if 11 <= heure < 17:
        return "jour"
    if 17 <= heure < 21:
        return "soir"
    return "nuit"


def _rvb(c):
    return int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)


def _melange(a, b, cent):
    ra, va, ba = _rvb(a)
    rb, vb, bb = _rvb(b)
    return "#%02x%02x%02x" % tuple(x + (y - x) * cent // 100 for x, y in ((ra, rb), (va, vb), (ba, bb)))


def teintes_fond(ton, heure):
    haut, bas, part = FONDS.get(ton, ("#151a2e", "#2d333b", "#adbac7"))
    vers, cent = MOMENTS[moment(heure)]
    return _melange(haut, vers, cent), _melange(bas, vers, cent), part


def hasard(i, j, graine=0):
    """Le même bruit entier que peinture.hasard, en dix-millièmes (0 à 9999)."""
    n = (i * 374761393 + j * 668265263 + graine * 2246822519) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) * 10000 // 65536


NB_PARTICULES = 14
# Par ton : (vie d'une particule en ms, déplacement sur sa vie en dix-millièmes : dx, dy ; balancement)
MOUVEMENTS = {
    "humour": (16000, 600, -3200, 250),     # bulles qui montent en se balançant
    "mystere": (22000, 2600, -300, 120),    # poussière de brume qui dérive de côté
    "emotion": (19000, -500, 2800, 300),    # flocons, pétales qui descendent lentement
    "epique": (14000, 900, -2400, 150),     # braises qui montent
}


def particule_fond(ton, i, t):
    """(x, y, opacité 0–255) d'une particule du fond : elle naît, traverse lentement, s'efface (cycle de vie)."""
    vie, dx, dy, bal = MOUVEMENTS.get(ton, MOUVEMENTS["mystere"])
    decal = hasard(i, 1, 17) * vie // 10000
    u = (t + decal) % vie * 10000 // vie                    # 0..9999 : l'âge
    x = hasard(i, 2, 17) + dx * u // 10000
    y = hasard(i, 3, 17) + dy * u // 10000
    tri = u * 4 % 20000                                      # balancement en triangle (deux allers-retours par vie)
    tri = tri if tri < 10000 else 20000 - tri
    x += bal * (tri - 5000) // 5000
    x %= 10000
    y %= 10000
    a = min(u, 10000 - u) * 255 * 3 // 10000                 # apparaît et s'efface sur un tiers de sa vie
    a = min(a, 150)
    return x, y, a


def delai_recompense(i):
    return 420 + 260 * i


# ---------------------------------------------------------------------------------------------------------------------
# Fichier de référence
# ---------------------------------------------------------------------------------------------------------------------
TEXTES = [
    "Coucou !",
    "On est devant la vitre. Mlle Renvoi lève les yeux et dit : « Bonjour*. » Je te jure que j'ai entendu l'astérisque.",
    "Il pleut, il pleut, il pleut… et moi, je suis une goutte d'encre ; tu vois le problème ?",
    "x" * 400,
    "",
]


def reference():
    l = ["# Animations des campagnes : valeurs de référence (outils/sprites/animations.py, écrites par reference.py).",
         "# Relues par AnimationsCampagneTests.cs (PC) et AnimationsTest.java (téléphone)."]
    for r in NIVEAUX + ("inconnu",):
        for sy in (1, 0):
            l.append("niveau %s %d %s" % (r, sy, niveau(r, sy == 1)))
    for (n, d) in ((1, 0), (6, 240), (8, 200), (2, 500)):
        for t in (0, 239, 240, 1199, 1440, 99999, -5):
            for niv in NIVEAUX:
                l.append("decor %d %d %d %s %d" % (n, d, t, niv, image_decor(n, d, t, niv)))
    for n in (1, 3, 5):
        for t in (0, 140, 280, 899, 900, 4149, 4150, 4299, 4300, 8599, 12345):
            for parle in (0, 1):
                for niv in NIVEAUX:
                    l.append("portrait %d 150 %d %d %s %d" % (n, t, parle, niv, image_portrait(n, 150, t, parle == 1, niv)))
    for i, x in enumerate(TEXTES):
        l.append("texte %d %s" % (i, x))
    for i, x in enumerate(TEXTES):
        l.append("ecriture %d %d %d" % (i, duree_ecriture(x), attente(x)))
        for ms in (0, 1, 21, 22, 23, 300, 1000, 2500, 5199, 5200, 9000):
            l.append("lettres %d %d %d" % (i, ms, lettres(x, ms)))
    for by in range(5):
        l.append("volet %d %s" % (by, " ".join(str(ordre_volet(bx, by, 12)) for bx in range(12))))
    for ton in ("humour", "mystere", "emotion", "epique", "autre"):
        for h in (0, 7, 12, 18, 23):
            l.append("fond %s %d %s" % (ton, h, " ".join(teintes_fond(ton, h))))
        for i in range(NB_PARTICULES):
            for t in (0, 5000, 123456):
                l.append("particule %s %d %d %d %d %d" % ((ton, i, t) + particule_fond(ton, i, t)))
    l.append("recompense %s" % " ".join(str(delai_recompense(i)) for i in range(5)))
    return "\n".join(l) + "\n"


CHEMIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "animations-reference.txt")


def ecrire_reference():
    with open(CHEMIN, "w", encoding="utf-8", newline="\n") as f:
        f.write(reference())


if __name__ == "__main__":
    ecrire_reference()
