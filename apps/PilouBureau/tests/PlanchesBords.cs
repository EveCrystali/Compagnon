using PilouBureau;
using Xunit;

// Rendus de contrôle (PNG) des scènes posées à côté de Pilou, des deux côtés de la fenêtre, et de la fenêtre
// découpée sur un écran à gauche du principal (X négatif). Mêmes calculs que la fenêtre (Placement.cs).
// Seulement si PILOU_PLANCHES_BORDS donne un dossier :
//     PILOU_PLANCHES_BORDS=/tmp/bords dotnet test --filter PlanchesBords
public class PlanchesBords
{
    private static readonly string? Dossier = Environment.GetEnvironmentVariable("PILOU_PLANCHES_BORDS");
    private static readonly Lazy<Banque> B = new(() => Banque.DepuisDossier(Path.Combine(DefenseTests.Racine(), "assets")));

    // Toile en unités de la fenêtre, z pixels par unité.
    private sealed class Toile
    {
        public readonly int W, H;
        public readonly double Z;
        public readonly uint[] Px;
        public double Ox, Oy; // décalage (unités) du repère courant
        public double? ClipX0, ClipX1;

        public Toile(double largeur, double hauteur, double z, uint fond)
        {
            Z = z;
            W = (int)Math.Ceiling(largeur * z);
            H = (int)Math.Ceiling(hauteur * z);
            Px = new uint[W * H];
            Array.Fill(Px, fond);
        }

        private bool Dedans(double ux) => (ClipX0 is null || ux >= ClipX0) && (ClipX1 is null || ux < ClipX1);

        public void Rect(double x, double y, double w, double h, uint c)
        {
            int x0 = (int)Math.Round((Ox + x) * Z), y0 = (int)Math.Round((Oy + y) * Z);
            int x1 = (int)Math.Round((Ox + x + w) * Z), y1 = (int)Math.Round((Oy + y + h) * Z);
            for (int py = Math.Max(0, y0); py < Math.Min(H, y1); py++)
            for (int px = Math.Max(0, x0); px < Math.Min(W, x1); px++)
                if (Dedans(px / Z - Ox)) Px[py * W + px] = ToileDefense.Melanger(Px[py * W + px], c);
        }

        public void Cadre(double x, double y, double w, double h, uint c)
        {
            double e = 1 / Z;
            Rect(x, y, w, e, c);
            Rect(x, y + h - e, w, e, c);
            Rect(x, y, e, h, c);
            Rect(x + w - e, y, e, h, c);
        }

        // Un dessin de la banque comme Pixels : cellule (c, r) en ((c + 1) t, (r + 1) t).
        public void Grille(uint[,] g, double x, double y, double t, bool miroir = false)
        {
            int h = g.GetLength(0), w = g.GetLength(1);
            for (int r = 0; r < h; r++)
            for (int c = 0; c < w; c++)
            {
                uint v = g[r, miroir ? w - 1 - c : c];
                if (v != 0) Rect(x + (c + 1) * t, y + (r + 1) * t, t, t, v);
            }
        }

        public void Image(uint[] px, int gw, int gh, double x, double y, double t)
        {
            for (int r = 0; r < gh; r++)
            for (int c = 0; c < gw; c++)
                if (px[r * gw + c] != 0) Rect(x + c * t, y + r * t, t, t, px[r * gw + c]);
        }

        public void Ligne(Pt a, Pt b, uint c, double ep = 1.2)
        {
            int n = (int)Math.Ceiling(Math.Max(Math.Abs(b.X - a.X), Math.Abs(b.Y - a.Y)) * Z) + 1;
            for (int i = 0; i <= n; i++)
            {
                double k = i / (double)n;
                Rect(a.X + (b.X - a.X) * k - ep / 2, a.Y + (b.Y - a.Y) * k - ep / 2, ep, ep, c);
            }
        }

        public void Texte(string s, double x, double y, uint c, double t) => Grille(Masque(Police.Texte(s), c), x, y, t);

