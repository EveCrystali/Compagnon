using System.IO;
using System.Reflection;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace PilouBureau;

// Ce que fait la personne, déduit de la fenêtre au premier plan, de l'écran, du son et de la caméra.
// Tout reste sur le PC : le titre de la fenêtre sert à reconnaître l'activité, puis il est oublié ;
// seuls des compteurs (« 3 h de tableur ») sont gardés dans le profil.
public static class Activites
{
    // Les tenues que Pilou peut porter (dessinées dans Scene) ; « nuit » vient de l'heure, pas d'une règle.
    public static readonly string[] Toutes =
        { "code", "tableur", "jeu-mmo", "jeu", "musique", "video", "lecture", "dessin", "visio", "nuit", "mail", "texte", "diaporama" };

    public static string Nom(string id) => id switch
    {
        "code" => "Code",
        "tableur" => "Tableur",
        "jeu-mmo" => "Jeu de rôle en ligne",
        "jeu" => "Jeu",
        "musique" => "Musique",
        "video" => "Vidéo",
        "lecture" => "Lecture",
        "dessin" => "Dessin et création",
        "visio" => "Visio",
        "nuit" => "Nuit",
        "mail" => "Mail",
        "texte" => "Écriture",
        "diaporama" => "Diaporama",
        _ => id,
    };

    // Petit signe affiché au-dessus de Pilou (en attendant le dessin de la tenue) et dans le menu.
    public static string Signe(string id) => id switch
    {
        "code" => "</>",
        "tableur" => "∑",
        "jeu-mmo" => "⚔",
        "jeu" => "▶",
        "musique" => "♪",
        "video" => "▣",
        "lecture" => "≡",
        "dessin" => "✎",
        "visio" => "◉",
        "nuit" => "☾",
        "mail" => "✉",
        "texte" => "¶",
        "diaporama" => "▤",
        _ => "",
    };

    // Ce que Pilou dit quand il endosse la tenue (une fois, pas à chaque retour sur l'app).
    public static string Accueil(string id) => id switch
    {
        "code" => "lunettes de geek : on code !",
        "tableur" => "je compte les cellules…",
        "jeu-mmo" => "bonne chasse, aventurier !",
        "jeu" => "manette en main !",
        "musique" => "♪ ça groove…",
        "video" => "pop-corn !",
        "lecture" => "chut, on lit.",
        "dessin" => "à tes pinceaux !",
        "visio" => "je me fais tout petit.",
        "nuit" => "il se fait tard…",
        "mail" => "du courrier !",
        "texte" => "à ta plume !",
        "diaporama" => "belle présentation !",
        _ => "",
    };

    // ---- Règles

    public sealed record Regle(string Activite, int Priorite, IReadOnlyList<string> Processus, Regex? Titre, Regex? Chemin, int Rang)
    {
        public bool Correspond(string processus, string titre, string chemin)
        {
            if (Processus.Count == 0 && Titre is null && Chemin is null) return false;
            if (Processus.Count > 0 && !Processus.Contains(processus, StringComparer.OrdinalIgnoreCase)) return false;
            try
            {
                if (Titre is not null && !Titre.IsMatch(titre)) return false;
                if (Chemin is not null && !Chemin.IsMatch(chemin)) return false;
            }
            catch (RegexMatchTimeoutException)
            {
                return false;
            }
            return true;
        }
    }

    private static readonly TimeSpan Delai = TimeSpan.FromMilliseconds(50);

    // Lit un fichier de règles ; une règle mal écrite (regex invalide) est ignorée, pas le fichier entier.
    public static (List<Regle> Regles, bool Remplacer) Lire(string json, int rangDepart = 0)
    {
        var liste = new List<Regle>();
        bool remplacer = false;
        try
        {
            using var doc = JsonDocument.Parse(json, new JsonDocumentOptions { CommentHandling = JsonCommentHandling.Skip, AllowTrailingCommas = true });
            var r = doc.RootElement;
            if (r.TryGetProperty("remplacer", out var rp) && rp.ValueKind == JsonValueKind.True) remplacer = true;
            if (!r.TryGetProperty("regles", out var regles) || regles.ValueKind != JsonValueKind.Array) return (liste, remplacer);
            int rang = rangDepart;
            foreach (var e in regles.EnumerateArray())
            {
                if (e.ValueKind != JsonValueKind.Object) continue;
                string S(string k) => e.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() ?? "" : "";
                var processus = e.TryGetProperty("processus", out var p) && p.ValueKind == JsonValueKind.Array
                    ? p.EnumerateArray().Where(x => x.ValueKind == JsonValueKind.String).Select(x => NomProcessus(x.GetString()!)).ToList()
                    : new List<string>();
                int priorite = e.TryGetProperty("priorite", out var pr) && pr.ValueKind == JsonValueKind.Number && pr.TryGetInt32(out var n) ? n : 10;
                Regex? Rx(string motif)
                {
                    if (motif == "") return null;
                    try
                    {
                        return new Regex(motif, RegexOptions.IgnoreCase | RegexOptions.CultureInvariant, Delai);
                    }
                    catch (ArgumentException)
                    {
                        throw new FormatException(motif);
                    }
                }
                try
                {
                    liste.Add(new Regle(S("activite").Trim().ToLowerInvariant(), priorite, processus, Rx(S("titre")), Rx(S("chemin")), rang++));
                }
                catch (FormatException)
                {
                    // expression invalide : cette règle seule est ignorée
                }
            }
        }
        catch (JsonException)
        {
            // fichier illisible : aucune règle
        }
        return (liste, remplacer);
    }

