# Les sons de Pilou

Une petite identité sonore 8 bits, discrète, la même sur PC et sur téléphone. **Coupée par défaut** (réglage
« Sons : aucun ») en attendant qu'Antoine tranche.

## Les sons

| Son | Moment | PC | Téléphone |
|---|---|---|---|
| `caresse` | clic sur Pilou (« pouic ») | clic, « ♥ Caresser » | Accueil, lecture d'une campagne |
| `mot` | petit mot spontané (très doux) | `FenetrePresence.Parler` | — (le mot du soir reste une notification muette) |
| `aventure` | ouverture de la fenêtre Aventure | `OuvrirAventure` | `ouvrirLecture` |
| `choix` | choix validé dans une campagne | `FenetreAventure.Choisir` (si accepté) | `Lecture.choisir` |
| `achat` | achat en boutique | `FenetreBoutique.Acheter` (si réussi) | `PageBoutique.acheter` (envoyé au PC) |
| `peche` | ça mord ! | `Peche.AnimerPeche` (le « ! ») | — (pas de pêche sur le téléphone) |
| `expedition` | retour d'expédition | `FenetreExpedition.Rentre` | — (pas d'événement local) |
| `campagne` | retour de campagne | `PresenceCampagne.AnnoncerRetour` | — (la notification de retour sonne déjà) |
| `palier` | nouveau palier de complicité | `FenetrePresence.Parler` (famille `palier-`) | — |
| `succes` | quête, coffre, niveau, succès | `Recompenser`, `VerifierNiveau`, `VerifierSucces` | — (calculés sur le PC) |

Toutes les mélodies sont en do majeur pentatonique (do ré mi sol la), aucune note au-dessus du ré 6 (1175 Hz), moins
d'une seconde (la plus longue, `palier`, fait 840 ms).

## Quand un son a le droit de partir

`GardeSons` (PC) et `Sons.Garde` (téléphone), mêmes règles, mêmes tests :

- jamais si le réglage est « aucun » (défaut) ;
- jamais quand Pilou est caché : plein écran, présentation, visio, caché à la main (PC) ; appel, visio (mode audio de
  communication), silencieux ou vibreur (téléphone) ;
- les sons **spontanés** (`mot`, `expedition`, `campagne`, `palier`, `succes`) jamais pendant la saisie, et **six par
  heure au plus** ; les sons qui répondent à un geste (clic, choix, achat) partent même si on vient de taper ;
- jamais en rafale : 1,2 s entre deux sons, 4 s avant de rejouer le même (clics répétés sur Pilou).

Les sons accompagnent des moments qui passent déjà par la retenue de la présence (`Vivacite.cs`) : ils n'en créent
aucun et n'en consomment aucun.

## Une seule source, trois synthèses identiques

- **`assets/sons.txt`** décrit chaque son, note par note : `son | début ms | durée ms | fréquence (ou de>à) | onde | volume`.
  Ondes : `tri` (triangle 4 bits, la voix de Pilou), `puls` (impulsion 25 %, l'accompagnement grave), `bruit` (souffle ;
  la fréquence est la cadence du générateur).
- **`Sons.cs`** (PC), **`Sons.java`** (téléphone) et **`outils/sons/sons.py`** synthétisent en entiers seulement
  (accumulateur de phase 32 bits, enveloppe sur 4096, décalages à droite) : mêmes octets partout.
- **`outils/sons/sons-reference.txt`** : longueur, crête et SHA-256 de chaque son. Testé par `SonsTests.cs` et
  `SonsTest.java`.

Le grain : 22 050 Hz mono 16 bits ; attaque de 4 ms et relâche quadratique de 60 ms par note (pas de clic) ; passe-bas à
deux pôles vers 1,4 kHz qui arrondit le triangle 4 bits ; fondu final de 8 ms (le son finit à zéro). Crête au plus
-6 dBFS en « normaux » (de -8 à -16 dBFS en pratique) ; « discrets » = × 3/16, environ -14,5 dB de moins.

Lecture : PC par `PlaySound` de Windows (winmm, depuis la mémoire, sans bibliothèque) ; téléphone par un `AudioTrack`
statique par son (usage « jeu », comme la Chasse aux bugs).

## Écouter, changer un son

```bash
py outils/sons/sons.py               # outils/sons/ecoute/*.wav et ecoute.html (normaux et discrets), mesures
py outils/sons/sons.py --verifier    # référence et règles de douceur (crête, durée, bords, aiguës)
py outils/sons/sons.py --reference   # après un changement voulu de sons.txt
```

`ecoute/` n'est pas versionné. Les sons de la Chasse aux bugs (téléphone) restent à part, avec leur propre case.
