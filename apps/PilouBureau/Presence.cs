using System.Globalization;
using System.IO;
using System.Text;

namespace PilouBureau;

// La présence de Pilou au quotidien (docs/PRESENCE.md) : petits mots rares et justes, complicité qui grandit sans jamais
// baisser, dates fêtées une fois, journal écrit de son point de vue, prénom (facultatif). Ce fichier est le MOTEUR, sans
// WPF ni réseau ; android/.../Presence.java en est la copie exacte (mêmes tirages, mêmes textes) : les vecteurs partagés
// android/app/src/test/resources/presence-vecteurs.txt, écrits d'ici (PresenceVecteurs), sont relus par les tests Java.
//
//   Banque      assets/presence/mots.txt (petits mots) et journal.txt (gabarits du journal) : « famille|filtres|texte »
//   Choix       Presence.Mot(contexte, banque, dits, graine) : famille selon le moment, puis une ligne jamais dite (ou
//               dite il y a le plus longtemps) ; graine = date + appareil : reproductible
//   Cadence      Cadences.Observer / Pret / Noter (PC : au plus 3 par jour, moments calmes) ; Presence.MinuteDuSoir et
//               Presence.JourDeMot (téléphone : au plus un mot par jour, le soir)
//   Complicité  Presence.Totaux(moi, autres) : compteurs qui ne font que monter, jours ensemble en union
//   Journal     FaitsDuJour (un jour, un appareil), FaitsDuJour.Fusion (max et union : ordre et doublons sans effet), Presence.Ecrire
//   Synchro     Appareil.Texte() : message dédié (sujet Presence.Sujet(code)), Appareil.Lire, EtatPresence.Recevoir
public static class Presence
{
    public const int Version = 1;
    public const int LongueurMax = 90;
    public const int PrenomMax = 16;
    // Taille d'un message de synchronisation, au plus (chiffré : sous Telephone.TailleMax, comme Groupe.TailleJson).
    public const int TailleMessage = 2750;
    public const int JoursDansMessage = 7, JoursOuverts = 14, JoursGardes = 400, DitsGardes = 900;
    private static readonly CultureInfo Ci = CultureInfo.InvariantCulture;

    // ---- Hachage (FNV-1a 64 sur les caractères UTF-16, comme Presence.java)

    public static ulong Hash(string s)
    {
        ulong h = 14695981039346656037UL;
        foreach (char c in s)
        {
            h ^= c;
            h *= 1099511628211UL;
        }
        return h;
    }

    public static int Tirer(string graine, int n) => n <= 0 ? 0 : (int)(Hash(graine) % (ulong)n);

    public static string Id(string famille, string texte) => (Hash(famille + "|" + texte) & 0xffffffffUL).ToString("x8", Ci);

    // ---- Banque de textes

    public sealed record Ligne(string Famille, int Palier, string Stades, string Variante, string Texte, string Id, IReadOnlyList<string> Trous);

    public static List<Ligne> Lire(string texte)
    {
        var l = new List<Ligne>();
        foreach (var brut in texte.Replace("\r\n", "\n").Split('\n'))
        {
            var ligne = Rogner(brut);
            if (ligne.Length == 0 || ligne[0] == '#') continue;
            var p = ligne.Split('|');
            if (p.Length != 3) continue;
            var famille = Rogner(p[0]);
            var t = Rogner(p[2]);
            if (famille.Length == 0 || t.Length == 0) continue;
            int palier = 0;
            string stades = "", variante = "";
            foreach (var f0 in p[1].Split(','))
            {
                var f = Rogner(f0);
                if (f.Length == 0) continue;
                if (f == "calin" || f == "espiegle") variante = f;
                else if (f[0] == 'c' && f.Length == 2 && f[1] >= '0' && f[1] <= '9') palier = f[1] - '0';
                else if (f[0] == 's' && f.Length > 1) stades = f[1..];
            }
            l.Add(new Ligne(famille, palier, stades, variante, t, Id(famille, t), Trous(t)));
        }
        return l;
    }

    public static List<string> Trous(string t)
    {
        var l = new List<string>();
        int i = 0;
        while ((i = t.IndexOf('{', i)) >= 0)
        {
            int j = t.IndexOf('}', i);
            if (j < 0) break;
            var nom = t.Substring(i + 1, j - i - 1);
            if (!l.Contains(nom)) l.Add(nom);
            i = j + 1;
        }
        return l;
    }

    private static List<Ligne>? _mots, _gabarits;

    public static IReadOnlyList<Ligne> Mots => _mots ??= Lire(Ressource("mots.txt"));
    public static IReadOnlyList<Ligne> Gabarits => _gabarits ??= Lire(Ressource("journal.txt"));

    // Les mots des traits de personnalité (assets/presence/traits.txt : annonce-<trait>, trait-<trait>), et la banque
    // entière où Presence.Mot puise : les petits mots de toujours, puis ceux des traits.
    private static List<Ligne>? _repliques, _banque;

    public static IReadOnlyList<Ligne> Repliques => _repliques ??= Lire(Ressource("traits.txt"));
    public static IReadOnlyList<Ligne> Banque => _banque ??= Mots.Concat(Repliques).ToList();

    private static string Ressource(string nom)
    {
        try
        {
            using var flux = typeof(Presence).Assembly.GetManifestResourceStream("presence:" + nom);
            if (flux is null) return "";
            using var r = new StreamReader(flux, Encoding.UTF8);
            return r.ReadToEnd();
        }
        catch (IOException)
        {
            return "";
        }
    }

    public static string Remplir(string texte, IReadOnlyDictionary<string, string> valeurs)
    {
        var b = new StringBuilder(texte);
        foreach (var t in Trous(texte))
            if (valeurs.TryGetValue(t, out var v)) b.Replace("{" + t + "}", v);
        return b.ToString();
    }

    // ---- Choix d'une ligne : jamais deux fois la même avant que toutes les autres de sa famille soient passées

    public sealed record Qui(int Palier, int Stade, string Variante);

