"""Finition fine (2×), suite : objets tenus en main et petits accessoires (main, sucette, pierre de calme, flash, pancarte,
lanterne-courge, macaron, manette, nid d'oiseau, parchemin, pinceau, sucre d'orge, guirlande, clavier, lampe).

Même principe que finition_objets.py : redessin des formes en pixels fins quand le sprite est simple, retouche ciblée du
rejeu fin sinon.
"""
import math

import fins
from finition import finition, trait, arc, points, disque, poly, composantes, \
    ENCRE, NOIR2, BLANC, CREME, CREME_O, GRIS, GRIS_C, ARDOISE, ARGENT, ARGENT_C, B1, B2, B3, B4, O1, O2, O3, O4, O5, \
    J1, J2, J3, J4, V1, V2, V3, V4, S1, S2, S3, BR1, BR2, BR3
from finition_lot3 import vider, px, trait_fin
from finition_objets import rr, teinte_ell, croissant, recolorer
from finition_objets2 import recette, zones
from retouches_fines import appliquer, eclaircir, assombrir

clair, sombre = fins.clair, fins.sombre


@finition("main", auto=False)
def _main(t, k):
    """Main ouverte (« tape m'en cinq ») : quatre doigts arrondis, pouce, creux de la paume, manchette bleue."""
    vider(t)
    e = t.e
    rr(t, 3, 7, 12, 11, 1.3, O4)
    for i, h in enumerate((7, 8, 8, 7)):
        x0, top = 3 + i * 3 - 0.1, 7 - h + 1
        rr(t, x0, top, 2.3, h + 1.5, 1.15, O4)
        t.rect(x0 + 0.1, top + 0.9, 0.5, h - 2, O5)
        t.rect(x0 + 2.0, top + 2.0, 0.3, h - 2.5, O3)
    # Pouce : capsule penchée.
    t.poly([(14.4, 13.6), (16.2, 9.4), (18, 9.9), (18, 11.4), (15.2, 17)], O4)
    t.ell(17.0, 10.3, 1.0, 1.1, O4)
    trait_fin(t, 16.6, 10.0, 15.2, 13.2, O5, 1)
    # Paume : ombre à droite et en bas, pli de la ligne de vie.
    for Y in range(int(7 * e), int(18 * e)):
        for X in range(int(3 * e), int(15 * e)):
            if t.g[Y][X] == O4 and (X >= int(14.2 * e) or Y >= int(17.2 * e)):
                t.g[Y][X] = O3
    arc(t, 8.6, 10.6, 3.4, 2.3, 20, 160, O3, {O4, O5})
    # Manchette bleue : filet clair en haut, pli sombre.
    rr(t, 3, 18, 12, 2, 0.3, B3)
    t.rect(3, 18, 12, 0.4, B4)
    t.rect(3, 19.5, 12, 0.5, B2)
    t.contour(O1)


@finition("sucette", auto=False)
def _sucette(t, k):
    """Sucette : spirale nette violet et bleu sur fond crème, croissant d'ombre, reflet, bâton éclairé à gauche."""
    vider(t)
    e = t.e
    cx, cy, R = 7.0, 6.6, 6.5
    for Y in range(t.H):
        for X in range(t.W):
            x_, y_ = (X + 0.5) / e - cx, (Y + 0.5) / e - cy
            r = math.hypot(x_, y_)
            if r > R or Y >= int(14 * e):
                continue
            th = math.atan2(y_, x_)
            ph = (r * 0.62 + th / math.pi) % 2.0
            c = V3 if ph < 0.62 else (B3 if 1.0 <= ph < 1.52 else CREME)
            if r < 0.9:
                c = V2
            t.pf(X, Y, c)
    croissant(t, cx, cy, R, R, {CREME}, CREME_O, (0.25, 0.25), 0.8)
    t.ell(4.4, 3.6, 1.4, 0.8, BLANC)
    arc(t, cx, cy, R - 0.9, R - 0.9, 200, 250, BLANC, {CREME, CREME_O})
    t.rect(6, 13.5, 2, 10.5, CREME_O)
    t.rect(6, 13.5, 0.6, 10.5, BLANC)
    t.rect(7.5, 13.5, 0.5, 10.5, GRIS_C)
    t.contour(V1)


@finition("pierre-calme", auto=False)
def _pierre(t, k):
    """Galet de calme : gris profond en dessous, dos plus clair, reflet doux, spirale bleue tracée au trait fin."""
    vider(t)
    e = t.e
    t.ell(7, 5.5, 6.8, 4.4, ARDOISE)
    t.ell(6.3, 4.7, 5.3, 3.2, GRIS)
    teinte_ell(t, 5.2, 3.5, 3.2, 1.7, {GRIS}, "#8c98a6", lambda u, v: -0.4 * u - 0.9 * v > 0.2)
    croissant(t, 6.3, 4.7, 5.3, 3.2, {GRIS}, "#5f6b79", (0.3, 0.3), 0.8)
    pts = []
    for i in range(150):
        a = i * 0.113
        r = 0.2 + i * 0.0225
        pts.append((7 + math.cos(a) * r * 1.5, 5 + math.sin(a) * r * 0.82))
    for (x, y) in pts:
        t.pf(int(x * e), int(y * e), B4)
    t.contour(ENCRE)


