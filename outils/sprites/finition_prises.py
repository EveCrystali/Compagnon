"""Finition fine (2×) des prises de pêche (`prise-*`) : écailles, yeux ronds, nageoires à rayons, nacre, rivets.

Les coordonnées sont celles du dessin d'origine (grille 1×, avant rognage) ; les pinceaux de finition.py travaillent en
pixels fins et ne recouvrent que les couleurs du corps, jamais le cerne.
"""
import math

from finition import (detail, disque, trait, arc, points, poly, oeil, scintille, lisere_lateral, eclaircir, assombrir,
                      ENCRE, BLANC, CREME, CREME_O, GRIS, GRIS_C, ARDOISE, ARGENT, ARGENT_C, B1, B2, B3, B4, NUIT, O1, O2,
                      O3, O4, O5, J3, J4, V1, V2, V3, V4, S2, S3, T2, T3)


def poisson_fin(t, x, y, w, h, corps, clair, detail_c, queue, taches, lanterne):
    """Poissons de la pêche : œil rond, écailles en arcs, ouïe, reflet de dos, rayons de queue. Appelé par
    generer.poisson() pendant le dessin fin, avant le cerne."""
    e = t.e
    cx, cy = x + w * 0.45, y + h / 2
    qx = x + w * 0.83
    corps_sur = {corps, clair}
    sombre = assombrir(corps, 0.16)
    clair2 = eclaircir(corps, 0.3)
    # Œil : on efface le carré d'origine, puis anneau clair, pupille, reflet.
    ex, ey = int(cx - w * 0.28), int(cy - h * 0.15)
    for Y in range(ey * e, (ey + 2) * e):
        for X in range(ex * e, (ex + 2) * e):
            if t.getf(X, Y) is not None:
                t.g[Y][X] = corps
    oeil(t, ex + 1, ey + 1, 0.85 if h >= 10 else 0.75, fond=BLANC if corps != BLANC else CREME_O, sur=corps_sur)
    # Écailles : petits arcs décalés d'une rangée sur l'autre.
    lignes = max(2, int(h * 0.55 / 1.6)) if corps != "#f2a94e" and h < 16 else 0
    for j in range(lignes):
        yy = cy - h * 0.26 + j * 1.6
        Y = int(yy * e)
        x0 = cx - w * 0.1 + (j % 2) * 1.0
        n = int((qx - 3.5 - x0) / 2.0)
        for i in range(n):
            X = int((x0 + i * 2.0) * e)
            col = sombre if j % 2 == 0 else assombrir(clair, 0.1) if (x0 + i * 2.0) > cx else sombre
            points(t, [(X, Y), (X + 1, Y + 1), (X + 2, Y + 1), (X + 3, Y)], col, {corps})
    # Ouïe : arc qui enveloppe la tête.
    arc(t, cx - w * 0.09, cy, w * 0.07, h * 0.34, 105, 255, sombre, corps_sur)
    # Reflet de dos et ligne latérale.
    disque(t, cx + w * 0.02, cy - h * 0.3, w * 0.14, 0.55, eclaircir(corps, 0.42), {corps})
    trait(t, cx - w * 0.08, cy + h * 0.02, qx - 2.5, cy + h * 0.02, assombrir(clair, 0.08), {clair, corps})
    # Queue : rayons.
    for dy in (-0.42, -0.2, 0.0, 0.2, 0.42):
        trait(t, qx - 1.3, cy, x + w - 0.6, cy + h * dy, clair2, {corps})
    # Nageoire dorsale : deux rayons.
    trait(t, cx + 0.5, cy - h / 2 - 0.2, cx + 2.8, cy - h / 2 - 1.6, assombrir(detail_c, 0.1), {detail_c})
    trait(t, cx + 1.5, cy - h / 2 - 0.1, cx + 3.4, cy - h / 2 - 0.4, assombrir(detail_c, 0.1), {detail_c})
    # Bouche.
    trait(t, cx - w * 0.42 + 0.4, cy + h * 0.12, cx - w * 0.42 + 1.6, cy + h * 0.1, assombrir(corps, 0.3), corps_sur)
    if lanterne:
        # Leurre : éclat en croix.
        lx, ly = ex - 2.5, cy - h / 2 - 5
        scintille(t, int(lx * e), int(ly * e), BLANC, 3)


