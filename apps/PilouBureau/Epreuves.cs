namespace PilouBureau;

// Les épreuves des campagnes (docs/CAMPAGNES.md : nœud « epreuve »), sans WPF : la logique des mini-jeux, testable ;
// la fenêtre Aventure (VueEpreuve.cs) ne fait que dessiner et transmettre les clics et les touches.
// Chaque jeu dure 10 à 25 s, se joue à la souris ou au clavier, et devient un peu plus exigeant avec la difficulté
// (1 à 3) ; la variable « bonus » de l'histoire (Aide) l'adoucit un peu. Le temps est en ms depuis le début du jeu.
// Tout tirage vient de la graine : même graine, même jeu (les maquettes et les tests en dépendent).
public abstract class MiniJeu
{
    public string Jeu { get; }
    public int Difficulte { get; }
    public int Aide { get; }
    public bool Fini { get; protected set; }
    public bool Reussi { get; protected set; }
    // Ce que la fenêtre écrit sous le jeu (« 2 / 3 », « trop tôt ! »…) et l'instant du dernier événement (ms).
    public string Message { get; protected set; } = "";
    public double MessageT { get; protected set; } = double.NegativeInfinity;
    // Durée prévue (ms) : la limite au-delà de laquelle le jeu s'arrête de lui-même.
    public abstract double Limite { get; }
    // Score montré : réussites / nécessaires.
    public int Touches { get; protected set; }
    public abstract int Besoin { get; }
    public double FiniA { get; protected set; } = double.NaN;

    protected readonly Hasard Tirage;

    protected MiniJeu(string jeu, int difficulte, int aide, ulong graine)
    {
        Jeu = jeu;
        Difficulte = Math.Clamp(difficulte, 1, 3);
        Aide = Math.Clamp(aide, 0, 5);
        Tirage = new Hasard(graine);
    }

    // Tolérances élargies de 8 % par point d'aide (40 % au plus).
    protected double Souplesse => 1 + 0.08 * Aide;

    public abstract void Avancer(double t);

    // Clic (x, y dans l'arène 0..400 × 0..200) ou touche ; pour la mémoire, touche = 0..3 (le signe choisi).
    public abstract void Appuyer(double t, double x = double.NaN, double y = double.NaN, int touche = -1);

    protected void Dire(string m, double t)
    {
        Message = m;
        MessageT = t;
    }

    protected void Terminer(bool reussi, double t)
    {
        if (Fini) return;
        Fini = true;
        Reussi = reussi;
        FiniA = t;
        Dire(reussi ? "réussi !" : "raté…", t);
    }

    public static MiniJeu? Creer(string jeu, int difficulte, int aide, ulong graine) => jeu switch
    {
        "reflexe" => new Reflexe(difficulte, aide, graine),
        "memoire" => new Memoire(difficulte, aide, graine),
        "rythme" => new Rythme(difficulte, aide, graine),
        "visee" => new Visee(difficulte, aide, graine),
        _ => null, // « des » et jeux inconnus : les dés (TirageDes)
    };

    public const double ArenaL = 400, ArenaH = 200;
}

// Réflexe : cinq manches ; l'étoile s'allume après un temps au hasard ; il faut appuyer avant qu'elle s'éteigne.
// Appuyer trop tôt fait perdre la manche. Il en faut 3 (4 en difficulté 3).
public sealed class Reflexe : MiniJeu
{
    public enum Etape { Guette, Allume, Pause }

    public const int Manches = 5;
    public override int Besoin => Difficulte == 3 ? 4 : 3;
    public double Fenetre => (Difficulte switch { 1 => 900, 2 => 650, _ => 480 }) * Souplesse;
    public override double Limite => 25_000;
    public int Manche { get; private set; }
    public int Ratees { get; private set; }
    public Etape Phase { get; private set; } = Etape.Guette;
    public double Allumage { get; private set; }
    private double _pauseFin;

