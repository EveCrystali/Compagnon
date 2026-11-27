using System.Globalization;
using System.Windows;
using System.Windows.Media;

namespace PilouBureau;

// Un texte écrit avec la police pixel de Pilou (PolicePixel.cs, docs/POLICE.md) : coupé à la largeur disponible,
// chaque pixel de police sur un nombre entier de pixels physiques, dessin fin (2×) quand il tombe juste. Un caractère
// sans dessin (emoji…) est dessiné par la police système dans sa case. Toute la boîte prend la souris (Tag gardé).
public sealed class TextePixel : FrameworkElement
{
    private string _texte = "";
    private Brush _couleur = Brushes.Black;
    private List<string> _lignes = new();
    private double _unite = 1;          // unités WPF par pixel de police (1×)
    private int _largeurMax;            // en pixels de police, celle de la dernière mesure

    // Pixels physiques par unité de cet élément (mise à l'échelle de Windows × échelle de la fenêtre). Par défaut,
    // ceux de la fenêtre de Pilou (Placement.cs) ; une autre fenêtre donne les siens.
    public Func<double> PhysiqueParUnite { get; set; } = () => Finesse.PhysiqueParUnite;

    // Taille voulue d'un pixel de police, en unités WPF : ramenée au nombre entier de pixels physiques le plus proche.
    public double Taille { get; set; } = 1.3;

    public bool Titre { get; set; }

    public int MaxLignes { get; set; }

    public TextePixel(string texte, Brush couleur)
    {
        _texte = texte;
        _couleur = couleur;
        SnapsToDevicePixels = true;
        RenderOptions.SetEdgeMode(this, EdgeMode.Aliased);
    }

    public string Texte
    {
        get => _texte;
        set
        {
            if (_texte == value) return;
            _texte = value;
            InvalidateMeasure();
            InvalidateVisual();
        }
    }

    public Brush Couleur
    {
        get => _couleur;
        set
        {
            _couleur = value;
            InvalidateVisual();
        }
    }

    // Pixels physiques par pixel de police : au moins 1, le plus proche de la taille voulue.
    public static int PixelsPhysiques(double taille, double physiqueParUnite) =>
        Math.Max(1, (int)Math.Round(taille * physiqueParUnite, MidpointRounding.AwayFromZero));

    private PolicePixel? Police => Titre ? PolicePixel.Titre : PolicePixel.Texte;

    private PolicePixel? PoliceDessin(int n) =>
        Finesse.Active && n % 2 == 0 ? PolicePixel.Ressource(Titre ? "titre2x" : "texte2x") ?? Police : Police;

    protected override Size MeasureOverride(Size dispo)
    {
        var p = Police;
        double ppu = Math.Max(0.1, PhysiqueParUnite());
        int n = PixelsPhysiques(Taille, ppu);
        _unite = n / ppu;
        if (p is null) return new Size(0, 0);
        _largeurMax = double.IsInfinity(dispo.Width) ? 0 : Math.Max(1, (int)Math.Floor(dispo.Width / _unite));
        _lignes = p.Couper(_texte, _largeurMax, MaxLignes);
        var (w, h) = p.Boite(_lignes);
        return new Size(w * _unite, h * _unite);
    }

    protected override void OnRender(DrawingContext dc)
    {
        var p = Police;
        if (p is null) return;
        // Toute la boîte prend la souris (un clic entre deux lettres reste sur le texte).
        dc.DrawRectangle(Brushes.Transparent, null, new Rect(RenderSize));
        double ppu = Math.Max(0.1, PhysiqueParUnite());
        int n = PixelsPhysiques(Taille, ppu);
        var dessin = PoliceDessin(n) ?? p;
        double pas = _unite / dessin.Echelle;
        var geo = new StreamGeometry();
        using (var g = geo.Open())
        {
            foreach (var pose in dessin.Poser(_lignes))
            {
                if (pose.Dessin is null)
                {
                    if (pose.Code is not (' ' or 0xA0 or 0x202F or 0x2009)) Systeme(dc, pose, p);
                    continue;
                }
                var rangs = pose.Dessin.Rangs;
                for (int r = 0; r < rangs.Length; r++)
                {
                    int k = 0;
                    while (k < rangs[r].Length)
                    {
                        if (rangs[r][k] != '#')
                        {
                            k++;
                            continue;
                        }
                        int fin = k;
                        while (fin < rangs[r].Length && rangs[r][fin] == '#') fin++;
                        double x = pose.X * _unite + k * pas, y = pose.Y * _unite + (pose.Dessin.Haut + r) * pas;
                        g.BeginFigure(new Point(x, y), true, true);
                        g.LineTo(new Point(x + (fin - k) * pas, y), false, false);
                        g.LineTo(new Point(x + (fin - k) * pas, y + pas), false, false);
                        g.LineTo(new Point(x, y + pas), false, false);
                        k = fin;
                    }
                }
            }
        }
        geo.Freeze();
        dc.DrawGeometry(_couleur, null, geo);
    }

    // Secours : un caractère sans dessin, écrit par la police système au milieu de sa case.
    private void Systeme(DrawingContext dc, PolicePixel.Pose pose, PolicePixel p)
    {
        var ft = new FormattedText(char.ConvertFromUtf32(pose.Code), CultureInfo.CurrentUICulture, FlowDirection.LeftToRight,
            new Typeface("Segoe UI Symbol"), 9 * _unite, _couleur, 1.0);
        double cx = pose.X * _unite + p.Inconnu * _unite / 2, cy = pose.Y * _unite + 6.5 * _unite;
        dc.DrawText(ft, new Point(cx - ft.Width / 2, cy - ft.Height / 2));
    }
}