@detail("prise-algue")
def _algue(t):
    lisere_lateral(t, {B2, B3, T2})
    # Bulles d'air : reflet.
    for X in range(t.W):
        for Y in range(0, 6 * t.e):
            if t.g[Y][X] == B4:
                if t.getf(X - 1, Y - 1) == B4 and t.getf(X - 2, Y - 2) is not None and t.getf(X - 2, Y - 2) != B4:
                    t.g[Y][X] = BLANC
    # Nervure : un filet clair au cœur de chaque ruban.
    for Y in range(16, t.H - 4, 3):
        for X in range(1, t.W - 1):
            c = t.g[Y][X]
            if c in (B2, B3, T2) and t.g[Y][X - 1] == c and t.g[Y][X + 1] == c and (X + Y) % 7 == 0:
                t.g[Y][X] = eclaircir(c, 0.25)


@detail("prise-botte")
def _botte(t):
    sur = {GRIS, GRIS_C, ARDOISE}
    # Coutures du bas de tige et de la semelle.
    for X in range(2 * 2, 17 * 2, 3):
        points(t, [(X, 17 * 2 + 1)], eclaircir(GRIS, 0.4), {GRIS})
    for X in range(2 * 2, 17 * 2, 4):
        points(t, [(X, 19 * 2 + 1), (X + 1, 19 * 2 + 1)], eclaircir(ARDOISE, 0.3), {ARDOISE})
    # Plis du cuir à la cheville.
    trait(t, 5.5, 12.4, 11.5, 13.2, assombrir(GRIS, 0.3), {GRIS})
    trait(t, 6.5, 13.6, 12, 14.4, assombrir(GRIS, 0.25), {GRIS})
    # Lacets : œillets ronds.
    for yy in (5, 8, 11):
        disque(t, 10.4, yy + 0.5, 0.7, 0.5, assombrir(GRIS_C, 0.35), {GRIS_C})
        trait(t, 10.2, yy + 0.5, 11.8, yy + 0.5, eclaircir(GRIS_C, 0.6), {GRIS_C})
    # Taches de vase.
    points(t, [(9, 30), (12, 33), (20, 28), (24, 31), (27, 33), (15, 35)], assombrir(GRIS, 0.35), {GRIS})
    # Revers du haut : ourlet clair.
    trait(t, 4.4, 1.3, 12.6, 1.3, eclaircir(ARDOISE, 0.45), {ARDOISE})
    # Goutte du bout : reflet.
    points(t, [(30, 42)], BLANC, {B3})


@detail("prise-caillou")
def _caillou(t):
    sur = {GRIS_C, CREME_O, "#909dab"}
    # Grain de la pierre : points clairs et sombres.
    pts = [(10, 9), (14, 14), (22, 8), (27, 12), (31, 17), (18, 17), (9, 15), (24, 5), (12, 5), (28, 7)]
    points(t, pts[::2], assombrir(GRIS_C, 0.2), {GRIS_C, "#909dab"})
    points(t, [(x + 3, y + 3) for x, y in pts[1::3]], eclaircir(GRIS_C, 0.45), {GRIS_C, CREME_O})
    # Veine de quartz et fissure.
    trait(t, 4, 17, 15, 13, eclaircir(GRIS_C, 0.55), {GRIS_C, "#909dab"})
    trait(t, 22, 6, 26, 11, assombrir(GRIS_C, 0.35), {GRIS_C})
    trait(t, 26, 11, 25, 14, assombrir(GRIS_C, 0.35), {GRIS_C})
    # Reflet mouillé.
    scintille(t, 12, 8, BLANC, 2)


@detail("prise-ecrevisse")
def _ecrevisse(t):
    sur = {O1, O2, O3}
    d = assombrir(O2, 0.28)
    # Segments du corps et de l'abdomen.
    for xx in (9.6, 11.4, 13.4):
        arc(t, xx, 10, 0.9, 3.6, -90, 90, d, {O2, O3})
    for xx in (18.8, 20.6, 22.0):
        trait(t, xx, 8.3, xx, 11.7, assombrir(O3, 0.25), {O3})
    # Carapace luisante.
    disque(t, 10.6, 8.3, 2.6, 0.9, eclaircir(O3, 0.5), {O3})
    # Yeux sur tiges.
    oeil(t, 10.5, 7, 0.55, sur=None)
    oeil(t, 13.5, 7, 0.55, sur=None)
    # Pinces : fente et reflet.
    for s in (-1, 1):
        x = 12 + s * 8
        trait(t, x - s * 0.6, 4.8, x + s * 1.8, 3.0, assombrir(O2, 0.4), {O2})
        points(t, [(int((x - s * 1.6) * 2), 8)], eclaircir(O2, 0.5), {O2})
        trait(t, 12 + s * 4, 8, x - s * 1.5, 7, assombrir(O2, 0.2), {O2})


