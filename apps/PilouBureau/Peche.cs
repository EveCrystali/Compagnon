using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Shapes;

namespace PilouBureau;

// Pêche et cuisine : Pilou sort sa canne au bord d'une petite eau en pixels. Quand le bouchon plonge,
// un clic dans la seconde ferre la prise ; sinon Pilou tente sa chance seul, bien moins souvent avec
// succès (Butin.cs). Avec ses prises, il cuisine : marmite, flammes, vapeur, et un plat, souvent nouveau.
public sealed partial class FenetrePilou
{
    private const double FenetreMorsure = 1200;
    private const double LargeurEau = 28 * 4;

    private Pixels? _eau, _canne, _bouchon, _alerte, _marmite, _feu, _trophee, _cadre;
    private Line? _fil;
    private readonly List<(Pixels Forme, double Ne, double X, double Y, double Vx, bool Goutte)> _volutes = new();
    private double _mordA, _resultatJusque, _cuitA;
    private bool _remue, _resultat;
    private Point _posBouchon, _posMarmite;

    private static readonly Brush EauBase = Geler(Color.FromRgb(0x4a, 0x8f, 0xdc));
    private static readonly Brush EauClaire = Geler(Color.FromRgb(0xb4, 0xdb, 0xff));
    private static readonly Brush EauSombre = Geler(Color.FromRgb(0x1f, 0x4f, 0x8a));
    private static readonly Brush Argent = Geler(Color.FromRgb(0xb8, 0xc4, 0xd2));
    private static readonly Brush ArgentSombre = Geler(Color.FromRgb(0x57, 0x60, 0x6a));
    private static readonly Brush Fumee = Geler(Color.FromRgb(0x2d, 0x33, 0x3b));
    private static readonly Brush FumeeClaire = Geler(Color.FromRgb(0x76, 0x83, 0x90));
    private static readonly Brush Ambre = Geler(Color.FromRgb(0xc9, 0x7a, 0x28));

    private int CoteJeu => _aGauche ? 1 : -1;
    private double EauX => CoteJeu > 0 ? TeteX + 70 : TeteX - 70 - LargeurEau;
    private double SolY => HauteurBulle + Scene.Sol;

    // ---- Sprites

    private static readonly int[,] MotifCanne = Pixels.Motif(
        "000000001", "000000010", "000000100", "000001000", "000010000", "000100000", "002200000", "012200000", "100000000");
    private static readonly int[,] MotifBouchon = Pixels.Motif("020", "232", "222", "111", "010");
    private static readonly int[,] MotifMarmite = Pixels.Motif(
        "0002222222000", "1122222222211", "0233333333320", "0233333333320", "0223333333220", "0022222222200");
    private static readonly int[,] MotifFeu1 = Pixels.Motif("0100010010", "1210121121", "1221222212");
    private static readonly int[,] MotifFeu2 = Pixels.Motif("0010100100", "1121211210", "2212212221");
    private static readonly int[,] MotifVolute = Pixels.Motif("0110", "1111", "0110");
    private static readonly int[,] MotifAssiette = Pixels.Motif(
        "0000223322000", "0002333332200", "0022222222220", "1111111111111", "0111111111110");

    private static int[,] Eau(double t)
    {
        int decal = (int)(t / 260) % 4;
        var lignes = new string[3];
        lignes[0] = new string(Enumerable.Range(0, 28).Select(x => (x + decal) % 4 == 0 ? '2' : '0').ToArray());
        lignes[1] = new string(Enumerable.Range(0, 28).Select(x => (x + decal) % 7 == 0 ? '2' : '1').ToArray());
        lignes[2] = new string('3', 28);
        return Pixels.Motif(lignes);
    }

