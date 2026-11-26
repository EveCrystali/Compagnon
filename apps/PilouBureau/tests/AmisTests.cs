using System.Text.Json;
using PilouBureau;
using Xunit;

public class AmisTests
{
    private const double T0 = 1_800_000_000_000;

    private static (CarnetAmis A, CarnetAmis B) DeuxPc() =>
        (new CarnetAmis { Moi = Amis.NouvelleIdentite() }, new CarnetAmis { Moi = Amis.NouvelleIdentite() });

    private static Vitrine Vitrine(string nom = "Pilou") => new() { Nom = nom, Niveau = 7, Stade = 3, Equipe = new() { ["tete"] = "chapeau-pirate" } };

    // ---- Codes

    [Fact]
    public void CodeAmiEstLEmpreinteDeLaCle()
    {
        var id = Amis.NouvelleIdentite();
        Assert.Equal(12, id.Code.Length);
        Assert.True(Amis.Valide(id.Code));
        Assert.Equal(id.Code, Amis.Empreinte(id.Publique));
        Assert.Matches("^PILOU-[A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4}$", Amis.Formater(id.Code));
        Assert.NotEqual(id.Code, Amis.NouvelleIdentite().Code);
    }

    [Fact]
    public void CodeSaisiNormalise()
    {
        Assert.Equal("7F3K9QXAM2HT".Replace("0", ""), Amis.Normaliser("pilou-7f3k 9qxa-m2ht"));
        Assert.True(Amis.Valide("PILOU-7F3K-9QXA-M2HT"));
        Assert.True(Amis.Valide("7f3k9qxam2ht"));
        Assert.False(Amis.Valide("PILOU-7F3K-9QXA"));
        // Un code de groupe (16 signes) n'est pas un code ami.
        Assert.False(Amis.Valide("ABCD-EFGH-JKMN-PQRS"));
    }

    [Fact]
    public void CleQuiNeRedonnePasLeCodeEstRefusee()
    {
        var a = Amis.NouvelleIdentite();
        var b = Amis.NouvelleIdentite();
        Assert.True(Amis.Authentique(a.Code, a.Publique));
        Assert.False(Amis.Authentique(a.Code, b.Publique));
        Assert.False(Amis.Authentique(a.Code, "pas du base64 !"));
        Assert.False(Amis.Authentique(a.Code, null));
    }

    // ---- Dérivations : même vecteur que android/.../AmisTest.java

    [Fact]
    public void VecteurCommunAvecLeTelephone()
    {
        Assert.Equal("pilou-85913c41bb6794a5b77c6709", Amis.SujetBoite("PILOU-ABCD-EFGH-JKMN"));
        Assert.Equal(Amis.SujetBoite("PILOU-ABCD-EFGH-JKMN"), Amis.SujetBoite("abcd efgh jkmn"));
        Assert.Equal("d3b777c4a2b5cd51c1c107381b283c7be4ef1b066da675e1430ee805d5b538a4", Convert.ToHexString(Amis.CleBoite("ABCDEFGHJKMN")).ToLowerInvariant());
        var secret = Enumerable.Range(0, 32).Select(i => (byte)i).ToArray();
        var (sujet, cle) = Amis.Paire(secret, "PILOU-ABCD-EFGH-JKMN", "PILOU-PQRS-TUVW-XYZ2");
        Assert.Equal("pilou-abbaa91136238890812f2bd3", sujet);
        Assert.Equal("84365017af9cc44dd3433b1b13c2eb20dd7b83b04f12bed742b82a3873b1ff64", Convert.ToHexString(cle).ToLowerInvariant());
        Assert.Equal("GQWMKMXKYVZM", Amis.Empreinte(Convert.ToBase64String(secret)));
    }

