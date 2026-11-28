using System.Globalization;
using System.IO;
using PilouBureau;
using Xunit;
using Xunit.Abstractions;

namespace PilouBureau.Tests;

// Les traits de personnalité (docs/TRAITS.md) : ce que la décision d'Antoine exige. On les découvre (aucun choix, aucune
// indication), ils ne se perdent pas, trois dominants au plus qui changent lentement, aucun chiffre ni bonus, une annonce
// dite une seule fois dans le groupe, des répliques sous la cadence de toujours. Les vecteurs partagés (TraitsVecteurs,
// plus bas) prouvent que le téléphone calcule exactement la même chose.
public class TraitsTests
{
    private readonly ITestOutputHelper _sortie;

    public TraitsTests(ITestOutputHelper sortie) => _sortie = sortie;

    private static readonly DateTime Lundi = new(2026, 11, 23); // un lundi
    private static int J(DateTime d) => Presence.Jour(d);

    // Un journal où le fait donné revient chaque jour, pendant n jours finissant la veille de « fin ».
    private static EtatPresence Vecu(DateTime fin, int n, Action<FaitsDuJour, DateTime> fait)
    {
        var e = PresenceTests.Neuf("pc-1", "pc");
        for (int d = n; d >= 1; d--)
        {
            var jour = fin.AddDays(-d);
            e.Marquer(J(jour));
            var f = e.Aujourdhui(Presence.JourTexte(jour));
            f.Mn = 60;
            fait(f, jour);
        }
        return e;
    }

    // ---- La définition et ses textes

    [Fact]
    public void Une_vingtaine_de_traits_bien_definis()
    {
        var t = Traits.Tous;
        Assert.InRange(t.Count, 18, Traits.Max);
        Assert.Equal(Enumerable.Range(1, t.Count), t.Select(x => x.Numero)); // numéros sans trou : un bit chacun
        Assert.Equal(t.Count, t.Select(x => x.Id).Distinct().Count());
        Assert.Equal(t.Count, t.Select(x => x.Nom).Distinct().Count());
        Assert.All(t, x => Assert.Matches("^[a-z]+(-[a-z]+)*$", x.Id));
        Assert.All(t, x => Assert.InRange(x.Seuil, 3, 60)); // une habitude, pas un coup de chance ni une corvée
        // Chaque ligne du fichier est un trait : aucune n'est ignorée pour une faute de frappe.
        var fichier = File.ReadAllLines(Path.Combine(CampagnesVecteurs.Racine().FullName, "assets", "traits.txt"));
        Assert.Equal(fichier.Count(l => l.Length > 0 && l[0] != '#'), t.Count);
    }

    [Fact]
    public void Une_condition_fausse_est_refusee()
    {
        Assert.NotNull(Traits.Condition("pc>=1&we=1"));
        Assert.NotNull(Traits.Condition("ex="));
        Assert.Null(Traits.Condition("xx>=1"));
        Assert.Null(Traits.Condition("pc>=beaucoup"));
        Assert.Null(Traits.Condition("ac>=3"));
        Assert.Null(Traits.Condition(""));
        Assert.Empty(Traits.Lire("1|a|A|0|pc>=1\n61|b|B|3|pc>=1\n2|c|C|3|pc\n"));
        Assert.Single(Traits.Lire("# titre\n1|a|A|3|pc>=1\n1|b|B|3|pc>=1\n"));
    }

