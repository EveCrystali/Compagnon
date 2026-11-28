# Pilotage

Plusieurs sessions Claude travaillent en même temps sur le dépôt. **Une seule les dirige : la session pilote.**
Ce fichier dit qui décide quoi, comment on se répartit le travail et où en est chaque chantier.
Toute session le lit avant de commencer, juste après `CLAUDE.md`.

**Git sur ce dépôt (Antoine, 28 novembre 2026)** : commit, push, PR et fusion à CI verte se font automatiquement, sans
demander. Cette règle l'emporte sur toute consigne globale « demander avant de pousser ».

## Qui fait quoi

| Rôle | Fait | Ne fait pas |
|---|---|---|
| **Antoine** | Tranche le produit (tout ce qui va dans `DECISIONS.md`), teste sur ses vrais appareils, peut tout réorienter. | — |
| **Session pilote** (ouverte le 27 novembre 2026, titre « Pilote Compagnon ») | Tient le cap, fixe les priorités, découpe le travail en chantiers, lance les sessions avec un brief, arbitre entre chantiers, relit les comptes rendus, tient ce fichier et `ETAT.md`. | Coder un gros chantier elle-même ; trancher à la place d'Antoine une question de produit. |
| **Session de chantier** | Fait un seul chantier, dans son périmètre de fichiers, jusqu'à la PR fusionnée ; rend un compte rendu. | Changer de cap, ouvrir un second sujet, toucher aux fichiers d'un autre chantier, modifier ce fichier. |

Une session ouverte par Antoine sans passer par le pilote est un chantier comme un autre : elle s'inscrit dans le
tableau ci-dessous via son compte rendu, et le pilote l'intègre.

## Le cap (fixé par le pilote, 27 novembre 2026)

**Phase actuelle (Antoine, 27 novembre 2026 au soir) : le meilleur rendu possible, systématiquement.** Le contenu est
là (quatre campagnes, présence, boutique, métiers). On ne rajoute pas de fonctions de jeu : on rend l'existant plus
beau, plus vivant, plus immersif, et on le prouve sur de vrais appareils.

**Finition de la version 1 (Antoine, 28 novembre 2026)** : le projet se peaufine. Un défaut de détail (texte tranché,
chevauchement, pixel inégal, libellé tronqué, chiffre faux dans une doc) est un vrai défaut. Chaque capture se relit
à l'œil avant de dire « fait ». L'état des lieux et l'ordre proposé sont dans [AUDIT-V1.md](AUDIT-V1.md).

**Haute définition (Antoine, 28 novembre 2026)** : le pixel art n'est jamais une baisse de qualité ni de définition
(règle 9 de `CLAUDE.md`). Scènes des campagnes à 480 × 240 unités au minimum. Trois chantiers liés : le moteur du
Théâtre (taille, format compact, charge mesurée), la peinture des 46 décors, les personnages et Pilou à la nouvelle
unité. Le moteur fixe le format ; les deux autres s'y conforment.

**Exigence de rendu** : chaque chantier qui touche à l'image ou au son va au-delà du strict nécessaire. Planche de
contrôle avant / après, relecture à l'œil de chaque image produite, capture sur le vrai PC quand c'est possible,
une seconde passe de finition avant la PR. « Ça marche » ne suffit pas : « c'est beau » est le critère.

**Outils** : pas de logiciel 3D ni d'éditeur graphique. Les sprites restent générés par le code Python de
`outils/sprites/` (texte versionné, rendu identique PC / Android, références partagées). Pillow et numpy sont permis
pour les planches de contrôle et les mesures, jamais dans le rendu livré. Les sons sont synthétisés par un script
maison, comme les sprites.

