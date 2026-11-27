using PilouBureau;
using Xunit;

// La police pixel (assets/police) se met en page au pixel près comme outils/sprites/police.py et comme le téléphone
// (PolicePixelTest.java) : mêmes lignes, mêmes largeurs, mêmes pixels (police-reference.txt).
public class PolicePixelTests
{
    private static string Racine()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d is not null && !File.Exists(Path.Combine(d.FullName, "assets", "index.txt"))) d = d.Parent;
        Assert.NotNull(d);
        return d!.FullName;
    }

    private sealed record Cas(string Police, int Max, int MaxLignes, string Texte, List<(int Largeur, string Texte)> Lignes, uint Empreinte);

    private static List<Cas> Reference()
    {
        var l = File.ReadAllLines(Path.Combine(Racine(), "outils", "sprites", "police-reference.txt"));
        var cas = new List<Cas>();
        for (int i = 0; i < l.Length; i++)
        {
            if (!l[i].StartsWith("= ")) continue;
            var t = l[i].Split(' ');
            string texte = l[++i].Replace("\\n", "\n").Replace("\\\\", "\\");
            var lignes = new List<(int, string)>();
            while (l[i + 1].StartsWith("| "))
            {
                var s = l[++i];
                int sp = s.IndexOf(' ', 2);
                lignes.Add((int.Parse(s[2..sp]), s[(sp + 1)..]));
            }
            uint emp = uint.Parse(l[++i][2..]);
            cas.Add(new Cas(t[1], int.Parse(t[2]), int.Parse(t[3]), texte, lignes, emp));
        }
        return cas;
    }

    [Fact]
    public void Memes_lignes_largeurs_et_pixels_que_la_reference()
    {
        var cas = Reference();
        Assert.True(cas.Count >= 100);
        var ecarts = new List<string>();
        foreach (var c in cas)
        {
            var p = PolicePixel.Ressource(c.Police)!;
            var lignes = p.Couper(c.Texte, c.Max, c.MaxLignes);
            var attendu = c.Lignes.Select(x => x.Texte).ToList();
            if (!lignes.SequenceEqual(attendu)) ecarts.Add($"{c.Police} {c.Max} « {c.Texte} » : [{string.Join(" / ", lignes)}]");
            else if (!lignes.Select(p.Largeur).SequenceEqual(c.Lignes.Select(x => x.Largeur))) ecarts.Add($"largeur « {c.Texte} »");
            else if (p.Empreinte(lignes) != c.Empreinte) ecarts.Add($"pixels « {c.Texte} »");
        }
        Assert.Empty(ecarts);
    }

    [Fact]
    public void Les_quatre_polices_sont_embarquees_et_le_dessin_fin_a_les_memes_chasses()
    {
        foreach (var (un, deux) in new[] { ("texte", "texte2x"), ("titre", "titre2x") })
        {
            var a = PolicePixel.Ressource(un)!;
            var b = PolicePixel.Ressource(deux)!;
            Assert.Equal(2, b.Echelle);
            Assert.Equal(a.Ligne, b.Ligne);
            var t = "Voix ambiguë d'un cœur qui, au zéphyr, préfère les jattes de kiwis ♥";
            Assert.Equal(a.Couper(t, 120), b.Couper(t, 120));
        }
    }

    [Fact]
    public void Tout_le_francais_a_un_dessin()
    {
        var p = PolicePixel.Texte!;
        foreach (char c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" +
                           "éèêëàâäîïôöùûüÿçœæÉÈÊËÀÂÄÎÏÔÖÙÛÜŸÇŒÆ«»’…–—!?:;.,()♥✓✧→¤  ")
            Assert.True(p.Connu(c), $"« {c} » sans dessin");
    }

    [Fact]
    public void Typographie_francaise_espaces_fines_et_apostrophe()
    {
        Assert.Equal("bonjour ! c’est « toi »", PolicePixel.Preparer("bonjour ! c'est « toi »"));
        // Jamais de « ! » seul en début de ligne.
        var p = PolicePixel.Texte!;
        foreach (var l in p.Couper("tu m'as appelé ? je fais demi-tour !", 30)) Assert.False(l.StartsWith('!') || l.StartsWith('?'));
    }
}
