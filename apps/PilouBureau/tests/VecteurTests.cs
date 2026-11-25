using PilouBureau;
using Xunit;
using Xunit.Abstractions;

public class TelephoneTests(ITestOutputHelper sortie)
{
    // Vecteur partagé avec android/app/src/test/java/fr/pilou/compagnon/ChiffreTest.java : si l'un change, l'autre aussi.
    public const string Code = "ABCD-EFGH-JKMN-PQRS";
    public const string Clair = "{\"v\":1,\"nom\":\"Pilou\"}";
    public static readonly byte[] Nonce = Enumerable.Range(0, 12).Select(i => (byte)i).ToArray();

    [Fact]
    public void Vecteur_commun_avec_Android()
    {
        var chiffre = Telephone.Chiffrer(Code, Clair, Nonce);
        sortie.WriteLine($"SUJET={Telephone.Sujet(Code)}");
        sortie.WriteLine($"CHIFFRE={chiffre}");
        Assert.Equal(Clair, Telephone.Dechiffrer("abcd efgh jkmn pqrs", chiffre));
        Assert.Equal("pilou-", Telephone.Sujet(Code)[..6]);
        Assert.Equal(30, Telephone.Sujet(Code).Length);
    }

    [Fact]
    public void Code_neuf_valide_et_sans_caracteres_ambigus()
    {
        var c = Telephone.NouveauCode();
        Assert.Matches("^[A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4}$", c);
        Assert.True(Telephone.Valide(c));
        Assert.DoesNotContain('O', c);
        Assert.DoesNotContain('I', c);
        Assert.False(Telephone.Valide("ABCD"));
    }

    [Fact]
    public void Message_altere_refuse()
    {
        var c = Telephone.Chiffrer(Code, Clair);
        var octets = Convert.FromBase64String(c);
        octets[15] ^= 1;
        Assert.ThrowsAny<System.Security.Cryptography.CryptographicException>(() =>
            Telephone.Dechiffrer(Code, Convert.ToBase64String(octets)));
    }

    [Fact]
    public void Sessions_triees_sans_les_calmes_et_signature_insensible_aux_outils()
    {
        const double T = 1_800_000_000_000;
        var travail = new EtatSession("a", T, "repos", 0, true, "Bash", 1, false, false, "Pilou", 1, true, "api", DebutTour: T - 5000);
        var attend = new EtatSession("b", T, "repos", 0, false, "", 0, false, false, "Pilou", 1, true, "site", Attente: "permission", DebutOutil: T - 1000);
        var calme = new EtatSession("c", T, "repos", 0, false, "", 0, false, false, "Pilou", 1, true, "vieux", FinTour: T - 5 * 3600_000);
        var s = Telephone.Sessions(new[] { travail, attend, calme }, T);
        Assert.Equal(new[] { "permission", "travail" }, s.Select(x => x.Etat));
        Assert.Equal("Bash", s[1].Outil);

        var s2 = Telephone.Sessions(new[] { travail with { Outil = "Read" }, attend, calme }, T);
        Assert.Equal(Telephone.Signature(s, 3, "repos"), Telephone.Signature(s2, 3, "repos"));
        Assert.Contains("\"etat\":\"permission\"", Telephone.Charge(s, T, "Pilou", 3, "Petit pixel", "bleu", "repos", 1));
    }

    [Fact]
    public void Lien_d_appairage()
    {
        Assert.Equal("pilou://appairer?c=ABCDEFGHJKMNPQRS", Telephone.Lien(Code, Telephone.RelaisParDefaut));
        Assert.Equal("pilou://appairer?c=ABCDEFGHJKMNPQRS&s=https%3A%2F%2Fntfy.exemple.fr", Telephone.Lien(Code, "https://ntfy.exemple.fr"));
    }
}
