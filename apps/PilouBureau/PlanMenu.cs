namespace PilouBureau;

// Le plan du menu clic droit « Sept portes » (docs/AUDIT-MENU.md, « Le menu retenu ») : rien que du texte et des
// règles, testable sans Windows. La construction WPF est dans MenuPortes.cs.
//
//   [bandeau : niveau · XP · po]                 → boutique (seule porte)
//   ── En ce moment ──   0 à 2 lignes, place fixe, seulement si quelque chose se passe
//   ── Toujours là ──    (ce titre n'apparaît que sous une zone « En ce moment »)
//   ♥ Prendre soin · ✉ Aventure… · ⚔ Expédition ▸ · ► Jouer ▸ · 📖 Journal…
//   ─────
//   ◐ Apparence ▸ · ◎ Il se montre ▸ · ◌ Il se cache ▸ · ★ Progrès ▸ · ⇄ Amis et appareils ▸ · ⚙ Réglages ▸
//   ─────
//   ◌ Se cacher 10 min · ⏻ Quitter
public enum EnCeMoment
{
    Attend,     // ✉ il est revenu d'aventure et attend la réponse
    Expedition, // ⚔ il est en expédition : voir, rappeler
    Visite,     // ↩ il est parti chez un ami : le rappeler
    Soin,       // ♥ une jauge est basse ou il boude
    Jeu,        // ■ un petit jeu est en cours : l'arrêter
}

public readonly record struct Porte(string Signe, string Titre, bool Sous);

public static class PlanMenu
{
    // La zone « En ce moment » ne dépasse jamais deux lignes : au-delà, le menu bougerait trop d'une fois à l'autre.
    public const int MomentsMax = 2;

    // Ordre de priorité fixé par l'audit : ce qui attend une réponse, puis ce qui est loin, puis le soin, puis le jeu.
    public static IReadOnlyList<EnCeMoment> Moments(bool attend, bool expedition, bool visite, bool soin, bool jeu)
    {
        var l = new List<EnCeMoment>(MomentsMax);
        void Si(bool vrai, EnCeMoment m)
        {
            if (vrai && l.Count < MomentsMax) l.Add(m);
        }
        Si(attend, EnCeMoment.Attend);
        Si(expedition, EnCeMoment.Expedition);
        Si(visite, EnCeMoment.Visite);
        Si(soin, EnCeMoment.Soin);
        Si(jeu, EnCeMoment.Jeu);
        return l;
    }

    public static string Signe(EnCeMoment m) => m switch
    {
        EnCeMoment.Attend => "✉",
        EnCeMoment.Expedition => "⚔",
        EnCeMoment.Visite => "↩",
        EnCeMoment.Soin => "♥",
        _ => "■",
    };

    public const string TitreMoment = "En ce moment";
    public const string TitreToujours = "Toujours là";

    // Les portes, dans l'ordre. Sous : la porte ouvre un sous-menu (▸) ; sinon un clic agit ou ouvre une fenêtre.
    public static readonly Porte Soin = new("♥", "Prendre soin", false);
    public static readonly Porte Aventure = new("✉", "Aventure…", false);
    public static readonly Porte Expedition = new("⚔", "Expédition", true);
    public static readonly Porte Jouer = new("►", "Jouer", true);
    public static readonly Porte Journal = new("📖", "Journal…", false);
    public static readonly Porte Apparence = new("◐", "Apparence", true);
    public static readonly Porte SeMontre = new("◎", "Il se montre", true);
    public static readonly Porte SeCache = new("◌", "Il se cache", true);
    public static readonly Porte Progres = new("★", "Progrès", true);
    public static readonly Porte Amis = new("⇄", "Amis et appareils", true);
    public static readonly Porte Reglages = new("⚙", "Réglages", true);
    public static readonly Porte Cacher = new("◌", "Se cacher 10 min", false);
    public static readonly Porte Quitter = new("⏻", "Quitter", false);

    // Trois blocs séparés par un trait : le quotidien, les réglages et suivis, la sortie.
    public static readonly IReadOnlyList<IReadOnlyList<Porte>> Blocs = new IReadOnlyList<Porte>[]
    {
        new[] { Soin, Aventure, Expedition, Jouer, Journal },
        new[] { Apparence, SeMontre, SeCache, Progres, Amis, Reglages },
        new[] { Cacher, Quitter },
    };

    // Lignes stables du premier niveau, bandeau compris (sans titres ni zone « En ce moment »).
    public static int LignesStables => 1 + Blocs.Sum(b => b.Count);

    // L'état des soins dit en clair, à la suite de « Prendre soin » (« Prendre soin · il a faim »).
    public static string EtatSoins(bool vacances, bool boude, bool amadoue, bool rayonne, string? manque) =>
        vacances ? "en vacances"
        : amadoue ? "il se laisse amadouer ☁ (gains ×0,6)"
        : boude ? "il boude ☁ (gains ×0,6)"
        : manque is not null ? Manque(manque)
        : rayonne ? "il rayonne ✧ (gains ×1,2)"
        : "tout va bien";

    // Les noms de Soins.Besoins (faim, proprete, moral).
    public static string Manque(string besoin) => besoin switch
    {
        "faim" => "il a faim",
        "proprete" => "il a besoin d'un bain",
        "moral" => "il a besoin d'un câlin",
        _ => "il a besoin de toi",
    };
}
