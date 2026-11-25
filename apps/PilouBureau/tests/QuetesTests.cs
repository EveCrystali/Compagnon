using PilouBureau;
using Xunit;

public class QuetesTests
{
    private static readonly DateTime Mercredi = new(2026, 11, 25, 10, 0, 0);

    [Fact]
    public void Meme_jour_meme_appareil_memes_quetes_et_autre_appareil_autres()
    {
        var a = Quetes.Tirer(Periode.Jour, Quetes.CleJour(Mercredi), "pc-perso", Array.Empty<string>());
        var b = Quetes.Tirer(Periode.Jour, Quetes.CleJour(Mercredi), "pc-perso", Array.Empty<string>());
        Assert.Equal(3, a.Count);
        Assert.Equal(a.Select(q => q.Texte), b.Select(q => q.Texte));
        Assert.Equal(3, a.Select(q => q.Cle).Distinct().Count());
        var autres = Enumerable.Range(0, 20).Select(i => string.Join("|", Quetes.Tirer(Periode.Jour, Quetes.CleJour(Mercredi), "pc-" + i, Array.Empty<string>()).Select(q => q.Texte)));
        Assert.True(autres.Distinct().Count() > 1);
        Assert.All(a, q => Assert.InRange(q.Po, 20, 40));
    }

    [Fact]
    public void Quetes_optionnelles_seulement_apres_un_premier_signal()
    {
        for (int i = 0; i < 40; i++)
            Assert.DoesNotContain(Quetes.Tirer(Periode.Semaine, "S" + i, "g" + i, Array.Empty<string>()), q => q.Cle is "tour" or "commit" or "chasse" or "activite:code");
        var vues = new[] { "tour", "commit", "tests", "chasse", "activite:code" };
        bool vu = Enumerable.Range(0, 40).Any(i => Quetes.Tirer(Periode.Semaine, "S" + i, "g" + i, vues).Any(q => q.Cle == "tour"));
        Assert.True(vu);
    }

    [Fact]
    public void Actualiser_renouvelle_a_minuit_et_le_lundi_et_garde_la_semaine_en_cours()
    {
        var e = new EtatQuetes();
        Quetes.Actualiser(e, Mercredi, "pc");
        Assert.Equal(7, e.Liste.Count);
        var semaine = e.Liste.Where(q => q.Periode == Periode.Semaine).Select(q => q.Id).ToList();
        e.Liste.First(q => q.Periode == Periode.Jour).Fait = 1;

        Quetes.Actualiser(e, Mercredi.AddDays(1), "pc");
        Assert.All(e.Liste.Where(q => q.Periode == Periode.Jour), q => Assert.Equal(0, q.Fait));
        Assert.Equal(semaine, e.Liste.Where(q => q.Periode == Periode.Semaine).Select(q => q.Id).ToList());

        Quetes.Actualiser(e, new DateTime(2026, 11, 30, 0, 5, 0), "pc"); // lundi
        Assert.NotEqual(semaine, e.Liste.Where(q => q.Periode == Periode.Semaine).Select(q => q.Id).ToList());
        Assert.Equal("S2026-11-30", e.Semaine);
        Assert.Equal("S2026-11-23", Quetes.CleSemaine(Mercredi));
    }

    [Fact]
    public void Signaler_fait_avancer_reussit_une_fois_et_ouvre_le_coffre()
    {
        var e = new EtatQuetes();
        Quetes.Actualiser(e, Mercredi, "pc");
        var jour = e.Liste.Where(q => q.Periode == Periode.Jour).ToList();
        var gains = new List<RecompenseQuete>();
        foreach (var q in jour)
        {
            Assert.DoesNotContain(Quetes.Signaler(e, q.Cle, q.Objectif - 1, Mercredi, "pc"), r => r.Texte == q.Texte);
            gains.AddRange(Quetes.Signaler(e, q.Cle, 5000, Mercredi, "pc"));
        }
        Assert.All(jour, q => Assert.True(q.Reussie));
        Assert.Single(gains, r => r.Coffre);
        Assert.Equal(1, Quetes.Serie(e, Mercredi));
        // Plus rien à gagner sur les mêmes quêtes.
        foreach (var q in jour) Assert.DoesNotContain(Quetes.Signaler(e, q.Cle, 10, Mercredi, "pc"), r => r.Texte == q.Texte);
    }

    [Fact]
    public void Serie_de_jours_d_affilee_puis_remise_a_zero()
    {
        var e = new EtatQuetes();
        for (int j = 0; j < 3; j++)
        {
            var t = Mercredi.AddDays(j);
            Quetes.Actualiser(e, t, "pc");
            foreach (var q in e.Liste.Where(q => q.Periode == Periode.Jour).ToList()) Quetes.Signaler(e, q.Cle, 100000, t, "pc");
        }
        Assert.Equal(3, Quetes.Serie(e, Mercredi.AddDays(2)));
        Assert.Equal(3, Quetes.Serie(e, Mercredi.AddDays(3)));   // aujourd'hui pas encore fini : la série tient
        Assert.Equal(0, Quetes.Serie(e, Mercredi.AddDays(5)));   // un jour sauté
    }

