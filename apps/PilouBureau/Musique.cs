using System.IO;
using System.Reflection;
using System.Threading;

namespace PilouBureau;

// Musiques et ambiances de l'Aventure (docs/SONS.md). Décrites dans assets/musiques.txt, synthétisées ici en entiers,
// exactement comme Musique.java et outils/sons/sons.py (empreintes dans outils/sons/musiques-reference.txt). Lues
// par waveOut de Windows (winmm, sans bibliothèque), à côté des sons : PlaySound n'en joue qu'un à la fois.
public static partial class Musique
{
    public const int Taux = Sons.Taux;

    // Réglage « Musique » : aucune, discrète (par défaut), normale.
    public static readonly string[] Niveaux = { "aucune", "discrete", "normale" };
    public static readonly string[] Tons = { "prologue", "humour", "mystere", "emotion" };

    public sealed record Voix(string Onde, int Volume, int Attaque, int Relache, int Declin, int Tenue, List<string> Jetons);
    public sealed record Morceau(int Ms, int Pas, int Filtre, List<Voix> Voix);
    public readonly record struct NoteBoucle(int Pas, int Longueur, long F0, long F1);

    private static readonly long[] Gamme = { 261626, 277183, 293665, 311127, 329628, 349228, 369994, 391995, 415305, 440000, 466164, 493883 };
    private static readonly string[] NomsNotes = { "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B" };

    // Jeton → milli-hertz : « A4 », « F#3 » ou un nombre de hertz (bruit).
    public static long Frequence(string j)
    {
        if (char.IsAsciiDigit(j[0])) return long.Parse(j) * 1000;
        int octave = j[^1] - '0';
        long f = Gamme[Array.IndexOf(NomsNotes, j[..^1])];
        return octave >= 4 ? f << (octave - 4) : f >> (4 - octave);
    }

    public static (Dictionary<string, Morceau> Morceaux, Dictionary<string, string> Decors) Lire(string texte)
    {
        var morceaux = new Dictionary<string, Morceau>();
        var decors = new Dictionary<string, string>();
        Morceau? courant = null;
        Voix? voix = null;
        foreach (var brute in texte.Split('\n'))
        {
            var l = brute.Trim();
            if (l.Length == 0 || l.StartsWith('#')) continue;
            var p = l.Split('|').Select(x => x.Trim()).ToArray();
            var jetons = p[^1].Split(' ', StringSplitOptions.RemoveEmptyEntries);
            switch (p[0])
            {
                case "morceau":
                    morceaux[p[1]] = courant = new Morceau(int.Parse(p[2]), int.Parse(p[3]), int.Parse(p[4]), new());
                    break;
                case "voix":
                    voix = new Voix(p[1], int.Parse(p[2]), int.Parse(p[3]), int.Parse(p[4]), int.Parse(p[5]), int.Parse(p[6]), jetons.ToList());
                    courant!.Voix.Add(voix);
                    break;
                case "+":
                    voix!.Jetons.AddRange(jetons);
                    break;
                case "decors":
                    foreach (var d in jetons) decors[d] = p[1];
                    break;
            }
        }
        return (morceaux, decors);
    }

    // La suite se répète jusqu'au bout du morceau ; une note tenue au bout repart au début.
    public static List<NoteBoucle> Notes(IReadOnlyList<string> jetons, int pas)
    {
        var e = new string[pas];
        for (int k = 0; k < pas; k++) e[k] = jetons[k % jetons.Count];
        var notes = new List<NoteBoucle>();
        for (int k = 0; k < pas; k++)
        {
            if (e[k] is "-" or ".") continue;
            int longueur = 1;
            while (longueur < pas && e[(k + longueur) % pas] == "-") longueur++;
            var f = e[k].Split('>');
            notes.Add(new NoteBoucle(k, longueur, Frequence(f[0]), Frequence(f[^1])));
        }
        return notes;
    }

    // Échantillons 16 bits de la boucle au réglage « normale » ; le dernier enchaîne sur le premier.
    public static short[] Synthetiser(Morceau m)
    {
        int pasEch = Taux * m.Ms / 1000, total = pasEch * m.Pas;
        var acc = new long[total];
        foreach (var v in m.Voix)
        {
            foreach (var note in Notes(v.Jetons, m.Pas))
            {
                int s0 = note.Pas * pasEch, n = note.Longueur * pasEch;
                if (v.Tenue > 0) n = Math.Min(n, Taux * v.Tenue / 1000);
                int a = Math.Min(n / 2, Taux * v.Attaque / 1000), r = Math.Min(n / 2, Taux * v.Relache / 1000);
                long phase = 0;
                int lfsr = 1;
                for (int i = 0; i < n; i++)
                {
                    long fm = (note.F0 * (n - i) + note.F1 * i) / n;
                    long inc = fm * 4294967296L / (Taux * 1000L);
                    long avant = phase;
                    phase = (phase + inc) & 0xFFFFFFFFL;
                    int p = (int)(phase >> 16);
                    long x;
                    if (v.Onde == "tri")
                    {
                        int t = p < 32768 ? p : 65535 - p;
                        x = ((t >> 11) * 2 - 15) * 2184L;
                    }
                    else if (v.Onde == "puls") x = p < 16384 ? 24000 : -8000;
                    else
                    {
                        if (phase < avant)
                        {
                            int b = (lfsr ^ (lfsr >> 1)) & 1;
                            lfsr = (lfsr >> 1) | (b << 14);
                        }
                        x = (lfsr & 1) != 0 ? 20000 : -20000;
                    }
                    long e = 4096;
                    if (i < a) e = 4096L * i / a;
                    if (r > 0 && i >= n - r)
                    {
                        long q = n - i;
                        e = Math.Min(e, 4096L * q * q / ((long)r * r));
                    }
                    e = e * (4096 - (long)v.Declin * i / n) / 4096;
                    acc[(s0 + i) % total] += (x * e * v.Volume * 10) >> 24;
                }
            }
        }
        // Passe-bas en anneau : un tour pour mettre le filtre en régime, le second donne la sortie.
        var sortie = new short[total];
        long y1 = 0, y2 = 0;
        for (int tour = 0; tour < 2; tour++)
            for (int i = 0; i < total; i++)
            {
                y1 += (((acc[i] << 8) - y1) * m.Filtre) >> 8;
                y2 += ((y1 - y2) * m.Filtre) >> 8;
                if (tour == 1) sortie[i] = (short)Math.Clamp(y2 >> 8, -32767, 32767);
            }
        return sortie;
    }

