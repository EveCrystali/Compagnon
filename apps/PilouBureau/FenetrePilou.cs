using System.Diagnostics;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Interop;
using System.Windows.Media;
using System.Windows.Shapes;
using System.Windows.Threading;

namespace PilouBureau;

// Fenêtre transparente toujours au premier plan : Pilou vit sur le bas de l'écran,
// avec au-dessus de lui une bulle qui dit où en est chaque session (Claude, Codex, autres sources).
// Seuls ses pixels et la bulle prennent la souris ; le reste laisse passer les clics.
public sealed partial class FenetrePilou : Window
{
    private const double LargeurBase = Placement.LargeurBase;
    private const double HauteurBulle = Placement.HauteurBulle;

    private enum Geste { Rien, Marche, Assis, Baille, Ballon, SauteSouris }

    private sealed record Palette(Brush Fond, Brush Bord, Brush Texte, Brush Pale, Brush Bleu, Brush Orange);

    private static readonly Palette Claire = new(
        Gel(0xf2, 0xf6, 0xf8, 0xfa), Gel(0xff, 0x6c, 0xb6, 0xff), Gel(0xff, 0x1c, 0x21, 0x28),
        Gel(0xff, 0x57, 0x60, 0x6a), Gel(0xff, 0x2f, 0x7e, 0xd8), Gel(0xff, 0xc8, 0x6a, 0x1c));
    private static readonly Palette Sombre = new(
        Gel(0xf2, 0x2d, 0x33, 0x3b), Gel(0xff, 0x6c, 0xb6, 0xff), Gel(0xff, 0xcd, 0xd9, 0xe5),
        Gel(0xff, 0x90, 0x9d, 0xab), Gel(0xff, 0x6c, 0xb6, 0xff), Gel(0xff, 0xf6, 0x9d, 0x50));

    private readonly string _dossier;
    private readonly bool _devant;
    private readonly Reglages _reglages;
    private readonly Scene _scene = new();
    private readonly Grid _racine = new();
    private readonly Border _bulle;
    private readonly StackPanel _lignes = new();
    private readonly StackPanel _pileBulle;
    private readonly Pixels _queue;
    private readonly Suivi _suivi = new();
    private readonly Stopwatch _chrono = Stopwatch.StartNew();
    private readonly Random _hasard = new();
    private readonly DispatcherTimer _image;
    private readonly DispatcherTimer _lecture;
    private readonly Dictionary<string, (bool EnTour, string Attente, double FinTour)> _vus = new();
    // Ce que la personne a déjà lu (clic sur la bulle ou sur Pilou) : session → signature de son état.
    private readonly Dictionary<string, string> _lus = new();
    private IReadOnlyList<EtatSession> _vivantes = Array.Empty<EtatSession>();

    private IntPtr _nous;
    private Rect _zone;
    private bool _zoneConnue;
    private double _x, _yPieds, _vy;
    private bool _auSol = true;
    private double _cible;
    private Geste _geste = Geste.Rien;
    private double _gesteFin, _pauseJusque = 3000;
    private double _assis;
    private int _sens = 1;
    private double _clignePlus = 2000, _cligneFin, _regardPlus = 3000, _clinFin;
    private int _regard;
    private double _tCaresse = -1e9, _atterri = -1e9, _tSaut = -1e9, _salueJusque = -1e9, _alerteJusque = -1e9;
    private double _dernierEvenement;
    private double _cacheJusque;
    private Point? _appui;
    private double _appuiT;
    private bool _attrape;
    private Vector _prise;
    private double _dernierT;
    private bool _aGauche;
    private int _image0;
    private bool _attend;
    private bool _court;
    // Jeux : souris, toque, ballon, messages.
    private Point _souris;
    private readonly Queue<(double T, Point P)> _trace = new();
    private double _etourdiJusque = -1e9;
    private double _survolSceneDebut = -1;
    private bool _ronronDit;
    private double _toqueDebut = -1e9;
    private Point _sautDepart, _sautCible;
    private double _sautDebut;
    private double _balleX, _balleRot, _balleKick = -1e9;
    private string _message = "";
    private double _messageJusque = -1e9;
    private readonly HashSet<string> _dit = new();
    private double _inactif;
    private bool _survol;
    private bool _sombre;
    private double _themeLu = -1e9;

    public FenetrePilou(string dossier, bool devant = false, bool demo = false)
    {
        _dossier = dossier;
        _devant = devant;
        _demo = demo;
        _reglages = Reglages.Lire(dossier);
        if (demo) Tournage.Regler(_reglages); // tournage : réglages fictifs, en mémoire (FenetreVisite.cs)
        CalculerEchelle();
        WindowStyle = WindowStyle.None;
        AllowsTransparency = true;
        Background = Brushes.Transparent;
        ShowInTaskbar = false;
        ResizeMode = ResizeMode.NoResize;
        ShowActivated = false;
        Topmost = true;
        Title = "Pilou";

        // Pointe en escalier : 1 bord, 2 fond (la rangée du haut efface le bord de la bulle).
        _queue = new Pixels(Pixels.Motif("1222221", "0122210", "0012100", "0001000"), new Brush?[] { null, Brushes.Transparent, Brushes.Transparent }, null, 3);
        _bulle = new Border
        {
            BorderThickness = new Thickness(3),
            CornerRadius = new CornerRadius(0),
            Padding = new Thickness(10, 5, 10, 6),
            MaxWidth = LargeurBase - 8,
            Child = _lignes,
            Cursor = Cursors.Hand,
            ToolTip = "Clic : afficher Claude ; la bulle se range (c'est lu)",
        };
        _bulle.MouseLeftButtonUp += (_, e) =>
        {
            // Pilou demande ton prénom (une seule fois) : un clic ouvre la petite fenêtre, où refuser est aussi simple.
            if (ClicPrenom(e.OriginalSource))
            {
                e.Handled = true;
                return;
            }
            // Ce qui parle de l'aventure (ligne d'attente, annonce du retour) ouvre la fenêtre Aventure.
            if (ClicAventure(e.OriginalSource))
            {
                e.Handled = true;
                return;
            }
            ToutLu();
            Natif.Activer(Natif.TrouverClaude());
            e.Handled = true;
        };
        _pileBulle = new StackPanel
        {
            Orientation = Orientation.Vertical,
            VerticalAlignment = VerticalAlignment.Bottom,
            // La bulle descend jusqu'au-dessus de l'antenne (la scène garde une marge vide en haut).
            RenderTransform = new TranslateTransform(0, Scene.MargeY + 6 * Scene.PA),
        };
        _pileBulle.Children.Add(_bulle);
        _pileBulle.Children.Add(_queue);

        _scene.Width = Scene.Largeur;
        _scene.Height = Scene.Hauteur;
        _scene.Cursor = Cursors.Hand;

        _racine.RowDefinitions.Add(new RowDefinition { Height = new GridLength(HauteurBulle) });
        _racine.RowDefinitions.Add(new RowDefinition { Height = new GridLength(Scene.Hauteur) });
        Grid.SetRow(_pileBulle, 0);
        Grid.SetRow(_scene, 1);
        _racine.Children.Add(_pileBulle);
        _racine.Children.Add(_scene);
        _racine.MouseEnter += (_, _) => _survol = true;
        _racine.MouseLeave += (_, _) => _survol = false;
        Content = _racine;
        InitialiserJeux();
        AppliquerTaille();
        Placer(false);
        Peindre();

        var menu = new ContextMenu();
        menu.Opened += (_, _) =>
        {
            MenuRetro.Habiller(menu, _sombre || BulleSombre);
            Remplir(menu);
        };
        MenuRetro.Habiller(menu, _sombre || BulleSombre);
        Remplir(menu);
        // Fenêtre qui ne s'active pas : sans aide, le menu ne se fermait pas au clic ailleurs (MenuRetro.cs).
        _ = new MenuDiscret(menu, this);
        _scene.ContextMenu = menu;
        _bulle.ContextMenu = menu;

        _scene.MouseLeftButtonDown += Appui;
        _scene.MouseMove += Bouge;
        _scene.MouseLeftButtonUp += Relache;

        Finesse.Repli += () => Dispatcher.BeginInvoke(() =>
        {
            _reglages.DessinFin = false;
            _reglages.Ecrire(_dossier);
            AppliquerTaille();
            Dire("dessin fin indisponible sur cet écran : je reviens au dessin d'origine", 5000);
        });
        SourceInitialized += (_, _) =>
        {
            _nous = new WindowInteropHelper(this).Handle;
            Natif.StyleDiscret(_nous);
            // La fenêtre connaît maintenant son écran : si sa mise à l'échelle n'est pas celle supposée, on recalcule.
            if (Math.Abs(VisualTreeHelper.GetDpi(this).DpiScaleX - Finesse.Dpi) > 1e-6) AppliquerTaille();
        };

        _lecture = new DispatcherTimer(TimeSpan.FromMilliseconds(300), DispatcherPriority.Background, (_, _) => Lire(), Dispatcher);
        _image = new DispatcherTimer(TimeSpan.FromMilliseconds(33), DispatcherPriority.Render, (_, _) => Image(), Dispatcher);
        Loaded += (_, _) =>
        {
            Lire();
            _lecture.Start();
            _image.Start();
            DemarrerMises();
            DemarrerActivites();
            DemarrerConnecteurs();
            DemarrerGestes();
            Bienvenue();
        };
        Closed += (_, _) =>
        {
            ArreterGestes();
            Quotidien(EcrirePresence);
        };
    }

