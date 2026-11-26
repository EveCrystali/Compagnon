using System.Reflection;
using PilouBureau;
using Xunit;

// Pilou au clavier et Pilou photographe : compteur de frappes, scènes animées, anti-doublon des captures.
public class GestesTests
{
    [Fact]
    public void LeCompteurNeRecoitQueDesInstants()
    {
        // Garantie de confidentialité par construction : aucune méthode publique ne prend de touche, de caractère
        // ni de code ; Frappe ne reçoit qu'un instant.
        var publiques = typeof(CompteurFrappes).GetMethods(BindingFlags.Public | BindingFlags.Instance | BindingFlags.DeclaredOnly);
        foreach (var m in publiques)
            Assert.All(m.GetParameters(), p => Assert.Equal(typeof(double), p.ParameterType));
        var champs = typeof(CompteurFrappes).GetFields(BindingFlags.NonPublic | BindingFlags.Instance);
        Assert.All(champs, f => Assert.DoesNotContain("char", f.FieldType.ToString(), StringComparison.OrdinalIgnoreCase));
        Assert.All(champs, f => Assert.NotEqual(typeof(string), f.FieldType));
    }

    [Fact]
    public void RafaleSeulementAuDelaDuSeuilDansLaFenetre()
    {
        var c = new CompteurFrappes();
        for (int i = 0; i < CompteurFrappes.Seuil - 1; i++) c.Frappe(i * 200);
        double t = (CompteurFrappes.Seuil - 2) * 200;
        Assert.False(c.Rafale(t));
        c.Frappe(t + 100);
        Assert.True(c.Rafale(t + 100));
        // Cinq secondes plus tard, les vieilles frappes sont oubliées.
        Assert.False(c.Rafale(t + 100 + CompteurFrappes.Fenetre + 1));
        Assert.Equal(0, c.Recentes(t + 100 + CompteurFrappes.Fenetre + 1));
    }

    [Fact]
    public void FrappesLentesNeFontPasDeRafale()
    {
        var c = new CompteurFrappes();
        for (int i = 0; i < 100; i++) c.Frappe(i * 1000.0); // une par seconde : 5 dans la fenêtre
        Assert.False(c.Rafale(99_000));
        Assert.True(c.Recentes(99_000) <= 6);
    }

    [Fact]
    public void LeCompteurNeGardePasPlusQueNecessaire()
    {
        var c = new CompteurFrappes();
        for (int i = 0; i < 10_000; i++) c.Frappe(1000); // tout au même instant
        Assert.True(c.Recentes(1000) <= 4 * CompteurFrappes.Seuil);
    }

    [Fact]
    public void SilenceDepuisLaDerniereFrappe()
    {
        var c = new CompteurFrappes();
        Assert.True(double.IsPositiveInfinity(c.Silence(0)));
        c.Frappe(500);
        Assert.Equal(1500, c.Silence(2000));
    }

    [Fact]
    public void SceneClavierEntreTapeEtSort()
    {
        var s = new SceneClavier();
        Assert.False(s.Avancer(0, rafale: false, silence: 0, permis: true));
        Assert.Equal(EtapeClavier.Aucune, s.Etape);
        Assert.True(s.Avancer(100, rafale: true, silence: 0, permis: true));
        Assert.Equal(EtapeClavier.Entree, s.Etape);
        // Pendant l'entrée : pouf et tour sur lui-même, puis assis devant le clavier.
        var d0 = s.Dessin(150);
        Assert.Contains(d0.Objets, o => o.StartsWith("pouf-"));
        Assert.DoesNotContain("clavier-mini", d0.Objets);
        var d1 = s.Dessin(100 + SceneClavier.DureeEntree * 0.9);
        Assert.Contains("clavier-mini", d1.Objets);
        Assert.Equal(1, d1.Assis);
        s.Avancer(100 + SceneClavier.DureeEntree, true, 0, true);
        Assert.Equal(EtapeClavier.Tape, s.Etape);
        var tape = s.Dessin(5000);
        Assert.Equal(new[] { "clavier-mini" }, tape.Objets);
        Assert.True(tape.Concentre);
        // Il tape tant qu'on tape, même sans rafale (une frappe de temps en temps suffit).
        s.Avancer(20_000, false, 3000, true);
        Assert.Equal(EtapeClavier.Tape, s.Etape);
        // Neuf secondes sans frappe : pouf inverse.
        s.Avancer(30_000, false, SceneClavier.SilenceSortie, true);
        Assert.Equal(EtapeClavier.Sortie, s.Etape);
        Assert.Contains(s.Dessin(30_100).Objets, o => o.StartsWith("pouf-"));
        s.Avancer(30_000 + SceneClavier.DureeSortie, false, 99_999, true);
        Assert.Equal(EtapeClavier.Aucune, s.Etape);
        Assert.Empty(s.Dessin(40_000).Objets);
    }

