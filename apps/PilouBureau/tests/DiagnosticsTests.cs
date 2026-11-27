using PilouBureau;
using Xunit;

// Erreurs du fichier actif (extensions Visual Studio / VS Code → POST /diagnostics) : lecture, chemin jamais
// gardé, regroupement, transitions vers zéro, repos, durée de vie, API.
public class DiagnosticsTests
{
    private static RapportDiagnostics R(string fichier, int e, int a, double t, string source = "vs", string message = "") =>
        new(source, fichier, e, a, message, t);

    // Fait avancer le suivi : un relevé à t, puis un battement après le regroupement.
    private static AnnonceDiagnostics? Apres(SuiviDiagnostics s, RapportDiagnostics r, bool saisie = false)
    {
        s.Recevoir(r);
        return s.Battre(r.T + SuiviDiagnostics.Regroupement, saisie);
    }

    [Fact]
    public void Lecture_et_nom_seul()
    {
        var r = RapportDiagnostics.Lire("""{"source":"vs","fichier":"C:\\Users\\antoine\\Travail\\Program.cs","erreurs":3,"avertissements":2}""", 10, out var err)!;
        Assert.Equal("", err);
        Assert.Equal(("vs", "Program.cs", 3, 2, 10.0), (r.Source, r.Fichier, r.Erreurs, r.Avertissements, r.T));
        Assert.Equal("app.ts", RapportDiagnostics.Lire("""{"source":"vscode","fichier":"/home/a/projet/src/app.ts"}""", 0, out _)!.Fichier);
        // Comptes absurdes bornés, manquants à zéro.
        var b = RapportDiagnostics.Lire("""{"source":"vs","fichier":"x.cs","erreurs":-4,"avertissements":1e9}""", 0, out _)!;
        Assert.Equal((0, 99_999), (b.Erreurs, b.Avertissements));
        Assert.Null(RapportDiagnostics.Lire("""{"fichier":"x.cs"}""", 0, out err));
        Assert.Contains("source", err);
        Assert.Null(RapportDiagnostics.Lire("pas du json", 0, out err));
        Assert.Null(RapportDiagnostics.Lire("[1]", 0, out _));
        // Fermé : plus de fichier actif.
        var f = RapportDiagnostics.Lire("""{"source":"vs","fichier":"x.cs","erreurs":2,"ferme":true}""", 0, out _)!;
        Assert.Equal(("", 0), (f.Fichier, f.Erreurs));
    }

    [Theory]
    [InlineData(@"CS0246: 'Foo' introuvable dans C:\Users\antoine\src\Projet\Foo.cs", "CS0246: 'Foo' introuvable dans Foo.cs")]
    [InlineData("Cannot find module '/home/antoine/projet/lib/util.ts'", "Cannot find module 'util.ts'")]
    [InlineData(@"voir \\serveur\partage\dossier\a.cs ligne 3", "voir a.cs ligne 3")]
    [InlineData("file:///c:/Users/a/x.ts manquant", "x.ts manquant")]
    [InlineData("ligne\nsuivante\t ici", "ligne suivante ici")]
    public void Le_chemin_ne_sort_jamais(string message, string attendu) =>
        Assert.Equal(attendu, RapportDiagnostics.Nettoyer(message, 200));

    [Fact]
    public void Message_tronque_et_desactive_par_defaut()
    {
        var s = new SuiviDiagnostics();
        var a = Apres(s, R("Program.cs", 1, 0, 0, message: new string('x', 300)))!;
        Assert.Equal("1 erreur · Program.cs", a.Texte);
        s.AvecMessage = true;
        a = Apres(s, R("Program.cs", 2, 0, 60_000, message: "CS1002: ; attendu " + new string('x', 300)))!;
        Assert.StartsWith("2 erreurs · Program.cs — CS1002: ; attendu", a.Texte);
        Assert.EndsWith("…", a.Texte);
        Assert.True(a.Texte.Length <= "2 erreurs · Program.cs — ".Length + SuiviDiagnostics.MaxMessageAffiche);
    }

