namespace PilouBureau;

// « Défense du bureau » : la logique du jeu de tir de Pilou sur une bande de l'écran, sans WPF (testée dans
// tests/DefenseTests.cs). Le monde se compte en pixels de jeu (un pixel de jeu = k pixels d'écran) : W × H,
// la largeur et la hauteur de la bande. Pilou, en bas, tire des étincelles vers le haut ; des vagues de bugs
// avancent en formation, descendent d'un cran à chaque bord et tirent parfois ; des fenêtres et des post-it
// servent d'abris et s'effritent ; des bonus tombent. Tout le hasard vient d'une graine (même graine, mêmes
// gestes → même partie) et le temps avance par pas fixes de 1/120 s, quelle que soit la cadence d'affichage.
public enum PhaseDefense { Accueil, Jeu, EntreVagues, Pause, Fin }

public enum SorteBug { Scarabee, Araignee, Ver, Blinde, Diviseur, Mini, Rapide }

public enum SorteBonus { Double, Bouclier, Ralenti }

public enum EvenementDefense { Tir, Touche, Fele, Explosion, Blesse, BouclierUse, Bonus, Vague, Boss, BossTouche, BossVaincu, Abri, Fin }

public sealed class BugDefense
{
    public SorteBug Sorte;
    public double X, Y;            // coin haut-gauche
    public int Pv = 1;
    public int Col = -1, Rang = -1; // en formation (Col ≥ 0) ; sinon libre (mini, rapide)
    public bool Vivant = true;
    public double Vx, Vy, X0, Phase;
    public int Passages;

    public bool EnFormation => Col >= 0;
    public double L => Sorte switch { SorteBug.Mini => 10, SorteBug.Rapide => 16, _ => 18 };
    public double Ht => Sorte switch { SorteBug.Mini => 8, SorteBug.Rapide => 12, _ => 14 };

    public int Points => Sorte switch
    {
        SorteBug.Scarabee => 30, SorteBug.Araignee => 20, SorteBug.Ver => 10, SorteBug.Blinde => 40,
        SorteBug.Diviseur => 20, SorteBug.Mini => 10, _ => 50,
    };
}

public sealed class BossDefense
{
    public const double L = 72, Ht = 44; // le « Bug de prod » de Chasse aux bugs, dessiné deux fois plus grand
    public double X, Y, T;
    public int Pv, PvMax;
    public double ProchainTir = 1.2, ProchainRenfort = 5;
}

public sealed class TirDefense
{
    public double X, Y, Vx, Vy;    // X : centre ; Y : haut
    public bool Ami, Mort;
    public double Largeur => Ami ? 3 : 7;
    public double Hauteur => Ami ? 9 : 7;
}

public sealed class BonusDefense
{
    public const double Taille = 12;
    public double X, Y;
    public SorteBonus Sorte;
    public bool Pris;
}

public sealed class EclatDefense
{
    public double X, Y, Vx, Vy, Vie;
    public uint Couleur;
}

// Abri : une petite fenêtre ou un post-it, en cases de 3 pixels de jeu ; chaque case a ses points de vie.
public sealed class Abri
{
    public const int Case = 3;
    // Fenêtre : b barre de titre, p boutons, c cadre, v vitre. Post-it : p papier, l lignes écrites, f pli.
    public static readonly string[] Fenetre =
    {
        "bbbbbbbbbbbbb",
        "bbbbbbbbpbpbp",
        "ccccccccccccc",
        "cvvvvvvvvvvvc",
        "cvvvvvvvvvvvc",
        "cvvvvvvvvvvvc",
        "cvvvvvvvvvvvc",
        "cvvvvvvvvvvvc",
        "ccccccccccccc",
    };
    public static readonly string[] PostIt =
    {
        "ppppppppppppp",
        "ppppppppppppp",
        "pplllllllllpp",
        "ppppppppppppp",
        "pplllllllpppp",
        "ppppppppppppp",
        "ppllllllppppp",
        "ppppppppppppf",
        "pppppppppppff",
    };

    public double X, Y;
    public bool EstFenetre;
    public char[,] Sorte = new char[0, 0];
    public int[,] Pv = new int[0, 0];

    public int Lignes => Pv.GetLength(0);
    public int Colonnes => Pv.GetLength(1);
    public double Largeur => Colonnes * Case;
    public double Hauteur => Lignes * Case;

    public static Abri Creer(double x, double y, bool fenetre)
    {
        var modele = fenetre ? Fenetre : PostIt;
        var a = new Abri { X = x, Y = y, EstFenetre = fenetre, Sorte = new char[modele.Length, modele[0].Length], Pv = new int[modele.Length, modele[0].Length] };
        for (int r = 0; r < modele.Length; r++)
        for (int c = 0; c < modele[r].Length; c++)
        {
            char k = modele[r][c];
            a.Sorte[r, c] = k;
            // Cadre et barre de la fenêtre : deux coups ; vitre, papier : un seul ; le pli du post-it : un.
            a.Pv[r, c] = k is 'b' or 'c' or 'p' && fenetre ? 2 : k == '.' ? 0 : 1;
        }
        return a;
    }

    public int PvMax(int r, int c) => EstFenetre && Sorte[r, c] is 'b' or 'c' or 'p' ? 2 : 1;

