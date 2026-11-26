namespace PilouBureau;

// Image en pixels de jeu (ARGB, alpha non prémultiplié), sans WPF : la fenêtre la copie dans un WriteableBitmap
// agrandi sans lissage ; les tests en font des PNG (planche, storyboard).
public sealed class ToileDefense
{
    public int W { get; }
    public int H { get; }
    public uint[] Px { get; }
    // Décalage de tout le dessin (petite secousse quand Pilou est touché).
    public int Dx, Dy;

    public ToileDefense(int w, int h)
    {
        W = w;
        H = h;
        Px = new uint[w * h];
    }

    public void Vider(uint c) => Array.Fill(Px, c);

    // Source sur destination (« source-over »), alpha droit.
    public static uint Melanger(uint fond, uint c)
    {
        uint sa = c >> 24;
        if (sa == 255) return c;
        if (sa == 0) return fond;
        uint da = fond >> 24;
        uint oa = sa + da * (255 - sa) / 255;
        if (oa == 0) return 0;
        uint Canal(int d) => (((c >> d) & 255) * sa + ((fond >> d) & 255) * da * (255 - sa) / 255) / oa;
        return oa << 24 | Canal(16) << 16 | Canal(8) << 8 | Canal(0);
    }

    public static uint Opacite(uint c, double o) => o >= 1 ? c : (uint)Math.Round((c >> 24) * Math.Clamp(o, 0, 1)) << 24 | (c & 0xffffff);

    public void Point(int x, int y, uint c)
    {
        x += Dx;
        y += Dy;
        if ((uint)x >= (uint)W || (uint)y >= (uint)H || c >> 24 == 0) return;
        ref uint d = ref Px[y * W + x];
        d = Melanger(d, c);
    }

    public void Rect(int x, int y, int w, int h, uint c)
    {
        for (int j = 0; j < h; j++)
        for (int i = 0; i < w; i++)
            Point(x + i, y + j, c);
    }

    public void Cadre(int x, int y, int w, int h, uint c)
    {
        Rect(x, y, w, 1, c);
        Rect(x, y + h - 1, w, 1, c);
        Rect(x, y + 1, 1, h - 2, c);
        Rect(x + w - 1, y + 1, 1, h - 2, c);
    }

    // Grille de couleurs (sprite de la banque), agrandie d'un facteur entier.
    public void Grille(uint[,] g, int x, int y, int echelle = 1, double opacite = 1, bool miroir = false, uint eclaircir = 0)
    {
        int h = g.GetLength(0), w = g.GetLength(1);
        for (int r = 0; r < h; r++)
        for (int c = 0; c < w; c++)
        {
            uint v = g[r, miroir ? w - 1 - c : c];
            if (v >> 24 == 0) continue;
            if (eclaircir != 0) v = Melanger(v, eclaircir) | (v & 0xff000000);
            v = Opacite(v, opacite);
            if (echelle == 1) Point(x + c, y + r, v);
            else Rect(x + c * echelle, y + r * echelle, echelle, echelle, v);
        }
    }

    // Image ARGB ligne par ligne (le rendu de Pilou, 48 × 56).
    public void Image(uint[] g, int gw, int gh, int x, int y, double opacite = 1)
    {
        for (int r = 0; r < gh; r++)
        for (int c = 0; c < gw; c++)
        {
            uint v = g[r * gw + c];
            if (v >> 24 != 0) Point(x + c, y + r, Opacite(v, opacite));
        }
    }

    public static int Largeur(string texte, int echelle = 1) => texte.Length == 0 ? 0 : Police.Texte(texte).GetLength(1) * echelle;

    // Texte de la police pixel (majuscules), avec une ombre d'un pixel en bas à droite si demandée.
    public void Texte(string texte, int x, int y, uint c, int echelle = 1, uint ombre = 0)
    {
        if (texte.Length == 0) return;
        var m = Police.Texte(texte.ToUpperInvariant());
        int h = m.GetLength(0), w = m.GetLength(1);
        for (int r = 0; r < h; r++)
        for (int k = 0; k < w; k++)
        {
            if (m[r, k] == 0) continue;
            if (ombre != 0) Rect(x + k * echelle + echelle, y + r * echelle + echelle, echelle, echelle, ombre);
        }
        for (int r = 0; r < h; r++)
        for (int k = 0; k < w; k++)
            if (m[r, k] != 0) Rect(x + k * echelle, y + r * echelle, echelle, echelle, c);
    }

