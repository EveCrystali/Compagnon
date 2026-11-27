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
  "souvenirs": [ { "id": "phare-rallume", "nom": "La lumière revenue", "texte": "Tu as rallumé le phare." } ]
}
```

`ton` : `humour`, `mystere`, `emotion` ou `epique`. `niveau` : niveau de Pilou requis pour commencer.

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
| `lieu` | court libellé affiché en tête (« La jetée », « Sous le phare ») |

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
- durées et longueurs dans les bornes ; récompenses plafonnées (voir plus bas) ;
- statistiques rendues : nœuds, mots, choix et attentes par parcours (min, médiane, max), temps réel
  total par parcours, nombre de fins atteignables.

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

## Les campagnes

| Id | Titre | Ton | Niveau |
|---|---|---|---|
| *(à venir)* | | | |
