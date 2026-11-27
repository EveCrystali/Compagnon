using System.Diagnostics;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Threading;

namespace PilouBureau;

// Ce que Pilou donne à la fenêtre du jeu : où se placer, qui il est, et comment créditer une partie.
public sealed record LancementDefense(
    Rect Zone,                                   // zone de travail de l'écran de Pilou (unités WPF)
    double Echelle,                              // pixels physiques par unité WPF
    double Largeur,                              // part de la largeur de l'écran (centrée)
    bool Demo,
    bool FlashsReduits,
    int Meilleur,
    ulong Graine,
    Allure Pilou,                                // son allure (couleur, stade, objets portés)
    Func<PartieDefense, ResultatDefense> Crediter,
    Func<bool> IaAttend,
    Action<bool> ChangerFlashs);

// « Défense du bureau » : une bande de l'écran au-dessus de la barre des tâches (42 % de la hauteur), toujours
// devant, légèrement assombrie. Le jeu est dessiné en pixels de jeu (DessinDefense) dans un WriteableBitmap
// agrandi sans lissage d'un facteur entier. Une image toutes les 16 ms au plus (CompositionTarget.Rendering,
// même sur un écran à 144 Hz) tant que ça bouge ; à l'arrêt (accueil, pause, fin), 8 images par seconde ;
// cachée, aucune. Tout s'arrête à la fermeture.
public sealed class FenetreDefense : Window
{
    public const double PartHauteur = 0.42;

    private readonly LancementDefense _l;
    private readonly PartieDefense _partie;
    private readonly PiloteDemo? _pilote;
    private readonly ToileDefense _toile;
    private readonly WriteableBitmap _bitmap;
    private readonly Image _image = new();
    private readonly int _k;
    private readonly double _gauchePhys;
    private readonly Stopwatch _chrono = Stopwatch.StartNew();
    private readonly VueDefense _vue;
    private readonly DispatcherTimer _lent, _veille;
    private bool _rendu, _ferme, _credite, _cachePlein;
    private double _dernier, _derniereImage, _finDemo = -1, _alerteJusque, _flashJusque;
    private int _gauche, _droite;
    private (int X, int Y) _souris = (int.MinValue, int.MinValue);

    public FenetreDefense(LancementDefense l)
    {
        _l = l;
        // Taille en pixels physiques : la bande, puis un facteur entier k (un pixel de jeu = k × k pixels d'écran).
        var z = l.Zone;
        double s = l.Echelle;
        var bande = Placement.Bande(z.Left, z.Top, z.Width, z.Height, s, l.Largeur, PartHauteur);
        _k = bande.K;
        int w = bande.W, h = bande.H;
        _partie = new PartieDefense(w, h, l.Graine);
        _pilote = l.Demo ? new PiloteDemo(l.Graine) : null;
        _toile = new ToileDefense(w, h);
        _vue = new VueDefense { Demo = l.Demo, FlashsReduits = l.FlashsReduits, Meilleur = l.Meilleur };
        _bitmap = new WriteableBitmap(w, h, 96, 96, PixelFormats.Bgra32, null);

        WindowStyle = WindowStyle.None;
        AllowsTransparency = true;
        Background = Brushes.Transparent;
        ShowInTaskbar = false;
        ResizeMode = ResizeMode.NoResize;
        Topmost = true;
        Title = "Défense du bureau";
        UseLayoutRounding = true;
        Width = w * _k / s;
        Height = h * _k / s;
        _gauchePhys = bande.GauchePhys;
        Left = _gauchePhys / s;
        Top = bande.HautPhys / s;
        _image.Source = _bitmap;
        _image.Stretch = Stretch.Fill;
        _image.Width = Width;
        _image.Height = Height;
        RenderOptions.SetBitmapScalingMode(_image, BitmapScalingMode.NearestNeighbor);
        Content = _image;
        Cursor = Cursors.Cross;

        _lent = new DispatcherTimer(TimeSpan.FromMilliseconds(125), DispatcherPriority.Render, (_, _) => Tic(), Dispatcher);
        _veille = new DispatcherTimer(TimeSpan.FromSeconds(1), DispatcherPriority.Background, (_, _) => Veiller(), Dispatcher);

        MouseLeftButtonDown += Clic;
        MouseLeftButtonUp += (_, _) => _partie.Tirer = false;
        MouseRightButtonUp += (_, e) =>
        {
            e.Handled = true;
            Close();
        };
        KeyDown += Touche;
        KeyUp += Relache;
        Deactivated += (_, _) =>
        {
            // Partie ailleurs (clic dans une autre appli) : pause, touches relâchées.
            _gauche = _droite = 0;
            _partie.Diriger(0);
            _partie.Tirer = false;
            if (!_l.Demo) _partie.Pause(true);
            Rythme();
        };
        Loaded += (_, _) =>
        {
            Activate();
            Focus();
            if (_l.Demo) _partie.Commencer();
            _veille.Start();
            Peindre(0);
            Rythme();
        };
        IsVisibleChanged += (_, _) => Rythme();
        Closed += (_, _) => Arreter();
    }

