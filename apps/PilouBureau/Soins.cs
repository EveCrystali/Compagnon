using System.Globalization;
using System.Text.Json;

namespace PilouBureau;

// Soins de Pilou : une couche légère et passive par-dessus le reste. Trois besoins qui baissent lentement
// (faim, propreté, moral) ; rien ne s'affiche tant que tout va bien ; sous le seuil, une petite icône près
// de Pilou, et un clic la comble. Aucune punition : au pire, négligé, Pilou a l'air terne. Bien soigné
// (les trois au-dessus de 70), il rayonne (XP et po × 1,2) ; la qualité des soins des derniers jours choisit
// la variante de ses prochains stades d'évolution.
//
// Temps réel, même appareils éteints : l'état est une fonction pure d'une base (état connu à un instant),
// d'un journal d'actions horodatées (identifiant unique, fusionné par union entre appareils, comme les
// gains) et de l'heure. Même calcul dans Soins.java (téléphone) ; vecteurs communs dans les tests.
public sealed class EtatSoins
{
    public double Faim { get; set; } = 100;
    public double Proprete { get; set; } = 100;
    public double Moral { get; set; } = 100;
    // Moyenne glissante (≈ 3 jours) de la moyenne des trois besoins : la qualité des soins.
    public double Score { get; set; } = 80;
    public double T { get; set; }
    public string Rythme { get; set; } = Soins.Normal;
    public bool Vacances { get; set; }

    public EtatSoins Copie() => (EtatSoins)MemberwiseClone();
}

public sealed record ActionSoin(string Id, string Type, double T, string Objet = "");

// Ce qu'un appareil garde : la base, les actions récentes, et l'appareil d'origine de la base (entre deux
// bases différentes, celle de l'origine la plus petite l'emporte, puis la plus récente : tout le groupe converge).
public sealed class CarnetSoins
{
    public EtatSoins? Base { get; set; }
    public string Origine { get; set; } = "";
    public List<ActionSoin> Actions { get; set; } = new();
    // Identifiants déjà repliés dans la base (une action relue en retard n'est jamais comptée deux fois).
    public List<string> Plies { get; set; } = new();
}

public static class Soins
{
    public const string Doux = "doux", Normal = "normal", Exigeant = "exigeant";
    public const string Faim = "faim", Proprete = "proprete", Moral = "moral";
    public const double Seuil = 30, SeuilTerne = 10, SeuilRayonnant = 70;
    private const double Heure = 3600_000, Jour = 24 * Heure;
    // Heures pour vider un besoin plein, au rythme normal.
    public const double HeuresFaim = 36, HeuresProprete = 48, HeuresMoral = 30;
    private const double TauScore = 3 * Jour;
    public const double Garder = 2 * Jour; // au-delà, les actions sont repliées dans la base

    public static readonly IReadOnlyList<string> Besoins = new[] { Faim, Proprete, Moral };

    // En-cas de la boutique (consommables) : Pilou mange d'abord le meilleur. Le moral qu'il apporte en plus.
    public static readonly IReadOnlyList<(string Id, int Moral)> EnCas = new[]
    {
        ("gateau", 15), ("soupe", 10), ("pomme", 5), ("croquettes", 0),
    };

    public static double Facteur(string rythme) => rythme switch { Doux => 0.6, Exigeant => 1.6, _ => 1.0 };

    public static EtatSoins Neuf(double t) => new() { T = t };

    // ---- La fonction pure

    // État à l'instant « maintenant » : la base, puis chaque action dans l'ordre (heure, identifiant).
    // Une action antérieure à la base (arrivée en retard) s'applique à l'heure de la base.
    public static EtatSoins Calculer(EtatSoins base_, IEnumerable<ActionSoin> actions, double maintenant)
    {
        var e = base_.Copie();
        foreach (var a in actions.OrderBy(a => Math.Max(a.T, base_.T)).ThenBy(a => a.Id, StringComparer.Ordinal))
        {
            double t = Math.Max(a.T, base_.T);
            if (t > maintenant) break;
            Avancer(e, t);
            Appliquer(e, a);
        }
        Avancer(e, Math.Max(maintenant, e.T));
        return e;
    }

