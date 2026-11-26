using System.Globalization;
using System.Text.Json;

namespace PilouBureau;

// Tournage d'une vidéo de présentation sur un vrai écran (outils/tourner-ecran-gauche.ps1).
// Ici, rien que la logique sans Windows (testable) : options de lancement, choix de l'écran, déroulé de la
// visite guidée, données fictives (profil, amis, réglages) et chronologie pour le montage.
// Le mode démo vit en mémoire : le profil démo ne s'écrit jamais (Profil.EnMemoire), le vrai n'est même pas lu.

// Un écran, en pixels physiques : X, Y du coin haut gauche (négatifs à gauche ou au-dessus de l'écran principal).
public sealed record CadreEcran(int X, int Y, int Largeur, int Hauteur)
{
    public int Droite => X + Largeur;
    public int Bas => Y + Hauteur;
}

// --visite-guidee[=<chronologie.json>] : joue la visite guidée puis quitte (mode démo, en mémoire).
// --ecran=gauche|droite|principal : pose Pilou en bas de cet écran pour cette session (réglages inchangés).
// --placer=x,y : pose Pilou sur l'écran de ce point (pixels physiques), en bas, pour cette session.
public sealed record OptionsTournage(bool Visite, string? Chronologie, string? Ecran, (int X, int Y)? Placer)
{
    public static readonly OptionsTournage Aucune = new(false, null, null, null);

    public static readonly string[] Ecrans = { "gauche", "droite", "principal" };

    // Lit les options de tournage ; renvoie aussi ce qui reste (les autres options, le dossier).
    // Une valeur invalide est ignorée (Pilou démarre comme d'habitude), mais l'option est quand même retirée.
    public static (OptionsTournage Options, string[] Reste) Analyser(IEnumerable<string> args)
    {
        bool visite = false;
        string? chronologie = null, ecran = null;
        (int, int)? placer = null;
        var reste = new List<string>();
        foreach (var a in args)
        {
            if (a == "--visite-guidee") visite = true;
            else if (a.StartsWith("--visite-guidee=", StringComparison.Ordinal))
            {
                visite = true;
                var c = a["--visite-guidee=".Length..].Trim().Trim('"');
                chronologie = c == "" ? null : c;
            }
            else if (a.StartsWith("--ecran=", StringComparison.Ordinal))
            {
                var e = a["--ecran=".Length..].Trim().ToLowerInvariant();
                ecran = Ecrans.Contains(e) ? e : null;
            }
            else if (a.StartsWith("--placer=", StringComparison.Ordinal)) placer = Point(a["--placer=".Length..]);
            else reste.Add(a);
        }
        return (new OptionsTournage(visite, chronologie, ecran, placer), reste.ToArray());
    }

    private static (int, int)? Point(string s)
    {
        var p = s.Split(',');
        return p.Length == 2
               && int.TryParse(p[0].Trim(), NumberStyles.Integer, CultureInfo.InvariantCulture, out var x)
               && int.TryParse(p[1].Trim(), NumberStyles.Integer, CultureInfo.InvariantCulture, out var y)
            ? (x, y) : null;
    }
}

public sealed record Moment(string Etape, long T, bool Jouee = true);

// Une étape de la visite guidée : son nom, sa durée, la scène --essai= qu'elle joue (s'il y en a une) et si elle
// dépend d'une fonction que l'exe n'a peut-être pas encore (sautée sans elle).
public sealed record EtapeVisite(string Nom, double Secondes, string? Scene = null, bool Optionnelle = false);

public static class Tournage
{
    // L'écran le plus à gauche (plus petit X ; à égalité, le plus haut). -1 : aucun écran.
    public static int PlusAGauche(IReadOnlyList<CadreEcran> ecrans)
    {
        int choisi = -1;
        for (int i = 0; i < ecrans.Count; i++)
            if (choisi < 0 || ecrans[i].X < ecrans[choisi].X || (ecrans[i].X == ecrans[choisi].X && ecrans[i].Y < ecrans[choisi].Y))
                choisi = i;
        return choisi;
    }

