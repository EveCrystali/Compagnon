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

Tenu par le pilote. Dernière mise à jour : 28 novembre 2026, matin.

| Chantier | Branche / PR | Périmètre | État |
|---|---|---|---|
| Style pixel de l'Aventure (bulles de récit, choix, bandeau, puce de lieu), puis théâtre de « La Grande Panne » | `claude/aventure-style-pixel`, puis `claude/theatre-grande-panne` | lecture de l'Aventure PC et Android (`Lecture.java`, `PageAventure.java`, `FenetreAventure.cs`, `Theatre*`), `assets/scenes/` | En cours (prioritaire : vu par Antoine sur son téléphone) |
| Guide de style et écrans Android hors Aventure | `claude/guide-style` | `docs/STYLE.md`, icônes pixel, en-tête, barre du bas, Accueil, Jouer, Boutique, Collection (Android) | En cours |
| Menu : finition, puis première minute et mode d'emploi | `claude/menu-finition` (#98), puis `claude/premiere-minute` | `MenuPortes.cs`, `MenuRetro.*`, bienvenue de `FenetrePilou.cs`, `docs/MODE-EMPLOI.md`, premier lancement Android | En cours |
| Saynètes de repos et réactions au monde | `claude/saynetes-repos` | `RenduPilou.*`, gestes de `FenetrePilou.cs`, `animations.py`, `Animations.java`, `PilouVue.java` | En cours |
| Musiques et ambiances synthétisées | `claude/musiques` | `outils/sons/`, `assets/sons.txt`, `Sons.cs`, `Sons.java` | En cours |
| Traits de personnalité | `claude/traits` | nouveaux `Traits.cs` / `Traits.java` et leur référence, « Pilou et moi » (`FenetrePresence.cs`), `assets/presence/` | En cours |
| Progression : campagnes ouvertes par un haut fait, avantage du niveau visible en expédition | `claude/progression-campagnes` | `Campagnes.cs` et son pendant Android, `valider.py`, `CAMPAGNES.md`, affichage du départ d'expédition | En cours |
| Pilotage (ce fichier) | `claude/pilotage` | `docs/PILOTAGE.md`, `CLAUDE.md` | En cours |

Fusionnés :
- 27 novembre : tournage de la promo (#80), montage de la promo (#78), boutons du journal et taille « Petit » (#79),
  pilotage (#81).
- 28 novembre, nuit : divergence de campagne détectée même en retard (#82) ; relecture de 110 captures Android et
  portrait qui ne cache plus « ⋯ » (#83) ; audit du menu et menu retenu par Antoine, « Sept portes » + « En ce moment »
  (#84, #85) ; liste de contrôle Windows, quatre défauts corrigés (#86) ; dix sons 8 bits (#87) ; police pixel
  maison de la bulle (#88) ; vie du personnage, ressorts, ombre, poussière, lumière de l'heure (#90) ; gains qui ne
  passent plus sur la bulle (#91).
- 28 novembre, matin : sons « normaux » par défaut (#93) ; théâtre des campagnes, prologue mis en scène, une seule
  unité de pixel sur téléphone, bandeau au-dessus de la scène (#95) ; audit large avant la v1 (#96) ; menu « Sept portes » (#97).

Leçon : la relecture des captures Robolectric (#83) n'a pas vu le décor trop agrandi qu'Antoine a vu sur son
téléphone. Les captures de contrôle doivent être prises au format d'un vrai téléphone en portrait (1080 × 2400,
densité 2,75), pas seulement au format par défaut.

### Questions ouvertes pour Antoine

- Reste de [AUDIT-V1.md](AUDIT-V1.md) : Pilou peut-il poser de rares questions à deux réponses ? Public de la v1
  (toi et tes amis, ou diffusion publique) ?
- Menu : « Caresser » est sorti du menu (c'est le clic gauche). D'accord ?
- Windows à 125 / 150 %, épreuves au clavier et à la souris, extensions d'éditeur : à vérifier à la main (#86).

### File d'attente (lancés par le pilote, dans cet ordre)

1. **Fenêtres PC hors Aventure et menu** (boutique, soins, réglages, journal) au guide de style, après `docs/STYLE.md`.
2. **Tournage et montage réels de la promo** sur le PC, une fois le rendu de la nuit fusionné.