        private static uint[,] Masque(int[,] m, uint c)
        {
            var g = new uint[m.GetLength(0), m.GetLength(1)];
            for (int r = 0; r < m.GetLength(0); r++)
            for (int k = 0; k < m.GetLength(1); k++)
                g[r, k] = m[r, k] != 0 ? c : 0;
            return g;
        }
    }

    private const uint Fond = 0xff2d333b, Repere = 0x40ffffff, Fil = 0xd9f6f8fa, Eau1 = 0xff4a8fdc, Eau2 = 0xffb4dbff, Eau3 = 0xff1f4f8a,
        Orange = 0xfff69d50, Rouge = 0xffff5050, Vert = 0xff57d97a;

    private static uint[,] G(string id, double t = 0) => Banque.Grille(B.Value[id]!, t);

    private static int[,] Motif(uint[,] g)
    {
        var m = new int[g.GetLength(0), g.GetLength(1)];
        for (int r = 0; r < g.GetLength(0); r++)
        for (int c = 0; c < g.GetLength(1); c++)
            m[r, c] = g[r, c] != 0 ? 1 : 0;
        return m;
    }

    private static (uint[] Px, Geometrie Geo) Pilou(int regard, int stade = 2, string expr = "concentre", IReadOnlyList<string>? objets = null)
    {
        var a = new Allure { Expr = expr, Regard = regard, Stade = stade, Objets = objets ?? Array.Empty<string>() };
        var px = RenduPilou.Rendre(a, B.Value, out var geo);
        return (px, geo);
    }

    private static void Fenetre(Toile o, bool aGauche)
    {
        o.Cadre(0, 0, Placement.LargeurBase, Placement.HauteurBulle + Placement.HauteurScene, Repere);
        o.Rect(0, Placement.SolY, Placement.LargeurBase, 1 / o.Z, Repere);
    }

    private static void DessinerPilou(Toile o, bool aGauche, uint[] px) =>
        o.Image(px, RenduPilou.W, RenduPilou.H, Placement.SceneX(aGauche) + Placement.MargeX, Placement.HauteurBulle + Placement.MargeY, Placement.PX);

    // Pêche : eau, Pilou (tourné vers l'eau), canne dans la main, fil du bout de la canne au bouchon, « ! ».
    private static void Peche(Toile o, bool aGauche, double lance, bool mord, int stade = 2)
    {
        int sens = Placement.Sens(aGauche);
        var (px, geo) = Pilou(sens, stade, mord ? "attente" : "concentre");
        var canne = G("canne");
        var g = Placement.Peche(aGauche, geo, canne.GetLength(1), Placement.ReperesCanne(Motif(canne)));
        Fenetre(o, aGauche);
        for (int i = 0; i < 28; i++)
        {
            o.Rect(g.Eau.X + i * 4, g.Eau.Y, 4, 4, i % 4 == 0 ? Eau2 : Eau1);
            o.Rect(g.Eau.X + i * 4, g.Eau.Y + 4, 4, 4, i % 7 == 0 ? Eau2 : Eau1);
            o.Rect(g.Eau.X + i * 4, g.Eau.Y + 8, 4, 4, Eau3);
        }
        DessinerPilou(o, aGauche, px);
        o.Grille(canne, g.CanneX, g.CanneY, Placement.TailleCanne, g.CanneMiroir);
        var b = Placement.Lancer(g, lance);
        if (lance >= 1 && mord) b = b with { Y = b.Y + 8 };
        var bouchon = G("bouchon");
        o.Grille(bouchon, b.X - (bouchon.GetLength(1) / 2.0 + 1) * 1.6, b.Y - 1.6, 1.6);
        o.Ligne(g.Bout, b, Fil);
        if (mord) o.Texte("!", g.Attache.X - 2, g.Attache.Y - 32, Orange, 4);
        // Repères : main (vert), bout de la canne (rouge).
        o.Rect(g.Main.X - 1, g.Main.Y - 1, 2, 2, Vert);
        o.Rect(g.Bout.X - 1, g.Bout.Y - 1, 2, 2, Rouge);
    }

