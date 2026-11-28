"""Le Théâtre en haute définition (docs/SCENES-HD.md) : la référence de ce que Theatre.cs et Theatre.java calculent
pour une scène HD (480 × 240 unités).

  lire_decor_hd(texte)          assets/decors/decor-<campagne>-<décor>.txt (format compact à plans) → décor
  composer_hd(...)              l'image ARGB de 480 × 240 : plans « fond », acteurs, personnage et Pilou triés par
                                leurs pieds, plans « devant », effets
  convertir_scenes(campagne)    assets/scenes/<campagne>.txt → assets/scenes-hd/<campagne>.txt (repère des paysages :
                                pixel HD = 2,5 x, 2,5 y + 40)

Le Pilou de scène HD est le Pilou fin du bureau (rendu.rendre, grille 96 × 112), posé par theatre.pose_hd. Le moteur
commun (theatre.py) porte les deux définitions : une scène lue avec theatre.HD a ses longueurs × 5/2.

    py outils/sprites/theatre_hd.py          # réécrit assets/scenes-hd/*.txt et outils/sprites/theatre-hd-reference.txt
"""
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import animations  # noqa: E402
import theatre  # noqa: E402
from theatre import ASSETS, fnv  # noqa: E402

PILOU_HD_X, PILOU_HD_Y = 48, 107        # ancre du Pilou fin : colonne du milieu, ligne de ses pieds


# ---- Le décor à plans

def _couleur(c):
    """« #rrggbb » ou « #rrggbbaa » → ARGB."""
    rgb = int(c[1:7], 16)
    a = int(c[7:9], 16) if len(c) >= 9 else 255
    return (a << 24) | rgb


def lire_decor_hd(texte):
    """{id, w, h, plans: [(nom, profondeur, devant, duree, [images : listes à plat de w × h entiers ARGB])]}.
    Même algorithme que decors_hd.decoder (session « paysages ») : « [n]c » une plage, « . » le pixel de l'image
    précédente du même plan, « , » transparent (0). Un fichier sans ligne « plan: » a un seul plan."""
    lignes = [l.rstrip("\r") for l in texte.split("\n")]
    d = {"id": "", "w": 0, "h": 0, "plans": []}
    i, plan = 0, None
    while i < len(lignes):
        l = lignes[i]
        i += 1
        if not l or l.startswith("#"):
            continue
        cle, _, val = l.partition(":")
        val = val.strip()
        if cle == "id":
            d["id"] = val
        elif cle == "ancre":
            d["ancre"] = tuple(int(v) for v in val.split())
        elif cle == "taille":
            d["w"], d["h"] = (int(v) for v in val.split())
        elif cle == "plan":
            nom, prof, couche = val.split()
            plan = [nom, int(prof), couche == "devant", 0, {}, []]
        elif cle in ("duree", "palette") and plan is None:
            plan = ["decor", 0, False, 0, {}, []]
            i -= 1
        elif cle == "duree":
            plan[3] = int(val)
        elif cle == "palette":
            for paire in val.split():
                a, _, b = paire.partition("=")
                plan[4][a] = _couleur(b)
        elif cle == "images":
            w, h = d["w"], d["h"]
            prec = None
            for _ in range(int(val)):
                im = [0] * (w * h)
                for y in range(h):
                    x, k, o = 0, 0, y * w
                    for ch in lignes[i]:
                        if "0" <= ch <= "9":
                            k = k * 10 + ord(ch) - 48
                            continue
                        k = k or 1
                        if ch == ".":
                            im[o + x:o + x + k] = prec[o + x:o + x + k]
                        elif ch != ",":
                            im[o + x:o + x + k] = [plan[4][ch]] * k
                        x += k
                        k = 0
                    assert x == w, "%s : rangée de %d pixels au lieu de %d" % (d["id"], x, w)
                    i += 1
                plan[5].append(im)
                prec = im
            d["plans"].append((plan[0], plan[1], plan[2], plan[3], plan[5]))
            plan = None
    return d


def charger_decor_hd(campagne, decor):
    f = os.path.join(ASSETS, "decors", "decor-%s-%s.txt" % (campagne, decor))
    if not os.path.isfile(f):
        return None
    with open(f, encoding="utf-8") as fh:
        return lire_decor_hd(fh.read())


