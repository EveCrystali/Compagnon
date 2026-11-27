using System.Globalization;
using PilouBureau;
using static PilouBureau.Campagnes;

// Simulateur rapide et exact d'une partie (miroir de Campagnes.Moteur) : mêmes check-points, mêmes effets et mêmes
// tirages (graine de la partie, compteur de tirages), sans horloge ni journal. Il sert à chercher, par milliers de
// marches à graine fixe, des parcours qui couvrent chaque nœud, chaque arête et chaque fin ; le vrai moteur rejoue
// ensuite ces parcours (ParcoursTests) et doit trouver, pas à pas, exactement les mêmes états.
public sealed class Simu
{
    private static readonly CultureInfo Ci = CultureInfo.InvariantCulture;
    public readonly Campagne C;
    private readonly Dictionary<string, int> _drapeau = new(StringComparer.Ordinal), _objet = new(StringComparer.Ordinal);
    public readonly Dictionary<string, int> Statique;

    public Simu(Campagne c, IEnumerable<string>? vers = null)
    {
        C = c;
        foreach (var n in c.Noeuds.Values)
            foreach (var e in n.Effets.Concat(n.Options.SelectMany(o => o.Effets)))
                if (e.Sorte == "drapeau") _drapeau.TryAdd(e.Nom, _drapeau.Count);
        foreach (var o in c.Objets) _objet.TryAdd(o.Id, _objet.Count);
        if (_drapeau.Count > 64 || _objet.Count > 64) throw new InvalidOperationException("trop de drapeaux ou d'objets pour le simulateur");
        Statique = Distances(this, vers ?? c.Noeuds.Values.Where(n => n.Type == "fin").Select(n => n.Id));
    }

    public sealed class Etat
    {
        public string Noeud = "";
        public Dictionary<string, int> Vars = new(StringComparer.Ordinal);
        public ulong O, D;
        public bool AvecCp;
        public string CpNoeud = "";
        public Dictionary<string, int> CpVars = new(StringComparer.Ordinal);
        public ulong CpO, CpD;
        public int Tirages;
        public bool Geste = true;
        public Phase Phase;
        public int Minutes; // attente ou repos en cours
        public HashSet<string> Credits = new(StringComparer.Ordinal);
    }

    // Un pas d'une marche : où l'on est (phase, vue), ce qu'on y fait, ce que cela coûte en temps.
    public sealed record Pas(Phase Phase, string Vue, string Action, int Minutes);

    public sealed class Marche
    {
        public string Graine = "";
        public int Politique;
        public readonly List<Pas> Pas = new();
        public readonly HashSet<string> Aretes = new(StringComparer.Ordinal), Noeuds = new(StringComparer.Ordinal);
        public readonly HashSet<string> Credits = new(StringComparer.Ordinal);
        public string Fin = "", Issue = "";
        public long Minutes;
        public int Choix, Attentes, Longues, Echecs, Abandons, Po, Xp;
        public readonly List<string> Defauts = new();
    }

    public string Vue(Etat s) =>
        s.Noeud + "|" + string.Join(",", s.Vars.OrderBy(kv => kv.Key, StringComparer.Ordinal).Select(kv => kv.Key + ":" + kv.Value.ToString(Ci))) + "|"
        + string.Join(",", Noms(_objet, s.O)) + "|" + string.Join(",", Noms(_drapeau, s.D));

    private static IEnumerable<string> Noms(Dictionary<string, int> index, ulong bits) =>
        index.Where(kv => (bits & (1UL << kv.Value)) != 0).Select(kv => kv.Key).OrderBy(x => x, StringComparer.Ordinal);

    private bool Vrai(Condition? k, Etat s)
    {
        if (k is null) return true;
        switch (k.Sorte)
        {
            case "var":
                int v = s.Vars.GetValueOrDefault(k.Nom);
                return (k.Min is null || v >= k.Min) && (k.Max is null || v <= k.Max);
            case "objet": return _objet.TryGetValue(k.Nom, out var o) && (s.O & (1UL << o)) != 0;
            case "drapeau": return _drapeau.TryGetValue(k.Nom, out var d) && (s.D & (1UL << d)) != 0;
            case "non": return k.Sous.Count == 1 && !Vrai(k.Sous[0], s);
            case "tous": return k.Sous.All(x => Vrai(x, s));
            case "un": return k.Sous.Any(x => Vrai(x, s));
            default: return false;
        }
    }

