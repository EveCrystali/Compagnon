using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Input;
using System.Windows.Markup;
using System.Windows.Media;
using System.Windows.Media.Animation;
using System.Windows.Media.Imaging;
using System.Windows.Threading;
using static PilouBureau.Campagnes;

namespace PilouBureau;

// La fenêtre « Aventure » (docs/CAMPAGNES.md, « Sur Windows ») : même habit rétro que la boutique et les expéditions.
//   Bibliothèque : les campagnes (le prologue d'abord), leur ton (signe de forme), accroche, durée, verrou, progression,
//                  fins trouvées ; Commencer, Reprendre, Rejouer.
//   Lecture      : la correspondance. Pilou écrit ses messages un à un (lettre à lettre, un clic accélère), son
//                  portrait fin prend l'humeur du message, la bande de décor montre le lieu ; les options en boutons
//                  (clavier 1 à 4) ; le choix du joueur s'inscrit dans le fil. Attente : Pilou en tenue de voyage, le
//                  compte à rebours, l'heure de retour, « tu peux fermer cette fenêtre ». Épreuves : VueEpreuve.cs.
//   Carnet       : souvenirs, fins (« ? » pour celles qui restent), titres, objets exclusifs.
// La logique vit sans WPF dans Aventure.cs et Epreuves.cs. Une erreur d'affichage ici ne touche jamais Pilou.
internal sealed class FenetreAventure : Window
{
    private enum Vue { Bibliotheque, Lecture, Carnet }

    private readonly FenetrePilou _pilou;
    private readonly Bandeau _bandeau = new(compact: true);
    private readonly Grid _corps = new();
    private readonly StackPanel _onglets = new() { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right, VerticalAlignment = VerticalAlignment.Center };
    private readonly DispatcherTimer _horloge = new() { Interval = TimeSpan.FromSeconds(1) };
    private readonly DispatcherTimer _anim = new(DispatcherPriority.Render) { Interval = TimeSpan.FromMilliseconds(33) };
    private Vue _vue = Vue.Bibliotheque;
    private string _cleVue = "";
    private double _t;
    private int _erreurs;

    // Lecture
    private readonly StackPanel _fil = new() { Margin = new Thickness(18, 14, 18, 18) };
    private readonly ScrollViewer _defile = new() { VerticalScrollBarVisibility = ScrollBarVisibility.Auto, HorizontalScrollBarVisibility = ScrollBarVisibility.Disabled };
    private readonly Border _action = new() { Padding = new Thickness(16, 12, 16, 14), BorderThickness = new Thickness(0, 2, 0, 0) };
    private readonly Grid _scene = new();
    private readonly Image _portrait = new() { Stretch = Stretch.Uniform, Width = 168, Height = 196 };
    private readonly TextBlock _humeur = Texte(11.5, Bandeau.Violet);
    private readonly Pixels _chapitreN = new(Police.Texte(" "), new Brush?[] { null, Bandeau.OrangePo }, Bandeau.Encre, 2);
    private readonly TextBlock _chapitreTitre = Texte(14, Bandeau.ArgentClair, true);
    private readonly StackPanel _progression = new() { Orientation = Orientation.Horizontal, Margin = new Thickness(0, 6, 0, 2) };
    private readonly TextBlock _lieu = Texte(12, Bandeau.BleuClair);
    private readonly WrapPanel _sac = new();
    private readonly Grid _bandeDecor = new() { Height = 118, ClipToBounds = true };
    private readonly Image _decorImage = new() { Stretch = Stretch.UniformToFill };
    private readonly Pixels _decorLieu = new(Police.Texte(" "), new Brush?[] { null, Gel("#fff6e0") }, Gel("#151a2e"), 3);
    private readonly TextBlock _decorChapitre = Texte(11.5, Gel("#fff6e0"));
    private readonly StackPanel _ecrit = new() { Orientation = Orientation.Horizontal, Margin = new Thickness(46, 4, 0, 0), Visibility = Visibility.Collapsed };
    private uint[]? _portraitPrecedent, _voyagePrecedent;
    private Image? _voyage;
    private TextBlock? _compte, _heureRetour;
    private Border? _jaugeAttente;
    private readonly System.Diagnostics.Stopwatch _chrono = System.Diagnostics.Stopwatch.StartNew();
    private Vue? _vueMontree;
    private Campagne? _campagne;
    private Etat? _etat;
    private List<Aventure.Element> _elements = new();
    private int _montres;
    private Aventure.Element? _enCours;
    private TextBlock? _texteEnCours;
    private double _debutEcriture, _pauseJusque, _dernierClic = -1e9;
    private bool _toutDeSuite, _confirmer;
    private string _cleAction = "", _decorMontre = "\u0001", _message = "";
    private string _humeurMontree = "neutre";
    private VueEpreuve? _epreuve;
    // Animations (ScenesAnimees.cs) : décor en boucle et ses transitions, portrait du personnage, fond, vignettes.
    private readonly ScenesAnimees _anims;
    private readonly Image _decorAncien = new() { Stretch = Stretch.UniformToFill, Visibility = Visibility.Collapsed, IsHitTestVisible = false };
    private readonly Image _persoImage = new() { Width = 104, Height = 104, Stretch = Stretch.Uniform, Visibility = Visibility.Collapsed };
    private readonly TextBlock _persoNom = Texte(11, Gel("#fff6e0"));
    private readonly StackPanel _perso = new() { HorizontalAlignment = HorizontalAlignment.Right, VerticalAlignment = VerticalAlignment.Bottom, Margin = new Thickness(0, 0, 16, 4), IsHitTestVisible = false };
    private Aventure.Element? _dernierPilou;
    private string _persoCle = "\u0001";

    private static readonly Brush Fond = Gel("#0f1324"), Case = Gel("#1f2540"), CaseClaire = Gel("#2a3156"), Ferme = Gel("#3b4654"),
        Parchemin = Gel("#efe0c0"), ParcheminBord = Gel("#8a6e4b"), Encre = Gel("#1c2128"), EncrePale = Gel("#5b4a34"), Ombre = Gel("#0a0d1a"),
        Creme = Gel("#fff6e0"), Ardoise = Gel(Aventure.Ardoise);

    internal static Brush Gel(string hex)
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

    private static TextBlock Texte(string texte, double taille, Brush couleur, bool gras = false)
    {
        var t = Texte(taille, couleur, gras);
        t.Text = texte;
        return t;
    }

    // Titre en police pixel (capitales, Police.cs).
    private static Pixels Enseigne(string texte, Brush couleur, double taille = 2, Brush? contour = null) =>
        new(Police.Texte(texte.ToUpperInvariant()), new Brush?[] { null, couleur }, contour ?? Bandeau.Encre, taille)
            { HorizontalAlignment = HorizontalAlignment.Left, SnapsToDevicePixels = true };

    // ---- Habit des boutons et des barres de défilement (rétro : ombre pixel, enfoncé au clic)

    private static ControlTemplate? _gabaritBouton;
    private static Style? _styleBarre;

    private static ControlTemplate? GabaritBouton()
    {
        if (_gabaritBouton is not null) return _gabaritBouton;
        try
        {
            _gabaritBouton = (ControlTemplate)XamlReader.Parse("""
                <ControlTemplate xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
                                 xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" TargetType="Button">
                  <Grid SnapsToDevicePixels="True">
                    <Border x:Name="ombre" Background="#0a0d1a" Margin="3,3,-3,-3"/>
                    <Border x:Name="fond" Background="{TemplateBinding Background}" BorderBrush="{TemplateBinding BorderBrush}"
                            BorderThickness="{TemplateBinding BorderThickness}" Padding="{TemplateBinding Padding}">
                      <Border.RenderTransform><TranslateTransform x:Name="decale"/></Border.RenderTransform>
                      <ContentPresenter HorizontalAlignment="{TemplateBinding HorizontalContentAlignment}" VerticalAlignment="Center"
                                        RecognizesAccessKey="False"/>
                    </Border>
                  </Grid>
                  <ControlTemplate.Triggers>
                    <Trigger Property="IsMouseOver" Value="True">
                      <Setter TargetName="fond" Property="BorderBrush" Value="#f69d50"/>
                      <Setter TargetName="decale" Property="X" Value="-1"/>
                      <Setter TargetName="decale" Property="Y" Value="-1"/>
                    </Trigger>
                    <Trigger Property="IsKeyboardFocused" Value="True">
                      <Setter TargetName="fond" Property="BorderBrush" Value="#b4dbff"/>
                    </Trigger>
                    <Trigger Property="IsPressed" Value="True">
                      <Setter TargetName="decale" Property="X" Value="2"/>
                      <Setter TargetName="decale" Property="Y" Value="2"/>
                      <Setter TargetName="ombre" Property="Visibility" Value="Hidden"/>
                    </Trigger>
                    <Trigger Property="IsEnabled" Value="False">
                      <Setter Property="Opacity" Value="0.45"/>
                    </Trigger>
                  </ControlTemplate.Triggers>
                </ControlTemplate>
                """);
        }
        catch (Exception e) when (e is XamlParseException or InvalidOperationException or InvalidCastException)
        {
            _gabaritBouton = null; // bouton ordinaire
        }
        return _gabaritBouton;
    }

    private static Style? StyleBarre()
    {
        if (_styleBarre is not null) return _styleBarre;
        try
        {
            _styleBarre = (Style)XamlReader.Parse("""
                <Style xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
                       xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" TargetType="ScrollBar">
                  <Setter Property="Width" Value="10"/>
                  <Setter Property="MinWidth" Value="10"/>
                  <Setter Property="Template">
                    <Setter.Value>
                      <ControlTemplate TargetType="ScrollBar">
                        <Border Background="#121729" BorderBrush="#1f2540" BorderThickness="1,0,0,0">
                          <Track x:Name="PART_Track" IsDirectionReversed="True">
                            <Track.Thumb>
                              <Thumb>
                                <Thumb.Template>
                                  <ControlTemplate TargetType="Thumb">
                                    <Border Background="#3b4654" BorderBrush="#6a5acd" BorderThickness="1" Margin="2,2,2,2"/>
                                  </ControlTemplate>
                                </Thumb.Template>
                              </Thumb>
                            </Track.Thumb>
                          </Track>
                        </Border>
                      </ControlTemplate>
                    </Setter.Value>
                  </Setter>
                </Style>
                """);
        }
        catch (Exception e) when (e is XamlParseException or InvalidOperationException or InvalidCastException)
        {
            _styleBarre = null;
        }
        return _styleBarre;
    }