    public void Centre(string texte, int cx, int y, uint c, int echelle = 1, uint ombre = 0) =>
        Texte(texte, cx - Largeur(texte.ToUpperInvariant(), echelle) / 2, y, c, echelle, ombre);
}

// Ce que la fenêtre sait en plus de la partie : réglages, record, gains, effets du moment.
public sealed class VueDefense
{
    public bool FlashsReduits;
    public bool Demo;
    public int Meilleur;
    public ResultatDefense? Resultat;
    public bool IaAttend;
    public double Alerte;   // 0..1 : cadre orange (Pilou touché)
    public double Flash;    // 0..1 : voile clair bref (Bug de prod vaincu), jamais si les flashs sont réduits
}

// Le dessin de Défense du bureau : bande légèrement assombrie, cadre pixel, abris, bugs, tirs, Pilou, bandeau.
// Couleurs : orange, bleu, violet, crème, argent, jaune de post-it — jamais d'opposition rouge-vert ; les tirs de
// Pilou (traits orange verticaux) et ceux des bugs (losanges violets) se distinguent aussi par la forme.
public static class DessinDefense
{
    public const uint Voile = 0x520f141a, Bandeau = 0xd80f141a, Encre = 0xff1c2128, Creme = 0xfff6f8fa, Gris = 0xff768390,
        Argent = 0xffb8c4d2, Bleu = 0xff6cb6ff, BleuClair = 0xffb4dbff, BleuFonce = 0xff2f7ed8, Marine = 0xff1f4f8a,
        Orange = 0xfff69d50, OrangeClair = 0xffffd8b0, Brun = 0xff8a4a1f, Violet = 0xff9b8cff, VioletClair = 0xffd2caff,
        Jaune = 0xfff5d76e, JauneFonce = 0xffc9a227, JaunePale = 0xfffff6cc, FondBoite = 0xe60f141a;

    // Zones cliquables (pixels de jeu) : fermer ✕ (toujours), réglage des flashs (accueil), rejouer et quitter (fin).
    public static Clics.Zone Fermer(int w) => new(w - 14, 1, 12, 12);

    public static Clics.Zone Flashs(int w, int h) => new(w / 2 - 70, Haut(h) + 120, 140, 9);

    public static Clics.Zone Rejouer(int w, int h) => new(w / 2 - 66, Haut(h) + 104, 60, 14);

    public static Clics.Zone Quitter(int w, int h) => new(w / 2 + 6, Haut(h) + 104, 60, 14);

    // Haut de la boîte centrale (accueil, fin) : 132 pixels de haut au plus, sous le bandeau.
    private static int Haut(int h) => Math.Max(PartieDefense.Hud + 2, (h - 132) / 2);

    private static readonly Dictionary<(string, int), uint[,]> Cache = new();

    private static uint[,]? Sprite(Banque b, string id, double t)
    {
        var s = b[id];
        int image = s is null || s.Duree <= 0 || s.Images.Count <= 1 ? 0 : (int)(Math.Floor(Math.Max(0, t) / s.Duree) % s.Images.Count);
        if (s is null) return null;
        lock (Cache)
        {
            if (!Cache.TryGetValue((id, image), out var g)) Cache[(id, image)] = g = Banque.Grille(s, image * Math.Max(1, s.Duree));
            return g;
        }
    }

    private static void Poser(ToileDefense o, Banque b, string id, double t, int x, int y, uint secours, int l, int h, int echelle = 1,
        double opacite = 1, uint eclaircir = 0)
    {
        if (Sprite(b, id, t) is { } g) o.Grille(g, x, y, echelle, opacite, false, eclaircir);
        else o.Rect(x, y, l * echelle, h * echelle, ToileDefense.Opacite(secours, opacite));
    }

    public static string IdBug(BugDefense b) => b.Sorte switch
    {
        SorteBug.Scarabee => "bug-scarabee", SorteBug.Araignee => "bug-araignee", SorteBug.Ver => "bug-ver",
        SorteBug.Blinde => b.Pv > 1 ? "defense-blinde" : "defense-blinde-fele", SorteBug.Diviseur => "defense-diviseur",
        SorteBug.Mini => "defense-mini", _ => "defense-rapide",
    };