    public int Restant
    {
        get
        {
            int n = 0;
            foreach (var v in Pv) n += v;
            return n;
        }
    }

    // La case sous un point du monde (r, c), ou (-1, -1).
    public (int R, int C) CaseSous(double x, double y)
    {
        int c = (int)Math.Floor((x - X) / Case), r = (int)Math.Floor((y - Y) / Case);
        return r >= 0 && c >= 0 && r < Lignes && c < Colonnes ? (r, c) : (-1, -1);
    }

    public bool Recouvre(double x, double y, double l, double h) =>
        x < X + Largeur && x + l > X && y < Y + Hauteur && y + h > Y;

    // Toutes les cases sous un rectangle perdent tous leurs points (un bug qui passe dessus les mange).
    public int Ronger(double x, double y, double l, double h)
    {
        int n = 0;
        int c0 = Math.Max(0, (int)Math.Floor((x - X) / Case)), c1 = Math.Min(Colonnes - 1, (int)Math.Floor((x + l - 0.001 - X) / Case));
        int r0 = Math.Max(0, (int)Math.Floor((y - Y) / Case)), r1 = Math.Min(Lignes - 1, (int)Math.Floor((y + h - 0.001 - Y) / Case));
        for (int r = r0; r <= r1; r++)
        for (int c = c0; c <= c1; c++)
            if (Pv[r, c] > 0)
            {
                Pv[r, c] = 0;
                n++;
            }
        return n;
    }
}

// Ce que le pilote automatique (démo) ou la personne demandent.
public sealed class PartieDefense
{
    public const double Pas = 1.0 / 120;
    public const int Hud = 14;
    public const double JoueurL = 26, JoueurH = 28;
    public const double Cadence = 0.30, VitesseEtincelle = 250, VitesseClavier = 170, VitesseSouris = 340;
    public const double DureeDouble = 10, DureeBouclier = 15, DureeRalenti = 6, FacteurRalenti = 0.45;
    public const double Invulnerable = 1.6, DureeCombo = 2.5, PauseVagues = 2.0;
    public const int VagueBossTous = 5, ViesDepart = 3, XpMax = 30;
    public const double EspaceX = 28, EspaceY = 18;

    public int W { get; }
    public int H { get; }
    public double Sol => H - 3;                       // pieds de Pilou
    public double HautJoueur => Sol - JoueurH;
    public double AbriY => H - 80;                    // haut des abris
    public double LigneBureau => HautJoueur - 4;      // un bug de la formation qui la touche : le bureau est envahi

    public PhaseDefense Phase { get; private set; } = PhaseDefense.Accueil;
    public double JoueurX { get; private set; }
    public double VitesseJoueur { get; private set; }
    public double CibleX { get; private set; }
    public bool Tirer { get; set; }
    public int Vies { get; private set; } = ViesDepart;
    public int Score { get; private set; }
    public int Vague { get; private set; }
    public int VaguesFinies { get; private set; }
    public int VagueAtteinte => Math.Max(1, Vague);
    public int BossVaincus { get; private set; }
    public int Combo { get; private set; }
    public int ComboMax { get; private set; }
    public int BugsTues { get; private set; }
    public double Double { get; private set; }
    public double Bouclier { get; private set; }
    public double Ralenti { get; private set; }
    public double Invuln { get; private set; }
    public double ComboReste { get; private set; }
    public double Temps { get; private set; }
    public double PauseVague { get; private set; }
    public string Fin { get; private set; } = "";
    public int Total { get; private set; }            // bugs de la formation au début de la vague
    public double SensFormation { get; private set; } = 1;
    // Tests et rendus de contrôle : Pilou ne perd pas de vie ; la vague ne finit pas faute de bugs.
    public bool Immortel { get; set; }
    public bool VagueSansFin { get; set; }

    public List<BugDefense> Bugs { get; } = new();
    public BossDefense? Boss { get; private set; }
    public List<TirDefense> Tirs { get; } = new();
    public List<BonusDefense> Bonus { get; } = new();
    public List<EclatDefense> Eclats { get; } = new();
    public List<Abri> Abris { get; } = new();

    private readonly Hasard _h;
    private readonly List<EvenementDefense> _evenements = new();
    private double _acc, _prochainTir, _prochainTirBug, _prochainRapide;
    private int _rapidesRestants, _depuisBonus, _sens;
    private bool _souris = true, _demandeTir;
    private PhaseDefense _avantPause;

    public PartieDefense(int largeur, int hauteur, ulong graine)
    {
        W = Math.Max(160, largeur);
        H = Math.Max(150, hauteur);
        _h = new Hasard(graine);
        JoueurX = CibleX = W / 2.0;
    }

    private double Alea() => (_h.Brut() >> 11) * (1.0 / (1UL << 53));

    // Multiplicateur de combo : × 1,5 tous les cinq bugs abattus d'affilée, × 3 au plus.
    public double Multiplicateur => 1 + 0.5 * Math.Min(4, Combo / 5);

    public static bool VagueDeBoss(int v) => v > 0 && v % VagueBossTous == 0;

    // XP de la partie (comme Chasse aux bugs) : score / 150 + 2 par vague franchie, entre 1 et 30.
    public int Xp() => GainsDefense.Xp(Score, VaguesFinies);

    public int Vivants => Bugs.Count(b => b.Vivant && b.EnFormation);

    // ---- Commandes

