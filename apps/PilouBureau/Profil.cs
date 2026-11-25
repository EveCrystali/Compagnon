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
    // Pêche et cuisine : prises de chaque espèce (carnet), ingrédients en réserve, plats déjà faits.
    public Dictionary<string, int> Carnet { get; set; } = new();
    public Dictionary<string, int> Stock { get; set; } = new();
    public List<string> Plats { get; set; } = new();
    public int PlatsCuisines { get; set; }
    // Gains du téléphone déjà crédités (identifiants) : un message relu n'est jamais compté deux fois.
    public List<string> Recus { get; set; } = new();
    // XP gagnée sur le téléphone (atelier), créditée par chaque PC du groupe : comptée au maximum, pas en somme.
    public int XpTelephone { get; set; }
    // Activités (compteurs seulement, jamais de titre de fenêtre) : secondes par activité, succès obtenus,
    // réunions des 7 derniers jours (dates), présentations faites.
    public Dictionary<string, long> Activites { get; set; } = new();
    public List<string> Succes { get; set; } = new();
    public List<DateTime> Reunions { get; set; } = new();
    public int Presentations { get; set; }
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

    // XP de tout le groupe : ce PC, les PC du dossier de partage, et ceux du relais (Groupe).
    public int Total(string dossier, IEnumerable<Groupe.Compteur>? groupe = null) =>
        Groupe.Total(this, AutresDuDossier(dossier), groupe ?? Array.Empty<Groupe.Compteur>());

    public List<Profil> AutresDuDossier(string dossier)
    {
        var autres = new List<Profil>();
        try
        {
            if (!Directory.Exists(dossier)) return autres;
            foreach (var f in Directory.EnumerateFiles(dossier, "profil-*.json"))
            {
                if (string.Equals(f, Chemin(dossier), StringComparison.OrdinalIgnoreCase)) continue;
                try
                {
                    var autre = JsonSerializer.Deserialize<Profil>(File.ReadAllText(f), Options);
                    if (autre is not null) autres.Add(autre);
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
        return autres;
    }

    public static int Niveau(int xp) => (int)Math.Floor(Math.Sqrt(xp / 5.0)) + 1;
    public static int XpPourNiveau(int niveau) => 5 * (niveau - 1) * (niveau - 1);
}
