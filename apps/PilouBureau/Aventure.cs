using System.Globalization;
using static PilouBureau.Campagnes;

namespace PilouBureau;

// Les campagnes vues par l'interface du PC (fenêtre « Aventure », bulle, menus, icône près de l'horloge), sans WPF :
// testable. Le moteur (Campagnes.cs) dit où en est l'histoire ; ici, ce que l'on en montre et quand on le dit.
//
// Règles (docs/CAMPAGNES.md, « Sur Windows ») :
//   - chaque état a un signe de forme, jamais une opposition rouge / vert (orange, bleu, violet, crème) ;
//   - le retour de Pilou est annoncé UNE fois (bulle et petit saut), jamais relancé ; pendant les heures calmes, en
//     plein écran, en visio ou s'il est absent (expédition, visite), l'annonce attend ; un signe « ! » discret reste
//     sur Pilou et dans le menu de l'icône tant que la fenêtre n'a pas été ouverte ;
//   - au démarrage, rien n'est annoncé avant la première lecture du groupe : le PC rattrape ce que le téléphone a
//     fait, puis annonce une seule fois l'état à jour.
public static class Aventure
{
    // ---- Signes et teintes (couleurs en #rrggbb, lues par la fenêtre et par les maquettes)

    public const string Orange = "#f69d50", Bleu = "#6cb6ff", Violet = "#9b8cff", Creme = "#e8d5b0", Or = "#f5d76e", Ardoise = "#768390",
        BleuClair = "#b4dbff";

    public static string SigneTon(string ton) => ton switch
    {
        "humour" => "☺", "mystere" => "◈", "emotion" => "♥", "epique" => "⚔", _ => "✦",
    };

    public static string NomTon(string ton) => ton switch
    {
        "humour" => "drôle", "mystere" => "mystère", "emotion" => "émouvante", "epique" => "épique", _ => ton,
    };

    public static string TeinteTon(string ton) => ton switch
    {
        "humour" => Orange, "mystere" => Violet, "emotion" => Creme, "epique" => Bleu, _ => BleuClair,
    };

    public static string SigneIssue(string issue) => issue switch
    {
        "bonne" => "★", "douce-amere" => "◐", "mauvaise" => "✕", "secrete" => "✦", _ => "◇",
    };

    public static string NomIssue(string issue) => issue switch
    {
        "bonne" => "belle fin", "douce-amere" => "fin douce-amère", "mauvaise" => "fin sombre", "secrete" => "fin secrète", _ => "fin",
    };

    public static string TeinteIssue(string issue) => issue switch
    {
        "bonne" => Or, "douce-amere" => Violet, "mauvaise" => Ardoise, "secrete" => Bleu, _ => BleuClair,
    };

    public static string SigneJeu(string jeu) => jeu switch
    {
        "reflexe" => "⚡", "memoire" => "◆", "rythme" => "♪", "visee" => "◎", _ => "⚄",
    };

    public static string NomJeu(string jeu) => jeu switch
    {
        "reflexe" => "Réflexe", "memoire" => "Mémoire", "rythme" => "Rythme", "visee" => "Visée", _ => "Les dés",
    };

    public static string Consigne(string jeu) => jeu switch
    {
        "reflexe" => "Quand l'étoile s'allume, clique (ou Espace) tout de suite. Pas avant !",
        "memoire" => "Regarde la suite de signes, puis refais-la : clic, ou touches 1 à 4.",
        "rythme" => "Clique (ou Espace) quand chaque note passe sur la ligne.",
        "visee" => "Clique sur la luciole (ou Espace quand elle passe dans le viseur).",
        _ => "Les dés décident : tu n'as rien à faire.",
    };

    // Nombre de pastilles pleines pour la difficulté (◆◆◇).
    public static string Pastilles(int difficulte) =>
        new string('◆', Math.Clamp(difficulte, 1, 3)) + new string('◇', 3 - Math.Clamp(difficulte, 1, 3));

    // ---- Temps

    // « 12 min », « 1 h 05 », « moins d'une minute ».
    public static string Restant(double ms)
    {
        if (ms < 60_000) return "moins d'une minute";
        int min = (int)Math.Ceiling(ms / 60_000);
        return min < 60 ? $"{min} min" : $"{min / 60} h {min % 60:00}";
    }

    public static string Heure(long ms) => Heure(DateTimeOffset.FromUnixTimeMilliseconds(ms).LocalDateTime);

    public static string Heure(DateTime local) => string.Create(CultureInfo.InvariantCulture, $"{local.Hour} h {local.Minute:00}");

    // ---- État court (menu clic droit, menu de l'icône)

    public static bool Attend(Carnet k, Etat? e) =>
        e is { Phase: Phase.Choix or Phase.Epreuve or Phase.Depart or Phase.Fin } && k.NonLus > 0;

