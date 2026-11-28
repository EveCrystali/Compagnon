namespace PilouBureau;

// Ce que les niveaux ouvrent : l'accès (rayons et objets de la boutique, jeux, stades d'évolution) et les
// titres (honorifiques). Les objets eux-mêmes s'achètent en pièces d'or ; chaque niveau gagné en rapporte.
public static class Acces
{
    // Niveau d'accès de chaque jeu (les futurs jeux s'ajoutent ici).
    public static readonly IReadOnlyList<(string Id, string Nom, int Niveau)> Jeux = new[]
    {
        ("etoile", "Étoile filante", 1),
        ("bulles", "Bulles", 1),
        ("peche", "Pêche", 2),
        ("tape", "Tape m'en cinq", 3),
        ("cuisine", "Cuisine", 4),
        ("chasse", "Chasse aux bugs (téléphone)", 5),
        ("defense", "Défense du bureau", 5),
    };

    public static int NiveauJeu(string id) => Jeux.FirstOrDefault(j => j.Id == id).Niveau is var n && n > 0 ? n : 1;

    public static bool JeuOuvert(string id, int niveau) => niveau >= NiveauJeu(id);

    // Évolution : une créature qui grandit (noms provisoires).
    public static readonly IReadOnlyList<(int Stade, string Nom, int Niveau)> Stades = new[]
    {
        (1, "Gouttelette", 1),
        (2, "Pilou", 10),
        (3, "Pilou Nimbus", 25),
        (4, "Pilou Astral", 40),
    };

    public static int Stade(int niveau) => Stades.Last(s => niveau >= s.Niveau).Stade;

    public static string NomStade(int stade) => Stades.FirstOrDefault(s => s.Stade == stade).Nom ?? "Pilou";

    // Pièces d'or gagnées en atteignant un niveau.
    public static int PoNiveau(int niveau) => 20 + 5 * niveau;

    // Total des pièces pour être passé du niveau « de » (exclu) au niveau « a » (inclus).
    public static int PoMontee(int de, int a) => Enumerable.Range(de + 1, Math.Max(0, a - de)).Sum(PoNiveau);

    // Niveau affiché : la courbe actuelle, jamais sous le niveau acquis.
    public static int Niveau(int xp, int acquis) => Math.Max(Profil.Niveau(xp), acquis);
}

// Évolution, montées de niveau payées, migration depuis les anciennes récompenses gratuites.
public sealed class Evolution
{
    // Stade le plus haut atteint (0 : profil d'avant la migration).
    public int StadeAtteint { get; set; }
    // Forme affichée choisie parmi les stades atteints (0 : la plus haute).
    public int StadeAffiche { get; set; }
    // Une pierre de calme a retenu l'évolution : Pilou reste à son stade jusqu'à « Laisser évoluer ».
    public bool Retenue { get; set; }
    // Dernier niveau pour lequel les pièces d'or ont été versées (partagé au maximum dans le groupe).
    public int NiveauPaye { get; set; }
    // 1 : les anciennes récompenses gagnées par niveau ont été versées dans l'inventaire.
    public int Migre { get; set; }
    // Plus haut niveau jamais atteint (ancienne courbe comprise) : le niveau affiché ne descend jamais dessous.
    public int NiveauAcquis { get; set; }
    // Variante de chaque stade (2 à 4), choisie au passage d'après la qualité des soins : « calin » ou
    // « espiegle ». Partagée dans le groupe ; la première décision l'emporte.
    public Dictionary<int, string> Variantes { get; set; } = new();
    // Ce que Pilou a gardé de son ancienne forme, par stade (2 à 4) : l'option choisie la première fois que sa scène
    // d'évolution est jouée (assets/evolutions.txt). Revoir la scène ne la change plus.
    public Dictionary<int, string> Gardes { get; set; } = new();

    public int Affiche => StadeAffiche >= 1 && StadeAffiche <= StadeAtteint ? StadeAffiche : Math.Max(1, StadeAtteint);

    // Une évolution est due : le niveau a passé un palier que Pilou n'a pas encore franchi.
    public bool Due(int niveau) => Acces.Stade(niveau) > Math.Max(1, StadeAtteint);
}

public static class Migration
{
    // Ce que l'ancien système donnait gratuitement au niveau atteint (ancienne courbe, xp = 5·(n−1)²) devient
    // possédé (personne ne perd rien) ; ce niveau devient le niveau acquis ; les pièces d'or des niveaux déjà
    // atteints ne sont pas rétroactives ; l'évolution actuelle est acquise sans animation.
    public static void Appliquer(Profil p, int xpTotal, Reglages? reglages = null)
    {
        var ev = p.Evolution;
        if (ev.Migre >= 1) return;
        int niveau = Math.Max(Profil.NiveauAncien(xpTotal), ev.NiveauAcquis);
        ev.NiveauAcquis = niveau;
        foreach (var r in Recompenses.Toutes.Where(r => r.Niveau <= niveau))
            if (Recompenses.IdArticle(r) is { } id && !p.Bourse.Inventaire.Contains(id)) p.Bourse.Inventaire.Add(id);
        ev.NiveauPaye = Math.Max(ev.NiveauPaye, niveau);
        ev.StadeAtteint = Math.Max(ev.StadeAtteint, Acces.Stade(niveau));
        double t = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
        // Ce qui était porté le reste.
        if (reglages is not null)
        {
            if (reglages.Couleur != Couleur.Bleu && p.Bourse.Inventaire.Contains(Recompenses.IdCouleur(reglages.Couleur)))
                p.Bourse.Equipe[Boutique.Couleur] = new Port(Recompenses.IdCouleur(reglages.Couleur), t);
            if (reglages.Trainee && p.Bourse.Inventaire.Contains(Boutique.TraineeEtoiles))
                p.Bourse.Equipe[Boutique.Effet] = new Port(Boutique.TraineeEtoiles, t);
        }
        ev.Migre = 1;
    }
}
