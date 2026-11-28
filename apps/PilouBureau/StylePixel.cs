using System.Reflection;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Input;
using System.Windows.Media;

namespace PilouBureau;

// La main de Pilou dans les fenêtres du PC (docs/STYLE.md) : les pièces communes, à côté du cadre (CadrePixel.cs) et
// du texte (TextePixel.cs). Le pendant du téléphone est Style.java.
//   Texte      un texte en police pixel, aux pixels entiers de sa propre fenêtre ; tailles Petit, Corps, Grand
//   Enseigne   un mot en capitales, police « titre », avec une ombre d'un pixel de police
//   BoutonPixel  un bouton au cadre pixel : principal (fond d'accent) ou secondaire ; survol, appui, fermé
//   IconePixel   une icône de la banque (« ui-… », « signe-… ») teintée
//   Signes     les signes de clavier dessinés par leur sprite 7 × 7 dans un texte (assets/signes.txt)
//   Defileur   la barre de défilement en pixels (un poussoir carré dans un creux)
internal static class StylePixel
{
    // Tailles d'un pixel de police, en unités WPF (docs/STYLE.md, « Texte ») : 1, 2 et 3 pixels physiques à 100 %.
    // Plancher de lisibilité : un texte en minuscules ne descend jamais sous « Corps » (hauteur d'x de 10 px à 100 % ;
    // le menu « Sept portes », qui se lit bien, en fait 7). « Petit » (hauteur d'x de 5 px) est réservé aux
    // étiquettes en capitales et aux nombres, dont la hauteur fait 7 px : StylePixel.Etiquette.
    public const double Petit = 1.3, Corps = 2, Grand = 3;

    private static readonly System.Globalization.CultureInfo Francais = new("fr-FR");

    public static string Capitales(string s) => s.ToUpper(Francais);

    // Étiquette d'un ou deux mots : capitales, police « titre », taille « petit » (la seule place de cette taille).
    public static TextePixel Etiquette(string texte, Brush couleur) => Texte(Capitales(texte), couleur, Petit, true);

    public static readonly Brush Eteint = FenetreAventure.Gel("#7d8796"), Creux = FenetreAventure.Gel("#2a3156"),
        Coche = FenetreAventure.Gel("#6cb6ff"), Orange = FenetreAventure.Gel("#f69d50"), Page = FenetreAventure.Gel("#0b0e1a");

    private static readonly Color EncreIcone = Color.FromRgb(0x1c, 0x21, 0x28);

    // Pixels physiques par unité WPF pour un élément : la mise à l'échelle de l'écran de sa fenêtre.
    public static double Physique(Visual v) => VisualTreeHelper.GetDpi(v).DpiScaleX;

    public static TextePixel Texte(string texte, Brush couleur, double taille = Petit, bool gras = false)
    {
        TextePixel t = null!;
        t = new TextePixel(texte, couleur) { Taille = taille, Titre = gras, PhysiqueParUnite = () => Physique(t) };
        return t;
    }

    // Un mot d'enseigne (« BOUTIQUE », « ESSAYAGE ») : police « titre », ombre d'un pixel de police en bas à droite.
    public static Grid Enseigne(string texte, Brush couleur, Brush? ombre, double taille)
    {
        var g = new Grid { HorizontalAlignment = HorizontalAlignment.Left, SnapsToDevicePixels = true };
        if (ombre is not null)
        {
            var o = Texte(texte, ombre, taille, true);
            o.Margin = new Thickness(taille, taille, 0, 0);
            o.IsHitTestVisible = false;
            g.Children.Add(o);
        }
        var t = Texte(texte, couleur, taille, true);
        t.Margin = new Thickness(0, 0, taille, taille);
        g.Children.Add(t);
        // Les capitales occupent les rangées 3 à 9 : on rogne les rangées d'accent vides du haut (sauf deux, pour É).
        g.Margin = new Thickness(0, -taille, 0, 0);
        return g;
    }

    // Le titre-logo d'une fenêtre, au pixel fin (LogoPixel.cs) : orange, relief, cerne, ombre à la couleur du bord.
    public static LogoPixel Logo(string texte, Brush? couleur = null, Brush? ombre = null) => new(texte, couleur ?? Orange, ombre);

