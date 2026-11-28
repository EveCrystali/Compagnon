using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace PilouBureau;

// Campagnes (docs/CAMPAGNES.md) : de longs récits à choix, en temps réel. Pilou écrit, le joueur choisit, Pilou met
// du vrai temps à agir. Ce fichier est le MOTEUR, sans interface ni WPF ; android/.../Campagnes.java en est la copie
// exacte (mêmes règles, mêmes tirages, mêmes messages) : les vecteurs partagés
// android/app/src/test/resources/campagnes-vecteurs.txt, écrits d'ici (CampagnesTests), sont relus par les tests Java.
//
// ---- API, pour qui écrit une interface (détail : docs/CAMPAGNES.md, « API du moteur »)
//
//   Bibliothèque   Campagnes.Disponibles()            ids des campagnes embarquées (assets/campagnes/<id>/)
//                  Campagnes.Charger(id)              la campagne (fiche + chapitres), null si inconnue
//   Carnet         Campagnes.Carnet                   tout ce qu'un appareil garde : partie en cours, parties
//                                                     suspendues, historique, fil des messages (profil du PC)
//   État courant   Campagnes.Actualiser(carnet, Charger, maintenant) → Etat (null : aucune partie)
//                    Etat.Phase   Choix | Epreuve | Depart | Attente | Repos | Fin | Abandon | Cassee
//                    Etat.Options (Choix), Etat.Jeu / Difficulte / Aide (Epreuve), Etat.Fin (ms Unix : fin de
//                    l'attente ou du repos → notification locale, bulle), Etat.Pendant et Etat.Tenue (Pilou occupé),
//                    Etat.Lieu, Etat.Decor, Etat.Humeur, Etat.Chapitre…, Etat.Progression, Etat.Issue (fin obtenue),
//                    Etat.Reprise et Message.Reprise (retour à un check-point : ce que Pilou redit n'est pas nouveau)
//                    carnet.Fil : les messages (Pilou et joueur), carnet.NonLus, Campagnes.MarquerLu(carnet)
//   Ouverture      Campagnes.Manque(carnet, campagne, niveau, succès, Charger) → "" ou « s'ouvre au niveau 5 et après … »
//   Décisions      Campagnes.Demarrer(carnet, campagne, niveau, maintenant, appareil, Charger, …, succès) → null ou la raison du refus
//                  Campagnes.Choisir(carnet, campagne, maintenant, appareil, idOption)   (phase Choix)
//                  Campagnes.Continuer(…)        « vas-y » : Pilou part (phase Depart)
//                  Campagnes.Epreuve(…, reussie) résultat d'un mini-jeu (phase Epreuve)
//                  Campagnes.EpreuveAuDe(…)      l'appareil ne sait pas jouer ce jeu : tirage « des » à la place
//                  Campagnes.Abandonner(…)       la partie s'arrête ; Demarrer la reprendra au dernier check-point
//   Synchro        Campagnes.Messages(carnet, appareil, "pc" | "tel") → 1 ou 2 JSON (≤ TailleJson) à chiffrer et publier
//                  sur Campagnes.Sujet(code) ; Campagnes.Recevoir(carnet, json, appareil, Charger, maintenant) : fusion
//                  idempotente (ordre et doublons sans effet)
//   Récompenses    Campagnes.Crediter(profil, Charger) (PC seulement : il reste l'arbitre des po)
//   Sur le PC, la fenêtre fait tout cela pour l'interface : FenetreCampagne.cs (EtatCampagne, CampagneChoisir…).
//
// ---- Principe
//
// L'état se déduit d'un journal : la liste des décisions (étape, heure, appareil, nœud, valeur). Rejouer(campagne,
// partie, maintenant) redonne toujours le même état. Deux appareils décident pour la même étape : la plus ancienne
// gagne (égalité : plus petit identifiant d'appareil). Une partie = un résumé d'état (« base », posée à un
// check-point) + les décisions prises depuis ; Compacter avance la base quand la dernière décision d'avant le
// check-point a plus de dix minutes (le temps qu'un autre appareil se manifeste). Dans les messages et le carnet,
// nœuds, variables, objets, drapeaux et décors sont désignés par un code de 4 caractères tiré de leur identifiant.
public static class Campagnes
{
    public enum Phase { Aucune, Choix, Epreuve, Depart, Attente, Repos, Fin, Abandon, Cassee }

    // Valeurs d'une décision qui n'est pas un choix (un choix : le rang de l'option, ≥ 0).
    public const int Suite = -1, Reussite = -2, Rate = -3, Abandon = -4;
    // Délai de grâce avant d'avancer la base au check-point suivant, taille du journal gardé.
    public const long Grace = 600_000;
    public const int MaxEntrees = 24, GardeEntrees = 12, MaxParEtape = 6, MaxAvance = 64, MaxPas = 4000, MaxFil = 150;
    // JSON d'un message de synchronisation, au plus (chiffré puis base64 : sous Telephone.TailleMax, comme Groupe.TailleJson).
    public const int TailleJson = 2750;
    public static readonly string[] Jeux = { "reflexe", "memoire", "rythme", "visee", "des" };
    public static readonly string[] Humeurs = { "joie", "peur", "triste", "surpris", "determine", "fatigue", "tendre", "colere", "malice", "neutre" };
    public static readonly string[] Tenues = { "marche", "course", "bateau", "grimpe", "nage", "nuit", "cache", "attend" };

    // ---- Modèle d'une campagne (lu des fichiers JSON)

    public sealed class Condition
    {
        public string Sorte = "";   // var, objet, drapeau, non, tous, un ; autre chose : fausse
        public string Nom = "";
        public int? Min, Max;
        public List<Condition> Sous = new();
    }

    // Sorte : var (Valeur ajoutée), objet ou drapeau (Valeur 1 : donné / posé, 0 : perdu / ôté).
    public sealed record Effet(string Sorte, string Nom, int Valeur);
    public sealed record Option(string Id, string Libelle, string Vers, Condition? Si, IReadOnlyList<Effet> Effets);
    public sealed record IssueHasard(int Poids, string Vers, Condition? Si);
    public sealed record Prime(int Po, int Xp, string Souvenir = "", string Titre = "", string Objet = "")
    {
        public bool Vide => Po <= 0 && Xp <= 0 && Souvenir == "" && Titre == "" && Objet == "";
    }

    public sealed record Chapitre(string Id, string Titre, string Fichier);
    // Objet, souvenir ou décor déclaré dans la fiche. Portable : objet exclusif gagné à une fin, qui se porte
    // (Emplacement : tete, yeux, cou, dos, main, pieds ou compagnon ; à défaut, la main).
    public sealed record Nomme(string Id, string Nom, string Texte = "", bool Portable = false, string Emplacement = "");

    public sealed class Noeud
    {
        public string Id = "", Chapitre = "", Type = "", Lieu = "", Humeur = "neutre", Decor = "", Suite = "", Pendant = "", Tenue = "",
            Jeu = "", Bonus = "", Reussite = "", Echec = "", Issue = "", Titre = "";
        // Facultatifs (interfaces seulement) : le personnage que le message fait parler ou décrit, et son expression.
        public string Personnage = "", Expression = "";
        public List<string> Texte = new();
        public bool Checkpoint;
        public List<Effet> Effets = new();
        public Prime Recompense = new(0, 0);
        public List<Option> Options = new();
        public List<IssueHasard> Issues = new();
        public int DureeMin, DureeMax, Difficulte = 1, ReposMin;
    }

    public sealed class Campagne
    {
        public string Id = "", Titre = "", Ton = "", Accroche = "", Duree = "", Depart = "";
        public int Niveau = 1;
        // Conditions d'ouverture en plus du niveau (facultatives) : hauts faits obtenus (ids de Succes.Tous), campagnes finies.
        public List<string> Succes = new(), Apres = new();
        public List<Chapitre> Chapitres = new();
        public SortedDictionary<string, int> Variables = new(StringComparer.Ordinal);
        public List<Nomme> Objets = new(), Souvenirs = new(), Decors = new();
        public Dictionary<string, Noeud> Noeuds = new(StringComparer.Ordinal);
        // code court → identifiant, par famille (n nœuds, v variables, o objets, d drapeaux, c décors).
        private readonly Dictionary<string, string> _codes = new(StringComparer.Ordinal);

        public Noeud? Noeud(string id) => Noeuds.GetValueOrDefault(id);

        public string? Decode(char famille, string code) => _codes.GetValueOrDefault(famille + code);

        public Nomme? Souvenir(string id) => Souvenirs.FirstOrDefault(s => s.Id == id);

        internal void Indexer()
        {
            _codes.Clear();
            void Ajouter(char famille, IEnumerable<string> ids)
            {
                foreach (var id in ids.OrderBy(x => x, StringComparer.Ordinal))
                    _codes.TryAdd(famille + Code(id), id); // deux ids de même code : le premier (le validateur l'interdit)
            }
            Ajouter('n', Noeuds.Keys);
            Ajouter('v', Variables.Keys);
            Ajouter('o', Objets.Select(o => o.Id));
            Ajouter('c', Decors.Select(o => o.Id));
            var drapeaux = new SortedSet<string>(StringComparer.Ordinal);
            foreach (var n in Noeuds.Values)
            {
                foreach (var e in n.Effets.Concat(n.Options.SelectMany(o => o.Effets)))
                    if (e.Sorte == "drapeau") drapeaux.Add(e.Nom);
            }
            Ajouter('d', drapeaux);
        }
    }

    // ---- Codes courts et tirages (identiques sur le PC et le téléphone)

    private const string Alphabet64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";

    // La lettre d'une décision dans la route : Abandon (-4) → A, Rate → B, Reussite → C, Suite → D, option 0 → E…
    private static char Pas64(int valeur) => Alphabet64[valeur - Abandon];

    private static bool CheminValide(string chemin, int e) =>
        chemin.Length == e && chemin.All(ch => Alphabet64.IndexOf(ch) is >= 0 and <= 16 - Abandon);

    // 4 caractères tirés de l'identifiant (FNV-1a 64 bits, 24 bits gardés) : ce qui voyage dans les messages.
    public static string Code(string id)
    {
        ulong h = Hasard.Graine(id);
        var c = new char[4];
        for (int i = 0; i < 4; i++) c[i] = Alphabet64[(int)((h >> (6 * i)) & 63)];
        return new string(c);
    }

    // Le n-ième tirage d'une partie (hasard, duree_max, épreuve « des ») : il ne dépend que de la graine et de n.
    public static Hasard Tirage(string graine, int n) =>
        new(Hasard.Graine("campagne|" + graine + "|" + n.ToString(CultureInfo.InvariantCulture)));

    // Chance de réussir une épreuve au dé, en % : 70, 55, 40 selon la difficulté, ± 5 par point de la variable bonus.
    public static int ChanceDe(int difficulte, int bonus) =>
        Math.Clamp(85 - 15 * Math.Clamp(difficulte, 1, 3) + 5 * Math.Clamp(bonus, -20, 20), 10, 95);

    public static bool JeuAuto(string jeu) => jeu == "des" || !Jeux.Contains(jeu);

    private static long Seconde(long ms) => ms - ms % 1000;

    // ---- Lecture des fichiers

