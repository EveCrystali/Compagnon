namespace PilouBureau;

// Pêche et cuisine, la partie sans dessin : ce qu'on peut pêcher, avec quelle chance, ce qu'on en
// cuisine. Tout tirage passe par un Random reçu en paramètre (graine fixe dans les tests).

// Rareté : un signe de forme et un cadre différent par rang, pas seulement une couleur.
public enum Rarete { Commun, PeuCommun, Rare, Epique, Legendaire, Mythique }

// Forme du sprite d'une prise (Peche.cs les dessine) ; couleurs : principale, claire, détail.
public enum Forme { Poisson, Long, Plat, Coquillage, Crabe, Algue, Botte, Bouteille, Caillou, Cle, Pieuvre, Hippocampe, Coffre, Perle, Baleine }

public sealed record Prise(string Id, string Nom, Rarete Rarete, int Xp, int NiveauMin, Forme Forme, string Couleur, string Clair,
    string Detail, string Saveur = "")
{
    // Saveur vide : pas un ingrédient (botte, clé…).
    public bool Comestible => Saveur != "";
}

public sealed record Recette(string Id, string Nom, int NiveauMin, string[] Saveurs, int Xp);

// Ce que la marmite a donné.
public sealed record Plat(string Id, string Nom, bool Decouverte, bool Rate, int Xp, IReadOnlyList<string> Utilises, bool Inventee);

public static class Butin
{
    // Pêche « à la main » (clic quand ça mord) : toujours une prise. Seul, Pilou ferre au hasard :
    // une chance sur trois environ, et jamais mieux que « rare ».
    public const double ChanceSeul = 0.35;
    public const Rarete PlafondSeul = Rarete.Rare;

    public static readonly IReadOnlyList<Prise> Prises = new Prise[]
    {
        new("goujon", "Goujon bleu", Rarete.Commun, 3, 1, Forme.Poisson, "#4a8fdc", "#b4dbff", "#1f4f8a", "poisson"),
        new("ablette", "Ablette", Rarete.Commun, 3, 1, Forme.Poisson, "#adbac7", "#e6ecf2", "#57606a", "poisson"),
        new("algue", "Algue frisée", Rarete.Commun, 2, 1, Forme.Algue, "#3f7fd6", "#8fbaf0", "#1f4f8a", "algue"),
        new("botte", "Vieille botte", Rarete.Commun, 1, 1, Forme.Botte, "#768390", "#adbac7", "#3b4654"),
        new("caillou", "Caillou tout lisse", Rarete.Commun, 1, 1, Forme.Caillou, "#909dab", "#cdd9e5", "#57606a"),
        new("perche", "Perche rayée", Rarete.PeuCommun, 6, 2, Forme.Poisson, "#f2a94e", "#ffd59a", "#7a4210", "poisson"),
        new("ecrevisse", "Écrevisse", Rarete.PeuCommun, 6, 2, Forme.Crabe, "#d9803a", "#ffc89a", "#8a4a1f", "crustace"),
        new("spirale", "Coquillage spirale", Rarete.PeuCommun, 5, 2, Forme.Coquillage, "#f6f8fa", "#ffffff", "#c9d1d9", "coquillage"),
        new("bouteille", "Bouteille à message", Rarete.PeuCommun, 8, 3, Forme.Bouteille, "#6cb6ff", "#d2eaff", "#1f4f8a"),
        new("truite", "Truite argentée", Rarete.PeuCommun, 7, 3, Forme.Poisson, "#b8c4d2", "#ffffff", "#3b4654", "poisson"),
        new("anguille", "Anguille d'encre", Rarete.Rare, 14, 5, Forme.Long, "#2a5ea8", "#6cb6ff", "#0d2a4d", "poisson"),
        new("crabe", "Crabe bleu", Rarete.Rare, 14, 6, Forme.Crabe, "#3f7fd6", "#8fbaf0", "#0d2a4d", "crustace"),
        new("cle", "Clé rouillée", Rarete.Rare, 12, 7, Forme.Cle, "#c97a28", "#f2a94e", "#7a4210"),
        new("pieuvre", "Pieuvre de poche", Rarete.Rare, 16, 8, Forme.Pieuvre, "#9b8cff", "#d2caff", "#3a2a7a", "mollusque"),
        new("saumon", "Saumon des glaces", Rarete.Rare, 18, 10, Forme.Poisson, "#f69d50", "#ffd8b0", "#8a4a1f", "poisson"),
        new("lanterne", "Poisson-lanterne", Rarete.Epique, 30, 15, Forme.Poisson, "#1f4f8a", "#ffd8b0", "#f69d50", "poisson"),
        new("hippocampe", "Hippocampe doré", Rarete.Epique, 32, 18, Forme.Hippocampe, "#f2a94e", "#ffe7b8", "#7a4210", "poisson"),
        new("coffre", "Coffret englouti", Rarete.Epique, 35, 20, Forme.Coffre, "#c97a28", "#f2a94e", "#3b4654"),
        new("raie", "Raie étoilée", Rarete.Epique, 34, 22, Forme.Plat, "#6a5acd", "#d2caff", "#ffd8b0", "poisson"),
        new("perle", "Perle de lune", Rarete.Legendaire, 60, 25, Forme.Perle, "#e6ecf2", "#ffffff", "#9b8cff"),
        new("carpe", "Carpe des pixels", Rarete.Legendaire, 70, 30, Forme.Poisson, "#f69d50", "#ffffff", "#2f7ed8", "poisson"),
        new("comete", "Poisson-comète", Rarete.Legendaire, 80, 35, Forme.Long, "#ffd8b0", "#ffffff", "#f69d50", "poisson"),
        new("baleineau", "Baleineau de nuage", Rarete.Legendaire, 100, 40, Forme.Baleine, "#b4dbff", "#ffffff", "#4a8fdc", "poisson"),
    };

