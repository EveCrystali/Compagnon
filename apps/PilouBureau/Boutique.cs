namespace PilouBureau;

// Boutique de Pilou : gratuite, virtuelle. On y dépense des pièces d'or (« po ») gagnées en quêtes ;
// aucune vraie monnaie, aucun achat réel. Les objets sont des identifiants : leur dessin vit dans Scene
// (PC) et Dessin (Android) ; en attendant, la boutique les montre par leur nom et un signe.
public sealed record Article(string Id, string Nom, string Slot, int Prix, int NiveauMin, Rarete Rarete, bool Permanent = false);

// Ce que Pilou porte : un objet par emplacement, horodaté (entre appareils, la dernière écriture gagne).
public sealed record Port(string Id, double T);

public static class Boutique
{
    public const string Tete = "tete", Yeux = "yeux", Cou = "cou", Dos = "dos", Main = "main", Pieds = "pieds", Compagnon = "compagnon", Effet = "effet", Couleur = "couleur";
    // Emplacements qui se portent (Bourse.Equipe) ; « accessoire » (le chapeau historique, porté via les réglages),
    // « bonus » (actif dès qu'il est possédé) et « consommable » (s'achète plusieurs fois) sont à part.
    public static readonly string[] Slots = { Tete, Yeux, Cou, Dos, Main, Pieds, Compagnon, Effet, Couleur };
    public const string Accessoire = "accessoire", Bonus = "bonus", Consommable = "consommable";
    public static readonly string[] Rayons = { Accessoire, Tete, Yeux, Cou, Dos, Main, Pieds, Compagnon, Effet, Couleur, Bonus, Consommable };
    public const string TraineeEtoiles = "trainee-etoiles", CanneDoree = "canne-doree", MarmiteCuivre = "marmite-cuivre", PierreCalme = "pierre-calme";

