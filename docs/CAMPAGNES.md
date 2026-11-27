# Campagnes : des histoires à choix, en temps réel

Une campagne est un long récit où Pilou part à l'aventure et **écrit au joueur**. Il raconte à la
première personne (« je »), s'adresse au joueur (« tu ») et lui demande conseil. Le joueur choisit ;
Pilou agit, et cela prend du **vrai temps** : il marche dix minutes, traverse pendant deux heures, dort
une nuit. Pendant ce temps, plus de nouvelles. Puis il revient, et il faut choisir encore.

Ce document est le contrat commun : auteurs des histoires, moteur (PC et Android), interfaces.

## Les règles du jeu (décidées avec Antoine)

- **Un ton par campagne** : une drôle, une à suspense, une émouvante… Chaque campagne a sa voix.
- **Rythme mixte** : la plupart des attentes durent 5 à 30 min ; quelques grandes traversées durent 1 à
  3 h (ou une nuit). Une campagne se joue sur une à deux semaines, à raison de quelques choix par jour.
- **Check-points** : on peut poser le téléphone ou fermer le PC à tout moment, rien ne se perd. Une
  attente continue de s'écouler appareil éteint. Un check-point au moins par chapitre.
- **Échec** : un mauvais choix ou une épreuve ratée peut faire échouer. Pilou rentre cabossé, se repose,
  et repart **du dernier check-point**. Ce qui était acquis avant reste acquis. Certaines mauvaises
  fins existent en bout d'histoire.
- **Pilou reste à l'écran, occupé** : pendant une attente il ne disparaît pas ; il est en tenue de
  voyage et marche sur place (ou rame, grimpe, dort). Sa bulle dit où il en est et quand il revient.
- **Une seule campagne en cours** à la fois. On peut l'abandonner (elle reprendra du dernier check-point).
- **Mascotte passive** : jamais plus d'un ou deux gestes pour répondre. Le retour de Pilou est annoncé
  une fois (bulle sur PC, notification sur téléphone), sans relance insistante.
- **Contenu original** : aucun personnage, lieu, nom ou intrigue repris d'une œuvre existante. Tout
  public. Jamais d'opposition rouge / vert dans ce qui s'affiche ; chaque état a aussi un signe de forme.

## Ce qui rend une campagne prenante (consignes d'écriture)

- **Suspense** : chaque attente longue se termine sur une question ouverte (« j'entends quelque chose
  derrière la porte. J'y vais. »). Le joueur doit avoir envie de savoir.
- **Émotion** : des personnages qui reviennent, des promesses tenues ou trahies, des choix qui coûtent.
  Un choix du chapitre 2 doit pouvoir changer une scène du chapitre 7 (drapeaux).
- **Vraies branches** : au moins deux routes principales distinctes par campagne, 4 à 6 fins (bonne,
  douce-amère, mauvaise, secrète…). Pas de faux choix à répétition : au moins un choix sur trois a une
  conséquence visible.
- **Temps long** : la durée d'une attente doit se justifier dans le récit (la marée, la nuit, la
  montée). Les plus longues tombent en fin de chapitre.
- **Récompenses** : une petite à chaque fin de chapitre, une grande à la fin, des « souvenirs » à
  collectionner selon les fins.
- **Voix** : phrases courtes, lisibles sur téléphone. 30 à 110 mots par message. Pilou est curieux,
  tendre, un peu trouillard, souvent drôle malgré lui. Français, tutoiement.
- **Taille visée** : 8 à 12 chapitres, 120 à 200 nœuds, 12 000 à 20 000 mots ; sur un parcours, 30 à 45
  choix et 14 à 22 attentes (dont 3 à 5 longues).

## Format des fichiers

Une campagne = un dossier `assets/campagnes/<id>/`, en JSON UTF-8 :

- `campagne.json` : la fiche ;
- `chapitre-01.json`, `chapitre-02.json`… : les nœuds, un fichier par chapitre.

