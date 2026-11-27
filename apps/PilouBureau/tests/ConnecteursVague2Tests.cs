using System.Net;
using System.Net.Http;
using System.Text;
using System.Text.Json.Nodes;
using PilouBureau;
using Xunit;

// Deuxième vague de connecteurs : chaque protocole est testé sur des réponses enregistrées, sans réseau.
public class ConnecteursVague2Tests
{
    // ---- Outils communs

    // Serveur HTTP enregistré : une réponse par appel, et les requêtes reçues pour vérifier les en-têtes.
    private sealed class Rejoueur : HttpMessageHandler
    {
        public readonly List<HttpRequestMessage> Requetes = new();
        private readonly Queue<Func<HttpRequestMessage, HttpResponseMessage>> _reponses = new();

        public Rejoueur Puis(Func<HttpRequestMessage, HttpResponseMessage> f)
        {
            _reponses.Enqueue(f);
            return this;
        }

        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage r, CancellationToken ct)
        {
            Requetes.Add(r);
            return Task.FromResult(_reponses.Dequeue()(r));
        }
    }

    private static HttpResponseMessage Json(string corps, string? etag = null)
    {
        var r = new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(corps, Encoding.UTF8, "application/json") };
        if (etag is not null) r.Headers.ETag = new System.Net.Http.Headers.EntityTagHeaderValue(etag);
        return r;
    }

    private static (Registre R, ContexteConnecteur Ctx, List<EvenementPilou> Recus) Monter(Connecteur c, HttpMessageHandler? http = null)
    {
        var r = new Registre(new ReglagesConnecteurs(), new CoffreMemoire(), () => { }, http is null ? null : new HttpClient(http));
        var recus = new List<EvenementPilou>();
        r.Evenement += recus.Add;
        r.Ajouter(c);
        return (r, r.Contexte(c), recus);
    }

    [Fact]
    public void Tous_les_connecteurs_sont_desactives_par_defaut_et_gardent_leurs_jetons_au_coffre()
    {
        Connecteur[] tous =
        {
            new ConnecteurDiscordBot(), new ConnecteurGitHub(), new ConnecteurMail(), new ConnecteurAgenda(),
            new ConnecteurSpotify(), new ConnecteurTwitch(), new ConnecteurYouTube(), new ConnecteurHomeAssistant(),
        };
        Assert.Equal(tous.Length, tous.Select(c => c.Id).Distinct().Count());
        foreach (var c in tous)
        {
            var coffre = new CoffreMemoire();
            var reglages = new ReglagesConnecteurs();
            var r = new Registre(reglages, coffre, () => { });
            r.Ajouter(c);
            Assert.False(r.Actif(c));
            Assert.NotEqual("", c.Aide);
            var ctx = r.Contexte(c);
            foreach (var s in c.Reglages.Where(x => x.Type == TypeReglage.Secret))
            {
                ctx.Ecrire(s.Cle, "jeton-" + s.Cle);
                Assert.Equal("jeton-" + s.Cle, coffre.Lire($"{c.Id}.{s.Cle}"));
            }
            // Aucun secret dans les réglages en clair (fichier reglages.json).
            var clair = string.Join("|", reglages.Valeurs.Values.SelectMany(v => v.Values));
            Assert.DoesNotContain("jeton-", clair);
        }
        Assert.Contains("selfbot", new ConnecteurDiscordBot().Aide);
    }

    // ---- Discord : passerelle v10

    [Fact]
    public void Discord_hello_identify_ready_battement_puis_message()
    {
        var p = new PasserelleDiscord("JETON");
        var r = p.Recevoir("""{"op":10,"d":{"heartbeat_interval":41250}}""");
        Assert.Equal(41250, p.IntervalleBattement);
        var identify = JsonNode.Parse(Assert.Single(r.AEnvoyer))!;
        Assert.Equal(2, (int)identify["op"]!);
        Assert.Equal("JETON", (string)identify["d"]!["token"]!);
        Assert.Equal(PasserelleDiscord.Intents, (int)identify["d"]!["intents"]!);
        Assert.Equal("""{"op":1,"d":null}""", p.Battement());

        p.Recevoir("""{"op":0,"s":1,"t":"READY","d":{"session_id":"abc","resume_gateway_url":"wss://reprise.discord.gg","user":{"id":"999"}}}""");
        Assert.True(p.Pret);
        Assert.Equal("999", p.IdBot);
        Assert.Equal(1, p.Sequence);
        Assert.Equal("""{"op":1,"d":1}""", p.Battement());
        p.AccuseAttendu = true;
        p.Recevoir("""{"op":11}""");
        Assert.False(p.AccuseAttendu);
        Assert.Single(p.Recevoir("""{"op":1}""").AEnvoyer);                // battement demandé par le serveur

        p.Recevoir("""{"op":0,"s":2,"t":"GUILD_CREATE","d":{"id":"g","channels":[{"id":"42","name":"général"}]}}""");
        var m = p.Recevoir("""
            {"op":0,"s":3,"t":"MESSAGE_CREATE","d":{"id":"m1","channel_id":"42","guild_id":"g","content":"salut <@999> !",
             "author":{"id":"7","username":"lea","global_name":"Léa"},"mentions":[{"id":"999"}]}}
            """).Message;
        Assert.NotNull(m);
        Assert.Equal(3, p.Sequence);
        var a = PasserelleDiscord.Annonce(m!, p.IdBot, "", Array.Empty<string>(), false, p.Salons);
        Assert.Equal("💬 #général · Léa", a!.Value.Titre);
        Assert.Equal("salut @toi !", a.Value.Texte);
        Assert.Equal(1, a.Value.Gravite);
        // Contenu masqué : le titre seul.
        Assert.Equal("t'a mentionné", PasserelleDiscord.Annonce(m!, p.IdBot, "", Array.Empty<string>(), true, p.Salons)!.Value.Texte);
    }

    [Fact]
    public void Discord_filtre_salons_bots_et_mes_propres_messages()
    {
        var salons = new Dictionary<string, string> { ["42"] = "général", ["43"] = "hors-sujet" };
        MessageDiscord M(string salon, string auteurId, bool bot = false, params string[] mentions) =>
            new("m", salon, "g", "x", auteurId, "texte", bot, mentions);
        Assert.Null(PasserelleDiscord.Annonce(M("43", "7"), "999", "5", new[] { "42" }, false, salons));     // salon non suivi
        Assert.NotNull(PasserelleDiscord.Annonce(M("42", "7"), "999", "5", new[] { "42" }, false, salons));  // salon suivi
        Assert.NotNull(PasserelleDiscord.Annonce(M("43", "7", false, "5"), "999", "5", new[] { "42" }, false, salons)); // mention de moi
        Assert.Null(PasserelleDiscord.Annonce(M("42", "7", true), "999", "5", new[] { "42" }, false, salons)); // un bot
        Assert.Null(PasserelleDiscord.Annonce(M("42", "5"), "999", "5", new[] { "42" }, false, salons));       // moi-même
    }

    [Fact]
    public void Discord_reprise_reconnect_et_session_invalide()
    {
        var p = new PasserelleDiscord("J", "abc", 17, "wss://reprise.discord.gg");
        var reprise = JsonNode.Parse(Assert.Single(p.Recevoir("""{"op":10,"d":{"heartbeat_interval":1000}}""").AEnvoyer))!;
        Assert.Equal(6, (int)reprise["op"]!);
        Assert.Equal("abc", (string)reprise["d"]!["session_id"]!);
        Assert.Equal(17, (int)reprise["d"]!["seq"]!);
        var r7 = p.Recevoir("""{"op":7,"d":null}""");
        Assert.True(r7.Reconnecter && r7.Reprendre);
        var r9 = p.Recevoir("""{"op":9,"d":false}""");
        Assert.True(r9.Reconnecter);
        Assert.False(r9.Reprendre);
        Assert.Equal("", p.SessionId);
        Assert.Null(p.Sequence);
    }

    // ---- GitHub : ETag et notifications

    private const string Notifs = """
        [{"id":"1","reason":"review_requested","updated_at":"2026-11-25T10:00:00Z","subject":{"title":"Ajoute les connecteurs","type":"PullRequest"},"repository":{"full_name":"moi/compagnon"}},
         {"id":"2","reason":"ci_activity","updated_at":"2026-11-25T10:01:00Z","subject":{"title":"CI workflow run failed for main branch","type":"CheckSuite"},"repository":{"full_name":"moi/compagnon"}},
         {"id":"3","reason":"ci_activity","updated_at":"2026-11-25T10:02:00Z","subject":{"title":"CI workflow run succeeded for main branch","type":"CheckSuite"},"repository":{"full_name":"moi/compagnon"}},
         {"id":"4","reason":"comment","updated_at":"2026-11-25T10:03:00Z","subject":{"title":"Bug météo","type":"Issue"},"repository":{"full_name":"moi/compagnon"}},
         {"id":"5","reason":"subscribed","updated_at":"2026-11-25T10:04:00Z","subject":{"title":"bruit","type":"Issue"},"repository":{"full_name":"autre/x"}}]
        """;

    [Fact]
    public void GitHub_lit_les_notifications_une_seule_fois()
    {
        var vus = new HashSet<string>();
        var l = ConnecteurGitHub.LireNotifications(Notifs, vus, new ConnecteurGitHub.OptionsGitHub());
        Assert.Equal(4, l.Count);
        Assert.Equal("👀 Revue demandée · compagnon", l[0].Titre);
        Assert.StartsWith("✕ CI rouge", l[1].Titre);
        Assert.StartsWith("✓ CI verte", l[2].Titre);
        Assert.Equal("tests", l[2].Donnee("quete"));
        Assert.StartsWith("💬 Commentaire", l[3].Titre);
        Assert.Empty(ConnecteurGitHub.LireNotifications(Notifs, vus, new ConnecteurGitHub.OptionsGitHub()));
        // CI et commentaires décochés : la revue seule.
        Assert.Single(ConnecteurGitHub.LireNotifications(Notifs, new HashSet<string>(), new ConnecteurGitHub.OptionsGitHub(Ci: false, Commentaires: false)));
        var f = ConnecteurGitHub.LireFusions("""{"items":[{"id":9,"number":21,"title":"Connecteurs","repository_url":"https://api.github.com/repos/moi/compagnon"}]}""", vus);
        Assert.Equal("✦ PR fusionnée · compagnon", Assert.Single(f).Titre);
        Assert.Equal("fete", f[0].Donnee("humeur"));
    }

    [Fact]
    public async Task GitHub_envoie_If_None_Match_et_ne_relit_rien_sur_304()
    {
        var http = new Rejoueur()
            .Puis(_ => Json(Notifs, "\"v1\""))
            .Puis(_ => new HttpResponseMessage(HttpStatusCode.NotModified))
            .Puis(_ => Json("""[{"id":"6","reason":"mention","updated_at":"2026-11-25T11:00:00Z","subject":{"title":"@toi","type":"Issue"},"repository":{"full_name":"moi/compagnon"}}]""", "\"v2\""));
        var g = new ConnecteurGitHub();
        var (_, ctx, recus) = Monter(g, http);
        ctx.Ecrire("jeton", "ghp_x");
        ctx.Ecrire("fusions", "non");
        await g.Sonder(ctx, CancellationToken.None);               // premier relevé : rien d'annoncé
        Assert.Empty(recus);
        Assert.False(http.Requetes[0].Headers.Contains("If-None-Match"));
        Assert.Equal("Bearer", http.Requetes[0].Headers.Authorization!.Scheme);
        await g.Sonder(ctx, CancellationToken.None);               // 304
        Assert.Equal("\"v1\"", http.Requetes[1].Headers.GetValues("If-None-Match").Single());
        Assert.Empty(recus);
        await g.Sonder(ctx, CancellationToken.None);               // du nouveau
        Assert.Equal("@ Mentionné · compagnon", Assert.Single(recus).Titre);
    }

    // ---- Mail : IMAP

    // Flux duplex enregistré : ce que le serveur dit est prêt d'avance ; ce que le client écrit est gardé.
    private sealed class FluxImap : Stream
    {
        private readonly MemoryStream _serveur;
        public readonly StringBuilder Ecrit = new();
        public FluxImap(string serveur) => _serveur = new MemoryStream(Encoding.UTF8.GetBytes(serveur.Replace("\r\n", "\n").Replace("\n", "\r\n")));
        public override int Read(byte[] b, int o, int n) => _serveur.Read(b, o, n);
        public override void Write(byte[] b, int o, int n) => Ecrit.Append(Encoding.UTF8.GetString(b, o, n));
        public override bool CanRead => true;
        public override bool CanWrite => true;
        public override bool CanSeek => false;
        public override long Length => throw new NotSupportedException();
        public override long Position { get => 0; set { } }
        public override void Flush() { }
        public override long Seek(long o, SeekOrigin s) => throw new NotSupportedException();
        public override void SetLength(long v) => throw new NotSupportedException();
    }

    private static string Litteral(string s) => $"{{{Encoding.UTF8.GetByteCount(s.Replace("\n", "\r\n"))}}}\n{s}";

    [Fact]
    public async Task Mail_premier_releve_resume_puis_en_tetes_seulement()
    {
        var m = new ConnecteurMail();
        var (_, ctx, _) = Monter(m);
        ctx.Ecrire("utilisateur", "moi@exemple.fr");
        ctx.Ecrire("motdepasse", "app-pass");
        ctx.Ecrire("importants", "patron.fr");

        var premier = new FluxImap("""
            * OK IMAP prêt
            A1 OK LOGIN réussi
            * 12 EXISTS
            * OK [UIDVALIDITY 777] UIDs
            * OK [UIDNEXT 105] prédit
            A2 OK [READ-ONLY] EXAMINE
            * SEARCH 101 103
            A3 OK SEARCH
            * BYE
            A4 OK LOGOUT
            """);
        var e1 = await m.Relever(new ClientImap(premier), ctx, CancellationToken.None);
        Assert.Equal("📬 2 mails non lus", Assert.Single(e1).Titre);
        Assert.Contains("A1 LOGIN \"moi@exemple.fr\" \"app-pass\"", premier.Ecrit.ToString());
        Assert.Contains("EXAMINE INBOX", premier.Ecrit.ToString());           // lecture seule : rien n'est marqué lu
        Assert.Equal("777:104", ctx.Lire("curseur"));

        var entete = "From: =?UTF-8?Q?Jean_P=C3=A9pin?= <jean@patron.fr>\nSubject: =?UTF-8?B?UsOpdW5pb24gZGVtYWlu?=\n\n";
        var second = new FluxImap($"""
            * OK IMAP prêt
            A1 OK LOGIN
            * OK [UIDVALIDITY 777] UIDs
            * OK [UIDNEXT 107] prédit
            A2 OK EXAMINE
            * SEARCH 101 103 105 106
            A3 OK SEARCH
            * 1 FETCH (UID 105 BODY[HEADER.FIELDS (FROM SUBJECT)] {Litteral(entete)})
            A4 OK FETCH
            * 2 FETCH (UID 106 BODY[HEADER.FIELDS (FROM SUBJECT)] {Litteral("From: Lou <lou@ailleurs.org>\nSubject: Coucou\n\n")})
            A5 OK FETCH
            A6 OK LOGOUT
            """);
        var e2 = await m.Relever(new ClientImap(second), ctx, CancellationToken.None);
        Assert.Equal(2, e2.Count);
        Assert.Equal("✉ Jean Pépin", e2[0].Titre);
        Assert.Equal("Réunion demain", e2[0].Texte);
        Assert.Equal(1, e2[0].Gravite);                                      // expéditeur important
        Assert.Equal("mail", e2[0].Donnee("tenue"));
        Assert.Equal("✉ Lou", e2[1].Titre);
        Assert.Equal(0, e2[1].Gravite);
        var ecrit = second.Ecrit.ToString();
        Assert.Contains("UID FETCH 105 (BODY.PEEK[HEADER.FIELDS (FROM SUBJECT)])", ecrit);
        Assert.DoesNotContain("BODY[]", ecrit);                              // jamais le corps
        Assert.DoesNotContain("TEXT", ecrit);
        Assert.Equal("777:106", ctx.Lire("curseur"));
    }

    [Fact]
    public async Task Mail_identifiants_refuses()
    {
        var m = new ConnecteurMail();
        var (_, ctx, _) = Monter(m);
        var f = new FluxImap("* OK prêt\nA1 NO [AUTHENTICATIONFAILED] Invalid credentials\n");
        var x = await Assert.ThrowsAsync<IOException>(() => m.Relever(new ClientImap(f), ctx, CancellationToken.None));
        Assert.Contains("mot de passe d'application", x.Message);
    }

    [Fact]
    public void Mail_decode_RFC2047_et_expediteur()
    {
        Assert.Equal("Café à 10 h", ClientImap.Decoder("=?iso-8859-1?Q?Caf=E9_=E0?= 10 h"));
        Assert.Equal("Réunion demain", ClientImap.Decoder("=?UTF-8?B?UsOpdW5pb24=?= =?UTF-8?B?IGRlbWFpbg==?="));
        Assert.Equal(("Jean Pépin", "jean@patron.fr"), ClientImap.Expediteur("\"Jean Pépin\" <jean@patron.fr>"));
        Assert.Equal("lou@ailleurs.org", ClientImap.Expediteur("lou@ailleurs.org").Adresse);
        Assert.Equal("\"a\\\"b\"", ClientImap.Quoter("a\"b"));
    }

    // ---- Agenda : ICS

    private static readonly TimeZoneInfo Paris = Ics.Fuseau("Europe/Paris")!;

    private const string Calendrier = """
        BEGIN:VCALENDAR
        VERSION:2.0
        BEGIN:VEVENT
        UID:point@ex
        SUMMARY:Point d'équipe\, hebdo
        DTSTART;TZID=Europe/Paris:20261019T093000
        DTEND;TZID=Europe/Paris:20261019T100000
        RRULE:FREQ=WEEKLY;BYDAY=MO,TH;COUNT=6
        EXDATE;TZID=Europe/Paris:20261022T093000
        END:VEVENT
        BEGIN:VEVENT
        UID:point@ex
        RECURRENCE-ID;TZID=Europe/Paris:20261026T093000
        SUMMARY:Point déplacé
        DTSTART;TZID=Europe/Paris:20261026T110000
        DTEND;TZID=Europe/Paris:20261026T113000
        END:VEVENT
        BEGIN:VEVENT
        UID:utc@ex
        SUMMARY:Appel avec un très long titre qui se poursuit
          sur la ligne suivante
        DTSTART:20261125T140000Z
        DURATION:PT45M
        END:VEVENT
        BEGIN:VEVENT
        UID:ferie@ex
        SUMMARY:Férié
        DTSTART;VALUE=DATE:20261111
        END:VEVENT
        BEGIN:VEVENT
        UID:annule@ex
        STATUS:CANCELLED
        SUMMARY:Annulé
        DTSTART:20261125T150000Z
        END:VEVENT
        END:VCALENDAR
        """;

    [Fact]
    public void Ics_fuseaux_depliage_duree_et_annulation()
    {
        var evts = Ics.Lire(Calendrier);
        Assert.Equal(4, evts.Count);                                         // l'annulé est écarté
        Assert.Equal("Point d'équipe, hebdo", evts[0].Titre);
        Assert.Equal(new DateTimeOffset(2026, 10, 19, 7, 30, 0, TimeSpan.Zero), evts[0].Debut);  // 9 h 30 à Paris, heure d'été
        Assert.Equal("Appel avec un très long titre qui se poursuit sur la ligne suivante", evts[2].Titre);
        Assert.Equal(TimeSpan.FromMinutes(45), evts[2].Fin - evts[2].Debut);
        Assert.True(evts[3].JourEntier);
    }

    [Fact]
    public void Ics_recurrence_hebdo_exdate_remplacement_et_changement_d_heure()
    {
        var occ = Ics.Occurrences(Ics.Lire(Calendrier), new DateTimeOffset(2026, 10, 1, 0, 0, 0, TimeSpan.Zero),
            new DateTimeOffset(2026, 12, 31, 0, 0, 0, TimeSpan.Zero));
        var points = occ.Where(o => o.Titre.StartsWith("Point")).Select(o => TimeZoneInfo.ConvertTime(o.Debut, Paris).DateTime).ToList();
        // COUNT=6 : lu 19, (je 22 exclu), lu 26 (déplacé à 11 h), je 29, lu 2/11, je 5/11 ; la série compte l'exclu.
        Assert.Equal(new[]
        {
            new DateTime(2026, 10, 19, 9, 30, 0), new DateTime(2026, 10, 26, 11, 0, 0), new DateTime(2026, 10, 29, 9, 30, 0),
            new DateTime(2026, 11, 2, 9, 30, 0), new DateTime(2026, 11, 5, 9, 30, 0),
        }, points);
        // Après le passage à l'heure d'hiver (25 octobre), toujours 9 h 30 à Paris, donc 8 h 30 UTC.
        Assert.Contains(occ, o => o.Debut == new DateTimeOffset(2026, 10, 29, 8, 30, 0, TimeSpan.Zero));
        Assert.DoesNotContain(occ, o => o.Titre == "Férié");                // jour entier : pas une réunion
    }

    [Fact]
    public void Ics_quotidien_until_intervalle()
    {
        var ics = "BEGIN:VEVENT\nUID:q\nSUMMARY:Stand-up\nDTSTART:20261123T080000Z\nDTEND:20261123T081500Z\n" +
                  "RRULE:FREQ=DAILY;INTERVAL=2;UNTIL=20261129T080000Z\nEND:VEVENT";
        var occ = Ics.Occurrences(Ics.Lire(ics), DateTimeOffset.MinValue.AddYears(2000), new DateTimeOffset(2027, 1, 1, 0, 0, 0, TimeSpan.Zero));
        Assert.Equal(new[] { 23, 25, 27, 29 }, occ.Select(o => o.Debut.Day));
    }

    [Fact]
    public void Agenda_previent_avant_puis_se_cache_pendant_la_reunion()
    {
        var a = new ConnecteurAgenda();
        var evts = Ics.Lire(Calendrier);
        var debut = new DateTimeOffset(2026, 11, 25, 14, 0, 0, TimeSpan.Zero);
        var e1 = a.Examiner(evts, debut.AddMinutes(-4.5), 5, true, 0);
        Assert.Equal("▦ Dans 5 min", Assert.Single(e1).Titre);
        Assert.False(ConnecteurAgenda.EnReunion);
        Assert.Empty(a.Examiner(evts, debut.AddMinutes(-3), 5, true, 0)); // une seule fois
        var e2 = a.Examiner(evts, debut.AddSeconds(30), 5, true, 10_000);
        Assert.Equal("agenda:ponctuel", Assert.Single(e2).Donnee("quete"));
        Assert.True(ConnecteurAgenda.EnReunion);
        a.Examiner(evts, debut.AddMinutes(50), 5, true, 0);
        Assert.False(ConnecteurAgenda.EnReunion);
        // Absent du PC au début : pas de quête « ponctuel ».
        Assert.Empty(new ConnecteurAgenda().Examiner(evts, debut.AddSeconds(30), 5, false, 10 * 60_000));
        Assert.False(ConnecteurAgenda.EnReunion);                            // « se cacher » décoché
    }

    // ---- Spotify : PKCE

    [Fact]
    public void Pkce_vecteur_de_la_RFC_7636()
    {
        Assert.Equal("E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM", Pkce.Defi("dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"));
        var v = Pkce.Verificateur();
        Assert.Equal(64, v.Length);
        Assert.Matches("^[A-Za-z0-9._~-]+$", v);
        Assert.NotEqual(v, Pkce.Verificateur());
        var url = ConnecteurSpotify.UrlAutorisation("cid", "http://127.0.0.1:47822/callback", "DEFI", "etat");
        Assert.Contains("code_challenge_method=S256&code_challenge=DEFI", url);
        Assert.Contains("redirect_uri=http%3A%2F%2F127.0.0.1%3A47822%2Fcallback", url);
        Assert.DoesNotContain("secret", url);
    }

    [Fact]
    public void Spotify_lit_le_morceau_en_cours()
    {
        var l = ConnecteurSpotify.LireLecture("""
            {"is_playing":true,"item":{"id":"t1","name":"Clair de lune","artists":[{"name":"Debussy"},{"name":"Pianiste"}]}}
            """);
        Assert.Equal(new LectureSpotify("t1", "Clair de lune", "Debussy, Pianiste", true, 0), l);
        Assert.Null(ConnecteurSpotify.LireLecture("""{"is_playing":false,"item":null}"""));
    }

    // ---- Twitch et YouTube

    [Fact]
    public void Twitch_annonce_seulement_les_passages_en_live()
    {
        var t = new ConnecteurTwitch();
        var lives = ConnecteurTwitch.LireLives("""
            {"data":[{"user_login":"Zevent","user_name":"ZEvent","title":"Marathon","game_name":"Just Chatting"}]}
            """);
        Assert.Empty(t.Comparer(lives));                                     // premier relevé : point de départ
        Assert.Empty(t.Comparer(lives));                                     // toujours en live
        Assert.Empty(t.Comparer(new List<LiveTwitch>()));                    // fini
        var e = Assert.Single(t.Comparer(lives));                            // de retour
        Assert.Equal("▶ ZEvent est en live", e.Titre);
        Assert.Equal("Just Chatting · Marathon", e.Texte);
    }

    [Fact]
    public async Task Twitch_demande_un_jeton_d_application_puis_les_streams()
    {
        var http = new Rejoueur()
            .Puis(_ => Json("""{"access_token":"app","expires_in":5000000,"token_type":"bearer"}"""))
            .Puis(_ => Json("""{"data":[]}"""));
        var t = new ConnecteurTwitch();
        var (_, ctx, _) = Monter(t, http);
        ctx.Ecrire("client", "cid");
        ctx.Ecrire("secret", "sec");
        ctx.Ecrire("chaines", "zevent, Mistermv");
        await t.Sonder(ctx, CancellationToken.None);
        Assert.Equal("https://id.twitch.tv/oauth2/token", http.Requetes[0].RequestUri!.ToString());
        var streams = http.Requetes[1];
        Assert.Equal("https://api.twitch.tv/helix/streams?first=100&user_login=zevent&user_login=mistermv", streams.RequestUri!.ToString());
        Assert.Equal("cid", streams.Headers.GetValues("Client-Id").Single());
        Assert.Equal("app", streams.Headers.Authorization!.Parameter);
    }

    [Fact]
    public void YouTube_lit_le_flux_RSS_de_la_chaine()
    {
        var v = ConnecteurYouTube.LireFlux("""
            <?xml version="1.0" encoding="UTF-8"?>
            <feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
             <title>Chaîne</title>
             <entry><yt:videoId>abc123</yt:videoId><title>Nouvelle vidéo</title><author><name>Ma chaîne</name></author>
              <published>2026-11-25T08:00:00+00:00</published></entry>
            </feed>
            """);
        Assert.Equal(new VideoYouTube("abc123", "Nouvelle vidéo", "Ma chaîne", new DateTimeOffset(2026, 11, 25, 8, 0, 0, TimeSpan.Zero)), Assert.Single(v));
        Assert.Empty(ConnecteurYouTube.LireFlux("pas du xml"));
    }

    // ---- Home Assistant

    [Fact]
    public void HomeAssistant_auth_abonnement_et_filtre_des_entites()
    {
        Assert.Equal("ws://homeassistant.local:8123/api/websocket", ProtocoleHomeAssistant.Adresse("http://homeassistant.local:8123/"));
        Assert.Equal("wss://maison.exemple.fr/ha/api/websocket", ProtocoleHomeAssistant.Adresse("https://maison.exemple.fr/ha"));
        var p = new ProtocoleHomeAssistant("LONG", new[] { "binary_sensor.porte" });
        var auth = JsonNode.Parse(Assert.Single(p.Recevoir("""{"type":"auth_required","ha_version":"2026.11"}""").AEnvoyer))!;
        Assert.Equal("auth", (string)auth["type"]!);
        Assert.Equal("LONG", (string)auth["access_token"]!);
        var sub = JsonNode.Parse(Assert.Single(p.Recevoir("""{"type":"auth_ok"}""").AEnvoyer))!;
        Assert.Equal("subscribe_events", (string)sub["type"]!);
        Assert.Equal("state_changed", (string)sub["event_type"]!);
        p.Recevoir("""{"id":1,"type":"result","success":true,"result":null}""");
        Assert.True(p.Abonne);

        string Evt(string id, string avant, string apres) => new JsonObject
        {
            ["id"] = 1, ["type"] = "event",
            ["event"] = new JsonObject
            {
                ["event_type"] = "state_changed",
                ["data"] = new JsonObject
                {
                    ["entity_id"] = id,
                    ["old_state"] = new JsonObject { ["state"] = avant },
                    ["new_state"] = new JsonObject { ["state"] = apres, ["attributes"] = new JsonObject { ["friendly_name"] = "Porte d'entrée" } },
                },
            },
        }.ToJsonString();
        var c = p.Recevoir(Evt("binary_sensor.porte", "off", "on")).Changement;
        Assert.Equal("Porte d'entrée", c!.Nom);
        Assert.Equal("allumé", ProtocoleHomeAssistant.Etat(c.Apres));
        Assert.Null(p.Recevoir(Evt("light.salon", "off", "on")).Changement);      // entité non suivie
        Assert.Null(p.Recevoir(Evt("binary_sensor.porte", "on", "on")).Changement); // attribut seul
        Assert.Throws<InvalidOperationException>(() => new ProtocoleHomeAssistant("x", Array.Empty<string>()).Recevoir("""{"type":"auth_invalid"}"""));
    }

    // ---- Registre : nouvelles du téléphone, sorties

    private sealed class SortieTest : Connecteur
    {
        public readonly List<EvenementPilou> Sortis = new();
        public override string Id => "sortie-test";
        public override string Nom => "Sortie";
        public override string Description => "";
        public override ModeConnecteur Mode => ModeConnecteur.Passif;
        public override bool Sortie => true;

        public override Task Sortir(ContexteConnecteur ctx, EvenementPilou e, CancellationToken ct)
        {
            lock (Sortis) Sortis.Add(e);
            return Task.CompletedTask;
        }
    }

    [Fact]
    public void Registre_garde_5_annonces_horodatees_et_ne_publie_que_vers_les_sorties_actives()
    {
        var r = new Registre(new ReglagesConnecteurs(), new CoffreMemoire(), () => { });
        for (int i = 0; i < 8; i++) r.Recevoir(new EvenementPilou("mail", "notification", "✉ n" + i, "sujet"));
        r.Recevoir(new EvenementPilou("meteo", "meteo", "pluie"));
        r.Recevoir(new EvenementPilou("api", "session", "s"));
        var an = r.Annonces();
        Assert.Equal(Registre.TailleAnnonces, an.Count);
        Assert.Equal("✉ n7", an[0].Titre);
        Assert.True(an[0].T > 0);
        var tel = Telephone.Annonces(an, masquer: true);
        Assert.Equal("", tel[0]["texte"]);
        Assert.Equal("✉ n7", tel[0]["titre"]);

        var s = new SortieTest();
        r.Ajouter(s);
        r.Publier(new EvenementPilou("pilou", "notification", "⏳ Une IA t'attend"));
        Thread.Sleep(200);
        Assert.Empty(s.Sortis);                                               // pas activée : rien ne sort
        r.Activer(s, true);
        r.Publier(new EvenementPilou("pilou", "notification", "✦ Quête réussie"));
        SpinWait.SpinUntil(() => { lock (s.Sortis) return s.Sortis.Count > 0; }, 20_000);
        Assert.Equal("✦ Quête réussie", Assert.Single(s.Sortis).Titre);
    }
}
