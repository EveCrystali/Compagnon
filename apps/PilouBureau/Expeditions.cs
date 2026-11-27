using System.Globalization;
using System.Security.Cryptography;

namespace PilouBureau;

// Expéditions de Pilou (docs/EXPEDITIONS.md) : une petite aventure qui se joue toute seule. On choisit un lieu
// (un clic), Pilou part avec son baluchon et son épée en bois, une pancarte le remplace, et l'expédition se
// résout seule : une suite d'événements tirés d'une graine (combats contre des créatures, pièges, coffres,
// rencontres), puis une issue — victoire, partielle ou défaite. Il rapporte un peu de po et d'XP, parfois un
// butin introuvable en boutique, et un journal de quelques lignes.
//
// On ne peut pas en abuser : chaque départ coûte de l'énergie (⚡, 0 à 100), il faut attendre un peu entre deux
// expéditions et il y en a trois par jour au plus (pour tout le groupe d'appareils). L'énergie remonte seule
// jusqu'à 50 (≈ +5/h), surtout en travaillant (temps passé dans une appli de travail, IA qui finit, quête
// réussie ; jamais au nombre de frappes), et en mangeant (plats cuisinés, en-cas de route de la boutique).
// Pilou boudeur : tout se recharge deux fois moins vite.
//
// Logique pure (sans WPF) : testée par ExpeditionsTests.cs. L'expédition appartient à l'appareil qui la lance :
// ses gains vont dans le compteur G de cet appareil (Bourse.PoGagnes, Profil.Xp), une seule fois.

// ---- Énergie

public sealed class Energie
{
    public double Valeur { get; set; } = 50;
    // Dernière mise à jour (ms Unix) ; 0 : jamais.
    public double T { get; set; }
    // Plafonds du jour : énergie déjà gagnée en travaillant, en mangeant (remis à zéro à minuit).
    public string Jour { get; set; } = "";
    public double Travail { get; set; }
    public double Nourriture { get; set; }
    // Secondes de travail productif pas encore converties en énergie.
    public double Reliquat { get; set; }
    // Dernier bonus « une IA a fini » (ms Unix) : au plus un toutes les 3 min.
    public double DernierTour { get; set; }
}

public static class Jauge
{
    public const double Max = 100;
    // À l'attente : +5 par heure, jusqu'à 50 seulement ; au-delà, il faut travailler ou manger.
    public const double PlafondAttente = 50, ParHeure = 5;
    // Travail productif : +1 toutes les 6 min passées dans une appli de travail (au plus 40 par jour, travail,
    // IA et quêtes compris). Un appel compte au plus une minute (un long silence du minuteur ne paie pas double).
    public const double Tranche = 360, PlafondTravail = 40, AppelMax = 60;
    public const double BonusTour = 1, BonusQuete = 2, EcartTours = 180_000;
    // Nourriture : au plus 40 par jour.
    public const double PlafondNourriture = 40;
    // Pilou boude : tout se recharge deux fois moins vite.
    public const double Boudeur = 0.5;

    // Ce qu'un repas rend (plats cuisinés, en-cas des soins, en-cas de route de la boutique).
    public static double Repas(string objet) => objet switch
    {
        "jus-etoile" => 30,
        "galette-route" => 15,
        "plat" => 6,
        "plat-invente" => 4,
        "plat-rate" => 1,
        "gateau" => 6,
        "soupe" => 5,
        "pomme" => 4,
        "croquettes" => 2,
        _ => 0,
    };

    public static int Affiche(Energie e) => (int)Math.Floor(Math.Clamp(e.Valeur, 0, Max));

    private static void Journee(Energie e, DateTime local)
    {
        var jour = Quetes.CleJour(local);
        if (e.Jour == jour) return;
        e.Jour = jour;
        e.Travail = e.Nourriture = 0;
    }

    private static double Facteur(bool boude) => boude ? Boudeur : 1;

    private static double Ajouter(Energie e, double quantite)
    {
        double avant = e.Valeur;
        e.Valeur = Math.Clamp(e.Valeur + quantite, 0, Max);
        return e.Valeur - avant;
    }

    // Le temps passe : la jauge remonte seule jusqu'à 50.
    public static double Avancer(Energie e, double maintenant, bool boude)
    {
        if (e.T <= 0 || maintenant <= e.T)
        {
            if (e.T <= 0) e.T = maintenant;
            return 0;
        }
        double dt = maintenant - e.T;
        e.T = maintenant;
        if (e.Valeur >= PlafondAttente) return 0;
        double gain = Math.Min(PlafondAttente - e.Valeur, dt / 3_600_000 * ParHeure * Facteur(boude));
        return Ajouter(e, gain);
    }

    // Travail productif (secondes passées dans une appli de travail, la personne présente). Renvoie l'énergie gagnée.
    public static double Travailler(Energie e, double secondes, DateTime local, bool boude)
    {
        Journee(e, local);
        if (secondes <= 0) return 0;
        e.Reliquat += Math.Min(secondes, AppelMax) * Facteur(boude);
        int tranches = (int)(e.Reliquat / Tranche);
        if (tranches == 0) return 0;
        e.Reliquat -= tranches * Tranche;
        return Travail(e, tranches);
    }