@detail("prise-spirale")
def _spirale(t):
    # Sillon sombre entre deux tours, un peu au large du ruban.
    for k in range(0, 900):
        a = k * 0.014
        r = 0.9 + a * 0.75 + 1.25
        X, Y = int((10 + math.cos(a) * r) * t.e), int((10 + math.sin(a) * r) * t.e)
        if 0 <= Y < t.H and 0 <= X < t.W and t.g[Y][X] in (CREME, CREME_O):
            t.g[Y][X] = assombrir(CREME_O, 0.22)
    # Cœur de la coquille.
    disque(t, 9.8, 9.8, 1.7, 1.7, O4, {O4, O3, CREME, CREME_O})
    disque(t, 9.4, 9.4, 0.8, 0.8, O5, {O4, O3})
    scintille(t, 7, 7, BLANC, 1)


@detail("prise-bouteille")
def _bouteille(t):
    sur = {B3, B4, CREME, GRIS}
    # Bouchon : veines et bord.
    points(t, [(8, 1), (11, 3), (14, 2), (17, 4), (9, 5)], assombrir("#a86f3c", 0.3), {"#a86f3c"})
    trait(t, 3.3, 1.2, 8.7, 1.2, eclaircir("#a86f3c", 0.35), {"#a86f3c"})
    # Col : anneau de verre.
    trait(t, 3.6, 5.2, 8.4, 5.2, eclaircir(B3, 0.5), {B3})
    # Reflet de verre long, en arc, à gauche.
    arc(t, 6, 15, 4.4, 7.2, 150, 205, BLANC, {B3, B4})
    points(t, [(10, 26), (10, 27), (10, 28)], BLANC, {B4})
    # Fond du verre : épaisseur.
    arc(t, 6, 15, 4.6, 8.0, 40, 140, assombrir(B3, 0.35), {B3})
    # Étiquette : coin plié, lignes de texte, cachet.
    trait(t, 3, 12.4, 3, 18.8, CREME_O, {CREME})
    for yy, n in ((13.5, 5), (14.9, 4), (16.2, 5), (17.5, 3)):
        trait(t, 3.9, yy, 3.9 + n * 0.55, yy, assombrir(GRIS, 0.1), {CREME})
    poly(t, [(8, 12), (9, 12), (9, 13.2)], CREME_O, {CREME})
    disque(t, 6.3, 11.5, 0.8, 0.8, O3, {B3, B4, CREME})
    points(t, [(12, 22)], O5, {O3})
    # Bulles dans le goulot.
    points(t, [(8, 11), (9, 13), (8, 15)], BLANC, {B3, B4})


@detail("prise-anguille")
def _anguille(t):
    e = t.e
    # Œil rond.
    for Y in range(8, 12):
        for X in range(8, 12):
            if t.g[Y][X] in (ENCRE, BLANC):
                t.g[Y][X] = "#2a5ea8"
    oeil(t, 5, 5, 0.8, fond=B3, sur={"#2a5ea8", B3})
    # Ligne latérale et reflet de dos le long de l'ondulation.
    for xx in range(8, 112):
        x = xx / 4.0
        if x > 29:
            break
        y = 5 + math.sin(x / 4) * 2.5
        if xx % 9 == 0:
            points(t, [(int(x * e), int((y - 0.6) * e))], eclaircir("#2a5ea8", 0.3), {"#2a5ea8"})
        if xx % 2 == 0:
            points(t, [(int(x * e), int((y - 1.9) * e))], "#3b72c2", {"#2a5ea8"})
    # Bouche et branchie.
    trait(t, 3.2, 6.4, 5.0, 6.7, "#10305e", {"#2a5ea8"})
    arc(t, 7.6, 5, 0.8, 1.8, 100, 260, "#16407a", {"#2a5ea8", B3})


