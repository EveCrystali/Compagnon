using System.Globalization;
using System.IO;
using System.Text;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Interop;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Threading;

namespace PilouBureau;

// --essai=menu[:<porte>[/<sous-porte>]][:clair|sombre][:moment][:joueur] : le vrai menu clic droit ouvert sur Pilou.
//   joueur : le menu attend un vrai clic droit (pilou.txt dit où) ; sinon il s'ouvre seul, sans clic.
//   <porte> : un mot de son titre, sans accents (jouer, apparence, montre, cache, progres, amis, reglages, expedition) ;
//   apparence/accessoire ouvre aussi le sous-menu Accessoire.
//   moment : une expédition en cours et un Pilou qui a faim (rien n'est écrit), pour la zone « En ce moment ».
// Avec --captures=<dossier> : chaque fenêtre du menu (menu, sous-menus) rendue en PNG à 100, 125 et 150 %, et
// « menu.txt » donne leur place à l'écran en pixels physiques (pour recadrer une vraie capture d'écran).
// Le menu reste ouvert jusqu'à la fin de l'essai : il peut aussi être photographié à l'écran.
public sealed partial class FenetrePilou
{
    private void EssaiMenu(string quoi)
    {
        string chemin = "";
        bool moment = false, joueur = false;
        foreach (var p in quoi.Split(':', StringSplitOptions.RemoveEmptyEntries))
        {
            if (p is "clair" or "sombre")
            {
                _reglages.Theme = p == "sombre" ? ThemeBulle.Sombre : ThemeBulle.Clair;
                _sombre = p == "sombre";
                _themeLu = Maintenant;
            }
            else if (p == "moment") moment = true;
            else if (p == "joueur") joueur = true;
            else chemin = p;
        }
        if (moment)
        {
            if (!joueur) EssaiExpedition("absent"); // en expédition, Pilou n'est pas là pour recevoir le clic
            EssaiSoins(Soins.Faim);
        }
        // Il reste sous le curseur jusqu'au clic (en mémoire) ; le menu, lui, montre le vrai réglage.
        if (joueur)
        {
            bool promenade = _reglages.Promenade;
            _reglages.Promenade = false;
            void Rendre(object? s, ContextMenuEventArgs e)
            {
                _scene.ContextMenuOpening -= Rendre;
                _bulle.ContextMenuOpening -= Rendre;
                _reglages.Promenade = promenade;
            }
            _scene.ContextMenuOpening += Rendre;
            _bulle.ContextMenuOpening += Rendre;
        }
        if (_scene.ContextMenu is not { } menu) return;
        var mots = chemin.Split('/', StringSplitOptions.RemoveEmptyEntries);
        var dossier = Environment.GetCommandLineArgs().FirstOrDefault(a => a.StartsWith("--captures=", StringComparison.Ordinal))?["--captures=".Length..]?.Trim('"');
        // Après l'ouverture : le vrai curseur passe sur chaque porte du chemin et le survol ouvre son sous-menu,
        // puis le rendu. Un sous-menu ouvert par le seul code (IsSubmenuOpen) reste invisible à l'écran.
        void Ouvert()
        {
            Apres(600, () => Survoler(menu, mots, 0));
            if (dossier is not null) Apres(1100 + 900 * mots.Length, () => RendreMenu(dossier, quoi));
        }
        if (joueur)
        {
            // Mode joueur : rien ne s'ouvre tout seul ; « pilou.txt » dit où cliquer (centre de Pilou, pixels
            // physiques) et le menu attend un vrai clic droit.
            void UneFois(object? s, RoutedEventArgs e)
            {
                menu.Opened -= UneFois;
                Ouvert();
                if (dossier is not null) JournalClavier(menu, Path.Combine(dossier, "clavier.txt"));
            }
            menu.Opened += UneFois;
            if (dossier is not null)
                Apres(300, () =>
                {
                    Directory.CreateDirectory(dossier);
                    var c = VersEcran.Transform(new Point(_x, _yPieds - 10 * Scene.PA * K));
                    File.WriteAllText(Path.Combine(dossier, "pilou.txt"), string.Create(CultureInfo.InvariantCulture, $"{c.X:0} {c.Y:0}"));
                });
            return;
        }
        Apres(300, () =>
        {
            menu.PlacementTarget = _scene;
            menu.Placement = PlacementMode.Top;
            menu.IsOpen = true;
            Ouvert();
        });
    }

    private void Survoler(ItemsControl parent, string[] mots, int i)
    {
        if (i >= mots.Length || TrouverEntree(parent, mots[i]) is not { HasItems: true } m) return;
        var centre = m.PointToScreen(new Point(m.ActualWidth * 0.4, m.ActualHeight / 2));
        Natif.PlacerSouris((int)centre.X, (int)centre.Y);
        Apres(700, () =>
        {
            if (!m.IsSubmenuOpen) m.IsSubmenuOpen = true; // filet : si le survol n'a pas suffi
            m.UpdateLayout();
            Survoler(m, mots, i + 1);
        });
    }

