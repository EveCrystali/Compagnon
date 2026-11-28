# La présence de Pilou au quotidien

> « On doit s'attacher à notre Pilou petit à petit, l'aimer… aimer le retrouver comme simple compagnon en dehors des
> campagnes ; il devient notre ami virtuel qui nous suit dans la poche et sur PC. Il communique avec nous, sans jamais
> entrer dans un rôle de spammeur : on doit sentir sa présence sans qu'elle dérange. » (Antoine)

Pilou parle peu, au bon moment, avec ses mots à lui. Il se souvient de ce qu'on a vécu ensemble, il s'attache, et il
écrit son journal. Rien de mécanique, rien de culpabilisant : on peut l'oublier une semaine, il est content de nous
retrouver, et la complicité n'a pas baissé.

## Les règles (les mêmes sur PC et téléphone)

| | PC | Téléphone |
|---|---|---|
| Petits mots spontanés | **au plus 3 par jour**, espacés d'au moins **90 min** | **au plus 1 par jour** : le mot du soir |
| Quand | premier retour au clavier du jour ; retour après une vraie pause (au moins **45 min** sans clavier ni souris) ; fin de journée (après 18 h, une fois **1 h 30** de présence dans la journée) | entre **19 h et 20 h 30** (minute tirée de la date et de l'appareil), rattrapé jusqu'à 21 h 30 si le téléphone dormait ; **jamais la nuit**, jamais en journée |
| Jamais | pendant la saisie (frappe depuis moins de 4 s), en plein écran, présentation, visio ou réunion, quand une IA attend, pendant une campagne, une visite, une expédition, un mini-jeu, quand Pilou est caché, tenu par la souris, ou quand une autre phrase est à l'écran | quand l'app est ouverte (le mot est alors en tête de l'Accueil) ; aucune relance ; une notification ignorée s'efface d'elle-même au bout de 3 h |
| Budget | **commun avec les réactions cosmétiques** : il faut que la retenue (`Vivacite.cs`, 2 min 30 de repos) soit libre, et le mot la relance | une seule notification, silencieuse (canal à importance basse, sans son ni vibration), **sans badge** |
| Moment manqué | le premier bonjour et le retour attendent au plus **25 min** un moment calme, puis passent leur tour ; la dernière place du jour est gardée pour le soir | pas de rattrapage le lendemain |
| Réglages | « Pilou me parle » : **peu** (1 par jour : le bonjour), **normalement** (3), **jamais** | « Pilou me parle » (peu ramène le mot du soir à « parfois », jamais coupe tout) ; « Le mot du soir » : **chaque jour** (par défaut), **parfois** (mardi, samedi, et le jeudi une semaine sur deux : 2 à 3 par semaine), **jamais** |

Les anciennes phrases à heure fixe (« bonjour ! », « bonne semaine ! », « bon week-end ! », « il se fait tard… ») passent
désormais par ces règles. Reste « bon appétit ! » vers midi, une réaction cosmétique comme les autres (et muette quand
Pilou ne parle « jamais »).

Le mot du jour du téléphone est le même toute la journée : en tête de l'Accueil, dans le widget, dans la bulle
flottante, et dans la notification du soir.

## Les petits mots

`assets/presence/mots.txt`, commun au PC et à l'app (573 mots ; les 636 lignes du fichier comptent aussi ses commentaires et lignes vides ; 90 caractères au plus, minuscules, voix de
`docs/LORE.md`). Une ligne : `famille|filtres|texte`.

- **Filtres** : `c1`…`c4` (palier de complicité minimal : les familles deviennent plus personnelles), `s1`, `s4`,
  `s34`… (stade d'évolution : la gouttelette parle comme un petit, l'Astral regarde les étoiles), `calin` ou `espiegle`
  (variante d'évolution).
- **Trous** : `{prenom}`, `{metier}`, `{niveau}`, `{objet}`, `{prise}`, `{plat}`, `{jours}`, `{annees}`, `{palier}`. Une
  ligne à trou n'est choisie que si la valeur est connue. Le prénom n'est proposé qu'**une fois sur cinq** au plus (une
  sur trois chez les Inséparables), hors des familles « prénom ».
- **Familles** : bonjour, retour-nuit, lundi, weekend, retour-1h, retour-jours, retour-weekend, retour-semaine,
  retour-long, fin-seance, soir, vendredi, tard, saison-(hiver, printemps, ete, automne), fete-(nouvel-an, chandeleur,
  printemps, poisson, musique, rentree, automne, citrouille, hiver, noel, reveillon), meteo-(pluie, orage, neige,
  brouillard, vent, chaleur, froid, degage), metier, niveau, objet, souvenir-(prologue, grande-panne, phare-eteint,
  petit-nuage : seulement après avoir fini la campagne, et à partir de Copain), souvenir-prise et souvenir-plat (la
  veille), pensee, curiosite-(code, tableur, texte, mail, musique, video, lecture, dessin, jeu : l'activité seulement,
  **jamais un titre de fenêtre ni un nom de fichier**), palier-1…4, date-(j7, m1, m6, j100, j200, j500, j1000, a),
  prenom-(demande, merci, refus), tel-soir.
- **Traits de personnalité** : leurs annonces et leurs répliques (`annonce-<trait>`, `trait-<trait>`) sont à part, dans
  `assets/presence/traits.txt`, et passent par le même choix et la même cadence ([TRAITS.md](TRAITS.md)).
- **Écrire** : jamais de reproche (« tu m'as manqué » oui, « tu m'as abandonné » jamais), jamais d'injonction (pas de
  « tu devrais »), jamais de culpabilité, rien de personnel. Le test `La_banque_a_plus_de_400_mots…` refuse quelques
  tournures interdites et toute ligne trop longue.