    [Fact]
    public void SceneClavierJamaisSansPermission()
    {
        var s = new SceneClavier();
        Assert.False(s.Avancer(0, rafale: true, silence: 0, permis: false)); // plein écran, visite, mini-jeu…
        Assert.Equal(EtapeClavier.Aucune, s.Etape);
        s.Avancer(10, true, 0, true);
        s.Avancer(10 + SceneClavier.DureeEntree, true, 0, true);
        Assert.Equal(EtapeClavier.Tape, s.Etape);
        // Il se cache (plein écran) ou part en visite : il range tout de suite le clavier.
        s.Avancer(5000, true, 0, false);
        Assert.Equal(EtapeClavier.Sortie, s.Etape);
    }

    [Fact]
    public void LeTourPasseParLeDos()
    {
        var s = new SceneClavier();
        s.Avancer(0, true, 0, true);
        var vus = Enumerable.Range(0, 4).Select(i => s.Dessin(i * SceneClavier.PasTour + 10)).ToList();
        Assert.Contains(vus, d => d.Dos);
        Assert.Contains(vus, d => d.Regard == 1);
        Assert.Contains(vus, d => d.Regard == -1);
    }

    [Fact]
    public void UneSeuleAnimationParCapture()
    {
        var a = new AntiDoublon();
        // Impr. écran, puis l'image dans le presse-papiers, puis le fichier dans Captures d'écran : une capture.
        Assert.True(a.Accepter(1000));
        Assert.False(a.Accepter(1040));
        Assert.False(a.Accepter(1600));
        Assert.False(a.Accepter(2999));
        // Une nouvelle capture, plus tard.
        Assert.True(a.Accepter(3000));
        Assert.False(a.Accepter(3500));
        Assert.True(a.Accepter(9000));
    }

    [Fact]
    public void ScenePhotoFlashPuisPolaroid()
    {
        var p = new ScenePhoto();
        Assert.Empty(p.Dessin(0).Objets);
        Assert.True(p.Declencher(1000));
        Assert.False(p.Declencher(1500)); // déjà en cours
        Assert.True(p.Active(1500));
        Assert.Equal(new[] { "appareil-photo" }, p.Dessin(1100).Objets);
        var flash = p.Dessin(1460);
        Assert.Contains("photo-flash", flash.Objets);
        Assert.InRange(flash.Flash, 0.01, 1);
        Assert.Equal("CLIC !", flash.Bruit);
        // Le flash est bref : plus rien 200 ms après.
        Assert.Equal(0, p.Dessin(1700).Flash);
        Assert.Contains("polaroid-1", p.Dessin(1700).Objets);
        Assert.Contains("polaroid-4", p.Dessin(1000 + ScenePhoto.Duree - 10).Objets);
        Assert.False(p.Active(1000 + ScenePhoto.Duree));
        Assert.Empty(p.Dessin(1000 + ScenePhoto.Duree).Objets);
    }

