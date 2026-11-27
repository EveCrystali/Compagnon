# Pilotage

Plusieurs sessions Claude travaillent en même temps sur le dépôt. **Une seule les dirige : la session pilote.**
Ce fichier dit qui décide quoi, comment on se répartit le travail et où en est chaque chantier.
Toute session le lit avant de commencer, juste après `CLAUDE.md`.

## Qui fait quoi

| Rôle | Fait | Ne fait pas |
|---|---|---|
| **Antoine** | Tranche le produit (tout ce qui va dans `DECISIONS.md`), teste sur ses vrais appareils, peut tout réorienter. | — |
| **Session pilote** (ouverte le 27 novembre 2026, titre « Pilote ») | Tient le cap, fixe les priorités, découpe le travail en chantiers, lance les sessions avec un brief, arbitre entre chantiers, relit les comptes rendus, tient ce fichier et `ETAT.md`. | Coder un gros chantier elle-même ; trancher à la place d'Antoine une question de produit. |
| **Session de chantier** | Fait un seul chantier, dans son périmètre de fichiers, jusqu'à la PR fusionnée ; rend un compte rendu. | Changer de cap, ouvrir un second sujet, toucher aux fichiers d'un autre chantier, modifier ce fichier. |

Une session ouverte par Antoine sans passer par le pilote est un chantier comme un autre : elle s'inscrit dans le
tableau ci-dessous via son compte rendu, et le pilote l'intègre.

## Le cap (fixé par le pilote, 27 novembre 2026)

**Phase actuelle : finir et prouver, pas ajouter.** Le contenu est là (quatre campagnes, présence, boutique, métiers).
Ce qui manque, c'est la preuve sur de vrais appareils et la vidéo qui montre le tout.

Priorités, dans l'ordre :

1. **Vidéo de promo** : tournage (`outils/tourner-ecran-gauche.ps1`) puis montage (`outils/video/`). Les deux
   chantiers sont ouverts.
2. **Vérification sur vrai Windows** (PC d'Antoine, session locale) : liste de contrôle de `TEST-JEU.md`, fenêtre
   Aventure à 100 / 125 / 150 %, dessin fin, journal. Tout ce que `ETAT.md` classe « jamais vérifié » côté Windows.
3. **Vérification sur vrai téléphone** : avec Antoine, car aucune session ne pilote son téléphone. Relire d'abord à
   l'œil les captures `captures-ui` de la CI (gratuit, possible tout de suite).
4. **Points connus** de `ETAT.md`, un par chantier, du plus visible au moins visible : divergence de campagne entre
   appareils, deux écrans à échelles différentes, poids de l'exe.
5. **Seuils de complicité** : pas avant le 4 décembre 2026 (une semaine d'usage réel), et sur les retours d'Antoine.

Hors cap tant que le pilote ne l'a pas rouvert : toute idée de `IDEES.md`, toute nouvelle campagne, tout nouveau
connecteur. Une session qui pense qu'il faut en sortir le dit dans son compte rendu ; elle ne s'y lance pas.

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

Tenu par le pilote. Dernière mise à jour : 27 novembre 2026, 23 h.

| Chantier | Branche / PR | Périmètre | État |
|---|---|---|---|
| Animations des campagnes en pixel art | `claude/campaign-animations-pixel-art-66992c` | à préciser par son compte rendu ; présumé `assets/`, `outils/sprites/` | En cours, rien de modifié ni commité à 23 h |
| Relecture des captures Android | `claude/relecture-captures` | lecture seule ; correction Android seulement pour un défaut évident, hors moteur des campagnes | Lancé par le pilote |
| Liste de contrôle Windows (`TEST-JEU.md`) | `claude/controle-windows` | `apps/PilouBureau/` hors moteur des campagnes, `docs/TEST-JEU.md` | Lancé par le pilote |
| Divergence de campagne entre appareils | `claude/divergence-campagne` | moteur des campagnes PC et Android, vecteurs partagés, leurs tests | Lancé par le pilote |
| Pilotage (ce fichier) | `claude/pilotage`, PR #81 | `docs/PILOTAGE.md`, `CLAUDE.md` | PR ouverte |

Fusionnés le 27 novembre : tournage de la promo (#80), montage de la promo (#78), boutons du journal et taille
« Petit » (#79).

### File d'attente

Vide. Prochain candidat : tournage et montage réels de la promo sur le PC d'Antoine (priorité 1), une fois la liste
de contrôle Windows passée, pour filmer une version vérifiée.
