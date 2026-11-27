using PilouBureau;
using Xunit;

// Géométrie autour de Pilou et bornage à l'écran courant (Placement.cs) : les deux côtés, plusieurs tailles,
// un écran à gauche du principal (X négatif).
public class PlacementTests
{
    private static readonly Lazy<Banque> B = new(() => Banque.DepuisDossier(Path.Combine(DefenseTests.Racine(), "assets")));

    public static readonly double[] Tailles = { 1, 1.5, 2, 2.6 };

    // Écrans (unités WPF) : principal, un écran à gauche du principal (X négatif), un écran étroit.
    public static readonly (double G, double D, double H, double B)[] Zones =
    {
        (0, 1920, 0, 1040), (-1280, 0, 0, 984), (-2560, -1280, 120, 1000), (1920, 3200, -200, 800), (-1024, 0, 0, 728),
    };

    private static int[,] Motif(string id)
    {
        var g = Banque.Grille(B.Value[id]!, 0);
        var m = new int[g.GetLength(0), g.GetLength(1)];
        for (int r = 0; r < g.GetLength(0); r++)
        for (int c = 0; c < g.GetLength(1); c++)
            m[r, c] = g[r, c] != 0 ? 1 : 0;
        return m;
    }

    private static Geometrie Geo(int stade, string expr = "concentre")
    {
        RenduPilou.Rendre(new Allure { Stade = stade, Expr = expr }, B.Value, out var g);
        return g;
    }

    private static GeoPeche Peche(bool aGauche, int stade = 2)
    {
        var m = Motif("canne");
        return Placement.Peche(aGauche, Geo(stade), m.GetLength(1), Placement.ReperesCanne(m));
    }

    [Fact]
    public void ReperesDeLaCanne()
    {
        var (prise, bout) = Placement.ReperesCanne(Motif("canne"));
        Assert.Equal(new Pt(29, 1), bout);
        // La prise est en bas à gauche, sur le manche.
        Assert.True(prise.X < 8 && prise.Y > 22, $"prise {prise}");
        Assert.NotEqual(0, Motif("canne")[(int)prise.Y, (int)prise.X]);
    }

    [Theory]
    [InlineData(true, 1)]
    [InlineData(true, 2)]
    [InlineData(true, 3)]
    [InlineData(true, 4)]
    [InlineData(false, 1)]
    [InlineData(false, 2)]
    [InlineData(false, 3)]
    [InlineData(false, 4)]
    public void LaCanneEstDansLaMainEtLeFilPartDuBout(bool aGauche, int stade)
    {
        var m = Motif("canne");
        var reperes = Placement.ReperesCanne(m);
        var g = Peche(aGauche, stade);
        int sens = Placement.Sens(aGauche);
        double t = Placement.TailleCanne;
        // La cellule de la prise (dans le dessin, retourné ou non) tombe pile sur la main de Pilou.
        double colPrise = g.CanneMiroir ? m.GetLength(1) - 1 - reperes.Prise.X : reperes.Prise.X;
        Assert.Equal(g.Main.X, g.CanneX + (colPrise + 1.5) * t, 6);
        Assert.Equal(g.Main.Y, g.CanneY + (reperes.Prise.Y + 1.5) * t, 6);
        Assert.Equal(sens < 0, g.CanneMiroir);
        // La main est celle du côté de l'eau, sur le flanc de Pilou.
        Assert.True(sens * (g.Main.X - Placement.TeteX(aGauche)) > 10, $"main {g.Main}");
        // Le bout est plus haut que la main et du côté de l'eau ; le bouchon est sur l'eau, plus loin encore.
        Assert.True(g.Bout.Y < g.Main.Y - 30);
        Assert.True(sens * (g.Bout.X - g.Main.X) > 30);
        Assert.True(sens * (g.Attache.X - g.Bout.X) > 0);
        Assert.InRange(g.Attache.X, g.Eau.X + 8, g.Eau.X + g.Eau.Largeur - 8);
        Assert.True(g.Attache.Y < g.Eau.Y);
        // L'eau est du côté de la place, toute dans la fenêtre, au sol.
        Assert.True(sens * (g.Eau.X + g.Eau.Largeur / 2 - Placement.TeteX(aGauche)) > 0);
        Assert.InRange(g.Eau.X, 0, Placement.LargeurBase - g.Eau.Largeur);
        Assert.Equal(Placement.SolY, g.Eau.Y + g.Eau.Hauteur, 6);
        // La canne entière reste dans la fenêtre.
        Assert.InRange(g.CanneX, 0, Placement.LargeurBase - (m.GetLength(1) + 2) * t);
        Assert.True(g.CanneY > 0);
        // Le lancer part du bout de la canne et finit sur le bouchon posé.
        Assert.Equal(g.Bout, Placement.Lancer(g, 0));
        Assert.Equal(g.Attache, Placement.Lancer(g, 1));
    }

