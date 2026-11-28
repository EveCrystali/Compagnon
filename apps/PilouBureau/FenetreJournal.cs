using System.Globalization;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;

namespace PilouBureau;

// Le journal de Pilou (docs/PRESENCE.md) : une page par jour où il s'est passé quelque chose, écrite de son point de vue
// à partir des seuls faits du jour, avec un petit dessin de lui dans l'humeur de la journée. Style de la boutique et
// de l'Aventure (nuit, argent, violet, orange). On feuillette avec ◀ ▶ (ou les flèches du clavier).
internal sealed class FenetreJournal : Window
{
    private readonly FenetrePilou _pilou;
    private readonly TextBlock _date = Texte(13, Bandeau.Violet, true);
    private readonly TextBlock _texte = Texte(15.5, Bandeau.ArgentClair);
    private readonly TextBlock _humeur = Texte(12, Bandeau.Argent);
    private readonly TextBlock _page = Texte(11.5, Bandeau.Argent);
    private readonly TextBlock _complicite = Texte(12, Bandeau.ArgentClair, true);
    private readonly TextBlock _jauge = Texte(12, Bandeau.OrangePo);
    private readonly Border _dessin = new() { Width = 120, Height = 136, Margin = new Thickness(0, 0, 18, 0), VerticalAlignment = VerticalAlignment.Top };
    private readonly Button _avant = Bouton("◀  Plus ancien"), _apres = Bouton("Plus récent  ▶"), _aujourdhui = Bouton("Dernière page");
    private List<Presence.Entree> _entrees = new();
    private int _i;

    private static readonly Brush Fond = Gel("#0f1324"), Feuille = Gel("#1f2540"), Liseré = Gel("#6a5acd");

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

    // Habit rétro de l'Aventure : sans lui, Windows peint le bouton désactivé en gris clair et le texte argent disparaît.
    private static Button Bouton(string texte)
    {
        var b = new Button
        {
            Content = texte, Margin = new Thickness(0, 0, 8, 0), Padding = new Thickness(12, 5, 12, 5), MinWidth = 90,
            Background = Gel("#2a3156"), Foreground = Bandeau.ArgentClair, BorderBrush = Gel("#6a5acd"), BorderThickness = new Thickness(2),
            FontFamily = new FontFamily("Segoe UI"), FontWeight = FontWeights.SemiBold, Cursor = Cursors.Hand,
            HorizontalContentAlignment = HorizontalAlignment.Center,
        };
        if (FenetreAventure.GabaritBouton() is { } g) b.Template = g;
        return b;
    }

