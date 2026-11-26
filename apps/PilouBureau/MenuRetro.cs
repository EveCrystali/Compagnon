using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Interop;
using System.Windows.Media;
using System.Windows.Threading;

namespace PilouBureau;

// Habillage rétro du menu clic droit (MenuRetro.xaml) et couleurs selon le thème : bleu nuit (comme la boutique)
// ou crème. Surbrillance orange la nuit, bleue le jour ; coche bleue ; jamais d'opposition rouge / vert.
public partial class MenuRetro : ResourceDictionary
{
    private static MenuRetro? _commun;

    public MenuRetro()
    {
        InitializeComponent();
    }

    private static Brush Gel(string hex)
    {
        var b = new SolidColorBrush((Color)ColorConverter.ConvertFromString(hex));
        b.Freeze();
        return b;
    }

    private static readonly (string Cle, Brush Nuit, Brush Jour)[] Couleurs =
    {
        ("MenuFond", Bandeau.Nuit, Gel("#fbf3e4")),
        ("MenuTexte", Bandeau.ArgentClair, Bandeau.Encre),
        ("MenuPale", Bandeau.Argent, Gel("#57606a")),
        ("MenuEteint", Gel("#7d8796"), Gel("#767c84")),
        ("MenuSurvolFond", Bandeau.OrangePo, Gel("#1f5fae")),
        ("MenuSurvolTexte", Bandeau.Nuit, Gel("#ffffff")),
        ("MenuBordExt", Gel("#0b0e1a"), Bandeau.Encre),
        ("MenuBordMilieu", Bandeau.Bord, Gel("#2f7ed8")),
        ("MenuBiseauClair", Gel("#3a4270"), Gel("#ffffff")),
        ("MenuBiseauSombre", Gel("#0b0e1a"), Gel("#d9c7a3")),
        ("MenuPointilles", Bandeau.Bord, Gel("#c86a1c")),
        ("MenuCoche", Bandeau.BleuXp, Gel("#1f5fae")),
    };

    // À appeler à chaque ouverture : le thème de Pilou a pu changer depuis.
    public static void Habiller(ContextMenu menu, bool sombre)
    {
        try { HabillerSansFilet(menu, sombre); }
        catch (Exception e) { System.Diagnostics.Debug.WriteLine("menu rétro indisponible : " + e); }
    }

    private static void HabillerSansFilet(ContextMenu menu, bool sombre)
    {
        _commun ??= new MenuRetro();
        if (!menu.Resources.MergedDictionaries.Contains(_commun)) menu.Resources.MergedDictionaries.Add(_commun);
        if (menu.Style is null && _commun["MenuRetroStyle"] is Style s) menu.Style = s;
        foreach (var (cle, nuit, jour) in Couleurs) menu.Resources[cle] = sombre ? nuit : jour;
    }
}

// Le menu clic droit d'une fenêtre qui ne s'active jamais (WS_EX_NOACTIVATE) ne se ferme pas tout seul quand on
// clique ailleurs : sans le premier plan, WPF ne reçoit pas le clic extérieur qui lui fait perdre la capture.
// Correctif classique des menus de zone de notification : à l'ouverture, on met la fenêtre du menu au premier plan
// (permis : on vient de recevoir le clic droit). Filet de sécurité : toutes les 50 ms, un bouton enfoncé hors du menu
// et de ses sous-menus, ou le focus parti dans une autre appli, ferme le menu ; Échap aussi.
// À la fermeture, le premier plan revient à la fenêtre d'avant (Pilou ne garde pas le clavier), sauf si une fenêtre
// de Pilou (boutique…) ou une autre appli l'a pris entre-temps.
internal sealed class MenuDiscret
{
    private readonly ContextMenu _menu;
    private readonly Window _pilou;
    private readonly DispatcherTimer _veille;
    private bool _basAvant, _aEuLeFocus;

    public MenuDiscret(ContextMenu menu, Window pilou)
    {
        _menu = menu;
        _pilou = pilou;
        _veille = new DispatcherTimer(DispatcherPriority.Input, menu.Dispatcher) { Interval = TimeSpan.FromMilliseconds(50) };
        _veille.Tick += (_, _) => Veiller();
        menu.Opened += (_, _) => Ouvert();
        menu.Closed += (_, _) => Ferme();
        menu.PreviewKeyDown += (_, e) =>
        {
            if (e.Key != Key.Escape) return;
            _menu.IsOpen = false;
            e.Handled = true;
        };
    }

    private void Ouvert()
    {
        // Surtout pas de SetForegroundWindow ici : changer d'activation pendant que le menu est ouvert lui fait
        // perdre la capture de la souris, et WPF le referme aussitôt (v0.9.31 : le menu n'apparaissait plus).
        // On ne fait que surveiller les clics : un bouton enfoncé hors du menu le ferme.
        _basAvant = Natif.BoutonEnfonce();
        _aEuLeFocus = Natif.DeNotreProcessus(Natif.AuPremierPlan());
        _veille.Start();
    }

    private void Veiller()
    {
        if (!_menu.IsOpen)
        {
            _veille.Stop();
            return;
        }
        bool bas = Natif.BoutonEnfonce();
        bool chezNous = Natif.DeNotreProcessus(Natif.AuPremierPlan());
        if (chezNous) _aEuLeFocus = true;
        var (x, y) = Natif.Souris();
        bool dedans = x != int.MinValue && Clics.DansUne(Natif.FenetresPopup(), x, y);
        if (Clics.FermerMenu(_basAvant, bas, dedans, _aEuLeFocus, chezNous)) _menu.IsOpen = false;
        _basAvant = bas;
    }

    private void Ferme() => _veille.Stop();
}