    private static Brush Gel(byte a, byte r, byte g, byte b)
    {
        var br = new SolidColorBrush(Color.FromArgb(a, r, g, b));
        br.Freeze();
        return br;
    }

    // Échelle de la fenêtre : la Taille choisie, ramenée en dessin fin à celle qui met un pixel fin de Pilou sur un
    // nombre entier de pixels physiques (Placement.Echelle) ; recalculée quand la Taille, le réglage ou l'écran changent.
    private double _k = 1;
    private double K => _k;
    private double Maintenant => _chrono.Elapsed.TotalMilliseconds;
    private static double Epoque => DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
    private Palette Couleurs => _sombre || BulleSombre ? Sombre : Claire;

    // La bulle de nuit (boutique) impose le texte clair du thème sombre.
    private bool BulleSombre => PilouBureau.Boutique.Style(EquipeCourant().GetValueOrDefault(PilouBureau.Boutique.Bulle, ""))?.Sombre == true;

    private static readonly Dictionary<string, Brush> _pinceaux = new();

    private static Brush Pinceau(string hex)
    {
        if (_pinceaux.TryGetValue(hex, out var b)) return b;
        var br = new SolidColorBrush((Color)ColorConverter.ConvertFromString(hex));
        br.Freeze();
        return _pinceaux[hex] = br;
    }

    // ---- Options (clic droit)

    private void Remplir(ContextMenu menu)
    {
        menu.Items.Clear();
        // En tête : le bandeau (niveau, XP, po) et la boutique, mise en avant.
        menu.Items.Add(BandeauMenu());
        int neufs = NouveautesBoutique();
        menu.Items.Add(Entree(neufs > 0 ? $"🛒 Boutique ({neufs} nouveauté{(neufs > 1 ? "s" : "")})" : "🛒 Boutique", OuvrirBoutique));
        menu.Items.Add(Prudemment(MenuAventure, Entree("✉ Aventure…", OuvrirAventure)));
        menu.Items.Add(new Separator());
        menu.Items.Add(Entree("♥ Caresser", Caresser));
        menu.Items.Add(Entree("♥ Prendre soin de Pilou", PrendreSoin));
        menu.Items.Add(MenuSoins());
        menu.Items.Add(MenuPilouEtMoi());
        menu.Items.Add(Entree("Afficher Claude", () => Natif.Activer(Natif.TrouverClaude())));
        menu.Items.Add(new Separator());
        menu.Items.Add(Choix("Taille", new[] { ("Petit", 0.75), ("Normal", 1.0), ("Grand", 1.3) }, _reglages.Taille,
            v => { _reglages.Taille = v; AppliquerTaille(); }));
        var fin = Case("Dessin fin", _reglages.DessinFin, v =>
        {
            _reglages.DessinFin = v;
            if (_jeuEnCours != Jeu.Aucun) Arreter(""); // ce qui est posé autour de Pilou a été mesuré pour l'autre dessin
            AppliquerTaille();
        });
        fin.ToolTip = "Pilou dessiné deux fois plus fin, en pixels nets à toutes les mises à l'échelle. Décoché : le dessin d'origine.\n"
                      + MesuresDessin();
        menu.Items.Add(fin);
        menu.Items.Add(Choix("Bulle", new[] { ("Détaillée", ModeBulle.Detaillee), ("Compacte (détail au survol)", ModeBulle.Compacte), ("Seulement quand on t'attend", ModeBulle.Masquee) },
            _reglages.Bulle, v => _reglages.Bulle = v));
        menu.Items.Add(Choix("Thème de la bulle", new[] { ("Comme Windows", ThemeBulle.Auto), ("Clair", ThemeBulle.Clair), ("Sombre", ThemeBulle.Sombre) },
            _reglages.Theme, v => { _reglages.Theme = v; _themeLu = -1e9; }));
        var accessoires = new MenuItem { Header = "Accessoire" };
        foreach (var a in new[] { Accessoire.Saison, Accessoire.Aucun, Accessoire.Feuille, Accessoire.Noeud, Accessoire.Casque,
                     Accessoire.Bonnet, Accessoire.Lunettes, Accessoire.Couronne, Accessoire.ChapeauPeche, Accessoire.Toque,
                     Accessoire.Tablier, Accessoire.EtoileMer })
        {
            bool possede = a is Accessoire.Saison or Accessoire.Aucun || Possede(Recompenses.IdAccessoire(a));
            var m = new MenuItem
            {
                Header = possede ? Nom(a) : $"{Nom(a)} — boutique",
                IsCheckable = true,
                IsChecked = _reglages.Accessoire == a,
                IsEnabled = possede,
            };
            m.Click += (_, _) =>
            {
                _reglages.Accessoire = a;
                _reglages.Ecrire(_dossier);
            };
            accessoires.Items.Add(m);
        }
        menu.Items.Add(accessoires);

        // Couleur : celles qu'on possède (boutique) ; le bleu de base est toujours là.
        var couleurs = new MenuItem { Header = "Couleur" };
        var porteeCouleur = EquipeCourant().GetValueOrDefault(PilouBureau.Boutique.Couleur, "");
        var bleu = new MenuItem { Header = "Bleu ciel", IsCheckable = true, IsChecked = porteeCouleur == "" };
        bleu.Click += (_, _) => Equiper(PilouBureau.Boutique.Couleur, "");
        couleurs.Items.Add(bleu);
        foreach (var a in PilouBureau.Boutique.Catalogue.Where(a => a.Slot == PilouBureau.Boutique.Couleur && Possede(a.Id)))
        {
            var m = new MenuItem { Header = a.Nom, IsCheckable = true, IsChecked = porteeCouleur == a.Id };
            m.Click += (_, _) => Equiper(PilouBureau.Boutique.Couleur, a.Id);
            couleurs.Items.Add(m);
        }
        couleurs.Items.Add(new Separator());
        couleurs.Items.Add(Entree("D'autres couleurs à la boutique…", () => OuvrirBoutique(PilouBureau.Boutique.Couleur)));
        menu.Items.Add(couleurs);
        // Ce qu'il porte : un clic retire l'objet (parapluie compris), sans passer par la boutique.
        var portes = EquipeCourant()
            .Where(kv => kv.Value != "" && PilouBureau.Boutique.SurPilou(kv.Key) && kv.Key != PilouBureau.Boutique.Effet)
            .OrderBy(kv => kv.Key).ToList();
        if (portes.Count > 0)
        {
            var garde = new MenuItem { Header = $"Ce qu'il porte ({portes.Count})" };
            foreach (var (slot, id) in portes)
            {
                var nom = PilouBureau.Boutique.Trouver(id)?.Nom ?? id;
                garde.Items.Add(Entree($"✕ Retirer : {nom}", () => { Equiper(slot, ""); Dire($"{nom} rangé", 2500); }));
            }
            if (portes.Count > 1)
            {
                garde.Items.Add(new Separator());
                garde.Items.Add(Entree("✕ Tout retirer", () =>
                {
                    foreach (var (slot, _) in portes) Equiper(slot, "");
                    Dire("tout est rangé", 2500);
                }));
            }
            menu.Items.Add(garde);
        }
        if (Possede(PilouBureau.Boutique.TraineeEtoiles))
            menu.Items.Add(Case("Traînée d'étoiles", EquipeCourant().GetValueOrDefault(PilouBureau.Boutique.Effet) == PilouBureau.Boutique.TraineeEtoiles,
                v => Equiper(PilouBureau.Boutique.Effet, v ? PilouBureau.Boutique.TraineeEtoiles : "")));

        menu.Items.Add(MenuNiveaux());
        menu.Items.Add(MenuEvolution());
        menu.Items.Add(Case("Se promène", _reglages.Promenade, v => _reglages.Promenade = v));
        menu.Items.Add(Case("Suit la souris du regard", _reglages.SuitSouris, v => _reglages.SuitSouris = v));
        menu.Items.Add(Case("Petits jeux (de temps en temps)", _reglages.Jeux, v => _reglages.Jeux = v));
        menu.Items.Add(MenuJouer());
        foreach (var m in MenusPeche()) menu.Items.Add(m);
        menu.Items.Add(MenuExpedition());
        menu.Items.Add(new Separator());
        menu.Items.Add(Entree(string.IsNullOrWhiteSpace(_reglages.DossierPartage) ? "Partager l'XP entre PC… (choisir un dossier)" : $"XP partagée : {_reglages.DossierPartage}", ChoisirPartage));
        menu.Items.Add(Case("Démarrer avec Windows", Demarrage.Actif(), Demarrage.Regler));
        menu.Items.Add(Case("Icône près de l'horloge", _reglages.IconeNotification, v =>
        {
            _reglages.IconeNotification = v;
            if (_zoneNotif is not null) _zoneNotif.IconeVisible = v;
        }));
        menu.Items.Add(MenuQuetes());
        foreach (var m in MenusAmis()) menu.Items.Add(m);
        menu.Items.Add(MenuIntegrations());
        menu.Items.Add(MenuConnecteurs());
        menu.Items.Add(MenuActivites());
        menu.Items.Add(MenuGestes());
        menu.Items.Add(MenuVersion());
        menu.Items.Add(new Separator());
        menu.Items.Add(Entree("Se cacher 10 min", () => _cacheJusque = Maintenant + 10 * 60_000));
        menu.Items.Add(Entree("Redémarrer Pilou", Redemarrer));
        menu.Items.Add(Entree("Quitter (revient à la prochaine session)", () => Application.Current.Shutdown()));
    }

