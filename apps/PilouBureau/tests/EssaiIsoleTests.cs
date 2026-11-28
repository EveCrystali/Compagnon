using System.Security.Cryptography;
using PilouBureau;
using Xunit;

// Un essai (--essai=, --instantane=, --film=, --captures=) ne touche jamais aux vraies données de Pilou (EssaiIsole.cs) :
// un dossier témoin joue le vrai dossier, et rien n'y change pendant qu'un essai écrit son profil, ses réglages, ses
// secrets et le compteur de XP.
public sealed class EssaiIsoleTests : IDisposable
{
    private readonly string _racine = Path.Combine(Path.GetTempPath(), "pilou-tests-essai-" + Guid.NewGuid().ToString("N"));
    private readonly string _temoin, _temp;

    public EssaiIsoleTests()
    {
        _temoin = Path.Combine(_racine, "compagnon");
        _temp = Path.Combine(_racine, "temp");
        Directory.CreateDirectory(Path.Combine(_temoin, "amis"));
        Directory.CreateDirectory(_temp);
        // Le vrai dossier, en miniature : un profil, des réglages, un ami, l'état d'une session.
        new Profil { Xp = 457 }.Ecrire(_temoin);
        new Reglages().Ecrire(_temoin);
        File.WriteAllText(Path.Combine(_temoin, "amis", "amis.json"), "{\"amis\":[]}");
        File.WriteAllText(Path.Combine(_temoin, "etat-abc.json"), "{\"session\":\"abc\"}");
    }

    public void Dispose()
    {
        try
        {
            Directory.Delete(_racine, true);
        }
        catch (IOException)
        {
        }
    }

    // Chaque fichier du dossier : chemin relatif → taille, date d'écriture et empreinte du contenu.
    private static SortedDictionary<string, string> Releve(string dossier) =>
        new(Directory.EnumerateFiles(dossier, "*", SearchOption.AllDirectories).ToDictionary(
            f => Path.GetRelativePath(dossier, f),
            f => $"{new FileInfo(f).Length} {File.GetLastWriteTimeUtc(f).Ticks} {Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(f)))}"));

    [Fact]
    public void Sans_dossier_donne_un_essai_prend_un_dossier_jetable_et_vide()
    {
        var (d, jetable) = EssaiIsole.Dossier(null, _temoin, _temp);
        Assert.True(jetable);
        Assert.False(EssaiIsole.Meme(d, _temoin));
        Assert.StartsWith(_temp, d);
        Assert.StartsWith(EssaiIsole.Prefixe, Path.GetFileName(d));
        Assert.Empty(Directory.EnumerateFileSystemEntries(d));
    }

    [Fact]
    public void Le_vrai_dossier_donne_autrement_ecrit_est_quand_meme_remplace()
    {
        foreach (var donne in new[] { _temoin, _temoin + Path.DirectorySeparatorChar, _temoin.ToUpperInvariant(), _temoin + "/" })
        {
            var (d, jetable) = EssaiIsole.Dossier(donne, _temoin, _temp);
            Assert.True(jetable, donne);
            Assert.False(EssaiIsole.Meme(d, _temoin), donne);
        }
    }

    [Fact]
    public void Un_autre_dossier_donne_est_garde_tel_quel()
    {
        var demo = Path.Combine(_racine, "demo");
        var (d, jetable) = EssaiIsole.Dossier(demo, _temoin, _temp);
        Assert.Equal(demo, d);
        Assert.False(jetable);
    }

    [Fact]
    public void Les_dossiers_d_essais_arretes_de_force_sont_effaces_et_eux_seuls()
    {
        var mort = Directory.CreateDirectory(Path.Combine(_temp, EssaiIsole.Prefixe + "999999-1")).FullName;
        File.WriteAllText(Path.Combine(mort, "reglages.json"), "{}");
        var vif = Directory.CreateDirectory(Path.Combine(_temp, EssaiIsole.Prefixe + "4242-1")).FullName;
        var autre = Directory.CreateDirectory(Path.Combine(_temp, "pilou-autre")).FullName;
        Assert.Equal(1, EssaiIsole.Nettoyer(_temp, pid => pid == 4242));
        Assert.False(Directory.Exists(mort));
        Assert.True(Directory.Exists(vif));
        Assert.True(Directory.Exists(autre));
    }

    [Fact]
    public void Rien_ne_change_dans_le_vrai_dossier_pendant_un_essai()
    {
        var avant = Releve(_temoin);
        var (d, _) = EssaiIsole.Dossier(null, _temoin, _temp);
        // Ce qu'un Pilou d'essai écrit en tournant : profil (XP des sessions), réglages, secrets, compteur, partage.
        var reglages = Reglages.Lire(d);
        Assert.Equal(d, reglages.Partage(d));                    // pas de dossier de partage hérité du vrai dossier
        reglages.Ecrire(d);
        var profil = Profil.Lire(d);
        Assert.NotEqual(457, profil.Xp);                         // le vrai profil n'est pas lu
        profil.Xp += 12;
        profil.Ecrire(reglages.Partage(d));
        new CoffreMemoire().Ecrire("telephone", "secret");
        File.WriteAllText(Path.Combine(d, "caresses.txt"), "1");
        Assert.Equal(avant, Releve(_temoin));
        // À la sortie, le dossier jetable disparaît ; le vrai dossier, lui, ne peut jamais être effacé par là.
        EssaiIsole.Effacer(d);
        Assert.False(Directory.Exists(d));
        EssaiIsole.Effacer(_temoin);
        Assert.Equal(avant, Releve(_temoin));
    }
}
