namespace PilouBureau;

// Saynètes de repos (docs/SPRITES.md, « Saynètes de repos ») : la banque assets/saynetes.txt, le tirage pondéré et
// ce qu'une saynète impose à Pilou à chaque instant. Mêmes règles que outils/sprites/saynetes.py et Saynetes.java,
// en arithmétique entière (divisions vers le bas) : saynetes-reference.txt, relu par SaynetesTests.cs et
// SaynetesTest.java. Aucun gain (xp, pièces) n'est lié aux saynètes.
public static class Saynetes
{
    public static readonly string[] Continus = { "assis", "saut", "etire", "penche" };

    // Contexte du tirage : heure, mois (1…12), stade, objets portés, compagnon porté, main libre, tu travailles.
    public sealed record Contexte(int Heure, int Mois, int Stade, IReadOnlyCollection<string> Objets, bool Compagnon,
        bool MainLibre, bool Travail);

    // Ce que la saynète impose : continus en millièmes (assis 0…1000, saut, étirement, penché), le reste tel quel.
    public sealed record Jeu(int Assis, int Saut, int Etire, int Penche, string Expr, int Regard, int RegardY,
        bool Cligne, bool Baille, bool Salue, IReadOnlyList<string> Objets);

    public sealed class Saynete
    {
        public string Id = "";
        public int Poids, Duree;
        internal readonly List<(int A, int B)> Heures = new();
        internal readonly List<int> Mois = new();
        internal (int A, int B)? Stades;
        internal string[] ObjetsRequis = Array.Empty<string>();
        internal bool Compagnon, MainLibre, Repos;
        public bool Tourne;
        internal readonly Dictionary<string, List<(int T, int V)>> Cles = Continus.ToDictionary(k => k, _ => new List<(int, int)>());
        internal readonly List<(int T, string V)> Expr = new();
        internal readonly Dictionary<string, List<(int T, int V)>> Entiers = new()
        {
            ["regard"] = new(), ["regard_y"] = new(), ["cligne"] = new(), ["baille"] = new(), ["salue"] = new(),
        };
        internal readonly List<(int T, string[] V)> Objets = new();
    }

    private static long Div(long a, long b) => a / b - ((a % b != 0) && ((a < 0) != (b < 0)) ? 1 : 0);

    public static List<Saynete> Lire(string texte)
    {
        var banque = new List<Saynete>();
        foreach (var brut in texte.Replace("\r", "").Split('\n'))
        {
            var l = brut.Trim();
            if (l.Length == 0 || l.StartsWith('#')) continue;
            var m = l.Split(' ', StringSplitOptions.RemoveEmptyEntries);
            if (m[0] == "saynete")
            {
                var s = new Saynete { Id = m[1], Poids = int.Parse(m[2]), Duree = int.Parse(m[3]) };
                foreach (var q in m.Skip(4))
                {
                    int i = q.IndexOf('=');
                    string k = i < 0 ? q : q[..i], v = i < 0 ? "" : q[(i + 1)..];
                    switch (k)
                    {
                        case "heure":
                            foreach (var p in v.Split(','))
                            {
                                var ab = p.Split('-');
                                s.Heures.Add((int.Parse(ab[0]), int.Parse(ab[1])));
                            }
                            break;
                        case "mois": s.Mois.AddRange(v.Split(',').Select(int.Parse)); break;
                        case "stade":
                            var st = v.Split('-');
                            s.Stades = (int.Parse(st[0]), int.Parse(st[1]));
                            break;
                        case "objet": s.ObjetsRequis = v.Split('|'); break;
                        case "compagnon": s.Compagnon = true; break;
                        case "mainlibre": s.MainLibre = true; break;
                        case "repos": s.Repos = true; break;
                        case "tourne": s.Tourne = true; break;
                    }
                }
                banque.Add(s);
                continue;
            }
            var c = banque[^1];
            int t = int.Parse(m[0]);
            foreach (var kv in m.Skip(1))
            {
                int i = kv.IndexOf('=');
                string k = kv[..i], v = kv[(i + 1)..];
                if (c.Cles.TryGetValue(k, out var table)) table.Add((t, int.Parse(v)));
                else if (k == "objets") c.Objets.Add((t, v == "-" ? Array.Empty<string>() : v.Split(',')));
                else if (k == "expr") c.Expr.Add((t, v));
                else if (c.Entiers.TryGetValue(k, out var e)) e.Add((t, int.Parse(v)));
            }
        }
        return banque;
    }

