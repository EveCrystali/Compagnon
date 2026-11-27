namespace PilouBureau;

// Boutique de Pilou : gratuite, virtuelle. On y dépense des pièces d'or (« po ») gagnées en quêtes ;
// aucune vraie monnaie, aucun achat réel. Rayons par emplacement (Tête, Yeux, Cou…) ; dans chaque rayon,
// des rangées par palier de niveau (1, 5, 10, 15, 20, 30, 40, 50) : le niveau ouvre la rangée, les po
// achètent l'objet. Les offres du jour sont une vitrine (la première à -25 %). Dessins : assets/sprites.
// Boutique garnie (assets/catalogue.txt, écrit par outils/sprites/garde_robe.py, lu aussi par Boutique.java) :
// ensembles thématiques avec un bonus quand ils sont portés en entier, articles de saison, articles « de passage »
// (quelques jours par mois en vitrine), titres affichés, et une collection dont les paliers offrent titres et cadres.
public sealed record Article(string Id, string Nom, string Slot, int Prix, int NiveauMin, Rarete Rarete, bool Permanent = false)
{
    // Numéro stable du catalogue garni (0 : catalogue d'origine) : la synchro envoie l'inventaire en bits (Garde).
    public int Numero { get; init; }
    // Saison où il s'achète ("" : toute l'année) : hiver, printemps, ete, automne, frissons, fetes.
    public string Saison { get; init; } = "";
    public string Ensemble { get; init; } = "";
    // Ne s'achète que les jours où il passe en vitrine (Boutique.DePassage).
    public bool Passage { get; init; }
    // Récompense de collection ou d'ensemble (titre, cadre) : ne s'achète pas, se gagne.
    public bool Recompense { get; init; }
}

// Ensemble thématique : porté en entier, il ajoute un effet (Bonus, un sprite) ; possédé en entier, il donne un titre.
public sealed record Ensemble(string Id, string Nom, string Signe, string Bonus, string Titre, IReadOnlyList<string> Pieces)
{
    public string IdTitre => "titre-ens-" + Id;
}

// Palier de collection : à Nombre articles possédés (0 : tout le catalogue), un titre ou un cadre de bulle.
public sealed record PalierCollection(int Nombre, string Id, string Slot, string Nom);

// Ce que Pilou porte : un objet par emplacement, horodaté (entre appareils, la dernière écriture gagne).
public sealed record Port(string Id, double T);

// Cadre de bulle (cosmétique) : couleur et épaisseur du bord, arrondi ; Fond / Sombre imposent un fond sombre.
public sealed record StyleBulle(string Bord, int Epaisseur, int Rayon, string? Fond = null, bool Sombre = false);

public static class Boutique
{
    public const string Tete = "tete", Yeux = "yeux", Cou = "cou", Dos = "dos", Main = "main", Pieds = "pieds", Compagnon = "compagnon",
        Effet = "effet", Couleur = "couleur", Fond = "fond", Bulle = "bulle", Titre = "titre";
    // Emplacements qui se portent (Bourse.Equipe) ; « accessoire » (le chapeau historique, porté via les réglages),
    // « bonus » (actif dès qu'il est possédé) et « consommable » (s'achète plusieurs fois) sont à part.
    // « titre » : le titre affiché sous le nom de Pilou (bandeau), à la place du titre de niveau.
    public static readonly string[] Slots = { Tete, Yeux, Cou, Dos, Main, Pieds, Compagnon, Effet, Couleur, Fond, Bulle, Titre };
    public const string Accessoire = "accessoire", Bonus = "bonus", Consommable = "consommable", Speciaux = "speciaux";
    // Rayons de la boutique, dans l'ordre d'affichage ; « Spéciaux » réunit accessoires, bonus et consommables.
    // « Ensembles » est un rayon transversal : les pièces des ensembles thématiques, tous emplacements confondus.
    public const string RayonEnsembles = "ensembles";
    public static readonly string[] Rayons = { RayonEnsembles, Tete, Yeux, Cou, Dos, Main, Pieds, Compagnon, Effet, Couleur, Fond, Bulle, Titre, Speciaux };
    // Paliers de niveau : chacun ouvre une rangée dans les rayons qui en ont une.
    public static readonly int[] Paliers = { 1, 5, 10, 15, 20, 30, 40, 50 };
    public const string TraineeEtoiles = "trainee-etoiles", CanneDoree = "canne-doree", MarmiteCuivre = "marmite-cuivre", PierreCalme = "pierre-calme";

    // Plus haut palier atteint au niveau n (1 au minimum).
    public static int Palier(int niveau) => Paliers.LastOrDefault(p => p <= niveau, 1);

    // Prochain palier après le niveau n (0 : tout est ouvert).
    public static int ProchainPalier(int niveau) => Paliers.FirstOrDefault(p => p > niveau);

    public static string RayonDe(string slot) => slot is Accessoire or Bonus or Consommable ? Speciaux : slot;

    public static bool Ouvert(Article a, int niveau) => niveau >= a.NiveauMin;

