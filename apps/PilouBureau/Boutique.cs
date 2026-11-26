namespace PilouBureau;

// Boutique de Pilou : gratuite, virtuelle. On y dépense des pièces d'or (« po ») gagnées en quêtes ;
// aucune vraie monnaie, aucun achat réel. Rayons par emplacement (Tête, Yeux, Cou…) ; dans chaque rayon,
// des rangées par palier de niveau (1, 5, 10, 15, 20, 30, 40, 50) : le niveau ouvre la rangée, les po
// achètent l'objet. Les offres du jour sont une vitrine (la première à -25 %). Dessins : assets/sprites.
public sealed record Article(string Id, string Nom, string Slot, int Prix, int NiveauMin, Rarete Rarete, bool Permanent = false);

// Ce que Pilou porte : un objet par emplacement, horodaté (entre appareils, la dernière écriture gagne).
public sealed record Port(string Id, double T);

// Cadre de bulle (cosmétique) : couleur et épaisseur du bord, arrondi ; Fond / Sombre imposent un fond sombre.
public sealed record StyleBulle(string Bord, int Epaisseur, int Rayon, string? Fond = null, bool Sombre = false);

public static class Boutique
{
    public const string Tete = "tete", Yeux = "yeux", Cou = "cou", Dos = "dos", Main = "main", Pieds = "pieds", Compagnon = "compagnon",
        Effet = "effet", Couleur = "couleur", Fond = "fond", Bulle = "bulle";
    // Emplacements qui se portent (Bourse.Equipe) ; « accessoire » (le chapeau historique, porté via les réglages),
    // « bonus » (actif dès qu'il est possédé) et « consommable » (s'achète plusieurs fois) sont à part.
    public static readonly string[] Slots = { Tete, Yeux, Cou, Dos, Main, Pieds, Compagnon, Effet, Couleur, Fond, Bulle };
    public const string Accessoire = "accessoire", Bonus = "bonus", Consommable = "consommable", Speciaux = "speciaux";
    // Rayons de la boutique, dans l'ordre d'affichage ; « Spéciaux » réunit accessoires, bonus et consommables.
    public static readonly string[] Rayons = { Tete, Yeux, Cou, Dos, Main, Pieds, Compagnon, Effet, Couleur, Fond, Bulle, Speciaux };
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
        Paliers.Select(p => (p, Catalogue.Where(a => RayonDe(a.Slot) == rayon && a.NiveauMin == p).ToList()))
            .Where(r => r.Item2.Count > 0).ToList();

    // Articles des rangées ouvertes entre deux niveaux (avant exclu, après inclus) : les « nouveautés ».
    public static IReadOnlyList<Article> Debloques(int avant, int apres) =>
        Catalogue.Where(a => a.NiveauMin > avant && a.NiveauMin <= apres).ToList();

    // Rayons qui gagnent une rangée à ce palier (« Prochaine rangée : Dos, Main — niveau 15 »).
    public static IReadOnlyList<string> RayonsDuPalier(int palier) =>
        Rayons.Where(r => Catalogue.Any(a => RayonDe(a.Slot) == r && a.NiveauMin == palier)).ToList();

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

    // Catalogue commun avec l'app Android (Boutique.java) : mêmes identifiants, prix et paliers.
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
    }.Concat(Anciens()).ToList();

    // Le butin des expéditions (Expeditions.Exclusifs) se porte comme un article, mais ne se vend pas.
    public static Article? Trouver(string id) => Catalogue.FirstOrDefault(a => a.Id == id) ?? Expeditions.Exclusif(id);

    public static StyleBulle? Style(string id) => id switch
    {
        "bulle-doree" => new StyleBulle("#c9a227", 4, 0),
        "bulle-nuit" => new StyleBulle("#6cb6ff", 3, 0, "#16365e", true),
        "bulle-pixel" => new StyleBulle("#f69d50", 5, 0),
        "bulle-nuages" => new StyleBulle("#9b8cff", 3, 12),
        _ => null,
    };

    // Signe de l'emplacement (pas de couleur seule : un signe de forme, toujours).
    public static string Signe(string slot) => slot switch
    {
        Tete => "▲", Yeux => "◉", Cou => "◡", Dos => "▼", Main => "✚", Pieds => "▬", Compagnon => "♣", Effet => "✧", Couleur => "■",
        Fond => "▧", Bulle => "❝", Accessoire => "◆", Bonus => "★", Consommable => "◇", Speciaux => "★", _ => "·",
    };

    public static string NomSlot(string slot) => slot switch
    {
        Tete => "Tête", Yeux => "Yeux", Cou => "Cou", Dos => "Dos", Main => "Main", Pieds => "Pieds", Compagnon => "Compagnons", Effet => "Effets",
        Couleur => "Couleurs", Fond => "Décors", Bulle => "Bulles", Accessoire => "Accessoires", Bonus => "Bonus", Consommable => "Consommables",
        Speciaux => "Spéciaux", _ => slot,
    };

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
        var pool = Catalogue.Where(a => !a.Permanent).ToList();
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
        bool consommable = a.Slot == Consommable;
        if (!consommable && b.Inventaire.Contains(id)) return "déjà dans l'inventaire";
        if (!Ouvert(a, niveau)) return $"niveau {a.NiveauMin} requis";
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
        if (id != "" && (!b.Inventaire.Contains(id) || Trouver(id)?.Slot != slot)) return false;
        b.Equipe[slot] = new Port(id, t);
        return true;
    }

    // Ce qui est réellement porté : slot → id (les emplacements vides sont omis).
    public static Dictionary<string, string> Porte(IReadOnlyDictionary<string, Port> equipe) =>
        equipe.Where(kv => kv.Value.Id != "").ToDictionary(kv => kv.Key, kv => kv.Value.Id);

    // Ce qui se dessine sur Pilou lui-même (ni la couleur, ni le décor, ni le cadre de bulle).
    public static bool SurPilou(string slot) => slot is not (Couleur or Fond or Bulle);
}

// Pièces d'or, inventaire et équipement d'un appareil. Compteur G : chaque appareil ne fait que monter
// ses gains et ses dépenses ; le solde du groupe = Σ gains − Σ dépenses (− dépenses du téléphone, comptées
// au maximum : chaque PC du groupe applique les mêmes achats faits sur le téléphone).
public sealed class Bourse
{
    public int PoGagnes { get; set; }
    public int PoDepenses { get; set; }
    public int PoDepTelephone { get; set; }
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
