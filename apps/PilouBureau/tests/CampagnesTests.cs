using System.Text;
using System.Text.Json;
using PilouBureau;
using Xunit;
using Xunit.Abstractions;
using static PilouBureau.Campagnes;

public class CampagnesTests(ITestOutputHelper sortie)
{
    private const long T0 = CampagnesVecteurs.T0;
    private const string Code = "ABCD-EFGH-JKMN-PQRS";

    private static Campagne Essai => CampagnesVecteurs.Essai();
    private static Campagne Prologue => Charger("prologue")!;
    private static Campagne? Biblio(string id) => CampagnesVecteurs.Biblio(id);

    // ---- Vecteurs partagés avec le téléphone

    [Fact]
    public void Le_telephone_rejoue_les_memes_vecteurs()
    {
        var chemin = Path.Combine(CampagnesVecteurs.Racine().FullName, CampagnesVecteurs.Reference);
        var texte = CampagnesVecteurs.Tout();
        Assert.Equal(texte, CampagnesVecteurs.Tout()); // le scénario lui-même est reproductible
        if (Environment.GetEnvironmentVariable("PILOU_REGENERER") == "1") File.WriteAllText(chemin, texte);
        Assert.True(File.Exists(chemin), $"{CampagnesVecteurs.Reference} manque : PILOU_REGENERER=1 dotnet test");
        var attendu = File.ReadAllText(chemin).Replace("\r\n", "\n");
        if (attendu != texte)
        {
            var a = attendu.Split('\n');
            var b = texte.Split('\n');
            int i = 0;
            while (i < a.Length && i < b.Length && a[i] == b[i]) i++;
            Assert.Fail($"vecteurs différents à la ligne {i + 1} (PILOU_REGENERER=1 dotnet test si le moteur a changé exprès) :\n"
                        + $"fichier : {(i < a.Length ? a[i] : "(fin)")}\nmoteur  : {(i < b.Length ? b[i] : "(fin)")}");
        }
        sortie.WriteLine($"{texte.Split('\n').Length} lignes, {Encoding.UTF8.GetByteCount(texte)} octets");
    }

    // ---- Embarquement et lecture

    [Fact]
    public void Le_prologue_est_embarque_et_se_lit()
    {
        Assert.Contains("prologue", Disponibles());
        var c = Prologue;
        Assert.Equal("La colline d'en face", c.Titre);
        Assert.Equal("humour", c.Ton);
        Assert.Equal(1, c.Niveau);
        Assert.Equal(2, c.Chapitres.Count);
        Assert.InRange(c.Noeuds.Count, 15, 25);
        Assert.Equal("recit", c.Noeud(c.Depart)!.Type);
        Assert.True(c.Noeud("p2-pied")!.Checkpoint);
        Assert.Equal(6, c.Decors.Count);
        Assert.Equal("peur", c.Noeud("p1-mare")!.Humeur);
        Assert.Null(Charger("inconnue"));
        // Toutes les campagnes embarquées se lisent, et leur départ existe.
        foreach (var id in Disponibles())
        {
            var x = Charger(id);
            Assert.NotNull(x);
            Assert.NotNull(x!.Noeud(x.Depart));
        }
    }

    [Fact]
    public void Champs_inconnus_et_fichiers_abimes_ne_cassent_rien()
    {
        Assert.Null(Lire("pas du json", _ => null));
        Assert.Null(Lire("{\"titre\":\"sans id\"}", _ => null));
        var c = Lire("{\"v\":1,\"id\":\"x\",\"depart\":\"a\",\"futur\":{\"a\":1},\"chapitres\":[{\"id\":\"c1\",\"fichier\":\"un.json\"},{\"id\":\"c2\",\"fichier\":\"absent.json\"},"
                     + "{\"id\":\"c3\",\"fichier\":\"casse.json\"}]}",
            f => f == "un.json" ? "{\"noeuds\":{\"a\":{\"type\":\"recit\",\"texte\":\"un seul paragraphe\",\"humeur\":\"jamais-vue\",\"nouveau\":[1,2],\"suite\":\"b\"},"
                                  + "\"b\":{\"type\":\"teleportation\"}}}"
                : f == "casse.json" ? "{" : null)!;
        Assert.Equal(2, c.Noeuds.Count);
        Assert.Equal("neutre", c.Noeud("a")!.Humeur);
        Assert.Equal(new[] { "un seul paragraphe" }, c.Noeud("a")!.Texte);
        // Un type de nœud inconnu : la partie s'arrête proprement (« cassée »), sans exception.
        var e = Rejouer(c, Nouvelle(c, 1, T0, "pc", "g", false), T0);
        Assert.Equal(Phase.Cassee, e.Phase);
    }

    // ---- Le moteur

    private static Partie Jouer(Campagne c, Partie p, ref long t, string appareil, params int[] valeurs)
    {
        foreach (var v in valeurs)
        {
            var e = Rejouer(c, p, t);
            if (e.EnAttente) t = e.Fin;
            var q = Decider(c, p, t, appareil, v);
            Assert.True(q is not null, $"décision {v} refusée au nœud {Rejouer(c, p, t).Noeud} ({Rejouer(c, p, t).Phase})");
            p = q!;
            t += 1000;
        }
        return p;
    }

    [Fact]
    public void Conditions_effets_et_options_proposees()
    {
        var c = Essai;
        long t = T0;
        var p = Nouvelle(c, 1, t, "pc", "g", false);
        var e = Rejouer(c, p, t);
        Assert.Equal(Phase.Choix, e.Phase);
        Assert.Equal("a-carrefour", e.Noeud);
        Assert.Equal(2, e.Variables["courage"]);                       // 1 au départ, +1 à l'entrée
        Assert.Contains("parti", e.Drapeaux);
        // « sud » demande courage ≥ 2 ; « secret » : drapeau parti, pas de clé, et (ruse ≤ 0 ou du pain).
        Assert.Equal(new[] { "nord", "sud", "secret", "boucle" }, e.Options.Select(o => o.Id));
        Assert.Equal("Le départ", e.Lieu);
        Assert.Equal("d-un", e.Decor);
        Assert.Equal("determine", e.Humeur);
        Assert.Equal(new[] { "joie", "joie", "determine" }, e.Messages.Select(m => m.Humeur));
        p = Jouer(c, p, ref t, "pc", 0);                               // nord : ruse +2, la clé
        e = Rejouer(c, p, t);
        Assert.Equal(Phase.Attente, e.Phase);
        Assert.Equal(2, e.Variables["ruse"]);
        Assert.Contains("cle", e.Objets);
        Assert.Equal("La route du nord", e.Lieu);
        Assert.Equal("d-un", e.Decor);                                 // le décor s'hérite
        Assert.Equal("marche", e.Tenue);
        Assert.Equal("Pilou marche vers le nord", e.Pendant);
        Assert.InRange((e.Fin - e.T) / 60_000, 10, 30);                // duree_min à duree_max, tirage reproductible
        Assert.Equal(e.Fin, Rejouer(c, p, t + 5).Fin);
        Assert.Equal("joueur", e.Messages[3].Qui);
        Assert.Equal("Le nord", e.Messages[3].Texte);
    }

