using System.Globalization;
using System.Text;
using PilouBureau;

// Vecteurs partagés des campagnes : un scénario joué par le moteur C# (Campagnes.cs), écrit ligne à ligne dans
// android/app/src/test/resources/campagnes-vecteurs.txt. Le test Java (CampagnesTest) relit ce fichier, refait chaque
// opération avec Campagnes.java et compare le résultat : c'est la preuve que le PC et le téléphone rejouent pareil.
//
// Une ligne = une opération, ses entrées, puis le résultat attendu (le dernier champ peut contenir des espaces) :
//   code <id> <code> · tirage <graine> <n> <max> <valeur> · chance <difficulté> <bonus> <%> · sujet <code> <sujet>
//   cas <nom> · campagne <id> · partie <json>
//   rejouer <ms> <état> · decider <ms> <appareil> <valeur> <empreinte|refus> · de <ms> <0|1> · compacter <ms> <json>
//   carnet <nom> · demarrer <id> <niveau> <ms> <appareil> <graine> <neuf> <ok|refus>
//   choisir|continuer|aude|abandonner <id> <ms> <appareil> [option] <ok|refus> · epreuve <id> <ms> <appareil> <0|1> <ok|refus>
//   actualiser <ms> <état|rien> · messages <appareil> <sorte> <n> puis n lignes « m <json> »
//   recevoir <moi> <ms> <0|1> <json> · signature <json> · fil <messages> <non lus> <empreinte> · lu
//   acquis <id> <po> <xp> <fins> · attente <po> <xp>
public sealed class CampagnesVecteurs
{
    public const string Reference = "android/app/src/test/resources/campagnes-vecteurs.txt";
    public const long T0 = 1_790_000_000_000;
    private static readonly CultureInfo Ci = CultureInfo.InvariantCulture;

    public static DirectoryInfo Racine()
    {
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        while (dir is not null && !Directory.Exists(Path.Combine(dir.FullName, "android"))) dir = dir.Parent;
        return dir ?? throw new InvalidOperationException("racine du dépôt introuvable");
    }

    private static Campagnes.Campagne? _essai;

    // La campagne d'essai (android/app/src/test/resources/campagnes-essai/essai) : toutes les règles du moteur en 19 nœuds.
    public static Campagnes.Campagne Essai()
    {
        if (_essai is not null) return _essai;
        var dossier = Path.Combine(Racine().FullName, "android/app/src/test/resources/campagnes-essai/essai");
        _essai = Campagnes.Lire(File.ReadAllText(Path.Combine(dossier, "campagne.json")),
            f => File.Exists(Path.Combine(dossier, f)) ? File.ReadAllText(Path.Combine(dossier, f)) : null)!;
        Campagnes.Connaitre(_essai); // la boutique connaît ainsi ses objets exclusifs, comme ceux d'une campagne embarquée
        return _essai;
    }

    public static Campagnes.Campagne? Biblio(string id) => id == "essai" ? Essai() : Campagnes.Charger(id);

    public static string Empreinte(string s)
    {
        ulong h = 14695981039346656037UL;
        foreach (char c in s)
        {
            h ^= c;
            h *= 1099511628211UL;
        }
        return h.ToString("x16", Ci);
    }

    public readonly List<string> L = new();
    public Campagnes.Campagne C = null!;
    public Campagnes.Partie P = null!;
    public readonly Dictionary<string, Campagnes.Carnet> Carnets = new();
    public Campagnes.Carnet K = null!;

    private static string F(long n) => n.ToString(Ci);

    public void Note(string texte) => L.Add("# " + texte);

    public void Cas(string nom) => L.Add("cas " + nom);

    public void Campagne(string id)
    {
        C = Biblio(id)!;
        L.Add("campagne " + id);
    }

    public void Partie(string json)
    {
        P = Campagnes.LirePartie(json)!;
        L.Add("partie " + json);
    }

    public Campagnes.Etat Rejouer(long t)
    {
        var e = Campagnes.Rejouer(C, P, t);
        L.Add($"rejouer {F(t)} {e.Texte()}");
        return e;
    }

