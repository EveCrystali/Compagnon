using System.Globalization;
using System.IO;
using System.Reflection;

namespace PilouBureau;

// Banque de sprites partagée avec l'app Android : assets/sprites/<id>.txt (format décrit dans docs/SPRITES.md),
// assets/teintes.txt, assets/tenues.txt, assets/plats.txt. Embarqués dans l'exécutable (ressources) ;
// les tests les lisent dans le dossier assets/ du dépôt.
public sealed class Sprite
{
    public string Id { get; init; } = "";
    public string Slot { get; set; } = "objet";
    public string Ancre { get; set; } = "aucun";
    public int Dx { get; set; }
    public int Dy { get; set; }
    public bool Derriere { get; set; }
    public bool Coiffe { get; set; }
    public int Duree { get; set; }
    // Couleur par lettre : ARGB, ou une référence à la teinte de Pilou (@contour, @ombre, @base, @clair).
    public Dictionary<char, string> Palette { get; } = new();
    public List<string[]> Images { get; } = new();

    public int W => Images.Count == 0 ? 0 : Images[0].Max(l => l.Length);
    public int H => Images.Count == 0 ? 0 : Images[0].Length;

    public string[] Image(double t)
    {
        if (Images.Count == 0) return Array.Empty<string>();
        if (Duree <= 0 || Images.Count == 1) return Images[0];
        return Images[(int)(Math.Floor(Math.Max(0, t) / Duree) % Images.Count)];
    }

    public static Sprite Lire(string texte, string id = "")
    {
        var s = new Sprite { Id = id };
        var image = new List<string>();
        bool dans = false;
        string? idLu = null;
        foreach (var brut in texte.Replace("\r", "").Split('\n'))
        {
            var ligne = brut.TrimEnd();
            if (!dans)
            {
                if (ligne.Length == 0 || ligne.StartsWith('#')) continue;
                int i = ligne.IndexOf(':');
                if (i < 0) continue;
                string cle = ligne[..i].Trim(), val = ligne[(i + 1)..].Trim();
                switch (cle)
                {
                    case "images": dans = true; break;
                    case "id": idLu = val; break;
                    case "slot": s.Slot = val; break;
                    case "ancre": s.Ancre = val; break;
                    case "decalage":
                        var p = val.Split(' ', StringSplitOptions.RemoveEmptyEntries);
                        s.Dx = int.Parse(p[0], CultureInfo.InvariantCulture);
                        s.Dy = int.Parse(p[1], CultureInfo.InvariantCulture);
                        break;
                    case "couche": s.Derriere = val == "derriere"; break;
                    case "coiffe": s.Coiffe = val == "oui"; break;
                    case "duree": s.Duree = int.Parse(val, CultureInfo.InvariantCulture); break;
                    case "palette":
                        foreach (var paire in val.Split(' ', StringSplitOptions.RemoveEmptyEntries))
                            if (paire.Length > 2 && paire[1] == '=') s.Palette[paire[0]] = paire[2..];
                        break;
                }
            }
            else if (ligne == "---")
            {
                s.Images.Add(image.ToArray());
                image.Clear();
            }
            else if (ligne.Length > 0) image.Add(ligne);
        }
        if (image.Count > 0) s.Images.Add(image.ToArray());
        return idLu is null ? s : new Sprite
        {
            Id = idLu, Slot = s.Slot, Ancre = s.Ancre, Dx = s.Dx, Dy = s.Dy, Derriere = s.Derriere, Coiffe = s.Coiffe, Duree = s.Duree,
        }.Copier(s);
    }

    private Sprite Copier(Sprite de)
    {
        foreach (var (k, v) in de.Palette) Palette[k] = v;
        Images.AddRange(de.Images);
        return this;
    }

    // Couleur ARGB d'un code de palette (#rrggbb ou #rrggbbaa) ; 0 = transparent ou inconnu.
    public static uint Couleur(string code)
    {
        if (code.Length < 7 || code[0] != '#') return 0;
        uint rgb = uint.Parse(code.AsSpan(1, 6), NumberStyles.HexNumber, CultureInfo.InvariantCulture);
        uint a = code.Length >= 9 ? uint.Parse(code.AsSpan(7, 2), NumberStyles.HexNumber, CultureInfo.InvariantCulture) : 0xff;
        return a << 24 | rgb;
    }
}