    [Fact]
    public void Attente_puis_depart_confirme_puis_epreuve()
    {
        var c = Essai;
        long t = T0;
        var p = Jouer(c, Nouvelle(c, 1, t, "pc", "g", false), ref t, "pc", 0);
        var e = Rejouer(c, p, t);
        long fin = e.Fin;
        Assert.Null(Decider(c, p, fin - 1000, "pc", Suite));           // rien à décider pendant l'attente
        Assert.Equal(Phase.Attente, Rejouer(c, p, fin - 1).Phase);
        // Au retour, la nouvelle attente ne part pas toute seule : Pilou dit ce qu'il va faire, le joueur dit « vas-y ».
        e = Rejouer(c, p, fin);
        Assert.Equal(Phase.Depart, e.Phase);
        Assert.Equal("a-double", e.Noeud);
        Assert.Equal(0, e.Fin);
        Assert.Equal(Phase.Depart, Rejouer(c, p, fin + 86_400_000).Phase);
        Assert.Null(Decider(c, p, fin + 10_000, "pc", 0));
        p = Decider(c, p, fin + 10_500, "tel", Suite)!;
        e = Rejouer(c, p, fin + 11_000);
        Assert.Equal(Phase.Attente, e.Phase);
        Assert.Equal(fin + 10_000 + 5 * 60_000, e.Fin);                // l'heure de la décision, à la seconde
        Assert.Equal("nuit", e.Tenue);
        e = Rejouer(c, p, e.Fin);
        Assert.Equal(Phase.Epreuve, e.Phase);
        Assert.Equal("memoire", e.Jeu);
        Assert.Equal(2, e.Difficulte);
        Assert.Equal(2, e.Aide);                                       // la variable « ruse » aide
        Assert.Equal(65, e.Chance);
        Assert.Equal(DeDe(c, p, e), DeDe(c, p, Rejouer(c, p, e.T + 999_000)));
        var gagne = Decider(c, p, e.T, "pc", Reussite)!;
        Assert.Equal("b-entree", Rejouer(c, gagne, e.T).Noeud);
        Assert.Equal(new[] { "a-prime" }, Rejouer(c, gagne, e.T).Credits);
        var perd = Decider(c, p, e.T, "pc", Rate)!;
        Assert.Equal(Phase.Repos, Rejouer(c, perd, e.T).Phase);
    }

    [Fact]
    public void Echec_repos_puis_reprise_au_dernier_checkpoint()
    {
        var c = Essai;
        long t = T0;
        // nord, vas-y, épreuve réussie → chapitre b (check-point), la récompense de a-prime est acquise.
        var p = Jouer(c, Nouvelle(c, 1, t, "pc", "g", false), ref t, "pc", 0, Suite, Reussite);
        var e = Rejouer(c, p, t);
        Assert.Equal("b-entree", e.Noeud);
        Assert.Contains("pain", e.Objets);
        Assert.DoesNotContain("parti", e.Drapeaux);                    // drapeau ôté
        Assert.Equal(new[] { "porte", "fenetre", "trou" }, e.Options.Select(o => o.Id));
        p = Jouer(c, p, ref t, "pc", 3);                               // le trou : un piège
        e = Rejouer(c, p, t);
        Assert.Equal(Phase.Repos, e.Phase);
        Assert.Equal("b-piege", e.Noeud);
        Assert.Equal(10 * 60_000, e.Fin - e.T);
        Assert.Equal("Pilou se repose", e.Pendant);
        var retour = Rejouer(c, p, e.Fin);
        Assert.Equal(Phase.Choix, retour.Phase);
        Assert.Equal("b-entree", retour.Noeud);
        Assert.Equal(e.Fin, retour.T);
        Assert.Contains("cle", retour.Objets);                         // ce qui était acquis avant le check-point reste
        Assert.Contains("pain", retour.Objets);
        Assert.Equal(2, retour.Variables["ruse"]);
        Assert.Equal(new[] { "a-prime" }, retour.Credits);
        // Un échec du chapitre a ramène au départ : les effets de l'entrée y sont rejoués une fois, pas deux.
        t = T0;
        p = Jouer(c, Nouvelle(c, 1, t, "pc", "g", false), ref t, "pc", 0, Suite, Rate);
        e = Rejouer(c, p, t);
        Assert.Equal("a-chute", e.Noeud);
        retour = Rejouer(c, p, e.Fin);
        Assert.Equal("a-carrefour", retour.Noeud);
        Assert.Equal(2, retour.Variables["courage"]);
        Assert.Equal(0, retour.Variables["ruse"]);
        Assert.Empty(retour.Objets);
        Assert.Empty(retour.Credits);
    }

    [Fact]
    public void Fins_recompenses_et_progression()
    {
        var c = Essai;
        long t = T0;
        var p = Jouer(c, Nouvelle(c, 1, t, "pc", "g", false), ref t, "pc", 0, Suite, Reussite, 0);
        var e = Rejouer(c, p, t);
        Assert.Equal(Phase.Fin, e.Phase);
        Assert.Equal("bonne", e.Issue);
        Assert.Equal("Par la grande porte", e.TitreFin);
        Assert.Equal(new Prime(50, 20, "s-bon", "Testeur de portes", "cape"), e.Recompenses);
        Assert.Equal(new[] { "a-prime", "b-fin-bonne" }, e.Credits);
        Assert.Equal(1, e.Progression);
        Assert.Equal(2, e.ChapitreNumero);
        Assert.Null(Decider(c, p, t, "pc", Abandon));                  // plus rien à décider
        Assert.False(e.EnCours);
    }

    [Fact]
    public void Epreuve_au_de_et_jeu_inconnu()
    {
        var c = Essai;
        // « sud » : épreuve « des », résolue sans geste. Même graine → même issue ; la variable bonus pèse.
        int reussies = 0;
        for (int g = 0; g < 200; g++)
        {
            var p = Decider(c, Nouvelle(c, 1, T0, "pc", "graine" + g, false), T0, "pc", 1)!;
            var e = Rejouer(c, p, T0);
            Assert.Contains(e.Noeud, new[] { "b-entree", "a-chute" });
            Assert.Equal(e.Texte(), Rejouer(c, p, T0).Texte());
            bool attendu = Tirage("graine" + g, 0).Suivant(100) < ChanceDe(3, 2);
            Assert.Equal(attendu, e.Noeud == "b-entree");
            if (attendu) reussies++;
        }
        Assert.InRange(reussies, 70, 130);                             // 50 % (40 + 2 × 5)
        // « secret » : un jeu que nul ne connaît se joue aux dés, sans s'arrêter.
        var q = Decider(c, Nouvelle(c, 1, T0, "pc", "g", false), T0, "pc", 2)!;
        Assert.NotEqual(Phase.Epreuve, Rejouer(c, q, T0).Phase);
        Assert.True(JeuAuto("des") && JeuAuto("marelle") && !JeuAuto("rythme"));
        Assert.Equal(new[] { 70, 55, 40, 10, 95 }, new[] { ChanceDe(1, 0), ChanceDe(2, 0), ChanceDe(3, 0), ChanceDe(3, -9), ChanceDe(1, 9) });
    }