    public FenetreJournal(FenetrePilou pilou, string? jour)
    {
        _pilou = pilou;
        Title = "Journal de Pilou";
        Width = 680;
        Height = 470;
        MinWidth = 520;
        MinHeight = 380;
        WindowStartupLocation = WindowStartupLocation.CenterScreen;
        Topmost = true;
        Background = Fond;
        UseLayoutRounding = true;

        var racine = new DockPanel { Margin = new Thickness(18, 12, 18, 14) };
        var tete = new StackPanel { Margin = new Thickness(0, 0, 0, 10) };
        tete.Children.Add(new Pixels(Pixels.Texte("JOURNAL"), new Brush?[] { null, Bandeau.OrangePo }, Bandeau.Violet, 5)
            { HorizontalAlignment = HorizontalAlignment.Center, Margin = new Thickness(0, 4, 0, 4) });
        var sous = Texte(11.5, Bandeau.Argent);
        sous.Text = "Ce que Pilou écrit le soir, chaque jour où il s'est passé quelque chose. Rien de personnel : seulement ce qu'il a vécu.";
        sous.TextAlignment = TextAlignment.Center;
        tete.Children.Add(sous);
        DockPanel.SetDock(tete, Dock.Top);
        racine.Children.Add(tete);

        // Pied : complicité (palier, jours ensemble, jauge de signes) et navigation.
        var pied = new StackPanel { Margin = new Thickness(0, 12, 0, 0) };
        var nav = new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Center };
        nav.Children.Add(_avant);
        nav.Children.Add(_aujourdhui);
        nav.Children.Add(_apres);
        pied.Children.Add(nav);
        _page.HorizontalAlignment = HorizontalAlignment.Center;
        _page.Margin = new Thickness(0, 6, 0, 8);
        pied.Children.Add(_page);
        var lien = new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Center };
        lien.Children.Add(_complicite);
        _jauge.Margin = new Thickness(10, 0, 0, 0);
        lien.Children.Add(_jauge);
        pied.Children.Add(lien);
        DockPanel.SetDock(pied, Dock.Bottom);
        racine.Children.Add(pied);

        // La page : dessin à gauche, date et texte à droite.
        var page = new DockPanel();
        _dessin.Background = Gel("#151a2e");
        _dessin.BorderBrush = Liseré;
        _dessin.BorderThickness = new Thickness(2);
        DockPanel.SetDock(_dessin, Dock.Left);
        page.Children.Add(_dessin);
        var droite = new StackPanel();
        droite.Children.Add(_date);
        _humeur.Margin = new Thickness(0, 2, 0, 10);
        droite.Children.Add(_humeur);
        _texte.LineHeight = 23;
        droite.Children.Add(_texte);
        page.Children.Add(new ScrollViewer { Content = droite, VerticalScrollBarVisibility = ScrollBarVisibility.Auto });
        racine.Children.Add(new Border
        {
            Background = Feuille, BorderBrush = Liseré, BorderThickness = new Thickness(2), Padding = new Thickness(18, 16, 18, 16), Child = page,
        });
        Content = racine;

        _avant.Click += (_, _) => Feuilleter(1);
        _apres.Click += (_, _) => Feuilleter(-1);
        _aujourdhui.Click += (_, _) => Feuilleter(-_i);
        PreviewKeyDown += (_, e) =>
        {
            if (e.Key == Key.Escape) Close();
            else if (e.Key == Key.Left) Feuilleter(1);
            else if (e.Key == Key.Right) Feuilleter(-1);
        };
        Charger();
        Aller(jour);
    }

    private void Charger()
    {
        try
        {
            var e = _pilou.Pres;
            _entrees = e.JournalActif || e.Journal.Count > 0 ? e.Entrees(Presence.Gabarits) : new List<Presence.Entree>();
            var t = e.Totaux();
            int suivant = t.Palier + 1 < Presence.Seuils.Length ? Presence.Seuils[t.Palier + 1] : -1;
            _complicite.Text = $"♥ {Presence.NomPalier(t.Palier)} · {t.Jours} jour{(t.Jours > 1 ? "s" : "")} ensemble";
            _jauge.Text = suivant > 0 ? $"{FenetrePilou.JaugeComplicite(t.Points, Presence.Seuils[t.Palier], suivant)}  vers « {Presence.NomPalier(t.Palier + 1)} »" : "★ le plus haut palier";
        }
        catch (Exception x) when (x is not OutOfMemoryException)
        {
            _entrees = new List<Presence.Entree>();
        }
    }

    internal void Aller(string? jour)
    {
        Charger();
        _i = jour is null ? 0 : Math.Max(0, _entrees.FindIndex(x => x.Jour == jour));
        Montrer();
    }

    private void Feuilleter(int pas)
    {
        _i = Math.Clamp(_i + pas, 0, Math.Max(0, _entrees.Count - 1));
        Montrer();
    }

    private static string Signe(string humeur) => humeur switch
    {
        "fete" => "★ jour de fête", "tendre" => "♥ tout doux", "caresse" => "♥ bien soigné", "joie" => "☀ content",
        "fatigue" => "☾ un peu fatigué", "concentre" => "✎ appliqué", _ => "· tranquille",
    };

    private void Montrer()
    {
        _avant.IsEnabled = _i < _entrees.Count - 1;
        _apres.IsEnabled = _i > 0;
        _aujourdhui.IsEnabled = _i > 0;
        if (_entrees.Count == 0)
        {
            _date.Text = "Pas encore de page";
            _humeur.Text = "";
            _texte.Text = _pilou.Pres.JournalActif
                ? "Pilou n'a encore rien écrit. Ce soir, s'il s'est passé quelque chose, il prendra sa plume."
                : "Le journal est en pause (clic droit sur Pilou → Pilou et moi). Les pages déjà écrites restent ici.";
            _page.Text = "";
            Dessiner("repos");
            return;
        }
        var x = _entrees[_i];
        var d = DateOnly.ParseExact(x.Jour, "yyyy-MM-dd", CultureInfo.InvariantCulture);
        var texteDate = d.ToString("dddd d MMMM yyyy", CultureInfo.GetCultureInfo("fr-FR"));
        _date.Text = char.ToUpperInvariant(texteDate[0]) + texteDate[1..];
        _humeur.Text = Signe(x.Humeur);
        _texte.Text = x.Texte;
        _page.Text = $"page {_entrees.Count - _i} sur {_entrees.Count}";
        Dessiner(x.Humeur);
    }

    private void Dessiner(string humeur)
    {
        try
        {
            var image = Apercu.Image(_pilou.AllurePortrait(humeur, 0), fin: true);
            var vue = Apercu.Vue(image, Finesse.ZoomNet(2));
            vue.HorizontalAlignment = HorizontalAlignment.Center;
            vue.VerticalAlignment = VerticalAlignment.Center;
            _dessin.Child = vue;
        }
        catch (Exception x) when (x is not OutOfMemoryException)
        {
            _dessin.Child = null; // le dessin est un plus
        }
    }
}