Dans les textes : guillemets français « » et apostrophe typographique ou droite ; pas de guillemet
droit `"` dans la prose. Les identifiants sont en minuscules ASCII avec tirets (`porte-du-phare`), et
uniques dans toute la campagne.

### `campagne.json`

```json
{
  "v": 1,
  "id": "phare-eteint",
  "titre": "Le phare éteint",
  "ton": "mystere",
  "accroche": "Le phare de la côte s'est éteint il y a trois nuits. Pilou veut savoir pourquoi.",
  "niveau": 5,
  "duree": "≈ 10 jours",
  "depart": "ch1-lettre",
  "chapitres": [
    { "id": "ch1", "titre": "Une lettre sans timbre", "fichier": "chapitre-01.json" }
  ],
  "variables": { "courage": 0, "confiance": 0 },
  "objets": [ { "id": "lanterne", "nom": "Lanterne" } ],
  "souvenirs": [ { "id": "phare-rallume", "nom": "La lumière revenue", "texte": "Tu as rallumé le phare." } ],
  "decors": [ { "id": "jetee-brouillard", "nom": "La jetée", "description": "une jetée de bois dans le brouillard, lanterne éteinte, mer d'encre" } ]
}
```

`ton` : `humour`, `mystere`, `emotion` ou `epique`. `niveau` : niveau de Pilou requis pour commencer.
`decors` (facultatif) : les décors illustrés de la campagne, 6 à 14 ; la `description` sert à l'illustrateur.

### Fichier de chapitre

```json
{ "chapitre": "ch1", "noeuds": { "ch1-lettre": { "type": "recit", "texte": ["…"], "suite": "ch1-depart" } } }
```

Champs communs à tous les nœuds :

| Champ | Rôle |
|---|---|
| `type` | `recit`, `choix`, `attente`, `epreuve`, `hasard`, `echec`, `fin` |
| `texte` | liste de paragraphes (messages de Pilou), affichés l'un après l'autre |
| `checkpoint` | `true` : état sauvegardé ici ; un échec y ramène |
| `effets` | liste d'effets appliqués à l'entrée dans le nœud |
| `recompense` | `{ "po": 20, "xp": 10 }`, créditée une seule fois (fin de chapitre) |
| `lieu` | court libellé affiché en tête (« La jetée », « Sous le phare »), gardé tant qu'un nœud n'en donne pas un autre |
| `humeur` | facultatif : l'expression de Pilou pendant ce message, parmi `joie`, `peur`, `triste`, `surpris`, `determine`, `fatigue`, `tendre`, `colere`, `malice`, `neutre` (défaut : `neutre`) |
| `decor` | facultatif : identifiant d'un décor déclaré dans `decors` ; hérité du nœud précédent tant qu'il n'est pas redéfini |

`humeur` et `decor` servent aux interfaces (animer Pilou, illustrer la scène) ; un moteur ancien les ignore.

Les sept types :

- **`recit`** : du texte, puis `suite` (id du nœud suivant).
- **`choix`** : `options`, 2 à 4 entrées `{ "id", "libelle", "vers", "si"?, "effets"? }`. Une option dont
  la condition `si` est fausse n'est pas proposée. Il doit toujours rester au moins une option sans condition.