    [Fact]
    public void Deux_appareils_pour_la_meme_etape_la_plus_ancienne_gagne()
    {
        var c = Essai;
        var p = Nouvelle(c, 1, T0, "pc-a", "g", false);
        var nord = new Entree(0, T0 + 40_000, "pc-a", Campagnes.Code("a-carrefour"), 0);
        var boucle = new Entree(0, T0 + 50_000, "tel-b", Campagnes.Code("a-carrefour"), 3);
        Partie Avec(params Entree[] j)
        {
            var q = p.Copie();
            q.Journal = j.ToList();
            return q;
        }
        Assert.Equal("a-marche", Rejouer(c, Avec(nord, boucle), T0 + 60_000).Noeud);
        Assert.Equal("a-marche", Rejouer(c, Avec(boucle, nord, boucle, nord), T0 + 60_000).Noeud);   // désordre, doublons
        Assert.Equal(Rejouer(c, Avec(nord, boucle), T0 + 60_000).Texte(), Rejouer(c, Avec(boucle, nord, nord), T0 + 60_000).Texte());
        // Égalité d'heure : le plus petit identifiant d'appareil.
        var b2 = boucle with { T = nord.T };
        Assert.Equal("a-marche", Rejouer(c, Avec(b2, nord), T0 + 60_000).Noeud);
        var n2 = nord with { A = "tel-z" };
        Assert.Equal("a-boucle", Rejouer(c, Avec(n2, b2), T0 + 60_000).Noeud);
        // Une décision plus ancienne mais sans objet (autre nœud, option absente) ne gagne pas.
        var fausse = new Entree(0, T0 + 1000, "aaa", Campagnes.Code("a-prime"), 0);
        var absente = new Entree(0, T0 + 2000, "aaa", Campagnes.Code("a-carrefour"), 7);
        Assert.Equal("a-boucle", Rejouer(c, Avec(fausse, absente, boucle), T0 + 60_000).Noeud);
    }

    [Fact]
    public void Compacter_avance_la_base_sans_changer_l_etat()
    {
        var c = Essai;
        long t = T0;
        var p = Jouer(c, Nouvelle(c, 1, t, "pc", "g", false), ref t, "pc", 0, Suite, Reussite);
        var avant = Rejouer(c, p, t);
        Assert.Equal(3, p.Journal.Count);
        // Dans le délai de grâce : la base ne bouge pas (un autre appareil peut encore avoir décidé plus tôt).
        Assert.Equal(JsonPartie(p), JsonPartie(Compacter(c, p, t + Grace - 5000)));
        var q = Compacter(c, p, t + Grace + 1000);
        Assert.Empty(q.Journal);
        Assert.Equal(3, q.E);
        Assert.Equal(Campagnes.Code("b-entree"), q.Ici.N);
        Assert.Null(q.Cp);
        var apres = Rejouer(c, q, t + Grace + 1000);
        Assert.Equal(avant.Noeud, apres.Noeud);
        Assert.Equal(avant.Objets, apres.Objets);
        Assert.Equal(avant.Variables, apres.Variables);
        Assert.Equal(avant.Tirages, apres.Tirages);
        Assert.Equal(avant.Lieu, apres.Lieu);
        Assert.Equal(avant.Decor, apres.Decor);
        // Les messages gardent leur clé d'un côté à l'autre de la compaction.
        Assert.Equal(avant.Messages.Where(m => m.Noeud == "b-entree").Select(m => (m.E, m.I, m.Texte)), apres.Messages.Select(m => (m.E, m.I, m.Texte)));
        Assert.Equal(JsonPartie(q), JsonPartie(Compacter(c, q, t + 10 * Grace)));
        // Aller-retour par le JSON : rien ne se perd.
        Assert.Equal(JsonPartie(q), JsonPartie(LirePartie(JsonPartie(q))!));
        Assert.Equal(JsonPartie(p), JsonPartie(LirePartie(JsonPartie(p))!));
    }

    [Fact]
    public void Journal_trop_long_la_base_avance_au_milieu_du_chapitre()
    {
        var c = Essai;
        long t = T0;
        var p = Nouvelle(c, 1, t, "pc", "g", false);
        for (int i = 0; i < 40; i++)
        {
            p = Jouer(c, p, ref t, "pc", 3);                           // tourner en rond : choix, attente, choix…
            p = Compacter(c, p, t);
            Assert.True(p.Journal.Count <= MaxEntrees + 1, $"{p.Journal.Count} décisions gardées");
        }
        Assert.True(p.Entre);
        Assert.NotNull(p.Cp);
        Assert.Equal(Campagnes.Code("a-debut"), p.Cp!.N);
        var e = Rejouer(c, p, t);
        Assert.Equal(40, e.E);
        Assert.Equal(Phase.Attente, e.Phase);
        // Le dernier check-point est gardé : un échec y ramène toujours.
        e = Rejouer(c, p, e.Fin);
        p = Jouer(c, p, ref t, "pc", 1);                               // sud : les dés
        e = Rejouer(c, p, t);
        if (e.Phase == Phase.Repos) Assert.Equal("a-carrefour", Rejouer(c, p, e.Fin).Noeud);
        Assert.True(Octets(JsonPartie(p)) < 1200, $"{Octets(JsonPartie(p))} octets");
    }

    // ---- Carnets, fusion, synchronisation

    private static void Echanger(long t, params (string Nom, Carnet K)[] appareils)
    {
        var envois = appareils.Select(a => Messages(a.K, a.Nom, a.Nom.StartsWith("tel") ? "tel" : "pc")).ToList();
        for (int i = 0; i < appareils.Length; i++)
        {
            for (int j = 0; j < appareils.Length; j++)
                if (i != j)
                    foreach (var m in envois[j]) Recevoir(appareils[i].K, m, appareils[i].Nom, Biblio, t);
            Actualiser(appareils[i].K, Biblio, t);
        }
    }

