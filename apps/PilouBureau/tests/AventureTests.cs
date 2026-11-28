using PilouBureau;
using Xunit;
using static PilouBureau.Campagnes;

// La fenêtre « Aventure » et ce qui l'entoure sur le PC (Aventure.cs, Epreuves.cs) : annonce du retour une seule
// fois (différée aux heures calmes, en plein écran, Pilou absent), rattrapage au démarrage, refus croisés,
// bibliothèque, fil replié, mini-jeux et dés.
public class AventureTests
{
    private const long T0 = CampagnesVecteurs.T0;
    private static Campagne Prologue => Charger("prologue")!;
    private static Campagne? Biblio(string id) => CampagnesVecteurs.Biblio(id);
    private static readonly Aventure.Contexte Libre = new(false, false, false, false, true, false);

    // Le prologue jusqu'à sa première attente ; tout est lu (le joueur a suivi dans la fenêtre).
    private static (Carnet K, Etat E, long T) EnRoute(string appareil = "pc")
    {
        var k = new Carnet();
        long t = T0;
        Assert.Null(Demarrer(k, Prologue, 1, t, appareil, Biblio, "graine"));
        var e = Actualiser(k, Biblio, t)!;
        Assert.Equal(Phase.Choix, e.Phase);
        Assert.Null(Choisir(k, Prologue, t += 4000, appareil, e.Options[0].Id));
        e = Actualiser(k, Biblio, t)!;
        Assert.Equal(Phase.Attente, e.Phase);
        MarquerLu(k);
        return (k, e, t);
    }

    [Fact]
    public void Le_retour_est_annonce_une_seule_fois()
    {
        var (k, e, _) = EnRoute();
        // Pendant l'attente : ni signe ni annonce.
        Assert.Equal(Aventure.Aucun, Aventure.Evaluer(k, e, "", Libre));
        Assert.StartsWith("en route · ", Aventure.EtatCourt(k, e, e.T + 1000));
        Assert.StartsWith("⚑ ", Aventure.LigneBulle(e));
        // Il arrive : une annonce, avec le lieu, puis plus jamais pour ce retour ; le signe reste jusqu'à la lecture.
        var arrive = Actualiser(k, Biblio, e.Fin + 1000)!;
        Assert.Equal(Phase.Choix, arrive.Phase);
        var r = Aventure.Evaluer(k, arrive, "", Libre);
        Assert.True(r.Signe);
        Assert.Equal(Aventure.Geste.Annoncer, r.Geste);
        Assert.Equal("je suis arrivé ! j'ai besoin de toi", r.Texte);
        Assert.Equal(arrive.Lieu, r.Lieu);
        Assert.NotEqual("", r.Cle);
        Assert.Equal("il t'attend !", Aventure.EtatCourt(k, arrive, e.Fin + 2000));
        var encore = Aventure.Evaluer(k, arrive, r.Cle, Libre);
        Assert.True(encore.Signe);
        Assert.Equal(Aventure.Geste.Rien, encore.Geste);
        // La fenêtre ouverte, puis le fil lu : plus de signe.
        Assert.False(Aventure.Evaluer(k, arrive, r.Cle, Libre with { FenetreOuverte = true }).Signe);
        MarquerLu(k);
        Assert.False(Aventure.Evaluer(k, arrive, r.Cle, Libre).Signe);
        Assert.Equal("à toi de jouer", Aventure.EtatCourt(k, arrive, e.Fin + 2000));
    }

    [Fact]
    public void L_annonce_attend_les_heures_calmes_le_plein_ecran_et_le_retour_de_Pilou()
    {
        var (k, e, _) = EnRoute();
        var arrive = Actualiser(k, Biblio, e.Fin + 1000)!;
        foreach (var gene in new[] { Libre with { Calme = true }, Libre with { Discret = true }, Libre with { Absent = true }, Libre with { Pret = false } })
        {
            var r = Aventure.Evaluer(k, arrive, "", gene);
            Assert.True(r.Signe);                                   // le signe discret, oui
            Assert.Equal(Aventure.Geste.Rien, r.Geste);             // la bulle, plus tard
        }
        // Les conditions se lèvent : l'annonce part, une fois.
        Assert.Equal(Aventure.Geste.Annoncer, Aventure.Evaluer(k, arrive, "", Libre).Geste);
        // « Seulement le signe » : jamais de bulle, la clé est notée sans rien dire.
        Assert.Equal(Aventure.Geste.Taire, Aventure.Evaluer(k, arrive, "", Libre with { SigneSeul = true }).Geste);
    }

