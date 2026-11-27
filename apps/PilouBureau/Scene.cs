using System.Windows;
using System.Windows.Media;
using System.Windows.Media.Imaging;

namespace PilouBureau;

// Ce que la fenêtre demande de dessiner à un instant donné.
public sealed class Pose
{
    public Expr Expr;
    // Objets de la boutique portés, par emplacement (tete, yeux, cou, dos, main, compagnon, effet, couleur → id).
    public IReadOnlyDictionary<string, string> Equipe = new Dictionary<string, string>();
    // Stade d'évolution affiché (1 Gouttelette, 2 Pilou, 3 Pilou Nimbus, 4 Pilou Astral) et, pendant une
    // évolution, sa progression 0..1 (de Stade - 1 vers Stade) ; 0 hors évolution.
    public int Stade = 2;
    public double Evolution;
    public double T;            // horloge de l'animation (ms)
    public double Depuis;       // ms depuis le début de l'humeur passagère
    public int Regard;          // -1, 0, 1
    public bool Cligne;
    public bool Clin;
    public bool Fatigue;
    public bool Marche;
    public double Saut;         // en « anciens » pixels (1 = 5 unités WPF)
    public double Tremble;
    public double Chute;        // 0..1 : écrasement à l'atterrissage
    public double Assis;        // 0..1 : posé au sol, pieds rentrés
    public bool Baille;
    public int RegardY;         // -1 regarde en haut, 1 en bas
    public bool Salue;          // antenne qui s'agite (une session vient de finir)
    public Accessoire Accessoire;
    public bool Course;         // il court (pas rapides, petits nuages de poussière)
    public bool Etourdi;        // la souris l'a secoué : yeux en spirale, étoiles
    public double Zoom = 1;     // > 1 : il se colle à l'écran (toque)
    public double Toque;        // 0..1 : phase du « toc »
    public double Suspendu;     // 0..1 : accroché au curseur par l'antenne
    public bool Balle;
    public double BalleX;       // position de la balle depuis son centre (anciens pixels)
    public double BalleRot;     // rotation de la balle (radians)
    public Couleur Couleur;
    // Humeur imposée (campagnes) : « joie », « peur », « triste », « surpris », « determine », « fatigue », « tendre »,
    // « colere », « malice », « neutre » ; "" : celle de Expr.
    public string Humeur = "";
    public bool Trainee;        // traînée d'étoiles quand il marche (récompense)
    // Activité reconnue (Activites.Toutes : code, tableur, jeu-mmo, jeu, musique, video, lecture, dessin,
    // visio, nuit, mail, texte, diaporama) : la tenue à dessiner ; "" = aucune. Tenues de voyage des campagnes :
    // « voyage-marche », « voyage-course », « voyage-bateau », « voyage-grimpe », « voyage-nage », « voyage-nuit »,
    // « voyage-cache », « voyage-attend » (le rendu impose alors la pose : RenduPilou.Voyager).
    public string Tenue = "";
    // Petite réaction liée à l'activité : "danse" (musique), "sueur" (processeur chargé pendant le code), "".
    public string Reaction = "";
    // Soins : sprites en plus (variante d'évolution, rayonnement, mousse de la toilette, bouderie) ; il boude
    // (moue, sourcils froncés) ; il tourne le dos (ni visage, ni lunettes).
    public IReadOnlyList<string> Soins = Array.Empty<string>();
    public bool Boude, Dos;
    // Effets météo dessinés sur Pilou (sprites « meteo-… » : pluie, mouillé, neige, givre, soleil…).
    public IReadOnlyList<string> Meteo = Array.Empty<string>();
    // Parti en visite chez un ami : la pancarte remplace Pilou ; deux lignes écrites dessus (« chez Léo »,
    // « ↩ 14 h 20 »). "" : Pilou est là.
    public string Pancarte = "";
    // Petits gestes (Gestes.cs) : sprites en plus (pouf, mini clavier, appareil, polaroïd, enveloppe) ; flash de
    // l'appareil (0..1 : cadre blanc atténué autour de Pilou) ; bruitage écrit en pixels (« CLIC ! »).
    public IReadOnlyList<string> Gestes = Array.Empty<string>();
    public double Flash;
    public string Bruit = "";
}

