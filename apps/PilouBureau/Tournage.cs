using System.Globalization;
using System.IO;
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
    public bool Vide => Largeur <= 0 || Hauteur <= 0;
    public long Aire => Vide ? 0 : (long)Largeur * Hauteur;

    public static CadreEcran DeBords(int gauche, int haut, int droite, int bas) => new(gauche, haut, droite - gauche, bas - haut);

    // Le plus petit cadre qui contient les deux (un cadre vide ne compte pas).
    public CadreEcran Union(CadreEcran o) =>
        Vide ? o : o.Vide ? this : DeBords(Math.Min(X, o.X), Math.Min(Y, o.Y), Math.Max(Droite, o.Droite), Math.Max(Bas, o.Bas));

    public CadreEcran Inter(CadreEcran o)
    {
        int g = Math.Max(X, o.X), h = Math.Max(Y, o.Y), d = Math.Min(Droite, o.Droite), b = Math.Min(Bas, o.Bas);
        return d > g && b > h ? DeBords(g, h, d, b) : new CadreEcran(g, h, 0, 0);
    }

    public CadreEcran Elargi(int marge) => DeBords(X - marge, Y - marge, Droite + marge, Bas + marge);

    public bool Contient(CadreEcran o) => !o.Vide && o.X >= X && o.Y >= Y && o.Droite <= Droite && o.Bas <= Bas;
}

// --visite-guidee[=<chronologie.json>] : joue la visite guidée puis quitte (mode démo, en mémoire).
// --ecran=gauche|droite|principal : pose Pilou en bas de cet écran pour cette session (réglages inchangés).
// --placer=x,y : pose Pilou sur l'écran de ce point (pixels physiques), en bas, pour cette session.
// --sans-decor : visite guidée sans le décor de tournage (le vrai bureau reste visible derrière Pilou).
public sealed record OptionsTournage(bool Visite, string? Chronologie, string? Ecran, (int X, int Y)? Placer, bool SansDecor = false)
{
    public static readonly OptionsTournage Aucune = new(false, null, null, null);

    public static readonly string[] Ecrans = { "gauche", "droite", "principal" };

    // Lit les options de tournage ; renvoie aussi ce qui reste (les autres options, le dossier).
    // Une valeur invalide est ignorée (Pilou démarre comme d'habitude), mais l'option est quand même retirée.
    public static (OptionsTournage Options, string[] Reste) Analyser(IEnumerable<string> args)
    {
        bool visite = false, sansDecor = false;
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
            else if (a == "--sans-decor") sansDecor = true;
            else reste.Add(a);
        }
        return (new OptionsTournage(visite, chronologie, ecran, placer, sansDecor), reste.ToArray());
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

// Un rectangle d'intérêt pour le montage (pixels d'écran) : ce qu'il montre (« pilou », « pilou+menu+sous-menu »,
// « pilou+fenetre »…), de quand à quand (ms Unix), et le cadre 16:9 qui le contient (zoom/panoramique du monteur).
public sealed record Cadrage(string Etape, string Quoi, CadreEcran Zone, CadreEcran Zoom, long Debut, long Fin);

// Une fenêtre posée (unités WPF) ; sans WPF pour être testable.
public readonly record struct Place(double X, double Y, double Largeur, double Hauteur)
{
    public double Droite => X + Largeur;
    public double Bas => Y + Hauteur;
}

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