    // Dessin de chaque forme : 2 couleur, 3 claire, 4 détail (œil, nageoire).
    private static int[,] Sprite(Forme f) => f switch
    {
        Forme.Poisson => Pixels.Motif("000022220000", "200223322200", "222232222420", "222222222220", "200222222200", "000022220000"),
        Forme.Long => Pixels.Motif("00000000022220", "02220002222342", "22222222222220", "02200222200000"),
        Forme.Plat => Pixels.Motif("0000220000", "0002332000", "0223332220", "2223342222", "0022222200", "0000220000", "0000020000"),
        Forme.Coquillage => Pixels.Motif("00022000", "00233200", "02334320", "23343432", "23434332", "02333320", "00222200"),
        Forme.Crabe => Pixels.Motif("20000000002", "22000000022", "02222222220", "22234243222", "02222222220", "20202020202"),
        Forme.Algue => Pixels.Motif("002000", "020200", "002020", "020200", "002020", "020220", "202020", "022220"),
        Forme.Botte => Pixels.Motif("0022220", "0023320", "0022220", "0022220", "0022220", "2222220", "2222222", "4444444"),
        Forme.Bouteille => Pixels.Motif("00400", "00200", "02320", "23332", "23432", "23432", "23332", "23332", "02220"),
        Forme.Caillou => Pixels.Motif("0022200", "0233322", "2232222", "0222220"),
        Forme.Cle => Pixels.Motif("0220000000", "2002222222", "2002000202", "0220000202"),
        Forme.Pieuvre => Pixels.Motif("002222200", "023333320", "024323420", "022222220", "022222220", "020202020", "202020202", "020002020"),
        Forme.Hippocampe => Pixels.Motif("022200", "223420", "022220", "002220", "022320", "223200", "022200", "002200", "000220", "002200"),
        Forme.Coffre => Pixels.Motif("022222220", "233333332", "222242222", "244424442", "222242222", "222222222", "244444442"),
        Forme.Perle => Pixels.Motif("002200", "023320", "233332", "233342", "023420", "002200"),
        _ => Pixels.Motif("00000000040000", "00000000404000", "00022222222000", "02233333222220", "22234222222222", "02222222222220", "00222000000000"),
    };

    private static Brush Teinte(string hex) => Geler((Color)ColorConverter.ConvertFromString(hex));

    // Cadre de rareté : la forme change avec le rang (aucun · coins · trait · double · étoilé), la couleur aussi.
    private static (int[,] Motif, Brush?[] Palette)? Cadre(Rarete r, int w, int h)
    {
        if (r == Rarete.Commun) return null;
        int W = w + 4, H = h + 4;
        var m = new int[H, W];
        for (int y = 0; y < H; y++)
        for (int x = 0; x < W; x++)
        {
            bool bord = x == 0 || y == 0 || x == W - 1 || y == H - 1;
            bool coin = (x <= 1 || x >= W - 2) && (y <= 1 || y >= H - 2);
            m[y, x] = r switch
            {
                Rarete.PeuCommun => coin && bord ? 1 : 0,
                Rarete.Rare => bord ? 1 : 0,
                Rarete.Epique => bord ? 1 : coin ? 2 : 0,
                _ => bord ? ((x + y) % 2 == 0 ? 1 : 2) : coin ? 2 : 0,
            };
        }
        Brush?[] palette = r switch
        {
            Rarete.PeuCommun => new Brush?[] { null, ArgentSombre },
            Rarete.Rare => new Brush?[] { null, BleuClair },
            Rarete.Epique => new Brush?[] { null, OrangeJeu, OrangeClair },
            _ => new Brush?[] { null, Argent, OrangeJeu },
        };
        return (m, palette);
    }

    // ---- Pêche