    [Fact]
    public void PaireIdentiqueDesDeuxCotesEtSecreteSansLesCles()
    {
        var a = Amis.NouvelleIdentite();
        var b = Amis.NouvelleIdentite();
        var pa = Amis.Paire(Amis.Secret(a, b.Publique), a.Code, b.Code);
        var pb = Amis.Paire(Amis.Secret(b, a.Publique), b.Code, a.Code);
        Assert.Equal(pa.Sujet, pb.Sujet);
        Assert.Equal(pa.Cle, pb.Cle);
        // Un tiers qui connaît les deux codes (et même les deux clés publiques) n'a pas le secret.
        var c = Amis.NouvelleIdentite();
        var pc = Amis.Paire(Amis.Secret(c, b.Publique), a.Code, b.Code);
        Assert.NotEqual(pa.Sujet, pc.Sujet);
        var chiffre = Amis.Chiffrer(pa.Cle, "{\"t\":\"ici\"}");
        Assert.Equal("{\"t\":\"ici\"}", Amis.Dechiffrer(pb.Cle, chiffre));
        Assert.Null(Amis.Dechiffrer(pc.Cle, chiffre));
        Assert.Null(Amis.Dechiffrer(pa.Cle, "n'importe quoi"));
        // Sujets distincts du groupe et du téléphone.
        Assert.NotEqual(Groupe.Sujet("ABCD-EFGH-JKMN-PQRS"), Amis.SujetBoite("ABCDEFGHJKMN"));
    }

    // ---- Amitié

    [Fact]
    public void AmitieActiveQuandLesDeuxSeSontAjoutes()
    {
        var (a, b) = DeuxPc();
        var ea = Annuaire.Ajouter(a, Amis.Formater(b.Moi.Code), Vitrine("Léo"), T0);
        var demande = Assert.Single(ea, x => x.Quoi == "boite");
        Assert.Equal(b.Moi.Code, demande.Ami);
        Assert.Equal(EtatAmi.Attente, a.Trouver(b.Moi.Code)!.Etat);

        // B reçoit la demande sans avoir ajouté A : elle attend son accord.
        var eb = Annuaire.Boite(b, Amis.Lire(Amis.Ecrire(demande.Message!))!, Vitrine(), T0 + 1000);
        Assert.Contains(eb, x => x.Quoi == "demande");
        Assert.Equal(EtatAmi.Recue, b.Trouver(a.Moi.Code)!.Etat);
        Assert.Equal("Léo", b.Trouver(a.Moi.Code)!.Pilou.Nom);

        // B ajoute A à son tour (ou accepte) : accord envoyé dans la boîte de A.
        var accord = Assert.Single(Annuaire.Ajouter(b, a.Moi.Code, Vitrine(), T0 + 2000), x => x.Quoi == "boite");
        Assert.Equal("accepte", accord.Message!.T);
        Assert.Equal(EtatAmi.Actif, b.Trouver(a.Moi.Code)!.Etat);
        var fin = Annuaire.Boite(a, Amis.Lire(Amis.Ecrire(accord.Message))!, Vitrine("Léo"), T0 + 3000);
        Assert.Contains(fin, x => x.Quoi == "ami");
        Assert.Equal(EtatAmi.Actif, a.Trouver(b.Moi.Code)!.Etat);
        Assert.Equal(b.Moi.Publique, a.Trouver(b.Moi.Code)!.Cle);
    }

    [Fact]
    public void DemandesCroiseesDonnentUneAmitie()
    {
        var (a, b) = DeuxPc();
        var da = Annuaire.Ajouter(a, b.Moi.Code, Vitrine(), T0).Single().Message!;
        var db = Annuaire.Ajouter(b, a.Moi.Code, Vitrine(), T0).Single().Message!;
        Annuaire.Boite(b, da, Vitrine(), T0 + 10);
        Annuaire.Boite(a, db, Vitrine(), T0 + 10);
        Assert.Equal(EtatAmi.Actif, a.Trouver(b.Moi.Code)!.Etat);
        Assert.Equal(EtatAmi.Actif, b.Trouver(a.Moi.Code)!.Etat);
    }

    [Fact]
    public void DemandeUsurpeeIgnoree()
    {
        var (a, b) = DeuxPc();
        var pirate = Amis.NouvelleIdentite();
        Annuaire.Ajouter(b, a.Moi.Code, Vitrine(), T0);
        // Le pirate connaît le code de A et celui de B, mais pas la clé privée de A : sa clé ne redonne pas le code.
        var m = Amis.Message("demande", a.Moi.Code, T0);
        m.Cle = pirate.Publique;
        Assert.Empty(Annuaire.Boite(b, m, Vitrine(), T0));
        Assert.Equal(EtatAmi.Attente, b.Trouver(a.Moi.Code)!.Etat);
        Assert.Equal("", b.Trouver(a.Moi.Code)!.Cle);
    }