@detail("prise-crabe")
def _crabe(t):
    d = assombrir(B3, 0.25)
    # Carapace : sillons, reflet et petites taches.
    arc(t, 13, 9, 4.4, 2.5, 200, 340, d, {B3, B4})
    arc(t, 13, 10.5, 3.2, 1.2, 20, 160, d, {B3, B4})
    disque(t, 11, 7.6, 1.8, 0.6, BLANC, {B4})
    points(t, [(21, 17), (26, 17), (31, 18)], B2, {B4})
    # Yeux ronds sur leur tige.
    for ex in (11.5, 15.5):
        oeil(t, ex, 6.8, 0.6, sur=None)
    # Pinces : fente sombre et reflet.
    for s in (-1, 1):
        x = 13 + s * 9
        trait(t, x - s * 0.5, 4.8, x + s * 1.6, 3.4, B1, {B3})
        points(t, [(int((x - s * 1.4) * 2), 5)], BLANC, {B3, B4})
        # Joint de patte.
        for i in range(3):
            xx = 13 + s * (4 + i * 2)
            points(t, [(int(xx * 2 + s), 28)], B1, {B2, B3})
    # Bouche : petit sourire.
    arc(t, 13, 11.2, 1.3, 0.7, 20, 160, B1, {B3, B4})


@detail("prise-cle")
def _cle(t):
    O = "#c97a28"
    cl = eclaircir(O, 0.38)
    sb = assombrir(O, 0.3)
    # Anneau en relief : lumière en haut à gauche, ombre en bas à droite.
    arc(t, 5.5, 6, 4.7, 4.7, 170, 285, cl, {O})
    arc(t, 5.5, 6, 4.4, 4.4, 175, 275, cl, {O})
    arc(t, 5.5, 6, 4.7, 4.7, 350, 100, sb, {O})
    arc(t, 5.5, 6, 2.9, 2.9, 190, 280, sb, {O})
    arc(t, 5.5, 6, 2.9, 2.9, 10, 100, cl, {O})
    # Tige : filets de lumière et d'ombre, gravure.
    trait(t, 10.3, 5.3, 24.6, 5.3, cl, {O})
    trait(t, 10.3, 7.4, 24.6, 7.4, sb, {O})
    for xx in (13, 15.5, 18):
        trait(t, xx, 6.2, xx + 1.2, 6.2, sb, {O})
    # Dents : biseau.
    for xx in (19, 23):
        trait(t, xx, 8.3, xx, 10.8, sb, {O})
        trait(t, xx + 1.7, 8.3, xx + 1.7, 10.8, cl, {O})
    # Rivets ronds.
    for (xx, yy) in ((3.2, 2.9), (7.8, 2.9), (3.2, 9.3), (7.8, 9.3)):
        disque(t, xx, yy, 0.6, 0.6, O1, {O})
        points(t, [(int((xx - 0.3) * 2), int((yy - 0.3) * 2))], O4, {O1})


