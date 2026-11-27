"""Ambiances animées des décors de campagne (docs/SPRITES.md, « Décors animés ») : outil de fabrication, pas embarqué.

Chaque décor `decor-<campagne>-<id>` devient une boucle de 6 à 8 images (4 à 6 images par seconde), lente et sobre :
faisceau du phare qui tourne, reflets qui ondulent, brume qui respire, étoiles qui scintillent, flammes qui vacillent,
fumée qui monte, poussière dans un rai de lumière, bruine, neige, herbes au vent, câbles qui luisent…

Le principe : le dessin du décor est rejoué pour chaque image (`decors_campagnes.toiles`) avec une **phase** p de la
boucle (0 ≤ p < 1, `decors_campagnes.PHASE`) ; ses propres outils (flamme, mer, ciel de nuit, engrenages…) s'en servent
directement, puis les effets d'ambiance listés ici se posent dessus. Tout effet est une fonction **périodique** de p
(sinus de 2πp, ou cycle de vie (p + décalage) mod 1) : l'image n + 1 suit l'image n, et la dernière retombe sur la
première sans à-coup. Les couleurs viennent de la palette restreinte du décor (`PAL` de son module) : aucune couleur
nouvelle, jamais plus de 62. Rejoués à l'échelle 2, les effets travaillent en pixels fins (trame, reflets d'un pixel fin).

Réglage par décor (`REGLES`) : (images, duree en ms, garder, [effets]). `garder` : l'ancienne alternance du dessin (k)
suit la boucle (k = image × anciennes images ÷ images) ; faux : le dessin reste sur son image 0 et seuls la phase et les
effets bougent (on retire ainsi les anciennes alternances qui sautaient).
"""
import math

from peinture import Palette, palier, seuil, hasard, mix, lueur as _lueur, voile as _voile

TAU = 2 * math.pi


def s(p, d=0.0):
    """Sinus de la boucle."""
    return math.sin(TAU * (p + d))


def _pixels(t, cadre):
    x0, y0, x1, y1 = cadre
    e = t.e
    for Y in range(max(0, int(y0 * e)), min(t.H, int(math.ceil(y1 * e)))):
        for X in range(max(0, int(x0 * e)), min(t.W, int(math.ceil(x1 * e)))):
            yield X, Y, (X + 0.5) / e, (Y + 0.5) / e


def _clarte(c):
    return int(c[1:3], 16) * 2 + int(c[3:5], 16) * 4 + int(c[5:7], 16) * 3


