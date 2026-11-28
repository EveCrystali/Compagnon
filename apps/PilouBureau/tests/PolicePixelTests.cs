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

    [Theory]
    [InlineData(1.0, 1)]
    [InlineData(1.25, 2)]
    [InlineData(1.5, 2)]
    [InlineData(1.75, 2)]
    [InlineData(2.0, 3)]
    [InlineData(0.5, 1)]
    public void Un_pixel_de_police_tombe_sur_des_pixels_entiers(double echelleWindows, int attendu) =>
        Assert.Equal(attendu, PolicePixel.PixelsPhysiques(1.3, echelleWindows));

    [Fact]
    public void Tout_le_francais_a_un_dessin()
    {
        var p = PolicePixel.Texte!;
        foreach (char c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" +
                           "éèêëàâäîïôöùûüÿçœæÉÈÊËÀÂÄÎÏÔÖÙÛÜŸÇŒÆ«»’…–—!?:;.,()♥✓✧→¤  ")
            Assert.True(p.Connu(c), $"« {c} » sans dessin");
    }

    // « déjà », « toujours » : le j laisse le même blanc qu'un i après la lettre d'avant (son crochet passe dessous).
    [Fact]
    public void Le_j_ne_laisse_pas_plus_de_blanc_qu_un_i()
    {
        foreach (var police in new[] { PolicePixel.Texte!, PolicePixel.Titre! })
            foreach (char c in "aeéouàdnstxzr")
                Assert.True(Blanc(police, c, 'i') == Blanc(police, c, 'j'), $"« {c}j » ({police.Ligne})");
    }

    // Colonnes vides entre la lettre a et l'œil de la lettre b (rangées 5 à 10, sans point ni crochet).
    private static int Blanc(PolicePixel p, char a, char b)
    {
        var seul = p.Pixels(new[] { a.ToString() }).ToHashSet();
        int droite = seul.Max(q => q.X);
        int gauche = p.Pixels(new[] { $"{a}{b}" }).Where(q => !seul.Contains(q) && q.Y >= 5 && q.Y <= 10).Min(q => q.X);
        return gauche - droite - 1;
    }

    // Aucune lettre ni chiffre (4 de large et plus) n'est un pavé : au plus 82 % de pixels pleins dans sa boîte, aux
    // quatre polices. Le « m » gras en avait 97 % (« douce-a▮ère ») quand le gras bouchait ses jours d'un pixel.
    [Fact]
    public void Aucune_lettre_n_est_un_pave()
    {
        foreach (var nom in new[] { "texte", "titre", "texte2x", "titre2x" })
        {
            var p = PolicePixel.Ressource(nom)!;
            for (int c = 0x21; c < 0x2000; c++)
            {
                if (!char.IsLetterOrDigit((char)c) || p.GlypheDe(c) is not { Largeur: >= 4, Rangs.Length: > 0 } g) continue;
                int pleins = g.Rangs.Sum(r => r.Count(x => x == '#'));
                double part = (double)pleins / (g.Rangs.Length * g.Rangs[0].Length);
                Assert.True(part <= 0.82, $"{nom} « {(char)c} » : {part:P0} de pixels pleins");
            }
        }
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
