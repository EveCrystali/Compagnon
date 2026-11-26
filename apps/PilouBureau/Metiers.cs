namespace PilouBureau;

// Métiers : le temps passé dans chaque activité fait monter un métier (paliers d'heures).
// Succès : des défis de comportement (« 4 h de code d'affilée »), annoncés une fois, avec de l'XP.
public static class Metiers
{
    public sealed record Metier(string Id, string Nom, string[] Activites);

    public static readonly IReadOnlyList<Metier> Tous = new Metier[]
    {
        new("codeur", "Codeur", new[] { "code" }),
        new("tableur", "As du tableur", new[] { "tableur" }),
        new("joueur", "Joueur", new[] { "jeu", "jeu-mmo" }),
        new("musicien", "Mélomane", new[] { "musique" }),
        new("cinephile", "Cinéphile", new[] { "video" }),
        new("lecteur", "Lecteur", new[] { "lecture" }),
        new("artiste", "Artiste", new[] { "dessin" }),
        new("orateur", "Orateur", new[] { "visio", "diaporama" }),
        new("ecrivain", "Écrivain", new[] { "texte" }),
        new("facteur", "Facteur", new[] { "mail" }),
    };

    // Heures nécessaires pour chaque niveau de métier (1 à 6).
    public static readonly int[] Paliers = { 1, 5, 15, 40, 100, 250 };
    public static readonly string[] Grades = { "Novice", "Apprenti", "Compagnon", "Confirmé", "Expert", "Maître", "Légende" };

    public static long Secondes(Metier m, IReadOnlyDictionary<string, long> parActivite) =>
        m.Activites.Sum(a => parActivite.TryGetValue(a, out var s) ? s : 0);

    public static int Niveau(long secondes)
    {
        double heures = secondes / 3600.0;
        int n = 0;
        while (n < Paliers.Length && heures >= Paliers[n]) n++;
        return n;
    }

    // « 17 h / 40 h » vers le palier suivant ; au dernier palier, le total.
    public static string Progres(long secondes)
    {
        int n = Niveau(secondes);
        var h = secondes / 3600.0;
        return n >= Paliers.Length ? $"{h:0} h" : $"{h:0.#} h / {Paliers[n]} h";
    }

    public static Dictionary<string, int> Niveaux(IReadOnlyDictionary<string, long> parActivite) =>
        Tous.ToDictionary(m => m.Id, m => Niveau(Secondes(m, parActivite)));

    public static string DeActivite(string activite) => Tous.FirstOrDefault(m => m.Activites.Contains(activite))?.Id ?? "";
}

// Ce que l'on sait pour juger les succès (les compteurs du profil et la série en cours).
public sealed record Stats(
    IReadOnlyDictionary<string, long> Secondes, double SerieCodeSec, int ReunionsSemaine, int Presentations,
    DateTime Heure, string Activite, int SeancesClavier = 0, int Captures = 0, EtatDefense? Defense = null);

public static class Succes
{
    public sealed record Defi(string Id, string Nom, string Description, Func<Stats, double> Avancement, double But, int Xp = 25)
    {
        public bool Atteint(Stats s) => Avancement(s) >= But;
    }

    private static double H(Stats s, params string[] activites) => activites.Sum(a => s.Secondes.TryGetValue(a, out var v) ? v : 0) / 3600.0;

    private static bool Actif(Stats s) => s.Activite != "" && s.Activite != "nuit";

    public static readonly IReadOnlyList<Defi> Tous = new Defi[]
    {
        new("marathon", "Marathon", "4 h de code d'affilée", s => s.SerieCodeSec / 3600.0, 4),
        new("noctambule", "Noctambule", "actif entre 1 h et 4 h du matin", s => Actif(s) && s.Heure.Hour is >= 1 and < 4 ? 1 : 0, 1),
        new("leve-tot", "Lève-tôt", "actif avant 6 h du matin", s => Actif(s) && s.Heure.Hour is >= 4 and < 6 ? 1 : 0, 1),
        new("visio-man", "Visio-man", "10 réunions en 7 jours", s => s.ReunionsSemaine, 10),
        new("orateur", "Orateur", "5 présentations en plein écran", s => s.Presentations, 5),
        new("melomane", "Mélomane", "10 h de musique", s => H(s, "musique"), 10),
        new("tableur-fou", "Tableur fou", "10 h de tableur", s => H(s, "tableur"), 10),
        new("codeur-confirme", "Codeur confirmé", "50 h de code", s => H(s, "code"), 50, 50),
        new("gamer", "Gamer", "20 h de jeu", s => H(s, "jeu", "jeu-mmo"), 20),
        new("aventurier", "Aventurier", "10 h de jeu de rôle en ligne", s => H(s, "jeu-mmo"), 10),
        new("cinephile", "Cinéphile", "10 h de vidéo", s => H(s, "video"), 10),
        new("rat-de-bibliotheque", "Rat de bibliothèque", "10 h de lecture", s => H(s, "lecture"), 10),
        new("artiste", "Artiste", "10 h de dessin ou de création", s => H(s, "dessin"), 10),
        new("plume", "Plume", "10 h d'écriture", s => H(s, "texte"), 10),
        new("facteur", "Facteur", "5 h de mail", s => H(s, "mail"), 5),
        new("explorateur", "Explorateur", "8 activités différentes", s => Activites.Toutes.Count(a => s.Secondes.TryGetValue(a, out var v) && v >= 60), 8),
        new("dactylo", "Dactylo", "taper avec Pilou au clavier 25 fois", s => s.SeancesClavier, 25),
        new("photographe", "Photographe", "10 captures d'écran photographiées par Pilou", s => s.Captures, 10),
        new("couteau-suisse", "Couteau suisse", "4 métiers au rang Compagnon", s => Metiers.Tous.Count(m => Metiers.Niveau(Metiers.Secondes(m, s.Secondes)) >= 2), 4, 50),
        // Défense du bureau (DefenseTests.cs).
        new("pare-feu", "Pare-feu", "vaincre un Bug de prod à Défense du bureau", s => s.Defense?.Boss ?? 0, 1),
        new("rempart", "Rempart", "atteindre la vague 10 à Défense du bureau", s => s.Defense?.MeilleureVague ?? 0, 10, 40),
        new("gardien", "Gardien du bureau", "10 000 points à Défense du bureau", s => s.Defense?.Meilleur ?? 0, 10_000, 40),
    };

    // Les succès qui viennent d'être atteints (jamais deux fois le même).
    public static List<Defi> Nouveaux(Stats s, IEnumerable<string> deja)
    {
        var obtenus = deja.ToHashSet();
        return Tous.Where(d => !obtenus.Contains(d.Id) && d.Atteint(s)).ToList();
    }

    public static string Progres(Defi d, Stats s)
    {
        var a = Math.Min(d.Avancement(s), d.But);
        return d.But <= 1 ? "" : d.Id switch
        {
            "marathon" => $"{a:0.#} h / {d.But} h",
            "visio-man" or "orateur" or "explorateur" or "couteau-suisse" or "dactylo" or "photographe" => $"{a:0} / {d.But}",
            "rempart" => $"vague {a:0} / {d.But}",
            "gardien" => $"{a:0} / {d.But:0} points",
            _ => $"{a:0.#} h / {d.But} h",
        };
    }
}
