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

    [Fact]
    public void Memes_pixels_que_la_reference()
    {
        var lignes = File.ReadAllLines(Path.Combine(Racine(), "outils", "sprites", "rendus-reference.txt"))
            .Where(l => !l.StartsWith('#') && l.Trim() != "").ToList();
        Assert.True(lignes.Count >= 40);
        var ecarts = lignes.Where(l =>
        {
            var p = l.Split('|');
            return Empreinte(RenduPilou.Rendre(Lire(p[0]), B.Value)) != p[1].Trim();
        }).Select(l => l.Split('|')[0].Trim()).ToList();
        Assert.Empty(ecarts);
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
        Assert.Equal(13, b.Tenues.Count);
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
