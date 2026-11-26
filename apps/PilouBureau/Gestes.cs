namespace PilouBureau;

// Petits gestes de Pilou (sans WPF : testables) : il tape au clavier avec toi, il prend une photo quand tu
// fais une capture d'écran. Les crochets Windows qui les déclenchent sont dans Crochets.cs.

// Compteur de frappes. CONFIDENTIALITÉ : il ne reçoit qu'un instant (« une touche a été relâchée à t ») ;
// aucune touche, aucun caractère, aucun code n'entre ici, rien n'est écrit sur disque ni journalisé.
// Seuls les instants des 5 dernières secondes restent en mémoire, pour savoir si tu tapes en rafale.
public sealed class CompteurFrappes
{
    public const double Fenetre = 5000;   // ms
    public const int Seuil = 20;          // frappes dans la fenêtre pour parler de rafale (4 par seconde)

    private readonly Queue<double> _instants = new();

    // Instant de la dernière frappe (ms), -∞ s'il n'y en a jamais eu.
    public double Derniere { get; private set; } = double.NegativeInfinity;

    public void Frappe(double t)
    {
        _instants.Enqueue(t);
        Derniere = t;
        Purger(t);
    }

    public int Recentes(double t)
    {
        Purger(t);
        return _instants.Count;
    }

    public bool Rafale(double t) => Recentes(t) >= Seuil;

    public double Silence(double t) => t - Derniere;

    private void Purger(double t)
    {
        while (_instants.Count > 0 && t - _instants.Peek() > Fenetre) _instants.Dequeue();
        // Jamais plus que nécessaire en mémoire, même si quelqu'un tape très vite.
        while (_instants.Count > 4 * Seuil) _instants.Dequeue();
    }
}

public enum EtapeClavier { Aucune, Entree, Tape, Sortie }

// Ce que la scène doit dessiner pour un geste à un instant donné.
public sealed record DessinGeste(IReadOnlyList<string> Objets, int Regard = 0, bool Dos = false, double Assis = 0,
    bool Concentre = false, double Flash = 0, string Bruit = "", int RegardY = 0)
{
    public static readonly DessinGeste Rien = new(Array.Empty<string>());
}

// Pilou au clavier : un tour sur lui-même dans un pouf de fumée, il réapparaît assis devant un mini clavier
// et tape avec toi quelques dizaines de secondes au plus : après 6 s de silence, ou au bout de 40 s même si
// tu tapes encore, pouf inverse et il se relève (sinon, pendant une journée de travail, il ne s'arrête jamais).
// Pas à chaque rafale : après une séance, il se repose 10 min avant de revenir au clavier.
public sealed class SceneClavier
{
    public const double DureeEntree = 1300, DureeSortie = 800, SilenceSortie = 6000;
    public const double DureeMax = 40_000;
    public const double ReposApres = 10 * 60_000;
    // Une image du tour sur lui-même (ms) : un tour lent, sans tourbillon.
    public const double PasTour = 130;

    public EtapeClavier Etape { get; private set; } = EtapeClavier.Aucune;
    private double _debut;
    private double _libreA = double.NegativeInfinity;

    // Essai (--essai=clavier) : la séance part tout de suite, repos ou pas.
    public void OublierRepos() => _libreA = double.NegativeInfinity;

    public bool Active => Etape != EtapeClavier.Aucune;

    // Renvoie vrai quand Pilou vient d'entrer en scène (une « séance » de frappe commence).
    // permis : l'option est cochée et rien ne s'y oppose (plein écran, visite, mini-jeu, IA qui attend…).
    public bool Avancer(double t, bool rafale, double silence, bool permis)
    {
        switch (Etape)
        {
            case EtapeClavier.Aucune:
                if (permis && rafale && t >= _libreA)
                {
                    Etape = EtapeClavier.Entree;
                    _debut = t;
                    return true;
                }
                break;
            case EtapeClavier.Entree:
                if (!permis) Sortir(t);
                else if (t - _debut >= DureeEntree)
                {
                    Etape = EtapeClavier.Tape;
                    _debut = t;
                }
                break;
            case EtapeClavier.Tape:
                if (!permis || silence >= SilenceSortie || t - _debut >= DureeMax) Sortir(t);
                break;
            case EtapeClavier.Sortie:
                if (t - _debut >= DureeSortie)
                {
                    Etape = EtapeClavier.Aucune;
                    _libreA = t + ReposApres;
                }
                break;
        }
        return false;
    }

    private void Sortir(double t)
    {
        Etape = EtapeClavier.Sortie;
        _debut = t;
    }

