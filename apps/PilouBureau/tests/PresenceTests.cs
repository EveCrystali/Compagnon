using System.Globalization;
using System.Text;
using PilouBureau;
using Xunit;
using Xunit.Abstractions;

// La présence de Pilou au quotidien (docs/PRESENCE.md) : banque de mots, rythme, complicité, journal, prénom.
// Les vecteurs partagés (PresenceVecteurs, plus bas) prouvent que le téléphone calcule exactement la même chose.
public class PresenceTests
{
    private readonly ITestOutputHelper _sortie;

    public PresenceTests(ITestOutputHelper sortie) => _sortie = sortie;

    private static readonly CultureInfo Ci = CultureInfo.InvariantCulture;
    private static readonly IReadOnlyDictionary<string, int> Rien = new Dictionary<string, int>();

    // ---- Banque

    [Fact]
    public void La_banque_a_plus_de_400_mots_courts_et_sans_reproche()
    {
        var mots = Presence.Mots;
        Assert.True(mots.Count >= 400, $"{mots.Count} mots");
        Assert.All(mots, l => Assert.True(l.Texte.Length <= Presence.LongueurMax, $"trop long ({l.Texte.Length}) : {l.Texte}"));
        Assert.Equal(mots.Count, mots.Select(l => l.Id).Distinct().Count());
        // Jamais de reproche, d'injonction ni de culpabilité.
        string[] interdits = { "abandonn", "tu m'as laissé", "tu devrais", "il faut que tu", "dépêche", "travaille plus", "où étais-tu", "enfin te voilà" };
        Assert.All(mots, l => Assert.DoesNotContain(interdits, i => l.Texte.Contains(i, StringComparison.OrdinalIgnoreCase)));
        // Rien de personnel dans les trous : seulement ceux que le moteur sait remplir.
        string[] trous = { "prenom", "metier", "niveau", "objet", "prise", "plat", "jours", "annees", "palier" };
        Assert.All(mots, l => Assert.All(l.Trous, t => Assert.Contains(t, trous)));
    }

    [Fact]
    public void Chaque_famille_du_plan_a_au_moins_trois_lignes()
    {
        var familles = Presence.Mots.GroupBy(l => l.Famille).ToDictionary(g => g.Key, g => g.Count());
        var attendues = new List<string>
        {
            "bonjour", "retour-nuit", "lundi", "weekend", "retour-1h", "retour-jours", "retour-weekend", "retour-semaine", "retour-long",
            "fin-seance", "soir", "vendredi", "tard", "pensee", "tel-soir", "metier", "niveau", "objet", "souvenir-prise", "souvenir-plat",
            "prenom-demande", "prenom-merci", "prenom-refus", "date-a", "date-m1", "date-m6",
        };
        attendues.AddRange(new[] { "hiver", "printemps", "ete", "automne" }.Select(s => "saison-" + s));
        attendues.AddRange(Presence.MeteosNotables.Select(m => "meteo-" + m));
        attendues.AddRange(Presence.Curiosites.Select(c => "curiosite-" + c));
        attendues.AddRange(Presence.PaliersJours.Select(j => "date-j" + j));
        attendues.AddRange(Enumerable.Range(1, 4).Select(p => "palier-" + p));
        attendues.AddRange(Campagnes.Disponibles().Select(c => "souvenir-" + c));
        for (int m = 1; m <= 12; m++)
            for (int j = 1; j <= 31; j++)
                if (Presence.Fete(m, j) is { Length: > 0 } f) attendues.Add("fete-" + f);
        foreach (var f in attendues.Distinct())
            Assert.True(familles.GetValueOrDefault(f) >= 3, $"famille {f} : {familles.GetValueOrDefault(f)} ligne(s)");
    }

    [Fact]
    public void Les_gabarits_du_journal_couvrent_tous_les_sujets()
    {
        var g = Presence.Gabarits.GroupBy(l => l.Famille).ToDictionary(x => x.Key, x => x.Count());
        foreach (var f in new[] { "j-campagne", "j-niveau", "j-metier", "j-prise-rare", "j-visite", "j-expedition", "j-plat", "j-objet", "j-jeux",
                     "j-jeu", "j-caresses", "j-caresse", "j-soins", "j-peche", "j-quetes", "j-travail-long", "j-tard", "j-aventure", "j-calme", "j-mot", "j-fin" })
            Assert.True(g.GetValueOrDefault(f) >= 4, $"{f} : {g.GetValueOrDefault(f)}");
        foreach (var a in new[] { "code", "tableur", "texte", "mail", "visio", "diaporama", "musique", "video", "lecture", "dessin", "jeu" })
        {
            Assert.True(g.GetValueOrDefault("j-act-" + a) >= 4, a);
            Assert.True(g.GetValueOrDefault("mot-" + a) >= 5, "mot-" + a);
        }
        foreach (var m in Presence.MeteosNotables) Assert.True(g.GetValueOrDefault("j-meteo-" + m) >= 3, m);
    }

    // ---- Choix

