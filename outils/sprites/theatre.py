"""Le théâtre des campagnes (docs/SCENES.md) : la scène vivante de la fenêtre Aventure, en référence.

Un décor fin (192 × 80) où vivent le mini-Pilou (scene_pilou.py), des acteurs d'ambiance (acteurs_scenes.py) et,
plus tard, les personnages en pied. Tout ce que le PC (Theatre.cs) et le téléphone (Theatre.java) doivent calculer
de la même façon est ici, en arithmétique entière (pas de sinus de bibliothèque : des tables) :

  lire_scenes(texte)                   assets/scenes/<campagne>.txt → {décor: Scene}
  lire_animations(texte)               assets/scenes/animations.txt → {sprite: {nom: (première, nombre, pas, mode)}}
  pilou(sc, A, evts, t, regard, niv)   (x, y, image, miroir, visible) du mini-Pilou à l'instant t
  acteurs(sc, B, evts, t, niv)         ce qui est posé dans la scène : [(sprite, image, x, y, miroir), …] (pieds en y)
  effets(sc, evts, t, niv)             les effets de réaction (éclats, notes, ronds, ploufs) au-dessus de tout
  composer(...)                        l'image ARGB de 192 × 80 : décor, puis acteurs et Pilou triés par leurs pieds,
                                       puis les effets ; mélange alpha entier
  fnv(pixels)                          empreinte d'une image (FNV-1a 32 bits) pour comparer PC, téléphone et référence

Les événements (`evts`) sont des tuples (t, sorte, a, b), triés par t : « entree » (a : x de départ, 0 : le bord
gauche), « depart » (a : +1 droite, -1 gauche), « humeur » (a : humeur du message), « parle » (a : fin de la réplique
de Pilou ; une nouvelle réplique remplace la précédente, a = t la coupe), « perso » (a : sprite du personnage en pied,
"" : plus personne), « parle-perso » (a : fin de sa réplique), « clic » (a, b : point touché en pixels du décor). Ce qui dépend de la souris en continu (le regard) est un paramètre, pas un événement.

`python3 outils/sprites/theatre.py` écrit assets/scenes/animations.txt et outils/sprites/theatre-reference.txt
(relu par TheatreTests.cs et TheatreTest.java).
"""
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(ICI, "..", "..", "assets"))
sys.path.insert(0, ICI)

import animations  # noqa: E402

W, H = 192, 80
PAS = 83                       # douze images par seconde, « en deux » comme un dessin animé
VITESSE = 24                   # marche de Pilou, pixels fins par seconde
ENTREE, SORTIE_D, SORTIE_G = -14, 206, -14
PILOU = "scene-pilou"
PILOU_X, PILOU_Y = 17, 33      # ancre du sprite : centre, ligne des pieds
REGARD_CYCLE = 7000            # toutes les sept secondes, peut-être, il regarde ailleurs
REGARD_DEBUT, REGARD_DUREE = 3000, 1200
VOL_CYCLE, VOL_POSE = 1700, 1190
FUITE_VOL, FUITE_ABSENT = 1500, 6000
CLICS_MAX = 24                 # au-delà, les plus anciens clics sont oubliés (la scène ne garde pas tout)

# sin(2πi/32) × 1000, arrondi : la même table partout.
SINUS = [0, 195, 383, 556, 707, 831, 924, 981, 1000, 981, 924, 831, 707, 556, 383, 195,
         0, -195, -383, -556, -707, -831, -924, -981, -1000, -981, -924, -831, -707, -556, -383, -195]
# Lissage (« smoothstep ») en millièmes, pour i = 0..16 sur 16.
LISSE = [0, 11, 42, 89, 156, 229, 316, 410, 500, 590, 684, 771, 844, 911, 958, 989, 1000]

# Rythme (ms par image) et taille (largeur, hauteur) des sprites, remplis par charger() depuis la banque.
DUREES = {}
TAILLES = {}

# Le personnage en pied (pieds_campagnes.py) : il entre par la droite, se tient sur `interlocuteur`, respire, cligne,
# parle pendant sa réplique, sautille quand on le touche (et de temps en temps), et ressort par la droite.
VITESSE_PERSO = 48             # pixels fins par seconde
ENTREE_PERSO = W + 18
SAUT_PERSO = (0, -2, -4, -5, -4, -2, 0)   # le petit saut, une hauteur par pas de 83 ms
PERSO_CYCLE, PERSO_SAUT = 8000, 5000