    private void Appliquer(IEnumerable<Campagnes.Effet> effets, Etat s)
    {
        foreach (var e in effets)
        {
            if (e.Sorte == "var") s.Vars[e.Nom] = s.Vars.GetValueOrDefault(e.Nom) + e.Valeur;
            else if (e.Sorte == "objet" && _objet.TryGetValue(e.Nom, out var o))
                s.O = e.Valeur != 0 ? s.O | (1UL << o) : s.O & ~(1UL << o);
            else if (e.Sorte == "drapeau" && _drapeau.TryGetValue(e.Nom, out var d))
                s.D = e.Valeur != 0 ? s.D | (1UL << d) : s.D & ~(1UL << d);
        }
    }

    private int Tirer(string graine, Etat s, int max) => Tirage(graine, s.Tirages++).Suivant(max);

    private void Partir(string graine, Etat s, Noeud n)
    {
        int minutes = Math.Max(1, n.DureeMin);
        if (n.DureeMax > n.DureeMin) minutes = Tirage(graine, s.Tirages++).Entre(Math.Max(1, n.DureeMin), n.DureeMax);
        s.Minutes = minutes;
        s.Phase = Phase.Attente;
    }

    // Entrer dans un nœud (Mode.Neuf du moteur) et suivre jusqu'au prochain arrêt.
    private void Entrer(string graine, Etat s, string id, Marche m)
    {
        for (int pas = 0; pas < 4000; pas++)
        {
            if (C.Noeud(id) is not { } n)
            {
                s.Phase = Phase.Cassee;
                m.Defauts.Add($"nœud absent : {id}");
                return;
            }
            s.Noeud = id;
            m.Noeuds.Add(id);
            if (n.Checkpoint || !s.AvecCp)
            {
                s.AvecCp = true;
                (s.CpNoeud, s.CpVars, s.CpO, s.CpD) = (id, new(s.Vars, StringComparer.Ordinal), s.O, s.D);
            }
            Appliquer(n.Effets, s);
            if (n.Type == "fin" || !n.Recompense.Vide) s.Credits.Add(id);
            switch (n.Type)
            {
                case "recit":
                    id = n.Suite;
                    continue;
                case "choix":
                    s.Phase = Phase.Choix;
                    return;
                case "attente":
                    if (s.Geste) Partir(graine, s, n);
                    else s.Phase = Phase.Depart;
                    return;
                case "epreuve" when JeuAuto(n.Jeu):
                {
                    int bonus = n.Bonus == "" ? 0 : s.Vars.GetValueOrDefault(n.Bonus);
                    bool ok = Tirage(graine, s.Tirages).Suivant(100) < ChanceDe(n.Difficulte, bonus);
                    s.Tirages++;
                    m.Aretes.Add($"e:{id}:{(ok ? "ok" : "ko")}");
                    id = ok ? n.Reussite : n.Echec;
                    continue;
                }
                case "epreuve":
                    s.Phase = Phase.Epreuve;
                    return;
                case "hasard":
                {
                    var possibles = n.Issues.Select((x, i) => (x, i)).Where(p => Vrai(p.x.Si, s)).ToList();
                    if (possibles.Count == 0)
                    {
                        m.Defauts.Add($"{id} : hasard sans issue possible ({Vue(s)})");
                        possibles = n.Issues.Select((x, i) => (x, i)).ToList();
                    }
                    int tire = Tirer(graine, s, possibles.Sum(p => Math.Max(1, p.x.Poids)));
                    var issue = possibles[^1];
                    foreach (var p in possibles)
                    {
                        tire -= Math.Max(1, p.x.Poids);
                        if (tire < 0)
                        {
                            issue = p;
                            break;
                        }
                    }
                    m.Aretes.Add($"h:{id}:{issue.i}");
                    id = issue.x.Vers;
                    continue;
                }
                case "echec":
                    s.Minutes = Math.Max(1, n.ReposMin);
                    s.Phase = Phase.Repos;
                    return;
                case "fin":
                    s.Phase = Phase.Fin;
                    return;
                default:
                    s.Phase = Phase.Cassee;
                    m.Defauts.Add($"{id} : type {n.Type}");
                    return;
            }
        }
        s.Phase = Phase.Cassee;
        m.Defauts.Add($"{id} : boucle sans arrêt");
    }

