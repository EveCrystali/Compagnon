package fr.pilou.compagnon;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Paint;

/**
 * Pilou en pixel art, grille fine de 34 × 40 (le PC dessine sur 26 × 30 : même Pilou, pixels plus petits
 * d'un tiers). Une goutte cernée d'un pixel, ombrage tramé, reflet, pieds, yeux et bouche selon
 * l'humeur, antenne et étincelle orange, accessoire et couleur reçus du PC.
 */
public final class Dessin {
    public static final int W = 34, H = 40;
    /** À taille affichée égale, un pixel de cette grille vaut 28/36 d'un pixel de l'ancienne. */
    public static final float ECHELLE = 28f / 36f;
    private static final double K = 1.25 * 4 / 3.0; // anciens pixels → pixels de cette grille
    private static final int C = 17;                // axe du corps (entre les colonnes 16 et 17)

    private static final int ENCRE = 0xff1c2128, BLANC = 0xffffffff, ETINCELLE = 0xfff69d50, ETINCELLE_CLAIR = 0xffffd8b0,
            JOUE = 0xffffb37a, OMBRE_SOL = 0x33000000, LAINE = 0xfff69d50, LAINE_OMBRE = 0xffc8742e, CREME = 0xfff6f8fa,
            CREME_OMBRE = 0xffc9d1d9, ARCEAU = 0xff768390, FEUILLAGE = 0xffe0823d, NERVURE = 0xff8a4a1f, BLEU_CLAIR = 0xffb4dbff;

    /** Ce qui peint un rectangle : un Canvas Android, ou une image ordinaire pour les essais hors téléphone. */
    public interface Peintre {
        void rect(float gauche, float haut, float droite, float bas, int argb);
    }

    // Teinte : contour, ombre, base, clair.
    static int[] teinte(String couleur, String expr) {
        int[] bleu = {0xff1f4f8a, 0xff4a8fdc, 0xff6cb6ff, 0xffb4dbff};
        if (expr.equals("inquiet"))
            return couleur.equals("ambre") || couleur.equals("braise") ? bleu : new int[]{0xff8a4a1f, 0xffd9803a, 0xfff69d50, 0xffffc89a};
        switch (couleur) {
            case "nuit": return new int[]{0xff0d2a4d, 0xff2a5ea8, 0xff3f7fd6, 0xff8fbaf0};
            case "ambre": return new int[]{0xff7a4210, 0xffc97a28, 0xfff2a94e, 0xffffd59a};
            case "argent": return new int[]{0xff3b4654, 0xff8796a8, 0xffb8c4d2, 0xffe6ecf2};
            case "aurore": return new int[]{0xff3a2a7a, 0xff6a5acd, 0xff9b8cff, 0xffd2caff};
            case "lagon": return new int[]{0xff0f4a63, 0xff2689b8, 0xff3fb8e0, 0xffa8e4f7};
            case "braise": return new int[]{0xff6b2f0c, 0xffc45a1a, 0xfff07c2a, 0xffffc08a};
            case "nacre": return new int[]{0xff4d5566, 0xffb9b4cf, 0xffe4def5, 0xffffffff};
            case "abysse": return new int[]{0xff0a1230, 0xff1b2a6b, 0xff2f45a8, 0xff7f93e8};
            case "comete": return new int[]{0xff5a4410, 0xffc9a227, 0xfff5d76e, 0xfffff6cc};
            default: return bleu;
        }
    }

    // Yeux (œil gauche, 4 × 5 ; le droit est son miroir) : 1 encre, 2 reflet, 3 paupière.
    private static String[] oeil(String nom) {
        switch (nom) {
            case "cligne": case "dort": return new String[]{"0000", "0000", "0000", "1111", "0000"};
            case "fatigue": return new String[]{"3333", "3333", "1211", "1111", "0110"};
            case "concentre": return new String[]{"3333", "1111", "1211", "1111", "0000"};
            case "haut": return new String[]{"1211", "1111", "0110", "0000", "0000"};
            case "grimace": return new String[]{"1100", "0110", "0011", "0110", "1100"};
            case "heureux": return new String[]{"0000", "0110", "1001", "1001", "0000"};
            case "content": return new String[]{"0000", "0000", "1001", "0110", "0000"};
            case "inquiet": return new String[]{"0110", "1221", "1221", "1221", "0110"};
            default: return new String[]{"0110", "1211", "1111", "1111", "0110"};
        }
    }

