using PilouBureau;
using Xunit;
using Xunit.Abstractions;
using static PilouBureau.Campagnes;

// Synchronisation PC ↔ téléphone sur les vraies campagnes (docs/TEST-JEU.md) : le téléphone avance PC éteint, deux
// appareils divergent puis se retrouvent, des messages se perdent, arrivent deux fois ou dans le désordre ; les
// récompenses sont versées une fois par le PC ; et la taille des messages au pire (quatre campagnes finies avec toutes
// leurs fins, trois mises de côté, la plus longue jouée jusqu'au bout).
public class SynchroParcoursTests(ITestOutputHelper sortie)
{
    private const long T0 = CampagnesVecteurs.T0;
    private const string Code = "ABCD-EFGH-JKMN-PQRS";
    private static Campagne? B(string id) => CampagnesVecteurs.Biblio(id);

    // Un pas d'un joueur simple : une option au hasard, les dés pour une épreuve, « vas-y », l'attente franchie.
    private static Campagnes.Etat? Pas(Carnet k, Campagne c, ref long t, string appareil, Hasard h)
    {
        var e = Actualiser(k, B, t);
        if (e is null || !e.EnCours) return e;
        if (e.EnAttente)
        {
            t = Math.Max(t, e.Fin) + h.Suivant(60) * 1000L;
            return Actualiser(k, B, t);
        }
        t += 5_000 + h.Suivant(60) * 1000L;
        _ = e.Phase switch
        {
            Phase.Choix => Choisir(k, c, t, appareil, e.Options[h.Suivant(e.Options.Count)].Id),
            Phase.Epreuve => EpreuveAuDe(k, c, t, appareil),
            Phase.Depart => Continuer(k, c, t, appareil),
            _ => null,
        };
        return Actualiser(k, B, t);
    }

    // Suit une marche du simulateur sur un carnet (pour remplir un historique avec des fins précises).
    private static void Suivre(Carnet k, Campagne c, Simu.Marche m, ref long t, string appareil, Action? mesure = null)
    {
        Assert.Null(Demarrer(k, c, 99, t, appareil, B, m.Graine, neuf: true));
        foreach (var pas in m.Pas)
        {
            var e = Actualiser(k, B, t)!;
            string? r = null;
            switch (pas.Action)
            {
                case "": break;
                case "temps": t = Math.Max(t, e.Fin); break;
                case "abandon":
                    r = Abandonner(k, c, e.Phase == Phase.Attente ? e.T + (e.Fin - e.T) / 2 : t += 1000, appareil);
                    t = Math.Max(t, e.Fin) + 60_000;
                    r ??= Demarrer(k, c, 99, t, appareil, B, "x");
                    break;
                default:
                    t += 20_000;
                    if (pas.Action.StartsWith("o:", StringComparison.Ordinal)) r = Choisir(k, c, t, appareil, pas.Action[2..]);
                    else if (pas.Action is "ok" or "ko") r = Epreuve(k, c, t, appareil, pas.Action == "ok");
                    else if (pas.Action == "de") r = EpreuveAuDe(k, c, t, appareil);
                    else if (pas.Action == "suite") r = Continuer(k, c, t, appareil);
                    break;
            }
            Assert.Null(r);
            mesure?.Invoke();
        }
        Assert.Equal(Phase.Fin, Actualiser(k, B, t)!.Phase);
    }

    private static void Echanger(Carnet a, string ida, string sa, Carnet b, string idb, string sb, long t)
    {
        foreach (var m in Messages(a, ida, sa)) Recevoir(b, m, idb, B, t);
        Actualiser(b, B, t);
        foreach (var m in Messages(b, idb, sb)) Recevoir(a, m, ida, B, t);
        Actualiser(a, B, t);
    }

