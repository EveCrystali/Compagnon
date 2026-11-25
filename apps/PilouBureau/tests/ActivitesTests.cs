using PilouBureau;
using Xunit;

public class ActivitesTests
{
    private static readonly List<Activites.Regle> Defaut = Activites.Charger(null);
    private static readonly DateTime Midi = new(2026, 11, 25, 12, 0, 0);

    private static Activites.Contexte C(string proc = "", string titre = "", string chemin = "", Activites.Ecran ecran = Activites.Ecran.Normal,
        bool camera = false, bool micro = false, Dictionary<string, float>? sons = null, DateTime? heure = null) =>
        new(proc, titre, chemin, ecran, camera, micro, sons ?? new Dictionary<string, float>(), heure ?? Midi);

    [Fact]
    public void Les_regles_par_defaut_sont_embarquees_et_toutes_valides()
    {
        Assert.True(Defaut.Count > 25);
        Assert.All(Defaut, r => Assert.Contains(r.Activite, Activites.Toutes));
    }

    [Theory]
    [InlineData("EXCEL.EXE", "", "", "tableur")]
    [InlineData("devenv", "MonProjet - Microsoft Visual Studio", "", "code")]
    [InlineData("Code", "app.ts - compagnon - Visual Studio Code", "", "code")]
    [InlineData("WINWORD", "Rapport.docx - Word", "", "texte")]
    [InlineData("POWERPNT", "", "", "diaporama")]
    [InlineData("OUTLOOK", "Boîte de réception", "", "mail")]
    [InlineData("Spotify", "Daft Punk - One More Time", "", "musique")]
    [InlineData("vlc", "film.mkv - VLC", "", "video")]
    [InlineData("SumatraPDF", "doc.pdf", "", "lecture")]
    [InlineData("blender", "", "", "dessin")]
    [InlineData("Wow", "World of Warcraft", "", "jeu-mmo")]
    [InlineData("Teams", "Réunion", "", "visio")]
    [InlineData("notion", "", "", "texte")]
    [InlineData("soffice.bin", "budget.ods - LibreOffice Calc", "", "tableur")]
    [InlineData("soffice.bin", "lettre.odt - LibreOffice Writer", "", "texte")]
    [InlineData("chrome", "Budget 2026 - Google Sheets - Google Chrome", "", "tableur")]
    [InlineData("msedge", "Daft Punk - YouTube Music - Microsoft Edge", "", "musique")]
    [InlineData("firefox", "Stranger Things | Netflix — Mozilla Firefox", "", "video")]
    [InlineData("chrome", "Boîte de réception (3) - moi - Gmail", "", "mail")]
    [InlineData("chrome", "EveCrystali/Compagnon: Pilou - GitHub - Google Chrome", "", "code")]
    [InlineData("chrome", "Recette de crêpes - Marmiton", "", "")]
    [InlineData("chrome", "Nos partenaires - Google Chrome", "", "")]
    [InlineData("notepad", "", "", "texte")]
    [InlineData("inconnu", "Rien", "", "")]
    public void Reconnaissance(string proc, string titre, string chemin, string attendu) =>
        Assert.Equal(attendu, Activites.Detecter(C(proc, titre, chemin), Defaut));

    [Fact]
    public void Un_jeu_steam_est_reconnu_par_son_chemin_et_un_mmo_connu_gagne_sur_le_chemin()
    {
        Assert.Equal("jeu", Activites.Detecter(C("Hollow Knight2", "", @"D:\SteamLibrary\steamapps\common\Silksong\Silksong.exe"), Defaut));
        Assert.Equal("jeu-mmo", Activites.Detecter(C("ffxiv_dx11", "", @"C:\Program Files (x86)\Steam\steamapps\common\FINAL FANTASY XIV Online\game\ffxiv_dx11.exe"), Defaut));
        Assert.Equal("jeu", Activites.Detecter(C("javaw", "Minecraft 1.21.4"), Defaut));
        Assert.Equal("", Activites.Detecter(C("javaw", "IntelliJ helper"), Defaut));
    }

    [Fact]
    public void Camera_donne_visio_micro_seul_ne_remplace_pas_une_activite_reconnue()
    {
        Assert.Equal("visio", Activites.Detecter(C("EXCEL", camera: true), Defaut));
        Assert.Equal("tableur", Activites.Detecter(C("EXCEL", micro: true), Defaut));
        Assert.Equal("visio", Activites.Detecter(C("inconnu", micro: true), Defaut));
    }