    // Le temps passe : chaque besoin baisse en ligne droite (borné à 0) ; la moyenne glissante suit, par
    // tranches d'une heure au plus. En vacances, rien ne bouge.
    public static void Avancer(EtatSoins e, double jusqua)
    {
        while (e.T < jusqua)
        {
            double dt = Math.Min(Heure, jusqua - e.T);
            if (!e.Vacances)
            {
                double f = Facteur(e.Rythme) * dt / Heure * 100;
                e.Faim = Math.Max(0, e.Faim - f / HeuresFaim);
                e.Proprete = Math.Max(0, e.Proprete - f / HeuresProprete);
                e.Moral = Math.Max(0, e.Moral - f / HeuresMoral);
                double moyenne = (e.Faim + e.Proprete + e.Moral) / 3;
                e.Score += (moyenne - e.Score) * (1 - Math.Exp(-dt / TauScore));
            }
            e.T += dt;
        }
    }

    public static void Appliquer(EtatSoins e, ActionSoin a)
    {
        switch (a.Type)
        {
            case "nourrir":
                e.Faim = 100;
                e.Moral = Math.Min(100, e.Moral + BonusEnCas(a.Objet));
                break;
            case "laver":
                e.Proprete = 100;
                break;
            case "calin":
                e.Moral = 100;
                break;
            case "soin":
                e.Faim = e.Proprete = e.Moral = 100;
                break;
            case "caresse":
                e.Moral = Math.Min(100, e.Moral + 10);
                break;
            case "jouer":
                e.Moral = Math.Min(100, e.Moral + 15);
                break;
            case "rythme":
                if (a.Objet is Doux or Normal or Exigeant) e.Rythme = a.Objet;
                break;
            case "vacances":
                e.Vacances = a.Objet == "1";
                break;
        }
    }

    public static int BonusEnCas(string objet) =>
        objet.StartsWith("plat", StringComparison.Ordinal) ? 15 : EnCas.FirstOrDefault(x => x.Id == objet).Moral;

    // ---- Lecture de l'état

    public static double Valeur(EtatSoins e, string besoin) => besoin switch { Faim => e.Faim, Proprete => e.Proprete, _ => e.Moral };

    // Besoins sous le seuil, du plus pressant au moins pressant (l'icône près de Pilou montre le premier).
    public static List<string> Manques(EtatSoins e) =>
        Besoins.Where(b => Valeur(e, b) < Seuil).OrderBy(b => Valeur(e, b)).ToList();

    public static bool Rayonnant(EtatSoins e) => !e.Vacances && e.Faim > SeuilRayonnant && e.Proprete > SeuilRayonnant && e.Moral > SeuilRayonnant;

    // Négligé : deux besoins presque vides. Pilou a juste l'air terne (aucune autre conséquence).
    public static bool Terne(EtatSoins e) => !e.Vacances && Besoins.Count(b => Valeur(e, b) < SeuilTerne) >= 2;

    // Bonus d'XP et de pièces quand il rayonne.
    public static int Bonus(int gain, EtatSoins e) => Rayonnant(e) && gain > 0 ? (int)Math.Round(gain * 1.2) : gain;

    // Variante d'un stade (2 à 4), choisie au passage du stade d'après la qualité des soins.
    public static string Variante(double score) => score >= 60 ? "calin" : "espiegle";

    public static string NomVariante(string v) => v == "calin" ? "câlin" : v == "espiegle" ? "espiègle" : "";

    // Signe de forme de chaque besoin (pas de couleur seule).
    public static string Signe(string besoin) => besoin switch { Faim => "◒", Proprete => "✦", _ => "♥" };

    public static string Nom(string besoin) => besoin switch { Faim => "faim", Proprete => "propreté", _ => "moral" };

    // ---- Le carnet d'un appareil

    public static ActionSoin Action(string type, double t, string objet = "") =>
        new(Convert.ToHexString(System.Security.Cryptography.RandomNumberGenerator.GetBytes(6)).ToLowerInvariant(), type, t, objet);

    public static EtatSoins Etat(CarnetSoins c, double maintenant) =>
        Calculer(c.Base ?? Neuf(maintenant), c.Actions, maintenant);

    // Première fois (migration) : Pilou commence rassasié, propre et de bonne humeur.
    public static void Initialiser(CarnetSoins c, double maintenant, string appareil)
    {
        if (c.Base is not null) return;
        c.Base = Neuf(maintenant);
        c.Origine = appareil;
    }

    public static bool Ajouter(CarnetSoins c, ActionSoin a)
    {
        if (c.Actions.Any(x => x.Id == a.Id) || c.Plies.Contains(a.Id)) return false;
        c.Actions.Add(a);
        return true;
    }

    // Les actions de plus de deux jours rejoignent la base (heure ronde : le même repli partout).
    public static void Plier(CarnetSoins c, double maintenant)
    {
        if (c.Base is null) return;
        double limite = Math.Floor((maintenant - Garder) / Heure) * Heure;
        if (limite <= c.Base.T) return;
        var vieilles = c.Actions.Where(a => a.T < limite).ToList();
        c.Base = Calculer(c.Base, vieilles, limite);
        foreach (var a in vieilles) c.Plies.Add(a.Id);
        if (c.Plies.Count > 300) c.Plies.RemoveRange(0, c.Plies.Count - 300);
        c.Actions.RemoveAll(a => a.T < limite);
    }