    private static void Cuisine(Toile o, bool aGauche)
    {
        var (px, _) = Pilou(Placement.Sens(aGauche), objets: new[] { "acc-toque" });
        var marmite = G("marmite");
        var feu = G("feu");
        double tm = 2.2, tf = 1.6;
        var (hm, bm) = Placement.Rangs(Motif(marmite));
        var (hf, bf) = Placement.Rangs(Motif(feu));
        var (pm, pf) = Placement.Cuisine(aGauche, (marmite.GetLength(1) + 2) * tm, (bm + 2) * tm, (feu.GetLength(1) + 2) * tf, (hf + 1) * tf, (bf + 2) * tf);
        Fenetre(o, aGauche);
        DessinerPilou(o, aGauche, px);
        o.Grille(feu, pf.X, pf.Y, tf);
        o.Grille(marmite, pm.X, pm.Y, tm);
    }

    // Éléments « à côté » : main du tape m'en cinq, coffre du journal, badge boutique, en-cas, icône de soin.
    private static void ACote(Toile o, bool aGauche)
    {
        int sens = Placement.Sens(aGauche);
        var (px, _) = Pilou(sens, expr: "repos");
        Fenetre(o, aGauche);
        DessinerPilou(o, aGauche, px);
        var main = G("main");
        o.Grille(main, Placement.ACote(aGauche, sens, 34, (main.GetLength(1) + 2) * 2.2), Placement.TeteY - 6, 2.2, sens > 0);
        var coffre = G("coffre-expedition");
        o.Grille(coffre, Placement.ACote(aGauche, sens, 34, (coffre.GetLength(1) + 2) * 2), Placement.TeteY + 22, 2);
        var badge = G("badge-boutique");
        o.Grille(badge, Placement.ACote(aGauche, sens, 34, (badge.GetLength(1) + 2) * 2), Placement.TeteY - 60, 2);
        var encas = G("encas-pomme");
        o.Grille(encas, Placement.ACote(aGauche, sens, 20, (encas.GetLength(1) + 2) * Placement.PX), Placement.TeteY + 34, Placement.PX);
        var soin = G("soin-faim");
        o.Grille(soin, Placement.ACote(aGauche, -sens, 24, (soin.GetLength(1) + 2) * Placement.PX), Placement.TeteY + 4, Placement.PX);
    }

    // Deux écrans : un à gauche du principal (X négatif), Pilou collé à leur bord commun ou à un bord extérieur.
    private static void Ecrans(string chemin, double k)
    {
        var gaucheZ = (L: -1280.0, R: 0.0, B: 760.0);
        var principalZ = (L: 0.0, R: 1600.0, B: 860.0);
        double ox = 1300, z = 0.5;
        var o = new Toile(3000, 900, z, 0xff1c2128) { Ox = ox };
        o.Rect(gaucheZ.L, 0, gaucheZ.R - gaucheZ.L, gaucheZ.B, 0xff3b4654);
        o.Rect(principalZ.L, 0, principalZ.R - principalZ.L, principalZ.B, 0xff444c56);
        void Poser((double L, double R, double B) zone, double x)
        {
            var (min, max) = Placement.BornesPieds(zone.L, zone.R, k);
            x = Math.Clamp(x, min, max);
            bool aGauche = Placement.AGauche(x, zone.L, zone.R);
            double gauche = Placement.GaucheFenetre(x, aGauche, k), haut = Placement.HautFenetre(zone.B, k);
            var vis = Placement.Visible(gauche, k, zone.L, zone.R);
            // Cadre de la fenêtre (gris) et partie visible (découpée à l'écran courant).
            o.Cadre(gauche, haut, Placement.LargeurBase * k, (Placement.HauteurBulle + Placement.HauteurScene) * k, 0x60ffffff);
            var fen = new Toile(Placement.LargeurBase, Placement.HauteurBulle + Placement.HauteurScene, 2, 0);
            Peche(fen, aGauche, 1, true);
            double bulle = Placement.LargeurBulle(aGauche, vis);
            fen.Cadre(aGauche ? 0 : Placement.LargeurBase - bulle, 60, bulle, 70, 0xff6cb6ff);
            for (int py = 0; py < fen.H; py++)
            for (int px = 0; px < fen.W; px++)
            {
                double u = px / fen.Z;
                if (u < vis.X0 || u >= vis.X1 || fen.Px[py * fen.W + px] == 0) continue;
                double sx = gauche + u * k, sy = haut + py / fen.Z * k;
                int qx = (int)Math.Round((sx + ox) * z), qy = (int)Math.Round(sy * z);
                if (qx >= 0 && qy >= 0 && qx < o.W && qy < o.H) o.Px[qy * o.W + qx] = ToileDefense.Melanger(o.Px[qy * o.W + qx], fen.Px[py * fen.W + px]);
            }
        }
        Poser(gaucheZ, gaucheZ.L);     // bord gauche de l'écran de gauche
        Poser(gaucheZ, gaucheZ.R);     // bord droit de l'écran de gauche (frontière)
        Poser(principalZ, principalZ.L); // bord gauche du principal (frontière)
        Poser(principalZ, principalZ.R); // bord droit du principal
        Png.Ecrire(chemin, o.Px, o.W, o.H);
    }

