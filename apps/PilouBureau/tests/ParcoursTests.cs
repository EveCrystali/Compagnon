using System.Globalization;
using System.Text;
using System.Text.Json;
using PilouBureau;
using Xunit;
using Xunit.Abstractions;
using static PilouBureau.Campagnes;

// Le test de jeu (docs/TEST-JEU.md). Pour chaque campagne embarquée :
// 1. des milliers de marches du simulateur (Simu, exact, à graine fixe) couvrent chaque nœud, chaque arête et chaque fin ;
// 2. une sélection de ces marches (une par fin, puis de quoi couvrir toutes les arêtes, puis quelques joueurs « moyens »)
//    est rejouée par le vrai moteur, par le carnet, avec une horloge simulée : à chaque pas, la phase et l'état (nœud,
//    variables, objets, drapeaux) doivent être ceux du simulateur ; récompenses, messages, fil, abandons, reprises et
//    rejeu sont vérifiés en route ;
// 3. pour le prologue, la carte complète des états (Carte) prouve en plus qu'aucun état n'est une impasse.
// PILOU_TEST_JEU=<dossier> écrit le tableau des parcours (parcours.md et un CSV par campagne).
public class ParcoursTests(ITestOutputHelper sortie)
{
    private const long T0 = CampagnesVecteurs.T0;
    private static readonly CultureInfo Ci = CultureInfo.InvariantCulture;
    public static readonly string[] Ids = { "prologue", "grande-panne", "phare-eteint", "petit-nuage" };
    public const int Marches = 1500;

    // ---- La recherche (simulateur)

    public sealed class Recherche
    {
        public string Id = "";
        public Simu S = null!;
        public List<Simu.Marche> Toutes = new();
        public List<Simu.Marche> Choisies = new();
        public HashSet<string> Aretes = new(StringComparer.Ordinal), Noeuds = new(StringComparer.Ordinal);
        public Dictionary<string, int> Fins = new(StringComparer.Ordinal);
    }

    private static readonly Dictionary<string, Recherche> Recherches = new();

    public static Recherche Chercher(string id)
    {
        lock (Recherches)
        {
            if (Recherches.TryGetValue(id, out var deja)) return deja;
            var c = Charger(id)!;
            var r = new Recherche { Id = id, S = new Simu(c) };
            void Garder(Simu.Marche m)
            {
                r.Toutes.Add(m);
                r.Aretes.UnionWith(m.Aretes);
                r.Noeuds.UnionWith(m.Noeuds);
                if (m.Fin != "") r.Fins[m.Fin] = r.Fins.GetValueOrDefault(m.Fin) + 1;
            }
            for (int i = 0; i < Marches; i++)
                Garder(r.S.Jouer($"m{i}", Hasard.Graine($"choix|{id}|{i}"), i % 3 == 0 ? 1 : 0, abandons: i % 4 == 1, auDe: i % 2 == 0));
            // Arêtes encore jamais vues : des marches guidées vers leur nœud.
            foreach (var a in r.S.Aretes().Where(a => !r.Aretes.Contains(a)).ToList())
            {
                var vers = new Simu(c, new[] { a.Split(':')[1] });
                for (int i = 0; i < 300 && !r.Aretes.Contains(a); i++)
                    Garder(vers.Jouer($"v{r.Toutes.Count}", Hasard.Graine($"vers|{a}|{i}"), 1, abandons: false, auDe: i % 2 == 0));
            }
            // Sélection : la marche la plus courte vers chaque fin, puis de quoi couvrir les arêtes, puis des joueurs moyens.
            var vues = new HashSet<string>(StringComparer.Ordinal);
            foreach (var f in c.Noeuds.Values.Where(n => n.Type == "fin").OrderBy(n => n.Id, StringComparer.Ordinal))
                if (r.Toutes.Where(m => m.Fin == f.Id && m.Defauts.Count == 0).OrderBy(m => m.Pas.Count).FirstOrDefault() is { } m)
                {
                    r.Choisies.Add(m);
                    vues.UnionWith(m.Aretes);
                }
            while (true)
            {
                var m = r.Toutes.Where(x => x.Fin != "").OrderByDescending(x => x.Aretes.Count(a => !vues.Contains(a))).ThenBy(x => x.Pas.Count).First();
                if (m.Aretes.All(vues.Contains)) break;
                r.Choisies.Add(m);
                vues.UnionWith(m.Aretes);
            }
            foreach (var m in r.Toutes.Where(x => x.Politique == 0 && x.Abandons > 0 && x.Echecs > 0).Take(2)) r.Choisies.Add(m);
            foreach (var m in r.Toutes.Where(x => x.Politique == 0 && x.Abandons == 0).Take(3)) r.Choisies.Add(m);
            Recherches[id] = r;
            return r;
        }
    }

