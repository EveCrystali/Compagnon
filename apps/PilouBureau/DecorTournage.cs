using System.Globalization;
using System.IO;
using System.Windows;
using System.Windows.Interop;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Threading;

namespace PilouBureau;

// Décor de tournage (visite guidée, outils/tourner-ecran-gauche.ps1) : une fenêtre plein écran sur l'écran filmé,
// sous Pilou et ses fenêtres, qui dessine un bureau FICTIF : fond dégradé bleu nuit → orange doux, trois fenêtres
// factices (éditeur de code, tableur, navigateur) au contenu générique, une fausse barre des tâches avec une
// horloge et une fausse zone de notification où se trouve l'icône de Pilou. Elle cache tout ce qui est à la
// personne (icônes, vraie barre des tâches, console). Elle ne prend ni le focus ni la souris, et vit le temps de
// la visite. Pilou et ses fenêtres, montrés après elle, passent devant (elles sont toutes « au premier plan »).
public sealed class FenetreDecor : Window
{
    private readonly ToileDecor _toile;
    private readonly DispatcherTimer _horloge;

    public CadreEcran Ecran { get; }
    // Haut de la fausse barre des tâches (pixels d'écran) : Pilou s'y pose.
    public int HautBarre { get; }

    public FenetreDecor(CadreEcran ecran, int hauteurBarre)
    {
        Ecran = ecran;
        int barre = hauteurBarre is >= 28 and <= 120 ? hauteurBarre : 48;
        HautBarre = ecran.Bas - barre;
        WindowStyle = WindowStyle.None;
        ResizeMode = ResizeMode.NoResize;
        ShowInTaskbar = false;
        ShowActivated = false;
        Topmost = true;
        Focusable = false;
        IsHitTestVisible = false;
        Title = "Décor de tournage";
        Background = new SolidColorBrush(Color.FromRgb(0x14, 0x1a, 0x33));
        WindowStartupLocation = WindowStartupLocation.Manual;
        Left = ecran.X;
        Top = ecran.Y;
        Width = ecran.Largeur;
        Height = ecran.Hauteur;
        _toile = new ToileDecor { HauteurBarrePx = barre };
        Content = _toile;
        SourceInitialized += (_, _) =>
        {
            var h = new WindowInteropHelper(this).Handle;
            Natif.StyleDiscret(h);
            // Pixels d'écran → unités WPF, maintenant que la mise à l'échelle de cet écran est connue.
            if (PresentationSource.FromVisual(this)?.CompositionTarget?.TransformFromDevice is { } m)
            {
                var a = m.Transform(new Point(ecran.X, ecran.Y));
                var b = m.Transform(new Point(ecran.Droite, ecran.Bas));
                Left = a.X;
                Top = a.Y;
                Width = b.X - a.X;
                Height = b.Y - a.Y;
                _toile.Echelle = m.M22 > 0 ? m.M22 : 1;
            }
        };
        _horloge = new DispatcherTimer(TimeSpan.FromSeconds(5), DispatcherPriority.Background, (_, _) => _toile.InvalidateVisual(), Dispatcher);
        _horloge.Start();
        Closed += (_, _) => _horloge.Stop();
    }

    // Centre de la fausse icône de Pilou près de l'horloge (pixels d'écran) ; null avant le premier affichage.
    public (int X, int Y)? PositionIcone()
    {
        if (_toile.Icone is not { } c || PresentationSource.FromVisual(_toile) is null) return null;
        var p = _toile.PointToScreen(c);
        return ((int)Math.Round(p.X), (int)Math.Round(p.Y));
    }

    // Cadre de la fausse icône (pixels d'écran), pour le cadrage du menu de l'icône.
    public CadreEcran? CadreIcone()
    {
        if (PositionIcone() is not { } p) return null;
        int r = (int)Math.Round(20 / Math.Max(0.1, _toile.Echelle));
        return new CadreEcran(p.X - r, p.Y - r, 2 * r, 2 * r);
    }
}

// Le dessin du décor (unités WPF). Tout est original et générique : aucun nom, aucune marque, aucune donnée réelle.
internal sealed class ToileDecor : FrameworkElement
{
    public int HauteurBarrePx { get; init; } = 48;
    public double Echelle { get; set; } = 1; // unités WPF par pixel d'écran
    public Point? Icone { get; private set; }

