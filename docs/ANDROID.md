# Pilou sur Android

L'app montre sur le téléphone ce que Pilou voit sur le PC : quelles sessions Claude et Codex
travaillent, lesquelles ont fini, lesquelles t'attendent. Elle ne fait tourner aucune IA : elle écoute
le PC.

## L'app

Une barre de navigation en bas, quatre onglets (thème clair ou sombre selon le téléphone) :

| Onglet | Ce qu'on y trouve |
|---|---|
| **Accueil** | Pilou en grand (le toucher le caresse), niveau, titre et barre d'XP, état du PC (« ● en ligne » / « ◌ le PC dort »), **les quêtes** (du jour ◔, de la semaine ◑, du mois ●, progrès et pièces d'or, série), les sessions en cartes (❗ ? ◐ ✓ ■ ✕), les appareils du groupe, le mot du jour. Pas encore appairé : un guide en trois étapes. |
| **Jouer** | **Chasse aux bugs** en vedette (aperçu animé, record), puis les cartes de l'atelier : pêche, cuisine, étoile filante, bulles, tape m'en cinq. Un jeu pas encore ouvert montre « ◇ niveau N ». |
| **Collection** | Carnet de pêche (grille des 23 prises, cadre de rareté), livre de recettes, **Niveaux** (ce que chaque niveau ouvre : jeux, évolutions, titres, articles de boutique), style (ce qu'on possède), **Boutique**. |
| **Réglages** | Appairage, Pilou flottant (taille, cacher, ramener), notifications, jeux (sons, vibrations), mises à jour, diagnostic (journal de plantage, copier le diagnostic), à propos. |

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
(Collection → Boutique) est gratuite : aucune vraie monnaie. *Acheter* envoie la demande au PC, qui
vérifie le solde et le niveau puis l'applique ; en attendant, l'objet est « en route » et le solde
affiché le déduit déjà. *Porter* se voit tout de suite et part au PC. Les objets ne sont pas encore
dessinés : la boutique les montre par leur nom et un signe d'emplacement.

Les niveaux ouvrent l'accès (jeux, objets, évolution : Gouttelette, Pilou, Pilou Nimbus, Pilou
Astral) au lieu d'offrir des objets ; chaque niveau gagné rapporte des pièces d'or. Ce qui avait déjà
été gagné avant cette version reste acquis.

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
(neuf et appairé : sessions, quêtes, groupe), Jouer, Collection (Carnet, Recettes, Niveaux, Style, Boutique),
Réglages, Atelier (pêche, cuisine), Chasse aux bugs (accueil, partie, pause) et la mise à jour, en thème
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
| Taille du texte | ≥ 12 sp ; titres de page 28 sp, sections 12 sp en capitales espacées |
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
| Couleurs | achetées en boutique, portées au clic droit | achetées et portées dans la Boutique |
| Accessoires (chapeaux historiques) | achetés en boutique, choisis au clic droit | achetés dans la Boutique (choisis sur le PC) |
| Objets de boutique (tête, yeux, cou, dos, main, pieds, compagnon, effet) | ✓ Boutique… | ✓ Boutique (acheter, porter) |
| Météo (pluie, neige, chaleur… et ce que Pilou en pense) | ✓ connecteur Météo | ✓ carte Accueil, Pilou mouillé ou au sec |
| Quêtes et pièces d'or | ✓ menu Quêtes | ✓ Accueil ; les parties du téléphone comptent |
| Niveaux (accès), évolution | ✓ menus Niveau, Évolution | ✓ Collection → Niveaux ; jeux verrouillés « niveau N » |
| Caresse | ✓ | ✓ toucher Pilou (app, atelier), créditée au PC |
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