    // Rangées d'un rayon : (palier, articles), paliers sans article omis.
    public static IReadOnlyList<(int Palier, List<Article> Articles)> Rangees(string rayon) =>
        Paliers.Select(p => (p, Catalogue.Where(a => DansRayon(a, rayon) && a.NiveauMin == p).ToList()))
            .Where(r => r.Item2.Count > 0).ToList();

    // Pièce d'un ensemble (y compris les décors d'origine repris dans un ensemble).
    public static bool EstPiece(Article a) => Ensembles.Any(e => e.Pieces.Contains(a.Id));

    public static bool DansRayon(Article a, string rayon) => rayon == RayonEnsembles ? EstPiece(a) : RayonDe(a.Slot) == rayon;

    // Articles des rangées ouvertes entre deux niveaux (avant exclu, après inclus) : les « nouveautés ».
    public static IReadOnlyList<Article> Debloques(int avant, int apres) =>
        Catalogue.Where(a => a.NiveauMin > avant && a.NiveauMin <= apres).ToList();

    // Rayons qui gagnent une rangée à ce palier (« Prochaine rangée : Dos, Main — niveau 15 »).
    public static IReadOnlyList<string> RayonsDuPalier(int palier) =>
        Rayons.Where(r => r != RayonEnsembles && Catalogue.Any(a => RayonDe(a.Slot) == r && a.NiveauMin == palier)).ToList();

    // Anciennes récompenses de niveau, devenues articles (rangée = palier de l'ancien niveau ; prix selon ce niveau).
    private static IEnumerable<Article> Anciens()
    {
        foreach (var a in new[] { PilouBureau.Accessoire.Feuille, PilouBureau.Accessoire.Noeud, PilouBureau.Accessoire.Casque,
                     PilouBureau.Accessoire.Bonnet, PilouBureau.Accessoire.Lunettes, PilouBureau.Accessoire.Couronne,
                     PilouBureau.Accessoire.ChapeauPeche, PilouBureau.Accessoire.Toque, PilouBureau.Accessoire.Tablier,
                     PilouBureau.Accessoire.EtoileMer })
        {
            int n = Recompenses.Ancien(a);
            yield return new Article(Recompenses.IdAccessoire(a), Nom(a), Accessoire, Math.Min(600, 60 + 15 * n), Palier(n), Rang(n), true);
        }
        foreach (var c in Enum.GetValues<PilouBureau.Couleur>().Where(c => c != PilouBureau.Couleur.Bleu))
        {
            int n = Recompenses.Ancien(c);
            yield return new Article(Recompenses.IdCouleur(c), "Couleur " + Recompenses.NomCouleur(c).ToLowerInvariant(), Couleur,
                Math.Min(600, 100 + 10 * n), Palier(n), Rang(n), true);
        }
        yield return new Article(TraineeEtoiles, "Traînée d'étoiles", Effet, 220, 5, Rarete.Rare, true);
        yield return new Article(CanneDoree, "Canne dorée (plus de prises légendaires)", Bonus, 500, 30, Rarete.Legendaire, true);
        yield return new Article(MarmiteCuivre, "Marmite en cuivre (moins de plats brûlés)", Bonus, 520, 30, Rarete.Legendaire, true);
        yield return new Article(PierreCalme, "Pierre de calme (retient une évolution)", Consommable, 150, 5, Rarete.PeuCommun, true);
        // En-cas (soins) : Pilou mange d'abord le meilleur ; sans en-cas, il a toujours des croquettes gratuites.
        yield return new Article("pomme", "Pomme dorée (+ moral)", Consommable, 60, 1, Rarete.Commun, true);
        yield return new Article("soupe", "Soupe chaude (+ moral)", Consommable, 80, 1, Rarete.PeuCommun, true);
        yield return new Article("gateau", "Gâteau (+ moral)", Consommable, 120, 1, Rarete.PeuCommun, true);
        // En-cas de route (expéditions) : ils rendent de l'énergie ⚡ (Jauge.Repas), jamais de quoi gagner des po.
        yield return new Article("galette-route", "Galette de route (+15 ⚡)", Consommable, 60, 1, Rarete.Commun, true);
        yield return new Article("jus-etoile", "Jus d'étoile (+30 ⚡)", Consommable, 110, 5, Rarete.PeuCommun, true);
    }

    private static Rarete Rang(int niveau) => niveau switch
    {
        <= 3 => Rarete.Commun, <= 8 => Rarete.PeuCommun, <= 15 => Rarete.Rare, <= 30 => Rarete.Epique, _ => Rarete.Legendaire,
    };

    private static string Nom(PilouBureau.Accessoire a) => a switch
    {
        PilouBureau.Accessoire.Feuille => "Feuille d'automne",
        PilouBureau.Accessoire.Noeud => "Nœud papillon",
        PilouBureau.Accessoire.Casque => "Casque audio",
        PilouBureau.Accessoire.Bonnet => "Bonnet de laine",
        PilouBureau.Accessoire.Lunettes => "Lunettes de soleil",
        PilouBureau.Accessoire.Couronne => "Couronne",
        PilouBureau.Accessoire.ChapeauPeche => "Chapeau de pêcheur",
        PilouBureau.Accessoire.Toque => "Toque de chef",
        PilouBureau.Accessoire.Tablier => "Tablier",
        PilouBureau.Accessoire.EtoileMer => "Étoile de mer",
        _ => a.ToString(),
    };

