using PilouBureau;
using Xunit;

// Le mot de bienvenue : une seule fois, au tout premier lancement ; jamais pour un Pilou déjà installé.
public class BienvenueTests
{
    [Fact]
    public void NouvelleInstallation()
    {
        Assert.False(new Reglages().BienvenueFaite);
    }

    [Fact]
    public void AncienFichierSansLeChamp()
    {
        Assert.True(Reglages.Depuis("""{ "Taille": 1.2 }""").BienvenueFaite);
    }

    [Fact]
    public void ChampGardeTelQuel()
    {
        Assert.False(Reglages.Depuis("""{ "BienvenueFaite": false }""").BienvenueFaite);
        Assert.True(Reglages.Depuis("""{ "BienvenueFaite": true }""").BienvenueFaite);
    }

    [Fact]
    public void MotCourt()
    {
        Assert.InRange(Reglages.MotBienvenue.Length, 20, 100);
    }
}