    [Fact]
    public void Mesure_max_pour_le_score_de_chasse()
    {
        var e = new EtatQuetes { Vues = { "chasse" } };
        var q = new Quete { Cle = "chasse", Objectif = 1500, Periode = Periode.Semaine, Po = 100, Xp = 20 };
        e.Semaine = Quetes.CleSemaine(Mercredi);
        e.Jour = Quetes.CleJour(Mercredi);
        e.Mois = Quetes.CleMois(Mercredi);
        Quetes.Actualiser(e, Mercredi, "pc");
        e.Liste.Add(q);
        Quetes.Signaler(e, "chasse", 900, Mercredi, "pc");
        Quetes.Signaler(e, "chasse", 700, Mercredi, "pc");
        Assert.Equal(900, q.Fait);
        Assert.False(q.Reussie);
        Assert.Contains(Quetes.Signaler(e, "chasse", 1600, Mercredi, "pc"), r => r.Po == 100);
    }

    [Fact]
    public void Appliquer_credite_po_et_xp()
    {
        var p = new Profil();
        var (po, xp) = Quetes.Appliquer(p, new[] { new RecompenseQuete("a", 30, 6, false), new RecompenseQuete("b", 50, 10, true) });
        Assert.Equal((80, 16), (po, xp));
        Assert.Equal(80, p.Bourse.PoGagnes);
        Assert.Equal(16, p.Xp);
    }
}

public class BoutiqueTests
{
    private static readonly DateOnly Jour = new(2026, 11, 25);

    [Fact]
    public void Catalogue_complet_et_coherent()
    {
        var ids = new[]
        {
            "chapeau-pirate", "haut-de-forme", "casquette", "bandeau-ninja", "cornes-viking", "aureole", "chapeau-sorcier", "couronne-fleurs",
            "lunettes-rondes", "monocle", "masque-plongee", "echarpe", "cape", "medaille", "baguette", "ballon-helium", "parapluie", "tasse-cafe",
            "petit-chat", "petit-poisson-bocal", "trainee-coeurs", "trainee-notes", "aura", "lavande", "corail-orange", "ardoise", "sable", "glacier",
        };
        foreach (var id in ids) Assert.NotNull(Boutique.Trouver(id));
        Assert.Equal(Boutique.Catalogue.Count, Boutique.Catalogue.Select(a => a.Id).Distinct().Count());
        Assert.All(Boutique.Catalogue, a => Assert.InRange(a.Prix, 60, 600));
        Assert.All(Boutique.Catalogue, a => Assert.Contains(a.Slot, Boutique.Slots));
    }

    [Fact]
    public void Offres_du_jour_stables_variees_et_non_permanentes()
    {
        var a = Boutique.OffresDuJour(Jour);
        Assert.Equal(4, a.Count);
        Assert.Equal(a, Boutique.OffresDuJour(Jour));
        Assert.All(a, x => Assert.False(x.Permanent));
        Assert.Equal(4, a.Select(x => x.Id).Distinct().Count());
        var semaine = Enumerable.Range(0, 7).Select(i => string.Join(",", Boutique.OffresDuJour(Jour.AddDays(i)).Select(x => x.Id)));
        Assert.True(semaine.Distinct().Count() > 1);
        Assert.Equal(a[0].Prix * 3 / 4, Boutique.Prix(a[0], Jour));
    }

    [Fact]
    public void Achat_refuse_sans_assez_de_po_ou_de_niveau_et_solde_jamais_negatif()
    {
        var b = new Bourse { PoGagnes = 100 };
        Assert.Equal("il manque 20 po", Boutique.Acheter(b, "echarpe", 5, 50, Jour));
        var cher = Boutique.Catalogue.First(x => x.NiveauMin >= 10);
        Assert.Contains("niveau", Boutique.Acheter(b, cher.Id, 1, 10_000, Jour));
        Assert.Null(Boutique.Acheter(b, "echarpe", 5, 100, Jour));
        Assert.Equal(70, b.PoDepenses);
        Assert.Equal("déjà dans l'inventaire", Boutique.Acheter(b, "echarpe", 5, 100, Jour));
        var horsVente = Boutique.Catalogue.First(x => !x.Permanent && Boutique.OffresDuJour(Jour).All(o => o.Id != x.Id));
        Assert.Equal("pas en vente aujourd'hui", Boutique.Acheter(b, horsVente.Id, 50, 10_000, Jour));
    }

    [Fact]
    public void Equiper_seulement_ce_qu_on_possede_au_bon_emplacement()
    {
        var b = new Bourse { Inventaire = { "casquette", "echarpe" } };
        Assert.True(Boutique.Equiper(b, Boutique.Tete, "casquette", 10));
        Assert.False(Boutique.Equiper(b, Boutique.Yeux, "casquette", 11));
        Assert.False(Boutique.Equiper(b, Boutique.Tete, "aureole", 12));
        Assert.True(Boutique.Equiper(b, Boutique.Tete, "", 13));
        Assert.Empty(Boutique.Porte(b.Equipe));
    }

