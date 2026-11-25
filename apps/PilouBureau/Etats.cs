using System.IO;
using System.Text.Json;

namespace PilouBureau;

public enum Expr { Repos, Concentre, Attente, Grimace, Fete, Soulage, Dort, Inquiet, Caresse }

// Ce qu'une session du mod « compagnon » publie dans ~/.claude/compagnon/etat-<session>.json.
public sealed record EtatSession(
    string Session, double T, string Humeur, int Rev, bool EnTour, string Outil, int OutilRev,
    bool Inquiet, bool Fatigue, string Nom, int Niveau, bool Bureau,
    string Libelle = "", double DebutTour = 0, double FinTour = 0, string FinRaison = "", string Attente = "", double DebutOutil = 0, int Xp = 0)
{
    public static EtatSession? Lire(string json)
    {
        try
        {
            using var doc = JsonDocument.Parse(json);
            var r = doc.RootElement;
            string S(string k, string d = "") => r.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() ?? d : d;
            double N(string k) => r.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.Number ? v.GetDouble() : 0;
            bool B(string k, bool d = false) => r.TryGetProperty(k, out var v) ? v.ValueKind == JsonValueKind.True : d;
            return new EtatSession(S("session"), N("t"), S("humeur", "repos"), (int)N("rev"), B("enTour"), S("outil"),
                (int)N("outilRev"), B("inquiet"), B("fatigue"), S("nom", "Pilou"), Math.Max(1, (int)N("niveau")), B("bureau", true),
                S("libelle"), N("debutTour"), N("finTour"), S("finRaison"), S("attente"), N("debutOutil"), (int)N("xp"));
        }
        catch (JsonException)
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
        EtatSession? dernierEcrit = null;
        foreach (var e in etats)
        {
            if (dernierEcrit is null || e.T > dernierEcrit.T) dernierEcrit = e;
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
        BureauCoupe = dernierEcrit is { Bureau: false };

        Trace? choisie = null;
        double score = double.MinValue;
        foreach (var tr in _traces.Values)
        {
            if (maintenant - tr.Etat.T > Vivante) continue;
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
        if (_choisie is null) return Expr.Dort;
        var e = _choisie.Etat;
        if (e.Humeur == "dort") return Expr.Dort;
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
        _traces.Values.Where(tr => maintenant - tr.Etat.T <= Vivante).Select(tr => tr.Etat).ToList();

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
