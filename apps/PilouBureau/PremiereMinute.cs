namespace PilouBureau;

// La première minute (décision d'Antoine : pas de didacticiel, rien à cliquer) : au tout premier lancement, trois
// bulles au plus, de la voix de Pilou, espacées, qui passent seules. Une seule fois (Reglages.BienvenueFaite).
// Jamais pendant la saisie ni quand Pilou est caché ou occupé : la bulle attend son moment, puis abandonne.
public static class PremiereMinute
{
    public readonly record struct Mot(string Texte, double ApresMs, double DureeMs);

    // ApresMs : délai depuis la bulle précédente (la première : depuis le lancement).
    public static readonly IReadOnlyList<Mot> Mots = new Mot[]
    {
        new(Reglages.MotBienvenue, 4_000, 9_000),
        new("clic gauche : une caresse. clic droit : tout le reste. c'est tout, je suis une goutte simple", 40_000, 9_000),
        new("je sais écrire, presque. quand tu veux une histoire : clic droit, aventure ✉", 60_000, 9_000),
    };

    // Au-delà, une bulle qui n'a pas trouvé de moment calme est oubliée (et les suivantes avec) : mieux vaut se taire.
    public const double PatienceMs = 10 * 60_000;

    public enum Decision { Attendre, Dire, Abandonner }

    // depuis : temps écoulé depuis la bulle précédente (ou le lancement) ; libre : ni saisie, ni caché, ni occupé.
    public static Decision Decider(int prochaine, double depuis, bool libre)
    {
        if (prochaine >= Mots.Count) return Decision.Abandonner;
        var m = Mots[prochaine];
        if (depuis < m.ApresMs) return Decision.Attendre;
        if (depuis > m.ApresMs + PatienceMs) return Decision.Abandonner;
        return libre ? Decision.Dire : Decision.Attendre;
    }
}