    // Anciennes récompenses de niveau, devenues articles (niveau d'accès = ancien niveau ; prix selon ce niveau).
    private static IEnumerable<Article> Anciens()
    {
        foreach (var a in new[] { PilouBureau.Accessoire.Feuille, PilouBureau.Accessoire.Noeud, PilouBureau.Accessoire.Casque,
                     PilouBureau.Accessoire.Bonnet, PilouBureau.Accessoire.Lunettes, PilouBureau.Accessoire.Couronne,
                     PilouBureau.Accessoire.ChapeauPeche, PilouBureau.Accessoire.Toque, PilouBureau.Accessoire.Tablier,
                     PilouBureau.Accessoire.EtoileMer })
        {
            int n = Recompenses.Ancien(a);
            yield return new Article(Recompenses.IdAccessoire(a), Nom(a), Accessoire, Math.Min(600, 60 + 15 * n), n, Rang(n), true);
        }
        foreach (var c in Enum.GetValues<PilouBureau.Couleur>().Where(c => c != PilouBureau.Couleur.Bleu))
        {
            int n = Recompenses.Ancien(c);
            yield return new Article(Recompenses.IdCouleur(c), "Couleur " + Recompenses.NomCouleur(c).ToLowerInvariant(), Couleur,
                Math.Min(600, 100 + 10 * n), n, Rang(n), true);
        }
        yield return new Article(TraineeEtoiles, "Traînée d'étoiles", Effet, 220, 9, Rarete.Rare, true);
        yield return new Article(CanneDoree, "Canne dorée (plus de prises légendaires)", Bonus, 500, 30, Rarete.Legendaire, true);
        yield return new Article(MarmiteCuivre, "Marmite en cuivre (moins de plats brûlés)", Bonus, 520, 35, Rarete.Legendaire, true);
        yield return new Article(PierreCalme, "Pierre de calme (retient une évolution)", Consommable, 150, 9, Rarete.PeuCommun, true);
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

    public static readonly IReadOnlyList<Article> Catalogue = new Article[]
    {
        // Tête
        new("casquette", "Casquette", Tete, 80, 1, Rarete.Commun, true),
        new("bandeau-ninja", "Bandeau de ninja", Tete, 120, 2, Rarete.PeuCommun),
        new("chapeau-pirate", "Chapeau de pirate", Tete, 220, 4, Rarete.Rare),
        new("haut-de-forme", "Haut-de-forme", Tete, 260, 5, Rarete.Rare),
        new("couronne-fleurs", "Couronne de fleurs", Tete, 180, 3, Rarete.PeuCommun),
        new("cornes-viking", "Casque à cornes", Tete, 320, 8, Rarete.Epique),
        new("chapeau-sorcier", "Chapeau de sorcier", Tete, 380, 10, Rarete.Epique),
        new("aureole", "Auréole", Tete, 450, 15, Rarete.Legendaire),
        // Yeux
        new("lunettes-rondes", "Lunettes rondes", Yeux, 90, 1, Rarete.Commun, true),
        new("monocle", "Monocle", Yeux, 200, 6, Rarete.Rare),
        new("masque-plongee", "Masque de plongée", Yeux, 160, 3, Rarete.PeuCommun),
        // Cou et dos
        new("echarpe", "Écharpe", Cou, 70, 1, Rarete.Commun, true),
        new("medaille", "Médaille", Cou, 300, 9, Rarete.Epique),
        new("cape", "Cape", Dos, 280, 7, Rarete.Rare),
        // Main
        new("tasse-cafe", "Tasse de café", Main, 60, 1, Rarete.Commun, true),
        new("parapluie", "Parapluie", Main, 110, 2, Rarete.PeuCommun),
        new("ballon-helium", "Ballon", Main, 130, 3, Rarete.PeuCommun),
        new("baguette", "Baguette magique", Main, 340, 11, Rarete.Epique),
        // Météo : ce qui protège de la pluie, du froid et de la chaleur (Meteo.ContrePluie…)
        new("impermeable", "Imperméable", Dos, 180, 3, Rarete.PeuCommun),
        new("bottes-pluie", "Bottes de pluie", Pieds, 90, 2, Rarete.Commun),
        new("moufles", "Moufles", Main, 80, 2, Rarete.Commun),
        new("eventail", "Éventail", Main, 100, 3, Rarete.PeuCommun),
        new("parapluie-etoile", "Parapluie étoilé", Main, 420, 14, Rarete.Epique),
        // Compagnons
        new("petit-poisson-bocal", "Poisson en bocal", Compagnon, 240, 5, Rarete.Rare),
        new("petit-chat", "Petit chat", Compagnon, 520, 12, Rarete.Legendaire),
        // Effets
        new("trainee-coeurs", "Traînée de cœurs", Effet, 300, 6, Rarete.Rare),
        new("trainee-notes", "Traînée de notes", Effet, 340, 8, Rarete.Epique),
        new("aura", "Aura", Effet, 600, 18, Rarete.Legendaire),
        // Couleurs
        new("sable", "Couleur sable", Couleur, 150, 1, Rarete.Commun, true),
        new("ardoise", "Couleur ardoise", Couleur, 150, 2, Rarete.Commun, true),
        new("lavande", "Couleur lavande", Couleur, 200, 4, Rarete.PeuCommun),
        new("glacier", "Couleur glacier", Couleur, 220, 6, Rarete.Rare),
        new("corail-orange", "Couleur corail", Couleur, 250, 8, Rarete.Rare),
    }.Concat(Anciens()).ToList();

    public static Article? Trouver(string id) => Catalogue.FirstOrDefault(a => a.Id == id);

    // Signe de l'emplacement (pas de couleur seule : un signe de forme, toujours).
    public static string Signe(string slot) => slot switch
    {
        Tete => "▲", Yeux => "◉", Cou => "◡", Dos => "▼", Main => "✚", Pieds => "▬", Compagnon => "♣", Effet => "✧", Couleur => "■",
        Accessoire => "◆", Bonus => "★", Consommable => "◇", _ => "·",
    };

    public static string NomSlot(string slot) => slot switch
    {
        Tete => "Tête", Yeux => "Yeux", Cou => "Cou", Dos => "Dos", Main => "Main", Pieds => "Pieds", Compagnon => "Compagnon", Effet => "Effet", Couleur => "Couleur",
        Accessoire => "Accessoires", Bonus => "Bonus", Consommable => "Consommables", _ => slot,
    };

    // ---- Offres du jour : 4 objets non permanents, tirés de la date ; le premier à -25 %.
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

    public static bool EnVente(Article a, DateOnly jour) => a.Permanent || OffresDuJour(jour).Any(o => o.Id == a.Id);

    public static int Prix(Article a, DateOnly jour)
    {
        var offres = OffresDuJour(jour);
        return offres.Count > 0 && offres[0].Id == a.Id ? a.Prix * 3 / 4 : a.Prix;
    }

    // Achat : null si fait, sinon la raison du refus. Le solde ne devient jamais négatif.
    public static string? Acheter(Bourse b, string id, int niveau, int solde, DateOnly jour, bool parTelephone = false)
    {
        var a = Trouver(id);
        if (a is null) return "objet inconnu";
        bool consommable = a.Slot == Consommable;
        if (!consommable && b.Inventaire.Contains(id)) return "déjà dans l'inventaire";
        if (niveau < a.NiveauMin) return $"niveau {a.NiveauMin} requis";
        if (!EnVente(a, jour)) return "pas en vente aujourd'hui";
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