    private void DemarrerPeche(double t)
    {
        _resultat = false;
        _mordA = t + 700 + 3000 + _hasard.NextDouble() * 12000;
        double y = SolY - 12;
        _eau = new Pixels(Eau(t), new Brush?[] { null, EauBase, EauClaire, EauSombre }, null, 4) { IsHitTestVisible = false };
        Canvas.SetLeft(_eau, EauX - 4);
        Canvas.SetTop(_eau, y - 4);
        _jeu.Children.Add(_eau);

        var canne = CoteJeu > 0 ? MotifCanne : Miroir(MotifCanne);
        _canne = Pixels.Sprite("canne", 1.2 * Scene.PX, 0, CoteJeu < 0) ?? new Pixels(canne, new Brush?[] { null, ArgentSombre, OrangeJeu }, null, 4);
        _canne.IsHitTestVisible = false;
        double baseX = TeteX + CoteJeu * 22;
        Canvas.SetLeft(_canne, CoteJeu > 0 ? baseX - 4 : baseX - 36);
        Canvas.SetTop(_canne, SolY - 64);
        _jeu.Children.Add(_canne);

        _posBouchon = new Point(CoteJeu > 0 ? EauX + 44 : EauX + LargeurEau - 56, y - 18);
        _bouchon = Pixels.Sprite("bouchon", 1.6) ?? new Pixels(MotifBouchon, new Brush?[] { null, Creme, OrangeJeu, OrangeClair }, ContourXp, 3);
        _bouchon.Cursor = Cursors.Hand;
        _bouchon.MouseLeftButtonDown += (_, e) =>
        {
            ClicBouchon();
            e.Handled = true;
        };
        _jeu.Children.Add(_bouchon);
        _fil = new Line { Stroke = Creme, StrokeThickness = 1.2, IsHitTestVisible = false, Opacity = 0.85 };
        _jeu.Children.Add(_fil);
        Dire(_inactif > 60_000 ? "je vais pêcher un peu…" : "on pêche ? clique quand ça mord !", 2600);
    }

    private static int[,] Miroir(int[,] m)
    {
        int h = m.GetLength(0), w = m.GetLength(1);
        var r = new int[h, w];
        for (int y = 0; y < h; y++)
        for (int x = 0; x < w; x++)
            r[y, x] = m[y, w - 1 - x];
        return r;
    }

    private void ClicBouchon()
    {
        if (_resultat) return;
        var t = Maintenant;
        if (t < _mordA)
        {
            Dire("trop tôt ! il a filé", 2200);
            FinPeche(null, false, t);
        }
        else if (t < _mordA + FenetreMorsure)
        {
            FinPeche(Butin.Tirer(_hasard, Niveau, seul: false, canneDoree: Possede(PilouBureau.Boutique.CanneDoree)), false, t);
        }
    }

    private void FinPeche(Prise? p, bool seul, double t)
    {
        _resultat = true;
        _resultatJusque = t + (p is null ? 1600 : 3200);
        if (_bouchon is not null) _bouchon.Visibility = Visibility.Hidden;
        if (_fil is not null) _fil.Visibility = Visibility.Hidden;
        if (_alerte is not null) _jeu.Children.Remove(_alerte);
        _alerte = null;
        if (p is null)
        {
            if (seul) Dire("raté… il s'est échappé", 2200);
            return;
        }
        bool nouvelle = !_profil.Carnet.ContainsKey(p.Id);
        _profil.Carnet[p.Id] = (_profil.Carnet.TryGetValue(p.Id, out var n) ? n : 0) + 1;
        if (p.Comestible) _profil.Stock[p.Id] = (_profil.Stock.TryGetValue(p.Id, out var s) ? s : 0) + 1;
        if (!MontrerTropheeHd("prise-" + p.Id, p.Rarete))
            MontrerTrophee(Sprite(p.Forme), new Brush?[] { null, Teinte(p.Couleur), Teinte(p.Clair), Teinte(p.Detail) }, p.Rarete);
        Dire($"{Butin.Signe(p.Rarete)} {p.Nom} · {Butin.NomRarete(p.Rarete)}{(nouvelle ? " · nouveau !" : "")}{(seul ? " (tout seul !)" : "")}", 3600);
        Gagner(Butin.XpPrise(p, nouvelle), new Point(TeteX - 18, TeteY - 52));
        Signaler("peche", 1);
        if (p.Rarete >= Rarete.Rare) Signaler("peche:rare", 1);
        _salueJusque = t + 1800;
        _tSaut = t;
    }

