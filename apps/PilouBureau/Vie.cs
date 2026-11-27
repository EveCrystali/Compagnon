namespace PilouBureau;

// Vie du personnage (docs/SPRITES.md, « Vie du personnage ») : ressorts du saut, arc du saut, antenne qui suit en
// retard, lumière du moment, bouffées de poussière. Mêmes règles que outils/sprites/vie.py et Vie.java, en
// arithmétique entière (divisions vers le bas) : vie-reference.txt, relu par VieTests.cs et VieTest.java.
// Valeurs en millièmes (hauteur : millièmes d'« ancien pixel » ; étirement et antenne : −1000 … 1000).
// Niveau « aucune » : rien ; l'appelant garde les mouvements d'avant.
public static class Vie
{
    public const int Prep = 70, Reception = 280, RetardAntenne = 60, EtireVol = 350;
    public const int Appui = 60, EtireSautille = 220, BouffeeImage = 80;
    private static readonly (int T, int V)[] PrepCles = { (0, 0), (40, -450), (70, -200) };
    private static readonly (int T, int V)[] ReceptionCles = { (0, -600), (50, -700), (120, 260), (190, -100), (250, 30), (280, 0) };
    private static readonly (int T, int V)[] AppuiCles = { (0, -500), (60, 200) };
    private static readonly string[] Couvert = { "nuageux", "pluie", "averse", "orage", "neige", "brouillard" };

    // Bouffées, en pixels de la grille 1× : (recul, hauteur, opaque ?) depuis le talon, au ras du sol.
    public const uint Poussiere = 0xc0b5a690, PoussiereLegere = 0x78b5a690;
    internal static readonly (int Recul, int Haut, bool Plein)[][] Bouffees =
    {
        new[] { (0, 0, true), (1, 0, false) }, new[] { (1, -1, true), (2, 0, false) }, new[] { (2, -1, false) },
    };
    internal static readonly (int Recul, int Haut, bool Plein)[][] BouffeesAtterrissage =
    {
        new[] { (0, 0, true) }, new[] { (1, 0, true), (1, -1, false) }, new[] { (2, -1, false) },
    };

    private static long Div(long a, long b) => a / b - ((a % b != 0) && ((a < 0) != (b < 0)) ? 1 : 0);
    private static long Mod(long a, long b) => (a % b + b) % b;

    internal static int Cles((int T, int V)[] table, long d)
    {
        if (d <= table[0].T) return table[0].V;
        for (int i = 0; i + 1 < table.Length; i++)
        {
            var (t0, v0) = table[i];
            var (t1, v1) = table[i + 1];
            if (d < t1) return (int)(v0 + Div((long)(v1 - v0) * (d - t0), t1 - t0));
        }
        return table[^1].V;
    }

    private static int EtireBond(long d, int vol)
    {
        if (d < 0) return 0;
        if (d < Prep) return Cles(PrepCles, d);
        long k = d - Prep;
        if (k < vol) return (int)Div(EtireVol * Math.Abs(vol - 2 * k), vol);
        long r = k - vol;
        return r < Reception ? Cles(ReceptionCles, r) : 0;
    }

    private static int Antenne(int etireAvant) => (int)Div(-etireAvant * 8L, 10);

    public static (int Saut, int Etire, int Antenne) Bond(long d, int vol, int haut, string niveau)
    {
        if (niveau == AnimationsCampagne.Aucune || d < 0 || vol <= 0) return (0, 0, 0);
        if (niveau != AnimationsCampagne.Completes)
            return d >= vol ? (0, 0, 0) : ((int)Div(haut * 4L * d * (vol - d), (long)vol * vol), 0, 0);
        long k = d - Prep;
        int saut = k >= 0 && k < vol ? (int)Div(haut * 4L * k * (vol - k), (long)vol * vol) : 0;
        return (saut, EtireBond(d, vol), Antenne(EtireBond(d - RetardAntenne, vol)));
    }

    public static long DureeBond(int vol, string niveau) =>
        niveau == AnimationsCampagne.Aucune ? 0 : niveau == AnimationsCampagne.Completes ? Prep + vol + Reception + RetardAntenne : vol;

    private static int EtireSautiller(long d, int periode)
    {
        long k = Mod(d, periode);
        return k < Appui ? Cles(AppuiCles, k) : (int)Div(EtireSautille * Math.Abs(periode - 2 * k), periode);
    }

    public static (int Saut, int Etire, int Antenne) Sautille(long d, int periode, int haut, string niveau)
    {
        if (niveau == AnimationsCampagne.Aucune || d < 0 || periode <= 0) return (0, 0, 0);
        long k = Mod(d, periode);
        int saut = (int)Div(haut * 4L * k * (periode - k), (long)periode * periode);
        if (niveau != AnimationsCampagne.Completes) return (saut, 0, 0);
        return (saut, EtireSautiller(d, periode), Antenne(EtireSautiller(d - RetardAntenne, periode)));
    }

    private static int EtireReception(long d) => d >= 0 && d < Reception ? Cles(ReceptionCles, d) : 0;

    public static (int Etire, int Antenne) Recoit(long d, string niveau)
    {
        if (niveau != AnimationsCampagne.Completes || d < 0 || d >= Reception + RetardAntenne) return (0, 0);
        return (EtireReception(d), Antenne(EtireReception(d - RetardAntenne)));
    }

    // « matin », « soir », « nuit » ou "" (plein jour, ou aube et couchant par temps couvert).
    public static string Lumiere(int heure, string etat, string niveau)
    {
        if (niveau == AnimationsCampagne.Aucune) return "";
        long h = Mod(heure, 24);
        string m = h is >= 6 and < 9 ? "matin" : h is >= 17 and < 21 ? "soir" : h >= 21 || h < 6 ? "nuit" : "";
        if (m == "" || (m != "nuit" && Array.IndexOf(Couvert, etat) >= 0)) return "";
        return m;
    }

    private static (uint Vers, int Cent)? Source(string moment) => moment switch
    {
        "matin" => (0xffffd8b0, 10),
        "soir" => (0xffb98ad9, 16),
        "nuit" => (0xff1d2448, 18),
        _ => null,
    };

    // Une couleur ARGB (opaque) mêlée à la lumière du moment ; l'alpha est gardé.
    public static uint Eclairer(uint c, string moment)
    {
        if (Source(moment) is not { } s) return c;
        uint r = c & 0xff000000;
        for (int dec = 16; dec >= 0; dec -= 8)
        {
            long x = (c >> dec) & 0xff, y = (s.Vers >> dec) & 0xff;
            r |= (uint)(x + Div((y - x) * s.Cent, 100)) << dec;
        }
        return r;
    }

    public static uint[] Eclairer(uint[] te, string moment)
    {
        var o = new uint[te.Length];
        for (int i = 0; i < te.Length; i++) o[i] = Eclairer(te[i], moment);
        return o;
    }

    // Image (0 à 2 ; −1 : rien) de la bouffée du pied arrière : une tous les deux pas, quand il se pose.
    public static int Bouffee(long t, int cadence, int sens)
    {
        if (cadence <= 0) return -1;
        int arriere = sens >= 0 ? 0 : 1;
        long age = Mod(t - (long)cadence * (1 - arriere), 2L * cadence);
        return age < 3 * BouffeeImage ? (int)(age / BouffeeImage) : -1;
    }

    public static int BouffeeAtterrissage(long d) => d >= 0 && d < 3 * BouffeeImage ? (int)(d / BouffeeImage) : -1;
}