    private static readonly ImageSource? IconePilou = ChargerIcone();

    private static SolidColorBrush B(string hex, byte alpha = 255)
    {
        var c = (Color)ColorConverter.ConvertFromString(hex);
        var b = new SolidColorBrush(Color.FromArgb(alpha, c.R, c.G, c.B));
        b.Freeze();
        return b;
    }

    // Palette sans opposition rouge/vert : bleus, orangés, violets, jaunes, gris.
    private static readonly Brush Encre = B("#1b2138"), EncreClaire = B("#262d4a"), Titre = B("#2d3456"), Bord = B("#3b4470");
    private static readonly Brush Bleu = B("#6cb6ff"), Orange = B("#f69d50"), Violet = B("#c6a6f7"), Jaune = B("#e8c46b"), Gris = B("#8b93b8");
    private static readonly Brush GrisPale = B("#c9cfe6"), Blanc = B("#f7f8fc"), Papier = B("#ffffff"), Ligne = B("#e3e6f0");
    private static readonly Brush EnTeteTableur = B("#dce9fb"), BleuFonce = B("#2f6fb8"), OrangeDoux = B("#f3b07a");
    private static readonly Brush Ombre = B("#000000", 70), Barre = B("#0e1222", 235), BarreBord = B("#ffffff", 28);
    private static readonly Typeface Code = new(new FontFamily("Consolas"), FontStyles.Normal, FontWeights.Normal, FontStretches.Normal);
    private static readonly Typeface Texte = new(new FontFamily("Segoe UI"), FontStyles.Normal, FontWeights.Normal, FontStretches.Normal);
    private static readonly Typeface TexteGras = new(new FontFamily("Segoe UI"), FontStyles.Normal, FontWeights.SemiBold, FontStretches.Normal);

    private double Dpi => VisualTreeHelper.GetDpi(this).PixelsPerDip;

    private void Ecrire(DrawingContext dc, string texte, Typeface police, double taille, Brush pinceau, double x, double y)
    {
        var f = new FormattedText(texte, CultureInfo.GetCultureInfo("fr-FR"), FlowDirection.LeftToRight, police, taille, pinceau, Dpi);
        dc.DrawText(f, new Point(x, y));
    }

    protected override void OnRender(DrawingContext dc)
    {
        double l = ActualWidth, h = ActualHeight;
        if (l <= 0 || h <= 0) return;
        double barre = HauteurBarrePx * Echelle;
        double k = Math.Clamp(h / 1440, 0.6, 2); // tout se dessine pour 1440 et s'adapte

        // Fond : dégradé bleu nuit → indigo → orange doux, quelques halos.
        var fond = new LinearGradientBrush { StartPoint = new Point(0, 0), EndPoint = new Point(0.35, 1) };
        fond.GradientStops.Add(new GradientStop(Color.FromRgb(0x12, 0x17, 0x30), 0));
        fond.GradientStops.Add(new GradientStop(Color.FromRgb(0x25, 0x2c, 0x5c), 0.48));
        fond.GradientStops.Add(new GradientStop(Color.FromRgb(0x7a, 0x55, 0x78), 0.78));
        fond.GradientStops.Add(new GradientStop(Color.FromRgb(0xe9, 0x9a, 0x62), 1));
        dc.DrawRectangle(fond, null, new Rect(0, 0, l, h));
        foreach (var (cx, cy, r, couleur, a) in new[]
                 {
                     (0.82, 0.18, 260.0, "#6cb6ff", (byte)26), (0.12, 0.72, 320.0, "#f69d50", (byte)30),
                     (0.55, 0.92, 420.0, "#f3b07a", (byte)34), (0.30, 0.10, 180.0, "#c6a6f7", (byte)22),
                 })
            dc.DrawEllipse(B(couleur, a), null, new Point(l * cx, h * cy), r * k, r * k);

        Editeur(dc, new Rect(l * 0.035, h * 0.05, l * 0.36, h * 0.47), k);
        Tableur(dc, new Rect(l * 0.63, h * 0.06, l * 0.335, h * 0.40), k);
        Navigateur(dc, new Rect(l * 0.33, h * 0.17, l * 0.34, h * 0.38), k);
        BarreDesTaches(dc, new Rect(0, h - barre, l, barre), k);
    }