    // Sprite HD de la banque au-dessus de la tête (pixel de 1,5 : deux fois plus fin que l'ancien trophée).
    private bool MontrerTropheeHd(string id, Rarete r)
    {
        if (Pixels.DeSprite(id) is not { } d) return false;
        const double taille = 1.5;
        int sw = d.Motif.GetLength(1), sh = d.Motif.GetLength(0);
        double w = (sw + 2) * taille, h = (sh + 2) * taille;
        double x = Math.Round((TeteX - w / 2) / 3) * 3, y = Math.Max(4, TeteY - 30 - h);
        if (Cadre(r, (sw + 1) / 2, (sh + 1) / 2) is { } c)
        {
            _cadre = new Pixels(c.Motif, c.Palette, null, 3) { IsHitTestVisible = false };
            Canvas.SetLeft(_cadre, x - 2 * 3);
            Canvas.SetTop(_cadre, y - 2 * 3);
            _jeu.Children.Add(_cadre);
        }
        _trophee = new Pixels(d.Motif, d.Palette, null, taille) { IsHitTestVisible = false };
        Canvas.SetLeft(_trophee, x);
        Canvas.SetTop(_trophee, y);
        _jeu.Children.Add(_trophee);
        return true;
    }

    // La prise (ou le plat) s'affiche au-dessus de la tête, dans son cadre de rareté.
    private void MontrerTrophee(int[,] motif, Brush?[] palette, Rarete r)
    {
        const double taille = 3;
        double w = (motif.GetLength(1) + 2) * taille, h = (motif.GetLength(0) + 2) * taille;
        double x = Math.Round((TeteX - w / 2) / 3) * 3, y = Math.Max(4, TeteY - 30 - h);
        if (Cadre(r, motif.GetLength(1), motif.GetLength(0)) is { } c)
        {
            _cadre = new Pixels(c.Motif, c.Palette, null, taille) { IsHitTestVisible = false };
            Canvas.SetLeft(_cadre, x - 2 * taille);
            Canvas.SetTop(_cadre, y - 2 * taille);
            _jeu.Children.Add(_cadre);
        }
        _trophee = new Pixels(motif, palette, ContourXp, taille) { IsHitTestVisible = false };
        Canvas.SetLeft(_trophee, x);
        Canvas.SetTop(_trophee, y);
        _jeu.Children.Add(_trophee);
    }

    private void AnimerPeche(double t)
    {
        _eau?.Changer(Eau(t));
        if (_resultat)
        {
            if (t > _resultatJusque) Arreter("");
            return;
        }
        if (_bouchon is null || _fil is null) return;
        bool mord = t >= _mordA && t < _mordA + FenetreMorsure;
        double lance = Math.Clamp((t - _jeuDebut) / 700, 0, 1);
        // Lancer : le bouchon part du bout de la canne et décrit un arc jusqu'à l'eau.
        var bout = new Point(TeteX + CoteJeu * 22 + CoteJeu * 32, SolY - 64);
        double bx = bout.X + (_posBouchon.X - bout.X) * lance;
        double by = bout.Y + (_posBouchon.Y - bout.Y) * lance - Math.Sin(Math.PI * lance) * 30;
        if (lance >= 1) by += mord ? 8 + ((int)(t / 90) % 2) * 3 : ((int)(t / 600) % 2) * 3;
        Canvas.SetLeft(_bouchon, Math.Round(bx / 3) * 3);
        Canvas.SetTop(_bouchon, Math.Round(by / 3) * 3);
        _fil.X1 = bout.X + 2;
        _fil.Y1 = bout.Y + 2;
        _fil.X2 = bx + 7;
        _fil.Y2 = by + 2;

        if (mord && _alerte is null)
        {
            _alerte = new Pixels(Pixels.Texte("!"), new Brush?[] { null, OrangeJeu }, ContourXp, 4) { IsHitTestVisible = false };
            _jeu.Children.Add(_alerte);
            Eclabousser(new Point(_posBouchon.X + 4, _posBouchon.Y + 10), t);
            _tSaut = t;
        }
        if (_alerte is not null)
        {
            Canvas.SetLeft(_alerte, _posBouchon.X + 2);
            Canvas.SetTop(_alerte, _posBouchon.Y - 30 - ((int)(t / 120) % 2) * 4);
        }
        // Personne n'a ferré à temps : Pilou tente le coup tout seul.
        if (t >= _mordA + FenetreMorsure) FinPeche(Butin.Tirer(_hasard, Niveau, seul: true, canneDoree: Possede(PilouBureau.Boutique.CanneDoree)), true, t);
        AnimerVolutes(t);
    }

