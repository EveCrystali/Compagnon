# compagnon

Pilou, une petite goutte d'encre bleue à antenne, se promène par-dessus la fenêtre de Claude
(Pilou de bureau, ci-dessous) ou, à la demande, dans un widget de l'app (`/compagnon`), et réagit à ce qui se passe dans
la session. Le même compagnon suit toutes les sessions : nom, XP, énergie et souvenirs sont gardés
dans le magasin du mod.

Installation : `/plugin install compagnon --marketplace EveCrystali/Compagnon`, ou l'installateur
du [README](../../README.md) (mod, overlay et Codex d'un coup).

| Ce qui se passe | Ce qu'il fait | Signe de forme |
|---|---|---|
| rien | respire, cligne, regarde ailleurs, petit saut | yeux `● ●`, étincelle `✦` |
| Claude travaille | se concentre | yeux `◉ ◉`, étincelle qui tourne |
| commande de plus de 6 s | patiente | yeux `• •`, points `···` |
| outil en erreur | grimace et tremble | yeux `> <`, `✕` |
| commit ou tests réussis | saute de joie | yeux `^ ^`, étincelles |
| fin de tour | soulagé | yeux `◠ ◠`, bouffée `°` |
| 20 min sans message | s'endort (clic pour le réveiller) | yeux `─ ─`, `z Z` |
| quota ≥ 85 % | s'inquiète, vire à l'orange | yeux `○ ○`, `!` |
| clic | ronronne | `ω`, cœurs `♥` |

- `/compagnon` ouvre ou ferme le widget (fermé par défaut, rien au-dessus de la saisie) ; `/compagnon nom <x>` le renomme.
- Clic droit dans l'app : « Cacher » / « Montrer », « Renommer ».
- Palette bleu / orange (deutéranopie) ; chaque état a un signe de forme en plus de la couleur.
- Aucun toast, rien d'écrit dans la conversation, rien transmis à Claude.

## Pilou de bureau (overlay)

`apps/PilouBureau` : petite appli WPF transparente, **toujours au premier plan**. Pilou marche sur
le bas de l'écran (zone de travail, au-dessus de la barre des tâches) et porte une **bulle
permanente** : une ligne par session Claude ouverte.

| Signe | Statut |
|---|---|
| ❗ (orange) | attend ton autorisation |
| ? (orange) | te pose une question (AskUserQuestion, plan) |
| ◐ (bleu, tourne) | réfléchit · durée du tour, ou outil en cours · sa durée |
| ✓ | fini · il y a N min (visible 2 h) |
| ■ | interrompu |
| ✕ (orange) | erreur |

Une session qui vient de finir fait saluer Pilou (« vient de finir » en bleu pendant 1 min) ; une
session qui se met à attendre le fait sursauter et la bordure de la bulle clignote en orange.

**Options** : clic droit sur Pilou, sept portes rangées par intention (gardées dans
`~/.claude/compagnon/reglages.json`) ; le détail est dans le [mode d'emploi](../../docs/MODE-EMPLOI.md). Pour la
bulle : détaillée, compacte (urgences + résumé « ◐ 2 en cours · ✓ 3 finies », détail au survol) ou seulement quand
Claude attend (*Il se montre ▸ Bulle*) ; thème sombre par défaut, ou clair, ou comme Windows (*Réglages ▸ Thème de la bulle*, qui vaut aussi pour le menu).
Clic sur la bulle : met Claude au premier plan et range la bulle (« lu ») ; clic sur Pilou : caresse et « lu ». La bulle revient au prochain changement ; le survol remontre tout.

**Activités** (`Activites.cs`, `Sondes.cs`, `Metiers.cs`, règles `activites.json`) : toutes les 2 s,
Pilou lit la fenêtre au premier plan (programme, titre, chemin), l'état plein écran de Windows
(`SHQueryUserNotificationState`), les sessions audio (Core Audio : qui joue du son, et à quel niveau),
la caméra et le micro (registre `CapabilityAccessManager`), la charge du processeur et l'heure.
- Activité reconnue et stable 20 s → tenue (`Pose.Tenue`) : `code`, `tableur`, `jeu-mmo`, `jeu`,
  `musique`, `video`, `lecture`, `dessin`, `visio`, `nuit`, `mail`, `texte`, `diaporama`. Réactions
  (`Pose.Reaction`) : il danse sur la musique, transpire quand le processeur est à fond pendant le code,
  a sommeil la nuit ; une phrase à l'arrivée dans une activité (au plus toutes les 30 min).
- Discrétion : caché en plein écran, en présentation (même si une IA attend) et en visio ; réglable.
- Métiers (10, paliers 1 / 5 / 15 / 40 / 100 / 250 h, ou 6 / 30 / 90 / 240 / 600 / 1 500 h pour le travail) et
  22 succès, XP à la clé ; compteurs dans `profil-<PC>.json`, cumulés dans le groupe d'appareils et envoyés au
  téléphone (`metiers`, `succes`). Voir *Progrès ▸ Métiers* et *Progrès ▸ Succès*.
- Les titres de fenêtres ne sont ni écrits ni envoyés. Interrupteur général et une case par activité.

**Jeux et vie** :
- tu ne touches plus à rien depuis 3 min : il saute s'accrocher au curseur par l'antenne et gigote ; 10 min : il s'endort (premier geste = réveil, « bien dormi ! ») ;
- Claude t'attend et tu ne bouges plus depuis 45 s : il se colle à l'écran et toque (« TOC ») ;
- souris secouée près de lui : tête qui tourne (yeux en spirale, étoiles) ; souris posée sur lui : il ronronne ;
- ennui : il joue au ballon ; phrases du jour (bonjour, bon appétit, il se fait tard, bon week-end) ;
- **petites activités** (toutes les 14 à 28 min environ si tu es là, ou *Jouer ▸ Petit jeu au hasard*) : étoile filante à attraper (+10 xp), 3 bulles à éclater (+5 chacune, +5 de bonus), « tape m'en cinq » (+10) ; chaque gain s'affiche en « +N xp » ;
- **pêche** (dès le niveau 2 : *Jouer ▸ Pêcher*, ou parmi les petites activités, ou seul quand tu t'éloignes) : Pilou lance sa ligne au bord d'une petite eau ; après 3 à 15 s le bouchon plonge, éclabousse et un « ! » apparaît. Clic sur le bouchon dans la seconde : prise assurée. Trop tôt : le poisson file. Personne : Pilou ferre seul, une fois sur trois environ, jamais mieux que « rare ». 23 prises (poissons, crabes, botte, bouteille à message, coffret englouti, perle de lune…) en cinq raretés, chacune avec son signe et son cadre : `·` commun sans cadre, `◇` peu commun (coins), `◆` rare (trait bleu), `✦` épique (double, orange), `★` légendaire (argent et orange). Première prise d'une espèce : XP doublée. **Carnet de pêche** dans *Jouer* (« ??? » pour ce qui reste à trouver) ;
- **cuisine** (dès le niveau 4 : *Jouer ▸ Cuisiner*, ou seul) : avec les prises comestibles en réserve, marmite sur le feu, flammes et vapeur, puis un plat au-dessus de sa tête. 30 recettes du livre débloquées par niveau (Pilou tente d'abord celles jamais faites) et des plats inventés (préparation × ingrédient × touche : « Velouté d'anguille d'encre au clair de lune ») ; chaque plat nouveau rapporte un bonus. Un clic sur la marmite : il remue et rien ne brûle ; sinon, rarement, fumée noire. **Livre de recettes** dans *Jouer* ;
- **niveaux** (jusqu'à 50) : l'XP (jeux, pêche, cuisine, tours finis, commits, tests, caresses) fait monter de niveau, avec fête. Le niveau **ouvre l'accès** (jeux, rangées de la boutique, stades d'évolution) et rapporte des pièces d'or ; les accessoires et couleurs s'achètent à la **boutique** (clic sur le bandeau en haut du menu). Un titre tous les quelques niveaux. Détail : [README](../../README.md#clic-droit-sur-pilou).

Tout est dessiné en pixels, objets des jeux et chiffres compris (dessin fin 2× au choix : *Apparence ▸ Dessin fin*).

Au repos, Pilou se promène, s'assoit, bâille quand tout est calme depuis 3 min, saute, cligne de
l'œil, et suit la souris du regard quand elle passe près de lui.

Une session qui t'attend (autorisation, question) rend Pilou orange et inquiet, et il **court se
placer sous la souris** (sur l'horizontale) et la suit, en sautillant une fois arrivé, jusqu'à la
réponse ou au clic « lu ». Clic : caresse ; glisser : il change
d'écran et retombe ; clic droit : le menu (voir le [mode d'emploi](../../docs/MODE-EMPLOI.md)). Libellé d'une session : le
début de son premier message (le titre de l'app n'est pas lisible par un mod), sinon son dossier.

- Chaque session publie son état dans `~/.claude/compagnon/etat-<session>.json` ; l'overlay suit
  la session la plus active. Ses caresses reviennent par `~/.claude/compagnon/caresses.txt`.
- Le mod lance `~/.claude/compagnon/bureau/PilouBureau.exe` au démarrage d'une session s'il
  existe ; `/compagnon bureau` l'arrête ou le relance.
- Fabrication : `dotnet publish apps/PilouBureau -c Release -o ~/.claude/compagnon/bureau`.
- Essai visuel : `PilouBureau.exe --devant <dossier d'états>` (à l'écran) ou
  `--instantane=<png> <dossier>` (rendu WPF dans un PNG, sans écran : session RDP réduite).