    // ---- Le rejeu par le vrai moteur

    private static string VueMoteur(Campagnes.Etat e) =>
        e.Noeud + "|" + string.Join(",", e.Variables.Select(kv => kv.Key + ":" + kv.Value.ToString(Ci))) + "|" + string.Join(",", e.Objets) + "|"
        + string.Join(",", e.Drapeaux);

    // Délai humain avant une décision (ms) : souvent quelques secondes, parfois une demi-heure, parfois une nuit.
    private static long Delai(Hasard h)
    {
        int r = h.Suivant(100);
        return r < 70 ? 5_000 + h.Suivant(115) * 1000L : r < 95 ? 120_000 + h.Suivant(28) * 60_000L : 2 * 3_600_000L + h.Suivant(12) * 3_600_000L;
    }

    public static Parcours Rejouer(Simu simu, Simu.Marche m, CampagnesVecteurs v, int numero, bool rejeu)
    {
        var c = simu.C;
        var r = new Parcours { Campagne = c.Id, Cible = m.Fin, Graine = m.Graine };
        var h = new Hasard(Hasard.Graine($"rejeu|{c.Id}|{m.Graine}"));
        var pc = new Profil { Machine = "PC" };
        Campagne? B(string id) => CampagnesVecteurs.Biblio(id);
        string[] appareils = { "pc-a", "tel-b" };
        long t = T0 + numero * 86_400_000L;
        v.Cas($"parcours-{c.Id}-{m.Graine}");
        v.Carnet($"j-{c.Id}-{m.Graine}");
        pc.CarnetCampagnes = v.K; // le carnet joué est celui d'un PC : il verse les récompenses au fil de l'eau
        if (v.Demarrer(c.Id, 99, t, "pc-a", m.Graine) is { } refus)
        {
            r.Defauts.Add("démarrer : " + refus);
            return r;
        }
        var e = v.EtatH(t)!;
        foreach (var pas in m.Pas)
        {
            r.Pas++;
            if (e.Phase != pas.Phase || VueMoteur(e) != pas.Vue)
            {
                r.Defauts.Add($"pas {r.Pas} : moteur {e.Phase} {VueMoteur(e)} ≠ simulateur {pas.Phase} {pas.Vue}");
                break;
            }
            string app = appareils[h.Suivant(2)];
            foreach (var x in Messages(v.K, "PC-BUREAU-1a2b", "pc")) r.MaxOctets = Math.Max(r.MaxOctets, Octets(x));
            if (r.Pas % 16 == 0) v.MessagesH(app, app.StartsWith("tel", StringComparison.Ordinal) ? "tel" : "pc");
            if (h.Suivant(6) == 0) Crediter(pc, B);
            var n = c.Noeud(e.Noeud)!;
            string? refuse = null;
            switch (pas.Action)
            {
                case "":
                    break;
                case "abandon":
                {
                    long ta = e.Phase == Phase.Attente ? e.T + (e.Fin - e.T) / 2 : t + Delai(h);
                    refuse = v.Abandonner(c.Id, ta, app);
                    var ea = v.EtatH(ta)!;
                    if (ea.Phase != Phase.Abandon) r.Defauts.Add($"{n.Id} : après l'abandon, {ea.Phase}");
                    if (!Reprenable(v.K, c, ta)) r.Defauts.Add($"{n.Id} : abandonnée mais pas reprenable");
                    t = Math.Max(t, ta) + Delai(h) + 3_600_000;
                    refuse ??= v.Demarrer(c.Id, 99, t, app, "autre-graine");
                    e = v.EtatH(t)!;
                    if (!e.Reprise) r.Defauts.Add($"reprise au nœud {e.Noeud} non marquée « reprise »");
                    r.Abandons++;
                    break;
                }
                case "temps":
                {
                    long minutes = (e.Fin - e.T) / 60_000;
                    if (minutes != pas.Minutes || (e.Fin - e.T) % 60_000 != 0) r.Defauts.Add($"{n.Id} : {minutes} min au moteur, {pas.Minutes} au simulateur");
                    if (e.T < t - 1000) r.Defauts.Add($"{n.Id} : l'attente a commencé avant la décision");
                    if (e.Phase == Phase.Repos) r.Echecs++;
                    else
                    {
                        r.Attentes++;
                        if (minutes >= 60) r.Longues++;
                    }
                    r.Minutes += minutes;
                    // Au milieu : toujours là, rien à décider (sauf la mettre de côté) ; une seconde avant la fin : pas encore.
                    if (h.Suivant(3) == 0)
                    {
                        long milieu = e.T + (e.Fin - e.T) / 2;
                        var em = v.EtatH(milieu)!;
                        if (em.Phase != e.Phase || em.Fin != e.Fin) r.Defauts.Add($"{n.Id} : au milieu de l'attente, {em.Phase}");
                        if (v.Continuer(c.Id, milieu, app) is null) r.Defauts.Add($"{n.Id} : « vas-y » accepté pendant l'attente");
                        if (v.EtatH(e.Fin - 1000)!.Phase != e.Phase) r.Defauts.Add($"{n.Id} : l'attente finit en avance");
                    }
                    t = Math.Max(t, e.Fin) + (h.Suivant(2) == 0 ? 0 : Delai(h));
                    break;
                }
                default:
                    t += Delai(h);
                    if (pas.Action.StartsWith("o:", StringComparison.Ordinal))
                    {
                        if (h.Suivant(10) == 0 && v.Continuer(c.Id, t, app) is null) r.Defauts.Add($"{n.Id} : « vas-y » accepté pendant un choix");
                        var simuOptions = string.Join(",", simu.C.Noeud(n.Id)!.Options.Where(o => e.Options.Any(x => x.Id == o.Id)).Select(o => o.Id));
                        if (string.Join(",", e.Options.Select(o => o.Id)) != simuOptions) r.Defauts.Add($"{n.Id} : options dans le désordre");
                        refuse = v.Choisir(c.Id, t, app, pas.Action[2..]);
                        r.Choix++;
                    }
                    else if (pas.Action is "ok" or "ko") refuse = v.Epreuve(c.Id, t, app, pas.Action == "ok");
                    else if (pas.Action == "de") refuse = v.AuDe(c.Id, t, app);
                    else if (pas.Action == "suite") refuse = v.Continuer(c.Id, t, app);
                    if (e.Phase == Phase.Epreuve && e.Chance != ChanceDe(n.Difficulte, n.Bonus == "" ? 0 : e.Variables.GetValueOrDefault(n.Bonus)))
                        r.Defauts.Add($"{n.Id} : chance {e.Chance} %");
                    r.Decisions++;
                    break;
            }
            if (refuse is not null)
            {
                r.Defauts.Add($"{n.Id} : {pas.Action} refusé ({refuse})");
                break;
            }
            if (pas.Action == "") break;
            e = v.EtatH(t)!;
            if (e.Phase == Phase.Cassee)
            {
                r.Defauts.Add($"partie cassée au nœud {e.Noeud}");
                break;
            }
        }
        if (e.Phase == Phase.Fin)
        {
            r.Fin = e.Noeud;
            r.Issue = e.Issue;
            var (apo, axp) = Acquis(v.K, c);
            (r.Po, r.Xp) = (apo, axp);
            // Récompenses : exactement celles des nœuds traversés, une fois chacun.
            if ((apo, axp) != (m.Po, m.Xp)) r.Defauts.Add($"acquis {apo} po {axp} xp, nœuds traversés {m.Po} po {m.Xp} xp");
            foreach (var ch in c.Chapitres)
            {
                var dans = m.Credits.Where(id => c.Noeud(id)!.Chapitre == ch.Id && c.Noeud(id)!.Type != "fin").ToList();
                int cpo = dans.Sum(id => c.Noeud(id)!.Recompense.Po), cxp = dans.Sum(id => c.Noeud(id)!.Recompense.Xp);
                if (cpo > 40 || cxp > 20) r.Defauts.Add($"chapitre {ch.Id} : {cpo} po, {cxp} xp sur ce parcours (plafond 40 / 20)");
            }
            if (apo > 600 || axp > 300) r.Defauts.Add($"{apo} po, {axp} xp : au-delà du plafond de la campagne");
            var fin = c.Noeud(e.Noeud)!;
            if (!Fins(v.K, c).Any(f => f.Noeud == e.Noeud)) r.Defauts.Add("fin absente du carnet");
            if (fin.Recompense.Souvenir != "" && !Souvenirs(v.K, c).Any(s => s.Id == fin.Recompense.Souvenir)) r.Defauts.Add("souvenir absent");
            if (fin.Recompense.Objet != "" && !ObjetsGagnes(v.K, c).Contains(fin.Recompense.Objet)) r.Defauts.Add("objet absent");
            if (fin.Recompense.Titre != "" && !Titres(v.K, c).Contains(fin.Recompense.Titre)) r.Defauts.Add("titre absent");
            // Versé une fois par le PC, même après relecture du carnet et réception de ses propres messages, deux fois.
            var verse = Crediter(pc, B);
            if ((pc.Bourse.PoCampagnes, pc.XpTelephone) != (apo, axp))
                r.Defauts.Add($"le PC a versé {pc.Bourse.PoCampagnes} po {pc.XpTelephone} xp pour {apo} po {axp} xp acquis");
            if (fin.Recompense.Objet != "" && Boutique.TrouverTout(fin.Recompense.Objet) is not null && !pc.Bourse.Inventaire.Contains(fin.Recompense.Objet))
                r.Defauts.Add($"objet {fin.Recompense.Objet} pas rangé dans l'inventaire");
            _ = verse;
            var relu = JsonSerializer.Deserialize<Profil>(JsonSerializer.Serialize(pc))!;
            var autre = new Carnet();
            foreach (var x in Messages(v.K, "pc-a", "pc")) Recevoir(autre, x, "tel-z", B, t);
            Actualiser(autre, B, t);
            foreach (var x in Messages(autre, "tel-z", "tel"))
            {
                Recevoir(relu.CarnetCampagnes, x, "pc-a", B, t);
                Recevoir(relu.CarnetCampagnes, x, "pc-a", B, t);
            }
            Actualiser(relu.CarnetCampagnes, B, t);
            var encore = Crediter(relu, B);
            if (encore.Po != 0 || encore.Xp != 0 || encore.Objets.Count > 0) r.Defauts.Add($"versé deux fois : +{encore.Po} po, +{encore.Xp} xp");
            if (EnAttente(autre, B) != (0, 0)) r.Defauts.Add($"le téléphone attend encore {EnAttente(autre, B)} d'un PC qui a tout versé");
            if (rejeu)
            {
                // Rejouer : ni po ni xp de plus, même en allant ailleurs.
                t += 3_600_000;
                if (v.Demarrer(c.Id, 99, t, "tel-b", "rejeu-" + m.Graine, neuf: true) is { } rr) r.Defauts.Add("rejeu refusé : " + rr);
                var er = v.EtatH(t)!;
                if (!er.Rejeu) r.Defauts.Add("la nouvelle partie n'est pas un rejeu");
                for (int i = 0; i < 60 && er.EnCours; i++)
                {
                    if (er.EnAttente) t = er.Fin;
                    t += 2000;
                    er = v.EtatH(t)!;
                    if (er.Phase == Phase.Choix) v.Choisir(c.Id, t, "tel-b", er.Options[^1].Id);
                    else if (er.Phase == Phase.Epreuve) v.AuDe(c.Id, t, "tel-b");
                    else if (er.Phase == Phase.Depart) v.Continuer(c.Id, t, "tel-b");
                }
                if (Acquis(v.K, c) != (apo, axp)) r.Defauts.Add($"le rejeu a changé les acquis : {Acquis(v.K, c)}");
                var x = Crediter(pc, B);
                if (x.Po != 0 || x.Xp != 0) r.Defauts.Add($"le rejeu a versé {x.Po} po {x.Xp} xp");
            }
        }
        else r.Defauts.Add($"pas de fin (nœud {e.Noeud}, {e.Phase})");
        v.Fil();
        v.Acquis(c.Id);
        v.SignatureH();
        return r;
    }

