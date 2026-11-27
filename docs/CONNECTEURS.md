# Connecteurs

Clic droit sur Pilou → **Connecteurs…**. Chaque connecteur vit dans un fichier
(`apps/PilouBureau/Connecteurs/<Nom>.cs`), reste **coupé tant que tu ne le coches pas**, et porte
dans sa carte un volet *Comment l'activer ?* qui reprend les étapes ci-dessous.

Trois règles valent pour tous :

- **Jetons et mots de passe** : chiffrés par Windows (DPAPI) dans `secrets.bin`, jamais dans
  `reglages.json`. Un champ secret affiche seulement « ● enregistré (chiffré) ».
- **Rien d'autre n'est gardé** que ce que Pilou affiche : la bulle, le journal des 50 dernières lignes
  (en mémoire), les 5 dernières nouvelles pour le téléphone. Pour ne pas annoncer deux fois la même
  chose, certains connecteurs notent des identifiants (numéro de notification, de vidéo, de mail) —
  jamais un contenu.
- **Aucun contenu ne part ailleurs** que vers les sorties que tu as activées : le salon de sortie du
  bot Discord (qui ne reçoit que ce que Pilou vit : une IA t'attend, quête réussie, évolution) et la
  carte *Nouvelles* du téléphone, chiffrée de bout en bout par le relais, avec une case *Titre
  seulement*.

Les événements suivent le même chemin que ceux de l'[API locale](API.md) : bulle, saut, alerte
selon la gravité (0 info, 1 à voir, 2 urgent) ; certains prêtent une tenue à Pilou pour quelques
secondes, font la fête ou font avancer une quête.

| Connecteur | Signe | Rythme | Ce qu'il te faut |
| --- | --- | --- | --- |
| Discord (bot) | ♯ | connexion permanente | un bot créé par toi (jeton) |
| GitHub | ⑂ | 2 min | un jeton personnel |
| Mail | ✉ | 3 min | un mot de passe d'application IMAP |
| Agenda | ▦ | 1 min (lien relu toutes les 30 min) | le lien ICS secret de ton agenda |
| Éditeurs (VS, VS Code) | ⚠ | quand le fichier actif change (actif par défaut) | l'extension de ton éditeur ([EDITEURS.md](EDITEURS.md)) |
| Spotify | ♪ | 20 s | une app Spotify (Client ID) et ton accord |
| Twitch | ▶ | 3 min | une app Twitch (Client ID + secret) |
| YouTube | ▷ | 10 min | rien (une clé d'API pour les lives) |
| Home Assistant | ⌂ | connexion permanente | un jeton longue durée |

---

## Discord (bot)

**Ce qu'il fait.** Un message qui mentionne ton bot ou toi, ou n'importe quel message d'un salon que
tu suis : « 💬 #général · Léa : salut @toi ! ». Une mention compte comme « à voir ». En option, Pilou
poste dans un salon de sortie quand une IA t'attend, qu'une quête est réussie ou qu'il évolue.

**Ce qu'il lit.** Les messages des serveurs où *tu* as invité le bot, par la passerelle officielle
(Gateway v10 : battements, reprise de session, reconnexion progressive). Le contenu est tronqué à
140 caractères ; case *Masquer le contenu des messages* pour n'avoir que le salon et l'auteur.

> **Jamais de selfbot.** Pilou se connecte avec un *bot*, jamais avec ton compte personnel :
> automatiser un compte utilisateur est interdit par Discord et peut le faire bannir. Ne colle
> jamais ton propre jeton de compte.

**L'activer.**

1. [discord.com/developers/applications](https://discord.com/developers/applications) → *New
   Application* (nom : Pilou).
2. *Bot* → *Reset Token* → copie le jeton dans **Jeton du bot**.
3. Toujours dans *Bot*, coche **Message Content Intent** (sinon Discord coupe la connexion, code 4014).
4. *OAuth2 → URL Generator* : scope `bot`, permissions *View Channels*, *Read Message History* et, pour
   la sortie, *Send Messages*. Ouvre l'URL et invite le bot sur ton serveur.
5. Discord → Paramètres → Avancés → **Mode développeur**. Clic droit sur toi → *Copier l'identifiant*
   → **Ton ID Discord** (pour tes mentions) ; clic droit sur un salon → *Copier l'identifiant* →
   **Salons suivis (IDs)** (séparés par des virgules) ou **Salon de sortie (ID)**.
6. *Tester le salon de sortie* poste un message d'essai.

**Limites.** Un message toutes les 3 s au plus vers la sortie ; réponse 429 de Discord respectée
(`retry_after`). Les mentions (`@everyone`, rôles) sont neutralisées dans ce que Pilou poste.

## GitHub

**Ce qu'il fait.** « 👀 Revue demandée · dépôt », « @ Mentionné », « 💬 Commentaire », CI de tes
branches « ✕ CI rouge » (à voir) ou « ✓ CI verte » (quête *tests*), et « ✦ PR fusionnée » qui fait
la fête à Pilou.

**Ce qu'il lit.** `GET /notifications` (revues demandées, mentions, commentaires, CI) et la recherche
de tes PR fusionnées des 7 derniers jours, toutes les 2 minutes, avec `If-None-Match` : quand rien n'a
bougé, GitHub répond 304 et rien n'est décompté de ton quota. Le premier relevé ne fait qu'un point de
départ (pas d'avalanche à l'activation).

**L'activer.**

1. [github.com/settings/tokens](https://github.com/settings/tokens) → *Generate new token (classic)*.
2. Cases `notifications` et `repo` (ou `public_repo` si tes dépôts sont publics) ; une date
   d'expiration.
3. Colle-le dans **Jeton personnel**. Coche ou décoche revues, commentaires, CI, fusions.

Pour la CI, GitHub doit t'envoyer ces notifications : Settings → Notifications → *Actions* →
« Notify me » sur *Failed workflows only* ou tout.

## Mail

**Ce qu'il fait.** Pilou facteur : il enfile sa casquette, « ✉ Léa Martin — Réunion demain ». Un
expéditeur important (filtre facultatif : adresses ou domaines) compte comme « à voir » ; case
*Seulement les importants*.

**Ce qu'il lit.** IMAP sur TLS (port 993) : `EXAMINE INBOX` (lecture seule : **rien n'est marqué
lu**), `UID SEARCH UNSEEN`, puis pour chaque nouveau mail `BODY.PEEK[HEADER.FIELDS (FROM SUBJECT)]`
— l'expéditeur et le sujet, **jamais le corps**. Toutes les 3 minutes, au plus 5 mails par relevé. Au
premier relevé, un seul résumé (« 📬 4 mails non lus »). Case *Masquer le sujet*.

**L'activer.** Avec un **mot de passe d'application**, jamais ton mot de passe principal :

- **Gmail** : active la validation en deux étapes, puis
  [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords). Serveur
  `imap.gmail.com`.
- **iCloud** : [account.apple.com](https://account.apple.com) → Connexion et sécurité → Mots de passe
  d'app. Serveur `imap.mail.me.com`.
- **Fastmail** : Paramètres → Mots de passe et sécurité → Mots de passe d'application.
  `imap.fastmail.com`.
- **Outlook.com / Microsoft 365** : Microsoft a coupé l'IMAP par mot de passe (OAuth seulement) ;
  seuls certains comptes professionnels l'autorisent encore.

Remplis **Serveur IMAP**, **Port** (993), **Adresse mail** et **Mot de passe d'application**.

## Agenda

**Ce qu'il fait.** 5 minutes avant une réunion (2, 5, 10 ou 15 au choix) : « ▦ Dans 5 min —
Point d'équipe ». Pendant la réunion, Pilou se cache comme pendant une visio (réglage *Cacher pendant
les visios* des Activités, et case *Se cacher pendant les réunions*). Si tu es devant ton PC quand
elle commence, la quête **« Sois à l'heure à N réunions »** avance.

**Ce qu'il lit.** Le fichier ICS de ton agenda, relu toutes les 30 minutes : `VEVENT`, `DTSTART` et
`DTEND` avec fuseau (`TZID`, noms IANA ou Windows), heure UTC ou flottante, `DURATION`, récurrences
simples `RRULE` quotidiennes et hebdomadaires (`INTERVAL`, `COUNT`, `UNTIL`, `BYDAY`), `EXDATE`,
occurrences déplacées (`RECURRENCE-ID`), annulations. Une réunion hebdomadaire de 9 h reste à 9 h
après le changement d'heure. Les journées entières ne sont pas des réunions.

**L'activer.** Le lien est secret (quiconque l'a lit ton agenda) : il est chiffré comme un mot de passe.

- **Google Agenda** : Paramètres → ton agenda → *Intégrer l'agenda* → **Adresse secrète au format
  iCal**.
- **Outlook** : Paramètres → Calendrier → Calendriers partagés → *Publier un calendrier* → lien ICS.
- **iCloud** : partage public de l'agenda → lien `webcal://` (accepté tel quel).

## Spotify

**Ce qu'il fait.** Le morceau en cours : Pilou met ses écouteurs, danse et dit « ♪ titre — artiste ».
Il danse au **vrai tempo** du morceau quand Spotify le donne, sinon au niveau sonore comme avant.

**Ce qu'il lit.** `GET /me/player/currently-playing` toutes les 20 s (portées
`user-read-currently-playing` et `user-read-playback-state`, rien d'autre). Le tempo vient de
`/audio-features`, que Spotify refuse aux apps créées depuis fin 2024 : Pilou s'en passe alors.

**L'activer.** Connexion OAuth « PKCE » : aucun secret d'application sur le PC.

1. [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) → *Create app* (API :
   Web API).
2. **Redirect URI** : `http://127.0.0.1:47822/callback` (le même port que le réglage *Port de
   retour*) → *Save*.
3. Copie le **Client ID** (pas le secret).
4. *Se connecter à Spotify* : le navigateur s'ouvre, tu acceptes, Pilou reçoit la réponse sur
   127.0.0.1 et garde le jeton de rafraîchissement, chiffré.

Une app en mode développement ne sert qu'aux comptes ajoutés dans *User Management*.

## Twitch

**Ce qu'il fait.** « ▶ ZEvent est en live — Just Chatting · Marathon », au passage hors ligne → en
live seulement.

**Ce qu'il lit.** `GET /helix/streams` pour tes chaînes (100 au plus) toutes les 3 minutes, avec un
jeton d'application : aucun compte Twitch n'est connecté.

**L'activer.**

1. [dev.twitch.tv/console](https://dev.twitch.tv/console) → *Register Your Application* (OAuth
   Redirect URL : `http://localhost` ; catégorie *Application Integration*).
2. Copie le **Client ID**, puis *New Secret* → **Client secret**.
3. **Chaînes suivies** : leurs noms (`twitch.tv/<nom>`), séparés par des virgules.

## YouTube

**Ce qu'il fait.** « ▷ Nouvelle vidéo · Ma chaîne — titre » ; avec une clé d'API, « ▷ Ma chaîne
est en live ».

**Ce qu'il lit.** Le flux RSS public de chaque chaîne (`/feeds/videos.xml`, sans clé, toutes les
10 minutes, 15 chaînes au plus). Les lives passent par l'API Data v3 (`search?eventType=live`), qui
coûte 100 unités de quota sur 10 000 par jour : Pilou ne la consulte qu'une fois par heure, pour les
3 premières chaînes.

**L'activer.**

1. Identifiant de chaîne : page de la chaîne → *À propos* → *Partager la chaîne* → *Copier l'ID de la
   chaîne* (`UC…`). Écris-les dans **Chaînes suivies**.
2. Facultatif, pour les lives : [console.cloud.google.com](https://console.cloud.google.com) →
   nouveau projet → *YouTube Data API v3* → *Activer* → *Identifiants* → *Créer une clé d'API*
   (restreins-la à cette API) → **Clé d'API**.

## Home Assistant

**Ce qu'il fait.** Une entité choisie change d'état : « 🏠 Porte d'entrée — ouvert », « 🏠 Lave-linge
— terminé ». Les simples mises à jour d'attributs ne disent rien.

**Ce qu'il lit.** L'API WebSocket locale (`/api/websocket`) : authentification, puis
`subscribe_events` sur `state_changed`, filtré sur tes entités. Connexion permanente, reprise
progressive en cas de coupure. Rien ne sort de chez toi.

**L'activer.**

1. **Adresse** : par exemple `http://homeassistant.local:8123` (`https://…` donne `wss://`).
2. Home Assistant → ton profil → *Sécurité* → **Jetons d'accès longue durée** → *Créer un jeton*.
3. **Entités suivies** : leurs ID (`binary_sensor.porte_entree`, `sensor.lave_linge_etat`…), séparés
   par des virgules — Paramètres → Appareils et services → Entités.

---

## Téléphone : carte « Nouvelles »

Les 5 derniers messages et notifications des connecteurs (pas la météo, qui a sa carte) arrivent sur
l'Accueil de l'app Android, par le relais chiffré. Fenêtre des connecteurs → *Téléphone : nouvelles* :
*Envoyer au téléphone* (coché par défaut) et *Titre seulement* pour ne pas y faire passer le contenu.
La carte reste cachée tant qu'il n'y a rien.

## Écrire un connecteur

Un fichier `Connecteurs/<Nom>.cs`, une classe qui dérive de `Connecteur` : `Id`, `Nom`,
`Description`, `Signe`, `Aide`, `Reglages` (un réglage `Secret` part au coffre DPAPI ; `Visible:
false` pour un état interne), `Manque` (ce qui manque pour démarrer), puis `Sonder` (relevé à
`Intervalle`) ou `Ecouter` (`Mode = Ecoute`, relancée si elle s'arrête). `ctx.Emettre(new
EvenementPilou(...))` pour parler ; `Donnees` : `quete` (clé de quête), `tenue` (tenue prêtée
10 s), `humeur` = `fete`. Ajoute-le dans `FenetreConnecteurs.DemarrerConnecteurs` et teste son
protocole sur des réponses enregistrées (`tests/ConnecteursVague2Tests.cs`). Voir aussi
[API.md](API.md).