    // ---- Boutique garnie : assets/catalogue.txt (ressource « pilou:catalogue.txt »), même fichier que l'app Android.

    private sealed record Garniture(List<Article> Articles, List<Ensemble> Ensembles, List<PalierCollection> Paliers);

    private static readonly Garniture Garnie = LireGarniture(TexteRessource("catalogue.txt"));

    private static string TexteRessource(string nom)
    {
        using var flux = typeof(Boutique).Assembly.GetManifestResourceStream("pilou:" + nom);
        if (flux is null) return "";
        using var r = new System.IO.StreamReader(flux);
        return r.ReadToEnd();
    }

    // article|n°|id|nom|emplacement|prix|niveau|rareté|saison|ensemble|passage ; ensemble|id|nom|signe|bonus|titre|pièces… ;
    // palier|nombre|id|emplacement|nom. Une ligne mal formée est ignorée (rien ne plante).
    private static Garniture LireGarniture(string texte)
    {
        var g = new Garniture(new(), new(), new());
        foreach (var brut in texte.Replace("\r", "").Split('\n'))
        {
            if (brut.StartsWith('#') || brut.Length == 0) continue;
            var c = brut.Split('|');
            static int N(string s) => int.TryParse(s, System.Globalization.NumberStyles.Integer, System.Globalization.CultureInfo.InvariantCulture, out var n) ? n : -1;
            if (c[0] == "article" && c.Length == 11 && N(c[1]) > 0 && N(c[5]) >= 0 && N(c[6]) >= 1 && N(c[7]) is >= 0 and <= 5)
                g.Articles.Add(new Article(c[2], c[3], c[4], N(c[5]), N(c[6]), (Rarete)N(c[7]))
                    { Numero = N(c[1]), Saison = c[8], Ensemble = c[9], Passage = c[10] == "1" });
            else if (c[0] == "ensemble" && c.Length >= 8)
                g.Ensembles.Add(new Ensemble(c[1], c[2], c[3], c[4], c[5], c[6..]));
            else if (c[0] == "palier" && c.Length == 5 && N(c[1]) >= 0)
                g.Paliers.Add(new PalierCollection(N(c[1]), c[2], c[3], c[4]));
        }
        return g;
    }

