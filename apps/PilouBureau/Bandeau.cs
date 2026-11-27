using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Threading;

namespace PilouBureau;

// Bandeau de progression, le même partout (boutique, menu de Pilou, info-bulle) : niveau, barre d'XP en
// pixels, pièces d'or avec une pièce qui tourne, titre ; et, s'il y en a une, la prochaine rangée de boutique.
// Couleurs : bleu (XP), orange (po), argent, violet ; jamais d'opposition rouge / vert. L'énergie des expéditions
// (⚡, Expeditions.cs) s'affiche sous les po dès que Pilou la donne (Bandeau.Energie), sans rien changer aux appelants.
internal sealed class Bandeau : Border
{
    public static readonly Brush Nuit = Gel("#151a2e"), Nuit2 = Gel("#1f2540"), Bord = Gel("#6a5acd"), Argent = Gel("#adbac7"),
        ArgentClair = Gel("#e6ecf2"), BleuXp = Gel("#6cb6ff"), BleuSombre = Gel("#2d333b"), OrangePo = Gel("#f69d50"),
        Violet = Gel("#9b8cff"), Encre = Gel("#1c2128"), BleuClair = Gel("#b4dbff");

    private readonly ContentControl _niveau = new();
    private readonly TextBlock _titre = new() { Foreground = Argent, FontSize = 11, FontFamily = new FontFamily("Segoe UI") };
    private readonly StackPanel _barre = new() { Orientation = Orientation.Horizontal, Margin = new Thickness(0, 3, 0, 2) };
    private readonly TextBlock _xp = new() { Foreground = Argent, FontSize = 10.5, FontFamily = new FontFamily("Segoe UI") };
    private readonly Pixels? _piece = Pixels.Sprite("po-tourne", 2, dansPilou: false);
    private readonly TextBlock _po = new()
    {
        Foreground = OrangePo, FontSize = 17, FontWeight = FontWeights.Bold, FontFamily = new FontFamily("Consolas"),
        VerticalAlignment = VerticalAlignment.Center, Margin = new Thickness(4, 0, 0, 0),
    };
    private readonly TextBlock _suite = new()
    {
        Foreground = Violet, FontSize = 11, FontFamily = new FontFamily("Segoe UI"), TextWrapping = TextWrapping.Wrap,
        Margin = new Thickness(0, 4, 0, 0),
    };
    private readonly TextBlock _energie = new()
    {
        Foreground = Gel("#f5d76e"), FontSize = 12, FontWeight = FontWeights.Bold, FontFamily = new FontFamily("Consolas"),
        HorizontalAlignment = HorizontalAlignment.Right, Margin = new Thickness(0, 2, 0, 0), Visibility = Visibility.Collapsed,
        ToolTip = "Énergie des expéditions : elle remonte en travaillant, en mangeant, et un peu toute seule",
    };
    private readonly DispatcherTimer? _horloge;

    // Énergie des expéditions (0 à 100), fournie par Pilou ; null : pas d'énergie affichée.
    public static Func<int>? Energie;
    private double _t;
    private string _cle = "";

    private static Brush Gel(string hex)
    {
        var b = new SolidColorBrush((Color)ColorConverter.ConvertFromString(hex));
        b.Freeze();
        return b;
    }

    // Les animations suivent le réglage Windows « Afficher les animations » (mouvement réduit sinon).
    public static bool Anime => SystemParameters.ClientAreaAnimation;

