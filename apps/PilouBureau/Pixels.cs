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
    private double _t;          // taille d'une cellule dessinée
    private int _marge = 1;     // cellules vides autour du motif (2 en dessin fin : la même place que le dessin 1×)
    private int _echelle = 1;   // 2 : sprite du dessin fin (Affiner)

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

    // Dessin fin : passe au sprite deux fois plus fin de la banque (le dessin 2× s'il a exactement la taille doublée,
    // sinon le sprite 1× agrandi automatiquement). L'élément garde sa place et sa taille : seules les cellules sont
    // deux fois plus petites. Sans effet si le dessin fin est coupé ou si le sprite manque.
    public Pixels Affiner(string id, double t = 0, bool miroir = false)
    {
        if (!Finesse.Active || _echelle == 2) return this;
        if (DeSprite(Banque.Commune.FinExact(id), t, miroir) is not { } d) return this;
        if (d.Motif.GetLength(0) != _motif.GetLength(0) * 2 || d.Motif.GetLength(1) != _motif.GetLength(1) * 2) return this;
        _motif = d.Motif;
        _palette = d.Palette;
        _t /= 2;
        _marge = 2;
        _echelle = 2;
        // Cellules de taille entière en pixels physiques (Finesse.Net) : bords francs, sans lissage.
        RenderOptions.SetEdgeMode(this, EdgeMode.Aliased);
        InvalidateVisual();
        return this;
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
    public static (int[,] Motif, Brush?[] Palette)? DeSprite(string id, double t = 0, bool miroir = false) =>
        DeSprite(Banque.Commune[id], t, miroir);

    private static (int[,] Motif, Brush?[] Palette)? DeSprite(Sprite? s, double t, bool miroir)
    {
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

    // Un objet de la banque (prise, plat, jeu…), à la taille de pixel voulue (Scene.PX : celle de Pilou). En dessin
    // fin, la taille est ramenée à un nombre pair de pixels physiques et le sprite fin est dessiné (pixels entiers).
    // dansPilou : l'élément vit dans la fenêtre de Pilou (mise à l'échelle par la Taille) ; sinon dans une autre
    // fenêtre (menu, boutique), à l'échelle de l'écran.
    public static Pixels? Sprite(string id, double taille = Scene.PX, double t = 0, bool miroir = false, bool dansPilou = true) =>
        DeSprite(id, t, miroir) is { } d
            ? new Pixels(d.Motif, d.Palette, null, dansPilou ? Finesse.Net(taille) : Finesse.ZoomNet(taille)).Affiner(id, t, miroir)
            : null;

    // Image suivante d'un sprite animé (même taille, même palette si les couleurs n'ont pas bougé).
    public void Changer(string id, double t, bool miroir = false)
    {
        if (DeSprite(_echelle == 2 ? Banque.Commune.FinExact(id) : Banque.Commune[id], t, miroir) is not { } d) return;
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
        Brush? Cellule(int r, int c)
        {
            if (Plein(r, c)) return _motif[r, c] < _palette.Length ? _palette[_motif[r, c]] : null;
            return _contour is not null && (Plein(r - 1, c) || Plein(r + 1, c) || Plein(r, c - 1) || Plein(r, c + 1)) ? _contour : null;
        }
        // Une ligne à la fois ; les cellules voisines de même couleur font un seul rectangle.
        for (int r = -1; r <= h; r++)
        {
            int c = -1;
            while (c <= w)
            {
                var br = Cellule(r, c);
                if (br is null)
                {
                    c++;
                    continue;
                }
                int fin = c + 1;
                while (fin <= w && ReferenceEquals(Cellule(r, fin), br)) fin++;
                dc.DrawRectangle(br, null, new Rect((c + _marge) * _t, (r + _marge) * _t, (fin - c) * _t, _t));
                c = fin;
            }
        }
    }

    // Police 3 × 5 (« +10 xp », « NIVEAU 4 ») : Police.cs, commune avec les jeux dessinés sans WPF.
    public static int[,] Texte(string texte) => Police.Texte(texte);

    public static int[,] Motif(params string[] lignes)
    {
        var m = new int[lignes.Length, lignes[0].Length];
        for (int r = 0; r < lignes.Length; r++)
        for (int c = 0; c < lignes[r].Length; c++)
            m[r, c] = lignes[r][c] - '0';
        return m;
    }
}
