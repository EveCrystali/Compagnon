using System.Text.Json;
using PilouBureau;
using Xunit;
using Xunit.Abstractions;

// Métiers et succès partagés par le groupe d'appareils : chaque PC publie SES heures et SES compteurs,
// le total est la somme (maximum par appareil), les succès et les grades payés sont une union.
public class GroupeMetiersTests(ITestOutputHelper sortie)
{
    private const string Code = "ABCD-EFGH-JKMN-PQRS";
    private const long H = 3600;

    private static Groupe.Compteur C(string appareil, string machine, double t, Dictionary<string, long>? secondes = null,
        string[]? succes = null, Dictionary<string, int>? payes = null, int clavier = 0, int record = 0, int boss = 0) =>
        new(appareil, machine, machine, 0, 0, t, Array.Empty<string>(), Array.Empty<string>(),
            Secondes: secondes, SuccesObtenus: succes, MetiersPayes: payes, Clavier: clavier, DefRecord: record, DefBoss: boss);

    // Un compteur tel qu'il revient du relais (JSON publié puis relu).
    private static Groupe.Compteur Relu(Groupe.Compteur c) => Groupe.Lire(Groupe.Json(c))!;

    [Fact]
    public void Les_heures_du_groupe_sont_la_somme_des_appareils()
    {
        var moi = new Profil { Machine = "RTX", Activites = new() { ["code"] = 20 * H, ["musique"] = H }, SeancesClavier = 10, Defense = { Meilleur = 500, Boss = 1 } };
        var groupe = new[]
        {
            Relu(C("tagg-1", "TAGG", 1, new() { ["code"] = 15 * H, ["tableur"] = 7 * H }, clavier: 20, record: 900, boss: 2)),
            Relu(C("salon-2", "SALON", 1, new() { ["code"] = 10 * H })),
        };
        var c = Groupe.Cumuler(moi, Array.Empty<Profil>(), groupe);
        Assert.Equal(45 * H, c.Secondes["code"]);
        Assert.Equal(7 * H, c.Secondes["tableur"]);
        Assert.Equal(H, c.Secondes["musique"]);
        Assert.Equal(30, c.Clavier);
        Assert.Equal(900, c.Defense.Meilleur); // record : le maximum
        Assert.Equal(3, c.Defense.Boss);       // boss vaincus : la somme
        // Codeur : Apprenti (6 h) avec 20 h seul, Compagnon (30 h) avec le groupe.
        Assert.Equal(1, Metiers.Niveaux(moi.Activites)["codeur"]);
        Assert.Equal(2, Metiers.Niveaux(c.Secondes)["codeur"]);
        // Succès franchis à plusieurs : 30 frappes avec Pilou ≥ 25.
        var stats = Groupe.StatsGroupe(c, 0, 0, DateTime.Now, "code");
        Assert.Contains(Succes.Nouveaux(stats, moi.Succes), d => d.Id == "dactylo");
    }

    [Fact]
    public void Maximum_par_appareil_doublons_et_ordre_indifferents()
    {
        var messages = new[]
        {
            C("tagg-1", "TAGG", 1, new() { ["code"] = 5 * H }, succes: new[] { "marathon" }),
            C("tagg-1", "TAGG", 3, new() { ["code"] = 9 * H, ["mail"] = H }, clavier: 4),
            C("tagg-1", "TAGG", 2, new() { ["code"] = 7 * H, ["mail"] = 2 * H }),
            C("salon-2", "SALON", 1, new() { ["jeu"] = 3 * H }, succes: new[] { "gamer" }),
        };
        var m1 = new Groupe.Memoire();
        foreach (var c in messages) m1.Fusionner(Relu(c), "moi");
        var m2 = new Groupe.Memoire();
        foreach (var c in messages.Reverse().Concat(messages)) m2.Fusionner(Relu(c), "moi");
        var moi = new Profil { Machine = "MOI", Activites = new() { ["code"] = H } };
        var c1 = Groupe.Cumuler(moi, Array.Empty<Profil>(), m1.Compteurs);
        var c2 = Groupe.Cumuler(moi, Array.Empty<Profil>(), m2.Compteurs);
        Assert.Equal(c1.Secondes.OrderBy(x => x.Key), c2.Secondes.OrderBy(x => x.Key));
        Assert.Equal(10 * H, c1.Secondes["code"]);  // 1 h ici + 9 h (le plus grand vu de TAGG), pas 5 + 9 + 7
        Assert.Equal(2 * H, c1.Secondes["mail"]);   // maximum par activité, même s'il vient d'un message plus ancien
        Assert.Equal(4, c1.Clavier);
        Assert.Equal(new[] { "gamer", "marathon" }, c1.Succes.OrderBy(x => x));
        // Un message réentendu ne change rien.
        Assert.False(m1.Fusionner(Relu(messages[1]), "moi"));
        // Son propre compteur (renvoyé par le relais) est ignoré ; le même PC vu par le dossier et le relais compte une fois.
        Assert.False(m1.Fusionner(Relu(C("moi", "MOI", 9, new() { ["code"] = 99 * H })), "moi"));
        var dossier = new[] { new Profil { Machine = "TAGG", Activites = new() { ["code"] = 8 * H, ["mail"] = 3 * H } } };
        var c3 = Groupe.Cumuler(moi, dossier, m1.Compteurs);
        Assert.Equal(10 * H, c3.Secondes["code"]);
        Assert.Equal(3 * H, c3.Secondes["mail"]);
    }