    public bool Decider(long t, string appareil, int valeur)
    {
        var q = Campagnes.Decider(C, P, t, appareil, valeur);
        L.Add($"decider {F(t)} {appareil} {F(valeur)} {(q is null ? "refus" : Empreinte(Campagnes.JsonPartie(q)))}");
        if (q is not null) P = q;
        return q is not null;
    }

    public bool De(long t)
    {
        bool r = Campagnes.DeDe(C, P, Campagnes.Rejouer(C, P, t));
        L.Add($"de {F(t)} {(r ? 1 : 0)}");
        return r;
    }

    public void Compacter(long t)
    {
        P = Campagnes.Compacter(C, P, t);
        L.Add($"compacter {F(t)} {Campagnes.JsonPartie(P)}");
    }

    public void Carnet(string nom)
    {
        if (!Carnets.TryGetValue(nom, out var k)) Carnets[nom] = k = new Campagnes.Carnet();
        K = k;
        L.Add("carnet " + nom);
    }

    public string? Demarrer(string id, int niveau, long t, string appareil, string graine, bool neuf = false)
    {
        var r = Campagnes.Demarrer(K, Biblio(id)!, niveau, t, appareil, Biblio, graine, neuf);
        L.Add($"demarrer {id} {F(niveau)} {F(t)} {appareil} {graine} {(neuf ? 1 : 0)} {r ?? "ok"}");
        return r;
    }

    public string? Choisir(string id, long t, string appareil, string option)
    {
        var r = Campagnes.Choisir(K, Biblio(id)!, t, appareil, option);
        L.Add($"choisir {id} {F(t)} {appareil} {option} {r ?? "ok"}");
        return r;
    }

    public string? Continuer(string id, long t, string appareil)
    {
        var r = Campagnes.Continuer(K, Biblio(id)!, t, appareil);
        L.Add($"continuer {id} {F(t)} {appareil} {r ?? "ok"}");
        return r;
    }

    public string? Epreuve(string id, long t, string appareil, bool reussie)
    {
        var r = Campagnes.Epreuve(K, Biblio(id)!, t, appareil, reussie);
        L.Add($"epreuve {id} {F(t)} {appareil} {(reussie ? 1 : 0)} {r ?? "ok"}");
        return r;
    }

    public string? AuDe(string id, long t, string appareil)
    {
        var r = Campagnes.EpreuveAuDe(K, Biblio(id)!, t, appareil);
        L.Add($"aude {id} {F(t)} {appareil} {r ?? "ok"}");
        return r;
    }

    public string? Abandonner(string id, long t, string appareil)
    {
        var r = Campagnes.Abandonner(K, Biblio(id)!, t, appareil);
        L.Add($"abandonner {id} {F(t)} {appareil} {r ?? "ok"}");
        return r;
    }

    public Campagnes.Etat? Actualiser(long t)
    {
        var e = Campagnes.Actualiser(K, Biblio, t);
        L.Add($"actualiser {F(t)} {e?.Texte() ?? "rien"}");
        return e;
    }

    // Version courte pour les parcours complets (docs/TEST-JEU.md) : l'empreinte de l'état au lieu de son texte.
    // Sans la prose (textes des messages, lieu, ligne « pendant ») : une relecture d'orthographe des campagnes ne change pas
    // ces empreintes ; tout le reste (nœuds, phases, heures, tirages, variables, humeurs, décors, nombre de messages) compte.
    public Campagnes.Etat? EtatH(long t)
    {
        var e = Campagnes.Actualiser(K, Biblio, t);
        L.Add($"etat {F(t)} {(e is null ? "rien" : Empreinte(SansProse(e)))}");
        return e;
    }

    public static string SansProse(Campagnes.Etat e)
    {
        var champs = e.Texte().Split('|').Where(c => !c.StartsWith("lieu=", StringComparison.Ordinal) && !c.StartsWith("pendant=", StringComparison.Ordinal)
                                                       && !c.StartsWith("messages=", StringComparison.Ordinal));
        var b = new StringBuilder();
        foreach (var m in e.Messages) b.Append($"{m.E}.{m.I}.{m.Qui}.{m.Noeud}.{m.Humeur}.{m.Decor}.{m.T}.{(m.Reprise ? 1 : 0)}\n");
        return string.Join("|", champs) + "|messages=" + F(e.Messages.Count) + ":" + Empreinte(b.ToString());
    }

