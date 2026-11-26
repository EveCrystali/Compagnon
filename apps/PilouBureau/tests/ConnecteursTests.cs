using System.Net;
using System.Net.Http;
using System.Net.Sockets;
using System.Text;
using PilouBureau;
using Xunit;

// Météo : décodage Open-Meteo (réponses enregistrées), état, effets selon l'équipement, quêtes, offre parapluie.
public class MeteoTests
{
    private static readonly Lazy<Banque> B = new(() =>
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d is not null && !File.Exists(Path.Combine(d.FullName, "assets", "index.txt"))) d = d.Parent;
        return Banque.DepuisDossier(Path.Combine(d!.FullName, "assets"));
    });

    private const string Pluie = """
        {"latitude":48.86,"longitude":2.34,"current_units":{"temperature_2m":"°C"},
         "current":{"time":"2026-11-26T09:15","interval":900,"temperature_2m":8.4,"precipitation":1.2,"rain":1.2,"snowfall":0.0,
                    "weather_code":63,"wind_speed_10m":14.8,"is_day":1}}
        """;
    private const string Neige = """{"current":{"temperature_2m":-1.5,"precipitation":0.4,"rain":0,"snowfall":0.7,"weather_code":73,"wind_speed_10m":9,"is_day":0}}""";
    private const string Canicule = """{"current":{"temperature_2m":33.1,"precipitation":0,"rain":0,"snowfall":0,"weather_code":0,"wind_speed_10m":6,"is_day":1}}""";
    private const string Orage = """{"current":{"temperature_2m":21,"precipitation":4,"rain":4,"snowfall":0,"weather_code":95,"wind_speed_10m":30,"is_day":1}}""";
    private const string Villes = """
        {"results":[{"id":2988507,"name":"Paris","latitude":48.85341,"longitude":2.3488,"country":"France","admin1":"Île-de-France"},
                    {"id":4717560,"name":"Paris","latitude":33.66094,"longitude":-95.55551,"country":"États-Unis","admin1":"Texas"}]}
        """;

    [Fact]
    public void Decodage_open_meteo()
    {
        var r = Meteo.Lire(Pluie)!;
        Assert.Equal(8.4, r.Temperature, 1);
        Assert.Equal(63, r.Code);
        Assert.True(r.Jour);
        Assert.False(Meteo.Lire(Neige)!.Jour);
        Assert.Null(Meteo.Lire("{\"erreur\":true}"));
        Assert.Null(Meteo.Lire("pas du json"));
    }

    [Theory]
    [InlineData(63, 8, 0, 0, 10, Meteo.Pluie)]
    [InlineData(81, 12, 2, 0, 10, Meteo.Averse)]
    [InlineData(95, 20, 4, 0, 10, Meteo.Orage)]
    [InlineData(73, -1, 0, 0.7, 5, Meteo.Neige)]
    [InlineData(45, 6, 0, 0, 5, Meteo.Brouillard)]
    [InlineData(1, 12, 0, 0, 55, Meteo.Vent)]
    [InlineData(0, 33, 0, 0, 5, Meteo.Chaleur)]
    [InlineData(0, 1, 0, 0, 5, Meteo.Froid)]
    [InlineData(3, 15, 0, 0, 5, Meteo.Nuageux)]
    [InlineData(0, 15, 0, 0, 5, Meteo.Degage)]
    [InlineData(2, 15, 0.5, 0, 5, Meteo.Pluie)]   // il pleut même si le code dit « nuageux »
    public void Etat_selon_le_releve(int code, double temp, double pluie, double neige, double vent, string attendu) =>
        Assert.Equal(attendu, Meteo.Etat(new Releve(temp, pluie + neige, pluie, neige, code, vent, true)));

    [Fact]
    public void Mouille_sans_parapluie_au_sec_avec()
    {
        var sans = Meteo.Effet(Meteo.Pluie, new[] { "casquette" });
        Assert.Equal("mouille", sans.Inconfort);
        Assert.False(sans.Protege);
        Assert.Contains("meteo-mouille", sans.Sprites);
        Assert.Contains("meteo-pluie", sans.Sprites);

        foreach (var abri in new[] { "parapluie", "parapluie-etoile", "impermeable" })
        {
            var avec = Meteo.Effet(Meteo.Pluie, new[] { abri });
            Assert.True(avec.Protege);
            Assert.Equal("", avec.Inconfort);
            Assert.DoesNotContain("meteo-mouille", avec.Sprites);
            Assert.Equal(0, avec.Tremble);
        }
        var orage = Meteo.Effet(Meteo.Orage, Array.Empty<string>());
        Assert.Contains("meteo-eclair", orage.Sprites);
        Assert.Contains("meteo-averse", orage.Sprites);
    }

    [Fact]
    public void Froid_et_chaleur_selon_l_equipement()
    {
        Assert.Equal("froid", Meteo.Effet(Meteo.Neige, Array.Empty<string>()).Inconfort);
        Assert.Contains("meteo-givre", Meteo.Effet(Meteo.Neige, Array.Empty<string>()).Sprites);
        Assert.True(Meteo.Effet(Meteo.Neige, new[] { "acc-bonnet" }).Protege);
        Assert.True(Meteo.Effet(Meteo.Froid, new[] { "moufles" }).Protege);
        var chaud = Meteo.Effet(Meteo.Chaleur, Array.Empty<string>());
        Assert.Equal("sueur", chaud.Reaction);
        Assert.Equal("chaud", chaud.Inconfort);
        Assert.True(Meteo.Effet(Meteo.Chaleur, new[] { "eventail" }).Protege);
        Assert.True(Meteo.Effet(Meteo.Chaleur, new[] { "acc-lunettes" }).Protege);
        Assert.Same(EffetMeteo.Aucun, Meteo.Effet(Meteo.Degage, Array.Empty<string>()));
        Assert.Same(EffetMeteo.Aucun, Meteo.Effet(null, Array.Empty<string>()));
    }

    [Fact]
    public void EstMouille_lit_la_meteo_courante()
    {
        var avant = Meteo.Courante;
        try
        {
            Meteo.Courante = new Meteo.Situation(Meteo.Pluie, Meteo.Lire(Pluie)!, "Paris", DateTime.Now);
            Assert.True(Meteo.EstMouille(new[] { "echarpe" }));
            Assert.False(Meteo.EstMouille(new[] { "parapluie" }));
            Meteo.Courante = null;
            Assert.False(Meteo.EstMouille(Array.Empty<string>()));
        }
        finally
        {
            Meteo.Courante = avant;
        }
    }

    [Fact]
    public void Phrases_raleuses_et_contentes()
    {
        var mouille = Meteo.Effet(Meteo.Pluie, Array.Empty<string>());
        var sec = Meteo.Effet(Meteo.Pluie, new[] { "parapluie" });
        Assert.NotEqual("", Meteo.Phrase(Meteo.Pluie, mouille, 3));
        Assert.NotEqual(Meteo.Phrase(Meteo.Pluie, mouille, 0), Meteo.Phrase(Meteo.Pluie, sec, 0));
        Assert.Equal("", Meteo.Phrase(Meteo.Degage, EffetMeteo.Aucun, 0));
    }

    [Fact]
    public void Villes_et_adresses()
    {
        var v = Meteo.LireVilles(Villes);
        Assert.Equal(2, v.Count);
        Assert.Equal("Paris (Île-de-France, France)", v[0].Libelle);
        Assert.Empty(Meteo.LireVilles("{}"));
        Assert.Contains("latitude=48.8534&longitude=2.3488", Meteo.UrlPrevision(48.85341, 2.3488));
        Assert.Contains("name=Saint-%C3%89tienne", Meteo.UrlRecherche("Saint-Étienne"));
    }

    [Fact]
    public void Quete_meteo_bonus_une_fois_par_jour_et_hors_coffre()
    {
        var e = new EtatQuetes();
        var jour = new DateTime(2026, 11, 26, 10, 0, 0);
        var q = Quetes.AjouterMeteo(e, Meteo.Pluie, jour, "pc");
        Assert.NotNull(q);
        Assert.True(q!.Bonus);
        Assert.Equal("meteo:sec", q.Cle);
        Assert.Null(Quetes.AjouterMeteo(e, Meteo.Averse, jour, "pc"));    // déjà là
        Assert.Null(Quetes.AjouterMeteo(e, Meteo.Degage, jour, "pc"));    // rien à faire par beau temps
        // Les trois quotidiennes ordinaires ouvrent le coffre, même si la quête météo n'est pas faite.
        foreach (var x in e.Liste.Where(x => x.Periode == Periode.Jour && !x.Bonus)) x.Fait = x.Objectif - 1;
        var gains = new List<RecompenseQuete>();
        foreach (var x in e.Liste.Where(x => x.Periode == Periode.Jour && !x.Bonus).ToList())
            gains.AddRange(Quetes.Signaler(e, x.Cle, x.Cle == "presence" ? 30 : x.Cle == "chasse" ? x.Objectif : 1, jour, "pc"));
        Assert.Contains(gains, g => g.Coffre);
        // Trente minutes au sec : la quête météo est réussie.
        var r = Quetes.Signaler(e, "meteo:sec", 30, jour, "pc");
        Assert.Contains(r, g => g.Texte.Contains("au sec"));
        // Le lendemain, elle disparaît avec les autres quotidiennes.
        Quetes.Actualiser(e, jour.AddDays(1), "pc");
        Assert.DoesNotContain(e.Liste, x => x.Cle == "meteo:sec");
    }

    [Fact]
    public void Le_parapluie_s_invite_dans_les_offres_quand_il_pleut()
    {
        var avant = Boutique.Pluie;
        try
        {
            var jour = new DateOnly(2026, 11, 26);
            Boutique.Pluie = () => false;
            var sec = Boutique.OffresDuJour(jour);
            Boutique.Pluie = () => true;
            var pluie = Boutique.OffresDuJour(jour);
            Assert.Contains(pluie, a => a.Id == "parapluie");
            Assert.Equal(Math.Min(4, sec.Count), pluie.Count);
        }
        finally
        {
            Boutique.Pluie = avant;
        }
    }

    [Fact]
    public void Nouveaux_objets_meteo_au_catalogue_et_dessines()
    {
        foreach (var (id, slot) in new[] { ("impermeable", Boutique.Dos), ("bottes-pluie", Boutique.Pieds), ("moufles", Boutique.Main),
                     ("eventail", Boutique.Main), ("parapluie-etoile", Boutique.Main) })
        {
            var a = Boutique.Trouver(id);
            Assert.NotNull(a);
            Assert.Equal(slot, a!.Slot);
            Assert.NotNull(B.Value[id]);
        }
        foreach (var id in new[] { "meteo-pluie", "meteo-averse", "meteo-eclair", "meteo-mouille", "meteo-neige", "meteo-givre",
                     "meteo-soleil", "meteo-vent", "meteo-brouillard" })
            Assert.NotNull(B.Value[id]);
        Assert.Contains(Boutique.Pieds, Boutique.Slots);
        var b = new Bourse();
        b.Inventaire.Add("bottes-pluie");
        Assert.True(Boutique.Equiper(b, Boutique.Pieds, "bottes-pluie", 1));
    }

    [Fact]
    public void Pilou_mouille_est_dessine_differemment()
    {
        var sec = RenduPilou.Rendre(new Allure { Objets = new[] { "parapluie", "meteo-pluie" } }, B.Value);
        var mouille = RenduPilou.Rendre(new Allure { Objets = new[] { "meteo-pluie", "meteo-mouille" } }, B.Value);
        Assert.NotEqual(sec, mouille);
    }
}

