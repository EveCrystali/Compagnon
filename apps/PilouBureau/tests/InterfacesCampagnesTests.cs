using PilouBureau;
using Xunit;
using Xunit.Abstractions;
using static PilouBureau.Campagnes;

// Test de jeu, côté Windows (docs/TEST-JEU.md) : WPF ne tourne pas ici, on vérifie donc ce que les écrans de campagne
// lisent. Chaque humeur, tenue, décor, souvenir, objet, vignette et emblème qu'une campagne référence a de quoi être
// dessiné aux deux échelles ; les textes les plus longs passent entiers par la logique de la fenêtre ; les scènes
// d'essai (--essai=campagne:<id>) vont jusqu'à une fin dans leur budget de pas.
public class InterfacesCampagnesTests(ITestOutputHelper sortie)
{
    private static readonly Lazy<Banque> B = new(() => Banque.DepuisDossier(Path.Combine(CampagnesVecteurs.Racine().FullName, "assets")));

    [Fact]
    public void Tout_ce_qu_une_campagne_reference_se_dessine_aux_deux_echelles()
    {
        var b = B.Value;
        var manque = new List<string>();
        foreach (var id in ParcoursTests.Ids)
        {
            var c = Charger(id)!;
            if (Illustrations.Vignette(b, c.Id, 1) is null || Illustrations.Vignette(b, c.Id, 2) is null) manque.Add($"campagne-{c.Id}");
            if (Illustrations.Ton(b, c.Ton, 1) is null || Illustrations.Ton(b, c.Ton, 2) is null) manque.Add($"ton-{c.Ton}");
            foreach (var n in c.Noeuds.Values.OrderBy(n => n.Id, StringComparer.Ordinal))
            {
                if (n.Decor != "" && (Illustrations.Decor(b, c.Id, n.Decor, 1) is null || Illustrations.Decor(b, c.Id, n.Decor, 2) is null))
                    manque.Add($"{n.Id} : {Aventure.SpriteDecor(c.Id, n.Decor)}");
                if (!Humeurs.Contains(n.Humeur)) manque.Add($"{n.Id} : humeur {n.Humeur}");
                else if (n.Humeur != "neutre" && RenduPilou.NomOeil(n.Humeur) is { Length: > 0 } oeil && (b["oeil-" + oeil] is null || b.Fin("oeil-" + oeil) is null))
                    manque.Add($"{n.Id} : oeil-{oeil}");
                if (n.Type == "attente" && !RenduPilou.Voyages.Contains(n.Tenue)) manque.Add($"{n.Id} : tenue {n.Tenue} (voyage-{n.Tenue})");
                if (n.Type == "fin")
                {
                    var r = n.Recompense;
                    if (r.Souvenir != "" && (Illustrations.Souvenir(b, c.Id, r.Souvenir, 1) is null || Illustrations.Souvenir(b, c.Id, r.Souvenir, 2) is null))
                        manque.Add($"{n.Id} : {Illustrations.IdSouvenir(c.Id, r.Souvenir)}");
                    if (r.Objet != "" && (b[r.Objet] is null || b.Fin(r.Objet) is null)) manque.Add($"{n.Id} : objet {r.Objet}");
                    if (r.Objet != "" && Boutique.TrouverTout(r.Objet) is null) manque.Add($"{n.Id} : objet {r.Objet} inconnu de la boutique");
                }
            }
        }
        Assert.True(manque.Count == 0, string.Join("\n", manque));
    }