    [Theory]
    [InlineData(1)]
    [InlineData(2)]
    [InlineData(3)]
    [InlineData(4)]
    public void LaPecheADroiteEstLeMiroirDeLaPecheAGauche(int stade)
    {
        var g = Peche(true, stade);
        var d = Peche(false, stade);
        double L = Placement.LargeurBase;
        Assert.Equal(L - (g.Eau.X + g.Eau.Largeur), d.Eau.X, 6);
        Assert.Equal(L - g.Attache.X, d.Attache.X, 6);
        // La main (pixel entier de la grille) peut tomber à un pixel près.
        Assert.InRange(Math.Abs(L - g.Main.X - d.Main.X), 0, Placement.PX + 1e-6);
        Assert.InRange(Math.Abs(L - g.Bout.X - d.Bout.X), 0, Placement.PX + 1e-6);
        Assert.Equal(g.Bout.Y, d.Bout.Y, 6);
    }

    [Fact]
    public void LaCuisineEstPoseeAuSolDesDeuxCotes()
    {
        foreach (var aGauche in new[] { true, false })
        {
            // Dimensions des dessins de la banque (marmite 28 × 22 à 2,2 ; feu 26 × 10 à 1,6).
            var (marmite, feu) = Placement.Cuisine(aGauche, 30 * 2.2, 22 * 2.2, 28 * 1.6, 4 * 1.6, 11 * 1.6);
            int sens = Placement.Sens(aGauche);
            Assert.Equal(Placement.SolY, feu.Y + 11 * 1.6, 6); // flammes au sol
            Assert.True(marmite.Y + 22 * 2.2 < Placement.SolY); // la marmite au-dessus du sol
            Assert.True(marmite.Y + 22 * 2.2 > feu.Y + 4 * 1.6); // et posée sur les flammes
            Assert.Equal(marmite.X + 15 * 2.2, feu.X + 14 * 1.6, 6); // feu centré dessous
            Assert.True(sens * (marmite.X + 15 * 2.2 - Placement.TeteX(aGauche)) > 60);
            Assert.InRange(marmite.X, 0, Placement.LargeurBase - 30 * 2.2);
        }
        var g = Placement.Cuisine(true, 66, 48, 44, 6, 18).Marmite;
        var d = Placement.Cuisine(false, 66, 48, 44, 6, 18).Marmite;
        Assert.Equal(Placement.LargeurBase - (g.X + 66), d.X, 6);
    }

    [Theory]
    [InlineData(34, 44)]
    [InlineData(20, 30)]
    [InlineData(24, 28)]
    public void ACoteEstUnMiroirExact(double ecart, double largeur)
    {
        foreach (var sens in new[] { 1, -1 })
        {
            double g = Placement.ACote(true, sens, ecart, largeur);
            double d = Placement.ACote(false, -sens, ecart, largeur);
            Assert.Equal(Placement.LargeurBase - (g + largeur), d, 6);
            // Du bon côté de l'axe, à la bonne distance.
            double axe = Placement.TeteX(true);
            Assert.Equal(ecart, sens > 0 ? g - axe : axe - (g + largeur), 6);
        }
    }

