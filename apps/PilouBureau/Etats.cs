using System.IO;
using System.Text.Json;

namespace PilouBureau;

public enum Expr { Repos, Concentre, Attente, Grimace, Fete, Soulage, Dort, Inquiet, Caresse }

// Ce qu'une session publie dans ~/.claude/compagnon/etat-<session>.json : le mod « compagnon »
// pour Claude, `PilouBureau --signal` pour les autres (Codex, scripts…). Format : docs/BRANCHER.md.
public sealed record EtatSession(
    string Session, double T, string Humeur, int Rev, bool EnTour, string Outil, int OutilRev,
    bool Inquiet, bool Fatigue, string Nom, int Niveau, bool Bureau,
    string Libelle = "", double DebutTour = 0, double FinTour = 0, string FinRaison = "", string Attente = "", double DebutOutil = 0, int Xp = 0,
    string Source = "claude", double Ttl = Suivi.Vivante, int Commits = 0, int Tests = 0)
{
    // Claude republie son état toutes les 30 s ; une autre source n'écrit qu'à ses événements
    // et donne elle-même sa durée de vie (ttl).
    public bool Claude => Source == "claude";

    public string Json() => System.Text.Json.JsonSerializer.Serialize(new Dictionary<string, object>
    {
        ["v"] = 3, ["session"] = Session, ["source"] = Source, ["t"] = T, ["ttl"] = Ttl, ["humeur"] = Humeur, ["rev"] = Rev,
        ["enTour"] = EnTour, ["outil"] = Outil, ["outilRev"] = OutilRev, ["inquiet"] = Inquiet, ["fatigue"] = Fatigue,
        ["nom"] = Nom, ["niveau"] = Niveau, ["bureau"] = Bureau, ["libelle"] = Libelle, ["debutTour"] = DebutTour,
        ["finTour"] = FinTour, ["finRaison"] = FinRaison, ["attente"] = Attente, ["debutOutil"] = DebutOutil, ["xp"] = Xp,
        ["commits"] = Commits, ["tests"] = Tests,
    });

    public static EtatSession? Lire(string json)
    {
        try
        {
            using var doc = JsonDocument.Parse(json);
            var r = doc.RootElement;
            string S(string k, string d = "") => r.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() ?? d : d;
            double N(string k) => r.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.Number ? v.GetDouble() : 0;
            bool B(string k, bool d = false) => r.TryGetProperty(k, out var v) ? v.ValueKind == JsonValueKind.True : d;
            const double Vivante = Suivi.Vivante;
            return new EtatSession(S("session"), N("t"), S("humeur", "repos"), (int)N("rev"), B("enTour"), S("outil"),
                (int)N("outilRev"), B("inquiet"), B("fatigue"), S("nom", "Pilou"), Math.Max(1, (int)N("niveau")), B("bureau", true),
                S("libelle"), N("debutTour"), N("finTour"), S("finRaison"), S("attente"), N("debutOutil"), (int)N("xp"),
                S("source", "claude") is var src && src != "" ? src.ToLowerInvariant() : "claude",
                N("ttl") is var ttl && ttl > 0 ? ttl : Vivante, (int)N("commits"), (int)N("tests"));
        }
        catch (Exception e) when (e is JsonException or InvalidOperationException)
        {
            return null;
        }
    }
}

// Suit toutes les sessions et choisit celle que Pilou « écoute » : la plus récemment active.
public sealed class Suivi
{
    private sealed class Trace
    {
        public EtatSession Etat = null!;
        public double Activite;     // dernier changement observé (rev, outil, tour)
        public double TRev;         // quand l'humeur passagère a commencé
        public double TOutil;       // quand l'outil en cours a commencé
    }

    public const double Vivante = 90_000; // une session publie au moins toutes les 30 s
    private static readonly Dictionary<string, double> Durees = new()
    {
        ["grimace"] = 2600, ["fete"] = 3200, ["soulage"] = 2400, ["caresse"] = 2400,
    };

    private readonly Dictionary<string, Trace> _traces = new();

    public EtatSession? Courant { get; private set; }
    public bool BureauCoupe { get; private set; }