    private void Revenir(string graine, Etat s, Marche m, bool geste)
    {
        s.Vars = new(s.CpVars, StringComparer.Ordinal);
        s.O = s.CpO;
        s.D = s.CpD;
        s.Geste = geste;
        Entrer(graine, s, s.CpNoeud, m);
    }

    public List<(int Rang, Option O)> Visibles(Etat s) =>
        C.Noeud(s.Noeud)!.Options.Select((o, i) => (i, o)).Where(x => Vrai(x.o.Si, s)).ToList();

    // Une marche entière. Politique : 0 au hasard ; 1 guidée vers les cibles statiques (Statique) avec un peu de hasard.
    // Épreuves : réussies deux fois sur trois (ou laissées aux dés) ; abandons : une fois sur 30 décisions environ.
    public Marche Jouer(string graine, ulong choixGraine, int politique, bool abandons, bool auDe, int maxPas = 3000)
    {
        var m = new Marche { Graine = graine, Politique = politique };
        var h = new Hasard(choixGraine);
        var s = new Etat();
        foreach (var kv in C.Variables) s.Vars[kv.Key] = kv.Value;
        Entrer(graine, s, C.Depart, m);
        int decisions = 0;
        for (int i = 0; i < maxPas; i++)
        {
            var n = C.Noeud(s.Noeud)!;
            string vue = Vue(s);
            if (s.Phase is Phase.Fin or Phase.Cassee) break;
            if (abandons && s.Phase is Phase.Choix or Phase.Attente or Phase.Depart && h.Suivant(30) == 0 && m.Abandons < 3)
            {
                m.Pas.Add(new Pas(s.Phase, vue, "abandon", 0));
                m.Abandons++;
                Revenir(graine, s, m, true);
                continue;
            }
            switch (s.Phase)
            {
                case Phase.Choix:
                {
                    var v = Visibles(s);
                    if (v.Count == 0)
                    {
                        m.Defauts.Add($"{n.Id} : aucune option proposée ({vue})");
                        s.Phase = Phase.Cassee;
                        break;
                    }
                    var (rang, o) = politique == 1 && h.Suivant(5) != 0 ? Meilleure(v, s, h) : v[h.Suivant(v.Count)];
                    m.Pas.Add(new Pas(s.Phase, vue, "o:" + o.Id, 0));
                    m.Aretes.Add($"o:{n.Id}:{rang}");
                    m.Choix++;
                    decisions++;
                    s.Geste = true;
                    Appliquer(o.Effets, s);
                    Entrer(graine, s, o.Vers, m);
                    break;
                }
                case Phase.Epreuve:
                {
                    bool ok;
                    string action;
                    if (auDe && h.Suivant(3) == 0)
                    {
                        int bonus = n.Bonus == "" ? 0 : s.Vars.GetValueOrDefault(n.Bonus);
                        ok = Tirage(graine, s.Tirages).Suivant(100) < ChanceDe(n.Difficulte, bonus);
                        action = "de";
                    }
                    else
                    {
                        ok = politique == 1 && h.Suivant(5) != 0
                            ? (Statique.GetValueOrDefault(n.Reussite, int.MaxValue) <= Statique.GetValueOrDefault(n.Echec, int.MaxValue)) == (h.Suivant(8) != 0)
                            : h.Suivant(3) != 0;
                        action = ok ? "ok" : "ko";
                    }
                    m.Pas.Add(new Pas(s.Phase, vue, action, 0));
                    m.Aretes.Add($"e:{n.Id}:{(ok ? "ok" : "ko")}");
                    decisions++;
                    s.Tirages++;
                    s.Geste = true;
                    Entrer(graine, s, ok ? n.Reussite : n.Echec, m);
                    break;
                }
                case Phase.Depart:
                    m.Pas.Add(new Pas(s.Phase, vue, "suite", 0));
                    decisions++;
                    Partir(graine, s, n);
                    break;
                case Phase.Attente:
                case Phase.Repos:
                {
                    m.Pas.Add(new Pas(s.Phase, vue, "temps", s.Minutes));
                    m.Minutes += s.Minutes;
                    if (s.Phase == Phase.Attente)
                    {
                        m.Attentes++;
                        if (s.Minutes >= 60) m.Longues++;
                        m.Aretes.Add($"s:{n.Id}");
                        s.Geste = false;
                        Entrer(graine, s, n.Suite, m);
                    }
                    else
                    {
                        m.Echecs++;
                        m.Aretes.Add($"r:{n.Id}");
                        Revenir(graine, s, m, false);
                    }
                    break;
                }
            }
        }
        m.Pas.Add(new Pas(s.Phase, Vue(s), "", 0));
        if (s.Phase == Phase.Fin)
        {
            m.Fin = s.Noeud;
            m.Issue = C.Noeud(s.Noeud)!.Issue;
        }
        else if (s.Phase != Phase.Cassee) m.Defauts.Add($"pas de fin après {maxPas} pas ({Vue(s)})");
        m.Credits.UnionWith(s.Credits);
        m.Po = m.Credits.Sum(id => C.Noeud(id)!.Recompense.Po);
        m.Xp = m.Credits.Sum(id => C.Noeud(id)!.Recompense.Xp);
        return m;
    }

