using System.Globalization;
using System.Security.Cryptography;
using PilouBureau;
using Xunit;

// Le rendu C# tombe sur les mêmes pixels que le rendu de référence (outils/sprites/rendu.py) et que le téléphone.
public class RenduTests
{
    private static string Racine()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d is not null && !File.Exists(Path.Combine(d.FullName, "assets", "index.txt"))) d = d.Parent;
        Assert.NotNull(d);
        return d!.FullName;
    }

    private static readonly Lazy<Banque> B = new(() => Banque.DepuisDossier(Path.Combine(Racine(), "assets")));

    private static Allure Lire(string ligne)
    {
        var a = new Allure();
        foreach (var paire in ligne.Split(' ', StringSplitOptions.RemoveEmptyEntries))
        {
            var kv = paire.Split('=', 2);
            string k = kv[0], v = kv[1];
            double D() => double.Parse(v, CultureInfo.InvariantCulture);
            switch (k)
            {
                case "expr": a.Expr = v; break;
                case "couleur": a.Couleur = v; break;
                case "accessoire": a.Accessoire = v; break;
                case "tenue": a.Tenue = v; break;
                case "reaction": a.Reaction = v; break;
                case "objets": a.Objets = v.Split(','); break;
                case "cligne": a.Cligne = v == "1"; break;
                case "clin": a.Clin = v == "1"; break;
                case "marche": a.Marche = v == "1"; break;
                case "course": a.Course = v == "1"; break;
                case "baille": a.Baille = v == "1"; break;
                case "etourdi": a.Etourdi = v == "1"; break;
                case "fatigue": a.Fatigue = v == "1"; break;
                case "boude": a.Boude = v == "1"; break;
                case "dos": a.Dos = v == "1"; break;
                case "regard": a.Regard = int.Parse(v); break;
                case "regard_y": a.RegardY = int.Parse(v); break;
                case "stade": a.Stade = int.Parse(v); break;
                case "t": a.T = D(); break;
                case "saut": a.Saut = D(); break;
                case "chute": a.Chute = D(); break;
                case "assis": a.Assis = D(); break;
                case "suspendu": a.Suspendu = D(); break;
                case "tremble": a.Tremble = D(); break;
                case "evolution": a.Evolution = D(); break;
                default: throw new ArgumentException(k);
            }
        }
        return a;
    }

    private static string Empreinte(uint[] g)
    {
        var octets = new byte[g.Length * 4];
        for (int i = 0; i < g.Length; i++)
        {
            octets[i * 4] = (byte)(g[i] >> 24);
            octets[i * 4 + 1] = (byte)(g[i] >> 16);
            octets[i * 4 + 2] = (byte)(g[i] >> 8);
            octets[i * 4 + 3] = (byte)g[i];
        }
        return Convert.ToHexString(SHA256.HashData(octets)).ToLowerInvariant();
    }

    private static List<string> Reference(string fichier) =>
        File.ReadAllLines(Path.Combine(Racine(), "outils", "sprites", fichier)).Where(l => !l.StartsWith('#') && l.Trim() != "").ToList();

    private static List<string> Ecarts(string fichier, int echelle)
    {
        var lignes = Reference(fichier);
        Assert.True(lignes.Count >= 80);
        return lignes.Where(l =>
        {
            var p = l.Split('|');
            return Empreinte(RenduPilou.Rendre(Lire(p[0]), B.Value, echelle)) != p[1].Trim();
        }).Select(l => l.Split('|')[0].Trim()).ToList();
    }

    [Fact]
    public void Memes_pixels_que_la_reference() => Assert.Empty(Ecarts("rendus-reference.txt", 1));

    // Rendu fin (grille 96 × 112) : mêmes pixels que rendu.py à l'échelle 2 et que le téléphone.
    [Fact]
    public void Rendu_fin_memes_pixels_que_la_reference() => Assert.Empty(Ecarts("rendus-reference-2x.txt", 2));

    // L'agrandissement automatique d'un sprite 1× donne les mêmes lettres que rendu.agrandir, sprite par sprite.
    [Fact]
    public void Agrandissement_identique_a_la_reference()
    {
        var b = B.Value;
        var lignes = Reference("agrandis-reference.txt");
        Assert.Equal(b.Sprites.Count, lignes.Count);
        var ecarts = lignes.Where(l =>
        {
            var p = l.Split('|');
            var g = b[p[0].Trim()]!.Agrandi();
            string texte = string.Join("\n---\n", g.Images.Select(im => string.Join("\n", im)));
            return Convert.ToHexString(SHA256.HashData(System.Text.Encoding.UTF8.GetBytes(texte))).ToLowerInvariant() != p[1].Trim();
        }).Select(l => l.Split('|')[0].Trim()).ToList();
        Assert.Empty(ecarts);
    }

    // Sans flou ni nouvelle couleur : un sprite agrandi garde sa palette, double sa taille et ses ancrages.
    [Fact]
    public void Agrandissement_sans_nouvelle_couleur()
    {
        foreach (var s in B.Value.Sprites.Values)
        {
            var g = s.Agrandi();
            Assert.False(g.Natif);
            Assert.Equal((s.W * 2, s.H * 2, s.Dx * 2, s.Dy * 2, s.Images.Count), (g.W, g.H, g.Dx, g.Dy, g.Images.Count));
            for (int k = 0; k < s.Images.Count; k++)
            {
                var avant = s.Images[k].SelectMany(l => l).ToHashSet();
                avant.Add('.');
                Assert.All(g.Images[k], l => Assert.All(l, ch => Assert.Contains(ch, avant)));
            }
        }
    }

    // Les sprites redessinés en fin gardent l'emplacement, l'ancre et l'animation du sprite 1× (ancrages × 2).
    [Fact]
    public void Sprites_fins_coherents_avec_le_1x()
    {
        var b = B.Value;
        Assert.True(b.Fins.Count >= 100, $"{b.Fins.Count} sprites fins");
        var index = File.ReadAllLines(Path.Combine(Racine(), "assets", "index2x.txt")).Where(l => !l.StartsWith('#') && l.Trim() != "").ToList();
        Assert.Equal(b.Fins.Keys.OrderBy(k => k, StringComparer.Ordinal), index.OrderBy(k => k, StringComparer.Ordinal));
        foreach (var (id, f) in b.Fins)
        {
            var s = b[id];
            Assert.True(s is not null, id + " : pas de sprite 1×");
            Assert.True(f.Natif, id);
            Assert.Equal((s!.Slot, s.Ancre, s.Derriere, s.Coiffe, s.Duree, s.Images.Count), (f.Slot, f.Ancre, f.Derriere, f.Coiffe, f.Duree, f.Images.Count));
            Assert.True(Math.Abs(f.Dx - s.Dx * 2) <= 2 && Math.Abs(f.Dy - s.Dy * 2) <= 2, $"{id} : ancrage {f.Dx} {f.Dy} au lieu de {s.Dx * 2} {s.Dy * 2}");
            Assert.True(Math.Abs(f.W - s.W * 2) <= 4 && Math.Abs(f.H - s.H * 2) <= 4, $"{id} : taille {f.W} × {f.H}");
            foreach (var im in f.Images)
            foreach (var l in im)
                Assert.All(l.Where(ch => ch != '.'), ch => Assert.True(f.Palette.ContainsKey(ch), $"{id} : lettre {ch} sans couleur"));
        }
        Assert.Same(b.Fin("oeil-ouvert"), b.Fins["oeil-ouvert"]);
        Assert.Same(b.Fin("po"), b.Fin("po"));          // agrandi une seule fois
        Assert.Null(b.Fin("n-existe-pas"));
    }

    // Humeurs et tenues de voyage des campagnes : tout ce qu'il faut est dans la banque, aux deux échelles.
    [Fact]
    public void Humeurs_et_voyages_des_campagnes()
    {
        var b = B.Value;
        foreach (var h in new[] { "joie", "peur", "triste", "surpris", "determine", "fatigue", "tendre", "colere", "malice", "neutre" })
        {
            Assert.True(b["bouche-" + h] is not null && b.Fins.ContainsKey("bouche-" + h), "bouche-" + h);
            var repos = RenduPilou.Rendre(new Allure(), b);
            Assert.NotEqual(Empreinte(repos), Empreinte(RenduPilou.Rendre(new Allure { Expr = h }, b)));
        }
        foreach (var o in new[] { "peur", "triste", "surpris", "determine", "tendre", "colere", "malice", "malice-d" })
            Assert.True(b["oeil-" + o] is not null && b.Fins.ContainsKey("oeil-" + o), "oeil-" + o);
        foreach (var mode in RenduPilou.Voyages)
        {
            Assert.True(b.Tenues.ContainsKey("voyage-" + mode), mode);
            var a = new Allure { Tenue = "voyage-" + mode, T = 400 };
            Assert.NotEqual(Empreinte(RenduPilou.Rendre(new Allure { T = 400 }, b)), Empreinte(RenduPilou.Rendre(a, b)));
            Assert.Equal(96 * 112, RenduPilou.Rendre(a, b, 2).Length);
            Assert.Equal("repos", a.Expr);   // l'allure donnée n'est pas modifiée
        }
        Assert.True(RenduPilou.Voyager(new Allure { Tenue = "voyage-marche" }).Marche);
        Assert.Equal("dort", RenduPilou.Voyager(new Allure { Tenue = "voyage-nuit" }).Expr);
    }

    // Temps de rendu d'une image (Pilou équipé, animé), aux deux échelles : le rendu fin reste très en dessous de la
    // durée d'une image (33 ms à 30 images par seconde). Les temps mesurés sont écrits dans la sortie du test.
    [Fact]
    public void Rendu_fin_assez_rapide()
    {
        var b = B.Value;
        var a = Lire("expr=repos objets=chapeau-explorateur,lunettes-rondes,sac-a-dos,parapluie,oiseau");
        var tampon = new TamponRendu();
        var temps = new double[3];
        for (int e = 1; e <= 2; e++)
        {
            for (int i = 0; i < 60; i++) RenduPilou.Rendre(a, b, out _, null, e, tampon);   // échauffement
            const int n = 300;
            long debut = System.Diagnostics.Stopwatch.GetTimestamp();
            for (int i = 0; i < n; i++)
            {
                a.T = i * 33;
                RenduPilou.Rendre(a, b, out _, null, e, tampon);
            }
            temps[e] = System.Diagnostics.Stopwatch.GetElapsedTime(debut).TotalMilliseconds / n;
        }
        Console.WriteLine($"RENDU-TEMPS échelle 1 : {temps[1] * 1000:0} µs par image ; échelle 2 : {temps[2] * 1000:0} µs par image");
        Assert.True(temps[2] < 5, $"rendu fin : {temps[2]:0.00} ms par image");
    }

    // Le tampon réutilisé donne les mêmes pixels, et la géométrie reste en pixels de la grille 48 × 56.
    [Fact]
    public void Rendu_fin_tampon_et_geometrie()
    {
        var b = B.Value;
        var tampon = new TamponRendu();
        foreach (var l in Reference("rendus-reference-2x.txt").Take(30))
        {
            var p = l.Split('|');
            var g = RenduPilou.Rendre(Lire(p[0]), b, out var geo2, null, 2, tampon);
            Assert.Equal(p[1].Trim(), Empreinte(g));
            RenduPilou.Rendre(Lire(p[0]), b, out var geo1);
            Assert.Equal(geo1.Cx, geo2.Cx, 6);
            Assert.Equal(geo1.Ry, geo2.Ry, 6);
            Assert.InRange(geo2.Sommet - geo1.Sommet, -1, 1);
            Assert.InRange(geo2.Pied - geo1.Pied, -1, 1);
        }
    }

    [Fact]
    public void Banque_complete_et_coherente()
    {
        var b = B.Value;
        foreach (var id in new[]
                 {
                     "oeil-ouvert", "bouche-repos", "etincelle-roue", "acc-bonnet", "acc-chapeaupeche", "acc-etoilemer", "tenue-code-lunettes",
                     "chapeau-pirate", "haut-de-forme", "petit-chat", "petit-poisson-bocal", "trainee-coeurs", "aura", "po", "po-tourne",
                     "coffre-quete", "parchemin-quete", "marmite", "feu", "plat-invente", "plat-rate", "etoile", "bulle", "main", "ballon",
                     "canne", "bouchon", "bug-scarabee", "bug-prod", "astral-cape", "oeil-serein", "oeil-ouvert-g",
                 })
            Assert.True(b[id] is not null, id);
        foreach (var accessoire in Enum.GetValues<Accessoire>().Where(a => a is not Accessoire.Saison and not Accessoire.Aucun))
            Assert.True(b["acc-" + accessoire.ToString().ToLowerInvariant()] is not null, accessoire.ToString());
        foreach (var (tenue, ids) in b.Tenues)
        foreach (var id in ids)
            Assert.True(b[id] is not null, $"{tenue} → {id}");
        Assert.Equal(13 + RenduPilou.Voyages.Length, b.Tenues.Count);
        foreach (var p in Butin.Prises) Assert.True(b["prise-" + p.Id] is not null, p.Id);
        foreach (var r in Butin.Recettes) Assert.True(b[b.Plat(r.Id, false)] is not null, r.Id);
        foreach (var c in Enum.GetValues<Couleur>()) Assert.True(b.Teintes.ContainsKey(c.ToString().ToLowerInvariant()), c.ToString());
        foreach (var c in new[] { "lavande", "corail-orange", "ardoise", "sable", "glacier" }) Assert.True(b.Teintes.ContainsKey(c), c);
        foreach (var s in b.Sprites.Values)
        {
            Assert.True(s.H > 0, s.Id);
            Assert.All(s.Images, im => Assert.Equal(s.H, im.Length));
            foreach (var im in s.Images)
            foreach (var l in im)
                Assert.All(l.Where(ch => ch != '.'), ch => Assert.True(s.Palette.ContainsKey(ch), $"{s.Id} : lettre {ch} sans couleur"));
        }
    }

    [Fact]
    public void Inconnus_ignores_sans_planter()
    {
        var a = Lire("expr=repos t=0 objets=n-existe-pas tenue=inconnue accessoire=rien stade=9");
        Assert.Equal(RenduPilou.W * RenduPilou.H, RenduPilou.Rendre(a, B.Value).Length);
        Assert.Equal(RenduPilou.W * RenduPilou.H, RenduPilou.Rendre(new Allure(), new Banque()).Length);
        Assert.Equal(RenduPilou.W * RenduPilou.H * 4, RenduPilou.Rendre(a, B.Value, 2).Length);
        Assert.Equal(RenduPilou.W * RenduPilou.H * 4, RenduPilou.Rendre(new Allure { Tenue = "voyage-inconnu" }, new Banque(), 2).Length);
    }

    [Fact]
    public void Chaque_stade_a_sa_taille()
    {
        int Largeur(int stade)
        {
            var g = RenduPilou.Rendre(new Allure { Stade = stade }, B.Value, out var geo);
            return (int)Math.Round(geo.Rx * 2);
        }
        Assert.True(Largeur(1) < Largeur(2));
        Assert.True(Largeur(3) > Largeur(2));
        RenduPilou.Rendre(new Allure { Stade = 4 }, B.Value, out var astral);
        RenduPilou.Rendre(new Allure { Stade = 2 }, B.Value, out var pilou);
        Assert.True(astral.Ry > pilou.Ry);
    }
}