    [Fact]
    public void CodesRefuses()
    {
        var (a, _) = DeuxPc();
        Assert.NotNull(Annuaire.Refus(a, a.Moi.Code));
        Assert.NotNull(Annuaire.Refus(a, "PILOU-12"));
        Assert.Empty(Annuaire.Ajouter(a, a.Moi.Code, Vitrine(), T0));
        Assert.Empty(a.Amis);
    }

    [Fact]
    public void RetirerPrevientLAmiParLaPaire()
    {
        var (a, b) = Amis2();
        var e = Annuaire.Retirer(a, b.Moi.Code, T0);
        Assert.Equal("envoi", Assert.Single(e).Quoi);
        Assert.Empty(a.Amis);
        var r = Annuaire.Paire(b, b.Trouver(a.Moi.Code)!, Amis.Lire(Amis.Ecrire(e[0].Message!))!, T0 + 5);
        Assert.Contains(r, x => x.Quoi == "retire");
        Assert.Empty(b.Amis);
    }

    private static (CarnetAmis A, CarnetAmis B) Amis2()
    {
        var (a, b) = DeuxPc();
        var d = Annuaire.Ajouter(a, b.Moi.Code, Vitrine(), T0).Single().Message!;
        Annuaire.Boite(b, d, Vitrine(), T0);
        var acc = Annuaire.Accepter(b, a.Moi.Code, Vitrine(), T0).First(x => x.Quoi == "boite").Message!;
        Annuaire.Boite(a, acc, Vitrine(), T0);
        return (a, b);
    }

    [Fact]
    public void ListeVuIlYaEtEnLigne()
    {
        var a = new Ami { Code = "ABCDEFGHJKMN", Etat = EtatAmi.Actif, Vu = T0 - 5 * 60_000 };
        Assert.True(Amis.EnLigne(a, T0));
        Assert.Equal("en ligne", Amis.VuIlYa(a, T0));
        a.Vu = T0 - 40 * 60_000;
        Assert.False(Amis.EnLigne(a, T0));
        Assert.Equal("vu il y a 40 min", Amis.VuIlYa(a, T0));
        a.Vu = T0 - 3 * 3600_000;
        Assert.Equal("vu il y a 3 h", Amis.VuIlYa(a, T0));
        Assert.Equal("en attente de son accord", Amis.VuIlYa(new Ami { Etat = EtatAmi.Attente }, T0));
    }

    // ---- Messages et données partagées

    [Fact]
    public void MessageBorneEtNettoye()
    {
        var m = Amis.Message("presence", "ABCDEFGHJKMN", T0);
        m.Pilou = new Vitrine
        {
            Nom = "Léo‮\u0007" + new string('x', 80), Niveau = 50_000, Stade = 9, Variante = "pirate",
            Equipe = new() { ["tete"] = "chapeau-pirate", ["inconnu"] = "x", ["yeux"] = "<script>" },
            Faits = new Faits { Meteo = "Paris 12e", Quete = new string('q', 500) },
        };
        var lu = Amis.Lire(Amis.Ecrire(m))!;
        Assert.Equal(24, lu.Pilou!.Nom.Length);
        Assert.StartsWith("Léo", lu.Pilou.Nom);
        Assert.Equal(999, lu.Pilou.Niveau);
        Assert.Equal(4, lu.Pilou.Stade);
        Assert.Equal("", lu.Pilou.Variante);
        Assert.Equal(new[] { "tete" }, lu.Pilou.Equipe.Keys.ToArray());
        Assert.Equal("", lu.Pilou.Faits!.Meteo);
        Assert.Equal(60, lu.Pilou.Faits.Quete.Length);
        Assert.Null(Amis.Lire("{\"t\":\"pirater\",\"de\":\"ABCDEFGHJKMN\"}"));
        Assert.Null(Amis.Lire("{\"t\":\"ici\",\"de\":\"court\"}"));
        Assert.Null(Amis.Lire("pas du json"));
    }

