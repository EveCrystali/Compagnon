using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Net.Http;
using System.Reflection;
using System.Text.Json;

namespace PilouBureau;

// Mise à jour automatique : version.json de la dernière release (publiée à chaque fusion sur main).
// Un exécutable Windows en cours d'exécution ne peut pas être effacé mais peut être renommé :
// PilouBureau.exe devient PilouBureau.exe.ancien, le neuf prend sa place et se lance, l'ancien quitte.
public static class Mise
{
    public const string Depot = "EveCrystali/Compagnon";
    public static string UrlVersion => $"https://github.com/{Depot}/releases/latest/download/version.json";

    private static readonly HttpClient Http = CreerClient();

    private static HttpClient CreerClient()
    {
        var h = new HttpClient { Timeout = TimeSpan.FromMinutes(3) };
        h.DefaultRequestHeaders.UserAgent.ParseAdd("pilou-bureau");
        return h;
    }

    public sealed record Publication(string Version, string Zip);

    public static string Actuelle =>
        Assembly.GetEntryAssembly()?.GetCustomAttribute<AssemblyInformationalVersionAttribute>()?.InformationalVersion.Split('+')[0]
        ?? "0.0.0";

    // « 0.9.12 » contre « 0.9.4 » : nombre par nombre ; une préversion (« 0.8.0-beta.1 ») passe avant sa version.
    public static bool PlusRecente(string candidate, string actuelle)
    {
        static (int[] Nombres, string Suffixe) Lire(string v)
        {
            v = v.Trim().TrimStart('v', 'V');
            var tiret = v.IndexOf('-');
            var suffixe = tiret >= 0 ? v[(tiret + 1)..] : "";
            var nombres = (tiret >= 0 ? v[..tiret] : v).Split('.').Select(x => int.TryParse(x, out var n) ? n : 0).ToArray();
            return (nombres, suffixe);
        }
        var (a, sa) = Lire(candidate);
        var (b, sb) = Lire(actuelle);
        for (int i = 0; i < Math.Max(a.Length, b.Length); i++)
        {
            int x = i < a.Length ? a[i] : 0, y = i < b.Length ? b[i] : 0;
            if (x != y) return x > y;
        }
        if (sa == sb) return false;
        if (sa == "") return true;   // 0.8.0 > 0.8.0-beta.1
        if (sb == "") return false;
        return string.CompareOrdinal(sa, sb) > 0;
    }

    public static Publication? LireVersion(string json)
    {
        try
        {
            using var doc = JsonDocument.Parse(json);
            var r = doc.RootElement;
            var v = r.TryGetProperty("version", out var x) && x.ValueKind == JsonValueKind.String ? x.GetString() : null;
            var z = r.TryGetProperty("zip", out var y) && y.ValueKind == JsonValueKind.String ? y.GetString() : "PilouBureau.zip";
            return string.IsNullOrWhiteSpace(v) ? null : new Publication(v!, z ?? "PilouBureau.zip");
        }
        catch (JsonException)
        {
            return null;
        }
    }

    // Une version plus récente existe ? null : non, ou pas de réseau.
    public static async Task<Publication?> Chercher()
    {
        try
        {
            var p = LireVersion(await Http.GetStringAsync(UrlVersion));
            return p is not null && PlusRecente(p.Version, Actuelle) ? p : null;
        }
        catch (Exception e) when (e is HttpRequestException or TaskCanceledException)
        {
            return null;
        }
    }

    // Télécharge et pose la nouvelle version à côté de l'ancienne ; renvoie l'exécutable neuf à lancer.
    public static async Task<string?> Installer(Publication p)
    {
        var exe = Environment.ProcessPath;
        if (exe is null) return null;
        var dossier = Path.GetDirectoryName(exe)!;
        var url = $"https://github.com/{Depot}/releases/download/v{p.Version}/{p.Zip}";
        var tmp = Path.Combine(Path.GetTempPath(), $"PilouBureau-{p.Version}.zip");
        try
        {
            await using (var flux = await Http.GetStreamAsync(url))
            await using (var f = File.Create(tmp))
                await flux.CopyToAsync(f);
            using var zip = ZipFile.OpenRead(tmp);
            if (zip.GetEntry(Path.GetFileName(exe)) is null) return null; // archive inattendue : on ne touche à rien
            foreach (var entree in zip.Entries.Where(e => e.Name != ""))
            {
                var cible = Path.GetFullPath(Path.Combine(dossier, entree.FullName));
                if (!cible.StartsWith(dossier, StringComparison.OrdinalIgnoreCase)) continue;
                Directory.CreateDirectory(Path.GetDirectoryName(cible)!);
                if (File.Exists(cible))
                {
                    var ancien = cible + ".ancien";
                    if (File.Exists(ancien)) File.Delete(ancien);
                    File.Move(cible, ancien); // possible même pour l'exécutable en cours
                }
                entree.ExtractToFile(cible);
            }
            return exe;
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException or HttpRequestException or TaskCanceledException
                                      or InvalidDataException)
        {
            return null;
        }
        finally
        {
            try
            {
                File.Delete(tmp);
            }
            catch (IOException)
            {
                // reste dans %TEMP%
            }
        }
    }

    // Au démarrage : les restes de la version précédente.
    public static void Nettoyer()
    {
        try
        {
            var exe = Environment.ProcessPath;
            if (exe is null) return;
            foreach (var f in Directory.EnumerateFiles(Path.GetDirectoryName(exe)!, "*.ancien", SearchOption.AllDirectories))
            {
                try
                {
                    File.Delete(f);
                }
                catch (Exception e) when (e is IOException or UnauthorizedAccessException)
                {
                    // l'ancienne instance n'a pas encore fini de quitter : effacé la prochaine fois
                }
            }
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException)
        {
            // dossier en lecture seule
        }
    }

    // Le mod Claude suit : mêmes commandes que l'installateur, sans fenêtre.
    public static void MettreAJourMod()
    {
        foreach (var args in new[] { "plugin marketplace update pilou", "plugin update compagnon@pilou --scope user" })
        {
            try
            {
                // cmd /c : trouve aussi bien claude.exe que claude.cmd (installation npm).
                using var p = Process.Start(new ProcessStartInfo("cmd.exe", $"/c claude {args}") { UseShellExecute = false, CreateNoWindow = true });
                p?.WaitForExit(60_000);
            }
            catch (Exception e) when (e is System.ComponentModel.Win32Exception or InvalidOperationException)
            {
                return; // pas de cmd.exe (essai hors Windows)
            }
        }
    }
}
