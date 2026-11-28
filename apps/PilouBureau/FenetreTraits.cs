using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;

namespace PilouBureau;

// « Pilou et moi » (docs/TRAITS.md) : la complicité, les trois traits dominants de Pilou, puis tous ses traits : ceux
// qu'on a découverts avec leur icône et leur nom, les autres en silhouette « ? », sans dire comment ils viennent.
// Aucun chiffre : un trait ne donne rien, il dit seulement qui Pilou est devenu. Habit du Journal (nuit, argent,
// violet, orange) ; un trait dominant porte une étoile et un cadre orange plein, un trait inconnu un cadre pointillé.
internal sealed class FenetreTraits : Window
{
    private readonly FenetrePilou _pilou;
    private readonly TextBlock _complicite = Texte(12.5, Bandeau.ArgentClair, true);
    private readonly TextBlock _jauge = Texte(12.5, Bandeau.OrangePo);
    private readonly StackPanel _dominants = new() { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Center };
    private readonly TextBlock _aucun = Texte(12.5, Bandeau.Argent);
    private readonly WrapPanel _tous = new() { HorizontalAlignment = HorizontalAlignment.Center };
    private readonly TextBlock _compte = Texte(11.5, Bandeau.Argent);

    private static readonly Brush Fond = Gel("#0f1324"), Feuille = Gel("#1f2540"), Case = Gel("#151a2e"), Liseré = Gel("#6a5acd"),
        Eteint = Gel("#3b4654");

    private const int Colonnes = 5;
    private const double LargeurCase = 112;

    private static Brush Gel(string hex)
    {
        var b = new SolidColorBrush((Color)ColorConverter.ConvertFromString(hex));
        b.Freeze();
        return b;
    }

    private static TextBlock Texte(double taille, Brush couleur, bool gras = false) => new()
    {
        FontSize = taille, Foreground = couleur, FontWeight = gras ? FontWeights.Bold : FontWeights.Normal,
        FontFamily = new FontFamily("Segoe UI"), TextWrapping = TextWrapping.Wrap,
    };

    // La police pixel de Pilou (docs/POLICE.md), aux pixels entiers de cette fenêtre-ci.
    private TextePixel Pixel(string texte, Brush couleur, double taille) => new(texte, couleur)
    {
        Taille = taille, PhysiqueParUnite = () => VisualTreeHelper.GetDpi(this).DpiScaleX,
    };

    private FrameworkElement Titre(string texte)
    {
        var t = Pixel(texte, Bandeau.Violet, 2);
        t.HorizontalAlignment = HorizontalAlignment.Center;
        t.Margin = new Thickness(0, 14, 0, 8);
        return t;
    }

    public FenetreTraits(FenetrePilou pilou)
    {
        _pilou = pilou;
        Title = "Pilou et moi";
        Width = 640;
        SizeToContent = SizeToContent.Height;
        ResizeMode = ResizeMode.CanMinimize;
        WindowStartupLocation = WindowStartupLocation.CenterScreen;
        Topmost = true;
        Background = Fond;
        UseLayoutRounding = true;

        var racine = new StackPanel { Margin = new Thickness(18, 12, 18, 16) };
        racine.Children.Add(new Pixels(Pixels.Texte("PILOU ET MOI"), new Brush?[] { null, Bandeau.OrangePo }, Bandeau.Violet, 5)
            { HorizontalAlignment = HorizontalAlignment.Center, Margin = new Thickness(0, 4, 0, 6) });
        var lien = new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Center };
        lien.Children.Add(_complicite);
        _jauge.Margin = new Thickness(10, 0, 0, 0);
        lien.Children.Add(_jauge);
        racine.Children.Add(lien);

        racine.Children.Add(Titre("En ce moment, il est"));
        racine.Children.Add(_dominants);
        _aucun.TextAlignment = TextAlignment.Center;
        _aucun.Text = "Pilou n'a pas encore de trait. Ça vient tout seul, à force de vivre ensemble.";
        racine.Children.Add(_aucun);

        racine.Children.Add(Titre("Tous ses traits"));
        _tous.Width = Colonnes * LargeurCase;
        racine.Children.Add(new Border
        {
            Background = Feuille, BorderBrush = Liseré, BorderThickness = new Thickness(2), Padding = new Thickness(10, 12, 10, 4),
            HorizontalAlignment = HorizontalAlignment.Center, Child = _tous,
        });
        _compte.TextAlignment = TextAlignment.Center;
        _compte.Margin = new Thickness(0, 10, 0, 0);
        racine.Children.Add(_compte);
        var note = Texte(11.5, Bandeau.Argent);
        note.Text = "Pilou attrape ses traits à force de vivre avec toi. On ne les choisit pas, et un trait découvert reste.";
        note.TextAlignment = TextAlignment.Center;
        note.Margin = new Thickness(0, 2, 0, 0);
        racine.Children.Add(note);
        Content = racine;

