using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Animation;
using System.Windows.Media.Imaging;
using System.Windows.Shapes;

namespace PilouBureau;

// Les animations de la fenêtre Aventure (docs/CAMPAGNES.md, « Animations ») : décors qui vivent en boucle, portraits
// des personnages, transitions entre décors (volet pixelisé ou fondu), fond qui respire selon le ton et l'heure,
// vignettes de la bibliothèque. Les règles (quelle image, quand) sont communes avec le téléphone :
// AnimationsCampagne.cs. Ici : seulement l'affichage, sans allocation par image (images rendues une fois et gardées
// dans un cache borné ; le volet réécrit toujours le même tampon). Tout chemin est protégé : un sprite manquant ou une
// erreur retombent sur l'image fixe, jamais sur un plantage.
internal sealed class ScenesAnimees
{
    // ---- Cache borné des images rendues (par sprite et par image)

    private const int CacheMax = 28;
    private static readonly Dictionary<Sprite, BitmapSource?[]> Cache = new(ReferenceEqualityComparer.Instance);
    private static readonly LinkedList<Sprite> Ordre = new();

    internal static BitmapSource? Image(Sprite s, int k)
    {
        if (s.Images.Count == 0) return null;
        k = Math.Clamp(k, 0, s.Images.Count - 1);
        lock (Cache)
        {
            if (!Cache.TryGetValue(s, out var images))
            {
                images = new BitmapSource?[s.Images.Count];
                Cache[s] = images;
                Ordre.AddFirst(s);
                while (Ordre.Count > CacheMax)
                {
                    Cache.Remove(Ordre.Last!.Value);
                    Ordre.RemoveLast();
                }
            }
            else if (Ordre.First?.Value != s)
            {
                Ordre.Remove(s);
                Ordre.AddFirst(s);
            }
            return images[k] ??= Rendre(s, k);
        }
    }

    private static BitmapSource Rendre(Sprite s, int k)
    {
        var g = Banque.Grille(s, k * Math.Max(1, s.Duree));
        int h = g.GetLength(0), w = g.GetLength(1);
        var px = new uint[w * h];
        for (int y = 0; y < h; y++)
        for (int x = 0; x < w; x++)
            px[y * w + x] = g[y, x];
        return Apercu.Bitmap(px, w, h);
    }

    // ---- Réglages

    private readonly FenetrePilou _pilou;
    public ScenesAnimees(FenetrePilou pilou) => _pilou = pilou;

    // Le niveau effectif (réglage du menu, et réglage de Windows « Afficher les animations »).
    public string Niveau => AnimationsCampagne.Niveau(_pilou.AnimationsCampagnes, Bandeau.Anime);
    public bool Completes => Niveau == AnimationsCampagne.Completes;
    public bool Aucune => Niveau == AnimationsCampagne.Aucune;
    public bool TexteInstantane => _pilou.TexteInstantane || Aucune;
    public static int Echelle => Finesse.Active ? 2 : 1;

    // ---- Décor de la scène : boucle et transition

    private Image? _decor;
    private Sprite? _decorSprite;
    private long _decorK = -1;
    private Image? _ancien;
    private WriteableBitmap? _volet;
    private uint[]? _avant, _apres, _melange;
    private double _debutVolet = -1;
    private Sprite? _vientDe;