    [Fact]
    public void Chaque_trait_a_son_annonce_ses_repliques_et_la_voix_de_Pilou()
    {
        var r = Presence.Repliques;
        string[] interdits =
        {
            "abandonn", "tu m'as laissé", "tu devrais", "il faut que tu", "dépêche", "travaille plus", "où étais-tu", "enfin te voilà",
            "trop tard", "pas assez", "encore toi", "bonus", " xp", "pièces", "points",
        };
        foreach (var t in Traits.Tous)
        {
            Assert.Single(r, l => l.Famille == "annonce-" + t.Id);
            Assert.True(r.Count(l => l.Famille == "trait-" + t.Id) >= 3, $"{t.Id} : trois répliques au moins");
        }
        // Aucune famille orpheline (un trait renommé laisserait ses mots derrière lui).
        var familles = Traits.Tous.SelectMany(t => new[] { "annonce-" + t.Id, "trait-" + t.Id }).ToHashSet();
        Assert.All(r, l => Assert.Contains(l.Famille, familles));
        Assert.All(r, l => Assert.True(l.Texte.Length <= Presence.LongueurMax, $"trop long ({l.Texte.Length}) : {l.Texte}"));
        Assert.All(r, l => Assert.True(char.IsLower(l.Texte[0]) || l.Texte[0] == '«', l.Texte));
        Assert.All(r, l => Assert.Empty(l.Trous)); // rien de personnel : pas même un prénom
        Assert.All(r, l => Assert.DoesNotContain(interdits, i => l.Texte.Contains(i, StringComparison.OrdinalIgnoreCase)));
        Assert.All(r, l => Assert.DoesNotContain(l.Texte, char.IsDigit)); // aucun chiffre : ni heures, ni seuil, ni score
        Assert.Equal(r.Count, r.Select(l => l.Texte).Distinct().Count());
        Assert.Equal(r.Count, r.Select(l => l.Id).Distinct().Count());
        // Les répliques ne se mêlent pas aux petits mots de toujours, mais Presence.Mot puise dans les deux.
        Assert.Equal(Presence.Mots.Count + r.Count, Presence.Banque.Count);
        Assert.DoesNotContain(Presence.Mots, l => l.Famille.StartsWith("trait-") || l.Famille.StartsWith("annonce-"));
    }

    [Fact]
    public void Chaque_trait_a_son_icone_et_les_inconnus_une_silhouette()
    {
        var b = Banque.DepuisDossier(Path.Combine(CampagnesVecteurs.Racine().FullName, "assets"));
        foreach (var id in Traits.Tous.Select(t => t.Sprite).Append("trait-inconnu"))
        {
            Assert.True(b[id] is { W: 16, H: 16 }, $"{id} : icône de 16 × 16 attendue");
            Assert.True(b.FinExact(id) is { W: 32, H: 32, Natif: true }, $"{id} : dessin fin attendu");
        }
        // Deux traits ne partagent pas la même icône.
        var dessins = Traits.Tous.Select(t => string.Join("\n", b[t.Sprite]!.Images[0])).ToList();
        Assert.Equal(dessins.Count, dessins.Distinct().Count());
    }

    // ---- Découvrir : par l'habitude, et pour toujours

    [Fact]
    public void Un_trait_nait_d_une_habitude_pas_d_un_soir()
    {
        var tard = Traits.Trouver("couche-tard")!;
        var e = Vecu(Lundi, tard.Seuil - 1, (f, _) => f.Ta = 23 * 60 + 30);
        Assert.False(Traits.Decouvrir(e));
        Assert.Equal(0, e.Moi.Traits & tard.Bit);
        e = Vecu(Lundi, tard.Seuil, (f, _) => f.Ta = 23 * 60 + 30);
        Assert.True(Traits.Decouvrir(e));
        Assert.NotEqual(0, e.Moi.Traits & tard.Bit);
        Assert.False(Traits.Decouvrir(e)); // rien de neuf la seconde fois
        // 22 h 50 n'est pas « tard » : le fait compte, pas l'intention.
        e = Vecu(Lundi, 40, (f, _) => f.Ta = 22 * 60 + 50);
        Traits.Decouvrir(e);
        Assert.Equal(0, e.Moi.Traits & tard.Bit);
    }

    [Fact]
    public void Chaque_trait_peut_se_decouvrir()
    {
        // Un journal assez varié fait naître tous les traits : aucun n'est hors d'atteinte.
        var e = PresenceTests.Neuf("pc-1", "pc");
        for (int d = 0; d < 200; d++)
        {
            if (d % 10 is 5 or 6 or 7 or 8 or 9 && d % 20 > 10) continue; // des absences de cinq jours
            var jour = Lundi.AddDays(-200 + d);
            var f = e.Aujourdhui(Presence.JourTexte(jour));
            f.Mn = 90;
            f.Ta = 23 * 60 + 10;
            f.Ma = 1;
            f.Pc = 1;
            f.Pq = d % 9 == 0 ? 3 : 0;
            f.Px = "une truite argentée";
            f.Cu = 1;
            f.Ca = 6;
            f.Jx = 3;
            f.So = 2;
            f.Ce = 1;
            (f.Ac, f.Am) = (new[] { "lecture", "code", "musique", "dessin", "video" }[d % 5], 200);
            if (d % 4 == 0) f.Ex = "Caverne des câbles";
            if (d % 4 == 1) f.Vi = 1;
            if (d % 5 == 0) f.Ob = "Écharpe";
        }
        Traits.Decouvrir(e);
        var manquants = Traits.Tous.Where(t => (e.Moi.Traits & t.Bit) == 0).Select(t => t.Id).ToList();
        Assert.True(manquants.Count == 0, "jamais découverts : " + string.Join(", ", manquants));
    }

