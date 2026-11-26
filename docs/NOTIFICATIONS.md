# Clavier, captures d'écran et notifications

Trois petits gestes de Pilou sur Windows, chacun avec sa case dans **clic droit → Clavier, photo,
notifications**. Rien n'est imposé : décoche, et le crochet ou l'écoute correspondante est retiré aussitôt.

| Case | Par défaut | Ce que fait Pilou |
|---|---|---|
| Pilou tape avec moi au clavier | cochée | tu tapes en rafale : pouf de fumée, tour sur lui-même, il réapparaît assis devant un mini clavier et tape avec toi ; 9 s sans frappe, pouf inverse |
| Appareil photo à chaque capture d'écran | cochée | il sort son appareil, flash (cadre blanc bref), « CLIC ! », un polaroïd tombe à ses pieds et se développe |
| Notifications Windows dans la bulle | **décochée** | il lève la tête, brandit une enveloppe et montre la notification dans sa bulle (voir plus bas : nécessite une identité de package) |

Aucun geste ne se lance quand Pilou est caché pour ne pas gêner (plein écran, jeu, présentation, visio,
réunion à l'agenda), pendant une visite chez un ami, pendant un mini-jeu, quand une IA t'attend ni quand tu le
tiens à la souris. La tenue d'activité garde ses lunettes et chapeaux ; ce qu'elle tient en main (clavier de la
tenue code, manette…) laisse la place au mini clavier ou à l'appareil.

Essayer sans conditions réelles :

```
PilouBureau.exe --devant --essai=clavier        # frappes simulées 6 s, puis il range au bout de 9 s
PilouBureau.exe --devant --essai=photo
PilouBureau.exe --devant --essai=notif          # « Messagerie · Léo · On se voit à midi… »
PilouBureau.exe --devant --essai=notif:masque   # « 2 messages de Messagerie »
PilouBureau.exe --instantane=pilou.png --essai=clavier
```

Succès liés (menu Métiers et succès) : **Dactylo** (taper 25 fois avec Pilou) et **Photographe** (10 captures).
Le profil ne garde que ces deux nombres.

## Pilou tape au clavier

- **Détection** : un crochet clavier bas niveau (`WH_KEYBOARD_LL`, `Crochets.cs`). Il compte les touches
  *relâchées* (une touche maintenue ne compte qu'une fois) et ignore les frappes simulées par un logiciel.
  Rafale : au moins 15 frappes en 5 s (`CompteurFrappes`, `Gestes.cs`).
- **Confidentialité** : le crochet ne fait que compter. Il ne lit, ne garde, n'écrit ni ne journalise **aucune
  touche ni aucun caractère** : le compteur ne reçoit qu'un instant (« une frappe à t »), garde les instants des
  5 dernières secondes en mémoire, et rien d'autre. Seule exception : le code de la touche Impr. écran est
  comparé sur place pour détecter une capture (il n'est pas gardé non plus). Un test vérifie que le compteur
  n'a aucune entrée qui puisse recevoir une touche.
- Limite connue : Windows retire un crochet bas niveau qui répond trop lentement ; si l'interface de Pilou est
  très occupée, il peut cesser de compter jusqu'au prochain redémarrage.

## Capture d'écran → appareil photo

Trois signaux, combinés, et **une seule animation par capture** (les signaux des 2 s suivantes sont des échos,
`AntiDoublon`) :

1. la touche **Impr. écran** (même crochet, seulement ce code de touche) ;
2. une **image qui arrive dans le presse-papiers** (`AddClipboardFormatListener`, puis seulement « une image est
   là ? » via `IsClipboardFormatAvailable` : le contenu n'est jamais ouvert ni copié) — c'est ce que font
   Win+Maj+S et l'Outil Capture ;
3. un **fichier image créé** dans `Images\Screenshots` (redirection OneDrive comprise) et les dossiers OneDrive
   équivalents s'ils existent (`Pictures\Screenshots`, `Images\Captures d'écran`) — c'est ce que fait Win+Impr. écran.
   Seule l'extension du nom compte ; le fichier n'est pas lu.

Copier une image depuis un navigateur déclenche aussi l'appareil (même signal que Win+Maj+S) : c'est rare, et
la case le coupe. Le flash est un cadre blanc translucide autour de Pilou, 200 ms, jamais plein écran.

## Notifications Windows dans la bulle

### Ce que dit la documentation Microsoft (recherche du 26/11/2026)

- L'API documentée est **`UserNotificationListener`** (`Windows.UI.Notifications.Management`) : `GetAccessStatus`,
  `RequestAccessAsync` (à appeler sur le fil d'interface), `GetNotificationsAsync(NotificationKinds.Toast)`,
  `GetNotification`, `NotificationChanged`, `RemoveNotification`, `ClearNotifications`.
  [Notification listener](https://learn.microsoft.com/windows/apps/develop/notifications/app-notifications/notification-listener) ·
  [référence](https://learn.microsoft.com/uwp/api/windows.ui.notifications.management.usernotificationlistener)
- Elle exige de **déclarer la capacité `userNotificationListener`** (`uap3:Capability`) dans le manifeste du
  *package* ; c'est une capacité d'usage général, pas restreinte.
  [Déclarations de capacités](https://learn.microsoft.com/windows/apps/package-and-deploy/app-capability-declarations#general-use-capabilities) ·
  [uap3:Capability](https://learn.microsoft.com/uwp/schemas/appxpackage/uapmanifestschema/element-uap3-capability)
- Une appli Win32 non empaquetée n'a pas de manifeste de package : il lui faut une **identité de package**,
  soit MSIX, soit un **package avec emplacement externe** (« sparse package ») : un petit package signé,
  enregistré avec `Add-AppxPackage -ExternalLocation`, relié à l'exe par un élément `<msix>` dans son manifeste
  d'application. Le certificat doit être approuvé sur la machine (un certificat auto-signé doit être importé
  dans « Personnes autorisées »).
  [Grant package identity by packaging with external location](https://learn.microsoft.com/windows/apps/desktop/modernize/grant-identity-to-nonpackaged-apps) ·
  [Détecter l'identité](https://learn.microsoft.com/windows/msix/detect-package-identity)
- Côté .NET, les projections WinRT viennent d'un TFM Windows versionné, par exemple
  `net9.0-windows10.0.19041.0`.
  [Call Windows Runtime APIs in desktop apps](https://learn.microsoft.com/windows/apps/desktop/modernize/winrt-apis-desktop-apps)
- **On ne peut pas empêcher la bannière** d'une autre appli. La voie propre : activer **Ne pas déranger**
  (Paramètres › Système › Notifications) ; les notifications vont alors directement au centre de notifications,
  sans bannière, et Pilou les montre lui-même.
  [Réglage Do not disturb](https://learn.microsoft.com/windows/apps/develop/settings/settings-common#do-not-disturb)
- **`RemoveNotification` n'est pas utile ici** : il retire une notification du centre de notifications (elle
  serait perdue pour toi), il ne supprime pas une bannière déjà affichée. Pilou ne l'appelle jamais et ne touche
  pas au centre de notifications. Aucune API non documentée (WNF, base de données du centre…) n'est utilisée.

### Ce qui est fait, ce qui manque

| | État |
|---|---|
| Réglages : case (décochée par défaut), applis toutes / sauf cochées / seulement cochées, « masquer le contenu », lien vers Ne pas déranger | fait, testé (`NotificationsTests`) |
| Filtre, mise en une ligne, regroupement « 3 messages de X », heures calmes, auto-masquage | fait, testé |
| Bulle (initiale de l'appli dans un carré, nom, titre, une ligne) et enveloppe brandie | fait, visible avec `--essai=notif` |
| Abstraction `ISourceNotifications` et source Windows (`SourceNotifsWindows.cs`) : détection de l'identité (`GetCurrentPackageFullName`), `RequestAccessAsync`, relevé toutes les 2 s par différence d'identifiants (méthode de la doc), lecture du binding `ToastGeneric` | écrit et compilé, **jamais exécuté** (pas de Windows ici) |
| Identité de package pour Pilou | **manque** : rien n'est enregistré par l'installateur |

Dans la version livrée, Pilou n'a pas d'identité de package : la case « Notifications Windows » affiche
« indisponible : Windows réserve cette lecture aux applis empaquetées » et **rien n'est lu**. La version livrée
n'embarque même pas les projections WinRT (25 Mo de plus pour une fonction qui ne peut pas marcher sans identité).

### Donner une identité à Pilou (piste, non testée)

Tout est prêt dans le dépôt, mais rien de ceci n'a été essayé sur un vrai Windows :

1. Compiler la variante avec lecteur et manifeste d'identité :
   `dotnet publish apps/PilouBureau -c Release -r win-x64 --self-contained -p:IdentitePackage=true -p:PublishSingleFile=true`
   (TFM `net9.0-windows10.0.19041.0`, constante `LECTEUR_NOTIFS`, manifeste `identite/PilouBureau.identite.manifest`).
   La CI compile cette variante pour qu'elle reste compilable.
2. Poser un `pilou.png` à côté de `PilouBureau.exe` (logo exigé par le manifeste de package).
3. Avec le SDK Windows : `MakeAppx.exe pack /o /d identite /nv /p Pilou.msix` (dossier contenant
   `identite/AppxManifest.xml`), créer un certificat dont le sujet est `CN=PilouLocal`
   (`New-SelfSignedCertificate -Type CodeSigningCert -Subject "CN=PilouLocal" -CertStoreLocation Cert:\CurrentUser\My`),
   signer (`SignTool.exe sign /fd SHA256 …`), importer le `.cer` public dans `Cert:\CurrentUser\TrustedPeople`.
4. `Add-AppxPackage -Path Pilou.msix -ExternalLocation "$env:USERPROFILE\.claude\compagnon\bureau"`.
5. Relancer Pilou, cocher la case : Windows demande l'accès aux notifications.

Pour une diffusion à tous, il faudrait un vrai certificat de signature (Azure Trusted Signing ou autre) et que
l'installateur enregistre le package : c'est le travail qui reste.

### Confidentialité

Le contenu d'une notification (appli, titre, texte) reste **en mémoire, sur ce PC**, le temps de l'afficher
(8 s), puis il est oublié. Il n'est jamais écrit sur disque, jamais journalisé, jamais envoyé au téléphone, au
groupe d'appareils, aux amis, au webhook ni à l'API locale. Seuls les noms des applis que tu coches pour le
filtre sont gardés dans `reglages.json`. En mode « masquer le contenu », la bulle ne dit que « 1 message de X ».
Pas de logo d'appli : une initiale dans un carré. Pendant les heures calmes (réglage des amis) et quand Pilou
est caché, rien n'est montré (tout reste dans le centre de notifications de Windows).

## Sur Android (piste)

`NotificationListenerService` permettrait la même chose sur le téléphone (accès accordé par l'utilisateur dans
Paramètres › Notifications › Accès aux notifications, opt-in). Ce n'est pas fait : l'app Android ne montre pas
encore de bulle de Pilou par-dessus les autres applis pour ce genre d'événement, et ce service lit tout le
contenu des notifications du téléphone ; il mérite sa propre revue de confidentialité. Les sprites (enveloppe,
pouf…) sont déjà dans la banque commune et se dessinent à l'identique sur le téléphone.

## Sprites

`outils/sprites/gestes_sprites.py` : `pouf-1` à `pouf-5`, `clavier-mini` (6 images), `appareil-photo`,
`photo-flash`, `polaroid-1` à `polaroid-4`, `enveloppe-notif`, `enveloppe-close`. Palette bleu, orange, crème et
ardoise ; chaque état a aussi un signe de forme (touche enfoncée d'un pixel, enveloppe ouverte avec lettre ou
fermée avec cachet rond, photo qui se développe). Les poses de référence (`rendus-reference.txt`) couvrent ces
sprites : PC, téléphone et rendu Python tombent sur les mêmes pixels.
