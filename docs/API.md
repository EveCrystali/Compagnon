# API locale de Pilou

Pilou écoute sur **`127.0.0.1:47821`**, et seulement là : aucune autre machine du réseau ne peut le
joindre. Un script, une CI locale, un raccourci clavier ou un autre logiciel du PC peut ainsi lui
envoyer un événement (« build fini », « nouveau mail ») ou lire son état.

Réglages : clic droit sur Pilou → **Connecteurs…**, section *API locale* — l'activer ou la couper,
changer le port, **copier le jeton**, en tirer un nouveau (l'ancien cesse aussitôt de marcher).

## Règles

| Règle | Pourquoi |
|---|---|
| Écoute sur `127.0.0.1` seulement | rien n'entre depuis le réseau ; une connexion venue d'ailleurs reçoit `403` |
| En-tête `Authorization: Bearer <jeton>` obligatoire | un autre programme du PC ne parle pas à Pilou sans le jeton (`401` sinon) |
| Requête qui porte un en-tête `Origin` refusée (`403`) | une page web ouverte dans le navigateur ne peut pas viser Pilou |
| Corps de 64 Ko au plus (`413` au-delà) | |

Le jeton est tiré au hasard au premier lancement et rangé dans `reglages.json` (dossier
`%USERPROFILE%\.claude\compagnon\`). Les secrets des connecteurs (jetons d'API Discord, GitHub…) ne
vont jamais dans ce fichier : ils sont chiffrés par Windows (DPAPI, liés à ta session) dans
`secrets.bin`.

## `POST /evenements`

Envoie un événement à Pilou. Réponse `202 {"recu":true}`, ou `400 {"erreur":"…"}` si le JSON ne va pas.

```json
{
  "source": "ma-ci",
  "type": "fin",
  "titre": "Build nocturne",
  "texte": "312 tests, 0 échec",
  "gravite": 1,
  "donnees": { "duree": "4 min" }
}
```

| Champ | Obligatoire | Sens |
|---|---|---|
| `source` | oui | qui parle (lettres, chiffres, `-` ; nettoyé comme pour `--signal`) |
| `type` | oui | voir le tableau suivant |
| `titre` | oui | ce que dit la bulle (300 caractères au plus) |
| `texte` | non | détail (300 caractères au plus) |
| `gravite` | non | 0 normal, 1 important, 2 urgent (Pilou insiste, comme quand une IA attend) |
| `donnees` | non | paires texte → texte, 20 au plus |

| `type` | Ce que fait Pilou |
|---|---|
| `session` | une session de travail commence (comme `--signal tour`) |
| `attente` | quelqu'un attend ta réponse (comme une autorisation demandée) : Pilou s'agite |
| `fin` | travail fini : petite fête |
| `erreur` | ça a cassé : Pilou s'inquiète |
| `message`, `notification` | une bulle ❗ (gravité 2) ou ✉ |
| `meteo`, `activite` | réservés aux connecteurs météo et activités |

Les types `session`, `attente`, `fin` et `erreur` suivent le même chemin que `--signal` : ils
apparaissent aussi sur le téléphone et comptent pour les quêtes.

## `GET /etat`

Renvoie l'état de Pilou :

```json
{
  "nom": "Pilou", "niveau": 12, "humeur": "repos",
  "sessions": [ { "source": "claude", "libelle": "refonte", "etat": "travail" } ],
  "meteo": { "etat": "pluie", "temperature": 8, "ville": "Paris", "signe": "☂" }
}
```

`meteo` vaut `null` tant que le connecteur météo n'a reçu aucun relevé.

## `POST /diagnostics`

Erreurs et avertissements du fichier ouvert dans un éditeur (extensions Visual Studio et VS Code :
[EDITEURS.md](EDITEURS.md)). Réponse `202 {"recu":true}` (`false` si le connecteur *Éditeurs* est
coupé : rien n'est gardé), `400` si le JSON ne va pas.

```json
{ "source": "vs", "fichier": "Program.cs", "erreurs": 3, "avertissements": 2, "message": "CS1002: ; attendu" }
```

| Champ | Obligatoire | Sens |
|---|---|---|
| `source` | oui | `vs`, `vscode`… (lettres et chiffres) |
| `fichier` | non | nom du fichier actif ; un chemin est réduit au nom (ce qui suit le dernier `/` ou `\`). Vide : plus de fichier actif |
| `erreurs`, `avertissements` | non | comptes (0 par défaut) |
| `message` | non | premier message d'erreur ; chemins retirés, 160 caractères au plus, affiché seulement si la case est cochée dans Pilou |
| `ferme` | non | `true` : l'éditeur se ferme, l'état est oublié |

Pilou regroupe (2,5 s de calme, rien pendant la saisie, 20 s au moins entre deux bulles) et oublie un
éditeur muet depuis 5 min : renvoyer l'état une fois par minute suffit.

## Exemples

Le jeton se copie depuis la fenêtre Connecteurs ; ci-dessous, il est dans la variable `JETON`.

**curl** (Git Bash, WSL, ou `curl.exe` sous Windows) :

```sh
curl -s -X POST http://127.0.0.1:47821/evenements \
  -H "Authorization: Bearer $JETON" -H "Content-Type: application/json" \
  -d '{"source":"build","type":"fin","titre":"Build terminé","texte":"0 erreur"}'

curl -s http://127.0.0.1:47821/etat -H "Authorization: Bearer $JETON"
```

**PowerShell** :

```powershell
$jeton = "colle-le-jeton-ici"
$entetes = @{ Authorization = "Bearer $jeton" }
$corps = @{ source = "sauvegarde"; type = "notification"; titre = "Sauvegarde finie"; gravite = 1 } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:47821/evenements -Headers $entetes `
  -ContentType "application/json; charset=utf-8" -Body ([Text.Encoding]::UTF8.GetBytes($corps))

Invoke-RestMethod -Uri http://127.0.0.1:47821/etat -Headers $entetes
```

`PilouBureau.exe --signal …` continue de marcher, sans jeton (voir [BRANCHER.md](BRANCHER.md)).

## Écrire un connecteur

Un connecteur est **un fichier C#** dans `apps/PilouBureau/` : une classe qui hérite de `Connecteur`
(`Connecteurs.cs`) et qu'on ajoute au registre dans `FenetreConnecteurs.cs` (`_registre.Ajouter(...)`).
La fenêtre Connecteurs le montre ensuite tout seule : interrupteur, état, réglages, actions, journal.

```csharp
public sealed class ConnecteurExemple : Connecteur
{
    public override string Id => "exemple";
    public override string Nom => "Exemple";
    public override string Description => "Prévient quand un compteur bouge.";
    public override string Signe => "✦";                       // signe affiché (jamais une couleur seule)
    public override ModeConnecteur Mode => ModeConnecteur.Sondage; // ou Ecoute (boucle permanente), Passif
    public override TimeSpan Intervalle => TimeSpan.FromMinutes(5);

    public override IReadOnlyList<ReglageConnecteur> Reglages { get; } = new[]
    {
        new ReglageConnecteur("adresse", "Adresse", TypeReglage.Texte, Defaut: "https://exemple.fr/api"),
        new ReglageConnecteur("jeton", "Jeton", TypeReglage.Secret, Aide: "chiffré par Windows, jamais en clair"),
        new ReglageConnecteur("frequence", "Fréquence", TypeReglage.Liste, Choix: new[] { "5 min", "15 min" }),
        new ReglageConnecteur("bulles", "Bulles", TypeReglage.Case, Defaut: "oui"),
    };

    public override string? Manque(ContexteConnecteur ctx) => ctx.Lire("jeton") == "" ? "jeton à saisir" : null;

    public override async Task Sonder(ContexteConnecteur ctx, CancellationToken ct)
    {
        var json = await ctx.Http.GetStringAsync(ctx.Lire("adresse"), ct);
        ctx.Emettre(new EvenementPilou(Id, "notification", "Le compteur a bougé"));
    }
}
```

- `ctx.Lire` / `ctx.Ecrire` : réglages ; un réglage `Secret` passe par le coffre DPAPI.
- `ctx.Emettre` : envoie un événement (bulle, humeur, quêtes, téléphone) et l'inscrit au journal.
- Une exception dans `Sonder` met le connecteur en état *erreur* (✕) sans rien casser d'autre ; le
  registre réessaie au prochain intervalle.
- `Ecouter` (mode `Ecoute`) tourne en continu (websocket, flux) ; il est relancé s'il s'arrête.
- Tests : `apps/PilouBureau/tests/ConnecteursTests.cs` (registre, coffre en mémoire, API).
