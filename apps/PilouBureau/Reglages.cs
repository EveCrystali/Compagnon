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
    // Boutique : niveau à la dernière visite (rangées « débloquées ! ») et jour des offres déjà vues.
    public int BoutiqueVue { get; set; }
    public string BoutiqueOffresVues { get; set; } = "";
    // Dossier où chaque PC dépose son profil d'XP (OneDrive commun, partage réseau…) ; vide = local.
    public string DossierPartage { get; set; } = "";

    // Intégrations (menu « Intégrations »).
    // Identifiant de l'application Discord « Pilou » (Developer Portal) : public, partagé par tous.
    // Vide dans les réglages = celle-ci : le statut s'active d'une case, sans passer par le Developer Portal.
    public const string DiscordAppParDefaut = "1575620409070592051";
    public bool DiscordStatut { get; set; }
    private string _discordApp = "";
    public string DiscordApp
    {
        get => string.IsNullOrWhiteSpace(_discordApp) ? DiscordAppParDefaut : _discordApp;
        set => _discordApp = value ?? "";
    }
    public bool DiscordTitres { get; set; }
    // Adresse où prévenir quand une IA attend ou a fini un long travail (webhook Discord, Slack, ntfy).
    public string Webhook { get; set; } = "";
    public bool WebhookSeulementAbsent { get; set; } = true;
    // Code du groupe d'appareils (16 caractères) : appairage du téléphone ET partage de l'XP entre PC.
    // Relais ntfy (ntfy.sh ou le sien) commun à tout le groupe.
    public string Telephone { get; set; } = "";
    // Identifiant de ce PC dans le groupe (nom de la machine + 4 caractères tirés une fois).
    public string Appareil { get; set; } = "";
    public string Relais { get; set; } = PilouBureau.Telephone.RelaisParDefaut;
    // Dernier message du téléphone lu sur le sujet retour (identifiant ntfy).
    public string RetourDepuis { get; set; } = "";
    // Mise à jour automatique (dernière release du dépôt), vérifiée au démarrage puis chaque jour.
    public bool MiseAJourAuto { get; set; } = true;
    // Icône près de l'horloge (zone de notification) : la porte de secours si l'overlay ne répond plus.
    public bool IconeNotification { get; set; } = true;
    // Activités : Pilou regarde la fenêtre au premier plan (rien ne sort du PC) ; discrétion ; activités coupées.
    public bool Activites { get; set; } = true;
    public bool CacherPleinEcran { get; set; } = true;
    public bool CacherPresentation { get; set; } = true;
    public bool CacherVisio { get; set; } = true;
    public List<string> ActivitesCoupees { get; set; } = new();
    // Connecteurs (météo, API locale…) : activés, réglages non secrets. Les secrets sont dans secrets.bin (DPAPI).
    public ReglagesConnecteurs Connecteurs { get; set; } = new();
    // Amis (docs/AMIS.md) : recevoir des visites, partir en visite, raconter ses anecdotes ; heures calmes
    // (aucune visite, ni reçue ni rendue) de CalmeDebut à CalmeFin, heures locales ; égales : jamais calme.
    public bool AccepterVisites { get; set; } = true;
    public bool PartirEnVisite { get; set; } = true;
    public bool PartagerAnecdotes { get; set; } = true;
    public int CalmeDebut { get; set; } = 22;
    public int CalmeFin { get; set; } = 8;
    // Petits gestes (docs/NOTIFICATIONS.md) : Pilou tape avec toi (le crochet clavier compte les frappes,
    // jamais lesquelles), sort son appareil photo à chaque capture d'écran, montre les notifications Windows
    // dans sa bulle (désactivé par défaut ; filtre d'applis et mode « masquer le contenu »).
    public bool GesteClavier { get; set; } = true;
    public bool GestePhoto { get; set; } = true;
    public bool NotifsWindows { get; set; }
    public ModeApps NotifsMode { get; set; } = ModeApps.Toutes;
    public List<string> NotifsApps { get; set; } = new();
    public bool NotifsMasquer { get; set; }

    public ReglagesNotifs FiltreDesNotifs() => new(NotifsWindows, NotifsMode, NotifsApps, NotifsMasquer);

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

    // Accessoire réellement porté : « saison » choisit selon la date, parmi ce qui est possédé (boutique).
    public Accessoire Porte(DateTime jour, Func<Accessoire, bool> possede)
    {
        var a = Accessoire != Accessoire.Saison ? Accessoire : jour.Month switch
        {
            12 => Accessoire.Bonnet,
            1 or 2 => Accessoire.Casque,
            10 or 11 => Accessoire.Feuille,
            6 or 7 or 8 => Accessoire.Lunettes,
            _ => Accessoire.Aucun,
        };
        return a == Accessoire.Aucun || possede(a) ? a : Accessoire.Aucun;
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
