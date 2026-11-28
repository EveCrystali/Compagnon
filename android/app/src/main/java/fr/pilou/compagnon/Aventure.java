package fr.pilou.compagnon;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Matrix;
import android.graphics.Paint;
import android.os.SystemClock;
import android.view.View;

/**
 * Pièces communes de l'onglet Aventure (campagnes, docs/CAMPAGNES.md) : le ton d'une campagne (couleurs et signe de
 * forme), les issues des fins, les noms des épreuves, la scène (décor dessiné net, sinon un ciel pixel aux couleurs du
 * ton qui défile quand Pilou marche), les points d'écriture « … » et les étincelles d'une belle fin.
 * Couleurs : bleu, orange, violet, argent et crème ; jamais d'opposition rouge / vert ; chaque état a son signe.
 */
final class Aventure {
    private Aventure() {
    }

    static final int CREME = 0xfffff4e0, VIOLET_DOUX = 0xffc9b8ff;

    // ---- Ton d'une campagne

    static String signeTon(String ton) {
        switch (ton) {
            case "mystere": return "◆";
            case "emotion": return "♥";
            case "epique": return "▲";
            default: return "☼";
        }
    }

    static String nomTon(String ton) {
        switch (ton) {
            case "mystere": return "Mystère";
            case "emotion": return "Émotion";
            case "epique": return "Épique";
            default: return "Drôle";
        }
    }

    /** Couleur d'accent du ton, lisible sur le fond de la page (clair ou sombre). */
    static int accentTon(Context c, String ton) {
        Ui.Palette p = Ui.p(c);
        boolean sombre = Ui.sombre(c);
        switch (ton) {
            case "mystere":
            case "epique": return p.bleu;
            case "emotion": return sombre ? Vitrine.VIOLET : Vitrine.VIOLET_FONCE;
            default: return p.orange;
        }
    }

    /** Ciel (haut, bas), collines (loin, près) et lumière (soleil, lune, étoiles) d'un ton. */
    static int[] cielTon(String ton) {
        switch (ton) {
            case "mystere": return new int[]{0xff070b1c, 0xff26406e, 0xff18294a, 0xff0c1426, 0xffd9e6ff};
            case "emotion": return new int[]{0xff2a2156, 0xffd2a8d8, 0xff6d5aa8, 0xff3b2f6b, CREME};
            case "epique": return new int[]{0xff0f1a36, 0xff6a9fe0, 0xff3a5a96, 0xff1b2a52, 0xffffe9b8};
            default: return new int[]{0xff2a3f84, 0xfff0a36a, 0xff8a4f86, 0xff4a2f63, 0xffffe3a8};
        }
    }

    // ---- Issues des fins

    static String signeIssue(String issue) {
        switch (issue) {
            case "douce-amere": return "◐";
            case "mauvaise": return "▽";
            case "secrete": return "✧";
            default: return "★";
        }
    }

    static String nomIssue(String issue) {
        switch (issue) {
            case "douce-amere": return "Fin douce-amère";
            case "mauvaise": return "Mauvaise fin";
            case "secrete": return "Fin secrète";
            default: return "Bonne fin";
        }
    }

    static int couleurIssue(Context c, String issue) {
        Ui.Palette p = Ui.p(c);
        switch (issue) {
            case "douce-amere": return Ui.sombre(c) ? Vitrine.VIOLET : Vitrine.VIOLET_FONCE;
            case "mauvaise": return p.argent;
            case "secrete": return p.bleu;
            default: return p.orange;
        }
    }

    // ---- Épreuves

    static String nomJeu(String jeu) {
        switch (jeu) {
            case "reflexe": return "Réflexe";
            case "memoire": return "Mémoire";
            case "rythme": return "Rythme";
            case "visee": return "Visée";
            default: return "Les dés";
        }
    }

