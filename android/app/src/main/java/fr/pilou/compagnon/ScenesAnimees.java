package fr.pilou.compagnon;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Rect;
import android.graphics.RectF;
import android.os.SystemClock;
import android.text.Spannable;
import android.text.SpannableString;
import android.text.Spanned;
import android.text.style.ForegroundColorSpan;
import android.view.View;
import android.widget.TextView;

import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Les animations de l'onglet Aventure (docs/ANDROID.md, « Animations des campagnes ») : décors en boucle et volet
 * pixelisé entre deux décors, portraits des personnages qui respirent, clignent et parlent, écriture lettre à lettre,
 * fond qui respire selon le ton et l'heure. Les règles (quelle image, quand) sont communes avec le PC : Animations.java.
 * Ici : l'affichage seulement, sans allocation par image (images rendues une fois, cache borné ; rectangles réutilisés).
 * Rien ne bouge quand la vue n'est pas à l'écran ; un sprite manquant retombe sur l'image fixe.
 */
final class ScenesAnimees {
    private ScenesAnimees() {
    }

    // ---- Réglages (préférences de l'app ; l'échelle des animations du système passe avant)

    static String reglage(Context c) {
        return Prefs.de(c).getString("animationsCampagnes", "");          // vide : le système donne la valeur de départ
    }

    static void regler(Context c, String niveau) {
        Prefs.de(c).edit().putString("animationsCampagnes", niveau).apply();
    }

    static boolean texteInstantane(Context c) {
        return Prefs.de(c).getBoolean("texteInstantane", false) || Animations.AUCUNE.equals(niveau(c));
    }

    static void texteInstantane(Context c, boolean oui) {
        Prefs.de(c).edit().putBoolean("texteInstantane", oui).apply();
    }

    static String niveau(Context c) {
        return Animations.niveau(reglage(c), Vitrine.anime(c));
    }

    static String nomNiveau(String n) {
        return Animations.REDUITES.equals(n) ? "réduites" : Animations.AUCUNE.equals(n) ? "aucune" : "complètes";
    }

    // ---- Cache borné des images rendues, par sprite et par image

    private static final int CACHE_MAX = 24;
    private static final Map<Sprites.Sprite, Bitmap[]> CACHE = new IdentityHashMap<>();
    private static final LinkedHashMap<Sprites.Sprite, Boolean> ORDRE = new LinkedHashMap<>(32, 0.75f, true);

    static synchronized Bitmap image(Sprites.Sprite s, int k) {
        if (s == null || s.images.isEmpty()) return null;
        k = Math.max(0, Math.min(k, s.images.size() - 1));
        Bitmap[] b = CACHE.get(s);
        if (b == null) {
            b = new Bitmap[s.images.size()];
            CACHE.put(s, b);
            while (ORDRE.size() >= CACHE_MAX) {
                Sprites.Sprite vieux = ORDRE.keySet().iterator().next();
                ORDRE.remove(vieux);
                CACHE.remove(vieux);
            }
        }
        ORDRE.put(s, Boolean.TRUE);
        if (b[k] == null) b[k] = rendre(s, k);
        return b[k];
    }

    private static Bitmap rendre(Sprites.Sprite s, int k) {
        int w = s.w(), h = s.h();
        int[] g = new int[w * h];
        String[] im = s.images.get(k);
        int[] pal = s.compilee();
        for (int y = 0; y < im.length; y++)
            for (int x = 0; x < im[y].length() && x < w; x++) {
                char ch = im[y].charAt(x);
                int c = ch < 128 ? pal[ch] : 0;
                g[y * w + x] = (c >>> 24) == 0 ? 0 : c;
            }
        return Bitmap.createBitmap(g, w, h, Bitmap.Config.ARGB_8888);
    }

    // ---- Décor animé : boucle et volet (Aventure.Scene s'en sert)

    static final class Decor {
        private Sprites.Sprite sprite, avant;
        private int kAvant;
        private long debutVolet = -1;
        private final Rect src = new Rect(), dst = new Rect();
        /** Liste : quelques images seulement, trois fois plus lentes. */
        boolean ralenti;

        /** Le décor change : le précédent s'efface par un volet pixelisé (ou d'un coup, selon le niveau). */
        void regler(Sprites.Sprite s, long t, String niveau) {
            if (s == sprite) return;
            if (sprite != null && s != null && Animations.COMPLETES.equals(niveau) && !ralenti && sprite.w() == s.w() && sprite.h() == s.h()) {
                avant = sprite;
                kAvant = image(t, niveau);
                debutVolet = t;
            } else {
                avant = null;
                debutVolet = -1;
            }
            sprite = s;
        }

        Sprites.Sprite sprite() {
            return sprite;
        }

