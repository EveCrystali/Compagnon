using System.Globalization;
using PilouBureau;
using static PilouBureau.Campagnes;

// Le joueur automatique du test de jeu (docs/TEST-JEU.md).
//
// 1. Carte : un modèle abstrait de la campagne (nœud, variables, objets, drapeaux, dernier check-point), exploré en
//    entier : toutes les options, les deux issues de chaque épreuve, toutes les issues de chaque hasard, les échecs et
//    le retour au check-point. Chaque état d'arrêt (choix, épreuve, attente, échec, fin) est un sommet ; chaque décision
//    mène à une ou plusieurs issues (un hasard ou une épreuve aux dés en chemin). On y vérifie : nœuds et arêtes
//    atteints, impasses, boucles sans sortie, fins atteignables, conditions et objets impossibles, durées et récompenses.
// 2. Joueur : le vrai moteur (Campagnes.cs, par le carnet) mené par la carte vers une cible (une fin, une arête pas encore
//    vue) avec une horloge simulée ; à chaque pas, l'état du moteur doit être l'une des issues que prévoit la carte.
public sealed class Carte
{
    private static readonly CultureInfo Ci = CultureInfo.InvariantCulture;

    // Un état d'arrêt du modèle. Cp : l'état gardé au dernier check-point (null : jamais).
    public sealed class Etat
    {
        public string Noeud = "";
        public SortedDictionary<string, int> Vars = new(StringComparer.Ordinal);
        public SortedSet<string> Objets = new(StringComparer.Ordinal), Drapeaux = new(StringComparer.Ordinal);
        public Etat? Cp;
        public int Id;
        public string Cle = "";

        public Etat Copie() => new() { Noeud = Noeud, Vars = new(Vars, StringComparer.Ordinal), Objets = new(Objets, StringComparer.Ordinal),
            Drapeaux = new(Drapeaux, StringComparer.Ordinal), Cp = Cp };

        // Ce que l'on compare avec le moteur : nœud, variables, objets, drapeaux.
        public string Vue() => Noeud + "|" + string.Join(",", Vars.Select(kv => kv.Key + ":" + kv.Value.ToString(Ci))) + "|"
                               + string.Join(",", Objets) + "|" + string.Join(",", Drapeaux);

        public string Calculer() => Vue() + "#" + (Cp is null ? "-" : Cp.Vue());
    }

    // Une décision : son libellé (« o:<nœud>:<rang> », « e:<nœud>:ok|ko », « s:<nœud> » pour une attente, « r:<nœud> »
    // pour un repos), sa valeur pour le moteur, et ses issues.
    public sealed record Issue(Etat Vers, HashSet<string> Aretes, HashSet<string> Noeuds);
    public sealed record Decision(string Libelle, int Valeur, string Option, List<Issue> Issues, int MinutesMin, int MinutesMax);

    public readonly Campagne C;
    public readonly Dictionary<string, Etat> Etats = new(StringComparer.Ordinal);
    public readonly Dictionary<int, List<Decision>> Sorties = new();
    public readonly List<Etat> Liste = new();
    public readonly HashSet<string> NoeudsVus = new(StringComparer.Ordinal), AretesVues = new(StringComparer.Ordinal);
    public readonly List<string> Defauts = new();
    public Etat Depart = null!;
    public bool Tronquee;

    // Exploration en largeur jusqu'à maxEtats états ; au-delà (une vingtaine de drapeaux se combinent vite), la carte est
    // « tronquée » : le reste se développe à la demande (SortiesDe), (sans guidage : les parcours viennent du simulateur, Simu).
    public Carte(Campagne c, int maxEtats = 20_000)
    {
        C = c;
        var e0 = new Etat();
        foreach (var kv in c.Variables) e0.Vars[kv.Key] = kv.Value;
        var debut = Entrer(e0, c.Depart, new(), new());
        if (debut.Count != 1) Defauts.Add($"départ ambigu ({debut.Count} issues)");
        Depart = Garder(debut[0].Vers);
        NoeudsVus.UnionWith(debut[0].Noeuds);
        var file = new Queue<Etat>();
        file.Enqueue(Depart);
        var vus = new HashSet<int> { Depart.Id };
        while (file.Count > 0 && !Tronquee)
        {
            var s = file.Dequeue();
            foreach (var d in SortiesDe(s))
                foreach (var i in d.Issues)
                    if (vus.Add(i.Vers.Id))
                    {
                        if (vus.Count > maxEtats) Tronquee = true;
                        else file.Enqueue(i.Vers);
                    }
        }
        Exhaustive = !Tronquee;
        if (Tronquee) Oublier();
    }

    public readonly bool Exhaustive;
    private int _prochain;

    // Carte développée à la demande : quand elle devient trop grosse, on l'oublie (les états déjà tenus restent valables).
    private void Oublier()
    {
        Etats.Clear();
        Sorties.Clear();
        Liste.Clear();
        Etats[Depart.Cle] = Depart;
    }

