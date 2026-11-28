using System.IO;
using System.Globalization;

namespace PilouBureau;

// Le Théâtre en haute définition (docs/SCENES-HD.md) : décors à plans de 480 × 240, scènes HD, compositeur. Même calcul que
// outils/sprites/theatre_hd.py (référence) : TheatreHdTests.cs relit outils/sprites/theatre-hd-reference.txt. Le moteur
// (position de Pilou, acteurs, effets) est celui de Theatre.cs, qui porte les deux définitions. Rien ici ne dépend de WPF.

// Un plan d'un décor : « fond » (sous les acteurs) ou « devant » (par-dessus), animé image par image.
public sealed record PlanHd(string Nom, int Profondeur, bool Devant, int Duree, List<uint[]> Images);

public sealed class DecorHd
{
    public string Id { get; init; } = "";
    public int W { get; init; }
    public int H { get; init; }
    public (int X, int Y)? Ancre { get; init; }       // « ancre: x y » (sprites HD : les pieds)
    public List<PlanHd> Plans { get; } = new();

    // Les plans « fond » aplatis : un décor se recompose à chaque image, mais ses plans ne changent que toutes les `duree`
    // ms. On aplatit une fois chaque combinaison d'images (clé : leurs indices), puis on recopie. Borné : une combinaison
    // pèse 460 Ko en HD, et des plans de durées différentes en feraient beaucoup.
    private readonly Dictionary<string, uint[]> _fonds = new();
    private const int FondsMax = 48;

    internal uint[] Fond(long t, string niveau, bool cache)
    {
        var idx = new int[Plans.Count];
        int n = 0;
        foreach (var p in Plans)
            if (!p.Devant) idx[n++] = (int)AnimationsCampagne.ImageDecor(p.Images.Count, p.Duree, t, niveau);
        string cle = string.Join(',', idx.Take(n));
        if (cache)
            lock (_fonds)
                if (_fonds.TryGetValue(cle, out var pret)) return pret;
        var px = new uint[W * H];
        Array.Fill(px, 0xFF000000u);
        int k = 0;
        foreach (var p in Plans)
            if (!p.Devant) TheatreHd.Calque(px, p.Images[idx[k++]]);
        if (cache)
            lock (_fonds)
            {
                if (_fonds.Count >= FondsMax) _fonds.Clear();
                _fonds[cle] = px;
            }
        return px;
    }
}

// Un sprite HD (assets/sprites-hd, docs/SCENES-HD.md § 6 et 7) : images ARGB à plat (0 : transparent), ancre (Ax, Ay) des
// pieds, durée d'une image.
public sealed class SpriteHd
{
    public string Id { get; }
    public int W { get; }
    public int H { get; }
    public int Ax { get; }
    public int Ay { get; }
    public int Duree { get; }
    public List<uint[]> Images { get; }

    public SpriteHd(DecorHd d)
    {
        Id = d.Id;
        W = d.W;
        H = d.H;
        (Ax, Ay) = d.Ancre ?? (d.W / 2, d.H - 1);
        Duree = d.Plans[0].Duree;
        Images = d.Plans[0].Images;
    }

    // Une silhouette pour le moteur (Theatre.Contexte.Sprites : taille, durée, nombre d'images) : rien à dessiner dedans.
    public Sprite VersSprite()
    {
        var s = new Sprite { Id = Id, Duree = Duree };
        var vide = Enumerable.Repeat(new string('.', W), H).ToArray();
        for (int i = 0; i < Images.Count; i++) s.Images.Add(vide);
        return s;
    }
}

public static class TheatreHd
{
    public const int PilouX = 48, PilouY = 107;     // ancre du Pilou fin : colonne du milieu, ligne de ses pieds
    public const int PilouW = 96, PilouH = 112;     // sa grille (rendu fin, échelle 2)

    // Pour mesurer : faux, chaque image recompose tous les plans « fond » (le résultat est le même).
    public static bool CacheFonds { get; set; } = true;

    // ---- Le décor à plans : assets/decors/decor-<campagne>-<décor>.txt

    private static uint Couleur(string c)
    {
        uint rgb = uint.Parse(c.AsSpan(1, 6), NumberStyles.HexNumber, CultureInfo.InvariantCulture);
        uint a = c.Length >= 9 ? uint.Parse(c.AsSpan(7, 2), NumberStyles.HexNumber, CultureInfo.InvariantCulture) : 255;
        return a << 24 | rgb;
    }

