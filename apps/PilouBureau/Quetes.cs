using System.Globalization;

namespace PilouBureau;

// Quêtes de Pilou : 3 quotidiennes (minuit), 3 hebdomadaires (lundi), 1 du mois. Tirées de la date et de
// l'identifiant de l'appareil (même jour, même appareil → mêmes quêtes). Elles avancent par des signaux :
// Signaler("peche", 1), Signaler("activite:code", 15)… Réussies, elles rapportent des pièces d'or (po) et
// un peu d'XP ; les trois quotidiennes faites ouvrent un coffre, et les jours d'affilée font une série.
public enum Periode { Jour, Semaine, Mois }

public enum Mesure { Somme, Max }

// Une sorte de quête. Texte : {0} = objectif, {s} = « s » au pluriel, {x} = « x » au pluriel.
// Jour/Semaine/Mois : [min, max] de l'objectif, vide si la quête n'existe pas pour cette période.
// Toujours : proposée même si l'appareil n'a jamais vu ce signal (pêche, jeux…) ; sinon, seulement après
// un premier signal (pas de quête Codex pour qui n'a pas Codex, pas de Chasse aux bugs sans téléphone).
public sealed record Modele(string Cle, string Texte, Mesure Mesure, int[] Jour, int[] Semaine, int[] Mois, bool Toujours, int Pas = 1);

public sealed class Quete
{
    public string Id { get; set; } = "";
    public string Cle { get; set; } = "";
    public string Texte { get; set; } = "";
    public Periode Periode { get; set; }
    public int Objectif { get; set; }
    public int Fait { get; set; }
    public int Po { get; set; }
    public int Xp { get; set; }
    public bool Reussie { get; set; }
    // Quête bonus (météo) : ajoutée en cours de journée, elle ne compte pas pour le coffre du jour.
    public bool Bonus { get; set; }
}

public sealed class EtatQuetes
{
    public string Jour { get; set; } = "";
    public string Semaine { get; set; } = "";
    public string Mois { get; set; } = "";
    public List<Quete> Liste { get; set; } = new();
    // Signaux déjà vus au moins une fois sur cet appareil (ouvrent les quêtes « optionnelles »).
    public List<string> Vues { get; set; } = new();
    public int Serie { get; set; }
    public string DernierJourComplet { get; set; } = "";
    public string CoffreJour { get; set; } = "";
    public int Reussies { get; set; }
}

public sealed record RecompenseQuete(string Texte, int Po, int Xp, bool Coffre);

public static class Quetes
{
    public static readonly IReadOnlyList<Modele> Modeles = new Modele[]
    {
        new("tour", "Finis {0} tour{s} avec Claude ou Codex", Mesure.Somme, [3, 8], [20, 40], [100, 150], false),
        new("commit", "Fête {0} commit{s}", Mesure.Somme, [1, 3], [5, 12], [], false),
        new("tests", "Fais passer les tests {0} fois", Mesure.Somme, [1, 3], [5, 10], [], false),
        new("peche", "Pêche {0} prise{s}", Mesure.Somme, [2, 5], [10, 20], [40, 60], true),
        new("peche:rare", "Attrape {0} prise{s} rare{s} ou mieux", Mesure.Somme, [1, 1], [2, 4], [8, 12], true),
        new("cuisine", "Cuisine {0} plat{s}", Mesure.Somme, [1, 3], [5, 10], [25, 35], true),
        new("cuisine:nouveau", "Découvre {0} nouveau{x} plat{s}", Mesure.Somme, [], [1, 3], [5, 8], true),
        new("jeu", "Gagne {0} petit{s} jeu{x}", Mesure.Somme, [2, 4], [10, 15], [], true),
        new("caresse", "Caresse Pilou {0} fois", Mesure.Somme, [3, 6], [], [], true),
        new("soin", "Prends soin de Pilou {0} fois", Mesure.Somme, [], [2, 4], [], true),
        // Après une première visite chez un ami (Amis) : pas de quête de visite pour qui n'a pas d'amis.
        new("visite", "Rends visite à un ami ({0} fois)", Mesure.Somme, [1, 1], [2, 4], [], false),
        new("presence", "Passe {0} min avec Pilou", Mesure.Somme, [60, 180], [600, 1200], [2400, 3600], true, 30),
        new("agenda:ponctuel", "Sois à l'heure à {0} réunion{s}", Mesure.Somme, [1, 2], [3, 6], [], false),
        new("chasse","Atteins {0} points à Chasse aux bugs", Mesure.Max, [800, 2000], [3000, 6000], [], false, 100),
        new("activite:code", "Code pendant {0} min", Mesure.Somme, [30, 120], [300, 600], [1500, 2400], false, 15),
        new("activite:tableur", "Travaille {0} min sur un tableur", Mesure.Somme, [20, 60], [120, 300], [], false, 10),
        new("activite:musique", "Écoute {0} min de musique", Mesure.Somme, [30, 90], [240, 480], [], false, 15),
        new("activite:jeu", "Joue {0} min à un jeu vidéo", Mesure.Somme, [30, 90], [240, 480], [], false, 15),
    };