    public Bandeau(bool compact = false)
    {
        Background = Nuit;
        BorderBrush = Bord;
        BorderThickness = new Thickness(2);
        Padding = new Thickness(10, 6, 12, 6);
        SnapsToDevicePixels = true;
        var grille = new Grid();
        grille.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        grille.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        grille.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        _niveau.VerticalAlignment = VerticalAlignment.Center;
        _niveau.Margin = new Thickness(0, 0, 10, 0);
        grille.Children.Add(_niveau);
        var milieu = new StackPanel { VerticalAlignment = VerticalAlignment.Center, MinWidth = compact ? 150 : 220 };
        milieu.Children.Add(_titre);
        milieu.Children.Add(_barre);
        milieu.Children.Add(_xp);
        Grid.SetColumn(milieu, 1);
        grille.Children.Add(milieu);
        var po = new StackPanel { Orientation = Orientation.Horizontal, VerticalAlignment = VerticalAlignment.Center };
        if (_piece is not null) po.Children.Add(_piece);
        po.Children.Add(_po);
        var droite = new StackPanel { VerticalAlignment = VerticalAlignment.Center, Margin = new Thickness(14, 0, 0, 0) };
        droite.Children.Add(po);
        droite.Children.Add(_energie);
        Grid.SetColumn(droite, 2);
        grille.Children.Add(droite);
        var pile = new StackPanel();
        pile.Children.Add(grille);
        pile.Children.Add(_suite);
        Child = pile;
        RenderOptions.SetEdgeMode(this, EdgeMode.Aliased);
        if (_piece is not null && Anime)
        {
            _horloge = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(120) };
            _horloge.Tick += (_, _) =>
            {
                _t += 120;
                _piece.Changer("po-tourne", _t);
            };
            Loaded += (_, _) => _horloge.Start();
            Unloaded += (_, _) => _horloge.Stop();
        }
    }

    // Niveau n, XP totale, solde, titre ; suite : « Prochaine rangée : … » (vide : rien).
    public void Mettre(int niveau, int xp, int po, string titre, string suite = "")
    {
        // L'info-bulle se remet à jour souvent : rien à refaire si rien n'a changé.
        int? energie = Energie?.Invoke();
        var cle = $"{niveau}|{xp}|{po}|{titre}|{suite}|{energie}";
        if (cle == _cle) return;
        _cle = cle;
        _niveau.Content = Pastille(niveau);
        _titre.Text = titre;
        int de = Profil.XpPourNiveau(niveau), a = Profil.XpPourNiveau(niveau + 1);
        double x = a > de ? Math.Clamp((xp - de) / (double)(a - de), 0, 1) : 1;
        _barre.Children.Clear();
        const int cases = 20;
        int pleines = (int)Math.Floor(x * cases);
        for (int i = 0; i < cases; i++)
            _barre.Children.Add(new Border
            {
                Width = 7, Height = 8, Margin = new Thickness(0, 0, 1, 0),
                Background = i < pleines ? BleuXp : BleuSombre,
                BorderBrush = i < pleines ? BleuClair : Encre, BorderThickness = new Thickness(0, 1, 0, 0),
            });
        _xp.Text = $"{Math.Max(0, xp - de)} / {a - de} xp · encore {Math.Max(0, a - xp)} xp avant le niveau {niveau + 1}";
        _po.Text = $"{po} po";
        _energie.Text = energie is { } en ? $"⚡ {en}/100" : "";
        _energie.Visibility = energie is null ? Visibility.Collapsed : Visibility.Visible;
        _suite.Text = suite;
        _suite.Visibility = suite == "" ? Visibility.Collapsed : Visibility.Visible;
    }

    // « NIV » au-dessus du nombre, en police pixel, sur une pastille argent cerclée de violet.
    private static UIElement Pastille(int niveau)
    {
        var pile = new StackPanel { HorizontalAlignment = HorizontalAlignment.Center };
        pile.Children.Add(new Pixels(Pixels.Texte("NIV"), new Brush?[] { null, Argent }, null, 2) { HorizontalAlignment = HorizontalAlignment.Center });
        pile.Children.Add(new Pixels(Pixels.Texte(niveau.ToString()), new Brush?[] { null, ArgentClair }, Encre, 4)
            { HorizontalAlignment = HorizontalAlignment.Center });
        return new Border
        {
            Background = Nuit2, BorderBrush = Violet, BorderThickness = new Thickness(2), Padding = new Thickness(6, 3, 6, 4), Child = pile,
            MinWidth = 52,
        };
    }

    // « Prochaine rangée : Dos, Main — niveau 15 (encore 340 xp) » ; vide quand tout est ouvert.
    public static string ProchaineRangee(int niveau, int xp)
    {
        int p = Boutique.ProchainPalier(niveau);
        if (p == 0) return "Toutes les rangées de la boutique sont ouvertes.";
        var rayons = Boutique.RayonsDuPalier(p).Select(Boutique.NomSlot).ToList();
        string liste = rayons.Count <= 3 ? string.Join(", ", rayons) : string.Join(", ", rayons.Take(3)) + $" +{rayons.Count - 3}";
        return $"▲ Prochaine rangée : {liste} — niveau {p} (encore {Math.Max(0, Profil.XpPourNiveau(p) - xp)} xp)";
    }
}

