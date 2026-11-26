using System.IO;

namespace PilouBureau;

// Icône de Pilou (zone de notification, exécutable, Gestionnaire des tâches) : tirée du rendu de Pilou lui-même
// (RenduPilou, au repos, bleu), recadrée sur sa silhouette et agrandie au pixel près, sans lissage.
// Le fichier pilou.ico du dépôt en est la copie figée (ApplicationIcon a besoin d'un fichier à la compilation) ;
// un test vérifie qu'il correspond toujours au rendu. Le régénérer : PILOU_ICONE=ecrire dotnet test --filter Icone
public static class Icone
{
    public static readonly int[] Tailles = { 16, 20, 24, 32, 48 };
    private const uint OmbreSol = 0x33000000;

    // Pilou au repos, yeux ouverts, sans ombre au sol ni marge : (pixels ARGB ligne par ligne, largeur, hauteur).
    public static (uint[] Px, int W, int H) Silhouette(Banque b)
    {
        var g = RenduPilou.Rendre(new Allure(), b);
        int x0 = RenduPilou.W, y0 = RenduPilou.H, x1 = -1, y1 = -1;
        for (int y = 0; y < RenduPilou.H; y++)
        for (int x = 0; x < RenduPilou.W; x++)
        {
            uint c = g[y * RenduPilou.W + x];
            if (c == 0 || c == OmbreSol) continue;
            x0 = Math.Min(x0, x);
            y0 = Math.Min(y0, y);
            x1 = Math.Max(x1, x);
            y1 = Math.Max(y1, y);
        }
        if (x1 < 0) return (new uint[1], 1, 1); // banque vide : un pixel transparent
        int w = x1 - x0 + 1, h = y1 - y0 + 1;
        var o = new uint[w * h];
        for (int y = 0; y < h; y++)
        for (int x = 0; x < w; x++)
        {
            uint c = g[(y + y0) * RenduPilou.W + x + x0];
            o[y * w + x] = c == OmbreSol ? 0 : c;
        }
        return (o, w, h);
    }

    // Image carrée taille × taille : Pilou centré, agrandi d'un facteur entier si la place le permet,
    // sinon réduit au plus proche voisin (les petites tailles gardent l'aspect pixel).
    public static uint[] Image(uint[] px, int w, int h, int taille)
    {
        var o = new uint[taille * taille];
        int cote = Math.Max(w, h);
        double k = cote <= taille ? Math.Floor((double)taille / cote) : (double)taille / cote;
        int lw = Math.Max(1, (int)Math.Round(w * k)), lh = Math.Max(1, (int)Math.Round(h * k));
        int ox = (taille - lw) / 2, oy = (taille - lh) / 2;
        for (int y = 0; y < lh; y++)
        for (int x = 0; x < lw; x++)
        {
            int sx = Math.Min(w - 1, (int)(x / k)), sy = Math.Min(h - 1, (int)(y / k));
            o[(y + oy) * taille + x + ox] = px[sy * w + sx];
        }
        return o;
    }

    // Fichier .ico : une image BMP 32 bits (BGRA, de bas en haut, masque ET) par taille.
    public static byte[] Ico(IReadOnlyList<(int Taille, uint[] Px)> images)
    {
        var corps = images.Select(i => Bmp(i.Taille, i.Px)).ToList();
        using var m = new MemoryStream();
        using var w = new BinaryWriter(m);
        w.Write((ushort)0);
        w.Write((ushort)1); // icône
        w.Write((ushort)images.Count);
        int decalage = 6 + 16 * images.Count;
        for (int i = 0; i < images.Count; i++)
        {
            int t = images[i].Taille;
            w.Write((byte)(t >= 256 ? 0 : t));
            w.Write((byte)(t >= 256 ? 0 : t));
            w.Write((byte)0);   // pas de palette
            w.Write((byte)0);
            w.Write((ushort)1); // plans
            w.Write((ushort)32);
            w.Write(corps[i].Length);
            w.Write(decalage);
            decalage += corps[i].Length;
        }
        foreach (var c in corps) w.Write(c);
        w.Flush();
        return m.ToArray();
    }

    private static byte[] Bmp(int t, uint[] px)
    {
        int ligneMasque = (t + 31) / 32 * 4;
        using var m = new MemoryStream();
        using var w = new BinaryWriter(m);
        w.Write(40);
        w.Write(t);
        w.Write(t * 2); // image + masque
        w.Write((ushort)1);
        w.Write((ushort)32);
        w.Write(0);
        w.Write(t * t * 4 + ligneMasque * t);
        w.Write(0);
        w.Write(0);
        w.Write(0);
        w.Write(0);
        for (int y = t - 1; y >= 0; y--)
        for (int x = 0; x < t; x++)
        {
            uint c = px[y * t + x];
            w.Write((byte)c);
            w.Write((byte)(c >> 8));
            w.Write((byte)(c >> 16));
            w.Write((byte)(c >> 24));
        }
        for (int y = t - 1; y >= 0; y--)
        {
            var ligne = new byte[ligneMasque];
            for (int x = 0; x < t; x++)
                if (px[y * t + x] >> 24 == 0) ligne[x / 8] |= (byte)(0x80 >> (x % 8));
            w.Write(ligne);
        }
        w.Flush();
        return m.ToArray();
    }

    public static byte[] Generer(Banque b)
    {
        var (px, w, h) = Silhouette(b);
        return Ico(Tailles.Select(t => (t, Image(px, w, h, t))).ToList());
    }

    // Entrées d'un .ico : (taille, début, longueur des données de l'image).
    public static List<(int Taille, int Debut, int Longueur)> Entrees(byte[] ico)
    {
        var l = new List<(int, int, int)>();
        if (ico.Length < 6 || BitConverter.ToUInt16(ico, 2) != 1) return l;
        int n = BitConverter.ToUInt16(ico, 4);
        for (int i = 0; i < n && 6 + 16 * (i + 1) <= ico.Length; i++)
        {
            int p = 6 + 16 * i;
            int t = ico[p] == 0 ? 256 : ico[p];
            int longueur = BitConverter.ToInt32(ico, p + 8), debut = BitConverter.ToInt32(ico, p + 12);
            if (debut >= 0 && longueur > 0 && debut + longueur <= ico.Length) l.Add((t, debut, longueur));
        }
        return l;
    }

    // L'image la mieux adaptée à une taille voulue : exacte, sinon la plus petite plus grande, sinon la plus grande.
    public static int Choisir(IReadOnlyList<int> tailles, int voulue)
    {
        if (tailles.Count == 0) return -1;
        int meilleure = -1;
        for (int i = 0; i < tailles.Count; i++)
        {
            if (tailles[i] < voulue) continue;
            if (meilleure < 0 || tailles[i] < tailles[meilleure]) meilleure = i;
        }
        if (meilleure >= 0) return meilleure;
        for (int i = 0; i < tailles.Count; i++)
            if (meilleure < 0 || tailles[i] > tailles[meilleure]) meilleure = i;
        return meilleure;
    }
}
