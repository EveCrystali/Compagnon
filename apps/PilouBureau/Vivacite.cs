namespace PilouBureau;

// Dosage de la vivacité de Pilou (sans WPF : testable). Il reste d'abord passif : ses réactions « cosmétiques »
// (petite phrase quand l'activité change, « ça chauffe ! », « hmpf », plainte météo, tête qui tourne, petit jeu
// proposé…) ne partent pas à chaque fois, jamais pendant que tu tapes, et au plus une toutes les quelques minutes.
// Les signaux utiles (une IA t'attend, « ✓ fini », statuts des sessions) ne passent JAMAIS par ici.
// Réglage interne, sans mode ni curseur : les cases on/off existantes suffisent.
public static class Vivacite
{
    // Chance qu'une réaction cosmétique parte quand l'occasion se présente.
    public const double Chance = 0.5;
    // Temps de repos commun entre deux réactions cosmétiques (ms).
    public const double Repos = 150_000;
    // Dernière frappe il y a moins de ça : saisie en cours, pas de réaction (ms).
    public const double Saisie = 4000;
    // Clavier ou souris touchés il y a moins de ça : tu travailles, il bouge moins (ms).
    public const double Actif = 20_000;
    // Jeux spontanés au repos : intervalles allongés d'autant.
    public const double EspacementJeux = 1.75;

    // Applis de travail : au premier plan, Pilou se fait plus discret (moins de déplacements, plus lents).
    public static readonly string[] Travail = { "code", "tableur", "texte", "mail", "diaporama", "lecture", "dessin" };

    // Tu travailles : une frappe ou un geste de souris récent, ou une appli de travail au premier plan.
    public static bool AuTravail(double inactifMs, string activite) =>
        inactifMs < Actif || Array.IndexOf(Travail, activite) >= 0;

    // Saisie en cours : une frappe il y a moins de 4 s. Sans crochet clavier (cases clavier et photo décochées),
    // on ne voit que l'inactivité globale : une entrée de moins de 2 s en tient lieu.
    public static bool EnSaisie(double silenceFrappes, bool crochet, double inactifMs) =>
        crochet ? silenceFrappes < Saisie : inactifMs < 2000;
}

// Le temps de repos commun aux réactions cosmétiques, avec sa part de hasard (Random injecté pour les tests).
public sealed class Retenue
{
    private readonly Random _hasard;
    private readonly double _chance, _repos;

    public Retenue(Random hasard, double chance = Vivacite.Chance, double repos = Vivacite.Repos)
    {
        _hasard = hasard;
        _chance = chance;
        _repos = repos;
    }

    // Instant de la dernière réaction cosmétique (ms), -∞ s'il n'y en a pas encore eu.
    public double Derniere { get; private set; } = double.NegativeInfinity;

    // Le repos est-il fini (et personne ne tape) ? Ne tire pas au sort, ne consomme rien.
    public bool Libre(double t, bool saisie) => !saisie && t - Derniere >= _repos;

    // Une occasion de réagir : vrai (et le repos repart) si le repos est fini, que personne ne tape, et que le
    // tirage tombe bien. Une occasion manquée ne consomme pas le repos.
    public bool Tenter(double t, bool saisie)
    {
        if (!Libre(t, saisie)) return false;
        if (_hasard.NextDouble() >= _chance) return false;
        Derniere = t;
        return true;
    }

    // Une réaction partie sans tirage (un jeu proposé à heure dite…) : le repos repart quand même.
    public void Noter(double t) => Derniere = t;
}