// Pilou en pixel art, grille de 48 × 56 commune avec l'app Android (RenduPilou), ou sa version fine de 96 × 112
// (Finesse : réglage « Dessin fin »), affichée en pixels nets à la même place. Les effets (Z, confettis, étoiles…) restent dessinés ici, alignés sur
// la même grille. Les grandeurs du mouvement (Saut, BalleX…) restent en « anciens » pixels de 5 unités.
// Seuls les pixels dessinés prennent la souris.
public sealed class Scene : FrameworkElement
{
    // Pixel de l'ancienne grille (26 × 30) : unité des positions des effets et de Pixels par défaut.
    // (Valeurs communes avec Placement.cs, la géométrie testable sans WPF.)
    public const double P = Placement.P;
    // « Ancien » pixel (5 unités WPF), unité des déplacements de la fenêtre.
    public const double PA = Placement.PA;
    public const int W = Placement.W;
    public const int H = Placement.H;
    public const double MargeX = Placement.MargeX;
    public const double MargeY = Placement.MargeY;
    // Pixel de la grille fine : 48 × 56 sur la même largeur que l'ancienne grille.
    public const double PX = Placement.PX;
    private const double E = 1.25;      // anciens pixels → pixels de l'ancienne grille
    private const double C = 13;        // axe du corps dans l'ancienne grille
    private const double F = RenduPilou.W / (double)W; // ancienne grille → grille fine
    public static double Largeur => Placement.LargeurScene;
    public static double Hauteur => Placement.HauteurScene;
    // Ordonnée des pieds dans la scène.
    public static double Sol => Placement.SolScene;

    // Repères du dernier dessin (grille fine) : la main qui tient la canne, par exemple (Placement.MainDe).
    public Geometrie Geo { get; private set; }

    private readonly List<(int X, int Y, uint C)> _debord = new();

    public Pose Pose { get; set; } = new();

    private uint[]? _pixels;
    private int _echelle = 1;      // échelle du dernier rendu (1 : 48 × 56 ; 2 : 96 × 112)
    private double _zoom = 1;
    // Image gardée d'un rendu à l'autre : rien n'est alloué par image, et le bitmap n'est réécrit que si des pixels
    // ont changé (Pilou respire lentement : la plupart des images sont identiques à la précédente).
    private readonly TamponRendu _tampon = new();
    private WriteableBitmap? _image;
    private uint[] _affiche = Array.Empty<uint>();
    private bool _imagePleine;

    public Scene()
    {
        RenderOptions.SetBitmapScalingMode(this, BitmapScalingMode.NearestNeighbor);
        RenderOptions.SetEdgeMode(this, EdgeMode.Aliased);
    }

    private static SolidColorBrush B(string hex)
    {
        var b = new SolidColorBrush((Color)ColorConverter.ConvertFromString(hex));
        b.Freeze();
        return b;
    }

    private sealed record Teinte(Brush Contour, Brush Ombre, Brush Base, Brush Clair);

    private static readonly Teinte Bleu = new(B("#1f4f8a"), B("#4a8fdc"), B("#6cb6ff"), B("#b4dbff"));
    private static readonly Brush Encre = B("#1c2128");
    private static readonly Brush Blanc = B("#ffffff");
    private static readonly Brush Etincelle = B("#f69d50");
    private static readonly Brush EtincelleClair = B("#ffd8b0");
    private static readonly Brush Gris = B("#768390");
    private static readonly Brush Brume = B("#adbac7");

    // Un pixel de l'ancienne grille, posé sur la grille fine (2 × 2 pixels fins) : les effets gardent leur
    // taille et restent alignés sur les mêmes pixels que Pilou.
    private static Rect Case(double x, double y) =>
        new(MargeX + Math.Round(x * F) * PX, MargeY + Math.Round(y * F) * PX, 2 * PX, 2 * PX);

    // Carré de grille sous un point en unités WPF (pour les effets, qui restent alignés sur les pixels).
    private static void Grain(DrawingContext dc, double x, double y, Brush br, double taille = P)
    {
        double gx = MargeX + Math.Floor((x - MargeX) / taille) * taille, gy = MargeY + Math.Floor((y - MargeY) / taille) * taille;
        dc.DrawRectangle(br, null, new Rect(gx, gy, taille, taille));
    }