    [Fact]
    public void Un_succes_n_est_credite_qu_une_fois_dans_le_groupe()
    {
        // TAGG a franchi « Gamer » et l'a crédité ; RTX le reçoit : il l'ajoute sans XP, et ne le redébloque pas.
        var rtx = new Profil { Machine = "RTX", Activites = new() { ["jeu"] = 25 * H } };
        var groupe = new[] { Relu(C("tagg-1", "TAGG", 1, new() { ["jeu"] = 2 * H }, succes: new[] { "gamer" })) };
        var c = Groupe.Cumuler(rtx, Array.Empty<Profil>(), groupe);
        Assert.Equal(new[] { "gamer" }, Groupe.UnirSucces(rtx, c));
        Assert.Contains("gamer", rtx.Succes);
        Assert.DoesNotContain(Succes.Nouveaux(Groupe.StatsGroupe(c, 0, 0, DateTime.Now, "jeu"), rtx.Succes), d => d.Id == "gamer");
        Assert.Empty(Groupe.UnirSucces(rtx, c)); // deux fois : rien de plus
        // Et RTX le republie : l'union reste la même partout.
        Assert.Contains("gamer", Relu(Groupe.Moi(rtx, "rtx-1", "Pilou")).Succes);
    }

    [Fact]
    public void Un_grade_est_paye_une_fois_et_annonce_discretement_ailleurs()
    {
        var niveaux = new Dictionary<string, int>(Metiers.Tous.ToDictionary(m => m.Id, _ => 0)) { ["codeur"] = 2 };
        // RTX franchit Compagnon le premier : 10 × 1 + 10 × 2 xp (Apprenti n'avait jamais été payé).
        var payesRtx = new Dictionary<string, int>();
        var m = Metiers.Monter(niveaux, new Dictionary<string, int> { ["codeur"] = 0 }, payesRtx, Array.Empty<IReadOnlyDictionary<string, int>>());
        var x = Assert.Single(m);
        Assert.Equal(("codeur", 2, 30, false), (x.Metier.Id, x.Niveau, x.Xp, x.Discret));
        Assert.Equal(2, payesRtx["codeur"]);
        // TAGG reçoit les heures et les grades payés de RTX : petite annonce, sans XP.
        var payesTagg = new Dictionary<string, int> { ["codeur"] = 1 };
        m = Metiers.Monter(niveaux, new Dictionary<string, int> { ["codeur"] = 1 }, payesTagg, new[] { Relu(Groupe.Moi(new Profil { MetiersPayes = payesRtx }, "rtx", "")).Payes });
        x = Assert.Single(m);
        Assert.True(x.Discret);
        Assert.Equal(0, x.Xp);
        Assert.Equal(2, payesTagg["codeur"]);
        // Plus rien ensuite (ni au calcul suivant, ni au premier calcul après un redémarrage).
        Assert.Empty(Metiers.Monter(niveaux, niveaux, payesTagg, Array.Empty<IReadOnlyDictionary<string, int>>()));
        Assert.Empty(Metiers.Monter(niveaux, null, payesTagg, Array.Empty<IReadOnlyDictionary<string, int>>()));
    }

