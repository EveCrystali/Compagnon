using System.Globalization;

namespace PilouBureau;

// Le théâtre des campagnes (docs/SCENES.md) : la scène vivante de la fenêtre Aventure. Un décor fin (192 × 80) où
// vivent le mini-Pilou, des acteurs d'ambiance et les effets de réaction aux clics. Tout est calculé comme dans
// outils/sprites/theatre.py (référence) et Theatre.java : arithmétique entière, tables, même ordre des opérations ;
// TheatreTests.cs relit theatre-reference.txt. Rien ici ne dépend de WPF : la fenêtre ne fait que peindre l'image.
public static class Theatre
{
    public const int W = 192, H = 80;
    public const int Pas = 83;                  // douze images par seconde
    public const int Vitesse = 24;              // marche de Pilou, pixels fins par seconde
    public const int Entree = -14, SortieD = 206, SortieG = -14;
    public const string IdPilou = "scene-pilou";
    public const int PilouX = 17, PilouY = 33;  // ancre du sprite : centre, ligne des pieds
    private const int RegardCycle = 7000, RegardDebut = 3000, RegardDuree = 1200;
    private const int VolCycle = 1700, VolPose = 1190, FuiteVol = 1500, FuiteAbsent = 6000;
    public const int ClicsMax = 24;

    private static readonly int[] Sinus =
    {
        0, 195, 383, 556, 707, 831, 924, 981, 1000, 981, 924, 831, 707, 556, 383, 195,
        0, -195, -383, -556, -707, -831, -924, -981, -1000, -981, -924, -831, -707, -556, -383, -195,
    };
    private static readonly int[] LisseT = { 0, 11, 42, 89, 156, 229, 316, 410, 500, 590, 684, 771, 844, 911, 958, 989, 1000 };

    public static readonly string[] Humeurs = { "joie", "peur", "triste", "surpris", "determine", "fatigue", "tendre", "colere", "malice", "neutre" };

    private static long Div(long a, long b) => a / b;      // C# tronque vers zéro, comme la référence (div)

    private static int Lisse(long num, long den)
    {
        if (den <= 0 || num >= den) return 1000;
        if (num <= 0) return 0;
        return LisseT[num * 16 / den];
    }

    private static int Sin(long i) => Sinus[(int)(i % 32)];

    // ---- Scènes : assets/scenes/<campagne>.txt

    public sealed record Acteur(string Sprite, string Comportement, int[] P);

    public sealed record Sensible(string Nom, int X0, int Y0, int X1, int Y1, string Reaction, int[] P);

    public sealed class Scene
    {
        public string Nom { get; init; } = "";
        public (int X0, int Y0, int X1, int Y1) Sol { get; set; } = (0, 78, W, 78);
        public int Place { get; set; } = 24;
        public int Interlocuteur { get; set; } = 150;
        public List<Acteur> Acteurs { get; } = new();
        public List<Sensible> Sensibles { get; } = new();
    }

    private static IEnumerable<string[]> Mots(string texte)
    {
        foreach (var brut in texte.Replace("\r", "").Split('\n'))
        {
            int d = brut.IndexOf('#');
            var l = (d >= 0 ? brut[..d] : brut).Trim();
            if (l.Length > 0) yield return l.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        }
    }

    private static int Ent(string s) => int.Parse(s, CultureInfo.InvariantCulture);

    public static Dictionary<string, Scene> LireScenes(string texte)
    {
        var scenes = new Dictionary<string, Scene>();
        Scene? sc = null;
        foreach (var m in Mots(texte))
        {
            if (m[0] == "scene") scenes[m[1]] = sc = new Scene { Nom = m[1] };
            else if (sc is null) continue;
            else if (m[0] == "sol") sc.Sol = (Ent(m[1]), Ent(m[2]), Ent(m[3]), Ent(m[4]));
            else if (m[0] == "place") sc.Place = Ent(m[1]);
            else if (m[0] == "interlocuteur") sc.Interlocuteur = Ent(m[1]);
            else if (m[0] == "acteur") sc.Acteurs.Add(new Acteur("acteur-" + m[1], m[2], m.Skip(3).Select(Ent).ToArray()));
            else if (m[0] == "sensible")
                sc.Sensibles.Add(new Sensible(m[1], Ent(m[2]), Ent(m[3]), Ent(m[4]), Ent(m[5]), m[6], m.Skip(7).Select(Ent).ToArray()));
        }
        return scenes;
    }

