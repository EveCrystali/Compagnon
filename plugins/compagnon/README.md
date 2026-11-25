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

**Options (clic droit, gardées dans `~/.claude/compagnon/reglages.json`)** : taille (petit / normal /
grand) · bulle détaillée, compacte (urgences + résumé « ◐ 2 en cours · ✓ 3 finies », détail au
survol) ou seulement quand Claude attend · thème de la bulle (Windows / clair / sombre) · accessoire
(saison, aucun, bonnet de laine, casque audio, nœud papillon, feuille d'automne ; saison : feuille
en oct.–nov., bonnet en décembre, casque en janv.–févr.) · se promène · suit la souris du regard.
Clic sur la bulle : met Claude au premier plan et range la bulle (« lu ») ; clic sur Pilou : caresse et « lu ». La bulle revient au prochain changement ; le survol remontre tout.

**Jeux et vie** :
- tu ne touches plus à rien depuis 3 min : il saute s'accrocher au curseur par l'antenne et gigote ; 10 min : il s'endort (premier geste = réveil, « bien dormi ! ») ;
- Claude t'attend et tu ne bouges plus depuis 45 s : il se colle à l'écran et toque (« TOC ») ;
- souris secouée près de lui : tête qui tourne (yeux en spirale, étoiles) ; souris posée sur lui : il ronronne ;
- ennui : il joue au ballon ; phrases du jour (bonjour, bon appétit, il se fait tard, bon week-end) ;
- **petites activités** (toutes les 8–16 min si tu es là, ou « Jouer maintenant ») : étoile filante à attraper (+10 xp), 3 bulles à éclater (+5 chacune, +5 de bonus), « tape m'en cinq » (+10) ; chaque gain s'affiche en « +N xp » ;
- **pêche** (clic droit « Pêcher », une fois sur trois parmi les activités, ou seul quand tu t'éloignes) : Pilou lance sa ligne au bord d'une petite eau ; après 3 à 15 s le bouchon plonge, éclabousse et un « ! » apparaît. Clic sur le bouchon dans la seconde : prise assurée. Trop tôt : le poisson file. Personne : Pilou ferre seul, une fois sur trois environ, jamais mieux que « rare ». 23 prises (poissons, crabes, botte, bouteille à message, coffret englouti, perle de lune…) en cinq raretés, chacune avec son signe et son cadre : `·` commun sans cadre, `◇` peu commun (coins), `◆` rare (trait bleu), `✦` épique (double, orange), `★` légendaire (argent et orange). Première prise d'une espèce : XP doublée. **Carnet de pêche** au clic droit (« ??? » pour ce qui reste à trouver) ;
- **cuisine** (clic droit « Cuisiner », ou seul) : avec les prises comestibles en réserve, marmite sur le feu, flammes et vapeur, puis un plat au-dessus de sa tête. 30 recettes du livre débloquées par niveau (Pilou tente d'abord celles jamais faites) et des plats inventés (préparation × ingrédient × touche : « Velouté d'anguille d'encre au clair de lune ») ; chaque plat nouveau rapporte un bonus. Un clic sur la marmite : il remue et rien ne brûle ; sinon, rarement, fumée noire. **Livre de recettes** au clic droit ;
- **niveaux** (jusqu'à 50) : l'XP (jeux, pêche, cuisine, tours finis, commits, tests, caresses) fait monter de niveau, avec fête et récompense : nœud papillon 2, casque 3, bonnet 4, lunettes de soleil 5, couronne 7, chapeau de pêcheur 14, toque de chef 18, tablier 22, étoile de mer 27 ; couleurs lagon 20, braise 26, nacre 32, abysse 40, comète 50 ; canne dorée 30 (plus de légendaires), marmite en cuivre 35 (moins de ratés) ; un titre tous les quelques niveaux, jusqu'à « Pilou éternel ».

Tout est dessiné en pixels (grille 26 × 30, pixel de 4), objets des jeux et chiffres compris.

Au repos, Pilou se promène, s'assoit, bâille quand tout est calme depuis 3 min, saute, cligne de
l'œil, et suit la souris du regard quand elle passe près de lui.

Une session qui t'attend (autorisation, question) rend Pilou orange et inquiet, et il **court se
placer sous la souris** (sur l'horizontale) et la suit, en sautillant une fois arrivé, jusqu'à la
réponse ou au clic « lu ». Clic : caresse ; glisser : il change
d'écran et retombe ; clic droit : caresser, se cacher 10 min, quitter. Libellé d'une session : le
début de son premier message (le titre de l'app n'est pas lisible par un mod), sinon son dossier.

- Chaque session publie son état dans `~/.claude/compagnon/etat-<session>.json` ; l'overlay suit
  la session la plus active. Ses caresses reviennent par `~/.claude/compagnon/caresses.txt`.
- Le mod lance `~/.claude/compagnon/bureau/PilouBureau.exe` au démarrage d'une session s'il
  existe ; `/compagnon bureau` l'arrête ou le relance.
- Fabrication : `dotnet publish apps/PilouBureau -c Release -o ~/.claude/compagnon/bureau`.
- Essai visuel : `PilouBureau.exe --devant <dossier d'états>` (à l'écran) ou
  `--instantane=<png> <dossier>` (rendu WPF dans un PNG, sans écran : session RDP réduite).
