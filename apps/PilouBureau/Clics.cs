namespace PilouBureau;

// Règles de clic, sans WPF (testées dans tests/ClicsTests.cs) : zones de clic des petits jeux, fenêtres de temps,
// différence entre un clic court et un glisser de Pilou, fermeture du menu clic droit quand on clique ailleurs.
public static class Clics
{
    // Une zone en unités de la fenêtre de Pilou (avant mise à l'échelle) ou en pixels d'écran, selon l'usage.
    public readonly record struct Zone(double X, double Y, double Largeur, double Hauteur)
    {
        public Zone Elargie(double marge) => new(X - marge, Y - marge, Largeur + 2 * marge, Hauteur + 2 * marge);

        public bool Contient(double x, double y) => x >= X && x <= X + Largeur && y >= Y && y <= Y + Hauteur;
    }

    // Marge cliquable autour de chaque élément de jeu (étoile, bulle, main, bouchon, marmite) : un clic « à côté » compte.
    public const double MargeCible = 18;

    // Durées des jeux (ms), un peu plus longues qu'avant : on n'a pas toujours la souris sous la main.
    public const double DureeEtoile = 12_000;
    public const double DureeTapeCinq = 7_000;
    // Les bulles montent moins vite (unités par seconde) : on a le temps de les viser.
    public const double VitesseBulles = 16;

    // Pêche : une fois le « ! » apparu, on a 1,8 s pour ferrer ; un clic juste avant (réflexe) compte aussi.
    public const double FenetreMorsure = 1_800;
    public const double Anticipation = 200;
    // Trop tôt : pas de pénalité les deux premières fois ; au troisième clic trop tôt, le poisson file.
    public const int FuiteApres = 3;

    public enum Ferrage { Attendre, Ferre, TropTard }

    // Jugement d'un clic de pêche à l'instant de l'appui (MouseDown), pas du relâché.
    public static Ferrage Juger(double tAppui, double mordA, double fenetre = FenetreMorsure) =>
        tAppui < mordA - Anticipation ? Ferrage.Attendre
        : tAppui < mordA + fenetre ? Ferrage.Ferre
        : Ferrage.TropTard;

    public static bool Mord(double t, double mordA, double fenetre = FenetreMorsure) => t >= mordA && t < mordA + fenetre;

    // Un clic sur Pilou lui-même compte pour ces jeux-là (tape m'en cinq, ferrer, remuer la marmite) ;
    // l'étoile et les bulles se visent (avec la marge), sinon un clic sur Pilou reste une caresse.
    public static bool ClicSurPilouCompte(string jeu) => jeu is "tape" or "peche" or "cuisine";

    // Glisser de Pilou : au-delà de 10 unités, ou plus de 4 en gardant le bouton plus de 350 ms.
    // En dessous, c'est un clic (caresse ou coup de jeu), même si la main a un peu bougé.
    public const double SeuilGlisser = 10;
    public const double SeuilLent = 4;
    public const double DureeLente = 350;

    public static bool EstGlisser(double distance, double dureeMs) =>
        distance > SeuilGlisser || (distance > SeuilLent && dureeMs > DureeLente);

    // Menu clic droit ouvert : on le ferme si un bouton de souris vient d'être enfoncé (front montant)
    // hors du menu et de ses sous-menus, ou si le focus, qu'il avait reçu, est parti dans une autre appli.
    public static bool FermerMenu(bool basAvant, bool basMaintenant, bool sourisDansMenu, bool aEuLeFocus, bool focusChezNous) =>
        (basMaintenant && !basAvant && !sourisDansMenu) || (aEuLeFocus && !focusChezNous);

    public static bool DansUne(IEnumerable<Zone> zones, double x, double y) => zones.Any(z => z.Contient(x, y));
}