    public static string IdBonus(SorteBonus s) => s switch
    {
        SorteBonus.Double => "defense-bonus-double", SorteBonus.Bouclier => "defense-bonus-bouclier", _ => "defense-bonus-ralenti",
    };

    // L'allure de Pilou dans le jeu : concentré, grimace quand il est touché, content entre deux vagues.
    public static Allure AllurePilou(Allure fond, PartieDefense p, double t, ResultatDefense? r)
    {
        var a = fond.Copie();
        a.T = t;
        a.Expr = p.Phase switch
        {
            PhaseDefense.Accueil => "repos",
            PhaseDefense.Pause => "attente",
            PhaseDefense.EntreVagues => "fete",
            PhaseDefense.Fin => r?.Record == true ? "fete" : "soulage",
            _ => p.Invuln > 0.8 ? "grimace" : "concentre",
        };
        a.Marche = Math.Abs(p.VitesseJoueur) > 12 && p.Phase is PhaseDefense.Jeu or PhaseDefense.EntreVagues;
        a.Regard = Math.Abs(p.VitesseJoueur) > 12 ? Math.Sign(p.VitesseJoueur) : 0;
        a.RegardY = p.Phase == PhaseDefense.Jeu ? -1 : 0;
        a.Salue = p.Phase == PhaseDefense.EntreVagues;
        a.Saut = p.Phase == PhaseDefense.EntreVagues ? Math.Abs(Math.Sin(t / 160)) * 2 : 0;
        a.Dos = false;
        a.Boude = false;
        return a;
    }

    public static void Dessiner(ToileDefense o, PartieDefense p, Banque b, uint[] pilou, Geometrie geo, double t, VueDefense v)
    {
        int w = o.W, h = o.H;
        o.Dx = o.Dy = 0;
        o.Vider(Voile);
        if (v.Alerte > 0 && !v.FlashsReduits) o.Dx = (int)t / 40 % 2 == 0 ? 1 : -1;

        // Ligne du bureau : si la formation la touche, le bureau est envahi.
        for (int x = 2; x < w - 2; x += 6) o.Rect(x, (int)p.LigneBureau, 3, 1, 0x50b8c4d2);

        foreach (var a in p.Abris) DessinerAbri(o, a);

        // Bugs : la formation balance d'un pixel, les libres suivent leur trajet.
        foreach (var bug in p.Bugs)
        {
            if (!bug.Vivant) continue;
            int dy = bug.EnFormation && (int)(t / 400 + bug.Col) % 2 == 0 ? 1 : 0;
            Poser(o, b, IdBug(bug), t + bug.Col * 37, (int)Math.Round(bug.X), (int)Math.Round(bug.Y) + dy, PartieDefense.Teinte(bug.Sorte),
                (int)bug.L, (int)bug.Ht);
        }
        if (p.Boss is { } boss)
        {
            bool faible = boss.Pv < boss.PvMax / 3 && !v.FlashsReduits && (int)(t / 140) % 2 == 0;
            Poser(o, b, "bug-prod", t, (int)Math.Round(boss.X), (int)Math.Round(boss.Y), Orange, 36, 22, 2, 1, faible ? 0x66ffffffu : 0u);
            int l = Math.Min(160, w / 3), x0 = (w - l) / 2, y0 = PartieDefense.Hud + 2;
            o.Rect(x0 - 1, y0 - 1, l + 2, 5, Argent);
            o.Rect(x0, y0, l, 3, Encre);
            o.Rect(x0, y0, (int)Math.Round(l * boss.Pv / (double)boss.PvMax), 3, Orange);
        }

        foreach (var x in p.Bonus)
        {
            int bob = (int)(t / 300) % 2;
            Poser(o, b, IdBonus(x.Sorte), t, (int)Math.Round(x.X), (int)Math.Round(x.Y) + bob, Violet, 12, 12);
        }
        foreach (var tir in p.Tirs)
        {
            if (tir.Ami) Poser(o, b, "defense-etincelle", t, (int)Math.Round(tir.X) - 1, (int)Math.Round(tir.Y), Orange, 3, 9);
            else Poser(o, b, "defense-tir", t, (int)Math.Round(tir.X) - 3, (int)Math.Round(tir.Y), Violet, 7, 7);
        }
        foreach (var e in p.Eclats) o.Point((int)Math.Round(e.X), (int)Math.Round(e.Y), ToileDefense.Opacite(e.Couleur, Math.Min(1, e.Vie * 3)));

        // Pilou : il clignote après un coup (ou, flashs réduits, il pâlit simplement).
        double op = 1;
        if (p.Invuln > 0 && p.Phase == PhaseDefense.Jeu) op = v.FlashsReduits ? 0.55 : (int)(t / 90) % 2 == 0 ? 0.2 : 1;
        int px = (int)Math.Round(p.JoueurX) - RenduPilou.C, py = (int)Math.Round(p.Sol) - Math.Max(40, geo.Pied);
        if (pilou.Length == RenduPilou.W * RenduPilou.H) o.Image(pilou, RenduPilou.W, RenduPilou.H, px, py, op);
        else o.Rect((int)(p.JoueurX - PartieDefense.JoueurL / 2), (int)p.HautJoueur, (int)PartieDefense.JoueurL, (int)PartieDefense.JoueurH, Bleu);
        if (p.Bouclier > 0)
        {
            double cx = p.JoueurX, cy = p.Sol - 18;
            for (int i = 0; i < 20; i++)
            {
                double an = i * Math.PI / 10 + (v.FlashsReduits ? 0 : t / 500);
                o.Point((int)Math.Round(cx + Math.Cos(an) * 20), (int)Math.Round(cy + Math.Sin(an) * 21), i % 2 == 0 ? BleuClair : Bleu);
            }
        }

        o.Dx = o.Dy = 0;
        CadreRetro(o, v.Alerte > 0 && !v.FlashsReduits ? Orange : Bleu);
        DessinerBandeau(o, p, b, t, v);
        if (v.Flash > 0 && !v.FlashsReduits) o.Rect(0, 0, w, h, ToileDefense.Opacite(0x40fff6cc, v.Flash));

        switch (p.Phase)
        {
            case PhaseDefense.Accueil: Accueil(o, b, t, v); break;
            case PhaseDefense.Pause:
                Boite(o, w / 2 - 90, h / 2 - 24, 180, 40);
                o.Centre("PAUSE", w / 2, h / 2 - 16, Bleu, 3, Encre);
                o.Centre("CLIQUE OU ESPACE POUR REPRENDRE", w / 2, h / 2 + 4, Creme, 1, Encre);
                break;
            case PhaseDefense.EntreVagues:
            {
                bool suivanteBoss = PartieDefense.VagueDeBoss(p.Vague + 1);
                Boite(o, w / 2 - 110, h / 2 - 30, 220, 36);
                o.Centre(suivanteBoss ? "ATTENTION : BUG DE PROD" : $"VAGUE {p.Vague + 1}", w / 2, h / 2 - 22, suivanteBoss ? Orange : BleuClair, 2, Encre);
                o.Centre($"VAGUE {p.Vague} FRANCHIE : +{50 * p.Vague}", w / 2, h / 2 - 6, OrangeClair, 1, Encre);
                break;
            }
            case PhaseDefense.Fin: Fin(o, p, v); break;
        }
    }