    public void Observer(IEnumerable<EtatSession> etats, double maintenant)
    {
        etats = etats as IReadOnlyCollection<EtatSession> ?? etats.ToList();
        EtatSession? dernierEcrit = null;
        foreach (var e in etats)
        {
            if (e.Claude && (dernierEcrit is null || e.T > dernierEcrit.T)) dernierEcrit = e;
            if (!_traces.TryGetValue(e.Session, out var tr))
            {
                _traces[e.Session] = new Trace { Etat = e, Activite = 0, TRev = -1e12, TOutil = maintenant };
                continue;
            }
            if (e.Rev != tr.Etat.Rev)
            {
                tr.TRev = maintenant;
                tr.Activite = maintenant;
            }
            if (e.OutilRev != tr.Etat.OutilRev)
            {
                tr.TOutil = maintenant;
                tr.Activite = maintenant;
            }
            if (e.EnTour != tr.Etat.EnTour) tr.Activite = maintenant;
            tr.Etat = e;
        }
        // Fichier d'une autre source effacé (fin de session) : elle quitte la bulle tout de suite.
        var presentes = etats.Select(e => e.Session).ToHashSet();
        foreach (var cle in _traces.Where(kv => !kv.Value.Etat.Claude && !presentes.Contains(kv.Key)).Select(kv => kv.Key).ToList())
            _traces.Remove(cle);
        // « /compagnon bureau » coupé : seul le mod de Claude le décide.
        BureauCoupe = dernierEcrit is { Bureau: false, Claude: true };

        Trace? choisie = null;
        double score = double.MinValue;
        foreach (var tr in _traces.Values)
        {
            if (maintenant - tr.Etat.T > tr.Etat.Ttl) continue;
            var s = (tr.Etat.EnTour ? 1e15 : 0) + (tr.Etat.Humeur == "dort" ? 0 : 1e14) + tr.Activite;
            if (s > score)
            {
                score = s;
                choisie = tr;
            }
        }
        _choisie = choisie;
        Courant = choisie?.Etat;
    }

    private Trace? _choisie;

    public Expr Expression(double maintenant, double tCaresse)
    {
        if (maintenant - tCaresse < 2400) return Expr.Caresse;
        // Sans session d'IA (ou la session s'est endormie), Pilou est éveillé : c'est un compagnon de tout. Il ne dort
        // que si tu t'absentes, ou la nuit (Saynetes.Endormi, appliqué par FenetrePilou.Sommeil).
        if (_choisie is null) return Expr.Repos;
        var e = _choisie.Etat;
        if (e.Humeur == "dort") return Expr.Repos;
        if (Durees.TryGetValue(e.Humeur, out var d) && maintenant - _choisie.TRev < d)
        {
            return e.Humeur switch
            {
                "grimace" => Expr.Grimace,
                "fete" => Expr.Fete,
                "soulage" => Expr.Soulage,
                _ => Expr.Caresse,
            };
        }
        if (e.Outil != "" && maintenant - _choisie.TOutil > 6000) return Expr.Attente;
        if (e.EnTour) return Expr.Concentre;
        if (e.Inquiet) return Expr.Inquiet;
        return Expr.Repos;
    }

    // Les sessions encore ouvertes (elles publient au moins toutes les 30 s).
    public IReadOnlyList<EtatSession> Vivantes(double maintenant) =>
        _traces.Values.Where(tr => maintenant - tr.Etat.T <= tr.Etat.Ttl).Select(tr => tr.Etat).ToList();

    public double DepuisHumeur(double maintenant) => _choisie is null ? 1e9 : maintenant - _choisie.TRev;

    public static IEnumerable<EtatSession> LireDossier(string dossier)
    {
        if (!Directory.Exists(dossier)) yield break;
        foreach (var f in Directory.EnumerateFiles(dossier, "etat-*.json"))
        {
            string json;
            try
            {
                json = File.ReadAllText(f);
            }
            catch (IOException)
            {
                continue; // en cours d'écriture : relu au tour suivant
            }
            var e = EtatSession.Lire(json);
            if (e is not null) yield return e;
        }
    }
}