    [Fact]
    public void Planches()
    {
        if (string.IsNullOrEmpty(Dossier)) return;
        Directory.CreateDirectory(Dossier);
        const double z = 3;
        double l = Placement.LargeurBase, h = Placement.HauteurBulle + Placement.HauteurScene;
        foreach (var (nom, aGauche) in new[] { ("gauche", true), ("droite", false) })
        {
            // « gauche » : Pilou près du bord gauche de l'écran (la place est à sa droite).
            var o = new Toile(l * 3, h, z, Fond);
            Peche(o, aGauche, 0.5, false);
            o.Ox = l;
            Peche(o, aGauche, 1, false);
            o.Ox = 2 * l;
            Peche(o, aGauche, 1, true);
            Png.Ecrire(Path.Combine(Dossier, $"peche-{nom}.png"), o.Px, o.W, o.H);

            var s = new Toile(l * 2, h, z, Fond);
            Peche(s, aGauche, 1, false, stade: 1);
            s.Ox = l;
            Peche(s, aGauche, 1, false, stade: 4);
            Png.Ecrire(Path.Combine(Dossier, $"peche-{nom}-stades-1-4.png"), s.Px, s.W, s.H);

            var c = new Toile(l * 2, h, z, Fond);
            Cuisine(c, aGauche);
            c.Ox = l;
            ACote(c, aGauche);
            Png.Ecrire(Path.Combine(Dossier, $"cuisine-et-voisins-{nom}.png"), c.Px, c.W, c.H);
        }
        // Objets tenus en main : la grille 48 × 56 (cadre) et ce qui en dépasse, dessiné dans la marge de la scène.
        var ids = new[] { "parapluie", "telescope", "livre", "ombrelle", "baluchon", "cape", "guitare", "bouclier-couvercle" };
        var obj = new Toile(ids.Length * 70, 80, 4, Fond);
        for (int i = 0; i < ids.Length; i++)
        {
            var debord = new List<(int X, int Y, uint C)>();
            var px = RenduPilou.Rendre(new Allure { Expr = "concentre", Regard = 1, Objets = new[] { ids[i] } }, B.Value, out _, debord);
            obj.Cadre(i * 70 + 11, 12, RenduPilou.W, RenduPilou.H, Repere);
            obj.Image(px, RenduPilou.W, RenduPilou.H, i * 70 + 11, 12, 1);
            // Comme la scène du PC : ce qui dépasse de la grille est dessiné dans la marge (sauf sous le sol).
            foreach (var (x, y, c) in debord)
                if (y < RenduPilou.H) obj.Rect(i * 70 + 11 + x, 12 + y, 1, 1, c);
        }
        Png.Ecrire(Path.Combine(Dossier, "objets-tenus.png"), obj.Px, obj.W, obj.H);
        foreach (var k in new[] { 1.0, 1.5, 2.6 })
            Ecrans(Path.Combine(Dossier, $"ecrans-k{k.ToString(System.Globalization.CultureInfo.InvariantCulture)}.png"), k);
    }
}
