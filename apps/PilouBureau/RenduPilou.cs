namespace PilouBureau;

// Ce qu'on demande au dessin de Pilou (sans WPF : testable, et identique à RenduPilou.java côté Android).
public sealed class Allure
{
    // repos, concentre, attente, grimace, fete, soulage, dort, inquiet, caresse ; humeurs des campagnes : joie, peur,
    // triste, surpris, determine, fatigue, tendre, colere, malice, neutre.
    public string Expr = "repos";
    public double T;                         // horloge de l'animation (ms)
    public string Couleur = "bleu";          // nom d'une teinte (assets/teintes.txt)
    public string Accessoire = "";           // récompense de niveau : sprite « acc-<nom> »
    // Tenue d'activité (assets/tenues.txt), ou tenue de voyage des campagnes : « voyage-marche », « voyage-course »,
    // « voyage-bateau », « voyage-grimpe », « voyage-nage », « voyage-nuit », « voyage-cache », « voyage-attend »
    // (le rendu impose alors la pose : RenduPilou.Voyager).
    public string Tenue = "";
    public IReadOnlyList<string> Objets = Array.Empty<string>(); // objets de boutique équipés
    public bool Cligne, Clin, Marche, Course, Baille, Etourdi, Fatigue, Salue;
    public bool Boude, Dos;                  // il boude (moue, sourcils froncés au repos) ; dos tourné (pas de visage)
    public int Regard, RegardY;              // -1, 0, 1
    public double Saut, Chute, Assis, Suspendu, Tremble; // en « anciens pixels » (grille 26 × 30)
    public int Stade = 2;                    // 1 Gouttelette, 2 Pilou, 3 Pilou Nimbus, 4 Pilou Astral
    public double Evolution;                 // 0..1 : animation d'évolution vers Stade (0 ou 1 : aucune)
    public string Reaction = "";             // « sueur » : gouttes sur les tempes

    public Allure Copie() => (Allure)MemberwiseClone();
}

// Points utiles aux effets dessinés autour de Pilou (en pixels de la grille 48 × 56, quelle que soit l'échelle du rendu).
public readonly record struct Geometrie(double Cx, double Cy, double Rx, double Ry, int Sommet, int Ey, int Pied);

// Espace de travail d'un rendu, à garder d'une image à l'autre pour ne rien allouer (Scene, vues animées). L'image
// rendue est G : elle est réécrite au rendu suivant fait avec le même tampon.
public sealed class TamponRendu
{
    internal uint[] G = Array.Empty<uint>(), M = Array.Empty<uint>();
    internal bool[] Bord = Array.Empty<bool>();

    internal void Preparer(int n)
    {
        if (G.Length != n)
        {
            G = new uint[n];
            M = new uint[n];
            Bord = new bool[n];
        }
        else
        {
            Array.Clear(G);
            Array.Clear(M);
        }
    }
}

// Pilou en pixels : corps procédural (ombrage tramé, reflet, cerne), visage, antenne, et tout ce qu'il porte,
// tiré de la banque de sprites. Même règle que outils/sprites/rendu.py et RenduPilou.java. Deux échelles :
// 1 (grille 48 × 56, le rendu de toujours) et 2 (rendu fin, grille 96 × 112 : corps calculé à la finesse double,
// sprites d'assets/sprites2x ou, à défaut, sprites 1× agrandis par Sprite.Agrandi).
public static class RenduPilou
{
    public const int W = 48, H = 56, C = 24;
    // Tenues de voyage des campagnes (docs/CAMPAGNES.md) : Allure.Tenue = "voyage-" + mode.
    public static readonly string[] Voyages = { "marche", "course", "bateau", "grimpe", "nage", "nuit", "cache", "attend" };
    public const double K = 1.25 * 48 / 26; // anciens pixels → pixels de cette grille
    private const uint Joue = 0xffffb37a, JoueClaire = 0xffffc89a, OmbreSol = 0x33000000, Silhouette = 0xffe8f4ff, SilhouetteBord = 0xff6cb6ff, Goutte = 0xff1f4f8a,
        GoutteClaire = 0xffb4dbff, Blanc = 0xffffffff;
    private static readonly uint[] Eclat = { 0xffffd8b0, 0xfffff6cc, 0xffb4dbff };
    private static readonly string[] Ordre = { "dos", "cou", "visage", "yeux", "tete", "main", "compagnon", "effet", "objet" };
    private static readonly HashSet<string> Chaudes = new() { "ambre", "braise", "comete", "corail-orange", "sable", "mandarine", "miel", "peche", "caramel", "potiron", "cuivre" };
    private static readonly uint[] BleuDefaut = { 0xff1f4f8a, 0xff4a8fdc, 0xff6cb6ff, 0xffb4dbff };
    private static readonly uint[] OrangeDefaut = { 0xff8a4a1f, 0xffd9803a, 0xfff69d50, 0xffffc89a };