Chantiers de rendu (ouverts par le pilote le 27 novembre) : police pixel maison, sons 8 bits, vie du personnage
(ombre, ressorts, particules, lumière de l'heure), animations des campagnes.

Priorités de vérification, en parallèle :

1. **Vidéo de promo** : tournage (`outils/tourner-ecran-gauche.ps1`) puis montage (`outils/video/`). Les deux
   chantiers sont ouverts.
2. **Vérification sur vrai Windows** (PC d'Antoine, session locale) : liste de contrôle de `TEST-JEU.md`, fenêtre
   Aventure à 100 / 125 / 150 %, dessin fin, journal. Tout ce que `ETAT.md` classe « jamais vérifié » côté Windows.
3. **Vérification sur vrai téléphone** : avec Antoine, car aucune session ne pilote son téléphone. Relire d'abord à
   l'œil les captures `captures-ui` de la CI (gratuit, possible tout de suite).
4. **Points connus** de `ETAT.md`, un par chantier, du plus visible au moins visible : divergence de campagne entre
   appareils, deux écrans à échelles différentes, poids de l'exe.
5. **Seuils de complicité** : pas avant le 4 décembre 2026 (une semaine d'usage réel), et sur les retours d'Antoine.

Rouvert par Antoine le 28 novembre : les traits de personnalité, la première minute, l'ouverture de campagnes par
un haut fait. Hors cap tant que le pilote ne l'a pas rouvert : les petits jeux de `IDEES.md`, toute nouvelle campagne,
tout nouveau connecteur, tout gain passif sans le joueur. Une session qui pense qu'il faut en sortir le dit dans son compte rendu ; elle ne s'y lance pas.

## Règles d'orchestration

1. **Un chantier = une session = une branche `claude/<sujet>` = une PR.** Pas de PR fourre-tout.
2. **Périmètres disjoints.** Le brief nomme les fichiers du chantier. Deux chantiers ouverts ne touchent pas les mêmes
   fichiers de code. Besoin d'un fichier d'un autre chantier : le signaler au pilote, ne pas l'éditer.
3. **Fichiers partagés** : `CLAUDE.md`, `docs/ETAT.md`, `docs/DECISIONS.md`, `docs/PILOTAGE.md`, le catalogue et
   les fichiers de référence partagés PC / Android.
   - `PILOTAGE.md` : le pilote seul.
   - `CLAUDE.md` et `DECISIONS.md` : pas sans une demande d'Antoine ou du pilote. Changement minimal, une ligne
     plutôt qu'une section.
   - `ETAT.md` : chaque chantier met à jour **seulement les lignes de son sujet** en fin de chantier. Le pilote
     refait la synthèse.
   - En cas de conflit : fusionner `main` dans la branche, garder les deux côtés (règle de `CLAUDE.md`).
4. **Fusion** : dès que la CI est verte (règle d'Antoine). Exception : si deux PR ouvertes touchent le même fichier
   partagé, la plus petite passe d'abord, l'autre fusionne `main` ensuite.
5. **Pas de session sans brief.** Le pilote écrit le brief avec le modèle ci-dessous ; la session de chantier n'a que
   ce brief et le dépôt.
6. **Le compte rendu est un indice, pas un fait.** Le pilote vérifie la PR (diff, CI) avant de marquer un chantier
   « fait » ici.
7. **Modèles** : le pilote (Opus) analyse, décide, rédige. Une recherche large va à l'agent `recherche` ; un plan
   déjà décidé à l'agent `implementeur` ou à une session de chantier.

## Escalade

| Question | Va à |
|---|---|
| Produit, comportement, lore, tout ce qui changerait `DECISIONS.md` | Antoine, par le pilote |
| Deux chantiers qui se marchent dessus, ordre de fusion, périmètre flou | Le pilote |
| Choix technique interne au chantier | La session de chantier, noté dans la PR |
| Action irréversible hors fusion à CI verte (suppression, publication externe) | Antoine |

## Modèle de brief

```
Chantier : <nom court>            Branche : claude/<sujet>
But : <ce qui doit être vrai à la fin, en une ou deux phrases>
Périmètre : <fichiers et dossiers autorisés> — rien d'autre.
Hors périmètre : <ce qu'un autre chantier tient, ce qui est hors cap>
À lire : CLAUDE.md, docs/PILOTAGE.md, <docs du sujet>
Fini quand : <tests, capture, vérif sur le PC…> ; PR fusionnée à CI verte.
Compte rendu : selon le modèle de docs/PILOTAGE.md.
```

## Modèle de compte rendu (fin de chantier)

Trois lignes de résumé, puis :

- **Statut exact** : planifié / en cours / fait / testé / fusionné (avec le numéro de PR).
- **Vérifié** : quels tests, quelles captures, sur quel appareil.
- **Non vérifié** : ce qui n'a tourné ni sur un vrai Windows ni sur un vrai téléphone.
- **Fichiers touchés** hors du périmètre du brief, avec la raison.
- **Décisions** prises dans le chantier, et questions laissées au pilote ou à Antoine.

## Chantiers

Tenu par le pilote. Dernière mise à jour : 28 novembre 2026, après-midi.

**Gel pour la version 1 (Antoine, 28 novembre 2026)** : « termine ce qui était prévu et en cours, puis on stoppe
sur cela comme une v1 ». Aucun nouveau chantier, aucune nouvelle fonction. Seuls passent encore les défauts.

| Chantier | PR | État |
|---|---|---|
| Sons sur téléphone : un geste sonne au volume multimédia même en vibreur ; bouton « Essayer » | #171 | En CI. Défaut vu par Antoine sur son téléphone |
| Pilotage (ce fichier) | `claude/pilotage` | Tenu à jour |

Tout le reste est fusionné. Journée du 28 novembre :
- **Menu et première minute** : « Sept portes » (#97, #98), thème sombre par défaut sur PC (#102), trois bulles de
  bienvenue et mode d'emploi (#100), entrée « Musique » (#118).
- **Une seule écriture** : police pixel (#88, #107, #109), style pixel de l'Aventure (#103, #108), guide de style et
  Android (#110, #111, #154), fenêtres du PC et plancher de lisibilité (#114, #115, #116, #119, #152), habillage
  commun des fenêtres et titres au pixel fin (#135, #150, #159).
- **Vie et personnalité** : 30 saynètes de repos, réactions au monde, Pilou éveillé sans IA (#105, #113) ; vingt
  traits de personnalité (#106) ; campagnes ouvertes par un haut fait, aide du niveau visible (#101).
- **Sons et musiques** : dix sons, « normaux » par défaut (#87, #93) ; 8 boucles et ambiances (#104) ; thème de Pilou
  et second lot (#128).
- **Théâtre des campagnes** : prologue (#95), La Grande Panne (#112), Le phare éteint (#117), Petit Nuage (#120),
  scènes d'évolution et leur choix partagé (#129, #131, #133).
- **Haute définition (règle 9)** : étude (#121, #122), format (#130), moteur 480 × 240 avec le Pilou fin du bureau
  (#146, #149), métamorphose (#151) ; 29 personnages et 32 acteurs (#126, #132, #134, #136, #138, #139, #140) ;
  46 décors puis une passe en profondeur par campagne (#127, #137, #141 à #145, #147, #148, #153, #155 à #158,
  #160, #161, #164 à #170).
- **Sûreté** : un lancement d'essai n'écrit plus dans le vrai profil et n'envoie rien sur le réseau (#162) ; outil de
  planche d'une image par scène (#163).

Leçons de la journée :
- Les captures de contrôle se prennent au format d'un vrai téléphone en portrait (1078 × 2400).
- Quarante dessins en une passe donnent de la largeur, pas de la profondeur : un dessin à la fois, comparé en taille
  réelle au meilleur, cinq faiblesses écrites, trois tours.
- Un réglage coché qui ne produit rien sans explication est un défaut (sons muets en vibreur).
- Tout outil d'essai travaille sur des données jetables : le vérifier dans le code, pas le supposer.

### Clôture de la version 1

Ce qui reste avant de dire « v1 », dans l'ordre :

1. Fusion de #171, puis essai du son par Antoine (trois gestes donnés dans la PR).
2. **Essai sur le vrai téléphone d'Antoine** — rien de ceci n'a tourné sur un appareil réel : lecture d'une scène en
   haute définition (Pilou entre, parle, toucher la grenouille de la mare) ; les quatre campagnes sans rien de coupé ;
   une scène d'évolution et sa métamorphose ; le choix d'évolution qui passe d'un appareil à l'autre ; le Carnet
   « Ses évolutions » ; dix minutes de lecture (fluidité, chauffe, batterie, réglage ✧) ; plusieurs lieux à la suite
   sans plantage ; la grande police du système.
3. **Essai sur le PC à 125 % et 150 %**, deux écrans ; l'annonce d'une évolution par la bulle.
4. Écoute des 22 musiques et motifs (`py outils/sons/sons.py`, puis `outils/sons/ecoute/ecoute.html`).
5. Synthèse de `ETAT.md` par le pilote.
6. Tournage et montage de la vidéo de promo sur le PC (l'ancienne montre un Pilou qui n'existe plus).

### Questions ouvertes pour Antoine

- La clôture inclut-elle les points 2 à 6, ou seulement la fin des chantiers ?
- Public de la v1 : toi et tes amis, ou diffusion publique (signature, page de présentation, anglais) ?
- Menu : « Caresser » est sorti du menu (c'est le clic gauche). D'accord ?
- Le profil réel a probablement été réécrit par des essais le 28 novembre avant #162 (expérience peut-être créditée
  deux fois, de quelques points) : veux-tu qu'on le vérifie ?

### Après la version 1

Voir `IDEES.md`. Reportés par le gel : campagnes liées et deuxième personnage ; rares questions de Pilou ; liens
entre les campagnes et le Pilou du bureau, chorégraphies des choix ; parallaxe des décors ; rafales en fuite ;
navigation du menu au clavier ; signature et diffusion publique ; petits jeux.
