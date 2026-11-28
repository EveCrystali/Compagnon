package fr.pilou.compagnon;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Pilou en pixels : corps procédural (ombrage tramé, reflet, cerne), visage, antenne, et tout ce qu'il porte,
 * tiré de la banque de sprites. Même règle que RenduPilou.cs (PC) et outils/sprites/rendu.py. Deux échelles :
 * 1 (grille 48 × 56, le rendu de toujours) et 2 (rendu fin, grille 96 × 112 : corps calculé à la finesse double,
 * sprites d'assets/sprites2x ou, à défaut, sprites 1× agrandis par Sprites.agrandir).
 */
public final class RenduPilou {
    public static final int W = 48, H = 56, C = 24;
    public static final double K = 1.25 * 48 / 26;
    /** Tenues de voyage des campagnes (docs/CAMPAGNES.md) : Allure.tenue = "voyage-" + mode. */
    public static final List<String> VOYAGES = Collections.unmodifiableList(
            Arrays.asList("marche", "course", "bateau", "grimpe", "nage", "nuit", "cache", "attend"));
    /** Humeurs des campagnes (Allure.expr), en plus des humeurs d'origine. */
    public static final List<String> HUMEURS = Collections.unmodifiableList(
            Arrays.asList("joie", "peur", "triste", "surpris", "determine", "fatigue", "tendre", "colere", "malice", "neutre"));
    private static final int JOUE = 0xffffb37a, JOUE_CLAIRE = 0xffffc89a, OMBRE_SOL = 0x33000000, SILHOUETTE = 0xffe8f4ff,
            SILHOUETTE_BORD = 0xff6cb6ff, GOUTTE = 0xff1f4f8a, GOUTTE_CLAIRE = 0xffb4dbff, BLANC = 0xffffffff;
    private static final int[] ECLAT = {0xffffd8b0, 0xfffff6cc, 0xffb4dbff};
    private static final List<String> ORDRE = Arrays.asList("dos", "cou", "visage", "yeux", "tete", "main", "compagnon", "effet", "objet");
    private static final Set<String> CHAUDES = new HashSet<>(Arrays.asList("ambre", "braise", "comete", "corail-orange", "sable", "mandarine", "miel", "peche", "caramel", "potiron", "cuivre"));
    private static final int[] BLEU = {0xff1f4f8a, 0xff4a8fdc, 0xff6cb6ff, 0xffb4dbff};
    private static final int[] ORANGE = {0xff8a4a1f, 0xffd9803a, 0xfff69d50, 0xffffc89a};
    private static final int[][] CROIX = {{0, 0}, {-1, 0}, {1, 0}, {0, -1}, {0, 1}};
    // Dessins fins (2×) des petites formes que le rendu pose lui-même. « # » : couleur demandée.
    private static final String[] ETOILE_FINE = {"...#...", "...#...", "..###..", "#######", "..###..", "...#...", "...#..."};
    private static final String[] JOUE_FINE = {".####.", "######", "#o####", ".####."};
    private static final String[] GOUTTE_NIMBUS_FINE = {"..c..", "..c..", ".clc.", ".clc.", "clbbc", "cbbbc", ".ccc."};
    private static final String[] SUEUR_FINE = {"..gg..", "..gg..", ".gccg.", ".gccg.", "gcwccg", "gcwccg", "gccccg", ".gggg."};
    private static final int[] OMBRE_FINE = {2, 0, 3, 7}, PIED_FIN = {0, 0, 1, 3}, GUET = {-1, 0, 1, 0};

    /** Ce qu'on demande au dessin. */
    public static final class Allure implements Cloneable {
        /** repos, concentre, attente, grimace, fete, soulage, dort, inquiet, caresse ; humeurs des campagnes : HUMEURS.
         *  tenue : tenue d'activité (assets/tenues.txt) ou tenue de voyage « voyage-<mode> » (VOYAGES). */
        public String expr = "repos", couleur = "bleu", accessoire = "", tenue = "", reaction = "";
        public double t, saut, chute, assis, suspendu, tremble, evolution;
        public List<String> objets = Collections.emptyList();
        public boolean cligne, clin, marche, course, baille, etourdi, fatigue, salue;
        /** Bouche ouverte : le Théâtre HD fait parler le Pilou du bureau (docs/SCENES-HD.md). */
        public boolean parle;
        /** Il boude (moue, sourcils froncés au repos) ; dos tourné (pas de visage). */
        public boolean boude, dos;
        public int regard, regardY, stade = 2;
        /** Vie du personnage (Vie.java) : étirement du corps (−1 écrasé … 1 étiré), retard de l'antenne (−1 … 1,
         *  positif : pointe plus haute), ms depuis l'atterrissage (−1 : aucun), lumière du moment (« matin », « soir »,
         *  « nuit » ou "") ; vie : animations complètes (ombre tramée en l'air, bouffées de poussière). */
        public double etire, antenne, atterri = -1;
        public String lumiere = "";
        public boolean vie;

        public Allure copie() {
            try {
                return (Allure) clone();
            } catch (CloneNotSupportedException e) {
                throw new AssertionError(e);
            }
        }
    }

    /** Points utiles autour de Pilou (pixels de la grille 48 × 56, quelle que soit l'échelle du rendu). */
    public static final class Geometrie {
        public double cx, cy, rx, ry;
        public int sommet, ey, pied;
    }

    /** Espace de travail d'un rendu, à garder d'une image à l'autre pour ne rien allouer (vues animées).
     *  L'image rendue est celle du tampon : elle est réécrite au rendu suivant fait avec lui. */
    public static final class Tampon {
        int[] g = new int[0], m = new int[0];
        boolean[] bord = new boolean[0];

        void preparer(int n) {
            if (g.length != n) {
                g = new int[n];
                m = new int[n];
                bord = new boolean[n];
            } else {
                Arrays.fill(g, 0);
                Arrays.fill(m, 0);
            }
        }
    }

    private RenduPilou() {
    }

    static double stadeX(int s) {
        return s == 1 ? 0.72 : s == 3 ? 1.1 : s == 4 ? 0.9 : 1.0;
    }

    static double stadeY(int s) {
        return s == 1 ? 0.74 : s == 4 ? 1.2 : 1.0;
    }

    static String nomOeil(String expr) {
        switch (expr) {
            case "concentre": return "concentre";
            case "attente": return "haut";
            case "grimace": return "grimace";
            case "fete": case "caresse": case "joie": return "heureux";
            case "soulage": return "content";
            case "dort": return "dort";
            case "inquiet": return "inquiet";
            case "peur": case "triste": case "surpris": case "determine": case "fatigue": case "tendre": case "colere": case "malice":
                return expr;
            default: return "";
        }
    }

    private static String etincelle(String expr) {
        switch (expr) {
            case "concentre": case "attente": return "etincelle-roue";
            case "grimace": return "etincelle-x";
            case "dort": case "fatigue": return "etincelle-dort";
            case "inquiet": case "surpris": return "etincelle-alerte";
            case "caresse": case "tendre": return "etincelle-coeur";
            default: return null;
        }
    }

    public static int[] teinte(Allure a, Sprites.Banque b) {
        if (a.expr.equals("inquiet")) {
            int[] t = b.teintes.get(CHAUDES.contains(a.couleur) ? "bleu" : "orange");
            return t != null ? t : CHAUDES.contains(a.couleur) ? BLEU : ORANGE;
        }
        int[] t = b.teintes.get(a.couleur);
        if (t == null) t = b.teintes.get("bleu");
        return t != null ? t : BLEU;
    }

    /** Arrondi « au pair », comme le C# et le Python : les trois rendus tombent sur les mêmes pixels. */
    static int rond(double v) {
        return (int) Math.rint(v);
    }

    /**
     * Tenue de voyage « voyage-<mode> » : la pose que le mode impose (il marche sur place, rame, grimpe, dort…).
     * Ce que l'appelant a déjà demandé (regard, humeur) est gardé quand le mode ne dit rien.
     */
    public static Allure voyager(Allure p) {
        if (p.tenue == null || !p.tenue.startsWith("voyage-")) return p;
        String mode = p.tenue.substring(7);
        if (!VOYAGES.contains(mode)) return p;
        double t = p.t;
        Allure q = p.copie();
        switch (mode) {
            case "marche":
                q.marche = true;
                q.regard = p.regard != 0 ? p.regard : 1;
                break;
            case "course":
                q.marche = q.course = true;
                q.regard = p.regard != 0 ? p.regard : 1;
                break;
            case "bateau":
                q.assis = 1.0;
                q.saut = 0.5 + 0.5 * Math.sin(t / 520);        // tangage
                q.regard = p.regard != 0 ? p.regard : 1;
                break;
            case "grimpe":
                q.saut = 2.0 + 1.2 * Math.abs(Math.sin(t / 420)); // il se hisse, bras après bras
                q.regardY = -1;
                break;
            case "nage":
                q.assis = 1.0;
                q.saut = 0.4 + 0.4 * Math.sin(t / 450);
                break;
            case "nuit":
                q.expr = "dort";
                break;
            case "cache":
                q.assis = 1.0;
                q.chute = 0.25;
                q.regard = GUET[Math.floorMod((int) Math.floor(t / 900), 4)]; // il guette d'un côté puis de l'autre
                break;
            default: { // attend : il regarde sa montre, puis relève les yeux
                boolean leve = Math.floorMod((int) Math.floor(t / 1400), 3) == 2;
                q.assis = 1.0;
                q.regardY = leve ? 0 : 1;
                q.regard = leve ? p.regard : -1;
                break;
            }
        }
        return q;
    }

    /** Image ARGB H × W (grille 48 × 56), ligne par ligne, animation d'évolution comprise. */
    public static int[] rendre(Allure a, Sprites.Banque b, Geometrie geo) {
        return rendre(a, b, geo, 1, null);
    }

    /** Échelle 1 (48 × 56) ou 2 (rendu fin, 96 × 112). */
    public static int[] rendre(Allure a, Sprites.Banque b, Geometrie geo, int echelle) {
        return rendre(a, b, geo, echelle, null);
    }

    /** Avec un tampon réutilisé (l'image rendue est alors celle du tampon, réécrite au rendu suivant). */
    public static int[] rendre(Allure a, Sprites.Banque b, Geometrie geo, int echelle, Tampon tampon) {
        int ec = echelle == 2 ? 2 : 1;
        a = voyager(a);
        double e = a.evolution;
        if (e > 0 && e < 1 && a.stade > 1) {
            if (e < 0.85) {
                int k = (int) (Math.pow(e / 0.85, 2) * 12) % 2;
                Allure q = a.copie();
                q.stade = k == 0 ? a.stade - 1 : a.stade;
                q.evolution = 0;
                q.expr = "repos";
                return silhouetter(rendreStade(q, b, geo, ec, null), ec);
            }
            Allure n = a.copie();
            n.evolution = 0;
            int[] g = rendreStade(n, b, geo, ec, tampon);
            eclats(g, (e - 0.85) / 0.15, ec);
            return g;
        }
        return rendreStade(a, b, geo, ec, tampon);
    }

    private static boolean vide(int[] g, int x, int y, int w, int h) {
        return x < 0 || y < 0 || x >= w || y >= h || g[y * w + x] == 0 || g[y * w + x] == OMBRE_SOL;
    }

    private static int[] silhouetter(int[] g, int ec) {
        int w = W * ec, h = H * ec;
        int[] o = new int[w * h];
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++) {
                int c = g[y * w + x];
                if (c == 0 || c == OMBRE_SOL) {
                    o[y * w + x] = c;
                    continue;
                }
                boolean bord = false;
                for (int n = 1; n <= ec; n++)
                    bord |= vide(g, x + n, y, w, h) || vide(g, x - n, y, w, h) || vide(g, x, y + n, w, h) || vide(g, x, y - n, w, h);
                o[y * w + x] = bord ? SILHOUETTE_BORD : SILHOUETTE;
            }
        return o;
    }

    /** Petite étoile centrée en (x, y) : croix de 3 pixels à l'échelle 1, étoile à quatre branches de 7 pixels en fin. */
    private static void etoileDans(int[] g, int x, int y, int c, int ec) {
        int w = W * ec, h = H * ec;
        if (ec == 1) {
            for (int[] d : CROIX)
                if (x + d[0] >= 0 && x + d[0] < W && y + d[1] >= 0 && y + d[1] < H) g[(y + d[1]) * W + x + d[0]] = c;
            return;
        }
        for (int j = 0; j < 7; j++)
            for (int i = 0; i < 7; i++)
                if (ETOILE_FINE[j].charAt(i) == '#' && x + i - 3 >= 0 && x + i - 3 < w && y + j - 3 >= 0 && y + j - 3 < h)
                    g[(y + j - 3) * w + x + i - 3] = c;
    }

    private static void eclats(int[] g, double k, int ec) {
        double r = (4 + k * 20) * ec;
        for (int i = 0; i < 12; i++) {
            double an = i * Math.PI / 6;
            int x = rond(C * ec + Math.cos(an) * r), y = rond(36 * ec + Math.sin(an) * r * 0.85);
            etoileDans(g, x, y, ECLAT[i % 3], ec);
        }
    }

    /** Ton du corps au rendu fin (indice dans la teinte : 1 ombre, 2 base, 3 clair). Trame à trois paliers (un quart,
     *  un demi, trois quarts) au lieu du seul damier, ombre qui épouse le volume, reflet en croissant. */
    private static int tonFin(int x, int y, double u, double v, double r2) {
        double d2 = (u + 0.62) * (u + 0.62) + (v + 0.62) * (v + 0.62);
        if (r2 > 0.47 && d2 < 0.2025) return 3;
        if (r2 > 0.40 && d2 < 0.16 && (x + y) % 2 == 0) return 3;
        double s = v + 0.16 * u * u;
        if (s > 0.66) return 1;
        if (s > 0.58) return x % 2 == 0 && y % 2 == 1 ? 2 : 1;
        if (s > 0.50) return (x + y) % 2 == 0 ? 1 : 2;
        if (s > 0.42) return x % 2 == 0 && y % 2 == 0 ? 1 : 2;
        return 2;
    }

    private static final class Toile {
        final int[] g;
        final int w, h;
        int[] te;
        double t;

        Toile(int[] g, int w, int h) {
            this.g = g;
            this.w = w;
            this.h = h;
        }

        void px(int x, int y, int c) {
            if (c != 0 && x >= 0 && y >= 0 && x < w && y < h) g[y * w + x] = c;
        }

        void poser(Sprites.Sprite s, boolean miroir, int x, int y, String[] im) {
            if (im == null) im = s.image(t);
            int[] pal = s.compilee();
            for (int j = 0; j < im.length; j++) {
                String l = im[j];
                int n = l.length();
                for (int i = 0; i < n; i++) {
                    char ch = l.charAt(i);
                    if (ch == '.' || ch >= 128) continue;
                    int c = pal[ch];
                    if (c == 0) continue;
                    if (c >= 1 && c <= 4) c = te[c - 1];
                    px(x + (miroir ? n - 1 - i : i), y + j, c);
                }
            }
        }

        /** Motif fin posé par le rendu : lettres (jusqu'à trois) et leurs couleurs. */
        void motif(int x, int y, String[] lignes, char l1, int c1, char l2, int c2, char l3, int c3) {
            for (int j = 0; j < lignes.length; j++) {
                String l = lignes[j];
                for (int i = 0; i < l.length(); i++) {
                    char ch = l.charAt(i);
                    if (ch == l1) px(x + i, y + j, c1);
                    else if (ch == l2) px(x + i, y + j, c2);
                    else if (ch == l3) px(x + i, y + j, c3);
                }
            }
        }

        void etoile(int x, int y, int c, int ec) {
            if (ec == 1)
                for (int[] d : CROIX) px(x + d[0], y + d[1], c);
            else motif(x - 3, y - 3, ETOILE_FINE, '#', c, '#', c, '#', c);
        }
    }

    private static int rang(Sprites.Sprite s) {
        int r = ORDRE.indexOf(s.slot);
        return r >= 0 ? r : 9;
    }

    private static int[] rendreStade(Allure a, Sprites.Banque b, Geometrie geo, int ec, Tampon tampon) {
        int w = W * ec, h = H * ec, c0 = C * ec;
        int[] g, m;
        if (tampon == null) {
            g = new int[w * h];
            m = new int[w * h];
        } else {
            tampon.preparer(w * h);
            g = tampon.g;
            m = tampon.m;
        }
        Toile to = new Toile(g, w, h);
        int st = a.stade >= 1 && a.stade <= 4 ? a.stade : 2;
        int[] te = teinte(a, b);
        if (a.lumiere != null && !a.lumiere.isEmpty() && !a.expr.equals("inquiet")) te = Vie.eclairer(te, a.lumiere); // l'alerte garde sa couleur franche
        to.te = te;
        double t = a.t;
        to.t = t;
        double periode = a.expr.equals("dort") ? 4200 : a.expr.equals("concentre") || a.expr.equals("attente") ? 1600 : 2600;
        double bb = Math.sin(2 * Math.PI * t / periode);
        double rx = 6.8 - 0.2 * bb, ry = 5.6 + 0.3 * bb;
        if (a.expr.equals("caresse")) { rx += 0.5; ry -= 0.5; }
        if (a.expr.equals("dort")) { rx += 0.6; ry -= 0.9; }
        rx += 1.2 * a.chute + 0.7 * a.assis - 0.8 * a.suspendu;
        ry -= 1.4 * a.chute + 0.8 * a.assis - 1.1 * a.suspendu;
        rx -= 0.9 * a.etire;
        ry += 1.1 * a.etire;
        rx *= stadeX(st);
        ry *= stadeY(st);
        double cadence = a.course ? 70 : 160;
        double marche = a.marche ? Math.abs(Math.sin(t / cadence)) * (a.course ? 1.3 : 0.8) : 0;
        double sol = (21.6 - a.saut - marche + a.assis) * K;
        double cx = C + (a.tremble + a.suspendu * Math.sin(t / 260) * 1.2) * K;
        rx *= K;
        ry *= K;
        // Rendu fin : les mêmes grandeurs, deux fois plus grandes ; tout ce qui suit s'arrondit au pixel fin.
        if (ec != 1) {
            sol *= ec;
            cx = c0 + (cx - C) * ec;
            rx *= ec;
            ry *= ec;
        }
        double cy = sol - ry;
        int dx = rond(cx - c0);

        List<String> ids = new ArrayList<>();
        if (st == 4) ids.add("astral-cape");
        if (a.accessoire != null && !a.accessoire.isEmpty() && !a.accessoire.equals("aucun")) ids.add("acc-" + a.accessoire);
        if (a.tenue != null && !a.tenue.isEmpty()) {
            String[] tenue = b.tenues.get(a.tenue);
            if (tenue != null) ids.addAll(Arrays.asList(tenue));
        }
        if (a.objets != null) ids.addAll(a.objets);
        List<Sprites.Sprite> portes = new ArrayList<>();
        boolean coiffe = false;
        for (String id : ids) {
            Sprites.Sprite s = b.get(id, ec);
            if (s == null || (a.dos && (s.slot.equals("visage") || s.slot.equals("yeux")))) continue;
            portes.add(s);
            coiffe |= s.coiffe;
        }
        Collections.sort(portes, (p, q) -> Integer.compare(rang(p), rang(q)));

        int pied = rond(sol);
        int sommet = (int) Math.ceil(cy - ry);
        int ey = (int) Math.floor(cy - 6.6 * stadeY(st) * ec) + a.regardY * 2 * ec;
        int dxf = dx + a.regard * 2 * ec;
        double vitesse = a.salue || a.expr.equals("fete") ? 90 : a.expr.equals("concentre") ? 300 : 650;
        int balance = a.expr.equals("dort") ? 0
                : Math.max(-ec, Math.min(ec, rond(Math.sin(t / vitesse) * 0.9 * ec) + (a.marche ? -Integer.signum(a.regard) * ec : 0)));
        int hautAntenne = Math.max(2 * ec, (st == 1 ? 3 : 6) * ec + rond(a.antenne * 2 * ec));
        if (geo != null) {
            geo.cx = cx / ec; geo.cy = cy / ec; geo.rx = rx / ec; geo.ry = ry / ec;
            geo.sommet = Math.floorDiv(sommet, ec); geo.ey = Math.floorDiv(ey, ec); geo.pied = Math.floorDiv(pied, ec);
        }

        // Ancres (x puis y), dans l'ordre d'ANCRES : tete, yeux, bouche, cou, corps, main, main-g, pieds, cote, antenne.
        int[] ancres = {
                c0 + dx, sommet, c0 + dxf, ey, c0 + dxf, ey + 9 * ec, c0 + dx, rond(cy + ry * 0.45), c0 + dx, rond(cy),
                rond(cx + rx) - ec, rond(cy + ry * 0.15), rond(cx - rx), rond(cy + ry * 0.15), c0 + dx, pied,
                rond(cx + rx * 0.45), pied + 2 * ec, c0 + dx + 2 * balance, sommet - hautAntenne,
        };

        // Astral : couronne d'étincelles en orbite.
        List<int[]> orbite = new ArrayList<>();
        if (st == 4)
            for (int i = 0; i < 5; i++) {
                double an = t / 700 + i * 2 * Math.PI / 5;
                orbite.add(new int[]{rond(cx + Math.cos(an) * (rx + 4 * ec)), rond(sommet + 4 * ec + Math.sin(an) * 3.5 * ec),
                        Math.sin(an) > 0 ? 1 : 0, ECLAT[i % 3]});
            }

        for (Sprites.Sprite s : portes)
            if (s.derriere) poserAncre(to, s, ancres);
        for (int[] o : orbite)
            if (o[2] == 0) to.etoile(o[0], o[1], o[3], ec);

        // Ombre au sol.
        if (a.suspendu < 0.1) {
            int demi = (int) (Math.max(6, 15 * stadeX(st) - a.saut * 2.8) * ec);
            // Vie : en l'air, l'ombre s'éclaircit en trame (d'abord le bas de l'ombre, puis toute l'ombre).
            int trame = a.vie ? a.saut >= 2.4 ? 2 : a.saut >= 1.0 ? 1 : 0 : 0;
            if (ec == 1) {
                for (int x = C - demi; x < C + demi; x++) {
                    if (x < 0 || x >= W) continue;
                    if (g[52 * W + x] == 0 && ombre(trame, x, 0, false)) g[52 * W + x] = OMBRE_SOL;
                    if (Math.abs(x - C + 0.5) < demi - 3 && g[53 * W + x] == 0 && ombre(trame, x, 1, true)) g[53 * W + x] = OMBRE_SOL;
                }
            } else {
                // Quatre lignes fines, bouts arrondis.
                for (int j = 0; j < 4; j++) {
                    int retrait = OMBRE_FINE[j];
                    for (int x = c0 - demi + retrait; x < c0 + demi - retrait; x++)
                        if (x >= 0 && x < w && g[(104 + j) * w + x] == 0 && ombre(trame, x, j, j >= 2)) g[(104 + j) * w + x] = OMBRE_SOL;
                }
            }
        }

        // Rendu fin : le corps (ellipse, bosses et bras du Nimbus, pieds) tient dans un cadre connu d'avance ; les
        // boucles du corps et du cerne ne parcourent que lui (mêmes pixels qu'en parcourant toute la grille).
        int bx0 = 0, bx1 = w - 1, by0 = 0, by1 = h - 1;
        if (ec != 1) {
            double mg = st == 3 ? 0.3 * ry + 1 : 1;
            double gx0 = cx - rx - mg, gx1 = cx + rx + mg, gy0 = cy - ry - mg, gy1 = cy + ry + mg;
            if (st == 3) {
                double bras = rx + 4.4 * ec + 1;
                gx0 = Math.min(gx0, cx - bras);
                gx1 = Math.max(gx1, cx + bras);
                gy0 = Math.min(gy0, cy + ry * 0.28 - 3.2 * ec - 1);
                gy1 = Math.max(gy1, cy + ry * 0.28 + 3.2 * ec + 1);
            }
            if (a.assis <= 0.5) {
                gx0 = Math.min(gx0, (C - 10) * ec + dx);
                gx1 = Math.max(gx1, (C + 10) * ec + dx);
                gy0 = Math.min(gy0, pied - 2 * ec);
                gy1 = Math.max(gy1, pied + 4 * ec);
            }
            bx0 = Math.max(0, (int) Math.floor(gx0));
            bx1 = Math.min(w - 1, (int) Math.ceil(gx1));
            by0 = Math.max(0, (int) Math.floor(gy0));
            by1 = Math.min(h - 1, (int) Math.ceil(gy1));
        }

        // Corps : ombrage tramé, reflet ; Nimbus : volutes et bras ; puis cerne.
        double[][] bosses = null;
        if (st == 3) {
            int[] degres = {-160, -125, -90, -55, -20, 170, 10};
            bosses = new double[degres.length][];
            for (int i = 0; i < degres.length; i++) {
                double an = degres[i] * Math.PI / 180;
                bosses[i] = new double[]{cx + Math.cos(an) * rx * 0.84, cy + Math.sin(an) * ry * 0.84, ry * (degres[i] < 0 ? 0.3 : 0.24)};
            }
        }
        for (int y = by0; y <= by1; y++)
            for (int x = bx0; x <= bx1; x++) {
                double u = (x + 0.5 - cx) / rx, v = (y + 0.5 - cy) / ry, r2 = u * u + v * v;
                boolean dans = r2 <= 1;
                if (!dans && bosses != null) {
                    for (double[] o : bosses)
                        if (Math.pow(x + 0.5 - o[0], 2) + Math.pow(y + 0.5 - o[1], 2) <= o[2] * o[2]) dans = true;
                    r2 = Math.min(r2, 0.9);
                }
                if (!dans) continue;
                if (ec == 1) {
                    boolean damier = (x + y) % 2 == 0;
                    boolean reflet = u < -0.25 && v < -0.3;
                    m[y * w + x] = reflet && (r2 > 0.45 || (r2 > 0.34 && damier)) ? te[3] : v > 0.62 || (v > 0.46 && damier) ? te[1] : te[2];
                } else {
                    m[y * w + x] = te[tonFin(x, y, u, v, r2)];
                }
            }
        if (st == 3)
            for (int sg = -1; sg <= 1; sg += 2) {
                double bx = cx + sg * (rx + 1.2 * ec), by = cy + ry * 0.28 + Math.sin(t / 300 + sg) * 0.8 * ec;
                for (int y = by0; y <= by1; y++)
                    for (int x = bx0; x <= bx1; x++)
                        if (Math.pow((x + 0.5 - bx) / (3.2 * ec), 2) + Math.pow((y + 0.5 - by) / (2.4 * ec), 2) <= 1) m[y * w + x] = te[1];
            }
        if (a.assis <= 0.5) {
            int pas = a.marche ? (int) (Math.floor(t / cadence) % 2) : -1;
            int largeur = (st == 1 ? 5 : 6) * ec;
            int[][] pieds = st == 1 ? new int[][]{{0, C - 8}, {1, C + 3}} : new int[][]{{0, C - 10}, {1, C + 4}};
            for (int[] pd : pieds) {
                int px0 = pd[1] * ec;
                int haut = pied - (pas == pd[0] ? 2 * ec : 0);
                if (ec == 1) {
                    for (int x = px0; x < px0 + largeur; x++)
                        for (int y = haut; y <= haut + 1; y++)
                            if (x + dx >= 0 && x + dx < W && y >= 0 && y < H && (y == haut || (x > px0 && x < px0 + largeur - 1)))
                                m[y * W + x + dx] = te[1];
                } else {
                    // Pied fin : quatre lignes, semelle arrondie.
                    for (int j = 0; j < 4; j++) {
                        int retrait = PIED_FIN[j];
                        for (int x = px0 + retrait; x < px0 + largeur - retrait; x++)
                            if (x + dx >= 0 && x + dx < w && haut + j >= 0 && haut + j < h) m[(haut + j) * w + x + dx] = te[1];
                    }
                }
            }
        }
        if (ec == 1) {
            for (int y = 0; y < H; y++)
                for (int x = 0; x < W; x++) {
                    int c = m[y * W + x];
                    if (c == 0) continue;
                    boolean bord = x == 0 || y == 0 || x == W - 1 || y == H - 1 || m[y * W + x - 1] == 0 || m[y * W + x + 1] == 0
                            || m[(y - 1) * W + x] == 0 || m[(y + 1) * W + x] == 0;
                    g[y * W + x] = bord ? te[0] : c;
                }
        } else {
            // Cerne fin : deux pixels d'épaisseur, diagonales comprises (tout ce qui est à moins de √5 du vide).
            boolean[] bord1 = tampon != null ? tampon.bord : new boolean[w * h];
            for (int y = by0; y <= by1; y++)
                for (int x = bx0; x <= bx1; x++)
                    bord1[y * w + x] = m[y * w + x] != 0
                            && (x == 0 || y == 0 || x == w - 1 || y == h - 1 || m[y * w + x - 1] == 0 || m[y * w + x + 1] == 0
                            || m[(y - 1) * w + x] == 0 || m[(y + 1) * w + x] == 0);
            // Hors du cadre, tout est vide : le test du vide passe avant la lecture du premier passage.
            for (int y = by0; y <= by1; y++)
                for (int x = bx0; x <= bx1; x++) {
                    int c = m[y * w + x];
                    if (c == 0) continue;
                    boolean bord = x == 0 || y == 0 || x == w - 1 || y == h - 1;
                    for (int v = -1; v <= 1 && !bord; v++)
                        for (int u = -1; u <= 1; u++) {
                            int i = (y + v) * w + x + u;
                            if (m[i] == 0 || bord1[i]) {
                                bord = true;
                                break;
                            }
                        }
                    g[y * w + x] = bord ? te[0] : c;
                }
        }
        if (st == 3)
            for (int sg = -1; sg <= 1; sg += 2)
                for (int k = 0; k < 7 * ec; k++) {
                    double pasK = k / (double) ec;
                    double an = (sg < 0 ? 200 + pasK * 22 : -20 - pasK * 22) * Math.PI / 180;
                    int x = rond(cx + sg * rx * 0.55 + Math.cos(an) * 3 * ec), y = rond(cy - ry * 0.55 + Math.sin(an) * 2 * ec);
                    to.px(x, y, te[3]);
                    if (ec == 2) to.px(x, y + 1, te[3]);
                }

        // Visage (aucun s'il tourne le dos).
        boolean moue = a.boude && a.expr.equals("repos");
        String n0 = nomOeil(a.expr);
        String nom = a.etourdi ? "spirale" : !n0.isEmpty() ? n0 : moue ? "boude" : a.fatigue ? "fatigue" : "ouvert";
        if (a.baille) nom = "dort";
        if (st == 4 && nom.equals("ouvert")) nom = "serein";
        boolean peut = (a.expr.equals("repos") || a.expr.equals("inquiet") || a.expr.equals("attente") || a.expr.equals("neutre")) && !a.etourdi;
        String og = peut && a.cligne ? "cligne" : nom;
        String od = peut && (a.cligne || a.clin) ? "cligne" : nom;
        Sprites.Sprite grand = b.get("oeil-ouvert-g", ec);
        if (a.dos) {
            // vu de dos : ni yeux, ni bouche, ni joues
        } else if (st == 1 && og.equals("ouvert") && grand != null) {
            to.poser(grand, false, (C - 10) * ec + dxf, ey - ec, null);
            if (od.equals("ouvert")) to.poser(grand, true, (C + 2) * ec + dxf, ey - ec, null);
            else if (b.get("oeil-" + od, ec) != null) to.poser(b.get("oeil-" + od, ec), true, (C + 3) * ec + dxf, ey, null);
        } else {
            int ecart = st == 1 ? 1 : 0;
            Sprites.Sprite sg = b.get("oeil-" + og, ec), sdd = b.get("oeil-" + od + "-d", ec), sd = b.get("oeil-" + od, ec);
            if (sg != null) to.poser(sg, false, (C - 10 + ecart) * ec + dxf + sg.dx, ey + sg.dy, null);
            // Œil droit dessiné à part (regard dissymétrique : malice) : posé tel quel, sans miroir.
            if (sdd != null) to.poser(sdd, false, (C + 4 - ecart) * ec + dxf + sdd.dx, ey + sdd.dy, null);
            else if (sd != null) to.poser(sd, true, (C + 10 - ecart) * ec + dxf - sd.dx - sd.w(), ey + sd.dy, null);
        }
        Sprites.Sprite bo = a.dos ? null : b.get(a.baille ? "bouche-baille" : a.parle ? "bouche-surpris" : moue ? "bouche-boude" : "bouche-" + a.expr, ec);
        if (bo == null && !a.dos) bo = b.get("bouche-repos", ec);
        if (bo != null) to.poser(bo, false, c0 - bo.w() / 2 + dxf, ey + 9 * ec + bo.dy, null);
        if (!a.dos && (a.expr.equals("fete") || a.expr.equals("caresse") || a.expr.equals("joie") || a.expr.equals("tendre"))) {
            int joue = rond(rx) - ec;
            if (ec == 1) {
                for (int jx : new int[]{C - joue + dxf, C + joue - 3 + dxf})
                    for (int i = 0; i < 3; i++)
                        for (int j = 0; j < 2; j++) to.px(jx + i, ey + 7 + j, JOUE);
            } else {
                to.motif(c0 - joue + dxf, ey + 14, JOUE_FINE, '#', JOUE, 'o', JOUE_CLAIRE, 'o', JOUE_CLAIRE);
                to.motif(c0 + joue - 6 + dxf, ey + 14, JOUE_FINE, '#', JOUE, 'o', JOUE_CLAIRE, 'o', JOUE_CLAIRE);
            }
        }
        // Marque de l'humeur (larme, goutte, signe de colère…) : sprite « marque-<humeur> », sur l'ancre des yeux.
        if (!a.dos) {
            Sprites.Sprite marque = b.get("marque-" + a.expr, ec);
            if (marque != null) poserAncre(to, marque, ancres);
        }

        // Antenne(s) et étincelle(s), sauf sous un chapeau.
        if (!coiffe) {
            String sp = etincelle(a.expr);
            if (sp == null) {
                boolean grandeEt = a.expr.equals("fete") ? Math.floor(t / 120) % 2 == 0 : Math.floor(t / 900) % 2 == 0;
                sp = grandeEt ? "etincelle-grand" : "etincelle-petit";
            }
            Sprites.Sprite spr = b.get(sp, ec);
            String[] im = null;
            if (sp.equals("etincelle-roue") && spr != null && !spr.images.isEmpty())
                im = spr.images.get((int) (Math.floor(t / (a.expr.equals("concentre") ? 90 : 260)) % spr.images.size()));
            int[][] tiges = st == 3 ? new int[][]{{c0 - 7 * ec + dx, -1}, {c0 + 5 * ec + dx, 1}} : new int[][]{{c0 - ec + dx, 0}};
            int baseY = sommet + (st == 3 ? 3 * ec : 0);
            for (int[] tg : tiges) {
                for (int k = 1; k <= hautAntenne; k++) {
                    if (ec == 1) {
                        int dec = (k > hautAntenne / 2 ? balance : 0) + tg[1] * (k / 3);
                        to.px(tg[0] + dec, baseY - k, te[0]);
                        to.px(tg[0] + 1 + dec, baseY - k, te[0]);
                    } else {
                        // Tige fine : elle se courbe peu à peu vers la pointe ; un filet d'ombre lui donne du volume.
                        int courbe = Math.abs(balance) * Math.max(0, 2 * k - hautAntenne + 2) / (hautAntenne + 2);
                        int dec = (balance > 0 ? courbe : -courbe) + tg[1] * (k / 3);
                        for (int i = 0; i < 4; i++) to.px(tg[0] + i + dec, baseY - k, i == 1 ? te[1] : te[0]);
                    }
                }
                if (spr != null) {
                    int pointe = tg[0] + ec + balance + tg[1] * (hautAntenne / 3);
                    to.poser(spr, false, pointe + spr.dx, baseY - hautAntenne + spr.dy, im);
                }
            }
        }

        // Nimbus : petite traînée de gouttes qui tombent.
        if (st == 3) {
            double[] fx = {-0.6, 0.55, -0.1};
            for (int i = 0; i < 3; i++) {
                double ph = (t / 900 + i / 3.0) % 1;
                int x = rond(cx + rx * fx[i]), y = rond(cy + ry * 0.7 + ph * 9 * ec);
                if (y < pied) continue;
                if (ec == 1) {
                    to.px(x, y, te[3]);
                    to.px(x, y + 1, te[2]);
                    to.px(x - 1, y + 1, te[0]);
                    to.px(x + 1, y + 1, te[0]);
                    to.px(x, y + 2, te[0]);
                } else {
                    to.motif(x - 2, y, GOUTTE_NIMBUS_FINE, 'c', te[0], 'l', te[3], 'b', te[2]);
                }
            }
        }

        for (Sprites.Sprite s : portes)
            if (!s.derriere) poserAncre(to, s, ancres);
        for (int[] o : orbite)
            if (o[2] == 1) to.etoile(o[0], o[1], o[3], ec);

        // Réaction « sueur » : deux gouttes qui glissent sur les tempes.
        if ("sueur".equals(a.reaction))
            for (int i = 0; i < 2; i++) {
                int sg = i == 0 ? -1 : 1;
                double ph = (t / 1100 + i * 0.5) % 1;
                int x = rond(cx + sg * (rx - 2 * ec)), y = rond(ey - 2 * ec + ph * 8 * ec);
                if (ec == 1) {
                    to.px(x, y - 1, GOUTTE);
                    for (int[] d : new int[][]{{-1, 0}, {1, 0}, {-1, 1}, {1, 1}, {0, 2}}) to.px(x + d[0], y + d[1], GOUTTE);
                    to.px(x, y, GOUTTE_CLAIRE);
                    to.px(x, y + 1, BLANC);
                } else {
                    to.motif(x - 2, y - 2, SUEUR_FINE, 'g', GOUTTE, 'c', GOUTTE_CLAIRE, 'w', BLANC);
                }
            }

        // Vie : bouffées de poussière au ras du sol (le pied arrière en marchant, les deux côtés à l'atterrissage), en
        // blocs d'un pixel de la grille 1× ; posées seulement sur le vide ou l'ombre, jamais sur Pilou.
        if (a.vie && a.suspendu < 0.1 && a.assis <= 0.5) {
            int pg = (st == 1 ? C - 8 : C - 10) * ec, pd = (st == 1 ? C + 3 : C + 4) * ec, largeur = (st == 1 ? 5 : 6) * ec;
            if (a.marche && !a.course) {
                int sens = a.regard >= 0 ? 1 : -1;
                int ib = Vie.bouffee((long) Math.floor(t), (int) cadence, sens);
                if (ib >= 0) bouffee(g, w, h, ec, pied, sens > 0 ? pg + dx - ec : pd + dx + largeur, -sens, Vie.BOUFFEES[ib]);
            }
            int ia = a.atterri >= 0 ? Vie.bouffeeAtterrissage((long) Math.floor(a.atterri)) : -1;
            if (ia >= 0) {
                bouffee(g, w, h, ec, pied, pg + dx - ec, -1, Vie.BOUFFEES_ATTERRISSAGE[ia]);
                bouffee(g, w, h, ec, pied, pd + dx + largeur, 1, Vie.BOUFFEES_ATTERRISSAGE[ia]);
            }
        }
        return g;
    }

    /** Ombre tramée en l'air (trame 1 : le bas de l'ombre ; 2 : toute l'ombre). */
    private static boolean ombre(int trame, int x, int j, boolean bas) {
        return trame == 0 || (trame == 1 && !bas) || (x + j) % 2 == 0;
    }

    private static void bouffee(int[] g, int w, int h, int ec, int pied, int x0, int sg, int[][] points) {
        for (int[] p : points)
            for (int j = 0; j < ec; j++)
                for (int i = 0; i < ec; i++) {
                    int x = x0 + sg * p[0] * ec + i, y = pied + ec + p[1] * ec + j;
                    if (x >= 0 && x < w && y >= 0 && y < h && (g[y * w + x] == 0 || g[y * w + x] == OMBRE_SOL))
                        g[y * w + x] = p[2] == 1 ? Vie.POUSSIERE : Vie.POUSSIERE_LEGERE;
                }
    }

    private static final List<String> ANCRES = Arrays.asList("tete", "yeux", "bouche", "cou", "corps", "main", "main-g", "pieds", "cote", "antenne");

    private static void poserAncre(Toile to, Sprites.Sprite s, int[] ancres) {
        int i = ANCRES.indexOf(s.ancre);
        to.poser(s, false, (i < 0 ? 0 : ancres[2 * i]) + s.dx, (i < 0 ? 0 : ancres[2 * i + 1]) + s.dy, null);
    }
}