    // Essai du clavier (mode joueur) : toutes les 100 ms, ce qui a le focus, ce qui est surligné, les sous-menus ouverts,
    // et si la fenêtre de Pilou ou une autre appli a le premier plan ; une ligne à chaque changement.
    private void JournalClavier(ContextMenu menu, string fichier)
    {
        string avant = "";
        var t = new DispatcherTimer(DispatcherPriority.Background, Dispatcher) { Interval = TimeSpan.FromMilliseconds(100) };
        t.Tick += (_, _) =>
        {
            string Nom(object? o) => o is MenuItem { Header: string h } ? h : o is MenuItem ? "(bandeau)" : o?.GetType().Name ?? "rien";
            var surlignes = new List<string>();
            void Parcourir(ItemsControl c)
            {
                foreach (var m in c.Items.OfType<MenuItem>())
                {
                    if (m.IsHighlighted) surlignes.Add(Nom(m));
                    if (m.IsSubmenuOpen) { surlignes.Add("▸"); Parcourir(m); }
                }
            }
            Parcourir(menu);
            var ligne = menu.IsOpen
                ? $"focus={Nom(System.Windows.Input.Keyboard.FocusedElement)} · surligné={string.Join(" / ", surlignes)} · Pilou actif={IsActive} · premier plan={(Natif.DeNotreProcessus(Natif.AuPremierPlan()) ? "Pilou" : "autre appli")}"
                : "menu fermé";
            if (ligne != avant) File.AppendAllText(fichier, $"{DateTime.Now:HH:mm:ss.f} {ligne}{Environment.NewLine}");
            avant = ligne;
            if (!menu.IsOpen) t.Stop();
        };
        t.Start();
    }

    private void Apres(double ms, Action faire)
    {
        var m = new DispatcherTimer(DispatcherPriority.Normal, Dispatcher) { Interval = TimeSpan.FromMilliseconds(ms) };
        m.Tick += (_, _) =>
        {
            m.Stop();
            faire();
        };
        m.Start();
    }

    private static string SansAccents(string s)
    {
        var d = s.Normalize(NormalizationForm.FormD);
        return new string(d.Where(c => CharUnicodeInfo.GetUnicodeCategory(c) != UnicodeCategory.NonSpacingMark).ToArray()).ToLowerInvariant();
    }

    private static MenuItem? TrouverEntree(ItemsControl parent, string mot) =>
        parent.Items.OfType<MenuItem>().FirstOrDefault(m => m.Header is string h && SansAccents(h).Contains(SansAccents(mot)));

    // Les fenêtres du menu (la racine de chaque Popup ouvert), du menu principal au sous-menu le plus profond.
    private static List<FrameworkElement> FenetresDuMenu() =>
        PresentationSource.CurrentSources.OfType<HwndSource>()
            .Select(s => s.RootVisual).OfType<FrameworkElement>()
            .Where(r => r.GetType().Name == "PopupRoot" && r.IsVisible && r.ActualWidth > 1)
            .OrderBy(r => r.PointToScreen(new Point(0, 0)).X)
            .ToList();

    private static void RendreMenu(string dossier, string quoi)
    {
        Directory.CreateDirectory(dossier);
        var nom = "menu" + (quoi == "" ? "" : "-" + string.Join("-", quoi.Split(':', '/').Where(p => p != "")));
        var bilan = new List<string>();
        var fenetres = FenetresDuMenu();
        for (int i = 0; i < fenetres.Count; i++)
        {
            var r = fenetres[i];
            r.UpdateLayout();
            double l = r.ActualWidth, h = r.ActualHeight;
            var haut = r.PointToScreen(new Point(0, 0));
            var bas = r.PointToScreen(new Point(l, h));
            bilan.Add(string.Create(CultureInfo.InvariantCulture,
                $"{nom}-{i} {l:0}x{h:0} écran {haut.X:0},{haut.Y:0} → {bas.X:0},{bas.Y:0}"));
            foreach (var e in CapturesEssai.Echelles)
            {
                var rendu = new RenderTargetBitmap((int)Math.Ceiling(l * e), (int)Math.Ceiling(h * e), 96 * e, 96 * e, PixelFormats.Pbgra32);
                rendu.Render(r);
                var png = new PngBitmapEncoder();
                png.Frames.Add(BitmapFrame.Create(rendu));
                using var flux = File.Create(Path.Combine(dossier, $"{nom}-{i}-{(int)(e * 100)}.png"));
                png.Save(flux);
            }
        }
        File.AppendAllLines(Path.Combine(dossier, "menu.txt"), bilan);
    }
}
