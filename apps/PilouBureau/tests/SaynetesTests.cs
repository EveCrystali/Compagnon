using PilouBureau;
using Xunit;

// Saynètes de repos : mêmes tirages et mêmes poses que outils/sprites/saynetes.py (saynetes-reference.txt) et que le
// téléphone (SaynetesTest.java), à partir de la même banque (assets/saynetes.txt).
public class SaynetesTests
{
    private static string Racine()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d is not null && !File.Exists(Path.Combine(d.FullName, "assets", "index.txt"))) d = d.Parent;
        Assert.NotNull(d);
        return d!.FullName;
    }

    private static List<Saynetes.Saynete> Banque() =>
        Saynetes.Lire(File.ReadAllText(Path.Combine(Racine(), "assets", "saynetes.txt")));

    private static Dictionary<string, string> Champs(IEnumerable<string> mots) =>
        mots.Select(m => m.Split('=', 2)).ToDictionary(m => m[0], m => m[1]);

    internal static string Texte(Saynetes.Jeu? j) => j is null ? "fini"
        : $"assis={j.Assis} saut={j.Saut} etire={j.Etire} penche={j.Penche} expr={j.Expr} regard={j.Regard} regard_y={j.RegardY} "
          + $"cligne={(j.Cligne ? 1 : 0)} baille={(j.Baille ? 1 : 0)} salue={(j.Salue ? 1 : 0)} objets={(j.Objets.Count == 0 ? "-" : string.Join(',', j.Objets))}";

    [Fact]
    public void Memes_valeurs_que_la_reference()
    {
        var banque = Banque();
        Assert.True(banque.Count >= 15);
        var lignes = File.ReadAllLines(Path.Combine(Racine(), "outils", "sprites", "saynetes-reference.txt"))
            .Where(l => !l.StartsWith('#') && l.Trim() != "").ToList();
        Assert.True(lignes.Count > 1000);
        var ecarts = new List<string>();
        foreach (var l in lignes)
        {
            var (gauche, attendu) = (l[..l.IndexOf(" -> ")], l[(l.IndexOf(" -> ") + 4)..]);
            var m = gauche.Split(' ');
            string obtenu;
            if (m[0] == "tirer")
            {
                var c = Champs(m.Skip(1));
                var ctx = new Saynetes.Contexte(int.Parse(c["heure"]), int.Parse(c["mois"]), int.Parse(c["stade"]),
                    c["objets"] == "-" ? Array.Empty<string>() : c["objets"].Split(','), c["compagnon"] == "1",
                    c["mainlibre"] == "1", c["travail"] == "1", c["traits"] == "-" ? Array.Empty<string>() : c["traits"].Split(','));
                obtenu = Saynetes.Tirer(banque, int.Parse(c["u"]), ctx, c["evite"] == "-" ? "" : c["evite"]) is { Length: > 0 } id ? id : "-";
            }
            else if (m[0] == "eveil")
            {
                var c = Champs(m.Skip(1));
                int h = int.Parse(c["heure"]);
                obtenu = (Saynetes.Endormi(h, double.Parse(c["inactif"])) ? "dort" : "eveille") + $" nuit={(Saynetes.Nuit(h) ? 1 : 0)}";
            }
            else
                obtenu = Texte(Saynetes.Jouer(Saynetes.Trouver(banque, m[1])!, long.Parse(m[2]), m[3], int.Parse(m[4])));
            if (obtenu != attendu) ecarts.Add($"{gauche} : {obtenu} au lieu de {attendu}");
        }
        Assert.True(ecarts.Count == 0, string.Join('\n', ecarts.Take(10)));
    }

    // Un compagnon de tout : sans aucune session d'IA, Pilou est éveillé ; il ne dort que si on s'absente, ou la nuit.
    [Fact]
    public void Sans_ia_il_est_eveille()
    {
        var suivi = new Suivi();
        suivi.Observer(Array.Empty<EtatSession>(), 1_000_000);
        Assert.Equal(Expr.Repos, suivi.Expression(1_000_000, -1e12));
        Assert.False(Saynetes.Endormi(15, 3 * 60_000));
        Assert.True(Saynetes.Endormi(3, 3 * 60_000));
        Assert.True(Saynetes.Endormi(15, 11 * 60_000));
    }

    [Fact]
    public void Aucune_coupe_tout_et_les_rares_restent_rares()
    {
        var banque = Banque();
        foreach (var s in banque)
            Assert.Null(Saynetes.Jouer(s, s.Duree / 2, AnimationsCampagne.Aucune));
        var ctx = new Saynetes.Contexte(10, 6, 2, Array.Empty<string>(), false, true, false);
        var tires = Enumerable.Range(0, 10000).Select(u => Saynetes.Trouver(banque, Saynetes.Tirer(banque, u, ctx))!).ToList();
        int rares = tires.Count(s => s.Poids == 1);
        Assert.InRange(rares, 150, 500); // quatre rares : de l'ordre d'une fois sur cent chacune
        Assert.DoesNotContain(tires, s => s.Poids == 0); // les réactions au monde ne sont jamais tirées
    }
}
