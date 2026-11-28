package fr.pilou.compagnon;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.ColorFilter;
import android.graphics.Paint;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.graphics.drawable.Drawable;
import android.view.View;
import android.widget.LinearLayout;

import java.util.ArrayList;
import java.util.List;

/**
 * Le cadre « main de Pilou » (comme le menu « Sept portes » du PC, MenuRetro.xaml, cadre « MenuCadre ») : tout en pixels
 * de la scène (u = k pixels d'écran, Aventure.unite). Fond plein ; bord de 1 u dont les quatre coins sont en escalier
 * (le pixel de coin de 1 u × 1 u manque) ; à l'intérieur un biseau de 1 u (clair en haut et à gauche, sombre en bas et à
 * droite) ; une ombre portée de 1 u en bas et à droite, en escalier elle aussi (elle tient dans les limites du dessin :
 * le cadre visible est donc plus petit d'1 u à droite et en bas). État « appuyé » : fond de survol, ombre retirée, et
 * (dans un Pave) contenu décalé d'1 u, comme un bouton qu'on enfonce. Aucun arrondi, aucun lissage.
 */
public final class CadrePixel extends Drawable {
    /** Les couleurs du cadre (reprises de MenuRetro.cs), sombre et clair. */
    public static final class Couleurs {
        public final int fond, texte, pale, bord, biseauClair, biseauSombre, ombre, appuyeFond, appuyeTexte, titre, pointilles;

        Couleurs(int fond, int texte, int pale, int bord, int biseauClair, int biseauSombre, int ombre, int appuyeFond, int appuyeTexte,
                 int titre, int pointilles) {
            this.fond = fond;
            this.texte = texte;
            this.pale = pale;
            this.bord = bord;
            this.biseauClair = biseauClair;
            this.biseauSombre = biseauSombre;
            this.ombre = ombre;
            this.appuyeFond = appuyeFond;
            this.appuyeTexte = appuyeTexte;
            this.titre = titre;
            this.pointilles = pointilles;
        }
    }

    public static final Couleurs SOMBRE = new Couleurs(0xff151a2e, 0xffe6ecf2, 0xffadbac7, 0xff6a5acd, 0xff3a4270, 0xff0b0e1a, 0xff0b0e1a,
            0xfff69d50, 0xff151a2e, 0xff9b8cff, 0xff6a5acd);
    public static final Couleurs CLAIRE = new Couleurs(0xfffbf3e4, 0xff1c2128, 0xff57606a, 0xff2f7ed8, 0xffffffff, 0xffd9c7a3, 0xff1c2128,
            0xff1f5fae, 0xffffffff, 0xff6a4fc8, 0xffc86a1c);

    /** Les couleurs du thème courant (le même choix clair / sombre que le reste de l'app : Ui.sombre). */
    public static Couleurs de(Context c) {
        return Ui.sombre(c) ? SOMBRE : CLAIRE;
    }

    /** Les couleurs de la bulle du joueur : celles de l'état « appuyé » (orange en sombre, bleu en clair), même bord. */
    public static Couleurs joueur(Couleurs c) {
        return new Couleurs(c.appuyeFond, c.appuyeTexte, c.appuyeTexte, c.bord, c.biseauClair, c.biseauSombre, c.ombre, c.appuyeFond,
                c.appuyeTexte, c.titre, c.pointilles);
    }

    /**
     * Taille voulue (dp) d'un pixel de police pour le récit et les choix : 4 pixels d'écran sur un téléphone 1078 × 2400 à
     * densité 2,75, fois l'échelle de police du système ; TextePixelVue l'arrondit à un nombre entier de pixels d'écran.
     */
    public static float policeDp(Context c) {
        return 4f / 2.75f * c.getResources().getConfiguration().fontScale;
    }

    private final Couleurs couleurs;
    private final int u;
    private final boolean ombre;
    private boolean appuye, force;
    private final Paint encre = new Paint();

    public CadrePixel(Couleurs couleurs, int u, boolean ombre) {
        this.couleurs = couleurs;
        this.u = Math.max(1, u);
        this.ombre = ombre;
    }