    public static Ligne? Choisir(IEnumerable<Ligne> banque, string famille, Qui qui, IReadOnlyDictionary<string, string> valeurs,
        IReadOnlyDictionary<string, int> dits, string graine)
    {
        var c = banque.Where(l => l.Famille == famille && l.Palier <= qui.Palier
                                  && (l.Stades.Length == 0 || l.Stades.IndexOf((char)('0' + qui.Stade)) >= 0)
                                  && (l.Variante.Length == 0 || l.Variante == qui.Variante)
                                  && l.Trous.All(t => valeurs.TryGetValue(t, out var v) && v.Length > 0))
            .OrderBy(l => l.Id, StringComparer.Ordinal).ToList();
        if (c.Count == 0) return null;
        var neufs = c.Where(l => !dits.ContainsKey(l.Id)).ToList();
        var pool = neufs.Count > 0
            ? neufs
            : c.OrderBy(l => dits[l.Id]).ThenBy(l => l.Id, StringComparer.Ordinal).Take((c.Count + 2) / 3)
                .OrderBy(l => l.Id, StringComparer.Ordinal).ToList();
        return pool[Tirer(graine, pool.Count)];
    }

    // Garde la mémoire des lignes dites sous DitsGardes entrées (les plus anciennes partent).
    public static void Retenir(Dictionary<string, int> dits, string id, int jour)
    {
        dits[id] = jour;
        while (dits.Count > DitsGardes)
        {
            var plusVieux = dits.OrderBy(kv => kv.Value).ThenBy(kv => kv.Key, StringComparer.Ordinal).First().Key;
            dits.Remove(plusVieux);
        }
    }

    // ---- Calendrier

    public static int Jour(DateTime local) => DateOnly.FromDateTime(local).DayNumber - 719162;
    public static string JourTexte(DateTime local) => local.ToString("yyyy-MM-dd", Ci);
    public static string JourTexte(int jour) => DateOnly.FromDayNumber(jour + 719162).ToString("yyyy-MM-dd", Ci);
    public static int JourDe(string texte) =>
        DateOnly.TryParseExact(texte, "yyyy-MM-dd", Ci, DateTimeStyles.None, out var d) ? d.DayNumber - 719162 : int.MinValue;
    private static DateOnly Date(int jour) => DateOnly.FromDayNumber(jour + 719162);

    // Tôt le matin : de 5 h à 7 h 30 (avant, c'est encore la nuit de la veille).
    public static bool TotLeMatin(int heure, int minute) => heure * 60 + minute is >= 300 and < 450;

    public static string Saison(int mois) => mois switch
    {
        12 or 1 or 2 => "hiver", 3 or 4 or 5 => "printemps", 6 or 7 or 8 => "ete", _ => "automne",
    };

    // Fêtes génériques (aucune n'est religieuse ni commerciale au-delà du calendrier commun).
    public static string Fete(int mois, int jour) => (mois, jour) switch
    {
        (1, 1) => "nouvel-an",
        (2, 2) => "chandeleur",
        (3, 20) => "printemps",
        (4, 1) => "poisson",
        (6, 21) => "musique",
        (9, 1) => "rentree",
        (9, 22) => "automne",
        (10, 31) => "citrouille",
        (12, 21) => "hiver",
        (12, 24) or (12, 25) => "noel",
        (12, 31) => "reveillon",
        _ => "",
    };

    public static readonly string[] MeteosNotables = { "pluie", "orage", "neige", "brouillard", "vent", "chaleur", "froid", "degage" };

    public static string MeteoFamille(string etat) => etat == "averse" ? "pluie" : Array.IndexOf(MeteosNotables, etat) >= 0 ? etat : "";

    public static readonly string[] Curiosites = { "code", "tableur", "texte", "mail", "musique", "video", "lecture", "dessin", "jeu" };

    public static string CuriositeDe(string activite) => activite == "jeu-mmo" ? "jeu" : Array.IndexOf(Curiosites, activite) >= 0 ? activite : "";

    // ---- Moments et familles

    public enum Moment { Premier, Retour, Soir, Telephone }

    // Ce que l'appareil sait quand il va parler. Tout est local, rien de personnel (pas de titre ni de fichier).
    public sealed record Contexte(
        DateTime Local, Moment Moment, double AbsenceMin, double PresenceJourMin, double SeanceMin,
        string Activite, string Meteo, int Palier, int Stade, string Variante, string Prenom,
        string Metier = "", int Niveau = 0, string Objet = "", string Prise = "", string Plat = "", string Souvenir = "",
        string DateAFeter = "", int PalierNouveau = -1, bool DemanderPrenom = false, int JoursEnsemble = 0, int Annees = 0,
        // Traits de personnalité (Traits.cs) : celui à annoncer (une fois), et les dominants déjà annoncés (« a,b,c »).
        string TraitNouveau = "", string Traits = "");

    public sealed record Choix(string Famille, Ligne Ligne, string Texte);

