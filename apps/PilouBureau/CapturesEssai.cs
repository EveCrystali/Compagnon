using System.IO;
using System.Windows;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Threading;

namespace PilouBureau;

// --essai=<scène> --captures=<dossier> : quelques secondes après la scène, chaque fenêtre ouverte de l'exe d'essai
// (Aventure, expéditions, journal…) est rendue par WPF lui-même en PNG, à 100, 125 et 150 % (le même agencement en
// pixels indépendants, rendu plus fin), puis une seconde fois à sa taille minimale ; enfin l'essai quitte.
// Rien ne passe par l'écran : ni les autres fenêtres ni le bureau n'apparaissent, et l'écran peut être en veille.
// Un fichier « fenetres.txt » liste pour chaque fenêtre sa taille et si un défileur horizontal est visible.
// Limite : la fenêtre de Pilou elle-même se dessine à sa propre échelle ; ce rendu-ci n'en garde pas la taille à l'écran
// (Pilou peut y paraître plus grand). Pour elle, --instantane ou --film font foi ; ici, seule la bulle se lit.
// Ce rendu à 125 et 150 % n'est pas un vrai changement d'échelle Windows (pas de message DPI, pas d'arrondi des pixels).
public static class CapturesEssai
{
    public static readonly double[] Echelles = { 1.0, 1.25, 1.5 };

    public static void Programmer(Application app, string dossier, double apres)
    {
        Directory.CreateDirectory(dossier);
        var minuteur = new DispatcherTimer { Interval = TimeSpan.FromSeconds(apres) };
        minuteur.Tick += (_, _) =>
        {
            minuteur.Stop();
            var bilan = new List<string>();
            var fenetres = app.Windows.OfType<Window>().Where(f => f.IsVisible && f.Content is Visual).ToList();
            for (int i = 0; i < fenetres.Count; i++) Rendre(fenetres[i], Path.Combine(dossier, $"{i}-{Nom(fenetres[i])}"), "", bilan);
            // Puis à la taille minimale, pour les fenêtres qui en ont une.
            var reduites = fenetres.Where(f => f.MinWidth > 0 && f.MinHeight > 0 && f.ResizeMode != ResizeMode.NoResize).ToList();
            foreach (var f in reduites)
            {
                f.Width = f.MinWidth;
                f.Height = f.MinHeight;
            }
            var ensuite = new DispatcherTimer { Interval = TimeSpan.FromSeconds(1.5) };
            ensuite.Tick += (_, _) =>
            {
                ensuite.Stop();
                foreach (var f in reduites) Rendre(f, Path.Combine(dossier, $"{fenetres.IndexOf(f)}-{Nom(f)}"), "-min", bilan);
                File.WriteAllLines(Path.Combine(dossier, "fenetres.txt"), bilan);
                Environment.Exit(0); // un essai : rien à enregistrer, et rien ne doit retenir la fin
            };
            ensuite.Start();
        };
        minuteur.Start();
    }

    private static string Nom(Window f) => f.GetType().Name;

    private static void Rendre(Window f, string base_, string suffixe, List<string> bilan)
    {
        if (f.Content is not FrameworkElement racine) return;
        racine.UpdateLayout();
        double l = racine.ActualWidth, h = racine.ActualHeight;
        if (l < 1 || h < 1) return;
        foreach (var e in Echelles)
        {
            var rendu = new RenderTargetBitmap((int)Math.Ceiling(l * e), (int)Math.Ceiling(h * e), 96 * e, 96 * e, PixelFormats.Pbgra32);
            var fond = new DrawingVisual();
            using (var dc = fond.RenderOpen())
            {
                dc.DrawRectangle(f.Background ?? Brushes.Black, null, new Rect(0, 0, l, h));
                dc.DrawRectangle(new VisualBrush(racine), null, new Rect(0, 0, l, h));
            }
            rendu.Render(fond);
            var png = new PngBitmapEncoder();
            png.Frames.Add(BitmapFrame.Create(rendu));
            using var flux = File.Create($"{base_}{suffixe}-{(int)(e * 100)}.png");
            png.Save(flux);
        }
        bilan.Add($"{Path.GetFileName(base_)}{suffixe} {l:0}x{h:0} défileur-horizontal={DefileurHorizontal(racine)}");
    }

    // Un ScrollViewer dont la barre horizontale est visible, ou dont le contenu déborde à droite.
    private static string DefileurHorizontal(DependencyObject o)
    {
        var trouves = new List<string>();
        void Parcourir(DependencyObject d)
        {
            if (d is System.Windows.Controls.ScrollViewer sv && sv.IsVisible
                && (sv.ComputedHorizontalScrollBarVisibility == Visibility.Visible || sv.ExtentWidth > sv.ViewportWidth + 0.5))
                trouves.Add($"{sv.ExtentWidth:0}>{sv.ViewportWidth:0}");
            for (int i = 0; i < VisualTreeHelper.GetChildrenCount(d); i++) Parcourir(VisualTreeHelper.GetChild(d, i));
        }
        Parcourir(o);
        return trouves.Count == 0 ? "non" : "OUI " + string.Join(" ", trouves);
    }
}
