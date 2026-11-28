using System.Windows;
using System.Windows.Media;

namespace PilouBureau;

// Le titre-logo d'une fenêtre (« BOUTIQUE », « AVENTURE », « JOURNAL »…) au pixel fin (docs/STYLE.md, « Titres-logos »).
// Les lettres sont celles de la police « titre » en dessin fin (titre2x : capitales de 14 pixels de haut), chaque
// pixel valant un module (2 unités WPF, ramenées à un nombre entier de pixels physiques) : le logo a donc le pixel de
// la scène et des cadres, et non un pixel de police agrandi quatre ou cinq fois. Ce que ce pixel fin permet :
//   un relief (arête claire en haut de chaque trait, arête sombre en bas),
//   un cerne d'encre d'un pixel,
//   une ombre portée d'un pixel en bas à droite, à la couleur du bord.
// Seule la boîte de l'encre est gardée (pas de rangées vides au-dessus ni dessous). Une ligne, capitales.
internal sealed class LogoPixel : FrameworkElement
{
    private readonly string _texte;
    private Brush _couleur, _clair, _sombre;
    private readonly Brush _cerne, _ombre;
    private byte[,]? _grille;   // 0 vide, 1 ombre, 2 cerne, 3 corps, 4 arête claire, 5 arête sombre

    // Unités WPF par pixel du logo : le module des fenêtres du PC.
    public double Pixel { get; set; } = 2;

    public LogoPixel(string texte, Brush couleur, Brush? ombre = null, Brush? cerne = null)
    {
        _texte = StylePixel.Capitales(texte);
        _couleur = _clair = _sombre = couleur;
        _ombre = ombre ?? Bandeau.Bord;
        _cerne = cerne ?? Bandeau.Encre;
        Teinter(couleur);
        SnapsToDevicePixels = true;
        RenderOptions.SetEdgeMode(this, EdgeMode.Aliased);
        IsHitTestVisible = false;
        HorizontalAlignment = HorizontalAlignment.Left;
    }

    // Couleur du corps ; les deux arêtes du relief en sont déduites (plus claire, plus sombre).
    public Brush Couleur
    {
        get => _couleur;
        set
        {
            if (ReferenceEquals(_couleur, value)) return;
            Teinter(value);
            InvalidateVisual();
        }
    }

    private void Teinter(Brush couleur)
    {
        _couleur = couleur;
        var c = couleur is SolidColorBrush s ? s.Color : Colors.White;
        _clair = Gel(Meler(c, Colors.White, 0.45));
        _sombre = Gel(Meler(c, Color.FromRgb(0x2a, 0x1a, 0x3a), 0.38));
    }

    private static Color Meler(Color a, Color b, double t) => Color.FromRgb(
        (byte)Math.Round(a.R + (b.R - a.R) * t), (byte)Math.Round(a.G + (b.G - a.G) * t), (byte)Math.Round(a.B + (b.B - a.B) * t));

    private static Brush Gel(Color c)
    {
        var b = new SolidColorBrush(c);
        b.Freeze();
        return b;
    }

    // La grille du logo, en pixels fins : l'encre des lettres, son relief, son cerne et son ombre.
    private byte[,] Grille()
    {
        if (_grille is not null) return _grille;
        var police = (Finesse.Active ? PolicePixel.Ressource("titre2x") : null) ?? PolicePixel.Titre;
        if (police is null) return _grille = new byte[0, 0];
        int e = police.Echelle, f = 2 / e;   // f : pixels du logo par pixel de la police (1 en dessin fin, 2 sinon)
        var lignes = new List<string> { PolicePixel.Preparer(_texte) };
        int largeur = police.Largeur(lignes[0]) * 2, hauteur = police.Ligne * 2;
        var encre = new bool[hauteur, largeur + 2];
        int haut = int.MaxValue, bas = -1, droite = 0;
        foreach (var pose in police.Poser(lignes))
        {
            if (pose.Dessin is null) continue;
            var rangs = pose.Dessin.Rangs;
            for (int r = 0; r < rangs.Length; r++)
            for (int k = 0; k < rangs[r].Length; k++)
            {
                if (rangs[r][k] != '#') continue;
                for (int dy = 0; dy < f; dy++)
                for (int dx = 0; dx < f; dx++)
                {
                    int x = pose.X * 2 + k * f + dx, y = pose.Y * 2 + (pose.Dessin.Haut + r) * f + dy;
                    if (y < 0 || y >= hauteur || x < 0 || x >= largeur + 2) continue;
                    encre[y, x] = true;
                    haut = Math.Min(haut, y);
                    bas = Math.Max(bas, y);
                    droite = Math.Max(droite, x);
                }
            }
        }
        if (bas < 0) return _grille = new byte[0, 0];
        // Marge d'un pixel pour le cerne, puis d'un autre en bas à droite pour l'ombre.
        int w = droite + 1 + 3, h = bas - haut + 1 + 3;
        var g = new byte[h, w];
        bool Encre(int y, int x) => y >= 0 && y <= bas - haut && x >= 0 && x <= droite && encre[y + haut, x];
        bool Plein(int y, int x)
        {
            for (int dy = -1; dy <= 1; dy++)
            for (int dx = -1; dx <= 1; dx++)
                if (Encre(y + dy, x + dx)) return true;
            return false;
        }
        for (int y = -1; y < h - 1; y++)
        for (int x = -1; x < w - 1; x++)
        {
            byte v = 0;
            if (Encre(y, x)) v = !Encre(y - 1, x) ? (byte)4 : !Encre(y + 1, x) ? (byte)5 : (byte)3;
            else if (Plein(y, x)) v = 2;
            else if (Plein(y - 1, x - 1)) v = 1;
            g[y + 1, x + 1] = v;
        }
        return _grille = g;
    }

    private double Unite()
    {
        double ppu = Math.Max(0.1, StylePixel.Physique(this));
        return PolicePixel.PixelsPhysiques(Pixel, ppu) / ppu;
    }

    protected override Size MeasureOverride(Size dispo)
    {
        var g = Grille();
        double u = Unite();
        return new Size(g.GetLength(1) * u, g.GetLength(0) * u);
    }

    protected override void OnRender(DrawingContext dc)
    {
        var g = Grille();
        double u = Unite();
        int h = g.GetLength(0), w = g.GetLength(1);
        for (int y = 0; y < h; y++)
        {
            int x = 0;
            while (x < w)
            {
                byte v = g[y, x];
                int fin = x;
                while (fin < w && g[y, fin] == v) fin++;
                if (v != 0)
                    dc.DrawRectangle(v switch { 1 => _ombre, 2 => _cerne, 4 => _clair, 5 => _sombre, _ => _couleur }, null,
                        new Rect(x * u, y * u, (fin - x) * u, u));
                x = fin;
            }
        }
    }
}
