using PilouBureau;
using PilouVisualStudio;
using Xunit;

// Extension Visual Studio (integrations/visualstudio/Rapport.cs, sans rien de VS) : document actif seul, nom
// seul, message optionnel, JSON accepté par Pilou, jeton lu dans reglages.json.
public class VisualStudioTests
{
    private const string Actif = @"C:\Travail\Projet\Program.cs";

    private static readonly LigneErreur[] Lignes =
    {
        new(Actif, Gravite.Erreur, @"CS0246: 'Foo' introuvable (C:\Travail\Projet\Foo.cs)", 12),
        new(@"c:\travail\projet\program.cs", Gravite.Erreur, "CS1002: ; attendu", 3), // casse différente : même fichier
        new(Actif, Gravite.Avertissement, "CS0168: variable déclarée mais jamais utilisée", 8),
        new(Actif, Gravite.Message, "IDE0051", 9),
        new(@"C:\Travail\Projet\Autre.cs", Gravite.Erreur, "ailleurs", 1),
        new("", Gravite.Erreur, "erreur de build sans fichier", 0),
    };

    [Fact]
    public void Seul_le_document_actif_compte()
    {
        var r = Rapport.Compter(Actif, Lignes, avecMessage: false);
        Assert.Equal(("Program.cs", 2, 1, ""), (r.Fichier, r.Erreurs, r.Avertissements, r.Message));
        Assert.DoesNotContain("Travail", r.Json());
    }

    [Fact]
    public void Premier_message_par_ligne_sans_chemin()
    {
        var r = Rapport.Compter(Actif, Lignes, avecMessage: true);
        Assert.Equal("CS1002: ; attendu", r.Message);
        var r2 = Rapport.Compter(Actif, Lignes.Where(l => l.Ligne != 3), true);
        Assert.Equal("CS0246: 'Foo' introuvable (Foo.cs)", r2.Message);
    }

    [Fact]
    public void Json_lu_par_pilou()
    {
        var r = Rapport.Compter(Actif, Lignes, true);
        var lu = RapportDiagnostics.Lire(r.Json(), 5, out var err)!;
        Assert.Equal("", err);
        Assert.Equal(("vs", "Program.cs", 2, 1, "CS1002: ; attendu"), (lu.Source, lu.Fichier, lu.Erreurs, lu.Avertissements, lu.Message));
        var f = RapportDiagnostics.Lire(Rapport.Fermeture().Json(), 5, out _)!;
        Assert.Equal("", f.Fichier);
        Assert.True(r.Meme(Rapport.Compter(Actif, Lignes, true)));
        Assert.False(r.Meme(Rapport.Compter(Actif, Lignes.Skip(1), true)));
    }

    [Fact]
    public void Jeton_et_port()
    {
        const string json = """{ "Bulle": 1, "Connecteurs": { "Api": true, "PortApi": 50001, "JetonApi": "0a1b2c" } }""";
        Rapport.LireAcces(json, "", 0, out var jeton, out var port);
        Assert.Equal(("0a1b2c", 50001), (jeton, port));
        Rapport.LireAcces(json, "perso", 4000, out jeton, out port);
        Assert.Equal(("perso", 4000), (jeton, port));
        Rapport.LireAcces("", "", 0, out jeton, out port);
        Assert.Equal(("", Rapport.PortParDefaut), (jeton, port));
    }
}