    public static Prise? Trouver(string id) => Prises.FirstOrDefault(p => p.Id == id);

    public static string Signe(Rarete r) => r switch
    {
        Rarete.Commun => "·", Rarete.PeuCommun => "◇", Rarete.Rare => "◆", Rarete.Epique => "✦", _ => "★",
    };

    public static string NomRarete(Rarete r) => r switch
    {
        Rarete.Commun => "commun", Rarete.PeuCommun => "peu commun", Rarete.Rare => "rare", Rarete.Epique => "épique", _ => "légendaire",
    };

    // Poids des raretés : les rangs hauts gagnent du poids avec le niveau (et la canne dorée, niveau 30).
    public static double Poids(Rarete r, int niveau, bool canneDoree = false) => r switch
    {
        Rarete.Commun => 60,
        Rarete.PeuCommun => 26 + niveau * 0.3,
        Rarete.Rare => 10 + niveau * 0.35,
        Rarete.Epique => 3 + niveau * 0.2,
        _ => 0.6 + niveau * 0.06 + (canneDoree ? 1.5 : 0),
    };

    // Une prise, ou rien (Pilou seul a raté son coup).
    public static Prise? Tirer(Random hasard, int niveau, bool seul, bool canneDoree = false)
    {
        if (seul && hasard.NextDouble() >= ChanceSeul) return null;
        var possibles = Prises.Where(p => p.NiveauMin <= niveau && (!seul || p.Rarete <= PlafondSeul)).ToList();
        double total = possibles.Sum(p => Poids(p.Rarete, niveau, canneDoree));
        double x = hasard.NextDouble() * total;
        foreach (var p in possibles)
        {
            x -= Poids(p.Rarete, niveau, canneDoree);
            if (x < 0) return p;
        }
        return possibles[^1];
    }

    // XP d'une prise : la première de son espèce compte double (+5).
    public static int XpPrise(Prise p, bool nouvelle) => nouvelle ? p.Xp * 2 + 5 : p.Xp;

    // ---- Cuisine