    public void Commencer()
    {
        Bugs.Clear();
        Tirs.Clear();
        Bonus.Clear();
        Eclats.Clear();
        Boss = null;
        Vies = ViesDepart;
        Score = Vague = VaguesFinies = BossVaincus = Combo = ComboMax = BugsTues = 0;
        Double = Bouclier = Ralenti = Invuln = ComboReste = Temps = 0;
        Fin = "";
        JoueurX = CibleX = W / 2.0;
        _depuisBonus = 0;
        PoserAbris();
        Phase = PhaseDefense.Jeu;
        VagueSuivante();
    }

    // La souris : Pilou file vers cet x (vite, mais pas d'un coup).
    public void Viser(double x)
    {
        _souris = true;
        CibleX = Math.Clamp(x, JoueurL / 2 + 2, W - JoueurL / 2 - 2);
    }

    // Le clavier : -1 gauche, 1 droite, 0 rien. Une touche reprend la main sur la souris.
    public void Diriger(int sens)
    {
        _sens = Math.Sign(sens);
        if (_sens != 0) _souris = false;
    }

    // Un clic ou une pression : un tir dès que la cadence le permet (même si le bouton est déjà relâché).
    public void Appuyer() => _demandeTir = true;

    public void Pause(bool oui)
    {
        if (oui && Phase is PhaseDefense.Jeu or PhaseDefense.EntreVagues)
        {
            _avantPause = Phase;
            Phase = PhaseDefense.Pause;
            Tirer = false;
        }
        else if (!oui && Phase == PhaseDefense.Pause) Phase = _avantPause;
    }

    // Quitter en pleine partie : elle s'arrête là (les gains sont comptés sur ce qui est fait).
    public void Abandonner()
    {
        if (Phase is PhaseDefense.Jeu or PhaseDefense.EntreVagues or PhaseDefense.Pause) Terminer("Partie interrompue");
    }

    public List<EvenementDefense> Evenements()
    {
        var e = new List<EvenementDefense>(_evenements);
        _evenements.Clear();
        return e;
    }

    // ---- Le temps passe (par pas fixes)

    public void Avancer(double dt)
    {
        _acc += Math.Clamp(dt, 0, 0.1);
        while (_acc >= Pas)
        {
            _acc -= Pas;
            Etape(Pas);
        }
    }

    private void Etape(double dt)
    {
        if (Phase == PhaseDefense.Pause) return;
        foreach (var e in Eclats)
        {
            e.X += e.Vx * dt;
            e.Y += e.Vy * dt;
            e.Vy += 60 * dt;
            e.Vie -= dt;
        }
        Eclats.RemoveAll(e => e.Vie <= 0);
        if (Phase is PhaseDefense.Accueil or PhaseDefense.Fin) return;
        Temps += dt;
        BougerJoueur(dt);
        BougerTirs(dt);
        BougerBonus(dt);
        if (Phase == PhaseDefense.EntreVagues)
        {
            Collisions();
            PauseVague -= dt;
            if (PauseVague <= 0) VagueSuivante();
            Nettoyer();
            return;
        }
        Double = Math.Max(0, Double - dt);
        Bouclier = Math.Max(0, Bouclier - dt);
        Ralenti = Math.Max(0, Ralenti - dt);
        Invuln = Math.Max(0, Invuln - dt);
        ComboReste = Math.Max(0, ComboReste - dt);
        if (ComboReste <= 0) Combo = 0;
        double k = Ralenti > 0 ? FacteurRalenti : 1; // le ralenti freine les bugs et leurs tirs, pas Pilou

        _prochainTir -= dt;
        if ((Tirer || _demandeTir) && _prochainTir <= 0)
        {
            _prochainTir = Cadence;
            _demandeTir = false;
            double y = HautJoueur - 8;
            if (Double > 0)
            {
                Tirs.Add(new TirDefense { X = JoueurX - 6, Y = y, Vy = -VitesseEtincelle, Ami = true });
                Tirs.Add(new TirDefense { X = JoueurX + 6, Y = y, Vy = -VitesseEtincelle, Ami = true });
            }
            else Tirs.Add(new TirDefense { X = JoueurX, Y = y, Vy = -VitesseEtincelle, Ami = true });
            _evenements.Add(EvenementDefense.Tir);
        }

        BougerFormation(dt * k);
        BougerLibres(dt * k);
        if (Boss is not null) BougerBoss(dt * k);
        TirerBugs(dt * k);
        LacherRapides(dt);
        Collisions();
        Nettoyer();

        if (Phase == PhaseDefense.Jeu && !VagueSansFin && Vivants == 0 && Boss is null && _rapidesRestants == 0 && !Bugs.Any(b => b.Vivant))
        {
            VaguesFinies++;
            Score += 50 * Vague;
            Phase = PhaseDefense.EntreVagues;
            PauseVague = PauseVagues;
            Tirs.RemoveAll(t => !t.Ami);
        }
    }

    private void BougerJoueur(double dt)
    {
        double avant = JoueurX;
        if (_souris)
        {
            double d = CibleX - JoueurX, pas = VitesseSouris * dt;
            JoueurX += Math.Abs(d) <= pas ? d : Math.Sign(d) * pas;
        }
        else JoueurX += _sens * VitesseClavier * dt;
        JoueurX = Math.Clamp(JoueurX, JoueurL / 2 + 2, W - JoueurL / 2 - 2);
        VitesseJoueur = (JoueurX - avant) / dt;
    }

