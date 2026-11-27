"""Finition fine (2×) des décors de boutique (`fond-*`, scènes de 64 × 48 devenues 128 × 96).

Chaque décor est repeint en entier à la finesse double, à la même composition que le 1× (mêmes masses, mêmes
couleurs, mêmes images animées) : ciel en dégradé tramé, astres avec halo, reliefs à crête éclairée, détails fins
(étoiles à branches, fenêtres, feuilles, pétales). `finition(..., auto=False)` : pas de lumière automatique, tout est dit ici.
"""
import math

from finition import (finition, disque, trait, arc, points, poly, scintille, degrade_v, eclaircir, assombrir,
                      ENCRE, NOIR2, BLANC, CREME, CREME_O, GRIS, GRIS_C, ARDOISE, ARGENT, ARGENT_C, B1, B2, B3, B4,
                      NUIT, NUIT2, O1, O2, O3, O4, O5, J1, J2, J3, J4, V1, V2, V3, V4, S1, S2, S3, BR1, BR2, BR3, T1, T2, T3)

ROSE = "#ff9ec7"
CAFE, CAFE2, MOUSSE = "#3b2416", "#5c3a22", "#e8d5b0"
W, H = 64, 48


def vider(t):
    for r in t.g:
        for X in range(len(r)):
            r[X] = None


def rect(t, x, y, w, h, c):
    t.rect(x, y, w, h, c)


def ellipse(t, cx, cy, rx, ry, c, cond=None):
    t.ell(cx, cy, rx, ry, c, cond)


def halo(t, cx, cy, r, pas=2.0, n=3, k=0.07):
    """Halo tramé autour d'un astre : n anneaux, chacun un damier un peu plus clair que ce qu'il recouvre."""
    e = t.e
    for i in range(n, 0, -1):
        rr = r + i * pas
        for Y in range(max(0, int((cy - rr) * e)), min(t.H, int((cy + rr) * e) + 1)):
            for X in range(max(0, int((cx - rr) * e)), min(t.W, int((cx + rr) * e) + 1)):
                if ((X + 0.5) / e - cx) ** 2 + ((Y + 0.5) / e - cy) ** 2 <= rr * rr and (X + Y) % 2 == 0 and t.g[Y][X]:
                    t.g[Y][X] = eclaircir(t.g[Y][X], k * (n - i + 1))


def croissant(t, cx, cy, r, dx, dy, r2, c, ombre=None):
    """Disque (cx, cy, r) privé du disque (cx + dx, cy + dy, r2)."""
    e = t.e
    for Y in range(int((cy - r) * e) - 1, int((cy + r) * e) + 2):
        for X in range(int((cx - r) * e) - 1, int((cx + r) * e) + 2):
            x, y = (X + 0.5) / e, (Y + 0.5) / e
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r and (x - cx - dx) ** 2 + (y - cy - dy) ** 2 > r2 * r2:
                t.pf(X, Y, c)


def etoile(t, x, y, c, r=2, k=0):
    """Étoile à quatre branches centrée sur le point (x, y) de la grille 1× ; k > 0 : version plus grande."""
    scintille(t, int(x * t.e), int(y * t.e), c, r + k)


def relief(t, f, c, clair=None, sombre=None, y_max=None, haut=1):
    """Remplit sous la courbe y = f(x) (x en grille 1×, par pixel fin) ; crête éclairée, pied plus sombre."""
    e = t.e
    ym = t.H if y_max is None else int(y_max * e)
    for X in range(t.W):
        Y0 = int(f((X + 0.5) / e) * e)
        for Y in range(max(0, Y0), ym):
            t.g[Y][X] = c
        if clair:
            for d in range(haut):
                if 0 <= Y0 + d < t.H and Y0 + d < ym:
                    t.g[Y0 + d][X] = clair
        if sombre and Y0 + 6 < ym and (X % 2 == 0):
            for d in range(4, 6):
                if 0 <= Y0 + d < t.H:
                    t.g[Y0 + d][X] = sombre


def sapin(t, x, base, h, larg, c, clair=None, etages=4):
    """Sapin en étages (grille 1×) : triangles superposés, flanc gauche éclairé."""
    for i in range(etages):
        f0, f1 = i / etages, (i + 1) / etages
        y0, y1 = base - h + h * f0 * 0.85, base - h + h * (f1 * 0.85 + 0.15)
        w0, w1 = larg * (0.4 + 0.9 * f0), larg * (0.4 + 0.9 * f1)
        t.poly([(x, y0), (x + w1 / 2, y1), (x - w1 / 2, y1)], c)
        if clair:
            trait(t, x, y0 + 0.2, x - w1 / 2 + 0.3, y1 - 0.2, clair, {c})


@finition("fond-nuit", auto=False)
def _nuit(t, k):
    vider(t)
    degrade_v(t, 0, 48, 0, 64, ["#081a33", NUIT, NUIT2, "#1c4373"])
    # Voie lactée : bande diagonale de poussière claire.
    for i in range(160):
        a = i * 2.399
        u = (i * 0.37) % 1.0
        x, y = 4 + u * 56, 24 - u * 22 + math.sin(a) * 3.0
        points(t, [(int(x * 2), int(y * 2))], "#27508a" if i % 3 else "#3a68a6")
    halo(t, 50, 10, 5.0, 2.0, 3, 0.06)
    croissant(t, 50, 10, 5, 2.4, -0.8, 4.4, J4)
    points(t, [(96, 21), (97, 22), (94, 18)], J3)
    for i, (x, y) in enumerate(((6, 5), (14, 12), (22, 4), (31, 9), (40, 3), (9, 20), (27, 18), (58, 22), (45, 17))):
        if (i + k) % 2:
            etoile(t, x + 0.5, y + 0.5, J4 if i % 2 else B4, 2 + (i % 3 == 0))
        else:
            points(t, [(int(x * 2), int(y * 2)), (int(x * 2) + 1, int(y * 2))], J4 if i % 2 else B4)
    # Collines : crête éclairée, sapins en silhouette, maison à fenêtre éclairée.
    relief(t, lambda x: 38 + (x - 50) ** 2 / 90 if x > 28 else 99, "#122f55", "#2a5a96", None, haut=2)
    relief(t, lambda x: 38.5 + ((x - 14) / 26) ** 2 * 11.5 if x < 40 else 99, B1, B2, None, haut=2)
    for (x, b, h) in ((46, 42, 8), (52, 41.5, 10), (58, 42, 7), (7, 45, 9), (20, 47, 7)):
        sapin(t, x, b, h, h * 0.55, "#0a1f3d" if x > 40 else "#163c70", None, 3)
    rect(t, 32, 42, 5, 3, "#0a1f3d")
    t.poly([(31.4, 42), (34.5, 39.6), (37.6, 42)], "#0a1f3d")
    rect(t, 33.5, 43, 1.5, 1.5, J3)
    for X in range(20, 30, 3):
        for Y in range(76, 92):
            if t.g[Y][X] in (B1,):
                t.g[Y][X] = "#1b4c8c" if (X + Y) % 4 == 0 else B1