    // ---- Les bilans

    public sealed record Bilan(string Id, Recherche R, List<Parcours> Rejoues);

    private static readonly Dictionary<string, Bilan> Bilans = new();

    // Rejoue les marches choisies d'une campagne. v : où écrire les vecteurs (une marche par fin) ; null : nulle part.
    public static Bilan Rejouer(string id, CampagnesVecteurs? v = null)
    {
        var r = Chercher(id);
        var l = new List<Parcours>();
        var fins = new HashSet<string>(StringComparer.Ordinal);
        int i = 0;
        foreach (var m in r.Choisies)
        {
            bool vecteur = v is not null && fins.Add(m.Fin);
            l.Add(Rejouer(r.S, m, vecteur ? v! : new CampagnesVecteurs(), ++i, rejeu: i == 1));
        }
        return new Bilan(id, r, l);
    }

    public static Bilan BilanDe(string id)
    {
        lock (Bilans)
        {
            if (!Bilans.TryGetValue(id, out var b)) Bilans[id] = b = Rejouer(id);
            return b;
        }
    }

    public static string H(long minutes) => minutes >= 60 ? $"{minutes / 60} h {minutes % 60:00}" : $"{minutes} min";

    private static string Mmm(IEnumerable<long> valeurs, Func<long, string> f)
    {
        var l = valeurs.OrderBy(x => x).ToList();
        return l.Count == 0 ? "—" : $"{f(l[0])} / {f(l[l.Count / 2])} / {f(l[^1])}";
    }