**Choix** (`Presence.Mot`) : le moment donne une liste de familles (annonces d'abord : date à fêter, nouveau palier ;
puis retrouvailles selon l'absence, fête du jour, lundi, week-end ; puis une rotation pondérée tirée de la graine) ; la
première qui a une ligne possible l'emporte. Dans une famille, une ligne **jamais dite** est préférée ; sinon, une
parmi le tiers dit **il y a le plus longtemps**. Une ligne ne revient donc qu'après toutes les autres de sa famille.
Mémoire : les 900 dernières lignes dites (identifiant, jour). **Graine** : `date|appareil|n° du mot du jour` (PC),
`date|appareil|tel` (téléphone) : reproductible, testable, différente d'un appareil à l'autre.

## La complicité

Une jauge qui **monte lentement et ne baisse jamais**. Points du groupe :

```
Σ appareils (minutes ensemble ÷ 10 + caresses + 2 × soins + 2 × jeux)
+ 10 × jours ensemble + 5 × jours qui suivent un autre jour ensemble + 60 × campagnes finies
```

- **Plafonds par jour et par appareil** (au-delà, rien ne compte, rien n'est retiré) : 180 min ensemble, 10 caresses,
  6 soins, 6 jeux. Minutes ensemble : sur PC, la personne est là (clavier ou souris dans la minute) et Pilou est à
  l'écran ; sur téléphone, l'app est ouverte. Jeux : petits jeux gagnés, pêche, cuisine, Chasse aux bugs.
- **Jours ensemble** : l'union des jours vus par tous les appareils (un jour sur PC et téléphone compte une fois). Les
  jours qui se suivent rapportent un peu plus ; s'absenter ne retire rien.
- **Paliers** (annoncés **une fois** dans le groupe, sans récompense) : Connaissance (0), **Copain** (150), **Ami**
  (700), **Meilleur ami** (2 500), **Inséparables** (7 000). Pour un joueur régulier : Copain en une petite semaine, Ami
  en un mois environ, Meilleur ami en trois mois, Inséparables en sept à huit mois.
- **Ce qu'ils ouvrent** : des familles de phrases plus personnelles (`c1`…`c4`) ; des petits gestes (réglage « Petits
  gestes de complicité ») : à partir de Copain il te fait signe quand tu reviens (PC : il salue en sautillant ; téléphone :
  un petit bond à la première ouverture du jour), à partir d'Ami il s'assoupit quand tu travailles encore après 23 h,
  à partir de Meilleur ami il se tourne vers toi d'un clin d'œil ; les souvenirs de campagne à partir de Copain ; le
  prénom un peu plus souvent chez les Inséparables.
- **Dates** (fêtées **une fois**, sobrement, à la place du bonjour ou du mot du soir) : 7, 100, 200, 500 et 1 000 jours
  ensemble ; un mois et six mois après l'adoption ; chaque anniversaire de l'adoption. Une date passée de plus d'une
  semaine n'est plus fêtée (on ne célèbre pas en retard). L'adoption est le premier jour ensemble connu du groupe (pour
  qui avait déjà Pilou, le jour où cette version est arrivée).

Où la voir : PC, clic droit → **Progrès** (palier, jours ensemble, jauge de signes ■■■□□) et le pied du Journal ;
téléphone, la carte **Pilou et moi** de l'Accueil (barre bleue vers le palier suivant).

## Le journal de Pilou

Chaque jour où il s'est passé quelque chose, Pilou écrit **une entrée de 1 à 3 phrases**, de son point de vue, à partir
des **seuls faits du jour** : temps passé ensemble, temps de travail, activité principale, heure tardive, jeux gagnés,
caresses, soins, prises (la plus belle), plats, quêtes réussies, météo, campagne finie ou avancée, visite, niveau atteint,
métier monté, expédition, objet acheté. Jamais de titre, de fichier, de ville, de nom d'ami.

- **Gabarits** : `assets/presence/journal.txt` (même format). La chose la plus marquante d'abord (une campagne finie,
  un niveau, un métier, une prise rare…), puis, selon le tirage du jour, un **mot appris** lié à l'activité (« J'ai
  appris un mot : refactoriser. Je ne sais pas ce que ça veut dire, mais je l'ai dit trois fois. ») ou la première phrase
  d'une deuxième chose, et parfois une petite conclusion. Un seul « Aujourd'hui » par entrée. Trois phrases au plus.