    public static int Sol(Scene sc, int x)
    {
        var (x0, y0, x1, y1) = sc.Sol;
        if (x <= x0 || x1 == x0) return y0;
        if (x >= x1) return y1;
        return y0 + (int)Div((long)(y1 - y0) * (x - x0), x1 - x0);
    }

    // ---- Animations nommées : assets/scenes/animations.txt

    public readonly record struct Anim(int Premiere, int Nombre, int Pas, bool Boucle)
    {
        public int Duree => Nombre * Pas;
        public int Image(long dt)
        {
            if (dt < 0) dt = 0;
            long k = dt / Pas;
            return Premiere + (int)(Boucle ? k % Nombre : Math.Min(k, Nombre - 1));
        }
    }

    public static Dictionary<string, Dictionary<string, Anim>> LireAnimations(string texte)
    {
        var a = new Dictionary<string, Dictionary<string, Anim>>();
        foreach (var m in Mots(texte))
        {
            if (m.Length < 6) continue;
            if (!a.TryGetValue(m[0], out var d)) a[m[0]] = d = new();
            d[m[1]] = new Anim(Ent(m[2]), Ent(m[3]), Ent(m[4]), m[5] == "boucle");
        }
        return a;
    }

    // ---- Événements : entree (A : x de départ, 0 : le bord gauche), depart (A : +1 droite, -1 gauche), humeur
    // (Humeur), parle (A : fin de la réplique ; une nouvelle réplique remplace la précédente, A = T la coupe), clic
    // (A, B : point touché en pixels du décor). Toujours ajoutés dans l'ordre du temps.

    public readonly record struct Evenement(long T, string Sorte, long A = 0, long B = 0, string Humeur = "");

    // Ce que la scène sait calculer : la scène, les animations, la durée d'image de chaque sprite d'acteur.
    // Les clics déjà résolus sont gardés (la liste d'événements ne fait que s'allonger).
    public sealed class Contexte
    {
        public Scene Scene { get; }
        public Dictionary<string, Anim> P { get; }
        public Func<string, Sprite?> Sprites { get; }
        private readonly Dictionary<int, Cible> _cibles = new();
        private int _evtsVus = -1;
        private IReadOnlyList<Evenement>? _liste;

        public Contexte(Scene scene, Dictionary<string, Dictionary<string, Anim>> anims, Func<string, Sprite?> sprites)
        {
            Scene = scene;
            P = anims.TryGetValue(IdPilou, out var p) ? p : new();
            Sprites = sprites;
        }

        public int Duree(string sid) => Sprites(sid)?.Duree ?? 100;

        // Le clic evts[k] ne dépend que de ce qui le précède : on le garde tant que la liste de base ne change pas en
        // amont (une nouvelle liste, ou une liste raccourcie, vide le cache).
        internal Cible CibleDe(IReadOnlyList<Evenement> evts, int k)
        {
            var base_ = evts is Prefixe p ? p.Base : evts;
            if (!ReferenceEquals(base_, _liste) || base_.Count < _evtsVus)
            {
                _cibles.Clear();
                _liste = base_;
            }
            _evtsVus = base_.Count;
            if (_cibles.TryGetValue(k, out var c)) return c;
            var e = evts[k];
            return _cibles[k] = CibleA(this, new Prefixe(evts, k), e.T, (int)e.A, (int)e.B);
        }
    }

    // Les k premiers événements d'une liste, sans copie.
    private sealed class Prefixe : IReadOnlyList<Evenement>
    {
        private readonly IReadOnlyList<Evenement> _l;
        public Prefixe(IReadOnlyList<Evenement> l, int n)
        {
            _l = l is Prefixe p ? p._l : l;
            Count = n;
        }
        public IReadOnlyList<Evenement> Base => _l;
        public int Count { get; }
        public Evenement this[int i] => _l[i];
        public IEnumerator<Evenement> GetEnumerator()
        {
            for (int i = 0; i < Count; i++) yield return _l[i];
        }
        System.Collections.IEnumerator System.Collections.IEnumerable.GetEnumerator() => GetEnumerator();
    }

