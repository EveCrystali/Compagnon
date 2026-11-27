using System.IO;
using System.Reflection;
using System.Text;

namespace PilouBureau;

// La police pixel de Pilou, sa voix écrite (docs/POLICE.md) : glyphes lus dans assets/police/*.txt (écrits par
// outils/sprites/police.py), mise en page (largeur, coupure des lignes, espaces fines du français) identique au
// Python et à Android (PolicePixel.java), vérifiée par outils/sprites/police-reference.txt. Sans WPF : testable.
// Tout se compte en points de code (un emoji hors du plan de base est un seul caractère, comme en Python).
public sealed class PolicePixel
{
    public sealed record Glyphe(int Largeur, int Haut, string[] Rangs);

    private readonly Dictionary<int, Glyphe> _glyphes = new();
    private readonly Dictionary<long, int> _crenage = new();

    public int Echelle { get; private set; } = 1;
    public int Hauteur { get; private set; } = 12;   // rangées d'un glyphe, à son échelle
    public int Ligne { get; private set; } = 12;     // pas d'une ligne, en pixels 1×
    public int Chasse { get; private set; } = 1;
    public int Inconnu { get; private set; } = 6;    // case d'un caractère sans dessin (la police système le dessine)

    private const string AvantFine = "!?;:»›";
    private const string ApresFine = "«‹";
    private const string InsecableAvant = AvantFine + "  …,.";
    private const string InsecableApres = ApresFine + "  ";

    private static bool Dans(string s, int c) => c < 0x10000 && s.Contains((char)c);

    public static PolicePixel Lire(string contenu)
    {
        var p = new PolicePixel();
        var lignes = contenu.Replace("\r\n", "\n").Split('\n');
        for (int i = 0; i < lignes.Length; i++)
        {
            var l = lignes[i];
            if (l == "" || l.StartsWith('#')) continue;
            var t = l.Split(' ', StringSplitOptions.RemoveEmptyEntries);
            if (t[0] == "@")
            {
                int code = Convert.ToInt32(t[1], 16), larg = int.Parse(t[2]), haut = int.Parse(t[3]);
                var rangs = new List<string>();
                while (i + 1 < lignes.Length && lignes[i + 1] != "") rangs.Add(lignes[++i]);
                p._glyphes[code] = new Glyphe(larg, haut, rangs.ToArray());
            }
            else if (t[0] == "~")
                p._crenage[Cle(Convert.ToInt32(t[1], 16), Convert.ToInt32(t[2], 16))] = int.Parse(t[3]);
            else
            {
                int v = int.Parse(t[1]);
                switch (t[0])
                {
                    case "echelle": p.Echelle = v; break;
                    case "hauteur": p.Hauteur = v; break;
                    case "ligne": p.Ligne = v; break;
                    case "chasse": p.Chasse = v; break;
                    case "inconnu": p.Inconnu = v; break;
                }
            }
        }
        return p;
    }

    // Polices embarquées (« texte », « titre », et leur dessin fin « texte2x », « titre2x »), lues une fois.
    private static readonly Dictionary<string, PolicePixel?> Cache = new();

    public static PolicePixel? Ressource(string nom)
    {
        lock (Cache)
        {
            if (Cache.TryGetValue(nom, out var p)) return p;
            using var st = Assembly.GetExecutingAssembly().GetManifestResourceStream("police:" + nom + ".txt");
            p = st is null ? null : Lire(new StreamReader(st, Encoding.UTF8).ReadToEnd());
            Cache[nom] = p;
            return p;
        }
    }

    public static PolicePixel? Texte => Ressource("texte");
    public static PolicePixel? Titre => Ressource("titre");

    private static long Cle(int a, int b) => ((long)a << 32) | (uint)b;

    public bool Connu(int code) => _glyphes.ContainsKey(code);

    public Glyphe? GlypheDe(int code) => _glyphes.GetValueOrDefault(code);

