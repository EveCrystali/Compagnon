using System.Text.Json;
using PilouBureau;
using Xunit;
using static PilouBureau.Campagnes;

// Matière des maquettes de la fenêtre Aventure (rendu hors WPF) : les portraits fins de Pilou (humeurs, tenues de
// voyage) en PNG et les données d'une partie de démonstration (fil, options, attente, épreuve, fin, bibliothèque) en
// JSON, que outils/maquettes/aventure.py compose. Seulement si PILOU_PLANCHES_AVENTURE donne un dossier :
//     PILOU_PLANCHES_AVENTURE=/tmp/aventure dotnet test --filter PlanchesAventure
public class PlanchesAventure
{
    private static readonly string? Dossier = Environment.GetEnvironmentVariable("PILOU_PLANCHES_AVENTURE");
    private static readonly Lazy<Banque> B = new(() => Banque.DepuisDossier(Path.Combine(DefenseTests.Racine(), "assets")));

    private static void Pilou(string nom, Allure a)
    {
        var px = RenduPilou.Rendre(a, B.Value, 2);
        Png.Ecrire(Path.Combine(Dossier!, nom + ".png"), px, RenduPilou.W * 2, RenduPilou.H * 2);
    }

    // Une partie du prologue jouée jusqu'à l'état voulu (comme --essai=campagne:…).
    private static (Carnet K, Etat E) Partie(string quoi, long maintenant)
    {
        var c = Charger("prologue")!;
        var k = new Carnet();
        long t = quoi == "attente" ? maintenant - 30_000 : maintenant - 20 * 3_600_000L;
        Demarrer(k, c, 99, t, "pc", Charger, "vitrine");
        for (int pas = 0; pas < 400; pas++)
        {
            var e = Actualiser(k, Charger, t)!;
            bool arrete = quoi switch
            {
                "attente" => e.Phase == Phase.Attente,
                "lecture" => e.Phase == Phase.Choix && k.Fil.Any(m => m.Qui == "joueur"),
                "epreuve" => e.Phase == Phase.Epreuve,
                _ => !e.EnCours,
            };
            if (arrete || !e.EnCours) break;
            switch (e.Phase)
            {
                case Phase.Choix:
                    var n = c.Noeud(e.Noeud)!;
                    var o = quoi == "epreuve" ? e.Options.FirstOrDefault(x => c.Noeud(n.Options.First(y => y.Id == x.Id).Vers)?.Type == "epreuve") ?? e.Options[0] : e.Options[0];
                    Choisir(k, c, t += 3000, "pc", o.Id);
                    break;
                case Phase.Epreuve:
                    Epreuve(k, c, t += 3000, "pc", true);
                    break;
                case Phase.Depart:
                    Continuer(k, c, t += 3000, "pc");
                    break;
                default:
                    t = quoi == "attente" ? t + 1000 : e.Fin + 60_000;
                    break;
            }
        }
        var etat = Actualiser(k, Charger, Math.Max(t, maintenant))!;
        MarquerLu(k);
        return (k, etat);
    }

    private static object Vue(Carnet k, Etat e, Campagne c, long maintenant) => new
    {
        campagne = c.Titre, ton = c.Ton, phase = e.Phase.ToString(), chapitre = e.ChapitreNumero, chapitres = e.ChapitreTotal, chapitreTitre = e.ChapitreTitre,
        progression = e.Progression, lieu = e.Lieu, decor = e.Decor, humeur = e.Humeur, pendant = e.Pendant, tenue = e.Tenue, reprise = e.Reprise,
        retour = e.Fin > 0 ? Aventure.Heure(DateTimeOffset.FromUnixTimeMilliseconds(e.Fin).UtcDateTime) : "",
        reste = e.Fin > 0 ? Aventure.Restant(e.Fin - maintenant) : "", part = e.Fin > e.T ? 1 - (e.Fin - maintenant) / (double)(e.Fin - e.T) : 0,
        options = e.Options.Select(o => o.Libelle).ToList(),
        jeu = e.Jeu, nomJeu = Aventure.NomJeu(e.Jeu), signeJeu = Aventure.SigneJeu(e.Jeu), difficulte = Aventure.Pastilles(e.Difficulte), chance = e.Chance,
        consigne = Aventure.Consigne(e.Jeu), aide = e.Aide,
        issue = e.Issue, signeIssue = Aventure.SigneIssue(e.Issue), nomIssue = Aventure.NomIssue(e.Issue), teinteIssue = Aventure.TeinteIssue(e.Issue),
        titreFin = e.TitreFin, gains = e.Phase == Phase.Fin ? Aventure.Gains(c, e) : new List<string>(), fins = Aventure.Fins6(k, c),
        objets = e.Objets.Select(o => Aventure.NomObjet(c, o)).ToList(),
        fil = Aventure.Fil(k, c).Select(x => new { sorte = x.Sorte.ToString(), texte = x.Texte, humeur = x.Humeur, lieu = x.Lieu }).ToList(),
    };