    internal readonly record struct Cible(string Sorte, int I, string Reaction, int X);

    private static List<int> Clics(IReadOnlyList<Evenement> evts)
    {
        var c = new List<int>();
        for (int i = 0; i < evts.Count; i++)
            if (evts[i].Sorte == "clic") c.Add(i);
        return c.Count > ClicsMax ? c.GetRange(c.Count - ClicsMax, ClicsMax) : c;
    }

    private static string Face(string humeur) =>
        humeur is "" or "neutre" || Array.IndexOf(Humeurs, humeur) < 0 ? "repos" : "repos-" + humeur;

    // ---- Le mini-Pilou : (x au centre, y la ligne des pieds, image, miroir, visible)

    public readonly record struct EtatPilou(int X, int Y, int Image, bool Miroir, bool Visible);

    private struct Action
    {
        public string? Sorte;  // null ou "" : aucune ; "marche" ; "anim"
        public long T0;
        public int X0, X1;
        public string? Nom;
        public long Duree;
    }

    public static EtatPilou Pilou(Contexte cx, IReadOnlyList<Evenement> evts, long t, int regard = 0, string niveau = AnimationsCampagne.Completes)
    {
        var sc = cx.Scene;
        var P = cx.P;
        int x = sc.Place;
        string humeur = "neutre";
        if (niveau != AnimationsCampagne.Completes)
        {
            foreach (var e in evts)
                if (e.T <= t && e.Sorte == "humeur") humeur = e.Humeur;
            int im = P[Face(humeur)].Premiere;
            if (niveau == AnimationsCampagne.Reduites && AnimationsCampagne.Cligne(t)) im = P["cligne"].Premiere;
            return new EtatPilou(x, Sol(sc, x), im, x > W / 2, true);
        }
        var action = new Action { Sorte = "" };
        bool parti = false;
        var paroles = new List<(long, long)>();

        void Finir(long jusque)
        {
            if (action.Sorte == "marche")
            {
                long fait = (jusque - action.T0) * Vitesse / 1000;
                if (fait >= Math.Abs(action.X1 - action.X0))
                {
                    x = action.X1;
                    parti = action.X1 >= SortieD || action.X1 <= SortieG;
                    action.Sorte = "";
                }
            }
            else if (action.Sorte == "anim" && jusque - action.T0 >= action.Duree) action.Sorte = "";
        }

        int Position(long jusque)
        {
            if (action.Sorte != "marche") return x;
            long fait = (jusque - action.T0) * Vitesse / 1000;
            return (int)(action.X1 >= action.X0 ? action.X0 + fait : action.X0 - fait);
        }

        var vus = new HashSet<int>(Clics(evts));
        int nPilou = 0;
        for (int ie = 0; ie < evts.Count; ie++)
        {
            var e = evts[ie];
            if (e.T > t) break;
            Finir(e.T);
            switch (e.Sorte)
            {
                case "entree":
                {
                    int x0 = e.A != 0 ? (int)e.A : Entree;     // A : d'où il entre (0 : du bord gauche)
                    x = x0;
                    parti = false;
                    action = new Action { Sorte = "marche", T0 = e.T, X0 = x0, X1 = sc.Place };
                    break;
                }
                case "depart":
                {
                    x = Position(e.T);
                    action = new Action { Sorte = "marche", T0 = e.T, X0 = x, X1 = e.A >= 0 ? SortieD : SortieG };
                    break;
                }
                case "humeur":
                    humeur = Array.IndexOf(Humeurs, e.Humeur) >= 0 ? e.Humeur : "neutre";
                    if (action.Sorte is "" or "anim" && humeur is "joie" or "surpris")
                        action = new Action { Sorte = "anim", T0 = e.T, Nom = humeur, Duree = P[humeur].Duree };
                    break;
                case "parle":
                    paroles.Clear();                           // une nouvelle réplique remplace la précédente
                    paroles.Add((e.T, e.A));
                    break;
                case "clic" when vus.Contains(ie):
                {
                    if (parti || action.Sorte == "marche") break;
                    var c = cx.CibleDe(evts, ie);
                    if (c.Sorte == "pilou")
                    {
                        string nom = nPilou % 2 == 0 ? "joie" : "coucou";
                        nPilou++;
                        action = new Action { Sorte = "anim", T0 = e.T, Nom = nom, Duree = P[nom].Duree };
                    }
                    else if (c.Sorte == "sensible" && c.Reaction == "bulle")
                        action = new Action { Sorte = "anim", T0 = e.T, Nom = "surpris", Duree = P["surpris"].Duree + 1200 };
                    else if (c.Sorte is "sensible" or "acteur")
                        action = new Action { Sorte = "anim", T0 = e.T, Nom = c.X >= x ? "regard-d" : "regard-g", Duree = 900 };
                    break;
                }
            }
        }
        Finir(t);
        if (parti) return new EtatPilou(x, Sol(sc, x), P[Face(humeur)].Premiere, false, false);
        if (action.Sorte == "marche")
        {
            int px = Position(t);
            return new EtatPilou(px, Sol(sc, px), P["marche"].Image(t - action.T0), action.X1 < action.X0, true);
        }
        bool miroir = x > W / 2;
        int y = Sol(sc, x);
        if (action.Sorte == "anim")
        {
            var nom = action.Nom ?? "repos";
            if (nom == "surpris" && t - action.T0 >= P["surpris"].Duree) return new EtatPilou(x, y, P["repos-peur"].Image(t - action.T0), miroir, true);
            if (nom is "regard-d" or "regard-g") return new EtatPilou(x, y, P[nom].Premiere, false, true);
            return new EtatPilou(x, y, P[nom].Image(t - action.T0), miroir, true);
        }
        foreach (var (t0, t1) in paroles)
            if (t0 <= t && t < t1) return new EtatPilou(x, y, P["parle"].Image(t - t0), miroir, true);
        if (AnimationsCampagne.Cligne(t)) return new EtatPilou(x, y, P["cligne"].Premiere, miroir, true);
        if (regard != 0) return new EtatPilou(x, y, P[regard > 0 ? "regard-d" : "regard-g"].Premiere, false, true);
        long cy = t / RegardCycle, u = t % RegardCycle;
        if (AnimationsCampagne.Hasard(cy, 11, 3) < 4000 && u >= RegardDebut && u < RegardDebut + RegardDuree)
        {
            var nom = AnimationsCampagne.Hasard(cy, 12, 3) < 5000 ? "regard-g" : "regard-d";
            return new EtatPilou(x, y, P[nom].Premiere, false, true);
        }
        return new EtatPilou(x, y, P[Face(humeur)].Image(t), miroir, true);
    }

