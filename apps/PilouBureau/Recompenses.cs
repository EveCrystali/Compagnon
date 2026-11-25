namespace PilouBureau;

public enum Couleur { Bleu, Nuit, Ambre, Argent, Aurore, Lagon, Braise, Nacre, Abysse, Comete }
public enum TypeRecompense { Accessoire, Couleur, Titre, Effet }

public sealed record Recompense(int Niveau, TypeRecompense Type, string Nom, Accessoire? Accessoire = null, Couleur? Couleur = null);

// Ce que l'ancien système donnait par niveau. Désormais les niveaux n'offrent plus que les titres
// (honorifiques) : accessoires, couleurs et effets sont des articles de la boutique (Boutique.cs), au
// niveau d'accès d'origine. Cette liste sert aux titres et à la migration (rien de ce qui était acquis
// n'est perdu : Migration.Appliquer le verse dans l'inventaire).
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
        // Pêche et cuisine (niveaux 13 à 50).
        new(13, TypeRecompense.Titre, "Pêcheur du dimanche"),
        new(14, TypeRecompense.Accessoire, "Chapeau de pêcheur", Accessoire.ChapeauPeche),
        new(16, TypeRecompense.Titre, "Marmiton"),
        new(18, TypeRecompense.Accessoire, "Toque de chef", Accessoire.Toque),
        new(20, TypeRecompense.Titre, "Pêcheur aguerri"),
        new(20, TypeRecompense.Couleur, "Lagon", Couleur: PilouBureau.Couleur.Lagon),
        new(22, TypeRecompense.Accessoire, "Tablier", Accessoire.Tablier),
        new(24, TypeRecompense.Titre, "Chef de pixels"),
        new(26, TypeRecompense.Couleur, "Braise", Couleur: PilouBureau.Couleur.Braise),
        new(27, TypeRecompense.Accessoire, "Étoile de mer", Accessoire.EtoileMer),
        new(28, TypeRecompense.Titre, "Dompteur d'anguilles"),
        new(30, TypeRecompense.Effet, "Canne dorée (plus de prises légendaires)"),
        new(32, TypeRecompense.Titre, "Grand cuisinier"),
        new(32, TypeRecompense.Couleur, "Nacre", Couleur: PilouBureau.Couleur.Nacre),
        new(35, TypeRecompense.Effet, "Marmite en cuivre (moins de plats brûlés)"),
        new(36, TypeRecompense.Titre, "Maître des marées"),
        new(40, TypeRecompense.Titre, "Étoile des abysses"),
        new(40, TypeRecompense.Couleur, "Abysse", Couleur: PilouBureau.Couleur.Abysse),
        new(45, TypeRecompense.Titre, "Légende des lacs"),
        new(50, TypeRecompense.Titre, "Pilou éternel"),
        new(50, TypeRecompense.Couleur, "Comète", Couleur: PilouBureau.Couleur.Comete),
    };

    public const int Maximum = 50;

    // Identifiant de l'article de boutique qui remplace une ancienne récompense (null : un titre, ou le bleu de base).
    public static string? IdArticle(Recompense r) => r.Type switch
    {
        TypeRecompense.Accessoire when r.Accessoire is { } a => IdAccessoire(a),
        TypeRecompense.Couleur when r.Couleur is { } c && c != PilouBureau.Couleur.Bleu => IdCouleur(c),
        TypeRecompense.Effet when r.Nom.StartsWith("Traînée") => Boutique.TraineeEtoiles,
        TypeRecompense.Effet when r.Nom.StartsWith("Canne") => Boutique.CanneDoree,
        TypeRecompense.Effet when r.Nom.StartsWith("Marmite") => Boutique.MarmiteCuivre,
        _ => null,
    };

    public static string IdAccessoire(Accessoire a) => a.ToString().ToLowerInvariant();

    public static string IdCouleur(Couleur c) => "couleur-" + c.ToString().ToLowerInvariant();

    public static Couleur? CouleurDe(string id) =>
        Enum.GetValues<Couleur>().Cast<Couleur?>().FirstOrDefault(c => IdCouleur(c!.Value) == id);

    // Ancien niveau d'obtention (sert de niveau d'accès en boutique et au calcul du prix).
    public static int Ancien(Accessoire a) => Toutes.FirstOrDefault(r => r.Accessoire == a)?.Niveau ?? 1;
    public static int Ancien(Couleur c) => Toutes.FirstOrDefault(r => r.Couleur == c)?.Niveau ?? 1;

    public static string Titre(int niveau) =>
        Toutes.Where(r => r.Type == TypeRecompense.Titre && r.Niveau <= niveau).Select(r => r.Nom).LastOrDefault() ?? "Petit pixel";

    public static IEnumerable<Recompense> Au(int niveau) => Toutes.Where(r => r.Niveau == niveau);

    public static string NomCouleur(Couleur c) => Toutes.First(r => r.Couleur == c).Nom;
}
