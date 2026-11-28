package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.view.View;
import org.robolectric.RuntimeEnvironment;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;

/**
 * Le cadre pixel (CadrePixel) : tout se compte en u (ici u = 5 pixels d'écran) : bord d'1 u, coins en escalier (le pixel de
 * coin est vide), biseau d'1 u, ombre d'1 u en escalier, état « appuyé » sans ombre. Et le calage du fil sur une bulle entière.
 */
@RunWith(RobolectricTestRunner.class)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@Config(sdk = 34)
public class CadrePixelTest {
    private static final int U = 5;
    private static final CadrePixel.Couleurs C = CadrePixel.SOMBRE;

    private static Bitmap dessiner(CadrePixel d, int w, int h) {
        Bitmap b = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
        d.setBounds(0, 0, w, h);
        d.draw(new Canvas(b));
        return b;
    }

    @Test
    public void bordBiseauEtCoinsEnEscalier() {
        CadrePixel d = new CadrePixel(C, U, true);
        assertEquals(2 * U, d.dedans());
        assertEquals(U, d.ombre());
        Bitmap b = dessiner(d, 60, 40);   // cadre visible : 55 × 35, ombre d'1 u à droite et en bas
        // Les quatre coins du cadre : le pixel de 1 u × 1 u est vide.
        assertEquals(0, b.getPixel(0, 0));
        assertEquals(0, b.getPixel(U - 1, U - 1));
        assertEquals(0, b.getPixel(55 - 1, 0));
        assertEquals(0, b.getPixel(0, 35 - 1));
        // Le bord : 1 u, juste à côté du coin vide.
        assertEquals(C.bord, b.getPixel(U, 0));
        assertEquals(C.bord, b.getPixel(0, U));
        assertEquals(C.bord, b.getPixel(2 * U, U - 1));
        assertEquals(C.bord, b.getPixel(55 - 1, 2 * U));
        // Le biseau : 1 u, clair en haut et à gauche, sombre en bas et à droite ; puis le fond.
        assertEquals(C.biseauClair, b.getPixel(3 * U, U));
        assertEquals(C.biseauClair, b.getPixel(3 * U, 2 * U - 1));
        assertEquals(C.biseauClair, b.getPixel(U, 3 * U));
        assertEquals(C.biseauSombre, b.getPixel(3 * U, 35 - U - 1));
        assertEquals(C.biseauSombre, b.getPixel(55 - U - 1, 3 * U));
        assertEquals(C.fond, b.getPixel(3 * U, 2 * U));
        assertEquals(C.fond, b.getPixel(2 * U, 3 * U));
        // L'ombre : 1 u, en escalier elle aussi (ses coins haut-droite et bas-gauche manquent).
        assertEquals(C.ombre, b.getPixel(57, 20));
        assertEquals(C.ombre, b.getPixel(20, 37));
        assertEquals(0, b.getPixel(57, U + 2));
        assertEquals(0, b.getPixel(U + 2, 37));
        assertEquals(0, b.getPixel(59, 39));
    }

    @Test
    public void appuyeSansOmbreEtSansOmbreDuTout() {
        CadrePixel d = new CadrePixel(C, U, true);
        d.forcer(true);
        Bitmap b = dessiner(d, 60, 40);
        assertEquals(0, b.getPixel(57, 20));
        assertEquals(0, b.getPixel(20, 37));
        assertEquals(C.appuyeFond, b.getPixel(3 * U, 2 * U));
        assertEquals(C.bord, b.getPixel(U, 0));

        CadrePixel s = new CadrePixel(C, U, false);
        assertEquals(0, s.ombre());
        Bitmap c = dessiner(s, 60, 40);
        assertEquals(0, c.getPixel(0, 0));
        assertEquals(C.bord, c.getPixel(59 - U, 0 + 1));
        assertEquals(C.biseauSombre, c.getPixel(3 * U, 40 - U - 1));
        assertEquals(C.bord, c.getPixel(30, 39));
    }

    @Test
    public void lesPalettesSontCellesDuMenuDuPc() {
        assertEquals(0xff151a2e, CadrePixel.SOMBRE.fond);
        assertEquals(0xfffbf3e4, CadrePixel.CLAIRE.fond);
        assertEquals(0xff6a5acd, CadrePixel.SOMBRE.bord);
        assertEquals(0xff2f7ed8, CadrePixel.CLAIRE.bord);
        assertEquals(0xfff69d50, CadrePixel.SOMBRE.appuyeFond);
        assertEquals(0xff1f5fae, CadrePixel.CLAIRE.appuyeFond);
    }