    // Bouches (largeur paire, centrées sur l'axe) : 1 encre, 5 langue orange.
    private static String[] bouche(String expr) {
        switch (expr) {
            case "concentre": return new String[]{"1111"};
            case "attente": case "dort": return new String[]{"0110", "1001", "0110"};
            case "grimace": return new String[]{"01010101", "10101010"};
            case "fete": return new String[]{"111111", "155551", "015510", "001100"};
            case "inquiet": return new String[]{"011110", "100001"};
            case "caresse": return new String[]{"10011001", "01100110"};
            default: return new String[]{"100001", "011110"};
        }
    }

    private Dessin() {
    }

    /** Dessine Pilou dans un carré de (W + 2) × (H + 2) pixels de p points, à partir de (x0, y0). */
    public static void dessiner(Canvas cv, float x0, float y0, float p, String expr, long t, String couleur, boolean cligne, float saut) {
        dessiner(cv, x0, y0, p, expr, t, couleur, "aucun", cligne, saut);
    }

    public static void dessiner(Canvas cv, float x0, float y0, float p, String expr, long t, String couleur, String accessoire,
                                boolean cligne, float saut) {
        Paint pt = new Paint();
        pt.setAntiAlias(false);
        dessiner((g, h, d, b, c) -> {
            pt.setColor(c);
            cv.drawRect(g, h, d, b, pt);
        }, x0, y0, p, expr, t, couleur, accessoire, cligne, saut);
    }

    public static void dessiner(Peintre pe, float x0, float y0, float p, String expr, long t, String couleur, String accessoire,
                                boolean cligne, float saut) {
        int[] te = teinte(couleur, expr);
        double periode = expr.equals("dort") ? 4200 : expr.equals("concentre") || expr.equals("attente") ? 1600 : 2600;
        double b = Math.sin(2 * Math.PI * t / periode);
        double rx = 6.8 - 0.2 * b, ry = 5.6 + 0.3 * b;
        if (expr.equals("caresse")) { rx += 0.5; ry -= 0.5; }
        if (expr.equals("dort")) { rx += 0.6; ry -= 0.9; }
        rx *= K;
        ry *= K;
        double sol = (21.6 - saut) * K;
        double cx = C + (expr.equals("grimace") ? Math.sin(t / 30.0) * 0.5 : 0);
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
        int dx = (int) Math.round(cx - C);
        for (int px : new int[]{C - 7, C - 6, C - 5, C - 4, C + 3, C + 4, C + 5, C + 6})
            if (pied >= 0 && pied < H && px + dx >= 0 && px + dx < W) masque[px + dx][pied] = te[1];

        // Ombre au sol, plus petite quand il saute.
        int demi = (int) Math.max(4, 11 - saut * 2);
        float yo = (float) (28.4 * 4 / 3.0);
        for (int x = C - demi; x < C + demi; x++)
            pe.rect(x0 + (x + 1) * p, y0 + (yo + 1) * p, x0 + (x + 2) * p, y0 + (yo + 1.75f) * p, OMBRE_SOL);

        for (int y = 0; y < H; y++)
            for (int x = 0; x < W; x++) {
                if (masque[x][y] == 0) continue;
                boolean bord = x == 0 || y == 0 || x == W - 1 || y == H - 1 || masque[x - 1][y] == 0 || masque[x + 1][y] == 0
                        || masque[x][y - 1] == 0 || masque[x][y + 1] == 0;
                px(pe, x0, y0, p, x, y, bord ? te[0] : masque[x][y]);
            }

        // Visage.
        int ey = (int) Math.floor(cy - 3.6 * 4 / 3.0);
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
        String[] o = oeil(peutCligner && cligne ? "cligne" : nomOeil);
        motif(pe, x0, y0, p, o, C - 7 + dx, ey, false, te);
        motif(pe, x0, y0, p, o, C + 3 + dx, ey, true, te);
        String[] bo = bouche(expr);
        motif(pe, x0, y0, p, bo, C - bo[0].length() / 2 + dx, ey + 7, false, te);
        if (expr.equals("fete") || expr.equals("caresse"))
            for (int x : new int[]{C - 11, C - 10, C - 9, C + 8, C + 9, C + 10}) px(pe, x0, y0, p, x + dx, ey + 5, JOUE);

        // Antenne (quatre pixels) et étincelle, sauf sous un chapeau.
        int sommet = (int) Math.ceil(cy - ry);
        boolean coiffe = accessoire.equals("bonnet") || accessoire.equals("toque") || accessoire.equals("chapeaupeche");
        if (!coiffe) {
            double vitesse = expr.equals("concentre") ? 300 : expr.equals("fete") ? 90 : 650;
            int balance = expr.equals("dort") ? 0 : (int) Math.max(-1, Math.min(1, Math.round(Math.sin(t / vitesse) * 0.9)));
            int ax = C - 1 + dx;
            px(pe, x0, y0, p, ax, sommet - 1, te[0]);
            px(pe, x0, y0, p, ax, sommet - 2, te[0]);
            px(pe, x0, y0, p, ax + balance, sommet - 3, te[0]);
            px(pe, x0, y0, p, ax + balance, sommet - 4, te[0]);
            int bx = ax + balance * 2, by = sommet - 7;
            if (expr.equals("dort")) {
                px(pe, x0, y0, p, bx, by + 2, 0xff768390);
            } else {
                boolean vif = (t / (expr.equals("concentre") ? 200 : 600)) % 2 == 0;
                px(pe, x0, y0, p, bx, by, vif ? ETINCELLE_CLAIR : ETINCELLE);
                int[][] bras = {{-1, 0}, {1, 0}, {0, -1}, {0, 1}};
                for (int[] a : bras) px(pe, x0, y0, p, bx + a[0], by + a[1], ETINCELLE);
                if (vif) for (int[] a : bras) px(pe, x0, y0, p, bx + 2 * a[0], by + 2 * a[1], ETINCELLE_CLAIR);
            }
        }
        accessoire(pe, x0, y0, p, accessoire, dx, sommet, ey, pied, cx, cy, rx);
    }

