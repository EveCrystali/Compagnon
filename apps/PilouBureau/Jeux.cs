using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Shapes;

namespace PilouBureau;

// Petites activités avec Pilou : deux ou trois clics, quelques secondes, jamais bloquantes.
// Chaque gain s'affiche (« +10 xp ») et part au mod par ~/.claude/compagnon/bonus.txt
// (total cumulé), qui l'ajoute à l'XP partagée. Les niveaux débloquent des accessoires.
public sealed partial class FenetrePilou
{
    private enum Jeu { Aucun, Etoile, Bulles, TapeCinq }

    private sealed class BulleSavon
    {
        public Pixels Forme = null!;
        public double Nee, X0, Phase;
        public bool Eclatee;
    }

    private sealed class Flottant
    {
        public Pixels Texte = null!;
        public double Ne, X, Y;
    }

    private readonly Canvas _jeu = new();
    private Jeu _jeuEnCours = Jeu.Aucun;
    private double _jeuDebut, _prochainJeu = 4 * 60_000;
    private Pixels? _etoile;
    private Point _etoilePos;
    private Pixels? _main;
    private readonly List<BulleSavon> _bullesJeu = new();
    private int _bullesEclatees;
    private readonly List<Flottant> _flottants = new();
    private int _xpEnAttente;          // gagnée ici, pas encore revenue dans l'état publié
    private int _dernierXp = -1, _dernierNiveau = -1;
    private bool _dortBureau;

    private static readonly Brush OrangeJeu = Geler(Color.FromRgb(0xf6, 0x9d, 0x50));
    private static readonly Brush OrangeClair = Geler(Color.FromRgb(0xff, 0xd8, 0xb0));
    private static readonly Brush BulleFond = Geler(Color.FromArgb(0x55, 0x6c, 0xb6, 0xff));
    private static readonly Brush Blanc = Geler(Colors.White);
    private static readonly Brush ContourXp = Geler(Color.FromRgb(0x1c, 0x21, 0x28));

    // Motifs des jeux, au pixel de Pilou (4 unités).
    private static readonly int[,] MotifEtoile = Pixels.Motif(
        "0001000", "0001000", "0012100", "1112111", "0122210", "0012100", "0110110", "0100010");
    private static readonly int[,] MotifEtoile2 = Pixels.Motif(
        "0001000", "0001000", "0013100", "1113111", "0133310", "0013100", "0110110", "0100010");
    private static readonly int[,] MotifBulle = Pixels.Motif(
        "001110", "012221", "123222", "122222", "122222", "012220", "001100");
    private static readonly int[,] MotifMain = Pixels.Motif(
        "01010100", "01010100", "01010101", "01111101", "11111111", "01111110", "00111110", "00111100");
    private static readonly Brush BleuClair = Geler(Color.FromRgb(0xb4, 0xdb, 0xff));
    private static readonly Brush ContourBleu = Geler(Color.FromRgb(0x1f, 0x4f, 0x8a));
    private static readonly Brush Creme = Geler(Color.FromRgb(0xf6, 0xf8, 0xfa));

    private static Brush Geler(Color c)
    {
        var b = new SolidColorBrush(c);
        b.Freeze();
        return b;
    }

    // Repères dans la fenêtre (unités avant mise à l'échelle) : sommet de la tête de Pilou.
    private double TeteX => _aGauche ? Scene.Largeur / 2 : LargeurBase - Scene.Largeur / 2;
    private double TeteY => HauteurBulle + Scene.Sol - 15 * Scene.PA;
    private int Niveau => Math.Max(1, _suivi.Courant?.Niveau ?? 1);

    private void InitialiserJeux()
    {
        Grid.SetRowSpan(_jeu, 2);
        _racine.Children.Add(_jeu);
    }

