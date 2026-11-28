using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;

namespace PilouBureau;

// La scène du théâtre dans la fenêtre Aventure (docs/SCENES.md) : le décor entier, le mini-Pilou qui vit dans le lieu,
// les acteurs d'ambiance, les réactions aux clics. Tout le calcul est dans Theatre.cs (commun avec le téléphone) ; ici,
// seulement l'affichage : une image de 192 × 80 réécrite au plus douze fois par seconde (seulement quand son contenu
// change d'image), agrandie d'un facteur entier sans lissage, et la souris (regard, main au survol, clics).
// Changer de lieu fait un travelling : l'ancien décor part à gauche, le nouveau arrive, Pilou marche au milieu.
// Une erreur ici laisse l'image telle quelle (la fenêtre la remonte à Sur()).
internal sealed class VueTheatre : Border
{
    public const int Glisse = 1200;      // durée du travelling (ms)
    private const int EntreeX = 40;      // là où Pilou se trouve à la fin du travelling

    private readonly Image _image = new() { Stretch = Stretch.Fill, SnapsToDevicePixels = true };
    private readonly WriteableBitmap _bitmap = new(Theatre.W, Theatre.H, 96, 96, PixelFormats.Bgra32, null);
    private readonly uint[] _px = new uint[Theatre.W * Theatre.H];
    private readonly uint[] _avant = new uint[Theatre.W * Theatre.H];
    private readonly uint[] _apres = new uint[Theatre.W * Theatre.H];
    private readonly Func<string> _niveau;
    private readonly Func<uint[]> _teinte;

    private Theatre.Contexte? _cx;
    private Sprite? _decor;
    private List<Theatre.Evenement> _evts = new();
    private double _debut;
    private double _glisse = -1;
    private string _cle = "";
    private int _regard;
    private long _dernierPas = -1;
    private uint _derniere;

    public int Echelle { get; private set; } = 5;

    public VueTheatre(Func<string> niveau, Func<uint[]> teinte)
    {
        _niveau = niveau;
        _teinte = teinte;
        RenderOptions.SetBitmapScalingMode(_image, BitmapScalingMode.NearestNeighbor);
        _image.Source = _bitmap;
        Child = _image;
        ClipToBounds = true;
        _image.MouseMove += (_, e) => Souris(e.GetPosition(_image));
        _image.MouseLeave += (_, _) =>
        {
            _regard = 0;
            _image.Cursor = null;
        };
        _image.MouseLeftButtonDown += (_, e) =>
        {
            Cliquer(e.GetPosition(_image));
            e.Handled = true;
        };
    }

    // La plus grande échelle entière qui tient dans la place donnée (au moins 2).
    public void Ajuster(double largeur, double hauteur)
    {
        int k = (int)Math.Max(2, Math.Min(Math.Floor(largeur / Theatre.W), Math.Floor(hauteur / Theatre.H)));
        Echelle = k;
        _image.Width = Theatre.W * k;
        _image.Height = Theatre.H * k;
    }

    // ---- Les scènes embarquées : assets/scenes/<campagne>.txt et animations.txt (ressources « scene:<fichier> »)

    private static readonly Dictionary<string, Dictionary<string, Theatre.Scene>> Scenes = new();
    private static Dictionary<string, Dictionary<string, Theatre.Anim>>? _anims;

    private static string Ressource(string nom)
    {
        var a = typeof(VueTheatre).Assembly;
        using var st = a.GetManifestResourceStream("scene:" + nom);
        if (st is null) return "";
        using var r = new StreamReader(st);
        return r.ReadToEnd();
    }

    private static Theatre.Scene SceneDe(string campagne, string decor)
    {
        lock (Scenes)
        {
            if (!Scenes.TryGetValue(campagne, out var s)) Scenes[campagne] = s = Theatre.LireScenes(Ressource(campagne + ".txt"));
            // Un décor sans fiche de scène : Pilou marche en bas, sans acteurs.
            return s.TryGetValue(decor, out var sc) ? sc : new Theatre.Scene { Nom = decor, Sol = (0, 77, Theatre.W, 77), Place = 30 };
        }
    }

    private static Dictionary<string, Dictionary<string, Theatre.Anim>> Anims() => _anims ??= Theatre.LireAnimations(Ressource("animations.txt"));

    public bool Pret => _cx is not null && _cx.P.Count > 0;

    // ---- Ce que la fenêtre raconte

