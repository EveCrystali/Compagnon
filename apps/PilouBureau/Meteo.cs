using System.Globalization;
using System.Text.Json;

namespace PilouBureau;

// Météo de Pilou. Source : Open-Meteo (gratuit, sans clé) ; seule la position de la ville choisie dans les
// réglages part chez eux, jamais une localisation automatique. Cette classe est pure (décodage, état,
// effets sur Pilou) : le connecteur (ConnecteurMeteo) va chercher les relevés, l'overlay et l'app Android
// appliquent les effets. Même logique en Java (android/.../Meteo.java).
public sealed record Releve(double Temperature, double Precipitation, double Pluie, double Neige, int Code, double Vent, bool Jour);

public sealed record Ville(string Nom, string Region, string Pays, double Latitude, double Longitude)
{
    public string Libelle => Region != "" && Region != Nom ? $"{Nom} ({Region}, {Pays})" : Pays != "" ? $"{Nom} ({Pays})" : Nom;
}

// Ce que la météo fait à Pilou, selon ce qu'il porte.
// Sprites : effets ajoutés au dessin (gouttes, flocons, flaque…). Protege : il porte ce qu'il faut.
// Inconfort : "mouille", "froid", "chaud" ou "" ; Tremble : frisson (anciens pixels) ; Reaction : "sueur" ou "".
public sealed record EffetMeteo(IReadOnlyList<string> Sprites, bool Protege, string Inconfort, double Tremble, string Reaction)
{
    public static readonly EffetMeteo Aucun = new(Array.Empty<string>(), true, "", 0, "");
}

public static class Meteo
{
    public const string Degage = "degage", Nuageux = "nuageux", Pluie = "pluie", Averse = "averse", Orage = "orage",
        Neige = "neige", Brouillard = "brouillard", Vent = "vent", Chaleur = "chaleur", Froid = "froid";

    public static readonly string[] Etats = { Degage, Nuageux, Pluie, Averse, Orage, Neige, Brouillard, Vent, Chaleur, Froid };

    // Objets qui protègent (ids de la boutique ou accessoires « acc-… »).
    public static readonly string[] ContrePluie = { "parapluie", "parapluie-etoile", "impermeable" };
    public static readonly string[] ContreFroid = { "acc-bonnet", "echarpe", "moufles", "impermeable" };
    public static readonly string[] ContreChaleur = { "acc-lunettes", "eventail" };

    // ---- Dernière météo connue (lue par l'overlay, par le module « Soins », envoyée au téléphone)

    public sealed record Situation(string Etat, Releve Releve, string Ville, DateTime T);

    private static Situation? _courante;
    public static Situation? Courante
    {
        get => _courante;
        set => _courante = value;
    }

    // Pilou est-il mouillé, d'après la météo courante et ce qu'il porte ?
    public static bool EstMouille(IEnumerable<string> portes) =>
        Courante is { } c && Effet(c.Etat, portes).Inconfort == "mouille";

    // ---- Open-Meteo

    public static string UrlPrevision(double latitude, double longitude) =>
        "https://api.open-meteo.com/v1/forecast?latitude=" + latitude.ToString("0.####", CultureInfo.InvariantCulture)
        + "&longitude=" + longitude.ToString("0.####", CultureInfo.InvariantCulture)
        + "&current=temperature_2m,precipitation,rain,snowfall,weather_code,wind_speed_10m,is_day&timezone=auto";

    public static string UrlRecherche(string nom) =>
        $"https://geocoding-api.open-meteo.com/v1/search?name={Uri.EscapeDataString(nom.Trim())}&count=5&language=fr&format=json";