    // Montre ce décor (null : aucun dessin, la scène garde son repli). Rend vrai s'il est montré.
    public bool Decor(Image cible, Image? ancien, Sprite? s, double t)
    {
        var precedent = _decorSprite;
        var precedentK = _decorK;
        _decor = cible;
        _ancien = ancien;
        _decorSprite = s;
        _decorK = -1;
        _debutVolet = -1;
        if (ancien is not null) ancien.Visibility = Visibility.Collapsed;
        if (s is null) return false;
        try
        {
            if (precedent is not null && !ReferenceEquals(precedent, s) && !Aucune && precedent.W == s.W && precedent.H == s.H)
            {
                if (Completes)
                {
                    _vientDe = precedent;
                    _avant = Pixels(precedent, (int)Math.Max(0, precedentK), _avant);
                    _debutVolet = t;
                }
                else if (ancien is not null && Image(precedent, (int)Math.Max(0, precedentK)) is { } im)
                {
                    // Réduites : un fondu simple, l'ancien décor s'efface par-dessus.
                    ancien.Source = im;
                    ancien.Visibility = Visibility.Visible;
                    ancien.BeginAnimation(UIElement.OpacityProperty, new DoubleAnimation(1, 0, TimeSpan.FromMilliseconds(AnimationsCampagne.Transition)));
                }
            }
            Avancer(t);
            return true;
        }
        catch (Exception e) when (e is not OutOfMemoryException)
        {
            System.Diagnostics.Debug.WriteLine($"ScenesAnimees.Decor : {e}");
            cible.Source = Image(s, 0);
            return true;
        }
    }

    private static uint[] Pixels(Sprite s, int k, uint[]? tampon)
    {
        var im = Image(s, k)!;
        int n = im.PixelWidth * im.PixelHeight;
        if (tampon is null || tampon.Length != n) tampon = new uint[n];
        im.CopyPixels(tampon, im.PixelWidth * 4, 0);
        return tampon;
    }

    // ---- Portrait du personnage

    private Image? _perso;
    private Sprite? _persoSprite;
    private int _persoK = -1;
    private bool _parle;
    private double _persoDepuis;

