using System.Globalization;
using PilouBureau;
using Xunit;
using Xunit.Abstractions;

// Expéditions (docs/EXPEDITIONS.md) : jauge d'énergie, limites, tirage déterministe, équilibre, groupe.
public class ExpeditionsTests
{
    private const double H = 3_600_000;
    private static readonly DateTime Jour = new(2026, 11, 26, 10, 0, 0);
    private static readonly double T0 = new DateTimeOffset(Jour).ToUnixTimeMilliseconds();
    private readonly ITestOutputHelper _sortie;

    public ExpeditionsTests(ITestOutputHelper sortie) => _sortie = sortie;

    // ---- Jauge

    [Fact]
    public void Attente_remonte_doucement_jusqu_a_50_seulement()
    {
        var e = new Energie { Valeur = 10 };
        Assert.Equal(0, Jauge.Avancer(e, T0, false)); // première mesure : on note l'heure
        Assert.Equal(5, Jauge.Avancer(e, T0 + H, false), 6);
        Assert.Equal(15, e.Valeur, 6);
        Jauge.Avancer(e, T0 + 30 * H, false);
        Assert.Equal(Jauge.PlafondAttente, e.Valeur, 6);
        // Au-dessus de 50 (repas, travail), l'attente ne fait plus rien, et rien ne baisse.
        e.Valeur = 80;
        Assert.Equal(0, Jauge.Avancer(e, T0 + 40 * H, false));
        Assert.Equal(80, e.Valeur);
        // Une horloge qui recule ne fait rien.
        Assert.Equal(0, Jauge.Avancer(e, T0, false));
    }

    [Fact]
    public void Travail_productif_paie_par_tranches_et_plafonne_par_jour()
    {
        var e = new Energie { Valeur = 0 };
        // 5 min 59 : rien ; 6 min : +1.
        for (int i = 0; i < 359; i++) Jauge.Travailler(e, 1, Jour, false);
        Assert.Equal(0, e.Valeur);
        Assert.Equal(1, Jauge.Travailler(e, 1, Jour, false));
        // Un seul appel compte au plus une minute (un minuteur endormi ne paie pas d'un coup).
        Assert.Equal(0, Jauge.Travailler(e, 10_000, Jour, false));
        Assert.Equal(60, e.Reliquat);
        // Une journée entière de travail : plafonné à 40.
        for (int i = 0; i < 24 * 60; i++) Jauge.Travailler(e, 60, Jour.AddSeconds(i), false);
        Assert.Equal(Jauge.PlafondTravail, e.Travail);
        Assert.Equal(Jauge.PlafondTravail, e.Valeur, 6);
        // Le lendemain, le plafond repart.
        e.Reliquat = 0;
        double lendemain = 0;
        for (int i = 0; i < 6; i++) lendemain += Jauge.Travailler(e, 60, Jour.AddDays(1), false);
        Assert.Equal(1, lendemain);
        // Jamais au-dessus de 100.
        e.Valeur = 99.5;
        for (int i = 0; i < 100; i++) Jauge.Travailler(e, 60, Jour.AddDays(1), false);
        Assert.Equal(Jauge.Max, e.Valeur);
    }

    [Fact]
    public void Tours_finis_et_quetes_comptent_dans_le_plafond_du_travail()
    {
        var e = new Energie { Valeur = 0 };
        Assert.Equal(1, Jauge.Tour(e, T0, Jour, false));
        Assert.Equal(0, Jauge.Tour(e, T0 + 60_000, Jour, false)); // pas deux en 3 min
        Assert.Equal(1, Jauge.Tour(e, T0 + 180_000, Jour, false));
        Assert.Equal(2, Jauge.Quete(e, Jour, false));
        for (int i = 0; i < 100; i++) Jauge.Quete(e, Jour, false);
        Assert.Equal(Jauge.PlafondTravail, e.Travail);
        Assert.Equal(0, Jauge.Tour(e, T0 + 10 * H, Jour, false));
    }

    [Fact]
    public void Nourriture_rend_de_l_energie_dans_son_plafond()
    {
        var e = new Energie { Valeur = 0 };
        Assert.Equal(30, Jauge.Manger(e, "jus-etoile", Jour, false));
        Assert.Equal(6, Jauge.Manger(e, "plat", Jour, false));
        Assert.Equal(4, Jauge.Manger(e, "galette-route", Jour, false)); // reste 4 avant 40
        Assert.Equal(0, Jauge.Manger(e, "gateau", Jour, false));
        Assert.Equal(0, Jauge.Manger(e, "inconnu", Jour.AddDays(1), false));
        Assert.Equal(15, Jauge.Manger(e, "galette-route", Jour.AddDays(1), false));
        Assert.True(Jauge.Repas("plat") > Jauge.Repas("plat-rate"));
    }