    // Dossier de partage (OneDrive commun à tes PC, partage réseau…) : chaque PC y dépose son profil.
    private void ChoisirPartage()
    {
        var d = new Microsoft.Win32.OpenFolderDialog { Title = "Dossier où partager l'XP de Pilou entre tes PC" };
        if (d.ShowDialog() != true) return;
        _reglages.DossierPartage = d.FolderName;
        _reglages.Ecrire(_dossier);
        // Ce PC apporte son profil dans le nouveau dossier (il y garde son propre fichier).
        _profil.Ecrire(DossierPartage);
        _xpTotal = TotalXp();
        Dire($"XP partagée : {_xpTotal} xp en tout", 3500);
    }

    private static MenuItem Entree(string texte, Action action)
    {
        var m = new MenuItem { Header = texte };
        m.Click += (_, _) => action();
        return m;
    }

    private MenuItem Choix<T>(string titre, (string Nom, T Valeur)[] options, T actuel, Action<T> choisir)
    {
        var parent = new MenuItem { Header = titre };
        foreach (var (nom, valeur) in options)
        {
            var m = new MenuItem { Header = nom, IsCheckable = true, IsChecked = EqualityComparer<T>.Default.Equals(valeur, actuel) };
            m.Click += (_, _) =>
            {
                choisir(valeur);
                _reglages.Ecrire(_dossier);
            };
            parent.Items.Add(m);
        }
        return parent;
    }

    private MenuItem Case(string titre, bool actuel, Action<bool> choisir)
    {
        var m = new MenuItem { Header = titre, IsCheckable = true, IsChecked = actuel };
        m.Click += (_, _) =>
        {
            choisir(m.IsChecked);
            _reglages.Ecrire(_dossier);
        };
        return m;
    }

    private void AppliquerTaille()
    {
        CalculerEchelle();
        _racine.LayoutTransform = new ScaleTransform(K, K);
        Width = LargeurBase * K;
        Height = (HauteurBulle + Scene.Hauteur) * K;
        _scene.InvalidateVisual();
    }

    // Échelle de la fenêtre et repères du dessin fin (Finesse), d'après la Taille, le réglage « Dessin fin » et la
    // mise à l'échelle de l'écran où est la fenêtre (1 = 100 % ; avant son affichage : celle du système).
    private void CalculerEchelle()
    {
        double dpi = VisualTreeHelper.GetDpi(this).DpiScaleX;
        if (!(dpi > 0)) dpi = 1;
        Finesse.Active = _reglages.DessinFin && Placement.FinPossible(_reglages.Taille, dpi);
        Finesse.Dpi = dpi;
        _k = Placement.Echelle(_reglages.Taille, dpi, _reglages.DessinFin);
        Finesse.PhysiqueParUnite = _k * dpi;
    }

    // L'écran a changé de mise à l'échelle (autre écran, réglage Windows) : l'échelle nette est recalculée.
    protected override void OnDpiChanged(DpiScale ancien, DpiScale nouveau)
    {
        base.OnDpiChanged(ancien, nouveau);
        if (_jeuEnCours != Jeu.Aucun) Arreter(""); // ce qui est posé autour de Pilou a été mesuré à l'ancienne échelle
        AppliquerTaille();
    }

    // Mesures du dessin (diagnostic) : échelle, pixels physiques par pixel fin, temps du dernier rendu, part des
    // images dont le bitmap a dû être réécrit.
    public string MesuresDessin()
    {
        int n = Finesse.Active ? Placement.PixelsParPixelFin(_reglages.Taille, Finesse.Dpi) : 0;
        string net = Finesse.Active ? $"fin, {n} px physique(s) par pixel fin, Pilou {96 * n} px de large" : "d'origine";
        return $"dessin {net} · échelle écran {Finesse.Dpi:0.##} · rendu {_scene.DernierRenduMs:0.00} ms · "
               + $"{_scene.RendusEcrits}/{_scene.Rendus} images réécrites";
    }

