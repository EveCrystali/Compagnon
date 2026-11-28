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
    public void Le_panneau_des_choix_evite_l_accessoire_et_le_personnage()
    {
        // Le hall des Pas Comptés : l'afficheur « 1337 » est l'objet même de la scène ; Grumeau se tient à droite.
        var scenes = Theatre.LireScenes(File.ReadAllText(Assets("scenes", "grande-panne.txt")));
        int n = 0;
        foreach (var (_, sc) in scenes)
        foreach (var (w, h) in new[] { (104, 46), (90, 30), (120, 58) })
        {
            var (x, y) = Theatre.PlacerPanneau(sc, w, h, sc.Place, true);
            Assert.InRange(x, 0, Theatre.W - Math.Min(w, Theatre.W - 4));
            Assert.InRange(y, 9, Theatre.H);
            // S'il existe une place qui ne touche pas l'accessoire, le panneau la prend.
            if (sc.Cle is { } c)
            {
                bool possible = c.X0 - 2 >= w + 2 || Theatre.W - c.X1 - 2 >= w + 2 || c.Y1 <= Theatre.H - h - 2 || c.Y0 >= 9 + h;
                if (possible) Assert.False(x < c.X1 && x + w > c.X0 && y < c.Y1 && y + h > c.Y0, $"{sc.Nom} : le panneau couvre l'accessoire");
            }
            n++;
        }
        var hall = scenes["hall-pas-comptes"];
        var (hx, _) = Theatre.PlacerPanneau(hall, 104, 46, hall.Place, true);
        Assert.True(hx + 104 <= hall.Interlocuteur - 12 || hx >= hall.Interlocuteur + 12, "le panneau couvre Grumeau");
        Assert.True(n >= 30);
    }

    [Fact]
    public void Le_panneau_ne_couvre_ni_la_legende_ni_les_boutons_ni_un_humain_en_pied()
    {
        // Avec la légende du lieu (en haut à gauche) et les boutons (en haut à droite) comme obstacles, le panneau peut
        // monter jusqu'en haut, entre les deux ; un humain en pied (24 × 44) est plus grand qu'un personnage-objet.
        var gene = new List<(int, int, int, int)> { (1, 1, 60, 12), (158, 1, 192, 10) };
        foreach (var f in new[] { "grande-panne.txt", "phare-eteint.txt", "petit-nuage.txt" })
        foreach (var (_, sc) in Theatre.LireScenes(File.ReadAllText(Assets("scenes", f))))
        {
            var (x, y) = Theatre.PlacerPanneau(sc, 84, 30, sc.Place, true, (24, 44), gene);
            foreach (var (x0, y0, x1, y1) in gene)
                Assert.False(x < x1 && x + 84 > x0 && y < y1 && y + 30 > y0, $"{sc.Nom} : le panneau couvre l'interface");
        }
        var auberge = Theatre.LireScenes(File.ReadAllText(Assets("scenes", "phare-eteint.txt")))["auberge-bigorneau"];
        var (ax, ay) = Theatre.PlacerPanneau(auberge, 84, 30, auberge.Place, true, (24, 44), gene);
        var c = auberge.Cle!.Value;
        Assert.False(ax < c.X1 && ax + 84 > c.X0 && ay < c.Y1 && ay + 30 > c.Y0, "le panneau couvre l'horloge");
        int sp = Theatre.Sol(auberge, auberge.Interlocuteur);
        Assert.False(ax < auberge.Interlocuteur + 13 && ax + 84 > auberge.Interlocuteur - 13 && ay + 30 > sp - 44, "le panneau couvre Perrine");
    }

    [Fact]
    public void Petit_Nuage_sans_alpha_lisse()
    {
        // Petit Nuage : nuages, brume, vapeur et personnages n'ont aucune couleur semi-transparente ; le léger se dit en
        // trame (un pixel sur deux), comme dans les décors. Palette : #RRGGBB ou #RRGGBBAA.
        var b = B.Value;
        var sc = Theatre.LireScenes(File.ReadAllText(Assets("scenes", "petit-nuage.txt")));
        var ids = sc.Values.SelectMany(s => s.Acteurs).Select(a => a.Sprite)
            .Concat(b.Fins.Keys.Where(k => k.StartsWith("pied-petit-nuage-", StringComparison.Ordinal))).Distinct().ToList();
        Assert.True(ids.Count >= 15, $"{ids.Count} sprites");
        foreach (var id in ids)
        foreach (var (k, v) in b.Fins[id].Palette)
            Assert.True(v.Length != 9 || v.EndsWith("ff", StringComparison.OrdinalIgnoreCase), $"{id} : {k}={v} est semi-transparent");
        Assert.Equal(14, sc.Count);
    }

    [Fact]
    public void Aucun_acteur_hors_de_sa_zone()
    {
        // Chaque acteur, à chaque instant, reste dans la scène et dans sa zone (un vol dans sa boîte, une traversée
        // entre ses deux hauteurs, ce qui est posé sur l'eau ou le sol à sa place) : pas d'élément qui flotte n'importe où.
        var b = B.Value;
        var anims = Anims();
        foreach (var f in Directory.EnumerateFiles(Assets("scenes"), "*.txt").Where(f => Path.GetFileName(f) != "animations.txt"))
        foreach (var (_, sc) in Theatre.LireScenes(File.ReadAllText(f)))
        {
            var cx = new Theatre.Contexte(sc, anims, id => b.Fins.GetValueOrDefault(id));
            var evts = new List<Theatre.Evenement>();
            for (long t = 0; t < 30000; t += 97)
                foreach (var q in Theatre.Acteurs(cx, evts, t))
                {
                    Assert.InRange(q.Y, -10, Theatre.H + 4);
                    // Deux acteurs peuvent partager un sprite : la pose doit tenir dans la zone d'au moins l'un d'eux.
                    Assert.True(sc.Acteurs.Any(a => a.Sprite == q.Sprite && Dans(a, q)), $"{sc.Nom} : {q} hors de sa zone");
                }
        }

        static bool Dans(Theatre.Acteur a, Theatre.Pose q) => a.Comportement switch
        {
            "vol" => q.X >= a.P[0] - 2 && q.X <= a.P[2] + 2 && q.Y >= a.P[1] - 2 && q.Y <= a.P[3] + 2,
            "traverse" => q.Y >= a.P[0] - 2 && q.Y <= a.P[1] + 2,
            "rond" or "pose" => q.X == a.P[0] && q.Y == a.P[1],
            "saut" => q.X >= a.P[0] && q.X <= a.P[0] + 20 && q.Y <= a.P[1] && q.Y >= a.P[1] - 13,
            "chute" => q.Y >= a.P[1] && Math.Abs(q.X - a.P[0]) <= 4,
            "flotte" => true,
            _ => false,
        };
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