    [Fact]
    public void AnecdotesSansDonneePrivee()
    {
        var p = new Profil();
        p.Carnet["goujon"] = 3;
        p.Carnet[Butin.Prises.First(x => x.Rarete >= Rarete.Rare).Id] = 1;
        p.Plats.Add("soupe");
        p.Plats.Add("inv:Soupe secrète de Mamie");
        p.Quetes.Liste.Add(new Quete { Texte = "Pêche 3 prises", Reussie = true });
        p.Activites["code"] = 3600;
        p.Succes.Add("marathon");
        // Données qui ne doivent jamais sortir : titres de fenêtres, sessions, connecteurs, ville.
        p.Recus.Add("session-secrète-42");
        Meteo.Courante = new Meteo.Situation(Meteo.Pluie, null!, "Ville-Secrète", DateTime.Now);
        try
        {
            var faits = Amis.FaitsDe(p, Meteo.Pluie);
            var v = new Vitrine { Nom = "Pilou", Niveau = 12, Faits = faits };
            var m = Amis.Message("presence", "ABCDEFGHJKMN", T0);
            m.Pilou = v;
            var json = Amis.Ecrire(m);
            foreach (var secret in new[] { "Ville-Secrète", "session-secrète-42", "Mamie", "Marathon de code", "3600", "code\":" })
                Assert.DoesNotContain(secret, json);
            var props = JsonDocument.Parse(json).RootElement.GetProperty("pilou").GetProperty("faits").EnumerateObject().Select(x => x.Name).ToArray();
            Assert.Equal(new[] { "prise", "plat", "quete", "succes", "meteo", "evolution" }, props);
            var l = Amis.Anecdotes(Amis.Borner(v));
            Assert.Contains("je suis niveau 12 maintenant !", l);
            Assert.Contains(l, x => x.Contains("Soupe du pêcheur"));
            Assert.Contains(l, x => x.Contains("pleut"));
            Assert.Contains(l, x => x.Contains(Butin.Prises.Where(z => p.Carnet.ContainsKey(z.Id)).MaxBy(z => z.Rarete)!.Nom, StringComparison.OrdinalIgnoreCase));
            Assert.Contains(l, x => x.Contains("Marathon"));
        }
        finally
        {
            Meteo.Courante = null;
        }
    }

    [Fact]
    public void LignesDuRelais()
    {
        var texte = "{\"id\":\"a1\",\"time\":1700000000,\"event\":\"open\",\"topic\":\"pilou-x\"}\n"
                    + "{\"id\":\"a2\",\"time\":1700000005,\"event\":\"message\",\"topic\":\"pilou-x\",\"message\":\"QUJD\"}\n"
                    + "{\"id\":\"a3\",\"time\":1700000006,\"event\":\"keepalive\"}\n{tronqué\n"
                    + "{\"id\":\"a4\",\"time\":1700000009,\"event\":\"message\",\"topic\":\"pilou-y\",\"message\":\"REVG\"}";
        var l = Amis.LireRelais(texte);
        Assert.Equal(new[] { "a2", "a4" }, l.Select(b => b.Id).ToArray());
        Assert.Equal("pilou-y", l[1].Sujet);
        Assert.Equal(1700000009, l[1].Temps);
        Assert.Empty(Amis.LireRelais(""));
    }

    [Fact]
    public void SurnomLocalEtClePriveeJamaisEcrite()
    {
        var a = new Ami { Pilou = new Vitrine { Nom = "Pilou" } };
        Assert.Equal("Pilou", a.Nom);
        a.Surnom = "Léo";
        Assert.Equal("Léo", a.Nom);
        var c = new CarnetAmis { Moi = Amis.NouvelleIdentite() };
        var json = JsonSerializer.Serialize(c, Amis.Json);
        Assert.DoesNotContain(c.Moi.Privee, json);
        Assert.DoesNotContain("privee", json);
    }

