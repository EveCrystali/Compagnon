using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Security.Cryptography;

namespace PilouBureau;

// Les sons de Pilou (docs/SONS.md). Décrits dans assets/sons.txt, synthétisés ici en entiers, exactement comme
// Sons.java et outils/sons/sons.py (empreintes dans outils/sons/sons-reference.txt). Lus par Windows lui-même
// (PlaySound de winmm, depuis la mémoire), sans aucune bibliothèque.
public enum Son { Caresse, Mot, Aventure, Choix, Achat, Peche, Expedition, Campagne, Palier, Succes }

public readonly record struct NoteSon(int Debut, int Duree, int F0, int F1, string Onde, int Volume);

public static class Sons
{
    public const int Taux = 22050;
    private const int AttaqueMs = 4, RelacheMs = 60, QueueMs = 20, FonduMs = 8, Filtre = 120, Discret = 3;

    // Réglage « Sons » : aucun, discrets, normaux (par défaut).
    public static readonly string[] Niveaux = { "aucun", "discrets", "normaux" };

    public static string Id(Son s) => s.ToString().ToLowerInvariant();

    // Sons « spontanés » : ils arrivent sans geste de la personne, donc jamais pendant la saisie.
    public static bool Spontane(Son s) => s is Son.Mot or Son.Expedition or Son.Campagne or Son.Palier or Son.Succes;

    public static Dictionary<string, List<NoteSon>> Lire(string texte)
    {
        var sons = new Dictionary<string, List<NoteSon>>();
        foreach (var brute in texte.Split('\n'))
        {
            var l = brute.Trim();
            if (l.Length == 0 || l.StartsWith('#')) continue;
            var p = l.Split('|').Select(x => x.Trim()).ToArray();
            if (p.Length != 6) continue;
            var f = p[3].Split('>');
            var note = new NoteSon(int.Parse(p[1]), int.Parse(p[2]), int.Parse(f[0]), int.Parse(f[^1]), p[4], int.Parse(p[5]));
            if (!sons.TryGetValue(p[0], out var liste)) sons[p[0]] = liste = new();
            liste.Add(note);
        }
        return sons;
    }

    // Échantillons 16 bits du son au réglage « normaux ». Tout en entiers : >> arrondit vers le bas en C#, en Java
    // et en Python, et aucune division ne porte sur un nombre négatif.
    public static short[] Synthetiser(IReadOnlyList<NoteSon> notes)
    {
        int fin = 0;
        foreach (var n in notes) fin = Math.Max(fin, Taux * n.Debut / 1000 + Taux * n.Duree / 1000);
        fin += Taux * QueueMs / 1000;
        var acc = new long[fin];
        int a = Taux * AttaqueMs / 1000;
        foreach (var note in notes)
        {
            int s0 = Taux * note.Debut / 1000, n = Taux * note.Duree / 1000;
            int r = Math.Min(n / 2, Taux * RelacheMs / 1000);
            long phase = 0;
            int lfsr = 1;
            for (int i = 0; i < n; i++)
            {
                long fm = ((long)note.F0 * 1000 * (n - i) + (long)note.F1 * 1000 * i) / n;
                long inc = fm * 4294967296L / (Taux * 1000L);
                long avant = phase;
                phase = (phase + inc) & 0xFFFFFFFFL;
                int p = (int)(phase >> 16);
                long v;
                if (note.Onde == "tri")
                {
                    int t = p < 32768 ? p : 65535 - p;
                    v = ((t >> 11) * 2 - 15) * 2184L;
                }
                else if (note.Onde == "puls") v = p < 16384 ? 24000 : -8000;
                else
                {
                    if (phase < avant)
                    {
                        int b = (lfsr ^ (lfsr >> 1)) & 1;
                        lfsr = (lfsr >> 1) | (b << 14);
                    }
                    v = (lfsr & 1) != 0 ? 20000 : -20000;
                }
                long e = 4096;
                if (i < a) e = 4096L * i / a;
                if (i >= n - r)
                {
                    long k = n - i;
                    e = Math.Min(e, 4096L * k * k / ((long)r * r));
                }
                e = e * (4096 - 1024L * i / n) / 4096;
                acc[s0 + i] += (v * e * note.Volume * 10) >> 22;
            }
        }
        var sortie = new short[fin];
        long y1 = 0, y2 = 0;
        for (int i = 0; i < fin; i++)
        {
            long x = acc[i] << 8;
            y1 += ((x - y1) * Filtre) >> 8;
            y2 += ((y1 - y2) * Filtre) >> 8;
            sortie[i] = (short)Math.Clamp(y2 >> 8, -32767, 32767);
        }
        int f = Taux * FonduMs / 1000;
        for (int i = fin - f; i < fin; i++)
        {
            long g = ((long)(fin - 1 - i) << 16) / f;
            sortie[i] = (short)((sortie[i] * g) >> 16);
        }
        return sortie;
    }

    // « Discrets » : environ -14 dB, vraiment bas.
    public static short[] Adoucir(short[] s) => s.Select(x => (short)((x * Discret) >> 4)).ToArray();