    [Fact]
    public void Un_trait_acquis_ne_se_perd_pas()
    {
        var calin = Traits.Trouver("calin")!;
        var e = Vecu(Lundi, 10, (f, _) => f.Ca = 6);
        Traits.Decouvrir(e);
        Assert.NotEqual(0, e.Moi.Traits & calin.Bit);
        // Un an plus tard, le journal a oublié ces jours-là (400 jours gardés) : le trait reste.
        e.Journal.Clear();
        e.Compacter(J(Lundi) + 500);
        Assert.False(Traits.Decouvrir(e));
        Assert.NotEqual(0, e.Moi.Traits & calin.Bit);
        // Et il survit au fichier d'état.
        var relu = EtatPresence.Lire(e.Texte());
        Assert.Equal(e.Moi.Traits, relu.Moi.Traits);
        Assert.Equal(e.Texte(), relu.Texte());
    }

    [Fact]
    public void Journal_en_pause_rien_ne_se_decouvre()
    {
        // « Tenir son journal » coupé : aucun fait n'est noté, donc aucun trait ne naît. Rien n'est déduit d'ailleurs.
        var e = PresenceTests.Neuf("pc-1", "pc");
        for (int d = 1; d <= 60; d++) e.Ajouter("caresses", 10, Lundi.AddDays(-d));
        Assert.False(Traits.Decouvrir(e));
        Assert.Equal(0, e.Moi.Traits);
    }

    // ---- Entre appareils : union, comme les succès

    [Fact]
    public void Entre_appareils_les_traits_se_reunissent()
    {
        var pc = Vecu(Lundi, 10, (f, _) => f.Ca = 6);
        var tel = PresenceTests.Neuf("tel-1", "tel");
        for (int d = 10; d >= 1; d--) tel.Aujourdhui(Presence.JourTexte(Lundi.AddDays(-d))).Cu = 1;
        Traits.Decouvrir(pc);
        Traits.Decouvrir(tel);
        Assert.NotEqual(pc.Moi.Traits, tel.Moi.Traits);
        pc.Moi.TraitsDits = pc.Moi.Traits;
        int auj = J(Lundi);
        var mPc = pc.Message(auj);
        var mTel = tel.Message(auj);
        // Dans le désordre, en double : toujours la réunion, jamais moins.
        for (int k = 0; k < 3; k++)
        {
            tel.Recevoir(Appareil.LireMessage(mPc)!, auj);
            pc.Recevoir(Appareil.LireMessage(mTel)!, auj);
            pc.Recevoir(Appareil.LireMessage(mTel)!, auj);
        }
        long union = Traits.Trouver("calin")!.Bit | Traits.Trouver("gourmand")!.Bit;
        Assert.Equal(union, pc.Totaux().Traits);
        Assert.Equal(union, tel.Totaux().Traits);
        // Ce que le PC a déjà annoncé n'est pas redit par le téléphone.
        Assert.Equal(pc.Totaux().TraitsDits, tel.Totaux().TraitsDits);
        Assert.Equal("gourmand", Traits.AAnnoncer(Traits.Tous, tel.Totaux().Traits, tel.Totaux().TraitsDits)!.Id);
    }