    // ---- Les tests

    [Theory]
    [InlineData("prologue")]
    [InlineData("grande-panne")]
    [InlineData("phare-eteint")]
    [InlineData("petit-nuage")]
    public void Chaque_fin_chaque_noeud_chaque_arete_rejoues_par_le_moteur(string id)
    {
        var b = BilanDe(id);
        var r = b.R;
        var c = r.S.C;
        var defauts = new List<string>();
        foreach (var x in r.Toutes.SelectMany(m => m.Defauts).Distinct().Take(20)) defauts.Add("simulateur : " + x);
        foreach (var n in c.Noeuds.Keys.Where(n => !r.Noeuds.Contains(n)).OrderBy(n => n, StringComparer.Ordinal)) defauts.Add($"nœud {n} jamais atteint");
        foreach (var a in r.S.Aretes().Where(a => !r.Aretes.Contains(a))) defauts.Add($"arête {a} jamais traversée (option jamais proposée, issue jamais tirée ?)");
        foreach (var f in c.Noeuds.Values.Where(n => n.Type == "fin"))
            if (!r.Fins.ContainsKey(f.Id)) defauts.Add($"fin {f.Id} jamais atteinte");
        foreach (var p in b.Rejoues)
            foreach (var x in p.Defauts) defauts.Add($"moteur, marche {p.Graine} : {x}");
        // Plafonds sur chaque marche, échecs et reprises compris (on ne « farme » pas une récompense en échouant).
        foreach (var m in r.Toutes.Where(m => m.Fin != ""))
        {
            if (m.Po > 600 || m.Xp > 300) defauts.Add($"marche {m.Graine} : {m.Po} po, {m.Xp} xp");
            foreach (var g in m.Credits.Select(c.Noeud).Where(n => n!.Type != "fin").GroupBy(n => n!.Chapitre))
                if (g.Sum(n => n!.Recompense.Po) > 40 || g.Sum(n => n!.Recompense.Xp) > 20)
                    defauts.Add($"marche {m.Graine}, chapitre {g.Key} : {g.Sum(n => n!.Recompense.Po)} po, {g.Sum(n => n!.Recompense.Xp)} xp");
        }
        // Le moteur a traversé tout ce que le simulateur annonçait pour les marches choisies.
        var rejouees = new HashSet<string>(r.Choisies.SelectMany(m => m.Aretes));
        foreach (var a in r.Aretes.Where(a => !rejouees.Contains(a))) defauts.Add($"arête {a} pas rejouée par le moteur");
        if (b.Rejoues.Select(p => p.Fin).Distinct().Count() != r.Fins.Count) defauts.Add("toutes les fins ne sont pas rejouées par le moteur");
        var finies = r.Toutes.Where(m => m.Fin != "").ToList();
        sortie.WriteLine($"{id} : {r.Toutes.Count} marches du simulateur ({finies.Count} jusqu'à une fin), {b.Rejoues.Count} rejouées par le moteur ; "
                         + $"{r.Noeuds.Count}/{c.Noeuds.Count} nœuds, {r.Aretes.Count}/{r.S.Aretes().Count()} arêtes, {r.Fins.Count} fins ; "
                         + $"attentes et repos (min / médiane / max) : {Mmm(finies.Select(m => m.Minutes), H)} ; "
                         + $"message le plus gros {b.Rejoues.Max(p => p.MaxOctets)} octets");
        if (Environment.GetEnvironmentVariable("PILOU_TEST_JEU") is { Length: > 0 } dossier) Ecrire(dossier, b);
        Assert.True(defauts.Count == 0, string.Join("\n", defauts.Take(60)));
        Assert.All(b.Rejoues, p => Assert.True(p.MaxOctets <= TailleJson, $"{p.Graine} : message de {p.MaxOctets} octets"));
    }

