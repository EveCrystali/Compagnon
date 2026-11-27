package fr.pilou.compagnon;

import android.content.Context;
import android.content.res.ColorStateList;
import android.content.res.Configuration;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Typeface;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.RippleDrawable;
import android.text.TextUtils;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.Switch;
import android.widget.TextView;

import java.util.function.Consumer;

/**
 * Identité visuelle de l'app : palette (clair / sombre selon le système), cartes arrondies, boutons,
 * lignes de réglage, icônes pixel. Bleu / orange / argent / neutres : jamais de rouge ni de vert,
 * et chaque état garde un signe de forme en plus de sa couleur.
 */
final class Ui {
    static final class Palette {
        final int fond, surface, surface2, bord, texte, doux, bleu, orange, argent, surAccent, voile;

        Palette(int fond, int surface, int surface2, int bord, int texte, int doux, int bleu, int orange, int argent, int surAccent, int voile) {
            this.fond = fond;
            this.surface = surface;
            this.surface2 = surface2;
            this.bord = bord;
            this.texte = texte;
            this.doux = doux;
            this.bleu = bleu;
            this.orange = orange;
            this.argent = argent;
            this.surAccent = surAccent;
            this.voile = voile;
        }
    }

    // Thème clair : bleu, orange et argent assombris pour tenir le contraste WCAG AA (≥ 4,5:1) sur le fond
    // et sur les cartes (texte bleu ou orange, texte blanc sur bouton bleu).
    static final Palette CLAIRE = new Palette(0xfff6f8fa, 0xffffffff, 0xffeef2f6, 0xffd8dee4, 0xff1c2128, 0xff57606a,
            0xff1f6fc5, 0xffa8530f, 0xff6a7889, 0xffffffff, 0x141f6fc5);
    static final Palette SOMBRE = new Palette(0xff161b22, 0xff22272e, 0xff2d333b, 0xff373e47, 0xffcdd9e5, 0xff909dab,
            0xff6cb6ff, 0xfff69d50, 0xffadbac7, 0xff1c2128, 0x226cb6ff);

    /**
     * Échelle typographique (sp) : titre de page, titre de carte, corps, détail ; plus l'étiquette de section (capitales
     * espacées). Rien d'autre dans les pages : la hiérarchie se lit d'un coup d'œil.
     */
    static final float T_PAGE = 28, T_CARTE = 19, T_CORPS = 15, T_DETAIL = 13, T_ETIQUETTE = 12;

    private Ui() {
    }

