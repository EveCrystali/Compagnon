# Pilou sur Android

Un petit compagnon qui vit en bas de ton écran : sur le téléphone, tu retrouves le Pilou de ton PC,
qui mène sa petite vie sans te déranger (il joue, mange, pêche, cuisine) et grandit pendant que tu
travailles. Tu y joues à ses mini-jeux, suis ses quêtes, ses hauts faits et ses expéditions, et le
personnalises dans la boutique ; tout cela est optionnel, et la progression est partagée avec le PC.

Et au passage, s'il est branché à tes applis sur le PC, il te prévient : quelles sessions Claude et
Codex travaillent, lesquelles ont fini, lesquelles t'attendent, et les nouvelles des connecteurs.
L'app ne fait tourner aucune IA : elle écoute le PC.

## L'app

Une barre de navigation en bas, cinq onglets — **Accueil · Aventure · Jouer · Boutique · Collection** — (thème
clair ou sombre selon le téléphone), et en haut un **bandeau permanent** : pastille de niveau, mini barre d'XP
pixel, pièces d'or (une pièce qui tourne), titre et prochaine rangée de la boutique ; un toucher ouvre
Collection → Niveaux. La **roue** à droite du bandeau ouvre les Réglages (un second toucher, ou retour, revient à
l'onglet d'avant). Pastille « ! » orange sur Aventure quand Pilou est revenu et attend, sur Boutique quand une
rangée s'ouvre. Transitions courtes (fondu et glissement de 18 dp dans le sens de la navigation), figées si le
téléphone supprime les animations.