    [Fact]
    public void Groupe_solde_somme_des_appareils_et_achats_du_telephone_au_maximum()
    {
        var moi = new Profil { Machine = "PERSO", Bourse = new Bourse { PoGagnes = 300, PoDepenses = 80, PoDepTelephone = 50, Inventaire = { "echarpe" } } };
        var tagg = new Groupe.Compteur("b", "TAGG", "TAGG", 0, 0, 1, Array.Empty<string>(), Array.Empty<string>(), 200, 120, 50,
            new[] { "casquette" }, new Dictionary<string, Port> { [Boutique.Tete] = new("casquette", 5) });
        Assert.Equal(300 - 80 + 200 - 120 - 50, Groupe.SoldePo(moi, Array.Empty<Profil>(), new[] { tagg }));
        // Vu deux fois (dossier partagé et relais) : compté une fois.
        var tagg2 = new Profil { Machine = "TAGG", Bourse = new Bourse { PoGagnes = 150, PoDepenses = 100 } };
        Assert.Equal(300 - 80 + 200 - 120 - 50, Groupe.SoldePo(moi, new[] { tagg2 }, new[] { tagg }));
        Assert.Equal(new[] { "casquette", "echarpe" }, Groupe.Inventaire(moi, Array.Empty<Profil>(), new[] { tagg }));
        moi.Bourse.Equipe[Boutique.Tete] = new Port("", 9); // retiré plus tard ici : la dernière écriture gagne
        Assert.Equal("", Groupe.Equipe(moi, Array.Empty<Profil>(), new[] { tagg })[Boutique.Tete].Id);
    }

    [Fact]
    public void Compteur_porte_po_objets_et_equipement_et_fusionne()
    {
        var p = new Profil { Machine = "PERSO", Bourse = new Bourse { PoGagnes = 90, PoDepenses = 60, Inventaire = { "echarpe" } } };
        p.Bourse.Equipe[Boutique.Cou] = new Port("echarpe", 42);
        var relu = Groupe.Lire(Groupe.Json(Groupe.Moi(p, "a", "Perso")))!;
        Assert.Equal((90, 60), (relu.PoGagnes, relu.PoDepenses));
        Assert.Equal(new[] { "echarpe" }, relu.Objets);
        Assert.Equal("echarpe", relu.Porte[Boutique.Cou].Id);

        var mem = new Groupe.Memoire();
        Assert.True(mem.Fusionner(relu, "moi"));
        Assert.True(mem.Fusionner(relu with { PoGagnes = 120, Inventaire = new[] { "casquette" } }, "moi"));
        var f = mem.Autres["a"];
        Assert.Equal(120, f.PoGagnes);
        Assert.Equal(new[] { "casquette", "echarpe" }, f.Objets);
        Assert.False(mem.Fusionner(relu, "moi")); // plus ancien : rien ne change
    }

    [Fact]
    public void Gains_du_telephone_font_avancer_les_quetes_et_achetent_une_fois()
    {
        var p = new Profil { Bourse = new Bourse { PoGagnes = 500 } };
        var local = new DateTime(2026, 11, 25, 12, 0, 0);
        Quetes.Actualiser(p.Quetes, local, "pc");
        var peche = p.Quetes.Liste.FirstOrDefault(q => q.Cle == "peche");
        var g = new Telephone.Gain("g1", 10, new Dictionary<string, int> { ["goujon"] = 60 }, Array.Empty<string>(), 0,
            Achats: new[] { "echarpe" }, Equipe: new Dictionary<string, string> { [Boutique.Cou] = "echarpe" }, T: 99);
        var r = Telephone.Recevoir(p, g, new Telephone.Contexte(local, "pc", 5, 500));
        Assert.Equal(new[] { "echarpe" }, r.Achetes);
        Assert.Equal(70, p.Bourse.PoDepTelephone);
        Assert.Equal("echarpe", p.Bourse.Equipe[Boutique.Cou].Id);
        if (peche is not null) Assert.True(peche.Reussie);
        Assert.Equal(0, Telephone.Recevoir(p, g, new Telephone.Contexte(local, "pc", 5, 500)).Xp); // relu : rien
        Assert.Equal(70, p.Bourse.PoDepTelephone);

        var lu = Telephone.LireGain("""{"id":"g2","xp":3,"jeux":2,"chasse":1800,"achats":["casquette","inconnu"],"equipe":{"tete":"casquette","nimporte":"x"},"t":5}""")!;
        Assert.Equal((2, 1800), (lu.Jeux, lu.Chasse));
        Assert.Equal(new[] { "casquette" }, lu.Achats);
        Assert.Single(lu.Equipe!);
    }
}