    @Test
    public void filAncreEnBasLaDerniereBulleVientAuBasDuVisible() {
        // Hauts des bulles (pixels), fin du contenu 300, 250 visibles, marge 10 : le bas du contenu est au bas du visible (300 - 250).
        assertEquals(50, Lecture.Fil.cibleBas(new int[]{10, 100, 200}, 300, 250, 10));
        // Tout tient : on reste en haut (jamais négatif) ; c'est le fil qui colle ses bulles au bas (gravité), le vide est en haut.
        assertEquals(0, Lecture.Fil.cibleBas(new int[]{10, 100, 200}, 300, 400, 10));
        assertEquals(0, Lecture.Fil.cibleBas(new int[]{10, 100, 200}, 300, 300, 10));
        // Une seule bulle plus haute que l'écran : on montre son début (haut moins marge), pas sa fin.
        assertEquals(190, Lecture.Fil.cibleBas(new int[]{10, 100, 200}, 600, 50, 10));
        assertEquals(10, Lecture.Fil.cibleBas(new int[]{20}, 600, 100, 10));
        assertEquals(0, Lecture.Fil.cibleBas(new int[0], 0, 100, 10));
        // La bulle entamée en haut est masquée : le premier haut d'enfant à y ou plus bas ; rien après : la longueur.
        assertEquals(1, Lecture.Fil.premierEntier(new int[]{10, 100, 200}, 50));
        assertEquals(1, Lecture.Fil.premierEntier(new int[]{10, 100, 200}, 100));
        assertEquals(0, Lecture.Fil.premierEntier(new int[]{10, 100, 200}, 0));
        assertEquals(3, Lecture.Fil.premierEntier(new int[]{10, 100, 200}, 201));
    }

    private static void bulles(Lecture.Fil fil, int n) {
        for (int i = 0; i < n; i++) {
            android.widget.LinearLayout.LayoutParams lp = new android.widget.LinearLayout.LayoutParams(50, 100);
            lp.bottomMargin = 2 * U;
            fil.addView(new View(fil.getContext()), lp);
        }
    }

    private static void mesurer(Lecture.Fil fil, int visible) {
        fil.regler(visible, 2 * U);
        fil.measure(View.MeasureSpec.makeMeasureSpec(300, View.MeasureSpec.EXACTLY), View.MeasureSpec.makeMeasureSpec(0, View.MeasureSpec.UNSPECIFIED));
        fil.layout(0, 0, fil.getMeasuredWidth(), fil.getMeasuredHeight());
    }

    @Test
    public void filAncreEnBasMesureEtPlace() {
        Lecture.Fil fil = new Lecture.Fil(RuntimeEnvironment.getApplication());
        fil.setOrientation(android.widget.LinearLayout.VERTICAL);
        fil.setPadding(0, 2 * U, 0, 0);
        bulles(fil, 2);
        mesurer(fil, 1000);
        // Deux bulles courtes dans 1000 px : le fil fait la hauteur visible, la dernière bulle finit 2 u au-dessus du bas.
        assertEquals(1000, fil.getHeight());
        assertEquals(0, fil.cible());
        assertEquals(1000 - 2 * U, fil.getChildAt(1).getBottom());
        // Rien n'est entamé : à y = 0, la coupe tombe sur la première bulle (le vide est au-dessus).
        assertEquals(fil.getChildAt(0).getTop(), fil.hautEntier(0));
        org.junit.Assert.assertTrue(fil.getChildAt(0).getTop() > 2 * U);
        // Beaucoup de bulles : le bas du contenu est au bas du visible, et la bulle entamée en haut est coupée.
        bulles(fil, 10);
        mesurer(fil, 450);
        int fin = fil.getChildAt(fil.getChildCount() - 1).getBottom() + 2 * U;
        assertEquals(fin - 450, fil.cible());
        int y = fil.cible();
        int coupe = fil.hautEntier(y);
        org.junit.Assert.assertTrue("la coupe est dans la zone visible", coupe >= y && coupe < y + 450);
        org.junit.Assert.assertTrue("la première bulle gardée est entière (son haut est à la coupe)", coupe + 100 <= y + 450);
        assertEquals(2 * U, y + 450 - (fil.getChildAt(fil.getChildCount() - 1).getBottom()));
    }