    [Theory]
    [InlineData("grande-panne")]
    [InlineData("phare-eteint")]
    [InlineData("petit-nuage")]
    public void Le_telephone_finit_la_campagne_PC_eteint_puis_le_PC_verse_une_fois(string id)
    {
        var c = Charger(id)!;
        var tel = new Carnet();
        var h = new Hasard(Hasard.Graine("pc-eteint|" + id));
        long t = T0;
        Assert.Null(Demarrer(tel, c, 99, t, "tel-b", B, "g-" + id));
        var envois = new List<string>();
        Campagnes.Etat? e = null;
        for (int i = 0; i < 3000 && (e is null || e.EnCours); i++)
        {
            e = Pas(tel, c, ref t, "tel-b", h);
            envois.AddRange(Messages(tel, "tel-b", "tel"));   // publiés, mais personne n'écoute
        }
        Assert.Equal(Phase.Fin, e!.Phase);
        var acquis = Acquis(tel, c);
        Assert.Equal(acquis, EnAttente(tel, B));               // tout attend un PC
        // Le PC se rallume : il ne lit que le dernier message (les autres ont expiré sur le relais).
        var pc = new Profil { Machine = "PC" };
        Assert.True(Recevoir(pc.CarnetCampagnes, envois[^1], "pc-a", B, t + 1000));
        Assert.Equal(Phase.Fin, Actualiser(pc.CarnetCampagnes, B, t + 1000)!.Phase);
        Assert.Equal(acquis, Acquis(pc.CarnetCampagnes, c));
        var v = Crediter(pc, B);
        Assert.Equal(acquis, (v.Po, v.Xp));
        // Un ancien message arrive en retard, puis le dernier une seconde fois : rien ne bouge, rien n'est reversé.
        var signature = Signature(pc.CarnetCampagnes);
        Recevoir(pc.CarnetCampagnes, envois[envois.Count / 2], "pc-a", B, t + 2000);
        Recevoir(pc.CarnetCampagnes, envois[^1], "pc-a", B, t + 2000);
        Actualiser(pc.CarnetCampagnes, B, t + 2000);
        Assert.Equal(signature, Signature(pc.CarnetCampagnes));
        Assert.Equal((0, 0), (Crediter(pc, B).Po, Crediter(pc, B).Xp));
        // Le téléphone lit le PC : plus rien n'attend.
        foreach (var m in Messages(pc.CarnetCampagnes, "pc-a", "pc")) Recevoir(tel, m, "tel-b", B, t + 3000);
        Assert.Equal((0, 0), EnAttente(tel, B));
        Assert.Equal(Signature(pc.CarnetCampagnes), Signature(tel));
        sortie.WriteLine($"{id} : {envois.Count} messages publiés PC éteint, le plus gros {envois.Max(Octets)} octets ; {acquis.Po} po, {acquis.Xp} xp versés une fois");
    }

