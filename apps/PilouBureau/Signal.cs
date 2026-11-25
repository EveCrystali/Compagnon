using System.Diagnostics;
using System.IO;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace PilouBureau;

// Ce qu'un autre logiciel signale à Pilou. Trois entrées, un seul format :
// - le JSON d'un hook sur l'entrée standard (Codex, Claude Code, Cursor, Gemini CLI : hook_event_name) ;
// - le JSON du « notify » de Codex, passé en dernier argument ;
// - une ligne de commande : PilouBureau --signal <source> <événement> [valeur] [--id=x] [--libelle=y].
public sealed record Evenement(string Nom, string Session = "", string Outil = "", string Libelle = "", string Commande = "",
    bool Erreur = false, int Xp = 0);

public static class Signal
{
    // Une source autre que Claude n'écrit qu'à ses événements : sans nouvelles depuis 6 h, elle est oubliée.
    public const double DureeVie = 6 * 3600_000;

    private static readonly Regex Commit = new(@"\bgit\b(\s+-\S+(\s+\S+)?)*\s+commit\b", RegexOptions.Compiled);
    private static readonly Regex Tests = new(@"\b(dotnet\s+test|npm\s+(run\s+)?test|pnpm\s+test|yarn\s+test|pytest|jest|vitest|cargo\s+test|go\s+test)\b",
        RegexOptions.Compiled | RegexOptions.IgnoreCase);
    private static readonly HashSet<string> Questions = new(StringComparer.OrdinalIgnoreCase)
        { "AskUserQuestion", "ExitPlanMode", "request_user_input", "ask_user" };

    // Noms d'événements de chaque logiciel → geste de Pilou. Clés normalisées : minuscules, lettres et chiffres.
    private static readonly Dictionary<string, string> Gestes = new()
    {
        // ouverture et fermeture de session
        ["sessionstart"] = "ouverture", ["ouverture"] = "ouverture", ["start"] = "ouverture",
        ["sessionend"] = "fermeture", ["fermeture"] = "fermeture", ["finsession"] = "fermeture",
        // un tour commence (message envoyé)
        ["userpromptsubmit"] = "tour", ["beforesubmitprompt"] = "tour", ["beforeagent"] = "tour", ["tour"] = "tour", ["debut"] = "tour",
        // outils
        ["pretooluse"] = "outil", ["beforetool"] = "outil", ["beforeshellexecution"] = "outil", ["beforemcpexecution"] = "outil",
        ["beforereadfile"] = "outil", ["outil"] = "outil",
        ["posttooluse"] = "outilfini", ["aftertool"] = "outilfini", ["aftershellexecution"] = "outilfini",
        ["aftermcpexecution"] = "outilfini", ["afterfileedit"] = "outilfini", ["outilfini"] = "outilfini",
        // on attend l'humain
        ["permissionrequest"] = "permission", ["permission"] = "permission", ["question"] = "question",
        // fin de tour
        ["stop"] = "fin", ["afteragent"] = "fin", ["agentturncomplete"] = "fin", ["fin"] = "fin", ["fini"] = "fin",
        ["erreur"] = "erreur", ["error"] = "erreur", ["stopfailure"] = "erreur",
        ["interrupt"] = "interrompu", ["interrompu"] = "interrompu",
        ["xp"] = "xp",
    };

    public static string Normaliser(string nom) => new string(nom.Where(char.IsLetterOrDigit).ToArray()).ToLowerInvariant();

    public static string Geste(string evenement) => Gestes.TryGetValue(Normaliser(evenement), out var g) ? g : "";

    public static string Dossier(string cwd) => cwd.Split('/', '\\').LastOrDefault(x => x != "") ?? "";

    // Identifiant sûr pour un nom de fichier : lettres et chiffres, 16 au plus.
    public static string Propre(string s, string defaut, int max = 16)
    {
        var p = new string(s.Where(char.IsAsciiLetterOrDigit).Take(max).ToArray()).ToLowerInvariant();
        return p == "" ? defaut : p;
    }

    // ---- Lecture des entrées

