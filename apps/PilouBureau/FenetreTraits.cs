using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;

namespace PilouBureau;

// « Pilou et moi » (docs/TRAITS.md) : la complicité, les trois traits dominants de Pilou (à gauche), puis tous ses
// traits (à droite) : ceux qu'on a découverts avec leur icône et leur nom, les autres en silhouette « ? », sans dire
// comment ils viennent. Aucun chiffre : un trait ne donne rien, il dit seulement qui Pilou est devenu.
// Habit du Journal (nuit, argent, violet, orange). Un état ne tient jamais à la seule couleur : un trait dominant
// porte une étoile et un cadre orange plein, un trait inconnu un « ? » et un cadre pointillé.
internal sealed class FenetreTraits : Window
{
    private readonly FenetrePilou _pilou;
    private readonly TextePixel _complicite = Texte(12.5, Bandeau.ArgentClair, true);
    private readonly TextePixel _jauge = Texte(12.5, Bandeau.OrangePo);
    private readonly StackPanel _dominants = new();
    private readonly TextePixel _aucun = Texte(12.5, Bandeau.Argent);
    private readonly WrapPanel _tous = new();
    private readonly TextePixel _compte = Texte(11.5, Bandeau.Argent);

    private static readonly Brush Fond = Gel("#0f1324"), Feuille = Gel("#1f2540"), Case = Gel("#151a2e"), Liseré = Gel("#6a5acd"),
        Eteint = Gel("#566273"), Discret = Gel("#768390");

    private const int Colonnes = 5;
    private const double LargeurCase = 132, LargeurCarte = 260, Boite = 76;

    private static Brush Gel(string hex)
    {
        var b = new SolidColorBrush((Color)ColorConverter.ConvertFromString(hex));
        b.Freeze();
        return b;
    }

    // Police pixel de Pilou (docs/STYLE.md) : les anciennes tailles du système deviennent « petit » (détails) ou
    // « corps » (à partir de 14) ; gras : la police « titre ».
    private static TextePixel Texte(double taille, Brush couleur, bool gras = false) =>
        StylePixel.Texte("", couleur, taille >= 20 ? StylePixel.Grand : StylePixel.Corps, gras);

    // La police pixel de Pilou (docs/POLICE.md), aux pixels entiers de cette fenêtre-ci.
    private TextePixel Pixel(string texte, Brush couleur, double taille) => new(texte, couleur)
    {
        Taille = taille, PhysiqueParUnite = () => VisualTreeHelper.GetDpi(this).DpiScaleX,
    };

    private FrameworkElement Titre(string texte)
    {
        var t = Pixel(texte, Bandeau.Violet, 2);
        t.HorizontalAlignment = HorizontalAlignment.Left;
        t.Margin = new Thickness(0, 0, 0, 10);
        return t;
    }

    public FenetreTraits(FenetrePilou pilou)
    {
        _pilou = pilou;
        Title = "Pilou et moi";
        Width = 1060;
        Height = 860;
        ResizeMode = ResizeMode.NoResize;
        WindowStartupLocation = WindowStartupLocation.CenterScreen;
        Topmost = true;
        Background = Fond;
        UseLayoutRounding = true;

        var racine = new StackPanel { Margin = new Thickness(20, 12, 20, 14) };
        var enseigne = StylePixel.Logo("PILOU ET MOI");
        enseigne.HorizontalAlignment = HorizontalAlignment.Center;
        enseigne.Margin = new Thickness(0, 0, 0, 6);
        racine.Children.Add(enseigne);
        var lien = new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Center };
        lien.Children.Add(_complicite);
        _jauge.Margin = new Thickness(10, 0, 0, 0);
        lien.Children.Add(_jauge);
        racine.Children.Add(lien);

