using System.Windows;
using System.Windows.Media;

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
}

// Pilou en pixel art : une goutte bleue cernée, une antenne, une étincelle orange.
// Grille de 26 × 30 pixels de P unités WPF (centre du corps en x = 13). Les grandeurs du
// mouvement (Saut, BalleX…) restent en « anciens » pixels de 5 unités : × 1,25 ici.
// Fond transparent : seuls les pixels dessinés prennent la souris.
public sealed class Scene : FrameworkElement
{
    public const double P = 4;
    // « Ancien » pixel (5 unités WPF), unité des déplacements de la fenêtre.
    public const double PA = 5;
    public const int W = 26;
    public const int H = 30;
    public const double MargeX = 28;
    public const double MargeY = 26;
    private const double E = 1.25;      // anciens pixels → pixels de la grille
    private const double C = 13;        // axe du corps
    public static double Largeur => MargeX * 2 + W * P;
    public static double Hauteur => MargeY + H * P + 6;
    // Ordonnée des pieds dans la scène.
    public static double Sol => MargeY + 28.75 * P;

    public Pose Pose { get; set; } = new();

    private static SolidColorBrush B(string hex)
    {
        var b = new SolidColorBrush((Color)ColorConverter.ConvertFromString(hex));
        b.Freeze();
        return b;
    }

    private sealed record Teinte(Brush Contour, Brush Ombre, Brush Base, Brush Clair);

    private static readonly Teinte Bleu = new(B("#1f4f8a"), B("#4a8fdc"), B("#6cb6ff"), B("#b4dbff"));
    private static readonly Teinte Orange = new(B("#8a4a1f"), B("#d9803a"), B("#f69d50"), B("#ffc89a"));
    private static readonly Dictionary<Couleur, Teinte> Couleurs = new()
    {
        [Couleur.Bleu] = Bleu,
        [Couleur.Nuit] = new(B("#0d2a4d"), B("#2a5ea8"), B("#3f7fd6"), B("#8fbaf0")),
        [Couleur.Ambre] = new(B("#7a4210"), B("#c97a28"), B("#f2a94e"), B("#ffd59a")),
        [Couleur.Argent] = new(B("#3b4654"), B("#8796a8"), B("#b8c4d2"), B("#e6ecf2")),
        [Couleur.Aurore] = new(B("#3a2a7a"), B("#6a5acd"), B("#9b8cff"), B("#d2caff")),
        [Couleur.Lagon] = new(B("#0f4a63"), B("#2689b8"), B("#3fb8e0"), B("#a8e4f7")),
        [Couleur.Braise] = new(B("#6b2f0c"), B("#c45a1a"), B("#f07c2a"), B("#ffc08a")),
        [Couleur.Nacre] = new(B("#4d5566"), B("#b9b4cf"), B("#e4def5"), B("#ffffff")),
        [Couleur.Abysse] = new(B("#0a1230"), B("#1b2a6b"), B("#2f45a8"), B("#7f93e8")),
        [Couleur.Comete] = new(B("#5a4410"), B("#c9a227"), B("#f5d76e"), B("#fff6cc")),
    };
    private static readonly Brush Encre = B("#1c2128");
    private static readonly Brush Blanc = B("#ffffff");
    private static readonly Brush Etincelle = B("#f69d50");
    private static readonly Brush EtincelleClair = B("#ffd8b0");
    private static readonly Brush Gris = B("#768390");
    private static readonly Brush Brume = B("#adbac7");
    private static readonly Brush Joue = B("#ffb37a");
    private static readonly Brush OmbreSol = B("#55000000");
    private static readonly Brush Laine = B("#f69d50");
    private static readonly Brush LaineOmbre = B("#c8742e");
    private static readonly Brush Creme = B("#f6f8fa");
    private static readonly Brush CremeOmbre = B("#c9d1d9");
    private static readonly Brush Arceau = B("#768390");
    private static readonly Brush ArceauClair = B("#adbac7");
    private static readonly Brush Feuillage = B("#e0823d");
    private static readonly Brush Nervure = B("#8a4a1f");