    public static Releve? Lire(string json)
    {
        try
        {
            using var doc = JsonDocument.Parse(json);
            if (!doc.RootElement.TryGetProperty("current", out var c) || c.ValueKind != JsonValueKind.Object) return null;
            double N(string k) => c.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.Number ? v.GetDouble() : 0;
            if (!c.TryGetProperty("weather_code", out _) && !c.TryGetProperty("temperature_2m", out _)) return null;
            return new Releve(N("temperature_2m"), N("precipitation"), N("rain"), N("snowfall"), (int)N("weather_code"),
                N("wind_speed_10m"), !c.TryGetProperty("is_day", out var j) || j.ValueKind != JsonValueKind.Number || j.GetInt32() != 0);
        }
        catch (JsonException)
        {
            return null;
        }
    }

    public static List<Ville> LireVilles(string json)
    {
        var r = new List<Ville>();
        try
        {
            using var doc = JsonDocument.Parse(json);
            if (!doc.RootElement.TryGetProperty("results", out var res) || res.ValueKind != JsonValueKind.Array) return r;
            foreach (var v in res.EnumerateArray())
            {
                string S(string k) => v.TryGetProperty(k, out var x) && x.ValueKind == JsonValueKind.String ? x.GetString() ?? "" : "";
                if (!v.TryGetProperty("latitude", out var la) || !v.TryGetProperty("longitude", out var lo)) continue;
                r.Add(new Ville(S("name"), S("admin1"), S("country"), la.GetDouble(), lo.GetDouble()));
            }
        }
        catch (JsonException)
        {
            // réponse illisible : aucune ville
        }
        return r;
    }

    // Codes météo OMM (WMO) d'Open-Meteo → état de Pilou. L'orage et la neige passent avant la pluie,
    // la pluie avant le reste ; la température et le vent ne décident que par temps sec.
    public static string Etat(Releve r)
    {
        int c = r.Code;
        if (c is >= 95 and <= 99) return Orage;
        if (c is >= 71 and <= 77 or 85 or 86 || r.Neige > 0.05) return Neige;
        if (c is >= 80 and <= 82) return Averse;
        if (c is >= 51 and <= 67 || r.Pluie > 0.1) return Pluie;
        if (c is 45 or 48) return Brouillard;
        if (r.Vent >= 40) return Vent;
        if (r.Temperature > 28) return Chaleur;
        if (r.Temperature < 3) return Froid;
        return c is >= 2 and <= 3 ? Nuageux : Degage;
    }

    public static bool Pluvieux(string etat) => etat is Pluie or Averse or Orage;

    // Signe de forme (jamais la couleur seule).
    public static string Signe(string etat) => etat switch
    {
        Degage => "☀", Nuageux => "☁", Pluie or Averse => "☂", Orage => "⚡", Neige => "❄", Brouillard => "≋",
        Vent => "≈", Chaleur => "☼", Froid => "✻", _ => "·",
    };

    public static string Nom(string etat) => etat switch
    {
        Degage => "dégagé", Nuageux => "nuageux", Pluie => "pluie", Averse => "averses", Orage => "orage", Neige => "neige",
        Brouillard => "brouillard", Vent => "vent fort", Chaleur => "chaleur", Froid => "froid", _ => etat,
    };

    // ---- Effets sur Pilou

