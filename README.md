# Pilou — compagnon pour Claude Code

Un petit compagnon en pixel art qui vit sur le bas de l'écran, au premier plan, et suit toutes tes
sessions Claude Code : une bulle dit lesquelles réfléchissent, lesquelles ont fini et lesquelles
t'attendent. Il joue aussi (étoile filante, bulles, tape m'en cinq), gagne de l'XP et des niveaux.

Deux morceaux :
- `plugins/compagnon` : le mod Claude Code (état de chaque session, XP, widget de l'app) ;
- `apps/PilouBureau` : l'overlay Windows (WPF, .NET 9) qui dessine Pilou par-dessus tout.

## Installer (Windows)

```powershell
claude plugin marketplace add EveCrystali/pilou-compagnon
claude plugin install compagnon@pilou --scope user
```

Overlay : télécharger `PilouBureau.zip` de la dernière release et le décompresser dans
`%USERPROFILE%\.claude\compagnon\bureau\` (le mod le lance au démarrage de chaque session). Il faut le
.NET 9 Desktop Runtime. Ou le fabriquer depuis le dépôt :

```powershell
dotnet publish apps/PilouBureau -c Release -o "$env:USERPROFILE\.claude\compagnon\bureau"
```

## Mettre à jour

```powershell
claude plugin marketplace update pilou
claude plugin update compagnon@pilou --scope user
```

puis `/reload-plugins` dans Claude Code ; pour l'overlay, la nouvelle release (ou `dotnet publish`).

Détail des comportements et options : `plugins/compagnon/README.md`.
