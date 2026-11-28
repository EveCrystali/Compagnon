using PilouBureau;
using Xunit;
using B = PilouBureau.Flottants.Boite;

public class FlottantsTests
{
    private static readonly B Bulle = Flottants.DeBulle(20, 100, 300, 140);

    private static double? Seul(double x, double y, double l, double h, params B[] o) => Flottants.Placer(x, y, l, h, o);

    [Fact]
    public void Sans_obstacle_le_gain_ne_bouge_pas() => Assert.Equal(120, Seul(50, 120, 30, 12));

    [Fact]
    public void Loin_de_la_bulle_le_gain_ne_bouge_pas()
    {
        Assert.Equal(160, Seul(50, 160, 30, 12, Bulle));   // dessous
        Assert.Equal(40, Seul(50, 40, 30, 12, Bulle));     // dessus
        Assert.Equal(120, Seul(310, 120, 30, 12, Bulle));  // à côté
        Assert.Equal(-20, Seul(50, -20, 30, 12, Bulle));   // sorti par le haut en montant : il s'efface comme avant
    }

    [Fact]
    public void Un_gain_qui_touche_la_bulle_passe_juste_au_dessus() =>
        Assert.Equal(100 - Flottants.MargeBulle - 14, Seul(250, 120, 40, 14, Bulle));

    [Fact]
    public void Un_gain_qui_croiserait_la_bulle_en_montant_part_tout_de_suite_au_dessus()
    {
        Assert.Equal(100 - Flottants.MargeBulle - 14, Flottants.Placer(250, 150, 40, 14, new[] { Bulle }, reste: 38));
        Assert.Equal(200, Flottants.Placer(250, 200, 40, 14, new[] { Bulle }, reste: 38)); // ne l'atteindra pas
    }

    [Fact]
    public void La_piece_et_son_texte_restent_cote_a_cote()
    {
        // FlotterPo : la pièce (14 de large) finit 2 avant le texte « +30 po », sur la même ligne.
        var piece = new B(84, 120, 98, 134);
        Assert.Equal(120, Seul(100, 120, 40, 14, Bulle with { Haut = 500, Bas = 600 }, piece));
    }

    [Fact]
    public void Un_gain_repousse_s_empile_au_dessus_des_autres()
    {
        var succes = new B(40, 60, 140, 87);
        var y = Seul(60, 120, 40, 14, Bulle, succes);
        Assert.Equal(60 - Flottants.MargeGain - 14, y);
    }

    [Fact]
    public void Sans_place_au_dessus_le_gain_attend_cache() =>
        Assert.Null(Seul(50, 120, 30, 12, Flottants.DeBulle(20, 8, 300, 140)));

    // La scène d'une quête réussie, image par image : « SUCCES ! », la pièce, « +30 po », « +30 xp » montent pendant
    // qu'une bulle s'ouvre. Jamais un gain sur la bulle, jamais deux gains l'un sur l'autre.
    [Theory]
    [InlineData(0)]
    [InlineData(300)]
    [InlineData(900)]
    public void Pendant_toute_leur_montee_les_gains_ne_recouvrent_ni_la_bulle_ni_un_autre_gain(double ouverture)
    {
        // (x, y de départ, largeur, hauteur) comme dans Jeux.cs / FenetreQuetes.cs, tête en (150, 190).
        var gains = new (double X, double Y, double L, double H)[] { (104, 120, 160, 27), (148, 168, 14, 14), (164, 168, 46, 14), (132, 160, 46, 14) };
        var decale = new double[gains.Length];
        var avant = new double?[gains.Length];
        var bulle = Flottants.DeBulle(10, 125, 330, 172);
        for (double t = 0; t < Flottants.Vie; t += 16)
        {
            var obstacles = new List<B>();
            if (t >= ouverture) obstacles.Add(bulle);
            var places = new List<B>();
            for (int i = 0; i < gains.Length; i++)
            {
                var g = gains[i];
                double k = t / Flottants.Vie;
                double y = g.Y + decale[i] - k * Flottants.Montee;
                var p = Flottants.Placer(g.X, y, g.L, g.H, obstacles, (1 - k) * Flottants.Montee);
                Assert.NotNull(p);
                decale[i] += p!.Value - y;
                // Après l'image où la bulle s'ouvre, plus aucun saut : chaque gain monte d'un pas régulier.
                if (t - 16 >= ouverture && avant[i] is { } a) Assert.InRange(a - p.Value, 0, 1);
                avant[i] = p.Value;
                var boite = new B(g.X, p.Value, g.X + g.L, p.Value + g.H);
                if (t >= ouverture) Assert.False(Chevauche(boite, bulle), $"t={t} : gain {i} sur la bulle");
                foreach (var autre in places) Assert.False(Chevauche(boite, autre), $"t={t} : gain {i} sur un autre");
                places.Add(boite);
                obstacles.Add(boite);
            }
        }
    }

    private static bool Chevauche(B a, B b) => a.Gauche < b.Droite && a.Droite > b.Gauche && a.Haut < b.Bas && a.Bas > b.Haut;
}
