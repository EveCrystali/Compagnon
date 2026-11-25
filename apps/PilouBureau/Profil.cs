using System.IO;
using System.Text.Json;

namespace PilouBureau;

// L'XP de Pilou, gardée par l'overlay lui-même (Claude n'est pas nécessaire).
// Chaque PC écrit SON fichier profil-<machine>.json dans le dossier de partage ; le total est la
// somme de tous les fichiers du dossier. Deux PC n'écrivent donc jamais le même fichier.
public sealed class Profil
{
    public string Machine { get; set; } = Environment.MachineName;
    public int Xp { get; set; }
    // Dernière XP vue côté Claude (mod) sur ce PC : seul l'écart est ajouté.
    public int XpClaudeVue { get; set; } = -1;
    public int JeuxGagnes { get; set; }
    public int Caresses { get; set; }
    public DateTime MisAJour { get; set; } = DateTime.Now;

    private static readonly JsonSerializerOptions Options = new() { WriteIndented = true };

    public static string Chemin(string dossier) => Path.Combine(dossier, $"profil-{Environment.MachineName}.json");

    public static Profil Lire(string dossier)
    {
        try
        {
            var c = Chemin(dossier);
            if (File.Exists(c)) return JsonSerializer.Deserialize<Profil>(File.ReadAllText(c), Options) ?? new();
        }
        catch (Exception e) when (e is IOException or JsonException or UnauthorizedAccessException)
        {
            // illisible (synchronisation en cours) : on repart d'un profil vide, réécrit au prochain gain
        }
        return new();
    }

    public void Ecrire(string dossier)
    {
        try
        {
            Directory.CreateDirectory(dossier);
            MisAJour = DateTime.Now;
            var tmp = Chemin(dossier) + ".tmp";
            File.WriteAllText(tmp, JsonSerializer.Serialize(this, Options));
            File.Move(tmp, Chemin(dossier), true);
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException)
        {
            // gardé en mémoire, réécrit au prochain gain
        }
    }

    // XP de tous les PC du dossier de partage (ce PC compris, avec sa valeur en mémoire).
    public int Total(string dossier)
    {
        int total = Xp;
        try
        {
            if (!Directory.Exists(dossier)) return total;
            foreach (var f in Directory.EnumerateFiles(dossier, "profil-*.json"))
            {
                if (string.Equals(f, Chemin(dossier), StringComparison.OrdinalIgnoreCase)) continue;
                try
                {
                    var autre = JsonSerializer.Deserialize<Profil>(File.ReadAllText(f), Options);
                    if (autre is not null) total += Math.Max(0, autre.Xp);
                }
                catch (Exception e) when (e is IOException or JsonException)
                {
                    // fichier d'un autre PC en cours de synchronisation
                }
            }
        }
        catch (IOException)
        {
            // dossier de partage momentanément absent (réseau, OneDrive)
        }
        return total;
    }

    public static int Niveau(int xp) => (int)Math.Floor(Math.Sqrt(xp / 5.0)) + 1;
    public static int XpPourNiveau(int niveau) => 5 * (niveau - 1) * (niveau - 1);
}