    // Cadre rétro : double trait pixel, coins orange en équerre.
    private static void CadreRetro(ToileDefense o, uint c)
    {
        int w = o.W, h = o.H;
        o.Cadre(0, 0, w, h, Marine);
        o.Cadre(1, 1, w - 2, h - 2, c);
        foreach (var (x, y, sx, sy) in new[] { (0, 0, 1, 1), (w - 1, 0, -1, 1), (0, h - 1, 1, -1), (w - 1, h - 1, -1, -1) })
        {
            for (int i = 0; i < 6; i++)
            {
                o.Point(x + sx * i, y, Orange);
                o.Point(x, y + sy * i, Orange);
                o.Point(x + sx * i, y + sy, OrangeClair);
                o.Point(x + sx, y + sy * i, OrangeClair);
            }
        }
    }

    private static void DessinerAbri(ToileDefense o, Abri a)
    {
        for (int r = 0; r < a.Lignes; r++)
        for (int c = 0; c < a.Colonnes; c++)
        {
            int pv = a.Pv[r, c];
            if (pv <= 0) continue;
            char k = a.Sorte[r, c];
            bool abime = pv < a.PvMax(r, c);
            uint couleur = a.EstFenetre
                ? k switch
                {
                    'b' => abime ? Marine : BleuFonce,
                    'p' => abime ? Argent : Creme,
                    'c' => abime ? Gris : Argent,
                    _ => (r + c) % 5 == 0 ? 0xe0f6f8fa : 0xc8b4dbff, // vitre, un reflet en biais
                }
                : k switch { 'l' => JauneFonce, 'f' => 0xffa8862a, _ => (r + c) % 7 == 0 ? JaunePale : Jaune };
            int x = (int)a.X + c * Abri.Case, y = (int)a.Y + r * Abri.Case;
            o.Rect(x, y, Abri.Case, Abri.Case, couleur);
            if (abime) o.Point(x + (r + c) % 2, y + 1, Encre); // fêlure
        }
    }

