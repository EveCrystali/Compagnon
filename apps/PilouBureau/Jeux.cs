using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Shapes;

namespace PilouBureau;

// Petites activités avec Pilou : deux ou trois clics, quelques secondes, jamais bloquantes.
// Chaque gain s'affiche (« +10 xp ») et s'ajoute au profil de ce PC (Profil.cs), partagé entre PC
// via le dossier de partage. Les niveaux débloquent les récompenses (Recompenses.cs).
public sealed partial class FenetrePilou
{
    private enum Jeu { Aucun, Etoile, Bulles, TapeCinq, Peche, Cuisine }

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
    private Profil _profil = new();
    private int _xpTotal;              // tous les PC du dossier de partage
    private int _dernierNiveau = -1;
    private double _totalLu = -1e9;
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

    private static Pixels Cliquable(Pixels p)
    {
        p.Cursor = Cursors.Hand;
        return p;
    }

    private static Brush Geler(Color c)
    {
        var b = new SolidColorBrush(c);
        b.Freeze();
        return b;
    }

    // Repères dans la fenêtre (unités avant mise à l'échelle) : sommet de la tête de Pilou.
    private double TeteX => _aGauche ? Scene.Largeur / 2 : LargeurBase - Scene.Largeur / 2;
    private double TeteY => HauteurBulle + Scene.Sol - 15 * Scene.PA;
    // Courbe actuelle, jamais sous le plus haut niveau acquis (de cet appareil et du groupe).
    private int Niveau => Acces.Niveau(_xpTotal, NiveauAcquisGroupe());
    private string DossierPartage => _reglages.Partage(_dossier);

    private void InitialiserJeux()
    {
        _profil = Profil.Lire(DossierPartage);
        _xpTotal = TotalXp();
        // Anciennes récompenses gratuites → inventaire, niveau acquis (rien de ce qui était acquis n'est perdu).
        if (_profil.Evolution.Migre < 1)
        {
            Migration.Appliquer(_profil, _xpTotal, _reglages);
            _profil.Ecrire(DossierPartage);
        }
        _dernierNiveau = Niveau;
        Grid.SetRowSpan(_jeu, 2);
        _racine.Children.Add(_jeu);
    }

    // Essai (--essai=<nom>) : déclenche tout de suite un jeu ou un état, pour les rendus de contrôle.
    // Rendus de contrôle : stade, tenue ou objet imposés (--essai=stade:3, --essai=tenue:code, --essai=objet:cape).
    private int _essaiStade;
    private string _essaiTenue = "", _essaiObjet = "";

    private IReadOnlyDictionary<string, string> EquipeEssai(IReadOnlyDictionary<string, string> equipe)
    {
        if (_essaiObjet == "") return equipe;
        var d = new Dictionary<string, string>(equipe);
        var slot = Banque.Commune[_essaiObjet]?.Slot ?? "objet";
        d[_essaiObjet is "lavande" or "corail-orange" or "ardoise" or "sable" or "glacier" ? PilouBureau.Boutique.Couleur : slot] = _essaiObjet;
        return d;
    }

    public void Essai(string nom)
    {
        var t = Maintenant;
        if (nom.StartsWith("stade:") && int.TryParse(nom[6..], out var st)) _essaiStade = Math.Clamp(st, 1, 4);
        if (nom.StartsWith("tenue:")) _essaiTenue = nom[6..];
        if (nom.StartsWith("objet:")) _essaiObjet = nom[6..];
        if (nom.StartsWith("soins:")) EssaiSoins(nom[6..]);
        // --essai=visite:depart|arrivee|jeu|retour : une visite chez un ami « Léo », sans réseau.
        if (nom.StartsWith("visite:")) EssaiVisite(nom[7..]);
        // --essai=meteo:pluie, meteo:pluie:parapluie, meteo:neige, meteo:chaleur, meteo:orage…
        if (nom.StartsWith("meteo:"))
        {
            var parts = nom[6..].Split(':');
            _essaiMeteo = parts[0];
            if (parts.Length > 1) _essaiObjet = parts[1];
        }
        if (nom == "evolution")
        {
            _essaiStade = 0;
            DemarrerEvolution(Math.Min(4, StadeAffiche() + 1));
        }
        switch (nom)
        {
            case "etoile": Demarrer(Jeu.Etoile, t); break;
            case "bulles": Demarrer(Jeu.Bulles, t - 1800); break;
            case "tape": Demarrer(Jeu.TapeCinq, t); break;
            case "etourdi": _etourdiJusque = t + 6000; Dire("ouh, la tête me tourne…", 5000); break;
            case "peche": Demarrer(Jeu.Peche, t); break;
            case "mord":
                Demarrer(Jeu.Peche, t - 800);
                _mordA = t + 250;
                break;
            case "prise":
                Demarrer(Jeu.Peche, t);
                FinPeche(Butin.Prises[^1], false, t);
                break;
            case "cuisine":
                if (!Butin.PeutCuisiner(_profil.Stock)) _profil.Stock["goujon"] = 2;
                Demarrer(Jeu.Cuisine, t - 3000);
                break;
            case "niveau": Flotter("+10 xp"); Flotter("NIVEAU 5", 1.6, new Point(TeteX - 50, TeteY - 70)); Dire("niveau 5 ! nouveau : lunettes de soleil", 5000); break;
        }
    }