    public void FilH()
    {
        var b = new StringBuilder();
        foreach (var m in K.Fil) b.Append($"{m.P}.{m.E}.{m.I}.{m.Qui}.{m.Noeud}\n");
        L.Add($"filh {F(K.Fil.Count)} {F(K.NonLus)} {Empreinte(b.ToString())}");
    }

    // Les messages publiés, en empreinte, avec la taille du plus gros (octets de JSON).
    public List<string> MessagesH(string appareil, string sorte)
    {
        var l = Campagnes.Messages(K, appareil, sorte);
        L.Add($"messagesh {appareil} {sorte} {F(l.Count)} {F(l.Count == 0 ? 0 : l.Max(Campagnes.Octets))} {Empreinte(string.Join("\n", l))}");
        return l;
    }

    public void SignatureH() => L.Add("signatureh " + Empreinte(Campagnes.Signature(K)));

    public List<string> Messages(string appareil, string sorte)
    {
        var l = Campagnes.Messages(K, appareil, sorte);
        L.Add($"messages {appareil} {sorte} {F(l.Count)}");
        foreach (var m in l) L.Add("m " + m);
        return l;
    }

    public bool Recevoir(string moi, long t, string json)
    {
        bool r = Campagnes.Recevoir(K, json, moi, Biblio, t);
        L.Add($"recevoir {moi} {F(t)} {(r ? 1 : 0)} {json}");
        return r;
    }

    public string Signature()
    {
        var s = Campagnes.Signature(K);
        L.Add("signature " + s);
        return s;
    }

    public void Fil()
    {
        var b = new StringBuilder();
        foreach (var m in K.Fil) b.Append($"{m.P}.{m.E}.{m.I}.{m.Qui}.{m.Noeud}.{m.Texte}\n");
        L.Add($"fil {F(K.Fil.Count)} {F(K.NonLus)} {Empreinte(b.ToString())}");
    }

    public void Lu()
    {
        Campagnes.MarquerLu(K);
        L.Add("lu");
    }

    public (int Po, int Xp) Acquis(string id)
    {
        var c = Biblio(id)!;
        var a = Campagnes.Acquis(K, c);
        L.Add($"acquis {id} {F(a.Po)} {F(a.Xp)} {string.Join(",", Campagnes.Fins(K, c).Select(f => f.Noeud))}");
        return a;
    }

    public (int Po, int Xp) Attente()
    {
        var a = Campagnes.EnAttente(K, Biblio);
        L.Add($"attente {F(a.Po)} {F(a.Xp)}");
        return a;
    }

    // Échange complet : chaque carnet nommé reçoit les messages des autres, dans l'ordre donné.
    public void Echanger(long t, params string[] ordre) => Echanger(t, true, ordre);

    // Le même, avec les états sans la prose (vraies campagnes : la relecture d'orthographe ne change pas les vecteurs).
    public void EchangerH(long t, params string[] ordre) => Echanger(t, false, ordre);

    private void Echanger(long t, bool prose, string[] ordre)
    {
        var envois = new Dictionary<string, List<string>>();
        foreach (var nom in ordre.Distinct())
        {
            Carnet(nom);
            envois[nom] = Messages(nom, nom.StartsWith("tel") ? "tel" : "pc");
        }
        foreach (var nom in ordre)
        {
            Carnet(nom);
            foreach (var autre in ordre.Where(a => a != nom))
                foreach (var m in envois[autre]) Recevoir(nom, t, m);
            if (prose) Actualiser(t);
            else EtatH(t);
        }
    }

    // ---- Le scénario

