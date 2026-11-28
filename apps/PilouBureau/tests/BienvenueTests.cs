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

// La première minute : trois bulles au plus, espacées, rien à cliquer, jamais pendant la saisie.
public class PremiereMinuteTests
{
    [Fact]
    public void TroisBullesCourtesDeLaVoixDePilou()
    {
        Assert.InRange(PremiereMinute.Mots.Count, 1, 3);
        Assert.Equal(Reglages.MotBienvenue, PremiereMinute.Mots[0].Texte);
        foreach (var m in PremiereMinute.Mots)
        {
            Assert.InRange(m.Texte.Length, 20, 100);
            Assert.Equal(m.Texte.ToLowerInvariant(), m.Texte.Replace("Aventure", "aventure")); // minuscules (LORE.md)
            Assert.InRange(m.DureeMs, 6_000, 12_000);
        }
        // Espacées : jamais deux à moins de 30 s.
        Assert.All(PremiereMinute.Mots.Skip(1), m => Assert.True(m.ApresMs >= 30_000));
        // Les deux gestes et l'Aventure sont dits.
        var tout = string.Join(" ", PremiereMinute.Mots.Select(m => m.Texte));
        Assert.Contains("clic gauche", tout);
        Assert.Contains("clic droit", tout);
        Assert.Contains("aventure", tout);
    }

    [Fact]
    public void AttendLeMomentPuisSeTait()
    {
        var premier = PremiereMinute.Mots[0];
        Assert.Equal(PremiereMinute.Decision.Attendre, PremiereMinute.Decider(0, premier.ApresMs - 1, libre: true));
        Assert.Equal(PremiereMinute.Decision.Dire, PremiereMinute.Decider(0, premier.ApresMs, libre: true));
        // Pendant la saisie : il attend.
        Assert.Equal(PremiereMinute.Decision.Attendre, PremiereMinute.Decider(0, premier.ApresMs + 5_000, libre: false));
        // Trop longtemps sans moment calme : il abandonne.
        Assert.Equal(PremiereMinute.Decision.Abandonner, PremiereMinute.Decider(0, premier.ApresMs + PremiereMinute.PatienceMs + 1, libre: false));
        // Après la dernière : fini.
        Assert.Equal(PremiereMinute.Decision.Abandonner, PremiereMinute.Decider(PremiereMinute.Mots.Count, 1e9, libre: true));
    }
}