    private static void Fenetre(DrawingContext dc, Rect r, double k, Brush corps, Brush titre, string nom, Typeface police, Brush texte, ToileDecor t)
    {
        var rayon = 10 * k;
        dc.DrawRoundedRectangle(Ombre, null, new Rect(r.X + 6 * k, r.Y + 10 * k, r.Width, r.Height), rayon, rayon);
        dc.DrawRoundedRectangle(corps, new Pen(Bord, 1), r, rayon, rayon);
        var bandeau = new Rect(r.X, r.Y, r.Width, 34 * k);
        dc.PushClip(new RectangleGeometry(r, rayon, rayon));
        dc.DrawRectangle(titre, null, bandeau);
        dc.Pop();
        double x = r.X + 16 * k;
        foreach (var c in new[] { Orange, Jaune, Gris })
        {
            dc.DrawEllipse(c, null, new Point(x, r.Y + 17 * k), 6 * k, 6 * k);
            x += 20 * k;
        }
        t.Ecrire(dc, nom, police, 13 * k, texte, r.X + 84 * k, r.Y + 8 * k);
    }

    private void Editeur(DrawingContext dc, Rect r, double k)
    {
        Fenetre(dc, r, k, Encre, Titre, "atelier — tri.js", Texte, GrisPale, this);
        double haut = r.Y + 34 * k;
        // Arborescence de fichiers factice.
        var cote = new Rect(r.X, haut, r.Width * 0.24, r.Height - 34 * k);
        dc.PushClip(new RectangleGeometry(new Rect(r.X, haut, r.Width, r.Height - 34 * k), 0, 0));
        dc.DrawRectangle(EncreClaire, null, cote);
        string[] fichiers = { "▾ atelier", "   tri.js", "   meteo.js", "   cartes.js", "▸ essais", "▸ images", "  notes.md" };
        for (int i = 0; i < fichiers.Length; i++)
            Ecrire(dc, fichiers[i], Code, 13 * k, i == 1 ? Blanc : Gris, cote.X + 12 * k, haut + (14 + i * 24) * k);
        dc.DrawRectangle(B("#6cb6ff", 40), null, new Rect(cote.X, haut + 36 * k, cote.Width, 24 * k));
        // Code générique, coloré (bleu, orange, violet, jaune, gris).
        (string Texte, Brush Pinceau, int Retrait)[] lignes =
        {
            ("// trie les cartes par couleur puis par rang", Gris, 0),
            ("import { lireCiel } from './meteo.js';", Violet, 0),
            ("", Gris, 0),
            ("export function trier(cartes) {", Bleu, 0),
            ("const copie = [...cartes];", GrisPale, 1),
            ("copie.sort((a, b) => a.rang - b.rang);", GrisPale, 1),
            ("return copie;", Orange, 1),
            ("}", Bleu, 0),
            ("", Gris, 0),
            ("export async function sortie(jour) {", Bleu, 0),
            ("const ciel = await lireCiel(jour);", GrisPale, 1),
            ("if (ciel.pluie) prendre('parapluie');", Jaune, 1),
            ("for (const t of liste) {", Violet, 1),
            ("t.fini = t.etapes.every(e => e.ok);", GrisPale, 2),
            ("}", Violet, 1),
            ("return liste.filter(t => t.fini).length;", Orange, 1),
            ("}", Bleu, 0),
        };
        double x0 = cote.Right + 16 * k, y = haut + 14 * k;
        for (int i = 0; i < lignes.Length && y < r.Bottom - 24 * k; i++, y += 24 * k)
        {
            Ecrire(dc, (i + 1).ToString(CultureInfo.InvariantCulture).PadLeft(2), Code, 13 * k, B("#5a6288"), x0, y);
            Ecrire(dc, lignes[i].Texte, Code, 14 * k, lignes[i].Pinceau, x0 + (36 + lignes[i].Retrait * 28) * k, y);
        }
        // Le curseur de saisie.
        dc.DrawRectangle(Orange, null, new Rect(x0 + (36 + 28 + 12 * 8.4) * k, haut + (14 + 11 * 24) * k, 2 * k, 18 * k));
        dc.Pop();
    }