    [Fact]
    public void Deux_appareils_qui_se_parlent_voient_les_memes_traits()
    {
        // Chaque jour, le PC note les caresses et les soirées, le téléphone la cuisine ; ils s'écrivent le soir.
        var pc = PresenceTests.Neuf("pc-1", "pc");
        var tel = PresenceTests.Neuf("tel-1", "tel");
        for (int d = 40; d >= 1; d--)
        {
            var jour = Lundi.AddDays(-d);
            int j = J(jour);
            var f = pc.Aujourdhui(Presence.JourTexte(jour));
            (f.Mn, f.Ca) = (60, 6);
            if (d > 20) f.Ta = 23 * 60 + 30;
            tel.Aujourdhui(Presence.JourTexte(jour)).Cu = 1;
            tel.Recevoir(Appareil.LireMessage(pc.Message(j))!, j);
            pc.Recevoir(Appareil.LireMessage(tel.Message(j))!, j);
            Traits.Decouvrir(pc);
            Traits.Decouvrir(tel);
        }
        int auj = J(Lundi);
        tel.Recevoir(Appareil.LireMessage(pc.Message(auj))!, auj);
        Assert.Equal(pc.Totaux().Traits, tel.Totaux().Traits);
        Assert.Equal(pc.Moi.Traits, tel.Moi.Traits); // le journal fusionné est le même : chacun découvre tout
        var d1 = Traits.Dominants(pc, auj).Select(t => t.Id).ToList();
        Assert.Equal(new[] { "calin", "gourmand", "flaneur" }, d1);
        Assert.Equal(d1, Traits.Dominants(tel, auj).Select(t => t.Id));
    }

    [Fact]
    public void Un_ancien_message_sans_traits_se_lit_et_n_efface_rien()
    {
        var e = Vecu(Lundi, 10, (f, _) => f.Ca = 6);
        Traits.Decouvrir(e);
        long avant = e.Moi.Traits;
        var ancien = new Appareil { Id = "tel-vieux", Sorte = "tel", Minutes = 50 };
        Assert.DoesNotContain("\ntr ", ancien.Message());
        e.Recevoir(Appareil.LireMessage(ancien.Message())!, J(Lundi));
        Assert.Equal(avant, e.Totaux().Traits);
        // Des bits abîmés ne plantent pas et ne dépassent pas les 60 traits possibles.
        Assert.Equal(0, Traits.DeHex("zz"));
        Assert.Equal(0, Traits.DeHex("-1"));
        Assert.Equal(0, Traits.DeHex("ffffffffffffffffffff"));
        Assert.Equal(0x5, Traits.DeHex(Traits.Hex(0x5)));
        Assert.True(Presence.Octets(e.Message(J(Lundi))) <= Presence.TailleMessage);
    }

    // ---- Dominants : trois, et lentement

    [Fact]
    public void Trois_dominants_au_plus_les_plus_vecus_ces_derniers_temps()
    {
        // Tout est acquis, mais ces quatre dernières semaines il a surtout veillé, cuisiné et reçu des caresses.
        var e = Vecu(Lundi, 28, (f, jour) =>
        {
            f.Ta = 23 * 60 + 30;
            f.Cu = 1;
            if (jour.Day % 2 == 0) f.Ca = 6;
        });
        long tous = Traits.Tous.Aggregate(0L, (a, t) => a | t.Bit);
        var d = Traits.Dominants(Traits.Tous, tous, Traits.Journal(e), J(Lundi));
        Assert.Equal(Traits.NombreDominants, d.Count);
        Assert.Equal(new[] { "couche-tard", "gourmand", "calin" }, d.Select(t => t.Id));
        // Un seul trait acquis : un seul dominant. Aucun : aucun.
        Assert.Single(Traits.Dominants(Traits.Tous, Traits.Trouver("voyageur")!.Bit, Traits.Journal(e), J(Lundi)));
        Assert.Empty(Traits.Dominants(Traits.Tous, 0, Traits.Journal(e), J(Lundi)));
    }

    [Fact]
    public void Les_dominants_ne_bougent_pas_dans_la_semaine()
    {
        var e = Vecu(Lundi, 40, (f, _) => f.Ta = 23 * 60 + 30);
        long acquis = Traits.Tous.Aggregate(0L, (a, t) => a | t.Bit);
        var lundi = Traits.Dominants(Traits.Tous, acquis, Traits.Journal(e), J(Lundi)).Select(t => t.Id).ToList();
        // La semaine se remplit de tout autre chose : rien ne change avant lundi prochain.
        for (int k = 0; k < 7; k++)
        {
            var f = e.Aujourdhui(Presence.JourTexte(Lundi.AddDays(k)));
            (f.Mn, f.Ca, f.Cu, f.Jx, f.So) = (120, 9, 3, 5, 4);
            Assert.Equal(lundi, Traits.Dominants(Traits.Tous, acquis, Traits.Journal(e), J(Lundi.AddDays(k))).Select(t => t.Id));
        }
        var suivant = Traits.Dominants(Traits.Tous, acquis, Traits.Journal(e), J(Lundi.AddDays(7))).Select(t => t.Id).ToList();
        Assert.Equal("couche-tard", suivant[0]); // trois semaines sur quatre : il reste en tête
        Assert.NotEqual(lundi, suivant);          // mais la semaine vécue se voit
        Assert.Equal(1, Traits.JourDeSemaine(J(Lundi)));
        Assert.Equal(7, Traits.JourDeSemaine(J(Lundi.AddDays(-1))));
        Assert.Equal(4, Traits.JourDeSemaine(0)); // le 1er janvier 1970 était un jeudi
        Assert.Equal(J(Lundi), Traits.Lundi(J(Lundi.AddDays(6))));
    }

