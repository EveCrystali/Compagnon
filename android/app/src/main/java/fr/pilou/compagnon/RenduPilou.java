package fr.pilou.compagnon;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Pilou en 48 × 56 : corps procédural (ombrage tramé, reflet, cerne), visage, antenne, et tout ce qu'il porte,
 * tiré de la banque de sprites. Même règle que RenduPilou.cs (PC) et outils/sprites/rendu.py.
 */
public final class RenduPilou {
    public static final int W = 48, H = 56, C = 24;
    public static final double K = 1.25 * 48 / 26;
    private static final int JOUE = 0xffffb37a, OMBRE_SOL = 0x33000000, SILHOUETTE = 0xffe8f4ff, SILHOUETTE_BORD = 0xff6cb6ff,
            GOUTTE = 0xff1f4f8a, GOUTTE_CLAIRE = 0xffb4dbff, BLANC = 0xffffffff;
    private static final int[] ECLAT = {0xffffd8b0, 0xfffff6cc, 0xffb4dbff};
    private static final List<String> ORDRE = Arrays.asList("dos", "cou", "visage", "yeux", "tete", "main", "compagnon", "effet", "objet");
    private static final Set<String> CHAUDES = new HashSet<>(Arrays.asList("ambre", "braise", "comete", "corail-orange", "sable"));
    private static final int[] BLEU = {0xff1f4f8a, 0xff4a8fdc, 0xff6cb6ff, 0xffb4dbff};
    private static final int[] ORANGE = {0xff8a4a1f, 0xffd9803a, 0xfff69d50, 0xffffc89a};
    private static final int[][] CROIX = {{0, 0}, {-1, 0}, {1, 0}, {0, -1}, {0, 1}};

    /** Ce qu'on demande au dessin. */
    public static final class Allure implements Cloneable {
        public String expr = "repos", couleur = "bleu", accessoire = "", tenue = "", reaction = "";
        public double t, saut, chute, assis, suspendu, tremble, evolution;
        public List<String> objets = Collections.emptyList();
        public boolean cligne, clin, marche, course, baille, etourdi, fatigue, salue;
        public int regard, regardY, stade = 2;

        public Allure copie() {
            try {
                return (Allure) clone();
            } catch (CloneNotSupportedException e) {
                throw new AssertionError(e);
            }
        }
    }