    private void Eclabousser(Point ou, double t)
    {
        for (int i = 0; i < 5; i++)
        {
            var goutte = new Pixels(Pixels.Motif("1"), new Brush?[] { null, EauClaire }, null, 4) { IsHitTestVisible = false };
            _jeu.Children.Add(goutte);
            _volutes.Add((goutte, t, ou.X + (i - 2) * 4, ou.Y, (i - 2) * 22, true));
        }
    }

    // ---- Cuisine

    private void DemarrerCuisine(double t)
    {
        if (!Butin.PeutCuisiner(_profil.Stock))
        {
            Dire("rien à cuisiner : allons pêcher d'abord", 2600);
            _jeuEnCours = Jeu.Aucun;
            return;
        }
        _remue = false;
        _resultat = false;
        _cuitA = t + 4500;
        _posMarmite = new Point(CoteJeu > 0 ? TeteX + 60 : TeteX - 60 - 15 * 4, SolY - 40);
        _feu = Pixels.Sprite("feu", 1.6) ?? new Pixels(MotifFeu1, new Brush?[] { null, OrangeJeu, OrangeClair }, null, 4);
        _feu.IsHitTestVisible = false;
        Canvas.SetLeft(_feu, _posMarmite.X + 8);
        Canvas.SetTop(_feu, _posMarmite.Y + 26);
        _jeu.Children.Add(_feu);
        _marmite = Pixels.Sprite("marmite", 2.2) ?? new Pixels(MotifMarmite, new Brush?[] { null, ArgentSombre, Argent, EauSombre }, ContourXp, 4);
        _marmite.Cursor = Cursors.Hand;
        _marmite.ToolTip = "remuer";
        _marmite.MouseLeftButtonDown += (_, e) =>
        {
            if (!_remue && !_resultat)
            {
                _remue = true;
                Dire("je remue, ça ne brûlera pas", 2000);
            }
            e.Handled = true;
        };
        Canvas.SetLeft(_marmite, _posMarmite.X);
        Canvas.SetTop(_marmite, _posMarmite.Y);
        _jeu.Children.Add(_marmite);
        Dire("je cuisine quelque chose…", 2400);
    }

    private void AnimerCuisine(double t)
    {
        if (_feu is not null)
        {
            if (Banque.Commune["feu"] is not null) _feu.Changer("feu", t);
            else _feu.Changer((int)(t / 160) % 2 == 0 ? MotifFeu1 : MotifFeu2);
        }
        if (_marmite is not null && !_resultat && Banque.Commune["marmite"] is not null) _marmite.Changer("marmite", t);
        if (!_resultat)
        {
            if ((int)(t / 420) != (int)((t - 33) / 420)) Volute(new Point(_posMarmite.X + 18 + _hasard.Next(20), _posMarmite.Y - 4), t, Creme);
            if (t >= _cuitA) Servir(t);
        }
        else if (t > _resultatJusque) Arreter("");
        AnimerVolutes(t);
    }