    // L'écran le plus à droite (plus grand bord droit ; à égalité, le plus haut). -1 : aucun écran.
    public static int PlusADroite(IReadOnlyList<CadreEcran> ecrans)
    {
        int choisi = -1;
        for (int i = 0; i < ecrans.Count; i++)
            if (choisi < 0 || ecrans[i].Droite > ecrans[choisi].Droite || (ecrans[i].Droite == ecrans[choisi].Droite && ecrans[i].Y < ecrans[choisi].Y))
                choisi = i;
        return choisi;
    }

    // L'écran demandé par --ecran= ; « principal » : celui qui contient (0, 0).
    public static int Choisir(string ecran, IReadOnlyList<CadreEcran> ecrans) => ecran switch
    {
        "gauche" => PlusAGauche(ecrans),
        "droite" => PlusADroite(ecrans),
        _ => ecrans.Select((e, i) => (e, i)).Where(x => x.e.X <= 0 && x.e.Droite > 0 && x.e.Y <= 0 && x.e.Bas > 0)
            .Select(x => x.i).DefaultIfEmpty(PlusAGauche(ecrans)).First(),
    };

    // Le déroulé de la visite guidée (secondes) : ~1 min 30 de base, avec des pauses qui se lisent. Les étapes
    // « optionnelles » montrent des scènes qui n'existent peut-être pas encore dans cet exe : jouées si l'exe les
    // connaît (EssaiConnu, RayonEnsembles), sautées sinon (sans temps mort), et notées jouee: false pour le montage.
    // Elles viennent vers la fin, après les menus et la boutique.
    public static readonly IReadOnlyList<EtapeVisite> Etapes = new EtapeVisite[]
    {
        new("accueil", 3),                     // Pilou au repos, il dit bonjour
        new("promenade", 4),                   // il fait quelques pas
        new("attente", 5),                     // une IA t'attend : il court sous la souris
        new("menu", 14),                       // le vrai menu clic droit rétro : survol, Couleur, Ce qu'il porte, Intégrations, Quêtes
        new("boutique", 10),                   // la boutique : Vitrine, puis le rayon Tête, essai d'un objet
        new("amis", 6),                        // la fenêtre Amis (amis fictifs, code fictif)
        new("clavier", 5, "clavier"),          // il tape avec toi
        new("photo", 4, "photo"),              // capture d'écran : il prend la photo
        new("visite-depart", 5, "visite:depart"),
        new("visite-retour", 4, "visite:retour"),
        new("visite-jeu", 8, "visite:jeu"),    // Léo vient jouer chez lui
        new("meteo", 5, "meteo:pluie:parapluie"),
        new("etoile", 4, "etoile"),            // petit jeu : attrape l'étoile
        new("tape", 4, "tape"),                // petit jeu : tape m'en cinq
        new("evolution", 6, "evolution"),
        new("boutique-ensembles", 7, null, true),           // boutique : rayon Ensembles et compteur de collection
        new("defense", 9, "defense", true),                 // Défense du bureau : Pilou joue seul
        new("expedition-depart", 5, "expedition:depart", true),
        new("expedition-retour", 5, "expedition:retour", true),
        new("expedition-defaite", 5, "expedition:defaite", true),
        new("expedition-journal", 5, "expedition:journal", true),
        new("icone", 4),                       // le menu de l'icône près de l'horloge
        new("fin", 3),                         // au revoir
    };

    // Durée si tout est joué, et sans les étapes optionnelles.
    public static double Duree => Etapes.Sum(e => e.Secondes);
    public static double DureeDeBase => Etapes.Where(e => !e.Optionnelle).Sum(e => e.Secondes);

    public static double DureeDe(string etape) => Etapes.FirstOrDefault(e => e.Nom == etape)?.Secondes ?? 0;