    // La première forme qui tient dans la largeur donnée (unités WPF), de la plus longue à la plus courte ; la
    // dernière sinon. Un texte qui ne tient pas se reformule, il ne se tronque pas (comme Style.choisir sur le téléphone).
    public static string Choisir(double largeur, double taille, bool gras, Visual pour, params string[] formes)
    {
        var police = gras ? PolicePixel.Titre : PolicePixel.Texte;
        if (police is null) return formes[0];
        double ppu = Math.Max(0.1, Physique(pour)), unite = PolicePixel.PixelsPhysiques(taille, ppu) / ppu;
        foreach (var f in formes)
            if (police.Largeur(PolicePixel.Preparer(Preparer(f))) * unite <= largeur) return f;
        return formes[^1];
    }

    // ---- Signes : code d'un caractère → sprite 7 × 7 (assets/signes.txt, écrit par outils/sprites/icones.py).

    private static Dictionary<int, string>? _signes;

    public static IReadOnlyDictionary<int, string> Signes
    {
        get
        {
            if (_signes is not null) return _signes;
            var d = new Dictionary<int, string>();
            try
            {
                using var st = Assembly.GetExecutingAssembly().GetManifestResourceStream("pilou:signes.txt");
                if (st is not null)
                {
                    using var r = new System.IO.StreamReader(st);
                    foreach (var l in r.ReadToEnd().Split('\n'))
                    {
                        var t = l.Trim();
                        int i = t.IndexOf(' ');
                        if (t.Length == 0 || t[0] == '#' || i < 0) continue;
                        if (int.TryParse(t[..i], System.Globalization.NumberStyles.HexNumber, null, out var code)) d[code] = t[(i + 1)..].Trim();
                    }
                }
            }
            catch (System.IO.IOException)
            {
                // table absente : les signes restent dessinés par la police système
            }
            return _signes = d;
        }
    }

    // Signes de clavier que la police dessine déjà sous un autre code : le même dessin partout (comme Style.preparer).
    public static string Preparer(string s)
    {
        if (s.IndexOfAny(Doublons) < 0) return s;
        return s.Replace('⇢', '→').Replace('➜', '→').Replace('➔', '→').Replace('▴', '▲').Replace('▾', '▼')
            .Replace('❗', '!').Replace('✕', '✗').Replace('✖', '✗').Replace('►', '▶');
    }

    private static readonly char[] Doublons = { '⇢', '➜', '➔', '▴', '▾', '❗', '✕', '✖', '►' };

    // Dessine un sprite d'icône : son encre prend la couleur donnée, son accent orange reste. pas : unités par pixel du sprite.
    public static void Dessiner(DrawingContext dc, Sprite s, double x, double y, double pas, Brush couleur)
    {
        var im = s.Images[0];
        var pinceaux = new Dictionary<char, Brush>();
        for (int j = 0; j < im.Length; j++)
        {
            string l = im[j];
            int i = 0;
            while (i < l.Length)
            {
                char ch = l[i];
                if (ch == '.')
                {
                    i++;
                    continue;
                }
                int fin = i;
                while (fin < l.Length && l[fin] == ch) fin++;
                if (!pinceaux.TryGetValue(ch, out var b))
                {
                    uint c = s.Palette.TryGetValue(ch, out var code) ? Sprite.Couleur(code) : 0;
                    var col = Color.FromArgb((byte)(c >> 24), (byte)(c >> 16), (byte)(c >> 8), (byte)c);
                    b = col == EncreIcone ? couleur : new SolidColorBrush(col);
                    if (b.CanFreeze && !b.IsFrozen) b.Freeze();
                    pinceaux[ch] = b;
                }
                dc.DrawRectangle(b, null, new Rect(x + i * pas, y + j * pas, (fin - i) * pas, pas));
                i = fin;
            }
        }
    }

    // Le sprite d'un signe pour ce code, au dessin fin si demandé ; null si ce n'est pas un signe d'interface.
    public static Sprite? Signe(int code, bool fin) =>
        Signes.TryGetValue(code, out var id) ? (fin ? Banque.Commune.Fin(id) : null) ?? Banque.Commune[id] : null;

    // ---- Barre de défilement en pixels : un poussoir carré (bord violet) dans un creux, sans flèches.

    private static ResourceDictionary? _defileur;

    public static void Defileur(FrameworkElement racine)
    {
        _defileur ??= new ResourceDictionary { Source = new Uri("/PilouBureau;component/StyleFenetres.xaml", UriKind.Relative) };
        if (!racine.Resources.MergedDictionaries.Contains(_defileur)) racine.Resources.MergedDictionaries.Add(_defileur);
    }
}