    private Button Bouton(string texte, bool principal, Action action, double taille = 13)
    {
        var b = new Button
        {
            Content = new TextBlock { Text = texte, TextWrapping = TextWrapping.Wrap, FontSize = taille, FontFamily = new FontFamily("Segoe UI"), FontWeight = FontWeights.SemiBold },
            Padding = new Thickness(14, 7, 14, 7), MinWidth = 90, Cursor = Cursors.Hand, Margin = new Thickness(0, 0, 10, 8),
            Background = principal ? Bandeau.OrangePo : CaseClaire, Foreground = principal ? Encre : Bandeau.ArgentClair,
            BorderBrush = principal ? Encre : Bandeau.Bord, BorderThickness = new Thickness(2),
            HorizontalContentAlignment = HorizontalAlignment.Left, FocusVisualStyle = null,
        };
        if (GabaritBouton() is { } g) b.Template = g;
        b.Click += (_, _) => Sur(action);
        return b;
    }

    // ---- Construction

    public FenetreAventure(FenetrePilou pilou)
    {
        _pilou = pilou;
        _anims = new ScenesAnimees(pilou);
        Title = "Aventure de Pilou";
        Width = 1020;
        Height = 720;
        MinWidth = 840;
        MinHeight = 560;
        WindowStartupLocation = WindowStartupLocation.CenterScreen;
        Topmost = true;
        Background = Fond;
        UseLayoutRounding = true;
        SnapsToDevicePixels = true;
        if (StyleBarre() is { } sb) Resources[typeof(ScrollBar)] = sb;
        RenderOptions.SetBitmapScalingMode(_portrait, BitmapScalingMode.NearestNeighbor);
        RenderOptions.SetBitmapScalingMode(_decorImage, BitmapScalingMode.NearestNeighbor);
        RenderOptions.SetBitmapScalingMode(_decorAncien, BitmapScalingMode.NearestNeighbor);
        RenderOptions.SetBitmapScalingMode(_persoImage, BitmapScalingMode.NearestNeighbor);
        _persoNom.HorizontalAlignment = HorizontalAlignment.Center;
        _persoNom.FontStyle = FontStyles.Italic;
        _perso.Children.Add(_persoImage);
        _perso.Children.Add(_persoNom);

        var racine = new Grid { Margin = new Thickness(14, 10, 14, 12) };
        racine.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        racine.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        racine.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });
        racine.Children.Add(_bandeau);
        var tete = new Grid { Margin = new Thickness(0, 10, 0, 10) };
        var titre = new StackPanel { Orientation = Orientation.Horizontal, VerticalAlignment = VerticalAlignment.Center };
        titre.Children.Add(new Pixels(Police.Texte("AVENTURE"), new Brush?[] { null, Bandeau.OrangePo }, Gel("#6a5acd"), 5) { VerticalAlignment = VerticalAlignment.Center });
        titre.Children.Add(new TextBlock
        {
            Text = "Pilou t'écrit, tu choisis, il part pour de vrai.", Foreground = Bandeau.Argent, FontSize = 12, FontFamily = new FontFamily("Segoe UI"),
            FontStyle = FontStyles.Italic, VerticalAlignment = VerticalAlignment.Bottom, Margin = new Thickness(14, 0, 0, 2),
        });
        tete.Children.Add(titre);
        tete.Children.Add(_onglets);
        Grid.SetRow(tete, 1);
        racine.Children.Add(tete);
        Grid.SetRow(_corps, 2);
        racine.Children.Add(_corps);
        // Le fond respire très doucement selon le ton de la campagne et l'heure (ScenesAnimees.Fond).
        var cadreFond = new Grid();
        cadreFond.Children.Add(_anims.Fond());
        cadreFond.Children.Add(racine);
        Content = cadreFond;

        _defile.Content = _fil;
        _defile.PreviewMouseLeftButtonDown += (_, _) => Sur(Accelerer);
        _ecrit.Children.Add(Texte("Pilou écrit", 11.5, Bandeau.Argent));
        for (int i = 0; i < 3; i++)
            _ecrit.Children.Add(new Border { Width = 4, Height = 4, Background = Bandeau.Argent, Margin = new Thickness(i == 0 ? 6 : 3, 8, 0, 0) });

        _horloge.Tick += (_, _) => Sur(Rafraichir);
        _anim.Tick += (_, _) => Sur(Animer);
        Loaded += (_, _) => Sur(() =>
        {
            var e = _pilou.EtatCampagne;
            _vue = e is { Phase: not Phase.Aucune } && _pilou.CarnetCampagnes.Courante is not null && e.Phase != Phase.Abandon ? Vue.Lecture : Vue.Bibliotheque;
            Rafraichir();
            _horloge.Start();
            _anim.Start();
        });
        Closed += (_, _) =>
        {
            _horloge.Stop();
            _anim.Stop();
        };
        // Fenêtre réduite ou cachée : plus aucune minuterie d'animation.
        void Veille()
        {
            bool visible = IsVisible && WindowState != WindowState.Minimized && IsLoaded;
            if (visible && !_anim.IsEnabled) _anim.Start();
            else if (!visible && _anim.IsEnabled) _anim.Stop();
        }
        StateChanged += (_, _) => Sur(Veille);
        IsVisibleChanged += (_, _) => Sur(Veille);
        PreviewKeyDown += (_, e) => Sur(() => Touche(e));
    }

    // Une erreur dans la fenêtre : notée, la fenêtre se referme après trois (Pilou n'est jamais touché).
    private void Sur(Action a)
    {
        try
        {
            a();
        }
        catch (Exception e) when (e is not OutOfMemoryException)
        {
            System.Diagnostics.Debug.WriteLine($"FenetreAventure : {e}");
            if (++_erreurs >= 3)
            {
                _horloge.Stop();
                _anim.Stop();
                try
                {
                    Close();
                }
                catch (InvalidOperationException)
                {
                }
            }
        }
    }

    // ---- Rafraîchissement (chaque seconde, et après chaque décision)

    public void Rafraichir()
    {
        int niveau = _pilou.NiveauAventure;
        _bandeau.Mettre(niveau, _pilou.XpTotal, _pilou.EtatBourse().Solde, _pilou.TitreAffiche(niveau));
        var k = _pilou.CarnetCampagnes;
        _etat = _pilou.EtatCampagne;
        _campagne = _pilou.CampagneOuverte;
        bool lecture = _campagne is not null && _etat is not null && k.Courante is not null;
        if (_vue == Vue.Lecture && !lecture) _vue = Vue.Bibliotheque;
        Onglets(lecture);
        var cle = _vue + "|" + (_vue == Vue.Lecture ? $"{k.Courante?.Campagne}.{k.Courante?.P}" : $"{(long)(_pilou.EpoqueAventure / 60_000)}|{_etat?.Phase}|{k.Historique.Count}|{k.Courante?.P}");
        if (cle != _cleVue)
        {
            _cleVue = cle;
            _corps.Children.Clear();
            _epreuve = null;
            _anims.ViderVignettes();
            switch (_vue)
            {
                case Vue.Lecture:
                    ConstruireLecture();
                    break;
                case Vue.Carnet:
                    _corps.Children.Add(ConstruireCarnet());
                    break;
                default:
                    _corps.Children.Add(ConstruireBibliotheque());
                    break;
            }
            if (_vueMontree != _vue) Apparaitre(_corps);
            _vueMontree = _vue;
        }
        if (_vue == Vue.Lecture) MettreAJourLecture();
        _anims.Ton(_campagne?.Ton ?? "");
    }

    private void Montrer(Vue v)
    {
        _vue = v;
        _cleVue = "";
        Rafraichir();
    }

    private void Onglets(bool lecture)
    {
        var voulu = $"{lecture}|{_vue}";
        if (_onglets.Tag as string == voulu) return;
        _onglets.Tag = voulu;
        _onglets.Children.Clear();
        void Onglet(string texte, Vue v, bool permis)
        {
            if (!permis) return;
            bool actif = _vue == v;
            var b = Bouton(texte, false, () => Montrer(v), 12);
            b.Margin = new Thickness(8, 0, 0, 0);
            b.Padding = new Thickness(12, 5, 12, 5);
            b.MinWidth = 0;
            b.Background = actif ? Bandeau.Bord : Case;
            b.BorderBrush = actif ? Bandeau.Violet : Bandeau.Bord;
            _onglets.Children.Add(b);
        }
        Onglet("✉ En cours", Vue.Lecture, lecture);
        Onglet("☰ Bibliothèque", Vue.Bibliotheque, true);
        Onglet("❖ Carnet", Vue.Carnet, true);
        var reglage = Bouton("✧", false, MenuAnimations, 12);
        reglage.Margin = new Thickness(8, 0, 0, 0);
        reglage.Padding = new Thickness(10, 5, 10, 5);
        reglage.MinWidth = 0;
        reglage.Background = Case;
        reglage.ToolTip = "Animations des aventures";
        _onglets.Children.Add(reglage);
    }

    private static void Apparaitre(UIElement e, double ms = 260, double dy = 8)
    {
        if (!Bandeau.Anime) return;
        e.Opacity = 0;
        e.BeginAnimation(OpacityProperty, new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(ms)));
        var tr = new TranslateTransform(0, dy);
        e.RenderTransform = tr;
        tr.BeginAnimation(TranslateTransform.YProperty, new DoubleAnimation(dy, 0, TimeSpan.FromMilliseconds(ms)) { EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut } });
    }

    // ---- Bibliothèque

    private UIElement ConstruireBibliotheque()
    {
        var k = _pilou.CarnetCampagnes;
        var toutes = Disponibles().Select(Charger).OfType<Campagne>().ToList();
        var pile = new StackPanel { Margin = new Thickness(0, 0, 8, 8) };
        if (toutes.Count == 0)
        {
            pile.Children.Add(Vide("Aucune aventure dans cet exe.", "Les campagnes vivent dans assets/campagnes : elles arrivent avec la prochaine mise à jour."));
            return pile;
        }
        var fiches = Aventure.Bibliotheque(k, toutes, _pilou.NiveauAventure, _etat, (long)_pilou.EpoqueAventure);
        int i = 0;
        foreach (var f in fiches)
        {
            var carte = Fiche(f, toutes.First(c => c.Id == f.Id), k);
            pile.Children.Add(carte);
            if (Bandeau.Anime && _vueMontree != Vue.Bibliotheque)
            {
                carte.Opacity = 0;
                var delai = TimeSpan.FromMilliseconds(60 * i++);
                carte.BeginAnimation(OpacityProperty, new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(240)) { BeginTime = delai });
            }
        }
        pile.Children.Add(Texte("Une seule aventure à la fois. Pilou part pour de vrai : quelques minutes, parfois une heure ou deux. "
                                + "Tu peux fermer cette fenêtre, il te prévient à son retour (une fois, sans insister).", 11.5, Bandeau.Argent));
        return new ScrollViewer { Content = pile, VerticalScrollBarVisibility = ScrollBarVisibility.Auto };
    }

    private Border Fiche(Aventure.Fiche f, Campagne c, Carnet k)
    {
        bool ferme = f.Statut == Aventure.Statut.Verrouillee;
        var teinte = Gel(Aventure.TeinteTon(f.Ton));
        var carte = new Border
        {
            Background = f.Statut == Aventure.Statut.EnCours ? CaseClaire : Case, BorderBrush = ferme ? Ferme : teinte,
            BorderThickness = new Thickness(f.Statut == Aventure.Statut.EnCours ? 3 : 2), Padding = new Thickness(12, 10, 12, 10), Margin = new Thickness(0, 0, 0, 10),
            Opacity = ferme ? 0.6 : 1,
        };
        var g = new Grid();
        g.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(150) });
        g.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        g.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        g.Children.Add(Vignette(c, f, 150, 96));

        var pile = new StackPanel { Margin = new Thickness(14, 0, 10, 0) };
        var ligneTitre = new StackPanel { Orientation = Orientation.Horizontal };
        ligneTitre.Children.Add(Texte($"{(ferme ? "▣ " : "")}{f.Titre}", 17, Bandeau.ArgentClair, true));
        if (f.Id == "prologue" && f.Statut == Aventure.Statut.Nouvelle)
            ligneTitre.Children.Add(new Border
            {
                Background = Bandeau.OrangePo, Margin = new Thickness(10, 3, 0, 0), Padding = new Thickness(4, 3, 4, 2), VerticalAlignment = VerticalAlignment.Center,
                Child = new Pixels(Police.Texte("COMMENCE ICI"), new Brush?[] { null, Encre }, null, 1.5),
            });
        pile.Children.Add(ligneTitre);
        pile.Children.Add(Texte($"{Aventure.SigneTon(f.Ton)} {Aventure.NomTon(f.Ton)}  ·  ⌛ {f.Duree}  ·  niveau {f.Niveau}", 12, ferme ? Bandeau.Argent : teinte, true));
        var accroche = Texte(f.Accroche, 12.5, Bandeau.Argent);
        accroche.Margin = new Thickness(0, 4, 0, 6);
        accroche.MaxHeight = 52;
        accroche.TextTrimming = TextTrimming.WordEllipsis;
        pile.Children.Add(accroche);
        var bas = new StackPanel { Orientation = Orientation.Horizontal };
        bas.Children.Add(Cases(f.Progression, 16, teinte));
        bas.Children.Add(Texte($"   fins : {Aventure.Fins6(k, c)}", 12, Bandeau.ArgentClair));
        pile.Children.Add(bas);
        pile.Children.Add(Texte($"{Aventure.SigneStatut(f.Statut)} {f.Detail}", 11.5, f.Statut == Aventure.Statut.EnCours ? Bandeau.OrangePo : Bandeau.Violet));
        Grid.SetColumn(pile, 1);
        g.Children.Add(pile);

        var boutons = new StackPanel { VerticalAlignment = VerticalAlignment.Center };
        if (ferme)
            boutons.Children.Add(Texte($"▣ niveau {f.Niveau}", 12.5, Bandeau.Argent, true));
        else
        {
            string signe = f.Statut switch { Aventure.Statut.EnCours => "◉", Aventure.Statut.Suspendue => "◌", Aventure.Statut.Finie => "↻", _ => "▶" };
            var b = Bouton($"{signe} {f.Action}", f.Statut is Aventure.Statut.Nouvelle or Aventure.Statut.EnCours or Aventure.Statut.Suspendue,
                () => Lancer(f), 13.5);
            b.IsEnabled = !f.Bloquee;
            if (f.Bloquee) b.ToolTip = "Une seule aventure à la fois : finis ou mets de côté celle en cours";
            b.MinWidth = 140;
            boutons.Children.Add(b);
            if (f.Statut == Aventure.Statut.Suspendue && !f.Bloquee)
            {
                var neuf = Bouton("Repartir du début", false, () => Demarrer(f.Id, true), 11.5);
                neuf.MinWidth = 140;
                boutons.Children.Add(neuf);
            }
        }
        Grid.SetColumn(boutons, 2);
        g.Children.Add(boutons);
        carte.Child = g;
        return carte;
    }

    private void Lancer(Aventure.Fiche f)
    {
        switch (f.Statut)
        {
            case Aventure.Statut.EnCours:
                Montrer(Vue.Lecture);
                break;
            case Aventure.Statut.Finie:
                Demarrer(f.Id, true);
                break;
            default:
                Demarrer(f.Id, false);
                break;
        }
    }

    private void Demarrer(string id, bool neuf)
    {
        var r = _pilou.CampagneDemarrer(id, neuf);
        if (r is not null)
        {
            _message = r;
            _cleVue = "";
            Rafraichir();
            return;
        }
        _message = "";
        RemettreLecture();
        Montrer(Vue.Lecture);
    }

    // La vignette d'une campagne : son premier décor dessiné s'il existe, sinon un ciel à la teinte du ton et son signe.
    private UIElement Vignette(Campagne c, Aventure.Fiche f, double w, double h)
    {
        var cadre = new Grid { Width = w, Height = h, ClipToBounds = true, VerticalAlignment = VerticalAlignment.Top };
        bool ferme = f.Statut == Aventure.Statut.Verrouillee;
        var sprite = c.Decors.Select(d => Apercu.Sprite(Aventure.SpriteDecor(c.Id, d.Id), 0, ferme)).FirstOrDefault(s => s is not null);
        if (sprite is not null)
        {
            var im = new Image { Source = sprite, Stretch = Stretch.UniformToFill };
            RenderOptions.SetBitmapScalingMode(im, BitmapScalingMode.NearestNeighbor);
            cadre.Children.Add(im);
            // Ouverte : le décor vit un peu (quelques images, au ralenti).
            if (!ferme && c.Decors.Select(d => Illustrations.Decor(Banque.Commune, c.Id, d.Id, ScenesAnimees.Echelle)).FirstOrDefault(s => s is not null) is { } vivant)
                _anims.Vignette(im, vivant);
        }
        else
        {
            cadre.Children.Add(new Border { Background = Ciel(c.Ton) });
            cadre.Children.Add(Etoiles(w, h, Hasard.Graine(c.Id)));
            cadre.Children.Add(Collines(w, h, c.Ton, Hasard.Graine(c.Id + "/c")));
            cadre.Children.Add(new TextBlock
            {
                Text = Aventure.SigneTon(c.Ton), FontSize = 34, Foreground = Gel(Aventure.TeinteTon(c.Ton)), FontFamily = new FontFamily("Segoe UI Symbol"),
                HorizontalAlignment = HorizontalAlignment.Center, VerticalAlignment = VerticalAlignment.Center, Margin = new Thickness(0, 0, 0, 14),
            });
        }
        cadre.Children.Add(new Border { BorderBrush = Ombre, BorderThickness = new Thickness(2) });
        return cadre;
    }

    // Ciel en dégradé, par ton (jamais rouge / vert).
    internal static Brush Ciel(string ton)
    {
        var (haut, bas) = ton switch
        {
            "humour" => ("#1c2a55", "#c9774a"),
            "mystere" => ("#0d1022", "#3a2f6b"),
            "emotion" => ("#1d2440", "#8d7a96"),
            "epique" => ("#071a33", "#2f6fb0"),
            _ => ("#151a2e", "#3b4654"),
        };
        var g = new LinearGradientBrush((Color)ColorConverter.ConvertFromString(haut), (Color)ColorConverter.ConvertFromString(bas), 90);
        g.Freeze();
        return g;
    }

    // Quelques étoiles carrées, toujours les mêmes pour une graine.
    private static UIElement Etoiles(double w, double h, ulong graine)
    {
        var c = new Canvas { IsHitTestVisible = false };
        var r = new Hasard(graine);
        for (int i = 0; i < (int)(w * h / 900); i++)
        {
            double x = r.Suivant((int)w), y = r.Suivant((int)(h * 0.6));
            int s = r.Suivant(5) == 0 ? 3 : 2;
            var e = new Border { Width = s, Height = s, Background = r.Suivant(4) == 0 ? Gel("#ffd8b0") : Gel("#e6ecf2"), Opacity = 0.35 + r.Suivant(60) / 100.0 };
            Canvas.SetLeft(e, Math.Round(x));
            Canvas.SetTop(e, Math.Round(y));
            c.Children.Add(e);
        }
        return c;
    }

    // Deux rangées de collines en escalier (pixels de 4), devant le ciel.
    private static UIElement Collines(double w, double h, string ton, ulong graine)
    {
        var c = new Canvas { IsHitTestVisible = false };
        var r = new Hasard(graine);
        var (loin, pres) = ton switch
        {
            "humour" => ("#3a3f6e", "#252a4d"),
            "mystere" => ("#221f44", "#14142b"),
            "emotion" => ("#4a4466", "#2d2a45"),
            "epique" => ("#173d66", "#0f2645"),
            _ => ("#2d333b", "#1f2540"),
        };
        foreach (var (teinte, base_, ampleur) in new[] { (loin, 0.62, 0.16), (pres, 0.78, 0.12) })
        {
            double phase = r.Suivant(628) / 100.0, f = 1.5 + r.Suivant(150) / 100.0;
            for (int x = 0; x < w; x += 4)
            {
                double y = h * (base_ - ampleur * Math.Sin(x / w * Math.PI * f + phase) * Math.Sin(x / w * 2.3 + phase / 2));
                y = Math.Round(y / 4) * 4;
                var b = new Border { Width = 4, Height = Math.Max(0, h - y), Background = Gel(teinte) };
                Canvas.SetLeft(b, x);
                Canvas.SetTop(b, y);
                c.Children.Add(b);
            }
        }
        return c;
    }

    // Barre de progression en cases (comme le bandeau d'XP).
    private static StackPanel Cases(double x, int n, Brush plein)
    {
        var p = new StackPanel { Orientation = Orientation.Horizontal, VerticalAlignment = VerticalAlignment.Center };
        int pleines = (int)Math.Round(Math.Clamp(x, 0, 1) * n);
        for (int i = 0; i < n; i++)
            p.Children.Add(new Border
            {
                Width = 9, Height = 8, Margin = new Thickness(0, 0, 2, 0), Background = i < pleines ? plein : Bandeau.Nuit,
                BorderBrush = Bandeau.Bord, BorderThickness = new Thickness(i < pleines ? 0 : 1),
            });
        return p;
    }

    // Un état vide soigné : un petit Pilou, une phrase, une piste.
    private UIElement Vide(string titre, string sous)
    {
        var p = new StackPanel { HorizontalAlignment = HorizontalAlignment.Center, Margin = new Thickness(0, 40, 0, 20) };
        var im = new Image { Source = Apercu.Image(_pilou.AllurePortrait("tendre", 0), fin: true), Width = 96, Height = 112 };
        RenderOptions.SetBitmapScalingMode(im, BitmapScalingMode.NearestNeighbor);
        p.Children.Add(im);
        var t = Texte(titre, 15, Bandeau.ArgentClair, true);
        t.TextAlignment = TextAlignment.Center;
        t.Margin = new Thickness(0, 10, 0, 4);
        p.Children.Add(t);
        var s = Texte(sous, 12, Bandeau.Argent);
        s.TextAlignment = TextAlignment.Center;
        s.MaxWidth = 460;
        p.Children.Add(s);
        return p;
    }

    // ---- Carnet

    private UIElement ConstruireCarnet()
    {
        var k = _pilou.CarnetCampagnes;
        var pages = Aventure.Carnet(k, Disponibles().Select(Charger).OfType<Campagne>());
        var pile = new StackPanel { Margin = new Thickness(0, 0, 8, 8) };
        if (pages.All(p => p.Fins.Count == 0))
        {
            pile.Children.Add(Vide("Le carnet est encore vierge.", "Chaque fin d'aventure y laisse un souvenir, parfois un titre ou un objet à porter. "
                                                                    + "Commence par le prologue : la colline d'en face."));
        }
        foreach (var page in pages)
        {
            var c = page.Campagne;
            var tete = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(0, 12, 0, 6) };
            tete.Children.Add(Texte($"{Aventure.SigneTon(c.Ton)}  ", 15, Gel(Aventure.TeinteTon(c.Ton)), true));
            tete.Children.Add(Enseigne(c.Titre, Bandeau.ArgentClair, 2));
            tete.Children.Add(Texte($"   {page.Fins.Count}/{page.FinsTotal} fins", 12, Bandeau.Argent));
            pile.Children.Add(tete);
            var fins = new WrapPanel();
            var trouvees = page.Fins.ToDictionary(f => f.Noeud);
            foreach (var n in c.Noeuds.Values.Where(n => n.Type == "fin").OrderBy(n => trouvees.TryGetValue(n.Id, out var f) ? f.T : long.MaxValue).ThenBy(n => n.Id, StringComparer.Ordinal))
                fins.Children.Add(CarteFin(c, n, trouvees.GetValueOrDefault(n.Id)));
            pile.Children.Add(fins);
            if (page.Titres.Count > 0 || page.Objets.Count > 0)
            {
                var gains = new WrapPanel { Margin = new Thickness(0, 4, 0, 0) };
                foreach (var t in page.Titres) gains.Children.Add(Pastille($"✧ {t}", Bandeau.Violet));
                foreach (var o in page.Objets) gains.Children.Add(Pastille($"✦ {Aventure.NomObjet(c, o)} · exclusif", Bandeau.OrangePo, o));
                pile.Children.Add(gains);
            }
        }
        return new ScrollViewer { Content = pile, VerticalScrollBarVisibility = ScrollBarVisibility.Auto };
    }

    private static Border CarteFin(Campagne c, Noeud n, FinObtenue? f)
    {
        var teinte = Gel(Aventure.TeinteIssue(n.Issue));
        var p = new StackPanel();
        if (f is null)
        {
            p.Children.Add(Texte("? ? ?", 18, Ardoise, true));
            p.Children.Add(Texte("une fin à découvrir", 11.5, Bandeau.Argent));
        }
        else
        {
            p.Children.Add(Texte($"{Aventure.SigneIssue(n.Issue)}  {n.Titre}", 13.5, Encre, true));
            p.Children.Add(Texte($"{Aventure.NomIssue(n.Issue)} · {DateTimeOffset.FromUnixTimeMilliseconds(f.T).LocalDateTime:d MMM yyyy}", 11, EncrePale));
            if (f.Souvenir is { } s)
            {
                var t = Texte($"❖ {s.Nom}", 12, Encre, true);
                t.Margin = new Thickness(0, 6, 0, 0);
                p.Children.Add(t);
                if (s.Texte != "") p.Children.Add(Texte(s.Texte, 11.5, EncrePale));
            }
        }
        return new Border
        {
            Width = 230, MinHeight = 92, Margin = new Thickness(0, 0, 10, 10), Padding = new Thickness(10, 8, 10, 8),
            Background = f is null ? Case : Parchemin, BorderBrush = f is null ? Ferme : teinte, BorderThickness = new Thickness(f is null ? 2 : 3),
            Child = p,
        };
    }

    private static Border Pastille(string texte, Brush teinte, string? sprite = null)
    {
        var p = new StackPanel { Orientation = Orientation.Horizontal };
        if (sprite is not null && Apercu.Sprite(sprite) is { } im)
        {
            var v = Apercu.Vue(im, Math.Min(2, 22.0 / Math.Max(im.PixelWidth, im.PixelHeight)));
            v.Margin = new Thickness(0, 0, 6, 0);
            p.Children.Add(v);
        }
        p.Children.Add(Texte(texte, 12, teinte, true));
        return new Border { Background = Bandeau.Nuit, BorderBrush = teinte, BorderThickness = new Thickness(1), Padding = new Thickness(8, 3, 8, 3), Margin = new Thickness(0, 0, 8, 6), Child = p };
    }

    // ---- Lecture

    private void RemettreLecture()
    {
        _elements = new();
        _montres = 0;
        _enCours = null;
        _texteEnCours = null;
        _cleAction = "";
        _decorMontre = "\u0001";
        _confirmer = false;
        _toutDeSuite = false;
        _fil.Children.Clear();
    }

    private void ConstruireLecture()
    {
        RemettreLecture();
        var g = new Grid();
        g.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(232) });
        g.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });

        // À gauche : le portrait, le chapitre, le lieu, le sac.
        var gauche = new Border { Background = Bandeau.Nuit, BorderBrush = Bandeau.Bord, BorderThickness = new Thickness(2), Padding = new Thickness(12), Margin = new Thickness(0, 0, 12, 0) };
        var pg = new StackPanel();
        foreach (var x in new FrameworkElement[] { _portrait, _humeur, _chapitreN, _chapitreTitre, _progression, _lieu, _sac, _bandeDecor, _decorImage,
                     _decorLieu, _decorChapitre, _defile, _action, _scene, _ecrit })
            Lib(x);
        var cadre = new Grid { Height = 206, ClipToBounds = true };
        cadre.Children.Add(new Border { Background = Ciel(_campagne?.Ton ?? "") });
        cadre.Children.Add(Etoiles(204, 206, 7));
        cadre.Children.Add(new Border { Height = 26, VerticalAlignment = VerticalAlignment.Bottom, Background = Gel("#16365e") });
        _portrait.VerticalAlignment = VerticalAlignment.Bottom;
        _portrait.Margin = new Thickness(0, 0, 0, 6);
        cadre.Children.Add(_portrait);
        cadre.Children.Add(new Border { BorderBrush = Ombre, BorderThickness = new Thickness(2) });
        pg.Children.Add(cadre);
        _humeur.HorizontalAlignment = HorizontalAlignment.Center;
        _humeur.Margin = new Thickness(0, 6, 0, 10);
        _humeur.FontStyle = FontStyles.Italic;
        pg.Children.Add(_humeur);
        pg.Children.Add(_chapitreN);
        _chapitreTitre.Margin = new Thickness(0, 6, 0, 0);
        pg.Children.Add(_chapitreTitre);
        pg.Children.Add(_progression);
        _lieu.Margin = new Thickness(0, 6, 0, 12);
        pg.Children.Add(_lieu);
        pg.Children.Add(Enseigne("SAC", Bandeau.Violet, 2));
        _sac.Margin = new Thickness(0, 6, 0, 0);
        pg.Children.Add(_sac);
        var bas = new StackPanel { VerticalAlignment = VerticalAlignment.Bottom };
        var biblio = Bouton("☰ Bibliothèque", false, () => Montrer(Vue.Bibliotheque), 12);
        biblio.HorizontalAlignment = HorizontalAlignment.Stretch;
        bas.Children.Add(biblio);
        var cote = Bouton("◌ Mettre de côté…", false, () =>
        {
            _confirmer = true;
            _cleAction = "";
            MettreAJourLecture();
        }, 12);
        cote.HorizontalAlignment = HorizontalAlignment.Stretch;
        cote.ToolTip = "Pilou rentre ; l'aventure reprendra plus tard au dernier check-point (ce qui est acquis reste acquis)";
        bas.Children.Add(cote);
        var dock = new DockPanel();
        DockPanel.SetDock(bas, Dock.Bottom);
        dock.Children.Add(bas);
        dock.Children.Add(pg);
        gauche.Child = dock;
        g.Children.Add(gauche);

        // À droite : la bande de décor, le fil, la zone d'action.
        var droite = new Border { Background = Gel("#121729"), BorderBrush = Bandeau.Bord, BorderThickness = new Thickness(2) };
        var dg = new Grid();
        dg.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        dg.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });
        dg.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        _bandeDecor.Children.Clear();
        _bandeDecor.Children.Add(new Border { Background = Ciel(_campagne?.Ton ?? "") });
        _bandeDecor.Children.Add(_decorImage);
        _bandeDecor.Children.Add(Lib(_decorAncien));
        var legende = new StackPanel { VerticalAlignment = VerticalAlignment.Bottom, Margin = new Thickness(14, 0, 14, 10) };
        legende.Children.Add(_decorChapitre);
        legende.Children.Add(_decorLieu);
        _bandeDecor.Children.Add(new Border
        {
            VerticalAlignment = VerticalAlignment.Bottom, Height = 56, IsHitTestVisible = false,
            Background = new LinearGradientBrush(Color.FromArgb(0, 15, 19, 36), Color.FromArgb(200, 15, 19, 36), 90),
        });
        _bandeDecor.Children.Add(legende);
        _bandeDecor.Children.Add(Lib(_perso));
        _persoCle = "\u0001";
        _dernierPilou = null;
        _bandeDecor.Children.Add(new Border { BorderBrush = Bandeau.Bord, BorderThickness = new Thickness(0, 0, 0, 2), IsHitTestVisible = false });
        dg.Children.Add(_bandeDecor);
        _scene.Children.Clear();
        _scene.Children.Add(_defile);
        // Le haut du fil s'efface en douceur sous la bande de décor (au lieu d'une coupe nette).
        _scene.Children.Add(new Border
        {
            Height = 22, VerticalAlignment = VerticalAlignment.Top, IsHitTestVisible = false, Margin = new Thickness(0, 0, 10, 0),
            Background = new LinearGradientBrush(Color.FromArgb(255, 18, 23, 41), Color.FromArgb(0, 18, 23, 41), 90),
        });
        Grid.SetRow(_scene, 1);
        dg.Children.Add(_scene);
        _action.Background = Bandeau.Nuit2;
        _action.BorderBrush = Bandeau.Bord;
        Grid.SetRow(_action, 2);
        dg.Children.Add(_action);
        droite.Child = dg;
        Grid.SetColumn(droite, 1);
        g.Children.Add(droite);
        _corps.Children.Add(g);
    }

    // Chaque seconde : le fil (nouveaux messages), l'en-tête, la zone d'action, le compte à rebours.
    private void MettreAJourLecture()
    {
        var k = _pilou.CarnetCampagnes;
        if (_campagne is not { } c || _etat is not { } e) return;
        var elements = Aventure.Fil(k, c);
        // Le fil a changé en amont (une décision d'un autre appareil est passée avant) : on le refait.
        bool memeDebut = elements.Count >= _montres && Enumerable.Range(0, _montres).All(i => elements[i].Cle == _elements[i].Cle && elements[i].Sorte == _elements[i].Sorte);
        if (!memeDebut)
        {
            _fil.Children.Clear();
            _montres = 0;
            _enCours = null;
            _texteEnCours = null;
            _cleAction = "";
        }
        _elements = elements;
        if (_elements.Count == 0 && _fil.Children.Count == 0)
            _fil.Children.Add(Texte("Le fil commence ici : Pilou va t'écrire.", 12, Bandeau.Argent));

        Reecrire(_chapitreN, $"CHAPITRE {e.ChapitreNumero}/{Math.Max(e.ChapitreNumero, e.ChapitreTotal)}", 2);
        _chapitreTitre.Text = e.ChapitreTitre;
        _progression.Children.Clear();
        _progression.Children.Add(Cases(e.Progression, 14, Bandeau.OrangePo));
        _progression.Children.Add(Texte($"  {Math.Round(e.Progression * 100)} %", 11, Bandeau.Argent));
        _sac.Children.Clear();
        foreach (var o in e.Objets) _sac.Children.Add(Pastille(Aventure.NomObjet(c, o), Bandeau.ArgentClair, o));
        if (e.Objets.Count == 0) _sac.Children.Add(Texte("rien pour l'instant", 11.5, Bandeau.Argent));
        bool fini = Pret;
        if (fini) MettreAJourDecor(e.Decor, e.Lieu);
        Actions(e, c, fini);
        // Compte à rebours de l'attente, à la seconde.
        if (_compte is not null && e.EnAttente)
        {
            double reste = e.Fin - _pilou.EpoqueAventure;
            _compte.Text = reste > 0 ? $"encore {Aventure.Restant(reste)}" : "il arrive…";
            if (_jaugeAttente is not null) _jaugeAttente.Child = Cases(1 - reste / Math.Max(1, e.Fin - e.T), 24, Bandeau.OrangePo);
        }
    }

    // Un élément gardé d'une construction à l'autre : détaché de son ancien parent avant d'être reposé.
    private static T Lib<T>(T e) where T : FrameworkElement
    {
        switch (e.Parent)
        {
            case Panel p:
                p.Children.Remove(e);
                break;
            case Decorator d:
                d.Child = null;
                break;
            case ContentControl c:
                c.Content = null;
                break;
        }
        return e;
    }

    // Réécrit un texte en police pixel (la largeur suit).
    private static void Reecrire(Pixels p, string texte, double taille)
    {
        var m = Police.Texte(texte.ToUpperInvariant());
        p.Changer(m);
        p.Width = (m.GetLength(1) + 2) * taille;
    }

    // Tout ce qu'il y avait à écrire est écrit (la zone d'action peut apparaître).
    private bool Pret => _montres >= _elements.Count && _enCours is null;

    // ---- L'écriture lettre à lettre (33 ms)

    private void Animer()
    {
        _t = _chrono.Elapsed.TotalMilliseconds;
        _anims.Avancer(_t);
        if (_vue != Vue.Lecture) return;
        double now = _t;
        if (_enCours is { } el && _texteEnCours is { } tb)
        {
            int n = _toutDeSuite || _anims.TexteInstantane ? el.Texte.Length : AnimationsCampagne.Lettres(el.Texte, (long)(now - _debutEcriture));
            tb.Text = n >= el.Texte.Length ? el.Texte : el.Texte[..n] + ((int)(now / 280) % 2 == 0 ? "▌" : " ");
            if (n >= el.Texte.Length)
            {
                _enCours = null;
                _texteEnCours = null;
                // Les « … » avant le message suivant : plus longs pour un long message (AnimationsCampagne.Attente).
                _pauseJusque = now + (_toutDeSuite || _anims.TexteInstantane ? 0
                    : _montres < _elements.Count ? AnimationsCampagne.Attente(_elements[_montres].Texte) : Aventure.PauseEntreMessages);
            }
            Defiler();
        }
        else if (_montres < _elements.Count && now >= _pauseJusque)
        {
            // Les messages déjà lus d'un coup ; le prochain nouveau message de Pilou, lettre à lettre.
            while (_montres < _elements.Count)
            {
                var x = _elements[_montres];
                _montres++;
                if (x.Sorte == Aventure.Sorte.Pilou && x.Nouveau && !_anims.TexteInstantane && !_toutDeSuite)
                {
                    var (ligne, texte) = BullePilou(x, "");
                    _fil.Children.Add(ligne);
                    Apparaitre(ligne, 180, 6);
                    _enCours = x;
                    _texteEnCours = texte;
                    _debutEcriture = now;
                    _humeurMontree = x.Humeur;
                    _dernierPilou = x;
                    MettreAJourDecor(x.Decor, x.Lieu);
                    break;
                }
                var el2 = Element(x);
                _fil.Children.Add(el2);
                if (x.Nouveau || x.Sorte == Aventure.Sorte.Joueur) Apparaitre(el2, 200, 6);
                if (x.Sorte == Aventure.Sorte.Pilou)
                {
                    _humeurMontree = x.Humeur;
                    _dernierPilou = x;
                }
                if (x.Sorte == Aventure.Sorte.Chapitre && _montres < _elements.Count && _elements[_montres].Nouveau) Embleme(el2);
                if (x.Sorte is Aventure.Sorte.Pilou or Aventure.Sorte.Reprise) MettreAJourDecor(x.Decor, x.Lieu);
            }
            Defiler();
            if (Pret)
            {
                _toutDeSuite = false;
                if (_pilou.CarnetCampagnes.NonLus > 0) _pilou.CampagneMarquerLu();
                _cleAction = "";
                if (_etat is { } e && _campagne is { } c) Actions(e, c, true);
            }
        }
        // « Pilou écrit… » entre deux messages nouveaux.
        bool ecrit = _enCours is null && _montres < _elements.Count && _elements[_montres] is { Sorte: Aventure.Sorte.Pilou, Nouveau: true } && !_anims.TexteInstantane;
        if (ecrit != (_ecrit.Visibility == Visibility.Visible))
        {
            if (_ecrit.Parent is Panel p) p.Children.Remove(_ecrit);
            if (ecrit) _fil.Children.Add(_ecrit);
            _ecrit.Visibility = ecrit ? Visibility.Visible : Visibility.Collapsed;
        }
        if (ecrit)
            for (int i = 1; i < _ecrit.Children.Count; i++)
                _ecrit.Children[i].Opacity = (int)(now / 220) % 3 == i - 1 ? 1 : 0.3;

        // Le portrait : l'humeur du message en cours, il cligne ; il sautille un peu pendant qu'il écrit.
        if ((int)(now / 33) % 3 == 0) Portrait(now);
        PersonnageEnScene(now);
        if (_voyage is not null && _etat is { EnAttente: true } ea && (int)(now / 33) % 2 == 0)
        {
            var a = _pilou.AllurePortrait("repos", now, "voyage-" + (Array.IndexOf(RenduPilou.Voyages, ea.Tenue) >= 0 ? ea.Tenue : "marche"));
            if (ea.Phase == Phase.Repos) a.Objets = a.Objets.Append("pansement").ToList();
            if (Apercu.ImageSiChange(a, ref _voyagePrecedent, fin: true) is { } im) _voyage.Source = im;
        }
        _epreuve?.Animer();
    }

    private void Portrait(double now)
    {
        var humeur = _enCours?.Humeur ?? _humeurMontree;
        var a = _pilou.AllurePortrait(humeur is "" or "neutre" ? "repos" : humeur, now);
        if (!_anims.Aucune) a.Cligne = AnimationsCampagne.Cligne((long)now);     // même rythme que les personnages
        if (_enCours is not null && _anims.Completes) a.Saut = Math.Abs(Math.Sin(now / 160)) * 0.6;
        if (Apercu.ImageSiChange(a, ref _portraitPrecedent, fin: true) is { } im) _portrait.Source = im;
        _humeur.Text = NomHumeur(humeur);
    }

    private static string NomHumeur(string h) => h switch
    {
        "joie" => "◠ Pilou est tout content", "peur" => "◌ Pilou a un peu peur", "triste" => "◡ Pilou est triste", "surpris" => "◯ Pilou est surpris",
        "determine" => "▲ Pilou est décidé", "fatigue" => "◡ Pilou est fatigué", "tendre" => "♥ Pilou est attendri", "colere" => "◆ Pilou est fâché",
        "malice" => "◠ Pilou a une idée", _ => "· Pilou t'écoute",
    };

    private void Defiler()
    {
        if (_defile.VerticalOffset >= _defile.ScrollableHeight - 80 || _enCours is not null) _defile.ScrollToEnd();
    }

    // Un clic dans le fil (ou Espace) : le message en cours s'écrit d'un coup ; deux clics rapprochés : tout le reste.
    private void Accelerer()
    {
        if (_vue != Vue.Lecture) return;
        bool double_ = _t - _dernierClic < 450;
        _dernierClic = _t;
        if (_enCours is not null) _debutEcriture = -1e9;
        else _pauseJusque = 0;
        if (double_) _toutDeSuite = true;
    }

    private void MettreAJourDecor(string decor, string lieu)
    {
        if (_campagne is not { } c) return;
        var cle = decor + "|" + lieu;
        if (cle == _decorMontre) return;
        _decorMontre = cle;
        // Le décor animé (ScenesAnimees) : sa boucle, et une transition depuis le précédent (volet pixelisé ou fondu).
        var anime = Illustrations.Decor(Banque.Commune, c.Id, decor, ScenesAnimees.Echelle);
        bool premier = _decorImage.Source is null;
        object? sprite = _anims.Decor(_decorImage, _decorAncien, anime, _t) ? anime : null;
        _decorImage.Visibility = sprite is null ? Visibility.Collapsed : Visibility.Visible;
        if (sprite is not null && premier) Apparaitre(_decorImage, 420, 0);
        var nom = lieu != "" ? lieu : Aventure.NomDecor(c, decor);
        Reecrire(_decorLieu, nom, 3);
        _decorChapitre.Text = _etat is { } e ? $"{c.Titre} · chapitre {e.ChapitreNumero} · {e.ChapitreTitre}" : c.Titre;
        _lieu.Text = nom == "" ? "" : "▸ " + nom;
        if (sprite is null && _bandeDecor.Children.Count > 0 && _bandeDecor.Children[0] is Border fond)
        {
            // Pas encore de dessin pour ce décor : un ciel sobre, et le nom du lieu.
            fond.Background = Ciel(c.Ton);
            var deco = _bandeDecor.Children.OfType<FrameworkElement>().FirstOrDefault(x => x.Tag as string == "paysage");
            if (deco is not null) _bandeDecor.Children.Remove(deco);
            var paysage = new Grid { Tag = "paysage", IsHitTestVisible = false };
            paysage.Children.Add(Etoiles(760, 118, Hasard.Graine(cle)));
            paysage.Children.Add(Collines(760, 118, c.Ton, Hasard.Graine(cle + "/c")));
            _bandeDecor.Children.Insert(1, paysage);
        }
    }

    private (UIElement Ligne, TextBlock Texte) BullePilou(Aventure.Element x, string texte)
    {
        var tb = Texte(texte, 13.5, Encre);
        tb.LineHeight = 20;
        var bulle = new Border
        {
            Background = Parchemin, BorderBrush = ParcheminBord, BorderThickness = new Thickness(2), Padding = new Thickness(12, 8, 12, 9),
            MaxWidth = 560, HorizontalAlignment = HorizontalAlignment.Left, Child = tb,
        };
        var g = new Grid { Margin = new Thickness(0, 0, 60, 10) };
        g.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(40) });
        g.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        // Une petite tête au début d'une série de messages, la pointe de la bulle vers elle.
        var avant = _fil.Children.OfType<FrameworkElement>().LastOrDefault(f => !ReferenceEquals(f, _ecrit));
        bool premier = avant is not { Tag: "pilou" };
        if (premier)
        {
            var tete = new Image { Source = Apercu.Image(_pilou.AllurePortrait(x.Humeur is "" or "neutre" ? "repos" : x.Humeur, 0), fin: true), Width = 34, Height = 40, VerticalAlignment = VerticalAlignment.Top };
            RenderOptions.SetBitmapScalingMode(tete, BitmapScalingMode.NearestNeighbor);
            g.Children.Add(tete);
            var pointe = new Pixels(Pixels.Motif("0001", "0012", "0122", "0012", "0001"), new Brush?[] { null, ParcheminBord, Parchemin }, null, 2)
                { HorizontalAlignment = HorizontalAlignment.Right, VerticalAlignment = VerticalAlignment.Top, Margin = new Thickness(0, 10, -2, 0) };
            g.Children.Add(pointe);
        }
        Grid.SetColumn(bulle, 1);
        g.Children.Add(bulle);
        g.Tag = "pilou";
        return (g, tb);
    }

    private UIElement Element(Aventure.Element x)
    {
        switch (x.Sorte)
        {
            case Aventure.Sorte.Chapitre:
            {
                var g = new Grid { Margin = new Thickness(0, 10, 0, 14), Tag = "chapitre" };
                g.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
                g.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
                g.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
                g.Children.Add(new Border { Height = 2, Background = Bandeau.Bord, VerticalAlignment = VerticalAlignment.Center, Margin = new Thickness(0, 0, 10, 0) });
                var t = Enseigne(x.Texte, Bandeau.OrangePo, 2);
                Grid.SetColumn(t, 1);
                g.Children.Add(t);
                var d = new Border { Height = 2, Background = Bandeau.Bord, VerticalAlignment = VerticalAlignment.Center, Margin = new Thickness(10, 0, 0, 0) };
                Grid.SetColumn(d, 2);
                g.Children.Add(d);
                return g;
            }
            case Aventure.Sorte.Joueur:
            {
                var tb = Texte("▶ " + x.Texte, 13, Bandeau.ArgentClair, true);
                var p = new StackPanel { HorizontalAlignment = HorizontalAlignment.Right, Margin = new Thickness(90, 2, 0, 12), Tag = "joueur" };
                p.Children.Add(new TextBlock { Text = "toi", FontSize = 10.5, Foreground = Bandeau.Violet, HorizontalAlignment = HorizontalAlignment.Right, FontFamily = new FontFamily("Segoe UI"), Margin = new Thickness(0, 0, 4, 2) });
                p.Children.Add(new Border { Background = CaseClaire, BorderBrush = Bandeau.Violet, BorderThickness = new Thickness(2), Padding = new Thickness(12, 7, 12, 8), MaxWidth = 460, Child = tb });
                return p;
            }
            case Aventure.Sorte.Reprise:
            {
                var p = new StackPanel { Margin = new Thickness(40, 2, 60, 12), Tag = "reprise" };
                var tete = new StackPanel { Orientation = Orientation.Horizontal, Cursor = Cursors.Hand };
                tete.Children.Add(Texte(x.Texte, 13, Bandeau.Violet, true));
                var plus = Texte($"   ▸ relire ({x.Sous.Count})", 11.5, Bandeau.Argent);
                tete.Children.Add(plus);
                p.Children.Add(tete);
                var sous = new StackPanel { Visibility = Visibility.Collapsed, Margin = new Thickness(10, 4, 0, 0) };
                foreach (var s in x.Sous)
                {
                    var t = Texte(s, 12, Bandeau.Argent);
                    t.FontStyle = FontStyles.Italic;
                    t.Margin = new Thickness(0, 0, 0, 4);
                    sous.Children.Add(t);
                }
                p.Children.Add(sous);
                tete.MouseLeftButtonUp += (_, ev) =>
                {
                    ev.Handled = true;
                    bool ouvert = sous.Visibility == Visibility.Visible;
                    sous.Visibility = ouvert ? Visibility.Collapsed : Visibility.Visible;
                    plus.Text = ouvert ? $"   ▸ relire ({x.Sous.Count})" : "   ▾ replier";
                };
                return p;
            }
            default:
                return BullePilou(x, x.Texte).Ligne;
        }
    }

    // ---- Zone d'action : options, « vas-y », épreuve, attente, repos, fin

    private void Actions(Etat e, Campagne c, bool pret)
    {
        var cle = $"{e.Phase}|{e.Noeud}|{e.E}|{string.Join(",", e.Options.Select(o => o.Id))}|{pret}|{_confirmer}|{_message}|{_epreuve is not null}|{e.Reprise}";
        if (cle == _cleAction) return;
        _cleAction = cle;
        _compte = null;
        _heureRetour = null;
        _jaugeAttente = null;
        _voyage = null;
        _voyagePrecedent = null;
        var p = new StackPanel();
        if (!pret)
        {
            p.Children.Add(Texte("… (clic dans le fil : il écrit plus vite)", 11.5, Bandeau.Argent));
            _action.Child = p;
            return;
        }
        if (_message != "") p.Children.Add(Texte("◌ " + _message, 12, Bandeau.Violet, true));
        if (_confirmer)
        {
            p.Children.Add(Texte("Mettre l'aventure de côté ?", 15, Bandeau.ArgentClair, true));
            p.Children.Add(Texte("Pilou rentre à la maison. L'aventure reprendra au dernier check-point : ce qui est acquis reste acquis.", 12.5, Bandeau.Argent));
            var l = Rangee();
            l.Children.Add(Bouton("◌ Oui, la mettre de côté", false, () =>
            {
                _confirmer = false;
                _message = _pilou.CampagneAbandonner() ?? "";
                _cleAction = "";
                if (_message == "") Montrer(Vue.Bibliotheque);
                else Rafraichir();
            }));
            l.Children.Add(Bouton("▶ Non, on continue", true, () =>
            {
                _confirmer = false;
                _cleAction = "";
                Rafraichir();
            }));
            p.Children.Add(l);
            Poser(p);
            return;
        }
        switch (e.Phase)
        {
            case Phase.Choix:
            {
                p.Children.Add(Enseigne(e.Reprise ? "ON REPREND ICI · QUE FAIT PILOU ?" : "QUE FAIT PILOU ?", Bandeau.OrangePo, 2));
                if (e.Reprise)
                    p.Children.Add(Texte("↺ Après son repos, Pilou repart du dernier check-point. Ce qui était acquis l'est toujours.", 11.5, Bandeau.Violet));
                var l = new WrapPanel { Margin = new Thickness(0, 8, 0, 0) };
                int i = 1;
                foreach (var o in e.Options)
                {
                    int n = i++;
                    var b = BoutonOption(n, o.Libelle, () => Choisir(o.Id));
                    l.Children.Add(b);
                    if (Bandeau.Anime)
                    {
                        b.Opacity = 0;
                        b.BeginAnimation(OpacityProperty, new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(220)) { BeginTime = TimeSpan.FromMilliseconds(70 * n) });
                    }
                }
                p.Children.Add(l);
                break;
            }
            case Phase.Depart:
            {
                p.Children.Add(Enseigne("PILOU EST PRÊT À REPARTIR", Bandeau.OrangePo, 2));
                var l = Rangee();
                l.Children.Add(Bouton("▶ Vas-y !   (Entrée)", true, Continuer, 14));
                p.Children.Add(l);
                break;
            }
            case Phase.Epreuve:
                p.Children.Add(CarteEpreuve(e));
                break;
            case Phase.Attente:
            case Phase.Repos:
                p.Children.Add(CarteAttente(e));
                break;
            case Phase.Fin:
                p.Children.Add(CarteFinale(e, c));
                break;
            case Phase.Abandon:
            {
                p.Children.Add(Texte("◌ Aventure mise de côté.", 15, Bandeau.ArgentClair, true));
                p.Children.Add(Texte("Elle reprendra au dernier check-point quand tu voudras.", 12.5, Bandeau.Argent));
                var l = Rangee();
                l.Children.Add(Bouton("◌ Reprendre", true, () => Demarrer(c.Id, false)));
                l.Children.Add(Bouton("☰ Bibliothèque", false, () => Montrer(Vue.Bibliotheque)));
                p.Children.Add(l);
                break;
            }
            default:
                p.Children.Add(Texte("Cette aventure a un souci dans ses fichiers : elle ne peut pas continuer ici. Une mise à jour la réparera.", 12.5, Bandeau.Argent));
                break;
        }
        Poser(p);
    }

    private void Poser(UIElement contenu)
    {
        _action.Child = contenu;
        Apparaitre(contenu, 240, 10);
    }

    private static WrapPanel Rangee() => new() { Margin = new Thickness(0, 10, 0, 0) };

    private Button BoutonOption(int n, string libelle, Action action)
    {
        var contenu = new StackPanel { Orientation = Orientation.Horizontal };
        contenu.Children.Add(new Border
        {
            Background = Bandeau.Nuit, BorderBrush = Bandeau.Bord, BorderThickness = new Thickness(1), Padding = new Thickness(4, 3, 4, 3),
            Margin = new Thickness(0, 0, 10, 0), VerticalAlignment = VerticalAlignment.Center,
            Child = new Pixels(Police.Texte(n.ToString()), new Brush?[] { null, Bandeau.OrangePo }, null, 2),
        });
        contenu.Children.Add(new TextBlock
        {
            Text = libelle, FontSize = 13.5, FontFamily = new FontFamily("Segoe UI"), FontWeight = FontWeights.SemiBold, TextWrapping = TextWrapping.Wrap,
            MaxWidth = 300, VerticalAlignment = VerticalAlignment.Center,
        });
        var b = Bouton("", false, action);
        b.Content = contenu;
        b.MinWidth = 220;
        b.MaxWidth = 360;
        b.Tag = n;
        b.ToolTip = $"touche {n}";
        return b;
    }

    private void Choisir(string option)
    {
        _message = _pilou.CampagneChoisir(option) ?? "";
        _cleAction = "";
        Rafraichir();
    }

    private void Continuer()
    {
        _message = _pilou.CampagneContinuer() ?? "";
        _cleAction = "";
        Rafraichir();
    }

    private UIElement CarteEpreuve(Etat e)
    {
        var p = new StackPanel();
        var tete = new StackPanel { Orientation = Orientation.Horizontal };
        tete.Children.Add(Texte(Aventure.SigneJeu(e.Jeu) + "  ", 20, Bandeau.OrangePo, true));
        tete.Children.Add(Enseigne($"ÉPREUVE · {Aventure.NomJeu(e.Jeu)}", Bandeau.OrangePo, 2.5));
        tete.Children.Add(Texte($"   {Aventure.Pastilles(e.Difficulte)}", 14, Bandeau.Violet, true));
        p.Children.Add(tete);
        var aide = e.Aide > 0 ? $" · ce que Pilou a appris l'aide (+{e.Aide})" : "";
        p.Children.Add(Texte(Aventure.Consigne(e.Jeu) + aide, 12.5, Bandeau.Argent));
        var l = Rangee();
        if (!JeuAuto(e.Jeu))
            l.Children.Add(Bouton("▶ Jouer (≈ 15 s)", true, () => LancerEpreuve(e, false), 14));
        l.Children.Add(Bouton($"⚄ Laisser faire les dés ({e.Chance} %)", JeuAuto(e.Jeu), () => LancerEpreuve(e, true), 13));
        p.Children.Add(l);
        return p;
    }

    private void LancerEpreuve(Etat e, bool des)
    {
        if (_epreuve is not null) return;
        var graine = Hasard.Graine($"{_pilou.CarnetCampagnes.Courante?.Graine}|{e.Noeud}|{e.E}");
        VueEpreuve v;
        if (des || JeuAuto(e.Jeu))
        {
            if (_pilou.CampagneDeVa() is not { } va) return;
            v = new VueEpreuve(null, new TirageDes(e.Chance, va, graine), e);
        }
        else
        {
            var jeu = MiniJeu.Creer(e.Jeu, e.Difficulte, e.Aide, graine);
            if (jeu is null) return;
            v = new VueEpreuve(jeu, null, e);
        }
        v.Fini += (reussi, auDe) => Sur(() => FinEpreuve(reussi, auDe));
        v.AuxDes += () => Sur(() =>
        {
            FermerEpreuve();
            LancerEpreuve(e, true);
        });
        _epreuve = v;
        _scene.Children.Add(v);
        Apparaitre(v, 200, 0);
        _cleAction = "";
        _action.Child = Texte("Concentre-toi… (Échap : laisser faire les dés)", 12, Bandeau.Argent);
        Focus();
    }

    private void FermerEpreuve()
    {
        if (_epreuve is null) return;
        _scene.Children.Remove(_epreuve);
        _epreuve = null;
        _cleAction = "";
    }

    private void FinEpreuve(bool reussi, bool auDe)
    {
        FermerEpreuve();
        _message = (auDe ? _pilou.CampagneAuDe() : _pilou.CampagneEpreuve(reussi)) ?? "";
        Rafraichir();
    }

    private UIElement CarteAttente(Etat e)
    {
        var g = new Grid();
        g.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        g.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        var cadre = new Grid { Width = 132, Height = 132, ClipToBounds = true, Margin = new Thickness(0, 0, 16, 0) };
        cadre.Children.Add(new Border { Background = Ciel(_campagne?.Ton ?? "") });
        cadre.Children.Add(new Border { Height = 18, VerticalAlignment = VerticalAlignment.Bottom, Background = Gel("#16365e") });
        _voyage = new Image { Width = 112, Height = 131, VerticalAlignment = VerticalAlignment.Bottom, Stretch = Stretch.Uniform };
        RenderOptions.SetBitmapScalingMode(_voyage, BitmapScalingMode.NearestNeighbor);
        cadre.Children.Add(_voyage);
        cadre.Children.Add(new Border { BorderBrush = Ombre, BorderThickness = new Thickness(2) });
        g.Children.Add(cadre);
        var p = new StackPanel { VerticalAlignment = VerticalAlignment.Center };
        bool repos = e.Phase == Phase.Repos;
        p.Children.Add(Enseigne(repos ? "PILOU SE REPOSE" : "PILOU EST EN ROUTE", Bandeau.OrangePo, 2));
        var pendant = Texte(repos ? "Il est rentré un peu cabossé. Il reprend des forces." : (e.Pendant == "" ? "Pilou avance" : e.Pendant), 16, Bandeau.ArgentClair, true);
        pendant.Margin = new Thickness(0, 6, 0, 2);
        p.Children.Add(pendant);
        _heureRetour = Texte($"{(repos ? "jusqu'à" : "retour vers")} {Aventure.Heure(e.Fin)}", 13, Bandeau.Argent);
        p.Children.Add(_heureRetour);
        var ligne = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(0, 6, 0, 6) };
        _compte = new TextBlock { FontFamily = new FontFamily("Consolas"), FontSize = 20, FontWeight = FontWeights.Bold, Foreground = Bandeau.OrangePo, VerticalAlignment = VerticalAlignment.Center };
        ligne.Children.Add(_compte);
        _jaugeAttente = new Border { Margin = new Thickness(14, 0, 0, 0), VerticalAlignment = VerticalAlignment.Center };
        ligne.Children.Add(_jaugeAttente);
        p.Children.Add(ligne);
        p.Children.Add(Texte(repos ? "Ensuite, il reprendra au dernier check-point. Tu peux fermer cette fenêtre : je te préviens."
                                   : "Tu peux fermer cette fenêtre : je te préviens à mon retour. (Je reste en bas de ton écran, en route.)", 12, Bandeau.Violet));
        Grid.SetColumn(p, 1);
        g.Children.Add(p);
        return g;
    }

    private UIElement CarteFinale(Etat e, Campagne c)
    {
        var k = _pilou.CarnetCampagnes;
        var g = new Grid();
        g.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        g.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        var teinte = Gel(Aventure.TeinteIssue(e.Issue));
        var signe = new TextBlock
        {
            Text = Aventure.SigneIssue(e.Issue), FontSize = 56, Foreground = teinte, FontFamily = new FontFamily("Segoe UI Symbol"),
            VerticalAlignment = VerticalAlignment.Center, Margin = new Thickness(6, 0, 22, 0), RenderTransformOrigin = new System.Windows.Point(0.5, 0.5),
        };
        if (Bandeau.Anime)
        {
            var s = new ScaleTransform(0.4, 0.4);
            signe.RenderTransform = s;
            var a = new DoubleAnimation(0.4, 1, TimeSpan.FromMilliseconds(620)) { EasingFunction = new ElasticEase { Oscillations = 2, Springiness = 5 } };
            s.BeginAnimation(ScaleTransform.ScaleXProperty, a);
            s.BeginAnimation(ScaleTransform.ScaleYProperty, a);
        }
        g.Children.Add(signe);
        var p = new StackPanel();
        p.Children.Add(Enseigne(Aventure.NomIssue(e.Issue), teinte, 2.5));
        var titre = Texte($"« {e.TitreFin} »", 18, Bandeau.ArgentClair, true);
        titre.Margin = new Thickness(0, 6, 0, 6);
        p.Children.Add(titre);
        var gains = new WrapPanel();
        int i = 0;
        foreach (var x in Aventure.Gains(c, e))
        {
            var pas = Pastille(x, x.StartsWith('+') ? Bandeau.OrangePo : x.StartsWith('✦') ? Gel(Aventure.Or) : Bandeau.Violet, x.StartsWith('✦') ? e.Recompenses.Objet : null);
            gains.Children.Add(pas);
            _anims.Tomber(pas, AnimationsCampagne.DelaiRecompense(i++));
        }
        if (e.Rejeu) gains.Children.Add(Pastille("rejouée : ni po ni xp, mais les souvenirs manquants", Bandeau.Argent));
        // Le souvenir obtenu se pose avec un petit éclat, puis l'emblème du ton de la campagne.
        var vitrine = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(0, 4, 0, 6) };
        if (e.Recompenses.Souvenir is { Length: > 0 } sv && Illustrations.Souvenir(Banque.Commune, c.Id, sv, ScenesAnimees.Echelle) is { } ss)
            vitrine.Children.Add(_anims.Eclat(ScenesAnimees.Vue(ss, 72), 104, teinte, AnimationsCampagne.DelaiRecompense(i)));
        if (Illustrations.Ton(Banque.Commune, c.Ton, ScenesAnimees.Echelle) is { } ts)
            vitrine.Children.Add(_anims.Eclat(ScenesAnimees.Vue(ts, 36), 60, Gel(Aventure.TeinteTon(c.Ton)), AnimationsCampagne.DelaiRecompense(i + 1)));
        if (vitrine.Children.Count > 0) p.Children.Add(vitrine);
        p.Children.Add(gains);
        p.Children.Add(Texte($"Fins trouvées : {Aventure.Fins6(k, c)}", 13, Bandeau.ArgentClair, true));
        var l = Rangee();
        l.Children.Add(Bouton("❖ Le carnet", true, () => Montrer(Vue.Carnet)));
        l.Children.Add(Bouton("↻ Rejouer", false, () => Demarrer(c.Id, true)));
        l.Children.Add(Bouton("☰ Bibliothèque", false, () => Montrer(Vue.Bibliotheque)));
        p.Children.Add(l);
        Grid.SetColumn(p, 1);
        g.Children.Add(p);
        return g;
    }

    // ---- Animations : personnage en scène, emblème de chapitre, réglages

    // Le personnage du message en cours (ou du dernier) : son portrait au bord de la scène ; il parle tant que Pilou
    // écrit une de ses répliques (« … »).
    private void PersonnageEnScene(double now)
    {
        var el = _enCours ?? _dernierPilou;
        var cle = el?.Cle ?? "";
        if (cle != _persoCle)
        {
            _persoCle = cle;
            Sprite? s = null;
            string nom = "";
            if (el is not null && _campagne is { } c && AnimationsCampagne.PersonnageDe(_pilou.CarnetCampagnes, c, cle) is { } pe)
            {
                s = AnimationsCampagne.Portrait(Banque.Commune, c.Id, pe.Personnage, pe.Expression, ScenesAnimees.Echelle);
                nom = NomPersonnage(pe.Personnage);
            }
            _persoNom.Text = nom;
            _anims.Personnage(_persoImage, s, false, now);
        }
        _anims.Parle(_enCours is { } e && AnimationsCampagne.Parle(e.Texte));
    }

    private static string NomPersonnage(string id) => id switch
    {
        "grumeau" => "Grumeau", "le-rond" => "le Rond", "mlle-renvoi" => "Mlle Renvoi", "golem" => "le golem de tickets",
        "spectre-404" => "Quatre-Cent-Quatre", "dateur" => "le Dateur", "mme-echeance" => "Mme Échéance", "raccourcis" => "Ctrl, Alt et Suppr",
        "touche-s" => "S", "imprimante" => "l'Imprimante", "brouillon" => "Brouillon", "tic-tac" => "le Tic-Tac", "balayeur" => "le Balayeur",
        "anselme" => "Anselme", "lison" => "Lison", "tudal" => "Tudal", "perrine" => "Perrine", "odile" => "Odile", "basile" => "Basile",
        "vernier" => "M. Vernier", "tournebise" => "Tournebise", "ondee" => "Ondée", "mi-bemol" => "Mi-Bémol", "dentelle" => "Dentelle",
        "madame-bocal" => "Madame Bocal", "froisseuses" => "les Froisseuses", "enclumes" => "les Enclumes", "bergeronnette" => "la bergeronnette",
        _ => "",
    };

    // Un chapitre qui commence : l'emblème du ton de la campagne se pose au milieu du séparateur, avec un éclat.
    private void Embleme(UIElement separateur)
    {
        if (separateur is not Grid g || _campagne is not { } c || Illustrations.Ton(Banque.Commune, c.Ton, ScenesAnimees.Echelle) is not { } ts) return;
        var e = _anims.Eclat(ScenesAnimees.Vue(ts, 24), 44, Gel(Aventure.TeinteTon(c.Ton)), 120);
        g.ColumnDefinitions.Insert(1, new ColumnDefinition { Width = GridLength.Auto });
        foreach (UIElement x in g.Children)
            if (Grid.GetColumn(x) >= 1) Grid.SetColumn(x, Grid.GetColumn(x) + 1);
        Grid.SetColumn(e, 1);
        if (e is FrameworkElement fe) fe.Margin = new Thickness(0, 0, 8, 0);
        g.Children.Add(e);
    }

    // Le bouton « ✧ » : animations complètes, réduites ou aucune ; texte écrit d'un coup.
    private void MenuAnimations()
    {
        var m = new ContextMenu();
        void Choix(string texte, string niveau)
        {
            var i = new MenuItem { Header = texte, IsCheckable = true, IsChecked = _pilou.AnimationsCampagnes == niveau };
            i.Click += (_, _) => Sur(() =>
            {
                _pilou.AnimationsCampagnes = niveau;
                _cleVue = "";
                Rafraichir();
            });
            m.Items.Add(i);
        }
        Choix("Animations complètes", AnimationsCampagne.Completes);
        Choix("Animations réduites (décors fixes)", AnimationsCampagne.Reduites);
        Choix("Aucune animation", AnimationsCampagne.Aucune);
        m.Items.Add(new Separator());
        var t = new MenuItem { Header = "Texte instantané (sans lettre à lettre)", IsCheckable = true, IsChecked = _pilou.TexteInstantane };
        t.Click += (_, _) => Sur(() => _pilou.TexteInstantane = !_pilou.TexteInstantane);
        m.Items.Add(t);
        if (!Bandeau.Anime)
            m.Items.Add(new MenuItem { Header = "(Windows demande moins d'animations : rien ne bouge)", IsEnabled = false });
        m.Placement = PlacementMode.Bottom;
        m.PlacementTarget = _onglets;
        m.IsOpen = true;
    }

    // ---- Clavier : 1 à 4 (options, ou signes de la mémoire), Espace / Entrée (accélérer, « vas-y », jouer), Échap.

    private void Touche(KeyEventArgs e)
    {
        if (_epreuve is { } v)
        {
            e.Handled = v.Touche(e.Key);
            return;
        }
        if (_vue != Vue.Lecture) return;
        int n = e.Key switch { Key.D1 or Key.NumPad1 => 1, Key.D2 or Key.NumPad2 => 2, Key.D3 or Key.NumPad3 => 3, Key.D4 or Key.NumPad4 => 4, _ => 0 };
        if (n > 0 && Pret && _etat is { Phase: Phase.Choix } ec && n <= ec.Options.Count && !_confirmer)
        {
            e.Handled = true;
            Choisir(ec.Options[n - 1].Id);
            return;
        }
        if (e.Key is Key.Space or Key.Enter)
        {
            if (!Pret)
            {
                e.Handled = true;
                Accelerer();
            }
            else if (_etat is { Phase: Phase.Depart } && !_confirmer && e.Key == Key.Enter)
            {
                e.Handled = true;
                Continuer();
            }
        }
        if (e.Key == Key.Escape && _confirmer)
        {
            e.Handled = true;
            _confirmer = false;
            _cleAction = "";
            Rafraichir();
        }
    }
}
