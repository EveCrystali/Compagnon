using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;

namespace PilouBureau;

// Erreurs et avertissements du fichier ouvert dans l'éditeur (Visual Studio, VS Code), reçus par l'API locale
// (POST /diagnostics, docs/EDITEURS.md). Sans WPF : testable. Pilou reste passif : il ne parle que quand le
// compte du fichier actif change ou qu'on change de fichier, après 2,5 s de calme, jamais pendant la saisie,
// au plus une bulle toutes les 20 s ; un fichier propre où l'on arrive ne lui inspire rien.

// Un relevé envoyé par une extension d'éditeur. Fichier : nom seul (jamais le chemin) ; vide = plus de fichier actif.
public sealed record RapportDiagnostics(string Source, string Fichier, int Erreurs, int Avertissements, string Message = "", double T = 0)
{
    public const int MaxFichier = 80;
    public const int MaxMessage = 160;

    // Lecture tolérante ; null (avec l'erreur) si le corps ne va pas.
    // {"source":"vs","fichier":"Program.cs","erreurs":3,"avertissements":2,"message":"CS1002: ; attendu"}
    public static RapportDiagnostics? Lire(string json, double maintenant, out string erreur)
    {
        erreur = "";
        try
        {
            if (JsonNode.Parse(json) is not JsonObject o)
            {
                erreur = "objet JSON attendu";
                return null;
            }
            string S(string k) => o[k] is JsonValue v && v.TryGetValue<string>(out var s) ? s : "";
            int N(string k) => o[k] is JsonValue v && v.TryGetValue<double>(out var d) && !double.IsNaN(d)
                ? (int)Math.Clamp(d, 0, 99_999) : 0;
            var source = Signal.Propre(S("source"), "");
            if (source == "")
            {
                erreur = "« source » manquante (vs, vscode…)";
                return null;
            }
            bool ferme = o["ferme"] is JsonValue f && f.TryGetValue<bool>(out var b) && b;
            var fichier = ferme ? "" : NomFichier(S("fichier"));
            return new RapportDiagnostics(source, fichier, fichier == "" ? 0 : N("erreurs"), fichier == "" ? 0 : N("avertissements"),
                fichier == "" ? "" : Nettoyer(S("message"), MaxMessage), maintenant);
        }
        catch (JsonException)
        {
            erreur = "JSON illisible";
            return null;
        }
    }

    // Nom seul : ce qui suit le dernier « / » ou « \ » (le chemin n'est jamais gardé ni affiché).
    public static string NomFichier(string chemin)
    {
        var s = chemin.Trim();
        int i = s.LastIndexOfAny(new[] { '/', '\\' });
        if (i >= 0) s = s[(i + 1)..];
        return Nettoyer(s, MaxFichier);
    }

    // Chemins absolus dans un message (C:\…\X.cs, \\serveur\…, /home/…/x.ts, file:///…) : réduits au nom seul.
    private static readonly Regex Chemins = new(
        @"(file:///?)?([A-Za-z]:[\\/]|\\\\|/)([^\s""'<>|:*?]+[\\/])+(?<nom>[^\s""'<>|:*?\\/]+)", RegexOptions.Compiled);

    // Sur une ligne, sans caractère de contrôle, chemins réduits, borné (… au bout si coupé).
    public static string Nettoyer(string texte, int max)
    {
        var s = new string(texte.Select(c => char.IsControl(c) ? ' ' : c).ToArray());
        s = Chemins.Replace(s, m => m.Groups["nom"].Value);
        s = Regex.Replace(s, @"\s+", " ").Trim();
        return s.Length <= max ? s : s[..(max - 1)].TrimEnd() + "…";
    }
}

public enum TonDiagnostics { Erreurs, Avertissements, Propre }

public enum ReactionDiagnostics { Aucune, Grimace, Saut }

// Ce que Pilou dit : signe (forme lisible sans couleur), texte, ton (orange pour les erreurs, bleu sinon), réaction.
public sealed record AnnonceDiagnostics(string Signe, string Texte, TonDiagnostics Ton, ReactionDiagnostics Reaction)
{
    public string Ligne => $"{Signe} {Texte}";
}

public sealed class SuiviDiagnostics
{
    // Sans nouvelles d'un éditeur depuis 5 min (fermé, planté), son état est oublié. Les extensions renvoient
    // l'état courant toutes les minutes.
    public const double Ttl = 5 * 60_000;
    // Le compte (ou le fichier) doit rester le même 2,5 s avant d'être annoncé : pas de bulle à chaque frappe.
    public const double Regroupement = 2500;
    // Au plus une bulle toutes les 20 s ; ce qui change entre-temps est annoncé ensuite (le dernier état seulement).
    public const double Repos = 20_000;
    public const int MaxMessageAffiche = 60;

    private sealed record Etat(RapportDiagnostics R, double Depuis);

