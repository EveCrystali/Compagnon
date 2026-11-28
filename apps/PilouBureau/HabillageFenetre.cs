using System.ComponentModel;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Shell;

namespace PilouBureau;

// L'habillage commun des fenêtres du jeu (docs/STYLE.md, « Fenêtres du PC ») : la barre de titre claire de Windows
// laisse la place à une barre en pixels (icône de Pilou, titre en police pixel, boutons « réduire » et « fermer »
// maison avec survol et appui), et la fenêtre prend un cadre d'un module à la couleur du bord.
//
// Mode d'emploi : à la fin du constructeur, une fois Content, Title, ResizeMode et les tailles posés,
//     HabillageFenetre.Poser(this);
// Rien d'autre ne change dans la fenêtre : son contenu est glissé sous la barre.
//
// C'est le « chrome » de WPF (WindowChrome) et non une fenêtre sans bord : Windows garde donc tout ce qu'il sait
// faire. Tirer la barre déplace ; les bords redimensionnent si la fenêtre le permettait ; l'ancrage aux bords de
// l'écran, le double clic qui agrandit, Alt+F4, Alt+Espace, la taille minimale et le changement d'écran ou d'échelle
// restent ceux du système. Échap n'est pas pris ici : la fenêtre qui le gérait le gère toujours.
// La fenêtre de Pilou n'est pas concernée (elle ne prend jamais le focus), ni les bulles sans bord.
internal static class HabillageFenetre
{
    public const double HauteurBarre = 30;

    private static readonly Brush Barre = FenetreAventure.Gel("#0b0e1a"), BarreInactive = FenetreAventure.Gel("#151a2e"),
        TitreActif = FenetreAventure.Gel("#e6ecf2"), TitreInactif = FenetreAventure.Gel("#7d8796");

    public static void Poser(Window f)
    {
        if (f.Content is not UIElement contenu || f.Tag as string == "habillee") return;
        bool reduire = f.ResizeMode != ResizeMode.NoResize;
        bool redimensionner = f.ResizeMode is ResizeMode.CanResize or ResizeMode.CanResizeWithGrip;
        WindowChrome.SetWindowChrome(f, new WindowChrome
        {
            CaptionHeight = HauteurBarre, CornerRadius = new CornerRadius(0), GlassFrameThickness = new Thickness(0),
            ResizeBorderThickness = redimensionner ? new Thickness(6) : new Thickness(0), UseAeroCaptionButtons = false,
        });

        // ---- La barre : icône, titre, boutons.
        var barre = new DockPanel { Height = HauteurBarre, Background = Barre, LastChildFill = true, SnapsToDevicePixels = true };
        var fermer = Bouton("ui-fermer", "Fermer (Alt+F4)", () => f.Close());
        DockPanel.SetDock(fermer, Dock.Right);
        barre.Children.Add(fermer);
        if (reduire)
        {
            var bas = Bouton(null, "Réduire", () => f.WindowState = WindowState.Minimized);
            DockPanel.SetDock(bas, Dock.Right);
            barre.Children.Add(bas);
        }
        if (IconePilou() is { } icone)
        {
            DockPanel.SetDock(icone, Dock.Left);
            barre.Children.Add(icone);
        }
        var titre = StylePixel.Texte(f.Title, TitreActif, StylePixel.Corps, true);
        titre.MaxLignes = 1;
        titre.VerticalAlignment = VerticalAlignment.Center;
        titre.Margin = new Thickness(8, 0, 8, 0);
        titre.IsHitTestVisible = false;
        barre.Children.Add(titre);
        DependencyPropertyDescriptor.FromProperty(Window.TitleProperty, typeof(Window))?.AddValueChanged(f, (_, _) => titre.Texte = f.Title);

        // ---- Le cadre : un module (2 unités) à la couleur du bord, un liseré sous la barre, puis le contenu d'origine.
        f.Content = null;
        var pile = new DockPanel { LastChildFill = true };
        DockPanel.SetDock(barre, Dock.Top);
        pile.Children.Add(barre);
        var lisere = new Border { Height = 2, Background = Bandeau.Bord, SnapsToDevicePixels = true };
        DockPanel.SetDock(lisere, Dock.Top);
        pile.Children.Add(lisere);
        pile.Children.Add(contenu);
        var cadre = new Border
        {
            BorderBrush = Bandeau.Bord, BorderThickness = new Thickness(2), Background = f.Background, Child = pile, SnapsToDevicePixels = true,
        };
        f.Content = cadre;
        f.Tag = "habillee";
        // La fenêtre gardait la hauteur de la barre du système en plus de son contenu : la nôtre compte dans le contenu.
        if (f.SizeToContent == SizeToContent.Manual && !double.IsNaN(f.Height))
        {
            f.Height += 4;
            if (f.MinHeight > 0) f.MinHeight += 4;
        }

        void Peindre()
        {
            barre.Background = f.IsActive ? Barre : BarreInactive;
            titre.Couleur = f.IsActive ? TitreActif : TitreInactif;
            cadre.BorderBrush = lisere.Background = f.IsActive ? Bandeau.Bord : FenetreAventure.Gel("#3a4270");
            // Agrandie, Windows fait déborder la fenêtre de l'épaisseur de son bord : on rentre le contenu d'autant.
            cadre.Padding = f.WindowState == WindowState.Maximized ? new Thickness(6) : new Thickness(0);
        }
        f.Activated += (_, _) => Peindre();
        f.Deactivated += (_, _) => Peindre();
        f.StateChanged += (_, _) => Peindre();
        Peindre();
    }

