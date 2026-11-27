using System.Globalization;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;

namespace PilouBureau;

// Une épreuve de campagne dans la fenêtre Aventure : l'arène (400 × 200 unités, agrandie), dessinée en pixels nets,
// au-dessus du fil. La logique (Epreuves.cs) décide de tout ; ici on dessine, on transmet clics et touches, et on
// rend le résultat une fois l'animation de fin passée. Toujours possible : laisser faire les dés.
internal sealed class VueEpreuve : Border
{
    public const double K = 1.4; // unités de l'arène → unités WPF
    private const double Compte = 1500; // « prêt ? » avant le départ (ms)
    private const double Apres = 1400;  // le résultat reste affiché (ms)

    public event Action<bool, bool>? Fini; // réussi, aux dés
    public event Action? AuxDes;

    private readonly MiniJeu? _jeu;
    private readonly TirageDes? _des;
    private readonly Campagnes.Etat _etat;
    private readonly Arene _arene;
    private readonly System.Diagnostics.Stopwatch _chrono = System.Diagnostics.Stopwatch.StartNew();
    private bool _signale;

    private static Brush Gel(string hex) => FenetreAventure.Gel(hex);

    public VueEpreuve(MiniJeu? jeu, TirageDes? des, Campagnes.Etat etat)
    {
        _jeu = jeu;
        _des = des;
        _etat = etat;
        Background = new SolidColorBrush(Color.FromArgb(236, 15, 19, 36));
        var p = new StackPanel { HorizontalAlignment = HorizontalAlignment.Center, VerticalAlignment = VerticalAlignment.Center };
        string nom = jeu is null ? "LES DÉS" : Aventure.NomJeu(jeu.Jeu).ToUpperInvariant();
        var tete = new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Center, Margin = new Thickness(0, 0, 0, 6) };
        tete.Children.Add(new Pixels(Police.Texte($"ÉPREUVE · {nom}"), new Brush?[] { null, Bandeau.OrangePo }, Bandeau.Encre, 3));
        tete.Children.Add(new TextBlock
        {
            Text = "   " + Aventure.Pastilles(etat.Difficulte), Foreground = Bandeau.Violet, FontSize = 15, FontWeight = FontWeights.Bold,
            VerticalAlignment = VerticalAlignment.Center, FontFamily = new FontFamily("Segoe UI Symbol"),
        });
        p.Children.Add(tete);
        p.Children.Add(new TextBlock
        {
            Text = jeu is null ? $"Chance de réussir : {des!.Chance} %. Le dé décide." : Aventure.Consigne(jeu.Jeu),
            Foreground = Bandeau.Argent, FontSize = 12.5, FontFamily = new FontFamily("Segoe UI"), HorizontalAlignment = HorizontalAlignment.Center,
            Margin = new Thickness(0, 0, 0, 10),
        });
        _arene = new Arene(this) { Width = MiniJeu.ArenaL * K, Height = MiniJeu.ArenaH * K, Cursor = jeu is Visee ? Cursors.Cross : Cursors.Hand };
        _arene.MouseLeftButtonDown += (_, e) =>
        {
            e.Handled = true;
            var pt = e.GetPosition(_arene);
            Appuyer(pt.X / K, pt.Y / K);
        };
        p.Children.Add(new Border { BorderBrush = Bandeau.Bord, BorderThickness = new Thickness(3), Child = _arene, SnapsToDevicePixels = true });
        if (jeu is not null)
        {
            var des_ = new Button
            {
                Content = $"⚄ Laisser faire les dés ({etat.Chance} %)", Margin = new Thickness(0, 12, 0, 0), Padding = new Thickness(12, 5, 12, 5),
                HorizontalAlignment = HorizontalAlignment.Center, Background = Gel("#2a3156"), Foreground = Bandeau.ArgentClair, BorderBrush = Bandeau.Bord,
                BorderThickness = new Thickness(2), FontFamily = new FontFamily("Segoe UI"), FontWeight = FontWeights.SemiBold, Cursor = Cursors.Hand, Focusable = false,
            };
            des_.Click += (_, _) => { if (!_signale && !(_jeu?.Fini ?? false)) AuxDes?.Invoke(); };
            p.Children.Add(des_);
        }
        Child = p;
        Focusable = false;
    }

    // Temps du jeu (ms) : négatif pendant le « prêt ? ».
    private double T => _chrono.Elapsed.TotalMilliseconds - Compte;

    private void Appuyer(double x, double y)
    {
        if (_jeu is null || T < 0 || _jeu.Fini) return;
        if (_jeu is Memoire)
        {
            int i = Arene.Pave(x, y);
            if (i >= 0) _jeu.Appuyer(T, touche: i);
        }
        else if (_jeu is Visee) _jeu.Appuyer(T, x, y);
        else _jeu.Appuyer(T);
    }

    // Une touche : Espace ou Entrée (appuyer), 1 à 4 (mémoire), Échap (laisser faire les dés). Rend si elle est prise.
    public bool Touche(Key k)
    {
        if (k == Key.Escape)
        {
            if (_jeu is not null && !_jeu.Fini && !_signale) AuxDes?.Invoke();
            return true;
        }
        if (_jeu is null || T < 0 || _jeu.Fini) return k is Key.Space or Key.Enter;
        int n = k switch { Key.D1 or Key.NumPad1 => 0, Key.D2 or Key.NumPad2 => 1, Key.D3 or Key.NumPad3 => 2, Key.D4 or Key.NumPad4 => 3, _ => -1 };
        if (_jeu is Memoire && n >= 0)
        {
            _jeu.Appuyer(T, touche: n);
            return true;
        }
        if (k is Key.Space or Key.Enter)
        {
            _jeu.Appuyer(T);
            return true;
        }
        return false;
    }

    public void Animer()
    {
        double t = T;
        if (_jeu is not null && t >= 0)
        {
            _jeu.Avancer(t);
            if (_jeu.Fini && t - _jeu.FiniA > Apres && !_signale)
            {
                _signale = true;
                Fini?.Invoke(_jeu.Reussi, false);
            }
        }
        else if (_des is not null && t > TirageDes.Duree + Apres && !_signale)
        {
            _signale = true;
            Fini?.Invoke(_des.Reussi, true);
        }
        _arene.InvalidateVisual();
    }

    // ---- Le dessin

    private sealed class Arene : FrameworkElement
    {
        private readonly VueEpreuve _v;
        private static readonly Brush Nuit = Gel("#0d1022"), Nuit2 = Gel("#151a2e"), Ligne = Gel("#2d333b"), Or = Gel(Aventure.Or), Orange = Bandeau.OrangePo,
            Bleu = Bandeau.BleuXp, Violet = Bandeau.Violet, Creme = Gel("#fff6e0"), Ardoise = Gel(Aventure.Ardoise), Encre = Bandeau.Encre;
        private static readonly Brush[] Paves = { Bandeau.OrangePo, Bandeau.BleuXp, Bandeau.Violet, Gel(Aventure.Creme) };

        public Arene(VueEpreuve v)
        {
            _v = v;
            SnapsToDevicePixels = true;
            RenderOptions.SetEdgeMode(this, EdgeMode.Aliased);
        }

        // Pavé de la mémoire sous (x, y) (unités de l'arène), -1 : aucun.
        public static int Pave(double x, double y)
        {
            for (int i = 0; i < 4; i++)
            {
                var (px, py, s) = PaveA(i);
                if (x >= px && x <= px + s && y >= py && y <= py + s) return i;
            }
            return -1;
        }

        private static (double X, double Y, double S) PaveA(int i) => (38 + i * 84, 58, 70);

        private static void Carre(DrawingContext dc, Brush b, double x, double y, double w, double h) =>
            dc.DrawRectangle(b, null, new Rect(Math.Round(x * K), Math.Round(y * K), Math.Round(w * K), Math.Round(h * K)));

        private void Ecrire(DrawingContext dc, string s, double x, double y, double taille, Brush b, bool centre = true, string police = "Segoe UI", bool gras = true)
        {
            var ft = new FormattedText(s, CultureInfo.CurrentCulture, FlowDirection.LeftToRight,
                new Typeface(new FontFamily(police), FontStyles.Normal, gras ? FontWeights.Bold : FontWeights.Normal, FontStretches.Normal), taille, b,
                VisualTreeHelper.GetDpi(this).PixelsPerDip);
            dc.DrawText(ft, new Point(Math.Round(x * K - (centre ? ft.Width / 2 : 0)), Math.Round(y * K - ft.Height / 2)));
        }

        // Texte en police pixel (3 × 5), centré.
        private static void Pixel(DrawingContext dc, string s, double x, double y, double cellule, Brush b, Brush? contour = null)
        {
            var m = Police.Texte(s.ToUpperInvariant());
            int h = m.GetLength(0), w = m.GetLength(1);
            double x0 = Math.Round(x * K - w * cellule / 2), y0 = Math.Round(y * K - h * cellule / 2);
            if (contour is not null)
                for (int r = 0; r < h; r++)
                for (int c = 0; c < w; c++)
                    if (m[r, c] != 0) dc.DrawRectangle(contour, null, new Rect(x0 + (c - 1) * cellule, y0 + (r - 1) * cellule, cellule * 3, cellule * 3));
            for (int r = 0; r < h; r++)
            for (int c = 0; c < w; c++)
                if (m[r, c] != 0) dc.DrawRectangle(b, null, new Rect(x0 + c * cellule, y0 + r * cellule, cellule, cellule));
        }

        protected override void OnRender(DrawingContext dc)
        {
            try
            {
                Dessiner(dc);
            }
            catch (Exception e) when (e is not OutOfMemoryException)
            {
                System.Diagnostics.Debug.WriteLine($"VueEpreuve : {e}");
            }
        }

        private void Dessiner(DrawingContext dc)
        {
            double t = _v.T;
            Carre(dc, Nuit, 0, 0, MiniJeu.ArenaL, MiniJeu.ArenaH);
            for (int i = 0; i < 18; i++) Carre(dc, Nuit2, (i * 53 + 17) % 400, (i * 37 + 11) % 120, 2, 2);
            var jeu = _v._jeu;
            // Le temps qui reste, en cases, en haut.
            if (jeu is not null)
            {
                double reste = Math.Clamp(1 - Math.Max(0, t) / jeu.Limite, 0, 1);
                int n = 40, pleines = (int)Math.Ceiling(reste * n);
                for (int i = 0; i < n; i++) Carre(dc, i < pleines ? Bleu : Ligne, 10 + i * 9.5, 6, 7.5, 4);
            }
            switch (jeu)
            {
                case Reflexe r:
                    DessinerReflexe(dc, r, t);
                    break;
                case Memoire m:
                    DessinerMemoire(dc, m, t);
                    break;
                case Rythme y:
                    DessinerRythme(dc, y, t);
                    break;
                case Visee v:
                    DessinerVisee(dc, v, t);
                    break;
                default:
                    if (_v._des is { } d) DessinerDes(dc, d, t);
                    break;
            }
            if (t < 0) Bandeau_(dc, t > -700 ? "PARTEZ !" : "PRÊT ?", Orange);
            else if (jeu is { Fini: true }) Bandeau_(dc, jeu.Reussi ? "RÉUSSI !" : "RATÉ…", jeu.Reussi ? Or : Violet);
            else if (jeu is not null && jeu.Message != "" && t - jeu.MessageT < 900)
                Ecrire(dc, jeu.Message, 200, 186, 13, Creme);
        }

        private void Bandeau_(DrawingContext dc, string texte, Brush b)
        {
            Carre(dc, new SolidColorBrush(Color.FromArgb(200, 10, 13, 26)), 0, 78, 400, 44);
            Pixel(dc, texte.Replace("…", "..."), 200, 100, 6, b, Encre);
        }

        // Une étoile pixel (motif 9 × 9).
        private static readonly string[] Etoile =
        {
            "....#....", "....#....", "...###...", "#########", ".#######.", "..#####..", ".###.###.", ".##...##.", "#.......#",
        };

        private static void Motif(DrawingContext dc, string[] motif, double cx, double cy, double cellule, Brush b)
        {
            int h = motif.Length, w = motif[0].Length;
            for (int r = 0; r < h; r++)
            for (int c = 0; c < w; c++)
                if (motif[r][c] == '#') Carre(dc, b, cx + (c - w / 2.0) * cellule, cy + (r - h / 2.0) * cellule, cellule, cellule);
        }

        private void DessinerReflexe(DrawingContext dc, Reflexe r, double t)
        {
            bool allume = r.Phase == Reflexe.Etape.Allume;
            if (allume)
            {
                // Halo : trois carrés concentriques qui respirent.
                double k = 1 + 0.08 * Math.Sin(t / 60);
                for (int i = 3; i >= 1; i--)
                {
                    var halo = new SolidColorBrush(Color.FromArgb((byte)(28 * i), 0xf5, 0xd7, 0x6e));
                    Carre(dc, halo, 200 - 22 * i * k, 92 - 22 * i * k, 44 * i * k, 44 * i * k);
                }
            }
            Motif(dc, Etoile, 200, 92, 8, allume ? Or : (int)(t / 700) % 2 == 0 ? Ligne : Gel("#3b4654"));
            for (int i = 0; i < Reflexe.Manches; i++)
            {
                double x = 200 - (Reflexe.Manches - 1) * 15 + i * 30;
                if (i < r.Manche)
                {
                    bool touche = i < r.Touches + r.Ratees && TouchesAvant(r, i);
                    if (touche) Motif(dc, Losange, x, 160, 2.4, Orange);
                    else Ecrire(dc, "✕", x, 160, 15, Ardoise, police: "Segoe UI Symbol");
                }
                else Contour(dc, x - 7, 153, 14, 14, Ligne);
            }
            Ecrire(dc, $"il en faut {r.Besoin} sur {Reflexe.Manches}", 200, 26, 11.5, Gel("#adbac7"), gras: false);
        }

        // L'ordre exact des manches n'est pas gardé : les réussites d'abord (ce qui compte, c'est le nombre).
        private static bool TouchesAvant(Reflexe r, int i) => i < r.Touches;

        private static readonly string[] Losange = { "..#..", ".###.", "#####", ".###.", "..#.." };

        private static void Contour(DrawingContext dc, double x, double y, double w, double h, Brush b)
        {
            Carre(dc, b, x, y, w, 1.5);
            Carre(dc, b, x, y + h - 1.5, w, 1.5);
            Carre(dc, b, x, y, 1.5, h);
            Carre(dc, b, x + w - 1.5, y, 1.5, h);
        }

        private void DessinerMemoire(DrawingContext dc, Memoire m, double t)
        {
            int allume = m.SigneAllume(t);
            for (int i = 0; i < 4; i++)
            {
                var (x, y, s) = PaveA(i);
                bool vif = allume == i || (m.DernierAppui == i && t - m.DernierAppuiT < 240);
                Carre(dc, Gel("#0a0d1a"), x + 3, y + 3, s, s);
                var fond = Paves[i];
                if (!vif) fond = new SolidColorBrush(Color.FromArgb(70, ((SolidColorBrush)Paves[i]).Color.R, ((SolidColorBrush)Paves[i]).Color.G, ((SolidColorBrush)Paves[i]).Color.B));
                Carre(dc, fond, x + (vif ? 0 : 1), y + (vif ? 0 : 1), s, s);
                Contour(dc, x, y, s, s, vif ? Creme : Ligne);
                Ecrire(dc, Memoire.Signes[i], x + s / 2, y + s / 2, 30, vif ? Encre : Gel("#adbac7"), police: "Segoe UI Symbol");
                Pixel(dc, (i + 1).ToString(CultureInfo.InvariantCulture), x + s / 2, y + s + 12, 2.4, Gel("#768390"));
            }
            string etape = m.Phase == Memoire.Etape.Montre ? "REGARDE..." : "À TOI !";
            Pixel(dc, etape, 200, 34, 3, m.Phase == Memoire.Etape.Montre ? Bleu : Orange, Encre);
            for (int i = 0; i < m.Suite.Count; i++)
            {
                double x = 200 - (m.Suite.Count - 1) * 9 + i * 18;
                if (m.Phase == Memoire.Etape.Repete && i < m.Touches) Motif(dc, Losange, x, 168, 2, Orange);
                else Contour(dc, x - 5, 163, 10, 10, Ligne);
            }
            if (m.Chances > 1 && m.Phase == Memoire.Etape.Montre) Ecrire(dc, "une seconde chance si tu te trompes", 200, 186, 10.5, Gel("#768390"), gras: false);
        }

        private void DessinerRythme(DrawingContext dc, Rythme y, double t)
        {
            const double ligne = 70, vitesse = 0.12, haut = 72, h = 56;
            Carre(dc, Nuit2, 0, haut, 400, h);
            for (int x = 0; x < 400; x += 20) Carre(dc, Ligne, x - (t * vitesse) % 20 + 20, haut + h / 2, 8, 1.5);
            Carre(dc, Orange, ligne - 2, haut - 6, 4, h + 12);
            for (int i = 0; i < Rythme.Notes; i++)
            {
                double x = ligne + (y.Temps[i] - t) * vitesse;
                if (x < -20 || x > 420) continue;
                var etat = y.Jugees[i];
                if (etat == true)
                {
                    double d = t - y.Temps[i];
                    if (d < 320) Motif(dc, Losange, ligne, haut + h / 2, 2.4 + d / 40, new SolidColorBrush(Color.FromArgb((byte)Math.Max(0, 255 - d * 0.8), 0xf5, 0xd7, 0x6e)));
                    continue;
                }
                Motif(dc, Losange, x, haut + h / 2, 4, etat == false ? Ardoise : Bleu);
            }
            Ecrire(dc, $"♪ {y.Touches} / {y.Besoin}", 200, 36, 15, Creme);
        }

        private void DessinerVisee(DrawingContext dc, Visee v, double t)
        {
            // Le pré, la nuit : quelques herbes en bas.
            for (int x = 0; x < 400; x += 6) Carre(dc, Gel("#16365e"), x, 186 - (x * 7 % 9), 3, 20);
            // Le viseur du clavier, au centre.
            Contour(dc, 200 - v.Rayon * 1.3, 100 - v.Rayon * 1.3, v.Rayon * 2.6, v.Rayon * 2.6, Ligne);
            Carre(dc, Ligne, 199, 92, 2, 16);
            Carre(dc, Ligne, 192, 99, 16, 2);
            var (lx, ly) = v.Position(Math.Max(0, t));
            // La luciole : halo, ailes qui battent, cœur.
            for (int i = 3; i >= 1; i--)
                Carre(dc, new SolidColorBrush(Color.FromArgb((byte)(22 * i), 0xf5, 0xd7, 0x6e)), lx - v.Rayon * i / 2.2, ly - v.Rayon * i / 2.2, v.Rayon * i / 1.1, v.Rayon * i / 1.1);
            bool aile = (int)(t / 90) % 2 == 0;
            Carre(dc, Gel("#b4dbff"), lx - 9, ly - (aile ? 9 : 6), 6, aile ? 6 : 4);
            Carre(dc, Gel("#b4dbff"), lx + 3, ly - (aile ? 9 : 6), 6, aile ? 6 : 4);
            Carre(dc, Or, lx - 4, ly - 4, 8, 8);
            Carre(dc, Creme, lx - 2, ly - 2, 4, 4);
            if (t - v.DernierTir < 300)
            {
                double k = (t - v.DernierTir) / 300;
                Contour(dc, v.DernierPoint.X - 6 - 10 * k, v.DernierPoint.Y - 6 - 10 * k, 12 + 20 * k, 12 + 20 * k, Orange);
            }
            Ecrire(dc, $"◎ {v.Touches} / {v.Besoin}", 200, 26, 14, Creme);
        }

        private void DessinerDes(DrawingContext dc, TirageDes d, double t)
        {
            int valeur = t < 0 ? 0 : d.Valeur(t);
            bool fini = d.Fini(Math.Max(0, t));
            // Le dé : un gros carré à coins coupés, le nombre au centre.
            double x = 140, y = 34, s = 120;
            Carre(dc, Gel("#0a0d1a"), x + 4, y + 4, s, s);
            Carre(dc, Creme, x + 6, y, s - 12, s);
            Carre(dc, Creme, x, y + 6, s, s - 12);
            Ecrire(dc, valeur == 0 ? "?" : valeur.ToString(CultureInfo.InvariantCulture), x + s / 2, y + s / 2, 54, Encre, police: "Consolas");
            // La jauge de chance : la part qui réussit en bleu, le reste en ardoise ; le tirage s'y pose.
            double gx = 30, gy = 172, gw = 340;
            Carre(dc, Bleu, gx, gy, gw * d.Chance / 100.0, 8);
            Carre(dc, Ligne, gx + gw * d.Chance / 100.0, gy, gw * (100 - d.Chance) / 100.0, 8);
            Ecrire(dc, $"≤ {d.Chance} : réussi", gx + gw * d.Chance / 200.0, gy - 10, 10.5, Bleu, gras: false);
            if (fini)
            {
                double vx = gx + gw * (d.Final - 0.5) / 100.0;
                Carre(dc, d.Reussi ? Or : Violet, vx - 2, gy - 4, 4, 16);
            }
        }
    }
}