    static String consigneJeu(String jeu) {
        switch (jeu) {
            case "reflexe": return "Touche quand le curseur passe dans la zone orange.";
            case "memoire": return "Regarde bien la suite de signes, puis refais-la.";
            case "rythme": return "Touche l'écran quand chaque note arrive sur la ligne.";
            case "visee": return "Touche les cibles avant qu'elles ne filent.";
            default: return "Les dés décident pour Pilou.";
        }
    }

    /** « ◆◆◇ » : la difficulté se lit à la forme. */
    static String difficulte(int d) {
        StringBuilder b = new StringBuilder();
        for (int i = 1; i <= 3; i++) b.append(i <= d ? "◆" : "◇");
        return b.toString();
    }

    /** Pixel de grille de PilouVue pour un Pilou d'environ h dp de haut. */
    static float pixelPour(Context c, float hDp) {
        return hDp / ((Dessin.H + 2) * Dessin.ECHELLE) * c.getResources().getDisplayMetrics().density;
    }

    /**
     * L'unité de pixel de tout l'écran Aventure : celle du décor fin (192 pixels de large), le plus grand entier qui
     * tient dans la largeur (au moins 1). Décor, ciel de repli, portrait et Pilou la partagent : on ajuste la taille
     * des vues, jamais l'échelle d'une couche.
     */
    static int unite(int largeurPx) {
        return Math.max(1, largeurPx / Theatre.W);
    }

    /** Pixel de grille de PilouVue pour que le pixel fin de Pilou fasse k pixels d'écran (2k par pixel 1×). */
    static float pixelUnite(int k) {
        return 2f * k / Dessin.ECHELLE;
    }

    /** Pilou marche-t-il sur place dans cette tenue (le décor défile alors) ? */
    static float vitesse(String tenue) {
        switch (tenue) {
            case "course": return 9f;
            case "marche": return 4f;
            case "bateau":
            case "nage": return 2.5f;
            default: return 0f;
        }
    }

    // ---- La scène

    /**
     * Bande de décor : le sprite « decor-&lt;campagne&gt;-&lt;décor&gt; » s'il existe, posé au sol et agrandi d'un nombre entier
     * de pixels (net) ; sinon un ciel pixel en dégradé aux couleurs du ton, des collines tirées du nom du décor (chaque
     * lieu a son relief), le soleil, la lune ou des étoiles. Quand Pilou marche, le décor défile lentement.
     */
    static final class Scene extends View {
        private String campagne = "", ton = "humour", decor = "";
        private float vitesse;
        private boolean nuit;
        private Bitmap image, ciel, loin, pres;
        private String cle = "";
        private int bloc;
        private final Paint pt = new Paint();
        private final Matrix m = new Matrix();
        private final boolean anime;
        private final long t0 = SystemClock.uptimeMillis();
        /** Le décor dessiné, animé en boucle (ScenesAnimees.Decor : volet entre deux décors, ralenti dans les listes). */
        private final ScenesAnimees.Decor vivant = new ScenesAnimees.Decor();
        private String niveau = Animations.COMPLETES;

        Scene(Context c) {
            super(c);
            pt.setAntiAlias(false);
            pt.setFilterBitmap(false);
            anime = Vitrine.anime(c);
            vivant.ralenti = true;
            setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
        }

        /** Lecture : le décor vit à sa vitesse, et change par un volet ; ailleurs (listes, accueil), au ralenti. */
        void plein(boolean oui) {
            vivant.ralenti = !oui;
        }

        /** Le décor courant (décor vide : celui du ton seul). */
        void regler(String campagne, String ton, String decor) {
            campagne = campagne == null ? "" : campagne;
            ton = ton == null || ton.isEmpty() ? "humour" : ton;
            decor = decor == null ? "" : decor;
            if (campagne.equals(this.campagne) && ton.equals(this.ton) && decor.equals(this.decor)) return;
            this.campagne = campagne;
            this.ton = ton;
            this.decor = decor;
            cle = "";
            invalidate();
        }