    [Fact]
    public void Musique_entendue_quand_rien_n_est_reconnu_et_nuit_apres_23_h()
    {
        var sons = new Dictionary<string, float> { ["Spotify"] = 0.4f };
        Assert.Equal("musique", Activites.Detecter(C("explorer", sons: sons), Defaut));
        Assert.Equal("code", Activites.Detecter(C("Code", sons: sons), Defaut));
        Assert.Equal("", Activites.Detecter(C("explorer", sons: new() { ["Spotify"] = 0.001f }), Defaut));
        Assert.Equal("nuit", Activites.Detecter(C("explorer", heure: new DateTime(2026, 11, 25, 23, 30, 0)), Defaut));
        Assert.Equal("nuit", Activites.Detecter(C("", heure: new DateTime(2026, 11, 26, 2, 0, 0)), Defaut));
        Assert.Equal("code", Activites.Detecter(C("Code", heure: new DateTime(2026, 11, 25, 23, 30, 0)), Defaut));
        Assert.Equal("", Activites.Detecter(C("explorer", heure: new DateTime(2026, 11, 25, 22, 0, 0)), Defaut));
        Assert.Equal(0.4f, Activites.Crete(C("explorer", sons: sons), Defaut));
    }

    [Fact]
    public void Regles_personnelles_s_ajoutent_ignorent_ou_remplacent()
    {
        const string ajout = """
            { "regles": [
              { "activite": "code", "priorite": 50, "processus": ["monediteur.exe"] },
              { "activite": "", "priorite": 90, "processus": ["excel"] },
              { "activite": "jeu", "priorite": 50, "titre": "[regex cassée" },
              { "activite": "lecture", "priorite": 23, "processus": ["chrome"], "titre": "Marmiton" }
            ] }
            """;
        var r = Activites.Charger(ajout);
        Assert.Equal("code", Activites.Detecter(C("MonEditeur"), r));
        Assert.Equal("", Activites.Detecter(C("EXCEL"), r));          // ignoré par la personne
        Assert.Equal("lecture", Activites.Detecter(C("chrome", "Recette - Marmiton"), r));
        Assert.Equal("tableur", Activites.Detecter(C("chrome", "x - Google Sheets"), r)); // les règles par défaut restent

        var seules = Activites.Charger("""{ "remplacer": true, "regles": [ { "activite": "dessin", "processus": ["excel"] } ] }""");
        Assert.Equal("dessin", Activites.Detecter(C("excel"), seules));
        Assert.Equal("", Activites.Detecter(C("Code"), seules));

        Assert.Equal(Defaut.Count, Activites.Charger("pas du json").Count);
    }

    [Fact]
    public void A_priorite_egale_la_regle_personnelle_gagne()
    {
        var r = Activites.Charger("""{ "regles": [ { "activite": "dessin", "priorite": 29, "processus": ["excel"] } ] }""");
        Assert.Equal("dessin", Activites.Detecter(C("excel"), r));
    }

    [Fact]
    public void Discretion()
    {
        var o = new Activites.OptionsDiscretion();
        Assert.Equal((true, "plein-ecran"), Activites.Discretion(C(ecran: Activites.Ecran.Jeu3D), o, false));
        Assert.Equal((true, "plein-ecran"), Activites.Discretion(C(ecran: Activites.Ecran.PleinEcran), o, false));
        Assert.Equal((true, "presentation"), Activites.Discretion(C(ecran: Activites.Ecran.Presentation), o, true));
        Assert.Equal((true, "visio"), Activites.Discretion(C(micro: true), o, false));
        // Une IA qui attend garde Pilou visible, sauf en présentation.
        Assert.Equal((false, ""), Activites.Discretion(C(ecran: Activites.Ecran.Jeu3D), o, true));
        Assert.Equal((false, ""), Activites.Discretion(C(camera: true), o, true));
        // Options coupées.
        var rien = new Activites.OptionsDiscretion(false, false, false);
        Assert.Equal((false, ""), Activites.Discretion(C(ecran: Activites.Ecran.Presentation, camera: true), rien, false));
        Assert.Equal((false, ""), Activites.Discretion(C(), o, false));
    }

    [Fact]
    public void Une_tenue_ne_change_qu_apres_20_s_de_la_meme_activite()
    {
        var obs = new Activites.Observateur();
        Assert.False(obs.Observer("code", 0));
        Assert.False(obs.Observer("code", 19_000));
        Assert.True(obs.Observer("code", 20_000));
        Assert.Equal("code", obs.Tenue);
        Assert.False(obs.Observer("tableur", 25_000));   // coup d'œil
        Assert.False(obs.Observer("code", 30_000));
        Assert.Equal("code", obs.Tenue);
        Assert.False(obs.Observer("", 31_000));
        Assert.True(obs.Observer("", 51_000));
        Assert.Equal("", obs.Tenue);
    }
}

