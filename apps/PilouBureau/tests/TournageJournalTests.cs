using System.Text.Json;
using PilouBureau;
using Xunit;

// Tournage v2 : journal écrit au fil de l'eau, reprise après une étape en échec, cadrages pour le montage,
// fenêtres posées près de Pilou, Pilou en grand.
public class TournageJournalTests : IDisposable
{
    private readonly string _dossier = Path.Combine(Path.GetTempPath(), "pilou-journal-" + Guid.NewGuid().ToString("N"));
    private long _t = 1_800_000_000_000;

    public TournageJournalTests() => Directory.CreateDirectory(_dossier);

    public void Dispose()
    {
        if (Directory.Exists(_dossier)) Directory.Delete(_dossier, true);
    }

    private static readonly CadreEcran Ecran = new(0, 0, 2560, 1440);

    private JournalVisite Journal() => new(Path.Combine(_dossier, "chronologie-brute.json"), "0.9.45", Ecran, () => _t);

    private static List<JsonElement> Lignes(string chemin) =>
        File.ReadAllLines(chemin).Where(l => l.Trim() != "").Select(l => JsonDocument.Parse(l).RootElement.Clone()).ToList();

    private static JsonElement Instantane(string chemin) => JsonDocument.Parse(File.ReadAllText(chemin)).RootElement.Clone();

    [Fact]
    public void LesMomentsSEcriventAuFilDeLEauPasSeulementALaFin()
    {
        var j = Journal();
        var chrono = Path.Combine(_dossier, "chronologie-brute.json");
        Assert.Equal(Path.Combine(_dossier, "chronologie-brute.jsonl"), j.CheminLignes);
        Assert.False(File.Exists(chrono));

        j.Etape("accueil");
        Assert.Single(Lignes(j.CheminLignes!));
        var r = Instantane(chrono);
        Assert.False(r.GetProperty("complete").GetBoolean());
        Assert.Equal("accueil", r.GetProperty("etapes")[0].GetProperty("etape").GetString());

        _t += 2500;
        j.Etape("promenade");
        _t += 3000;
        j.Etape("defense", jouee: false);
        // L'overlay s'arrête net ici (pas de Terminer) : tout ce qui a été joué est déjà sur le disque.
        var lignes = Lignes(j.CheminLignes!);
        Assert.Equal(3, lignes.Count);
        Assert.All(lignes, l => Assert.Equal("etape", l.GetProperty("type").GetString()));
        r = Instantane(chrono);
        Assert.False(r.GetProperty("complete").GetBoolean());
        var e = r.GetProperty("etapes");
        Assert.Equal(3, e.GetArrayLength());
        Assert.Equal(_t - 3000, e[0].GetProperty("fin").GetInt64()); // l'accueil finit quand la promenade commence
        Assert.False(e[2].GetProperty("jouee").GetBoolean());
        Assert.False(File.Exists(chrono + ".tmp"));

        _t += 1000;
        j.Terminer();
        r = Instantane(chrono);
        Assert.True(r.GetProperty("complete").GetBoolean());
        Assert.Equal(_t, r.GetProperty("fin").GetInt64());
        Assert.Equal("fin", Lignes(j.CheminLignes!)[^1].GetProperty("type").GetString());
        Assert.True(j.Fini);
        j.Terminer(); // une seule fin
        Assert.Single(Lignes(j.CheminLignes!), l => l.GetProperty("type").GetString() == "fin");
    }

