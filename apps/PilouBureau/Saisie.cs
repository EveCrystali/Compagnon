using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;

namespace PilouBureau;

// Petite fenêtre pour saisir une valeur (adresse de webhook, identifiant Discord).
public static class Saisie
{
    public static string? Demander(string titre, string explication, string valeur)
    {
        var champ = new TextBox { Text = valeur, MinWidth = 420, Margin = new Thickness(0, 8, 0, 10), Padding = new Thickness(4, 3, 4, 3) };
        var ok = new Button { Content = "OK", IsDefault = true, MinWidth = 80, Margin = new Thickness(0, 0, 8, 0) };
        var annuler = new Button { Content = "Annuler", IsCancel = true, MinWidth = 80 };
        var boutons = new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right };
        boutons.Children.Add(ok);
        boutons.Children.Add(annuler);
        var pile = new StackPanel { Margin = new Thickness(14) };
        pile.Children.Add(new TextBlock { Text = explication, TextWrapping = TextWrapping.Wrap, MaxWidth = 420, FontSize = 12 });
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
        };
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
