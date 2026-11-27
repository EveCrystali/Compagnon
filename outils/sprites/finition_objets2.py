"""Finition fine (2×), suite : accessoires, objets et petits décors de la quatrième série.

Rejeu fin des formes, puis liserés et ombres choisis couleur par couleur (recettes de retouches_fines) et détails propres
à chaque sprite : reflets, étincelles, œillets, anses. Voir finition_objets.py pour les pinceaux.
"""
import math

import fins
from finition import finition, trait, arc, points, disque, poly, composantes, \
    ENCRE, NOIR2, BLANC, CREME, CREME_O, GRIS, GRIS_C, ARDOISE, ARGENT, ARGENT_C, B1, B2, B3, B4, O1, O2, O3, O4, O5, \
    J1, J2, J3, J4, V1, V2, V3, V4, S1, S2, S3, BR1, BR2, BR3
from finition_lot3 import vider, px, trait_fin
from finition_objets import rr, teinte_ell, croissant, recolorer
from retouches_fines import appliquer, eclaircir, assombrir

clair, sombre = fins.clair, fins.sombre


def recette(*ids, texte, plus=None):
    """Recette de retouches_fines (L liseré, O ombre, G gauche, D droite, P plis, M mailles, C couture, R reflet) puis,
    au besoin, un détail propre au sprite `plus(t, k)`."""
    def f(t, k):
        appliquer(t, texte)
        if plus:
            plus(t, k)
    for i in ids:
        finition(i, auto=False)(f)


def zones(t, couleur, pmin=1, pmax=10 ** 9):
    return [z for c, z in composantes(t) if c == couleur and pmin <= len(z) <= pmax]


# ---- nuages de bouderie ---------------------------------------------------------------------------------
recette("boude-nuage", texte="L:#768390 O:#768390 G:#768390")
recette("boude-eclaircie", texte="L:#c9d1d9 O:#c9d1d9 G:#f5d76e D:#f5d76e O:#f5d76e")


@finition("boude-bras", auto=False)
def _boude_bras(t, k):
    """Deux avant-bras croisés, capsules arrondies à la teinte de Pilou : cerne, base, filet de lumière ; celui du bas,
    devant, recouvre l'autre."""
    vider(t)
    e = t.e
    for (g, d, haut) in ((2, 27, 1), (5, 30, 3)):
        x0, x1, y0, y1 = g, d + 1, haut, haut + 4
        cy = (y0 + y1) / 2
        for r2, col in ((4.0, "@contour"), (1.0, "@base")):
            for Y in range(int(y0 * e), int(y1 * e)):
                for X in range(int(x0 * e), int(x1 * e)):
                    xx, yy = (X + 0.5) / e, (Y + 0.5) / e
                    cx = min(max(xx, x0 + 2), x1 - 2)
                    if (xx - cx) ** 2 + (yy - cy) ** 2 <= r2:
                        t.g[Y][X] = col
        Y = int((y0 + 1.0) * e)
        for X in range(int((x0 + 1.6) * e), int((x1 - 2.2) * e)):
            if t.g[Y][X] == "@base":
                t.g[Y][X] = "@clair"


# ---- accessoires -----------------------------------------------------------------------------------------
@finition("acc-chapeaupeche", auto=False)
def _chapeau_peche(t, k):
    """Bob de pêcheur : calotte lisse (la trame du 1× disparaît) éclairée en haut à gauche, bande, bord à surpiqûres,
    mouche de pêche."""
    e = t.e
    recolorer(t, ARGENT, GRIS_C)
    teinte_ell(t, 17, 11, 11, 9, {GRIS_C}, ARGENT, lambda u, v: -0.55 * u - 0.85 * v > 0.45)
    teinte_ell(t, 13, 4.6, 4, 1.6, {ARGENT}, ARGENT_C)
    croissant(t, 17, 11, 11, 9, {GRIS_C}, sombre(GRIS_C, 0.18), (0.3, 0.2), 0.86)
    for X in range(int(6.4 * e), int(27.6 * e)):
        if t.g[int(7 * e)][X] == GRIS:
            t.g[int(7 * e)][X] = GRIS_C
    Y = int(10.6 * e)
    for X in range(int(3 * e), int(31 * e), 4):
        for dx in (0, 1):
            if t.getf(X + dx, Y) in (GRIS_C, ARGENT):
                t.pf(X + dx, Y, ARGENT_C)
    t.ell(21.6, 3.9, 1.5, 1.1, O3)
    t.ell(21.2, 3.5, 0.7, 0.4, O5)
    trait_fin(t, 19.6, 3.0, 20.6, 3.6, B3, 1)
    trait_fin(t, 22.9, 3.0, 23.8, 2.0, B3, 1)
    px(t, [(int(23.4 * e), int(2.4 * e))], O5)