@finition("photo-flash", auto=False)
def _flash(t, k):
    """Éclat de flash : cœur blanc, halo crème en anneaux, quatre longs rayons et quatre courts qui s'effilent."""
    vider(t)
    e = t.e
    cx, cy = 10.5, 8.5
    t.ell(cx, cy, 4.2, 3.6, CREME)
    t.ell(cx, cy, 3.3, 2.8, "#fff6cc")
    for a, L in ((0, 10.2), (90, 8.2), (180, 10.2), (270, 8.2), (45, 5.4), (135, 5.4), (225, 5.4), (315, 5.4)):
        ar = math.radians(a)
        dx, dy = math.cos(ar), math.sin(ar)
        nx, ny = -dy, dx
        w = 1.0 if L > 6 else 0.7
        t.poly([(cx + nx * w, cy + ny * w), (cx + dx * L, cy + dy * L), (cx - nx * w, cy - ny * w)], "#fff6cc" if L > 6 else CREME)
        trait_fin(t, cx + dx * 2, cy + dy * 2, cx + dx * (L - 1.2), cy + dy * (L - 1.2), BLANC, 1)
    t.ell(cx, cy, 2.6, 2.2, BLANC)


@finition("pancarte", auto=False)
def _pancarte(t, k):
    """Pancarte de bois : cadre biseauté (lumière en haut, ombre en bas), clous, planche à reflets, poteau veiné."""
    e = t.e
    appliquer(t, "L:#a8703f O:#7a4b26 G:#a8703f D:#7a4b26 G:#7a4b26 D:#4a2e17")
    # Planche : liseré d'ombre en haut et à gauche, reflets en biais.
    for Y in range(int(3 * e), int(32 * e)):
        for X in range(int(2 * e), int(42 * e)):
            if t.g[Y][X] == CREME:
                if Y <= int(3 * e) + 1 or X <= int(2 * e) + 1:
                    t.g[Y][X] = "#e1e7ee"
                elif (X + Y) % 26 in (0, 1) and X < int(36 * e):
                    t.g[Y][X] = BLANC
    # Clous aux quatre coins du cadre.
    for (x, y) in ((1.0, 1.0), (42.6, 1.0), (1.0, 31.4), (42.6, 31.4)):
        X, Y = int(x * e), int(y * e)
        if t.getf(X, Y) in (BR2, "#a8703f", "#7a4b26", "#8f5a2f"):
            px(t, [(X, Y), (X + 1, Y)], "#545d68")
            t.pf(X, Y - 1, "#c9d1d9")
    # Veines du poteau.
    for Y in range(int(34 * e), int(42 * e), 3):
        X = int(21.2 * e) + (Y // 3) % 2
        if t.g[Y][X] == "#7a4b26":
            t.g[Y][X] = "#5f3a1e"


@finition("lanterne-courge", auto=False)
def _lanterne(t, k):
    """Lanterne-courge : côtes en relief, flanc éclairé à gauche, lueur dans les yeux et la bouche, queue éclairée."""
    e = t.e
    appliquer(t, "L:#f69d50 O:#f69d50 D:#f69d50 G:#fff6cc")
    for z in zones(t, "#fff6cc", 4, 300):
        X0 = min(x for x, y in z)
        Y0 = min(y for x, y in z)
        t.pf(X0, Y0, BLANC)
    appliquer(t, "L:#7a4b26")


@finition("macaron", auto=False)
def _macaron(t, k):
    appliquer(t, "L:#d2caff O:#d2caff D:#d2caff L:#ffffff")
    teinte_ell(t, 4.4, 3.6, 1.5, 0.7, {"#d2caff"}, "#ece8ff")


@finition("manette", auto=False)
def _manette(t, k):
    appliquer(t, "L:#adbac7 O:#adbac7 D:#adbac7 L:#3b4654")


@finition("nid-oiseau", auto=False)
def _nid(t, k):
    appliquer(t, "L:#f5d76e O:#f5d76e L:#7a4b26")


recette("parchemin-quete", texte="L:#e8d5b0 O:#e8d5b0 L:#c4a77d O:#c4a77d")
recette("pinceau", texte="G:#a86f3c D:#a86f3c L:#9b8cff")
recette("sucre-orge", texte="G:#f69d50 D:#f69d50")
recette("lampe-poche", texte="L:#b8c4d2 G:#6cb6ff")
recette("clavier-mini", texte="L:#545d68 O:#545d68")
recette("pelle-seau", texte="L:#f69d50 O:#f69d50 D:#f69d50 G:#ffd8b0 L:#4a8fdc")


@finition("guirlande", auto=False)
def _guirlande(t, k):
    """Guirlande : chaque ampoule a un petit éclat clair et une ombre."""
    for couleur in ("#9b8cff", "#6cb6ff", "#f5d76e", "#f69d50"):
        for z in zones(t, couleur, 6, 200):
            pts = sorted(z, key=lambda p: (p[1], p[0]))
            for (x, y) in pts[:2]:
                t.g[y][x] = clair(couleur, 0.55)
            for (x, y) in pts[-2:]:
                t.g[y][x] = sombre(couleur, 0.25)


# ======================================================================================================
# Reprises du lot précédent : plat-friture (trop chargé), soin-faim (sans finition propre), prise-ecrevisse (trop dense)
# ======================================================================================================
import finition_prises  # noqa: E402,F401  (pour que notre détail passe après celui du lot précédent)
from finition import detail, oeil  # noqa: E402

DORE = "#f2a94e"


@finition("plat-friture", auto=False)
def _friture(t, k):
    """Cornet de friture : papier en trois tons (lumière à gauche, ombre à droite), trois plis nets, bord roulé ;
    beignets dorés à un reflet chacun, sans trame."""
    vider(t)
    e = t.e
    t.poly([(2, 4), (24, 4), (21, 15), (5, 15)], BR3)
    for Y in range(t.H):
        for X in range(t.W):
            if t.g[Y][X] != BR3:
                continue
            x_, y_ = (X + 0.5) / e, (Y + 0.5) / e
            f = (x_ - 2 - (y_ - 4) * 0.27) / (22 - (y_ - 4) * 0.55)    # position dans la largeur du cornet
            if f < 0.14:
                t.g[Y][X] = eclaircir(BR3, 0.22)
            elif f > 0.8:
                t.g[Y][X] = BR2
            elif y_ > 13.8:
                t.g[Y][X] = assombrir(BR3, 0.12)
    for xf in (0.33, 0.55, 0.77):
        trait_fin(t, 2 + 22 * xf - 0.2, 5.2, 5 + 16 * xf, 14.6, BR2, 1)
    t.rect(2.4, 4.2, 21.2, 0.7, eclaircir(BR3, 0.35))
    for (x, y) in ((5, 3), (9, 2), (13, 3), (17, 2), (20, 3), (11, 1)):
        t.ell(x, y, 2.6, 2.0, DORE)
        croissant(t, x, y, 2.6, 2.0, {DORE}, "#d98f3c", (0.3, 0.3), 0.8)
        t.ell(x - 0.9, y - 0.7, 0.7, 0.45, J4)
    t.contour(BR1)


@finition("soin-faim", auto=False)
def _faim(t, k):
    """Bol fumant : bol rond avec soupe claire, ombre en bas à droite, rebord foncé, pied, deux volutes de vapeur."""
    vider(t)
    e = t.e
    t.ell(5.5, 4, 5, 5, O3, cond=lambda x, y, u, v: v > 0.05)
    croissant(t, 5.5, 4, 5, 5, {O3}, O2, (0.3, 0.2), 0.78)
    t.ell(5.5, 4.3, 4.4, 1.1, O4)
    t.ell(4.6, 4.1, 1.8, 0.4, O5)
    t.rect(0, 3.7, 11, 0.7, O2)
    t.rect(3, 9, 5, 1, O2)
    t.rect(3.4, 8.6, 4.2, 0.4, O2)
    teinte_ell(t, 3.4, 6.3, 0.9, 1.6, {O3}, O4)
    for (x0, ph) in ((3.2, 0.0), (6.8, 1.3)):
        for j in range(10):
            y = 3.0 - j * 0.3
            x = x0 + math.sin(j * 0.9 + ph) * 0.7
            t.pf(int(x * e), int(y * e), CREME_O if j < 7 else CREME_O + "88")
            t.pf(int(x * e) + 1, int(y * e), CREME_O if j < 5 else CREME_O + "88")
    t.contour(O1)


@detail("prise-ecrevisse")
def _ecrevisse(t):
    """Écrevisse : un peu de relief, pas de trame — carapace luisante, deux segments, yeux, une fente par pince."""
    d = assombrir(O2, 0.28)
    for xx in (11.0, 13.2):
        arc(t, xx, 10, 0.9, 3.4, -90, 90, d, {O2, O3})
    for xx in (19.6, 21.6):
        trait(t, xx, 8.5, xx, 11.5, assombrir(O3, 0.22), {O3})
    disque(t, 10.4, 8.4, 2.4, 0.8, eclaircir(O3, 0.45), {O3})
    oeil(t, 10.5, 7, 0.55, sur=None)
    oeil(t, 13.5, 7, 0.55, sur=None)
    for s in (-1, 1):
        x = 12 + s * 8
        trait(t, x - s * 0.6, 4.8, x + s * 1.8, 3.0, assombrir(O2, 0.4), {O2})


finition("prise-ecrevisse", auto=False)(lambda t, k: None)
