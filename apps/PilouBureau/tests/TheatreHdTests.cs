using System.Diagnostics;
using System.Globalization;
using Xunit;
using Xunit.Abstractions;

namespace PilouBureau.Tests;

// Le Théâtre en haute définition (docs/SCENES-HD.md) : Theatre.cs et TheatreHd.cs calculent exactement ce que calcule la
// référence (outils/sprites/theatre.py et theatre_hd.py) : décors à plans, état et pose du Pilou fin, acteurs, personnage,
// effets, et l'empreinte de l'image 480 × 240 composée pixel à pixel.
public class TheatreHdTests
{
    private readonly ITestOutputHelper _sortie;
    public TheatreHdTests(ITestOutputHelper sortie) => _sortie = sortie;

    private static readonly Lazy<Banque> B = new(() => Banque.DepuisDossier(Path.Combine(CampagnesVecteurs.Racine().FullName, "assets")));

    private static string Assets(params string[] p) => Path.Combine(new[] { CampagnesVecteurs.Racine().FullName, "assets" }.Concat(p).ToArray());

    private static Dictionary<string, Dictionary<string, Theatre.Anim>> Anims() =>
        Theatre.LireAnimations(File.ReadAllText(Assets("scenes", "animations.txt")));

    private static readonly Lazy<Dictionary<string, SpriteHd>> SpritesHd = new(() =>
        Directory.EnumerateFiles(Assets("sprites-hd"), "*.txt").Select(f => TheatreHd.LireSpriteHd(File.ReadAllText(f))).ToDictionary(s => s.Id));

    private static readonly Dictionary<string, Sprite> Silhouettes = new();

    // Ce que le moteur sait des sprites HD : taille, durée, nombre d'images (la référence : sprites-hd seuls, jamais l'ancien).
    private static Sprite? Silhouette(string id)
    {
        lock (Silhouettes)
        {
            if (Silhouettes.TryGetValue(id, out var s)) return s;
            return SpritesHd.Value.TryGetValue(id, out var h) ? Silhouettes[id] = h.VersSprite() : null;
        }
    }

    private static SpriteHd? Hd(string id) => SpritesHd.Value.GetValueOrDefault(id);

    private static Theatre.Evenement Evenement(string[] p)
    {
        long t = long.Parse(p[1]);
        return p[2] is "humeur" or "perso" ? new Theatre.Evenement(t, p[2], Humeur: p[3]) : new Theatre.Evenement(t, p[2], long.Parse(p[3]), long.Parse(p[4]));
    }

    private static string Pose(Theatre.Pose q) => $"{q.Sprite} {q.Image} {q.X} {q.Y} {(q.Miroir ? 1 : 0)}";