    public bool Demo => _l.Demo;

    private double Maintenant => _chrono.Elapsed.TotalMilliseconds;

    // Animé (Rendering) ou au ralenti (minuterie de 125 ms), selon ce qui se passe ; rien si caché ou fermé.
    private void Rythme()
    {
        bool visible = !_ferme && IsVisible;
        bool anime = visible && (_partie.Phase is PhaseDefense.Jeu or PhaseDefense.EntreVagues || _partie.Eclats.Count > 0);
        if (anime && !_rendu)
        {
            _dernier = Maintenant;
            CompositionTarget.Rendering += ImageSuivante;
            _rendu = true;
        }
        else if (!anime && _rendu)
        {
            CompositionTarget.Rendering -= ImageSuivante;
            _rendu = false;
        }
        if (visible && !anime) _lent.Start();
        else _lent.Stop();
    }

    private void ImageSuivante(object? sender, EventArgs e)
    {
        // Écrans à 120 ou 144 Hz : 60 images par seconde suffisent.
        if (Maintenant - _derniereImage < 15.5) return;
        Tic();
    }

    private void Tic()
    {
        if (_ferme) return;
        double t = Maintenant, dt = Math.Clamp((t - _dernier) / 1000, 0, 0.1);
        _dernier = t;
        _derniereImage = t;
        Suivre();
        _pilote?.Jouer(_partie, dt);
        _partie.Avancer(dt);
        foreach (var ev in _partie.Evenements())
            switch (ev)
            {
                case EvenementDefense.Blesse:
                    _alerteJusque = t + 300;
                    break;
                case EvenementDefense.BossVaincu:
                    _flashJusque = t + 140;
                    break;
                case EvenementDefense.Fin:
                    Crediter();
                    if (_l.Demo) _finDemo = t + 4000;
                    break;
            }
        // Démo : elle recommence toute seule quelques secondes après la fin.
        if (_l.Demo && _finDemo > 0 && t > _finDemo)
        {
            _finDemo = -1;
            _partie.Commencer();
        }
        Peindre(t);
        Rythme();
    }

    // La souris, où qu'elle soit (même au-dessus de la bande) : Pilou suit son x.
    private void Suivre()
    {
        if (_l.Demo) return;
        var p = Natif.Souris();
        if (p.X == int.MinValue || p == _souris) return;
        _souris = p;
        _partie.Viser((p.X - _gauchePhys) / _k);
    }

    private void Peindre(double t)
    {
        _vue.Alerte = t < _alerteJusque ? 1 : 0;
        _vue.Flash = t < _flashJusque ? 1 : 0;
        var a = DessinDefense.AllurePilou(_l.Pilou, _partie, t, _vue.Resultat);
        var pilou = RenduPilou.Rendre(a, Banque.Commune, out var geo);
        DessinDefense.Dessiner(_toile, _partie, Banque.Commune, pilou, geo, t, _vue);
        _bitmap.WritePixels(new Int32Rect(0, 0, _toile.W, _toile.H), _toile.Px, _toile.W * 4, 0);
    }

    // Une partie finie (ou quittée en cours) est créditée une fois : gains bornés, record, quête.
    private void Crediter()
    {
        if (_credite || _l.Demo || _partie.Score <= 0 && _partie.VaguesFinies == 0) return;
        _credite = true;
        _vue.Resultat = _l.Crediter(_partie);
        _vue.Meilleur = Math.Max(_vue.Meilleur, _partie.Score);
    }

    private void Rejouer()
    {
        _credite = false;
        _vue.Resultat = null;
        _partie.Commencer();
        Rythme();
    }