    // Texte en police pixel (Pixels.Texte), contour sombre, à la taille de pixel voulue.
    private static void TextePixel(DrawingContext dc, string texte, double x, double y, double taille, Brush br, Brush? contour)
    {
        var m = Pixels.Texte(texte);
        int h = m.GetLength(0), w = m.GetLength(1);
        bool Plein(int r, int c) => r >= 0 && c >= 0 && r < h && c < w && m[r, c] > 0;
        for (int r = -1; r <= h; r++)
        for (int c = -1; c <= w; c++)
        {
            Brush? b = Plein(r, c) ? br : contour is not null && (Plein(r - 1, c) || Plein(r + 1, c) || Plein(r, c - 1) || Plein(r, c + 1)) ? contour : null;
            if (b is not null) dc.DrawRectangle(b, null, new Rect(x + c * taille, y + r * taille, taille, taille));
        }
    }

    // Ce que la Pose demande, traduit pour le rendu commun.
    public static Allure Allure(Pose p)
    {
        // Objets de boutique portés (un par emplacement) ; la couleur achetée remplace la couleur de niveau.
        var objets = p.Equipe.Where(kv => Boutique.SurPilou(kv.Key) && kv.Value != "").Select(kv => kv.Value).ToList();
        var couleurAchetee = p.Equipe.GetValueOrDefault(Boutique.Couleur, "");
        // Anciennes couleurs de niveau (« couleur-ambre ») : la teinte porte le nom sans préfixe.
        if (couleurAchetee.StartsWith("couleur-")) couleurAchetee = couleurAchetee["couleur-".Length..];
        if (p.Reaction == "danse" && p.Tenue != "musique") objets.Add("tenue-musique-notes");
        // Ensembles portés en entier : leur effet bonus.
        objets.AddRange(Boutique.BonusPortes(p.Equipe));
        objets.AddRange(p.Soins);
        objets.AddRange(p.Meteo);
        // Pendant un geste, la tenue garde ses lunettes et chapeaux ; ce qu'elle tient en main laisse la place.
        var tenue = p.Tenue;
        if (p.Gestes.Count > 0 && tenue != "" && Banque.Commune.Tenues.TryGetValue(tenue, out var habits))
        {
            objets.InsertRange(0, GestesPilou.TenueCompatible(habits, id => Banque.Commune[id]?.Slot));
            tenue = "";
        }
        objets.AddRange(p.Gestes);
        return new Allure
        {
            Expr = p.Humeur != "" ? p.Humeur : p.Expr.ToString().ToLowerInvariant(),
            T = p.T,
            Couleur = couleurAchetee != "" ? couleurAchetee : p.Couleur.ToString().ToLowerInvariant(),
            Accessoire = p.Accessoire is Accessoire.Aucun or Accessoire.Saison ? "" : p.Accessoire.ToString().ToLowerInvariant(),
            Tenue = tenue,
            Objets = objets,
            Cligne = p.Cligne, Clin = p.Clin, Marche = p.Marche, Course = p.Course, Baille = p.Baille, Etourdi = p.Etourdi,
            Fatigue = p.Fatigue, Salue = p.Salue, Boude = p.Boude, Dos = p.Dos,
            Regard = p.Regard, RegardY = p.RegardY,
            Saut = p.Saut, Chute = p.Chute, Assis = p.Assis, Suspendu = p.Suspendu, Tremble = p.Tremble,
            Stade = p.Stade, Evolution = p.Evolution, Reaction = p.Reaction,
        };
    }

    protected override void OnRender(DrawingContext dc)
    {
        var p = Pose;
        if (p.Pancarte != "")
        {
            _zoom = 1;
            DessinerPancarte(dc, p);
            return;
        }
        _zoom = p.Zoom;
        // Collé à l'écran : tout grossit, à partir des pieds.
        dc.PushTransform(new ScaleTransform(p.Zoom, p.Zoom, MargeX + C * P, Sol));
        Dessiner(dc, p);
        dc.Pop();
        if (p.Flash > 0) Flash(dc, p.Flash);
        if (p.Bruit != "") TextePixel(dc, p.Bruit, MargeX + 6 * P, MargeY - 2 * P, 3, Blanc, Encre);
    }