    private long T(double now) => (long)Math.Max(0, now - _debut);

    private bool Vif => _niveau() == AnimationsCampagne.Completes;

    // Montre ce lieu (décor de la campagne) ; rend faux s'il n'a pas de dessin. glisser : un travelling depuis le lieu
    // précédent (faux quand la fenêtre rattrape d'un coup des messages déjà lus).
    public bool Lieu(string campagne, string decor, double now, bool glisser = true)
    {
        var cle = campagne + "|" + decor;
        if (cle == _cle && _cx is not null) return _decor is not null;
        var neuf = Illustrations.Decor(Banque.Commune, campagne, decor, 2);
        bool avait = _cx is not null && _decor is not null;
        if (neuf is null) return false;
        glisser = glisser && avait && Vif;
        if (glisser)
        {
            // Travelling : l'ancien lieu (sans Pilou) est gardé tel quel pour glisser.
            Theatre.Composer(_cx!, _decor, _teinte(), _evts, T(now), 0, _niveau(), _avant, avecPilou: false);
            _glisse = now;
        }
        _cle = cle;
        _decor = neuf;
        _cx = new Theatre.Contexte(SceneDe(campagne, decor), Anims(), id => Banque.Commune.Fins.GetValueOrDefault(id));
        _evts = new List<Theatre.Evenement>();
        _debut = glisser ? now + Glisse : now;
        if (!glisser) _glisse = -1;
        if (Vif) _evts.Add(new Theatre.Evenement(0, "entree", glisser ? EntreeX : 0));
        _dernierPas = -1;
        return true;
    }

    private void Ajouter(Theatre.Evenement e)
    {
        if (_cx is null || !Vif || _glisse >= 0) return;
        if (_evts.Count > 0 && e.T < _evts[^1].T) e = e with { T = _evts[^1].T };
        _evts.Add(e);
        _dernierPas = -1;
    }

    public void Humeur(string humeur, double now) => Ajouter(new Theatre.Evenement(T(now), "humeur", Humeur: humeur));

    public void Parle(double now, double fin) => Ajouter(new Theatre.Evenement(T(now), "parle", T(fin)));

    public void Tait(double now) => Ajouter(new Theatre.Evenement(T(now), "parle", T(now)));

    // Il s'en va (un choix l'envoie en route) ; il revient s'il était parti et que l'histoire continue ici.
    public void Depart(double now) => Ajouter(new Theatre.Evenement(T(now), "depart", 1));

    public void Revient(double now)
    {
        if (_cx is null) return;
        var p = Theatre.Pilou(_cx, _evts, T(now));
        if (!p.Visible) Ajouter(new Theatre.Evenement(T(now), "entree"));
    }

    public void Regarde(int sens) => _regard = Math.Sign(sens);

    // Il est en route (attente, repos) : la scène montre le lieu sans lui ; il reviendra par la gauche.
    public void Absent(double now)
    {
        if (_cx is null || !Vif) return;
        _evts = new List<Theatre.Evenement> { new(0, "entree", Theatre.SortieD + 4), new(0, "depart", 1) };
        _glisse = -1;
        _debut = now;
        _dernierPas = -1;
    }

    // ---- Souris

    private (int X, int Y) Point(Point p)
    {
        double k = _image.ActualWidth > 0 ? _image.ActualWidth / Theatre.W : Echelle;
        return ((int)Math.Floor(p.X / k), (int)Math.Floor(p.Y / k));
    }

    private double _now;

    private void Souris(Point p)
    {
        if (_cx is null) return;
        var (x, y) = Point(p);
        var pi = Theatre.Pilou(_cx, _evts, T(_now));
        _regard = x - pi.X > 14 ? 1 : x - pi.X < -14 ? -1 : 0;
        bool sensible = Vif && _glisse < 0 && Theatre.Repond(_cx, _evts, T(_now), x, y);
        _image.Cursor = sensible ? Cursors.Hand : null;
    }

    private void Cliquer(Point p)
    {
        if (_cx is null || !Vif || _glisse >= 0) return;
        var (x, y) = Point(p);
        Ajouter(new Theatre.Evenement(T(_now), "clic", x, y));
    }

    // ---- Chaque image (la minuterie de la fenêtre)