    [Fact]
    public void HeuresCalmes()
    {
        Assert.True(Amis.Calme(23, 22, 8));
        Assert.True(Amis.Calme(3, 22, 8));
        Assert.False(Amis.Calme(8, 22, 8));
        Assert.False(Amis.Calme(14, 22, 8));
        Assert.True(Amis.Calme(13, 12, 14));
        Assert.False(Amis.Calme(13, 10, 10));
    }

    // ---- Machine à états d'une visite

    private static readonly PorteAmi Ouverte = new(true, false, false);

    private static (CarnetAmis A, CarnetAmis B, Visites Va, Visites Vb) Duo()
    {
        var (a, b) = Amis2();
        return (a, b, new Visites(), new Visites());
    }

    // Livre les messages « envoi » produits d'un côté à la machine de l'autre.
    private static List<Effet> Livrer(IEnumerable<Effet> effets, CarnetAmis vers, Visites v, PorteAmi porte, double t)
    {
        var r = new List<Effet>();
        foreach (var e in effets.Where(x => x.Quoi == "envoi"))
        {
            var m = Amis.Lire(Amis.Ecrire(e.Message!))!;
            r.AddRange(v.Recevoir(m, vers.Trouver(m.De), vers.Moi.Code, porte, t));
        }
        return r;
    }

    [Fact]
    public void VisiteComplete()
    {
        var (a, b, va, vb) = Duo();
        var jour = new Journee();
        var ami = a.Trouver(b.Moi.Code)!;
        var depart = va.Partir(ami, a.Moi.Code, Vitrine("Léo"), T0, 6 * 60_000, false, jour);
        Assert.Contains(depart, x => x.Quoi == "depart");
        Assert.Equal(Etape.Depart, va.Sortie!.Etape);

        var chezB = Livrer(depart, b, vb, Ouverte, T0 + 20_000);
        Assert.Contains(chezB, x => x.Quoi == "arrivee");
        Assert.Equal("Léo", vb.Venue!.Invite.Nom);
        Assert.Contains(Livrer(chezB, a, va, Ouverte, T0 + 40_000), x => x.Quoi == "accueilli");
        Assert.True(va.Sortie.Accueilli);

        Assert.DoesNotContain(va.Avancer(a.Moi.Code, T0 + 1000), x => x.Quoi != "envoi");
        va.Avancer(a.Moi.Code, T0 + Visites.DepartMs + 1);
        Assert.Equal(Etape.Absent, va.Sortie.Etape);
        Assert.Contains(vb.Avancer(b.Moi.Code, T0 + 20_000 + Visites.ArriveeMs + 1), x => x.Quoi == "present");

        // Battements pendant la visite : chacun garde le contact.
        var ici = va.Avancer(a.Moi.Code, T0 + 2 * 60_000);
        Assert.Contains(ici, x => x.Message?.T == "ici");
        Livrer(ici, b, vb, Ouverte, T0 + 2 * 60_000);
        Assert.Equal(T0 + 2 * 60_000, vb.Venue.Contact);

        // Les deux PC lisent le relais toutes les 30 s : la visite se poursuit sans « silence ».
        double fin = T0 + Visites.DepartMs + 6 * 60_000;
        var vus = new List<Effet>();
        for (double t = T0 + 150_000; t < fin - 10_000; t += 30_000)
        {
            vus.AddRange(Livrer(va.Avancer(a.Moi.Code, t), b, vb, Ouverte, t + 5000));
            vus.AddRange(Livrer(vb.Avancer(b.Moi.Code, t + 5000), a, va, Ouverte, t + 10_000));
        }
        Assert.Empty(vus);
        Assert.Equal(Etape.Present, vb.Venue.Etape);

        // Au bout de la durée, chacun de son côté : l'invité part, Pilou rentre.
        var retour = va.Avancer(a.Moi.Code, fin + 1);
        Assert.Contains(retour, x => x.Quoi == "retour" && x.Raison == "fini");
        // Pilou prévient l'hôte en partant : son invité s'en va tout de suite, sans attendre sa propre horloge.
        var depart2 = Livrer(retour, b, vb, Ouverte, fin + 5000);
        Assert.Contains(depart2, x => x.Quoi == "invite-part" && x.Raison == "fin");
        Assert.Equal(Etape.Sortie, vb.Venue!.Etape);
        // L'hôte, de son côté, finit aussi à son heure ; ça ne fait rien de plus.
        Assert.DoesNotContain(vb.Avancer(b.Moi.Code, fin + 5001), x => x.Quoi == "invite-part");
        var rentre = va.Avancer(a.Moi.Code, fin + Visites.RetourMs + 2);
        Assert.Contains(rentre, x => x.Quoi == "rentre" && x.Raison == "fini");
        Assert.Null(va.Sortie);
        Assert.Contains(vb.Avancer(b.Moi.Code, T0 + 20_000 + 6 * 60_000 + Visites.SortieMs + 2), x => x.Quoi == "invite-parti");
        Assert.Null(vb.Venue);
        Assert.Equal((0, 0), (jour.Spontanees, jour.Cadeaux));
    }

