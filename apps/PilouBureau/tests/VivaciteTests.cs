using PilouBureau;
using Xunit;

// Pilou un peu moins hyperactif : réactions cosmétiques tirées au sort, temps de repos commun, rien pendant la
// saisie ; clavier et photo qui se reposent ; météo plus discrète. Hasard seedé : résultats reproductibles.
public class VivaciteTests
{
    // Hasard qui rend une suite de valeurs choisie (pour tester les deux branches du tirage).
    private sealed class Suite : Random
    {
        private readonly Queue<double> _v;
        public Suite(params double[] v) => _v = new Queue<double>(v);
        public override double NextDouble() => _v.Count > 0 ? _v.Dequeue() : 0.99;
    }

    [Fact]
    public void LeTirageDecideEtLeReposSuit()
    {
        var r = new Retenue(new Suite(0.7, 0.2, 0.1, 0.1));
        Assert.False(r.Tenter(0, saisie: false));                 // 0,7 ≥ 0,5 : occasion manquée
        Assert.True(double.IsNegativeInfinity(r.Derniere));        // …qui ne consomme pas le repos
        Assert.True(r.Tenter(1000, false));                        // 0,2 : elle part
        Assert.False(r.Tenter(1000 + Vivacite.Repos - 1, false));  // repos pas fini : pas même de tirage
        Assert.True(r.Tenter(1000 + Vivacite.Repos, false));       // 0,1
    }

    [Fact]
    public void RienPendantLaSaisie()
    {
        var r = new Retenue(new Suite(0.0, 0.0));
        Assert.False(r.Libre(0, saisie: true));
        Assert.False(r.Tenter(0, saisie: true));
        Assert.True(r.Tenter(10, saisie: false));
    }

    [Fact]
    public void NoterRelanceLeRepos()
    {
        var r = new Retenue(new Suite(0.0));
        Assert.True(r.Libre(0, false));
        r.Noter(5000);                                   // un jeu proposé, une photo, une séance clavier
        Assert.False(r.Libre(5000 + Vivacite.Repos - 1, false));
        Assert.True(r.Libre(5000 + Vivacite.Repos, false));
    }

    [Fact]
    public void EnvironUneFoisSurDeuxEtAuPlusUneToutesLesDeuxMinutesEtDemie()
    {
        var r = new Retenue(new Random(1234));
        // Une occasion par seconde pendant deux heures.
        var parties = new List<double>();
        for (double t = 0; t < 2 * 3_600_000; t += 1000)
            if (r.Tenter(t, false)) parties.Add(t);
        Assert.All(parties.Zip(parties.Skip(1)), p => Assert.True(p.Second - p.First >= Vivacite.Repos));
        Assert.InRange(parties.Count, 40, 2 * 3_600_000 / Vivacite.Repos + 1);

        // Des occasions rares (une seule, séparée par plus que le repos) : à peu près une sur deux part.
        var rare = new Retenue(new Random(42));
        int n = 0;
        for (int i = 0; i < 1000; i++)
            if (rare.Tenter(i * 1_000_000.0, false)) n++;
        Assert.InRange(n, 400, 600);
    }

    [Fact]
    public void AuTravailEtSaisie()
    {
        Assert.True(Vivacite.AuTravail(500, ""));           // souris ou clavier à l'instant
        Assert.True(Vivacite.AuTravail(600_000, "code"));   // IDE au premier plan
        Assert.True(Vivacite.AuTravail(600_000, "tableur"));
        Assert.False(Vivacite.AuTravail(60_000, "musique"));
        Assert.False(Vivacite.AuTravail(60_000, ""));
        Assert.True(Vivacite.EnSaisie(1000, crochet: true, inactifMs: 99_999));
        Assert.False(Vivacite.EnSaisie(Vivacite.Saisie, crochet: true, inactifMs: 0));
        Assert.True(Vivacite.EnSaisie(double.PositiveInfinity, crochet: false, inactifMs: 500));
        Assert.False(Vivacite.EnSaisie(0, crochet: false, inactifMs: 5000));
    }