    /** Fond arrondi aux quatre coins choisis (dp) : bulles de conversation (la pointe a un petit rayon). */
    static GradientDrawable coins(Context c, int fond, float hg, float hd, float bd, float bg, int bord) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(fond);
        float a = dp(c, hg), b = dp(c, hd), d = dp(c, bd), e = dp(c, bg);
        g.setCornerRadii(new float[]{a, a, b, b, d, d, e, e});
        if (bord != 0) g.setStroke(Math.max(1, dp(c, 1)), bord);
        return g;
    }

    /** Petit enfoncement au toucher (bouton, carte, option) : la vue répond sous le doigt. */
    static void enfoncer(View v) {
        v.setOnTouchListener((x, e) -> {
            switch (e.getActionMasked()) {
                case android.view.MotionEvent.ACTION_DOWN:
                    x.animate().scaleX(0.97f).scaleY(0.97f).setDuration(70).start();
                    break;
                case android.view.MotionEvent.ACTION_UP:
                case android.view.MotionEvent.ACTION_CANCEL:
                    x.animate().scaleX(1).scaleY(1).setDuration(120).start();
                    break;
                default:
                    break;
            }
            return false;
        });
    }

    /** Vibration très légère (réglage « Vibrations » des jeux). */
    @SuppressWarnings("deprecation")
    static void vibrer(Context c, int ms) {
        if (!Prefs.vibrations(c)) return;
        try {
            android.os.Vibrator v = c.getSystemService(android.os.Vibrator.class);
            if (v != null && v.hasVibrator()) v.vibrate(android.os.VibrationEffect.createOneShot(ms, Math.min(255, 40 + ms * 3)));
        } catch (RuntimeException e) {
            // pas de vibreur : tant pis
        }
    }

    /** Puce d'information sur fond sombre (scènes d'aventure) : texte clair sur voile. */
    static TextView puceScene(Context c, CharSequence s) {
        TextView t = texte(c, s, T_ETIQUETTE, Vitrine.ARGENT_CLAIR, true);
        t.setBackground(arrondi(c, 0x8c0d1117, 10, 0));
        t.setPadding(dp(c, 9), dp(c, 4), dp(c, 9), dp(c, 4));
        t.setSingleLine(true);
        t.setEllipsize(TextUtils.TruncateAt.END);
        return t;
    }

    static boolean sombre(Context c) {
        return (c.getResources().getConfiguration().uiMode & Configuration.UI_MODE_NIGHT_MASK) == Configuration.UI_MODE_NIGHT_YES;
    }

    static Palette p(Context c) {
        return sombre(c) ? SOMBRE : CLAIRE;
    }

    static int dp(Context c, float v) {
        return Math.round(TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, v, c.getResources().getDisplayMetrics()));
    }

    static GradientDrawable arrondi(Context c, int fond, float rayon, int bord) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(fond);
        g.setCornerRadius(dp(c, rayon));
        if (bord != 0) g.setStroke(dp(c, 1), bord);
        return g;
    }

    static Drawable touchable(Context c, Drawable fond, float rayon) {
        return new RippleDrawable(ColorStateList.valueOf(p(c).voile | 0x22000000), fond, arrondi(c, 0xff000000, rayon, 0));
    }

    static LinearLayout.LayoutParams large() {
        return new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
    }

    static LinearLayout.LayoutParams large(Context c, float basDp) {
        LinearLayout.LayoutParams l = large();
        l.bottomMargin = dp(c, basDp);
        return l;
    }

    static LinearLayout pile(Context c) {
        LinearLayout l = new LinearLayout(c);
        l.setOrientation(LinearLayout.VERTICAL);
        return l;
    }

    static LinearLayout rangee(Context c) {
        LinearLayout l = new LinearLayout(c);
        l.setOrientation(LinearLayout.HORIZONTAL);
        l.setGravity(Gravity.CENTER_VERTICAL);
        return l;
    }

    /** Carte arrondie (surface), contenu vertical. */
    static LinearLayout carte(Context c) {
        LinearLayout l = pile(c);
        l.setBackground(arrondi(c, p(c).surface, 18, p(c).bord));
        int m = dp(c, 16);
        l.setPadding(m, m, m, m);
        l.setElevation(dp(c, 1));
        return l;
    }

    static TextView texte(Context c, CharSequence s, float sp, int couleur, boolean gras) {
        TextView t = new TextView(c);
        t.setText(s);
        t.setTextSize(TypedValue.COMPLEX_UNIT_SP, sp);
        t.setTextColor(couleur);
        if (gras) t.setTypeface(Typeface.create("sans-serif-medium", Typeface.BOLD));
        t.setLineSpacing(0, 1.15f);
        return t;
    }

    static TextView titrePage(Context c, String s) {
        TextView t = texte(c, s, 28, p(c).texte, true);
        t.setPadding(0, dp(c, 12), 0, dp(c, 2));
        return t;
    }

    static TextView sousTitre(Context c, String s) {
        TextView t = texte(c, s, 14, p(c).doux, false);
        t.setPadding(0, 0, 0, dp(c, 16));
        return t;
    }

    static TextView titreSection(Context c, String s) {
        TextView t = texte(c, s.toUpperCase(java.util.Locale.FRENCH), 12, p(c).doux, true);
        t.setLetterSpacing(0.08f);
        t.setPadding(dp(c, 4), dp(c, 14), 0, dp(c, 8));
        return t;
    }

    /** Bouton plein (accent bleu) ou discret (surface). */
    static Button bouton(Context c, String s, boolean plein, View.OnClickListener action) {
        Palette p = p(c);
        Button b = new Button(c);
        b.setText(s);
        b.setAllCaps(false);
        b.setTextSize(TypedValue.COMPLEX_UNIT_SP, 15);
        b.setTypeface(Typeface.create("sans-serif-medium", Typeface.BOLD));
        b.setTextColor(plein ? p.surAccent : p.bleu);
        b.setBackground(touchable(c, arrondi(c, plein ? p.bleu : p.surface2, 14, 0), 14));
        b.setStateListAnimator(null);
        b.setPadding(dp(c, 18), dp(c, 12), dp(c, 18), dp(c, 12));
        b.setMinHeight(dp(c, 48));
        b.setOnClickListener(action);
        return b;
    }

    /** Ligne cliquable : titre, sous-titre, chevron. */
    static View ligne(Context c, String titre, String sous, int couleurTitre, View.OnClickListener action) {
        Palette p = p(c);
        LinearLayout r = rangee(c);
        r.setPadding(dp(c, 4), dp(c, 10), dp(c, 4), dp(c, 10));
        r.setMinimumHeight(dp(c, 48)); // zone tactile minimale
        LinearLayout t = pile(c);
        t.addView(texte(c, titre, 16, couleurTitre == 0 ? p.texte : couleurTitre, false));
        if (sous != null && !sous.isEmpty()) t.addView(texte(c, sous, 13, p.doux, false));
        r.addView(t, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        if (action != null) {
            r.addView(texte(c, "›", 22, p.doux, false));
            r.setBackground(touchable(c, arrondi(c, 0x00000000, 10, 0), 10));
            r.setOnClickListener(action);
        }
        return r;
    }

    /** Interrupteur avec titre et explication. */
    static Switch interrupteur(Context c, LinearLayout dans, String titre, String sous, boolean actif, Consumer<Boolean> choix) {
        Palette p = p(c);
        LinearLayout r = rangee(c);
        r.setPadding(dp(c, 4), dp(c, 8), 0, dp(c, 8));
        r.setMinimumHeight(dp(c, 48));
        LinearLayout t = pile(c);
        t.addView(texte(c, titre, 16, p.texte, false));
        if (sous != null && !sous.isEmpty()) t.addView(texte(c, sous, 13, p.doux, false));
        r.addView(t, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        Switch s = new Switch(c);
        s.setChecked(actif);
        int[][] etats = {{android.R.attr.state_checked}, {}};
        s.setThumbTintList(new ColorStateList(etats, new int[]{p.bleu, p.argent}));
        s.setTrackTintList(new ColorStateList(etats, new int[]{p.bleu & 0x66ffffff, p.bord}));
        s.setOnCheckedChangeListener((v, oui) -> choix.accept(oui));
        r.addView(s);
        r.setOnClickListener(v -> s.toggle());
        dans.addView(r, large());
        return s;
    }

    static View separateur(Context c) {
        View v = new View(c);
        v.setBackgroundColor(p(c).bord);
        LinearLayout.LayoutParams l = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, Math.max(1, dp(c, 0.6f)));
        l.topMargin = l.bottomMargin = dp(c, 4);
        v.setLayoutParams(l);
        return v;
    }

    /** Pastille ronde avec un signe (❗ ◐ ✓ ■ ✕ ?) : la forme dit l'état, la couleur le confirme. */
    static TextView pastille(Context c, String signe, int couleur) {
        TextView t = texte(c, signe, 16, couleur, true);
        t.setGravity(Gravity.CENTER);
        t.setBackground(arrondi(c, (couleur & 0x00ffffff) | 0x22000000, 20, 0));
        int d = dp(c, 38);
        t.setLayoutParams(new LinearLayout.LayoutParams(d, d));
        return t;
    }

    static TextView puceTexte(Context c, String s, int couleur) {
        TextView t = texte(c, s, 12, couleur, true);
        t.setBackground(arrondi(c, (couleur & 0x00ffffff) | 0x22000000, 12, 0));
        t.setPadding(dp(c, 10), dp(c, 4), dp(c, 10), dp(c, 4));
        t.setSingleLine(true);
        t.setEllipsize(TextUtils.TruncateAt.END);
        return t;
    }

    /** Icône pixel : un motif de caractères ('0' vide, '1'… indice de palette). */
    static final class Icone extends View {
        private String[] motif;
        private int[] pal;
        private final float px;
        private final Paint pt = new Paint();

        Icone(Context c, String[] motif, int[] pal, float pxDp) {
            super(c);
            this.motif = motif;
            this.pal = pal;
            px = dp(c, pxDp);
            pt.setAntiAlias(false);
            // Icône décorative : le libellé voisin dit déjà ce qu'elle représente (TalkBack la saute).
            setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
        }

        void couleurs(int[] p) {
            pal = p;
            invalidate();
        }

        @Override
        protected void onMeasure(int l, int h) {
            setMeasuredDimension(Math.round(motif[0].length() * px), Math.round(motif.length * px));
        }

        @Override
        protected void onDraw(Canvas cv) {
            Police.motif((g, hh, d, b, col) -> {
                pt.setColor(col);
                cv.drawRect(g, hh, d, b, pt);
            }, motif, 0, 0, px, pal);
        }
    }

    /** Barre d'XP en pixels : segments pleins (bleu) avec une pointe orange. */
    static final class Barre extends View {
        private float part;
        private final Paint pt = new Paint();

        Barre(Context c) {
            super(c);
        }

        void part(float v) {
            part = Math.max(0, Math.min(1, v));
            invalidate();
        }

        @Override
        protected void onMeasure(int l, int h) {
            setMeasuredDimension(MeasureSpec.getSize(l), dp(getContext(), 14));
        }

        @Override
        protected void onDraw(Canvas cv) {
            Palette p = p(getContext());
            int n = 24;
            float w = getWidth(), h = getHeight(), pas = w / n, ecart = Math.max(1, pas * 0.18f);
            int pleins = Math.round(part * n);
            for (int i = 0; i < n; i++) {
                pt.setColor(i < pleins ? (i == pleins - 1 ? p.orange : p.bleu) : p.surface2);
                cv.drawRect(i * pas, 0, (i + 1) * pas - ecart, h, pt);
            }
        }
    }

    // ---- Motifs d'icônes (12 × 12)

    static final String[] ACCUEIL = {"000001100000", "000011110000", "000111111000", "001111111100", "011111111110", "111111111111",
            "001111111100", "001100011100", "001100011100", "001100011100", "001111111100", "000000000000"};
    // Un fanion planté sur une colline : l'aventure.
    static final String[] AVENTURE = {"000110000000", "000111100000", "000111111000", "000111100000", "000110000000", "000100000000",
            "000100000000", "000100000000", "001110001100", "011111011110", "111111111111", "000000000000"};
    static final String[] JOUER = {
"000000000000", "000000000000", "011111111110", "111111111111", "110111111011", "100011110101",
            "110111111011", "111111111111", "111100001111", "011000000110", "000000000000", "000000000000"};
    // Sac de boutique (anse, sac, étoile découpée).
    static final String[] BOUTIQUE = {"000011110000", "000100001000", "000100001000", "011111111110", "011111111110", "011111011110",
            "011110001110", "011000000010", "011110001110", "011101110110", "011111111110", "001111111100"};
    static final String[] COLLECTION = {"000001100000", "000001100000", "000011110000", "111111111111", "011111111110", "001111111100",
            "000111111000", "001111111100", "001110011100", "011100001110", "011000000110", "000000000000"};
    static final String[] REGLAGES = {"000011110000", "011011110110", "011111111110", "001110011100", "111100001111", "111000000111",
            "111000000111", "111100001111", "001110011100", "011111111110", "011011110110", "000011110000"};
    // Cartes de jeux (plusieurs couleurs).
    static final String[] PECHE = {"000000000300", "000000003030", "000000030003", "000000300003", "000003000003", "000030000003",
            "000300000004", "003000000044", "030000000000", "011110002220", "122221022222", "011110002220"};
    static final String[] CUISINE = {"000300300300", "003003003000", "000300300300", "000000000000", "111111111111", "122222222221",
            "012222222210", "012222222210", "012222222210", "001111111100", "000300003000", "003330033300"};
    static final String[] ETOILE = {"300000000000", "030000000000", "003300000000", "000330001000", "000003011100", "000000111110",
            "000001111111", "000000111110", "000000110110", "000001100011", "000000000000", "000000000000"};
    static final String[] BULLES = {"000000011100", "000000100010", "011100100210", "100010100010", "102010011100", "100010000000",
            "011100000111", "000000001000", "000111001020", "001000101000", "001020100111", "000111000000"};
    static final String[] TAPE = {"000101010000", "000101010100", "000101010100", "010111111100", "011111111100", "001111111100",
            "001111111100", "000111111000", "000111111000", "000011110000", "000000000000", "000000000000"};
    static final String[] BUG = {"010000000010", "001000000100", "000111111000", "001111111100", "011211112110", "011111111110",
            "111111111111", "001111111100", "011011110110", "100011110001", "000100001000", "001000000100"};
    static final String[] COEUR = {"0110110", "1111111", "1111111", "0111110", "0011100", "0001000"};
}