    public int Crenage(int a, int b) => _crenage.GetValueOrDefault(Cle(a, b));

    public int LargeurGlyphe(int code) => _glyphes.TryGetValue(code, out var g) ? g.Largeur : Inconnu;

    public static int[] Codes(string s)
    {
        var r = new List<int>(s.Length);
        foreach (var rune in s.EnumerateRunes()) r.Add(rune.Value);
        return r.ToArray();
    }

    private static string Chaine(int[] c, int debut, int fin)
    {
        var b = new StringBuilder();
        for (int i = debut; i < fin; i++) b.Append(char.ConvertFromUtf32(c[i]));
        return b.ToString();
    }

    // Largeur en pixels 1× d'un texte préparé, sur une seule ligne.
    public int Largeur(string s) => Largeur(Codes(s), 0, Codes(s).Length);

    private int Largeur(int[] c, int debut, int fin)
    {
        int w = 0;
        for (int i = debut; i < fin; i++)
        {
            if (i > debut) w += Chasse + Crenage(c[i - 1], c[i]);
            w += LargeurGlyphe(c[i]);
        }
        return w;
    }

    // Apostrophe courbe, espace fine insécable avant ! ? ; : » et après «, sans sélecteurs de variante.
    public static string Preparer(string texte)
    {
        var t = Codes(texte.Replace("\r\n", "\n").Replace('\r', '\n')).Where(c => c != 0xFE0F && c != 0xFE0E && c != 0x200D).ToArray();
        var b = new StringBuilder();
        for (int i = 0; i < t.Length; i++)
        {
            int c = t[i];
            if (c == '\'') c = '’';
            if (c == ' ')
            {
                bool avant = i + 1 < t.Length && t[i + 1] < 0x10000 && AvantFine.Contains((char)t[i + 1]);
                bool apres = i > 0 && t[i - 1] < 0x10000 && ApresFine.Contains((char)t[i - 1]);
                if (avant || apres) c = 0x202F;
            }
            b.Append(char.ConvertFromUtf32(c));
        }
        return b.ToString();
    }

    private static bool Espace(int c) => c == ' ' || c == 0x2009;

    // Lignes d'un texte coupé à maxLargeur pixels 1× (0 : sans limite), au plus maxLignes (0 : toutes ; la dernière
    // finit alors par « … »). Même règle que mettre_en_page (outils/sprites/police.py).
    public List<string> Couper(string texte, int maxLargeur = 0, int maxLignes = 0)
    {
        var t = Codes(Preparer(texte));
        var morceaux = new List<(int[] M, int Sep)>(); // Sep : espace mangée, -1 après trait d'union, '\n', -2 fin
        var cour = new List<int>();
        foreach (int c in t)
        {
            if (Espace(c) || c == '\n')
            {
                morceaux.Add((cour.ToArray(), c));
                cour.Clear();
            }
            else if (c == '-' || c == 0x2010)
            {
                cour.Add(c);
                morceaux.Add((cour.ToArray(), -1));
                cour.Clear();
            }
            else cour.Add(c);
        }
        morceaux.Add((cour.ToArray(), -2));

        bool Tient(List<int> s, int n) => maxLargeur <= 0 || Largeur(s.ToArray(), 0, n) <= maxLargeur;

        var lignes = new List<List<int>>();
        var ligne = new List<int>();
        int attente = 0; // l'espace entre la ligne et le morceau suivant (0 : aucune)
        foreach (var (m, sep) in morceaux)
        {
            if (m.Length == 0 && Espace(sep))
            {
                if (ligne.Count > 0 && attente == 0) attente = sep;
                continue;
            }
            if (m.Length > 0)
            {
                if (ligne.Count == 0) ligne = m.ToList();
                else
                {
                    var cand = new List<int>(ligne);
                    if (attente != 0) cand.Add(attente);
                    cand.AddRange(m);
                    if (Tient(cand, cand.Count)) ligne = cand;
                    else
                    {
                        lignes.Add(ligne);
                        ligne = m.ToList();
                    }
                }
                while (!Tient(ligne, ligne.Count) && ligne.Count > 1)
                {
                    int n = 1;
                    while (n < ligne.Count && Tient(ligne, n + 1)) n++;
                    // Jamais de « ! », « ? », « » » ni d'espace insécable en tête de ligne, ni de « « » en fin.
                    while (n > 1 && (Dans(InsecableAvant, ligne[n]) || Dans(InsecableApres, ligne[n - 1]))) n--;
                    lignes.Add(ligne.Take(n).ToList());
                    ligne = ligne.Skip(n).ToList();
                }
            }
            attente = Espace(sep) ? sep : 0;
            if (sep == '\n')
            {
                lignes.Add(ligne);
                ligne = new List<int>();
            }
        }
        lignes.Add(ligne);
        if (maxLignes > 0 && lignes.Count > maxLignes)
        {
            var der = new List<int>(lignes[maxLignes - 1]);
            while (der.Count > 0)
            {
                var essai = new List<int>(der) { '…' };
                if (Tient(essai, essai.Count)) break;
                der.RemoveAt(der.Count - 1);
            }
            while (der.Count > 0 && (Espace(der[^1]) || der[^1] == 0x202F || der[^1] == 0xA0)) der.RemoveAt(der.Count - 1);
            der.Add('…');
            lignes = lignes.Take(maxLignes - 1).Append(der).ToList();
        }
        return lignes.Select(l => Chaine(l.ToArray(), 0, l.Count)).ToList();
    }