        // Deux colonnes, comme une fiche de personnage : qui il est en ce moment, puis tout ce qu'il peut devenir.
        var fiche = new Grid { Margin = new Thickness(0, 18, 0, 0), HorizontalAlignment = HorizontalAlignment.Center };
        fiche.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(LargeurCarte + 24) });
        fiche.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        var gauche = new StackPanel { Margin = new Thickness(0, 0, 24, 0) };
        gauche.Children.Add(Titre("En ce moment"));
        gauche.Children.Add(_dominants);
        _aucun.Texte = "Pilou n'a pas encore de trait. Ça vient tout seul, à force de vivre ensemble.";
        gauche.Children.Add(_aucun);
        fiche.Children.Add(gauche);
        var droite = new StackPanel();
        droite.Children.Add(Titre("Tous ses traits"));
        _tous.Width = Colonnes * LargeurCase;
        droite.Children.Add(new Border
        {
            Background = Feuille, BorderBrush = Liseré, BorderThickness = new Thickness(2), Padding = new Thickness(8, 12, 8, 2), Child = _tous,
        });
        Grid.SetColumn(droite, 1);
        fiche.Children.Add(droite);
        racine.Children.Add(fiche);

        _compte.Centre = true;
        _compte.Margin = new Thickness(0, 12, 0, 0);
        racine.Children.Add(_compte);
        var note = Texte(11.5, Bandeau.Argent);
        note.Texte = "Pilou attrape ses traits à force de vivre avec toi. On ne les choisit pas, et un trait découvert reste.";
        note.Centre = true;
        note.Margin = new Thickness(0, 2, 0, 0);
        racine.Children.Add(note);
        // Sur un petit écran (ou une grande échelle Windows), la fenêtre rétrécit et le contenu défile.
        Content = new ScrollViewer
        {
            Content = racine, Background = Fond, VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
            HorizontalScrollBarVisibility = ScrollBarVisibility.Auto,
        };
        StylePixel.Defileur(this);
        HabillageFenetre.Poser(this);

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
            _complicite.Texte = $"♥ {Presence.NomPalier(t.Palier)} · {t.Jours} jour{(t.Jours > 1 ? "s" : "")} ensemble";
            _jauge.Texte = suivant > 0
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
            _compte.Texte = reste == 0 ? "★ Tous ses traits sont découverts."
                : connus == 0 ? "Aucun trait découvert pour l'instant."
                : $"{connus} trait{(connus > 1 ? "s" : "")} découvert{(connus > 1 ? "s" : "")} · {reste} encore à découvrir";
        }
        catch (Exception x) when (x is not OutOfMemoryException)
        {
            _compte.Texte = ""; // la fenêtre reste ouverte, vide plutôt que fausse
        }
    }

    private static FrameworkElement? Icone(string sprite, double taille)
    {
        if (Pixels.Sprite(sprite, taille, dansPilou: false) is not { } icone) return null;
        icone.HorizontalAlignment = HorizontalAlignment.Center;
        icone.VerticalAlignment = VerticalAlignment.Center;
        return icone;
    }

    // Un trait dominant : icône, nom en police pixel, étoile dans le coin, cadre orange plein.
    private FrameworkElement Carte(Traits.Trait t)
    {
        var p = new DockPanel { LastChildFill = true };
        if (Icone(t.Sprite, 3) is { } icone)
        {
            DockPanel.SetDock(icone, Dock.Left);
            p.Children.Add(icone);
        }
        var etoile = Pixel("★", Bandeau.OrangePo, 2);
        etoile.VerticalAlignment = VerticalAlignment.Top;
        etoile.Margin = new Thickness(4, 4, 0, 0);
        DockPanel.SetDock(etoile, Dock.Right);
        p.Children.Add(etoile);
        var nom = Pixel(t.Nom, Bandeau.ArgentClair, 2);
        nom.VerticalAlignment = VerticalAlignment.Center;
        nom.HorizontalAlignment = HorizontalAlignment.Left;
        nom.Margin = new Thickness(8, 0, 0, 0);
        p.Children.Add(nom);
        return new Border
        {
            Width = LargeurCarte, MinHeight = Boite + 8, Background = Feuille, BorderBrush = Bandeau.OrangePo, BorderThickness = new Thickness(2),
            Padding = new Thickness(6, 4, 8, 4), Margin = new Thickness(0, 0, 0, 10), Child = p, ToolTip = t.Nom + " (trait dominant)",
        };
    }

    // Un trait dans la grille : découvert (icône, nom), dominant (cadre orange, « ★ » devant le nom), ou inconnu
    // (« ? », cadre pointillé).
    private FrameworkElement Vignette(Traits.Trait t, bool connu, bool dominant)
    {
        var p = new StackPanel { Width = LargeurCase, Margin = new Thickness(0, 0, 0, 8) };
        var dessin = new Grid { Width = Boite, Height = Boite };
        dessin.Children.Add(connu
            ? new Border { Background = Case, BorderBrush = dominant ? Bandeau.OrangePo : Liseré, BorderThickness = new Thickness(2) }
            : new System.Windows.Shapes.Rectangle
            {
                Fill = Case, Stroke = Eteint, StrokeThickness = 2, StrokeDashArray = new DoubleCollection { 2, 2 }, SnapsToDevicePixels = true,
            });
        if (Icone(connu ? t.Sprite : "trait-inconnu", 3) is { } icone) dessin.Children.Add(icone);
        p.Children.Add(dessin);
        var nom = Texte(11.5, dominant ? Bandeau.OrangePo : connu ? Bandeau.ArgentClair : Discret);
        nom.MaxLignes = 2;
        nom.Texte = dominant ? "★ " + t.Nom : connu ? t.Nom : "? ? ?";
        nom.Centre = true;
        nom.Margin = new Thickness(2, 4, 2, 0);
        nom.MinHeight = 48; // deux lignes de « corps »
        p.Children.Add(nom);
        p.ToolTip = connu ? t.Nom + (dominant ? " (trait dominant)" : "") : "Un trait que Pilou n'a pas encore";
        return p;
    }
}
