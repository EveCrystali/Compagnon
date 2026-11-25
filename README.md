# Pilou — le compagnon de tes IA de code

Une petite goutte d'encre bleue en pixels vit sur le bas de ton écran, au premier plan. Elle suit
tes sessions **Claude Code** et **Codex** (et tout outil que tu y branches). Une bulle te dit
lesquelles réfléchissent, lesquelles ont fini et lesquelles t'attendent. Elle joue aussi (étoile
filante, bulles, tape m'en cinq), gagne de l'XP et des niveaux, et débloque accessoires, couleurs
et titres.

```
 ❗ Claude · refonte-auth     attend ton autorisation
 ◐ Codex · mon-api            shell · 12 s
 ✓ Claude · docs              fini · il y a 3 min
```

## Installer (Windows 10/11)

Dans PowerShell :

```powershell
irm https://raw.githubusercontent.com/EveCrystali/Compagnon/main/installer.ps1 | iex
```

Rien d'autre à installer (.NET est inclus). Dépôt privé : télécharger `installer.ps1` et
`PilouBureau.zip` depuis la page des releases (connecté à GitHub), les mettre dans le même dossier,
puis clic droit sur `installer.ps1` → Exécuter avec PowerShell ; ou, avec `gh` connecté, lancer le
script tel quel. L'installateur pose l'overlay dans
`%USERPROFILE%\.claude\compagnon\bureau\`, ajoute le mod si Claude Code est là, branche Codex s'il est
là, et lance Pilou avec Windows. Le relancer met tout à jour. Options : `-SansCodex`, `-SansClaude`,
`-SansDemarrage` (télécharger le script, puis `.\installer.ps1 -SansCodex`).

À la main, si tu préfères :

```powershell
claude plugin marketplace add EveCrystali/Compagnon
claude plugin install compagnon@pilou --scope user
# overlay : PilouBureau.zip de la dernière release, décompressé dans %USERPROFILE%\.claude\compagnon\bureau\
```

## Sur Android

`Pilou.apk` (dans la release) : une vraie app à quatre onglets — **Accueil** (Pilou, niveau, état du
PC, sessions), **Jouer** (le jeu de tir **Chasse aux bugs**, pêche, cuisine, petits jeux),
**Collection** (carnet, recettes, récompenses, style) et **Réglages** — plus la notification
permanente, le widget et Pilou flottant par-dessus les applis. Les gains des jeux sont crédités au PC. Appairage par QR code depuis le PC (clic
droit → Intégrations → Android), échanges chiffrés de bout en bout. Détails et tableau de ce qui est
sur le téléphone : [docs/ANDROID.md](docs/ANDROID.md).

## Ce qu'il suit

| Source | Comment | Ce que dit la bulle |
|---|---|---|
| Claude Code (app, terminal) | le mod `compagnon` | titre de la session, outil en cours, autorisation, question, fini, erreur |
| Codex (CLI, app, extension) | hooks dans `~/.codex/hooks.json`, posés par Pilou | `Codex · dossier`, outil, autorisation, fini |
| tout le reste | `PilouBureau.exe --signal …` ou un fichier JSON | ce que l'outil signale |

Brancher un autre logiciel (Cursor, Gemini CLI, un script, ta CI) : [docs/BRANCHER.md](docs/BRANCHER.md).

## Clic droit sur Pilou

- **Réglages** : taille, bulle détaillée ou compacte, thème, accessoire, couleur, promenade, jeux ;
- **Pêcher, Cuisiner, Carnet de pêche, Livre de recettes** : clique sur le bouchon quand ça mord
  (sinon Pilou ferre seul, avec bien moins de chance) ; 23 prises en cinq raretés, 30 recettes et des
  plats inventés à chaque fournée (`apps/PilouBureau/Butin.cs`) ;
- **Niveaux** : ils **ouvrent l'accès** — jeux (pêche niveau 2, tape m'en cinq 3, cuisine 4, Chasse aux
  bugs 5), objets de la boutique (chacun a son niveau), stades d'évolution — et chaque niveau gagné
  rapporte des pièces d'or (20 + 5 × niveau). Les titres restent liés au niveau (honorifiques).
  Courbe : xp(n) = 25·(n−1)² (niveau 10 ≈ 2 000 xp, 25 ≈ 14 400, 50 ≈ 60 000) ; le niveau déjà
  atteint est gardé (« niveau acquis », partagé entre appareils), on ne redescend jamais.
  `apps/PilouBureau/Progression.cs` ;
- **Évolution** : Pilou grandit — Gouttelette (niveaux 1–9), Pilou (10–24), Pilou Nimbus (25–39), Pilou
  Astral (40+), noms provisoires. L'évolution se joue au premier lancement après le palier ; une
  *pierre de calme* (boutique) la retient ; *Forme affichée* choisit parmi les stades atteints ;
- **Quêtes** : 3 du jour (minuit), 3 de la semaine (lundi), 1 du mois, tirées pour chaque appareil
  (pêche, cuisine, jeux, caresses, présence, et, une fois vus : tours Claude/Codex, commits, tests,
  score de Chasse aux bugs, activités). Elles rapportent des **pièces d'or (po)** et un peu d'XP ; les
  trois du jour ouvrent un coffre, les jours d'affilée font une série. `apps/PilouBureau/Quetes.cs` ;
- **Boutique…** (gratuite, aucune vraie monnaie) : offres du jour (4 objets, un en promo), chapeaux,
  lunettes, écharpe, cape, objets à la main, compagnons, effets, couleurs, et les anciennes récompenses
  (accessoires, couleurs, traînée, canne dorée, marmite en cuivre). Rien de ce qui était déjà gagné
  n'est perdu : à la mise à jour, tout ce que le niveau avait débloqué passe dans l'inventaire.
  Pièces, objets et tenue sont partagés dans le groupe d'appareils. `apps/PilouBureau/Boutique.cs` ;
- **Partager l'XP entre PC…** : un dossier commun (OneDrive, partage réseau) ; chaque PC y écrit son
  fichier, le total fait les niveaux ;
- **Intégrations → Partager l'XP entre mes appareils** (sans dossier commun : PC perso et PC de
  travail, téléphone) : un code de groupe de 16 caractères, le même que celui du téléphone. Sur un
  autre PC : *Rejoindre un groupe* et taper le code. Chaque appareil publie son propre compteur d'XP,
  chiffré, sur le relais ntfy (à chaque gain, au démarrage, puis toutes les heures) et garde la plus
  grande valeur reçue de chacun des autres ; le niveau se calcule sur la somme. Un PC vu à la fois par
  le dossier et par le relais compte une fois ; l'XP gagnée dans l'atelier du téléphone compte une
  fois même si plusieurs PC l'ont reçue. *Appareils du groupe* : nom, XP, vu il y a… ; si le relais est
  bloqué (proxy d'entreprise), Pilou le dit (« relais injoignable ») ;
- **Intégrations** : brancher ou débrancher Codex · statut Discord « Joue à Pilou » (niveau, IA au
  travail) · me prévenir sur mon téléphone (webhook Discord, Slack ou ntfy) quand une IA attend
  depuis 30 s ou a fini un long travail, si je suis loin du PC ;
- **Démarrer avec Windows**, se cacher 10 min, quitter.

Pilou vit sans Claude : il garde son XP lui-même et joue même si aucune IA ne tourne.

## Mises à jour

Rien à faire. Chaque fusion sur `main` publie une release (`v0.9.<n>`) avec `version.json`.
- **PC** : une minute après le démarrage puis chaque jour, Pilou regarde la dernière release ; s'il y
  a du neuf, il la télécharge, met aussi à jour le mod Claude, et se relance (« nouvelle version… »
  dans sa bulle). Clic droit → *Version* : chercher maintenant, ou couper l'automatique.
- **Téléphone** : une fois par jour, l'app vérifie ; une notification « Pilou 0.9.n est disponible »,
  un appui, et Android demande de confirmer la mise à jour (la première fois, il faut autoriser Pilou
  à installer des applis). Bouton « Chercher une mise à jour » dans l'app.

À la main : relancer la ligne d'installation, ou `claude plugin marketplace update pilou` puis
`claude plugin update compagnon@pilou --scope user` et `/reload-plugins`.

## Pour contribuer

- `plugins/compagnon` : le mod Claude Code (TypeScript) — tests : `claude plugin test plugins/compagnon` ;
- `apps/PilouBureau` : l'overlay (WPF, .NET 9) — tests de la logique, sur tout OS :
  `dotnet test apps/PilouBureau/tests` ; compiler depuis Linux ou macOS :
  `dotnet build apps/PilouBureau -p:EnableWindowsTargeting=true` ;
- `android/` : l'app Android (Java, sans bibliothèque) — construite par GitHub Actions ;
- une release : fusionner sur `main` (ou pousser une étiquette `v…`) ; GitHub Actions fabrique
  `PilouBureau.zip`, `Pilou.apk`, `installer.ps1` et `version.json`.

Détail des comportements : [plugins/compagnon/README.md](plugins/compagnon/README.md).
