# État du travail

À mettre à jour à la fin de chaque session : ce qui est fait, ce qui est en cours, ce qui attend.
Dernière mise à jour : 27 novembre 2026.

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
- **Test de jeu automatisé** (docs/TEST-JEU.md) : 1 500 marches à graine fixe par campagne rejouées par le moteur,
  20 parties complètes comparées entre PC et téléphone, synchronisation avec messages perdus, interfaces dessinées.
- **Sons de Pilou** (docs/SONS.md) : dix sons 8 bits décrits dans `assets/sons.txt`, mêmes échantillons sur PC,
  téléphone et `outils/sons/sons.py` ; **coupés par défaut** (« Sons : aucun »), en attendant le choix d'Antoine.

## En cours

Aucune branche : tout est fusionné dans `main`. La visite guidée (`outils/tourner-ecran-gauche.ps1`) joue aussi la
pêche, la cuisine, l'Aventure (personnage, épreuve, fin), un petit mot, la complicité et le Journal.

## Ensuite

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

- Sous Windows : le dessin fin sur le bureau (charge, netteté à 125 % et 150 %), les extensions d'éditeur, la fenêtre des
  expéditions, la fenêtre Aventure et ses animations.
- Sur téléphone : les métiers, la boutique garnie, la fluidité du dessin fin, l'onglet Aventure et la notification de retour.
- La présence au quotidien : la cadence d'une vraie journée, la fenêtre Journal, le mot du soir (notification, Doze), le
  widget et la bulle avec le mot, la synchronisation entre deux appareils réels.
- Entre deux PC : le cumul des métiers et des succès, une visite entre amis.
- Les sons : écoutés par personne ; sur PC, seule la lecture du retour d'expédition a été vérifiée (Windows ouvre sa
  sortie audio) ; sur téléphone, aucune lecture réelle.

## Points connus

- Lecture des notifications Windows : attend un paquet signé (voir `NOTIFICATIONS.md`).
- Deux écrans à des échelles différentes : Windows étire encore la fenêtre de Pilou sur le second.
- L'exe pèse 128 Mo (.NET embarqué) ; la compression le ramènerait vers 60–70 Mo, non faite.
- Lancer une expédition depuis le téléphone n'est pas possible (lecture seule, voir `EXPEDITIONS.md`) ; seule la
  campagne se lance des deux côtés.
- **Divergence de campagne entre appareils partiellement détectée** : quand deux appareils décident chacun de leur côté au
  même choix, la base la plus avancée l'emporte, mais `Campagnes.Diverge` ne compare que si le rejeu de l'appareil perdant
  passe par la même étape ; s'il est encore en retard, il n'y a rien à comparer et le fil de ses messages n'est pas
  remis à zéro par cette comparaison (la base, elle, converge). Non couvert par les vecteurs.
- **Charge des animations non mesurée sur appareil** : décors à 4–5,5 images par seconde, portraits, écriture
  lettre à lettre et fond respirant tournent sous Robolectric et en tests, jamais sur un vrai téléphone ni un PC modeste
  (batterie, processeur). Le réglage « ✧ » (complètes, réduites, aucune) existe pour couper.
- **Captures Android des écrans animés non regardées** : `CapturesCampagnesTest` produit les images `jeu-*` et
  `aventure-personnage*` dans l'artefact `captures-ui` de la CI, mais personne ne les a encore relues à l'œil.