    [Fact]
    public void Pilou_boudeur_se_recharge_deux_fois_moins_vite()
    {
        var a = new Energie { Valeur = 0, T = T0 };
        var b = new Energie { Valeur = 0, T = T0 };
        Jauge.Avancer(a, T0 + 4 * H, false);
        Jauge.Avancer(b, T0 + 4 * H, true);
        Assert.Equal(a.Valeur / 2, b.Valeur, 6);
        a.Valeur = b.Valeur = 0;
        for (int i = 0; i < 60; i++)
        {
            Jauge.Travailler(a, 60, Jour, false);
            Jauge.Travailler(b, 60, Jour, true);
        }
        Assert.Equal(10, a.Valeur, 6);
        Assert.Equal(5, b.Valeur, 6); // 30 min « utiles » : 5 tranches de 6 min
        Assert.Equal(15, Jauge.Manger(new Energie { Valeur = 0 }, "jus-etoile", Jour, true));
        Assert.Equal(1, Jauge.Quete(new Energie { Valeur = 0 }, Jour, true));
    }

    [Fact]
    public void Depenser_ne_passe_jamais_sous_zero()
    {
        var e = new Energie { Valeur = 20 };
        Assert.False(Jauge.Depenser(e, 25));
        Assert.Equal(20, e.Valeur);
        Assert.True(Jauge.Depenser(e, 20));
        Assert.Equal(0, e.Valeur);
        Assert.False(Jauge.Depenser(e, -5));
    }

    // ---- Lieux, outils, butin

    [Fact]
    public void Lieux_coherents()
    {
        Assert.InRange(Expeditions.Lieux.Count, 3, 5);
        Assert.Equal(Expeditions.Lieux.Count, Expeditions.Lieux.Select(l => l.Id).Distinct().Count());
        Assert.Equal(Expeditions.Lieux.Count, Expeditions.Lieux.Select(l => l.Signe).Distinct().Count()); // un signe de forme chacun
        Assert.Equal(1, Expeditions.Lieux[0].Niveau);
        for (int i = 1; i < Expeditions.Lieux.Count; i++)
        {
            var (a, b) = (Expeditions.Lieux[i - 1], Expeditions.Lieux[i]);
            Assert.True(b.Niveau > a.Niveau && b.Cout > a.Cout && b.Minutes > a.Minutes && b.Risque > a.Risque, b.Id);
        }
        Assert.All(Expeditions.Lieux, l =>
        {
            Assert.InRange(l.Minutes, 20, 120);
            Assert.InRange(l.Cout, 1, (int)Jauge.Max);
            Assert.InRange(l.Evenements + 2, 5, 8); // le journal : départ, événements, retour
            Assert.NotNull(Expeditions.Exclusif(l.Exclusif));
            Assert.Contains(l.Boss, Expeditions.Creatures.Select(c => c.Id));
            Assert.All(l.Faune, f => Assert.Contains(f, Expeditions.Creatures.Select(c => c.Id)));
        });
        Assert.InRange(Expeditions.Creatures.Count, 4, 6);
    }

    [Fact]
    public void Butin_exclusif_introuvable_en_boutique_mais_portable()
    {
        foreach (var a in Expeditions.Exclusifs)
        {
            Assert.Null(Boutique.Catalogue.FirstOrDefault(x => x.Id == a.Id));
            Assert.Same(a, Boutique.Trouver(a.Id));
            var b = new Bourse { PoGagnes = 10_000 };
            Assert.Equal("introuvable en boutique : butin d'expédition", Boutique.Acheter(b, a.Id, 99, 10_000, DateOnly.FromDateTime(Jour)));
            Assert.Equal(0, b.PoDepenses);
            if (Boutique.Slots.Contains(a.Slot))
            {
                Assert.False(Boutique.Equiper(b, a.Slot, a.Id, 1)); // pas encore à nous
                b.Inventaire.Add(a.Id);
                Assert.True(Boutique.Equiper(b, a.Slot, a.Id, 1));
            }
        }
        // Les en-cas de route s'achètent, eux (consommables).
        var bourse = new Bourse();
        Assert.Null(Boutique.Acheter(bourse, "galette-route", 1, 500, DateOnly.FromDateTime(Jour)));
        Assert.Null(Boutique.Acheter(bourse, "galette-route", 1, 500, DateOnly.FromDateTime(Jour)));
        Assert.Equal(2, bourse.Consommables["galette-route"]);
        Assert.Equal("niveau 5 requis", Boutique.Acheter(bourse, "jus-etoile", 1, 500, DateOnly.FromDateTime(Jour)));
        // Acheter de l'énergie ne rapporte jamais de po : un ⚡ coûte bien plus qu'il ne rapporte en expédition.
        double poParEnergie = Expeditions.Lieux.Max(l => Simuler(l, 30, 2000).Po / l.Cout);
        Assert.True(Boutique.Trouver("galette-route")!.Prix / Jauge.Repas("galette-route") > 5 * poParEnergie);
        Assert.True(Boutique.Trouver("jus-etoile")!.Prix / Jauge.Repas("jus-etoile") > 5 * poParEnergie);
    }