    [Fact]
    public void Un_ancien_PC_du_groupe_ne_casse_rien()
    {
        // Message d'une version précédente : ni « act », ni « suc », ni « cpt ».
        var ancien = Groupe.Lire("""{"v":1,"appareil":"vieux-1","nom":"Pilou","machine":"VIEUX","xp":40,"xpTel":0,"t":5,"prises":[],"plats":[]}""")!;
        Assert.Empty(ancien.Temps);
        Assert.Empty(ancien.Succes);
        Assert.Empty(ancien.Payes);
        var m = new Groupe.Memoire();
        m.Fusionner(Relu(C("vieux-1", "VIEUX", 1, new() { ["code"] = 3 * H }, succes: new[] { "marathon" })), "moi");
        // Le même appareil revient d'une ancienne version : ce qu'on savait de lui reste.
        m.Fusionner(ancien, "moi");
        var t = Assert.Single(m.Compteurs);
        Assert.Equal(3 * H, t.Temps["code"]);
        Assert.Equal(new[] { "marathon" }, t.Succes);
        Assert.Equal(40, t.Xp);
        // Mémoire de groupe écrite par une version précédente (groupe.json sans ces champs) : relue sans erreur.
        var memoire = JsonSerializer.Deserialize<Groupe.Memoire>("""{"Autres":{"x":{"Appareil":"x","Nom":"","Machine":"X","Xp":3,"XpTelephone":0,"T":1,"Prises":[],"Plats":[]}}}""")!;
        Assert.Empty(memoire.Compteurs.Single().Temps);
        // Et la mémoire d'aujourd'hui se relit avec les métiers (groupe.json).
        var relue = JsonSerializer.Deserialize<Groupe.Memoire>(JsonSerializer.Serialize(m))!;
        Assert.Equal(3 * H, relue.Compteurs.Single().Temps["code"]);
        Assert.Equal(new[] { "marathon" }, relue.Compteurs.Single().Succes);
        // Et ce que publie ce PC, un ancien PC le lit comme avant (champs en plus, ignorés) : les mêmes clés qu'hier y sont.
        using var doc = JsonDocument.Parse(Groupe.Json(C("a", "A", 1, new() { ["code"] = 90 })));
        foreach (var cle in new[] { "appareil", "xp", "xpTel", "prises", "plats", "po", "objets", "equipe", "soins", "exp" })
            Assert.True(doc.RootElement.TryGetProperty(cle, out _), cle);
        Assert.Equal(1, doc.RootElement.GetProperty("act").GetProperty("code").GetInt32()); // en minutes
    }

    [Fact]
    public void Valeurs_bornees_a_la_lecture()
    {
        var c = Groupe.Lire("""{"appareil":"x","act":{"code":999999999,"inconnue":5,"jeu":-3},"suc":["gamer","pas-un-succes"],"mp":{"codeur":99,"x":1},"cpt":[5,"a",-2]}""")!;
        Assert.Equal(366L * 24 * 3600, c.Temps["code"]);
        Assert.False(c.Temps.ContainsKey("inconnue"));
        Assert.False(c.Temps.ContainsKey("jeu"));
        Assert.Equal(new[] { "gamer" }, c.Succes);
        Assert.Equal(Metiers.Grades.Length - 1, c.Payes["codeur"]);
        Assert.Equal((5, 0, 0), (c.Clavier, c.Captures, c.Presentations));
    }

    [Fact]
    public void Le_message_de_groupe_reste_petit()
    {
        // Gros profil : tout pêché, tout cuisiné, un quart de la boutique, douze soins récents, toutes les activités,
        // tous les succès, des grades payés partout.
        var p = new Profil
        {
            Machine = "RTX4070TI-MAISON",
            Carnet = Butin.Prises.ToDictionary(x => x.Id, _ => 3),
            Plats = Butin.Recettes.Select(r => r.Id).ToList(),
            Activites = Activites.Toutes.Where(a => a != "nuit").ToDictionary(a => a, _ => 1234L * H + 59),
            Succes = Succes.Tous.Select(d => d.Id).ToList(),
            MetiersPayes = Metiers.Tous.ToDictionary(m => m.Id, _ => 6),
            SeancesClavier = 1234, Captures = 56, Presentations = 78, Defense = { Meilleur = 123_456, MeilleureVague = 42, Boss = 17 },
        };
        p.Bourse.Inventaire.AddRange(Boutique.Catalogue.Where((_, i) => i % 4 == 0).Select(a => a.Id));
        p.Soins.Base = new EtatSoins();
        for (int i = 0; i < 12; i++) Soins.Ajouter(p.Soins, new ActionSoin($"a{i:0000000000}", "nourrir", 1.79e12 + i * 1000, "croquettes"));
        var moi = Groupe.Moi(p, "RTX4070TI-MAISON-a1b2", "Pilou");
        var avant = moi with
        {
            Secondes = null, SuccesObtenus = null, MetiersPayes = null, Clavier = 0, Captures = 0, Presentations = 0, DefRecord = 0, DefVague = 0, DefBoss = 0,
        };
        string json = Groupe.Json(moi), jsonAvant = Groupe.Json(avant);
        int chiffre = Telephone.Chiffrer(Code, json).Length, chiffreAvant = Telephone.Chiffrer(Code, jsonAvant).Length;
        sortie.WriteLine($"message de groupe : {chiffreAvant} → {chiffre} octets chiffrés (limite {Telephone.TailleMax})");
        Assert.True(chiffre < Telephone.TailleMax, $"{chiffre}");
        Assert.True(json.Length <= Groupe.TailleJson, $"{json.Length}");
        Assert.InRange(chiffre - chiffreAvant, 1, 900); // ≈ 770 octets pour un profil complet
        // Les soins récents tiennent toujours en entier.
        Assert.Equal(12, Groupe.Lire(json)!.Actions.Count);
        Assert.Equal(1234L * H, Groupe.Lire(json)!.Temps["code"]); // à la minute près
    }
}