    [Fact]
    public void Jamais_deux_fois_la_meme_ligne_avant_que_toute_la_famille_soit_passee()
    {
        var qui = new Presence.Qui(0, 2, "");
        var dits = new Dictionary<string, int>();
        var famille = Presence.Mots.Where(l => l.Famille == "bonjour" && l.Palier == 0 && l.Stades == "" && l.Variante == "" && l.Trous.Count == 0).ToList();
        var vus = new List<string>();
        for (int jour = 20000; jour < 20000 + famille.Count; jour++)
        {
            var l = Presence.Choisir(Presence.Mots, "bonjour", qui, new Dictionary<string, string>(), dits, $"{jour}|pc-1|bonjour")!;
            vus.Add(l.Id);
            Presence.Retenir(dits, l.Id, jour);
        }
        Assert.Equal(famille.Count, vus.Distinct().Count());
        // Ensuite, une ligne ne revient qu'après les plus récentes : jamais une des dix dernières.
        for (int jour = 30000; jour < 30060; jour++)
        {
            var l = Presence.Choisir(Presence.Mots, "bonjour", qui, new Dictionary<string, string>(), dits, $"{jour}|pc-1|bonjour")!;
            var recents = dits.OrderByDescending(kv => kv.Value).Take(10).Select(kv => kv.Key).ToList();
            Assert.DoesNotContain(l.Id, recents);
            Presence.Retenir(dits, l.Id, jour);
        }
    }

    [Fact]
    public void Meme_graine_meme_mot_et_graines_differentes_mots_varies()
    {
        var c = Ctx(new DateTime(2026, 11, 25, 9, 5, 0), Presence.Moment.Premier, absence: 700);
        var a = Presence.Mot(c, Presence.Mots, Rien, "2026-11-25|pc-1|1");
        var b = Presence.Mot(c, Presence.Mots, Rien, "2026-11-25|pc-1|1");
        Assert.Equal(a, b);
        var textes = Enumerable.Range(0, 60).Select(i => Presence.Mot(c, Presence.Mots, Rien, $"2026-11-{i}|pc-1|1")!.Texte).Distinct().Count();
        Assert.True(textes > 20, $"{textes} mots différents");
    }

    [Fact]
    public void Le_prenom_ne_vient_qu_avec_parcimonie_et_jamais_sans_permission()
    {
        int avec = 0, n = 400;
        for (int i = 0; i < n; i++)
        {
            var c = Ctx(new DateTime(2026, 11, 25, 15, 0, 0), Presence.Moment.Retour, palier: 3, prenom: "Lou");
            var m = Presence.Mot(c, Presence.Mots, Rien, $"g{i}")!;
            if (m.Texte.Contains("Lou")) avec++;
        }
        Assert.InRange(avec, 1, n / 5);
        var sans = Ctx(new DateTime(2026, 11, 25, 15, 0, 0), Presence.Moment.Retour, palier: 3);
        for (int i = 0; i < 200; i++) Assert.DoesNotContain("{", Presence.Mot(sans, Presence.Mots, Rien, $"g{i}")!.Texte);
    }

    [Fact]
    public void Les_familles_suivent_le_moment()
    {
        string F(Presence.Contexte c) => Presence.Mot(c, Presence.Mots, Rien, "x")!.Famille;
        var lundi = new DateTime(2026, 11, 23, 9, 0, 0);
        Assert.Equal("retour-semaine", F(Ctx(lundi, Presence.Moment.Premier, absence: 8 * 1440, palier: 1)));
        Assert.Equal("retour-weekend", F(Ctx(lundi, Presence.Moment.Premier, absence: 62 * 60)));
        Assert.Equal("lundi", F(Ctx(lundi, Presence.Moment.Premier, absence: 600)));
        Assert.Equal("date-j7", F(Ctx(lundi, Presence.Moment.Premier, absence: 600) with { DateAFeter = "j7" }));
        Assert.Equal("palier-2", F(Ctx(lundi, Presence.Moment.Premier, absence: 600, palier: 2) with { PalierNouveau = 2 }));
        Assert.Equal("fete-noel", F(Ctx(new DateTime(2026, 12, 25, 10, 0, 0), Presence.Moment.Premier, absence: 600)));
        Assert.Equal("vendredi", F(Ctx(new DateTime(2026, 11, 27, 18, 30, 0), Presence.Moment.Soir)));
        Assert.Equal("tard", F(Ctx(new DateTime(2026, 11, 25, 22, 40, 0), Presence.Moment.Soir)));
        Assert.Equal("prenom-demande", F(Ctx(lundi.AddHours(5), Presence.Moment.Retour, palier: 1) with { DemanderPrenom = true }));
        // Un souvenir de campagne ne vient qu'une fois copains et la campagne finie.
        var souv = Enumerable.Range(0, 300).Select(i => Presence.Mot(Ctx(lundi.AddHours(5), Presence.Moment.Retour, palier: 0) with { Souvenir = "phare-eteint" },
            Presence.Mots, Rien, "s" + i)!.Famille).ToList();
        Assert.DoesNotContain("souvenir-phare-eteint", souv);
    }

    // ---- Rythme (PC)

    private const long H = 3_600_000, M = 60_000;

    private static (int Dits, List<Presence.Moment> Moments) Journee(string parle, Func<long, bool> calme, IEnumerable<(long De, long A)> presences, DateTime jour)
    {
        var r = new Cadence { Jour = "2026-11-01", DerniereVue = 1 };
        var l = new List<Presence.Moment>();
        long t0 = new DateTimeOffset(jour.Date).ToUnixTimeMilliseconds();
        foreach (var (de, a) in presences)
            for (long t = de; t < a; t += 30_000)
            {
                var local = jour.Date.AddMilliseconds(t);
                Cadences.Observer(r, t0 + t, local, true);
                if (Cadences.Pret(r, t0 + t, parle, calme(t)) is { } m)
                {
                    l.Add(m);
                    Cadences.Noter(r, t0 + t, m);
                }
            }
        return (r.Dits, l);
    }

