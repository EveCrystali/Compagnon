using PilouBureau;
using Xunit;

public class ProgressionTests
{
    [Fact]
    public void Stades_par_niveau()
    {
        Assert.Equal(1, Acces.Stade(1));
        Assert.Equal(1, Acces.Stade(9));
        Assert.Equal(2, Acces.Stade(10));
        Assert.Equal(3, Acces.Stade(25));
        Assert.Equal(4, Acces.Stade(40));
        Assert.Equal(4, Acces.Stade(99));
        Assert.Equal("Pilou Nimbus", Acces.NomStade(3));
    }

    [Fact]
    public void Jeux_ouverts_par_niveau()
    {
        Assert.True(Acces.JeuOuvert("etoile", 1));
        Assert.False(Acces.JeuOuvert("peche", 1));
        Assert.True(Acces.JeuOuvert("peche", 2));
        Assert.False(Acces.JeuOuvert("chasse", 4));
        Assert.True(Acces.JeuOuvert("inconnu", 1));
    }

    [Fact]
    public void Pieces_par_niveau()
    {
        Assert.Equal(30, Acces.PoNiveau(2));
        Assert.Equal(30 + 35 + 40, Acces.PoMontee(1, 4));
        Assert.Equal(0, Acces.PoMontee(5, 5));
    }

    [Fact]
    public void Migration_verse_ce_qui_etait_acquis_et_seulement_une_fois()
    {
        var p = new Profil();
        var r = new Reglages { Couleur = Couleur.Ambre, Trainee = true };
        Migration.Appliquer(p, 5 * 11 * 11, r); // niveau 12 sur l'ancienne courbe
        // niveau 12 : feuille(1) noeud(2) casque(3) bonnet(4) lunettes(5) couronne(7), nuit(6) ambre(8) argent(10) aurore(12), traînée(9)
        foreach (var id in new[] { "feuille", "noeud", "casque", "bonnet", "lunettes", "couronne", "couleur-nuit", "couleur-ambre",
                     "couleur-argent", "couleur-aurore", Boutique.TraineeEtoiles })
            Assert.Contains(id, p.Bourse.Inventaire);
        Assert.DoesNotContain("chapeaupeche", p.Bourse.Inventaire);
        Assert.DoesNotContain(Boutique.CanneDoree, p.Bourse.Inventaire);
        Assert.Equal("couleur-ambre", p.Bourse.Equipe[Boutique.Couleur].Id);
        Assert.Equal(Boutique.TraineeEtoiles, p.Bourse.Equipe[Boutique.Effet].Id);
        Assert.Equal(2, p.Evolution.StadeAtteint);
        Assert.Equal(12, p.Evolution.NiveauPaye);
        Assert.Equal(12, p.Evolution.NiveauAcquis);
        Assert.Equal(0, p.Bourse.PoGagnes); // pas de pièces rétroactives
        int avant = p.Bourse.Inventaire.Count;
        Migration.Appliquer(p, 100_000, r);
        Assert.Equal(avant, p.Bourse.Inventaire.Count);
        Assert.False(p.Evolution.Due(12));
        Assert.True(p.Evolution.Due(25));
    }

    [Fact]
    public void Forme_affichee_parmi_les_stades_atteints()
    {
        var e = new Evolution { StadeAtteint = 3 };
        Assert.Equal(3, e.Affiche);
        e.StadeAffiche = 1;
        Assert.Equal(1, e.Affiche);
        e.StadeAffiche = 4; // pas encore atteint : on montre le plus haut atteint
        Assert.Equal(3, e.Affiche);
    }

    [Fact]
    public void Pierre_de_calme_s_achete_plusieurs_fois_et_les_bonus_sont_des_articles()
    {
        var b = new Bourse();
        var jour = new DateOnly(2026, 11, 25);
        Assert.Null(Boutique.Acheter(b, Boutique.PierreCalme, 10, 1000, jour));
        Assert.Null(Boutique.Acheter(b, Boutique.PierreCalme, 10, 1000, jour));
        Assert.Equal(2, b.Consommables[Boutique.PierreCalme]);
        Assert.DoesNotContain(Boutique.PierreCalme, b.Inventaire);
        Assert.Contains("niveau 30", Boutique.Acheter(b, Boutique.CanneDoree, 29, 10_000, jour));
        Assert.Null(Boutique.Acheter(b, Boutique.CanneDoree, 30, 10_000, jour));
        Assert.Contains(Boutique.CanneDoree, b.Inventaire);
    }

    [Fact]
    public void Canne_et_marmite_ne_jouent_que_possedees()
    {
        Assert.True(Butin.Poids(Rarete.Legendaire, 30, canneDoree: true) > Butin.Poids(Rarete.Legendaire, 30));
        Assert.True(Butin.ChanceRate(35, false, marmiteCuivre: true) < Butin.ChanceRate(35, false));
    }
}