    [Fact]
    public void UneEtapeEnEchecEstNoteeEtLaVisiteContinue()
    {
        var j = Journal();
        var jouees = new List<string>();
        // Le déroulé entier, joué comme FenetreVisite : une étape (« amis ») plante, les suivantes sont jouées.
        foreach (var (etape, debut, jouee) in Tournage.Planifier(_ => true))
        {
            _t = 1_800_000_000_000 + (long)(debut * 1000);
            j.Etape(etape.Nom, jouee);
            j.Executer(etape.Nom, () =>
            {
                if (etape.Nom == "amis") throw new InvalidOperationException("Specified element is already the logical child of another element.");
                jouees.Add(etape.Nom);
            });
        }
        j.Terminer();
        Assert.Equal(Tournage.Etapes.Count - 1, jouees.Count);
        Assert.Contains("clavier", jouees);
        Assert.Contains("fin", jouees);
        var erreur = Assert.Single(j.Erreurs);
        Assert.Equal("amis", erreur.Etape);
        Assert.Contains("InvalidOperationException", erreur.Message);
        // erreurs.txt, à côté de la chronologie, pour le zip.
        Assert.Equal(Path.Combine(_dossier, "erreurs.txt"), j.CheminErreurs);
        var texte = File.ReadAllText(j.CheminErreurs!);
        Assert.Contains("amis", texte);
        Assert.Contains("logical child", texte);
        var r = Instantane(Path.Combine(_dossier, "chronologie-brute.json"));
        Assert.True(r.GetProperty("complete").GetBoolean());
        Assert.Equal(1, r.GetProperty("erreurs").GetArrayLength());
        Assert.Equal(Tournage.Etapes.Count, r.GetProperty("etapes").GetArrayLength());
        Assert.Contains(Lignes(j.CheminLignes!), l => l.GetProperty("type").GetString() == "erreur");
    }

    [Fact]
    public void UneErreurQuiRevientAChaqueImageNeNoiePasLeJournal()
    {
        var j = Journal();
        j.Etape("meteo");
        for (int i = 0; i < 100; i++) j.Executer("meteo", () => throw new NullReferenceException("image"));
        Assert.Equal(JournalVisite.RepetitionsMax, j.Erreurs.Count);
        Assert.True(j.Executer("meteo", () => { }));
        // Une autre erreur, elle, est notée.
        j.Erreur("meteo", "autre chose");
        Assert.Equal(JournalVisite.RepetitionsMax + 1, j.Erreurs.Count);
    }

    [Fact]
    public void SansCheminToutResteEnMemoire()
    {
        var j = new JournalVisite(null, "0.9.45", null, () => 5);
        j.Etape("accueil");
        Assert.False(j.Executer("accueil", () => throw new ArgumentException("x")));
        j.Terminer();
        Assert.Null(j.CheminLignes);
        Assert.Single(j.Moments);
        Assert.Single(j.Erreurs);
        Assert.Empty(Directory.GetFiles(_dossier));
        Assert.Contains("\"complete\": true", j.Json());
    }

