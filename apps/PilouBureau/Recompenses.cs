namespace PilouBureau;

public enum Couleur { Bleu, Nuit, Ambre, Argent, Aurore }
public enum TypeRecompense { Accessoire, Couleur, Titre, Effet }

public sealed record Recompense(int Niveau, TypeRecompense Type, string Nom, Accessoire? Accessoire = null, Couleur? Couleur = null);

// Catalogue des récompenses, par niveau. Pour en ajouter : une ligne ici (et son dessin dans Scene).
public static class Recompenses
{
    public static readonly IReadOnlyList<Recompense> Toutes = new Recompense[]
    {
        new(1, TypeRecompense.Titre, "Petit pixel"),
        new(1, TypeRecompense.Couleur, "Bleu ciel", Couleur: PilouBureau.Couleur.Bleu),
        new(1, TypeRecompense.Accessoire, "Feuille d'automne", Accessoire.Feuille),
        new(2, TypeRecompense.Accessoire, "Nœud papillon", Accessoire.Noeud),
        new(3, TypeRecompense.Titre, "Apprenti"),
        new(3, TypeRecompense.Accessoire, "Casque audio", Accessoire.Casque),
        new(4, TypeRecompense.Accessoire, "Bonnet de laine", Accessoire.Bonnet),
        new(5, TypeRecompense.Titre, "Compagnon fidèle"),
        new(5, TypeRecompense.Accessoire, "Lunettes de soleil", Accessoire.Lunettes),
        new(6, TypeRecompense.Couleur, "Bleu nuit", Couleur: PilouBureau.Couleur.Nuit),
        new(7, TypeRecompense.Accessoire, "Couronne", Accessoire.Couronne),
        new(8, TypeRecompense.Titre, "Gardien des sessions"),
        new(8, TypeRecompense.Couleur, "Ambre", Couleur: PilouBureau.Couleur.Ambre),
        new(9, TypeRecompense.Effet, "Traînée d'étoiles"),
        new(10, TypeRecompense.Couleur, "Argent", Couleur: PilouBureau.Couleur.Argent),
        new(12, TypeRecompense.Titre, "Légende du bureau"),
        new(12, TypeRecompense.Couleur, "Aurore", Couleur: PilouBureau.Couleur.Aurore),
    };

    public static int Requis(Accessoire a) => Toutes.FirstOrDefault(r => r.Accessoire == a)?.Niveau ?? 1;
    public static int Requis(Couleur c) => Toutes.FirstOrDefault(r => r.Couleur == c)?.Niveau ?? 1;
    public static int RequisTrainee => Toutes.First(r => r.Type == TypeRecompense.Effet).Niveau;

    public static string Titre(int niveau) =>
        Toutes.Where(r => r.Type == TypeRecompense.Titre && r.Niveau <= niveau).Select(r => r.Nom).LastOrDefault() ?? "Petit pixel";

    public static IEnumerable<Recompense> Au(int niveau) => Toutes.Where(r => r.Niveau == niveau);

    public static string NomCouleur(Couleur c) => Toutes.First(r => r.Couleur == c).Nom;
}