    // Deux appareils jouent la même partie à tour de rôle ; 40 % des messages se perdent, certains arrivent deux fois ou
    // en retard. À la fin, tout arrive : les deux carnets sont identiques, la partie est finie, le PC verse une fois.
    [Theory]
    [InlineData("grande-panne", 1)]
    [InlineData("phare-eteint", 2)]
    [InlineData("petit-nuage", 3)]
    [InlineData("prologue", 4)]
    public void Messages_perdus_doubles_et_en_desordre(string id, int graine)
    {
        var c = Charger(id)!;
        var pc = new Profil { Machine = "PC" };
        var tel = new Carnet();
        var h = new Hasard((ulong)graine * 7919);
        long t = T0;
        Assert.Null(Demarrer(pc.CarnetCampagnes, c, 99, t, "pc-a", B, "g" + graine));
        Echanger(pc.CarnetCampagnes, "pc-a", "pc", tel, "tel-b", "tel", t);
        var enRetard = new List<(Carnet Vers, string Moi, string M)>();
        int perdus = 0, doubles = 0, retards = 0, refus = 0, pas = 0;
        Campagnes.Etat? e = null;
        for (; pas < 4000; pas++)
        {
            bool surLePc = h.Suivant(2) == 0;
            var (k, moi, sorte, autre, lui) = surLePc ? (pc.CarnetCampagnes, "pc-a", "pc", tel, "tel-b") : (tel, "tel-b", "tel", pc.CarnetCampagnes, "pc-a");
            e = Actualiser(k, B, t);
            if (e is not null && !e.EnCours && Actualiser(autre, B, t) is { EnCours: false }) break;
            var avant = Signature(k);
            e = Pas(k, c, ref t, moi, h);
            if (Signature(k) == avant) refus++;
            if (surLePc) Crediter(pc, B);
            foreach (var m in Messages(k, moi, sorte))
            {
                int x = h.Suivant(10);
                if (x < 4) perdus++;
                else if (x < 5)
                {
                    enRetard.Add((autre, lui, m));
                    retards++;
                }
                else
                {
                    Recevoir(autre, m, lui, B, t);
                    if (x == 9)
                    {
                        Recevoir(autre, m, lui, B, t);
                        doubles++;
                    }
                }
            }
            if (enRetard.Count > 0 && h.Suivant(3) == 0)
            {
                var (vers, qui, m) = enRetard[h.Suivant(enRetard.Count)];
                Recevoir(vers, m, qui, B, t);
            }
        }
        foreach (var (vers, qui, m) in enRetard) Recevoir(vers, m, qui, B, t);
        Echanger(pc.CarnetCampagnes, "pc-a", "pc", tel, "tel-b", "tel", t + 1000);
        Echanger(tel, "tel-b", "tel", pc.CarnetCampagnes, "pc-a", "pc", t + 2000);
        Assert.Equal(Phase.Fin, Actualiser(pc.CarnetCampagnes, B, t + 2000)!.Phase);
        Assert.Equal(Signature(pc.CarnetCampagnes), Signature(tel));
        Crediter(pc, B);
        var acquis = Acquis(pc.CarnetCampagnes, c);
        Assert.Equal(acquis, (pc.Bourse.PoCampagnes, pc.XpTelephone));
        Assert.Equal((0, 0), (Crediter(pc, B).Po, Crediter(pc, B).Xp));
        Assert.Equal((0, 0), EnAttente(tel, B));
        Assert.True(acquis.Po <= 600 && acquis.Xp <= 300, $"{acquis}");
        sortie.WriteLine($"{id} : {pas} pas, {perdus} messages perdus, {doubles} doublés, {retards} en retard, {refus} décisions sans effet "
                         + $"(appareil en retard) ; carnets identiques à la fin, {acquis.Po} po {acquis.Xp} xp versés une fois");
    }