    [Fact]
    public void Planches()
    {
        if (string.IsNullOrEmpty(Dossier)) return;
        Directory.CreateDirectory(Dossier);
        foreach (var h in Humeurs) Pilou("pilou-" + h, new Allure { Expr = h == "neutre" ? "repos" : h, T = 1200 });
        Pilou("pilou-repos", new Allure { Expr = "repos", T = 1200 });
        foreach (var v in RenduPilou.Voyages)
            for (int i = 0; i < 3; i++)
                Pilou($"voyage-{v}-{i}", new Allure { Tenue = "voyage-" + v, T = 300 + i * 333 });
        Pilou("voyage-nuit-pansement", new Allure { Tenue = "voyage-nuit", T = 300, Objets = new[] { "pansement" } });

        long maintenant = CampagnesVecteurs.T0 + 15 * 3_600_000L;
        var c = Charger("prologue")!;
        var vues = new Dictionary<string, object>();
        foreach (var quoi in new[] { "lecture", "attente", "epreuve", "fin" })
        {
            var (k, e) = Partie(quoi, maintenant);
            vues[quoi] = Vue(k, e, c, quoi == "attente" ? e.T + (e.Fin - e.T) * 2 / 5 : maintenant);
        }
        // La bibliothèque d'un joueur de niveau 6 : le prologue fini une fois, La Grande Panne en cours.
        var toutes = Disponibles().Select(Charger).OfType<Campagne>().ToList();
        var (kb, _) = Partie("fin", maintenant);
        var gp = Charger("grande-panne")!;
        long t = maintenant - 3_600_000;
        Demarrer(kb, gp, 6, t, "pc", Charger, "biblio");
        var eb = Actualiser(kb, Charger, t)!;
        for (int i = 0; i < 12 && eb.EnCours; i++)
        {
            if (eb.EnAttente) t = eb.Fin + 1000;
            else if (eb.Phase == Phase.Choix) Choisir(kb, gp, t += 2000, "pc", eb.Options[0].Id);
            else if (eb.Phase == Phase.Depart) Continuer(kb, gp, t += 2000, "pc");
            else if (eb.Phase == Phase.Epreuve) Epreuve(kb, gp, t += 2000, "pc", true);
            eb = Actualiser(kb, Charger, t)!;
        }
        // On la laisse en route : l'attente en cours.
        if (!eb.EnAttente && eb.Phase == Phase.Choix)
        {
            Choisir(kb, gp, t += 2000, "pc", eb.Options[0].Id);
            eb = Actualiser(kb, Charger, t)!;
        }
        var fiches = Aventure.Bibliotheque(kb, toutes, 6, eb, t + 60_000).Select(f => new
        {
            id = f.Id, titre = f.Titre, ton = f.Ton, signeTon = Aventure.SigneTon(f.Ton), nomTon = Aventure.NomTon(f.Ton), teinte = Aventure.TeinteTon(f.Ton),
            accroche = f.Accroche, duree = f.Duree, niveau = f.Niveau, statut = f.Statut.ToString(), signe = Aventure.SigneStatut(f.Statut),
            progression = f.Progression, fins = Aventure.Fins6(kb, toutes.First(x => x.Id == f.Id)), action = f.Action, detail = f.Detail, bloquee = f.Bloquee,
        }).ToList();
        vues["bibliotheque"] = fiches;
        File.WriteAllText(Path.Combine(Dossier, "donnees.json"), JsonSerializer.Serialize(vues, new JsonSerializerOptions { WriteIndented = true }));
        // Les épreuves à un instant parlant (pour l'arène des maquettes).
        var r = new Reflexe(1, 0, 3);
        r.Avancer(r.Allumage + 120);
        var m = new Memoire(2, 0, 5);
        var y = new Rythme(2, 0, 7);
        for (double tt = 0; tt < 4300; tt += 16)
        {
            y.Avancer(tt);
            if (y.Temps.Take(2).Any(x => Math.Abs(x - tt) < 10)) y.Appuyer(tt);
        }
        File.WriteAllText(Path.Combine(Dossier, "epreuves.json"), JsonSerializer.Serialize(new
        {
            reflexe = new { manche = r.Manche, touches = r.Touches, besoin = r.Besoin },
            memoire = new { suite = m.Suite, allume = m.SigneAllume(m.Debut + 10) },
            rythme = new { temps = y.Temps, t = 4300, jugees = y.Jugees, touches = y.Touches, besoin = y.Besoin },
            des = new { chance = 55, final = new TirageDes(55, true, 42).Final },
        }));
    }
}
