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
- **Dessin fin 2× sur les 589 sprites** : plus aucun n'est agrandi automatiquement (`python3 outils/sprites/fin.py` :
  « Encore agrandis automatiquement : 0 »).
- **Présence de Pilou** (docs/PRESENCE.md) : petits mots (banque de 573), cadence (3 par jour sur PC, 1 le soir sur
  téléphone), complicité, journal identique des deux côtés, prénom, « Pilou et moi ».
- **Police pixel de Pilou** (docs/POLICE.md) : 223 glyphes dessinés à la main, tout le français, quatre tailles (texte,
  titre, et leur dessin fin), mise en page identique PC / Android. Première vague : la phrase de Pilou en tête de bulle
  (PC), le mot du jour dans la bulle flottante, l'Accueil et le widget (Android). Le reste des fenêtres reste en police
  système (chantier suivant).
- **Vie du personnage** (docs/SPRITES.md) : sauts en arc avec ressorts, antenne en retard, ombre tramée en l'air,
  poussière en marchant et à l'atterrissage, lumière du moment ; réglage « ✧ » respecté, « aucune » = mouvements
  d'avant. Vu dans l'exe d'essai sur le PC d'Antoine (`--essai=vie`), processeur inchangé (≈ 6 % d'un cœur avant
  comme après) ; jamais vu sur un vrai téléphone.
- **Test de jeu automatisé** (docs/TEST-JEU.md) : 1 500 marches à graine fixe par campagne rejouées par le moteur,
  20 parties complètes comparées entre PC et téléphone, synchronisation avec messages perdus, interfaces dessinées.
- **Sons de Pilou** (docs/SONS.md) : dix sons 8 bits décrits dans `assets/sons.txt`, mêmes échantillons sur PC,
  téléphone et `outils/sons/sons.py` ; **normaux par défaut** (choix d'Antoine), réglables en aucun / discrets.

## En cours

- **Le théâtre des campagnes** (branche `claude/campaign-animations-pixel-art-66992c`, docs/SCENES.md) : la lecture de
  l'Aventure devient une scène vivante. Fait et testé : le moteur commun (référence Python, C#, Java, 3 tests de chaque
  côté qui retombent sur les mêmes pixels), le mini-Pilou de scène (taille M, une quarantaine d'images), 13 acteurs et
  effets, les six scènes du prologue (acteurs et réactions aux clics), la fenêtre PC en « Théâtre » (scène ×5, boîte
  de dialogue, choix sur la scène, travelling, départ en route, absence pendant l'attente), vue dans l'essai
  `campagne:lecture` / `attente` / `personnage` sur le PC d'Antoine. Le réglage « ✧ » décide désormais des animations
  (chez Antoine, Windows a « Afficher les animations » coupé : tout était figé). Sur téléphone, même scène en haut de la lecture, à une seule unité de pixel (k = largeur ÷ 192) pour décor, mini-Pilou, portrait et ciel de repli ; captures Robolectric 1080 × 2400 relues.
- La visite guidée (`outils/tourner-ecran-gauche.ps1`) joue aussi la pêche, la cuisine, l'Aventure (personnage,
  épreuve, fin), un petit mot, la complicité et le Journal.

## Ensuite

0. **Suite du théâtre** (docs/SCENES.md, « Ce qui reste ») : scènes et acteurs des trois grandes campagnes, les 29
   personnages en pied, les chorégraphies des choix, puis les quatre liens avec le Pilou du bureau.
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
- Entre deux PC : le cumul des métiers et des succès, une visite entre amis.
- Les sons : écoutés par personne ; sur PC, seule la lecture du retour d'expédition a été vérifiée (Windows ouvre sa
  sortie audio) ; sur téléphone, aucune lecture réelle.

## Points connus

- `PresenceTests.Vecteurs_partages_avec_le_telephone` échoue sur le PC d'Antoine, déjà sur `main` (28 novembre) : un
  écart d'une heure pile entre l'heure locale et l'époque, donc une question de fuseau ; la CI ne le voit pas.

- Lecture des notifications Windows : attend un paquet signé (voir `NOTIFICATIONS.md`).
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
  | `jeu-petit-grandepolice-*` barre du bas | « Boutique » et « Collection » se touchent, sans espace | Moyenne | Proposé : libellés réduits ou sur deux lignes en grande police (`Principale`) |
  | `jeu-petit-grandepolice-*` puce de lieu | Nom tronqué (« Au-dessus de l'Abr… », « Le Bigorneau Qui T… ») | Faible | Accepté (points de suspension), ou `maxWidth` plus large |
  | Toutes, en-tête | « Prochaine rangée : … (enc… » tronqué | Faible | Hors campagnes, à reformuler plus court |
  | `*-epreuve-jeu` | « ÉPREUVE » en police pixel : très petit, accent non visible | Faible | Proposé : police pixel ×2 pour ce titre |
  | `*-choix` | Dernière option coupée en bas, en fondu | — | Voulu (dock défilant), rien à faire |