HUMEURS = ("joie", "peur", "triste", "surpris", "determine", "fatigue", "tendre", "colere", "malice", "neutre")


def div(a, b):
    """Division entière tronquée vers zéro (comme C# et Java)."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def lisse(num, den):
    """Lissage entre 0 et 1000 de num/den (0 ≤ num ≤ den), par la table."""
    if den <= 0 or num >= den:
        return 1000
    if num <= 0:
        return 0
    return LISSE[num * 16 // den]


# ---- Les scènes : assets/scenes/<campagne>.txt

class Scene:
    def __init__(self, nom):
        self.nom = nom
        self.sol = (0, 78, W, 78)
        self.place = 24
        self.interlocuteur = 150
        self.acteurs = []          # (sprite, comportement, [paramètres entiers])
        self.sensibles = []        # (nom, x0, y0, x1, y1, réaction, [paramètres entiers])


def lire_scenes(texte):
    scenes, sc = {}, None
    for brut in texte.splitlines():
        l = brut.split("#", 1)[0].strip()
        if not l:
            continue
        m = l.split()
        if m[0] == "scene":
            sc = scenes[m[1]] = Scene(m[1])
        elif sc is None:
            continue
        elif m[0] == "sol":
            sc.sol = tuple(int(v) for v in m[1:5])
        elif m[0] == "place":
            sc.place = int(m[1])
        elif m[0] == "interlocuteur":
            sc.interlocuteur = int(m[1])
        elif m[0] == "acteur":
            sc.acteurs.append(("acteur-" + m[1], m[2], [int(v) for v in m[3:]]))
        elif m[0] == "sensible":
            sc.sensibles.append((m[1], int(m[2]), int(m[3]), int(m[4]), int(m[5]), m[6], [int(v) for v in m[7:]]))
    return scenes


def sol(sc, x):
    x0, y0, x1, y1 = sc.sol
    if x <= x0 or x1 == x0:
        return y0
    if x >= x1:
        return y1
    return y0 + div((y1 - y0) * (x - x0), x1 - x0)


# ---- Les animations nommées : assets/scenes/animations.txt

def lire_animations(texte):
    A = {}
    for brut in texte.splitlines():
        l = brut.split("#", 1)[0].strip()
        if not l:
            continue
        m = l.split()
        A.setdefault(m[0], {})[m[1]] = (int(m[2]), int(m[3]), int(m[4]), m[5])
    return A


def image_anim(a, dt):
    premiere, n, pas, mode = a
    if dt < 0:
        dt = 0
    k = dt // pas
    return premiere + (k % n if mode == "boucle" else min(k, n - 1))


def duree_anim(a):
    return a[1] * a[2]


# ---- Le mini-Pilou

def _face(humeur):
    return "repos" if humeur in ("", "neutre") or humeur not in HUMEURS else "repos-" + humeur


def _clics(evts):
    """Index des clics gardés (les CLICS_MAX derniers)."""
    c = [i for i, e in enumerate(evts) if e[1] == "clic"]
    return c[-CLICS_MAX:]


def pilou(sc, A, evts, t, regard=0, niv=animations.COMPLETES):
    """(x, y, image, miroir, visible) : x au centre, y la ligne des pieds."""
    P = A[PILOU]
    vif = niv == animations.COMPLETES
    x, humeur, action, parti = sc.place, "neutre", None, False
    paroles = []
    if not vif:
        for e in evts:
            if e[0] <= t and e[1] == "humeur":
                humeur = e[2]
        a = P[_face(humeur)]
        im = a[0]
        if niv == animations.REDUITES and animations.cligne(t):
            im = P["cligne"][0]
        return x, sol(sc, x), im, x > W // 2, True

    def fin_action(act, jusque):
        """Applique la fin d'une action terminée avant `jusque` ; rend (x, action restante, parti)."""
        nonlocal x, parti
        if act is None:
            return None
        if act[0] == "marche":
            _, t0, x0, x1 = act
            fait = (jusque - t0) * VITESSE // 1000
            if fait >= abs(x1 - x0):
                x = x1
                parti = x1 >= SORTIE_D or x1 <= SORTIE_G
                return None
            return act
        if act[0] == "anim":
            _, t0, nom, d = act
            return act if jusque - t0 < d else None
        return act

    def position(act, jusque):
        if act is not None and act[0] == "marche":
            _, t0, x0, x1 = act
            fait = (jusque - t0) * VITESSE // 1000
            return x0 + fait if x1 >= x0 else x0 - fait
        return x

    clics_vus = set(_clics(evts))
    n_pilou = 0
    for ie, e in enumerate(evts):
        if e[0] > t:
            break
        action = fin_action(action, e[0])
        sorte = e[1]
        if sorte == "entree":
            x0 = e[2] if e[2] else ENTREE          # a : d'où il entre (0 : du bord gauche)
            x, parti = x0, False
            action = ("marche", e[0], x0, sc.place)
        elif sorte == "depart":
            x = position(action, e[0])
            action = ("marche", e[0], x, SORTIE_D if e[2] >= 0 else SORTIE_G)
        elif sorte == "humeur":
            humeur = e[2] if e[2] in HUMEURS else "neutre"
            if action is None or action[0] == "anim":
                if humeur in ("joie", "surpris"):
                    action = ("anim", e[0], humeur, duree_anim(P[humeur]))
        elif sorte == "parle":
            paroles = [(e[0], e[2])]                # une nouvelle réplique remplace la précédente (a = t : coupée)
        elif sorte == "clic" and ie in clics_vus:
            if parti or (action is not None and action[0] == "marche"):
                continue
            cible = cible_clic(sc, A, evts, ie)
            if cible[0] == "pilou":
                nom = ("joie", "coucou")[n_pilou % 2]
                n_pilou += 1
                action = ("anim", e[0], nom, duree_anim(P[nom]))
            elif cible[0] == "sensible" and cible[2] == "bulle":
                action = ("anim", e[0], "surpris", duree_anim(P["surpris"]) + 1200)
            elif cible[0] in ("sensible", "acteur", "perso"):
                nom = "regard-d" if cible[3] >= x else "regard-g"
                action = ("anim", e[0], nom, 900)
    action = fin_action(action, t)
    if parti:
        return x, sol(sc, x), P[_face(humeur)][0], False, False
    if action is not None and action[0] == "marche":
        _, t0, x0, x1 = action
        px = position(action, t)
        return px, sol(sc, px), image_anim(P["marche"], t - t0), x1 < x0, True
    miroir = x > W // 2
    if action is not None and action[0] == "anim":
        _, t0, nom, d = action
        if nom == "surpris" and t - t0 >= duree_anim(P["surpris"]):
            return x, sol(sc, x), image_anim(P["repos-peur"], t - t0), miroir, True
        if nom in ("regard-d", "regard-g"):
            return x, sol(sc, x), P[nom][0], False, True
        return x, sol(sc, x), image_anim(P[nom], t - t0), miroir, True
    for (t0, t1) in paroles:
        if t0 <= t < t1:
            return x, sol(sc, x), image_anim(P["parle"], t - t0), miroir, True
    if animations.cligne(t):
        return x, sol(sc, x), P["cligne"][0], miroir, True
    if regard:
        return x, sol(sc, x), P["regard-d" if regard > 0 else "regard-g"][0], False, True
    c = t // REGARD_CYCLE
    u = t % REGARD_CYCLE
    if animations.hasard(c, 11, 3) < 4000 and REGARD_DEBUT <= u < REGARD_DEBUT + REGARD_DUREE:
        nom = "regard-g" if animations.hasard(c, 12, 3) < 5000 else "regard-d"
        return x, sol(sc, x), P[nom][0], False, True
    return x, sol(sc, x), image_anim(P[_face(humeur)], t), miroir, True


