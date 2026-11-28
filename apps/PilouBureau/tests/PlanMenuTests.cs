using PilouBureau;
using Xunit;

// Le menu clic droit « Sept portes » (docs/AUDIT-MENU.md, « Le menu retenu ») : un premier niveau court et stable,
// une zone « En ce moment » de deux lignes au plus.
public class PlanMenuTests
{
    [Fact]
    public void QuatorzeLignesStables()
    {
        // Bandeau compris, sans titres de section ni zone « En ce moment » (39 lignes avant).
        Assert.Equal(14, PlanMenu.LignesStables);
        var portes = PlanMenu.Blocs.SelectMany(b => b).ToList();
        Assert.Equal(portes.Count, portes.Select(p => p.Titre).Distinct().Count());
        // Chaque porte porte un signe de forme ; deux seulement partagent le leur (◌ : il se cache, se cacher 10 min).
        Assert.All(portes, p => Assert.False(string.IsNullOrWhiteSpace(p.Signe)));
        var partages = portes.GroupBy(p => p.Signe).Where(g => g.Count() > 1).ToList();
        Assert.Single(partages);
        Assert.Equal(new[] { "Il se cache", "Se cacher 10 min" }, partages[0].Select(p => p.Titre));
        // Le quotidien d'abord, la sortie à la fin.
        Assert.Equal(PlanMenu.Soin, PlanMenu.Blocs[0][0]);
        Assert.Equal(PlanMenu.Quitter, PlanMenu.Blocs[^1][^1]);
        // Pas de « & » ni de « _ » : WPF en ferait une lettre soulignée.
        Assert.All(portes, p => Assert.DoesNotContain('_', p.Titre));
        Assert.All(portes, p => Assert.DoesNotContain('&', p.Titre));
    }

    [Fact]
    public void LesPortesQuiOuvrentUneFenetreLeDisent()
    {
        foreach (var p in PlanMenu.Blocs.SelectMany(b => b))
            if (p.Titre.EndsWith('…')) Assert.False(p.Sous, p.Titre);
        Assert.True(PlanMenu.Jouer.Sous);
        Assert.False(PlanMenu.Aventure.Sous); // un clic : la fenêtre Aventure, directement
    }

    [Fact]
    public void RienNeSePasseRienNeSAffiche()
    {
        Assert.Empty(PlanMenu.Moments(false, false, false, false, false));
    }

    [Fact]
    public void DeuxLignesAuPlusDansLOrdreDeLAudit()
    {
        Assert.Equal(new[] { EnCeMoment.Attend, EnCeMoment.Expedition }, PlanMenu.Moments(true, true, true, true, true));
        Assert.Equal(new[] { EnCeMoment.Visite, EnCeMoment.Soin }, PlanMenu.Moments(false, false, true, true, true));
        Assert.Equal(new[] { EnCeMoment.Jeu }, PlanMenu.Moments(false, false, false, false, true));
        Assert.Equal(new[] { EnCeMoment.Attend, EnCeMoment.Jeu }, PlanMenu.Moments(true, false, false, false, true));
        // Toutes les combinaisons : jamais plus de deux lignes, jamais deux fois la même.
        for (int i = 0; i < 32; i++)
        {
            var l = PlanMenu.Moments((i & 1) != 0, (i & 2) != 0, (i & 4) != 0, (i & 8) != 0, (i & 16) != 0);
            Assert.True(l.Count <= PlanMenu.MomentsMax);
            Assert.Equal(l.Count, l.Distinct().Count());
            Assert.Equal(Math.Min(2, System.Numerics.BitOperations.PopCount((uint)i)), l.Count);
        }
    }

    [Fact]
    public void ChaqueMomentASonSigne()
    {
        var signes = Enum.GetValues<EnCeMoment>().Select(PlanMenu.Signe).ToList();
        Assert.Equal(signes.Count, signes.Distinct().Count());
    }

    [Fact]
    public void PasDeuxFoisLEtatDesSoins()
    {
        Assert.Equal("Prendre soin · tout va bien", PlanMenu.TitreSoin("tout va bien", dansLeMoment: false));
        Assert.Equal("Prendre soin", PlanMenu.TitreSoin("il a faim", dansLeMoment: true));
    }

    [Fact]
    public void EtatDesSoinsEnClair()
    {
        Assert.Equal("tout va bien", PlanMenu.EtatSoins(false, false, false, false, null));
        Assert.Equal("il a faim", PlanMenu.EtatSoins(false, false, false, false, Soins.Faim));
        Assert.Equal("il a besoin d'un bain", PlanMenu.EtatSoins(false, false, false, false, Soins.Proprete));
        Assert.Equal("il a besoin d'un câlin", PlanMenu.EtatSoins(false, false, false, false, Soins.Moral));
        // La bouderie passe avant le manque : c'est elle qui réduit les gains.
        Assert.StartsWith("il boude", PlanMenu.EtatSoins(false, true, false, false, Soins.Faim));
        Assert.StartsWith("il se laisse amadouer", PlanMenu.EtatSoins(false, true, true, false, null));
        Assert.StartsWith("il rayonne", PlanMenu.EtatSoins(false, false, false, true, null));
        Assert.Equal("en vacances", PlanMenu.EtatSoins(true, true, false, false, Soins.Faim));
        // Chaque besoin connu a sa phrase.
        Assert.All(Soins.Besoins, b => Assert.NotEqual("il a besoin de toi", PlanMenu.Manque(b)));
    }
}

// « Il se montre ▸ Musique », sous Sons : les trois niveaux de la musique de l'Aventure (#104).
public class PlanMenuMusiqueTests
{
    [Fact]
    public void ChoixDeMusique()
    {
        Assert.Equal(Musique.Niveaux, PlanMenu.ChoixMusique.Select(c => c.Valeur));
        Assert.Equal(new[] { "Aucune", "Discrète", "Normale" }, PlanMenu.ChoixMusique.Select(c => c.Nom));
        Assert.Contains(new Reglages().Musique, PlanMenu.ChoixMusique.Select(c => c.Valeur)); // le défaut est un choix du menu
    }
}
