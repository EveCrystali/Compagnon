#!/usr/bin/env python3
"""Sons de Pilou : synthèse de référence (docs/SONS.md).

Lit assets/sons.txt et calcule les échantillons exactement comme Sons.cs (PC) et Sons.java (Android) : tout est en
entiers (accumulateur de phase 32 bits, enveloppe en 1/4096, décalages à droite qui arrondissent vers le bas dans les
trois langages), donc les trois donnent les mêmes octets. Lit aussi assets/musiques.txt : les boucles de musique
et d'ambiance de l'Aventure, synthétisées de la même manière (références dans musiques-reference.txt).

    py outils/sons/sons.py               # écrit outils/sons/ecoute/*.wav, ecoute.html et affiche les mesures
    py outils/sons/sons.py --reference   # réécrit outils/sons/sons-reference.txt (si un son change)
    py outils/sons/sons.py --verifier    # vérifie la référence et les règles de douceur (code de sortie 1 sinon)
"""

import hashlib
import math
import struct
import sys
import wave
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
CATALOGUE = RACINE / "assets" / "sons.txt"
REFERENCE = Path(__file__).resolve().parent / "sons-reference.txt"
ECOUTE = Path(__file__).resolve().parent / "ecoute"

TAUX = 22050           # échantillons par seconde, mono, 16 bits
ATTAQUE_MS = 4         # montée de chaque note : pas de clic au début
RELACHE_MS = 60        # descente (quadratique) de chaque note, au plus la moitié de la note
QUEUE_MS = 20          # silence ajouté après la dernière note, le temps que le filtre retombe
FONDU_MS = 8           # fondu final sur le son entier : il finit exactement à zéro
FILTRE = 120           # passe-bas à deux pôles, coefficient sur 256 (vers 2,3 kHz) : arrondit le grain 8 bits
DISCRET = 3            # « discrets » : échantillon × 3 / 16 (environ -14 dB)

# Règles de douceur vérifiées par --verifier.
CRETE_MAX = 16384      # -6 dBFS au réglage « normaux »
DUREE_MAX_MS = 900
BORD_MAX = 64          # premier et dernier échantillons proches de zéro
NOTE_MAX_HZ = 1175     # fondamentale la plus haute permise pour tri et puls


def lire(chemin=CATALOGUE):
    """Renvoie {son: [(debut_ms, duree_ms, f0, f1, onde, volume)]} dans l'ordre du fichier."""
    sons = {}
    for n, ligne in enumerate(chemin.read_text(encoding="utf-8").splitlines(), 1):
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#"):
            continue
        p = [x.strip() for x in ligne.split("|")]
        if len(p) != 6:
            raise ValueError(f"sons.txt:{n} : six champs attendus")
        f = p[3].split(">")
        f0, f1 = int(f[0]), int(f[-1])
        if p[4] not in ("tri", "puls", "bruit"):
            raise ValueError(f"sons.txt:{n} : onde inconnue {p[4]}")
        sons.setdefault(p[0], []).append((int(p[1]), int(p[2]), f0, f1, p[4], int(p[5])))
    return sons