    private void Tableur(DrawingContext dc, Rect r, double k)
    {
        Fenetre(dc, r, k, Papier, B("#e9edf7"), "budget-vacances.tableur", Texte, B("#3b4470"), this);
        double haut = r.Y + 34 * k;
        dc.PushClip(new RectangleGeometry(new Rect(r.X, haut, r.Width, r.Height - 34 * k), 0, 0));
        string[] entetes = { "", "A", "B", "C", "D" };
        string[,] cases =
        {
            { "1", "Poste", "Prévu", "Réel", "Écart" },
            { "2", "Train", "180", "164", "-16" },
            { "3", "Gîte", "420", "420", "0" },
            { "4", "Repas", "260", "238", "-22" },
            { "5", "Musée", "45", "52", "+7" },
            { "6", "Vélo", "60", "48", "-12" },
            { "7", "Total", "965", "922", "-43" },
        };
        double colonne0 = 34 * k, ligne = 28 * k;
        double largeur = (r.Width - colonne0) / 4;
        var trait = new Pen(Ligne, 1);
        // En-têtes de colonnes.
        dc.DrawRectangle(B("#f2f4fa"), null, new Rect(r.X, haut, r.Width, ligne));
        for (int c = 1; c < entetes.Length; c++)
            Ecrire(dc, entetes[c], TexteGras, 12 * k, Gris, r.X + colonne0 + (c - 1) * largeur + largeur / 2 - 4 * k, haut + 6 * k);
        for (int i = 0; i < cases.GetLength(0); i++)
        {
            double y = haut + ligne * (i + 1);
            if (i == 0) dc.DrawRectangle(EnTeteTableur, null, new Rect(r.X + colonne0, y, r.Width - colonne0, ligne));
            if (i == cases.GetLength(0) - 1) dc.DrawRectangle(B("#fdebd9"), null, new Rect(r.X + colonne0, y, r.Width - colonne0, ligne));
            dc.DrawLine(trait, new Point(r.X, y), new Point(r.Right, y));
            Ecrire(dc, cases[i, 0], Texte, 12 * k, Gris, r.X + 10 * k, y + 6 * k);
            for (int c = 1; c < 5; c++)
                Ecrire(dc, cases[i, c], i == 0 || c == 1 ? TexteGras : Texte, 13 * k, i == 0 ? BleuFonce : B("#2a2f45"),
                    r.X + colonne0 + (c - 1) * largeur + 10 * k, y + 5 * k);
        }
        for (int c = 0; c < 5; c++)
        {
            double x = r.X + colonne0 + c * largeur;
            dc.DrawLine(trait, new Point(x, haut), new Point(x, haut + ligne * 8));
        }
        // Un petit histogramme : prévu (bleu) contre réel (orange).
        double bas = r.Bottom - 22 * k, gauche = r.X + colonne0 + 10 * k, pas = (r.Width - colonne0 - 20 * k) / 5;
        double haute = Math.Max(20 * k, bas - (haut + ligne * 8 + 18 * k));
        int[] prevu = { 180, 420, 260, 45, 60 }, reel = { 164, 420, 238, 52, 48 };
        for (int i = 0; i < 5; i++)
        {
            double hp = haute * prevu[i] / 420, hr = haute * reel[i] / 420;
            dc.DrawRectangle(Bleu, null, new Rect(gauche + i * pas + pas * 0.18, bas - hp, pas * 0.28, hp));
            dc.DrawRectangle(Orange, null, new Rect(gauche + i * pas + pas * 0.50, bas - hr, pas * 0.28, hr));
        }
        dc.DrawLine(new Pen(B("#b8bfd6"), 1), new Point(gauche, bas), new Point(r.Right - 10 * k, bas));
        dc.Pop();
    }