    // Le déroulé de la visite guidée (secondes) : ~1 min 35 en tout, des étapes courtes et enchaînées (2,5 à 4 s ;
    // un peu plus quand il y a plusieurs choses à voir : menu et sous-menus, boutique, Défense, jeu avec Léo).
    // Les étapes « optionnelles » montrent des scènes qui n'existent peut-être pas encore dans cet exe : jouées si
    // l'exe les connaît (EssaiConnu, RayonEnsembles), sautées sinon (sans temps mort), et notées jouee: false pour
    // le montage. Elles viennent vers la fin, après les menus et la boutique.
    public static readonly IReadOnlyList<EtapeVisite> Etapes = new EtapeVisite[]
    {
        new("accueil", 2.5),                   // Pilou au repos, il dit bonjour
        new("promenade", 3),                   // il fait quelques pas
        new("attente", 4),                     // une IA t'attend : il court sous la souris
        new("menu", 8),                        // le vrai menu clic droit rétro : survol, sous-menus Couleur et Intégrations
        new("boutique", 6.5),                  // la boutique : Vitrine, puis le rayon Tête, essai d'un objet
        new("amis", 3.5),                      // la fenêtre Amis (amis fictifs, code fictif)
        new("clavier", 3.5, "clavier"),        // il tape avec toi
        new("photo", 3, "photo"),              // capture d'écran : il prend la photo
        new("visite-depart", 3.5, "visite:depart"),
        new("visite-retour", 3.5, "visite:retour"),
        new("visite-jeu", 6, "visite:jeu"),    // Léo vient jouer chez lui
        new("meteo", 3.5, "meteo:pluie:parapluie"),
        new("etoile", 3.5, "etoile"),          // petit jeu : attrape l'étoile
        new("tape", 3, "tape"),                // petit jeu : tape m'en cinq
        new("evolution", 5, "evolution"),      // l'animation dure 4,2 s
        new("boutique-ensembles", 4, null, true),           // boutique : rayon Ensembles et compteur de collection
        new("defense", 7, "defense", true),                 // Défense du bureau : Pilou joue seul
        new("expedition-depart", 3.5, "expedition:depart", true),
        new("expedition-retour", 4, "expedition:retour", true),
        new("expedition-defaite", 3.5, "expedition:defaite", true),
        new("expedition-journal", 4, "expedition:journal", true),
        new("aventure-lecture", 4, "campagne:lecture", true),   // la fenêtre Aventure : Pilou écrit, on choisit
        new("aventure-retour", 3.5, "campagne:retour", true),   // il revient de son attente : une annonce, un signe
        new("icone", 3.5),                     // le menu de l'icône près de l'horloge
        new("fin", 2.5),                       // au revoir
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
        "clavier", "photo", "notif", "notif:masque", "defense",
        "visite:depart", "visite:arrivee", "visite:jeu", "visite:retour",
        "expedition:depart", "expedition:retour", "expedition:defaite", "expedition:journal",
        "campagne:lecture", "campagne:attente", "campagne:retour", "campagne:epreuve", "campagne:fin",
        "mot", "journal", "complicite",
    };

    // Familles à paramètre (--essai=stade:3, tenue:code, objet:cape, soins:faim, meteo:pluie:parapluie, campagne:prologue).
    public static readonly IReadOnlyList<string> FamillesConnues = new[] { "stade:", "tenue:", "objet:", "soins:", "meteo:", "humeur:", "dessin:", "campagne:" };

    public static bool EssaiConnu(string scene) =>
        EssaisConnus.Contains(scene) || EssaiAuBord(scene) is not null
        || FamillesConnues.Any(f => scene.StartsWith(f, StringComparison.Ordinal) && scene.Length > f.Length);

    // Jeux qui se rejouent collés à un bord de l'écran (--essai=peche:gauche, cuisine:droite…).
    public static readonly IReadOnlyList<string> JeuxAuBord = new[] { "peche", "mord", "prise", "cuisine", "tape", "etoile", "bulles" };

    // « peche:gauche » → (peche, bord gauche) ; null si ce n'est pas un essai au bord.
    public static (string Jeu, bool Gauche)? EssaiAuBord(string scene)
    {
        int i = scene.IndexOf(':');
        if (i < 0) return null;
        var (jeu, bord) = (scene[..i], scene[(i + 1)..]);
        return JeuxAuBord.Contains(jeu) && bord is "gauche" or "droite" ? (jeu, bord == "gauche") : null;
    }

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
            essais = EssaisConnus.Concat(JeuxAuBord.SelectMany(j => new[] { j + ":gauche", j + ":droite" })).Concat(FamillesConnues.Select(f => f + "*")).ToList(),
            rayons = Boutique.Rayons.ToList(),
            ensembles = RayonEnsembles(),
            // Durée de la visite avec ce que cet exe sait jouer : le script attend jusque-là (plus une marge).
            duree_s = Planifier(Disponible).Where(x => x.Jouee).Sum(x => x.Etape.Secondes),
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
        r.Taille = 1.3; // remplacée, une fois l'écran connu, par TailleTournage (en mémoire seulement)
        // Bulle courte : ce que Pilou dit et l'IA qui attend ; le détail des sessions encombrait l'image.
        r.Bulle = ModeBulle.Masquee;
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

