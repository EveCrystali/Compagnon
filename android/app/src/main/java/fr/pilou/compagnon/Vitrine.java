package fr.pilou.compagnon;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Paint;
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

    /**
     * Enseigne : un mot en capitales dans la police pixel « titre », avec une ombre d'un pixel ; clignote doucement si
     * « neon ». pxDp : l'ancienne taille (police 3 × 5) ; la police de Pilou, plus haute, prend les trois quarts.
     */
    static final class Pixel extends View {
        private String texte;
        private int couleur, ombre;
        private final int px;
        private final boolean neon;
        private final Paint pt = new Paint();

        Pixel(Context c, String texte, float pxDp, int couleur, int ombre, boolean neon) {
            super(c);
            this.texte = texte;
            this.couleur = couleur;
            this.ombre = ombre;
            this.px = Style.pixel(c, Math.max(Style.PETIT, pxDp * 0.75f));
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
            // Les capitales occupent les rangées 3 à 9 : deux rangées d'accent au-dessus, une d'ombre au-dessous.
            setMeasuredDimension(Style.largeur(texte, px, true) + px + getPaddingLeft() + getPaddingRight(), 10 * px + getPaddingTop() + getPaddingBottom());
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
            int x = getPaddingLeft(), y = getPaddingTop() - px;
            if (ombre != 0) Style.ecrire(cv, texte, x + px, y + px, px, ombre, true, pt);
            Style.ecrire(cv, texte, x, y, px, c, true, pt);
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
     * Bandeau permanent en haut de l'app (docs/STYLE.md, « En-tête ») : pastille de niveau au cadre violet, titre,
     * barre d'XP en cases, chiffres, pièces d'or avec une pièce qui tourne ; dessous, la prochaine rangée de la
     * boutique, sur toute la largeur. Tout est écrit en police pixel. Un toucher : la page des niveaux.
     * La roue des Réglages se pose par-dessus, en haut à droite : le bandeau lui garde « reserve » pixels.
     */
    static final class Bandeau extends View {
        private int niveau = 1, xp, po = -1;
        private String titre = "";
        private String[] suites = {};
        private final Paint pt = new Paint();
        private final boolean anime;
        private final int u, pp, pc, reserve;

        Bandeau(Context c) {
            super(c);
            pt.setAntiAlias(false);
            anime = anime(c);
            u = Style.u(c);
            pp = Style.pixel(c, Style.PETIT);
            pc = Math.max(pp, Style.pixel(c, Style.CORPS));
            reserve = Ui.dp(c, 50);
            setClickable(true);
            setFocusable(true);
        }

        void mettre(int niveau, int xp, int po, String titre, String[] suites) {
            if (niveau == this.niveau && xp == this.xp && po == this.po && titre.equals(this.titre) && java.util.Arrays.equals(suites, this.suites)) return;
            this.niveau = niveau;
            this.xp = xp;
            this.po = po;
            this.titre = titre;
            this.suites = suites;
            int haut = Butin.xpPourNiveau(niveau + 1);
            setContentDescription("Niveau " + niveau + ", " + titre + ", " + xp + " sur " + haut + " xp"
                    + (po >= 0 ? ", " + po + " pièces d'or" : "") + (suites.length == 0 ? "" : ". Boutique, prochaines rangées : " + suites[0].replace("▲ ", ""))
                    + ". Toucher : voir les niveaux.");
            requestLayout();
            invalidate();
        }

        // Hauteurs, en pixels de l'écran : marge, titre (12 rangées), barre, chiffres, puis la ligne de la boutique.
        private int yTitre() {
            return 2 * u;
        }

        private int yBarre() {
            return yTitre() + 13 * pp;
        }

        private int yXp() {
            return yBarre() + 3 * u - pp;
        }

        private int basCorps() {
            return yXp() + 12 * pp + u;
        }

        @Override
        protected void onMeasure(int l, int h) {
            int haut = suites.length == 0 ? basCorps() + 2 * u : basCorps() - pp + 12 * pp + 2 * u;
            setMeasuredDimension(MeasureSpec.getSize(l), Math.max(haut, Ui.dp(getContext(), 52)));
        }

        @Override
        protected void onDraw(Canvas cv) {
            int w = getWidth(), m = Ui.dp(getContext(), 12);
            cv.drawColor(NUIT);
            // Liseré violet d'un module, sur toute la largeur (comme le cadre de l'en-tête du menu du PC).
            pt.setColor(VIOLET_FONCE);
            cv.drawRect(0, getHeight() - u, w, getHeight(), pt);
            // Pastille de niveau : « NIV » au-dessus du nombre, cadre violet d'un module.
            String n = String.valueOf(niveau);
            int bx = m, by = yTitre(), bh = basCorps() - by, bw = Math.max(Ui.dp(getContext(), 42), Style.largeur("NIV", pp, false) + 2 * u + 4 * pp);
            pt.setColor(VIOLET);
            cv.drawRect(bx, by, bx + bw, by + bh, pt);
            pt.setColor(NUIT2);
            cv.drawRect(bx + u, by + u, bx + bw - u, by + bh - u, pt);
            Style.centrer(cv, "NIV", bx + bw / 2f, by + u + pp - 3 * pp, pp, ARGENT, false, pt);
            int pn = Math.max(pp, Style.pixel(getContext(), Style.PAGE));
            while (pn > pp && (Style.largeur(n, pn, true) > bw - 2 * u - 2 * pp || 7 * pn > bh - 2 * u - 11 * pp)) pn--;
            int yn = by + u + 9 * pp + (bh - 2 * u - 9 * pp - 7 * pn) / 2;
            Style.centrer(cv, n, bx + bw / 2f, yn - 3 * pn, pn, ARGENT_CLAIR, true, pt);
            // Pièces d'or, à gauche de la roue.
            String sPo = po < 0 ? "— po" : po + " po";
            int xPo = w - reserve - Style.largeur(sPo, pc, true);
            Style.ecrire(cv, sPo, xPo, yTitre() + 2 * pp, pc, ORANGE, true, pt);
            Sprites.Sprite piece = Sprites.banque().get("po-tourne");
            int xPiece = xPo;
            if (piece != null) {
                xPiece = xPo - piece.w() * pp - 2 * u;
                Dessin.Peintre pe = (g, hh, d, b, col) -> {
                    pt.setColor(col);
                    cv.drawRect(g, hh, d, b, pt);
                };
                Sprites.dessiner(pe, piece, xPiece, yTitre() + 2 * pp + 3 * pc + (7 * pc - piece.h() * pp) / 2, pp, anime ? SystemClock.uptimeMillis() : 0, false);
            }
            // Titre, barre d'XP en cases, chiffres.
            int x0 = bx + bw + 2 * u, x1 = xPiece - 2 * u;
            Style.ecrire(cv, Style.tronquer(titre, pp, true, x1 - x0), x0, yTitre(), pp, ARGENT_CLAIR, true, pt);
            // Niveau acquis gardé (comme l'Accueil) : si l'XP est sous le palier du niveau, la barre part du palier de la courbe.
            int bas = Butin.xpPourNiveau(Math.min(niveau, Butin.niveau(xp))), haut = Butin.xpPourNiveau(niveau + 1);
            float part = haut > bas ? Math.max(0, Math.min(1, (xp - bas) / (float) (haut - bas))) : 1;
            int pas = 4 * u, cases = Math.max(1, (x1 - x0 + u) / pas), yb = yBarre();
            int pleines = (int) Math.floor(part * cases);
            for (int i = 0; i < cases; i++) {
                pt.setColor(i < pleines ? BLEU : NUIT3);
                cv.drawRect(x0 + i * pas, yb, x0 + i * pas + 3 * u, yb + 3 * u, pt);
                if (i < pleines) {
                    pt.setColor(BLEU_CLAIR);
                    cv.drawRect(x0 + i * pas, yb, x0 + i * pas + 3 * u, yb + u, pt);
                }
            }
            String dans = Math.max(0, xp - bas) + " / " + (haut - bas) + " xp";
            String chiffres = Style.choisir(new String[]{dans + " · niveau " + (niveau + 1) + " dans " + Math.max(0, haut - xp) + " xp",
                    dans + " · niv " + (niveau + 1) + " dans " + Math.max(0, haut - xp) + " xp", dans}, pp, false, w - reserve - x0);
            Style.ecrire(cv, chiffres, x0, yXp(), pp, ARGENT, false, pt);
            if (suites.length > 0)
                Style.ecrire(cv, Style.choisir(suites, pp, false, w - 2 * m), m, basCorps() - pp, pp, VIOLET, false, pt);
            if (anime && isShown()) postInvalidateDelayed(120);
        }
    }

    /** « ▲ Niveau 15 : Dos, Main · encore 340 xp » : la prochaine rangée de la boutique ; vide quand tout est ouvert. */
    static String prochaineRangee(int niveau, int xp) {
        String[] f = prochainesRangees(niveau, xp);
        return f.length == 0 ? "" : f[0];
    }

    /** La même annonce, de la plus longue à la plus courte : le bandeau prend la première qui tient sur sa ligne. */
    static String[] prochainesRangees(int niveau, int xp) {
        int p = Boutique.prochainPalier(niveau);
        if (p == 0) return new String[0];
        java.util.List<String> r = Boutique.rayonsDuPalier(p);
        StringBuilder s = new StringBuilder();
        for (int i = 0; i < Math.min(3, r.size()); i++) s.append(i > 0 ? ", " : "").append(Boutique.nomSlot(r.get(i)));
        if (r.size() > 3) s.append(" +").append(r.size() - 3);
        String tete = "▲ Niveau " + p + " : ";
        return new String[]{tete + s + " · encore " + Math.max(0, Butin.xpPourNiveau(p) - xp) + " xp", tete + s,
                tete + r.size() + (r.size() > 1 ? " rangées" : " rangée")};
    }
}
