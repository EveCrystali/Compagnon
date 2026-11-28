"""Export des personnages en pied HD au format de docs/SCENES-HD.md (§ 6) : assets/sprites-hd/pied-<campagne>-<id>.txt.

    py outils/sprites/personnages_hd_export.py                  # toutes les campagnes de CAMPAGNES
    py outils/sprites/personnages_hd_export.py grande-panne     # une campagne

Python pur. Pour chaque personnage : `pied-<campagne>-<id>.txt` (humeur neutre) et `pied-<campagne>-<id>-<humeur>.txt`
(même nommage que les portraits), tous sur la même toile et le même ancrage, pour que le moteur change d'humeur sans
que le personnage bouge. Cinq images, dans l'ordre de SCENES-HD.md : 0 repos, 1 inspiré, 2 yeux fermés, 3 bouche
entrouverte, 4 bouche ouverte.

Sens du dessin : SCENES-HD.md veut un personnage qui **regarde vers la droite** dans son fichier ; le moteur le
retourne pour regarder Pilou. Les dessins de personnages_hd.py sont pensés pour la place habituelle (à droite de
Pilou, tournés vers la gauche, lumière en haut à gauche, inscriptions lisibles) : le fichier en est donc le miroir.
Retourné par le moteur à sa place habituelle, le personnage retrouve sa lumière et ses inscriptions à l'endroit.

Référence : outils/sprites/personnages-hd-reference.txt, une ligne par fichier — `id largeur hauteur ancre_x ancre_y
images duree`, puis l'empreinte FNV-1a de chaque image décodée (ARGB 0xFFrrggbb, transparent 0x00000000, rangée par
rangée, comme decors_hd.fnv).
"""
import os
import sys

import personnages_hd as P

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.normpath(os.path.join(ICI, "..", "..", "assets", "sprites-hd"))
REFERENCE = os.path.join(ICI, "personnages-hd-reference.txt")
LETTRES = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!$%&*+-/<>?@^_~"
CAMPAGNES = ("grande-panne", "phare-eteint", "petit-nuage")                      # campagnes exportées (une par PR)
IMAGES = ((0, 0, 0, 0), (0, 0, 1, 1), (2, 0, 0, 0), (0, 1, 0, 0), (0, 3, 0, 1))     # (paup, bouche, souffle, t)
DUREE = 150


def identifiant(cle, humeur="neutre"):
    base = "pied-%s-%s" % cle
    return base if humeur == "neutre" else base + "-" + humeur


def _plages(s):
    out, i, n = [], 0, len(s)
    while i < n:
        j = i
        while j < n and s[j] == s[i]:
            j += 1
        out.append((str(j - i) if j - i > 1 else "") + s[i])
        i = j
    return "".join(out)


def grilles(cle):
    """{humeur: [5 grilles]} sur une toile commune : rognée au plus juste sur toutes les humeurs, retournée (voir
    l'en-tête), le vide de ceux qui volent ajouté dessous. Renvoie aussi (largeur, hauteur, ancre_x, ancre_y)."""
    p = P.PERSOS[cle]
    brut = {h: [P.image(cle, P.Etat(h, paup, bou, souffle, t)).c for (paup, bou, souffle, t) in IMAGES]
            for h in p["humeurs"]}
    xs, ys = [], []
    for ims in brut.values():
        for g in ims:
            for y, rang in enumerate(g):
                for x, v in enumerate(rang):
                    if v is not None:
                        xs.append(x)
                        ys.append(y)
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    repos = brut["neutre"][0]
    rx = [x for rang in repos for x, v in enumerate(rang) if v is not None]
    axe = (min(rx) + max(rx) + 1) // 2
    w, h = x1 - x0 + 1, y1 - y0 + 1 + p["vol"]
    out = {}
    for hum, ims in brut.items():
        out[hum] = [[list(reversed(g[y][x0:x1 + 1])) if y <= y1 else [None] * w for y in range(y0, y0 + h)] for g in ims]
    return out, (w, h, x1 - axe, h - 1)


def encoder(sid, ims, mesures, commentaire=""):
    w, h, ax, ay = mesures
    couleurs = []
    for g in ims:
        for rang in g:
            for v in rang:
                if v is not None and v not in couleurs:
                    couleurs.append(v)
    assert len(couleurs) <= len(LETTRES), "%s : %d couleurs" % (sid, len(couleurs))
    lettre = {v: LETTRES[i] for i, v in enumerate(couleurs)}
    lettre[None] = ","
    lignes = ["# " + commentaire] if commentaire else []
    lignes += ["id: " + sid, "taille: %d %d" % (w, h), "ancre: %d %d" % (ax, ay), "duree: %d" % DUREE,
               "palette: " + " ".join("%s=%s" % (lettre[v], v) for v in couleurs), "images: %d" % len(ims)]
    prec = None
    for g in ims:
        for y in range(h):
            if prec is None:
                s = "".join(lettre[v] for v in g[y])
            else:
                s = "".join("." if a == b else lettre[a] for a, b in zip(g[y], prec[y]))
            lignes.append(_plages(s))
        prec = g
    return "\n".join(lignes) + "\n"