def synthetiser(notes):
    """Échantillons 16 bits signés du son, au réglage « normaux »."""
    fin = 0
    for debut, duree, *_ in notes:
        fin = max(fin, TAUX * debut // 1000 + TAUX * duree // 1000)
    fin += TAUX * QUEUE_MS // 1000
    acc = [0] * fin
    a = TAUX * ATTAQUE_MS // 1000
    for debut, duree, f0, f1, onde, volume in notes:
        s0 = TAUX * debut // 1000
        n = TAUX * duree // 1000
        r = min(n // 2, TAUX * RELACHE_MS // 1000)
        phase = 0
        lfsr = 1
        for i in range(n):
            fm = (f0 * 1000 * (n - i) + f1 * 1000 * i) // n          # fréquence en milli-hertz
            inc = fm * 4294967296 // (TAUX * 1000)
            avant = phase
            phase = (phase + inc) & 0xFFFFFFFF
            p = phase >> 16
            if onde == "tri":
                t = p if p < 32768 else 65535 - p                   # 0..32767
                v = ((t >> 11) * 2 - 15) * 2184                      # 16 marches, symétrique
            elif onde == "puls":
                v = 24000 if p < 16384 else -8000                    # 25 %, sans composante continue
            else:
                if phase < avant:                                    # un tour de phase : le bruit avance d'un pas
                    b = (lfsr ^ (lfsr >> 1)) & 1
                    lfsr = (lfsr >> 1) | (b << 14)
                v = 20000 if lfsr & 1 else -20000
            e = 4096
            if i < a:
                e = 4096 * i // a
            if i >= n - r:
                k = n - i
                e = min(e, 4096 * k * k // (r * r))
            e = e * (4096 - 1024 * i // n) // 4096                  # léger déclin pendant la note
            acc[s0 + i] += (v * e * volume * 10) >> 22
    sortie = [0] * fin
    y1 = y2 = 0
    for i in range(fin):
        x = acc[i] << 8
        y1 += ((x - y1) * FILTRE) >> 8
        y2 += ((y1 - y2) * FILTRE) >> 8
        s = y2 >> 8
        sortie[i] = max(-32767, min(32767, s))
    f = TAUX * FONDU_MS // 1000
    for i in range(fin - f, fin):
        g = ((fin - 1 - i) << 16) // f
        sortie[i] = (sortie[i] * g) >> 16
    return sortie


def discret(s):
    return [(x * DISCRET) >> 4 for x in s]


def octets(s):
    return struct.pack("<%dh" % len(s), *s)


def empreinte(s):
    return hashlib.sha256(octets(s)).hexdigest()


def mesures(s):
    crete = max(abs(x) for x in s)
    rms = math.sqrt(sum(x * x for x in s) / len(s))
    # Part d'énergie « aiguë » : énergie de la différence première rapportée à celle du signal (0 : très doux).
    diff = sum((s[i] - s[i - 1]) ** 2 for i in range(1, len(s)))
    aigu = diff / max(1, sum(x * x for x in s))
    return {
        "duree_ms": round(len(s) * 1000 / TAUX),
        "crete": crete,
        "crete_db": round(20 * math.log10(max(1, crete) / 32767), 1),
        "rms_db": round(20 * math.log10(max(1, rms) / 32767), 1),
        "aigu": round(aigu, 3),
        "debut": abs(s[0]),
        "fin": abs(s[-1]),
        "saut_max": max(abs(s[i] - s[i - 1]) for i in range(1, len(s))),
    }


def ecrire_wav(chemin, s):
    with wave.open(str(chemin), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(TAUX)
        w.writeframes(octets(s))


def page(sons, toutes, boucles=None):
    boucles = boucles or {}
    def ligne_boucle(nom, m):
        me = m["mesures"]
        barres = "".join(
            f"<span class=\"barre\" title=\"{lo}–{hi} Hz : {pc} %\"><i style=\"width:{max(1, round(pc))}%\"></i>"
            f"<small>{lo if lo < 1000 else str(lo // 1000) + ' k'}</small></span>"
            for (lo, hi), pc in zip(BANDES, me["spectre"]))
        if m["motif"]:
            ecouter = (f"<button onclick=\"jouer('{nom}')\">▶ normale</button> "
                       f"<button onclick=\"jouer('{nom}-discrete')\">▷ discrète</button>")
            saut = f"bords {me['debut']}, {me['fin']}"
        else:
            ecouter = (f"<button onclick=\"boucler('{nom}')\">▶ normale</button> "
                       f"<button onclick=\"boucler('{nom}-discrete')\">▷ discrète</button> "
                       f"<button class=\"jonction\" onclick=\"jouer('{nom}-jonction')\">⇄ jonction</button>")
            saut = f"{me['jonction']} / {me['p99']}"
        etalon = " <span class=\"etalon\">◆ étalon</span>" if nom == "emotion" else ""
        return (f"<tr><td><b>{nom}</b>{etalon}<br><small>{m['description']}</small></td><td>{ecouter}</td>"
                f"<td>{me['duree_ms'] / 1000:.1f} s</td><td>{me['crete_db']} dBFS</td><td>{me['rms_db']} dBFS</td>"
                f"<td>{saut}</td><td class=\"spectre\">{barres}</td></tr>")

    ambiances = {n for n, m in boucles.items() if m.get("ambiance")}
    groupes = [
        ("Le thème de Pilou", [n for n in boucles if n.startswith("pilou-")]),
        ("Les campagnes", [n for n in boucles if not n.startswith(("pilou-", "fin-")) and n not in ambiances]),
        ("Les fins (jouées une fois)", [n for n in boucles if n.startswith("fin-")]),
        ("Les ambiances (selon le décor)", [n for n in boucles if n in ambiances]),
    ]
    entete = ("<div class=\"tableau\"><table><tr><th>Morceau</th><th>Écouter</th><th>Durée</th><th>Crête</th><th>RMS</th>"
              "<th>Saut / p99</th><th>Spectre</th></tr>")
    blocs = "".join(f"<h3>{titre}</h3>{entete}{''.join(ligne_boucle(n, boucles[n]) for n in noms)}</table></div>"
                    for titre, noms in groupes if noms)
    bloc_musique = "" if not boucles else f"""
<h2>Musiques et ambiances</h2>
<p>Morceaux de <code>assets/musiques.txt</code>. Les boucles se lisent en boucle comme dans l'Aventure (fondu d'entrée
et de sortie à la lecture) ; « jonction » fait entendre leurs 4 dernières secondes suivies des 4 premières : on ne doit
rien entendre au passage. Les motifs de fin et le thème court se jouent une fois. ◆ <code>emotion</code> est l'étalon :
la boucle qu'Antoine a aimée dans « Trop grand pour mon pot ». Saut : écart entre le dernier et le premier échantillon,
comparé au 99ᵉ centile des écarts dans la boucle. Spectre : part d'énergie par bande (Hz).</p>
<p><button onclick="arreter()">⏹ arrêter</button></p>
{blocs}"""
    lignes = []
    for nom, m in toutes.items():
        lignes.append(
            f"<tr><td><b>{nom}</b></td>"
            f"<td><button onclick=\"jouer('{nom}')\">▶ normaux</button> "
            f"<button onclick=\"jouer('{nom}-discret')\">▷ discrets</button></td>"
            f"<td>{m['duree_ms']} ms</td><td>{m['crete_db']} dBFS</td><td>{m['rms_db']} dBFS</td>"
            f"<td>{m['aigu']}</td><td>{len(sons[nom])}</td></tr>")
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sons de Pilou</title>
<style>
:root {{ --fond:#f7f3ea; --texte:#2a2540; --bleu:#2f6fd6; --orange:#e07b1f; --ligne:#ddd3c0; }}
@media (prefers-color-scheme: dark) {{ :root {{ --fond:#1d1b29; --texte:#efe9da; --bleu:#7aa7f0; --orange:#f0a050; --ligne:#3a3650; }} }}
body {{ background:var(--fond); color:var(--texte); font:15px/1.5 system-ui, sans-serif; margin:0; padding:16px; }}
main {{ max-width:900px; margin:auto; }}
table {{ border-collapse:collapse; width:100%; }}
td, th {{ border-bottom:1px solid var(--ligne); padding:6px 8px; text-align:left; }}
button {{ font:inherit; border:2px solid var(--bleu); background:none; color:var(--bleu); border-radius:6px; padding:2px 10px; cursor:pointer; }}
button + button {{ border-color:var(--orange); color:var(--orange); border-style:dashed; }}
.tableau {{ overflow-x:auto; }}
button.jonction {{ border-style:dotted; }}
.spectre {{ white-space:nowrap; }}
.barre {{ display:inline-block; width:54px; margin-right:4px; vertical-align:middle; }}
.barre i {{ display:block; height:8px; background:var(--bleu); border-radius:2px; }}
.barre small {{ font-size:11px; opacity:.75; }}
td small {{ opacity:.8; }}
.etalon {{ color:var(--orange); font-weight:600; }}
</style></head><body><main>
<h1>Sons de Pilou</h1>
<p>Synthétisés depuis <code>assets/sons.txt</code> par <code>outils/sons/sons.py</code> ; le PC et le téléphone
calculent les mêmes échantillons (<code>sons-reference.txt</code>). « Aigu » : part d'énergie dans les aigus (plus
bas = plus doux).</p>
<p><button onclick="tout()">▶ tout écouter</button></p>
<div class="tableau"><table><tr><th>Son</th><th>Écouter</th><th>Durée</th><th>Crête</th><th>RMS</th><th>Aigu</th><th>Notes</th></tr>
{''.join(lignes)}
</table></div>
{bloc_musique}
<script>
let lecteur = null;
function jouer(n) {{ if (lecteur) lecteur.pause(); lecteur = new Audio(n + '.wav'); lecteur.play(); return lecteur; }}
function boucler(n) {{ const a = jouer(n); a.loop = true; return a; }}
function arreter() {{ if (lecteur) lecteur.pause(); }}
async function tout() {{
  for (const n of {list(toutes)!r}) {{
    const a = jouer(n);
    await new Promise(ok => {{ a.onended = ok; }});
    await new Promise(ok => setTimeout(ok, 500));
  }}
}}
</script></main></body></html>
"""


def verifier(sons):
    erreurs = []
    attendu = {}
    if REFERENCE.exists():
        for l in REFERENCE.read_text(encoding="utf-8").splitlines():
            if l.startswith("#") or not l.strip():
                continue
            p = [x.strip() for x in l.split("|")]
            attendu[p[0]] = p
    if set(attendu) != set(sons):
        erreurs.append(f"référence : sons {sorted(set(attendu) ^ set(sons))} manquants ou en trop")
    for nom, notes in sons.items():
        s = synthetiser(notes)
        m = mesures(s)
        if nom in attendu and attendu[nom][3] != empreinte(s):
            erreurs.append(f"{nom} : empreinte différente de la référence")
        if m["crete"] > CRETE_MAX:
            erreurs.append(f"{nom} : crête {m['crete']} > {CRETE_MAX}")
        if m["duree_ms"] > DUREE_MAX_MS:
            erreurs.append(f"{nom} : {m['duree_ms']} ms > {DUREE_MAX_MS}")
        if m["debut"] > BORD_MAX or m["fin"] > BORD_MAX:
            erreurs.append(f"{nom} : bords non nuls ({m['debut']}, {m['fin']})")
        for debut, duree, f0, f1, onde, volume in notes:
            if onde != "bruit" and max(f0, f1) > NOTE_MAX_HZ:
                erreurs.append(f"{nom} : note à {max(f0, f1)} Hz > {NOTE_MAX_HZ}")
    if len(sons) > 12:
        erreurs.append(f"{len(sons)} sons : douze au plus")
    return erreurs


# ---------------------------------------------------------------- musiques et ambiances (assets/musiques.txt)

MUSIQUES = RACINE / "assets" / "musiques.txt"
REFERENCE_MUSIQUES = Path(__file__).resolve().parent / "musiques-reference.txt"
TONS = ("prologue", "humour", "mystere", "emotion")   # une boucle par ton, plus le prologue
THEME = ("pilou-10", "pilou-25", "pilou-40")          # le thème de Pilou, un par scène d'évolution
FINS = ("fin-bonne", "fin-douce-amere", "fin-mauvaise", "fin-secrete")
DUREE_MOTIF_MS = (3000, 8500)
DISCRETE = 3           # « discrète » : × 3 / 8 à la lecture (environ -8,5 dB)
CRETE_BOUCLE_MAX = 6000                # -14,7 dBFS : la musique reste bien sous les sons
DUREE_BOUCLE_MS = (30000, 60000)
DUREE_AMBIANCE_MS = (20000, 60000)
NOTE_MAX_BOUCLE_HZ = 1175

# Fréquences de l'octave 4 en milli-hertz ; les autres octaves par décalage (entiers positifs : mêmes partout).
GAMME = {"C": 261626, "C#": 277183, "D": 293665, "D#": 311127, "E": 329628, "F": 349228, "F#": 369994,
         "G": 391995, "G#": 415305, "A": 440000, "A#": 466164, "B": 493883}


def frequence(jeton):
    """Jeton → milli-hertz : « A4 », « F#3 » ou un nombre de hertz (bruit)."""
    if jeton[0].isdigit():
        return int(jeton) * 1000
    nom, octave = jeton[:-1], int(jeton[-1])
    f = GAMME[nom]
    return f << (octave - 4) if octave >= 4 else f >> (4 - octave)


def lire_musiques(chemin=MUSIQUES):
    """Renvoie ({id: morceau}, {décor: ambiance}). Un morceau : dict(ms, pas, filtre, voix=[...])."""
    morceaux, decors, voix, courant, note = {}, {}, None, None, ""
    for n, ligne in enumerate(chemin.read_text(encoding="utf-8").splitlines(), 1):
        ligne = ligne.strip()
        if ligne.startswith("#"):
            note = ligne.lstrip("# ")                 # le commentaire juste au-dessus d'un morceau le décrit
            continue
        if not ligne:
            continue
        p = [x.strip() for x in ligne.split("|")]
        if p[0] == "morceau":
            courant = morceaux[p[1]] = {"ms": int(p[2]), "pas": int(p[3]), "filtre": int(p[4]), "voix": [],
                                        "motif": len(p) > 5 and p[5] == "motif", "description": note}
        elif p[0] == "voix":
            if p[1] not in ("tri", "puls", "bruit"):
                raise ValueError(f"musiques.txt:{n} : onde inconnue {p[1]}")
            voix = {"onde": p[1], "volume": int(p[2]), "attaque": int(p[3]), "relache": int(p[4]),
                    "declin": int(p[5]), "tenue": int(p[6]), "jetons": p[7].split()}
            courant["voix"].append(voix)
        elif p[0] == "+":
            voix["jetons"] += p[1].split()
        elif p[0] == "decors":
            for d in p[2].split():
                decors[d] = p[1]
        else:
            raise ValueError(f"musiques.txt:{n} : ligne inconnue {p[0]}")
    return morceaux, decors


def notes_voix(jetons, pas, boucle=True):
    """[(pas de départ, longueur en pas, f0, f1)] ; la suite se répète ; dans une boucle, une note tenue au bout
    repart au début (dans un motif, elle s'arrête au bout)."""
    e = [jetons[k % len(jetons)] for k in range(pas)]
    notes = []
    for k, j in enumerate(e):
        if j in ("-", "."):
            continue
        longueur = 1
        while longueur < pas and (boucle or k + longueur < pas) and e[(k + longueur) % pas] == "-":
            longueur += 1
        f = j.split(">")
        notes.append((k, longueur, frequence(f[0]), frequence(f[-1])))
    return notes


def synthetiser_boucle(m):
    """Échantillons 16 bits de la boucle, au réglage « normale ». Le dernier échantillon enchaîne sur le premier.
    Un motif (joué une fois) a une queue de 20 ms, un seul tour de filtre et un fondu final : il finit à zéro."""
    pas_ech = TAUX * m["ms"] // 1000
    motif = m["motif"]
    total = pas_ech * m["pas"] + (TAUX * QUEUE_MS // 1000 if motif else 0)
    acc = [0] * total
    for v in m["voix"]:
        onde, volume, d = v["onde"], v["volume"], v["declin"]
        for k, longueur, f0, f1 in notes_voix(v["jetons"], m["pas"], not motif):
            s0 = k * pas_ech
            n = longueur * pas_ech
            if v["tenue"] > 0:
                n = min(n, TAUX * v["tenue"] // 1000)
            a = min(n // 2, TAUX * v["attaque"] // 1000)
            r = min(n // 2, TAUX * v["relache"] // 1000)
            phase = 0
            lfsr = 1
            for i in range(n):
                fm = (f0 * (n - i) + f1 * i) // n
                inc = fm * 4294967296 // (TAUX * 1000)
                avant = phase
                phase = (phase + inc) & 0xFFFFFFFF
                p = phase >> 16
                if onde == "tri":
                    t = p if p < 32768 else 65535 - p
                    x = ((t >> 11) * 2 - 15) * 2184
                elif onde == "puls":
                    x = 24000 if p < 16384 else -8000
                else:
                    if phase < avant:
                        b = (lfsr ^ (lfsr >> 1)) & 1
                        lfsr = (lfsr >> 1) | (b << 14)
                    x = 20000 if lfsr & 1 else -20000
                e = 4096
                if i < a:
                    e = 4096 * i // a
                if r > 0 and i >= n - r:
                    q = n - i
                    e = min(e, 4096 * q * q // (r * r))
                e = e * (4096 - d * i // n) // 4096
                acc[(s0 + i) % total] += (x * e * volume * 10) >> 24
    # Passe-bas en anneau : un premier tour met le filtre en régime, le second donne la sortie ; ainsi la fin
    # enchaîne sur le début comme si la boucle tournait depuis toujours.
    f = m["filtre"]
    sortie = [0] * total
    y1 = y2 = 0
    for tour in range(1 if motif else 2):
        for i in range(total):
            y1 += (((acc[i] << 8) - y1) * f) >> 8
            y2 += ((y1 - y2) * f) >> 8
            if tour or motif:
                sortie[i] = max(-32767, min(32767, y2 >> 8))
    if motif:
        q = TAUX * FONDU_MS // 1000
        for i in range(total - q, total):
            g = ((total - 1 - i) << 16) // q
            sortie[i] = (sortie[i] * g) >> 16
    return sortie


def fft(x):
    n = len(x)
    if n == 1:
        return x
    pair, impair = fft(x[0::2]), fft(x[1::2])
    w = [complex(math.cos(2 * math.pi * k / n), -math.sin(2 * math.pi * k / n)) * impair[k] for k in range(n // 2)]
    return [pair[k] + w[k] for k in range(n // 2)] + [pair[k] - w[k] for k in range(n // 2)]


BANDES = ((0, 150), (150, 500), (500, 1500), (1500, 4000), (4000, 11025))


def spectre(s, taille=4096, fenetres=12):
    """Part d'énergie (en %) par bande de fréquences, moyennée sur des fenêtres de Hann réparties sur la boucle."""
    energie = [0.0] * len(BANDES)
    hann = [0.5 - 0.5 * math.cos(2 * math.pi * i / taille) for i in range(taille)]
    for w in range(fenetres):
        d = (len(s) - taille) * w // max(1, fenetres - 1)
        X = fft([s[d + i] * hann[i] for i in range(taille)])
        for k in range(1, taille // 2):
            hz = k * TAUX / taille
            for b, (lo, hi) in enumerate(BANDES):
                if lo <= hz < hi:
                    energie[b] += abs(X[k]) ** 2
    t = sum(energie) or 1
    return [round(100 * e / t, 1) for e in energie]


def mesures_boucle(s):
    m = mesures(s)
    diffs = sorted(abs(s[i] - s[i - 1]) for i in range(1, len(s)))
    m["jonction"] = abs(s[0] - s[-1])
    m["p99"] = diffs[len(diffs) * 99 // 100]
    m["spectre"] = spectre(s)
    return m


def discrete(s):
    return [(x * DISCRETE) >> 3 for x in s]


def verifier_musiques(morceaux, decors):
    erreurs = []
    attendu = {}
    if REFERENCE_MUSIQUES.exists():
        for l in REFERENCE_MUSIQUES.read_text(encoding="utf-8").splitlines():
            if l.startswith("#") or not l.strip():
                continue
            p = [x.strip() for x in l.split("|")]
            attendu[p[0]] = p
    if set(attendu) != set(morceaux):
        erreurs.append(f"référence des musiques : {sorted(set(attendu) ^ set(morceaux))} manquants ou en trop")
    for t in TONS + THEME + FINS + tuple(f"{t}-{v}" for t in TONS[1:] for v in ("calme", "tension")):
        if t not in morceaux:
            erreurs.append(f"musique « {t} » absente")
    for a in set(decors.values()):
        if a not in morceaux:
            erreurs.append(f"ambiance « {a} » citée par des décors mais absente")
    for nom, m in morceaux.items():
        s = synthetiser_boucle(m)
        me = mesures_boucle(s)
        if nom in attendu and attendu[nom][3] != empreinte(s):
            erreurs.append(f"{nom} : empreinte différente de la référence")
        if me["crete"] > CRETE_BOUCLE_MAX:
            erreurs.append(f"{nom} : crête {me['crete']} > {CRETE_BOUCLE_MAX}")
        ambiances = set(decors.values())
        lo, hi = DUREE_MOTIF_MS if m["motif"] else DUREE_AMBIANCE_MS if nom in ambiances else DUREE_BOUCLE_MS
        if not lo <= me["duree_ms"] <= hi:
            erreurs.append(f"{nom} : {me['duree_ms']} ms hors de {lo}–{hi}")
        if m["motif"]:
            if me["debut"] > BORD_MAX or me["fin"] > BORD_MAX:
                erreurs.append(f"{nom} : bords du motif non nuls ({me['debut']}, {me['fin']})")
        elif me["jonction"] > me["p99"]:
            erreurs.append(f"{nom} : saut à la jonction {me['jonction']} > p99 {me['p99']} (clic de boucle)")
        for v in m["voix"]:
            if len(v["jetons"]) > m["pas"] or m["pas"] % len(v["jetons"]):
                erreurs.append(f"{nom} : une voix a {len(v['jetons'])} jetons pour {m['pas']} pas")
            if v["onde"] != "bruit":
                for _, _, f0, f1 in notes_voix(v["jetons"], m["pas"], not m["motif"]):
                    if max(f0, f1) > NOTE_MAX_BOUCLE_HZ * 1000:
                        erreurs.append(f"{nom} : note à {max(f0, f1) // 1000} Hz > {NOTE_MAX_BOUCLE_HZ}")
    return erreurs


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sons = lire()
    morceaux, decors = lire_musiques()
    if "--reference" in sys.argv:
        l = ["# son | échantillons | crête | sha256 des échantillons 16 bits petit-boutiste (« normaux »)"]
        for nom, notes in sons.items():
            s = synthetiser(notes)
            l.append(f"{nom} | {len(s)} | {max(abs(x) for x in s)} | {empreinte(s)}")
        REFERENCE.write_text("\n".join(l) + "\n", encoding="utf-8", newline="\n")
        l = ["# boucle | échantillons | crête | sha256 des échantillons 16 bits petit-boutiste (« normale »)"]
        for nom, m in morceaux.items():
            s = synthetiser_boucle(m)
            l.append(f"{nom} | {len(s)} | {max(abs(x) for x in s)} | {empreinte(s)}")
        REFERENCE_MUSIQUES.write_text("\n".join(l) + "\n", encoding="utf-8", newline="\n")
        print(f"{REFERENCE.name} : {len(sons)} sons ; {REFERENCE_MUSIQUES.name} : {len(morceaux)} boucles")
        return 0
    if "--verifier" in sys.argv:
        erreurs = verifier(sons) + verifier_musiques(morceaux, decors)
        for e in erreurs:
            print("ERREUR", e)
        print(f"{len(sons)} sons, {len(morceaux)} boucles, {len(erreurs)} erreur(s)")
        return 1 if erreurs else 0
    ECOUTE.mkdir(exist_ok=True)
    toutes = {}
    print(f"{'son':<12}{'durée':>7}{'crête':>9}{'rms':>8}{'aigu':>7}{'saut':>7}{'bords':>9}")
    for nom, notes in sons.items():
        s = synthetiser(notes)
        ecrire_wav(ECOUTE / f"{nom}.wav", s)
        ecrire_wav(ECOUTE / f"{nom}-discret.wav", discret(s))
        m = toutes[nom] = mesures(s)
        print(f"{nom:<12}{m['duree_ms']:>5}ms{m['crete_db']:>7}dB{m['rms_db']:>6}dB{m['aigu']:>7}{m['saut_max']:>7}"
              f"{m['debut']:>5},{m['fin']:<3}")
    boucles = {}
    print(f"\n{'boucle':<12}{'durée':>7}{'crête':>9}{'rms':>8}{'saut':>7}{'p99':>6}  spectre % (<150, <500, <1,5 k, <4 k, plus)")
    for nom, m in morceaux.items():
        s = synthetiser_boucle(m)
        ecrire_wav(ECOUTE / f"{nom}.wav", s)
        ecrire_wav(ECOUTE / f"{nom}-discrete.wav", discrete(s))
        if not m["motif"]:
            q = TAUX * 4
            ecrire_wav(ECOUTE / f"{nom}-jonction.wav", s[-q:] + s[:q])
        me = mesures_boucle(s)
        boucles[nom] = dict(m, mesures=me, ambiance=nom in set(decors.values()))
        print(f"{nom:<12}{me['duree_ms'] / 1000:>6.1f}s{me['crete_db']:>7}dB{me['rms_db']:>6}dB{me['jonction']:>7}"
              f"{me['p99']:>6}  {me['spectre']}")
    (ECOUTE / "ecoute.html").write_text(page(sons, toutes, boucles), encoding="utf-8")
    print(f"→ {ECOUTE / 'ecoute.html'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