        /** Pilou marche (blocs par seconde ; 0 : le décor reste immobile). nuit : le ciel s'assombrit (repos, nuit). */
        void marcher(float v, boolean nuit) {
            if (v == vitesse && nuit == this.nuit) return;
            vitesse = v;
            if (nuit != this.nuit) cle = "";
            this.nuit = nuit;
            invalidate();
        }

        boolean illustree() {
            preparer();
            return image != null || vivant.sprite() != null;
        }

        private void preparer() {
            int w = getWidth(), h = getHeight();
            if (w <= 0 || h <= 0) return;
            String k = campagne + "|" + ton + "|" + decor + "|" + w + "|" + h + "|" + nuit;
            if (k.equals(cle)) return;
            cle = k;
            niveau = ScenesAnimees.niveau(getContext());
            Sprites.Sprite dessin = null;
            try {
                dessin = decor.isEmpty() ? null : Sprites.decor(Sprites.banque(), campagne, decor, 2);
            } catch (RuntimeException x) {
                Journal.noter("scène : décor animé", x);
            }
            vivant.regler(dessin, SystemClock.uptimeMillis() - t0, niveau);
            image = dessin == null ? (decor.isEmpty() ? null : Vitrine.sprite("decor-" + campagne + "-" + decor, 1, 0, false)) : null;
            ciel = loin = pres = null;
            if (image != null || dessin != null) return;
            bloc = unite(w);
            int cols = w / bloc + 2, rangs = h / bloc + 1;
            int[] t = cielTon(ton);
            int haut = nuit ? melanger(t[0], 0xff05070f, 0.5f) : t[0], bas = nuit ? melanger(t[1], t[0], 0.55f) : t[1];
            int[] px = new int[cols * rangs];
            for (int y = 0; y < rangs; y++) {
                float f = y / (float) Math.max(1, rangs - 1) * 7;
                int bande = (int) f;
                float reste = f - bande;
                for (int x = 0; x < cols; x++) {
                    int b = bande + (reste > 0.7f && ((x + y) & 1) == 0 ? 1 : 0); // trame entre deux bandes
                    px[y * cols + x] = melanger(haut, bas, Math.min(7, b) / 7f);
                }
            }
            long graine = Campagnes.code(campagne + "/" + decor).hashCode();
            java.util.Random r = new java.util.Random(graine);
            // Lumière : soleil (couchant ou d'aube), lune, étoiles.
            boolean etoiles = nuit || ton.equals("mystere") || ton.equals("epique");
            if (etoiles)
                for (int i = 0; i < cols * rangs / 90; i++) {
                    int x = r.nextInt(cols), y = r.nextInt(Math.max(1, rangs / 2));
                    px[y * cols + x] = melanger(t[4], haut, 0.2f + r.nextFloat() * 0.5f);
                }
            int cx = (int) (cols * (0.62f + r.nextFloat() * 0.25f)), cy = (int) (rangs * (etoiles ? 0.22f : 0.5f)), rayon = Math.max(3, rangs / 7);
            for (int y = Math.max(0, cy - rayon); y < Math.min(rangs, cy + rayon + 1); y++)
                for (int x = Math.max(0, cx - rayon); x < Math.min(cols, cx + rayon + 1); x++) {
                    int dx = x - cx, dy = y - cy;
                    if (dx * dx + dy * dy > rayon * rayon) continue;
                    boolean croissant = etoiles && (dx + 2) * (dx + 2) + (dy - 1) * (dy - 1) <= rayon * rayon;
                    if (!croissant) px[y * cols + x] = t[4];
                }
            ciel = Bitmap.createBitmap(px, cols, rangs, Bitmap.Config.ARGB_8888);
            loin = collines(cols * 3, rangs, r, 0.48f, 0.18f, nuit ? melanger(t[2], 0xff05070f, 0.4f) : t[2]);
            pres = collines(cols * 3, rangs, r, 0.72f, 0.14f, nuit ? melanger(t[3], 0xff05070f, 0.4f) : t[3]);
        }