// Socle des connecteurs : événements, registre, journal, secrets.
public class ConnecteursTests
{
    private sealed class Sonde : Connecteur
    {
        public int Releves;
        public override string Id => "sonde";
        public override string Nom => "Sonde";
        public override string Description => "test";
        public override TimeSpan Intervalle => TimeSpan.FromMinutes(5);
        public override IReadOnlyList<ReglageConnecteur> Reglages { get; } = new[]
        {
            new ReglageConnecteur("hote", "Hôte", TypeReglage.Texte, Defaut: "exemple.fr"),
            new ReglageConnecteur("jeton", "Jeton", TypeReglage.Secret),
        };

        public override string? Manque(ContexteConnecteur ctx) => ctx.Lire("jeton") == "" ? "jeton manquant" : null;

        public override Task Sonder(ContexteConnecteur ctx, CancellationToken ct)
        {
            Releves++;
            ctx.Emettre(new EvenementPilou("sonde", "notification", "relevé " + Releves));
            return Task.CompletedTask;
        }
    }

    [Fact]
    public void Evenement_lu_et_valide()
    {
        var e = EvenementPilou.Lire("""{"source":"mon-script","type":"notification","titre":"Build fini","texte":"12 tests","gravite":1,"donnees":{"duree":"42s"}}""", 1000, out var err)!;
        Assert.Equal("", err);
        Assert.Equal("monscript", e.Source);
        Assert.Equal(1, e.Gravite);
        Assert.Equal("42s", e.Donnee("duree"));
        Assert.Equal(1000, e.T);
        Assert.Null(EvenementPilou.Lire("""{"source":"x","type":"bidule","titre":"t"}""", 0, out err));
        Assert.Contains("type", err);
        Assert.Null(EvenementPilou.Lire("""{"type":"message","titre":"t"}""", 0, out err));
        Assert.Null(EvenementPilou.Lire("""{"source":"x","type":"message"}""", 0, out err));
        Assert.Null(EvenementPilou.Lire("[1,2]", 0, out err));
        var long_ = EvenementPilou.Lire("{\"source\":\"x\",\"type\":\"message\",\"titre\":\"" + new string('a', 2000) + "\"}", 0, out _)!;
        Assert.Equal(300, long_.Titre.Length);
        var relu = EvenementPilou.Lire(e.Json(), 1000, out _);
        Assert.Equal(e.Titre, relu!.Titre);
    }