    public void Avancer(double now)
    {
        _now = now;
        if (_cx is null) return;
        string niveau = _niveau();
        var teinte = _teinte();
        if (_glisse >= 0)
        {
            double f = (now - _glisse) / Glisse;
            if (f >= 1) _glisse = -1;
            else
            {
                Glisser(f, teinte);
                return;
            }
        }
        long t = T(now);
        long pas = t / Theatre.Pas;
        if (pas == _dernierPas && niveau == AnimationsCampagne.Completes) return;
        if (niveau != AnimationsCampagne.Completes && pas / 2 == _dernierPas / 2 && _dernierPas >= 0) return;
        _dernierPas = pas;
        Theatre.Composer(_cx, _decor, teinte, _evts, t, _regard, niveau, _px);
        uint h = Theatre.Fnv(_px);
        if (h == _derniere) return;
        _derniere = h;
        Ecrire(_px);
    }

    // Le travelling : décors côte à côte qui glissent (lissés), Pilou qui marche au milieu.
    private void Glisser(double f, uint[] teinte)
    {
        double l = f * f * (3 - 2 * f);
        int dx = (int)Math.Round(-l * Theatre.W);
        Theatre.Composer(_cx!, _decor, teinte, Array.Empty<Theatre.Evenement>(), 0, 0, _niveau(), _apres, avecPilou: false);
        for (int y = 0; y < Theatre.H; y++)
        for (int x = 0; x < Theatre.W; x++)
        {
            int sx = x - dx;
            _px[y * Theatre.W + x] = sx < Theatre.W ? _avant[y * Theatre.W + sx] : _apres[y * Theatre.W + sx - Theatre.W];
        }
        if (_cx!.P.TryGetValue("marche", out var m))
        {
            int px = EntreeX;
            Theatre.Poser(_px, Banque.Commune.Fins.GetValueOrDefault(Theatre.IdPilou), m.Image((long)(f * Glisse)), px,
                Theatre.Sol(_cx.Scene, px), false, teinte, Theatre.PilouX, Theatre.PilouY);
        }
        _derniere = 0;
        Ecrire(_px);
    }

    // ---- Le portrait de la boîte de dialogue : le même mini-Pilou que dans la scène (même dessin fin), agrandi d'un
    // facteur entier par la fenêtre ; il prend l'humeur du message, parle pendant l'écriture, cligne.

    private readonly uint[] _visage = new uint[Theatre.W * Theatre.H];
    private readonly uint[] _petit = new uint[VisageW * VisageH];
    private int _visageImage = -1;
    public const int VisageW = 34, VisageH = 36;

    // toujours : rend l'image même si elle n'a pas changé (une petite tête du fil, pas l'animation de la boîte).
    public BitmapSource? Visage(string humeur, bool parle, double now, bool toujours = false)
    {
        if (_cx is null || _cx.P.Count == 0) return null;
        var P = _cx.P;
        long t = (long)now;
        string face = humeur is "" or "neutre" || !P.ContainsKey("repos-" + humeur) ? "repos" : "repos-" + humeur;
        string niveau = _niveau();
        int im = niveau == AnimationsCampagne.Aucune ? P[face].Premiere
            : AnimationsCampagne.Cligne(t) ? P["cligne"].Premiere
            : niveau != AnimationsCampagne.Completes ? P[face].Premiere
            : parle ? P["parle"].Image(t) : P[face].Image(t);
        if (im == _visageImage && !toujours) return null;
        if (!toujours) _visageImage = im;
        Array.Clear(_visage);
        Theatre.Poser(_visage, Banque.Commune.Fins.GetValueOrDefault(Theatre.IdPilou), im, Theatre.PilouX, Theatre.PilouY, false, _teinte(),
            Theatre.PilouX, Theatre.PilouY);
        for (int y = 0; y < VisageH; y++)
            Array.Copy(_visage, y * Theatre.W, _petit, y * VisageW, VisageW);
        return Apercu.Bitmap(_petit, VisageW, VisageH);
    }

    private void Ecrire(uint[] px) => _bitmap.WritePixels(new Int32Rect(0, 0, Theatre.W, Theatre.H), px, Theatre.W * 4, 0);

    // Où est Pilou dans la scène, en coordonnées de ce contrôle (pour poser une bulle ou un choix à côté de lui).
    public Point PositionPilou(double now)
    {
        if (_cx is null) return new Point(0, 0);
        var p = Theatre.Pilou(_cx, _evts, T(now));
        double k = _image.ActualWidth > 0 ? _image.ActualWidth / Theatre.W : Echelle;
        return new Point(p.X * k, (p.Y - 24) * k);
    }
}