    // Les familles à essayer, dans l'ordre (la première qui a une ligne possible l'emporte).
    public static List<string> Plan(Contexte c, string graine)
    {
        var l = new List<string>();
        var d = c.Local;
        int dow = (int)d.DayOfWeek; // 0 dimanche … 6 samedi
        string saison = "saison-" + Saison(d.Month), fete = Fete(d.Month, d.Day), meteo = MeteoFamille(c.Meteo);
        void Annonces()
        {
            if (c.DateAFeter != "") l.Add("date-" + (c.DateAFeter[0] == 'a' ? "a" : c.DateAFeter));
            if (c.PalierNouveau > 0) l.Add("palier-" + c.PalierNouveau.ToString(Ci));
            if (c.TraitNouveau != "") l.Add("annonce-" + c.TraitNouveau);
        }
        var rot = new List<(string F, int Poids)>();
        void Souvenirs(int poids)
        {
            if (c.Souvenir != "") rot.Add(("souvenir-" + c.Souvenir, poids));
            if (c.Prise != "") rot.Add(("souvenir-prise", poids));
            if (c.Plat != "") rot.Add(("souvenir-plat", poids));
        }
        switch (c.Moment)
        {
            case Moment.Premier:
                Annonces();
                if (c.AbsenceMin >= 21 * 1440) l.Add("retour-long");
                if (c.AbsenceMin >= 5 * 1440) l.Add("retour-semaine");
                else if (c.AbsenceMin >= 40 * 60) l.Add(dow == 1 ? "retour-weekend" : "retour-jours");
                if (fete != "") l.Add("fete-" + fete);
                if (dow == 1 && d.Hour < 14) l.Add("lundi");
                if (dow is 0 or 6) l.Add("weekend");
                rot.Add(("bonjour", 4));
                if (c.AbsenceMin >= 360) rot.Add(("retour-nuit", 2));
                rot.Add((saison, 1));
                if (meteo != "") rot.Add(("meteo-" + meteo, 1));
                Souvenirs(1);
                rot.Add(("pensee", 1));
                break;
            case Moment.Retour:
                if (c.DemanderPrenom) l.Add("prenom-demande");
                rot.Add(("retour-1h", 4));
                if (CuriositeDe(c.Activite) is { Length: > 0 } cu) rot.Add(("curiosite-" + cu, 2));
                rot.Add(("pensee", 3));
                if (c.Metier != "") rot.Add(("metier", 2));
                if (c.Niveau > 0) rot.Add(("niveau", 2));
                if (c.Objet != "") rot.Add(("objet", 1));
                Souvenirs(1);
                if (meteo != "") rot.Add(("meteo-" + meteo, 1));
                break;
            case Moment.Soir:
                if (dow == 5) l.Add("vendredi");
                if (d.Hour >= 22 || d.Hour < 5) l.Add("tard");
                if (c.SeanceMin >= 150 || c.PresenceJourMin >= 360) l.Add("fin-seance");
                rot.Add(("soir", 4));
                rot.Add(("pensee", 2));
                Souvenirs(1);
                rot.Add((saison, 1));
                break;
            default:
                Annonces();
                if (fete != "") l.Add("fete-" + fete);
                rot.Add(("tel-soir", 4));
                rot.Add(("pensee", 3));
                Souvenirs(1);
                rot.Add((saison, 1));
                if (meteo != "") rot.Add(("meteo-" + meteo, 1));
                if (c.Objet != "") rot.Add(("objet", 1));
                if (c.Metier != "") rot.Add(("metier", 1));
                break;
        }
        // Les traits dominants colorent ce qu'il dit : une famille de répliques chacun, au poids d'une pensée rare.
        foreach (var id in c.Traits.Split(','))
            if (id != "") rot.Add(("trait-" + id, 1));
        // Tirage pondéré de la première famille de la rotation ; les autres suivent dans l'ordre (repli).
        int total = rot.Sum(r => r.Poids), v = Tirer(graine + "|famille", total);
        int premier = 0;
        for (int i = 0, acc = 0; i < rot.Count; i++)
        {
            acc += rot[i].Poids;
            if (v < acc)
            {
                premier = i;
                break;
            }
        }
        if (rot.Count > 0) l.Add(rot[premier].F);
        for (int i = 0; i < rot.Count; i++)
            if (i != premier) l.Add(rot[i].F);
        l.Add(c.Moment switch { Moment.Premier => "bonjour", Moment.Retour => "retour-1h", Moment.Soir => "soir", _ => "tel-soir" });
        l.Add("pensee");
        return l.Distinct().ToList();
    }

    // Première lettre seulement (« Truite argentée » → « truite argentée » ; un nom propre reste tel quel s'il est
    // dans le texte du gabarit, pas dans la valeur).
    private static string Minuscule(string s) => s.Length == 0 ? s : char.ToLowerInvariant(s[0]) + s[1..];
    private static string Majuscule(string s) => s.Length == 0 ? s : char.ToUpperInvariant(s[0]) + s[1..];

    public static readonly string[] Paliers = { "Connaissance", "Copain", "Ami", "Meilleur ami", "Inséparables" };
    public static readonly int[] Seuils = { 0, 150, 700, 2500, 7000 };

    public static string NomPalier(int p) => Paliers[Math.Clamp(p, 0, Paliers.Length - 1)];

    // Le mot à dire (null : rien qui convienne). Le prénom n'entre qu'avec parcimonie : une fois sur cinq au plus
    // (une sur trois chez les Inséparables), toujours dans les familles « prenom-… ».
    public static Choix? Mot(Contexte c, IReadOnlyList<Ligne> banque, IReadOnlyDictionary<string, int> dits, string graine)
    {
        var qui = new Qui(c.Palier, Math.Clamp(c.Stade, 1, 4), c.Variante);
        var valeurs = new Dictionary<string, string>();
        void Mettre(string k, string v)
        {
            if (v != "") valeurs[k] = v;
        }
        Mettre("metier", Minuscule(c.Metier));
        if (c.Niveau > 0) valeurs["niveau"] = c.Niveau.ToString(Ci);
        Mettre("objet", Minuscule(c.Objet));
        Mettre("prise", Minuscule(c.Prise));
        Mettre("plat", Minuscule(c.Plat));
        Mettre("palier", Minuscule(NomPalier(c.Palier)));
        if (c.JoursEnsemble > 0) valeurs["jours"] = c.JoursEnsemble.ToString(Ci);
        if (c.Annees > 0) valeurs["annees"] = c.Annees == 1 ? "un an" : c.Annees.ToString(Ci) + " ans";
        bool prenom = c.Prenom != "" && Tirer(graine + "|prenom", c.Palier >= 4 ? 3 : 5) == 0;
        foreach (var f in Plan(c, graine))
        {
            var v = new Dictionary<string, string>(valeurs);
            if (c.Prenom != "" && (prenom || f.StartsWith("prenom-", StringComparison.Ordinal))) v["prenom"] = c.Prenom;
            var ligne = Choisir(banque, f, qui, v, dits, graine + "|" + f);
            if (ligne is not null) return new Choix(f, ligne, Remplir(ligne.Texte, v));
        }
        return null;
    }

    // ---- Téléphone : le mot du soir (au plus un par jour, jamais la nuit)

    // Minute du jour où le téléphone le propose : entre 19 h et 20 h 30, tirée de la date et de l'appareil.
    public static int MinuteDuSoir(string jour, string appareil) => 19 * 60 + Tirer(jour + "|" + appareil + "|soir", 91);