    [Fact]
    public void DureeBorneeEntreCinqEtDixMinutes()
    {
        var r = new Random(4);
        for (int i = 0; i < 50; i++)
        {
            double d = Visites.Duree(r);
            Assert.InRange(d, Visites.DureeMin, Visites.DureeMax);
        }
        var (a, b, va, _) = Duo();
        va.Partir(a.Trouver(b.Moi.Code)!, a.Moi.Code, Vitrine(), T0, 60 * 60_000, false, new Journee());
        Assert.Equal(T0 + Visites.DepartMs + Visites.DureeMax, va.Sortie!.Fin);
    }

    [Fact]
    public void RappelRentreTouteSuiteEtPrevientLHote()
    {
        var (a, b, va, vb) = Duo();
        var d = va.Partir(a.Trouver(b.Moi.Code)!, a.Moi.Code, Vitrine(), T0, 8 * 60_000, false, new Journee());
        Livrer(Livrer(d, b, vb, Ouverte, T0 + 1000), a, va, Ouverte, T0 + 2000);
        va.Avancer(a.Moi.Code, T0 + Visites.DepartMs + 10);
        var rappel = va.Rappeler(a.Moi.Code, T0 + 60_000);
        Assert.Contains(rappel, x => x.Quoi == "retour" && x.Raison == "rappel");
        Assert.Equal(Etape.Retour, va.Sortie!.Etape);
        var chezB = Livrer(rappel, b, vb, Ouverte, T0 + 70_000);
        Assert.Contains(chezB, x => x.Quoi == "invite-part" && x.Raison == "rappel");
        // Un second rappel ne fait rien.
        Assert.Empty(va.Rappeler(a.Moi.Code, T0 + 61_000));
    }

    [Fact]
    public void RefusQuandLHoteNePeutPas()
    {
        foreach (var (porte, raison) in new[] { (new PorteAmi(false, false, false), "ferme"), (new PorteAmi(true, true, false), "occupe"), (new PorteAmi(true, false, true), "calme") })
        {
            var (a, b, va, vb) = Duo();
            var d = va.Partir(a.Trouver(b.Moi.Code)!, a.Moi.Code, Vitrine(), T0, 6 * 60_000, false, new Journee());
            var reponse = Livrer(d, b, vb, porte, T0 + 1000);
            Assert.Null(vb.Venue);
            Assert.Equal(raison, Assert.Single(reponse).Message!.Raison);
            var chezA = Livrer(reponse, a, va, Ouverte, T0 + 2000);
            Assert.Contains(chezA, x => x.Quoi == "retour" && x.Raison == "refus:" + raison);
        }
    }

    [Fact]
    public void UnSeulInviteALaFois()
    {
        var (a, b, va, vb) = Duo();
        var c = new CarnetAmis { Moi = Amis.NouvelleIdentite() };
        var vc = new Visites();
        // C devient ami de B.
        var dc = Annuaire.Ajouter(c, b.Moi.Code, Vitrine(), T0).Single().Message!;
        Annuaire.Boite(b, dc, Vitrine(), T0);
        Annuaire.Boite(c, Annuaire.Accepter(b, c.Moi.Code, Vitrine(), T0).First(x => x.Quoi == "boite").Message!, Vitrine(), T0);

        Livrer(va.Partir(a.Trouver(b.Moi.Code)!, a.Moi.Code, Vitrine(), T0, 6 * 60_000, false, new Journee()), b, vb, Ouverte, T0 + 10);
        var refus = Livrer(vc.Partir(c.Trouver(b.Moi.Code)!, c.Moi.Code, Vitrine(), T0, 6 * 60_000, false, new Journee()), b, vb, Ouverte, T0 + 20);
        Assert.Equal("invite", Assert.Single(refus).Message!.Raison);
        Assert.Equal(a.Moi.Code, vb.Venue!.Ami);
    }