    // Recettes du livre : saveurs demandées (une par ingrédient), débloquées par niveau.
    public static readonly IReadOnlyList<Recette> Recettes = new Recette[]
    {
        new("grille", "Poisson grillé", 1, new[] { "poisson" }, 4),
        new("tartine", "Tartine de la rivière", 1, new[] { "algue" }, 3),
        new("soupe", "Soupe du pêcheur", 2, new[] { "poisson", "algue" }, 8),
        new("croquettes", "Croquettes croustillantes", 2, new[] { "poisson", "poisson" }, 8),
        new("ecume", "Bouillon d'écume", 3, new[] { "coquillage" }, 6),
        new("brochette", "Brochette des berges", 3, new[] { "crustace" }, 7),
        new("papillote", "Papillote aux algues", 4, new[] { "poisson", "algue", "algue" }, 11),
        new("maki", "Makis de pixels", 5, new[] { "poisson", "algue" }, 10),
        new("gratin", "Gratin de la marée", 5, new[] { "crustace", "poisson" }, 12),
        new("tempura", "Tempura du soir", 6, new[] { "crustace", "algue" }, 12),
        new("chaudree", "Chaudrée des marins", 7, new[] { "coquillage", "poisson", "algue" }, 16),
        new("beignets", "Beignets de calamar", 8, new[] { "mollusque" }, 14),
        new("paella", "Riz de la lagune", 9, new[] { "crustace", "coquillage", "poisson" }, 20),
        new("ceviche", "Ceviche à l'ambre", 10, new[] { "poisson", "poisson", "algue" }, 18),
        new("ramen", "Ramen du clavier", 11, new[] { "poisson", "algue", "mollusque" }, 22),
        new("bisque", "Bisque bleue", 12, new[] { "crustace", "crustace" }, 20),
        new("fumet", "Fumet de minuit", 13, new[] { "poisson", "coquillage" }, 18),
        new("tourte", "Tourte du port", 14, new[] { "poisson", "poisson", "crustace" }, 24),
        new("carpaccio", "Carpaccio givré", 15, new[] { "poisson" }, 14),
        new("curry", "Curry des îles", 16, new[] { "crustace", "mollusque", "algue" }, 28),
        new("plateau", "Plateau de la criée", 18, new[] { "coquillage", "coquillage", "crustace" }, 30),
        new("bouillabaisse", "Marmite de la calanque", 20, new[] { "poisson", "poisson", "crustace", "coquillage" }, 40),
        new("risotto", "Risotto d'encre", 22, new[] { "mollusque", "algue" }, 30),
        new("feuillete", "Feuilleté des abysses", 24, new[] { "poisson", "mollusque", "crustace" }, 36),
        new("banquet", "Banquet des mouettes", 26, new[] { "poisson", "poisson", "poisson" }, 38),
        new("lune", "Velouté clair de lune", 28, new[] { "coquillage", "algue", "algue" }, 34),
        new("etoile", "Tarte étoilée", 30, new[] { "poisson", "crustace", "algue" }, 42),
        new("festin", "Festin du grand lac", 35, new[] { "poisson", "crustace", "mollusque", "coquillage" }, 60),
        new("nuage", "Soufflé de nuage", 40, new[] { "poisson", "algue", "coquillage" }, 55),
        new("legende", "Plat de légende", 45, new[] { "poisson", "poisson", "crustace", "mollusque", "algue" }, 90),
    };

    // Plats inventés : une préparation, un ingrédient, une touche. Assez de combinaisons pour qu'un
    // nouveau plat sorte presque à chaque fois.
    private static readonly string[] Preparations =
    {
        "Soupe", "Poêlée", "Tartine", "Brochette", "Velouté", "Gratin", "Beignets", "Papillote", "Salade", "Tourte", "Compotée",
        "Rouleaux", "Fricassée", "Bouchées", "Galette", "Croustillant", "Mijoté", "Crumble",
    };

    private static readonly string[] Touches =
    {
        "du dimanche", "à l'ancienne", "de minuit", "façon Pilou", "aux étoiles", "du pêcheur", "en croûte de sel", "du matin",
        "au beurre noisette", "des grands jours", "à la vapeur", "au feu de bois", "du lundi", "de la lagune", "en habit de fête",
        "au clair de lune", "des copains", "sans prétention",
    };

    private static string De(string mot) => "aeiouyéèêàâîôûh".Contains(char.ToLowerInvariant(mot[0])) ? $"d'{mot}" : $"de {mot}";

    // Nom court d'un ingrédient dans un plat : « Goujon bleu » → « goujon bleu », « Vieille… » jamais (non comestible).
    private static string Ingredient(Prise p) => char.ToLowerInvariant(p.Nom[0]) + p.Nom[1..];