    [Fact]
    public void Equipement_leger_et_seulement_possede()
    {
        Assert.All(Expeditions.Outils, o => Assert.True(o.Combat + o.Piege + o.Butin <= 8, o.Id));
        Assert.All(Expeditions.Outils, o => Assert.Contains(o.Emplacement, new[] { "arme", "talisman" }));
        Assert.All(Expeditions.Outils.Where(o => o.Id != Expeditions.EpeeBois), o => Assert.NotNull(Boutique.Trouver(o.Id)));
        var armes = Expeditions.Disponibles("arme", new[] { "lanterne", "medaille" });
        Assert.Equal(new[] { Expeditions.EpeeBois, "lanterne" }, armes.Select(o => o.Id));
        Assert.Equal(new[] { "medaille" }, Expeditions.Disponibles("talisman", new[] { "lanterne", "medaille" }).Select(o => o.Id));
        Assert.Equal((5, 6, 0), Expeditions.Bonus("lanterne", "bouclier-couvercle"));
        // Un talisman mis en arme (ou l'inverse) ne compte pas.
        Assert.Equal((0, 0, 0), Expeditions.Bonus("medaille", "lanterne"));
        var e = new EtatExpedition { Energie = { Valeur = 100 }, Arme = "objet-inconnu", Talisman = "medaille" };
        var x = Expeditions.Partir(e, Expeditions.Lieux[0], 5, T0, Jour, ExpeditionsAutres.Aucun, "pc", "abc")!;
        Assert.Equal(Expeditions.EpeeBois, x.Arme);
        Assert.Equal("medaille", x.Talisman);
    }