- **Humeur du jour** (le petit dessin) : fête (campagne finie, niveau), tendre (beaucoup de caresses), joie (jeux, prise
  rare, visite), fatigué (très tard, très long), soigné, appliqué, tranquille. Chacune a aussi son signe (★ ♥ ☀ ☾ ✎ ·).
- **Identique des deux côtés, par régénération** : on ne synchronise pas les textes mais les **faits** (compacts). Chaque
  appareil publie ses faits des 7 derniers jours ; chacun garde, par jour, les faits de chaque appareil, et les fusionne
  (**maximum** des nombres, la prise la plus rare, le métier au plus haut grade, la météo la plus marquante : ni l'ordre
  d'arrivée ni les doublons n'y changent rien, et ce qu'un téléphone a déjà crédité au PC n'est jamais compté deux fois).
  L'entrée ne dépend que du jour et des faits fusionnés : le PC et le téléphone écrivent mot pour mot la même chose.
- **Conservation** : les 14 derniers jours restent ouverts (un appareil en retard peut encore compléter) ; ensuite le
  jour est figé. 400 jours gardés.
- **Où le lire** : PC, clic droit → **📖 Journal…** (fenêtre rétro, ◀ ▶ ou flèches du clavier) ;
  téléphone, la carte **Pilou et moi** de l'Accueil (◀ ▶).
- Réglage « Tenir son journal » : coupé, plus aucun fait n'est noté ; les pages déjà écrites restent.

## Le prénom (facultatif)

Pilou demande **une seule fois**, gentiment, comment tu t'appelles (ou un surnom), quand vous êtes au moins Copains :
sur PC, un petit mot dans sa bulle à un retour de pause (un clic ouvre une petite fenêtre) ; sur téléphone, dans la carte
Pilou et moi. **Refuser est aussi simple qu'accepter** : deux boutons de même poids, et fermer la fenêtre vaut « je
préfère ne pas dire ». Il ne redemande jamais.

- Stocké localement (`presence.txt` sur PC, préférences sur le téléphone), **synchronisé seulement dans le groupe
  chiffré** de tes appareils. **Jamais envoyé aux amis** : il n'entre ni dans la vitrine, ni dans les messages entre
  Pilou, ni dans le message du téléphone, ni dans le compteur du groupe (test
  `Le_prenom_reste_dans_le_groupe_chiffre…`).
- 16 caractères au plus, nettoyé. Modifiable et effaçable (PC : Réglages ; téléphone : Réglages → Pilou et moi).
  Le choix le plus récent l'emporte dans tout le groupe (effacer compris).
- Utilisé avec parcimonie dans les petits mots (voir plus haut).

## Synchronisation