    public static double StadeX(int s) => s switch { 1 => 0.72, 3 => 1.1, 4 => 0.9, _ => 1.0 };
    public static double StadeY(int s) => s switch { 1 => 0.74, 4 => 1.2, _ => 1.0 };

    public static string NomOeil(string expr) => expr switch
    {
        "concentre" => "concentre", "attente" => "haut", "grimace" => "grimace", "fete" or "caresse" => "heureux",
        "soulage" => "content", "dort" => "dort", "inquiet" => "inquiet",
        "joie" => "heureux", "peur" => "peur", "triste" => "triste", "surpris" => "surpris", "determine" => "determine",
        "fatigue" => "fatigue", "tendre" => "tendre", "colere" => "colere", "malice" => "malice", _ => "",
    };

    private static string? Etincelle(string expr) => expr switch
    {
        "concentre" or "attente" => "etincelle-roue", "grimace" => "etincelle-x", "dort" => "etincelle-dort",
        "inquiet" or "surpris" => "etincelle-alerte", "caresse" or "tendre" => "etincelle-coeur", "fatigue" => "etincelle-dort", _ => null,
    };

    // Dessins fins (2×) des petites formes que le rendu pose lui-même. « # » : couleur demandée.
    private static readonly string[] EtoileFine = { "...#...", "...#...", "..###..", "#######", "..###..", "...#...", "...#..." };
    private static readonly string[] JoueFine = { ".####.", "######", "#o####", ".####." };
    private static readonly string[] GoutteNimbusFine = { "..c..", "..c..", ".clc.", ".clc.", "clbbc", "cbbbc", ".ccc." };
    private static readonly string[] SueurFine = { "..gg..", "..gg..", ".gccg.", ".gccg.", "gcwccg", "gcwccg", "gccccg", ".gggg." };

    // Tenue de voyage « voyage-<mode> » : la pose que le mode impose (il marche sur place, rame, grimpe, dort…).
    // Ce que l'appelant a déjà demandé (regard, humeur) est gardé quand le mode ne dit rien.
    public static Allure Voyager(Allure p)
    {
        if (!p.Tenue.StartsWith("voyage-", StringComparison.Ordinal)) return p;
        string mode = p.Tenue[7..];
        if (Array.IndexOf(Voyages, mode) < 0) return p;
        double t = p.T;
        var q = p.Copie();
        switch (mode)
        {
            case "marche":
                q.Marche = true;
                q.Regard = p.Regard != 0 ? p.Regard : 1;
                break;
            case "course":
                q.Marche = q.Course = true;
                q.Regard = p.Regard != 0 ? p.Regard : 1;
                break;
            case "bateau":
                q.Assis = 1.0;
                q.Saut = 0.5 + 0.5 * Math.Sin(t / 520);       // tangage
                q.Regard = p.Regard != 0 ? p.Regard : 1;
                break;
            case "grimpe":
                q.Saut = 2.0 + 1.2 * Math.Abs(Math.Sin(t / 420)); // il se hisse, bras après bras
                q.RegardY = -1;
                break;
            case "nage":
                q.Assis = 1.0;
                q.Saut = 0.4 + 0.4 * Math.Sin(t / 450);
                break;
            case "nuit":
                q.Expr = "dort";
                break;
            case "cache":
                q.Assis = 1.0;
                q.Chute = 0.25;
                q.Regard = Guet[Mod((int)Math.Floor(t / 900), 4)]; // il guette d'un côté puis de l'autre
                break;
            case "attend":
                bool leve = Mod((int)Math.Floor(t / 1400), 3) == 2; // il regarde sa montre, puis relève les yeux
                q.Assis = 1.0;
                q.RegardY = leve ? 0 : 1;
                q.Regard = leve ? p.Regard : -1;
                break;
        }
        return q;
    }

    private static readonly int[] Guet = { -1, 0, 1, 0 };
    private static int Mod(int a, int n) => (a % n + n) % n;

    public static uint[] Teinte(Allure a, Banque b)
    {
        uint[] T(string n, uint[] d) => b.Teintes.TryGetValue(n, out var t) ? t : d;
        if (a.Expr == "inquiet") return Chaudes.Contains(a.Couleur) ? T("bleu", BleuDefaut) : T("orange", OrangeDefaut);
        return b.Teintes.TryGetValue(a.Couleur, out var te) ? te : T("bleu", BleuDefaut);
    }

    // Image ARGB (H × W) × échelle², ligne par ligne, animation d'évolution comprise.
    public static uint[] Rendre(Allure a, Banque b, int echelle = 1) => Rendre(a, b, out _, null, echelle);

