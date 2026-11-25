using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using QRCoder;

namespace PilouBureau;

// Fenêtre d'appairage : un QR code à scanner avec l'app Android (ou le code à taper).
public static class Appairage
{
    public static void Montrer(string code, string relais)
    {
        var lien = Telephone.Lien(code, relais);
        var png = new PngByteQRCode(new QRCodeGenerator().CreateQrCode(lien, QRCodeGenerator.ECCLevel.M)).GetGraphic(8);
        var image = new BitmapImage();
        image.BeginInit();
        image.StreamSource = new MemoryStream(png);
        image.CacheOption = BitmapCacheOption.OnLoad;
        image.EndInit();

        var pile = new StackPanel { Margin = new Thickness(18), Width = 340 };
        pile.Children.Add(new TextBlock
        {
            Text = "Vise ce QR code avec l'appareil photo du téléphone : l'app Pilou s'ouvre et s'appaire. Ou tape le code dans l'app.",
            TextWrapping = TextWrapping.Wrap,
            FontSize = 12,
        });
        pile.Children.Add(new Image { Source = image, Width = 260, Height = 260, Margin = new Thickness(0, 12, 0, 8) });
        pile.Children.Add(new TextBox
        {
            Text = Telephone.Formater(code),
            IsReadOnly = true,
            FontFamily = new FontFamily("Consolas"),
            FontSize = 20,
            HorizontalContentAlignment = HorizontalAlignment.Center,
            BorderThickness = new Thickness(0),
        });
        pile.Children.Add(new TextBlock
        {
            Text = $"Relais : {relais}. Le contenu est chiffré : le relais ne voit qu'un texte illisible. " +
                   "Garde ce code pour toi : il donne accès à l'état de tes sessions.",
            TextWrapping = TextWrapping.Wrap,
            FontSize = 11,
            Foreground = Brushes.Gray,
            Margin = new Thickness(0, 10, 0, 0),
        });
        var ok = new Button { Content = "Fermer", IsDefault = true, IsCancel = true, MinWidth = 80, Margin = new Thickness(0, 12, 0, 0), HorizontalAlignment = HorizontalAlignment.Right };
        pile.Children.Add(ok);
        var f = new Window
        {
            Title = "Appairer mon téléphone",
            Content = pile,
            SizeToContent = SizeToContent.WidthAndHeight,
            ResizeMode = ResizeMode.NoResize,
            WindowStartupLocation = WindowStartupLocation.CenterScreen,
            Topmost = true,
        };
        ok.Click += (_, _) => f.Close();
        f.ShowDialog();
    }
}