    [Fact]
    public void Au_demarrage_le_PC_rattrape_le_telephone_et_n_annonce_qu_une_fois()
    {
        // Le téléphone joue, PC éteint : deux attentes passent.
        var (tel, e, t) = EnRoute("tel");
        var pc = new Carnet();
        foreach (var m in Messages(tel, "tel", "tel")) Recevoir(pc, m, "pc", Biblio, t);
        Actualiser(pc, Biblio, t);
        MarquerLu(pc);                                              // le PC avait tout lu avant de s'éteindre
        t = e.Fin + 60_000;
        e = Actualiser(tel, Biblio, t)!;
        Assert.Equal(Phase.Choix, e.Phase);
        var option = e.Options.First(o => o.Id != e.Options[0].Id || e.Options.Count == 1);
        Assert.Null(Choisir(tel, Prologue, t, "tel", option.Id));
        e = Actualiser(tel, Biblio, t)!;
        if (e.EnAttente) e = Actualiser(tel, Biblio, t = e.Fin + 60_000)!;
        Assert.False(e.EnAttente);
        MarquerLu(tel);

        // Le PC s'allume : son vieil état d'abord (l'attente est finie depuis longtemps) ; pas d'annonce avant la lecture du groupe.
        long allume = t + 3_600_000;
        var vieux = Actualiser(pc, Biblio, allume)!;
        var avant = Aventure.Evaluer(pc, vieux, "", Libre with { Pret = false });
        Assert.Equal(Aventure.Geste.Rien, avant.Geste);
        // Il lit le groupe : l'état rejoint celui du téléphone ; une seule annonce, celle d'aujourd'hui.
        foreach (var m in Messages(tel, "tel", "tel")) Recevoir(pc, m, "pc", Biblio, allume);
        var ajour = Actualiser(pc, Biblio, allume)!;
        Assert.Equal(e.Noeud, ajour.Noeud);
        var r = Aventure.Evaluer(pc, ajour, "", Libre);
        Assert.Equal(Aventure.Geste.Annoncer, r.Geste);
        Assert.Equal(Aventure.CleRetour(pc), r.Cle);
        // Relu dix fois (le relais redonne les mêmes messages) : rien de plus.
        for (int i = 0; i < 10; i++)
        {
            foreach (var m in Messages(tel, "tel", "tel")) Recevoir(pc, m, "pc", Biblio, allume + i * 90_000);
            var x = Actualiser(pc, Biblio, allume + i * 90_000)!;
            Assert.Equal(Aventure.Geste.Rien, Aventure.Evaluer(pc, x, r.Cle, Libre).Geste);
        }
    }

    [Fact]
    public void Refus_croises_campagne_et_le_reste()
    {
        // Pilou occupé ailleurs : pas de décision de campagne (l'abandon reste permis par la façade).
        Assert.Contains("expédition", Aventure.RefusDecision(true, false, false));
        Assert.Contains("visite", Aventure.RefusDecision(false, true, false));
        Assert.Contains("Défense", Aventure.RefusDecision(false, false, true));
        Assert.Null(Aventure.RefusDecision(false, false, false));
        // En route pour sa campagne : ni expédition, ni visite, ni Défense, ni petit jeu.
        var (k, e, _) = EnRoute();
        foreach (var quoi in new[] { "expedition", "visite", "defense", "jeu" })
        {
            Assert.NotNull(Aventure.RefusPendant(quoi, e, e.T + 1000));
            Assert.Null(Aventure.RefusPendant(quoi, e, e.Fin));       // l'attente est finie
        }
        var arrive = Actualiser(k, Biblio, e.Fin + 1000)!;
        Assert.Null(Aventure.RefusPendant("expedition", arrive, e.Fin + 1000));
        Assert.Null(Aventure.RefusPendant("visite", null, T0));
    }

