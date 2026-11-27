using Xunit;

namespace PilouBureau.Tests;

// Animations des campagnes (docs/SPRITES.md) : les règles communes relues dans outils/sprites/animations-reference.txt
// (écrit par outils/sprites/animations.py, relu aussi par AnimationsTest.java), les décors animés et les portraits.
public class AnimationsCampagneTests
{
    private static readonly Lazy<Banque> B = new(() => Banque.DepuisDossier(Path.Combine(CampagnesVecteurs.Racine().FullName, "assets")));

    private static string[] Lignes() =>
        File.ReadAllLines(Path.Combine(CampagnesVecteurs.Racine().FullName, "outils", "sprites", "animations-reference.txt"))
            .Where(l => l.Length > 0 && !l.StartsWith('#')).ToArray();

    [Fact]
    public void Memes_regles_que_la_reference()
    {
        var textes = new Dictionary<int, string>();
        int n = 0;
        foreach (var l in Lignes())
        {
            var p = l.Split(' ');
            switch (p[0])
            {
                case "niveau":
                    Assert.Equal(p[3], AnimationsCampagne.Niveau(p[1], p[2] == "1"));
                    break;
                case "decor":
                    Assert.Equal(long.Parse(p[5]), AnimationsCampagne.ImageDecor(int.Parse(p[1]), int.Parse(p[2]), long.Parse(p[3]), p[4]));
                    break;
                case "portrait":
                    Assert.True(int.Parse(p[6]) == AnimationsCampagne.ImagePortrait(int.Parse(p[1]), long.Parse(p[3]), p[4] == "1", p[5]), l);
                    break;
                case "texte":
                    textes[int.Parse(p[1])] = l.Length > 7 + p[1].Length ? l[(7 + p[1].Length)..] : "";
                    break;
                case "ecriture":
                {
                    var t = textes[int.Parse(p[1])];
                    Assert.Equal((long.Parse(p[2]), int.Parse(p[3])), (AnimationsCampagne.DureeEcriture(t), AnimationsCampagne.Attente(t)));
                    break;
                }
                case "lettres":
                    Assert.True(int.Parse(p[3]) == AnimationsCampagne.Lettres(textes[int.Parse(p[1])], long.Parse(p[2])), l);
                    break;
                case "volet":
                {
                    int by = int.Parse(p[1]);
                    for (int bx = 0; bx < 12; bx++) Assert.Equal(int.Parse(p[2 + bx]), AnimationsCampagne.OrdreVolet(bx, by, 12));
                    break;
                }
                case "fond":
                    Assert.Equal((p[3], p[4], p[5]), AnimationsCampagne.TeintesFond(p[1], int.Parse(p[2])));
                    break;
                case "particule":
                    Assert.True((int.Parse(p[4]), int.Parse(p[5]), int.Parse(p[6])) == AnimationsCampagne.ParticuleFond(p[1], int.Parse(p[2]), long.Parse(p[3])), l);
                    break;
                case "recompense":
                    for (int i = 1; i < p.Length; i++) Assert.Equal(int.Parse(p[i]), AnimationsCampagne.DelaiRecompense(i - 1));
                    break;
                default:
                    Assert.Fail("ligne inconnue : " + l);
                    break;
            }
            n++;
        }
        Assert.True(n > 500, $"{n} lignes");
    }

    [Fact]
    public void Chaque_decor_s_anime_en_boucle_sobre()
    {
        var b = B.Value;
        int n = 0;
        foreach (var (id, s) in b.Sprites.Where(kv => kv.Key.StartsWith("decor-", StringComparison.Ordinal)))
        {
            Assert.InRange(s.Images.Count, 4, 8);
            Assert.InRange(s.Duree, 125, 250);                  // 4 à 8 images par seconde
            var fin = b.Fin(id)!;
            Assert.Equal((s.Images.Count, s.Duree), (fin.Images.Count, fin.Duree));
            Assert.True(s.Palette.Count <= 62 && fin.Palette.Count <= 62, id);
            // Une boucle qui bouge, sans à-coup : chaque image diffère un peu de la suivante, jamais de tout.
            int total = fin.W * fin.H, change = 0;
            for (int k = 0; k < fin.Images.Count; k++)
            {
                var a = fin.Images[k];
                var c = fin.Images[(k + 1) % fin.Images.Count];
                int d = 0;
                for (int y = 0; y < a.Length; y++)
                for (int x = 0; x < a[y].Length; x++)
                    if (a[y][x] != c[y][x] && fin.Palette[a[y][x]] != fin.Palette[c[y][x]]) d++;
                Assert.True(d < total / 8, $"{id} : l'image {k} change {d} pixels sur {total}");
                change += d;
            }
            Assert.True(change > 0, id + " ne bouge pas");
            n++;
        }
        Assert.True(n >= 46, $"{n} décors");
    }

    [Fact]
    public void Chaque_personnage_des_campagnes_a_son_portrait_anime()
    {
        var b = B.Value;
        var racine = Path.Combine(CampagnesVecteurs.Racine().FullName, "assets", "campagnes");
        int noeuds = 0;
        foreach (var d in Directory.GetDirectories(racine))
        {
            var fiche = Path.Combine(d, "campagne.json");
            if (!File.Exists(fiche)) continue;
            var c = Campagnes.Lire(File.ReadAllText(fiche), f => File.Exists(Path.Combine(d, f)) ? File.ReadAllText(Path.Combine(d, f)) : null)!;
            foreach (var n in c.Noeuds.Values.Where(n => n.Personnage != ""))
            {
                var un = AnimationsCampagne.Portrait(b, c.Id, n.Personnage, n.Expression, 1);
                var fin = AnimationsCampagne.Portrait(b, c.Id, n.Personnage, n.Expression, 2);
                Assert.True(un is not null && fin is not null, $"{c.Id} {n.Id} : {n.Personnage}");
                Assert.Equal((32, 32, 5), (un!.W, un.H, un.Images.Count));
                Assert.Equal((64, 64, 5), (fin!.W, fin.H, fin.Images.Count));
                Assert.True(fin.Natif);
                noeuds++;
            }
        }
        Assert.True(noeuds > 100, $"{noeuds} nœuds avec un personnage");
        // Une expression non dessinée retombe sur le visage neutre ; un inconnu ne montre rien.
        Assert.Equal("portrait-phare-eteint-vernier", AnimationsCampagne.Portrait(b, "phare-eteint", "vernier", "colere", 1)!.Id);
        Assert.Null(AnimationsCampagne.Portrait(b, "phare-eteint", "personne", "", 2));
        Assert.Null(AnimationsCampagne.Portrait(b, "phare-eteint", "", "joie", 2));
    }

    [Fact]
    public void Lettre_a_lettre_puis_tout()
    {
        const string t = "Coucou. Ça va ?";
        Assert.Equal(0, AnimationsCampagne.Lettres(t, 0));
        Assert.True(AnimationsCampagne.Lettres(t, 100) is > 0 and < 15);
        Assert.Equal(t.Length, AnimationsCampagne.Lettres(t, AnimationsCampagne.DureeEcriture(t)));
        Assert.Equal("aucune", AnimationsCampagne.Niveau("completes", false));
        Assert.Equal("completes", AnimationsCampagne.Niveau("n'importe quoi", true));
    }
}