    // ---- Niveaux et XP

    // Appelé à chaque lecture : XP venue de Claude (tours finis, commits, caresses), XP des autres PC.
    private void SuivreXp()
    {
        // L'XP du mod vient d'une session Claude (toutes portent la même) ; les autres sources sont créditées à part.
        var claude = _vivantes.Where(e => e.Claude).MaxBy(e => e.T);
        if (claude is { } c)
        {
            if (_profil.XpClaudeVue < 0)
            {
                // Premier passage : un profil neuf reprend l'XP déjà gagnée avec Claude.
                if (_profil.Xp == 0) _profil.Xp = c.Xp;
                _profil.XpClaudeVue = c.Xp;
                _profil.Ecrire(DossierPartage);
            }
            else if (c.Xp > _profil.XpClaudeVue)
            {
                int gain = c.Xp - _profil.XpClaudeVue;
                _profil.XpClaudeVue = c.Xp;
                _profil.Xp += gain;
                _profil.Ecrire(DossierPartage);
                _xpTotal += gain;
                Flotter($"+{gain} xp");
            }
            else if (c.Xp < _profil.XpClaudeVue - 50)
            {
                _profil.XpClaudeVue = c.Xp; // magasin du mod remis à zéro
            }
        }
        if (Maintenant - _totalLu > 5000)
        {
            _xpTotal = TotalXp();
            _totalLu = Maintenant;
        }
        VerifierNiveau();
        var nom = _suivi.Courant?.Nom ?? "Pilou";
        int n = Niveau, suivant = Profil.XpPourNiveau(n + 1);
        var activite = TenueAffichee == "" ? "" : $" · {Activites.Signe(TenueAffichee)} {Activites.Nom(TenueAffichee)}";
        _scene.ToolTip = $"{nom} · niveau {n} · {_xpTotal}/{suivant} xp · {Recompenses.Titre(n)}{activite}";
    }

    private void VerifierNiveau()
    {
        int n = Niveau;
        if (_dernierNiveau > 0 && n > _dernierNiveau)
        {
            var ouvert = Ouvertures(_dernierNiveau, n);
            Dire(ouvert.Count > 0 ? $"niveau {n} ! accès : {string.Join(", ", ouvert)}" : $"niveau {n} !", 5500);
            Flotter($"NIVEAU {n}", 1.6, new Point(TeteX - 50, TeteY - 70));
            _salueJusque = Maintenant + 2500;
            _tSaut = Maintenant;
        }
        _dernierNiveau = n;
        if (n > _profil.Evolution.NiveauAcquis && _profil.Evolution.Migre >= 1)
        {
            _profil.Evolution.NiveauAcquis = n;
            _profil.Ecrire(DossierPartage);
        }
        PayerNiveaux(n);
        VerifierEvolution(n);
    }