// Rendus de Pilou pour l'interface (boutique, fiches) : même rendu commun que la scène (RenduPilou).
internal static class Apercu
{
    // fin : rendu fin (grille 96 × 112) si le réglage « Dessin fin » est actif. L'image garde sa taille en unités
    // (48 × 56 : elle porte 192 points par pouce), les mises en page ne changent pas.
    public static BitmapSource Image(Allure a, bool silhouette = false, bool fin = false)
    {
        int e = fin && Finesse.Active ? 2 : 1;
        var pixels = RenduPilou.Rendre(a, Banque.Commune, e);
        return Bitmap(pixels, RenduPilou.W * e, RenduPilou.H * e, silhouette, 96.0 * e);
    }

    // Comme Image, mais rien si les pixels sont ceux de l'image précédente (vues animées : pas de bitmap refait
    // quand Pilou n'a pas bougé). precedent : gardé par l'appelant d'un appel à l'autre.
    public static BitmapSource? ImageSiChange(Allure a, ref uint[]? precedent, bool fin = false)
    {
        int e = fin && Finesse.Active ? 2 : 1;
        var pixels = RenduPilou.Rendre(a, Banque.Commune, e);
        if (precedent is not null && pixels.AsSpan().SequenceEqual(precedent)) return null;
        precedent = pixels;
        return Bitmap(pixels, RenduPilou.W * e, RenduPilou.H * e, false, 96.0 * e);
    }

    public static BitmapSource Bitmap(uint[] pixels, int w, int h, bool silhouette = false, double dpi = 96)
    {
        var bgra = new byte[pixels.Length * 4];
        for (int i = 0; i < pixels.Length; i++)
        {
            uint c = pixels[i];
            if (silhouette && c >> 24 != 0) c = 0xFF3B4654;
            bgra[i * 4] = (byte)c;
            bgra[i * 4 + 1] = (byte)(c >> 8);
            bgra[i * 4 + 2] = (byte)(c >> 16);
            bgra[i * 4 + 3] = (byte)(c >> 24);
        }
        var image = BitmapSource.Create(w, h, dpi, dpi, PixelFormats.Bgra32, null, bgra, w * 4);
        image.Freeze();
        return image;
    }

    // Une image d'un sprite de la banque (décor, icône), en bitmap ; null s'il manque.
    public static BitmapSource? Sprite(string id, double t = 0, bool silhouette = false)
    {
        var s = Banque.Commune[id];
        if (s is null) return null;
        var g = Banque.Grille(s, t);
        int h = g.GetLength(0), w = g.GetLength(1);
        var px = new uint[w * h];
        for (int y = 0; y < h; y++)
        for (int x = 0; x < w; x++)
            px[y * w + x] = g[y, x];
        return Bitmap(px, w, h, silhouette);
    }

    public static Image Vue(ImageSource source, double zoom)
    {
        var im = new Image { Source = source, Width = source.Width * zoom, Height = source.Height * zoom, Stretch = Stretch.Fill };
        RenderOptions.SetBitmapScalingMode(im, BitmapScalingMode.NearestNeighbor);
        return im;
    }
}