    private static double Travail(Energie e, double quantite)
    {
        double permis = Math.Max(0, Math.Min(quantite, PlafondTravail - e.Travail));
        double gagne = Ajouter(e, permis);
        e.Travail += permis;
        return gagne;
    }

    // Une IA vient de finir (« ✓ fini ») : +1, au plus toutes les 3 min, dans le plafond du travail.
    public static double Tour(Energie e, double maintenant, DateTime local, bool boude)
    {
        Journee(e, local);
        if (maintenant - e.DernierTour < EcartTours) return 0;
        e.DernierTour = maintenant;
        return Travail(e, BonusTour * Facteur(boude));
    }

    // Une quête réussie : +2, dans le plafond du travail.
    public static double Quete(Energie e, DateTime local, bool boude)
    {
        Journee(e, local);
        return Travail(e, BonusQuete * Facteur(boude));
    }

    // Un repas : ce qu'il rend, dans le plafond du jour.
    public static double Manger(Energie e, string objet, DateTime local, bool boude)
    {
        Journee(e, local);
        double q = Repas(objet) * Facteur(boude);
        double permis = Math.Max(0, Math.Min(q, PlafondNourriture - e.Nourriture));
        double gagne = Ajouter(e, permis);
        e.Nourriture += permis;
        return gagne;
    }

    public static bool Depenser(Energie e, int cout)
    {
        if (cout < 0 || e.Valeur + 1e-9 < cout) return false;
        e.Valeur = Math.Max(0, e.Valeur - cout);
        return true;
    }
}

// ---- Le monde

public sealed record Creature(string Id, string Nom, int Force, bool Feminin = false)
{
    private string Bas => char.ToLowerInvariant(Nom[0]) + Nom[1..];
    // « un bug géant », « une hydre… » ; « le golem… », « l'hydre… », « la gargouille… ».
    public string Un => (Feminin ? "une " : "un ") + Bas;
    public string Le => ("aeiouyhéè".Contains(Bas[0]) ? "l'" : Feminin ? "la " : "le ") + Bas;
}

// Un lieu : niveau d'accès, coût en énergie, durée, rang de risque (0 à 4), nombre d'événements, faune, boss,
// pièces d'un coffre, prime de victoire, XP de victoire, chance d'un butin exclusif (sur victoire), son butin à lui.
public sealed record Lieu(
    string Id, string Nom, string Signe, int Niveau, int Cout, int Minutes, int Risque, int Evenements,
    string[] Faune, string Boss, int PoMin, int PoMax, int PoVictoire, int Xp, double ChanceRare, string Exclusif, string Accroche);

// Un objet possédé qui aide un peu en expédition (« arme/outil » ou « talisman ») : points de pourcentage.
public sealed record Outil(string Id, string Nom, string Emplacement, int Combat, int Piege, int Butin);

public enum Denouement { Victoire, Partielle, Defaite, Rappel }

// Une expédition en cours (ce qu'il faut pour la résoudre : tout le reste vient de la graine).
public sealed class Expedition
{
    public string Id { get; set; } = "";
    public string Lieu { get; set; } = "";
    public double Debut { get; set; }
    public double Fin { get; set; }
    public ulong Graine { get; set; }
    public string Arme { get; set; } = "";
    public string Talisman { get; set; } = "";
    public int Niveau { get; set; } = 1;
}

// Ce qu'elle a donné : issue, gains, butin, journal.
public sealed class Resultat
{
    public string Id { get; set; } = "";
    public string Lieu { get; set; } = "";
    public Denouement Issue { get; set; }
    public int Po { get; set; }
    public int Xp { get; set; }
    public int Fragments { get; set; }
    public string Objet { get; set; } = "";     // butin exclusif (cosmétique introuvable en boutique), "" sinon
    public string Trophee { get; set; } = "";   // premier boss battu ici : son trophée
    public bool Boss { get; set; }              // un boss battu
    public int Pv { get; set; }                 // cœurs restants (0 : défaite)
    public double Fin { get; set; }
    public List<string> Journal { get; set; } = new();
    // Gains déjà versés (une relecture ou un redémarrage ne paie jamais deux fois).
    public bool Credite { get; set; }

    // Butin « rare » pour la quête : éclats, objet exclusif, trophée.
    public int Rares => Fragments + (Objet != "" ? 1 : 0) + (Trophee != "" ? 1 : 0);
}

// Tout ce que l'appareil garde (dans son profil) : énergie, expédition en cours, dernier journal, limites, collection.
public sealed class EtatExpedition
{
    public Energie Energie { get; set; } = new();
    public Expedition? Courante { get; set; }
    public Resultat? Dernier { get; set; }
    public bool DernierLu { get; set; } = true;
    // Départs du jour (pour la limite) et fin du temps de repos (ms Unix).
    public string Jour { get; set; } = "";
    public int Nombre { get; set; }
    public double Libre { get; set; }
    // Équipement léger : un outil et un talisman parmi les objets possédés ("" : épée en bois, aucun talisman).
    public string Arme { get; set; } = "";
    public string Talisman { get; set; } = "";
    // Collection : éclats de cristal (forgés en butin exclusif à 25), trophées de boss, compteurs.
    public int Fragments { get; set; }
    public List<string> Trophees { get; set; } = new();
    public int Total { get; set; }
    public int Victoires { get; set; }
    public int Defaites { get; set; }
}