    private static void DessinerBandeau(ToileDefense o, PartieDefense p, Banque b, double t, VueDefense v)
    {
        int w = o.W, hud = PartieDefense.Hud;
        o.Rect(2, 2, w - 4, hud - 2, Bandeau);
        o.Rect(2, hud, w - 4, 1, Marine);
        int y = 5;
        o.Texte($"SCORE {p.Score:000000}", 6, y, Orange);
        int x = 6 + ToileDefense.Largeur($"SCORE {p.Score:000000}") + 8;
        var record = $"RECORD {Math.Max(v.Meilleur, v.Demo ? 0 : p.Score)}";
        if (v.Demo) record = "DEMO : PILOU JOUE SEUL";
        o.Texte(record, x, y, Gris);
        x += ToileDefense.Largeur(record) + 10;
        if (p.Phase != PhaseDefense.Accueil)
        {
            bool boss = p.Boss is not null;
            var vague = boss ? $"VAGUE {p.Vague} : BUG DE PROD" : $"VAGUE {Math.Max(1, p.Vague)}";
            o.Texte(vague, x, y, boss ? Orange : BleuClair);
            x += ToileDefense.Largeur(vague) + 10;
            if (p.Combo >= 2)
            {
                var combo = $"COMBO {p.Combo}" + (p.Multiplicateur > 1 ? $" x{p.Multiplicateur.ToString("0.#", System.Globalization.CultureInfo.InvariantCulture)}" : "");
                o.Texte(combo, x, y, VioletClair);
            }
        }
        // À droite : bonus en cours (icône et durée), vies, bouton ✕.
        int d = w - 18;
        var ferme = Fermer(w);
        o.Rect((int)ferme.X, (int)ferme.Y, (int)ferme.Largeur, (int)ferme.Hauteur, Encre);
        o.Cadre((int)ferme.X, (int)ferme.Y, (int)ferme.Largeur, (int)ferme.Hauteur, Argent);
        for (int i = 0; i < 6; i++)
        {
            o.Point((int)ferme.X + 3 + i, (int)ferme.Y + 3 + i, Creme);
            o.Point((int)ferme.X + 8 - i, (int)ferme.Y + 3 + i, Creme);
        }
        for (int i = 0; i < p.Vies; i++)
        {
            d -= 12;
            Poser(o, b, "vie", t, d, 3, Orange, 10, 9);
        }
        d -= 4;
        foreach (var (reste, duree, sorte) in new[] { (p.Ralenti, PartieDefense.DureeRalenti, SorteBonus.Ralenti),
                     (p.Bouclier, PartieDefense.DureeBouclier, SorteBonus.Bouclier), (p.Double, PartieDefense.DureeDouble, SorteBonus.Double) })
        {
            if (reste <= 0) continue;
            d -= 15;
            Poser(o, b, IdBonus(sorte), t, d, 1, Violet, 12, 12);
            o.Rect(d, hud - 1, (int)Math.Ceiling(12 * reste / duree), 1, Creme);
        }
        if (v.IaAttend)
        {
            const string texte = "! UNE IA T'ATTEND";
            int l = ToileDefense.Largeur(texte) + 8;
            if (!v.FlashsReduits && (int)(t / 600) % 2 == 1) return;
            o.Rect(w / 2 - l / 2, hud + 3, l, 9, FondBoite);
            o.Cadre(w / 2 - l / 2, hud + 3, l, 9, Orange);
            o.Centre(texte, w / 2, hud + 5, Orange);
        }
    }

    private static void Boite(ToileDefense o, int x, int y, int l, int h)
    {
        o.Rect(x, y, l, h, FondBoite);
        o.Cadre(x, y, l, h, Marine);
        o.Cadre(x + 1, y + 1, l - 2, h - 2, Bleu);
    }

    private static void Bouton(ToileDefense o, Clics.Zone z, string texte, uint c)
    {
        o.Rect((int)z.X, (int)z.Y, (int)z.Largeur, (int)z.Hauteur, c);
        o.Rect((int)z.X + 1, (int)z.Y + 1, (int)z.Largeur - 2, (int)z.Hauteur - 2, Encre);
        o.Centre(texte, (int)(z.X + z.Largeur / 2), (int)(z.Y + (z.Hauteur - 5) / 2), c);
    }

    private static void Accueil(ToileDefense o, Banque b, double t, VueDefense v)
    {
        int w = o.W, cx = w / 2, y = Haut(o.H);
        Boite(o, cx - 150, y, 300, 132);
        o.Centre("DÉFENSE", cx, y + 8, Orange, 3, Encre);
        o.Centre("DU BUREAU", cx, y + 27, Bleu, 3, Encre);
        // Les bugs et ce qu'ils valent.
        var bugs = new (string Id, string Points)[]
        {
            ("bug-scarabee", "30"), ("bug-araignee", "20"), ("bug-ver", "10"), ("defense-blinde", "40"), ("defense-diviseur", "20"),
            ("defense-rapide", "50"),
        };
        int x0 = cx - bugs.Length * 30 / 2;
        for (int i = 0; i < bugs.Length; i++)
        {
            Poser(o, b, bugs[i].Id, t + i * 90, x0 + i * 30 + 6, y + 46, Violet, 18, 14);
            o.Centre(bugs[i].Points, x0 + i * 30 + 15, y + 62, Gris);
        }
        // Les bonus.
        var bonus = new (SorteBonus S, string Nom)[] { (SorteBonus.Double, "TIR DOUBLE"), (SorteBonus.Bouclier, "BOUCLIER"), (SorteBonus.Ralenti, "RALENTI") };
        int bx = cx - 135;
        foreach (var (s, nom) in bonus)
        {
            Poser(o, b, IdBonus(s), t, bx, y + 72, Violet, 12, 12);
            o.Texte(nom, bx + 15, y + 76, OrangeClair);
            bx += 15 + ToileDefense.Largeur(nom) + 22;
        }
        o.Centre("SOURIS OU FLÈCHES / Q D : BOUGER    CLIC OU ESPACE : TIRER", cx, y + 90, Creme);
        o.Centre("P : PAUSE    ÉCHAP, CLIC DROIT OU X : QUITTER", cx, y + 99, Creme);
        var f = Flashs(w, o.H);
        o.Centre(v.FlashsReduits ? "FLASHS RÉDUITS : OUI (F)" : "FLASHS RÉDUITS : NON (F)", cx, (int)f.Y + 2, BleuClair);
        if (v.FlashsReduits || (int)(t / 500) % 2 == 0) o.Centre(v.Demo ? "DÉMO" : "CLIQUE POUR COMMENCER", cx, y + 110, Orange);
    }

    private static void Fin(ToileDefense o, PartieDefense p, VueDefense v)
    {
        int w = o.W, cx = w / 2, y = Haut(o.H);
        Boite(o, cx - 150, y, 300, 132);
        o.Centre("PARTIE TERMINÉE", cx, y + 8, Orange, 2, Encre);
        o.Centre(p.Fin.Replace("…", ""), cx, y + 24, Argent);
        o.Centre($"SCORE {p.Score}", cx, y + 36, Creme, 2, Encre);
        bool record = v.Resultat?.Record == true;
        o.Centre(record ? "NOUVEAU RECORD !" : $"RECORD {Math.Max(v.Meilleur, 0)}", cx, y + 54, record ? Orange : Gris);
        o.Centre($"VAGUE {p.VagueAtteinte}    BUGS {p.BugsTues}    COMBO MAX {p.ComboMax}", cx, y + 64, BleuClair);
        if (v.Demo) o.Centre("DÉMO : AUCUN GAIN", cx, y + 78, Gris);
        else if (v.Resultat is { } r)
        {
            o.Centre($"+{r.Xp} XP    +{r.Po} PO", cx, y + 78, OrangeClair, 1, Encre);
            if (r.Plafond) o.Centre("PLAFOND DU JOUR ATTEINT : REVIENS DEMAIN", cx, y + 88, Gris);
        }
        Bouton(o, Rejouer(w, o.H), "REJOUER", Orange);
        Bouton(o, Quitter(w, o.H), "QUITTER", Argent);
    }
}
