# Audit du menu clic droit (Windows)

Audit du 27 novembre 2026, sur le code de `main` (après #79 et #80). Aucun code modifié.
Constat d'Antoine : « le menu est très beau mais on s'y perd énormément avant de trouver ce qu'on veut ».

**En trois lignes**

- Le menu a **39 lignes au premier niveau** (jusqu'à 42 selon l'état), cinq séparateurs et aucun titre de section.
  Le style rétro n'est pas en cause : c'est l'architecture.
- Les gestes sont presque tous dans la règle 3 (deux ou trois). **Ce qui coûte, c'est la recherche des yeux** :
  jouer est à la 22ᵉ ligne, la discrétion en visio est rangée sous « Métiers et succès », le journal sous « Pilou et moi ».
- Recommandation : **la proposition A « Sept portes »** (14 lignes, regroupées par intention), complétée par **la
  ligne du moment** de la proposition C. Maquettes dans [`maquettes/menu/`](maquettes/menu/index.html).

Sommaire : [1. Relevé](#1-relevé) · [2. Diagnostic](#2-diagnostic) · [3. Propositions](#3-propositions) ·
[4. Recommandation](#4-recommandation) · [5. Questions pour Antoine](#5-questions-pour-antoine)

---

## 1. Relevé

### Méthode

- Arbre reconstruit depuis le code : `FenetrePilou.cs` (`Remplir`), puis chaque fonction appelée :
  `FenetreNiveaux.cs`, `PresenceCampagne.cs`, `FenetreSoins.cs`, `FenetrePresence.cs`, `JeuDefense.cs`, `Peche.cs`,
  `FenetreExpedition.cs`, `FenetreQuetes.cs`, `FenetreAmis.cs`, `FenetreIntegrations.cs`, `FenetreGroupe.cs`,
  `FenetreConnecteurs.cs`, `FenetreActivites.cs`, `FenetreGestes.cs`, `FenetreMise.cs`. Habillage : `MenuRetro.xaml`.
- **Pas de capture du menu ouvert.** L'exe d'essai a été construit et lancé avec un dossier de données jetable, mais
  l'accès au bureau (clic droit simulé) n'a pas été accordé à temps ; l'exe a été fermé. Juste après, un exe d'essai
  d'une autre session est apparu : je n'ai pas insisté. Tout ce qui suit vient du code.
- Le menu est **reconstruit à chaque ouverture** (`menu.Opened` → `Remplir`) : les libellés dynamiques ci-dessous sont
  ceux du moment de l'ouverture.

### Légende

`▸` sous-menu · `…` ouvre une fenêtre · `☐` case à cocher · `◉` choix exclusif · `ⓘ` ligne d'information grisée
(non cliquable) · `[si …]` entrée conditionnelle · `─` séparateur pointillé

### Arbre actuel

```
Clic droit sur Pilou (ou sur sa bulle)
│
├─  1  [Bandeau : niveau · barre d'XP · po]        clic → boutique (vitrine)
├─  2  🛒 Boutique  (ou « 🛒 Boutique (n nouveautés) »)                    clic → boutique
├─  3  ✉ Aventure… ▸  (« ✉ Aventure · en route… » / « · ! il t'attend »)
│        ├ Ouvrir l'aventure…  (« ✉ Lui répondre… » s'il attend)   → fenêtre Aventure (choix de campagne)
│        ├ ⓘ [si campagne en cours] ligne d'état
│        ├ ─
│        ├ Annonce de son retour ▸  ◉ Un petit saut et une bulle · ◉ Seulement le signe « ! »
│        ├ ⓘ Heures calmes (réglage des amis) : …
│        └ ⓘ Plein écran, présentation, visio : l'annonce attend
├─ ─
├─  4  ♥ Caresser
├─  5  ♥ Prendre soin de Pilou          (nourrit si faim < 80, lave si propreté < 80, câlin)
├─  6  Soins · tout va bien ▸  (ou « il a besoin de toi », « il boude ☁ (gains ×0,6) », « il rayonne ✧ »…)
│        ├ ⓘ résumé des jauges
│        ├ ♥ Prendre soin de Pilou                     (doublon de la ligne 5)
│        ├ ─
│        ├ ☐ Vacances (tout est figé)
│        └ ⓘ [si variantes] Variantes : …
├─  7  ♥ Pilou et moi ▸
│        ├ ⓘ Complicité : palier · n jours ensemble · jauge
│        ├ 📖 Journal de Pilou…                         → fenêtre Journal
│        ├ ─
│        ├ Pilou me parle ▸  ◉ Peu · ◉ Normalement · ◉ Jamais
│        ├ ☐ Tenir son journal (les faits du jour, rien de personnel)
│        ├ ☐ Petits gestes de complicité (signe, clin d'œil, sieste tardive)
│        ├ ─
│        ├ Lui dire comment je m'appelle…  /  Mon prénom pour Pilou : X — changer…
│        ├ [si prénom] Oublier mon prénom
│        └ ⓘ Le prénom reste entre tes appareils…
├─  8  Afficher Claude                                 → met la fenêtre Claude devant
├─ ─
├─  9  Taille ▸            ◉ Petit · ◉ Normal · ◉ Grand
├─ 10  ☐ Dessin fin        (infobulle : mesures du dessin)
├─ 11  Bulle ▸             ◉ Détaillée · ◉ Compacte (détail au survol) · ◉ Seulement quand on t'attend
├─ 12  Thème de la bulle ▸ ◉ Comme Windows · ◉ Clair · ◉ Sombre
├─ 13  Accessoire ▸        12 entrées ◉ (celles non possédées grisées « — boutique »)
├─ 14  Couleur ▸           ◉ Bleu ciel · ◉ couleurs possédées · ─ · D'autres couleurs à la boutique…
├─ 15  [si objet porté] Ce qu'il porte (n) ▸   ✕ Retirer : X … · ─ · ✕ Tout retirer
├─ 16  [si possédée] ☐ Traînée d'étoiles
├─ 17  Niveau n · xp/xp · titre ▸
│        ├ ⓘ [si niveau acquis gardé] Encore … xp
│        ├ ⓘ Prochain niveau : +n po
│        ├ ─
│        ├ ⓘ Jeux, puis ✓ / « niv n » pour chaque jeu
│        ├ ⓘ Évolution, puis ✓ / « niv n » pour chaque stade      (doublon partiel de la ligne 18)
│        ├ ⓘ Boutique : n/m articles dans les rangées ouvertes
│        ├ [si palier à venir] prochaine rangée → boutique
│        └ Titres ▸  ✓ / « niv n » pour chaque titre
├─ 18  Évolution · stade ▸
│        ├ [si retenue] Laisser Pilou évoluer / Ne plus retenir l'évolution
│        ├ ⓘ Pierres de calme : n
│        ├ ─
│        └ ⓘ Forme affichée, puis ◉ La plus grande atteinte · ◉ chaque stade atteint
├─ 19  ☐ Se promène
├─ 20  ☐ Suit la souris du regard
├─ 21  ☐ Petits jeux (de temps en temps)
├─ 22  Jouer ▸
│        ├ Petit jeu au hasard
│        ├ Défense du bureau   (ou « — niveau n »)
│        ├ ─
│        ├ Défense : largeur de la bande ▸  ◉ Tout l'écran · ◉ Deux tiers · ◉ Moitié
│        ├ ☐ Défense : réduire les flashs
│        └ ⓘ [si record] Record : …
├─ 23  Pêcher              (grisé « — niveau n » avant le niveau)
├─ 24  Cuisiner (n ingrédients) / Cuisiner (pêche d'abord)
├─ 25  Carnet de pêche — n/m ▸      une ligne par prise (grisée si jamais vue)
├─ 26  Livre de recettes — n/m · n plats inventés ▸   une ligne par recette, puis les plats inventés
├─ 27  ⚔ Partir en expédition… · ⚡ n ▸   (ou « ⚔ En expédition · retour vers 14 h 20 »)
│        en expédition : Voir l'expédition… · ↩ Rappeler Pilou
│        sinon : ⓘ état du jour · un lieu par ligne (⚡, durée, risque) · ─ · Équipement… ·
│                Donner un en-cas de route · [si dernier récit] Journal d'expédition…
├─ ─
├─ 28  Partager l'XP entre PC… (choisir un dossier)   /  XP partagée : <dossier>
├─ 29  ☐ Démarrer avec Windows
├─ 30  ☐ Icône près de l'horloge
├─ 31  Quêtes · n po · série n j ▸   ⓘ quêtes du jour, de la semaine, du mois · ⓘ coffre du jour
├─ 32  Amis…                                          → fenêtre Amis
├─ 33  [si parti en visite] Rappeler Pilou (parti chez X)
├─ 34  Intégrations ▸
│        ├ Codex : brancher / branché ✓ (débrancher)
│        ├ ─  Discord : statut… / ☐ statut · ☐ nom des sessions · changer d'application…
│        ├ ─  Me prévenir sur mon téléphone… (webhook) · [si actif] ☐ seulement loin du PC · envoyer un essai
│        ├ ─  Groupe d'appareils : revoir le code · Appareils du groupe (n) ▸ · Rejoindre… · nouveau code ·
│        │    Quitter le groupe     (hors groupe : Partager l'XP entre mes appareils… · Rejoindre un groupe…)
│        │    Relais du groupe : …
│        │    ⓘ [si téléphone] dernier envoi au téléphone : …
│        └ ─  Brancher un autre logiciel… (aide)
├─ 35  Connecteurs…                                   → fenêtre Connecteurs
├─ 36  Métiers et succès ▸
│        ├ ⓘ en ce moment : … (· caché (visio) …)
│        ├ ─  ⓘ un métier par ligne (grade, progrès)
│        ├ ─  Succès (n/m) ▸   une ligne par succès
│        └ Activités : réglages ▸
│             ├ ☐ Pilou regarde mes fenêtres (rien ne sort du PC)
│             ├ ☐ Se cacher en plein écran (jeu, vidéo)
│             ├ ☐ Se cacher en présentation
│             ├ ☐ Se cacher en visio (caméra ou micro)
│             ├ ─  ☐ une case par activité reconnue
│             └ ─  Ajouter mes logiciels… (activites.json)
├─ 37  Clavier, photo, notifications ▸
│        ├ ☐ Pilou tape avec moi au clavier…  ☐ Appareil photo à chaque capture  ☐ Notifications Windows dans la bulle
│        ├ ⓘ [si notifications] état : …
│        └ Notifications : réglages ▸
│             ├ Applis ▸  ◉ Toutes · ◉ Toutes sauf celles cochées · ◉ Seulement celles cochées
│             ├ ☐ une case par appli vue
│             ├ ─  ☐ Masquer le contenu · Paramètres Windows : Ne pas déranger… · Comment ça marche…
├─ 38  Version 0.9.n ▸     Chercher une mise à jour maintenant · ☐ Se mettre à jour tout seul
├─ ─
├─ 39  Se cacher 10 min
├─ 40  Redémarrer Pilou
└─ 41  Quitter (revient à la prochaine session)
```

Sans les trois entrées conditionnelles (15, 16, 33), il reste **38 lignes plus le bandeau**.

### Mesures

| Mesure | Valeur |
|---|---|
| Lignes au premier niveau | 38 + bandeau (jusqu'à 41 + bandeau) |
| Séparateurs au premier niveau | 5 ; le bloc le plus long (lignes 9 à 27) fait **19 lignes** sans coupure |
| Sous-menus au premier niveau | 22 |
| Profondeur maximale | 3 niveaux (Intégrations ▸ Appareils du groupe ▸ ; Clavier… ▸ Notifications : réglages ▸ Applis ▸ ; Métiers ▸ Activités : réglages ▸) |
| Plus large sous-menu | Activités : réglages (4 cases + une par activité + 1) ; Accessoire (12) |
| Lignes avec un repère visuel (♥ ✉ 🛒 ⚔ 📖) | 7 sur 38 |
| Lignes d'information grisées dans les sous-menus | une trentaine, mêlées aux actions |
| Raccourcis clavier (lettre soulignée) | aucun |
| Hauteur estimée du premier niveau | ≈ 980 px à 100 % (22 px par ligne, `MinHeight` de `MenuRetro.xaml`) ; ≈ 1 225 px à 125 % : **plus haut qu'un écran 1080p, le menu défile**. Confiance : 70 % (non mesuré à l'écran) |

### Ce que fait le clic gauche (pour comparer)

Clic sur Pilou : une caresse. S'il attend son aventure : ouvre la fenêtre Aventure. Pendant un jeu : joue.
Sur la pancarte de visite ou d'expédition : rappelle ou montre où il est. Le clic gauche est déjà le geste le plus
court ; le menu ne doit pas le doubler en haut de liste.

Le menu de l'icône près de l'horloge (`MenuNotification.cs`, 8 entrées) est une porte de secours ; il est hors de cet
audit mais reste cohérent avec toutes les propositions.

---

## 2. Diagnostic

### Gestes par tâche, aujourd'hui

Un **geste** = un clic (droit ou gauche) ou un survol qui ouvre un sous-menu. **Rang** = la ligne du premier niveau
qu'il faut trouver des yeux (sur 38).

| Tâche | Chemin | Gestes | Rang | Verdict |
|---|---|---|---|---|
| Caresser | clic gauche sur Pilou | 1 | — | bon |
| Soigner / nourrir | clic droit · ♥ Prendre soin | 2 | 5 | bon, mais trois lignes « ♥ » / « Soins » se suivent |
| Petit jeu | clic droit · Jouer ▸ · Petit jeu au hasard | 3 | 22 | hors règle, et loin |
| Pêcher | clic droit · Pêcher | 2 | 23 | bon geste, rang très bas |
| Défense du bureau | clic droit · Jouer ▸ · Défense | 3 | 22 | hors règle |
| Partir en expédition | clic droit · ⚔ Expédition ▸ · un lieu | 3 | 27 | hors règle |
| Lancer une campagne | clic droit · ✉ Aventure ▸ · Ouvrir l'aventure… · (choix dans la fenêtre) | 3 + 1 | 3 | « Aventure… » promet une fenêtre et ouvre un sous-menu |
| Voir le journal | clic droit · ♥ Pilou et moi ▸ · 📖 Journal… | 3 | 7 | introuvable sans le savoir |
| Ouvrir la boutique | clic droit · bandeau ou 🛒 | 2 | 1 | bon (deux portes) |
| Se cacher 10 min | clic droit · Se cacher 10 min | 2 | 39 | bon geste, au fond |
| Se cacher en visio (réglage) | clic droit · Métiers et succès ▸ · Activités : réglages ▸ · case | 4 | 36 | **le pire** : rangé sous un libellé qui n'a rien à voir |
| Bulle plus discrète | clic droit · Bulle ▸ · Seulement quand on t'attend | 3 | 11 | correct |
| Pilou parle moins | clic droit · ♥ Pilou et moi ▸ · Pilou me parle ▸ · Peu | 4 | 7 | hors règle |
| Changer d'accessoire | clic droit · Accessoire ▸ · un accessoire | 3 | 13 | correct (rare) |
| Quitter | clic droit · Quitter | 2 | 41 | bon geste, dernière ligne d'un menu qui défile |

Lecture : sur 15 tâches, **8 tiennent en deux gestes**, 5 en trois, 2 en quatre. Le compte de clics n'est pas le cœur
du problème. **Le cœur, c'est le rang** : les tâches de jeu sont entre la 22ᵉ et la 27ᵉ ligne, et la discrétion est
éparpillée.

### Les défauts, par famille

**Trop large.** 38 lignes, dont 22 sous-menus. Au-delà d'une dizaine de lignes sans titre, l'œil lit tout à chaque
fois au lieu de sauter à la bonne zone.

**Pas de zones.** Cinq séparateurs, aucun titre de section. Le bloc 9 → 27 mélange apparence (taille, couleur),
progression (niveau, évolution), comportement (se promène, suit la souris) et jeux (jouer, pêcher, expédition).

**Regroupements incohérents.**

| Ce qu'on cherche | Où c'est | Pourquoi on ne le trouve pas |
|---|---|---|
| Se cacher en plein écran, présentation, visio | Métiers et succès ▸ Activités : réglages ▸ | la discrétion sous un libellé de progression |
| Le journal de Pilou | ♥ Pilou et moi ▸ | aucune ligne ne dit « Journal » au premier niveau |
| Pilou me parle (fréquence) | ♥ Pilou et moi ▸ … ▸ | un réglage de discrétion à côté du prénom |
| Les quêtes | entre « Icône près de l'horloge » et « Amis… » | une entrée de jeu dans le bloc des réglages système |
| Les réglages de Défense | Jouer ▸ | des réglages mêlés aux actions de jeu |
| Notifications Windows | Clavier, photo, notifications ▸ | un libellé-inventaire, pas une intention |

**La discrétion est éparpillée en huit endroits** : Bulle ▸, Pilou et moi ▸ Pilou me parle ▸, Pilou et moi ▸ Petits
gestes, Aventure ▸ Annonce de son retour ▸, Métiers ▸ Activités : réglages ▸ (plein écran, présentation, visio),
Se promène, Petits jeux (de temps en temps), Se cacher 10 min. C'est pourtant ce qu'un nouveau joueur cherche en
premier (règle 3 : Pilou reste passif).

**Doublons.**

| Doublon | Lignes |
|---|---|
| ♥ Prendre soin de Pilou | 5 et Soins ▸ |
| Boutique | bandeau (1) et 🛒 (2) — voulu, mais deux lignes pour une porte |
| Partager l'XP | « Partager l'XP entre PC… (choisir un dossier) » (28) et Intégrations ▸ « Partager l'XP entre mes appareils… (nouveau code) » : **deux mécanismes, presque le même libellé** |
| Les stades d'évolution | Niveau ▸ (liste ✓) et Évolution ▸ |
| Les po | bandeau et en-tête « Quêtes · n po » |
| Rappeler Pilou | « Rappeler Pilou (parti chez X) » (33) et Expédition ▸ « ↩ Rappeler Pilou » |
| Journal | Pilou et moi ▸ Journal de Pilou… et Expédition ▸ Journal d'expédition… |

**Libellés ambigus.**

- « Soins · tout va bien » : un état écrit comme un titre ; on ne sait pas si c'est cliquable.
- « Aventure… » : les points de suspension annoncent une fenêtre, l'entrée ouvre un sous-menu.
- « Intégrations » et « Connecteurs… » : voisins, et rien ne dit la différence.
- « Clavier, photo, notifications » et « Métiers et succès » : des inventaires, pas des intentions.
- « Afficher Claude » : à quoi ça sert dans le menu d'un compagnon, sans contexte.
- « Quitter (revient à la prochaine session) » : rassurant, mais long ; la parenthèse irait mieux en infobulle.

**Entrées rares placées haut, fréquentes placées bas.** « Afficher Claude » (rare) est dans le premier bloc ;
Taille, Dessin fin, Thème de la bulle (réglés une fois) occupent les lignes 9 à 12. Jouer, Pêcher, Expédition (tous
les jours) sont aux lignes 22 à 27.

**Les lignes bougent.** Trois entrées conditionnelles (Ce qu'il porte, Traînée, Rappeler) et des libellés qui changent
de longueur (« Soins · il se laisse amadouer ☁ (gains ×0,6) », « ⚔ En expédition · retour vers 14 h 20 ») décalent tout
ce qui suit. La mémoire du geste (« c'est à peu près là ») ne s'installe pas.

**Peu de repères.** 7 lignes sur 38 ont un signe. Pourtant le gabarit a déjà une place prévue pour une icône
(`ContentSource="Icon"` dans `MenuRetro.xaml`), inutilisée. Pas de lettre soulignée pour le clavier.

**Information et action mêlées.** Une trentaine de lignes grisées (ⓘ) dans les sous-menus. En gris, une information
ressemble à une action désactivée. Pour un œil deutéranope, le gris éteint (`#7d8796` sur `#151a2e`) n'est séparé de
l'actif que par la luminosité.

---

## 3. Propositions

Trois réorganisations distinctes. Toutes gardent le gabarit rétro (cadre double biseauté, Consolas, pointillés,
curseur ► en pixels, coche ✓ en pixels, survol orange de nuit et bleu de jour). Toutes ajoutent deux repères :

- **un signe de forme en tête de chaque porte** (♥ ✉ ⚔ ► 🛒 📖 ◐ ◌ ★ ⇄ ⚙), dans la colonne d'icône déjà prévue ;
- **des titres de section** à la place des séparateurs nus, et les choix courts (◉) **à plat sous un titre** plutôt
  que dans un sous-menu de plus.

Les entrées non nommées dans les arbres gardent leur contenu actuel ; seul leur rangement change.

### A — « Sept portes » : un premier niveau court, par intention

```
[Bandeau : niveau · XP · po]                       → boutique
 ── la ligne du moment (voir C), seulement si besoin ──
♥  Prendre soin                                     (état en clair : « il a faim », « tout va bien »)
✉  Aventure…                                        → fenêtre Aventure, directement
⚔  Expédition ▸                                     lieux · équipement… · en-cas · journal d'expédition…
►  Jouer ▸        Petit jeu au hasard · Défense du bureau · Pêcher · Cuisiner
                  ── Carnets ── Carnet de pêche ▸ · Livre de recettes ▸ · ⓘ record de Défense
🛒 Boutique
📖 Journal…                                         → fenêtre Journal
 ── ── ──
◐  Apparence ▸    Accessoire ▸ · Couleur ▸ · Ce qu'il porte ▸ · ☐ Traînée d'étoiles · Forme affichée ▸
                  ── Taille ── ◉ Petit ◉ Normal ◉ Grand   ☐ Dessin fin
◌  Discrétion ▸   ── Bulle ── ◉ Détaillée ◉ Compacte ◉ Seulement quand on t'attend
                  ── Il me parle ── ◉ Peu ◉ Normalement ◉ Jamais
                  ── Se cacher ── ☐ en plein écran ☐ en présentation ☐ en visio
                  ── Il bouge ── ☐ Se promène ☐ Suit la souris ☐ Petits jeux ☐ Petits gestes de complicité
                  ── Retour d'aventure ── ◉ saut et bulle ◉ signe « ! »
                  ☐ Vacances (tout est figé)
★  Progrès ▸      Niveau et titres ▸ · Évolution ▸ · Quêtes ▸ · Métiers ▸ · Succès ▸ · ⓘ complicité
⇄  Amis et appareils ▸   Amis… · Groupe d'appareils ▸ · Connecteurs… · Intégrations ▸ · Notifications Windows ▸
⚙  Réglages ▸     Mon prénom… · ☐ Tenir son journal · Activités observées ▸ · ☐ Clavier · ☐ Photo
                  · Thème de la bulle ▸ · ☐ Démarrer avec Windows · ☐ Icône près de l'horloge
                  · Partager l'XP par dossier… · Afficher Claude · Version ▸ · Redémarrer Pilou
 ── ── ──
◌  Se cacher 10 min
   Quitter
```

- **14 lignes** au premier niveau (bandeau compris), contre 39. Profondeur maximale : 3 (Amis et appareils ▸ Groupe ▸
  Appareils ▸), comme aujourd'hui, mais sur une entrée rare.
- Chaque porte répond à une question : *je m'en occupe, je pars, je joue, j'achète, je relis, je le règle*.
- Les deux « Partager l'XP » sont rapprochés (dossier dans Réglages, code dans Groupe) et renommés pour dire leur
  mécanisme. « Prendre soin » n'existe plus qu'une fois ; l'état des soins devient son sous-titre.
- Aventure s'ouvre en un clic ; son réglage d'annonce part dans Discrétion.
- Coût : Pêcher passe de 2 à 3 gestes (il entre dans Jouer). Changer d'accessoire passe de 3 à 4.

Maquette : [`maquettes/menu/a-sept-portes.html`](maquettes/menu/a-sept-portes.html)

### B — « Rangée de raccourcis » : les cinq actions du jour en une ligne d'icônes

```
[Bandeau : niveau · XP · po]
[ ♥ Soin ]  [ ✉ Aventure ]  [ ► Jeu ]  [ ⚔ Expé ]  [ 📖 Journal ]     ← une seule ligne, cinq cases cliquables
 ── ── ──
►  Jouer ▸           Défense du bureau · Pêcher · Cuisiner · Carnets ▸
⚔  Expédition ▸      (comme aujourd'hui)
🛒 Boutique
◌  Discrétion ▸      (comme en A)
◐  Apparence ▸       (comme en A)
⋯  Tout le reste ▸   Progrès ▸ · Amis et appareils ▸ · Réglages ▸
 ── ── ──
   Quitter
```

- **9 lignes** dont une rangée de cinq cases. La case ► lance un petit jeu au hasard ; la case ⚔ ouvre la fenêtre
  Expéditions.
- Le plus rapide pour les tâches du quotidien : soin, aventure, jeu, journal en **deux gestes**, sans lire.
- Risques : une rangée de boutons dans un `ContextMenu` WPF est un contrôle sur mesure (comme le bandeau, qui en est déjà
  un). Le survol au clavier et la fermeture au clic sont à refaire à la main. Une case sans texte se devine mal la
  première semaine : il faut l'infobulle. « Tout le reste » redevient un tiroir où l'on se perd. Faisabilité :
  Confiance 70 %.

Maquette : [`maquettes/menu/b-raccourcis.html`](maquettes/menu/b-raccourcis.html)

### C — « Le menu du moment » : il s'adapte à ce que vit Pilou

```
[Bandeau : niveau · XP · po]
 ── En ce moment ──                                ← zone de 0 à 2 lignes, toujours à cette place
   ✉  Lui répondre…                [s'il attend après une aventure]
   ⚔  Voir l'expédition · ↩ rappeler [s'il est en expédition]
   ↩  Rappeler Pilou de chez X     [s'il est en visite]
   ♥  Prendre soin · il a faim     [si une jauge est basse]
   ■  Arrêter le jeu               [si un jeu est en cours]
 ── Toujours là ──
♥  Prendre soin
✉  Aventure…
►  Jouer ▸          (hasard, Défense, Pêcher, Cuisiner, Expédition ▸, Carnets ▸)
🛒 Boutique
📖 Journal…
◌  Discrétion ▸
⋯  Plus ▸           Apparence ▸ · Progrès ▸ · Amis et appareils ▸ · Réglages ▸
 ── ── ──
   Quitter
```

- **10 lignes** stables plus 0 à 2 lignes du moment. L'urgence du moment est la première ligne sous le bandeau.
- Risque : un menu qui change déroute. Garde-fou : la zone du moment a **une place fixe et au plus deux lignes** ;
  tout ce qui est en dessous ne bouge jamais.
- Expédition passe dans Jouer : partir coûte 4 gestes (contre 3), mais la suivre ou rappeler Pilou en coûte 2.

Maquette : [`maquettes/menu/c-moment.html`](maquettes/menu/c-moment.html)

### Gestes par tâche, avant / après

Gestes = clics + survols de sous-menu. Entre parenthèses : le rang à trouver des yeux au premier niveau.

| Tâche | Avant | A | B | C |
|---|---|---|---|---|
| Caresser | 1 (clic gauche) | 1 | 1 | 1 |
| Soigner / nourrir | 2 (5ᵉ) | 2 (2ᵉ) | 2 (case ♥) | 2 (1ʳᵉ si besoin, sinon 2ᵉ) |
| Petit jeu | 3 (22ᵉ) | 3 (5ᵉ) | **2** (case ►) | 3 (4ᵉ) |
| Pêcher | **2** (23ᵉ) | 3 (5ᵉ) | 3 (3ᵉ) | 3 (4ᵉ) |
| Défense du bureau | 3 (22ᵉ) | 3 (5ᵉ) | 3 (3ᵉ) | 3 (4ᵉ) |
| Partir en expédition | 3 (27ᵉ) | 3 (4ᵉ) | 3 (case ⚔ puis la fenêtre) | 4 (4ᵉ) |
| Suivre / rappeler l'expédition | 3 (27ᵉ) | 3 (4ᵉ) | 3 | **2** (zone du moment) |
| Lancer une campagne | 3 + choix (3ᵉ) | **2** + choix (3ᵉ) | **2** + choix | **2** + choix |
| Répondre après une aventure | 1 (clic gauche) | 1 | 1 | 1 (ou 2 par le menu, 1ʳᵉ ligne) |
| Voir le journal | 3 (7ᵉ, caché) | **2** (7ᵉ) | **2** (case 📖) | **2** (6ᵉ) |
| Ouvrir la boutique | 2 (1ʳᵉ) | 2 | 2 | 2 |
| Se cacher 10 min | 2 (39ᵉ) | 2 (13ᵉ) | 3 (Discrétion ▸) | 3 (Discrétion ▸) |
| Se cacher en visio | 4 (36ᵉ, caché) | **3** (9ᵉ) | **3** | **3** |
| Bulle plus discrète | 3 (11ᵉ) | 3 (9ᵉ) | 3 | 3 |
| Pilou parle moins | 4 (7ᵉ, caché) | **3** (9ᵉ) | **3** | **3** |
| Changer d'accessoire | 3 (13ᵉ) | 4 (8ᵉ) | 4 | 5 (Plus ▸ Apparence ▸) |
| Quitter | 2 (41ᵉ) | 2 (14ᵉ) | 2 (9ᵉ) | 2 (10ᵉ) |
| **Lignes au premier niveau** | **39** | **14** | **9** (dont 5 cases) | **10 + 0 à 2** |

Ce que ça dit :

- Les trois propositions divisent par trois à quatre la longueur du premier niveau. C'est le gain principal.
- B est la plus rapide sur le quotidien, mais la plus chère à coder et la moins lisible au premier usage.
- C est la meilleure quand quelque chose se passe, la plus longue pour l'apparence.
- A n'a que deux reculs (Pêcher, Accessoire : +1 geste chacun) et aucun risque technique : ce ne sont que des
  `MenuItem` rangés autrement.

### Maquettes

Pages HTML statiques, sans script : le survol ouvre les sous-menus en CSS, comme le menu WPF. Chaque page a le thème
nuit et le thème jour (case en haut). Couleurs reprises de `MenuRetro.cs` et `Bandeau.cs` : nuit `#151a2e`, cadre
violet `#6a5acd`, survol orange `#f69d50`, coche bleue `#6cb6ff` ; jour crème `#fbf3e4`, survol bleu `#1f5fae`,
pointillés orange `#c86a1c`. Aucun rouge, aucun vert ; chaque état porte un signe (►, ✓, ◉, ☐, ⓘ, ▸).

- [`maquettes/menu/index.html`](maquettes/menu/index.html) : les quatre côte à côte
- [`avant.html`](maquettes/menu/avant.html) · [`a-sept-portes.html`](maquettes/menu/a-sept-portes.html) ·
  [`b-raccourcis.html`](maquettes/menu/b-raccourcis.html) · [`c-moment.html`](maquettes/menu/c-moment.html)

Les maquettes montrent l'organisation, pas un rendu au pixel : la police et les espacements suivent `MenuRetro.xaml`
à peu près, sans être une capture.

---

## 4. Recommandation

**A « Sept portes », avec la zone « En ce moment » de C.** Confiance : 75 %.

Pourquoi :

- A règle ce qu'Antoine décrit (« on s'y perd ») : 14 lignes regroupées par intention, avec un signe et un titre.
- La zone du moment de C apporte le seul gain que A n'a pas (suivre une expédition, rappeler, répondre), sur une place
  fixe de deux lignes au plus. Elle remplace les entrées conditionnelles qui, aujourd'hui, font bouger le menu.
- B garde une bonne idée (les cases), mais coûte un contrôle sur mesure et un apprentissage. À revoir plus tard si
  A ne suffit pas.
- A + C ne touche que la construction du menu (`Remplir` et les fonctions `Menu…`) et un peu le gabarit
  (`MenuRetro.xaml` : titres de section, colonne d'icône). Aucune donnée, aucun réglage ne change de nom :
  `reglages.json` reste compatible.

Ordre de mise en œuvre suggéré (chantier séparé, lancé par le pilote après le choix d'Antoine) :

1. Titres de section et signes dans la colonne d'icône (`MenuRetro.xaml`).
2. Rangement en portes ; suppression des doublons ; libellés renommés.
3. Zone « En ce moment ».
4. Test sur le PC à 100, 125 et 150 % : le premier niveau ne défile plus ; captures dans `docs/`.
5. Android : vérifier si le menu de la bulle a le même défaut (hors de cet audit).

---

## 5. Réponses d'Antoine (27 novembre 2026)

| # | Question | Réponse |
|---|---|---|
| 1 | Quelle proposition : A + zone du moment, A seule, B ou C ? | **A + zone « En ce moment »** (la recommandation) |
| 2 | Pêcher et Cuisiner dans Jouer (+1 geste) ? | **Oui** : ils entrent dans Jouer ▸ |
| 3 | Deux portes vers la boutique ou une seule ? | **Une seule.** Laquelle garder (bandeau ou ligne 🛒) reste à confirmer ; à défaut, le bandeau, qui montre déjà les po |
| 4 | « Afficher Claude » ? | **Retiré du menu** |
| 5 | Partage d'XP par dossier ? | **Retiré du menu principal** ; il vit seulement dans Réglages ▸ |
| 6 | Discrétion : un long sous-menu ou deux ? | **Deux sous-menus** : « Il se montre » (bulle, il me parle, il bouge, retour d'aventure) et « Il se cache » (se cacher 10 min, plein écran, présentation, visio, vacances) |

### Le menu retenu

A, avec la zone « En ce moment » de C et les réponses 2 à 6. C'est la cible du chantier d'implémentation.
Maquette : [`maquettes/menu/retenu.html`](maquettes/menu/retenu.html).

```
[Bandeau : niveau · XP · po]                        → boutique (seule porte ; les nouveautés de la boutique restent à y afficher)
 ── En ce moment ──   0 à 2 lignes, place fixe, seulement si quelque chose se passe :
   ✉ Il t'attend : lui répondre…   ⚔ En expédition · voir / rappeler   ↩ Rappeler Pilou de chez X
   ♥ Prendre soin · il a faim      ■ Arrêter le jeu
 ── Toujours là ──
♥  Prendre soin                                      (état en clair : « tout va bien », « il a faim »)
✉  Aventure…                                         → fenêtre Aventure, directement
⚔  Expédition ▸                                      lieux · équipement… · en-cas · journal d'expédition…
►  Jouer ▸         Petit jeu au hasard · Défense du bureau · Pêcher · Cuisiner
                   ── Carnets ── Carnet de pêche ▸ · Livre de recettes ▸ · ── Réglages de Défense ▸
📖 Journal…                                          → fenêtre Journal
 ── ── ──
◐  Apparence ▸     Accessoire ▸ · Couleur ▸ · Ce qu'il porte ▸ · ☐ Traînée · Forme affichée ▸ · Taille · ☐ Dessin fin
◌  Il se montre ▸  ── Bulle ── · ── Il me parle ── · ── Il bouge ── · ── Retour d'aventure ──
◌  Il se cache ▸   ☐ en plein écran · ☐ en présentation · ☐ en visio · ☐ Vacances (tout est figé)
★  Progrès ▸       Niveau et titres ▸ · Évolution ▸ · Quêtes ▸ · Métiers ▸ · Succès ▸ · ⓘ complicité
⇄  Amis et appareils ▸   Amis… · Groupe d'appareils ▸ · Connecteurs… · Intégrations ▸ · Notifications Windows ▸
⚙  Réglages ▸      Mon prénom… · ☐ Tenir son journal · Activités observées ▸ · ☐ Clavier · ☐ Photo
                   · Thème de la bulle ▸ · ☐ Démarrer avec Windows · ☐ Icône près de l'horloge
                   · Partager l'XP par un dossier… · Version ▸ · Redémarrer Pilou
 ── ── ──
◌  Se cacher 10 min
   Quitter
```

- 14 lignes stables (bandeau compris), plus 0 à 2 lignes du moment.
- Retirés : la ligne 🛒 (le bandeau est la porte), « Afficher Claude », les entrées conditionnelles qui faisaient bouger
  le menu (elles passent dans la zone du moment).
- Les gestes du tableau de la section 3 (colonne A) restent valables, sauf : suivre ou rappeler l'expédition passe
  de 3 à 2 (zone du moment) ; rappeler Pilou d'une visite reste à 2 ; régler la discrétion reste à 3.
- À confirmer pendant l'implémentation : le bandeau doit avoir l'air cliquable (infobulle « Ouvrir la boutique »
  déjà là ; un survol visible le dira mieux).
