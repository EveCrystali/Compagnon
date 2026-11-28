# Les sons de Pilou

Une petite identité sonore 8 bits, discrète, la même sur PC et sur téléphone. Réglage « Sons » sur
**normaux par défaut** (Antoine, 28 novembre 2026) ; « discrets » et « aucun » restent au choix.

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

- jamais si le réglage est « aucun » ;
- un son qui **répond à un geste du joueur** (`caresse`, `choix`, `achat`, `peche`, `aventure`, sons de Chasse aux
  bugs) passe par le **volume multimédia, quel que soit le mode de sonnerie**, comme dans n'importe quel jeu ; il ne
  se tait que pendant un appel ou une visio (téléphone : mode audio de communication ; PC : visio, réunion,
  présentation), en « Ne pas déranger » silence total, ou volume multimédia à zéro ;
- un son **spontané** se tait en plus quand Pilou est caché : plein écran, caché à la main (PC) ; silencieux ou
  vibreur (téléphone) ;
- les sons **spontanés** (`mot`, `expedition`, `campagne`, `palier`, `succes`) jamais pendant la saisie, et **six par
  heure au plus** ; les sons qui répondent à un geste (clic, choix, achat) partent même si on vient de taper ;
- jamais en rafale : 1,2 s entre deux sons, 4 s avant de rejouer le même (clics répétés sur Pilou).

**Un réglage coché qui ne produit rien sans explication est un défaut.** Sur le téléphone, chaque son qui n'a pas
pu partir est noté pour le diagnostic (« son X non joué : raison », cinq lignes au plus, rien de personnel) ; les
Réglages ont un bouton **« Essayer »** sous Sons et Musique : il joue un son tout de suite (même au réglage « Aucun »,
sans la garde d'espacement) ou dit en clair pourquoi rien ne peut sortir (« volume multimédia à zéro », « téléphone en
appel ou en visio »).

Le piège corrigé en v1 : le téléphone taisait tout dès qu'il était en vibreur ou en silencieux, volume multimédia
monté ou pas, sans rien dire ; beaucoup de gens laissent leur téléphone en vibreur. Le PC avait le même genre de
piège, plus discret : un geste dans la fenêtre Aventure se taisait si Pilou était caché à la main ou si Windows
signalait un plein écran.

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

## Musiques et ambiances de l'Aventure

Des boucles et des motifs synthétisés de la même manière que les sons, décrites dans **`assets/musiques.txt`** (aucun fichier audio
importé, mélodies originales), mêmes échantillons sur PC (`Musique.cs`), téléphone (`Musique.java`) et
`outils/sons/sons.py` ; empreintes dans **`outils/sons/musiques-reference.txt`**, testées par `MusiqueTests.cs` et
`MusiqueTest.java`.

| Boucle | Quand | Durée | Caractère |
|---|---|---|---|
| `prologue` | La colline d'en face | 32 s | do majeur, 120 à la noire, mélodie, basse, grelot |
| `humour` | campagnes au ton « humour » (La Grande Panne) | 35,5 s | piqué, basse « poum-tchac », bloc de bois |
| `mystere` | ton « mystère » (Le phare éteint) | 44,8 s | la mineur lent, nappe qui se relaie, cloche de brume, houle |
| `emotion` | ton « émotion » (Petit Nuage) | 48 s | boîte à musique, voix basse, basse tenue |
| `vent` | décors de plein air, de col, de sommet | 40 s | rafales de souffle qui se relaient, sifflement à peine |
| `pluie` | jardin après l'orage, place sous la pluie, vitre embuée | 32 s | deux fonds de pluie, quelques gouttes |
| `hall` | halls, tours, archives, caves | 36 s | souffle grave, bourdon, pas lointains et leur écho |
| `mer` | ports, jetées, grèves, falaises | 42 s | ressac continu, vagues qui montent et se retirent |

La musique suit la campagne ouverte (le prologue a la sienne, les autres celle de leur ton ; un ton sans boucle reste
muet) et l'ambiance suit le décor (lignes `decors` du fichier ; un décor non cité n'a pas d'ambiance). Les deux jouent
ensemble ; changer de décor croise les ambiances.

Règles :

- **réglage séparé** « Musique : aucune / discrète / normale », **« discrète » par défaut** (× 3/8 à la lecture,
  environ -8,5 dB) ; un réglage déjà enregistré garde son choix ;
- **seulement dans l'Aventure** : la fenêtre Aventure au premier plan (PC), la lecture d'une campagne à l'écran avec le
  focus (téléphone) ; perdre le premier plan, réduire, fermer coupe en fondu ;
- **au volume multimédia, quel que soit le mode de sonnerie** (comme un jeu) ; silence pendant un appel ou une visio
  (téléphone), en visio, réunion ou présentation (PC) ;
- **très bas** : crête au plus 6000 (-14,7 dBFS) au réglage « normale », de -19 à -26 dBFS en pratique, RMS vers
  -30 dBFS ; les sons de Pilou restent devant ;