    public Reflexe(int difficulte, int aide, ulong graine) : base("reflexe", difficulte, aide, graine) => Allumage = Prochain(0);

    private double Prochain(double t) => t + 1300 + Tirage.Suivant(1700);

    public override void Avancer(double t)
    {
        // Plusieurs étapes peuvent être passées d'un coup (fenêtre gelée un instant) : on les rattrape dans l'ordre.
        for (int i = 0; i < 4 * Manches && !Fini; i++)
        {
            var avant = (Phase, Manche);
            if (Phase == Etape.Guette && t >= Allumage) Phase = Etape.Allume;
            else if (Phase == Etape.Allume && t > Allumage + Fenetre) Clore(false, Allumage + Fenetre, "trop tard !");
            else if (Phase == Etape.Pause && t >= _pauseFin)
            {
                Phase = Etape.Guette;
                Allumage = Prochain(_pauseFin);
            }
            if ((Phase, Manche) == avant) break;
        }
        if (!Fini && t >= Limite) Terminer(Touches >= Besoin, t);
    }

    public override void Appuyer(double t, double x = double.NaN, double y = double.NaN, int touche = -1)
    {
        Avancer(t);
        if (Fini) return;
        if (Phase == Etape.Guette) Clore(false, t, "trop tôt !");
        else if (Phase == Etape.Allume) Clore(true, t, $"{(int)(t - Allumage)} ms !");
    }

    private void Clore(bool touche, double t, string message)
    {
        Manche++;
        if (touche) Touches++;
        else Ratees++;
        Dire(message, t);
        if (Touches >= Besoin) Terminer(true, t);
        else if (Manches - Ratees < Besoin) Terminer(false, t);
        else
        {
            Phase = Etape.Pause;
            _pauseFin = t + 700;
        }
    }
}

// Mémoire : quatre signes (◆ ● ▲ ■) ; Pilou en montre une suite, il faut la refaire. Difficultés 1 et 2 : une
// seconde chance (la même suite est remontrée).
public sealed class Memoire : MiniJeu
{
    public enum Etape { Montre, Repete }

    public static readonly string[] Signes = { "◆", "●", "▲", "■" };
    public IReadOnlyList<int> Suite { get; }
    public override int Besoin => Suite.Count;
    public double DureeAllume => Difficulte == 3 ? 520 : 650;
    public double Ecart => Difficulte == 3 ? 160 : 220;
    public override double Limite => 25_000;
    public Etape Phase { get; private set; } = Etape.Montre;
    public int Chances { get; private set; }
    public double Debut { get; private set; } = 900; // début de la présentation en cours
    public int DernierAppui { get; private set; } = -1;
    public double DernierAppuiT { get; private set; } = double.NegativeInfinity;
    private double _saisieDepuis;

    public Memoire(int difficulte, int aide, ulong graine) : base("memoire", difficulte, aide, graine)
    {
        int n = 3 + Difficulte;
        var s = new List<int>();
        for (int i = 0; i < n; i++)
        {
            int v = Tirage.Suivant(4);
            if (s.Count >= 2 && s[^1] == v && s[^2] == v) v = (v + 1) % 4; // jamais trois fois le même de suite
            s.Add(v);
        }
        Suite = s;
        Chances = Difficulte < 3 ? 2 : 1;
    }

    private double FinPresentation => Debut + Suite.Count * (DureeAllume + Ecart);

    // Le signe allumé pendant la présentation (-1 : aucun).
    public int SigneAllume(double t)
    {
        if (Phase != Etape.Montre || t < Debut) return -1;
        double d = t - Debut, pas = DureeAllume + Ecart;
        int i = (int)(d / pas);
        return i < Suite.Count && d - i * pas < DureeAllume ? Suite[i] : -1;
    }