        private static Bitmap collines(int cols, int rangs, java.util.Random r, float base, float amp, int couleur) {
            int[] px = new int[cols * rangs];
            double a = r.nextDouble() * 6, b = r.nextDouble() * 6, f1 = 2 * Math.PI * (2 + r.nextInt(3)) / cols, f2 = 2 * Math.PI * (5 + r.nextInt(4)) / cols;
            int bord = melanger(couleur, 0xffffffff, 0.12f);
            for (int x = 0; x < cols; x++) {
                double y = rangs * (base - amp * (Math.sin(x * f1 + a) + 0.45 * Math.sin(x * f2 + b)) / 1.45);
                int sommet = Math.max(0, Math.min(rangs - 1, (int) Math.round(y)));
                for (int k = sommet; k < rangs; k++) px[k * cols + x] = k == sommet ? bord : couleur;
            }
            return Bitmap.createBitmap(px, cols, rangs, Bitmap.Config.ARGB_8888);
        }

        static int melanger(int a, int b, float k) {
            k = Math.max(0, Math.min(1, k));
            int ra = (a >> 16) & 255, ga = (a >> 8) & 255, ba = a & 255, rb = (b >> 16) & 255, gb = (b >> 8) & 255, bb = b & 255;
            return 0xff000000 | Math.round(ra + (rb - ra) * k) << 16 | Math.round(ga + (gb - ga) * k) << 8 | Math.round(ba + (bb - ba) * k);
        }

        @Override
        protected void onDraw(Canvas cv) {
            preparer();
            int w = getWidth(), h = getHeight();
            if (w <= 0 || h <= 0) return;
            float t = anime ? (SystemClock.uptimeMillis() - t0) / 1000f : 0;
            boolean bouge = anime && vitesse > 0;
            if (vivant.sprite() != null) {
                // Décor animé (dessin fin) : agrandi d'un nombre entier de pixels, posé au sol ; il défile quand Pilou marche.
                long ms = SystemClock.uptimeMillis() - t0;
                Sprites.Sprite sp = vivant.sprite();
                int k = Math.max(1, unite(w) * Theatre.W / Math.max(1, sp.w()));   // une seule unité de pixel : celle du décor fin
                float iw = sp.w() * k, ih = sp.h() * k;
                float x0 = bouge ? -((t * vitesse * k / 2) % iw) : (w - iw) / 2;
                if (!bouge && iw < w) x0 = 0;
                try {
                    for (float x = x0; x < w; x += iw) {
                        vivant.dessiner(cv, pt, ms, niveau, Math.round(x), Math.round(h - ih), k);
                        if (!bouge && iw >= w) break;
                    }
                } catch (RuntimeException x) {
                    Journal.noter("scène : dessin du décor", x);
                }
                long pas = vivant.prochain(ms, niveau);
                if (isShown() && !bouge && pas > 0) postInvalidateDelayed(pas);
            } else if (image != null) {
                // Décor illustré : agrandi d'un nombre entier de pixels pour couvrir la hauteur, posé au sol.
                int k = Math.max(1, unite(w) * Theatre.W / Math.max(1, image.getWidth()));
                float iw = image.getWidth() * k, ih = image.getHeight() * k;
                float x0 = bouge ? -((t * vitesse * k) % iw) : (w - iw) / 2;
                if (!bouge && iw < w) x0 = 0;
                for (float x = x0; x < w; x += iw) {
                    m.reset();
                    m.setScale(k, k);
                    m.postTranslate(Math.round(x), Math.round(h - ih));
                    cv.drawBitmap(image, m, pt);
                    if (!bouge && iw >= w) break;
                }
            } else if (ciel != null) {
                m.reset();
                m.setScale(bloc, bloc);
                cv.drawBitmap(ciel, m, pt);
                dessinerCouche(cv, loin, bouge ? t * vitesse * 0.35f : 0);
                dessinerCouche(cv, pres, bouge ? t * vitesse : 0);
                // Étoiles qui scintillent (deux ou trois à la fois).
                if (anime && (nuit || ton.equals("mystere") || ton.equals("epique"))) {
                    long k = SystemClock.uptimeMillis() / 400;
                    java.util.Random r = new java.util.Random(k);
                    pt.setColor(cielTon(ton)[4]);
                    for (int i = 0; i < 3; i++) {
                        float x = r.nextInt(Math.max(1, w / bloc)) * bloc, y = r.nextInt(Math.max(1, h / bloc / 3)) * bloc;
                        cv.drawRect(x, y, x + bloc, y + bloc, pt);
                    }
                }
            }
            if (anime && isShown() && (bouge || (image == null && vivant.sprite() == null))) postInvalidateDelayed(bouge ? 66 : 400);
        }