    // Une journée de bureau hachée : arrivée, pauses, déjeuner, retours, soirée.
    private static readonly (long, long)[] Hachee =
    {
        (8 * H, 10 * H), (10 * H + 50 * M, 12 * H), (13 * H + 30 * M, 15 * H), (15 * H + 50 * M, 17 * H), (17 * H + 50 * M, 19 * H + 30 * M),
        (20 * H + 30 * M, 23 * H + 30 * M),
    };

    [Fact]
    public void Au_plus_trois_mots_par_jour_et_espaces_d_une_heure_et_demie()
    {
        var (dits, moments) = Journee("normal", _ => true, Hachee, new DateTime(2026, 11, 25));
        Assert.Equal(3, dits);
        Assert.Equal(Presence.Moment.Premier, moments[0]);
        Assert.Contains(Presence.Moment.Soir, moments);
        Assert.Equal(1, Journee("peu", _ => true, Hachee, new DateTime(2026, 11, 25)).Dits);
        Assert.Equal(0, Journee("jamais", _ => true, Hachee, new DateTime(2026, 11, 25)).Dits);
        // Des centaines de retours dans la journée n'y changent rien.
        var miettes = Enumerable.Range(0, 60).Select(i => (6 * H + i * 15 * M, 6 * H + i * 15 * M + 2 * M)).ToList();
        Assert.True(Journee("normal", _ => true, miettes, new DateTime(2026, 11, 25)).Dits <= 3);
    }

    [Fact]
    public void Rien_pendant_la_saisie_le_plein_ecran_ou_une_attente()
    {
        // Jamais calme (on tape sans arrêt, ou plein écran, visio, IA qui attend) : rien du tout.
        Assert.Equal(0, Journee("normal", _ => false, Hachee, new DateTime(2026, 11, 25)).Dits);
        // Calme seulement de 16 h à 16 h 05 : le premier bonjour a expiré, il ne revient pas plus tard.
        var (d, m) = Journee("normal", t => t >= 16 * H && t < 16 * H + 5 * M, Hachee, new DateTime(2026, 11, 25));
        Assert.DoesNotContain(Presence.Moment.Premier, m);
        Assert.True(d <= 1);
    }

    [Fact]
    public void Le_premier_lancement_ne_salue_pas_et_le_mot_expire_sans_relance()
    {
        var r = new Cadence();
        long t = 1_790_000_000_000;
        Cadences.Observer(r, t, new DateTime(2026, 11, 25, 9, 0, 0), true);
        Assert.Null(Cadences.Pret(r, t, "normal", true)); // tout premier lancement : la bienvenue suffit
        Cadences.Observer(r, t + 20 * H, new DateTime(2026, 11, 26, 9, 0, 0), true);
        Assert.Null(Cadences.Pret(r, t + 20 * H, "normal", false));
        Assert.Null(Cadences.Pret(r, t + 20 * H + 26 * M, "normal", true)); // trop tard : il passe son tour
    }

    [Fact]
    public void Le_mot_du_soir_du_telephone_reste_sage()
    {
        for (int i = 0; i < 400; i++)
        {
            int m = Presence.MinuteDuSoir($"2026-{1 + i % 12:00}-{1 + i % 28:00}", "tel-" + i);
            Assert.InRange(m, 19 * 60, 20 * 60 + 30);
        }
        int parfois = 0, chaque = 0, jamais = 0, peu = 0;
        for (var d = new DateTime(2026, 1, 5); d < new DateTime(2026, 1, 5).AddDays(7 * 20); d = d.AddDays(1))
        {
            if (Presence.JourDeMot(d, "parfois", "normal")) parfois++;
            if (Presence.JourDeMot(d, "chaque", "normal")) chaque++;
            if (Presence.JourDeMot(d, "chaque", "jamais")) jamais++;
            if (Presence.JourDeMot(d, "chaque", "peu")) peu++;
        }
        Assert.Equal(140, chaque);
        Assert.Equal(0, jamais);
        Assert.InRange(parfois, 40, 60); // 2 à 3 par semaine
        Assert.Equal(parfois, peu);
    }

    // ---- Complicité

    [Fact]
    public void La_complicite_ne_baisse_jamais_et_ne_compte_rien_deux_fois()
    {
        var pc = Neuf("pc-1", "pc");
        var tel = Neuf("tel-1", "tel");
        var h = new Random(7);
        var messages = new List<string>();
        int avant = 0;
        var jour = new DateTime(2026, 3, 1, 10, 0, 0);
        for (int i = 0; i < 300; i++)
        {
            if (i % 5 == 0) jour = jour.AddDays(h.Next(1, 4)); // des absences de plusieurs jours : sans punition
            var qui = h.Next(2) == 0 ? pc : tel;
            qui.Ajouter(new[] { "minutes", "caresses", "soins", "jeux" }[h.Next(4)], h.Next(1, 30), jour);
            qui.Aujourdhui(Presence.JourTexte(jour)).Ca++;
            messages.Add(qui.Message(Presence.Jour(jour)));
            // Messages relus, en désordre, en double.
            var m = messages[h.Next(messages.Count)];
            pc.Recevoir(Appareil.LireMessage(m)!, Presence.Jour(jour));
            tel.Recevoir(Appareil.LireMessage(m)!, Presence.Jour(jour));
            int p = pc.Totaux().Points;
            Assert.True(p >= avant, $"la complicité a baissé : {avant} → {p}");
            avant = p;
        }
        foreach (var m in messages)
        {
            pc.Recevoir(Appareil.LireMessage(m)!, Presence.Jour(jour));
            tel.Recevoir(Appareil.LireMessage(m)!, Presence.Jour(jour));
        }
        Assert.Equal(pc.Totaux(), tel.Totaux() with { }, new TotauxEgaux());
        // Recevoir encore tout ne change rien : pas de double compte.
        var fige = pc.Totaux().Points;
        foreach (var m in messages) pc.Recevoir(Appareil.LireMessage(m)!, Presence.Jour(jour));
        Assert.Equal(fige, pc.Totaux().Points);
        // Un jour passé sur les deux appareils compte une fois.
        Assert.Equal(pc.Moi.Jours.Union(tel.Moi.Jours).Count(), pc.Totaux().Jours);
    }