    [Fact]
    public void La_bibliotheque_met_le_prologue_d_abord_et_dit_ou_l_on_en_est()
    {
        var toutes = Disponibles().Select(Charger).OfType<Campagne>().ToList();
        Assert.True(toutes.Count >= 4);
        var k = new Carnet();
        var l = Aventure.Bibliotheque(k, toutes, 1, null, T0);
        Assert.Equal("prologue", l[0].Id);
        Assert.Equal(Aventure.Statut.Nouvelle, l[0].Statut);
        Assert.Equal("Commencer", l[0].Action);
        Assert.All(l.Skip(1), f => Assert.Equal(Aventure.Statut.Verrouillee, f.Statut));
        Assert.True(l.Skip(1).Select(f => f.Niveau).SequenceEqual(l.Skip(1).Select(f => f.Niveau).Order()));

        var (k2, e, _) = EnRoute();
        l = Aventure.Bibliotheque(k2, toutes, 99, e, e.T + 1000);
        Assert.Equal(Aventure.Statut.EnCours, l[0].Statut);
        Assert.Equal("Reprendre", l[0].Action);
        Assert.StartsWith("en route", l[0].Detail);
        Assert.All(l.Skip(1), f => Assert.True(f.Bloquee));
        Assert.All(l, f => Assert.InRange(f.FinsTotal, 2, 6));
        Assert.Equal("? ?", Aventure.Fins6(k2, Prologue));
    }

    [Fact]
    public void Jusqu_a_la_fin_les_gains_et_les_fins_restantes()
    {
        var k = new Carnet();
        long t = T0;
        Assert.Null(Demarrer(k, Prologue, 1, t, "pc", Biblio, "fin"));
        var e = Actualiser(k, Biblio, t)!;
        for (int i = 0; i < 200 && e.EnCours; i++)
        {
            if (e.EnAttente) t = e.Fin;
            t += 2000;
            e = Actualiser(k, Biblio, t)!;
            _ = e.Phase switch
            {
                Phase.Choix => Choisir(k, Prologue, t, "pc", e.Options[^1].Id),
                Phase.Epreuve => Epreuve(k, Prologue, t, "pc", true),
                Phase.Depart => Continuer(k, Prologue, t, "pc"),
                _ => null,
            };
            e = Actualiser(k, Biblio, t)!;
        }
        Assert.Equal(Phase.Fin, e.Phase);
        var gains = Aventure.Gains(Prologue, e);
        Assert.Contains(gains, g => g.EndsWith(" po") || g.EndsWith(" xp") || g.StartsWith("❖"));
        var fins = Aventure.Fins6(k, Prologue);
        Assert.Contains("?", fins);
        Assert.StartsWith(Aventure.SigneIssue(e.Issue), fins);
        var fiche = Aventure.Bibliotheque(k, new[] { Prologue }, 1, e, t)[0];
        Assert.Equal(Aventure.Statut.Finie, fiche.Statut);
        Assert.Equal("Rejouer", fiche.Action);
        var page = Aventure.Carnet(k, new[] { Prologue })[0];
        Assert.Single(page.Fins);
    }

