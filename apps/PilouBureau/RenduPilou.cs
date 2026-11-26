namespace PilouBureau;

// Ce qu'on demande au dessin de Pilou (sans WPF : testable, et identique à RenduPilou.java côté Android).
public sealed class Allure
{
    public string Expr = "repos";            // repos, concentre, attente, grimace, fete, soulage, dort, inquiet, caresse
    public double T;                         // horloge de l'animation (ms)
    public string Couleur = "bleu";          // nom d'une teinte (assets/teintes.txt)
    public string Accessoire = "";           // récompense de niveau : sprite « acc-<nom> »
    public string Tenue = "";                // tenue d'activité (assets/tenues.txt)
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

// Points utiles aux effets dessinés autour de Pilou (en pixels de la grille 48 × 56).
public readonly record struct Geometrie(double Cx, double Cy, double Rx, double Ry, int Sommet, int Ey, int Pied);

// Pilou en 48 × 56 : corps procédural (ombrage tramé, reflet, cerne), visage, antenne, et tout ce qu'il porte,
// tiré de la banque de sprites. Même règle que outils/sprites/rendu.py et RenduPilou.java.
public static class RenduPilou
{
    public const int W = 48, H = 56, C = 24;
    public const double K = 1.25 * 48 / 26; // anciens pixels → pixels de cette grille
    private const uint Joue = 0xffffb37a, OmbreSol = 0x33000000, Silhouette = 0xffe8f4ff, SilhouetteBord = 0xff6cb6ff, Goutte = 0xff1f4f8a,
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
        "soulage" => "content", "dort" => "dort", "inquiet" => "inquiet", _ => "",
    };

    private static string? Etincelle(string expr) => expr switch
    {
        "concentre" or "attente" => "etincelle-roue", "grimace" => "etincelle-x", "dort" => "etincelle-dort",
        "inquiet" => "etincelle-alerte", "caresse" => "etincelle-coeur", _ => null,
    };

    public static uint[] Teinte(Allure a, Banque b)
    {
        uint[] T(string n, uint[] d) => b.Teintes.TryGetValue(n, out var t) ? t : d;
        if (a.Expr == "inquiet") return Chaudes.Contains(a.Couleur) ? T("bleu", BleuDefaut) : T("orange", OrangeDefaut);
        return b.Teintes.TryGetValue(a.Couleur, out var te) ? te : T("bleu", BleuDefaut);
    }

    // Image ARGB H × W (ligne par ligne), animation d'évolution comprise.
    public static uint[] Rendre(Allure a, Banque b) => Rendre(a, b, out _);

