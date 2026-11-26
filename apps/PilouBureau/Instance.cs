namespace PilouBureau;

// Ce que demande la ligne de commande, et ce qu'on fait quand un autre Pilou tourne déjà (sans Windows : testable).
public enum ModeLancement
{
    Signal,     // --signal <source> … : un événement à déposer, puis on rend la main
    Brancher,   // --brancher / --debrancher <outil>
    Essai,      // --instantane=, --film=, --essai= : un Pilou d'essai, à côté de l'instance habituelle
    Principal,  // Pilou habituel (une seule instance)
}

public sealed record Lancement(ModeLancement Mode, bool Redemarrer, bool ApresMaj)
{
    public static Lancement Analyser(IReadOnlyList<string> args)
    {
        if (args.Contains("--signal")) return new(ModeLancement.Signal, false, false);
        if (args.Count >= 2 && args[0] is "--brancher" or "--debrancher") return new(ModeLancement.Brancher, false, false);
        bool essai = args.Any(a => a.StartsWith("--instantane=") || a.StartsWith("--film=") || a.StartsWith("--essai="));
        if (essai) return new(ModeLancement.Essai, false, false);
        return new(ModeLancement.Principal, args.Contains("--redemarrer"), args.Contains("--apres-maj"));
    }

    // Ce qui reste une fois retirées les options d'instance (--apres-maj, --redemarrer).
    public static string[] Reste(IEnumerable<string> args) => args.Where(a => a is not "--apres-maj" and not "--redemarrer").ToArray();
}

// L'autre Pilou, vu d'ici : le verrou commun (mutex nommé) et la fenêtre relais qui lui transmet nos demandes.
public interface IAutreInstance
{
    bool Prendre();                    // le verrou est libre : on le prend
    bool Attendre(TimeSpan delai);     // attend que l'autre le rende (il quitte)
    bool DemanderAfficher();           // « montre-toi » ; faux si l'autre ne répond pas (introuvable ou figé)
    bool DemanderQuitter();            // « quitte proprement » ; faux s'il ne répond pas
    void Forcer();                     // arrête de force les autres processus de Pilou
}

public enum Issue
{
    Demarrer, // on devient le Pilou
    Rendre,   // un autre Pilou s'en charge : on quitte tout de suite
}

public static class Instance
{
    public static readonly TimeSpan AttenteMaj = TimeSpan.FromSeconds(15);
    public static readonly TimeSpan AttenteQuitter = TimeSpan.FromSeconds(10);
    public static readonly TimeSpan AttenteForce = TimeSpan.FromSeconds(5);

    // Relancer l'exe quand Pilou tourne : il se montre, rien de plus. S'il ne répond plus (figé), on le remplace :
    // relancer marche toujours, même quand le menu de l'overlay ne s'ouvre plus.
    public static Issue Decider(Lancement l, IAutreInstance autre)
    {
        if (autre.Prendre()) return Issue.Demarrer;
        if (l.ApresMaj)
            return autre.Attendre(AttenteMaj) || Remplacer(autre) ? Issue.Demarrer : Issue.Rendre;
        if (l.Redemarrer)
            return autre.DemanderQuitter() && autre.Attendre(AttenteQuitter) || Remplacer(autre) ? Issue.Demarrer : Issue.Rendre;
        if (autre.DemanderAfficher()) return Issue.Rendre;
        return Remplacer(autre) ? Issue.Demarrer : Issue.Rendre;
    }

    private static bool Remplacer(IAutreInstance autre)
    {
        autre.Forcer();
        return autre.Attendre(AttenteForce);
    }
}
