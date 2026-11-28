using PilouBureau;
using Xunit;

// Vie du personnage : mêmes valeurs que outils/sprites/vie.py (vie-reference.txt) et que le téléphone (VieTest.java).
public class VieTests
{
    private static string Racine()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d is not null && !File.Exists(Path.Combine(d.FullName, "assets", "index.txt"))) d = d.Parent;
        Assert.NotNull(d);
        return d!.FullName;
    }

    private static string Hex(uint c) => "#" + (c & 0xffffff).ToString("x6");

    private static uint Couleur(string hex) => 0xff000000 | Convert.ToUInt32(hex[1..], 16);

    [Fact]
    public void Memes_valeurs_que_la_reference()
    {
        var lignes = File.ReadAllLines(Path.Combine(Racine(), "outils", "sprites", "vie-reference.txt"))
            .Where(l => !l.StartsWith('#') && l.Trim() != "").ToList();
        Assert.True(lignes.Count > 400);
        var ecarts = new List<string>();
        foreach (var l in lignes)
        {
            var c = l.Split(' ');
            string obtenu = c[0] switch
            {
                "duree" => $"{Vie.DureeBond(int.Parse(c[2]), c[1])}",
                "bond" => Trio(Vie.Bond(long.Parse(c[4]), int.Parse(c[2]), int.Parse(c[3]), c[1])),
                "sautille" => Trio(Vie.Sautille(long.Parse(c[4]), int.Parse(c[2]), int.Parse(c[3]), c[1])),
                "reception" => Vie.Recoit(long.Parse(c[2]), c[1]) is var (e, a) ? $"{e} {a}" : "",
                "lumiere" => Vie.Lumiere(int.Parse(c[1]), c[2] == "-" ? "" : c[2], c[3]) is { Length: > 0 } m ? m : "-",
                "eclaire" => Hex(Vie.Eclairer(Couleur(c[2]), c[1])),
                "bouffee" => string.Join(' ', Enumerable.Range(0, 70).Select(i => Vie.Bouffee(i * 10, int.Parse(c[1]), int.Parse(c[2])))),
                "atterrissage" => string.Join(' ', Enumerable.Range(0, 32).Select(i => Vie.BouffeeAtterrissage(i * 10 - 20))),
                _ => throw new ArgumentException(c[0]),
            };
            int n = c[0] switch
            {
                "duree" => 3, "bond" or "sautille" => 5, "reception" => 3, "lumiere" => 4, "eclaire" => 3, _ => c[0] == "bouffee" ? 3 : 1,
            };
            string attendu = string.Join(' ', c.Skip(n));
            if (obtenu != attendu) ecarts.Add($"{l} → {obtenu}");
        }
        Assert.Empty(ecarts);
    }

    private static string Trio((int, int, int) v) => $"{v.Item1} {v.Item2} {v.Item3}";

    [Fact]
    public void Le_saut_complet_retombe_et_s_arrete()
    {
        // L'arc monte jusqu'à la hauteur demandée, puis tout revient à zéro après la durée du bond.
        int max = Enumerable.Range(0, 1000).Max(d => Vie.Bond(d, 520, 2000, AnimationsCampagne.Completes).Saut);
        Assert.InRange(max, 1990, 2000);
        Assert.Equal((0, 0, 0), Vie.Bond(Vie.DureeBond(520, AnimationsCampagne.Completes), 520, 2000, AnimationsCampagne.Completes));
        // Réduites : l'arc seul, sans écrasement ni antenne.
        Assert.All(Enumerable.Range(0, 600), d => Assert.Equal(0, Vie.Bond(d, 520, 2000, AnimationsCampagne.Reduites).Etire));
    }

    [Fact]
    public void La_lumiere_garde_l_alpha_et_ne_touche_pas_le_plein_jour()
    {
        Assert.Equal(0x80123456u, Vie.Eclairer(0x80123456u, "jour"));
        Assert.Equal(0x80000000u, Vie.Eclairer(0x80000000u, "nuit") & 0xff000000);
        Assert.Equal("", Vie.Lumiere(12, "", AnimationsCampagne.Completes));
        Assert.Equal("", Vie.Lumiere(22, "", AnimationsCampagne.Aucune));
    }
}