    private void BougerTirs(double dt)
    {
        foreach (var t in Tirs)
        {
            t.X += t.Vx * dt * (t.Ami || Ralenti <= 0 ? 1 : FacteurRalenti);
            t.Y += t.Vy * dt * (t.Ami || Ralenti <= 0 ? 1 : FacteurRalenti);
            if (t.Y < -12 || t.Y > H + 4 || t.X < -8 || t.X > W + 8) t.Mort = true;
        }
    }

    private void BougerBonus(double dt)
    {
        foreach (var b in Bonus)
        {
            b.Y += 42 * dt;
            if (b.Y > H) b.Pris = true;
        }
    }

    // Vitesse de la formation : plus elle se vide, plus elle file ; plus la vague est haute, plus elle part vite.
    public double VitesseFormation()
    {
        double baseV = W / 30.0 + 2.5 * Vague;
        int total = Math.Max(1, Total);
        return Math.Min(240, baseV * (1 + 1.8 * (1 - Vivants / (double)total)));
    }

    private void BougerFormation(double dt)
    {
        var vivants = Bugs.Where(b => b.Vivant && b.EnFormation).ToList();
        if (vivants.Count == 0) return;
        double dx = SensFormation * VitesseFormation() * dt;
        double gauche = vivants.Min(b => b.X) + dx, droite = vivants.Max(b => b.X + b.L) + dx;
        bool bord = gauche < 4 || droite > W - 4;
        foreach (var b in vivants)
        {
            if (bord) b.Y += 7;
            else b.X += dx;
            foreach (var a in Abris)
                if (a.Recouvre(b.X, b.Y, b.L, b.Ht))
                    a.Ronger(b.X, b.Y, b.L, b.Ht);
            if (b.Y + b.Ht >= LigneBureau && Phase == PhaseDefense.Jeu) Terminer("Les bugs ont envahi le bureau !");
        }
        if (bord) SensFormation = -SensFormation;
    }

    private void BougerLibres(double dt)
    {
        foreach (var b in Bugs)
        {
            if (!b.Vivant || b.EnFormation) continue;
            if (b.Sorte == SorteBug.Rapide)
            {
                // Il pique en zigzag et se rapproche de Pilou ; passé en bas, il revient une fois par le haut.
                b.Phase += dt;
                b.Y += b.Vy * dt;
                double vers = JoueurX - b.L / 2 - b.X0;
                b.X0 += Math.Sign(vers) * Math.Min(Math.Abs(vers), 22 * dt);
                b.X = Math.Clamp(b.X0 + Math.Sin(b.Phase * 3.1) * 28, 2, W - b.L - 2);
                if (b.Y > H + 2)
                {
                    if (++b.Passages >= 2) b.Vivant = false; // il s'enfuit
                    else
                    {
                        b.Y = Hud - b.Ht;
                        b.X0 = 10 + Alea() * (W - 40);
                    }
                }
            }
            else
            {
                // Moitié de bug : rebondit sur les côtés en descendant.
                b.X += b.Vx * dt;
                if (b.X < 2 || b.X + b.L > W - 2) b.Vx = -b.Vx;
                b.X = Math.Clamp(b.X, 2, W - b.L - 2);
                b.Y += b.Vy * dt;
                if (b.Y > H) b.Vivant = false;
            }
        }
    }

    private void BougerBoss(double dt)
    {
        var b = Boss!;
        b.T += dt;
        double amplitude = (W - BossDefense.L - 8) / 2, omega = Math.Min(1.4, (70 + 3 * Vague) / Math.Max(40, amplitude));
        b.X = (W - BossDefense.L) / 2 + Math.Sin(b.T * omega) * amplitude;
        b.Y = Hud + 8 + Math.Sin(b.T * 2.1) * 3;
        b.ProchainTir -= dt;
        if (b.ProchainTir <= 0)
        {
            b.ProchainTir = Math.Max(0.6, 1.3 - Vague * 0.03);
            double cx = b.X + BossDefense.L / 2, cy = b.Y + BossDefense.Ht - 4;
            for (int i = -1; i <= 1; i++) Tirs.Add(new TirDefense { X = cx + i * 10, Y = cy, Vx = i * 24, Vy = 80 + 2 * Vague });
        }
        b.ProchainRenfort -= dt;
        if (b.ProchainRenfort <= 0)
        {
            b.ProchainRenfort = 7;
            for (int s = -1; s <= 1; s += 2) Libre(SorteBug.Mini, b.X + BossDefense.L / 2 - 5 + s * 20, b.Y + BossDefense.Ht - 10, s * 26);
        }
    }

