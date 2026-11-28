"""Les personnages en pied dans la scène (docs/SCENES.md, « Personnages en pied ») : `pied-<campagne>-<personnage>`.

Dessin fin seulement, au pixel de la scène. Pour les personnages-objets (le sablier, la feuille, le tampon,
l'imprimante, les touches…), le portrait 1× (32 × 32, dessiné nativement par portraits_campagnes.py) est déjà un corps
entier : on le reprend tel quel, recadré au plus juste pour que ses pieds touchent la ligne du sol. Ses cinq images
gardent leur ordre (0 et 1 repos, 2 yeux fermés, 3 et 4 bouche ouverte) : les animations nommées `repos`, `cligne`,
`parle` sont écrites dans assets/scenes/animations.txt par theatre.py. Un personnage dessiné en buste (Mlle Renvoi)
se tient derrière un guichet qu'on lui pose devant.

Les humains (Le phare éteint) ont un portrait en buste : ils sont dessinés en pied par humains_pied.py.
Campagnes déjà passées au théâtre en pied : CAMPAGNES (une campagne par PR, décidé avec le pilote le 28 novembre 2026).
"""
import os

CAMPAGNES = ("grande-panne", "phare-eteint")

# Personnages en buste : le meuble posé devant eux (lignes d'en bas recouvertes).
GUICHETS = {("grande-panne", "mlle-renvoi")}
GUICHET = {"k": "#1a1726", "c": "#b8844f", "b": "#8a5a33", "d": "#5a3820", "v": "#cfe0ea"}

IDS = []


def _ids():
    import portraits_campagnes
    return sorted("pied-%s-%s" % (c, p) for (c, p) in portraits_campagnes.PERSOS if c in CAMPAGNES)


def ids():
    return _ids()


def _lire_1x(c, p):
    import rendu
    import toile
    chemin = os.path.join(toile.SORTIE, "portrait-%s-%s.txt" % (c, p))
    with open(chemin, encoding="utf-8") as fh:
        return rendu.lire(fh.read(), "portrait-%s-%s" % (c, p))


def _grilles(s):
    """Les images du sprite en grilles de couleurs (None = transparent)."""
    out = []
    for im in s.images:
        out.append([[None if ch == "." else s.palette[ch] for ch in ligne.ljust(s.w, ".")] for ligne in im])
    return out


def _guichet(g, w):
    """Un guichet de bois verni devant le buste : comptoir de 8 lignes, plateau clair, vitre sur le côté."""
    h = len(g)
    largeur = len(g[0])
    hauteur = 8
    for y in range(h - hauteur, h):
        for x in range(largeur):
            r = y - (h - hauteur)
            if r == 0:
                c = GUICHET["k"]
            elif r == 1:
                c = GUICHET["c"]
            elif r == hauteur - 1:
                c = GUICHET["k"]
            else:
                c = GUICHET["b"] if (x % 6) else GUICHET["d"]
            if x in (0, largeur - 1):
                c = GUICHET["k"]
            g[y][x] = c
    return g


def tout():
    """Écrit les sprites en pied (dessin fin seulement : n'agit qu'au passage à l'échelle 2 de generer.py)."""
    import portraits_campagnes
    import toile
    from toile import Toile, ecrire
    if toile.ECHELLE != 2:
        return
    for (c, p) in sorted(portraits_campagnes.PERSOS):
        if c not in CAMPAGNES:
            continue
        import humains_pied
        if (c, p) in humains_pied.GENS:
            # Les humains : dessinés en pied par humains_pied.py (leur portrait est un buste).
            ims = humains_pied.images((c, p))
            duree = 150
        else:
            s = _lire_1x(c, p)
            ims = _grilles(s)
            duree = s.duree
        h, w = len(ims[0]), len(ims[0][0])
        # Recadrage commun à toutes les images : la boîte des pixels pleins.
        xs = [x for g in ims for y in range(h) for x in range(w) if g[y][x] is not None]
        ys = [y for g in ims for y in range(h) for x in range(w) if g[y][x] is not None]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        if (c, p) in GUICHETS:
            x0, x1 = max(0, x0 - 3), min(w - 1, x1 + 3)
        cw, ch = x1 - x0 + 1, y1 - y0 + 1
        W2, H2 = cw + (cw % 2), ch + (ch % 2)          # la toile fine a des côtés pairs : on ajoute en haut et à droite
        toiles = []
        for g in ims:
            t = Toile(W2 // 2, H2 // 2)
            t.e = 2
            t.g = [[None] * W2 for _ in range(H2)]
            for y in range(ch):
                for x in range(cw):
                    t.g[y + H2 - ch][x] = g[y0 + y][x0 + x]
            if (c, p) in GUICHETS:
                t.g = _guichet(t.g, W2)
            toiles.append(t)
        sid = "pied-%s-%s" % (c, p)
        ecrire(sid, toiles, duree=duree, commentaire="Personnage en pied (pieds_campagnes.py, docs/SCENES.md) : %s" % p)
        IDS.append(sid)