    // debord : s'il est donné, reçoit les pixels des objets qui sortent de la grille (parapluie, longue-vue, livre
    // tenus au bout de la main…), en coordonnées de la grille rendue, dans l'ordre de dessin. Le PC les dessine dans
    // la marge de sa scène au lieu de les couper au bord de la grille ; le rendu dans la grille ne change pas.
    // echelle : 1 (grille 48 × 56) ou 2 (rendu fin, 96 × 112). tampon : espace de travail réutilisé (l'image rendue
    // est alors celle du tampon, réécrite au rendu suivant).
    public static uint[] Rendre(Allure a, Banque b, out Geometrie geo, List<(int X, int Y, uint C)>? debord = null, int echelle = 1,
        TamponRendu? tampon = null)
    {
        int ec = echelle == 2 ? 2 : 1;
        a = Voyager(a);
        double e = a.Evolution;
        if (e > 0 && e < 1 && a.Stade > 1)
        {
            if (e < 0.85)
            {
                // Silhouette claire qui alterne ancien et nouveau stade, de plus en plus vite.
                int k = (int)(Math.Pow(e / 0.85, 2) * 12) % 2;
                var q = a.Copie();
                q.Stade = k == 0 ? a.Stade - 1 : a.Stade;
                q.Evolution = 0;
                q.Expr = "repos";
                return Silhouetter(RendreStade(q, b, out geo, null, ec, null), ec);
            }
            var n = a.Copie();
            n.Evolution = 0;
            var g = RendreStade(n, b, out geo, debord, ec, tampon);
            Eclats(g, (e - 0.85) / 0.15, ec);
            return g;
        }
        return RendreStade(a, b, out geo, debord, ec, tampon);
    }

    private static uint[] Silhouetter(uint[] g, int ec)
    {
        int w = W * ec, h = H * ec;
        var o = new uint[w * h];
        bool Vide(int x, int y) => x < 0 || y < 0 || x >= w || y >= h || g[y * w + x] == 0 || g[y * w + x] == OmbreSol;
        for (int y = 0; y < h; y++)
        for (int x = 0; x < w; x++)
        {
            uint c = g[y * w + x];
            if (c == 0 || c == OmbreSol)
            {
                o[y * w + x] = c;
                continue;
            }
            bool bord = false;
            for (int n = 1; n <= ec; n++) bord |= Vide(x + n, y) || Vide(x - n, y) || Vide(x, y + n) || Vide(x, y - n);
            o[y * w + x] = bord ? SilhouetteBord : Silhouette;
        }
        return o;
    }

    // Petite étoile centrée en (x, y) : croix de 3 pixels à l'échelle 1, étoile à quatre branches de 7 pixels en fin.
    private static void EtoileDans(uint[] g, int x, int y, uint c, int ec)
    {
        int w = W * ec, h = H * ec;
        if (ec == 1)
        {
            foreach (var (u, v) in Croix)
                if (x + u is >= 0 and < W && y + v is >= 0 and < H) g[(y + v) * W + x + u] = c;
            return;
        }
        for (int j = 0; j < 7; j++)
        for (int i = 0; i < 7; i++)
            if (EtoileFine[j][i] == '#' && x + i - 3 >= 0 && x + i - 3 < w && y + j - 3 >= 0 && y + j - 3 < h) g[(y + j - 3) * w + x + i - 3] = c;
    }

    private static void Eclats(uint[] g, double k, int ec)
    {
        double r = (4 + k * 20) * ec;
        for (int i = 0; i < 12; i++)
        {
            double an = i * Math.PI / 6;
            int x = (int)Math.Round(C * ec + Math.Cos(an) * r), y = (int)Math.Round(36 * ec + Math.Sin(an) * r * 0.85);
            EtoileDans(g, x, y, Eclat[i % 3], ec);
        }
    }

    private static readonly (int, int)[] Croix = { (0, 0), (-1, 0), (1, 0), (0, -1), (0, 1) };

    // Ton du corps au rendu fin (indice dans la teinte : 1 ombre, 2 base, 3 clair). Trame à trois paliers (un quart,
    // un demi, trois quarts) au lieu du seul damier, ombre qui épouse le volume, reflet en croissant.
    private static int TonFin(int x, int y, double u, double v, double r2)
    {
        double d2 = (u + 0.62) * (u + 0.62) + (v + 0.62) * (v + 0.62);
        if (r2 > 0.47 && d2 < 0.2025) return 3;
        if (r2 > 0.40 && d2 < 0.16 && (x + y) % 2 == 0) return 3;
        double s = v + 0.16 * u * u;
        if (s > 0.66) return 1;
        if (s > 0.58) return x % 2 == 0 && y % 2 == 1 ? 2 : 1;
        if (s > 0.50) return (x + y) % 2 == 0 ? 1 : 2;
        if (s > 0.42) return x % 2 == 0 && y % 2 == 0 ? 1 : 2;
        return 2;
    }

