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

`Pilou.apk` (dans la release) : notification permanente avec l'état des sessions, widget d'écran
d'accueil, et Pilou flottant par-dessus les applis. Appairage par QR code depuis le PC (clic droit →
Intégrations → Android), état chiffré de bout en bout. Détails : [docs/ANDROID.md](docs/ANDROID.md).

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
- **Récompenses** : tout le catalogue jusqu'au niveau 50 (`apps/PilouBureau/Recompenses.cs`) : titres,
  accessoires (chapeau de pêcheur, toque, tablier…), couleurs, canne dorée, marmite en cuivre ;
- **Partager l'XP entre PC…** : un dossier commun (OneDrive, partage réseau) ; chaque PC y écrit son
  fichier, le total fait les niveaux ;
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