    // Scènes --essai= que cet exe sait jouer. Une nouvelle scène (Jeux.cs, FenetrePilou.Essai) s'ajoute ICI aussi :
    // c'est cette liste que lisent la visite guidée et --essais-disponibles (outils/tourner-ecran-gauche.ps1).
    public static readonly IReadOnlyList<string> EssaisConnus = new[]
    {
        "etoile", "bulles", "tape", "etourdi", "peche", "mord", "prise", "cuisine", "niveau", "evolution",
        "clavier", "photo", "notif", "notif:masque",
        "visite:depart", "visite:arrivee", "visite:jeu", "visite:retour",
    };

    // Familles à paramètre (--essai=stade:3, tenue:code, objet:cape, soins:faim, meteo:pluie:parapluie).
    public static readonly IReadOnlyList<string> FamillesConnues = new[] { "stade:", "tenue:", "objet:", "soins:", "meteo:" };

    public static bool EssaiConnu(string scene) =>
        EssaisConnus.Contains(scene) || FamillesConnues.Any(f => scene.StartsWith(f, StringComparison.Ordinal) && scene.Length > f.Length);

    // Le rayon « Ensembles » de la boutique, s'il existe dans cette version ; null sinon.
    public static string? RayonEnsembles() =>
        Boutique.Rayons.FirstOrDefault(r => r.StartsWith("ensemble", StringComparison.OrdinalIgnoreCase)
                                            || Boutique.NomSlot(r).StartsWith("Ensemble", StringComparison.OrdinalIgnoreCase));

    public static bool Disponible(EtapeVisite e) =>
        !e.Optionnelle || (e.Scene is { } scene ? EssaiConnu(scene) : e.Nom == "boutique-ensembles" && RayonEnsembles() is not null);

    // Le programme : début de chaque étape (s) et si elle est jouée ; une étape sautée ne prend pas de temps.
    public static List<(EtapeVisite Etape, double Debut, bool Jouee)> Planifier(Func<EtapeVisite, bool> disponible)
    {
        var plan = new List<(EtapeVisite, double, bool)>();
        double t = 0;
        foreach (var e in Etapes)
        {
            bool jouee = disponible(e);
            plan.Add((e, t, jouee));
            if (jouee) t += e.Secondes;
        }
        return plan;
    }

    // --essais-disponibles=<fichier> : ce que cet exe sait montrer (le script de tournage le lit avant de filmer).
    public static string Disponibles(string version) =>
        JsonSerializer.Serialize(new
        {
            version,
            essais = EssaisConnus.Concat(FamillesConnues.Select(f => f + "*")).ToList(),
            rayons = Boutique.Rayons.ToList(),
            ensembles = RayonEnsembles(),
            etapes = Etapes.Select(e => new { etape = e.Nom, jouee = Disponible(e) }).ToList(),
        }, new JsonSerializerOptions { WriteIndented = true });

    // ---- Données fictives (mode démo)

    public const int NiveauDemo = 18;
    // Code ami affiché en démo : visiblement fictif (PILOU-ABCD-2345-WXYZ), jamais celui de la personne.
    public const string CodeDemo = "ABCD2345WXYZ";
    public const string AmiDemo = "ESSAYEZ23ESS"; // Léo, le même que les essais --essai=visite:…

    // Un Pilou de niveau 18, quelques objets portés, des po : seulement en mémoire (EnMemoire : rien n'est écrit).
    public static Profil ProfilDemo(double epoque)
    {
        var p = new Profil
        {
            EnMemoire = true,
            Xp = Profil.XpPourNiveau(NiveauDemo) + 240,
            XpClaudeVue = 0,
            JeuxGagnes = 37,
            Caresses = 212,
            SeancesClavier = 14,
            Captures = 9,
        };
        p.Stock["goujon"] = 2;
        p.Bourse.PoGagnes = 1860;
        p.Bourse.PoDepenses = 420;
        p.Bourse.Inventaire.AddRange(new[]
        {
            "chapeau-pirate", "casquette", "echarpe", "lunettes-rondes", "tasse-cafe", "parapluie", "petit-chat",
            "glacier", "lavande", "sable", "bulle-doree", Boutique.TraineeEtoiles,
        });
        p.Bourse.Equipe[Boutique.Tete] = new Port("chapeau-pirate", epoque);
        p.Bourse.Equipe[Boutique.Cou] = new Port("echarpe", epoque);
        p.Bourse.Equipe[Boutique.Compagnon] = new Port("petit-chat", epoque);
        p.Bourse.Equipe[Boutique.Couleur] = new Port("glacier", epoque);
        int stade = Acces.Stade(NiveauDemo);
        p.Evolution.StadeAtteint = stade;
        p.Evolution.NiveauAcquis = NiveauDemo;
        p.Evolution.NiveauPaye = NiveauDemo;
        p.Evolution.Migre = 1;
        p.Evolution.Variantes[2] = "calin";
        return p;
    }

