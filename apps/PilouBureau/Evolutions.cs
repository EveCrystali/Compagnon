using System.IO;
using System.Reflection;

namespace PilouBureau;

// Les scènes d'évolution (docs/SCENES.md, « Scènes d'évolution ») : lecteur de assets/evolutions.txt. Traduction exacte
// de outils/sprites/evolutions.py (référence) ; Evolutions.java fait de même sur Android. EvolutionsTests rejoue
// outils/sprites/evolutions-reference.txt.
public static class Evolutions
{
    public static readonly string[] Variantes = { "calin", "espiegle" };
    public const int MsLettre = 30, MsMin = 900, MsMax = 7000;

    public sealed record Element(string Sorte, string Cle, string Humeur, string Texte);

    public sealed record Replique(string Humeur, string Texte);

    public sealed class Scene
    {
        public int Stade { get; init; }
        public string Titre { get; set; } = "";
        public string Decor { get; set; } = "";
        // Morceau de assets/musiques.txt (docs/SONS.md) ; vide : la boucle du ton « émotion ».
        public string Musique { get; set; } = "";
        public string Question { get; set; } = "";
        public List<(string Id, string Libelle)> Options { get; } = new();
        public List<Element> Elements { get; } = new();
    }

    // { stade : scène } ; une ligne inconnue est ignorée (un fichier plus récent reste lisible).
    public static SortedDictionary<int, Scene> Lire(string texte)
    {
        var scenes = new SortedDictionary<int, Scene>();
        Scene? sc = null;
        foreach (var brute in texte.Split('\n'))
        {
            var ligne = brute.Trim();
            if (ligne.Length == 0 || ligne.StartsWith('#')) continue;
            var (mot, reste) = Couper(ligne);
            if (mot == "scene")
            {
                sc = new Scene { Stade = int.Parse(reste, System.Globalization.CultureInfo.InvariantCulture) };
                scenes[sc.Stade] = sc;
                continue;
            }
            if (sc is null) continue;
            switch (mot)
            {
                case "titre":
                    sc.Titre = reste;
                    break;
                case "decor":
                    sc.Decor = reste;
                    break;
                case "musique":
                    sc.Musique = reste;
                    break;
                case "pilou" or "calin" or "espiegle":
                {
                    var (h, t) = Couper(reste);
                    sc.Elements.Add(new Element(mot, "", h, t));
                    break;
                }
                case "choix":
                    sc.Question = reste;
                    sc.Elements.Add(new Element("choix", "", "", reste));
                    break;
                case "option":
                {
                    var (id, lib) = Couper(reste);
                    sc.Options.Add((id, lib));
                    break;
                }
                case "apres":
                {
                    var (id, r) = Couper(reste);
                    var (h, t) = Couper(r);
                    sc.Elements.Add(new Element("apres", id, h, t));
                    break;
                }
            }
        }
        return scenes;
    }

    // Comme str.partition(" ") : le premier mot, puis le reste (vide s'il n'y a pas d'espace).
    private static (string, string) Couper(string s)
    {
        int i = s.IndexOf(' ');
        return i < 0 ? (s, "") : (s[..i], s[(i + 1)..]);
    }

    // La variante du stade (Soins.Variante) ; inconnue ou absente : câline.
    public static string Variante(string? v) => v is "calin" or "espiegle" ? v : "calin";

    // Les répliques dites, dans l'ordre. choix null : jusqu'à la question (incluse, humeur vide) ; sinon toute la scène,
    // avec la réplique de ce choix.
    public static List<Replique> Deroule(Scene sc, string? variante, string? choix)
    {
        var v = Variante(variante);
        var r = new List<Replique>();
        foreach (var e in sc.Elements)
        {
            if (e.Sorte == "pilou" || e.Sorte == v) r.Add(new Replique(e.Humeur, e.Texte));
            else if (e.Sorte == "choix")
            {
                if (choix is null)
                {
                    r.Add(new Replique("", e.Texte));
                    return r;
                }
            }
            else if (e.Sorte == "apres" && e.Cle == choix) r.Add(new Replique(e.Humeur, e.Texte));
        }
        return r;
    }

    // Le temps que Pilou met à écrire une réplique (et à la dire dans la scène).
    public static int MsEcriture(string texte) => Math.Max(MsMin, Math.Min(MsMax, MsLettre * texte.Length));

    private static SortedDictionary<int, Scene>? _embarquees;

    // Les scènes embarquées dans l'exe (ressource « pilou:evolutions.txt »).
    public static SortedDictionary<int, Scene> Embarquees()
    {
        if (_embarquees is not null) return _embarquees;
        using var st = Assembly.GetExecutingAssembly().GetManifestResourceStream("pilou:evolutions.txt");
        if (st is null) return _embarquees = new();
        using var rd = new StreamReader(st);
        return _embarquees = Lire(rd.ReadToEnd());
    }

    // Le libellé de ce que Pilou a gardé à ce stade (pour le Carnet), ou "".
    public static string Garde(Scene sc, string? id) => sc.Options.FirstOrDefault(o => o.Id == id).Libelle ?? "";
}