- **fondus** : entrée en 1,5 s, sortie en 1 s ;
- **boucle sans clic** : les notes qui dépassent la fin repartent au début, et le passe-bas tourne en anneau (un tour de
  mise en régime, puis la sortie) ; `--verifier` exige que le saut entre le dernier et le premier échantillon ne
  dépasse pas le 99ᵉ centile des sauts dans la boucle.

### Second lot : le thème de Pilou, calme et tension, les fins

Étalon : `emotion` (boîte à musique, voix basse, 80 à la noire), la boucle qu'Antoine a aimée dans la scène d'évolution
« Trop grand pour mon pot ». Le second lot est écrit dans la même main : mélodie simple et chantante, timbre doux, tempo
posé, tendre et un peu drôle.

| Morceau | Genre | Durée | En une phrase |
|---|---|---|---|
| `pilou-10` | boucle | 42,6 s | Le thème de Pilou à la boîte à musique seule, pour la scène du niveau 10. |
| `pilou-25` | boucle | 42,6 s | Le même thème, avec une seconde voix liée dessous et une basse douce (niveau 25). |
| `pilou-40` | boucle | 42,6 s | Le petit ensemble : thème doublé à l'octave, seconde voix, basse qui marche, grelot (niveau 40). |
| `pilou-court` | motif | 4 s | La tête du thème, proposée pour le retour d'aventure et le palier (rien n'est remplacé). |
| `humour-calme` | boucle | 38,4 s | L'après-midi au bureau : une mélodie qui flâne et se rattrape d'un petit sol-sol. |
| `humour-tension` | boucle | 34,2 s | La pendule tourne, il faut choisir : notes répétées, basse piquée, tic-tac, rien de grave. |
| `mystere-calme` | boucle | 41,3 s | Une berceuse au phare : boîte à musique lente et houle au loin. |
| `mystere-tension` | boucle | 38,4 s | Un cœur qui bat un peu plus vite, l'horloge, une phrase qui interroge. |
| `emotion-calme` | boucle | 41,3 s | Encore plus doux que l'étalon : on se pose, la voix fredonne. |
| `emotion-tension` | boucle | 41 s | Le petit trac du bon choix : la mélodie monte jusqu'au ré aigu et se pose. |
| `fin-bonne` | motif | 6 s | La mélodie monte et se pose sur le do aigu, un grelot. |
| `fin-douce-amere` | motif | 7,2 s | La phrase descend, puis un dernier accord qui garde un peu d'espoir. |
| `fin-mauvaise` | motif | 5 s | Un « oups » gentil qui dégringole, rien qui fasse peur. |
| `fin-secrete` | motif | 7 s | Des arpèges qui montent comme des étincelles, puis le do majeur tout en haut. |

Le **thème de Pilou** a la même mélodie, le même tempo (90 à la noire) et la même grille dans ses trois versions : il
grandit avec Pilou sans changer d'air.

**Choisir le morceau** : le champ facultatif **`musique`** d'une scène ou d'un nœud vaut soit l'identifiant d'un
morceau (`pilou-25`, `fin-secrete`…), soit `calme` ou `tension` (la variante du ton de la campagne : `mystere-tension`
au phare). Sans champ, ou s'il nomme un morceau absent, c'est la boucle du ton. `Musique.Pour(campagne, ton, musique)`
(PC) et `Musique.pour(…)` (téléphone) font ce choix ; `Musique.Suivre` / `suivre` prennent la valeur du champ par un
dernier argument facultatif. Le prologue n'a pas de variante : `calme` ou `tension` y gardent sa boucle.

**Motifs** (genre `motif` sur la ligne `morceau`) : joués une fois, sans boucle (une queue de 20 ms, un fondu final,
ils commencent et finissent à zéro ; de 3 à 8,5 s). Le motif part tout de suite à son niveau, la boucle en cours
s'efface en 1 s, puis le silence ; il ne rejoue qu'après qu'un autre morceau a été demandé.

Format d'une boucle : `morceau | id | ms par pas | pas | filtre [| motif]`, puis ses voix
`voix | onde | volume | attaque ms | relâche ms | déclin | tenue max ms | jetons`, une ligne `+ | jetons` continue la
voix précédente. Un jeton par pas : une note (`C4`, `F#3`), une cadence de bruit en Hz, un glissé `de>à`, `-` tient,
`.` se tait ; une voix plus courte que le morceau se répète.

Lecture : PC par `waveOut` de Windows (winmm, sans bibliothèque ; `PlaySound` ne joue qu'un son à la fois), quatre
tampons de 100 ms remplis par la table de mixage `Melangeur` ; téléphone par un `AudioTrack` en flux, même table. La
sortie audio est rendue dès que tout s'est éteint.

`py outils/sons/sons.py` écrit aussi, dans `ecoute/`, chaque boucle (normale, discrète) et sa **jonction** (4 dernières
secondes puis 4 premières, pour entendre le passage), et la page d'écoute montre crête, RMS, saut et spectre par bande.
