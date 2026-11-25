# Pilou — compagnon pour Claude Code

Un petit compagnon en pixel art qui vit sur le bas de l'écran, au premier plan, et suit toutes tes
sessions Claude Code : une bulle dit lesquelles réfléchissent, lesquelles ont fini et lesquelles
t'attendent. Il joue aussi (étoile filante, bulles, tape m'en cinq), gagne de l'XP et des niveaux.

Deux morceaux :
- `plugins/compagnon` : le mod Claude Code (état de chaque session, XP, widget de l'app) ;
- `apps/PilouBureau` : l'overlay Windows (WPF, .NET 9) qui dessine Pilou par-dessus tout.

## Installer (Windows)

```powershell
claude plugin marketplace add EveCrystali/Compagnon
claude plugin install compagnon@pilou --scope user
```

Overlay : télécharger `PilouBureau.zip` de la dernière release et le décompresser dans
`%USERPROFILE%\.claude\compagnon\bureau\` (le mod le lance au démarrage de chaque session). Il faut le
.NET 9 Desktop Runtime. Ou le fabriquer depuis le dépôt :

```powershell
dotnet publish apps/PilouBureau -c Release -o "$env:USERPROFILE\.claude\compagnon\bureau"
```

## Sans Claude, sur un autre PC

L'overlay vit seul : il garde lui-même l'XP (profil `profil-<PC>.json`) et joue même quand Claude
est fermé ou absent ; seule la bulle de statut des sessions a besoin du mod. Clic droit :
- **Démarrer avec Windows** : il se lance à l'ouverture de session (clé Run de l'utilisateur) ;
- **Partager l'XP entre PC…** : choisir un dossier commun (OneDrive, partage réseau). Chaque PC y
  écrit son propre fichier, le total est la somme : les niveaux sont les mêmes partout.

## Récompenses

Catalogue par niveau dans `apps/PilouBureau/Recompenses.cs` (menu clic droit « Récompenses ») :
accessoires, couleurs (bleu nuit 6, ambre 8, argent 10, aurore 12), titres, traînée d'étoiles (9).
Il s'allonge à chaque version.

## Mettre à jour

```powershell
claude plugin marketplace update pilou
claude plugin update compagnon@pilou --scope user
```

puis `/reload-plugins` dans Claude Code ; pour l'overlay, la nouvelle release (ou `dotnet publish`).

Détail des comportements et options : `plugins/compagnon/README.md`.
