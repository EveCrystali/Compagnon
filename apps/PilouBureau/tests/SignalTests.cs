using System.Text.Json;
using PilouBureau;
using Xunit;

public class SignalTests
{
    private const double T0 = 1_800_000_000_000;

    private static EtatSession Jouer(params (string Json, double T)[] evenements)
    {
        EtatSession? e = null;
        foreach (var (json, t) in evenements)
        {
            var ev = Signal.DepuisJson(json)!;
            var (suivant, effacer) = Signal.Appliquer("codex", ev with { Session = "codex-abc" }, e, t);
            Assert.False(effacer);
            e = suivant ?? e;
        }
        return e!;
    }

    [Fact]
    public void Un_tour_Codex_complet_passe_par_travail_outil_puis_fini()
    {
        var debut = Jouer(("""{"hook_event_name":"UserPromptSubmit","session_id":"abc","cwd":"C:\\code\\mon-api","prompt":"x"}""", T0));
        Assert.True(debut.EnTour);
        Assert.Equal("mon-api", debut.Libelle);
        Assert.Equal("codex", debut.Source);
        Assert.Equal(Signal.DureeVie, debut.Ttl);

        var outil = Jouer(
            ("""{"hook_event_name":"UserPromptSubmit","session_id":"abc","cwd":"/x/mon-api"}""", T0),
            ("""{"hook_event_name":"PreToolUse","session_id":"abc","tool_name":"shell","tool_input":{"command":["bash","-lc","ls"]}}""", T0 + 1000));
        Assert.Equal("shell", outil.Outil);
        Assert.Equal(T0, outil.DebutTour);
        Assert.Equal(1, outil.OutilRev);

        var fin = Jouer(
            ("""{"hook_event_name":"UserPromptSubmit","session_id":"abc","cwd":"/x/mon-api"}""", T0),
            ("""{"hook_event_name":"PreToolUse","session_id":"abc","tool_name":"shell"}""", T0 + 1000),
            ("""{"hook_event_name":"PostToolUse","session_id":"abc","tool_name":"shell","tool_response":{"exit_code":0}}""", T0 + 2000),
            ("""{"hook_event_name":"Stop","session_id":"abc","last_assistant_message":"ok"}""", T0 + 3000));
        Assert.False(fin.EnTour);
        Assert.Equal("", fin.Outil);
        Assert.Equal(T0 + 3000, fin.FinTour);
        Assert.Equal("", fin.FinRaison);
        Assert.Equal("soulage", fin.Humeur);
        Assert.Equal(1, fin.Xp);
    }

    [Fact]
    public void Demande_d_autorisation_puis_outil_execute()
    {
        var attend = Jouer(
            ("""{"hook_event_name":"UserPromptSubmit","session_id":"abc"}""", T0),
            ("""{"hook_event_name":"PermissionRequest","session_id":"abc","tool_name":"shell"}""", T0 + 500));
        Assert.Equal("permission", attend.Attente);

        var repris = Jouer(
            ("""{"hook_event_name":"UserPromptSubmit","session_id":"abc"}""", T0),
            ("""{"hook_event_name":"PermissionRequest","session_id":"abc","tool_name":"shell"}""", T0 + 500),
            ("""{"hook_event_name":"PostToolUse","session_id":"abc","tool_name":"shell"}""", T0 + 900));
        Assert.Equal("", repris.Attente);
    }

    [Fact]
    public void Commit_reussi_fait_la_fete_et_outil_en_erreur_grimace()
    {
        var commit = Jouer(("""{"hook_event_name":"PostToolUse","session_id":"abc","tool_input":{"command":"git commit -m x"},"tool_response":{"exit_code":0}}""", T0));
        Assert.Equal("fete", commit.Humeur);
        Assert.Equal(5, commit.Xp);

        var rate = Jouer(("""{"hook_event_name":"PostToolUse","session_id":"abc","tool_input":{"command":"git commit -m x"},"tool_response":{"exit_code":1}}""", T0));
        Assert.Equal("grimace", rate.Humeur);
        Assert.Equal(0, rate.Xp);
    }

    [Fact]
    public void Fin_de_session_efface_et_evenement_inconnu_n_ecrit_rien()
    {
        var fin = Signal.DepuisJson("""{"hook_event_name":"SessionEnd","session_id":"abc","reason":"exit"}""")!;
        Assert.True(Signal.Appliquer("codex", fin, null, T0).Effacer);

        var inconnu = Signal.DepuisJson("""{"hook_event_name":"PreCompact","session_id":"abc"}""")!;
        Assert.Null(Signal.Appliquer("codex", inconnu, null, T0).Etat);
    }

    [Fact]
    public void Notify_legacy_de_Codex_et_notification_de_Claude_sont_compris()
    {
        var notify = Signal.DepuisJson("""{"type":"agent-turn-complete","thread-id":"t1","turn-id":"u","cwd":"/a/b","input-messages":[],"last-assistant-message":"fini"}""")!;
        Assert.Equal("fin", Signal.Geste(notify.Nom));
        Assert.Equal("t1", notify.Session);

        var permission = Signal.DepuisJson("""{"hook_event_name":"Notification","session_id":"s","notification_type":"permission_prompt"}""")!;
        Assert.Equal("permission", Signal.Geste(permission.Nom));

        var autre = Signal.DepuisJson("""{"hook_event_name":"Notification","session_id":"s","notification_type":"idle_prompt"}""")!;
        Assert.Equal("", Signal.Geste(autre.Nom));
    }