@detail("prise-pieuvre")
def _pieuvre(t):
    for ex in (9, 15):
        for Y in range(15, 22):
            for X in range(2 * ex - 3, 2 * ex + 3):
                if t.getf(X, Y) in (ENCRE, BLANC):
                    t.g[Y][X] = V3
        oeil(t, ex, 9, 0.85, fond=V4, sur={V3, V4})
    # Taches de la tête.
    for (xx, yy, r) in ((7, 4, 0.7), (16.5, 3.5, 0.6), (13, 5.3, 0.5), (19, 7, 0.5)):
        disque(t, xx, yy, r, r * 0.8, V4, {V3})
    # Joues.
    disque(t, 6.2, 11.2, 1.2, 0.7, "#c7a4ff", {V3})
    disque(t, 17.8, 11.2, 1.2, 0.7, "#c7a4ff", {V3})
    # Ventouses : paires de points clairs le long de chaque tentacule.
    for X in range(10, 48):
        for Y in range(27, 41):
            if t.g[Y][X] in (V3, V2) and (Y % 4 == 1) and (X + Y // 4) % 5 == 0 and t.getf(X - 1, Y) == t.g[Y][X] and t.getf(X + 1, Y) == t.g[Y][X]:
                t.g[Y][X] = V4 if t.g[Y][X] == V3 else V3
    # Bouche.
    trait(t, 11, 11.6, 13, 11.6, V1, {V3, V1})
    arc(t, 12, 11.2, 0.8, 0.6, 20, 160, V1, {V3})


@detail("prise-hippocampe")
def _hippocampe(t):
    O = "#f2a94e"
    for Y in range(4, 12):
        for X in range(14, 20):
            if t.getf(X, Y) == ENCRE:
                t.g[Y][X] = O
    oeil(t, 8, 4, 0.75, sur={O})
    # Anneaux du ventre : arcs fins.
    for yy in (9, 11, 13, 15, 17):
        arc(t, 7, yy, 3.2, 1.1, 10, 170, assombrir(O, 0.28), {O, "#ffe7b8"})
    # Épines de la nuque.
    for (xx, yy) in ((10, 1), (11.5, 2.4), (12, 4)):
        points(t, [(int(xx * 2), int(yy * 2))], assombrir(O, 0.3), {O})
    # Nageoire dorsale : rayons.
    for dy in (-1.5, 0, 1.5):
        trait(t, 3.2, 10 + dy * 0.4, 0.8, 10 + dy, eclaircir("#c97a28", 0.35), {"#c97a28"})
    # Museau : narine.
    points(t, [(24, 7)], assombrir(O, 0.4), {O})
    # Queue enroulée : crête claire.
    arc(t, 5, 24, 1.8, 1.7, 180, 300, eclaircir(O, 0.4), {O})


@detail("prise-coffre")
def _coffre(t):
    bois, bois_c = "#c97a28", "#f2a94e"
    bs = assombrir(bois, 0.3)
    # Planches du coffre.
    for xx in (5.5, 15.5):
        trait(t, xx, 9.2, xx, 14.8, bs, {bois})
    trait(t, 1.5, 12, 8.4, 12, bs, {bois})
    trait(t, 13.6, 12, 20.5, 12, bs, {bois})
    # Couvercle : veines arrondies et reflet.
    for rr in (4, 7):
        arc(t, 11, 9, rr + 1.2, 4.2, 200, 340, assombrir(bois_c, 0.18), {bois_c})
    disque(t, 6, 5.6, 3.2, 0.7, eclaircir(bois_c, 0.5), {bois_c})
    # Bandes de métal : rivets.
    for xx in (2.5, 5.5, 15.5, 18.5):
        for yy in (8, 16):
            disque(t, xx, yy, 0.55, 0.55, eclaircir(ARDOISE, 0.55), {ARDOISE})
    # Serrure : biseau, trou de serrure rond.
    trait(t, 9.2, 8.2, 12.8, 8.2, J4, {J3})
    trait(t, 9.2, 12.8, 12.8, 12.8, "#c9a227", {J3})
    for Y in range(18, 26):
        for X in range(18, 26):
            if t.getf(X, Y) == ENCRE:
                t.g[Y][X] = J3
    disque(t, 11, 10, 0.7, 0.7, ENCRE, {J3})
    poly(t, [(10.6, 10), (11.4, 10), (11.7, 11.6), (10.3, 11.6)], ENCRE, {J3})
    # Étincelles.
    for (xx, yy, c) in ((3, 4, B3), (17, 3, B4), (15, 12, J4)):
        for Y in range(int(yy * 2) - 2, int(yy * 2) + 4):
            for X in range(int(xx * 2) - 2, int(xx * 2) + 4):
                if t.getf(X, Y) in (c,) and yy < 8:
                    t.g[Y][X] = None
        if yy < 8:
            scintille(t, int(xx * 2) + 1, int(yy * 2) + 1, c, 2)
    points(t, [(30, 24)], BLANC, {bois})


@detail("prise-raie")
def _raie(t):
    # Étoiles : croix fines au lieu de croix de gros pixels.
    for (xx, yy) in ((10, 8), (17, 7), (14, 11)):
        for Y in range(yy * 2 - 3, yy * 2 + 5):
            for X in range(xx * 2 - 3, xx * 2 + 5):
                if t.getf(X, Y) in (O5, J4):
                    t.g[Y][X] = V3
        scintille(t, xx * 2 + 1, yy * 2 + 1, O5 if yy < 11 else J4, 2)
        points(t, [(xx * 2 + 1, yy * 2 + 1)], BLANC)
    # Nervures des ailes.
    d = assombrir(V3, 0.12)
    for (x1, y1) in ((6, 8.6), (9, 10.6), (19, 10.6), (22, 8.6)):
        trait(t, 14, 9, x1, y1, d, {V3})
    # Rebord clair de l'aile.
    trait(t, 5.5, 9, 14, 3.4, eclaircir(V2, 0.3), {V2})
    trait(t, 14, 3.4, 22.5, 9, eclaircir(V2, 0.3), {V2})
    # Yeux et sourire.
    for ex in (11.5, 16.5):
        for Y in range(8, 14):
            for X in range(2 * int(ex) - 1, 2 * int(ex) + 4):
                if t.getf(X, Y) == ENCRE:
                    t.g[Y][X] = V3
        oeil(t, ex, 5.5, 0.6, fond=V4, sur={V3, V4})
    arc(t, 14, 8, 2.0, 1.0, 20, 160, V1, {V3})
    # Queue : arête sombre.
    trait(t, 14.4, 15, 15.2, 18.6, assombrir(V2, 0.3), {V2})


@detail("prise-perle")
def _perle(t):
    # Coquille : stries rayonnantes depuis la charnière.
    d = assombrir(S3, 0.16)
    for (x1, y1) in ((2, 11), (3.4, 13), (6, 14.6), (9, 15.2), (12, 14.6), (14.6, 13), (16, 11)):
        trait(t, 9, 8.5, x1, y1, d, {S3})
    arc(t, 9, 10, 8.0, 5.0, 20, 160, assombrir(S3, 0.3), {S3})
    # Perle : nacre irisée (bleu pâle, violet pâle, crème), reflet net.
    arc(t, 9, 7, 5.0, 5.0, 20, 130, "#c9c1ff", {ARGENT_C})
    arc(t, 9, 7, 4.3, 4.3, 30, 120, "#bfe0ff", {ARGENT_C})
    disque(t, 11.2, 9.3, 1.6, 1.3, V4, {ARGENT_C, V4})
    disque(t, 7.5, 5.5, 1.5, 1.5, BLANC, {ARGENT_C, BLANC})
    scintille(t, 14, 11, BLANC, 2)
    points(t, [(24, 10)], O5, {ARGENT_C})


@detail("prise-comete")
def _comete(t):
    for Y in range(8, 14):
        for X in range(6, 14):
            if t.getf(X, Y) == ENCRE:
                t.g[Y][X] = O5
    oeil(t, 5, 6, 0.8, fond=BLANC, sur={O5, BLANC})
    # Tête : halo clair et reflet.
    disque(t, 6.2, 4.2, 1.8, 0.9, BLANC, {O5, BLANC})
    # Traînée : filets plus clairs au cœur et poussière.
    for X in range(26, t.W - 4, 2):
        Y = 12
        if t.getf(X, Y) in (O3, O4):
            t.g[Y][X] = eclaircir(O4, 0.4)
    # Étincelles en croix fine.
    for (xx, yy) in ((20, 2), (26, 9), (30, 4)):
        for Y in range(yy * 2 - 1, yy * 2 + 3):
            for X in range(xx * 2 - 1, xx * 2 + 3):
                if t.getf(X, Y) == BLANC:
                    t.g[Y][X] = None
        scintille(t, xx * 2, yy * 2, BLANC, 2)


@detail("prise-baleineau")
def _baleineau(t):
    for Y in range(16, 24):
        for X in range(10, 18):
            if t.getf(X, Y) == ENCRE:
                t.g[Y][X] = B4
    oeil(t, 7, 10, 0.85, fond=BLANC, sur={B4, BLANC})
    # Sillons du ventre.
    for dy in (0.0, 1.2, 2.4):
        arc(t, 14, 13.2 + dy, 10.5, 3.6, 25, 155, assombrir(BLANC, 0.1), {BLANC})
    # Joue.
    disque(t, 4.2, 13, 2.4, 1.3, O4, {O4, B4, BLANC})
    # Jet : gouttes rondes.
    for (xx, yy, r) in ((7.5, 2.5, 1.0), (5.5, 1.2, 0.7), (9.5, 0.6, 0.6)):
        disque(t, xx, yy, r, r, BLANC, {BLANC})
        points(t, [(int((xx - r * 0.4) * 2), int((yy - r * 0.4) * 2))], B4, {BLANC})
    # Queue : rayons.
    for dy in (-5, -2.5, 0, 2.5, 5):
        trait(t, 26, 10, 32.5, 10 + dy, B3, {B4})
    # Reflet de dos.
    disque(t, 14, 5.3, 6, 0.7, BLANC, {B4})