    // Le prologue est assez petit pour une carte complète de ses états : aucune impasse, aucun état sans fin.
    [Fact]
    public void La_carte_complete_du_prologue_n_a_ni_impasse_ni_boucle()
    {
        var carte = new Carte(Charger("prologue")!);
        Assert.True(carte.Exhaustive);
        var d = carte.Distances(s => carte.C.Noeud(s.Noeud)!.Type == "fin");
        foreach (var s in carte.Liste)
        {
            Assert.True(carte.C.Noeud(s.Noeud)!.Type == "fin" || carte.SortiesDe(s).Any(x => x.Issues.Count > 0), $"impasse en {s.Vue()}");
            Assert.True(d[s.Id] != int.MaxValue, $"aucune fin depuis {s.Vue()}");
        }
        Assert.Empty(carte.Defauts);
        Assert.Equal("", string.Join(",", carte.C.Noeuds.Keys.Where(n => !carte.NoeudsVus.Contains(n))));
        Assert.Equal("", string.Join(",", carte.Aretes().Where(a => !carte.AretesVues.Contains(a))));
        var (min, max, _) = carte.Durees();
        sortie.WriteLine($"prologue : {carte.Liste.Count} états, attentes sans échec de {H(min)} à {H(max)}");
    }

    // Conditions : un drapeau testé est posé quelque part ; un objet requis se donne quelque part ; une variable testée
    // change quelque part. Attentes : dans les bornes décidées (5 à 30 min, 1 à 3 h pour les longues, en fin de chapitre).
    [Fact]
    public void Conditions_possibles_et_attentes_dans_les_bornes()
    {
        var defauts = new List<string>();
        var notes = new List<string>();
        foreach (var id in Ids)
        {
            var c = Charger(id)!;
            var poses = new HashSet<string>(c.Noeuds.Values.SelectMany(n => n.Effets.Concat(n.Options.SelectMany(o => o.Effets)))
                .Where(e => e.Sorte is "drapeau" or "objet" ? e.Valeur != 0 : e.Valeur != 0).Select(e => e.Sorte + ":" + e.Nom));
            foreach (var (ou, k) in Conditions(c))
                foreach (var f in Feuilles(k))
                    if (f.Sorte is "drapeau" or "objet" or "var" && !poses.Contains(f.Sorte + ":" + f.Nom))
                        defauts.Add($"{id} : {ou} teste {f.Sorte} « {f.Nom} », que rien ne donne ni ne change");
            foreach (var n in c.Noeuds.Values.Where(n => n.Type == "attente").OrderBy(n => n.Id, StringComparer.Ordinal))
            {
                int min = n.DureeMin, max = Math.Max(n.DureeMin, n.DureeMax);
                bool longue = max >= 60;
                if (id == "prologue") continue; // le prologue, court, apprend le geste : des attentes d'une à quelques minutes
                if (!longue && (min < 5 || max > 30)) notes.Add($"{id} : {n.Id} attend {min}–{max} min (hors 5–30 min)");
                if (longue && (min < 60 || max > 180) && n.Tenue != "nuit") notes.Add($"{id} : {n.Id} attend {min}–{max} min (longue hors 1–3 h)");
                if (longue && !FinDeChapitre(c, n)) notes.Add($"{id} : {n.Id} ({min}–{max} min) n'est pas en fin de chapitre");
            }
        }
        foreach (var x in notes) sortie.WriteLine(x);
        Assert.True(defauts.Count == 0, string.Join("\n", defauts));
    }

