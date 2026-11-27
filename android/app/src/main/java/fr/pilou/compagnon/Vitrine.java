package fr.pilou.compagnon;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Typeface;
import android.graphics.drawable.BitmapDrawable;
import android.os.SystemClock;
import android.provider.Settings;
import android.view.View;

/**
 * Pièces communes de la boutique rétro : images des articles (Pilou qui les porte, décor, bulle, icône),
 * silhouettes des rangées fermées, texte en police pixel, pièce d'or qui tourne et bandeau niveau / XP / po.
 * Couleurs : bleu, orange, argent, violet, neutres ; jamais d'opposition rouge / vert.
 */
final class Vitrine {
    static final int NUIT = 0xff151a2e, NUIT2 = 0xff1f2540, NUIT3 = 0xff2a3156, ENCRE = 0xff1c2128, ARGENT = 0xffadbac7,
            ARGENT_CLAIR = 0xffe6ecf2, BLEU = 0xff6cb6ff, BLEU_CLAIR = 0xffb4dbff, ORANGE = 0xfff69d50, ORANGE_CLAIR = 0xffffd8b0,
            VIOLET = 0xff9b8cff, VIOLET_FONCE = 0xff6a5acd, FERME = 0xff3b4654, GRIS = 0xff768390, SOL = 0xff16365e, CIEL = 0xff0d2a4d;

    private Vitrine() {
    }

    /** Les animations suivent le réglage système (« supprimer les animations » : tout reste immobile). */
    static boolean anime(Context c) {
        try {
            return Settings.Global.getFloat(c.getContentResolver(), Settings.Global.ANIMATOR_DURATION_SCALE, 1f) > 0;
        } catch (RuntimeException e) {
            return true;
        }
    }

    static String teinte(String id) {
        return id != null && id.startsWith("couleur-") ? id.substring("couleur-".length()) : id;
    }

    /** Allure de Pilou qui porte un article (ou dans sa couleur), stade 2. */
    static RenduPilou.Allure allure(Boutique.Article a, long t) {
        RenduPilou.Allure al = Dessin.allure("repos", t, "bleu", "", false, 0);
        if (a.slot.equals(Boutique.COULEUR)) al.couleur = teinte(a.id);
        else if (a.slot.equals(Boutique.ACCESSOIRE)) al.accessoire = a.id;
        else al.objets = java.util.Collections.singletonList(a.id);
        return al;
    }

    /** Pilou rendu dans une image (pixel de p points), en silhouette argent sombre si fermé. */
    static Bitmap pilou(RenduPilou.Allure al, float p, boolean silhouette) {
        int[] g = RenduPilou.rendre(al, Sprites.banque(), null);
        return image(g, Dessin.W, Dessin.H, p, silhouette);
    }

    /** Une image de sprite (décor, icône), pixel de p points ; null s'il manque. */
    static Bitmap sprite(String id, float p, double t, boolean silhouette) {
        Sprites.Sprite s = Sprites.banque().get(id);
        if (s == null) return null;
        int w = s.w(), h = s.h();
        int[] g = new int[w * h];
        Sprites.dessiner((x0, y0, x1, y1, c) -> {
            int x = Math.round(x0), y = Math.round(y0);
            if (x >= 0 && y >= 0 && x < w && y < h) g[y * w + x] = c;
        }, s, 0, 0, 1, t, false);
        return image(g, w, h, p, silhouette);
    }