    // Tour sur lui-même : face, profil droit, dos, profil gauche, une image toutes les 130 ms.
    private static (int Regard, bool Dos) Tour(double ms) => ((int)(ms / PasTour) % 4) switch
    {
        0 => (1, false),
        1 => (0, true),
        2 => (-1, false),
        _ => (0, false),
    };

    public DessinGeste Dessin(double t)
    {
        double ms = t - _debut;
        switch (Etape)
        {
            case EtapeClavier.Entree:
            {
                double p = Math.Clamp(ms / DureeEntree, 0, 1);
                if (p < 0.6)
                {
                    var (r, dos) = Tour(ms);
                    var pouf = p < 0.15 ? "pouf-1" : p < 0.3 ? "pouf-2" : "pouf-3";
                    return new DessinGeste(new[] { pouf }, r, dos);
                }
                return new DessinGeste(new[] { "clavier-mini", p < 0.8 ? "pouf-4" : "pouf-5" }, Assis: 1, Concentre: true);
            }
            case EtapeClavier.Tape:
                return new DessinGeste(new[] { "clavier-mini" }, Assis: 1, Concentre: true);
            case EtapeClavier.Sortie:
            {
                double q = Math.Clamp(ms / DureeSortie, 0, 1);
                if (q < 0.25) return new DessinGeste(new[] { "clavier-mini", "pouf-2" }, Assis: 1, Concentre: true);
                if (q < 0.45) return new DessinGeste(new[] { "clavier-mini", "pouf-3" }, Assis: 1);
                var (r, dos) = q < 0.7 ? Tour(ms) : (0, false);
                return new DessinGeste(new[] { q < 0.7 ? "pouf-3" : q < 0.85 ? "pouf-4" : "pouf-5" }, r, dos);
            }
            default:
                return DessinGeste.Rien;
        }
    }
}

// D'où vient le signal de capture d'écran (aucun ne lit ni ne copie l'image).
public enum SourceCapture { ImprEcran, PressePapiers, Dossier, Essai }

// Une capture d'écran se signale souvent trois fois (touche Impr. écran, image dans le presse-papiers,
// fichier dans Captures d'écran) : une seule animation par capture, les signaux des 2 s suivantes sont
// des échos de la même.
public sealed class AntiDoublon
{
    public const double Fenetre = 2000;
    private double _derniere = double.NegativeInfinity;

    public bool Accepter(double t)
    {
        if (t - _derniere < Fenetre) return false;
        _derniere = t;
        return true;
    }
}

// Pilou photographe : il sort son appareil, flash (cadre blanc bref), « clic ! », un polaroïd tombe, il range.
// Au plus une photo toutes les 2 min : les captures en série ne relancent pas la scène.
public sealed class ScenePhoto
{
    public const double Duree = 3000, Repos = 120_000, DureeFlash = 150;
    private double _debut = double.NegativeInfinity;

    public bool Active(double t) => t - _debut < Duree;

    // Renvoie vrai si la scène démarre (ni en cours, ni dans les 2 min qui suivent la précédente).
    public bool Declencher(double t)
    {
        if (t - _debut < Repos) return false;
        _debut = t;
        return true;
    }

    public void Arreter() => _debut = double.NegativeInfinity;

    public DessinGeste Dessin(double t)
    {
        double ms = t - _debut;
        if (ms < 0 || ms >= Duree) return DessinGeste.Rien;
        string[] Avec(params string[] o) => o;
        if (ms < 450) return new DessinGeste(Avec("appareil-photo"), Concentre: true);
        if (ms < 450 + DureeFlash)
        {
            // Flash : retombe en 150 ms ; jamais plein blanc (Scene le dessine en cadre fin, très atténué).
            double f = 1 - (ms - 450) / DureeFlash;
            return new DessinGeste(Avec("appareil-photo", "photo-flash"), Concentre: true, Flash: f, Bruit: "CLIC !");
        }
        if (ms < 1150) return new DessinGeste(Avec("appareil-photo", "polaroid-1"), Bruit: "CLIC !");
        if (ms < 1550) return new DessinGeste(Avec("appareil-photo", "polaroid-2"));
        if (ms < 1950) return new DessinGeste(Avec("polaroid-3"));
        return new DessinGeste(Avec("polaroid-4"));
    }
}

public static class GestesPilou
{
    // Pendant un geste, les objets « en main » de la tenue d'activité (manette, calculatrice, clavier de la
    // tenue code…) laissent la place ; lunettes, chapeaux et écouteurs restent. Renvoie les sprites à garder.
    public static List<string> TenueCompatible(IEnumerable<string> tenue, Func<string, string?> slot) =>
        tenue.Where(id => slot(id) is not ("main" or "objet")).ToList();
}
