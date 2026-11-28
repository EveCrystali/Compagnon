using Xunit;

namespace PilouBureau.Tests;

// Le théâtre des campagnes (docs/SCENES.md) : Theatre.cs calcule exactement ce que calcule la référence
// (outils/sprites/theatre.py, relue aussi par TheatreTest.java) — position et image de Pilou, acteurs, effets, et
// l'empreinte de l'image composée pixel à pixel.
public class TheatreTests
{
    private static readonly Lazy<Banque> B = new(() => Banque.DepuisDossier(Path.Combine(CampagnesVecteurs.Racine().FullName, "assets")));

    private static string Assets(params string[] p) => Path.Combine(new[] { CampagnesVecteurs.Racine().FullName, "assets" }.Concat(p).ToArray());

    private static Dictionary<string, Dictionary<string, Theatre.Anim>> Anims() =>
        Theatre.LireAnimations(File.ReadAllText(Assets("scenes", "animations.txt")));

    private static Theatre.Evenement Evenement(string[] p)
    {
        long t = long.Parse(p[1]);
        return p[2] is "humeur" or "perso" ? new Theatre.Evenement(t, p[2], Humeur: p[3]) : new Theatre.Evenement(t, p[2], long.Parse(p[3]), long.Parse(p[4]));
    }

    [Fact]
    public void Memes_scenes_que_la_reference()
    {
        var b = B.Value;
        var anims = Anims();
        var lignes = File.ReadAllLines(Path.Combine(CampagnesVecteurs.Racine().FullName, "outils", "sprites", "theatre-reference.txt"))
            .Where(l => l.Length > 0 && !l.StartsWith('#'));
        Theatre.Contexte? cx = null;
        Sprite? decor = null;
        uint[] teinte = Array.Empty<uint>();
        string niveau = "", nom = "";
        int regard = 0;
        var evts = new List<Theatre.Evenement>();
        int n = 0, images = 0;
        foreach (var l in lignes)
        {
            var p = l.Split(' ');
            switch (p[0])
            {
                case "scenario":
                {
                    nom = p[1];
                    var scenes = Theatre.LireScenes(File.ReadAllText(Assets("scenes", p[2] + ".txt")));
                    cx = new Theatre.Contexte(scenes[p[3]], anims, id => b.Fins.GetValueOrDefault(id));
                    decor = b.Fins.GetValueOrDefault(Illustrations.IdDecor(p[2], p[3]));
                    teinte = b.Teintes[p[4]];
                    niveau = p[5];
                    regard = int.Parse(p[6]);
                    evts = new List<Theatre.Evenement>();
                    break;
                }
                case "evenement":
                    evts.Add(Evenement(p));
                    break;
                case "pilou":
                {
                    var e = Theatre.Pilou(cx!, evts, long.Parse(p[1]), regard, niveau);
                    Assert.True((e.X, e.Y, e.Image, e.Miroir, e.Visible) ==
                        (int.Parse(p[2]), int.Parse(p[3]), int.Parse(p[4]), p[5] == "1", p[6] == "1"), $"{nom} : {l} ≠ {e}");
                    break;
                }
                case "perso":
                {
                    var q = Theatre.Perso(cx!, evts, long.Parse(p[1]), niveau);
                    var attendu = p[2] == "-" ? "-" : string.Join(" ", p.Skip(2));
                    var vu = q is { } v ? $"{v.Sprite} {v.Image} {v.X} {v.Y} {(v.Miroir ? 1 : 0)}" : "-";
                    Assert.True(attendu == vu, $"{nom} : {l} ≠ {vu}");
                    break;
                }
                case "acteurs":
                {
                    long t = long.Parse(p[1]);
                    var poses = Theatre.Acteurs(cx!, evts, t, niveau).Concat(Theatre.Effets(cx!, evts, t, niveau))
                        .Select(q => $"{q.Sprite}:{q.Image}:{q.X}:{q.Y}:{(q.Miroir ? 1 : 0)}").ToList();
                    Assert.True(string.Join(" ", poses.DefaultIfEmpty("-")) == string.Join(" ", p.Skip(2)), $"{nom} : {l}");
                    break;
                }
                case "image":
                {
                    var px = Theatre.Composer(cx!, decor, teinte, evts, long.Parse(p[1]), regard, niveau);
                    Assert.True(Theatre.Fnv(px) == uint.Parse(p[2]), $"{nom} : image à {p[1]} ms");
                    images++;
                    break;
                }
                default:
                    Assert.Fail("ligne inconnue : " + l);
                    break;
            }
            n++;
        }
        Assert.True(n > 500 && images > 50, $"{n} lignes, {images} images");
    }

    [Fact]
    public void Chaque_scene_a_son_decor_et_ses_acteurs()
    {
        var b = B.Value;
        var anims = Anims();
        Assert.True(anims.ContainsKey(Theatre.IdPilou));
        var pilou = b.Fins.GetValueOrDefault(Theatre.IdPilou);
        Assert.NotNull(pilou);
        foreach (var (_, a) in anims[Theatre.IdPilou]) Assert.True(a.Premiere + a.Nombre <= pilou!.Images.Count);
        int n = 0;
        foreach (var f in Directory.EnumerateFiles(Assets("scenes"), "*.txt").Where(f => Path.GetFileName(f) != "animations.txt"))
        {
            var campagne = Path.GetFileNameWithoutExtension(f);
            foreach (var (id, sc) in Theatre.LireScenes(File.ReadAllText(f)))
            {
                Assert.NotNull(b.Fins.GetValueOrDefault(Illustrations.IdDecor(campagne, id)));
                Assert.InRange(sc.Place, 8, Theatre.W - 8);
                Assert.InRange(sc.Sol.Y0, 30, Theatre.H);
                Assert.InRange(sc.Sol.Y1, 20, Theatre.H);
                foreach (var a in sc.Acteurs)
                {
                    Assert.NotNull(b.Fins.GetValueOrDefault(a.Sprite));
                    Assert.Contains(a.Comportement, new[] { "vol", "traverse", "rond", "saut", "pose", "flotte", "chute" });
                }
                foreach (var s in sc.Sensibles) Assert.Contains(s.Reaction, new[] { "bulle", "rond", "graines" });
                Assert.InRange(sc.Interlocuteur, 20, Theatre.W - 8);
                n++;
            }
        }
        Assert.True(n >= 6, $"{n} scènes");
    }

    [Fact]
    public void Un_clic_ne_change_que_ce_qui_le_suit()
    {
        // La scène se recalcule à chaque image depuis la liste d'événements : ajouter un clic ne doit pas modifier le
        // passé (ce que Pilou faisait avant le clic reste identique).
        var b = B.Value;
        var sc = Theatre.LireScenes(File.ReadAllText(Assets("scenes", "prologue.txt")))["mare"];
        var cx = new Theatre.Contexte(sc, Anims(), id => b.Fins.GetValueOrDefault(id));
        var evts = new List<Theatre.Evenement> { new(0, "entree") };
        var avant = Enumerable.Range(0, 40).Select(i => Theatre.Pilou(cx, evts, i * 100L)).ToList();
        evts.Add(new Theatre.Evenement(4000, "clic", 18, 70));
        var apres = Enumerable.Range(0, 40).Select(i => Theatre.Pilou(cx, evts, i * 100L)).ToList();
        Assert.Equal(avant, apres);
        Assert.NotEqual(Theatre.Pilou(cx, evts.Take(1).ToList(), 4200), Theatre.Pilou(cx, evts, 4200));
    }
}