    [Fact]
    public void LeClavierSeReposeDixMinutesApresUneSeance()
    {
        var s = new SceneClavier();
        Assert.True(s.Avancer(0, rafale: true, silence: 0, permis: true));
        s.Avancer(SceneClavier.DureeEntree, true, 0, true);
        s.Avancer(20_000, false, SceneClavier.SilenceSortie, true);
        Assert.Equal(EtapeClavier.Sortie, s.Etape);
        double fin = 20_000 + SceneClavier.DureeSortie;
        s.Avancer(fin, false, 99_999, true);
        Assert.Equal(EtapeClavier.Aucune, s.Etape);
        // Nouvelle rafale tout de suite, puis 9 min plus tard : il ne revient pas.
        Assert.False(s.Avancer(fin + 1000, true, 0, true));
        Assert.False(s.Avancer(fin + 9 * 60_000, true, 0, true));
        Assert.Equal(EtapeClavier.Aucune, s.Etape);
        // Dix minutes après : nouvelle séance.
        Assert.True(s.Avancer(fin + SceneClavier.ReposApres, true, 0, true));
        // L'essai (--essai=clavier) passe outre le repos.
        var e = new SceneClavier();
        e.Avancer(0, true, 0, true);
        e.Avancer(SceneClavier.DureeEntree, true, 0, true);
        e.Avancer(5000, true, 0, false);
        e.Avancer(5000 + SceneClavier.DureeSortie, false, 0, true);
        e.OublierRepos();
        Assert.True(e.Avancer(6000, true, 0, true));
    }

    [Fact]
    public void UneRafaleDemandePlusDeFrappesQuAvant()
    {
        var c = new CompteurFrappes();
        for (int i = 0; i < 15; i++) c.Frappe(i * 100); // l'ancien seuil
        Assert.False(c.Rafale(1500));
        Assert.Equal(20, CompteurFrappes.Seuil);
    }

    [Fact]
    public void AuPlusUnePhotoToutesLesDeuxMinutes()
    {
        var p = new ScenePhoto();
        Assert.True(p.Declencher(0));
        Assert.False(p.Declencher(ScenePhoto.Duree + 1));       // scène finie, mais l'appareil se repose
        Assert.False(p.Declencher(ScenePhoto.Repos - 1));
        Assert.True(p.Declencher(ScenePhoto.Repos));
        Assert.True(ScenePhoto.Repos >= 120_000);
    }

    [Fact]
    public void LeFlashEstPlusCourt()
    {
        var p = new ScenePhoto();
        p.Declencher(0);
        Assert.True(p.Dessin(460).Flash > 0);
        Assert.Equal(0, p.Dessin(450 + ScenePhoto.DureeFlash).Flash);
        Assert.True(ScenePhoto.DureeFlash <= 150);
    }

    [Fact]
    public void LEclairEstRareEtBref()
    {
        int vus = 0, n = 0;
        for (double t = 0; t < 120_000; t += 20, n++)
            if (Meteo.Effet(Meteo.Orage, Array.Empty<string>(), t).Sprites.Contains("meteo-eclair")) vus++;
        // 280 ms toutes les 12 s : moins de 3 % du temps (un tiers avant).
        Assert.InRange(vus / (double)n, 0.015, 0.03);
        Assert.Contains("meteo-eclair", Meteo.Effet(Meteo.Orage, Array.Empty<string>(), 0).Sprites);
        Assert.DoesNotContain("meteo-eclair", Meteo.Effet(Meteo.Orage, Array.Empty<string>(), 5000).Sprites);
        // La pluie, elle, reste là tout le temps.
        Assert.Contains("meteo-averse", Meteo.Effet(Meteo.Orage, Array.Empty<string>(), 5000).Sprites);
    }

    [Fact]
    public void LesParticulesMeteoSontClairsemeesEtTranslucides()
    {
        var b = Banque.DepuisDossier(Path.Combine(RacineAssets(), "assets"));
        foreach (var (id, max) in new[] { ("meteo-pluie", 70), ("meteo-averse", 80), ("meteo-neige", 20), ("meteo-vent", 30), ("meteo-eclair", 20) })
        {
            var s = b[id];
            Assert.NotNull(s);
            for (int k = 0; k < s!.Images.Count; k++)
            {
                var g = Banque.Grille(s, s.Duree * k + 1);
                int pleins = 0;
                foreach (var c in g)
                {
                    if (c == 0) continue;
                    pleins++;
                    Assert.True(c >> 24 < 0xc0, $"{id} : pixel trop opaque ({c:x8})");
                }
                Assert.True(pleins <= max, $"{id} image {k} : {pleins} pixels (au plus {max})");
            }
        }
    }

    private static string RacineAssets()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d is not null && !File.Exists(Path.Combine(d.FullName, "assets", "index.txt"))) d = d.Parent;
        return d!.FullName;
    }
}