    // Essai (--essai=<nom>) : déclenche tout de suite un jeu ou un état, pour les rendus de contrôle.
    public void Essai(string nom)
    {
        var t = Maintenant;
        switch (nom)
        {
            case "etoile": Demarrer(Jeu.Etoile, t); break;
            case "bulles": Demarrer(Jeu.Bulles, t - 1800); break;
            case "tape": Demarrer(Jeu.TapeCinq, t); break;
            case "etourdi": _etourdiJusque = t + 6000; Dire("ouh, la tête me tourne…", 5000); break;
            case "niveau": Flotter("+10 xp"); Flotter("NIVEAU 5", 1.6, new Point(TeteX - 50, TeteY - 70)); Dire("niveau 5 ! nouveau : lunettes de soleil", 5000); break;
        }
    }

    // ---- Niveaux et XP

    // Appelé à chaque lecture : XP gagnée ailleurs (tour fini, commit, caresse) et montée de niveau.
    private void SuivreXp()
    {
        if (_suivi.Courant is not { } c) return;
        if (_dernierXp >= 0 && c.Xp > _dernierXp)
        {
            int gain = c.Xp - _dernierXp;
            int deja = Math.Min(gain, _xpEnAttente);
            _xpEnAttente -= deja;
            if (gain - deja > 0) Flotter($"+{gain - deja} xp");
        }
        if (c.Xp > _dernierXp) _dernierXp = c.Xp;
        if (_dernierNiveau > 0 && c.Niveau > _dernierNiveau)
        {
            var debloque = Enum.GetValues<Accessoire>().Where(a => Reglages.Requis(a) == c.Niveau).ToList();
            Dire(debloque.Count > 0 ? $"niveau {c.Niveau} ! nouveau : {Nom(debloque[0]).ToLowerInvariant()}" : $"niveau {c.Niveau} !", 5000);
            Flotter($"NIVEAU {c.Niveau}", 1.6);
            _salueJusque = Maintenant + 2500;
            _tSaut = Maintenant;
        }
        if (c.Niveau > _dernierNiveau) _dernierNiveau = c.Niveau;
    }

    private static string Nom(Accessoire a) => a switch
    {
        Accessoire.Bonnet => "Bonnet de laine",
        Accessoire.Casque => "Casque audio",
        Accessoire.Noeud => "Nœud papillon",
        Accessoire.Feuille => "Feuille d'automne",
        Accessoire.Lunettes => "Lunettes de soleil",
        Accessoire.Couronne => "Couronne",
        Accessoire.Aucun => "Aucun",
        _ => "Selon la saison",
    };

    private void Gagner(int xp, Point ou)
    {
        _xpEnAttente += xp;
        Flotter($"+{xp} xp", 1, ou);
        try
        {
            Directory.CreateDirectory(_dossier);
            var chemin = System.IO.Path.Combine(_dossier, "bonus.txt");
            int total = File.Exists(chemin) && int.TryParse(File.ReadAllText(chemin).Trim(), out var v) ? v : 0;
            File.WriteAllText(chemin, (total + xp).ToString());
        }
        catch (IOException)
        {
            // le gain reste affiché, il sera perdu pour l'XP partagée
        }
    }

    // « +10 xp » qui monte et s'efface au-dessus de la tête (ou d'un point donné).
    private void Flotter(string texte, double taille = 1, Point? ou = null)
    {
        var tb = new Pixels(Pixels.Texte(texte), new Brush?[] { null, OrangeJeu }, ContourXp, taille >= 1.5 ? 3 : 2) { IsHitTestVisible = false };
        var p = ou ?? new Point(TeteX - 18, TeteY - 10);
        _jeu.Children.Add(tb);
        _flottants.Add(new Flottant { Texte = tb, Ne = Maintenant, X = p.X, Y = p.Y });
    }

    // ---- Sommeil de bureau

    // Personne au clavier depuis 10 min et rien qui tourne : il s'endort. Le premier geste le réveille.
    private Expr Sommeil(Expr expr, double t)
    {
        bool personne = _inactif > 10 * 60_000 && !_vivantes.Any(e => e.EnTour || e.Attente != "");
        if (personne && !_dortBureau)
        {
            _dortBureau = true;
            Arreter("");
        }
        if (_dortBureau && _inactif < 2500)
        {
            _dortBureau = false;
            _tSaut = t;
            Dire("bien dormi !", 2500);
        }
        return _dortBureau && expr is Expr.Repos or Expr.Inquiet ? Expr.Dort : expr;
    }