// « Comment veux-tu que je t'appelle ? » : un prénom ou un surnom, ou rien. Les deux boutons ont le même poids.
internal sealed class FenetrePrenom : Window
{
    public event Action<string, bool>? Choisi;
    private readonly TextBox _champ;
    private bool _fait;

    public FenetrePrenom(string actuel)
    {
        Title = "Pilou et moi";
        Width = 430;
        SizeToContent = SizeToContent.Height;
        ResizeMode = ResizeMode.NoResize;
        WindowStartupLocation = WindowStartupLocation.CenterScreen;
        Topmost = true;
        Background = new SolidColorBrush(Color.FromRgb(0x0f, 0x13, 0x24));
        var p = new StackPanel { Margin = new Thickness(20, 16, 20, 18) };
        p.Children.Add(new TextBlock
        {
            Text = "Comment veux-tu que je t'appelle ?", Foreground = Bandeau.ArgentClair, FontSize = 16, FontWeight = FontWeights.Bold,
            FontFamily = new FontFamily("Segoe UI"),
        });
        p.Children.Add(new TextBlock
        {
            Text = "Un prénom ou un surnom. Il reste entre tes appareils (dans le groupe chiffré), jamais chez tes amis. "
                   + "Tu peux le changer ou l'effacer quand tu veux (Pilou et moi).",
            Foreground = Bandeau.Argent, FontSize = 12, TextWrapping = TextWrapping.Wrap, Margin = new Thickness(0, 6, 0, 10),
            FontFamily = new FontFamily("Segoe UI"),
        });
        _champ = new TextBox
        {
            Text = actuel, MaxLength = Presence.PrenomMax, FontSize = 15, Padding = new Thickness(6, 4, 6, 4),
            Background = new SolidColorBrush(Color.FromRgb(0x1f, 0x25, 0x40)), Foreground = Bandeau.ArgentClair, BorderBrush = Bandeau.Bord,
            CaretBrush = Bandeau.ArgentClair,
        };
        p.Children.Add(_champ);
        var boutons = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(0, 14, 0, 0) };
        Button B(string t)
        {
            var b = new Button
            {
                Content = t, Padding = new Thickness(14, 6, 14, 6), Margin = new Thickness(0, 0, 10, 0), MinWidth = 150,
                Background = new SolidColorBrush(Color.FromRgb(0x2a, 0x31, 0x56)), Foreground = Bandeau.ArgentClair, BorderBrush = Bandeau.Bord,
                BorderThickness = new Thickness(2), FontWeight = FontWeights.SemiBold, Cursor = Cursors.Hand,
                HorizontalContentAlignment = HorizontalAlignment.Center,
            };
            if (FenetreAventure.GabaritBouton() is { } g) b.Template = g;
            return b;
        }
        var oui = B("C'est ça");
        oui.IsDefault = true;
        var non = B("Je préfère ne pas dire");
        oui.Click += (_, _) => Fin(_champ.Text, false);
        non.Click += (_, _) => Fin("", true);
        boutons.Children.Add(oui);
        boutons.Children.Add(non);
        p.Children.Add(boutons);
        Content = p;
        Loaded += (_, _) =>
        {
            _champ.Focus();
            _champ.SelectAll();
        };
        PreviewKeyDown += (_, e) =>
        {
            if (e.Key == Key.Escape) Fin("", true);
        };
        // Fermer la fenêtre, c'est aussi « je préfère ne pas dire » : on ne redemandera pas.
        Closed += (_, _) =>
        {
            if (!_fait) Choisi?.Invoke("", true);
        };
    }

    private void Fin(string prenom, bool refus)
    {
        if (_fait) return;
        _fait = true;
        Choisi?.Invoke(Presence.NettoyerPrenom(prenom), refus || Presence.NettoyerPrenom(prenom) == "");
        Close();
    }
}