    // ---- Les acteurs : (x au centre, y la ligne du bas, image ou -1 s'il est absent, miroir)

    public readonly record struct Pose(string Sprite, int Image, int X, int Y, bool Miroir);

    private static List<long> Fuites(Contexte cx, IReadOnlyList<Evenement> evts, int i, long t)
    {
        var f = new List<long>();
        foreach (var k in Clics(evts))
        {
            if (evts[k].T > t) continue;
            var c = cx.CibleDe(evts, k);
            if (c.Sorte == "acteur" && c.I == i) f.Add(evts[k].T);
        }
        return f;
    }

    private static (int X, int Y, bool Miroir) Vol(int[] p, long t)
    {
        int x0 = p[0], y0 = p[1], x1 = p[2], y1 = p[3], g = p[4];
        long c = t / VolCycle, u = t % VolCycle;
        int ax = x0 + AnimationsCampagne.Hasard(c, 1, g) * (x1 - x0) / 10000;
        int ay = y0 + AnimationsCampagne.Hasard(c, 2, g) * (y1 - y0) / 10000;
        int bx = x0 + AnimationsCampagne.Hasard(c + 1, 1, g) * (x1 - x0) / 10000;
        int by = y0 + AnimationsCampagne.Hasard(c + 1, 2, g) * (y1 - y0) / 10000;
        int f = u < VolPose ? 0 : Lisse(u - VolPose, VolCycle - VolPose);
        int x = ax + (int)Div((long)(bx - ax) * f, 1000);
        int y = ay + (int)Div((long)(by - ay) * f, 1000) + (int)Div(Sin(t / 140), 700);
        return (x, y, bx < ax);
    }