    [Fact]
    public void Texte_signe_et_ton()
    {
        var s = new SuiviDiagnostics();
        var a = Apres(s, R("Program.cs", 3, 2, 0))!;
        Assert.Equal("⚠ 3 erreurs · 2 avert. · Program.cs", a.Ligne);
        Assert.Equal(TonDiagnostics.Erreurs, a.Ton);
        Assert.Equal(ReactionDiagnostics.Aucune, a.Reaction); // nouveau fichier : pas de grimace
        a = Apres(s, R("Autre.cs", 0, 4, 60_000))!;
        Assert.Equal("△ 4 avert. · Autre.cs", a.Ligne);
        Assert.Equal(TonDiagnostics.Avertissements, a.Ton);
        s.AvecNom = false;
        Assert.Equal("⚠ 1 erreur", Apres(s, R("Autre.cs", 1, 0, 120_000))!.Ligne);
    }

    [Fact]
    public void Regroupement_pas_de_bulle_a_chaque_frappe()
    {
        var s = new SuiviDiagnostics();
        s.Recevoir(R("a.cs", 1, 0, 0));
        Assert.Null(s.Battre(1000, false));
        s.Recevoir(R("a.cs", 2, 0, 1500));      // ça bouge encore : le compte repart
        Assert.Null(s.Battre(3000, false));
        s.Recevoir(R("a.cs", 3, 0, 2000));
        Assert.Null(s.Battre(4000, false));
        var a = s.Battre(4500, false)!;         // 2,5 s de calme : une seule bulle, le dernier état
        Assert.Equal("3 erreurs · a.cs", a.Texte);
        Assert.Null(s.Battre(5000, false));     // déjà dit
        // Le battement (mêmes comptes) ne relance rien.
        s.Recevoir(R("a.cs", 3, 0, 60_000));
        Assert.Null(s.Battre(70_000, false));
    }

    [Fact]
    public void Jamais_pendant_la_saisie()
    {
        var s = new SuiviDiagnostics();
        s.Recevoir(R("a.cs", 2, 0, 0));
        Assert.Null(s.Battre(5000, true));
        Assert.NotNull(s.Battre(6000, false));
    }

    [Fact]
    public void Grimace_quand_ca_augmente_saut_quand_propre()
    {
        var s = new SuiviDiagnostics();
        Apres(s, R("a.cs", 1, 0, 0));
        var plus = Apres(s, R("a.cs", 4, 0, 30_000))!;
        Assert.Equal(ReactionDiagnostics.Grimace, plus.Reaction);
        var moins = Apres(s, R("a.cs", 2, 0, 60_000))!;
        Assert.Equal(ReactionDiagnostics.Aucune, moins.Reaction);
        var propre = Apres(s, R("a.cs", 0, 0, 90_000))!;
        Assert.Equal(("✓ propre ! · a.cs", ReactionDiagnostics.Saut, TonDiagnostics.Propre), (propre.Ligne, propre.Reaction, propre.Ton));
        Assert.Equal(1, s.Propres);
        // Plus d'erreur mais des avertissements : toujours la fête.
        Apres(s, R("a.cs", 1, 3, 120_000));
        var p2 = Apres(s, R("a.cs", 0, 3, 150_000))!;
        Assert.Equal("✓ plus d'erreur ! · 3 avert. · a.cs", p2.Ligne);
        Assert.Equal(2, s.Propres);
    }

    [Fact]
    public void Se_tait_sur_un_fichier_propre()
    {
        var s = new SuiviDiagnostics();
        Assert.Null(Apres(s, R("propre.cs", 0, 0, 0)));     // on arrive sur un fichier propre : rien
        Apres(s, R("propre.cs", 0, 2, 30_000));
        Assert.Null(Apres(s, R("propre.cs", 0, 0, 60_000))); // les avertissements partent : rien non plus
        Assert.Equal(0, s.Propres);
        // Passer à zéro sans avoir eu d'erreur dans CE fichier n'est pas une fête.
        Apres(s, R("b.cs", 2, 0, 90_000));
        Assert.Null(Apres(s, R("c.cs", 0, 0, 120_000)));
        Assert.Equal(0, s.Propres);
    }

