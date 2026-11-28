# Audit large : ce qui sépare Pilou d'un jeu professionnel

Écrit par le pilote le 28 novembre 2026, à la demande d'Antoine, au moment où le projet entre en finition de sa
version 1. Question posée : qu'est-ce qui différencie Pilou d'une application professionnelle, et qu'est-ce qui
l'amènerait au sommet sur les animations, les campagnes, le narratif, l'attachement, la beauté, le jeu « idle », et
faut-il un côté RPG en plus ?

**Statut : un diagnostic et des propositions. Rien ici n'est décidé ni construit.** Les chantiers ne partent qu'après
les réponses d'Antoine aux questions de la fin.

## Méthode et limites

- Relevé : lecture de `LORE.md`, `ETAT.md`, `DECISIONS.md`, `IDEES.md`, plus deux inventaires du code et des contenus
  faits par des agents de recherche (comptes par recherche de texte, rien compilé ni exécuté). Quelques points
  contrôlés à la main. **Confiance sur les chiffres : 85 %.**
- Le jugement « niveau professionnel » est celui du pilote, par comparaison avec les compagnons de bureau, les jeux
  « idle » et les fictions interactives du commerce. **Confiance sur le diagnostic : 70 %.** Ce n'est pas un test
  auprès de joueurs : personne d'autre qu'Antoine n'a joué.
- Aucun vrai téléphone, aucun second PC, aucun écran à 125 / 150 % n'a servi à cet audit.

## Ce qui est déjà au niveau

| Point | Fait mesuré |
|---|---|
| Volume et tenue du récit | 4 campagnes, 618 nœuds, 159 choix (423 options), 25 épreuves, 20 fins, 207 drapeaux, 128 conditions ; relues de bout en bout |
| Distribution | 29 personnages, 69 portraits animés, 46 décors animés, 20 souvenirs |
| Une voix | `LORE.md` tient le personnage ; 600 petits mots environ, journal régénéré à l'identique des deux côtés |
| Respect du joueur | 3 mots par jour au plus, rien pendant la saisie, complicité qui ne baisse jamais, tout est optionnel |
| Économie pensée | 251 objets, 10 ensembles, 6 raretés, saisons, « de passage » ; cible d'un an de collection |
| Rigueur technique | environ 600 tests, 5 jobs de CI, références partagées PC / Android, 1 500 marches rejouées par campagne |

Peu de projets amateurs ont ce socle. L'écart avec un produit professionnel n'est donc **pas dans la quantité**. Il
est dans quatre choses : la preuve sur de vrais appareils, les cinq premières minutes, l'unité visuelle et sonore,
et la vie du personnage entre deux événements.

## Les sept axes