    // Flash de l'appareil photo : un cadre blanc fin et translucide autour de Pilou, bref (150 ms) et jamais
    // plein écran ni opaque, pour ne pas éblouir ni attirer l'œil pendant le travail.
    private static void Flash(DrawingContext dc, double force)
    {
        double ep = P;
        var r = new Rect(MargeX - 3 * P, MargeY - 2 * P, W * P + 6 * P, H * P + 4 * P);
        dc.PushOpacity(Math.Clamp(force, 0, 1) * 0.35);
        dc.DrawRectangle(null, new Pen(Blanc, ep), r);
        dc.Pop();
    }

    // Pancarte « parti chez… » plantée au sol à la place de Pilou, posée sur la même grille (elle prend
    // la souris comme lui : un clic rappelle Pilou), puis le texte écrit sur le papier.
    private void DessinerPancarte(DrawingContext dc, Pose p)
    {
        int e = Finesse.Echelle;
        int gw = RenduPilou.W * e, gh = RenduPilou.H * e;
        double pf = PX / e;
        var s = Banque.Commune.Echelle("pancarte", e);
        var pixels = new uint[gw * gh];
        int gx0 = 0, gy0 = 0, w = 0;
        if (s is not null)
        {
            var g = Banque.Grille(s, p.T);
            int h = g.GetLength(0);
            w = g.GetLength(1);
            gx0 = (gw - w) / 2;
            gy0 = Math.Max(0, (int)Math.Round((Sol - MargeY) / pf) - h);
            for (int y = 0; y < h && gy0 + y < gh; y++)
            for (int x = 0; x < w && gx0 + x < gw; x++)
                pixels[(gy0 + y) * gw + gx0 + x] = g[y, x];
        }
        _pixels = pixels;
        _echelle = e;
        Image(dc, pixels, e);
        var lignes = p.Pancarte.Split('\n');
        double dpi = VisualTreeHelper.GetDpi(this).PixelsPerDip;
        double cx = MargeX + (gx0 + w / 2.0) * pf, y0 = MargeY + (gy0 + 4 * e) * pf;
        for (int i = 0; i < lignes.Length && i < 2; i++)
        {
            var ft = new FormattedText(lignes[i], System.Globalization.CultureInfo.CurrentCulture, FlowDirection.LeftToRight,
                new Typeface(new FontFamily("Segoe UI"), FontStyles.Normal, FontWeights.Bold, FontStretches.Normal),
                i == 0 ? 11 : 10.5, i == 0 ? Encre : Bleu1, dpi)
            { MaxTextWidth = 36 * PX, Trimming = TextTrimming.CharacterEllipsis, TextAlignment = TextAlignment.Center };
            dc.DrawText(ft, new Point(cx - 18 * PX, y0 + i * 15));
        }
    }

    private static readonly Brush Bleu1 = B("#1f4f8a");

    // La grille rendue (ARGB, échelle e), posée dans le même rectangle quelle que soit l'échelle. Le bitmap est gardé :
    // il n'est réécrit que si les pixels ont changé depuis la dernière image (aucune allocation sinon). En mémoire,
    // un uint ARGB est déjà l'ordre B, G, R, A du format Bgra32 : les pixels passent tels quels.
    private void Image(DrawingContext dc, uint[] pixels, int e)
    {
        int w = RenduPilou.W * e, h = RenduPilou.H * e;
        if (_image is null || _image.PixelWidth != w || _affiche.Length != pixels.Length)
        {
            _image = new WriteableBitmap(w, h, 96, 96, PixelFormats.Bgra32, null);
            _affiche = new uint[pixels.Length];
            _imagePleine = false;
        }
        if (!_imagePleine || !pixels.AsSpan().SequenceEqual(_affiche))
        {
            pixels.CopyTo(_affiche, 0);
            _image.WritePixels(new Int32Rect(0, 0, w, h), _affiche, w * 4, 0);
            _imagePleine = true;
            RendusEcrits++;
        }
        dc.DrawImage(_image, new Rect(MargeX, MargeY, RenduPilou.W * PX, RenduPilou.H * PX));
    }

    // Mesures (diagnostic, essais) : images rendues, images dont le bitmap a dû être réécrit, temps du dernier rendu.
    public int Rendus { get; private set; }
    public int RendusEcrits { get; private set; }
    public double DernierRenduMs { get; private set; }