    private (int, Option) Meilleure(List<(int Rang, Option O)> v, Etat s, Hasard h)
    {
        int best = v.Min(x => Statique.GetValueOrDefault(x.O.Vers, int.MaxValue));
        var l = v.Where(x => Statique.GetValueOrDefault(x.O.Vers, int.MaxValue) == best).ToList();
        return l[h.Suivant(l.Count)];
    }

    // Distance statique (en décisions, conditions ignorées) de chaque nœud aux cibles.
    public static Dictionary<string, int> Distances(Simu s, IEnumerable<string> cibles)
    {
        var c = s.C;
        static bool Arret(Noeud n) => n.Type is "choix" or "attente" or "echec" || (n.Type == "epreuve" && !JeuAuto(n.Jeu));
        var avant = new Dictionary<string, List<(string, int)>>(StringComparer.Ordinal);
        void Lien(Noeud de, string vers)
        {
            if (!avant.TryGetValue(vers, out var l)) avant[vers] = l = new();
            l.Add((de.Id, Arret(de) ? 1 : 0));
        }
        foreach (var n in c.Noeuds.Values)
        {
            if (n.Suite != "") Lien(n, n.Suite);
            foreach (var o in n.Options) Lien(n, o.Vers);
            foreach (var x in n.Issues) Lien(n, x.Vers);
            if (n.Reussite != "") Lien(n, n.Reussite);
            if (n.Echec != "") Lien(n, n.Echec);
        }
        var d = new Dictionary<string, int>(StringComparer.Ordinal);
        var file = new LinkedList<string>();
        foreach (var x in cibles)
        {
            d[x] = 0;
            file.AddLast(x);
        }
        while (file.Count > 0)
        {
            var v = file.First!.Value;
            file.RemoveFirst();
            foreach (var (u, w) in avant.GetValueOrDefault(v) ?? new())
                if (!d.TryGetValue(u, out var du) || d[v] + w < du)
                {
                    d[u] = d[v] + w;
                    if (w == 0) file.AddFirst(u);
                    else file.AddLast(u);
                }
        }
        return d;
    }

    // Toutes les arêtes du graphe des nœuds.
    public IEnumerable<string> Aretes()
    {
        foreach (var n in C.Noeuds.Values.OrderBy(x => x.Id, StringComparer.Ordinal))
            switch (n.Type)
            {
                case "choix":
                    for (int i = 0; i < n.Options.Count; i++) yield return $"o:{n.Id}:{i}";
                    break;
                case "epreuve":
                    yield return $"e:{n.Id}:ok";
                    yield return $"e:{n.Id}:ko";
                    break;
                case "hasard":
                    for (int i = 0; i < n.Issues.Count; i++) yield return $"h:{n.Id}:{i}";
                    break;
                case "attente":
                    yield return $"s:{n.Id}";
                    break;
                case "echec":
                    yield return $"r:{n.Id}";
                    break;
            }
    }
}