    private static string Nom(Accessoire a) => a switch
    {
        Accessoire.Bonnet => "Bonnet de laine",
        Accessoire.Casque => "Casque audio",
        Accessoire.Noeud => "Nœud papillon",
        Accessoire.Feuille => "Feuille d'automne",
        Accessoire.Lunettes => "Lunettes de soleil",
        Accessoire.Couronne => "Couronne",
        Accessoire.ChapeauPeche => "Chapeau de pêcheur",
        Accessoire.Toque => "Toque de chef",
        Accessoire.Tablier => "Tablier",
        Accessoire.EtoileMer => "Étoile de mer",
        Accessoire.Aucun => "Aucun",
        _ => "Selon la saison",
    };

    private void Gagner(int xp, Point ou)
    {
        xp = BonusSoins(xp);
        SoinJeu();
        _profil.Xp += xp;
        _profil.JeuxGagnes++;
        _profil.Ecrire(DossierPartage);
        _xpTotal += xp;
        Flotter($"+{xp} xp", 1, ou);
        VerifierNiveau();
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
        // Une fois sur trois, une partie de pêche (tu es là : à toi de ferrer).
        Demarrer(_hasard.NextDouble() < 0.33 && Acces.JeuOuvert("peche", Niveau) ? Jeu.Peche : JeuAuHasard(), t);
    }

    private static string IdJeu(Jeu j) => j switch
    {
        Jeu.Etoile => "etoile", Jeu.Bulles => "bulles", Jeu.TapeCinq => "tape", Jeu.Peche => "peche", Jeu.Cuisine => "cuisine", _ => "",
    };

    // Un jeu au hasard parmi ceux que le niveau ouvre (étoile, bulles, tape m'en cinq).
    private Jeu JeuAuHasard()
    {
        var ouverts = new[] { Jeu.Etoile, Jeu.Bulles, Jeu.TapeCinq }.Where(j => Acces.JeuOuvert(IdJeu(j), Niveau)).ToList();
        return ouverts.Count == 0 ? Jeu.Etoile : ouverts[_hasard.Next(ouverts.Count)];
    }

    private void Demarrer(Jeu jeu, double t)
    {
        if (jeu != Jeu.Aucun && !Acces.JeuOuvert(IdJeu(jeu), Niveau))
        {
            Dire($"{Acces.Jeux.First(x => x.Id == IdJeu(jeu)).Nom} : niveau {Acces.NiveauJeu(IdJeu(jeu))}", 3000);
            return;
        }
        Arreter("");
        _jeuEnCours = jeu;
        _jeuDebut = t;
        _geste = Geste.Rien;
        switch (jeu)
        {
            case Jeu.Etoile:
                _etoile = Pixels.Sprite("etoile", 2.2) ?? new Pixels(MotifEtoile, new Brush?[] { null, OrangeJeu, OrangeClair, Blanc }, ContourXp);
                _etoile.Cursor = Cursors.Hand;
                _etoilePos = new Point(Math.Clamp(TeteX + (_hasard.NextDouble() * 2 - 1) * 120, 16, LargeurBase - 40), 24 + _hasard.NextDouble() * 70);
                _etoile.MouseLeftButtonDown += (_, e) =>
                {
                    Gagner(10, _etoilePos);
                    Signaler("jeu", 1);
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
                        Forme = Cliquable(Pixels.Sprite("bulle", 2.2) ?? new Pixels(MotifBulle, new Brush?[] { null, Creme, BulleFond, Blanc }, null)),
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
                            Signaler("jeu", 1);
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
            case Jeu.Peche:
                DemarrerPeche(t);
                break;
            case Jeu.Cuisine:
                DemarrerCuisine(t);
                break;
            case Jeu.TapeCinq:
                _main = Pixels.Sprite("main", 2.2) ?? new Pixels(MotifMain, new Brush?[] { null, Creme }, ContourBleu);
                _main.Cursor = Cursors.Hand;
                _main.MouseLeftButtonDown += (_, e) =>
                {
                    Gagner(10, new Point(TeteX - 18, TeteY - 30));
                    Signaler("jeu", 1);
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
        ArreterPeche();
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
                if (Banque.Commune["etoile"] is not null) _etoile.Changer("etoile", t);
                else _etoile.Changer((int)(t / 220) % 2 == 0 ? MotifEtoile : MotifEtoile2);
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
            case Jeu.Peche:
                AnimerPeche(t);
                break;
            case Jeu.Cuisine:
                AnimerCuisine(t);
                break;
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
