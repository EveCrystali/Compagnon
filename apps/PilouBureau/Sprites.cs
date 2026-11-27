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
    // Rendu fin : faux si ce sprite 2× vient de l'agrandissement automatique d'un sprite 1× (Agrandi) ; vrai s'il est
    // dessiné (assets/sprites2x, ou tout sprite 1×).
    public bool Natif { get; private set; } = true;

    private uint[]? _compilee;

    // Palette prête à peindre, par lettre : ARGB ; 0 : rien ; 1 à 4 : contour, ombre, base, clair de la teinte de
    // Pilou. Calculée une fois (le rendu ne relit pas les codes à chaque pixel).
    public uint[] Compilee()
    {
        if (_compilee is { } pret) return pret;
        var c = new uint[128];
        foreach (var (ch, code) in Palette)
            if (ch < 128)
                c[ch] = code switch { "@contour" => 1, "@ombre" => 2, "@base" => 3, "@clair" => 4, _ => Couleur(code) };
        return _compilee = c;
    }

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

    // ---- Agrandissement automatique (rendu fin) : même règle que rendu.agrandir (Python) et Sprites.agrandir (Java).
    // Règle « MMPX » (McGuire et Gagiu, 2021) : chaque pixel devient 2 × 2 pixels pris parmi lui-même et ses voisins,
    // sans flou ni nouvelle couleur ; les cernes sombres d'un pixel sont gardés, les diagonales et les pentes 2:1
    // lissées. Les couleurs se comparent par leur lettre ; le vide (« . », hors de l'image) compte comme une couleur.
    public Sprite Agrandi()
    {
        var g = new Sprite { Id = Id, Slot = Slot, Ancre = Ancre, Dx = Dx * 2, Dy = Dy * 2, Derriere = Derriere, Coiffe = Coiffe, Duree = Duree, Natif = false };
        foreach (var (k, v) in Palette) g.Palette[k] = v;
        foreach (var im in Images) g.Images.Add(AgrandirImage(im, Palette));
        return g;
    }

    // Clarté d'une couleur de palette : (r + v + b + 1) × (256 − alpha) ; vide : 256. Les références à la teinte de
    // Pilou prennent les valeurs du bleu, pour que l'agrandissement ne dépende pas de la teinte portée.
    public static int Clarte(string code)
    {
        code = code switch { "@contour" => "#1f4f8a", "@ombre" => "#4a8fdc", "@base" => "#6cb6ff", "@clair" => "#b4dbff", _ => code };
        if (code.Length < 7 || code[0] != '#') return 256;
        uint c = Couleur(code);
        return (int)(((c >> 16 & 0xff) + (c >> 8 & 0xff) + (c & 0xff) + 1) * (256 - (c >> 24)));
    }

    public static string[] AgrandirImage(string[] im, IReadOnlyDictionary<char, string> palette)
    {
        int h = im.Length, w = h == 0 ? 0 : im.Max(l => l.Length);
        var clarte = new Dictionary<char, int> { ['.'] = 256 };
        foreach (var (k, v) in palette) clarte[k] = Clarte(v);
        char Src(int x, int y) => y >= 0 && y < h && x >= 0 && x < im[y].Length ? im[y][x] : '.';
        int Cl(char ch) => clarte.TryGetValue(ch, out var v) ? v : 256;
        var sortie = new string[h * 2];
        var haut = new char[w * 2];
        var bas = new char[w * 2];
        for (int y = 0; y < h; y++)
        {
            for (int x = 0; x < w; x++)
            {
                char A = Src(x - 1, y - 1), B = Src(x, y - 1), C = Src(x + 1, y - 1);
                char D = Src(x - 1, y), E = Src(x, y), F = Src(x + 1, y);
                char G = Src(x - 1, y + 1), H = Src(x, y + 1), I = Src(x + 1, y + 1);
                char J = E, K = E, L = E, M = E;
                if (!(A == E && B == E && C == E && D == E && F == E && G == E && H == E && I == E))
                {
                    char P = Src(x, y - 2), S = Src(x, y + 2), Q = Src(x - 2, y), R = Src(x + 2, y);
                    int Bl = Cl(B), Dl = Cl(D), El = Cl(E), Fl = Cl(F), Hl = Cl(H);
                    // Pentes 1:1 (coins arrondis, diagonales lissées).
                    if (D == B && D != H && D != F && (El >= Dl || E == A) && (E == A || E == C || E == G) && (El < Dl || A != D || E != P || E != Q)) J = D;
                    if (B == F && B != D && B != H && (El >= Bl || E == C) && (E == A || E == C || E == I) && (El < Bl || C != B || E != P || E != R)) K = B;
                    if (H == D && H != F && H != B && (El >= Hl || E == G) && (E == A || E == G || E == I) && (El < Hl || G != H || E != S || E != Q)) L = H;
                    if (F == H && F != B && F != D && (El >= Fl || E == I) && (E == C || E == G || E == I) && (El < Fl || I != H || E != R || E != S)) M = F;
                    // Croisements.
                    if (E != F && E == C && E == I && E == D && E == Q && F == B && F == H && F != Src(x + 3, y)) K = M = F;
                    if (E != D && E == A && E == G && E == F && E == R && D == B && D == H && D != Src(x - 3, y)) J = L = D;
                    if (E != H && E == G && E == I && E == B && E == P && H == D && H == F && H != Src(x, y + 3)) L = M = H;
                    if (E != B && E == A && E == C && E == H && E == S && B == D && B == F && B != Src(x, y - 3)) J = K = B;
                    if (Bl < El && E == G && E == H && E == I && E == S && E != A && E != D && E != C && E != F) J = K = B;
                    if (Hl < El && E == A && E == B && E == C && E == P && E != D && E != G && E != I && E != F) L = M = H;
                    if (Fl < El && E == A && E == D && E == G && E == Q && E != B && E != C && E != I && E != H) K = M = F;
                    if (Dl < El && E == C && E == F && E == I && E == R && E != B && E != A && E != G && E != H) J = L = D;
                    // Pentes 2:1.
                    if (H != B)
                    {
                        if (H != A && H != E && H != C)
                        {
                            if (H == G && H == F && H == R && H != D && H != Src(x + 2, y - 1)) L = M;
                            if (H == I && H == D && H == Q && H != F && H != Src(x - 2, y - 1)) M = L;
                        }
                        if (B != I && B != G && B != E)
                        {
                            if (B == A && B == F && B == R && B != D && B != Src(x + 2, y + 1)) J = K;
                            if (B == C && B == D && B == Q && B != F && B != Src(x - 2, y + 1)) K = J;
                        }
                    }
                    if (F != D)
                    {
                        if (D != I && D != E && D != C)
                        {
                            if (D == A && D == H && D == S && D != B && D != Src(x + 1, y + 2)) J = L;
                            if (D == G && D == B && D == P && D != H && D != Src(x + 1, y - 2)) L = J;
                        }
                        if (F != E && F != A && F != G)
                        {
                            if (F == C && F == H && F == S && F != B && F != Src(x - 1, y + 2)) K = M;
                            if (F == I && F == B && F == P && F != H && F != Src(x - 1, y - 2)) M = K;
                        }
                    }
                }
                haut[x * 2] = J;
                haut[x * 2 + 1] = K;
                bas[x * 2] = L;
                bas[x * 2 + 1] = M;
            }
            sortie[y * 2] = new string(haut);
            sortie[y * 2 + 1] = new string(bas);
        }
        return sortie;
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

    // Rendu fin (grille 96 × 112) : sprites redessinés en 2× (assets/sprites2x) ; les autres sont agrandis à la
    // demande à partir du sprite 1× (Sprite.Agrandi) et gardés.
    public Dictionary<string, Sprite> Fins { get; } = new();
    private readonly Dictionary<string, Sprite?> _agrandis = new();

    // Sprite du rendu fin : le dessin 2× s'il existe, sinon le sprite 1× agrandi (calculé une fois).
    public Sprite? Fin(string id) => Fins.TryGetValue(id, out var natif) ? natif : Auto(id);

    // Le sprite 1× agrandi automatiquement (exactement deux fois plus grand, mêmes ancrages × 2), même s'il existe
    // un dessin fin : pour ce qui se place d'après la taille du sprite 1×.
    public Sprite? Auto(string id)
    {
        lock (_agrandis)
        {
            if (_agrandis.TryGetValue(id, out var s)) return s;
            return _agrandis[id] = Sprites.GetValueOrDefault(id)?.Agrandi();
        }
    }

    // Sprite fin de la taille exacte du sprite 1× doublé : le dessin fin s'il la respecte, sinon l'agrandi.
    public Sprite? FinExact(string id)
    {
        var s = this[id];
        if (s is null) return null;
        return Fins.TryGetValue(id, out var f) && f.W == s.W * 2 && f.H == s.H * 2 && f.Images.Count == s.Images.Count && f.Duree == s.Duree
            ? f : Auto(id);
    }

    // Sprite à l'échelle demandée (1 : grille 48 × 56 ; 2 : rendu fin).
    public Sprite? Echelle(string id, int echelle) => echelle == 2 ? Fin(id) : this[id];

    public static Banque DepuisDossier(string assets)
    {
        var b = new Banque();
        foreach (var f in Directory.EnumerateFiles(Path.Combine(assets, "sprites"), "*.txt"))
        {
            var s = Sprite.Lire(File.ReadAllText(f), Path.GetFileNameWithoutExtension(f));
            b.Sprites[s.Id] = s;
        }
        var fins = Path.Combine(assets, "sprites2x");
        if (Directory.Exists(fins))
            foreach (var f in Directory.EnumerateFiles(fins, "*.txt"))
            {
                var s = Sprite.Lire(File.ReadAllText(f), Path.GetFileNameWithoutExtension(f));
                b.Fins[s.Id] = s;
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
            bool fin = nom.StartsWith("sprite2x:", StringComparison.Ordinal);
            if (!fin && !nom.StartsWith("sprite:", StringComparison.Ordinal)) continue;
            if (nom == "sprite:index") continue;
            using var r = new StreamReader(a.GetManifestResourceStream(nom)!);
            var s = Sprite.Lire(r.ReadToEnd(), nom[(fin ? 9 : 7)..]);
            (fin ? b.Fins : b.Sprites)[s.Id] = s;
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

// Illustrations des campagnes (docs/SPRITES.md, « Décors et illustrations des campagnes ») : décor d'une scène
// (bandeau de 96 × 40, 192 × 80 en fin), timbre d'un souvenir, vignette d'une campagne, emblème d'un ton. Chaque
// fonction rend le sprite à l'échelle demandée (1, ou 2 : dessin fin), ou null si la banque ne l'a pas : l'interface
// garde alors son repli.
public static class Illustrations
{
    public const int DecorLargeur = 96, DecorHauteur = 40;

    public static string IdDecor(string campagne, string decor) => "decor-" + campagne + "-" + decor;
    public static string IdSouvenir(string campagne, string souvenir) => "souvenir-" + campagne + "-" + souvenir;
    public static string IdVignette(string campagne) => "campagne-" + campagne;
    public static string IdTon(string ton) => "ton-" + ton;

    public static Sprite? Decor(Banque b, string campagne, string? decor, int echelle = 2) =>
        string.IsNullOrEmpty(decor) ? null : Lire(b, IdDecor(campagne, decor), echelle);

    public static Sprite? Souvenir(Banque b, string campagne, string souvenir, int echelle = 2) =>
        Lire(b, IdSouvenir(campagne, souvenir), echelle);

    public static Sprite? Vignette(Banque b, string campagne, int echelle = 2) => Lire(b, IdVignette(campagne), echelle);

    public static Sprite? Ton(Banque b, string ton, int echelle = 2) => Lire(b, IdTon(ton), echelle);

    private static Sprite? Lire(Banque b, string id, int echelle) => b[id] is null ? null : b.Echelle(id, echelle);
}
