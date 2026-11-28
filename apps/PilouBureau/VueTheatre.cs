using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;

namespace PilouBureau;

// La scène du théâtre dans la fenêtre Aventure (docs/SCENES.md, docs/SCENES-HD.md) : le décor entier, Pilou qui vit dans
// le lieu, les acteurs d'ambiance, les réactions aux clics. Tout le calcul est dans Theatre.cs et TheatreHd.cs (communs
// avec le téléphone) ; ici, seulement l'affichage : une image réécrite au plus douze fois par seconde (seulement quand
// son contenu change), agrandie d'un facteur entier sans lissage, et la souris (regard, main au survol, clics).
// Deux définitions, jamais mélangées dans une image : un lieu dont le décor HD existe (assets/decors) se joue en
// 480 × 240 avec le Pilou fin du bureau et les sprites HD ; les autres restent en 192 × 80 avec le mini-Pilou.
// Changer de lieu fait un travelling (entre deux lieux de même définition) : l'ancien décor part à gauche, le nouveau
// arrive. Une erreur ici laisse l'image telle quelle (la fenêtre la remonte à Sur()).
internal sealed class VueTheatre : Border
{
    public const int Glisse = 1200;      // durée du travelling (ms)
    private const int EntreeX = 40;      // là où Pilou se trouve à la fin du travelling (ancienne unité)

    // Une surface par définition : bitmap et tampons.
    private sealed class Surface
    {
        public readonly int W, H;
        public readonly WriteableBitmap Bitmap;
        public readonly uint[] Px, Avant, Apres;

        public Surface(int w, int h)
        {
            W = w;
            H = h;
            Bitmap = new WriteableBitmap(w, h, 96, 96, PixelFormats.Bgra32, null);
            Px = new uint[w * h];
            Avant = new uint[w * h];
            Apres = new uint[w * h];
        }
    }

    private readonly Surface _ancienne = new(Theatre.W, Theatre.H);
    private Surface? _hdSurface;
    private Surface _s;

    private readonly Image _image = new() { Stretch = Stretch.Fill, SnapsToDevicePixels = true };
    private readonly Func<string> _niveau;
    private readonly Func<uint[]> _teinte;
    private readonly Func<Allure>? _allure;

    private Theatre.Contexte? _cx;
    private Sprite? _decor;
    private DecorHd? _decorHd;
    private bool _hd;
    private List<Theatre.Evenement> _evts = new();
    private double _debut;
    private double _glisse = -1;
    private string _cle = "";
    private int _regard;
    private long _dernierPas = -1;
    private uint _derniere;
    private double _largeur = Theatre.W * 5, _hauteur = Theatre.H * 5;

    // Le Pilou fin du bureau (HD) : rendu par RenduPilou avec l'allure du joueur, relue toutes les cinq secondes.
    private Func<PoseHd, uint[]>? _rendre;
    private double _allureLue = -1e12;

    public int Echelle { get; private set; } = 5;

    // La taille du lieu courant, en pixels de scène (192 × 80, ou 480 × 240 en HD).
    public int LargeurScene => _s.W;
    public int HauteurScene => _s.H;
    public bool Hd => _hd;

