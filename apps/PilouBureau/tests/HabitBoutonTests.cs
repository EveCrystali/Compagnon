using System.Xml.Linq;
using PilouBureau;
using Xunit;

// Le gabarit rétro des boutons est du XAML en texte, chargé à l'exécution : une erreur ne se voit qu'à l'écran
// (boutons Windows, texte illisible une fois désactivés). Sans WPF ici, on vérifie ce qui l'avait cassé : un
// Setter de trigger doit viser un élément nommé du gabarit, jamais un TranslateTransform ou un autre Freezable.
public class HabitBoutonTests
{
    private static readonly XNamespace X = "http://schemas.microsoft.com/winfx/2006/xaml";

    [Fact]
    public void Les_setters_du_gabarit_visent_des_elements()
    {
        var doc = XDocument.Parse(HabitBouton.Xaml);
        var noms = doc.Descendants().Where(e => e.Attribute(X + "Name") is not null)
            .ToDictionary(e => e.Attribute(X + "Name")!.Value, e => e.Name.LocalName);
        var cibles = doc.Descendants().Where(e => e.Name.LocalName == "Setter")
            .Select(e => e.Attribute("TargetName")?.Value).OfType<string>().ToList();
        Assert.NotEmpty(cibles);
        foreach (var c in cibles)
        {
            Assert.True(noms.TryGetValue(c, out var type), $"cible inconnue : {c}");
            Assert.DoesNotContain("Transform", type);
            Assert.DoesNotContain("Brush", type);
        }
        Assert.Equal("Button", doc.Root!.Attribute("TargetType")?.Value);
    }
}