// Ce que les autres appareils du groupe ont dit de leurs expéditions (limite et repos partagés).
public sealed record ExpeditionsAutres(int Aujourdhui, double Libre)
{
    public static readonly ExpeditionsAutres Aucun = new(0, 0);
}

public static class Expeditions
{
    public const int ParJour = 3, PvMax = 3, Forge = 25;
    public const double Repos = 30 * 60_000;      // entre deux expéditions (après le retour)
    public const double Cabosse = 20 * 60_000;    // pansement après une défaite
    public const double ChanceBoss = 0.5;         // le dernier événement est un boss une fois sur deux
    public const string EpeeBois = "epee-bois";

    public static readonly IReadOnlyList<Creature> Creatures = new Creature[]
    {
        new("bug-geant", "Bug géant", 1),
        new("slime-cache", "Slime de cache", 2),
        new("spectre-404", "Spectre 404", 2),
        new("golem-tickets", "Golem de tickets", 3),
        new("hydre-dependances", "Hydre des dépendances", 3, true),
        new("gargouille-latence", "Gargouille de latence", 4, true),
    };

    public static readonly IReadOnlyList<Lieu> Lieux = new Lieu[]
    {
        new("caverne-cables", "Caverne des câbles", "▼", 1, 15, 20, 0, 3, new[] { "bug-geant", "spectre-404" }, "bug-geant",
            2, 4, 2, 3, 0.015, "torche", "des câbles emmêlés à perte de vue"),
        new("foret-onglets", "Forêt des onglets", "♣", 5, 25, 40, 1, 4, new[] { "bug-geant", "slime-cache" }, "slime-cache",
            2, 5, 3, 4, 0.02, "slime-apprivoise", "des milliers d'onglets ouverts, jamais refermés"),
        new("tour-tampon", "Tour du tampon", "▲", 10, 35, 60, 2, 4, new[] { "slime-cache", "spectre-404" }, "golem-tickets",
            3, 6, 4, 6, 0.025, "bouclier-couvercle", "chaque étage attend que le précédent se vide"),
        new("marais-majs", "Marais des mises à jour", "≈", 15, 45, 90, 3, 5, new[] { "spectre-404", "slime-cache" }, "hydre-dependances",
            3, 7, 5, 7, 0.03, "casque-passoire", "on y redémarre sans cesse, à 37 %"),
        new("citadelle-nuage", "Citadelle du nuage", "☁", 25, 60, 120, 4, 6, new[] { "spectre-404", "golem-tickets" }, "gargouille-latence",
            4, 8, 6, 9, 0.04, "carte-tresor", "tout là-haut, au-dessus des serveurs"),
    };

    // Armes, outils et talismans : des objets de la boutique (ou du butin) qui aident un peu, jamais beaucoup.
    public static readonly IReadOnlyList<Outil> Outils = new Outil[]
    {
        new(EpeeBois, "Épée en bois", "arme", 0, 0, 0),
        new("epee-mousse", "Épée en mousse", "arme", 5, 0, 0),
        new("baguette", "Baguette magique", "arme", 3, 0, 2),
        new("lanterne", "Lanterne", "arme", 0, 6, 0),
        new("parapluie", "Parapluie", "arme", 0, 4, 0),
        new("canne-or", "Canne à pêche dorée", "arme", 0, 0, 4),
        new("torche", "Torche", "arme", 3, 5, 0),
        new("medaille", "Médaille", "talisman", 3, 0, 0),
        new("aureole", "Auréole", "talisman", 0, 4, 0),
        new("collier-perles", "Collier de perles", "talisman", 0, 0, 4),
        new("couronne-laurier", "Couronne de laurier", "talisman", 2, 2, 0),
        new("bouclier-couvercle", "Bouclier-couvercle", "talisman", 5, 0, 0),
        new("carte-tresor", "Carte au trésor", "talisman", 0, 0, 6),
    };

    // Butin exclusif : introuvable en boutique (Boutique.Trouver les connaît, Boutique.Acheter les refuse).
    public static readonly IReadOnlyList<Article> Exclusifs = new Article[]
    {
        new("torche", "Torche (butin d'expédition)", Boutique.Main, 0, 1, Rarete.Rare, true),
        new("slime-apprivoise", "Slime apprivoisé (butin d'expédition)", Boutique.Compagnon, 0, 1, Rarete.Epique, true),
        new("bouclier-couvercle", "Bouclier-couvercle (butin d'expédition)", Boutique.Dos, 0, 1, Rarete.Rare, true),
        new("casque-passoire", "Casque-passoire (butin d'expédition)", Boutique.Tete, 0, 1, Rarete.Epique, true),
        new("carte-tresor", "Carte au trésor (butin d'expédition)", Boutique.Bonus, 0, 1, Rarete.Legendaire, true),
    };