    private static uint[] RendreStade(Allure a, Banque b, out Geometrie geo, List<(int X, int Y, uint C)>? debord, int ec, TamponRendu? tampon)
    {
        int w = W * ec, h = H * ec, c0 = C * ec;
        uint[] g, m;
        if (tampon is null)
        {
            g = new uint[w * h];
            m = new uint[w * h];
        }
        else
        {
            tampon.Preparer(w * h);
            g = tampon.G;
            m = tampon.M;
        }
        void Px(int x, int y, uint c)
        {
            if (c == 0) return;
            if (x >= 0 && y >= 0 && x < w && y < h) g[y * w + x] = c;
            else debord?.Add((x, y, c));
        }
        Sprite? S(string id) => ec == 1 ? b[id] : b.Fin(id);

        int st = a.Stade is >= 1 and <= 4 ? a.Stade : 2;
        var te = Teinte(a, b);
        double t = a.T;
        double periode = a.Expr == "dort" ? 4200 : a.Expr is "concentre" or "attente" ? 1600 : 2600;
        double bb = Math.Sin(2 * Math.PI * t / periode);
        double rx = 6.8 - 0.2 * bb, ry = 5.6 + 0.3 * bb;
        if (a.Expr == "caresse") { rx += 0.5; ry -= 0.5; }
        if (a.Expr == "dort") { rx += 0.6; ry -= 0.9; }
        rx += 1.2 * a.Chute + 0.7 * a.Assis - 0.8 * a.Suspendu;
        ry -= 1.4 * a.Chute + 0.8 * a.Assis - 1.1 * a.Suspendu;
        rx *= StadeX(st);
        ry *= StadeY(st);
        double cadence = a.Course ? 70 : 160;
        double marche = a.Marche ? Math.Abs(Math.Sin(t / cadence)) * (a.Course ? 1.3 : 0.8) : 0;
        double sol = (21.6 - a.Saut - marche + a.Assis) * K;
        double cx = C + (a.Tremble + a.Suspendu * Math.Sin(t / 260) * 1.2) * K;
        rx *= K;
        ry *= K;
        // Rendu fin : les mêmes grandeurs, deux fois plus grandes ; tout ce qui suit s'arrondit au pixel fin.
        if (ec != 1)
        {
            sol *= ec;
            cx = c0 + (cx - C) * ec;
            rx *= ec;
            ry *= ec;
        }
        double cy = sol - ry;
        int dx = (int)Math.Round(cx - c0, MidpointRounding.ToEven);

        // Ce que Pilou porte : cape du stade 4, accessoire, tenue, objets ; inconnus ignorés.
        var ids = new List<string>();
        if (st == 4) ids.Add("astral-cape");
        if (a.Accessoire != "") ids.Add("acc-" + a.Accessoire);
        if (a.Tenue != "" && b.Tenues.TryGetValue(a.Tenue, out var tenue)) ids.AddRange(tenue);
        ids.AddRange(a.Objets);
        var portes = ids.Select(S).Where(s => s is not null && !(a.Dos && s.Slot is "visage" or "yeux")).Select(s => s!).ToList();
        bool coiffe = portes.Any(s => s.Coiffe);

        int pied = (int)Math.Round(sol, MidpointRounding.ToEven);
        int sommet = (int)Math.Ceiling(cy - ry);
        int ey = (int)Math.Floor(cy - 6.6 * StadeY(st) * ec) + a.RegardY * 2 * ec;
        int dxf = dx + a.Regard * 2 * ec;
        double vitesse = a.Salue || a.Expr == "fete" ? 90 : a.Expr == "concentre" ? 300 : 650;
        int balance = a.Expr == "dort" ? 0 : Math.Clamp((int)Math.Round(Math.Sin(t / vitesse) * 0.9 * ec, MidpointRounding.ToEven)
            + (a.Marche ? -Math.Sign(a.Regard) * ec : 0), -ec, ec);
        int hautAntenne = (st == 1 ? 3 : 6) * ec;
        geo = new Geometrie(cx / ec, cy / ec, rx / ec, ry / ec, (int)Math.Floor(sommet / (double)ec), (int)Math.Floor(ey / (double)ec),
            (int)Math.Floor(pied / (double)ec));

        (int, int) Ancre(string n) => n switch
        {
            "tete" => (c0 + dx, sommet),
            "yeux" => (c0 + dxf, ey),
            "bouche" => (c0 + dxf, ey + 9 * ec),
            "cou" => (c0 + dx, Rond(cy + ry * 0.45)),
            "corps" => (c0 + dx, Rond(cy)),
            "main" => (Rond(cx + rx) - ec, Rond(cy + ry * 0.15)),
            "main-g" => (Rond(cx - rx), Rond(cy + ry * 0.15)),
            "pieds" => (c0 + dx, pied),
            "cote" => (Rond(cx + rx * 0.45), pied + 2 * ec),
            "antenne" => (c0 + dx + 2 * balance, sommet - hautAntenne),
            _ => (0, 0),
        };

        void Poser(Sprite s, bool miroir = false, int? x0 = null, int? y0 = null, string[]? im = null)
        {
            int x, y;
            if (x0 is null)
            {
                var (ax, ay) = Ancre(s.Ancre);
                x = ax + s.Dx;
                y = ay + s.Dy;
            }
            else
            {
                x = x0.Value;
                y = y0!.Value;
            }
            im ??= s.Image(t);
            var pal = s.Compilee();
            for (int j = 0; j < im.Length; j++)
            {
                var l = im[j];
                for (int i = 0; i < l.Length; i++)
                {
                    char ch = l[i];
                    if (ch == '.' || ch >= 128) continue;
                    uint c = pal[ch];
                    if (c == 0) continue;
                    if (c <= 4) c = te[c - 1];
                    Px(x + (miroir ? l.Length - 1 - i : i), y + j, c);
                }
            }
        }

        // Motif fin posé par le rendu : chaque lettre prend la couleur donnée par « couleur » (0 : rien).
        void Motif(int x, int y, string[] lignes, Func<char, uint> couleur)
        {
            for (int j = 0; j < lignes.Length; j++)
            for (int i = 0; i < lignes[j].Length; i++)
                Px(x + i, y + j, couleur(lignes[j][i]));
        }

        int Rang(Sprite s) => Array.IndexOf(Ordre, s.Slot) is var r && r >= 0 ? r : 9;
        void Etoile(int x, int y, uint c)
        {
            if (ec == 1)
                foreach (var (u, v) in Croix) Px(x + u, y + v, c);
            else Motif(x - 3, y - 3, EtoileFine, ch => ch == '#' ? c : 0);
        }

        // Astral : couronne d'étincelles en orbite (la moitié arrière passe derrière le corps).
        var orbite = new List<(int X, int Y, bool Devant, uint C)>();
        if (st == 4)
            for (int i = 0; i < 5; i++)
            {
                double an = t / 700 + i * 2 * Math.PI / 5;
                orbite.Add((Rond(cx + Math.Cos(an) * (rx + 4 * ec)), Rond(sommet + 4 * ec + Math.Sin(an) * 3.5 * ec), Math.Sin(an) > 0, Eclat[i % 3]));
            }

        foreach (var s in portes.Where(s => s.Derriere).OrderBy(Rang)) Poser(s);
        foreach (var o in orbite.Where(o => !o.Devant)) Etoile(o.X, o.Y, o.C);

        // Ombre au sol.
        if (a.Suspendu < 0.1)
        {
            int demi = (int)(Math.Max(6, 15 * StadeX(st) - a.Saut * 2.8) * ec);
            if (ec == 1)
                for (int x = C - demi; x < C + demi; x++)
                {
                    if (x < 0 || x >= W) continue;
                    if (g[52 * W + x] == 0) g[52 * W + x] = OmbreSol;
                    if (Math.Abs(x - C + 0.5) < demi - 3 && g[53 * W + x] == 0) g[53 * W + x] = OmbreSol;
                }
            else
                // Quatre lignes fines, bouts arrondis.
                for (int j = 0; j < 4; j++)
                {
                    int retrait = OmbreFine[j];
                    for (int x = c0 - demi + retrait; x < c0 + demi - retrait; x++)
                        if (x >= 0 && x < w && g[(104 + j) * w + x] == 0) g[(104 + j) * w + x] = OmbreSol;
                }
        }

        // Rendu fin : le corps (ellipse, bosses et bras du Nimbus, pieds) tient dans un cadre connu d'avance ; les
        // boucles du corps et du cerne ne parcourent que lui (mêmes pixels qu'en parcourant toute la grille).
        int bx0 = 0, bx1 = w - 1, by0 = 0, by1 = h - 1;
        if (ec != 1)
        {
            double mg = st == 3 ? 0.3 * ry + 1 : 1;
            double gx0 = cx - rx - mg, gx1 = cx + rx + mg, gy0 = cy - ry - mg, gy1 = cy + ry + mg;
            if (st == 3)
            {
                double bras = rx + 4.4 * ec + 1;
                gx0 = Math.Min(gx0, cx - bras);
                gx1 = Math.Max(gx1, cx + bras);
                gy0 = Math.Min(gy0, cy + ry * 0.28 - 3.2 * ec - 1);
                gy1 = Math.Max(gy1, cy + ry * 0.28 + 3.2 * ec + 1);
            }
            if (a.Assis <= 0.5)
            {
                gx0 = Math.Min(gx0, (C - 10) * ec + dx);
                gx1 = Math.Max(gx1, (C + 10) * ec + dx);
                gy0 = Math.Min(gy0, pied - 2 * ec);
                gy1 = Math.Max(gy1, pied + 4 * ec);
            }
            bx0 = Math.Max(0, (int)Math.Floor(gx0));
            bx1 = Math.Min(w - 1, (int)Math.Ceiling(gx1));
            by0 = Math.Max(0, (int)Math.Floor(gy0));
            by1 = Math.Min(h - 1, (int)Math.Ceiling(gy1));
        }

        // Corps : ombrage tramé, reflet ; Nimbus : volutes et bras ; puis cerne.
        var bosses = new List<(double X, double Y, double R)>();
        if (st == 3)
            foreach (var deg in new[] { -160, -125, -90, -55, -20, 170, 10 })
            {
                double an = deg * Math.PI / 180;
                bosses.Add((cx + Math.Cos(an) * rx * 0.84, cy + Math.Sin(an) * ry * 0.84, ry * (deg < 0 ? 0.3 : 0.24)));
            }
        for (int y = by0; y <= by1; y++)
        for (int x = bx0; x <= bx1; x++)
        {
            double u = (x + 0.5 - cx) / rx, v = (y + 0.5 - cy) / ry, r2 = u * u + v * v;
            bool dans = r2 <= 1;
            if (!dans && bosses.Count > 0)
            {
                foreach (var o in bosses)
                    if (Math.Pow(x + 0.5 - o.X, 2) + Math.Pow(y + 0.5 - o.Y, 2) <= o.R * o.R) dans = true;
                r2 = Math.Min(r2, 0.9);
            }
            if (!dans) continue;
            if (ec == 1)
            {
                bool damier = (x + y) % 2 == 0;
                bool reflet = u < -0.25 && v < -0.3;
                m[y * w + x] = reflet && (r2 > 0.45 || (r2 > 0.34 && damier)) ? te[3] : v > 0.62 || (v > 0.46 && damier) ? te[1] : te[2];
            }
            else m[y * w + x] = te[TonFin(x, y, u, v, r2)];
        }
        if (st == 3)
            foreach (int sg in new[] { -1, 1 })
            {
                double bx = cx + sg * (rx + 1.2 * ec), by = cy + ry * 0.28 + Math.Sin(t / 300 + sg) * 0.8 * ec;
                for (int y = by0; y <= by1; y++)
                for (int x = bx0; x <= bx1; x++)
                    if (Math.Pow((x + 0.5 - bx) / (3.2 * ec), 2) + Math.Pow((y + 0.5 - by) / (2.4 * ec), 2) <= 1) m[y * w + x] = te[1];
            }
        if (a.Assis <= 0.5)
        {
            int pas = a.Marche ? (int)Math.Floor(t / cadence) % 2 : -1;
            int largeur = (st == 1 ? 5 : 6) * ec;
            var pieds = st == 1 ? new[] { (0, C - 8), (1, C + 3) } : new[] { (0, C - 10), (1, C + 4) };
            foreach (var (cote, px1) in pieds)
            {
                int px0 = px1 * ec;
                int haut = pied - (pas == cote ? 2 * ec : 0);
                if (ec == 1)
                {
                    for (int x = px0; x < px0 + largeur; x++)
                    foreach (int y in new[] { haut, haut + 1 })
                        if (x + dx is >= 0 and < W && y is >= 0 and < H && (y == haut || (x > px0 && x < px0 + largeur - 1)))
                            m[y * W + x + dx] = te[1];
                }
                else
                    // Pied fin : quatre lignes, semelle arrondie.
                    for (int j = 0; j < 4; j++)
                    {
                        int retrait = PiedFin[j];
                        for (int x = px0 + retrait; x < px0 + largeur - retrait; x++)
                            if (x + dx >= 0 && x + dx < w && haut + j >= 0 && haut + j < h) m[(haut + j) * w + x + dx] = te[1];
                    }
            }
        }
        if (ec == 1)
        {
            for (int y = 0; y < H; y++)
            for (int x = 0; x < W; x++)
            {
                uint c = m[y * W + x];
                if (c == 0) continue;
                bool bord = x == 0 || y == 0 || x == W - 1 || y == H - 1 || m[y * W + x - 1] == 0 || m[y * W + x + 1] == 0
                            || m[(y - 1) * W + x] == 0 || m[(y + 1) * W + x] == 0;
                g[y * W + x] = bord ? te[0] : c;
            }
        }
        else
        {
            // Cerne fin : deux pixels d'épaisseur, diagonales comprises (tout ce qui est à moins de √5 du vide).
            bool Vide(int x, int y) => x < 0 || y < 0 || x >= w || y >= h || m[y * w + x] == 0;
            var bord1 = tampon?.Bord ?? new bool[w * h];
            for (int y = by0; y <= by1; y++)
            for (int x = bx0; x <= bx1; x++)
                bord1[y * w + x] = m[y * w + x] != 0 && (Vide(x - 1, y) || Vide(x + 1, y) || Vide(x, y - 1) || Vide(x, y + 1));
            for (int y = by0; y <= by1; y++)
            for (int x = bx0; x <= bx1; x++)
            {
                uint c = m[y * w + x];
                if (c == 0) continue;
                // Hors du cadre, tout est vide : le test du vide passe avant la lecture du premier passage.
                bool bord = x == 0 || y == 0 || x == w - 1 || y == h - 1;
                for (int v = -1; v <= 1 && !bord; v++)
                for (int u = -1; u <= 1; u++)
                {
                    int i = (y + v) * w + x + u;
                    if (m[i] == 0 || bord1[i])
                    {
                        bord = true;
                        break;
                    }
                }
                g[y * w + x] = bord ? te[0] : c;
            }
        }
        if (st == 3)
            foreach (int sg in new[] { -1, 1 })
                for (int k = 0; k < 7 * ec; k++)
                {
                    double pasK = k / (double)ec;
                    double an = (sg < 0 ? 200 + pasK * 22 : -20 - pasK * 22) * Math.PI / 180;
                    int x = Rond(cx + sg * rx * 0.55 + Math.Cos(an) * 3 * ec), y = Rond(cy - ry * 0.55 + Math.Sin(an) * 2 * ec);
                    Px(x, y, te[3]);
                    if (ec == 2) Px(x, y + 1, te[3]);
                }

        // Visage (aucun s'il tourne le dos).
        bool moue = a.Boude && a.Expr == "repos";
        string nom = a.Etourdi ? "spirale" : NomOeil(a.Expr) is { Length: > 0 } n0 ? n0 : moue ? "boude" : a.Fatigue ? "fatigue" : "ouvert";
        if (a.Baille) nom = "dort";
        if (st == 4 && nom == "ouvert") nom = "serein";
        bool peut = a.Expr is "repos" or "inquiet" or "attente" or "neutre" && !a.Etourdi;
        string og = peut && a.Cligne ? "cligne" : nom;
        string od = peut && (a.Cligne || a.Clin) ? "cligne" : nom;
        if (!a.Dos && st == 1 && og == "ouvert" && S("oeil-ouvert-g") is { } grand)
        {
            Poser(grand, false, (C - 10) * ec + dxf, ey - ec);
            if (od == "ouvert") Poser(grand, true, (C + 2) * ec + dxf, ey - ec);
            else if (S("oeil-" + od) is { } so) Poser(so, true, (C + 3) * ec + dxf, ey);
        }
        else if (!a.Dos)
        {
            int ecart = st == 1 ? 1 : 0;
            if (S("oeil-" + og) is { } sg) Poser(sg, false, (C - 10 + ecart) * ec + dxf + sg.Dx, ey + sg.Dy);
            // Œil droit dessiné à part (regard dissymétrique : malice) : posé tel quel, sans miroir.
            if (S("oeil-" + od + "-d") is { } sdd) Poser(sdd, false, (C + 4 - ecart) * ec + dxf + sdd.Dx, ey + sdd.Dy);
            else if (S("oeil-" + od) is { } sd) Poser(sd, true, (C + 10 - ecart) * ec + dxf - sd.Dx - sd.W, ey + sd.Dy);
        }
        var bo = a.Dos ? null : S(a.Baille ? "bouche-baille" : moue ? "bouche-boude" : "bouche-" + a.Expr) ?? S("bouche-repos");
        if (bo is not null) Poser(bo, false, c0 - bo.W / 2 + dxf, ey + 9 * ec + bo.Dy);
        if (a.Expr is "fete" or "caresse" or "joie" or "tendre" && !a.Dos)
        {
            int joue = Rond(rx) - ec;
            if (ec == 1)
                foreach (int jx in new[] { C - joue + dxf, C + joue - 3 + dxf })
                    for (int i = 0; i < 3; i++)
                    for (int j = 0; j < 2; j++)
                        Px(jx + i, ey + 7 + j, Joue);
            else
            {
                Motif(c0 - joue + dxf, ey + 14, JoueFine, ch => ch == '#' ? Joue : ch == 'o' ? JoueClaire : 0);
                Motif(c0 + joue - 6 + dxf, ey + 14, JoueFine, ch => ch == '#' ? Joue : ch == 'o' ? JoueClaire : 0);
            }
        }
        // Marque de l'humeur (larme, goutte, signe de colère…) : sprite « marque-<humeur> », sur l'ancre des yeux.
        if (!a.Dos && S("marque-" + a.Expr) is { } marque) Poser(marque);

        // Antenne(s) et étincelle(s), sauf sous un chapeau.
        if (!coiffe)
        {
            string sp = Etincelle(a.Expr) ?? ((a.Expr == "fete" ? Math.Floor(t / 120) % 2 == 0 : Math.Floor(t / 900) % 2 == 0)
                ? "etincelle-grand" : "etincelle-petit");
            var spr = S(sp);
            string[]? im = null;
            if (sp == "etincelle-roue" && spr is not null && spr.Images.Count > 0)
                im = spr.Images[(int)(Math.Floor(t / (a.Expr == "concentre" ? 90 : 260)) % spr.Images.Count)];
            var tiges = st == 3 ? new[] { (c0 - 7 * ec + dx, -1), (c0 + 5 * ec + dx, 1) } : new[] { (c0 - ec + dx, 0) };
            int baseY = sommet + (st == 3 ? 3 * ec : 0);
            foreach (var (x0, pente) in tiges)
            {
                for (int k = 1; k <= hautAntenne; k++)
                {
                    if (ec == 1)
                    {
                        int dec = (k > hautAntenne / 2 ? balance : 0) + pente * (k / 3);
                        Px(x0 + dec, baseY - k, te[0]);
                        Px(x0 + 1 + dec, baseY - k, te[0]);
                    }
                    else
                    {
                        // Tige fine : elle se courbe peu à peu vers la pointe ; un filet d'ombre lui donne du volume.
                        int courbe = Math.Abs(balance) * Math.Max(0, 2 * k - hautAntenne + 2) / (hautAntenne + 2);
                        int dec = (balance > 0 ? courbe : -courbe) + pente * (k / 3);
                        for (int i = 0; i < 4; i++) Px(x0 + i + dec, baseY - k, i == 1 ? te[1] : te[0]);
                    }
                }
                if (spr is not null)
                {
                    int pointe = x0 + ec + balance + pente * (hautAntenne / 3);
                    Poser(spr, false, pointe + spr.Dx, baseY - hautAntenne + spr.Dy, im);
                }
            }
        }

        // Nimbus : petite traînée de gouttes qui tombent.
        if (st == 3)
        {
            double[] fx = { -0.6, 0.55, -0.1 };
            for (int i = 0; i < 3; i++)
            {
                double ph = (t / 900 + i / 3.0) % 1;
                int x = Rond(cx + rx * fx[i]), y = Rond(cy + ry * 0.7 + ph * 9 * ec);
                if (y < pied) continue;
                if (ec == 1)
                {
                    Px(x, y, te[3]);
                    Px(x, y + 1, te[2]);
                    Px(x - 1, y + 1, te[0]);
                    Px(x + 1, y + 1, te[0]);
                    Px(x, y + 2, te[0]);
                }
                else Motif(x - 2, y, GoutteNimbusFine, ch => ch == 'c' ? te[0] : ch == 'l' ? te[3] : ch == 'b' ? te[2] : 0);
            }
        }

        foreach (var s in portes.Where(s => !s.Derriere).OrderBy(Rang)) Poser(s);
        foreach (var o in orbite.Where(o => o.Devant)) Etoile(o.X, o.Y, o.C);

        // Réaction « sueur » : deux gouttes qui glissent sur les tempes.
        if (a.Reaction == "sueur")
            for (int i = 0; i < 2; i++)
            {
                int sg = i == 0 ? -1 : 1;
                double ph = (t / 1100 + i * 0.5) % 1;
                int x = Rond(cx + sg * (rx - 2 * ec)), y = Rond(ey - 2 * ec + ph * 8 * ec);
                if (ec == 1)
                {
                    Px(x, y - 1, Goutte);
                    foreach (var (u, v) in new[] { (-1, 0), (1, 0), (-1, 1), (1, 1), (0, 2) }) Px(x + u, y + v, Goutte);
                    Px(x, y, GoutteClaire);
                    Px(x, y + 1, Blanc);
                }
                else Motif(x - 2, y - 2, SueurFine, ch => ch == 'g' ? Goutte : ch == 'c' ? GoutteClaire : ch == 'w' ? Blanc : 0);
            }
        return g;
    }

    private static readonly int[] OmbreFine = { 2, 0, 3, 7 }, PiedFin = { 0, 0, 1, 3 };

    // Arrondi « au pair », comme round() de Python : les trois rendus tombent sur les mêmes pixels.
    // Ancre de la main de Pilou du côté sens (+1 : « main », à droite à l'écran ; −1 : « main-g »), grille 48 × 56.
    public static (int X, int Y) AncreMain(Geometrie g, int sens) =>
        (sens >= 0 ? Rond(g.Cx + g.Rx) - 1 : Rond(g.Cx - g.Rx), Rond(g.Cy + g.Ry * 0.15));

    private static int Rond(double v) => (int)Math.Round(v, MidpointRounding.ToEven);
}