    [Fact]
    public void LesCadragesSuiventLeMenuPuisLeSousMenuEtSontSerialises()
    {
        var j = Journal();
        var c = new Cadreur(Ecran);
        var pilou = new CadreEcran(1150, 1150, 270, 240);
        var menu = new CadreEcran(1280, 700, 300, 520);
        var sousMenu = new CadreEcran(1580, 900, 260, 200);
        j.Etape("menu");
        j.Cadre(c.Observer("menu", "pilou", pilou, _t));
        _t += 200;
        j.Cadre(c.Observer("menu", "pilou", pilou with { X = 1160 }, _t)); // il bouge à peine : même cadrage
        _t += 600;
        j.Cadre(c.Observer("menu", "pilou+menu", pilou.Union(menu), _t)); // le menu s'ouvre : nouveau cadrage
        _t += 1500;
        j.Cadre(c.Observer("menu", "pilou+menu+sous-menu", pilou.Union(menu).Union(sousMenu), _t));
        _t += 1200;
        j.Cadre(c.Fermer(_t));
        Assert.Null(c.Fermer(_t)); // rien d'ouvert

        var cadres = j.Cadres;
        Assert.Equal(new[] { "pilou", "pilou+menu", "pilou+menu+sous-menu" }, cadres.Select(x => x.Quoi));
        Assert.Equal(1160 + 270, cadres[0].Zone.Droite); // le petit écart a agrandi le premier
        Assert.All(cadres, x => Assert.True(x.Fin >= x.Debut));
        Assert.Equal(cadres[0].Fin, cadres[1].Debut);
        Assert.True(cadres[2].Zone.Contient(sousMenu));

        var r = Instantane(Path.Combine(_dossier, "chronologie-brute.json"));
        var lus = r.GetProperty("etapes")[0].GetProperty("cadres");
        Assert.Equal(3, lus.GetArrayLength());
        var dernier = lus[2];
        Assert.Equal("pilou+menu+sous-menu", dernier.GetProperty("quoi").GetString());
        Assert.Equal(cadres[2].Debut, dernier.GetProperty("debut").GetInt64());
        Assert.Equal(cadres[2].Fin, dernier.GetProperty("fin").GetInt64());
        var zone = dernier.GetProperty("zone");
        Assert.Equal(cadres[2].Zone.X, zone.GetProperty("x").GetInt32());
        Assert.Equal(cadres[2].Zone.Hauteur, zone.GetProperty("hauteur").GetInt32());
        var zoom = dernier.GetProperty("zoom");
        double l = zoom.GetProperty("largeur").GetInt32(), h = zoom.GetProperty("hauteur").GetInt32();
        Assert.InRange(l / h, 16 / 9.0 - 0.01, 16 / 9.0 + 0.01);
        Assert.Equal(3, Lignes(j.CheminLignes!).Count(x => x.GetProperty("type").GetString() == "cadre"));
        Assert.Equal(2560, r.GetProperty("ecran").GetProperty("largeur").GetInt32());
    }

    [Fact]
    public void UnCadrageChangeAvecLEtapeEtResteDansLEcran()
    {
        var c = new Cadreur(Ecran);
        Assert.Null(c.Observer("boutique", "pilou+boutique", new CadreEcran(100, 700, 1300, 800), 0));
        var ferme = c.Observer("amis", "pilou+amis", new CadreEcran(500, 700, 900, 700), 100);
        Assert.NotNull(ferme);
        Assert.Equal("boutique", ferme!.Etape);
        Assert.Equal(1440, ferme.Zone.Bas); // coupé au bas de l'écran
        // Une zone hors de l'écran (Pilou parti chez Léo) ferme le cadrage en cours.
        var parti = c.Observer("amis", "pilou", new CadreEcran(-600, 1200, 300, 240), 300);
        Assert.Equal("amis", parti!.Etape);
        Assert.Null(c.Fermer(400));
        // Une fenêtre fermée (zone deux fois plus petite) : nouveau cadrage.
        c.Observer("x", "pilou+fenetre", new CadreEcran(400, 500, 1200, 900), 500);
        Assert.NotNull(c.Observer("x", "pilou+fenetre", new CadreEcran(1100, 1150, 300, 250), 600));
    }

    [Fact]
    public void LeZoom169ContientLaZoneEtResteDansLEcran()
    {
        var petit = Tournage.Zoom169(new CadreEcran(2400, 1300, 100, 100), Ecran);
        Assert.InRange(petit.Largeur, Ecran.Largeur / 3 - 1, Ecran.Largeur / 3 + 1); // jamais plus serré qu'un tiers de l'écran
        Assert.InRange(petit.Largeur / (double)petit.Hauteur, 1.77, 1.78);
        Assert.True(Ecran.Contient(petit));
        Assert.True(petit.Contient(new CadreEcran(2400, 1300, 100, 100)));

        var grand = Tournage.Zoom169(new CadreEcran(100, 300, 1500, 1100), Ecran);
        Assert.True(grand.Contient(new CadreEcran(100, 300, 1500, 1100)));
        Assert.True(Ecran.Contient(grand));

        Assert.Equal(Ecran, Tournage.Zoom169(new CadreEcran(0, 0, 3000, 2000), Ecran));
        Assert.Equal(Ecran, Tournage.Zoom169(new CadreEcran(5, 5, 0, 0), Ecran));
        // Écran d'un autre format (16:10) : 16:9 quand même.
        var ecran1610 = new CadreEcran(-1920, 0, 1920, 1200);
        var z = Tournage.Zoom169(new CadreEcran(-1900, 100, 1800, 1050), ecran1610);
        Assert.InRange(z.Largeur / (double)z.Hauteur, 1.77, 1.78);
        Assert.True(ecran1610.Contient(z));
    }