    public static Article? Exclusif(string id) => Exclusifs.FirstOrDefault(a => a.Id == id);

    public static bool EstExclusif(string id) => Exclusifs.Any(a => a.Id == id);

    public static Lieu? Trouver(string id) => Lieux.FirstOrDefault(l => l.Id == id);

    public static Creature Bete(string id) => Creatures.FirstOrDefault(c => c.Id == id) ?? Creatures[0];

    public static Outil? OutilDe(string id) => Outils.FirstOrDefault(o => o.Id == id);

    public static string Trophee(string boss) => "trophee-" + boss;

    // Les outils qu'on peut emporter (l'épée en bois est toujours là ; les autres doivent être possédés).
    public static List<Outil> Disponibles(string emplacement, IReadOnlyCollection<string> possedes) =>
        Outils.Where(o => o.Emplacement == emplacement && (o.Id == EpeeBois || possedes.Contains(o.Id))).ToList();

    // Bonus total (combat, pièges, butin) de l'équipement, en points de pourcentage.
    public static (int Combat, int Piege, int Butin) Bonus(string arme, string talisman)
    {
        var a = OutilDe(arme) is { Emplacement: "arme" } x ? x : null;
        var t = OutilDe(talisman) is { Emplacement: "talisman" } y ? y : null;
        return ((a?.Combat ?? 0) + (t?.Combat ?? 0), (a?.Piege ?? 0) + (t?.Piege ?? 0), (a?.Butin ?? 0) + (t?.Butin ?? 0));
    }

    public static string Effet(Outil o)
    {
        var l = new List<string>();
        if (o.Combat > 0) l.Add($"combat +{o.Combat} %");
        if (o.Piege > 0) l.Add($"pièges +{o.Piege} %");
        if (o.Butin > 0) l.Add($"butin +{o.Butin} %");
        return l.Count == 0 ? "rien de spécial, mais ça rassure" : string.Join(", ", l);
    }

    // Risque en signes de forme : ◆◆◇◇◇.
    public static string Risque(Lieu l) => new string('◆', l.Risque + 1) + new string('◇', 4 - l.Risque);

    public static string Duree(int minutes) => minutes < 60 ? $"{minutes} min" : minutes % 60 == 0 ? $"{minutes / 60} h" : $"{minutes / 60} h {minutes % 60:00}";

    // ---- Limites : énergie, repos, trois par jour (pour tout le groupe), pas pendant une visite ni un jeu

    private static void Journee(EtatExpedition e, DateTime local)
    {
        var jour = Quetes.CleJour(local);
        if (e.Jour == jour) return;
        e.Jour = jour;
        e.Nombre = 0;
    }

    public static int Restantes(EtatExpedition e, DateTime local, ExpeditionsAutres autres)
    {
        Journee(e, local);
        return Math.Max(0, ParJour - e.Nombre - autres.Aujourdhui);
    }

    // Fin du repos (la plus tardive du groupe), 0 s'il n'y en a pas.
    public static double LibreA(EtatExpedition e, ExpeditionsAutres autres) => Math.Max(e.Libre, autres.Libre);

    // null : il peut partir ; sinon, pourquoi pas (une phrase courte).
    public static string? Refus(EtatExpedition e, Lieu l, int niveau, double maintenant, DateTime local, ExpeditionsAutres autres,
        string occupe = "")
    {
        if (e.Courante is not null) return "Pilou est déjà en expédition";
        if (occupe != "") return occupe;
        if (niveau < l.Niveau) return $"niveau {l.Niveau} requis";
        if (Restantes(e, local, autres) <= 0) return $"{ParJour} expéditions aujourd'hui : c'est assez, reviens demain";
        double libre = LibreA(e, autres);
        if (maintenant < libre) return $"Pilou se repose encore ({Statut.Duree(libre - maintenant)})";
        int energie = Jauge.Affiche(e.Energie);
        if (energie < l.Cout) return $"il faut {l.Cout} ⚡ (Pilou en a {energie})";
        return null;
    }

    public static string NouvelId() => Convert.ToHexString(RandomNumberGenerator.GetBytes(5)).ToLowerInvariant();

    public static ulong GraineDe(string appareil, string id) => Hasard.Graine($"expedition|{appareil}|{id}");

    // Départ : énergie dépensée, départ compté, repos programmé après le retour. null si refusé (Refus le dit).
    public static Expedition? Partir(EtatExpedition e, Lieu l, int niveau, double maintenant, DateTime local, ExpeditionsAutres autres,
        string appareil, string id, string occupe = "")
    {
        if (Refus(e, l, niveau, maintenant, local, autres, occupe) is not null) return null;
        if (!Jauge.Depenser(e.Energie, l.Cout)) return null;
        var possible = new HashSet<string>(Outils.Select(o => o.Id));
        var x = new Expedition
        {
            Id = id, Lieu = l.Id, Debut = maintenant, Fin = maintenant + l.Minutes * 60_000.0, Graine = GraineDe(appareil, id),
            Arme = possible.Contains(e.Arme) ? e.Arme : EpeeBois, Talisman = possible.Contains(e.Talisman) ? e.Talisman : "",
            Niveau = Math.Max(1, niveau),
        };
        e.Courante = x;
        e.Nombre++;
        e.Libre = x.Fin + Repos;
        return x;
    }