    private sealed class TotauxEgaux : IEqualityComparer<Presence.Totaux>
    {
        public bool Equals(Presence.Totaux? a, Presence.Totaux? b) =>
            a!.Points == b!.Points && a.Palier == b.Palier && a.Jours == b.Jours && a.Adoption == b.Adoption && a.Prenom == b.Prenom;
        public int GetHashCode(Presence.Totaux t) => t.Points;
    }

    [Fact]
    public void Les_plafonds_du_jour_ne_punissent_pas()
    {
        var e = Neuf("pc-1", "pc");
        var j = new DateTime(2026, 5, 2, 9, 0, 0);
        Assert.Equal(Presence.MaxCaresses, e.Ajouter("caresses", 50, j));
        Assert.Equal(0, e.Ajouter("caresses", 5, j));
        Assert.Equal(3, e.Ajouter("caresses", 3, j.AddDays(1)));
        Assert.Equal(Presence.MaxCaresses + 3, e.Moi.Caresses);
        Assert.Equal(2, e.Moi.Jours.Count);
    }

    [Fact]
    public void Paliers_et_dates_annonces_une_seule_fois()
    {
        Assert.Equal(0, Presence.PalierDe(0));
        Assert.Equal(1, Presence.PalierDe(150));
        Assert.Equal(4, Presence.PalierDe(1_000_000));
        var e = Neuf("pc-1", "pc");
        int d0 = Presence.Jour(new DateTime(2026, 1, 10));
        for (int i = 0; i < 7; i++) e.Marquer(d0 + i);
        var t = e.Totaux();
        Assert.Equal("j7", Presence.DateAFeter(t, d0 + 6));
        e.Moi.Fetes.Add("j7");
        Assert.Equal("", Presence.DateAFeter(e.Totaux(), d0 + 6));
        // Un mois après l'adoption (et pas en retard d'un mois de plus).
        Assert.Equal("m1", Presence.DateAFeter(e.Totaux(), Presence.Jour(new DateTime(2026, 2, 10))));
        Assert.Equal("", Presence.DateAFeter(e.Totaux(), Presence.Jour(new DateTime(2026, 3, 30))));
        Assert.Equal("a1", Presence.DateAFeter(e.Totaux(), Presence.Jour(new DateTime(2027, 1, 10))));
        // L'annonce d'un palier faite ailleurs dans le groupe compte ici.
        var tel = Neuf("tel-1", "tel");
        tel.Moi.PalierAnnonce = 2;
        e.Recevoir(Appareil.LireMessage(tel.Message(d0))!, d0);
        Assert.Equal(2, e.Totaux().PalierAnnonce);
    }

    // ---- Journal

    [Fact]
    public void Le_journal_est_identique_des_deux_cotes()
    {
        var pc = Neuf("pc-1", "pc");
        var tel = Neuf("tel-1", "tel");
        var h = new Random(3);
        var jour0 = new DateTime(2026, 6, 1);
        var envois = new List<string>();
        for (int d = 0; d < 40; d++)
        {
            var jour = jour0.AddDays(d);
            var j = Presence.JourTexte(jour);
            var f = pc.Aujourdhui(j);
            f.Mn = h.Next(0, 400);
            f.Tv = h.Next(0, 500);
            (f.Ac, f.Am) = (new[] { "code", "tableur", "musique", "mail", "texte" }[h.Next(5)], h.Next(0, 300));
            if (h.Next(4) == 0) f.Nv = 10 + d;
            if (h.Next(5) == 0) (f.Mo, f.Mg) = ("Codeur", 2);
            if (h.Next(3) == 0) f.Me = new[] { "pluie", "neige", "degage" }[h.Next(3)];
            var g = tel.Aujourdhui(j);
            g.Ca = h.Next(0, 8);
            g.So = h.Next(0, 3);
            if (h.Next(3) == 0) (g.Px, g.Pq, g.Pc) = (new[] { "une truite argentée", "une perle de lune" }[h.Next(2)], h.Next(0, 5), 1);
            if (h.Next(6) == 0) g.Cx = "une soupe du pêcheur";
            envois.Add(pc.Message(Presence.Jour(jour)));
            envois.Add(tel.Message(Presence.Jour(jour)));
            // Le téléphone ne lit que de temps en temps (hors ligne, relais qui garde 12 h…).
            if (d % 3 == 2)
                foreach (var m in envois.TakeLast(6).Reverse()) tel.Recevoir(Appareil.LireMessage(m)!, Presence.Jour(jour));
            foreach (var m in envois.TakeLast(2)) pc.Recevoir(Appareil.LireMessage(m)!, Presence.Jour(jour));
            pc.Compacter(Presence.Jour(jour));
            tel.Compacter(Presence.Jour(jour));
        }
        foreach (var m in envois.TakeLast(4))
        {
            tel.Recevoir(Appareil.LireMessage(m)!, Presence.Jour(jour0.AddDays(39)));
            pc.Recevoir(Appareil.LireMessage(m)!, Presence.Jour(jour0.AddDays(39)));
        }
        var a = pc.Entrees(Presence.Gabarits);
        var b = tel.Entrees(Presence.Gabarits);
        Assert.True(a.Count >= 30);
        Assert.Equal(a, b);
        Assert.All(a, x => Assert.InRange(Presence.Phrases(x.Texte), 1, 3));
        Assert.All(a, x => Assert.DoesNotContain("{", x.Texte));
        foreach (var x in a.Take(6)) _sortie.WriteLine($"{x.Jour} [{x.Humeur}] {x.Texte}");
    }