    [Fact]
    public void Registre_releve_journal_et_secrets()
    {
        var reglages = new ReglagesConnecteurs();
        var coffre = new CoffreMemoire();
        int sauvegardes = 0;
        var r = new Registre(reglages, coffre, () => sauvegardes++);
        var recus = new List<EvenementPilou>();
        r.Evenement += recus.Add;
        var s = new Sonde();
        r.Ajouter(s);
        var ctx = r.Contexte(s);
        Assert.Equal("exemple.fr", ctx.Lire("hote"));
        Assert.Equal(EtatConnecteur.Desactive, r.Etat(s));
        r.Activer(s, true);
        Assert.Equal(EtatConnecteur.AConfigurer, r.Etat(s));
        r.Battre();
        Assert.Equal(0, s.Releves);                         // pas de jeton : rien ne part

        r.Regler("sonde", "jeton", "s3cr3t");
        Assert.Equal("s3cr3t", ctx.Lire("jeton"));
        Assert.Equal("s3cr3t", coffre.Valeurs["sonde.jeton"]);
        Assert.False(reglages.Valeurs.TryGetValue("sonde", out var v) && v.ContainsKey("jeton")); // jamais dans reglages.json

        r.Battre();
        SpinWait.SpinUntil(() => s.Releves == 1, 2000);
        Assert.Equal(1, s.Releves);
        SpinWait.SpinUntil(() => recus.Count == 1, 2000);
        Assert.Equal("relevé 1", recus.Single().Titre);
        Assert.Equal(EtatConnecteur.Actif, r.Etat(s));
        r.Battre();                                           // pas encore dû (5 min)
        Thread.Sleep(50);
        Assert.Equal(1, s.Releves);
        Assert.Equal("relevé 1", r.Dernier("sonde")!.Titre);
        Assert.Contains(r.Journal(), l => l.Texte.Contains("relevé 1"));
        Assert.True(sauvegardes > 0);
    }