    private void Navigateur(DrawingContext dc, Rect r, double k)
    {
        Fenetre(dc, r, k, Blanc, B("#dfe4f2"), "Recettes du dimanche", Texte, B("#3b4470"), this);
        double haut = r.Y + 34 * k;
        dc.PushClip(new RectangleGeometry(new Rect(r.X, haut, r.Width, r.Height - 34 * k), 0, 0));
        // Barre d'adresse factice.
        dc.DrawRectangle(B("#eef1f8"), null, new Rect(r.X, haut, r.Width, 40 * k));
        dc.DrawRoundedRectangle(Papier, new Pen(B("#cfd5e6"), 1), new Rect(r.X + 70 * k, haut + 7 * k, r.Width - 90 * k, 26 * k), 13 * k, 13 * k);
        Ecrire(dc, "exemple.org/recettes/tarte-aux-pommes", Texte, 13 * k, B("#5b6386"), r.X + 86 * k, haut + 11 * k);
        foreach (var (i, glyphe) in new[] { (0, "‹"), (1, "›") })
            Ecrire(dc, glyphe, TexteGras, 20 * k, Gris, r.X + (14 + i * 22) * k, haut + 5 * k);
        // Page : bandeau orangé, titre, lignes de texte, trois cartes.
        double y = haut + 40 * k;
        var bandeau = new LinearGradientBrush(Color.FromRgb(0xf6, 0x9d, 0x50), Color.FromRgb(0xe8, 0xc4, 0x6b), 0);
        dc.DrawRectangle(bandeau, null, new Rect(r.X, y, r.Width, 120 * k));
        Ecrire(dc, "Tarte aux pommes", TexteGras, 30 * k, Papier, r.X + 28 * k, y + 28 * k);
        Ecrire(dc, "45 min · 6 parts · facile", Texte, 15 * k, Papier, r.X + 30 * k, y + 74 * k);
        y += 140 * k;
        double[] longueurs = { 0.86, 0.92, 0.70, 0.88, 0.54 };
        foreach (var f in longueurs)
        {
            dc.DrawRoundedRectangle(B("#d5daea"), null, new Rect(r.X + 28 * k, y, (r.Width - 56 * k) * f, 10 * k), 5 * k, 5 * k);
            y += 22 * k;
        }
        y += 10 * k;
        double carte = (r.Width - 56 * k - 2 * 16 * k) / 3;
        Brush[] teintes = { B("#6cb6ff", 110), B("#c6a6f7", 120), B("#f3b07a", 130) };
        for (int i = 0; i < 3; i++)
        {
            var c = new Rect(r.X + 28 * k + i * (carte + 16 * k), y, carte, Math.Max(10, r.Bottom - y - 18 * k));
            dc.DrawRoundedRectangle(teintes[i], null, c, 8 * k, 8 * k);
        }
        dc.Pop();
    }