    public static string Empreinte(short[] s)
    {
        var o = new byte[s.Length * 2];
        for (int i = 0; i < s.Length; i++)
        {
            o[i * 2] = (byte)s[i];
            o[i * 2 + 1] = (byte)(s[i] >> 8);
        }
        return Convert.ToHexString(SHA256.HashData(o)).ToLowerInvariant();
    }

    public static byte[] Wav(short[] s)
    {
        using var m = new MemoryStream();
        using var w = new BinaryWriter(m);
        w.Write("RIFF"u8); w.Write(36 + s.Length * 2); w.Write("WAVE"u8);
        w.Write("fmt "u8); w.Write(16); w.Write((short)1); w.Write((short)1); w.Write(Taux); w.Write(Taux * 2);
        w.Write((short)2); w.Write((short)16);
        w.Write("data"u8); w.Write(s.Length * 2);
        foreach (var x in s) w.Write(x);
        w.Flush();
        return m.ToArray();
    }

    // ---- Lecture (overlay) ----

    private static Dictionary<string, List<NoteSon>>? _catalogue;
    private static readonly Dictionary<(Son, bool), GCHandle> Prets = new();
    private static readonly object Verrou = new();
    private static Func<string> _niveau = () => "aucun";
    private static Func<string> _musique = () => "aucune";
    private static Func<bool> _cache = () => true, _saisie = () => false;
    private static readonly GardeSons Garde = new();

    // Branché une fois au démarrage : le réglage, « Pilou est caché » (plein écran, présentation, visio, caché à la
    // main), « on tape » et le réglage de la musique (Musique.cs).
    public static void Brancher(Func<string> niveau, Func<bool> cache, Func<bool> saisie, Func<string>? musique = null)
    {
        _niveau = niveau;
        _cache = cache;
        _saisie = saisie;
        if (musique is not null) _musique = musique;
    }

    internal static bool Cache() => _cache();
    internal static string NiveauMusique() => _musique();

    public static void Jouer(Son son)
    {
        try
        {
            var niveau = _niveau();
            if (!Garde.Peut(son, Environment.TickCount64, niveau, _cache(), _saisie())) return;
            var h = Pret(son, niveau == "discrets");
            if (h is { } g) PlaySound(g.AddrOfPinnedObject(), IntPtr.Zero, SndMemory | SndAsync | SndNoDefault);
        }
        catch (Exception e) when (e is DllNotFoundException or EntryPointNotFoundException or InvalidOperationException)
        {
            // pas de sortie audio : silence
        }
    }

    // Le WAV du son, épinglé en mémoire pour toute la vie de l'appli (PlaySound le lit pendant qu'il joue).
    private static GCHandle? Pret(Son son, bool discret)
    {
        lock (Verrou)
        {
            if (Prets.TryGetValue((son, discret), out var h)) return h;
            _catalogue ??= Lire(LireRessource());
            if (!_catalogue.TryGetValue(Id(son), out var notes)) return null;
            var s = Synthetiser(notes);
            h = GCHandle.Alloc(Wav(discret ? Adoucir(s) : s), GCHandleType.Pinned);
            Prets[(son, discret)] = h;
            return h;
        }
    }

    private static string LireRessource()
    {
        using var st = Assembly.GetExecutingAssembly().GetManifestResourceStream("pilou:sons.txt");
        if (st is null) return "";
        using var r = new StreamReader(st);
        return r.ReadToEnd();
    }

    private const uint SndAsync = 0x0001, SndNoDefault = 0x0002, SndMemory = 0x0004;

    [DllImport("winmm.dll", EntryPoint = "PlaySoundW", CharSet = CharSet.Unicode)]
    private static extern bool PlaySound(IntPtr son, IntPtr module, uint options);
}

// Quand un son a le droit de partir (sans WPF : testable). Rien quand le réglage est « aucun », rien quand Pilou est
// caché (plein écran, présentation, visio), rien de spontané pendant la saisie, jamais en rafale.
public sealed class GardeSons
{
    public const long Espacement = 1200;      // entre deux sons, quels qu'ils soient (ms)
    public const long MemeSon = 4000;         // avant de rejouer le même son (clics répétés sur Pilou…)
    public const int SpontanesParHeure = 6;

    private long _dernier = long.MinValue / 2;
    private readonly Dictionary<Son, long> _parSon = new();
    private readonly Queue<long> _spontanes = new();

    public bool Peut(Son son, long t, string niveau, bool cache, bool saisie)
    {
        if (niveau is not ("discrets" or "normaux") || cache) return false;
        bool spontane = Sons.Spontane(son);
        if (spontane && saisie) return false;
        if (t - _dernier < Espacement) return false;
        if (_parSon.TryGetValue(son, out var d) && t - d < MemeSon) return false;
        while (_spontanes.Count > 0 && t - _spontanes.Peek() >= 3_600_000) _spontanes.Dequeue();
        if (spontane && _spontanes.Count >= SpontanesParHeure) return false;
        _dernier = t;
        _parSon[son] = t;
        if (spontane) _spontanes.Enqueue(t);
        return true;
    }
}