    // Le temps passe : l'expédition finie se résout (une fois). Renvoie le résultat à créditer, null sinon.
    public static Resultat? Avancer(EtatExpedition e, double maintenant, IReadOnlyCollection<string> possedes)
    {
        if (e.Courante is not { } x || maintenant < x.Fin) return null;
        var r = Resoudre(x, possedes, e.Trophees);
        e.Courante = null;
        e.Dernier = r;
        e.DernierLu = false;
        e.Libre = Math.Max(e.Libre, x.Fin + Repos);
        return r;
    }

    // Rappelé en route : il rentre tout de suite, les mains vides (le départ reste compté, le repos aussi).
    public static Resultat? Rappeler(EtatExpedition e, double maintenant)
    {
        if (e.Courante is not { } x) return null;
        var l = Trouver(x.Lieu);
        var r = new Resultat
        {
            Id = x.Id, Lieu = x.Lieu, Issue = Denouement.Rappel, Pv = PvMax, Fin = maintenant, Credite = true,
            Journal = new List<string>
            {
                $"✦ Départ pour {De(l?.Nom ?? "l'aventure")}.",
                "☏ On m'appelle ! Je fais demi-tour avant le premier carrefour.",
                "↩ Rentré les mains vides, mais avec de bonnes chaussettes.",
            },
        };
        e.Courante = null;
        e.Dernier = r;
        e.DernierLu = true;
        e.Libre = maintenant + Repos;
        return r;
    }

    // Les gains d'un résultat, versés une seule fois au profil de cet appareil. bonus : × 0,6 s'il boude, × 1,2
    // s'il rayonne (Soins.Bonus). Renvoie ce qui a été versé (0 si déjà fait) et l'objet forgé avec les éclats.
    public static (int Po, int Xp, string Forge) Crediter(Profil p, Resultat r, Func<int, int>? bonus = null)
    {
        if (r.Credite) return (0, 0, "");
        r.Credite = true;
        var e = p.Expedition;
        bonus ??= x => x;
        int po = r.Po > 0 ? bonus(r.Po) : 0, xp = r.Xp > 0 ? bonus(r.Xp) : 0;
        p.Bourse.PoGagnes += po;
        p.Xp += xp;
        if (r.Issue != Denouement.Rappel) e.Total++;
        if (r.Issue == Denouement.Victoire) e.Victoires++;
        if (r.Issue == Denouement.Defaite) e.Defaites++;
        if (r.Objet != "" && !p.Bourse.Inventaire.Contains(r.Objet)) p.Bourse.Inventaire.Add(r.Objet);
        if (r.Trophee != "" && !e.Trophees.Contains(r.Trophee)) e.Trophees.Add(r.Trophee);
        e.Fragments += r.Fragments;
        string forge = "";
        if (e.Fragments >= Forge)
        {
            e.Fragments -= Forge;
            forge = Exclusifs.Select(a => a.Id).FirstOrDefault(id => !p.Bourse.Inventaire.Contains(id)) ?? "";
            if (forge != "") p.Bourse.Inventaire.Add(forge);
            else p.Bourse.PoGagnes += 40; // tout est déjà forgé : les éclats se revendent
        }
        return (po, xp, forge);
    }

    // ---- La résolution (pure : même expédition, mêmes possessions → même résultat, partout)

    private enum Sorte { Combat, Piege, Coffre, Rencontre, Repos, Boss }

    private static double Reel(Hasard h) => (h.Brut() >> 11) * (1.0 / (1UL << 53));

    private static T Un<T>(Hasard h, IReadOnlyList<T> l) => l[h.Suivant(l.Count)];

    private static Sorte Tirer(Hasard h)
    {
        int x = h.Suivant(100);
        return x < 38 ? Sorte.Combat : x < 60 ? Sorte.Piege : x < 82 ? Sorte.Coffre : x < 94 ? Sorte.Rencontre : Sorte.Repos;
    }

    // Chance de gagner un combat : la force de la bête, le risque du lieu, un peu d'avance de niveau, l'équipement.
    public static double ChanceCombat(Creature c, Lieu l, int niveau, int bonus, bool boss) =>
        Math.Clamp(0.80 - 0.07 * (c.Force + (boss ? 1 : 0)) - 0.015 * l.Risque + Avance(l, niveau) + bonus / 100.0, 0.2, 0.95);

    public static double ChancePiege(Lieu l, int niveau, int bonus) =>
        Math.Clamp(0.75 - 0.025 * l.Risque + Avance(l, niveau) + bonus / 100.0, 0.3, 0.95);

    // Avance de niveau sur le lieu : +0,6 point par niveau, 6 au plus.
    private static double Avance(Lieu l, int niveau) => Math.Clamp(niveau - l.Niveau, 0, 10) * 0.006;