    // Taille de Pilou pendant le tournage, d'après la hauteur de la zone de travail (unités WPF) : ×2 environ sur un
    // écran de 1440 (2,6 au lieu de 1,3), pour que le montage puisse zoomer sans flou. En mémoire seulement.
    public static double TailleTournage(double hauteurZone) =>
        double.IsFinite(hauteurZone) && hauteurZone > 0 ? Math.Clamp(Math.Round(hauteurZone / 540, 1), 1.3, 3.0) : 1.3;

    // Une fenêtre (boutique, amis, expéditions…) posée à côté de Pilou, en bas de l'écran : à sa gauche s'il y a la
    // place (sinon à sa droite), son bas un peu au-dessus du sol. Pilou et la fenêtre forment un bloc compact dans le
    // tiers bas/milieu, que le montage cadre en 16:9. Trop grande : réduite à la zone.
    public static Place PoserPres(Place zone, double pilouX, double demiPilou, double largeur, double hauteur, double marge = 24)
    {
        double l = Math.Min(largeur, zone.Largeur * 0.9), h = Math.Min(hauteur, zone.Hauteur * 0.8);
        double gauche = pilouX - demiPilou - marge - l, droite = pilouX + demiPilou + marge;
        double x = gauche >= zone.X + marge ? gauche
            : droite + l <= zone.Droite - marge ? droite
            : Math.Clamp(pilouX - l / 2, zone.X + marge, Math.Max(zone.X + marge, zone.Droite - marge - l));
        double y = Math.Max(zone.Y + marge, zone.Bas - marge - h);
        return new Place(x, y, l, h);
    }

    // Le cadre 16:9 du monteur autour d'une zone d'intérêt : la zone plus une marge, jamais plus étroit qu'un tiers de
    // l'écran (sinon le zoom serait flou), centré sur elle et poussé dans l'écran.
    public static CadreEcran Zoom169(CadreEcran zone, CadreEcran ecran, int marge = 48)
    {
        if (zone.Vide || ecran.Vide) return ecran;
        double min = Math.Max(640, ecran.Largeur / 3.0);
        double l = Math.Max(Math.Max(zone.Largeur + 2.0 * marge, (zone.Hauteur + 2.0 * marge) * 16 / 9), min);
        l = Math.Min(l, ecran.Largeur);
        double h = Math.Min(l * 9 / 16, ecran.Hauteur);
        l = Math.Min(l, h * 16 / 9);
        double cx = zone.X + zone.Largeur / 2.0, cy = zone.Y + zone.Hauteur / 2.0;
        double x = Math.Clamp(cx - l / 2, ecran.X, ecran.Droite - l), y = Math.Clamp(cy - h / 2, ecran.Y, ecran.Bas - h);
        return new CadreEcran((int)Math.Round(x), (int)Math.Round(y), (int)Math.Round(l), (int)Math.Round(h));
    }

    // Chronologie pour le montage : version de Pilou, chaque étape, son instant (ms Unix) et si elle a été jouée.
    public static string Chronologie(IEnumerable<Moment> moments, string version = "") =>
        JsonSerializer.Serialize(new
        {
            version,
            etapes = moments.Select(m => new { etape = m.Etape, t = m.T, jouee = m.Jouee }).ToList(),
        }, new JsonSerializerOptions { WriteIndented = true });
}

