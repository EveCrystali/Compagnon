using PilouBureau;
using Xunit;

// Le menu de l'icône près de l'horloge : la porte de secours quand le menu de l'overlay ne s'ouvre plus.
public class MenuNotificationTests
{
    [Fact]
    public void ToutesLesPortesDeSecours()
    {
        var choix = MenuNotification.Entrees.Where(e => e.Choix is not null).Select(e => e.Choix!.Value).ToList();
        Assert.Equal(Enum.GetValues<ChoixNotification>(), choix.Order());
        Assert.Equal(choix.Count, choix.Distinct().Count());
        Assert.Equal(ChoixNotification.Afficher, MenuNotification.Entrees[0].Choix);
        Assert.Equal(ChoixNotification.Quitter, MenuNotification.Entrees[^1].Choix);
    }

    [Fact]
    public void Textes()
    {
        Assert.Equal("Pilou", MenuNotification.Infobulle);
        Assert.Contains(MenuNotification.Entrees, e => e.Texte == "Afficher / ramener Pilou");
        Assert.Contains(MenuNotification.Entrees, e => e.Texte == "Ouvrir le menu de Pilou");
        Assert.Contains(MenuNotification.Entrees, e => e.Texte == "Chercher une mise à jour");
        Assert.Contains(MenuNotification.Entrees, e => e.Texte == "Redémarrer Pilou");
        // « & » soulignerait une lettre dans un menu Win32 ; pas de séparateurs collés.
        Assert.All(MenuNotification.Entrees.Where(e => e.Choix is not null), e => Assert.DoesNotContain('&', e.Texte));
        var liste = MenuNotification.Entrees.ToList();
        for (int i = 1; i < liste.Count; i++) Assert.False(liste[i].Choix is null && liste[i - 1].Choix is null);
    }

    [Fact]
    public void NumerosRendusParLeMenu()
    {
        Assert.Null(MenuNotification.Lire(0)); // fermé sans choix
        Assert.Null(MenuNotification.Lire(99));
        Assert.Equal(ChoixNotification.Redemarrer, MenuNotification.Lire((int)ChoixNotification.Redemarrer));
    }
}