    [Fact]
    public void LesSpritesDesGestesExistent()
    {
        var b = Banque.DepuisDossier(Path.Combine(RacineAssets(), "assets"));
        var ids = new HashSet<string>();
        var s = new SceneClavier();
        s.Avancer(0, true, 0, true);
        for (int t = 0; t < 1000; t += 20) ids.UnionWith(s.Dessin(t).Objets);
        s.Avancer(1000, true, 0, true);
        s.Avancer(2000, false, 99_999, true);
        for (int t = 2000; t < 2800; t += 20) ids.UnionWith(s.Dessin(t).Objets);
        var p = new ScenePhoto();
        p.Declencher(0);
        for (int t = 0; t < 3000; t += 20) ids.UnionWith(p.Dessin(t).Objets);
        ids.UnionWith(new[] { "enveloppe-notif", "enveloppe-close" });
        Assert.True(ids.Count >= 13);
        Assert.All(ids, id => Assert.NotNull(b[id]));
    }

    [Fact]
    public void LaTenueGardeSesLunettesPendantUnGeste()
    {
        var slots = new Dictionary<string, string>
        {
            ["tenue-code-lunettes"] = "yeux", ["tenue-code-clavier"] = "objet", ["tenue-jeu-manette"] = "main", ["tenue-jeu-casque"] = "tete",
        };
        var garde = GestesPilou.TenueCompatible(new[] { "tenue-code-lunettes", "tenue-code-clavier" }, id => slots.GetValueOrDefault(id));
        Assert.Equal(new[] { "tenue-code-lunettes" }, garde);
        garde = GestesPilou.TenueCompatible(new[] { "tenue-jeu-casque", "tenue-jeu-manette" }, id => slots.GetValueOrDefault(id));
        Assert.Equal(new[] { "tenue-jeu-casque" }, garde);
    }

    [Fact]
    public void SuccesDactyloEtPhotographe()
    {
        var s = new Stats(new Dictionary<string, long>(), 0, 0, 0, new DateTime(2026, 1, 5, 14, 0, 0), "", SeancesClavier: 25, Captures: 9);
        var nouveaux = Succes.Nouveaux(s, Array.Empty<string>()).Select(d => d.Id).ToList();
        Assert.Contains("dactylo", nouveaux);
        Assert.DoesNotContain("photographe", nouveaux);
        Assert.Equal("9 / 10", Succes.Progres(Succes.Tous.Single(d => d.Id == "photographe"), s));
    }

    private static string RacineAssets()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d is not null && !File.Exists(Path.Combine(d.FullName, "assets", "index.txt"))) d = d.Parent;
        return d!.FullName;
    }

    [Fact]
    public void SceneClavierSArreteMemeSiOnTapeSansFin()
    {
        var s = new SceneClavier();
        Assert.True(s.Avancer(0, true, 0, true));
        s.Avancer(SceneClavier.DureeEntree, true, 0, true);
        Assert.Equal(EtapeClavier.Tape, s.Etape);
        double t = SceneClavier.DureeEntree;
        // frappe continue : le silence reste nul, mais la séance est bornée
        while (t + 500 < SceneClavier.DureeEntree + SceneClavier.DureeMax) { t += 500; s.Avancer(t, true, 0, true); }
        Assert.Equal(EtapeClavier.Tape, s.Etape);
        t = SceneClavier.DureeEntree + SceneClavier.DureeMax;
        s.Avancer(t, true, 0, true);
        Assert.Equal(EtapeClavier.Sortie, s.Etape);
        s.Avancer(t + SceneClavier.DureeSortie, true, 0, true);
        Assert.Equal(EtapeClavier.Aucune, s.Etape);
        // repos : la rafale suivante ne le ramène pas tout de suite
        Assert.False(s.Avancer(t + SceneClavier.DureeSortie + 60_000, true, 0, true));
        Assert.True(s.Avancer(t + SceneClavier.DureeSortie + SceneClavier.ReposApres + 1, true, 0, true));
    }
}