    // Catalogue commun avec l'app Android (Boutique.java) : mêmes identifiants, prix et paliers ; puis les anciennes
    // récompenses, puis la boutique garnie (dans l'ordre du fichier). L'ordre compte : la vitrine tire dedans.
    public static readonly IReadOnlyList<Article> Catalogue = new Article[]
    {
        // Tête
        new("casquette", "Casquette", Tete, 80, 1, Rarete.Commun, true),
        new("beret", "Béret", Tete, 90, 1, Rarete.Commun),
        new("bonnet-pompon", "Bonnet à pompon", Tete, 110, 1, Rarete.Commun),
        new("bandeau-ninja", "Bandeau de ninja", Tete, 120, 1, Rarete.PeuCommun),
        new("couronne-fleurs", "Couronne de fleurs", Tete, 180, 5, Rarete.PeuCommun),
        new("casque-chantier", "Casque de chantier", Tete, 180, 5, Rarete.PeuCommun),
        new("chapeau-pirate", "Chapeau de pirate", Tete, 220, 5, Rarete.Rare),
        new("haut-de-forme", "Haut-de-forme", Tete, 260, 5, Rarete.Rare),
        new("sombrero", "Sombrero", Tete, 280, 10, Rarete.Rare),
        new("chapeau-cowboy", "Chapeau de cowboy", Tete, 300, 10, Rarete.Rare),
        new("cornes-viking", "Casque à cornes", Tete, 320, 10, Rarete.Epique),
        new("chapeau-sorcier", "Chapeau de sorcier", Tete, 380, 10, Rarete.Epique),
        new("oreilles-chat", "Oreilles de chat", Tete, 360, 15, Rarete.Rare),
        new("aureole", "Auréole", Tete, 450, 15, Rarete.Legendaire),
        new("couronne-laurier", "Couronne de laurier", Tete, 520, 20, Rarete.Epique),
        new("antenne-neon", "Antennes néon", Tete, 1000, 40, Rarete.Legendaire),
        // Yeux
        new("lunettes-rondes", "Lunettes rondes", Yeux, 90, 1, Rarete.Commun, true),
        new("masque-plongee", "Masque de plongée", Yeux, 160, 1, Rarete.PeuCommun),
        new("lunettes-3d", "Lunettes 3D", Yeux, 160, 5, Rarete.PeuCommun),
        new("monocle", "Monocle", Yeux, 200, 5, Rarete.Rare),
        new("visiere-pilote", "Visière de pilote", Yeux, 380, 15, Rarete.Rare),
        new("lunettes-coeur", "Lunettes cœur", Yeux, 450, 20, Rarete.Epique),
        // Cou
        new("echarpe", "Écharpe", Cou, 70, 1, Rarete.Commun, true),
        new("bandana", "Bandana", Cou, 80, 1, Rarete.Commun),
        new("noeud-pois", "Nœud à pois", Cou, 150, 5, Rarete.PeuCommun),
        new("medaille", "Médaille", Cou, 300, 5, Rarete.Epique),
        new("cravate", "Cravate", Cou, 240, 10, Rarete.Rare),
        new("collier-perles", "Collier de perles", Cou, 750, 30, Rarete.Epique),
        // Dos (l'imperméable protège aussi de la pluie)
        new("impermeable", "Imperméable", Dos, 180, 1, Rarete.PeuCommun),
        new("sac-a-dos", "Sac à dos", Dos, 170, 5, Rarete.PeuCommun),
        new("cape", "Cape", Dos, 280, 5, Rarete.Rare),
        new("carapace", "Carapace", Dos, 420, 15, Rarete.Rare),
        new("ailes-papillon", "Ailes de papillon", Dos, 900, 30, Rarete.Epique),
        new("jetpack", "Jetpack", Dos, 1500, 50, Rarete.Legendaire),
        // Main (parapluie, moufles, éventail : contre la pluie, le froid, la chaleur — Meteo)
        new("tasse-cafe", "Tasse de café", Main, 60, 1, Rarete.Commun, true),
        new("sucette", "Sucette", Main, 70, 1, Rarete.Commun),
        new("moufles", "Moufles", Main, 80, 1, Rarete.Commun),
        new("eventail", "Éventail", Main, 100, 1, Rarete.PeuCommun),
        new("parapluie", "Parapluie", Main, 110, 1, Rarete.PeuCommun),
        new("ballon-helium", "Ballon", Main, 130, 1, Rarete.PeuCommun),
        new("epee-mousse", "Épée en mousse", Main, 190, 5, Rarete.PeuCommun),
        new("lanterne", "Lanterne", Main, 260, 10, Rarete.Rare),
        new("baguette", "Baguette magique", Main, 340, 10, Rarete.Epique),
        new("parapluie-etoile", "Parapluie étoilé", Main, 420, 10, Rarete.Epique),
        new("guitare", "Guitare", Main, 560, 20, Rarete.Epique),
        new("canne-or", "Canne à pêche dorée", Main, 820, 30, Rarete.Legendaire),
        // Pieds
        new("bottes-pluie", "Bottes de pluie", Pieds, 90, 1, Rarete.Commun),
        new("baskets", "Baskets", Pieds, 100, 1, Rarete.Commun),
        new("palmes", "Palmes", Pieds, 230, 10, Rarete.Rare),
        new("patins", "Patins", Pieds, 480, 20, Rarete.Epique),
        // Compagnons
        new("petit-poisson-bocal", "Poisson en bocal", Compagnon, 240, 5, Rarete.Rare),
        new("oiseau", "Oiseau", Compagnon, 450, 10, Rarete.Rare),
        new("petit-chat", "Petit chat", Compagnon, 520, 10, Rarete.Legendaire),
        new("petit-robot", "Petit robot", Compagnon, 700, 20, Rarete.Epique),
        new("fantome", "Fantôme", Compagnon, 900, 30, Rarete.Epique),
        new("mini-dragon", "Mini-dragon", Compagnon, 1300, 40, Rarete.Legendaire),
        // Effets
        new("bulles-savon", "Bulles de savon", Effet, 260, 5, Rarete.PeuCommun),
        new("trainee-coeurs", "Traînée de cœurs", Effet, 300, 5, Rarete.Rare),
        new("trainee-notes", "Traînée de notes", Effet, 340, 5, Rarete.Epique),
        new("confettis", "Confettis", Effet, 420, 15, Rarete.Rare),
        new("aura", "Aura", Effet, 600, 15, Rarete.Legendaire),
        new("trainee-prisme", "Arc prisme", Effet, 950, 30, Rarete.Epique),
        new("aura-feu", "Aura de feu", Effet, 1500, 50, Rarete.Legendaire),
        // Couleurs (teintes de Pilou)
        new("sable", "Couleur sable", Couleur, 150, 1, Rarete.Commun, true),
        new("ardoise", "Couleur ardoise", Couleur, 150, 1, Rarete.Commun, true),
        new("lavande", "Couleur lavande", Couleur, 200, 1, Rarete.PeuCommun),
        new("glacier", "Couleur glacier", Couleur, 220, 5, Rarete.Rare),
        new("pervenche", "Couleur pervenche", Couleur, 220, 5, Rarete.PeuCommun),
        new("corail-orange", "Couleur corail", Couleur, 250, 5, Rarete.Rare),
        new("mandarine", "Couleur mandarine", Couleur, 300, 10, Rarete.Rare),
        new("miel", "Couleur miel", Couleur, 380, 15, Rarete.Rare),
        new("prune", "Couleur prune", Couleur, 450, 20, Rarete.Epique),
        new("acier", "Couleur acier", Couleur, 600, 30, Rarete.Epique),
        new("peche", "Couleur pêche", Couleur, 800, 40, Rarete.Legendaire),
        // Décors : derrière Pilou (téléphone, aperçu de la boutique)
        new("fond-nuit", "Décor nuit étoilée", Fond, 120, 1, Rarete.Commun),
        new("fond-foret", "Décor forêt bleutée", Fond, 250, 5, Rarete.PeuCommun),
        new("fond-plage", "Décor plage", Fond, 350, 10, Rarete.Rare),
        new("fond-arcade", "Décor salle d'arcade", Fond, 600, 20, Rarete.Epique),
        new("fond-espace", "Décor espace", Fond, 900, 30, Rarete.Legendaire),
        // Cadres de bulle
        new("bulle-doree", "Bulle dorée", Bulle, 200, 5, Rarete.PeuCommun),
        new("bulle-nuit", "Bulle de nuit", Bulle, 260, 10, Rarete.Rare),
        new("bulle-pixel", "Bulle pixel", Bulle, 320, 15, Rarete.Rare),
        new("bulle-nuages", "Bulle nuage", Bulle, 400, 20, Rarete.Epique),
    }.Concat(Anciens()).Concat(Garnie.Articles).ToList();