        int image(long t, String niveau) {
            if (sprite == null) return 0;
            int n = ralenti ? Math.min(4, sprite.images.size()) : sprite.images.size();
            int d = ralenti ? sprite.duree * 3 : sprite.duree;
            return (int) Animations.imageDecor(n, d, t, niveau);
        }

        /** Dessine le décor (k : agrandissement entier) au point (x, y) de la toile. */
        void dessiner(Canvas cv, Paint pt, long t, String niveau, int x, int y, int k) {
            if (sprite == null) return;
            Bitmap b = ScenesAnimees.image(sprite, image(t, niveau));
            if (b == null) return;
            dst.set(x, y, x + b.getWidth() * k, y + b.getHeight() * k);
            if (debutVolet >= 0 && avant != null) {
                float p = (t - debutVolet) / (float) Animations.TRANSITION;
                Bitmap a = ScenesAnimees.image(avant, kAvant);
                if (p >= 1 || a == null) {
                    debutVolet = -1;
                    avant = null;
                } else {
                    cv.drawBitmap(a, null, dst, pt);
                    int bloc = Animations.VOLET_BLOC * b.getWidth() / Sprites.DECOR_LARGEUR;
                    int nbx = (b.getWidth() + bloc - 1) / bloc, nby = (b.getHeight() + bloc - 1) / bloc, seuil = (int) (p * 10000);
                    for (int by = 0; by < nby; by++)
                        for (int bx = 0; bx < nbx; bx++) {
                            if (Animations.ordreVolet(bx, by, nbx) >= seuil) continue;
                            src.set(bx * bloc, by * bloc, Math.min(b.getWidth(), (bx + 1) * bloc), Math.min(b.getHeight(), (by + 1) * bloc));
                            dst.set(x + src.left * k, y + src.top * k, x + src.right * k, y + src.bottom * k);
                            cv.drawBitmap(b, src, dst, pt);
                        }
                    return;
                }
            }
            cv.drawBitmap(b, null, dst, pt);
        }

        /** Dans combien de ms l'image change (-1 : jamais, rien à redessiner). */
        long prochain(long t, String niveau) {
            if (debutVolet >= 0) return 33;
            if (sprite == null || !Animations.COMPLETES.equals(niveau) || sprite.images.size() <= 1 || sprite.duree <= 0) return -1;
            long d = ralenti ? sprite.duree * 3L : sprite.duree;
            return d - t % d;
        }
    }

    // ---- Portrait d'un personnage, au bord de la scène

    static final class Portrait extends View {
        private Sprites.Sprite sprite;
        private boolean parle;
        private long depuis;
        private final Paint pt = new Paint();
        private final Rect dst = new Rect();
        private String niveau = Animations.COMPLETES;

        Portrait(Context c) {
            super(c);
            pt.setFilterBitmap(false);
            pt.setAntiAlias(false);
            setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_YES);
        }

        /** Le personnage du message (null : personne) ; il entre en glissant si tout est animé. */
        void montrer(Sprites.Sprite s, String nom) {
            niveau = niveau(getContext());
            if (s == sprite) return;
            sprite = s;
            depuis = SystemClock.uptimeMillis();
            setContentDescription(nom == null || nom.isEmpty() ? null : nom);
            setVisibility(s == null ? GONE : VISIBLE);
            if (s != null && !Animations.AUCUNE.equals(niveau)) {
                setAlpha(0);
                setTranslationX(Animations.COMPLETES.equals(niveau) ? Ui.dp(getContext(), 14) : 0);
                animate().alpha(1).translationX(0).setDuration(340).start();
            }
            invalidate();
        }

        /** Pour les tests : pixels d'écran par pixel fin du portrait (0 : personne). */
        int echelle() {
            if (sprite == null || sprite.images.isEmpty()) return 0;
            return Math.max(1, Math.min(getWidth() / sprite.w(), getHeight() / sprite.h()));
        }

        void parle(boolean p) {
            if (p == parle) return;
            parle = p;
            invalidate();
        }