    public static Resultat Resoudre(Expedition x, IReadOnlyCollection<string> possedes, IReadOnlyCollection<string>? trophees = null)
    {
        var l = Trouver(x.Lieu) ?? Lieux[0];
        var h = new Hasard(x.Graine);
        var (bCombat, bPiege, bButin) = Bonus(x.Arme, x.Talisman);
        var arme = OutilDe(x.Arme) is { Emplacement: "arme" } o ? o : OutilDe(EpeeBois)!;
        var j = new List<string> { Un(h, Departs).Replace("{lieu}", De(l.Nom)).Replace("{arme}", Mon(arme)) };
        int pv = PvMax, po = 0, fragments = 0;
        bool bossVu = false, bossBattu = false;
        string bossNom = Bete(l.Boss).Nom;
        for (int i = 0; i < l.Evenements && pv > 0; i++)
        {
            var sorte = i == l.Evenements - 1 && Reel(h) < ChanceBoss ? Sorte.Boss : Tirer(h);
            switch (sorte)
            {
                case Sorte.Combat:
                {
                    var c = Bete(Un(h, l.Faune));
                    if (Reel(h) < ChanceCombat(c, l, x.Niveau, bCombat, false))
                    {
                        int gain = h.Entre(1, 2 + l.Risque);
                        po += gain;
                        j.Add(Un(h, CombatsGagnes).Replace("{Un}", Majuscule(c.Un)).Replace("{un}", c.Un).Replace("{Le}", Majuscule(c.Le)).Replace("{le}", c.Le).Replace("{arme}", Mon(arme)) + $" (+{gain} po)");
                    }
                    else
                    {
                        pv--;
                        j.Add(Un(h, CombatsPerdus).Replace("{Un}", Majuscule(c.Un)).Replace("{un}", c.Un).Replace("{Le}", Majuscule(c.Le)).Replace("{le}", c.Le) + " (♥ −1)");
                    }
                    break;
                }
                case Sorte.Boss:
                {
                    bossVu = true;
                    var c = Bete(l.Boss);
                    if (Reel(h) < ChanceCombat(c, l, x.Niveau, bCombat, true))
                    {
                        bossBattu = true;
                        int gain = h.Entre(2 + l.Risque, 4 + 2 * l.Risque);
                        po += gain;
                        j.Add(Un(h, BossGagnes).Replace("{Un}", Majuscule(c.Un)).Replace("{un}", c.Un).Replace("{Le}", Majuscule(c.Le)).Replace("{le}", c.Le) + $" (+{gain} po)");
                    }
                    else
                    {
                        pv -= 2; // un boss tape fort
                        j.Add(Un(h, BossPerdus).Replace("{Un}", Majuscule(c.Un)).Replace("{un}", c.Un).Replace("{Le}", Majuscule(c.Le)).Replace("{le}", c.Le) + " (♥ −2)");
                    }
                    break;
                }
                case Sorte.Piege:
                    if (Reel(h) < ChancePiege(l, x.Niveau, bPiege)) j.Add(Un(h, PiegesEvites));
                    else
                    {
                        pv--;
                        j.Add(Un(h, PiegesSubis) + " (♥ −1)");
                    }
                    break;
                case Sorte.Coffre:
                {
                    int gain = (int)Math.Round(h.Entre(l.PoMin, l.PoMax) * (1 + bButin / 100.0));
                    po += gain;
                    bool eclat = Reel(h) < 0.10 + 0.02 * l.Risque;
                    if (eclat) fragments++;
                    j.Add(Un(h, Coffres) + $" : {gain} po" + (eclat ? " et un éclat de cristal ◆" : "") + ".");
                    break;
                }
                case Sorte.Rencontre:
                {
                    int sorteR = h.Suivant(4);
                    if (sorteR <= 1)
                    {
                        int gain = h.Entre(1, 3);
                        po += gain;
                        j.Add(Un(h, RencontresPo) + $" (+{gain} po)");
                    }
                    else if (sorteR == 2 && pv < PvMax)
                    {
                        pv++;
                        j.Add(Un(h, RencontresSoin) + " (♥ +1)");
                    }
                    else j.Add(Un(h, RencontresDroles));
                    break;
                }
                case Sorte.Repos:
                    if (pv < PvMax)
                    {
                        pv++;
                        j.Add(Un(h, Feux) + " (♥ +1)");
                    }
                    else j.Add(Un(h, Feux));
                    break;
            }
        }

        var r = new Resultat { Id = x.Id, Lieu = l.Id, Pv = Math.Max(0, pv), Fin = x.Fin, Boss = bossBattu };
        if (pv <= 0)
        {
            r.Issue = Denouement.Defaite;
            r.Xp = Math.Max(1, l.Xp / 3);
            j.Add(Un(h, Defaites));
        }
        else if (pv == 1 || (bossVu && !bossBattu))
        {
            r.Issue = Denouement.Partielle;
            r.Po = (int)Math.Round(po * 0.6);
            r.Xp = Math.Max(1, (int)Math.Round(l.Xp * 0.6));
            r.Fragments = fragments;
            j.Add(Un(h, Partielles).Replace("{po}", r.Po.ToString(CultureInfo.InvariantCulture)));
        }
        else
        {
            r.Issue = Denouement.Victoire;
            r.Po = po + l.PoVictoire;
            r.Xp = l.Xp;
            r.Fragments = fragments;
            // Butin exclusif : rare (quelques %), celui du lieu d'abord, sinon un autre pas encore possédé.
            if (Reel(h) < l.ChanceRare * (1 + bButin / 25.0))
            {
                var manquants = Exclusifs.Select(a => a.Id).Where(id => !possedes.Contains(id)).ToList();
                r.Objet = manquants.Contains(l.Exclusif) ? l.Exclusif : manquants.Count > 0 ? manquants[h.Suivant(manquants.Count)] : "";
                if (r.Objet == "") r.Fragments += 3;
            }
            if (bossBattu && !(trophees ?? Array.Empty<string>()).Contains(Trophee(l.Boss))) r.Trophee = Trophee(l.Boss);
            var fin = Un(h, Victoires).Replace("{po}", r.Po.ToString(CultureInfo.InvariantCulture));
            if (r.Objet != "") fin += $" Et dans le baluchon : {Minuscule(NomCourt(r.Objet))} !";
            else if (r.Trophee != "") fin += $" Trophée : {bossNom} ★";
            j.Add(fin);
        }
        r.Journal = j;
        return r;
    }

