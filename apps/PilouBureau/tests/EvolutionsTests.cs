using System.Globalization;
using PilouBureau;
using Xunit;

// Les scènes d'évolution : mêmes répliques que la référence (outils/sprites/evolutions-reference.txt), rejouée aussi par
// EvolutionsTest.java sur Android.
public class EvolutionsTests
{
    private static string Racine(params string[] p) => Path.Combine(new[] { CampagnesVecteurs.Racine().FullName }.Concat(p).ToArray());

    private static SortedDictionary<int, Evolutions.Scene> Scenes() => Evolutions.Lire(File.ReadAllText(Racine("assets", "evolutions.txt")));

    [Fact]
    public void Memes_repliques_que_la_reference()
    {
        var scenes = Scenes();
        var attendu = File.ReadAllLines(Racine("outils", "sprites", "evolutions-reference.txt")).Where(l => !l.StartsWith('#')).ToList();
        var obtenu = new List<string>();
        foreach (var (stade, sc) in scenes)
        {
            obtenu.Add($"scene {stade} {sc.Decor} | {sc.Titre} | {sc.Question} | {(sc.Musique == "" ? "-" : sc.Musique)}");
            foreach (var (id, lib) in sc.Options) obtenu.Add($"option {id} {lib}");
            foreach (var v in new[] { "calin", "espiegle", "autre" })
            foreach (var choix in new string?[] { null }.Concat(sc.Options.Select(o => o.Id)))
            {
                var d = Evolutions.Deroule(sc, v, choix);
                obtenu.Add(string.Create(CultureInfo.InvariantCulture, $"deroule {stade} {v} {choix ?? "-"} {d.Count}"));
                foreach (var r in d)
                    obtenu.Add(string.Create(CultureInfo.InvariantCulture, $"  {(r.Humeur == "" ? "-" : r.Humeur)} {Evolutions.MsEcriture(r.Texte)} {r.Texte}"));
            }
        }
        Assert.Equal(attendu.Count, obtenu.Count);
        for (int i = 0; i < attendu.Count; i++) Assert.Equal(attendu[i], obtenu[i]);
    }

    [Fact]
    public void Trois_scenes_un_choix_qui_compte_et_une_fin_heureuse()
    {
        var scenes = Scenes();
        Assert.Equal(new[] { 2, 3, 4 }, scenes.Keys.ToArray());
        var theatre = Theatre.LireScenes(File.ReadAllText(Racine("assets", "scenes", "evolution.txt")));
        foreach (var (_, sc) in scenes)
        {
            Assert.NotEqual("", sc.Titre);
            Assert.True(theatre.ContainsKey(sc.Decor), sc.Decor);
            Assert.Equal(3, sc.Options.Count);
            foreach (var v in Evolutions.Variantes)
            {
                // Jusqu'à la question (incluse, sans humeur) ; puis la réplique du choix et la fin, toujours heureuse.
                var avant = Evolutions.Deroule(sc, v, null);
                Assert.Equal("", avant[^1].Humeur);
                foreach (var (id, _) in sc.Options)
                {
                    var d = Evolutions.Deroule(sc, v, id);
                    Assert.Equal("joie", d[^1].Humeur);
                    Assert.Equal(avant.Count + 1, d.Count);
                    Assert.All(d, r => Assert.Contains(r.Humeur, Theatre.Humeurs));
                }
            }
            // La variante câline ou espiègle se dit dans la scène : une réplique les distingue.
            Assert.NotEqual(Evolutions.Deroule(sc, "calin", null)[2].Texte, Evolutions.Deroule(sc, "espiegle", null)[2].Texte);
        }
        Assert.Equal("calin", Evolutions.Variante(null));
        Assert.Equal("", Evolutions.Garde(scenes[2], "inconnu"));
        Assert.Equal("Le petit « ploc » quand il saute", Evolutions.Garde(scenes[2], "ploc"));
    }
}