    private static readonly Dictionary<string, Article> ParId = Catalogue.GroupBy(a => a.Id).ToDictionary(g => g.Key, g => g.First());

    // Le butin des expéditions (Expeditions.Exclusifs) et les objets gagnés en campagne (Campagnes.Exclusifs) se
    // portent comme un article, mais ne se vendent pas.
    public static Article? Trouver(string id) => ParId.GetValueOrDefault(id) ?? Expeditions.Exclusif(id) ?? Campagnes.Exclusif(id);

    public static IReadOnlyList<Ensemble> Ensembles => Garnie.Ensembles;
    public static IReadOnlyList<PalierCollection> PaliersCollection => Garnie.Paliers;

    // Récompenses (titres d'ensemble, titres et cadres de collection) : des articles qui ne s'achètent pas.
    public static readonly IReadOnlyList<Article> Trophees = Garnie.Ensembles
        .Select(e => new Article(e.IdTitre, e.Titre, Titre, 0, 1, Rarete.Epique) { Ensemble = e.Id, Recompense = true })
        .Concat(Garnie.Paliers.Select(p => new Article(p.Id, p.Nom, p.Slot, 0, 1, p.Nombre == 0 ? Rarete.Mythique
            : p.Nombre >= 120 ? Rarete.Legendaire : p.Nombre >= 50 ? Rarete.Epique : Rarete.Rare) { Recompense = true }))
        .ToList();

    // Article du catalogue ou récompense.
    public static Article? TrouverTout(string id) => Trouver(id) ?? Trophees.FirstOrDefault(a => a.Id == id);

    public static StyleBulle? Style(string id) => id switch
    {
        "bulle-doree" => new StyleBulle("#c9a227", 4, 0),
        "bulle-nuit" => new StyleBulle("#6cb6ff", 3, 0, "#16365e", true),
        "bulle-pixel" => new StyleBulle("#f69d50", 5, 0),
        "bulle-nuages" => new StyleBulle("#9b8cff", 3, 12),
        "bulle-bois" => new StyleBulle("#a86f3c", 4, 2, "#f3e2c4"),
        "bulle-lagon" => new StyleBulle("#3fb8e0", 3, 6),
        "bulle-parchemin" => new StyleBulle("#8a6e4b", 3, 1, "#f6ead0"),
        "bulle-givre" => new StyleBulle("#b4dbff", 4, 10, "#eaf6ff"),
        "bulle-guirlande" => new StyleBulle("#f69d50", 5, 6, "#16365e", true),
        "bulle-ronde" => new StyleBulle("#6cb6ff", 3, 18),
        "bulle-encre" => new StyleBulle("#9b8cff", 3, 4, "#1c2128", true),
        "bulle-ambre" => new StyleBulle("#f2a94e", 4, 3, "#3a2410", true),
        "bulle-cristal" => new StyleBulle("#d2caff", 5, 14, "#f4f1ff"),
        "cadre-bronze" => new StyleBulle("#c4783a", 4, 2),
        "cadre-argent" => new StyleBulle("#b8c4d2", 5, 3),
        "cadre-or" => new StyleBulle("#f5d76e", 5, 4, "#fff9e0"),
        "cadre-prisme" => new StyleBulle("#9b8cff", 6, 8, "#0d2a4d", true),
        _ => null,
    };

    // Signe de l'emplacement (pas de couleur seule : un signe de forme, toujours).
    public static string Signe(string slot) => slot switch
    {
        Tete => "▲", Yeux => "◉", Cou => "◡", Dos => "▼", Main => "✚", Pieds => "▬", Compagnon => "♣", Effet => "✧", Couleur => "■",
        Fond => "▧", Bulle => "❝", Titre => "❞", RayonEnsembles => "❖", Accessoire => "◆", Bonus => "★", Consommable => "◇", Speciaux => "★", _ => "·",
    };