    private void Dessiner(DrawingContext dc, Pose p)
    {
        _debord.Clear();
        int e = Finesse.Echelle;
        long debut = System.Diagnostics.Stopwatch.GetTimestamp();
        var pixels = RenduPilou.Rendre(Allure(p), Banque.Commune, out var geo, _debord, e, _tampon);
        _pixels = pixels;
        _echelle = e;
        Geo = geo;
        Image(dc, pixels, e);
        Rendus++;
        DernierRenduMs = System.Diagnostics.Stopwatch.GetElapsedTime(debut).TotalMilliseconds;
        // Ce qui dépasse de la grille (parapluie, longue-vue tenus au bout de la main) : dans la marge de la scène
        // (12 pixels de grille de chaque côté), au lieu d'être coupé au bord de la grille.
        double pf = PX / e;
        foreach (var (x, y, c) in _debord)
            if (y < RenduPilou.H * e) dc.DrawRectangle(Pinceau(c), null, new Rect(MargeX + x * pf, MargeY + y * pf, pf, pf));

        // Repères dans l'ancienne grille, pour les effets.
        double cx = geo.Cx / F;
        int sommet = (int)Math.Round(geo.Sommet / F);
        int ey = (int)Math.Round(geo.Ey / F);
        int dx = (int)Math.Round(cx - C);
        if (p.Course) Poussiere(dc, p.T, p.Regard);
        if (p.Trainee && p.Marche) Trainee(dc, p.T, p.Regard);
        if (p.Balle) Balle(dc, p);
        if (p.Etourdi) Etoiles(dc, p.T, cx, sommet);
        if (p.Toque > 0) Ondes(dc, p.Toque);
        if (p.Evolution is > 0 and < 1 || p.Reaction == "sueur") return; // l'évolution et la sueur se suffisent
        Effets(dc, p, ey, dx);
    }

    // Seuls les pixels dessinés de Pilou prennent la souris (pas son ombre ni le vide autour).
    protected override HitTestResult? HitTestCore(PointHitTestParameters h)
    {
        var px = _pixels;
        if (px is null) return null;
        double ox = MargeX + C * P, oy = Sol;
        double x = ox + (h.HitPoint.X - ox) / _zoom, y = oy + (h.HitPoint.Y - oy) / _zoom;
        int e = _echelle, gw = RenduPilou.W * e;
        int gx = (int)Math.Floor((x - MargeX) / (PX / e)), gy = (int)Math.Floor((y - MargeY) / (PX / e));
        if (gx < 0 || gy < 0 || gx >= gw || gy >= RenduPilou.H * e || px.Length != gw * RenduPilou.H * e) return null;
        uint c = px[gy * gw + gx];
        return c >> 24 == 0xff ? new PointHitTestResult(this, h.HitPoint) : null;
    }