    // Ce jour-là, un mot ? « chaque » jour, « parfois » (mardi, samedi, et le jeudi une semaine sur deux : 2 à 3 par
    // semaine), « jamais ». Le réglage global « Pilou me parle » l'emporte : « peu » ramène à « parfois », « jamais » à rien.
    public static bool JourDeMot(DateTime local, string frequence, string parle)
    {
        if (parle == "jamais" || frequence == "jamais") return false;
        var f = parle == "peu" ? "parfois" : frequence;
        if (f != "parfois") return true;
        var dow = local.DayOfWeek;
        return dow is DayOfWeek.Tuesday or DayOfWeek.Saturday || (dow == DayOfWeek.Thursday && ISOWeek.GetWeekOfYear(local) % 2 == 1);
    }

    // ---- Complicité : une jauge qui monte lentement et ne baisse jamais

    // Par jour et par appareil, au plus : 180 min ensemble, 10 caresses, 6 soins, 6 jeux (le reste ne compte pas, sans punir).
    public const int MaxMinutes = 180, MaxCaresses = 10, MaxSoins = 6, MaxJeux = 6;

    public sealed record Totaux(int Points, int Palier, int Jours, int Adoption, IReadOnlyCollection<string> Fetes, int PalierAnnonce,
        string Prenom, long PrenomT, bool PrenomDemande, int Finies, long Traits = 0, long TraitsDits = 0);

    public static int PalierDe(int points)
    {
        int p = 0;
        for (int i = 0; i < Seuils.Length; i++)
            if (points >= Seuils[i]) p = i;
        return p;
    }

    public static Totaux Calculer(Appareil moi, IEnumerable<Appareil> autres)
    {
        var tous = new List<Appareil> { moi };
        tous.AddRange(autres.Where(a => a.Id != moi.Id));
        var jours = new SortedSet<int>();
        var finies = new SortedSet<string>(StringComparer.Ordinal);
        var fetes = new SortedSet<string>(StringComparer.Ordinal);
        long points = 0;
        int annonce = 0, adoption = int.MaxValue;
        string prenom = "";
        long prenomT = -1;
        bool demande = false;
        long traits = 0, traitsDits = 0;
        foreach (var a in tous)
        {
            traits |= a.Traits;
            traitsDits |= a.TraitsDits;
            points += a.Minutes / 10 + a.Caresses + 2L * a.Soins + 2L * a.Jeux;
            jours.UnionWith(a.Jours);
            finies.UnionWith(a.Finies);
            fetes.UnionWith(a.Fetes);
            annonce = Math.Max(annonce, a.PalierAnnonce);
            if (a.Jours.Count > 0) adoption = Math.Min(adoption, a.Jours.Min);
            if (a.PrenomT > prenomT || (a.PrenomT == prenomT && string.CompareOrdinal(a.Prenom, prenom) < 0))
            {
                prenomT = a.PrenomT;
                prenom = a.Prenom;
            }
            demande |= a.PrenomDemande;
        }
        int suites = jours.Count(j => jours.Contains(j - 1));
        points += 10L * jours.Count + 5L * suites + 60L * finies.Count;
        int pts = (int)Math.Min(int.MaxValue, points);
        return new Totaux(pts, PalierDe(pts), jours.Count, adoption == int.MaxValue ? -1 : adoption, fetes, annonce,
            prenomT < 0 ? "" : prenom, Math.Max(0, prenomT), demande, finies.Count, traits, traitsDits);
    }

    // La date à fêter aujourd'hui (une seule, sobrement), ou "" : anniversaire de l'adoption, un mois, six mois, puis
    // 7, 100, 200, 500 et 1 000 jours ensemble. Une date fêtée ne revient jamais ; une date passée depuis plus d'une
    // semaine n'est plus fêtée (on ne célèbre pas en retard).
    public static readonly int[] PaliersJours = { 7, 100, 200, 500, 1000 };

    public static string DateAFeter(Totaux t, int aujourdhui)
    {
        if (t.Adoption < 0 || aujourdhui < t.Adoption) return "";
        var debut = Date(t.Adoption);
        var auj = Date(aujourdhui);
        for (int n = 1; n <= 50; n++)
        {
            var anniv = debut.AddYears(n);
            if (anniv > auj) break;
            int ecart = auj.DayNumber - anniv.DayNumber;
            if (ecart < 7 && !t.Fetes.Contains("a" + n.ToString(Ci))) return "a" + n.ToString(Ci);
        }
        foreach (var m in new[] { 1, 6 })
        {
            int ecart = auj.DayNumber - debut.AddMonths(m).DayNumber;
            if (ecart is >= 0 and < 7 && !t.Fetes.Contains("m" + m.ToString(Ci))) return "m" + m.ToString(Ci);
        }
        foreach (var n in PaliersJours)
            if (t.Jours >= n && t.Jours < n + 7 && !t.Fetes.Contains("j" + n.ToString(Ci))) return "j" + n.ToString(Ci);
        return "";
    }

    public static string NettoyerPrenom(string? s)
    {
        if (s is null) return "";
        var b = new StringBuilder();
        foreach (char c0 in s)
        {
            char ch = char.IsControl(c0) ? ' ' : c0;
            if (ch is '|' or '{' or '}' or ';' or '=' or ',' || char.IsSurrogate(ch)) continue;
            if (ch == ' ' && (b.Length == 0 || b[^1] == ' ')) continue;
            b.Append(ch);
        }
        var r = Rogner(b.ToString());
        return r.Length > PrenomMax ? Rogner(r[..PrenomMax]) : r;
    }

    // Retire les espaces simples au début et à la fin (seulement eux : même résultat qu'en Java).
    public static string Rogner(string s)
    {
        int a = 0, b = s.Length;
        while (a < b && s[a] == ' ') a++;
        while (b > a && s[b - 1] == ' ') b--;
        return s[a..b];
    }