    [Fact]
    public void Journal_borne_a_50_lignes()
    {
        var r = new Registre(new ReglagesConnecteurs(), new CoffreMemoire(), () => { });
        for (int i = 0; i < 80; i++) r.Recevoir(new EvenementPilou("x", "message", "n" + i));
        var j = r.Journal();
        Assert.Equal(Registre.TailleJournal, j.Count);
        Assert.Contains("n79", j[0].Texte);
    }

    private sealed class Panne : Connecteur
    {
        public override string Id => "panne";
        public override string Nom => "Panne";
        public override string Description => "";
        public override bool ActifParDefaut => true;
        public override Task Sonder(ContexteConnecteur ctx, CancellationToken ct) => throw new HttpRequestException("non");
    }

    [Fact]
    public void Un_connecteur_en_panne_passe_en_erreur_sans_rien_casser()
    {
        var r = new Registre(new ReglagesConnecteurs(), new CoffreMemoire(), () => { });
        var p = new Panne();
        r.Ajouter(p);
        r.Battre();
        SpinWait.SpinUntil(() => r.Etat(p) == EtatConnecteur.Erreur, 2000);
        Assert.Equal(EtatConnecteur.Erreur, r.Etat(p));
        Assert.Equal("service injoignable", r.Erreur("panne"));
    }

    [Fact]
    public void Connecteur_integre_suit_le_reglage_d_origine()
    {
        bool actif = false;
        var c = new ConnecteurIntegre("activites", "Activités", "", "▣", () => actif, v => actif = v);
        var r = new Registre(new ReglagesConnecteurs(), new CoffreMemoire(), () => { });
        r.Ajouter(c);
        Assert.False(r.Actif(c));
        r.Activer(c, true);
        Assert.True(actif);
        Assert.True(r.Actif(c));
        actif = false;                                       // coupé ailleurs (menu Activités)
        Assert.False(r.Actif(c));
    }