    // ---- Activités

    private void ProposerJeu(double t, Expr expr)
    {
        if (!_reglages.Jeux || _jeuEnCours != Jeu.Aucun || t < _prochainJeu) return;
        if (expr is not Expr.Repos || _dortBureau || _inactif > 60_000 || _geste == Geste.SauteSouris || _attrape) return;
        _prochainJeu = t + (8 + _hasard.NextDouble() * 8) * 60_000;
        Demarrer((Jeu)(1 + _hasard.Next(3)), t);
    }

    private void Demarrer(Jeu jeu, double t)
    {
        Arreter("");
        _jeuEnCours = jeu;
        _jeuDebut = t;
        _geste = Geste.Rien;
        switch (jeu)
        {
            case Jeu.Etoile:
                _etoile = new Pixels(MotifEtoile, new Brush?[] { null, OrangeJeu, OrangeClair, Blanc }, ContourXp) { Cursor = Cursors.Hand };
                _etoilePos = new Point(Math.Clamp(TeteX + (_hasard.NextDouble() * 2 - 1) * 120, 16, LargeurBase - 40), 24 + _hasard.NextDouble() * 70);
                _etoile.MouseLeftButtonDown += (_, e) =>
                {
                    Gagner(10, _etoilePos);
                    Arreter("bien vu !");
                    _salueJusque = Maintenant + 1500;
                    e.Handled = true;
                };
                _jeu.Children.Add(_etoile);
                Dire("une étoile filante ! attrape-la", 2600);
                break;
            case Jeu.Bulles:
                _bullesEclatees = 0;
                for (int i = 0; i < 3; i++)
                {
                    var b = new BulleSavon
                    {
                        Forme = new Pixels(MotifBulle, new Brush?[] { null, Creme, BulleFond, Blanc }, null) { Cursor = Cursors.Hand },
                        Nee = t + i * 450,
                        X0 = TeteX + (i - 1) * 34,
                        Phase = _hasard.NextDouble() * 6,
                    };
                    b.Forme.MouseLeftButtonDown += (_, e) =>
                    {
                        if (b.Eclatee) return;
                        b.Eclatee = true;
                        _bullesEclatees++;
                        var ou = new Point(Canvas.GetLeft(b.Forme), Canvas.GetTop(b.Forme));
                        _jeu.Children.Remove(b.Forme);
                        Gagner(5, ou);
                        if (_bullesEclatees == 3)
                        {
                            Gagner(5, new Point(TeteX - 30, TeteY - 40));
                            Arreter("toutes ! bonus");
                            _salueJusque = Maintenant + 1500;
                        }
                        e.Handled = true;
                    };
                    b.Forme.Visibility = Visibility.Hidden;
                    _bullesJeu.Add(b);
                    _jeu.Children.Add(b.Forme);
                }
                Dire("pop les bulles !", 2400);
                break;
            case Jeu.TapeCinq:
                _main = new Pixels(MotifMain, new Brush?[] { null, Creme }, ContourBleu) { Cursor = Cursors.Hand };
                _main.MouseLeftButtonDown += (_, e) =>
                {
                    Gagner(10, new Point(TeteX - 18, TeteY - 30));
                    Arreter("ouais !");
                    _salueJusque = Maintenant + 1800;
                    _tSaut = Maintenant;
                    e.Handled = true;
                };
                _jeu.Children.Add(_main);
                Dire("tape m'en cinq !", 2600);
                break;
        }
    }

    private void Arreter(string mot)
    {
        if (_etoile is not null) _jeu.Children.Remove(_etoile);
        if (_main is not null) _jeu.Children.Remove(_main);
        foreach (var b in _bullesJeu) _jeu.Children.Remove(b.Forme);
        _etoile = null;
        _main = null;
        _bullesJeu.Clear();
        _jeuEnCours = Jeu.Aucun;
        if (mot != "") Dire(mot, 1800);
    }

