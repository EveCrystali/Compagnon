using System.Text.Json;
using PilouBureau;
using Xunit;

// Notifications Windows dans la bulle : filtre d'applis, masquage, heures calmes, file d'affichage, réglages.
public class NotificationsTests
{
    private static ReglagesNotifs R(ModeApps mode = ModeApps.Toutes, bool masquer = false, bool actif = true, params string[] apps) =>
        new(actif, mode, apps, masquer);

    private static readonly NotifRecue Msg = new("Messagerie", "Léo", "On se voit à midi ?");

    [Fact]
    public void DesactiveeParDefaut()
    {
        var r = new Reglages();
        Assert.False(r.NotifsWindows);
        Assert.False(r.FiltreDesNotifs().Actif);
        Assert.Null(FiltreNotifs.Preparer(Msg, r.FiltreDesNotifs(), calme: false, discret: false));
        // Les deux autres gestes sont proposés, et se décochent.
        Assert.True(r.GesteClavier);
        Assert.True(r.GestePhoto);
    }

    [Fact]
    public void ReglagesRelusSansContenuDeNotification()
    {
        var r = new Reglages { NotifsWindows = true, NotifsMode = ModeApps.Sauf, NotifsMasquer = true };
        r.NotifsApps.Add("Messagerie");
        var json = JsonSerializer.Serialize(r);
        var lu = JsonSerializer.Deserialize<Reglages>(json)!;
        Assert.True(lu.NotifsWindows);
        Assert.Equal(ModeApps.Sauf, lu.NotifsMode);
        Assert.True(lu.NotifsMasquer);
        Assert.Equal(new[] { "Messagerie" }, lu.NotifsApps);
        Assert.DoesNotContain("midi", json);
    }

    [Fact]
    public void FiltreToutesSaufSeulement()
    {
        Assert.True(FiltreNotifs.Admise("Messagerie", ModeApps.Toutes, Array.Empty<string>()));
        Assert.False(FiltreNotifs.Admise("Messagerie", ModeApps.Sauf, new[] { "messagerie" }));
        Assert.True(FiltreNotifs.Admise("Agenda", ModeApps.Sauf, new[] { "Messagerie" }));
        Assert.True(FiltreNotifs.Admise("Messagerie", ModeApps.Seulement, new[] { " Messagerie " }));
        Assert.False(FiltreNotifs.Admise("Agenda", ModeApps.Seulement, new[] { "Messagerie" }));
        Assert.False(FiltreNotifs.Admise("Agenda", ModeApps.Seulement, Array.Empty<string>()));
        Assert.Null(FiltreNotifs.Preparer(Msg, R(ModeApps.Sauf, false, true, "Messagerie"), false, false));
        Assert.NotNull(FiltreNotifs.Preparer(Msg, R(ModeApps.Seulement, false, true, "Messagerie"), false, false));
    }

    [Fact]
    public void MasquerLeContenu()
    {
        var a = FiltreNotifs.Preparer(Msg, R(masquer: true), false, false)!;
        Assert.True(a.Masquee);
        Assert.Equal("", a.Titre);
        Assert.Equal("", a.Texte);
        Assert.Equal("1 message de Messagerie", FiltreNotifs.Resume(a));
        Assert.Equal("M", a.Initiale);
        var b = FiltreNotifs.Preparer(Msg, R(), false, false)!;
        Assert.False(b.Masquee);
        Assert.Equal("Léo", b.Titre);
        Assert.Equal("On se voit à midi ?", b.Texte);
    }

    [Fact]
    public void HeuresCalmesEtDiscretionNeMontrentRien()
    {
        Assert.Null(FiltreNotifs.Preparer(Msg, R(), calme: true, discret: false));
        Assert.Null(FiltreNotifs.Preparer(Msg, R(), calme: false, discret: true));
        Assert.Null(FiltreNotifs.Preparer(Msg, R(actif: false), false, false));
    }

    [Fact]
    public void UneSeuleLigneCourte()
    {
        Assert.Equal("ligne un ligne deux", FiltreNotifs.Ligne("ligne un\r\nligne\tdeux"));
        Assert.Equal("a b", FiltreNotifs.Ligne("a" + (char)0x2028 + "b"));
        var longue = FiltreNotifs.Ligne(new string('x', 500));
        Assert.Equal(FiltreNotifs.LongueurMax, longue.Length);
        Assert.EndsWith("…", longue);
        Assert.Equal("", FiltreNotifs.Ligne(null));
        // Notification vide, ou sans nom d'appli.
        Assert.Null(FiltreNotifs.Preparer(new NotifRecue("X", " ", "\n"), R(), false, false));
        Assert.Equal("une appli", FiltreNotifs.Preparer(new NotifRecue("", "Titre", ""), R(), false, false)!.App);
    }

    [Fact]
    public void FileUneAUneQuelquesSecondes()
    {
        var f = new FileNotifs();
        Assert.Null(f.Courante(0));
        f.Ajouter(new NotifAffichee("A", "t1", "", false), 0);
        f.Ajouter(new NotifAffichee("B", "t2", "", false), 10);
        Assert.Equal("A", f.Courante(20)!.App);
        Assert.Equal(1, f.EnAttente);
        Assert.Equal("A", f.Courante(FileNotifs.Duree)!.App);
        Assert.Equal("B", f.Courante(20 + FileNotifs.Duree)!.App);
        Assert.Null(f.Courante(20 + 3 * FileNotifs.Duree));
    }

    [Fact]
    public void FileMasqueeRegroupeParAppli()
    {
        var f = new FileNotifs();
        var m = new NotifAffichee("Messagerie", "", "", true);
        f.Ajouter(m, 0);
        Assert.Equal(1, f.Courante(0)!.Nombre);
        f.Ajouter(m, 100);
        f.Ajouter(m, 200);
        var c = f.Courante(300)!;
        Assert.Equal(3, c.Nombre);
        Assert.Equal("3 messages de Messagerie", FiltreNotifs.Resume(c));
        Assert.Equal(0, f.EnAttente);
    }

    [Fact]
    public void FileBorneeEtVidable()
    {
        var f = new FileNotifs();
        for (int i = 0; i < 20; i++) f.Ajouter(new NotifAffichee("A" + i, "t", "", false), i);
        Assert.True(f.EnAttente <= FileNotifs.Max);
        f.Vider();
        Assert.Null(f.Courante(100));
        Assert.Equal(0, f.EnAttente);
    }
}
