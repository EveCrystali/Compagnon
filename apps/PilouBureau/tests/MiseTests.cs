using PilouBureau;
using Xunit;

public class MiseTests
{
    [Theory]
    [InlineData("0.9.12", "0.9.4", true)]
    [InlineData("0.9.4", "0.9.12", false)]
    [InlineData("0.9.4", "0.9.4", false)]
    [InlineData("v1.0", "0.9.99", true)]
    [InlineData("0.9.1", "0.8.0", true)]
    [InlineData("0.8.0", "0.8.0-beta.1", true)]
    [InlineData("0.8.0-beta.2", "0.8.0-beta.1", true)]
    [InlineData("0.8.0-beta.1", "0.8.0", false)]
    [InlineData("0.9.3", "0.9-dev", true)]
    public void Comparaison_des_versions(string candidate, string actuelle, bool attendu) =>
        Assert.Equal(attendu, Mise.PlusRecente(candidate, actuelle));

    [Fact]
    public void Lecture_de_version_json()
    {
        var p = Mise.LireVersion("""{"version":"0.9.7","apkCode":1234,"zip":"PilouBureau.zip","apk":"Pilou.apk"}""")!;
        Assert.Equal("0.9.7", p.Version);
        Assert.Equal("PilouBureau.zip", p.Zip);
        Assert.Null(Mise.LireVersion("{}"));
        Assert.Null(Mise.LireVersion("pas du json"));
    }
}