    public static uint[] Rendre(Allure a, Banque b, out Geometrie geo)
    {
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
                return Silhouetter(RendreStade(q, b, out geo));
            }
            var n = a.Copie();
            n.Evolution = 0;
            var g = RendreStade(n, b, out geo);
            Eclats(g, (e - 0.85) / 0.15);
            return g;
        }
        return RendreStade(a, b, out geo);
    }

    private static uint[] Silhouetter(uint[] g)
    {
        var o = new uint[W * H];
        bool Vide(int x, int y) => x < 0 || y < 0 || x >= W || y >= H || g[y * W + x] == 0 || g[y * W + x] == OmbreSol;
        for (int y = 0; y < H; y++)
        for (int x = 0; x < W; x++)
        {
            uint c = g[y * W + x];
            if (c == 0 || c == OmbreSol) o[y * W + x] = c;
            else o[y * W + x] = Vide(x + 1, y) || Vide(x - 1, y) || Vide(x, y + 1) || Vide(x, y - 1) ? SilhouetteBord : Silhouette;
        }
        return o;
    }

    private static void Eclats(uint[] g, double k)
    {
        double r = 4 + k * 20;
        for (int i = 0; i < 12; i++)
        {
            double an = i * Math.PI / 6;
            int x = (int)Math.Round(C + Math.Cos(an) * r), y = (int)Math.Round(36 + Math.Sin(an) * r * 0.85);
            foreach (var (u, v) in Croix)
                if (x + u is >= 0 and < W && y + v is >= 0 and < H) g[(y + v) * W + x + u] = Eclat[i % 3];
        }
    }

    private static readonly (int, int)[] Croix = { (0, 0), (-1, 0), (1, 0), (0, -1), (0, 1) };

    private static uint[] RendreStade(Allure a, Banque b, out Geometrie geo)
    {
        var g = new uint[W * H];
        void Px(int x, int y, uint c)
        {
            if (c != 0 && x >= 0 && y >= 0 && x < W && y < H) g[y * W + x] = c;
        }

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
        double cy = sol - ry;
        int dx = (int)Math.Round(cx - C, MidpointRounding.ToEven);

        // Ce que Pilou porte : cape du stade 4, accessoire, tenue, objets ; inconnus ignorés.
        var ids = new List<string>();
        if (st == 4) ids.Add("astral-cape");
        if (a.Accessoire != "") ids.Add("acc-" + a.Accessoire);
        if (a.Tenue != "" && b.Tenues.TryGetValue(a.Tenue, out var tenue)) ids.AddRange(tenue);
        ids.AddRange(a.Objets);
        var portes = ids.Select(i => b[i]).Where(s => s is not null && !(a.Dos && s.Slot is "visage" or "yeux")).Select(s => s!).ToList();
        bool coiffe = portes.Any(s => s.Coiffe);

        int pied = (int)Math.Round(sol, MidpointRounding.ToEven);
        int sommet = (int)Math.Ceiling(cy - ry);
        int ey = (int)Math.Floor(cy - 6.6 * StadeY(st)) + a.RegardY * 2;
        int dxf = dx + a.Regard * 2;
        double vitesse = a.Salue || a.Expr == "fete" ? 90 : a.Expr == "concentre" ? 300 : 650;
        int balance = a.Expr == "dort" ? 0 : Math.Clamp((int)Math.Round(Math.Sin(t / vitesse) * 0.9, MidpointRounding.ToEven)
            + (a.Marche ? -Math.Sign(a.Regard) : 0), -1, 1);
        int hautAntenne = st == 1 ? 3 : 6;
        geo = new Geometrie(cx, cy, rx, ry, sommet, ey, pied);

        (int, int) Ancre(string n) => n switch
        {
            "tete" => (C + dx, sommet),
            "yeux" => (C + dxf, ey),
            "bouche" => (C + dxf, ey + 9),
            "cou" => (C + dx, Rond(cy + ry * 0.45)),
            "corps" => (C + dx, Rond(cy)),
            "main" => (Rond(cx + rx) - 1, Rond(cy + ry * 0.15)),
            "main-g" => (Rond(cx - rx), Rond(cy + ry * 0.15)),
            "pieds" => (C + dx, pied),
            "cote" => (Rond(cx + rx * 0.45), pied + 2),
            "antenne" => (C + dx + 2 * balance, sommet - hautAntenne),
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
            for (int j = 0; j < im.Length; j++)
            {
                var l = im[j];
                for (int i = 0; i < l.Length; i++)
                {
                    char ch = l[i];
                    if (ch == '.' || !s.Palette.TryGetValue(ch, out var code)) continue;
                    uint c = code switch
                    {
                        "@contour" => te[0], "@ombre" => te[1], "@base" => te[2], "@clair" => te[3], _ => Sprite.Couleur(code),
                    };
                    Px(x + (miroir ? l.Length - 1 - i : i), y + j, c);
                }
            }
        }

        int Rang(Sprite s) => Array.IndexOf(Ordre, s.Slot) is var r && r >= 0 ? r : 9;
        void Etoile(int x, int y, uint c)
        {
            foreach (var (u, v) in Croix) Px(x + u, y + v, c);
        }

        // Astral : couronne d'étincelles en orbite (la moitié arrière passe derrière le corps).
        var orbite = new List<(int X, int Y, bool Devant, uint C)>();
        if (st == 4)
            for (int i = 0; i < 5; i++)
            {
                double an = t / 700 + i * 2 * Math.PI / 5;
                orbite.Add((Rond(cx + Math.Cos(an) * (rx + 4)), Rond(sommet + 4 + Math.Sin(an) * 3.5), Math.Sin(an) > 0, Eclat[i % 3]));
            }

        foreach (var s in portes.Where(s => s.Derriere).OrderBy(Rang)) Poser(s);
        foreach (var o in orbite.Where(o => !o.Devant)) Etoile(o.X, o.Y, o.C);

        // Ombre au sol.
        if (a.Suspendu < 0.1)
        {
            int demi = (int)Math.Max(6, 15 * StadeX(st) - a.Saut * 2.8);
            for (int x = C - demi; x < C + demi; x++)
            {
                if (x < 0 || x >= W) continue;
                if (g[52 * W + x] == 0) g[52 * W + x] = OmbreSol;
                if (Math.Abs(x - C + 0.5) < demi - 3 && g[53 * W + x] == 0) g[53 * W + x] = OmbreSol;
            }
        }

        // Corps : ombrage tramé, reflet ; Nimbus : volutes et bras ; puis cerne.
        var m = new uint[W * H];
        var bosses = new List<(double X, double Y, double R)>();
        if (st == 3)
            foreach (var deg in new[] { -160, -125, -90, -55, -20, 170, 10 })
            {
                double an = deg * Math.PI / 180;
                bosses.Add((cx + Math.Cos(an) * rx * 0.84, cy + Math.Sin(an) * ry * 0.84, ry * (deg < 0 ? 0.3 : 0.24)));
            }
        for (int y = 0; y < H; y++)
        for (int x = 0; x < W; x++)
        {
            double u = (x + 0.5 - cx) / rx, v = (y + 0.5 - cy) / ry, r2 = u * u + v * v;
            bool dans = r2 <= 1;
            if (!dans && bosses.Count > 0)
            {
                dans = bosses.Any(o => Math.Pow(x + 0.5 - o.X, 2) + Math.Pow(y + 0.5 - o.Y, 2) <= o.R * o.R);
                r2 = Math.Min(r2, 0.9);
            }
            if (!dans) continue;
            bool damier = (x + y) % 2 == 0;
            bool reflet = u < -0.25 && v < -0.3;
            m[y * W + x] = reflet && (r2 > 0.45 || (r2 > 0.34 && damier)) ? te[3] : v > 0.62 || (v > 0.46 && damier) ? te[1] : te[2];
        }
        if (st == 3)
            foreach (int sg in new[] { -1, 1 })
            {
                double bx = cx + sg * (rx + 1.2), by = cy + ry * 0.28 + Math.Sin(t / 300 + sg) * 0.8;
                for (int y = 0; y < H; y++)
                for (int x = 0; x < W; x++)
                    if (Math.Pow((x + 0.5 - bx) / 3.2, 2) + Math.Pow((y + 0.5 - by) / 2.4, 2) <= 1) m[y * W + x] = te[1];
            }
        if (a.Assis <= 0.5)
        {
            int pas = a.Marche ? (int)Math.Floor(t / cadence) % 2 : -1;
            int largeur = st == 1 ? 5 : 6;
            var pieds = st == 1 ? new[] { (0, C - 8), (1, C + 3) } : new[] { (0, C - 10), (1, C + 4) };
            foreach (var (cote, px0) in pieds)
            {
                int haut = pied - (pas == cote ? 2 : 0);
                for (int x = px0; x < px0 + largeur; x++)
                foreach (int y in new[] { haut, haut + 1 })
                    if (x + dx is >= 0 and < W && y is >= 0 and < H && (y == haut || (x > px0 && x < px0 + largeur - 1)))
                        m[y * W + x + dx] = te[1];
            }
        }
        for (int y = 0; y < H; y++)
        for (int x = 0; x < W; x++)
        {
            uint c = m[y * W + x];
            if (c == 0) continue;
            bool bord = x == 0 || y == 0 || x == W - 1 || y == H - 1 || m[y * W + x - 1] == 0 || m[y * W + x + 1] == 0
                        || m[(y - 1) * W + x] == 0 || m[(y + 1) * W + x] == 0;
            g[y * W + x] = bord ? te[0] : c;
        }
        if (st == 3)
            foreach (int sg in new[] { -1, 1 })
                for (int k = 0; k < 7; k++)
                {
                    double an = (sg < 0 ? 200 + k * 22 : -20 - k * 22) * Math.PI / 180;
                    Px(Rond(cx + sg * rx * 0.55 + Math.Cos(an) * 3), Rond(cy - ry * 0.55 + Math.Sin(an) * 2), te[3]);
                }

        // Visage (aucun s'il tourne le dos).
        bool moue = a.Boude && a.Expr == "repos";
        string nom = a.Etourdi ? "spirale" : NomOeil(a.Expr) is { Length: > 0 } n0 ? n0 : moue ? "boude" : a.Fatigue ? "fatigue" : "ouvert";
        if (a.Baille) nom = "dort";
        if (st == 4 && nom == "ouvert") nom = "serein";
        bool peut = a.Expr is "repos" or "inquiet" or "attente" && !a.Etourdi;
        string og = peut && a.Cligne ? "cligne" : nom;
        string od = peut && (a.Cligne || a.Clin) ? "cligne" : nom;
        if (!a.Dos && st == 1 && og == "ouvert" && b["oeil-ouvert-g"] is { } grand)
        {
            Poser(grand, false, C - 10 + dxf, ey - 1);
            if (od == "ouvert") Poser(grand, true, C + 2 + dxf, ey - 1);
            else if (b["oeil-" + od] is { } so) Poser(so, true, C + 3 + dxf, ey);
        }
        else if (!a.Dos)
        {
            int ecart = st == 1 ? 1 : 0;
            if (b["oeil-" + og] is { } sg) Poser(sg, false, C - 10 + ecart + dxf, ey);
            if (b["oeil-" + od] is { } sd) Poser(sd, true, C + 4 - ecart + dxf, ey);
        }
        var bo = a.Dos ? null : b[a.Baille ? "bouche-baille" : moue ? "bouche-boude" : "bouche-" + a.Expr] ?? b["bouche-repos"];
        if (bo is not null) Poser(bo, false, C - bo.W / 2 + dxf, ey + 9);
        if (a.Expr is "fete" or "caresse" && !a.Dos)
        {
            int joue = Rond(rx) - 1;
            foreach (int jx in new[] { C - joue + dxf, C + joue - 3 + dxf })
                for (int i = 0; i < 3; i++)
                for (int j = 0; j < 2; j++)
                    Px(jx + i, ey + 7 + j, Joue);
        }

        // Antenne(s) et étincelle(s), sauf sous un chapeau.
        if (!coiffe)
        {
            string sp = Etincelle(a.Expr) ?? ((a.Expr == "fete" ? Math.Floor(t / 120) % 2 == 0 : Math.Floor(t / 900) % 2 == 0)
                ? "etincelle-grand" : "etincelle-petit");
            var spr = b[sp];
            string[]? im = null;
            if (sp == "etincelle-roue" && spr is not null && spr.Images.Count > 0)
                im = spr.Images[(int)(Math.Floor(t / (a.Expr == "concentre" ? 90 : 260)) % spr.Images.Count)];
            var tiges = st == 3 ? new[] { (C - 7 + dx, -1), (C + 5 + dx, 1) } : new[] { (C - 1 + dx, 0) };
            int baseY = sommet + (st == 3 ? 3 : 0);
            foreach (var (x0, pente) in tiges)
            {
                for (int k = 1; k <= hautAntenne; k++)
                {
                    int dec = (k > hautAntenne / 2 ? balance : 0) + pente * (k / 3);
                    Px(x0 + dec, baseY - k, te[0]);
                    Px(x0 + 1 + dec, baseY - k, te[0]);
                }
                if (spr is not null)
                {
                    int pointe = x0 + 1 + balance + pente * (hautAntenne / 3);
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
                int x = Rond(cx + rx * fx[i]), y = Rond(cy + ry * 0.7 + ph * 9);
                if (y < pied) continue;
                Px(x, y, te[3]);
                Px(x, y + 1, te[2]);
                Px(x - 1, y + 1, te[0]);
                Px(x + 1, y + 1, te[0]);
                Px(x, y + 2, te[0]);
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
                int x = Rond(cx + sg * (rx - 2)), y = Rond(ey - 2 + ph * 8);
                Px(x, y - 1, Goutte);
                foreach (var (u, v) in new[] { (-1, 0), (1, 0), (-1, 1), (1, 1), (0, 2) }) Px(x + u, y + v, Goutte);
                Px(x, y, GoutteClaire);
                Px(x, y + 1, Blanc);
            }
        return g;
    }

    // Arrondi « au pair », comme round() de Python : les trois rendus tombent sur les mêmes pixels.
    private static int Rond(double v) => (int)Math.Round(v, MidpointRounding.ToEven);
}