    // Récompenses (po) par période : de la quête la plus facile à la plus dure.
    private static (int Min, int Max) Bareme(Periode p) => p switch
    {
        Periode.Jour => (20, 40),
        Periode.Semaine => (90, 150),
        _ => (300, 400),
    };

    private static int Nombre(Periode p) => p == Periode.Mois ? 1 : 3;

    public static string CleJour(DateTime local) => local.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);

    // La semaine commence le lundi.
    public static string CleSemaine(DateTime local)
    {
        int decalage = ((int)local.DayOfWeek + 6) % 7;
        return "S" + local.Date.AddDays(-decalage).ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);
    }

    public static string CleMois(DateTime local) => local.ToString("yyyy-MM", CultureInfo.InvariantCulture);

    // Fin de la période (pour « encore 5 h »).
    public static DateTime Fin(Periode p, DateTime local) => p switch
    {
        Periode.Jour => local.Date.AddDays(1),
        Periode.Semaine => local.Date.AddDays(7 - ((int)local.DayOfWeek + 6) % 7),
        _ => new DateTime(local.Year, local.Month, 1).AddMonths(1),
    };

    public static string Texte(Modele m, int objectif) =>
        m.Texte.Replace("{0}", objectif.ToString(CultureInfo.InvariantCulture))
            .Replace("{s}", objectif > 1 ? "s" : "").Replace("{x}", objectif > 1 ? "x" : "");

    private static int[] Plage(Modele m, Periode p) => p switch { Periode.Jour => m.Jour, Periode.Semaine => m.Semaine, _ => m.Mois };

    // Tirage des quêtes d'une période (pur : même graine, même période → mêmes quêtes).
    public static List<Quete> Tirer(Periode p, string clePeriode, string graine, IReadOnlyCollection<string> vues)
    {
        var h = new Hasard(Hasard.Graine($"quetes|{graine}|{clePeriode}"));
        var pool = Modeles.Where(m => Plage(m, p).Length == 2 && (m.Toujours || vues.Contains(m.Cle))).ToList();
        var (bmin, bmax) = Bareme(p);
        var r = new List<Quete>();
        for (int n = 0; n < Nombre(p) && pool.Count > 0; n++)
        {
            var m = pool[h.Suivant(pool.Count)];
            pool.Remove(m);
            var plage = Plage(m, p);
            int objectif = h.Entre(plage[0], plage[1]);
            if (m.Pas > 1) objectif = Math.Max(m.Pas, (int)Math.Round(objectif / (double)m.Pas) * m.Pas);
            double difficulte = plage[1] == plage[0] ? 0.5 : (objectif - plage[0]) / (double)(plage[1] - plage[0]);
            int po = (int)Math.Round(bmin + Math.Clamp(difficulte, 0, 1) * (bmax - bmin));
            r.Add(new Quete
            {
                Id = $"{clePeriode}:{m.Cle}",
                Cle = m.Cle,
                Texte = Texte(m, objectif),
                Periode = p,
                Objectif = objectif,
                Po = po,
                Xp = Math.Max(2, po / 5),
            });
        }
        return r;
    }

    // Nouvelle journée, semaine ou mois : les quêtes de la période échue laissent place à de nouvelles.
    public static void Actualiser(EtatQuetes e, DateTime local, string graine)
    {
        void Periode1(Periode p, string cle, Func<EtatQuetes, string> lire, Action<EtatQuetes, string> ecrire)
        {
            if (lire(e) == cle && e.Liste.Any(q => q.Periode == p)) return;
            e.Liste.RemoveAll(q => q.Periode == p);
            e.Liste.AddRange(Tirer(p, cle, graine, e.Vues));
            ecrire(e, cle);
        }
        Periode1(Periode.Jour, CleJour(local), x => x.Jour, (x, v) => x.Jour = v);
        Periode1(Periode.Semaine, CleSemaine(local), x => x.Semaine, (x, v) => x.Semaine = v);
        Periode1(Periode.Mois, CleMois(local), x => x.Mois, (x, v) => x.Mois = v);
        e.Liste = e.Liste.OrderBy(q => q.Periode).ToList();
    }

    // Série en cours : jours d'affilée où le coffre a été ouvert (hier ou aujourd'hui compris).
    public static int Serie(EtatQuetes e, DateTime local)
    {
        var aujourdhui = CleJour(local);
        var hier = CleJour(local.AddDays(-1));
        return e.DernierJourComplet == aujourdhui || e.DernierJourComplet == hier ? e.Serie : 0;
    }

    // Un signal fait avancer les quêtes qui l'attendent ; renvoie les récompenses gagnées (à créditer).
    public static List<RecompenseQuete> Signaler(EtatQuetes e, string cle, int quantite, DateTime local, string graine)
    {
        var gains = new List<RecompenseQuete>();
        if (string.IsNullOrWhiteSpace(cle) || quantite <= 0) return gains;
        if (!e.Vues.Contains(cle)) e.Vues.Add(cle);
        Actualiser(e, local, graine);
        var mesure = Modeles.FirstOrDefault(m => m.Cle == cle)?.Mesure ?? Mesure.Somme;
        foreach (var q in e.Liste.Where(q => q.Cle == cle && !q.Reussie))
        {
            q.Fait = mesure == Mesure.Max ? Math.Max(q.Fait, quantite) : q.Fait + quantite;
            if (q.Fait < q.Objectif) continue;
            q.Fait = q.Objectif;
            q.Reussie = true;
            e.Reussies++;
            gains.Add(new RecompenseQuete(q.Texte, q.Po, q.Xp, false));
        }
        var jour = CleJour(local);
        var quotidiennes = e.Liste.Where(q => q.Periode == Periode.Jour && !q.Bonus).ToList();
        if (gains.Count > 0 && quotidiennes.Count > 0 && quotidiennes.All(q => q.Reussie) && e.CoffreJour != jour)
        {
            e.CoffreJour = jour;
            e.Serie = e.DernierJourComplet == CleJour(local.AddDays(-1)) ? e.Serie + 1 : 1;
            e.DernierJourComplet = jour;
            int po = 40 + 10 * Math.Min(e.Serie, 7);
            gains.Add(new RecompenseQuete($"Coffre du jour · série de {e.Serie} jour{(e.Serie > 1 ? "s" : "")}", po, 10, true));
        }
        return gains;
    }

    // Quête météo bonus : proposée une fois par jour quand le temps s'y prête (pluie, froid, canicule).
    // Renvoie la quête ajoutée, ou null (déjà là, ou temps sans quête).
    public static Quete? AjouterMeteo(EtatQuetes e, string etat, DateTime local, string graine)
    {
        Actualiser(e, local, graine);
        if (Meteo.Quete(etat) is not { } m) return null;
        var jour = CleJour(local);
        var id = $"{jour}:{m.Cle}";
        if (e.Liste.Any(q => q.Id == id)) return null;
        var q = new Quete
        {
            Id = id, Cle = m.Cle, Texte = m.Texte, Periode = Periode.Jour, Objectif = m.Objectif, Po = m.Po, Xp = Math.Max(2, m.Po / 5),
            Bonus = true,
        };
        e.Liste.Add(q);
        e.Liste = e.Liste.OrderBy(x => x.Periode).ToList();
        return q;
    }

    // Crédite les récompenses au profil de cet appareil : po gagnées, XP. Renvoie les totaux.
    public static (int Po, int Xp) Appliquer(Profil p, IEnumerable<RecompenseQuete> recompenses)
    {
        int po = 0, xp = 0;
        foreach (var r in recompenses)
        {
            po += r.Po;
            xp += r.Xp;
        }
        p.Bourse.PoGagnes += po;
        p.Xp += xp;
        return (po, xp);
    }

    public static string Signe(Periode p) => p switch { Periode.Jour => "◔", Periode.Semaine => "◑", _ => "●" };

    public static string NomPeriode(Periode p) => p switch { Periode.Jour => "Du jour", Periode.Semaine => "De la semaine", _ => "Du mois" };

    // « encore 5 h » / « encore 3 j ».
    public static string Reste(Periode p, DateTime local)
    {
        var d = Fin(p, local) - local;
        return d.TotalHours < 1 ? $"encore {Math.Max(1, (int)d.TotalMinutes)} min"
            : d.TotalHours < 48 ? $"encore {(int)d.TotalHours} h"
            : $"encore {(int)d.TotalDays} j";
    }
}
