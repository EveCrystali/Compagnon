using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;

namespace PilouBureau;

// Petite fenêtre pour saisir une valeur (adresse de webhook, identifiant Discord).
public static class Saisie
{
    public static string? Demander(string titre, string explication, string valeur)
    {
        // Au guide de style (docs/STYLE.md) : fond de nuit, texte en police pixel, champ carré, boutons au cadre pixel.
        var champ = ChampPixel.Habiller(new TextBox { Text = valeur, MinWidth = 460, Margin = new Thickness(0, 8, 0, 12) });
        var ok = new BoutonPixel("OK", true, StylePixel.Corps) { IsDefault = true, Margin = new Thickness(0, 0, 10, 0) };
        var annuler = new BoutonPixel("Annuler", false, StylePixel.Corps) { IsCancel = true };
        var boutons = new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right };
        boutons.Children.Add(ok);
        boutons.Children.Add(annuler);
        var pile = new StackPanel { Margin = new Thickness(20, 14, 20, 18) };
        pile.Children.Add(new Border { MaxWidth = 460, HorizontalAlignment = HorizontalAlignment.Left, Child = StylePixel.Texte(explication, CadrePixel.Texte, StylePixel.Corps) });
        pile.Children.Add(champ);
        pile.Children.Add(boutons);
        var f = new Window
        {
            Title = titre,
            Content = pile,
            SizeToContent = SizeToContent.WidthAndHeight,
            ResizeMode = ResizeMode.NoResize,
            WindowStartupLocation = WindowStartupLocation.CenterScreen,
            Topmost = true,
            ShowInTaskbar = true,
            Background = FenetreAventure.Gel("#0f1324"),
            UseLayoutRounding = true,
        };
        HabillageFenetre.Poser(f);
        ok.Click += (_, _) => f.DialogResult = true;
        f.Loaded += (_, _) =>
        {
            champ.Focus();
            champ.SelectAll();
            Keyboard.Focus(champ);
        };
        return f.ShowDialog() == true ? champ.Text.Trim() : null;
    }
}