    [Fact]
    public void Ce_que_Pilou_redit_apres_un_echec_est_replie()
    {
        var c = CampagnesVecteurs.Essai();
        long t = T0;
        var p = Nouvelle(c, 1, t, "pc", "g", false);
        foreach (var v in new[] { 0, Suite, Reussite, 3 })
        {
            var x = Rejouer(c, p, t);
            if (x.EnAttente) t = x.Fin;
            p = Decider(c, p, t, "pc", v)!;
            t += 1000;
        }
        var k = new Carnet { Courante = p };
        var e = Actualiser(k, Biblio, t)!;
        Assert.Equal(Phase.Repos, e.Phase);
        MarquerLu(k);
        e = Actualiser(k, Biblio, e.Fin + 1000)!;
        Assert.True(e.Reprise);
        var fil = Aventure.Fil(k, c);
        // La dernière question reste lisible (pour y répondre) ; la reprise n'est pas une nouveauté écrite en double.
        Assert.Contains(fil, x => x.Sorte == Aventure.Sorte.Chapitre);
        Assert.Contains(fil, x => x.Sorte == Aventure.Sorte.Joueur);
        Assert.Equal(Aventure.Sorte.Pilou, fil[^1].Sorte);
        Assert.Equal("me revoilà, reposé ! on reprend ?", Aventure.Evaluer(k, e, "", Libre).Texte);
    }

    [Fact]
    public void L_ecriture_lettre_a_lettre()
    {
        Assert.Equal(0, Aventure.Lettres("bonjour", 0));
        Assert.Equal(7, Aventure.Lettres("bonjour", 10_000));
        var long_ = new string('a', 600);
        Assert.True(Aventure.Lettres(long_, 3000) > Aventure.Lettres("court", 3000) || Aventure.Lettres("court", 3000) == 5);
        Assert.True(Aventure.Lettres(long_, 3000) < 600);
        Assert.Equal("moins d'une minute", Aventure.Restant(20_000));
        Assert.Equal("12 min", Aventure.Restant(11.2 * 60_000));
        Assert.Equal("1 h 05", Aventure.Restant(65 * 60_000));
    }

    [Fact]
    public void Jamais_d_opposition_rouge_vert_et_un_signe_par_etat()
    {
        var teintes = new[] { "humour", "mystere", "emotion", "epique" }.Select(Aventure.TeinteTon)
            .Concat(new[] { "bonne", "douce-amere", "mauvaise", "secrete" }.Select(Aventure.TeinteIssue)).ToList();
        foreach (var hex in teintes)
        {
            int r = Convert.ToInt32(hex[1..3], 16), g = Convert.ToInt32(hex[3..5], 16), b = Convert.ToInt32(hex[5..7], 16);
            Assert.False(r > 180 && g < 110 && b < 110, $"{hex} : rouge");
            Assert.False(g > 160 && r < 120 && b < 140, $"{hex} : vert");
        }
        var signes = new[] { "bonne", "douce-amere", "mauvaise", "secrete" }.Select(Aventure.SigneIssue).ToList();
        Assert.Equal(signes.Count, signes.Distinct().Count());
        var tons = new[] { "humour", "mystere", "emotion", "epique" }.Select(Aventure.SigneTon).ToList();
        Assert.Equal(tons.Count, tons.Distinct().Count());
        var etats = Enum.GetValues<Aventure.Statut>().Select(Aventure.SigneStatut).ToList();
        Assert.Equal(etats.Count, etats.Distinct().Count());
    }

    // ---- Mini-jeux

    // Un joueur parfait (il appuie au bon moment) et un joueur absent (il ne fait rien).
    private static (MiniJeu Jeu, double Fin) Jouer(string jeu, int difficulte, bool parfait, ulong graine, bool clavier = false)
    {
        var j = MiniJeu.Creer(jeu, difficulte, 0, graine)!;
        double t = 0;
        int note = 0;
        for (; t < 40_000 && !j.Fini; t += 16)
        {
            j.Avancer(t);
            if (!parfait || j.Fini) continue;
            switch (j)
            {
                case Reflexe r when r.Phase == Reflexe.Etape.Allume && t - r.Allumage >= 200:
                    j.Appuyer(t);
                    break;
                case Memoire m when m.Phase == Memoire.Etape.Repete && t % 400 < 16:
                    j.Appuyer(t, touche: m.Suite[m.Touches]);
                    break;
                case Rythme y when note < Rythme.Notes && t >= y.Temps[note]:
                    j.Appuyer(t);
                    note++;
                    break;
                case Visee v when clavier:
                {
                    var (px, py) = v.Position(t);
                    if (Math.Abs(px - MiniJeu.ArenaL / 2) < v.Rayon && Math.Abs(py - MiniJeu.ArenaH / 2) < v.Rayon && t - v.DernierTir > 300) j.Appuyer(t);
                    break;
                }
                case Visee v when t % 1500 < 16:
                {
                    var (x, y) = v.Position(t);
                    j.Appuyer(t, x + 3, y - 2);
                    break;
                }
            }
        }
        return (j, t);
    }