    internal static (int X, int Y, int Image, bool Miroir) PositionActeur(Contexte cx, IReadOnlyList<Evenement> evts, int i, long t)
    {
        var a = cx.Scene.Acteurs[i];
        var p = a.P;
        long duree = Math.Max(1, cx.Duree(a.Sprite));
        var fuites = a.Comportement is "vol" or "traverse" ? Fuites(cx, evts, i, t) : new List<long>();
        switch (a.Comportement)
        {
            case "vol":
            {
                for (int k = fuites.Count - 1; k >= 0; k--)
                {
                    long tf = fuites[k];
                    if (t < tf + FuiteAbsent)
                    {
                        if (t >= tf + FuiteVol) return (0, 0, -1, false);
                        var (fx, fy, _) = Vol(p, tf);
                        int d = fx < W / 2 ? 1 : -1;
                        return ((int)(fx - d * ((t - tf) * 90 / 1000)), (int)(fy - (t - tf) * 30 / 1000), (int)(t / duree), d > 0);
                    }
                }
                var (x, y, m) = Vol(p, t);
                return (x, y, (int)(t / duree), m);
            }
            case "traverse":
            {
                int y0 = p[0], y1 = p[1], periode = p[2], decalage = p[3], vitesse = p[4];
                long tt = t + decalage, c = tt / periode, u = tt % periode;
                long x = -12 + u * vitesse / 1000;
                long y = y0 + AnimationsCampagne.Hasard(c, 3, 5) * (y1 - y0) / 10000 + Div(Sin(t / 160), 800);
                foreach (var tf in fuites)
                    if ((tf + decalage) / periode == c)
                    {
                        x += (t - tf) * 60 / 1000;
                        y -= (t - tf) * 25 / 1000;
                    }
                if (x > W + 12 || y < -8) return (0, 0, -1, false);
                return ((int)x, (int)y, (int)(t / duree), false);
            }
            case "rond":
            {
                long u = (t + p[3]) % p[2];
                if (u >= 5 * 280) return (0, 0, -1, false);
                return (p[0], p[1], (int)(u / 280), false);
            }
            case "saut":
            {
                long u = (t + p[3]) % p[2];
                if (u >= 700) return (0, 0, -1, false);
                long f = u * 1000 / 700;
                long arc = 12 * 4 * f * (1000 - f) / 1000000;
                return ((int)(p[0] + 20 * f / 1000), (int)(p[1] - arc), f < 400 ? 0 : f < 600 ? 1 : 2, false);
            }
            case "pose":
                return (p[0], p[1], (int)(t / duree), false);
            case "flotte":
            {
                long u = (t + p[3]) % p[2];
                long px = p[0] + Div(u * p[4], 1000) + Div(Sin(u / 200) * 2L, 1000);
                long py = p[1] + Div(u * p[5], 1000);
                if (px < -8 || px > W + 8 || py < -8 || py > H + 8) return (0, 0, -1, false);
                return ((int)px, (int)py, (int)(t / duree), false);
            }
            case "chute":
            {
                long u = (t + p[3]) % p[2];
                long py = p[1] + u * 14 / 1000;
                long px = p[0] + Div(Sin(u / 150) * 4L, 1000);
                if (py > H + 4) return (0, 0, -1, false);
                return ((int)px, (int)py, (int)(u / duree), false);
            }
        }
        return (0, 0, -1, false);
    }

    private static Cible CibleA(Contexte cx, IReadOnlyList<Evenement> avant, long tc, int x, int y)
    {
        var sc = cx.Scene;
        var p = Pilou(cx, avant, tc);
        if (p.Visible && Math.Abs(x - p.X) <= 10 && y >= p.Y - 22 && y <= p.Y + 1) return new Cible("pilou", 0, "", p.X);
        for (int i = 0; i < sc.Acteurs.Count; i++)
        {
            if (sc.Acteurs[i].Comportement is not ("vol" or "traverse")) continue;
            var (ax, ay, im, _) = PositionActeur(cx, avant, i, tc);
            if (im >= 0 && Math.Abs(x - ax) <= 6 && y >= ay - 7 && y <= ay + 2) return new Cible("acteur", i, "", 0);
        }
        for (int j = 0; j < sc.Sensibles.Count; j++)
        {
            var s = sc.Sensibles[j];
            if (x >= s.X0 && x <= s.X1 && y >= s.Y0 && y <= s.Y1) return new Cible("sensible", j, s.Reaction, x);
        }
        return new Cible("rien", 0, "", 0);
    }