    // ---- Lecture des sessions et bulle

    private void Lire()
    {
        try
        {
            var etats = Suivi.LireDossier(_dossier).ToList();
            var epoque = Epoque;
            _suivi.Observer(etats, epoque);
            if (_suivi.BureauCoupe && !_devant) Application.Current.Shutdown();
            var vivantes = _suivi.Vivantes(epoque);
            _vivantes = vivantes;
            _attend = vivantes.Any(e => e.Attente != "");
            Transitions(vivantes);
            SuivreXp();
            Integrer(vivantes, epoque);
            BattreConnecteurs(vivantes, epoque);
            SuivreQuetes(vivantes);
            SuivreSoins();
            SuivreExpedition();
            SuivreCampagne(epoque);
            SuivreQuotidien();
            if (Maintenant - _themeLu > 5000)
            {
                _sombre = _reglages.Sombre();
                _themeLu = Maintenant;
            }
            Heure();
            Bulle(vivantes, epoque);
        }
        catch (IOException)
        {
            // dossier momentanément inaccessible : on garde l'état précédent
        }
    }

    // Une session vient de finir → Pilou salue ; une session se met à attendre → il sursaute.
    private void Transitions(IReadOnlyList<EtatSession> vivantes)
    {
        var t = Maintenant;
        foreach (var e in vivantes)
        {
            if (_vus.TryGetValue(e.Session, out var avant))
            {
                if (e.FinTour > avant.FinTour && !e.EnTour && e.FinRaison == "")
                {
                    Signaler("tour", 1);
                    EnergieTour();
                    _salueJusque = t + 1800;
                    _tSaut = t;
                    _dernierEvenement = t;
                }
                if (e.Attente != "" && avant.Attente == "")
                {
                    PublierSortie("⏳ Une IA t'attend", e.Claude ? "Claude Code" : "");
                    _alerteJusque = t + 5000;
                    _tSaut = t;
                    _dernierEvenement = t;
                }
                if (e.EnTour != avant.EnTour) _dernierEvenement = t;
            }
            _vus[e.Session] = (e.EnTour, e.Attente, e.FinTour);
        }
    }

    private void Peindre()
    {
        var c = Couleurs;
        bool alerte = Maintenant < _alerteJusque;
        var bord = alerte && (int)(Maintenant / 250) % 2 == 0 ? c.Orange : alerte ? c.Bleu : c.Bord;
        // Cadre de bulle acheté en boutique : bord, épaisseur, arrondi (et fond nuit pour la bulle de nuit).
        var style = PilouBureau.Boutique.Style(EquipeCourant().GetValueOrDefault(PilouBureau.Boutique.Bulle, ""));
        var fond = style?.Fond is { } f ? Pinceau(f) : c.Fond;
        if (style is not null && !alerte) bord = Pinceau(style.Bord);
        _bulle.Background = fond;
        _bulle.BorderBrush = bord;
        _bulle.BorderThickness = new Thickness(style?.Epaisseur ?? 3);
        _bulle.CornerRadius = new CornerRadius(style?.Rayon ?? 0);
        _queue.Palette = new Brush?[] { null, bord, fond };
    }

    // Ce qui change quand il se passe quelque chose de nouveau dans la session (l'outil en cours, non).
    private static string Signature(EtatSession e) => $"{e.Attente}|{e.EnTour}|{e.DebutTour}|{e.FinTour}|{e.FinRaison}";

    private void ToutLu()
    {
        foreach (var e in _vivantes) _lus[e.Session] = Signature(e);
        _notifs.Vider();
        _survol = false;
        _alerteJusque = -1e9;
        Bulle(_vivantes, Epoque);
    }

    private void Bulle(IReadOnlyList<EtatSession> vivantes, double epoque)
    {
        // Au survol : tout. Sinon : seulement les sessions où il s'est passé quelque chose depuis le dernier « lu ».
        var nonLues = _survol ? vivantes : vivantes.Where(e => !_lus.TryGetValue(e.Session, out var sig) || sig != Signature(e)).ToList();
        var (toutes, autres) = Statut.Lignes(nonLues, epoque, _image0++);
        var resume = Statut.Resumer(vivantes, epoque);
        bool detail = _reglages.Bulle == ModeBulle.Detaillee || _survol;
        var urgentes = toutes.Where(l => l.Ton == Ton.Attente || l.Nouveau).ToList();
        var lignes = detail ? toutes : urgentes;

        _lignes.Children.Clear();
        if (Maintenant < _messageJusque)
            _lignes.Children.Add(new TextBlock
            {
                Tag = _messageTag == "" ? null : _messageTag,
                Text = _message,
                FontFamily = new FontFamily("Segoe UI"),
                FontSize = 12.5,
                FontStyle = FontStyles.Italic,
                Foreground = Couleurs.Texte,
                Margin = new Thickness(0, 1, 0, 1),
            });
        if (BlocDiagnostics() is { } diag) _lignes.Children.Add(diag);
        foreach (var l in lignes) _lignes.Children.Add(Ligne(l));
        if (detail && autres > 0)
            _lignes.Children.Add(Discret($"+ {autres} autre{(autres > 1 ? "s" : "")} session{(autres > 1 ? "s" : "")} au calme"));
        var texteResume = Statut.TexteResume(resume);
        if (!detail && _reglages.Bulle == ModeBulle.Compacte && nonLues.Count > 0 && texteResume != "")
            _lignes.Children.Add(Discret(texteResume));
        if (_survol && toutes.Count == 0)
            _lignes.Children.Add(Discret(vivantes.Count == 0 ? "aucune session ouverte" : "rien en cours"));
        // En route pour sa campagne : une ligne discrète, sous les sessions (elles passent d'abord).
        LignesCampagne();

        // Parti chez un ami : une ligne dit où il est et quand il revient ; les sessions restent au-dessous.
        if (LigneVisite() is { Length: > 0 } visite) _lignes.Children.Insert(Maintenant < _messageJusque ? 1 : 0, Discret(visite));
        // En expédition : pareil, une ligne (où, retour vers…), les sessions restent au-dessous.
        if (LigneExpedition() is { Length: > 0 } exp) _lignes.Children.Insert(Maintenant < _messageJusque ? 1 : 0, Discret(exp));
        // Notification Windows (désactivé par défaut) : tout en haut, quelques secondes.
        if (BlocNotif() is { } notif) _lignes.Children.Insert(0, notif);
        bool visible = _lignes.Children.Count > 0;
        _pileBulle.Visibility = visible ? Visibility.Visible : Visibility.Hidden;
        Peindre();
    }

    // Pilou parle : une phrase en italique en tête de bulle, quelques secondes.
    private void Dire(string texte, double ms = 3500)
    {
        _message = texte;
        _messageTag = "";
        _messageJusque = Maintenant + ms;
        Bulle(_vivantes, Epoque);
    }

    // Tout premier lancement : un mot de bienvenue, une seule fois (noté aussitôt dans reglages.json).
    private void Bienvenue()
    {
        if (_demo || _reglages.BienvenueFaite) return;
        _reglages.BienvenueFaite = true;
        _reglages.Ecrire(_dossier);
        var t = new DispatcherTimer(DispatcherPriority.Background, Dispatcher) { Interval = TimeSpan.FromSeconds(4) };
        t.Tick += (_, _) =>
        {
            t.Stop();
            Dosage.Noter(Maintenant);
            Dire(Reglages.MotBienvenue, 9000);
        };
        t.Start();
    }