    // Une partie en JSON, écrite à la main : décisions dans l'ordre donné (désordre et doublons permis).
    public static string JsonBrut(string campagne, string depart, long t, string[] appareils, params (int E, long Dt, int A, string N, int V)[] journal) =>
        "{\"c\":\"" + campagne + "\",\"p\":1,\"d\":" + F(t / 1000) + ",\"o\":\"pc-a\",\"g\":\"graine\",\"x\":2,\"e\":0,\"r\":0,\"i\":0,\"n\":0,\"t\":" + F(t / 1000)
        + ",\"ici\":[\"" + Campagnes.Code(depart) + "\",{},\"\",\"\",\"\",\"\"],\"l\":[" + string.Join(",", appareils.Select(a => "\"" + a + "\"")) + "],\"j\":["
        + string.Join(",", journal.Select(j => $"[{F(j.E)},{F(j.Dt)},{F(j.A)},\"{Campagnes.Code(j.N)}\",{F(j.V)}]")) + "]}";

    private void Marche(string id, int graine, int pas, bool abandon = true)
    {
        var h = new Hasard(Hasard.Graine($"marche|{id}|{graine}"));
        long t = T0 + graine * 977_000L + 123;
        Cas($"marche-{id}-{graine}");
        Campagne(id);
        Partie(Campagnes.JsonPartie(Campagnes.Nouvelle(C, 1 + graine, t, "pc-a", "g" + graine, graine % 3 == 2)));
        string[] appareils = { "pc-a", "tel-b", "pc-c" };
        for (int i = 0; i < pas; i++)
        {
            var e = Rejouer(t);
            string a = appareils[h.Suivant(appareils.Length)];
            if (!e.EnCours) break;
            switch (e.Phase)
            {
                case Campagnes.Phase.Choix:
                    if (h.Suivant(8) == 0) Decider(t, a, 3 - h.Suivant(8));  // parfois une option absente ou une valeur hors sujet
                    Decider(t, a, e.Options[h.Suivant(e.Options.Count)].Rang);
                    break;
                case Campagnes.Phase.Epreuve:
                    Decider(t, a, h.Suivant(3) == 0 ? (De(t) ? Campagnes.Reussite : Campagnes.Rate)
                        : h.Suivant(2) == 0 ? Campagnes.Reussite : Campagnes.Rate);
                    break;
                case Campagnes.Phase.Depart:
                    if (h.Suivant(6) == 0) Decider(t, a, 0);
                    Decider(t, a, Campagnes.Suite);
                    break;
                default:
                    if (h.Suivant(4) == 0)
                    {
                        Rejouer(t + (e.Fin - t) / 2);                      // au milieu de l'attente : toujours là
                        Decider(t + 1000, a, Campagnes.Suite);             // rien à décider pendant l'attente
                    }
                    if (abandon && h.Suivant(12) == 0) Decider(t + 2000, a, Campagnes.Abandon);
                    else t = e.Fin + h.Suivant(90) * 1000L;
                    break;
            }
            t += h.Suivant(120) * 1000L + h.Suivant(1000);
            if (h.Suivant(4) == 0) Compacter(t);
        }
        Rejouer(t + 86_400_000);
        Compacter(t + 86_400_000);
        Rejouer(t + 86_400_000);
    }

    // Des vecteurs pour d'autres campagnes (une campagne en cours d'écriture, par exemple) : quelques parties entières
    // chacune, à faire rejouer par le moteur Java (PILOU_VECTEURS=<fichier> côté CampagnesTest).
    public static string Pour(IEnumerable<Campagnes.Campagne> campagnes)
    {
        var s = new CampagnesVecteurs();
        foreach (var c in campagnes)
        {
            Campagnes.Connaitre(c);
            for (int g = 0; g < 3; g++) s.Marche(c.Id, g, 400, abandon: false);
        }
        return string.Join("\n", s.L) + "\n";
    }

