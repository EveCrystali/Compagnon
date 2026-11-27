using System.Text.Json;
using PilouBureau;
using Xunit;
using Xunit.Abstractions;

// Métiers et succès vus du téléphone (heures, avancement) et taille du message publié.
public class MetiersTelephoneTests
{
    private const string Code = "ABCD-EFGH-JKMN-PQRS";
    private readonly ITestOutputHelper _sortie;

    public MetiersTelephoneTests(ITestOutputHelper sortie) => _sortie = sortie;

    private static Stats S(Profil p, double serie = 0) =>
        new(p.Activites, serie, p.Reunions.Count, p.Presentations, DateTime.Now, "", p.SeancesClavier, p.Captures, p.Defense);

    [Fact]
    public void Heures_en_dixiemes_et_avancement_des_succes()
    {
        var p = new Profil
        {
            Activites = new() { ["code"] = (long)(5.7 * 3600), ["musique"] = 3 * 3600 + 1200, ["jeu"] = 3600, ["jeu-mmo"] = 1800, ["mail"] = 100 },
            Succes = new() { "melomane" },
            SeancesClavier = 7,
        };
        var d = Telephone.MetiersEtSucces(p, S(p, serie: 2.5 * 3600));
        var heures = Assert.IsType<Dictionary<string, int>>(d["heures"]);
        Assert.Equal(57, heures["codeur"]);
        Assert.Equal(33, heures["musicien"]);
        Assert.Equal(15, heures["joueur"]);   // jeu + jeu de rôle
        Assert.False(heures.ContainsKey("facteur")); // 100 s : moins d'un dixième d'heure
        Assert.False(heures.ContainsKey("tableur"));
        var niveaux = Assert.IsType<Dictionary<string, int>>(d["metiers"]);
        Assert.False(niveaux.ContainsKey("codeur")); // Novice : 5,7 h / 6 h
        Assert.Equal(1, niveaux["musicien"]); // Novice → Apprenti à 1 h
        var avance = Assert.IsType<Dictionary<string, int>>(d["avance"]);
        Assert.Equal(25, avance["marathon"]);   // 2,5 h / 4 h
        Assert.Equal(70, avance["dactylo"]);    // 7 / 25
        Assert.Equal(57, avance["codeur-confirme"]);
        Assert.False(avance.ContainsKey("melomane"));   // obtenu
        Assert.False(avance.ContainsKey("noctambule")); // succès d'un coup : pas d'avancement
        Assert.False(avance.ContainsKey("visio-man"));  // pas commencé
        Assert.Equal(new List<string> { "melomane" }, d["succes"]);
        // Jamais « fini » avant l'heure : 9,99 h de musique sur 10 → 99 dixièmes.
        var q = new Profil { Activites = new() { ["musique"] = 10 * 3600 - 30 } };
        Assert.Equal(99, Succes.Avancements(S(q), q.Succes)["melomane"]);
    }

    [Fact]
    public void Unites_des_succes()
    {
        Assert.Equal("h", Succes.Unite(Succes.Tous.Single(d => d.Id == "marathon")));
        Assert.Equal("n", Succes.Unite(Succes.Tous.Single(d => d.Id == "visio-man")));
        Assert.Equal("vague", Succes.Unite(Succes.Tous.Single(d => d.Id == "rempart")));
        Assert.Equal("points", Succes.Unite(Succes.Tous.Single(d => d.Id == "gardien")));
        Assert.Equal("", Succes.Unite(Succes.Tous.Single(d => d.Id == "noctambule")));
    }

