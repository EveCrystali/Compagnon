using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Threading;

namespace PilouBureau;

// Bandeau de progression, le même partout (boutique, menu de Pilou, info-bulle, Aventure, expéditions) : niveau,
// barre d'XP, pièces d'or avec une pièce qui tourne, titre ; et, s'il y en a une, la prochaine rangée de boutique.
// Tout est en pixels au module de 2 (docs/STYLE.md, « En-tête commun ») : textes en police pixel, nombre du niveau en
// logo fin, barre d'XP par pas de 2. Couleurs : bleu (XP), orange (po), argent, violet ; jamais d'opposition
// rouge / vert. L'énergie des expéditions (Expeditions.cs) s'affiche sous les po dès que Pilou la donne (Bandeau.Energie).
internal sealed class Bandeau : Border
{
    public static readonly Brush Nuit = Gel("#151a2e"), Nuit2 = Gel("#1f2540"), Bord = Gel("#6a5acd"), Argent = Gel("#adbac7"),
        ArgentClair = Gel("#e6ecf2"), BleuXp = Gel("#6cb6ff"), BleuSombre = Gel("#2d333b"), OrangePo = Gel("#f69d50"),
        Violet = Gel("#9b8cff"), Encre = Gel("#1c2128"), BleuClair = Gel("#b4dbff");

    private static readonly Brush Jaune = Gel("#f5d76e");

    private readonly ContentControl _niveau = new();
    private readonly StackPanel _milieu;
    private readonly TextePixel _titre = StylePixel.Texte("", Argent, StylePixel.Corps);
    private readonly StackPanel _barre = new() { Orientation = Orientation.Horizontal };
    private readonly TextePixel _xp = StylePixel.Texte("", Argent, StylePixel.Corps);
    private readonly Pixels? _piece = Pixels.Sprite("po-tourne", 2, dansPilou: false);
    private readonly TextePixel _po = StylePixel.Texte("", OrangePo, StylePixel.Corps, true);
    private readonly TextePixel _suite = StylePixel.Texte("", Violet, StylePixel.Corps);
    private readonly TextePixel _energieTexte = StylePixel.Etiquette("", Jaune);
    private readonly StackPanel _energie = new()
    {
        Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right, Margin = new Thickness(0, 2, 0, 0),
        Visibility = Visibility.Collapsed, Background = Brushes.Transparent,
        ToolTip = "Énergie des expéditions : elle remonte en travaillant, en mangeant, et un peu toute seule",
    };
    private readonly DispatcherTimer? _horloge;

    // Énergie des expéditions (0 à 100), fournie par Pilou ; null : pas d'énergie affichée.
    public static Func<int>? Energie;
    private double _t;
    private string _cle = "";
    private string[] _formesXp = { "" }, _formesSuite = Array.Empty<string>();

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
        UseLayoutRounding = true;
        var grille = new Grid();
        grille.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        grille.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        grille.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        _niveau.VerticalAlignment = VerticalAlignment.Center;
        _niveau.Margin = new Thickness(0, 0, 10, 0);
        _niveau.Focusable = false;
        grille.Children.Add(_niveau);
        // Une ligne de police pixel a trois rangées d'accents au-dessus des minuscules : les lignes se resserrent.
        _titre.Margin = new Thickness(0, -4, 0, 2);
        _titre.MaxLignes = 1;
        _xp.Margin = new Thickness(0, -2, 0, -2);
        _xp.MaxLignes = 1;
        _milieu = new StackPanel { VerticalAlignment = VerticalAlignment.Center, MinWidth = compact ? 150 : 220 };
        _milieu.Children.Add(_titre);
        _milieu.Children.Add(_barre);
        _milieu.Children.Add(_xp);
        _milieu.SizeChanged += (_, _) => Ajuster();
        Grid.SetColumn(_milieu, 1);
        grille.Children.Add(_milieu);
        var po = new StackPanel { Orientation = Orientation.Horizontal, VerticalAlignment = VerticalAlignment.Center, HorizontalAlignment = HorizontalAlignment.Right };
        if (_piece is not null)
        {
            _piece.VerticalAlignment = VerticalAlignment.Center;
            po.Children.Add(_piece);
        }
        _po.VerticalAlignment = VerticalAlignment.Center;
        _po.Margin = new Thickness(6, -2, 0, 0);
        po.Children.Add(_po);
        _energie.Children.Add(new IconePixel("ui-eclair", Jaune) { Pixel = 1, VerticalAlignment = VerticalAlignment.Center });
        _energieTexte.Margin = new Thickness(4, 0, 0, 0);
        _energieTexte.VerticalAlignment = VerticalAlignment.Center;
        _energie.Children.Add(_energieTexte);
        var droite = new StackPanel { VerticalAlignment = VerticalAlignment.Center, Margin = new Thickness(14, 0, 0, 0) };
        droite.Children.Add(po);
        droite.Children.Add(_energie);
        Grid.SetColumn(droite, 2);
        grille.Children.Add(droite);
        _suite.Margin = new Thickness(0, 2, 0, -2);
        _suite.SizeChanged += (_, _) => Ajuster();
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