    public void Personnage(Image cible, Sprite? s, bool parle, double t)
    {
        _perso = cible;
        _parle = parle;
        if (ReferenceEquals(s, _persoSprite)) return;
        _persoSprite = s;
        _persoK = -1;
        _persoDepuis = t;
        if (s is null)
        {
            cible.Visibility = Visibility.Collapsed;
            return;
        }
        cible.Source = Image(s, 0);
        cible.Visibility = Visibility.Visible;
        if (!Aucune)
        {
            // Il entre doucement par le côté.
            cible.Opacity = 0;
            cible.BeginAnimation(UIElement.OpacityProperty, new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(320)));
            var tr = new TranslateTransform(Completes ? 18 : 0, 0);
            cible.RenderTransform = tr;
            if (Completes)
                tr.BeginAnimation(TranslateTransform.XProperty, new DoubleAnimation(18, 0, TimeSpan.FromMilliseconds(380))
                    { EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut } });
        }
    }

    public void Parle(bool parle) => _parle = parle;

    // ---- Vignettes de la bibliothèque (le premier décor de chaque campagne, au ralenti)

    private readonly List<(Image Im, Sprite S, int K)> _vignettes = new();

    public void ViderVignettes() => _vignettes.Clear();

    public void Vignette(Image im, Sprite s) => _vignettes.Add((im, s, -1));

    // ---- Fond de la fenêtre

    private Canvas? _fond;
    private readonly Rectangle[] _part = new Rectangle[AnimationsCampagne.NbParticules];
    private string _fondCle = "", _fondTon = "";
    private long _fondK = -1;

    public UIElement Fond()
    {
        _fond = new Canvas { IsHitTestVisible = false, ClipToBounds = true };
        for (int i = 0; i < _part.Length; i++)
        {
            _part[i] = new Rectangle { Width = 3, Height = 3, Opacity = 0, IsHitTestVisible = false };
            _fond.Children.Add(_part[i]);
        }
        return _fond;
    }

    // Ton de la campagne en cours ("" : aucune).
    public void Ton(string ton)
    {
        if (_fond is null) return;
        int heure = DateTime.Now.Hour;
        var cle = ton + "|" + AnimationsCampagne.Moment(heure);
        if (cle == _fondCle) return;
        _fondCle = cle;
        _fondTon = ton;
        var (haut, bas, part) = AnimationsCampagne.TeintesFond(ton, heure);
        var g = new LinearGradientBrush((Color)ColorConverter.ConvertFromString(haut), (Color)ColorConverter.ConvertFromString(bas), 90);
        g.Freeze();
        _fond.Background = g;
        var p = new SolidColorBrush((Color)ColorConverter.ConvertFromString(part));
        p.Freeze();
        foreach (var r in _part) r.Fill = p;
        _fondK = -1;
    }

    // ---- Chaque image (la minuterie de la fenêtre) : rien ne change tant que l'image à montrer est la même.

    public void Avancer(double t)
    {
        long ms = (long)t;
        string niveau = Niveau;
        // Décor : la transition, puis la boucle.
        if (_decor is not null && _decorSprite is { } s)
        {
            if (_debutVolet >= 0 && _vientDe is not null)
            {
                double p = (t - _debutVolet) / AnimationsCampagne.Transition;
                if (p >= 1)
                {
                    _debutVolet = -1;
                    _vientDe = null;
                    _decorK = -1;
                }
                else
                {
                    Volet(s, p);
                    return;
                }
            }
            long k = AnimationsCampagne.ImageDecor(s.Images.Count, s.Duree, ms, niveau);
            if (k != _decorK)
            {
                _decorK = k;
                _decor.Source = Image(s, (int)k);
            }
        }
        // Portrait : respiration, clignement, parole.
        if (_perso is not null && _persoSprite is { } ps)
        {
            int k = AnimationsCampagne.ImagePortrait(ps.Images.Count, ms - (long)_persoDepuis, _parle, niveau);
            if (k != _persoK)
            {
                _persoK = k;
                _perso.Source = Image(ps, k);
            }
        }
        // Vignettes : au ralenti (une image toutes les deux durées), et seulement si tout est animé.
        for (int i = 0; i < _vignettes.Count; i++)
        {
            var (im, vs, vk) = _vignettes[i];
            int k = niveau == AnimationsCampagne.Completes ? (int)(ms / Math.Max(1, vs.Duree * 3) % Math.Min(4, vs.Images.Count)) : 0;
            if (k == vk) continue;
            im.Source = Image(vs, k);
            _vignettes[i] = (im, vs, k);
        }
        // Fond : quatre images par seconde.
        if (_fond is not null && _fond.ActualWidth > 0)
        {
            long fk = niveau == AnimationsCampagne.Completes ? ms / 250 : 0;
            if (fk != _fondK)
            {
                _fondK = fk;
                bool montre = niveau == AnimationsCampagne.Completes && _fondTon != "";
                for (int i = 0; i < _part.Length; i++)
                {
                    var (x, y, a) = AnimationsCampagne.ParticuleFond(_fondTon, i, fk * 250);
                    _part[i].Opacity = montre ? a / 255.0 * 0.7 : 0;
                    Canvas.SetLeft(_part[i], Math.Round(x / 10000.0 * _fond.ActualWidth));
                    Canvas.SetTop(_part[i], Math.Round(y / 10000.0 * _fond.ActualHeight));
                }
            }
        }
    }

    // Le volet pixelisé : les blocs du nouveau décor apparaissent dans l'ordre commun (AnimationsCampagne.OrdreVolet).
    private void Volet(Sprite s, double p)
    {
        if (_decor is null || _avant is null) return;
        var neuf = Image(s, 0)!;
        int w = neuf.PixelWidth, h = neuf.PixelHeight;
        if (_volet is null || _volet.PixelWidth != w || _volet.PixelHeight != h)
        {
            _volet = new WriteableBitmap(w, h, neuf.DpiX, neuf.DpiY, PixelFormats.Bgra32, null);
            _melange = new uint[w * h];
        }
        _apres = Pixels(s, 0, _apres);
        if (_avant.Length != _apres.Length) return;
        int bloc = AnimationsCampagne.VoletBloc * w / Illustrations.DecorLargeur;
        int nbx = (w + bloc - 1) / bloc;
        int seuil = (int)(p * 10000);
        for (int y = 0; y < h; y++)
        {
            int by = y / bloc;
            for (int x = 0; x < w; x++)
            {
                bool montre = AnimationsCampagne.OrdreVolet(x / bloc, by, nbx) < seuil;
                _melange![y * w + x] = montre ? _apres[y * w + x] : _avant[y * w + x];
            }
        }
        _volet.WritePixels(new Int32Rect(0, 0, w, h), _melange, w * 4, 0);
        if (!ReferenceEquals(_decor.Source, _volet)) _decor.Source = _volet;
    }

    // ---- Petits effets d'interface (entrées, chutes, éclats), selon le niveau

    // Un élément tombe en place après `delai` ms (récompenses de fin).
    public void Tomber(UIElement e, int delai)
    {
        if (Aucune) return;
        e.Opacity = 0;
        e.BeginAnimation(UIElement.OpacityProperty, new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(240)) { BeginTime = TimeSpan.FromMilliseconds(delai) });
        if (!Completes) return;
        var tr = new TranslateTransform(0, -26);
        e.RenderTransform = tr;
        tr.BeginAnimation(TranslateTransform.YProperty, new DoubleAnimation(-26, 0, TimeSpan.FromMilliseconds(520))
            { BeginTime = TimeSpan.FromMilliseconds(delai), EasingFunction = new BounceEase { Bounces = 1, Bounciness = 3 } });
    }

    // Un emblème ou un souvenir qui se pose avec un petit éclat (quatre traits qui s'écartent puis s'effacent).
    public UIElement Eclat(UIElement contenu, double taille, Brush teinte, int delai = 0)
    {
        var g = new Grid { Width = taille, Height = taille };
        if (!Aucune)
        {
            for (int i = 0; i < 4; i++)
            {
                var r = new Rectangle { Width = 3, Height = taille * 0.22, Fill = teinte, Opacity = 0, IsHitTestVisible = false,
                    HorizontalAlignment = HorizontalAlignment.Center, VerticalAlignment = VerticalAlignment.Center,
                    RenderTransformOrigin = new Point(0.5, 0.5) };
                var groupe = new TransformGroup();
                var dep = new TranslateTransform(0, 0);
                groupe.Children.Add(dep);
                groupe.Children.Add(new RotateTransform(45 + i * 90));
                r.RenderTransform = groupe;
                g.Children.Add(r);
                if (Completes)
                {
                    var debut = TimeSpan.FromMilliseconds(delai + 260);
                    dep.BeginAnimation(TranslateTransform.YProperty, new DoubleAnimation(-taille * 0.2, -taille * 0.62, TimeSpan.FromMilliseconds(520)) { BeginTime = debut });
                    var o = new DoubleAnimationUsingKeyFrames { BeginTime = debut };
                    o.KeyFrames.Add(new LinearDoubleKeyFrame(0.9, KeyTime.FromTimeSpan(TimeSpan.FromMilliseconds(80))));
                    o.KeyFrames.Add(new LinearDoubleKeyFrame(0, KeyTime.FromTimeSpan(TimeSpan.FromMilliseconds(520))));
                    r.BeginAnimation(UIElement.OpacityProperty, o);
                }
            }
        }
        g.Children.Add(contenu);
        if (!Aucune)
        {
            contenu.RenderTransformOrigin = new Point(0.5, 0.5);
            var sc = new ScaleTransform(0.3, 0.3);
            contenu.RenderTransform = sc;
            contenu.Opacity = 0;
            var d = TimeSpan.FromMilliseconds(delai);
            contenu.BeginAnimation(UIElement.OpacityProperty, new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(200)) { BeginTime = d });
            var a = new DoubleAnimation(0.3, 1, TimeSpan.FromMilliseconds(Completes ? 520 : 200))
                { BeginTime = d, EasingFunction = Completes ? new BackEase { Amplitude = 0.5 } : null };
            sc.BeginAnimation(ScaleTransform.ScaleXProperty, a);
            sc.BeginAnimation(ScaleTransform.ScaleYProperty, a);
        }
        return g;
    }

    // Une image nette d'un sprite (première image), à la taille donnée.
    public static Image Vue(Sprite s, double largeur)
    {
        var src = Image(s, 0);
        var im = new Image { Source = src, Width = largeur, Height = largeur * s.H / Math.Max(1, s.W), Stretch = Stretch.Uniform };
        RenderOptions.SetBitmapScalingMode(im, BitmapScalingMode.NearestNeighbor);
        return im;
    }
}