    public static string Tout()
    {
        var s = new CampagnesVecteurs();
        s.L.Add("# Vecteurs partagés des campagnes, écrits par le moteur du PC (apps/PilouBureau/tests/CampagnesVecteurs.cs).");
        s.L.Add("# Le téléphone les rejoue (android/.../CampagnesTest.java) : mêmes états, mêmes tirages, mêmes messages.");
        s.L.Add("# Pour les refaire après un changement du moteur : PILOU_REGENERER=1 dotnet test apps/PilouBureau/tests");
        foreach (var id in new[] { "p1-lettre", "porte-du-phare", "a", "ch12-fin-secrete", "courage", "lanterne", "a-menti" })
            s.L.Add($"code {id} {Campagnes.Code(id)}");
        foreach (var (g, n, max) in new[] { ("graine", 0, 100), ("graine", 1, 100), ("a1b2c3d4", 7, 3), ("a1b2c3d4", 250, 1000), ("", 0, 2) })
            s.L.Add($"tirage {(g == "" ? "-" : g)} {n} {max} {Campagnes.Tirage(g, n).Suivant(max)}");
        foreach (var (d, b) in new[] { (1, 0), (2, 0), (3, 0), (3, 4), (1, -30), (2, 9), (0, 0), (7, 1) })
            s.L.Add($"chance {d} {b} {Campagnes.ChanceDe(d, b)}");
        s.L.Add($"sujet ABCD-EFGH-JKMN-PQRS {Campagnes.Sujet("ABCD-EFGH-JKMN-PQRS")}");

        // 1. Des parties entières, au hasard, sur les deux campagnes (états, refus, tirages, compactions).
        for (int g = 0; g < 4; g++) s.Marche("prologue", g, 40);
        for (int g = 0; g < 8; g++) s.Marche("essai", g, 45);

        // 2. Conflits : deux appareils décident pour la même étape. La plus ancienne gagne ; à égalité, le plus petit
        //    identifiant d'appareil. Le journal arrive dans le désordre, avec des doublons : même état.
        s.Cas("conflit-plus-ancienne");
        s.Campagne("essai");
        string[] app = { "pc-a", "tel-b" };
        s.Partie(JsonBrut("essai", "a-debut", T0, app, (0, 50, 1, "a-carrefour", 3), (0, 40, 0, "a-carrefour", 0)));
        s.Rejouer(T0 + 60_000);
        s.Partie(JsonBrut("essai", "a-debut", T0, app, (0, 40, 0, "a-carrefour", 0), (0, 50, 1, "a-carrefour", 3), (0, 40, 0, "a-carrefour", 0)));
        s.Rejouer(T0 + 60_000);
        s.Cas("conflit-egalite-appareil");
        s.Partie(JsonBrut("essai", "a-debut", T0, app, (0, 40, 1, "a-carrefour", 3), (0, 40, 0, "a-carrefour", 0)));
        s.Rejouer(T0 + 60_000);
        s.Partie(JsonBrut("essai", "a-debut", T0, new[] { "tel-b", "pc-a" }, (0, 40, 1, "a-carrefour", 0), (0, 40, 0, "a-carrefour", 3)));
        s.Rejouer(T0 + 60_000);
        s.Cas("conflit-suite-orpheline");
        // tel-b a choisi « boucle » (perdant) puis, après son attente, « nord » ; pc-a avait choisi « nord » avant :
        // la suite de tel-b (étape 1, prise au carrefour) ne vaut que si l'histoire qui gagne repasse par ce nœud.
        s.Partie(JsonBrut("essai", "a-debut", T0, app, (1, 400, 1, "a-carrefour", 0), (0, 50, 1, "a-carrefour", 3), (0, 40, 0, "a-carrefour", 0),
            (1, 3000, 0, "a-double", -1), (2, 3400, 1, "a-epreuve", -2), (2, 3400, 0, "a-epreuve", -3), (2, 3300, 1, "a-prime", 1)));
        s.Rejouer(T0 + 60_000);
        s.Rejouer(T0 + 40 * 60_000);
        s.Rejouer(T0 + 4 * 3600_000);
        s.Cas("horloge-en-avance");
        // pc-a attend encore (son horloge retarde), tel-b a déjà continué après l'attente : pc-a suit.
        s.Partie(JsonBrut("essai", "a-debut", T0, app, (0, 10, 0, "a-carrefour", 3), (1, 300, 1, "a-carrefour", 3), (1, 20, 1, "a-boucle", -1)));
        s.Rejouer(T0 + 20_000);
        s.Rejouer(T0 + 400_000);
        s.Cas("abandon-pendant-l-attente");
        s.Partie(JsonBrut("essai", "a-debut", T0, app, (0, 10, 0, "a-carrefour", 3), (1, 500, 1, "a-carrefour", 0), (1, 200, 0, "a-boucle", -4), (1, 320, 0, "a-boucle", -4)));
        s.Rejouer(T0 + 100_000);
        s.Rejouer(T0 + 900_000);
        s.Compacter(T0 + 900_000);
        s.Cas("journal-mal-forme");
        s.Partie(JsonBrut("essai", "a-debut", T0, app, (0, 10, 0, "a-carrefour", 9), (0, 11, 0, "a-prime", 0), (0, 12, 1, "a-carrefour", 2), (5, 13, 1, "a-carrefour", 0),
            (0, 14, 1, "a-carrefour", -1), (0, 15, 1, "a-carrefour", 1)));
        s.Rejouer(T0 + 60_000);

        // 3. Carnets : trois appareils (deux PC, un téléphone) qui s'échangent leurs messages.
        s.Cas("carnets-prologue");
        long t = T0 + 5_000;
        s.Carnet("pc-a");
        s.Demarrer("essai", 1, t, "pc-a", "g1");                      // niveau insuffisant
        s.Demarrer("prologue", 1, t, "pc-a", "g1");
        s.Demarrer("essai", 5, t + 1000, "pc-a", "g2");               // une seule campagne à la fois
        s.Actualiser(t);
        s.Fil();
        s.Choisir("prologue", t + 20_000, "pc-a", "pont");            // pas proposé
        s.Choisir("prologue", t + 20_000, "pc-a", "corde");
        s.Actualiser(t + 30_000);
        s.Echanger(t + 31_000, "pc-a", "tel-b", "pc-c");
        s.Carnet("tel-b");
        s.Actualiser(t + 90_000);
        s.Lu();
        s.Choisir("prologue", t + 95_000, "tel-b", "pont");
        s.Fil();
        // Pendant ce temps, hors ligne, pc-c choisit autre chose, plus tard : il perdra.
        s.Carnet("pc-c");
        s.Choisir("prologue", t + 99_000, "pc-c", "tour");
        s.Actualiser(t + 100_000);
        s.Echanger(t + 101_000, "pc-c", "pc-a", "tel-b");
        foreach (var nom in new[] { "pc-a", "tel-b", "pc-c" })
        {
            s.Carnet(nom);
            s.Signature();
        }
        s.Carnet("tel-b");
        s.Actualiser(t + 200_000);
        s.Choisir("prologue", t + 200_000, "tel-b", "raccourci");
        var e = s.Actualiser(t + 200_000)!;
        s.Echanger(t + 201_000, "tel-b", "pc-a", "pc-c");
        s.Carnet("pc-a");
        long fin = Math.Max(e.Fin, t + 201_000) + 1000;
        e = s.Actualiser(fin)!;
        // Selon le tirage : il grimpe (attente) ou il glisse (repos, puis retour au bâton).
        for (int i = 0; i < 12 && e.EnCours; i++)
        {
            fin = Math.Max(fin, e.Fin) + 5_000;
            e = s.Actualiser(fin)!;
            if (e.Phase == Campagnes.Phase.Choix) s.Choisir("prologue", fin, i % 2 == 0 ? "pc-a" : "pc-c", e.Options[^1].Id == "rentre" ? "reste" : "sentier");
            else if (e.Phase == Campagnes.Phase.Depart) s.Continuer("prologue", fin, "pc-a");
            e = s.Actualiser(fin + 1000)!;
        }
        s.Fil();
        s.Acquis("prologue");
        s.Echanger(fin + 2000, "pc-a", "tel-b", "pc-c");
        s.Carnet("tel-b");
        s.Acquis("prologue");
        s.Attente();
        foreach (var nom in new[] { "pc-a", "tel-b", "pc-c" })
        {
            s.Carnet(nom);
            s.Signature();
        }

        // 4. Rejouer une campagne finie (ni po ni xp de plus), abandonner, en commencer une autre, reprendre.
        s.Cas("carnets-rejeu-abandon-reprise");
        long u = fin + 3_600_000;
        s.Carnet("tel-b");
        s.Demarrer("prologue", 3, u, "tel-b", "g3");
        s.Choisir("prologue", u + 10_000, "tel-b", "gouter");
        s.Actualiser(u + 80_000);
        s.Choisir("prologue", u + 80_000, "tel-b", "saute");
        s.AuDe("prologue", u + 85_000, "tel-b");
        s.Actualiser(u + 86_000);
        s.Abandonner("prologue", u + 90_000, "tel-b");
        s.Actualiser(u + 91_000);
        s.Demarrer("essai", 3, u + 100_000, "tel-b", "g4");
        s.Choisir("essai", u + 110_000, "tel-b", "nord");
        s.Actualiser(u + 120_000);
        s.Signature();
        s.Echanger(u + 121_000, "tel-b", "pc-a", "pc-c");
        // pc-c, qui n'a pas encore reçu la suite, abandonne l'essai et reprend le prologue à son check-point.
        s.Carnet("pc-c");
        s.Abandonner("essai", u + 130_000, "pc-c");
        s.Demarrer("prologue", 3, u + 140_000, "pc-c", "g5");
        s.Actualiser(u + 141_000);
        s.Signature();
        s.Echanger(u + 150_000, "pc-c", "tel-b", "pc-a");
        s.Carnet("pc-a");
        s.Actualiser(u + 151_000);
        s.Acquis("prologue");
        s.Acquis("essai");
        s.Demarrer("essai", 3, u + 152_000, "pc-a", "g6");            // refusé : le prologue est en cours
        s.Abandonner("prologue", u + 160_000, "pc-a");
        s.Demarrer("essai", 3, u + 170_000, "pc-a", "g6");            // reprise de l'essai au carrefour
        s.Actualiser(u + 171_000);
        s.Demarrer("prologue", 3, u + 172_000, "pc-a", "g7", true);
        s.Abandonner("essai", u + 180_000, "pc-a");
        s.Demarrer("prologue", 3, u + 190_000, "pc-a", "g7", true);   // neuf : depuis le début, pas depuis le bâton
        s.Actualiser(u + 191_000);
        s.Echanger(u + 200_000, "pc-a", "pc-c", "tel-b");
        s.Echanger(u + 201_000, "tel-b", "pc-c", "pc-a");
        foreach (var nom in new[] { "pc-a", "tel-b", "pc-c" })
        {
            s.Carnet(nom);
            s.Signature();
        }

        // 5. Deux départs en même temps sur deux appareils : la partie au plus grand numéro, puis la plus ancienne.
        s.Cas("carnets-departs-simultanes");
        s.Carnet("pc-x");
        s.Demarrer("essai", 9, T0, "pc-x", "gx");
        s.Carnet("tel-y");
        s.Demarrer("prologue", 9, T0 + 3000, "tel-y", "gy");
        s.Echanger(T0 + 10_000, "pc-x", "tel-y");
        s.Echanger(T0 + 11_000, "tel-y", "pc-x");
        foreach (var nom in new[] { "pc-x", "tel-y" })
        {
            s.Carnet(nom);
            s.Signature();
        }
        s.Recevoir("pc-x", T0 + 12_000, "{\"v\":2,\"a\":\"pc-z\"}");
        s.Recevoir("pc-x", T0 + 12_000, "pas du json");
        s.Recevoir("pc-x", T0 + 12_000, "{\"v\":1,\"a\":\"pc-z\",\"k\":\"pc\",\"q\":{\"c\":\"Mauvais Id\",\"p\":9},\"h\":{\"x\":[1,0,{},\"zz\"]}}");
        s.Signature();

        // 6. Divergence au-delà du délai de grâce : au même choix, chacun prend une route et avance seul pendant des heures ;
        //    en se retrouvant, la base la plus avancée l'emporte et le fil du perdant repart de cette base.
        s.Cas("divergence-au-dela-du-delai");
        var hd = new Hasard(77);
        long td = T0 + 400 * 86_400_000L;
        void Pas(string id, string app, ref long tt)
        {
            var x = s.EtatH(tt)!;
            if (!x.EnCours) return;
            if (x.EnAttente)
            {
                tt = x.Fin + 1000;
                s.EtatH(tt);
                return;
            }
            tt += 30_000;
            if (x.Phase == Campagnes.Phase.Choix) s.Choisir(id, tt, app, x.Options[hd.Suivant(x.Options.Count)].Id);
            else if (x.Phase == Campagnes.Phase.Epreuve) s.AuDe(id, tt, app);
            else s.Continuer(id, tt, app);
        }
        s.Carnet("dv-pc");
        s.Demarrer("phare-eteint", 99, td, "pc-a", "dv");
        for (int i = 0; i < 60; i++)
        {
            var x = s.EtatH(td)!;
            if (x.Phase == Campagnes.Phase.Choix && x.Options.Count >= 2 && x.ChapitreNumero >= 2) break;
            Pas("phare-eteint", "pc-a", ref td);
        }
        s.EchangerH(td, "dv-pc", "dv-tel");
        var ed = s.EtatH(td)!;
        s.Carnet("dv-pc");
        s.Choisir("phare-eteint", td + 10_000, "pc-a", ed.Options[0].Id);
        s.Carnet("dv-tel");
        s.Choisir("phare-eteint", td + 70_000, "tel-b", ed.Options[1].Id);
        long tp = td + 10_000, tq = td + 70_000;
        for (int i = 0; i < 6; i++)
        {
            s.Carnet("dv-pc");
            Pas("phare-eteint", "pc-a", ref tp);
            s.Carnet("dv-tel");
            Pas("phare-eteint", "tel-b", ref tq);
        }
        s.EchangerH(Math.Max(tp, tq) + 1000, "dv-tel", "dv-pc");
        foreach (var nom in new[] { "dv-pc", "dv-tel" })
        {
            s.Carnet(nom);
            s.FilH();
            s.SignatureH();
        }

        // 6 bis. Divergence quand le perdant est en retard : au même choix, le PC avance de huit pas, le téléphone d'aucun ;
        //    une heure plus tard, le rejeu du téléphone n'atteint pas l'étape de la base reçue. La route des décisions dit
        //    que les histoires se sont séparées : le fil du téléphone repart de la base reçue, sans son choix perdant.
        s.Cas("divergence-perdant-en-retard");
        td = T0 + 420 * 86_400_000L;
        s.Carnet("dr-pc");
        s.Demarrer("phare-eteint", 99, td, "pc-a", "dr");
        for (int i = 0; i < 60; i++)
        {
            var x = s.EtatH(td)!;
            if (x.Phase == Campagnes.Phase.Choix && x.Options.Count >= 2 && x.ChapitreNumero >= 2) break;
            Pas("phare-eteint", "pc-a", ref td);
        }
        s.EchangerH(td, "dr-pc", "dr-tel");
        ed = s.EtatH(td)!;
        s.Carnet("dr-pc");
        s.Choisir("phare-eteint", td + 10_000, "pc-a", ed.Options[0].Id);
        s.Carnet("dr-tel");
        s.Choisir("phare-eteint", td + 70_000, "tel-b", ed.Options[1].Id);
        tp = td + 10_000;
        s.Carnet("dr-pc");
        for (int i = 0; i < 8; i++) Pas("phare-eteint", "pc-a", ref tp);
        long tr = Math.Max(tp, td + 70_000) + 3_600_000;
        s.Carnet("dr-pc");
        s.EtatH(tr);
        s.Carnet("dr-tel");
        s.EtatH(tr);
        s.Carnet("dr-pc");
        foreach (var m in s.MessagesH("pc-a", "pc"))
        {
            s.Carnet("dr-tel");
            s.Recevoir("tel-b", tr, m);
        }
        s.Carnet("dr-tel");
        s.EtatH(tr);
        s.FilH();
        s.EchangerH(tr + 1000, "dr-tel", "dr-pc");
        foreach (var nom in new[] { "dr-pc", "dr-tel" })
        {
            s.Carnet(nom);
            s.FilH();
            s.SignatureH();
        }

        // 7. Parcours complets des quatre campagnes (docs/TEST-JEU.md) : pour chaque fin, une partie entière trouvée par le
        //    simulateur et jouée par le carnet (choix, épreuves, dés, « vas-y », attentes franchies à l'horloge, échecs,
        //    abandons et reprises, rejeu), états en empreinte, messages et signature en empreinte.
        foreach (var id in ParcoursTests.Ids)
        {
            s.Note($"parcours complets : {id}");
            ParcoursTests.Rejouer(id, s);
        }
        return string.Join("\n", s.L) + "\n";
    }
}