    // ---- Ce que ça change : des mots, rien d'autre

    [Fact]
    public void Le_trait_est_annonce_une_seule_fois_au_bonjour()
    {
        var e = Vecu(Lundi, 10, (f, _) => f.Ca = 6);
        Traits.Decouvrir(e);
        var t = e.Totaux();
        var neuf = Traits.AAnnoncer(Traits.Tous, t.Traits, t.TraitsDits)!;
        Assert.Equal("calin", neuf.Id);
        var matin = Lundi.AddHours(9);
        var c = PresenceTests.Ctx(matin, Presence.Moment.Premier) with { TraitNouveau = neuf.Id };
        var choix = Presence.Mot(c, Presence.Banque, e.Dits, "g")!;
        Assert.Equal("annonce-calin", choix.Famille);
        Assert.Equal(Presence.Repliques.Single(l => l.Famille == "annonce-calin").Texte, choix.Texte);
        // Une date à fêter ou un nouveau palier passent d'abord : le trait attendra demain, il n'est pas perdu.
        var fete = Presence.Mot(c with { PalierNouveau = 1, Palier = 1 }, Presence.Banque, e.Dits, "g")!;
        Assert.Equal("palier-1", fete.Famille);
        // Annoncé : plus rien à annoncer, ni ici ni sur un autre appareil du groupe.
        e.Moi.TraitsDits |= neuf.Bit;
        t = e.Totaux();
        Assert.Null(Traits.AAnnoncer(Traits.Tous, t.Traits, t.TraitsDits));
        // Hors du bonjour (retour de pause, soir), jamais d'annonce.
        foreach (var m in new[] { Presence.Moment.Retour, Presence.Moment.Soir })
            Assert.DoesNotContain(Presence.Plan(PresenceTests.Ctx(matin, m) with { TraitNouveau = neuf.Id }, "g"), f => f.StartsWith("annonce-"));
    }

    [Fact]
    public void Les_repliques_viennent_des_dominants_sous_la_cadence_de_toujours()
    {
        var matin = Lundi.AddHours(9);
        var dominants = "couche-tard,gourmand,calin";
        var vus = new HashSet<string>();
        int traits = 0, total = 0;
        foreach (var m in new[] { Presence.Moment.Premier, Presence.Moment.Retour, Presence.Moment.Soir, Presence.Moment.Telephone })
            for (int g = 0; g < 400; g++)
            {
                var c = PresenceTests.Ctx(matin.AddDays(g % 5), m, absence: 60) with { Traits = dominants };
                var choix = Presence.Mot(c, Presence.Banque, new Dictionary<string, int>(), "graine-" + g)!;
                total++;
                if (!choix.Famille.StartsWith("trait-")) continue;
                traits++;
                vus.Add(choix.Famille["trait-".Length..]);
            }
        // Un mot sur quatre environ : la personnalité colore, elle ne remplace pas le reste.
        Assert.Equal(new[] { "calin", "couche-tard", "gourmand" }, vus.OrderBy(x => x, StringComparer.Ordinal));
        Assert.InRange(traits * 100 / total, 10, 40);
        // Sans trait dominant, le plan est celui d'avant, à la famille près.
        var sans = PresenceTests.Ctx(matin, Presence.Moment.Retour, absence: 60);
        Assert.DoesNotContain(Presence.Plan(sans, "g"), f => f.StartsWith("trait-") || f.StartsWith("annonce-"));
        Assert.Equal(Presence.Plan(sans, "g"), Presence.Plan(sans with { Traits = "" }, "g"));
        // La cadence ne connaît pas les traits : trois mots par jour au plus, qu'il en ait ou non.
        Assert.Equal(3, Cadences.Plafond("normal"));
    }