    private static System.Windows.Shapes.Path EtoileVectorielle()
    {
        var g = new StreamGeometry();
        using (var c = g.Open())
        {
            for (int i = 0; i < 10; i++)
            {
                double a = -Math.PI / 2 + i * Math.PI / 5, r = i % 2 == 0 ? 13 : 5.5;
                var pt = new Point(13 + Math.Cos(a) * r, 13 + Math.Sin(a) * r);
                if (i == 0) c.BeginFigure(pt, true, true);
                else c.LineTo(pt, true, false);
            }
        }
        g.Freeze();
        return new System.Windows.Shapes.Path
        {
            Data = g,
            Fill = OrangeJeu,
            Stroke = OrangeClair,
            StrokeThickness = 1.5,
            Cursor = Cursors.Hand,
            RenderTransformOrigin = new Point(0.5, 0.5),
            RenderTransform = new RotateTransform(),
        };
    }

    // Une image : positions, délais, fin des jeux, XP qui flotte.
    private void AnimerJeux(double t)
    {
        var age = t - _jeuDebut;
        switch (_jeuEnCours)
        {
            case Jeu.Etoile when _etoile is not null:
                if (age > 9000)
                {
                    Arreter("trop tard, elle est partie…");
                    break;
                }
                // Alignée sur la grille de pixels ; elle scintille au lieu de tourner.
                Canvas.SetLeft(_etoile, Math.Round((_etoilePos.X + Math.Sin(t / 400) * 6) / 4) * 4);
                Canvas.SetTop(_etoile, Math.Round((_etoilePos.Y + Math.Cos(t / 520) * 4) / 4) * 4);
                _etoile.Changer((int)(t / 220) % 2 == 0 ? MotifEtoile : MotifEtoile2);
                _etoile.Opacity = age > 7500 ? (9000 - age) / 1500 : 1;
                break;
            case Jeu.Bulles:
            {
                bool restent = false;
                foreach (var b in _bullesJeu)
                {
                    if (b.Eclatee) continue;
                    double vie = t - b.Nee;
                    if (vie < 0) continue;
                    double y = TeteY - 10 - vie / 1000 * 22;
                    if (y < -30) { b.Eclatee = true; _jeu.Children.Remove(b.Forme); continue; }
                    restent = true;
                    b.Forme.Visibility = Visibility.Visible;
                    Canvas.SetLeft(b.Forme, Math.Round((b.X0 - 16 + Math.Sin(vie / 600 + b.Phase) * 14) / 4) * 4);
                    Canvas.SetTop(b.Forme, Math.Round(y / 4) * 4);
                }
                if (!restent && age > 1500) Arreter(_bullesEclatees > 0 ? "" : "plus de bulles…");
                break;
            }
            case Jeu.TapeCinq when _main is not null:
                if (age > 4500)
                {
                    Arreter("bon… plus tard");
                    break;
                }
                // Elle s'agite d'un pixel, au lieu de grossir (le pixel reste net).
                _main.Palette = new Brush?[] { null, (int)(t / 250) % 2 == 0 ? Creme : OrangeClair };
                // À côté de sa tête, du côté où il y a de la place dans la fenêtre.
                Canvas.SetLeft(_main, _aGauche ? TeteX + 34 : TeteX - 70);
                Canvas.SetTop(_main, TeteY - 6 + ((int)(t / 200) % 2) * 4);
                if ((int)(age / 900) != (int)((age - 33) / 900)) _tSaut = t;
                break;
        }

        for (int i = _flottants.Count - 1; i >= 0; i--)
        {
            var f = _flottants[i];
            double k = (t - f.Ne) / 1400;
            if (k >= 1)
            {
                _jeu.Children.Remove(f.Texte);
                _flottants.RemoveAt(i);
                continue;
            }
            Canvas.SetLeft(f.Texte, f.X);
            Canvas.SetTop(f.Texte, f.Y - k * 38);
            f.Texte.Opacity = k < 0.7 ? 1 : (1 - k) / 0.3;
        }
    }
}