Un **message dédié**, sur un **sujet à part** du relais (`Presence.Sujet(code)`, HMAC « pilou-presence-v1 »), chiffré
avec le code du groupe comme les autres. Les anciens appareils ne l'écoutent pas ; le message du téléphone et le compteur
du groupe ne grossissent pas (`Telephone.cs`). Format texte, une ligne par champ :

```
pilou-presence 1
a <appareil>            k pc|tel            t <ms>
c <minutes> <caresses> <soins> <jeux>       (compteurs qui ne font que monter)
j <premier jour> <jours en hexadécimal, un bit par jour>
f <campagnes finies>    pa <palier annoncé>  fe <dates fêtées>
n <ms> <prénom>         q 1 (prénom déjà demandé)
d <jour> <faits>        (les 7 derniers jours)
```

Fusion : maximum par compteur et par appareil, union des jours, des campagnes et des dates, prénom le plus récent :
idempotente. Le message reste sous 2 750 octets (les faits les plus anciens partent d'abord). Publication sur
changement, au plus une fois par quart d'heure (tout de suite pour le prénom, une annonce ou une date), puis toutes les
6 h ; lecture toutes les 3 min (PC) ou 5 min (service du téléphone) et à l'ouverture de l'app.

## Fichiers

| | |
|---|---|
| `apps/PilouBureau/Presence.cs`, `EtatPresence.cs` | le moteur (sans WPF) : banque, choix, cadence, complicité, faits, journal, message, état |
| `android/.../Presence.java` | sa copie exacte, sans dépendance Android |
| `apps/PilouBureau/FenetrePresence.cs` | sur l'overlay : observation, petits mots, gestes, synchronisation (le menu est dans `MenuPortes.cs`) |
| `apps/PilouBureau/FenetreJournal.cs` | la fenêtre Journal et la petite fenêtre du prénom |
| `android/.../PresenceTel.java`, `PresenceVue.java`, `MotDuSoir.java` | état, carte de l'Accueil, réglages, notification du soir |
| `assets/presence/mots.txt`, `journal.txt` | les textes, communs |
| `presence.txt` (dossier de Pilou, jamais le dossier partagé) | l'état du PC ; préférence `presence` sur le téléphone, même format |

## Tests

- C# (`tests/PresenceTests.cs`) : banque (taille, longueur, tournures interdites, trous connus, au moins trois lignes par
  famille), non-répétition, déterminisme, parcimonie du prénom, familles selon le moment, **au plus trois mots par jour**,
  **rien sans calme**, expiration sans relance, mot du soir entre 19 h et 20 h 30 et 2 à 3 fois par semaine en
  « parfois », **complicité qui ne baisse jamais et ne compte rien deux fois** (messages relus, en désordre, en double),
  plafonds, paliers et dates fêtées une fois, **journal identique** sur deux appareils qui s'écrivent en désordre, fusion
  commutative, associative et idempotente, **prénom jamais chez les amis**, état relu à l'identique, message sous la
  limite du relais.
- **Vecteurs partagés** : `android/app/src/test/resources/presence-vecteurs.txt`, écrits par le PC
  (`PILOU_REGENERER=1 dotnet test apps/PilouBureau/tests`), rejoués ligne à ligne par `PresenceTest.java` (mots, journal,
  fusion, mot du soir, totaux, messages, réception, cadence).
- Java : `PresenceTest` (vecteurs, banque, rythme du téléphone, complicité, prénom), `PresenceTelTest` (Robolectric : un
  mot du soir par jour au plus, jamais la nuit ni en journée, « jamais » coupe tout, plafonds, prénom) ; captures
  `presence-accueil`, `presence-accueil-long`, `presence-reglages-long` dans l'artefact `captures-ui`.

## Essais (PC)

`--essai=mot` (cinq petits mots, un toutes les 7 s, à des moments différents), `--essai=journal` (la fenêtre Journal),
`--essai=complicite` (annonce d'un palier avec le signe et le clin d'œil, puis le journal). Données de démonstration en
mémoire : rien n'est écrit ni publié.

## Pas vérifié sur un vrai appareil

Rien de tout cela n'a tourné sur un vrai Windows ni un vrai téléphone : la cadence réelle d'une journée, la fenêtre
Journal à 125 % et 150 %, la notification du soir (Doze peut la retarder de quelques minutes, jamais l'avancer), le
widget, la bulle, la synchronisation entre deux appareils réels.