    // Un bouton de la barre : carré, icône de la banque (ou le trait « réduire »), survol en fond d'accent, appui enfoncé.
    private static FrameworkElement Bouton(string? icone, string bulle, Action action)
    {
        FrameworkElement dessin = icone is not null
            ? new IconePixel(icone, CadrePixel.Texte) { Pixel = 1 }
            : new Border { Width = 10, Height = 2, Background = CadrePixel.Texte, VerticalAlignment = VerticalAlignment.Bottom, Margin = new Thickness(1, 0, 1, 2) };
        var boite = new Grid { Width = 12, Height = 12 };
        boite.Children.Add(dessin);
        var cadre = new CadrePixel
        {
            U = 2, AvecOmbre = false, Retrait = 1, Child = boite, Fond = Barre, Couleur = FenetreAventure.Gel("#3a4270"),
            VerticalAlignment = VerticalAlignment.Center, Margin = new Thickness(0, 0, 4, 0), Cursor = Cursors.Hand, ToolTip = bulle,
        };
        WindowChrome.SetIsHitTestVisibleInChrome(cadre, true);
        void Teindre(bool survol)
        {
            cadre.Survol = survol;
            cadre.Couleur = survol ? CadrePixel.SurvolFond : FenetreAventure.Gel("#3a4270");
            var encre = survol ? CadrePixel.SurvolTexte : CadrePixel.Texte;
            if (dessin is IconePixel ip) ip.Couleur = encre;
            else if (dessin is Border b) b.Background = encre;
            cadre.InvalidateVisual();
        }
        cadre.MouseEnter += (_, _) => Teindre(true);
        cadre.MouseLeave += (_, _) =>
        {
            cadre.Enfonce = false;
            Teindre(false);
        };
        cadre.MouseLeftButtonDown += (_, e) =>
        {
            cadre.Enfonce = true;
            e.Handled = true;
        };
        cadre.MouseLeftButtonUp += (_, e) =>
        {
            bool appuye = cadre.Enfonce;
            cadre.Enfonce = false;
            e.Handled = true;
            if (appuye) action();
        };
        return cadre;
    }

    // L'icône de Pilou (celle de la zone de notification), 16 × 16, sans lissage.
    private static FrameworkElement? IconePilou()
    {
        try
        {
            var (px, w, h) = Icone.Silhouette(Banque.Commune);
            var image = Icone.Image(px, w, h, 16);
            var octets = new byte[16 * 16 * 4];
            Buffer.BlockCopy(image, 0, octets, 0, octets.Length);
            var source = BitmapSource.Create(16, 16, 96, 96, PixelFormats.Bgra32, null, octets, 16 * 4);
            source.Freeze();
            var vue = new Image { Source = source, Width = 16, Height = 16, Margin = new Thickness(8, 0, 0, 0), VerticalAlignment = VerticalAlignment.Center, IsHitTestVisible = false };
            RenderOptions.SetBitmapScalingMode(vue, BitmapScalingMode.NearestNeighbor);
            return vue;
        }
        catch (Exception e) when (e is ArgumentException or InvalidOperationException or IndexOutOfRangeException)
        {
            return null; // pas d'icône : le titre suffit
        }
    }
}