    private static List<Saynete>? _commune;

    // La banque embarquée (ressource « pilou:saynetes.txt ») ; vide si elle manque.
    public static List<Saynete> Commune => _commune ??= Lire(LireRessource());

    private static string LireRessource()
    {
        using var st = typeof(Saynetes).Assembly.GetManifestResourceStream("pilou:saynetes.txt");
        if (st is null) return "";
        using var r = new System.IO.StreamReader(st);
        return r.ReadToEnd();
    }

    public static bool Permise(Saynete s, Contexte c)
    {
        if (s.Heures.Count > 0 && !s.Heures.Any(h => h.A <= h.B ? h.A <= c.Heure && c.Heure < h.B : c.Heure >= h.A || c.Heure < h.B))
            return false;
        if (s.Mois.Count > 0 && !s.Mois.Contains(c.Mois)) return false;
        if (s.Stades is { } st && (c.Stade < st.A || c.Stade > st.B)) return false;
        if (s.ObjetsRequis.Length > 0 && !s.ObjetsRequis.Any(c.Objets.Contains)) return false;
        if (s.Compagnon && !c.Compagnon) return false;
        if (s.MainLibre && !c.MainLibre) return false;
        if (s.Repos && c.Travail) return false;
        return true;
    }

    // L'identifiant tiré (u : 0…9999) parmi les saynètes permises, sauf « evite » ; "" s'il n'y en a pas.
    public static string Tirer(IReadOnlyList<Saynete> banque, int u, Contexte c, string evite = "")
    {
        var ok = banque.Where(s => s.Id != evite && Permise(s, c)).ToList();
        long total = ok.Sum(s => (long)s.Poids);
        if (total == 0) return "";
        long x = Div(u * total, 10000);
        foreach (var s in ok)
        {
            if (x < s.Poids) return s.Id;
            x -= s.Poids;
        }
        return ok[^1].Id;
    }

    public static Saynete? Trouver(IReadOnlyList<Saynete> banque, string id) => banque.FirstOrDefault(s => s.Id == id);

    internal static int Cles(List<(int T, int V)> table, long d)
    {
        if (table.Count == 0) return 0;
        if (d <= table[0].T) return d == table[0].T ? table[0].V : 0;
        for (int i = 0; i + 1 < table.Count; i++)
        {
            var (t0, v0) = table[i];
            var (t1, v1) = table[i + 1];
            if (d < t1) return (int)(v0 + Div((long)(v1 - v0) * (d - t0), t1 - t0));
        }
        return table[^1].V;
    }

    private static T Dernier<T>(List<(int T, T V)> table, long d, T defaut)
    {
        var v = defaut;
        foreach (var (t, x) in table)
            if (t <= d) v = x;
        return v;
    }

    // Ce que la saynète impose d ms après son début ; null si elle est finie, ou au niveau « aucune ».
    public static Jeu? Jouer(Saynete s, long d, string niveau, int sens = 1)
    {
        if (niveau == AnimationsCampagne.Aucune || d < 0 || d >= s.Duree) return null;
        bool completes = niveau == AnimationsCampagne.Completes;
        int saut = completes ? Cles(s.Cles["saut"], d) : 0, etire = completes ? Cles(s.Cles["etire"], d) : 0;
        int penche = completes ? Cles(s.Cles["penche"], d) : 0;
        int regard = Dernier(s.Entiers["regard"], d, 0);
        if (s.Tourne && sens < 0)
        {
            regard = -regard;
            penche = -penche;
        }
        return new Jeu(Cles(s.Cles["assis"], d), saut, etire, penche, Dernier(s.Expr, d, "repos"), regard,
            Dernier(s.Entiers["regard_y"], d, 0), Dernier(s.Entiers["cligne"], d, 0) != 0, Dernier(s.Entiers["baille"], d, 0) != 0,
            Dernier(s.Entiers["salue"], d, 0) != 0, Dernier(s.Objets, d, Array.Empty<string>()));
    }
}