    // Format compact à plans : « [n]c » une plage de n pixels de la lettre c, « . » le pixel de l'image précédente du même
    // plan, « , » transparent (0). Un fichier sans ligne « plan: » a un seul plan.
    public static DecorHd LireDecorHd(string texte)
    {
        var lignes = texte.Split('\n');
        for (int j = 0; j < lignes.Length; j++) lignes[j] = lignes[j].TrimEnd('\r');
        string id = "";
        int w = 0, h = 0;
        var plans = new List<PlanHd>();
        string nomPlan = "";
        int prof = 0, duree = 0;
        bool devant = false, enPlan = false;
        (int, int)? ancre = null;
        var palette = new Dictionary<char, uint>();
        var ims = new List<uint[]>();
        int i = 0;
        while (i < lignes.Length)
        {
            var l = lignes[i++];
            if (l.Length == 0 || l[0] == '#') continue;
            int d = l.IndexOf(':');
            string cle = d >= 0 ? l[..d] : l, val = d >= 0 ? l[(d + 1)..].Trim() : "";
            if (cle == "id") id = val;
            else if (cle == "ancre")
            {
                var v = val.Split(' ', StringSplitOptions.RemoveEmptyEntries);
                ancre = (int.Parse(v[0], CultureInfo.InvariantCulture), int.Parse(v[1], CultureInfo.InvariantCulture));
            }
            else if (cle == "taille")
            {
                var v = val.Split(' ', StringSplitOptions.RemoveEmptyEntries);
                w = int.Parse(v[0], CultureInfo.InvariantCulture);
                h = int.Parse(v[1], CultureInfo.InvariantCulture);
            }
            else if (cle == "plan")
            {
                var v = val.Split(' ', StringSplitOptions.RemoveEmptyEntries);
                (nomPlan, prof, devant, duree, enPlan) = (v[0], int.Parse(v[1], CultureInfo.InvariantCulture), v[2] == "devant", 0, true);
                palette = new Dictionary<char, uint>();
                ims = new List<uint[]>();
            }
            else if ((cle == "duree" || cle == "palette") && !enPlan)
            {
                (nomPlan, prof, devant, duree, enPlan) = ("decor", 0, false, 0, true);
                palette = new Dictionary<char, uint>();
                ims = new List<uint[]>();
                i--;
            }
            else if (cle == "duree") duree = int.Parse(val, CultureInfo.InvariantCulture);
            else if (cle == "palette")
            {
                foreach (var paire in val.Split(' ', StringSplitOptions.RemoveEmptyEntries))
                {
                    int e = paire.IndexOf('=');
                    palette[paire[0]] = Couleur(paire[(e + 1)..]);
                }
            }
            else if (cle == "images")
            {
                uint[]? prec = null;
                int n = int.Parse(val, CultureInfo.InvariantCulture);
                for (int q = 0; q < n; q++)
                {
                    var im = new uint[w * h];
                    for (int y = 0; y < h; y++)
                    {
                        int x = 0, k = 0, o = y * w;
                        foreach (char ch in lignes[i])
                        {
                            if (ch is >= '0' and <= '9') { k = k * 10 + ch - '0'; continue; }
                            if (k == 0) k = 1;
                            if (ch == '.') Array.Copy(prec ?? throw new InvalidDataException(id + " : « . » sans image précédente"), o + x, im, o + x, k);
                            else if (ch != ',') Array.Fill(im, palette.TryGetValue(ch, out var c) ? c : throw new InvalidDataException(id + " : lettre « " + ch + " » sans couleur"), o + x, k);
                            x += k;
                            k = 0;
                        }
                        if (x != w) throw new InvalidDataException($"{id} : rangée de {x} pixels au lieu de {w}");
                        i++;
                    }
                    ims.Add(im);
                    prec = im;
                }
                plans.Add(new PlanHd(nomPlan, prof, devant, duree, ims));
                enPlan = false;
            }
        }
        var decor = new DecorHd { Id = id, W = w, H = h, Ancre = ancre };
        decor.Plans.AddRange(plans);
        return decor;
    }

    // ---- Les ressources embarquées : « decor:<id> » (assets/decors) et « scenehd:<campagne>.txt » (assets/scenes-hd)

