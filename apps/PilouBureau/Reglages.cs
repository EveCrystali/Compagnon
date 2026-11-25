using System.IO;
using System.Text.Json;
using Microsoft.Win32;

namespace PilouBureau;

public enum ModeBulle { Detaillee, Compacte, Masquee }
public enum ThemeBulle { Auto, Clair, Sombre }
public enum Accessoire { Saison, Aucun, Bonnet, Casque, Noeud, Feuille, Lunettes, Couronne, ChapeauPeche, Toque, Tablier, EtoileMer }

// Options de Pilou, gardées dans ~/.claude/compagnon/reglages.json (choisies au clic droit).
public sealed class Reglages
{
    public double Taille { get; set; } = 1.0;
    public ModeBulle Bulle { get; set; } = ModeBulle.Compacte;
    public ThemeBulle Theme { get; set; } = ThemeBulle.Auto;
    public Accessoire Accessoire { get; set; } = Accessoire.Saison;
    public bool Promenade { get; set; } = true;
    public bool SuitSouris { get; set; } = true;
    public bool Jeux { get; set; } = true;
    public Couleur Couleur { get; set; } = Couleur.Bleu;
    public bool Trainee { get; set; } = true;
    // Dossier où chaque PC dépose son profil d'XP (OneDrive commun, partage réseau…) ; vide = local.
    public string DossierPartage { get; set; } = "";

    // Intégrations (menu « Intégrations »).
    // Identifiant de l'application Discord « Pilou » (Developer Portal) : public, partagé par tous.
    public const string DiscordAppParDefaut = "";
    public bool DiscordStatut { get; set; }
    public string DiscordApp { get; set; } = DiscordAppParDefaut;
    public bool DiscordTitres { get; set; }
    // Adresse où prévenir quand une IA attend ou a fini un long travail (webhook Discord, Slack, ntfy).
    public string Webhook { get; set; } = "";
    public bool WebhookSeulementAbsent { get; set; } = true;
    // Téléphone appairé (app Android) : code d'appairage et relais ntfy (ntfy.sh ou le sien).
    public string Telephone { get; set; } = "";
    public string Relais { get; set; } = PilouBureau.Telephone.RelaisParDefaut;
    // Dernier message du téléphone lu sur le sujet retour (identifiant ntfy).
    public string RetourDepuis { get; set; } = "";
    // Mise à jour automatique (dernière release du dépôt), vérifiée au démarrage puis chaque jour.
    public bool MiseAJourAuto { get; set; } = true;

    public static int Requis(Accessoire a) => Recompenses.Requis(a);

    public string Partage(string local) => string.IsNullOrWhiteSpace(DossierPartage) ? local : DossierPartage;

    private static readonly JsonSerializerOptions Options = new() { WriteIndented = true };

    public static Reglages Lire(string dossier)
    {
        try
        {
            var chemin = Path.Combine(dossier, "reglages.json");
            if (File.Exists(chemin)) return JsonSerializer.Deserialize<Reglages>(File.ReadAllText(chemin), Options) ?? new();
        }
        catch (Exception e) when (e is IOException or JsonException or UnauthorizedAccessException)
        {
            // fichier illisible : réglages par défaut
        }
        return new();
    }

    public void Ecrire(string dossier)
    {
        try
        {
            Directory.CreateDirectory(dossier);
            File.WriteAllText(Path.Combine(dossier, "reglages.json"), JsonSerializer.Serialize(this, Options));
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException)
        {
            // réglage gardé pour cette exécution seulement
        }
    }

    // Accessoire réellement porté : « saison » choisit selon la date.
    public Accessoire Porte(DateTime jour, int niveau)
    {
        var a = Accessoire != Accessoire.Saison ? Accessoire : jour.Month switch
        {
            12 => Accessoire.Bonnet,
            1 or 2 => Accessoire.Casque,
            10 or 11 => Accessoire.Feuille,
            6 or 7 or 8 => Accessoire.Lunettes,
            _ => Accessoire.Aucun,
        };
        return niveau >= Requis(a) ? a : Accessoire.Aucun;
    }

    public bool Sombre()
    {
        if (Theme != ThemeBulle.Auto) return Theme == ThemeBulle.Sombre;
        try
        {
            using var cle = Registry.CurrentUser.OpenSubKey(@"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize");
            return cle?.GetValue("AppsUseLightTheme") is int v && v == 0;
        }
        catch (Exception)
        {
            return true;
        }
    }
}
