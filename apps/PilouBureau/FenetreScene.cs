using System.Diagnostics;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Threading;

namespace PilouBureau;

// Une scène d'évolution (docs/SCENES.md, « Scènes d'évolution ») : Pilou raconte au fond du jardin, devant son
// pot-cabane, ce qui vient de lui arriver. Le théâtre (VueTheatre) en haut, la boîte de dialogue dessous : chaque
// réplique s'écrit lettre à lettre (Evolutions.MsEcriture) pendant qu'il parle ; un clic ou Espace passe à la suite.
// Un seul choix (1 à 3 au clavier) : ce qu'il garde de son ancienne forme. Ouverte seulement par le joueur (la bulle
// d'annonce, le Carnet), jamais d'elle-même.
internal sealed class FenetreScene : Window
{
    private static readonly Brush Fond = FenetreAventure.Gel("#0f1324");

    private readonly Evolutions.Scene _sc;
    private readonly string _variante;
    private readonly Action<string>? _garder;
    private readonly VueTheatre _theatre;
    private readonly Stopwatch _chrono = Stopwatch.StartNew();
    private readonly DispatcherTimer _minuterie;
    private readonly TextePixel _replique = new("", CadrePixel.Texte) { Taille = 2 };
    private readonly TextePixel _suite = new("▼", CadrePixel.Titre) { Taille = 2 };
    private readonly StackPanel _options = new() { Margin = new Thickness(0, 10, 0, 0) };
    private readonly CadrePixel _boite;
    private List<Evolutions.Replique> _lignes;
    private int _i = -1;
    private double _debut, _fin;
    private bool _choisi, _termine;

    public double T => _chrono.Elapsed.TotalMilliseconds;

