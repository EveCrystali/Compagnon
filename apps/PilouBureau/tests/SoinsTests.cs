using System.Text.Json;
using PilouBureau;
using Xunit;

public class SoinsTests
{
    private const double H = 3600_000;
    private const double T0 = 1_789_999_200_000; // une heure ronde

    private static ActionSoin A(string id, string type, double heures, string objet = "") => new(id, type, T0 + heures * H, objet);

    // Vecteur partagé avec android/app/src/test/java/fr/pilou/compagnon/SoinsTest.java : si l'un change, l'autre aussi.
    public static readonly ActionSoin[] Vecteur =
    {
        A("a1", "nourrir", 10, "gateau"),
        A("a2", "rythme", 12, "exigeant"),
        A("a3", "laver", 20),
        A("a4", "vacances", 24, "1"),
        A("a5", "vacances", 48, "0"),
        A("a6", "caresse", 50),
    };

    [Fact]
    public void Vecteur_commun_avec_Android()
    {
        var e = Soins.Calculer(Soins.Neuf(T0), Vecteur, T0 + 54 * H);
        // faim : pleine à 10 h, puis 2 h normales, 12 h et 6 h exigeantes (×1,6), vacances entre les deux.
        Assert.Equal(100 - (2 + 12 * 1.6 + 6 * 1.6) * 100 / 36, e.Faim, 6);
        Assert.Equal(100 - (4 * 1.6 + 6 * 1.6) * 100 / 48, e.Proprete, 6);
        Assert.Equal(0, e.Moral, 6);
        Assert.Equal("exigeant", e.Rythme);
        Assert.False(e.Vacances);
        Assert.Equal(T0 + 54 * H, e.T);
        Assert.Equal(73.792665, Math.Round(e.Score, 6));
    }

    [Fact]
    public void Decroissance_lente_et_rythmes()
    {
        var e = Soins.Calculer(Soins.Neuf(T0), Array.Empty<ActionSoin>(), T0 + 18 * H);
        Assert.Equal(50, e.Faim, 6);
        Assert.Equal(62.5, e.Proprete, 6);
        Assert.Equal(40, e.Moral, 6);
        Assert.Equal(0, Soins.Calculer(Soins.Neuf(T0), Array.Empty<ActionSoin>(), T0 + 36 * H).Faim, 6);
        var doux = Soins.Calculer(Soins.Neuf(T0), new[] { A("r", "rythme", 0, "doux") }, T0 + 18 * H);
        Assert.Equal(70, doux.Faim, 6);
        Assert.Empty(Soins.Manques(Soins.Calculer(Soins.Neuf(T0), Array.Empty<ActionSoin>(), T0 + 6 * H)));
    }

    [Fact]
    public void Vacances_figent_tout()
    {
        var e = Soins.Calculer(Soins.Neuf(T0), new[] { A("v", "vacances", 1, "1") }, T0 + 500 * H);
        Assert.True(e.Vacances);
        Assert.Equal(100 - 100 / 36.0, e.Faim, 6);
        Assert.False(Soins.Terne(e));
        Assert.False(Soins.Rayonnant(e));
    }

    [Fact]
    public void Un_clic_comble_et_soin_comble_tout()
    {
        var b = new EtatSoins { Faim = 8, Proprete = 20, Moral = 5, T = T0 };
        Assert.Equal(new[] { Soins.Moral, Soins.Faim, Soins.Proprete }, Soins.Manques(b));
        Assert.True(Soins.Terne(b));
        var nourri = Soins.Calculer(b, new[] { A("n", "nourrir", 0, "gateau") }, T0);
        Assert.Equal((100.0, 20.0), (nourri.Faim, nourri.Moral));
        var tout = Soins.Calculer(b, new[] { A("s", "soin", 0) }, T0);
        Assert.Equal((100.0, 100.0, 100.0), (tout.Faim, tout.Proprete, tout.Moral));
        Assert.True(Soins.Rayonnant(tout));
        Assert.Equal(12, Soins.Bonus(10, tout));
        Assert.Equal(10, Soins.Bonus(10, b));
        Assert.Equal(15, Soins.BonusEnCas("plat-soupe"));
        Assert.Equal(0, Soins.BonusEnCas("croquettes"));
    }

    [Fact]
    public void Deux_appareils_convergent_quel_que_soit_l_ordre()
    {
        CarnetSoins Carnet(string origine) => new() { Base = Soins.Neuf(T0), Origine = origine };
        var pc = Carnet("pc-b");
        var portable = Carnet("pc-a");
        Soins.Ajouter(pc, A("x1", "nourrir", 5));
        Soins.Ajouter(pc, A("x2", "laver", 9));
        Soins.Ajouter(portable, A("y1", "calin", 7));

        Assert.True(Soins.Fusionner(pc, portable.Base, portable.Origine, portable.Actions));
        Assert.True(Soins.Fusionner(portable, pc.Base, pc.Origine, pc.Actions));
        Assert.False(Soins.Fusionner(portable, pc.Base, pc.Origine, pc.Actions)); // relu : rien
        Assert.Equal("pc-a", pc.Origine); // la plus petite origine l'emporte partout
        var a = Soins.Etat(pc, T0 + 20 * H);
        var b = Soins.Etat(portable, T0 + 20 * H);
        Assert.Equal((a.Faim, a.Proprete, a.Moral, a.Score), (b.Faim, b.Proprete, b.Moral, b.Score));
    }