    // Les plus longs textes réels passent entiers par la logique de la fenêtre (fil, options, fin) : rien n'est coupé.
    [Fact]
    public void Les_textes_les_plus_longs_passent_entiers()
    {
        foreach (var id in ParcoursTests.Ids)
        {
            var c = Charger(id)!;
            var long1 = c.Noeuds.Values.SelectMany(n => n.Texte).OrderByDescending(t => t.Split(' ').Length).First();
            var choix = c.Noeuds.Values.Where(n => n.Type == "choix").OrderByDescending(n => n.Options.Count).ThenByDescending(n => n.Options.Sum(o => o.Libelle.Length)).First();
            int mots = long1.Split(' ', StringSplitOptions.RemoveEmptyEntries).Length;
            int libelle = c.Noeuds.Values.SelectMany(n => n.Options).Max(o => o.Libelle.Length);
            sortie.WriteLine($"{id} : message le plus long {mots} mots ; choix le plus chargé {choix.Id} ({choix.Options.Count} options, "
                             + $"{choix.Options.Sum(o => o.Libelle.Length)} caractères) ; libellé le plus long {libelle} caractères");
            Assert.True(mots <= 160, $"{id} : {mots} mots");
            Assert.True(libelle <= 60, $"{id} : libellé de {libelle} caractères");
            // Le fil de la fenêtre garde chaque message en entier.
            var k = new Carnet();
            long t = CampagnesVecteurs.T0;
            Assert.Null(Demarrer(k, c, 99, t, "pc", Charger, "fil"));
            var h = new Hasard(Hasard.Graine("fil|" + id));
            for (int i = 0; i < 3000; i++)
            {
                var e = Actualiser(k, Charger, t)!;
                if (!e.EnCours) break;
                if (e.EnAttente) t = e.Fin;
                else if (e.Phase == Phase.Choix) Choisir(k, c, t += 1000, "pc", e.Options[h.Suivant(e.Options.Count)].Id);
                else if (e.Phase == Phase.Epreuve) EpreuveAuDe(k, c, t += 1000, "pc");
                else Continuer(k, c, t += 1000, "pc");
                foreach (var x in Aventure.Fil(k, c))
                    if (x.Texte != "" && !k.Fil.Any(m => m.Texte == x.Texte) && !x.Texte.StartsWith("↺", StringComparison.Ordinal) && x.Sorte.ToString() is "Pilou" or "Joueur")
                        Assert.Fail($"{id} : texte du fil transformé : {x.Texte}");
            }
            var fin = Actualiser(k, Charger, t)!;
            Assert.Equal(Phase.Fin, fin.Phase);
            Assert.NotEmpty(Aventure.Gains(c, fin));
        }
    }

    // --essai=campagne:<id> (FenetreCampagne.EssaiCampagne) : même politique, un message ou une décision par pas, au plus
    // 600 pas. Chaque campagne doit y arriver à une fin.
    [Theory]
    [InlineData("prologue")]
    [InlineData("grande-panne")]
    [InlineData("phare-eteint")]
    [InlineData("petit-nuage")]
    public void La_scene_d_essai_va_jusqu_a_une_fin(string id)
    {
        var c = Charger(id)!;
        var k = new Carnet();
        long t = CampagnesVecteurs.T0;
        Assert.Null(Demarrer(k, c, int.MaxValue, t, "essai", Charger, "essai"));
        int choix = 0, pas = 0;
        Campagnes.Etat? e = null;
        while (++pas <= 600)
        {
            e = Actualiser(k, Charger, t)!;
            if (k.Fil.FirstOrDefault(m => NonLu(k, m)) is { } m)
            {
                k.Lu = $"{m.P}.{m.E}.{m.I}";
                continue;
            }
            if (!e.EnCours) break;
            switch (e.Phase)
            {
                case Phase.Choix: Choisir(k, c, t += 1000, "essai", e.Options[choix++ % e.Options.Count].Id); break;
                case Phase.Epreuve: EpreuveAuDe(k, c, t += 1000, "essai"); break;
                case Phase.Depart: Continuer(k, c, t += 1000, "essai"); break;
                default: t = e.Fin; break;
            }
        }
        sortie.WriteLine($"{id} : --essai=campagne:{id} finit en {pas} pas de 2,5 s ({pas * 2.5 / 60:0.0} min), fin {e!.Noeud}");
        Assert.Equal(Phase.Fin, e.Phase);
    }
}