    // Niveau n, XP totale, solde, titre ; suites : l'annonce de la prochaine rangée, de la forme la plus longue à la
    // plus courte (Bandeau.ProchainesRangees) : le bandeau prend la première qui tient sur sa ligne. Aucune : rien.
    public void Mettre(int niveau, int xp, int po, string titre, params string[] suites)
    {
        // L'info-bulle se remet à jour souvent : rien à refaire si rien n'a changé.
        int? energie = Energie?.Invoke();
        suites = suites.Where(s => s != "").ToArray();
        var cle = $"{niveau}|{xp}|{po}|{titre}|{string.Join("|", suites)}|{energie}";
        if (cle == _cle) return;
        _cle = cle;
        _niveau.Content = Pastille(niveau);
        _titre.Texte = titre;
        int de = Profil.XpPourNiveau(niveau), a = Profil.XpPourNiveau(niveau + 1);
        double x = a > de ? Math.Clamp((xp - de) / (double)(a - de), 0, 1) : 1;
        _barre.Children.Clear();
        // Vingt cases de 6 sur 8, séparées de 2 : tout tombe sur le module.
        const int cases = 20;
        int pleines = (int)Math.Floor(x * cases);
        for (int i = 0; i < cases; i++)
            _barre.Children.Add(new Border
            {
                Width = 6, Height = 8, Margin = new Thickness(0, 0, 2, 0),
                Background = i < pleines ? BleuXp : BleuSombre,
                BorderBrush = i < pleines ? BleuClair : Encre, BorderThickness = new Thickness(0, 2, 0, 0),
            });
        string compte = $"{Math.Max(0, xp - de)} / {a - de} xp", reste = $"encore {Math.Max(0, a - xp)} xp";
        _formesXp = new[] { $"{compte} · {reste} avant le niveau {niveau + 1}", $"{compte} · {reste}", compte };
        _po.Texte = $"{po} po";
        _energieTexte.Texte = energie is { } en ? $"{en}/100" : "";
        _energie.Visibility = energie is null ? Visibility.Collapsed : Visibility.Visible;
        _formesSuite = suites;
        _suite.Visibility = suites.Length == 0 ? Visibility.Collapsed : Visibility.Visible;
        Ajuster();
    }

    // Un texte qui ne tient pas se reformule : chaque ligne prend la forme la plus longue qui tient dans sa largeur.
    private void Ajuster()
    {
        _xp.Texte = StylePixel.Choisir(_milieu.ActualWidth, StylePixel.Corps, false, this, _formesXp);
        if (_formesSuite.Length > 0) _suite.Texte = StylePixel.Choisir(_suite.ActualWidth, StylePixel.Corps, false, this, _formesSuite);
    }

    // « NIV » au-dessus du nombre, sur une pastille cerclée de violet ; le nombre est un logo fin (relief, cerne).
    private static UIElement Pastille(int niveau)
    {
        var pile = new StackPanel { HorizontalAlignment = HorizontalAlignment.Center };
        var niv = StylePixel.Etiquette("niv", Argent);
        niv.HorizontalAlignment = HorizontalAlignment.Center;
        niv.Margin = new Thickness(0, -3, 0, 0);
        pile.Children.Add(niv);
        pile.Children.Add(new LogoPixel(niveau.ToString(), ArgentClair, Encre) { HorizontalAlignment = HorizontalAlignment.Center });
        return new Border
        {
            Background = Nuit2, BorderBrush = Violet, BorderThickness = new Thickness(2), Padding = new Thickness(6, 2, 6, 2), Child = pile,
            MinWidth = 52,
        };
    }

    // « ▲ Prochaine rangée : Dos, Main — niveau 15 (encore 340 xp) » ; pour une entrée de menu.
    public static string ProchaineRangee(int niveau, int xp)
    {
        int p = Boutique.ProchainPalier(niveau);
        if (p == 0) return "Toutes les rangées de la boutique sont ouvertes.";
        return $"▲ Prochaine rangée : {Rayons(p)} — niveau {p} (encore {Math.Max(0, Profil.XpPourNiveau(p) - xp)} xp)";
    }

    private static string Rayons(int palier) => Boutique.ListeRayons(palier);

    // La même annonce pour le bandeau, de la plus longue à la plus courte (Boutique.AnnoncesRangee).
    public static string[] ProchainesRangees(int niveau, int xp) => Boutique.AnnoncesRangee(niveau, xp);
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