    [Fact]
    public void Ligne_de_commande_generique()
    {
        var ev = Signal.DepuisArguments("outil", "build", "ci-42", "Build nocturne");
        var (e, _) = Signal.Appliquer("script", ev with { Session = "script-ci42" }, null, T0);
        Assert.Equal("build", e!.Outil);
        Assert.Equal("Build nocturne", e.Libelle);

        var xp = Signal.DepuisArguments("xp", "999", "", "");
        Assert.Equal(50, xp.Xp); // borné
        Assert.Equal("fin", Signal.Geste("Stop"));
        Assert.Equal("tour", Signal.Geste("before_submit_prompt")); // Cursor
        Assert.Equal("outil", Signal.Geste("BeforeTool")); // Gemini CLI
    }

    [Fact]
    public void L_etat_ecrit_se_relit_a_l_identique_et_la_bulle_montre_la_source()
    {
        var ev = Signal.DepuisJson("""{"hook_event_name":"PermissionRequest","session_id":"abc","cwd":"/x/site"}""")!;
        var (e, _) = Signal.Appliquer("codex", ev with { Session = "codex-abc" }, null, T0);
        var relu = EtatSession.Lire(e!.Json())!;
        Assert.Equal(e, relu);
        var (lignes, _) = Statut.Lignes(new[] { relu }, T0 + 1000);
        Assert.Equal("Codex · site", lignes.Single().Libelle);
        Assert.Equal("❗", lignes.Single().Signe);
    }

    [Fact]
    public void Ecriture_sur_disque_puis_effacement()
    {
        var dossier = Path.Combine(Path.GetTempPath(), "pilou-" + Guid.NewGuid().ToString("N"));
        try
        {
            Signal.Ecrire(dossier, "codex", new Evenement("userpromptsubmit", "019a-ef/../x", Libelle: "api"), T0);
            var fichier = Assert.Single(Directory.GetFiles(dossier));
            Assert.Equal("etat-codex-019aefx.json", Path.GetFileName(fichier));
            var lu = Assert.Single(Suivi.LireDossier(dossier));
            Assert.True(lu.EnTour);
            Assert.Equal("codex-019aefx", lu.Session);

            Signal.Ecrire(dossier, "codex", new Evenement("sessionend", "019a-ef/../x"), T0 + 10);
            Assert.Empty(Directory.GetFiles(dossier));
        }
        finally
        {
            if (Directory.Exists(dossier)) Directory.Delete(dossier, true);
        }
    }

    [Fact]
    public void Une_session_Codex_vit_des_heures_et_disparait_quand_son_fichier_part()
    {
        var ev = Signal.DepuisJson("""{"hook_event_name":"Stop","session_id":"abc"}""")!;
        var (e, _) = Signal.Appliquer("codex", ev with { Session = "codex-abc" }, null, T0);
        var suivi = new Suivi();
        suivi.Observer(new[] { e! }, T0 + 3_600_000);
        Assert.Single(suivi.Vivantes(T0 + 3_600_000)); // 1 h sans événement : toujours là
        suivi.Observer(Array.Empty<EtatSession>(), T0 + 3_600_000);
        Assert.Empty(suivi.Vivantes(T0 + 3_600_000));
    }

    [Fact]
    public void Les_anciens_fichiers_du_mod_restent_des_sessions_Claude()
    {
        var e = EtatSession.Lire("""{"v":2,"session":"a1b2c3d4","t":1,"humeur":"repos","enTour":true,"nom":"Pilou","niveau":3,"bureau":true}""")!;
        Assert.True(e.Claude);
        Assert.Equal(Suivi.Vivante, e.Ttl);
    }
}

public class CodexTests
{
    private const string Exe = @"C:\Users\x\.claude\compagnon\bureau\PilouBureau.exe";

    [Fact]
    public void Brancher_garde_les_hooks_existants_et_debrancher_les_rend_intacts()
    {
        const string existant = """
            {"description":"à moi","hooks":{"Stop":[{"hooks":[{"type":"command","command":"say fini"}]}]}}
            """;
        var avec = Codex.AvecPilou(existant, Exe);
        using (var doc = JsonDocument.Parse(avec))
        {
            var hooks = doc.RootElement.GetProperty("hooks");
            Assert.Equal(2, hooks.GetProperty("Stop").GetArrayLength());
            var pilou = hooks.GetProperty("PreToolUse")[0].GetProperty("hooks")[0];
            Assert.Equal($"\"{Exe}\" --signal codex", pilou.GetProperty("command").GetString());
            Assert.True(pilou.GetProperty("async").GetBoolean());
            Assert.False(hooks.GetProperty("SessionEnd")[0].GetProperty("hooks")[0].TryGetProperty("async", out _));
            Assert.Equal("à moi", doc.RootElement.GetProperty("description").GetString());
        }

        // Brancher deux fois ne double rien.
        var deux = Codex.AvecPilou(avec, Exe);
        Assert.Equal(avec, deux);

        var sans = Codex.SansPilou(avec);
        using var apres = JsonDocument.Parse(sans);
        var stop = apres.RootElement.GetProperty("hooks").GetProperty("Stop");
        Assert.Equal(1, stop.GetArrayLength());
        Assert.Equal("say fini", stop[0].GetProperty("hooks")[0].GetProperty("command").GetString());
        Assert.False(apres.RootElement.GetProperty("hooks").TryGetProperty("PreToolUse", out _));
    }

    [Fact]
    public void Debrancher_un_fichier_qui_n_avait_que_Pilou_le_vide()
    {
        Assert.Equal("", Codex.SansPilou(Codex.AvecPilou(null, Exe)));
    }

    [Fact]
    public void Un_fichier_casse_n_est_pas_ecrase()
    {
        Assert.Throws<InvalidDataException>(() => Codex.AvecPilou("{ pas du json", Exe));
    }
}