    [Fact]
    public void Les_faits_fusionnent_sans_ordre_ni_doublon()
    {
        var h = new Random(11);
        for (int i = 0; i < 200; i++)
        {
            var a = Hasard(h);
            var b = Hasard(h);
            var c = Hasard(h);
            Assert.Equal(FaitsDuJour.Fusion(a, b).Texte(), FaitsDuJour.Fusion(b, a).Texte());
            Assert.Equal(FaitsDuJour.Fusion(a, a).Texte(), a.Texte());
            Assert.Equal(FaitsDuJour.Fusion(FaitsDuJour.Fusion(a, b), c).Texte(), FaitsDuJour.Fusion(a, FaitsDuJour.Fusion(b, c)).Texte());
            Assert.Equal(a.Texte(), FaitsDuJour.Lire(a.Texte()).Texte());
        }
    }

    // ---- Prénom et vie privée

    [Fact]
    public void Le_prenom_reste_dans_le_groupe_chiffre_et_ne_va_jamais_aux_amis()
    {
        var e = Neuf("pc-1", "pc");
        e.ChoisirPrenom("  Margot\t la Grande  ", 1_790_000_000_000);
        Assert.Equal("Margot la Grande", e.Prenom);
        Assert.Contains("Margot", e.Message(20000));        // le message du groupe (chiffré avec le code du groupe)
        // Ce qui part vers les amis : la vitrine et ses faits. Rien n'y vient de la présence.
        var p = new Profil();
        var message = Amis.Message("vitrine", "ABCD2345WXYZ", 0);
        message.Pilou = new Vitrine { Nom = "Pilou", Faits = Amis.FaitsDe(p, "pluie") };
        var json = Amis.Ecrire(message);
        Assert.DoesNotContain("Margot", json);
        Assert.DoesNotContain("Margot", Groupe.Json(Groupe.Moi(p, "pc-1", "PC")));
        Assert.DoesNotContain("Margot", Telephone.Charge(new List<Telephone.SessionTel>(), 0, "Pilou", 1, "", "bleu", "repos", 0,
            Telephone.Progression(p, 0, "")));
        // Effacer : le choix le plus récent l'emporte dans tout le groupe.
        var tel = Neuf("tel-1", "tel");
        tel.Recevoir(Appareil.LireMessage(e.Message(20000))!, 20000);
        Assert.Equal("Margot la Grande", tel.Prenom);
        tel.ChoisirPrenom("", 1_790_000_100_000);
        e.Recevoir(Appareil.LireMessage(tel.Message(20000))!, 20000);
        Assert.Equal("", e.Prenom);
        Assert.True(e.Totaux().PrenomDemande); // et on ne redemande pas
    }

    [Fact]
    public void Les_scenes_d_essai_sont_connues_de_la_visite_guidee()
    {
        foreach (var s in new[] { "mot", "journal", "complicite" }) Assert.True(Tournage.EssaiConnu(s), s);
    }

    [Fact]
    public void Les_prises_et_les_plats_ont_leur_article()
    {
        Assert.Equal("une truite argentée", Presence.AvecArticle("truite", "Truite argentée"));
        Assert.Equal("un goujon bleu", Presence.AvecArticle("goujon", "Goujon bleu"));
        Assert.Equal("des croquettes croustillantes", Presence.AvecArticle("croquettes", "Croquettes croustillantes"));
        Assert.Equal("un riz de la lagune", Presence.AvecArticle("paella", "Riz de la lagune"));
        // Toutes les prises et toutes les recettes connues reçoivent un article.
        Assert.All(Butin.Prises, p => Assert.Matches("^(un|une|des) ", Presence.AvecArticle(p.Id, p.Nom)));
        Assert.All(Butin.Recettes, r => Assert.Matches("^(un|une|des) ", Presence.AvecArticle(r.Id, r.Nom)));
    }

    [Fact]
    public void L_etat_se_relit_a_l_identique()
    {
        var e = Neuf("pc-1", "pc");
        var j = new DateTime(2026, 4, 3, 21, 0, 0);
        e.Ajouter("minutes", 40, j);
        e.Aujourdhui("2026-04-03").Ca = 3;
        e.Dits["0a1b2c3d"] = 20500;
        e.Parle = "peu";
        e.MotJour = "2026-04-03";
        e.MotTexte = "coucou. je pensais à toi, c'est tout";
        e.Cadence = new Cadence { Jour = "2026-04-03", Dits = 2, DernierMot = 5, DerniereVue = 6, Attente = "soir", PresenceJourMin = 12.5 };
        e.ActJour = "2026-04-03";
        e.ActSec["code"] = 1200;
        var tel = Neuf("tel-1", "tel");
        tel.ChoisirPrenom("Lou", 3);
        e.Recevoir(Appareil.LireMessage(tel.Message(Presence.Jour(j)))!, Presence.Jour(j));
        var texte = e.Texte();
        Assert.Equal(texte, EtatPresence.Lire(texte).Texte());
        Assert.Equal("", EtatPresence.Lire("n'importe quoi").Texte().Contains("Lou") ? "x" : "");
    }