// Suit la zone d'intérêt de l'étape en cours, observée quelques fois par seconde, et la découpe en cadrages
// successifs : un nouveau dès que ce qu'on montre change (un sous-menu s'ouvre, une fenêtre se ferme) ou bouge
// nettement (Pilou se promène). Une petite variation agrandit le cadrage en cours au lieu d'en ouvrir un autre.
public sealed class Cadreur
{
    public const int Tolerance = 64;
    private readonly CadreEcran _ecran;
    private string _etape = "", _quoi = "";
    private CadreEcran _zone = new(0, 0, 0, 0);
    private long _debut;
    private bool _ouvert;

    public Cadreur(CadreEcran ecran) => _ecran = ecran;

    // Renvoie le cadrage qui vient de se terminer, s'il y en a un.
    public Cadrage? Observer(string etape, string quoi, CadreEcran zone, long t)
    {
        zone = zone.Inter(_ecran);
        if (zone.Vide) return Fermer(t);
        if (_ouvert && etape == _etape && quoi == _quoi && _zone.Elargi(Tolerance).Contient(zone) && zone.Aire * 2 >= _zone.Aire)
        {
            _zone = _zone.Union(zone);
            return null;
        }
        var ferme = Fermer(t);
        (_etape, _quoi, _zone, _debut, _ouvert) = (etape, quoi, zone, t, true);
        return ferme;
    }

    public Cadrage? Fermer(long t)
    {
        if (!_ouvert) return null;
        _ouvert = false;
        return new Cadrage(_etape, _quoi, _zone, Tournage.Zoom169(_zone, _ecran), _debut, Math.Max(_debut, t));
    }
}

// Journal de la visite guidée, écrit au fil de l'eau : chaque événement (étape, cadrage, erreur, fin) s'ajoute à
// <chronologie>.jsonl, une ligne JSON par événement, et la chronologie complète (<chronologie>) est réécrite à chaque
// fois (fichier temporaire puis remplacement). Si l'overlay s'arrête net, le script de tournage a quand même tout
// ce qui a été joué. Les erreurs vont aussi, en clair, dans erreurs.txt à côté (le script le met dans le zip).
// Sans chemin : tout reste en mémoire.
public sealed class JournalVisite
{
    private readonly string? _instantane, _lignes, _erreurs;
    private readonly string _version;
    private readonly CadreEcran? _ecran;
    private readonly Func<long> _horloge;
    private readonly List<Moment> _moments = new();
    private readonly List<Cadrage> _cadres = new();
    private readonly List<(long T, string Etape, string Message)> _fautes = new();
    private readonly Dictionary<string, int> _repetitions = new();
    private readonly object _verrou = new();
    private long? _fin;

    public const int RepetitionsMax = 3;

    private static readonly JsonSerializerOptions Lisible = new() { WriteIndented = true };

    public JournalVisite(string? chronologie, string version, CadreEcran? ecran, Func<long> horloge)
    {
        _version = version;
        _ecran = ecran;
        _horloge = horloge;
        if (string.IsNullOrWhiteSpace(chronologie)) return;
        _instantane = chronologie;
        _lignes = Path.ChangeExtension(chronologie, ".jsonl");
        _erreurs = Path.Combine(Path.GetDirectoryName(Path.GetFullPath(chronologie)) ?? ".", "erreurs.txt");
    }

    public string? CheminLignes => _lignes;
    public string? CheminErreurs => _erreurs;
    public string EtapeCourante { get; private set; } = "";
    public bool Fini => _fin is not null;

    public IReadOnlyList<Moment> Moments
    {
        get { lock (_verrou) return _moments.ToList(); }
    }

    public IReadOnlyList<Cadrage> Cadres
    {
        get { lock (_verrou) return _cadres.ToList(); }
    }

    public IReadOnlyList<(long T, string Etape, string Message)> Erreurs
    {
        get { lock (_verrou) return _fautes.ToList(); }
    }

    public void Etape(string nom, bool jouee = true)
    {
        long t = _horloge();
        lock (_verrou)
        {
            _moments.Add(new Moment(nom, t, jouee));
            if (jouee) EtapeCourante = nom;
        }
        Ecrire(new { type = "etape", etape = nom, t, jouee });
    }

    public void Cadre(Cadrage? c)
    {
        if (c is null) return;
        lock (_verrou) _cadres.Add(c);
        Ecrire(new { type = "cadre", etape = c.Etape, quoi = c.Quoi, debut = c.Debut, fin = c.Fin, zone = Zone(c.Zone), zoom = Zone(c.Zoom) });
    }

