using PilouBureau;
using Xunit;

public class SonsTests
{
    private static string Racine()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d is not null && !File.Exists(Path.Combine(d.FullName, "assets", "index.txt"))) d = d.Parent;
        Assert.NotNull(d);
        return d!.FullName;
    }

    private static Dictionary<string, List<NoteSon>> Catalogue() =>
        Sons.Lire(File.ReadAllText(Path.Combine(Racine(), "assets", "sons.txt")));

    // Mêmes échantillons que outils/sons/sons.py et que le téléphone (SonsTest.java).
    [Fact]
    public void Memes_echantillons_que_la_reference()
    {
        var c = Catalogue();
        var lignes = File.ReadAllLines(Path.Combine(Racine(), "outils", "sons", "sons-reference.txt"))
            .Where(l => !l.StartsWith('#') && l.Trim() != "").ToList();
        Assert.Equal(c.Count, lignes.Count);
        foreach (var l in lignes)
        {
            var p = l.Split('|').Select(x => x.Trim()).ToArray();
            var s = Sons.Synthetiser(c[p[0]]);
            Assert.True(s.Length == int.Parse(p[1]), p[0] + " : longueur");
            Assert.True(Sons.Empreinte(s) == p[3], p[0] + " : empreinte");
        }
    }

    [Fact]
    public void Chaque_son_du_code_est_decrit()
    {
        var c = Catalogue();
        foreach (var s in Enum.GetValues<Son>()) Assert.True(c.ContainsKey(Sons.Id(s)), Sons.Id(s));
        Assert.Equal(Enum.GetValues<Son>().Length, c.Count);
    }

    // Douceur : pas de clic au début ni à la fin, crête sous -6 dBFS, moins d'une seconde.
    [Fact]
    public void Sons_doux_et_courts()
    {
        foreach (var (nom, notes) in Catalogue())
        {
            var s = Sons.Synthetiser(notes);
            Assert.True(Math.Abs((int)s[0]) <= 64 && Math.Abs((int)s[^1]) <= 64, nom + " : bords");
            Assert.True(s.Max(x => Math.Abs((int)x)) <= 16384, nom + " : crête");
            Assert.True(s.Length < Sons.Taux * 0.9, nom + " : durée");
            var d = Sons.Adoucir(s);
            Assert.True(d.Max(x => Math.Abs((int)x)) <= 16384 * 3 / 16 + 1, nom + " : discret");
        }
    }

    [Fact]
    public void Wav_bien_forme()
    {
        var w = Sons.Wav(new short[] { 0, 1000, -1000, 0 });
        Assert.Equal(44 + 8, w.Length);
        Assert.Equal("RIFF", System.Text.Encoding.ASCII.GetString(w, 0, 4));
        Assert.Equal(22050, BitConverter.ToInt32(w, 24));
    }

    [Fact]
    public void Aucun_son_par_defaut()
    {
        Assert.Equal("aucun", new Reglages().Sons);
        Assert.False(new GardeSons().Peut(Son.Caresse, 0, "aucun", false, false));
    }

    [Fact]
    public void Garde_cache_saisie_et_rafale()
    {
        var g = new GardeSons();
        Assert.False(g.Peut(Son.Caresse, 0, "normaux", cache: true, saisie: false));   // plein écran, visio
        Assert.False(g.Peut(Son.Mot, 0, "normaux", cache: false, saisie: true));       // spontané pendant la saisie
        Assert.True(g.Peut(Son.Caresse, 0, "discrets", false, saisie: true));          // un geste : il répond
        Assert.False(g.Peut(Son.Choix, 500, "normaux", false, false));                  // trop tôt
        Assert.True(g.Peut(Son.Choix, 1300, "normaux", false, false));
        Assert.False(g.Peut(Son.Caresse, 2600, "normaux", false, false));               // même son, < 4 s
        Assert.True(g.Peut(Son.Caresse, 4100, "normaux", false, false));
    }

    [Fact]
    public void Au_plus_six_sons_spontanes_par_heure()
    {
        var g = new GardeSons();
        int partis = 0;
        for (long t = 0; t < 3_600_000; t += 60_000)
            if (g.Peut(Son.Succes, t, "normaux", false, false)) partis++;
        Assert.Equal(GardeSons.SpontanesParHeure, partis);
        Assert.True(g.Peut(Son.Succes, 3_700_000, "normaux", false, false));
    }
}