// Une icône de la banque (« ui-… » 12 × 12, « signe-… » 7 × 7), teintée ; Pixel : unités WPF par pixel de l'icône,
// ramenées au nombre entier de pixels physiques le plus proche (dessin fin quand ce nombre est pair).
internal sealed class IconePixel : FrameworkElement
{
    private readonly string _id;
    private Brush _couleur;

    public double Pixel { get; set; } = 2;

    public IconePixel(string id, Brush couleur)
    {
        _id = id;
        _couleur = couleur;
        SnapsToDevicePixels = true;
        RenderOptions.SetEdgeMode(this, EdgeMode.Aliased);
        IsHitTestVisible = false;
    }

    public Brush Couleur
    {
        get => _couleur;
        set
        {
            _couleur = value;
            InvalidateVisual();
        }
    }

    private (int N, double Unite) Mesure()
    {
        double ppu = Math.Max(0.1, StylePixel.Physique(this));
        int n = PolicePixel.PixelsPhysiques(Pixel, ppu);
        return (n, n / ppu);
    }

    protected override Size MeasureOverride(Size dispo)
    {
        var s = Banque.Commune[_id];
        if (s is null) return new Size(0, 0);
        double u = Mesure().Unite;
        return new Size(s.Images[0][0].Length * u, s.Images[0].Length * u);
    }

    protected override void OnRender(DrawingContext dc)
    {
        var (n, u) = Mesure();
        bool fin = Finesse.Active && n % 2 == 0;
        var s = (fin ? Banque.Commune.Fin(_id) : null) ?? Banque.Commune[_id];
        if (s is null) return;
        var petit = Banque.Commune[_id];
        double pas = petit is not null && s.Images[0].Length > petit.Images[0].Length ? u / 2 : u;
        StylePixel.Dessiner(dc, s, 0, 0, pas, _couleur);
    }
}

// Un bouton au cadre pixel (docs/STYLE.md, « États »). Principal : fond d'accent, texte inversé. Secondaire : fond de
// nuit. Survol et appui : fond d'accent, et le cadre s'enfonce d'un module à l'appui. Fermé : texte éteint, bord en
// pointillés, plus d'ombre portée. C'est un vrai Button (clavier, Click, IsEnabled) dont l'habit est en pixels.
internal sealed class BoutonPixel : Button
{
    private readonly CadrePixel _cadre;
    private readonly TextePixel _texte;
    private readonly bool _principal;

    public BoutonPixel(string libelle, bool principal = false, double taille = StylePixel.Corps, double u = 2)
    {
        _principal = principal;
        _texte = StylePixel.Texte(libelle, CadrePixel.Texte, taille, true);
        _texte.HorizontalAlignment = HorizontalAlignment.Center;
        _texte.VerticalAlignment = VerticalAlignment.Center;
        _texte.Margin = new Thickness(3 * u, u, 3 * u, u);
        _cadre = new CadrePixel { U = u, Child = _texte };
        // L'habit du système est retiré : il ne reste que le contenu.
        var gabarit = new ControlTemplate(typeof(Button)) { VisualTree = new FrameworkElementFactory(typeof(ContentPresenter)) };
        Template = gabarit;
        Content = _cadre;
        Cursor = Cursors.Hand;
        Focusable = true;
        FocusVisualStyle = null;
        SnapsToDevicePixels = true;
        UseLayoutRounding = true;
        MouseEnter += (_, _) => Peindre();
        MouseLeave += (_, _) => Peindre();
        IsEnabledChanged += (_, _) => Peindre();
        GotKeyboardFocus += (_, _) => Peindre();
        LostKeyboardFocus += (_, _) => Peindre();
        Peindre();
    }

    public string Libelle
    {
        get => _texte.Texte;
        set => _texte.Texte = value;
    }

    protected override void OnIsPressedChanged(DependencyPropertyChangedEventArgs e)
    {
        base.OnIsPressedChanged(e);
        Peindre();
    }

    private void Peindre()
    {
        bool ferme = !IsEnabled, survol = !ferme && (IsMouseOver || IsKeyboardFocused);
        _cadre.Pointille = ferme;
        _cadre.Fond = _principal && !ferme ? CadrePixel.SurvolFond : CadrePixel.FondNuit;
        _cadre.Couleur = ferme ? StylePixel.Eteint : _principal ? CadrePixel.Ombre : CadrePixel.Bord;
        _cadre.Survol = survol && !_principal;
        _cadre.Enfonce = !ferme && IsPressed;
        _texte.Couleur = ferme ? StylePixel.Eteint : _principal || survol || IsPressed ? CadrePixel.SurvolTexte : CadrePixel.Texte;
        _cadre.InvalidateVisual();
    }
}