    [Fact]
    public void AmiDeconnecteChacunRentreSeul()
    {
        // Pas d'accueil après le départ : il rentre au bout de 2 min 30.
        var (a, b, va, vb) = Duo();
        va.Partir(a.Trouver(b.Moi.Code)!, a.Moi.Code, Vitrine(), T0, 6 * 60_000, false, new Journee());
        Assert.DoesNotContain(va.Avancer(a.Moi.Code, T0 + 60_000), x => x.Quoi == "retour");
        Assert.Contains(va.Avancer(a.Moi.Code, T0 + Visites.AttenteMax + 1), x => x.Quoi == "retour" && x.Raison == "silence");

        // Accueilli, puis plus de nouvelles : l'invité quitte l'écran de l'hôte, et Pilou rentre de son côté.
        (a, b, va, vb) = Duo();
        var d = va.Partir(a.Trouver(b.Moi.Code)!, a.Moi.Code, Vitrine(), T0, 10 * 60_000, false, new Journee());
        Livrer(Livrer(d, b, vb, Ouverte, T0 + 1000), a, va, Ouverte, T0 + 2000);
        Assert.Contains(vb.Avancer(b.Moi.Code, T0 + 1000 + Visites.SilenceMax + 1), x => x.Quoi == "invite-part" && x.Raison == "silence");
        Assert.Contains(va.Avancer(a.Moi.Code, T0 + 2000 + Visites.SilenceMax + 1), x => x.Quoi == "retour" && x.Raison == "silence");
    }

    [Fact]
    public void HoteQuiPasseEnPleinEcranRaccompagne()
    {
        var (a, b, va, vb) = Duo();
        var d = va.Partir(a.Trouver(b.Moi.Code)!, a.Moi.Code, Vitrine(), T0, 6 * 60_000, false, new Journee());
        Livrer(Livrer(d, b, vb, Ouverte, T0 + 1000), a, va, Ouverte, T0 + 2000);
        var fin = vb.Congedier(b.Moi.Code, T0 + 30_000, "discret");
        Assert.Contains(fin, x => x.Quoi == "invite-part");
        Assert.Contains(Livrer(fin, a, va, Ouverte, T0 + 31_000), x => x.Quoi == "retour" && x.Raison == "fin");
    }

    [Fact]
    public void PasDeVisiteSiPasAmiOuDejaParti()
    {
        var (a, b, va, _) = Duo();
        var ami = a.Trouver(b.Moi.Code)!;
        Assert.Empty(va.Partir(new Ami { Code = "ABCDEFGHJKMN", Etat = EtatAmi.Attente }, a.Moi.Code, Vitrine(), T0, 6e5, false, new Journee()));
        va.Partir(ami, a.Moi.Code, Vitrine(), T0, 6e5, false, new Journee());
        Assert.Empty(va.Partir(ami, a.Moi.Code, Vitrine(), T0 + 1, 6e5, false, new Journee()));
        // Un message d'un inconnu ne touche à rien.
        var m = Amis.Message("rappel", Amis.NouvelleIdentite().Code, T0);
        Assert.Empty(va.Recevoir(m, null, a.Moi.Code, Ouverte, T0));
    }

    // ---- Plafonds du jour