# ---- Le personnage en pied

def _x_entree(sc, t_in, t):
    return max(sc.interlocuteur, ENTREE_PERSO - (t - t_in) * VITESSE_PERSO // 1000)


def _etat_perso(sc, evts, t):
    """(sprite courant, depuis quand, sortie (sprite, quand, x) de celui qui s'en va, répliques)."""
    cur, t_in, sortie, paroles = "", 0, None, []
    for e in evts:
        if e[0] > t:
            break
        if e[1] == "perso":
            sid = e[2] or ""
            if sid == cur:
                continue
            # Remplacé par un autre : il s'efface ; plus personne : il ressort en marchant.
            sortie = (cur, e[0], _x_entree(sc, t_in, e[0])) if cur and not sid else None
            cur, t_in, paroles = sid, e[0], []
        elif e[1] == "parle-perso":
            paroles = [(e[0], e[2])]
    return cur, t_in, sortie, paroles


def perso(sc, A, evts, t, niv=animations.COMPLETES):
    """(sprite, image, x, y, miroir) du personnage en pied, ou None. Il regarde vers la place de Pilou."""
    cur, t_in, sortie, paroles = _etat_perso(sc, evts, t)
    miroir = sc.place > sc.interlocuteur
    if niv != animations.COMPLETES:
        if not cur or cur not in A:
            return None
        a = A[cur]
        im = a["cligne"][0] if niv == animations.REDUITES and animations.cligne(t + 1700) and "cligne" in a else a["repos"][0]
        return cur, im, sc.interlocuteur, sol(sc, sc.interlocuteur), miroir
    if not cur:
        if sortie is None or sortie[0] not in A:
            return None
        sid, t_out, x_out = sortie
        x = x_out + (t - t_out) * VITESSE_PERSO // 1000
        if x > W + 30:
            return None
        k = (t // 166) % 2
        return sid, image_anim(A[sid]["repos"], t), x, sol(sc, min(x, W)) - k, False
    if cur not in A:
        return None
    a = A[cur]
    x = _x_entree(sc, t_in, t)
    y = sol(sc, x)
    if x > sc.interlocuteur:
        k = (t // 166) % 2                 # il trottine : un pixel de haut une image sur deux
        return cur, image_anim(a["repos"], t), x, y - k, miroir
    # Un saut quand on le touche, ou de temps en temps.
    saut = -1
    for k in _clics(evts):
        tc = evts[k][0]
        if t_in <= tc <= t and t - tc < len(SAUT_PERSO) * PAS and cible_clic(sc, A, evts, k)[0] == "perso":
            saut = (t - tc) // PAS
    c, u = t // PERSO_CYCLE, t % PERSO_CYCLE
    if saut < 0 and t - t_in > PERSO_CYCLE and animations.hasard(c, 21, 7) < 3000 and PERSO_SAUT <= u < PERSO_SAUT + len(SAUT_PERSO) * PAS:
        saut = (u - PERSO_SAUT) // PAS
    if saut >= 0:
        return cur, a["repos"][0], x, y + SAUT_PERSO[saut], miroir
    for (t0, t1) in paroles:
        if t0 <= t < t1 and "parle" in a:
            return cur, image_anim(a["parle"], t - t0), x, y, miroir
    if "cligne" in a and animations.cligne(t + 1700):
        return cur, a["cligne"][0], x, y, miroir
    return cur, image_anim(a["repos"], t), x, y, miroir


# ---- Les acteurs

def _fuites(sc, A, evts, i, t):
    """Instants où l'acteur i a été touché (jusqu'à t)."""
    return [evts[k][0] for k in _clics(evts) if evts[k][0] <= t and cible_clic(sc, A, evts, k)[:2] == ("acteur", i)]


def _vol(p, t):
    x0, y0, x1, y1, g = p
    c, u = t // VOL_CYCLE, t % VOL_CYCLE
    ax = x0 + animations.hasard(c, 1, g) * (x1 - x0) // 10000
    ay = y0 + animations.hasard(c, 2, g) * (y1 - y0) // 10000
    bx = x0 + animations.hasard(c + 1, 1, g) * (x1 - x0) // 10000
    by = y0 + animations.hasard(c + 1, 2, g) * (y1 - y0) // 10000
    f = 0 if u < VOL_POSE else lisse(u - VOL_POSE, VOL_CYCLE - VOL_POSE)
    x = ax + div((bx - ax) * f, 1000)
    y = ay + div((by - ay) * f, 1000) + div(SINUS[(t // 140) % 32], 700)
    return x, y, bx < ax


def position_acteur(sc, A, evts, i, t, duree=100):
    """(x, y, image ou -1 si l'acteur est absent, miroir) ; x au centre, y la ligne du bas. duree : celle du sprite
    (les acteurs qui ne font que boucler suivent son rythme)."""
    duree = max(1, duree)
    sid, comp, p = sc.acteurs[i]
    fuites = _fuites(sc, A, evts, i, t) if comp in ("vol", "traverse") else []
    if comp == "vol":
        for tf in reversed(fuites):
            if t < tf + FUITE_ABSENT:
                if t >= tf + FUITE_VOL:
                    return 0, 0, -1, False
                fx, fy, _ = _vol(p, tf)
                d = 1 if fx < W // 2 else -1
                return fx - d * ((t - tf) * 90 // 1000), fy - (t - tf) * 30 // 1000, t // duree, d > 0
        x, y, m = _vol(p, t)
        return x, y, t // duree, m
    if comp == "traverse":
        y0, y1, periode, decalage, vitesse = p
        tt = t + decalage
        c, u = tt // periode, tt % periode
        x = -12 + u * vitesse // 1000
        y = y0 + animations.hasard(c, 3, 5) * (y1 - y0) // 10000 + div(SINUS[(t // 160) % 32], 800)
        for tf in fuites:
            if (tf + decalage) // periode == c:
                x += (t - tf) * 60 // 1000
                y -= (t - tf) * 25 // 1000
        if x > W + 12 or y < -8:
            return 0, 0, -1, False
        return x, y, t // duree, False
    if comp == "rond":
        x, y, periode, decalage = p
        u = (t + decalage) % periode
        if u >= 5 * 280:
            return 0, 0, -1, False
        return x, y, u // 280, False
    if comp == "saut":
        x, y, periode, decalage = p
        u = (t + decalage) % periode
        if u >= 700:
            return 0, 0, -1, False
        f = u * 1000 // 700
        arc = 12 * 4 * f * (1000 - f) // 1000000
        return x + 20 * f // 1000, y - arc, 0 if f < 400 else 1 if f < 600 else 2, False
    if comp == "pose":
        x, y = p[0], p[1]
        return x, y, t // duree, False
    if comp == "flotte":
        x, y, periode, decalage, vx, vy = p
        u = (t + decalage) % periode
        px = x + div(u * vx, 1000) + div(SINUS[(u // 200) % 32] * 2, 1000)
        py = y + div(u * vy, 1000)
        if px < -8 or px > W + 8 or py < -8 or py > H + 8:
            return 0, 0, -1, False
        return px, py, t // duree, False
    if comp == "chute":
        x, y, periode, decalage = p
        u = (t + decalage) % periode
        py = y + u * 14 // 1000
        px = x + div(SINUS[(u // 150) % 32] * 4, 1000)
        if py > H + 4:
            return 0, 0, -1, False
        return px, py, u // duree, False
    return 0, 0, -1, False


def _boite(B, sid):
    s = B.get(sid)
    return (s.w, s.h) if s is not None else (6, 6)


_MEMO = {}


def cible_clic(sc, A, evts, k):
    """Ce que touche le clic evts[k] : ("pilou", 0, "", x), ("acteur", i, "", 0), ("sensible", j, réaction, x) ou
    ("rien", 0, "", 0). Le clic ne voit que les événements qui le précèdent."""
    cle = (id(sc), k, tuple(evts[:k + 1]))
    if cle in _MEMO:
        return _MEMO[cle]
    tc, _, cx, cy = evts[k]
    avant = evts[:k]
    r = _cible(sc, A, avant, tc, cx, cy)
    _MEMO[cle] = r
    return r


def _cible(sc, A, avant, tc, cx, cy):
    px, py, _, _, vis = pilou(sc, A, avant, tc)
    if vis and abs(cx - px) <= 10 and py - 22 <= cy <= py + 1:
        return ("pilou", 0, "", px)
    pp = perso(sc, A, avant, tc)
    if pp is not None:
        w, h = TAILLES.get(pp[0], (24, 32))
        if abs(cx - pp[2]) <= w // 2 and pp[3] - h < cy <= pp[3]:
            return ("perso", 0, "", pp[2])
    for i, (sid, comp, p) in enumerate(sc.acteurs):
        if comp not in ("vol", "traverse"):
            continue
        ax, ay, im, _ = position_acteur(sc, A, avant, i, tc, DUREES.get(sid, 100))
        if im >= 0 and abs(cx - ax) <= 6 and ay - 7 <= cy <= ay + 2:
            return ("acteur", i, "", 0)
    for j, (nom, x0, y0, x1, y1, reaction, p) in enumerate(sc.sensibles):
        if x0 <= cx <= x1 and y0 <= cy <= y1:
            return ("sensible", j, reaction, cx)
    return ("rien", 0, "", 0)


def acteurs(sc, A, B, evts, t, niv=animations.COMPLETES):
    """[(sprite, image, x, y, miroir)] des acteurs présents (x au centre, y le bas), sans Pilou ni les effets."""
    if niv != animations.COMPLETES:
        return []
    out = []
    for i, (sid, comp, p) in enumerate(sc.acteurs):
        x, y, im, m = position_acteur(sc, A, evts, i, t, DUREES.get(sid, 100))
        if im < 0 or sid not in B:
            continue
        out.append((sid, im % len(B[sid].images), x, y, m))
    return out


def effets(sc, A, B, evts, t, niv=animations.COMPLETES):
    """Les effets de réaction en cours, au-dessus de tout : [(sprite, image, x, y, miroir)]."""
    if niv != animations.COMPLETES:
        return []
    out = []
    ronds = {}
    for k in _clics(evts):
        e = evts[k]
        tc = e[0]
        if tc > t:
            break
        dt = t - tc
        cible = cible_clic(sc, A, evts, k)
        if cible[0] == "pilou" and dt < 350:
            px, py, _, _, _ = pilou(sc, A, evts[:k], tc)
            out.append(("acteur-eclats", dt // 70, px, py - 24, False))
        elif cible[0] == "sensible":
            j, reaction = cible[1], cible[2]
            pr = sc.sensibles[j][6]
            if reaction == "bulle" and dt < 1050:
                out.append(("acteur-bulle", (0, 1, 2, 1, 2, 3, 0)[dt // 150], pr[0], pr[1], False))
            if reaction == "bulle" and dt < 1100:
                out.append(("acteur-note", (t // 180) % 2, pr[0] + 5, pr[1] - 5 - dt * 10 // 1000, False))
            if reaction == "rond":
                ronds[j] = ronds.get(j, 0) + 1
                if dt < 1400:
                    out.append(("acteur-rond", dt // 280, e[2], e[3] + 2, False))
                if ronds[j] % 3 == 0 and dt < 700:
                    f = dt * 1000 // 700
                    arc = 12 * 4 * f * (1000 - f) // 1000000
                    out.append(("acteur-poisson", 0 if f < 400 else 1 if f < 600 else 2, e[2] + 20 * f // 1000, e[3] - arc, False))
                    if dt < 360:
                        out.append(("acteur-plouf", dt // 90, e[2], e[3], False))
                if ronds[j] % 3 == 0 and 700 <= dt < 1060:
                    out.append(("acteur-plouf", (dt - 700) // 90, e[2] + 20, e[3], False))
            if reaction == "graines" and dt < 4000:
                for k in range(5):
                    vx = -8 - k * 3
                    vy = -6 + k * 2
                    gx = pr[0] + div(dt * vx, 1000) + div(SINUS[(dt // 200 + k * 5) % 32] * 2, 1000)
                    gy = pr[1] + div(dt * vy, 1000)
                    out.append(("acteur-graine", (t // 300 + k) % 2, gx, gy, False))
    return [o for o in out if o[0] in B]


# ---- Le compositeur

def _argb(c, teinte):
    if c.startswith("@"):
        c = teinte[("@contour", "@ombre", "@base", "@clair").index(c)]
    r, v, b = int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)
    a = int(c[7:9], 16) if len(c) >= 9 else 255
    return a, r, v, b


def poser(px, B, sid, im, x, y, miroir, teinte, ancre_x=None, ancre_y=None):
    """Pose l'image im du sprite sid : (x, y) est le point d'ancrage (par défaut le milieu du bas)."""
    s = B.get(sid)
    if s is None or not s.images:
        return
    g = s.images[im % len(s.images)]
    w, h = s.w, s.h
    ax = w // 2 if ancre_x is None else ancre_x
    ay = h - 1 if ancre_y is None else ancre_y
    ox, oy = x - (w - 1 - ax if miroir else ax), y - ay
    cache = {}
    for j, ligne in enumerate(g):
        Y = oy + j
        if Y < 0 or Y >= H:
            continue
        for i, ch in enumerate(ligne):
            if ch == ".":
                continue
            X = ox + (w - 1 - i if miroir else i)
            if X < 0 or X >= W:
                continue
            if ch not in cache:
                cache[ch] = _argb(s.palette[ch], teinte)
            a, r, v, b = cache[ch]
            if a == 0:
                continue
            k = Y * W + X
            if a == 255:
                px[k] = 0xFF000000 | (r << 16) | (v << 8) | b
            else:
                d = px[k]
                dr, dv, db = (d >> 16) & 255, (d >> 8) & 255, d & 255
                r2 = (r * a + dr * (255 - a) + 127) // 255
                v2 = (v * a + dv * (255 - a) + 127) // 255
                b2 = (b * a + db * (255 - a) + 127) // 255
                px[k] = 0xFF000000 | (r2 << 16) | (v2 << 8) | b2


def composer(B, teinte, decor, sc, A, evts, t, regard=0, niv=animations.COMPLETES):
    """L'image de la scène à l'instant t : liste de W × H entiers ARGB."""
    px = [0xFF000000] * (W * H)
    if decor is not None:
        k = animations.image_decor(len(decor.images), decor.duree, t, niv)
        B2 = {"_decor": decor}
        poser(px, B2, "_decor", k, 0, 0, False, teinte, 0, 0)
    poses = [(y, 0, sid, im, x, m) for (sid, im, x, y, m) in acteurs(sc, A, B, evts, t, niv)]
    pp = perso(sc, A, evts, t, niv)
    if pp is not None and pp[0] in B:
        poses.append((pp[3], 0, pp[0], pp[1], pp[2], pp[4]))
    x, y, im, m, vis = pilou(sc, A, evts, t, regard, niv)
    if vis:
        poses.append((y, 1, PILOU, im, x, m))
    poses.sort(key=lambda q: (q[0], q[1]))
    for (y, _, sid, im, x, m) in poses:
        if sid == PILOU:
            poser(px, B, sid, im, x, y, m, teinte, PILOU_X, PILOU_Y)
        else:
            poser(px, B, sid, im, x, y, m, teinte)
    for (sid, im, x, y, m) in effets(sc, A, B, evts, t, niv):
        poser(px, B, sid, im, x, y, m, teinte)
    return px


def fnv(px):
    h = 0x811C9DC5
    for v in px:
        for s in (0, 8, 16, 24):
            h ^= (v >> s) & 255
            h = (h * 0x01000193) & 0xFFFFFFFF
    return h


# ---- Fichiers communs et référence

def ecrire_animations():
    import scene_pilou
    _, table = scene_pilou.planche()
    lignes = ["# Animations nommées des sprites de scène : sprite nom première nombre pas(ms) mode (boucle | tient).",
              "# Écrit par outils/sprites/theatre.py d'après scene_pilou.py ; lu par Theatre.cs et Theatre.java."]
    for nom in scene_pilou.ORDRE:
        p, n, pas, mode = table[nom]
        lignes.append("%s %s %d %d %d %s" % (PILOU, nom, p, n, pas, mode))
    # Les personnages en pied : l'ordre des images de leurs portraits (0 et 1 repos, 2 yeux fermés, 3 et 4 parole).
    import pieds_campagnes
    for sid in pieds_campagnes.ids():
        lignes.append("%s repos 0 2 900 boucle" % sid)
        lignes.append("%s cligne 2 1 150 tient" % sid)
        lignes.append("%s parle 3 2 140 boucle" % sid)
    d = os.path.join(ASSETS, "scenes")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "animations.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lignes) + "\n")


def charger():
    import rendu
    B = {}
    for nom in ("sprites2x",):
        d = os.path.join(ASSETS, nom)
        for f in sorted(os.listdir(d)):
            if f.endswith(".txt") and (f.startswith("acteur-") or f.startswith("scene-") or f.startswith("decor-") or f.startswith("pied-")):
                with open(os.path.join(d, f), encoding="utf-8") as fh:
                    s = rendu.lire(fh.read(), f[:-4])
                B[s.id] = s
    with open(os.path.join(ASSETS, "scenes", "animations.txt"), encoding="utf-8") as fh:
        A = lire_animations(fh.read())
    for i, sp in B.items():
        DUREES[i] = sp.duree
        TAILLES[i] = (sp.w, sp.h)
    return B, A


def scenes_de(campagne):
    with open(os.path.join(ASSETS, "scenes", campagne + ".txt"), encoding="utf-8") as fh:
        return lire_scenes(fh.read())


TEINTES = {
    "bleu": ("#1f4f8a", "#4a8fdc", "#6cb6ff", "#b4dbff"),
    "orange": ("#8a4a1f", "#d9803a", "#f69d50", "#ffc89a"),
}

# Les scénarios de la référence : (nom, campagne, décor, teinte, niveau, regard, événements, instants).
SCENARIOS = [
    ("mare-entree", "prologue", "mare", "bleu", "completes", 0, [(0, "entree", 0, 0)], list(range(0, 9001, 250))),
    ("mare-clics", "prologue", "mare", "bleu", "completes", 0,
     [(0, "entree", 0, 0), (4000, "clic", 24, 70), (5200, "clic", 96, 54), (7000, "clic", 60, 64),
      (7300, "clic", 70, 66), (7600, "clic", 80, 62), (9000, "clic", 24, 70)],
     list(range(3500, 11001, 125))),
    ("mare-recit", "prologue", "mare", "orange", "completes", 1,
     [(0, "humeur", "peur", 0), (500, "parle", 3200, 0), (4000, "humeur", "joie", 0), (6000, "depart", 1, 0)],
     list(range(0, 16001, 250))),
    ("seuil-traverse", "prologue", "seuil", "bleu", "completes", 0,
     [(0, "entree", 40, 0), (900, "parle", 4000, 0), (1500, "parle", 1500, 0), (2600, "depart", -1, 0)],
     list(range(0, 6001, 200))),
    ("mare-reduites", "prologue", "mare", "bleu", "reduites", 0, [(0, "entree", 0, 0), (2000, "clic", 24, 70)],
     [0, 1000, 4150, 4299, 8000]),
    ("mare-aucune", "prologue", "mare", "bleu", "aucune", 0, [(0, "entree", 0, 0)], [0, 4200, 9000]),
]
SCENARIOS.append(("hall-grumeau", "grande-panne", "hall-pas-comptes", "bleu", "completes", 0,
                  [(0, "entree", 0, 0), (800, "perso", "pied-grande-panne-grumeau", 0), (3500, "parle-perso", 5600, 0),
                   (6500, "clic", 150, 70), (7400, "humeur", "joie", 0), (12000, "perso", "pied-grande-panne-tic-tac", 0),
                   (15000, "perso", "", 0)],
                  list(range(0, 19001, 250))))
SCENARIOS.append(("hall-reduites", "grande-panne", "hall-pas-comptes", "bleu", "reduites", 0,
                  [(0, "perso", "pied-grande-panne-grumeau", 0)], [0, 4150, 4299, 6000]))
for _d in ("jardin", "pente", "pied-colline", "seuil", "sommet"):
    SCENARIOS.append((_d + "-vie", "prologue", _d, "bleu", "completes", 0, [(0, "entree", 0, 0)],
                      list(range(0, 20001, 500))))


def _evt(e):
    return "evenement %d %s %s %s" % (e[0], e[1], e[2], e[3])


def ecrire_reference():
    B, A = charger()
    lignes = ["# Théâtre des campagnes : valeurs de référence (outils/sprites/theatre.py).",
              "# Relues par TheatreTests.cs (PC) et TheatreTest.java (téléphone).",
              "# scenario nom campagne décor teinte niveau regard ; evenement t sorte a b ;",
              "# pilou t x y image miroir visible ; acteurs t sprite:image:x:y:miroir … ; image t empreinte"]
    cache = {}
    for (nom, camp, dec, teinte, niv, regard, evts, instants) in SCENARIOS:
        if camp not in cache:
            cache[camp] = scenes_de(camp)
        sc = cache[camp][dec]
        decor = B.get("decor-%s-%s" % (camp, dec))
        lignes.append("scenario %s %s %s %s %s %d" % (nom, camp, dec, teinte, niv, regard))
        for e in evts:
            lignes.append(_evt(e))
        for t in instants:
            x, y, im, m, vis = pilou(sc, A, evts, t, regard, niv)
            lignes.append("pilou %d %d %d %d %d %d" % (t, x, y, im, int(m), int(vis)))
            pp = perso(sc, A, evts, t, niv)
            if pp is not None or any(e[1] == "perso" for e in evts):
                lignes.append("perso %d %s" % (t, "%s %d %d %d %d" % (pp[0], pp[1], pp[2], pp[3], int(pp[4])) if pp else "-"))
            ac = acteurs(sc, A, B, evts, t, niv) + effets(sc, A, B, evts, t, niv)
            lignes.append("acteurs %d %s" % (t, " ".join("%s:%d:%d:%d:%d" % (s, i, ax, ay, int(am)) for (s, i, ax, ay, am) in ac) or "-"))
            if t % 1000 == 0 or nom == "mare-clics":
                px = composer(B, TEINTES[teinte], decor, sc, A, evts, t, regard, niv)
                lignes.append("image %d %d" % (t, fnv(px)))
    with open(os.path.join(ICI, "theatre-reference.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lignes) + "\n")
    return len(lignes)


if __name__ == "__main__":
    ecrire_animations()
    print(ecrire_reference(), "lignes dans theatre-reference.txt")