    // Phrase liée à l'heure, une fois par jour. Le bonjour, le lundi, le vendredi et le soir sont devenus les petits mots
    // de la présence au quotidien (FenetrePresence.cs) : au plus trois par jour, aux moments calmes.
    private void Heure()
    {
        var n = DateTime.Now;
        string jour = n.ToString("yyyyMMdd");
        void Une(string cle, bool quand, string texte)
        {
            if (_demo || CampagneOccupe || !quand || _dit.Contains($"{cle}-{jour}") || !Dosage.Libre(Maintenant, EnSaisie)) return;
            if (!PresenceCoupee && _presence is { Parle: "jamais" }) return;
            _dit.Add($"{cle}-{jour}");
            Dosage.Noter(Maintenant);
            Dire(texte, 6000);
        }
        Une("midi", n.Hour == 12 && n.Minute < 20, "bon appétit !");
    }

    private TextBlock Discret(string texte) => new()
    {
        Text = texte,
        FontFamily = new FontFamily("Segoe UI"),
        FontSize = 11.5,
        Foreground = Couleurs.Pale,
        Margin = new Thickness(0, 1, 0, 1),
    };

    private TextBlock Ligne(LigneStatut l)
    {
        var c = Couleurs;
        var signe = l.Ton switch { Ton.Attente => c.Orange, Ton.Travail => c.Bleu, _ => l.Nouveau ? c.Bleu : c.Pale };
        var tb = new TextBlock
        {
            FontFamily = new FontFamily("Segoe UI"),
            FontSize = 12.5,
            Foreground = c.Texte,
            TextTrimming = TextTrimming.CharacterEllipsis,
            Margin = new Thickness(0, 1, 0, 1),
        };
        tb.Inlines.Add(new Run(l.Signe) { Foreground = signe, FontWeight = FontWeights.Bold, FontFamily = new FontFamily("Segoe UI Symbol") });
        tb.Inlines.Add(new Run(" "));
        if (l.Libelle != "")
        {
            tb.Inlines.Add(new Run(l.Libelle) { FontWeight = FontWeights.SemiBold });
            tb.Inlines.Add(new Run("  "));
        }
        tb.Inlines.Add(new Run(l.Texte)
        {
            Foreground = l.Ton == Ton.Attente ? c.Orange : l.Nouveau ? c.Bleu : c.Pale,
            FontWeight = l.Ton == Ton.Attente || l.Nouveau ? FontWeights.SemiBold : FontWeights.Normal,
        });
        return tb;
    }

    // ---- Placement

    private void Placer(bool aGauche)
    {
        _aGauche = aGauche;
        var cote = aGauche ? HorizontalAlignment.Left : HorizontalAlignment.Right;
        _scene.HorizontalAlignment = cote;
        _pileBulle.HorizontalAlignment = cote;
        _queue.HorizontalAlignment = cote;
        double marge = Scene.Largeur / 2 - 12;
        _queue.Margin = aGauche ? new Thickness(marge, -6, 0, 0) : new Thickness(0, -6, marge, 0);
    }

    private double PiedsDansFenetre => Placement.PiedsDansFenetre(_aGauche, K);

    private Matrix VersWpf => PresentationSource.FromVisual(this)?.CompositionTarget?.TransformFromDevice ?? Matrix.Identity;
    private Matrix VersEcran => PresentationSource.FromVisual(this)?.CompositionTarget?.TransformToDevice ?? Matrix.Identity;

    private Rect ZoneSous(double x, double y)
    {
        var p = VersEcran.Transform(new Point(x, y));
        var r = Natif.ZoneTravail((int)p.X, (int)p.Y);
        SolDuDecor(ref r, (int)p.X, (int)p.Y); // tournage : la fausse barre des tâches (FenetreVisite.cs)
        var m = VersWpf;
        return new Rect(m.Transform(new Point(r.Left, r.Top)), m.Transform(new Point(r.Right, r.Bottom)));
    }

    private void PlacerAuDepart()
    {
        if (PlacerSurDemande()) return; // --ecran= / --placer= (FenetreVisite.cs)
        var claude = Natif.TrouverClaude();
        if (claude != IntPtr.Zero && Natif.Cadre(claude) is { } c)
        {
            var centre = VersWpf.Transform(new Point((c.Left + c.Right) / 2.0, (c.Top + c.Bottom) / 2.0));
            _zone = ZoneSous(centre.X, centre.Y);
        }
        else _zone = ZoneSous(10, 10);
        _x = _zone.Right - Scene.Largeur / 2 * K - 30;
        _yPieds = _zone.Bottom;
        _cible = _x;
        _zoneConnue = true;
    }

    // ---- Animation

