using PilouBureau;
using Xunit;
using Xunit.Abstractions;

public class GroupeTests(ITestOutputHelper sortie)
{
    private const string Code = "ABCD-EFGH-JKMN-PQRS";

    private static Groupe.Compteur C(string appareil, string machine, int xp, double t, int tel = 0, string[]? prises = null) =>
        new(appareil, machine, machine, xp, tel, t, prises ?? Array.Empty<string>(), Array.Empty<string>());

    [Fact]
    public void Sujet_du_groupe_commun_avec_Android()
    {
        // Même vecteur que android/app/src/test/java/fr/pilou/compagnon/GroupeTest.java.
        sortie.WriteLine(Groupe.Sujet(Code));
        Assert.Equal(Groupe.Sujet(Code), Groupe.Sujet("abcd efgh jkmn pqrs"));
        Assert.NotEqual(Telephone.Sujet(Code), Groupe.Sujet(Code));
        Assert.NotEqual(Telephone.SujetRetour(Code), Groupe.Sujet(Code));
        Assert.Equal("pilou-4404248bb27fbeba24ba6972", Groupe.Sujet(Code));
    }

    [Fact]
    public void Fusion_garde_le_maximum_par_appareil_et_ignore_le_sien()
    {
        var m = new Groupe.Memoire();
        Assert.True(m.Fusionner(C("tagg-1a2b", "TAGG", 300, 10), "perso-9f9f"));
        Assert.True(m.Fusionner(C("tagg-1a2b", "TAGG", 420, 20, prises: new[] { "goujon" }), "perso-9f9f"));
        // Un vieux message arrivé en retard ne fait pas reculer le compteur.
        Assert.False(m.Fusionner(C("tagg-1a2b", "TAGG", 300, 10), "perso-9f9f"));
        Assert.False(m.Fusionner(C("perso-9f9f", "PERSO", 9999, 30), "perso-9f9f"));
        var t = Assert.Single(m.Compteurs);
        Assert.Equal(420, t.Xp);
        Assert.Equal(new[] { "goujon" }, t.Prises);
    }

    [Fact]
    public void Fusion_idempotente_et_insensible_a_l_ordre()
    {
        var messages = new[] { C("a", "A", 5, 1), C("a", "A", 50, 3), C("b", "B", 7, 2), C("a", "A", 20, 2) };
        var m1 = new Groupe.Memoire();
        foreach (var c in messages) m1.Fusionner(c, "moi");
        var m2 = new Groupe.Memoire();
        foreach (var c in messages.Reverse().Concat(messages)) m2.Fusionner(c, "moi");
        var moi = new Profil { Machine = "MOI", Xp = 100 };
        Assert.Equal(Groupe.Total(moi, Array.Empty<Profil>(), m1.Compteurs), Groupe.Total(moi, Array.Empty<Profil>(), m2.Compteurs));
        Assert.Equal(157, Groupe.Total(moi, Array.Empty<Profil>(), m1.Compteurs));
    }

    [Fact]
    public void Un_PC_vu_par_le_dossier_et_par_le_relais_compte_une_fois()
    {
        var moi = new Profil { Machine = "PERSO", Xp = 1000 };
        var dossier = new[] { new Profil { Machine = "SALON", Xp = 200 } };
        var groupe = new[] { C("salon-aaaa", "SALON", 250, 5), C("tagg-bbbb", "TAGG", 300, 5), C("perso-cccc", "PERSO", 1, 5) };
        // SALON : max(200, 250) ; TAGG : 300 ; PERSO (moi) ignoré côté relais.
        Assert.Equal(1000 + 250 + 300, Groupe.Total(moi, dossier, groupe));
    }

    [Fact]
    public void Les_gains_du_telephone_comptent_au_maximum_pas_en_somme()
    {
        // Les deux PC ont crédité les mêmes gains du téléphone (même sujet retour) : 40 xp, pas 80.
        var moi = new Profil { Machine = "PERSO", Xp = 100, XpTelephone = 40 };
        var groupe = new[] { C("tagg", "TAGG", 300, 5, tel: 40) };
        Assert.Equal(100 + 300 + 40, Groupe.Total(moi, Array.Empty<Profil>(), groupe));
        // Le PC de bureau a vu un gain de plus (le perso était éteint plus de 12 h) : on prend le plus grand.
        groupe = new[] { C("tagg", "TAGG", 300, 5, tel: 55) };
        Assert.Equal(100 + 300 + 55, Groupe.Total(moi, Array.Empty<Profil>(), groupe));
    }

    [Fact]
    public void Message_chiffre_aller_retour()
    {
        var c = C("tagg-1a2b", "TAGG", 321, 1_800_000_000_000, tel: 4, prises: new[] { "goujon", "perle" });
        var ligne = "{\"id\":\"m1\",\"event\":\"message\",\"message\":\"" + Telephone.Chiffrer(Code, Groupe.Json(c)) + "\"}\n"
                    + "{\"id\":\"k\",\"event\":\"keepalive\"}\n"
                    + "{\"id\":\"m2\",\"event\":\"message\",\"message\":\"" + Telephone.Chiffrer("ZZZZ-ZZZZ-ZZZZ-ZZZZ", Groupe.Json(c)) + "\"}";
        var (liste, dernier) = Groupe.LireMessages(Code, ligne);
        var lu = Assert.Single(liste); // celui d'un autre groupe est ignoré
        Assert.Equal("m2", dernier);
        Assert.Equal(321, lu.Xp);
        Assert.Equal(4, lu.XpTelephone);
        Assert.Equal(new[] { "goujon", "perle" }, lu.Prises);
        Assert.Null(Groupe.Lire("""{"xp":5}"""));
    }

    [Fact]
    public void Migration_le_code_du_telephone_devient_celui_du_groupe()
    {
        // Un PC déjà appairé (PR #6) garde son code : il est valide comme code de groupe, sans rien changer.
        var r = new Reglages { Telephone = Code };
        Assert.True(Telephone.Valide(r.Telephone));
        Assert.Equal("pilou-", Groupe.Sujet(r.Telephone)[..6]);
    }

    [Fact]
    public void Memoire_sur_disque()
    {
        var d = Path.Combine(Path.GetTempPath(), "pilou-groupe-" + Guid.NewGuid().ToString("N"));
        try
        {
            var m = new Groupe.Memoire { Depuis = "abc" };
            m.Fusionner(C("tagg", "TAGG", 12, 3, prises: new[] { "goujon" }), "moi");
            m.Ecrire(d);
            var relu = Groupe.Memoire.Lire(d);
            Assert.Equal("abc", relu.Depuis);
            Assert.Equal(12, Assert.Single(relu.Compteurs).Xp);
        }
        finally
        {
            if (Directory.Exists(d)) Directory.Delete(d, true);
        }
    }
}