    private static string? Ressource(string nom)
    {
        using var st = typeof(TheatreHd).Assembly.GetManifestResourceStream(nom);
        if (st is null) return null;
        using var r = new StreamReader(st);
        return r.ReadToEnd();
    }

    private static readonly Dictionary<string, DecorHd?> Decors = new();
    private static readonly Dictionary<string, Dictionary<string, Theatre.Scene>> ScenesCache = new();

    // Le décor « decor-<campagne>-<décor> », décodé une fois (null s'il n'existe pas).
    public static DecorHd? Decor(string id)
    {
        lock (Decors)
        {
            if (Decors.TryGetValue(id, out var d)) return d;
            var t = Ressource("decor:" + id);
            return Decors[id] = t is null ? null : LireDecorHd(t);
        }
    }

    public static SpriteHd LireSpriteHd(string texte) => new(LireDecorHd(texte));

    private static readonly Dictionary<string, SpriteHd?> SpritesCache = new();

    // Le sprite HD d'un acteur ou d'un personnage (ressource « spritehd:<id> »), décodé une fois ; null s'il n'existe pas.
    public static SpriteHd? SpriteHdDe(string id)
    {
        lock (SpritesCache)
        {
            if (SpritesCache.TryGetValue(id, out var s)) return s;
            var t = Ressource("spritehd:" + id);
            return SpritesCache[id] = t is null ? null : LireSpriteHd(t);
        }
    }

    // Les scènes HD d'une campagne (vide si la campagne n'en a pas).
    public static Dictionary<string, Theatre.Scene> ScenesHd(string campagne)
    {
        lock (ScenesCache)
        {
            if (ScenesCache.TryGetValue(campagne, out var s)) return s;
            var t = Ressource("scenehd:" + campagne + ".txt");
            return ScenesCache[campagne] = t is null ? new() : Theatre.LireScenes(t, Theatre.Hd);
        }
    }

    // ---- Le Pilou fin du bureau, rendu pour la scène

    // Une fonction pose → grille 96 × 112 ARGB (0 : vide), par RenduPilou à l'échelle 2. baseAllure : les champs propres au
    // joueur (stade, couleur, accessoire…) ; par défaut, le Pilou de démonstration (stade 2, bleu). La grille rendue est
    // celle d'un tampon réutilisé : elle n'est valable que jusqu'à l'appel suivant (ComposerHd la consomme aussitôt).
    public static Func<PoseHd, uint[]> RendeurPilou(Banque b, Allure? baseAllure = null)
    {
        var tampon = new TamponRendu();
        return pose =>
        {
            var a = baseAllure?.Copie() ?? new Allure();
            a.Expr = pose.Expr;
            a.T = pose.T;
            a.Marche = pose.Marche;
            a.Parle = pose.Parle;
            a.Cligne = pose.Cligne;
            a.Regard = pose.Regard;
            a.Saut = pose.Saut;
            a.Salue = pose.Salue;
            return RenduPilou.Rendre(a, b, out _, null, 2, tampon);
        };
    }

    // ---- Le compositeur HD

    private static void Melanger(uint[] px, int k, uint c)
    {
        uint a = c >> 24;
        if (a == 0) return;
        if (a == 255)
        {
            px[k] = c;
            return;
        }
        uint d = px[k];
        uint r = ((c >> 16 & 255) * a + (d >> 16 & 255) * (255 - a) + 127) / 255;
        uint v = ((c >> 8 & 255) * a + (d >> 8 & 255) * (255 - a) + 127) / 255;
        uint b = ((c & 255) * a + (d & 255) * (255 - a) + 127) / 255;
        px[k] = 0xFF000000 | r << 16 | v << 8 | b;
    }

    internal static void Calque(uint[] px, uint[] im)
    {
        for (int k = 0; k < im.Length; k++)
        {
            uint c = im[k];
            if (c != 0) Melanger(px, k, c);
        }
    }

    private static void PoserGrille(uint[] px, int w, int h, uint[] g, int gw, int x, int y, int ax, int ay)
    {
        int gh = g.Length / gw;
        int ox = x - ax, oy = y - ay;
        for (int j = 0; j < gh; j++)
        {
            int Y = oy + j;
            if (Y < 0 || Y >= h) continue;
            for (int i = 0; i < gw; i++)
            {
                uint c = g[j * gw + i];
                int X = ox + i;
                if (c != 0 && X >= 0 && X < w) Melanger(px, Y * w + X, c);
            }
        }
    }

