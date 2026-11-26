using PilouBureau;
using Xunit;

// Boutique garnie : catalogue partagé (assets/catalogue.txt), ensembles, saisons, passages, collection, synchro compacte.
public class BoutiqueGarnieTests
{
    private static readonly Lazy<Banque> B = new(() =>
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d is not null && !File.Exists(Path.Combine(d.FullName, "assets", "index.txt"))) d = d.Parent;
        return Banque.DepuisDossier(Path.Combine(d!.FullName, "assets"));
    });

    private static IEnumerable<Article> Garnis => Boutique.Catalogue.Where(a => a.Numero > 0);

    [Fact]
    public void Catalogue_garni_lu_et_coherent()
    {
        Assert.True(Garnis.Count() >= 110, $"{Garnis.Count()} articles garnis");
        Assert.True(Boutique.Catalogue.Count >= 2 * 111, $"{Boutique.Catalogue.Count} articles en tout");
        Assert.Equal(Boutique.Catalogue.Count, Boutique.Catalogue.Select(a => a.Id).Distinct().Count());
        Assert.Equal(Garnis.Count(), Garnis.Select(a => a.Numero).Distinct().Count());
        // Tous les emplacements gagnent des articles, et le nouvel emplacement « titre » existe.
        foreach (var slot in Boutique.Slots) Assert.Contains(Garnis, a => a.Slot == slot);
        Assert.All(Garnis, a => Assert.Contains(a.Saison, Boutique.Saisons.Append("")));
        // Cinq raretés et le mythique, chacun à son signe.
        Assert.Equal(6, Enum.GetValues<Rarete>().Select(Boutique.SigneRarete).Distinct().Count());
        Assert.Contains(Garnis, a => a.Rarete == Rarete.Mythique);
    }

    [Fact]
    public void Chaque_article_a_son_dessin()
    {
        foreach (var a in Garnis)
        {
            if (a.Slot == Boutique.Couleur) Assert.True(B.Value.Teintes.ContainsKey(a.Id), a.Id);
            else if (a.Slot == Boutique.Bulle) Assert.NotNull(Boutique.Style(a.Id));
            else if (a.Slot == Boutique.Titre) Assert.StartsWith("« ", a.Nom);
            else
            {
                Assert.True(B.Value[a.Id] is not null, a.Id);
                if (a.Slot != Boutique.Fond) Assert.Equal(a.Slot, B.Value[a.Id]!.Slot);
            }
        }
        foreach (var e in Boutique.Ensembles) Assert.True(B.Value[e.Bonus] is not null, e.Bonus);
        foreach (var t in Boutique.Trophees.Where(t => t.Slot == Boutique.Bulle)) Assert.NotNull(Boutique.Style(t.Id));
    }

    [Fact]
    public void Ensembles_de_cinq_ou_six_pieces_a_des_emplacements_differents()
    {
        Assert.True(Boutique.Ensembles.Count >= 8);
        foreach (var e in Boutique.Ensembles)
        {
            Assert.InRange(e.Pieces.Count, 5, 6);
            var slots = e.Pieces.Select(p => Boutique.Trouver(p)!.Slot).ToList();
            Assert.Equal(slots.Count, slots.Distinct().Count());
            Assert.StartsWith("« ", e.Titre);
        }
        Assert.NotEmpty(Boutique.Rangees(Boutique.RayonEnsembles));
        Assert.Equal("Ensembles", Boutique.NomSlot(Boutique.RayonEnsembles));
        Assert.DoesNotContain(Boutique.RayonEnsembles, Boutique.RayonsDuPalier(1));
    }

    [Fact]
    public void Bonus_d_ensemble_seulement_porte_en_entier()
    {
        var e = Boutique.EnsembleDe("explorateur")!;
        var porte = e.Pieces.ToDictionary(p => Boutique.Trouver(p)!.Slot, p => p);
        Assert.Equal(new[] { "bonus-explorateur" }, Boutique.BonusPortes(porte));
        porte.Remove(Boutique.Main);
        Assert.Empty(Boutique.BonusPortes(porte));
        // Un décor d'origine compte dans son ensemble (Rétro-arcade et le décor salle d'arcade).
        Assert.Contains("fond-arcade", Boutique.EnsembleDe("arcade")!.Pieces);
    }

    [Fact]
    public void Collection_paliers_et_titres_gagnes()
    {
        var inv = new List<string>();
        Assert.Equal(0, Boutique.Collection(inv));
        Assert.Equal(10, Boutique.Seuil(Boutique.ProchainPalierCollection(0)!));
        inv.AddRange(Boutique.Catalogue.Where(Boutique.Collectionnable).Take(10).Select(a => a.Id));
        inv.Add(Boutique.PierreCalme); // consommable : ne compte pas
        // Le butin exclusif d'expédition (ne s'achète pas) ne compte pas non plus, ni dans le total.
        foreach (var x in Expeditions.Exclusifs)
        {
            inv.Add(x.Id);
            Assert.DoesNotContain(Boutique.Catalogue, a => a.Id == x.Id);
        }
        Assert.Equal(10, Boutique.Collection(inv));
        Assert.Contains("titre-col-herbe", Boutique.Gagnees(inv));
        Assert.Equal(25, Boutique.Seuil(Boutique.ProchainPalierCollection(10)!));
        // Ensemble complet → son titre ; on peut le porter, pas l'acheter.
        var e = Boutique.EnsembleDe("jardinier")!;
        Assert.DoesNotContain(e.IdTitre, Boutique.Gagnees(inv));
        inv.AddRange(e.Pieces);
        Assert.Contains(e.IdTitre, Boutique.Gagnees(inv));
        var b = new Bourse { Inventaire = inv };
        Assert.True(Boutique.Equiper(b, Boutique.Titre, e.IdTitre, 1));
        Assert.Equal("« Jardinier émérite »", Boutique.NomTitre(e.IdTitre));
        Assert.False(Boutique.Equiper(b, Boutique.Titre, "titre-col-musee", 2));
        Assert.Equal("objet inconnu", Boutique.Acheter(b, e.IdTitre, 50, 10_000, new DateOnly(2026, 11, 26)));
        // Le dernier palier : tout le catalogue.
        Assert.Equal(Boutique.TotalCollection, Boutique.Seuil(Boutique.PaliersCollection.Last()));
        Assert.True(Boutique.TotalCollection >= 220);
    }

    [Fact]
    public void Saisons_et_jours_restants()
    {
        var j = new DateOnly(2026, 11, 26);
        Assert.True(Boutique.EnSaison("automne", j));
        Assert.Equal(5, Boutique.JoursRestants("automne", j));
        Assert.False(Boutique.EnSaison("hiver", j));
        Assert.Equal(new DateOnly(2026, 12, 1), Boutique.Retour("hiver", j));
        Assert.Equal(new DateOnly(2027, 10, 15), Boutique.Retour("frissons", j));
        Assert.True(Boutique.EnSaison("fetes", new DateOnly(2027, 1, 6)));
        Assert.False(Boutique.EnSaison("fetes", new DateOnly(2027, 1, 7)));
        Assert.Equal(28, Boutique.JoursRestants("fetes", new DateOnly(2026, 12, 10)));
        var b = new Bourse();
        Assert.Contains("hors saison", Boutique.Acheter(b, "bonnet-oreillettes", 50, 10_000, j));
        Assert.Null(Boutique.Acheter(b, "bonnet-oreillettes", 50, 10_000, new DateOnly(2026, 12, 2)));
    }

    [Fact]
    public void Passages_trois_jours_par_mois()
    {
        var passagers = Boutique.Catalogue.Where(a => a.Passage).ToList();
        Assert.True(passagers.Count >= 8);
        foreach (var a in passagers)
        {
            var debut = new DateOnly(2027, 3, 1);
            int jours = Enumerable.Range(0, 31).Count(i => Boutique.DePassage(a, debut.AddDays(i)));
            Assert.Equal(Boutique.JoursPassage, jours);
            Assert.NotNull(Boutique.ProchainPassage(a, debut));
        }
        var aujourd = new DateOnly(2026, 11, 26);
        var de = Boutique.Passages(aujourd);
        Assert.Equal(new[] { "nebuleuse", "fond-aurore" }, de.Select(a => a.Id));
        var b = new Bourse();
        Assert.Null(Boutique.Acheter(b, "nebuleuse", 50, 10_000, aujourd));
        var ailleurs = passagers.First(a => !Boutique.DePassage(a, aujourd));
        Assert.Contains("vitrine", Boutique.Acheter(b, ailleurs.Id, 50, 10_000, aujourd));
        Assert.InRange(Boutique.PassageRestant(de[0], aujourd), 1, 3);
    }

    // Même vitrine que le téléphone (BoutiqueTest.java) et qu'un calcul indépendant : graine = date.
    [Theory]
    [InlineData("2026-11-26", "perroquet-caramel,chapeau-paille,ballon-helium,patins", "nebuleuse,fond-aurore")]
    [InlineData("2026-12-24", "fond-montagne,mini-goutte,panier-dos,fond-foret", "ailes-libellule")]
    [InlineData("2027-07-14", "titre-matinal,cuivre,haut-de-forme,bulle-ambre", "")]
    [InlineData("2027-10-31", "herisson,baguette,impermeable,lunettes-3d", "")]
    public void Vitrine_deterministe(string date, string offres, string passages)
    {
        var avant = Boutique.Pluie;
        Boutique.Pluie = () => false;
        try
        {
            var j = DateOnly.Parse(date, System.Globalization.CultureInfo.InvariantCulture);
            Assert.Equal(offres, string.Join(",", Boutique.OffresDuJour(j).Select(a => a.Id)));
            Assert.Equal(passages, string.Join(",", Boutique.Passages(j).Select(a => a.Id)));
            Assert.All(Boutique.OffresDuJour(j), a => Assert.True(Boutique.Disponible(a, j)));
        }
        finally
        {
            Boutique.Pluie = avant;
        }
    }

    [Fact]
    public void Synchro_compacte_de_l_inventaire()
    {
        var inv = Garnis.Select(a => a.Id).Concat(new[] { "casquette", "cape", "couleur-ambre" }).ToList();
        var garde = Boutique.Garde(inv);
        Assert.True(garde.Length < 40, garde);
        Assert.Equal(Garnis.Select(a => a.Id).OrderBy(x => x), Boutique.Deplier(garde).OrderBy(x => x));
        Assert.Equal(new[] { "casquette", "cape", "couleur-ambre" }, Boutique.HorsGarde(inv));
        Assert.Empty(Boutique.Deplier("!!pas du base64"));
        // Le compteur du groupe garde tout l'inventaire en restant petit.
        var p = new Profil();
        p.Bourse.Inventaire.AddRange(inv);
        p.Bourse.Equipe[Boutique.Titre] = new Port("titre-reveur", 5);
        var json = Groupe.Json(Groupe.Moi(p, "pc-1", "PC"));
        Assert.True(json.Length < 2600, $"{json.Length} caractères");
        var relu = Groupe.Lire(json)!;
        Assert.Equal(inv.OrderBy(x => x), relu.Objets.OrderBy(x => x));
        Assert.Equal("titre-reveur", relu.Porte[Boutique.Titre].Id);
    }

    // Calibrage : des petits achats chaque jour ou deux, et tout collectionner demande des mois.
    [Fact]
    public void Economie_calibree()
    {
        var collection = Boutique.Catalogue.Where(Boutique.Collectionnable).ToList();
        int total = collection.Sum(a => a.Prix);
        Assert.InRange(total, 60_000, 80_000);
        Assert.True(collection.Count(a => a.Prix <= 80) >= 30, "petits achats");
        foreach (Rarete r in Enum.GetValues<Rarete>())
            Assert.Contains(Garnis, a => a.Rarete == r);
        // Plus rare, plus cher (en moyenne, sur la boutique garnie).
        var moyennes = Enum.GetValues<Rarete>().Select(r => Garnis.Where(a => a.Rarete == r).Average(a => a.Prix)).ToList();
        for (int i = 1; i < moyennes.Count; i++) Assert.True(moyennes[i] > moyennes[i - 1]);
    }
}