    // Le point touché répond-il au clic (pour la main au survol) ?
    public static bool Repond(Contexte cx, IReadOnlyList<Evenement> evts, long t, int x, int y)
    {
        var c = CibleA(cx, evts, t, x, y);
        return c.Sorte != "rien";
    }

    public static List<Pose> Acteurs(Contexte cx, IReadOnlyList<Evenement> evts, long t, string niveau = AnimationsCampagne.Completes)
    {
        var o = new List<Pose>();
        if (niveau != AnimationsCampagne.Completes) return o;
        var sc = cx.Scene;
        for (int i = 0; i < sc.Acteurs.Count; i++)
        {
            var (x, y, im, m) = PositionActeur(cx, evts, i, t);
            if (im < 0 || cx.Sprites(sc.Acteurs[i].Sprite) is not { } s || s.Images.Count == 0) continue;
            o.Add(new Pose(sc.Acteurs[i].Sprite, im % s.Images.Count, x, y, m));
        }
        return o;
    }

    private static readonly int[] Bulle = { 0, 1, 2, 1, 2, 3, 0 };

    public static List<Pose> Effets(Contexte cx, IReadOnlyList<Evenement> evts, long t, string niveau = AnimationsCampagne.Completes)
    {
        var o = new List<Pose>();
        if (niveau != AnimationsCampagne.Completes) return o;
        var sc = cx.Scene;
        var ronds = new Dictionary<int, int>();
        foreach (var k in Clics(evts))
        {
            var e = evts[k];
            long tc = e.T;
            if (tc > t) break;
            long dt = t - tc;
            var c = cx.CibleDe(evts, k);
            int ex = (int)e.A, ey = (int)e.B;
            if (c.Sorte == "pilou" && dt < 350)
            {
                var p = Pilou(cx, new Prefixe(evts, k), tc);
                o.Add(new Pose("acteur-eclats", (int)(dt / 70), p.X, p.Y - 24, false));
            }
            else if (c.Sorte == "sensible")
            {
                var pr = sc.Sensibles[c.I].P;
                if (c.Reaction == "bulle" && dt < 1050) o.Add(new Pose("acteur-bulle", Bulle[dt / 150], pr[0], pr[1], false));
                if (c.Reaction == "bulle" && dt < 1100)
                    o.Add(new Pose("acteur-note", (int)(t / 180 % 2), pr[0] + 5, (int)(pr[1] - 5 - dt * 10 / 1000), false));
                if (c.Reaction == "rond")
                {
                    ronds[c.I] = ronds.GetValueOrDefault(c.I) + 1;
                    if (dt < 1400) o.Add(new Pose("acteur-rond", (int)(dt / 280), ex, ey + 2, false));
                    if (ronds[c.I] % 3 == 0 && dt < 700)
                    {
                        long f = dt * 1000 / 700;
                        long arc = 12 * 4 * f * (1000 - f) / 1000000;
                        o.Add(new Pose("acteur-poisson", f < 400 ? 0 : f < 600 ? 1 : 2, (int)(ex + 20 * f / 1000), (int)(ey - arc), false));
                        if (dt < 360) o.Add(new Pose("acteur-plouf", (int)(dt / 90), ex, ey, false));
                    }
                    if (ronds[c.I] % 3 == 0 && dt >= 700 && dt < 1060) o.Add(new Pose("acteur-plouf", (int)((dt - 700) / 90), ex + 20, ey, false));
                }
                if (c.Reaction == "graines" && dt < 4000)
                    for (int g = 0; g < 5; g++)
                    {
                        int vx = -8 - g * 3, vy = -6 + g * 2;
                        long gx = pr[0] + Div(dt * vx, 1000) + Div(Sin(dt / 200 + g * 5) * 2L, 1000);
                        long gy = pr[1] + Div(dt * vy, 1000);
                        o.Add(new Pose("acteur-graine", (int)((t / 300 + g) % 2), (int)gx, (int)gy, false));
                    }
            }
        }
        o.RemoveAll(q => cx.Sprites(q.Sprite) is null);
        return o;
    }