    public int unite() {
        return u;
    }

    /** Ce que le bord et le biseau prennent à l'intérieur du cadre, de chaque côté : 2 u. */
    public int dedans() {
        return 2 * u;
    }

    /** Ce que l'ombre prend à droite et en bas : 1 u, ou rien sans ombre. */
    public int ombre() {
        return ombre ? u : 0;
    }

    public boolean appuye() {
        return appuye || force;
    }

    /** Pose l'état « appuyé » à la main (un choix qu'on vient de faire). */
    public void forcer(boolean oui) {
        if (force == oui) return;
        force = oui;
        invalidateSelf();
    }

    @Override
    public boolean isStateful() {
        return true;
    }

    @Override
    protected boolean onStateChange(int[] etat) {
        boolean p = false;
        for (int s : etat) if (s == android.R.attr.state_pressed) p = true;
        if (p == appuye) return false;
        appuye = p;
        return true;
    }

    private void rect(Canvas c, int x0, int y0, int x1, int y1, int couleur) {
        if (x1 <= x0 || y1 <= y0) return;
        encre.setColor(couleur);
        c.drawRect(x0, y0, x1, y1, encre);
    }

    /** Un rectangle sans ses quatre pixels de coin (une croix : les coins en escalier). */
    private void escalier(Canvas c, int l, int t, int r, int b, int couleur) {
        rect(c, l + u, t, r - u, b, couleur);
        rect(c, l, t + u, r, b - u, couleur);
    }

    @Override
    public void draw(Canvas c) {
        Rect g = getBounds();
        int l = g.left, t = g.top, r = g.right - ombre(), b = g.bottom - ombre();
        boolean enfonce = appuye();
        if (ombre && !enfonce) escalier(c, l + u, t + u, r + u, b + u, couleurs.ombre);
        escalier(c, l, t, r, b, couleurs.bord);
        int il = l + u, it = t + u, ir = r - u, ib = b - u;
        rect(c, il, it, ir, ib, enfonce ? couleurs.appuyeFond : couleurs.fond);
        if (ir - il >= 3 * u && ib - it >= 3 * u) {
            rect(c, il, it, ir, it + u, couleurs.biseauClair);
            rect(c, il, it + u, il + u, ib - u, couleurs.biseauClair);
            rect(c, ir - u, it + u, ir, ib - u, couleurs.biseauSombre);
            rect(c, il, ib - u, ir, ib, couleurs.biseauSombre);
        }
    }

    @Override
    public void setAlpha(int alpha) {
    }

    @Override
    public void setColorFilter(ColorFilter colorFilter) {
    }

    @Override
    public int getOpacity() {
        return PixelFormat.TRANSLUCENT;
    }

    /**
     * Une vue à cadre pixel : fond CadrePixel, contenu rembourré de 2 u (bord + biseau) plus l'air voulu, plus l'ombre ;
     * appuyée, le contenu descend d'1 u vers la droite et les textes enregistrés prennent la couleur « appuyé ».
     */
    public static final class Pave extends LinearLayout {
        private final CadrePixel cadre;
        private final Couleurs couleurs;
        private final List<TextePixelVue> textes = new ArrayList<>();
        private final List<Integer> normales = new ArrayList<>();

        public Pave(Context c, Couleurs couleurs, int u, boolean ombre) {
            super(c);
            this.couleurs = couleurs;
            cadre = new CadrePixel(couleurs, u, ombre);
            setBackground(cadre);
            setClipChildren(false);
            setClipToPadding(false);
        }

        public CadrePixel cadre() {
            return cadre;
        }

        /** Rembourrage : bord, biseau, puis airH / airV pixels d'écran d'air, puis l'ombre à droite et en bas. */
        public void air(int airH, int airV) {
            int d = cadre.dedans();
            setPadding(d + airH, d + airV, d + airH + cadre.ombre(), d + airV + cadre.ombre());
        }

        /** Un texte du pavé : sa couleur normale, et « appuyé texte » quand le pavé est enfoncé. */
        public void encre(TextePixelVue t, int normale) {
            textes.add(t);
            normales.add(normale);
            t.couleur(normale);
        }