        private void dessinerCouche(Canvas cv, Bitmap b, float decalage) {
            if (b == null) return;
            float largeur = b.getWidth() * bloc;
            float x0 = -((decalage * bloc) % largeur);
            for (float x = x0; x < getWidth(); x += largeur) {
                m.reset();
                m.setScale(bloc, bloc);
                m.postTranslate(Math.round(x / bloc) * bloc, 0);
                cv.drawBitmap(b, m, pt);
            }
        }
    }

    // ---- Les points d'écriture « … »

    /** Trois points pixel qui sautillent : Pilou écrit. */
    static final class Points extends View {
        private final Paint pt = new Paint();
        private final int couleur;
        private final boolean anime;

        Points(Context c, int couleur) {
            super(c);
            this.couleur = couleur;
            anime = Vitrine.anime(c);
            setContentDescription("Pilou écrit…");
        }

        @Override
        protected void onMeasure(int l, int h) {
            setMeasuredDimension(Ui.dp(getContext(), 34), Ui.dp(getContext(), 16));
        }

        @Override
        protected void onDraw(Canvas cv) {
            float b = Ui.dp(getContext(), 5), ecart = Ui.dp(getContext(), 6);
            long t = SystemClock.uptimeMillis();
            for (int i = 0; i < 3; i++) {
                double phase = anime ? Math.sin((t / 160.0) - i * 0.9) : 0;
                float y = getHeight() - b - (float) Math.max(0, phase) * Ui.dp(getContext(), 5);
                pt.setColor(couleur);
                pt.setAlpha(anime ? (int) (150 + 105 * Math.max(0, phase)) : 255);
                float x = i * (b + ecart);
                cv.drawRect(Math.round(x), Math.round(y), Math.round(x + b), Math.round(y + b), pt);
            }
            if (anime && isShown()) postInvalidateDelayed(50);
        }
    }

    // ---- Étincelles d'une belle fin

    /** Des pixels d'or et de ciel qui tombent doucement, trois secondes. */
    static final class Etincelles extends View {
        private final Paint pt = new Paint();
        private final long debut = SystemClock.uptimeMillis();
        private final float[] x = new float[34], v = new float[34], y0 = new float[34];
        private final int[] c = new int[34];

        Etincelles(Context ctx, int[] couleurs) {
            super(ctx);
            java.util.Random r = new java.util.Random(7);
            for (int i = 0; i < x.length; i++) {
                x[i] = r.nextFloat();
                y0[i] = -r.nextFloat() * 0.6f;
                v[i] = 0.25f + r.nextFloat() * 0.45f;
                c[i] = couleurs[i % couleurs.length];
            }
            setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
            setClickable(false);
        }