    // « en route · 12 min », « se repose · 40 min », « il t'attend ! », « à toi de jouer », « finie » ; "" : aucune partie.
    public static string EtatCourt(Carnet k, Etat? e, long maintenant)
    {
        if (e is null) return "";
        if (Attend(k, e)) return "il t'attend !";
        return e.Phase switch
        {
            Phase.Attente => $"en route · {Restant(e.Fin - maintenant)}",
            Phase.Repos => $"se repose · {Restant(e.Fin - maintenant)}",
            Phase.Choix or Phase.Epreuve or Phase.Depart => "à toi de jouer",
            Phase.Fin => "finie",
            _ => "",
        };
    }

    // La ligne de la bulle pendant une attente ou un repos : « ⚑ Pilou longe la falaise · retour vers 15 h 40 ».
    public static string LigneBulle(Etat? e) =>
        e is { EnAttente: true } ? "⚑ " + Ligne(e, DateTimeOffset.FromUnixTimeMilliseconds(e.Fin).LocalDateTime) : "";

    // Au survol de cette ligne : le chapitre et le lieu.
    public static string DetailBulle(Etat? e)
    {
        if (e is null) return "";
        var l = new List<string>();
        if (e.ChapitreTitre != "") l.Add($"Chapitre {e.ChapitreNumero}/{e.ChapitreTotal} · {e.ChapitreTitre}");
        if (e.Lieu != "") l.Add("▸ " + e.Lieu);
        l.Add("clic : ouvrir l'aventure");
        return string.Join("\n", l);
    }

    // ---- Le retour : annoncé une fois, signe discret tant que ce n'est pas lu

    public enum Geste { Rien, Annoncer, Taire }

    // FenetreOuverte : la fenêtre Aventure est visible (elle lit le fil elle-même). Calme : heures calmes. Discret :
    // plein écran, présentation, visio, Pilou caché. Absent : en expédition ou en visite. Pret : la première lecture du
    // groupe est faite (ou il n'y a pas de groupe). SigneSeul : réglage « seulement le signe », aucune bulle.
    public readonly record struct Contexte(bool FenetreOuverte, bool Calme, bool Discret, bool Absent, bool Pret, bool SigneSeul);

    // Signe : le « ! » sur Pilou et dans les menus. Geste : ce qu'il faut faire maintenant (Annoncer, ou Taire : noter
    // la clé comme annoncée sans rien montrer). Cle : ce qui identifie ce retour (le dernier message de Pilou).
    public sealed record Retour(bool Signe, Geste Geste, string Cle, string Texte, string Lieu);

    public static readonly Retour Aucun = new(false, Geste.Rien, "", "", "");

    public static string CleRetour(Carnet k)
    {
        var m = k.Fil.LastOrDefault(x => x.Qui == "pilou");
        return m is null ? "" : string.Create(CultureInfo.InvariantCulture, $"{m.P}.{m.E}.{m.I}");
    }

    public static Retour Evaluer(Carnet k, Etat? e, string dejaAnnonce, Contexte c)
    {
        if (e is null || !Attend(k, e) || c.FenetreOuverte) return Aucun;
        var cle = CleRetour(k);
        var texte = e.Phase switch
        {
            Phase.Fin => "je suis de retour… viens voir comment ça finit",
            Phase.Depart => "me revoilà ! je repars quand tu me dis « vas-y »",
            _ when e.Reprise => "me revoilà, reposé ! on reprend ?",
            _ => "je suis arrivé ! j'ai besoin de toi",
        };
        var geste = cle == dejaAnnonce || !c.Pret ? Geste.Rien
            : c.SigneSeul ? Geste.Taire
            : c.Calme || c.Discret || c.Absent ? Geste.Rien
            : Geste.Annoncer;
        return new Retour(true, geste, cle, texte, e.Lieu);
    }

    // ---- Refus croisés : une campagne qui attend et le reste (expédition, visite, Défense, petits jeux)

    // Pourquoi Pilou ne peut pas répondre à sa campagne maintenant (null s'il le peut). L'abandon reste toujours permis.
    public static string? RefusDecision(bool expedition, bool visite, bool defense) =>
        expedition ? "Pilou est en expédition : la campagne attendra son retour"
        : visite ? "Pilou est en visite chez un ami : la campagne attendra son retour"
        : defense ? "Pilou joue à Défense du bureau : la campagne attendra la fin de la partie"
        : null;