    [Theory]
    [InlineData("reflexe")]
    [InlineData("memoire")]
    [InlineData("rythme")]
    [InlineData("visee")]
    public void Chaque_epreuve_se_gagne_en_jouant_bien_et_se_perd_sans_rien_faire(string jeu)
    {
        for (int d = 1; d <= 3; d++)
            for (ulong g = 1; g <= 12; g++)
            {
                var (bon, fin) = Jouer(jeu, d, true, g);
                Assert.True(bon.Fini && bon.Reussi, $"{jeu} {d} graine {g} : raté en jouant bien ({bon.Message})");
                Assert.InRange(fin, 2_000, 25_000);
                var (rien, finRien) = Jouer(jeu, d, false, g);
                Assert.True(rien.Fini && !rien.Reussi, $"{jeu} {d} graine {g} : gagné sans rien faire");
                // Sans rien faire, on ne reste pas coincé : 25 s au plus.
                Assert.InRange(finRien, 3_000, 25_016);
            }
    }

    [Fact]
    public void Les_epreuves_sont_reproductibles_et_plus_dures_avec_la_difficulte()
    {
        var a = (Memoire)MiniJeu.Creer("memoire", 2, 0, 77)!;
        var b = (Memoire)MiniJeu.Creer("memoire", 2, 0, 77)!;
        Assert.Equal(a.Suite, b.Suite);
        Assert.True(((Memoire)MiniJeu.Creer("memoire", 3, 0, 1)!).Suite.Count > ((Memoire)MiniJeu.Creer("memoire", 1, 0, 1)!).Suite.Count);
        Assert.True(new Reflexe(3, 0, 1).Fenetre < new Reflexe(1, 0, 1).Fenetre);
        Assert.True(new Rythme(3, 0, 1).Tolerance < new Rythme(1, 0, 1).Tolerance);
        Assert.True(new Visee(3, 0, 1).Rayon < new Visee(1, 0, 1).Rayon);
        // L'aide de l'histoire (variable bonus) élargit un peu les tolérances.
        Assert.True(new Reflexe(2, 3, 1).Fenetre > new Reflexe(2, 0, 1).Fenetre);
        Assert.Null(MiniJeu.Creer("des", 2, 0, 1));
        Assert.Null(MiniJeu.Creer("inconnu", 2, 0, 1));
    }

    [Fact]
    public void Reflexe_trop_tot_perd_la_manche_et_la_visee_marche_au_clavier()
    {
        var r = new Reflexe(1, 0, 5);
        r.Appuyer(100);                                             // l'étoile n'est pas encore allumée
        Assert.Equal("trop tôt !", r.Message);
        Assert.Equal(1, r.Ratees);
        var (v, _) = Jouer("visee", 1, true, 3, clavier: true);
        Assert.True(v.Touches > 0);
        // Une fenêtre gelée longtemps : le réflexe rattrape les manches passées, sans rester coincé.
        var gel = new Reflexe(2, 0, 9);
        gel.Avancer(60_000);
        Assert.True(gel.Fini);
        Assert.False(gel.Reussi);
    }