        @Override
        protected void drawableStateChanged() {
            super.drawableStateChanged();
            recolorer();
        }

        /** Après un forçage de l'état « appuyé ». */
        public void forcer(boolean oui) {
            cadre.forcer(oui);
            recolorer();
            invalidate();
        }

        private void recolorer() {
            boolean e = cadre.appuye();
            for (int i = 0; i < textes.size(); i++) textes.get(i).couleur(e ? couleurs.appuyeTexte : normales.get(i));
        }

        @Override
        protected void dispatchDraw(Canvas c) {
            if (cadre.appuye()) {
                int s = c.save();
                c.translate(cadre.unite(), cadre.unite());
                super.dispatchDraw(c);
                c.restoreToCount(s);
            } else super.dispatchDraw(c);
        }
    }

    /** Un trait en pointillés de pixels : un carré de 1 u tous les 2 u. */
    public static final class Pointilles extends View {
        private final int u;
        private final Paint encre = new Paint();

        public Pointilles(Context c, int couleur, int u) {
            super(c);
            this.u = Math.max(1, u);
            encre.setColor(couleur);
        }

        @Override
        protected void onMeasure(int mw, int mh) {
            setMeasuredDimension(resolveSize(2 * u, mw), u);
        }

        @Override
        protected void onDraw(Canvas c) {
            for (int x = 0; x + u <= getWidth(); x += 2 * u) c.drawRect(x, 0, x + u, u, encre);
        }
    }

    /** Trois carrés de 1 u, espacés d'1 u : le glyphe « ⋯ » du bandeau. */
    public static final class TroisPoints extends View {
        private final int u;
        private final Paint encre = new Paint();

        public TroisPoints(Context c, int couleur, int u) {
            super(c);
            this.u = Math.max(1, u);
            encre.setColor(couleur);
        }

        @Override
        protected void onMeasure(int mw, int mh) {
            setMeasuredDimension(5 * u, u);
        }

        @Override
        protected void onDraw(Canvas c) {
            for (int i = 0; i < 3; i++) c.drawRect(2 * i * u, 0, (2 * i + 1) * u, u, encre);
        }
    }

    /**
     * Une jauge en carrés pixel (comme « Cases » de FenetreAventure.cs) : des carrés de taille × u séparés d'1 u, sur toute
     * la largeur de la vue ; le dernier carré s'allonge pour finir exactement au bord. Pleins : couleur « plein », les
     * autres : couleur « vide ».
     */
    public static final class Cases extends View {
        private final int u, taille, plein, vide;
        private float part;
        private final Paint encre = new Paint();

        public Cases(Context c, int plein, int vide, int u, int taille) {
            super(c);
            this.u = Math.max(1, u);
            this.taille = Math.max(1, taille);
            this.plein = plein;
            this.vide = vide;
        }

        public void part(float v) {
            part = Math.max(0, Math.min(1, v));
            invalidate();
        }

        /** Nombre de carrés qui tiennent dans la largeur (carrés de taille u, espacés d'1 u). */
        public static int nombre(int largeur, int u, int taille) {
            return Math.max(1, (largeur + u) / ((taille + 1) * u));
        }

        /** Nombre de carrés pleins pour une part de 0 à 1, au moins un dès que la part n'est pas nulle. */
        public static int pleines(float part, int n) {
            int p = Math.round(Math.max(0, Math.min(1, part)) * n);
            return part > 0 ? Math.max(1, p) : 0;
        }

        @Override
        protected void onMeasure(int mw, int mh) {
            setMeasuredDimension(resolveSize(0, mw), taille * u);
        }

        @Override
        protected void onDraw(Canvas c) {
            int w = getWidth(), n = nombre(w, u, taille), pas = (taille + 1) * u, p = pleines(part, n);
            for (int i = 0; i < n; i++) {
                encre.setColor(i < p ? plein : vide);
                int x = i * pas;
                c.drawRect(x, 0, i == n - 1 ? w : x + taille * u, taille * u, encre);
            }
        }
    }
}