    public FenetreScene(FenetrePilou pilou, Evolutions.Scene sc, string variante, Action<string>? garder)
    {
        _sc = sc;
        _variante = Evolutions.Variante(variante);
        _garder = garder;
        _lignes = Evolutions.Deroule(sc, _variante, null);
        Title = "Pilou · " + sc.Titre;
        // La scène à ×4 (768 × 320) : la fenêtre tient sur un écran de portable à 125 % ; sa taille ne bouge pas d'une
        // réplique à l'autre (la boîte prend la place qui reste).
        Width = 830;
        Height = 640;
        ResizeMode = ResizeMode.CanMinimize;
        WindowStartupLocation = WindowStartupLocation.CenterScreen;
        Background = Fond;
        UseLayoutRounding = true;
        SnapsToDevicePixels = true;
        ShowInTaskbar = true;
        // Habillage maison : pas de barre de titre Windows (claire, système) au-dessus du pixel sombre ; la tête de la
        // fenêtre est dessinée ici (titre, ✕), on la déplace en la tirant, Échap ferme.
        WindowStyle = WindowStyle.None;
        ResizeMode = ResizeMode.NoResize;
        BorderBrush = Bandeau.Bord;
        BorderThickness = new Thickness(2);

        _theatre = new VueTheatre(() => AnimationsCampagne.Niveau(pilou.AnimationsCampagnes, Bandeau.Anime),
            () => RenduPilou.Teinte(pilou.AllurePortrait("repos", 0), Banque.Commune));
        // En HD, Pilou entre de près (x 150) : il est à sa place (250) quand la métamorphose commence.
        _theatre.Lieu("evolution", sc.Decor, 0, glisser: false, entree: TheatreHd.ScenesHd("evolution").ContainsKey(sc.Decor) ? 150 : 0);
        if (_theatre.Hd)
        {
            // Le fond du jardin en HD (480 × 240 à ×2) : la fenêtre s'élargit, sans jamais dépasser la zone de travail.
            _theatre.Ajuster(Theatre.Hd.W * 2, Theatre.Hd.H * 2);
            var zone = FenetreAventure.ZoneTravail();
            Width = Math.Min(Theatre.Hd.W * 2 + 44, zone.Width);
            Height = Math.Min(800, zone.Height);
        }
        else _theatre.Ajuster(Theatre.W * 4, Theatre.H * 4);

        var racine = new Grid { Margin = new Thickness(18, 12, 18, 14) };
        racine.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        racine.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        racine.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });

        var tete = new Grid { Margin = new Thickness(0, 0, 0, 10), Background = Brushes.Transparent, Cursor = Cursors.SizeAll };
        tete.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        tete.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        tete.Children.Add(new TextePixel(sc.Titre, Bandeau.OrangePo) { Taille = 3, Titre = true, VerticalAlignment = VerticalAlignment.Center });
        var croix = new TextePixel("✕", CadrePixel.Texte) { Taille = 2 };
        var fermer = new CadrePixel { U = 2, Child = croix, Cursor = Cursors.Hand, VerticalAlignment = VerticalAlignment.Center, ToolTip = "Fermer (Échap)" };
        fermer.Change += () => croix.Couleur = fermer.Survol ? CadrePixel.SurvolTexte : CadrePixel.Texte;
        fermer.MouseEnter += (_, _) => fermer.Survol = true;
        fermer.MouseLeave += (_, _) => fermer.Survol = false;
        fermer.MouseLeftButtonDown += (_, e) =>
        {
            e.Handled = true;
            Close();
        };
        Grid.SetColumn(fermer, 1);
        tete.Children.Add(fermer);
        tete.MouseLeftButtonDown += (_, e) =>
        {
            if (e.ButtonState == MouseButtonState.Pressed) DragMove();
        };
        racine.Children.Add(tete);

        var scene = new Border { BorderBrush = Bandeau.Bord, BorderThickness = new Thickness(2), HorizontalAlignment = HorizontalAlignment.Center, Child = _theatre };
        Grid.SetRow(scene, 1);
        racine.Children.Add(scene);

        var dedans = new Grid { Margin = new Thickness(10, 6, 10, 6) };
        dedans.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        dedans.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        var pile = new StackPanel();
        pile.Children.Add(_replique);
        pile.Children.Add(_options);
        dedans.Children.Add(pile);
        _suite.VerticalAlignment = VerticalAlignment.Bottom;
        _suite.Margin = new Thickness(10, 0, 0, 0);
        Grid.SetColumn(_suite, 1);
        dedans.Children.Add(_suite);
        _boite = new CadrePixel { U = Math.Max(2, _theatre.Echelle * 0.6), Child = dedans, Margin = new Thickness(0, 12, 0, 0), Cursor = Cursors.Hand };
        _boite.MouseLeftButtonDown += (_, _) => Suivant();
        Grid.SetRow(_boite, 2);
        racine.Children.Add(_boite);
        Content = racine;

        KeyDown += (_, e) =>
        {
            if (e.Key is Key.Space or Key.Enter) Suivant();
            else if (e.Key == Key.Escape) Close();
            else if (e.Key is >= Key.D1 and <= Key.D3 && _options.Children.Count > 0) Choisir(e.Key - Key.D1);
            else if (e.Key is >= Key.NumPad1 and <= Key.NumPad3 && _options.Children.Count > 0) Choisir(e.Key - Key.NumPad1);
        };
        // docs/SONS.md : le thème de Pilou de ce stade (champ « musique »), sinon la boucle du ton « émotion ».
        Musique.Suivre(this, () => "evolution", () => "emotion", () => _sc.Decor, () => _sc.Musique == "" ? null : _sc.Musique);
        _minuterie = new DispatcherTimer(DispatcherPriority.Render, Dispatcher) { Interval = TimeSpan.FromMilliseconds(30) };
        _minuterie.Tick += (_, _) => Avancer();
        _minuterie.Start();
        Closed += (_, _) => _minuterie.Stop();
        // En HD, Pilou est le Pilou fin du bureau : il entre sous son ancienne forme, puis la métamorphose se joue (le bureau
        // fond l'ancienne forme dans la nouvelle), puis il parle. À l'ancienne définition, il parle dès son entrée.
        if (_theatre.Hd)
        {
            _theatre.Metamorphose(sc.Stade - 1, sc.Stade, T + 2200);
            Dire(0, T + 2200 + VueTheatre.DureeMetamorphose + 500);
        }
        else Dire(0, T + 900);                            // le temps que Pilou entre dans la scène
    }

    // La réplique i commence à l'instant donné.
    private void Dire(int i, double debut)
    {
        _i = i;
        _debut = debut;
        var r = _lignes[i];
        _fin = debut + Evolutions.MsEcriture(r.Texte);
        _replique.Texte = "";
        _suite.Visibility = Visibility.Hidden;
        if (r.Humeur != "")
        {
            _theatre.Humeur(r.Humeur, debut);
            _theatre.Parle(debut, _fin);
        }
    }

    private void Avancer()
    {
        double now = T;
        _theatre.Avancer(now);
        if (_i < 0 || _i >= _lignes.Count) return;
        var texte = _lignes[_i].Texte;
        int n = now >= _fin ? texte.Length : now <= _debut ? 0 : (int)(texte.Length * (now - _debut) / (_fin - _debut));
        _replique.Texte = n >= texte.Length ? texte : texte[..n] + ((int)(now / 280) % 2 == 0 ? "▌" : " ");
        if (n < texte.Length) return;
        bool question = _lignes[_i].Humeur == "" && !_choisi;
        if (question && _options.Children.Count == 0) MontrerOptions();
        _suite.Visibility = question || _termine ? Visibility.Hidden : Visibility.Visible;
    }


    // Un clic dans la boîte ou Espace : finir d'écrire, sinon passer à la réplique suivante, sinon fermer.
    private void Suivant()
    {
        double now = T;
        if (_i < 0) return;
        if (now < _fin)
        {
            _fin = now;
            _theatre.Tait(now);
            return;
        }
        if (_lignes[_i].Humeur == "" && !_choisi) return;         // la question attend sa réponse
        if (_i + 1 < _lignes.Count) Dire(_i + 1, now);
        else if (_termine) Close();
        else Terminer();
    }

    private void MontrerOptions()
    {
        for (int k = 0; k < _sc.Options.Count; k++)
        {
            int n = k;
            var (_, libelle) = _sc.Options[k];
            var texte = new TextePixel($"{n + 1}. {libelle}", CadrePixel.Texte) { Taille = 2 };
            var cadre = new CadrePixel { U = Math.Max(2, Math.Round(_theatre.Echelle * 0.6)), Child = texte, Margin = new Thickness(0, 0, 0, 6), Cursor = Cursors.Hand };
            cadre.Change += () => texte.Couleur = cadre.Survol ? CadrePixel.SurvolTexte : CadrePixel.Texte;
            cadre.MouseEnter += (_, _) =>
            {
                cadre.Survol = true;
                _theatre.Regarde(1);
            };
            cadre.MouseLeave += (_, _) =>
            {
                cadre.Survol = false;
                _theatre.Regarde(0);
            };
            cadre.MouseLeftButtonDown += (_, e) =>
            {
                e.Handled = true;
                Choisir(n);
            };
            _options.Children.Add(cadre);
        }
    }

    // Le choix : gardé la première fois seulement (le Carnet laisse revoir la scène sans le changer).
    private void Choisir(int k)
    {
        if (_choisi || k < 0 || k >= _sc.Options.Count) return;
        _choisi = true;
        var id = _sc.Options[k].Id;
        _garder?.Invoke(id);
        _options.Children.Clear();
        _theatre.Regarde(0);
        int avant = _lignes.Count - 1;                             // la question n'est pas dans la suite
        _lignes = Evolutions.Deroule(_sc, _variante, id);
        Dire(avant, T);
    }

    // La dernière réplique est lue : un bouton pour revenir au bureau.
    private void Terminer()
    {
        _termine = true;
        _theatre.Tait(T);
        var texte = new TextePixel("▸ retour au bureau", CadrePixel.Texte) { Taille = 2 };
        var cadre = new CadrePixel { U = Math.Max(2, Math.Round(_theatre.Echelle * 0.6)), Child = texte, HorizontalAlignment = HorizontalAlignment.Right, Cursor = Cursors.Hand };
        cadre.Change += () => texte.Couleur = cadre.Survol ? CadrePixel.SurvolTexte : CadrePixel.Texte;
        cadre.MouseEnter += (_, _) => cadre.Survol = true;
        cadre.MouseLeave += (_, _) => cadre.Survol = false;
        cadre.MouseLeftButtonDown += (_, e) =>
        {
            e.Handled = true;
            Close();
        };
        _options.Children.Add(cadre);
    }
}

