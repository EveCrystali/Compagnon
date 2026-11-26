using PilouBureau;
using Xunit;

// L'icône de Pilou (pilou.ico) : tirée de son rendu, aux tailles de Windows, et à jour.
public class IconeTests
{
    private static string Racine()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d is not null && !File.Exists(Path.Combine(d.FullName, "assets", "index.txt"))) d = d.Parent;
        Assert.NotNull(d);
        return d!.FullName;
    }

    private static readonly Lazy<Banque> B = new(() => Banque.DepuisDossier(Path.Combine(Racine(), "assets")));

    [Fact]
    public void LeFichierDuDepotEstLeRenduDePilou()
    {
        var chemin = Path.Combine(Racine(), "apps", "PilouBureau", "pilou.ico");
        var neuf = Icone.Generer(B.Value);
        // PILOU_ICONE=ecrire dotnet test --filter Icone : régénère pilou.ico après un changement du dessin.
        if (Environment.GetEnvironmentVariable("PILOU_ICONE") == "ecrire") File.WriteAllBytes(chemin, neuf);
        Assert.True(File.Exists(chemin), "pilou.ico manque : PILOU_ICONE=ecrire dotnet test --filter Icone");
        Assert.Equal(neuf, File.ReadAllBytes(chemin));
    }

    [Fact]
    public void ToutesLesTaillesDeWindows()
    {
        var ico = Icone.Generer(B.Value);
        Assert.Equal(new[] { 16, 20, 24, 32, 48 }, Icone.Entrees(ico).Select(e => e.Taille));
        foreach (var (t, debut, longueur) in Icone.Entrees(ico))
        {
            Assert.Equal(40, BitConverter.ToInt32(ico, debut));          // BITMAPINFOHEADER
            Assert.Equal(t, BitConverter.ToInt32(ico, debut + 4));
            Assert.Equal(2 * t, BitConverter.ToInt32(ico, debut + 8));   // image + masque
            Assert.Equal(40 + t * t * 4 + (t + 31) / 32 * 4 * t, longueur);
        }
    }

    [Fact]
    public void PilouRemplitLImageSansDeborder()
    {
        var (px, w, h) = Icone.Silhouette(B.Value);
        Assert.True(w > 16 && h > 16, $"silhouette {w}x{h}");
        foreach (var t in Icone.Tailles)
        {
            var im = Icone.Image(px, w, h, t);
            int pleins = im.Count(c => c >> 24 != 0);
            Assert.True(pleins > t * t / 4, $"{t} px : Pilou trop petit ({pleins} pixels)");
            // centré : autant de rangées vides en haut qu'en bas (à une près)
            var pleines = Enumerable.Range(0, t).Where(y => im.Skip(y * t).Take(t).Any(c => c >> 24 != 0)).ToList();
            Assert.InRange(pleines[0] - (t - 1 - pleines[^1]), -1, 1);
        }
    }

    [Fact]
    public void AgranditAuPixelPres()
    {
        var px = new uint[] { 0xff000001, 0xff000002, 0xff000003, 0xff000004 };
        var im = Icone.Image(px, 2, 2, 4);
        Assert.Equal(new uint[]
        {
            0xff000001, 0xff000001, 0xff000002, 0xff000002,
            0xff000001, 0xff000001, 0xff000002, 0xff000002,
            0xff000003, 0xff000003, 0xff000004, 0xff000004,
            0xff000003, 0xff000003, 0xff000004, 0xff000004,
        }, im);
    }

    [Theory]
    [InlineData(16, 0)]
    [InlineData(20, 1)]
    [InlineData(18, 1)]   // pas d'image 18 : on prend 20 (Windows réduit un peu)
    [InlineData(40, 4)]
    [InlineData(64, 4)]   // plus grand que tout : la plus grande
    public void ChoisitLaBonneTaille(int voulue, int attendu)
    {
        Assert.Equal(attendu, Icone.Choisir(new[] { 16, 20, 24, 32, 48 }, voulue));
    }

    [Fact]
    public void IcoIllisible()
    {
        Assert.Empty(Icone.Entrees(new byte[] { 0, 0, 2, 0 }));
        Assert.Equal(-1, Icone.Choisir(Array.Empty<int>(), 16));
    }
}