    // Un gros profil réaliste : tout pêché, tout cuisiné, un quart de la boutique, quatre sessions ouvertes, six amis,
    // trois appareils, cinq nouvelles, des heures dans chaque métier, la moitié des succès obtenus.
    private static (Dictionary<string, object> Progression, Func<Dictionary<string, object>, string> Charge) Message(int nbSessions = 4, int partBoutique = 4)
    {
        var p = new Profil
        {
            Carnet = Butin.Prises.ToDictionary(x => x.Id, _ => 12),
            Plats = Butin.Recettes.Select(r => r.Id).Concat(Enumerable.Range(0, 30).Select(i => $"inv:Galette inventée numéro {i}")).ToList(),
            Recus = Enumerable.Range(0, 10).Select(i => $"{i:x12}").ToList(),
            Activites = Activites.Toutes.Where(a => a != "nuit").ToDictionary(a => a, a => 987L * 3600 + 1234),
            SeancesClavier = 12, Captures = 7, Presentations = 3,
            Defense = new EtatDefense { Meilleur = 8765, MeilleureVague = 7 },
        };
        p.Succes = Succes.Tous.Where((_, i) => i % 2 == 1).Select(d => d.Id).ToList();
        p.Soins.Base = new EtatSoins();
        p.Evolution.Variantes[2] = "calin";
        p.Evolution.Variantes[3] = "espiegle";
        var inventaire = Boutique.Catalogue.Where((_, i) => i % partBoutique == 0).Select(a => a.Id).ToList();
        var equipe = Boutique.Slots.Take(6).ToDictionary(s => s, s => new Port(Boutique.Catalogue.FirstOrDefault(a => a.Slot == s)?.Id ?? "", 1.7e12));
        var local = new DateTime(2026, 11, 27, 14, 0, 0);
        Quetes.Actualiser(p.Quetes, local, "pc-de-test");
        const double t = 1_790_000_000_000;
        var sessions = Enumerable.Range(0, nbSessions).Select(i => new Telephone.SessionTel(Guid.NewGuid().ToString(), "claude",
            "refonte du module de facturation client", i == 0 ? "permission" : "travail", t - i * 60_000, "Bash")).ToList();
        var d = Telephone.Progression(p, 123_456, "lunettes", S(p, serie: 3.2 * 3600));
        {
            foreach (var (k, v) in Telephone.EtatBoutique(54_321, inventaire, equipe, p.Quetes, local)) d[k] = v;
            d["stade"] = 4;
            d["expedition"] = Expeditions.PourTelephone(new EtatExpedition { Energie = { Valeur = 73.6 } }, t, local, ExpeditionsAutres.Aucun);
            d["annonces"] = Enumerable.Range(0, 5).Select(i => new Dictionary<string, object>
            {
                ["source"] = "discord", ["titre"] = $"Message de Camille dans #projet-{i}", ["texte"] = "On se cale la démo de jeudi à 14 h ? J'ai mis les maquettes dans le dossier partagé.", ["t"] = t,
            }).ToList();
            d["meteo"] = new Dictionary<string, object> { ["etat"] = "pluie", ["temperature"] = 8.0, ["ville"] = "Saint-Germain-en-Laye", ["signe"] = "☂" };
            d["appareils"] = Enumerable.Range(0, 3).Select(i => new Dictionary<string, object> { ["nom"] = $"PC-BUREAU-{i:00}", ["xp"] = 12_345, ["t"] = t }).ToList();
            d["amis"] = Enumerable.Range(0, 6).Select(i => new Dictionary<string, object>
            {
                ["nom"] = $"Pilou de Léo {i:00}", ["niveau"] = 23, ["stade"] = 3, ["t"] = t, ["actif"] = true,
            }).ToList();
            d["visite"] = "parti chez Pilou de Léo 01 · retour vers 15 h 40";
        }
        return (d, x => Telephone.Charge(sessions, t, "Pilou", 48, "Légende des pixels", "comete", "concentre", 3, x));
    }

    private static Dictionary<string, object> Sans(Dictionary<string, object> d, params string[] cles)
    {
        var r = new Dictionary<string, object>(d);
        foreach (var c in cles) r.Remove(c);
        return r;
    }

    private static int Taille(string json) => Telephone.Chiffrer(Code, json).Length;

    [Fact]
    public void Le_message_le_plus_gros_reste_sous_la_limite_ntfy()
    {
        var (d, charge) = Message();
        int complet = Taille(charge(d)), avant = Taille(charge(Sans(d, "heures", "avance")));
        int leger = Taille(charge(Sans(d, "carnet", "plats"))), legerAvant = Taille(charge(Sans(d, "carnet", "plats", "heures", "avance")));
        _sortie.WriteLine($"complet : {avant} → {complet} octets chiffrés ; sans carnet ni recettes : {legerAvant} → {leger} (limite {Telephone.TailleMax})");
        // Les heures des métiers et l'avancement des succès ajoutent peu.
        Assert.InRange(complet - avant, 1, 450);

        // Ce qui part vraiment : sous la limite, toujours avec les métiers et les succès (heures et avancement compris).
        var corps = Telephone.SousLimite(Code, d, charge);
        using var doc = JsonDocument.Parse(Telephone.Dechiffrer(Code, corps));
        var r = doc.RootElement;
        _sortie.WriteLine($"publié : {corps.Length} octets, sans {string.Join(", ", Telephone.Allegements.Where(k => !r.TryGetProperty(k, out _)))}");
        Assert.True(corps.Length <= Telephone.TailleMax, $"{corps.Length} octets");
        foreach (var cle in new[] { "heures", "avance", "succes", "sessions", "recus", "objets", "garde", "porte", "quetes", "soins", "expedition" })
            Assert.True(r.TryGetProperty(cle, out _), cle);
        Assert.Equal(9873, r.GetProperty("heures").GetProperty("codeur").GetInt32());
    }