    [Fact]
    public void EnvieDePartirDeuxFoisParJourAuPlus()
    {
        var (a, b, va, _) = Duo();
        var ami = a.Trouver(b.Moi.Code)!;
        ami.Vu = T0 - 60_000;
        var jour = new Journee();
        Visites.Actualiser(jour, new DateTime(2026, 11, 26, 14, 0, 0));
        var r = new Random(1);
        Assert.Same(ami, va.Envie(a.Amis, jour, true, true, false, false, T0, r));
        Assert.Null(va.Envie(a.Amis, jour, false, true, false, false, T0, r));   // réglage décoché
        Assert.Null(va.Envie(a.Amis, jour, true, false, false, false, T0, r));   // PC occupé
        Assert.Null(va.Envie(a.Amis, jour, true, true, true, false, T0, r));     // plein écran, visio…
        Assert.Null(va.Envie(a.Amis, jour, true, true, false, true, T0, r));     // heures calmes
        ami.Pilou.Accepte = false;
        Assert.Null(va.Envie(a.Amis, jour, true, true, false, false, T0, r));
        ami.Pilou.Accepte = true;
        ami.Pilou.Libre = false;
        Assert.Null(va.Envie(a.Amis, jour, true, true, false, false, T0, r));
        ami.Pilou.Libre = true;
        Assert.Null(va.Envie(a.Amis, jour, true, true, false, false, T0 + Amis.EnLigneMs, r)); // hors ligne

        for (int i = 0; i < 2; i++)
        {
            Assert.NotNull(va.Envie(a.Amis, jour, true, true, false, false, T0, r));
            va.Partir(ami, a.Moi.Code, Vitrine(), T0, 6e5, true, jour);
            va.Sortie = null;
        }
        Assert.Equal(2, jour.Spontanees);
        Assert.Null(va.Envie(a.Amis, jour, true, true, false, false, T0, r));
        // Le lendemain, le compteur repart.
        Visites.Actualiser(jour, new DateTime(2026, 11, 27, 9, 0, 0));
        Assert.Equal(0, jour.Spontanees);
    }

    [Fact]
    public void CadeauxEtCaressesPlafonnes()
    {
        var j = new Journee();
        var r = new Random(2);
        Assert.Equal((0, 0), Visites.Cadeau(j, "fini", false, r));      // jamais accueilli
        Assert.Equal((0, 0), Visites.Cadeau(j, "refus:ferme", true, r));
        Assert.Equal((0, 0), Visites.Cadeau(j, "silence", true, r));
        var (po, xp) = Visites.Cadeau(j, "fini", true, r);
        Assert.InRange(po, 8, 15);
        Assert.Equal(5, xp);
        Assert.NotEqual(0, Visites.Cadeau(j, "rappel", true, r).Po);
        Assert.Equal((0, 0), Visites.Cadeau(j, "fini", true, r));
        Assert.Equal(10, Enumerable.Range(0, 8).Sum(_ => Visites.Caresse(j)));
    }

    [Fact]
    public void CaresseDeLHoteArriveChezLInvite()
    {
        var (a, b, va, vb) = Duo();
        var d = va.Partir(a.Trouver(b.Moi.Code)!, a.Moi.Code, Vitrine(), T0, 6e5, false, new Journee());
        Livrer(Livrer(d, b, vb, Ouverte, T0 + 1000), a, va, Ouverte, T0 + 2000);
        va.Avancer(a.Moi.Code, T0 + Visites.DepartMs + 1);
        var m = Amis.Message("caresse", b.Moi.Code, T0 + 10_000);
        m.Visite = vb.Venue!.Id;
        Assert.Contains(va.Recevoir(m, a.Trouver(b.Moi.Code), a.Moi.Code, Ouverte, T0 + 10_000), x => x.Quoi == "caresse");
    }

    [Fact]
    public void CarnetRelu()
    {
        var dossier = Path.Combine(Path.GetTempPath(), "pilou-amis-" + Guid.NewGuid().ToString("N"));
        try
        {
            var (a, _) = Amis2();
            a.Jour.Spontanees = 1;
            a.Ecrire(dossier);
            var lu = CarnetAmis.Lire(dossier);
            Assert.Equal(a.Moi.Code, lu.Moi.Code);
            Assert.Equal(EtatAmi.Actif, lu.Amis.Single().Etat);
            Assert.Equal(1, lu.Jour.Spontanees);
            Assert.Equal("", CarnetAmis.Lire(dossier + "-absent").Moi.Code);
        }
        finally
        {
            if (Directory.Exists(dossier)) Directory.Delete(dossier, true);
        }
    }
}
