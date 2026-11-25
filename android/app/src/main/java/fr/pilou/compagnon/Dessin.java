package fr.pilou.compagnon;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Paint;

/**
 * Pilou en pixel art, même dessin que Scene.cs : une goutte cernée sur une grille de 26 × 30,
 * ombrage tramé, reflet, pieds, yeux et bouche selon l'humeur, antenne et étincelle orange.
 */
public final class Dessin {
    public static final int W = 26, H = 30;
    private static final double E = 1.25, C = 13;
    private static final int ENCRE = 0xff1c2128, BLANC = 0xffffffff, ETINCELLE = 0xfff69d50, ETINCELLE_CLAIR = 0xffffd8b0,
            JOUE = 0xffffb37a, OMBRE_SOL = 0x33000000;

    private static final int[][] BLEU = {{0xff1f4f8a, 0xff4a8fdc, 0xff6cb6ff, 0xffb4dbff}};
    private static final int[] ORANGE = {0xff8a4a1f, 0xffd9803a, 0xfff69d50, 0xffffc89a};

    // Teinte : contour, ombre, base, clair.
    static int[] teinte(String couleur, String expr) {
        if (expr.equals("inquiet")) return couleur.equals("ambre") ? BLEU[0] : ORANGE;
        switch (couleur) {
            case "nuit": return new int[]{0xff0d2a4d, 0xff2a5ea8, 0xff3f7fd6, 0xff8fbaf0};
            case "ambre": return new int[]{0xff7a4210, 0xffc97a28, 0xfff2a94e, 0xffffd59a};
            case "argent": return new int[]{0xff3b4654, 0xff8796a8, 0xffb8c4d2, 0xffe6ecf2};
            case "aurore": return new int[]{0xff3a2a7a, 0xff6a5acd, 0xff9b8cff, 0xffd2caff};
            default: return BLEU[0];
        }
    }

    // Yeux (œil gauche ; le droit est son miroir) : 1 encre, 2 reflet, 3 paupière.
    private static int[][] oeil(String nom) {
        switch (nom) {
            case "cligne": case "dort": return new int[][]{{0, 0, 0}, {0, 0, 0}, {1, 1, 1}};
            case "fatigue": return new int[][]{{3, 3, 3}, {2, 1, 1}, {1, 1, 1}};
            case "concentre": return new int[][]{{3, 3, 3}, {1, 1, 1}, {2, 1, 1}};
            case "haut": return new int[][]{{1, 2, 1}, {1, 1, 1}};
            case "grimace": return new int[][]{{1, 1, 0}, {0, 1, 1}, {1, 1, 0}};
            case "heureux": return new int[][]{{0, 1, 0}, {1, 0, 1}, {1, 0, 1}};
            case "content": return new int[][]{{0, 0, 0}, {1, 0, 1}, {0, 1, 0}};
            case "inquiet": return new int[][]{{0, 1, 0}, {1, 2, 1}, {1, 2, 1}, {0, 1, 0}};
            default: return new int[][]{{2, 1, 1}, {1, 1, 1}, {1, 1, 1}};
        }
    }

    // Bouches (centrées sur l'axe) : 1 encre, 5 langue orange.
    private static int[][] bouche(String expr) {
        switch (expr) {
            case "concentre": return new int[][]{{1, 1}};
            case "attente": case "dort": return new int[][]{{1, 1}, {1, 1}};
            case "grimace": return new int[][]{{0, 1, 0, 1, 0, 1}, {1, 0, 1, 0, 1, 0}};
            case "fete": return new int[][]{{1, 1, 1, 1}, {1, 5, 5, 1}, {0, 1, 1, 0}};
            case "inquiet": return new int[][]{{0, 1, 1, 0}, {1, 0, 0, 1}};
            case "caresse": return new int[][]{{1, 0, 1, 1, 0, 1}, {0, 1, 0, 0, 1, 0}};
            default: return new int[][]{{1, 0, 0, 1}, {0, 1, 1, 0}};
        }
    }

    private Dessin() {
    }