    // Une longue attente « en fin de chapitre » : après elle, plus de choix avant le chapitre suivant (ou la fin).
    private static bool FinDeChapitre(Campagne c, Noeud n)
    {
        var vus = new HashSet<string>();
        var file = new Queue<string>();
        file.Enqueue(n.Suite);
        while (file.Count > 0)
        {
            var id = file.Dequeue();
            if (!vus.Add(id) || c.Noeud(id) is not { } x) continue;
            if (x.Chapitre != n.Chapitre || x.Type == "fin") continue;
            if (x.Type is "choix" or "attente" or "epreuve") return false;
            if (x.Suite != "") file.Enqueue(x.Suite);
            foreach (var i in x.Issues) file.Enqueue(i.Vers);
        }
        return true;
    }

    private static IEnumerable<(string Ou, Condition K)> Conditions(Campagne c)
    {
        foreach (var n in c.Noeuds.Values)
        {
            foreach (var o in n.Options)
                if (o.Si is not null) yield return ($"{n.Id}/{o.Id}", o.Si);
            foreach (var x in n.Issues)
                if (x.Si is not null) yield return ($"{n.Id}/hasard", x.Si);
        }
    }

    private static IEnumerable<Condition> Feuilles(Condition k) => k.Sorte is "non" or "tous" or "un" ? k.Sous.SelectMany(Feuilles) : new[] { k };