    public VueTheatre(Func<string> niveau, Func<uint[]> teinte, Func<Allure>? allure = null)
    {
        _niveau = niveau;
        _teinte = teinte;
        _allure = allure;
        _s = _ancienne;
        RenderOptions.SetBitmapScalingMode(_image, BitmapScalingMode.NearestNeighbor);
        _image.Source = _s.Bitmap;
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

    // La plus grande échelle entière qui tient dans la place donnée (au moins 2), pour la définition du lieu courant.
    public void Ajuster(double largeur, double hauteur)
    {
        _largeur = largeur;
        _hauteur = hauteur;
        int k = (int)Math.Max(2, Math.Min(Math.Floor(largeur / _s.W), Math.Floor(hauteur / _s.H)));
        Echelle = k;
        _image.Width = _s.W * k;
        _image.Height = _s.H * k;
    }

    // Change de surface (de définition) : la taille affichée suit.
    private void Surface_(bool hd)
    {
        var s = hd ? _hdSurface ??= new Surface(Theatre.Hd.W, Theatre.Hd.H) : _ancienne;
        if (ReferenceEquals(s, _s)) return;
        _s = s;
        _image.Source = s.Bitmap;
        _derniere = 0;
        Ajuster(_largeur, _hauteur);
        Redimensionne?.Invoke();
    }

    // La définition a changé : la fenêtre recalcule sa mise en page (hauteur de la scène, cadres).
    public event Action? Redimensionne;

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

    // Les sprites HD vus par le moteur commun (taille, nombre d'images) : leur silhouette, faite une fois.
    private static readonly Dictionary<string, Sprite?> Silhouettes = new();

    private static Sprite? Silhouette(string id)
    {
        lock (Silhouettes)
        {
            if (!Silhouettes.TryGetValue(id, out var s)) Silhouettes[id] = s = TheatreHd.SpriteHdDe(id)?.VersSprite();
            return s;
        }
    }

    public bool Pret => _cx is not null && _cx.P.Count > 0;

    // ---- Ce que la fenêtre raconte

    private long T(double now) => (long)Math.Max(0, now - _debut);

    private bool Vif => _niveau() == AnimationsCampagne.Completes;

    // Montre ce lieu (décor de la campagne) ; rend faux s'il n'a pas de dessin. glisser : un travelling depuis le lieu
    // précédent (faux quand la fenêtre rattrape d'un coup des messages déjà lus). Le HD est pris dès que le décor HD et
    // sa scène HD existent (docs/SCENES-HD.md, § 2).
    public bool Lieu(string campagne, string decor, double now, bool glisser = true)
    {
        var cle = campagne + "|" + decor;
        if (cle == _cle && _cx is not null) return _decor is not null || _decorHd is not null;
        var idDecor = "decor-" + campagne + "-" + decor;
        var decorHd = TheatreHd.ScenesHd(campagne).TryGetValue(decor, out var scHd) ? TheatreHd.Decor(idDecor) : null;
        var neuf = decorHd is null ? Illustrations.Decor(Banque.Commune, campagne, decor, 2) : null;
        if (decorHd is null && neuf is null) return false;
        bool hd = decorHd is not null;
        bool avait = _cx is not null && (_decor is not null || _decorHd is not null);
        glisser = glisser && avait && Vif && hd == _hd;
        if (glisser)
        {
            // Travelling : l'ancien lieu (sans Pilou) est gardé tel quel pour glisser.
            ComposerSansPilou(_s.Avant, now);
            _glisse = now;
        }
        _cle = cle;
        _hd = hd;
        _decor = neuf;
        _decorHd = decorHd;
        Surface_(hd);
        _cx = hd
            ? new Theatre.Contexte(scHd!, Anims(), Silhouette)
            : new Theatre.Contexte(SceneDe(campagne, decor), Anims(), id => Banque.Commune.Fins.GetValueOrDefault(id));
        _evts = new List<Theatre.Evenement>();
        _perso = "";
        _debut = glisser ? now + Glisse : now;
        if (!glisser) _glisse = -1;
        if (Vif) _evts.Add(new Theatre.Evenement(0, "entree", glisser ? Theatre.E(_cx.Scene, EntreeX) : 0));
        _dernierPas = -1;
        return true;
    }

    private void Ajouter(Theatre.Evenement e)
    {
        if (_cx is null || !Vif) return;          // pendant un travelling, l'événement tombe au début de la nouvelle scène
        if (_evts.Count > 0 && e.T < _evts[^1].T) e = e with { T = _evts[^1].T };
        _evts.Add(e);
        _dernierPas = -1;
    }

    public void Humeur(string humeur, double now) => Ajouter(new Theatre.Evenement(T(now), "humeur", Humeur: humeur));

    public void Parle(double now, double fin) => Ajouter(new Theatre.Evenement(T(now), "parle", T(fin)));

    public void Tait(double now)
    {
        Ajouter(new Theatre.Evenement(T(now), "parle", T(now)));
        if (_perso != "") Ajouter(new Theatre.Evenement(T(now), "parle-perso", T(now)));
    }

    // Le personnage en pied (pied-<campagne>-<personnage>) : il entre par la droite ; "" : il ressort.
    private string _perso = "", _persoHumeur = "";

    // humeur : l'expression du message ; en HD, le personnage prend la variante dessinée pour elle
    // (pied-<campagne>-<id>-<humeur>, même toile et même ancre), sinon sa version neutre.
    public void Perso(string sprite, double now, string humeur = "")
    {
        _persoHumeur = humeur;
        if (sprite == _perso) return;
        _perso = sprite;
        Ajouter(new Theatre.Evenement(T(now), "perso", Humeur: sprite));
    }

    private SpriteHd? SpriteHd(string id) =>
        id == _perso && _persoHumeur is { Length: > 0 } h && TheatreHd.SpriteHdDe(id + "-" + h) is { } v ? v : TheatreHd.SpriteHdDe(id);

    // Sa réplique : c'est lui qui parle, pas Pilou.
    public void ParlePerso(double now, double fin) => Ajouter(new Theatre.Evenement(T(now), "parle-perso", T(fin)));

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
        int dehors = _cx.Scene.D.W + Theatre.E(_cx.Scene, Theatre.SortieD - Theatre.W + 4);
        _evts = new List<Theatre.Evenement> { new(0, "entree", dehors), new(0, "depart", 1) };
        _glisse = -1;
        _debut = now;
        _dernierPas = -1;
    }

