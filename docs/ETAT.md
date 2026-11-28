# État du travail

À mettre à jour à la fin de chaque session : ce qui est fait, ce qui est en cours, ce qui attend.
Dernière mise à jour : 28 novembre 2026.

## En ligne (v0.9.75 et suivantes)

- Overlay Windows, app Android, mod Claude Code, extensions VS Code et Visual Studio.
- Boutique garnie, métiers et succès partagés entre appareils, expéditions, Défense du bureau,
  visites entre amis, connecteurs, météo.
- **Campagnes jouables des deux côtés** : le moteur (PC et Android, validateur, synchronisation), quatre histoires
  (prologue, La Grande Panne, Le phare éteint, Petit Nuage) et leurs interfaces Aventure. Sur Windows : Pilou occupé en
  tenue de voyage, retour annoncé une seule fois, fenêtre Aventure, épreuves, récompenses, scènes d'essai
  (`--essai=campagne:…`). Sur Android : onglet Aventure (conversation, épreuves, attente), notification de retour,
  bulle flottante, accueil repensé.
- **Les trois grandes campagnes ont été relues de bout en bout** (parcours entiers, raccords, dosage des fins, orthographe) ;
  les quatre sont passées au correcteur LanguageTool (français) le 27 novembre : 550 signalements triés, aucune faute
  retenue, aucun texte modifié. Le prologue est court exprès.
- **Illustrations** : 46 décors animés en boucle, 69 portraits animés de 29 personnages (champs `personnage` et
  `expression` des nœuds, relus un par un le 27 novembre), 20 souvenirs, une vignette par campagne et un emblème par
  ton, objets exclusifs des fins.
- **Paysages haute définition** (docs/PEINTURE.md) : moteur de peinture `outils/sprites/paysage.py`, format « décor compact »
  (`assets/decors/`, docs/SPRITES.md) ; les 46 décors sont peints en 480 × 240 (règle 9), au format à plans de docs/SCENES-HD.md :
  prologue (6), La Grande Panne (12), Le phare éteint (14), Petit Nuage (14) ; planches dans
  `docs/maquettes/paysages/<campagne>/`. Pas encore affichés dans l'app (le Théâtre HD est un autre chantier) ; les
  anciens décors 192 × 80 restent en service jusqu'à la bascule. Jamais vus sur un vrai Windows ni un vrai téléphone.
- **Personnages haute définition** (docs/SPRITES.md) : les 29 personnages en pied des trois campagnes sont redessinés
  à l'unité 480 × 240 et exportés (`assets/sprites-hd/`, 69 fichiers, 438 Ko, format de docs/SCENES-HD.md, référence
  `personnages-hd-reference.txt`). Pas encore affichés dans l'app (le Théâtre HD ne les lit pas encore) ; jamais vus
  sur un vrai Windows ni un vrai téléphone. Les 29 acteurs de scène (bêtes et effets) sont redessinés et exportés
  eux aussi (`acteur-<nom>.txt`). Les effets clairs (brume, vapeur, ronds) ne se lisent que sur un décor, pas sur fond clair.
- **Dessin fin 2×** : 664 sprites redessinés sur 693, dont les 54 icônes d'interface (docs/STYLE.md) ; restent agrandis
  automatiquement les 29 particules des saynètes (`sc-*`), d'après `python3 outils/sprites/fin.py`.
- **Présence de Pilou** (docs/PRESENCE.md) : petits mots (banque de 573), cadence (3 par jour sur PC, 1 le soir sur
  téléphone), complicité, journal identique des deux côtés, prénom, « Pilou et moi ».