    public static string Inventer(Random hasard, Prise ingredient) =>
        $"{Preparations[hasard.Next(Preparations.Length)]} {De(Ingredient(ingredient))} {Touches[hasard.Next(Touches.Length)]}";

    // Peut-on cuisiner cette recette avec ce stock (une saveur par ingrédient) ? Renvoie les ids pris.
    public static List<string>? Choisir(Recette r, IReadOnlyDictionary<string, int> stock)
    {
        var reste = stock.Where(kv => kv.Value > 0).ToDictionary(kv => kv.Key, kv => kv.Value);
        var pris = new List<string>();
        foreach (var saveur in r.Saveurs)
        {
            // L'ingrédient le plus commun d'abord : les raretés se gardent.
            var id = reste.Keys.Select(Trouver).Where(p => p is not null && p.Saveur == saveur && reste[p.Id] > 0)
                .OrderBy(p => p!.Rarete).ThenBy(p => p!.Xp).Select(p => p!.Id).FirstOrDefault();
            if (id is null) return null;
            reste[id]--;
            pris.Add(id);
        }
        return pris;
    }

    public static bool PeutCuisiner(IReadOnlyDictionary<string, int> stock) =>
        stock.Any(kv => kv.Value > 0 && Trouver(kv.Key) is { Comestible: true });

    // Chance de rater (fumée noire) : 8 %, moins avec le niveau ; remuer la marmite l'annule.
    public static double ChanceRate(int niveau, bool remue, bool marmiteCuivre = false) =>
        remue ? 0 : Math.Max(0.02, 0.08 - (marmiteCuivre ? 0.04 : 0) - niveau * 0.0005);

    // Une recette du livre si le stock le permet (plutôt une pas encore faite), sinon un plat inventé.
    public static Plat? Cuisiner(Random hasard, int niveau, IReadOnlyDictionary<string, int> stock, ICollection<string> connues, bool remue = false,
        bool marmiteCuivre = false)
    {
        if (!PeutCuisiner(stock)) return null;
        var possibles = Recettes.Where(r => r.NiveauMin <= niveau)
            .Select(r => (Recette: r, Pris: Choisir(r, stock)))
            .Where(x => x.Pris is not null)
            .ToList();
        var nouvelles = possibles.Where(x => !connues.Contains(x.Recette.Id)).ToList();
        bool rate = hasard.NextDouble() < ChanceRate(niveau, remue, marmiteCuivre);

        // Un plat du livre jamais fait : on le tente en priorité. Sinon, une fois sur deux, on invente.
        (Recette Recette, List<string>? Pris)? choisie =
            nouvelles.Count > 0 && hasard.NextDouble() < 0.75 ? nouvelles[hasard.Next(nouvelles.Count)]
            : possibles.Count > 0 && hasard.NextDouble() < 0.5 ? possibles[hasard.Next(possibles.Count)]
            : null;

        if (choisie is { } c)
        {
            var neuf = !connues.Contains(c.Recette.Id);
            if (rate) return new Plat(c.Recette.Id, c.Recette.Nom, false, true, 1, c.Pris!, false);
            return new Plat(c.Recette.Id, c.Recette.Nom, neuf, false, neuf ? c.Recette.Xp * 2 : c.Recette.Xp, c.Pris!, false);
        }

        // Plat inventé : un ingrédient comestible du stock (le plus commun), un nom tiré au sort.
        var ingredient = stock.Where(kv => kv.Value > 0).Select(kv => Trouver(kv.Key)).Where(p => p is { Comestible: true })
            .OrderBy(p => p!.Rarete).ThenBy(_ => hasard.Next()).First()!;
        var nom = Inventer(hasard, ingredient);
        var id = "inv:" + nom;
        if (rate) return new Plat(id, nom, false, true, 1, new[] { ingredient.Id }, true);
        bool decouverte = !connues.Contains(id);
        int xp = 2 + ingredient.Xp + (decouverte ? 4 : 0);
        return new Plat(id, nom, decouverte, false, xp, new[] { ingredient.Id }, true);
    }
}