    // Pose l'image im d'un sprite HD : (x, y) est son ancre ; le miroir se fait autour de l'ancre.
    private static void PoserHd(uint[] px, int w, int h, SpriteHd s, int im, int x, int y, bool miroir)
    {
        var g = s.Images[((im % s.Images.Count) + s.Images.Count) % s.Images.Count];
        int ox = x - (miroir ? s.W - 1 - s.Ax : s.Ax), oy = y - s.Ay;
        for (int j = 0; j < s.H; j++)
        {
            int Y = oy + j;
            if (Y < 0 || Y >= h) continue;
            int o = j * s.W;
            for (int i = 0; i < s.W; i++)
            {
                uint c = g[o + i];
                if (c == 0) continue;
                int X = ox + (miroir ? s.W - 1 - i : i);
                if (X >= 0 && X < w) Melanger(px, Y * w + X, c);
            }
        }
    }

    // L'image HD de la scène à l'instant t : plans « fond », puis acteurs, personnage et Pilou triés par leurs pieds (Pilou
    // après les autres à égalité), puis plans « devant », puis effets. sprites : les sprites HD des acteurs et personnages
    // (cx.Sprites n'en donne que la taille, la durée et le nombre d'images) ; ceux qui manquent ne sont pas dessinés : jamais
    // d'ancien sprite agrandi (docs/SCENES-HD.md, § 2). Un personnage HD regarde à droite : il est retourné pour regarder
    // Pilou. Sans décor : fond noir. rendrePilou : grille 96 × 112.
    public static uint[] ComposerHd(DecorHd? decor, Theatre.Contexte cx, Func<string, SpriteHd?> sprites,
        IReadOnlyList<Theatre.Evenement> evts, long t, Func<PoseHd, uint[]> rendrePilou, int regard = 0,
        string niveau = AnimationsCampagne.Completes, uint[]? sortie = null)
    {
        var sc = cx.Scene;
        int w = sc.D.W, h = sc.D.H;
        var px = sortie is not null && sortie.Length == w * h ? sortie : new uint[w * h];
        bool decorOk = decor is not null && decor.W == w && decor.H == h;
        if (decorOk) Array.Copy(decor!.Fond(t, niveau, CacheFonds), px, px.Length);
        else Array.Fill(px, 0xFF000000u);
        var poses = new List<(int Y, int Z, Theatre.Pose? P, Theatre.EtatPilouFin? E)>();
        foreach (var a in Theatre.Acteurs(cx, evts, t, niveau)) poses.Add((a.Y, 0, a, null));
        if (Theatre.Perso(cx, evts, t, niveau) is { } pp && sprites(pp.Sprite) is not null)
            poses.Add((pp.Y, 0, pp with { Miroir = !pp.Miroir }, null));
        var etat = Theatre.PilouEtat(cx, evts, t, regard, niveau);
        if (etat.Visible) poses.Add((etat.Y, 1, null, etat));
        // Tri stable par (pieds, Pilou après les acteurs à égalité), comme la référence.
        var tries = poses.Select((q, i) => (q, i)).OrderBy(q => q.q.Y).ThenBy(q => q.q.Z).ThenBy(q => q.i).Select(q => q.q);
        foreach (var q in tries)
        {
            if (q.E is { } e) PoserGrille(px, w, h, rendrePilou(Theatre.PoseHd(e, t)), PilouW, e.X, q.Y, PilouX, PilouY);
            else
            {
                var s = q.P!.Value;
                if (sprites(s.Sprite) is { } sh) PoserHd(px, w, h, sh, s.Image, s.X, s.Y, s.Miroir);
            }
        }
        if (decorOk)
            foreach (var p in decor!.Plans)
                if (p.Devant) Calque(px, p.Images[(int)AnimationsCampagne.ImageDecor(p.Images.Count, p.Duree, t, niveau)]);
        foreach (var q in Theatre.Effets(cx, evts, t, niveau))
            if (sprites(q.Sprite) is { } sh) PoserHd(px, w, h, sh, q.Image, q.X, q.Y, q.Miroir);
        return px;
    }
}