    // ---- Souris

    private (int X, int Y) Point(Point p)
    {
        double k = _image.ActualWidth > 0 ? _image.ActualWidth / _s.W : Echelle;
        return ((int)Math.Floor(p.X / k), (int)Math.Floor(p.Y / k));
    }

    private double _now;

    private void Souris(Point p)
    {
        if (_cx is null) return;
        var (x, y) = Point(p);
        var pi = Theatre.Pilou(_cx, _evts, T(_now));
        int seuil = Theatre.E(_cx.Scene, 14);
        _regard = x - pi.X > seuil ? 1 : x - pi.X < -seuil ? -1 : 0;
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

    // L'allure de base du Pilou fin : celle du joueur, relue toutes les cinq secondes ; le rendeur la copie à chaque image,
    // donc la métamorphose peut changer son stade et son évolution d'une image à l'autre.
    private Allure? _base;
    private (int Avant, int Apres, double Debut)? _metamorphose;
    public const double DureeMetamorphose = 4200;              // la même que l'évolution du bureau

    // La métamorphose (scènes d'évolution, docs/SCENES.md) : Pilou garde son ancien stade jusqu'à debut, puis le bureau
    // fond l'ancienne forme dans la nouvelle (Allure.Evolution de 0 à 1), puis il reste au nouveau stade.
    public void Metamorphose(int avant, int apres, double debut) => _metamorphose = (avant, apres, debut);

    private Func<PoseHd, uint[]> RendrePilou(double now)
    {
        if (_rendre is null || now - _allureLue > 5000)
        {
            _allureLue = now;
            _base = _allure?.Invoke().Copie() ?? new Allure();
            _rendre = TheatreHd.RendeurPilou(Banque.Commune, _base);
        }
        if (_metamorphose is { } m && _base is not null)
        {
            double f = (now - m.Debut) / DureeMetamorphose;
            _base.Stade = f < 0 ? m.Avant : m.Apres;
            _base.Evolution = f is > 0 and < 1 ? Math.Max(0.001, f) : 0;
        }
        return _rendre;
    }

    private void Composer(long t, string niveau, uint[] sortie, double now)
    {
        if (_hd) TheatreHd.ComposerHd(_decorHd, _cx!, SpriteHd, _evts, t, RendrePilou(now), _regard, niveau, sortie);
        else Theatre.Composer(_cx!, _decor, _teinte(), _evts, t, _regard, niveau, sortie);
    }

    // Le lieu sans Pilou ni événements (pour le travelling).
    private void ComposerSansPilou(uint[] sortie, double now)
    {
        if (_hd) TheatreHd.ComposerHd(_decorHd, _cx!, TheatreHd.SpriteHdDe, Array.Empty<Theatre.Evenement>(), 0, _ => Vide, 0, _niveau(), sortie);
        else Theatre.Composer(_cx!, _decor, _teinte(), _evts, T(now), 0, _niveau(), sortie, avecPilou: false);
    }

    private static readonly uint[] Vide = new uint[TheatreHd.PilouW * TheatreHd.PilouH];

    public void Avancer(double now)
    {
        _now = now;
        if (_cx is null) return;
        string niveau = _niveau();
        if (_glisse >= 0)
        {
            double f = (now - _glisse) / Glisse;
            if (f >= 1) _glisse = -1;
            else
            {
                Glisser(f, now);
                return;
            }
        }
        long t = T(now);
        long pas = t / Theatre.Pas;
        if (pas == _dernierPas && niveau == AnimationsCampagne.Completes) return;
        if (niveau != AnimationsCampagne.Completes && pas / 2 == _dernierPas / 2 && _dernierPas >= 0) return;
        _dernierPas = pas;
        Composer(t, niveau, _s.Px, now);
        uint h = Theatre.Fnv(_s.Px);
        if (h == _derniere) return;
        _derniere = h;
        Ecrire(_s.Px);
    }

    // Le travelling : décors côte à côte qui glissent (lissés) ; à l'ancienne définition, Pilou marche au milieu.
    private void Glisser(double f, double now)
    {
        double l = f * f * (3 - 2 * f);
        int w = _s.W, hh = _s.H;
        int dx = (int)Math.Round(-l * w);
        ComposerSansPilou(_s.Apres, now);
        for (int y = 0; y < hh; y++)
        for (int x = 0; x < w; x++)
        {
            int sx = x - dx;
            _s.Px[y * w + x] = sx < w ? _s.Avant[y * w + sx] : _s.Apres[y * w + sx - w];
        }
        if (!_hd && _cx!.P.TryGetValue("marche", out var m))
        {
            int px = EntreeX;
            Theatre.Poser(_s.Px, Banque.Commune.Fins.GetValueOrDefault(Theatre.IdPilou), m.Image((long)(f * Glisse)), px,
                Theatre.Sol(_cx.Scene, px), false, _teinte(), Theatre.PilouX, Theatre.PilouY);
        }
        _derniere = 0;
        Ecrire(_s.Px);
    }

    // ---- Le portrait de la boîte de dialogue : le mini-Pilou de scène (même dessin fin), agrandi d'un facteur entier
    // par la fenêtre ; il prend l'humeur du message, parle pendant l'écriture, cligne.

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

    // ---- En HD, les portraits de la boîte au pixel de la scène (docs/SCENES-HD.md) : le Pilou fin (son stade, son
    // allure, l'humeur du message, la bouche qui parle), recadré sur son corps ; et le buste du personnage, tiré de son
    // sprite HD en pied (la variante de l'humeur s'il y en a une). La fenêtre les affiche à l'échelle de la scène.

    // Le cadre du corps du Pilou fin dans sa grille 96 × 112, par stade (mesuré sur le rendu fin, marge d'une unité).
    private static (int X, int Y, int W, int H) CorpsPilou(int stade) => stade switch
    {
        1 => (24, 39, 48, 70),
        3 => (4, 26, 88, 86),
        4 => (7, 9, 82, 104),
        _ => (16, 20, 64, 89),
    };

    private PoseHd _dernierVisage;
    private int _dernierStade = -1;

    public BitmapSource? VisageHd(string humeur, bool parle, double now, bool toujours = false)
    {
        if (!_hd) return null;
        long t = (long)now;
        string niveau = _niveau();
        bool vif = niveau == AnimationsCampagne.Completes;
        var pose = new PoseHd(humeur is "" or "neutre" ? "repos" : humeur, vif ? t / Theatre.Pas * Theatre.Pas : 0, false,
            vif && parle && t / 140 % 2 == 0, niveau != AnimationsCampagne.Aucune && AnimationsCampagne.Cligne(t), 0, 0, false);
        var rendre = RendrePilou(now);
        int stade = _base?.Stade ?? 2;
        if (!toujours && pose == _dernierVisage && stade == _dernierStade) return null;
        _dernierVisage = pose;
        _dernierStade = stade;
        var g = rendre(pose);
        var (x0, y0, w, h) = CorpsPilou(stade);
        var crop = new uint[w * h];
        for (int y = 0; y < h; y++)
            Array.Copy(g, (y0 + y) * TheatreHd.PilouW + x0, crop, y * w, w);
        return Apercu.Bitmap(crop, w, h);
    }

    // Le buste du personnage en pied : le haut de son sprite HD (64 unités au plus), image de repos ou de parole.
    private string _busteVu = "";
    private int _busteImage = -1;

    public BitmapSource? BusteHd(bool parle, double now, bool toujours = false)
    {
        if (!_hd || _perso == "" || SpriteHd(_perso) is not { } s) return null;
        long t = (long)now;
        bool vif = _niveau() == AnimationsCampagne.Completes;
        int im = !vif ? 0 : parle && s.Images.Count >= 5 ? 3 + (int)(t / 140 % 2)
            : s.Images.Count >= 3 && AnimationsCampagne.Cligne(t + 1700) ? 2 : (int)(t / 900 % 2);
        im = Math.Min(im, s.Images.Count - 1);
        var cle = s.Id + "|" + _persoHumeur;
        if (!toujours && cle == _busteVu && im == _busteImage) return null;
        _busteVu = cle;
        _busteImage = im;
        // Le haut du sprite : on saute les rangées vides du dessus, puis 64 unités.
        var g = s.Images[im];
        int haut = 0;
        while (haut < s.H - 1 && Enumerable.Range(0, s.W).All(x => g[haut * s.W + x] == 0)) haut++;
        int h = Math.Min(64, s.H - haut);
        var crop = new uint[s.W * h];
        Array.Copy(g, haut * s.W, crop, 0, s.W * h);
        // Le dessin HD regarde à droite : retourné, il regarde Pilou (à gauche de la boîte).
        for (int y = 0; y < h; y++) Array.Reverse(crop, y * s.W, s.W);
        return Apercu.Bitmap(crop, s.W, h);
    }

    private void Ecrire(uint[] px) => _s.Bitmap.WritePixels(new Int32Rect(0, 0, _s.W, _s.H), px, _s.W * 4, 0);

    // Où poser un panneau de w × h pixels de scène (Theatre.PlacerPanneau) : coin haut-gauche en pixels de scène. gene :
    // ce que la fenêtre pose déjà sur la scène, en pixels de scène.
    public (int X, int Y) PlacerPanneau(int w, int h, double now, IReadOnlyList<(int X0, int Y0, int X1, int Y1)>? gene = null)
    {
        if (_cx is null) return (2, 9);
        var p = Theatre.Pilou(_cx, _evts, T(now));
        (int, int)? taille = null;
        if (_perso != "")
        {
            if (_hd && TheatreHd.SpriteHdDe(_perso) is { } sh) taille = (sh.W, sh.H);
            else if (!_hd && _cx.Sprites(_perso) is { Images.Count: > 0 } s && s.Images[0].Length > 0) taille = (s.Images[0][0].Length, s.Images[0].Length);
        }
        return Theatre.PlacerPanneau(_cx.Scene, w, h, p.X, _perso != "", taille, gene);
    }

    // Où est Pilou dans la scène, en coordonnées de ce contrôle (pour poser une bulle ou un choix à côté de lui).
    public Point PositionPilou(double now)
    {
        if (_cx is null) return new Point(0, 0);
        var p = Theatre.Pilou(_cx, _evts, T(now));
        double k = _image.ActualWidth > 0 ? _image.ActualWidth / _s.W : Echelle;
        return new Point(p.X * k, (p.Y - Theatre.E(_cx.Scene, 24)) * k);
    }
}