    // portes : ids portés (objets de boutique et accessoire sous la forme « acc-<nom> »).
    public static EffetMeteo Effet(string? etat, IEnumerable<string> portes, double t = 0)
    {
        if (string.IsNullOrEmpty(etat)) return EffetMeteo.Aucun;
        var p = portes as ICollection<string> ?? portes.ToList();
        bool A(string[] liste) => liste.Any(p.Contains);
        double frisson = Math.Sin(t / 55.0) * 0.35;
        switch (etat)
        {
            case Pluie:
            case Averse:
            case Orage:
            {
                bool sec = A(ContrePluie);
                var s = new List<string> { etat == Averse || etat == Orage ? "meteo-averse" : "meteo-pluie" };
                if (etat == Orage) s.Add("meteo-eclair");
                if (!sec) s.Add("meteo-mouille");
                return new EffetMeteo(s, sec, sec ? "" : "mouille", sec ? 0 : frisson, "");
            }
            case Neige:
            {
                bool chaud = A(ContreFroid);
                var s = new List<string> { "meteo-neige" };
                if (!chaud) s.Add("meteo-givre");
                return new EffetMeteo(s, chaud, chaud ? "" : "froid", chaud ? 0 : frisson, "");
            }
            case Froid:
            {
                bool chaud = A(ContreFroid);
                return new EffetMeteo(chaud ? Array.Empty<string>() : new[] { "meteo-givre" }, chaud, chaud ? "" : "froid",
                    chaud ? 0 : frisson * 0.7, "");
            }
            case Chaleur:
            {
                bool frais = A(ContreChaleur);
                return new EffetMeteo(new[] { "meteo-soleil" }, frais, frais ? "" : "chaud", 0, frais ? "" : "sueur");
            }
            case Vent:
                return new EffetMeteo(new[] { "meteo-vent" }, true, "", Math.Sin(t / 160.0) * 0.25, "");
            case Brouillard:
                return new EffetMeteo(new[] { "meteo-brouillard" }, true, "", 0, "");
            default:
                return EffetMeteo.Aucun;
        }
    }

    // Ce que Pilou dit (bulles râleuses quand il subit, contentes quand il est équipé). Graine : variété stable.
    public static string Phrase(string etat, EffetMeteo e, int graine)
    {
        string[] l = (e.Inconfort, etat) switch
        {
            ("mouille", Orage) => new[] { "un orage et pas de parapluie… sérieusement ?", "je suis trempé jusqu'à l'antenne !", "brr, ça tonne et ça mouille !" },
            ("mouille", _) => new[] { "brr, je suis trempé !", "personne n'a pensé au parapluie ?", "je vais rouiller, moi…", "flic, floc… c'est moi qui fais floc.", "un parapluie, c'est trop demander ?" },
            ("froid", Neige) => new[] { "j'ai les pieds gelés !", "un bonnet, vite !", "la neige c'est joli… de loin." },
            ("froid", _) => new[] { "brr, il caille !", "une écharpe ne serait pas de refus…", "je grelotte, là." },
            ("chaud", _) => new[] { "il fait une chaleur… je fonds !", "des lunettes de soleil, par pitié !", "pfiou, quelqu'un a un éventail ?" },
            (_, Pluie or Averse) => new[] { "bien au sec sous mon parapluie ☂", "il peut pleuvoir, je suis paré !" },
            (_, Orage) => new[] { "je ne bouge pas de sous mon parapluie !" },
            (_, Neige) => new[] { "bien au chaud sous la neige ❄", "j'adore la neige quand je suis couvert !" },
            (_, Chaleur) => new[] { "grand soleil, lunettes de rigueur ☼" },
            (_, Vent) => new[] { "ça souffle ! je tiens mon antenne…" },
            (_, Brouillard) => new[] { "on n'y voit rien, ce matin…" },
            _ => Array.Empty<string>(),
        };
        return l.Length == 0 ? "" : l[(graine % l.Length + l.Length) % l.Length];
    }

    // Quête météo du jour proposée quand le temps s'y prête : clé, texte, objectif (minutes), récompense.
    public static (string Cle, string Texte, int Objectif, int Po)? Quete(string etat) => etat switch
    {
        Pluie or Averse or Orage => ("meteo:sec", "Reste au sec sous la pluie (30 min avec un parapluie)", 30, 35),
        Neige or Froid => ("meteo:chaud", "Reste bien couvert dans le froid (30 min)", 30, 35),
        Chaleur => ("meteo:canicule", "Survis à la canicule (60 min au frais)", 60, 45),
        _ => null,
    };

    // Le Json envoyé au téléphone (champ « meteo » du message, facultatif).
    public static Dictionary<string, object> PourTelephone(Situation s) => new()
    {
        ["etat"] = s.Etat,
        ["temperature"] = Math.Round(s.Releve.Temperature),
        ["ville"] = s.Ville,
        ["signe"] = Signe(s.Etat),
    };
}