| Onglet | Ce qu'on y trouve |
|---|---|
| **Accueil** | Pilou en grand en dessin fin (le toucher le caresse, devant son décor s'il en porte un ; en tenue de voyage, avec « ⟶ en route · retour vers 15 h 40 » sous lui, quand il est parti en aventure), niveau, titre et barre d'XP, état du PC (« ● en ligne » / « ◌ le PC dort »). Puis la carte **Aventure** en tête quand une campagne est en cours (sa scène, Pilou qui marche, le compte à rebours ; ou « ● Il t'attend ! »), l'expédition du PC, la météo, **les quêtes** (◔ ◑ ●), les sessions (❗ ? ◐ ✓ ■ ✕), la **Vitrine**, **Métiers et succès**. Le reste (nouvelles des connecteurs, appareils et amis du groupe, mot du jour) est replié derrière « Nouvelles, groupe, mot du jour ▾ » (le choix est gardé). Pas encore appairé : qui est Pilou, puis un guide en trois étapes. |
| **Aventure** | Les campagnes : Pilou t'écrit, tu choisis, il part pour de vrai (voir plus bas). |
| **Boutique** | Boutique rétro : enseigne néon, cabine d'essayage (décor, Pilou qui porte l'objet ; *Essayer / Acheter / Porter*), onglets par rayon, étagères par rangée de niveau (cadenas + « NIV 15 » et silhouette tant que la rangée est fermée, « RANGÉE DÉBLOQUÉE ! » qui clignote), vitrine (offres du jour, nouveautés, prochaine rangée, à ta portée). Pastille « ! » sur l'onglet quand il y a du nouveau. |
| **Jouer** | **Chasse aux bugs** en vedette (aperçu animé, record), puis les cartes de l'atelier : pêche, cuisine, étoile filante, bulles, tape m'en cinq. Un jeu pas encore ouvert montre « ◇ niveau N ». |
| **Collection** | Carnet de pêche (grille des 23 prises, cadre de rareté), livre de recettes, **Niveaux** (ce que chaque niveau ouvre : jeux, évolutions, titres, et la **prochaine rangée** de la boutique avec « Voir en boutique »), style (ce qu'on possède), **Métiers** (métiers et succès du PC, voir plus bas). |
| **Réglages** (roue du bandeau) | Appairage, Pilou flottant (taille, cacher, ramener), notifications (dont « Retours de Pilou (aventures) »), soins, jeux (sons, vibrations), mises à jour, diagnostic (journal de plantage, copier le diagnostic), à propos. |

### Aventure : les campagnes

Le contrat (format, moteur, synchronisation) est `docs/CAMPAGNES.md` ; le moteur est `Campagnes.java`, la façade du
téléphone `CampagnesTel.java`. Les campagnes se lisent hors du fil d'interface au lancement (`CampagnesTel.precharger`),
l'onglet montre « Pilou déplie ses cartes… » le temps qu'il faut.

- **La liste** : la campagne en cours d'abord (sa scène avec Pilou, « ● Il t'attend ! » ou le compte à rebours et
  l'heure de retour), puis une carte par campagne, le prologue en premier : bande de décor aux couleurs du ton et
  signe de forme (☼ drôle, ◆ mystère, ♥ émotion, ▲ épique), titre, accroche, durée, chapitres, niveau requis
  (« ◇ Niveau 8 requis » et ce qu'il manque), progression d'une partie mise de côté (chapitre, lieu de reprise,
  barre), fins obtenues (« Fins 1 / 6 ★ ◐ ? ? ? ? »), et **Commencer**, **Reprendre** / **Recommencer** (avec
  confirmation) ou **Rejouer**. Une seule aventure à la fois : les autres boutons attendent, et le disent. Les po et
  l'xp gagnés que nul PC n'a encore versés sont rappelés en haut (« … attendent ton PC »).
- **La lecture**, en conversation : en haut la **scène** (le décor `decor-<campagne>-<décor>` de la banque de sprites,
  dessiné net à l'échelle entière et posé au sol ; à défaut un ciel pixel en dégradé tramé aux couleurs du ton, des
  collines tirées du nom du lieu, soleil, lune ou étoiles qui scintillent), Pilou en dessin fin qui prend l'**humeur**
  de chaque message (il cligne, respire, sursaute quand il a peur ou qu'il est surpris), le chapitre, le lieu, un fil
  d'avancement. Le **fil** : Pilou écrit « … » puis son message apparaît (rythme selon la longueur, un toucher sur le
  fil accélère) ; tes choix s'affichent en bulles bleues « à toi » ; des séparateurs disent le chapitre qui commence,
  le lieu qui change, l'heure après une longue absence ; ce que Pilou redit après un échec est marqué « ↺ On reprend
  au dernier check-point » et grisé. En bas, selon la phase : 2 à 4 **options** en gros boutons (libellé sur deux
  lignes), « **Vas-y, Pilou !** » (départ, avec la durée prévue), l'**épreuve** (Jouer ou « Les dés · 55 % »), l'**attente**
  (Pilou en tenue de voyage qui marche sur place et le décor qui défile, la ligne `pendant`, le compte à rebours,
  l'heure de retour, la barre, « Tu peux poser ton téléphone : je te préviens. »), le **repos** après un échec (Pilou
  cabossé, pansement, heure de reprise, « Reprise au dernier check-point : <lieu> »).
- **Les épreuves** (`Epreuves.java`, 10 à 25 s, d'une main) : *réflexe* (toucher quand le curseur passe dans la zone ;
  deux sur trois), *mémoire* (refaire une suite de 3 à 5 signes ● ▲ ■ ◆, deux essais), *rythme* (8 notes à toucher
  sur la ligne), *visée* (toucher des cibles qui filent), et les *dés* (le tirage du moteur, animé sur une jauge où la
  part qui réussit est bleue). Toujours « Laisser faire les dés » ; chaque coup a son signe (✓ / ✕) en plus de sa
  couleur, une vibration légère si les vibrations sont permises ; le résultat montre Pilou qui réagit, puis
  « Continuer ».
- **La fin** : l'issue avec son signe (★ bonne, ◐ douce-amère, ▽ mauvaise, ✧ secrète) et des étincelles pour les
  belles, le titre de la fin, les po et l'xp (« Ces gains attendent ton PC » tant qu'aucun PC ne les a versés ; rien en
  rejouant), le titre gagné, l'objet exclusif (Pilou qui le porte, ou « ? » tant que son dessin manque), le souvenir,
  la grille des fins (celles qu'on a, les autres « ? ? ? »), puis « Retour aux aventures » ou « Rejouer ».
- **Le carnet de voyage** : par campagne, les fins, les souvenirs, les titres et les objets exclusifs ; vide, il le dit
  et propose le prologue.
- **Mettre de côté** en deux gestes : « ⋯ » → « Mettre l'aventure de côté… », puis une confirmation qui dit où
  Pilou reprendra et que rien d'acquis ne se perd. Possible même pendant une attente.
- **Retour de Pilou** (`Retour.java`) : à la fin d'une attente ou d'un repos, **une** notification locale (canal
  « Retours de Pilou (aventures) ») : « Pilou est arrivé : <lieu> — Il a besoin de toi. », jamais le texte de l'histoire.
  Programmée à l'heure de fin avec `AlarmManager.setAndAllowWhileIdle` (pas de permission d'alarme exacte : Android
  peut la retarder de quelques minutes en veille), même app fermée et hors ligne ; reprogrammée après chaque
  décision, chaque synchronisation, à l'ouverture de l'app et au redémarrage du téléphone (`Demarrage`). Pas de relance ;
  rien si l'app est au premier plan ; se coupe dans Réglages → Notifications. La toucher ouvre la lecture.
- **Pilou flottant** : pendant une attente, il porte sa tenue de voyage et sa bulle commence par « ⟶ en route ·
  retour 15 h 40 » ; à son retour, un petit « ! » orange jusqu'à ce qu'on ouvre l'aventure, et le toucher y mène.
- **Synchronisation** : `CampagnesTel.synchroniser` à chaque décision, à l'ouverture de l'app et toutes les 5 min
  (service d'écoute). Le téléphone avance PC éteint ; seules les récompenses attendent un PC.


### Animations des campagnes

`ScenesAnimees.java` (affichage) et `Animations.java` (règles communes avec le PC, vérifiées par `AnimationsTest` sur
`outils/sprites/animations-reference.txt`). La scène (`Aventure.Scene`) dessine le décor en dessin fin et le fait vivre :
à sa vitesse dans la lecture (`plein(true)`), au ralenti (quatre images, trois fois plus lentes) dans la liste et sur
l'accueil ; un décor qui change s'efface par un volet pixelisé. Le personnage du message (champ `personnage` du nœud)
apparaît au bord droit de la scène (`ScenesAnimees.Portrait`, 96 dp), respire, cligne, et parle pendant ses répliques.
Pilou écrit lettre à lettre (`ScenesAnimees.Ecriture` : le texte est posé en entier, la fin reste invisible, la bulle
ne bouge pas ; un toucher écrit tout). Le fond de la lecture prend une teinte légère du ton et de l'heure (lisible en
clair comme en sombre). À la fin, les récompenses tombent une à une ; le souvenir et l'emblème du ton se posent avec un
éclat. Menu « ⋯ » de la lecture : « Animations : complètes / réduites / aucune » et « Texte instantané » (préférences
`animationsCampagnes`, `texteInstantane`) ; l'échelle des animations du système à 0 coupe tout. Rien ne se redessine
hors de l'écran (`isShown`), images rendues une fois (cache de 24 sprites), décors et portraits fins lus à la demande.
Capture Robolectric : `aventure-personnage`, `aventure-personnage-sans-animation`.

### Chasse aux bugs

Un jeu de tir à vagues, original : Pilou, en bas, tire tout seul des étincelles ; on le déplace en
glissant le doigt. Les bugs descendent en zigzag (scarabée 30 points, araignée 20, ver 10) et tirent
de petites croix. Trois boucliers en accolades `{ }` s'effritent sous les tirs ; leur milieu est vide,
les étincelles y passent. Bonus : **café** (tir rapide 8 s), **✓ tests** (bouclier, encaisse un coup).
Toutes les 5 vagues, le **Bug de prod** (barre de vie). Trois vies ; si les bugs atteignent la ligne de
la prod, la partie s'arrête. Sons rétro synthétisés par l'app (aucun fichier), vibrations ; les deux se
coupent dans Réglages → Jeux. XP de la partie : score / 150 + 2 par vague franchie, au plus 30,
créditée au PC comme les autres gains.

## Trois niveaux d'affichage

| Niveau | Ce qu'on voit | Réglage |
|---|---|---|
| 1. Notification permanente | « ❗ 1 t'attend · ◐ 2 en cours », les lignes en la dépliant, Pilou en icône | toujours là pendant l'écoute |
| 2. Widget | Pilou, son niveau et les 4 sessions qui comptent | appui long sur l'écran d'accueil → Widgets → Pilou |
| 3. Pilou flottant | Pilou par-dessus les autres applis ; toucher : la bulle (au-dessus de lui, ou en dessous s'il est en haut) ; glisser : le déplacer ; appui long : ouvrir l’app ; cacher / ramener : notification ou Réglages ; taille réglable dans l'app (60 à 250 %) | case « Pilou flottant » (autorisation « Afficher par-dessus d'autres applis ») |

Alertes en plus : une notification sonore quand une IA attend ton autorisation ou te pose une
question, une plus discrète quand une session finit (chacune se coupe dans l'app).

## Installer

1. Télécharger `Pilou.apk` depuis la dernière release du dépôt, l'ouvrir sur le téléphone et accepter
   l'installation d'une app hors Play Store.
2. Sur le PC : clic droit sur Pilou → Intégrations → **Android : appairer mon téléphone…**
3. Viser le QR code avec l'appareil photo : l'app s'ouvre et s'appaire. Sinon, taper le code de 16
   caractères dans l'app.
4. Dans l'app : autoriser les notifications, cocher « Pilou flottant » si tu le veux, ajouter le widget.

## Quêtes, pièces d'or et boutique

Le PC tire les quêtes (3 du jour, 3 de la semaine, 1 du mois) et tient le solde de pièces d'or (po) ;
le téléphone les affiche (Accueil) et y contribue : pêche, cuisine, petits jeux, caresses et score de
Chasse aux bugs partent avec les gains, chiffrés, et font avancer les quêtes du PC. La **Boutique**
(onglet principal) est gratuite : aucune vraie monnaie. Même catalogue que le PC : des rayons par
emplacement, chacun en rangées de niveau (1, 5, 10, 15, 20, 30, 40, 50) ; le niveau ouvre la rangée,
les pièces d'or achètent. *Acheter* envoie la demande au PC, qui vérifie le solde et le niveau puis
l'applique (l'objet portable est porté dès son arrivée) ; en attendant, l'objet est « ⇢ en route » et le
solde affiché le déduit déjà. *Porter* se voit tout de suite et part au PC. Signes d'état : cadenas + NIV
(fermé), ◉ (achetable), ◌ (trop cher), ✓ (à toi), ★ (porté). Quand un niveau ouvre des rangées, une
fenêtre « NIVEAU N ! Rangées débloquées » propose « Voir en boutique ». Les animations (pièces, néon,
clignotements) se figent si le téléphone supprime les animations.

Les niveaux ouvrent l'accès (jeux, objets, évolution : Gouttelette, Pilou, Pilou Nimbus, Pilou
Astral) au lieu d'offrir des objets ; chaque niveau gagné rapporte des pièces d'or. Ce qui avait déjà
été gagné avant cette version reste acquis.

## Soins

Le PC envoie l'état des soins calculé à son heure (faim, propreté, moral, vacances, bouderie) et les
variantes d'évolution ; le téléphone y ajoute les soins qu'il a faits et que le PC n'a pas encore
comptés. Sur l'Accueil, une petite icône (◒ faim, ✦ propreté, ♥ moral) n'apparaît près de Pilou que si
un besoin passe sous 30 % : un toucher la comble ; **♥ Prendre soin de Pilou** comble tout. Les soins
partent avec les gains (actions datées, identifiant unique) et le PC les verse au journal commun.
Pilou boudeur quand il est négligé (moue, nuage gris, bras croisés du Nimbus, dos tourné parfois ;
« ☁ Pilou boude : gains ×0,6 » sous la barre d'XP, et l'XP des jeux du téléphone × 0,6), rayonnant quand
il est bien soigné (× 1,2), variante câlin ou espiègle : le téléphone les dessine comme le PC.

Réglages → *Soins* : vacances (tout est figé) et « Me prévenir s'il a besoin de moi » — **désactivé par
défaut**, une notification par jour au plus. Pas de mode de difficulté : le même rythme pour tous.

## Mises à jour

Une fois par jour, l'app lit `version.json` de la dernière release. Une version plus récente donne une
notification ; la toucher télécharge `Pilou.apk` et ouvre la confirmation d'Android (« Mettre à
jour »). La première fois, Android demande d'autoriser Pilou à installer des applis. Une app installée
hors Play Store ne peut pas se mettre à jour sans cette confirmation.

## Comment ça passe du PC au téléphone

```
PilouBureau ── POST chiffré ──▶ relais ntfy ── flux JSON ──▶ app Android
 (à chaque changement d'état,      (ntfy.sh par défaut,       (service au premier plan :
  regroupé sur 3 s ; sinon un       ou ton serveur ntfy)       notification, widget, Pilou flottant)
  battement toutes les 15 min)
```

- Le code d'appairage donne le **sujet** ntfy et la **clé** AES-256-GCM (HMAC-SHA256 du code, deux
  usages). Le relais ne voit qu'un texte en base64 ; sans le code, on ne trouve même pas le sujet.
- Seuls les changements d'état partent (attente, travail, fini…), pas chaque outil : le téléphone
  calcule les durées lui-même. ntfy.sh gratuit limite le nombre de messages par jour ; au-delà,
  Pilou se tait 5 min et réessaie. Avec ton propre serveur ntfy, pas de limite (Intégrations →
  Android : relais…, et le même dans l'app).
- Sans nouvelles depuis 25 min, le téléphone considère que le PC dort.
- Format du message déchiffré : `Telephone.Charge` dans `apps/PilouBureau/Telephone.cs`. Le même
  vecteur de test vérifie le chiffrement des deux côtés (`VecteurTests.cs`, `ChiffreTest.java`).

## Construire

L'app est en Java, sans aucune bibliothèque (le framework Android suffit). GitHub Actions la construit
(`ci.yml`, `release.yml`). En local, avec le SDK Android : `cd android && ./gradlew assembleRelease`.

La clé de signature `android/app/pilou.keystore` est publique (mot de passe dans `app/build.gradle`) :
elle sert à ce que chaque version s'installe par-dessus la précédente. Pour une diffusion plus large,
fournir une clé privée par `PILOU_KEYSTORE` et `PILOU_KEYSTORE_PASS` (secrets de la CI).

## Revue d'interface

L'interface se relit régulièrement, sur captures plutôt que de mémoire.

**Les captures.** `CapturesTest` (Robolectric, rendu graphique natif) photographie chaque écran : Accueil
(neuf et appairé : sessions, quêtes, groupe), Jouer, Boutique (vitrine, rayons Dos / Tête / Décors avec essayage,
fenêtre « Rangées débloquées »), Collection (Carnet, Recettes, Niveaux, Style),
Réglages, **Aventure** (liste neuve, en cours, mise de côté ; lecture : choix, retour, épreuve, repos, reprise, fin ; confirmation ; carnet ; accueil pendant une attente et quand Pilou attend), les cinq épreuves (au départ et en cours de partie), Atelier (pêche, cuisine), Chasse aux bugs (accueil, partie, pause) et la mise à jour, en thème
**clair et sombre**, sur un **petit** (360 × 640 dp) et un **grand** téléphone (412 × 915 dp). Les pages qui
défilent sont aussi prises en entier (`…-long.png`).

- **En local** (SDK Android) : `cd android && ./gradlew testReleaseUnitTest --tests '*CapturesTest*'`,
  images dans `android/app/build/captures/`.
- **Dans la CI** : artefact `captures-ui` du job Android. Les miniatures du petit téléphone sont aussi dans
  le journal du job, en lignes `CAPTURE <nom> <i>/<n> <base64>` ; un petit script les reconstitue en PNG.
- Le test ne fait jamais échouer le build : un écran qui refuse de se dessiner écrit `CAPTURE-ERREUR`.

**La check-list**, écran par écran, en clair puis en sombre :

| Point | Seuil |
|---|---|
| Contraste du texte | ≥ 4,5:1 (WCAG AA) ; ≥ 3:1 pour les signes et icônes |
| Taille du texte | échelle `Ui.T_*` : 28 (page), 19 (carte), 15 (corps), 13 (détail), 12 (étiquette en capitales espacées) ; 16 pour les messages des campagnes ; jamais sous 12 sp |
| Zones tactiles | ≥ 48 × 48 dp (lignes de réglage, boutons, onglets) |
| Marges | grille de 4 / 8 dp ; pages à 18 dp des bords, cartes à 16 dp de padding |
| Débordements | aucun texte coupé au milieu d'un mot, aucun bloc hors de l'écran sur petit téléphone |
| États vides | non appairé, aucune session, carnet vide : un message et une action, jamais un trou |
| Couleurs | jamais rouge contre vert (deutéranopie) ; chaque état a aussi un signe (❗ ? ◐ ✓ ■ ✕ ◇) |
| Accessibilité | `contentDescription` sur ce qui n'a pas de texte ; icônes décoratives ignorées par TalkBack ; onglet courant « sélectionné » |
| Cohérence | mêmes composants partout (`Ui.bouton`, `Ui.carte`, `Ui.ligne`) ; pas de bouton Android brut |

## L'atelier : pêcher, cuisiner, jouer

Onglet **Jouer** → une carte de l'atelier : une petite scène en pixels où Pilou pêche, cuisine et
joue, avec les mêmes règles que sur le PC. Le carnet, les recettes et les récompenses sont dans
l'onglet **Collection**.

- **Pêche** : Pilou lance sa ligne ; quand le bouchon plonge (« ! »), il reste 1,2 s pour le toucher.
  Trop tôt, le poisson file. Sans rien faire, Pilou ferre seul : une fois sur trois environ, et jamais
  mieux que « rare ». 23 prises, cinq raretés reconnaissables au signe (`· ◇ ◆ ✦ ★`) et au cadre
  (aucun, coins, trait, double, étoilé). La première prise d'une espèce compte double (+5).
- **Cuisine** : avec ce qu'il a pêché sur le téléphone, Pilou cuisine (30 recettes débloquées par
  niveau, plats inventés). Toucher la marmite pour remuer évite de brûler le plat.
- **Jouer** : étoile filante à attraper (+10), trois bulles à éclater (+5 chacune, +5 de bonus),
  « tape m'en cinq » (+10). **Caresse** : toucher Pilou (+1, au plus toutes les 3 s).
- **Carnet de pêche, livre de recettes, récompenses** : ce qui est connu sur le PC et sur le
  téléphone ; « ??? » pour le reste.

L'XP vit sur le PC. Chaque gain part, chiffré, sur un deuxième sujet ntfy tiré du même code
(`pilou-retour-v1`) ; le PC le relit toutes les 90 s, le crédite une seule fois (par son identifiant)
et le cite dans son prochain état ; le téléphone le retire alors de sa file. Hors ligne, les gains
attendent (« +N en attente du PC ») et repartent. Le panier d'ingrédients du téléphone est le sien ;
le carnet et les recettes connues s'additionnent.

## Groupe d'appareils

Le code d'appairage est aussi le code du **groupe** : un autre PC qui le saisit (*Intégrations →
Rejoindre un groupe*) partage l'XP avec celui-ci, sans dossier commun. Chaque PC publie son propre
compteur sur un troisième sujet (`pilou-groupe-v1`) et garde, pour chacun des autres, la plus grande
valeur reçue (compteur G) ; le total est la somme. Les gains du téléphone sont crédités par **chaque**
PC du groupe dans un compteur à part (`XpTelephone`), dont on prend le maximum : ils ne comptent qu'une
fois. L'app affiche la liste *Appareils du groupe* (nom, XP, vu il y a…) que le PC lui transmet.

