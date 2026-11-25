using System.IO;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace PilouBureau;

// Branchements vers d'autres logiciels. Chacun est réversible et ne touche qu'à ce qui porte la marque de Pilou.
public static class Integrations
{
    // PilouBureau --brancher codex / --debrancher codex (installateur, ligne de commande).
    public static int Ligne(bool brancher, string logiciel)
    {
        if (!string.Equals(logiciel, "codex", StringComparison.OrdinalIgnoreCase))
        {
            Console.Error.WriteLine($"inconnu : {logiciel} (connu : codex)");
            return 2;
        }
        var exe = Environment.ProcessPath ?? "PilouBureau.exe";
        var message = brancher ? Codex.Brancher(exe) : Codex.Debrancher();
        Console.WriteLine(message);
        return 0;
    }
}

// Codex (CLI, app, extension) lit ~/.codex/hooks.json : mêmes événements que les hooks de Claude Code,
// JSON sur l'entrée standard. Pilou y pose une commande par événement, asynchrone : Codex n'attend pas.
public static class Codex
{
    private const string Marque = "--signal codex";

    // Événements suivis et s'ils peuvent tourner en tâche de fond (SessionEnd est toujours synchrone chez Codex).
    private static readonly (string Nom, bool Asynchrone)[] Evenements =
    {
        ("SessionStart", true), ("UserPromptSubmit", true), ("PreToolUse", true), ("PermissionRequest", true),
        ("PostToolUse", true), ("Stop", true), ("SessionEnd", false),
    };

    public static string Dossier =>
        Environment.GetEnvironmentVariable("CODEX_HOME") is { Length: > 0 } d
            ? d
            : Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".codex");

    public static string Fichier => Path.Combine(Dossier, "hooks.json");

    public static bool Installe => Directory.Exists(Dossier);

    public static bool Branche()
    {
        try
        {
            return File.Exists(Fichier) && File.ReadAllText(Fichier).Contains(Marque, StringComparison.Ordinal);
        }
        catch (IOException)
        {
            return false;
        }
    }

    public static string Commande(string exe) => $"\"{exe}\" {Marque}";

    // Texte du hooks.json après branchement (pur, pour les tests) : les hooks d'autrui restent intacts.
    public static string AvecPilou(string? existant, string exe)
    {
        var racine = Sans(existant);
        var hooks = racine["hooks"] as JsonObject ?? new JsonObject();
        racine["hooks"] = hooks;
        foreach (var (nom, asynchrone) in Evenements)
        {
            var groupes = hooks[nom] as JsonArray ?? new JsonArray();
            hooks[nom] = groupes;
            var handler = new JsonObject
            {
                ["type"] = "command",
                ["command"] = Commande(exe),
                ["timeout"] = 5,
                ["statusMessage"] = "Pilou",
            };
            if (asynchrone) handler["async"] = true;
            groupes.Add(new JsonObject { ["hooks"] = new JsonArray { handler } });
        }
        return racine.ToJsonString(new JsonSerializerOptions { WriteIndented = true });
    }

    // Texte du hooks.json sans Pilou ; vide si plus rien n'y reste.
    public static string SansPilou(string? existant)
    {
        var racine = Sans(existant);
        if (racine["hooks"] is JsonObject h && h.Count == 0) racine.Remove("hooks");
        return racine.Count == 0 ? "" : racine.ToJsonString(new JsonSerializerOptions { WriteIndented = true });
    }

    private static JsonObject Sans(string? existant)
    {
        JsonObject racine;
        try
        {
            racine = (string.IsNullOrWhiteSpace(existant) ? null : JsonNode.Parse(existant) as JsonObject) ?? new JsonObject();
        }
        catch (JsonException)
        {
            throw new InvalidDataException($"{Fichier} n'est pas un JSON valide : corrige-le avant de brancher Pilou.");
        }
        if (racine["hooks"] is not JsonObject hooks) return racine;
        foreach (var nom in hooks.Select(kv => kv.Key).ToList())
        {
            if (hooks[nom] is not JsonArray groupes) continue;
            foreach (var groupe in groupes.OfType<JsonObject>().ToList())
            {
                if (groupe["hooks"] is not JsonArray handlers) continue;
                foreach (var hd in handlers.OfType<JsonObject>().Where(EstPilou).ToList()) handlers.Remove(hd);
                if (handlers.Count == 0) groupes.Remove(groupe);
            }
            if (groupes.Count == 0) hooks.Remove(nom);
        }
        return racine;
    }

    private static bool EstPilou(JsonObject handler) =>
        handler["command"]?.GetValueKind() == JsonValueKind.String
        && handler["command"]!.GetValue<string>().Contains(Marque, StringComparison.Ordinal);

    public static string Brancher(string exe)
    {
        try
        {
            Directory.CreateDirectory(Dossier);
            var avant = File.Exists(Fichier) ? File.ReadAllText(Fichier) : null;
            var sauvegarde = Fichier + ".avant-pilou";
            if (avant is not null && !File.Exists(sauvegarde)) File.WriteAllText(sauvegarde, avant);
            File.WriteAllText(Fichier, AvecPilou(avant, exe));
            return "Codex branché : Pilou suit ses sessions. Si Codex te demande de passer en revue de nouveaux hooks (/hooks), accepte ceux de Pilou.";
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException or InvalidDataException)
        {
            return $"Codex non branché : {e.Message}";
        }
    }

    public static string Debrancher()
    {
        try
        {
            if (!File.Exists(Fichier)) return "Codex n'était pas branché.";
            var reste = SansPilou(File.ReadAllText(Fichier));
            if (reste == "") File.Delete(Fichier);
            else File.WriteAllText(Fichier, reste);
            return "Codex débranché.";
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException or InvalidDataException)
        {
            return $"Codex toujours branché : {e.Message}";
        }
    }
}
