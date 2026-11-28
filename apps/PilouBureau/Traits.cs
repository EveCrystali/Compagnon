using System.Globalization;
using System.IO;
using System.Text;

namespace PilouBureau;

// Les traits de personnalité de Pilou (docs/TRAITS.md) : un « RPG de personnalité », sans chiffre à optimiser. Pilou
// attrape des traits à force de vivre avec le joueur (couche-tard, pêcheur du dimanche, câlin…). On les découvre, on ne
// les choisit pas ; un trait acquis ne se perd pas ; trois « dominants » à la fois, qui changent lentement.
// Aucun effet chiffré : un trait change des mots (assets/presence/traits.txt) et se montre dans « Pilou et moi ».
//
// Ce fichier est le MOTEUR, sans WPF ; android/.../Traits.java en est la copie exacte. Les deux lisent assets/traits.txt
// et rejouent android/app/src/test/resources/traits-vecteurs.txt, écrit d'ici (TraitsTests).
//
//   Faits       le journal de Pilou, déjà fusionné entre appareils (Presence.FaitsDuJour, un par jour)
//   Mesure      le nombre de jours du journal qui remplissent la condition du trait
//   Acquis      mesure >= seuil ; un bit par trait (Appareil.Traits), réuni par « ou » entre appareils
//   Dominants   trois au plus parmi les acquis : les plus vécus pendant les 28 jours d'avant le lundi de la semaine
//               en cours (ils ne changent donc qu'une fois par semaine, et peu à la fois)
public static class Traits
{
    public const int Max = 60;
    public const int NombreDominants = 3;
    public const int Fenetre = 28;
    private static readonly CultureInfo Ci = CultureInfo.InvariantCulture;

    public static readonly string[] Nombres = { "mn", "tv", "am", "ta", "jx", "ca", "so", "pc", "pq", "cu", "qu", "ce", "vi", "nv", "mg", "ma", "we", "sem", "abs" };
    public static readonly string[] Textes = { "ac", "px", "cx", "me", "cf", "mo", "ex", "ob" };

    // Un terme de condition : fait, comparaison (>= <= = !=), valeur (nombre ou texte).
    public sealed record Terme(string Fait, string Op, string Valeur, int Nombre, bool Texte);

    public sealed record Trait(int Numero, string Id, string Nom, int Seuil, IReadOnlyList<Terme> Condition)
    {
        public long Bit => 1L << (Numero - 1);
        public string Sprite => "trait-" + Id;
    }

    // ---- Définition (assets/traits.txt) : « numéro|identifiant|nom|seuil|condition » ; une ligne fausse est ignorée.

    public static List<Trait> Lire(string texte)
    {
        var l = new List<Trait>();
        foreach (var brut in texte.Replace("\r\n", "\n").Split('\n'))
        {
            var ligne = Presence.Rogner(brut);
            if (ligne.Length == 0 || ligne[0] == '#') continue;
            var p = ligne.Split('|');
            if (p.Length != 5) continue;
            if (!int.TryParse(p[0], NumberStyles.None, Ci, out var n) || n < 1 || n > Max) continue;
            if (!int.TryParse(p[3], NumberStyles.None, Ci, out var seuil) || seuil < 1) continue;
            string id = Presence.Rogner(p[1]), nom = Presence.Rogner(p[2]);
            var condition = Condition(Presence.Rogner(p[4]));
            if (id.Length == 0 || nom.Length == 0 || condition is null || l.Any(t => t.Numero == n || t.Id == id)) continue;
            l.Add(new Trait(n, id, nom, seuil, condition));
        }
        return l.OrderBy(t => t.Numero).ToList();
    }

    private static readonly string[] Ops = { ">=", "<=", "!=", "=" };

    // « pc>=1&we=1 » ; null si un terme ne se lit pas (fait inconnu, nombre attendu…).
    public static List<Terme>? Condition(string texte)
    {
        var l = new List<Terme>();
        foreach (var brut in texte.Split('&'))
        {
            var t = Presence.Rogner(brut);
            string op = "";
            int i = -1;
            foreach (var o in Ops)
            {
                i = t.IndexOf(o, StringComparison.Ordinal);
                if (i > 0)
                {
                    op = o;
                    break;
                }
            }
            if (op == "") return null;
            string fait = t[..i], valeur = t[(i + op.Length)..];
            if (Array.IndexOf(Nombres, fait) >= 0)
            {
                if (!int.TryParse(valeur, NumberStyles.None, Ci, out var n)) return null;
                l.Add(new Terme(fait, op, valeur, n, false));
            }
            else if (Array.IndexOf(Textes, fait) >= 0 && op is "=" or "!=") l.Add(new Terme(fait, op, valeur, 0, true));
            else return null;
        }
        return l.Count == 0 ? null : l;
    }

    private static List<Trait>? _tous;

    public static IReadOnlyList<Trait> Tous => _tous ??= Lire(Ressource());

    public static Trait? Trouver(string id) => Tous.FirstOrDefault(t => t.Id == id);

    private static string Ressource()
    {
        try
        {
            using var flux = typeof(Traits).Assembly.GetManifestResourceStream("pilou:traits.txt");
            if (flux is null) return "";
            using var r = new StreamReader(flux, Encoding.UTF8);
            return r.ReadToEnd();
        }
        catch (IOException)
        {
            return "";
        }
    }

    // ---- Mesure

    // 1 lundi … 7 dimanche (le jour 0 de Presence.Jour, le 1er janvier 1970, est un jeudi).
    public static int JourDeSemaine(int jour) => (((jour + 3) % 7) + 7) % 7 + 1;

    public static int Lundi(int jour) => jour - (JourDeSemaine(jour) - 1);