    [Fact]
    public void Demarrer_niveau_requis_et_une_seule_campagne()
    {
        var k = new Carnet();
        Assert.Equal("niveau 3 requis", Demarrer(k, Essai, 2, T0, "pc", Biblio, "g"));
        Assert.Null(k.Courante);
        Assert.Null(Demarrer(k, Essai, 3, T0, "pc", Biblio, "g"));
        Assert.Equal("une campagne est déjà en cours", Demarrer(k, Prologue, 3, T0 + 1000, "pc", Biblio, "g"));
        Assert.True(EnCours(k, Biblio, T0 + 1000));
        Assert.Equal(1, k.Courante!.P);
        Assert.Equal(3, k.Fil.Count);
        Assert.Equal(3, k.NonLus);
        MarquerLu(k);
        Assert.Equal(0, k.NonLus);
        Assert.Null(Choisir(k, Essai, T0 + 5000, "pc", "boucle"));
        Assert.Equal(5, k.Fil.Count);                                  // le choix du joueur, puis Pilou
        Assert.Equal(1, k.NonLus);
        Assert.Equal("ce n'est pas possible maintenant", Choisir(k, Essai, T0 + 6000, "pc", "nord"));
        Assert.Equal("aucune partie en cours", Choisir(k, Prologue, T0 + 6000, "pc", "lampe"));
        Assert.Null(Abandonner(k, Essai, T0 + 7000, "pc"));
        Assert.False(EnCours(k, Biblio, T0 + 8000));
        Assert.True(Reprenable(k, Essai, T0 + 8000));
        Assert.False(Reprenable(k, Prologue, T0 + 8000));
        Assert.Null(Demarrer(k, Prologue, 3, T0 + 9000, "pc", Biblio, "g2"));
        Assert.Equal(2, k.Courante!.P);
        Assert.True(k.Suspendues.ContainsKey("essai"));
    }

    [Fact]
    public void Fusion_idempotente_insensible_a_l_ordre_et_aux_doublons()
    {
        // Trois appareils jouent chacun de leur côté la même partie reçue ; leurs messages arrivent n'importe comment.
        var a = new Carnet();
        Assert.Null(Demarrer(a, Essai, 5, T0, "pc-a", Biblio, "g"));
        var depart = Messages(a, "pc-a", "pc");
        var b = new Carnet();
        var tel = new Carnet();
        foreach (var m in depart)
        {
            Assert.True(Recevoir(b, m, "pc-b", Biblio, T0 + 1000));
            Assert.False(Recevoir(b, m, "pc-b", Biblio, T0 + 1000));   // doublon : rien ne change
            Recevoir(tel, m, "tel-c", Biblio, T0 + 1000);
            Assert.False(Recevoir(a, m, "pc-a", Biblio, T0 + 1000));   // le sien : ignoré
        }
        Assert.Null(Choisir(a, Essai, T0 + 40_000, "pc-a", "nord"));
        Assert.Null(Choisir(b, Essai, T0 + 50_000, "pc-b", "boucle"));
        Assert.Null(Choisir(tel, Essai, T0 + 45_000, "tel-c", "sud"));
        var lots = new[] { Messages(a, "pc-a", "pc"), Messages(b, "pc-b", "pc"), Messages(tel, "tel-c", "tel"), depart };
        var signatures = new HashSet<string>();
        int[][] ordres = { new[] { 0, 1, 2, 3 }, new[] { 3, 2, 1, 0 }, new[] { 2, 0, 3, 1, 0, 2 }, new[] { 1, 1, 3, 0, 2 }, new[] { 2, 3, 1, 0 }, new[] { 0, 2, 1 } };
        foreach (var ordre in ordres)
        {
            var k = new Carnet();
            foreach (var i in ordre)
                foreach (var m in lots[i]) Recevoir(k, m, "pc-z", Biblio, T0 + 60_000);
            var e = Actualiser(k, Biblio, T0 + 60_000)!;
            Assert.Equal("a-marche", e.Noeud);                         // « nord », la plus ancienne des trois décisions
            signatures.Add(Signature(k));
        }
        Assert.Single(signatures);
        // Chacun des trois, après échange, arrive au même carnet.
        Echanger(T0 + 61_000, ("pc-a", a), ("pc-b", b), ("tel-c", tel));
        Assert.Equal(Signature(a), Signature(b));
        Assert.Equal(Signature(a), Signature(tel));
        Assert.Equal(signatures.Single(), Signature(a));
    }

    [Fact]
    public void Le_telephone_avance_PC_eteint_et_les_recompenses_attendent_le_PC()
    {
        var tel = new Carnet();
        long t = T0;
        Assert.Null(Demarrer(tel, Essai, 5, t, "tel", Biblio, "g"));
        Assert.Null(Choisir(tel, Essai, t += 5000, "tel", "nord"));
        t = Actualiser(tel, Biblio, t)!.Fin;
        Assert.Null(Continuer(tel, Essai, t, "tel"));
        t = Actualiser(tel, Biblio, t)!.Fin;
        Assert.Equal(Phase.Epreuve, Actualiser(tel, Biblio, t)!.Phase);
        Assert.Null(Epreuve(tel, Essai, t, "tel", true));
        Assert.Null(Choisir(tel, Essai, t += 5000, "tel", "porte"));
        var e = Actualiser(tel, Biblio, t)!;
        Assert.Equal(Phase.Fin, e.Phase);
        Assert.Equal((60, 25), Acquis(tel, Essai));
        Assert.Equal((60, 25), EnAttente(tel, Biblio));                // rien n'est versé tant qu'aucun PC ne l'a vu
        Assert.Equal(new[] { "b-fin-bonne" }, Fins(tel, Essai).Select(f => f.Noeud));
        Assert.Equal(new[] { "s-bon" }, Souvenirs(tel, Essai).Select(s => s.Id));
        Assert.Equal(new[] { "Testeur de portes" }, Titres(tel, Essai));
        Assert.Equal(new[] { "cape" }, ObjetsGagnes(tel, Essai));

        // Le PC s'allume : il reçoit, verse une fois, l'annonce ; le téléphone n'attend plus.
        var pc = new Profil { Machine = "PC" };
        foreach (var m in Messages(tel, "tel", "tel")) Assert.True(Recevoir(pc.CarnetCampagnes, m, "pc", Biblio, t));
        Actualiser(pc.CarnetCampagnes, Biblio, t);
        var v = Crediter(pc, Biblio);
        Assert.Equal((60, 25), (v.Po, v.Xp));
        Assert.Equal(new[] { "cape" }, v.Objets);
        Assert.Equal(60, pc.Bourse.PoCampagnes);
        Assert.Equal(25, pc.XpTelephone);
        Assert.Contains("cape", pc.Bourse.Inventaire);
        v = Crediter(pc, Biblio);                                      // une seule fois
        Assert.Equal((0, 0), (v.Po, v.Xp));
        Assert.Empty(v.Objets);
        foreach (var m in Messages(pc.CarnetCampagnes, "pc", "pc")) Recevoir(tel, m, "tel", Biblio, t);
        Assert.Equal((0, 0), EnAttente(tel, Biblio));
        // Un message du téléphone relu, ou rejoué par un autre PC : toujours rien de plus.
        foreach (var m in Messages(tel, "tel", "tel")) Recevoir(pc.CarnetCampagnes, m, "pc", Biblio, t + 1000);
        Actualiser(pc.CarnetCampagnes, Biblio, t + 1000);
        Assert.Equal((0, 0), (Crediter(pc, Biblio).Po, Crediter(pc, Biblio).Xp));
        Assert.Equal(60, pc.Bourse.PoCampagnes);
    }

