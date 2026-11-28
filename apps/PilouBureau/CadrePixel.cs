using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace PilouBureau;

// Le cadre pixel de l'Aventure (docs/SCENES.md, « Style ») : la main de Pilou autour de ce qui se lit et se touche
// sous la scène (boîte de réplique, choix, cartouche du lieu), à l'image du menu « Sept portes » (MenuRetro.xaml).
// Tout est compté en unités U, le pixel de la scène (5 unités WPF à ×5) :
//   ombre portée de 1 U en bas et à droite ; bord de 1 U ; biseau de 1 U (clair en haut et à gauche, sombre en bas
//   et à droite) ; puis le fond, et le contenu avec un retrait de 1 U. Coins en escalier : le pixel de coin de chaque
//   couche est retiré (aucun arrondi lissé). Appuyé : fond de survol, plus d'ombre, contenu décalé de 1 U.
// Mêmes mesures que CadrePixel.java (téléphone).
internal sealed class CadrePixel : Decorator
{
    public static readonly Brush FondNuit = FenetreAventure.Gel("#151a2e"), Texte = FenetreAventure.Gel("#e6ecf2"),
        Pale = FenetreAventure.Gel("#adbac7"), Bord = FenetreAventure.Gel("#6a5acd"), Clair = FenetreAventure.Gel("#3a4270"),
        Sombre = FenetreAventure.Gel("#0b0e1a"), Ombre = FenetreAventure.Gel("#0b0e1a"), SurvolFond = FenetreAventure.Gel("#f69d50"),
        SurvolTexte = FenetreAventure.Gel("#151a2e"), Titre = FenetreAventure.Gel("#9b8cff"), Pointilles = FenetreAventure.Gel("#6a5acd");

    private double _u = 5;
    private bool _enfonce, _survol;

    public CadrePixel()
    {
        SnapsToDevicePixels = true;
        UseLayoutRounding = true;
    }

    // L'unité (le pixel de la scène, en unités WPF).
    public double U
    {
        get => _u;
        set
        {
            _u = Math.Max(1, value);
            InvalidateMeasure();
            InvalidateVisual();
        }
    }

    public Brush Fond { get; set; } = FondNuit;
    public Brush Couleur { get; set; } = Bord;
    public bool AvecOmbre { get; set; } = true;
    // Retrait du contenu dans le fond, en unités U.
    public double Retrait { get; set; } = 1;

    public bool Survol
    {
        get => _survol;
        set
        {
            if (_survol == value) return;
            _survol = value;
            InvalidateVisual();
            Change?.Invoke();
        }
    }

    public bool Enfonce
    {
        get => _enfonce;
        set
        {
            if (_enfonce == value) return;
            _enfonce = value;
            InvalidateArrange();
            InvalidateVisual();
        }
    }

    // Prévenu quand le survol change (le contenu peut changer de couleur).
    public event Action? Change;

    private double Ombre_ => AvecOmbre ? _u : 0;
    private double Bordure => (2 + Retrait) * _u;     // bord + biseau + retrait

    protected override Size MeasureOverride(Size dispo)
    {
        double e = Bordure * 2, o = Ombre_;
        var enfant = new Size(Math.Max(0, dispo.Width - e - o), Math.Max(0, dispo.Height - e - o));
        Child?.Measure(enfant);
        var d = Child?.DesiredSize ?? new Size(0, 0);
        return new Size(d.Width + e + o, d.Height + e + o);
    }

    protected override Size ArrangeOverride(Size taille)
    {
        double e = Bordure, o = Ombre_, dx = _enfonce ? o : 0;
        Child?.Arrange(new Rect(e + dx, e + dx, Math.Max(0, taille.Width - 2 * e - o), Math.Max(0, taille.Height - 2 * e - o)));
        return taille;
    }

    // Un rectangle aux coins en escalier : deux rectangles croisés (le pixel de coin reste vide).
    private void Escalier(DrawingContext dc, Brush b, double x, double y, double w, double h)
    {
        if (w <= 0 || h <= 0) return;
        double u = _u;
        if (w > 2 * u) dc.DrawRectangle(b, null, new Rect(x + u, y, w - 2 * u, h));
        if (h > 2 * u) dc.DrawRectangle(b, null, new Rect(x, y + u, w, h - 2 * u));
    }

    protected override void OnRender(DrawingContext dc)
    {
        double u = _u, o = Ombre_, W = ActualWidth - o, H = ActualHeight - o;
        if (W <= 2 * u || H <= 2 * u) return;
        double dx = _enfonce ? o : 0;
        // L'ombre portée (absente quand on appuie : le cadre descend dessus).
        if (o > 0 && !_enfonce) Escalier(dc, Ombre, o, o, W, H);
        // Le bord, puis le biseau et le fond.
        Escalier(dc, Couleur, dx, dx, W, H);
        double x = dx + u, y = dx + u, w = W - 2 * u, h = H - 2 * u;
        bool survol = _survol || _enfonce;
        dc.DrawRectangle(survol ? SurvolFond : Sombre, null, new Rect(x, y, w, h));
        if (!survol) dc.DrawRectangle(Clair, null, new Rect(x, y, w - u, h - u));
        dc.DrawRectangle(survol ? SurvolFond : Fond, null, new Rect(x + u, y + u, Math.Max(0, w - 2 * u), Math.Max(0, h - 2 * u)));
    }

    // Une puce « ▶ » en pixels de U (3 × 5 pixels), à la couleur donnée.
    public static UIElement Puce(double u, Brush couleur)
    {
        var g = new StreamGeometry();
        using (var c = g.Open())
        {
            void Pixel(double x, double y)
            {
                c.BeginFigure(new Point(x * u, y * u), true, true);
                c.LineTo(new Point((x + 1) * u, y * u), false, false);
                c.LineTo(new Point((x + 1) * u, (y + 1) * u), false, false);
                c.LineTo(new Point(x * u, (y + 1) * u), false, false);
            }
            foreach (var (x, y) in new[] { (0, 0), (0, 1), (1, 1), (0, 2), (1, 2), (2, 2), (0, 3), (1, 3), (0, 4) }) Pixel(x, y);
        }
        g.Freeze();
        return new System.Windows.Shapes.Path { Data = g, Fill = couleur, SnapsToDevicePixels = true, VerticalAlignment = VerticalAlignment.Top };
    }
}
