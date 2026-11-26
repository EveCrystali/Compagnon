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
    public bool Trainee;        // traînée d'étoiles quand il marche (récompense)
    // Activité reconnue (Activites.Toutes : code, tableur, jeu-mmo, jeu, musique, video, lecture, dessin,
    // visio, nuit, mail, texte, diaporama) : la tenue à dessiner ; "" = aucune.
    public string Tenue = "";
    // Petite réaction liée à l'activité : "danse" (musique), "sueur" (processeur chargé pendant le code), "".
    public string Reaction = "";
    // Soins : sprites en plus (variante d'évolution, rayonnement, mousse de la toilette, bouderie) ; il boude
    // (moue, sourcils froncés) ; il tourne le dos (ni visage, ni lunettes).
    public IReadOnlyList<string> Soins = Array.Empty<string>();
    public bool Boude, Dos;
    // Effets météo dessinés sur Pilou (sprites « meteo-… » : pluie, mouillé, neige, givre, soleil…).
    public IReadOnlyList<string> Meteo = Array.Empty<string>();
}

// Pilou en pixel art, grille fine de 48 × 56 commune avec l'app Android (RenduPilou), affichée en pixels
// nets à la même taille qu'avant. Les effets (Z, confettis, étoiles…) restent dessinés ici, alignés sur
// la même grille. Les grandeurs du mouvement (Saut, BalleX…) restent en « anciens » pixels de 5 unités.
// Seuls les pixels dessinés prennent la souris.
public sealed class Scene : FrameworkElement
{
    // Pixel de l'ancienne grille (26 × 30) : unité des positions des effets et de Pixels par défaut.
    public const double P = 4;
    // « Ancien » pixel (5 unités WPF), unité des déplacements de la fenêtre.
    public const double PA = 5;
    public const int W = 26;
    public const int H = 30;
    public const double MargeX = 28;
    public const double MargeY = 26;
    // Pixel de la grille fine : 48 × 56 sur la même largeur que l'ancienne grille.
    public const double PX = W * P / RenduPilou.W;
    private const double E = 1.25;      // anciens pixels → pixels de l'ancienne grille
    private const double C = 13;        // axe du corps dans l'ancienne grille
    private const double F = RenduPilou.W / (double)W; // ancienne grille → grille fine
    public static double Largeur => MargeX * 2 + W * P;
    public static double Hauteur => MargeY + H * P + 6;
    // Ordonnée des pieds dans la scène.
    public static double Sol => MargeY + 28.75 * P;

    public Pose Pose { get; set; } = new();

    private uint[]? _pixels;
    private double _zoom = 1;

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
        var objets = p.Equipe.Where(kv => kv.Key != Boutique.Couleur && kv.Value != "").Select(kv => kv.Value).ToList();
        var couleurAchetee = p.Equipe.GetValueOrDefault(Boutique.Couleur, "");
        if (p.Reaction == "danse" && p.Tenue != "musique") objets.Add("tenue-musique-notes");
        objets.AddRange(p.Soins);
        objets.AddRange(p.Meteo);
        return new Allure
        {
            Expr = p.Expr.ToString().ToLowerInvariant(),
            T = p.T,
            Couleur = couleurAchetee != "" ? couleurAchetee : p.Couleur.ToString().ToLowerInvariant(),
            Accessoire = p.Accessoire is Accessoire.Aucun or Accessoire.Saison ? "" : p.Accessoire.ToString().ToLowerInvariant(),
            Tenue = p.Tenue,
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
        _zoom = p.Zoom;
        // Collé à l'écran : tout grossit, à partir des pieds.
        dc.PushTransform(new ScaleTransform(p.Zoom, p.Zoom, MargeX + C * P, Sol));
        Dessiner(dc, p);
        dc.Pop();
    }