    /** Points utiles autour de Pilou (pixels de la grille). */
    public static final class Geometrie {
        public double cx, cy, rx, ry;
        public int sommet, ey, pied;
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
            case "fete": case "caresse": return "heureux";
            case "soulage": return "content";
            case "dort": return "dort";
            case "inquiet": return "inquiet";
            default: return "";
        }
    }

    private static String etincelle(String expr) {
        switch (expr) {
            case "concentre": case "attente": return "etincelle-roue";
            case "grimace": return "etincelle-x";
            case "dort": return "etincelle-dort";
            case "inquiet": return "etincelle-alerte";
            case "caresse": return "etincelle-coeur";
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

    /** Image ARGB H × W, ligne par ligne, animation d'évolution comprise. */
    public static int[] rendre(Allure a, Sprites.Banque b, Geometrie geo) {
        double e = a.evolution;
        if (e > 0 && e < 1 && a.stade > 1) {
            if (e < 0.85) {
                int k = (int) (Math.pow(e / 0.85, 2) * 12) % 2;
                Allure q = a.copie();
                q.stade = k == 0 ? a.stade - 1 : a.stade;
                q.evolution = 0;
                q.expr = "repos";
                return silhouetter(rendreStade(q, b, geo));
            }
            Allure n = a.copie();
            n.evolution = 0;
            int[] g = rendreStade(n, b, geo);
            eclats(g, (e - 0.85) / 0.15);
            return g;
        }
        return rendreStade(a, b, geo);
    }

    private static boolean vide(int[] g, int x, int y) {
        return x < 0 || y < 0 || x >= W || y >= H || g[y * W + x] == 0 || g[y * W + x] == OMBRE_SOL;
    }

    private static int[] silhouetter(int[] g) {
        int[] o = new int[W * H];
        for (int y = 0; y < H; y++)
            for (int x = 0; x < W; x++) {
                int c = g[y * W + x];
                if (c == 0 || c == OMBRE_SOL) o[y * W + x] = c;
                else o[y * W + x] = vide(g, x + 1, y) || vide(g, x - 1, y) || vide(g, x, y + 1) || vide(g, x, y - 1) ? SILHOUETTE_BORD : SILHOUETTE;
            }
        return o;
    }

    private static void eclats(int[] g, double k) {
        double r = 4 + k * 20;
        for (int i = 0; i < 12; i++) {
            double an = i * Math.PI / 6;
            int x = rond(C + Math.cos(an) * r), y = rond(36 + Math.sin(an) * r * 0.85);
            for (int[] c : CROIX)
                if (x + c[0] >= 0 && x + c[0] < W && y + c[1] >= 0 && y + c[1] < H) g[(y + c[1]) * W + x + c[0]] = ECLAT[i % 3];
        }
    }

    private static final class Toile {
        final int[] g = new int[W * H];
        int[] te;
        double t;

        void px(int x, int y, int c) {
            if (c != 0 && x >= 0 && y >= 0 && x < W && y < H) g[y * W + x] = c;
        }

        void poser(Sprites.Sprite s, boolean miroir, int x, int y, String[] im) {
            if (im == null) im = s.image(t);
            for (int j = 0; j < im.length; j++) {
                String l = im[j];
                for (int i = 0; i < l.length(); i++) {
                    char ch = l.charAt(i);
                    if (ch == '.') continue;
                    String code = s.palette.get(ch);
                    if (code == null) continue;
                    int c;
                    switch (code) {
                        case "@contour": c = te[0]; break;
                        case "@ombre": c = te[1]; break;
                        case "@base": c = te[2]; break;
                        case "@clair": c = te[3]; break;
                        default: c = Sprites.couleur(code);
                    }
                    px(x + (miroir ? l.length() - 1 - i : i), y + j, c);
                }
            }
        }

        void etoile(int x, int y, int c) {
            for (int[] d : CROIX) px(x + d[0], y + d[1], c);
        }
    }

    private static int rang(Sprites.Sprite s) {
        int r = ORDRE.indexOf(s.slot);
        return r >= 0 ? r : 9;
    }

    private static int[] rendreStade(Allure a, Sprites.Banque b, Geometrie geo) {
        Toile to = new Toile();
        int st = a.stade >= 1 && a.stade <= 4 ? a.stade : 2;
        int[] te = teinte(a, b);
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
        rx *= stadeX(st);
        ry *= stadeY(st);
        double cadence = a.course ? 70 : 160;
        double marche = a.marche ? Math.abs(Math.sin(t / cadence)) * (a.course ? 1.3 : 0.8) : 0;
        double sol = (21.6 - a.saut - marche + a.assis) * K;
        double cx = C + (a.tremble + a.suspendu * Math.sin(t / 260) * 1.2) * K;
        rx *= K;
        ry *= K;
        double cy = sol - ry;
        int dx = rond(cx - C);

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
            Sprites.Sprite s = b.get(id);
            if (s == null) continue;
            portes.add(s);
            coiffe |= s.coiffe;
        }
        Collections.sort(portes, (p, q) -> Integer.compare(rang(p), rang(q)));

        int pied = rond(sol);
        int sommet = (int) Math.ceil(cy - ry);
        int ey = (int) Math.floor(cy - 6.6 * stadeY(st)) + a.regardY * 2;
        int dxf = dx + a.regard * 2;
        double vitesse = a.salue || a.expr.equals("fete") ? 90 : a.expr.equals("concentre") ? 300 : 650;
        int balance = a.expr.equals("dort") ? 0
                : Math.max(-1, Math.min(1, rond(Math.sin(t / vitesse) * 0.9) + (a.marche ? -Integer.signum(a.regard) : 0)));
        int hautAntenne = st == 1 ? 3 : 6;
        if (geo != null) {
            geo.cx = cx; geo.cy = cy; geo.rx = rx; geo.ry = ry; geo.sommet = sommet; geo.ey = ey; geo.pied = pied;
        }

        // Ancres : tete, yeux, bouche, cou, corps, main, main-g, pieds, cote, antenne.
        java.util.Map<String, int[]> ancres = new java.util.HashMap<>();
        ancres.put("tete", new int[]{C + dx, sommet});
        ancres.put("yeux", new int[]{C + dxf, ey});
        ancres.put("bouche", new int[]{C + dxf, ey + 9});
        ancres.put("cou", new int[]{C + dx, rond(cy + ry * 0.45)});
        ancres.put("corps", new int[]{C + dx, rond(cy)});
        ancres.put("main", new int[]{rond(cx + rx) - 1, rond(cy + ry * 0.15)});
        ancres.put("main-g", new int[]{rond(cx - rx), rond(cy + ry * 0.15)});
        ancres.put("pieds", new int[]{C + dx, pied});
        ancres.put("cote", new int[]{rond(cx + rx * 0.45), pied + 2});
        ancres.put("antenne", new int[]{C + dx + 2 * balance, sommet - hautAntenne});

        // Astral : couronne d'étincelles en orbite.
        List<int[]> orbite = new ArrayList<>();
        if (st == 4)
            for (int i = 0; i < 5; i++) {
                double an = t / 700 + i * 2 * Math.PI / 5;
                orbite.add(new int[]{rond(cx + Math.cos(an) * (rx + 4)), rond(sommet + 4 + Math.sin(an) * 3.5), Math.sin(an) > 0 ? 1 : 0, ECLAT[i % 3]});
            }

        for (Sprites.Sprite s : portes)
            if (s.derriere) poserAncre(to, s, ancres);
        for (int[] o : orbite)
            if (o[2] == 0) to.etoile(o[0], o[1], o[3]);

        int[] g = to.g;
        if (a.suspendu < 0.1) {
            int demi = (int) Math.max(6, 15 * stadeX(st) - a.saut * 2.8);
            for (int x = C - demi; x < C + demi; x++) {
                if (x < 0 || x >= W) continue;
                if (g[52 * W + x] == 0) g[52 * W + x] = OMBRE_SOL;
                if (Math.abs(x - C + 0.5) < demi - 3 && g[53 * W + x] == 0) g[53 * W + x] = OMBRE_SOL;
            }
        }

        int[] m = new int[W * H];
        List<double[]> bosses = new ArrayList<>();
        if (st == 3)
            for (int deg : new int[]{-160, -125, -90, -55, -20, 170, 10}) {
                double an = deg * Math.PI / 180;
                bosses.add(new double[]{cx + Math.cos(an) * rx * 0.84, cy + Math.sin(an) * ry * 0.84, ry * (deg < 0 ? 0.3 : 0.24)});
            }
        for (int y = 0; y < H; y++)
            for (int x = 0; x < W; x++) {
                double u = (x + 0.5 - cx) / rx, v = (y + 0.5 - cy) / ry, r2 = u * u + v * v;
                boolean dans = r2 <= 1;
                if (!dans && !bosses.isEmpty()) {
                    for (double[] o : bosses)
                        if (Math.pow(x + 0.5 - o[0], 2) + Math.pow(y + 0.5 - o[1], 2) <= o[2] * o[2]) dans = true;
                    r2 = Math.min(r2, 0.9);
                }
                if (!dans) continue;
                boolean damier = (x + y) % 2 == 0;
                boolean reflet = u < -0.25 && v < -0.3;
                m[y * W + x] = reflet && (r2 > 0.45 || (r2 > 0.34 && damier)) ? te[3] : v > 0.62 || (v > 0.46 && damier) ? te[1] : te[2];
            }
        if (st == 3)
            for (int sg : new int[]{-1, 1}) {
                double bx = cx + sg * (rx + 1.2), by = cy + ry * 0.28 + Math.sin(t / 300 + sg) * 0.8;
                for (int y = 0; y < H; y++)
                    for (int x = 0; x < W; x++)
                        if (Math.pow((x + 0.5 - bx) / 3.2, 2) + Math.pow((y + 0.5 - by) / 2.4, 2) <= 1) m[y * W + x] = te[1];
            }
        if (a.assis <= 0.5) {
            int pas = a.marche ? (int) (Math.floor(t / cadence) % 2) : -1;
            int largeur = st == 1 ? 5 : 6;
            int[][] pieds = st == 1 ? new int[][]{{0, C - 8}, {1, C + 3}} : new int[][]{{0, C - 10}, {1, C + 4}};
            for (int[] pd : pieds) {
                int haut = pied - (pas == pd[0] ? 2 : 0);
                for (int x = pd[1]; x < pd[1] + largeur; x++)
                    for (int y : new int[]{haut, haut + 1})
                        if (x + dx >= 0 && x + dx < W && y >= 0 && y < H && (y == haut || (x > pd[1] && x < pd[1] + largeur - 1)))
                            m[y * W + x + dx] = te[1];
            }
        }
        for (int y = 0; y < H; y++)
            for (int x = 0; x < W; x++) {
                int c = m[y * W + x];
                if (c == 0) continue;
                boolean bord = x == 0 || y == 0 || x == W - 1 || y == H - 1 || m[y * W + x - 1] == 0 || m[y * W + x + 1] == 0
                        || m[(y - 1) * W + x] == 0 || m[(y + 1) * W + x] == 0;
                g[y * W + x] = bord ? te[0] : c;
            }
        if (st == 3)
            for (int sg : new int[]{-1, 1})
                for (int k = 0; k < 7; k++) {
                    double an = (sg < 0 ? 200 + k * 22 : -20 - k * 22) * Math.PI / 180;
                    to.px(rond(cx + sg * rx * 0.55 + Math.cos(an) * 3), rond(cy - ry * 0.55 + Math.sin(an) * 2), te[3]);
                }

        // Visage.
        String n0 = nomOeil(a.expr);
        String nom = a.etourdi ? "spirale" : !n0.isEmpty() ? n0 : a.fatigue ? "fatigue" : "ouvert";
        if (a.baille) nom = "dort";
        if (st == 4 && nom.equals("ouvert")) nom = "serein";
        boolean peut = (a.expr.equals("repos") || a.expr.equals("inquiet") || a.expr.equals("attente")) && !a.etourdi;
        String og = peut && a.cligne ? "cligne" : nom;
        String od = peut && (a.cligne || a.clin) ? "cligne" : nom;
        Sprites.Sprite grand = b.get("oeil-ouvert-g");
        if (st == 1 && og.equals("ouvert") && grand != null) {
            to.poser(grand, false, C - 10 + dxf, ey - 1, null);
            if (od.equals("ouvert")) to.poser(grand, true, C + 2 + dxf, ey - 1, null);
            else if (b.get("oeil-" + od) != null) to.poser(b.get("oeil-" + od), true, C + 3 + dxf, ey, null);
        } else {
            int ecart = st == 1 ? 1 : 0;
            if (b.get("oeil-" + og) != null) to.poser(b.get("oeil-" + og), false, C - 10 + ecart + dxf, ey, null);
            if (b.get("oeil-" + od) != null) to.poser(b.get("oeil-" + od), true, C + 4 - ecart + dxf, ey, null);
        }
        Sprites.Sprite bo = b.get(a.baille ? "bouche-baille" : "bouche-" + a.expr);
        if (bo == null) bo = b.get("bouche-repos");
        if (bo != null) to.poser(bo, false, C - bo.w() / 2 + dxf, ey + 9, null);
        if (a.expr.equals("fete") || a.expr.equals("caresse")) {
            int joue = rond(rx) - 1;
            for (int jx : new int[]{C - joue + dxf, C + joue - 3 + dxf})
                for (int i = 0; i < 3; i++)
                    for (int j = 0; j < 2; j++) to.px(jx + i, ey + 7 + j, JOUE);
        }

        // Antenne(s) et étincelle(s), sauf sous un chapeau.
        if (!coiffe) {
            String sp = etincelle(a.expr);
            if (sp == null) {
                boolean grandeEt = a.expr.equals("fete") ? Math.floor(t / 120) % 2 == 0 : Math.floor(t / 900) % 2 == 0;
                sp = grandeEt ? "etincelle-grand" : "etincelle-petit";
            }
            Sprites.Sprite spr = b.get(sp);
            String[] im = null;
            if (sp.equals("etincelle-roue") && spr != null && !spr.images.isEmpty())
                im = spr.images.get((int) (Math.floor(t / (a.expr.equals("concentre") ? 90 : 260)) % spr.images.size()));
            int[][] tiges = st == 3 ? new int[][]{{C - 7 + dx, -1}, {C + 5 + dx, 1}} : new int[][]{{C - 1 + dx, 0}};
            int baseY = sommet + (st == 3 ? 3 : 0);
            for (int[] tg : tiges) {
                for (int k = 1; k <= hautAntenne; k++) {
                    int dec = (k > hautAntenne / 2 ? balance : 0) + tg[1] * (k / 3);
                    to.px(tg[0] + dec, baseY - k, te[0]);
                    to.px(tg[0] + 1 + dec, baseY - k, te[0]);
                }
                if (spr != null) {
                    int pointe = tg[0] + 1 + balance + tg[1] * (hautAntenne / 3);
                    to.poser(spr, false, pointe + spr.dx, baseY - hautAntenne + spr.dy, im);
                }
            }
        }

        if (st == 3) {
            double[] fx = {-0.6, 0.55, -0.1};
            for (int i = 0; i < 3; i++) {
                double ph = (t / 900 + i / 3.0) % 1;
                int x = rond(cx + rx * fx[i]), y = rond(cy + ry * 0.7 + ph * 9);
                if (y < pied) continue;
                to.px(x, y, te[3]);
                to.px(x, y + 1, te[2]);
                to.px(x - 1, y + 1, te[0]);
                to.px(x + 1, y + 1, te[0]);
                to.px(x, y + 2, te[0]);
            }
        }

        for (Sprites.Sprite s : portes)
            if (!s.derriere) poserAncre(to, s, ancres);
        for (int[] o : orbite)
            if (o[2] == 1) to.etoile(o[0], o[1], o[3]);

        if ("sueur".equals(a.reaction))
            for (int i = 0; i < 2; i++) {
                int sg = i == 0 ? -1 : 1;
                double ph = (t / 1100 + i * 0.5) % 1;
                int x = rond(cx + sg * (rx - 2)), y = rond(ey - 2 + ph * 8);
                to.px(x, y - 1, GOUTTE);
                for (int[] d : new int[][]{{-1, 0}, {1, 0}, {-1, 1}, {1, 1}, {0, 2}}) to.px(x + d[0], y + d[1], GOUTTE);
                to.px(x, y, GOUTTE_CLAIRE);
                to.px(x, y + 1, BLANC);
            }
        return g;
    }

    private static void poserAncre(Toile to, Sprites.Sprite s, java.util.Map<String, int[]> ancres) {
        int[] a = ancres.get(s.ancre);
        if (a == null) a = new int[]{0, 0};
        to.poser(s, false, a[0] + s.dx, a[1] + s.dy, null);
    }
}