        @Override
        protected void onDraw(Canvas cv) {
            float t = (SystemClock.uptimeMillis() - debut) / 1000f;
            if (t > 3.2f || !Vitrine.anime(getContext())) return;
            float b = Ui.dp(getContext(), 3);
            for (int i = 0; i < x.length; i++) {
                float yy = (y0[i] + v[i] * t) * getHeight();
                if (yy < 0 || yy > getHeight()) continue;
                pt.setColor(c[i]);
                pt.setAlpha((int) (255 * Math.max(0, Math.min(1, 3.2f - t))));
                float xx = x[i] * getWidth() + (float) Math.sin(t * 3 + i) * b * 2;
                float s = (i % 3 == 0) ? b * 2 : b;
                cv.drawRect(Math.round(xx), Math.round(yy), Math.round(xx + s), Math.round(yy + s), pt);
            }
            postInvalidateDelayed(40);
        }
    }

    /**
     * Feuille du bas (menu, confirmation) : un titre, un texte, puis des actions par trois (libellé, plein ?, action).
     * Toucher le voile la referme.
     */
    static View feuille(Context c, String titre, String texte, Runnable fermer, Object... actions) {
        Ui.Palette p = Ui.p(c);
        android.widget.FrameLayout voile = new android.widget.FrameLayout(c);
        voile.setBackgroundColor(0x990d1117);
        voile.setClickable(true);
        voile.setOnClickListener(v -> fermer.run());
        android.widget.LinearLayout f = Ui.pile(c);
        f.setBackground(Ui.coins(c, p.surface, 22, 22, 0, 0, 0));
        f.setPadding(Ui.dp(c, 20), Ui.dp(c, 18), Ui.dp(c, 20), Ui.dp(c, 20));
        f.setClickable(true);
        View poignee = new View(c);
        poignee.setBackground(Ui.arrondi(c, p.bord, 3, 0));
        android.widget.LinearLayout.LayoutParams lpg = new android.widget.LinearLayout.LayoutParams(Ui.dp(c, 36), Ui.dp(c, 4));
        lpg.gravity = android.view.Gravity.CENTER_HORIZONTAL;
        lpg.bottomMargin = Ui.dp(c, 14);
        f.addView(poignee, lpg);
        if (titre != null) f.addView(Ui.texte(c, titre, Ui.T_CARTE, p.texte, true), Ui.large());
        if (texte != null) {
            android.widget.TextView t = Ui.texte(c, texte, Ui.T_CORPS, p.doux, false);
            t.setPadding(0, Ui.dp(c, 6), 0, Ui.dp(c, 6));
            f.addView(t, Ui.large());
        }
        for (int i = 0; i + 2 < actions.length; i += 3) {
            View.OnClickListener a = (View.OnClickListener) actions[i + 2];
            android.widget.Button b = Ui.bouton(c, (String) actions[i], (Boolean) actions[i + 1], a);
            android.widget.LinearLayout.LayoutParams l = Ui.large();
            l.topMargin = Ui.dp(c, 8);
            f.addView(b, l);
        }
        voile.addView(f, new android.widget.FrameLayout.LayoutParams(android.view.ViewGroup.LayoutParams.MATCH_PARENT,
                android.view.ViewGroup.LayoutParams.WRAP_CONTENT, android.view.Gravity.BOTTOM));
        if (Vitrine.anime(c)) {
            f.setTranslationY(Ui.dp(c, 60));
            f.animate().translationY(0).setDuration(220).setInterpolator(new android.view.animation.DecelerateInterpolator(1.8f)).start();
        }
        return voile;
    }

    /** « 12:34 », « 1:05:20 » : un compte à rebours lisible en police pixel. */

    static String compte(long ms) {
        long s = Math.max(0, (ms + 999) / 1000);
        long h = s / 3600, m = s / 60 % 60, ss = s % 60;
        return h > 0 ? String.format(java.util.Locale.ROOT, "%d:%02d:%02d", h, m, ss) : String.format(java.util.Locale.ROOT, "%02d:%02d", m, ss);
    }
}
