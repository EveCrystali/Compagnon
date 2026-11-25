# Brancher un logiciel sur Pilou

Pilou ne connaît qu'une chose : des fichiers `etat-*.json` dans `%USERPROFILE%\.claude\compagnon\`.
Chaque fichier est une session, une ligne de la bulle. Le mod de Claude Code en écrit un par session ;
tout autre logiciel peut en écrire aussi, de trois façons, de la plus simple à la plus libre.

| Entrée | Pour qui | Effort |
|---|---|---|
| hooks JSON (`--signal <source>` sur l'entrée standard) | Codex, Cursor, Gemini CLI, tout outil à hooks « façon Claude Code » | une ligne de config |
| ligne de commande (`--signal <source> <événement>`) | scripts, builds, CI, tâches planifiées | une commande |
| fichier d'état écrit à la main | une extension, un bot, un autre langage | le format ci-dessous |

## 1. Codex : déjà fait

Clic droit sur Pilou → **Intégrations → Codex : brancher** (ou l'installateur, qui le fait tout seul).
Pilou ajoute à `~/.codex/hooks.json` une commande par événement (`SessionStart`, `UserPromptSubmit`,
`PreToolUse`, `PermissionRequest`, `PostToolUse`, `Stop`, `SessionEnd`), asynchrone : Codex n'attend
jamais Pilou. Les hooks qui étaient déjà là restent ; une copie de l'ancien fichier est gardée dans
`hooks.json.avant-pilou`. Codex peut demander une fois de passer en revue les nouveaux hooks
(`/hooks`) : accepter ceux de Pilou.

Dans la bulle, les sessions Codex portent leur nom : `◐ Codex · mon-api · shell · 12 s`.

## 2. Un autre outil à hooks

Toute commande qui reçoit sur son entrée standard un JSON avec `hook_event_name` (et de préférence
`session_id`, `cwd`, `tool_name`) est comprise :

```
"C:\Users\<toi>\.claude\compagnon\bureau\PilouBureau.exe" --signal <source>
```

`<source>` est le nom affiché (`cursor`, `gemini`, `aider`…). Noms d'événements reconnus, quelle
que soit la casse : `SessionStart` · `UserPromptSubmit`, `beforeSubmitPrompt`, `BeforeAgent` ·
`PreToolUse`, `BeforeTool`, `beforeShellExecution`, `beforeMCPExecution` · `PostToolUse`,
`AfterTool`, `afterShellExecution`, `afterFileEdit` · `PermissionRequest`, `Notification`
(`permission_prompt`) · `Stop`, `AfterAgent` · `SessionEnd`. Les autres sont ignorés.

Recettes à adapter (formats de ces outils non vérifiés ici : regarder leur documentation de hooks) :
- **Cursor** (`~/.cursor/hooks.json`) : les événements `beforeSubmitPrompt`, `beforeShellExecution`,
  `afterShellExecution`, `stop`, chacun avec `{"command": "\"…\\PilouBureau.exe\" --signal cursor"}`.
- **Gemini CLI** (`~/.gemini/settings.json`, clé `hooks`) : `BeforeAgent`, `BeforeTool`, `AfterTool`,
  `AfterAgent`, `SessionEnd`, avec la même commande et `--signal gemini`.

Ce qui marche pour un outil, une fois essayé, mérite une entrée dans `Integrations.cs` (bouton
« brancher » comme pour Codex) : les PR sont bienvenues.

## 3. Ligne de commande (scripts, builds, CI)

```powershell
$pilou = "$env:USERPROFILE\.claude\compagnon\bureau\PilouBureau.exe"
& $pilou --signal build tour --id=nuit --libelle="Build nocturne"   # ◐ Build · Build nocturne · réfléchit
& $pilou --signal build outil tests --id=nuit                       # ◐ … · tests · 3 s
& $pilou --signal build fin --id=nuit                               # ✓ … · vient de finir (Pilou salue)
& $pilou --signal build erreur --id=nuit                            # ✕ … · erreur (Pilou grimace)
& $pilou --signal build permission --id=nuit                        # ❗ … attend ton autorisation
& $pilou --signal build xp 10 --id=nuit                             # +10 xp (50 au plus)
& $pilou --signal build fermeture --id=nuit                         # la ligne disparaît
```

Événements : `ouverture`, `tour`, `outil <nom>`, `outilfini`, `permission`, `question`, `fin`,
`erreur`, `interrompu`, `xp <n>`, `fermeture`. `--id` distingue plusieurs sessions d'une même
source ; `--libelle` donne le texte de la ligne. `ouverture` et `tour` lancent Pilou s'il dort.

Exemple : prévenir quand une longue commande finit.

```powershell
function Pilou-Suivre([string]$nom, [scriptblock]$bloc) {
    & $pilou --signal terminal tour --id=$nom --libelle=$nom
    try { & $bloc; & $pilou --signal terminal fin --id=$nom }
    catch { & $pilou --signal terminal erreur --id=$nom; throw }
}
Pilou-Suivre 'migration' { dotnet ef database update }
```

## 4. Le fichier d'état (format v3)

`etat-<source>-<id>.json`, écrit d'un bloc (fichier temporaire puis renommage) :

| Champ | Sens |
|---|---|
| `v` | 3 |
| `session` | identifiant unique, `<source>-<id>` |
| `source` | `claude`, `codex`… (affiché devant le libellé sauf pour Claude) |
| `t` | dernière écriture, ms depuis 1970 (UTC) |
| `ttl` | durée de vie sans nouvelle écriture, en ms (Claude : 90 000, republie toutes les 30 s ; autres : 6 h) |
| `libelle` | texte de la ligne (dossier, titre) |
| `enTour` | en train de travailler |
| `debutTour`, `finTour` | début et fin du dernier tour, ms |
| `finRaison` | `""` fini, `interrompu`, `erreur` |
| `attente` | `""`, `permission`, `question` : on attend l'humain |
| `outil`, `debutOutil`, `outilRev` | outil en cours, son début, compteur (+1 à chaque outil) |
| `humeur`, `rev` | humeur passagère (`grimace`, `fete`, `soulage`) et compteur (+1 pour la rejouer) |
| `xp` | XP cumulée de cette session : Pilou crédite chaque hausse |

Supprimer le fichier retire la session de la bulle.

## Sortir de l'écran

- **Discord, statut** : Intégrations → *Discord : statut « Joue à Pilou »*. Il faut l'identifiant
  d'une application Discord (discord.com/developers → New Application, nommée « Pilou », avec une
  image `pilou` dans Rich Presence → Art Assets). Un seul identifiant sert à tout le monde : le mettre
  dans `Reglages.DiscordAppParDefaut` pour que les autres n'aient rien à faire. Rien ne sort de la
  machine sauf vers l'app Discord locale ; les noms de sessions ne sont montrés que si on coche l'option.
- **Téléphone** : Intégrations → *Me prévenir sur mon téléphone…* : un webhook Discord (salon à soi),
  Slack, ou `https://ntfy.sh/<sujet>`. Un message quand une IA attend depuis 30 s, ou a fini un travail
  de plus de 2 min — par défaut seulement si tu n'as pas touché au PC depuis 30 s.

## Pistes

Teams / Outlook (Pilou s'écarte pendant une réunion), état de la CI GitHub, VS Code (tâches,
débogueur), Spotify (il danse), minuteur Pomodoro, un « Pilou d'équipe » sur Discord qui montre les
compagnons des amis. Chaque piste passe par l'une des trois entrées ci-dessus.