- **`attente`** : du vrai temps. `duree_min` (minutes, 1 à 600), `duree_max` facultatif (tirage
  reproductible entre les deux), `pendant` (ligne d'état : « Pilou longe la falaise »), `tenue`
  (`marche`, `course`, `bateau`, `grimpe`, `nage`, `nuit`, `cache`, `attend`), `suite`. Le `texte` est ce
  que Pilou dit **avant** de partir. Pas de nouvelles pendant l'attente.
- **`epreuve`** : un mini-jeu. `jeu` (`reflexe`, `memoire`, `rythme`, `visee`, `des`), `difficulte` 1 à 3,
  `bonus` facultatif (nom d'une variable qui aide), `reussite` et `echec` (ids). `des` est un tirage
  sans geste ; tout appareil qui ne sait pas jouer un jeu le remplace par `des`.
- **`hasard`** : `issues`, liste de `{ "poids", "vers", "si"? }`. Tirage reproductible.
- **`echec`** : Pilou échoue. `repos_min` (minutes de repos, 10 à 180), puis retour au dernier check-point.
- **`fin`** : `issue` (`bonne`, `douce-amere`, `mauvaise`, `secrete`), `titre`, `recompenses`
  (`{ "po", "xp", "souvenir"?, "titre"?, "objet"? }`).

Effets : `{ "var": "courage", "plus": 1 }` (négatif permis), `{ "objet": "lanterne", "donne": true }`
(ou `false` pour le perdre), `{ "drapeau": "a-menti" }`, `{ "drapeau": "a-menti", "ote": true }`.

Conditions (`si`) : `{ "var": "courage", "min": 2 }`, `{ "var": "courage", "max": 1 }`,
`{ "objet": "lanterne" }`, `{ "drapeau": "a-menti" }`, `{ "non": { … } }`, `{ "tous": [ … ] }`,
`{ "un": [ … ] }`.

### Ce que le validateur exige

- tous les `vers`, `suite`, `reussite`, `echec`, `depart` pointent sur un nœud existant ;
- tout nœud est atteignable depuis `depart` ; aucune boucle sans attente ni choix ;
- depuis tout nœud, une `fin` est atteignable ; au moins une fin `bonne` ;
- un `checkpoint` au début de chaque chapitre ; aucun nœud `echec` atteignable avant le premier check-point ;
- tout `choix` a au moins une option sans condition ; variables, objets, drapeaux et souvenirs utilisés
  sont déclarés (les drapeaux se déclarent par leur premier usage en effet) ;
- toute `humeur` est l'une des dix valeurs ; tout `decor` utilisé est déclaré dans `decors` ;
- durées et longueurs dans les bornes ; récompenses plafonnées (voir plus bas) ;
- statistiques rendues : nœuds, mots, choix et attentes par parcours (min, médiane, max), temps réel
  total par parcours, nombre de fins atteignables.

Le validateur est `outils/campagnes/valider.py` (Python 3, sans dépendance) ; la CI le lance sur toutes
les campagnes de `assets/campagnes/` :

```
python3 outils/campagnes/valider.py                      # toutes les campagnes
python3 outils/campagnes/valider.py assets/campagnes/x   # une seule
```

Chaque message dit le fichier, le nœud et la raison. Une **erreur** fait échouer (code de sortie 1) ; un
**avertissement** ne bloque pas ; une **note** situe la campagne par rapport à la taille visée.

### Précisions du format (ce que le moteur et le validateur appliquent)

Le moteur a demandé de trancher quelques points que le format laissait ouverts. Ils font partie du contrat :

- **Fichiers** : UTF-8 sans BOM ; jamais deux fois la même clé dans un objet JSON ; `id` de la fiche = nom
  du dossier ; `chapitre` du fichier = `id` du chapitre ; un fichier `.json` absent de `chapitres` n'est pas lu.
- **Identifiants** : minuscules ASCII, chiffres, tirets (`^[a-z0-9]+(-[a-z0-9]+)*$`), pour la campagne, les
  chapitres, les nœuds, les options, les variables, les objets, les drapeaux, les souvenirs et les décors.
  Les nœuds sont uniques dans toute la campagne ; les options, dans leur `choix`. Deux identifiants d'une même
  famille ne doivent pas avoir le même **code court** (4 caractères tirés de l'identifiant, utilisés dans les
  messages entre appareils) : c'est très rare, et le validateur dit lequel renommer.
- **Textes** : `texte` est obligatoire pour `recit`, `choix`, `attente`, `echec`, `fin` ; facultatif pour
  `epreuve` et `hasard`. Un message de plus de 110 mots est un avertissement, de plus de 160 une erreur ;
  avertissement aussi si plus d'un tiers des messages font moins de 30 mots. Libellé d'option : 60 caractères
  au plus (avertissement) ; `pendant` : 60 ; `lieu` : 40.
- **Récits** : ils s'enchaînent sans geste. Après un `choix`, Pilou dit tout ce qu'il a à dire (récits, puis
  le `texte` de l'attente) et part : l'attente commence à l'heure du choix.
- **Deux attentes de suite** (ou une attente juste après un repos) : Pilou ne repart jamais sans un geste. Au
  retour, il dit le `texte` de la nouvelle attente et le joueur répond « vas-y » (une décision « continuer ») ;
  l'attente commence alors. Écrire le `texte` d'une attente comme ce que Pilou dit avant de partir.
- **`attente`** : `pendant` et `tenue` sont obligatoires ; `duree_max`, s'il est là, va de `duree_min` à 600.
- **`epreuve`** : `difficulte` obligatoire. Aux dés (jeu `des`, jeu inconnu, ou appareil qui ne sait pas jouer
  le jeu), la chance de réussir est de 70 %, 55 % ou 40 % selon la difficulté, plus 5 points par point de la
  variable `bonus` (bornée entre 10 % et 95 %). Un jeu inconnu est un avertissement.
- **`hasard`** : `poids` entier ≥ 1. Si aucune issue n'a sa condition vraie, le moteur tire parmi toutes
  (avertissement si toutes les issues ont une condition).
- **Conditions** : `{ "var": …, "min": 2, "max": 5 }` peut porter les deux bornes ; un drapeau testé doit
  être posé par au moins un effet quelque part.
- **Check-point** : l'état est gardé **avant** les effets du nœud. Après un échec et son repos, Pilou y
  rentre de nouveau : son texte est redit, ses effets rejoués une fois. Variables, objets, drapeaux et décor
  reviennent à ce qu'ils étaient ; les récompenses déjà touchées restent, et ne se touchent pas deux fois.
  Tout nœud par lequel on entre dans un chapitre (depuis un autre chapitre, ou le départ) est un check-point.
- **Échec en boucle** : erreur si un `echec` est atteignable depuis un check-point sans `choix`, `attente`
  ni mini-jeu entre les deux (récits, hasards, épreuves aux dés seulement) : après chaque repos, Pilou y
  retomberait tout seul.
- **Récompenses** : un nœud ordinaire porte `recompense` (`po`, `xp` seulement) ; une fin porte `recompenses`
  (obligatoire, même à zéro), avec en plus `souvenir` (déclaré), `titre` (le texte du titre, 40 caractères au
  plus) et `objet` (l'identifiant de l'article à porter, à ajouter à la boutique comme article non achetable).
  Un seul titre et un seul objet par campagne (plusieurs fins peuvent donner le même). Une fin a un `titre`
  (son nom) et une `issue`.
- **Rejouer** : ni po ni xp ; les souvenirs manquants se gagnent, ainsi que le titre et l'objet s'ils
  manquaient encore.

## Récompenses (plafonds)

Une campagne entière rapporte au plus **600 po et 300 xp** sur le meilleur parcours (fins de chapitre
comprises), un **titre**, un **objet exclusif** à porter et un **souvenir** par fin. Un chapitre : au
plus 40 po et 20 xp. Rejouer une campagne finie ne redonne ni po ni xp : seulement les souvenirs manquants.

## État, sauvegarde et synchronisation

L'état d'une partie se déduit entièrement d'un **journal** : la liste ordonnée des décisions prises
(option choisie, résultat d'épreuve, horodatage de chaque entrée dans un nœud d'attente). Rejouer le
journal sur le fichier de la campagne redonne exactement le même état sur le PC et sur le téléphone :
variables, objets, drapeaux, nœud courant, fin de l'attente en cours, dernier check-point.

- N'importe quel appareil du groupe peut ajouter la décision suivante. Si deux appareils décident pour
  la même étape, la plus ancienne gagne (égalité : plus petit identifiant d'appareil).
- Les tirages (`hasard`, `duree_max`, `des`) dépendent d'une graine fixée au début de la partie.
- Le journal voyage par les canaux existants (téléphone ↔ PC, PC ↔ PC), en restant petit : il part du
  dernier check-point, précédé d'un résumé de l'état à ce check-point.
- Les récompenses sont créditées une seule fois, par nœud, quel que soit l'appareil.
- Le téléphone doit pouvoir avancer **PC éteint** : l'histoire ne dépend pas du PC ; seules les
  récompenses attendent le PC, comme les achats de la boutique.
- Fin d'attente : notification locale sur le téléphone (programmée à l'heure de fin, même hors ligne),
  bulle sur le PC.

## API du moteur

Le moteur est écrit deux fois, à l'identique : `apps/PilouBureau/Campagnes.cs` (PC, sans WPF) et
`android/app/src/main/java/fr/pilou/compagnon/Campagnes.java` (Java pur). Le PC écrit des vecteurs
(`android/app/src/test/resources/campagnes-vecteurs.txt` : parties entières, conflits, journaux en désordre,
fusions, messages) que les tests Java rejouent ligne à ligne. Les noms ci-dessous sont ceux du C# ; en Java,
les mêmes en minuscule (`Campagnes.actualiser`, `etat.phase`…).

### Les campagnes embarquées

- `Campagnes.Disponibles()` : les identifiants (tout dossier de `assets/campagnes/` qui a une fiche : rien
  à déclarer ailleurs). `Campagnes.Charger(id)` : la campagne, ou `null`.
- `Campagne` : `Id`, `Titre`, `Ton`, `Accroche`, `Niveau`, `Duree`, `Chapitres`, `Souvenirs`, `Decors`,
  `Noeuds`.

### L'état courant

Tout part du **carnet** (`Campagnes.Carnet`) : la partie en cours, les parties suspendues, l'historique et
le fil des messages. Sur le PC il vit dans le profil (`Profil.CarnetCampagnes`) ; sur le téléphone dans les
préférences (`CampagnesTel.carnet(contexte)`).

`Campagnes.Actualiser(carnet, Campagnes.Charger, maintenant)` rejoue la partie à l'heure donnée (ms Unix) et
rend l'`Etat`, ou `null` s'il n'y a pas de partie. À appeler à l'ouverture, après chaque décision, et quand
une attente finit.

| `Etat` | Sens |
|---|---|
| `Phase` | `Choix` (des options), `Epreuve` (un mini-jeu), `Depart` (Pilou attend un « vas-y »), `Attente` (parti), `Repos` (après un échec), `Fin`, `Abandon`, `Cassee` (fichier de campagne incohérent) |
| `Options` | phase `Choix` : les options proposées (`Id`, `Libelle`), conditions déjà appliquées |
| `Jeu`, `Difficulte`, `Aide`, `Chance` | phase `Epreuve` : le jeu, sa difficulté 1 à 3, la valeur de la variable bonus, la chance aux dés (%) |
| `Fin` | phases `Attente` et `Repos` : l'heure de retour (ms Unix), pour la bulle et la notification locale ; 0 sinon |
| `Pendant`, `Tenue` | phases `Depart`, `Attente`, `Repos` : la ligne d'état et la tenue de Pilou occupé (`Repos` : « Pilou se repose », `nuit`) |
| `Lieu`, `Decor`, `Humeur` | le lieu et le décor courants (hérités), l'humeur du dernier message |
| `Chapitre`, `ChapitreTitre`, `ChapitreNumero`, `ChapitreTotal`, `Progression` | où l'on en est (progression de 0 à 1) |
| `Issue`, `TitreFin`, `Recompenses` | phase `Fin` : la fin obtenue |
| `Variables`, `Objets`, `Drapeaux` | l'état de l'histoire (pour un écran « sac à dos ») |

Le **fil** (`carnet.Fil`) est la correspondance : les messages de Pilou (`Qui` = `pilou`) et les choix du
joueur (`joueur`), chacun avec son `Texte`, son `Noeud`, son `Lieu`, son `Humeur`, son `Decor` et son heure
`T`. `carnet.NonLus` compte les messages de Pilou pas encore lus, `Campagnes.NonLu(carnet, message)` le dit
pour un message, `Campagnes.MarquerLu(carnet)` marque tout lu. Le fil garde les 150 derniers messages.

`Campagnes.Ligne(etat, heureDeFin)` donne « Pilou longe la falaise · retour vers 15 h 40 ».
`Campagnes.Fins`, `Souvenirs`, `Titres`, `ObjetsGagnes`, `Acquis` lisent l'historique d'une campagne ;
`Campagnes.Finie`, `EnCours`, `Reprenable` disent où en est le carnet.

### Les décisions

Chacune renvoie `null` si c'est fait, sinon une raison courte à montrer telle quelle.

| Fonction | Quand |
|---|---|
| `Demarrer(carnet, campagne, niveau, maintenant, appareil, Charger)` | aucune partie en cours ; reprend au dernier check-point une campagne abandonnée (`neuf: true` : depuis le début) |
| `Choisir(carnet, campagne, maintenant, appareil, idOption)` | phase `Choix` |
| `Continuer(…)` | phase `Depart` : « vas-y » |
| `Epreuve(…, reussie)` | phase `Epreuve` : le résultat du mini-jeu |
| `EpreuveAuDe(…)` | phase `Epreuve` : l'appareil ne sait pas jouer ce jeu, les dés décident |
| `Abandonner(…)` | à tout moment, même pendant une attente |

`appareil` est l'identifiant de l'appareil dans le groupe (PC : `Reglages.Appareil` ; téléphone :
`CampagnesTel.appareil`). Sur le PC, la fenêtre offre `CampagneDemarrer`, `CampagneChoisir`,
`CampagneContinuer`, `CampagneEpreuve`, `CampagneAuDe`, `CampagneAbandonner`, `EtatCampagne` et
`CampagneEnAttente` (`FenetreCampagne.cs`) ; sur le téléphone, `CampagnesTel` offre les mêmes
(`demarrer`, `choisir`, `continuer`, `epreuve`, `auDe`, `abandonner`, `etat`, `lu`, `enAttente`). Ces deux
façades gardent le carnet, publient et refusent une décision quand Pilou est en expédition ou en visite.

Pendant une attente de campagne ou un repos, le PC refuse les départs en expédition et en visite
(« Pilou est en campagne… ») ; pendant une expédition ou une visite, il refuse les décisions de campagne,
sauf l'abandon. `--essai=campagne:<id>` déroule une campagne en accéléré dans la bulle, sans rien écrire.

### Le moteur pur

`Campagnes.Rejouer(campagne, partie, maintenant)` rend l'état d'une `Partie` ; `Campagnes.Decider(campagne,
partie, maintenant, appareil, valeur)` rend la partie avec la décision ajoutée, ou `null` si elle n'est pas
valide (valeur : le rang de l'option, ou `Suite`, `Reussite`, `Rate`, `Abandon`) ; `Campagnes.Compacter`
avance la base. Une `Partie`, c'est une **base** (le résumé de l'état à un check-point : nœud, variables,
objets, drapeaux, décor, heure, tirages déjà faits) et le **journal** des décisions prises depuis. Une
décision : son étape, son heure (à la seconde), son appareil, le nœud où elle est prise, sa valeur.

- Même journal, même état, partout : les tirages (`hasard`, `duree_max`, dés) ne dépendent que de la graine
  de la partie et du nombre de tirages déjà faits.
- Deux décisions pour la même étape : la plus ancienne gagne ; à égalité, le plus petit identifiant
  d'appareil. Une décision prise ailleurs que là où en est l'histoire (autre nœud, option absente) ne compte
  pas. L'ordre d'arrivée et les doublons ne changent rien.
- La base avance au check-point suivant quand la décision qui y mène a plus de dix minutes (le temps qu'un
  autre appareil dise qu'il avait décidé avant). Au-delà de 24 décisions sans check-point, elle avance au
  milieu du chapitre, en gardant le check-point.
- Une attente finit toute seule quand son heure est passée. Si un autre appareil, dont l'horloge avance, a
  déjà décidé la suite, l'état le suit.
- Une seule partie en cours dans le groupe : celle au plus grand numéro (à égalité, la plus ancienne). Une
  partie mise de côté ou abandonnée reste suspendue à son dernier check-point jusqu'à ce qu'on la reprenne.

### Synchronisation

Un **message dédié**, sur un sujet à part du relais (`Campagnes.Sujet(code)`, tiré du code du groupe comme
les autres ; chiffré de la même façon). Les messages existants ne changent pas, et un ancien appareil
n'écoute pas ce sujet. Chaque appareil publie son carnet quand il change (et toutes les 6 h) ; le PC relit le
sujet toutes les 90 s, le téléphone toutes les 5 min et à chaque décision.
`Campagnes.Messages(carnet, appareil, "pc" | "tel")` rend un message (deux ou plus seulement s'il y a
beaucoup de parties suspendues), chacun de 2 750 octets au plus ; `Campagnes.Recevoir(carnet, json,
appareil, Charger, maintenant)` le fusionne : même résultat dans n'importe quel ordre, autant de fois
qu'on veut.

```
{"v":1,"a":"<appareil>","k":"pc"|"tel",
 "q":<partie en cours>, "s":[<parties suspendues>],
 "h":{"<campagne>":[<n° de la dernière partie>,<n° de la dernière partie finie>,{"<fin>":<secondes>},"<nœuds récompensés>"]}}

partie = {"c":"<campagne>","p":<n°>,"d":<départ, s>,"o":"<appareil d'origine>","g":"<graine>",
          "x":<1 rejeu + 2 geste + 4 nœud déjà entré + 8 abandonnée>,
          "e":<étape>,"r":<rang>,"i":<messages déjà émis>,"n":<tirages faits>,"t":<heure de la base, s>,
          "ici":["<nœud>",{"<variable>":<valeur>},"<objets>","<drapeaux>","<décor>","<nœud du lieu>"],
          "cp":[…le dernier check-point, s'il n'est pas « ici »…],
          "l":["<appareil>",…],"j":[[<étape>,<secondes depuis la base>,<rang de l'appareil>,"<nœud>",<valeur>],…]}
```

Nœuds, variables, objets, drapeaux et décors y sont des **codes courts** de 4 caractères
(`Campagnes.Code(id)`), mis bout à bout quand il y en a plusieurs. Mesuré (test
`Messages_sous_la_limite_pour_une_campagne_de_200_noeuds`) sur une campagne de 258 nœuds jouée jusqu'au
bout, 371 décisions, avec deux autres campagnes finies (six fins chacune) et deux suspendues : 1 854 octets
de JSON au plus, soit 2 512 chiffrés pour une limite de 3 800 ; le prologue au départ : 192 octets, 296
chiffrés. Pour comparaison, le message de groupe d'un profil garni fait déjà 3 404 octets chiffrés et celui
du téléphone est allégé pour tenir en 3 792 : d'où le message à part.

**Récompenses.** L'historique (`h`) dit quels nœuds ont été récompensés ; chaque PC verse ceux qu'il n'a pas
encore versés (`Campagnes.Crediter`), dans deux compteurs à part que tous les PC du groupe tiennent à
l'identique et qui se comptent **au maximum, jamais en somme** : les po dans `Bourse.PoCampagnes`, l'xp dans
`Profil.XpTelephone` (le compteur des gains du téléphone, déjà partagé). Le téléphone ne verse rien : il
montre ce qui attend un PC (`Campagnes.EnAttente`), comme pour les achats. L'objet d'une fin rejoint
l'inventaire quand la boutique connaît son identifiant ; souvenirs et titres se lisent dans l'historique.

## Les campagnes

| Id | Titre | Ton | Niveau |
|---|---|---|---|
| `prologue` | La colline d'en face | humour | 1 |