    private void Servir(double t)
    {
        _resultat = true;
        var plat = Butin.Cuisiner(_hasard, Niveau, _profil.Stock, _profil.Plats, _remue, Possede(PilouBureau.Boutique.MarmiteCuivre));
        if (plat is null)
        {
            Arreter("");
            return;
        }
        foreach (var id in plat.Utilises)
            if (_profil.Stock.TryGetValue(id, out var n)) _profil.Stock[id] = Math.Max(0, n - 1);
        _profil.PlatsCuisines++;
        _resultatJusque = t + 3400;
        if (_feu is not null) _feu.Visibility = Visibility.Hidden;
        if (plat.Rate)
        {
            for (int i = 0; i < 6; i++) Volute(new Point(_posMarmite.X + 10 + i * 6, _posMarmite.Y - 2), t + i * 90, i % 2 == 0 ? Fumee : FumeeClaire);
            Dire("oups… c'est brûlé", 2600);
            Gagner(plat.Xp, new Point(TeteX - 18, TeteY - 40));
            return;
        }
        if (plat.Decouverte) _profil.Plats.Add(plat.Id);
        var ingredient = Butin.Trouver(plat.Utilises[0]);
        var palette = new Brush?[] { null, Creme, Teinte(ingredient?.Couleur ?? "#f69d50"), Teinte(ingredient?.Clair ?? "#ffd8b0") };
        var rang = plat.Inventee ? Rarete.Commun : plat.Xp >= 40 ? Rarete.Epique : plat.Xp >= 16 ? Rarete.Rare : Rarete.PeuCommun;
        var rangAffiche = plat.Decouverte ? (Rarete)Math.Max((int)rang, (int)Rarete.PeuCommun) : rang;
        if (!MontrerTropheeHd(Banque.Commune.Plat(plat.Inventee ? "" : plat.Id, false), rangAffiche))
            MontrerTrophee(MotifAssiette, palette, rangAffiche);
        Dire(plat.Decouverte ? $"✦ nouveau plat : {plat.Nom} !" : $"{plat.Nom}, encore un régal", 3800);
        Gagner(plat.Xp, new Point(TeteX - 18, TeteY - 52));
        Signaler("cuisine", 1);
        if (plat.Decouverte) Signaler("cuisine:nouveau", 1);
        _salueJusque = t + 1800;
        _tSaut = t;
    }

    private void Volute(Point ou, double ne, Brush couleur)
    {
        var v = new Pixels(MotifVolute, new Brush?[] { null, couleur }, null, 3) { IsHitTestVisible = false, Opacity = 0 };
        _jeu.Children.Add(v);
        _volutes.Add((v, ne, ou.X, ou.Y, (_hasard.NextDouble() - 0.5) * 10, false));
    }

    // Vapeur, fumée et gouttes : elles montent (ou retombent), s'écartent et s'effacent.
    private void AnimerVolutes(double t)
    {
        for (int i = _volutes.Count - 1; i >= 0; i--)
        {
            var (f, ne, x, y, vx, goutte) = _volutes[i];
            double k = (t - ne) / 1400;
            if (k < 0) continue;
            if (k >= 1)
            {
                _jeu.Children.Remove(f);
                _volutes.RemoveAt(i);
                continue;
            }
            double yy = goutte ? y - Math.Sin(Math.PI * k) * 18 : y - k * 40;
            Canvas.SetLeft(f, Math.Round((x + vx * k + (goutte ? 0 : Math.Sin(k * 6) * 3)) / 3) * 3);
            Canvas.SetTop(f, Math.Round(yy / 3) * 3);
            f.Opacity = goutte ? 1 - k : k < 0.2 ? k / 0.2 : (1 - k) / 0.8;
        }
    }

    private void ArreterPeche()
    {
        foreach (var e in new UIElement?[] { _eau, _canne, _bouchon, _alerte, _marmite, _feu, _trophee, _cadre, _fil })
            if (e is not null) _jeu.Children.Remove(e);
        foreach (var v in _volutes) _jeu.Children.Remove(v.Forme);
        _volutes.Clear();
        _eau = _canne = _bouchon = _alerte = _marmite = _feu = _trophee = _cadre = null;
        _fil = null;
        if (_resultat) _profil.Ecrire(DossierPartage);
        _resultat = false;
    }

    // Pendant la pêche, il regarde l'eau et se concentre ; il guette quand ça mord.
    private Expr ExprJeu(Expr montre, double t)
    {
        if (_jeuEnCours == Jeu.Peche && !_resultat) return t >= _mordA ? Expr.Attente : Expr.Concentre;
        if (_jeuEnCours == Jeu.Cuisine && !_resultat) return Expr.Concentre;
        return montre;
    }