    // Prises et plats avec leur article (« une truite argentée », « des croquettes croustillantes »), pour le journal.
    private static readonly HashSet<string> Feminins = new(StringComparer.Ordinal)
    {
        "ablette", "algue", "botte", "perche", "ecrevisse", "bouteille", "truite", "anguille", "cle", "pieuvre", "raie", "perle", "carpe",
        "tartine", "soupe", "brochette", "papillote", "tempura", "chaudree", "bisque", "tourte", "bouillabaisse", "etoile",
    };
    private static readonly HashSet<string> Pluriels = new(StringComparer.Ordinal) { "croquettes", "maki", "beignets" };

    public static string AvecArticle(string id, string nom)
    {
        if (nom == "") return "";
        return (Pluriels.Contains(id) ? "des " : Feminins.Contains(id) ? "une " : "un ") + Minuscule(nom);
    }

    // ---- Journal : une entrée de 1 à 3 phrases, de son point de vue, tirée des seuls faits du jour

    public sealed record Entree(string Jour, string Texte, string Humeur);

    private static readonly string[] ActivitesJournal =
        { "code", "tableur", "texte", "mail", "visio", "diaporama", "musique", "video", "lecture", "dessin", "jeu" };

    public static int Phrases(string t)
    {
        int n = 0;
        for (int i = 0; i < t.Length; i++)
            if (t[i] is '.' or '!' or '?' or '…' && (i + 1 == t.Length || t[i + 1] == ' ')) n++;
        return n;
    }

    // Les sujets du jour, du plus marquant au plus ordinaire (famille du gabarit, valeurs).
    public static List<(string Famille, Dictionary<string, string> Valeurs)> Sujets(FaitsDuJour f)
    {
        var l = new List<(string, Dictionary<string, string>)>();
        void S(bool si, string famille, params (string K, string V)[] v)
        {
            if (si) l.Add((famille, v.ToDictionary(x => x.K, x => x.V)));
        }
        S(f.Cf != "", "j-campagne", ("campagne", f.Cf));
        S(f.Nv > 0, "j-niveau", ("niveau", f.Nv.ToString(Ci)));
        S(f.Mo != "", "j-metier", ("metier", Minuscule(f.Mo)));
        S(f.Px != "" && f.Pq >= 2, "j-prise-rare", ("prise", f.Px));
        S(f.Vi > 0, "j-visite");
        S(f.Ex != "", "j-expedition", ("lieu", f.Ex));
        S(f.Cx != "", "j-plat", ("plat", f.Cx));
        S(f.Ob != "", "j-objet", ("objet", Minuscule(f.Ob)));
        S(f.Jx >= 3, "j-jeux", ("n", f.Jx.ToString(Ci)));
        S(f.Jx is > 0 and < 3, "j-jeu");
        S(f.Ca >= 5, "j-caresses");
        S(f.Ca is > 0 and < 5, "j-caresse");
        S(f.So > 0, "j-soins");
        S(f.Pc > 0 && f.Px != "" && f.Pq < 2, "j-peche", ("prise", f.Px));
        S(f.Qu > 0, "j-quetes", ("n", f.Qu.ToString(Ci)));
        S(f.Tv >= 300, "j-travail-long");
        var ac = f.Ac == "jeu-mmo" ? "jeu" : f.Ac;
        S(Array.IndexOf(ActivitesJournal, ac) >= 0 && f.Am >= 20, "j-act-" + ac);
        S(f.Ta >= 22 * 60, "j-tard");
        S(MeteoFamille(f.Me) != "", "j-meteo-" + MeteoFamille(f.Me));
        S(f.Ce > 0 && f.Cf == "", "j-aventure");
        S(f.Mn >= 5 || l.Count == 0, "j-calme");
        return l;
    }

    public static string Humeur(FaitsDuJour f) =>
        f.Cf != "" || f.Nv > 0 ? "fete"
        : f.Ca >= 5 ? "tendre"
        : f.Jx >= 3 || f.Pq >= 2 || f.Vi > 0 ? "joie"
        : f.Ta >= 23 * 60 || f.Tv >= 420 ? "fatigue"
        : f.Ca > 0 || f.So > 0 ? "caresse"
        : f.Tv >= 120 ? "concentre"
        : "repos";

    // L'entrée d'un jour (null : rien ne s'est passé). Ne dépend que du jour et des faits : PC et téléphone écrivent
    // exactement la même chose à partir des mêmes faits fusionnés.
    public static Entree? Ecrire(string jour, FaitsDuJour f, IReadOnlyList<Ligne> gabarits)
    {
        if (f.Vide) return null;
        var sujets = Sujets(f);
        var qui = new Qui(9, 2, "");
        var vides = new Dictionary<string, int>();
        var phrases = new List<string>();
        string? Une(string famille, Dictionary<string, string> v, int k)
        {
            var g = Choisir(gabarits, famille, qui, v, vides, jour + "|journal|" + famille + "|" + k.ToString(Ci));
            return g is null ? null : Majuscule(Remplir(g.Texte, v));
        }
        int premier = -1;
        for (int i = 0; i < sujets.Count && phrases.Count == 0; i++)
            if (Une(sujets[i].Famille, sujets[i].Valeurs, 1) is { } t)
            {
                phrases.Add(t);
                premier = i;
            }
        if (phrases.Count == 0) return null;
        bool Ajouter(string? t)
        {
            // Une seule fois « Aujourd'hui » par entrée : la suite s'en passe.
            if (t is not null && t.StartsWith("Aujourd'hui, ", StringComparison.Ordinal)) t = Majuscule(t["Aujourd'hui, ".Length..]);
            else if (t is not null && t.StartsWith("Aujourd'hui ", StringComparison.Ordinal)) t = Majuscule(t["Aujourd'hui ".Length..]);
            if (t is null || t.Length == 0 || Phrases(string.Join(" ", phrases.Append(t))) > 3) return false;
            phrases.Add(t);
            return true;
        }
        // Un mot appris (selon l'activité du jour), une fois sur trois ; s'il ne tient pas en entier, sa première phrase.
        var ac = f.Ac == "jeu-mmo" ? "jeu" : f.Ac;
        bool mot = false;
        if (Array.IndexOf(ActivitesJournal, ac) >= 0 && f.Am >= 20 && Tirer(jour + "|journal|mot", 3) == 0
            && Choisir(gabarits, "mot-" + ac, qui, new Dictionary<string, string>(), vides, jour + "|journal|mot-" + ac) is { } m
            && Une("j-mot", new Dictionary<string, string> { ["mot"] = m.Texte }, 3) is { } tm)
            mot = Ajouter(tm) || Ajouter(PremierePhrase(tm));
        if (!mot)
        {
            // Sinon, une deuxième chose (sa première phrase), parmi les quatre suivantes (pas la journée « calme » s'il
            // s'est passé autre chose), puis, une fois sur deux, une petite conclusion s'il reste de la place.
            var reste = sujets.Where((s, i) => i != premier && !(s.Famille == "j-calme" && sujets.Count > 1)).Take(4).ToList();
            if (reste.Count > 0)
            {
                var s = reste[Tirer(jour + "|journal|second", reste.Count)];
                if (Une(s.Famille, s.Valeurs, 2) is { } t) Ajouter(PremierePhrase(t));
            }
            if (Tirer(jour + "|journal|fin", 2) == 0) Ajouter(Une("j-fin", new Dictionary<string, string>(), 4));
        }
        return new Entree(jour, string.Join(" ", phrases), Humeur(f));
    }