    private static string S(JsonElement o, string cle, string defaut = "") =>
        o.ValueKind == JsonValueKind.Object && o.TryGetProperty(cle, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() ?? defaut : defaut;

    private static int N(JsonElement o, string cle, int defaut = 0) =>
        o.ValueKind == JsonValueKind.Object && o.TryGetProperty(cle, out var v) && v.ValueKind == JsonValueKind.Number && v.TryGetInt32(out var n) ? n : defaut;

    private static bool B(JsonElement o, string cle, bool defaut = false) =>
        o.ValueKind == JsonValueKind.Object && o.TryGetProperty(cle, out var v)
            ? v.ValueKind == JsonValueKind.True || (v.ValueKind != JsonValueKind.False && defaut) : defaut;

    private static IEnumerable<JsonElement> L(JsonElement o, string cle) =>
        o.ValueKind == JsonValueKind.Object && o.TryGetProperty(cle, out var v) && v.ValueKind == JsonValueKind.Array
            ? v.EnumerateArray().ToList() : new List<JsonElement>();

    private static Condition? LireCondition(JsonElement o, string cle)
    {
        if (o.ValueKind != JsonValueKind.Object || !o.TryGetProperty(cle, out var v)) return null;
        return LireCondition(v);
    }

    private static Condition LireCondition(JsonElement v)
    {
        var c = new Condition { Sorte = "inconnue" };
        if (v.ValueKind != JsonValueKind.Object) return c;
        if (v.TryGetProperty("non", out var non))
        {
            c.Sorte = "non";
            c.Sous.Add(LireCondition(non));
        }
        else if (v.TryGetProperty("tous", out var tous) && tous.ValueKind == JsonValueKind.Array)
        {
            c.Sorte = "tous";
            foreach (var x in tous.EnumerateArray()) c.Sous.Add(LireCondition(x));
        }
        else if (v.TryGetProperty("un", out var un) && un.ValueKind == JsonValueKind.Array)
        {
            c.Sorte = "un";
            foreach (var x in un.EnumerateArray()) c.Sous.Add(LireCondition(x));
        }
        else if (S(v, "var") != "")
        {
            c.Sorte = "var";
            c.Nom = S(v, "var");
            if (v.TryGetProperty("min", out var mi) && mi.ValueKind == JsonValueKind.Number && mi.TryGetInt32(out var a)) c.Min = a;
            if (v.TryGetProperty("max", out var ma) && ma.ValueKind == JsonValueKind.Number && ma.TryGetInt32(out var b)) c.Max = b;
            if (c.Min is null && c.Max is null) c.Min = 1;
        }
        else if (S(v, "objet") != "")
        {
            c.Sorte = "objet";
            c.Nom = S(v, "objet");
        }
        else if (S(v, "drapeau") != "")
        {
            c.Sorte = "drapeau";
            c.Nom = S(v, "drapeau");
        }
        return c;
    }

    private static List<Effet> LireEffets(JsonElement o)
    {
        var l = new List<Effet>();
        foreach (var e in L(o, "effets"))
        {
            if (S(e, "var") != "") l.Add(new Effet("var", S(e, "var"), N(e, "plus")));
            else if (S(e, "objet") != "") l.Add(new Effet("objet", S(e, "objet"), B(e, "donne", true) ? 1 : 0));
            else if (S(e, "drapeau") != "") l.Add(new Effet("drapeau", S(e, "drapeau"), B(e, "ote") ? 0 : 1));
        }
        return l;
    }

    // Une liste d'identifiants (au plus 8, sans doublon, dans l'ordre de la fiche).
    private static List<string> LireIds(JsonElement o, string cle)
    {
        var l = new List<string>();
        foreach (var x in L(o, cle))
            if (x.ValueKind == JsonValueKind.String && IdValide(x.GetString() ?? "") && !l.Contains(x.GetString()!) && l.Count < 8) l.Add(x.GetString()!);
        return l;
    }

    private static Prime LirePrime(JsonElement o, string cle)
    {
        if (o.ValueKind != JsonValueKind.Object || !o.TryGetProperty(cle, out var r) || r.ValueKind != JsonValueKind.Object) return new Prime(0, 0);
        return new Prime(Math.Max(0, N(r, "po")), Math.Max(0, N(r, "xp")), S(r, "souvenir"), S(r, "titre"), S(r, "objet"));
    }

    private static List<Nomme> LireNommes(JsonElement o, string cle)
    {
        var l = new List<Nomme>();
        foreach (var x in L(o, cle))
            if (S(x, "id") != "") l.Add(new Nomme(S(x, "id"), S(x, "nom"), S(x, "texte", S(x, "description")), B(x, "portable"), S(x, "emplacement")));
        return l;
    }

    private static Noeud LireNoeud(string id, string chapitre, JsonElement o)
    {
        var n = new Noeud
        {
            Id = id, Chapitre = chapitre, Type = S(o, "type"), Lieu = S(o, "lieu"), Humeur = S(o, "humeur", "neutre"), Decor = S(o, "decor"),
            Suite = S(o, "suite"), Pendant = S(o, "pendant"), Tenue = S(o, "tenue"), Jeu = S(o, "jeu"), Bonus = S(o, "bonus"),
            Reussite = S(o, "reussite"), Echec = S(o, "echec"), Issue = S(o, "issue"), Titre = S(o, "titre"),
            Checkpoint = B(o, "checkpoint"), Effets = LireEffets(o), DureeMin = N(o, "duree_min"), DureeMax = N(o, "duree_max"),
            Difficulte = N(o, "difficulte", 1), ReposMin = N(o, "repos_min"),
            Personnage = S(o, "personnage"), Expression = S(o, "expression"),
        };
        if (!Humeurs.Contains(n.Humeur)) n.Humeur = "neutre";
        if (o.TryGetProperty("texte", out var t))
        {
            if (t.ValueKind == JsonValueKind.String) n.Texte.Add(t.GetString() ?? "");
            else if (t.ValueKind == JsonValueKind.Array)
                foreach (var x in t.EnumerateArray())
                    if (x.ValueKind == JsonValueKind.String) n.Texte.Add(x.GetString() ?? "");
        }
        foreach (var x in L(o, "options"))
            n.Options.Add(new Option(S(x, "id"), S(x, "libelle"), S(x, "vers"), LireCondition(x, "si"), LireEffets(x)));
        foreach (var x in L(o, "issues"))
            n.Issues.Add(new IssueHasard(N(x, "poids", 1), S(x, "vers"), LireCondition(x, "si")));
        // Un nœud ordinaire : « recompense » (po, xp). Une fin : « recompenses » (po, xp, souvenir, titre, objet).
        n.Recompense = n.Type == "fin" ? LirePrime(o, "recompenses") : LirePrime(o, "recompense") with { Souvenir = "", Titre = "", Objet = "" };
        return n;
    }

    // La fiche (campagne.json) et ses chapitres ; fichier : nom du fichier de chapitre → son texte (null : absent).
    // null si la fiche est illisible. Un chapitre absent ou illisible est sauté (le validateur le signale).
    public static Campagne? Lire(string fiche, Func<string, string?> fichier)
    {
        try
        {
            using var doc = JsonDocument.Parse(fiche);
            var r = doc.RootElement;
            if (r.ValueKind != JsonValueKind.Object || S(r, "id") == "") return null;
            var c = new Campagne
            {
                Id = S(r, "id"), Titre = S(r, "titre"), Ton = S(r, "ton"), Accroche = S(r, "accroche"), Duree = S(r, "duree"),
                Depart = S(r, "depart"), Niveau = Math.Max(1, N(r, "niveau", 1)),
                Objets = LireNommes(r, "objets"), Souvenirs = LireNommes(r, "souvenirs"), Decors = LireNommes(r, "decors"),
                Succes = LireIds(r, "succes"), Apres = LireIds(r, "campagnes"),
            };
            if (r.TryGetProperty("variables", out var vars) && vars.ValueKind == JsonValueKind.Object)
                foreach (var x in vars.EnumerateObject())
                    c.Variables[x.Name] = x.Value.ValueKind == JsonValueKind.Number && x.Value.TryGetInt32(out var n) ? n : 0;
            foreach (var x in L(r, "chapitres"))
            {
                var ch = new Chapitre(S(x, "id"), S(x, "titre"), S(x, "fichier"));
                c.Chapitres.Add(ch);
                var texte = fichier(ch.Fichier);
                if (texte is null) continue;
                try
                {
                    using var d2 = JsonDocument.Parse(texte);
                    if (d2.RootElement.ValueKind == JsonValueKind.Object && d2.RootElement.TryGetProperty("noeuds", out var noeuds)
                        && noeuds.ValueKind == JsonValueKind.Object)
                        foreach (var x2 in noeuds.EnumerateObject())
                            if (x2.Value.ValueKind == JsonValueKind.Object) c.Noeuds.TryAdd(x2.Name, LireNoeud(x2.Name, ch.Id, x2.Value));
                }
                catch (JsonException)
                {
                    // chapitre illisible : sauté
                }
            }
            c.Indexer();
            return c;
        }
        catch (JsonException)
        {
            return null;
        }
    }

    // ---- Bibliothèque : les campagnes embarquées dans l'exécutable (ressources « campagne:<id>/<fichier> »)

    private static readonly Dictionary<string, Campagne?> Cache = new();

    private static string? Ressource(string nom)
    {
        var a = typeof(Campagnes).Assembly;
        var vrai = a.GetManifestResourceNames().FirstOrDefault(x => x.Replace('\\', '/') == "campagne:" + nom);
        if (vrai is null) return null;
        using var flux = a.GetManifestResourceStream(vrai);
        if (flux is null) return null;
        using var r = new System.IO.StreamReader(flux, Encoding.UTF8);
        return r.ReadToEnd();
    }

    // Index des campagnes disponibles (ids, triés).
    public static IReadOnlyList<string> Disponibles() =>
        typeof(Campagnes).Assembly.GetManifestResourceNames().Select(x => x.Replace('\\', '/'))
            .Where(x => x.StartsWith("campagne:", StringComparison.Ordinal) && x.EndsWith("/campagne.json", StringComparison.Ordinal))
            .Select(x => x["campagne:".Length..^"/campagne.json".Length]).OrderBy(x => x, StringComparer.Ordinal).ToList();

    // Ajoute une campagne à la bibliothèque sans passer par les ressources (tests, campagne lue d'un dossier).
    public static void Connaitre(Campagne c)
    {
        lock (Cache)
        {
            Cache[c.Id] = c;
            _exclusifs = null;
        }
    }

    // ---- Objets exclusifs : les objets « portable » des campagnes, gagnés à une fin. Ils se portent comme un article
    // de la boutique (Boutique.Trouver les connaît) mais ne s'achètent pas. Le dessin peut manquer : l'objet existe
    // quand même, sans sprite, en attendant l'illustrateur.

    private static Dictionary<string, Article>? _exclusifs;

    public static IReadOnlyCollection<Article> Exclusifs
    {
        get
        {
            lock (Cache)
            {
                if (_exclusifs is not null) return _exclusifs.Values;
                foreach (var id in Disponibles()) Charger(id);
                var d = new Dictionary<string, Article>(StringComparer.Ordinal);
                foreach (var c in Cache.Values.Where(c => c is not null).OrderBy(c => c!.Id, StringComparer.Ordinal))
                    foreach (var o in c!.Objets.Where(o => o.Portable))
                        d.TryAdd(o.Id, new Article(o.Id, o.Nom == "" ? o.Id : o.Nom,
                            Boutique.Slots.Contains(o.Emplacement) && Boutique.SurPilou(o.Emplacement) ? o.Emplacement : Boutique.Main, 0, 1, Rarete.Epique, true));
                _exclusifs = d;
                return d.Values;
            }
        }
    }

    public static Article? Exclusif(string id)
    {
        lock (Cache)
        {
            _ = Exclusifs;
            return _exclusifs!.GetValueOrDefault(id);
        }
    }

    public static bool EstExclusif(string id) => Exclusif(id) is not null;

    public static Campagne? Charger(string id)
    {
        lock (Cache)
        {
            if (Cache.TryGetValue(id, out var c)) return c;
            var fiche = Ressource(id + "/campagne.json");
            c = fiche is null ? null : Lire(fiche, f => Ressource(id + "/" + f));
            if (c is not null && c.Id != id) c = null;
            Cache[id] = c;
            return c;
        }
    }

    // ---- Partie : un résumé d'état (la base) et les décisions prises depuis

    // Une décision. E : étape (rang de la décision dans la partie) ; T : heure (ms Unix, à la seconde) ; A : appareil ;
    // N : code du nœud où elle est prise ; V : rang de l'option, ou Suite, Reussite, Rate, Abandon.
    public sealed record Entree(int E, long T, string A, string N, int V);

    // État à un point de l'histoire, en codes : nœud, variables (≠ valeur de départ), objets, drapeaux, décor, nœud du lieu.
    public sealed class Instantane
    {
        public string N { get; set; } = "";
        public Dictionary<string, int> V { get; set; } = new();
        public List<string> O { get; set; } = new();
        public List<string> D { get; set; } = new();
        public string Decor { get; set; } = "";
        public string Lieu { get; set; } = "";

        public Instantane Copie() => new() { N = N, V = new(V), O = new(O), D = new(D), Decor = Decor, Lieu = Lieu };
    }

    public sealed class Partie
    {
        // Identité : campagne, numéro de partie (croissant dans le groupe), heure de départ, appareil d'origine, graine.
        public string Campagne { get; set; } = "";
        public int P { get; set; }
        public long D { get; set; }
        public string O { get; set; } = "";
        public string Graine { get; set; } = "";
        // Campagne déjà finie une fois quand la partie a commencé : ni po ni xp, seulement ce qui manque.
        public bool Rejeu { get; set; }
        // Base : décisions déjà consommées, rang (check-points franchis), messages déjà émis dans l'étape, tirages faits,
        // curseur de temps (ms), geste (le curseur vient d'une décision), entre (le nœud est déjà entré), abandonnée.
        public int E { get; set; }
        public int R { get; set; }
        public int I { get; set; }
        public int Tirages { get; set; }
        public long T { get; set; }
        public bool Geste { get; set; }
        public bool Entre { get; set; }
        public bool Abandonnee { get; set; }
        // Reprise : on revient à un check-point (après un échec, ou une partie abandonnée qu'on reprend) ; ce que Pilou
        // redit jusqu'à la prochaine décision n'est pas une nouveauté.
        public bool Reprise { get; set; }
        public Instantane Ici { get; set; } = new();
        // Dernier check-point (null : c'est « Ici », pas encore entré).
        public Instantane? Cp { get; set; }
        // Route : une lettre par décision consommée depuis le départ (Pas64 de sa valeur), donc E lettres ; vide ou d'une
        // autre longueur : inconnue (message d'un appareil plus ancien). Deux routes dont aucune ne prolonge l'autre
        // racontent deux histoires.
        public string Chemin { get; set; } = "";
        public List<Entree> Journal { get; set; } = new();

        public Partie Copie() => new()
        {
            Campagne = Campagne, P = P, D = D, O = O, Graine = Graine, Rejeu = Rejeu, E = E, R = R, I = I, Tirages = Tirages, T = T,
            Geste = Geste, Entre = Entre, Abandonnee = Abandonnee, Reprise = Reprise, Ici = Ici.Copie(), Cp = Cp?.Copie(), Chemin = Chemin,
            Journal = new(Journal),
        };
    }

    // Un message du fil : Pilou (« pilou ») ou le choix du joueur (« joueur »). Clé stable : partie, étape, rang.
    // Reprise : Pilou le redit en revenant à un check-point (après un échec) ; l'interface peut le replier ou le
    // remplacer par un mot court (« Bon. On reprend ici. ») au lieu de le montrer comme une nouveauté.
    public sealed record Message(int P, int E, int I, string Qui, string Texte, string Noeud, string Lieu, string Humeur, string Decor, long T,
        bool Reprise = false);

    // Point où la base peut avancer. Mur : heure de la dernière décision qui y mène. Naturel : check-point ou abandon.
    public sealed record Point(Partie Base, long Mur, bool Naturel);

    public sealed record OptionVue(int Rang, string Id, string Libelle);

    // Ce que l'interface affiche.
    public sealed class Etat
    {
        public Phase Phase;
        public string Campagne = "", Noeud = "", Lieu = "", Decor = "", Humeur = "neutre";
        public string Chapitre = "", ChapitreTitre = "";
        public int ChapitreNumero, ChapitreTotal;
        public double Progression;
        // Prochaine étape, tirages faits, curseur de temps, fin de l'attente ou du repos (0 : aucune), en ms Unix.
        public int E, Tirages;
        public long T, Fin;
        public string Pendant = "", Tenue = "";
        public List<OptionVue> Options = new();
        public string Jeu = "";
        public int Difficulte, Aide, Chance;
        public SortedDictionary<string, int> Variables = new(StringComparer.Ordinal);
        public List<string> Objets = new(), Drapeaux = new();
        // Messages émis depuis la base (le fil complet est dans le carnet), nœuds à récompense franchis, fin obtenue.
        public List<Message> Messages = new();
        public List<string> Credits = new();
        public string Issue = "", TitreFin = "";
        public Prime Recompenses = new(0, 0);
        public bool Rejeu;
        // On vient de revenir à un check-point (échec, reprise d'une partie abandonnée) et rien n'a encore été décidé.
        public bool Reprise;
        public List<Point> Points = new();
        // Route jusqu'ici (voir Partie.Chemin) ; inconnue si sa longueur n'est pas E.
        public string Chemin = "";

        public bool EnAttente => Phase is Phase.Attente or Phase.Repos;
        public bool EnCours => Phase is Phase.Choix or Phase.Epreuve or Phase.Depart or Phase.Attente or Phase.Repos;

        // Texte canonique (une ligne), pour les vecteurs partagés avec le téléphone.
        public string Texte()
        {
            var ci = CultureInfo.InvariantCulture;
            ulong h = 14695981039346656037UL;
            foreach (var m in Messages)
                foreach (char ch in $"{m.E}.{m.I}.{m.Qui}.{m.Noeud}.{m.Humeur}.{m.Decor}.{m.Lieu}.{m.T}.{(m.Reprise ? 1 : 0)}.{m.Texte}\n")
                {
                    h ^= ch;
                    h *= 1099511628211UL;
                }
            return string.Join("|", new[]
            {
                "phase=" + Phase, "noeud=" + Noeud, "e=" + E.ToString(ci), "t=" + T.ToString(ci), "fin=" + Fin.ToString(ci),
                "reprise=" + (Reprise ? "1" : "0"),
                "tirages=" + Tirages.ToString(ci), "chapitre=" + Chapitre + ":" + ChapitreNumero.ToString(ci) + "/" + ChapitreTotal.ToString(ci),
                "lieu=" + Lieu, "decor=" + Decor, "humeur=" + Humeur, "pendant=" + Pendant, "tenue=" + Tenue,
                "options=" + string.Join(",", Options.Select(o => o.Rang.ToString(ci) + ":" + o.Id)),
                "jeu=" + Jeu + ":" + Difficulte.ToString(ci) + ":" + Aide.ToString(ci) + ":" + Chance.ToString(ci),
                "vars=" + string.Join(",", Variables.Select(kv => kv.Key + ":" + kv.Value.ToString(ci))),
                "objets=" + string.Join(",", Objets), "drapeaux=" + string.Join(",", Drapeaux),
                "credits=" + string.Join(",", Credits), "issue=" + Issue + ":" + Recompenses.Po.ToString(ci) + ":" + Recompenses.Xp.ToString(ci),
                "messages=" + Messages.Count.ToString(ci) + ":" + h.ToString("x16", ci),
            });
        }
    }

    // ---- Rejeu

    private sealed class Cours
    {
        public string Noeud = "";
        public Dictionary<string, int> Vars = new(StringComparer.Ordinal);
        public SortedSet<string> Objets = new(StringComparer.Ordinal), Drapeaux = new(StringComparer.Ordinal);
        public string Decor = "", LieuDe = "", Chemin = "";
        public bool AvecCp;
        public string CpNoeud = "", CpDecor = "", CpLieuDe = "";
        public Dictionary<string, int> CpVars = new(StringComparer.Ordinal);
        public SortedSet<string> CpObjets = new(StringComparer.Ordinal), CpDrapeaux = new(StringComparer.Ordinal);
        public int E, R, I, Tirages, Pas;
        public long T, Fin, Mur = long.MinValue;
        public bool Geste, Reprise;
        public Phase Phase = Phase.Aucune;
        public List<Message> Messages = new();
        public List<string> Credits = new();
        public List<Point> Points = new();

        public Cours Copie() => new()
        {
            Noeud = Noeud, Chemin = Chemin, Vars = new(Vars, StringComparer.Ordinal), Objets = new(Objets, StringComparer.Ordinal),
            Drapeaux = new(Drapeaux, StringComparer.Ordinal), Decor = Decor, LieuDe = LieuDe, AvecCp = AvecCp, CpNoeud = CpNoeud,
            CpDecor = CpDecor, CpLieuDe = CpLieuDe, CpVars = new(CpVars, StringComparer.Ordinal),
            CpObjets = new(CpObjets, StringComparer.Ordinal), CpDrapeaux = new(CpDrapeaux, StringComparer.Ordinal),
            E = E, R = R, I = I, Tirages = Tirages, Pas = Pas, T = T, Fin = Fin, Mur = Mur, Geste = Geste, Reprise = Reprise, Phase = Phase,
            Messages = new(Messages), Credits = new(Credits), Points = new(Points),
        };
    }

    private enum Mode { Neuf, Repris, Suite }

    private sealed class Moteur
    {
        private readonly Campagne _c;
        private readonly Partie _p;

        public Moteur(Campagne c, Partie p)
        {
            _c = c;
            _p = p;
        }

        private bool Vrai(Condition? k, Cours s)
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

        private static void Appliquer(IEnumerable<Effet> effets, Cours s)
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

        // Instantané (en codes) de l'état courant, prêt à entrer dans le nœud donné.
        private Instantane Photo(string noeud, Dictionary<string, int> vars, IEnumerable<string> objets, IEnumerable<string> drapeaux,
            string decor, string lieuDe)
        {
            var x = new Instantane { N = Code(noeud), Decor = decor == "" ? "" : Code(decor), Lieu = lieuDe == "" ? "" : Code(lieuDe) };
            foreach (var kv in vars.OrderBy(kv => kv.Key, StringComparer.Ordinal))
                if (kv.Value != _c.Variables.GetValueOrDefault(kv.Key)) x.V[Code(kv.Key)] = kv.Value;
            x.O = objets.Select(Code).OrderBy(c => c, StringComparer.Ordinal).ToList();
            x.D = drapeaux.Select(Code).OrderBy(c => c, StringComparer.Ordinal).ToList();
            return x;
        }

        private Partie Base(Cours s, Instantane ici, Instantane? cp, int i, bool entre, bool abandonnee) => new()
        {
            Campagne = _p.Campagne, P = _p.P, D = _p.D, O = _p.O, Graine = _p.Graine, Rejeu = _p.Rejeu,
            E = s.E, R = s.R, I = i, Tirages = s.Tirages, T = s.T, Geste = s.Geste, Entre = entre, Abandonnee = abandonnee,
            Reprise = s.Reprise && !abandonnee, Ici = ici, Cp = cp, Chemin = s.Chemin,
        };

        private Instantane PhotoCp(Cours s) => Photo(s.CpNoeud, s.CpVars, s.CpObjets, s.CpDrapeaux, s.CpDecor, s.CpLieuDe);

        private void Charger(Instantane x, Cours s, bool cp)
        {
            var vars = new Dictionary<string, int>(_c.Variables, StringComparer.Ordinal);
            foreach (var kv in x.V)
                if (_c.Decode('v', kv.Key) is { } id) vars[id] = kv.Value;
            var objets = new SortedSet<string>(StringComparer.Ordinal);
            foreach (var k in x.O)
                if (_c.Decode('o', k) is { } id) objets.Add(id);
            var drapeaux = new SortedSet<string>(StringComparer.Ordinal);
            foreach (var k in x.D)
                if (_c.Decode('d', k) is { } id) drapeaux.Add(id);
            string decor = x.Decor == "" ? "" : _c.Decode('c', x.Decor) ?? "", lieu = x.Lieu == "" ? "" : _c.Decode('n', x.Lieu) ?? "";
            string noeud = _c.Decode('n', x.N) ?? "";
            if (cp)
            {
                s.AvecCp = true;
                (s.CpNoeud, s.CpVars, s.CpObjets, s.CpDrapeaux, s.CpDecor, s.CpLieuDe) = (noeud, vars, objets, drapeaux, decor, lieu);
            }
            else (s.Noeud, s.Vars, s.Objets, s.Drapeaux, s.Decor, s.LieuDe) = (noeud, vars, objets, drapeaux, decor, lieu);
        }

        private string Lieu(Cours s) => s.LieuDe == "" ? "" : _c.Noeud(s.LieuDe)?.Lieu ?? "";

        private void Dire(Cours s, string qui, string texte, Noeud n) =>
            s.Messages.Add(new Message(_p.P, s.E, s.I++, qui, texte, n.Id, Lieu(s), qui == "pilou" ? n.Humeur : "neutre", s.Decor, s.T, s.Reprise));

        private bool LancerDe(Cours s, Noeud n) =>
            Tirage(_p.Graine, s.Tirages).Suivant(100) < ChanceDe(n.Difficulte, n.Bonus == "" ? 0 : s.Vars.GetValueOrDefault(n.Bonus));

        private void Partir(Cours s, Noeud n)
        {
            int minutes = Math.Max(1, n.DureeMin);
            if (n.DureeMax > n.DureeMin) minutes = Tirage(_p.Graine, s.Tirages++).Entre(Math.Max(1, n.DureeMin), n.DureeMax);
            s.Fin = s.T + minutes * 60_000L;
            s.Phase = Phase.Attente;
        }

        // Entre dans un nœud et suit les nœuds automatiques jusqu'à un arrêt (décision, attente, repos, fin).
        public void Entrer(Cours s, string id, Mode mode)
        {
            while (true)
            {
                if (++s.Pas > MaxPas || _c.Noeud(id) is not { } n)
                {
                    s.Phase = Phase.Cassee;
                    return;
                }
                s.Noeud = id;
                int avant = s.I;
                if (mode == Mode.Neuf)
                {
                    if (n.Checkpoint || !s.AvecCp)
                    {
                        s.AvecCp = true;
                        s.CpNoeud = id;
                        s.CpVars = new(s.Vars, StringComparer.Ordinal);
                        s.CpObjets = new(s.Objets, StringComparer.Ordinal);
                        s.CpDrapeaux = new(s.Drapeaux, StringComparer.Ordinal);
                        s.CpDecor = s.Decor;
                        s.CpLieuDe = s.LieuDe;
                        if (n.Checkpoint) s.Points.Add(new Point(Base(s, PhotoCp(s), null, s.I, false, false), s.Mur, true));
                        if (n.Checkpoint) s.R++;
                    }
                    if (n.Decor != "") s.Decor = n.Decor;
                    if (n.Lieu != "") s.LieuDe = id;
                    Appliquer(n.Effets, s);
                    if ((n.Type == "fin" || !n.Recompense.Vide) && !s.Credits.Contains(id)) s.Credits.Add(id);
                }
                if (mode != Mode.Suite)
                    foreach (var t in n.Texte) Dire(s, "pilou", t, n);
                switch (n.Type)
                {
                    case "recit":
                        id = n.Suite;
                        mode = Mode.Neuf;
                        continue;
                    case "choix":
                        s.Phase = Phase.Choix;
                        break;
                    case "attente":
                        if (!s.Geste) s.Phase = Phase.Depart;
                        else
                        {
                            Partir(s, n);
                            return;
                        }
                        break;
                    case "epreuve":
                        if (JeuAuto(n.Jeu))
                        {
                            bool ok = LancerDe(s, n);
                            s.Tirages++;
                            id = ok ? n.Reussite : n.Echec;
                            mode = Mode.Neuf;
                            continue;
                        }
                        s.Phase = Phase.Epreuve;
                        break;
                    case "hasard":
                    {
                        // On tire parmi les issues dont la condition est vraie (un « hasard » sert aussi d'aiguillage :
                        // conditions complémentaires). Aucune de vraie, ce que le validateur interdit : parmi toutes.
                        var possibles = n.Issues.Where(x => Vrai(x.Si, s)).ToList();
                        if (possibles.Count == 0) possibles = n.Issues;
                        if (possibles.Count == 0)
                        {
                            s.Phase = Phase.Cassee;
                            return;
                        }
                        int total = possibles.Sum(x => Math.Max(1, x.Poids));
                        int tire = Tirage(_p.Graine, s.Tirages++).Suivant(total);
                        var issue = possibles[^1];
                        foreach (var x in possibles)
                        {
                            tire -= Math.Max(1, x.Poids);
                            if (tire < 0)
                            {
                                issue = x;
                                break;
                            }
                        }
                        id = issue.Vers;
                        mode = Mode.Neuf;
                        continue;
                    }
                    case "echec":
                        s.Fin = s.T + Math.Max(1, n.ReposMin) * 60_000L;
                        s.Phase = Phase.Repos;
                        return;
                    case "fin":
                        s.Phase = Phase.Fin;
                        return;
                    default:
                        s.Phase = Phase.Cassee;
                        return;
                }
                // Arrêt sur une décision : un point de secours (base au milieu d'un chapitre, si le journal devient trop long).
                s.Points.Add(new Point(Base(s, Photo(s.Noeud, s.Vars, s.Objets, s.Drapeaux, s.Decor, s.LieuDe), PhotoCp(s), avant, true, false), s.Mur, false));
                return;
            }
        }

        // L'attente ou le repos est fini : Pilou revient (ou repart du dernier check-point).
        public void Ecouler(Cours s)
        {
            var n = _c.Noeud(s.Noeud)!;
            s.T = s.Fin;
            s.Fin = 0;
            s.Geste = false;
            if (s.Phase == Phase.Attente) Entrer(s, n.Suite, Mode.Neuf);
            else
            {
                s.Vars = new(s.CpVars, StringComparer.Ordinal);
                s.Objets = new(s.CpObjets, StringComparer.Ordinal);
                s.Drapeaux = new(s.CpDrapeaux, StringComparer.Ordinal);
                s.Decor = s.CpDecor;
                s.LieuDe = s.CpLieuDe;
                s.Reprise = true;
                Entrer(s, s.CpNoeud, Mode.Neuf);
            }
        }

        public List<Option> Visibles(Cours s, Noeud n) => n.Options.Where(o => Vrai(o.Si, s)).ToList();

        public bool Valide(Cours s, Entree x)
        {
            if (x.N != Code(s.Noeud)) return false;
            switch (s.Phase)
            {
                case Phase.Choix:
                    var n = _c.Noeud(s.Noeud)!;
                    return x.V == Abandon || (x.V >= 0 && x.V < n.Options.Count && Vrai(n.Options[x.V].Si, s));
                case Phase.Epreuve: return x.V is Reussite or Rate or Abandon;
                case Phase.Depart: return x.V is Suite or Abandon;
                case Phase.Attente:
                case Phase.Repos: return x.V == Abandon && x.T < s.Fin;
                default: return false;
            }
        }

        public void Decider(Cours s, Entree x)
        {
            var n = _c.Noeud(s.Noeud)!;
            var phase = s.Phase;
            s.T = Math.Max(s.T, x.T);
            s.Mur = x.T;
            if (s.Chemin.Length == s.E) s.Chemin += Pas64(x.V);
            s.E++;
            s.I = 0;
            s.Fin = 0;
            if (x.V == Abandon)
            {
                s.Phase = Phase.Abandon;
                s.Points.Add(new Point(Base(s, PhotoCp(s), null, 0, false, true), s.Mur, true));
                return;
            }
            s.Geste = true;
            s.Reprise = false;
            switch (phase)
            {
                case Phase.Choix:
                    var o = n.Options[x.V];
                    Dire(s, "joueur", o.Libelle, n);
                    Appliquer(o.Effets, s);
                    Entrer(s, o.Vers, Mode.Neuf);
                    break;
                case Phase.Epreuve:
                    s.Tirages++;
                    Entrer(s, x.V == Reussite ? n.Reussite : n.Echec, Mode.Neuf);
                    break;
                case Phase.Depart:
                    Partir(s, n);
                    break;
            }
        }

        private static bool Timer(Cours s) => s.Phase is Phase.Attente or Phase.Repos;

        private static bool Terminal(Cours s) => s.Phase is Phase.Fin or Phase.Abandon or Phase.Cassee or Phase.Aucune;

        public Cours Jouer(long maintenant)
        {
            var s = new Cours
            {
                E = _p.E, R = _p.R, I = _p.I, Tirages = _p.Tirages, T = _p.T, Geste = _p.Geste, Reprise = _p.Reprise, Chemin = _p.Chemin,
            };
            Charger(_p.Ici, s, false);
            if (_p.Cp is not null) Charger(_p.Cp, s, true);
            if (_p.Abandonnee)
            {
                // Base d'une partie abandonnée : « Ici » est le check-point où elle reprendra.
                Charger(_p.Ici, s, true);
                s.Phase = Phase.Abandon;
                return s;
            }
            if (s.Noeud == "" || _c.Noeud(s.Noeud) is null)
            {
                s.Phase = Phase.Cassee;
                return s;
            }
            Entrer(s, s.Noeud, _p.Entre ? Mode.Repris : Mode.Neuf);

            var parEtape = new Dictionary<int, List<Entree>>();
            foreach (var x in Ordonner(_p.Journal))
            {
                if (!parEtape.TryGetValue(x.E, out var l)) parEtape[x.E] = l = new List<Entree>();
                l.Add(x);
            }
            while (!Terminal(s))
            {
                var candidats = parEtape.GetValueOrDefault(s.E) ?? new List<Entree>();
                var v = candidats.FirstOrDefault(x => Valide(s, x));
                if (!Timer(s))
                {
                    if (v is null) break;
                    Decider(s, v);
                    continue;
                }
                if (v is not null)
                {
                    Decider(s, v); // abandon pendant l'attente
                    continue;
                }
                if (maintenant >= s.Fin)
                {
                    Ecouler(s);
                    continue;
                }
                // L'attente n'est pas finie ici, mais un autre appareil (horloge en avance) a peut-être déjà décidé la
                // suite : on regarde plus loin sans rien changer, et on n'y va que si une décision valide nous y attend.
                if (candidats.Count == 0) break;
                var plus = s.Copie();
                Entree? trouve = null;
                while (Timer(plus) && trouve is null)
                {
                    Ecouler(plus);
                    if (Terminal(plus)) break;
                    trouve = candidats.FirstOrDefault(x => Valide(plus, x));
                }
                if (trouve is null) break;
                s = plus;
                Decider(s, trouve);
            }
            return s;
        }

        public Etat Vue(Cours s)
        {
            var e = new Etat
            {
                Phase = s.Phase, Campagne = _c.Id, Noeud = s.Noeud, Lieu = Lieu(s), Decor = s.Decor, E = s.E, Tirages = s.Tirages, T = s.T,
                Fin = Timer(s) ? s.Fin : 0, Messages = s.Messages, Credits = s.Credits, Points = s.Points, Rejeu = _p.Rejeu, Reprise = s.Reprise,
                Chemin = s.Chemin, ChapitreTotal = _c.Chapitres.Count,
            };
            foreach (var kv in s.Vars) e.Variables[kv.Key] = kv.Value;
            e.Objets = s.Objets.ToList();
            e.Drapeaux = s.Drapeaux.ToList();
            if (_c.Noeud(s.Noeud) is not { } n) return e;
            e.Humeur = n.Humeur;
            e.Chapitre = n.Chapitre;
            int rang = _c.Chapitres.FindIndex(c => c.Id == n.Chapitre);
            e.ChapitreNumero = rang + 1;
            e.ChapitreTitre = rang >= 0 ? _c.Chapitres[rang].Titre : "";
            e.Progression = s.Phase == Phase.Fin ? 1 : _c.Chapitres.Count == 0 ? 0 : Math.Max(0, rang) / (double)_c.Chapitres.Count;
            switch (s.Phase)
            {
                case Phase.Choix:
                    for (int i = 0; i < n.Options.Count; i++)
                        if (Vrai(n.Options[i].Si, s)) e.Options.Add(new OptionVue(i, n.Options[i].Id, n.Options[i].Libelle));
                    break;
                case Phase.Epreuve:
                    e.Jeu = n.Jeu;
                    e.Difficulte = Math.Clamp(n.Difficulte, 1, 3);
                    e.Aide = n.Bonus == "" ? 0 : s.Vars.GetValueOrDefault(n.Bonus);
                    e.Chance = ChanceDe(n.Difficulte, e.Aide);
                    break;
                case Phase.Depart:
                case Phase.Attente:
                    e.Pendant = n.Pendant;
                    e.Tenue = Tenues.Contains(n.Tenue) ? n.Tenue : "marche";
                    break;
                case Phase.Repos:
                    e.Pendant = "Pilou se repose";
                    e.Tenue = "nuit";
                    break;
                case Phase.Fin:
                    e.Issue = n.Issue;
                    e.TitreFin = n.Titre;
                    e.Recompenses = n.Recompense;
                    break;
            }
            return e;
        }
    }

    // Ordre canonique des décisions : étape, heure, appareil, nœud, valeur. Doublons retirés.
    public static List<Entree> Ordonner(IEnumerable<Entree> journal)
    {
        var l = journal.Distinct().ToList();
        l.Sort((a, b) =>
        {
            if (a.E != b.E) return a.E.CompareTo(b.E);
            if (a.T != b.T) return a.T.CompareTo(b.T);
            int c = string.CompareOrdinal(a.A, b.A);
            if (c != 0) return c;
            c = string.CompareOrdinal(a.N, b.N);
            return c != 0 ? c : a.V.CompareTo(b.V);
        });
        return l;
    }

    // Journal borné : à partir de l'étape de la base, au plus MaxParEtape décisions par étape (les plus anciennes).
    private static List<Entree> Borner(IEnumerable<Entree> journal, int depuis)
    {
        var r = new List<Entree>();
        int etape = int.MinValue, n = 0;
        foreach (var x in Ordonner(journal))
        {
            if (x.E < depuis || x.E > depuis + MaxAvance) continue;
            if (x.E != etape)
            {
                etape = x.E;
                n = 0;
            }
            if (++n <= MaxParEtape) r.Add(x);
        }
        return r;
    }

    // L'état d'une partie à l'heure donnée (ms Unix) : pur, même résultat partout.
    public static Etat Rejouer(Campagne c, Partie p, long maintenant)
    {
        var r = new Moteur(c, p);
        return r.Vue(r.Jouer(maintenant));
    }

    // Nouvelle partie, au nœud de départ. p : numéro de partie (plus grand que tous ceux connus du groupe).
    public static Partie Nouvelle(Campagne c, int p, long maintenant, string appareil, string graine, bool rejeu) => new()
    {
        Campagne = c.Id, P = p, D = Seconde(maintenant), O = appareil, Graine = graine, Rejeu = rejeu, T = Seconde(maintenant), Geste = true,
        Ici = new Instantane { N = Code(c.Depart) },
    };

    // Ajoute une décision au journal si elle est valide maintenant ; null sinon (rien ne change).
    public static Partie? Decider(Campagne c, Partie p, long maintenant, string appareil, int valeur)
    {
        var r = new Moteur(c, p);
        var s = r.Jouer(maintenant);
        var x = new Entree(s.E, Seconde(maintenant), appareil, Code(s.Noeud), valeur);
        if (!r.Valide(s, x)) return null;
        var q = p.Copie();
        q.Journal = Borner(q.Journal.Append(x), q.E);
        return q;
    }

    // Le tirage « des » qui remplace un mini-jeu que l'appareil ne sait pas jouer (même résultat partout).
    public static bool DeDe(Campagne c, Partie p, Etat e) =>
        Tirage(p.Graine, e.Tirages).Suivant(100) < ChanceDe(e.Difficulte, e.Aide);

    // Avance la base : au dernier check-point (ou abandon) dont la décision qui y mène a plus de Grace ; au milieu
    // d'un chapitre si le journal devient trop long. Le journal ne garde que les décisions à partir de la base.
    public static Partie Compacter(Campagne c, Partie p, long maintenant)
    {
        var e = Rejouer(c, p, maintenant);
        Point? choisi = null;
        foreach (var pt in e.Points)
            if (pt.Naturel && pt.Mur <= maintenant - Grace) choisi = pt;
        if (e.E - (choisi?.Base.E ?? p.E) > MaxEntrees)
            choisi = e.Points.FirstOrDefault(pt => e.E - pt.Base.E <= GardeEntrees) ?? choisi;
        var q = choisi is null || !Avance(choisi.Base, p) ? p.Copie() : choisi.Base.Copie();
        q.Journal = Borner(p.Journal, q.E);
        return q;
    }

    // ---- Comparaisons et fusion (sans les fichiers de campagne : tout est en codes)

    private static int CompareIdentite(Partie a, Partie b)
    {
        if (a.P != b.P) return b.P.CompareTo(a.P);          // le plus grand numéro d'abord
        if (a.D != b.D) return a.D.CompareTo(b.D);          // puis la plus ancienne
        int c = string.CompareOrdinal(a.O, b.O);
        if (c != 0) return c;
        c = string.CompareOrdinal(a.Campagne, b.Campagne);
        return c != 0 ? c : string.CompareOrdinal(a.Graine, b.Graine);
    }

    private static bool MemeIdentite(Partie a, Partie b) => CompareIdentite(a, b) == 0;

    // < 0 : la base de a est préférée (plus avancée ; à égalité la plus ancienne, puis l'ordre du texte).
    private static int CompareBase(Partie a, Partie b)
    {
        if (a.E != b.E) return b.E.CompareTo(a.E);
        if (a.R != b.R) return b.R.CompareTo(a.R);
        if (a.T != b.T) return a.T.CompareTo(b.T);
        return string.CompareOrdinal(JsonPartie(a, false), JsonPartie(b, false));
    }

    private static bool Avance(Partie a, Partie b) => CompareBase(a, b) < 0;

    // Deux vues de la même partie : la meilleure base, l'union des décisions.
    private static Partie Unir(Partie a, Partie b)
    {
        var q = (CompareBase(a, b) <= 0 ? a : b).Copie();
        q.Journal = Borner(a.Journal.Concat(b.Journal), q.E);
        return q;
    }

    // La partie qui fait foi entre deux (null : absente).
    private static Partie? Meilleure(Partie? a, Partie? b)
    {
        if (a is null) return b?.Copie();
        if (b is null) return a.Copie();
        int c = CompareIdentite(a, b);
        return c == 0 ? Unir(a, b) : c < 0 ? a.Copie() : b.Copie();
    }

    // ---- Carnet : ce qu'un appareil garde

    // Bilan d'une campagne dans le groupe. P : numéro de sa dernière partie commencée ; Finie : numéro de la dernière
    // partie menée à une fin ; Fins : code de la fin → première fois (secondes Unix) ; Noeuds : codes des nœuds dont
    // la récompense (po, xp) est acquise, triés.
    public sealed class Bilan
    {
        public int P { get; set; }
        public int Finie { get; set; }
        public Dictionary<string, long> Fins { get; set; } = new();
        public List<string> Noeuds { get; set; } = new();
    }

    public sealed class Carnet
    {
        public Partie? Courante { get; set; }
        public Dictionary<string, Partie> Suspendues { get; set; } = new();
        public Dictionary<string, Bilan> Historique { get; set; } = new();
        // Propre à l'appareil : le fil des messages (les MaxFil derniers), la clé du dernier message lu,
        // les récompenses déjà versées ici (PC), celles qu'un PC a déjà versées (téléphone).
        public List<Message> Fil { get; set; } = new();
        public string Lu { get; set; } = "";
        public List<string> Payes { get; set; } = new();
        public List<string> PayesPc { get; set; } = new();

        public int NonLus => Fil.Count(m => m.Qui == "pilou" && ApresLu(m, Lu));
    }

    private static string Cle(Message m) => string.Create(CultureInfo.InvariantCulture, $"{m.P}.{m.E}.{m.I}");

    private static bool ApresLu(Message m, string lu)
    {
        var c = lu.Split('.');
        if (c.Length != 3 || !int.TryParse(c[0], out var p) || !int.TryParse(c[1], out var e) || !int.TryParse(c[2], out var i)) return true;
        return m.P != p ? m.P > p : m.E != e ? m.E > e : m.I > i;
    }

    public static bool NonLu(Carnet k, Message m) => ApresLu(m, k.Lu);

    public static void MarquerLu(Carnet k)
    {
        if (k.Fil.Count > 0) k.Lu = Cle(k.Fil[^1]);
    }

    private static Bilan BilanDe(Carnet k, string campagne)
    {
        if (!k.Historique.TryGetValue(campagne, out var b)) k.Historique[campagne] = b = new Bilan();
        return b;
    }

    // Numéro de la prochaine partie : plus grand que tout ce que ce carnet connaît.
    private static int Prochain(Carnet k)
    {
        int p = k.Courante?.P ?? 0;
        foreach (var s in k.Suspendues.Values) p = Math.Max(p, s.P);
        foreach (var b in k.Historique.Values) p = Math.Max(p, Math.Max(b.P, b.Finie));
        return p + 1;
    }

    // Ce que la partie apporte à l'historique (récompenses acquises, fin obtenue).
    private static bool Noter(Carnet k, Partie p, Etat e)
    {
        var b = BilanDe(k, p.Campagne);
        bool change = false;
        if (p.P > b.P)
        {
            b.P = p.P;
            change = true;
        }
        if (!p.Rejeu)
            foreach (var id in e.Credits)
            {
                var code = Code(id);
                if (b.Noeuds.Contains(code)) continue;
                b.Noeuds.Add(code);
                b.Noeuds.Sort(StringComparer.Ordinal);
                change = true;
            }
        if (e.Phase == Phase.Fin)
        {
            var code = Code(e.Noeud);
            long t = e.T / 1000;
            if (!b.Fins.TryGetValue(code, out var avant) || t < avant)
            {
                b.Fins[code] = t;
                change = true;
            }
            if (p.P > b.Finie)
            {
                b.Finie = p.P;
                change = true;
            }
        }
        return change;
    }

    // Parties suspendues périmées : remplacées par une partie plus récente de la même campagne, ou finie depuis.
    private static void Nettoyer(Carnet k)
    {
        if (k.Courante is { } c) BilanDe(k, c.Campagne).P = Math.Max(BilanDe(k, c.Campagne).P, c.P);
        foreach (var (id, s) in k.Suspendues.ToList())
        {
            var b = BilanDe(k, id);
            b.P = Math.Max(b.P, s.P);
            if (s.P < b.P || s.P <= b.Finie || (k.Courante is { } x && x.Campagne == id && CompareIdentite(x, s) <= 0)) k.Suspendues.Remove(id);
        }
    }

    // La partie mise de côté : sa base au dernier check-point, marquée abandonnée (null : finie, rien à garder).
    private static Partie? Suspendre(Carnet k, Partie p, Func<string, Campagne?> biblio, long maintenant)
    {
        if (p.Abandonnee && p.Journal.Count == 0) return p.Copie();
        if (biblio(p.Campagne) is not { } c) return p.Copie(); // campagne inconnue ici : gardée telle quelle
        var e = Rejouer(c, p, maintenant);
        Noter(k, p, e);
        if (e.Phase is Phase.Fin or Phase.Cassee) return null;
        // Abandon : la base « abandonnée » au dernier check-point ; sinon la même, construite ici.
        var abandon = e.Points.LastOrDefault(pt => pt.Base.Abandonnee)?.Base;
        if (abandon is not null) return abandon.Copie();
        var q = Decider(c, p, Math.Max(maintenant, e.T), p.O, Abandon);
        if (q is null) return p.Copie();
        return Rejouer(c, q, maintenant).Points.LastOrDefault(pt => pt.Base.Abandonnee)?.Base.Copie() ?? p.Copie();
    }

    private static void Ranger(Carnet k, Partie perdante, Func<string, Campagne?> biblio, long maintenant)
    {
        if (Suspendre(k, perdante, biblio, maintenant) is not { } s) return;
        k.Suspendues[s.Campagne] = Meilleure(k.Suspendues.GetValueOrDefault(s.Campagne), s)!;
    }

    // À appeler régulièrement (et après chaque décision ou réception) : rejoue la partie en cours, note les
    // récompenses acquises dans l'historique, avance la base, complète le fil. Renvoie l'état (null : aucune partie,
    // ou campagne inconnue de cet appareil).
    public static Etat? Actualiser(Carnet k, Func<string, Campagne?> biblio, long maintenant)
    {
        Nettoyer(k);
        if (k.Courante is not { } p || biblio(p.Campagne) is not { } c) return null;
        var e = Rejouer(c, p, maintenant);
        Noter(k, p, e);
        // Le fil : ce qui précède la base reste ; ce qui la suit est remplacé par le rejeu (une décision peut avoir perdu).
        k.Fil.RemoveAll(m => m.P == p.P && (m.E > p.E || (m.E == p.E && m.I >= p.I)));
        k.Fil.AddRange(e.Messages);
        if (k.Fil.Count > MaxFil) k.Fil.RemoveRange(0, k.Fil.Count - MaxFil);
        k.Courante = Compacter(c, p, maintenant);
        return e;
    }

    // ---- Décisions sur le carnet (ce qu'appelle l'interface). Chaque fonction renvoie null si c'est fait, sinon la raison.

    public static string NouvelleGraine() => Convert.ToHexString(RandomNumberGenerator.GetBytes(4)).ToLowerInvariant();

    public static bool Finie(Carnet k, string campagne) => k.Historique.TryGetValue(campagne, out var b) && b.Fins.Count > 0;

    // « a », « a et b », « a, b et c ».
    private static string Et(IReadOnlyList<string> l) => l.Count <= 1 ? string.Concat(l) : string.Join(", ", l.Take(l.Count - 1)) + " et " + l[^1];

    // Ce qu'il manque pour ouvrir la campagne, en une ligne sans rien dévoiler de l'histoire ("" : ouverte) : le niveau,
    // les hauts faits (par leur nom), les campagnes à finir (par leur titre). Le téléphone fait le même texte.
    public static string Manque(Carnet k, Campagne c, int niveau, IReadOnlyCollection<string> succes, Func<string, Campagne?> biblio)
    {
        var l = new List<string>();
        if (niveau < c.Niveau) l.Add($"au niveau {c.Niveau}");
        var hf = c.Succes.Where(id => !succes.Contains(id))
            .Select(id => "« " + (PilouBureau.Succes.Tous.FirstOrDefault(d => d.Id == id)?.Nom ?? id) + " »").ToList();
        if (hf.Count > 0) l.Add((hf.Count == 1 ? "avec le haut fait " : "avec les hauts faits ") + Et(hf));
        var ca = c.Apres.Where(id => !Finie(k, id)).Select(id => "« " + (biblio(id)?.Titre is { Length: > 0 } t ? t : id) + " »").ToList();
        if (ca.Count > 0) l.Add("après " + Et(ca));
        return l.Count == 0 ? "" : "s'ouvre " + Et(l);
    }

    // Une partie est-elle en cours (ni finie, ni abandonnée) ?
    public static bool EnCours(Carnet k, Func<string, Campagne?> biblio, long maintenant)
    {
        if (k.Courante is not { } p) return false;
        if (biblio(p.Campagne) is not { } c) return !p.Abandonnee;
        return Rejouer(c, p, maintenant).EnCours;
    }

    // Peut-on reprendre cette campagne à un check-point (partie abandonnée ou mise de côté) ?
    public static bool Reprenable(Carnet k, Campagne c, long maintenant) =>
        k.Suspendues.ContainsKey(c.Id) || (k.Courante is { } p && p.Campagne == c.Id && Rejouer(c, p, maintenant).Phase == Phase.Abandon);

    // Démarre la campagne, ou la reprend à son dernier check-point si elle avait été abandonnée (neuf : repartir du
    // début quand même). Une seule campagne à la fois : il faut finir ou abandonner celle en cours.
    public static string? Demarrer(Carnet k, Campagne c, int niveau, long maintenant, string appareil, Func<string, Campagne?> biblio,
        string? graine = null, bool neuf = false, IReadOnlyCollection<string>? succes = null)
    {
        if (niveau < c.Niveau) return $"niveau {c.Niveau} requis";
        // succes null : l'appelant ne vérifie pas les hauts faits ni les campagnes à finir (essai, vitrine).
        if (succes is not null && Manque(k, c, niveau, succes, biblio) is { Length: > 0 } manque) return manque;
        if (c.Noeud(c.Depart) is null) return "campagne illisible";
        Actualiser(k, biblio, maintenant);
        if (EnCours(k, biblio, maintenant)) return "une campagne est déjà en cours";
        int numero = Prochain(k);
        if (k.Courante is { } avant) Ranger(k, avant, biblio, maintenant);
        k.Suspendues.TryGetValue(c.Id, out var reprise);
        k.Suspendues.Remove(c.Id);
        // Reprise : l'état du dernier check-point, sous une nouvelle identité de partie.
        var b = reprise is null || neuf ? null : Suspendre(k, reprise, biblio, maintenant);
        Partie p;
        if (b is not null)
        {
            p = b.Copie();
            p.Journal = new();
            if (p.Abandonnee)
            {
                p.Entre = false;
                p.Cp = null;
                p.I = 0;
            }
            p.Abandonnee = false;
            p.Reprise = true;
            p.P = numero;
            p.D = p.T = Seconde(maintenant);
            p.O = appareil;
            p.Geste = true;
            p.Rejeu = p.Rejeu || Finie(k, c.Id);
        }
        else p = Nouvelle(c, numero, maintenant, appareil, graine ?? NouvelleGraine(), Finie(k, c.Id));
        k.Courante = p;
        Actualiser(k, biblio, maintenant);
        return null;
    }

    private static string? Decider(Carnet k, Campagne c, long maintenant, string appareil, int valeur)
    {
        if (k.Courante is not { } p || p.Campagne != c.Id) return "aucune partie en cours";
        var q = Decider(c, p, maintenant, appareil, valeur);
        if (q is null) return "ce n'est pas possible maintenant";
        k.Courante = q;
        Actualiser(k, _ => c, maintenant);
        return null;
    }

    public static string? Choisir(Carnet k, Campagne c, long maintenant, string appareil, string option)
    {
        if (k.Courante is not { } p || p.Campagne != c.Id) return "aucune partie en cours";
        var e = Rejouer(c, p, maintenant);
        var o = e.Options.FirstOrDefault(x => x.Id == option);
        return e.Phase != Phase.Choix || o is null ? "ce n'est pas possible maintenant" : Decider(k, c, maintenant, appareil, o.Rang);
    }

    public static string? Continuer(Carnet k, Campagne c, long maintenant, string appareil) => Decider(k, c, maintenant, appareil, Suite);

    public static string? Epreuve(Carnet k, Campagne c, long maintenant, string appareil, bool reussie) =>
        Decider(k, c, maintenant, appareil, reussie ? Reussite : Rate);

    public static string? EpreuveAuDe(Carnet k, Campagne c, long maintenant, string appareil)
    {
        if (k.Courante is not { } p || p.Campagne != c.Id) return "aucune partie en cours";
        var e = Rejouer(c, p, maintenant);
        return e.Phase != Phase.Epreuve ? "ce n'est pas possible maintenant" : Epreuve(k, c, maintenant, appareil, DeDe(c, p, e));
    }

    public static string? Abandonner(Carnet k, Campagne c, long maintenant, string appareil) => Decider(k, c, maintenant, appareil, Abandon);

    // ---- Ce que montre l'interface, en plus de l'état

    public sealed record FinObtenue(string Noeud, string Issue, string Titre, long T, Nomme? Souvenir);

    // Les fins déjà obtenues d'une campagne (les plus anciennes d'abord), avec leur souvenir.
    public static List<FinObtenue> Fins(Carnet k, Campagne c)
    {
        var l = new List<FinObtenue>();
        if (!k.Historique.TryGetValue(c.Id, out var b)) return l;
        foreach (var (code, t) in b.Fins.OrderBy(kv => kv.Key, StringComparer.Ordinal))
            if (c.Decode('n', code) is { } id && c.Noeud(id) is { Type: "fin" } n)
                l.Add(new FinObtenue(id, n.Issue, n.Titre, t * 1000, n.Recompense.Souvenir == "" ? null : c.Souvenir(n.Recompense.Souvenir)));
        return l.OrderBy(f => f.T).ThenBy(f => f.Noeud, StringComparer.Ordinal).ToList();
    }

    public static List<Nomme> Souvenirs(Carnet k, Campagne c) =>
        Fins(k, c).Where(f => f.Souvenir is not null).Select(f => f.Souvenir!).Distinct().ToList();

    // Titres et objets exclusifs gagnés (toutes fins obtenues).
    public static List<string> Titres(Carnet k, Campagne c) =>
        Fins(k, c).Select(f => c.Noeud(f.Noeud)!.Recompense.Titre).Where(t => t != "").Distinct().ToList();

    public static List<string> ObjetsGagnes(Carnet k, Campagne c) =>
        Fins(k, c).Select(f => c.Noeud(f.Noeud)!.Recompense.Objet).Where(t => t != "").Distinct().ToList();

    // Po et xp acquis dans cette campagne (selon l'historique du groupe).
    public static (int Po, int Xp) Acquis(Carnet k, Campagne c)
    {
        int po = 0, xp = 0;
        if (k.Historique.TryGetValue(c.Id, out var b))
            foreach (var code in b.Noeuds)
                if (c.Decode('n', code) is { } id && c.Noeud(id) is { } n)
                {
                    po += n.Recompense.Po;
                    xp += n.Recompense.Xp;
                }
        return (po, xp);
    }

    private static string Heure(DateTime local) => string.Create(CultureInfo.InvariantCulture, $"{local.Hour} h {local.Minute:00}");

    // « Pilou longe la falaise · retour vers 15 h 40 » (attente), « Pilou se repose · jusqu'à 15 h 40 » (repos), "" sinon.
    public static string Ligne(Etat e, DateTime finLocale) => e.Phase switch
    {
        Phase.Attente => $"{(e.Pendant == "" ? "Pilou est en route" : e.Pendant)} · retour vers {Heure(finLocale)}",
        Phase.Repos => $"Pilou se repose · jusqu'à {Heure(finLocale)}",
        _ => "",
    };

    // ---- Récompenses (PC) : chaque nœud acquis est versé une fois. Les po vont dans Bourse.PoCampagnes et l'xp dans
    // Profil.XpTelephone : deux compteurs « à part », que chaque PC du groupe tient à l'identique et qui se comptent au
    // maximum, jamais en somme (comme les gains du téléphone). L'objet exclusif d'une fin (déclaré « portable » dans la
    // fiche : Exclusifs) rejoint l'inventaire ; souvenirs et titres se lisent dans l'historique (Souvenirs, Titres).

    public sealed record Versement(int Po, int Xp, List<string> Objets);

    public static Versement Crediter(Profil p, Func<string, Campagne?> biblio)
    {
        var k = p.CarnetCampagnes;
        int po = 0, xp = 0;
        var objets = new List<string>();
        foreach (var (campagne, b) in k.Historique)
        {
            if (biblio(campagne) is not { } c) continue;
            foreach (var code in b.Noeuds)
            {
                var cle = campagne + "/" + code;
                if (k.Payes.Contains(cle) || c.Decode('n', code) is not { } id || c.Noeud(id) is not { } n) continue;
                k.Payes.Add(cle);
                po += n.Recompense.Po;
                xp += n.Recompense.Xp;
            }
            foreach (var objet in ObjetsGagnes(k, c))
                if (!p.Bourse.Inventaire.Contains(objet) && Boutique.TrouverTout(objet) is not null)
                {
                    p.Bourse.Inventaire.Add(objet);
                    objets.Add(objet);
                }
        }
        p.Bourse.PoCampagnes += po;
        p.XpTelephone += xp;
        return new Versement(po, xp, objets);
    }

    // ---- Synchronisation : un message dédié, sur un sujet à part (les anciens appareils ne l'écoutent pas)

    public static string Sujet(string code) =>
        "pilou-" + Convert.ToHexString(HMACSHA256.HashData(
            Encoding.UTF8.GetBytes(Telephone.Normaliser(code)), Encoding.UTF8.GetBytes("pilou-campagne-v1"))).ToLowerInvariant()[..24];

    private static void Chaine(StringBuilder b, string s)
    {
        b.Append('"');
        foreach (char ch in s)
        {
            if (ch == '"' || ch == '\\') b.Append('\\').Append(ch);
            else if (ch < ' ') b.Append("\\u").Append(((int)ch).ToString("x4", CultureInfo.InvariantCulture));
            else b.Append(ch);
        }
        b.Append('"');
    }

    private static void JsonInstantane(StringBuilder b, Instantane x)
    {
        b.Append('[');
        Chaine(b, x.N);
        b.Append(",{");
        bool premier = true;
        foreach (var kv in x.V.OrderBy(kv => kv.Key, StringComparer.Ordinal))
        {
            if (!premier) b.Append(',');
            premier = false;
            Chaine(b, kv.Key);
            b.Append(':').Append(kv.Value.ToString(CultureInfo.InvariantCulture));
        }
        b.Append("},");
        Chaine(b, string.Concat(x.O.OrderBy(c => c, StringComparer.Ordinal)));
        b.Append(',');
        Chaine(b, string.Concat(x.D.OrderBy(c => c, StringComparer.Ordinal)));
        b.Append(',');
        Chaine(b, x.Decor);
        b.Append(',');
        Chaine(b, x.Lieu);
        b.Append(']');
    }

    // Une partie en JSON compact. Heures en secondes ; celles des décisions, relatives à la base.
    // {"c":campagne,"p":n°,"d":départ,"o":origine,"g":graine,"x":drapeaux (1 rejeu, 2 geste, 4 entré, 8 abandonnée, 16 reprise),
    //  "e":étape,"r":rang,"i":messages,"n":tirages,"t":curseur,"ici":[…],"cp":[…]?,"u":route?,"l":[appareils],"j":[[e,dt,a,nœud,v]…]}
    public static string JsonPartie(Partie p, bool journal = true)
    {
        var ci = CultureInfo.InvariantCulture;
        var b = new StringBuilder();
        b.Append("{\"c\":");
        Chaine(b, p.Campagne);
        b.Append(",\"p\":").Append(p.P.ToString(ci)).Append(",\"d\":").Append((p.D / 1000).ToString(ci)).Append(",\"o\":");
        Chaine(b, p.O);
        b.Append(",\"g\":");
        Chaine(b, p.Graine);
        int x = (p.Rejeu ? 1 : 0) | (p.Geste ? 2 : 0) | (p.Entre ? 4 : 0) | (p.Abandonnee ? 8 : 0) | (p.Reprise ? 16 : 0);
        b.Append(",\"x\":").Append(x.ToString(ci)).Append(",\"e\":").Append(p.E.ToString(ci)).Append(",\"r\":").Append(p.R.ToString(ci))
            .Append(",\"i\":").Append(p.I.ToString(ci)).Append(",\"n\":").Append(p.Tirages.ToString(ci))
            .Append(",\"t\":").Append((p.T / 1000).ToString(ci)).Append(",\"ici\":");
        JsonInstantane(b, p.Ici);
        if (p.Cp is not null)
        {
            b.Append(",\"cp\":");
            JsonInstantane(b, p.Cp);
        }
        if (p.Chemin != "")
        {
            b.Append(",\"u\":");
            Chaine(b, p.Chemin);
        }
        if (journal && p.Journal.Count > 0)
        {
            var l = Ordonner(p.Journal);
            var appareils = l.Select(e => e.A).Distinct().OrderBy(a => a, StringComparer.Ordinal).ToList();
            b.Append(",\"l\":[");
            for (int i = 0; i < appareils.Count; i++)
            {
                if (i > 0) b.Append(',');
                Chaine(b, appareils[i]);
            }
            b.Append("],\"j\":[");
            for (int i = 0; i < l.Count; i++)
            {
                if (i > 0) b.Append(',');
                b.Append('[').Append(l[i].E.ToString(ci)).Append(',').Append(((l[i].T - p.T) / 1000).ToString(ci)).Append(',')
                    .Append(appareils.IndexOf(l[i].A).ToString(ci)).Append(',');
                Chaine(b, l[i].N);
                b.Append(',').Append(l[i].V.ToString(ci)).Append(']');
            }
            b.Append(']');
        }
        b.Append('}');
        return b.ToString();
    }

    private static void JsonBilan(StringBuilder b, Bilan x)
    {
        var ci = CultureInfo.InvariantCulture;
        b.Append('[').Append(x.P.ToString(ci)).Append(',').Append(x.Finie.ToString(ci)).Append(",{");
        bool premier = true;
        foreach (var kv in x.Fins.OrderBy(kv => kv.Key, StringComparer.Ordinal))
        {
            if (!premier) b.Append(',');
            premier = false;
            Chaine(b, kv.Key);
            b.Append(':').Append(kv.Value.ToString(ci));
        }
        b.Append("},");
        Chaine(b, string.Concat(x.Noeuds.OrderBy(c => c, StringComparer.Ordinal)));
        b.Append(']');
    }

    // {"v":1,"a":appareil,"k":"pc"|"tel","q":partie en cours?,"s":[parties suspendues],"h":{campagne:[P,Finie,{fin:t},"nœuds"]}}
    private static string JsonMessage(Carnet k, string appareil, string sorte, bool courante, IEnumerable<Partie> suspendues, bool historique)
    {
        suspendues = suspendues.OrderBy(x => x.Campagne, StringComparer.Ordinal);
        var b = new StringBuilder();
        b.Append("{\"v\":1,\"a\":");
        Chaine(b, appareil);
        b.Append(",\"k\":");
        Chaine(b, sorte);
        if (courante && k.Courante is not null) b.Append(",\"q\":").Append(JsonPartie(k.Courante));
        var s = suspendues.ToList();
        if (s.Count > 0)
        {
            b.Append(",\"s\":[");
            for (int i = 0; i < s.Count; i++)
            {
                if (i > 0) b.Append(',');
                b.Append(JsonPartie(s[i]));
            }
            b.Append(']');
        }
        if (historique)
        {
            b.Append(",\"h\":{");
            bool premier = true;
            foreach (var kv in k.Historique.OrderBy(kv => kv.Key, StringComparer.Ordinal))
            {
                if (!premier) b.Append(',');
                premier = false;
                Chaine(b, kv.Key);
                b.Append(':');
                JsonBilan(b, kv.Value);
            }
            b.Append('}');
        }
        b.Append('}');
        return b.ToString();
    }

    public static int Octets(string json) => Encoding.UTF8.GetByteCount(json);

    // Ce que l'appareil publie : un message s'il tient sous TailleJson, sinon la partie en cours et l'historique
    // d'abord, puis les parties suspendues (une par message au besoin). Vide si le carnet n'a rien à dire.
    public static List<string> Messages(Carnet k, string appareil, string sorte)
    {
        var l = new List<string>();
        if (k.Courante is null && k.Suspendues.Count == 0 && k.Historique.Count == 0) return l;
        var tout = JsonMessage(k, appareil, sorte, true, k.Suspendues.Values, true);
        if (Octets(tout) <= TailleJson || k.Suspendues.Count == 0)
        {
            l.Add(tout);
            return l;
        }
        l.Add(JsonMessage(k, appareil, sorte, true, Array.Empty<Partie>(), true));
        var lot = new List<Partie>();
        foreach (var s in k.Suspendues.Values)
        {
            lot.Add(s);
            if (Octets(JsonMessage(k, appareil, sorte, false, lot, false)) <= TailleJson || lot.Count == 1) continue;
            lot.RemoveAt(lot.Count - 1);
            l.Add(JsonMessage(k, appareil, sorte, false, lot, false));
            lot = new List<Partie> { s };
        }
        if (lot.Count > 0) l.Add(JsonMessage(k, appareil, sorte, false, lot, false));
        return l;
    }

    // Signature de ce qui est synchronisé (pour ne publier que sur changement).
    public static string Signature(Carnet k) => JsonMessage(k, "", "", true, k.Suspendues.Values, true);

    private static bool CodeValide(string s) => s.Length == 4 && s.All(ch => Alphabet64.Contains(ch));

    private static List<string> Codes(string s)
    {
        var l = new List<string>();
        if (s.Length % 4 != 0 || s.Length > 4 * 400) return l;
        for (int i = 0; i < s.Length; i += 4)
            if (CodeValide(s.Substring(i, 4)) && !l.Contains(s.Substring(i, 4))) l.Add(s.Substring(i, 4));
        l.Sort(StringComparer.Ordinal);
        return l;
    }

    private static bool IdValide(string s) => s.Length is > 0 and <= 40 && s.All(ch => ch is (>= 'a' and <= 'z') or (>= '0' and <= '9') or '-');

    private static long Long(JsonElement o, string cle) =>
        o.ValueKind == JsonValueKind.Object && o.TryGetProperty(cle, out var v) && v.ValueKind == JsonValueKind.Number && v.TryGetInt64(out var n) ? n : 0;

    private static Instantane? LireInstantane(JsonElement o, string cle)
    {
        if (!o.TryGetProperty(cle, out var a) || a.ValueKind != JsonValueKind.Array || a.GetArrayLength() != 6) return null;
        string Texte(int i) => a[i].ValueKind == JsonValueKind.String ? a[i].GetString() ?? "" : "";
        var x = new Instantane { N = Texte(0), O = Codes(Texte(2)), D = Codes(Texte(3)), Decor = Texte(4), Lieu = Texte(5) };
        if (!CodeValide(x.N) || (x.Decor != "" && !CodeValide(x.Decor)) || (x.Lieu != "" && !CodeValide(x.Lieu))) return null;
        if (a[1].ValueKind == JsonValueKind.Object)
            foreach (var kv in a[1].EnumerateObject())
                if (CodeValide(kv.Name) && kv.Value.ValueKind == JsonValueKind.Number && kv.Value.TryGetInt32(out var n) && x.V.Count < 200)
                    x.V[kv.Name] = n;
        return x;
    }

    // Une partie lue d'un message ; null si elle est mal formée (on ne garde rien d'à moitié lu).
    public static Partie? LirePartie(JsonElement o)
    {
        if (o.ValueKind != JsonValueKind.Object) return null;
        int x = N(o, "x");
        var p = new Partie
        {
            Campagne = S(o, "c"), P = N(o, "p"), D = Long(o, "d") * 1000, O = S(o, "o"), Graine = S(o, "g"),
            Rejeu = (x & 1) != 0, Geste = (x & 2) != 0, Entre = (x & 4) != 0, Abandonnee = (x & 8) != 0, Reprise = (x & 16) != 0,
            E = N(o, "e"), R = N(o, "r"), I = N(o, "i"), Tirages = N(o, "n"), T = Long(o, "t") * 1000,
        };
        if (!IdValide(p.Campagne) || p.P < 1 || p.E < 0 || p.R < 0 || p.I < 0 || p.Tirages < 0 || p.O.Length is 0 or > 64 || p.Graine.Length is 0 or > 32
            || p.D <= 0 || p.T <= 0)
            return null;
        if (LireInstantane(o, "ici") is not { } ici) return null;
        p.Ici = ici;
        p.Cp = LireInstantane(o, "cp");
        var chemin = S(o, "u");
        p.Chemin = CheminValide(chemin, p.E) ? chemin : "";
        var appareils = L(o, "l").Select(a => a.ValueKind == JsonValueKind.String ? a.GetString() ?? "" : "").ToList();
        foreach (var j in L(o, "j"))
        {
            if (p.Journal.Count >= 400) break;
            if (j.ValueKind != JsonValueKind.Array || j.GetArrayLength() != 5) continue;
            if (j[0].ValueKind != JsonValueKind.Number || j[1].ValueKind != JsonValueKind.Number || j[2].ValueKind != JsonValueKind.Number
                || j[4].ValueKind != JsonValueKind.Number) continue;
            if (!j[0].TryGetInt32(out var e) || !j[1].TryGetInt64(out var dt) || !j[2].TryGetInt32(out var a) || !j[4].TryGetInt32(out var v)) continue;
            var n = j[3].ValueKind == JsonValueKind.String ? j[3].GetString() ?? "" : "";
            if (a < 0 || a >= appareils.Count || appareils[a].Length is 0 or > 64 || !CodeValide(n) || v < Abandon || v > 16 || e < p.E) continue;
            p.Journal.Add(new Entree(e, p.T + dt * 1000, appareils[a], n, v));
        }
        p.Journal = Borner(p.Journal, p.E);
        return p;
    }

    public static Partie? LirePartie(string json)
    {
        try
        {
            using var doc = JsonDocument.Parse(json);
            return LirePartie(doc.RootElement);
        }
        catch (Exception e) when (e is JsonException or InvalidOperationException)
        {
            return null;
        }
    }

    private static bool FusionBilan(Bilan b, JsonElement a)
    {
        if (a.ValueKind != JsonValueKind.Array || a.GetArrayLength() != 4) return false;
        bool change = false;
        if (a[0].ValueKind == JsonValueKind.Number && a[0].TryGetInt32(out var p) && p > b.P)
        {
            b.P = p;
            change = true;
        }
        if (a[1].ValueKind == JsonValueKind.Number && a[1].TryGetInt32(out var f) && f > b.Finie)
        {
            b.Finie = f;
            change = true;
        }
        if (a[2].ValueKind == JsonValueKind.Object)
            foreach (var kv in a[2].EnumerateObject())
                if (CodeValide(kv.Name) && kv.Value.ValueKind == JsonValueKind.Number && kv.Value.TryGetInt64(out var t) && t > 0
                    && (b.Fins.TryGetValue(kv.Name, out var avant) ? t < avant : b.Fins.Count < 40))
                {
                    b.Fins[kv.Name] = t;
                    change = true;
                }
        if (a[3].ValueKind == JsonValueKind.String)
            foreach (var code in Codes(a[3].GetString() ?? ""))
                if (!b.Noeuds.Contains(code))
                {
                    b.Noeuds.Add(code);
                    change = true;
                }
        b.Noeuds.Sort(StringComparer.Ordinal);
        return change;
    }

    // La base reçue (plus avancée que la mienne) contredit-elle mon histoire ? Les deux routes connues : l'une doit
    // prolonger l'autre (mon rejeu peut être en retard ou en avance sur la base reçue). Une route inconnue (appareil plus
    // ancien) : si mon rejeu passe par la même étape, il doit y être au même point (même rang, même nœud, même état) ;
    // s'il n'y est pas encore, rien à comparer.
    private static bool Diverge(Campagne c, Partie mienne, Partie recue, long maintenant)
    {
        var e = Rejouer(c, mienne, maintenant);
        if (CheminValide(e.Chemin, e.E) && CheminValide(recue.Chemin, recue.E))
            return !recue.Chemin.StartsWith(e.Chemin, StringComparison.Ordinal) && !e.Chemin.StartsWith(recue.Chemin, StringComparison.Ordinal);
        var points = e.Points.Where(pt => pt.Base.E == recue.E && !pt.Base.Abandonnee).ToList();
        if (points.Count == 0) return false;
        string Ici(Partie p)
        {
            var b = new StringBuilder();
            JsonInstantane(b, p.Ici);
            return p.R.ToString(CultureInfo.InvariantCulture) + b;
        }
        var attendu = Ici(recue);
        return points.All(pt => Ici(pt.Base) != attendu);
    }

    // Fusion d'un message reçu (d'un autre appareil du groupe) : idempotente, insensible à l'ordre et aux doublons.
    // Renvoie true si le carnet a changé. Appeler ensuite Actualiser (et Crediter sur un PC).
    public static bool Recevoir(Carnet k, string json, string moi, Func<string, Campagne?> biblio, long maintenant)
    {
        try
        {
            using var doc = JsonDocument.Parse(json);
            var r = doc.RootElement;
            if (r.ValueKind != JsonValueKind.Object || N(r, "v") != 1) return false;
            var appareil = S(r, "a");
            if (appareil == "" || appareil == moi) return false;
            var avant = Signature(k) + "|" + string.Join(",", k.PayesPc);
            if (r.TryGetProperty("h", out var h) && h.ValueKind == JsonValueKind.Object)
                foreach (var kv in h.EnumerateObject())
                {
                    if (!IdValide(kv.Name) || (k.Historique.Count >= 40 && !k.Historique.ContainsKey(kv.Name))) continue;
                    FusionBilan(BilanDe(k, kv.Name), kv.Value);
                    // Ce qu'un PC annonce comme acquis, il l'a versé (ou le versera) : le téléphone n'attend plus.
                    if (S(r, "k") == "pc" && kv.Value.ValueKind == JsonValueKind.Array && kv.Value.GetArrayLength() == 4
                        && kv.Value[3].ValueKind == JsonValueKind.String)
                        foreach (var code in Codes(kv.Value[3].GetString() ?? ""))
                            if (!k.PayesPc.Contains(kv.Name + "/" + code)) k.PayesPc.Add(kv.Name + "/" + code);
                }
            foreach (var x in L(r, "s"))
                if (LirePartie(x) is { } s)
                    k.Suspendues[s.Campagne] = Meilleure(k.Suspendues.GetValueOrDefault(s.Campagne), s)!;
            if (r.TryGetProperty("q", out var q) && LirePartie(q) is { } recue)
            {
                if (k.Courante is not { } mienne) k.Courante = recue;
                else
                {
                    int c = CompareIdentite(mienne, recue);
                    if (c == 0)
                    {
                        // Les deux appareils ont avancé chacun de son côté au-delà du délai de grâce, et la base reçue,
                        // plus avancée, n'est pas sur ma route : ce que mon fil raconte de cette partie n'a pas eu lieu
                        // (on ne sait pas où les routes se sont séparées). Le fil repart de la base reçue.
                        if (Avance(recue, mienne) && biblio(mienne.Campagne) is { } cm && Diverge(cm, mienne, recue, maintenant))
                            k.Fil.RemoveAll(m => m.P == mienne.P);
                        k.Courante = Unir(mienne, recue);
                    }
                    else
                    {
                        var (gagne, perd) = c < 0 ? (mienne, recue) : (recue, mienne);
                        k.Courante = gagne.Copie();
                        if (perd.Campagne != gagne.Campagne) Ranger(k, perd, biblio, maintenant);
                    }
                }
            }
            Nettoyer(k);
            return Signature(k) + "|" + string.Join(",", k.PayesPc) != avant;
        }
        catch (Exception e) when (e is JsonException or InvalidOperationException)
        {
            return false;
        }
    }

    // Récompenses acquises que nul PC n'a encore versées (vu du téléphone) : elles attendent le PC.
    public static (int Po, int Xp) EnAttente(Carnet k, Func<string, Campagne?> biblio)
    {
        int po = 0, xp = 0;
        foreach (var (campagne, b) in k.Historique)
        {
            if (biblio(campagne) is not { } c) continue;
            foreach (var code in b.Noeuds)
                if (!k.PayesPc.Contains(campagne + "/" + code) && c.Decode('n', code) is { } id && c.Noeud(id) is { } n)
                {
                    po += n.Recompense.Po;
                    xp += n.Recompense.Xp;
                }
        }
        return (po, xp);
    }

    // Réponse de ntfy (une ligne JSON par événement) → messages déchiffrés, et identifiant du dernier message vu.
    public static (List<string> Messages, string Dernier) LireRelais(string code, string texte)
    {
        var l = new List<string>();
        string dernier = "";
        foreach (var ligne in texte.Split('\n', StringSplitOptions.RemoveEmptyEntries))
        {
            try
            {
                using var doc = JsonDocument.Parse(ligne);
                var r = doc.RootElement;
                if (r.TryGetProperty("event", out var ev) && ev.GetString() != "message") continue;
                if (r.TryGetProperty("id", out var id) && id.ValueKind == JsonValueKind.String) dernier = id.GetString() ?? dernier;
                if (!r.TryGetProperty("message", out var m) || m.ValueKind != JsonValueKind.String) continue;
                l.Add(Telephone.Dechiffrer(code, m.GetString() ?? ""));
            }
            catch (Exception e) when (e is JsonException or FormatException or CryptographicException or ArgumentException or InvalidOperationException)
            {
                // illisible ou d'un autre groupe : ignoré
            }
        }
        return (l, dernier);
    }
}