    private void TirerBugs(double dt)
    {
        _prochainTirBug -= dt;
        if (_prochainTirBug > 0) return;
        var formation = Bugs.Where(b => b.Vivant && b.EnFormation).ToList();
        int colonnes = Math.Max(1, formation.Select(b => b.Col).Distinct().Count());
        double frequence = (0.55 + 0.1 * Vague) * Math.Max(0.7, colonnes / 10.0);
        _prochainTirBug = 1 / Math.Min(3.5, frequence) * (0.6 + Alea() * 0.8);
        if (formation.Count == 0) return;
        // Le bug du bas d'une colonne : au hasard, ou (dès la vague 3, une fois sur trois) celle au-dessus de Pilou.
        var bas = formation.GroupBy(b => b.Col).Select(g => g.MaxBy(b => b.Rang)!).ToList();
        BugDefense tireur = Vague >= 3 && Alea() < 0.33
            ? bas.MinBy(b => Math.Abs(b.X + b.L / 2 - JoueurX))!
            : bas[(int)(Alea() * bas.Count) % bas.Count];
        Tirs.Add(new TirDefense { X = tireur.X + tireur.L / 2, Y = tireur.Y + tireur.Ht, Vy = Math.Min(150, 70 + 5 * Vague) });
    }

    private void LacherRapides(double dt)
    {
        if (_rapidesRestants <= 0) return;
        _prochainRapide -= dt;
        if (_prochainRapide > 0) return;
        _prochainRapide = 5 + Alea() * 4;
        _rapidesRestants--;
        var r = Libre(SorteBug.Rapide, 10 + Alea() * (W - 40), Hud - 12, 0);
        r.Vy = 55 + 3 * Vague;
        r.X0 = r.X;
    }

    private BugDefense Libre(SorteBug sorte, double x, double y, double vx)
    {
        var b = new BugDefense { Sorte = sorte, X = x, Y = y, Vx = vx, Vy = 30 + 2 * Vague };
        Bugs.Add(b);
        return b;
    }

    // ---- Collisions

    private static bool Chevauche(double ax, double ay, double al, double ah, double bx, double by, double bl, double bh) =>
        ax < bx + bl && ax + al > bx && ay < by + bh && ay + ah > by;

    private void Collisions()
    {
        foreach (var t in Tirs)
        {
            if (t.Mort) continue;
            if (t.Ami) ToucherAmi(t);
            else ToucherEnnemi(t);
        }
        // Les étincelles éteignent les tirs des bugs qu'elles croisent.
        foreach (var a in Tirs)
        {
            if (a.Mort || !a.Ami) continue;
            foreach (var e in Tirs)
                if (!e.Mort && !e.Ami && Math.Abs(a.X - e.X) < 4 && a.Y < e.Y + 7 && a.Y + 9 > e.Y)
                {
                    a.Mort = e.Mort = true;
                    Eclater(e.X, e.Y + 3, 0xff9b8cff, 4);
                    break;
                }
        }
        double jx = JoueurX - JoueurL / 2;
        foreach (var b in Bugs)
        {
            if (!b.Vivant || b.EnFormation) continue;
            if (Chevauche(b.X + 1, b.Y + 1, b.L - 2, b.Ht - 2, jx, HautJoueur, JoueurL, JoueurH))
            {
                b.Vivant = false;
                Eclater(b.X + b.L / 2, b.Y + b.Ht / 2, Teinte(b.Sorte), 8);
                Blesser();
                continue;
            }
            if (b.Sorte == SorteBug.Mini)
                foreach (var a in Abris)
                    if (a.Recouvre(b.X, b.Y, b.L, b.Ht))
                    {
                        a.Ronger(b.X, b.Y + b.Ht - 4, b.L, 4);
                        b.Vivant = false;
                        Eclater(b.X + b.L / 2, b.Y + b.Ht, 0xff9b8cff, 6);
                        _evenements.Add(EvenementDefense.Abri);
                        break;
                    }
        }
        foreach (var b in Bonus)
        {
            if (b.Pris) continue;
            if (Chevauche(b.X, b.Y, BonusDefense.Taille, BonusDefense.Taille, jx, HautJoueur - 4, JoueurL, JoueurH + 4))
            {
                b.Pris = true;
                Score += 25;
                switch (b.Sorte)
                {
                    case SorteBonus.Double: Double = DureeDouble; break;
                    case SorteBonus.Bouclier: Bouclier = DureeBouclier; break;
                    default: Ralenti = DureeRalenti; break;
                }
                _evenements.Add(EvenementDefense.Bonus);
            }
        }
    }

    private void ToucherAmi(TirDefense t)
    {
        double x = t.X - 1, l = 3, y = t.Y, h = 9;
        if (Boss is { } boss && Chevauche(x, y, l, h, boss.X + 4, boss.Y + 4, BossDefense.L - 8, BossDefense.Ht - 8))
        {
            t.Mort = true;
            boss.Pv--;
            _evenements.Add(EvenementDefense.BossTouche);
            Eclater(t.X, t.Y, 0xfff69d50, 3);
            if (boss.Pv <= 0)
            {
                Marquer(300 + 60 * Vague);
                BossVaincus++;
                Eclater(boss.X + BossDefense.L / 2, boss.Y + BossDefense.Ht / 2, 0xfff69d50, 30);
                Eclater(boss.X + BossDefense.L / 2, boss.Y + BossDefense.Ht / 2, 0xffffd8b0, 16);
                _evenements.Add(EvenementDefense.BossVaincu);
                _evenements.Add(EvenementDefense.Explosion);
                Bonus.Add(new BonusDefense { X = boss.X + BossDefense.L / 2 - 6, Y = boss.Y + BossDefense.Ht, Sorte = (SorteBonus)(int)(Alea() * 3 % 3) });
                Boss = null;
            }
            return;
        }
        foreach (var b in Bugs)
        {
            if (!b.Vivant || !Chevauche(x, y, l, h, b.X + 1, b.Y + 1, b.L - 2, b.Ht - 2)) continue;
            t.Mort = true;
            if (b.Sorte == SorteBug.Blinde && b.Pv > 1)
            {
                b.Pv--;
                Score += 5;
                Eclater(t.X, b.Y + b.Ht, 0xffb8c4d2, 4);
                _evenements.Add(EvenementDefense.Fele);
                return;
            }
            Tuer(b);
            return;
        }
    }

