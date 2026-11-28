using System.Globalization;

namespace PilouBureau;

// Animations des campagnes (docs/SPRITES.md, « Animations des campagnes ») : les règles communes au PC et au
// téléphone, en arithmétique entière (même résultat partout). Référence : outils/sprites/animations.py, et son fichier
// outils/sprites/animations-reference.txt relu par AnimationsCampagneTests.cs et AnimationsTest.java.
// Sans WPF : la fenêtre (ScenesAnimees.cs) s'en sert pour choisir les images, écrire lettre à lettre, enchaîner les
// décors et animer le fond.
public static class AnimationsCampagne
{
    public const string Completes = "completes", Reduites = "reduites", Aucune = "aucune";
    public static readonly string[] Niveaux = { Completes, Reduites, Aucune };

    public const int Respiration = 900, ClignePeriode = 4300, ClignDuree = 150, PasParole = 140;
    private static readonly int[] Parole = { 3, 4, 3, 0 };
    public const int ParLettre = 22, PausePoint = 230, PauseVirgule = 90, DureeMax = 5200;
    public const int Transition = 360, VoletBloc = 8;

    // Le niveau effectif : le réglage du joueur (bouton « ✧ ») décide ; tant qu'il n'a rien choisi (réglage vide), le
    // système donne la valeur de départ (« aucune » si Windows demande moins d'animations, sinon « completes »).
    public static string Niveau(string? reglage, bool systeme)
    {
        if (reglage is not null && Array.IndexOf(Niveaux, reglage) >= 0) return reglage;
        return systeme ? Completes : Aucune;
    }

    public static long ImageDecor(int n, int duree, long t, string niveau) =>
        niveau != Completes || n <= 1 || duree <= 0 || t < 0 ? 0 : t / duree % n;

    public static bool Cligne(long t) => t >= 0 && t % ClignePeriode >= ClignePeriode - ClignDuree;

    // Image d'un portrait : 0 et 1 repos (respiration), 2 yeux fermés, 3 et 4 parole (portraits_campagnes.py).
    public static int ImagePortrait(int n, long t, bool parle, string niveau)
    {
        if (n <= 1 || niveau == Aucune || t < 0) return 0;
        if (n > 2 && Cligne(t)) return 2;
        if (niveau != Completes) return 0;
        if (parle && n >= 5) return Parole[(int)(t / PasParole % Parole.Length)];
        return (int)(t / Respiration % 2);
    }

    private static int Cout(char c) => c switch
    {
        '.' or '!' or '?' or '…' => ParLettre + PausePoint,
        ',' or ';' or ':' => ParLettre + PauseVirgule,
        _ => ParLettre,
    };

    private static long Brut(string texte)
    {
        long s = 0;
        foreach (var c in texte) s += Cout(c);
        return s;
    }

    public static long DureeEcriture(string texte) => Math.Min(Brut(texte), DureeMax);

    // Lettres écrites après ms : une lettre, une petite pause aux virgules, une plus longue aux points ; un long
    // message ne dure jamais plus de DureeMax.
    public static int Lettres(string texte, long ms)
    {
        if (ms <= 0) return 0;
        long brut = Brut(texte);
        if (brut <= 0) return texte.Length;
        long total = Math.Min(brut, DureeMax), lim = ms * brut, acc = 0;
        for (int i = 0; i < texte.Length; i++)
        {
            acc += Cout(texte[i]) * total;
            if (acc > lim) return i;
        }
        return texte.Length;
    }

    // Les « … » de Pilou qui écrit, avant un message nouveau.
    public static int Attente(string texte) => Math.Max(600, Math.Min(1500, 450 + 3 * texte.Length));

    private static readonly int[,] Bayer = { { 0, 8, 2, 10 }, { 12, 4, 14, 6 }, { 3, 11, 1, 9 }, { 15, 7, 13, 5 } };

    // Volet pixelisé : ordre d'apparition d'un bloc (dix-millièmes) ; montré quand ordre < progression × 10000.
    public static int OrdreVolet(int bx, int by, int nbx)
    {
        int trame = (Bayer[by % 4, bx % 4] * 2 + 1) * 10000 / 32;
        int balaye = bx * 10000 / Math.Max(1, nbx - 1);
        return (trame * 6 + balaye * 4) / 10;
    }

    // ---- Fond animé : ton et heure
    private static readonly Dictionary<string, (string Haut, string Bas, string Part)> Fonds = new()
    {
        ["humour"] = ("#1c2448", "#3a3263", "#ffc89a"),
        ["mystere"] = ("#0b1022", "#1d2448", "#a9bbd8"),
        ["emotion"] = ("#1d2240", "#4a3f66", "#f2c6d6"),
        ["epique"] = ("#071a33", "#173d66", "#ffd29a"),
    };

    public static string Moment(int heure) => heure is >= 6 and < 11 ? "matin" : heure is >= 11 and < 17 ? "jour" : heure is >= 17 and < 21 ? "soir" : "nuit";