    public static string NomSlot(string slot) => slot switch
    {
        Tete => "Tête", Yeux => "Yeux", Cou => "Cou", Dos => "Dos", Main => "Main", Pieds => "Pieds", Compagnon => "Compagnons", Effet => "Effets",
        Couleur => "Couleurs", Fond => "Décors", Bulle => "Bulles", Titre => "Titres", RayonEnsembles => "Ensembles", Accessoire => "Accessoires", Bonus => "Bonus",
        Consommable => "Consommables", Speciaux => "Spéciaux", _ => slot,
    };

    // ---- Raretés : un signe de forme et une couleur (jamais rouge / vert), de commun à mythique.

    public static string SigneRarete(Rarete r) => r switch
    {
        Rarete.Commun => "·", Rarete.PeuCommun => "◇", Rarete.Rare => "◆", Rarete.Epique => "✦", Rarete.Legendaire => "★", _ => "✺",
    };

    public static string NomRarete(Rarete r) => r == Rarete.Mythique ? "mythique" : Butin.NomRarete(r);

    // Argent, bleu, violet, orange, or, crème irisé.
    public static string CouleurRarete(Rarete r) => r switch
    {
        Rarete.Commun => "#adbac7", Rarete.PeuCommun => "#6cb6ff", Rarete.Rare => "#9b8cff", Rarete.Epique => "#f69d50",
        Rarete.Legendaire => "#f5d76e", _ => "#fff6cc",
    };

    // ---- Saisons (articles saisonniers) : visibles toute l'année, achetables pendant leur saison.

    public static readonly string[] Saisons = { "hiver", "printemps", "ete", "automne", "frissons", "fetes" };

    public static bool EnSaison(string saison, DateOnly j) => saison switch
    {
        "" => true,
        "hiver" => j.Month is 12 or 1 or 2,
        "printemps" => j.Month is 3 or 4 or 5,
        "ete" => j.Month is 6 or 7 or 8,
        "automne" => j.Month is 9 or 10 or 11,
        "frissons" => (j.Month == 10 && j.Day >= 15) || (j.Month == 11 && j.Day <= 5),
        "fetes" => (j.Month == 12 && j.Day >= 10) || (j.Month == 1 && j.Day <= 6),
        _ => false,
    };

    public static string NomSaison(string saison) => saison switch
    {
        "hiver" => "hiver", "printemps" => "printemps", "ete" => "été", "automne" => "automne", "frissons" => "Nuit des frissons",
        "fetes" => "Fêtes de l'hiver", _ => saison,
    };

    // Jours restants (aujourd'hui compris) avant la fin de la saison ; 0 hors saison.
    public static int JoursRestants(string saison, DateOnly j)
    {
        int n = 0;
        while (n < 370 && EnSaison(saison, j.AddDays(n))) n++;
        return saison == "" ? 0 : n;
    }

    // Premier jour de la prochaine saison (après j), ou null.
    public static DateOnly? Retour(string saison, DateOnly j)
    {
        for (int i = 1; i <= 370; i++)
            if (EnSaison(saison, j.AddDays(i)) && !EnSaison(saison, j.AddDays(i - 1))) return j.AddDays(i);
        return null;
    }

    // ---- Articles de passage : trois jours par mois en vitrine, tirés de l'identifiant et du mois (comme le téléphone).

    public const int JoursPassage = 3;

    private static int DebutPassage(string id, DateOnly j) =>
        1 + new Hasard(Hasard.Graine($"passage|{id}|{j.Year:D4}-{j.Month:D2}")).Suivant(26);

    public static bool DePassage(Article a, DateOnly j) => a.Passage && j.Day >= DebutPassage(a.Id, j) && j.Day < DebutPassage(a.Id, j) + JoursPassage;

    // Jours de passage restants (aujourd'hui compris) ; 0 s'il n'est pas en vitrine.
    public static int PassageRestant(Article a, DateOnly j) => DePassage(a, j) ? DebutPassage(a.Id, j) + JoursPassage - j.Day : 0;

    public static DateOnly? ProchainPassage(Article a, DateOnly j)
    {
        if (!a.Passage) return null;
        for (int i = 1; i <= 62; i++)
            if (DePassage(a, j.AddDays(i))) return j.AddDays(i);
        return null;
    }

    // Les articles de passage en vitrine ce jour-là (ordre du catalogue).
    public static IReadOnlyList<Article> Passages(DateOnly j) => Catalogue.Where(a => DePassage(a, j)).ToList();

    // Achetable ce jour-là (saison, passage) ; le niveau et les po se vérifient à part.
    public static bool Disponible(Article a, DateOnly j) => !a.Recompense && EnSaison(a.Saison, j) && (!a.Passage || DePassage(a, j));

    // ---- Collection : tous les articles sauf les consommables ; ses paliers donnent titres et cadres (pas de po).

    public static bool Collectionnable(Article a) => a.Slot != Consommable && !a.Recompense;

    public static int TotalCollection { get; } = Catalogue.Count(Collectionnable);

    public static int Collection(IEnumerable<string> inventaire) =>
        inventaire.Distinct().Count(id => ParId.TryGetValue(id, out var a) && Collectionnable(a));

    public static int Seuil(PalierCollection p) => p.Nombre <= 0 ? TotalCollection : p.Nombre;

    public static PalierCollection? ProchainPalierCollection(int possedes) =>
        PaliersCollection.Where(p => Seuil(p) > possedes).OrderBy(Seuil).FirstOrDefault();

