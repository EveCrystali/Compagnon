using System.Text.Json;
using PilouBureau;
using Xunit;

// Canal retour : ce que le téléphone gagne dans l'atelier, crédité par le PC une seule fois.
public class RetourTests
{
    private const string Code = "ABCD-EFGH-JKMN-PQRS";

    // Produit par Chiffre.chiffrer (Java, android/) avec le nonce 0b 0a … 00 : le PC doit le relire.
    private const string ChiffreJava =
        "CwoJCAcGBQQDAgEAvHMcyNTTLMvvDj8R7ZMt3bH28CF4obx9dta8COWrOYM1NQ7ri8HsUENAELS04KyjJeltNiwaqSNgKQcAhKlOcorrxqvHN4+qrUPC/C01dhzJpg7S1QnAh0o84kghFMQt9EoIfFhpxjk=";

    [Fact]
    public void Sujet_retour_commun_avec_Android()
    {
        Assert.Equal("pilou-7f73fb3174ad7b3e4ba8e683", Telephone.SujetRetour(Code));
        Assert.NotEqual(Telephone.Sujet(Code), Telephone.SujetRetour(Code));
    }

    [Fact]
    public void Le_PC_relit_un_gain_chiffre_par_le_telephone()
    {
        var g = Telephone.LireGain(Telephone.Dechiffrer(Code, ChiffreJava))!;
        Assert.Equal("abc123def456", g.Id);
        Assert.Equal(7, g.Xp);
        Assert.Equal(1, g.Prises["goujon"]);
        Assert.Equal(new[] { "grille" }, g.Plats);
        Assert.Equal(2, g.Caresses);
    }

    [Fact]
    public void Un_gain_n_est_credite_qu_une_fois()
    {
        var p = new Profil { Xp = 100 };
        var g = new Telephone.Gain("g1", 12, new Dictionary<string, int> { ["goujon"] = 2 }, new[] { "grille", "inv:Soupe de goujon bleu du lundi" }, 3);
        Assert.Equal(12, Telephone.Crediter(p, g));
        Assert.Equal(0, Telephone.Crediter(p, g));
        Assert.Equal(112, p.Xp);
        Assert.Equal(2, p.Carnet["goujon"]);
        Assert.Equal(3, p.Caresses);
        Assert.Equal(2, p.PlatsCuisines);
        Assert.Contains("grille", p.Plats);
        Assert.Equal(new[] { "g1" }, p.Recus);
    }

    [Fact]
    public void Gains_bornes_et_prises_inconnues_ignorees()
    {
        var g = Telephone.LireGain("""{"id":"x","xp":999999,"prises":{"goujon":3,"licorne":1},"caresses":-4}""")!;
        Assert.Equal(2000, g.Xp);
        Assert.Equal(0, g.Caresses);
        Assert.Single(g.Prises);
        Assert.Null(Telephone.LireGain("""{"xp":5}"""));
    }

    [Fact]
    public void Reponse_ntfy_lue_ligne_par_ligne()
    {
        var ok = Telephone.Chiffrer(Code, """{"id":"g2","xp":5}""");
        var autre = Telephone.Chiffrer("ZZZZ-ZZZZ-ZZZZ-ZZZZ", """{"id":"g3","xp":5}""");
        var texte = string.Join("\n",
            """{"id":"m1","event":"message","message":"%s"}""".Replace("%s", ok),
            """{"id":"m2","event":"message","message":"%s"}""".Replace("%s", autre),
            """{"id":"k","event":"keepalive"}""",
            "pas du json");
        var (gains, dernier) = Telephone.LireRetours(Code, texte);
        Assert.Equal("g2", Assert.Single(gains).Id);
        Assert.Equal("m2", dernier);
    }

    [Fact]
    public void L_etat_publie_porte_la_progression()
    {
        var p = new Profil { Carnet = { ["goujon"] = 1 }, Plats = { "grille", "inv:Galette d'algue frisée du matin" }, Recus = { "g1" } };
        var json = Telephone.Charge(new List<Telephone.SessionTel>(), 1, "Pilou", 4, "Apprenti", "bleu", "repos", 0,
            Telephone.Progression(p, 80, "lunettes"));
        using var d = JsonDocument.Parse(json);
        var r = d.RootElement;
        Assert.Equal(80, r.GetProperty("xp").GetInt32());
        Assert.Equal("lunettes", r.GetProperty("accessoire").GetString());
        Assert.Equal("goujon", r.GetProperty("carnet")[0].GetString());
        Assert.Equal(1, r.GetProperty("plats").GetArrayLength());
        Assert.Equal(1, r.GetProperty("inventes").GetInt32());
        Assert.Equal("g1", r.GetProperty("recus")[0].GetString());
        // Une fois chiffré, l'état reste sous la limite d'un message ntfy (4 096 octets).
        Assert.True(Telephone.Chiffrer(Code, json).Length < 4096);
    }
}