    [Fact]
    public void Tot_le_matin_se_note_comme_un_fait_du_jour()
    {
        Assert.False(Presence.TotLeMatin(4, 59));
        Assert.True(Presence.TotLeMatin(5, 0));
        Assert.True(Presence.TotLeMatin(7, 29));
        Assert.False(Presence.TotLeMatin(7, 30));
        var f = FaitsDuJour.Lire("mn=30;ma=7");
        Assert.Equal(1, f.Ma);
        Assert.Equal("mn=30;ma=1", f.Texte());
        Assert.Equal(1, FaitsDuJour.Fusion(new FaitsDuJour(), f).Ma);
        Assert.Equal(1, FaitsDuJour.Fusion(f, new FaitsDuJour()).Ma);
    }

    // ---- Vecteurs partagés avec le téléphone

    [Fact]
    public void Vecteurs_partages_avec_le_telephone()
    {
        var chemin = Path.Combine(CampagnesVecteurs.Racine().FullName, TraitsVecteurs.Reference);
        var texte = TraitsVecteurs.Tout();
        Assert.Equal(texte, TraitsVecteurs.Tout());
        if (Environment.GetEnvironmentVariable("PILOU_REGENERER") == "1") File.WriteAllText(chemin, texte);
        Assert.True(File.Exists(chemin), $"{TraitsVecteurs.Reference} manque : PILOU_REGENERER=1 dotnet test");
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
        _sortie.WriteLine($"{texte.Split('\n').Length} lignes");
    }
}

// Vecteurs partagés des traits : une ligne = une opération, ses entrées (séparées par des tabulations), puis le résultat.
// android/app/src/test/resources/traits-vecteurs.txt ; TraitsTest.java refait chaque opération.
//   trait <numéro> <identifiant> <nom> <seuil> <condition relue>
//   cas <aujourd'hui> <acquis avant, hex> <journal : « jour faits|jour faits »> <mesures « n,n,… »> <acquis après, hex>
//       <dominants « a,b,c »> <à annoncer, annoncés = acquis avant>
//   etat <état de présence> <aujourd'hui> <acquis du groupe> <annoncés du groupe> <dominants> <état après Decouvrir>
//   mot <moment> <date> <palier> <trait nouveau> <traits> <graine> <famille|id|texte>
//   bits <hex lu> <hex relu>
public static class TraitsVecteurs
{
    public const string Reference = "android/app/src/test/resources/traits-vecteurs.txt";
    private static readonly CultureInfo Ci = CultureInfo.InvariantCulture;

    public static string Condition(Traits.Trait t) => string.Join("&", t.Condition.Select(c => c.Fait + c.Op + c.Valeur));

    private static FaitsDuJour Hasard(Random h)
    {
        var f = PresenceTests.Hasard(h);
        f.Mn = Math.Max(f.Mn, 5);
        if (h.Next(2) == 0) f.Ma = 1;
        if (h.Next(2) == 0) f.Ta = h.Next(1300, 1440);
        if (h.Next(3) == 0) f.Ca = h.Next(4, 9);
        if (h.Next(3) == 0) f.So = h.Next(1, 4);
        if (h.Next(3) == 0) f.Jx = h.Next(2, 6);
        if (h.Next(3) == 0) (f.Ac, f.Am) = (new[] { "lecture", "code", "musique", "dessin", "video" }[h.Next(5)], h.Next(10, 300));
        return f;
    }