        PreviewKeyDown += (_, e) =>
        {
            if (e.Key == Key.Escape) Close();
        };
        Charger();
    }

    internal void Charger()
    {
        try
        {
            var e = _pilou.Pres;
            var t = e.Totaux();
            int suivant = t.Palier + 1 < Presence.Seuils.Length ? Presence.Seuils[t.Palier + 1] : -1;
            _complicite.Text = $"♥ {Presence.NomPalier(t.Palier)} · {t.Jours} jour{(t.Jours > 1 ? "s" : "")} ensemble";
            _jauge.Text = suivant > 0
                ? $"{FenetrePilou.JaugeComplicite(t.Points, Presence.Seuils[t.Palier], suivant)}  vers « {Presence.NomPalier(t.Palier + 1)} »"
                : "★ le plus haut palier";
            var dominants = Traits.Dominants(e, Presence.Jour(DateTime.Now));
            _dominants.Children.Clear();
            foreach (var d in dominants) _dominants.Children.Add(Carte(d));
            _dominants.Visibility = dominants.Count > 0 ? Visibility.Visible : Visibility.Collapsed;
            _aucun.Visibility = dominants.Count > 0 ? Visibility.Collapsed : Visibility.Visible;
            _tous.Children.Clear();
            int connus = 0;
            foreach (var x in Traits.Tous)
            {
                bool connu = (t.Traits & x.Bit) != 0;
                if (connu) connus++;
                _tous.Children.Add(Vignette(x, connu, dominants.Contains(x)));
            }
            int reste = Traits.Tous.Count - connus;
            _compte.Text = reste == 0 ? "★ Tous ses traits sont découverts."
                : connus == 0 ? "Aucun trait découvert pour l'instant."
                : $"{connus} trait{(connus > 1 ? "s" : "")} découvert{(connus > 1 ? "s" : "")} · {reste} encore à découvrir";
        }
        catch (Exception x) when (x is not OutOfMemoryException)
        {
            _compte.Text = ""; // la fenêtre reste ouverte, vide plutôt que fausse
        }
    }

    // Un trait dominant : grande icône, étoile, nom en police pixel, cadre orange plein.
    private FrameworkElement Carte(Traits.Trait t)
    {
        var p = new StackPanel { Width = 168 };
        var haut = new Grid { Height = 72 };
        if (Pixels.Sprite(t.Sprite, 4, dansPilou: false) is { } icone)
        {
            icone.HorizontalAlignment = HorizontalAlignment.Center;
            icone.VerticalAlignment = VerticalAlignment.Center;
            haut.Children.Add(icone);
        }
        var etoile = Pixel("★", Bandeau.OrangePo, 2);
        etoile.HorizontalAlignment = HorizontalAlignment.Right;
        etoile.VerticalAlignment = VerticalAlignment.Top;
        haut.Children.Add(etoile);
        p.Children.Add(haut);
        var nom = Pixel(t.Nom, Bandeau.ArgentClair, 2);
        nom.HorizontalAlignment = HorizontalAlignment.Center;
        nom.Margin = new Thickness(0, 6, 0, 0);
        p.Children.Add(nom);
        return new Border
        {
            Background = Feuille, BorderBrush = Bandeau.OrangePo, BorderThickness = new Thickness(2), Padding = new Thickness(8, 8, 8, 10),
            Margin = new Thickness(6, 0, 6, 0), Child = p, ToolTip = t.Nom + " (trait dominant)",
        };
    }

    // Un trait dans la grille : découvert (icône, nom), dominant (étoile en plus), ou inconnu (« ? », cadre pointillé).
    private FrameworkElement Vignette(Traits.Trait t, bool connu, bool dominant)
    {
        var p = new StackPanel { Width = LargeurCase, Margin = new Thickness(0, 0, 0, 10) };
        var dessin = new Grid { Width = 60, Height = 60 };
        dessin.Children.Add(connu
            ? new Border { Background = Case, BorderBrush = dominant ? Bandeau.OrangePo : Liseré, BorderThickness = new Thickness(2) }
            : new System.Windows.Shapes.Rectangle
            {
                Fill = Case, Stroke = Eteint, StrokeThickness = 2, StrokeDashArray = new DoubleCollection { 2, 2 }, SnapsToDevicePixels = true,
            });
        if (Pixels.Sprite(connu ? t.Sprite : "trait-inconnu", 3, dansPilou: false) is { } icone)
        {
            icone.HorizontalAlignment = HorizontalAlignment.Center;
            icone.VerticalAlignment = VerticalAlignment.Center;
            dessin.Children.Add(icone);
        }
        if (dominant)
        {
            var etoile = Pixel("★", Bandeau.OrangePo, 1);
            etoile.HorizontalAlignment = HorizontalAlignment.Right;
            etoile.VerticalAlignment = VerticalAlignment.Top;
            etoile.Margin = new Thickness(0, 4, 5, 0);
            dessin.Children.Add(etoile);
        }
        p.Children.Add(dessin);
        var nom = Texte(11.5, connu ? Bandeau.ArgentClair : Eteint, connu);
        nom.Text = connu ? t.Nom : "? ? ?";
        nom.TextAlignment = TextAlignment.Center;
        nom.Margin = new Thickness(2, 4, 2, 0);
        nom.MinHeight = 32;
        p.Children.Add(nom);
        p.ToolTip = connu ? t.Nom + (dominant ? " (trait dominant)" : "") : "Un trait que Pilou n'a pas encore";
        return p;
    }
}
