#!/usr/bin/env python3
"""Sons de Pilou : synthèse de référence (docs/SONS.md).

Lit assets/sons.txt et calcule les échantillons exactement comme Sons.cs (PC) et Sons.java (Android) : tout est en
entiers (accumulateur de phase 32 bits, enveloppe en 1/4096, décalages à droite qui arrondissent vers le bas dans les
trois langages), donc les trois donnent les mêmes octets.

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


def page(sons, toutes):
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
</style></head><body><main>
<h1>Sons de Pilou</h1>
<p>Synthétisés depuis <code>assets/sons.txt</code> par <code>outils/sons/sons.py</code> ; le PC et le téléphone
calculent les mêmes échantillons (<code>sons-reference.txt</code>). « Aigu » : part d'énergie dans les aigus (plus
bas = plus doux).</p>
<p><button onclick="tout()">▶ tout écouter</button></p>
<div class="tableau"><table><tr><th>Son</th><th>Écouter</th><th>Durée</th><th>Crête</th><th>RMS</th><th>Aigu</th><th>Notes</th></tr>
{''.join(lignes)}
</table></div>
<script>
let lecteur = null;
function jouer(n) {{ if (lecteur) lecteur.pause(); lecteur = new Audio(n + '.wav'); lecteur.play(); return lecteur; }}
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


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sons = lire()
    if "--reference" in sys.argv:
        l = ["# son | échantillons | crête | sha256 des échantillons 16 bits petit-boutiste (« normaux »)"]
        for nom, notes in sons.items():
            s = synthetiser(notes)
            l.append(f"{nom} | {len(s)} | {max(abs(x) for x in s)} | {empreinte(s)}")
        REFERENCE.write_text("\n".join(l) + "\n", encoding="utf-8", newline="\n")
        print(f"{REFERENCE.name} : {len(sons)} sons")
        return 0
    if "--verifier" in sys.argv:
        erreurs = verifier(sons)
        for e in erreurs:
            print("ERREUR", e)
        print(f"{len(sons)} sons, {len(erreurs)} erreur(s)")
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
    (ECOUTE / "ecoute.html").write_text(page(sons, toutes), encoding="utf-8")
    print(f"→ {ECOUTE / 'ecoute.html'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