    // Pilou à gauche, au centre, à droite de chaque écran, à chaque taille : la scène reste sur son écran,
    // la fenêtre est découpée à cet écran, la bulle aussi, et l'eau tient dans la partie visible.
    [Fact]
    public void BalayageDesEcransEtDesTailles()
    {
        foreach (var z in Zones)
        foreach (var k in Tailles)
        foreach (var f in new[] { 0.0, 0.25, 0.5, 0.75, 1.0 })
        {
            var (min, max) = Placement.BornesPieds(z.G, z.D, k);
            double x = Math.Clamp(z.G + (z.D - z.G) * f, min, max);
            bool aGauche = Placement.AGauche(x, z.G, z.D);
            double gauche = Placement.GaucheFenetre(x, aGauche, k);
            string cas = $"zone {z} k {k} f {f}";
            Assert.Equal(x, gauche + Placement.TeteX(aGauche) * k, 0.51);
            // La scène de Pilou est sur son écran.
            double sceneG = gauche + Placement.SceneX(aGauche) * k, sceneD = sceneG + Placement.LargeurScene * k;
            Assert.True(sceneG >= z.G - 0.51 && sceneD <= z.D + 0.51, cas);
            var vis = Placement.Visible(gauche, k, z.G, z.D);
            Assert.True(vis.X0 <= Placement.SceneX(aGauche) + 0.51 / k && vis.X1 >= Placement.SceneX(aGauche) + Placement.LargeurScene - 0.51 / k, cas);
            // Ce qui est visible est sur l'écran.
            Assert.True(gauche + vis.X0 * k >= z.G - 1e-6 && gauche + vis.X1 * k <= z.D + 1e-6, cas);
            // La bulle, alignée du côté de Pilou, ne dépasse pas la partie visible.
            double bulle = Placement.LargeurBulle(aGauche, vis);
            double bulleG = aGauche ? 0 : Placement.LargeurBase - bulle;
            Assert.True(bulleG >= vis.X0 - 1e-6 && bulleG + bulle <= vis.X1 + 1e-6, cas);
            // Pilou va du côté de la place : l'eau de la pêche tient dans la partie visible.
            var p = Placement.Peche(aGauche, Geo(2), 30, Placement.ReperesCanne(Motif("canne")));
            Assert.True(p.Eau.X >= vis.X0 && p.Eau.X + p.Eau.Largeur <= vis.X1, cas);
        }
    }

    [Fact]
    public void LaFenetreEstEntiereQuandLEcranEstAssezLarge()
    {
        foreach (var k in Tailles)
        foreach (var z in Zones.Where(z => z.D - z.G >= 2 * (Placement.LargeurBase - Placement.LargeurScene / 2) * k))
        foreach (var f in new[] { 0.0, 0.5, 1.0 })
        {
            var (min, max) = Placement.BornesPieds(z.G, z.D, k);
            double x = Math.Clamp(z.G + (z.D - z.G) * f, min, max);
            bool aGauche = Placement.AGauche(x, z.G, z.D);
            Assert.Equal((0.0, Placement.LargeurBase), Placement.Visible(Placement.GaucheFenetre(x, aGauche, k), k, z.G, z.D));
        }
    }

    [Fact]
    public void LaSortieParLeBordQuitteLEcranCourant()
    {
        foreach (var z in Zones)
        foreach (var k in Tailles)
        {
            Assert.Equal(-1, Placement.SensSortie(z.G + 10, z.G, z.D));
            Assert.Equal(1, Placement.SensSortie(z.D - 10, z.G, z.D));
            foreach (var sens in new[] { -1, 1 })
            {
                double x = Placement.Sortie(sens, z.G, z.D, k);
                bool aGauche = Placement.AGauche(x, z.G, z.D);
                double gauche = Placement.GaucheFenetre(x, aGauche, k);
                double sceneG = gauche + Placement.SceneX(aGauche) * k, sceneD = sceneG + Placement.LargeurScene * k;
                // Pilou est entièrement hors de son écran : sur l'écran voisin, la fenêtre découpée ne montre rien de lui.
                Assert.True(sceneD <= z.G || sceneG >= z.D, $"zone {z} k {k} sens {sens}");
                var vis = Placement.Visible(gauche, k, z.G, z.D);
                double sx0 = Placement.SceneX(aGauche), sx1 = sx0 + Placement.LargeurScene;
                Assert.True(vis.X1 <= sx0 + 1e-6 || vis.X0 >= sx1 - 1e-6);
            }
        }
    }