    private static (string Vers, int Cent) Teinte(string moment) => moment switch
    {
        "matin" => ("#f6c89a", 12),
        "jour" => ("#9fb4de", 8),
        "soir" => ("#d9803a", 14),
        _ => ("#05070f", 30),
    };

    private static string Melange(string a, string b, int cent)
    {
        int C(string s, int i) => int.Parse(s.AsSpan(1 + 2 * i, 2), NumberStyles.HexNumber, CultureInfo.InvariantCulture);
        Span<int> r = stackalloc int[3];
        for (int i = 0; i < 3; i++) r[i] = C(a, i) + (int)FloorDiv((C(b, i) - C(a, i)) * cent, 100);
        return string.Create(CultureInfo.InvariantCulture, $"#{r[0]:x2}{r[1]:x2}{r[2]:x2}");
    }

    // Trois couleurs du fond (haut, bas, particules) selon le ton de la campagne et l'heure.
    public static (string Haut, string Bas, string Particule) TeintesFond(string ton, int heure)
    {
        var (h, b, p) = Fonds.TryGetValue(ton, out var f) ? f : ("#151a2e", "#2d333b", "#adbac7");
        var (vers, cent) = Teinte(Moment(heure));
        return (Melange(h, vers, cent), Melange(b, vers, cent), p);
    }

    // Le même bruit entier que outils/sprites/peinture.hasard, en dix-millièmes.
    public static int Hasard(long i, long j, long graine = 0)
    {
        uint n = unchecked((uint)(i * 374761393L + j * 668265263L + graine * 2246822519L));
        n = unchecked((n ^ (n >> 13)) * 1274126177u);
        return (int)(((n ^ (n >> 16)) & 0xFFFF) * 10000 / 65536);
    }

    public const int NbParticules = 14;

    private static (int Vie, int Dx, int Dy, int Bal) Mouvement(string ton) => ton switch
    {
        "humour" => (16000, 600, -3200, 250),
        "emotion" => (19000, -500, 2800, 300),
        "epique" => (14000, 900, -2400, 150),
        _ => (22000, 2600, -300, 120),
    };

    // Une particule du fond : x, y en dix-millièmes, opacité 0–150 ; elle naît, traverse lentement, s'efface.
    public static (int X, int Y, int A) ParticuleFond(string ton, int i, long t)
    {
        var (vie, dx, dy, bal) = Mouvement(ton);
        long decal = (long)Hasard(i, 1, 17) * vie / 10000;
        long u = (t + decal) % vie * 10000 / vie;
        long x = Hasard(i, 2, 17) + FloorDiv(dx * u, 10000);
        long y = Hasard(i, 3, 17) + FloorDiv(dy * u, 10000);
        long tri = u * 4 % 20000;
        if (tri >= 10000) tri = 20000 - tri;
        x += FloorDiv(bal * (tri - 5000), 5000);
        x = Mod(x, 10000);
        y = Mod(y, 10000);
        long a = Math.Min(Math.Min(u, 10000 - u) * 255 * 3 / 10000, 150);
        return ((int)x, (int)y, (int)a);
    }

    // Python arrondit les divisions vers le bas et rend un reste positif : mêmes règles ici.
    private static long FloorDiv(long a, long b) => a / b - (a % b != 0 && (a < 0) != (b < 0) ? 1 : 0);
    private static long Mod(long a, long b) => (a % b + b) % b;

    public static int DelaiRecompense(int i) => 420 + 260 * i;

    // ---- Portraits des personnages

    public static string IdPortrait(string campagne, string personnage, string expression = "") =>
        "portrait-" + campagne + "-" + personnage + (expression is "" or "neutre" ? "" : "-" + expression);

    // Le portrait d'un personnage à l'échelle demandée : son expression si elle est dessinée, sinon son visage neutre ;
    // null s'il n'a pas de portrait (rien n'est montré).
    public static Sprite? Portrait(Banque b, string campagne, string personnage, string expression, int echelle = 2)
    {
        if (string.IsNullOrEmpty(personnage)) return null;
        var id = IdPortrait(campagne, personnage, expression);
        if (b[id] is null) id = IdPortrait(campagne, personnage);
        return b[id] is null ? null : b.Echelle(id, echelle);
    }

    // Parle-t-il dans ce message ? (une réplique entre guillemets)
    public static bool Parle(string texte) => texte.Contains('«');

    // Le personnage d'un élément du fil (clé « partie.étape.rang » du message), d'après son nœud : (id, expression).
    public static (string Personnage, string Expression)? PersonnageDe(Campagnes.Carnet k, Campagnes.Campagne c, string cle)
    {
        foreach (var m in k.Fil)
        {
            if (string.Create(CultureInfo.InvariantCulture, $"{m.P}.{m.E}.{m.I}") != cle) continue;
            var n = c.Noeud(m.Noeud);
            return n is null || n.Personnage == "" ? null : (n.Personnage, n.Expression);
        }
        return null;
    }
}