@finition("fond-foret", auto=False)
def _foret(t, k):
    vider(t)
    degrade_v(t, 0, 40, 0, 64, ["#0d2a40", "#12324a", "#1b4560", "#2b6079"])
    disque(t, 14, 8, 3, 3, "#c9e4f2", None)   # lune pâle derrière les branches
    halo(t, 14, 8, 3, 2.0, 3, 0.05)
    # Deux rangs de sapins : le fond brumeux, l'avant plus saturé et éclairé à gauche.
    for i, x in enumerate(range(-2, 66, 9)):
        h = 18 + (i * 7) % 10
        sapin(t, x + 4.5, 46, h, 9.5, B1 if i % 2 else T2, B3 if i % 2 else T3, 5)
    degrade_v(t, 36, 40, 0, 64, ["#2f6a86", "#2b6079", "#255567"])
    rect(t, 0, 40, 64, 8, T1)
    for x in range(0, 64, 2):
        points(t, [(x * 2, 76 + (x // 2 + k) % 2 * 2)], "#5c8fa8")
    for i in range(0, 64, 3):
        trait(t, i, 41, i + 2, 43 + i % 2, "#1a6382", {T1})
    # Brume : bandes tramées entre les troncs.
    for Y in range(60, 78):
        for X in range(128):
            if (X + Y) % 2 == 0 and (Y - 62) % 8 < 1:
                c = t.g[Y][X]
                if c:
                    t.g[Y][X] = eclaircir(c, 0.1)
    # Lucioles : étoile fine et halo.
    for i, (x, y) in enumerate(((10, 30), (30, 26), (52, 32), (42, 18))):
        if (i + k) % 2 == 0:
            etoile(t, x + 0.5, y + 0.5, J3, 1)
            points(t, [(x * 2, y * 2 + 2)], J4)
        else:
            points(t, [(x * 2, y * 2)], J3)


@finition("fond-plage", auto=False)
def _plage(t, k):
    vider(t)
    degrade_v(t, 0, 24, 0, 64, [B3, B4, "#d8ecff"])
    # Soleil : disque, halo, rayons courts.
    halo(t, 12, 10, 5.0, 2.0, 3, 0.05)
    disque(t, 12, 10, 6, 6, J3, None)
    disque(t, 12, 10, 4.3, 4.3, J4, None)
    disque(t, 11, 8.6, 1.4, 1.0, BLANC, None)
    for a in range(0, 360, 45):
        x, y = 12 + math.cos(math.radians(a)) * 8.2, 10 + math.sin(math.radians(a)) * 8.2
        trait(t, x, y, 12 + math.cos(math.radians(a)) * 9.6, 10 + math.sin(math.radians(a)) * 9.6, J3, None)
    # Nuage lointain.
    for (x, y, rx, ry) in ((35, 8, 5, 1.6), (38, 7, 4, 1.8), (41, 8.2, 3, 1.3)):
        disque(t, x, y, rx, ry, BLANC, None)
    t.pf(60, 14, BLANC)
    # Mer : bandes de plus en plus sombres, vaguelettes crème et reflet du soleil.
    degrade_v(t, 24, 36, 0, 64, ["#6cb6ff", B2, "#3d7fcc", "#3472bb"])
    rect(t, 0, 24, 64, 0.5, B4)
    for y in (26, 29, 32, 34.5):
        for x in range(0, 64, 6):
            xx = x + (k * 3) % 6 + (y % 3)
            trait(t, xx, y, xx + 2.5, y, B4 if y < 30 else "#8fc4ff", None)
    for i in range(6):
        trait(t, 10 + (k * 2) % 4, 25 + i * 1.2, 15 + (k * 2) % 4 - i * 0.4, 25 + i * 1.2, J4, None)
    # Plage : sable en dégradé, grains, coquillages.
    degrade_v(t, 36, 48, 0, 64, [S3, "#dcc79c", S2])
    rect(t, 0, 36, 64, 1, "#f4ead2")
    for x in range(1, 64, 3):
        points(t, [(x * 2 + (x % 2), 80 + (x * 7) % 14)], S2 if x % 2 else "#f4ead2")
    for X in range(0, 128):
        t.g[72][X] = "#f6efe0" if (X + k) % 5 < 3 else B4   # frange d'écume
    disque(t, 52, 42, 3, 1.5, O4, None)
    arc(t, 52, 42, 2.5, 1.3, 190, 350, O3, None)
    for a in range(5):
        trait(t, 52, 43, 49.6 + a * 1.2, 41.2, O3, None)
    # Parasol : mât, calotte à lamelles crème, nervures, ombre sur le sable.
    rect(t, 48, 24, 0.7, 14, BR2)
    trait(t, 48.1, 24, 48.1, 38, BR3, None)
    t.ell(48.5, 25.5, 9.5, 5.5, O3, cond=lambda x, y, u, v: v < 0)
    for Y in range(0, 52):
        for X in range(76, 118):
            if t.g[Y][X] == O3 and ((X - 76) // 4) % 2 == 1:
                t.g[Y][X] = CREME
    arc(t, 48.5, 25.5, 9.2, 5.2, 195, 345, O4, {O3, CREME})
    trait(t, 39, 25.5, 58, 25.5, O2, {O3, CREME})
    for x in (43, 48.5, 54):
        trait(t, 48.5, 20.2, x, 25.4, O2, {O3, CREME})
    disque(t, 48.5, 41.5, 7, 1.0, "#c9b387", {S3, "#dcc79c", S2})


@finition("fond-arcade", auto=False)
def _arcade(t, k):
    vider(t)
    degrade_v(t, 0, 48, 0, 64, ["#10152a", "#151a2e", "#1a2038"])
    # Néons sur le mur : tubes lumineux et halo.
    for y, c in ((6, V3 if k else B3), (8, O3 if k else V3)):
        rect(t, 0, y, 64, 1, c)
        for X in range(0, 128):
            if X % 2 == 0:
                for Y in (int(y * 2) - 1, int(y * 2) + 2):
                    if 0 <= Y < t.H:
                        t.g[Y][X] = assombrir(c, 0.55)
    # Trois bornes : fût, pans éclairés, écran à reflets, commandes rondes.
    for i, x in enumerate((4, 26, 48)):
        ecr = (B3, O3, V3)[(i + k) % 3]
        rect(t, x, 14, 12, 24, V1)
        rect(t, x, 14, 1, 24, V2)
        rect(t, x + 11, 14, 1, 24, "#2a1c5c")
        t.poly([(x - 1, 14), (x + 13, 14), (x + 11, 11), (x + 1, 11)], V2)
        rect(t, x + 2, 16, 8, 7, "#0c0f22")
        rect(t, x + 2.5, 16.5, 7, 6, ecr)
        rect(t, x + 3, 17, 3, 2, BLANC)
        for r in range(0, 6, 2):
            trait(t, x + 2.5, 17 + r + 0.5, x + 9.5, 17 + r + 0.5, assombrir(ecr, 0.2), {ecr})
        rect(t, x + 2, 25, 8, 4, "#2a1c5c")
        disque(t, x + 3.5, 27.5, 1.0, 1.0, O3, None)
        disque(t, x + 3.2, 27.2, 0.35, 0.35, O5, None)
        disque(t, x + 8, 27.5, 1.0, 1.0, B3, None)
        disque(t, x + 7.7, 27.2, 0.35, 0.35, B4, None)
        rect(t, x + 2, 31, 8, 1, "#0c0f22")
        rect(t, x + 3, 33, 6, 4, "#3a2a7a")
    # Sol à damier en perspective, reflet des écrans.
    for y in range(38, 48, 2):
        for x in range(0, 64, 2):
            rect(t, x, y, 2, 2, "#262c45" if (x // 2 + y // 2) % 2 == 0 else "#1a1f36")
    for i, x in enumerate((4, 26, 48)):
        ecr = (B3, O3, V3)[(i + k) % 3]
        for Y in range(76, 90):
            for X in range(x * 2 + 4, x * 2 + 20):
                if (X + Y) % 2 == 0 and abs(X - (x * 2 + 12)) < 8 - (Y - 76) * 0.5:
                    t.g[Y][X] = assombrir(ecr, 0.55)


@finition("fond-espace", auto=False)
def _espace(t, k):
    vider(t)
    degrade_v(t, 0, 48, 0, 64, ["#05061a", "#090b1f", "#0e0d2e"])
    # Nébuleuse : volutes tramées violettes et bleues.
    for (cx, cy, rx, ry, c) in ((18, 30, 22, 10, "#1f1846"), (24, 28, 12, 5, "#2e2466"), (10, 34, 8, 4, "#3a2a7a")):
        disque(t, cx, cy, rx, ry, c, None)
    for Y in range(40, 80):
        for X in range(8, 70):
            u, v = (X / 2 - 24) / 12, (Y / 2 - 28) / 5
            if 0.8 <= u * u + v * v <= 1.2 and (X + Y) % 2 == 0:
                t.pf(X, Y, "#241c55")
    # Étoiles de trois tailles, certaines à branches.
    for i in range(18):
        x, y = (i * 29 + 7) % 64, (i * 17 + 3) % 48
        c = B4 if (i + k) % 3 else J4
        if i % 5 == 0:
            etoile(t, x + 0.5, y + 0.5, c, 2)
        else:
            points(t, [(x * 2, y * 2), (x * 2 + 1, y * 2)] if i % 2 else [(x * 2, y * 2)], c)
    # Planète : sphère ombrée, bandes, anneau passant devant et derrière.
    halo(t, 46, 16, 8, 1.5, 2, 0.04)
    for (cx, cy, r, c) in ((46, 16, 8, O3),):
        disque(t, cx, cy, r, r, c, None)
    for Y in range(0, 96):
        for X in range(0, 128):
            u, v = (X / 2 - 46) / 8, (Y / 2 - 16) / 8
            d2 = u * u + v * v
            if d2 <= 1:
                sh = (u + 0.55) * 0.5 + (v + 0.4) * 0.5
                if sh > 0.75 and (X + Y) % 2 == 0 or sh > 1.0:
                    t.g[Y][X] = O2
                elif (Y // 3) % 4 == 0 and sh < 0.7:
                    t.g[Y][X] = eclaircir(O3, 0.18)
    disque(t, 43, 13, 3.8, 2.8, O5, None)
    disque(t, 42, 12, 1.2, 0.9, BLANC, None)
    # Anneau : l'arrière, puis l'avant.
    for a in range(0, 360, 1):
        r = math.radians(a)
        x, y = 46 + math.cos(r) * 14, 17 + math.sin(r) * 3.5
        fond = math.sin(r) < 0
        pas = 2 if fond else 3
        for d in range(pas):
            xx, yy = int(x * 2), int(y * 2) + d
            if fond:
                if 0 <= yy < t.H and 0 <= xx < t.W and (((xx - 92) / 16) ** 2 + ((yy - 32) / 16) ** 2 > 1):
                    t.pf(xx, yy, assombrir(J3, 0.3))
            else:
                t.pf(xx, yy, J3 if a % 6 < 4 else J4)
    # Satellite et comète.
    disque(t, 8, 8, 1.4, 1.4, ARGENT, None)
    disque(t, 7.6, 7.6, 0.5, 0.5, BLANC, None)
    trait(t, 56, 40, 61, 37, J4, None)
    trait(t, 52, 41.5, 57, 38.5, "#6a7fb0", None)


@finition("fond-patisserie", auto=False)
def _patisserie(t, k):
    vider(t)
    # Mur rayé crème et bleu pâle, bord de store festonné.
    for x in range(W):
        rect(t, x, 0, 1, 30, CREME if (x // 4) % 2 else B4)
    for x in range(0, W, 8):
        trait(t, x + 0.2, 0, x + 0.2, 28.5, eclaircir(B4, 0.5), None)
    rect(t, 0, 10, W, 2, BR2)
    trait(t, 0, 10, 64, 10, BR3, None)
    for i, x in enumerate(range(4, 60, 7)):
        c = [V3, O4, B3, J4, ROSE][i % 5]
        disque(t, x + 2, 8, 2.6, 1.6, c, None)
        disque(t, x + 1.3, 7.4, 1.0, 0.5, eclaircir(c, 0.6), None)
        trait(t, x, 6.8, x + 4.6, 6.8, CREME, None)
    # Comptoir : bois en planches, rebord clair, ombre sous le rebord.
    degrade_v(t, 30, 48, 0, 64, [BR3, "#946032", BR2])
    rect(t, 0, 30, W, 2, S3)
    trait(t, 0, 30, 64, 30, "#f4ead2", None)
    trait(t, 0, 32.2, 64, 32.2, "#a07a4a", None)
    for x in range(2, 64, 6):
        rect(t, x, 34, 0.6, 14, BR2)
        trait(t, x + 1, 34, x + 1, 47.6, eclaircir(BR3, 0.18), None)
    # Gâteau à étages : crème, napage, cerise, bougie qui vacille.
    rect(t, 6, 22, 14, 8, CREME)
    rect(t, 9, 16, 8, 6, V4)
    rect(t, 6, 22, 14, 2, V3)
    for x in range(6, 20, 2):
        disque(t, x + 1, 24.2, 1.1, 1.2, V3, None)
    arc(t, 13, 23, 7, 7, 200, 340, BLANC, {CREME})
    trait(t, 9, 16.3, 17, 16.3, eclaircir(V4, 0.5), None)
    disque(t, 13, 15, 1.7, 1.7, B2, None)
    disque(t, 12.4, 14.4, 0.5, 0.4, B4, None)
    rect(t, 12.8, 12.5, 0.5, 2.0, BR2)
    disque(t, 13 + (0.5 if k else -0.2), 11.6, 0.7, 1.0, J3, None)
    disque(t, 13 + (0.5 if k else -0.2), 11.8, 0.35, 0.5, J4, None)
    for x in (8, 11, 15, 17):
        points(t, [(x * 2, 34), (x * 2 + 1, 35)], O3 if x % 2 else B3)
    # Plateau de beignets.
    rect(t, 46, 24, 12, 6, S2)
    trait(t, 46, 24.2, 58, 24.2, S3, None)
    for x in (48, 51, 54):
        disque(t, x + 1, 23, 1.7, 1.7, O3, None)
        disque(t, x + 1, 23, 0.55, 0.55, S2, None)
        disque(t, x + 0.4, 22.2, 0.55, 0.4, O5, None)
        arc(t, x + 1, 23, 1.6, 1.6, 20, 120, O2, None)


@finition("fond-observatoire", auto=False)
def _observatoire(t, k):
    vider(t)
    degrade_v(t, 0, 48, 0, 64, ["#081a33", NUIT, NUIT2, "#1d4372"])
    for i in range(16):
        x, y = (i * 23 + 5) % 64, (i * 11 + 2) % 26
        c = J4 if (i + k) % 3 else B4
        if i % 4 == 0 and (i + k) % 2:
            etoile(t, x + 0.5, y + 0.5, c, 2)
        else:
            points(t, [(x * 2, y * 2), (x * 2 + 1, y * 2)], c)
    # Colline.
    relief(t, lambda x: 42 + ((x - 32) / 40) ** 2 * 6, "#12283f", "#24456b", None, haut=2)
    # Dôme : coque d'argent éclairée à gauche, nervures, fente ouverte, tube du télescope.
    t.ell(46, 31, 11, 10, ARGENT, cond=lambda x, y, u, v: v < 0)
    for Y in range(40, 64):
        for X in range(70, 116):
            u, v = (X / 2 - 46) / 11, (Y / 2 - 31) / 10
            if u * u + v * v <= 1 and t.g[Y][X] == ARGENT:
                sh = u * 0.7 + v * 0.3
                t.g[Y][X] = ARGENT_C if sh < -0.45 else (GRIS_C if sh > 0.5 else ARGENT)
    arc(t, 46, 31, 10.4, 9.4, 205, 335, BLANC, {ARGENT_C, ARGENT})
    rect(t, 35, 30, 22, 8, GRIS_C)
    rect(t, 35, 30, 22, 1, ARGENT_C)
    trait(t, 35, 31.5, 57, 31.5, GRIS, None)
    for X in range(70, 114, 4):
        t.pf(X, 62, GRIS)
    # Fente du dôme avec le tube qui sort.
    t.ell(42, 26, 2, 4, NUIT)
    t.ell(42, 26, 1.6, 3.6, "#0a1f3d")
    trait(t, 43, 27, 52, 17, J2, None)
    trait(t, 44, 27, 53, 17, J3, None)
    trait(t, 43.4, 26.6, 52.4, 16.6, J4, None)
    disque(t, 52.6, 16.6, 1.0, 1.0, J2, None)
    disque(t, 52.4, 16.4, 0.4, 0.4, J4, None)
    # Hublots éclairés.
    for x in (38, 44, 50):
        rect(t, x, 33, 3, 3, J4 if k else J3)
        if k:
            rect(t, x, 33, 3, 0.5, BLANC)
        trait(t, x + 1.5, 33, x + 1.5, 36, GRIS_C, None)
        trait(t, x, 34.5, x + 3, 34.5, GRIS_C, None)
    # Escalier de pierre.
    for i in range(5):
        rect(t, 30 - i * 1.4, 40 + i * 1.2, 6, 1.2, "#2a4a73")
        trait(t, 30 - i * 1.4, 40 + i * 1.2, 36 - i * 1.4, 40 + i * 1.2, "#4a6f9c", None)


@finition("fond-mer-cafe", auto=False)
def _mer_cafe(t, k):
    vider(t)
    degrade_v(t, 0, 26, 0, 64, [O4, O5, "#ffe3c4"])
    # Soleil couchant : disque, bandes, halo, nuages crème.
    halo(t, 14, 22, 6.0, 2.0, 3, 0.05)
    t.ell(14, 22, 6, 6, J3, cond=lambda x, y, u, v: v < 0.4)
    disque(t, 14, 21, 4.2, 3.8, J4, None)
    for (x, y, rx, ry) in ((34, 6, 6, 1.5), (30, 7.2, 4, 1.4), (50, 11, 5, 1.2)):
        disque(t, x, y, rx, ry, CREME, None)
    # Mer de café : bandes sombres, crème en volutes, reflet du soleil.
    degrade_v(t, 24, 48, 0, 64, [CAFE2, "#4d301c", CAFE])
    for y in range(26, 48, 4):
        for x in range(0, 64, 8):
            xx = x + ((y // 4 + k) % 2) * 4
            arc(t, xx + 2, y + 0.5, 2.4, 1.0, 190, 350, MOUSSE, None)
            trait(t, xx + 0.5, y + 1.0, xx + 3.5, y + 1.0, "#7a5333", None)
    for i in range(5):
        trait(t, 12 + i * 0.4, 25 + i * 1.6, 17 - i * 0.4, 25 + i * 1.6, J3, None)
    # Île-tasse : porcelaine, anse, liseré, café à l'intérieur, vapeur ondulante.
    rect(t, 40, 16, 16, 12, CREME)
    for Y in range(32, 56):
        for X in range(80, 112):
            sh = (X - 80) / 32
            if t.g[Y][X] == CREME and sh > 0.78:
                t.g[Y][X] = CREME_O
    rect(t, 40, 16, 16, 2, CAFE)
    trait(t, 40, 16, 56, 16, "#7a5333", None)
    arc(t, 48, 28, 8, 1.4, 20, 160, CREME_O, {CREME, CREME_O})
    t.anneau(57, 22, 4, 4, CREME, ep=2)
    arc(t, 57, 22, 3.8, 3.8, 200, 330, BLANC, {CREME})
    arc(t, 57, 22, 2.2, 2.2, 20, 140, CREME_O, {CREME})
    trait(t, 41, 18.4, 41, 27, BLANC, {CREME})
    for i in range(3):
        for j in range(8):
            x = 44 + i * 4 + math.sin(j * 0.9 + k * 1.5 + i) * 0.9
            points(t, [(int(x * 2), int((12 - (i + k) % 2 - j * 0.5) * 2))], ARGENT_C if j < 6 else GRIS_C)


@finition("fond-potager", auto=False)
def _potager(t, k):
    vider(t)
    degrade_v(t, 0, 28, 0, 64, [B3, B4, "#d8ecff", "#eef6ff"])
    halo(t, 52, 8, 5, 2.0, 3, 0.05)
    t.ell(52, 8, 5, 5, J3)
    disque(t, 52, 8, 3.4, 3.4, J4, None)
    for a in range(0, 360, 45):
        r = math.radians(a)
        trait(t, 52 + math.cos(r) * 6.5, 8 + math.sin(r) * 6.5, 52 + math.cos(r) * 8, 8 + math.sin(r) * 8, J3, None)
    for (x, y, rx, ry) in ((10, 6, 5, 1.5), (14, 5.4, 3.5, 1.4), (30, 11, 4, 1.2)):
        disque(t, x, y, rx, ry, BLANC, None)
    # Terre : sillons en relief.
    degrade_v(t, 22, 48, 0, 64, [BR2, "#6c4120", BR1, "#4a2e17"])
    # Clôture en piquets arrondis, lisse et ombre.
    rect(t, 0, 18, 64, 1, S2)
    for x in range(0, 64, 5):
        rect(t, x, 17, 2, 6, S3)
        t.poly([(x, 17), (x + 1, 15.8), (x + 2, 17)], S3)
        trait(t, x, 17.4, x, 22.6, BLANC, None)
        trait(t, x + 1.8, 18, x + 1.8, 22.6, S2, None)
    rect(t, 0, 19.2, 64, 0.6, "#f4ead2")
    for y in (28, 36, 44):
        rect(t, 0, y, W, 1, BR1)
        trait(t, 0, y - 0.3, 64, y - 0.3, "#8a5a30", None)
        for x in range(3, 64, 8):
            if y == 36:
                # Carotte : fanes de feuilles ondulées (bleu-vert pâle), racine à reflets.
                t.poly([(x, y - 1), (x + 3, y - 1), (x + 1.5, y + 3.4)], O3)
                trait(t, x + 0.4, y - 0.6, x + 1.5, y + 2.6, O2, {O3})
                trait(t, x + 0.5, y - 0.8, x + 1.4, y + 1.4, O4, {O3})
                for dx in (-1.2, 0.2, 1.4):
                    trait(t, x + 1.5, y - 1.2, x + 1.5 + dx, y - 5 - k * 0.6, T3 if dx else T2, None)
                    disque(t, x + 1.5 + dx, y - 5.4 - k * 0.6, 0.8, 0.6, T3, None)
            else:
                # Chou : feuilles en rosette, reflet et nervure.
                disque(t, x + 2, y - 2, 3.2, 2.5, T2, None)
                disque(t, x + 2, y - 2.6, 2.2, 1.5, T3, None)
                disque(t, x + 1.5, y - 3.0, 0.9, 0.5, eclaircir(T3, 0.5), None)
                arc(t, x + 2, y - 2, 3.0, 2.3, 20, 160, T1, None)
                trait(t, x + 2, y - 3.6, x + 2, y - 0.8, T1, {T2, T3})


@finition("fond-frissons", auto=False)
def _frissons(t, k):
    vider(t)
    degrade_v(t, 0, 40, 0, 64, ["#120a2e", "#1a1040", "#2a1a5a", "#3a2670"])
    halo(t, 46, 12, 8, 2.0, 4, 0.05)
    t.ell(46, 12, 8, 8, J4)
    # Lune : cratères, ombre du bord, chauve-souris qui la traverse.
    for (x, y, r) in ((44, 10, 2.0), (49, 14, 1.4), (47, 9, 0.9), (43, 15, 0.9)):
        disque(t, x, y, r, r, J3, None)
        disque(t, x + 0.3, y + 0.3, r * 0.6, r * 0.6, "#fff0b0", None)
    arc(t, 46, 12, 7.6, 7.6, 20, 120, "#e8d27a", None)
    # Arbres morts : tronc et branches fines, noueux.
    for x0 in (6, 56):
        rect(t, x0, 18, 3, 24, ENCRE)
        trait(t, x0 + 1, 24, x0 - 6, 16, ENCRE, None)
        trait(t, x0 + 2, 24, x0 - 5, 16, ENCRE, None)
        trait(t, x0 + 1, 28, x0 + 7, 21, ENCRE, None)
        trait(t, x0 + 2, 28, x0 + 8, 21, ENCRE, None)
        for (a, b, c_, d) in ((x0 - 4, 18, x0 - 7, 15), (x0 - 3, 20, x0 - 5, 22), (x0 + 5, 23, x0 + 9, 22), (x0 + 6, 22, x0 + 8, 18)):
            trait(t, a, b, c_, d, ENCRE, None)
        trait(t, x0 + 0.2, 20, x0 + 0.2, 41, "#251a50", None)
    for (x, y) in ((22, 14), (30, 8), (37, 18)):
        # Chauve-souris : ailes en arc.
        arc(t, x - 1.5, y, 1.5, 1.0, 180, 330, ENCRE, None)
        arc(t, x + 1.5, y, 1.5, 1.0, 210, 360, ENCRE, None)
        rect(t, x - 0.5, y - 0.5, 1, 1.4, ENCRE)
    rect(t, 0, 40, W, 8, "#120a2a")
    degrade_v(t, 38, 48, 0, 64, ["#241648", "#120a2a", "#0c0620"])
    # Citrouilles : côtes, queue, visage éclairé de l'intérieur, braises.
    for x in (14, 34, 48):
        disque(t, x, 40, 4, 3, O3, None)
        for dx in (-1.8, 0, 1.8):
            arc(t, x + dx, 40, 1.2, 3.0, 90, 270, O2, None) if dx < 0 else arc(t, x + dx, 40, 1.2, 3.0, -90, 90, O2, None)
        disque(t, x - 1.6, 38.6, 1.2, 0.7, O4, None)
        rect(t, x - 0.4, 36.2, 0.8, 1.4, BR2)
        lum = J4 if (x + k) % 2 else J3
        t.poly([(x - 2.0, 40.1), (x - 0.9, 38.5), (x - 0.2, 40.1)], lum)
        t.poly([(x + 0.4, 40.1), (x + 1.1, 38.5), (x + 2.0, 40.1)], lum)
        rect(t, x - 1.2, 41.2, 2.4, 0.5, lum)
    for i in range(10):
        points(t, [((i * 13 + 5) % 126, 80 + (i * 5) % 14)], "#3a2670")


@finition("fond-fetes", auto=False)
def _fetes(t, k):
    vider(t)
    degrade_v(t, 0, 40, 0, 64, ["#081a33", NUIT, NUIT2, "#1d4372"])
    # Neige : sol, ondulations, reflets bleutés.
    rect(t, 0, 40, W, 8, BLANC)
    for x in range(0, 64, 5):
        arc(t, x + 2.5, 41, 3, 0.9, 190, 350, B4, None)
    degrade_v(t, 44, 48, 0, 64, [CREME, "#e6f0fa", B4])
    # Maisons : murs, toits enneigés débordants, fenêtres à croisillons, cheminées fumantes.
    for i, x in enumerate((2, 22, 42)):
        h = 14 + i % 2 * 4
        c = [V1, BR2, B1][i]
        rect(t, x, 40 - h, 18, h, c)
        rect(t, x, 40 - h, 1, h, eclaircir(c, 0.25))
        rect(t, x + 17, 40 - h, 1, h, assombrir(c, 0.3))
        t.poly([(x - 1.4, 40 - h + 0.5), (x + 9, 40 - h - 7.5), (x + 19.4, 40 - h + 0.5)], CREME)
        t.poly([(x - 0.6, 40 - h), (x + 9, 40 - h - 6.2), (x + 18.6, 40 - h)], BLANC)
        trait(t, x - 1.4, 40 - h + 0.6, x + 19.4, 40 - h + 0.6, B4, None)
        for dx in (1.5, 4.5, 7.5, 10.5, 13.5):
            disque(t, x + dx, 40 - h + 0.2, 1.1, 0.8, BLANC, None)
        for wx in (x + 3, x + 11):
            lum = J3 if (i + k) % 3 else O4
            rect(t, wx, 40 - h + 4, 4, 4, lum)
            rect(t, wx, 40 - h + 4, 4, 0.5, eclaircir(lum, 0.5))
            trait(t, wx + 2, 40 - h + 4, wx + 2, 40 - h + 8, assombrir(c, 0.4), None)
            trait(t, wx, 40 - h + 6, wx + 4, 40 - h + 6, assombrir(c, 0.4), None)
            rect(t, wx - 0.5, 40 - h + 8, 5, 0.6, BLANC)
        rect(t, x + 14, 40 - h - 5, 2, 4, assombrir(c, 0.3))
        rect(t, x + 14, 40 - h - 5.6, 2.6, 0.8, BLANC)
        for j in range(3):
            disque(t, x + 15.2 + math.sin(j + k) * 0.7, 40 - h - 8 - j * 1.6, 0.8 + j * 0.3, 0.6 + j * 0.3, "#9fb8d4", None)
    # Guirlande de fanions : cordon en chaînette, fanions triangulaires.
    for X in range(0, 128):
        x = X / 2
        y = 10 + (1 - math.cos(x / 63 * math.pi * 2)) * 3
        t.pf(X, int(y * 2), "#c9d6e8")
        if X % 6 == (k * 2) % 6:
            col = [B3, O3, J3, V3][(X // 6 + k) % 4]
            t.poly([(x - 0.8, y + 0.2), (x + 0.8, y + 0.2), (x, y + 2.6)], col)
    # Flocons.
    for i in range(14):
        x, y = (i * 17 + 3) % 64, (i * 7 + k * 5) % 38
        if i % 4 == 0:
            etoile(t, x + 0.5, y + 0.5, BLANC, 1)
        else:
            points(t, [(x * 2, y * 2), (x * 2 + 1, y * 2)], BLANC)


@finition("fond-montagne", auto=False)
def _montagne(t, k):
    vider(t)
    degrade_v(t, 0, 40, 0, 64, [B3, "#8ec6ff", B4, "#d8ecff"])
    for x0, h, c in ((-4, 30, B1), (44, 28, B1), (20, 38, B2)):
        # Montagne : pans éclairé à gauche et ombré à droite, chapeau de neige dentelé, crêtes.
        t.poly([(x0, 40), (x0 + 16, 40 - h), (x0 + 32, 40)], c)
        for Y in range(t.H):
            for X in range(t.W):
                if t.g[Y][X] == c:
                    xx, yy = (X + 0.5) / 2, (Y + 0.5) / 2
                    if xx > x0 + 16 + (yy - (40 - h)) * 0.0 and (xx - (x0 + 16)) > (40 - yy) * 0.12:
                        t.g[Y][X] = assombrir(c, 0.2)
        t.poly([(x0 + 10.5, 40 - h + 7.5), (x0 + 12.5, 40 - h + 5.6), (x0 + 14, 40 - h + 7.6), (x0 + 16, 40 - h),
                (x0 + 18.4, 40 - h + 7.0), (x0 + 19.6, 40 - h + 5.8), (x0 + 21.5, 40 - h + 7.5), (x0 + 16, 40 - h + 5.5)], BLANC)
        trait(t, x0 + 16, 40 - h, x0 + 21.5, 40 - h + 7.5, B4, {BLANC})
    # Sapins d'avant-plan sur la rive.
    for x in (3, 9, 55, 60):
        sapin(t, x, 39, 8, 4, "#17608a", "#2c86b5", 3)
    # Lac : miroir des montagnes et ridules.
    degrade_v(t, 38, 48, 0, 64, [T2, "#2aa0cc", T3, "#2689b8"])
    for x in range(0, 64, 6):
        xx = x + (k * 3) % 6
        trait(t, xx, 42, xx + 3, 42, T3, None)
        trait(t, xx + 1.5, 44.5, xx + 4.5, 44.5, "#5fcdf0", None)
        trait(t, xx - 1, 46.5, xx + 1.5, 46.5, "#2689b8", None)
    for i in range(6):
        trait(t, 30 + i * 0.6, 40.5 + i * 1.0, 36 - i * 0.6, 40.5 + i * 1.0, B4, None)
    # Nuage qui dérive.
    for (dx, dy, rx, ry) in ((0, 0, 5, 1.6), (-2.5, 0.6, 3, 1.2), (3, 0.6, 3.2, 1.2)):
        disque(t, 8 + k + dx, 8 + dy, rx, ry, BLANC, None)
    disque(t, 7 + k, 7.2, 2.2, 0.5, "#eef6ff", None)


@finition("fond-ville", auto=False)
def _ville(t, k):
    vider(t)
    degrade_v(t, 0, 48, 0, 64, ["#050c1f", "#0b1530", NUIT, "#183a66"])
    for i in range(10):
        x, y = (i * 29 + 5) % 64, (i * 11 + 2) % 20
        points(t, [(x * 2, y * 2)], B4 if i % 2 else J4)
    # Lune en croissant avec halo.
    halo(t, 10, 8, 3, 2.0, 3, 0.05)
    croissant(t, 10, 8, 3, 1.2, -0.4, 2.6, J4)
    # Immeubles : façade avec arête éclairée, fenêtres, antennes, enseigne, reflets.
    for i, (x, w, h) in enumerate(((0, 10, 24), (11, 8, 32), (20, 12, 20), (33, 9, 36), (43, 10, 26), (54, 10, 30))):
        c = [ARDOISE, NOIR2][i % 2]
        rect(t, x, 48 - h, w, h, c)
        rect(t, x, 48 - h, w, 0.6, eclaircir(c, 0.35))
        rect(t, x, 48 - h, 0.6, h, eclaircir(c, 0.2))
        rect(t, x + w - 0.6, 48 - h, 0.6, h, assombrir(c, 0.35))
        for wy in range(48 - h + 3, 46, 4):
            for wx in range(x + 2, x + w - 1, 3):
                if (wx * 7 + wy * 3 + i + k) % 5 < 2:
                    lum = J3 if (wx + wy) % 2 else O4
                    rect(t, wx, wy, 1.6, 2.0, lum)
                    rect(t, wx, wy, 1.6, 0.4, eclaircir(lum, 0.5))
                else:
                    rect(t, wx, wy, 1.6, 2.0, assombrir(c, 0.3))
        if i in (1, 3, 5):
            rect(t, x + w / 2 - 0.2, 48 - h - 4, 0.5, 4, GRIS)
            disque(t, x + w / 2 + 0.05, 48 - h - 4.2, 0.6, 0.6, O3 if k else O2, None)
    # Enseigne au néon et lumières de la rue.
    rect(t, 24, 34, 5, 1.2, V3 if k else B3)
    for X in range(0, 128):
        if X % 3 == 0:
            t.pf(X, 93, "#1b2d4f")
    for x in (6, 28, 40, 52):
        points(t, [(x * 2, 94), (x * 2 + 1, 94)], J3)


@finition("fond-bibliotheque", auto=False)
def _bibliotheque(t, k):
    vider(t)
    degrade_v(t, 0, 48, 0, 64, [BR1, "#3a2412", BR1])
    cols = [B2, O3, V2, J2, B1, O2, V3, S2]
    for y0 in (2, 16, 30):
        x, i = 1, y0
        while x < 63:
            w = 2 + (i * 7) % 3
            h = 8 + (i * 5) % 3
            c = cols[i % len(cols)]
            haut = y0 + 11 - h
            rect(t, x, haut, w, h, c)
            rect(t, x, haut, 0.6, h, eclaircir(c, 0.3))
            rect(t, x + w - 0.6, haut, 0.6, h, assombrir(c, 0.3))
            rect(t, x, haut + 2, w, 1, J4 if i % 3 == 0 else CREME_O)
            rect(t, x, haut + h - 2.5, w, 0.5, J3 if i % 2 else CREME_O)
            if i % 5 == 0:
                disque(t, x + w / 2, haut + h / 2 + 0.5, 0.5, 0.5, J4, None)
            if i % 7 == 3:  # livre penché
                t.poly([(x, haut - 0.2), (x + w, haut - 1.6), (x + w, haut), (x, haut)], eclaircir(c, 0.3))
            x += w + (1 if i % 4 == 0 else 0)
            i += 1
        # Étagère : planche épaisse, face éclairée, ombre dessous.
        rect(t, 0, y0 + 11, W, 2, BR3)
        trait(t, 0, y0 + 11, 64, y0 + 11, "#c4905a", None)
        trait(t, 0, y0 + 13, 64, y0 + 13, "#3a2412", None)
    rect(t, 0, 44, W, 4, BR2)
    trait(t, 0, 44, 64, 44, BR3, None)
    # Petite lampe de lecture : cône de lumière tramé.
    for Y in range(20, 70):
        for X in range(90, 128):
            if (X + Y) % 2 == 0 and abs(X - 112) < (Y - 20) * 0.5 and t.g[Y][X]:
                t.g[Y][X] = eclaircir(t.g[Y][X], 0.12)
    # Poussière dorée en suspension.
    for (x, y) in ((12, 14), (25, 29), (44, 12), (57, 38), (35, 21)):
        points(t, [(x * 2, y * 2)], J3)


@finition("fond-cerisiers", auto=False)
def _cerisiers(t, k):
    vider(t)
    degrade_v(t, 0, 38, 0, 64, [B4, "#cfe6ff", "#e6f2ff", "#f3f8ff"])
    for (x, y, rx, ry) in ((30, 8, 6, 1.6), (34, 7.4, 4, 1.4)):
        disque(t, x, y, rx, ry, BLANC, None)
    # Eau de l'étang : reflets rosés, nénuphars à pétales.
    degrade_v(t, 38, 48, 0, 64, [T2, "#2aa0cc", T3, T2])
    for x in range(0, 64, 5):
        trait(t, x + (k * 2) % 5, 41, x + 3 + (k * 2) % 5, 41, T3, None)
        trait(t, x + 2, 44, x + 4.4, 44, "#6bd0f0", None)
    for (x, y) in ((22, 44), (40, 42)):
        disque(t, x, y, 2.2, 0.8, "#1a6382", None)
        disque(t, x, y - 0.4, 0.8, 0.5, ROSE, None)
    # Deux cerisiers : tronc tordu, branches, houppiers en grappes de pétales.
    for x0 in (12, 50):
        rect(t, x0 - 1, 24, 3, 16, BR2)
        trait(t, x0 - 0.5, 24, x0 - 0.5, 40, BR3, None)
        trait(t, x0 + 1.6, 26, x0 + 1.6, 40, BR1, None)
        trait(t, x0, 26, x0 - 5, 20, BR2, None)
        trait(t, x0 + 1, 26, x0 + 6, 19, BR2, None)
        for dx, dy, r in ((-6, 18, 6), (5, 17, 6), (0, 12, 7), (-2, 21, 5), (6, 22, 4)):
            c = ROSE if (dx + dy) % 2 else V4
            disque(t, x0 + dx, dy, r, r * 0.8, c, None)
        # Lumière : grappes claires en haut à gauche, ombres violettes en bas à droite.
        for (dx, dy, r) in ((-7.5, 15.5, 2.4), (3.0, 14.5, 2.4), (-2, 9.5, 2.8), (-4, 19.5, 1.8)):
            disque(t, x0 + dx, dy, r, r * 0.7, "#ffc4de", {ROSE})
            disque(t, x0 + dx, dy, r, r * 0.7, BLANC, {V4})
        for (dx, dy, r) in ((7.5, 24, 2.4), (1.5, 16, 3.0), (-4.5, 23, 2.2)):
            disque(t, x0 + dx, dy, r, r * 0.6, "#c97ab0", {ROSE})
            disque(t, x0 + dx, dy, r, r * 0.6, "#a89ae0", {V4})
        for (dx, dy) in ((-3, 12), (4, 10), (-9, 17), (9, 20), (0, 19)):
            points(t, [(int((x0 + dx) * 2), int(dy * 2)), (int((x0 + dx) * 2) + 1, int(dy * 2) + 1)], BLANC)
    # Pétales qui tombent : petits cœurs obliques.
    for i in range(10):
        x, y = (i * 13 + k * 5) % 62, (i * 9 + k * 7) % 38 + 4
        c = [ROSE, V4][i % 2]
        X, Y = x * 2, y * 2
        points(t, [(X, Y), (X + 1, Y), (X + 1 + k, Y + 1), (X + 2, Y + 1)], c)
        points(t, [(X, Y + 1)], assombrir(c, 0.15))


@finition("fond-automne", auto=False)
def _automne(t, k):
    vider(t)
    degrade_v(t, 0, 40, 0, 64, [O5, "#ffe0bd", "#ffe8cc", "#fff1de"])
    halo(t, 48, 5, 4, 2.0, 2, 0.04)
    for i, x0 in enumerate((6, 26, 46, 60)):
        c = [O3, O2, J3, BR3][i]
        rect(t, x0 - 1, 20, 3, 22, BR1)
        trait(t, x0 - 0.6, 20, x0 - 0.6, 41.6, BR2, None)
        trait(t, x0 + 1.4, 21, x0 + 1.4, 41.6, "#2e1c0e", None)
        disque(t, x0, 14 + i % 2 * 3, 9, 9, c, None)
        for (dx, dy, r) in ((-4, 2, 4.5), (4, 3, 4), (0, -4, 4.5)):
            disque(t, x0 + dx, 14 + i % 2 * 3 + dy, r, r, eclaircir(c, 0.1), None)
        arc(t, x0, 14 + i % 2 * 3, 8.6, 8.6, 20, 160, assombrir(c, 0.25), None)
        disque(t, x0 - 3, 11 + i % 2 * 3, 3, 2, O5, None)
        for j in range(5):
            X, Y = int((x0 - 6 + j * 3 + (i % 2)) * 2), int((10 + (j * 5) % 9 + i % 2 * 3) * 2)
            points(t, [(X, Y), (X + 1, Y + 1)], assombrir(c, 0.22) if j % 2 else eclaircir(c, 0.3))
    # Sol : tapis de feuilles et brindilles.
    degrade_v(t, 40, 48, 0, 64, [BR2, "#6a4120", "#52331a"])
    for x in range(0, 64, 3):
        c = [O3, J3, BR3][x % 3]
        points(t, [(x * 2, 82 + (x % 2) * 2), (x * 2 + 1, 82 + (x % 2) * 2 + 1), (x * 2 + 2, 82 + (x % 2) * 2)], c)
    for X in range(0, 128, 7):
        t.pf(X, 88 + (X // 7) % 3, BR1)
    # Feuilles en chute, obliques et vrillées.
    for i in range(6):
        x, y = (i * 11 + k * 4) % 62 + 1, (i * 7 + k * 9) % 34 + 4
        c = [O3, J3, BR3][i % 3]
        X, Y = x * 2, y * 2
        if k:
            points(t, [(X, Y), (X + 1, Y), (X + 1, Y + 1), (X + 2, Y + 1), (X + 2, Y + 2), (X, Y + 1)], c)
        else:
            points(t, [(X, Y), (X + 1, Y), (X + 2, Y + 1), (X + 3, Y + 1), (X + 1, Y + 1)], c)
        points(t, [(X + 1, Y)], eclaircir(c, 0.35))


@finition("fond-aurore", auto=False)
def _aurore(t, k):
    vider(t)
    degrade_v(t, 0, 48, 0, 64, ["#050d22", "#07122a", "#0b1d3e", "#0f2a52"])
    # Rideaux d'aurore : franges verticales tramées, trois nappes qui ondulent.
    for c, dy, haut in (("#3fb8e0", 4, 14), ("#6cb6ff", 10, 16), ("#9b8cff", 16, 14)):
        for X in range(128):
            x = X / 2
            y0 = dy + math.sin(x / 8 + k * 0.8 + dy) * 3
            Y0 = int(y0 * 2)
            for j in range(haut):
                Y = Y0 + j
                if not (0 <= Y < t.H):
                    continue
                f = j / haut
                if f < 0.15 and (X + Y) % 2 == 0:
                    continue
                if f > 0.7 and (X + Y) % 2 == 1:
                    continue
                if f > 0.88 and (X % 3):
                    continue
                if (X % 8 == 0) and f > 0.6:
                    continue
                base = t.g[Y][X] or "#07122a"
                mix = 0.85 if f < 0.45 else 0.6 if f < 0.75 else 0.35
                r1, g1, b1 = [int(base[i:i + 2], 16) for i in (1, 3, 5)]
                r2, g2, b2 = [int(c[i:i + 2], 16) for i in (1, 3, 5)]
                t.g[Y][X] = "#%02x%02x%02x" % (int(r1 + (r2 - r1) * mix), int(g1 + (g2 - g1) * mix), int(b1 + (b2 - b1) * mix))
    for i in range(12):
        x, y = (i * 19 + 7) % 64, (i * 13) % 30
        if i % 4 == 0 and (i + k) % 2:
            etoile(t, x + 0.5, y + 0.5, BLANC, 1)
        else:
            points(t, [(x * 2, y * 2)], BLANC)
    # Banquise : dôme de glace, éclats bleus, reflet vert-bleu de l'aurore.
    t.ell(32, 56, 44, 16, BLANC)
    t.ell(32, 56, 44, 15, B4, cond=lambda x, y, u, v: v > -0.85)
    arc(t, 32, 56, 43.6, 15.6, 200, 340, "#e4f2ff", None)
    for X in range(10, 118, 6):
        Y = 84 + (X * 5) % 9
        if 0 <= Y < t.H and t.g[Y][X]:
            t.g[Y][X] = "#8fc4ff"
    for X in range(20, 108, 4):
        for Y in range(80, 86):
            if t.g[Y][X] in (BLANC, B4) and (X + Y) % 3 == 0:
                t.g[Y][X] = "#bfe6f5"