    [Fact]
    public void Les_des_tombent_sur_un_nombre_coherent_avec_la_chance()
    {
        for (ulong g = 1; g < 200; g++)
        {
            int chance = 10 + (int)(g % 85);
            var oui = new TirageDes(chance, true, g);
            var non = new TirageDes(chance, false, g);
            Assert.InRange(oui.Final, 1, chance);
            Assert.InRange(non.Final, chance + 1, 100);
            Assert.Equal(oui.Final, oui.Valeur(TirageDes.Duree));
            Assert.False(oui.Fini(TirageDes.Duree - 1));
            Assert.True(oui.Fini(TirageDes.Duree));
        }
        // Le moteur et l'animation disent la même chose : le dé du moteur décide, l'animation suit.
        var k = new Carnet();
        long t = T0;
        var c = CampagnesVecteurs.Essai();
        var p = Nouvelle(c, 1, t, "pc", "d", false);
        foreach (var v in new[] { 0, Suite })
        {
            var x = Rejouer(c, p, t);
            if (x.EnAttente) t = x.Fin;
            p = Decider(c, p, t, "pc", v)!;
            t += 1000;
        }
        var e = Rejouer(c, p, t);
        if (e.EnAttente) e = Rejouer(c, p, t = e.Fin);
        Assert.Equal(Phase.Epreuve, e.Phase);
        bool de = DeDe(c, p, e);
        var tirage = new TirageDes(e.Chance, de, 42);
        Assert.Equal(de, tirage.Final <= e.Chance);
        _ = k;
    }

    // Une campagne fermée par un haut fait et par une autre campagne : la bibliothèque dit ce qui manque (une ligne, le
    // signe ▣), le démarrage est refusé avec le même texte, puis tout s'ouvre une fois le haut fait obtenu et le prologue fini.
    [Fact]
    public void Une_campagne_s_ouvre_par_un_haut_fait_et_une_campagne_finie()
    {
        var hf = CampagnesVecteurs.HautFait();
        Assert.Equal(new[] { "plume" }, hf.Succes);
        Assert.Equal(new[] { "prologue" }, hf.Apres);
        var toutes = new[] { Prologue, hf };
        var k = new Carnet();
        var f = Aventure.Bibliotheque(k, toutes, 2, null, T0, new[] { "marathon" }).Single(x => x.Id == hf.Id);
        Assert.Equal(Aventure.Statut.Verrouillee, f.Statut);
        Assert.Equal("▣", Aventure.SigneStatut(f.Statut));
        Assert.Equal("s'ouvre avec le haut fait « Plume » et après « La colline d'en face »", f.Detail);
        Assert.Equal("haut fait", f.Verrou);
        Assert.Equal("niveau 2", Aventure.Bibliotheque(k, toutes, 1, null, T0).Single(x => x.Id == hf.Id).Verrou);
        Assert.Equal(f.Detail, Demarrer(k, hf, 2, T0, "pc", CampagnesVecteurs.Biblio, "g", false, new[] { "marathon" }));
        Assert.Null(Demarrer(k, hf, 2, T0, "pc", CampagnesVecteurs.Biblio, "g")); // sans liste de hauts faits : pas vérifié (essai)
        var k2 = new Carnet();
        Recevoir(k2, "{\"v\":1,\"a\":\"pc-z\",\"k\":\"pc\",\"h\":{\"prologue\":[1,1,{\"" + Code("fin-x") + "\":1790000000},\"\"]}}", "pc", CampagnesVecteurs.Biblio, T0);
        var ouverte = Aventure.Bibliotheque(k2, toutes, 2, null, T0, new[] { "plume" }).Single(x => x.Id == hf.Id);
        Assert.Equal(Aventure.Statut.Nouvelle, ouverte.Statut);
        Assert.Null(Demarrer(k2, hf, 2, T0, "pc", CampagnesVecteurs.Biblio, "g", false, new[] { "plume" }));
    }

    // Aucune des campagnes embarquées ne s'ouvre par un haut fait ni par une autre campagne (pas encore) : seul le niveau.
    [Fact]
    public void Les_campagnes_embarquees_ne_demandent_que_le_niveau()
    {
        foreach (var id in Disponibles())
        {
            var c = Charger(id)!;
            Assert.Empty(c.Succes);
            Assert.Empty(c.Apres);
            Assert.Equal(c.Niveau <= 1 ? "" : $"s'ouvre au niveau {c.Niveau}", Manque(new Carnet(), c, 1, Array.Empty<string>(), Charger));
        }
    }
}