    public static int Possedes(Ensemble e, IReadOnlyCollection<string> inventaire) => e.Pieces.Count(inventaire.Contains);

    public static bool Complet(Ensemble e, IReadOnlyCollection<string> inventaire) => e.Pieces.All(inventaire.Contains);

    // Porté en entier : chaque pièce est à son emplacement.
    public static bool PorteEnEntier(Ensemble e, IReadOnlyDictionary<string, string> porte) =>
        e.Pieces.All(p => Trouver(p) is { } a && porte.GetValueOrDefault(a.Slot) == p);

    // Effets des ensembles portés en entier, à ajouter aux objets dessinés sur Pilou.
    public static IEnumerable<string> BonusPortes(IReadOnlyDictionary<string, string> porte) =>
        Ensembles.Where(e => PorteEnEntier(e, porte)).Select(e => e.Bonus);

    // Récompenses gagnées (titres d'ensemble complets, paliers de collection atteints).
    public static IReadOnlyList<string> Gagnees(IReadOnlyCollection<string> inventaire)
    {
        int n = Collection(inventaire);
        return Ensembles.Where(e => Complet(e, inventaire)).Select(e => e.IdTitre)
            .Concat(PaliersCollection.Where(p => n >= Seuil(p)).Select(p => p.Id)).ToList();
    }

    public static Ensemble? EnsembleDe(string id) => Ensembles.FirstOrDefault(e => e.Id == id);

    // Nom du titre porté (article titre ou récompense) ; null si aucun.
    public static string? NomTitre(string? id) => id is { Length: > 0 } && TrouverTout(id) is { Slot: Titre } a ? a.Nom : null;

    // ---- Synchronisation compacte : les articles numérotés partent en bits (base64url), les autres en identifiants.

    public static string Garde(IEnumerable<string> inventaire)
    {
        var nums = inventaire.Select(id => Trouver(id)?.Numero ?? 0).Where(n => n > 0).ToList();
        if (nums.Count == 0) return "";
        var octets = new byte[(nums.Max() + 7) / 8];
        foreach (var n in nums) octets[(n - 1) / 8] |= (byte)(1 << ((n - 1) % 8));
        return Convert.ToBase64String(octets).TrimEnd('=').Replace('+', '-').Replace('/', '_');
    }

    // Les objets gagnés en campagne ne voyagent pas dans ces messages (déjà près de la limite de taille) : chaque
    // appareil les déduit de l'historique des campagnes, qui a son propre message.
    public static List<string> HorsGarde(IEnumerable<string> inventaire) =>
        inventaire.Where(id => (Trouver(id)?.Numero ?? 0) == 0 && (ParId.ContainsKey(id) || !Campagnes.EstExclusif(id))).ToList();

    public static List<string> Deplier(string? garde)
    {
        var r = new List<string>();
        if (string.IsNullOrEmpty(garde) || garde.Length > 400) return r;
        try
        {
            var b64 = garde.Replace('-', '+').Replace('_', '/');
            var octets = Convert.FromBase64String(b64 + new string('=', (4 - b64.Length % 4) % 4));
            var parNumero = Garnie.Articles.ToDictionary(a => a.Numero, a => a.Id);
            for (int i = 0; i < octets.Length * 8; i++)
                if ((octets[i / 8] >> (i % 8) & 1) != 0 && parNumero.TryGetValue(i + 1, out var id)) r.Add(id);
        }
        catch (FormatException)
        {
            // garde illisible : ignorée
        }
        return r;
    }

    // ---- Offres du jour (vitrine) : 4 objets non permanents, tirés de la date ; le premier à -25 %.
    // Offre météo : quand il pleut (Meteo.Courante), le parapluie s'invite dans les offres s'il n'y est pas.

    public static Func<bool> Pluie = () => Meteo.Courante is { } m && Meteo.Pluvieux(m.Etat);

    public static IReadOnlyList<Article> OffresDuJour(DateOnly jour)
    {
        var offres = OffresTirees(jour).ToList();
        if (Pluie() && offres.All(o => o.Id != "parapluie") && Trouver("parapluie") is { } p)
        {
            if (offres.Count >= 4) offres.RemoveAt(offres.Count - 1);
            offres.Add(p);
        }
        return offres;
    }

    private static IReadOnlyList<Article> OffresTirees(DateOnly jour)
    {
        var tirage = new Hasard(Hasard.Graine($"boutique|{jour:yyyy-MM-dd}"));
        // Pas les articles de passage (ils ont leur propre étagère) ni ceux hors saison.
        var pool = Catalogue.Where(a => !a.Permanent && !a.Passage && EnSaison(a.Saison, jour)).ToList();
        var offres = new List<Article>();
        while (offres.Count < 4 && pool.Count > 0)
        {
            int i = tirage.Suivant(pool.Count);
            offres.Add(pool[i]);
            pool.RemoveAt(i);
        }
        return offres;
    }

    public static int Prix(Article a, DateOnly jour)
    {
        var offres = OffresDuJour(jour);
        return offres.Count > 0 && offres[0].Id == a.Id ? a.Prix * 3 / 4 : a.Prix;
    }