    [Fact]
    public void Repli_ne_change_pas_l_etat_et_ignore_les_doublons()
    {
        var c = new CarnetSoins { Base = Soins.Neuf(T0), Origine = "pc" };
        Soins.Ajouter(c, A("p1", "nourrir", 3, "pomme"));
        Soins.Ajouter(c, A("p2", "caresse", 70));
        var avant = Soins.Etat(c, T0 + 80 * H);
        Soins.Plier(c, T0 + 80 * H + 1234);
        Assert.Single(c.Actions);
        Assert.Equal(T0 + 32 * H, c.Base!.T);
        var apres = Soins.Etat(c, T0 + 80 * H);
        Assert.Equal(avant.Faim, apres.Faim, 9);
        Assert.Equal(avant.Score, apres.Score, 9);
        Assert.False(Soins.Ajouter(c, A("p1", "nourrir", 3, "pomme"))); // déjà replié
        Assert.False(Soins.Fusionner(c, null, "", new[] { A("vieux", "soin", 1) })); // antérieur à la base
    }

    [Fact]
    public void Variantes_selon_les_soins()
    {
        Assert.Equal("calin", Soins.Variante(75));
        Assert.Equal("espiegle", Soins.Variante(40));
        var f = Groupe.FusionVariantes(new IReadOnlyDictionary<int, string>[]
            { new Dictionary<int, string> { [2] = "espiegle" }, new Dictionary<int, string> { [2] = "calin", [3] = "calin" } });
        Assert.Equal("calin", f[2]);
        Assert.Equal(2, f.Count);
        // Négligé longtemps, le score baisse (la variante sera espiègle) ; bien soigné, il reste haut.
        var neglige = Soins.Calculer(Soins.Neuf(T0), Array.Empty<ActionSoin>(), T0 + 6 * 24 * H);
        Assert.True(neglige.Score < 60);
        var soigne = Soins.Calculer(Soins.Neuf(T0), Enumerable.Range(0, 12).Select(i => A("s" + i, "soin", i * 12)), T0 + 6 * 24 * H);
        Assert.True(soigne.Score >= 60);
    }

    [Fact]
    public void Message_du_groupe_porte_les_soins_et_reste_court()
    {
        var p = new Profil();
        p.Soins = new CarnetSoins { Base = Soins.Neuf(T0), Origine = "pc" };
        for (int i = 0; i < 200; i++) Soins.Ajouter(p.Soins, Soins.Action("nourrir", T0 + i * 60_000, "gateau"));
        p.Evolution.Variantes[2] = "calin";
        var json = Groupe.Json(Groupe.Moi(p, "pc", "Perso"));
        Assert.True(json.Length <= 2600, $"{json.Length}");
        var lu = Groupe.Lire(json)!;
        Assert.Equal("pc", lu.SoinsOrigine);
        Assert.Equal(T0, lu.SoinsBase!.T);
        Assert.NotEmpty(lu.Actions);
        Assert.Equal("calin", lu.Formes[2]);
    }

    [Fact]
    public void Soins_faits_sur_le_telephone()
    {
        var p = new Profil();
        p.Soins = new CarnetSoins { Base = Soins.Neuf(T0), Origine = "pc" };
        var g = Telephone.LireGain($$"""{"id":"g9","soins":[["t1","nourrir",{{T0 + H}},"pomme"],["t2","inconnu",1],["t3","calin",{{T0 + 2 * H}}]],"t":5}""")!;
        Assert.Equal(2, g.Soins!.Count);
        var local = new DateTime(2026, 11, 25, 12, 0, 0);
        Telephone.Recevoir(p, g, new Telephone.Contexte(local, "pc", 5, 500));
        Assert.Equal(2, p.Soins.Actions.Count);
        Telephone.Recevoir(p, g with { Id = "g10" }, new Telephone.Contexte(local, "pc", 5, 500));
        Assert.Equal(2, p.Soins.Actions.Count); // mêmes identifiants : rien de neuf

        var etat = Soins.LireEtat(JsonDocument.Parse(JsonSerializer.Serialize(Soins.JsonEtat(Soins.Etat(p.Soins, T0 + 3 * H)))).RootElement)!;
        Assert.Equal(100 - 100 / 36.0 * 2, etat.Faim, 2);
    }
}