# ---- Les sprites HD : acteurs et personnages en pied (assets/sprites-hd, docs/SCENES-HD.md § 6 et 7)

class SpriteHd:
    """Un sprite HD : images ARGB à plat (0 : transparent), ancre (x, y) des pieds, durée d'une image."""
    def __init__(self, d):
        self.id, self.w, self.h = d["id"], d["w"], d["h"]
        self.ax, self.ay = d.get("ancre", (d["w"] // 2, d["h"] - 1))
        _, _, _, self.duree, self.images = d["plans"][0]


def lire_sprite_hd(texte):
    return SpriteHd(lire_decor_hd(texte))


def charger_sprites_hd():
    """{id: SpriteHd} de assets/sprites-hd ; renseigne aussi theatre.TAILLES_HD."""
    B = {}
    dossier = os.path.join(ASSETS, "sprites-hd")
    if not os.path.isdir(dossier):
        return B
    for f in sorted(os.listdir(dossier)):
        if f.endswith(".txt"):
            with open(os.path.join(dossier, f), encoding="utf-8") as fh:
                s = lire_sprite_hd(fh.read())
            B[s.id] = s
            theatre.TAILLES_HD[s.id] = (s.w, s.h)
            theatre.DUREES_HD[s.id] = s.duree
    return B


def _poser_hd(px, w, h, s, im, x, y, miroir):
    g = s.images[im % len(s.images)]
    ox = x - (s.w - 1 - s.ax if miroir else s.ax)
    oy = y - s.ay
    for j in range(s.h):
        Y = oy + j
        if Y < 0 or Y >= h:
            continue
        o = j * s.w
        for i in range(s.w):
            c = g[o + i]
            if not c:
                continue
            X = ox + (s.w - 1 - i if miroir else i)
            if 0 <= X < w:
                _melanger(px, Y * w + X, c)


# ---- Les scènes HD

def scenes_hd(campagne):
    f = os.path.join(ASSETS, "scenes-hd", campagne + ".txt")
    if not os.path.isfile(f):
        return {}
    with open(f, encoding="utf-8") as fh:
        return theatre.lire_scenes(fh.read(), theatre.HD)


def _x(v):
    return v * 5 // 2


def _y(v):
    return v * 5 // 2 + 40


def _l(v):
    return v * 5 // 2


# Paramètres de chaque comportement : quoi est une abscisse (x), une ordonnée (y), une longueur ou une vitesse (l), ou
# reste tel quel (=).
_PARAMS = {"vol": "xyxy=", "traverse": "yy==l", "rond": "xy==", "saut": "xy==", "pose": "xy", "flotte": "xy==ll",
           "chute": "xy=="}
_REACTIONS = {"bulle": "xy", "rond": "", "graines": "xy"}


def _conv(vals, motif):
    out = []
    for i, v in enumerate(vals):
        c = motif[i] if i < len(motif) else "="
        out.append(_x(v) if c == "x" else _y(v) if c == "y" else _l(v) if c == "l" else v)
    return out


# Ajustements après conversion, quand le tableau HD le demande : {(campagne, décor): {champ: valeur}}. Un champ
# (place, interlocuteur…) remplace la valeur convertie ; « sensible:<nom> » remplace cette ligne entière ; « + » ajoute
# des lignes à la fin de la scène (les bêtes que les paysages HD ne peignent plus : elles deviennent des acteurs, posés
# aux coordonnées données par la session « paysages »).
AJUSTEMENTS = {
    ("prologue", "mare"): {
        "place": 80,                                # loin du tronc du grand arbre, à gauche
        "sensible:grenouille": "sensible grenouille 228 176 252 197 bulle 240 186",
        "acteur:libellule": "acteur libellule vol 150 105 400 150 7",   # au-dessus des roseaux, jamais posée sur l'eau
        "+": ["acteur grenouille pose 240 195",       # sur le nénuphar du milieu
              "acteur canard pose 190 180"],          # sur l'eau libre
    },
    ("prologue", "jardin"): {"+": ["acteur escargot pose 235 200"]},          # sur la grande feuille
    ("grande-panne", "marais-majs"): {"+": ["acteur canard pose 355 200"]},
    ("phare-eteint", "guet-de-nuit"): {"cle": "240 50 300 145"},              # le phare vu par la fenêtre, pas toute la fenêtre
    ("petit-nuage", "etang-qui-fume"): {
        "+": ["acteur grenouille pose 195 228"],                              # sur la berge
        "sensible:grenouille": "sensible grenouille 183 210 207 229 bulle 195 219",
    },
}


def convertir_scenes(campagne):
    """assets/scenes/<campagne>.txt → assets/scenes-hd/<campagne>.txt, dans le repère des paysages HD (x × 2,5,
    y × 2,5 + 40 ; longueurs et vitesses × 2,5). Les commentaires d'en-tête sont remplacés par celui-ci."""
    with open(os.path.join(ASSETS, "scenes", campagne + ".txt"), encoding="utf-8") as fh:
        texte = fh.read()
    out = ["# Scènes HD de « %s » (docs/SCENES-HD.md) : écrites par outils/sprites/theatre_hd.py depuis" % campagne,
           "# assets/scenes/%s.txt, dans le repère des paysages (x × 2,5 ; y × 2,5 + 40). Ne pas modifier à la main :" % campagne,
           "# corriger la scène d'origine, ou le tableau."]
    nom = ""

    def finir():
        aj = AJUSTEMENTS.get((campagne, nom), {})
        while out and out[-1] == "":
            out.pop()
        out.extend(aj.get("+", []))
        # Une réaction demandée qui n'existait pas dans la scène d'origine.
        for k, v in aj.items():
            if k.startswith(("sensible:", "acteur:")) and v not in out:
                out.append(v)
        out.append("")

    for brut in texte.splitlines():
        l = brut.split("#", 1)[0].strip()
        if not l:
            if out[-1] != "":
                out.append("")
            continue
        m = l.split()
        if m[0] == "scene":
            if nom:
                finir()
            nom = m[1]
        aj = AJUSTEMENTS.get((campagne, nom), {})
        if m[0] == "sensible" and "sensible:" + m[1] in aj:
            out.append(aj["sensible:" + m[1]])
        elif m[0] == "acteur" and "acteur:" + m[1] in aj:
            out.append(aj["acteur:" + m[1]])
        elif m[0] in aj:
            out.append("%s %s" % (m[0], aj[m[0]]))
        elif m[0] == "sol" or m[0] == "cle":
            v = [int(x) for x in m[1:5]]
            out.append("%s %d %d %d %d" % (m[0], _x(v[0]), _y(v[1]), _x(v[2]), _y(v[3])))
        elif m[0] in ("place", "interlocuteur"):
            out.append("%s %d" % (m[0], _x(int(m[1]))))
        elif m[0] == "acteur":
            p = _conv([int(x) for x in m[3:]], _PARAMS.get(m[2], ""))
            out.append("acteur %s %s %s" % (m[1], m[2], " ".join(str(v) for v in p)))
        elif m[0] == "sensible":
            v = [int(x) for x in m[2:6]]
            p = _conv([int(x) for x in m[7:]], _REACTIONS.get(m[6], ""))
            out.append("sensible %s %d %d %d %d %s%s" % (m[1], _x(v[0]), _y(v[1]), _x(v[2]), _y(v[3]), m[6],
                                                        "".join(" %d" % x for x in p)))
        else:
            out.append(l)
    if nom:
        finir()
    os.makedirs(os.path.join(ASSETS, "scenes-hd"), exist_ok=True)
    with open(os.path.join(ASSETS, "scenes-hd", campagne + ".txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out).rstrip("\n") + "\n")


# ---- Le Pilou fin du bureau, rendu pour la scène

def rendeur_pilou(base=None):
    """Une fonction pose → grille 96 × 112 d'entiers ARGB (0 : vide), par rendu.rendre à l'échelle 2. base : les
    champs propres au joueur (stade, couleur, accessoire…) ; par défaut, le Pilou de démonstration (stade 2, bleu)."""
    import rendu
    B, T, TEN = rendu.banque(), rendu.teintes(), rendu.tenues()
    cache = {}

    def f(pose):
        kw = dict(base or {})
        kw.update(pose)
        cle = tuple(sorted(kw.items()))
        if cle not in cache:
            g = rendu.rendre(rendu.Pose(**kw), B, T, TEN, 2)
            cache[cle] = [[0 if c is None else _couleur(c) for c in row] for row in g]
        return cache[cle]
    return f


# ---- Le compositeur HD

def _melanger(px, k, c):
    a = (c >> 24) & 255
    if a == 0:
        return
    if a == 255:
        px[k] = c
        return
    d = px[k]
    r = (((c >> 16) & 255) * a + ((d >> 16) & 255) * (255 - a) + 127) // 255
    v = (((c >> 8) & 255) * a + ((d >> 8) & 255) * (255 - a) + 127) // 255
    b = ((c & 255) * a + (d & 255) * (255 - a) + 127) // 255
    px[k] = 0xFF000000 | (r << 16) | (v << 8) | b


def _calque(px, im):
    for k, c in enumerate(im):
        if c:
            _melanger(px, k, c)


def _poser_grille(px, w, h, g, x, y, ax, ay):
    gh, gw = len(g), len(g[0])
    ox, oy = x - ax, y - ay
    for j in range(gh):
        Y = oy + j
        if Y < 0 or Y >= h:
            continue
        row = g[j]
        for i in range(gw):
            c = row[i]
            X = ox + i
            if c and 0 <= X < w:
                _melanger(px, Y * w + X, c)


def composer_hd(decor, sc, A, B, evts, t, rendre, regard=0, niv=animations.COMPLETES):
    """L'image HD de la scène à l'instant t : liste de 480 × 240 entiers ARGB. B : les sprites HD des acteurs et des
    personnages, {id: SpriteHd} (ceux qui manquent ne sont pas dessinés : jamais d'ancien sprite agrandi,
    docs/SCENES-HD.md § 2). Un personnage HD est dessiné regardant à droite : il est retourné pour regarder Pilou."""
    w, h = sc.d.w, sc.d.h
    px = [0xFF000000] * (w * h)
    devant = []
    for (_, _, dev, duree, ims) in (decor["plans"] if decor else []):
        im = ims[animations.image_decor(len(ims), duree, t, niv)]
        if dev:
            devant.append(im)
        else:
            _calque(px, im)
    poses = [(y, 0, ("s", sid, im, x, m)) for (sid, im, x, y, m) in theatre.acteurs(sc, A, B, evts, t, niv)]
    pp = theatre.perso(sc, A, evts, t, niv)
    if pp is not None and pp[0] in B:
        poses.append((pp[3], 0, ("s", pp[0], pp[1], pp[2], not pp[4])))
    etat = theatre.pilou_etat(sc, A, evts, t, regard, niv)
    if etat[5]:
        poses.append((etat[1], 1, ("p", etat)))
    poses.sort(key=lambda q: (q[0], q[1]))
    for (y, _, q) in poses:
        if q[0] == "p":
            _poser_grille(px, w, h, rendre(theatre.pose_hd(q[1], t)), q[1][0], y, PILOU_HD_X, PILOU_HD_Y)
        else:
            _, sid, im, x, m = q
            _poser_hd(px, w, h, B[sid], im, x, y, m)
    for im in devant:
        _calque(px, im)
    for (sid, im, x, y, m) in theatre.effets(sc, A, B, evts, t, niv):
        _poser_hd(px, w, h, B[sid], im, x, y, m)
    return px


# ---- La référence

SCENARIOS_HD = [
    ("mare-hd", "prologue", "mare", "completes", 0,
     [(0, "entree", 0, 0), (2600, "humeur", "joie", 0), (3000, "parle", 4200, 0), (5000, "clic", 75 * 5 // 2, 70 * 5 // 2 + 40),
      (6000, "humeur", "surpris", 0), (7000, "depart", 1, 0)],
     [0, 1000, 2600, 3100, 3240, 5100, 5400, 6100, 8000, 12000]),
    ("seuil-hd-reduites", "prologue", "seuil", "reduites", 0, [(0, "entree", 0, 0)], [0, 4150, 4299]),
    ("mare-hd-clics", "prologue", "mare", "completes", 0,
     [(0, "entree", 0, 0), (4000, "clic", 240, 175), (5200, "clic", 150, 215), (5600, "clic", 160, 214), (6000, "clic", 170, 216)],
     [4100, 4400, 5000, 5300, 5800, 6100, 6400, 7000]),
    ("hall-hd-perso", "grande-panne", "hall-pas-comptes", "completes", 0,
     [(0, "entree", 0, 0), (800, "perso", "pied-grande-panne-raccourcis", 0), (3500, "parle-perso", 5600, 0),
      (6500, "clic", 370, 200)],
     [800, 2000, 3600, 3740, 6550, 6700, 9000]),
]


def ecrire_reference():
    _, A = theatre.charger()
    B = charger_sprites_hd()
    rendre = rendeur_pilou()
    lignes = ["# Théâtre HD : valeurs de référence (outils/sprites/theatre_hd.py), relues par TheatreTests.cs et",
              "# TheatreTest.java. decor id plan largeur hauteur images duree empreintes… ; scenario nom campagne décor",
              "# niveau regard ; evenement t sorte a b ; pilou t x y animation dt miroir visible humeur ; pose t champs ;",
              "# image t empreinte."]
    for f in sorted(os.listdir(os.path.join(ASSETS, "decors"))):
        if not f.endswith(".txt"):
            continue
        with open(os.path.join(ASSETS, "decors", f), encoding="utf-8") as fh:
            d = lire_decor_hd(fh.read())
        for (nom, prof, dev, duree, ims) in d["plans"]:
            lignes.append("decor %s %s %d %d %d %d %s" % (d["id"], nom, d["w"], d["h"], len(ims), duree,
                                                         " ".join(str(fnv(im)) for im in ims)))
    for (nom, camp, dec, niv, regard, evts, instants) in SCENARIOS_HD:
        sc = scenes_hd(camp)[dec]
        decor = charger_decor_hd(camp, dec)
        lignes.append("scenario %s %s %s %s %d" % (nom, camp, dec, niv, regard))
        for e in evts:
            lignes.append(theatre._evt(e))
        for t in instants:
            et = theatre.pilou_etat(sc, A, evts, t, regard, niv)
            lignes.append("pilou %d %d %d %s %d %d %d %s" % (t, et[0], et[1], et[2], et[3], int(et[4]), int(et[5]), et[6]))
            pose = theatre.pose_hd(et, t)
            lignes.append("pose %d %s" % (t, " ".join("%s=%s" % (k, _texte(v)) for k, v in sorted(pose.items()))))
            for (s, i, ax, ay, am) in theatre.acteurs(sc, A, B, evts, t, niv) + theatre.effets(sc, A, B, evts, t, niv):
                lignes.append("acteur %d %s %d %d %d %d" % (t, s, i, ax, ay, int(am)))
            pp = theatre.perso(sc, A, evts, t, niv)
            if pp is not None:
                lignes.append("perso %d %s %d %d %d %d" % (t, pp[0], pp[1], pp[2], pp[3], int(pp[4])))
            px = composer_hd(decor, sc, A, B, evts, t, rendre, regard, niv)
            lignes.append("image %d %d" % (t, fnv(px)))
    with open(os.path.join(ICI, "theatre-hd-reference.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lignes) + "\n")
    return len(lignes)


def _texte(v):
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, float):
        return repr(v)
    return str(v)


def campagnes_hd():
    """Les campagnes qui ont au moins un décor HD et une fiche de scènes : on convertit leurs scènes."""
    ids = set()
    for f in os.listdir(os.path.join(ASSETS, "decors")):
        for c in os.listdir(os.path.join(ASSETS, "scenes")):
            c = c[:-4]
            if f.startswith("decor-" + c + "-") and c != "animations":
                ids.add(c)
    return sorted(ids)


if __name__ == "__main__":
    for c in campagnes_hd():
        convertir_scenes(c)
    print(ecrire_reference(), "lignes dans theatre-hd-reference.txt")