    private static Bitmap image(int[] g, int w, int h, float p, boolean silhouette) {
        int pw = Math.max(1, Math.round(w * p)), ph = Math.max(1, Math.round(h * p));
        Bitmap b = Bitmap.createBitmap(pw, ph, Bitmap.Config.ARGB_8888);
        Canvas cv = new Canvas(b);
        Paint pt = new Paint();
        pt.setAntiAlias(false);
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++) {
                int c = g[y * w + x];
                if (c == 0 || (c >>> 24) == 0) continue;
                pt.setColor(silhouette ? FERME : c);
                cv.drawRect(x * p, y * p, (x + 1) * p, (y + 1) * p, pt);
            }
        return b;
    }

    /** Décor en fond de scène : image nette (pas de lissage), à recadrer par la vue. */
    static BitmapDrawable decor(Context c, String id) {
        Bitmap b = sprite(id, 1, 0, false);
        if (b == null) return null;
        BitmapDrawable d = new BitmapDrawable(c.getResources(), b);
        d.setFilterBitmap(false);
        d.setAntiAlias(false);
        return d;
    }

    /** Icône d'un bonus ou d'un consommable. */
    static String icone(String id) {
        return id;
    }

    /** Texte en police pixel (Police), avec ombre ; clignote doucement si « neon ». */
    static final class Pixel extends View {
        private String texte;
        private int couleur, ombre;
        private final float px;
        private final boolean neon;
        private final Paint pt = new Paint();

        Pixel(Context c, String texte, float pxDp, int couleur, int ombre, boolean neon) {
            super(c);
            this.texte = texte;
            this.couleur = couleur;
            this.ombre = ombre;
            this.px = Ui.dp(c, pxDp);
            this.neon = neon && anime(c);
            pt.setAntiAlias(false);
            setContentDescription(texte);
        }

        void texte(String s, int c) {
            texte = s;
            couleur = c;
            setContentDescription(s);
            requestLayout();
            invalidate();
        }

        @Override
        protected void onMeasure(int l, int h) {
            setMeasuredDimension(Math.round((Police.largeur(texte) + 1) * px), Math.round(6 * px));
        }

        @Override
        protected void onDraw(Canvas cv) {
            int c = couleur;
            if (neon) {
                // Enseigne néon : un grésillement bref toutes les quelques secondes.
                long k = SystemClock.uptimeMillis() / 140 % 37;
                if (k == 0 || k == 2) c = ORANGE_CLAIR;
                postInvalidateDelayed(140);
            }
            int cc = c;
            Dessin.Peintre pe = (g, hh, d, b, col) -> {
                pt.setColor(col);
                cv.drawRect(g, hh, d, b, pt);
            };
            if (ombre != 0) Police.ecrire(pe, texte, px, px, px, ombre);
            Police.ecrire(pe, texte, 0, 0, px, cc);
        }
    }

    /** Pièce d'or qui tourne (sprite po-tourne), immobile si les animations sont coupées. */
    static final class Piece extends View {
        private final float px;
        private final boolean anime;
        private final Paint pt = new Paint();

        Piece(Context c, float pxDp) {
            super(c);
            px = Ui.dp(c, pxDp);
            anime = anime(c);
            setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
        }

        @Override
        protected void onMeasure(int l, int h) {
            Sprites.Sprite s = Sprites.banque().get("po-tourne");
            int w = s == null ? 10 : s.w(), hh = s == null ? 10 : s.h();
            setMeasuredDimension(Math.round(w * px), Math.round(hh * px));
        }

        @Override
        protected void onDraw(Canvas cv) {
            long t = anime ? SystemClock.uptimeMillis() : 0;
            Sprites.dessiner((g, h, d, b, col) -> {
                pt.setColor(col);
                cv.drawRect(g, h, d, b, pt);
            }, Sprites.banque().get("po-tourne"), 0, 0, px, t, false);
            if (anime && isShown()) postInvalidateDelayed(120);
        }
    }

    /**
     * Bandeau permanent en haut de l'app : niveau (pastille pixel), mini barre d'XP, pièces d'or avec une pièce
     * qui tourne, titre ; dessous, la prochaine rangée de la boutique. Un toucher : la page des niveaux.
     */
    static final class Bandeau extends View {
        private int niveau = 1, xp, po = -1;
        private String titre = "", suite = "";
        private final Paint pt = new Paint(), txt = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final boolean anime;

        Bandeau(Context c) {
            super(c);
            pt.setAntiAlias(false);
            txt.setTypeface(Typeface.create("sans-serif-medium", Typeface.BOLD));
            anime = anime(c);
            setClickable(true);
            setFocusable(true);
        }

        void mettre(int niveau, int xp, int po, String titre, String suite) {
            if (niveau == this.niveau && xp == this.xp && po == this.po && titre.equals(this.titre) && suite.equals(this.suite)) return;
            this.niveau = niveau;
            this.xp = xp;
            this.po = po;
            this.titre = titre;
            this.suite = suite;
            int haut = Butin.xpPourNiveau(niveau + 1);
            setContentDescription("Niveau " + niveau + ", " + titre + ", " + xp + " sur " + haut + " xp"
                    + (po >= 0 ? ", " + po + " pièces d'or" : "") + (suite.isEmpty() ? "" : ". " + suite) + ". Toucher : voir les niveaux.");
            requestLayout();
            invalidate();
        }

        private float dp(float v) {
            return Ui.dp(getContext(), v);
        }

        @Override
        protected void onMeasure(int l, int h) {
            setMeasuredDimension(MeasureSpec.getSize(l), Math.round(dp(suite.isEmpty() ? 52 : 70)));
        }

        @Override
        protected void onDraw(Canvas cv) {
            float w = getWidth(), m = dp(12);
            cv.drawColor(NUIT);
            pt.setColor(VIOLET_FONCE);
            cv.drawRect(0, getHeight() - dp(2), w, getHeight(), pt);
            Dessin.Peintre pe = (g, hh, d, b, col) -> {
                pt.setColor(col);
                cv.drawRect(g, hh, d, b, pt);
            };
            // Pastille de niveau : « NIV » au-dessus du nombre, cadre violet.
            float bx = m, by = dp(6), bw = dp(42), bh = dp(40);
            pt.setColor(VIOLET);
            cv.drawRect(bx, by, bx + bw, by + bh, pt);
            pt.setColor(NUIT2);
            cv.drawRect(bx + dp(2), by + dp(2), bx + bw - dp(2), by + bh - dp(2), pt);
            float p1 = dp(1.5f);
            Police.centre(pe, "NIV", bx + bw / 2, by + dp(5), p1, ARGENT, 0);
            String n = String.valueOf(niveau);
            float p2 = n.length() >= 3 ? dp(2.5f) : dp(3.5f);
            Police.centre(pe, n, bx + bw / 2, by + dp(15), p2, ARGENT_CLAIR, ENCRE);
            // Pièces d'or à droite.
            String sPo = po < 0 ? "— po" : po + " po";
            txt.setTextSize(dp(16));
            txt.setColor(ORANGE);
            float lPo = txt.measureText(sPo);
            float xPo = w - m - lPo;
            cv.drawText(sPo, xPo, by + dp(20), txt);
            Sprites.Sprite piece = Sprites.banque().get("po-tourne");
            if (piece != null) {
                float pp = dp(1.6f);
                Sprites.dessiner(pe, piece, xPo - piece.w() * pp - dp(6), by + dp(7), pp, anime ? SystemClock.uptimeMillis() : 0, false);
            }
            // Titre, barre d'XP pixel, chiffres.
            float x0 = bx + bw + dp(10), x1 = xPo - dp(30);
            txt.setTextSize(dp(12));
            txt.setColor(ARGENT_CLAIR);
            String t = titre;
            while (t.length() > 3 && txt.measureText(t) > x1 - x0) t = t.substring(0, t.length() - 2);
            if (!t.equals(titre)) t = t + "…";
            cv.drawText(t, x0, by + dp(13), txt);
            // Niveau acquis gardé (comme l'Accueil) : si l'XP est sous le palier du niveau, la barre part du palier de la courbe.
            int bas = Butin.xpPourNiveau(Math.min(niveau, Butin.niveau(xp))), haut = Butin.xpPourNiveau(niveau + 1);
            float part = haut > bas ? Math.max(0, Math.min(1, (xp - bas) / (float) (haut - bas))) : 1;
            int cases = 16;
            float pas = (x1 - x0) / cases, ecart = Math.max(1, pas * 0.2f), yb = by + dp(19);
            int pleines = (int) Math.floor(part * cases);
            for (int i = 0; i < cases; i++) {
                pt.setColor(i < pleines ? BLEU : NUIT3);
                cv.drawRect(x0 + i * pas, yb, x0 + (i + 1) * pas - ecart, yb + dp(8), pt);
                if (i < pleines) {
                    pt.setColor(BLEU_CLAIR);
                    cv.drawRect(x0 + i * pas, yb, x0 + (i + 1) * pas - ecart, yb + dp(2), pt);
                }
            }
            txt.setTextSize(dp(10.5f));
            txt.setColor(ARGENT);
            txt.setTypeface(Typeface.DEFAULT);
            cv.drawText(Math.max(0, xp - bas) + " / " + (haut - bas) + " xp · niv " + (niveau + 1) + " dans " + Math.max(0, haut - xp) + " xp",
                    x0, yb + dp(20), txt);
            if (!suite.isEmpty()) {
                txt.setColor(VIOLET);
                txt.setTextSize(dp(11));
                String s = suite;
                while (s.length() > 3 && txt.measureText(s) > w - 2 * m) s = s.substring(0, s.length() - 2);
                cv.drawText(s.equals(suite) ? s : s + "…", m, getHeight() - dp(9), txt);
            }
            txt.setTypeface(Typeface.create("sans-serif-medium", Typeface.BOLD));
            if (anime && isShown()) postInvalidateDelayed(120);
        }
    }

    /** « ▲ Prochaine rangée : Dos, Main — niveau 15 (encore 340 xp) » ; vide quand tout est ouvert. */
    static String prochaineRangee(int niveau, int xp) {
        int p = Boutique.prochainPalier(niveau);
        if (p == 0) return "";
        java.util.List<String> r = Boutique.rayonsDuPalier(p);
        StringBuilder s = new StringBuilder();
        for (int i = 0; i < Math.min(3, r.size()); i++) s.append(i > 0 ? ", " : "").append(Boutique.nomSlot(r.get(i)));
        if (r.size() > 3) s.append(" +").append(r.size() - 3);
        return "▲ Prochaine rangée : " + s + " — niveau " + p + " (encore " + Math.max(0, Butin.xpPourNiveau(p) - xp) + " xp)";
    }
}