    [Fact]
    public void Credit_unique_dans_tout_le_groupe()
    {
        // Deux PC et un téléphone voient la même fin. Chaque PC verse dans ses compteurs « à part » ; le groupe les
        // compte au maximum, jamais en somme : 60 po et 25 xp, pas 120 et 50.
        var a = new Profil { Machine = "A" };
        var b = new Profil { Machine = "B" };
        var tel = new Carnet();
        long t = T0;
        Assert.Null(Demarrer(a.CarnetCampagnes, Essai, 5, t, "pc-a", Biblio, "g"));
        Echanger(t + 1000, ("pc-a", a.CarnetCampagnes), ("pc-b", b.CarnetCampagnes), ("tel", tel));
        Assert.Null(Choisir(b.CarnetCampagnes, Essai, t += 5000, "pc-b", "nord"));
        t = Actualiser(b.CarnetCampagnes, Biblio, t)!.Fin;
        Echanger(t, ("pc-a", a.CarnetCampagnes), ("pc-b", b.CarnetCampagnes), ("tel", tel));
        Assert.Null(Continuer(tel, Essai, t, "tel"));
        t = Actualiser(tel, Biblio, t)!.Fin;
        Assert.Null(EpreuveAuDe(tel, Essai, t, "tel"));
        Echanger(t, ("pc-a", a.CarnetCampagnes), ("pc-b", b.CarnetCampagnes), ("tel", tel));
        var e = Actualiser(a.CarnetCampagnes, Biblio, t)!;
        if (e.Phase == Phase.Repos)
        {
            // Les dés ont dit non : repos, retour au départ, et cette fois par le sud jusqu'à ce que ça passe.
            for (int i = 0; i < 40 && e.Noeud != "b-entree"; i++)
            {
                t = Math.Max(t, e.Fin) + 1000;
                e = Actualiser(a.CarnetCampagnes, Biblio, t)!;
                if (e.Phase == Phase.Choix && e.Noeud == "a-carrefour") Assert.Null(Choisir(a.CarnetCampagnes, Essai, t, "pc-a", "sud"));
                e = Actualiser(a.CarnetCampagnes, Biblio, t)!;
            }
        }
        Assert.Equal("b-entree", e.Noeud);
        Assert.Null(Choisir(a.CarnetCampagnes, Essai, t += 5000, "pc-a", e.Options[0].Id == "porte" ? "porte" : "fenetre"));
        e = Actualiser(a.CarnetCampagnes, Biblio, t)!;
        for (int i = 0; i < 40 && e.Phase != Phase.Fin; i++)
        {
            t = Math.Max(t, e.Fin) + 1000;
            e = Actualiser(a.CarnetCampagnes, Biblio, t)!;
            if (e.Phase == Phase.Choix) Assert.Null(Choisir(a.CarnetCampagnes, Essai, t, "pc-a", "fenetre"));
            e = Actualiser(a.CarnetCampagnes, Biblio, t)!;
        }
        Assert.Equal(Phase.Fin, e.Phase);
        for (int tour = 0; tour < 3; tour++)
        {
            Echanger(t + tour, ("pc-a", a.CarnetCampagnes), ("pc-b", b.CarnetCampagnes), ("tel", tel));
            Crediter(a, Biblio);
            Crediter(b, Biblio);
        }
        var (po, xp) = Acquis(a.CarnetCampagnes, Essai);
        Assert.True(po >= 10 && xp >= 6, $"{po} po, {xp} xp");
        Assert.Equal((po, xp), (a.Bourse.PoCampagnes, a.XpTelephone));
        Assert.Equal((po, xp), (b.Bourse.PoCampagnes, b.XpTelephone));
        Assert.Equal((0, 0), EnAttente(tel, Biblio));
        // Le groupe : le PC a, le PC b vu dans le dossier partagé, et b vu par le relais.
        var compteurB = Groupe.Moi(b, "pc-b", "B");
        Assert.Equal(xp, Groupe.Total(a, new[] { b }, Array.Empty<Groupe.Compteur>()));
        Assert.Equal(xp, Groupe.Total(a, Array.Empty<Profil>(), new[] { compteurB }));
        Assert.Equal(po, Groupe.SoldePo(a, new[] { b }, Array.Empty<Groupe.Compteur>()));
        Assert.Equal(po, Groupe.SoldePo(a, Array.Empty<Profil>(), new[] { compteurB }));
        Assert.Equal(po, Groupe.SoldePo(b, new[] { a }, Array.Empty<Groupe.Compteur>()));
        // Le message de groupe n'a pas grossi : les campagnes ont leur message à elles.
        Assert.DoesNotContain("camp", Groupe.Json(compteurB), StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public void Rejouer_une_campagne_finie_ne_redonne_ni_po_ni_xp()
    {
        var k = new Carnet();
        long t = T0;
        (string Noeud, int Po, int Xp) Partie(string graine, string fin)
        {
            Assert.Null(Demarrer(k, Prologue, 1, t, "pc", Biblio, graine));
            var e = Actualiser(k, Biblio, t)!;
            for (int i = 0; i < 60 && e.Phase != Phase.Fin; i++)
            {
                if (e.EnAttente) t = e.Fin;
                t += 1000;
                e = Actualiser(k, Biblio, t)!;
                string? r = e.Phase switch
                {
                    Phase.Choix => Choisir(k, Prologue, t, "pc", e.Options.Any(o => o.Id == fin) ? fin
                        : e.Options.Any(o => o.Id == "sentier") ? "sentier" : e.Options.Any(o => o.Id == "tour") ? "tour" : e.Options[0].Id),
                    Phase.Epreuve => Epreuve(k, Prologue, t, "pc", true),
                    Phase.Depart => Continuer(k, Prologue, t, "pc"),
                    _ => null,
                };
                Assert.Null(r);
                e = Actualiser(k, Biblio, t)!;
            }
            Assert.Equal(Phase.Fin, e.Phase);
            var (po, xp) = Acquis(k, Prologue);
            return (e.Noeud, po, xp);
        }
        Assert.Equal(("p2-fin-prudent", 15, 8), Partie("g1", "rentre"));
        Assert.False(k.Courante!.Rejeu);
        Assert.True(Finie(k, "prologue"));
        // Deuxième partie, l'autre fin : le souvenir manquant, mais ni po ni xp de plus.
        Assert.Equal(("p2-fin-coucher", 15, 8), Partie("g2", "reste"));
        Assert.True(k.Courante!.Rejeu);
        Assert.Equal(new[] { "question-gardee", "coucher-de-soleil" }, Souvenirs(k, Prologue).Select(s => s.Id));
        Assert.Equal(2, Fins(k, Prologue).Count);
        var p = new Profil { CarnetCampagnes = k };
        Assert.Equal((15, 8), (Crediter(p, Biblio).Po, p.XpTelephone));
    }

    [Fact]
    public void Abandon_puis_reprise_au_dernier_checkpoint_sur_un_autre_appareil()
    {
        var a = new Carnet();
        var b = new Carnet();
        long t = T0;
        Assert.Null(Demarrer(a, Essai, 5, t, "pc-a", Biblio, "g"));
        Assert.Null(Choisir(a, Essai, t += 5000, "pc-a", "nord"));
        t = Actualiser(a, Biblio, t)!.Fin;
        Assert.Null(Continuer(a, Essai, t, "pc-a"));
        t = Actualiser(a, Biblio, t)!.Fin;
        Assert.Null(Epreuve(a, Essai, t, "pc-a", true));
        Assert.Null(Choisir(a, Essai, t += 5000, "pc-a", "fenetre"));  // dans le chapitre b, après le check-point
        Assert.Equal(Phase.Attente, Actualiser(a, Biblio, t)!.Phase);
        Assert.Null(Abandonner(a, Essai, t += 5000, "pc-a"));          // on peut abandonner pendant une attente
        Assert.Equal(Phase.Abandon, Actualiser(a, Biblio, t)!.Phase);
        Assert.Null(Demarrer(a, Prologue, 5, t += 5000, "pc-a", Biblio, "g2"));
        Echanger(t, ("pc-a", a), ("pc-b", b));
        Assert.Equal("prologue", b.Courante!.Campagne);
        Assert.True(Reprenable(b, Essai, t));
        Assert.Equal((10, 5), Acquis(b, Essai));                       // ce qui était acquis reste acquis
        Assert.Equal("une campagne est déjà en cours", Demarrer(b, Essai, 5, t, "pc-b", Biblio, "g3"));
        Assert.Null(Abandonner(b, Prologue, t += 5000, "pc-b"));
        Assert.Null(Demarrer(b, Essai, 5, t += 5000, "pc-b", Biblio, "g3"));
        var e = Actualiser(b, Biblio, t)!;
        Assert.Equal("b-entree", e.Noeud);                             // le dernier check-point, pas le début
        Assert.Equal(Phase.Choix, e.Phase);
        Assert.Contains("cle", e.Objets);
        Assert.Equal(3, b.Courante!.P);
        Assert.Equal("g", b.Courante.Graine);
        Echanger(t, ("pc-a", a), ("pc-b", b));
        Assert.Equal(Signature(a), Signature(b));
        Assert.Equal("essai", a.Courante!.Campagne);
        Assert.False(a.Suspendues.ContainsKey("essai"));
        Assert.True(a.Suspendues.ContainsKey("prologue"));
        // Un vieux message (l'essai encore en cours, partie n° 1) ne fait pas revenir en arrière.
        var vieux = new Carnet();
        Demarrer(vieux, Essai, 5, T0, "pc-a", Biblio, "g");
        foreach (var m in Messages(vieux, "pc-vieux", "pc")) Recevoir(a, m, "pc-a", Biblio, t);
        Actualiser(a, Biblio, t);
        Assert.Equal(Signature(a), Signature(b));
    }

    // ---- Tailles

    // Une longue campagne fabriquée : chapitres × nœuds, des variables, des objets, des drapeaux, des fins.
    private static Campagne Longue(string id, int chapitres, int parChapitre)
    {
        var fiche = new StringBuilder();
        fiche.Append("{\"v\":1,\"id\":\"" + id + "\",\"titre\":\"Longue\",\"depart\":\"ch01-entree-du-chapitre\",\"niveau\":1,\"chapitres\":[");
        var fichiers = new Dictionary<string, string>();
        for (int ch = 1; ch <= chapitres; ch++)
        {
            fiche.Append($"{(ch > 1 ? "," : "")}{{\"id\":\"ch{ch:00}\",\"titre\":\"Chapitre {ch}\",\"fichier\":\"chapitre-{ch:00}.json\"}}");
            var b = new StringBuilder("{\"chapitre\":\"ch" + ch.ToString("00") + "\",\"noeuds\":{");
            string N(int i) => i == 0 ? $"ch{ch:00}-entree-du-chapitre" : $"ch{ch:00}-carrefour-numero-{i:00}";
            string suivant = ch < chapitres ? $"ch{ch + 1:00}-entree-du-chapitre" : "fin-de-la-longue-campagne-1";
            for (int i = 0; i < parChapitre; i++)
            {
                string vers = i + 1 < parChapitre ? N(i + 1) : suivant;
                if (i > 0) b.Append(',');
                b.Append($"\"{N(i)}\":");
                if (i == 0)
                    b.Append($"{{\"type\":\"recit\",\"checkpoint\":true,\"lieu\":\"Lieu {ch}\",\"decor\":\"decor-numero-{ch % 14:00}\",\"texte\":[\"Chapitre {ch}.\"],"
                             + $"\"effets\":[{{\"var\":\"variable-numero-{ch % 12:00}\",\"plus\":{ch}}},{{\"drapeau\":\"drapeau-du-chapitre-{ch:00}\"}},"
                             + $"{{\"objet\":\"objet-numero-{ch % 10:00}\",\"donne\":true}}],\"suite\":\"{vers}\"}}");
                else if (i == parChapitre - 1)
                    b.Append($"{{\"type\":\"recit\",\"recompense\":{{\"po\":40,\"xp\":20}},\"texte\":[\"Fin du chapitre {ch}.\"],\"suite\":\"{vers}\"}}");
                else if (i % 4 == 1)
                    b.Append($"{{\"type\":\"attente\",\"texte\":[\"J'y vais.\"],\"duree_min\":30,\"duree_max\":180,\"pendant\":\"Pilou marche\",\"tenue\":\"marche\",\"suite\":\"{vers}\"}}");
                else if (i % 4 == 3)
                    b.Append($"{{\"type\":\"epreuve\",\"jeu\":\"rythme\",\"difficulte\":2,\"reussite\":\"{vers}\",\"echec\":\"{N(i)}-rate\"}},"
                             + $"\"{N(i)}-rate\":{{\"type\":\"echec\",\"texte\":[\"Aïe.\"],\"repos_min\":30}}");
                else
                    b.Append($"{{\"type\":\"choix\",\"texte\":[\"Par où ?\"],\"options\":[{{\"id\":\"a\",\"libelle\":\"A\",\"vers\":\"{vers}\","
                             + $"\"effets\":[{{\"drapeau\":\"drapeau-{ch:00}-{i:00}\"}},{{\"var\":\"variable-numero-{i % 12:00}\",\"plus\":1}}]}},"
                             + $"{{\"id\":\"b\",\"libelle\":\"B\",\"vers\":\"{vers}\"}},{{\"id\":\"c\",\"libelle\":\"Retour\",\"vers\":\"{N(i - 1)}\"}}]}}");
            }
            if (ch == chapitres)
                for (int f = 1; f <= 6; f++)
                    b.Append($",\"fin-de-la-longue-campagne-{f}\":{{\"type\":\"fin\",\"issue\":\"bonne\",\"titre\":\"Fin {f}\",\"texte\":[\"Fin.\"],"
                             + $"\"recompenses\":{{\"po\":120,\"xp\":60,\"souvenir\":\"souvenir-{f}\"}}}}");
            b.Append("}}");
            fichiers[$"chapitre-{ch:00}.json"] = b.ToString();
        }
        fiche.Append("],\"variables\":{");
        fiche.Append(string.Join(",", Enumerable.Range(0, 12).Select(i => $"\"variable-numero-{i:00}\":0")));
        fiche.Append("},\"objets\":[");
        fiche.Append(string.Join(",", Enumerable.Range(0, 10).Select(i => $"{{\"id\":\"objet-numero-{i:00}\",\"nom\":\"Objet {i}\"}}")));
        fiche.Append("],\"decors\":[");
        fiche.Append(string.Join(",", Enumerable.Range(0, 14).Select(i => $"{{\"id\":\"decor-numero-{i:00}\",\"nom\":\"Décor {i}\"}}")));
        fiche.Append("]}");
        return Lire(fiche.ToString(), f => fichiers.GetValueOrDefault(f))!;
    }

    [Fact]
    public void Messages_sous_la_limite_pour_une_campagne_de_200_noeuds()
    {
        // Trois longues campagnes (12 chapitres, ≥ 200 nœuds chacune). Deux sont déjà finies (six fins chacune) ; la
        // troisième est abandonnée en route, puis reprise et jouée jusqu'au bout en mesurant chaque message.
        var longues = new[] { "alpha", "beta", "gamma" }.ToDictionary(id => id, id => Longue("la-longue-campagne-" + id, 12, 17));
        Campagne? B(string id) => longues.Values.FirstOrDefault(c => c.Id == id) ?? Biblio(id);
        Assert.All(longues.Values, c => Assert.True(c.Noeuds.Count >= 200, $"{c.Noeuds.Count} nœuds"));
        // Aucun code court en double sur 200 nœuds (le validateur le garantit pour les vraies campagnes).
        Assert.All(longues.Values, c => Assert.Equal(c.Noeuds.Count, c.Noeuds.Keys.Select(Campagnes.Code).Distinct().Count()));

        var k = new Carnet();
        string[] appareils = { "PC-BUREAU-1a2b", "tel-0123456789ab", "PORTABLE-TRAVAIL-9f9f" };
        long t = T0;
        int max = 0, maxJson = 0, maxPartie = 0, messages = 0, decisions = 0;
        var h = new Hasard(42);
        void Mesurer()
        {
            var l = Messages(k, appareils[0], "pc");
            messages += l.Count;
            foreach (var m in l)
            {
                Assert.True(Octets(m) <= TailleJson, $"{Octets(m)} octets de JSON");
                if (Octets(m) <= maxJson) continue;                    // on ne chiffre que le plus gros vu jusqu'ici
                maxJson = Octets(m);
                int chiffre = Telephone.Chiffrer(Code, m).Length;
                max = Math.Max(max, chiffre);
                Assert.True(chiffre <= Telephone.TailleMax, $"{chiffre} octets chiffrés");
            }
            if (k.Courante is not null) maxPartie = Math.Max(maxPartie, Octets(JsonPartie(k.Courante)));
        }
        void Jouer(Campagne c, int fin, int jusqua, bool mesurer)
        {
            Assert.Null(Demarrer(k, c, 1, t, appareils[0], B, "graine" + fin));
            var e = Actualiser(k, B, t)!;
            for (int i = 0; i < 4000 && e.EnCours && decisions < jusqua; i++)
            {
                if (e.EnAttente) t = e.Fin;
                t += 20_000;                                           // quelques choix à la suite : la base n'a pas le temps d'avancer
                e = Actualiser(k, B, t)!;
                string a = appareils[h.Suivant(appareils.Length)];
                string? r = e.Phase switch
                {
                    // De temps en temps un retour en arrière : le journal s'allonge sans passer de check-point.
                    Phase.Choix => Choisir(k, c, t, a, h.Suivant(5) == 0 ? "c" : h.Suivant(2) == 0 ? "a" : "b"),
                    Phase.Epreuve => Epreuve(k, c, t, a, h.Suivant(4) != 0),
                    Phase.Depart => Continuer(k, c, t, a),
                    _ => null,
                };
                Assert.Null(r);
                decisions++;
                e = Actualiser(k, B, t)!;
                if (mesurer) Mesurer();
            }
            if (e.Phase == Phase.Fin)
            {
                // Les cinq autres fins, comme si on les avait obtenues en rejouant (pire cas pour l'historique).
                var b = k.Historique[c.Id];
                for (int f = 2; f <= 6; f++) b.Fins[Campagnes.Code($"fin-de-la-longue-campagne-{f}")] = t / 1000 + f;
            }
        }
        // Deux campagnes déjà finies, six fins chacune, toutes leurs fins de chapitre touchées (pire cas pour l'historique).
        foreach (var (id, numero) in new[] { ("alpha", 1), ("beta", 2) })
        {
            var c = longues[id];
            var bilan = new Bilan { P = numero, Finie = numero };
            foreach (var n in c.Noeuds.Values.Where(n => !n.Recompense.Vide && n.Type != "fin")) bilan.Noeuds.Add(Campagnes.Code(n.Id));
            bilan.Noeuds.Add(Campagnes.Code("fin-de-la-longue-campagne-1"));
            bilan.Noeuds.Sort(StringComparer.Ordinal);
            for (int f = 1; f <= 6; f++) bilan.Fins[Campagnes.Code($"fin-de-la-longue-campagne-{f}")] = T0 / 1000 + f;
            k.Historique[c.Id] = bilan;
            Assert.Equal(13, bilan.Noeuds.Count);                      // 12 fins de chapitre et la fin
        }
        decisions = 0;
        Jouer(longues["gamma"], 3, 70, false);                         // abandonnée au milieu…
        Assert.Null(Abandonner(k, longues["gamma"], t += 1000, appareils[1]));
        Assert.Null(Demarrer(k, Essai, 5, t += 1000, appareils[0], B, "g"));
        Assert.Null(Abandonner(k, Essai, t += 1000, appareils[0]));    // … l'essai aussi…
        decisions = 0;
        Assert.Null(Demarrer(k, Prologue, 5, t += 1000, appareils[0], B, "g"));
        Assert.Null(Choisir(k, Prologue, t += 1000, appareils[0], "corde"));
        Assert.Null(Abandonner(k, Prologue, t += 1000, appareils[0]));
        decisions = 0;
        Jouer(longues["gamma"], 4, int.MaxValue, true);                // … puis reprise et jouée jusqu'au bout, en mesurant.
        Assert.Equal(Phase.Fin, Actualiser(k, B, t)!.Phase);
        Assert.Equal(2, k.Suspendues.Count);
        Assert.True(decisions > 150, $"{decisions} décisions");
        sortie.WriteLine($"campagne de {longues["gamma"].Noeuds.Count} nœuds, {decisions} décisions, {messages} messages : "
                         + $"au plus {maxJson} octets de JSON (limite {TailleJson}), {max} chiffrés (limite {Telephone.TailleMax}) ; partie seule : au plus {maxPartie} octets de JSON");
        var dernier = Messages(k, appareils[0], "pc");
        sortie.WriteLine($"dernier message ({Octets(dernier[0])} octets, 3 campagnes finies avec 6 fins, 2 suspendues) : {dernier[0]}");
        Assert.Single(dernier);
        Assert.True(max < Telephone.TailleMax);
        Assert.True(Telephone.Chiffrer(Code, dernier[0]).Length < Telephone.TailleMax);
        sortie.WriteLine($"dernier message chiffré : {Telephone.Chiffrer(Code, dernier[0]).Length} octets");
    }

    [Fact]
    public void Message_trop_gros_les_parties_suspendues_partent_a_part()
    {
        // Cas extrême (beaucoup de campagnes suspendues) : plusieurs messages, chacun sous la limite, et la fusion
        // de tous redonne le même carnet.
        var k = new Carnet();
        long t = T0;
        var toutes = Enumerable.Range(0, 14).Select(i => Longue($"campagne-suspendue-numero-{i:00}", 3, 9)).ToList();
        Campagne? B(string id) => toutes.FirstOrDefault(c => c.Id == id) ?? Biblio(id);
        foreach (var c in toutes)
        {
            Assert.Null(Demarrer(k, c, 1, t += 1000, "PC-BUREAU-1a2b", B, "g"));
            for (int i = 0; i < 9; i++)
            {
                var e = Actualiser(k, B, t)!;
                if (e.EnAttente) t = e.Fin + 1000;
                e = Actualiser(k, B, t)!;
                if (e.Phase == Phase.Choix) Choisir(k, c, t, "PC-BUREAU-1a2b", "a");
                else if (e.Phase == Phase.Epreuve) Epreuve(k, c, t, "PC-BUREAU-1a2b", true);
                else if (e.Phase == Phase.Depart) Continuer(k, c, t, "PC-BUREAU-1a2b");
            }
            Assert.Null(Abandonner(k, c, t += 1000, "PC-BUREAU-1a2b"));
        }
        Assert.Null(Demarrer(k, Prologue, 1, t += 1000, "PC-BUREAU-1a2b", B, "g"));
        var l = Messages(k, "PC-BUREAU-1a2b", "pc");
        Assert.True(l.Count > 1, "un seul message");
        Assert.All(l, m => Assert.True(Octets(m) <= TailleJson, $"{Octets(m)} octets"));
        sortie.WriteLine($"{k.Suspendues.Count} parties suspendues : {l.Count} messages de {string.Join(", ", l.Select(Octets))} octets");
        var autre = new Carnet();
        foreach (var m in l.AsEnumerable().Reverse()) Recevoir(autre, m, "tel", B, t);
        Actualiser(autre, B, t);
        Assert.Equal(Signature(k), Signature(autre));
    }

    // ---- Profil du PC

    [Fact]
    public void Le_carnet_se_garde_dans_le_profil()
    {
        var p = new Profil { Machine = "PC" };
        var k = p.CarnetCampagnes;
        Demarrer(k, Essai, 5, T0, "pc-a", Biblio, "g");
        Choisir(k, Essai, T0 + 5000, "pc-a", "boucle");
        Abandonner(k, Essai, T0 + 6000, "pc-a");
        Demarrer(k, Prologue, 5, T0 + 7000, "pc-a", Biblio, "g2");
        Choisir(k, Prologue, T0 + 8000, "tel-b", "lampe");
        k.Historique["essai"].Fins["Zz09"] = 12;
        k.Historique["essai"].Fins["aB-_"] = 15;
        MarquerLu(k);
        var json = JsonSerializer.Serialize(p);
        var q = JsonSerializer.Deserialize<Profil>(json)!;
        Assert.Equal(Signature(k), Signature(q.CarnetCampagnes));
        Assert.Equal(k.Fil, q.CarnetCampagnes.Fil);
        Assert.Equal(k.Lu, q.CarnetCampagnes.Lu);
        Assert.Equal(Actualiser(k, Biblio, T0 + 9000)!.Texte(), Actualiser(q.CarnetCampagnes, Biblio, T0 + 9000)!.Texte());
        // Un profil d'avant les campagnes se lit toujours (carnet vide), et un carnet vide ne publie rien.
        var ancien = JsonSerializer.Deserialize<Profil>("{\"Machine\":\"PC\",\"Xp\":12}")!;
        Assert.Null(ancien.CarnetCampagnes.Courante);
        Assert.Empty(Messages(ancien.CarnetCampagnes, "pc", "pc"));
        Assert.Null(Actualiser(ancien.CarnetCampagnes, Biblio, T0));
    }

    [Fact]
    public void Sujet_dedie_et_lecture_du_relais()
    {
        var sujet = Campagnes.Sujet(Code);
        sortie.WriteLine(sujet);
        Assert.Equal(sujet, Campagnes.Sujet("abcd efgh jkmn pqrs"));
        Assert.NotEqual(Telephone.Sujet(Code), sujet);
        Assert.NotEqual(Telephone.SujetRetour(Code), sujet);
        Assert.NotEqual(Groupe.Sujet(Code), sujet);
        var k = new Carnet();
        Demarrer(k, Prologue, 1, T0, "pc-a", Biblio, "g");
        var m = Messages(k, "pc-a", "pc").Single();
        sortie.WriteLine($"prologue au départ : {Octets(m)} octets de JSON, {Telephone.Chiffrer(Code, m).Length} chiffrés : {m}");
        var flux = "{\"id\":\"a1\",\"event\":\"open\"}\n"
                   + "{\"id\":\"a2\",\"event\":\"message\",\"message\":\"" + Telephone.Chiffrer(Code, m) + "\"}\n"
                   + "{\"id\":\"a3\",\"event\":\"message\",\"message\":\"" + Telephone.Chiffrer("ZZZZ-ZZZZ-ZZZZ-ZZZZ", m) + "\"}\n"
                   + "pas du json\n";
        var (messages, dernier) = LireRelais(Code, flux);
        Assert.Equal(new[] { m }, messages);
        Assert.Equal("a3", dernier);
        // Un ancien appareil qui lirait ce message comme un compteur de groupe ou un gain du téléphone l'ignore.
        Assert.Null(Telephone.LireGain(m));
        Assert.Equal("pc-a", JsonDocument.Parse(m).RootElement.GetProperty("a").GetString());
    }

    [Fact]
    public void Ligne_d_etat_pour_la_bulle()
    {
        long t = T0;
        var p = Jouer(Essai, Nouvelle(Essai, 1, t, "pc", "g", false), ref t, "pc", 3);
        var e = Rejouer(Essai, p, t);
        Assert.Equal("Pilou tourne en rond · retour vers 15 h 05", Ligne(e, new DateTime(2026, 11, 27, 15, 5, 0)));
        Assert.Equal("", Ligne(Rejouer(Essai, p, e.Fin), DateTime.Now));
    }
}