    [Fact]
    public void Trop_long_le_message_s_allege_pas_a_pas()
    {
        // Huit sessions et toute la boutique : on retire ce qu'il faut, dans l'ordre, et rien de plus.
        var (d, charge) = Message(nbSessions: 8, partBoutique: 1);
        var corps = Telephone.SousLimite(Code, d, charge);
        _sortie.WriteLine($"très gros profil : {Taille(charge(d))} → {corps.Length} octets chiffrés");
        using var doc = JsonDocument.Parse(Telephone.Dechiffrer(Code, corps));
        var r = doc.RootElement;
        Assert.False(r.TryGetProperty("carnet", out _));
        Assert.False(r.TryGetProperty("plats", out _));
        Assert.True(r.TryGetProperty("sessions", out _));
        Assert.True(r.TryGetProperty("recus", out _));
        // Un petit message passe tel quel.
        var petit = new Dictionary<string, object> { ["xp"] = 3, ["carnet"] = new List<string> { "goujon" } };
        var c = Telephone.SousLimite(Code, petit, x => Telephone.Charge(new List<Telephone.SessionTel>(), 1, "Pilou", 1, "", "bleu", "repos", 0, x));
        Assert.Contains("goujon", Telephone.Dechiffrer(Code, c));
    }

    // ---- Catalogue miroir du téléphone (Metiers.java)

    private const string Reference = "android/app/src/test/resources/metiers-succes.txt";

    // Le catalogue des métiers et des succès en texte, ligne à ligne : le test Java (MetiersTest) refait le même
    // texte depuis Metiers.java et le compare à ce fichier.
    public static string Catalogue()
    {
        var ci = System.Globalization.CultureInfo.InvariantCulture;
        var l = new List<string>
        {
            "# Catalogue des métiers et des succès, tiré de apps/PilouBureau/Metiers.cs (MetiersTelephoneTests).",
            "# Le téléphone en a une copie (android/.../Metiers.java) : MetiersTest vérifie qu'elle donne ce même texte.",
            "# Pour le refaire après un changement du PC : PILOU_REGENERER=1 dotnet test apps/PilouBureau/tests",
            "paliers " + string.Join(",", Metiers.Paliers),
            "paliersTravail " + string.Join(",", Metiers.PaliersTravail),
            "grades " + string.Join(",", Metiers.Grades),
        };
        l.AddRange(Metiers.Tous.Select(m => $"metier {m.Id}|{m.Nom}|{string.Join(",", m.Activites)}|{(m.Travail ? "travail" : "loisir")}"));
        l.AddRange(Succes.Tous.Select(d => $"succes {d.Id}|{d.Nom}|{d.Description}|{d.But.ToString("0.##", ci)}|{d.Xp}|{Succes.Unite(d)}"));
        return string.Join("\n", l) + "\n";
    }

    [Fact]
    public void Le_telephone_a_le_meme_catalogue()
    {
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        while (dir is not null && !Directory.Exists(Path.Combine(dir.FullName, "android"))) dir = dir.Parent;
        Assert.NotNull(dir);
        var chemin = Path.Combine(dir!.FullName, Reference);
        if (Environment.GetEnvironmentVariable("PILOU_REGENERER") == "1") File.WriteAllText(chemin, Catalogue());
        Assert.True(File.Exists(chemin), $"{Reference} manque : PILOU_REGENERER=1 dotnet test");
        Assert.Equal(Catalogue(), File.ReadAllText(chemin).Replace("\r\n", "\n"));
    }
}
