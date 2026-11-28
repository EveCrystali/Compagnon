using System.Windows;

namespace PilouBureau;

// La phrase de Pilou en tête de bulle (ce qu'il dit, ses petits mots : docs/PRESENCE.md) écrite dans sa police
// pixel (TextePixel.cs, docs/POLICE.md) : coupée à la largeur de la bulle, quatre lignes au plus.
public sealed partial class FenetrePilou
{
    private FrameworkElement Phrase(string texte, string? tag) => new TextePixel(texte, Couleurs.Texte)
    {
        Tag = tag,
        MaxLignes = 4,
        Margin = new Thickness(0, 2, 0, 3),
    };
}