    // Achat : null si fait, sinon la raison du refus. La rangée doit être ouverte (niveau) ; le solde ne devient jamais négatif.
    public static string? Acheter(Bourse b, string id, int niveau, int solde, DateOnly jour, bool parTelephone = false)
    {
        var a = Trouver(id);
        if (a is null) return "objet inconnu";
        if (Expeditions.EstExclusif(id)) return "introuvable en boutique : butin d'expédition";
        if (!ParId.ContainsKey(id) && Campagnes.EstExclusif(id)) return "introuvable en boutique : récompense de campagne";
        bool consommable = a.Slot == Consommable;
        if (!consommable && b.Inventaire.Contains(id)) return "déjà dans l'inventaire";
        if (!Ouvert(a, niveau)) return $"niveau {a.NiveauMin} requis";
        if (a.Saison != "" && !EnSaison(a.Saison, jour)) return $"hors saison (revient : {NomSaison(a.Saison)})";
        if (a.Passage && !DePassage(a, jour)) return "seulement quand il passe en vitrine";
        int prix = Prix(a, jour);
        if (solde < prix) return $"il manque {prix - solde} po";
        if (parTelephone) b.PoDepTelephone += prix;
        else b.PoDepenses += prix;
        if (consommable) b.Consommables[id] = b.Consommables.GetValueOrDefault(id) + 1;
        else b.Inventaire.Add(id);
        return null;
    }

    // Équiper (ou retirer, id vide) : seulement un objet possédé ; horodaté pour la fusion entre appareils.
    public static bool Equiper(Bourse b, string slot, string id, double t)
    {
        if (!Slots.Contains(slot)) return false;
        if (id != "" && !PeutPorter(b.Inventaire, slot, id)) return false;
        b.Equipe[slot] = new Port(id, t);
        return true;
    }

    // Possédé (ou récompense gagnée) et à cet emplacement.
    public static bool PeutPorter(IReadOnlyCollection<string> inventaire, string slot, string id) =>
        TrouverTout(id) is { } a && a.Slot == slot && (a.Recompense ? Gagnees(inventaire).Contains(id) : inventaire.Contains(id));

    // Ce qui est réellement porté : slot → id (les emplacements vides sont omis).
    public static Dictionary<string, string> Porte(IReadOnlyDictionary<string, Port> equipe) =>
        equipe.Where(kv => kv.Value.Id != "").ToDictionary(kv => kv.Key, kv => kv.Value.Id);

    // Ce qui se dessine sur Pilou lui-même (ni la couleur, ni le décor, ni le cadre de bulle).
    public static bool SurPilou(string slot) => slot is not (Couleur or Fond or Bulle or Titre);
}

// Pièces d'or, inventaire et équipement d'un appareil. Compteur G : chaque appareil ne fait que monter
// ses gains et ses dépenses ; le solde du groupe = Σ gains − Σ dépenses (− dépenses du téléphone, comptées
// au maximum : chaque PC du groupe applique les mêmes achats faits sur le téléphone).
public sealed class Bourse
{
    public int PoGagnes { get; set; }
    public int PoDepenses { get; set; }
    public int PoDepTelephone { get; set; }
    // Po gagnées en campagne (Campagnes.Crediter) : chaque PC du groupe verse les mêmes, comptées au maximum.
    public int PoCampagnes { get; set; }
    public List<string> Inventaire { get; set; } = new();
    // Consommables achetés et pas encore utilisés (pierre de calme…), propres à cet appareil.
    public Dictionary<string, int> Consommables { get; set; } = new();
    public Dictionary<string, Port> Equipe { get; set; } = new();

    // Fusion d'un autre appareil : union des objets, dernière écriture gagne par emplacement.
    public static Dictionary<string, Port> FusionEquipe(IEnumerable<IReadOnlyDictionary<string, Port>> toutes)
    {
        var r = new Dictionary<string, Port>();
        foreach (var e in toutes)
            foreach (var (slot, port) in e)
                if (!r.TryGetValue(slot, out var avant) || port.T > avant.T) r[slot] = port;
        return r;
    }
}

// Tirage déterministe (même graine → même suite, sur toutes les versions de .NET) : xorshift64*.
public sealed class Hasard
{
    private ulong _s;

    public Hasard(ulong graine) => _s = graine == 0 ? 0x9E3779B97F4A7C15UL : graine;

    // FNV-1a 64 bits : une chaîne → une graine stable (string.GetHashCode change à chaque lancement).
    public static ulong Graine(string s)
    {
        ulong h = 14695981039346656037UL;
        foreach (char c in s)
        {
            h ^= c;
            h *= 1099511628211UL;
        }
        return h;
    }

    public ulong Brut()
    {
        _s ^= _s >> 12;
        _s ^= _s << 25;
        _s ^= _s >> 27;
        return _s * 2685821657736338717UL;
    }

    public int Suivant(int max) => max <= 1 ? 0 : (int)(Brut() % (ulong)max);

    public int Entre(int min, int max) => min >= max ? min : min + Suivant(max - min + 1);
}