    // Amis fictifs : Léo (en ligne), Maya (vue il y a 3 h), Sam (demande reçue), Noé (en attente). Code fictif.
    public static CarnetAmis CarnetDemo(double epoque)
    {
        Ami Un(string code, string nom, EtatAmi etat, double vu, int niveau, int stade, int amitie, Dictionary<string, string> equipe) => new()
        {
            Code = code, Etat = etat, Surnom = nom, Vu = vu, Amitie = amitie, Ajoute = epoque - 9 * 86_400_000.0,
            Pilou = new Vitrine { Nom = nom, Niveau = niveau, Stade = stade, Equipe = equipe },
        };
        var c = new CarnetAmis { Moi = new Identite { Code = CodeDemo } };
        c.Amis.Add(Un(AmiDemo, "Léo", EtatAmi.Actif, epoque - 60_000, 12, 2, 4,
            new() { [Boutique.Tete] = "chapeau-pirate", [Boutique.Couleur] = "couleur-ambre" }));
        c.Amis.Add(Un("MAYA2345KPQR", "Maya", EtatAmi.Actif, epoque - 3 * 3_600_000.0, 27, 3, 7, new() { [Boutique.Main] = "parapluie" }));
        c.Amis.Add(Un("SAMX6789HJKN", "Sam", EtatAmi.Recue, epoque - 120_000, 6, 1, 0, new()));
        c.Amis.Add(Un("NAEZ3456TUVW", "Noé", EtatAmi.Attente, 0, 1, 1, 0, new()));
        return c;
    }

    // Réglages de tournage (en mémoire) : bulle détaillée, pas de mise à jour ni de réseau, rien qui le cache,
    // pas de petit jeu au hasard, aucun crochet clavier ni lecture des notifications, l'icône près de l'horloge.
    public static void Regler(Reglages r)
    {
        r.Taille = 1.3;
        r.Bulle = ModeBulle.Detaillee;
        r.Promenade = true;
        r.SuitSouris = true;
        r.Jeux = false;
        r.DossierPartage = "";
        r.DiscordStatut = false;
        r.Webhook = "";
        r.Telephone = "";
        r.MiseAJourAuto = false;
        r.IconeNotification = true;
        r.Activites = false;
        r.CacherPleinEcran = false;
        r.CacherPresentation = false;
        r.CacherVisio = false;
        r.GesteClavier = false;
        r.GestePhoto = false;
        r.NotifsWindows = false;
        r.PartirEnVisite = false;
        r.Connecteurs = new ReglagesConnecteurs { Api = false };
        r.BoutiqueVue = NiveauDemo - 4; // quelques rangées « nouvelles » à montrer
        r.BoutiqueOffresVues = "";
    }

    // Chronologie pour le montage : version de Pilou, chaque étape, son instant (ms Unix) et si elle a été jouée.
    public static string Chronologie(IEnumerable<Moment> moments, string version = "") =>
        JsonSerializer.Serialize(new
        {
            version,
            etapes = moments.Select(m => new { etape = m.Etape, t = m.T, jouee = m.Jouee }).ToList(),
        }, new JsonSerializerOptions { WriteIndented = true });
}