    [Fact]
    public void Le_message_reste_sous_la_limite_du_relais()
    {
        var e = Neuf("pc-1", "pc");
        var j = new DateTime(2023, 1, 1);
        for (int d = 0; d < 1400; d += 1) e.Marquer(Presence.Jour(j.AddDays(d)));
        for (int d = 1390; d < 1400; d++)
        {
            var f = e.Aujourdhui(Presence.JourTexte(j.AddDays(d)));
            (f.Mn, f.Tv, f.Ac, f.Am, f.Px, f.Pq, f.Cx, f.Cf, f.Mo, f.Ex, f.Ob) =
                (300, 200, "code", 150, new string('x', 40), 3, new string('y', 40), new string('z', 40), new string('m', 40), new string('e', 40), new string('o', 40));
        }
        for (int i = 0; i < 30; i++) e.Moi.Fetes.Add("j" + i);
        var m = e.Message(Presence.Jour(j.AddDays(1399)));
        Assert.True(Presence.Octets(m) <= Presence.TailleMessage, $"{Presence.Octets(m)} octets");
        Assert.Equal(1400, Appareil.LireMessage(m)!.Jours.Count);
        Assert.True(Telephone.Chiffrer("ABCDEFGHJKMNPQRS", m).Length <= Telephone.TailleMax);
    }

    [Fact]
    public void Vecteurs_partages_avec_le_telephone()
    {
        var chemin = Path.Combine(CampagnesVecteurs.Racine().FullName, PresenceVecteurs.Reference);
        var texte = PresenceVecteurs.Tout();
        Assert.Equal(texte, PresenceVecteurs.Tout());
        if (Environment.GetEnvironmentVariable("PILOU_REGENERER") == "1") File.WriteAllText(chemin, texte);
        Assert.True(File.Exists(chemin), $"{PresenceVecteurs.Reference} manque : PILOU_REGENERER=1 dotnet test");
        var attendu = File.ReadAllText(chemin).Replace("\r\n", "\n");
        if (attendu != texte)
        {
            var a = attendu.Split('\n');
            var b = texte.Split('\n');
            int i = 0;
            while (i < a.Length && i < b.Length && a[i] == b[i]) i++;
            Assert.Fail($"vecteurs différents à la ligne {i + 1} (PILOU_REGENERER=1 dotnet test si le moteur a changé exprès) :\n"
                        + $"fichier : {(i < a.Length ? a[i] : "(fin)")}\nmoteur  : {(i < b.Length ? b[i] : "(fin)")}");
        }
        _sortie.WriteLine($"{texte.Split('\n').Length} lignes");
    }

    // ---- Outils

    internal static EtatPresence Neuf(string id, string sorte) => new() { Moi = new Appareil { Id = id, Sorte = sorte } };

    internal static Presence.Contexte Ctx(DateTime local, Presence.Moment m, double absence = 0, int palier = 0, string prenom = "") =>
        new(local, m, absence, 120, 60, "code", "", palier, 2, "", prenom);

    internal static FaitsDuJour Hasard(Random h)
    {
        var f = new FaitsDuJour
        {
            Mn = h.Next(0, 3) * h.Next(0, 300), Tv = h.Next(0, 2) * h.Next(0, 600), Jx = h.Next(0, 2) * h.Next(0, 6), Ca = h.Next(0, 9),
            So = h.Next(0, 2) * h.Next(0, 4), Pc = h.Next(0, 3), Cu = h.Next(0, 2), Qu = h.Next(0, 2) * h.Next(0, 4), Ce = h.Next(0, 2) * h.Next(0, 9),
            Vi = h.Next(0, 4) == 0 ? 1 : 0, Nv = h.Next(0, 6) == 0 ? h.Next(2, 60) : 0, Ta = h.Next(0, 3) == 0 ? h.Next(1260, 1440) : 0,
        };
        if (h.Next(2) == 0) (f.Ac, f.Am) = (new[] { "code", "tableur", "texte", "mail", "visio", "musique", "video", "lecture", "dessin", "jeu-mmo", "diaporama" }[h.Next(11)], h.Next(0, 400));
        if (f.Pc > 0) (f.Px, f.Pq) = (new[] { "une truite argentée", "un goujon bleu", "une perle de lune", "une vieille botte", "un crabe bleu" }[h.Next(5)], h.Next(0, 5));
        if (f.Cu > 0) f.Cx = new[] { "une soupe du pêcheur", "une tartine de la rivière", "un poisson grillé" }[h.Next(3)];
        if (h.Next(3) == 0) f.Me = new[] { "pluie", "averse", "orage", "neige", "brouillard", "vent", "chaleur", "froid", "degage", "nuageux" }[h.Next(10)];
        if (h.Next(8) == 0) f.Cf = new[] { "Le phare éteint", "La Grande Panne", "Petit Nuage" }[h.Next(3)];
        if (h.Next(5) == 0) (f.Mo, f.Mg) = (new[] { "Codeur", "Mélomane", "As du tableur" }[h.Next(3)], h.Next(1, 6));
        if (h.Next(7) == 0) f.Ex = "Caverne des câbles";
        if (h.Next(7) == 0) f.Ob = new[] { "Écharpe", "Cape étoilée" }[h.Next(2)];
        return f;
    }
}

