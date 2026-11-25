# Pilou sur Android

L'app montre sur le téléphone ce que Pilou voit sur le PC : quelles sessions Claude et Codex
travaillent, lesquelles ont fini, lesquelles t'attendent. Elle ne fait tourner aucune IA : elle écoute
le PC.

## Trois niveaux d'affichage

| Niveau | Ce qu'on voit | Réglage |
|---|---|---|
| 1. Notification permanente | « ❗ 1 t'attend · ◐ 2 en cours », les lignes en la dépliant, Pilou en icône | toujours là pendant l'écoute |
| 2. Widget | Pilou, son niveau et les 4 sessions qui comptent | appui long sur l'écran d'accueil → Widgets → Pilou |
| 3. Pilou flottant | Pilou par-dessus les autres applis ; toucher : la bulle ; glisser : le déplacer ; appui long : caché 10 min | case « Pilou flottant » (autorisation « Afficher par-dessus d'autres applis ») |

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

## Pas encore

Caresser Pilou depuis le téléphone (retour vers le PC), XP gagnée sur le téléphone, plusieurs PC
appairés au même téléphone, Pilou qui se promène sur le bord de l'écran.