    public List<Decision> SortiesDe(Etat s)
    {
        if (Sorties.TryGetValue(s.Id, out var l)) return l;
        if (!Exhaustive && Etats.Count > 150_000) Oublier();
        l = new List<Decision>();
        foreach (var d in Decisions(s))
        {
            var issues = new List<Issue>();
            foreach (var i in d.Issues)
            {
                issues.Add(i with { Vers = Garder(i.Vers) });
                NoeudsVus.UnionWith(i.Noeuds);
                AretesVues.UnionWith(i.Aretes);
            }
            l.Add(d with { Issues = issues });
        }
        Sorties[s.Id] = l;
        return l;
    }

    private Etat Garder(Etat e)
    {
        e.Cle = e.Calculer();
        if (Etats.TryGetValue(e.Cle, out var x)) return x;
        e.Id = _prochain++;
        if (!Tronquee) Liste.Add(e);
        Etats[e.Cle] = e;
        NoeudsVus.Add(e.Noeud);
        return e;
    }

    public Etat? Trouver(string vue, Etat? cp) => Etats.GetValueOrDefault(vue + "#" + (cp is null ? "-" : cp.Vue()));

    // ---- Le modèle (miroir de Campagnes.Moteur, en Mode.Neuf)

    public bool Vrai(Condition? k, Etat s)
    {
        if (k is null) return true;
        switch (k.Sorte)
        {
            case "var":
                int v = s.Vars.GetValueOrDefault(k.Nom);
                return (k.Min is null || v >= k.Min) && (k.Max is null || v <= k.Max);
            case "objet": return s.Objets.Contains(k.Nom);
            case "drapeau": return s.Drapeaux.Contains(k.Nom);
            case "non": return k.Sous.Count == 1 && !Vrai(k.Sous[0], s);
            case "tous": return k.Sous.All(x => Vrai(x, s));
            case "un": return k.Sous.Any(x => Vrai(x, s));
            default: return false;
        }
    }

    private static void Appliquer(IEnumerable<Campagnes.Effet> effets, Etat s)
    {
        foreach (var e in effets)
        {
            if (e.Sorte == "var") s.Vars[e.Nom] = s.Vars.GetValueOrDefault(e.Nom) + e.Valeur;
            else if (e.Sorte == "objet")
            {
                if (e.Valeur != 0) s.Objets.Add(e.Nom);
                else s.Objets.Remove(e.Nom);
            }
            else if (e.Sorte == "drapeau")
            {
                if (e.Valeur != 0) s.Drapeaux.Add(e.Nom);
                else s.Drapeaux.Remove(e.Nom);
            }
        }
    }

    // Entre dans un nœud (effets, check-point) et suit récits, hasards et épreuves aux dés jusqu'aux arrêts possibles.
    private List<Issue> Entrer(Etat s, string id, HashSet<string> aretes, HashSet<string> noeuds, int pas = 0)
    {
        var r = new List<Issue>();
        if (pas > 500 || C.Noeud(id) is not { } n)
        {
            Defauts.Add($"{id} : nœud absent ou boucle de récits");
            return r;
        }
        s = s.Copie();
        s.Noeud = id;
        noeuds = new(noeuds, StringComparer.Ordinal) { id };
        if (n.Checkpoint || s.Cp is null)
        {
            var cp = s.Copie();
            cp.Cp = null;
            s.Cp = cp;
        }
        Appliquer(n.Effets, s);
        switch (n.Type)
        {
            case "recit":
                return Entrer(s, n.Suite, aretes, noeuds, pas + 1);
            case "epreuve" when JeuAuto(n.Jeu):
                r.AddRange(Entrer(s, n.Reussite, new(aretes) { $"e:{id}:ok" }, noeuds, pas + 1));
                r.AddRange(Entrer(s, n.Echec, new(aretes) { $"e:{id}:ko" }, noeuds, pas + 1));
                return r;
            case "hasard":
            {
                var possibles = n.Issues.Select((x, i) => (x, i)).Where(p => Vrai(p.x.Si, s)).ToList();
                if (possibles.Count == 0)
                {
                    Defauts.Add($"{id} : hasard sans issue possible ({s.Vue()})");
                    possibles = n.Issues.Select((x, i) => (x, i)).ToList();
                }
                foreach (var (x, i) in possibles) r.AddRange(Entrer(s, x.Vers, new(aretes) { $"h:{id}:{i}" }, noeuds, pas + 1));
                return r;
            }
            case "choix" or "attente" or "epreuve" or "echec" or "fin":
                r.Add(new Issue(s, aretes, noeuds));
                return r;
            default:
                Defauts.Add($"{id} : type inconnu {n.Type}");
                return r;
        }
    }