    // Pourquoi Pilou ne peut pas faire autre chose (quoi : expedition, visite, defense, jeu) pendant l'attente ou le
    // repos d'une campagne ; null s'il le peut.
    public static string? RefusPendant(string quoi, Etat? e, long maintenant)
    {
        if (e is not { EnAttente: true } || maintenant >= e.Fin) return null;
        string ou = e.Phase == Phase.Repos ? "Pilou se repose de son aventure" : "Pilou est en route pour son aventure";
        return quoi switch
        {
            "expedition" => $"{ou} : l'expédition attendra son retour",
            "visite" => $"{ou} : la visite attendra son retour",
            "defense" => $"{ou} : on jouera à son retour",
            _ => $"{ou} : on jouera à son retour",
        };
    }

    // ---- La bibliothèque : les campagnes, le prologue d'abord

    public enum Statut { Verrouillee, Nouvelle, EnCours, Suspendue, Finie }

    public sealed record Fiche(string Id, string Titre, string Ton, string Accroche, string Duree, int Niveau, Statut Statut,
        double Progression, int Fins, int FinsTotal, string Action, string Detail, bool Bloquee);

    public static int TotalFins(Campagne c) => c.Noeuds.Values.Count(n => n.Type == "fin");

    public static List<Fiche> Bibliotheque(Carnet k, IEnumerable<Campagne> campagnes, int niveau, Etat? e, long maintenant)
    {
        var l = new List<Fiche>();
        string courante = e is { EnCours: true } && k.Courante is { } p ? p.Campagne : "";
        foreach (var c in campagnes.OrderBy(c => c.Id == "prologue" ? 0 : 1).ThenBy(c => c.Niveau).ThenBy(c => c.Titre, StringComparer.CurrentCulture))
        {
            int fins = Fins(k, c).Count, total = TotalFins(c);
            Statut s;
            double prog = 0;
            string action, detail;
            if (c.Id == courante)
            {
                s = Statut.EnCours;
                prog = e!.Progression;
                action = "Reprendre";
                detail = EtatCourt(k, e, maintenant) is { Length: > 0 } ec ? ec : $"chapitre {e.ChapitreNumero}/{e.ChapitreTotal}";
            }
            else if (niveau < c.Niveau)
            {
                s = Statut.Verrouillee;
                action = "";
                detail = $"s'ouvre au niveau {c.Niveau}";
            }
            else if (k.Suspendues.TryGetValue(c.Id, out var sp) || (k.Courante is { } q && q.Campagne == c.Id && Reprenable(k, c, maintenant)))
            {
                s = Statut.Suspendue;
                var partie = sp ?? k.Courante!;
                prog = Math.Clamp(Rejouer(c, partie, maintenant).Progression, 0, 1);
                action = "Reprendre";
                detail = "reprend au dernier check-point";
            }
            else if (fins > 0)
            {
                s = Statut.Finie;
                prog = 1;
                action = "Rejouer";
                detail = fins >= total ? "toutes les fins trouvées !" : $"{total - fins} fin{(total - fins > 1 ? "s" : "")} à découvrir";
            }
            else
            {
                s = Statut.Nouvelle;
                action = "Commencer";
                detail = "pas encore commencée";
            }
            bool bloquee = courante != "" && c.Id != courante && s != Statut.Verrouillee;
            l.Add(new Fiche(c.Id, c.Titre, c.Ton, c.Accroche, c.Duree, c.Niveau, s, prog, fins, total, action, detail, bloquee));
        }
        return l;
    }

    public static string SigneStatut(Statut s) => s switch
    {
        Statut.Verrouillee => "▣", Statut.Nouvelle => "▶", Statut.EnCours => "◉", Statut.Suspendue => "◌", _ => "✓",
    };

    // « ★ ◐ ? ? ? ? » : les fins trouvées (leur signe), puis un « ? » par fin restante.
    public static string Fins6(Carnet k, Campagne c)
    {
        var trouvees = Fins(k, c).Select(f => SigneIssue(f.Issue)).ToList();
        int reste = Math.Max(0, TotalFins(c) - trouvees.Count);
        return string.Join(" ", trouvees.Concat(Enumerable.Repeat("?", reste)));
    }

    // ---- Le fil, tel que la fenêtre le montre

    public enum Sorte { Chapitre, Pilou, Joueur, Reprise }

    // Un élément du fil. Nouveau : pas encore lu (à écrire lettre à lettre). Sous : les messages repliés d'une reprise.
    public sealed record Element(Sorte Sorte, string Texte, string Humeur, string Lieu, string Decor, bool Nouveau, string Cle,
        IReadOnlyList<string> Sous);

