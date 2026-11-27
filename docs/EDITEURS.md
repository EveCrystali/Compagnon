# Pilou dans ton éditeur (Visual Studio, VS Code)

Une petite extension pour ton éditeur, et Pilou connaît l'état du fichier ouvert :

```
 ⚠ 3 erreurs · 2 avert. · Program.cs
```

- **Les erreurs augmentent** : petite grimace, et la ligne ci-dessus (signe ⚠, en orange).
- **Tu repasses à zéro erreur** (après en avoir eu dans ce fichier) : « ✓ propre ! · Program.cs », petit
  saut. Ça fait avancer la quête *Repasse N fichiers à zéro erreur*.
- **Que des avertissements** : « △ 2 avert. · Program.cs », en bleu.
- **Le reste du temps, il se tait** : un fichier propre où tu arrives ne lui inspire rien. Au survol de
  Pilou, une ligne discrète rappelle l'état du fichier actif.

Le signe porte le sens (⚠ erreurs, △ avertissements, ✓ propre), la couleur le double (orange, bleu ;
jamais de rouge-vert).

## La retenue

Pilou ne parle pas à chaque frappe :

| Règle | Valeur |
| --- | --- |
| Le compte (ou le fichier) doit rester stable avant d'être annoncé | 2,5 s |
| Pendant que tu tapes | rien (il attend la pause) |
| Entre deux bulles | 20 s au moins ; ce qui change entre-temps est annoncé ensuite, seulement le dernier état |
| Ce qui déclenche une bulle | un compte qui change, un changement de fichier (s'il a des erreurs ou avertissements) |
| Éditeur fermé sans prévenir | état oublié au bout de 5 min (l'extension redit l'état chaque minute tant que la fenêtre a le focus) |

Réglages côté Pilou : clic droit → **Connecteurs…** → carte **Éditeurs (Visual Studio, VS Code)** :
interrupteur, *Nom du fichier dans la bulle* (sinon « fichier actif »), *Premier message d'erreur*
(coupé par défaut, tronqué à 60 caractères).

## Installer

Les deux extensions sont dans la [dernière release](https://github.com/EveCrystali/Compagnon/releases/latest)
(entre deux releases : artefacts `pilou-vscode` et `PilouVisualStudio` du workflow *Vérifier*).

### Visual Studio 2022 (et suivant)

1. Télécharge `PilouVisualStudio.vsix`.
2. Ferme Visual Studio, double-clique sur le `.vsix` (l'installateur VSIX de Visual Studio s'ouvre),
   choisis ton installation, *Install*.
3. Relance Visual Studio. L'extension se charge en arrière-plan, sans rien ralentir.
4. Réglages : **Outils → Options → Pilou → Général** (activer, premier message, jeton, port).

Elle lit la **Liste d'erreurs** (`IErrorList`) et garde les lignes du document actif
(`DTE.ActiveDocument`), erreurs de build et IntelliSense confondues. Elle compte ce que la Liste
d'erreurs affiche : si tu y masques les avertissements (bouton *Avertissements*), Pilou ne les voit
plus non plus. Projet .NET Framework, .NET, C++ : peu importe, c'est la Liste d'erreurs qui fait foi.

### VS Code

1. Télécharge `pilou-vscode.vsix`.
2. VS Code → Extensions → `…` → **Installer depuis un VSIX…** (ou
   `code --install-extension pilou-vscode.vsix`).
3. Réglages (`pilou.*`) : `pilou.actif`, `pilou.envoyerMessage`, `pilou.jeton`, `pilou.port`.

Elle suit `vscode.languages.onDidChangeDiagnostics` et le changement d'éditeur actif, et compte les
diagnostics *Error* et *Warning* du document actif.

### Le jeton

Rien à faire en général : les deux extensions lisent le jeton de l'API locale là où Pilou le range,
`%USERPROFILE%\.claude\compagnon\reglages.json` (`Connecteurs.JetonApi`, et le port
`Connecteurs.PortApi`). Si tu en tires un nouveau, elles le relisent d'elles-mêmes. Sinon, copie-le
depuis Pilou (Connecteurs… → *Copier le jeton*) dans le réglage de l'extension.

## Ce qui est envoyé, et à qui

Seulement à **Pilou, sur ta machine** : `POST http://127.0.0.1:47821/diagnostics`, avec le jeton
(voir [API.md](API.md)). Aucune autre adresse, aucune télémétrie, aucune dépendance chargée à
l'exécution.

```json
{ "source": "vs", "fichier": "Program.cs", "erreurs": 3, "avertissements": 2 }
```

- **`fichier`** : le **nom seul**, jamais le chemin (ni le nom de la solution ou du dossier).
  Pilou recoupe de toute façon ce qui suit le dernier `/` ou `\`.
- **`message`** (facultatif) : seulement si tu coches *Premier message d'erreur* dans l'extension. Les
  chemins absolus qu'il contient (`C:\…\Foo.cs`, `/home/…/util.ts`, `\\serveur\…`) sont réduits au nom
  de fichier, avant l'envoi puis de nouveau par Pilou. Pilou ne l'affiche que si sa propre case est
  cochée.
- **Pas de code, pas de contenu de fichier**, pas de numéro de ligne.
- **Rien n'est écrit sur le disque** : Pilou garde l'état en mémoire (5 min au plus sans nouvelles) et
  note seulement ses bulles dans le journal des connecteurs (en mémoire, 50 lignes). Rien ne part vers
  le téléphone ni les sorties (Discord, webhook).
- `"ferme": true` (envoyé quand l'éditeur se ferme) efface l'état tout de suite.

Connecteur coupé dans Pilou : l'API répond `202 {"recu":false}` et ne garde rien.

## Écrire le tien

N'importe quel éditeur peut faire pareil (JetBrains, Vim, un script) : `POST /diagnostics` avec
`source` (lettres et chiffres), `fichier`, `erreurs`, `avertissements`, éventuellement `message`.
Renvoie l'état quand il change et une fois par minute ; envoie `"ferme": true` en partant.

## Construire les extensions

- VS Code : `cd integrations/vscode && npm ci && npm run compile && npm test && npm run package`
  → `pilou-vscode.vsix`.
- Visual Studio (Windows, Visual Studio ou ses Build Tools avec la charge *Développement d'extensions
  Visual Studio*) : `msbuild integrations/visualstudio/PilouVisualStudio.csproj -restore
  -p:Configuration=Release` → `integrations/visualstudio/bin/Release/PilouVisualStudio.vsix`. La partie
  sans Visual Studio (`Rapport.cs`) est testée avec Pilou (`dotnet test apps/PilouBureau/tests`).
