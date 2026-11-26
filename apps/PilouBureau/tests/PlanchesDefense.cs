using System.IO.Compression;
using PilouBureau;
using Xunit;

// Planches de contrôle de Défense du bureau (PNG) : les sprites, et un storyboard d'une partie de démo.
// Seulement si PILOU_PLANCHES_DEFENSE donne un dossier :
//     PILOU_PLANCHES_DEFENSE=/tmp/defense dotnet test --filter PlanchesDefense
public class PlanchesDefense
{
    private static readonly string? Dossier = Environment.GetEnvironmentVariable("PILOU_PLANCHES_DEFENSE");
    private static readonly Lazy<Banque> B = new(() => Banque.DepuisDossier(Path.Combine(DefenseTests.Racine(), "assets")));

    [Fact]
    public void Planches()
    {
        if (string.IsNullOrEmpty(Dossier)) return;
        Directory.CreateDirectory(Dossier);
        Png.Ecrire(Path.Combine(Dossier, "planche-sprites.png"), PlancheSprites(), 4);
        var (story, w, h) = Storyboard();
        Png.Ecrire(Path.Combine(Dossier, "storyboard.png"), story, w, h);
        var (jeu, jw, jh) = Scene(28, 2);
        Png.Ecrire(Path.Combine(Dossier, "partie-x2.png"), jeu, jw, jh);
    }

    // Fond de bureau générique : dégradé, deux fenêtres quelconques (ni marque ni logo).
    private static uint[] Bureau(int w, int h, int graine)
    {
        var px = new uint[w * h];
        for (int y = 0; y < h; y++)
        for (int x = 0; x < w; x++)
        {
            double k = (x / (double)w + y / (double)h) / 2;
            uint r = (uint)(70 + 40 * k), g = (uint)(96 + 40 * k), b = (uint)(130 + 50 * k);
            px[y * w + x] = 0xff000000 | r << 16 | g << 8 | b;
        }
        void Fenetre(int fx, int fy, int fw, int fh, uint barre)
        {
            for (int y = fy; y < Math.Min(h, fy + fh); y++)
            for (int x = fx; x < Math.Min(w, fx + fw); x++)
                px[y * w + x] = y < fy + 10 ? barre : (x - fx) % 40 < 30 && (y - fy) % 9 < 2 && y > fy + 16 ? 0xffd0d7de : 0xfff6f8fa;
        }
        Fenetre(40 + graine * 13 % 60, 10, w / 3, h - 20, 0xff57606a);
        Fenetre(w / 2 + 30, 30, w / 3, h, 0xff2f7ed8);
        return px;
    }

    private static uint[] Composer(uint[] fond, ToileDefense o)
    {
        var r = (uint[])fond.Clone();
        for (int i = 0; i < r.Length; i++) r[i] = ToileDefense.Melanger(r[i], o.Px[i]);
        return r;
    }

    private static ToileDefense Rendre(PartieDefense p, double t, VueDefense v)
    {
        var o = new ToileDefense(p.W, p.H);
        var a = DessinDefense.AllurePilou(new Allure(), p, t, v.Resultat);
        var px = RenduPilou.Rendre(a, B.Value, out var geo);
        DessinDefense.Dessiner(o, p, B.Value, px, geo, t, v);
        return o;
    }

    // Une partie de démo arrêtée à l'instant voulu (la démo est déterministe : même graine, même image).
    private static (PartieDefense P, double T) Demo(double secondes, int sauter = 0, int w = 960, int h = 216)
    {
        var p = new PartieDefense(w, h, 2026);
        var pilote = new PiloteDemo(2026);
        p.Commencer();
        p.Immortel = true;
        if (sauter > 0) p.SauterA(sauter);
        for (int i = 0; i < (int)(secondes * 60); i++)
        {
            pilote.Jouer(p, 1 / 60.0);
            p.Avancer(1 / 60.0);
        }
        return (p, secondes * 1000);
    }

    private static (uint[] Px, int W, int H) Scene(double secondes, int zoom)
    {
        var (p, t) = Demo(secondes);
        var o = Rendre(p, t, new VueDefense { Meilleur = 4200 });
        var img = Composer(Bureau(p.W, p.H, 1), o);
        return (Agrandir(img, p.W, p.H, zoom), p.W * zoom, p.H * zoom);
    }

    private static uint[] Agrandir(uint[] px, int w, int h, int z)
    {
        var r = new uint[w * z * h * z];
        for (int y = 0; y < h * z; y++)
        for (int x = 0; x < w * z; x++)
            r[y * w * z + x] = px[y / z * w + x / z];
        return r;
    }

