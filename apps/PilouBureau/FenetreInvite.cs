using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Interop;
using System.Windows.Media;

namespace PilouBureau;

// Le Pilou d'un ami, en visite sur cet écran : une petite fenêtre transparente (comme celle de Pilou),
// dessinée par le même moteur avec SES couleurs, son stade, sa variante, ses objets et son accessoire.
// Une bulle au-dessus pour ce qu'il raconte. Un clic dessus : on le caresse.
public sealed class FenetreInvite : Window
{
    private const double Largeur = 300, HauteurBulle = 96;

    private readonly Scene _scene = new();
    private readonly Border _bulle;
    // Le nom et la phrase de l'invité, dans la police pixel de Pilou (la même taille que sa bulle : BullePixel.cs).
    private readonly TextePixel _texte = new("", Brushes.Black) { MaxLignes = 4, Margin = new Thickness(0, 0, 0, 2) };
    private readonly TextePixel _nom = new("", Brushes.Black) { Titre = true, MaxLignes = 1 };
    private readonly double _k;
    private double _bulleJusque = -1e12;

    public event Action? Caresse;

    public FenetreInvite(string nom, double k, bool sombre)
    {
        _k = k;
        WindowStyle = WindowStyle.None;
        AllowsTransparency = true;
        Background = Brushes.Transparent;
        ShowInTaskbar = false;
        ResizeMode = ResizeMode.NoResize;
        ShowActivated = false;
        Topmost = true;
        Title = $"{nom} en visite";

        // Bulle de l'invité : bord orange (celle de Pilou est bleue), nom en tête.
        var fond = Gel(sombre ? "#2d333b" : "#f6f8fa");
        var texte = Gel(sombre ? "#cdd9e5" : "#1c2128");
        _texte.Couleur = texte;
        _nom.Couleur = Gel(sombre ? "#f69d50" : "#9c4a0a");
        _nom.Texte = nom;
        var pile = new StackPanel();
        pile.Children.Add(_nom);
        pile.Children.Add(_texte);
        _bulle = new Border
        {
            BorderThickness = new Thickness(3),
            BorderBrush = Gel(sombre ? "#f69d50" : "#c86a1c"),
            Background = fond,
            Padding = new Thickness(8, 3, 8, 5),
            MaxWidth = Largeur - 20,
            HorizontalAlignment = HorizontalAlignment.Center,
            VerticalAlignment = VerticalAlignment.Bottom,
            Child = pile,
            Visibility = Visibility.Hidden,
            RenderTransform = new TranslateTransform(0, Scene.MargeY + 4 * Scene.PA),
        };
        _scene.Width = Scene.Largeur;
        _scene.Height = Scene.Hauteur;
        _scene.Cursor = Cursors.Hand;
        _scene.HorizontalAlignment = HorizontalAlignment.Center;
        _scene.ToolTip = $"{nom} est en visite · clic : le caresser";
        _scene.MouseLeftButtonUp += (_, e) =>
        {
            Caresse?.Invoke();
            e.Handled = true;
        };

        var racine = new Grid { LayoutTransform = new ScaleTransform(k, k) };
        racine.RowDefinitions.Add(new RowDefinition { Height = new GridLength(HauteurBulle) });
        racine.RowDefinitions.Add(new RowDefinition { Height = new GridLength(Scene.Hauteur) });
        Grid.SetRow(_bulle, 0);
        Grid.SetRow(_scene, 1);
        racine.Children.Add(_bulle);
        racine.Children.Add(_scene);
        Content = racine;
        Width = Largeur * k;
        Height = (HauteurBulle + Scene.Hauteur) * k;
        SourceInitialized += (_, _) => Natif.StyleDiscret(new WindowInteropHelper(this).Handle);
    }

    private static Brush Gel(string hex)
    {
        var b = new SolidColorBrush((Color)ColorConverter.ConvertFromString(hex));
        b.Freeze();
        return b;
    }

    public void Dire(string texte, double maintenant, double ms = 4500)
    {
        _texte.Texte = texte;
        _bulleJusque = maintenant + ms;
        _bulle.Visibility = Visibility.Visible;
    }

    private double _zoneGauche = double.NegativeInfinity, _zoneDroite = double.PositiveInfinity;

    // Écran de l'hôte : l'invité qui entre par le bord apparaît au bord, pas sur l'écran voisin.
    public void Borner(double zoneGauche, double zoneDroite)
    {
        _zoneGauche = zoneGauche;
        _zoneDroite = zoneDroite;
    }

    // x : milieu des pieds ; pieds : ordonnée du sol (unités WPF de l'écran).
    public void Poser(Pose p, double x, double pieds, double maintenant)
    {
        if (maintenant > _bulleJusque && _bulle.Visibility == Visibility.Visible) _bulle.Visibility = Visibility.Hidden;
        _scene.Pose = p;
        _scene.InvalidateVisual();
        Left = Math.Round(x - Largeur / 2 * _k);
        Top = Math.Round(pieds - (HauteurBulle + Scene.Sol) * _k);
        if (Finesse.Active)
        {
            Left = Placement.Aligner(Left, Finesse.Dpi);
            Top = Placement.Aligner(Top, Finesse.Dpi);
        }
        // Partie de la fenêtre sur l'écran de l'hôte (unités avant k) ; le reste est découpé.
        double x0 = Math.Clamp((_zoneGauche - Left) / _k, 0, Largeur), x1 = Math.Clamp((_zoneDroite - Left) / _k, 0, Largeur);
        var racine = (FrameworkElement)Content;
        racine.Clip = x0 <= 0 && x1 >= Largeur ? null : new RectangleGeometry(new Rect(x0, -4000, Math.Max(0, x1 - x0), 8000));
    }
}