Partagé dans le groupe : XP, pièces d'or, objets et tenue, carnet et recettes, soins et variantes
d'évolution, limites d'expédition, et **métiers et succès**. Pour ces derniers, chaque PC publie ses
propres totaux (champ `act` : minutes par activité non nulles ; `cpt` : frappes avec Pilou, captures,
présentations, record, vague et boss de Défense du bureau), la liste de ses succès (`suc`) et les grades
de métier déjà récompensés (`mp`). Le total du groupe est la somme (plus grande valeur reçue de chaque
appareil, records au maximum), les succès et grades payés une union : le premier PC qui franchit un
succès ou un grade crédite l'XP, les autres le reprennent sans XP. Un ancien PC ignore ces champs.

## Métiers et succès

*Collection → Métiers* (et la petite carte **Métiers et succès** de l'Accueil, qui y mène) montre les
métiers du groupe : nom, grade (Novice → Légende), barre vers le palier suivant (« 5,7 h / 6 h »),
⚒ pour un métier de travail, ♪ pour un loisir, triés par heures, ceux à 0 h grisés ; puis
« Succès 3/22 », les obtenus d'abord (✓), les autres avec leur description et leur avancement
(« 3 / 10 », « 2,5 h / 4 h »). Le PC envoie `metiers` (niveaux) et `succes` (ids) — ce qu'envoie aussi
un ancien PC, dont l'app montre alors le grade seul (« au moins 30 h ») — et, s'il est à jour,
`heures` (dixièmes d'heure par métier) et `avance` (dixièmes d'avancement des succès commencés). Le
catalogue (`Metiers.java`) est le même que celui du PC : `src/test/resources/metiers-succes.txt`, écrit
par le test C# depuis `Metiers.cs`, est relu par `MetiersTest`. Un message trop long est allégé pas à
pas (`Telephone.SousLimite`) ; l'app garde alors carnet, recettes, heures et avancement du message
précédent.

## Météo

Quand le connecteur météo du PC est actif, le message du PC porte un champ facultatif
`meteo` : `{"etat":"pluie","temperature":8,"ville":"Paris","signe":"☂"}`. Le téléphone ne contacte
aucun service météo. L'Accueil montre une carte (« ☂ pluie · 8 °C · Paris » et ce qu'en dit Pilou),
et Pilou subit le temps dans l'app, le widget et Pilou flottant, avec les mêmes règles que le PC
(`Meteo.java`, miroir de `Meteo.cs`) : mouillé sans parapluie ni imperméable, grelottant sans bonnet,
écharpe ni moufles, en sueur sans lunettes ni éventail. Une météo vieille de plus de trois heures
(PC éteint) n'est plus montrée. Sans le champ (ancien PC, connecteur coupé), rien ne change.