Échelle : **solide** (au niveau), **correct** (fonctionne, se voit qu'il manque une passe), **mince** (c'est là que
l'on reconnaît un projet amateur).

| Axe | Niveau | L'écart principal |
|---|---|---|
| Campagnes | solide | Mise en scène et musique absentes hors prologue |
| Narratif | solide | Pas de fil qui relie tout ; les personnages disparaissent après leur campagne |
| Attachement | correct | Pilou se souvient, mais ne demande rien et n'offre rien |
| Beauté | correct | Deux écritures visuelles se mélangent (pixel et police système) |
| Animations | correct | Peu de variété au repos, peu de réactions au monde |
| Jeu « idle » | mince | Rien ne se passe pour de vrai pendant qu'on travaille |
| RPG | en germe | Les expéditions en ont déjà les pièces, sans vitrine |
| Produit (hors jeu) | mince | Installation, première minute, signature, vérification réelle |

### 1. Animations

Constat :
- Pilou est dessiné par le code (`RenduPilou.cs`) : 9 expressions, une dizaine de gestes, 4 stades, 8 tenues.
- Au repos, il ne connaît que cinq occupations (`FenetrePilou.cs:22` : marche, assis, bâille, ballon, saute vers la
  souris). C'est ce qu'on regarde le plus, et c'est le plus court.
- Depuis #90 : ressorts, antenne en retard, ombre, poussière. C'est la bonne direction.
- Aucune réaction aux bords de l'écran, à une fenêtre qu'on pose près de lui, au fait d'être pris et lâché.
- Les objets portés ne changent pas ses gestes (une canne à pêche, un jetpack, un compagnon ne font rien de plus).

Ce que fait un compagnon de bureau du commerce : **trente à soixante petites saynètes de repos**, tirées au hasard
avec des poids, dont certaines très rares. C'est la rareté qui fait dire « tiens, je ne l'avais jamais vu faire ça »
après trois mois.

Propositions :
1. **Banque de saynètes de repos** (30 pour la v1) : il lit, il compte ses pièces, il poursuit son étincelle, il
   s'endort par étapes, il regarde par-dessus le bord de la barre, il joue avec son compagnon. Chacune de 3 à 8 s,
   au calme seulement, sous la retenue existante. Certaines liées à l'heure, à la saison, à l'objet porté, au stade.
2. **Réactions au monde** : pris et lâché (il pend, retombe, se secoue), bord d'écran (il freine, regarde le vide),
   long survol, double clic.
3. **Raccords** : aucun changement d'état en coupe franche ; un temps d'anticipation avant, un temps de retombée
   après (la règle de #90 étendue à tous les gestes).
4. **Interfaces qui répondent** : fenêtres qui s'ouvrent en deux images, boutons qui s'enfoncent d'un pixel,
   compteurs de pièces qui roulent, objet acheté qui saute dans la tenue.

### 2. Campagnes

Constat :
- Le fond est là. La forme vient de changer : le « Théâtre » (#95) met le prologue en scène, avec un mini-Pilou et
  13 acteurs. Les trois grandes campagnes restent en décor + portrait.
- **Aucune musique.** Dix sons d'interface, zéro boucle d'ambiance. Une campagne « émotion » (Petit Nuage) et une
  campagne « mystère » (Le phare éteint) sans musique perdent la moitié de leur effet.
- Rejouer ne rapporte rien ; le Carnet garde les fins, ce qui suffit si les fins manquantes se devinent.
- Aucun rappel d'une campagne dans une autre (vérifié par recherche des noms : seuls les petits mots citent Grumeau).

Propositions :
1. **Théâtre pour les trois grandes campagnes**, une par PR (lancé après #95, « La Grande Panne » d'abord).
2. **Une boucle musicale par ton** (humour, mystère, émotion) plus une pour le bureau la nuit, synthétisées par le
   script maison comme les sons, de 30 à 60 s, très bas, coupables par le réglage des sons. Plus trois ou quatre
   ambiances (vent, pluie, hall).
3. **Un « précédemment »** d'une phrase au retour d'une attente longue, écrit par Pilou.
4. **Carnet qui donne envie** : silhouette des fins non vues, pourcentage par campagne, sans révéler.

### 3. Narratif

Constat :
- Chaque campagne est une île. Le lore a pourtant un monde (le bureau, l'intérieur de l'ordinateur, le dehors) et
  quatre stades d'évolution, mais **aucune histoire ne les relie**.
- Passer de Gouttelette à Pilou au niveau 10 est le plus grand moment de la progression. Il n'a pas de scène.
- Grumeau, Lison, Brouillon n'existent plus une fois leur campagne finie.

Propositions :
1. **Les évolutions racontées** : une courte scène du Théâtre à chaque stade (niveaux 10, 25, 40), où Pilou dit ce
   qui change pour lui. Trois scènes, écrites une fois.
2. **Les personnages reviennent** : une carte postale de Lison, Grumeau qui traverse le bas de l'écran une fois par
   mois, quatre secondes en retard. Rare, jamais deux fois la même semaine, seulement si la campagne est finie.
3. **Un fil d'ensemble discret** : d'où vient l'encre, pourquoi cet écran-ci. Semé dans le journal et les petits
   mots, résolu dans une cinquième campagne courte, plus tard. À écrire d'abord comme un plan, validé par Antoine.

### 4. Attachement

Constat :
- Les bases sont justes et rares : il se souvient (900 dernières lignes, souvenirs de campagne cités), il fête les
  dates, il ne culpabilise jamais, la complicité ne redescend pas.
- Mais la relation va dans un seul sens. **Pilou ne demande jamais rien au joueur et ne lui donne jamais rien.**
  Or on s'attache à ce qui nous connaît et à ce qui pense à nous.
- Les cinq paliers de complicité n'ouvrent rien de visible, à part leur annonce.

Propositions :
1. **De rares questions** (une par semaine au plus, deux réponses, ignorer vaut « plus tard ») : « tu préfères le
   matin ou le soir ? ». La réponse est gardée et **citée des semaines après**. C'est le levier d'attachement le plus
   fort de tout cet audit. Il touche à une décision (« pas de réponse depuis la bulle ») : **à trancher par Antoine**.
2. **Pilou offre** : un caillou, un dessin, une prise ratée, posés dans un petit coffre « de Pilou pour toi ». Sans
   valeur en pièces. Une fois de temps en temps, jamais annoncé deux fois.
3. **Un geste par palier** : Copain, il vient s'asseoir près du curseur ; Ami, il s'endort contre lui ;
   Inséparables, il fait signe quand la session s'ouvre. Rien à acheter : ça se mérite par le temps.
4. **Ses goûts à lui**, découverts peu à peu (son plat préféré, ce qui lui fait peur) et notés dans « Pilou et moi ».

### 5. Beauté

Constat :
- Le dessin des sprites est au niveau : 589 sprites en dessin fin, aucun agrandi automatiquement.
- **Deux écritures se mélangent.** La capture PC de #95 le montre : titres en police pixel, texte en police système,
  boutons avec des signes de clavier (☰ ❖ ✧ ⋯). Sur Android : pixel art dans la scène, police système partout
  ailleurs. Un jeu professionnel a **une seule main**.
- Pas de guide de style écrit : chaque fenêtre a été faite à son tour.
- Jamais vu à 125 % ni 150 %, ni sur deux écrans d'échelles différentes (point connu).

Propositions :
1. **Guide de style** (`docs/STYLE.md`) : palette nommée, cadres, marges, tailles de texte, états des boutons, jeu
   d'icônes pixel maison qui remplace les signes de clavier. Une page, des exemples dessinés.
2. **Police pixel partout** où elle reste lisible (titres, boutons, nombres) ; police système seulement pour les
   longs textes de récit, et ce choix écrit noir sur blanc.
3. **Passe d'unification fenêtre par fenêtre**, avec planche avant / après, dans l'ordre où le joueur les voit :
   bulle, menu (en cours), boutique, soins, Aventure, réglages, puis Android écran par écran.
4. **Les échelles** : 125 %, 150 %, deux écrans. À faire sur le PC d'Antoine, en changeant l'échelle le temps du test.

### 6. Jeu « idle »

Constat :
- C'est l'axe le plus mince, et c'est pourtant la promesse : « il grandit pendant que tu travailles ».
- Pendant qu'on travaille : l'énergie monte, les heures de métier comptent, un petit jeu se propose toutes les 14 à
  28 minutes. **Aucun gain passif d'expérience ni de pièces, rien à découvrir au retour.**
- Les dix métiers comptent des heures et donnent un grade. Ils ne changent rien d'autre.
- Le niveau « maximum 50 » est déclaré mais jamais appliqué ; rien n'est prévu après.

Ce que fait un bon jeu « idle » : **le monde avance sans vous, et le plaisir est de revenir voir**. Ce n'est pas
contraire à « Pilou reste passif » : c'est même le seul jeu qui ne demande rien.

Propositions :
1. **« Pendant que tu travaillais »** : Pilou a une occupation de fond visible (il jardine sous son pot de fleurs, il
   trie ses trouvailles, il écrit). Au retour d'une pause, un seul geste montre ce qu'il a fait : une pousse, un
   objet trouvé, une page de journal. Plafonné par jour, comme tout le reste.
2. **Le jardin du pot de fleurs** (il est déjà dans le lore) : trois ou quatre plantes qui poussent en temps réel sur
   des jours, que la météo réelle arrose. Rien à perdre si on l'oublie.
3. **Les métiers se voient** : un Pilou « codeur » de grade élevé gagne un tic, un accessoire discret, des répliques.
   Pas de bonus chiffré : une personnalité.
4. **Après le niveau 50** : décider. Soit un plafond assumé avec une fin douce, soit des « constellations » (niveaux
   de prestige purement cosmétiques).

Cet axe ajoute des fonctions de jeu : il sort du cap actuel (« on ne rajoute pas de fonctions »). **À rouvrir par
Antoine**, ou à garder pour après la version 1.

### 7. Un côté RPG en plus ?

Constat : il existe déjà. Les expéditions ont 5 lieux, 6 créatures, des cœurs, 13 outils à effets (7 armes,
6 talismans), des objets exclusifs, un butin. L'évolution a 4 stades et deux variantes (câlin, espiègle). Ce qui
manque n'est pas la mécanique, c'est **la vitrine** : on ne voit ni carte, ni bestiaire, ni récit de l'expédition.

Recommandation du pilote : **ne pas ajouter de statistiques ni d'arbre de compétences.** Raisons :
- cela contredit trois décisions (« d'abord un animal de bureau », « tout est optionnel », « pas de difficulté ») ;
- des chiffres à optimiser changent la relation : on gère un personnage au lieu de s'y attacher ;
- l'équilibrage coûterait des semaines pour un gain d'image faible.

À la place, un **RPG de personnalité** :
1. **Traits** nés des habitudes réelles (couche-tard, pêcheur du dimanche, lecteur), affichés dans « Pilou et moi »,
   qui changent des répliques et des saynètes. On ne les choisit pas : on les découvre.
2. **Carte de l'intérieur de l'ordinateur** qui se dévoile lieu par lieu, **bestiaire** illustré des six créatures
   (et des personnages croisés), **récit** de chaque expédition écrit par Pilou dans le journal.
3. **Évolution lisible** : avant le stade, montrer vers quelle variante il penche et pourquoi.

Confiance dans cette recommandation : 70 %. Si Antoine veut de vraies statistiques, le bon endroit est l'expédition
seule (elle est déjà un combat), jamais le Pilou du bureau.

### 8. Le produit autour du jeu

C'est ici qu'on reconnaît d'abord un logiciel professionnel, avant même d'avoir joué.

| Sujet | État | Effet sur un inconnu |
|---|---|---|
| Installation | une ligne PowerShell, dépôt privé | la plupart des gens s'arrêtent là |
| Signature du binaire | aucune (certificat local seulement) | Windows affiche un avertissement ; bloque aussi la lecture des notifications |
| Poids | 128 Mo, compression non faite | téléchargement et mise à jour lourds |
| Première minute | un mot de bienvenue, pas de visite | 44 réglages et un menu, sans guide |
| Présentation | un README, pas de page ni de site | rien à partager |
| Android | pas de fiche de magasin trouvée | installation à la main |
| Langue | français seul | public limité |
| Erreurs | pas de journal général ni de rapport de plantage | un plantage chez un inconnu ne se saura jamais |
| Preuve réelle | longue liste « jamais vérifié » dans `ETAT.md` | sons jamais écoutés, téléphone jamais vu en vrai |
| Documentation | `plugins/compagnon/README.md` périmé (17 succès au lieu de 22, fréquences fausses) ; tableau de `CAMPAGNES.md` incomplet ; 573 petits mots annoncés, 636 lignes comptées | détails, mais c'est la v1 |

La **première minute** mérite un chantier à elle : Pilou arrive, se présente en trois bulles, montre un geste
(caresse), propose le prologue, et laisse tranquille. Les réglages viennent après, par défaut bien choisis.

## Ordre proposé pour la version 1

Rangé par effet sur la perception, à coût raisonnable. Les numéros 1 à 6 restent dans le cap actuel (finir et
embellir l'existant). Les autres demandent une décision.

| Rang | Chantier | Axe | Dans le cap ? |
|---|---|---|---|
| 1 | Vérification sur vrais appareils et corrections (téléphone avec Antoine, 125 / 150 %, sons écoutés) | Produit | oui |
| 2 | Guide de style, icônes pixel maison, police pixel partout, passe fenêtre par fenêtre | Beauté | oui |
| 3 | Banque de 30 saynètes de repos et réactions au monde | Animations | oui |
| 4 | Théâtre des trois grandes campagnes | Campagnes | oui (lancé) |
| 5 | Musiques et ambiances synthétisées | Campagnes | oui |
| 6 | Première minute | Produit | oui |
| 7 | Scènes d'évolution, personnages qui reviennent | Narratif | à confirmer (contenu neuf, mais court) |
| 8 | Gestes de palier, cadeaux de Pilou | Attachement | à confirmer |
| 9 | Signature, installeur simple, exe allégé, page de présentation, promo finale | Produit | dépend de la question 4 |
| 10 | « Pendant que tu travaillais », jardin | Idle | non : à rouvrir |
| 11 | Questions de Pilou | Attachement | non : décision à revoir |
| 12 | Traits, carte, bestiaire | RPG | non : à rouvrir |

## Questions pour Antoine

1. **Idle** : rouvre-t-on le cap pour « pendant que tu travaillais » et le jardin avant la v1, ou après ?
2. **Questions de Pilou** : acceptes-tu qu'il pose une question rare à deux réponses (cela modifie la décision « pas
   de réponse depuis la bulle ») ?
3. **RPG** : personnalité (traits, carte, bestiaire) comme recommandé, ou de vraies statistiques dans les expéditions ?
4. **Public de la v1** : toi et tes amis, ou une diffusion publique ? La réponse décide de la signature (payante),
   de la page de présentation, de la fiche Android et de l'anglais.
5. **Après le niveau 50** : plafond assumé ou niveaux de prestige cosmétiques ?
