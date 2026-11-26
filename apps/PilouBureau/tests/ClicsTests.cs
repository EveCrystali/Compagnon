using PilouBureau;
using Xunit;

// Clics des petits jeux et du menu : zones généreuses, fenêtres de temps, clic court contre glisser,
// fermeture du menu quand on clique ailleurs.
public class ClicsTests
{
    [Fact]
    public void LaZoneElargieAttrapeUnClicACoteDeLaCible()
    {
        // La main de tape m'en cinq : 22 × 22 unités en (100, 50).
        var main = new Clics.Zone(100, 50, 22, 22);
        Assert.True(main.Contient(111, 61));
        Assert.False(main.Contient(95, 61));                       // à côté : raté sans marge
        var zone = main.Elargie(Clics.MargeCible);
        Assert.True(zone.Contient(95, 61));                        // à côté : compte avec la marge
        Assert.True(zone.Contient(100 - Clics.MargeCible, 50 - Clics.MargeCible));
        Assert.True(zone.Contient(122 + Clics.MargeCible, 72 + Clics.MargeCible));
        Assert.False(zone.Contient(122 + Clics.MargeCible + 1, 61));
        Assert.Equal(22 + 2 * Clics.MargeCible, zone.Largeur);
    }

    [Fact]
    public void LaMargeEstGenereuseMaisPasEnvahissante()
    {
        Assert.InRange(Clics.MargeCible, 12, 30);
    }

    [Fact]
    public void DansUneRegardeToutesLesZones()
    {
        var zones = new[] { new Clics.Zone(0, 0, 100, 300), new Clics.Zone(96, 40, 180, 200) };
        Assert.True(Clics.DansUne(zones, 50, 50));
        Assert.True(Clics.DansUne(zones, 200, 100));               // dans le sous-menu
        Assert.False(Clics.DansUne(zones, 500, 100));
        Assert.False(Clics.DansUne(Array.Empty<Clics.Zone>(), 0, 0));
    }

    [Fact]
    public void PecheOnFerreDansLaFenetreJugeeAlAppui()
    {
        const double mord = 10_000;
        Assert.Equal(Clics.Ferrage.Attendre, Clics.Juger(5_000, mord));
        Assert.Equal(Clics.Ferrage.Attendre, Clics.Juger(mord - Clics.Anticipation - 1, mord));
        Assert.Equal(Clics.Ferrage.Ferre, Clics.Juger(mord - Clics.Anticipation, mord));   // réflexe un poil en avance
        Assert.Equal(Clics.Ferrage.Ferre, Clics.Juger(mord, mord));
        Assert.Equal(Clics.Ferrage.Ferre, Clics.Juger(mord + 1_500, mord));                 // l'ancienne fenêtre (1,2 s) aurait raté
        Assert.Equal(Clics.Ferrage.TropTard, Clics.Juger(mord + Clics.FenetreMorsure, mord));
    }

    [Fact]
    public void PecheLaFenetreEstPlusLargeQuAvant()
    {
        Assert.True(Clics.FenetreMorsure >= 1_500);
        Assert.True(Clics.Mord(10_500, 10_000));
        Assert.False(Clics.Mord(9_999, 10_000));
        Assert.False(Clics.Mord(10_000 + Clics.FenetreMorsure, 10_000));
        Assert.True(Clics.FuiteApres >= 2);                         // un clic trop tôt ne fait plus tout rater
    }

    [Fact]
    public void LesJeuxDurentAssezPourCliquer()
    {
        Assert.True(Clics.DureeEtoile > 9_000);
        Assert.True(Clics.DureeTapeCinq > 4_500);
        Assert.True(Clics.VitesseBulles < 22);
    }

    [Theory]
    [InlineData("tape", true)]
    [InlineData("peche", true)]
    [InlineData("cuisine", true)]
    [InlineData("etoile", false)]
    [InlineData("bulles", false)]
    [InlineData("", false)]
    public void UnClicSurPilouCompteSelonLeJeu(string jeu, bool compte)
    {
        Assert.Equal(compte, Clics.ClicSurPilouCompte(jeu));
    }

    [Theory]
    [InlineData(0, 50, false)]      // clic net
    [InlineData(6, 80, false)]      // la main a tremblé : encore un clic (avant : glisser dès 5)
    [InlineData(9.9, 100, false)]
    [InlineData(11, 60, true)]      // vrai geste
    [InlineData(5, 400, true)]      // lent et un peu déplacé : on le prend
    [InlineData(3, 2000, false)]    // appui long immobile : pas un glisser
    public void ClicCourtOuGlisser(double distance, double ms, bool glisser)
    {
        Assert.Equal(glisser, Clics.EstGlisser(distance, ms));
    }

    [Fact]
    public void MenuSeFermeAuClicDehors()
    {
        // Front montant hors du menu : on ferme.
        Assert.True(Clics.FermerMenu(basAvant: false, basMaintenant: true, sourisDansMenu: false, aEuLeFocus: false, focusChezNous: false));
        // Dans le menu ou un sous-menu : on laisse WPF faire.
        Assert.False(Clics.FermerMenu(false, true, sourisDansMenu: true, aEuLeFocus: true, focusChezNous: true));
        // Bouton déjà enfoncé à l'ouverture (le clic droit lui-même) : pas de fermeture tant qu'il n'est pas relâché.
        Assert.False(Clics.FermerMenu(basAvant: true, basMaintenant: true, sourisDansMenu: false, aEuLeFocus: false, focusChezNous: false));
        // Rien d'enfoncé, focus jamais reçu (SetForegroundWindow refusé) : on reste ouvert.
        Assert.False(Clics.FermerMenu(false, false, false, aEuLeFocus: false, focusChezNous: false));
    }

    [Fact]
    public void MenuSeFermeQuandLeFocusPart()
    {
        Assert.True(Clics.FermerMenu(false, false, true, aEuLeFocus: true, focusChezNous: false));
        Assert.False(Clics.FermerMenu(false, false, true, aEuLeFocus: true, focusChezNous: true));
    }
}