    public static string NomCourt(string id) => (Exclusif(id)?.Nom ?? id).Replace(" (butin d'expédition)", "");

    public static string NomIssue(Denouement i) => i switch
    {
        Denouement.Victoire => "victoire", Denouement.Partielle => "à moitié", Denouement.Defaite => "défaite", _ => "rappelé",
    };

    // Signe de forme de l'issue (pas de couleur seule) : ★ victoire, ◐ partielle, ✕ défaite, ↩ rappel.
    public static string SigneIssue(Denouement i) => i switch { Denouement.Victoire => "★", Denouement.Partielle => "◐", Denouement.Defaite => "✕", _ => "↩" };

    private static string Minuscule(string s) => s == "" ? s : char.ToLowerInvariant(s[0]) + s[1..];

    // « mon épée en bois », « ma lanterne », « mon parapluie ».
    private static string Mon(Outil o)
    {
        var nom = Minuscule(o.Nom);
        bool feminin = o.Id is "baguette" or "lanterne" or "canne-or" or "torche";
        return ("aeiouyéèêh".Contains(nom[0]) || !feminin ? "mon " : "ma ") + nom;
    }

    private static string Majuscule(string s) => s == "" ? s : char.ToUpperInvariant(s[0]) + s[1..];

    // « la Caverne des câbles », « le Marais… » : l'article qui va avec le lieu.
    public static string De(string nom) => nom switch
    {
        _ when nom.StartsWith("Caverne") || nom.StartsWith("Forêt") || nom.StartsWith("Tour") || nom.StartsWith("Citadelle") => "la " + nom,
        _ when nom.StartsWith("Marais") => "le " + nom,
        _ => nom,
    };

    // ---- Le journal (ton léger, tout est inventé)

    private static readonly string[] Departs =
    {
        "✦ Départ pour {lieu}, {arme} au clair.",
        "✦ En route pour {lieu} : baluchon, {arme} et un goûter.",
        "✦ Cap sur {lieu}. J'ai pris {arme}, au cas où.",
        "✦ Je file vers {lieu}, {arme} à la ceinture.",
    };

    private static readonly string[] CombatsGagnes =
    {
        "⚔ {Un} surgit d'un vieux connecteur. Trois coups de {arme} : rangé dans un ticket",
        "⚔ {Un} me barre la route. Je fais un pas de côté, et hop, c'est gagné",
        "⚔ Duel contre {un}. Plus de pattes que moi, mais moins d'aplomb",
        "⚔ {Un} voulait mon goûter. Reparti sans, et moi avec ses pièces",
        "⚔ {Un} attaque ! Mon plus beau regard sévère suffit : fuite",
    };

    private static readonly string[] CombatsPerdus =
    {
        "✕ {Un} m'a eu par surprise. Aïe",
        "✕ {Un} a répété la même attaque trois fois. Aïe aïe",
        "✕ J'ai glissé devant {un}, qui en a profité",
        "✕ {Un} m'a mordu le baluchon, puis le pied",
    };

    private static readonly string[] BossGagnes =
    {
        "★ Le chef des lieux : {un} énorme ! Découpé en petites sous-tâches",
        "★ Combat final contre {le}, qui s'effondre en messages d'erreur polis",
        "★ {Le} gronde, je souris, le doute s'installe. Victoire",
    };

    private static readonly string[] BossPerdus =
    {
        "✕ {Le} m'a assigné un problème bloquant. Repli stratégique",
        "✕ Trop costaud, {le}. Je note son point faible pour la prochaine fois",
        "✕ {Le} m'a renvoyé à l'entrée d'un souffle",
    };