# ---------------------------------------------------------------------------------------------------------------------
# Effets : chacun est une fabrique qui rend f(t, p, pal)
# ---------------------------------------------------------------------------------------------------------------------
def scintille(cadre, ecart=140, part=0.45, graine=1, croix=True):
    """Étoiles (ou paillettes) : les points clairs isolés du cadre s'éteignent un instant chacun à son tour ; au rendu
    fin, les plus brillantes portent un instant une petite croix."""
    def f(t, p, pal):
        base = [r[:] for r in t.g]
        e = t.e
        for X, Y, x, y in _pixels(t, cadre):
            c = base[Y][X]
            if c is None:
                continue
            vois = [base[Y + b][X + a] for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))
                    if 0 <= X + a < t.W and 0 <= Y + b < t.H]
            if not vois or any(v is None for v in vois):
                continue
            k = _clarte(c)
            if not all(k - _clarte(v) > ecart for v in vois):
                continue
            h = hasard(X // e, Y // e, graine)
            if h > part * 1.6:
                continue
            v = s(p, h * 7.3)
            if v < -0.55:
                t.g[Y][X] = min(vois, key=_clarte) if v < -0.85 else pal.proche(mix(c, min(vois, key=_clarte), 0.6))
            elif v > 0.8 and croix and e == 2:
                for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if 0 <= X + a < t.W and 0 <= Y + b < t.H:
                        t.g[Y + b][X + a] = pal.proche(mix(base[Y + b][X + a], c, 0.55))
    return f


def brume(y0, y1, force=0.5, couleur=None, x0=0, x1=96, niveaux=2, sur=None):
    """Banc de brume qui respire et se déforme sur place (ondes stationnaires croisées : rien ne file vite)."""
    def f(t, p, pal):
        c = couleur

        def k(x, y):
            if y < y0 or y > y1:
                return 0
            u = (y - y0) / (y1 - y0)
            onde = (math.sin(x / 6.5 + 1.3 * math.sin(y / 4)) * math.cos(TAU * p)
                    + math.sin(x / 9.5 + 2.1) * math.sin(TAU * p)) * 0.5
            return force * math.sin(u * math.pi) * (0.55 + 0.45 * onde)
        _voile(t, k, c, pal, (x0, y0, x1, y1), niveaux=niveaux, sur=sur)
    return f


def reflets(cadre, couleur, n=16, ampleur=1.6, eau=None, graine=3, longueur=(1.5, 4.5)):
    """Reflets sur l'eau : de courts traits clairs qui glissent d'avant en arrière et s'allument, s'éteignent."""
    def f(t, p, pal):
        x0, y0, x1, y1 = cadre
        e = t.e
        eaux = set(eau) if eau else None
        for i in range(n):
            bx = x0 + hasard(i, 11, graine) * (x1 - x0)
            by = y0 + 0.5 + hasard(i, 12, graine) * (y1 - y0 - 1)
            l = longueur[0] + hasard(i, 13, graine) * (longueur[1] - longueur[0]) * (0.5 + (by - y0) / max(1, y1 - y0))
            d = hasard(i, 14, graine)
            if s(p, d) < -0.35:
                continue
            x = bx + ampleur * s(p, d + 0.25)
            Y = int(by * e)
            for X in range(int(x * e), int((x + l) * e)):
                if 0 <= X < t.W and 0 <= Y < t.H and x0 * e <= X < x1 * e:
                    if eaux is None or t.g[Y][X] in eaux:
                        t.g[Y][X] = couleur
    return f


def onduler(cadre, ampleur=1.0, longueur=3.0, decalage=0.0):
    """Ondulation : chaque ligne du cadre glisse de quelques pixels réels, en vague qui respire (eau, chaleur)."""
    def f(t, p, pal):
        x0, y0, x1, y1 = cadre
        e = t.e
        X0, X1 = max(0, int(x0 * e)), min(t.W, int(math.ceil(x1 * e)))
        for Y in range(max(0, int(y0 * e)), min(t.H, int(math.ceil(y1 * e)))):
            d = int(round(ampleur * e * math.sin(TAU * (p + decalage) + Y / (longueur * e))))
            if not d:
                continue
            ligne = t.g[Y][X0:X1]
            n = len(ligne)
            t.g[Y][X0:X1] = [ligne[min(max(i - d, 0), n - 1)] for i in range(n)]
    return f


def vent(cadre, ampleur=1.0, decalage=0.0, sur=None):
    """Herbes, feuillages, drapeaux au vent : le haut du cadre balance plus que le bas (le bas reste planté)."""
    def f(t, p, pal):
        x0, y0, x1, y1 = cadre
        e = t.e
        X0, X1 = max(0, int(x0 * e)), min(t.W, int(math.ceil(x1 * e)))
        Y0, Y1 = max(0, int(y0 * e)), min(t.H, int(math.ceil(y1 * e)))
        base = [r[:] for r in t.g]
        for Y in range(Y0, Y1):
            haut = 1 - (Y - Y0) / max(1, Y1 - Y0)
            d = int(round(ampleur * e * haut * (0.6 * s(p, decalage) + 0.4 * s(p, decalage + 0.31) )))
            if not d:
                continue
            for X in range(X0, X1):
                src = min(max(X - d, X0), X1 - 1)
                c = base[Y][src]
                if sur is None or c in sur or base[Y][X] in sur:
                    t.g[Y][X] = c
    return f


def particules(cadre, couleurs, n=12, dx=0.0, dy=4.0, graine=5, vie=(0.12, 0.88), taille=1, sur=None, oscille=0.0, cond=None):
    """Particules qui vivent et passent : poussière, neige, bruine, aiguilles, braises, lucioles, graines. Chacune avance
    de (dx, dy) sur sa vie (une boucle), visible entre vie[0] et vie[1] : elle naît et s'efface sans saut."""
    def f(t, p, pal):
        x0, y0, x1, y1 = cadre
        e = t.e
        for i in range(n):
            h = hasard(i, 1, graine)
            u = (p + h) % 1.0
            if not (vie[0] <= u <= vie[1]):
                continue
            x = x0 + hasard(i, 2, graine) * (x1 - x0) + dx * u + oscille * math.sin(TAU * (u * 2 + h))
            y = y0 + hasard(i, 3, graine) * (y1 - y0) + dy * u
            if cond is not None and not cond(x, y):
                continue
            c = couleurs[int(hasard(i, 4, graine) * len(couleurs)) % len(couleurs)]
            X, Y = int(x * e), int(y * e)
            tl = max(1, int(taille * e)) if taille >= 1 else 1
            for a in range(tl):
                for b in range(tl):
                    if 0 <= X + a < t.W and 0 <= Y + b < t.H and x0 * e <= X + a < x1 * e and y0 * e <= Y + b < y1 * e:
                        if sur is None or t.g[Y + b][X + a] in sur:
                            t.g[Y + b][X + a] = c
    return f


def pluie(cadre, couleur, n=22, pente=-0.35, longueur=2.2, graine=9, tours=2):
    """Pluie fine : des traits obliques qui tombent sans fin (chacun parcourt le cadre `tours` fois par boucle)."""
    def f(t, p, pal):
        x0, y0, x1, y1 = cadre
        e = t.e
        H = y1 - y0
        W = x1 - x0
        for i in range(n):
            u = (hasard(i, 1, graine) + p * tours) % 1.0
            y = y0 + u * (H + longueur) - longueur
            x = x0 + (hasard(i, 2, graine) * W + (y - y0) * pente) % W
            for j in range(int(longueur * e)):
                X, Y = int(x * e + j * pente), int(y * e) + j
                if 0 <= X < t.W and y0 * e <= Y < min(t.H, y1 * e):
                    t.g[Y][X] = pal.proche(mix(t.g[Y][X], couleur, 0.6))
    return f


def pulse(x, y, r, couleur, force=0.5, ampleur=0.25, ry=None, teinte=False, decalage=0.0):
    """Halo qui respire (lanterne, néon, flaque de lumière, câble chaud)."""
    def f(t, p, pal):
        k = force * (1 + ampleur * s(p, decalage))
        _lueur(t, x, y, r, couleur, pal, force=max(0.05, k), ry=ry, teinte=teinte)
    return f


def fumee(x, y, couleur, n=4, haut=9.0, derive=3.0, r=(0.7, 2.0), force=0.65, graine=2):
    """Fumée, vapeur : des bouffées qui montent, gonflent et se dissipent en se fondant au fond."""
    def f(t, p, pal):
        for i in range(n):
            u = (p + i / n) % 1.0
            cx = x + derive * u + 0.7 * math.sin(TAU * (u * 1.5 + hasard(i, 1, graine)))
            cy = y - haut * u
            rr = r[0] + (r[1] - r[0]) * u
            k = force * (1 - u) * min(1.0, u * 6)

            def kf(px, py, cx=cx, cy=cy, rr=rr, k=k):
                d = math.hypot(px - cx, (py - cy) * 1.2) / rr
                return k * (1 - d) * 1.6 if d < 1 else 0
            _voile(t, kf, couleur, pal, (cx - rr - 1, cy - rr - 1, cx + rr + 1, cy + rr + 1), niveaux=2)
    return f


def faisceau(x, y, longueur, couleur, demi=0.16, force=0.75, haut=None, bas=None):
    """Faisceau du phare qui tourne : un pinceau de lumière qui balaie, s'allonge quand il passe de côté, s'efface
    quand il tourne vers le large ; un éclat blanc quand il passe face à nous."""
    def f(t, p, pal):
        a = TAU * p
        cote = math.cos(a)          # -1 : vers la gauche, 1 : vers la droite
        face = math.sin(a)          # > 0 : vers nous
        L = longueur * abs(cote)
        y0 = haut if haut is not None else y - 6
        y1 = bas if bas is not None else y + 6
        if L > 2:
            sens = 1 if cote > 0 else -1
            x0, x1 = (x, x + L) if sens > 0 else (x - L, x)

            def k(px, py):
                d = (px - x) * sens
                if d <= 0 or d > L:
                    return 0
                largeur = 0.6 + d * demi
                v = abs(py - y) / largeur
                if v >= 1:
                    return 0
                return force * (1 - v) * (1 - 0.65 * d / L) * (0.55 + 0.45 * abs(cote))
            _voile(t, k, couleur, pal, (x0, y0, x1, y1), niveaux=3)
        if face > 0.55:
            _lueur(t, x, y, 3 + 3 * face, couleur, pal, force=0.5 * face, teinte=True)
    return f


def alterner(cadre, de, vers, part=0.5, decalage=0.0):
    """Une couleur du cadre en prend une autre pendant une partie de la boucle (voyant, chiffre, néon qui baisse)."""
    def f(t, p, pal):
        if (p + decalage) % 1.0 >= part:
            return
        for X, Y, x, y in _pixels(t, cadre):
            if t.g[Y][X] == de:
                t.g[Y][X] = vers
    return f


def balayage(cadre, couleur, largeur=3.0, pente=0.6, force=0.6, sur=None):
    """Un reflet qui passe (vitre, barre de chargement, lentille) : une bande claire qui traverse le cadre une fois par
    boucle (elle sort d'un côté avant de rentrer de l'autre)."""
    def f(t, p, pal):
        x0, y0, x1, y1 = cadre
        W = x1 - x0 + largeur * 2 + (y1 - y0) * pente
        c0 = x0 - largeur - (y1 - y0) * pente + p * W

        def k(px, py):
            d = abs(px - (c0 + (py - y0) * pente))
            return force * (1 - d / largeur) if d < largeur else 0
        _voile(t, k, couleur, pal, cadre, niveaux=2, sur=sur)
    return f


# ---------------------------------------------------------------------------------------------------------------------
# Les décors : (images, durée par image, garder l'ancienne alternance, effets)
# Les coordonnées sont celles de la grille 1× (96 × 40).
# ---------------------------------------------------------------------------------------------------------------------
def regles():
    """Construite à la demande (les palettes viennent des modules de décors)."""
    import decors_prologue as P
    import decors_panne as G
    import decors_phare as F
    import decors_nuage as N
    R = {}

    def d(campagne, id_, images, duree, garder, effets):
        R["decor-%s-%s" % (campagne, id_)] = (images, duree, garder, effets)

    # ---- Prologue : fin d'après-midi dorée, herbes au vent, graines et pollen.
    herbes_p = [P.S1, P.S2, P.S3, P.S4, P.OR1, P.OR2, P.OR3]
    d("prologue", "seuil", 6, 230, True, [
        vent((60, 26, 96, 40), 0.8, sur=herbes_p),
        particules((66, 4, 96, 30), [P.OR3, P.CREME], n=6, dx=5, dy=-3, graine=21, oscille=0.8)])
    d("prologue", "jardin", 6, 230, True, [
        vent((0, 20, 96, 40), 1.0, sur=herbes_p),
        particules((0, 4, 96, 30), [P.CREME, P.OR3], n=10, dx=7, dy=-2, graine=22, oscille=1.0)])
    d("prologue", "mare", 6, 240, True, [
        onduler((8, 26, 88, 37), 0.5, 1.6), reflets((10, 27, 86, 36), P.CIEL[0], n=12, ampleur=1.2, eau=[P.EAU1, P.EAU2, P.EAU3], graine=23),
        vent((0, 14, 16, 36), 0.8, sur=herbes_p), vent((82, 14, 96, 36), 0.8, 0.4, sur=herbes_p)])
    d("prologue", "pied-colline", 6, 230, True, [
        vent((0, 26, 96, 40), 1.0, sur=herbes_p),
        particules((0, 8, 96, 32), [P.CREME, P.OR3], n=8, dx=6, dy=-2, graine=24, oscille=0.8)])
    d("prologue", "pente", 6, 230, True, [
        vent((0, 22, 96, 40), 1.0, 0.2, sur=herbes_p),
        particules((10, 6, 96, 30), [P.BLANC, P.CREME], n=10, dx=10, dy=-4, graine=25, oscille=1.2)])
    d("prologue", "sommet", 6, 250, True, [
        pulse(66, 29, 18, P.SOLEIL2, force=0.3, ampleur=0.35, ry=9), vent((10, 12, 26, 24), 0.8, sur=herbes_p)])

    # ---- La Grande Panne : néons, câbles, papiers, poussière de bureau.
    d("grande-panne", "bureau-1337", 6, 240, True, [
        onduler((0, 2, 96, 22), 0.5, 3), balayage((60, 30, 96, 40), G.C3, largeur=2.5, force=0.4, sur=[G.N0, G.N1, G.N2])])
    d("grande-panne", "bureau-echeance", 6, 240, True, [
        pulse(48, 30, 14, G.J3, force=0.35, ampleur=0.3, ry=8),
        particules((32, 14, 66, 34), [G.J3, G.E5], n=9, dx=2, dy=-4, graine=31, oscille=0.6)])
    d("grande-panne", "cabane-brouillon", 6, 240, True, [
        particules((50, 0, 96, 32), [G.E5, G.BLANC], n=12, dx=-3, dy=5, graine=32, oscille=0.6),
        pulse(84, 6, 16, G.E5, force=0.25, ampleur=0.3)])
    d("grande-panne", "caverne-cables", 6, 240, True, [
        pulse(28, 30, 14, G.C2, force=0.45, ampleur=0.35, teinte=True), scintille((0, 0, 96, 40), ecart=120, part=0.6, graine=33),
        particules((20, 18, 36, 32), [G.C3, G.T3], n=6, dx=0, dy=-8, graine=34)])
    d("grande-panne", "citadelle-nuage", 6, 250, True, [
        scintille((0, 0, 96, 18), ecart=80, part=0.5, graine=35),
        pulse(48, 18, 10, G.J3, force=0.2, ampleur=0.5)])
    d("grande-panne", "dossier-temp", 6, 200, True, [
        particules((0, 0, 96, 16), [G.G4, G.E5], n=10, dx=-16, dy=1, graine=36, taille=1),
        particules((0, 0, 96, 30), [G.BLANC], n=4, dx=-10, dy=3, graine=37, oscille=1.0)])
    d("grande-panne", "etage-guichets", 6, 240, False, [
        particules((28, 0, 96, 40), [G.J3, G.BLANC], n=16, dx=2, dy=-3, graine=38, oscille=0.6,
                   cond=lambda x, y: 0 < (x - 30) - (40 - y) * 0.6 < 10),
        pulse(70, 20, 18, G.J3, force=0.12, ampleur=0.6)])
    d("grande-panne", "file-impression", 6, 240, True, [
        pulse(30, 8, 12, G.J3, force=0.35, ampleur=0.3), particules((0, 10, 70, 30), [G.E5], n=8, dx=4, dy=-3, graine=39)])
    d("grande-panne", "hall-pas-comptes", 6, 240, True, [
        pulse(52, 10, 18, G.O2, force=0.35, ampleur=0.3, ry=8, teinte=True)])
    d("grande-panne", "horloge-systeme", 8, 200, True, [
        particules((30, 2, 66, 36), [G.N3, G.CIEL1], n=10, dx=0, dy=6, graine=40)])
    d("grande-panne", "marais-majs", 6, 220, True, [
        pluie((0, 0, 96, 34), G.G4, n=20, graine=41), brume(14, 30, 0.4, G.G4),
        balayage((30, 9, 72, 13), G.C3, largeur=2, force=0.7), reflets((0, 32, 96, 40), G.G3, n=10, graine=42)])
    d("grande-panne", "tour-tampon", 6, 240, True, [
        fumee(51, 4, G.G4, haut=8, derive=4), pulse(48, 33, 10, G.O2, force=0.25, ampleur=0.4, teinte=True)])

    # ---- Le phare éteint : nuit bleue, brume, mer, lanternes.
    d("phare-eteint", "chez-pilou", 6, 240, False, [
        particules((24, 4, 70, 30), [F.L4, F.L5], n=8, dx=-2, dy=3, graine=51, oscille=0.5,
                   cond=lambda x, y: 0 < (x - 30) + (y - 22) * 1.4 < 30),
        onduler((57, 4, 85, 17), 0.5, 2)])
    d("phare-eteint", "port-trebrume", 6, 240, False, [
        brume(12, 29, 0.35, F.BR3), reflets((0, 23, 96, 31), F.BR3, n=10, graine=52, eau=[F.MER0, F.MER1, F.MER2])])
    d("phare-eteint", "auberge-bigorneau", 6, 240, True, [
        fumee(48, 18, F.BR4, n=4, haut=9, derive=1.5, r=(0.8, 2.2), force=0.9),
        pulse(48, 21, 16, F.L4, force=0.12, ampleur=0.8)])
    d("phare-eteint", "guet-de-nuit", 6, 250, True, [
        brume(8, 28, 0.3, F.N3, x0=56, x1=88), reflets((56, 22, 88, 28), F.N3, n=6, ampleur=1, graine=53, eau=[F.N0, F.N1, F.MER0])])
    d("phare-eteint", "passe-pied", 6, 250, False, [
        brume(4, 24, 0.4, F.BR3), particules((0, 6, 96, 22), [F.CREME], n=3, dx=10, dy=-1, graine=54, vie=(0.2, 0.8))])
    d("phare-eteint", "pied-du-phare", 6, 240, True, [
        particules((0, 26, 96, 36), [F.BR4, F.CREME], n=10, dx=1, dy=-4, graine=55, vie=(0.1, 0.5))])
    d("phare-eteint", "place-mairie", 6, 220, False, [
        pluie((0, 0, 96, 40), F.BR4, n=16, pente=-0.4, graine=56), brume(2, 22, 0.25, F.BR3)])
    d("phare-eteint", "atelier-basile", 8, 200, False, [
        particules((4, 6, 60, 30), [F.LAITON2, F.L4], n=12, dx=2, dy=-3, graine=57, oscille=0.6),
        pulse(30, 30, 26, F.LAITON2, force=0.12, ampleur=0.6, ry=14)])
    d("phare-eteint", "sentier-douaniers", 6, 260, False, [
        brume(8, 32, 0.45, F.BR4), reflets((0, 30, 70, 40), F.BR3, n=8, graine=58, eau=[F.BR1, F.BR2, F.N3])])
    d("phare-eteint", "grotte-souffleur", 6, 240, True, [
        reflets((48, 24, 92, 31), F.BR4, n=8, ampleur=1.2, graine=59), pulse(28, 29, 18, F.L3, force=0.18, ampleur=0.5, teinte=True),
        particules((52, 18, 90, 30), [F.BR4, F.CREME], n=6, dx=-2, dy=-3, graine=60, vie=(0.1, 0.45))])
    d("phare-eteint", "cave-du-phare", 6, 240, True, [
        pulse(48, 32, 22, F.L4, force=0.2, ampleur=0.7, ry=14, teinte=True),
        particules((60, 4, 70, 34), [F.BR3], n=3, dx=0, dy=16, graine=61, vie=(0.2, 0.9))])
    d("phare-eteint", "chambre-de-veille", 6, 240, True, [
        pulse(7.5, 24, 14, F.L3, force=0.2, ampleur=0.5), fumee(74, 13, F.BR3, n=3, haut=6, derive=1, r=(0.4, 1.2), force=0.5)])
    d("phare-eteint", "lanterne-du-phare", 8, 200, False, [
        balayage((40, 7, 57, 25), F.L5, largeur=2.5, pente=0.2, force=0.7), brume(0, 40, 0.3, F.BR4)])
    d("phare-eteint", "jetee-nuit", 8, 220, False, [
        faisceau(84, 7, 72, F.L4, demi=0.2, force=0.55, haut=0, bas=22), brume(16, 32, 0.3, F.N4),
        reflets((0, 22, 96, 40), F.N3, n=12, graine=62, eau=[F.N0, F.N1, F.MER0])])

    # ---- Petit Nuage : ciels lavés, troupeau de nuages, neige, vapeur.
    herbes_n = [N.H1, N.H2, N.H3, N.H4, N.P1, N.P2, N.P3, N.P4]
    d("petit-nuage", "jardin-lave", 6, 250, True, [
        onduler((0, 22, 96, 40), 0.5, 1.5), reflets((0, 24, 96, 40), N.C3, n=12, graine=71, eau=[N.EA1, N.EA2, N.EA3, N.EA4])])
    d("petit-nuage", "chemin-creux", 6, 240, True, [
        vent((0, 12, 34, 32), 0.8, sur=herbes_n), vent((62, 12, 96, 32), 0.8, 0.3, sur=herbes_n),
        particules((0, 4, 96, 30), [N.NE4, N.P4], n=8, dx=8, dy=-2, graine=72, oscille=1.0)])
    d("petit-nuage", "pre-aux-draps", 6, 230, True, [vent((0, 22, 96, 40), 0.8, sur=herbes_n)])
    d("petit-nuage", "etang-qui-fume", 6, 260, True, [
        reflets((0, 28, 96, 38), N.EA4, n=10, graine=73, eau=[N.EA1, N.EA2, N.EA3]), scintille((0, 0, 50, 24), ecart=60, part=0.6, graine=74)])
    d("petit-nuage", "plateau-rape", 6, 200, True, [
        vent((0, 24, 96, 38), 1.0, sur=herbes_n), particules((0, 14, 96, 36), [N.P3, N.TE3], n=12, dx=14, dy=-1, graine=75)])
    d("petit-nuage", "halte-girouette", 6, 250, True, [
        scintille((0, 0, 96, 16), ecart=70, part=0.5, graine=76), pulse(44, 33, 8, N.L2, force=0.3, ampleur=0.4)])
    d("petit-nuage", "sentier-des-melezes", 6, 240, False, [
        particules((0, 8, 96, 38), [N.M2, N.M1], n=12, dx=-3, dy=7, graine=77, oscille=0.8), vent((0, 10, 96, 34), 0.6, sur=[N.M1, N.M2])])
    d("petit-nuage", "terrier-aux-bocaux", 6, 240, True, [
        pulse(48, 20, 16, N.L2, force=0.25, ampleur=0.4), scintille((0, 0, 96, 30), ecart=110, part=0.5, graine=78)])
    d("petit-nuage", "col-blanc", 6, 260, True, [
        particules((0, 0, 96, 36), [N.NE4, N.NE3], n=18, dx=-4, dy=6, graine=79, oscille=0.6)])
    d("petit-nuage", "trou-qui-siffle", 6, 180, True, [scintille((0, 0, 96, 40), ecart=120, part=0.4, graine=80)])
    d("petit-nuage", "grande-salle", 6, 240, False, [
        particules((40, 4, 56, 36), [N.SO3, N.NE3], n=10, dx=0, dy=4, graine=81, oscille=0.6),
        particules((0, 4, 96, 34), [N.EA4], n=4, dx=0, dy=14, graine=82, vie=(0.3, 0.9))])
    d("petit-nuage", "abreuvoir", 6, 260, True, [
        reflets((0, 30, 96, 37), N.SO3, n=10, graine=83), scintille((0, 0, 96, 8), ecart=60, part=0.5, graine=84)])
    d("petit-nuage", "abreuvoir-aube", 6, 260, True, [reflets((0, 30, 96, 37), N.AU2, n=10, graine=85)])
    d("petit-nuage", "fenetre-maison", 6, 250, True, [
        fumee(34, 24, N.NE3, n=4, haut=8, derive=1.5, r=(0.5, 1.6), force=0.6), pulse(10, 26, 16, N.L2, force=0.15, ampleur=0.5, ry=10)])
    return R


_REGLES = None


def regle(sid):
    global _REGLES
    if _REGLES is None:
        _REGLES = regles()
    return _REGLES.get(sid)