    // Ballon : sprite de la banque (quatre images de rotation), au sol devant Pilou.
    private static void Balle(DrawingContext dc, Pose p)
    {
        int e = Finesse.Echelle;
        var s = Banque.Commune.Echelle("ballon", e);
        if (s is null) return;
        int quart = (int)Math.Floor(((p.BalleRot % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI) / (Math.PI / 4)) % Math.Max(1, s.Images.Count);
        var g = Banque.Grille(s, s.Duree * quart);
        double bx = (RenduPilou.C + p.BalleX * RenduPilou.K) * e, pf = PX / e;
        int x0 = (int)Math.Round(bx) - s.W / 2, y0 = 53 * e - s.H - (int)Math.Round(Math.Abs(Math.Sin(p.BalleRot)) * 1.5 * e);
        for (int y = 0; y < g.GetLength(0); y++)
        for (int x = 0; x < g.GetLength(1); x++)
            if (g[y, x] != 0)
                dc.DrawRectangle(Pinceau(g[y, x]), null, new Rect(MargeX + (x0 + x) * pf, MargeY + (y0 + y) * pf, pf, pf));
    }

    private static readonly Dictionary<uint, Brush> Pinceaux = new();

    public static Brush Pinceau(uint argb)
    {
        if (Pinceaux.TryGetValue(argb, out var b)) return b;
        var br = new SolidColorBrush(Color.FromArgb((byte)(argb >> 24), (byte)(argb >> 16), (byte)(argb >> 8), (byte)argb));
        br.Freeze();
        return Pinceaux[argb] = br;
    }

    // ---- Petites formes des effets (étoile, cœur, goutte…) : faites de cases de l'ancienne grille (2 × 2 pixels
    // de la grille 48 × 56). En dessin fin, la forme est agrandie deux fois par la règle commune
    // (Sprite.AgrandirImage) : quatre pixels fins par case, coins arrondis, au lieu de gros carrés.
    private static readonly string[] FormeEtoile = { ".#.", "###", ".#." };
    private static readonly string[] FormeCoeur = { "h.#", "###", ".#." };
    private static readonly string[] FormeGoutte = { ".c.", "clc", "cwc", ".c." };
    private static readonly string[] FormeSoupir = { ".#.", "#.#", ".#." };
    // Clarté des lettres pour l'agrandissement : le trait (#, c) plus sombre que les reflets (h, l, w).
    private static readonly Dictionary<char, string> ClartesFormes = new()
    {
        ['#'] = "#606060", ['c'] = "#303030", ['h'] = "#e0e0e0", ['l'] = "#c0c0c0", ['w'] = "#ffffff",
    };
    private static readonly Dictionary<string[], string[]> FormesFines = new();

    // La forme, coin haut-gauche sur la case (x, y) ; couleur : pinceau d'une lettre (null : rien).
    private static void Forme(DrawingContext dc, string[] forme, int x, int y, Func<char, Brush?> couleur)
    {
        if (Finesse.Echelle != 2)
        {
            for (int j = 0; j < forme.Length; j++)
            for (int i = 0; i < forme[j].Length; i++)
                if (couleur(forme[j][i]) is { } b) dc.DrawRectangle(b, null, Case(x + i, y + j));
            return;
        }
        if (!FormesFines.TryGetValue(forme, out var fine))
            FormesFines[forme] = fine = Sprite.AgrandirImage(Sprite.AgrandirImage(forme, ClartesFormes), ClartesFormes);
        double pf = PX / 2, x0 = MargeX + Math.Round(x * F) * PX, y0 = MargeY + Math.Round(y * F) * PX;
        for (int j = 0; j < fine.Length; j++)
        {
            var l = fine[j];
            for (int i = 0; i < l.Length;)
            {
                int fin = i + 1;
                while (fin < l.Length && l[fin] == l[i]) fin++;
                if (couleur(l[i]) is { } b) dc.DrawRectangle(b, null, new Rect(x0 + i * pf, y0 + j * pf, (fin - i) * pf, pf));
                i = fin;
            }
        }
    }

    // Trois petites étoiles en croix qui tournent autour de la tête.
    private static void Etoiles(DrawingContext dc, double t, double cx, int sommet)
    {
        for (int i = 0; i < 3; i++)
        {
            double a = t / 260.0 + i * 2.094;
            int x = (int)Math.Round(cx + Math.Cos(a) * 9), y = (int)Math.Round(sommet + 1 + Math.Sin(a) * 2);
            var br = i % 2 == 0 ? Etincelle : Bleu.Clair;
            Forme(dc, FormeEtoile, x - 1, y - 1, ch => ch == '#' ? br : null);
        }
    }

    // « Toc » : anneaux de pixels qui partent du front, et le mot en police pixel.
    private static void Ondes(DrawingContext dc, double phase)
    {
        for (int i = 0; i < 2; i++)
        {
            double k = (phase + i * 0.5) % 1.0;
            double rx = 3 + k * 9, ry = 2.5 + k * 7;
            dc.PushOpacity(1 - k);
            for (double a = 0; a < 2 * Math.PI; a += 0.12)
                dc.DrawRectangle(Bleu.Clair, null, Case(Math.Round(C - 0.5 + Math.Cos(a) * rx), Math.Round(12 + Math.Sin(a) * ry)));
            dc.Pop();
        }
        if (phase < 0.6) TextePixel(dc, "TOC", MargeX + 20 * P, MargeY + (1 - phase * 2) * P, 3, Etincelle, Encre);
    }

    private static void Effets(DrawingContext dc, Pose p, int ey, int dx)
    {
        var t = p.T;
        switch (p.Expr)
        {
            case Expr.Dort:
            {
                // Trois Z en pixels qui montent et grossissent.
                for (int i = 0; i < 3; i++)
                {
                    double phase = (t / 2400.0 + i / 3.0) % 1.0;
                    double taille = phase < 0.33 ? 2 : phase < 0.66 ? 3 : 4;
                    dc.PushOpacity(1 - phase * 0.8);
                    TextePixel(dc, "Z", MargeX + (19 + phase * 7) * P, MargeY + (ey - 1 - phase * 11) * P, taille, Brume, Bleu.Contour);
                    dc.Pop();
                }
                break;
            }
            case Expr.Fete:
            {
                // Confettis en gerbe, alignés sur la grille.
                for (int i = 0; i < 12; i++)
                {
                    double a = i * 0.53 + 0.2;
                    double r = 34 + (p.Depuis / 12 + i * 7) % 28;
                    double px = Largeur / 2 + Math.Cos(a) * r * 1.3, py = MargeY + 12 * P - Math.Sin(a) * r * 0.9 + p.Depuis / 40 % 12;
                    Grain(dc, px, py, i % 3 == 0 ? Etincelle : i % 3 == 1 ? Bleu.Base : EtincelleClair);
                }
                break;
            }
            case Expr.Caresse:
            {
                for (int i = 0; i < 3; i++)
                {
                    double phase = (t / 1500.0 + i / 3.0) % 1.0;
                    dc.PushOpacity(Math.Clamp(1 - phase, 0, 1));
                    int x = (int)Math.Round(4 + i * 8 + Math.Sin(phase * 6 + i) * 1.5), y = (int)Math.Round(ey - 3 - phase * 12);
                    Forme(dc, FormeCoeur, x, y, ch => ch == '#' ? Etincelle : ch == 'h' ? EtincelleClair : null);
                    dc.Pop();
                }
                break;
            }
            case Expr.Attente:
            {
                int n = (int)(t / 400) % 4;
                for (int i = 0; i < n; i++) dc.DrawRectangle(Gris, null, Case(22 + i * 2, ey + 2));
                break;
            }
            case Expr.Soulage:
            {
                double phase = Math.Min(1, p.Depuis / 1400);
                int x = (int)Math.Round(21 + phase * 6), y = (int)Math.Round(ey + 4 - phase * 8);
                dc.PushOpacity(1 - phase);
                Forme(dc, FormeSoupir, x, y, ch => ch == '#' ? Brume : null);
                dc.Pop();
                break;
            }
            case Expr.Inquiet:
            {
                // Goutte de sueur en pixels qui glisse.
                double phase = t / 1200.0 % 1.0;
                int x = 21 + dx, y = (int)Math.Round(ey + phase * 6);
                dc.PushOpacity(1 - phase);
                Forme(dc, FormeGoutte, x - 1, y - 1, ch => ch == 'c' ? Bleu.Contour : ch == 'l' ? Bleu.Clair : ch == 'w' ? Blanc : null);
                dc.Pop();
                break;
            }
        }
    }

    // Traînée d'étoiles (récompense) : des éclats orange et bleus qui restent derrière lui.
    private static void Trainee(DrawingContext dc, double t, int sens)
    {
        int arriere = sens >= 0 ? -1 : 1;
        for (int i = 0; i < 5; i++)
        {
            double phase = (t / 900.0 + i / 5.0) % 1.0;
            int x = (int)Math.Round(C + arriere * (6 + phase * 10)), y = (int)Math.Round(24 - phase * 6 + (i % 2) * 2);
            dc.PushOpacity(1 - phase);
            var br = i % 2 == 0 ? Etincelle : Bleu.Clair;
            dc.DrawRectangle(br, null, Case(x, y));
            if (phase < 0.4)
            {
                dc.DrawRectangle(EtincelleClair, null, Case(x + 1, y));
                dc.DrawRectangle(EtincelleClair, null, Case(x, y - 1));
            }
            dc.Pop();
        }
    }

    // Petits nuages de pixels derrière lui quand il court.
    private static void Poussiere(DrawingContext dc, double t, int sens)
    {
        int arriere = sens >= 0 ? -1 : 1;
        for (int i = 0; i < 3; i++)
        {
            double phase = (t / 420.0 + i / 3.0) % 1.0;
            int x = (int)Math.Round(C + arriere * (8 + phase * 7)), y = (int)Math.Round(27 - phase * 2.5);
            dc.PushOpacity(0.6 * (1 - phase));
            dc.DrawRectangle(Brume, null, Case(x, y));
            if (phase > 0.3) dc.DrawRectangle(Brume, null, Case(x + arriere, y));
            if (phase > 0.6) dc.DrawRectangle(Brume, null, Case(x, y - 1));
            dc.Pop();
        }
    }
}