    // La première phrase d'un texte (jusqu'au premier point, point d'exclamation ou d'interrogation suivi d'un blanc).
    public static string PremierePhrase(string t)
    {
        for (int i = 0; i < t.Length; i++)
            if (t[i] is '.' or '!' or '?' or '…' && (i + 1 == t.Length || t[i + 1] == ' ')) return t[..(i + 1)];
        return t;
    }

    // ---- Synchronisation : un message dédié, sur un sujet à part (les anciens appareils ne l'écoutent pas)

    public static string Sujet(string code) =>
        "pilou-" + Convert.ToHexString(System.Security.Cryptography.HMACSHA256.HashData(
            Encoding.UTF8.GetBytes(Telephone.Normaliser(code)), Encoding.UTF8.GetBytes("pilou-presence-v1"))).ToLowerInvariant()[..24];

    public static int Octets(string s) => Encoding.UTF8.GetByteCount(s);

    // Valeur sûre pour le format texte (ni séparateur ni saut de ligne), 40 caractères au plus.
    public static string Propre(string? s, int max = 40)
    {
        if (string.IsNullOrEmpty(s)) return "";
        var b = new StringBuilder();
        foreach (char ch in s)
            b.Append(ch is ';' or '=' or '|' or ',' || char.IsControl(ch) || char.IsSurrogate(ch) ? ' ' : ch);
        var r = Rogner(b.ToString());
        return r.Length > max ? Rogner(r[..max]) : r;
    }
}

// Les faits d'un jour, vus par un appareil (rien de personnel : des nombres, des noms d'objets ou d'espèces du jeu).
// Fusion : maximum des nombres, et pour chaque paire (nom, poids) celle de plus grand poids : ni l'ordre d'arrivée ni
// les doublons n'y changent rien, et ce qu'un téléphone a déjà crédité au PC n'est jamais compté deux fois.
public sealed class FaitsDuJour
{
    // Ma : 1 si la personne était là tôt le matin (entre 5 h et 7 h 30), pour le trait « lève-tôt ».
    public int Mn, Tv, Am, Ta, Jx, Ca, So, Pc, Pq, Cu, Qu, Ce, Vi, Nv, Mg, Ma;
    public string Ac = "", Px = "", Cx = "", Me = "", Cf = "", Mo = "", Ex = "", Ob = "";

    public bool Vide => Mn < 5 && Tv == 0 && Jx == 0 && Ca == 0 && So == 0 && Pc == 0 && Cu == 0 && Qu == 0 && Ce == 0 && Vi == 0
                        && Nv == 0 && Cf == "" && Mo == "" && Ex == "" && Ob == "" && Cx == "" && Px == "";

    private static readonly string[] OrdreMeteo = { "orage", "neige", "pluie", "averse", "brouillard", "vent", "chaleur", "froid", "degage", "nuageux" };

    private static int RangMeteo(string m)
    {
        int i = Array.IndexOf(OrdreMeteo, m);
        return i < 0 ? int.MaxValue : i;
    }

    private static string Min(string a, string b) => a == "" ? b : b == "" ? a : string.CompareOrdinal(a, b) <= 0 ? a : b;

    public static FaitsDuJour Fusion(FaitsDuJour a, FaitsDuJour b)
    {
        var r = new FaitsDuJour
        {
            Mn = Math.Max(a.Mn, b.Mn), Tv = Math.Max(a.Tv, b.Tv), Ta = Math.Max(a.Ta, b.Ta), Jx = Math.Max(a.Jx, b.Jx),
            Ca = Math.Max(a.Ca, b.Ca), So = Math.Max(a.So, b.So), Pc = Math.Max(a.Pc, b.Pc), Cu = Math.Max(a.Cu, b.Cu),
            Qu = Math.Max(a.Qu, b.Qu), Ce = Math.Max(a.Ce, b.Ce), Vi = Math.Max(a.Vi, b.Vi), Nv = Math.Max(a.Nv, b.Nv),
            Ma = Math.Max(a.Ma, b.Ma),
            Cx = Min(a.Cx, b.Cx), Cf = Min(a.Cf, b.Cf), Ex = Min(a.Ex, b.Ex), Ob = Min(a.Ob, b.Ob),
        };
        (r.Ac, r.Am) = a.Am > b.Am || (a.Am == b.Am && Min(a.Ac, b.Ac) == a.Ac) ? (a.Ac, a.Am) : (b.Ac, b.Am);
        (r.Px, r.Pq) = a.Px != "" && (b.Px == "" || a.Pq > b.Pq || (a.Pq == b.Pq && string.CompareOrdinal(a.Px, b.Px) <= 0)) ? (a.Px, a.Pq) : (b.Px, b.Pq);
        (r.Mo, r.Mg) = a.Mo != "" && (b.Mo == "" || a.Mg > b.Mg || (a.Mg == b.Mg && string.CompareOrdinal(a.Mo, b.Mo) <= 0)) ? (a.Mo, a.Mg) : (b.Mo, b.Mg);
        r.Me = RangMeteo(a.Me) <= RangMeteo(b.Me) ? (RangMeteo(a.Me) == RangMeteo(b.Me) ? Min(a.Me, b.Me) : a.Me) : b.Me;
        return r;
    }