public sealed class Banque
{
    public Dictionary<string, Sprite> Sprites { get; } = new();
    // Teinte : contour, ombre, base, clair (ARGB).
    public Dictionary<string, uint[]> Teintes { get; } = new();
    public Dictionary<string, string[]> Tenues { get; } = new();
    public Dictionary<string, string> Plats { get; } = new();

    public Sprite? this[string id] => Sprites.GetValueOrDefault(id);

    public static Banque DepuisDossier(string assets)
    {
        var b = new Banque();
        foreach (var f in Directory.EnumerateFiles(Path.Combine(assets, "sprites"), "*.txt"))
        {
            var s = Sprite.Lire(File.ReadAllText(f), Path.GetFileNameWithoutExtension(f));
            b.Sprites[s.Id] = s;
        }
        b.Tables(n => File.ReadAllText(Path.Combine(assets, n)));
        return b;
    }

    // Ressources embarquées : « sprite:<id> » et « pilou:<fichier> » (voir PilouBureau.csproj).
    public static Banque DepuisRessources(Assembly a)
    {
        var b = new Banque();
        foreach (var nom in a.GetManifestResourceNames())
        {
            if (!nom.StartsWith("sprite:", StringComparison.Ordinal)) continue;
            if (nom == "sprite:index") continue;
            using var r = new StreamReader(a.GetManifestResourceStream(nom)!);
            var s = Sprite.Lire(r.ReadToEnd(), nom[7..]);
            b.Sprites[s.Id] = s;
        }
        b.Tables(n =>
        {
            using var st = a.GetManifestResourceStream("pilou:" + n);
            if (st is null) return "";
            using var r = new StreamReader(st);
            return r.ReadToEnd();
        });
        return b;
    }

    private static Banque? _commune;

    // La banque de l'application (ressources de l'exécutable) ; vide si elles manquent : rien ne plante.
    public static Banque Commune => _commune ??= DepuisRessources(typeof(Banque).Assembly);

    public static void Utiliser(Banque b) => _commune = b;

    private void Tables(Func<string, string> lire)
    {
        foreach (var (nom, valeurs) in Lignes(lire("teintes.txt")))
            if (valeurs.Length == 4) Teintes[nom] = valeurs.Select(Sprite.Couleur).ToArray();
        foreach (var (nom, valeurs) in Lignes(lire("tenues.txt"))) Tenues[nom] = valeurs;
        foreach (var (nom, valeurs) in Lignes(lire("plats.txt")))
            if (valeurs.Length > 0) Plats[nom] = valeurs[0];
    }

    private static IEnumerable<(string, string[])> Lignes(string texte)
    {
        foreach (var brut in texte.Replace("\r", "").Split('\n'))
        {
            var l = brut.Trim();
            int i = l.IndexOf(':');
            if (l.Length == 0 || l.StartsWith('#') || i < 0) continue;
            yield return (l[..i].Trim(), l[(i + 1)..].Split(' ', StringSplitOptions.RemoveEmptyEntries));
        }
    }

    // Sprite du plat d'une recette (plat inventé : « inv:… » ; plat brûlé : plat-rate).
    public string Plat(string idRecette, bool rate) =>
        rate ? "plat-rate" : Plats.TryGetValue(idRecette, out var s) ? s : "plat-invente";

    // Grille de couleurs ARGB d'une image d'un sprite objet (ni teinte, ni ancre) : pour les jeux.
    public static uint[,] Grille(Sprite s, double t = 0)
    {
        var im = s.Image(t);
        int h = im.Length, w = s.W;
        var g = new uint[h, w];
        for (int y = 0; y < h; y++)
        for (int x = 0; x < im[y].Length; x++)
            if (im[y][x] != '.' && s.Palette.TryGetValue(im[y][x], out var c)) g[y, x] = Sprite.Couleur(c);
        return g;
    }
}
