namespace PilouBureau;

// Le petit menu de l'icône près de l'horloge (ZoneNotification.cs) : la porte de secours, indépendante du menu
// clic droit de l'overlay. Rien que du texte et des numéros ici (testable sans Windows).
public enum ChoixNotification
{
    Afficher = 1,
    OuvrirMenu = 2,
    MiseAJour = 3,
    Redemarrer = 4,
    Quitter = 5,
    Expedition = 6,
    Defense = 7,
    Aventure = 8,
}

public static class MenuNotification
{
    public const string Infobulle = "Pilou, ton petit compagnon de bureau";

    // null : un trait de séparation. La première entrée est celle du clic gauche (en gras dans le menu).
    public static readonly IReadOnlyList<(ChoixNotification? Choix, string Texte)> Entrees = new (ChoixNotification?, string)[]
    {
        (ChoixNotification.Afficher, "Afficher / ramener Pilou"),
        (ChoixNotification.OuvrirMenu, "Ouvrir le menu de Pilou"),
        (ChoixNotification.Aventure, "Aventure…"),
        (ChoixNotification.Expedition, "Partir en expédition…"),
        (ChoixNotification.Defense, "Jouer à Défense du bureau"),
        (null, ""),
        (ChoixNotification.MiseAJour, "Chercher une mise à jour"),
        (ChoixNotification.Redemarrer, "Redémarrer Pilou"),
        (null, ""),
        (ChoixNotification.Quitter, "Quitter Pilou"),
    };

    // Le texte d'une entrée : celui de la liste, ou l'état de l'aventure (« Aventure… (en route · 12 min) »,
    // « Aventure… (! il t'attend) ») que donne Pilou. Jamais de « & » (il soulignerait une lettre).
    public static string Texte(ChoixNotification choix, string texte, string? aventure) =>
        (choix == ChoixNotification.Aventure && !string.IsNullOrWhiteSpace(aventure) ? aventure! : texte).Replace("&", "et");

    // Le numéro rendu par TrackPopupMenu (0 : menu fermé sans choix).
    public static ChoixNotification? Lire(int id) =>
        Enum.IsDefined(typeof(ChoixNotification), id) ? (ChoixNotification)id : null;
}