    /** Dessine Pilou dans un carré de (W + 2) × (H + 2) pixels de p points, à partir de (x0, y0). */
    public static void dessiner(Canvas cv, float x0, float y0, float p, String expr, long t, String couleur, boolean cligne, float saut) {
        Paint pt = new Paint();
        pt.setAntiAlias(false);
        int[] te = teinte(couleur, expr);
        double periode = expr.equals("dort") ? 4200 : expr.equals("concentre") || expr.equals("attente") ? 1600 : 2600;
        double b = Math.sin(2 * Math.PI * t / periode);
        double rx = 6.8 - 0.2 * b, ry = 5.6 + 0.3 * b;
        if (expr.equals("caresse")) { rx += 0.5; ry -= 0.5; }
        if (expr.equals("dort")) { rx += 0.6; ry -= 0.9; }
        double sol = (21.6 - saut) * E;
        double cx = C + (expr.equals("grimace") ? Math.sin(t / 30.0) * 0.4 : 0);
        rx *= E;
        ry *= E;
        double cy = sol - ry;

        int[][] masque = new int[W][H];
        for (int y = 0; y < H; y++)
            for (int x = 0; x < W; x++) {
                double u = (x + 0.5 - cx) / rx, v = (y + 0.5 - cy) / ry, r2 = u * u + v * v;
                if (r2 > 1) continue;
                boolean damier = (x + y) % 2 == 0;
                boolean reflet = u < -0.25 && v < -0.3;
                masque[x][y] = reflet && (r2 > 0.45 || (r2 > 0.34 && damier)) ? te[3]
                        : v > 0.62 || (v > 0.46 && damier) ? te[1] : te[2];
            }
        int pied = (int) Math.round(sol);
        for (int px : new int[]{8, 9, 10, 15, 16, 17})
            if (pied >= 0 && pied < H) masque[px][pied] = te[1];

        // Ombre au sol.
        pt.setColor(OMBRE_SOL);
        int demi = (int) Math.max(3, 8 - saut * 1.5);
        for (int x = 13 - demi; x < 13 + demi; x++)
            cv.drawRect(x0 + (x + 1) * p, y0 + (28.4f + 1) * p, x0 + (x + 2) * p, y0 + (28.4f + 1.75f) * p, pt);

        for (int y = 0; y < H; y++)
            for (int x = 0; x < W; x++) {
                if (masque[x][y] == 0) continue;
                boolean bord = x == 0 || y == 0 || x == W - 1 || y == H - 1 || masque[x - 1][y] == 0 || masque[x + 1][y] == 0
                        || masque[x][y - 1] == 0 || masque[x][y + 1] == 0;
                px(cv, pt, x0, y0, p, x, y, bord ? te[0] : masque[x][y]);
            }

        // Visage.
        int ey = (int) Math.floor(cy - 3.6);
        String nomOeil;
        switch (expr) {
            case "concentre": nomOeil = "concentre"; break;
            case "attente": nomOeil = "haut"; break;
            case "grimace": nomOeil = "grimace"; break;
            case "fete": case "caresse": nomOeil = "heureux"; break;
            case "soulage": nomOeil = "content"; break;
            case "dort": nomOeil = "dort"; break;
            case "inquiet": nomOeil = "inquiet"; break;
            default: nomOeil = "ouvert";
        }
        boolean peutCligner = expr.equals("repos") || expr.equals("inquiet") || expr.equals("attente");
        int[][] o = oeil(peutCligner && cligne ? "cligne" : nomOeil);
        motif(cv, pt, x0, y0, p, o, 11 - o[0].length, ey, false, te);
        motif(cv, pt, x0, y0, p, o, 15, ey, true, te);
        int[][] bo = bouche(expr);
        motif(cv, pt, x0, y0, p, bo, 13 - bo[0].length / 2, ey + 5, false, te);
        if (expr.equals("fete") || expr.equals("caresse"))
            for (int x : new int[]{5, 6, 19, 20}) px(cv, pt, x0, y0, p, x, ey + 4, JOUE);

        // Antenne et étincelle.
        int sommet = (int) Math.ceil(cy - ry);
        double vitesse = expr.equals("concentre") ? 300 : expr.equals("fete") ? 90 : 650;
        int balance = expr.equals("dort") ? 0 : (int) Math.max(-1, Math.min(1, Math.round(Math.sin(t / vitesse) * 0.9)));
        px(cv, pt, x0, y0, p, 13, sommet - 1, te[0]);
        px(cv, pt, x0, y0, p, 13, sommet - 2, te[0]);
        px(cv, pt, x0, y0, p, 13 + balance, sommet - 3, te[0]);
        int bx = 13 + balance * 2, by = sommet - 5;
        if (expr.equals("dort")) {
            px(cv, pt, x0, y0, p, bx, by + 1, 0xff768390);
        } else {
            boolean vif = (t / (expr.equals("concentre") ? 200 : 600)) % 2 == 0;
            px(cv, pt, x0, y0, p, bx, by, vif ? ETINCELLE_CLAIR : ETINCELLE);
            px(cv, pt, x0, y0, p, bx - 1, by, ETINCELLE);
            px(cv, pt, x0, y0, p, bx + 1, by, ETINCELLE);
            px(cv, pt, x0, y0, p, bx, by - 1, ETINCELLE);
            px(cv, pt, x0, y0, p, bx, by + 1, ETINCELLE);
        }
    }

    private static void px(Canvas cv, Paint pt, float x0, float y0, float p, int x, int y, int couleur) {
        pt.setColor(couleur);
        cv.drawRect(x0 + (x + 1) * p, y0 + (y + 1) * p, x0 + (x + 2) * p, y0 + (y + 2) * p, pt);
    }

    private static void motif(Canvas cv, Paint pt, float x0, float y0, float p, int[][] m, int x, int y, boolean miroir, int[] te) {
        for (int r = 0; r < m.length; r++)
            for (int c = 0; c < m[r].length; c++) {
                int v = m[r][miroir ? m[r].length - 1 - c : c];
                int couleur = v == 1 ? ENCRE : v == 2 ? BLANC : v == 3 ? te[1] : v == 5 ? ETINCELLE : 0;
                if (couleur != 0) px(cv, pt, x0, y0, p, x + c, y + r, couleur);
            }
    }

    /** Pilou dans une image (widget, notification). */
    public static Bitmap image(String expr, String couleur, int p) {
        Bitmap b = Bitmap.createBitmap((W + 2) * p, (H + 2) * p, Bitmap.Config.ARGB_8888);
        dessiner(new Canvas(b), 0, 0, p, expr, 0, couleur, false, 0);
        return b;
    }
}