    public static string Tout()
    {
        var l = new List<string> { "# vecteurs des traits (apps/PilouBureau/tests/TraitsTests.cs) : ne pas modifier à la main" };
        void Ligne(params string[] champs) => l.Add(string.Join("\t", champs));

        foreach (var t in Traits.Tous)
            Ligne("trait", t.Numero.ToString(Ci), t.Id, t.Nom, t.Seuil.ToString(Ci), Condition(t));

        // Des journaux de toutes tailles, troués d'absences, lus à des jours variés de la semaine.
        var h = new Random(2811);
        int debut = Presence.Jour(new DateTime(2026, 1, 1));
        for (int i = 0; i < 60; i++)
        {
            int n = h.Next(0, 140), jour = debut + h.Next(0, 400);
            var journal = new SortedDictionary<int, FaitsDuJour>();
            for (int k = 0; k < n; k++)
            {
                jour += h.Next(6) == 0 ? h.Next(2, 9) : 1;
                var f = Hasard(h);
                if (!f.Vide) journal[jour] = f;
            }
            int auj = jour + h.Next(0, 10);
            long avant = h.Next(3) == 0 ? (long)h.Next(0, 1 << 20) : 0;
            long apres = avant | Traits.Acquis(Traits.Tous, journal);
            Ligne("cas", auj.ToString(Ci), Traits.Hex(avant),
                string.Join("|", journal.Select(kv => Presence.JourTexte(kv.Key) + " " + kv.Value.Texte())),
                string.Join(",", Traits.Tous.Select(t => Traits.Mesure(t, journal).ToString(Ci))),
                Traits.Hex(apres),
                string.Join(",", Traits.Dominants(Traits.Tous, apres, journal, auj).Select(t => t.Id)),
                Traits.AAnnoncer(Traits.Tous, apres, avant)?.Id ?? "-");
        }

        // Des états entiers : deux appareils, des faits croisés, ce que le groupe a déjà découvert et annoncé.
        for (int i = 0; i < 12; i++)
        {
            var e = new EtatPresence { Moi = new Appareil { Id = "pc-" + i, Sorte = "pc" } };
            var autre = new Appareil { Id = "tel-" + i, Sorte = "tel", Traits = h.Next(0, 1 << 20), TraitsDits = h.Next(0, 1 << 20) };
            int auj = debut + 300 + h.Next(0, 60);
            for (int d = 90; d >= 0; d--)
            {
                if (h.Next(5) == 0) continue;
                var jour = Presence.JourTexte(auj - d);
                var f = Hasard(h);
                e.Aujourdhui(jour);
                e.Journal[jour][e.Moi.Id] = f;
                if (h.Next(3) == 0) e.Journal[jour][autre.Id] = Hasard(h);
                e.Marquer(auj - d);
            }
            e.Recevoir(autre, auj);
            e.Moi.TraitsDits = h.Next(0, 1 << 20);
            var avant = e.Texte();
            Traits.Decouvrir(e);
            var t = e.Totaux();
            Ligne("etat", PresenceVecteurs.Echapper(avant), auj.ToString(Ci), Traits.Hex(t.Traits), Traits.Hex(t.TraitsDits),
                string.Join(",", Traits.Dominants(e, auj).Select(x => x.Id)), PresenceVecteurs.Echapper(e.Texte()));
        }

        // Les mots : l'annonce au bonjour, les répliques des dominants à tous les moments.
        var ids = Traits.Tous.Select(t => t.Id).ToList();
        var dits = new Dictionary<string, int>();
        for (int i = 0; i < 160; i++)
        {
            var d = new DateTime(2026, 1, 1).AddDays(h.Next(0, 800)).AddMinutes(h.Next(0, 1440));
            var m = (Presence.Moment)h.Next(4);
            var nouveau = h.Next(3) == 0 ? ids[h.Next(ids.Count)] : "";
            var dominants = string.Join(",", Enumerable.Range(0, h.Next(0, 4)).Select(_ => ids[h.Next(ids.Count)]).Distinct());
            int palier = h.Next(0, 5);
            var graine = Presence.JourTexte(d) + "|pc-" + h.Next(3) + "|" + h.Next(3);
            var c = new Presence.Contexte(d, m, h.Next(0, 3000), h.Next(0, 600), h.Next(0, 400), "", "", palier, 2, "", "",
                TraitNouveau: nouveau, Traits: dominants);
            var choix = Presence.Mot(c, Presence.Banque, dits, graine);
            Ligne("mot", m.ToString(), d.ToString("yyyy-MM-dd'T'HH:mm", Ci), palier.ToString(Ci), nouveau, dominants, graine,
                choix is null ? "-" : choix.Famille + "|" + choix.Ligne.Id + "|" + choix.Texte);
        }

        foreach (var s in new[] { "0", "1", "5", "fffff", "80000", "fffffffffffffff", "ffffffffffffffff", "zz", "", "-1", "1F" })
            Ligne("bits", s, Traits.Hex(Traits.DeHex(s)));
        return string.Join("\n", l) + "\n";
    }
}