    [Fact]
    public void Repos_entre_deux_bulles_puis_le_dernier_etat()
    {
        var s = new SuiviDiagnostics();
        Assert.NotNull(Apres(s, R("a.cs", 1, 0, 0)));
        Assert.Null(Apres(s, R("a.cs", 2, 0, 5000)));        // trop tôt (repos de 20 s)
        Assert.Null(Apres(s, R("b.cs", 5, 0, 10_000)));
        var a = s.Battre(SuiviDiagnostics.Repos + 2500, false)!;
        Assert.Equal("5 erreurs · b.cs", a.Texte);           // seulement l'état courant
        // Le passage à zéro attend lui aussi la fin du repos, mais n'est pas perdu.
        s.Recevoir(R("b.cs", 0, 0, 25_000));
        Assert.Null(s.Battre(30_000, false));
        Assert.Equal(ReactionDiagnostics.Saut, s.Battre(SuiviDiagnostics.Repos * 2 + 3000, false)!.Reaction);
    }

    [Fact]
    public void Duree_de_vie_et_fermeture()
    {
        var s = new SuiviDiagnostics();
        Apres(s, R("a.cs", 2, 0, 0));
        Assert.NotNull(s.Courant(SuiviDiagnostics.Ttl - 1));
        Assert.Equal("⚠ 2 erreurs · a.cs", s.Resume(1000));
        Assert.Null(s.Courant(SuiviDiagnostics.Ttl + 1));    // éditeur fermé sans prévenir : oublié
        Assert.Null(s.Battre(SuiviDiagnostics.Ttl + 1, false));
        Assert.Null(s.Resume(SuiviDiagnostics.Ttl + 1));
        // À la réouverture, le même état est annoncé de nouveau.
        var t = SuiviDiagnostics.Ttl + 10_000;
        Assert.NotNull(Apres(s, R("a.cs", 2, 0, t)));
        // Fermeture explicite.
        s.Recevoir(R("", 0, 0, t + 5000));
        Assert.Null(s.Courant(t + 5000));
    }

    [Fact]
    public void Plusieurs_editeurs_le_plus_recent_parle()
    {
        var s = new SuiviDiagnostics();
        Apres(s, R("a.cs", 1, 0, 0, "vs"));
        var a = Apres(s, R("app.ts", 2, 0, 30_000, "vscode"))!;
        Assert.Equal("2 erreurs · app.ts", a.Texte);
        Assert.Equal("app.ts", s.Courant(33_000)!.Fichier);
        Assert.Null(Apres(s, R("a.cs", 0, 0, 60_000, "vs")));  // retour dans VS sur un fichier propre : rien
        Assert.Equal("✓ a.cs : aucune erreur", s.Resume(63_000));
    }

    [Fact]
    public void Api_route_diagnostics()
    {
        RapportDiagnostics? recu = null;
        bool actif = true;
        var api = new ApiLocale(() => "jeton", () => "{}", _ => { }, () => 42, d => { recu = d; return actif; });
        var entetes = new Dictionary<string, string> { ["Authorization"] = "Bearer jeton" };
        var (code, corps) = api.Traiter("POST", "/diagnostics", entetes,
            """{"source":"vscode","fichier":"C:\\x\\y\\Program.cs","erreurs":1,"avertissements":0}""");
        Assert.Equal(202, code);
        Assert.Contains("\"recu\":true", corps);
        Assert.Equal(("Program.cs", 42.0), (recu!.Fichier, recu.T));
        actif = false;
        Assert.Contains("\"recu\":false", api.Traiter("POST", "/diagnostics", entetes, """{"source":"vs","fichier":"a.cs"}""").Corps);
        Assert.Equal(400, api.Traiter("POST", "/diagnostics", entetes, "{}").Code);
        Assert.Equal(405, api.Traiter("GET", "/diagnostics", entetes, "").Code);
        Assert.Equal(401, api.Traiter("POST", "/diagnostics", new Dictionary<string, string>(), "{}").Code);
        // Sans suivi branché (anciens appels), la route n'existe pas.
        var sans = new ApiLocale(() => "jeton", () => "{}", _ => { });
        Assert.Equal(404, sans.Traiter("POST", "/diagnostics", entetes, "{}").Code);
    }
}