    // Ce qu'un autre appareil sait : union des actions ; entre deux bases, l'origine la plus petite l'emporte,
    // puis la plus récente. Renvoie true si quelque chose a changé.
    public static bool Fusionner(CarnetSoins c, EtatSoins? base_, string origine, IEnumerable<ActionSoin> actions)
    {
        bool change = false;
        if (base_ is not null && origine != "")
        {
            bool prendre = c.Base is null
                           || string.CompareOrdinal(origine, c.Origine) < 0
                           || (origine == c.Origine && base_.T > c.Base.T);
            if (prendre)
            {
                c.Base = base_.Copie();
                c.Origine = origine;
                c.Actions.RemoveAll(a => a.T < base_.T);
                change = true;
            }
        }
        // Une action plus ancienne que notre base y est déjà repliée (ailleurs) : on ne la rejoue pas.
        foreach (var a in actions)
            if (c.Base is null || a.T >= c.Base.T)
                change |= Ajouter(c, a);
        return change;
    }

    // ---- Échanges (groupe, téléphone)

    public static Dictionary<string, object> JsonEtat(EtatSoins e) => new()
    {
        ["f"] = Math.Round(e.Faim, 3), ["p"] = Math.Round(e.Proprete, 3), ["m"] = Math.Round(e.Moral, 3),
        ["s"] = Math.Round(e.Score, 3), ["t"] = e.T, ["r"] = e.Rythme, ["v"] = e.Vacances ? 1 : 0,
    };

    public static object JsonAction(ActionSoin a) => a.Objet == ""
        ? new object[] { a.Id, a.Type, a.T }
        : new object[] { a.Id, a.Type, a.T, a.Objet };

    public static EtatSoins? LireEtat(JsonElement r)
    {
        if (r.ValueKind != JsonValueKind.Object) return null;
        double N(string k, double d) => r.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.Number ? v.GetDouble() : d;
        double T(string k) => Math.Clamp(N(k, 100), 0, 100);
        var rythme = r.TryGetProperty("r", out var rv) && rv.ValueKind == JsonValueKind.String ? rv.GetString() ?? Normal : Normal;
        var t = N("t", 0);
        if (t <= 0) return null;
        return new EtatSoins
        {
            Faim = T("f"), Proprete = T("p"), Moral = T("m"), Score = Math.Clamp(N("s", 80), 0, 100), T = t,
            Rythme = rythme is Doux or Exigeant ? rythme : Normal, Vacances = N("v", 0) == 1,
        };
    }

    private static readonly HashSet<string> Types = new()
        { "nourrir", "laver", "calin", "soin", "caresse", "jouer", "rythme", "vacances", "debut" };

    public static List<ActionSoin> LireActions(JsonElement r, int max = 200)
    {
        var l = new List<ActionSoin>();
        if (r.ValueKind != JsonValueKind.Array) return l;
        foreach (var x in r.EnumerateArray())
        {
            if (l.Count >= max) break;
            if (x.ValueKind != JsonValueKind.Array || x.GetArrayLength() < 3) continue;
            var id = x[0].ValueKind == JsonValueKind.String ? x[0].GetString() ?? "" : "";
            var type = x[1].ValueKind == JsonValueKind.String ? x[1].GetString() ?? "" : "";
            if (id is not { Length: > 0 and <= 32 } || !Types.Contains(type) || x[2].ValueKind != JsonValueKind.Number) continue;
            var objet = x.GetArrayLength() > 3 && x[3].ValueKind == JsonValueKind.String ? x[3].GetString() ?? "" : "";
            l.Add(new ActionSoin(id, type, x[2].GetDouble(), objet.Length > 40 ? objet[..40] : objet));
        }
        return l;
    }

    // Ce qui part dans les messages (taille comptée : un message ntfy reste sous 4 096 octets).
    public static List<ActionSoin> Recentes(CarnetSoins c, int max) =>
        c.Actions.OrderByDescending(a => a.T).Take(max).ToList();

    // « faim 18 % · propreté 64 % · moral 91 % » (menu, sur demande seulement).
    public static string Resume(EtatSoins e) => string.Join(" · ",
        Besoins.Select(b => $"{Signe(b)} {Nom(b)} {Math.Round(Valeur(e, b)).ToString(CultureInfo.InvariantCulture)} %"));
}