    // Divergence : au même choix, le PC choisit d'abord, le téléphone (hors ligne) un peu après. Dans le délai de grâce
    // (10 min), le plus ancien gagne et le téléphone revient sur la route du PC. Au-delà, chacun ayant avancé seul, la
    // base la plus avancée l'emporte : les deux carnets se retrouvent quand même identiques.
    [Theory]
    [InlineData("phare-eteint", false)]
    [InlineData("phare-eteint", true)]
    [InlineData("petit-nuage", false)]
    [InlineData("grande-panne", true)]
    public void Deux_appareils_divergent_puis_se_retrouvent(string id, bool auDela)
    {
        var c = Charger(id)!;
        var pc = new Carnet();
        var tel = new Carnet();
        var h = new Hasard(Hasard.Graine("divergence|" + id));
        long t = T0;
        Assert.Null(Demarrer(pc, c, 99, t, "pc-a", B, "g"));
        Campagnes.Etat e = Actualiser(pc, B, t)!;
        // Avancer jusqu'à un choix à deux options au moins, au chapitre 2.
        for (int i = 0; i < 500 && !(e.Phase == Phase.Choix && e.Options.Count >= 2 && e.ChapitreNumero >= 2); i++) e = Pas(pc, c, ref t, "pc-a", h)!;
        Echanger(pc, "pc-a", "pc", tel, "tel-b", "tel", t);
        var et = Actualiser(tel, B, t)!;
        Assert.Equal(e.Noeud, et.Noeud);
        Assert.Null(Choisir(pc, c, t + 10_000, "pc-a", e.Options[0].Id));
        Assert.Null(Choisir(tel, c, t + 70_000, "tel-b", e.Options[1].Id));
        long tp = t + 10_000, tt = t + 70_000;
        if (auDela)
            for (int i = 0; i < 6; i++)
            {
                Pas(pc, c, ref tp, "pc-a", h);
                Pas(tel, c, ref tt, "tel-b", h);
            }
        long tm = Math.Max(tp, tt) + (auDela ? 0 : 60_000);
        if (!auDela) tm = t + 3 * 60_000;
        Echanger(tel, "tel-b", "tel", pc, "pc-a", "pc", tm);
        Echanger(pc, "pc-a", "pc", tel, "tel-b", "tel", tm + 1000);
        var ep = Actualiser(pc, B, tm + 2000)!;
        var et2 = Actualiser(tel, B, tm + 2000)!;
        Assert.Equal(ep.Texte(), et2.Texte());
        Assert.Equal(Signature(pc), Signature(tel));
        // Aucun fil ne garde le choix perdant (ni la suite qu'il avait racontée) : un seul choix au nœud de la divergence.
        var choix = pc.Fil.Concat(tel.Fil).Where(m => m.Qui == "joueur" && m.Noeud == e.Noeud).Select(m => m.Texte).Distinct().ToList();
        Assert.True(choix.Count <= 1, string.Join(" / ", choix));
        foreach (var k in new[] { pc, tel })
        {
            var cles = k.Fil.Select(m => (m.P, m.E, m.I)).ToList();
            Assert.Equal(cles.Count, cles.Distinct().Count());
            Assert.Equal(cles.OrderBy(x => x.P).ThenBy(x => x.E).ThenBy(x => x.I), cles); // dans l'ordre de l'histoire
        }
        string gagnant = choix.Count == 0 ? "(choix hors du fil)" : choix[0] == e.Options[0].Libelle ? "le PC (le plus ancien)" : "le téléphone (le plus avancé)";
        if (!auDela) Assert.Equal(new[] { e.Options[0].Libelle }, choix);
        sortie.WriteLine($"{id}, {(auDela ? "au-delà" : "dans")} du délai de grâce : au choix {e.Noeud}, c'est {gagnant} qui l'emporte ; "
                         + $"fils de {pc.Fil.Count} et {tel.Fil.Count} messages ; carnets identiques");
    }

    // Divergence quand le perdant est en retard : au même choix, chacun prend sa route ; le PC avance de huit pas, le
    // téléphone d'aucun. Le rejeu du téléphone n'atteint pas l'étape de la base reçue (rien à comparer au même point) :
    // c'est la route des décisions, portée par la base, qui dit que les histoires se sont séparées. Le fil du téléphone
    // ne garde pas son choix perdant, et les deux carnets se retrouvent identiques.
    [Theory]
    [InlineData("phare-eteint")]
    [InlineData("grande-panne")]
    [InlineData("petit-nuage")]
    public void Divergence_quand_le_perdant_est_en_retard(string id)
    {
        var c = Charger(id)!;
        var pc = new Carnet();
        var tel = new Carnet();
        var h = new Hasard(Hasard.Graine("retard|" + id));
        long t = T0;
        Assert.Null(Demarrer(pc, c, 99, t, "pc-a", B, "g"));
        Campagnes.Etat e = Actualiser(pc, B, t)!;
        for (int i = 0; i < 500 && !(e.Phase == Phase.Choix && e.Options.Count >= 2 && e.ChapitreNumero >= 2); i++) e = Pas(pc, c, ref t, "pc-a", h)!;
        Echanger(pc, "pc-a", "pc", tel, "tel-b", "tel", t);
        Assert.Null(Choisir(pc, c, t + 10_000, "pc-a", e.Options[0].Id));
        Assert.Null(Choisir(tel, c, t + 70_000, "tel-b", e.Options[1].Id));
        long tp = t + 10_000;
        for (int i = 0; i < 8; i++) Pas(pc, c, ref tp, "pc-a", h);
        long tm = Math.Max(tp, t + 70_000) + 3_600_000;
        Actualiser(pc, B, tm);
        Actualiser(tel, B, tm);
        // Le cas visé : le rejeu du téléphone est en retard sur la base du PC.
        Assert.True(Rejouer(c, tel.Courante!, tm).E < pc.Courante!.E, $"rejeu {Rejouer(c, tel.Courante!, tm).E}, base reçue {pc.Courante!.E}");
        foreach (var m in Messages(pc, "pc-a", "pc")) Recevoir(tel, m, "tel-b", B, tm);
        Actualiser(tel, B, tm);
        var perdu = tel.Fil.Where(m => m.Qui == "joueur" && m.Noeud == e.Noeud && m.Texte == e.Options[1].Libelle).ToList();
        Assert.True(perdu.Count == 0, $"le fil du téléphone garde le choix perdant « {e.Options[1].Libelle} »");
        Echanger(tel, "tel-b", "tel", pc, "pc-a", "pc", tm + 1000);
        Assert.Equal(Signature(pc), Signature(tel));
        var cles = tel.Fil.Select(m => (m.P, m.E, m.I)).ToList();
        Assert.Equal(cles.Count, cles.Distinct().Count());
        sortie.WriteLine($"{id} : base reçue à l'étape {pc.Courante!.E}, fil du téléphone de {tel.Fil.Count} messages, sans le choix perdant");
    }

