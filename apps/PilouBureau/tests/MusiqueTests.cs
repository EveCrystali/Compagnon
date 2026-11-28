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
    public void Chaque_scene_du_theatre_a_la_musique_de_son_ton()
    {
        // Une campagne passée au théâtre (assets/scenes/<campagne>.txt) : sa musique est celle de son ton (Petit Nuage :
        // « emotion »), elle existe au catalogue ; chaque décor de scène a une ambiance connue ou aucune.
        var c = Catalogue();
        var dossier = Path.Combine(CampagnesVecteurs.Racine().FullName, "assets", "scenes");
        int n = 0;
        foreach (var f in Directory.EnumerateFiles(dossier, "*.txt").Where(f => Path.GetFileName(f) != "animations.txt"))
        {
            var id = Path.GetFileNameWithoutExtension(f);
            var camp = Campagnes.Charger(id);
            Assert.NotNull(camp);
            var m = Musique.Pour(id, camp!.Ton);
            Assert.NotNull(m);
            Assert.True(c.Morceaux.ContainsKey(m!), $"{id} : {m}");
            foreach (var (decor, _) in Theatre.LireScenes(File.ReadAllText(f)))
            {
                var a = c.Decors.GetValueOrDefault(decor);
                Assert.True(a is null || c.Morceaux.ContainsKey(a), $"{id}/{decor} : {a}");
                n++;
            }
        }
        Assert.Equal("emotion", Musique.Pour("petit-nuage", Campagnes.Charger("petit-nuage")!.Ton));
        Assert.Equal("vent", c.Decors["halte-girouette"]);
        Assert.True(n >= 40, $"{n} scènes");
    }

    [Fact]
    public void Les_boucles_restent_basses_et_sans_saut()
    {
        foreach (var (id, m) in Catalogue().Morceaux)
        {
            var s = Musique.Synthetiser(m);
            Assert.True(s.Max(x => Math.Abs((int)x)) <= 6000, id);
            if (m.Motif)
            {
                // Un motif (une fin, le thème court) : joué une fois, il commence et finit à zéro.
                Assert.True(Math.Abs((int)s[0]) <= 64 && Math.Abs((int)s[^1]) <= 64, id + " : bords");
                Assert.InRange(s.Length * 1000L / Musique.Taux, 3000, 8500);
                continue;
            }
            var sauts = Enumerable.Range(1, s.Length - 1).Select(i => Math.Abs(s[i] - s[i - 1])).OrderBy(x => x).ToArray();
            Assert.True(Math.Abs(s[0] - s[^1]) <= sauts[sauts.Length * 99 / 100], id + " : clic à la jonction");
            Assert.InRange(s.Length * 1000L / Musique.Taux, Musique.Tons.Contains(id) ? 30000 : 20000, 60000);
        }
    }

    [Fact]
    public void Le_champ_musique_choisit_le_morceau()
    {
        var c = Catalogue().Morceaux;
        foreach (var id in new[] { "pilou-10", "pilou-25", "pilou-40", "pilou-court", "fin-bonne", "fin-douce-amere", "fin-mauvaise", "fin-secrete" })
            Assert.True(c.ContainsKey(id), id);
        foreach (var t in new[] { "humour", "mystere", "emotion" })
        {
            Assert.True(c.ContainsKey(t + "-calme") && c.ContainsKey(t + "-tension"), t);
            Assert.Equal(t + "-tension", Musique.Pour("x", t, "tension"));
            Assert.Equal(t + "-calme", Musique.Pour("x", t, "calme"));
        }
        Assert.Equal("emotion", Musique.Pour("petit-nuage", "emotion", null));
        Assert.Equal("pilou-25", Musique.Pour("evolution", "emotion", "pilou-25"));
        Assert.Equal("fin-secrete", Musique.Pour("phare-eteint", "mystere", "fin-secrete"));
        Assert.Equal("prologue", Musique.Pour("prologue", "humour", "calme"));     // pas de variante : la boucle du ton
        Assert.Equal("mystere", Musique.Pour("phare-eteint", "mystere", "inconnu"));
        Assert.True(Musique.EstMotif("fin-bonne") && Musique.EstMotif("pilou-court") && !Musique.EstMotif("pilou-10"));
    }

    [Fact]
    public void Un_motif_joue_une_fois_puis_le_silence()
    {
        var motif = Enumerable.Repeat((short)5000, Musique.Taux / 5).ToArray();       // 200 ms
        var boucle = Enumerable.Repeat((short)2000, 1000).ToArray();
        var t = new Melangeur(id => id == "fin" ? motif : boucle, id => id == "fin");
        var bloc = new short[Musique.Taux / 10];
        t.Viser("emotion", null, 65536);
        for (int i = 0; i < 20; i++) t.Remplir(bloc);
        Assert.Equal(2000, bloc[^1]);
        t.Viser("fin", null, 65536);
        t.Remplir(bloc);
        Assert.True(bloc[0] > 5000, "le motif part tout de suite, par-dessus la boucle qui s'efface");
        for (int i = 0; i < 15; i++) { t.Viser("fin", null, 65536); t.Remplir(bloc); }
        Assert.Equal(0, bloc[^1]);
        Assert.True(t.Silencieux, "joué une fois, il ne recommence pas tant qu'on reste sur la fin");
        t.Viser("emotion", null, 65536);
        t.Viser("fin", null, 65536);
        t.Remplir(bloc);
        Assert.True(bloc[0] > 4000, "après un autre morceau, il peut rejouer");
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