// Essai --essai=lieu:<campagne>:<décor>[:<personnage>[:<humeur>]] (captures, docs/SCENES-HD.md) : la vue de scène seule,
// à son unité entière, avec Pilou qui entre, se réjouit puis parle, et le personnage en pied s'il est donné. Rien n'est écrit.
internal sealed class FenetreLieu : Window
{
    private readonly VueTheatre _theatre;
    private readonly System.Diagnostics.Stopwatch _chrono = System.Diagnostics.Stopwatch.StartNew();

    public FenetreLieu(FenetrePilou pilou, string campagne, string decor, string perso = "", string humeur = "")
    {
        Title = "Pilou · lieu " + campagne + " " + decor;
        Background = FenetreAventure.Gel("#0f1324");
        SizeToContent = SizeToContent.WidthAndHeight;
        ResizeMode = ResizeMode.CanMinimize;
        WindowStartupLocation = WindowStartupLocation.CenterScreen;
        UseLayoutRounding = true;
        _theatre = new VueTheatre(() => AnimationsCampagne.Niveau(pilou.AnimationsCampagnes, Bandeau.Anime),
            () => RenduPilou.Teinte(pilou.AllurePortrait("repos", 0), Banque.Commune), () => pilou.AllurePortrait("repos", 0));
        _theatre.Lieu(campagne, decor, 0, glisser: false);
        _theatre.Ajuster(Theatre.Hd.W * 2, Theatre.Hd.H * 2);
        _theatre.Humeur("joie", 2600);
        _theatre.Parle(3200, 6400);
        if (perso != "") _theatre.Perso("pied-" + campagne + "-" + perso, 400, humeur);
        Content = new Border { Padding = new Thickness(12), Child = _theatre };
        var m = new DispatcherTimer(DispatcherPriority.Render, Dispatcher) { Interval = TimeSpan.FromMilliseconds(30) };
        bool ecrit = false;
        m.Tick += (_, _) =>
        {
            _theatre.Avancer(_chrono.Elapsed.TotalMilliseconds);
            // Au bout de 4 s (Pilou entré, il parle) : le rendu de la scène en PNG, %TEMP%\pilou-lieu-<campagne>-<décor>.png.
            if (ecrit || _chrono.ElapsedMilliseconds < 4000 || Content is not FrameworkElement c || c.ActualWidth <= 0) return;
            ecrit = true;
            var rtb = new System.Windows.Media.Imaging.RenderTargetBitmap((int)c.ActualWidth, (int)c.ActualHeight, 96, 96, System.Windows.Media.PixelFormats.Pbgra32);
            rtb.Render(c);
            var enc = new System.Windows.Media.Imaging.PngBitmapEncoder();
            enc.Frames.Add(System.Windows.Media.Imaging.BitmapFrame.Create(rtb));
            using var fs = System.IO.File.Create(System.IO.Path.Combine(System.IO.Path.GetTempPath(), $"pilou-lieu-{campagne}-{decor}{(perso == "" ? "" : "-" + perso)}{(humeur == "" ? "" : "-" + humeur)}.png"));
            enc.Save(fs);
        };
        m.Start();
        Closed += (_, _) => m.Stop();
    }
}