    // Un glyphe posé : position (pixels 1×) de sa case, son code, et son dessin (null : la police système le dessine).
    public readonly record struct Pose(int X, int Y, int Code, Glyphe? Dessin);

    public IEnumerable<Pose> Poser(IReadOnlyList<string> lignes)
    {
        for (int i = 0; i < lignes.Count; i++)
        {
            var c = Codes(lignes[i]);
            int x = 0;
            for (int k = 0; k < c.Length; k++)
            {
                if (k > 0) x += Chasse + Crenage(c[k - 1], c[k]);
                var g = _glyphes.GetValueOrDefault(c[k]);
                yield return new Pose(x, i * Ligne, c[k], g);
                x += g?.Largeur ?? Inconnu;
            }
        }
    }

    // Pixels allumés, à l'échelle de la police (dessin fin : deux fois plus de pixels).
    public IEnumerable<(int X, int Y)> Pixels(IReadOnlyList<string> lignes)
    {
        foreach (var p in Poser(lignes))
        {
            if (p.Dessin is null) continue;
            for (int r = 0; r < p.Dessin.Rangs.Length; r++)
            for (int k = 0; k < p.Dessin.Rangs[r].Length; k++)
                if (p.Dessin.Rangs[r][k] == '#') yield return (p.X * Echelle + k, p.Y * Echelle + p.Dessin.Haut + r);
        }
    }

    // FNV-1a 32 bits des pixels allumés, en ordre de lecture (comme police.py).
    public uint Empreinte(IReadOnlyList<string> lignes)
    {
        uint h = 2166136261;
        foreach (var (x, y) in Pixels(lignes).Distinct().OrderBy(p => p.Y).ThenBy(p => p.X))
            h = unchecked((h ^ (uint)(x * 65536 + y)) * 16777619);
        return h;
    }

    // Taille de la boîte d'un texte coupé, en pixels 1× : la plus longue ligne, et toutes les lignes.
    public (int Largeur, int Hauteur) Boite(IReadOnlyList<string> lignes) =>
        (lignes.Count == 0 ? 0 : lignes.Max(Largeur), lignes.Count == 0 ? 0 : (lignes.Count - 1) * Ligne + Hauteur / Echelle);
}