    public static Evenement? DepuisJson(string json)
    {
        try
        {
            using var doc = JsonDocument.Parse(json);
            var r = doc.RootElement;
            if (r.ValueKind != JsonValueKind.Object) return null;
            string S(params string[] cles)
            {
                foreach (var k in cles)
                    if (r.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.String) return v.GetString() ?? "";
                return "";
            }
            var nom = S("hook_event_name", "hookEventName", "event", "type");
            if (nom == "") return null;
            var cwd = S("cwd");
            if (cwd == "" && r.TryGetProperty("workspace_roots", out var racines) && racines.ValueKind == JsonValueKind.Array
                && racines.GetArrayLength() > 0 && racines[0].ValueKind == JsonValueKind.String)
                cwd = racines[0].GetString() ?? "";
            var commande = "";
            if (r.TryGetProperty("tool_input", out var entree) && entree.ValueKind == JsonValueKind.Object
                && entree.TryGetProperty("command", out var c))
                commande = c.ValueKind switch
                {
                    JsonValueKind.String => c.GetString() ?? "",
                    JsonValueKind.Array => string.Join(" ", c.EnumerateArray().Select(x => x.ToString())),
                    _ => "",
                };
            if (commande == "") commande = S("command");
            var outil = S("tool_name", "toolName");
            if (outil == "" && commande != "") outil = "shell";
            var statut = S("status", "reason");
            bool erreur = statut is "error" or "failed"
                || (r.TryGetProperty("tool_response", out var reponse) && EnErreur(reponse))
                || (r.TryGetProperty("tool_output", out var sortie) && EnErreur(sortie));

            var n = Normaliser(nom);
            if (n == "notification") n = S("notification_type") == "permission_prompt" ? "permissionrequest" : "";
            if (n == "stop" && statut is "aborted" or "cancelled") n = "interrupt";
            return new Evenement(n, S("session_id", "sessionId", "thread-id", "thread_id", "conversation_id"), outil, Dossier(cwd),
                commande, erreur);
        }
        catch (JsonException)
        {
            return null;
        }
    }

    private static bool EnErreur(JsonElement e)
    {
        if (e.ValueKind != JsonValueKind.Object) return false;
        foreach (var k in new[] { "exit_code", "exitCode" })
            if (e.TryGetProperty(k, out var x) && x.ValueKind == JsonValueKind.Number && x.TryGetInt32(out var code) && code != 0)
                return true;
        return (e.TryGetProperty("is_error", out var ie) && ie.ValueKind == JsonValueKind.True)
            || (e.TryGetProperty("success", out var su) && su.ValueKind == JsonValueKind.False);
    }

    public static Evenement DepuisArguments(string evenement, string valeur, string session, string libelle)
    {
        var n = Normaliser(evenement);
        if (n == "xp") return new Evenement(n, session, Libelle: libelle, Xp: int.TryParse(valeur, out var x) ? Math.Clamp(x, 0, 50) : 0);
        return new Evenement(n, session, Outil: n == "outil" ? valeur : "", Libelle: libelle);
    }

    // ---- L'événement appliqué à l'état précédent (pur : c'est ce que vérifient les tests)

    // Résultat : le nouvel état (null : rien à écrire) et s'il faut effacer la session.
    public static (EtatSession? Etat, bool Effacer) Appliquer(string source, Evenement ev, EtatSession? avant, double maintenant)
    {
        var geste = Geste(ev.Nom);
        if (geste == "") return (null, false);
        if (geste == "fermeture") return (null, true);

        var e = (avant ?? new EtatSession(ev.Session, maintenant, "repos", 0, false, "", 0, false, false, "Pilou", 1, true))
            with { Session = ev.Session, T = maintenant, Source = source, Ttl = DureeVie };
        if (ev.Libelle != "") e = e with { Libelle = ev.Libelle };
        EtatSession Humeur(EtatSession x, string h, int xp = 0) => x with { Humeur = h, Rev = x.Rev + 1, Xp = x.Xp + xp };

        e = geste switch
        {
            "ouverture" => e,
            "tour" => e with { EnTour = true, DebutTour = maintenant, Attente = "", Outil = "", FinRaison = "" },
            "outil" => e with
            {
                EnTour = true,
                DebutTour = e.EnTour && e.DebutTour > 0 ? e.DebutTour : maintenant,
                Outil = ev.Outil == "" ? "outil" : ev.Outil,
                OutilRev = e.OutilRev + 1,
                DebutOutil = maintenant,
                Attente = Questions.Contains(ev.Outil) ? "question" : "",
            },
            "outilfini" => Finir(e with { Outil = "", Attente = "" }),
            "permission" => e with { Attente = "permission", DebutOutil = maintenant },
            "question" => e with { Attente = "question", DebutOutil = maintenant },
            "fin" when ev.Erreur => Humeur(Clore(e, "erreur"), "grimace"),
            "fin" => Humeur(Clore(e, ""), "soulage", 1),
            "erreur" => Humeur(Clore(e, "erreur"), "grimace"),
            "interrompu" => Clore(e, "interrompu"),
            "xp" => Humeur(e, "fete", ev.Xp),
            _ => e,
        };
        return (e, false);

        EtatSession Clore(EtatSession x, string raison) =>
            x with { EnTour = false, Outil = "", Attente = "", FinTour = maintenant, FinRaison = raison };

        // Outil terminé : grimace s'il a échoué, fête pour un commit ou des tests.
        EtatSession Finir(EtatSession x)
        {
            if (ev.Erreur) return Humeur(x, "grimace");
            if (Commit.IsMatch(ev.Commande)) return Humeur(x, "fete", 5) with { Commits = x.Commits + 1 };
            if (Tests.IsMatch(ev.Commande)) return Humeur(x, "fete", 2) with { Tests = x.Tests + 1 };
            return x;
        }
    }

