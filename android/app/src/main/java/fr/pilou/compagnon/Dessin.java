package fr.pilou.compagnon;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Paint;

import java.util.Collections;
import java.util.List;

/**
 * Pilou en pixel art, grille de 48 × 56 commune au PC et au téléphone (RenduPilou), dessiné dans un carré de
 * (W + 2) × (H + 2) pixels de p points (un pixel de marge). Tout ce qu'il porte vient de la banque de sprites.
 */
public final class Dessin {
    public static final int W = RenduPilou.W, H = RenduPilou.H;
    /** À taille affichée égale, un pixel de cette grille vaut 28/50 d'un pixel de la grille d'origine (26 × 30). */
    public static final float ECHELLE = 28f / 50f;

    /** Ce qui peint un rectangle : un Canvas Android, ou une image ordinaire pour les essais hors téléphone. */
    public interface Peintre {
        void rect(float gauche, float haut, float droite, float bas, int argb);
    }

    private Dessin() {
    }

    public static void dessiner(Canvas cv, float x0, float y0, float p, String expr, long t, String couleur, boolean cligne, float saut) {
        dessiner(cv, x0, y0, p, expr, t, couleur, "aucun", cligne, saut);
    }

    public static void dessiner(Canvas cv, float x0, float y0, float p, String expr, long t, String couleur, String accessoire,
                                boolean cligne, float saut) {
        dessiner(peintre(cv), x0, y0, p, allure(expr, t, couleur, accessoire, cligne, saut));
    }

    public static void dessiner(Peintre pe, float x0, float y0, float p, String expr, long t, String couleur, String accessoire,
                                boolean cligne, float saut) {
        dessiner(pe, x0, y0, p, allure(expr, t, couleur, accessoire, cligne, saut));
    }

    /** Tout ce que le PC sait : stade, évolution, tenue, objets de boutique… */
    public static void dessiner(Canvas cv, float x0, float y0, float p, RenduPilou.Allure a) {
        dessiner(peintre(cv), x0, y0, p, a);
    }

    public static void dessiner(Peintre pe, float x0, float y0, float p, RenduPilou.Allure a) {
        int[] g = RenduPilou.rendre(a, Sprites.banque(), null);
        for (int y = 0; y < H; y++)
            for (int x = 0; x < W; x++) {
                int c = g[y * W + x];
                if (c != 0) pe.rect(x0 + (x + 1) * p, y0 + (y + 1) * p, x0 + (x + 2) * p, y0 + (y + 2) * p, c);
            }
    }

    /** Rendu fin (grille 96 × 112) dans le même carré : p reste la taille d'un pixel de la grille 48 × 56. */
    public static void dessinerFin(Peintre pe, float x0, float y0, float p, RenduPilou.Allure a) {
        int[] g = RenduPilou.rendre(a, Sprites.banque(), null, 2);
        float f = p / 2;
        for (int y = 0; y < 2 * H; y++)
            for (int x = 0; x < 2 * W; x++) {
                int c = g[y * 2 * W + x];
                if (c != 0) pe.rect(x0 + (x + 2) * f, y0 + (y + 2) * f, x0 + (x + 3) * f, y0 + (y + 3) * f, c);
            }
    }

    /**
     * Pixels physiques d'un pixel fin pour une vue dont le pixel de grille vaut p : l'entier le plus proche, pour que
     * chaque pixel fin tombe sur un nombre entier de pixels de l'écran. Moins de 2 : la vue reste au rendu 1×.
     */
    public static int pixelFin(float p) {
        return Math.round(p / 2);
    }

    /**
     * Image de Pilou au rendu fin, réécrite d'une image à l'autre sans rien allouer : une vue animée la garde et la
     * dessine d'un seul trait (un bitmap de 96 × 112 agrandi au plus proche voisin) au lieu d'un rectangle par pixel.
     */
    public static final class ImageFine {
        public static final int LARGEUR = 2 * W, HAUTEUR = 2 * H;
        private final RenduPilou.Tampon tampon = new RenduPilou.Tampon();
        private final int[] dernier = new int[LARGEUR * HAUTEUR];
        private final Bitmap bitmap = Bitmap.createBitmap(LARGEUR, HAUTEUR, Bitmap.Config.ARGB_8888);
        private final Paint pinceau = new Paint();
        private final android.graphics.RectF cadre = new android.graphics.RectF();
        private boolean pleine;

        public ImageFine() {
            pinceau.setAntiAlias(false);
            pinceau.setFilterBitmap(false);
            pinceau.setDither(false);
        }

        /** Rend l'allure ; le bitmap n'est réécrit que si des pixels ont changé (Pilou respire lentement). */
        public void rendre(RenduPilou.Allure a) {
            int[] g = RenduPilou.rendre(a, Sprites.banque(), null, 2, tampon);
            if (pleine && java.util.Arrays.equals(g, dernier)) return;
            System.arraycopy(g, 0, dernier, 0, dernier.length);
            bitmap.setPixels(dernier, 0, LARGEUR, 0, 0, LARGEUR, HAUTEUR);
            pleine = true;
        }

        /** Dessine l'image, coin haut-gauche de la grille en (x0, y0), f pixels de l'écran par pixel fin. */
        public void dessiner(Canvas cv, float x0, float y0, float f) {
            cadre.set(x0, y0, x0 + LARGEUR * f, y0 + HAUTEUR * f);
            cv.drawBitmap(bitmap, null, cadre, pinceau);
        }
    }

    public static RenduPilou.Allure allure(String expr, long t, String couleur, String accessoire, boolean cligne, float saut) {
        RenduPilou.Allure a = new RenduPilou.Allure();
        a.expr = expr == null ? "repos" : expr;
        a.t = t;
        a.couleur = couleur == null ? "bleu" : couleur;
        a.accessoire = accessoire == null || accessoire.equals("aucun") ? "" : accessoire;
        a.cligne = cligne;
        a.saut = saut;
        return a;
    }

    private static Peintre peintre(Canvas cv) {
        Paint pt = new Paint();
        pt.setAntiAlias(false);
        return (g, h, d, b, c) -> {
            pt.setColor(c);
            cv.drawRect(g, h, d, b, pt);
        };
    }

    /** Pilou dans une image (widget, notification) : même encombrement qu'avant (36 pixels d'origine par p). */
    public static Bitmap image(String expr, String couleur, int p) {
        return image(expr, couleur, "aucun", p);
    }

    public static Bitmap image(String expr, String couleur, String accessoire, int p) {
        return image(allure(expr, 0, couleur, accessoire, false, 0), p);
    }

    public static Bitmap image(RenduPilou.Allure a, int p) {
        float pf = p * 36f / (W + 2);
        int lw = Math.round((W + 2) * pf), lh = Math.round((H + 2) * pf);
        Bitmap b = Bitmap.createBitmap(lw, lh, Bitmap.Config.ARGB_8888);
        dessiner(new Canvas(b), 0, 0, pf, a);
        return b;
    }

    /** Un objet seul (prise, plat, jeu…) tiré de la banque. */
    public static void objet(Peintre pe, String id, float x0, float y0, float p, double t, boolean miroir) {
        Sprites.dessiner(pe, Sprites.banque().get(id), x0, y0, p, t, miroir);
    }

    /** Objets de boutique équipés, depuis une liste séparée par des virgules (état du PC). */
    static List<String> liste(String s) {
        if (s == null || s.trim().isEmpty()) return Collections.emptyList();
        return java.util.Arrays.asList(s.trim().split("\\s*,\\s*"));
    }
}