    private readonly Dictionary<string, Etat> _parSource = new();
    private readonly object _verrou = new();
    private RapportDiagnostics? _vu;
    private double _derniere = double.NegativeInfinity;

    // Réglages (fenêtre Connecteurs) : premier message d'erreur (coupé par défaut), nom du fichier (montré par défaut).
    public bool AvecMessage { get; set; }
    public bool AvecNom { get; set; } = true;

    // Fichiers passés à zéro erreur (succès « Zéro erreur »).
    public int Propres { get; private set; }

    public void Recevoir(RapportDiagnostics r)
    {
        lock (_verrou)
        {
            if (r.Fichier == "")
            {
                _parSource.Remove(r.Source);
                return;
            }
            // Le battement (même fichier, mêmes comptes) ne fait que prolonger la durée de vie.
            var depuis = _parSource.TryGetValue(r.Source, out var avant) && Meme(avant.R, r) ? avant.Depuis : r.T;
            _parSource[r.Source] = new Etat(r, depuis);
        }
    }

    private static bool Meme(RapportDiagnostics a, RapportDiagnostics b) =>
        a.Source == b.Source && a.Fichier == b.Fichier && a.Erreurs == b.Erreurs && a.Avertissements == b.Avertissements;

    private Etat? CourantEtat(double t)
    {
        lock (_verrou)
        {
            foreach (var k in _parSource.Where(p => t - p.Value.R.T > Ttl).Select(p => p.Key).ToList()) _parSource.Remove(k);
            return _parSource.Values.OrderByDescending(e => e.R.T).FirstOrDefault();
        }
    }

    // Le dernier relevé encore valable (l'éditeur le plus récemment actif), null si aucun.
    public RapportDiagnostics? Courant(double t) => CourantEtat(t)?.R;

    // Appelé régulièrement : une annonce s'il y a lieu, sinon null. Saisie en cours : on attend.
    public AnnonceDiagnostics? Battre(double t, bool saisie)
    {
        var e = CourantEtat(t);
        if (e is null)
        {
            _vu = null; // éditeur fermé : à la réouverture, l'état est annoncé de nouveau
            return null;
        }
        var r = e.R;
        if (_vu is { } v0 && Meme(v0, r)) return null;
        if (t - e.Depuis < Regroupement || saisie) return null;

        bool memeFichier = _vu is { } v && v.Source == r.Source && v.Fichier == r.Fichier;
        int erreursAvant = memeFichier ? _vu!.Erreurs : 0;
        bool propre = memeFichier && erreursAvant > 0 && r.Erreurs == 0;
        // Rien à dire : un fichier sans erreur ni avertissement (où l'on arrive, ou dont les avertissements partent).
        if (!propre && r.Erreurs == 0 && r.Avertissements == 0)
        {
            _vu = r;
            return null;
        }
        if (t - _derniere < Repos) return null;
        _vu = r;
        _derniere = t;
        if (propre) Propres++;
        var reaction = propre ? ReactionDiagnostics.Saut
            : memeFichier && r.Erreurs > erreursAvant ? ReactionDiagnostics.Grimace : ReactionDiagnostics.Aucune;
        return Annonce(r, propre, reaction);
    }

    private AnnonceDiagnostics Annonce(RapportDiagnostics r, bool propre, ReactionDiagnostics reaction)
    {
        var nom = AvecNom ? r.Fichier : "";
        if (propre)
            return new("✓",
                Joindre(r.Avertissements > 0 ? "plus d'erreur !" : "propre !", Avert(r.Avertissements), nom),
                TonDiagnostics.Propre, reaction);
        if (r.Erreurs > 0)
        {
            var texte = Joindre(r.Erreurs == 1 ? "1 erreur" : $"{r.Erreurs} erreurs", Avert(r.Avertissements), nom);
            if (AvecMessage && r.Message != "") texte += " — " + RapportDiagnostics.Nettoyer(r.Message, MaxMessageAffiche);
            return new("⚠", texte, TonDiagnostics.Erreurs, reaction);
        }
        return new("△", Joindre(Avert(r.Avertissements), nom), TonDiagnostics.Avertissements, reaction);
    }

    private static string Avert(int n) => n == 0 ? "" : $"{n} avert.";

    private static string Joindre(params string[] parties) => string.Join(" · ", parties.Where(p => p != ""));

    // Au survol : l'état du fichier actif, même quand Pilou n'a rien dit.
    public string? Resume(double t)
    {
        if (Courant(t) is not { } r) return null;
        var nom = AvecNom ? r.Fichier : "fichier actif";
        if (r.Erreurs == 0 && r.Avertissements == 0) return $"✓ {nom} : aucune erreur";
        return r.Erreurs > 0
            ? "⚠ " + Joindre(r.Erreurs == 1 ? "1 erreur" : $"{r.Erreurs} erreurs", Avert(r.Avertissements), nom)
            : "△ " + Joindre(Avert(r.Avertissements), nom);
    }
}