    private static (uint[] Px, int W, int H) Storyboard()
    {
        const int w = 960, h = 216, legende = 14;
        var cases = new List<(string Titre, uint[] Px)>();
        void Case(string titre, PartieDefense p, double t, VueDefense v) => cases.Add((titre, Composer(Bureau(w, h, cases.Count), Rendre(p, t, v))));

        var accueil = new PartieDefense(w, h, 2026);
        Case("1. ACCUEIL : LES BUGS, LES BONUS, LES TOUCHES", accueil, 1200, new VueDefense { Meilleur = 4200 });
        var (d1, t1) = Demo(2.5);
        Case("2. VAGUE 1 : LA FORMATION ARRIVE, PILOU TIRE", d1, t1, new VueDefense { Meilleur = 4200 });
        var (d2, t2) = Demo(26);
        Case("3. COMBO, BONUS QUI TOMBE, ABRIS ENTAMÉS", d2, t2, new VueDefense { Meilleur = 4200 });
        var (d3, t3) = Demo(9, 7);
        Case("4. VAGUE 7 : BLINDÉS, DIVISEURS, MOUCHERONS", d3, t3, new VueDefense { Meilleur = 4200, IaAttend = true });
        var (d4, t4) = Demo(5, 5);
        Case("5. VAGUE 5 : LE BUG DE PROD", d4, t4, new VueDefense { Meilleur = 4200 });
        var (d5, t5) = Demo(12, 3);
        d5.Pause(true);
        Case("6. PAUSE (AUTRE APPLI EN PLEIN ÉCRAN, OU P)", d5, t5, new VueDefense { Meilleur = 4200 });
        var (d6, t6) = Demo(0.5);
        d6.ViderVague();
        for (int i = 0; i < 30; i++) d6.Avancer(1 / 60.0);
        Case("7. VAGUE FRANCHIE", d6, t6 + 500, new VueDefense { Meilleur = 4200 });
        var (d7, t7) = Demo(40, 4);
        d7.Abandonner();
        Case("8. FIN : SCORE, RECORD, GAINS BORNÉS", d7, t7, new VueDefense { Meilleur = 4200, Resultat = new ResultatDefense(26, 7, false, true) });

        int cols = 2, rows = (cases.Count + 1) / 2, sw = cols * w + 3 * 8, sh = rows * (h + legende) + (rows + 1) * 8;
        var o = new ToileDefense(sw, sh);
        o.Vider(0xff0f141a);
        for (int i = 0; i < cases.Count; i++)
        {
            int x = 8 + i % cols * (w + 8), y = 8 + i / cols * (h + legende + 8);
            o.Texte(cases[i].Titre, x, y + 2, 0xffffd8b0);
            o.Image(cases[i].Px, w, h, x, y + legende);
        }
        return (Agrandir(o.Px, sw, sh, 1), sw, sh);
    }