    private void Image()
    {
        var t = Maintenant;
        double dt = Math.Clamp((t - _dernierT) / 1000.0, 0, 0.1);
        _dernierT = t;
        if (_nous == IntPtr.Zero) return;
        if (!_zoneConnue) PlacerAuDepart();
        // Caché : à la demande (10 min), ou par discrétion (plein écran, présentation, visio — Activites.Discretion).
        if (t < _cacheJusque || (_discret && t >= _ramenePlusQueDiscretJusque))
        {
            if (IsVisible) Hide();
            if (_invite is { IsVisible: true }) _invite.Hide();
            return;
        }
        if (!IsVisible) Show();

        var epoque = Epoque;
        var expr = _suivi.Expression(epoque, _tCaresse == -1e9 ? -1e12 : epoque - (t - _tCaresse));
        if (_attend && expr is not Expr.Caresse) expr = Expr.Inquiet;
        bool fatigue = (_suivi.Courant?.Fatigue ?? false) || TenueAffichee == "nuit";
        _inactif = Natif.InactifMs();
        Observer(t);
        expr = Sommeil(expr, t);
        expr = NuitTardive(expr, t);
        var stadePose = _essaiStade > 0 ? _essaiStade : StadeAffiche();
        var (objetsSoins, boude, dosTourne) = PoseSoins(stadePose, t);
        _exprCourante = expr;
        // En visite (chez un ami, ou un ami chez lui) ou en expédition, pas de petit jeu ni d'occupation tout seul.
        if (!_visites.Occupe && !EnExpedition && !CampagneOccupe)
        {
            ProposerJeu(t, expr);
            OccuperSeul(t, expr);
        }

        // Pendant une visite ou une expédition, l'écran reste celui du départ (sinon, passé le bord, l'écran voisin
        // deviendrait le sien : sortie recalculée en route, pancarte posée sur l'autre écran).
        if (!_attrape && _auSol) _zone = ZoneSous(XEcran, _zone.Bottom - 10);
        double sol = _zone.Bottom;
        var (min, max) = Placement.BornesPieds(_zone.Left, _zone.Right, K);

        bool marche = false;
        if (_attrape)
        {
            _geste = Geste.Rien;
        }
        else if (_geste == Geste.SauteSouris)
        {
            SauterSouris(t);
        }
        else if (!_auSol)
        {
            _vy += 2600 * dt;
            _yPieds += _vy * dt;
            if (_yPieds >= sol)
            {
                _yPieds = sol;
                if (_vy > 380) _vy = -_vy * 0.32;
                else
                {
                    _vy = 0;
                    _auSol = true;
                }
                _atterri = t;
            }
        }
        else if (VisiteBouge(dt, out var enRoute) || ExpeditionBouge(dt, out enRoute))
        {
            _yPieds = sol;
            marche = enRoute;
        }
        else
        {
            _yPieds = sol;
            _x = Math.Clamp(_x, min, max);
            // Au clavier ou l'appareil photo en main, il reste sur place.
            // En route pour sa campagne, il reste à sa place (sa tenue de voyage l'anime sur place) ; une IA qui
            // t'attend le fait quand même courir sous la souris.
            if (GesteEnCours || CampagneOccupe) _geste = Geste.Rien;
            marche = MarcheVisite(dt, min, max) || Courir(t, dt, min, max)
                     || (_jeuEnCours == Jeu.Aucun && !_dortBureau && !GesteEnCours && !CampagneOccupe && Gestes(expr, fatigue, t, dt, min, max));
        }

        // Assis : on s'y pose et on s'en relève en douceur.
        double viseAssis = _geste == Geste.Assis || _dortBureau ? 1 : 0;
        _assis += Math.Clamp(viseAssis - _assis, -4 * dt, 4 * dt);

        if (t >= _clignePlus)
        {
            _cligneFin = t + 150;
            _clignePlus = t + 2500 + _hasard.NextDouble() * 4000;
        }
        if (t >= _regardPlus)
        {
            _regard = _hasard.Next(-1, 2);
            _regardPlus = t + 1800 + _hasard.NextDouble() * 3500;
            if (expr == Expr.Repos && _hasard.NextDouble() < 0.1) _clinFin = t + 450;
        }
        var (rx, ry) = RegardSouris(expr, marche);
        if (_geste == Geste.Ballon) rx = _sens;
        if (_jeuEnCours is Jeu.Peche or Jeu.Cuisine) rx = CoteJeu;

        // Accroché au curseur, posé sur l'écran pour toquer, ou caressé par la souris qui s'attarde.
        double suspendu = _geste == Geste.SauteSouris && t - _sautDebut > 700 ? 1 : 0;
        double phaseToque = (t - _toqueDebut) / 1600;
        bool toque = phaseToque is >= 0 and < 1;
        bool ronron = _survolSceneDebut >= 0 && t - _survolSceneDebut > 1500 && _appui is null;
        bool etourdi = t < _etourdiJusque;
        var montre = _attrape ? Expr.Inquiet : _geste == Geste.SauteSouris ? Expr.Fete : ronron ? Expr.Caresse : ExprJeu(expr, t);

        double depuis = _suivi.DepuisHumeur(epoque);
        // Sauts, ressorts et réception d'une chute (VieFenetre.cs) : forme selon le réglage ✧.
        string niveauVie = NiveauVie;
        var mouvement = Bondir(expr, t, depuis, niveauVie);
        if (_attrape) mouvement = mouvement with { Saut = 0, Etire = 0, Antenne = 0 };
        double saut = mouvement.Saut;

        // Météo vécue : gouttes, flocons, soleil ; mouillé ou gelé sans l'équipement, il frissonne et grimace.
        var meteo = EffetMeteoCourant(t);
        // Une grimace 6 s sur 30 (au lieu de 6 sur 18), comme sur le téléphone (Meteo.java).
        if (meteo.Inconfort is "mouille" or "froid" && montre == Expr.Repos && (int)(t / Meteo.PeriodeGrimace) % Meteo.CycleGrimace == 0) montre = Expr.Grimace;
        montre = ExprDiagnostics(montre, t);
        _scene.Pose = new Pose
        {
            Meteo = meteo.Sprites,
            Expr = montre,
            T = t,
            Depuis = ronron ? t - _survolSceneDebut : expr == Expr.Caresse ? t - _tCaresse : depuis,
            Regard = rx,
            RegardY = ry,
            Cligne = t < _cligneFin,
            Clin = t < _clinFin,
            Fatigue = fatigue,
            Marche = marche,
            Course = _court,
            Saut = saut,
            Tremble = suspendu > 0 ? Math.Sin(t / 70.0) * 0.5
                : etourdi ? Math.Sin(t / 120.0) * 0.4
                : expr == Expr.Grimace && depuis < 900 ? ((int)(t / 70) % 2 == 0 ? 0.6 : -0.6)
                : Balancement(t) + meteo.Tremble,
            Chute = mouvement.Chute,
            Assis = _assis,
            Baille = _geste == Geste.Baille && expr == Expr.Repos,
            Salue = t < _salueJusque,
            Accessoire = _reglages.Porte(DateTime.Now, a => Possede(Recompenses.IdAccessoire(a))),
            Equipe = EquipeEssai(EquipeCourant()),
            Stade = stadePose,
            Evolution = ProgresEvolution(t),
            Couleur = Recompenses.CouleurDe(EquipeCourant().GetValueOrDefault(PilouBureau.Boutique.Couleur, "")) ?? Couleur.Bleu,
            Trainee = EquipeCourant().GetValueOrDefault(PilouBureau.Boutique.Effet) == PilouBureau.Boutique.TraineeEtoiles,
            Etourdi = etourdi,
            Zoom = toque ? 1 + 0.38 * Math.Sin(Math.PI * Math.Min(1, phaseToque * 1.15)) : 1,
            Toque = toque && phaseToque > 0.2 ? (phaseToque - 0.2) / 0.8 : 0,
            Suspendu = suspendu,
            Balle = _geste == Geste.Ballon,
            BalleX = _balleX,
            BalleRot = _balleRot,
            Tenue = _essaiTenue != "" ? _essaiTenue : TenueAffichee,
            Humeur = _essaiHumeur,
            Reaction = ReactionAffichee != "" ? ReactionAffichee : meteo.Reaction,
            Soins = objetsSoins,
            // Il boude : moue et sourcils au repos ; dos tourné seulement immobile, au repos et sans jeu en cours.
            Boude = boude && montre == Expr.Repos,
            Dos = dosTourne && montre == Expr.Repos && !marche && _jeuEnCours == Jeu.Aucun && !_attrape,
        };
        HabillerVisite(_scene.Pose, t);
        HabillerExpedition(_scene.Pose, t);
        HabillerGestes(_scene.Pose, t);
        HabillerCampagne(_scene.Pose);
        HabillerVie(_scene.Pose, mouvement, niveauVie);
        _scene.InvalidateVisual();
        AnimerInvite(t);
        AnimerJeux(t);
        AnimerSoins(t);
        AnimerBoutique(t);
        AnimerExpedition(t);
        AnimerRetour(t);
        AnimerEssaiVie(t);
        if (t < _alerteJusque) Peindre();

        bool gauche = Placement.AGauche(_x, _zone.Left, _zone.Right);
        // Côté changé en plein jeu (Pilou lâché de l'autre côté) : l'eau, la marmite… étaient posées de l'autre côté.
        if (gauche != _aGauche && !_attrape)
        {
            if (_jeuEnCours != Jeu.Aucun) Arreter("");
            Placer(gauche);
        }
        // Dessin fin : la fenêtre se pose sur un pixel physique entier, même en marchant.
        double gaucheFenetre = Placement.GaucheFenetre(_x, _aGauche, K), haut = Placement.HautFenetre(_yPieds, K);
        Left = Finesse.Active ? Placement.Aligner(gaucheFenetre, Finesse.Dpi) : gaucheFenetre;
        Top = Finesse.Active ? Placement.Aligner(haut, Finesse.Dpi) : haut;
        Borner();
    }

    // Ce qui déborde de l'écran courant (un écran voisin, à gauche en X négatif, ou rien) est découpé : la bulle
    // se resserre, et Pilou qui part par le bord disparaît au bord au lieu de réapparaître sur l'écran d'à côté.
    private (double X0, double X1) _visible = (0, LargeurBase);
    private bool _visibleAGauche;