    // Yeux (œil gauche ; le droit est le miroir) : 1 encre, 2 reflet, 3 paupière.
    private static readonly Dictionary<string, int[,]> Yeux = new()
    {
        ["ouvert"] = new[,] { { 2, 1, 1 }, { 1, 1, 1 }, { 1, 1, 1 }, { 0, 0, 0 } },
        ["cligne"] = new[,] { { 0, 0, 0 }, { 0, 0, 0 }, { 1, 1, 1 }, { 0, 0, 0 } },
        ["fatigue"] = new[,] { { 3, 3, 3 }, { 2, 1, 1 }, { 1, 1, 1 }, { 0, 0, 0 } },
        ["concentre"] = new[,] { { 3, 3, 3 }, { 1, 1, 1 }, { 2, 1, 1 }, { 0, 0, 0 } },
        ["haut"] = new[,] { { 1, 2, 1 }, { 1, 1, 1 }, { 0, 0, 0 }, { 0, 0, 0 } },
        ["grimace"] = new[,] { { 1, 1, 0 }, { 0, 1, 1 }, { 1, 1, 0 }, { 0, 0, 0 } },
        ["heureux"] = new[,] { { 0, 1, 0 }, { 1, 0, 1 }, { 1, 0, 1 }, { 0, 0, 0 } },
        ["content"] = new[,] { { 0, 0, 0 }, { 1, 0, 1 }, { 0, 1, 0 }, { 0, 0, 0 } },
        ["dort"] = new[,] { { 0, 0, 0 }, { 0, 0, 0 }, { 1, 1, 1 }, { 0, 0, 0 } },
        ["inquiet"] = new[,] { { 0, 1, 0 }, { 1, 2, 1 }, { 1, 2, 1 }, { 0, 1, 0 } },
        ["spirale"] = new[,] { { 1, 1, 1 }, { 1, 0, 0 }, { 1, 0, 1 }, { 1, 1, 1 } },
    };
    private static readonly int[,] Baillement = { { 0, 1, 1, 0 }, { 1, 5, 5, 1 }, { 1, 5, 5, 1 }, { 0, 1, 1, 0 } };

    // Bouches (largeur paire, centrées sur l'axe) : 1 encre, 5 langue orange.
    private static readonly Dictionary<Expr, int[,]> Bouches = new()
    {
        [Expr.Repos] = new[,] { { 1, 0, 0, 1 }, { 0, 1, 1, 0 } },
        [Expr.Concentre] = new[,] { { 1, 1 } },
        [Expr.Attente] = new[,] { { 1, 1 }, { 1, 1 } },
        [Expr.Grimace] = new[,] { { 0, 1, 0, 1, 0, 1 }, { 1, 0, 1, 0, 1, 0 } },
        [Expr.Fete] = new[,] { { 1, 1, 1, 1 }, { 1, 5, 5, 1 }, { 0, 1, 1, 0 } },
        [Expr.Soulage] = new[,] { { 1, 0, 0, 1 }, { 0, 1, 1, 0 } },
        [Expr.Dort] = new[,] { { 1, 1 }, { 1, 1 } },
        [Expr.Inquiet] = new[,] { { 0, 1, 1, 0 }, { 1, 0, 0, 1 } },
        [Expr.Caresse] = new[,] { { 1, 0, 1, 1, 0, 1 }, { 0, 1, 0, 0, 1, 0 } },
    };

    private static Rect Case(double x, double y) => new(MargeX + x * P, MargeY + y * P, P, P);

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

    protected override void OnRender(DrawingContext dc)
    {
        var p = Pose;
        // Collé à l'écran : tout grossit, à partir des pieds.
        dc.PushTransform(new ScaleTransform(p.Zoom, p.Zoom, MargeX + C * P, Sol));
        Dessiner(dc, p);
        dc.Pop();
    }