    [Fact]
    public void Connecteur_meteo_applique_un_releve_et_emet_au_changement()
    {
        var avant = Meteo.Courante;
        try
        {
            Meteo.Courante = null;
            var r = new Registre(new ReglagesConnecteurs(), new CoffreMemoire(), () => { });
            var recus = new List<EvenementPilou>();
            r.Evenement += recus.Add;
            var m = new ConnecteurMeteo();
            r.Ajouter(m);
            var ctx = r.Contexte(m);
            Assert.NotNull(m.Manque(ctx));
            ctx.Ecrire("ville", "Paris");
            ctx.Ecrire("latitude", "48.85");
            ctx.Ecrire("longitude", "2.35");
            Assert.Null(m.Manque(ctx));
            m.Appliquer(ctx, """{"current":{"temperature_2m":8,"rain":1.2,"weather_code":63,"wind_speed_10m":10,"is_day":1}}""");
            Assert.Equal(Meteo.Pluie, Meteo.Courante!.Etat);
            Assert.Single(recus);
            Assert.Equal("meteo", recus[0].Type);
            Assert.Equal("pluie", recus[0].Donnee("etat"));
            m.Appliquer(ctx, """{"current":{"temperature_2m":9,"rain":0.8,"weather_code":61,"wind_speed_10m":10,"is_day":1}}""");
            Assert.Single(recus);                              // toujours la pluie : pas de nouvel événement
        }
        finally
        {
            Meteo.Courante = avant;
        }
    }
}

// API locale : jeton, refus des pages web, routes ; et une vraie connexion sur 127.0.0.1.
public class ApiLocaleTests
{
    private static ApiLocale Api(List<EvenementPilou> recus) =>
        new(() => "abc123", () => """{"niveau":3}""", recus.Add, () => 42);

    private static Dictionary<string, string> Entetes(string? jeton = "abc123") =>
        jeton is null ? new() : new() { ["Authorization"] = "Bearer " + jeton };

    [Fact]
    public void Jeton_obligatoire()
    {
        var api = Api(new());
        Assert.Equal(401, api.Traiter("GET", "/etat", Entetes(null), "").Code);
        Assert.Equal(401, api.Traiter("GET", "/etat", Entetes("faux"), "").Code);
        Assert.Equal(200, api.Traiter("GET", "/etat", Entetes(), "").Code);
    }

    [Fact]
    public void Page_web_refusee()
    {
        var e = Entetes();
        e["Origin"] = "https://exemple.fr";
        Assert.Equal(403, Api(new()).Traiter("POST", "/evenements", e, "{}").Code);
    }

    [Fact]
    public void Evenement_poste()
    {
        var recus = new List<EvenementPilou>();
        var api = Api(recus);
        var (code, _) = api.Traiter("POST", "/evenements", Entetes(), """{"source":"ci","type":"fin","titre":"Build nocturne"}""");
        Assert.Equal(202, code);
        Assert.Equal("Build nocturne", recus.Single().Titre);
        Assert.Equal(42, recus.Single().T);
        Assert.Equal(400, api.Traiter("POST", "/evenements", Entetes(), "{\"source\":\"ci\"}").Code);
        Assert.Equal(405, api.Traiter("DELETE", "/etat", Entetes(), "").Code);
        Assert.Equal(404, api.Traiter("GET", "/ailleurs", Entetes(), "").Code);
    }

    [Fact]
    public async Task Vraie_connexion_en_boucle_locale()
    {
        var recus = new List<EvenementPilou>();
        using var api = Api(recus);
        Assert.True(api.Demarrer(0));                  // port libre choisi par le système
        using var http = new HttpClient();
        http.DefaultRequestHeaders.Add("Authorization", "Bearer abc123");
        var etat = await http.GetStringAsync($"http://127.0.0.1:{api.Port}/etat");
        Assert.Equal("""{"niveau":3}""", etat);
        var r = await http.PostAsync($"http://127.0.0.1:{api.Port}/evenements",
            new StringContent("""{"source":"script","type":"message","titre":"coucou"}""", Encoding.UTF8, "application/json"));
        Assert.Equal(HttpStatusCode.Accepted, r.StatusCode);
        Assert.Equal("coucou", recus.Single().Titre);
        using var sans = new HttpClient();
        Assert.Equal(HttpStatusCode.Unauthorized, (await sans.GetAsync($"http://127.0.0.1:{api.Port}/etat")).StatusCode);
    }

    [Fact]
    public void Ecoute_seulement_en_boucle_locale()
    {
        using var api = Api(new());
        Assert.True(api.Demarrer(0));
        // Joindre le port par une autre adresse de la machine échoue : la socket n'écoute que sur 127.0.0.1.
        var autres = Dns.GetHostAddresses(Dns.GetHostName()).Where(a => a.AddressFamily == AddressFamily.InterNetwork && !IPAddress.IsLoopback(a)).ToList();
        foreach (var a in autres)
        {
            using var c = new TcpClient();
            Assert.ThrowsAny<SocketException>(() => c.Connect(a, api.Port));
        }
    }
}
