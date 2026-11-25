namespace PilouBureau;

// Boutique de Pilou : gratuite, virtuelle. On y dépense des pièces d'or (« po ») gagnées en quêtes ;
// aucune vraie monnaie, aucun achat réel. Les objets sont des identifiants : leur dessin vit dans Scene
// (PC) et Dessin (Android) ; en attendant, la boutique les montre par leur nom et un signe.
public sealed record Article(string Id, string Nom, string Slot, int Prix, int NiveauMin, Rarete Rarete, bool Permanent = false);

// Ce que Pilou porte : un objet par emplacement, horodaté (entre appareils, la dernière écriture gagne).
public sealed record Port(string Id, double T);

public static class Boutique
{
    public const string Tete = "tete", Yeux = "yeux", Cou = "cou", Dos = "dos", Main = "main", Compagnon = "compagnon", Effet = "effet", Couleur = "couleur";
    public static readonly string[] Slots = { Tete, Yeux, Cou, Dos, Main, Compagnon, Effet, Couleur };

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
    };

    public static Article? Trouver(string id) => Catalogue.FirstOrDefault(a => a.Id == id);

    // Signe de l'emplacement (pas de couleur seule : un signe de forme, toujours).
    public static string Signe(string slot) => slot switch
    {
        Tete => "▲", Yeux => "◉", Cou => "◡", Dos => "▼", Main => "✚", Compagnon => "♣", Effet => "✧", Couleur => "■", _ => "·",
    };

    public static string NomSlot(string slot) => slot switch
    {
        Tete => "Tête", Yeux => "Yeux", Cou => "Cou", Dos => "Dos", Main => "Main", Compagnon => "Compagnon", Effet => "Effet", Couleur => "Couleur", _ => slot,
    };

    // ---- Offres du jour : 4 objets non permanents, tirés de la date ; le premier à -25 %.

    public static IReadOnlyList<Article> OffresDuJour(DateOnly jour)
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
        if (b.Inventaire.Contains(id)) return "déjà dans l'inventaire";
        if (niveau < a.NiveauMin) return $"niveau {a.NiveauMin} requis";
        if (!EnVente(a, jour)) return "pas en vente aujourd'hui";
        int prix = Prix(a, jour);
        if (solde < prix) return $"il manque {prix - solde} po";
        if (parTelephone) b.PoDepTelephone += prix;
        else b.PoDepenses += prix;
        b.Inventaire.Add(id);
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
