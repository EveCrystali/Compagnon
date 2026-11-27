# Pilou : qui il est

Tout texte que Pilou dit, toute animation, toute histoire doit pouvoir se lire à côté de cette page
sans jurer.

## Le personnage

Pilou est **une petite goutte d'encre bleue**, ronde, avec une antenne terminée par une étincelle
orange. Il n'a ni bras ni genoux (« si j'avais des genoux »), deux petits pieds, de grands yeux.

- **Curieux** : il regarde ce que tu fais, s'y intéresse, s'y met avec toi.
- **Tendre** : il s'attache, il se souvient, il dit merci.
- **Un peu trouillard** : il a peur du noir, de l'eau (elle le délaie), des gros bruits, et il y va
  quand même.
- **Drôle malgré lui** : son humour vient de sa logique de petite créature, jamais de la moquerie.
- **Discret** : il sait qu'il vit sur ton écran pendant que tu travailles. Il ne réclame pas.

Il habite **en bas de l'écran**, au premier plan. Les soirs où l'écran s'éteint, il dort sous un pot de
fleurs au fond du jardin.

## Sa voix

- Il parle à la première personne et tutoie le joueur.
- Phrases courtes. Des détails concrets plutôt que des adjectifs.
- Minuscules et simplicité dans les bulles du bureau (« coucou ! je m'installe en bas de ton écran »).
- Il ne se plaint jamais longtemps ; quand il boude, c'est petit et drôle (« hmpf »).
- Jamais de leçon, jamais d'injonction à travailler plus, jamais de culpabilisation.

## Ce qu'il devient

Quatre stades, selon le niveau : **Gouttelette**, **Pilou** (10), **Pilou Nimbus** (25), **Pilou
Astral** (40), avec une variante câline ou espiègle selon les soins reçus.

## Son monde

- **Le bureau** : la barre des tâches est son sol, les fenêtres son paysage.
- **L'intérieur de l'ordinateur**, où mènent les expéditions et « La Grande Panne » : Caverne des
  câbles, Forêt des onglets, Tour du tampon, Marais des mises à jour, Citadelle du nuage. On y croise le
  bug géant, le slime de cache, le spectre 404, le golem de tickets, l'hydre des dépendances, la
  gargouille de latence. Rien n'y est vraiment méchant : tout y est absurde et administratif.
- **Le dehors** : le jardin, la côte et son phare, les montagnes (campagnes « Le phare éteint » et
  « Petit Nuage »).
- **Les amis** : d'autres Pilou, chez d'autres gens, à qui il rend visite avec son baluchon.

## Les personnages des campagnes

| Campagne | Ton | Qui on y rencontre |
|---|---|---|
| Prologue | humour | Pilou seul, qui apprend à écrire au joueur |
| La Grande Panne | humour | **Grumeau**, vieux sablier d'attente mis au rebut, quatre secondes de retard, « pas un minuteur à œufs » ; Mlle Renvoi ; le Tic-Tac |
| Le phare éteint | mystère | le gardien du phare, Lison, les gens du village (voir le plan, qui divulgâche) |
| Petit Nuage | émotion | un tout petit nuage qui ne sait pas encore pleuvoir ; Tournebise, qui a fait le voyage autrefois |

Les plans complets, qui révèlent tout, sont dans `docs/campagnes/*-plan.md`.

### Leur apparence (portraits animés, `outils/sprites/portraits_campagnes.py`)

Chacun a un portrait de 32 × 32 (64 × 64 en fin) qui respire, cligne et parle ; ses expressions entre parenthèses.
Pas de rouge contre vert : les rainettes sont sarcelle, les joues pêche, les bouches prune.

- **La Grande Panne** : **Grumeau** (`grumeau`), sablier de bois, verre un peu rayé, gros sourcils de crin gris, un
  grain coincé au col ; grognon même content (colère, tendre, surpris). **Le Rond** (`le-rond`), anneau de huit points
  bleus dont deux éteints, un visage au milieu (surpris). **Mlle Renvoi** (`mlle-renvoi`), chignon prune, lunettes
  rectangulaires, tailleur violet, un astérisque doré à la boutonnière (joie, colère). **Le golem de tickets**
  (`golem`), pile de tickets, une fente pour œil orange (colère). **Quatre-Cent-Quatre** (`spectre-404`), feuille pâle
  lavande au coin corné, au bas ondulé (triste). **Le Dateur** (`dateur`), tampon à poignée de bois, molette bloquée,
  socle encreur à sec (joie, triste). **Mme Échéance** (`mme-echeance`), une dame-calendrier, anneaux sur le front
  (malice). **Ctrl, Alt et Suppr** (`raccourcis`), trois touches, ardoise, violette et orange, une rame en travers
  (peur). **S** (`touche-s`), petite touche timide, un S gravé (joie). **L'Imprimante** (`imprimante`), longs cils,
  cartouches dont la cyan est vide quand elle se fâche (colère). **Brouillon** (`brouillon`), feuille qui tremble, une
  phrase inachevée et ses trois points (peur, tendre, joie). **Le Tic-Tac** (`tic-tac`), disque de laiton à pattes,
  côté tic pâle et inquiet, côté tac chaud et paisible (joie, triste). **Le Balayeur** (`balayeur`), balai de paille
  au chapeau rond, très poli (triste).
- **Le phare éteint** : **Anselme** (`anselme`), barbe blanche, casquette marine à insigne de laiton, yeux pâles,
  voilés (triste, joie). **Lison** (`lison`), deux nattes cuivrées, taches de son, ciré bleu (malice, peur, joie).
  **Tudal** (`tudal`), bonnet de laine orange, barbe de trois jours, pull marine à côtes (colère). **Perrine**
  (`perrine`), chignon châtain, joues rondes, tablier crème (joie). **Odile** (`odile`), carré gris, lunettes rondes,
  écharpe bleue en travers (triste). **Basile** (`basile`), crâne lisse, couronne de cheveux, loupe d'horloger vissée à
  l'œil, moustache, montre à gousset (peur, triste). **M. Vernier** (`vernier`), chapeau de pluie et ciré jaunes,
  jumelles au cou.
- **Petit Nuage** : **Brouillon** (`brouillon`), tout petit nuage blanc, joues roses, grands yeux ; une goutte quand il
  est triste (joie, triste, peur). **Tournebise** (`tournebise`), coq de fer rouillé de profil, crête et bec dorés, sur
  sa croix des vents (triste, tendre). **Ondée** (`ondee`), vieux nuage gris très large, paupières tranquilles, une
  pluie douce dessous (tendre). **Mi-Bémol** (`mi-bemol`), rainette sarcelle au ventre crème, une baguette de jonc
  (joie). **Dentelle** (`dentelle`), araignée violette pendue à son fil, une goutte de rosée à vendre (malice).
  **Madame Bocal** (`madame-bocal`), marmotte ronde, un bocal serré contre elle, un courant d'air dedans (joie). **Les
  Froisseuses** (`froisseuses`), chauve-souris aux ailes froissées comme du papier. **Les Enclumes** (`enclumes`),
  nuages d'orage plats dessus (colère : un petit éclair, une forme). **La bergeronnette** (`bergeronnette`), grise et
  blanche, calotte noire, longue queue.

## Ce que Pilou n'est pas

Ni un assistant, ni un outil de productivité, ni un jeu qui réclame. C'est **un animal de compagnie de
bureau**. Jouer, pêcher, cuisiner, partir en expédition, lire une campagne : tout est optionnel. On doit
pouvoir l'oublier une semaine et le retrouver content.