## Ce qui est sur le téléphone, et ce qui n'y est pas

| Fonction | PC | Téléphone |
|---|---|---|
| État des sessions (❗ ? ◐ ✓ ■ ✕) | bulle | notification, widget, Pilou flottant |
| Humeurs (concentré, inquiet, fête, grimace, soulagé, endormi) | ✓ | ✓ (venues du PC ; fête et caresse aussi dans l'atelier) |
| Niveau, titre, XP | ✓ | ✓ reçus du PC, plus les gains en attente |
| Expéditions (docs/EXPEDITIONS.md) | lancées au clic droit ou depuis l'icône près de l'horloge | lecture seule : carte « ⚔ Expédition » (en route, retour vers…, dernier journal) et ⚡ près de l'XP |
| Couleurs | achetées en boutique, portées au clic droit | achetées et portées dans la Boutique |
| Accessoires (chapeaux historiques) | achetés en boutique, choisis au clic droit | achetés dans la Boutique (choisis sur le PC) |
| Objets de boutique (tête, yeux, cou, dos, main, pieds, compagnon, effet) | ✓ Boutique (rayons, rangées, essayage) | ✓ onglet Boutique (rayons, rangées, essayage) |
| Décors (derrière Pilou) | aperçu dans la boutique | ✓ Accueil et essayage |
| Cadres de bulle | ✓ bulle de Pilou | ✓ Pilou flottant |
| Bandeau niveau / XP / po | menu, boutique, info-bulle | ✓ en haut de chaque onglet |
| Météo (pluie, neige, chaleur… et ce que Pilou en pense) | ✓ connecteur Météo | ✓ carte Accueil, Pilou mouillé ou au sec |
| Quêtes et pièces d'or | ✓ menu Quêtes | ✓ Accueil ; les parties du téléphone comptent |
| Niveaux (accès), évolution | ✓ menus Niveau, Évolution | ✓ Collection → Niveaux ; jeux verrouillés « niveau N » |
| Caresse | ✓ | ✓ toucher Pilou (app, atelier), créditée au PC |
| Soins (faim, propreté, moral ; icône seulement s'il en a besoin) | ✓ icône près de Pilou, clic droit | ✓ Accueil, Réglages → Soins |
| Étoile filante, bulles, tape m'en cinq | ✓ | ✓ atelier |
| Pêche, cuisine | ✓ | ✓ atelier |
| Carnet de pêche, livre de recettes | ✓ | ✓ onglet Collection |
| Taille de Pilou | ✓ | ✓ curseur |
| Alertes (une IA attend, a fini) | webhook | ✓ notifications |
| Mises à jour | automatiques | notification, un appui, confirmation d'Android |
| Messages du jour (bonjour, bon appétit…) | ✓ | pas encore |
| Traînée d'étoiles (niveau 9) | ✓ | pas encore |
| Thème clair/sombre de la bulle | ✓ | pas encore (bulle claire) |
| Promenade, suit la souris, s'accroche au curseur, toque à l'écran, ballon | ✓ | sans objet (pas de souris) ; on déplace Pilou au doigt |
| Intégrations (Codex, Discord, webhook, autres logiciels) | ✓ | sans objet : elles vivent sur le PC, le téléphone en voit le résultat |

Le dessin du téléphone est plus fin (grille 34 × 40 au lieu de 26 × 30, même taille à l'écran) ; le
PC garde pour l'instant sa grille.

## Pas encore

Plusieurs PC appairés au même téléphone, Pilou qui se promène sur le bord de l'écran, messages du
jour et traînée d'étoiles sur le téléphone.