    // Quelle musique pour quelle campagne : le prologue a la sienne, les autres celle de leur ton.
    public static string? Pour(string? campagne, string? ton) =>
        campagne == "prologue" ? "prologue" : ton is "humour" or "mystere" or "emotion" ? ton : null;

    public static string? Ambiance(string? decor) =>
        decor is not null && Catalogue().Decors.TryGetValue(decor, out var a) ? a : null;

    // Gain sur 65536 selon le réglage : « discrète » = × 3 / 8 (environ -8,5 dB).
    public static int Gain(string niveau) => niveau switch { "normale" => 65536, "discrete" => 65536 * 3 / 8, _ => 0 };

    // ---- Lecture (overlay) ----

    private static (Dictionary<string, Morceau> Morceaux, Dictionary<string, string> Decors)? _catalogue;
    private static readonly Dictionary<string, short[]> Boucles = new();

    private static (Dictionary<string, Morceau> Morceaux, Dictionary<string, string> Decors) Catalogue()
    {
        lock (Boucles) return _catalogue ??= Lire(LireRessource());
    }

    private static readonly HashSet<string> EnCalcul = new();

    // La boucle si elle est prête ; sinon son calcul part à côté (une fraction de seconde) et le prochain tour la prend.
    internal static short[]? Boucle(string id)
    {
        var c = Catalogue();
        lock (Boucles)
        {
            if (Boucles.TryGetValue(id, out var s)) return s;
            if (!c.Morceaux.TryGetValue(id, out var m) || !EnCalcul.Add(id)) return null;
            ThreadPool.QueueUserWorkItem(_ =>
            {
                var b = Synthetiser(m);
                lock (Boucles) { Boucles[id] = b; EnCalcul.Remove(id); }
            });
            return null;
        }
    }

    private static string LireRessource()
    {
        using var st = Assembly.GetExecutingAssembly().GetManifestResourceStream("pilou:musiques.txt");
        if (st is null) return "";
        using var r = new StreamReader(st);
        return r.ReadToEnd();
    }

}

// La table de mixage (sans audio : testable) : une couche par boucle, chacune avec son gain qui glisse vers sa cible.
// Fondu d'entrée de 1,5 s, de sortie de 1 s ; changer de musique ou de décor croise les deux boucles.
public sealed class Melangeur
{
    public const int Entree = Musique.Taux * 3 / 2, Sortie = Musique.Taux;

    private sealed class Couche
    {
        public required string Id;
        public required bool EstMusique;
        public required short[] S;
        public int Pos, Gain, Cible;
    }

    private readonly Func<string, short[]?> _boucle;
    private readonly List<Couche> _couches = new();

    public Melangeur(Func<string, short[]?> boucle) => _boucle = boucle;

    public bool Silencieux { get { lock (_couches) return _couches.Count == 0; } }

    public void Viser(string? musique, string? ambiance, int gain)
    {
        lock (_couches)
        {
            Regler(true, musique, gain);
            Regler(false, ambiance, gain);
        }
    }

    private void Regler(bool estMusique, string? id, int gain)
    {
        bool present = false;
        foreach (var c in _couches.Where(c => c.EstMusique == estMusique))
        {
            bool garde = c.Id == id && gain > 0;
            c.Cible = garde ? gain : 0;
            present |= garde;
        }
        if (present || id is null || gain <= 0) return;
        if (_boucle(id) is { Length: > 0 } s) _couches.Add(new Couche { Id = id, EstMusique = estMusique, S = s, Cible = gain });
    }

    public void Remplir(short[] bloc)
    {
        lock (_couches)
        {
            Array.Clear(bloc);
            var somme = new long[bloc.Length];
            foreach (var c in _couches)
            {
                int monte = Math.Max(1, (c.Cible + Entree - 1) / Entree), descend = (65536 + Sortie - 1) / Sortie;
                for (int i = 0; i < bloc.Length; i++)
                {
                    if (c.Gain < c.Cible) c.Gain = Math.Min(c.Cible, c.Gain + monte);
                    else if (c.Gain > c.Cible) c.Gain = Math.Max(c.Cible, c.Gain - descend);
                    somme[i] += ((long)c.S[c.Pos] * c.Gain) >> 16;
                    if (++c.Pos == c.S.Length) c.Pos = 0;
                }
            }
            for (int i = 0; i < bloc.Length; i++) bloc[i] = (short)Math.Clamp(somme[i], -32767, 32767);
            _couches.RemoveAll(c => c.Gain == 0 && c.Cible == 0);
        }
    }
}
