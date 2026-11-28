package fr.pilou.compagnon;

import android.content.Context;
import android.content.res.ColorStateList;
import android.graphics.Canvas;
import android.graphics.ColorFilter;
import android.graphics.Paint;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.graphics.Typeface;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.StateListDrawable;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * La main de Pilou dans les interfaces (docs/STYLE.md) : palette du menu « Sept portes » (crème le jour, bleu nuit
 * la nuit), cadre en pixels (ombre, couleur, biseau ; coins en escalier, jamais d'arrondi lissé), texte en police
 * pixel (docs/POLICE.md), icônes pixel (outils/sprites/icones.py), pointillés, boutons et leurs états.
 * Tout se mesure en « modules » : le pixel de la scène de l'Aventure, un nombre entier de pixels de l'écran.
 * Jamais d'opposition rouge / vert ; chaque état porte un signe de forme en plus de sa couleur.
 */
final class Style {
    static final class Palette {
        final int page, carte, creux, texte, pale, eteint, accent, surAccent, bordExt, bord, biseauClair, biseauSombre,
                pointilles, coche, titre, orange, bleu;

        Palette(int page, int carte, int creux, int texte, int pale, int eteint, int accent, int surAccent, int bordExt, int bord,
                int biseauClair, int biseauSombre, int pointilles, int coche, int titre, int orange, int bleu) {
            this.page = page;
            this.carte = carte;
            this.creux = creux;
            this.texte = texte;
            this.pale = pale;
            this.eteint = eteint;
            this.accent = accent;
            this.surAccent = surAccent;
            this.bordExt = bordExt;
            this.bord = bord;
            this.biseauClair = biseauClair;
            this.biseauSombre = biseauSombre;
            this.pointilles = pointilles;
            this.coche = coche;
            this.titre = titre;
            this.orange = orange;
            this.bleu = bleu;
        }
    }

    // Les couleurs du menu « Sept portes » (MenuRetro.cs), plus le fond de page et le creux (docs/STYLE.md).
    static final Palette CLAIRE = new Palette(0xffefe3cb, 0xfffbf3e4, 0xffe6d7b8, 0xff1c2128, 0xff57606a, 0xff767c84,
            0xff1f5fae, 0xffffffff, 0xff1c2128, 0xff2f7ed8, 0xffffffff, 0xffd9c7a3, 0xffc86a1c, 0xff1f5fae, 0xff6a4fc8,
            0xff9c4a0a, 0xff1f5fae);
    static final Palette SOMBRE = new Palette(0xff0b0e1a, 0xff151a2e, 0xff2a3156, 0xffe6ecf2, 0xffadbac7, 0xff7d8796,
            0xfff69d50, 0xff151a2e, 0xff0b0e1a, 0xff6a5acd, 0xff3a4270, 0xff0b0e1a, 0xff6a5acd, 0xff6cb6ff, 0xff9b8cff,
            0xfff69d50, 0xff6cb6ff);
    /** Le bandeau et la boutique sont de nuit dans les deux thèmes (comme l'en-tête du menu du PC). */
    static final Palette NUIT = SOMBRE;

    /**
     * Tailles d'un pixel de police, en dp (× la taille de police du système) : petit, corps, titre de page. Le corps
     * est celui du récit de l'Aventure : 4 pixels de l'écran sur un téléphone de 1078 px à densité 2,75.
     */
    static final float PETIT = 1.25f, CORPS = 4f / 2.75f, PAGE = 2.4f;

    private Style() {
    }

    static Palette p(Context c) {
        return Ui.sombre(c) ? SOMBRE : CLAIRE;
    }

    /**
     * Le module : le pixel de la scène de l'Aventure (Aventure.unite : la largeur de l'écran divisée par 192, en
     * pixels entiers ; 5 sur un téléphone de 1078 px). Cadres, pointillés et marges se comptent en modules, comme
     * sous la scène (CadrePixel de l'Aventure, docs/SCENES.md) : une seule taille de pixel dans toute l'app.
     */
    static int u(Context c) {
        android.util.DisplayMetrics m = c.getResources().getDisplayMetrics();
        return Math.max(2, Aventure.unite(Math.min(m.widthPixels, m.heightPixels)));
    }

    /** Pixels de l'écran par pixel de police pour une taille en dp ; suit la taille de police du système. */
    static int pixel(Context c, float dp) {
        float k = c.getResources().getDisplayMetrics().density * Math.max(0.85f, c.getResources().getConfiguration().fontScale);
        return Math.max(1, Math.round(dp * k));
    }

    /** La taille (dp par pixel de police) qui rend une taille de texte du système (sp). */
    static float taille(float sp) {
        // Plancher de lisibilité (docs/STYLE.md) : un texte en minuscules ne descend jamais sous le corps. « Petit » est
        // réservé aux étiquettes en capitales (titres de section, « NIV ») : il se demande explicitement.
        return sp >= 24 ? PAGE : CORPS;
    }

    // ---------------------------------------------------------------------------------------------------- Texte

    private static Map<Integer, String> signes;

    /** Code d'un caractère → sprite du signe 7 × 7 (assets/signes.txt, écrit par outils/sprites/icones.py). */
    static synchronized Map<Integer, String> signes() {
        if (signes != null) return signes;
        Map<Integer, String> m = new HashMap<>();
        for (String l : Sprites.ressource("/signes.txt").split("\n")) {
            String t = l.trim();
            int i = t.indexOf(' ');
            if (t.isEmpty() || t.startsWith("#") || i < 0) continue;
            try {
                m.put(Integer.parseInt(t.substring(0, i), 16), t.substring(i + 1).trim());
            } catch (NumberFormatException e) {
                // ligne abîmée : on la saute
            }
        }
        signes = m;
        return m;
    }

    /** Signes de clavier que la police dessine déjà sous un autre code : le même dessin partout. */
    static String preparer(CharSequence s) {
        if (s == null) return "";
        StringBuilder b = new StringBuilder(s.length());
        s.codePoints().forEach(c -> {
            switch (c) {
                case 0x21E2: case 0x279C: case 0x2794: b.append('→'); break; // ⇢ ➜ ➔
                case 0x25B4: b.append('▲'); break;                           // ▴
                case 0x25BE: b.append('▼'); break;                           // ▾
                case 0x2757: b.append('!'); break;                           // ❗
                case 0x2715: case 0x2716: b.append('✗'); break;              // ✕ ✖
                case 0x25BA: b.append('▶'); break;                           // ►
                case 0x203A: b.append('›'); break;
                default: b.appendCodePoint(c);
            }
        });
        return b.toString();
    }

    static PolicePixel police(boolean gras) {
        PolicePixel p = gras ? PolicePixel.ressource("titre") : null;
        return p != null ? p : PolicePixel.texte();
    }

    /** Largeur d'un texte sur une ligne, en pixels de l'écran. */
    static int largeur(String s, int pixel, boolean gras) {
        PolicePixel p = police(gras);
        return p == null ? 0 : p.largeur(PolicePixel.preparer(preparer(s))) * pixel;
    }

    /** Le texte s'il tient sur une ligne de cette largeur (pixels de l'écran), sinon coupé et fini par « … ». */
    static String tronquer(String s, int pixel, boolean gras, float largeurMax) {
        PolicePixel p = police(gras);
        if (p == null) return s;
        List<String> l = p.couper(preparer(s), Math.max(1, (int) (largeurMax / pixel)), 1);
        return l.isEmpty() ? "" : l.get(0);
    }

    /**
     * La plus grande taille de police (pixels de l'écran par pixel de police, au plus celle de tailleDp) qui laisse
     * chaque nom dans sa case : des libellés voisins ne se touchent jamais, même en grande police.
     */
    static int pixelQuiTient(Context c, String[] noms, float tailleDp, boolean gras, int largeurCase) {
        // Jamais sous la taille « petit » : en dessous, on ne lit plus.
        int px = pixel(c, tailleDp), plancher = Math.min(px, pixel(c, PETIT));
        for (; px > plancher; px--) {
            boolean tient = true;
            for (String n : noms) tient &= largeur(n, px, gras) <= largeurCase;
            if (tient) break;
        }
        return px;
    }

    /**
     * Taille de police d'un groupe d'options posé dans une carte (« ● Normalement | Peu | Jamais ») : la plus grande
     * qui laisse chaque nom, précédé de son rond « ● », sur une seule ligne dans sa case.
     */
    static int pixelOptions(Context c, String[] noms) {
        String[] avec = new String[noms.length];
        for (int i = 0; i < noms.length; i++) avec[i] = "● " + noms[i];
        int dedans = c.getResources().getDisplayMetrics().widthPixels - Ui.dp(c, 36 + 24 + 16) - 5 * u(c);
        return pixelQuiTient(c, avec, CORPS, false, dedans / noms.length - 4 * u(c));
    }

    /** Le premier texte de la liste qui tient dans la largeur (le dernier sinon) : du plus long au plus court. */
    static String choisir(String[] formes, int pixel, boolean gras, float largeurMax) {
        for (String f : formes) if (largeur(f, pixel, gras) <= largeurMax) return f;
        return formes[formes.length - 1];
    }

    /** Écrit une ligne à (x, y) : coin haut-gauche de la case de 12 rangées ; les capitales occupent les rangées 3 à 9. */
    static void ecrire(Canvas c, String s, float x, float y, int pixel, int couleur, boolean gras, Paint encre) {
        dessiner(c, Collections.singletonList(PolicePixel.preparer(preparer(s))), pixel, x, y, couleur, gras, encre, null, 0, 0);
    }

    /** Écrit une ligne centrée sur cx. */
    static void centrer(Canvas c, String s, float cx, float y, int pixel, int couleur, boolean gras, Paint encre) {
        ecrire(c, s, Math.round(cx - largeur(s, pixel, gras) / 2f), y, pixel, couleur, gras, encre);
    }

    /** Des lignes déjà coupées ; alignement : Gravity.LEFT, CENTER_HORIZONTAL ou RIGHT dans la largeur donnée. */
    static void dessiner(Canvas c, List<String> lignes, int pixel, float x0, float y0, int couleur, boolean gras, Paint encre,
                         Paint systeme, int alignement, int largeur) {
        PolicePixel p = police(gras);
        if (p == null) return;
        PolicePixel d = pixel % 2 == 0 ? PolicePixel.ressource(gras ? "titre2x" : "texte2x") : null;
        if (d == null) d = p;
        float pas = (float) pixel / d.echelle;
        encre.setAntiAlias(false);
        encre.setStyle(Paint.Style.FILL);
        Map<Integer, String> sg = signes();
        for (int n = 0; n < lignes.size(); n++) {
            String ligne = lignes.get(n);
            float dx = 0;
            if (alignement != 0 && largeur > 0) {
                int lw = p.largeur(ligne) * pixel;
                if ((alignement & Gravity.HORIZONTAL_GRAVITY_MASK) == Gravity.CENTER_HORIZONTAL) dx = (largeur - lw) / 2;
                else if ((alignement & Gravity.HORIZONTAL_GRAVITY_MASK) == Gravity.RIGHT) dx = largeur - lw;
            }
            float xl = x0 + dx, yl = y0 + n * d.ligne * pixel;
            for (PolicePixel.Pose pose : d.poser(Collections.singletonList(ligne))) {
                float gx = xl + pose.x * pixel;
                if (pose.dessin == null) {
                    int code = pose.code;
                    if (code == ' ' || code == 0xA0 || code == 0x202F || code == 0x2009) continue;
                    String id = sg.get(code);
                    Sprites.Sprite s = id == null ? null : Sprites.banque().get(id, pixel % 2 == 0 ? 2 : 1);
                    if (s != null) {
                        icone(c, s, gx, yl + 3 * pixel, s.images.get(0).length > 7 ? pixel / 2f : pixel, couleur, encre);
                    } else if (systeme != null) {
                        systeme.setColor(couleur);
                        systeme.setTextSize(9f * pixel);
                        String t = new String(Character.toChars(code));
                        float cx = gx + p.inconnu * pixel / 2f, cy = yl + 6.5f * pixel;
                        Paint.FontMetrics fm = systeme.getFontMetrics();
                        c.drawText(t, cx - systeme.measureText(t) / 2, cy - (fm.ascent + fm.descent) / 2, systeme);
                    }
                    continue;
                }
                encre.setColor(couleur);
                String[] rangs = pose.dessin.rangs;
                for (int r = 0; r < rangs.length; r++) {
                    String rang = rangs[r];
                    int k = 0, fin;
                    while (k < rang.length()) {
                        if (rang.charAt(k) != '#') {
                            k++;
                            continue;
                        }
                        fin = k;
                        while (fin < rang.length() && rang.charAt(fin) == '#') fin++;
                        float y = yl + (pose.dessin.haut + r) * pas;
                        c.drawRect(gx + k * pas, y, gx + fin * pas, y + pas, encre);
                        k = fin;
                    }
                }
            }
        }
    }

    // ------------------------------------------------------------------------------------------------- Titre-logo

    /**
     * La grille d'un titre-logo au pixel fin (le pendant de LogoPixel.cs, docs/STYLE.md « Titres-logos ») : les lettres
     * de la police « titre » en dessin fin (capitales de 14 pixels), une arête claire en haut de chaque trait, une
     * arête sombre en bas, un cerne d'un pixel et une ombre portée d'un pixel en bas à droite. Seule la boîte de
     * l'encre est gardée. Valeurs : 0 vide, 1 ombre, 2 cerne, 3 corps, 4 arête claire, 5 arête sombre.
     */
    static byte[][] grilleLogo(String texte) {
        PolicePixel d = PolicePixel.ressource("titre2x");
        if (d == null) d = PolicePixel.ressource("titre");
        if (d == null) return new byte[0][0];
        int f = 2 / d.echelle;
        List<String> lignes = Collections.singletonList(PolicePixel.preparer(preparer(texte)));
        int largeur = d.largeur(lignes.get(0)) * 2 + 2, hauteur = d.ligne * 2;
        boolean[][] encre = new boolean[hauteur][largeur];
        int haut = Integer.MAX_VALUE, bas = -1, droite = 0;
        for (PolicePixel.Pose pose : d.poser(lignes)) {
            if (pose.dessin == null) continue;
            String[] rangs = pose.dessin.rangs;
            for (int r = 0; r < rangs.length; r++)
                for (int k = 0; k < rangs[r].length(); k++) {
                    if (rangs[r].charAt(k) != '#') continue;
                    for (int dy = 0; dy < f; dy++)
                        for (int dx = 0; dx < f; dx++) {
                            int x = pose.x * 2 + k * f + dx, y = pose.y * 2 + (pose.dessin.haut + r) * f + dy;
                            if (y < 0 || y >= hauteur || x < 0 || x >= largeur) continue;
                            encre[y][x] = true;
                            haut = Math.min(haut, y);
                            bas = Math.max(bas, y);
                            droite = Math.max(droite, x);
                        }
                }
        }
        if (bas < 0) return new byte[0][0];
        int w = droite + 4, h = bas - haut + 4;
        byte[][] g = new byte[h][w];
        for (int y = -1; y < h - 1; y++)
            for (int x = -1; x < w - 1; x++) {
                byte v = 0;
                if (encreLogo(encre, haut, bas, droite, y, x))
                    v = !encreLogo(encre, haut, bas, droite, y - 1, x) ? (byte) 4 : !encreLogo(encre, haut, bas, droite, y + 1, x) ? (byte) 5 : (byte) 3;
                else if (pleinLogo(encre, haut, bas, droite, y, x)) v = 2;
                else if (pleinLogo(encre, haut, bas, droite, y - 1, x - 1)) v = 1;
                g[y + 1][x + 1] = v;
            }
        return g;
    }

    private static boolean encreLogo(boolean[][] e, int haut, int bas, int droite, int y, int x) {
        return y >= 0 && y <= bas - haut && x >= 0 && x <= droite && e[y + haut][x];
    }

    private static boolean pleinLogo(boolean[][] e, int haut, int bas, int droite, int y, int x) {
        for (int dy = -1; dy <= 1; dy++)
            for (int dx = -1; dx <= 1; dx++)
                if (encreLogo(e, haut, bas, droite, y + dy, x + dx)) return true;
        return false;
    }

    /** Dessine un titre-logo : (x, y) son coin haut-gauche, fin : pixels de l'écran par pixel du logo. */
    static void logo(Canvas c, byte[][] g, float x, float y, int fin, int couleur, int ombre, int cerne, Paint pt) {
        int clair = melange(couleur, 0xffffffff, 0.45f), sombre = melange(couleur, 0xff2a1a3a, 0.38f);
        pt.setAntiAlias(false);
        pt.setStyle(Paint.Style.FILL);
        for (int j = 0; j < g.length; j++) {
            int i = 0;
            while (i < g[j].length) {
                byte v = g[j][i];
                int k = i;
                while (k < g[j].length && g[j][k] == v) k++;
                if (v != 0) {
                    pt.setColor(v == 1 ? ombre : v == 2 ? cerne : v == 4 ? clair : v == 5 ? sombre : couleur);
                    c.drawRect(x + i * fin, y + j * fin, x + k * fin, y + (j + 1) * fin, pt);
                }
                i = k;
            }
        }
    }

    private static final int ENCRE_ICONE = 0xff1c2128;

    /** Dessine une icône : son encre prend la couleur donnée, son accent orange reste. pas : pixels d'écran par pixel du sprite. */
    static void icone(Canvas c, Sprites.Sprite s, float x, float y, float pas, int couleur, Paint pt) {
        if (s == null) return;
        pt.setAntiAlias(false);
        pt.setStyle(Paint.Style.FILL);
        String[] im = s.images.get(0);
        for (int j = 0; j < im.length; j++) {
            String l = im[j];
            int i = 0;
            while (i < l.length()) {
                char ch = l.charAt(i);
                if (ch == '.') {
                    i++;
                    continue;
                }
                int fin = i;
                while (fin < l.length() && l.charAt(fin) == ch) fin++;
                int col = Sprites.couleur(s.palette.get(ch));
                pt.setColor(col == ENCRE_ICONE ? couleur : col);
                c.drawRect(x + i * pas, y + j * pas, x + fin * pas, y + (j + 1) * pas, pt);
                i = fin;
            }
        }
    }

    /**
     * Un texte en police pixel. C'est un TextView (setText, setTextColor, setGravity, setSingleLine, lecteur d'écran)
     * dont la mesure et le dessin sont ceux de la police pixel : coupé à la largeur, pixels entiers, dessin fin (2×)
     * quand il tombe juste. Sans la police (ressource absente), il reste un TextView ordinaire.
     */
    static final class Texte extends TextView {
        private final int pixel;
        private final boolean gras;
        private List<String> lignes = Collections.emptyList();
        private final Paint encre = new Paint(), systeme = new Paint(Paint.ANTI_ALIAS_FLAG);
        private String icone;
        private int largeurTexte, hauteurTexte;

        Texte(Context c, CharSequence s, float tailleDp, int couleur, boolean gras) {
            this(c, s, Style.pixel(c, tailleDp), couleur, gras, true);
        }

        /** Taille donnée en pixels de l'écran par pixel de police (libellés qui doivent tenir dans une case). */
        Texte(Context c, CharSequence s, int pixel, int couleur, boolean gras, boolean exact) {
            super(c);
            this.pixel = Math.max(1, pixel);
            this.gras = gras;
            setTextColor(couleur);
            setIncludeFontPadding(false);
            systeme.setTypeface(Typeface.DEFAULT);
            setText(s);
        }

        int pixel() {
            return pixel;
        }

        /** Une icône 12 × 12 (« ui-… ») devant le texte, à la hauteur des capitales ; null : aucune. */
        Texte icone(String id) {
            icone = id;
            requestLayout();
            invalidate();
            return this;
        }

        private int largeurIcone() {
            return icone == null ? 0 : 12 * pixel + (getText().length() == 0 ? 0 : 3 * pixel);
        }

        @Override
        public void setText(CharSequence text, BufferType type) {
            super.setText(text, type);
            requestLayout();
            invalidate();
        }

        @Override
        protected void onMeasure(int mw, int mh) {
            PolicePixel p = police(gras);
            if (p == null) {
                super.onMeasure(mw, mh);
                return;
            }
            int mode = MeasureSpec.getMode(mw);
            int dispo = mode == MeasureSpec.UNSPECIFIED ? Integer.MAX_VALUE : MeasureSpec.getSize(mw);
            if (getMaxWidth() > 0 && getMaxWidth() < dispo) dispo = getMaxWidth();
            int marges = getPaddingLeft() + getPaddingRight() + largeurIcone();
            int max = dispo >= Integer.MAX_VALUE / 2 ? 0 : Math.max(1, (dispo - marges) / pixel);
            int maxLignes = getMaxLines() > 0 && getMaxLines() < 1000 ? getMaxLines() : 0;
            lignes = p.couper(preparer(getText()), max, maxLignes);
            int[] b = p.boite(lignes);
            largeurTexte = b[0] * pixel;
            hauteurTexte = Math.max(b[1], icone == null ? 0 : 12) * pixel;
            int w = largeurTexte + marges;
            if (mode == MeasureSpec.EXACTLY) w = MeasureSpec.getSize(mw);
            else w = Math.max(w, getSuggestedMinimumWidth());
            int h = hauteurTexte + getPaddingTop() + getPaddingBottom();
            h = Math.max(h, Math.max(getSuggestedMinimumHeight(), getMinHeight()));
            if (MeasureSpec.getMode(mh) == MeasureSpec.EXACTLY) h = MeasureSpec.getSize(mh);
            setMeasuredDimension(w, h);
        }

        @Override
        protected void onDraw(Canvas c) {
            if (police(gras) == null) {
                super.onDraw(c);
                return;
            }
            int couleur = getCurrentTextColor();
            int g = getGravity();
            int dedansL = getWidth() - getPaddingLeft() - getPaddingRight(), dedansH = getHeight() - getPaddingTop() - getPaddingBottom();
            int y = getPaddingTop();
            int gv = g & Gravity.VERTICAL_GRAVITY_MASK;
            if (gv == Gravity.CENTER_VERTICAL) y += (dedansH - hauteurTexte) / 2;
            else if (gv == Gravity.BOTTOM) y += dedansH - hauteurTexte;
            int gh = g & Gravity.HORIZONTAL_GRAVITY_MASK;
            int x = getPaddingLeft(), li = largeurIcone(), bloc = largeurTexte + li;
            if (gh == Gravity.CENTER_HORIZONTAL) x += (dedansL - bloc) / 2;
            else if (gh == Gravity.RIGHT || (g & Gravity.RELATIVE_HORIZONTAL_GRAVITY_MASK) == Gravity.END) x += dedansL - bloc;
            if (icone != null) {
                Sprites.Sprite s = Sprites.banque().get(icone, pixel % 2 == 0 ? 2 : 1);
                if (s != null) Style.icone(c, s, x, y, s.images.get(0).length > 12 ? pixel / 2f : pixel, couleur, encre);
            }
            // Chaque ligne s'aligne dans le bloc de texte (centrée si le texte l'est).
            Style.dessiner(c, lignes, pixel, x + li, y, couleur, gras, encre, systeme,
                    gh == Gravity.CENTER_HORIZONTAL ? Gravity.CENTER_HORIZONTAL : 0, largeurTexte);
        }
    }

    /** Même signature que Ui.texte : la taille en sp choisit petit, corps ou titre de page ; gras : la police « titre ». */
    static Texte texte(Context c, CharSequence s, float sp, int couleur, boolean gras) {
        return new Texte(c, s, taille(sp), couleur, gras || sp >= 17);
    }

    static Texte titrePage(Context c, String s) {
        Texte t = new Texte(c, s, PAGE, p(c).texte, true);
        t.setPadding(0, Ui.dp(c, 12), 0, Ui.dp(c, 2));
        return t;
    }

    static Texte sousTitre(Context c, String s) {
        Texte t = new Texte(c, s, CORPS, p(c).pale, false);
        t.setPadding(0, 0, 0, Ui.dp(c, 14));
        return t;
    }

    // ---------------------------------------------------------------------------------------------------- Cadres

    /**
     * Le cadre en pixels, celui du menu « Sept portes » tel que l'Aventure l'a posé sur le téléphone (docs/SCENES.md) :
     * un module de bord aux coins en escalier (le pixel du coin manque), un module de biseau à l'intérieur (clair en haut
     * et à gauche, sombre en bas et à droite), le fond, et une ombre portée d'un module en bas et à droite.
     * « fin » : sans l'ombre portée (boutons, cases). « plat » : le bord seul (puces, étiquettes). « pointille » : le
     * bord en pointillés, sans biseau (ce qui est fermé). Aucun arrondi, aucun lissage.
     */
    static class Cadre extends Drawable {
        static final int PLEIN = 0, FIN = 1, PLAT = 2;
        final int u, sorte;
        private final int fond, ombre, bord, clair, sombre;
        private boolean pointille;
        private final Paint pt = new Paint();

        /** ext : la couleur de l'ombre portée (cadre plein) ou du bord (fin, plat) ; bord : le bord du cadre plein. */
        Cadre(int u, int sorte, int fond, int ext, int bord, int clair, int sombre) {
            this.u = u;
            this.sorte = sorte;
            this.fond = fond;
            this.ombre = ext;
            this.bord = sorte == PLEIN ? bord : ext;
            this.clair = clair;
            this.sombre = sombre;
            pt.setAntiAlias(false);
        }

        Cadre pointille() {
            pointille = true;
            return this;
        }

        /** Ce que le cadre prend à gauche et en haut (bord, biseau). À droite et en bas, l'ombre portée s'ajoute. */
        int epaisseur() {
            return sorte == PLAT ? u : 2 * u;
        }

        int portee() {
            return sorte == PLEIN ? u : 0;
        }

        @Override
        public boolean getPadding(Rect r) {
            int e = epaisseur();
            r.set(e, e, e + portee(), e + portee());
            return true;
        }

        private void rect(Canvas c, int g, int h, int d, int b, int couleur) {
            if (d <= g || b <= h || couleur == 0) return;
            pt.setColor(couleur);
            c.drawRect(g, h, d, b, pt);
        }

        // Un rectangle sans ses quatre pixels de coin : les coins en escalier.
        private void escalier(Canvas c, int g, int h, int d, int b, int couleur) {
            rect(c, g + u, h, d - u, b, couleur);
            rect(c, g, h + u, d, b - u, couleur);
        }

        @Override
        public void draw(Canvas c) {
            Rect z = getBounds();
            int g = z.left, h = z.top, d = z.right - portee(), bas = z.bottom - portee();
            if (d - g <= 2 * u || bas - h <= 2 * u) {
                rect(c, g, h, d, bas, fond);
                return;
            }
            if (sorte == PLEIN) escalier(c, g + u, h + u, d + u, bas + u, ombre);
            if (pointille) {
                rect(c, g + u, h + u, d - u, bas - u, fond);
                pt.setColor(bord);
                for (int x = g + u; x + u <= d - u; x += 2 * u) {
                    c.drawRect(x, h, x + u, h + u, pt);
                    c.drawRect(x, bas - u, x + u, bas, pt);
                }
                for (int y = h + u; y + u <= bas - u; y += 2 * u) {
                    c.drawRect(g, y, g + u, y + u, pt);
                    c.drawRect(d - u, y, d, y + u, pt);
                }
                return;
            }
            escalier(c, g, h, d, bas, bord);
            int ig = g + u, ih = h + u, id = d - u, ib = bas - u;
            rect(c, ig, ih, id, ib, fond);
            if (sorte != PLAT && id - ig >= 3 * u && ib - ih >= 3 * u) {
                rect(c, ig, ih, id, ih + u, clair);
                rect(c, ig, ih + u, ig + u, ib - u, clair);
                rect(c, id - u, ih + u, id, ib - u, sombre);
                rect(c, ig, ib - u, id, ib, sombre);
            }
        }

        @Override
        public void setAlpha(int a) {
        }

        @Override
        public void setColorFilter(ColorFilter f) {
        }

        @Override
        public int getOpacity() {
            return PixelFormat.TRANSLUCENT;
        }
    }

    static Cadre cadre(Context c, Palette p) {
        return new Cadre(u(c), Cadre.PLEIN, p.carte, p.bordExt, p.bord, p.biseauClair, p.biseauSombre);
    }

    /** Cadre plein dont le module de couleur prend une autre couleur (carte qui appelle : orange). */
    static Cadre cadre(Context c, Palette p, int bord) {
        return new Cadre(u(c), Cadre.PLEIN, p.carte, p.bordExt, bord, p.biseauClair, p.biseauSombre);
    }

    static Cadre cadreFin(Context c, Palette p, int fond) {
        return new Cadre(u(c), Cadre.FIN, fond, p.bord, 0, p.biseauClair, p.biseauSombre);
    }

    static Cadre plat(Context c, int fond, int bord) {
        return new Cadre(u(c), Cadre.PLAT, fond, bord, 0, 0, 0);
    }

    /** Carte qu'on touche : sous le doigt, le fond prend la couleur d'accent (le « survol » du menu). */
    static Drawable touchable(Context c, Palette p, int bord) {
        StateListDrawable s = new StateListDrawable();
        s.addState(new int[]{android.R.attr.state_pressed}, new Cadre(u(c), Cadre.PLEIN, melange(p.carte, p.accent, 0.3f), 0, p.accent, p.biseauSombre, p.biseauClair));
        s.addState(new int[0], cadre(c, p, bord == 0 ? p.bord : bord));
        return s;
    }

    private static boolean fonce(int c) {
        return (((c >> 16) & 255) * 299 + ((c >> 8) & 255) * 587 + (c & 255) * 114) / 1000 < 90;
    }

    /**
     * Le cadre en pixels qui remplace un fond arrondi du système : une carte (rayon ≥ 16 avec un bord) prend le cadre
     * plein, tout autre fond bordé un cadre plat, un fond sans bord un simple pavé aux coins en escalier.
     */
    static Drawable arrondi(Context c, int fond, float rayon, int bord) {
        Palette p = fonce(fond) && (fond >>> 24) == 255 ? NUIT : p(c);
        if (rayon >= 16 && bord != 0)
            return new Cadre(u(c), Cadre.PLEIN, fond, p.bordExt, bord == Ui.p(c).bord ? p.bord : bord, p.biseauClair, p.biseauSombre);
        return new Cadre(u(c), Cadre.PLAT, fond, bord != 0 ? bord : fond, 0, 0, 0);
    }

    /** Ce qu'on touche : sous le doigt, un cadre plat à la couleur d'accent (le « survol » du menu). */
    static Drawable touchable(Context c, Drawable repos, float rayon) {
        Palette p = p(c);
        StateListDrawable s = new StateListDrawable();
        boolean plein = repos instanceof Cadre && ((Cadre) repos).sorte == Cadre.PLEIN;
        s.addState(new int[]{android.R.attr.state_pressed}, plein
                ? new Cadre(u(c), Cadre.PLEIN, melange(p.carte, p.accent, 0.3f), 0, p.accent, p.biseauSombre, p.biseauClair)
                : plat(c, melange(p.carte, p.accent, 0.3f), p.accent));
        s.addState(new int[0], repos);
        return s;
    }

    /** Pose un fond sans perdre les marges de la vue ; elles valent au moins l'épaisseur du cadre. */
    static void fond(View v, Drawable d) {
        int g = v.getPaddingLeft(), h = v.getPaddingTop(), dr = v.getPaddingRight(), b = v.getPaddingBottom();
        v.setBackground(d);
        Rect r = new Rect();
        if (d != null && d.getPadding(r)) v.setPadding(Math.max(g, r.left), Math.max(h, r.top), Math.max(dr, r.right), Math.max(b, r.bottom));
        else v.setPadding(g, h, dr, b);
    }

    static int melange(int a, int b, float t) {
        int r = Math.round(((a >> 16) & 255) * (1 - t) + ((b >> 16) & 255) * t), g = Math.round(((a >> 8) & 255) * (1 - t) + ((b >> 8) & 255) * t),
                bl = Math.round((a & 255) * (1 - t) + (b & 255) * t);
        return 0xff000000 | r << 16 | g << 8 | bl;
    }

    /** Carte : cadre plein, contenu vertical, 12 dp de marge intérieure. */
    static LinearLayout carte(Context c) {
        return carte(c, p(c));
    }

    static LinearLayout carte(Context c, Palette p) {
        LinearLayout l = Ui.pile(c);
        l.setBackground(cadre(c, p));
        int m = 2 * u(c) + Ui.dp(c, 12);
        l.setPadding(m, m, m + u(c), m + u(c));
        return l;
    }

    // ---------------------------------------------------------------------------------------------------- Boutons

    /**
     * Bouton. Principal (plein) : fond d'accent, texte inversé, biseau en relief. Secondaire : fond de carte.
     * Appui : le biseau s'inverse (le bouton s'enfonce) et le secondaire prend le fond d'accent.
     * Fermé (setEnabled(false)) : texte éteint, cadre en pointillés.
     */
    static Texte bouton(Context c, String s, boolean plein, View.OnClickListener action) {
        return bouton(c, p(c), s, plein, action);
    }

    static Texte bouton(Context c, Palette p, String s, boolean plein, View.OnClickListener action) {
        Texte b = new Texte(c, s, CORPS, p.texte, true);
        int u = u(c);
        int[][] etats = {{-android.R.attr.state_enabled}, {android.R.attr.state_pressed}, {}};
        b.setTextColor(new ColorStateList(etats, new int[]{p.eteint, p.surAccent, plein ? p.surAccent : p.texte}));
        int haut = melange(p.accent, 0xffffffff, 0.35f), bas = melange(p.accent, 0xff000000, 0.35f);
        StateListDrawable d = new StateListDrawable();
        d.addState(etats[0], new Cadre(u, Cadre.FIN, p.carte, p.eteint, 0, p.carte, p.carte).pointille());
        d.addState(etats[1], new Cadre(u, Cadre.FIN, p.accent, p.bordExt, 0, bas, haut));
        d.addState(etats[2], plein ? new Cadre(u, Cadre.FIN, p.accent, p.bordExt, 0, haut, bas) : cadreFin(c, p, p.carte));
        b.setBackground(d);
        b.setGravity(Gravity.CENTER);
        b.setPadding(2 * u + Ui.dp(c, 14), 2 * u + Ui.dp(c, 6), 2 * u + Ui.dp(c, 14), 2 * u + Ui.dp(c, 6));
        b.setMinHeight(Ui.dp(c, 48));
        b.setClickable(true);
        b.setFocusable(true);
        b.setOnClickListener(action);
        return b;
    }

    /**
     * Étiquette d'un ou deux mots (prix, « NIV 15 », « À TOI ») : capitales, police « titre », taille « petit ». C'est la
     * seule place de la taille « petit » avec les titres de section : en capitales, sa hauteur de lettre vaut celle
     * d'un texte courant (docs/STYLE.md, « Plancher de lisibilité »).
     */
    static Texte etiquette(Context c, String s, int couleur) {
        Texte t = new Texte(c, s.toUpperCase(Locale.FRENCH), PETIT, couleur, true);
        t.setSingleLine(true);
        return t;
    }

    /** Puce : un mot dans un cadre plat (état, étiquette). La couleur borde et écrit ; le fond reste celui de la carte. */
    static Texte puce(Context c, String s, int couleur) {
        Texte t = new Texte(c, s, CORPS, couleur, true);
        puce(t, couleur);
        t.setSingleLine(true);
        return t;
    }

    static void puce(Texte t, int couleur) {
        Context c = t.getContext();
        int u = u(c);
        t.setTextColor(couleur);
        t.setBackground(plat(c, melange(p(c).carte, couleur, 0.12f), couleur));
        t.setPadding(u + Ui.dp(c, 8), u + Ui.dp(c, 2), u + Ui.dp(c, 8), u + Ui.dp(c, 2));
    }

    /** Case : un signe dans un carré au cadre fin (ce que la pastille ronde était). La forme du signe dit l'état. */
    static Texte caseSigne(Context c, String signe, int couleur) {
        Texte t = new Texte(c, signe, CORPS, couleur, false);
        t.setGravity(Gravity.CENTER);
        Palette p = p(c);
        t.setBackground(new Cadre(u(c), Cadre.PLAT, melange(p.carte, couleur, 0.12f), couleur, 0, 0, 0));
        int d = Ui.dp(c, 38);
        t.setLayoutParams(new LinearLayout.LayoutParams(d, d));
        return t;
    }

    // ---------------------------------------------------------------------------------------------------- Réglages

    /**
     * La case à cocher du menu « Sept portes » : un carré vide au bord de deux pixels ; cochée, le carré laisse la
     * place à la coche ✓, à la couleur du choix. La forme dit l'état, pas la couleur.
     */
    static final class Coche extends View implements android.widget.Checkable {
        private boolean cochee;
        private final int px;
        private final Palette p;
        private final Paint pt = new Paint();
        private java.util.function.Consumer<Boolean> choix;

        Coche(Context c, Palette p, boolean cochee) {
            super(c);
            this.p = p;
            this.cochee = cochee;
            px = Math.max(1, Math.round(1.5f * c.getResources().getDisplayMetrics().density));
            pt.setAntiAlias(false);
            setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
        }

        void auChoix(java.util.function.Consumer<Boolean> c) {
            choix = c;
        }

        @Override
        public void setChecked(boolean oui) {
            if (oui == cochee) return;
            cochee = oui;
            invalidate();
            if (choix != null) choix.accept(oui);
        }

        @Override
        public boolean isChecked() {
            return cochee;
        }

        @Override
        public void toggle() {
            setChecked(!cochee);
        }

        @Override
        protected void onMeasure(int l, int h) {
            setMeasuredDimension(12 * px, 12 * px);
        }

        @Override
        protected void onDraw(Canvas c) {
            if (cochee) {
                boolean fin = px % 2 == 0;
                Style.icone(c, Sprites.banque().get("ui-coche", fin ? 2 : 1), 0, 0, fin ? px / 2f : px, isEnabled() ? p.coche : p.eteint, pt);
                return;
            }
            pt.setColor(isEnabled() ? p.pale : p.eteint);
            c.drawRect(px, px, 11 * px, 3 * px, pt);
            c.drawRect(px, 9 * px, 11 * px, 11 * px, pt);
            c.drawRect(px, 3 * px, 3 * px, 9 * px, pt);
            c.drawRect(9 * px, 3 * px, 11 * px, 9 * px, pt);
        }
    }

    /** Ligne de réglage qu'on coche : titre, explication, case à cocher. Un toucher sur la ligne la bascule. */
    static Coche interrupteur(Context c, LinearLayout dans, String titre, String sous, boolean actif, java.util.function.Consumer<Boolean> choix) {
        Palette p = p(c);
        LinearLayout r = Ui.rangee(c);
        r.setPadding(Ui.dp(c, 4), Ui.dp(c, 8), Ui.dp(c, 4), Ui.dp(c, 8));
        r.setMinimumHeight(Ui.dp(c, 48));
        LinearLayout t = Ui.pile(c);
        t.addView(new Texte(c, titre, CORPS, p.texte, false));
        if (sous != null && !sous.isEmpty()) t.addView(new Texte(c, sous, CORPS, p.pale, false));
        LinearLayout.LayoutParams lt = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1);
        lt.rightMargin = Ui.dp(c, 10);
        r.addView(t, lt);
        Coche k = new Coche(c, p, actif);
        k.auChoix(oui -> {
            r.setContentDescription(titre + (oui ? " : coché" : " : décoché"));
            choix.accept(oui);
        });
        r.setContentDescription(titre + (actif ? " : coché" : " : décoché"));
        r.addView(k);
        fond(r, touchable(c, plat(c, 0, 0), 0));
        r.setOnClickListener(v -> k.toggle());
        dans.addView(r, Ui.large());
        return k;
    }

    /** Ligne qu'on touche : titre, explication, chevron. */
    static View ligne(Context c, String titre, String sous, int couleurTitre, View.OnClickListener action) {
        Palette p = p(c);
        LinearLayout r = Ui.rangee(c);
        r.setPadding(Ui.dp(c, 4), Ui.dp(c, 8), Ui.dp(c, 4), Ui.dp(c, 8));
        r.setMinimumHeight(Ui.dp(c, 48));
        LinearLayout t = Ui.pile(c);
        t.addView(new Texte(c, titre, CORPS, couleurTitre == 0 ? p.texte : couleurTitre, false));
        if (sous != null && !sous.isEmpty()) t.addView(new Texte(c, sous, CORPS, p.pale, false));
        LinearLayout.LayoutParams lt = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1);
        lt.rightMargin = Ui.dp(c, 10);
        r.addView(t, lt);
        if (action != null) {
            r.addView(chevron(c, p.pale));
            fond(r, touchable(c, plat(c, 0, 0), 0));
            r.setOnClickListener(action);
        }
        return r;
    }

    /** Champ de saisie : la police est celle du système (docs/STYLE.md), le cadre est en pixels, dans le creux. */
    static void champ(android.widget.EditText e) {
        Context c = e.getContext();
        Palette p = p(c);
        e.setTextColor(p.texte);
        e.setHintTextColor(p.eteint);
        e.setBackground(plat(c, p.creux, p.bord));
        e.setPadding(Ui.dp(c, 14), Ui.dp(c, 12), Ui.dp(c, 14), Ui.dp(c, 12));
    }

    /** Curseur : une barre en cases (pleines jusqu'à la valeur) et un poussoir carré au cadre fin. */
    static void curseur(android.widget.SeekBar b) {
        Context c = b.getContext();
        Palette p = p(c);
        int u = u(c);
        b.setProgressDrawable(new Drawable() {
            private final Paint pt = new Paint();

            @Override
            public void draw(Canvas cv) {
                Rect z = getBounds();
                barre(cv, z.left, z.centerY() - u, z.width(), 2 * u, u, getLevel() / 10000f, p.coche, 0, p.creux, pt);
            }

            @Override
            protected boolean onLevelChange(int niveau) {
                invalidateSelf();
                return true;
            }

            @Override
            public void setAlpha(int a) {
            }

            @Override
            public void setColorFilter(ColorFilter f) {
            }

            @Override
            public int getOpacity() {
                return PixelFormat.TRANSLUCENT;
            }
        });
        b.setThumb(new Cadre(u, Cadre.FIN, p.carte, p.coche, 0, p.biseauClair, p.biseauSombre) {
            @Override
            public int getIntrinsicWidth() {
                return 6 * u;
            }

            @Override
            public int getIntrinsicHeight() {
                return 8 * u;
            }
        });
        b.setThumbOffset(0);
        b.setSplitTrack(false);
        b.setBackground(null);
        b.setMinimumHeight(Ui.dp(c, 40));
        b.setPadding(0, Ui.dp(c, 8), 0, Ui.dp(c, 8));
    }

    /** Message bref (ce que le système appelle un toast) : un cadre de nuit, en police pixel. */
    @SuppressWarnings("deprecation")
    static void dire(Context c, String s, boolean long_) {
        try {
            Texte t = new Texte(c, s, CORPS, NUIT.texte, false);
            t.setGravity(Gravity.CENTER_HORIZONTAL);
            t.setMaxWidth(Ui.dp(c, 300));
            int m = 2 * u(c) + Ui.dp(c, 12);
            t.setPadding(m, m - Ui.dp(c, 4), m + u(c), m - Ui.dp(c, 4) + u(c));
            t.setBackground(cadre(c, NUIT));
            t.setPadding(m, m - Ui.dp(c, 4), m + u(c), m - Ui.dp(c, 4) + u(c));
            android.widget.Toast toast = new android.widget.Toast(c.getApplicationContext());
            toast.setView(t);
            toast.setDuration(long_ ? android.widget.Toast.LENGTH_LONG : android.widget.Toast.LENGTH_SHORT);
            toast.show();
        } catch (RuntimeException e) {
            android.widget.Toast.makeText(c, s, long_ ? android.widget.Toast.LENGTH_LONG : android.widget.Toast.LENGTH_SHORT).show();
        }
    }

    // ---------------------------------------------------------------------------------------------------- Pointillés, titres

    /** Ligne de pointillés : un module allumé, un module éteint, d'un bord à l'autre. */
    static final class Pointilles extends View {
        private final Paint pt = new Paint();
        private final int u;

        Pointilles(Context c, int couleur) {
            super(c);
            u = u(c);
            pt.setColor(couleur);
            pt.setAntiAlias(false);
            setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
        }

        @Override
        protected void onMeasure(int l, int h) {
            setMeasuredDimension(MeasureSpec.getSize(l), u);
        }

        @Override
        protected void onDraw(Canvas c) {
            for (int x = 0; x + u <= getWidth(); x += 2 * u) c.drawRect(x, 0, x + u, u, pt);
        }
    }

    /** Séparateur dans une carte : pointillés, 4 dp au-dessus et au-dessous. */
    static View separateur(Context c) {
        return separateur(c, p(c));
    }

    static View separateur(Context c, Palette p) {
        Pointilles v = new Pointilles(c, p.pointilles);
        LinearLayout.LayoutParams l = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        l.topMargin = l.bottomMargin = Ui.dp(c, 6);
        v.setLayoutParams(l);
        return v;
    }

    /** Titre de section : petites capitales violettes, puis des pointillés jusqu'au bord (« EN CE MOMENT ······ »). */
    static final class TitreSection extends LinearLayout {
        final Texte texte;

        TitreSection(Context c, Palette p, String s) {
            super(c);
            setOrientation(HORIZONTAL);
            setGravity(Gravity.CENTER_VERTICAL);
            texte = new Texte(c, s.toUpperCase(Locale.FRENCH), PETIT, p.titre, true);
            texte.setSingleLine(true);
            addView(texte);
            Pointilles pts = new Pointilles(c, p.pointilles);
            LayoutParams l = new LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1);
            l.leftMargin = 3 * u(c);
            addView(pts, l);
            setPadding(Ui.dp(c, 2), Ui.dp(c, 12), 0, Ui.dp(c, 6));
        }

        void setText(String s) {
            texte.setText(s.toUpperCase(Locale.FRENCH));
        }
    }

    static TitreSection titreSection(Context c, String s) {
        return new TitreSection(c, p(c), s);
    }

    /** Chevron « suite » au bout d'une ligne qu'on touche (l'icône, pas le signe de clavier ›). */
    static Icone chevron(Context c, int couleur) {
        return new Icone(c, "ui-suite", couleur, 1.5f);
    }

    // ---------------------------------------------------------------------------------------------------- Icône, barre

    /** Icône pixel de la banque (« ui-… », 12 × 12) : un pixel de l'icône = pixelDp dp, en pixels entiers. */
    static final class Icone extends View {
        private String id;
        private int couleur;
        private final int pixel;
        private final Paint pt = new Paint();

        Icone(Context c, String id, int couleur, float pixelDp) {
            super(c);
            this.id = id;
            this.couleur = couleur;
            pixel = Math.max(1, Math.round(pixelDp * c.getResources().getDisplayMetrics().density));
            setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
        }

        void couleur(int c) {
            couleur = c;
            invalidate();
        }

        void icone(String i) {
            id = i;
            requestLayout();
            invalidate();
        }

        private Sprites.Sprite sprite(int echelle) {
            return Sprites.banque().get(id, echelle);
        }

        @Override
        protected void onMeasure(int l, int h) {
            Sprites.Sprite s = sprite(1);
            int w = s == null ? 12 : s.w(), hh = s == null ? 12 : s.h();
            setMeasuredDimension(w * pixel + getPaddingLeft() + getPaddingRight(), hh * pixel + getPaddingTop() + getPaddingBottom());
        }

        @Override
        protected void onDraw(Canvas c) {
            boolean fin = pixel % 2 == 0;
            Style.icone(c, sprite(fin ? 2 : 1), getPaddingLeft(), getPaddingTop(), fin ? pixel / 2f : pixel, couleur, pt);
        }
    }

    /** Barre de progression : cases d'un module et demi de large dans un creux, la dernière case pleine en orange. */
    static final class Barre extends View {
        private float part;
        private final Paint pt = new Paint();
        private final Palette p;
        private final int u;

        Barre(Context c) {
            this(c, Style.p(c));
        }

        Barre(Context c, Palette p) {
            super(c);
            this.p = p;
            u = u(c);
            pt.setAntiAlias(false);
        }

        void part(float v) {
            part = Math.max(0, Math.min(1, v));
            invalidate();
        }

        @Override
        protected void onMeasure(int l, int h) {
            setMeasuredDimension(MeasureSpec.getSize(l), 4 * u);
        }

        @Override
        protected void onDraw(Canvas c) {
            barre(c, 0, 0, getWidth(), getHeight(), u, part, p.bleu, p.orange, p.creux, pt);
        }
    }

    /** Dessine une barre en cases : case de 3 modules, écart d'un module, calée à gauche sur des pixels entiers. */
    static void barre(Canvas c, int x, int y, int w, int h, int u, float part, int plein, int pointe, int creux, Paint pt) {
        int pas = 4 * u, n = Math.max(1, (w + u) / pas);
        int pleins = Math.round(Math.max(0, Math.min(1, part)) * n);
        if (part > 0 && pleins == 0) pleins = 1;
        for (int i = 0; i < n; i++) {
            pt.setColor(i < pleins ? (i == pleins - 1 && pointe != 0 ? pointe : plein) : creux);
            c.drawRect(x + i * pas, y, x + i * pas + 3 * u, y + h, pt);
        }
    }
}
