using System.Windows;
using System.Windows.Media;

namespace PilouBureau;

// Petit dessin en pixels (même style que Pilou) : un motif, une palette, un contour automatique.
// Seuls les pixels dessinés prennent la souris.
public sealed class Pixels : FrameworkElement
{
    private int[,] _motif;
    private Brush?[] _palette;
    private readonly Brush? _contour;
    private readonly double _t;

    public Pixels(int[,] motif, Brush?[] palette, Brush? contour = null, double taille = Scene.P)
    {
        _motif = motif;
        _palette = palette;
        _contour = contour;
        _t = taille;
        Width = (motif.GetLength(1) + 2) * taille;
        Height = (motif.GetLength(0) + 2) * taille;
        SnapsToDevicePixels = true;
    }

    public Brush?[] Palette
    {
        get => _palette;
        set
        {
            _palette = value;
            InvalidateVisual();
        }
    }

    // Motif et palette d'une image d'un sprite de la banque (assets/sprites) ; null s'il manque.
    public static (int[,] Motif, Brush?[] Palette)? DeSprite(string id, double t = 0, bool miroir = false)
    {
        var s = Banque.Commune[id];
        if (s is null) return null;
        var g = Banque.Grille(s, t);
        int h = g.GetLength(0), w = g.GetLength(1);
        var couleurs = new List<uint>();
        var m = new int[h, w];
        for (int y = 0; y < h; y++)
        for (int x = 0; x < w; x++)
        {
            uint c = g[y, miroir ? w - 1 - x : x];
            if (c == 0) continue;
            int i = couleurs.IndexOf(c);
            if (i < 0)
            {
                couleurs.Add(c);
                i = couleurs.Count - 1;
            }
            m[y, x] = i + 1;
        }
        var palette = new Brush?[couleurs.Count + 1];
        for (int i = 0; i < couleurs.Count; i++) palette[i + 1] = Scene.Pinceau(couleurs[i]);
        return (m, palette);
    }

    // Un objet de la banque (prise, plat, jeu…), à la taille de pixel voulue (Scene.PX : celle de Pilou).
    public static Pixels? Sprite(string id, double taille = Scene.PX, double t = 0, bool miroir = false) =>
        DeSprite(id, t, miroir) is { } d ? new Pixels(d.Motif, d.Palette, null, taille) : null;

    // Image suivante d'un sprite animé (même taille, même palette si les couleurs n'ont pas bougé).
    public void Changer(string id, double t, bool miroir = false)
    {
        if (DeSprite(id, t, miroir) is not { } d) return;
        _palette = d.Palette;
        Changer(d.Motif);
    }

    public void Changer(int[,] motif)
    {
        _motif = motif;
        InvalidateVisual();
    }

    protected override void OnRender(DrawingContext dc)
    {
        int h = _motif.GetLength(0), w = _motif.GetLength(1);
        bool Plein(int r, int c) => r >= 0 && c >= 0 && r < h && c < w && _motif[r, c] > 0;
        for (int r = -1; r <= h; r++)
        for (int c = -1; c <= w; c++)
        {
            Brush? br = null;
            if (Plein(r, c)) br = _motif[r, c] < _palette.Length ? _palette[_motif[r, c]] : null;
            else if (_contour is not null && (Plein(r - 1, c) || Plein(r + 1, c) || Plein(r, c - 1) || Plein(r, c + 1))) br = _contour;
            if (br is not null) dc.DrawRectangle(br, null, new Rect((c + 1) * _t, (r + 1) * _t, _t, _t));
        }
    }

