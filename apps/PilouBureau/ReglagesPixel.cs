using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Input;
using System.Windows.Media;

namespace PilouBureau;

// Les pièces de réglage des fenêtres du PC (docs/STYLE.md, « Réglages : lignes, cases, options, curseur »), les mêmes
// que sur le téléphone (Style.interrupteur, Style.pixelOptions, Style.champ) :
//   CasePixel      la case à cocher du menu : carré vide au bord de 2 ; cochée, la coche ✓ prend sa place
//   OptionsPixel   des options exclusives dans un creux : la choisie porte un cadre plat et un rond plein
//   DepliantPixel  une ligne « ▶ titre » qui déplie un texte (à la place de l'Expander du système)
//   StylePixel.Champ  l'habit d'un champ de saisie : creux de nuit, bord carré (le texte reste en police système)
// Ce sont de vrais contrôles (clavier, Click, IsEnabled) dont seul l'habit est en pixels.

// Le carré de la case : vide au bord de 2 unités ; cochée, la coche seule, à la couleur « coche ».
internal sealed class CocheDessin : FrameworkElement
{
    private static readonly string[] Motif = { ".......", "......#", ".....##", "#...##.", "##.##..", ".###...", "..#...." };

    public bool Cochee { get; set; }
    public Brush Couleur { get; set; } = CadrePixel.Pale;

    public CocheDessin()
    {
        Width = Height = 16;
        SnapsToDevicePixels = true;
        RenderOptions.SetEdgeMode(this, EdgeMode.Aliased);
    }

    protected override void OnRender(DrawingContext dc)
    {
        dc.DrawRectangle(Brushes.Transparent, null, new Rect(0, 0, 16, 16));
        if (!Cochee)
        {
            dc.DrawRectangle(Couleur, null, new Rect(0, 0, 16, 2));
            dc.DrawRectangle(Couleur, null, new Rect(0, 14, 16, 2));
            dc.DrawRectangle(Couleur, null, new Rect(0, 2, 2, 12));
            dc.DrawRectangle(Couleur, null, new Rect(14, 2, 2, 12));
            return;
        }
        for (int y = 0; y < 7; y++)
        for (int x = 0; x < 7; x++)
            if (Motif[y][x] == '#') dc.DrawRectangle(Couleur, null, new Rect(1 + x * 2, 1 + y * 2, 2, 2));
    }
}

internal sealed class CasePixel : CheckBox
{
    private readonly CocheDessin _coche = new() { VerticalAlignment = VerticalAlignment.Top, Margin = new Thickness(0, 5, 0, 0) };
    private readonly TextePixel? _texte;

    public CasePixel(string libelle = "")
    {
        var rangee = new DockPanel { Background = Brushes.Transparent };
        DockPanel.SetDock(_coche, Dock.Left);
        rangee.Children.Add(_coche);
        if (libelle != "")
        {
            _texte = StylePixel.Texte(libelle, CadrePixel.Texte, StylePixel.Corps);
            _texte.Margin = new Thickness(10, 0, 0, 0);
            rangee.Children.Add(_texte);
        }
        Template = new ControlTemplate(typeof(CheckBox)) { VisualTree = new FrameworkElementFactory(typeof(ContentPresenter)) };
        Content = rangee;
        Cursor = Cursors.Hand;
        FocusVisualStyle = null;
        SnapsToDevicePixels = true;
        UseLayoutRounding = true;
        Checked += (_, _) => Peindre();
        Unchecked += (_, _) => Peindre();
        MouseEnter += (_, _) => Peindre();
        MouseLeave += (_, _) => Peindre();
        IsEnabledChanged += (_, _) => Peindre();
        GotKeyboardFocus += (_, _) => Peindre();
        LostKeyboardFocus += (_, _) => Peindre();
        Loaded += (_, _) => Peindre();
        Peindre();
    }

    private void Peindre()
    {
        bool ferme = !IsEnabled, survol = !ferme && (IsMouseOver || IsKeyboardFocused), cochee = IsChecked == true;
        _coche.Cochee = cochee;
        _coche.Couleur = ferme ? StylePixel.Eteint : survol ? StylePixel.Orange : cochee ? StylePixel.Coche : CadrePixel.Pale;
        _coche.InvalidateVisual();
        if (_texte is not null) _texte.Couleur = ferme ? StylePixel.Eteint : survol ? StylePixel.Orange : CadrePixel.Texte;
    }
}

// Des options exclusives, côte à côte dans un creux (elles passent à la ligne si la place manque). La choisie porte
// un cadre plat à la couleur « coche » et un rond plein devant son nom ; les autres un rond vide.
internal sealed class OptionsPixel : Border
{
    private readonly List<(Button Bouton, Border Cadre, TextePixel Texte, string Nom)> _options = new();
    private int _index;

    public event Action<int>? Choisi;