    private void Dessiner(DrawingContext dc, Pose p)
    {
        var pixels = RenduPilou.Rendre(Allure(p), Banque.Commune, out var geo);
        _pixels = pixels;
        var bgra = new byte[pixels.Length * 4];
        for (int i = 0; i < pixels.Length; i++)
        {
            uint c = pixels[i];
            bgra[i * 4] = (byte)c;
            bgra[i * 4 + 1] = (byte)(c >> 8);
            bgra[i * 4 + 2] = (byte)(c >> 16);
            bgra[i * 4 + 3] = (byte)(c >> 24);
        }
        var image = BitmapSource.Create(RenduPilou.W, RenduPilou.H, 96, 96, PixelFormats.Bgra32, null, bgra, RenduPilou.W * 4);
        image.Freeze();
        dc.DrawImage(image, new Rect(MargeX, MargeY, RenduPilou.W * PX, RenduPilou.H * PX));

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
        int gx = (int)Math.Floor((x - MargeX) / PX), gy = (int)Math.Floor((y - MargeY) / PX);
        if (gx < 0 || gy < 0 || gx >= RenduPilou.W || gy >= RenduPilou.H) return null;
        uint c = px[gy * RenduPilou.W + gx];
        return c >> 24 == 0xff ? new PointHitTestResult(this, h.HitPoint) : null;
    }

    // Ballon : sprite de la banque (quatre images de rotation), au sol devant Pilou.
    private static void Balle(DrawingContext dc, Pose p)
    {
        var s = Banque.Commune["ballon"];
        if (s is null) return;
        int quart = (int)Math.Floor(((p.BalleRot % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI) / (Math.PI / 4)) % Math.Max(1, s.Images.Count);
        var g = Banque.Grille(s, s.Duree * quart);
        double bx = RenduPilou.C + p.BalleX * RenduPilou.K;
        int x0 = (int)Math.Round(bx) - s.W / 2, y0 = 53 - s.H - (int)Math.Round(Math.Abs(Math.Sin(p.BalleRot)) * 1.5);
        for (int y = 0; y < g.GetLength(0); y++)
        for (int x = 0; x < g.GetLength(1); x++)
            if (g[y, x] != 0)
                dc.DrawRectangle(Pinceau(g[y, x]), null, new Rect(MargeX + (x0 + x) * PX, MargeY + (y0 + y) * PX, PX, PX));
    }

    private static readonly Dictionary<uint, Brush> Pinceaux = new();

    public static Brush Pinceau(uint argb)
    {
        if (Pinceaux.TryGetValue(argb, out var b)) return b;
        var br = new SolidColorBrush(Color.FromArgb((byte)(argb >> 24), (byte)(argb >> 16), (byte)(argb >> 8), (byte)argb));
        br.Freeze();
        return Pinceaux[argb] = br;
    }

    // Trois petites étoiles en croix qui tournent autour de la tête.
    private static void Etoiles(DrawingContext dc, double t, double cx, int sommet)
    {
        for (int i = 0; i < 3; i++)
        {
            double a = t / 260.0 + i * 2.094;
            int x = (int)Math.Round(cx + Math.Cos(a) * 9), y = (int)Math.Round(sommet + 1 + Math.Sin(a) * 2);
            var br = i % 2 == 0 ? Etincelle : Bleu.Clair;
            foreach (var (a2, b2) in new[] { (0, 0), (-1, 0), (1, 0), (0, -1), (0, 1) }) dc.DrawRectangle(br, null, Case(x + a2, y + b2));
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
                    foreach (var (a, b) in new[] { (0, 0), (2, 0), (0, 1), (1, 1), (2, 1), (1, 2) }) dc.DrawRectangle(Etincelle, null, Case(x + a, y + b));
                    dc.DrawRectangle(EtincelleClair, null, Case(x, y));
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
                foreach (var (a, b) in new[] { (1, 0), (0, 1), (2, 1), (1, 2) }) dc.DrawRectangle(Brume, null, Case(x + a, y + b));
                dc.Pop();
                break;
            }
            case Expr.Inquiet:
            {
                // Goutte de sueur en pixels qui glisse.
                double phase = t / 1200.0 % 1.0;
                int x = 21 + dx, y = (int)Math.Round(ey + phase * 6);
                dc.PushOpacity(1 - phase);
                dc.DrawRectangle(Bleu.Contour, null, Case(x, y - 1));
                foreach (var (a, b) in new[] { (-1, 0), (0, 0), (1, 0), (-1, 1), (1, 1), (0, 2) }) dc.DrawRectangle(Bleu.Contour, null, Case(x + a, y + b));
                dc.DrawRectangle(Bleu.Clair, null, Case(x, y));
                dc.DrawRectangle(Blanc, null, Case(x, y + 1));
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