    private static void Ecrire(string dossier, Bilan b)
    {
        Directory.CreateDirectory(dossier);
        var r = b.R;
        var csv = new StringBuilder("source,campagne,graine,fin,issue,choix,attentes,longues,echecs,abandons,minutes,po,xp,octets_max,defauts\n");
        foreach (var p in b.Rejoues)
            csv.Append(Ci, $"moteur,{p.Campagne},{p.Graine},{p.Fin},{p.Issue},{p.Choix},{p.Attentes},{p.Longues},{p.Echecs},{p.Abandons},{p.Minutes},{p.Po},{p.Xp},{p.MaxOctets},{p.Defauts.Count}\n");
        foreach (var m in r.Toutes)
            csv.Append(Ci, $"simulateur,{r.Id},{m.Graine},{m.Fin},{m.Issue},{m.Choix},{m.Attentes},{m.Longues},{m.Echecs},{m.Abandons},{m.Minutes},{m.Po},{m.Xp},,{m.Defauts.Count}\n");
        File.WriteAllText(Path.Combine(dossier, $"parcours-{b.Id}.csv"), csv.ToString());
        var finies = r.Toutes.Where(m => m.Fin != "").ToList();
        var md = new StringBuilder();
        md.Append(Ci, $"## {r.S.C.Titre} (`{b.Id}`)\n\n");
        md.Append(Ci, $"{r.Toutes.Count} marches du simulateur, {b.Rejoues.Count} rejouées par le moteur. {r.Noeuds.Count}/{r.S.C.Noeuds.Count} nœuds, "
                      + $"{r.Aretes.Count}/{r.S.Aretes().Count()} arêtes.\n\n");
        md.Append("| Mesure (min / médiane / max) | Toutes les marches | Sans échec ni abandon |\n|---|---|---|\n");
        var propres = finies.Where(m => m.Echecs == 0 && m.Abandons == 0).ToList();
        md.Append(Ci, $"| Temps réel (attentes + repos) | {Mmm(finies.Select(m => m.Minutes), H)} | {Mmm(propres.Select(m => m.Minutes), H)} |\n");
        md.Append(Ci, $"| Choix | {Mmm(finies.Select(m => (long)m.Choix), x => x.ToString(Ci))} | {Mmm(propres.Select(m => (long)m.Choix), x => x.ToString(Ci))} |\n");
        md.Append(Ci, $"| Attentes | {Mmm(finies.Select(m => (long)m.Attentes), x => x.ToString(Ci))} | {Mmm(propres.Select(m => (long)m.Attentes), x => x.ToString(Ci))} |\n");
        md.Append(Ci, $"| dont ≥ 1 h | {Mmm(finies.Select(m => (long)m.Longues), x => x.ToString(Ci))} | {Mmm(propres.Select(m => (long)m.Longues), x => x.ToString(Ci))} |\n");
        md.Append(Ci, $"| Échecs | {Mmm(finies.Select(m => (long)m.Echecs), x => x.ToString(Ci))} | — |\n");
        md.Append(Ci, $"| po | {Mmm(finies.Select(m => (long)m.Po), x => x.ToString(Ci))} | {Mmm(propres.Select(m => (long)m.Po), x => x.ToString(Ci))} |\n");
        md.Append(Ci, $"| xp | {Mmm(finies.Select(m => (long)m.Xp), x => x.ToString(Ci))} | {Mmm(propres.Select(m => (long)m.Xp), x => x.ToString(Ci))} |\n\n");
        md.Append("| Fin | Issue | Joueur au hasard (part des marches) | Rejouée par le moteur (graine : choix, attentes, temps, po/xp, octets) |\n|---|---|---|---|\n");
        var auHasard = finies.Where(m => m.Politique == 0).ToList();
        foreach (var (fin, _) in r.Fins.OrderByDescending(kv => auHasard.Count(m => m.Fin == kv.Key)))
        {
            var p = b.Rejoues.FirstOrDefault(x => x.Fin == fin);
            string rejouee = p is null ? "—" : FormattableString.Invariant($"{p.Graine} : {p.Choix} choix, {p.Attentes} attentes, {H(p.Minutes)}, {p.Po}/{p.Xp}, {p.MaxOctets} o");
            md.Append(FormattableString.Invariant($"| `{fin}` | {r.S.C.Noeud(fin)!.Issue} | {100.0 * auHasard.Count(m => m.Fin == fin) / Math.Max(1, auHasard.Count):0.0} % | {rejouee} |\n"));
        }
        md.Append('\n');
        File.WriteAllText(Path.Combine(dossier, $"parcours-{b.Id}.md"), md.ToString());
    }
}