    // « EXCEL.EXE » → « excel ».
    public static string NomProcessus(string nom)
    {
        nom = nom.Trim();
        if (nom.EndsWith(".exe", StringComparison.OrdinalIgnoreCase)) nom = nom[..^4];
        return nom.ToLowerInvariant();
    }

    public static string ReglesParDefautJson()
    {
        using var flux = typeof(Activites).Assembly.GetManifestResourceStream("PilouBureau.activites.json");
        if (flux is null) return "{\"regles\":[]}";
        using var lecteur = new StreamReader(flux);
        return lecteur.ReadToEnd();
    }

    // Règles par défaut + celles de la personne (placées devant : à priorité égale, elles gagnent).
    public static List<Regle> Charger(string? jsonPersonnel)
    {
        var (defaut, _) = Lire(ReglesParDefautJson(), 1000);
        if (string.IsNullOrWhiteSpace(jsonPersonnel)) return defaut;
        var (perso, remplacer) = Lire(jsonPersonnel, 0);
        return remplacer ? perso : perso.Concat(defaut).ToList();
    }

    // ---- Ce qui se passe à l'écran

    public enum Ecran { Normal, PleinEcran, Jeu3D, Presentation, Verrouille }

    public sealed record Contexte(
        string Processus, string Titre, string Chemin, Ecran Ecran, bool Camera, bool Micro,
        IReadOnlyDictionary<string, float> Sons, DateTime Heure, double Cpu = 0, double InactifMs = 0)
    {
        public static Contexte Vide(DateTime heure) =>
            new("", "", "", Ecran.Normal, false, false, new Dictionary<string, float>(), heure);
    }

    public const float SeuilSon = 0.02f;

    // L'activité du moment ("" : rien de reconnu). Ordre : visio (caméra ou micro), règles, musique entendue, nuit.
    public static string Detecter(Contexte c, IReadOnlyList<Regle> regles)
    {
        if (c.Camera) return "visio";
        Regle? meilleure = null;
        var proc = NomProcessus(c.Processus);
        foreach (var r in regles)
        {
            if (!r.Correspond(proc, c.Titre, c.Chemin)) continue;
            if (meilleure is null || r.Priorite > meilleure.Priorite || (r.Priorite == meilleure.Priorite && r.Rang < meilleure.Rang))
                meilleure = r;
        }
        if (meilleure is not null && meilleure.Activite != "") return meilleure.Activite;
        if (meilleure is null && c.Micro) return "visio";
        // Rien au premier plan, mais une app de musique joue : on danse.
        if (meilleure is null)
            foreach (var (p, niveau) in c.Sons)
                if (niveau >= SeuilSon && regles.Any(r => r.Activite == "musique" && r.Titre is null && r.Processus.Contains(NomProcessus(p), StringComparer.OrdinalIgnoreCase)))
                    return "musique";
        var h = c.Heure.Hour;
        if (h >= 23 || h < 5) return "nuit";
        return "";
    }

    // Niveau sonore de l'app au premier plan, ou de la musique qui joue.
    public static float Crete(Contexte c, IReadOnlyList<Regle> regles)
    {
        float max = 0;
        foreach (var (p, niveau) in c.Sons)
            if (NomProcessus(p) == NomProcessus(c.Processus)
                || regles.Any(r => r.Activite == "musique" && r.Processus.Contains(NomProcessus(p), StringComparer.OrdinalIgnoreCase)))
                max = Math.Max(max, niveau);
        return max;
    }

    // ---- Discrétion : ne jamais gêner

    public sealed record OptionsDiscretion(bool PleinEcran = true, bool Presentation = true, bool Visio = true);

    // Faut-il cacher Pilou, et pourquoi. Une IA qui attend garde Pilou visible, sauf en présentation.
    public static (bool Cacher, string Raison) Discretion(Contexte c, OptionsDiscretion o, bool iaAttend)
    {
        if (c.Ecran == Ecran.Presentation && o.Presentation) return (true, "presentation");
        if (iaAttend) return (false, "");
        if (c.Ecran is Ecran.PleinEcran or Ecran.Jeu3D && o.PleinEcran) return (true, "plein-ecran");
        if ((c.Camera || c.Micro) && o.Visio) return (true, "visio");
        return (false, "");
    }

    // ---- Une tenue ne change que si l'activité tient (20 s) : un coup d'œil à une autre app ne compte pas.

    public sealed class Observateur
    {
        public const double Stable = 20_000;
        private string _candidate = "";
        private double _depuis;

        public string Tenue { get; private set; } = "";

        // Renvoie vrai quand la tenue vient de changer.
        public bool Observer(string activite, double maintenant)
        {
            if (activite != _candidate)
            {
                _candidate = activite;
                _depuis = maintenant;
            }
            if (Tenue != _candidate && maintenant - _depuis >= Stable)
            {
                Tenue = _candidate;
                return true;
            }
            return false;
        }

        public double Depuis(double maintenant) => maintenant - _depuis;
    }
}