// Vecteurs partagés de la présence : une ligne = une opération, ses entrées (séparées par des tabulations), puis le
// résultat attendu. android/app/src/test/resources/presence-vecteurs.txt ; PresenceTest.java refait chaque opération.
//   hash <texte> <hex> · mot <moment> <date> <absence> <jour> <séance> <activité> <météo> <palier> <stade> <variante>
//   <prénom> <métier> <niveau> <objet> <prise> <plat> <souvenir> <date à fêter> <palier nouveau> <demander> <jours>
//   <années> <dits> <graine> <famille|id|texte> · journal <jour> <faits> <texte|humeur> · fusion <a> <b> <résultat>
//   soir <jour> <appareil> <minute> · jourdemot <jour> <fréquence> <parle> <0|1>
//   totaux <état> <aujourd'hui> <points palier jours adoption date> · message <état> <aujourd'hui> <message>
//   recevoir <état> <message> <aujourd'hui> <0|1> <état après> · cadence <état> <ms> <date> <présent> <parle> <calme> <moment|-> <état après>
public static class PresenceVecteurs
{
    public const string Reference = "android/app/src/test/resources/presence-vecteurs.txt";
    private static readonly CultureInfo Ci = CultureInfo.InvariantCulture;

    public static string Echapper(string s) => s.Replace("\\", "\\\\").Replace("\n", "\\n").Replace("\t", "\\t");

    private static string Date(DateTime d) => d.ToString("yyyy-MM-dd'T'HH:mm", Ci);

    private static string Dits(IReadOnlyDictionary<string, int> d) =>
        string.Join(",", d.OrderBy(kv => kv.Key, StringComparer.Ordinal).Select(kv => kv.Key + ":" + kv.Value.ToString(Ci)));