    // Police 3 × 5 pour « +10 xp » et « NIVEAU 4 ».
    private static readonly Dictionary<char, string[]> Police = new()
    {
        ['0'] = new[] { "111", "101", "101", "101", "111" },
        ['1'] = new[] { "010", "110", "010", "010", "111" },
        ['2'] = new[] { "111", "001", "111", "100", "111" },
        ['3'] = new[] { "111", "001", "111", "001", "111" },
        ['4'] = new[] { "101", "101", "111", "001", "001" },
        ['5'] = new[] { "111", "100", "111", "001", "111" },
        ['6'] = new[] { "111", "100", "111", "101", "111" },
        ['7'] = new[] { "111", "001", "010", "010", "010" },
        ['8'] = new[] { "111", "101", "111", "101", "111" },
        ['9'] = new[] { "111", "101", "111", "001", "111" },
        ['+'] = new[] { "000", "010", "111", "010", "000" },
        ['x'] = new[] { "000", "101", "010", "101", "000" },
        ['p'] = new[] { "000", "110", "101", "110", "100" },
        ['N'] = new[] { "101", "111", "111", "101", "101" },
        ['I'] = new[] { "111", "010", "010", "010", "111" },
        ['V'] = new[] { "101", "101", "101", "101", "010" },
        ['E'] = new[] { "111", "100", "110", "100", "111" },
        ['A'] = new[] { "010", "101", "111", "101", "101" },
        ['U'] = new[] { "101", "101", "101", "101", "111" },
        ['T'] = new[] { "111", "010", "010", "010", "010" },
        ['O'] = new[] { "111", "101", "101", "101", "111" },
        ['C'] = new[] { "111", "100", "100", "100", "111" },
        ['Z'] = new[] { "111", "001", "010", "100", "111" },
        ['!'] = new[] { "1", "1", "1", "0", "1" },
        ['S'] = new[] { "111", "100", "111", "001", "111" },
        // Le reste de l'alphabet (enseigne « BOUTIQUE », « RANGÉE DÉBLOQUÉE »…).
        ['B'] = new[] { "110", "101", "110", "101", "110" },
        ['D'] = new[] { "110", "101", "101", "101", "110" },
        ['F'] = new[] { "111", "100", "110", "100", "100" },
        ['G'] = new[] { "111", "100", "101", "101", "111" },
        ['H'] = new[] { "101", "101", "111", "101", "101" },
        ['J'] = new[] { "001", "001", "001", "101", "111" },
        ['K'] = new[] { "101", "101", "110", "101", "101" },
        ['L'] = new[] { "100", "100", "100", "100", "111" },
        ['M'] = new[] { "10001", "11011", "10101", "10001", "10001" },
        ['P'] = new[] { "111", "101", "111", "100", "100" },
        ['Q'] = new[] { "111", "101", "101", "111", "001" },
        ['R'] = new[] { "110", "101", "110", "101", "101" },
        ['W'] = new[] { "10001", "10001", "10101", "11011", "10001" },
        ['X'] = new[] { "101", "101", "010", "101", "101" },
        ['Y'] = new[] { "101", "101", "010", "010", "010" },
        ['É'] = new[] { "111", "100", "110", "100", "111" },
        ['-'] = new[] { "000", "000", "111", "000", "000" },
        ['.'] = new[] { "0", "0", "0", "0", "1" },
        ['/'] = new[] { "001", "001", "010", "100", "100" },
        [' '] = new[] { "0", "0", "0", "0", "0" },
    };

    public static int[,] Texte(string texte)
    {
        var glyphes = texte.Select(c => Police.TryGetValue(c, out var g) ? g : Police[' ']).ToList();
        int largeur = glyphes.Sum(g => g[0].Length) + Math.Max(0, glyphes.Count - 1);
        var m = new int[5, largeur];
        int x = 0;
        foreach (var g in glyphes)
        {
            for (int r = 0; r < 5; r++)
            for (int c = 0; c < g[r].Length; c++)
                m[r, x + c] = g[r][c] == '1' ? 1 : 0;
            x += g[0].Length + 1;
        }
        return m;
    }

    public static int[,] Motif(params string[] lignes)
    {
        var m = new int[lignes.Length, lignes[0].Length];
        for (int r = 0; r < lignes.Length; r++)
        for (int c = 0; c < lignes[r].Length; c++)
            m[r, c] = lignes[r][c] - '0';
        return m;
    }
}