    private void ToucherEnnemi(TirDefense t)
    {
        foreach (var a in Abris)
        {
            var (r, c) = a.CaseSous(t.X, t.Y + t.Hauteur - 1);
            if (r < 0 || a.Pv[r, c] <= 0)
            {
                (r, c) = a.CaseSous(t.X, t.Y + t.Hauteur / 2);
                if (r < 0 || a.Pv[r, c] <= 0) continue;
            }
            a.Pv[r, c]--;
            // Un éclat de plus, à côté (l'abri s'effrite comme un vieux papier).
            if (Alea() < 0.5)
            {
                int dr = (int)(Alea() * 3) - 1, dc = (int)(Alea() * 3) - 1;
                int rr = Math.Clamp(r + dr, 0, a.Lignes - 1), cc = Math.Clamp(c + dc, 0, a.Colonnes - 1);
                if (a.Pv[rr, cc] > 0) a.Pv[rr, cc]--;
            }
            t.Mort = true;
            Eclater(t.X, t.Y + t.Hauteur, a.EstFenetre ? 0xffb4dbff : 0xfff5d76e, 3);
            _evenements.Add(EvenementDefense.Abri);
            return;
        }
        double jx = JoueurX - JoueurL / 2;
        if (Chevauche(t.X - 2, t.Y + 1, 4, 5, jx + 2, HautJoueur + 2, JoueurL - 4, JoueurH - 2))
        {
            t.Mort = true;
            Blesser();
        }
    }

    private void Marquer(int points)
    {
        Combo++;
        ComboMax = Math.Max(ComboMax, Combo);
        ComboReste = DureeCombo;
        Score += (int)Math.Round(points * Multiplicateur);
    }

    private void Tuer(BugDefense b)
    {
        b.Vivant = false;
        BugsTues++;
        Marquer(b.Points);
        _evenements.Add(EvenementDefense.Touche);
        Eclater(b.X + b.L / 2, b.Y + b.Ht / 2, Teinte(b.Sorte), 9);
        if (b.Sorte == SorteBug.Diviseur)
            for (int s = -1; s <= 1; s += 2) Libre(SorteBug.Mini, b.X + 4 + s * 4, b.Y + 3, s * 28);
        // Un bonus de temps en temps (au plus deux à l'écran) ; jamais plus de vingt bugs sans.
        _depuisBonus++;
        if (Bonus.Count(x => !x.Pris) < 2 && (Alea() < 0.06 || _depuisBonus >= 20))
        {
            _depuisBonus = 0;
            Bonus.Add(new BonusDefense { X = b.X + b.L / 2 - 6, Y = b.Y, Sorte = (SorteBonus)((int)(Alea() * 3) % 3) });
        }
    }

    public static uint Teinte(SorteBug s) => s switch
    {
        SorteBug.Scarabee => 0xfff69d50, SorteBug.Araignee => 0xff6cb6ff, SorteBug.Ver => 0xffb8c4d2,
        SorteBug.Rapide => 0xffffd8b0, _ => 0xff9b8cff,
    };

    private void Blesser()
    {
        if (Immortel || Invuln > 0 || Phase != PhaseDefense.Jeu) return;
        if (Bouclier > 0)
        {
            Bouclier = 0;
            Invuln = 0.8;
            _evenements.Add(EvenementDefense.BouclierUse);
            return;
        }
        Vies--;
        Invuln = Invulnerable;
        Combo = 0;
        ComboReste = 0;
        _evenements.Add(EvenementDefense.Blesse);
        Eclater(JoueurX, HautJoueur + 10, 0xff6cb6ff, 12);
        if (Vies <= 0) Terminer("Plus de vies…");
    }

    private void Eclater(double x, double y, uint couleur, int n)
    {
        for (int i = 0; i < n; i++)
        {
            double a = Alea() * Math.PI * 2, v = 20 + Alea() * 45;
            Eclats.Add(new EclatDefense { X = x, Y = y, Vx = Math.Cos(a) * v, Vy = Math.Sin(a) * v - 10, Vie = 0.4 + Alea() * 0.35, Couleur = couleur });
        }
        if (Eclats.Count > 400) Eclats.RemoveRange(0, Eclats.Count - 400);
    }

    private void Nettoyer()
    {
        Tirs.RemoveAll(t => t.Mort);
        Bonus.RemoveAll(b => b.Pris);
        Bugs.RemoveAll(b => !b.Vivant && !b.EnFormation);
    }

    private void Terminer(string raison)
    {
        if (Phase == PhaseDefense.Fin) return;
        Phase = PhaseDefense.Fin;
        Fin = raison;
        Tirer = false;
        _evenements.Add(EvenementDefense.Fin);
    }

    // ---- Vagues