    // Taille des messages au pire, sur les vraies campagnes : un carnet qui a obtenu les 20 fins des quatre campagnes,
    // trois campagnes mises de côté, et la plus longue marche de chaque campagne jouée jusqu'au bout.
    [Fact]
    public void Taille_des_messages_au_pire()
    {
        var k = new Carnet();
        long t = T0;
        int maxJson = 0, maxChiffre = 0;
        string pire = "";
        void Mesurer()
        {
            foreach (var m in Messages(k, "PC-BUREAU-1a2b", "pc"))
            {
                Assert.True(Octets(m) <= TailleJson, $"{Octets(m)} octets de JSON");
                if (Octets(m) <= maxJson) continue;
                maxJson = Octets(m);
                pire = m;
                maxChiffre = Math.Max(maxChiffre, Telephone.Chiffrer(Code, m).Length);
            }
        }
        var lignes = new List<string>();
        foreach (var id in ParcoursTests.Ids)
        {
            var r = ParcoursTests.Chercher(id);
            var c = r.S.C;
            foreach (var fin in r.Fins.Keys.OrderBy(x => x, StringComparer.Ordinal))
                Suivre(k, c, r.Toutes.First(m => m.Fin == fin && m.Defauts.Count == 0), ref t, "pc-a");
            t += 3_600_000;
        }
        // Trois campagnes mises de côté au milieu, puis la plus longue marche de la quatrième, mesurée pas à pas.
        foreach (var id in ParcoursTests.Ids)
        {
            var autres = ParcoursTests.Ids.Where(x => x != id).ToList();
            foreach (var a in autres)
            {
                var c = Charger(a)!;
                Assert.Null(Demarrer(k, c, 99, t, "tel-b", B, "s-" + a, neuf: true));
                var h = new Hasard(Hasard.Graine("suspendue|" + a));
                for (int i = 0; i < (a == "prologue" ? 3 : 40) && Actualiser(k, B, t)!.EnCours; i++) Pas(k, c, ref t, "tel-b", h);
                Assert.Null(Abandonner(k, c, t += 1000, "tel-b"));
                Actualiser(k, B, t);
            }
            var r = ParcoursTests.Chercher(id);
            var longue = r.Toutes.Where(m => m.Fin != "" && m.Defauts.Count == 0).OrderByDescending(m => m.Pas.Count).First();
            int avant = maxJson;
            maxJson = 0;
            Suivre(k, r.S.C, longue, ref t, "pc-a", Mesurer);
            lignes.Add($"{id} : plus longue marche ({longue.Pas.Count} pas, {longue.Echecs} échecs, {longue.Abandons} abandons), "
                       + $"20 fins dans l'historique, {k.Suspendues.Count} parties suspendues : {maxJson} octets de JSON au plus");
            maxJson = Math.Max(avant, maxJson);
            t += 3_600_000;
        }
        foreach (var l in lignes) sortie.WriteLine(l);
        sortie.WriteLine($"au pire : {maxJson} octets de JSON (limite {TailleJson}), {maxChiffre} chiffrés (limite {Telephone.TailleMax})");
        sortie.WriteLine("message le plus gros : " + pire);
        Assert.True(maxChiffre <= Telephone.TailleMax);
    }
}