    // « mn=120;tv=95;ac=code;… » : clés dans un ordre fixe, seulement ce qui n'est pas nul.
    public string Texte()
    {
        var b = new StringBuilder();
        void N(string k, int v)
        {
            if (v == 0) return;
            if (b.Length > 0) b.Append(';');
            b.Append(k).Append('=').Append(v.ToString(CultureInfo.InvariantCulture));
        }
        void S(string k, string v)
        {
            if (v == "") return;
            if (b.Length > 0) b.Append(';');
            b.Append(k).Append('=').Append(v);
        }
        N("mn", Mn); N("tv", Tv); S("ac", Ac); N("am", Am); N("ta", Ta); N("jx", Jx); N("ca", Ca); N("so", So);
        N("pc", Pc); S("px", Px); N("pq", Pq); N("cu", Cu); S("cx", Cx); N("qu", Qu); S("me", Me); S("cf", Cf); N("ce", Ce);
        N("vi", Vi); N("nv", Nv); S("mo", Mo); N("mg", Mg); S("ex", Ex); S("ob", Ob); N("ma", Ma);
        return b.ToString();
    }

    public static FaitsDuJour Lire(string? texte)
    {
        var f = new FaitsDuJour();
        if (string.IsNullOrEmpty(texte)) return f;
        foreach (var paire in texte.Split(';'))
        {
            int i = paire.IndexOf('=');
            if (i <= 0) continue;
            var k = paire[..i];
            var v = Presence.Propre(paire[(i + 1)..]);
            int n = int.TryParse(v, NumberStyles.Integer, CultureInfo.InvariantCulture, out var x) ? Math.Clamp(x, 0, 100_000) : 0;
            switch (k)
            {
                case "mn": f.Mn = n; break;
                case "tv": f.Tv = n; break;
                case "ac": f.Ac = v; break;
                case "am": f.Am = n; break;
                case "ta": f.Ta = Math.Min(n, 1439); break;
                case "jx": f.Jx = n; break;
                case "ca": f.Ca = n; break;
                case "so": f.So = n; break;
                case "pc": f.Pc = n; break;
                case "px": f.Px = v; break;
                case "pq": f.Pq = Math.Min(n, 9); break;
                case "cu": f.Cu = n; break;
                case "cx": f.Cx = v; break;
                case "qu": f.Qu = n; break;
                case "me": f.Me = v; break;
                case "cf": f.Cf = v; break;
                case "ce": f.Ce = n; break;
                case "vi": f.Vi = n; break;
                case "nv": f.Nv = Math.Min(n, 999); break;
                case "mo": f.Mo = v; break;
                case "mg": f.Mg = Math.Min(n, 9); break;
                case "ex": f.Ex = v; break;
                case "ob": f.Ob = v; break;
                case "ma": f.Ma = Math.Min(n, 1); break;
            }
        }
        return f;
    }

    public FaitsDuJour Copie() => Lire(Texte());
}

// Ce qu'un appareil sait de lui (et garde des autres) pour la complicité : des compteurs qui ne font que monter, les
// jours passés ensemble, les campagnes finies, les annonces déjà faites, le prénom (chiffré dans le groupe seulement).
public sealed class Appareil
{
    public string Id = "", Sorte = "pc";
    public long T;
    public int Minutes, Caresses, Soins, Jeux, PalierAnnonce;
    public SortedSet<int> Jours = new();
    public SortedSet<string> Finies = new(StringComparer.Ordinal), Fetes = new(StringComparer.Ordinal);
    public string Prenom = "";
    public long PrenomT = -1;
    public bool PrenomDemande;
    // Traits de personnalité (Traits.cs) : un bit par trait acquis, un bit par trait déjà annoncé. Jamais retirés.
    public long Traits, TraitsDits;
    // FaitsDuJour des derniers jours (message seulement ; l'état les range dans son journal).
    public SortedDictionary<string, FaitsDuJour> Recents = new(StringComparer.Ordinal);

    // Fusion de deux états du même appareil : maximum, union, prénom le plus récent. Renvoie vrai si quelque chose change.
    public bool Absorber(Appareil b)
    {
        var avant = Texte(true);
        T = Math.Max(T, b.T);
        Minutes = Math.Max(Minutes, b.Minutes);
        Caresses = Math.Max(Caresses, b.Caresses);
        Soins = Math.Max(Soins, b.Soins);
        Jeux = Math.Max(Jeux, b.Jeux);
        PalierAnnonce = Math.Max(PalierAnnonce, b.PalierAnnonce);
        Jours.UnionWith(b.Jours);
        Finies.UnionWith(b.Finies);
        Fetes.UnionWith(b.Fetes);
        if (b.PrenomT > PrenomT || (b.PrenomT == PrenomT && string.CompareOrdinal(b.Prenom, Prenom) < 0))
        {
            PrenomT = b.PrenomT;
            Prenom = b.Prenom;
        }
        PrenomDemande |= b.PrenomDemande;
        Traits |= b.Traits;
        TraitsDits |= b.TraitsDits;
        if (b.Sorte is "pc" or "tel") Sorte = b.Sorte;
        foreach (var (j, f) in b.Recents)
            Recents[j] = Recents.TryGetValue(j, out var x) ? FaitsDuJour.Fusion(x, f) : f.Copie();
        return avant != Texte(true);
    }

    private static string Hex(SortedSet<int> jours, out int origine)
    {
        origine = jours.Count == 0 ? 0 : jours.Min;
        if (jours.Count == 0) return "";
        int n = jours.Max - origine + 1;
        var b = new StringBuilder();
        for (int i = 0; i < n; i += 4)
        {
            int v = 0;
            for (int k = 0; k < 4; k++)
                if (jours.Contains(origine + i + k)) v |= 8 >> k;
            b.Append("0123456789abcdef"[v]);
        }
        return b.ToString();
    }

