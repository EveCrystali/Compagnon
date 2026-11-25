# Pilou sur Android

L'app montre sur le téléphone ce que Pilou voit sur le PC : quelles sessions Claude et Codex
travaillent, lesquelles ont fini, lesquelles t'attendent. Elle ne fait tourner aucune IA : elle écoute
le PC.

## Trois niveaux d'affichage

| Niveau | Ce qu'on voit | Réglage |
|---|---|---|
| 1. Notification permanente | « ❗ 1 t'attend · ◐ 2 en cours », les lignes en la dépliant, Pilou en icône | toujours là pendant l'écoute |
| 2. Widget | Pilou, son niveau et les 4 sessions qui comptent | appui long sur l'écran d'accueil → Widgets → Pilou |
| 3. Pilou flottant | Pilou par-dessus les autres applis ; toucher : la bulle (au-dessus de lui, ou en dessous s'il est en haut) ; glisser : le déplacer ; appui long : caché 10 min ; taille réglable dans l'app (60 à 250 %) | case « Pilou flottant » (autorisation « Afficher par-dessus d'autres applis ») |

Alertes en plus : une notification sonore quand une IA attend ton autorisation ou te pose une
question, une plus discrète quand une session finit (chacune se coupe dans l'app).

## Installer

1. Télécharger `Pilou.apk` depuis la dernière release du dépôt, l'ouvrir sur le téléphone et accepter
   l'installation d'une app hors Play Store.
2. Sur le PC : clic droit sur Pilou → Intégrations → **Android : appairer mon téléphone…**
3. Viser le QR code avec l'appareil photo : l'app s'ouvre et s'appaire. Sinon, taper le code de 16
   caractères dans l'app.
4. Dans l'app : autoriser les notifications, cocher « Pilou flottant » si tu le veux, ajouter le widget.

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

## L'atelier : pêcher, cuisiner, jouer

Bouton « Atelier de Pilou » sur l'écran de l'app : une petite scène en pixels où Pilou pêche, cuisine
et joue, avec les mêmes règles que sur le PC.

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

## Ce qui est sur le téléphone, et ce qui n'y est pas

| Fonction | PC | Téléphone |
|---|---|---|
| État des sessions (❗ ? ◐ ✓ ■ ✕) | bulle | notification, widget, Pilou flottant |
| Humeurs (concentré, inquiet, fête, grimace, soulagé, endormi) | ✓ | ✓ (venues du PC ; fête et caresse aussi dans l'atelier) |
| Niveau, titre, XP | ✓ | ✓ reçus du PC, plus les gains en attente |
| Couleurs (10) | choix au clic droit | affichées (choisies sur le PC) |
| Accessoires (11) | choix au clic droit | affichés (choisis sur le PC) |
| Catalogue des récompenses | ✓ | ✓ atelier |
| Caresse | ✓ | ✓ toucher Pilou (app, atelier), créditée au PC |
| Étoile filante, bulles, tape m'en cinq | ✓ | ✓ atelier |
| Pêche, cuisine | ✓ | ✓ atelier |
| Carnet de pêche, livre de recettes | ✓ | ✓ atelier |
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