@finition("acc-etoilemer", auto=False)
def _etoile_mer(t, k):
    """Étoile de mer : cinq bras effilés, flanc droit plus sombre, chapelet de granules clairs, cerne brun."""
    vider(t)
    e = t.e
    cx, cy, r = 6.5, 6.9, 5.7
    pts = []
    for i in range(10):
        a = math.radians(-90 + i * 36)
        rr_ = r if i % 2 == 0 else r * 0.46
        pts.append((cx + math.cos(a) * rr_, cy + math.sin(a) * rr_))
    t.poly(pts, O3)
    for Y in range(t.H):
        for X in range(t.W):
            if t.g[Y][X] == O3:
                dx, dy = (X + 0.5) / e - cx, (Y + 0.5) / e - cy
                if dx + dy * 0.7 > r * 0.42:
                    t.g[Y][X] = O2
                elif dx + dy < -r * 0.62:
                    t.g[Y][X] = eclaircir(O3, 0.2)
    for i in range(5):
        a = math.radians(-90 + i * 72)
        for f in (0.3, 0.62):
            X, Y = int((cx + math.cos(a) * r * f) * e), int((cy + math.sin(a) * r * f) * e)
            for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
                t.pf(X + dx, Y + dy, O5)
    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1), (-1, 0), (0, -1), (-1, -1), (-1, 1), (1, -1)):
        t.pf(int(cx * e) + dx, int(cy * e) + dy, O5 if dx + dy < 1 else O4)
    t.contour(O1)


@finition("acc-feuille", auto=False)
def _feuille_acc(t, k):
    """Feuille posée sur la tête : limbe en deux tons, nervure et nervures secondaires, tige, cerne brun."""
    vider(t)
    e = t.e
    ang = math.radians(-45)
    ca, sa = math.cos(ang), math.sin(ang)
    cx, cy = 6.2, 5.8
    for Y in range(t.H):
        for X in range(t.W):
            dx, dy = (X + 0.5) / e - cx, (Y + 0.5) / e - cy
            u = (dx * ca + dy * sa) / 4.7
            v = (-dx * sa + dy * ca) / (2.55 * (1 - 0.18 * u))
            if u * u + v * v <= 1:
                if abs(v) < 0.09:
                    t.pf(X, Y, O1)
                elif v < 0:
                    t.pf(X, Y, O3)
                else:
                    t.pf(X, Y, O2)
    for n in range(-3, 4):
        if n == 0:
            continue
        x0, y0 = cx + (n * 1.1) * ca, cy + (n * 1.1) * sa
        for sgn in (-1, 1):
            trait_fin(t, x0, y0, x0 + (sgn * -sa) * 1.5 + ca * 0.6, y0 + (sgn * ca) * 1.5 + sa * 0.6,
                      O2 if sgn < 0 else assombrir(O2, 0.25), 1)
    trait_fin(t, 1.4, 10.4, 3.2, 8.8, O1, 1)
    t.contour(O1)


@finition("acc-tablier", auto=False)
def _tablier(t, k):
    """Tablier : plis de lumière à gauche et d'ombre à droite, ourlet, poche à surpiqûres."""
    e = t.e
    for Y in range(t.H):
        for X in range(t.W):
            if t.g[Y][X] == CREME:
                f = (X / e - 1) / 18
                if f < 0.12:
                    t.g[Y][X] = BLANC
                elif f > 0.82:
                    t.g[Y][X] = CREME_O
                elif f > 0.7:
                    t.g[Y][X] = "#e1e7ee"
    for X in range(int(1.4 * e), int(18.6 * e)):
        Y = int(16.3 * e)
        if t.g[Y][X] in (CREME, BLANC):
            t.g[Y][X] = "#e1e7ee"
    for Y in range(int(7 * e), int(12 * e)):
        for X in range(int(6 * e), int(14 * e)):
            if t.g[Y][X] == O3:
                if X < int(6.5 * e):
                    t.g[Y][X] = O4
                elif Y >= int(11.4 * e) or X >= int(13.4 * e):
                    t.g[Y][X] = O2
    for X in range(int(6.8 * e), int(13.2 * e), 3):
        t.pf(X, int(7.9 * e), O4)
        t.pf(X + 1, int(7.9 * e), O4)


