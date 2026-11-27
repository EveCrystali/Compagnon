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
        A("a2", "rythme", 12, "exigeant"), // ancien réglage de difficulté : ignoré
        A("a3", "laver", 20),
        A("a4", "vacances", 24, "1"),
        A("a5", "vacances", 48, "0"),
        A("a6", "caresse", 50),
    };

    [Fact]
    public void Vecteur_commun_avec_Android()
    {
        var e = Soins.Calculer(Soins.Neuf(T0), Vecteur, T0 + 54 * H);
        // Un seul rythme : faim pleine à 10 h, puis 14 h et 6 h (vacances entre les deux) ; le « rythme » est ignoré.
        Assert.Equal(100 - 20 * 100 / 36.0, e.Faim, 6);
        Assert.Equal(100 - 10 * 100 / 48.0, e.Proprete, 6);
        Assert.Equal(25, e.Moral, 6);
        Assert.False(e.Vacances);
        Assert.False(e.Boude);
        Assert.Equal(T0 + 54 * H, e.T);
        Assert.Equal(ScoreVecteur, Math.Round(e.Score, 6));
    }

    public const double ScoreVecteur = 76.861989;

    [Fact]
    public void Decroissance_lente_et_meme_rythme_pour_tous()
    {
        var e = Soins.Calculer(Soins.Neuf(T0), Array.Empty<ActionSoin>(), T0 + 18 * H);
        Assert.Equal(50, e.Faim, 6);
        Assert.Equal(62.5, e.Proprete, 6);
        Assert.Equal(40, e.Moral, 6);
        Assert.Equal(0, Soins.Calculer(Soins.Neuf(T0), Array.Empty<ActionSoin>(), T0 + 36 * H).Faim, 6);
        // Un ancien journal avec « rythme doux » ou « exigeant » : même état, sans erreur.
        foreach (var r in new[] { "doux", "exigeant", "n'importe quoi" })
            Assert.Equal(50, Soins.Calculer(Soins.Neuf(T0), new[] { A("r", "rythme", 0, r) }, T0 + 18 * H).Faim, 6);
        Assert.Empty(Soins.Manques(Soins.Calculer(Soins.Neuf(T0), Array.Empty<ActionSoin>(), T0 + 6 * H)));
    }

    [Fact]
    public void Vacances_figent_tout()
    {
        var e = Soins.Calculer(Soins.Neuf(T0), new[] { A("v", "vacances", 1, "1") }, T0 + 500 * H);
        Assert.True(e.Vacances);
        Assert.Equal(100 - 100 / 36.0, e.Faim, 6);
        Assert.False(Soins.Boudeur(e));
        Assert.False(Soins.Rayonnant(e));
        Assert.Equal(1, Soins.Multiplicateur(e));
    }

    [Fact]
    public void Un_clic_comble_et_soin_comble_tout()
    {
        var b = new EtatSoins { Faim = 8, Proprete = 20, Moral = 5, T = T0 };
        Assert.Equal(new[] { Soins.Moral, Soins.Faim, Soins.Proprete }, Soins.Manques(b));
        var nourri = Soins.Calculer(b, new[] { A("n", "nourrir", 0, "gateau") }, T0);
        Assert.Equal((100.0, 20.0), (nourri.Faim, nourri.Moral));
        var tout = Soins.Calculer(b, new[] { A("s", "soin", 0) }, T0);
        Assert.Equal((100.0, 100.0, 100.0), (tout.Faim, tout.Proprete, tout.Moral));
        Assert.True(Soins.Rayonnant(tout));
        Assert.Equal(12, Soins.Bonus(10, tout));
        Assert.Equal(10, Soins.Bonus(10, b)); // besoins bas, mais il ne boude pas encore
        Assert.Equal(15, Soins.BonusEnCas("plat-soupe"));
        Assert.Equal(0, Soins.BonusEnCas("croquettes"));
    }

    // Bouderie (mêmes cas dans SoinsTest.java) : deux besoins sous 20 %, il boude aussitôt.
    [Fact]
    public void Deux_besoins_bas_il_boude_puis_se_laisse_amadouer()
    {
        var neuf = Soins.Neuf(T0);
        var a28 = Soins.Calculer(neuf, Array.Empty<ActionSoin>(), T0 + 28 * H);
        Assert.False(Soins.Boudeur(a28)); // le moral seul est bas depuis 4 h
        var a29 = Soins.Calculer(neuf, Array.Empty<ActionSoin>(), T0 + 29 * H);
        Assert.True(Soins.Boudeur(a29)); // la faim passe sous 20 % aussi
        Assert.False(Soins.Amadoue(a29));
        Assert.Equal(0.6, Soins.Multiplicateur(a29));
        Assert.Equal(6, Soins.Bonus(10, a29));
        Assert.Equal(3, Soins.Bonus(5, a29));
        Assert.Equal(9, Soins.Bonus(15, a29));
        Assert.Equal(1, Soins.Bonus(1, a29)); // un gain rapporte toujours au moins 1
        Assert.Equal(0, Soins.Bonus(0, a29));

        // Une caresse ne suffit pas (le moral reste bas) ; le soin complet, si : 30 min de rancune.
        var caresse = Soins.Calculer(neuf, new[] { A("c", "caresse", 30) }, T0 + 30.5 * H);
        Assert.True(Soins.Boudeur(caresse));
        Assert.False(Soins.Amadoue(caresse));
        var soin = new[] { A("s", "soin", 31) };
        var amadoue = Soins.Calculer(neuf, soin, T0 + 31.25 * H);
        Assert.True(Soins.Boudeur(amadoue));
        Assert.True(Soins.Amadoue(amadoue));
        Assert.Equal(6, Soins.Bonus(10, amadoue)); // les gains restent réduits tant qu'il boude
        Assert.Equal(T0 + 31.5 * H, amadoue.FinBouderie);
        var reconcilie = Soins.Calculer(neuf, soin, T0 + 31.5 * H);
        Assert.False(Soins.Boudeur(reconcilie));
        Assert.True(Soins.Rayonnant(reconcilie));
        Assert.Equal(12, Soins.Bonus(10, reconcilie)); // rayonnant : × 1,2
        Assert.Equal(6, Soins.Bonus(5, reconcilie));
    }

    [Fact]
    public void Un_seul_besoin_bas_six_heures_et_il_boude()
    {
        var soins = new[] { A("n", "nourrir", 20), A("l", "laver", 20) };
        var avant = Soins.Calculer(Soins.Neuf(T0), soins, T0 + 29.5 * H); // moral sous 20 % depuis 24 h
        Assert.False(Soins.Boudeur(avant));
        Assert.Equal(1, Soins.Multiplicateur(avant));
        var apres = Soins.Calculer(Soins.Neuf(T0), soins, T0 + 30 * H);
        Assert.True(Soins.Boudeur(apres));
        // Un câlin à temps : le compteur de négligence repart de zéro.
        var calin = Soins.Calculer(Soins.Neuf(T0), soins.Append(A("c", "calin", 27)), T0 + 32 * H);
        Assert.False(Soins.Boudeur(calin));
        Assert.Equal(0, calin.Neglige);
    }

    [Fact]
    public void En_vacances_il_ne_boude_pas_et_la_bouderie_voyage()
    {
        var vacances = Soins.Calculer(Soins.Neuf(T0), new[] { A("v", "vacances", 0, "1") }, T0 + 100 * H);
        Assert.False(Soins.Boudeur(vacances));
        // L'état part au téléphone et aux autres PC tel quel (clés n, b, fb).
        var e = Soins.Calculer(Soins.Neuf(T0), new[] { A("s", "soin", 31) }, T0 + 31.25 * H);
        var lu = Soins.LireEtat(JsonDocument.Parse(JsonSerializer.Serialize(Soins.JsonEtat(e))).RootElement)!;
        Assert.True(lu.Boude);
        Assert.Equal(e.FinBouderie, lu.FinBouderie);
        Assert.True(Soins.Amadoue(lu));
        // Un ancien état avec « r » (rythme) se lit sans erreur.
        var ancien = Soins.LireEtat(JsonDocument.Parse("{\"f\":50,\"p\":60,\"m\":70,\"s\":80,\"t\":" + T0 + ",\"r\":\"exigeant\",\"v\":0}").RootElement)!;
        Assert.Equal(50, ancien.Faim);
        Assert.False(ancien.Boude);
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
        Assert.Equal((a.Boude, a.FinBouderie, a.Neglige), (b.Boude, b.FinBouderie, b.Neglige));
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
        Assert.True(json.Length <= Groupe.TailleJson, $"{json.Length}");
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