    // Abris : trois à sept, également espacés, une fenêtre puis un post-it.
    private void PoserAbris()
    {
        Abris.Clear();
        int n = Math.Clamp((int)Math.Round(W / 200.0), 3, 7);
        double l = Abri.Fenetre[0].Length * Abri.Case, ecart = (W - n * l) / (n + 1);
        for (int i = 0; i < n; i++) Abris.Add(Abri.Creer(Math.Round(ecart + i * (l + ecart)), AbriY, i % 2 == 0));
    }

    public int Colonnes => Math.Clamp((int)(W * 0.55 / EspaceX), 6, 14);

    public int RangsMax => Math.Clamp((int)((AbriY - 24 - (Hud + 8)) / EspaceY), 2, 5);

    public int Rangs(int vague) => Math.Clamp(3 + (vague - 1) / 2, 2, RangsMax);

    private void VagueSuivante()
    {
        Vague++;
        Bugs.Clear();
        Tirs.RemoveAll(t => !t.Ami);
        SensFormation = 1;
        _prochainTirBug = 1.4;
        // Après chaque Bug de prod, les abris sont neufs.
        if (Vague > 1 && VagueDeBoss(Vague - 1)) PoserAbris();
        if (VagueDeBoss(Vague))
        {
            int pv = 30 + 6 * Vague;
            Boss = new BossDefense { Pv = pv, PvMax = pv, X = (W - BossDefense.L) / 2, Y = Hud + 8 };
            Total = 0;
            _rapidesRestants = 0;
            _evenements.Add(EvenementDefense.Boss);
        }
        else
        {
            Boss = null;
            int cols = Colonnes, rangs = Rangs(Vague);
            double largeur = (cols - 1) * EspaceX + 18;
            double x0 = Math.Round((W - largeur) / 2);
            double y0 = Hud + 8 + Math.Min(12, 2 * (Vague - 1));
            y0 = Math.Min(y0, AbriY - 24 - rangs * EspaceY);
            // Blindés en tête dès la vague 3, de plus en plus nombreux ; diviseurs mêlés aux autres dès la vague 4.
            double partBlindes = Math.Clamp((Vague - 2) * 0.25, 0, 1);
            double partDiviseurs = Vague >= 4 ? Math.Min(0.4, 0.12 + 0.03 * Vague) : 0;
            for (int r = 0; r < rangs; r++)
            for (int c = 0; c < cols; c++)
            {
                var sorte = r == 0 ? SorteBug.Scarabee : r <= 2 ? SorteBug.Araignee : SorteBug.Ver;
                if (r == 0 && Alea() < partBlindes) sorte = SorteBug.Blinde;
                else if (r > 0 && Alea() < partDiviseurs) sorte = SorteBug.Diviseur;
                Bugs.Add(new BugDefense
                {
                    Sorte = sorte, X = x0 + c * EspaceX, Y = y0 + r * EspaceY, Col = c, Rang = r, Pv = sorte == SorteBug.Blinde ? 2 : 1,
                });
            }
            Total = Bugs.Count;
            _rapidesRestants = Vague >= 2 ? Math.Min(5, Vague / 2 + (W > 1200 ? 1 : 0)) : 0;
            _prochainRapide = 3 + Alea() * 3;
            _evenements.Add(EvenementDefense.Vague);
        }
        Phase = PhaseDefense.Jeu;
    }

    // ---- Pour les tests et les rendus de contrôle

    public void SauterA(int vague)
    {
        if (Phase is PhaseDefense.Accueil or PhaseDefense.Fin) Commencer();
        Vague = Math.Max(0, vague - 1);
        VaguesFinies = Vague;
        VagueSuivante();
    }

    public void PoserTir(double x, double y, bool ami) =>
        Tirs.Add(new TirDefense { X = x, Y = y, Vy = ami ? -VitesseEtincelle : 80, Ami = ami });

    public void PoserBonus(double x, double y, SorteBonus sorte) => Bonus.Add(new BonusDefense { X = x, Y = y, Sorte = sorte });

    public BugDefense PoserBug(SorteBug sorte, double x, double y)
    {
        var b = new BugDefense { Sorte = sorte, X = x, Y = y, Pv = sorte == SorteBug.Blinde ? 2 : 1, Vy = 0 };
        if (sorte is not (SorteBug.Mini or SorteBug.Rapide))
        {
            b.Col = 99;
            b.Rang = 0;
        }
        Bugs.Add(b);
        return b;
    }

    public void Placer(double x)
    {
        JoueurX = CibleX = Math.Clamp(x, JoueurL / 2 + 2, W - JoueurL / 2 - 2);
    }

    public void ViderVague()
    {
        Bugs.Clear();
        Boss = null;
        _rapidesRestants = 0;
    }

    public void Ralentir(double s) => Ralenti = s;

    // Empreinte de l'état (déterminisme) : score, positions arrondies, abris.
    public string Empreinte()
    {
        var h = new System.Text.StringBuilder();
        h.Append($"{Phase}|{Score}|{Vague}|{Vies}|{Combo}|{Math.Round(JoueurX, 2)}|");
        foreach (var b in Bugs) h.Append($"{b.Sorte}{(b.Vivant ? 1 : 0)}{Math.Round(b.X, 1)},{Math.Round(b.Y, 1)};");
        foreach (var t in Tirs) h.Append($"{(t.Ami ? 'a' : 'e')}{Math.Round(t.X, 1)},{Math.Round(t.Y, 1)};");
        foreach (var a in Abris) h.Append(a.Restant).Append('/');
        return Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(System.Text.Encoding.UTF8.GetBytes(h.ToString())))[..16];
    }
}