    // ---- Écriture du fichier d'état

    public static string Chemin(string dossier, string source, string session) =>
        Path.Combine(dossier, $"etat-{source}-{Propre(session, "defaut")}.json");

    // Applique l'événement au fichier de la session ; renvoie le geste joué.
    public static string Ecrire(string dossier, string source, Evenement ev, double maintenant)
    {
        source = Propre(source, "autre");
        var id = Propre(ev.Session, "defaut");
        ev = ev with { Session = $"{source}-{id}" };
        var chemin = Chemin(dossier, source, id);
        using var verrou = new Mutex(false, $@"Local\PilouSignal-{source}-{id}");
        bool tenu;
        try
        {
            tenu = verrou.WaitOne(2000);
        }
        catch (AbandonedMutexException)
        {
            tenu = true;
        }
        try
        {
            EtatSession? avant = null;
            if (File.Exists(chemin))
            {
                try
                {
                    avant = EtatSession.Lire(File.ReadAllText(chemin));
                }
                catch (IOException)
                {
                    // illisible un instant : on repart de zéro
                }
            }
            var (etat, effacer) = Appliquer(source, ev, avant, maintenant);
            if (effacer)
            {
                File.Delete(chemin);
                return "fermeture";
            }
            if (etat is null) return "";
            Directory.CreateDirectory(dossier);
            var tmp = $"{chemin}.{Environment.ProcessId}.tmp";
            File.WriteAllText(tmp, etat.Json());
            File.Move(tmp, chemin, true);
            return Geste(ev.Nom);
        }
        finally
        {
            if (tenu) verrou.ReleaseMutex();
        }
    }

    // ---- Point d'entrée : PilouBureau --signal …

    public static int Principal(string[] args, string dossier)
    {
        try
        {
            string Option(string nom) => args.FirstOrDefault(a => a.StartsWith($"--{nom}="))?[(nom.Length + 3)..] ?? "";
            var positions = args.Where(a => !a.StartsWith("--")).ToList();
            var source = positions.ElementAtOrDefault(0) ?? "autre";
            Evenement? ev = null;
            var json = positions.Skip(1).LastOrDefault(a => a.TrimStart().StartsWith('{'));
            if (json is not null) ev = DepuisJson(json);
            else if (positions.Count >= 2)
                ev = DepuisArguments(positions[1], positions.ElementAtOrDefault(2) ?? "", Option("id"), Option("libelle"));
            else if (Console.IsInputRedirected) ev = DepuisJson(Console.In.ReadToEnd());
            if (ev is null) return 0;
            if (Option("id") != "") ev = ev with { Session = Option("id") };
            if (Option("libelle") != "") ev = ev with { Libelle = Option("libelle") };

            var geste = Ecrire(dossier, source, ev, DateTimeOffset.UtcNow.ToUnixTimeMilliseconds());
            // Un logiciel s'ouvre ou travaille et Pilou n'est pas là : il arrive.
            if (geste is "ouverture" or "tour" && !Mutex.TryOpenExisting(@"Local\PilouBureau", out _)) Lancer(dossier);
        }
        catch (Exception)
        {
            // jamais d'erreur renvoyée au logiciel qui signale : Pilou ne doit rien bloquer
        }
        return 0;
    }

    private static void Lancer(string dossier)
    {
        var exe = Environment.ProcessPath;
        if (exe is null || !OperatingSystem.IsWindows()) return;
        // ShellExecute : l'overlay n'hérite pas des tuyaux du hook (le logiciel n'attend pas sa fin).
        var info = new ProcessStartInfo(exe) { UseShellExecute = true };
        if (dossier != Defaut()) info.ArgumentList.Add(dossier);
        Process.Start(info);
    }

    public static string Defaut() =>
        Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".claude", "compagnon");
}