    public static string Tout()
    {
        var l = new List<string> { "# vecteurs de la présence (apps/PilouBureau/tests/PresenceTests.cs) : ne pas modifier à la main" };
        void Ligne(params string[] champs) => l.Add(string.Join("\t", champs));

        foreach (var s in new[] { "", "a", "Pilou", "é∞ goutte d'encre", "2026-11-27|tel-ab12|soir" })
            Ligne("hash", s, Presence.Hash(s).ToString("x16", Ci));

        // Petits mots : tous les moments, des dates variées, une mémoire qui grandit.
        var h = new Random(2026);
        var dits = new Dictionary<string, int>();
        var activites = new[] { "", "code", "tableur", "texte", "mail", "musique", "video", "lecture", "dessin", "jeu-mmo", "visio" };
        var meteos = new[] { "", "pluie", "averse", "orage", "neige", "brouillard", "vent", "chaleur", "froid", "degage", "nuageux" };
        var souvenirs = new[] { "", "", "prologue", "grande-panne", "phare-eteint", "petit-nuage" };
        var dates = new[] { "", "", "", "", "j7", "m1", "m6", "j100", "a1", "a3", "j1000" };
        for (int i = 0; i < 700; i++)
        {
            if (i % 30 == 0) dits.Clear(); // des mémoires courtes : le fichier reste lisible
            var d = new DateTime(2026, 1, 1).AddDays(h.Next(0, 800)).AddMinutes(h.Next(0, 1440));
            var m = (Presence.Moment)h.Next(4);
            var c = new Presence.Contexte(d, m, h.Next(4) switch { 0 => 0, 1 => h.Next(45, 300), 2 => h.Next(300, 3000), _ => h.Next(3000, 40000) },
                h.Next(0, 600), h.Next(0, 400), activites[h.Next(activites.Length)], meteos[h.Next(meteos.Length)], h.Next(0, 5), h.Next(1, 5),
                new[] { "", "calin", "espiegle" }[h.Next(3)], h.Next(4) == 0 ? "Lou" : "",
                h.Next(3) == 0 ? "Codeur" : "", h.Next(3) == 0 ? h.Next(2, 60) : 0, h.Next(3) == 0 ? "Écharpe rayée" : "",
                h.Next(3) == 0 ? "une truite argentée" : "", h.Next(4) == 0 ? "une soupe du pêcheur" : "", souvenirs[h.Next(souvenirs.Length)],
                dates[h.Next(dates.Length)], h.Next(6) == 0 ? h.Next(1, 5) : -1, h.Next(8) == 0, h.Next(0, 900), h.Next(0, 4));
            var graine = Presence.JourTexte(d) + "|pc-" + h.Next(3).ToString(Ci) + "|" + h.Next(3).ToString(Ci);
            var choix = Presence.Mot(c, Presence.Mots, dits, graine);
            Ligne("mot", c.Moment.ToString(), Date(c.Local), c.AbsenceMin.ToString(Ci), c.PresenceJourMin.ToString(Ci), c.SeanceMin.ToString(Ci),
                c.Activite, c.Meteo, c.Palier.ToString(Ci), c.Stade.ToString(Ci), c.Variante, c.Prenom, c.Metier, c.Niveau.ToString(Ci), c.Objet,
                c.Prise, c.Plat, c.Souvenir, c.DateAFeter, c.PalierNouveau.ToString(Ci), c.DemanderPrenom ? "1" : "0", c.JoursEnsemble.ToString(Ci),
                c.Annees.ToString(Ci), Dits(dits), graine, choix is null ? "-" : choix.Famille + "|" + choix.Ligne.Id + "|" + choix.Texte);
            if (choix is not null) Presence.Retenir(dits, choix.Ligne.Id, Presence.Jour(d));
        }

        // Journal : 400 jours de faits au hasard.
        for (int i = 0; i < 400; i++)
        {
            var f = PresenceTests.Hasard(h);
            var jour = Presence.JourTexte(new DateTime(2026, 1, 1).AddDays(i));
            var e = Presence.Ecrire(jour, f, Presence.Gabarits);
            Ligne("journal", jour, f.Texte(), e is null ? "-" : e.Texte + "|" + e.Humeur);
        }
        for (int i = 0; i < 150; i++)
        {
            var a = PresenceTests.Hasard(h);
            var b = PresenceTests.Hasard(h);
            Ligne("fusion", a.Texte(), b.Texte(), FaitsDuJour.Fusion(a, b).Texte());
        }
        for (int i = 0; i < 60; i++)
        {
            var jour = Presence.JourTexte(new DateTime(2026, 1, 1).AddDays(h.Next(0, 900)));
            var app = "tel-" + h.Next(0, 99999).ToString("x4", Ci);
            Ligne("soir", jour, app, Presence.MinuteDuSoir(jour, app).ToString(Ci));
        }
        for (int i = 0; i < 120; i++)
        {
            var d = new DateTime(2025, 12, 1).AddDays(i * 3 + h.Next(3));
            var f = new[] { "chaque", "parfois", "jamais" }[h.Next(3)];
            var p = new[] { "normal", "peu", "jamais" }[h.Next(3)];
            Ligne("jourdemot", Presence.JourTexte(d), f, p, Presence.JourDeMot(d, f, p) ? "1" : "0");
        }

        // Complicité et synchronisation : deux appareils qui vivent et s'écrivent.
        var pc = PresenceTests.Neuf("pc-7f3a", "pc");
        var tel = PresenceTests.Neuf("tel-91c0", "tel");
        var jour0 = new DateTime(2026, 2, 20, 9, 0, 0);
        for (int i = 0; i < 60; i++)
        {
            var d = jour0.AddDays(i / 2 + (i % 7 == 0 ? 3 : 0)).AddHours(i % 5);
            int auj = Presence.Jour(d);
            var qui = i % 3 == 0 ? tel : pc;
            qui.Ajouter(new[] { "minutes", "caresses", "soins", "jeux" }[h.Next(4)], h.Next(1, 40), d);
            var f = qui.Aujourdhui(Presence.JourTexte(d));
            f.Mn += h.Next(0, 30);
            f.Ca += h.Next(0, 2);
            if (h.Next(10) == 0) qui.Moi.Finies.Add(new[] { "prologue", "phare-eteint" }[h.Next(2)]);
            if (h.Next(15) == 0) qui.Moi.Fetes.Add(new[] { "j7", "m1" }[h.Next(2)]);
            if (h.Next(20) == 0) qui.ChoisirPrenom(new[] { "Lou", "Sam", "" }[h.Next(3)], 1_790_000_000_000 + i * 1000L);
            if (h.Next(25) == 0) qui.Moi.PalierAnnonce = Math.Max(qui.Moi.PalierAnnonce, qui.Totaux().Palier);
            var etat = qui.Texte();
            var msg = qui.Message(auj);
            Ligne("message", Echapper(etat), auj.ToString(Ci), Echapper(msg));
            var autre = qui == pc ? tel : pc;
            var avant = autre.Texte();
            bool change = autre.Recevoir(Appareil.LireMessage(msg)!, auj);
            bool compacter = i % 4 == 0;
            if (compacter) autre.Compacter(auj);
            Ligne("recevoir", Echapper(avant), Echapper(msg), auj.ToString(Ci), compacter ? "1" : "0", change ? "1" : "0", Echapper(autre.Texte()));
            var t = autre.Totaux();
            Ligne("totaux", Echapper(autre.Texte()), auj.ToString(Ci),
                $"{t.Points} {t.Palier} {t.Jours} {t.Adoption} {(Presence.DateAFeter(t, auj) is { Length: > 0 } df ? df : "-")}");
            // Ce que relit le téléphone : l'état tel qu'écrit (le fichier fait foi des deux côtés).
            pc = EtatPresence.Lire(pc.Texte());
            tel = EtatPresence.Lire(tel.Texte());
        }

        // Cadence du PC : une semaine de présences hachées, d'état en état.
        var cad = PresenceTests.Neuf("pc-7f3a", "pc");
        // Décalage fixe (UTC) : le fichier de référence ne dépend pas du fuseau de la machine qui lance le test.
        long t0 = new DateTimeOffset(new DateTime(2026, 11, 22, 7, 0, 0), TimeSpan.Zero).ToUnixTimeMilliseconds();
        var dl = new DateTime(2026, 11, 22, 7, 0, 0);
        for (int i = 0; i < 500; i++)
        {
            long pas = h.Next(10) == 0 ? h.Next(40, 900) * 60_000L : h.Next(1, 60) * 30_000L;
            t0 += pas;
            dl = dl.AddMilliseconds(pas);
            bool present = h.Next(5) != 0, calme = h.Next(3) != 0;
            var parle = new[] { "normal", "normal", "normal", "peu", "jamais" }[h.Next(5)];
            cad = EtatPresence.Lire(cad.Texte());
            var avant = cad.Texte();
            Cadences.Observer(cad.Cadence, t0, dl, present);
            var m = Cadences.Pret(cad.Cadence, t0, parle, calme);
            if (m is { } mm) Cadences.Noter(cad.Cadence, t0, mm);
            Ligne("cadence", Echapper(avant), t0.ToString(Ci), dl.ToString("yyyy-MM-dd'T'HH:mm:ss", Ci), present ? "1" : "0", parle, calme ? "1" : "0",
                m?.ToString() ?? "-", Echapper(cad.Texte()));
        }
        return string.Join("\n", l) + "\n";
    }
}