        @Override
        protected void onDraw(Canvas cv) {
            if (sprite == null) return;
            long t = SystemClock.uptimeMillis() - depuis;
            int k = Animations.imagePortrait(sprite.images.size(), t, parle, niveau);
            Bitmap b = image(sprite, k);
            if (b == null) return;
            int z = Math.max(1, Math.min(getWidth() / b.getWidth(), getHeight() / b.getHeight()));
            int w = b.getWidth() * z, h = b.getHeight() * z;
            int x = (getWidth() - w) / 2, y = getHeight() - h;
            dst.set(x, y, x + w, y + h);
            cv.drawBitmap(b, null, dst, pt);
            if (!Animations.AUCUNE.equals(niveau) && isShown()) {
                // Prochain changement possible : parole, respiration ou clignement.
                long pas = parle ? Animations.PAS_PAROLE - t % Animations.PAS_PAROLE
                        : Math.min(Animations.RESPIRATION - t % Animations.RESPIRATION, Animations.CLIGNE_PERIODE - Animations.CLIGNE_DUREE - t % Animations.CLIGNE_PERIODE > 0
                        ? Animations.CLIGNE_PERIODE - Animations.CLIGNE_DUREE - t % Animations.CLIGNE_PERIODE : Animations.CLIGNE_PERIODE - t % Animations.CLIGNE_PERIODE);
                postInvalidateDelayed(Math.max(30, pas));
            }
        }
    }

    // ---- Écriture lettre à lettre (le texte est posé en entier, la fin reste invisible : la bulle ne bouge pas)

    static final class Ecriture implements Runnable {
        private final TextView vue;
        private final String texte;
        private final ForegroundColorSpan cache = new ForegroundColorSpan(Color.TRANSPARENT);
        private final Spannable s;
        private final long debut = SystemClock.uptimeMillis();
        private final Runnable fini;
        private boolean termine;

        Ecriture(TextView vue, String texte, Runnable fini) {
            this.vue = vue;
            this.texte = texte;
            this.fini = fini;
            s = new SpannableString(texte);
            s.setSpan(cache, 0, texte.length(), Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
            vue.setText(s, TextView.BufferType.SPANNABLE);
            vue.post(this);
        }

        @Override
        public void run() {
            if (termine) return;
            int n = Animations.lettres(texte, SystemClock.uptimeMillis() - debut);
            if (n >= texte.length()) {
                terminer();
                return;
            }
            Spannable sp = (Spannable) vue.getText();
            sp.setSpan(cache, n, texte.length(), Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
            vue.postDelayed(this, 33);
        }

        /** Tout d'un coup (un toucher, ou la fin). */
        void terminer() {
            if (termine) return;
            termine = true;
            vue.removeCallbacks(this);
            if (vue.getText() instanceof Spannable) ((Spannable) vue.getText()).removeSpan(cache);
            if (fini != null) fini.run();
        }

        boolean termine() {
            return termine;
        }
    }

    // ---- Petits effets d'interface, selon le niveau

    /** Une récompense tombe en place après delai ms. */
    static void tomber(View v, int delai) {
        String n = niveau(v.getContext());
        if (Animations.AUCUNE.equals(n)) return;
        v.setAlpha(0);
        if (Animations.COMPLETES.equals(n)) v.setTranslationY(-Ui.dp(v.getContext(), 22));
        v.animate().alpha(1).translationY(0).setStartDelay(delai).setDuration(Animations.COMPLETES.equals(n) ? 520 : 240)
                .setInterpolator(new android.view.animation.OvershootInterpolator(1.4f)).start();
    }

    /** Une image nette d'un sprite (première image) de la largeur donnée (dp) ; null s'il manque. */
    static View vignette(Context c, Sprites.Sprite s, int largeurDp) {
        Bitmap b = s == null ? null : image(s, 0);
        if (b == null) return null;
        android.widget.ImageView im = new android.widget.ImageView(c);
        android.graphics.drawable.BitmapDrawable d = new android.graphics.drawable.BitmapDrawable(c.getResources(), b);
        d.setFilterBitmap(false);
        d.setAntiAlias(false);
        im.setImageDrawable(d);
        im.setScaleType(android.widget.ImageView.ScaleType.FIT_CENTER);
        int w = Ui.dp(c, largeurDp);
        im.setLayoutParams(new android.widget.FrameLayout.LayoutParams(w, w * b.getHeight() / Math.max(1, b.getWidth()), android.view.Gravity.CENTER));
        im.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        return im;
    }

    /** Le contenu se pose (il grandit d'un coup doux) et quatre petits traits s'écartent : un éclat. */
    static View eclat(Context c, View contenu, int couleur, int delai) {
        android.widget.FrameLayout f = new android.widget.FrameLayout(c);
        int pad = Ui.dp(c, 12);
        f.setPadding(pad, pad, pad, pad);
        f.setClipChildren(false);
        f.addView(contenu);
        String n = niveau(c);
        if (Animations.AUCUNE.equals(n)) return f;
        contenu.setAlpha(0);
        contenu.setScaleX(0.3f);
        contenu.setScaleY(0.3f);
        contenu.animate().alpha(1).scaleX(1).scaleY(1).setStartDelay(delai).setDuration(Animations.COMPLETES.equals(n) ? 520 : 220)
                .setInterpolator(new android.view.animation.OvershootInterpolator(1.6f)).start();
        if (!Animations.COMPLETES.equals(n)) return f;
        for (int i = 0; i < 4; i++) {
            View r = new View(c);
            r.setBackgroundColor(couleur);
            r.setAlpha(0);
            f.addView(r, new android.widget.FrameLayout.LayoutParams(Ui.dp(c, 3), Ui.dp(c, 9), android.view.Gravity.CENTER));
            double a = Math.toRadians(45 + i * 90);
            float d = Ui.dp(c, 30);
            r.setRotation(45 + i * 90);
            r.animate().alpha(0.9f).translationX((float) Math.sin(a) * d).translationY(-(float) Math.cos(a) * d)
                    .setStartDelay(delai + 260).setDuration(300).withEndAction(() -> r.animate().alpha(0).setDuration(240).start()).start();
        }
        return f;
    }

    /** Le nom d'un personnage, pour l'accessibilité. */
    static String nomPersonnage(String id) {
        switch (id == null ? "" : id) {
            case "grumeau": return "Grumeau";
            case "le-rond": return "le Rond";
            case "mlle-renvoi": return "Mlle Renvoi";
            case "golem": return "le golem de tickets";
            case "spectre-404": return "Quatre-Cent-Quatre";
            case "dateur": return "le Dateur";
            case "mme-echeance": return "Mme Échéance";
            case "raccourcis": return "Ctrl, Alt et Suppr";
            case "touche-s": return "S";
            case "imprimante": return "l'Imprimante";
            case "brouillon": return "Brouillon";
            case "tic-tac": return "le Tic-Tac";
            case "balayeur": return "le Balayeur";
            case "anselme": return "Anselme";
            case "lison": return "Lison";
            case "tudal": return "Tudal";
            case "perrine": return "Perrine";
            case "odile": return "Odile";
            case "basile": return "Basile";
            case "vernier": return "M. Vernier";
            case "tournebise": return "Tournebise";
            case "ondee": return "Ondée";
            case "mi-bemol": return "Mi-Bémol";
            case "dentelle": return "Dentelle";
            case "madame-bocal": return "Madame Bocal";
            case "froisseuses": return "les Froisseuses";
            case "enclumes": return "les Enclumes";
            case "bergeronnette": return "la bergeronnette";
            default: return "";
        }
    }


    // ---- Fond qui respire : dégradé du ton et de l'heure, quelques particules lentes

    static final class Fond extends View {
        private String ton = "";
        private int heure = -1;
        private int haut, bas, part;
        private final Paint pt = new Paint();
        private final RectF r = new RectF();
        private Bitmap degrade;
        private int base = 0;
        private final int[] particule = new int[3];

        Fond(Context c) {
            super(c);
            setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
        }

        /** La couleur de fond du thème : le dégradé ne fait que la teinter (lisible en clair comme en sombre). */
        void base(int c) {
            base = c;
            degrade = null;
        }

        void ton(String t) {
            t = t == null ? "" : t;
            int h = java.util.Calendar.getInstance().get(java.util.Calendar.HOUR_OF_DAY);
            if (t.equals(ton) && h == heure) return;
            ton = t;
            heure = h;
            String[] c = Animations.teintesFond(t, h);
            haut = Color.parseColor(c[0]);
            bas = Color.parseColor(c[1]);
            part = Color.parseColor(c[2]);
            if (base != 0) {
                haut = Aventure.Scene.melanger(base, haut, 0.22f);
                bas = Aventure.Scene.melanger(base, bas, 0.32f);
            }
            degrade = null;
            invalidate();
        }

        @Override
        protected void onDraw(Canvas cv) {
            int w = getWidth(), h = getHeight();
            if (w <= 0 || h <= 0 || ton.isEmpty()) return;
            if (degrade == null) {
                // Seize bandes, en dur (pixel) : le dégradé est calculé une fois.
                int[] px = new int[16];
                for (int i = 0; i < 16; i++) px[i] = Aventure.Scene.melanger(haut, bas, i / 15f);
                degrade = Bitmap.createBitmap(px, 1, 16, Bitmap.Config.ARGB_8888);
            }
            r.set(0, 0, w, h);
            pt.setFilterBitmap(false);
            cv.drawBitmap(degrade, null, r, pt);
            String niveau = niveau(getContext());
            if (!Animations.COMPLETES.equals(niveau)) return;
            long t = SystemClock.uptimeMillis() / 250 * 250;
            float b = Ui.dp(getContext(), 3);
            pt.setColor(part);
            for (int i = 0; i < Animations.NB_PARTICULES; i++) {
                int[] p = Animations.particuleFond(ton, i, t, particule);
                pt.setAlpha(p[2] * 6 / 10);
                float x = Math.round(p[0] / 10000f * w), y = Math.round(p[1] / 10000f * h);
                cv.drawRect(x, y, x + b, y + b, pt);
            }
            pt.setAlpha(255);
            if (isShown()) postInvalidateDelayed(250 - SystemClock.uptimeMillis() % 250);
        }
    }
}
