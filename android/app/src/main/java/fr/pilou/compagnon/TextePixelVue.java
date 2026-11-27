package fr.pilou.compagnon;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Typeface;
import android.view.View;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Un texte écrit avec la police pixel de Pilou (PolicePixel.java, docs/POLICE.md) : coupé à la largeur disponible,
 * chaque pixel de police sur un nombre entier de pixels de l'écran, dessin fin (2×) quand il tombe juste. Un
 * caractère sans dessin (emoji…) est écrit par la police système dans sa case. Même rendu que TextePixel.cs (PC).
 */
public final class TextePixelVue extends View {
    private String texte = "";
    private int couleur;
    private final int pixel;          // pixels de l'écran par pixel de police (1×)
    private int maxLignes, maxLargeur;
    private List<String> lignes = Collections.emptyList();
    private final Paint encre = new Paint();
    private final Paint systeme = new Paint(Paint.ANTI_ALIAS_FLAG);

    /** tailleDp : taille voulue d'un pixel de police, ramenée au nombre entier de pixels de l'écran le plus proche. */
    public TextePixelVue(Context c, float tailleDp, int couleur) {
        super(c);
        pixel = pixels(tailleDp, c.getResources().getDisplayMetrics().density);
        this.couleur = couleur;
        encre.setColor(couleur);
        systeme.setColor(couleur);
        systeme.setTypeface(Typeface.DEFAULT);
    }

    /** Pixels de l'écran par pixel de police : au moins 1, le plus proche de la taille voulue. */
    public static int pixels(float tailleDp, float densite) {
        return Math.max(1, Math.round(tailleDp * densite));
    }

    public void texte(String s) {
        String t = s == null ? "" : s;
        if (t.equals(texte)) return;
        texte = t;
        setContentDescription(t);
        requestLayout();
        invalidate();
    }

    public String texte() {
        return texte;
    }

    public void couleur(int c) {
        couleur = c;
        encre.setColor(c);
        systeme.setColor(c);
        invalidate();
    }

    /** Largeur maximale en pixels de l'écran (0 : celle que donne le parent). */
    public void maxLargeur(int px) {
        maxLargeur = px;
        requestLayout();
    }

    public void maxLignes(int n) {
        maxLignes = n;
        requestLayout();
    }

    @Override
    protected void onMeasure(int mw, int mh) {
        PolicePixel p = PolicePixel.texte();
        if (p == null) {
            setMeasuredDimension(0, 0);
            return;
        }
        int mode = MeasureSpec.getMode(mw);
        int dispo = mode == MeasureSpec.UNSPECIFIED ? Integer.MAX_VALUE : MeasureSpec.getSize(mw);
        if (maxLargeur > 0) dispo = Math.min(dispo, maxLargeur);
        dispo -= getPaddingLeft() + getPaddingRight();
        int max = dispo >= Integer.MAX_VALUE / 2 ? 0 : Math.max(1, dispo / pixel);
        lignes = p.couper(texte, max, maxLignes);
        int[] b = p.boite(lignes);
        int w = b[0] * pixel + getPaddingLeft() + getPaddingRight();
        if (mode == MeasureSpec.EXACTLY) w = MeasureSpec.getSize(mw);
        setMeasuredDimension(w, b[1] * pixel + getPaddingTop() + getPaddingBottom());
    }

    @Override
    protected void onDraw(Canvas c) {
        dessiner(c, lignes, pixel, getPaddingLeft(), getPaddingTop(), encre, systeme);
    }

    /** Écrit des lignes déjà coupées, à (x, y), un pixel de police = pixel pixels de l'écran. */
    static void dessiner(Canvas c, List<String> lignes, int pixel, float x0, float y0, Paint encre, Paint systeme) {
        PolicePixel p = PolicePixel.texte();
        if (p == null) return;
        PolicePixel d = pixel % 2 == 0 ? PolicePixel.ressource("texte2x") : null;
        if (d == null) d = p;
        float pas = (float) pixel / d.echelle;
        for (PolicePixel.Pose pose : d.poser(lignes)) {
            if (pose.dessin == null) {
                if (pose.code != ' ' && pose.code != 0xA0 && pose.code != 0x202F && pose.code != 0x2009) {
                    systeme.setTextSize(9f * pixel);
                    String s = new String(Character.toChars(pose.code));
                    float cx = x0 + pose.x * pixel + p.inconnu * pixel / 2f, cy = y0 + pose.y * pixel + 6.5f * pixel;
                    Paint.FontMetrics fm = systeme.getFontMetrics();
                    c.drawText(s, cx - systeme.measureText(s) / 2, cy - (fm.ascent + fm.descent) / 2, systeme);
                }
                continue;
            }
            String[] rangs = pose.dessin.rangs;
            for (int r = 0; r < rangs.length; r++) {
                int k = 0;
                while (k < rangs[r].length()) {
                    if (rangs[r].charAt(k) != '#') {
                        k++;
                        continue;
                    }
                    int fin = k;
                    while (fin < rangs[r].length() && rangs[r].charAt(fin) == '#') fin++;
                    float x = x0 + pose.x * pixel + k * pas, y = y0 + pose.y * pixel + (pose.dessin.haut + r) * pas;
                    c.drawRect(x, y, x + (fin - k) * pas, y + pas, encre);
                    k = fin;
                }
            }
        }
    }

    /**
     * Image d'un texte (widget : RemoteViews n'accepte pas de vue maison), coupé à largeurMax pixels de l'écran ;
     * null si le texte est vide ou la police absente.
     */
    static Bitmap image(Context ctx, String texte, float tailleDp, int couleur, int largeurMax, int maxLignes) {
        PolicePixel p = PolicePixel.texte();
        if (p == null || texte == null || texte.isEmpty()) return null;
        float densite = ctx.getResources().getDisplayMetrics().density;
        int pixel = pixels(tailleDp, densite);
        List<String> lignes = new ArrayList<>(p.couper(texte, largeurMax <= 0 ? 0 : Math.max(1, largeurMax / pixel), maxLignes));
        int[] b = p.boite(lignes);
        if (b[0] <= 0 || b[1] <= 0) return null;
        Bitmap bmp = Bitmap.createBitmap(b[0] * pixel, b[1] * pixel, Bitmap.Config.ARGB_8888);
        bmp.setDensity(ctx.getResources().getDisplayMetrics().densityDpi);
        Paint encre = new Paint();
        encre.setColor(couleur);
        Paint systeme = new Paint(Paint.ANTI_ALIAS_FLAG);
        systeme.setColor(couleur);
        dessiner(new Canvas(bmp), lignes, pixel, 0, 0, encre, systeme);
        return bmp;
    }
}
