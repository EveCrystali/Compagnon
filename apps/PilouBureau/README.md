# PilouBureau

Overlay WPF de Pilou : il dessine le compagnon en pixel art sur le bas de l'écran, lit les états
de sessions dans `%USERPROFILE%\.claude\compagnon\etat-*.json` et porte les intégrations (Codex,
Discord, webhook). Comportements : `plugins/compagnon/README.md` § Pilou de bureau ; entrées et
format : `docs/BRANCHER.md`.

| Fichier | Rôle |
|---|---|
| `Program.cs` | point d'entrée : overlay, `--signal`, `--brancher` / `--debrancher` |
| `Etats.cs` | format d'état v3, choix de la session suivie |
| `Statut.cs` | lignes de la bulle |
| `Signal.cs` | événements d'autres logiciels → état |
| `Integrations.cs` | branchement Codex (`~/.codex/hooks.json`) |
| `Discord.cs` | statut Discord (Rich Presence), webhook |
| `FenetrePilou.cs`, `FenetreIntegrations.cs`, `Jeux.cs`, `Scene.cs`, `Pixels.cs` | fenêtre, dessin, jeux |
| `tests/` | tests xunit de la logique sans WPF |