    public override void Avancer(double t)
    {
        if (Fini) return;
        if (t >= Limite) Terminer(false, t);
        else if (Phase == Etape.Montre && t >= FinPresentation)
        {
            Phase = Etape.Repete;
            Touches = 0;
            _saisieDepuis = t;
            Dire("à toi !", t);
        }
        else if (Phase == Etape.Repete && t - _saisieDepuis > 4500 * Souplesse) Rater(t, "trop long…"); // 4,5 s sans rien toucher
    }

    public override void Appuyer(double t, double x = double.NaN, double y = double.NaN, int touche = -1)
    {
        Avancer(t);
        if (Fini || Phase != Etape.Repete || touche is < 0 or > 3) return;
        DernierAppui = touche;
        DernierAppuiT = t;
        if (Suite[Touches] == touche)
        {
            Touches++;
            _saisieDepuis = t;
            if (Touches == Suite.Count) Terminer(true, t);
        }
        else Rater(t, "oups, pas celui-là");
    }

    private void Rater(double t, string m)
    {
        Chances--;
        if (Chances <= 0)
        {
            Terminer(false, t);
            return;
        }
        Dire(m + " · je te la remontre", t);
        Phase = Etape.Montre;
        Touches = 0;
        Debut = t + 900;
    }
}

// Rythme : huit notes glissent vers une ligne ; il faut appuyer quand elles passent dessus.
public sealed class Rythme : MiniJeu
{
    public const int Notes = 8;
    public IReadOnlyList<double> Temps { get; }
    public double Tolerance => (Difficulte switch { 1 => 220, 2 => 160, _ => 115 }) * Souplesse;
    public double Intervalle => Difficulte switch { 1 => 1000, 2 => 850, _ => 700 };
    public override int Besoin => Difficulte == 1 ? 5 : 6;
    public override double Limite => Temps[^1] + 1200;
    // Pour chaque note : null pas encore jugée, true touchée, false manquée.
    public bool?[] Jugees { get; }
    public int Manquees { get; private set; }

    public Rythme(int difficulte, int aide, ulong graine) : base("rythme", difficulte, aide, graine)
    {
        var t = new List<double>();
        double x = 2200;
        for (int i = 0; i < Notes; i++)
        {
            t.Add(x);
            // Un peu de syncope en difficulté 2 et 3 (une demi-mesure de plus, ou de moins en 3).
            int r = Tirage.Suivant(6);
            x += Difficulte >= 2 && r == 0 ? Intervalle * 1.5 : Difficulte == 3 && r == 1 ? Intervalle * 0.5 + 120 : Intervalle;
        }
        Temps = t;
        Jugees = new bool?[Notes];
    }

    public override void Avancer(double t)
    {
        if (Fini) return;
        for (int i = 0; i < Notes; i++)
            if (Jugees[i] is null && t > Temps[i] + Tolerance)
            {
                Jugees[i] = false;
                Manquees++;
                Dire("manquée", t);
            }
        Bilan(t);
    }

    public override void Appuyer(double t, double x = double.NaN, double y = double.NaN, int touche = -1)
    {
        Avancer(t);
        if (Fini) return;
        int meilleure = -1;
        for (int i = 0; i < Notes; i++)
            if (Jugees[i] is null && Math.Abs(t - Temps[i]) <= Tolerance && (meilleure < 0 || Math.Abs(t - Temps[i]) < Math.Abs(t - Temps[meilleure])))
                meilleure = i;
        if (meilleure < 0)
        {
            Dire("à contretemps", t);
            return;
        }
        Jugees[meilleure] = true;
        Touches++;
        Dire(Math.Abs(t - Temps[meilleure]) < Tolerance / 2 ? "pile !" : "bien", t);
        Bilan(t);
    }

    private void Bilan(double t)
    {
        if (Touches >= Besoin && Jugees.All(j => j is not null)) Terminer(true, t);
        else if (Notes - Manquees < Besoin) Terminer(false, t);
        else if (Jugees.All(j => j is not null)) Terminer(Touches >= Besoin, t);
    }
}

