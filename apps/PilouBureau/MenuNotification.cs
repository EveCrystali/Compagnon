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
}

public static class MenuNotification
{
    public const string Infobulle = "Pilou";

    // null : un trait de séparation. La première entrée est celle du clic gauche (en gras dans le menu).
    public static readonly IReadOnlyList<(ChoixNotification? Choix, string Texte)> Entrees = new (ChoixNotification?, string)[]
    {
        (ChoixNotification.Afficher, "Afficher / ramener Pilou"),
        (ChoixNotification.OuvrirMenu, "Ouvrir le menu de Pilou"),
        (null, ""),
        (ChoixNotification.MiseAJour, "Chercher une mise à jour"),
        (ChoixNotification.Redemarrer, "Redémarrer Pilou"),
        (null, ""),
        (ChoixNotification.Quitter, "Quitter Pilou"),
    };

    // Le numéro rendu par TrackPopupMenu (0 : menu fermé sans choix).
    public static ChoixNotification? Lire(int id) =>
        Enum.IsDefined(typeof(ChoixNotification), id) ? (ChoixNotification)id : null;
}
