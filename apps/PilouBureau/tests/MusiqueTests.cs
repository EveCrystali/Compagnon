using PilouBureau;
using Xunit;

// Musiques et ambiances (docs/SONS.md) : mêmes échantillons que Musique.java et outils/sons/sons.py.
public class MusiqueTests
{
    private static string Racine()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d is not null && !File.Exists(Path.Combine(d.FullName, "assets", "musiques.txt"))) d = d.Parent;
        return d?.FullName ?? throw new DirectoryNotFoundException("racine du dépôt");
    }

    private static (Dictionary<string, Musique.Morceau> Morceaux, Dictionary<string, string> Decors) Catalogue() =>
        Musique.Lire(File.ReadAllText(Path.Combine(Racine(), "assets", "musiques.txt")));

    [Fact]
    public void Memes_echantillons_que_la_reference()
    {
        var c = Catalogue();
        int vus = 0;
        foreach (var l in File.ReadAllLines(Path.Combine(Racine(), "outils", "sons", "musiques-reference.txt")))
        {
            if (l.StartsWith('#') || l.Trim().Length == 0) continue;
            var p = l.Split('|').Select(x => x.Trim()).ToArray();
            var s = Musique.Synthetiser(c.Morceaux[p[0]]);
            Assert.Equal(int.Parse(p[1]), s.Length);
            Assert.Equal(p[3], Sons.Empreinte(s));
            vus++;
        }
        Assert.Equal(c.Morceaux.Count, vus);
    }

    [Fact]
    public void Une_musique_par_ton_et_des_ambiances_pour_les_decors()
    {
        var c = Catalogue();
        foreach (var t in Musique.Tons) Assert.True(c.Morceaux.ContainsKey(t), t);
        Assert.Equal("prologue", Musique.Pour("prologue", "humour"));
        Assert.Equal("mystere", Musique.Pour("phare-eteint", "mystere"));
        Assert.Null(Musique.Pour("inconnue", "epique"));
        Assert.All(c.Decors.Values.Distinct(), a => Assert.True(c.Morceaux.ContainsKey(a), a));
        Assert.Equal("mer", c.Decors["port-trebrume"]);
    }

    [Fact]
    public void Les_boucles_restent_basses_et_sans_saut()
    {
        foreach (var (id, m) in Catalogue().Morceaux)
        {
            var s = Musique.Synthetiser(m);
            Assert.True(s.Max(x => Math.Abs((int)x)) <= 6000, id);
            var sauts = Enumerable.Range(1, s.Length - 1).Select(i => Math.Abs(s[i] - s[i - 1])).OrderBy(x => x).ToArray();
            Assert.True(Math.Abs(s[0] - s[^1]) <= sauts[sauts.Length * 99 / 100], id + " : clic à la jonction");
            Assert.InRange(s.Length * 1000L / Musique.Taux, Musique.Tons.Contains(id) ? 30000 : 20000, 60000);
        }
    }

    [Fact]
    public void Discrete_par_defaut_et_aucune_coupe_tout()
    {
        Assert.Equal("discrete", new Reglages().Musique);
        Assert.Equal("normaux", System.Text.Json.JsonSerializer.Deserialize<Reglages>("""{"Sons":"normaux"}""")!.Sons);
        Assert.Equal(0, Musique.Gain("aucune"));
        Assert.Equal(65536 * 3 / 8, Musique.Gain("discrete"));
        Assert.Equal(65536, Musique.Gain("normale"));
    }

    [Fact]
    public void Fondu_d_entree_puis_de_sortie()
    {
        var boucle = Enumerable.Repeat((short)8000, 1000).ToArray();
        var t = new Melangeur(_ => boucle);
        var bloc = new short[Musique.Taux / 10];
        t.Viser("humour", null, 65536);
        t.Remplir(bloc);
        Assert.True(bloc[0] < 100, "le son commence à zéro");
        Assert.True(bloc[^1] < 8000, "pas encore à plein volume après 100 ms");
        for (int i = 0; i < 15; i++) t.Remplir(bloc);
        Assert.Equal(8000, bloc[^1]);
        t.Viser(null, null, 65536);
        for (int i = 0; i < 10; i++) t.Remplir(bloc);
        Assert.Equal(0, bloc[^1]);
        Assert.True(t.Silencieux);
    }

    [Fact]
    public void Changer_de_decor_croise_les_ambiances()
    {
        var t = new Melangeur(id => Enumerable.Repeat((short)(id == "mer" ? 4000 : 2000), 500).ToArray());
        var bloc = new short[Musique.Taux / 10];
        t.Viser(null, "mer", 65536);
        for (int i = 0; i < 20; i++) t.Remplir(bloc);
        Assert.Equal(4000, bloc[^1]);
        t.Viser(null, "vent", 65536);
        t.Remplir(bloc);
        Assert.InRange(bloc[^1], 2000, 6000);
        for (int i = 0; i < 20; i++) t.Remplir(bloc);
        Assert.Equal(2000, bloc[^1]);
    }
}