    private void Borner()
    {
        var v = Placement.Visible(Left, K, _zone.Left, _zone.Right);
        if (v == _visible && _aGauche == _visibleAGauche) return;
        _visibleAGauche = _aGauche;
        _visible = v;
        _racine.Clip = v == (0, LargeurBase) ? null : new RectangleGeometry(new Rect(v.X0, -4000, v.X1 - v.X0, 8000));
        _bulle.MaxWidth = Placement.LargeurBulle(_aGauche, v);
    }

    // Claude t'attend (et ce n'est pas encore « lu ») : Pilou court se placer sous la souris,
    // sur l'horizontale, et la suit tant que personne ne répond. Renvoie s'il court.
    private bool Courir(double t, double dt, double min, double max)
    {
        _court = false;
        bool appel = _vivantes.Any(e => e.Attente != "" && (!_lus.TryGetValue(e.Session, out var sig) || sig != Signature(e)));
        if (!appel) return false;
        if (_jeuEnCours != Jeu.Aucun) Arreter("");
        var (sx, sy) = Natif.Souris();
        if (sx == int.MinValue) return false;
        double cible = Math.Clamp(VersWpf.Transform(new Point(sx, sy)).X, min, max);
        double ecart = cible - _x;
        _geste = Geste.Rien;
        if (Math.Abs(ecart) < 6 * K)
        {
            // Arrivé sous la souris : il sautille pour se faire voir ; sans réaction depuis 45 s, il toque à l'écran.
            if (_inactif > 45_000)
            {
                if (t - _toqueDebut > 7000)
                {
                    _toqueDebut = t;
                    Dire("toc toc ! Claude t'attend", 2800);
                }
            }
            else if (t - _tSaut > 1400) _tSaut = t;
            return false;
        }
        _sens = Math.Sign(ecart);
        double vitesse = Math.Min(320, 90 + Math.Abs(ecart) * 1.5) * K;
        _x += _sens * Math.Min(Math.Abs(ecart), vitesse * dt);
        _court = true;
        return true;
    }

    // Petite vie au repos : marcher, s'asseoir, bâiller, ne rien faire. Renvoie s'il marche.
    // Pendant que tu travailles (Vivacite.AuTravail), il bouge moins : pauses deux fois plus longues, petits pas
    // plus lents et plus courts, pas de ballon ni de sautillement ; il préfère rester assis.
    private bool Gestes(Expr expr, bool fatigue, double t, double dt, double min, double max)
    {
        bool calme = expr is Expr.Repos;
        bool travail = AuTravail;
        double pause = travail ? 2 : 1.3;
        bool assisPermis = expr is Expr.Repos or Expr.Concentre or Expr.Attente;
        if (!assisPermis || (_geste is Geste.Marche or Geste.Baille or Geste.Ballon && !calme)) _geste = Geste.Rien;

        switch (_geste)
        {
            case Geste.Marche:
            {
                double ecart = _cible - _x;
                if (Math.Abs(ecart) < 2)
                {
                    _geste = Geste.Rien;
                    _pauseJusque = t + (2500 + _hasard.NextDouble() * 6000) * pause;
                    return false;
                }
                _sens = Math.Sign(ecart);
                double vitesse = (fatigue || _boudeur ? 26 : 40) * (travail ? 0.75 : 1); // fatigué ou boudeur : il traîne les pieds
                _x += _sens * Math.Min(Math.Abs(ecart), vitesse * dt * K);
                return true;
            }
            case Geste.Ballon:
            {
                if (t >= _gesteFin)
                {
                    _geste = Geste.Rien;
                    _pauseJusque = t + (3000 + _hasard.NextDouble() * 4000) * pause;
                    return false;
                }
                double ecart = _cible - _x;
                if (Math.Abs(ecart) < 4)
                {
                    _cible = Math.Clamp(_x + (_hasard.NextDouble() < 0.5 ? -1 : 1) * (120 + _hasard.NextDouble() * 160) * K, min, max);
                    return false;
                }
                _sens = Math.Sign(ecart);
                double v = 34 * K;
                _x += _sens * Math.Min(Math.Abs(ecart), v * dt);
                // La balle roule devant lui ; de temps en temps, un petit coup de pied l'envoie plus loin.
                if (t - _balleKick > 2600 && _hasard.NextDouble() < 0.02) _balleKick = t;
                double coup = t - _balleKick < 700 ? Math.Sin(Math.PI * (t - _balleKick) / 700) * 7 : 0;
                double vise = _sens * (8 + coup);
                _balleX += Math.Clamp(vise - _balleX, -30 * dt, 30 * dt);
                _balleRot += _sens * (v * dt + (coup > 0 ? 4 * dt * K : 0)) / (2.2 * Scene.PA * K);
                return true;
            }
            case Geste.Assis or Geste.Baille when t >= _gesteFin:
                _geste = Geste.Rien;
                _pauseJusque = t + (2000 + _hasard.NextDouble() * 5000) * pause;
                return false;
            case Geste.Rien when t >= _pauseJusque && calme:
            {
                double ennui = t - _dernierEvenement;
                double tirage = _hasard.NextDouble();
                if (_inactif > 180_000 && _hasard.NextDouble() < 0.35 && PreparerSaut(t))
                    return false;
                if (_reglages.Promenade && !travail && ennui > 60_000 && _hasard.NextDouble() < 0.12)
                {
                    _geste = Geste.Ballon;
                    _gesteFin = t + 9000 + _hasard.NextDouble() * 8000;
                    _cible = Math.Clamp(_x + (_hasard.NextDouble() < 0.5 ? -1 : 1) * 200 * K, min, max);
                    _balleX = 0;
                    return false;
                }
                if (tirage < 0.12 && (fatigue || ennui > 180_000))
                {
                    _geste = Geste.Baille;
                    _gesteFin = t + 1700;
                }
                else if (tirage < (travail ? 0.55 : 0.40))
                {
                    _geste = Geste.Assis;
                    _gesteFin = t + 6000 + _hasard.NextDouble() * 12000;
                }
                else if (tirage < 0.88 && _reglages.Promenade)
                {
                    _geste = Geste.Marche;
                    _cible = Math.Clamp(_x + (_hasard.NextDouble() * 2 - 1) * (travail ? 120 : 240) * K, min, max);
                }
                else
                {
                    if (!travail) _tSaut = t; // un petit sautillement, seulement quand tu ne travailles pas
                    _pauseJusque = t + (3000 + _hasard.NextDouble() * 5000) * pause;
                }
                return false;
            }
            default:
                return false;
        }
    }

    // Ce que fait la souris autour de lui : secousse (étourdi), survol prolongé (ronron).
    private void Observer(double t)
    {
        var (sx, sy) = Natif.Souris();
        if (sx == int.MinValue) return;
        _souris = VersWpf.Transform(new Point(sx, sy));
        _trace.Enqueue((t, _souris));
        while (_trace.Count > 0 && t - _trace.Peek().T > 700) _trace.Dequeue();
        double chemin = 0;
        Point? avant = null;
        foreach (var (_, pt) in _trace)
        {
            // Un saut de plus de 400 px d'une image à l'autre est une téléportation (premier relevé, autre écran), pas une secousse.
            if (avant is { } a && (pt - a).Length < 400) chemin += (pt - a).Length;
            avant = pt;
        }
        if (_trace.Count < 8) chemin = 0;
        double dx = _souris.X - _x, dy = _souris.Y - (_yPieds - 10 * Scene.PA * K);
        bool pres = Math.Abs(dx) < 380 && Math.Abs(dy) < 380;
        // Souris secouée près de lui : la tête lui tourne, mais pas à chaque fois (souvent, c'est juste du travail).
        if (pres && chemin > 1700 && t > _etourdiJusque + 3000 && _geste != Geste.SauteSouris && !_attrape && !CampagneOccupe)
        {
            if (Dosage.Tenter(t, EnSaisie))
            {
                _etourdiJusque = t + 2800;
                Dire("ouh, la tête me tourne…", 2800);
            }
            else _etourdiJusque = t; // occasion manquée : pas de nouveau tirage avant 3 s
        }
        if (_scene.IsMouseOver && !_attrape)
        {
            if (_survolSceneDebut < 0) _survolSceneDebut = t;
            if (!_ronronDit && t - _survolSceneDebut > 1500 && !CampagneOccupe)
            {
                _ronronDit = true;
                Dire("rrr…", 1800);
            }
        }
        else
        {
            _survolSceneDebut = -1;
            _ronronDit = false;
        }
    }