@finition("appareil-photo", auto=False)
def _appareil(t, k):
    """Appareil photo : capot qui accroche la lumière, objectif en anneaux avec reflets."""
    appliquer(t, "L:#3b4654 O:#3b4654 L:#545d68")
    lent = zones(t, "#4a8fdc", 40)
    if lent:
        z = max(lent, key=len)
        xs, ys = [p[0] for p in z], [p[1] for p in z]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        r = (max(xs) - min(xs)) / 2
        for X, Y in z:
            dx, dy = X - cx, Y - cy
            d = math.hypot(dx, dy) / max(r, 1)
            if d > 0.72:
                t.g[Y][X] = "#1f4f8a" if (dx + dy) > 0 else "#3a74bd"
            elif dx + dy < -0.55 * r:
                t.g[Y][X] = B3
        for dx, dy in ((-0.45, -0.5), (-0.3, -0.5), (-0.45, -0.35)):
            t.pf(int(cx + dx * r), int(cy + dy * r), BLANC)
        px(t, [(int(cx + 0.35 * r), int(cy + 0.45 * r))], B4)


@finition("arrosoir", auto=False)
def _arrosoir(t, k):
    appliquer(t, "L:#6cb6ff O:#4a8fdc G:#b4dbff L:#4a8fdc")


@finition("bouchon", auto=False)
def _bouchon(t, k):
    """Flotteur : orange en haut, blanc en bas, reflet rond sur chaque moitié, tige grise."""
    appliquer(t, "O:#f6f8fa G:#768390")
    teinte_ell(t, 3, 2.8 + k, 0.9, 0.6, {O3}, O4)
    teinte_ell(t, 3, 5.4 + k, 0.8, 0.5, {CREME}, BLANC)


recette("clochette", texte="L:#f5d76e O:#f5d76e D:#f5d76e")
recette("coffre-quete", texte="L:#a86f3c O:#7a4b26 L:#c9a227 O:#c9a227 L:#7a4b26")
recette("coffre-expedition-ouvert", texte="L:#a86f3c O:#7a4b26 L:#7a4b26 O:#4a2e17 L:#b8c4d2 G:#b8c4d2")
recette("cube-pixel", texte="L:#6a5acd O:#6a5acd D:#6a5acd G:#9b8cff")
recette("eclair-energie", texte="L:#f5d76e O:#f5d76e G:#f5d76e")
recette("enveloppe-close", texte="L:#f6f8fa O:#f6f8fa L:#d9803a O:#d9803a")
recette("enveloppe-notif", texte="L:#ffffff O:#f6f8fa L:#f6f8fa O:#f69d50")
recette("etoile", texte="L:#f5d76e O:#f5d76e D:#f5d76e")
recette("fouet", texte="L:#b8c4d2 O:#b8c4d2 L:#4a8fdc O:#4a8fdc G:#6cb6ff")
recette("fourchette-geante", texte="G:#b8c4d2 D:#b8c4d2 L:#e6ecf2")
recette("jeton-arcade", texte="L:#f5d76e O:#f5d76e D:#f5d76e")


@finition("carapace", auto=False)
def _carapace(t, k):
    """Carapace : dôme éclairé en haut à gauche, flanc droit plus sombre, écailles en relief (lumière dessus)."""
    appliquer(t, "L:#c4a77d")
    croissant(t, 23, 22, 20, 18, {S2}, sombre(S2, 0.14), (0.3, 0.1), 0.82)
    for cx, cy in ((23, 9), (12, 16), (34, 16), (17, 25), (29, 25)):
        croissant(t, cx, cy, 4.4, 3.4, {S3}, "#d3bf98", (0.25, 0.3), 0.8)
        teinte_ell(t, cx - 1.2, cy - 1.2, 1.4, 0.8, {S3}, "#f6ead2")
