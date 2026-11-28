using PilouBureau;
using Xunit;

// Thème sombre par défaut sur PC ; un réglage déjà enregistré garde son choix (Antoine, 28 novembre 2026).
public class ThemeTests
{
    [Fact]
    public void SombreParDefaut()
    {
        Assert.Equal(ThemeBulle.Sombre, new Reglages().Theme);
        Assert.True(new Reglages().Sombre());
        Assert.Equal(ThemeBulle.Sombre, Reglages.Depuis("""{ "Taille": 1.0 }""").Theme); // champ absent
    }

    [Fact]
    public void ChoixEnregistreGarde()
    {
        Assert.Equal(ThemeBulle.Auto, Reglages.Depuis("""{ "Theme": 0 }""").Theme);
        Assert.Equal(ThemeBulle.Clair, Reglages.Depuis("""{ "Theme": 1 }""").Theme);
        Assert.False(Reglages.Depuis("""{ "Theme": 1 }""").Sombre());
    }
}
