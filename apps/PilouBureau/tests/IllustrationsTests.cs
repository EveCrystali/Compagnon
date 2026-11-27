using Xunit;

namespace PilouBureau.Tests;

// Illustrations des campagnes (docs/SPRITES.md) : chaque décor, souvenir, objet exclusif et vignette déclaré dans une
// fiche de assets/campagnes a son sprite, au bon format, aux deux échelles.
public class IllustrationsTests
{
    private static readonly Lazy<Banque> B = new(() => Banque.DepuisDossier(Path.Combine(CampagnesVecteurs.Racine().FullName, "assets")));

    private static IEnumerable<Campagnes.Campagne> Fiches()
    {
        var racine = Path.Combine(CampagnesVecteurs.Racine().FullName, "assets", "campagnes");
        foreach (var d in Directory.GetDirectories(racine).OrderBy(x => x, StringComparer.Ordinal))
        {
            var fiche = Path.Combine(d, "campagne.json");
            if (!File.Exists(fiche)) continue;
            var c = Campagnes.Lire(File.ReadAllText(fiche), f => File.Exists(Path.Combine(d, f)) ? File.ReadAllText(Path.Combine(d, f)) : null);
            Assert.NotNull(c);
            yield return c!;
        }
    }

    private static bool Opaque(Sprite s) => s.Images.All(im => im.All(l => !l.Contains('.')));

    [Fact]
    public void Chaque_decor_declare_a_son_bandeau_aux_deux_echelles()
    {
        var b = B.Value;
        int n = 0;
        foreach (var c in Fiches())
            foreach (var d in c.Decors)
            {
                var un = Illustrations.Decor(b, c.Id, d.Id, 1);
                var fin = Illustrations.Decor(b, c.Id, d.Id, 2);
                Assert.True(un is not null, Illustrations.IdDecor(c.Id, d.Id));
                Assert.Equal((Illustrations.DecorLargeur, Illustrations.DecorHauteur), (un!.W, un.H));
                Assert.True(fin!.Natif, "dessin fin natif : " + d.Id);
                Assert.Equal((un.W * 2, un.H * 2, un.Images.Count, un.Duree), (fin.W, fin.H, fin.Images.Count, fin.Duree));
                Assert.Same(fin, b.FinExact(Illustrations.IdDecor(c.Id, d.Id)));
                Assert.True(Opaque(un) && Opaque(fin), "un décor est opaque : " + d.Id);
                Assert.Equal("aucun", un.Ancre);
                n++;
            }
        Assert.True(n >= 40, $"{n} décors");
        Assert.Null(Illustrations.Decor(b, "prologue", "nulle-part"));
        Assert.Null(Illustrations.Decor(b, "prologue", ""));
    }

    [Fact]
    public void Souvenirs_vignettes_et_emblemes()
    {
        var b = B.Value;
        foreach (var c in Fiches())
        {
            foreach (var s in c.Souvenirs)
            {
                var t = Illustrations.Souvenir(b, c.Id, s.Id, 1);
                Assert.True(t is not null, Illustrations.IdSouvenir(c.Id, s.Id));
                Assert.Equal((24, 24), (t!.W, t.H));
                Assert.True(Illustrations.Souvenir(b, c.Id, s.Id)!.Natif);
            }
            Assert.Equal((32, 32), (Illustrations.Vignette(b, c.Id, 1)!.W, Illustrations.Vignette(b, c.Id, 1)!.H));
            Assert.True(Illustrations.Ton(b, c.Ton) is not null, c.Ton);
        }
        // Un emblème par ton, chacun d'une forme à lui : leurs silhouettes (pixels pleins) diffèrent deux à deux.
        var formes = new[] { "humour", "mystere", "emotion", "epique" }
            .Select(t => string.Join("|", Illustrations.Ton(b, t, 1)!.Images[0].Select(l => new string(l.Select(ch => ch == '.' ? '.' : '#').ToArray()))))
            .ToList();
        Assert.Equal(formes.Count, formes.Distinct().Count());
    }

    [Fact]
    public void Objets_exclusifs_dessines_et_portes_a_leur_emplacement()
    {
        var b = B.Value;
        var ancres = new Dictionary<string, string[]>
        {
            ["tete"] = new[] { "tete" }, ["yeux"] = new[] { "yeux" }, ["cou"] = new[] { "cou" }, ["dos"] = new[] { "cou", "corps", "main-g" },
            ["main"] = new[] { "main", "main-g" }, ["pieds"] = new[] { "pieds" }, ["compagnon"] = new[] { "cote" },
        };
        int n = 0;
        foreach (var c in Fiches())
            foreach (var o in c.Objets.Where(o => o.Portable))
            {
                var s = b[o.Id];
                Assert.True(s is not null, o.Id);
                Assert.Equal(o.Emplacement, s!.Slot);
                Assert.Contains(s.Ancre, ancres[o.Emplacement]);
                Assert.True(b.Fin(o.Id)!.Natif, "dessin fin natif : " + o.Id);
                // Le catalogue des exclusifs (Boutique.Trouver) le range au même emplacement que son sprite.
                Assert.Equal(s.Slot, Boutique.Trouver(o.Id)!.Slot);
                // Il se porte : le rendu le pose sur Pilou aux quatre stades, aux deux échelles.
                foreach (var stade in new[] { 1, 2, 3, 4 })
                {
                    var nu = RenduPilou.Rendre(new Allure { Stade = stade }, b, 2);
                    var porte = RenduPilou.Rendre(new Allure { Stade = stade, Objets = new[] { o.Id } }, b, 2);
                    Assert.False(nu.SequenceEqual(porte), $"{o.Id} invisible au stade {stade}");
                }
                n++;
            }
        Assert.True(n >= 13, $"{n} objets exclusifs");
    }
}