    private static readonly string[] PiegesEvites =
    {
        "◇ Une dalle demande « Êtes-vous sûr ? ». J'ai répondu non : elle s'est rendormie.",
        "◇ Un fil tendu au ras du sol. Je l'ai enjambé sans même le relire.",
        "◇ Une boucle infinie dans le couloir : j'en suis sorti au deuxième tour.",
        "◇ Un piège à mise en veille. J'ai bougé la souris à temps.",
    };

    private static readonly string[] PiegesSubis =
    {
        "✕ Une boucle infinie au détour d'un couloir : j'ai tourné en rond un bon moment",
        "✕ Une trappe marquée « provisoire » depuis l'an dernier. J'y suis tombé",
        "✕ Une pluie de virgules oubliées. Ça pique",
        "✕ Un tapis roulant de notifications : il m'a emporté",
    };

    private static readonly string[] Coffres =
    {
        "▣ Un coffre entrouvert sous des câbles",
        "▣ Un coffre étiqueté « ne pas ouvrir ». Je l'ai ouvert",
        "▣ Un coffre caché derrière un rideau de poussière",
        "▣ Un petit coffre qui ronronnait. Dedans",
    };

    private static readonly string[] RencontresPo =
    {
        "☺ Un vieux curseur égaré m'indique un raccourci et me donne un pourboire",
        "☺ Un marchand de parenthèses me rachète un caillou tout lisse",
        "☺ Une tortue de mise à jour me double… et laisse tomber sa monnaie",
    };

    private static readonly string[] RencontresSoin =
    {
        "☺ Une fée du cache me refait une beauté",
        "☺ Un lutin de l'assistance me pose un pansement tout neuf",
    };

    private static readonly string[] RencontresDroles =
    {
        "☺ Un écho me demande si j'ai essayé de redémarrer. On a bien ri.",
        "☺ Un panneau indique « par ici » dans les deux sens. Je prends le troisième.",
        "☺ Une chauve-souris de ping fait l'aller-retour, encore et encore.",
    };

    private static readonly string[] Feux =
    {
        "☕ Feu de camp : une tasse de thé, les pieds au chaud",
        "☕ Petite sieste sous un rocher bien tiède",
        "☕ Pique-nique au bord d'un ruisseau de pixels",
    };

    private static readonly string[] Victoires =
    {
        "✓ Retour avec {po} po et pas une égratignure.",
        "✓ Mission accomplie : {po} po dans le baluchon.",
        "✓ Je rentre en héros, {po} po en poche.",
    };

    private static readonly string[] Partielles =
    {
        "◐ Je rentre avec {po} po et une jolie bosse.",
        "◐ À moitié réussi : {po} po, et des choses à raconter.",
    };

    private static readonly string[] Defaites =
    {
        "✕ Je rentre bredouille et un peu cabossé. La prochaine fois !",
        "✕ Retraite ! Rien dans le baluchon, mais j'ai appris des trucs.",
        "✕ Bon. On dira que c'était un repérage.",
    };

    // ---- Groupe et téléphone

    // Les autres appareils du groupe : départs du même jour (somme) et fin de repos (la plus tardive).
    public static ExpeditionsAutres Autres(IEnumerable<(string Jour, int Nombre, double Libre)> autres, DateTime local)
    {
        var jour = Quetes.CleJour(local);
        int n = 0;
        double libre = 0;
        foreach (var (j, nb, li) in autres)
        {
            if (j == jour) n += Math.Clamp(nb, 0, ParJour);
            libre = Math.Max(libre, li);
        }
        return new ExpeditionsAutres(n, libre);
    }

    // Ce que voit le téléphone (lecture seule) : énergie, expédition en cours, repos, dernier journal.
    public static Dictionary<string, object> PourTelephone(EtatExpedition e, double maintenant, DateTime local, ExpeditionsAutres autres)
    {
        var d = new Dictionary<string, object>
        {
            ["energie"] = Jauge.Affiche(e.Energie),
            ["reste"] = Restantes(e, local, autres),
            ["libre"] = LibreA(e, autres),
        };
        if (e.Courante is { } x)
        {
            d["etat"] = "en";
            d["lieu"] = Trouver(x.Lieu)?.Nom ?? x.Lieu;
            d["retour"] = x.Fin;
        }
        else d["etat"] = maintenant < LibreA(e, autres) ? "repos" : "pret";
        if (e.Dernier is { } r)
        {
            d["issue"] = r.Issue.ToString().ToLowerInvariant();
            d["dernier"] = Trouver(r.Lieu)?.Nom ?? r.Lieu;
            d["t"] = r.Fin;
            d["journal"] = r.Journal.Take(9).Select(s => s.Length > 110 ? s[..109] + "…" : s).ToList();
        }
        return d;
    }

    // « en expédition · Caverne des câbles · retour vers 15 h 40 ».
    public static string Ligne(EtatExpedition e, DateTime retourLocal) =>
        e.Courante is { } x ? $"en expédition · {Trouver(x.Lieu)?.Nom ?? x.Lieu} · retour vers {Amis.Heure(retourLocal)}" : "";
}