    [Fact]
    public void LaPetiteFenetreResteSurLEcranDePilou()
    {
        foreach (var z in Zones)
        foreach (var k in Tailles)
        foreach (var aGauche in new[] { true, false })
        {
            var (min, max) = Placement.BornesPieds(z.G, z.D, k);
            double x = aGauche ? min : max;
            double gauche = Placement.GaucheFenetre(x, aGauche, k), haut = Placement.HautFenetre(z.B, k);
            var (fx, fy) = Placement.PresDe(gauche, haut, k, aGauche, 330, 220, z.G, z.H, z.D, z.B);
            Assert.InRange(fx, z.G, z.D - 330);
            Assert.InRange(fy, z.H, z.B - 220);
        }
    }

    [Fact]
    public void LaBandeDeDefenseEstCentreeSurLEcranDePilou()
    {
        foreach (var z in Zones)
        foreach (var s in new[] { 1.0, 1.25, 1.5, 2.0 })
        foreach (var part in new[] { 1.0, 0.66, 0.5 })
        {
            var b = Placement.Bande(z.G, z.H, z.D - z.G, z.B - z.H, s, part, 0.42);
            Assert.InRange(b.GauchePhys, z.G * s - 1, z.D * s - b.W * b.K + 1);
            Assert.Equal(Math.Round(z.B * s), b.HautPhys + b.H * b.K, 6);
            Assert.InRange(b.GauchePhys + b.W * b.K / 2.0, (z.G + z.D) / 2 * s - 1, (z.G + z.D) / 2 * s + 1);
        }
    }

    [Fact]
    public void BornerGardeLeSegmentDansLIntervalle()
    {
        Assert.Equal(10, Placement.Borner(-50, 40, 10, 300));
        Assert.Equal(260, Placement.Borner(290, 40, 10, 300));
        Assert.Equal(100, Placement.Borner(100, 40, 10, 300));
        Assert.Equal(10, Placement.Borner(100, 400, 10, 300)); // trop large : collé à gauche
    }

    [Fact]
    public void EssaisAuBord()
    {
        Assert.Equal(("peche", true), Tournage.EssaiAuBord("peche:gauche"));
        Assert.Equal(("cuisine", false), Tournage.EssaiAuBord("cuisine:droite"));
        Assert.Null(Tournage.EssaiAuBord("peche:haut"));
        Assert.Null(Tournage.EssaiAuBord("meteo:pluie"));
        Assert.True(Tournage.EssaiConnu("peche:droite"));
        Assert.True(Tournage.EssaiConnu("tape:gauche"));
    }

    [Fact]
    public void LaMainDeRenduPilouEstSymetrique()
    {
        foreach (var st in new[] { 1, 2, 3, 4 })
        {
            var g = Geo(st, "repos");
            var (dx, dy) = RenduPilou.AncreMain(g, 1);
            var (gx, gy) = RenduPilou.AncreMain(g, -1);
            Assert.Equal(dy, gy);
            Assert.InRange(Math.Abs((dx + 0.5) - RenduPilou.C - (RenduPilou.C - (gx + 0.5))), 0, 1);
        }
    }

    // Ce qui dépasse de la grille 48 × 56 (objets tenus au bout de la main) tient dans la marge de la scène,
    // donc dans la fenêtre et sur l'écran de Pilou, à chaque stade.
    [Fact]
    public void LesObjetsTenusTiennentDansLaScene()
    {
        var ids = Directory.EnumerateFiles(Path.Combine(DefenseTests.Racine(), "assets", "sprites"), "*.txt")
            .Select(f => Path.GetFileNameWithoutExtension(f)).Where(id => B.Value[id] is { Ancre: "main" or "main-g" or "cote" }).ToList();
        Assert.Contains("parapluie", ids);
        foreach (var st in new[] { 1, 2, 3, 4 })
        foreach (var id in ids)
        {
            var debord = new List<(int X, int Y, uint C)>();
            RenduPilou.Rendre(new Allure { Stade = st, Objets = new[] { id } }, B.Value, out _, debord);
            // Chaque pixel débordant (unités de la scène) reste dans la scène, à un quart d'unité près.
            Assert.All(debord, d => Assert.InRange(Placement.MargeX + d.X * Placement.PX, -0.25, Placement.LargeurScene - Placement.PX + 0.25));
            if (id == "parapluie" && st == 2) Assert.NotEmpty(debord); // il dépassait : coupé net au bord de la grille
        }
    }
}