    private void BarreDesTaches(DrawingContext dc, Rect r, double k)
    {
        dc.DrawRectangle(Barre, null, r);
        dc.DrawLine(new Pen(BarreBord, 1), r.TopLeft, r.TopRight);
        double t = Math.Min(r.Height * 0.62, 34 * k), milieu = r.Y + r.Height / 2;
        // Lanceur et applications factices, au centre : de simples pastilles colorées.
        Brush[] applis = { B("#6cb6ff"), B("#f69d50"), B("#c6a6f7"), B("#e8c46b"), B("#8b93b8"), B("#4f8fd6") };
        double total = (applis.Length + 1) * (t + 12 * k), x = r.X + r.Width / 2 - total / 2;
        // Le lanceur : quatre carrés arrondis (générique).
        double q = t * 0.42;
        for (int i = 0; i < 4; i++)
            dc.DrawRoundedRectangle(B("#c9cfe6"), null, new Rect(x + (i % 2) * (q + 3 * k), milieu - q - 1.5 * k + (i / 2) * (q + 3 * k), q, q), 2 * k, 2 * k);
        x += t + 12 * k;
        for (int i = 0; i < applis.Length; i++, x += t + 12 * k)
        {
            dc.DrawRoundedRectangle(applis[i], null, new Rect(x, milieu - t / 2, t, t), 7 * k, 7 * k);
            dc.DrawRoundedRectangle(B("#ffffff", 70), null, new Rect(x + t * 0.25, milieu - t * 0.2, t * 0.5, t * 0.4), 3 * k, 3 * k);
            if (i < 3) dc.DrawRoundedRectangle(GrisPale, null, new Rect(x + t / 2 - 5 * k, r.Bottom - 6 * k, 10 * k, 3 * k), 1.5 * k, 1.5 * k);
        }
        // Zone de notification : chevron, Pilou, réseau, son, puis l'horloge.
        var maintenant = DateTime.Now;
        string heure = maintenant.ToString("HH:mm", CultureInfo.InvariantCulture), date = maintenant.ToString("dd/MM/yyyy", CultureInfo.InvariantCulture);
        double droite = r.Right - 18 * k;
        var fh = new FormattedText(date, CultureInfo.InvariantCulture, FlowDirection.LeftToRight, Texte, 12 * k, Blanc, Dpi);
        double xh = droite - fh.Width;
        Ecrire(dc, heure, Texte, 12 * k, Blanc, xh + (fh.Width - new FormattedText(heure, CultureInfo.InvariantCulture, FlowDirection.LeftToRight, Texte, 12 * k, Blanc, Dpi).Width), milieu - 17 * k);
        Ecrire(dc, date, Texte, 12 * k, Blanc, xh, milieu + 1 * k);
        double xi = xh - 30 * k;
        // Son : un haut-parleur stylisé.
        var hp = new StreamGeometry();
        using (var g = hp.Open())
        {
            g.BeginFigure(new Point(xi - 8 * k, milieu - 3 * k), true, true);
            g.LineTo(new Point(xi - 4 * k, milieu - 3 * k), true, false);
            g.LineTo(new Point(xi + 1 * k, milieu - 8 * k), true, false);
            g.LineTo(new Point(xi + 1 * k, milieu + 8 * k), true, false);
            g.LineTo(new Point(xi - 4 * k, milieu + 3 * k), true, false);
            g.LineTo(new Point(xi - 8 * k, milieu + 3 * k), true, false);
        }
        hp.Freeze();
        dc.DrawGeometry(Blanc, null, hp);
        dc.DrawGeometry(null, new Pen(Blanc, 1.4 * k), Arc(new Point(xi + 2 * k, milieu), 6 * k));
        xi -= 34 * k;
        // Réseau : trois arcs.
        for (int i = 1; i <= 3; i++)
            dc.DrawGeometry(null, new Pen(Blanc, 1.6 * k), Arc(new Point(xi, milieu + 7 * k), 4.5 * k * i, -135, -45));
        dc.DrawEllipse(Blanc, null, new Point(xi, milieu + 6 * k), 1.6 * k, 1.6 * k);
        xi -= 34 * k;
        // L'icône de Pilou, avec un léger halo.
        var centre = new Point(xi, milieu);
        dc.DrawRoundedRectangle(B("#ffffff", 26), null, new Rect(xi - 15 * k, milieu - 15 * k, 30 * k, 30 * k), 5 * k, 5 * k);
        double ti = 22 * k;
        if (IconePilou is { } ic) dc.DrawImage(ic, new Rect(xi - ti / 2, milieu - ti / 2, ti, ti));
        else dc.DrawEllipse(Bleu, null, centre, ti / 2, ti / 2);
        Icone = centre;
        xi -= 30 * k;
        Ecrire(dc, "˄", TexteGras, 13 * k, Blanc, xi - 4 * k, milieu - 10 * k);
    }

    private static Geometry Arc(Point c, double r, double de = -60, double a = 60)
    {
        Point P(double deg) => new(c.X + r * Math.Cos(deg * Math.PI / 180), c.Y + r * Math.Sin(deg * Math.PI / 180));
        var g = new StreamGeometry();
        using (var s = g.Open())
        {
            s.BeginFigure(P(de), false, false);
            s.ArcTo(P(a), new Size(r, r), 0, false, SweepDirection.Clockwise, true, false);
        }
        g.Freeze();
        return g;
    }

    private static ImageSource? ChargerIcone()
    {
        try
        {
            using var flux = typeof(ToileDecor).Assembly.GetManifestResourceStream("pilou:icone.ico");
            if (flux is null) return null;
            var m = new MemoryStream();
            flux.CopyTo(m);
            m.Position = 0;
            var d = new IconBitmapDecoder(m, BitmapCreateOptions.PreservePixelFormat, BitmapCacheOption.OnLoad);
            var image = d.Frames.OrderByDescending(f => f.PixelWidth).First();
            image.Freeze();
            return image;
        }
        catch (Exception e) when (e is IOException or NotSupportedException or InvalidOperationException or FileFormatException)
        {
            return null;
        }
    }
}