// Pilote de la démo (--essai=defense) : Pilou joue seul. Il esquive ce qui tombe au-dessus de lui, va chercher
// les bonus, vise le bug le plus bas, tire tout le temps ; il réagit avec un petit temps de retard (il finit
// donc par perdre, et la démo recommence).
public sealed class PiloteDemo
{
    private readonly Hasard _h;
    private double _prochaineDecision, _cible = -1;

    public PiloteDemo(ulong graine) => _h = new Hasard(graine ^ 0x5DEECE66DUL);

    private double Alea() => (_h.Brut() >> 11) * (1.0 / (1UL << 53));

    public void Jouer(PartieDefense p, double dt)
    {
        if (p.Phase is not (PhaseDefense.Jeu or PhaseDefense.EntreVagues)) return;
        p.Tirer = true;
        _prochaineDecision -= dt;
        double x = p.JoueurX;
        // Danger juste au-dessus : esquive tout de suite (sans attendre la prochaine décision).
        bool Menace(double mx, double my) => my > p.HautJoueur - 70 && my < p.Sol && Math.Abs(mx - x) < 18;
        var menaces = p.Tirs.Where(t => !t.Ami && Menace(t.X, t.Y)).Select(t => t.X)
            .Concat(p.Bugs.Where(b => b.Vivant && !b.EnFormation && Menace(b.X + b.L / 2, b.Y + b.Ht)).Select(b => b.X + b.L / 2)).ToList();
        if (menaces.Count > 0 && Alea() < 0.9)
        {
            double m = menaces.Average();
            double gauche = x - 36, droite = x + 36;
            bool versDroite = m < x ? droite < p.W - 16 : gauche < 16;
            _cible = versDroite ? droite : gauche;
            _prochaineDecision = 0.25;
        }
        else if (_prochaineDecision <= 0)
        {
            _prochaineDecision = 0.15 + Alea() * 0.25;
            var bonus = p.Bonus.Where(b => b.Y > p.H * 0.35).MinBy(b => Math.Abs(b.X + 6 - x));
            if (bonus is not null) _cible = bonus.X + 6;
            else if (p.Boss is { } boss) _cible = boss.X + BossDefense.L / 2 + (Alea() - 0.5) * 30;
            else
            {
                var bas = p.Bugs.Where(b => b.Vivant).OrderByDescending(b => b.EnFormation ? b.Y : b.Y + 40)
                    .ThenBy(b => Math.Abs(b.X + b.L / 2 - x)).FirstOrDefault();
                if (bas is not null) _cible = bas.X + bas.L / 2 + (Alea() - 0.5) * 8;
            }
        }
        if (_cible >= 0) p.Viser(_cible);
    }
}

// Ce que la personne garde de Défense du bureau (profil de ce PC) : record, plus haute vague, bugs de prod
// vaincus, et ce qui a été gagné aujourd'hui (plafonds quotidiens).
public sealed class EtatDefense
{
    public int Meilleur { get; set; }
    public int MeilleureVague { get; set; }
    public int Boss { get; set; }
    public int Parties { get; set; }
    public string Jour { get; set; } = "";
    public int XpJour { get; set; }
    public int PoJour { get; set; }
}

public sealed record ResultatDefense(int Xp, int Po, bool Plafond, bool Record);

// Gains modestes et bornés, du même ordre que les autres jeux : une partie rapporte au plus 30 xp (comme
// Chasse aux bugs) et 10 po ; par jour, au plus 120 xp et 30 po (le prix d'une quête du jour).
public static class GainsDefense
{
    public const int PoPartieMax = 10, XpJourMax = 120, PoJourMax = 30;

    public static int Xp(int score, int vaguesFinies) => score <= 0 ? 0 : Math.Clamp(score / 150 + 2 * vaguesFinies, 1, PartieDefense.XpMax);

    public static int Po(int score, int vaguesFinies) => score <= 0 ? 0 : Math.Min(PoPartieMax, score / 600 + vaguesFinies / 2);

    // Crédite une partie finie : record, plus haute vague, bugs de prod, et les gains du jour (bornés).
    public static ResultatDefense Crediter(EtatDefense e, DateTime local, int score, int vaguesFinies, int vagueAtteinte, int boss)
    {
        var jour = Quetes.CleJour(local);
        if (e.Jour != jour)
        {
            e.Jour = jour;
            e.XpJour = e.PoJour = 0;
        }
        e.Parties++;
        bool record = score > e.Meilleur && score > 0;
        e.Meilleur = Math.Max(e.Meilleur, score);
        e.MeilleureVague = Math.Max(e.MeilleureVague, vagueAtteinte);
        e.Boss += Math.Max(0, boss);
        int xpBrut = Xp(score, vaguesFinies), poBrut = Po(score, vaguesFinies);
        int xp = Math.Max(0, Math.Min(xpBrut, XpJourMax - e.XpJour));
        int po = Math.Max(0, Math.Min(poBrut, PoJourMax - e.PoJour));
        e.XpJour += xp;
        e.PoJour += po;
        return new ResultatDefense(xp, po, xp < xpBrut || po < poBrut, record);
    }
}