    private IEnumerable<Decision> Decisions(Etat s)
    {
        var n = C.Noeud(s.Noeud)!;
        switch (n.Type)
        {
            case "choix":
                for (int i = 0; i < n.Options.Count; i++)
                {
                    var o = n.Options[i];
                    if (!Vrai(o.Si, s)) continue;
                    var t = s.Copie();
                    Appliquer(o.Effets, t);
                    yield return new Decision($"o:{n.Id}:{i}", i, o.Id, Entrer(t, o.Vers, new() { $"o:{n.Id}:{i}" }, new()), 0, 0);
                }
                break;
            case "epreuve":
                yield return new Decision($"e:{n.Id}:ok", Reussite, "", Entrer(s, n.Reussite, new() { $"e:{n.Id}:ok" }, new()), 0, 0);
                yield return new Decision($"e:{n.Id}:ko", Rate, "", Entrer(s, n.Echec, new() { $"e:{n.Id}:ko" }, new()), 0, 0);
                break;
            case "attente":
                int min = Math.Max(1, n.DureeMin), max = Math.Max(min, n.DureeMax);
                yield return new Decision($"s:{n.Id}", Suite, "", Entrer(s, n.Suite, new() { $"s:{n.Id}" }, new()), min, max);
                break;
            case "echec":
            {
                var cp = s.Cp!.Copie();
                cp.Cp = s.Cp;
                yield return new Decision($"r:{n.Id}", Suite, "", Entrer(cp, cp.Noeud, new() { $"r:{n.Id}" }, new()), Math.Max(1, n.ReposMin),
                    Math.Max(1, n.ReposMin));
                break;
            }
        }
    }

    // ---- Les arêtes du graphe des nœuds (ce que la carte doit toutes traverser)

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

    // Distance (en décisions, optimiste : les hasards tombent bien) de chaque état à un but.
    public int[] Distances(Func<Etat, bool> but)
    {
        var d = new int[Liste.Count];
        Array.Fill(d, int.MaxValue);
        var avant = new List<int>[Liste.Count];
        for (int i = 0; i < Liste.Count; i++) avant[i] = new();
        foreach (var (s, l) in Sorties)
            foreach (var x in l)
                foreach (var i in x.Issues)
                    avant[i.Vers.Id].Add(s);
        var file = new Queue<int>();
        foreach (var s in Liste)
            if (but(s))
            {
                d[s.Id] = 0;
                file.Enqueue(s.Id);
            }
        while (file.Count > 0)
        {
            int v = file.Dequeue();
            foreach (var u in avant[v])
                if (d[u] == int.MaxValue)
                {
                    d[u] = d[v] + 1;
                    file.Enqueue(u);
                }
        }
        return d;
    }

    // Les fins de la campagne.
    public IEnumerable<Noeud> Fins => C.Noeuds.Values.Where(n => n.Type == "fin").OrderBy(n => n.Id, StringComparer.Ordinal);

    // Bornes du temps réel (minutes) d'un parcours sans échec : le plus court (durées min) et le plus long (durées max).
    public (long Min, long Max, bool Cycle) Durees()
    {
        var memoMin = new Dictionary<int, long>();
        var memoMax = new Dictionary<int, long>();
        var enCours = new HashSet<int>();
        bool cycle = false;
        (long, long) Visiter(Etat s)
        {
            if (memoMin.TryGetValue(s.Id, out var a)) return (a, memoMax[s.Id]);
            if (C.Noeud(s.Noeud)!.Type == "fin") return (memoMin[s.Id] = 0, memoMax[s.Id] = 0);
            if (!enCours.Add(s.Id))
            {
                cycle = true;
                return (long.MaxValue / 4, long.MinValue / 4);
            }
            long mi = long.MaxValue / 4, ma = long.MinValue / 4;
            foreach (var x in Sorties[s.Id])
            {
                if (x.Libelle.StartsWith("r:", StringComparison.Ordinal)) continue; // sans échec
                foreach (var i in x.Issues)
                {
                    var (a2, b2) = Visiter(i.Vers);
                    mi = Math.Min(mi, a2 + x.MinutesMin);
                    ma = Math.Max(ma, b2 + x.MinutesMax);
                }
            }
            enCours.Remove(s.Id);
            memoMin[s.Id] = mi;
            memoMax[s.Id] = ma;
            return (mi, ma);
        }
        var (m1, m2) = Visiter(Depart);
        return (m1, m2, cycle);
    }
}

// Un parcours rejoué par le vrai moteur (ParcoursTests.Rejouer).
public sealed class Parcours
{
    public string Campagne = "", Cible = "", Graine = "", Fin = "", Issue = "";
    public int Decisions, Choix, Attentes, Longues, Echecs, Abandons, Pas, MaxOctets, Po, Xp;
    public long Minutes;
    public readonly HashSet<string> Aretes = new(StringComparer.Ordinal), Noeuds = new(StringComparer.Ordinal);
    public readonly List<string> Defauts = new();
}