    private static int Nombre(FaitsDuJour f, string fait, int jour, int ecart) => fait switch
    {
        "mn" => f.Mn, "tv" => f.Tv, "am" => f.Am, "ta" => f.Ta, "jx" => f.Jx, "ca" => f.Ca, "so" => f.So, "pc" => f.Pc, "pq" => f.Pq,
        "cu" => f.Cu, "qu" => f.Qu, "ce" => f.Ce, "vi" => f.Vi, "nv" => f.Nv, "mg" => f.Mg, "ma" => f.Ma,
        "we" => JourDeSemaine(jour) >= 6 ? 1 : 0, "sem" => JourDeSemaine(jour), "abs" => ecart, _ => 0,
    };

    private static string Texte(FaitsDuJour f, string fait) => fait switch
    {
        "ac" => f.Ac, "px" => f.Px, "cx" => f.Cx, "me" => f.Me, "cf" => f.Cf, "mo" => f.Mo, "ex" => f.Ex, "ob" => f.Ob, _ => "",
    };

    // Ce jour-là remplit-il la condition ? ecart : jours écoulés depuis la page précédente du journal (0 : première page).
    public static bool Vrai(Trait t, FaitsDuJour f, int jour, int ecart)
    {
        foreach (var c in t.Condition)
        {
            bool ok;
            if (c.Texte) ok = (Texte(f, c.Fait) == c.Valeur) == (c.Op == "=");
            else
            {
                int v = Nombre(f, c.Fait, jour, ecart);
                ok = c.Op switch { ">=" => v >= c.Nombre, "<=" => v <= c.Nombre, "=" => v == c.Nombre, _ => v != c.Nombre };
            }
            if (!ok) return false;
        }
        return true;
    }

    // Nombre de jours du journal, de « de » à « a » compris, qui remplissent la condition.
    public static int Mesure(Trait t, SortedDictionary<int, FaitsDuJour> journal, int de = int.MinValue, int a = int.MaxValue)
    {
        int n = 0, avant = int.MinValue;
        foreach (var (jour, f) in journal)
        {
            int ecart = avant == int.MinValue ? 0 : jour - avant;
            avant = jour;
            if (jour >= de && jour <= a && Vrai(t, f, jour, ecart)) n++;
        }
        return n;
    }

    // Le journal tel que les traits le lisent : un jour → ses faits fusionnés (tous appareils), sans les jours vides.
    public static SortedDictionary<int, FaitsDuJour> Journal(EtatPresence e)
    {
        var r = new SortedDictionary<int, FaitsDuJour>();
        foreach (var jour in e.Journal.Keys)
        {
            int j = Presence.JourDe(jour);
            if (j == int.MinValue) continue;
            var f = e.FaitsDu(jour);
            if (!f.Vide) r[j] = f;
        }
        return r;
    }

    // ---- Acquis : un bit par trait. Ce que le journal donne aujourd'hui ; l'appareil le garde par « ou » (jamais perdu).

    public static long Acquis(IEnumerable<Trait> traits, SortedDictionary<int, FaitsDuJour> journal)
    {
        long bits = 0;
        foreach (var t in traits)
            if (Mesure(t, journal) >= t.Seuil) bits |= t.Bit;
        return bits;
    }

    public static List<Trait> Parmi(IEnumerable<Trait> traits, long bits) => traits.Where(t => (bits & t.Bit) != 0).ToList();

    // Le prochain trait à annoncer (le plus petit numéro acquis et pas encore annoncé), ou null.
    public static Trait? AAnnoncer(IEnumerable<Trait> traits, long acquis, long annonces) =>
        Parmi(traits, acquis & ~annonces).FirstOrDefault();

    // ---- Dominants : trois au plus, les plus vécus récemment ; à égalité, le plus petit numéro.

    // Vivacité d'un trait : jours remplis pendant la fenêtre, rapportés au seuil (en millièmes).
    public static int Vivacite(Trait t, SortedDictionary<int, FaitsDuJour> journal, int aujourdhui)
    {
        int lundi = Lundi(aujourdhui);
        return Mesure(t, journal, lundi - Fenetre, lundi - 1) * 1000 / t.Seuil;
    }

    public static List<Trait> Dominants(IEnumerable<Trait> traits, long acquis, SortedDictionary<int, FaitsDuJour> journal, int aujourdhui) =>
        Parmi(traits, acquis).Select(t => (T: t, V: Vivacite(t, journal, aujourdhui)))
            .OrderByDescending(x => x.V).ThenBy(x => x.T.Numero).Take(NombreDominants).Select(x => x.T).ToList();

    // Les traits dominants de Pilou sur cet appareil, aujourd'hui (pour les répliques, « Pilou et moi » et, plus tard,
    // les saynètes). Réunit ce que tous les appareils du groupe ont découvert.
    public static List<Trait> Dominants(EtatPresence e, int aujourdhui) =>
        Dominants(Tous, e.Totaux().Traits, Journal(e), aujourdhui);

    // Découvre ce que le journal donne de nouveau ; vrai si un trait vient d'être acquis sur cet appareil.
    public static bool Decouvrir(EtatPresence e)
    {
        long avant = e.Moi.Traits;
        e.Moi.Traits |= Acquis(Tous, Journal(e));
        return e.Moi.Traits != avant;
    }

    // ---- Texte des bits (message entre appareils, fichier d'état) : hexadécimal, « 0 » si rien.

    public static string Hex(long bits) => bits.ToString("x", Ci);

    public static long DeHex(string s) =>
        s.Length is > 0 and <= 15 && long.TryParse(s, NumberStyles.AllowHexSpecifier, Ci, out var v) && v >= 0 ? v & ((1L << Max) - 1) : 0;
}