    public void Erreur(string etape, Exception e) => Erreur(etape, $"{e.GetType().Name} : {e.Message}", e.ToString());

    public void Erreur(string etape, string message, string? detail = null)
    {
        long t = _horloge();
        lock (_verrou)
        {
            // La même erreur qui revient à chaque image (30 fois par seconde) : notée trois fois, pas plus.
            var cle = etape + "|" + message;
            int deja = _repetitions.GetValueOrDefault(cle);
            _repetitions[cle] = deja + 1;
            if (deja >= RepetitionsMax) return;
            _fautes.Add((t, etape, message));
        }
        Ecrire(new { type = "erreur", etape, t, message });
        if (_erreurs is null) return;
        try
        {
            var heure = DateTimeOffset.FromUnixTimeMilliseconds(t).ToLocalTime().ToString("HH:mm:ss.fff", CultureInfo.InvariantCulture);
            lock (_verrou)
                File.AppendAllText(_erreurs, $"[{heure}] étape « {etape} » : {message}{Environment.NewLine}"
                                             + (detail is null ? "" : detail + Environment.NewLine));
        }
        catch (Exception x) when (x is IOException or UnauthorizedAccessException)
        {
            // pas de fichier d'erreurs : elles restent dans la chronologie
        }
    }

    // Joue une action ; si elle échoue, l'erreur est notée et la visite continue (faux : elle a échoué).
    public bool Executer(string etape, Action action)
    {
        try
        {
            action();
            return true;
        }
        catch (Exception e)
        {
            Erreur(etape, e);
            return false;
        }
    }

    // Le signal de fin : le script sait que la visite est allée au bout.
    public void Terminer()
    {
        long t;
        lock (_verrou)
        {
            if (_fin is not null) return;
            _fin = t = _horloge();
        }
        Ecrire(new { type = "fin", t });
    }

    private static object Zone(CadreEcran z) => new { x = z.X, y = z.Y, largeur = z.Largeur, hauteur = z.Hauteur };

    // La chronologie complète : chaque étape (début, fin, jouée), ses cadrages, les erreurs, et si la visite est finie.
    public string Json()
    {
        lock (_verrou)
        {
            long? FinDe(int i)
            {
                for (int j = i + 1; j < _moments.Count; j++)
                    if (_moments[j].T > _moments[i].T || _moments[j].Jouee) return _moments[j].T;
                return _fin ?? _cadres.Where(c => c.Etape == _moments[i].Etape).Select(c => (long?)c.Fin).Max();
            }
            return JsonSerializer.Serialize(new
            {
                version = _version,
                complete = _fin is not null,
                fin = _fin,
                ecran = _ecran is { } e ? Zone(e) : null,
                etapes = _moments.Select((m, i) => new
                {
                    etape = m.Etape,
                    t = m.T,
                    fin = m.Jouee ? FinDe(i) : m.T,
                    jouee = m.Jouee,
                    cadres = m.Jouee
                        ? _cadres.Where(c => c.Etape == m.Etape)
                            .Select(c => (object)new { quoi = c.Quoi, debut = c.Debut, fin = c.Fin, zone = Zone(c.Zone), zoom = Zone(c.Zoom) }).ToList()
                        : new List<object>(),
                }).ToList(),
                erreurs = _fautes.Select(f => new { t = f.T, etape = f.Etape, message = f.Message }).ToList(),
            }, Lisible);
        }
    }

    private void Ecrire(object ligne)
    {
        if (_lignes is null || _instantane is null) return;
        try
        {
            lock (_verrou)
            {
                File.AppendAllText(_lignes, JsonSerializer.Serialize(ligne) + "\n");
                var provisoire = _instantane + ".tmp";
                File.WriteAllText(provisoire, Json());
                File.Move(provisoire, _instantane, true);
            }
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException)
        {
            // disque plein, dossier effacé : la vidéo reste bonne, la chronologie sera incomplète
        }
    }
}