    // Texte de l'appareil (message et fichier d'état). recents : les lignes « d » des faits récents.
    public string Texte(bool recents = true, int maxRecents = int.MaxValue)
    {
        var ci = CultureInfo.InvariantCulture;
        var b = new StringBuilder();
        b.Append("a ").Append(Id).Append('\n');
        b.Append("k ").Append(Sorte).Append('\n');
        b.Append("t ").Append(T.ToString(ci)).Append('\n');
        b.Append("c ").Append(Minutes.ToString(ci)).Append(' ').Append(Caresses.ToString(ci)).Append(' ').Append(Soins.ToString(ci))
            .Append(' ').Append(Jeux.ToString(ci)).Append('\n');
        var hex = Hex(Jours, out var origine);
        if (hex != "") b.Append("j ").Append(origine.ToString(ci)).Append(' ').Append(hex).Append('\n');
        if (Finies.Count > 0) b.Append("f ").Append(string.Join(",", Finies)).Append('\n');
        if (PalierAnnonce > 0) b.Append("pa ").Append(PalierAnnonce.ToString(ci)).Append('\n');
        if (Fetes.Count > 0) b.Append("fe ").Append(string.Join(",", Fetes)).Append('\n');
        if (PrenomT >= 0) b.Append("n ").Append(PrenomT.ToString(ci)).Append(' ').Append(Prenom).Append('\n');
        if (PrenomDemande) b.Append("q 1\n");
        if (Traits != 0 || TraitsDits != 0)
            b.Append("tr ").Append(PilouBureau.Traits.Hex(Traits)).Append(' ').Append(PilouBureau.Traits.Hex(TraitsDits)).Append('\n');
        if (recents)
            foreach (var (j, f) in Recents.Reverse().Take(maxRecents).Reverse())
                if (f.Texte() is { Length: > 0 } ft) b.Append("d ").Append(j).Append(' ').Append(ft).Append('\n');
        return b.ToString();
    }

    // Lit une ligne de l'appareil ; faux si elle n'en est pas une.
    public bool LireLigne(string ligne)
    {
        int i = ligne.IndexOf(' ');
        var k = i < 0 ? ligne : ligne[..i];
        var v = i < 0 ? "" : ligne[(i + 1)..];
        var ci = CultureInfo.InvariantCulture;
        int N(string s) => int.TryParse(s, NumberStyles.Integer, ci, out var n) ? Math.Clamp(n, 0, 100_000_000) : 0;
        switch (k)
        {
            case "a": Id = Presence.Propre(v, 64); return true;
            case "k": Sorte = v == "tel" ? "tel" : "pc"; return true;
            case "t": T = long.TryParse(v, NumberStyles.Integer, ci, out var t) ? Math.Max(0, t) : 0; return true;
            case "c":
            {
                var p = v.Split(' ');
                if (p.Length >= 4)
                {
                    Minutes = N(p[0]);
                    Caresses = N(p[1]);
                    Soins = N(p[2]);
                    Jeux = N(p[3]);
                }
                return true;
            }
            case "j":
            {
                var p = v.Split(' ');
                if (p.Length == 2 && int.TryParse(p[0], NumberStyles.Integer, ci, out var o) && o is > 0 and < 200_000 && p[1].Length <= 2000)
                    for (int x = 0; x < p[1].Length; x++)
                    {
                        int h = "0123456789abcdef".IndexOf(p[1][x]);
                        if (h < 0) continue;
                        for (int bit = 0; bit < 4; bit++)
                            if ((h & (8 >> bit)) != 0) Jours.Add(o + x * 4 + bit);
                    }
                return true;
            }
            case "f":
                foreach (var x in v.Split(',')) if (Presence.Propre(x) is { Length: > 0 } id && Finies.Count < 100) Finies.Add(id);
                return true;
            case "pa": PalierAnnonce = Math.Min(N(v), Presence.Paliers.Length - 1); return true;
            case "fe":
                foreach (var x in v.Split(',')) if (Presence.Propre(x, 8) is { Length: > 0 } id && Fetes.Count < 200) Fetes.Add(id);
                return true;
            case "n":
            {
                int s = v.IndexOf(' ');
                var tt = s < 0 ? v : v[..s];
                if (long.TryParse(tt, NumberStyles.Integer, ci, out var pt) && pt >= 0)
                {
                    PrenomT = pt;
                    Prenom = Presence.NettoyerPrenom(s < 0 ? "" : v[(s + 1)..]);
                }
                return true;
            }
            case "q": PrenomDemande = v == "1"; return true;
            case "tr":
            {
                var p = v.Split(' ');
                if (p.Length == 2)
                {
                    Traits = PilouBureau.Traits.DeHex(p[0]);
                    TraitsDits = PilouBureau.Traits.DeHex(p[1]);
                }
                return true;
            }
            case "d":
            {
                int s = v.IndexOf(' ');
                if (s > 0 && Presence.JourDe(v[..s]) != int.MinValue && Recents.Count < 30) Recents[v[..s]] = FaitsDuJour.Lire(v[(s + 1)..]);
                return true;
            }
        }
        return false;
    }

    public static Appareil? Lire(string texte)
    {
        var a = new Appareil();
        foreach (var l in texte.Replace("\r\n", "\n").Split('\n'))
            if (l.Length > 0) a.LireLigne(l);
        return a.Id == "" ? null : a;
    }

    // Le message à publier : sous Presence.TailleMessage octets (les faits les plus anciens partent d'abord).
    public string Message()
    {
        for (int n = Presence.JoursDansMessage; n >= 0; n--)
        {
            var m = "pilou-presence 1\n" + Texte(true, n);
            if (Presence.Octets(m) <= Presence.TailleMessage || n == 0) return m;
        }
        return "pilou-presence 1\n" + Texte(false);
    }

    public static Appareil? LireMessage(string texte)
    {
        var t = texte.Replace("\r\n", "\n");
        if (!t.StartsWith("pilou-presence 1\n", StringComparison.Ordinal)) return null;
        return Lire(t["pilou-presence 1\n".Length..]);
    }
}