def decoder(texte):
    """Le lecteur de référence (celui de decors_hd.decoder, plus `ancre` et la virgule transparente)."""
    d = {"palette": {}, "images": []}
    lignes = texte.split("\n")
    i = 0
    while True:
        l = lignes[i]
        i += 1
        if not l or l.startswith("#"):
            continue
        cle, _, val = l.partition(":")
        val = val.strip()
        if cle == "id":
            d["id"] = val
        elif cle == "taille":
            d["w"], d["h"] = (int(v) for v in val.split())
        elif cle == "ancre":
            d["ancre"] = tuple(int(v) for v in val.split())
        elif cle == "duree":
            d["duree"] = int(val)
        elif cle == "palette":
            for paire in val.split():
                a, _, b = paire.partition("=")
                d["palette"][a] = b
        elif cle == "images":
            n = int(val)
            break
    prec = None
    for _ in range(n):
        image = []
        for y in range(d["h"]):
            rang, x, k = [], 0, 0
            for ch in lignes[i]:
                if "0" <= ch <= "9":
                    k = k * 10 + ord(ch) - 48
                    continue
                k = k or 1
                rang.extend(prec[y][x:x + k] if ch == "." else ch * k)
                x += k
                k = 0
            assert x == d["w"], "rangée de %d pixels au lieu de %d" % (x, d["w"])
            image.append(rang)
            i += 1
        d["images"].append(image)
        prec = image
    return d


def fnv(image, palette):
    h = 0x811C9DC5
    octets = {k: (int(v[5:7], 16), int(v[3:5], 16), int(v[1:3], 16), 255) for k, v in palette.items()}
    octets[","] = (0, 0, 0, 0)
    for rang in image:
        for ch in rang:
            for o in octets[ch]:
                h ^= o
                h = (h * 0x01000193) & 0xFFFFFFFF
    return h


def exporter(campagnes=CAMPAGNES):
    os.makedirs(SORTIE, exist_ok=True)
    ref, poids = [], 0
    for cle in P.ORDRE:
        if cle[0] not in campagnes:
            continue
        p = P.PERSOS[cle]
        parhumeur, mesures = grilles(cle)
        for hum in p["humeurs"]:
            sid = identifiant(cle, hum)
            texte = encoder(sid, parhumeur[hum], mesures,
                            "Personnage en pied, haute définition : %s (%s) — %s" % (p["nom"], hum, p["description"]))
            d = decoder(texte)
            inverse = {v: k for k, v in d["palette"].items()}
            inverse[None] = ","
            for g, image in zip(parhumeur[hum], d["images"]):
                assert ["".join(r) for r in image] == ["".join(inverse[v] for v in rang) for rang in g], sid
            with open(os.path.join(SORTIE, sid + ".txt"), "w", encoding="utf-8", newline="\n") as f:
                f.write(texte)
            poids += len(texte.encode("utf-8"))
            ref.append("%s %d %d %d %d %d %d %s" % (sid, d["w"], d["h"], d["ancre"][0], d["ancre"][1], len(d["images"]),
                                                     d["duree"], " ".join("%08x" % fnv(im, d["palette"]) for im in d["images"])))
    return ref, poids


def main():
    campagnes = tuple(sys.argv[1:]) or CAMPAGNES
    ref, poids = exporter(campagnes)
    autres = []
    if os.path.isfile(REFERENCE):
        with open(REFERENCE, encoding="utf-8") as f:
            autres = [l for l in f.read().split("\n") if l and not l.startswith("#")
                      and not any(l.startswith("pied-%s-" % c) for c in campagnes)]
    entete = ["# Personnages en pied HD (personnages_hd_export.py) : id largeur hauteur ancre_x ancre_y images duree, puis",
              "# l'empreinte FNV-1a de chaque image décodée (ARGB 0xFFrrggbb, transparent 0x00000000, rangée par rangée)."]
    with open(REFERENCE, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(entete + sorted(autres + ref)) + "\n")
    print("%d fichiers, %d Ko" % (len(ref), poids // 1024))


if __name__ == "__main__":
    main()