    // ---- Le compositeur : décor, puis acteurs et Pilou triés par leurs pieds, puis les effets.

    // teinte : contour, ombre, base, clair (ARGB) pour les couleurs @ du mini-Pilou.
    public static void Poser(uint[] px, Sprite? s, int im, int x, int y, bool miroir, uint[] teinte, int? ancreX = null, int? ancreY = null)
    {
        if (s is null || s.Images.Count == 0) return;
        var g = s.Images[((im % s.Images.Count) + s.Images.Count) % s.Images.Count];
        var pal = s.Compilee();
        int w = s.W, h = s.H;
        int ax = ancreX ?? w / 2, ay = ancreY ?? h - 1;
        int ox = x - (miroir ? w - 1 - ax : ax), oy = y - ay;
        for (int j = 0; j < g.Length; j++)
        {
            int Y = oy + j;
            if (Y < 0 || Y >= H) continue;
            var ligne = g[j];
            for (int i = 0; i < ligne.Length; i++)
            {
                char ch = ligne[i];
                if (ch == '.' || ch >= 128) continue;
                int X = ox + (miroir ? w - 1 - i : i);
                if (X < 0 || X >= W) continue;
                uint c = pal[ch];
                if (c is >= 1 and <= 4) c = teinte[c - 1] | 0xFF000000;
                uint a = c >> 24;
                if (a == 0) continue;
                int k = Y * W + X;
                if (a == 255) px[k] = c;
                else
                {
                    uint d = px[k];
                    uint r = ((c >> 16 & 255) * a + (d >> 16 & 255) * (255 - a) + 127) / 255;
                    uint v = ((c >> 8 & 255) * a + (d >> 8 & 255) * (255 - a) + 127) / 255;
                    uint b = ((c & 255) * a + (d & 255) * (255 - a) + 127) / 255;
                    px[k] = 0xFF000000 | r << 16 | v << 8 | b;
                }
            }
        }
    }

    // avecPilou : faux pendant un travelling (la fenêtre pose Pilou elle-même par-dessus les deux décors qui glissent).
    public static uint[] Composer(Contexte cx, Sprite? decor, uint[] teinte, IReadOnlyList<Evenement> evts, long t, int regard = 0,
        string niveau = AnimationsCampagne.Completes, uint[]? sortie = null, bool avecPilou = true)
    {
        var px = sortie is { Length: W * H } ? sortie : new uint[W * H];
        Array.Fill(px, 0xFF000000u);
        if (decor is not null && decor.Images.Count > 0)
        {
            int k = (int)AnimationsCampagne.ImageDecor(decor.Images.Count, decor.Duree, t, niveau);
            Poser(px, decor, k, 0, 0, false, teinte, 0, 0);
        }
        var poses = new List<(int Y, int Z, Pose P)>();
        foreach (var a in Acteurs(cx, evts, t, niveau)) poses.Add((a.Y, 0, a));
        var p = Pilou(cx, evts, t, regard, niveau);
        if (p.Visible && avecPilou) poses.Add((p.Y, 1, new Pose(IdPilou, p.Image, p.X, p.Y, p.Miroir)));
        // Tri stable par (pieds, Pilou après les acteurs à égalité), comme la référence.
        var tries = poses.Select((q, i) => (q, i)).OrderBy(q => q.q.Y).ThenBy(q => q.q.Z).ThenBy(q => q.i).Select(q => q.q);
        foreach (var (_, _, q) in tries)
        {
            if (q.Sprite == IdPilou) Poser(px, cx.Sprites(IdPilou), q.Image, q.X, q.Y, q.Miroir, teinte, PilouX, PilouY);
            else Poser(px, cx.Sprites(q.Sprite), q.Image, q.X, q.Y, q.Miroir, teinte);
        }
        foreach (var q in Effets(cx, evts, t, niveau)) Poser(px, cx.Sprites(q.Sprite), q.Image, q.X, q.Y, q.Miroir, teinte);
        return px;
    }

    public static uint Fnv(uint[] px)
    {
        uint h = 0x811C9DC5;
        foreach (var v in px)
            for (int s = 0; s < 32; s += 8)
            {
                h ^= v >> s & 255;
                h *= 0x01000193;
            }
        return h;
    }
}