- **Traits de personnalité** (docs/TRAITS.md) : vingt traits nés des habitudes (jours du journal), découverts et jamais
  perdus, trois dominants qui changent une fois par semaine ; aucun chiffre ni bonus : une annonce dite une fois, des
  répliques (80 lignes), et « Pilou et moi » (PC : Journal → Ses traits… ; téléphone : carte de l'Accueil) avec les
  inconnus en « ? ». Moteur commun `Traits.cs` / `Traits.java`, vecteurs partagés, union entre appareils.
- **Police pixel de Pilou** (docs/POLICE.md) : 223 glyphes dessinés à la main, tout le français, quatre tailles (texte,
  titre, et leur dessin fin), mise en page identique PC / Android. Première vague : la phrase de Pilou en tête de bulle
  (PC), le mot du jour dans la bulle flottante, l'Accueil et le widget (Android). Depuis le guide de style : tout
  l'Accueil, Jouer, la Boutique, la Collection, l'en-tête et la barre du bas du téléphone.
- **Guide de style** (docs/STYLE.md, 28 novembre 2026) : la main de Pilou écrite et mesurée sur le menu « Sept
  portes », la bulle et le cadre de l'Aventure : palette nommée (clair, sombre), module, cadre en pixels (bord, biseau,
  ombre portée, coins en escalier), tailles de police, états des boutons, titres de section, pointillés, puces ;
  54 icônes pixel maison (`outils/sprites/icones.py`, `ui-*` 12 × 12 et `signe-*` 7 × 7) à la place des signes de
  clavier. Appliqué au téléphone hors Aventure : en-tête (« Prochaine rangée… » reformulée, plus jamais tronquée),
  barre du bas (libellés qui ne se touchent plus en grande police), Accueil, Jouer, Boutique, Collection, « Rangées
  débloquées » (`Style.java`). Captures Robolectric 1078 × 2400 à 440 dpi en clair, sombre et grande police, relues
  une par une (`CapturesStyleTest`, docs/captures/style/). Finition du même jour : Réglages (cases à cocher du
  menu, options, curseur, champs), carte « Pilou et moi » et ses traits, ligne de premier lancement, icône du besoin
  de soin, messages brefs ; `TextesSystemeTest` échoue dès qu'un texte de ces écrans est écrit en police système.
  **Jamais vu sur un vrai téléphone.** Restent en style système : liste des aventures, épreuves, atelier, chasse aux
  bugs, installation, bulle flottante. PC : la boutique et « Rangées débloquées » sont au guide (`StylePixel.cs` :
  texte, bouton et ses états, icône, barre de défilement en pixels), le journal, la question du prénom, « Pilou et moi » et les expéditions aussi, vus dans l'exe
  d'essai à 100 % ; restent amis et connecteurs (formulaires au thème clair du système), l'invitation, et l'en-tête
  commun (`Bandeau.cs`). Plancher de lisibilité (docs/STYLE.md) : plus aucun texte en minuscules dans la plus petite taille
  de la police pixel, sur le PC (hauteur d'x de 10 px à 100 %, 7 pour le menu) comme sur le téléphone ; « petit » ne
  sert plus qu'aux capitales et aux nombres. La bulle du bureau reste sous ce plancher (5 px) : à trancher.
  Habillage commun des fenêtres du PC (`HabillageFenetre`) : barre de titre en pixels, icône de Pilou, boutons maison,
  posé sur boutique, journal, prénom, « Pilou et moi », expéditions ; essayé pour de vrai sur le PC (ouverture, déplacement,
  redimensionnement, taille minimale, réduire, ✕, Alt+F4, Échap). Pas encore sur l'Aventure, la scène d'évolution, amis,
  connecteurs.
- **Vie du personnage** (docs/SPRITES.md) : sauts en arc avec ressorts, antenne en retard, ombre tramée en l'air,
  poussière en marchant et à l'atterrissage, lumière du moment ; réglage « ✧ » respecté, « aucune » = mouvements
  d'avant. Vu dans l'exe d'essai sur le PC d'Antoine (`--essai=vie`), processeur inchangé (≈ 6 % d'un cœur avant
  comme après) ; jamais vu sur un vrai téléphone.
- **Saynètes de repos** (docs/SPRITES.md) : 30 petites scènes de 3 à 8 s (lit, compte ses pièces, poursuit son
  étincelle, s'endort, regarde les étoiles, pêche, grignote… quatre rares), tirées avec des poids, selon l'heure, le
  mois, le stade, l'objet porté, le compagnon et les traits dominants ; trois réactions au monde sur le PC (freine au
  bord, lâché, long survol). Même banque et mêmes tirages sur le PC et le téléphone. Sans aucune session d'IA, Pilou est
  désormais éveillé (il ne dort que si on s'absente, ou la nuit). Vu dans l'exe d'essai sur le PC d'Antoine
  (`--essai=saynete`, `--essai=eveil`) ; jamais vu sur un vrai téléphone.
- **Test de jeu automatisé** (docs/TEST-JEU.md) : 1 500 marches à graine fixe par campagne rejouées par le moteur,
  20 parties complètes comparées entre PC et téléphone, synchronisation avec messages perdus, interfaces dessinées.
- **Sons de Pilou** (docs/SONS.md) : dix sons 8 bits décrits dans `assets/sons.txt`, mêmes échantillons sur PC,
  téléphone et `outils/sons/sons.py` ; **normaux par défaut** (choix d'Antoine), réglables en aucun / discrets. Musiques et ambiances de l'Aventure : 4 boucles (prologue, humour, mystère, émotion) et 4 ambiances (vent, pluie, hall, mer), réglage « Musique » à part, « discrète » par défaut. Second lot : le thème de Pilou en trois versions (niveaux 10, 25, 40) et en motif court, une boucle calme et une de tension légère par ton, quatre motifs de fin ; choix par le champ facultatif « musique ».
- **Première minute et mode d'emploi** : au tout premier lancement, trois bulles de Pilou qui passent seules (il
  s'installe ; clic gauche, clic droit ; l'Aventure), jamais pendant la saisie, une seule fois ; sur Android, une ligne
  discrète sur l'Accueil, qui part à la première caresse. Page joueur [MODE-EMPLOI.md](MODE-EMPLOI.md), rangée comme
  le menu, liée du README et de *Réglages ▸ Mode d'emploi…*. Film : `docs/maquettes/premiere-minute/`.
- **Menu clic droit « Sept portes »** (Windows, docs/AUDIT-MENU.md) : 14 lignes stables au premier niveau au lieu de 39
  (sept portes par intention, un signe de forme chacune), une zone « En ce moment » de deux lignes au plus, titres de
  section, rond pour les choix exclusifs et carré pour les cases. Rien n'est perdu (table ancien → nouveau dans la PR).
  **Thème sombre par défaut sur PC** (bulle, menu, fenêtre d'invitation : un seul réglage ; un choix déjà enregistré
  est gardé). Vu au vrai clic droit sur le PC d'Antoine, clair et sombre, à 100 % ; 125 et 150 % en rendu WPF seulement
  (`--essai=menu[:porte][:clair|sombre][:moment][:joueur]`, planche `docs/maquettes/menu/captures/sept-portes.png`).

## En cours

- **Le théâtre des campagnes** (PR #95 fusionnée ; docs/SCENES.md) : la lecture de l'Aventure
  devient une scène vivante. Fait et testé : le moteur commun (référence Python, C#, Java, qui retombent sur les mêmes
  pixels), le mini-Pilou de scène (taille M), 13 acteurs et effets, les six scènes du prologue (acteurs et réactions aux
  clics) ; sur PC, la fenêtre en « Théâtre » (scène ×5, boîte de dialogue, choix sur la scène, travelling, départ en
  route, absence pendant l'attente), vue en essai sur le PC d'Antoine ; sur téléphone, la scène en haut de la lecture à
  une seule unité de pixel (k = largeur ÷ 192) pour décor, mini-Pilou, portrait et ciel de repli, bandeau au-dessus
  (captures Robolectric 1078 × 2400 relues). Le réglage « ✧ » décide désormais des animations (chez Antoine, Windows a
  « Afficher les animations » coupé : tout était figé). Jamais vu sur un vrai téléphone.
- **Progression et campagnes** (branche `claude/progression-campagnes`) : une campagne peut s'ouvrir par un haut fait
  ou une campagne finie, en plus du niveau (`"succes"`, `"campagnes"`, PC et Android, validateur) ; la Bibliothèque
  dit ce qui manque. L'aide du niveau en expédition se voit au départ et contre le boss. Testé (PC, CI) ; jamais vu
  sur un vrai téléphone.
- **Style pixel de l'Aventure** (PR #103 et #108) : sous la scène, cadres pixel (bord, coins en
  escalier, biseau, ombre, comme le menu « Sept portes ») et police pixel pour le récit, les choix, le bandeau et le lieu,
  sur PC et téléphone ; fil calé sur des bulles entières (plus de ligne tranchée). Captures téléphone sombre, clair,
  grande police et PC à 100 % relues ; jamais vu sur un vrai téléphone. Seconde passe (#108) : cartes, menu ⋯ et fil « Relire »
  au même style.
- **Théâtre de « La Grande Panne »** (branche `claude/theatre-grande-panne`) : 12 scènes avec leurs acteurs (paquets de
  données, curseur, tickets, bulles, étincelles), les 13 personnages en pied (repris de leurs portraits 1×, Mlle Renvoi
  derrière un guichet), qui entrent, parlent leurs répliques et sautillent quand on les touche ; moteur commun étendu
  (référence, C#, Java). Vu sur le PC d'Antoine (essai `personnage`) ; jamais sur un vrai téléphone.
- **Théâtre du « Phare éteint »** (branche `claude/theatre-phare-eteint`) : 14 scènes (mouettes, chat, papillons de
  nuit, crabes), les 7 humains dessinés en pied (`humains_pied.py`). Sur PC, le panneau des choix se pose du côté
  opposé au personnage, sans couvrir l'accessoire clé (`cle`), la légende ni les boutons ; le paquet volant du hall des
  Pas Comptés est retiré. Rendus PC (essai) et capture téléphone Robolectric relus ; jamais sur un vrai téléphone.
- **Théâtre de « Petit Nuage »** (branche `claude/theatre-petit-nuage`) : 14 scènes (petits nuages qui passent, brume,
  vapeur, flocons, aiguilles de mélèze, rafales, ronds dans l'eau), tout en trame, sans alpha lissé ; les 9 personnages
  en pied, les volants flottent au-dessus du sol. La musique du ton « émotion » et l'ambiance du décor sont visées dans
  ces scènes (trace pendant l'essai PC ; test par scène). Sur PC, un choix trop long passe à la ligne au lieu d'être
  coupé. Jamais sur un vrai téléphone ; le son lui-même n'a pas été écouté.
- **Scènes d'évolution** (branche `claude/scenes-evolution`, docs/SCENES.md) : trois scènes au fond du jardin (niveaux
  10, 25, 40), un choix « ce qu'il garde », variante câline ou espiègle dite dans la scène ; annoncées par une seule
  bulle, ouvertes seulement au clic ; Carnet « Ses évolutions » sur PC et téléphone ; script commun avec référence.
  Captures PC (essai) et téléphone (Robolectric) relues. Pas joué en vrai : l'annonce par bulle sur le PC (un essai
  écrirait dans le vrai profil), ni sur un vrai téléphone. Jardin des Ronces corrigé (pot, ronces, Brouillon en pied).
- La visite guidée (`outils/tourner-ecran-gauche.ps1`) joue aussi la pêche, la cuisine, l'Aventure (personnage,
  épreuve, fin), un petit mot, la complicité et le Journal.

## Ensuite

0. **Suite du théâtre** (docs/SCENES.md, « Ce qui reste ») : les chorégraphies des choix, puis les quatre liens avec
   le Pilou du bureau.
1. **Vidéo de promo** avec les campagnes : tourner sur le PC d'Antoine (`outils/tourner-ecran-gauche.ps1`, décor
   fictif), puis monter avec `outils/video/monter.py` (plan de montage `outils/video/montage.json`, voir
   [VIDEO.md](VIDEO.md)). L'outil n'a été essayé que sur l'ancien tournage (Pilou 0.9.45, sans pêche, cuisine,
   Aventure, mot ni complicité) : après le nouveau tournage, regarder la planche et ajuster sous-plages, durées et
   cadrages des scènes récentes, puis remplacer `docs/promo/`.
2. **Liste de contrôle manuelle de `TEST-JEU.md`** sur un vrai Windows et un vrai téléphone (fenêtre Aventure à 100, 125
   et 150 %, notification de retour en veille, jeu PC éteint puis allumé, décision au même choix sur deux appareils).
3. **Ajuster les seuils de complicité** après une semaine d'usage réel (PC et téléphone) : les paliers arrivent-ils trop
   vite ou trop lentement ? Relire aussi les mots et le journal sur cette semaine.

## Jamais vérifié sur un vrai appareil

- Sous Windows (liste passée le 27 novembre 2026, détail dans `TEST-JEU.md`) : vus et corrigés sur le PC d'Antoine, la
  fenêtre Aventure (taille minimale), la fenêtre des expéditions, le journal, la charge du dessin fin (≈ 5 % d'un cœur),
  la relance en pleine campagne, une fin versée une fois. Restent : un vrai écran à 125 % et 150 % (dont la police pixel de la bulle, vue à 100 % seulement), les épreuves jouées
  au clavier et à la souris, les extensions d'éditeur, les animations à l'œil.
- Sur téléphone : les métiers, la boutique garnie, la fluidité du dessin fin, l'onglet Aventure et la notification de retour.
- La présence au quotidien : la cadence d'une vraie journée, la fenêtre Journal sur de vraies pages, le mot du soir (notification, Doze), le
  widget et la bulle avec le mot, la synchronisation entre deux appareils réels.
- Les traits : la fenêtre « Pilou et moi » sur un Windows à 125 % ou 150 %, la carte sur un vrai téléphone, la naissance
  d'un trait au fil de vraies semaines et son annonce entre deux appareils ; les seuils sont une première estimation.
- Entre deux PC : le cumul des métiers et des succès, une visite entre amis.
- Les sons : écoutés par personne ; sur PC, seule la lecture du retour d'expédition a été vérifiée (Windows ouvre sa
  sortie audio) ; sur téléphone, aucune lecture réelle.
- Les musiques : écoutées par personne. Sur PC, la boucle du prologue joue dans l'exe d'essai (session audio active, crête
  mesurée vers -30 dBFS) et se coupe quand la fenêtre est réduite ; les autres boucles et le téléphone : jamais lus en vrai. Second lot : jamais lu dans l'exe.

## Points connus


- Lecture des notifications Windows : attend un paquet signé (voir `NOTIFICATIONS.md`).
- **Menu clic droit au clavier** : les flèches, Entrée et Échap vont à l'appli au premier plan, pas au menu (Pilou
  ne prend jamais le premier plan, règle 8). Souris seulement ; voir `AUDIT-MENU.md`.
- Deux écrans à des échelles différentes : Windows étire encore la fenêtre de Pilou sur le second.
- L'exe pèse 128 Mo (.NET embarqué) ; la compression le ramènerait vers 60–70 Mo, non faite.
- Lancer une expédition depuis le téléphone n'est pas possible (lecture seule, voir `EXPEDITIONS.md`) ; seule la
  campagne se lance des deux côtés.
- **Charge des animations non mesurée sur appareil** : décors à 4–5,5 images par seconde, portraits, écriture
  lettre à lettre et fond respirant tournent sous Robolectric et en tests, jamais sur un vrai téléphone ni un PC modeste
  (batterie, processeur). Le réglage « ✧ » (complètes, réduites, aucune) existe pour couper.
- **Captures Android des écrans animés relues le 27 novembre 2026** (artefact `captures-ui`, CI `main` 46076343814) :
  les 102 images `jeu-*` (4 campagnes × clair, sombre, grande police) et les 8 `aventure-personnage*`, une par une.
  Robolectric n'est pas un vrai téléphone : polices, densité et animations réelles restent à voir sur appareil. Les
  ~350 autres captures (accueil, boutique, collection…) n'ont pas été relues une par une. Rien de rouge / vert, aucun
  état porté par la seule couleur (fins : ★ ◐ ✧, jauges en carrés), sprites nets, aucune donnée personnelle.

  | Capture | Défaut | Gravité | Suite |
  |---|---|---|---|
  | Petit écran, scène avec portrait (`*-grande-panne-choix`, `*-phare-eteint-*`, `aventure-personnage*`) | Le portrait (96 dp) remonte jusqu'à la barre du haut et passe **devant** le bouton « ⋯ » et la fin du titre | Moyenne | Corrigé : la barre passe devant (`Lecture.java`) |
  | Même cas, titre long (« La nuit des six bateaux ») | Était coupé par le portrait ; il passe maintenant en entier devant lui (vérifié sur les captures de la PR) | Faible | Si le chevauchement gêne sur téléphone : portrait plus petit à 156 dp (choix de design) |
  | `*-grande-panne-*` chapitre 1 (« 13 h 37 ») | Le titre blanc se pose sur l'afficheur pixel « 1337 » du décor : deux textes superposés | Faible | Décor (`assets/`) ou titre décalé : à trancher |
  | Titres de chapitre sur décor clair (prologue, `petit-nuage` « Lâcher ») | Blanc + ombre sur ciel crème ou rose : lisible mais contraste faible | Faible | Proposé : voile sombre derrière le titre |
  | `jeu-petit-grandepolice-*` barre du bas | « Boutique » et « Collection » se touchent, sans espace | Moyenne | Corrigé le 28 novembre (guide de style) : les libellés prennent la plus grande taille qui tient dans leur case |
  | `jeu-petit-grandepolice-*` puce de lieu | Nom tronqué (« Au-dessus de l'Abr… », « Le Bigorneau Qui T… ») | Faible | Accepté (points de suspension), ou `maxWidth` plus large |
  | Toutes, en-tête | « Prochaine rangée : … (enc… » tronqué | Faible | Hors campagnes, à reformuler plus court |
  | `*-epreuve-jeu` | « ÉPREUVE » en police pixel : très petit, accent non visible | Faible | Proposé : police pixel ×2 pour ce titre |
  | `*-choix` | Dernière option coupée en bas, en fondu | — | Voulu (dock défilant), rien à faire |
