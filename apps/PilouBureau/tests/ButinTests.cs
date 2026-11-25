using PilouBureau;
using Xunit;

public class ButinTests
{
    private static Dictionary<Rarete, int> Pecher(bool seul, int niveau, int fois, out int rien)
    {
        var hasard = new Random(1234);
        var compte = Enum.GetValues<Rarete>().ToDictionary(r => r, _ => 0);
        rien = 0;
        for (int i = 0; i < fois; i++)
        {
            var p = Butin.Tirer(hasard, niveau, seul);
            if (p is null) rien++;
            else compte[p.Rarete]++;
        }
        return compte;
    }

    [Fact]
    public void A_la_main_on_prend_toujours_seul_bien_moins_souvent()
    {
        Pecher(false, 10, 5000, out var rienMain);
        Pecher(true, 10, 5000, out var rienSeul);
        Assert.Equal(0, rienMain);
        double reussite = 1 - rienSeul / 5000.0;
        Assert.InRange(reussite, Butin.ChanceSeul - 0.03, Butin.ChanceSeul + 0.03);
    }

    [Fact]
    public void Seul_jamais_mieux_que_rare_et_niveau_minimum_respecte()
    {
        var seul = Pecher(true, 50, 20000, out _);
        Assert.Equal(0, seul[Rarete.Epique] + seul[Rarete.Legendaire]);
        var main = Pecher(false, 50, 20000, out _);
        Assert.True(main[Rarete.Legendaire] > 0);
        Assert.True(main[Rarete.Commun] > main[Rarete.Rare]);

        var hasard = new Random(7);
        for (int i = 0; i < 3000; i++) Assert.True(Butin.Tirer(hasard, 1, false)!.NiveauMin <= 1);
    }

    [Fact]
    public void Le_niveau_rend_les_raretes_plus_frequentes()
    {
        var bas = Pecher(false, 25, 30000, out _);
        var haut = Pecher(false, 45, 30000, out _);
        Assert.True(haut[Rarete.Legendaire] > bas[Rarete.Legendaire]);
    }

    [Fact]
    public void Premiere_prise_compte_double()
    {
        var p = Butin.Trouver("anguille")!;
        Assert.Equal(p.Xp * 2 + 5, Butin.XpPrise(p, nouvelle: true));
        Assert.Equal(p.Xp, Butin.XpPrise(p, nouvelle: false));
    }

    [Fact]
    public void Catalogue_coherent()
    {
        Assert.Equal(Butin.Prises.Count, Butin.Prises.Select(p => p.Id).Distinct().Count());
        Assert.Equal(Butin.Recettes.Count, Butin.Recettes.Select(r => r.Id).Distinct().Count());
        Assert.InRange(Butin.Recettes.Count, 28, 40);
        var saveurs = Butin.Prises.Where(p => p.Comestible).Select(p => p.Saveur).ToHashSet();
        // Chaque recette est faisable avec des prises qui existent.
        foreach (var r in Butin.Recettes) Assert.All(r.Saveurs, s => Assert.Contains(s, saveurs));
        foreach (Rarete r in Enum.GetValues<Rarete>()) Assert.Contains(Butin.Prises, p => p.Rarete == r);
    }

    [Fact]
    public void Cuisine_decouvre_puis_varie()
    {
        var hasard = new Random(42);
        var connues = new HashSet<string>();
        var noms = new HashSet<string>();
        int decouvertes = 0, rates = 0;
        for (int i = 0; i < 60; i++)
        {
            var stock = new Dictionary<string, int> { ["goujon"] = 3, ["algue"] = 2, ["crabe"] = 1, ["spirale"] = 1 };
            var plat = Butin.Cuisiner(hasard, 12, stock, connues)!;
            Assert.NotNull(plat);
            Assert.All(plat.Utilises, id => Assert.True(stock[id] > 0));
            if (plat.Rate)
            {
                rates++;
                Assert.False(plat.Decouverte);
                continue;
            }
            if (plat.Decouverte)
            {
                decouvertes++;
                Assert.True(connues.Add(plat.Id));
            }
            noms.Add(plat.Nom);
        }
        Assert.True(decouvertes >= 20, $"{decouvertes} découvertes");
        Assert.True(noms.Count >= 20);
        Assert.True(rates < 15);
    }

    [Fact]
    public void Rien_a_cuisiner_sans_ingredient_comestible()
    {
        Assert.Null(Butin.Cuisiner(new Random(1), 10, new Dictionary<string, int> { ["botte"] = 3, ["cle"] = 1 }, new HashSet<string>()));
        Assert.Null(Butin.Cuisiner(new Random(1), 10, new Dictionary<string, int>(), new HashSet<string>()));
    }

    [Fact]
    public void Remuer_empeche_de_bruler()
    {
        var hasard = new Random(3);
        for (int i = 0; i < 500; i++)
            Assert.False(Butin.Cuisiner(hasard, 5, new Dictionary<string, int> { ["goujon"] = 1 }, new HashSet<string>(), remue: true)!.Rate);
        Assert.True(Butin.ChanceRate(40, false) < Butin.ChanceRate(5, false));
    }

    [Fact]
    public void Noms_inventes_bien_ecrits()
    {
        var nom = Butin.Inventer(new Random(5), Butin.Trouver("anguille")!);
        Assert.Contains("d'anguille d'encre", nom);
        Assert.DoesNotContain("de a", nom);
    }

    [Theory]
    [InlineData(0)]
    [InlineData(4)]
    [InlineData(5)]
    [InlineData(500)]
    [InlineData(12005)]
    [InlineData(40000)]
    public void La_courbe_de_niveaux_ne_baisse_personne(int xp)
    {
        int ancien = (int)Math.Floor(Math.Sqrt(xp / 5.0)) + 1;
        Assert.True(Profil.Niveau(xp) >= ancien);
    }

    [Fact]
    public void Recompenses_jusqu_au_niveau_50()
    {
        Assert.Equal(50, Recompenses.Toutes.Max(r => r.Niveau));
        Assert.Equal(50, Profil.Niveau(Profil.XpPourNiveau(50)));
        Assert.Equal("Pilou éternel", Recompenses.Titre(50));
        Assert.Equal(9, Recompenses.RequisTrainee);
        foreach (Accessoire a in Enum.GetValues<Accessoire>().Where(a => a is not Accessoire.Saison and not Accessoire.Aucun))
            Assert.Contains(Recompenses.Toutes, r => r.Accessoire == a);
        foreach (Couleur c in Enum.GetValues<Couleur>()) Assert.Contains(Recompenses.Toutes, r => r.Couleur == c);
    }
}