    // Le fil de la partie en cours : séparateurs de chapitre, messages de Pilou et choix du joueur ; ce que Pilou redit
    // au retour d'un échec est replié en une ligne « Bon. On reprend ici. », sauf la dernière question (pour répondre).
    public static List<Element> Fil(Carnet k, Campagne c)
    {
        var l = new List<Element>();
        if (k.Courante is not { } p) return l;
        var messages = k.Fil.Where(m => m.P == p.P).ToList();
        string chapitre = "";
        for (int i = 0; i < messages.Count; i++)
        {
            var m = messages[i];
            var ch = c.Noeud(m.Noeud)?.Chapitre ?? "";
            if (ch != "" && ch != chapitre)
            {
                chapitre = ch;
                int n = c.Chapitres.FindIndex(x => x.Id == ch);
                if (n >= 0) l.Add(new Element(Sorte.Chapitre, $"Chapitre {n + 1} · {c.Chapitres[n].Titre}", "", "", "", false, "ch:" + ch, Array.Empty<string>()));
            }
            var cle = string.Create(CultureInfo.InvariantCulture, $"{m.P}.{m.E}.{m.I}");
            if (m.Reprise && m.Qui == "pilou")
            {
                // La suite des messages redits, sauf le dernier s'il clôt le fil (la question à laquelle répondre).
                int j = i;
                while (j + 1 < messages.Count && messages[j + 1].Reprise && messages[j + 1].Qui == "pilou") j++;
                bool dernierOuvert = j == messages.Count - 1;
                int fin = dernierOuvert ? j - 1 : j;
                if (fin >= i)
                {
                    var sous = messages.Skip(i).Take(fin - i + 1).Select(x => x.Texte).ToList();
                    l.Add(new Element(Sorte.Reprise, "↺ Bon. On reprend ici.", "determine", m.Lieu, m.Decor, NonLu(k, messages[fin]), cle, sous));
                }
                if (dernierOuvert)
                {
                    var d = messages[j];
                    l.Add(new Element(Sorte.Pilou, d.Texte, d.Humeur, d.Lieu, d.Decor, NonLu(k, d),
                        string.Create(CultureInfo.InvariantCulture, $"{d.P}.{d.E}.{d.I}"), Array.Empty<string>()));
                }
                i = j;
                continue;
            }
            l.Add(new Element(m.Qui == "joueur" ? Sorte.Joueur : Sorte.Pilou, m.Texte, m.Humeur, m.Lieu, m.Decor,
                m.Qui == "pilou" && NonLu(k, m), cle, Array.Empty<string>()));
        }
        return l;
    }

    // Vitesse d'écriture d'un message (ms par caractère) et pause « Pilou écrit… » entre deux messages.
    public const double MsParLettre = 18, PauseEntreMessages = 650;

    // Combien de lettres d'un message sont écrites après ms (l'écriture accélère un peu sur les longs messages).
    public static int Lettres(string texte, double ms) =>
        ms <= 0 ? 0 : Math.Min(texte.Length, (int)(ms / Math.Max(8, MsParLettre - texte.Length / 40.0)));

    // ---- Carnet : souvenirs, fins, titres de toutes les campagnes

    public sealed record Page(Campagne Campagne, List<FinObtenue> Fins, List<Nomme> Souvenirs, List<string> Titres, List<string> Objets, int FinsTotal);

    public static List<Page> Carnet(Carnet k, IEnumerable<Campagne> campagnes) =>
        campagnes.OrderBy(c => c.Id == "prologue" ? 0 : 1).ThenBy(c => c.Niveau)
            .Select(c => new Page(c, Fins(k, c), Souvenirs(k, c), Titres(k, c), ObjetsGagnes(k, c), TotalFins(c))).ToList();

    // Nom d'un objet de campagne (sac à dos, récompenses) : celui de la fiche, sinon l'identifiant.
    public static string NomObjet(Campagne c, string id) => c.Objets.FirstOrDefault(o => o.Id == id)?.Nom is { Length: > 0 } n ? n : id;

    public static string NomDecor(Campagne c, string id) => c.Decors.FirstOrDefault(d => d.Id == id)?.Nom ?? "";

    // Sprite d'un décor dans la banque (un illustrateur les ajoute) : « decor-<campagne>-<decor> ».
    public static string SpriteDecor(string campagne, string decor) => decor == "" ? "" : $"decor-{campagne}-{decor}";

    // ---- Récompenses d'une fin, en lignes courtes (« +40 po », « ✦ Bonnet de givre »…)

    public static List<string> Gains(Campagne c, Etat e)
    {
        var l = new List<string>();
        var r = e.Recompenses;
        if (!e.Rejeu && r.Po > 0) l.Add($"+{r.Po} po");
        if (!e.Rejeu && r.Xp > 0) l.Add($"+{r.Xp} xp");
        if (r.Titre != "") l.Add($"✧ titre « {r.Titre} »");
        if (r.Objet != "") l.Add($"✦ {NomObjet(c, r.Objet)} (objet exclusif)");
        if (r.Souvenir != "" && c.Souvenir(r.Souvenir) is { } s) l.Add($"❖ souvenir : {s.Nom}");
        return l;
    }
}