// Visée : une luciole vole dans l'arène (400 × 200) ; il faut la toucher assez de fois avant la fin du temps.
// Au clavier, Espace tire au viseur fixe du centre (un peu plus large).
public sealed class Visee : MiniJeu
{
    public double Rayon => (Difficulte switch { 1 => 24, 2 => 19, _ => 15 }) * Souplesse;
    public override int Besoin => Difficulte switch { 1 => 4, 2 => 5, _ => 6 };
    public override double Limite => 16_000;
    public int Manques { get; private set; }
    public double DernierTir { get; private set; } = double.NegativeInfinity;
    public (double X, double Y) DernierPoint { get; private set; }
    private double _phase, _phase2;
    private double _vitesse;

    public Visee(int difficulte, int aide, ulong graine) : base("visee", difficulte, aide, graine)
    {
        _phase = Tirage.Suivant(628) / 100.0;
        _phase2 = Tirage.Suivant(628) / 100.0;
        _vitesse = Difficulte switch { 1 => 0.75, 2 => 0.95, _ => 1.15 };
    }

    public (double X, double Y) Position(double t)
    {
        double s = t / 1000 * _vitesse * (1 + 0.06 * Touches);
        double x = ArenaL / 2 + 160 * Math.Sin(1.3 * s + _phase) * Math.Cos(0.37 * s);
        double y = ArenaH / 2 + 72 * Math.Sin(2.1 * s + _phase2);
        return (x, y);
    }

    public override void Avancer(double t)
    {
        if (!Fini && t >= Limite) Terminer(Touches >= Besoin, t);
    }

    public override void Appuyer(double t, double x = double.NaN, double y = double.NaN, int touche = -1)
    {
        Avancer(t);
        if (Fini) return;
        bool clavier = double.IsNaN(x);
        if (clavier) (x, y) = (ArenaL / 2, ArenaH / 2);
        var (lx, ly) = Position(t);
        double r = Rayon * (clavier ? 1.3 : 1);
        DernierTir = t;
        DernierPoint = (x, y);
        if ((lx - x) * (lx - x) + (ly - y) * (ly - y) <= r * r)
        {
            Touches++;
            Dire($"touché ! {Touches}/{Besoin}", t);
            // La luciole repart d'ailleurs.
            _phase += 1.7 + Tirage.Suivant(100) / 100.0;
            _phase2 += 0.9;
            if (Touches >= Besoin) Terminer(true, t);
        }
        else
        {
            Manques++;
            Dire("raté, encore !", t);
        }
    }
}

// Les dés (jeu « des », jeu inconnu, ou « laisser faire les dés ») : le moteur a déjà décidé (Campagnes.DeDe) ; ici,
// seulement le tirage animé d'un dé à 100 faces qui tombe sur un nombre cohérent avec la chance (≤ chance : réussi).
public sealed class TirageDes
{
    public const double Duree = 2400;
    public int Chance { get; }
    public bool Reussi { get; }
    public int Final { get; }
    private readonly List<(double T, int V)> _faces = new();

    public TirageDes(int chance, bool reussi, ulong graine)
    {
        Chance = Math.Clamp(chance, 1, 99);
        Reussi = reussi;
        var h = new Hasard(graine);
        Final = reussi ? 1 + h.Suivant(Chance) : Chance + 1 + h.Suivant(100 - Chance);
        // Les faces défilent de plus en plus lentement (40 ms au début, ~380 ms à la fin).
        double t = 0;
        while (t < Duree - 420)
        {
            _faces.Add((t, 1 + h.Suivant(100)));
            double k = t / Duree;
            t += 40 + 340 * k * k;
        }
        _faces.Add((Duree - 420, Final));
    }

    public int Valeur(double t)
    {
        int v = _faces[0].V;
        foreach (var (ft, fv) in _faces)
            if (ft <= t) v = fv;
        return v;
    }

    public bool Fini(double t) => t >= Duree;
}