    public OptionsPixel(IReadOnlyList<string> noms, int index)
    {
        _index = index;
        Background = StylePixel.Creux;
        Padding = new Thickness(4);
        HorizontalAlignment = HorizontalAlignment.Left;
        SnapsToDevicePixels = true;
        UseLayoutRounding = true;
        var rangee = new WrapPanel();
        for (int i = 0; i < noms.Count; i++)
        {
            int k = i;
            var texte = StylePixel.Texte("", CadrePixel.Pale, StylePixel.Corps);
            var cadre = new Border { BorderThickness = new Thickness(2), Padding = new Thickness(8, 0, 10, 0), Child = texte };
            var b = new Button
            {
                Template = new ControlTemplate(typeof(Button)) { VisualTree = new FrameworkElementFactory(typeof(ContentPresenter)) },
                Content = cadre, Cursor = Cursors.Hand, FocusVisualStyle = null, Margin = new Thickness(0, 0, 2, 0),
            };
            b.Click += (_, _) =>
            {
                if (_index == k) return;
                _index = k;
                Peindre();
                Choisi?.Invoke(k);
            };
            b.MouseEnter += (_, _) => Peindre();
            b.MouseLeave += (_, _) => Peindre();
            b.GotKeyboardFocus += (_, _) => Peindre();
            b.LostKeyboardFocus += (_, _) => Peindre();
            _options.Add((b, cadre, texte, noms[i]));
            rangee.Children.Add(b);
        }
        Child = rangee;
        Peindre();
    }

    public int Index => _index;

    private void Peindre()
    {
        for (int i = 0; i < _options.Count; i++)
        {
            var (b, cadre, texte, nom) = _options[i];
            bool choisie = i == _index, survol = b.IsMouseOver || b.IsKeyboardFocused;
            texte.Texte = (choisie ? "● " : "○ ") + nom;
            texte.Couleur = survol ? StylePixel.Orange : choisie ? CadrePixel.Texte : CadrePixel.Pale;
            cadre.BorderBrush = choisie ? StylePixel.Coche : Brushes.Transparent;
            cadre.Background = choisie ? CadrePixel.FondNuit : Brushes.Transparent;
        }
    }
}

// Une ligne « ▶ titre » ; un clic déplie le texte dessous (« ▼ titre »).
internal sealed class DepliantPixel : StackPanel
{
    public DepliantPixel(string titre, string texte)
    {
        var tete = StylePixel.Texte("▶ " + titre, StylePixel.Coche, StylePixel.Corps);
        var corps = StylePixel.Texte(texte, CadrePixel.Pale, StylePixel.Corps);
        corps.Margin = new Thickness(18, 0, 0, 2);
        corps.Visibility = Visibility.Collapsed;
        var b = new Button
        {
            Template = new ControlTemplate(typeof(Button)) { VisualTree = new FrameworkElementFactory(typeof(ContentPresenter)) },
            Content = tete, Cursor = Cursors.Hand, FocusVisualStyle = null, HorizontalAlignment = HorizontalAlignment.Left,
        };
        void Peindre() => tete.Couleur = b.IsMouseOver || b.IsKeyboardFocused ? StylePixel.Orange : StylePixel.Coche;
        b.Click += (_, _) =>
        {
            bool ouvert = corps.Visibility != Visibility.Visible;
            corps.Visibility = ouvert ? Visibility.Visible : Visibility.Collapsed;
            tete.Texte = (ouvert ? "▼ " : "▶ ") + titre;
        };
        b.MouseEnter += (_, _) => Peindre();
        b.MouseLeave += (_, _) => Peindre();
        b.GotKeyboardFocus += (_, _) => Peindre();
        b.LostKeyboardFocus += (_, _) => Peindre();
        Children.Add(b);
        Children.Add(corps);
    }
}

internal static class ChampPixel
{
    private static readonly Brush Fond = FenetreAventure.Gel("#1f2540");

    // L'habit d'un champ de saisie (TextBox, PasswordBox) : creux de nuit, bord carré de 2 à la couleur du bord. Le
    // texte reste en police système (docs/STYLE.md, « Où la police système reste permise »).
    public static T Habiller<T>(T champ) where T : Control
    {
        champ.Background = Fond;
        champ.Foreground = CadrePixel.Texte;
        champ.BorderBrush = CadrePixel.Bord;
        champ.BorderThickness = new Thickness(2);
        champ.FontSize = 15;
        champ.Padding = new Thickness(6, 3, 6, 3);
        champ.VerticalContentAlignment = VerticalAlignment.Center;
        if (champ is TextBoxBase t)
        {
            t.CaretBrush = CadrePixel.Texte;
            t.SelectionBrush = StylePixel.Orange;
        }
        if (champ is PasswordBox p)
        {
            p.CaretBrush = CadrePixel.Texte;
            p.SelectionBrush = StylePixel.Orange;
        }
        return champ;
    }
}