    @Test
    public void lieuTientDansLaSceneAvecUneUniteDeMarge() {
        for (int k = 1; k <= 6; k++) {
            for (int largeur : new int[]{192 * k, 192 * k + 118, 192 * k + 300, 1078}) {
                if (largeur < 192 * k) continue;
                int gauche = (largeur - 192 * k) / 2, droite = gauche + 192 * k;   // la scène, centrée par TheatreVue
                // Le bord droit de la puce est à 1 u du bord droit de la scène.
                assertEquals(droite - k, largeur - Lecture.margeLieuDroite(largeur, k));
                // La puce la plus large commence à 1 u du bord gauche de la scène.
                assertEquals(gauche + k, droite - k - Lecture.largeurPuceMax(k));
            }
        }
        // Mesurée pour de bon : un lieu très long reste sur une ligne, et la puce ne dépasse pas la largeur max.
        android.content.Context c = RuntimeEnvironment.getApplication();
        CadrePixel.Pave puce = new CadrePixel.Pave(c, C, U, false);
        puce.air(U, U);
        TextePixelVue t = new TextePixelVue(c, 4f, 0xffffffff);
        t.maxLignes(1);
        t.maxLargeur(Lecture.largeurTexteLieu(U));
        t.texte("☀  Devant la porte de la maison du bout du chemin, là où le vent tourne à droite derrière la colline");
        puce.addView(t);
        puce.measure(View.MeasureSpec.makeMeasureSpec(1078, View.MeasureSpec.AT_MOST), View.MeasureSpec.makeMeasureSpec(0, View.MeasureSpec.UNSPECIFIED));
        org.junit.Assert.assertTrue("puce " + puce.getMeasuredWidth() + " <= " + Lecture.largeurPuceMax(U), puce.getMeasuredWidth() <= Lecture.largeurPuceMax(U));
        assertEquals(1, PolicePixel.texte().couper(PolicePixel.preparer(t.texte()), Lecture.largeurTexteLieu(U) / t.pixel(), 1).size());
        // Un lieu court garde sa taille naturelle.
        t.texte("☀  Devant la porte");
        puce.measure(View.MeasureSpec.makeMeasureSpec(1078, View.MeasureSpec.AT_MOST), View.MeasureSpec.makeMeasureSpec(0, View.MeasureSpec.UNSPECIFIED));
        org.junit.Assert.assertTrue(puce.getMeasuredWidth() < Lecture.largeurPuceMax(U) / 2);
    }

    @Test
    public void jaugeEnCarresPixel() {
        // 192 u de large, carrés d'1 u espacés d'1 u : 96 carrés, le dernier finit pile au bord.
        assertEquals(96, CadrePixel.Cases.nombre(192 * U, U, 1));
        assertEquals(10, CadrePixel.Cases.nombre(30 * U, U, 2));
        assertEquals(0, CadrePixel.Cases.pleines(0f, 96));
        assertEquals(1, CadrePixel.Cases.pleines(0.001f, 96));
        assertEquals(48, CadrePixel.Cases.pleines(0.5f, 96));
        assertEquals(96, CadrePixel.Cases.pleines(7f, 96));
        CadrePixel.Cases j = new CadrePixel.Cases(RuntimeEnvironment.getApplication(), 0xffff0000, 0xff0000ff, U, 1);
        j.part(0.5f);
        j.measure(View.MeasureSpec.makeMeasureSpec(192 * U, View.MeasureSpec.EXACTLY), View.MeasureSpec.makeMeasureSpec(0, View.MeasureSpec.UNSPECIFIED));
        j.layout(0, 0, 192 * U, U);
        Bitmap b = Bitmap.createBitmap(192 * U, U, Bitmap.Config.ARGB_8888);
        j.draw(new Canvas(b));
        assertEquals(0xffff0000, b.getPixel(0, 0));                // premier carré plein
        assertEquals(0, b.getPixel(U, 0));                          // l'espace d'1 u reste vide
        assertEquals(0xffff0000, b.getPixel(2 * U, 0));            // deuxième carré
        assertEquals(0xff0000ff, b.getPixel(2 * 60 * U, 0));       // seconde moitié : vide
        assertEquals(0xff0000ff, b.getPixel(192 * U - 1, 0));      // finit au bord exact
    }
}