    private static ToileDefense PlancheSprites()
    {
        var ids = new (string Id, string Nom)[]
        {
            ("bug-scarabee", "SCARABÉE 30"), ("bug-araignee", "ARAIGNÉE 20"), ("bug-ver", "VER 10"), ("defense-blinde", "BLINDÉ 40"),
            ("defense-blinde-fele", "BLINDÉ FÊLÉ"), ("defense-diviseur", "DIVISEUR 20"), ("defense-mini", "MOITIÉ 10"),
            ("defense-rapide", "MOUCHERON 50"), ("defense-etincelle", "ÉTINCELLE"), ("defense-tir", "TIR DES BUGS"),
            ("defense-bonus-double", "TIR DOUBLE"), ("defense-bonus-bouclier", "BOUCLIER"), ("defense-bonus-ralenti", "RALENTI"),
            ("vie", "VIE"),
        };
        const int w = 390, h = 170;
        var o = new ToileDefense(w, h);
        o.Vider(0xff1c2128);
        o.Texte("DÉFENSE DU BUREAU : SPRITES (PIXELS DE JEU, DEUX IMAGES)", 4, 3, 0xfff69d50);
        int x = 4, y = 14;
        foreach (var (id, nom) in ids)
        {
            var s = B.Value[id]!;
            var titre = nom.Replace("Ê", "E");
            int largeur = s.Images.Count * (s.W + 3) - 3, lw = Math.Max(largeur, ToileDefense.Largeur(titre)) + 10;
            if (x + lw > w)
            {
                x = 4;
                y += 28;
            }
            for (int k = 0; k < s.Images.Count; k++) o.Grille(Banque.Grille(s, k * Math.Max(1, s.Duree)), x + k * (s.W + 3), y);
            o.Texte(titre, x, y + 17, 0xffb8c4d2);
            x += lw;
        }
        var prod = B.Value["bug-prod"]!;
        o.Grille(Banque.Grille(prod, 0), 312, 108, 2);
        o.Texte("BUG DE PROD X2", 312, 158, 0xffb8c4d2);
        // Abris neufs et entamés, puis Pilou en jeu.
        y = 116;
        var partie = new PartieDefense(960, 216, 1);
        partie.Commencer();
        var neuf = partie.Abris[0];
        var post = partie.Abris[1];
        var abime = Abri.Creer(0, 0, true);
        var dechire = Abri.Creer(0, 0, false);
        var h2 = new Hasard(3);
        for (int i = 0; i < 40; i++)
        {
            abime.Pv[h2.Suivant(abime.Lignes), h2.Suivant(abime.Colonnes)] = Math.Max(0, abime.Pv[h2.Suivant(abime.Lignes), h2.Suivant(abime.Colonnes)] - 1);
            dechire.Pv[h2.Suivant(dechire.Lignes), h2.Suivant(dechire.Colonnes)] = 0;
        }
        int ax = 4;
        foreach (var a in new[] { neuf, abime, post, dechire })
        {
            var p = new PartieDefense(960, 216, 1);
            p.Commencer();
            p.ViderVague();
            a.X = ax;
            a.Y = y;
            p.Abris.Clear();
            p.Abris.Add(a);
            var toile = new ToileDefense(w, h);
            DessinDefense.Dessiner(toile, p, B.Value, Array.Empty<uint>(), default, 0, new VueDefense());
            for (int yy = (int)a.Y; yy < a.Y + a.Hauteur; yy++)
            for (int xx = (int)a.X; xx < a.X + a.Largeur; xx++)
                o.Px[yy * w + xx] = toile.Px[yy * w + xx] >> 24 >= 0xa0 ? toile.Px[yy * w + xx] | 0xff000000 : o.Px[yy * w + xx];
            ax += 44;
        }
        o.Texte("ABRIS : NEUFS, ENTAMÉS", 4, y + 31, 0xffb8c4d2);
        o.Texte("PILOU EN JEU", 186, 158, 0xffb8c4d2);
        int pxx = 180;
        foreach (var expr in new[] { "concentre", "grimace", "fete" })
        {
            var g = RenduPilou.Rendre(new Allure { Expr = expr, RegardY = expr == "concentre" ? -1 : 0 }, B.Value);
            o.Image(g, RenduPilou.W, RenduPilou.H, pxx, 100);
            pxx += 42;
        }
        return o;
    }
}

// PNG RGBA minimal (zlib de .NET, CRC maison) : pour les planches de contrôle seulement.
public static class Png
{
    public static void Ecrire(string chemin, ToileDefense o, int zoom)
    {
        var px = new uint[o.W * zoom * o.H * zoom];
        for (int y = 0; y < o.H * zoom; y++)
        for (int x = 0; x < o.W * zoom; x++)
            px[y * o.W * zoom + x] = o.Px[y / zoom * o.W + x / zoom];
        Ecrire(chemin, px, o.W * zoom, o.H * zoom);
    }

    public static void Ecrire(string chemin, uint[] px, int w, int h)
    {
        using var brut = new MemoryStream();
        for (int y = 0; y < h; y++)
        {
            brut.WriteByte(0);
            for (int x = 0; x < w; x++)
            {
                uint c = px[y * w + x];
                brut.WriteByte((byte)(c >> 16));
                brut.WriteByte((byte)(c >> 8));
                brut.WriteByte((byte)c);
                brut.WriteByte((byte)(c >> 24));
            }
        }
        using var z = new MemoryStream();
        using (var zl = new ZLibStream(z, CompressionLevel.Optimal, true)) brut.WriteTo(zl);
        using var f = File.Create(chemin);
        f.Write(new byte[] { 0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a });
        var ihdr = new byte[13];
        Be(ihdr, 0, (uint)w);
        Be(ihdr, 4, (uint)h);
        ihdr[8] = 8;
        ihdr[9] = 6;
        Bloc(f, "IHDR", ihdr);
        Bloc(f, "IDAT", z.ToArray());
        Bloc(f, "IEND", Array.Empty<byte>());
    }

    private static void Be(byte[] b, int i, uint v)
    {
        b[i] = (byte)(v >> 24);
        b[i + 1] = (byte)(v >> 16);
        b[i + 2] = (byte)(v >> 8);
        b[i + 3] = (byte)v;
    }

    private static void Bloc(Stream f, string type, byte[] donnees)
    {
        var l = new byte[4];
        Be(l, 0, (uint)donnees.Length);
        f.Write(l);
        var t = System.Text.Encoding.ASCII.GetBytes(type);
        f.Write(t);
        f.Write(donnees);
        uint crc = 0xffffffff;
        foreach (var b in t.Concat(donnees))
        {
            crc ^= b;
            for (int k = 0; k < 8; k++) crc = (crc & 1) != 0 ? 0xedb88320 ^ (crc >> 1) : crc >> 1;
        }
        Be(l, 0, ~crc);
        f.Write(l);
    }
}