    private static void accessoire(Peintre pe, float x0, float y0, float p, String a, int dx, int sommet, int ey, int pied,
                                   double cx, double cy, double rx) {
        switch (a) {
            case "lunettes": {
                int[] verres = {C - 8 + dx, C + 2 + dx};
                for (int g : verres)
                    for (int y = ey - 1; y <= ey + 3; y++)
                        for (int i = 0; i < 6; i++) {
                            if ((y == ey - 1 || y == ey + 3) && (i == 0 || i == 5)) continue;
                            px(pe, x0, y0, p, g + i, y, ENCRE);
                        }
                for (int x = C - 2 + dx; x < C + 2 + dx; x++) px(pe, x0, y0, p, x, ey, ENCRE);
                px(pe, x0, y0, p, verres[0] + 1, ey, BLEU_CLAIR);
                px(pe, x0, y0, p, verres[1] + 1, ey, BLEU_CLAIR);
                break;
            }
            case "couronne":
                grille(pe, x0, y0, p, new String[]{"1000110001", "1100110011", "1111111111", "1411111141"}, C - 5 + dx, sommet - 3,
                        LAINE, BLEU_CLAIR);
                break;
            case "noeud":
                grille(pe, x0, y0, p, new String[]{"11000011", "11100111", "11144111", "11100111", "11000011"}, C - 4 + dx, pied - 7,
                        LAINE, LAINE_OMBRE);
                break;
            case "feuille":
                grille(pe, x0, y0, p, new String[]{"000011", "000111", "001141", "011410", "114100", "410000"}, C - 10 + dx, sommet - 3,
                        FEUILLAGE, NERVURE);
                break;
            case "etoilemer":
                grille(pe, x0, y0, p, new String[]{"00100", "11111", "01410", "01010", "10001"}, C + 5 + dx, sommet - 2,
                        LAINE, LAINE_OMBRE);
                break;
            case "bonnet": {
                for (int y = sommet - 1; y <= sommet + 4; y++) {
                    double v = (y + 0.5 - cy) / (5.6 * K), demi = rx * Math.sqrt(Math.max(0, 1 - v * v)) + 0.5;
                    int couleur = y == sommet + 4 ? CREME : (y % 2 == 0 ? LAINE : LAINE_OMBRE);
                    for (int x = (int) Math.floor(cx - demi); x <= (int) Math.ceil(cx + demi) - 1; x++)
                        px(pe, x0, y0, p, x, y, couleur);
                }
                grille(pe, x0, y0, p, new String[]{"0110", "1111", "0110"}, C - 2 + dx, sommet - 4, CREME, CREME);
                break;
            }
            case "toque":
                grille(pe, x0, y0, p, new String[]{
                        "0011011100", "0111111110", "1111111111", "1111111111", "0111111110",
                        "0044444400", "0011111100", "0011111100"}, C - 5 + dx, sommet - 6, CREME, CREME_OMBRE);
                break;
            case "chapeaupeche":
                grille(pe, x0, y0, p, new String[]{
                        "00011111111000", "00111111111100", "00111111111100", "00444444444400", "11111111111111"},
                        C - 7 + dx, sommet - 3, 0xffadbac7, LAINE);
                break;
            case "casque": {
                int g = (int) Math.floor(cx - rx) - 1, d = (int) Math.ceil(cx + rx);
                for (int x = g + 1; x <= d - 1; x++) {
                    double u = (x + 0.5 - cx) / (rx + 1.5);
                    int y = (int) Math.round(cy - (5.6 * K + 1.5) * Math.sqrt(Math.max(0, 1 - u * u)));
                    if (y < ey) px(pe, x0, y0, p, x, y, ARCEAU);
                }
                for (int y = ey; y < ey + 5; y++)
                    for (int i = 0; i < 2; i++) {
                        px(pe, x0, y0, p, g + i, y, LAINE);
                        px(pe, x0, y0, p, d - i, y, LAINE);
                    }
                break;
            }
            case "tablier":
                grille(pe, x0, y0, p, new String[]{"1000000001", "0100000010", "0011111100", "0011111100", "0011441100", "0011441100"},
                        C - 5 + dx, ey + 9, CREME, CREME_OMBRE);
                break;
            default:
                break;
        }
    }