    [Fact]
    public void LesFenetresSePosentACoteDePilouEnBas()
    {
        var zone = new Place(0, 0, 2560, 1392);
        // Pilou au milieu : la fenêtre à sa gauche, son bas juste au-dessus du sol.
        var a = Tournage.PoserPres(zone, 1280, 135, 560, 680);
        Assert.Equal(1280 - 135 - 24 - 560, a.X);
        Assert.Equal(1392 - 24 - 680, a.Y);
        Assert.True(a.Droite <= 1280 - 135);
        Assert.True(a.Y > zone.Hauteur / 3); // dans le tiers bas/milieu
        // Pilou tout à gauche : à sa droite.
        var b = Tournage.PoserPres(zone, 200, 135, 1000, 720);
        Assert.Equal(200 + 135 + 24, b.X);
        // Trop grande pour l'écran : réduite, et toujours dedans.
        var c = Tournage.PoserPres(new Place(0, 0, 1280, 700), 640, 100, 1600, 900);
        Assert.True(c.X >= 0 && c.Droite <= 1280 && c.Y >= 0 && c.Bas <= 700);
        Assert.True(c.Largeur < 1600 && c.Hauteur < 900);
    }

    [Fact]
    public void PilouEstPlusGrandPendantLeTournage()
    {
        Assert.Equal(2.6, Tournage.TailleTournage(1392)); // 2560 × 1440, barre de 48 : le double de 1,3
        Assert.Equal(1.9, Tournage.TailleTournage(1032)); // 1920 × 1080
        Assert.Equal(3.0, Tournage.TailleTournage(2112)); // 4K à 100 % : plafonné
        Assert.Equal(1.3, Tournage.TailleTournage(400));
        Assert.Equal(1.3, Tournage.TailleTournage(double.NaN));
    }

    [Fact]
    public void LeDecorPeutEtreCoupeEtLaDureeEstDonneeAuScript()
    {
        var (o, reste) = OptionsTournage.Analyser(new[] { "--visite-guidee=c.json", "--sans-decor", "--ecran=gauche", "demo" });
        Assert.True(o.SansDecor);
        Assert.Equal(new[] { "demo" }, reste);
        Assert.False(OptionsTournage.Analyser(new[] { "--visite-guidee" }).Options.SansDecor);

        using var d = JsonDocument.Parse(Tournage.Disponibles("0.9.45"));
        double attendu = Tournage.Planifier(Tournage.Disponible).Where(x => x.Jouee).Sum(x => x.Etape.Secondes);
        Assert.Equal(attendu, d.RootElement.GetProperty("duree_s").GetDouble(), 3);
        Assert.InRange(attendu, 60, 150);
    }

    [Fact]
    public void LesCadresSUnissentEtSeCroisent()
    {
        var a = new CadreEcran(0, 0, 100, 100);
        var b = new CadreEcran(50, 50, 100, 100);
        Assert.Equal(new CadreEcran(0, 0, 150, 150), a.Union(b));
        Assert.Equal(new CadreEcran(50, 50, 50, 50), a.Inter(b));
        Assert.True(a.Inter(new CadreEcran(200, 200, 10, 10)).Vide);
        Assert.Equal(b, new CadreEcran(0, 0, 0, 0).Union(b));
        Assert.True(a.Elargi(10).Contient(a));
        Assert.False(a.Contient(b));
    }
}