    // Plein écran ailleurs (jeu, vidéo, présentation) : pause et la bande se cache ; elle revient en pause.
    private void Veiller()
    {
        _vue.IaAttend = _l.IaAttend();
        var ecran = Sondes.Ecran();
        bool plein = ecran is Activites.Ecran.PleinEcran or Activites.Ecran.Jeu3D or Activites.Ecran.Presentation;
        if (plein && !_cachePlein)
        {
            _cachePlein = true;
            if (!_l.Demo) _partie.Pause(true);
            Hide();
        }
        else if (!plein && _cachePlein)
        {
            _cachePlein = false;
            Show();
        }
    }

    private Point Monde(MouseEventArgs e)
    {
        var p = e.GetPosition(_image);
        return new Point(p.X / Math.Max(1, _image.ActualWidth) * _toile.W, p.Y / Math.Max(1, _image.ActualHeight) * _toile.H);
    }

    private void Clic(object sender, MouseButtonEventArgs e)
    {
        e.Handled = true;
        var m = Monde(e);
        if (DessinDefense.Fermer(_toile.W).Elargie(3).Contient(m.X, m.Y))
        {
            Close();
            return;
        }
        switch (_partie.Phase)
        {
            case PhaseDefense.Accueil:
                if (DessinDefense.Flashs(_toile.W, _toile.H).Contient(m.X, m.Y)) BasculerFlashs();
                else if (!_l.Demo) _partie.Commencer();
                break;
            case PhaseDefense.Pause:
                _partie.Pause(false);
                break;
            case PhaseDefense.Fin:
                if (DessinDefense.Rejouer(_toile.W, _toile.H).Contient(m.X, m.Y)) Rejouer();
                else if (DessinDefense.Quitter(_toile.W, _toile.H).Contient(m.X, m.Y)) Close();
                break;
            default:
                if (!_l.Demo)
                {
                    _partie.Tirer = true;
                    _partie.Appuyer();
                }
                break;
        }
        Rythme();
    }

    private void BasculerFlashs()
    {
        _vue.FlashsReduits = !_vue.FlashsReduits;
        _l.ChangerFlashs(_vue.FlashsReduits);
        Peindre(Maintenant);
    }

    private void Touche(object sender, KeyEventArgs e)
    {
        e.Handled = true;
        switch (e.Key)
        {
            case Key.Escape:
                Close();
                return;
            case Key.F:
                BasculerFlashs();
                return;
            case Key.P:
                if (_partie.Phase == PhaseDefense.Pause) _partie.Pause(false);
                else _partie.Pause(true);
                break;
            case Key.Left or Key.A or Key.Q:
                _gauche = 1;
                break;
            case Key.Right or Key.D:
                _droite = 1;
                break;
            case Key.Space or Key.Enter or Key.Up or Key.W or Key.Z:
                if (_partie.Phase == PhaseDefense.Accueil && !_l.Demo) _partie.Commencer();
                else if (_partie.Phase == PhaseDefense.Pause) _partie.Pause(false);
                else if (_partie.Phase == PhaseDefense.Fin && !e.IsRepeat && !_l.Demo) Rejouer();
                else if (!_l.Demo)
                {
                    if (!e.IsRepeat) _partie.Appuyer();
                    _partie.Tirer = true;
                }
                break;
            default:
                e.Handled = false;
                return;
        }
        if (!_l.Demo) _partie.Diriger(_droite - _gauche);
        Rythme();
    }

    private void Relache(object sender, KeyEventArgs e)
    {
        switch (e.Key)
        {
            case Key.Left or Key.A or Key.Q: _gauche = 0; break;
            case Key.Right or Key.D: _droite = 0; break;
            case Key.Space or Key.Enter or Key.Up or Key.W or Key.Z: _partie.Tirer = false; break;
            default: return;
        }
        if (!_l.Demo) _partie.Diriger(_droite - _gauche);
    }

    // Fermeture : plus aucune minuterie ni abonnement au rendu ; la partie en cours est comptée.
    private void Arreter()
    {
        if (_ferme) return;
        _ferme = true;
        if (_rendu) CompositionTarget.Rendering -= ImageSuivante;
        _rendu = false;
        _lent.Stop();
        _veille.Stop();
        _chrono.Stop();
        _partie.Abandonner();
        _partie.Evenements();
        Crediter();
    }
}