    [Fact]
    public void Tout_est_dessine()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d is not null && !File.Exists(Path.Combine(d.FullName, "assets", "index.txt"))) d = d.Parent;
        var banque = Banque.DepuisDossier(Path.Combine(d!.FullName, "assets"));
        // Butin exclusif portable : dessiné, à son emplacement.
        foreach (var a in Expeditions.Exclusifs)
        {
            Assert.NotNull(banque[a.Id]);
            if (Boutique.Slots.Contains(a.Slot)) Assert.Equal(a.Slot, banque[a.Id]!.Slot);
        }
        foreach (var l in Expeditions.Lieux) Assert.NotNull(banque[Expeditions.Trophee(l.Boss)]);
        foreach (var c in Expeditions.Creatures) Assert.NotNull(banque["crea-" + c.Id]);
        foreach (var id in new[] { Expeditions.EpeeBois, "baluchon", "pansement", "coffre-expedition", "coffre-expedition-ouvert", "eclat-cristal",
                     "eclair-energie", "galette-route", "jus-etoile", "pancarte" })
            Assert.NotNull(banque[id]);
    }

    // ---- Limites

    [Fact]
    public void Energie_repos_et_trois_par_jour()
    {
        var l = Expeditions.Lieux[0];
        var e = new EtatExpedition { Energie = { Valeur = 100, T = T0 } };
        Assert.Equal("niveau 5 requis", Expeditions.Refus(e, Expeditions.Lieux[1], 4, T0, Jour, ExpeditionsAutres.Aucun));
        Assert.Equal("Pilou est en visite", Expeditions.Refus(e, l, 4, T0, Jour, ExpeditionsAutres.Aucun, "Pilou est en visite"));
        Assert.Null(Expeditions.Partir(e, l, 4, T0, Jour, ExpeditionsAutres.Aucun, "pc", "x", "Pilou est en visite"));
        double t = T0;
        for (int i = 0; i < Expeditions.ParJour; i++)
        {
            Assert.Null(Expeditions.Refus(e, l, 4, t, Jour, ExpeditionsAutres.Aucun));
            var x = Expeditions.Partir(e, l, 4, t, Jour, ExpeditionsAutres.Aucun, "pc", "x" + i)!;
            Assert.Equal(100 - (i + 1) * l.Cout, e.Energie.Valeur, 6);
            Assert.Equal("Pilou est déjà en expédition", Expeditions.Refus(e, l, 4, t + 1000, Jour, ExpeditionsAutres.Aucun));
            Assert.Null(Expeditions.Avancer(e, x.Fin - 1, Array.Empty<string>()));
            var r = Expeditions.Avancer(e, x.Fin, Array.Empty<string>());
            Assert.NotNull(r);
            Assert.Null(Expeditions.Avancer(e, x.Fin + 1, Array.Empty<string>())); // une seule résolution
            if (i < Expeditions.ParJour - 1)
                Assert.StartsWith("Pilou se repose encore", Expeditions.Refus(e, l, 4, x.Fin + 60_000, Jour, ExpeditionsAutres.Aucun));
            t = x.Fin + Expeditions.Repos;
        }
        Assert.Equal(0, Expeditions.Restantes(e, Jour, ExpeditionsAutres.Aucun));
        Assert.Contains("reviens demain", Expeditions.Refus(e, l, 4, t, Jour, ExpeditionsAutres.Aucun));
        // Le lendemain, trois de plus ; sans énergie, non.
        Assert.Null(Expeditions.Refus(e, l, 4, t, Jour.AddDays(1), ExpeditionsAutres.Aucun));
        e.Energie.Valeur = l.Cout - 1;
        Assert.Equal($"il faut {l.Cout} ⚡ (Pilou en a {l.Cout - 1})", Expeditions.Refus(e, l, 4, t, Jour.AddDays(1), ExpeditionsAutres.Aucun));
    }

    [Fact]
    public void La_limite_et_le_repos_valent_pour_tout_le_groupe()
    {
        var l = Expeditions.Lieux[0];
        var e = new EtatExpedition { Energie = { Valeur = 100 } };
        var autres = Expeditions.Autres(new[] { (Quetes.CleJour(Jour), 2, 0.0), (Quetes.CleJour(Jour.AddDays(-1)), 3, 0.0) }, Jour);
        Assert.Equal(2, autres.Aujourdhui); // les départs d'hier ne comptent plus
        Assert.Equal(1, Expeditions.Restantes(e, Jour, autres));
        Assert.NotNull(Expeditions.Partir(e, l, 1, T0, Jour, autres, "pc", "a"));
        Expeditions.Avancer(e, T0 + 10 * H, Array.Empty<string>());
        Assert.Contains("reviens demain", Expeditions.Refus(e, l, 1, T0 + 10 * H, Jour, autres));
        // Pilou parti depuis l'autre PC : ici, il se repose jusqu'à son retour (+ repos).
        var f = new EtatExpedition { Energie = { Valeur = 100 } };
        var loin = Expeditions.Autres(new[] { (Quetes.CleJour(Jour), 1, T0 + H) }, Jour);
        Assert.StartsWith("Pilou se repose encore", Expeditions.Refus(f, l, 1, T0, Jour, loin));
        Assert.Null(Expeditions.Refus(f, l, 1, T0 + H, Jour, loin));
    }

    [Fact]
    public void Rappel_rentre_les_mains_vides()
    {
        var p = new Profil();
        var e = p.Expedition;
        e.Energie.Valeur = 100;
        var x = Expeditions.Partir(e, Expeditions.Lieux[0], 1, T0, Jour, ExpeditionsAutres.Aucun, "pc", "r")!;
        var r = Expeditions.Rappeler(e, T0 + 60_000)!;
        Assert.Equal(Denouement.Rappel, r.Issue);
        Assert.Null(e.Courante);
        Assert.Equal((0, 0, ""), Expeditions.Crediter(p, r));
        Assert.Equal(0, p.Bourse.PoGagnes);
        Assert.Equal(1, e.Nombre); // le départ reste compté
        Assert.StartsWith("Pilou se repose encore", Expeditions.Refus(e, Expeditions.Lieux[0], 1, T0 + 120_000, Jour, ExpeditionsAutres.Aucun));
        Assert.Null(Expeditions.Avancer(e, x.Fin, Array.Empty<string>()));
    }

    // ---- Tirage déterministe

    // L'avance de niveau se voit : au départ (+0,6 % par niveau au-dessus du lieu, 6 % au plus) et dans la ligne du boss.
    [Fact]
    public void L_aide_du_niveau_se_voit_au_depart_et_contre_le_boss()
    {
        var l = Expeditions.Lieux[1];
        Assert.Equal("", Expeditions.AideAuDepart(l, l.Niveau));
        Assert.Equal("ton niveau t'aide : +1,8 %", Expeditions.AideAuDepart(l, l.Niveau + 3));
        Assert.Equal("ton niveau t'aide : +6 % (au plus)", Expeditions.AideAuDepart(l, l.Niveau + 25));
        int vus = 0;
        for (int i = 0; i < 200; i++)
        {
            var bas = Expeditions.Resoudre(Exp(l, "b" + i, l.Niveau), Array.Empty<string>()).Journal;
            var haut = Expeditions.Resoudre(Exp(l, "b" + i, l.Niveau + 3), Array.Empty<string>()).Journal;
            Assert.DoesNotContain(bas, s => s.Contains("mon niveau"));
            var boss = haut.Where(s => s.StartsWith("★") || s.Contains("(♥ −2)")).ToList();
            Assert.All(boss, s => Assert.Contains("+1,8 %", s));
            vus += boss.Count;
        }
        Assert.True(vus > 20, $"{vus} combats de boss");
    }

    private static Expedition Exp(Lieu l, string id, int niveau, string arme = "", string talisman = "") => new()
    {
        Id = id, Lieu = l.Id, Debut = T0, Fin = T0 + l.Minutes * 60_000.0, Graine = Expeditions.GraineDe("pc-essai", id), Niveau = niveau,
        Arme = arme == "" ? Expeditions.EpeeBois : arme, Talisman = talisman,
    };

    [Fact]
    public void Meme_graine_meme_aventure()
    {
        var l = Expeditions.Lieux[2];
        var a = Expeditions.Resoudre(Exp(l, "graine-1", 12), Array.Empty<string>());
        var b = Expeditions.Resoudre(Exp(l, "graine-1", 12), Array.Empty<string>());
        Assert.Equal(a.Journal, b.Journal);
        Assert.Equal((a.Issue, a.Po, a.Xp, a.Fragments, a.Objet), (b.Issue, b.Po, b.Xp, b.Fragments, b.Objet));
        // Graine stable d'une version à l'autre (FNV-1a + xorshift : rien qui dépende du runtime).
        Assert.Equal(Hasard.Graine("expedition|pc-essai|graine-1"), Expeditions.GraineDe("pc-essai", "graine-1"));
        // Des graines différentes racontent d'autres histoires.
        var journaux = Enumerable.Range(0, 40).Select(i => string.Join("|", Expeditions.Resoudre(Exp(l, "g" + i, 12), Array.Empty<string>()).Journal));
        Assert.True(journaux.Distinct().Count() > 30);
    }

    [Fact]
    public void Journal_court_et_lisible()
    {
        foreach (var l in Expeditions.Lieux)
            for (int i = 0; i < 300; i++)
            {
                var r = Expeditions.Resoudre(Exp(l, $"j{i}", l.Niveau + 3), Array.Empty<string>());
                Assert.InRange(r.Journal.Count, 5, 8);
                Assert.All(r.Journal, s => Assert.InRange(s.Length, 10, 130));
                Assert.All(r.Journal, s => Assert.DoesNotContain("{", s));
                Assert.StartsWith("✦", r.Journal[0]);
                Assert.Equal(r.Issue switch { Denouement.Victoire => "✓", Denouement.Partielle => "◐", _ => "✕" }, r.Journal[^1][..1]);
                if (r.Issue == Denouement.Defaite)
                {
                    Assert.Equal(0, r.Po);
                    Assert.Equal("", r.Objet);
                    Assert.True(r.Xp >= 1);
                }
                if (r.Objet != "") Assert.Equal(Denouement.Victoire, r.Issue);
            }
    }

    [Fact]
    public void Credite_une_seule_fois_et_forge_les_eclats()
    {
        var p = new Profil();
        var l = Expeditions.Lieux[1];
        var r = Enumerable.Range(0, 500).Select(i => Expeditions.Resoudre(Exp(l, $"v{i}", 9), Array.Empty<string>()))
            .First(x => x.Issue == Denouement.Victoire && x.Po > 0);
        var (po, xp, _) = Expeditions.Crediter(p, r, g => (int)Math.Floor(g * 0.6 + 0.5)); // il boude : × 0,6
        Assert.Equal((int)Math.Floor(r.Po * 0.6 + 0.5), po);
        Assert.Equal(po, p.Bourse.PoGagnes);
        Assert.Equal(xp, p.Xp);
        Assert.Equal((0, 0, ""), Expeditions.Crediter(p, r));
        Assert.Equal(po, p.Bourse.PoGagnes);
        Assert.Equal(1, p.Expedition.Victoires);
        // 25 éclats : un objet exclusif forgé (le premier qui manque), puis des po quand tout est là.
        p.Expedition.Fragments = Expeditions.Forge - 1;
        var (_, _, forge) = Expeditions.Crediter(p, new Resultat { Issue = Denouement.Partielle, Fragments = 1 });
        Assert.Equal(Expeditions.Exclusifs[0].Id, forge);
        Assert.Contains(forge, p.Bourse.Inventaire);
        Assert.Equal(0, p.Expedition.Fragments);
        foreach (var a in Expeditions.Exclusifs) if (!p.Bourse.Inventaire.Contains(a.Id)) p.Bourse.Inventaire.Add(a.Id);
        int avant = p.Bourse.PoGagnes;
        Expeditions.Crediter(p, new Resultat { Issue = Denouement.Partielle, Fragments = Expeditions.Forge });
        Assert.Equal(avant + 40, p.Bourse.PoGagnes);
    }

    [Fact]
    public void Butin_exclusif_jamais_en_double_et_trophee_une_fois()
    {
        var l = Expeditions.Lieux[0];
        var tous = Expeditions.Exclusifs.Select(a => a.Id).ToList();
        for (int i = 0; i < 3000; i++)
        {
            var r = Expeditions.Resoudre(Exp(l, $"d{i}", 30, "canne-or", "carte-tresor"), new[] { "torche" }, new[] { Expeditions.Trophee(l.Boss) });
            Assert.NotEqual("torche", r.Objet);
            Assert.Equal("", r.Trophee);
            var s = Expeditions.Resoudre(Exp(l, $"d{i}", 30, "canne-or", "carte-tresor"), tous);
            Assert.Equal("", s.Objet);
            if (s.Boss && s.Issue == Denouement.Victoire) Assert.Equal("trophee-bug-geant", s.Trophee);
        }
    }

    [Fact]
    public void Exemples_de_journal()
    {
        var l = Expeditions.Lieux[2];
        foreach (var voulu in new[] { Denouement.Victoire, Denouement.Partielle, Denouement.Defaite })
        {
            var r = Enumerable.Range(0, 2000).Select(i => Expeditions.Resoudre(Exp(l, $"ex{i}", 12, "lanterne", "medaille"), Array.Empty<string>()))
                .First(x => x.Issue == voulu && (voulu != Denouement.Victoire || x.Boss));
            _sortie.WriteLine($"-- {Expeditions.NomIssue(r.Issue)} : {r.Po} po, {r.Xp} xp");
            foreach (var ligne in r.Journal) _sortie.WriteLine(ligne);
        }
    }

    // ---- Équilibre (chiffres repris dans la PR)

    private sealed record Bilan(double Victoire, double Partielle, double Defaite, double Po, double Xp, double Rare, double Exclusif, double Boss);

    private static Bilan Simuler(Lieu l, int niveau, int n, string arme = "", string talisman = "")
    {
        int v = 0, pa = 0, d = 0, rare = 0, excl = 0, boss = 0;
        double po = 0, xp = 0;
        for (int i = 0; i < n; i++)
        {
            var r = Expeditions.Resoudre(Exp(l, $"s{l.Id}{arme}{talisman}{i}", niveau, arme, talisman), Array.Empty<string>());
            if (r.Issue == Denouement.Victoire) v++;
            else if (r.Issue == Denouement.Partielle) pa++;
            else d++;
            po += r.Po;
            xp += r.Xp;
            if (r.Rares > 0) rare++;
            if (r.Objet != "") excl++;
            if (r.Boss) boss++;
        }
        return new Bilan(v / (double)n, pa / (double)n, d / (double)n, po / n, xp / n, rare / (double)n, excl / (double)n, boss / (double)n);
    }

    [Fact]
    public void Equilibre_sur_10000_expeditions_par_lieu()
    {
        const int N = 10_000;
        var lignes = new List<string> { "lieu | niv | ⚡ | durée | victoire | partielle | défaite | po moy. | xp moy. | butin rare | exclusif | po/jour (3) | xp/jour (3)" };
        var bilans = Expeditions.Lieux.Select(l => (l, Simuler(l, l.Niveau + 2, N))).ToList();
        foreach (var (l, b) in bilans)
            lignes.Add(string.Create(CultureInfo.InvariantCulture,
                $"{l.Nom} | {l.Niveau} | {l.Cout} | {Expeditions.Duree(l.Minutes)} | {b.Victoire:P1} | {b.Partielle:P1} | {b.Defaite:P1} | {b.Po:0.0} | {b.Xp:0.0} | {b.Rare:P1} | {b.Exclusif:P2} | {3 * b.Po:0} | {3 * b.Xp:0}"));
        foreach (var s in lignes) _sortie.WriteLine(s);
        foreach (var (l, b) in bilans)
        {
            // Il gagne le plus souvent, perd parfois.
            Assert.InRange(b.Victoire, 0.35, 0.80);
            Assert.InRange(b.Defaite, 0.05, 0.30);
            // Butin exclusif rare : quelques pour cent au plus.
            Assert.InRange(b.Exclusif, 0.003, 0.05);
            // Une journée (3 expéditions) rapporte de l'ordre d'une ou deux parties de pêche (≈ 10 à 40 po, ≈ 10 à 30 xp).
            Assert.InRange(3 * b.Po, 8, 40);
            Assert.InRange(3 * b.Xp, 5, 30);
        }
        // Un bon équipement aide un peu, sans tout changer.
        var nu = Simuler(Expeditions.Lieux[2], 12, N);
        var equipe = Simuler(Expeditions.Lieux[2], 12, N, "torche", "bouclier-couvercle");
        Assert.InRange(equipe.Victoire - nu.Victoire, 0.02, 0.20);
        lignes.Add(string.Create(CultureInfo.InvariantCulture,
            $"Tour du tampon, torche + bouclier-couvercle : victoire {equipe.Victoire:P1} (sans : {nu.Victoire:P1})"));
        // Une journée type, limitée par l'énergie : 50 (attente) + 60 (travail) + ≈ 10 (un plat) ≈ 120 ⚡.
        foreach (var l in Expeditions.Lieux)
        {
            var b = Simuler(l, l.Niveau + 2, 2000);
            int parJour = Math.Min(Expeditions.ParJour, 120 / l.Cout);
            lignes.Add(string.Create(CultureInfo.InvariantCulture, $"journée type (≈ 120 ⚡) à {l.Nom} : {parJour} × → {parJour * b.Po:0} po, {parJour * b.Xp:0} xp"));
        }
        foreach (var s in lignes) _sortie.WriteLine(s);
    }

    // ---- Groupe : pas de double gain

    [Fact]
    public void Gains_d_une_expedition_comptes_une_fois_dans_le_groupe()
    {
        var pc = new Profil { Machine = "PC-MAISON" };
        var travail = new Profil { Machine = "PC-TRAVAIL" };
        pc.Expedition.Energie.Valeur = 100;
        var l = Expeditions.Lieux[0];
        var x = Expeditions.Partir(pc.Expedition, l, 3, T0, Jour, ExpeditionsAutres.Aucun, "maison-1", "g1")!;
        var r = Expeditions.Avancer(pc.Expedition, x.Fin, pc.Bourse.Inventaire)!;
        Expeditions.Crediter(pc, r);
        Expeditions.Crediter(pc, r); // relu au redémarrage : rien de plus
        int gagne = pc.Bourse.PoGagnes;
        // Le compteur de ce PC voyage (relais), arrive deux fois, et en retard : le solde de l'autre PC ne le compte qu'une fois.
        var c = Groupe.Lire(Groupe.Json(Groupe.Moi(pc, "maison-1", "PC-MAISON")))!;
        Assert.Equal(1, c.ExpNombre);
        Assert.Equal(Quetes.CleJour(Jour), c.ExpJour);
        Assert.Equal(pc.Expedition.Libre, c.ExpLibre);
        var mem = new Groupe.Memoire();
        mem.Fusionner(c, "travail-1");
        mem.Fusionner(c, "travail-1");
        Assert.Equal(gagne, Groupe.SoldePo(travail, Array.Empty<Profil>(), mem.Compteurs));
        // Vu à la fois par le dossier partagé et par le relais : toujours une fois.
        Assert.Equal(gagne, Groupe.SoldePo(travail, new[] { pc }, mem.Compteurs));
        // L'autre PC n'a pas d'expédition à résoudre (elle appartient au PC qui l'a lancée)…
        Assert.Null(Expeditions.Avancer(travail.Expedition, x.Fin + H, travail.Bourse.Inventaire));
        // … et il voit la limite du jour et le repos du groupe.
        var autres = Expeditions.Autres(mem.Compteurs.Select(k => (k.ExpJour, k.ExpNombre, k.ExpLibre)), Jour);
        Assert.Equal(Expeditions.ParJour - 1, Expeditions.Restantes(travail.Expedition, Jour, autres));
        Assert.Equal(pc.Expedition.Libre, Expeditions.LibreA(travail.Expedition, autres));
    }

    [Fact]
    public void Fusion_des_compteurs_d_expedition()
    {
        var hier = new Groupe.Compteur("a", "A", "A", 0, 0, 1, Array.Empty<string>(), Array.Empty<string>(), ExpJour: "2026-11-25", ExpNombre: 3, ExpLibre: 100);
        var auj = hier with { T = 2, ExpJour = "2026-11-26", ExpNombre = 1, ExpLibre = 50 };
        var mem = new Groupe.Memoire();
        mem.Fusionner(hier, "moi");
        Assert.True(mem.Fusionner(auj, "moi"));
        var f = mem.Autres["a"];
        Assert.Equal(("2026-11-26", 1, 100.0), (f.ExpJour, f.ExpNombre, f.ExpLibre));
        // Un vieux message arrivé en retard ne fait pas reculer le jour.
        mem.Fusionner(hier, "moi");
        Assert.Equal(("2026-11-26", 1), (mem.Autres["a"].ExpJour, mem.Autres["a"].ExpNombre));
        // Un ancien PC (sans « exp ») : rien.
        var vieux = Groupe.Lire("{\"appareil\":\"b\",\"xp\":3}")!;
        Assert.Equal(("", 0, 0.0), (vieux.ExpJour, vieux.ExpNombre, vieux.ExpLibre));
    }

    // ---- Quêtes et téléphone

    [Fact]
    public void Quetes_d_expedition()
    {
        var q = new EtatQuetes();
        Assert.DoesNotContain(Quetes.Tirer(Periode.Semaine, "S2026-11-23", "pc", q.Vues), x => x.Cle.StartsWith("expedition"));
        foreach (var cle in new[] { "expedition", "expedition:boss", "expedition:rare" })
            Assert.NotNull(Quetes.Modeles.FirstOrDefault(m => m.Cle == cle));
        // Une fois vues, elles peuvent tomber.
        var vues = new[] { "expedition", "expedition:boss", "expedition:rare" };
        bool vue = Enumerable.Range(0, 60).Any(i => Quetes.Tirer(Periode.Semaine, $"S{i}", "pc", vues).Any(x => x.Cle.StartsWith("expedition")));
        Assert.True(vue);
        Assert.Equal("Termine 1 expédition", Quetes.Texte(Quetes.Modeles.First(m => m.Cle == "expedition"), 1));
        Assert.Equal("Rapporte 2 butins rares d'expédition", Quetes.Texte(Quetes.Modeles.First(m => m.Cle == "expedition:rare"), 2));
    }

    [Fact]
    public void Ce_que_voit_le_telephone()
    {
        var e = new EtatExpedition { Energie = { Valeur = 73.6 } };
        var d = Expeditions.PourTelephone(e, T0, Jour, ExpeditionsAutres.Aucun);
        Assert.Equal(73, d["energie"]);
        Assert.Equal("pret", d["etat"]);
        var x = Expeditions.Partir(e, Expeditions.Lieux[0], 1, T0, Jour, ExpeditionsAutres.Aucun, "pc", "t")!;
        d = Expeditions.PourTelephone(e, T0 + 1000, Jour, ExpeditionsAutres.Aucun);
        Assert.Equal("en", d["etat"]);
        Assert.Equal("Caverne des câbles", d["lieu"]);
        Assert.Equal(x.Fin, d["retour"]);
        Assert.Equal(2, d["reste"]);
        Expeditions.Avancer(e, x.Fin, Array.Empty<string>());
        d = Expeditions.PourTelephone(e, x.Fin + 1000, Jour, ExpeditionsAutres.Aucun);
        Assert.Equal("repos", d["etat"]);
        Assert.IsType<List<string>>(d["journal"]);
        Assert.InRange(((List<string>)d["journal"]).Count, 5, 8);
        // Le tout reste petit (le message ntfy est limité à 4 096 octets).
        Assert.True(System.Text.Json.JsonSerializer.Serialize(d).Length < 1400);
        Assert.Equal($"en expédition · Caverne des câbles · retour vers 15 h 40",
            Expeditions.Ligne(new EtatExpedition { Courante = new Expedition { Lieu = "caverne-cables" } }, new DateTime(2026, 11, 26, 15, 40, 0)));
    }
}