    [Fact]
    public void Memes_scenes_hd_que_la_reference()
    {
        var anims = Anims();
        var rendre = TheatreHd.RendeurPilou(B.Value);
        var lignes = File.ReadAllLines(Path.Combine(CampagnesVecteurs.Racine().FullName, "outils", "sprites", "theatre-hd-reference.txt"))
            .Where(l => l.Length > 0 && !l.StartsWith('#'));

        // Les décors : une ligne par plan, l'empreinte de chacune de ses images.
        var attendusDecors = new List<string>();
        foreach (var f in Directory.EnumerateFiles(Assets("decors"), "*.txt").OrderBy(f => f, StringComparer.Ordinal))
        {
            var d = TheatreHd.LireDecorHd(File.ReadAllText(f));
            foreach (var pl in d.Plans)
                attendusDecors.Add($"decor {d.Id} {pl.Nom} {d.W} {d.H} {pl.Images.Count} {pl.Duree} {string.Join(" ", pl.Images.Select(im => Theatre.Fnv(im)))}");
        }

        Theatre.Contexte? cx = null;
        DecorHd? decor = null;
        string niveau = "", nom = "";
        int regard = 0, n = 0, images = 0, decors = 0, poses = 0, acteurs = 0, persos = 0;
        var evts = new List<Theatre.Evenement>();
        Theatre.EtatPilouFin etat = default;
        long t = 0;
        var attActeurs = new List<string>();
        string? attPerso = null;
        foreach (var l in lignes)
        {
            var p = l.Split(' ');
            switch (p[0])
            {
                case "decor":
                    Assert.Contains(l, attendusDecors);
                    decors++;
                    break;
                case "scenario":
                {
                    nom = p[1];
                    var scenes = Theatre.LireScenes(File.ReadAllText(Assets("scenes-hd", p[2] + ".txt")), Theatre.Hd);
                    cx = new Theatre.Contexte(scenes[p[3]], anims, Silhouette);
                    var fd = Assets("decors", $"decor-{p[2]}-{p[3]}.txt");
                    decor = File.Exists(fd) ? TheatreHd.LireDecorHd(File.ReadAllText(fd)) : null;
                    niveau = p[4];
                    regard = int.Parse(p[5]);
                    evts = new List<Theatre.Evenement>();
                    break;
                }
                case "evenement":
                    evts.Add(Evenement(p));
                    break;
                case "pilou":
                {
                    t = long.Parse(p[1]);
                    etat = Theatre.PilouEtat(cx!, evts, t, regard, niveau);
                    Assert.True((etat.X, etat.Y, etat.Anim, etat.Dt, etat.Miroir, etat.Visible, etat.Humeur) ==
                        (int.Parse(p[2]), int.Parse(p[3]), p[4], long.Parse(p[5]), p[6] == "1", p[7] == "1", p[8]), $"{nom} : {l} ≠ {etat}");
                    attActeurs.Clear();
                    attPerso = null;
                    break;
                }
                case "pose":
                {
                    var champs = p.Skip(2).Select(c => c.Split('=')).ToDictionary(c => c[0], c => c[1]);
                    var v = Theatre.PoseHd(etat, t);
                    bool B01(string k) => champs.TryGetValue(k, out var s) && s == "1";
                    Assert.Equal(long.Parse(p[1]), t);
                    Assert.Equal(champs["expr"], v.Expr);
                    Assert.Equal(long.Parse(champs["t"]), v.T);
                    Assert.Equal(B01("marche"), v.Marche);
                    Assert.Equal(B01("parle"), v.Parle);
                    Assert.Equal(B01("cligne"), v.Cligne);
                    Assert.Equal(B01("salue"), v.Salue);
                    Assert.Equal(champs.TryGetValue("regard", out var rg) ? int.Parse(rg) : 0, v.Regard);
                    Assert.Equal(champs.TryGetValue("saut", out var sa) ? double.Parse(sa, CultureInfo.InvariantCulture) : 0.0, v.Saut);
                    foreach (var k in champs.Keys) Assert.Contains(k, new[] { "expr", "t", "marche", "parle", "cligne", "regard", "saut", "salue" });
                    poses++;
                    break;
                }
                case "acteur":
                    attActeurs.Add(string.Join(" ", p.Skip(2)));
                    acteurs++;
                    break;
                case "perso":
                    attPerso = string.Join(" ", p.Skip(2));
                    persos++;
                    break;
                case "image":
                {
                    var vus = Theatre.Acteurs(cx!, evts, t, niveau).Concat(Theatre.Effets(cx!, evts, t, niveau)).Select(Pose).ToList();
                    Assert.True(attActeurs.SequenceEqual(vus), $"{nom} à {t} ms : acteurs {string.Join(" | ", vus)} ≠ {string.Join(" | ", attActeurs)}");
                    var pe = Theatre.Perso(cx!, evts, t, niveau);
                    Assert.True((pe is { } q ? Pose(q) : null) == attPerso, $"{nom} à {t} ms : personnage");
                    var px = TheatreHd.ComposerHd(decor, cx!, Hd, evts, long.Parse(p[1]), rendre, regard, niveau);
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
        Assert.Equal(attendusDecors.Count, decors);
        Assert.True(images >= 28 && poses == images && decors >= 6 && acteurs > 0 && persos > 0, $"{n} lignes, {images} images, {acteurs} acteurs, {persos} personnages");
    }

    [Fact]
    public void L_ancienne_definition_ne_change_pas()
    {
        var sc = Theatre.LireScenes(File.ReadAllText(Assets("scenes", "prologue.txt")))["mare"];
        Assert.Equal((192, 80), (sc.D.W, sc.D.H));
        Assert.Equal(7, Theatre.E(sc, 7));
        var hd = Theatre.LireScenes(File.ReadAllText(Assets("scenes-hd", "prologue.txt")), Theatre.Hd)["mare"];
        Assert.Equal((480, 240), (hd.D.W, hd.D.H));
        Assert.Equal(17, Theatre.E(hd, 7));
        Assert.Equal(-35, Theatre.E(hd, -14));
    }

    [Fact]
    public void Mesure_decor_et_composition()
    {
        var anims = Anims();
        var b = B.Value;
        var fichier = Assets("decors", "decor-prologue-mare.txt");
        var texte = File.ReadAllText(fichier);

        long d0 = Stopwatch.GetTimestamp();
        var decor = TheatreHd.LireDecorHd(texte);
        double premier = Stopwatch.GetElapsedTime(d0).TotalMilliseconds;
        d0 = Stopwatch.GetTimestamp();
        for (int i = 0; i < 5; i++) TheatreHd.LireDecorHd(texte);
        double chauffe = Stopwatch.GetElapsedTime(d0).TotalMilliseconds / 5;
        _sortie.WriteLine($"MESURE chargement du décor HD (mare, {decor.Plans.Count} plans, {decor.Plans.Sum(p => p.Images.Count)} images, {new FileInfo(fichier).Length / 1024} Ko) : 1re fois {premier:0.0} ms, ensuite {chauffe:0.0} ms");

        var sc = Theatre.LireScenes(File.ReadAllText(Assets("scenes-hd", "prologue.txt")), Theatre.Hd)["mare"];
        var cx = new Theatre.Contexte(sc, anims, Silhouette);
        var evts = new List<Theatre.Evenement> { new(0, "entree"), new(3000, "parle", 9000), new(5000, "clic", 187, 215) };
        var rendre = TheatreHd.RendeurPilou(b);
        var sortie = new uint[480 * 240];
        foreach (var cache in new[] { true, false })
        {
            TheatreHd.CacheFonds = cache;
            for (int i = 0; i < 40; i++) TheatreHd.ComposerHd(decor, cx, Hd, evts, i * 83, rendre, 0, "completes", sortie);
            long t0 = Stopwatch.GetTimestamp();
            for (int i = 0; i < 120; i++) TheatreHd.ComposerHd(decor, cx, Hd, evts, 8000 + i * 83, rendre, 0, "completes", sortie);
            _sortie.WriteLine($"MESURE ComposerHd 480 × 240, cache des plans fond {(cache ? "avec" : "sans")} : {Stopwatch.GetElapsedTime(t0).TotalMilliseconds / 120:0.00} ms par image (120 images)");
        }
        TheatreHd.CacheFonds = true;

        // Pour comparaison : le Pilou fin seul, puis l'ancien compositeur sur la mare 192 × 80.
        var pose = new PoseHd("repos", 0, false, false, false, 0, 0.0, false);
        long t1 = Stopwatch.GetTimestamp();
        for (int i = 0; i < 120; i++) rendre(pose with { T = i * 83 });
        _sortie.WriteLine($"MESURE rendu du Pilou fin seul (96 × 112) : {Stopwatch.GetElapsedTime(t1).TotalMilliseconds / 120:0.00} ms par image");

        var ancien = Theatre.LireScenes(File.ReadAllText(Assets("scenes", "prologue.txt")))["mare"];
        var cxA = new Theatre.Contexte(ancien, anims, id => b.Fins.GetValueOrDefault(id));
        var decorA = b.Fins.GetValueOrDefault(Illustrations.IdDecor("prologue", "mare"));
        var teinte = b.Teintes["bleu"];
        var px = new uint[Theatre.W * Theatre.H];
        for (int i = 0; i < 40; i++) Theatre.Composer(cxA, decorA, teinte, evts, i * 83, 0, "completes", px);
        long t2 = Stopwatch.GetTimestamp();
        for (int i = 0; i < 120; i++) Theatre.Composer(cxA, decorA, teinte, evts, 8000 + i * 83, 0, "completes", px);
        _sortie.WriteLine($"MESURE ancien Composer 192 × 80 (mare) : {Stopwatch.GetElapsedTime(t2).TotalMilliseconds / 120:0.00} ms par image (120 images)");
    }
}