    // ---- Pilou s'occupe seul quand tu t'éloignes un moment (pas assez pour qu'il dorme).

    private double _prochainSolo = 10 * 60_000;

    private void OccuperSeul(double t, Expr expr)
    {
        if (!_reglages.Jeux || _jeuEnCours != Jeu.Aucun || t < _prochainSolo || _dortBureau || _attrape) return;
        if (expr is not Expr.Repos || _inactif is < 90_000 or > 9 * 60_000 || _geste == Geste.SauteSouris) return;
        // Toutes les 7 à 16 min environ (4 à 9 avant).
        _prochainSolo = t + (4 + _hasard.NextDouble() * 5) * Vivacite.EspacementJeux * 60_000;
        Dosage.Noter(t);
        Demarrer(Butin.PeutCuisiner(_profil.Stock) && _hasard.NextDouble() < 0.35 ? Jeu.Cuisine : Jeu.Peche, t);
    }

    // ---- Menus

    private IEnumerable<object> MenusPeche()
    {
        var pecher = Entree(Acces.JeuOuvert("peche", Niveau) ? "Pêcher" : $"Pêcher — niveau {Acces.NiveauJeu("peche")}", () => Demarrer(Jeu.Peche, Maintenant));
        pecher.IsEnabled = Acces.JeuOuvert("peche", Niveau);
        yield return pecher;
        int ingredients = _profil.Stock.Where(kv => Butin.Trouver(kv.Key) is { Comestible: true }).Sum(kv => kv.Value);
        var cuisiner = Entree(ingredients > 0 ? $"Cuisiner ({ingredients} ingrédient{(ingredients > 1 ? "s" : "")})" : "Cuisiner (pêche d'abord)",
            () => Demarrer(Jeu.Cuisine, Maintenant));
        cuisiner.IsEnabled = ingredients > 0 && Acces.JeuOuvert("cuisine", Niveau);
        if (!Acces.JeuOuvert("cuisine", Niveau)) cuisiner.Header = $"Cuisiner — niveau {Acces.NiveauJeu("cuisine")}";
        yield return cuisiner;

        int vues = Butin.Prises.Count(p => _profil.Carnet.ContainsKey(p.Id));
        var carnet = new MenuItem { Header = $"Carnet de pêche — {vues}/{Butin.Prises.Count}" };
        foreach (var p in Butin.Prises)
        {
            bool vue = _profil.Carnet.TryGetValue(p.Id, out var n);
            var stock = _profil.Stock.TryGetValue(p.Id, out var s) && s > 0 ? $" · {s} en réserve" : "";
            carnet.Items.Add(new MenuItem
            {
                Header = vue
                    ? $"{Butin.Signe(p.Rarete)}  {p.Nom} ×{n} ({Butin.NomRarete(p.Rarete)}){stock}"
                    : $"{Butin.Signe(p.Rarete)}  ??? ({Butin.NomRarete(p.Rarete)}, niveau {p.NiveauMin})",
                IsEnabled = vue,
            });
        }
        yield return carnet;

        int faites = Butin.Recettes.Count(r => _profil.Plats.Contains(r.Id));
        var inventes = _profil.Plats.Where(id => id.StartsWith("inv:")).ToList();
        var livre = new MenuItem { Header = $"Livre de recettes — {faites}/{Butin.Recettes.Count} · {inventes.Count} plats inventés" };
        foreach (var r in Butin.Recettes)
        {
            bool faite = _profil.Plats.Contains(r.Id);
            livre.Items.Add(new MenuItem
            {
                Header = faite ? $"✓  {r.Nom}" : $"??? (niveau {r.NiveauMin}, {r.Saveurs.Length} ingrédient{(r.Saveurs.Length > 1 ? "s" : "")})",
                IsEnabled = faite,
            });
        }
        if (inventes.Count > 0)
        {
            livre.Items.Add(new Separator());
            foreach (var id in inventes.TakeLast(12).Reverse()) livre.Items.Add(new MenuItem { Header = "✦  " + id[4..] });
        }
        yield return livre;
    }
}