    // Plus personne ne bouge depuis 3 min : Pilou saute s'accrocher au curseur par l'antenne.
    private bool PreparerSaut(double t)
    {
        var pieds = new Point(_souris.X, _souris.Y + 21 * Scene.PA * K);
        // Le curseur doit être au-dessus de lui, sur son écran, et pas trop loin.
        if (pieds.Y > _zone.Bottom - 80 || pieds.Y < _zone.Top + 40) return false;
        if (_souris.X < _zone.Left || _souris.X > _zone.Right || Math.Abs(_souris.X - _x) > 900) return false;
        _geste = Geste.SauteSouris;
        _sautDebut = t;
        _sautDepart = new Point(_x, _yPieds);
        _sautCible = pieds;
        _sens = Math.Sign(_souris.X - _x);
        Dire("je l'attrape !", 1800);
        return true;
    }

    private void SauterSouris(double t)
    {
        double a = (t - _sautDebut) / 700;
        if (a < 1)
        {
            // Bond en cloche jusqu'au curseur.
            double haut = Math.Min(140, Math.Abs(_sautDepart.Y - _sautCible.Y) * 0.3 + 50) * K;
            _x = _sautDepart.X + (_sautCible.X - _sautDepart.X) * a;
            _yPieds = _sautDepart.Y + (_sautCible.Y - _sautDepart.Y) * a - Math.Sin(Math.PI * a) * haut;
            return;
        }
        // Accroché : il gigote. Si la souris repart (on est revenu) ou au bout de 2,6 s, il lâche.
        var pieds = new Point(_souris.X, _souris.Y + 21 * Scene.PA * K);
        bool bouge = (pieds - _sautCible).Length > 25;
        _x = _sautCible.X;
        _yPieds = _sautCible.Y;
        if (bouge || t - _sautDebut > 700 + 2600)
        {
            _geste = Geste.Rien;
            _auSol = false;
            _vy = 0;
            _pauseJusque = t + 5000;
            if (!bouge) Dire("elle est trop lourde…", 2400);
        }
    }

    // Le regard suit la souris quand elle passe près de Pilou.
    private (int X, int Y) RegardSouris(Expr expr, bool marche)
    {
        if (marche) return (_sens, 0);
        if (expr is not (Expr.Repos or Expr.Inquiet or Expr.Attente)) return (0, 0);
        if (!_reglages.SuitSouris) return (expr == Expr.Attente ? 0 : _regard, 0);
        var (sx, sy) = Natif.Souris();
        if (sx == int.MinValue) return (_regard, 0);
        var souris = VersWpf.Transform(new Point(sx, sy));
        double dx = souris.X - _x, dy = souris.Y - (_yPieds - 12 * Scene.PA * K);
        if (Math.Abs(dx) > 520 || Math.Abs(dy) > 420) return (expr == Expr.Attente ? 0 : _regard, 0);
        return (Math.Abs(dx) < 22 * K ? 0 : Math.Sign(dx), dy < -50 * K ? -1 : dy > 40 * K ? 1 : 0);
    }

    // Essai sans écran : ce que dessine la fenêtre, enregistré en PNG (fond transparent).
    public void Instantane(string chemin)
    {
        var rendu = new System.Windows.Media.Imaging.RenderTargetBitmap(
            (int)Math.Ceiling(Width), (int)Math.Ceiling(Height), 96, 96, PixelFormats.Pbgra32);
        rendu.Render(_racine);
        var png = new System.Windows.Media.Imaging.PngBitmapEncoder();
        png.Frames.Add(System.Windows.Media.Imaging.BitmapFrame.Create(rendu));
        using var f = File.Create(chemin);
        png.Save(f);
    }

    // ---- Souris sur Pilou

    private void Caresser()
    {
        Signaler("caresse", 1);
        SoinCaresse();
        Vecu(f => f.Ca++, "caresses");
        _tCaresse = Maintenant;
        _geste = Geste.Rien;
        try
        {
            Directory.CreateDirectory(_dossier);
            var chemin = System.IO.Path.Combine(_dossier, "caresses.txt");
            int n = File.Exists(chemin) && int.TryParse(File.ReadAllText(chemin).Trim(), out var v) ? v : 0;
            File.WriteAllText(chemin, (n + 1).ToString());
        }
        catch (IOException)
        {
            // la caresse reste locale
        }
    }

    private void Appui(object sender, MouseButtonEventArgs e)
    {
        // Parti en visite : la pancarte ne se déplace pas ; un clic dessus rappelle Pilou.
        if (_visites.Sortie is not null)
        {
            _appuiPancarte = true;
            e.Handled = true;
            return;
        }
        // En expédition : la pancarte ne bouge pas non plus ; un clic montre où il est.
        if (EnExpedition)
        {
            _expAppui = true;
            e.Handled = true;
            return;
        }
        _appui = PointToScreen(e.GetPosition(this));
        _appuiT = Maintenant;
        var souris = VersWpf.Transform(_appui.Value);
        _prise = new Vector(souris.X - _x, souris.Y - _yPieds);
        _scene.CaptureMouse();
        e.Handled = true;
    }

    private void Bouge(object sender, MouseEventArgs e)
    {
        if (_appui is not { } depart) return;
        var ecran = PointToScreen(e.GetPosition(this));
        var dip = VersWpf.Transform(ecran);
        // Un clic dont la main tremble un peu reste un clic (caresse, coup de jeu) : seuil en unités WPF (Clics.EstGlisser).
        if (!_attrape && Clics.EstGlisser((dip - VersWpf.Transform(depart)).Length, Maintenant - _appuiT)) _attrape = true;
        if (!_attrape) return;
        _x = dip.X - _prise.X;
        _yPieds = dip.Y - _prise.Y;
        _auSol = false;
        _vy = 0;
    }

    private void Relache(object sender, MouseButtonEventArgs e)
    {
        _scene.ReleaseMouseCapture();
        if (_appuiPancarte)
        {
            _appuiPancarte = false;
            Rappeler();
            e.Handled = true;
            return;
        }
        if (_expAppui)
        {
            _expAppui = false;
            if (ExpeditionAbsent) OuvrirExpeditions(false);
            e.Handled = true;
            return;
        }
        if (!_attrape && _appui is not null)
        {
            // Pendant tape m'en cinq, la pêche ou la cuisine, un clic sur Pilou joue (jugé à l'instant de l'appui).
            // Il t'attend pour son aventure : un clic sur lui ouvre la fenêtre (sinon, c'est une caresse).
            if (!ClicJeuSurPilou(_appuiT))
            {
                if (_retour.Signe) OuvrirAventure();
                else Caresser();
            }
            ToutLu();
        }
        if (_attrape)
        {
            _attrape = false;
            _zone = ZoneSous(_x, _yPieds);
            _cible = _x;
            _pauseJusque = Maintenant + 4000;
        }
        _appui = null;
        e.Handled = true;
    }
}