    // Motif à deux couleurs : 1 première, 4 seconde.
    private static void grille(Peintre pe, float x0, float y0, float p, String[] m, int x, int y, int c1, int c4) {
        for (int r = 0; r < m.length; r++)
            for (int c = 0; c < m[r].length(); c++) {
                char v = m[r].charAt(c);
                if (v == '1') px(pe, x0, y0, p, x + c, y + r, c1);
                else if (v == '4') px(pe, x0, y0, p, x + c, y + r, c4);
            }
    }

    private static void px(Peintre pe, float x0, float y0, float p, int x, int y, int couleur) {
        if (x < -1 || y < -1 || x > W || y > H) return;
        pe.rect(x0 + (x + 1) * p, y0 + (y + 1) * p, x0 + (x + 2) * p, y0 + (y + 2) * p, couleur);
    }

    private static void motif(Peintre pe, float x0, float y0, float p, String[] m, int x, int y, boolean miroir, int[] te) {
        for (int r = 0; r < m.length; r++)
            for (int c = 0; c < m[r].length(); c++) {
                char v = m[r].charAt(miroir ? m[r].length() - 1 - c : c);
                int couleur = v == '1' ? ENCRE : v == '2' ? BLANC : v == '3' ? te[1] : v == '5' ? ETINCELLE : 0;
                if (couleur != 0) px(pe, x0, y0, p, x + c, y + r, couleur);
            }
    }

    /** Pilou dans une image (widget, notification). */
    public static Bitmap image(String expr, String couleur, int p) {
        return image(expr, couleur, "aucun", p);
    }

    public static Bitmap image(String expr, String couleur, String accessoire, int p) {
        Bitmap b = Bitmap.createBitmap((W + 2) * p, (H + 2) * p, Bitmap.Config.ARGB_8888);
        dessiner(new Canvas(b), 0, 0, p, expr, 0, couleur, accessoire, false, 0);
        return b;
    }
}