    private void Dessiner(DrawingContext dc, Pose p)
    {
        var t = p.T;
        // Inquiet : orange ; si Pilou est déjà ambre, il vire au bleu (le changement reste visible).
        var teinte = p.Expr == Expr.Inquiet ? (p.Couleur is Couleur.Ambre or Couleur.Braise or Couleur.Comete ? Bleu : Orange) : Couleurs[p.Couleur];
        double periode = p.Expr switch { Expr.Dort => 4200, Expr.Concentre or Expr.Attente => 1600, _ => 2600 };
        double b = Math.Sin(2 * Math.PI * t / periode);
        // Grandeurs en anciens pixels, converties ensuite (× E).
        double rx = 6.8 - 0.2 * b, ry = 5.6 + 0.3 * b;
        if (p.Expr == Expr.Caresse) { rx += 0.5; ry -= 0.5; }
        if (p.Expr == Expr.Dort) { rx += 0.6; ry -= 0.9; }
        rx += 1.2 * p.Chute + 0.7 * p.Assis - 0.8 * p.Suspendu;
        ry -= 1.4 * p.Chute + 0.8 * p.Assis - 1.1 * p.Suspendu;
        double cadence = p.Course ? 70 : 160;
        double marche = p.Marche ? Math.Abs(Math.Sin(t / cadence)) * (p.Course ? 1.3 : 0.8) : 0;
        double sol = (21.6 - p.Saut - marche + 1.0 * p.Assis) * E;
        double cx = C + (p.Tremble + p.Suspendu * Math.Sin(t / 260.0) * 1.2) * E;
        rx *= E;
        ry *= E;
        double cy = sol - ry;

        // Masque : corps (ombrage tramé, reflet), pieds, puis contour sur les bords.
        var masque = new Brush?[W, H];
        for (int y = 0; y < H; y++)
        for (int x = 0; x < W; x++)
        {
            double u = (x + 0.5 - cx) / rx, v = (y + 0.5 - cy) / ry, r2 = u * u + v * v;
            if (r2 > 1) continue;
            bool damier = (x + y) % 2 == 0;
            bool zoneReflet = u < -0.25 && v < -0.3;
            masque[x, y] = zoneReflet && (r2 > 0.45 || (r2 > 0.34 && damier)) ? teinte.Clair
                : v > 0.62 || (v > 0.46 && damier) ? teinte.Ombre
                : teinte.Base;
        }
        int pied = (int)Math.Round(sol);
        int pas = p.Marche ? (int)(t / cadence) % 2 : -1;
        if (p.Assis <= 0.5)
            foreach (var (px, cote) in new[] { (8, 0), (9, 0), (10, 0), (15, 1), (16, 1), (17, 1) })
            {
                int py = pied - (pas == cote ? 1 : 0);
                int x = px + (int)Math.Round(cx - C);
                if (x is >= 0 and < W && py is >= 0 and < H) masque[x, py] = teinte.Ombre;
            }
        var contour = new bool[W, H];
        for (int y = 0; y < H; y++)
        for (int x = 0; x < W; x++)
        {
            if (masque[x, y] is null) continue;
            if (x == 0 || y == 0 || x == W - 1 || y == H - 1 || masque[x - 1, y] is null || masque[x + 1, y] is null
                || masque[x, y - 1] is null || masque[x, y + 1] is null)
                contour[x, y] = true;
        }

        // Ombre au sol, en pixels, plus petite quand il saute.
        if (p.Suspendu < 0.1 && p.Zoom < 1.05)
        {
            int demi = (int)Math.Max(3, 8 - p.Saut * 1.5);
            for (int x = 13 - demi; x < 13 + demi; x++)
            {
                var r = Case(x, 28.4);
                dc.DrawRectangle(OmbreSol, null, new Rect(r.X, r.Y, P, P * 0.75));
            }
        }

        void Px(double x, double y, Brush br) => dc.DrawRectangle(br, null, Case(x, y));
        for (int y = 0; y < H; y++)
        for (int x = 0; x < W; x++)
            if (masque[x, y] is { } br) Px(x, y, contour[x, y] ? teinte.Contour : br);

        // Visage.
        int ey = (int)Math.Floor(cy - 3.6) + p.RegardY;
        int regard = p.Regard;
        string oeil = p.Etourdi ? "spirale" : p.Expr switch
        {
            Expr.Concentre => "concentre",
            Expr.Attente => "haut",
            Expr.Grimace => "grimace",
            Expr.Fete or Expr.Caresse => "heureux",
            Expr.Soulage => "content",
            Expr.Dort => "dort",
            Expr.Inquiet => "inquiet",
            _ => p.Fatigue ? "fatigue" : "ouvert",
        };
        bool peutCligner = p.Expr is Expr.Repos or Expr.Inquiet or Expr.Attente && !p.Etourdi;
        if (p.Baille) oeil = "dort";
        string oeilG = peutCligner && p.Cligne ? "cligne" : oeil;
        string oeilD = peutCligner && (p.Cligne || p.Clin) ? "cligne" : oeil;
        int dx = (int)Math.Round(cx - C);
        // Œil gauche : bord droit en colonne 10 ; œil droit : son miroir (colonnes 15 et suivantes).
        Motif(dc, Yeux[oeilG], 11 - Yeux[oeilG].GetLength(1) + regard + dx, ey, false, teinte);
        Motif(dc, Yeux[oeilD], 15 + regard + dx, ey, true, teinte);
        var bouche = p.Baille ? Baillement : Bouches[p.Expr];
        Motif(dc, bouche, 13 - bouche.GetLength(1) / 2 + regard + dx, ey + 5, false, teinte);
        if (p.Expr is Expr.Fete or Expr.Caresse)
            foreach (int x in new[] { 5, 6, 19, 20 })
                Px(x + regard + dx, ey + 4, Joue);

        // Antenne (trois pixels) et étincelle.
        int sommet = (int)Math.Ceiling(cy - ry);
        double vitesse = p.Salue ? 90 : p.Expr == Expr.Concentre ? 300 : 650;
        int balance = p.Expr == Expr.Dort ? 0 : (int)Math.Round(Math.Sin(t / vitesse) * 0.9) + (p.Marche ? -Math.Sign(regard) : 0);
        balance = Math.Clamp(balance, -1, 1);
        var accessoire = p.Accessoire;
        if (accessoire == Accessoire.Bonnet)
        {
            Bonnet(dc, dx, sommet, t);
            Bout(dc, p, 20 + dx, sommet - 11);
        }
        else if (accessoire == Accessoire.Toque)
        {
            Toque(dc, dx, sommet);
            Bout(dc, p, 13 + dx, sommet - 10);
        }
        else
        {
            Px(13 + dx, sommet - 1, teinte.Contour);
            Px(13 + dx, sommet - 2, teinte.Contour);
            Px(13 + dx + balance, sommet - 3, teinte.Contour);
            Bout(dc, p, 13 + dx + balance * 2, sommet - 5);
        }
        if (accessoire == Accessoire.Casque) Casque(dc, cx, cy, rx, ry, ey);
        if (accessoire == Accessoire.Noeud)
            Motif2(dc, new[,] { { 4, 4, 0, 0, 4, 4 }, { 4, 1, 4, 4, 1, 4 }, { 4, 1, 4, 4, 1, 4 }, { 4, 4, 0, 0, 4, 4 } }, 10 + dx, pied - 5, Laine, LaineOmbre);
        if (accessoire == Accessoire.Lunettes)
        {
            // Lunettes de soleil : deux verres sombres reliés par un pont, un reflet chacun.
            int gx = 7 + regard + dx, dxv = 15 + regard + dx;
            for (int y = ey; y <= ey + 3; y++)
            for (int i = 0; i < 4; i++)
            {
                if ((y == ey || y == ey + 3) && (i == 0 || i == 3)) continue;
                Px(gx + i, y, Encre);
                Px(dxv + i, y, Encre);
            }
            for (int x = gx + 4; x < dxv; x++) Px(x, ey + 1, Encre);
            Px(gx + 1, ey + 1, Bleu.Clair);
            Px(dxv + 1, ey + 1, Bleu.Clair);
        }
        if (accessoire == Accessoire.Couronne)
            Motif2(dc, new[,]
            {
                { 1, 0, 0, 1, 1, 0, 0, 1 }, { 1, 1, 0, 1, 1, 0, 1, 1 }, { 1, 1, 1, 1, 1, 1, 1, 1 }, { 1, 4, 1, 1, 1, 1, 4, 1 },
            }, 9 + dx, sommet - 3, Laine, Bleu.Clair);
        if (accessoire == Accessoire.ChapeauPeche) ChapeauPeche(dc, dx, sommet);
        if (accessoire == Accessoire.Tablier) Tablier(dc, dx, ey, pied);
        if (accessoire == Accessoire.EtoileMer)
            Motif2(dc, new[,] { { 0, 0, 1, 0, 0 }, { 1, 1, 4, 1, 1 }, { 0, 1, 1, 1, 0 }, { 0, 1, 0, 1, 0 } }, 16 + dx, sommet - 1, Laine, EtincelleClair);
        if (accessoire == Accessoire.Feuille)
            Motif2(dc, new[,] { { 0, 0, 0, 1, 4 }, { 0, 0, 1, 1, 1 }, { 0, 1, 4, 1, 0 }, { 1, 4, 1, 0, 0 }, { 4, 0, 0, 0, 0 } }, 5 + dx, sommet - 2, Feuillage, Nervure);

        if (p.Course) Poussiere(dc, t, p.Regard);
        if (p.Trainee && p.Marche) Trainee(dc, t, p.Regard);
        if (p.Balle) Balle(dc, p);
        if (p.Etourdi) Etoiles(dc, t, cx, sommet);
        if (p.Toque > 0) Ondes(dc, p.Toque);
        Effets(dc, p, ey, dx);
    }