public class MetiersTests
{
    [Theory]
    [InlineData(0, 0)]
    [InlineData(3599, 0)]
    [InlineData(3600, 1)]
    [InlineData(5 * 3600, 2)]
    [InlineData(39 * 3600, 3)]
    [InlineData(40 * 3600, 4)]
    [InlineData(1000 * 3600, 6)]
    public void Paliers(long secondes, int niveau) => Assert.Equal(niveau, Metiers.Niveau(secondes));

    [Fact]
    public void Un_metier_additionne_ses_activites()
    {
        var s = new Dictionary<string, long> { ["jeu"] = 3 * 3600, ["jeu-mmo"] = 3 * 3600 };
        var joueur = Metiers.Tous.Single(m => m.Id == "joueur");
        Assert.Equal(2, Metiers.Niveau(Metiers.Secondes(joueur, s)));
        Assert.Equal("6 h / 15 h", Metiers.Progres(Metiers.Secondes(joueur, s)));
        Assert.Equal("joueur", Metiers.DeActivite("jeu-mmo"));
        Assert.All(Activites.Toutes.Where(a => a != "nuit"), a => Assert.NotEqual("", Metiers.DeActivite(a)));
    }

    private static Stats S(Dictionary<string, long>? sec = null, double serie = 0, int reunions = 0, int pres = 0, int heure = 12, string act = "code") =>
        new(sec ?? new Dictionary<string, long>(), serie, reunions, pres, new DateTime(2026, 11, 25, heure, 0, 0), act);

    [Fact]
    public void Succes_debloques_une_seule_fois()
    {
        Assert.Empty(Succes.Nouveaux(S(), Array.Empty<string>()));
        Assert.Contains(Succes.Nouveaux(S(serie: 4 * 3600), Array.Empty<string>()), d => d.Id == "marathon");
        Assert.DoesNotContain(Succes.Nouveaux(S(serie: 4 * 3600), new[] { "marathon" }), d => d.Id == "marathon");
        Assert.Contains(Succes.Nouveaux(S(new() { ["tableur"] = 10 * 3600 }), Array.Empty<string>()), d => d.Id == "tableur-fou");
        Assert.Contains(Succes.Nouveaux(S(reunions: 10), Array.Empty<string>()), d => d.Id == "visio-man");
        Assert.Contains(Succes.Nouveaux(S(pres: 5), Array.Empty<string>()), d => d.Id == "orateur");
        Assert.Contains(Succes.Nouveaux(S(heure: 2), Array.Empty<string>()), d => d.Id == "noctambule");
        Assert.DoesNotContain(Succes.Nouveaux(S(heure: 2, act: "nuit"), Array.Empty<string>()), d => d.Id == "noctambule");
        Assert.Contains(Succes.Nouveaux(S(heure: 5), Array.Empty<string>()), d => d.Id == "leve-tot");

        var huit = Activites.Toutes.Take(8).ToDictionary(a => a, _ => 120L);
        Assert.Contains(Succes.Nouveaux(S(huit), Array.Empty<string>()), d => d.Id == "explorateur");

        var quatre = new Dictionary<string, long> { ["code"] = 5 * 3600, ["tableur"] = 5 * 3600, ["musique"] = 5 * 3600, ["mail"] = 5 * 3600 };
        Assert.Contains(Succes.Nouveaux(S(quatre), Array.Empty<string>()), d => d.Id == "couteau-suisse");
    }

    [Fact]
    public void Progres_lisible()
    {
        var marathon = Succes.Tous.Single(d => d.Id == "marathon");
        Assert.Equal("2.5 h / 4 h", Succes.Progres(marathon, S(serie: 2.5 * 3600)).Replace(',', '.'));
        var visio = Succes.Tous.Single(d => d.Id == "visio-man");
        Assert.Equal("3 / 10", Succes.Progres(visio, S(reunions: 3)));
        Assert.True(Succes.Tous.Count >= 15);
        Assert.Equal(Succes.Tous.Count, Succes.Tous.Select(d => d.Id).Distinct().Count());
    }

    [Fact]
    public void Le_telephone_recoit_metiers_et_succes()
    {
        var p = new Profil { Activites = new() { ["code"] = 6 * 3600 }, Succes = new() { "marathon" } };
        var prog = Telephone.Progression(p, 100, "aucun");
        var metiers = Assert.IsType<Dictionary<string, int>>(prog["metiers"]);
        Assert.Equal(2, metiers["codeur"]);
        Assert.False(metiers.ContainsKey("tableur"));
        Assert.Equal(new List<string> { "marathon" }, prog["succes"]);
    }
}