    // Ballon en pixels : disque crème cerné, bande orange qui tourne.
    private static void Balle(DrawingContext dc, Pose p)
    {
        double bx = C + p.BalleX * E;
        int x0 = (int)Math.Round(bx) - 3, y0 = 22 - (int)Math.Round(Math.Abs(Math.Sin(p.BalleRot)) * 0.8);
        int quart = (int)Math.Floor(((p.BalleRot % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI) / (Math.PI / 4)) % 4;
        var disque = new[] { "0011100", "0111110", "1111111", "1111111", "1111111", "0111110", "0011100" };
        for (int r = 0; r < 7; r++)
        for (int c = 0; c < 7; c++)
        {
            if (disque[r][c] == '0') continue;
            bool bord = r == 0 || c == 0 || r == 6 || c == 6 || disque[r - 1][c] == '0' || disque[r + 1][c] == '0' || disque[r][c - 1] == '0' || disque[r][c + 1] == '0';
            bool bande = quart switch { 0 => r == 3, 1 => r == c, 2 => c == 3, _ => r + c == 6 };
            var br = bord ? Bleu.Contour : bande ? Laine : r + c > 7 ? CremeOmbre : Creme;
            dc.DrawRectangle(br, null, Case(x0 + c, y0 + r));
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

    // Motif à deux tons : 1 = couleur, 4 = ombre / détail.
    private static void Motif2(DrawingContext dc, int[,] m, int x0, int y0, Brush c1, Brush c4)
    {
        for (int r = 0; r < m.GetLength(0); r++)
        for (int c = 0; c < m.GetLength(1); c++)
        {
            Brush? br = m[r, c] switch { 1 => c1, 4 => c4, _ => null };
            if (br is not null) dc.DrawRectangle(br, null, Case(x0 + c, y0 + r));
        }
    }

    // Bonnet de laine orange à revers crème et pompon, posé sur le haut du crâne.
    private static void Bonnet(DrawingContext dc, int dx, int sommet, double t)
    {
        void Px(int x, int y, Brush br) => dc.DrawRectangle(br, null, Case(x + dx, y));
        // Revers : deux rangées crème, côtes de laine qui bougent un peu.
        for (int x = 6; x <= 19; x++)
        {
            Px(x, sommet, Creme);
            Px(x, sommet + 1, (x + (int)(t / 400)) % 3 == 0 ? CremeOmbre : Creme);
        }
        // Cône qui penche à droite, côtes en alternance.
        int[][] rangs = { new[] { 7, 18 }, new[] { 8, 18 }, new[] { 9, 18 }, new[] { 10, 18 }, new[] { 12, 19 }, new[] { 14, 19 } };
        for (int i = 0; i < rangs.Length; i++)
        {
            int y = sommet - 1 - i;
            for (int x = rangs[i][0]; x <= rangs[i][1]; x++) Px(x, y, x % 2 == 0 ? Laine : LaineOmbre);
        }
        // Pompon.
        foreach (var (a, b) in new[] { (19, -8), (20, -8), (21, -8), (19, -9), (20, -9), (21, -9), (20, -10), (20, -7) }) Px(a, sommet + b, Creme);
        Px(19, sommet - 9, Blanc);
    }

    // Chapeau de pêcheur (bob) : bord large, calotte bleu nuit, une mouche orange piquée sur le côté.
    private static void ChapeauPeche(DrawingContext dc, int dx, int sommet)
    {
        void Px(int x, int y, Brush br) => dc.DrawRectangle(br, null, Case(x + dx, y));
        for (int x = 4; x <= 21; x++) Px(x, sommet + 1, x is 4 or 21 ? Arceau : ArceauClair);
        for (int y = sommet - 2; y <= sommet; y++)
            for (int x = 7; x <= 18; x++)
                if (x != 13 || y != sommet - 2) Px(x, y, y == sommet ? Arceau : (x + y) % 3 == 0 ? Arceau : ArceauClair);
        Px(17, sommet - 1, Laine);
        Px(18, sommet - 2, Etincelle);
        Px(16, sommet - 2, EtincelleClair);
    }

    // Toque de chef : bandeau, puis un chapeau blanc bouffant (l'antenne ressort au sommet).
    private static void Toque(DrawingContext dc, int dx, int sommet)
    {
        void Px(int x, int y, Brush br) => dc.DrawRectangle(br, null, Case(x + dx, y));
        for (int x = 8; x <= 17; x++)
        {
            Px(x, sommet, CremeOmbre);
            Px(x, sommet - 1, Creme);
        }
        int[][] rangs = { new[] { 8, 17 }, new[] { 7, 18 }, new[] { 7, 18 }, new[] { 7, 18 }, new[] { 8, 17 }, new[] { 10, 15 } };
        for (int i = 0; i < rangs.Length; i++)
            for (int x = rangs[i][0]; x <= rangs[i][1]; x++)
                Px(x, sommet - 2 - i, x == rangs[i][0] || x == rangs[i][1] || i == rangs.Length - 1 ? CremeOmbre : Blanc);
        Px(10, sommet - 4, CremeOmbre);
        Px(15, sommet - 5, CremeOmbre);
    }

    // Tablier crème noué derrière, poche orange au milieu du ventre.
    private static void Tablier(DrawingContext dc, int dx, int ey, int pied)
    {
        void Px(int x, int y, Brush br) => dc.DrawRectangle(br, null, Case(x + dx, y));
        int haut = ey + 7, bas = pied - 2;
        for (int y = haut; y <= bas; y++)
            for (int x = 9; x <= 16; x++)
                Px(x, y, x is 9 or 16 || y == bas ? CremeOmbre : Creme);
        for (int x = 11; x <= 14; x++) Px(x, haut + 2, Laine);
        for (int x = 11; x <= 14; x++) Px(x, haut + 3, LaineOmbre);
        Px(8, haut, CremeOmbre);
        Px(17, haut, CremeOmbre);
    }

    // Casque audio : arceau gris par-dessus la tête, écouteurs orange de part et d'autre.
    private static void Casque(DrawingContext dc, double cx, double cy, double rx, double ry, int ey)
    {
        void Px(int x, int y, Brush br) => dc.DrawRectangle(br, null, Case(x, y));
        for (double a = Math.PI * 1.1; a <= Math.PI * 1.9; a += 0.04)
        {
            int x = (int)Math.Floor(cx + Math.Cos(a) * (rx + 0.7));
            int y = (int)Math.Floor(cy + Math.Sin(a) * (ry + 1.1));
            Px(x, y, a < Math.PI * 1.35 ? ArceauClair : Arceau);
        }
        int g = (int)Math.Floor(cx - rx) - 1, d = (int)Math.Ceiling(cx + rx) - 1;
        for (int y = ey; y <= ey + 3; y++)
        {
            Px(g, y, Laine);
            Px(g + 1, y, LaineOmbre);
            Px(d, y, LaineOmbre);
            Px(d + 1, y, Laine);
        }
        Px(g, ey, EtincelleClair);
        Px(d + 1, ey, EtincelleClair);
    }

    private static void Motif(DrawingContext dc, int[,] m, int x0, int y0, bool miroir, Teinte teinte)
    {
        int h = m.GetLength(0), w = m.GetLength(1);
        for (int r = 0; r < h; r++)
        for (int c = 0; c < w; c++)
        {
            int v = m[r, miroir ? w - 1 - c : c];
            Brush? br = v switch { 1 => Encre, 2 => Blanc, 3 => teinte.Ombre, 5 => Etincelle, _ => null };
            if (br is not null) dc.DrawRectangle(br, null, Case(x0 + c, y0 + r));
        }
    }

    // Étincelle au bout de l'antenne, centrée sur (x, y) : 3 × 3 pixels.
    private static void Bout(DrawingContext dc, Pose p, int x, int y)
    {
        void Px(int dx, int dy, Brush br) => dc.DrawRectangle(br, null, Case(x + dx, y + dy));
        var t = p.T;
        switch (p.Expr)
        {
            case Expr.Concentre:
            case Expr.Attente:
            {
                // Roue : deux points lumineux qui tournent sur un anneau.
                var anneau = new (int, int)[] { (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1) };
                int k = (int)(t / (p.Expr == Expr.Concentre ? 90 : 260)) % 8;
                for (int i = 0; i < 8; i++) Px(anneau[i].Item1, anneau[i].Item2, i == k || i == (k + 7) % 8 ? Etincelle : EtincelleClair);
                break;
            }
            case Expr.Grimace:
                foreach (var (a, b) in new[] { (-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1) }) Px(a, b, Etincelle);
                break;
            case Expr.Dort:
                Px(0, 0, Gris);
                break;
            case Expr.Inquiet:
                if ((int)(t / 300) % 2 == 0)
                {
                    Px(0, -2, Etincelle);
                    Px(0, -1, Etincelle);
                    Px(0, 1, Etincelle);
                }
                break;
            case Expr.Caresse:
                foreach (var (a, b) in new[] { (-1, -1), (1, -1), (-1, 0), (0, 0), (1, 0), (0, 1) }) Px(a, b, Etincelle);
                break;
            default:
            {
                bool grand = p.Expr == Expr.Fete ? (int)(t / 120) % 2 == 0 : (int)(t / 900) % 2 == 0;
                if (grand)
                {
                    foreach (var (a, b) in new[] { (0, -1), (-1, 0), (1, 0), (0, 1) }) Px(a, b, Etincelle);
                    Px(0, 0, EtincelleClair);
                }
                else
                {
                    foreach (var (a, b) in new[] { (-1, -1), (1, -1), (-1, 1), (1, 1) }) Px(a, b, EtincelleClair);
                    Px(0, 0, Etincelle);
                }
                break;
            }
        }
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
